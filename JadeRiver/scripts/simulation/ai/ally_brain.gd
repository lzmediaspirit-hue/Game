class_name AllyBrain
extends RefCounted
## CompanionBrain / PetBrain core (S22, S26): follow the owner, pick the owner's
## nearest enemy, strike with a readable wind-up, retreat at low HP, sit while the
## owner meditates. Allies never block portals and never enter portal areas.

static func think(game, a: EnemyState, delta: float, attack_power: float, reach: float) -> void:
	var c = game.active()
	var st: ActorState = game.actor_state(c.id) if c else null
	if st == null: return
	a.ai.timer = float(a.ai.timer) - delta
	a.action_time += delta
	if a.flash > 0.0: a.flash = maxf(0.0, a.flash - delta)
	if a.ai.state == "downed":
		a.action = "death" if a.action_time < 0.8 else "idle"
		a.hidden = a.action_time > 0.8
		if float(a.ai.timer) <= 0.0 or c.cultivator.meditating:
			a.ai.state = "follow"
			a.hidden = false
			a.pools.hp = a.pools.max_hp
		return
	if c.cultivator.meditating:
		a.action = "idle"
		a.velocity = Vector2.ZERO
		a.pools.hp = minf(a.pools.max_hp, a.pools.hp + a.pools.max_hp * 0.05 * delta)
		return
	var side := -1 if int(game.combat.timeline(c.id).facing) > 0 else 1
	var home = st.plane + Vector2(side * float(a.ai.get("offset", 60)), float(a.ai.get("depth_offset", 10)))
	var target: EnemyState = null
	var best := 260.0
	for e in game.room_rt.living_enemies():
		if e.team != "enemy" or e.hidden or e.def.get("passive", false): continue
		var d = e.plane.distance_to(st.plane)
		if d < best:
			best = d
			target = e
	match str(a.ai.state):
		"windup":
			a.velocity = Vector2.ZERO
			a.action = "windup"
			if float(a.ai.timer) <= 0.0:
				var tgt: EnemyState = game.room_rt.enemies.get(int(a.ai.get("target_uid", -1)))
				if tgt != null and tgt.alive and absf(tgt.plane.x - a.plane.x) <= reach + tgt.half_width() + 10 and absf(tgt.plane.y - a.plane.y) <= 34:
					game.combat.ally_hits_enemy(a, tgt, attack_power)
				a.ai.state = "recover"
				a.ai.timer = 0.6
				a.action = "attack"
				a.action_time = 0.0
			return
		"recover":
			a.action = "attack" if a.action_time < 0.33 else "idle"
			if float(a.ai.timer) <= 0.0: a.ai.state = "follow"
			return
	if target != null:
		var dx := target.plane.x - a.plane.x
		a.facing = 1 if dx >= 0 else -1
		if absf(dx) <= reach + target.half_width() and absf(target.plane.y - a.plane.y) <= 26:
			a.ai.state = "windup"
			a.ai.timer = 0.35
			a.ai.target_uid = target.uid
			a.action_time = 0.0
			return
		var want := Vector2(target.plane.x - a.facing * (reach * 0.7), target.plane.y) - a.plane
		a.velocity = want.limit_length(1.0) * float(a.ai.get("speed", 180))
	else:
		var to_home = home - a.plane
		if to_home.length() > 24.0:
			a.velocity = to_home.normalized() * minf(float(a.ai.get("speed", 180)) * (1.6 if to_home.length() > 300 else 1.0), to_home.length() / delta)
			a.facing = 1 if to_home.x >= 0 else -1
		else:
			a.velocity = Vector2.ZERO
			a.facing = int(game.combat.timeline(c.id).facing)
	a.action = "walk" if a.velocity.length() > 5.0 else "idle"
	var next := a.plane + a.velocity * delta
	var b = game.room_rt.geometry.bounds
	a.plane = next.clamp(b.position + Vector2(16, 6), b.end - Vector2(16, 12))
	if a.plane.distance_to(st.plane) > 700.0: a.plane = st.plane + Vector2(side * 50, 8)
	a.altitude = 0.0
