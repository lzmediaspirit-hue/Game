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
var frames: Dictionary = {}
var cell := Vector2(32, 48)     ## the body sheet's cell and the feet in it (the tile set's manifest)
var foot := Vector2(16, 46)
## The aim the HUD is showing (decision 30): {kind, slot, form, dir, at, reach, half, target (EnemyState or null)}, {}
## when no thumb is aiming. The world draws it on the ground.
var aim: Dictionary = {}
## Decision 35: the pose drawn (the sheet's row name; the guard and plunge poses fall back to idle and jump cells while
## the sheet has none) and how long the Plunge's impact pose holds after it lands.
var pose := "idle"
var impact_t := 0.0
const IMPACT_S := 0.25
## The stand-in cell for a pose the sheet does not have yet: [row, frame].
const FALLBACK := {"guard": ["idle", 0], "plunge": ["jump", 1], "plunge_land": ["jump", 2]}
var autopilot: Autopilot = null   ## Phase 4: auto-path and auto-hunt drive the stick (S49), on the grid
var stage_pose := ""              ## decision 39: the pose a staged scene holds the body in ("" for the motor's own)

var surface: WalkSurface:
	get: return state.surface

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
	var body: Dictionary = world.room.tileset.get("body", {})
	frames = body.get("frames", {})
	cell = Vector2(float(body.get("cell", [32, 48])[0]), float(body.get("cell", [32, 48])[1]))
	foot = Vector2(float(body.get("foot", [16, 46])[0]), float(body.get("foot", [16, 46])[1]))
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

## An attack along `dir` on the plane; `aimed` (a dragged aim) snaps only to a foe within a few degrees. `finisher`
## (decision 35, a long drag): the combo's last step at once.
func aim_attack(dir: Vector2, aimed := true, finisher := false) -> Dictionary:
	var r := Game.submit({"type": "basic_attack", "facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "aimed": aimed, "finisher": finisher})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	return r

## Decision 35, a long drag on Attack: the combo's finisher step at once along the drag (snapping as an aim does).
func finisher(dir: Vector2) -> Dictionary:
	return aim_attack(dir, true, true)

## Can the body plunge now: in the air (not sinking, not already dropping), the Plunge art known and ready, hands free.
func plunge_ready() -> bool:
	if not bound() or motor.grounded or motor.plunging or motor.sink_t >= 0.0: return false
	var c = Game.character(actor_id)
	return Game.combat.knows_art(c, "plunge") and c.pools.cooldown("plunge") <= 0.0 and not Game.combat.is_wounded(actor_id) and not c.pools.blocked("attack")

## Decision 35, a drag down on Attack in the air: Combat's Plunge (the art, its cooldown, the strike where it lands),
## carried by the motor's straight drop.
func plunge() -> Dictionary:
	if not bound(): return {"ok": false, "reason": "unbound"}
	var r := Game.submit({"type": "plunge"})
	if r.get("ok", false): motor.plunge(float(ContentDB.movement("plunge.speed", 900.0)))
	return r

## Decision 35, Attack held still: the slotted stance technique when one is ready (`hold_stance`), else the guard (its
## damage cut and parry window are the weapon family's). "stance", "guard", or "" when this weapon cannot guard.
func hold_guard() -> String:
	if not bound(): return ""
	if bool(TopdownAim.cfg("hold_stance", true)):
		var s := stance_slot()
		if s >= 0 and use_technique(s).get("ok", false): return "stance"
	return "guard" if Game.submit({"type": "guard_start"}).get("ok", false) else ""

func release_guard() -> void:
	if bound(): Game.submit({"type": "guard_end"})

## The first slotted stance technique (a counter form) that is off cooldown, or -1.
func stance_slot() -> int:
	var c = Game.character(actor_id) if bound() else null
	if c == null: return -1
	for i in mini(c.cultivator.technique_slots.size(), ProgressionRules.technique_slot_count(c)):
		var tid = c.cultivator.technique_slots[i]
		if tid == null or str(tid) == "": continue
		if str(ContentDB.entry("techniques", str(tid)).get("damage_type", "")) == "stance" and c.pools.cooldown("tech:" + str(tid)) <= 0.0: return i
	return -1

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
## snaps to. `dir` zero: the soft lock round the facing. `move` (decision 35): what Attack is armed for, aim,
## finisher, plunge or guard; a plunge shows its landing ring on the floor under the body, a guard its guarded front.
func preview_aim(kind: String, slot: int, dir: Vector2, k: float, move := "aim") -> void:
	if not bound():
		aim = {}
		return
	if move == "plunge" or move == "guard":
		var g := room_floor()
		aim = {"kind": kind, "slot": slot, "move": move, "form": move, "dir": motor.dir, "at": motor.pos, "ground": g,
			"reach": float(ContentDB.movement("plunge.radius", 60.0)), "half": 0.0, "target": null}
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
	aim = {"kind": kind, "slot": slot, "move": move, "form": form, "dir": d, "reach": reach, "half": half, "target": foe,
		"at": TopdownAim.point_at(motor.pos, d, dist, reach)}

## The floor's height under the body (the room's edge or a hole reads as the body's own height).
func room_floor() -> float:
	var g: float = world.room.height_at(motor.pos)
	return g if g < INF else motor.z

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
		# Phase 4, as on player.gd (S49): auto-path and auto-hunt hold the joystick until you take it; a push cancels
		# auto-path. The autopilot's stick is the stick the ways out read.
		if move.length() > 0.2:
			if Game.world.auto_path_target(c) != "": Game.submit({"type": "auto_path", "target": ""})
		elif world.get("live") == true:
			if autopilot == null: autopilot = Autopilot.new(self)
			move = autopilot.drive(c, delta)
			last_axis = move
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
	impact_t = maxf(0.0, impact_t - delta)
	var events := motor.drain()
	for e in events:
		if str(e.type) in ["landed", "splashed"] and e.get("plunge", false):
			# The Plunge lands: Combat strikes round the spot on its next tick (a splash in the water strikes nothing).
			state.plunging = false
			if str(e.type) == "landed":
				state.plunge_impact = {"x": motor.pos.x, "y": motor.pos.y, "alt": motor.z, "surface": ground.id}
				impact_t = IMPACT_S
	if state.plunging and not motor.plunging and motor.grounded: state.plunging = false
	_mirror()
	if bound(): Game.combat.face_on_plane(actor_id, motor.dir)
	return events

## The authorities' view of the body: where it is, how high, and whether it stands on the grid.
func _mirror() -> void:
	state.plane = motor.pos
	state.altitude = motor.z
	state.velocity = motor.vel
	state.surface = ground if motor.grounded and motor.sink_t < 0.0 else null
	state.zone_id = world.room.id

## Pick the pose from the motor (and Combat's timeline: an attack or cast plays the strike, arm back until its hit
## frame), place the node: x on whole art px, y at the sort key, the body drawn back down to its whole-pixel screen row
## (TopdownWorld keeps every key a multiple of 1/64, so the offset is exact).
func sync(delta: float) -> void:
	var m := motor
	var next := "idle"
	var f := 0
	var tl: Dictionary = Game.combat.timeline(actor_id) if bound() else {}
	if m.plunging: next = "plunge"
	elif impact_t > 0.0 and m.grounded: next = "plunge_land"
	elif m.sink_t >= 0.0 or not m.grounded:
		next = "jump"
		f = 1 if m.sink_t >= 0.0 or m.vz < 120.0 else 0
	elif m.dash_t > 0.0: next = "dash"
	elif bound() and Game.combat.is_busy(actor_id) or attack_time > 0.0: next = "strike"
	elif not tl.is_empty() and tl.guard: next = "guard"
	elif m.land_t > 0.0:
		next = "jump"
		f = 2
	elif m.vel.length() > 12.0: next = "walk"
	if stage_pose != "": next = stage_pose   # a staged scene's pose (decision 39)
	if next != anim:
		anim = next
		anim_t = 0.0
	anim_t += delta
	pose = anim
	match anim:
		"idle": f = int(anim_t * 2.0) % 2
		"walk": f = int(anim_t * 8.0 * clampf(m.vel.length() / m.walk, 0.5, 1.2)) % 4
		"dash": f = int(anim_t * 12.0) % 2
		"strike": f = 1 if (tl.is_empty() and anim_t > 0.08) or (not tl.is_empty() and float(tl.t) >= float(tl.hit_at)) else 0
		# Decision 35's poses (plan §1.4: guard 2 frames at 6 fps, held on the last; plunge 3 at 12, the last its impact),
		# drawn from the sheet's own rows when it has them, else from the stand-in cells in FALLBACK.
		"guard": f = mini(int(anim_t * 6.0), pose_frames("guard") - 1)
		"plunge": f = mini(int(anim_t * 12.0), maxi(0, pose_frames("plunge") - 2))
		"plunge_land":
			pose = "plunge"
			f = pose_frames("plunge") - 1
	if FALLBACK.has(anim) and pose_frames(pose) <= 0:
		pose = str(FALLBACK[anim][0])
		f = int(FALLBACK[anim][1])
	frame = f
	screen = Vector2(roundf(m.pos.x / TopdownRoom.ART), roundf((m.pos.y - m.z) / TopdownRoom.ART))
	position = Vector2(screen.x, world.room.sort_key(m.pos, m.z))
	queue_redraw()

## How many frames the sheet draws for `name` in the current facing's row (0: the sheet has no such pose).
func pose_frames(name: String) -> int:
	var row := "e" if motor.row == "w" else motor.row
	return ((frames.get(name, {}) as Dictionary).get(row, []) as Array).size()

func frame_rect() -> Rect2:
	var row := "e" if motor.row == "w" else motor.row
	var list: Array = (frames.get(pose, {}) as Dictionary).get(row, [])
	if list.is_empty(): list = (frames.get("idle", {}) as Dictionary).get(row, [[0, 0]])
	var at: Array = list[clampi(frame, 0, list.size() - 1)]
	return Rect2(Vector2(float(at[0]), float(at[1])), cell)

## Draw the current frame with its feet at `feet` on `canvas` (the silhouette overlay draws the same frame).
func draw_body(canvas: CanvasItem, feet: Vector2, tint := Color.WHITE) -> void:
	var src := frame_rect()
	var flip := motor.row == "w"
	canvas.draw_set_transform(feet, 0.0, Vector2(-1, 1) if flip else Vector2.ONE)
	canvas.draw_texture_rect_region(world.atlas("body"), Rect2(-foot, cell), src, tint)
	canvas.draw_set_transform(Vector2.ZERO)

func _draw() -> void:
	var inv: bool = motor.invuln > 0.0 or (bound() and float(Game.combat.timeline(actor_id).dodge_t) > 0.0)
	var blink := inv and int(Time.get_ticks_msec() / 25) % 2 == 0
	var hurt := bound() and float(Game.combat.timeline(actor_id).flinch) > 0.0
	draw_body(self, Vector2(0, screen.y - position.y), Color(1, 1, 1, 0.6) if blink else (Color(1.6, 0.8, 0.8) if hurt else Color.WHITE))
