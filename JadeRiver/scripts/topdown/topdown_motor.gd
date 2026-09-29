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
	_took_off()

## The jump's apex over its take-off, and its airtime back to the same height (movement numbers, §As built).
func apex() -> float: return impulse * impulse / (2.0 * gravity)
func airtime() -> float: return 2.0 * impulse / gravity

## One frame of input. `jump` and `dash` are presses (edges) this frame; the frame runs as 120 Hz substeps.
func step(dt: float, axis: Vector2, jump := false, dash := false) -> void:
	if jump: buffer = buffer_s
	if dash: _start_dash(axis)
	var left := dt
	while left > 0.00001:
		var h := minf(STEP, left)
		_substep(h, axis)
		left -= h

## The floor under a ground point, the water's surface included for a body that walks on it.
func floor_at(p: Vector2) -> float:
	var h := room.height_at(p)
	return 0.0 if water_walk and h == TopdownRoom.WATER_Z else h

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
			place(safe)
			events.append({"type": "reset"})
		return
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
		var target := axis.normalized() * (sprint if mag > tiptoe_axis else walk * tiptoe) * speed_k if mag > 0.05 else Vector2.ZERO
		if grounded: vel = vel.move_toward(target, (accel if target != Vector2.ZERO else decel) * h)
		else:
			var against := target != Vector2.ZERO and vel.length() > 1.0 and target.normalized().dot(vel.normalized()) < -0.2
			if _magnet(h, axis): pass   # the landing assist brakes; the stick does not push on along the jump meanwhile
			elif target != Vector2.ZERO and not long_jump:
				vel = vel.move_toward(target.limit_length(walk), accel * air_control * (air_turn if against else 1.0) * h)
			elif against: vel = vel.move_toward(Vector2.ZERO, accel * air_control * air_turn * h)
			elif target == Vector2.ZERO and not long_jump: vel = vel.move_toward(Vector2.ZERO, air_brake * h)
	if axis.length() > 0.2 and dash_t <= 0.0 and push_t <= 0.0 and not lock_face and not plunging: _face(axis)
	_turn_row(h)
	# A gust or a current (S17, the World authority's hazard drift) carries the body on top of its own step; walls and
	# the bank stop it as they stop walking.
	var v := vel + (drift if not plunging else Vector2.ZERO)
	_move(Vector2(v.x * h, 0.0), axis)
	_move(Vector2(0.0, v.y * h), axis)
	_vertical(h)

func _jump() -> void:
	var carried := dash_t > 0.0 or since_dash <= long_window + dash_distance / dash_speed
	vz = impulse
	peak = z
	if grounded: _took_off()
	grounded = false
	coyote = 0.0
	buffer = 0.0
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
	var t := (vz + sqrt(maxf(0.0, vz * vz + 2.0 * gravity * (z - here)))) / gravity   # to come down to the top
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
			if _clear_ground():
				safe = pos
				safe_z = z
		return
	coyote = maxf(0.0, coyote - h)
	if plunging: z += vz * h   # the Plunge holds its speed
	else:
		z += vz * h - 0.5 * gravity * h * h   # exact within the step, so the apex and airtime match the numbers
		vz -= gravity * h
	peak = maxf(peak, z)
	_push_out()
	ground = floor_at(pos)
	if z <= ground:
		z = ground
		if vz <= 0.0: _land()

func _land() -> void:
	var fall := peak - z
	var plunged := plunging
	grounded = true
	vz = 0.0
	long_jump = false
	plunging = false
	if plunged: buffer = 0.0   # a Jump pressed on the way down does not bounce out of the impact
	var cp := TopdownRoom.cell_of(pos)
	if room.is_water(cp.x, cp.y) and not water_walk:
		sink_t = 0.0
		vel = Vector2.ZERO
		events.append({"type": "splashed", "fall": fall, "plunge": plunged})
		return
	land_t = squash_s
	# Decision 43: a landing on a top the body jumped onto (higher than the floor it left, or across a gap, or the
	# landing assist's) holds at the top's edge a moment, so a stick still pushed along the jump does not run it off.
	var assisted := magnet_used
	if assisted or z >= takeoff_z + step_up or (crossed_low and z >= takeoff_z - 0.5): land_hold = magnet_hold_s
	magnet_used = false
	events.append({"type": "landed", "fall": fall, "plunge": plunged, "assisted": assisted})
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
	if grounded and room.is_water(cp.x, cp.y) and not water_walk: return true
	return floor_at(c) > z + (step_up if grounded else mantle)

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
