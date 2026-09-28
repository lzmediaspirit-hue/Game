extends Node2D
## Top-down redesign: the playing character in the prototype room. It owns the TopdownMotor, samples the HUD's joystick
## and buttons (the same fields and calls the HUD drives on player.gd) and draws the character through TopdownFigure
## (Phase 3, decision 32): the real layers, wearing the character's equipment and dyes from the save.
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
## The figure's action drawn this frame (`anim` is the state it comes from: a strike plays the blow's own action, the
## Plunge's landing its impact frame), and how long the Plunge's impact pose holds after it lands (decision 35).
var pose := "idle"
var impact_t := 0.0
const IMPACT_S := 0.25
## While the i-frames blink, the body fades as one image in this group: faded layer by layer, the clothes would show
## the body through them.
var ghost: CanvasGroup
var tint := Color.WHITE   ## this frame's tint: red while flinching
var autopilot: Autopilot = null   ## Phase 4: auto-path and auto-hunt drive the stick (S49), on the grid
## Decision 38, the combat feel (CombatFeel): a dodge refused while a blow is committed waits `dodge_buffer` seconds for
## its cancel point; an attack in or just after a dash is a dash attack (its smear, a longer lunge); the body flashes
## white as it is struck and hops with a knockback; `action_phase` is the phase of the blow or cast the figure plays
## (anticipation, active, recovery). Decision 37's drawn moves: the dash attack is the step `dash_combo` that began it; a
## parried blow plays the parry's deflection for `parry_t`.
var dodge_buffer := 0.0
var dash_attack := false
var dash_combo := -1
var parry_t := 0.0
var hurt_t := 99.0
var knock_t := 0.0
var knock_s := 0.0
var action_phase := ""
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
	figure = TopdownFigure.wearing(outfit())
	ghost = CanvasGroup.new()
	ghost.self_modulate = Color(1, 1, 1, 0.6)
	ghost.visible = false
	var faded := Node2D.new()
	faded.draw.connect(func(): draw_body(faded, Vector2(0, screen.y - position.y), tint))
	ghost.add_child(faded)
	add_child(ghost)
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
		dodge_buffer = 0.0
	elif str(r.get("reason", "")) == "committed" and dodge_buffer <= 0.0:
		dodge_buffer = float(CombatFeel.cfg().get("dodge_buffer_s", 0.2))   # decision 38: it goes when the blow may be cancelled

## A tap of Attack: the soft lock (the nearest foe in the cone round the stick, else the facing).
func attack() -> void:
	if not bound():
		attack_time = 0.25
		return
	aim_attack(last_axis if last_axis.length() > 0.2 else motor.dir, false)

## An attack along `dir` on the plane; `aimed` (a dragged aim) snaps only to a foe within a few degrees. `finisher`
## (decision 35, a long drag): the combo's last step at once.
func aim_attack(dir: Vector2, aimed := true, finisher := false) -> Dictionary:
	# Decision 38: each step lunges toward its aim; out of a dash it is a dash attack (the dash ends in it, a longer
	# lunge). Known before the step starts, as its event is played as it is sent.
	dash_attack = motor.grounded and (motor.dash_t > 0.0 or motor.since_dash <= float(CombatFeel.cfg().get("dash_attack_s", 0.15)))
	var r := Game.submit({"type": "basic_attack", "facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "aimed": aimed, "finisher": finisher})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	if r.get("ok", false) and not r.get("queued", false):
		dash_combo = int(r.get("combo", 0)) if dash_attack else -1
		if dash_attack: motor.dash_t = 0.0
		var lunge := CombatFeel.lunge(str(Game.combat.timeline(actor_id).get("family", "fists")), int(r.get("combo", 0)), dash_attack)
		if lunge > 0.0 and motor.grounded: motor.push(Vector2(r.get("aim", dir)).normalized() * lunge / 0.1, 0.1)
	return r

## A guard parried a blow (Combat's `parried`): the figure turns it aside, the parry's deflection played once.
func parried() -> void:
	var a := TopdownFigure.spec(TopdownFigure.resolve("", _family(), "parry"))
	parry_t = float(a.frames) / float(a.fps)

## The wielded weapon family (fists when unbound).
func _family() -> String:
	return str(StatRules.family(Game.character(actor_id)).get("id", "fists")) if bound() else "fists"

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
		if not forced.is_empty():
			if float(Game.combat.timeline(actor_id).flinch) > 0.0 and knock_t <= 0.0:
				knock_t = float(forced.time)   # decision 38: struck and knocked back, the body hops
				knock_s = knock_t
			motor.push(forced.velocity, float(forced.time))
		if dodge_buffer > 0.0:
			dodge_buffer = maxf(0.0, dodge_buffer - delta)
			if dodge_buffer > 0.0 and CombatFeel.dodge_cancel(Game.combat.timeline(actor_id), c) != "committed": dodge()
		# Gusts and currents (S17) add their push to walking, as on player.gd; a meditating or wounded body is anchored.
		motor.drift = Game.world.hazard_drift(actor_id) if not c.cultivator.meditating and not Game.combat.is_wounded(actor_id) else Vector2.ZERO
	motor.step(delta, move, _jump, _dash)
	_jump = false
	_dash = false
	attack_time = maxf(0.0, attack_time - delta)
	impact_t = maxf(0.0, impact_t - delta)
	knock_t = maxf(0.0, knock_t - delta)
	parry_t = maxf(0.0, parry_t - delta)
	hurt_t += delta
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

## Pick the action and frame from the motor and Combat's timeline, then place the node: x on whole art px, y at the
## sort key, the body drawn back down to its whole-pixel screen row (TopdownWorld keeps every key a multiple of 1/64,
## so the offset is exact). A blow plays its own pose on Combat's clock, its hit frame on the hit; a technique with no
## pose of its own plays the hand-seal cast. Decision 37's drawn moves: a parried blow plays the parry's deflection, the
## flute's held melody loops the flute at the lips, the finisher armed on Attack holds the charge's wind-up.
func sync(delta: float) -> void:
	var m := motor
	var tl: Dictionary = Game.combat.timeline(actor_id) if bound() else {}
	var next := "idle"
	var f := -1    # -1: the action's own clock
	if bound() and Game.combat.is_wounded(actor_id): next = "knockdown"
	elif m.plunging: next = "plunge"
	elif impact_t > 0.0 and m.grounded: next = "plunge_land"
	elif m.sink_t >= 0.0:
		next = "jump"
		f = 3
	elif bound() and Game.combat.is_busy(actor_id):
		next = "strike"
		pose = _strike_pose(tl)
		f = TopdownFigure.strike_frame(pose, float(tl.t), float(tl.duration), float(tl.hit_at))
	elif attack_time > 0.0:
		next = "strike"
		pose = "punch_2"
		f = TopdownFigure.strike_frame(pose, 0.25 - attack_time, 0.25, 0.1)
	elif parry_t > 0.0: next = "parry"
	elif bound() and Game.combat.is_playing(actor_id) and m.vel.length() <= 12.0: next = "melody"
	elif bound() and float(tl.get("flinch", 0.0)) > 0.0: next = "hurt"
	elif m.dash_t > 0.0: next = "dodge" if m.dash_dir.dot(m.dir) < -0.3 else "dash"
	elif not m.grounded:
		next = "jump"
		f = 0 if m.vz > 340.0 else (1 if m.vz > 140.0 else (2 if m.vz > -140.0 else 3))
	elif bound() and str(aim.get("move", "")) == "finisher": next = "charge"
	elif not tl.is_empty() and tl.guard: next = "guard"
	elif m.land_t > 0.0:
		next = "jump"
		f = 4
	elif meditating: next = "meditate"
	elif m.vel.length() > 12.0: next = "run" if m.vel.length() > m.walk * 1.15 else "walk"
	if stage_pose != "": next = TopdownFigure.resolve(stage_pose)   # a staged scene's pose (decision 39)
	if next != anim:
		anim = next
		anim_t = 0.0
	anim_t += delta * (clampf(m.vel.length() / m.walk, 0.5, 1.2) if anim == "walk" else 1.0)
	match anim:
		"strike": pass
		# Decision 35: the Plunge drops tucked, then dives (frames 0-1 on its clock); landed, its impact frame holds.
		"plunge":
			pose = "plunge"
			f = mini(TopdownFigure.frame_at(pose, anim_t), TopdownFigure.hit_frame(pose) - 1)
		"plunge_land":
			pose = "plunge"
			f = TopdownFigure.hit_frame(pose)
		"parry", "charge": pose = TopdownFigure.resolve("", _family(), anim)
		# The held melody: the flute at the lips, its note frames looping (combat_feel.json `melody_loop`).
		"melody":
			pose = TopdownFigure.resolve("", _family(), anim)
			var loop := CombatFeel.melody_loop()
			f = int(loop[0]) + int(anim_t * float(TopdownFigure.spec(pose).fps)) % (int(loop[1]) - int(loop[0]) + 1)
		_: pose = anim
	frame = f if f >= 0 else TopdownFigure.frame_at(pose, anim_t)
	# Decision 38: the phase of the blow or cast under way (CombatFeel), and the hop of a knockback, which lifts the drawn
	# body only.
	action_phase = CombatFeel.phase_of(tl, Game.character(actor_id)) if anim == "strike" and bound() else ""
	var hop := 0.0
	if knock_t > 0.0 and knock_s > 0.0:
		hop = roundf(float(CombatFeel.cfg().get("flash", {}).get("player_hop_px", 4)) * sin(PI * (1.0 - knock_t / knock_s)))
	screen = Vector2(roundf(m.pos.x / TopdownRoom.ART), roundf((m.pos.y - m.z) / TopdownRoom.ART) - hop)
	position = Vector2(screen.x, world.room.sort_key(m.pos, m.z))
	var inv: bool = motor.invuln > 0.0 or (bound() and float(Game.combat.timeline(actor_id).dodge_t) > 0.0)
	var hurt := bound() and float(Game.combat.timeline(actor_id).flinch) > 0.0
	tint = Color(1.6, 0.8, 0.8) if hurt else Color.WHITE
	ghost.visible = inv and int(Time.get_ticks_msec() / 25) % 2 == 0
	if ghost.visible: ghost.get_child(0).queue_redraw()
	queue_redraw()

## A blow's or a technique's pose: its own drawn action (a side-view name resolves to one), or the cast for a
## technique that has no pose of its own, each as the wielded family plays it (TopdownFigure.resolve with the family:
## the heavy sabre cuts two-handed, the bell tolls, the brush writes its talisman, the flute plays at the lips, the bow
## draws). A basic step struck in the air, out of a dash or thrown plays that move's pose (the air strike, the dash
## slash or the thrust families' lunge, the fan's throw).
func _strike_pose(tl: Dictionary) -> String:
	var fam := _family()
	if str(tl.technique) != "":
		var t := ContentDB.entry("techniques", str(tl.technique))
		var raw = t.get("action")
		if raw == null or str(raw) in ["", "null", "meditate_burst"]: return TopdownFigure.resolve("cast", fam)
		# Decision 38: a cast whose own action does not suit a fight seen from above (meditation sits facing the camera,
		# a jump leaves the floor) plays its form's top-down pose (combat_feel.json).
		if str(raw) in ["meditate", "jump"]: return TopdownFigure.resolve(CombatFeel.form_pose(t, StatRules.family(Game.character(actor_id))), fam)
		return TopdownFigure.resolve(str(tl.action), fam)
	var move := ""
	if tl.get("air_attack", false): move = "air"
	elif dash_attack and int(tl.get("combo", -1)) == dash_combo: move = "dash"
	elif (tl.get("step", {}) as Dictionary).has("throw"): move = "throw"
	return TopdownFigure.resolve(str(tl.action), str(tl.get("family", fam)), move)

## Draw the current frame with its feet at `feet` on `canvas` (the silhouette overlay draws the same frame).
func draw_body(canvas: CanvasItem, feet: Vector2, tint := Color.WHITE) -> void:
	figure.draw(canvas, feet, pose, motor.row, frame, tint)

func _draw() -> void:
	# Decision 38: the first frames of a blow turn the body white (every layer at once), then the flinch's red tint.
	material = TopdownFx.white_material() if hurt_t < float(CombatFeel.cfg().get("flash", {}).get("white_s", 0.05)) else null
	if not ghost.visible: draw_body(self, Vector2(0, screen.y - position.y), tint)
