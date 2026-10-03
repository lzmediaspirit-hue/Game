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
## when no thumb is aiming. The world draws it on the ground. Decision 45: while it is armed for the finisher, the charge
## gathers (`charge_t`, advanced in sync); the moment it is let go the charge held is kept (`charge_let_go`) for the
## finisher the HUD strikes next, in the same frame.
var aim: Dictionary = {}:
	set(v):
		var was := str(aim.get("move", "")) == "finisher"
		var now := str(v.get("move", "")) == "finisher"
		if was and not now:
			charge_let_go = charge_t if v.is_empty() else 0.0
			charge_t = 0.0
		aim = v
var charge_t := 0.0        ## seconds the finisher has been held armed
var charge_let_go := 0.0   ## the charge of the finisher just let go (0 once it is struck or a frame has passed)
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
## Decision 44: the pose a place's use plays (open, tend, sit: data/places.json `pose`), from the HUD before the page it
## opens and held while that page is open; a step or a blow ends it ("" for none).
var place_pose := ""
## Decision 42, animation canceling (CombatFeel.weave): a technique pressed during a basic step, or a basic attack during
## a technique, cuts the blow's recovery once it has landed; pressed early, it waits here (combat_feel.json
## `weave.buffer_s`) and goes at the cut: {kind: "attack" | "technique", dir, aimed, finisher, slot, k, left}.
var weave := {}
var _no_buffer := false
## T1 (docs/architecture/topdown_mechanics.md): this press of Jump already started a glide (a press starts one, as the
## side view's hold does).
var _glide_spent := false
## T1: the body's pose on a climbable face: the reviewed hang pose (AGENTS.md rule 4: no new body movement is drawn for
## it), reaching up the face.
const CLIMB_POSE := "work_hang"
## Decision 43, the chain's flow (CombatFeel.flow): the last step Combat began that the body has turned to and lunged
## for (a tapped step does both as it is sent; a queued one, or a finisher asked for mid-chain, as it begins).
var _step_seen := -1

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
	if bound() and meditating: Game.submit({"type": "stop_meditation", "reason": "jump"})   # decision 42: a jump rises from the seat
	_jump = true

## A tap of Dodge: Combat's dodge (its cooldown, second charge, i-frames), carried by the motor's dash.
func dodge() -> void:
	if not bound():
		_dash = true
		return
	if not motor.can_dash():
		_air_dodge()
		return
	var r := Game.submit({"type": "dodge", "direction": last_axis, "facing": facing, "moves": false})
	if r.get("ok", false):
		motor.dash_cd = 0.0   # Combat keeps the cooldown
		_dash = true
		dodge_buffer = 0.0
		weave = {}   # the dodge goes instead of a press waiting for its cut
	elif str(r.get("reason", "")) == "committed" and dodge_buffer <= 0.0:
		# Decision 38: it goes when the blow may be cancelled; decision 43: held until that point, however heavy the blow
		# (up to `flow.dodge_hold_s`), never dropped before it.
		var tl: Dictionary = Game.combat.timeline(actor_id)
		var until := float(CombatFeel.timeline_phases(tl, Game.character(actor_id)).get("cancel_from", 0.0)) - float(tl.t) + 3.0 / 60.0
		dodge_buffer = clampf(until, float(CombatFeel.cfg().get("dodge_buffer_s", 0.2)), float(CombatFeel.flow().get("dodge_hold_s", 0.6)))

## T1 · a tap of Dodge in the air: Combat's Swallow Dart (it darts along the stick, holding the height; once an
## airtime, on the dodge's cooldown) or its Wind Blink, carried by the motor: Combat's forced motion pushes it and the
## motor holds the height while the dart lasts.
func _air_dodge() -> void:
	if motor.grounded or not motor.climbing.is_empty() or motor.plunging or motor.sink_t >= 0.0: return
	var r := Game.submit({"type": "dodge", "direction": last_axis if last_axis.length() > 0.2 else motor.dir, "facing": facing, "moves": true})
	if r.get("air_dash", false): motor.air_hold(state.dash_hold)
	elif r.get("blink", false): motor.vz = maxf(motor.vz, float(TopdownMotor.conf("traverse.double_jump_impulse", 325.0)) * 0.4)

## T1 · a climbable face in reach (TopdownTraverse.climb_near): {climb, end} or {}.
func climb_near() -> Dictionary:
	var tr := motor.traverse()
	if tr == null or tr.climbs.is_empty() or not motor.grounded or motor.sink_t >= 0.0: return {}
	return tr.climb_near(motor.pos, motor.z)

## T1 · climb on (the context's Climb, or the stick held toward the face): the World authority says whether this one is
## open (a sealed loft, a library floor: its side-view row's `requires`), and a shut one says why over the body.
func climb() -> bool:
	var near := climb_near()
	if near.is_empty() or not bound(): return false
	climb_hold = 0.0
	var cl: Dictionary = near.climb
	var open: Dictionary = Game.world.climbable_open(Game.character(actor_id), _side_climbable(str(cl.id)))
	if not open.get("ok", false):
		climb_hold = -1.0   # said once a hold
		if world.get("effects") != null: world.effects.add("text", world.player_feet() + Vector2(0, -120), {"text": str(open.get("text", "")), "color": UiKit.MIST, "size": 18, "dur": 1.8})
		return false
	var c = Game.character(actor_id)
	motor.climb_speed = float(TopdownMotor.conf("traverse.climb_speed", 80.0)) * (1.0 + clampf(c.stats.value("climb_speed"), 0.0, 0.5))
	if motor.start_climb(cl, str(near.end) == "top"):
		if c.cultivator.meditating: Game.submit({"type": "stop_meditation", "reason": "moved"})
		return true
	return false

## The side view's own row of a climbable (its `requires` and `locked_text`), by its id.
func _side_climbable(id: String) -> Dictionary:
	for cl in ContentDB.room(Game.room_rt.room_id).get("climbables", []):
		if str(cl.get("id", "")) == id: return cl
	return {"id": id}

## A tap of Attack: the soft lock (the nearest foe in the cone round the stick, else the facing).
func attack() -> void:
	if not bound():
		attack_time = 0.25
		return
	aim_attack(last_axis if last_axis.length() > 0.2 else motor.dir, false)

## An attack along `dir` on the plane; `aimed` (a dragged aim) snaps only to a foe within a few degrees. `finisher`
## (decision 35, a long drag): the combo's last step at once.
func aim_attack(dir: Vector2, aimed := true, finisher := false, charge_s := 0.0) -> Dictionary:
	# Decision 43: a tap made while a technique waits in the buffer goes after it (the presses in their order).
	if not _no_buffer and str(weave.get("kind", "")) == "technique" and not finisher:
		_buffer({"kind": "attack", "dir": dir, "aimed": aimed, "finisher": false})
		return {"ok": false, "reason": "busy", "buffered": true}
	# Decision 38: each step lunges toward its aim; out of a dash it is a dash attack (the dash ends in it, a longer
	# lunge). Known before the step starts, as its event is played as it is sent.
	dash_attack = motor.grounded and (motor.dash_t > 0.0 or motor.since_dash <= float(CombatFeel.cfg().get("dash_attack_s", 0.15)))
	var r := Game.submit({"type": "basic_attack", "facing": 1 if dir.x >= 0.0 else -1, "aim": dir, "aimed": aimed, "finisher": finisher, "charge_s": charge_s})
	if not r.get("ok", false) and str(r.get("reason", "")) == "busy": _buffer({"kind": "attack", "dir": dir, "aimed": aimed, "finisher": finisher, "charge_s": charge_s})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	if r.get("ok", false) and not r.get("queued", false):
		dash_combo = int(r.get("combo", 0)) if dash_attack else -1
		if dash_attack: motor.dash_t = 0.0
		_step_seen = int(Game.combat.timeline(actor_id).get("starts", 0))
		_lunge(Vector2(r.get("aim", dir)), int(r.get("combo", 0)), r.get("at"))
	return r

## Decision 43: a step lunges toward the foe its aim picked (CombatFeel.pull: to half the weapon's reach from it, a
## little further than the step's own lunge at most, never into it), else its own lunge along the aim (decision 38).
func _lunge(aim: Vector2, combo: int, at) -> void:
	if not motor.grounded or aim.length() < 0.01: return
	var fam := str(Game.combat.timeline(actor_id).get("family", "fists"))
	var own := CombatFeel.lunge(fam, combo, dash_attack and combo == dash_combo)
	if own <= 0.0: return   # the families that strike from where they stand (the bow, the flute, the bell)
	var reach := float(ContentDB.entry("weapon_families", fam).get("reach", 46))
	var length := CombatFeel.pull(own, reach, motor.pos.distance_to(at) if at is Vector2 else -1.0)
	var secs := float(CombatFeel.flow().get("pull", {}).get("time_s", 0.1))
	if length > 0.0: motor.push(aim.normalized() * length / secs, secs)

## Decision 43: a step Combat began on its own (a queued step, aimed again as it began; a finisher asked for mid-chain)
## turns the body to its aim and lunges as a tapped step does, once, the frame it begins.
func _follow_steps() -> void:
	var tl: Dictionary = Game.combat.timeline(actor_id)
	var n := int(tl.get("starts", 0))
	if n == _step_seen: return
	_step_seen = n
	if str(tl.get("action", "")) == "" or str(tl.get("technique", "")) != "": return
	var aim: Vector2 = tl.get("aim", motor.dir)
	motor.face(aim)
	dash_combo = -1
	_lunge(aim, int(tl.get("combo", 0)), tl.get("target_at"))

## A guard parried a blow (Combat's `parried`): the figure turns it aside, the parry's deflection played once.
func parried() -> void:
	var a := TopdownFigure.spec(TopdownFigure.resolve("", _family(), "parry"))
	parry_t = float(a.frames) / float(a.fps)

## The wielded weapon family (fists when unbound).
func _family() -> String:
	return str(StatRules.family(Game.character(actor_id)).get("id", "fists")) if bound() else "fists"

## Decision 35, a long drag on Attack: the combo's finisher step at once along the drag (snapping as an aim does).
## Decision 45: the charged attack, as strong as the charge held past the finisher's line (`charge_s`, else the charge
## just let go).
func finisher(dir: Vector2, charge_s := -1.0) -> Dictionary:
	var held := charge_let_go if charge_s < 0.0 else charge_s
	charge_let_go = 0.0
	return aim_attack(dir, true, true, held)

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
		_no_buffer = true   # a held guard does not wait to enter its stance later
		var entered: bool = s >= 0 and use_technique(s).get("ok", false)
		_no_buffer = false
		if entered: return "stance"
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
	if not r.get("ok", false) and str(r.get("reason", "")) == "busy": _buffer({"kind": "technique", "slot": slot, "dir": dir, "k": k, "aimed": aimed})
	if r.get("ok", false) and r.has("aim"): motor.face(r.aim)
	return r

## Decision 42: a press the hands are too busy for waits for the cut of the blow under way (CombatFeel.weave), unless
## it is the buffered press going now. A newer technique takes the place of an older press; decision 43: Attack taps
## made while a press waits are kept behind it (`more`, up to `flow.more_taps`), each the chain's next step after it.
func _buffer(press: Dictionary) -> void:
	if _no_buffer: return
	var secs := float(CombatFeel.weave_cfg().get("buffer_s", 0.4))
	if not weave.is_empty() and str(press.kind) == "attack" and not bool(press.get("finisher", false)):
		weave.more = mini(int(weave.get("more", 0)) + 1, int(CombatFeel.flow().get("more_taps", 2)))
		weave.left = maxf(float(weave.left), secs)
		return
	press.left = secs
	weave = press

## The buffered press goes the moment the blow under way may be cut (or has ended); else it runs out, but not while a
## step queued ahead of it has still to play (decision 43: the presses in their order). The taps kept behind it follow.
func _tick_weave(delta: float) -> void:
	if weave.is_empty(): return
	var kind := "technique" if str(weave.kind) == "technique" else "basic"
	var tl: Dictionary = Game.combat.timeline(actor_id)
	if not CombatFeel.weave(tl, kind, Game.character(actor_id)) in ["cancel", "free"]:
		if not CombatFeel.waits_ahead(tl): weave.left = float(weave.left) - delta
		if float(weave.left) <= 0.0: weave = {}
		return
	var b := weave
	weave = {}
	_no_buffer = true
	if kind == "technique": aim_technique(int(b.slot), b.dir, float(b.k), bool(b.aimed))
	else: aim_attack(b.dir, bool(b.aimed), bool(b.finisher), float(b.get("charge_s", 0.0)))
	_no_buffer = false
	for i in int(b.get("more", 0)): attack()

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

## Decision 44: play a place's pose (the HUD's `_play_place_pose`), from its first frame.
func play_place_pose(p: String) -> void:
	place_pose = TopdownFigure.resolve(p)
	anim = ""

func end_place_pose() -> void:
	place_pose = ""
func reset_sprint() -> void: pass

## The stick, or WASD / arrows on a keyboard: pushed, the body sprints (decision 42); Alt walks slowly, as a light touch
## of the stick does (the motor's tiptoe band).
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
		# Decision 42: moving rises from meditation at once, as the side view's stick does (unless the Agility gate lets
		# the body cultivate on the move); the figure walks, never sits sliding.
		if move.length() > 0.05 and c.cultivator.meditating and not StatRules.gate_flag(c, "move_keeps_cultivate"):
			Game.submit({"type": "stop_meditation", "reason": "moved"})
		if Game.combat.is_wounded(actor_id) or c.pools.blocked("move"): move = Vector2.ZERO
		if c.pools.has_status("confusion"): move = -move
		_follow_steps()
		var tl: Dictionary = Game.combat.timeline(actor_id)
		# Decision 43: the stick pushed past its tiptoe band cuts a blow's recovery at its cancel point when no press waits
		# on it (CombatAuthority.move_cancel), so a sprint leaves a chain as cleanly as a dodge.
		if move.length() > motor.tiptoe_axis and Game.combat.is_busy(actor_id) and weave.is_empty() and dodge_buffer <= 0.0 \
				and CombatFeel.phase_of(tl, c) == "recovery" and CombatFeel.dodge_cancel(tl, c) == "cancel":
			Game.submit({"type": "move_cancel"})
		motor.speed_k = Game.combat.move_factor(actor_id) if not Game.combat.is_wounded(actor_id) else 0.0
		# Decision 43: the feet are planted through a blow's anticipation and active frames on the ground (its lunge
		# carries it; the recovery keeps the attack's walk).
		if motor.grounded and CombatFeel.phase_of(tl, c) in ["anticipation", "active"]: motor.speed_k *= float(CombatFeel.flow().get("plant", 0.0))
		motor.lock_face = Game.combat.is_busy(actor_id)
		motor.water_walk = Game.combat.knows_art(c, "water_skimming")
		# T1: the movement arts this character knows reach the motor, as the side view's _sync_arts reaches its solver.
		motor.double_jump = Game.combat.knows_art(c, "double_jump")
		motor.wall_step = Game.combat.knows_art(c, "wall_step")
		_hold_jump(c)
		_climb_hold(c, move, delta)
		var forced: Dictionary = Game.combat.forced_motion(actor_id)
		# T1: a blow knocks the body off a climbable face (the side view's knock_off_climb).
		if not motor.climbing.is_empty() and (float(Game.combat.timeline(actor_id).flinch) > 0.0 or Game.combat.is_wounded(actor_id)): motor.release_climb(false)
		if not forced.is_empty():
			if float(Game.combat.timeline(actor_id).flinch) > 0.0 and knock_t <= 0.0:
				knock_t = float(forced.time)   # decision 38: struck and knocked back, the body hops
				knock_s = knock_t
			motor.push(forced.velocity, float(forced.time))
		if dodge_buffer > 0.0:
			dodge_buffer = maxf(0.0, dodge_buffer - delta)
			if dodge_buffer > 0.0 and CombatFeel.dodge_cancel(Game.combat.timeline(actor_id), c) != "committed": dodge()
		_tick_weave(delta)
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
	if bound(): _announce(events)
	if bound(): Game.combat.face_on_plane(actor_id, motor.dir)
	return events

## T1 · Jump held in the air as the body comes down: Combat's Falling Leaf Glide (its QI, its art_used), once a press,
## as the side view's hold glides; let go, landed, or on a face, it ends. The motor glides while Combat's body does.
func _hold_jump(c) -> void:
	var held := jump_held or Input.is_physical_key_pressed(KEY_SPACE)
	if not held: _glide_spent = false
	var air := not motor.grounded and motor.climbing.is_empty() and not motor.plunging and motor.sink_t < 0.0
	if state.gliding and (not held or not air): Game.submit({"type": "glide", "on": false})
	elif held and air and motor.vz <= 0.0 and not state.gliding and not _glide_spent and Game.combat.knows_art(c, "glide"):
		_glide_spent = true
		state.surface = null
		Game.submit({"type": "glide", "on": true})
	motor.gliding = state.gliding

## T1 · the stick held toward a climbable face (into it at its foot, over the edge at its top) for the side view's hold
## climbs on.
func _climb_hold(c, move: Vector2, delta: float) -> void:
	if not motor.climbing.is_empty() or Game.combat.is_busy(actor_id) or c.pools.blocked("move"):
		climb_hold = 0.0
		return
	var near := climb_near()
	var toward := false
	if not near.is_empty() and move.length() > 0.7:
		var d: Vector2 = near.climb.dir if str(near.end) == "foot" else -(near.climb.dir as Vector2)
		toward = move.normalized().dot(d) > 0.8
	if not toward:
		climb_hold = 0.0
		return
	if climb_hold < 0.0: return   # a shut one said why: once a hold
	climb_hold += delta
	# Over the top's edge it climbs down at once (a moment's hold would walk the body off the edge); into the face at the
	# foot it waits the side view's hold, so a push against a wall is not a climb.
	if str(near.end) == "top" or climb_hold >= float(TopdownMotor.conf("traverse.climb_hold_s", 0.3)): climb()

## T1 · what the motor did that the side view's movement authority announces (LocalAuthority.announce: art_used for the
## arts the quests and lessons count, mover_boarded, the climb's start and end, a wall kick), on the body's state.
func _announce(events: Array) -> void:
	for e in events:
		match str(e.type):
			"boarded": state.events.append({"name": "mover_boarded", "mover": str(e.raft)})
			"double_jumped": state.events.append({"name": "art_used", "art": "double_jump"})
			"wall_kicked":
				state.events.append({"name": "wall_kicked", "side": int(signf((e.side as Vector2).x + (e.side as Vector2).y)), "kicks": int(e.kicks)})
				state.events.append({"name": "art_used", "art": "wall_step"})
			"skimmed": state.events.append({"name": "art_used", "art": "water_skimming"})
			"bounced": state.events.append({"name": "art_used", "art": "bounce"})
			"climb_started": state.events.append({"name": "climb_started", "climbable": str(e.climbable)})
			"climb_finished": state.events.append({"name": "climb_finished", "climbable": str(e.climbable), "end": str(e.end)})
	if not state.events.is_empty(): LocalAuthority.announce(state, actor_id)

## The authorities' view of the body: where it is, how high, and whether it stands on the grid.
func _mirror() -> void:
	state.plane = motor.pos
	state.altitude = motor.z
	state.velocity = motor.vel
	state.surface = ground if motor.grounded and motor.sink_t < 0.0 else null
	state.zone_id = world.room.id
	# T1: on a climbable face (Combat refuses blows and arts there), and a dart's once an airtime ends with the airtime.
	state.climbing = {"id": str(motor.climbing.id), "kind": str(motor.climbing.kind)} if not motor.climbing.is_empty() else {}
	if motor.grounded: state.air_dash_used = false

## Pick the action and frame from the motor and Combat's timeline, then place the node: x on whole art px, y at the
## sort key, the body drawn back down to its whole-pixel screen row (TopdownWorld keeps every key a multiple of 1/64,
## so the offset is exact). A blow plays its own pose on Combat's clock, its hit frame on the hit; a technique with no
## pose of its own plays the hand-seal cast. Decision 37's drawn moves: a parried blow plays the parry's deflection, the
## flute's held melody loops the flute at the lips, the finisher armed on Attack holds the charge's wind-up.
func sync(delta: float) -> void:
	var m := motor
	# Decision 45: the finisher armed on Attack charges; a charge let go and not struck this frame is dropped.
	charge_let_go = 0.0
	if str(aim.get("move", "")) == "finisher": charge_t += delta
	if bound(): _follow_steps()   # decision 43: a step Combat began this frame is drawn turned to its aim from its first frame
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
	elif not m.climbing.is_empty(): next = "climb"   # T1: on a climbable face, reaching up it (the reviewed hang pose)
	elif not m.grounded:
		next = "jump"
		f = 0 if m.vz > 340.0 else (1 if m.vz > 140.0 else (2 if m.vz > -140.0 else 3))
	elif bound() and str(aim.get("move", "")) == "finisher": next = "charge"
	elif not tl.is_empty() and tl.guard: next = "guard"
	elif m.land_t > 0.0:
		next = "jump"
		f = 4
	# Decision 42: the stick past its tiptoe band sprints (the run the sheets draw), a light touch walks; a body on the
	# move never sits in meditation's pose (moving ends the meditation, physics_step).
	elif m.vel.length() > 12.0: next = "run" if m.running else "walk"
	elif meditating: next = "meditate"
	# Decision 44: a place's pose while the body is at rest (seated at the mat even as it meditates); anything else, a
	# step or a blow, ends it.
	if place_pose != "":
		if next in ["idle", "meditate"]: next = place_pose
		else: place_pose = ""
	if stage_pose != "": next = TopdownFigure.resolve(stage_pose)   # a staged scene's pose (decision 39)
	if next != anim:
		anim = next
		anim_t = 0.0
	# The feet keep to the ground: the walk's cycle at the walk's pace, the run's at the sprint's.
	var pace := 1.0
	if anim == "walk": pace = clampf(m.vel.length() / m.walk, 0.5, 1.2)
	elif anim == "run": pace = clampf(m.vel.length() / m.sprint, 0.5, 1.2)
	anim_t += delta * pace
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
		# T1: a climb plays the hang pose (its every layer and facing reviewed, the weapon stowed) facing the face: its
		# reaching frames hand over hand while the stick moves the body along the face, one reach held while it rests.
		"climb":
			pose = CLIMB_POSE
			f = (1 + int(anim_t * float(TopdownFigure.spec(pose).fps)) % 4) if m.climb_moving else 2
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
	# A cut holds the body's clocks still (Game.paused): no flinch's red or dodge's blink is held through it (decision 45).
	var inv: bool = not Game.paused and (motor.invuln > 0.0 or (bound() and float(Game.combat.timeline(actor_id).dodge_t) > 0.0))
	var hurt := bound() and float(Game.combat.timeline(actor_id).flinch) > 0.0 and not Game.paused
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
	# A cut holds the simulation (and this body's clock) still: no blow's white is held through it either.
	material = TopdownFx.white_material() if hurt_t < float(CombatFeel.cfg().get("flash", {}).get("white_s", 0.05)) and not Game.paused else null
	if not ghost.visible: draw_body(self, Vector2(0, screen.y - position.y), tint)
