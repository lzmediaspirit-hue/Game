class_name EnemyAuthority
extends Authority
## S13 · Owns EnemyState for every live monster in the loaded room, spawn slots
## and respawn timers. Monsters use the same stats and combat rules as players.

var rng: RandomNumberGenerator = RandomNumberGenerator.new()

func subscribe() -> void:
	GameEvents.subscribe("room_entered", _on_room_entered, 40)
	GameEvents.subscribe("quest_accepted", _on_state_change, 40)
	GameEvents.subscribe("objective_progressed", _on_state_change, 40)
	GameEvents.subscribe("item_added", _on_state_change, 40)
	GameEvents.subscribe("flag_set", _on_state_change, 40)
	GameEvents.subscribe("actor_defeated", _on_defeated, 45)

func _on_defeated(p: Dictionary) -> void:
	if str(p.get("role", "")) == "field_boss": emit("field_boss_defeated", {"room": str(p.get("room", "")), "enemy": str(p.get("def", ""))})
	# S46: a Beast King falls. Its zone's beasts lose the +10% at once, and its lair's egg nest opens for 30 minutes.
	var king := ContentDB.entry("beast_kings", str(p.get("def", "")))
	if king.is_empty(): return
	if game.room_rt != null:
		for e in game.room_rt.living_enemies():
			if e.ai.get("king_buff", false): _set_king_buff(e, false)
	var nests: Dictionary = game.account.rooms.get("king_nests", {})
	nests[str(king.id)] = Clock.now_utc() + float(king.get("nest", {}).get("minutes", 30)) * 60.0
	game.account.rooms["king_nests"] = nests
	emit("king_nest_opened", {"king": str(king.id), "room": str(king.get("room", "")), "minutes": float(king.get("nest", {}).get("minutes", 30))})

## S46 Beast Kings: alive unless its field-boss respawn timer is running (account-wide, like every field boss).
func king_alive(king_id: String) -> bool:
	return Clock.now_utc() >= float(game.account.rooms.get("field_boss_timers", {}).get(king_id, 0.0))

## The King whose zone this room is in and who lives now ({} when none).
func living_king(room_id: String) -> Dictionary:
	var zone := str(ContentDB.room(room_id).get("zone", ""))
	for k in ContentDB.all("beast_kings"):
		if str(k.get("zone", "")) == zone and king_alive(str(k.id)): return k
	return {}

## While its King lives, a beast of its zone is 10% stronger (HP and attack); the King itself is not.
func _apply_king_buff(e: EnemyState) -> void:
	if game.room_rt == null or WorldAuthority.beast_rank(e.def, e.level) <= 0 or e.team != "enemy": return
	var k := living_king(game.room_rt.room_id)
	if k.is_empty() or str(k.id) == e.def_id: return
	e.ai["king_mult"] = 1.0 + float(k.get("buff", 0.1))
	_set_king_buff(e, true)

func _set_king_buff(e: EnemyState, on: bool) -> void:
	var m := float(e.ai.get("king_mult", 1.1))
	var f := m if on else 1.0 / m
	e.stats.attack = float(e.stats.get("attack", 0.0)) * f
	e.stats.max_hp = float(e.stats.get("max_hp", 0.0)) * f
	var frac := e.pools.hp / maxf(1.0, e.pools.max_hp)
	e.pools.max_hp = float(e.stats.max_hp)
	e.pools.hp = e.pools.max_hp * frac
	e.ai["king_buff"] = on

func _on_room_entered(_p: Dictionary) -> void:
	populate()

func _on_state_change(_p: Dictionary) -> void:
	# Conditional spawns (Old Snapper after five shells) appear when their requirement holds.
	if game.room_rt == null: return
	for slot in game.room_rt.spawn_slots:
		if int(slot.uid) == 0 and float(slot.timer) > 900.0 and _spawn_allowed(slot.spec):
			slot.timer = 1.0

func _spawn_allowed(spec: Dictionary) -> bool:
	if spec.has("requires") and not RequirementRules.passes(spec.requires, game.ctx()): return false
	if spec.get("field_boss", false):
		var until := float(game.account.rooms.get("field_boss_timers", {}).get(str(spec.enemy), 0.0))
		if Clock.now_utc() < until: return false
		if not Unlocks.is_unlocked(game.active_id, "field_bosses"): return false
	# S46: the paw-marked beasts that gather while a Beast King lives.
	if spec.has("king_alive") and not king_alive(str(spec.king_alive)): return false
	# S49: a calendar boss (the Drowned Abbot) wakes again after its first defeat only while its event is open.
	if spec.has("calendar"):
		var c = game.active()
		if c != null and c.collection_first_kills.has(str(spec.enemy)) and not game.calendar.repeat_open(c, str(spec.calendar)): return false
	return true

func populate() -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return
	rng = Rng.stream(game.active_id, "world") if game.active_id != "" else rng
	# Keep what the room's own event already summoned (a trial boss, a siege brute).
	var keep := {}
	for uid in rt.enemies:
		if rt.enemies[uid].summoned: keep[uid] = rt.enemies[uid]
	rt.enemies = keep
	rt.spawn_slots.clear()
	var index := 0
	for spec in rt.def.get("spawns", []):
		var points: Array = spec.get("points", [])
		if points.is_empty(): continue
		var count := int(spec.get("max", points.size()))
		for i in count:
			var p: Array = points[i % points.size()]
			rt.spawn_slots.append({"spec": spec, "index": index, "point": Vector2(float(p[0]), float(p[1])), "uid": 0,
				"timer": 0.2 + i * 0.15 if _spawn_allowed(spec) else 99999.0})
			index += 1

func tick(delta: float) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return
	# A trial that clears the ground (S48 Temper trials) holds the room's own foes back until it ends.
	var held: bool = rt.event.get("active", false) and rt.event.get("clear_room", false)
	for slot in rt.spawn_slots:
		if int(slot.uid) != 0 or held: continue
		slot.timer = float(slot.timer) - delta
		if float(slot.timer) <= 0.0:
			if _spawn_allowed(slot.spec): _spawn(slot)
			else: slot.timer = 99999.0
	for uid in rt.enemies.keys():
		var e: EnemyState = rt.enemies[uid]
		if e.team == "ally": continue
		e.action_time += delta
		if e.flash > 0.0: e.flash = maxf(0.0, e.flash - delta)
		if not e.alive:
			e.dead_time += delta
			e.action = "death"
			if e.dead_time > 1.6:
				rt.enemies.erase(uid)
				emit("enemy_removed", {"uid": uid})
			continue
		if absf(e.knockback) > 0.5:
			var step := e.knockback * minf(1.0, delta * 12.0)
			var before := e.velocity
			e.velocity = Vector2(step / delta, 0)
			move_enemy(e, delta)
			e.velocity = before
			e.knockback -= step
		_check_phases(e)
		if e.def.get("ai", {}).get("profile", "") == "event_eel":
			_eel(e, delta)
			continue
		e.ai.summon_cd = maxf(0.0, float(e.ai.get("summon_cd", 0.0)) - delta)
		e.ai.stun_guard = maxf(0.0, float(e.ai.get("stun_guard", 0.0)) - delta)
		if e.def.has("flees_after_s") and not str(e.ai.state) in ["idle", "patrol"]:
			# Story bosses that cannot be beaten yet (Elder Gu) hold for a while, then escape,
			# dropping what they carried.
			e.ai.engaged_t = float(e.ai.get("engaged_t", 0.0)) + delta
			if float(e.ai.engaged_t) >= float(e.def.flees_after_s):
				_flee(e)
				continue
		EnemyBrain.think(self, e, delta)
		if e.def.get("ai", {}).get("profile", "") == "burrower":
			e.hidden = e.ai.state in ["aggro", "patrol"] and e.velocity.length() > 5.0 and not e.pools.has_status("sense_locked")
		if bool(e.def.get("flying", false)):
			# Flyers hover within a grounded fighter's melee band (+60, S43) and swoop lower to strike.
			e.hover = 48.0 + sin(game.sim_time * 2.0 + e.uid) * 8.0 - (32.0 if e.ai.state in ["attack"] else 0.0)
		else:
			# S47 v1.1: a foe the fan's wind has launched rises and falls in an arc until it lands.
			var la: Dictionary = e.pools.status("launched")
			if not la.is_empty():
				var dur := maxf(0.1, float(la.get("duration", 0.8)))
				e.hover = float(ContentDB.entry("status_effects", "launched").get("lift", 46)) * sin(PI * clampf(1.0 - float(la.remaining) / dur, 0.0, 1.0))
				e.ai.lifted = true
			elif e.ai.get("lifted", false):
				e.hover = 0.0
				e.ai.erase("lifted")

func _spawn(slot: Dictionary) -> EnemyState:
	var rt: RoomRuntime = game.room_rt
	var spec: Dictionary = slot.spec
	var def := ContentDB.entry("enemies", str(spec.enemy))
	if def.is_empty(): return null
	var e := EnemyState.new()
	e.uid = rt.uid()
	e.def_id = str(spec.enemy)
	e.def = def
	var lv_range: Array = spec.get("level", def.get("level", [1, 1]))
	e.level = rng.randi_range(int(lv_range[0]), int(lv_range[lv_range.size() - 1]))
	e.elite = bool(spec.get("elite", false))
	e.role = "elite" if e.elite else str(def.get("role", "normal"))
	e.element = str(def.get("element", "none"))
	e.realm_index = ProgressionRules.realm_index_for_level(e.level)
	e.stats = StatRules.mob_stats(def, e.level, e.elite)
	e.pools.max_hp = float(e.stats.max_hp)
	e.pools.hp = e.pools.max_hp
	e.spawn_index = int(slot.index)
	var point: Vector2 = slot.point
	# Respawn at an empty point out of view when possible.
	var st: ActorState = game.actor_state(game.active_id)
	if st != null and absf(point.x - st.plane.x) < 500.0 and spec.get("points", []).size() > 1:
		for p in spec.points:
			var cand := Vector2(float(p[0]), float(p[1]))
			if absf(cand.x - st.plane.x) >= 500.0:
				point = cand
				break
	e.plane = point
	e.spawn_point = point
	var surf: WalkSurface = rt.geometry.index.get(str(spec.get("surface", "ground")))
	if surf == null:
		for s in rt.geometry.surfaces:
			if s.contains(point):
				surf = s
				break
	e.surface_id = surf.id if surf else ""
	e.home_surface = e.surface_id
	e.altitude = surf.height_at(point) if surf else 0.0
	e.facing = -1 if rng.randf() < 0.5 else 1
	e.ai = {"state": "idle", "timer": rng.randf_range(0.5, 2.0), "target": "", "attack": 0, "patrol_x": point.x, "patrol_y": point.y,
		"hit_done": false, "phase": -1, "dash_left": 0.0, "summon_cd": 8.0}
	e.hidden = bool(def.get("hidden_in_fog", false)) and not Unlocks.is_unlocked(game.active_id, "spirit_sense")
	slot.uid = e.uid
	rt.enemies[e.uid] = e
	_apply_king_buff(e)
	var event_name := "elite_spawned" if e.elite else ("field_boss_spawned" if e.role == "field_boss" else "enemy_spawned")
	emit(event_name, {"room": rt.room_id, "enemy": e.uid, "def": e.def_id, "level": e.level})
	var kd := ContentDB.entry("beast_kings", e.def_id)
	if not kd.is_empty(): emit("beast_king_spawned", {"king": e.def_id, "zone": str(kd.get("zone", "")), "room": rt.room_id, "buff": float(kd.get("buff", 0.1))})
	if event_name != "enemy_spawned": emit("enemy_spawned", {"room": rt.room_id, "enemy": e.uid, "def": e.def_id, "level": e.level})
	return e

## Spawn a specific enemy (quests, spars, boss summons, events).
func spawn_at(def_id: String, point: Vector2, level := -1, extra := {}) -> EnemyState:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return null
	var def := ContentDB.entry("enemies", def_id)
	var lv: Array = def.get("level", [1, 1])
	var slot := {"spec": {"enemy": def_id, "level": [level, level] if level > 0 else lv, "points": [[point.x, point.y]], "elite": extra.get("elite", false)},
		"index": -1, "point": point, "uid": 0, "timer": 0.0}
	var e := _spawn(slot)
	if e:
		e.summoned = true
		if extra.has("team"): e.team = str(extra.team)
		if extra.has("pet_owner"): e.pet_owner = str(extra.pet_owner)
	return e

func move_enemy(e: EnemyState, delta: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var next := e.plane + e.velocity * delta
	var b := rt.geometry.bounds
	next = next.clamp(b.position + Vector2(16, 6), b.end - Vector2(16, 12))
	if bool(e.def.get("flying", false)):
		e.plane = next
		return
	var surf: WalkSurface = rt.geometry.index.get(e.surface_id)
	if surf == null:
		e.plane = next
		return
	var ok_next := func(p: Vector2) -> bool:
		return surf.contains(p) and not rt.geometry.blocks_at(p, surf.height_at(p), surf.stratum) and not _in_portal(p)
	if ok_next.call(next): e.plane = next
	elif ok_next.call(Vector2(next.x, e.plane.y)): e.plane = Vector2(next.x, e.plane.y)
	elif ok_next.call(Vector2(e.plane.x, next.y)): e.plane = Vector2(e.plane.x, next.y)
	e.altitude = surf.height_at(e.plane)

func _in_portal(p: Vector2) -> bool:
	# Spawns and patrols never enter portal areas.
	for portal in game.room_rt.def.get("portals", []):
		var at: Array = portal.get("at", [0, 0])
		if absf(p.x - float(at[0])) < 40.0 and absf(p.y - float(at[1])) < 30.0: return true
	return false

func enemy_attack_release(e: EnemyState, attack: Dictionary) -> void:
	if attack.has("summon"):
		e.ai.summon_cd = 12.0
		for i in 2:
			var off := Vector2((i * 2 - 1) * 120, rng.randf_range(-30, 30))
			spawn_at(str(attack.summon), (e.plane + off).clamp(Vector2(60, 640), Vector2(game.room_rt.width() - 60, 940)), int(attack.get("summon_level", -1)))
		emit("enemy_summoned", {"enemy": e.uid})
		return
	if attack.has("buff_allies"):
		for other in game.room_rt.living_enemies():
			if other != e and other.plane.distance_to(e.plane) < 300:
				other.stats.attack = float(other.stats.attack) * (1.0 + float(attack.buff_allies))
		emit("enemy_buffed", {"enemy": e.uid})
		return
	if attack.has("projectile"):
		game.combat.spawn_enemy_projectile(e, attack)
		return
	if float(attack.get("dash", 0.0)) <= 0.0:
		game.combat.enemy_strike(e, attack)
		e.ai.hit_done = true

func stagger(e: EnemyState, seconds: float) -> void:
	e.ai.state = "stagger"
	e.ai.timer = seconds
	e.action = "hurt"
	e.action_time = 0.0

func _check_phases(e: EnemyState) -> void:
	var phases: Array = e.def.get("phases", [])
	for i in phases.size():
		if i <= int(e.ai.get("phase", -1)): continue
		var ph: Dictionary = phases[i]
		# A phase opens below its share of HP, or (for a boss that cannot be beaten yet) after its seconds in the fight.
		var timed := ph.has("after_s") and float(e.ai.get("engaged_t", 0.0)) >= float(ph.after_s)
		if timed or e.pools.hp <= e.pools.max_hp * float(ph.get("below", 0)):
			e.ai.phase = i
			match str(ph.get("action", "")):
				"dig_in":
					e.ai.state = "dug_in"
					e.ai.timer = float(ph.get("duration", 3.0))
				"drink_wine":
					e.pools.hp = minf(e.pools.max_hp, e.pools.hp + e.pools.max_hp * float(ph.get("heal", 0.1)))
					enemy_attack_release(e, {"summon": "mudwater_bandit"})
				"summon":
					enemy_attack_release(e, {"summon": _phase_summon(e, ph), "summon_level": int(ph.get("summon_level", -1))})
				"self_detonate":
					# S48: a telegraphed nascent-soul self-detonation. Get out of the ring before it bursts.
					e.ai.state = "detonating"
					e.invulnerable = true
					e.ai.timer = float(ph.get("windup", 3.0))
					e.ai.detonation = {"radius": float(ph.get("radius", 280)), "damage": float(ph.get("damage", 0.6))}
					emit("attack_started", {"actor": str(e.uid), "enemy": true, "attack": "soul_detonation", "windup": float(ph.get("windup", 3.0)),
						"facing": e.facing, "radius": float(ph.get("radius", 280))})
				"enrage":
					# The last stand: shorter pauses between attacks and harder blows.
					e.ai.enraged = {"cd": float(ph.get("cooldown", 0.7)), "damage": float(ph.get("damage", 1.25))}
					if ph.has("summon"): enemy_attack_release(e, {"summon": str(ph.summon)})
			emit("boss_phase", {"enemy": e.uid, "phase": i + 1, "action": str(ph.get("action", ""))})

## The nascent soul bursts: everyone in the ring takes a share of max HP (guarding halves it, a dodge slips it) and
## the boss is gone; the fight is won, the loot still falls.
func boss_detonate(e: EnemyState) -> void:
	game.combat.resolve_boss_detonation(e)

## Who a summoning phase calls: the phase's own "summon", else the boss's summoning attack.
func _phase_summon(e: EnemyState, ph: Dictionary) -> String:
	if ph.has("summon"): return str(ph.summon)
	for a in e.def.get("attacks", []):
		if a.has("summon"): return str(a.summon)
	return "paper_talisman_ghost"

func _eel(e: EnemyState, delta: float) -> void:
	# The Hollowed Eel cannot be hurt; it surfaces from the river and lunges.
	e.invulnerable = true
	e.ai.timer = float(e.ai.timer) - delta
	var tgt := EnemyBrain.target_position(self, e)
	match str(e.ai.state):
		"idle", "patrol", "aggro":
			e.action = "idle"
			e.hover = 40.0
			if not tgt.is_empty(): e.plane.x = move_toward(e.plane.x, tgt.pos.x, 60.0 * delta)
			if float(e.ai.timer) <= 0.0 and not tgt.is_empty():
				e.ai.state = "windup"
				e.ai.timer = 1.0
				e.facing = 1 if tgt.pos.x >= e.plane.x else -1
				emit("attack_started", {"actor": str(e.uid), "enemy": true, "attack": "lunge", "windup": 1.0, "facing": e.facing})
		"windup":
			e.action = "windup"
			if float(e.ai.timer) <= 0.0:
				e.ai.state = "attack"
				e.ai.timer = 0.5
				game.combat.enemy_strike(e, e.def.attacks[0])
		"attack":
			e.action = "attack"
			if float(e.ai.timer) <= 0.0:
				e.ai.state = "idle"
				e.ai.timer = rng.randf_range(3.0, 5.0)

## Defeat (Combat calls this when HP reaches 0 and announces actor_defeated with the
## payload returned here). World rolls loot on actor_defeated; Enemies then marks field bosses.
func defeat(e: EnemyState, killer: String) -> Dictionary:
	if not e.alive: return {}
	e.alive = false
	e.action = "death"
	e.action_time = 0.0
	e.dead_time = 0.0
	var rt: RoomRuntime = game.room_rt
	for slot in rt.spawn_slots:
		if int(slot.uid) == e.uid:
			slot.uid = 0
			var spec: Dictionary = slot.spec
			slot.timer = 180.0 if e.elite else float(spec.get("respawn_s", rng.randf_range(7.0, 12.0)))
			if spec.get("field_boss", false):
				var timers: Dictionary = game.account.rooms.get("field_boss_timers", {})
				timers[e.def_id] = Clock.now_utc() + float(e.def.get("respawn_min", 45)) * 60.0
				game.account.rooms["field_boss_timers"] = timers
				slot.timer = 99999.0
	var payload := {"victim": str(e.uid), "victim_kind": "enemy", "def": e.def_id, "level": e.level, "role": e.role, "elite": e.elite,
		"killer": killer, "room": rt.room_id, "x": e.plane.x, "y": e.plane.y, "alt": e.altitude, "first_hit_by_player": e.first_hit_by_player,
		"summoned": e.summoned}
	return payload

func _flee(e: EnemyState) -> void:
	var c = game.active()
	if c != null:
		var drop := LootRules.roll(str(e.def.get("loot", e.def_id)), Rng.stream(c.id, "loot"), e.level, 0.0, 0.0, {"no_equipment": true})
		game.world._drop_loot(c, drop, e.plane, e.altitude)
	emit("boss_fled", {"enemy": e.uid, "def": e.def_id, "room": game.room_rt.room_id})
	release(e)

## Remove a monster without a defeat (tamed or fled): no loot, no kill credit; its spawn slot refills.
func release(e: EnemyState) -> void:
	if not e.alive: return
	e.alive = false
	e.action = "death"
	e.dead_time = 0.0
	for slot in game.room_rt.spawn_slots:
		if int(slot.uid) == e.uid:
			slot.uid = 0
			slot.timer = float(slot.spec.get("respawn_s", 12.0))
	emit("actor_released", {"uid": e.uid, "def": e.def_id})

func end_spar(e: EnemyState, winner_actor: String) -> void:
	e.alive = false
	e.action = "hurt"
	e.dead_time = 0.8
	game.combat.end_spar(game.active_id)
	var c = game.active()
	if c: c.pools.hp = maxf(c.pools.hp, c.pools.max_hp)
	emit("spar_ended", {"actor": game.active_id, "opponent": e.def_id, "winner": "player" if winner_actor.begins_with("c") else "opponent",
		"room": game.room_rt.room_id})

func start_spar(def_id: String, point: Vector2, level := -1) -> EnemyState:
	game.combat.begin_spar(game.active_id)
	var e := spawn_at(def_id, point, level)
	if e:
		e.ai.state = "aggro"
		e.ai.timer = 1.0
		emit("spar_started", {"actor": game.active_id, "opponent": def_id})
	return e

## The player lost a spar at 10% HP: the opponent bows out and nobody is hurt.
func player_lost_spar() -> void:
	if game.room_rt == null: return
	for e in game.room_rt.living_enemies():
		if e.def.get("spar", false):
			e.alive = false
			e.dead_time = 0.8
			game.combat.end_spar(game.active_id)
			var c = game.active()
			if c: c.pools.hp = c.pools.max_hp
			emit("spar_ended", {"actor": game.active_id, "opponent": e.def_id, "winner": "opponent", "room": game.room_rt.room_id})
			return
