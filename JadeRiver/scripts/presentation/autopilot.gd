class_name Autopilot
extends RefCounted
## S49 mobile conventions: quest auto-path and auto-hunt drive the player's joystick and buttons. The autopilot only
## makes input (an axis, a jump, an attack, a technique); the World and Combat authorities decide the rest, and any
## touch of the joystick hands the controls back. Within a room it follows the navigation graph (walk, jump, climb,
## drop) with the plain jump every character has; on the height grid TopdownRoute steers it round the room's props at
## the player's sprint (decision 42).

const MOVE := {"jump": MovementSolver.JUMP_IMPULSE, "climb": true, "drop": true}
const MELEE_REACH := 62.0
const BOW_REACH := 360.0

var player
var hop_cd := 0.0
var swing_cd := 0.0
var tech_cd := 0.0
var tech_slot := 0
var climb_dir := 0.0

func _init(p) -> void:
	player = p

## The joystick for this frame: Vector2.ZERO when there is nothing to do.
func drive(c, delta: float) -> Vector2:
	hop_cd -= delta
	swing_cd -= delta
	tech_cd -= delta
	if Game.room_rt == null: return Vector2.ZERO
	var step: Dictionary = Game.world.auto_path_step(c)
	if not step.is_empty() and step.has("place"):
		# Decision 43: the walk to a place ends on its user's cell (the grid's route round everything on the way).
		var to_place := _toward(Vector2(float(step.x), float(step.y)), "", 10.0 if Game.room_rt.topdown != null else 40.0)
		if to_place != Vector2.INF: return to_place
		Game.world.auto_path_arrive(c)
		return Vector2.ZERO
	if not step.is_empty() and step.has("dock"):
		var at_dock := _toward(Vector2(float(step.x), float(step.y)), "", 50.0)
		if at_dock != Vector2.INF: return at_dock
		if hop_cd <= 0.0:
			hop_cd = 2.0
			Game.world.auto_path_board(c, str(step.dock))
		return Vector2.ZERO
	if not step.is_empty(): return _to_portal(step)
	if Game.world.auto_hunting(c.id): return _hunt(c)
	return Vector2.ZERO

## Walk (and climb and jump) to the route's portal, then take it: press up at a door, walk out through an edge. On the
## height grid every way is walked into along its own direction (a building's door north, an interior's south).
func _to_portal(step: Dictionary) -> Vector2:
	var goal := Vector2(float(step.x), float(step.y))
	var axis := _toward(goal, str(step.get("surface", "")), 40.0 if Game.room_rt.topdown == null else 14.0)
	if axis != Vector2.INF: return axis
	var way: Dictionary = Game.room_rt.portal_def(str(step.get("portal", "")))
	if way.has("dir"): return Vector2(float(way.dir[0]), float(way.dir[1]))
	if step.get("press_up", false): return Vector2(0, -1)
	return Vector2(1.0 if goal.x > Game.room_rt.width() * 0.5 else -1.0, 0)

## The nearest foe that can be fought (not a spar partner, not one who has yielded): close in and fight it with
## basic attacks and the equipped techniques. Treasures, pills and breakthroughs are never used.
func _hunt(c) -> Vector2:
	var here: Vector2 = player.plane
	var best: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("spar", false) or e.ai.get("surrendered", false): continue
		if not _reachable(e.plane, e.altitude): continue   # on the grid: never a foe on a roof there is no way onto
		if best == null or here.distance_to(e.plane) < here.distance_to(best.plane): best = e
	# Between fights (nothing within reach of a few steps), gather what the last ones dropped.
	if best == null or here.distance_to(best.plane) > 220.0:
		var drop := _nearest_loot(here)
		if not drop.is_empty():
			var at := Vector2(float(drop.x), float(drop.y))
			var go := _toward(at, "", 24.0)
			if go != Vector2.INF: return go
			Game.submit({"type": "pick_up", "uid": int(drop.uid)})
			return Vector2.ZERO
	if best == null: return Vector2.ZERO
	var d: Vector2 = best.plane - here
	var reach := BOW_REACH if str(StatRules.family(c).get("id", "")) == "bow" else MELEE_REACH
	var grid: bool = Game.room_rt.topdown != null
	var same: bool = player.surface != null and (TopdownAim.compatible(best.altitude - player.altitude) if grid else player.surface.id == best.surface_id)
	# On the grid the blow aims at the nearest foe round the stick itself (the soft lock, decision 30).
	if same and (d.length() <= reach if grid else absf(d.x) <= reach and absf(d.y) <= 24.0):
		if absf(d.x) > 1.0 and not grid: player.facing = int(signf(d.x))
		if swing_cd <= 0.0:
			player.attack()
			swing_cd = 0.35
		if tech_cd <= 0.0:
			player.use_technique(tech_slot)
			tech_slot = (tech_slot + 1) % 4
			tech_cd = 1.2
		return Vector2.ZERO
	var stand := best.plane - (d.normalized() * reach * 0.6 if grid else Vector2(signf(d.x) * reach * 0.6, 0.0))
	# On the grid the spot to strike from is on the foe's own floor (its blows and ours reach only there).
	if grid: stand = Game.room_rt.topdown.spot_near(stand, best.altitude, here, 8.0)
	var axis := _toward(stand, best.surface_id, 10.0)
	return Vector2.ZERO if axis == Vector2.INF else axis

## Toward a point, across surfaces when it lies on another one (the room's navigation graph); INF when there.
func _toward(goal: Vector2, goal_surface: String, near: float) -> Vector2:
	if Game.room_rt.topdown != null: return _toward_grid(goal, near)
	var here: Vector2 = player.plane
	if not player.state.climbing.is_empty(): return Vector2(0, climb_dir)
	if player.surface == null: return Vector2(signf(goal.x - here.x) * 0.7, 0)   # in the air: steer
	var geo: ZoneGeometry = Game.room_rt.geometry
	if goal_surface == "":
		var under: WalkSurface = geo.surface_under(goal, 0.0)
		goal_surface = under.id if under != null else ""
	var aim := goal
	var arriving := true
	if goal_surface != "" and goal_surface != player.surface.id:
		var path: Array = geo.nav_path(player.surface.id, goal_surface, MOVE)
		if not path.is_empty():
			arriving = false
			var e: Dictionary = path[0]
			var from_pt: Vector2 = e.from_pt
			aim = from_pt
			if here.distance_to(from_pt) <= 18.0:
				aim = e.to_pt
				match str(e.kind):
					"jump":
						if hop_cd <= 0.0:
							player.jump()
							hop_cd = 0.6
					"climb":
						climb_dir = -1.0 if float(e.to_alt) > float(e.from_alt) else 1.0
						return Vector2(0, climb_dir)
					"drop":
						aim = (e.to_pt as Vector2) + ((e.to_pt as Vector2) - from_pt).normalized() * 24.0
	var d := aim - here
	if arriving and d.length() <= near: return Vector2.INF
	return Vector2(d.x, d.y * 1.4).normalized()

## Redesign Phase 4, decision 42: toward a point on the height grid by TopdownRoute: the room's cells (walking, stairs,
## drops and a jump one level up, which it presses Jump for), round every solid prop, wall and bank with the foot box
## clear of them, in straight runs; the stick fully pushed, so the body sprints as the player's does. INF when there.
var _route: TopdownRoute = null
func _toward_grid(goal: Vector2, near: float) -> Vector2:
	var room: TopdownRoom = Game.room_rt.topdown
	if _route == null or _route.room != room: _route = TopdownRoute.new(room)
	var axis := _route.steer(player.plane, player.altitude, player.surface != null, goal, near)
	if _route.jump and hop_cd <= 0.0 and player.surface != null:
		player.jump()
		hop_cd = 0.5
	return axis

## The nearest drop within 500 px that can be walked to: on the ground in the side view (not one left on a ledge); on
## the height grid on any floor there is a way onto.
func _nearest_loot(here: Vector2) -> Dictionary:
	var best := {}
	var best_d := 500.0
	var grid: bool = Game.room_rt.topdown != null
	for l in Game.room_rt.loot:
		var at := Vector2(float(l.x), float(l.y))
		if not grid and float(l.get("alt", 0.0)) > 10.0: continue
		var dist := here.distance_to(at)
		if dist < best_d and _reachable(at, float(l.get("alt", 0.0))):
			best_d = dist
			best = l
	return best

## Can the body get to a spot at `alt` on foot (the side view's graph handles its own): on the height grid its floor
## is the body's own within a step, or the grid's path (walks, stairs, drops, a hop a level up) reaches its cell.
## Asked each frame, so the answer for a cell is kept until the body's own cell changes.
var _reach_from := ""
var _reach_cache := {}
func _reachable(at: Vector2, alt: float) -> bool:
	var room: TopdownRoom = Game.room_rt.topdown
	if room == null or absf(alt - player.altitude) <= 8.0: return true
	var from := TopdownRoom.cell_of(player.plane)
	var key := "%s%s" % [room.id, str(from)]
	if key != _reach_from:
		_reach_from = key
		_reach_cache.clear()
	var to := TopdownRoom.cell_of(room.nearest_standable(at))
	if not _reach_cache.has(to): _reach_cache[to] = to == from or not TopdownRoute.find(room, from, to, true).is_empty()
	return bool(_reach_cache[to])
