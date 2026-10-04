class_name Autopilot
extends RefCounted
## S49 mobile conventions: quest auto-path and auto-hunt drive the player's joystick and buttons. The autopilot only
## makes input (an axis, a jump, an attack, a technique); the World and Combat authorities decide the rest, and any
## touch of the joystick hands the controls back. Within a room TopdownRoute steers it on the height grid round the
## room's props at the player's sprint (decision 42), pressing Jump for a hop a level up.

const MELEE_REACH := 62.0
const BOW_REACH := 360.0

var player
var hop_cd := 0.0
var swing_cd := 0.0
var tech_cd := 0.0
var tech_slot := 0

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
		var to_place := toward_grid(Vector2(float(step.x), float(step.y)), 10.0)
		if to_place != Vector2.INF: return to_place
		Game.world.auto_path_arrive(c)
		return Vector2.ZERO
	if not step.is_empty() and step.has("dock"):
		var at_dock := toward_grid(Vector2(float(step.x), float(step.y)), 50.0)
		if at_dock != Vector2.INF: return at_dock
		if hop_cd <= 0.0:
			hop_cd = 2.0
			Game.world.auto_path_board(c, str(step.dock))
		return Vector2.ZERO
	if not step.is_empty(): return _to_portal(step)
	if Game.world.auto_hunting(c.id): return _hunt(c)
	return Vector2.ZERO

## Walk to the route's portal, then take it: every way is walked into along its own direction (a building's door north,
## an interior's south, an edge out through its side).
func _to_portal(step: Dictionary) -> Vector2:
	var goal := Vector2(float(step.x), float(step.y))
	var axis := toward_grid(goal, 14.0)
	if axis != Vector2.INF: return axis
	var way: Dictionary = Game.room_rt.portal_def(str(step.get("portal", "")))
	if way.has("dir"): return Vector2(float(way.dir[0]), float(way.dir[1]))
	return Vector2(1.0 if goal.x > Game.room_rt.width() * 0.5 else -1.0, 0)

## The nearest foe that can be fought (not a spar partner, not one who has yielded): close in and fight it with
## basic attacks and the equipped techniques. Treasures, pills and breakthroughs are never used.
func _hunt(c) -> Vector2:
	var here: Vector2 = player.plane
	var best: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("spar", false) or e.ai.get("surrendered", false): continue
		if not _reachable(e.plane, e.altitude): continue   # never a foe on a roof there is no way onto
		if best == null or here.distance_to(e.plane) < here.distance_to(best.plane): best = e
	# Between fights (nothing within reach of a few steps), gather what the last ones dropped.
	if best == null or here.distance_to(best.plane) > 220.0:
		var drop := _nearest_loot(here)
		if not drop.is_empty():
			var at := Vector2(float(drop.x), float(drop.y))
			var go := toward_grid(at, 24.0)
			if go != Vector2.INF: return go
			Game.submit({"type": "pick_up", "uid": int(drop.uid)})
			return Vector2.ZERO
	if best == null: return Vector2.ZERO
	var d: Vector2 = best.plane - here
	var reach := BOW_REACH if str(StatRules.family(c).get("id", "")) == "bow" else MELEE_REACH
	var same: bool = player.surface != null and TopdownAim.compatible(best.altitude - player.altitude)
	# The blow aims at the nearest foe round the stick itself (the soft lock, decision 30).
	if same and d.length() <= reach:
		if swing_cd <= 0.0:
			player.attack()
			swing_cd = 0.35
		if tech_cd <= 0.0:
			player.use_technique(tech_slot)
			tech_slot = (tech_slot + 1) % 4
			tech_cd = 1.2
		return Vector2.ZERO
	# The spot to strike from is on the foe's own floor (its blows and ours reach only there).
	var stand := Game.room_rt.topdown.spot_near(best.plane - d.normalized() * reach * 0.6, best.altitude, here, 8.0)
	var axis := toward_grid(stand, 10.0)
	return Vector2.ZERO if axis == Vector2.INF else axis

## Redesign Phase 4, decision 42: toward a point on the height grid by TopdownRoute: the room's cells (walking, stairs,
## drops and a jump one level up, which it presses Jump for), round every solid prop, wall and bank with the foot box
## clear of them, in straight runs; the stick fully pushed, so the body sprints as the player's does. INF when there.
var _route: TopdownRoute = null
func toward_grid(goal: Vector2, near: float) -> Vector2:
	var room: TopdownRoom = Game.room_rt.topdown
	if _route == null or _route.room != room: _route = TopdownRoute.new(room)
	var axis := _route.steer(player.plane, player.altitude, player.surface != null, goal, near)
	if _route.jump and hop_cd <= 0.0 and player.surface != null:
		player.jump()
		hop_cd = 0.5
	return axis

## The nearest drop within 500 px that can be walked to: on any floor there is a way onto.
func _nearest_loot(here: Vector2) -> Dictionary:
	var best := {}
	var best_d := 500.0
	for l in Game.room_rt.loot:
		var at := Vector2(float(l.x), float(l.y))
		var dist := here.distance_to(at)
		if dist < best_d and _reachable(at, float(l.get("alt", 0.0))):
			best_d = dist
			best = l
	return best

## Can the body get to a spot at `alt` on foot: its floor is the body's own within a step, or the grid's path (walks,
## stairs, drops, a hop a level up) reaches its cell. Asked each frame, so the answer for a cell is kept until the body's
## own cell changes.
var _reach_from := ""
var _reach_cache := {}
func _reachable(at: Vector2, alt: float) -> bool:
	var room: TopdownRoom = Game.room_rt.topdown
	if absf(alt - player.altitude) <= 8.0: return true
	var from := TopdownRoom.cell_of(player.plane)
	var key := "%s%s" % [room.id, str(from)]
	if key != _reach_from:
		_reach_from = key
		_reach_cache.clear()
	var to := TopdownRoom.cell_of(room.nearest_standable(at))
	if not _reach_cache.has(to): _reach_cache[to] = to == from or not TopdownRoute.find(room, from, to, true).is_empty()
	return bool(_reach_cache[to])
