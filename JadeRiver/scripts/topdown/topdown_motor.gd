class_name TopdownMotor
extends RefCounted
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1.6): the character controller on a TopdownRoom.
## 8-way analog walking with acceleration and a tiptoe band, a Jump button (decision 28: jumping is always on the
## button) that clears one level, falls down any open edge, coyote time and an input buffer, a dash that doubles as a
## long jump when Jump follows it, and collision per height level with corner sliding. Ground plane (x, depth y) plus
## height z in world units, stepped at 120 Hz; numbers from movement.json `topdown`. Nothing here draws: the view
## reads the state and drains `events`.

const STEP := 1.0 / 120.0

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
var row := "s"             ## the drawn facing: s, e, n or w (w mirrors e)
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

var walk: float
var tiptoe_axis: float
var tiptoe: float
var accel: float
var decel: float
var air_control: float
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
	accel = walk / float(conf("accel_s", 0.08))
	decel = walk / float(conf("stop_s", 0.06))
	air_control = conf("air_control", 0.35)
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
	sink_t = -1.0
	safe = p
	safe_z = z

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
	# Horizontal velocity: the dash holds its own; otherwise accelerate toward the stick (tiptoe below 0.6), with a
	# third of that control in the air, where no input keeps the momentum (and a long jump keeps its carry).
	if push_t > 0.0:
		push_t -= h
		vel = push_v
		if push_t <= 0.0: vel = Vector2.ZERO
	elif dash_t > 0.0:
		dash_t -= h
		vel = dash_dir * dash_speed
		if dash_t <= 0.0 and grounded: vel = dash_dir * walk if axis.length() > 0.2 else Vector2.ZERO
	else:
		var mag := minf(1.0, axis.length())
		var target := axis.normalized() * walk * speed_k * (tiptoe if mag <= tiptoe_axis else 1.0) if mag > 0.05 else Vector2.ZERO
		if grounded: vel = vel.move_toward(target, (accel if target != Vector2.ZERO else decel) * h)
		elif target != Vector2.ZERO and not long_jump: vel = vel.move_toward(target, accel * air_control * h)
	if axis.length() > 0.2 and dash_t <= 0.0 and push_t <= 0.0 and not lock_face: _face(axis)
	_move(Vector2(vel.x * h, 0.0), axis)
	_move(Vector2(0.0, vel.y * h), axis)
	_vertical(h)

func _jump() -> void:
	var carried := dash_t > 0.0 or since_dash <= long_window + dash_distance / dash_speed
	vz = impulse
	peak = z
	grounded = false
	coyote = 0.0
	buffer = 0.0
	if carried and dash_dir != Vector2.ZERO:
		long_jump = true
		vel = dash_dir * long_speed
		dash_t = 0.0
	events.append({"type": "jumped", "long": long_jump, "z": z})

func _vertical(h: float) -> void:
	var ground := floor_at(pos)
	if grounded:
		if ground < z - step_up:
			grounded = false
			coyote = coyote_s
			vz = 0.0
			peak = z
			events.append({"type": "fell", "z": z})
		else:
			z = ground   # stairs and small steps follow the floor
			if _clear_ground():
				safe = pos
				safe_z = z
		return
	coyote = maxf(0.0, coyote - h)
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
	grounded = true
	vz = 0.0
	long_jump = false
	var cp := TopdownRoom.cell_of(pos)
	if room.is_water(cp.x, cp.y) and not water_walk:
		sink_t = 0.0
		vel = Vector2.ZERO
		events.append({"type": "splashed", "fall": fall})
		return
	land_t = squash_s
	events.append({"type": "landed", "fall": fall})
	if buffer > 0.0: _jump()

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
	if v.length() > 0.01: _face(v)

## 8-way analog facing; the drawn row (S, E, N, W) changes only when the stick sits 20° nearer another row (plan §1.4).
func _face(axis: Vector2) -> void:
	dir = axis.normalized()
	var a := rad_to_deg(dir.angle())
	var rows := {"e": 0.0, "s": 90.0, "w": 180.0, "n": -90.0}
	var best := row
	for r in rows:
		if absf(angle_difference(deg_to_rad(a), deg_to_rad(rows[r]))) < absf(angle_difference(deg_to_rad(a), deg_to_rad(rows[best]))): best = r
	var cur := absf(rad_to_deg(angle_difference(deg_to_rad(a), deg_to_rad(rows[row]))))
	var nxt := absf(rad_to_deg(angle_difference(deg_to_rad(a), deg_to_rad(rows[best]))))
	if cur - nxt >= 20.0: row = best

func drain() -> Array:
	var out := events
	events = []
	return out
