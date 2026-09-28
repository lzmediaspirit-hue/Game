class_name AllyBrain
extends RefCounted
## CompanionBrain / PetBrain core (S22, S26): follow the owner, pick the owner's
## nearest enemy, strike with a readable wind-up, retreat at low HP, sit while the
## owner meditates. Allies never block portals and never enter portal areas.
## S43 rule 12: they walk on surfaces and follow the owner along the navigation graph; more than 480 away,
## or 2 s unable to reach the owner's surface, they blink to the owner in a puff of mist.
##
## Redesign Phase 4: in a room on the height grid the rules are the same and only the steering is the grid's
## (TopdownBrain): the follow spot is behind the owner along its facing on the plane, on its floor; the way there is
## the grid's path (walks, stairs, drops, and a hop a level up for an ally that jumps, on the grid's gravity, as the
## player jumps); a strike reaches on the plane and only a foe on a compatible height (TopdownAim); a blink lands on the
## owner's floor on its side of any wall.

## Put a new ally on the surface under it (or its owner's), at that surface's height; on the height grid on a free spot
## of its owner's floor near where it was put.
static func settle(game, a: EnemyState, st: ActorState) -> void:
	if game.room_rt == null: return
	var grid: TopdownRoom = game.room_rt.topdown
	if grid != null and st != null:
		var ground := TopdownBrain.floor_under(grid, st)
		a.plane = TopdownBrain.spot_by(grid, st.plane, ground, a.plane)
		a.altitude = grid.floor_at(a.plane)
		a.surface_id = ""
		a.home_surface = ""
		return
	var geo: ZoneGeometry = game.room_rt.geometry
	var s: WalkSurface = st.surface if st != null and st.surface != null and st.surface.contains(a.plane) else geo.surface_under(a.plane, 0.0)
	if s == null and st != null: s = st.surface
	if s != null and not s.contains(a.plane) and st != null: a.plane = st.plane
	a.surface_id = s.id if s else ""
	a.home_surface = a.surface_id
	a.altitude = s.height_at(a.plane) if s else 0.0

## Blink to the owner (S43 rule 12): beside it, on its floor (on the height grid, on its side of any wall).
static func blink_to(game, a: EnemyState, st: ActorState, side: int) -> void:
	var grid: TopdownRoom = game.room_rt.topdown if game.room_rt != null else null
	var s: WalkSurface = st.surface
	var p: Vector2 = st.plane + Vector2(side * 50, 8)
	if grid != null:
		var ground := TopdownBrain.floor_under(grid, st)
		a.plane = TopdownBrain.spot_by(grid, st.plane, ground, p)
		a.altitude = grid.floor_at(a.plane)
		a.vz = 0.0
	else:
		if s != null and not s.contains(p): p = st.plane
		a.plane = p
		a.surface_id = s.id if s else a.surface_id
		a.altitude = s.height_at(p) if s else st.altitude
	a.hop = {}
	a.ai.stuck = 0.0
	a.ai.blink_t = 0.5

## Is `tgt` within an ally's strike: `reach` (plus `slack`) out and `depth` across in the side view; on the height grid
## within reach on the plane and on a height its blow reaches (TopdownAim: a foe a level up or down is out of it).
static func in_reach(grid: TopdownRoom, a: EnemyState, tgt: EnemyState, reach: float, slack: float, depth: float) -> bool:
	if grid != null:
		return a.plane.distance_to(tgt.plane) <= reach + tgt.half_width() + slack and TopdownAim.compatible(tgt.altitude - a.altitude)
	return absf(tgt.plane.x - a.plane.x) <= reach + tgt.half_width() + slack and absf(tgt.plane.y - a.plane.y) <= depth

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
	var grid: TopdownRoom = game.room_rt.topdown
	# On the grid the floor underfoot carries it: stairs and steps at once, a drop under gravity.
	if grid != null and not bool(EnemyBrain.movement_of(a).get("fly", false)): TopdownBrain.fall(grid, a, delta)
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
	var owner_floor: float = TopdownBrain.floor_under(grid, st) if grid != null else st.altitude
	if grid != null:
		home = TopdownBrain.follow_spot(grid, st.plane, owner_floor, game.combat.timeline(c.id).get("aim", Vector2(-side, 0)),
			float(a.ai.get("offset", 60)), float(a.ai.get("depth_offset", 10)))
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
		blink_to(game, a, st, -1 if int(game.combat.timeline(c.id).facing) > 0 else 1)
		a.ai.state = "follow"
		return
	match str(a.ai.state):
		"windup":
			a.velocity = Vector2.ZERO
			a.action = "windup"
			if float(a.ai.timer) <= 0.0:
				var tgt: EnemyState = game.room_rt.enemies.get(int(a.ai.get("target_uid", -1)))
				if tgt != null and tgt.alive and in_reach(grid, a, tgt, reach, 10.0, 34.0):
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
	# Follow the owner onto another surface along the graph; blink when it cannot be reached (S43). On the grid the
	# grid's own path does this below.
	var geo: ZoneGeometry = game.room_rt.geometry
	var owner_surf: WalkSurface = st.surface if st.surface != null else geo.surface_under(st.plane, st.altitude)
	if grid == null and not staying and a.surface_id != "" and owner_surf != null and owner_surf.id != a.surface_id and (target == null or a.plane.distance_to(st.plane) > 200.0):
		var path: Array = geo.nav_path(a.surface_id, owner_surf.id, EnemyBrain.movement_of(a))
		if path.is_empty():
			a.ai.stuck = float(a.ai.get("stuck", 0.0)) + delta
		else:
			a.ai.stuck = 0.0
			EnemyBrain._follow_edge(game.enemies, a, path[0], delta)
			if a.plane.distance_to(st.plane) > 480.0: blink_to(game, a, st, side)
			return
	elif grid == null:
		a.ai.stuck = 0.0
	if not staying and (a.plane.distance_to(st.plane) > 480.0 or float(a.ai.get("stuck", 0.0)) >= 2.0):
		blink_to(game, a, st, side)
		return
	if grid != null:
		_steer_on_grid(game, grid, a, target, home, owner_floor, reach, delta)
		return
	if target != null:
		var dx := target.plane.x - a.plane.x
		a.facing = 1 if dx >= 0 else -1
		if in_reach(null, a, target, reach, 0.0, 26.0):
			_wind_up(a, target)
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

static func _wind_up(a: EnemyState, target: EnemyState) -> void:
	a.ai.state = "windup"
	a.ai.timer = 0.35
	a.ai.target_uid = target.uid
	a.action_time = 0.0

## Redesign Phase 4: close on the target and strike it, or keep the follow spot, on the height grid. The way is the
## grid's (TopdownBrain.chase, which hops a level up for an ally that jumps); an ally that makes no headway toward a
## spot it is far from is stuck, and after 2 s it blinks to its owner (think).
static func _steer_on_grid(game, grid: TopdownRoom, a: EnemyState, target: EnemyState, home: Vector2, owner_floor: float, reach: float, delta: float) -> void:
	var speed := float(a.ai.get("speed", 180))
	var before := a.plane
	var goal := home
	var goal_alt := owner_floor
	if target != null:
		var d := target.plane - a.plane
		if d.length() > 0.5: a.aim = d.normalized()
		a.facing = 1 if d.x >= 0.0 else -1
		if in_reach(grid, a, target, reach, 0.0, 26.0):
			a.velocity = Vector2.ZERO
			_wind_up(a, target)
			return
		goal = target.plane - (d.normalized() if d.length() > 0.5 else Vector2.RIGHT) * reach * 0.7
		goal_alt = grid.floor_at(target.plane)
	var far := a.plane.distance_to(goal)
	if target == null and far <= 24.0 and absf(a.altitude - goal_alt) <= 8.0:
		a.velocity = Vector2.ZERO
		a.action = "idle"
		a.ai.stuck = 0.0
		var face: Vector2 = game.combat.timeline(game.active_id).get("aim", Vector2(a.facing, 0))
		a.aim = face
		a.facing = 1 if face.x >= 0.0 else -1
		return
	TopdownBrain.chase(game.enemies, a, goal, goal_alt, speed * (1.6 if far > 300.0 else 1.0), delta, false)
	if a.velocity.length() > 1.0: a.aim = a.velocity.normalized()
	# No headway toward a spot it is far from (a wall, a roof with no way up): stuck.
	var gone := a.plane.distance_to(before)
	if a.hop.is_empty() and far > 40.0 and gone < speed * delta * 0.25: a.ai.stuck = float(a.ai.get("stuck", 0.0)) + delta
	else: a.ai.stuck = 0.0
	a.action = "walk" if a.velocity.length() > 5.0 or not a.hop.is_empty() else "idle"
