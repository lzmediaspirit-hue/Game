class_name EnemyBrain
extends RefCounted
## S13 · Monster AI: idle → patrol (own platform) → aggro (on sight or hit) →
## wind-up (readable 0.3–0.6 s tell) → attack → recover → flee/return. Monsters
## never follow through portals; leaving the 600-unit leash resets them.

static func target_position(auth, e: EnemyState) -> Dictionary:
	var c = auth.game.active()
	if c == null or auth.game.combat.is_wounded(c.id): return {}
	var st: ActorState = auth.game.actor_state(c.id)
	if st == null: return {}
	if c.pools.has_status("spawn_protection") and e.ai.state in ["idle", "patrol"]: return {}
	return {"id": c.id, "pos": st.plane, "alt": st.altitude}

const ATTACK_CD := {"slow_melee": 1.8, "melee": 1.1, "charger": 1.5, "ranged": 1.6, "ranged_melee": 1.4, "leaper": 1.5, "flyer": 1.4,
	"flyer_ranged": 1.6, "burrower": 1.6, "caster": 1.8, "guard_counter": 1.4, "humanoid": 1.0, "duelist": 0.9, "snapper": 1.6}

static func think(auth, e: EnemyState, delta: float) -> void:
	var ai := e.ai
	var def := e.def
	var profile := str(def.get("ai", {}).get("profile", "melee"))
	ai.timer = float(ai.timer) - delta
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
			if tgt.is_empty():
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
			var back := e.spawn_point - e.plane
			if back.length() < 12.0 or float(ai.timer) <= 0.0:
				e.pools.hp = e.pools.max_hp
				e.threat.clear()
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

static func _set_state(_auth, e: EnemyState, state: String, timer: float) -> void:
	e.ai.state = state
	e.ai.timer = timer
	e.action_time = 0.0
