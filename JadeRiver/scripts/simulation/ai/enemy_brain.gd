class_name EnemyBrain
extends RefCounted
## S13 · Monster AI: idle → patrol (own platform) → aggro (on sight or hit) →
## wind-up (readable 0.3–0.6 s tell) → attack → recover → flee/return. Monsters
## never follow through portals; leaving the 600-unit leash resets them.
## S43 rule 11: a target on another surface is chased along the room's navigation graph (walk, jump,
## drop and climb edges, by the species' movement data). A melee monster that cannot reach its target
## takes half damage from it after 2 s and goes home after 6 s, healing 10% a second; flyers ignore the graph.

static func target_position(auth, e: EnemyState) -> Dictionary:
	var c = auth.game.active()
	if c == null or auth.game.combat.is_wounded(c.id): return {}
	var st: ActorState = auth.game.actor_state(c.id)
	if st == null: return {}
	if c.pools.has_status("spawn_protection") and e.ai.state in ["idle", "patrol"]: return {}
	if in_sanctuary(auth, st.plane) and not e.is_boss(): return {}
	return {"id": c.id, "pos": st.plane, "alt": st.altitude}

## Shrines are sanctuaries: monsters neither aggro on nor chase a player standing by one,
## so nobody is killed again while resting after a revival.
static func in_sanctuary(auth, p: Vector2) -> bool:
	var rt = auth.game.room_rt
	if rt == null: return false
	var r := float(ContentDB.stat_const("combat.shrine_sanctuary", 240))
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) == "shrine":
			var at: Array = o.get("at", [0, 0])
			if p.distance_to(Vector2(float(at[0]), float(at[1]))) <= r: return true
	return false

const ATTACK_CD := {"slow_melee": 1.8, "melee": 1.1, "charger": 1.5, "ranged": 1.6, "ranged_melee": 1.4, "leaper": 1.5, "flyer": 1.4,
	"flyer_ranged": 1.6, "burrower": 1.6, "caster": 1.8, "guard_counter": 1.4, "humanoid": 1.0, "duelist": 0.9, "snapper": 1.6}

static func think(auth, e: EnemyState, delta: float) -> void:
	var ai := e.ai
	var def := e.def
	var profile := str(def.get("ai", {}).get("profile", "melee"))
	ai.timer = float(ai.timer) - delta
	if not e.hop.is_empty():
		_hop(auth, e, delta)   # a jump, drop or climb finishes before anything else
		return
	if e.pools.blocked("move") and ai.state not in ["dead"]:
		e.velocity = Vector2.ZERO
		if ai.state in ["windup", "attack"]:
			ai.state = "recover"
			ai.timer = 0.4
		return
	if def.get("passive", false):
		_wander(auth, e, delta, 0.4)
		return
	var tgt := target_position(auth, e)
	var aggro_r := float(def.get("ai", {}).get("aggro_range", 200))
	var c = auth.game.active()
	if c != null and "concealment" in c.cultivator.secret_arts: aggro_r *= 0.5
	# A fuelled Concealment formation hides the player until struck; Restraint slows monsters (S16).
	var hidden: bool = c != null and e.team == "enemy" and (auth.game.workshop.formation_effect(c, "conceal") > 0.0 or c.pools.has_status("veiled"))   # S47 Veil Talisman
	if hidden: aggro_r = 0.0
	match str(ai.state):
		"idle", "patrol":
			if not tgt.is_empty():
				var d: Vector2 = tgt.pos - e.plane
				if (absf(d.x) <= aggro_r and absf(d.y) <= 140.0) or e.threat.size() > 0:
					_set_state(auth, e, "aggro", 0.0)
					auth.emit("enemy_aggro", {"enemy": e.uid, "target": tgt.id, "def": e.def_id})
					return
			if ai.state == "idle":
				e.velocity = Vector2.ZERO
				e.action = "idle"
				if float(ai.timer) <= 0.0:
					var span := float(def.get("ai", {}).get("patrol", 140))
					ai.patrol_x = e.spawn_point.x + auth.rng.randf_range(-span, span)
					ai.patrol_y = clampf(e.spawn_point.y + auth.rng.randf_range(-40, 40), 630, 950)
					_set_state(auth, e, "patrol", 4.0)
			else:
				_wander(auth, e, delta, 0.5)
		"aggro":
			if tgt.is_empty() or (hidden and e.threat.is_empty()):
				_set_state(auth, e, "return", 6.0)
				return
			if e.plane.distance_to(e.spawn_point) > float(ContentDB.stat_const("combat.leash", 600)) and not e.is_boss():
				e.threat.clear()
				_set_state(auth, e, "return", 6.0)
				return
			var flee := float(def.get("ai", {}).get("flee_below", 0.0))
			if flee > 0.0 and e.pools.hp < e.pools.max_hp * flee and not ai.get("fled", false):
				ai.fled = true
				_set_state(auth, e, "flee", 2.5)
				return
			var attacks: Array = def.get("attacks", [])
			if attacks.is_empty(): return
			if _chase_on_graph(auth, e, tgt, delta): return
			# Flyers ignore the graph: they sink or climb toward the height they hunt at.
			if bool(def.get("flying", false)): e.altitude = move_toward(e.altitude, maxf(0.0, float(tgt.get("alt", 0.0))), 120.0 * delta)
			var attack: Dictionary = attacks[_choose_attack(auth, e, attacks)]
			var reach := float(attack.hitbox.x[1])
			var d: Vector2 = tgt.pos - e.plane
			e.facing = 1 if d.x >= 0 else -1
			var keep := float(def.get("keep_distance", 0))
			var depth := float(attack.hitbox.get("depth", 26))
			if ai.get("counter", false):
				ai.timer = 0.0
				reach += 30.0
			var in_x := absf(d.x) <= reach + 14.0 and (keep <= 0.0 or absf(d.x) >= keep * 0.5 or reach > 200)
			var in_y := absf(d.y) <= depth * 0.8
			if bool(def.get("flying", false)): in_y = absf(d.y) <= depth * 0.8 + 10
			if in_x and in_y and float(ai.timer) <= 0.0:
				ai.attack = attacks.find(attack)
				ai.counter = false
				_set_state(auth, e, "windup", float(attack.windup_s))
				ai.hit_done = false
				auth.emit("attack_started", {"actor": str(e.uid), "enemy": true, "attack": attack.id, "windup": float(attack.windup_s), "facing": e.facing})
				return
			var speed := float(def.get("ai", {}).get("move_speed", 90)) * (0.6 if e.pools.has_status("slow") else 1.0)
			if c != null and e.team == "enemy": speed *= 1.0 - clampf(auth.game.workshop.formation_effect(c, "enemy_slow"), 0.0, 0.9)
			var want: Vector2 = Vector2.ZERO
			if keep > 0.0 and absf(d.x) < keep:
				want.x = -signf(d.x)
			elif not in_x:
				want.x = signf(d.x)
			if not in_y: want.y = signf(d.y)
			e.velocity = want.normalized() * speed if want != Vector2.ZERO else Vector2.ZERO
			e.action = "walk" if e.velocity != Vector2.ZERO else "idle"
			auth.move_enemy(e, delta)
		"windup":
			e.velocity = Vector2.ZERO
			e.action = "windup"
			if float(ai.timer) <= 0.0:
				var attack2: Dictionary = def.attacks[int(ai.attack)]
				_set_state(auth, e, "attack", float(attack2.get("active_s", 0.18)) + 0.12)
				ai.dash_left = float(attack2.get("dash", 0.0))
				ai.repeat = int(attack2.get("repeat", 1)) - 1
				auth.enemy_attack_release(e, attack2)
		"attack":
			e.action = "attack"
			if float(ai.dash_left) > 0.0:
				var step := minf(float(ai.dash_left), 520.0 * delta)
				ai.dash_left = float(ai.dash_left) - step
				e.velocity = Vector2(e.facing * step / delta, 0)
				auth.move_enemy(e, delta)
				if not ai.hit_done:
					auth.game.combat.enemy_strike(e, def.attacks[int(ai.attack)])
					ai.hit_done = true
			else:
				e.velocity = Vector2.ZERO
			if float(ai.timer) <= 0.0:
				if int(ai.get("repeat", 0)) > 0:
					ai.repeat = int(ai.repeat) - 1
					ai.hit_done = false
					var attack3: Dictionary = def.attacks[int(ai.attack)]
					ai.dash_left = float(attack3.get("dash", 0.0))
					_set_state(auth, e, "windup", 0.25)
					return
				_set_state(auth, e, "recover", float(def.attacks[int(ai.attack)].get("recover_s", 0.45)))
		"recover", "stagger":
			e.velocity = Vector2.ZERO
			e.action = "idle" if ai.state == "recover" else "hurt"
			if float(ai.timer) <= 0.0:
				# Pause between attacks so every monster's rhythm stays readable (S13).
				var cd := float(def.get("ai", {}).get("attack_cd", ATTACK_CD.get(str(def.get("ai", {}).get("profile", "melee")), 1.0)))
				if ai.has("enraged"): cd *= float(ai.enraged.cd)
				_set_state(auth, e, "aggro", cd * auth.rng.randf_range(0.8, 1.2))
		"flee":
			if tgt.is_empty() or float(ai.timer) <= 0.0:
				_set_state(auth, e, "aggro", 0.3)
				return
			var away: Vector2 = e.plane - tgt.pos
			e.facing = 1 if away.x >= 0 else -1
			e.velocity = Vector2(signf(away.x), 0) * float(def.get("ai", {}).get("move_speed", 90)) * 1.2
			e.action = "walk"
			auth.move_enemy(e, delta)
		"return":
			# Led home by the out-of-reach rule: heal 10% a second on the way (S43).
			if ai.get("leashed", false): e.pools.hp = minf(e.pools.max_hp, e.pools.hp + e.pools.max_hp * 0.1 * delta)
			if e.home_surface != "" and e.surface_id != e.home_surface and not bool(def.get("flying", false)):
				var home_path: Array = auth.game.room_rt.geometry.nav_path(e.surface_id, e.home_surface, movement_of(e))
				if not home_path.is_empty() and float(ai.timer) > 0.0:
					_follow_edge(auth, e, home_path[0], delta)
					return
				# No way back on foot: it slips home out of sight.
				e.surface_id = e.home_surface
				e.plane = e.spawn_point
				var hs: WalkSurface = auth.game.room_rt.geometry.index.get(e.home_surface)
				e.altitude = hs.height_at(e.plane) if hs else 0.0
			if bool(def.get("flying", false)) and e.home_surface != "":
				var home: WalkSurface = auth.game.room_rt.geometry.index.get(e.home_surface)
				if home: e.altitude = move_toward(e.altitude, home.height_at(e.spawn_point), 120.0 * delta)
			var back := e.spawn_point - e.plane
			if back.length() < 12.0 or float(ai.timer) <= 0.0:
				e.pools.hp = e.pools.max_hp
				e.threat.clear()
				ai.leashed = false
				ai.unreach = 0.0
				_set_state(auth, e, "idle", 1.0)
				return
			e.facing = 1 if back.x >= 0 else -1
			e.velocity = back.normalized() * float(def.get("ai", {}).get("move_speed", 90))
			e.action = "walk"
			auth.move_enemy(e, delta)
		"dug_in":
			e.velocity = Vector2.ZERO
			e.action = "hurt"
			e.invulnerable = true
			if float(ai.timer) <= 0.0:
				e.invulnerable = false
				_set_state(auth, e, "aggro", 0.2)
		"guard":
			e.velocity = Vector2.ZERO
			e.action = "windup"
			if float(ai.timer) <= 0.0: _set_state(auth, e, "aggro", 0.0)

static func _choose_attack(auth, e: EnemyState, attacks: Array) -> int:
	if attacks.size() == 1: return 0
	# Prefer ranged attacks when far, melee when close; summons on a slow timer.
	var tgt := target_position(auth, e)
	var dist := absf(tgt.pos.x - e.plane.x) if not tgt.is_empty() else 0.0
	var best := 0
	for i in attacks.size():
		var a: Dictionary = attacks[i]
		if a.has("summon"):
			if float(e.ai.get("summon_cd", 0.0)) <= 0.0 and e.pools.hp < e.pools.max_hp * 0.6:
				return i
			continue
		if a.has("buff_allies"):
			if auth.rng.randf() < 0.15: return i
			continue
		if dist > 140.0 and float(a.hitbox.x[1]) > 200.0: return i
		if dist <= 140.0 and float(a.hitbox.x[1]) <= 200.0: best = i
	return best

static func _wander(auth, e: EnemyState, delta: float, speed_factor: float) -> void:
	var tx := float(e.ai.get("patrol_x", e.spawn_point.x))
	var ty := float(e.ai.get("patrol_y", e.spawn_point.y))
	var d := Vector2(tx, ty) - e.plane
	if d.length() < 6.0 or float(e.ai.timer) <= 0.0:
		_set_state(auth, e, "idle", auth.rng.randf_range(1.0, 3.0))
		return
	e.facing = 1 if d.x >= 0 else -1
	e.velocity = d.normalized() * float(e.def.get("ai", {}).get("move_speed", 90)) * speed_factor
	e.action = "walk"
	auth.move_enemy(e, delta)

# ------------------------------------------------------------------ S43 rule 11: moving between surfaces
static func movement_of(e: EnemyState) -> Dictionary:
	var fly := bool(e.def.get("flying", false))
	return e.def.get("movement", {"jump": 0, "climb": false, "fly": fly, "drop": not fly})

static func _has_ranged(e: EnemyState) -> bool:
	for a in e.def.get("attacks", []):
		if float(a.get("hitbox", {}).get("x", [0, 0])[1]) > 200.0: return true
	return false

## Chase a target standing on another surface along the navigation graph. Returns true when this frame's
## movement is handled here (following an edge, waiting beneath an unreachable target, or giving up).
static func _chase_on_graph(auth, e: EnemyState, tgt: Dictionary, delta: float) -> bool:
	var mv := movement_of(e)
	if bool(mv.get("fly", false)) or bool(e.def.get("flying", false)) or e.is_boss() or auth.game.room_rt == null: return false
	var geo: ZoneGeometry = auth.game.room_rt.geometry
	var tpos: Vector2 = tgt.pos
	var talt := float(tgt.get("alt", 0.0))
	var under: WalkSurface = geo.surface_under(tpos, talt)
	var above := talt - (under.height_at(tpos) if under else 0.0)
	var tsurf := under.id if under else ""
	var path: Array = []
	var reachable := above <= 60.0
	if reachable and tsurf != "" and tsurf != e.surface_id:
		path = geo.nav_path(e.surface_id, tsurf, mv)
		reachable = not path.is_empty()
	if reachable:
		e.ai.unreach = 0.0
		if path.is_empty(): return false
		# Archers and throwers shoot from where they stand while the target is in range.
		if _has_ranged(e) and absf(tpos.x - e.plane.x) <= 320.0: return false
		_follow_edge(auth, e, path[0], delta)
		return true
	e.ai.unreach = float(e.ai.get("unreach", 0.0)) + delta
	if _has_ranged(e): return false   # imps and apes throw rubble up at it
	if float(e.ai.unreach) >= 6.0:
		e.threat.clear()
		e.ai.leashed = true
		auth.emit("enemy_leashed", {"enemy": e.uid, "reason": "out_of_reach"})
		_set_state(auth, e, "return", 8.0)
		return true
	# Pace beneath it, waiting for it to come down.
	var dx := tpos.x - e.plane.x
	e.facing = 1 if dx >= 0 else -1
	var speed := float(e.def.get("ai", {}).get("move_speed", 90))
	e.velocity = Vector2(signf(dx), 0) * speed if absf(dx) > 30.0 else Vector2.ZERO
	e.action = "walk" if e.velocity != Vector2.ZERO else "idle"
	auth.move_enemy(e, delta)
	return true

## Walk to an edge's take-off point, then hop along it.
static func _follow_edge(auth, e: EnemyState, edge: Dictionary, delta: float) -> void:
	var d: Vector2 = (edge.from_pt as Vector2) - e.plane
	if d.length() <= 10.0:
		_start_hop(auth, e, edge)
		return
	var speed := float(e.def.get("ai", {}).get("move_speed", 90))
	e.facing = 1 if d.x >= 0 else -1
	e.velocity = d.normalized() * speed
	e.action = "walk"
	var before := e.plane
	auth.move_enemy(e, delta)
	if e.plane.distance_to(before) < 0.01: _start_hop(auth, e, edge)   # blocked short of the spot: go from here

static func _start_hop(_auth, e: EnemyState, edge: Dictionary) -> void:
	var g := MovementSolver.GRAVITY
	var a0 := e.altitude
	var a1 := float(edge.to_alt)
	var h := {"edge": edge, "t": 0.0, "from": e.plane, "to": edge.to_pt, "a0": a0, "a1": a1, "kind": str(edge.kind), "v": 0.0, "T": 0.3}
	match str(edge.kind):
		"jump":
			var v := float(movement_of(e).get("jump", 530))
			h.v = v
			h.T = (v + sqrt(maxf(0.0, v * v - 2.0 * g * (a1 - a0)))) / g
		"drop": h.T = 0.1 + sqrt(2.0 * maxf(1.0, a0 - a1) / g)
		"climb": h.T = absf(a1 - a0) / 80.0 + 0.2
		"walk": h.T = maxf(0.05, (e.plane as Vector2).distance_to(edge.to_pt) / maxf(1.0, float(e.def.get("ai", {}).get("move_speed", 90))))
	e.hop = h
	e.facing = 1 if (edge.to_pt as Vector2).x >= e.plane.x else -1

static func _hop(auth, e: EnemyState, delta: float) -> void:
	var h := e.hop
	h.t = float(h.t) + delta
	var t := float(h.t)
	var k := clampf(t / maxf(0.01, float(h.T)), 0.0, 1.0)
	e.plane = (h.from as Vector2).lerp(h.to, k)
	match str(h.kind):
		"jump": e.altitude = float(h.a0) + float(h.v) * t - 0.5 * MovementSolver.GRAVITY * t * t
		"drop": e.altitude = maxf(float(h.a1), float(h.a0) - 0.5 * MovementSolver.GRAVITY * maxf(0.0, t - 0.1) * maxf(0.0, t - 0.1))
		_: e.altitude = lerpf(float(h.a0), float(h.a1), k)
	e.velocity = Vector2.ZERO
	e.action = "walk"
	if k >= 1.0:
		var edge: Dictionary = h.edge
		var s: WalkSurface = auth.game.room_rt.geometry.index.get(str(edge.to)) if auth.game.room_rt else null
		e.surface_id = str(edge.to)
		e.altitude = s.height_at(e.plane) if s else float(h.a1)
		e.hop = {}

static func _set_state(_auth, e: EnemyState, state: String, timer: float) -> void:
	e.ai.state = state
	e.ai.timer = timer
	e.action_time = 0.0
