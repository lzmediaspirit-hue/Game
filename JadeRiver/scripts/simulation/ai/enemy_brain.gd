class_name EnemyBrain
extends RefCounted
## S13 · Monster AI: idle → patrol → aggro (on sight or hit) → wind-up (readable 0.3–0.6 s tell) → attack → recover →
## flee/return. Monsters never follow through portals; leaving the 600-unit leash resets them. A melee monster that
## cannot reach its target takes half damage from it after 2 s and goes home after 6 s, healing 10% a second (S43
## rule 11).
##
## The brains' shared rules (audit 45, S11): TopdownBrain steers the states that look and move (idle, patrol, aggro,
## flee, return) on the height grid, and AllyBrain moves allies with the same hops, so both call EnemyBrain's public
## functions: the target and sight, noticing and giving up, the wind-up and the chase speed, the state and its timer
## (set_state), wandering, the choice of attack, and the hops (start_hop, hop). EnemyBrain itself runs the states on
## their own clocks: the wind-up, the blow, the recovery and the rest.

static func target_position(auth, e: EnemyState) -> Dictionary:
	var c = auth.game.active()
	if c == null or auth.game.combat.is_wounded(c.id): return {}
	var st: ActorState = auth.game.actor_state(c.id)
	if st == null: return {}
	if c.pools.has_status("spawn_protection") and e.ai.state in ["idle", "patrol"]: return {}
	if in_sanctuary(auth, st.plane) and not e.is_boss(): return {}
	# S48 Phantom Double: an illusion of the player draws the foes near it (bosses see through it).
	var d: Dictionary = auth.game.combat.decoy_for(e, c.id)
	if not d.is_empty(): return {"id": "decoy", "pos": Vector2(float(d.x), float(d.y)), "alt": float(d.alt)}
	return {"id": c.id, "pos": st.plane, "alt": st.altitude}

## Shrines are sanctuaries: monsters neither aggro on nor chase a player standing by one,
## so nobody is killed again while resting after a revival. A room's object can hold one too, of its own
## `sanctuary` radius (the Hollow Night's lamp at Aunt Ping's door).
static func in_sanctuary(auth, p: Vector2) -> bool:
	var rt = auth.game.room_rt
	if rt == null: return false
	for s in sanctuaries(rt.def):
		if p.distance_to(s[0]) <= float(s[1]): return true
	return false

## A room's sanctuaries as [[point, radius]], its shrines' and its objects' own, in its objects' order: every foe asks
## each tick, so they are gathered once for the room's definition (not looked for through all its things each time).
static var _sanct_def: Dictionary = {}
static var _sanct: Array = []
static func sanctuaries(def: Dictionary) -> Array:
	if is_same(def, _sanct_def): return _sanct
	var r := float(ContentDB.stat_const("combat.shrine_sanctuary", 240))
	var out: Array = []
	for o in def.get("objects", []):
		var sr := r if str(o.get("type", "")) == "shrine" else float(o.get("sanctuary", 0.0))
		if sr > 0.0:
			var at: Array = o.get("at", [0, 0])
			out.append([Vector2(float(at[0]), float(at[1])), sr])
	_sanct_def = def
	_sanct = out
	return out

## Sight aggro stops at a crowd: a phone screen cannot read a pile of foes at once. While an elite or boss is
## fighting the player, or `combat.sight_aggro_cap` ordinary foes already are, another ordinary monster that
## sees the player stays put and joins only when struck. Elites, bosses and anything summoned (a boss's adds,
## an event's waves) always come: those crowds are the fight.
static func may_join(auth, e: EnemyState) -> bool:
	if e.elite or e.is_boss() or e.summoned or e.team != "enemy" or auth.game.room_rt == null: return true
	var cap := int(ContentDB.stat_const("combat.sight_aggro_cap", 2))
	var n := 0
	for o in auth.game.room_rt.living_enemies():
		if o == e or o.team != "enemy" or not str(o.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"]: continue
		if o.elite or o.is_boss(): return false
		n += 1
	return n < cap

const ATTACK_CD := {"slow_melee": 1.8, "melee": 1.1, "charger": 1.5, "ranged": 1.6, "ranged_melee": 1.4, "leaper": 1.5, "flyer": 1.4,
	"flyer_ranged": 1.6, "burrower": 1.6, "caster": 1.8, "guard_counter": 1.4, "humanoid": 1.0, "duelist": 0.9, "snapper": 1.6}

static func think(auth, e: EnemyState, delta: float) -> void:
	var ai := e.ai
	var def := e.def
	var profile := str(def.get("ai", {}).get("profile", "melee"))
	ai.timer = float(ai.timer) - delta
	if not e.hop.is_empty():
		hop(auth, e, delta)   # a jump, drop or climb finishes before anything else
		return
	# S49: a named foe who has yielded kneels and waits for the victor's judgement.
	if ai.get("surrendered", false):
		e.velocity = Vector2.ZERO
		e.action = "idle"
		return
	if e.pools.blocked("move") and ai.state not in ["dead"]:
		e.velocity = Vector2.ZERO
		if ai.state in ["windup", "attack"]:
			ai.state = "recover"
			ai.timer = 0.4
		return
	if def.get("passive", false):
		wander(auth, e, delta, 0.4)
		return
	# Redesign Phase 2: noticing, chasing, fleeing and going home steer on the plane (TopdownBrain); the wind-up, the
	# blow and the recovery below run on their own clocks.
	if str(ai.state) in TopdownBrain.STATES:
		TopdownBrain.think(auth, e, delta)
		return
	match str(ai.state):
		"windup":
			e.velocity = Vector2.ZERO
			e.action = "windup"
			if float(ai.timer) <= 0.0:
				var attack2: Dictionary = def.attacks[int(ai.attack)]
				set_state(auth, e, "attack", float(attack2.get("active_s", 0.18)) + 0.12)
				ai.dash_left = float(attack2.get("dash", 0.0))
				ai.repeat = int(attack2.get("repeat", 1)) - 1
				auth.enemy_attack_release(e, attack2)
		"attack":
			e.action = "attack"
			if float(ai.dash_left) > 0.0:
				var step := minf(float(ai.dash_left), 520.0 * delta)
				ai.dash_left = float(ai.dash_left) - step
				e.velocity = e.aim_dir() * step / delta
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
					set_state(auth, e, "windup", 0.25)
					return
				set_state(auth, e, "recover", float(def.attacks[int(ai.attack)].get("recover_s", 0.45)))
		"recover", "stagger":
			e.velocity = Vector2.ZERO
			e.action = "idle" if ai.state == "recover" else "hurt"
			if float(ai.timer) <= 0.0:
				# Pause between attacks so every monster's rhythm stays readable (S13).
				var cd := float(def.get("ai", {}).get("attack_cd", ATTACK_CD.get(str(def.get("ai", {}).get("profile", "melee")), 1.0)))
				if ai.has("enraged"): cd *= float(ai.enraged.cd)
				set_state(auth, e, "aggro", cd * auth.rng.randf_range(0.8, 1.2))
		"dug_in":
			e.velocity = Vector2.ZERO
			e.action = "hurt"
			e.invulnerable = true
			if float(ai.timer) <= 0.0:
				e.invulnerable = false
				set_state(auth, e, "aggro", 0.2)
		"detonating":
			# S48: a cornered cultivator burns his nascent soul; the blast comes when the timer runs out.
			e.velocity = Vector2.ZERO
			e.action = "windup"
			e.invulnerable = true
			if float(ai.timer) <= 0.0: auth.boss_detonate(e)
		"guard":
			e.velocity = Vector2.ZERO
			e.action = "windup"
			if float(ai.timer) <= 0.0: set_state(auth, e, "aggro", 0.0)

## How far a foe notices the player (its aggro range, halved by Concealment) and whether the player is hidden from it
## (a fuelled Concealment formation or a Veil Talisman, until struck: S16, S47).
static func sight(auth, e: EnemyState) -> Dictionary:
	var aggro_r := float(e.def.get("ai", {}).get("aggro_range", 200))
	var c = auth.game.active()
	if c != null and "concealment" in c.cultivator.secret_arts: aggro_r *= 0.5
	var hidden: bool = c != null and e.team == "enemy" and (auth.game.workshop.formation_effect(c, "conceal") > 0.0 or c.pools.has_status("veiled"))
	return {"range": 0.0 if hidden else aggro_r, "hidden": hidden}

## An idle or patrolling foe turns on the player it sees (when the crowd cap lets it) or that struck it.
static func notices(auth, e: EnemyState, tgt: Dictionary, sees: bool) -> bool:
	if not ((sees and may_join(auth, e)) or e.threat.size() > 0): return false
	set_state(auth, e, "aggro", 0.0)
	auth.emit("enemy_aggro", {"enemy": e.uid, "target": tgt.id, "def": e.def_id})
	return true

## A foe in a fight gives up (the target gone or hidden, past the 600 leash: home) or turns to flee at its flee share.
static func gives_up(auth, e: EnemyState, tgt: Dictionary, hidden: bool) -> bool:
	if tgt.is_empty() or (hidden and e.threat.is_empty()):
		set_state(auth, e, "return", 6.0)
		return true
	if e.plane.distance_to(e.spawn_point) > float(ContentDB.stat_const("combat.leash", 600)) and not e.is_boss():
		e.threat.clear()
		set_state(auth, e, "return", 6.0)
		return true
	var flee := float(e.def.get("ai", {}).get("flee_below", 0.0))
	if flee > 0.0 and e.pools.hp < e.pools.max_hp * flee and not e.ai.get("fled", false):
		e.ai.fled = true
		set_state(auth, e, "flee", 2.5)
		return true
	return false

## Begin an attack's readable wind-up (S13).
static func wind_up(auth, e: EnemyState, attacks: Array, attack: Dictionary) -> void:
	e.ai.attack = attacks.find(attack)
	e.ai.counter = false
	set_state(auth, e, "windup", float(attack.windup_s))
	e.ai.hit_done = false
	auth.emit("attack_started", {"actor": str(e.uid), "enemy": true, "attack": attack.id, "windup": float(attack.windup_s), "facing": e.facing})

## Its chase speed: slowed by a slow, a stronger Presence (S28) and a Restraint formation (S16).
static func chase_speed(auth, e: EnemyState) -> float:
	var speed := float(e.def.get("ai", {}).get("move_speed", 90)) * (0.6 if e.pools.has_status("slow") else 1.0) * (1.0 - FieldAuthority.enemy_loss(e))
	var c = auth.game.active()
	if c != null and e.team == "enemy": speed *= 1.0 - clampf(auth.game.workshop.formation_effect(c, "enemy_slow"), 0.0, 0.9)
	return speed

## Which of its attacks a foe winds up next (an index into `attacks`): ranged when far, melee when close, a summon or a
## buff on its own timer and chance.
static func choose_attack(auth, e: EnemyState, attacks: Array) -> int:
	if attacks.size() == 1: return 0
	# Prefer ranged attacks when far, melee when close; summons on a slow timer.
	var tgt := target_position(auth, e)
	var dist := 0.0
	if not tgt.is_empty(): dist = (tgt.pos as Vector2).distance_to(e.plane)   # how far the target is, on the plane
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

## Walk toward its patrol spot at `speed_factor` of its pace; there (or out of time) it stands idle a while.
static func wander(auth, e: EnemyState, delta: float, speed_factor: float) -> void:
	var tx := float(e.ai.get("patrol_x", e.spawn_point.x))
	var ty := float(e.ai.get("patrol_y", e.spawn_point.y))
	var d := Vector2(tx, ty) - e.plane
	if d.length() < 6.0 or float(e.ai.timer) <= 0.0:
		set_state(auth, e, "idle", auth.rng.randf_range(1.0, 3.0))
		return
	e.facing = 1 if d.x >= 0 else -1
	e.velocity = d.normalized() * float(e.def.get("ai", {}).get("move_speed", 90)) * speed_factor
	e.action = "walk"
	auth.move_enemy(e, delta)

# ------------------------------------------------------------------ S43 rule 11: reach and the hops
## The species' movement data: its jump, whether it climbs, flies or drops.
static func movement_of(e: EnemyState) -> Dictionary:
	var fly := bool(e.def.get("flying", false))
	return e.def.get("movement", {"jump": 0, "climb": false, "fly": fly, "drop": not fly})

## S43 rule 11: after 6 s unable to reach its target a melee foe gives up and goes home, healing on the way.
static func out_of_reach_too_long(auth, e: EnemyState) -> bool:
	if float(e.ai.get("unreach", 0.0)) < 6.0: return false
	e.threat.clear()
	e.ai.leashed = true
	auth.emit("enemy_leashed", {"enemy": e.uid, "reason": "out_of_reach"})
	set_state(auth, e, "return", 8.0)
	return true

## A hop along an edge (a jump, a drop, a climb, a walk), on gravity `g` with the jump `impulse` (> 0; else the
## species' own): TopdownBrain passes the height grid's.
static func start_hop(_auth, e: EnemyState, edge: Dictionary, g := MovementSolver.GRAVITY, impulse := -1.0) -> void:
	var a0 := e.altitude
	var a1 := float(edge.to_alt)
	var h := {"edge": edge, "t": 0.0, "from": e.plane, "to": edge.to_pt, "a0": a0, "a1": a1, "kind": str(edge.kind), "v": 0.0, "T": 0.3, "g": g}
	match str(edge.kind):
		"jump":
			var v := impulse if impulse > 0.0 else float(movement_of(e).get("jump", 530))
			h.v = v
			h.T = (v + sqrt(maxf(0.0, v * v - 2.0 * g * (a1 - a0)))) / g
		"drop": h.T = 0.1 + sqrt(2.0 * maxf(1.0, a0 - a1) / g)
		"climb": h.T = absf(a1 - a0) / 80.0 + 0.2
		"walk": h.T = maxf(0.05, (e.plane as Vector2).distance_to(edge.to_pt) / maxf(1.0, float(e.def.get("ai", {}).get("move_speed", 90))))
	e.hop = h
	e.facing = 1 if (edge.to_pt as Vector2).x >= e.plane.x else -1

## A hop under way (start_hop): along its arc to the edge's landing, then onto the surface it lands on.
static func hop(auth, e: EnemyState, delta: float) -> void:
	var h := e.hop
	h.t = float(h.t) + delta
	var t := float(h.t)
	var k := clampf(t / maxf(0.01, float(h.T)), 0.0, 1.0)
	e.plane = (h.from as Vector2).lerp(h.to, k)
	var g := float(h.get("g", MovementSolver.GRAVITY))
	match str(h.kind):
		"jump": e.altitude = float(h.a0) + float(h.v) * t - 0.5 * g * t * t
		"drop": e.altitude = maxf(float(h.a1), float(h.a0) - 0.5 * g * maxf(0.0, t - 0.1) * maxf(0.0, t - 0.1))
		_: e.altitude = lerpf(float(h.a0), float(h.a1), k)
	e.velocity = Vector2.ZERO
	e.action = "walk"
	if k >= 1.0:
		var edge: Dictionary = h.edge
		var s: WalkSurface = auth.game.room_rt.geometry.index.get(str(edge.to)) if auth.game.room_rt else null
		e.surface_id = str(edge.to)
		e.altitude = s.height_at(e.plane) if s else float(h.a1)
		e.hop = {}

## Into `state`, for `timer` seconds; its action's clock starts again.
static func set_state(_auth, e: EnemyState, state: String, timer: float) -> void:
	e.ai.state = state
	e.ai.timer = timer
	e.action_time = 0.0
