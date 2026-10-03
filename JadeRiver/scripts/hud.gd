class_name Hud
extends Control
## S24 · The play screen. Every element stays hidden until the unlock service
## reveals it. Controls send intents (or ask the shell to open a page); nothing
## here changes game state. P5a: laid out to the approved mockups 01 (a fight) and 02 (at rest), at 1280 × 720
## (docs/ui_style_guide.md §9), and mirrored for the left-handed option.
##
## The right thumb holds two rings round the 132 px attack button. Ring 1 (R 132): jump, the four techniques of the
## page, dodge. Ring 2 (R 214): the fan, which holds the system toggles (Cultivate, Presence, Sphere, Sense, Pet;
## roadmap decision 20) and opens and closes with a tap, and beside it what the moment needs: a toggle that is on,
## pinned while the fan is closed, and in a fight the healing slot, the Draught and the treasures, then the context or
## the post chip and the weapon swap. An empty slot is not drawn (review G3). With no foe near the healing slot and the
## treasures rest, and the fan opens again if the player left it open; a foe near folds the fan. The lower middle stays
## clear for the fight (CLEAR_ZONE, checked by the hud_suite).
##
## Decision 42 (the prototype APK's feedback): the Attack button and the technique buttons stay out at rest as in a
## fight (they no longer fold into beads), and whatever the world offers in reach (talk, gather, open, enter) has its
## own button on ring 2, never the Attack button's face. The techniques are the Techniques tree's node pictures
## (TechniquePicture: the character large in the art's pose in its element's ink on a starry ground, at a button's size
## its upper body, in a jade frame), round TILE px buttons in the thumb's arc (decision 43); Jump is 64 px. A
## companion's chip shows the top-down figure's head for a top-down character (HudPanels._draw_face).
##
## The QI bar exists only once the character has a QI pool (Bone Forging 1, with the first technique: decision 45): a
## Mortal has no Qi, so no QI bar is drawn.
##
## Audit 45, S6 (docs/architecture/hud.md): this file keeps the HUD's state, its frame (_process and _draw, which call
## the parts in order), its input (_input, with the keys) and the facade; the work is done by its parts in scripts/hud/,
## one for each section (HudPart says how a part works):
##   - HudLayout: where every control stands and which show, ring 2, the hit circles, the points badges, rest and fight;
##   - HudInput: the touches, the aiming gestures, the pet wheel and the holds;
##   - HudActions: what a control asks of the game (the context, a harvest, a place's pose, the quick slots...);
##   - HudNotices: the game's events as log lines, toasts and captions (rows of data/cues.json, and code for the rest);
##   - HudTours: the tutorial coach's anchors;
##   - HudControls, HudPanels, HudMinimap, HudTopStack: the drawing, in that order of the screen's parts;
##   - HudSideView: the side view's own answers (decision 41's frozen fallback), each called from one branch marked
##     "side view", so retiring the side view deletes the file and those branches.

var frame_style: StyleBox
var player: Node2D
var world: Node2D
var skill_page := 0
var scroll_progress := 1.0
var scroll_direction := -1
var touches: Dictionary = {}
var joystick_id := -999
var joystick_origin := Vector2.ZERO
var joystick_pos := Vector2.ZERO
var mouse_down := false
var left_handed := false
# The right-hand cluster (mockups 01 and 02): angles in degrees on screen (0 to the right, 90 down) round the attack
# button, mirrored when left-handed.
const RING1_R := 132.0
const RING2_R := 214.0
const FAN_R := 150.0          # the open fan's toggles round the fan button
const PAPER_R := 190.0        # the paper fan behind them
const JUMP_DEG := 150.0
## Decision 43: the techniques are round buttons TILE px across (from decision 42's 56 px squares) in the thumb's arc
## round Attack, 28-30° apart and a little further out than ring 1 (SKILL_R) so the bigger circles keep a few pixels
## clear of each other, of Jump and of ring 2; the last comes in to stand clear under the context's label.
const SKILL_DEG := [184.0, 212.0, 240.0, 270.0]
const SKILL_R := [146.0, 146.0, 144.0, 128.0]
const DODGE_DEG := 300.0
const FAN_DEG := 160.0
## Decision 42: Jump drawn at r 32 (64 px, from 52), the context's own button at r CTX_R. Decision 43: a technique a round
## button TILE px across (x1.21 of the old square), its picture PICTURE px across inside the ring (the card's miniature,
## TechniquePicture.draw_round), the ready flash READY_S long.
const JUMP_R := 32.0
const TILE := 68.0
## Test hook: rules_tests holds the round buttons' pictures to it.
const PICTURE := 58
const READY_S := 0.35
const CTX_R := 30.0
## Ring 2 beside the fan. A pinned toggle, the quick slots, the first treasure, the context and the swap have their
## own places; the rest take the next free one.
## Decision 45: the fourth place at 244° (from 248°), so a circle there keeps clear of the context's label ("Talk · Lu",
## CTX_LABEL_W under the 270° button) as well as of the 240° technique.
const RING2_DEG := [178.0, 204.0, 226.0, 244.0, 270.0, 292.0]
## Keep Post (at rest only) takes the first treasure's place (in a fight only); the context holds 270° at rest too.
## Decision 45: three quick slots ("quick:0" the healing slot where mockup 01 has it, then 226° and 244°, an arc over
## the techniques under the thumb); a quick slot drawn first keeps its home and a treasure takes the next free place.
const RING2_HOME := {"pin": 178.0, "quick:0": 204.0, "quick:1": 226.0, "quick:2": 244.0, "treasure:0": 226.0, "post": 226.0,
	"context": 270.0, "swap": 292.0}
## Decision 45: more than ring 2's six places hold (three quick slots, the Draught, two treasures, a pin, the context and
## the swap late in the game) go on an outer row R3 round Attack, clear of ring 2, the screen's edge, the purse and the
## clear zone; every place of both rows stays at least 62 px from every other.
const RING3_R := 276.0
const RING3_DEG := [216.0, 233.0, 250.0, 267.0]
## Decision 45: the quick slots' indexes (InventoryState.quick); their roles are "quick:0" to "quick:2", and a tour's
## anchor "quick" is all of them that show (tour_rect).
const QUICK_SLOTS := [0, 1, 2]
## The fan's toggles in their order round it when open: only the revealed ones, packed from the first place.
const FAN_DEG_OPEN := [180.0, 202.0, 224.0, 246.0, 268.0]
const FAN_TOGGLES := ["cultivate", "presence", "sphere", "sense", "pet"]
const FAN_ROLE := {"cultivate": "meditate", "presence": "presence", "sphere": "sphere", "sense": "sense", "pet": "pet"}
const FIGHT_HOLD_S := 2.0     # the fight state holds this long after the last foe leaves, so the ring does not flicker
## The lower middle the mockups keep open for the fight: the player and the party stand here at the common camera
## positions (the player at x 640 give or take the camera's look-ahead, the feet at y 470 with the camera free and
## down to about 640 with it at its lowest). No HUD control or panel is drawn in it (the hud_suite checks).
const CLEAR_ZONE := Rect2(380, 324, 520, 332)
## The top centre's stack (the room's name, an event, a fortune card, the toasts) starts under the party chips, or
## under the boss bar in a boss fight, and stops above the clear zone.
const TOP_STACK := 96.0
const TOP_STACK_BOSS := 184.0
## The log sits above the joystick's half, newest at the foot, and keeps left of the clear zone (mockup 01).
const LOG_FOOT := 451.0
const LOG_W := 356.0
## The party chips' face crop: this far above the feet on the idle frame, this big.
const FACE_AT := Vector2(2, -80)
const FACE_BOX := 30.0
## Decision 42: a top-down companion's face, its figure at x2 and its face's middle this far under the top of its bare
## body's idle frame (the head's crown).
const FACE_TOP_K := 2
const FACE_TOP_HEAD := 10.0
## Points to spend: one row a point system the player spends by hand. The HUD reads its count from its authority
## ([authority, getter], given the character), shows the badge `points_<id>` (tools/icons, its own colour, shape and
## symbol) at the top right of the player panel while the unlock is open and the count is above 0, and a tap asks the
## shell for its page and tab. Its log line on appearing is `hud.points_<id>`.
const POINT_SYSTEMS := [
	{"id": "meridian", "unlock": "foundation", "count": ["progression", "meridian_points_free"], "page": "cultivation", "tab": "foundation"},
	{"id": "realisation", "unlock": "technique_slots_2", "count": ["progression", "realisations_free"], "page": "techniques", "tab": ""},
	{"id": "bench", "unlock": "apprentice_bench", "count": ["posts", "bench_points_free"], "page": "posts", "tab": "bench"},
	{"id": "post_art", "unlock": "post_arts", "count": ["posts", "art_points_free"], "page": "works", "tab": "arts"},
]
const POINTS_PITCH := 48.0    # the badges' row, leftward from the panel's top right corner, a 48 px target each
const POINTS_POP_S := 0.3     # a badge appears with a small pop (none with Reduce motion)
var attack_center := Vector2(1165, 605)
var jump_center := Vector2(1051, 671)
var guard_center := Vector2(1231, 491)     # dodge on a tap, guard on a hold (ring 1 at 300°)
var slots := [Vector2(1019, 595), Vector2(1041, 528), Vector2(1093, 480), Vector2(1165, 477)]
var fan_center := Vector2(964, 678)
var page_center := Vector2(1240, 672)      # the technique page tab, "1/2"
# The fan's toggles where they stand while it is open (set with the fan each frame; the pet wheel opens round Pet).
## Test hook: rules_tests taps the presence toggle here.
var presence_center := Vector2(825, 622)
var pet_center := Vector2(959, 528)
var context_center := Vector2(1165, 391)   # the context's own button on ring 2 (at rest too, decision 42)
var auto_center := Vector2(1232, 292)    # S49: the auto-hunt toggle, under the icon row (only where allowed)
var tracker_paths: Array = []            # S49: [{rect, target}] the tracker's auto-path buttons this frame
var tracker_rect := Rect2()              # the tracker's plate as last drawn (a tap on it opens Quests)
var minimap_rect := Rect2(1032, 16, 232, 140)
var icon_row := [["menu", Vector2(1064, 188)], ["bag", Vector2(1120, 188)], ["map", Vector2(1176, 188)], ["mail", Vector2(1232, 188)]]   # pitch 56 (P4 §2.1)
# Rest and fight (P5a): the fan folds in a fight and opens again at rest as the player left it.
var fight := true             # a foe is near (or was, within FIGHT_HOLD_S)
var fight_left := 0.0
var fight_override = null     # tests and previews: true or false stands in for the room
var fan_open := false
var fan_rest_open := true     # the player's choice at rest: open, as mockup 02 draws it, until they close it
var _settled := false
signal open_page(page: String, args: Dictionary)
signal dialogue_requested(convo: Dictionary)
signal fishing_requested(object_id: String)
var log_lines: Array = []          # [{text, t, color}]
var toasts: Array = []             # [{text, t, kind}]
var toasts_fit := 3                # how many toasts the top stack had room for last frame (the rest wait)
var objective_seen: Dictionary = {}   # quest -> progress last toasted, while the tracker is still hidden
var banner := {"text": "", "sub": "", "t": 0.0}
var vignette := {"title": "", "text": "", "t": 99.0}   # S49: a fortune encounter's card, read at the top of the screen
# S40 captions: sound-only cues written out when the player turns captions on.
const CAPTIONS := {"boss_phase": "boss_roar", "field_boss_spawned": "distant_roar", "bell_rung": "bell", "mail_received": "letter",
	"qi_backlash": "backlash", "defence_warning": "war_drums", "attack_started": "wind_up", "enemy_aggro": "noticed"}
var caption := {"text": "", "t": 9.0}
var context: Dictionary = {}
var channel := {"object": "", "t": 0.0, "dur": 0.0, "action": ""}
## S45 harvest tap: after the hold, a ring shrinks toward the Attack button; tap it inside the gold band.
var tapping := {"object": "", "t": 0.0, "ring": 1.0, "target": 0.7, "window": 0.12}
var cultivate_hold := 0.0
var cultivate_pressed := false
var guard_hold := 0.0
var guard_pressed := false
# v2 HUD: hold the Pet button for the command wheel (follow, stay, attack, passive, ride, the Pet Bag).
var pet_pressed := false
var pet_hold := 0.0
var pet_wheel := false
var pet_pick := -1
# S47 v1.1 flute: hold Attack past the family's hold time to play the melody; release to stop.
var attack_pressed := false
var attack_hold := 0.0
const PET_WHEEL := ["follow", "stay", "attack", "passive", "ride", "bag"]
var pulses: Dictionary = {}        # element -> seconds of reveal pulse
var equip_prompt := EquipPrompt.new()   # a better piece picked up or received, offered at the right for 10 s
var t := 0.0
var _faces: Dictionary = {}        # companion id -> its idle frame's layers (a classic character's); "top|id" -> its TopdownFigure
var _points_seen: Dictionary = {}  # points badge id -> HUD time it appeared (its pop)
var _points_primed := false        # the badges showing when the HUD was bound pop but write no log line
var points_override: Dictionary = {}   # tests and previews: points badge id -> the count to show in place of its getter
var _hollow_last := -1.0
var _hollow_dir := 0.0
## The smallest HUD hit circle's radius (P4, docs/ui_style_guide.md §7): 48 px across, and never less than the drawn
## radius + 4.
const HIT_MIN := 24.0
## The tracker's plate starts this far under the player panel (clear of the status row and the Hollowing meter's
## stops), and stops at the foot, above the log.
const TRACKER_DROP := 52.0
const TRACKER_FOOT := 320.0
## Decision 44: using a place plays its pose first (data/places.json `pose`: open a lid, a letter box or a door; tend a bed
## or a furnace; sit on the mat), for PLACE_POSE_S, then opens its page; a second tap on the context button opens it at
## once. The body keeps the pose while the page it opened is open (seated at the mat through the Cultivation page) and
## rises when it closes (set_blocked). Each pose raises its sound (`place_open`, `place_tend`, `place_sit`).
const PLACE_POSE_S := 0.4
var place_pending: Dictionary = {}   ## {page, args, t}: a page waiting for its place's pose
## The context button's words under it, as wide as the ring leaves them (HudLayout.context_label_rect). Audit 45 S6: 116
## (from 128), so the sixth place of ring 2 (292°, the weapon swap's) keeps clear of the label's end: at 128 its circle
## crossed the label's top corner by 3 px at 1280 × 720. Nothing moves; a label wider than 116 px ends in "…" sooner.
const CTX_LABEL_W := 116.0
## The log's rows at most, and a wrapped row's indent (HudPanels.log_rows).
const LOG_ROWS := 6
const LOG_INDENT := 14.0
## How long a fortune card stays (HudTopStack's vignette), and a toast's second line's row.
const VIGNETTE_S := 9.0
const TOAST_ROW := 22.0
## Pages and dialogue block world input; held controls are released at once.
var blocked := false
## A moment holds world input for a moment (P6, at most 1.5 s); kept apart from `blocked` so a page closing never ends it.
var moment_lock := false
var moments: Node = null   # the MomentView: a press during its lock goes to it (a tap skips a skippable moment)
## A staged scene's cut holds the controls (decision 39): every touch, click and key goes to the SceneDirector (a tap
## moves the talk on, a hold skips to the next hand-off).
var scene_lock := false
var scenes: Node = null
## Decision 43: the tutorial coach (TutorialCoach): while a tour dims the screen it keeps touches from the HUD but for its
## spotlight (and a guide's card buttons).
var coach: Node = null
var _from = null   # the payload of the event being handled (toast, drop_toasts_from)
## Decision 43: the arts seen cooling, and when each was ready again (the HUD's clock), for the ready flash.
var _cooling := {}
var _ready_at := {}
## The purse and the status row under the player panel as last drawn (none when they are not): the world's labels keep
## off them (the prototype's QA saw Artisan Row's way plate under the purse on the Fairground).
var purse_rect := Rect2()
var status_rect := Rect2()
## Decision 43: the places drawn on the minimap this frame ({id, at}), and their states, looked at twice a second.
var minimap_places: Array = []
var _place_states := {}
var _place_look := 0.0
var _place_room := ""
## Worked out once and kept (each its part's): the tours' targets and the points badges once a frame, the node plate's
## chance once a second, the techniques' look once a frame, a grid room's map once a room.
var _tour_targets := FrameMemo.new()
var _badges_memo := FrameMemo.new()
var _badges: Array = []   ## the badges last worked out (obstacle_rects knows the frame's by them)
var _plate_key := ""
var _plate_text := ""
var _look_now := FrameMemo.new(1, false)
var _grid_maps: Dictionary = {}

# ------------------------------------------------------------------ the parts
var layout: HudLayout
var tours: HudTours
var input: HudInput
var actions: HudActions
var notices: HudNotices
var controls: HudControls
var panels: HudPanels
var minimap: HudMinimap
var top_stack: HudTopStack
var side_view: HudSideView   # the side view's own answers (S12 deletes it with the side view)

func _init() -> void:
	layout = HudLayout.new(self)
	tours = HudTours.new(self)
	input = HudInput.new(self)
	actions = HudActions.new(self)
	notices = HudNotices.new(self)
	controls = HudControls.new(self)
	panels = HudPanels.new(self)
	minimap = HudMinimap.new(self)
	top_stack = HudTopStack.new(self)
	side_view = HudSideView.new(self)

func _ready() -> void:
	frame_style = UiKit.style("minor_panel")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if Game and GameEvents:
		GameEvents.event.connect(_on_event)
		left_handed = bool(Game.account.settings.get("left_handed", false))
	layout.place_cluster()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)
	if bound(): WorldLabels.party_fight = false

func bound() -> bool:
	return is_instance_valid(player) and player.actor_id != "" and Game.active() != null

func shown(element: String) -> bool:
	return not bound() or Game.is_revealed("hud:" + element)

func _process(delta: float) -> void:
	t += delta
	actions.tick_place_pose(delta)
	input.advance_scroll(delta)
	notices.age(delta)
	input.tick_holds(delta)
	actions.tick_channel(delta)
	actions.tick_tap(delta)
	input.tick_aims(delta)
	if bound(): equip_prompt.tick(Game.active(), delta)
	if bound() and world: context = world.context
	layout.tick_fight(delta)
	var badges := layout.frame_badges()
	layout.tick_points(badges)
	# G4: the world's names keep clear of the HUD's controls, and the party's HP lines show only in a fight.
	WorldLabels.party_fight = bound() and fight
	if bound() and is_instance_valid(world) and "label_obstacles" in world: world.label_obstacles = layout.obstacle_rects(badges)
	queue_redraw()

func _notification(what):
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		for id in touches:   # a guard held on Attack (decision 35) ends with its touch
			var g = touches[id].get("gesture")
			if g != null and g.guarding and input.aims(): player.release_guard()
		touches.clear()
		joystick_id = -999
		mouse_down = false
		input.attack_up()
		if is_instance_valid(player):
			player.movement = Vector2.ZERO
			player.joystick_engaged = false
			player.reset_sprint()

func set_blocked(value: bool) -> void:
	if value and not blocked: _notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	blocked = value
	# Decision 44: the page a place's pose opened has closed: the body rises (a pose still waiting for its page stays).
	if not value and place_pending.is_empty() and is_instance_valid(player) and player.has_method("end_place_pose"): player.end_place_pose()   # side view: no place poses

func set_moment_lock(value: bool) -> void:
	if value and not moment_lock: _notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	moment_lock = value

## A staged scene's cut takes the controls (held ones let go at once) and gives them back.
func set_scene_lock(value: bool) -> void:
	if value and not scene_lock: _notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	scene_lock = value

func _input(event):
	if blocked or (coach != null and coach.holds(event)): return
	if scene_lock:
		if scenes: scenes.input(event)
		return
	if moment_lock:
		var pressed: bool = (event is InputEventScreenTouch or event is InputEventMouseButton or event is InputEventKey) and event.pressed and not event.is_echo()
		if pressed and moments: moments.press()
		return
	if event is InputEventMouse and event.device == -1: return
	if event is InputEventScreenTouch:
		if event.pressed and not event.canceled: input.press(event.index, event.position)
		else: input.release(event.index)
	elif event is InputEventScreenDrag: input.drag(event.index, event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		mouse_down = event.pressed
		if event.pressed: input.press(-1, event.position)
		else: input.release(-1)
	elif event is InputEventMouseMotion and mouse_down: input.drag(-1, event.position)
	elif event is InputEventKey and not event.echo:
		if not bound():   # the engine tests' bare side-view player (no character)
			if event.pressed:
				match event.physical_keycode:
					KEY_SPACE: player.jump()
					KEY_J: player.attack()
					KEY_M: player.meditate()
					KEY_TAB: input.scroll_skills(-1)
			return
		var kc: int = event.physical_keycode
		if event.pressed:
			match kc:
				KEY_SPACE: player.jump()
				KEY_J, KEY_ENTER: input.primary()
				KEY_F: if layout.context_shown(): actions.use_context()
				KEY_C: if shown("cultivate"): actions.tap_cultivate()
				KEY_K:
					if shown("guard"):
						guard_pressed = true
						guard_hold = 0.0
				KEY_Q: if shown("quick_use"): actions.use_quick()
				KEY_V: if layout.has_draught(): actions.drink_draught()
				KEY_G: if shown("presence"): actions.toggle_presence()
				KEY_H: if shown("sphere"): actions.toggle_sphere()
				KEY_O: if layout.post_chip(): actions.keep_post()
				KEY_R: if shown("weapon_swap"): actions.swap_weapon()
				KEY_Z: if shown("treasure_1"): actions.use_treasure(0)
				KEY_X: if shown("treasure_2"): actions.use_treasure(1)
				KEY_TAB: if shown("menu"): open_page.emit("menu", {})
				KEY_I, KEY_B: if shown("bag"): open_page.emit("inventory", {})
				KEY_M: if shown("map"): open_page.emit("world_map", {})
				KEY_L: if shown("quest_tracker"): open_page.emit("quests", {})
				KEY_E: if shown("pet"): open_page.emit("spirit_animals", {})
				KEY_P: if shown("cultivate"): open_page.emit("cultivation", {})
				KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
					if shown("skills"): player.use_technique(kc - KEY_1)
		else:
			if kc in [KEY_J, KEY_ENTER]: input.attack_up()
			if kc == KEY_K and guard_pressed:
				guard_pressed = false
				if guard_hold <= 0.18: input.dodge()
				Game.submit({"type": "guard_end"})

func add_log(text: String, color = UiKit.PAPER, always := false) -> void:
	log_lines.append({"text": text, "t": 0.0, "color": color, "always": always})
	while log_lines.size() > 5: log_lines.pop_front()

func toast(text: String, kind := "unlock", sub := "") -> void:
	toasts.append({"text": text, "t": 0.0, "kind": kind, "sub": sub, "life": 3.2 if sub == "" else 5.0, "from": _from})
	while toasts.size() > 3: toasts.pop_front()

## P6: a moment that takes an event into itself (a breakthrough's unlock, a tribulation's result) takes back the toast
## the HUD made for it; `_from` is the payload of the event being handled while the toast was made.
func drop_toasts_from(p: Dictionary) -> void:
	toasts = toasts.filter(func(tt): return not is_same(tt.get("from"), p))

func _on_event(name: String, p: Dictionary) -> void:
	_from = p
	notices.handle(name, p)
	_from = null

## A HUD button: the HD kit's hud_ring (tools/ui/build_ui_hd.py: a jade-enamel face with a vertical sheen, a thin gold
## bezel, a gloss arc and, when active, a soft gold halo), the nearest of its sizes scaled to `radius`. `pressed` sinks
## the face while a finger holds the button (and while the fan stands open).
func ring(center: Vector2, radius: float, active := false, opacity := 1.0, gold := false, pressed := false) -> void:
	var size: int = UiKit.HUD_RINGS[0]
	for s in UiKit.HUD_RINGS:
		if absf(float(s) - radius * 2.0) < absf(float(size) - radius * 2.0): size = s
	var tex := UiKit.hd_texture("hud_ring_%d" % size, "active" if active or gold else ("pressed" if pressed else "normal"))
	if tex == null: return
	var half := (size * 0.5 + UiKit.HUD_RING_PAD) * radius * 2.0 / float(size)
	draw_texture_rect(tex, Rect2(center - Vector2(half, half), Vector2(half, half) * 2.0), false, Color(1, 1, 1, opacity))

## A HUD glyph or icon centred on `center`, at a whole-number scale of its art in a `size` box (SpriteCache.draw_icon):
## 32 for a glyph in a button ring (a legacy glyph's 16 art px at 2x, an HD glyph 1:1), 64 in the attack ring,
## 32 for an item in an item ring (its native 32, or a legacy item's 32 art px at 1x), 24 for a status icon.
func glyph(id: String, center: Vector2, size := 32.0, color := Color.WHITE) -> void:
	SpriteCache.draw_icon(self, Rect2(center - Vector2(size, size) * 0.5, Vector2(size, size)), id, color)

func _draw():
	if not is_instance_valid(player): return
	if not bound():   # the engine tests' bare side-view player (no character)
		panels.draw_legacy()
		return
	var c = Game.active()
	tracker_rect = Rect2()
	tracker_paths = []
	panels.draw_player_panel(c)
	panels.draw_points(c)
	panels.draw_party(c)
	if shown("quest_tracker"): panels.draw_tracker(c)
	if shown("minimap") and Game.account.settings.get("minimap", true) and (not is_instance_valid(world) or world.get("hud_minimap") != false): minimap.draw(c)
	panels.draw_icon_row(c)
	controls.draw_auto_hunt(c)
	purse_rect = Rect2()
	if shown("currency") and not panels.boss_arena(): panels.draw_purse()
	controls.draw(c)
	if shown("progress_bar"): panels.draw_progress(c)
	panels.draw_log()
	top_stack.draw_boss()
	top_stack.draw(c)
	equip_prompt.draw(self, Game.account.settings.get("reduce_motion", false))
	controls.draw_pet_wheel(c)
	# The harvest ring (S45) sits over every other control while it runs.
	if tapping.object != "": controls.draw_tap_ring()
	controls.draw_tap_words()
	controls.draw_stick()

# ------------------------------------------------------------------ the facade

# HudLayout (hud/hud_layout.gd)
func _layout() -> void: layout.place_cluster()
func _on(center: Vector2, r: float, deg: float, exact := false) -> Vector2: return layout.on_ring(center, r, deg, exact)
func _tick_fight(delta: float) -> void: layout.tick_fight(delta)
func set_state(in_fight: bool, open := false) -> void: layout.set_state(in_fight, open)
func _slot_filled(slot: int) -> bool: return layout.slot_filled(slot)
func _fan_items() -> Array: return layout.fan_items()
func toggle_on(c, id: String) -> bool: return layout.toggle_on(c, id)
func _ring2(c) -> Array: return layout.ring2(c)
func ring2_places(items: Array, taken: Array = []) -> Array: return layout.ring2_places(items, taken)
func hit_targets(badges = null) -> Array: return layout.hit_targets(badges)
func point_badges(c) -> Array: return layout.point_badges(c)
func _frame_badges() -> Array: return layout.frame_badges()
func _tick_points(badges = null) -> void: layout.tick_points(badges)
func points_pop(id: String) -> float: return layout.points_pop(id)
func obstacle_rects(badges = null) -> Array: return layout.obstacle_rects(badges)
func log_rect() -> Rect2: return layout.log_rect()
func panel_rect(c) -> Rect2: return layout.panel_rect(c)
static func go_hit(drawn: Rect2) -> Rect2: return HudLayout.go_hit(drawn)
func _context_shown() -> bool: return layout.context_shown()
func context_label_rect() -> Rect2: return layout.context_label_rect()

# HudTours (hud/hud_tours.gd)
func tour_targets() -> Array: return tours.tour_targets()
func tour_rect(name: String) -> Rect2: return tours.tour_rect(name)

# HudInput (hud/hud_input.gd)
func scroll_skills(direction: int) -> void: input.scroll_skills(direction)
func advance_scroll(delta: float) -> void: input.advance_scroll(delta)
func role_at(p: Vector2) -> String: return input.role_at(p)
func press(id: int, p: Vector2): input.press(id, p)
func toggle_fan() -> void: input.toggle_fan()
func drag(id: int, p: Vector2): input.drag(id, p)
func release(id: int): input.release(id)
func _tick_aims(delta: float) -> void: input.tick_aims(delta)
func armed(g: AimGesture) -> String: return input.armed(g)
func primary() -> void: input.primary()
func attack_first() -> bool: return input.attack_first()
func attack_gesture() -> AimGesture: return input.attack_gesture()

# HudActions (hud/hud_actions.gd)
func finish_tap(timing: float) -> void: actions.finish_tap(timing)
func open_points(id: String) -> void: actions.open_points(id)
func tap_cultivate() -> void: actions.tap_cultivate()
func keep_post() -> void: actions.keep_post()
func place_pose_of(object_id: String) -> String: return actions.place_pose_of(object_id)
func _tick_place_pose(delta: float) -> void: actions.tick_place_pose(delta)
func open_place_page() -> void: actions.open_place_page()
func use_context() -> void: actions.use_context()
func begin_harvest(object_id: String) -> void: actions.begin_harvest(object_id)
func _after_interact(r: Dictionary, object_id: String) -> void: actions.after_interact(r, object_id)
func swap_weapon() -> void: actions.swap_weapon()
func use_treasure(slot: int) -> void: actions.use_treasure(slot)
func drink_draught() -> void: actions.drink_draught()
func use_quick(slot := 0) -> void: actions.use_quick(slot)
func toggle_sphere() -> void: actions.toggle_sphere()
func toggle_presence() -> void: actions.toggle_presence()

# HudNotices (hud/hud_notices.gd)
func world_news(room := "") -> bool: return notices.world_news(room)
func _caption_worthy(name: String, p: Dictionary) -> bool: return notices.caption_worthy(name, p)
static func spar_line(opponent: String, moment: String) -> String: return HudNotices.spar_line(opponent, moment)

# HudControls (hud/hud_controls.gd)
func skill_position(index: float) -> Vector2: return controls.skill_position(index)
func draw_skill_slot(center: Vector2, slot: int, opacity: float) -> void: controls.draw_skill_slot(center, slot, opacity)
func draw_skill_scroll() -> void: controls.draw_skill_scroll()
func _context_glyph() -> String: return controls.context_glyph()
func attack_glyph(c) -> String: return controls.attack_glyph(c)
func armed_glow() -> float: return controls.armed_glow()

# HudPanels (hud/hud_panels.gd)
func bar(r: Rect2, frac: float, fill: Color, label: String, value_text: String, ahead := 0.0, flash := 0.0) -> void: panels.bar(r, frac, fill, label, value_text, ahead, flash)
func hub_ready(c) -> bool: return panels.hub_ready(c)
static func tracker_objective(words: String, count: String, width: float) -> String: return HudPanels.tracker_objective(words, count, width)
func log_rows(lines: Array) -> Array: return panels.log_rows(lines)

# HudMinimap (hud/hud_minimap.gd)
func place_marks(c, room_id: String, to_map: Callable, top := -INF) -> Array: return minimap.place_marks(c, room_id, to_map, top)
func minimap_place_at(p: Vector2) -> Dictionary: return minimap.place_at(p)
static func minimap_way(from: Vector2, to: Vector2) -> Vector2: return HudMinimap.way_toward(from, to)
static func _edge_point(r: Rect2, center: Vector2, way: Vector2) -> Vector2: return HudMinimap.edge_point(r, center, way)

# HudTopStack (hud/hud_top_stack.gd)
func _band_on_top() -> bool: return top_stack.band_on_top()
static func toast_sub_rows(sub: String) -> Array: return HudTopStack.toast_sub_rows(sub)
func toast_rects(y: float) -> Array: return top_stack.toast_rects(y)
