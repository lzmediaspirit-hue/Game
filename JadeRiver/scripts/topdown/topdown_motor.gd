class_name TopdownMotor
extends RefCounted
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1.6): the character controller on a TopdownRoom.
## 8-way analog movement with acceleration: the stick pushed past its tiptoe band sprints (decision 42), a light touch
## walks slowly (the tiptoe, for a careful step to a ledge); in the air the body carries no more than the walk the world
## was measured at (154), so every jump, drop and gap reaches as it was measured. A Jump button (decision 28: jumping is
## always on the button) that clears one level, falls down any open edge, coyote time and an input buffer, a dash that
## doubles as a long jump when Jump follows it, and collision per height level with corner sliding. Ground plane (x,
## depth y) plus height z in world units, stepped at 120 Hz; numbers from movement.json `topdown`. Nothing here draws:
## the view reads the state and drains `events`.
##
## Decision 43 (the jump is hard to control at the sprint's speed: a jump onto a box sails over it): in the air the
## stick steers at `air_control` of the ground's pick-up, brakes `air_turn` times harder when it pulls against the
## motion, and let go the body slows to a stop over `air_brake_s` (a dash's long jump keeps its carry unless pulled
## back); and the landing assist (`magnet`): a jump that would carry past the far edge of a flat top it came onto (a
## box, a roof: not the floor it left, unless it crossed a gap to it) by no more than `magnet` units, with the stick
## along the jump, brakes smoothly to land `magnet_margin` inside that edge. The drawn row turns through the rows
## between, one every `turn_row_s`, when the stick swings round (an aimed blow's `face` turns it at once).

const STEP := 1.0 / 120.0
## T3: the eight ways round a body the wind looks along for a drop (the axes and the diagonals).
const WIND_AXES := [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1),
	Vector2(0.70710678, 0.70710678), Vector2(-0.70710678, 0.70710678), Vector2(0.70710678, -0.70710678), Vector2(-0.70710678, -0.70710678)]
## The body's eight drawn rows and their angles on the ground (east 0, south 90); NW, W and SW mirror NE, E and SE.
const ROW_ANGLES := {"s": 90.0, "se": 45.0, "e": 0.0, "ne": -45.0, "n": -90.0, "nw": -135.0, "w": 180.0, "sw": 135.0}

var room: TopdownRoom
var pos := Vector2.ZERO
var z := 0.0
var vz := 0.0
var vel := Vector2.ZERO
var grounded := true
var coyote := 0.0          ## seconds a jump is still allowed after walking off an edge
var buffer := 0.0          ## seconds a Jump pressed in the air waits for the ground
var dash_t := 0.0          ## seconds of dash left
var dash_dir := Vector2.ZERO
var dash_cd := 0.0
var since_dash := 99.0
var long_jump := false
var invuln := 0.0
var dir := Vector2(0, 1)   ## the facing, a unit vector (8-way analog)
var row := "s"             ## the drawn facing: s, se, e, ne, n, or nw, w, sw (drawn as mirrors of ne, e, se)
var peak := 0.0            ## the highest z of this airtime
var land_t := 0.0          ## landing squash left
var sink_t := -1.0         ## >= 0 while a splash plays, then back to the safe spot
var safe := Vector2.ZERO
var safe_z := 0.0
var events: Array = []     ## {type: jumped | landed | dashed | fell | splashed | reset, ...}, drained by the view
## Phase 2. Walking on water is a special skill (decision 29): off by default, the player turns it on for a character
## who knows the Water Skimming art; then the water's surface is a floor at the bank's height.
var water_walk := false
var push_v := Vector2.ZERO ## a knockback or a technique's dash: this velocity for push_t seconds, no steering
var push_t := 0.0
var lock_face := false     ## an attack or cast keeps the facing on its aim
var speed_k := 1.0         ## the combat authority's move factor (an attack on the ground walks at x0.3)
## Decision 35: the Plunge (the movement art) drops straight down at a fixed speed, no steering; its landing is the
## strike (the `landed` event carries `plunge`, and Combat resolves it).
var plunging := false
## Phase 4: the push the room's hazards put on the body (a gust, a current), in units a second, added to its step.
var drift := Vector2.ZERO
## Decision 43: the floor the airtime began from, whether the body has since passed over a floor lower than it (a gap:
## a top as high as the one it left is then a new one to land on), and how long the drawn row has held (its turn).
var takeoff_z := 0.0
var crossed_low := false
var row_t := 0.0
var magnet_on := false   ## the landing assist braked this substep (tests and traces)
var magnet_used := false ## the landing assist braked in this airtime
var land_hold := 0.0     ## after an assisted landing: seconds the top's edge still holds a body the stick pushes on
## T1 (docs/architecture/topdown_mechanics.md): the side view's movement arts and traversal on the grid. The arts this
## body knows (the player sets them from Combat, as `water_walk`), and the state of each.
var gliding := false       ## Falling Leaf Glide, held (Combat's glide: its QI and its art_used): the fall capped, a carry
var double_jump := false   ## Cloud Ladder Step known: a second jump in the air
var wall_step := false     ## Wall-Step known: a kick off a wall face pushed into, in the air
var jumps := 0             ## jumps this airtime (the second is the Cloud Ladder Step's)
var wall_kicks := 0        ## Wall-Step kicks this airtime
var hold_t := 0.0          ## Swallow Dart: seconds the height is held while the dart carries the body
var ride := ""             ## the raft the body stands on ("" when none)
var ride_off := Vector2.ZERO
var skimming := false      ## on the water's surface with Water Skimming (the entry is announced once)
var climbing: Dictionary = {}   ## the climbable face the body is on (TopdownTraverse.climbs), {} when none
var climb_k := 0.0         ## 0 at the climbable's foot, 1 at its top
var climb_moving := false  ## the stick moves it along the face this frame (the climb's pose cycles)
var flying := false        ## Cloud Stride's flight, while Combat holds it (the player keeps the two together)
var fly_input := 0.0       ## +1 climbing (Jump held), -1 descending (Evade held), 0 holding the height
var _trav_room = null
var _trav: TopdownTraverse = null
## T2 (topdown_mechanics.md): Breath Control known (the player sets it from Combat): open water is swum, `swim_left`
## seconds of breath, at the swim's pace, out onto a bank `swim_out` over the water; out of breath the body sinks and is
## back on its last safe spot, as without it. `wade_free`: the shallows do not slow it (a Water Sphere's frozen ground,
## the side view's frozen_ground). A fall into a pit (rotten boards over one, gone) strikes nothing here: the World
## authority's hazard volume does.
var swim := false
var swimming := false
var swim_left := 0.0
var wade_free := false
var swim_s: float
var swim_factor: float
var swim_out: float
## T3: the swim's stroke (topdown_mechanics.md): a pull and a glide every `swim_stroke` seconds while the swimmer moves,
## the pace surging `swim_surge` of itself on the pull and easing on the glide (the same pace on the whole), each pull
## announced (`stroked`: the wake's ring); `stroke_t` is how far into this stroke it is.
var swim_stroke: float
var swim_surge: float
var stroke_t := 0.0
var shallow_factor: float
var wind_edge: float
var _wading := {}          ## the paint marks that are floors under shallow water (the tile set's `flood`), per room
var _wading_room = null

var walk: float
var tiptoe_axis: float
var tiptoe: float
var sprint: float
## Decision 42: the stick's band the body last moved in: true while it sprints (the run the sheets draw), false while a
## light touch walks. Kept through a stop, so the figure does not flick to the walk as it slows.
var running := false
var accel: float
var decel: float
var air_control: float
var air_brake: float
var air_turn: float
var magnet: float
var magnet_margin: float
var magnet_decel: float
var magnet_hold_s: float
var turn_row_s: float
var gravity: float
var impulse: float
var step_up: float
var mantle: float
var coyote_s: float
var buffer_s: float
var dash_speed: float
var dash_distance: float
var back_step: float
var dash_cooldown: float
var invuln_s: float
var long_window: float
var long_speed: float
var half := Vector2(8, 5)
var nudge: float
var squash_s: float
var reset_s: float
var glide_fall: float
var glide_drift: float
var updraft_ease: float
var climb_speed: float
var fly_climb: float
var fly_ceiling: float
var fly_k: float

static func conf(key: String, fallback = 0.0):
	return ContentDB.movement("topdown." + key, fallback)

func _init(r: TopdownRoom, at := Vector2.INF) -> void:
	room = r
	walk = conf("walk", 154.0)
	tiptoe_axis = conf("tiptoe_axis", 0.6)
	tiptoe = conf("tiptoe", 0.45)
	sprint = conf("sprint", walk)
	accel = sprint / float(conf("accel_s", 0.08))
	decel = sprint / float(conf("stop_s", 0.06))
	air_control = conf("air_control", 0.35)
	air_brake = walk / maxf(0.01, float(conf("air_brake_s", 0.3)))
	air_turn = conf("air_turn", 2.5)
	magnet = conf("magnet", 28.0)
	magnet_margin = conf("magnet_margin", 6.0)
	magnet_decel = conf("magnet_decel", 2400.0)
	magnet_hold_s = conf("magnet_hold_s", 0.3)
	turn_row_s = conf("turn_row_s", 0.016)
	gravity = conf("gravity", 1700.0)
	impulse = conf("impulse", 400.0)
	step_up = conf("step_up", 8.0)
	mantle = conf("mantle", 12.0)
	coyote_s = conf("coyote_s", 0.1)
	buffer_s = conf("buffer_s", 0.12)
	dash_speed = conf("dash_speed", 430.0)
	dash_distance = conf("dash_distance", 96.0)
	back_step = conf("back_step", 48.0)
	dash_cooldown = ContentDB.movement("dodge.cooldown_s", 2.5)
	invuln_s = conf("dash_invuln_s", 0.15)
	long_window = conf("long_jump_window_s", 0.12)
	long_speed = conf("long_jump_speed", 300.0)
	var box: Array = conf("box", [16, 10])
	half = Vector2(float(box[0]), float(box[1])) * 0.5
	nudge = conf("corner_nudge", 10.0)
	squash_s = conf("land_squash_s", 0.1)
	reset_s = conf("water_reset_s", 0.5)
	glide_fall = conf("traverse.glide_fall", 90.0)
	glide_drift = conf("traverse.glide_drift", 1.1)
	updraft_ease = conf("traverse.updraft_ease", 3.0)
	climb_speed = conf("traverse.climb_speed", 80.0)
	fly_climb = conf("traverse.fly_climb", 160.0)
	fly_ceiling = conf("traverse.fly_ceiling", 160.0)
	fly_k = conf("traverse.fly_speed", 1.2)
	swim_s = conf("traverse.swim_s", 30.0)
	swim_factor = conf("traverse.swim_factor", 0.6)
	swim_out = conf("traverse.swim_out", 24.0)
	swim_stroke = conf("traverse.swim_stroke_s", 0.9)
	swim_surge = conf("traverse.swim_surge", 0.15)
	shallow_factor = conf("traverse.shallow_factor", 0.7)
	wind_edge = conf("traverse.wind_edge", 36.0)
	swim_left = swim_s
	place(room.spawn if at == Vector2.INF else at)

## Stand on the floor at a ground point.
func place(p: Vector2) -> void:
	pos = p
	z = floor_at(p)
	vz = 0.0
	vel = Vector2.ZERO
	grounded = true
	plunging = false
	sink_t = -1.0
	safe = p
	safe_z = z
	climbing = {}
	gliding = false
	hold_t = 0.0
	ride = ""
	flying = false
	swimming = false
	swim_left = swim_s
	_took_off()

## The jump's apex over its take-off, and its airtime back to the same height (movement numbers, §As built).
func apex() -> float: return impulse * impulse / (2.0 * gravity)
## Test hook: the top-down suite.
func airtime() -> float: return 2.0 * impulse / gravity

## One frame of input. `jump` and `dash` are presses (edges) this frame; the frame runs as 120 Hz substeps.
func step(dt: float, axis: Vector2, jump := false, dash := false) -> void:
	if not climbing.is_empty():
		# T1: on a climbable face Jump lets go (a hop back off it); the dash waits for the ground.
		if jump: release_climb(true)
		else:
			var lc := dt
			while lc > 0.00001 and not climbing.is_empty():
				var hc := minf(STEP, lc)
				_climb_step(hc, axis)
				lc -= hc
			return
	# T1: a press in the air past the coyote time kicks off a wall pushed into (Wall-Step), else is the Cloud Ladder
	# Step's second jump; otherwise it waits for the ground (the buffer), as the side view's jump does.
	if jump and flying: jump = false   # a flier climbs on the held button (fly_input), it does not jump
	if jump and not grounded and coyote <= 0.0 and sink_t < 0.0 and not plunging and (_wall_kick(axis) or _double_jump()): jump = false
	if jump: buffer = buffer_s
	if dash: _start_dash(axis)
	_ride()
	var left := dt
	while left > 0.00001:
		var h := minf(STEP, left)
		_substep(h, axis)
		left -= h

## T1: the room's traversal (TopdownTraverse.of), null when its layout has none (the common case costs one compare).
func traverse() -> TopdownTraverse:
	if _trav_room != room:
		_trav_room = room
		var t := TopdownTraverse.of(room)
		_trav = t if t != null and not t.is_empty() else null
	return _trav

## The floor under a ground point, the water's surface included for a body that walks on it, and a raft's deck where
## one floats there now (T1).
func floor_at(p: Vector2) -> float:
	var h := room.height_at(p)
	var tr := traverse()
	if tr != null:
		# T1: a raft's deck over the water, a lift's over the floor under it; whole boards over a pit; a flood's water.
		if not tr.rafts.is_empty():
			var r := tr.raft_at(p)
			if not r.is_empty():
				var dz := tr.deck_z(r)
				# A raft floats on the water; a lift's or a lantern's deck (T2) hangs over whatever floor is under it. A body
				# below a hanging lantern (more than the mantle's reach under its lid) passes under it.
				var under_lantern := str(r.kind) == "lantern" and z < dz - mantle - 0.5
				if h == TopdownRoom.WATER_Z or (str(r.kind) != "raft" and dz >= h - 0.5 and not under_lantern): return dz
		if not tr.crumbles.is_empty():
			var cb := tr.crumble_at(p)
			if not cb.is_empty() and float(cb.z) > h: return float(cb.z)
			# T2: boards that were the floor itself, gone: the floor under them, or a hole (water, a pit).
			var gone := tr.crumble_gone_at(p) if cb.is_empty() else {}
			if not gone.is_empty() and absf(float(gone.z) - h) < 0.5: return float(gone.under)
		if not tr.cracks.is_empty():
			# T3: a cracked slab stands over the floor until a Plunge breaks it.
			var ck := tr.crack_at(p)
			if not ck.is_empty() and float(ck.z) > h: return float(ck.z)
		if not tr.floods.is_empty() and h < INF and not water_walk and tr.flooded(p, h): return TopdownRoom.WATER_Z
	return 0.0 if water_walk and h == TopdownRoom.WATER_Z else h

## The raft whose deck is at a ground point now ({} when none, or the room has none).
func _raft_under(p: Vector2) -> Dictionary:
	var tr := traverse()
	return {} if tr == null or tr.rafts.is_empty() else tr.raft_at(p)

## The cell under a point is open water a walking body stops at (a raft's deck over it is a floor, and whole boards).
func _water_at(c: Vector2) -> bool:
	var cp := TopdownRoom.cell_of(c)
	var tr := traverse()
	if room.is_water(cp.x, cp.y): return _raft_under(c).is_empty() and (tr == null or tr.crumbles.is_empty() or tr.crumble_at(c).is_empty())
	if tr == null: return false
	if _hole_at(c) != "": return true   # T2: boards that were the floor gave way over water or a pit
	return not tr.floods.is_empty() and floor_at(c) == TopdownRoom.WATER_Z and room.height_at(c) < INF

## T2 · the hole at a ground point where flush boards gave way ("water", "pit"; "" when none, or a deck hangs over it).
func _hole_at(c: Vector2) -> String:
	var tr := traverse()
	if tr == null or tr.crumbles.is_empty(): return ""
	var gone := tr.crumble_gone_at(c)
	if gone.is_empty() or str(gone.hole) == "" or not _raft_under(c).is_empty(): return ""
	return str(gone.hole)

## T2 · open water a body with Breath Control swims (the room's own water, not a flood's nor a hole's).
func _swims_at(c: Vector2) -> bool:
	var cp := TopdownRoom.cell_of(c)
	return swim and not water_walk and room.is_water(cp.x, cp.y) and _raft_under(c).is_empty()

## T1 · the push of a current on a body standing in it (the side view's current volume: only while it stands).
func _current() -> Vector2:
	var tr := traverse()
	if tr == null or tr.currents.is_empty() or not grounded or plunging or ride != "": return Vector2.ZERO   # a deck rides over it
	return tr.current_at(pos)

## T2 · the wind's push on a body standing in it (the side view's wind volume: strong for part of its cycle, a breeze the
## rest, harder within `wind_edge` of a drop).
func _wind() -> Vector2:
	var tr := traverse()
	if tr == null or tr.winds.is_empty() or not grounded or plunging or not climbing.is_empty(): return Vector2.ZERO
	var wv := tr.wind_at(pos)
	if wv.is_empty(): return Vector2.ZERO
	var k := tr.wind_strength(wv)
	# T3: a drop within `wind_edge` along any of the eight ways round the body (T2 looked along the four axes only, so a
	# brink cut on the diagonal was missed).
	for d in WIND_AXES:
		if floor_at(pos + (d as Vector2) * wind_edge) < z - step_up:
			k *= float(wv.edge_factor)
			break
	return (wv.push as Vector2) * k

## T2 · the pace the floor underfoot allows: the shallows slow a wading body (a floor under shallow water: the tile set's
## `flood`, the side view's water_shallow), and a swimmer goes at the swim's pace.
func _pace() -> float:
	if swimming: return swim_factor * (1.0 + swim_surge * cos(TAU * stroke_t / maxf(0.1, swim_stroke)))   # T3: the stroke's surge
	if wade_free or not grounded: return 1.0
	if _wading_room != room:
		_wading_room = room
		_wading = {}
		var paints: Dictionary = room.tileset.get("paint", {})
		for mark in paints:
			if bool((paints[mark] as Dictionary).get("flood", false)): _wading[str(mark)] = true
	if _wading.is_empty() or ride != "": return 1.0
	var cp := TopdownRoom.cell_of(pos)
	return shallow_factor if _wading.has(room.paint_at(cp.x, cp.y)) and absf(z - room.height_at(pos)) < 0.5 else 1.0

## The nearest spot to `p` a body stands on dry: `p` itself unless the water has come over it (a flood risen over the last
## safe spot sends the body to the nearest dry floor instead). T2: within a level of the safe spot's floor where there is
## one (a gallery, a rock, the dry edge of the room; never the top of a pillar the flood laps).
func _dry(p: Vector2) -> Vector2:
	if not _water_at(p): return p
	var c0 := TopdownRoom.cell_of(p)
	var near := Vector2.INF
	for r in range(1, maxi(room.w, room.h)):
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r: continue
				var q := (Vector2(c0 + Vector2i(dx, dy)) + Vector2(0.5, 0.5)) * TopdownRoom.TILE
				if not room.standable(TopdownRoom.cell_of(q)) or _water_at(q): continue
				if floor_at(q) <= safe_z + TopdownRoom.LEVEL + 0.5: return q
				if near == Vector2.INF: near = q
	return near if near != Vector2.INF else p

## T1 · a raft carries its rider: the deck's move since the last frame (the room's clock, the side view's mover rule),
## before the body's own step. Boarding it is announced (the side view's mover_boarded) and sets a trigger raft off.
func _ride() -> void:
	var tr := traverse()
	if tr == null or tr.rafts.is_empty():
		ride = ""
		return
	var r := {}
	if grounded and sink_t < 0.0:
		# Still on the deck where it stood at the last frame (the clock has moved it since), else on the one under it now:
		# a raft over the water, a lift at the body's own height.
		var was := tr.raft(ride) if ride != "" else {}
		if not was.is_empty() and Rect2((was.rest as Rect2).position + ride_off, (was.rest as Rect2).size).has_point(pos): r = was
		else:
			var now := tr.raft_at(pos)
			if not now.is_empty() and absf(tr.deck_z(now) - z) <= step_up and (str(now.kind) != "raft" or room.height_at(pos) == TopdownRoom.WATER_Z): r = now
	if r.is_empty():
		ride = ""
		return
	var off := tr.raft_offset(r)
	if ride != str(r.id):
		ride = str(r.id)
		ride_off = off
		tr.trigger(ride)
		events.append({"type": "boarded", "raft": ride})
		return
	var d := off - ride_off
	ride_off = off
	if d.length() < 0.0001: return
	# The deck moved under the feet: the body goes with it, along each axis a wall does not stop.
	if not blocked_at(pos + d): pos += d
	else:
		if not blocked_at(pos + Vector2(d.x, 0.0)): pos.x += d.x
		if not blocked_at(pos + Vector2(0.0, d.y)): pos.y += d.y

## Can a dash start now (on the ground or within coyote time, not sinking)? The combat dodge asks before it spends its
## cooldown.
func can_dash() -> bool:
	return sink_t < 0.0 and (grounded or coyote > 0.0)

## Carry the body at `v` for `secs` (a knockback away from the attacker, a technique's dash): it may push off an open
## edge to the floor below; walls and the bank stop it as they stop walking.
func push(v: Vector2, secs: float) -> void:
	if sink_t >= 0.0: return
	push_v = v
	push_t = secs

## Plunge from anywhere in the air: straight down at `speed` until the floor. False on the ground, sinking or already
## plunging.
func plunge(speed: float) -> bool:
	if grounded or sink_t >= 0.0 or plunging: return false
	plunging = true
	vz = -absf(speed)
	vel = Vector2.ZERO
	dash_t = 0.0
	push_t = 0.0
	long_jump = false
	buffer = 0.0
	coyote = 0.0
	events.append({"type": "plunged", "z": z})
	return true

func _start_dash(axis: Vector2) -> void:
	if dash_cd > 0.0 or not can_dash(): return
	var moving := axis.length() > 0.2
	dash_dir = axis.normalized() if moving else -dir
	dash_t = (dash_distance if moving else back_step) / dash_speed
	dash_cd = dash_cooldown
	invuln = invuln_s
	since_dash = 0.0
	events.append({"type": "dashed", "back": not moving})

func _substep(h: float, axis: Vector2) -> void:
	dash_cd = maxf(0.0, dash_cd - h)
	invuln = maxf(0.0, invuln - h)
	land_t = maxf(0.0, land_t - h)
	land_hold = maxf(0.0, land_hold - h)
	buffer = maxf(0.0, buffer - h)
	since_dash += h
	if sink_t >= 0.0:
		sink_t += h
		z -= 60.0 * h
		if sink_t >= reset_s:
			place(_dry(safe))
			events.append({"type": "reset"})
		return
	# T2 · Breath Control: a swimmer's breath runs out over `swim_s`; then it sinks, as a body without the art does at once.
	if swimming:
		swim_left -= h
		if swim_left <= 0.0 or not grounded or not _swims_at(pos):
			if swim_left <= 0.0:
				swimming = false
				sink_t = 0.0
				vel = Vector2.ZERO
				events.append({"type": "splashed", "fall": 0.0, "plunge": false, "breath": true})
				return
			if grounded: swimming = false   # hauled out onto the bank
	elif grounded and climbing.is_empty(): swim_left = swim_s
	if buffer > 0.0 and (grounded or coyote > 0.0): _jump()
	# Horizontal velocity: the dash holds its own; otherwise accelerate toward the stick (a sprint past the tiptoe band,
	# the tiptoe within it), with a third of that control in the air, where the stick steers no faster than the walk,
	# brakes harder pulled against the motion, and let go slows the body to a stop (decision 43; a long jump keeps its
	# carry unless the stick pulls it back).
	magnet_on = false
	if plunging:
		vel = Vector2.ZERO
	elif push_t > 0.0:
		push_t -= h
		vel = push_v
		if push_t <= 0.0: vel = Vector2.ZERO
	elif dash_t > 0.0:
		dash_t -= h
		vel = dash_dir * dash_speed
		if dash_t <= 0.0 and grounded: vel = dash_dir * (sprint if axis.length() > tiptoe_axis else walk * tiptoe) if axis.length() > 0.2 else Vector2.ZERO
	else:
		var mag := minf(1.0, axis.length())
		if mag > 0.05 and grounded: running = mag > tiptoe_axis
		var target := axis.normalized() * (sprint if mag > tiptoe_axis else walk * tiptoe) * speed_k * _pace() if mag > 0.05 else Vector2.ZERO
		# T2 · ice (the side view's traction rule): underfoot, the body gains or sheds at most its traction of speed a second,
		# so it slides on and slides to a stop.
		var ice: Dictionary = traverse().ice_at(pos) if grounded and traverse() != null and not traverse().ices.is_empty() and not swimming else {}
		if not ice.is_empty(): vel = vel.move_toward(target, float(ice.traction) * h)
		elif grounded: vel = vel.move_toward(target, (accel if target != Vector2.ZERO else decel) * h)
		elif flying:
			# T1 · flight (Cloud Stride): the stick steers the body over anything lower than it at the walk's pace, at once.
			vel = vel.move_toward(axis.normalized() * walk * fly_k * speed_k if mag > 0.05 else Vector2.ZERO, accel * h)
		elif gliding:
			# T1 · Falling Leaf Glide: the body sails on at the drift (the side view's x1.1 of the walk), steered by the
			# stick at the air's pick-up, along the way it was going when the stick is let go: a glide is a dash across a
			# gap. The landing assist still brakes it onto a top it would overshoot.
			if not _magnet(h, axis):
				var gd := walk * glide_drift
				var way := axis.normalized() if mag > 0.05 else (vel.normalized() if vel.length() > 1.0 else dir)
				vel = vel.move_toward(way * gd, accel * air_control * h)
		else:
			var against := target != Vector2.ZERO and vel.length() > 1.0 and target.normalized().dot(vel.normalized()) < -0.2
			if _magnet(h, axis): pass   # the landing assist brakes; the stick does not push on along the jump meanwhile
			elif target != Vector2.ZERO and not long_jump:
				vel = vel.move_toward(target.limit_length(walk), accel * air_control * (air_turn if against else 1.0) * h)
			elif against: vel = vel.move_toward(Vector2.ZERO, accel * air_control * air_turn * h)
			elif target == Vector2.ZERO and not long_jump: vel = vel.move_toward(Vector2.ZERO, air_brake * h)
	if axis.length() > 0.2 and dash_t <= 0.0 and push_t <= 0.0 and not lock_face and not plunging: _face(axis)
	_turn_row(h)
	# T3 · the swim's stroke: a pull every `swim_stroke` seconds while the swimmer moves (the first at once), announced.
	var stroking := swimming and grounded and axis.length() > 0.2
	var was := stroke_t
	stroke_t = fposmod(stroke_t + h, maxf(0.1, swim_stroke)) if stroking else 0.0
	if stroking and (was <= 0.0 or stroke_t < was): events.append({"type": "stroked"})
	# A gust or a current (S17, the World authority's hazard drift) carries the body on top of its own step; walls and
	# the bank stop it as they stop walking.
	var v := vel + (drift if not plunging else Vector2.ZERO) + _current() + _wind()
	_move(Vector2(v.x * h, 0.0), axis)
	_move(Vector2(0.0, v.y * h), axis)
	_vertical(h)

func _jump() -> void:
	var carried := dash_t > 0.0 or since_dash <= long_window + dash_distance / dash_speed
	swimming = false   # T2: a swimmer's jump out of the water
	vz = impulse
	peak = z
	if grounded: _took_off()
	grounded = false
	coyote = 0.0
	buffer = 0.0
	jumps = 1
	if carried and dash_dir != Vector2.ZERO:
		long_jump = true
		vel = dash_dir * long_speed
		dash_t = 0.0
	else:
		vel = vel.limit_length(walk)   # decision 42: a sprint's jump reaches as the walk's did
	events.append({"type": "jumped", "long": long_jump, "z": z})

## The body leaves the floor it stood on (a jump or a step off an edge): the landing assist keeps that floor apart.
func _took_off() -> void:
	takeoff_z = z
	crossed_low = false
	magnet_used = false
	land_hold = 0.0
	jumps = 1
	wall_kicks = 0

## T1 · Cloud Ladder Step (the side view's double jump): once an airtime, a second jump at its own impulse, from
## wherever the body is in the air (not out of a Plunge or a Swallow Dart's hold).
func _double_jump() -> bool:
	if not double_jump or jumps >= 2 or hold_t > 0.0: return false
	jumps = 2
	vz = float(conf("traverse.double_jump_impulse", 325.0))
	peak = maxf(peak, z)
	gliding = false
	long_jump = false
	events.append({"type": "double_jumped", "z": z})
	return true

## T1 · Wall-Step: in the air, the stick pushing into a wall face (a floor above the mantle's reach, a prop, the room's
## edge) within `wall_reach`: a kick up at its own speed and off the wall, three an airtime. True when it kicked.
func _wall_kick(axis: Vector2) -> bool:
	if not wall_step or wall_kicks >= int(conf("traverse.wall_kicks", 3)) or axis.length() < 0.5 or hold_t > 0.0: return false
	var into := axis.normalized()
	# The wall straight along the push: east, west, north or south (the face a body can push against on the grid).
	var side := Vector2(signf(into.x), 0.0) if absf(into.x) >= absf(into.y) else Vector2(0.0, signf(into.y))
	var reach := float(conf("traverse.wall_reach", 12.0)) + (half.x if side.x != 0.0 else half.y)
	var probe := pos + side * reach
	var cp := TopdownRoom.cell_of(probe)
	if not (room.level(cp.x, cp.y) == TopdownRoom.SOLID or floor_at(probe) > z + mantle): return false
	wall_kicks += 1
	vz = float(conf("traverse.wall_kick_speed", 340.0))
	peak = maxf(peak, z)
	gliding = false
	long_jump = false
	var away_s := float(conf("traverse.wall_away_s", 0.2))
	push(-side * float(conf("traverse.wall_away", 60.0)) / away_s, away_s)
	face(-side)
	events.append({"type": "wall_kicked", "side": side, "kicks": wall_kicks})
	return true

## T1 · Swallow Dart: the height held for `secs` while Combat's dart carries the body (its forced motion, a push).
func air_hold(secs: float) -> void:
	if grounded or secs <= 0.0: return
	hold_t = secs
	vz = 0.0
	gliding = false

# ------------------------------------------------------------------ T1: climbable faces
## Climb on at the foot (or, `from_top`, over the top's edge): the body against the face, Combat's arts and the dash
## put away until it steps off. False when it cannot (in the air, sinking, already on one).
func start_climb(c: Dictionary, from_top: bool) -> bool:
	if c.is_empty() or not climbing.is_empty() or not grounded or sink_t >= 0.0 or plunging: return false
	climbing = c
	climb_k = 1.0 if from_top else 0.0
	climb_moving = false
	vel = Vector2.ZERO
	vz = 0.0
	dash_t = 0.0
	push_t = 0.0
	long_jump = false
	gliding = false
	grounded = false
	ride = ""
	_climb_place()
	face(c.dir)
	events.append({"type": "climb_started", "climbable": str(c.id)})
	return true

## Where a body on the face stands: against it on the foot's side, at the height the climb has reached.
func _climb_place() -> void:
	var c := climbing
	var d: Vector2 = c.dir
	var back := (half.y if absf(d.y) > 0.5 else half.x) + 1.0
	pos = (c.face as Vector2) - d * back
	z = lerpf(float(c.foot_z), float(c.top_z), climb_k)
	peak = z

## One substep on the face: the stick toward the top climbs, away from it climbs down, at the climb's speed; at either
## end the body steps off onto that floor.
func _climb_step(h: float, axis: Vector2) -> void:
	var c := climbing
	var along := axis.dot(c.dir) if axis.length() > 0.2 else 0.0
	if absf(along) < 0.3: along = 0.0
	climb_moving = along != 0.0
	var height := maxf(1.0, float(c.top_z) - float(c.foot_z))
	climb_k = clampf(climb_k + signf(along) * climb_speed * h / height, 0.0, 1.0)
	_climb_place()
	if climb_k >= 1.0 and along > 0.0: _leave_climb("top")
	elif climb_k <= 0.0 and along < 0.0: _leave_climb("foot")

func _leave_climb(end: String) -> void:
	var c := climbing
	var d: Vector2 = c.dir
	climbing = {}
	climb_moving = false
	if end == "top":
		pos = (c.face as Vector2) + d * ((half.y if absf(d.y) > 0.5 else half.x) + 2.0)
		z = float(c.top_z)
	else:
		z = float(c.foot_z)
	vz = 0.0
	vel = Vector2.ZERO
	grounded = true
	coyote = 0.0
	buffer = 0.0
	_took_off()
	jumps = 0
	events.append({"type": "climb_finished", "climbable": str(c.id), "end": end})

## Let go of the face: a hop back off it (`jumped`, Jump pressed on it) or knocked off by a blow; either way the body
## falls to the floor at its foot.
func release_climb(jumped: bool) -> void:
	if climbing.is_empty(): return
	var c := climbing
	var d: Vector2 = c.dir
	climbing = {}
	climb_moving = false
	grounded = false
	_took_off()
	takeoff_z = float(c.foot_z)
	peak = z
	vz = impulse * 0.5 if jumped else 0.0
	vel = -d * walk * (0.6 if jumped else 0.3)
	events.append({"type": "climb_finished", "climbable": str(c.id), "end": "jump" if jumped else "knocked"})

## Decision 43 · the landing assist. In the air over a flat top (a box, a roof, a ledge; not a stair or the water) that
## is not the floor the body left (unless it crossed a gap to it), with the body above it and the stick along the jump:
## when the jump as it goes would carry past the top's far edge before coming down to it, by no more than `magnet`
## units, it brakes smoothly (at most `magnet_decel`) so the body comes down `magnet_margin` inside that edge; once it
## has taken hold it holds to the landing. True while it brakes (the stick then does not push on along the jump).
func _magnet(h: float, axis: Vector2) -> bool:
	var here := floor_at(pos)
	if here < takeoff_z - step_up: crossed_low = true
	if magnet <= 0.0 or plunging or push_t > 0.0 or dash_t > 0.0 or here == INF or here > z + 0.01: return false
	if absf(here - takeoff_z) <= 0.5 and not crossed_low: return false   # the floor it left
	var speed := vel.length()
	if speed < 1.0 or axis.length() < 0.2 or axis.normalized().dot(vel / speed) < 0.3: return false
	var cp := TopdownRoom.cell_of(pos)
	if room.is_water(cp.x, cp.y) or not room.stair_at(cp.x, cp.y).is_empty(): return false
	var g := gravity * gravity_k()
	var t := (vz + sqrt(maxf(0.0, vz * vz + 2.0 * g * (z - here)))) / g   # to come down to the top
	if t <= h: return false
	var d := vel / speed
	var travel := speed * t
	var ahead := _run_on(here, d, travel + magnet_margin + 2.0)
	var keep := ahead - magnet_margin
	var over := travel - keep
	if over <= 0.0: return false
	if not magnet_used and (over > magnet or keep < 0.0): return false   # it takes hold only of a near miss
	keep = maxf(keep, 0.0)
	var a := minf(2.0 * (travel - keep) / (t * t), magnet_decel)
	vel -= d * minf(a * h, speed)
	magnet_on = true
	magnet_used = true
	return true

## How far along `d` from the body the flat top at height `top` goes on (up to `most`), in 2-unit steps.
func _run_on(top: float, d: Vector2, most: float) -> float:
	var s := 0.0
	while s < most:
		var p := pos + d * (s + 2.0)
		var cp := TopdownRoom.cell_of(p)
		if absf(floor_at(p) - top) > 0.5 or not room.stair_at(cp.x, cp.y).is_empty(): return s
		s += 2.0
	return most

func _vertical(h: float) -> void:
	var ground := floor_at(pos)
	if grounded:
		if ground < z - step_up:
			_took_off()
			grounded = false
			coyote = coyote_s
			vz = 0.0
			peak = z
			if dash_t <= 0.0 and push_t <= 0.0: vel = vel.limit_length(walk)   # a sprint off a ledge drops as the walk did
			events.append({"type": "fell", "z": z})
		else:
			z = ground   # stairs and small steps follow the floor
			# A safe spot is never a raft's deck (it moves on) nor the water's surface (T1), nor boards that may give way (T2).
			var trs := traverse()
			if _clear_ground() and ride == "" and room.height_at(pos) != TopdownRoom.WATER_Z and (trs == null or trs.crumbles.is_empty() or trs.crumble_at(pos).is_empty()):
				safe = pos
				safe_z = z
			# T1 · Water Skimming: stepping out onto the water's surface is the art's use, announced once an outing.
			var on_water := water_walk and room.height_at(pos) == TopdownRoom.WATER_Z and ride == ""
			if on_water and not skimming: events.append({"type": "skimmed"})
			skimming = on_water
			# T1 · rotten boards underfoot start to give way (the side view's crumble).
			var tr := traverse()
			if tr != null and not tr.crumbles.is_empty():
				var cb := tr.crumble_at(pos)
				if not cb.is_empty() and absf(float(cb.z) - z) < 0.5: tr.touch(cb)
				# T3 · gone boards that were the floor wait while the body stands under them (the floor they drop to), so
				# coming back they never lift it onto them.
				var gone := tr.crumble_gone_at(pos) if cb.is_empty() else {}
				if not gone.is_empty() and str(gone.hole) == "" and absf(float(gone.under) - z) < 0.5: tr.hold(gone)
		return
	coyote = maxf(0.0, coyote - h)
	if flying:
		_fly_step(h)
		return
	var up := updraft_here()
	if plunging: z += vz * h   # the Plunge holds its speed
	elif hold_t > 0.0:
		hold_t = maxf(0.0, hold_t - h)   # T1 · Swallow Dart holds the height while it carries the body
		vz = 0.0
	elif not up.is_empty() and vz < float(up.speed):
		# T1 · an updraft eases the fall into a rise toward its speed while falling or gliding (the side view's rule).
		z += vz * h
		vz += (float(up.speed) - vz) * minf(1.0, updraft_ease * h)
	elif gliding and vz <= -glide_fall:
		vz = -glide_fall   # T1 · Falling Leaf Glide caps the fall
		z += vz * h
	else:
		# T3 · a live low-gravity volume lightens the fall, never the jump (the side view's rule): the same impulse, its
		# share of the pull, so a jump in it climbs higher and comes down slower.
		var g := gravity * gravity_k()
		z += vz * h - 0.5 * g * h * h   # exact within the step, so the apex and airtime match the numbers
		vz -= g * h
		if gliding: vz = maxf(vz, -glide_fall)
	peak = maxf(peak, z)
	_push_out()
	ground = floor_at(pos)
	if z <= ground:
		z = ground
		if vz <= 0.0: _land()

## T1 · flight (Cloud Stride; Combat grants it and pays its QI): from the air the body holds its height; `fly_input`
## (+1 Jump held, -1 Evade held) climbs or descends at `fly_climb`, never past `fly_ceiling` over the floor under it
## (an updraft lifts a flier at half its speed, as in the side view). Coming down onto a floor lands, and ends it.
func fly(on: bool) -> void:
	if on and (grounded or sink_t >= 0.0 or not climbing.is_empty()): return
	flying = on
	if on:
		vz = 0.0
		gliding = false
		plunging = false
		hold_t = 0.0
		long_jump = false
		events.append({"type": "took_off"})

func _fly_step(h: float) -> void:
	var under := floor_at(pos)
	var lift := 0.0
	var up := updraft_here()
	if fly_input >= 0.0 and not up.is_empty(): lift = float(up.speed) * 0.5
	vz = fly_input * fly_climb + lift
	var top := (under if under < INF else z) + fly_ceiling
	var nz := z + vz * h
	if vz > 0.0: nz = minf(nz, maxf(top, z))   # never past the ceiling (over a drop it holds where it is)
	z = nz
	peak = maxf(peak, z)
	_push_out()
	under = floor_at(pos)
	if z <= under and fly_input < 0.0:
		z = under
		flying = false
		events.append({"type": "flight_landed"})
		_land()
	elif z < under: z = under

## T3 · the share of gravity's pull on the body where it is: a live low-gravity volume's (TopdownTraverse.gravity_at),
## 1.0 elsewhere or in a room with none.
func gravity_k() -> float:
	var tr := traverse()
	return 1.0 if tr == null or tr.lowgs.is_empty() else tr.gravity_at(pos)

## T1: the updraft the body is in, in the air ({} when none, or the room has none, or it plunges).
func updraft_here() -> Dictionary:
	var tr := traverse()
	return {} if tr == null or tr.updrafts.is_empty() or plunging else tr.updraft_at(pos, z)

func _land() -> void:
	# T3 · a Plunge coming down on a cracked slab breaks it and falls on through (the side view's rule 10): the body is
	# still plunging, onto the floor under the slab, where it lands and strikes.
	if plunging:
		var trc := traverse()
		var ck: Dictionary = trc.crack_at(pos) if trc != null and not trc.cracks.is_empty() else {}
		if not ck.is_empty() and absf(float(ck.z) - z) < 0.5:
			trc.break_crack(ck)
			events.append({"type": "cracked", "crack": str(ck.id), "z": z})
			return
	var fall := peak - z
	var plunged := plunging
	grounded = true
	vz = 0.0
	long_jump = false
	plunging = false
	gliding = false
	hold_t = 0.0
	jumps = 0
	if plunged: buffer = 0.0   # a Jump pressed on the way down does not bounce out of the impact
	# T2: a pit takes a skimmer too (Water Skimming runs on water, not on air).
	if (_water_at(pos) and not water_walk) or _hole_at(pos) == "pit":
		# T2 · Breath Control: open water is swum while the breath lasts (a splash, then the swim).
		if _swims_at(pos) and swim_left > 0.0:
			swimming = true
			land_t = squash_s
			events.append({"type": "swam", "fall": fall, "plunge": plunged})
			return
		sink_t = 0.0
		vel = Vector2.ZERO
		# T2: a pit under boards that gave way swallows the body without a splash (its spikes are the World authority's).
		events.append({"type": "pitfall" if _hole_at(pos) == "pit" else "splashed", "fall": fall, "plunge": plunged})
		return
	swimming = false
	land_t = squash_s
	# Decision 43: a landing on a top the body jumped onto (higher than the floor it left, or across a gap, or the
	# landing assist's) holds at the top's edge a moment, so a stick still pushed along the jump does not run it off.
	var assisted := magnet_used
	if assisted or z >= takeoff_z + step_up or (crossed_low and z >= takeoff_z - 0.5): land_hold = magnet_hold_s
	magnet_used = false
	events.append({"type": "landed", "fall": fall, "plunge": plunged, "assisted": assisted})
	# T1 · a bounce (the Fairground's drum, a lily pad, the bent bamboo) launches the body straight back up.
	var tr := traverse()
	var b: Dictionary = tr.bounce_at(pos, z) if tr != null and not tr.bounces.is_empty() and not plunged else {}
	if not b.is_empty():
		_took_off()
		grounded = false
		vz = float(b.speed)
		peak = z
		b.sprung = tr.time   # T3: the drum's skin, the leaf, the culm give under it and spring back (TopdownTraverseView)
		events.append({"type": "bounced", "bounce": str(b.id)})
		return
	if buffer > 0.0 and not plunged: _jump()

## A point is clear of the edges when every corner of the foot box is on the same floor as its centre.
func _clear_ground() -> bool:
	for c in _corners(pos):
		if absf(floor_at(c) - z) > 0.5: return false
	return true

func _corners(p: Vector2) -> Array:
	return [p + Vector2(-half.x, -half.y), p + Vector2(half.x, -half.y), p + Vector2(-half.x, half.y), p + Vector2(half.x, half.y)]

## A cell corner blocks when it holds a prop or the room's edge, water while walking (the bank: only a jump takes you
## over water), or a floor above the body's reach: one step (8) on the ground, the mantle (12) in the air.
func _corner_blocks(c: Vector2) -> bool:
	var cp := TopdownRoom.cell_of(c)
	if room.level(cp.x, cp.y) == TopdownRoom.SOLID: return true
	if grounded and not water_walk and _water_at(c) and not _swims_at(c): return true   # T1: a raft's deck is a floor, and whole boards
	var tr := traverse()
	if tr != null and not tr.hatches.is_empty() and not tr.hatch_at(c).is_empty(): return true   # T2: a sealed hatch
	return floor_at(c) > z + (swim_out if swimming else step_up if grounded else mantle)

func blocked_at(p: Vector2) -> bool:
	for c in _corners(p):
		if _corner_blocks(c): return true
	return false

## Move along one axis as far as the floor lets (halving the step into a wall), then slide round a corner the box
## only clips: when the stick points mostly along this axis and a small side step clears the way.
func _move(delta: Vector2, axis: Vector2) -> void:
	if delta.length() < 0.00001: return
	# Decision 43: just after an assisted landing the top's edge holds the body a moment, so a stick still pushed along
	# the jump does not run it off the far side before the thumb lets go.
	if land_hold > 0.0 and grounded and floor_at(pos + delta) < z - step_up: return
	if not blocked_at(pos + delta):
		pos += delta
		return
	var part := delta
	for i in 4:
		part *= 0.5
		if not blocked_at(pos + part): pos += part
	var along := absf(axis.x) if delta.x != 0.0 else absf(axis.y)
	var across := absf(axis.y) if delta.x != 0.0 else absf(axis.x)
	if along < 0.5 or across > 0.35: return
	var side := Vector2(0, 1) if delta.x != 0.0 else Vector2(1, 0)
	for d in range(2, int(nudge) + 1, 2):
		for s in [-1.0, 1.0]:
			var shift: Vector2 = side * s * float(d)
			if not blocked_at(pos + shift) and not blocked_at(pos + shift + delta):
				var step_len := minf(float(d), delta.length())
				pos += side * s * step_len
				return

## In the air a body that ends up inside a higher floor (walking off a ledge leaves the back of the foot box over it)
## is pushed out the shorter way.
func _push_out() -> void:
	for i in 2:
		var moved := false
		for c in _corners(pos):
			var cp := TopdownRoom.cell_of(c)
			if not (room.level(cp.x, cp.y) == TopdownRoom.SOLID or floor_at(c) > z + mantle): continue
			var cell := Rect2(Vector2(cp) * TopdownRoom.TILE, Vector2.ONE * TopdownRoom.TILE)
			var px: float = (cell.position.x - c.x - 0.01) if c.x > pos.x else (cell.end.x - c.x + 0.01)
			var py: float = (cell.position.y - c.y - 0.01) if c.y > pos.y else (cell.end.y - c.y + 0.01)
			pos += Vector2(px, 0) if absf(px) < absf(py) else Vector2(0, py)
			moved = true
			break
		if not moved: return

## Turn to face `v` at once (an attack's aim), with the drawn row's hysteresis.
func face(v: Vector2) -> void:
	if v.length() <= 0.01: return
	dir = v.normalized()
	row = nearest_row(dir, row, ROW_ANGLES, 10.0)
	row_t = turn_row_s

## 8-way analog facing from the stick; the drawn row follows in _turn_row.
func _face(axis: Vector2) -> void:
	dir = axis.normalized()

## The drawn row (S, SE, E, NE, N, and NW, W, SW that mirror NE, E, SE) changes only when the facing sits 10° nearer
## another row (plan §1.4). Decision 43: a swing of more than one row turns through the rows between, one every
## `turn_row_s` (the first at once), the way past the camera (S) for a half turn, so a turn round reads as a turn.
func _turn_row(h: float) -> void:
	var want := nearest_row(dir, row, ROW_ANGLES, 10.0)
	if want == row:
		row_t = turn_row_s
		return
	row_t += h
	if turn_row_s <= 0.0:
		row = want
		return
	if row_t < turn_row_s: return
	row_t = 0.0
	var order := ["e", "se", "s", "sw", "w", "nw", "n", "ne"]
	var i := order.find(row)
	var j := order.find(want)
	if i < 0 or j < 0:
		row = want
		return
	var d := posmod(j - i, 8)
	var way := 1 if d < 4 else (-1 if d > 4 else (1 if posmod(2 - i, 8) <= 4 else -1))
	row = order[posmod(i + way, 8)]

## The drawn row of `rows` (name -> its angle on the ground in degrees, east 0, south 90) for direction `v`: the nearest,
## but `current` stays until another is `band` degrees nearer (the hysteresis of plan §1.4; the foes' eight facings
## use it too).
static func nearest_row(v: Vector2, current: String, rows: Dictionary, band := 20.0) -> String:
	var a := v.angle()
	var best := current if rows.has(current) else str(rows.keys()[0])
	for r in rows:
		if absf(angle_difference(a, deg_to_rad(rows[r]))) < absf(angle_difference(a, deg_to_rad(rows[best]))): best = r
	if not rows.has(current): return best
	var cur := absf(rad_to_deg(angle_difference(a, deg_to_rad(rows[current]))))
	var nxt := absf(rad_to_deg(angle_difference(a, deg_to_rad(rows[best]))))
	return best if cur - nxt >= band else current

func drain() -> Array:
	var out := events
	events = []
	return out
