extends Node2D
## Top-down redesign, Phase 1: the playing character in the prototype room. It owns the TopdownMotor, samples the
## HUD's joystick and buttons (the same fields and calls the HUD drives on player.gd) and draws the PLACEHOLDER body
## (art/topdown/placeholder_body.png; the layered set is Phase 5). No combat yet (Phase 2): Attack only lights its ring.

const BODY := preload("res://art/topdown/placeholder_body.png")

var world: Node2D
var motor: TopdownMotor
var actor_id := ""
var authority = null
var state := {"flying": false, "climbing": {}}
# The HUD's fields (hud.gd drives these on player.gd too).
var movement := Vector2.ZERO
var joystick_engaged := false
var jump_held := false
var fly_up := false
var fly_down := false
var attack_time := 0.0
var meditating := false
var channel_time := 0.0
var channel_action := ""
var climb_hold := 0.0
var last_axis := Vector2.ZERO
var _jump := false
var _dash := false
var anim := "idle"
var frame := 0
var anim_t := 0.0
var screen := Vector2.ZERO   ## the body's feet on the world viewport, whole art px
var frames: Dictionary = {}

var plane: Vector2:
	get: return motor.pos
var altitude: float:
	get: return motor.z
var facing: int:
	get: return -1 if motor.dir.x < -0.1 else 1
var hp: float:
	get: return Game.character(actor_id).pools.hp if bound() else 100.0
var qi: float:
	get: return Game.character(actor_id).pools.qi if bound() else 100.0

func bound() -> bool:
	return actor_id != "" and Game.character(actor_id) != null

func _ready() -> void:
	frames = world.room.tileset.get("body", {}).get("frames", {})

func jump() -> void: _jump = true
func dodge() -> void: _dash = true
func attack() -> void: attack_time = 0.25
func meditate() -> void: pass
func reset_sprint() -> void: pass
func use_technique(_slot: int) -> Dictionary: return {"ok": false, "reason": "topdown_phase_1"}

## The stick, or WASD / arrows on a keyboard (Alt walks slowly, as the tiptoe band).
func axis() -> Vector2:
	if joystick_engaged or movement != Vector2.ZERO: return movement
	var k := Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))).normalized()
	return k * (0.5 if Input.is_physical_key_pressed(KEY_ALT) else 1.0)

func physics_step(delta: float) -> Array:
	last_axis = axis()
	motor.step(delta, last_axis, _jump, _dash)
	_jump = false
	_dash = false
	attack_time = maxf(0.0, attack_time - delta)
	return motor.drain()

## Pick the pose from the motor and place the node: x on whole art px, y at the sort key, the body drawn back down to
## its whole-pixel screen row (TopdownWorld keeps every key a multiple of 1/64, so the offset is exact).
func sync(delta: float) -> void:
	var m := motor
	var next := "idle"
	var f := 0
	if m.sink_t >= 0.0 or not m.grounded:
		next = "jump"
		f = 1 if m.sink_t >= 0.0 or m.vz < 120.0 else 0
	elif m.dash_t > 0.0: next = "dash"
	elif m.land_t > 0.0:
		next = "jump"
		f = 2
	elif m.vel.length() > 12.0: next = "walk"
	if next != anim:
		anim = next
		anim_t = 0.0
	anim_t += delta
	match anim:
		"idle": f = int(anim_t * 2.0) % 2
		"walk": f = int(anim_t * 8.0 * clampf(m.vel.length() / m.walk, 0.5, 1.2)) % 4
		"dash": f = int(anim_t * 12.0) % 2
	frame = f
	screen = Vector2(roundf(m.pos.x / TopdownRoom.ART), roundf((m.pos.y - m.z) / TopdownRoom.ART))
	position = Vector2(screen.x, world.room.sort_key(m.pos, m.z))
	queue_redraw()

func frame_rect() -> Rect2:
	var row := "e" if motor.row == "w" else motor.row
	var at: Array = frames.get(anim, {}).get(row, [[0, 0]])[frame]
	return Rect2(float(at[0]), float(at[1]), 32, 48)

## Draw the current frame with its feet at `feet` on `canvas` (the silhouette overlay draws the same frame).
func draw_body(canvas: CanvasItem, feet: Vector2, tint := Color.WHITE) -> void:
	var src := frame_rect()
	var flip := motor.row == "w"
	canvas.draw_set_transform(feet, 0.0, Vector2(-1, 1) if flip else Vector2.ONE)
	canvas.draw_texture_rect_region(BODY, Rect2(-16, -46, 32, 48), src, tint)
	canvas.draw_set_transform(Vector2.ZERO)

func _draw() -> void:
	var blink := motor.invuln > 0.0 and int(motor.invuln * 40.0) % 2 == 0
	draw_body(self, Vector2(0, screen.y - position.y), Color(1, 1, 1, 0.6) if blink else Color.WHITE)
