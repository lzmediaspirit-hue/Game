class_name TopdownBrain
extends RefCounted
## Top-down redesign, Phase 2 (docs/redesign_top_down_plan.md §2.2 "Enemy and ally AI"): the S13 monster rules on a
## height grid (TopdownRoom). EnemyBrain keeps the states and their timing (wind-up, blow, recovery, stagger) and hands
## the ones that move over the room here: idle and patrol on the home floor, noticing the player (sight on the plane, a
## level up or down: no higher), the chase, fleeing, and going home. The rules are EnemyBrain's own (sight, the crowd cap,
## the 600 leash, the flee share, the chase speed, the "can't reach you" rule); only the steering is the grid's.
##
## The chase goes straight at the player on one floor with a clear line, else along TopdownRoom.find_path: walking,
## stairs, dropping off any edge, and for a jumper (the species' movement jump > 0) a hop one level up. A ground-bound
## foe that has no way up waits beneath the target; after 6 s it gives up and goes home healing (S43 rule 11).

const STATES := ["idle", "patrol", "aggro", "flee", "return"]

static func conf(key: String, fallback = 0.0):
	return ContentDB.movement("topdown.foes." + key, fallback)

static func think(auth, e: EnemyState, delta: float) -> void:
	var ai := e.ai
	var room: TopdownRoom = auth.game.room_rt.topdown
	var tgt := EnemyBrain.target_position(auth, e)
	var seen := EnemyBrain.sight(auth, e)
	match str(ai.state):
		"idle", "patrol":
			if not tgt.is_empty():
				var d: Vector2 = tgt.pos - e.plane
				var sees := d.length() <= float(seen.range) and absf(float(tgt.alt) - e.altitude) <= TopdownRoom.LEVEL + 0.5
				if EnemyBrain.notices(auth, e, tgt, sees): return
			if ai.state == "idle":
				e.velocity = Vector2.ZERO
				e.action = "idle"
				if float(ai.timer) <= 0.0:
					var span := float(e.def.get("ai", {}).get("patrol", 140))
					for i in 4:
						var p := e.spawn_point + Vector2(auth.rng.randf_range(-span, span), auth.rng.randf_range(-span, span) * 0.5)
						if room.free_at(p, e.altitude, conf("radius", 8.0)) and absf(room.height_at(p) - e.altitude) <= 8.0:
							ai.patrol_x = p.x
							ai.patrol_y = p.y
							break
					EnemyBrain._set_state(auth, e, "patrol", 4.0)
			else:
				EnemyBrain._wander(auth, e, delta, 0.5)
		"aggro":
			if EnemyBrain.gives_up(auth, e, tgt, seen.hidden): return
			var d: Vector2 = tgt.pos - e.plane
			if e.pools.has_status("fear") or e.pools.has_status("confusion"):
				var away := -d.normalized() if e.pools.has_status("fear") and d.length() > 0.1 else Vector2.from_angle(auth.game.sim_time * 1.4 + e.uid)
				_walk(auth, e, away, EnemyBrain.chase_speed(auth, e) * (0.9 if e.pools.has_status("fear") else 0.45), delta)
				return
			var attacks: Array = e.def.get("attacks", [])
			if attacks.is_empty(): return
			var attack: Dictionary = attacks[EnemyBrain._choose_attack(auth, e, attacks)]
			var reach := float(attack.hitbox.x[1])
			if ai.get("counter", false):
				ai.timer = 0.0
				reach += 30.0
			var dist := d.length()
			var level_ok := TopdownAim.compatible(float(tgt.alt) - e.altitude)
			var keep := float(e.def.get("keep_distance", 0))
			if dist > 0.5: e.aim = d / dist
			e.facing = 1 if d.x >= 0.0 else -1
			if level_ok and dist <= reach + 14.0 and (keep <= 0.0 or dist >= keep * 0.5 or reach > 200.0):
				if float(ai.timer) <= 0.0: EnemyBrain.wind_up(auth, e, attacks, attack)
				else: _walk(auth, e, Vector2.ZERO, 0.0, delta)
				return
			if keep > 0.0 and dist < keep:
				_walk(auth, e, -e.aim, EnemyBrain.chase_speed(auth, e), delta)
				return
			chase(auth, e, tgt.pos, float(tgt.alt), EnemyBrain.chase_speed(auth, e), delta)
		"flee":
			if tgt.is_empty() or float(ai.timer) <= 0.0:
				EnemyBrain._set_state(auth, e, "aggro", 0.3)
				return
			var off: Vector2 = e.plane - tgt.pos
			_walk(auth, e, off.normalized() if off.length() > 0.1 else Vector2.RIGHT, float(e.def.get("ai", {}).get("move_speed", 90)) * 1.2, delta)
		"return":
			# Led home by the out-of-reach rule: heal 10% a second on the way (S43).
			if ai.get("leashed", false): e.pools.hp = minf(e.pools.max_hp, e.pools.hp + e.pools.max_hp * 0.1 * delta)
			var home := room.height_at(e.spawn_point)
			if e.plane.distance_to(e.spawn_point) < 12.0 or float(ai.timer) <= 0.0:
				if e.plane.distance_to(e.spawn_point) >= 12.0:   # no way back on foot: it slips home out of sight
					e.plane = e.spawn_point
					e.altitude = home
				e.pools.hp = e.pools.max_hp
				e.threat.clear()
				ai.leashed = false
				ai.unreach = 0.0
				EnemyBrain._set_state(auth, e, "idle", 1.0)
				return
			chase(auth, e, e.spawn_point, home, float(e.def.get("ai", {}).get("move_speed", 90)), delta, false)

## Walk toward `goal` (at height `goal_alt`): straight on one floor with a clear line, else along the grid's path,
## hopping up a level where a jumper can. With no way there a chaser (`hunt`) paces beneath and, after 6 s, gives up.
static func chase(auth, e: EnemyState, goal: Vector2, goal_alt: float, speed: float, delta: float, hunt := true) -> void:
	var ai := e.ai
	var room: TopdownRoom = auth.game.room_rt.topdown
	if absf(goal_alt - e.altitude) <= 8.0 and line_clear(room, e.plane, goal, e.altitude):
		ai.unreach = 0.0
		ai.path = []
		_walk(auth, e, (goal - e.plane).normalized() if goal.distance_to(e.plane) > 1.0 else Vector2.ZERO, speed, delta)
		return
	var there := TopdownRoom.cell_of(goal)
	ai.replan = float(ai.get("replan", 0.0)) - delta
	if float(ai.replan) <= 0.0 or ai.get("path_goal", Vector2i(-1, -1)) != there:
		ai.path = room.find_path(TopdownRoom.cell_of(e.plane), there, float(EnemyBrain.movement_of(e).get("jump", 0)) > 0.0)
		ai.path_goal = there
		ai.replan = conf("replan_s", 0.4)
	var path: Array = ai.path
	while not path.is_empty() and TopdownRoom.cell_of(e.plane) == path[0]: path.pop_front()
	if path.is_empty():
		if not hunt:
			_walk(auth, e, (goal - e.plane).normalized(), speed, delta)
			return
		ai.unreach = float(ai.get("unreach", 0.0)) + delta
		if EnemyBrain.out_of_reach_too_long(auth, e): return
		# Pace beneath it, waiting for it to come down.
		var under := goal - e.plane
		_walk(auth, e, under.normalized() if under.length() > 30.0 else Vector2.ZERO, speed, delta)
		return
	ai.unreach = 0.0
	var next: Vector2 = (Vector2(path[0]) + Vector2(0.5, 0.5)) * TopdownRoom.TILE
	var rise := room.cell_floor(path[0]) - e.altitude
	var stairs := not room.stair_at(path[0].x, path[0].y).is_empty() or not room.stair_at(TopdownRoom.cell_of(e.plane).x, TopdownRoom.cell_of(e.plane).y).is_empty()
	if rise > 8.5 and not stairs and e.plane.distance_to(next) <= TopdownRoom.TILE * 1.2:
		# A jumper hops the level up, on the grid's own gravity and a jump that clears one level.
		EnemyBrain._start_hop(auth, e, {"kind": "jump", "to": "", "to_alt": room.cell_floor(path[0]), "to_pt": next},
			float(ContentDB.movement("topdown.gravity", 1700)), conf("impulse", 400.0))
		return
	_walk(auth, e, (next - e.plane).normalized(), speed, delta)

# ------------------------------------------------------------------ Phase 4: allies on the grid (AllyBrain)
## The floor under a body (its own height while it stands; the floor below while it is in the air).
static func floor_under(room: TopdownRoom, st: ActorState) -> float:
	var g := room.height_at(st.plane)
	return g if g < INF and g <= st.altitude + 1.0 else st.altitude

## A free spot for an ally on the owner's floor toward `want`, on the owner's side of any wall (a clear walk from the
## owner): `want` itself, else halfway or a quarter of the way there; the owner's own spot when none is.
static func spot_by(room: TopdownRoom, owner: Vector2, ground: float, want: Vector2) -> Vector2:
	var r := float(conf("radius", 8.0))
	for k in [1.0, 0.5, 0.25]:
		var p := owner.lerp(want, k)
		if room.free_at(p, ground, r) and absf(room.floor_at(p) - ground) <= 8.0 and line_clear(room, owner, p, ground): return p
	return owner

## Where an ally keeps while it follows on the grid: `offset` behind the owner along its facing on the plane (`facing`,
## a direction) and `depth` to its side, on its ground (spot_by).
static func follow_spot(room: TopdownRoom, owner: Vector2, ground: float, facing: Vector2, offset: float, depth: float) -> Vector2:
	var f := facing.normalized() if facing.length() > 0.01 else Vector2.RIGHT
	return spot_by(room, owner, ground, owner - f * offset + Vector2(-f.y, f.x) * depth)

## Is the straight line from `a` to `b` walkable on the floor at `z` (no wall, prop, water or drop on the way)?
static func line_clear(room: TopdownRoom, a: Vector2, b: Vector2, z: float) -> bool:
	var n := ceili(a.distance_to(b) / 10.0)
	var r := float(conf("radius", 8.0))
	for i in range(1, n + 1):
		var p := a.lerp(b, float(i) / float(n))
		if not room.free_at(p, z, r) or room.height_at(p) < z - 8.0: return false
	return true

static func _walk(auth, e: EnemyState, dir: Vector2, speed: float, delta: float) -> void:
	e.velocity = dir * speed
	if dir.x != 0.0: e.facing = 1 if dir.x > 0.0 else -1
	e.action = "walk" if e.velocity != Vector2.ZERO else "idle"
	auth.move_enemy(e, delta)

## The grid's move for a foe or an ally (EnemyAuthority.move_enemy): along the plane where its footing is free (sliding
## along a wall on one axis), up stairs and small steps, and off any edge into a fall to the floor below (a knockback
## can push it off a ledge). It keeps out of the ways out, as in the side view (one already in a way may walk out of
## it). A flyer goes where it likes.
static func move(auth, e: EnemyState, delta: float) -> void:
	var room: TopdownRoom = auth.game.room_rt.topdown
	var next := e.plane + e.velocity * delta
	if bool(e.def.get("flying", false)):
		e.plane = next.clamp(Vector2.ZERO, Vector2(room.w, room.h) * TopdownRoom.TILE)
		return
	var r := float(conf("radius", 8.0))
	var in_way: bool = auth._in_portal(e.plane)
	var ok := func(p: Vector2) -> bool: return room.free_at(p, e.altitude, r) and (in_way or not auth._in_portal(p))
	if ok.call(next): e.plane = next
	elif ok.call(Vector2(next.x, e.plane.y)): e.plane = Vector2(next.x, e.plane.y)
	elif ok.call(Vector2(e.plane.x, next.y)): e.plane = Vector2(e.plane.x, next.y)

## Follow the floor underfoot, once a tick (EnemyAuthority): stairs and steps at once, a drop under gravity.
static func fall(room: TopdownRoom, e: EnemyState, delta: float) -> void:
	var ground := room.height_at(e.plane)
	if ground == INF: return
	if ground < e.altitude - 8.0 or e.vz > 0.0:
		e.vz -= float(ContentDB.movement("topdown.gravity", 1700)) * delta
		e.altitude = maxf(ground, e.altitude + e.vz * delta)
		if e.altitude <= ground: e.vz = 0.0
	else:
		e.altitude = ground
		e.vz = 0.0
