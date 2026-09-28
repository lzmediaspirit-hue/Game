extends Node2D
## Top-down redesign: the playing character in the prototype room. It owns the TopdownMotor, samples the HUD's joystick
## and buttons (the same fields and calls the HUD drives on player.gd) and draws the PLACEHOLDER body
## (art/topdown/placeholder_body.png; the layered set is Phase 5).
##
## Phase 2: bound to a character in the room's RoomRuntime (the world entered it through the World authority), every
## action is an intent to Game as in the side view. Attack and techniques aim on the plane (`aim` and `aimed`, decision
## 30), the dodge is Combat's (its cooldown, i-frames and events) carried by the motor's dash, and Combat's forced motion
## (a knockback, a technique's dash) pushes the motor. An ActorState mirrors the motor for the authorities.


var world: Node2D
var motor: TopdownMotor
var actor_id := ""
var authority = null
var state := ActorState.new()   ## the body as the authorities read it (plane, altitude, surface, velocity), from the motor
var ground: WalkSurface         ## a stand-in surface while the motor stands on the grid, so Combat can tell ground from air
# The HUD's fields (hud.gd drives these on player.gd too).
var movement := Vector2.ZERO
var joystick_engaged := false
var jump_held := false
var fly_up := false
var fly_down := false
var attack_time := 0.0
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
var figure: TopdownFigure    ## the layered character (TopdownFigure), wearing outfit()
## The aim the HUD is showing (decision 30): {kind, slot, form, dir, at, reach, half, target (EnemyState or null)}, {}
## when no thumb is aiming. The world draws it on the ground.
var aim: Dictionary = {}

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
var meditating: bool:
	get: return Game.character(actor_id).cultivator.meditating if bound() else false

## Bound: a character in the room this view entered (not the Phase 1 view tests, which run the motor alone).
func bound() -> bool:
	return actor_id != "" and Game.character(actor_id) != null and Game.room_rt != null and Game.room_rt.topdown == world.room

func _ready() -> void:
	figure = TopdownFigure.wearing(outfit())
	ground = WalkSurface.new({"id": "grid", "rect": [0, 0, world.room.w * TopdownRoom.TILE, world.room.h * TopdownRoom.TILE], "stratum": "ground"})
	_mirror()

func jump() -> void:
	if bound() and (Game.combat.is_wounded(actor_id) or Game.character(actor_id).pools.blocked("move")): return
	_jump = true

## A tap of Dodge: Combat's dodge (its cooldown, second charge, i-frames), carried by the motor's dash.
func dodge() -> void:
	if not bound():
		_dash = true
		return
	if not motor.can_dash(): return
	var r := Game.submit({"type": "dodge", "direction": last_axis, "facing": facing, "moves": false})
	if r.get("ok", false):
		motor.dash_cd = 0.0   # Combat keeps the cooldown
		_dash = true

## A tap of Attack: the soft lock (the nearest foe in the cone round the stick, else the facing).
func attack() -> void:
	if not bound():
		attack_time = 0.25
		return
	aim_attack(last_axis if last_axis.length() > 0.2 else motor.dir, false)

## An attack along `dir` on the plane; `aimed` (a dragged aim) snaps only to a foe within a few degrees.
func aim_attack(dir: Vector2, aimed := true) -> Dictionary:
	var r := Game.submit({"type": "basic_attack", "facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "aimed": aimed})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	return r

## A tap of a technique: cast at the soft lock.
func use_technique(slot: int) -> Dictionary:
	return aim_technique(slot, last_axis if last_axis.length() > 0.2 else motor.dir, -1.0, false)

## A technique aimed along `dir`; `k` (0..1 of its reach, -1 for the lock's) places a circle at a point.
func aim_technique(slot: int, dir: Vector2, k := -1.0, aimed := true) -> Dictionary:
	if not bound(): return {"ok": false, "reason": "unbound"}
	var t := _technique(slot)
	var dist := k * TopdownAim.reach_of(t) if k >= 0.0 else -1.0
	var r := Game.submit({"type": "use_technique", "slot": slot, "facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "aimed": aimed, "dist": dist})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	return r

func _technique(slot: int) -> Dictionary:
	var c = Game.character(actor_id)
	if c == null or slot < 0 or slot >= c.cultivator.technique_slots.size() or c.cultivator.technique_slots[slot] == null: return {}
	return ContentDB.entry("techniques", str(c.cultivator.technique_slots[slot]))

## What an aiming thumb would do now (the HUD asks each frame; the world draws it): the form, its reach, and the foe it
## snaps to. `dir` zero: the soft lock round the facing.
func preview_aim(kind: String, slot: int, dir: Vector2, k: float) -> void:
	if not bound():
		aim = {}
		return
	var t := _technique(slot) if kind == "skill" else {}
	var fam := StatRules.family(Game.character(actor_id))
	var form := TopdownAim.form_of(t) if kind == "skill" else "line"
	var reach := TopdownAim.reach_of(t) if kind == "skill" else float(fam.get("reach", 46))
	var half := TopdownAim.half_width_of(t) if kind == "skill" else float(fam.get("depth", 30))
	var foes: Array = Game.room_rt.living_enemies()
	var air := not motor.grounded
	var d := dir if dir != Vector2.ZERO else motor.dir
	var foe := TopdownAim.snap(foes, motor.pos, motor.z, d, reach, air) if dir != Vector2.ZERO else TopdownAim.soft_target(foes, motor.pos, motor.z, d, air)
	if foe != null and foe.plane.distance_to(motor.pos) > 0.5: d = (foe.plane - motor.pos).normalized()
	var dist := k * reach if dir != Vector2.ZERO else (foe.plane.distance_to(motor.pos) if foe != null else reach * 0.66)
	aim = {"kind": kind, "slot": slot, "form": form, "dir": d, "reach": reach, "half": half, "target": foe,
		"at": TopdownAim.point_at(motor.pos, d, dist, reach)}

## What the body wears: the bound character's appearance, equipment and dyes (InventoryAuthority.outfit_for, as the
## side view's avatar); unbound (the Phase 1 view tests), the creator's starting clothes.
func outfit() -> Dictionary:
	return InventoryAuthority.outfit_for(Game.character(actor_id)) if bound() else TopdownFigure.DialoguePage.full_outfit({})

## The equipment changed (a piece equipped, a dye, a look from the wardrobe): dress the figure again.
func refresh_outfit() -> void:
	figure.set_outfit(outfit())

## The HUD's other calls on player.gd.
func meditate() -> void:
	if bound(): Game.submit({"type": "toggle_meditation"})
func reset_sprint() -> void: pass

## The stick, or WASD / arrows on a keyboard (Alt walks slowly, as the tiptoe band).
func axis() -> Vector2:
	if joystick_engaged or movement != Vector2.ZERO: return movement
	var k := Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP))).normalized()
	return k * (0.5 if Input.is_physical_key_pressed(KEY_ALT) else 1.0)

func physics_step(delta: float) -> Array:
	last_axis = axis()
	var move := last_axis
	if bound():
		var c = Game.character(actor_id)
		if Game.combat.is_wounded(actor_id) or c.pools.blocked("move"): move = Vector2.ZERO
		if c.pools.has_status("confusion"): move = -move
		motor.speed_k = Game.combat.move_factor(actor_id) if not Game.combat.is_wounded(actor_id) else 0.0
		motor.lock_face = Game.combat.is_busy(actor_id)
		motor.water_walk = Game.combat.knows_art(c, "water_skimming")
		var forced: Dictionary = Game.combat.forced_motion(actor_id)
		if not forced.is_empty(): motor.push(forced.velocity, float(forced.time))
	motor.step(delta, move, _jump, _dash)
	_jump = false
	_dash = false
	attack_time = maxf(0.0, attack_time - delta)
	_mirror()
	if bound(): Game.combat.face_on_plane(actor_id, motor.dir)
	return motor.drain()

## The authorities' view of the body: where it is, how high, and whether it stands on the grid.
func _mirror() -> void:
	state.plane = motor.pos
	state.altitude = motor.z
	state.velocity = motor.vel
	state.surface = ground if motor.grounded and motor.sink_t < 0.0 else null
	state.zone_id = world.room.id

## Pick the action and frame from the motor and Combat's timeline, then place the node: x on whole art px, y at the
## sort key, the body drawn back down to its whole-pixel screen row (TopdownWorld keeps every key a multiple of 1/64,
## so the offset is exact). A blow plays its own pose on Combat's clock, its hit frame on the hit; a technique with no
## pose of its own plays the hand-seal cast.
func sync(delta: float) -> void:
	var m := motor
	var tl: Dictionary = Game.combat.timeline(actor_id) if bound() else {}
	var next := "idle"
	var f := -1    # -1: the action's own clock
	if bound() and Game.combat.is_wounded(actor_id): next = "knockdown"
	elif m.sink_t >= 0.0:
		next = "jump"
		f = 3
	elif bound() and Game.combat.is_busy(actor_id):
		next = _strike_pose(tl)
		f = TopdownFigure.strike_frame(next, float(tl.t), float(tl.duration), float(tl.hit_at))
	elif attack_time > 0.0:
		next = "punch_2"
		f = TopdownFigure.strike_frame(next, 0.25 - attack_time, 0.25, 0.1)
	elif bound() and float(tl.get("flinch", 0.0)) > 0.0: next = "hurt"
	elif m.dash_t > 0.0: next = "dodge" if m.dash_dir.dot(m.dir) < -0.3 else "dash"
	elif state.plunging: next = "plunge"    # the drag-down in the air (decision 35), once the grid's Plunge sets it
	elif not m.grounded:
		next = "jump"
		f = 0 if m.vz > 340.0 else (1 if m.vz > 140.0 else (2 if m.vz > -140.0 else 3))
	elif bound() and bool(tl.get("guard", false)): next = "guard"
	elif m.land_t > 0.0:
		next = "jump"
		f = 4
	elif meditating: next = "meditate"
	elif m.vel.length() > 12.0: next = "run" if m.vel.length() > m.walk * 1.15 else "walk"
	if next != anim:
		anim = next
		anim_t = 0.0
	anim_t += delta * (clampf(m.vel.length() / m.walk, 0.5, 1.2) if anim == "walk" else 1.0)
	frame = f if f >= 0 else TopdownFigure.frame_at(anim, anim_t)
	screen = Vector2(roundf(m.pos.x / TopdownRoom.ART), roundf((m.pos.y - m.z) / TopdownRoom.ART))
	position = Vector2(screen.x, world.room.sort_key(m.pos, m.z))
	queue_redraw()

## A blow's or a technique's pose: its own drawn action (a side-view name resolves to one), or the cast for a
## technique that has no pose of its own.
func _strike_pose(tl: Dictionary) -> String:
	if str(tl.technique) != "":
		var raw = ContentDB.entry("techniques", str(tl.technique)).get("action")
		if raw == null or str(raw) in ["", "null", "meditate_burst"]: return "cast"
	return TopdownFigure.resolve(str(tl.action))

## Draw the current frame with its feet at `feet` on `canvas` (the silhouette overlay draws the same frame).
func draw_body(canvas: CanvasItem, feet: Vector2, tint := Color.WHITE) -> void:
	figure.draw(canvas, feet, anim, motor.row, frame, tint)

func _draw() -> void:
	var inv: bool = motor.invuln > 0.0 or (bound() and float(Game.combat.timeline(actor_id).dodge_t) > 0.0)
	var blink := inv and int(Time.get_ticks_msec() / 25) % 2 == 0
	var hurt := bound() and float(Game.combat.timeline(actor_id).flinch) > 0.0
	draw_body(self, Vector2(0, screen.y - position.y), Color(1, 1, 1, 0.6) if blink else (Color(1.6, 0.8, 0.8) if hurt else Color.WHITE))
