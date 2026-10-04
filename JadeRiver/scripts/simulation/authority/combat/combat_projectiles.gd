class_name CombatProjectiles
extends CombatPart
## CombatAuthority's part for projectiles, the player's and the foes': arrows, notes of Qi, thrown fans, flying swords,
## throwables and foes' missiles. The shots in flight are the room's (`RoomRuntime.projectiles`).

func spawn_projectile(p: Dictionary) -> void:
	if game.room_rt == null: return
	p.uid = game.room_rt.uid()
	p.travelled = 0.0
	p.hits = []
	p.delay = float(p.get("delay", 0.0))
	_aim_shot(p)
	game.room_rt.projectiles.append(p)
	emit("projectile_spawned", {"uid": p.uid, "team": p.team, "art": str(p.get("art", "arrow")), "element": str(p.get("element", "none"))})

## Redesign Phase 2: a shot on the plane leaves along its thrower's aim. Its spot, laid out along x by the spawner (so
## far ahead, so far aside), turns with the aim; it flies at its thrower's feet (`feet`) along the ground plane.
func _aim_shot(p: Dictionary) -> void:
	var o := Vector2(float(p.x), float(p.y))
	var feet := 0.0
	var aim := Vector2(float(p.dir), 0)
	var foe: EnemyState = game.room_rt.enemies.get(int(str(p.owner))) if str(p.owner).is_valid_int() else null
	if foe != null:
		o = foe.plane
		feet = foe.altitude
		aim = foe.aim_dir()
	elif game.actor_state(str(p.owner)) != null:
		o = game.actor_state(str(p.owner)).plane
		feet = game.actor_state(str(p.owner)).altitude
		aim = combat.timeline(str(p.owner)).get("aim", aim)
	var ahead := (float(p.x) - o.x) * float(p.dir)
	var aside := float(p.y) - o.y
	var at := o + aim * ahead + Vector2(-aim.y, aim.x) * aside
	p.x = at.x
	p.y = at.y
	p.aim = aim
	p.feet = feet
	p.dir = 1 if aim.x >= 0.0 else -1

## A shot's view for the hit test: at its thrower's feet along its aim, with the ground band.
func _shot_view(p: Dictionary) -> Dictionary:
	return {"x": p.x, "y": p.y, "alt": float(p.feet), "aim": p.aim, "band": TopdownAim.band(false)}

## Does a shot stop here: at a face higher than shot_wall over its feet (S43 rule 10)?
func _shot_stops(rt: RoomRuntime, p: Dictionary) -> bool:
	return rt.topdown.height_at(Vector2(p.x, p.y)) > float(p.feet) + float(ContentDB.movement("topdown.combat.shot_wall", 24))

func spawn_enemy_projectile(e: EnemyState, attack: Dictionary) -> void:
	var pr: Dictionary = attack.get("projectile", {})
	spawn_projectile({"team": "enemy", "owner": str(e.uid), "x": e.plane.x + e.facing * e.half_width(), "y": e.plane.y,
		"alt": e.altitude + e.hover + e.height() * 0.55, "dir": e.facing, "speed": float(pr.get("speed", 400)),
		"range": float(attack.hitbox.x[1]), "pierce": 0, "art": str(pr.get("art", "pebble")), "enemy_attack": attack,
		"element": e.element})

func tick_projectiles(delta: float) -> void:
	if game.room_rt == null: return
	var rt = game.room_rt
	var c = game.active()
	for p in rt.projectiles.duplicate():
		if float(p.delay) > 0.0:
			p.delay = float(p.delay) - delta
			continue
		var step := float(p.speed) * delta
		var remaining := minf(step, float(p.range) - float(p.travelled))
		var done := false
		while remaining > 0.001 and not done:
			var s := minf(remaining, 6.0)
			if p.get("seek", false) and p.team == "player":
				var tgt := combat._nearest_enemy(Vector2(p.x, p.y), 220.0)
				if tgt: p.y = move_toward(float(p.y), tgt.plane.y, 60.0 * delta)
			var along: Vector2 = p.get("aim", Vector2(float(p.dir), 0))
			p.x = float(p.x) + along.x * s
			p.y = float(p.y) + along.y * s
			p.travelled = float(p.travelled) + s
			remaining -= s
			# S43 rule 10: shots pass through platform decks but stop at blocks and walls, whoever threw them.
			if _shot_stops(rt, p):
				done = true
				break
			if p.team == "player":
				for e in rt.living_enemies():
					if e.team != "enemy" or e.hidden or p.hits.has(e.uid): continue
					# Shots fly at chest height; the band reaches down to the ground so a crab or a rat
					# under the line is struck too. Fired from the air, a shot still passes over them.
					if CombatAuthority.hit_test(_shot_view(p), int(p.dir), {"x": [-12, 12], "depth": 26, "alt": [-56, 40]}, combat.enemy_view(e)):
						p.hits.append(e.uid)
						if c != null:
							var view := combat.player_view(c)
							combat.player_hits_enemy(c, view, e, p.attack, int(p.dir))
							if float(p.get("burst", 0.0)) > 0.0: combat.treasures.burst(c, p, e)
						if p.hits.size() > int(p.get("pierce", 0)):
							done = true
							break
			elif c != null and not combat.wounded.has(c.id):
				var cv := combat.player_view(c)
				var fxs: Dictionary = combat.treasure_fx.get(c.id, {})
				# The Sealing Gourd drinks every missile that comes within its reach (S47).
				if float(fxs.get("gourd", 0.0)) > 0.0 and Vector2(float(p.x), float(p.y)).distance_to(Vector2(float(cv.x), float(cv.y))) < float(fxs.get("gourd_r", 240.0)):
					emit("projectile_absorbed", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt})
					done = true
					break
				if CombatAuthority.hit_test(_shot_view(p), int(p.dir), {"x": [-10, 10], "depth": 24, "alt": [0, 40]}, cv) \
						and float(fxs.get("reflect", 0.0)) > 0.0:
					# The Bright Mirror sends it back at whoever threw it (S47).
					p.team = "player"
					p.dir = -int(p.dir)
					p.aim = -(p.aim as Vector2)
					p.owner = c.id
					p.travelled = 0.0
					p.hits = []
					p.attack = {"damage_type": "qi", "element": str(p.get("element", "none")), "mult": [1.4, 1.4], "range": [1.0, 1.0], "source": "bright_mirror"}
					emit("projectile_reflected", {"actor": c.id, "x": p.x, "y": p.y, "alt": p.alt})
					break
				if CombatAuthority.hit_test(_shot_view(p), int(p.dir), {"x": [-10, 10], "depth": 24, "alt": [0, 40]}, cv):
					var e2: EnemyState = rt.enemies.get(int(str(p.owner)))
					if e2 != null:
						combat.enemy_hits_player(e2, c, combat.enemy_view(e2), cv, p.enemy_attack)
					done = true
		if (done or float(p.travelled) >= float(p.range)) and p.get("returning", false) and not p.get("returned", false):
			# A thrown fan (S47 v1.1) turns at the end of its flight and cuts its way back.
			p.returned = true
			p.dir = -int(p.dir)
			p.aim = -(p.aim as Vector2)
			p.travelled = 0.0
			p.hits = []
			continue
		if done or float(p.travelled) >= float(p.range):
			# A poison pill that meets no one still breaks where it lands.
			if c != null and p.team == "player" and (p.hits as Array).is_empty() and not (p.get("cloud", {}) as Dictionary).is_empty():
				combat.treasures.burst(c, p, null)
			rt.projectiles.erase(p)
			emit("projectile_ended", {"uid": p.uid, "x": p.x, "y": p.y, "alt": p.alt})
