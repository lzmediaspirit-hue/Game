class_name AllyBrain
extends RefCounted
## CompanionBrain / PetBrain core (S22, S26): follow the owner, pick the owner's
## nearest enemy, strike with a readable wind-up, retreat at low HP, sit while the
## owner meditates. Allies never block portals and never enter portal areas.
## S43 rule 12: they walk on surfaces and follow the owner along the navigation graph; more than 480 away,
## or 2 s unable to reach the owner's surface, they blink to the owner in a puff of mist.

## Put a new ally on the surface under it (or its owner's), at that surface's height.
static func settle(game, a: EnemyState, st: ActorState) -> void:
	if game.room_rt == null: return
	var geo: ZoneGeometry = game.room_rt.geometry
	var s: WalkSurface = st.surface if st != null and st.surface != null and st.surface.contains(a.plane) else geo.surface_under(a.plane, 0.0)
	if s == null and st != null: s = st.surface
	if s != null and not s.contains(a.plane) and st != null: a.plane = st.plane
	a.surface_id = s.id if s else ""
	a.home_surface = a.surface_id
	a.altitude = s.height_at(a.plane) if s else 0.0

## Blink to the owner (S43 rule 12).
static func blink_to(a: EnemyState, st: ActorState, side: int) -> void:
	var s: WalkSurface = st.surface
	var p: Vector2 = st.plane + Vector2(side * 50, 8)
	if s != null and not s.contains(p): p = st.plane
	a.plane = p
	a.hop = {}
	a.surface_id = s.id if s else a.surface_id
	a.altitude = s.height_at(p) if s else st.altitude
	a.ai.stuck = 0.0
	a.ai.blink_t = 0.5

static func think(game, a: EnemyState, delta: float, attack_power: float, reach: float) -> void:
	var c = game.active()
	var st: ActorState = game.actor_state(c.id) if c else null
	if st == null: return
	a.ai.timer = float(a.ai.timer) - delta
	a.action_time += delta
	a.ai.blink_t = maxf(0.0, float(a.ai.get("blink_t", 0.0)) - delta)
	if a.flash > 0.0: a.flash = maxf(0.0, a.flash - delta)
	if not a.hop.is_empty():
		EnemyBrain._hop(game.enemies, a, delta)
		return
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
	# The pet command wheel (v2 HUD): stay holds a spot, attack reaches wider, passive never fights.
	var cmd := str(a.ai.get("command", "follow"))
	var staying := cmd == "stay"
	if staying: home = a.ai.get("stay_at", a.plane)
	var target: EnemyState = null
	var best := 600.0 if cmd == "attack" else 260.0
	var from: Vector2 = home if staying else st.plane
	for e in game.room_rt.living_enemies():
		if cmd == "passive": break
		if e.team != "enemy" or e.hidden or e.def.get("passive", false): continue
		var d = e.plane.distance_to(a.plane if cmd == "attack" else from)
		if staying and d > reach + e.half_width() + 60.0: continue
		if d < best:
			best = d
			target = e
	# Left far behind (another screen, a portal jump): blink back at once, whatever it was doing (S43). A pet told to
	# stay keeps its post unless you leave it very far behind.
	if a.plane.distance_to(st.plane) > (1400.0 if staying else 480.0):
		blink_to(a, st, -1 if int(game.combat.timeline(c.id).facing) > 0 else 1)
		a.ai.state = "follow"
		return
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
	# Follow the owner onto another surface along the graph; blink when it cannot be reached (S43).
	var geo: ZoneGeometry = game.room_rt.geometry
	var owner_surf: WalkSurface = st.surface if st.surface != null else geo.surface_under(st.plane, st.altitude)
	if not staying and a.surface_id != "" and owner_surf != null and owner_surf.id != a.surface_id and (target == null or a.plane.distance_to(st.plane) > 200.0):
		var path: Array = geo.nav_path(a.surface_id, owner_surf.id, EnemyBrain.movement_of(a))
		if path.is_empty():
			a.ai.stuck = float(a.ai.get("stuck", 0.0)) + delta
		else:
			a.ai.stuck = 0.0
			EnemyBrain._follow_edge(game.enemies, a, path[0], delta)
			if a.plane.distance_to(st.plane) > 480.0: blink_to(a, st, side)
			return
	else:
		a.ai.stuck = 0.0
	if not staying and (a.plane.distance_to(st.plane) > 480.0 or float(a.ai.get("stuck", 0.0)) >= 2.0):
		blink_to(a, st, side)
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
	if a.surface_id == "":
		var next := a.plane + a.velocity * delta
		var b = game.room_rt.geometry.bounds
		a.plane = next.clamp(b.position + Vector2(16, 6), b.end - Vector2(16, 12))
		a.altitude = 0.0
	else:
		game.enemies.move_enemy(a, delta)   # on its surface, like any walker
