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
## companion's chip shows the top-down figure's head for a top-down character (_draw_face).
##
## The QI bar exists only once the character has a QI pool (Bone Forging 1, with the first technique: decision 45): a
## Mortal has no Qi, so no QI bar is drawn.

const MenuPage = preload("res://scripts/ui/pages/menu_page.gd")

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
var meditate_center := Vector2(814, 678)
var presence_center := Vector2(825, 622)
var sphere_center := Vector2(856, 574)
var sense_center := Vector2(903, 541)
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

signal page_changed(page: int)
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

func _ready() -> void:
	frame_style = UiKit.style("minor_panel")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	if Game and GameEvents:
		GameEvents.event.connect(_on_event)
		left_handed = bool(Game.account.settings.get("left_handed", false))
	_layout()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)
	if bound(): WorldLabels.party_fight = false

## Every fixed place of the right-hand cluster from its ring and angle (mockups 01 and 02), mirrored when left-handed.
func _layout() -> void:
	attack_center = _mirror_x(Vector2(1165, 605))
	jump_center = _on(attack_center, RING1_R, JUMP_DEG)
	guard_center = _on(attack_center, RING1_R, DODGE_DEG)
	slots = range(SKILL_DEG.size()).map(func(i): return _on(attack_center, float(SKILL_R[i]), float(SKILL_DEG[i])))
	fan_center = _on(attack_center, RING2_R, FAN_DEG)
	page_center = _mirror_x(Vector2(1240, 672))

func _mirror_x(p: Vector2) -> Vector2:
	return Vector2(1280.0 - p.x, p.y) if left_handed else p

## The point `r` from `center` at `deg` (screen degrees, mirrored when left-handed), on whole pixels unless `exact`.
func _on(center: Vector2, r: float, deg: float, exact := false) -> Vector2:
	var v := Vector2.from_angle(deg_to_rad(deg)) * r
	if left_handed: v.x = -v.x
	return center + v if exact else (center + v).round()

func bound() -> bool:
	return is_instance_valid(player) and player.actor_id != "" and Game.active() != null

func shown(element: String) -> bool:
	return not bound() or Game.is_revealed("hud:" + element)

func scroll_skills(direction: int) -> void:
	if scroll_progress < 1.0: return
	if bound() and not Unlocks.is_unlocked(Game.active_id, "technique_page_2"): return
	scroll_direction = direction
	scroll_progress = 0.0
	skill_page = (skill_page + 1) % 2
	page_changed.emit(skill_page)
	if bound(): Game.active().skill_page = skill_page

func advance_scroll(delta: float) -> void:
	scroll_progress = minf(1.0, scroll_progress + delta / 0.36)

func _process(delta: float) -> void:
	t += delta
	_tick_place_pose(delta)
	advance_scroll(delta)
	for l in log_lines: l.t += delta
	log_lines = log_lines.filter(func(l): return l.t < 6.0)
	# While a moment holds the screen (P6) the toasts wait under it, so the two never cover each other; a toast the top
	# stack had no room for waits for the one above it to go.
	if not _moment_on_screen():
		var n := toasts.size() if not is_visible_in_tree() else maxi(1, toasts_fit)
		for i in mini(n, toasts.size()): toasts[i].t += delta
		toasts = toasts.filter(func(tt): return tt.t < float(tt.get("life", 3.2)))
	if not _band_on_top(): banner.t += delta   # the room's name keeps its time for after a band over it
	vignette.t = float(vignette.t) + delta
	caption.t = float(caption.t) + delta
	for k in pulses.keys():
		pulses[k] -= delta
		if pulses[k] <= 0: pulses.erase(k)
	if cultivate_pressed:
		cultivate_hold += delta
		if cultivate_hold >= float(ContentDB.curve("meditation.hold_page_s", 0.6)) if Game else 0.6:
			cultivate_pressed = false
			cultivate_hold = -99.0
			open_page.emit("cultivation", {})
	if pet_pressed and not pet_wheel:
		pet_hold += delta
		if pet_hold >= 0.45:
			pet_wheel = true
			pet_pick = -1
	if guard_pressed:
		guard_hold += delta
		if guard_hold > 0.18 and bound() and not player.state.flying and not Game.combat.timeline(Game.active_id).guard:
			Game.submit({"type": "guard_start"})
	if attack_pressed:
		attack_hold += delta
		_try_melody()
	_tick_channel(delta)
	_tick_tap(delta)
	_tick_aims(delta)
	if bound(): equip_prompt.tick(Game.active(), delta)
	if bound() and world: context = world.context
	_tick_fight(delta)
	var badges := _frame_badges()
	_tick_points(badges)
	# G4: the world's names keep clear of the HUD's controls, and the party's HP lines show only in a fight.
	WorldLabels.party_fight = bound() and fight
	if bound() and is_instance_valid(world) and "label_obstacles" in world: world.label_obstacles = obstacle_rects(badges)
	queue_redraw()

## Rest and fight (P5a): a foe near folds the fan and brings out the healing slot and the treasures; with none near
## for FIGHT_HOLD_S the fan opens again if the player left it open. The techniques and Attack stay out either way
## (decision 42).
func _tick_fight(delta: float) -> void:
	var near := _fight_now()
	fight_left = FIGHT_HOLD_S if near else maxf(0.0, fight_left - delta)
	var now := near or fight_left > 0.0
	if not _settled:
		_settled = true
		fight = now
		fan_open = fan_rest_open and not now
	elif now != fight:
		fight = now
		fan_open = false if fight else fan_rest_open

func _fight_now() -> bool:
	if fight_override != null: return bool(fight_override)
	if not bound(): return true
	return WorldLabels.fight_near(Game.active(), player.plane) or _enemy_close() or _foe_engaged()

## Tests and previews: hold the HUD at rest or in a fight, the fan open or closed.
func set_state(in_fight: bool, open := false) -> void:
	fight_override = in_fight
	fight = in_fight
	fight_left = 0.0
	fan_open = open
	_settled = true

func _tick_channel(delta: float) -> void:
	if channel.object == "" or not bound(): return
	if player.last_axis.length() > 0.2:
		channel.object = ""
		player.channel_time = 0.0
		player.channel_action = ""
		return
	channel.t += delta
	player.channel_time = channel.t
	player.channel_action = channel.action
	if channel.t >= channel.dur:
		var obj: String = channel.object
		channel.object = ""
		if channel.action == "gather" and not (channel.get("tap", {}) as Dictionary).is_empty():
			var tp: Dictionary = channel.tap
			tapping = {"object": obj, "t": 0.0, "ring": float(tp.get("ring_s", 1.0)), "target": float(tp.get("target", 0.7)), "window": float(tp.get("window", 0.12))}
			return
		player.channel_time = 0.0
		player.channel_action = ""
		if channel.action in ["gather", "mine"]:
			var r := Game.submit({"type": "complete_node", "object": obj})
			if r.ok: add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(r.item)), int(r.count)], UiKit.BRIGHT_JADE)

func _tick_tap(delta: float) -> void:
	if tapping.object == "" or not bound(): return
	tapping.t += delta
	if tapping.t >= float(tapping.ring): finish_tap(1.0)

## The tap landed (or the ring ran out): `timing` is how far the ring had shrunk, 0..1.
func finish_tap(timing: float) -> void:
	var obj: String = tapping.object
	tapping.object = ""
	player.channel_time = 0.0
	player.channel_action = ""
	var r := Game.submit({"type": "complete_node", "object": obj, "timing": timing})
	if not r.ok:
		if r.has("text"): add_log(str(r.text), UiKit.MIST)
		return
	add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(r.item)), int(r.count)], UiKit.GOLD if r.get("perfect", false) else UiKit.BRIGHT_JADE)
	pulses["tap:" + ("perfect" if r.get("perfect", false) else "miss")] = 0.6

func _notification(what):
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		for id in touches:   # a guard held on Attack (decision 35) ends with its touch
			var g = touches[id].get("gesture")
			if g != null and g.guarding and _aims(): player.release_guard()
		touches.clear()
		joystick_id = -999
		mouse_down = false
		_attack_up()
		if is_instance_valid(player):
			player.movement = Vector2.ZERO
			player.joystick_engaged = false
			player.reset_sprint()

# ------------------------------------------------------------------ the layout now
## A technique slot that holds a technique (an empty or locked slot is not drawn, review G3).
func _slot_filled(slot: int) -> bool:
	if not bound(): return true
	var c = Game.active()
	if slot >= ProgressionRules.technique_slot_count(c) or slot >= c.cultivator.technique_slots.size(): return false
	var tid = c.cultivator.technique_slots[slot]
	return tid != null and str(tid) != ""

## The techniques are out: once the HUD shows them, at rest as in a fight (decision 42).
func _skills_live() -> bool:
	return shown("skills")

## The page tab shows with the techniques once the second page is open.
func _page_tab_shown(c) -> bool:
	return _skills_live() and (not bound() or Unlocks.is_unlocked(c.id, "technique_page_2"))

## The fan's toggles the player has, each with its role and its place while the fan is open.
func _fan_items() -> Array:
	var out: Array = []
	for id in FAN_TOGGLES:
		if not shown(id): continue
		var deg: float = FAN_DEG_OPEN[out.size()]
		var at := _on(fan_center, FAN_R, deg)
		out.append({"id": id, "role": FAN_ROLE[id], "center": at, "deg": deg})
		set(str(FAN_ROLE[id]) + "_center", at)
	return out

## A toggle that is on: Cultivate while meditating, the Presence held, the Sphere raised.
func toggle_on(c, id: String) -> bool:
	if c == null: return false
	match id:
		"cultivate": return c.cultivator.meditating
		"presence": return Game.field.is_on(c.id)
		"sphere": return Game.field.sphere_on(c.id)
	return false

## The toggles pinned beside the closed fan: the ones that are on (decision 20: the fan shows them while closed).
func _pins(c) -> Array:
	if not bound(): return ["presence"] if shown("presence") else []
	return FAN_TOGGLES.filter(func(id): return shown(id) and toggle_on(c, id))

func _treasure_id(c, slot: int) -> String:
	var tid := str(c.inventory.treasures[slot])
	return "" if tid == "" or c.inventory.count(tid) <= 0 else tid   # sold or stored: the slot is empty again

## Ring 2 beside the fan as it stands now: [{role, center, deg, toggle}]. While the fan is closed, a toggle that is on;
## in a fight, the healing slot, the Draught and the treasures that hold something; at rest, the healing slot while it
## holds something to drink or a quest step asks for it (Granny's Remedy: the player must see where the tea goes), clear
## of the open fan; the context whenever the world offers something in reach (decision 42: its own button, at rest as in
## a fight) and, at rest beside a node, the post chip; the weapon swap when there is a spare. An empty slot is not drawn
## (mockup 01).
func _ring2(c) -> Array:
	var items: Array = []
	var loose := not bound()
	if not loose and c == null: return items
	if not fan_open:
		for id in _pins(c): items.append({"role": FAN_ROLE[id], "home": "pin" if items.is_empty() else "", "toggle": id})
	if fight and not fan_open:
		# Decision 45: the three quick slots, each while it holds something (every one unbound).
		for qi in QUICK_SLOTS:
			if shown("quick_use") and (loose or str(c.inventory.quick[qi]) != ""): items.append({"role": "quick:%d" % qi, "home": "quick:%d" % qi})
		if _has_draught(): items.append({"role": "draught", "home": ""})
		for ti in 2:
			if shown("treasure_%d" % (ti + 1)) and (loose or _treasure_id(c, ti) != ""): items.append({"role": "treasure:%d" % ti, "home": "treasure:%d" % ti})
	elif not fight and not loose and shown("quick_use"):
		for qi in QUICK_SLOTS:
			if c.inventory.count(str(c.inventory.quick[qi])) > 0 or (qi == 0 and _quick_asked(c)): items.append({"role": "quick:%d" % qi, "home": "quick:%d" % qi})
	if _context_shown(): items.append({"role": "context", "home": "context"})
	if _post_chip(): items.append({"role": "post", "home": "post"})
	if shown("weapon_swap") and (loose or c.inventory.loadout.get("spare") != null): items.append({"role": "swap", "home": "swap"})
	var fan_at: Array = _fan_items().map(func(f): return f.center) if fan_open else []
	return ring2_places(items, RING2_DEG.filter(func(d): return fan_at.any(func(p): return (p as Vector2).distance_to(_on(attack_center, RING2_R, float(d))) < 60.0)))

## Places on ring 2 for `items` ([{role, home}]): each takes its home if it is free, the rest the next free place in
## order (never one of `taken`, the places the open fan covers). Decision 45: past ring 2's free places the rest stand
## on the outer row (RING3_DEG), in order; past both (a load no state makes), the last spread over the outer row.
func ring2_places(items: Array, taken: Array = []) -> Array:
	var out: Array = []
	var deg := {}
	var outer := {}
	var free: Array = RING2_DEG.filter(func(d): return not taken.has(d))
	for i in items.size():
		var home := str(items[i].get("home", ""))
		if RING2_HOME.has(home) and free.has(RING2_HOME[home]):
			deg[i] = RING2_HOME[home]
			free.erase(RING2_HOME[home])
	var row3: Array = RING3_DEG.duplicate()
	for i in items.size():
		if deg.has(i): continue
		if not free.is_empty(): deg[i] = free.pop_front()
		else:
			outer[i] = true
			deg[i] = row3.pop_front() if not row3.is_empty() else lerpf(RING3_DEG[0], RING3_DEG[-1], float(i % 4) / 3.0)
	for i in items.size():
		var o: Dictionary = items[i].duplicate()
		o.deg = float(deg[i])
		o.center = _on(attack_center, RING3_R if outer.has(i) else RING2_R, float(deg[i]))
		out.append(o)
	return out

# ------------------------------------------------------------------ input
## The smallest HUD hit circle's radius (P4, docs/ui_style_guide.md §7): 48 px across, and never less than the drawn
## radius + 4.
const HIT_MIN := 24.0

## Every round control the HUD shows now, as a hit circle {role, center, drawn, r}. The hud_suite in rules_tests holds
## the table to HIT_MIN and the drawn radius + 4.
## `badges`: the points badges showing (the HUD's frame passes its own, _frame_badges), else asked now.
func hit_targets(badges = null) -> Array:
	var out: Array = []
	var add := func(role: String, center: Vector2, drawn: float, hit := 0.0) -> void:
		out.append({"role": role, "center": center, "drawn": drawn, "r": maxf(maxf(HIT_MIN, drawn + 4.0), hit)})
	var c = Game.active()
	if shown("attack"): add.call("attack", attack_center, 66.0, 74.0)
	if shown("jump"): add.call("jump", jump_center, JUMP_R)
	if shown("guard"): add.call("guard", guard_center, 26.0)
	if _skills_live():
		# A technique's round button (decision 43): `drawn` its radius, its hit circle a little past it.
		for i in slots.size():
			if _slot_filled(i + skill_page * 4): add.call("skill", slots[i], TILE * 0.5, TILE * 0.5 + 6.0)
	if _page_tab_shown(c): add.call("page", page_center, 24.0)
	var fan := _fan_items()
	if not fan.is_empty():
		add.call("fan", fan_center, 26.0)
		if fan_open:
			for f in fan: add.call(str(f.role), f.center, 26.0)
	for it in _ring2(c): add.call(str(it.role), it.center, CTX_R if str(it.role) == "context" else 26.0)
	for ic in icon_row:
		if shown(ic[0]): add.call("icon:" + str(ic[0]), ic[1], 26.0)
	for pc in _party_chips(c): add.call("pets:" + str(pc.kind) + ":" + str(pc.uid), pc.center, float(pc.r))
	if _auto_hunt_shown(c): add.call("auto_hunt", auto_center, 26.0)
	for pb in (point_badges(c) if badges == null else badges): add.call("points:" + str(pb.id), pb.center, 16.0, POINTS_PITCH * 0.5)
	return out

## Decision 45: hit_targets as they stand this frame, for the tutorial coach (tour_rect). The coach asks for several
## anchors a frame, and each asking afresh counted the points badges again (the Realisations' walks the technique trees):
## half a millisecond a frame on a desktop while a HUD lesson showed. Asked again on a new frame, when the game moves on
## (Game.revision) or the fan opens or shuts.
var _tour_targets := FrameMemo.new()
func tour_targets() -> Array:
	return _tour_targets.value([fan_open, fight, skill_page], func(): return hit_targets(_frame_badges()))

## Decision 43 (docs/redesign/tutorials.md): a tutorial's anchor on the HUD, by name, so a tour never leans on how the HUD
## is laid out: a round control by its role in hit_targets ("attack", "jump", "skill" for all the technique buttons,
## "icon:menu", "points:meridian", …) or a plate ("minimap", "portrait", "tracker", "progress", "log", and the panel's
## "qi" and "soul" bars with their labels). Rect2() while it is not shown. Decision 44: a Treasure button ("treasure:0",
## "treasure:1") comes out only in a fight; at rest, once revealed, its anchor is where it comes out then (ring 2).
func tour_rect(name: String) -> Rect2:
	var c = Game.active()
	match name:
		"minimap": return minimap_rect if shown("minimap") else Rect2()
		"portrait": return panel_rect(c) if shown("player_panel") else Rect2()
		"tracker": return tracker_rect if shown("quest_tracker") else Rect2()
		"progress": return Rect2(0, 704, 1280, 16) if shown("progress_bar") else Rect2()
		"log": return log_rect()
		"qi", "soul":
			# The bars' rows as _draw_player_panel lays them: HP, then QI once there is a pool, then SL.
			if c == null or not shown("player_panel"): return Rect2()
			var qi: bool = c.pools.max_qi > 0.0 and shown("qi_bar")
			var at := panel_rect(c).position + Vector2(18, 78.0 if shown("hp_bar") else 60.0)
			if name == "qi": return Rect2(at, Vector2(330, 14)) if qi else Rect2()
			return Rect2(at + Vector2(0, 18.0 if qi else 0.0), Vector2(330, 14)) if c.pools.max_soul > 0.0 and shown("soul_bar") else Rect2()
	var out := Rect2()
	for tg in tour_targets():
		# Decision 45: "quick" is the quick slots that show ("quick:0" to "quick:2" each on its own).
		if str(tg.role) != name and not (name == "quick" and str(tg.role).begins_with("quick:")): continue
		var d := float(tg.drawn) + 2.0
		var r := Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0)
		out = r if out.size == Vector2.ZERO else out.merge(r)
	if out.size == Vector2.ZERO and name in ["treasure:0", "treasure:1"] and not fight and shown("treasure_%d" % (int(name.right(1)) + 1)):
		var at := _on(attack_center, RING2_R, float(RING2_HOME["treasure:0"]) + 22.0 * int(name.right(1)))
		return Rect2(at - Vector2(28, 28), Vector2(56, 56))
	return out

## The points badges showing now, in POINT_SYSTEMS order: {id, count, center, page, tab}. Bound only (the counts are
## the character's); a system not yet unlocked or with nothing to spend has none.
func point_badges(c) -> Array:
	var out: Array = []
	if c == null or not bound() or not shown("player_panel"): return out
	var panel := panel_rect(c)
	for row in POINT_SYSTEMS:
		if not Unlocks.is_unlocked(c.id, str(row.unlock)): continue
		var n := int(points_override[row.id]) if points_override.has(row.id) else int(Game.get(str(row.count[0])).call(str(row.count[1]), c))
		if n <= 0: continue
		out.append({"id": str(row.id), "count": n, "page": str(row.page), "tab": str(row.tab),
			"center": Vector2(panel.end.x - 22.0 - out.size() * POINTS_PITCH, panel.position.y + 2.0)})
	return out

## A tap on a points badge asks the shell for its system's page, on the tab where the points are spent.
func open_points(id: String) -> void:
	for row in POINT_SYSTEMS:
		if str(row.id) != id: continue
		open_page.emit(str(row.page), {"tab": str(row.tab)} if str(row.tab) != "" else {})
		Audio.ui("ui_open")

## The points badges for the HUD's own frame (its tick, the rects the world's names keep off, its drawing), worked out
## once a frame: each asks every system for its count, and the Realisations' walks the technique trees (a tenth of the
## HUD's frame, three times over). Asked again when the game moves on (Game.revision), the frame is another or a test's
## override changes; point_badges itself always asks afresh.
var _badges_memo := FrameMemo.new()
var _badges: Array = []   ## the badges last worked out (obstacle_rects knows the frame's by them)
func _frame_badges() -> Array:
	var c = Game.active() if bound() else null
	return _badges_memo.value([c.get_instance_id() if c is Object else 0, points_override], _work_badges.bind(c))

func _work_badges(c) -> Array:
	_badges = point_badges(c)
	return _badges

## Each frame: a badge newly shown starts its pop, and (after the first look) writes its line to the log. `badges`: the
## frame's (_frame_badges), else asked now.
func _tick_points(badges = null) -> void:
	var now := {}
	for pb in (point_badges(Game.active() if bound() else null) if badges == null else badges):
		now[pb.id] = true
		if not _points_seen.has(pb.id):
			_points_seen[pb.id] = t
			if _points_primed: add_log(Tx.t("hud.points_" + str(pb.id)), UiKit.PALE_GOLD)
	for id in _points_seen.keys():
		if not now.has(id): _points_seen.erase(id)
	_points_primed = bound()

## A badge's pop: how far in (0 .. 1) since it appeared, 1 at once with Reduce motion.
func points_pop(id: String) -> float:
	if UiKit.reduce_motion(): return 1.0
	return clampf((t - float(_points_seen.get(id, -99.0))) / POINTS_POP_S, 0.0, 1.0)

## The badges in their row, each popping in as it appears: from small past full size and back, fading in.
func _draw_points(_c) -> void:
	for pb in _frame_badges():
		var k := points_pop(str(pb.id))
		if k >= 1.0:
			glyph("points_" + str(pb.id), pb.center, 32)
			continue
		var s := lerpf(0.4, 1.2, k / 0.6) if k < 0.6 else lerpf(1.2, 1.0, (k - 0.6) / 0.4)
		draw_set_transform(pb.center, 0.0, Vector2(s, s))
		glyph("points_" + str(pb.id), Vector2.ZERO, 32, Color(1, 1, 1, clampf(k * 2.5, 0.0, 1.0)))
		draw_set_transform(Vector2.ZERO)

## The screen rects the HUD covers now (its round controls as drawn, its panels and plates), which the world's names
## keep clear of (G4). `badges`: the points badges as hit_targets takes them.
func obstacle_rects(badges = null) -> Array:
	var out: Array = []
	# Asked with the frame's badges (the HUD's own frame): the frame's targets, shared with the tutorial coach's anchors.
	for tg in (tour_targets() if badges != null and is_same(badges, _badges) else hit_targets(badges)):
		var d := float(tg.drawn) + 2.0
		out.append(Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0))
	var c = Game.active()
	if shown("player_panel"): out.append(panel_rect(c))
	if shown("minimap"): out.append(minimap_rect)
	if tracker_rect.size.x > 0.0: out.append(tracker_rect)
	if purse_rect.size.x > 0.0: out.append(purse_rect)
	if status_rect.size.x > 0.0 and shown("player_panel"): out.append(status_rect)
	if not equip_prompt.current.is_empty(): out.append(EquipPrompt.RECT)
	if _boss() != null: out.append(Rect2(400, 92, 480, 84))
	if _context_shown(): out.append(context_label_rect())
	var log_r := log_rect()
	if log_r.size.x > 0.0: out.append(log_r)
	return out

## The log's rows as they stand (none when it is empty): the world's labels keep off them while they show (the
## polish pass saw a boarlet's plate across "Codex: Body training").
func log_rect() -> Rect2:
	var lines := log_lines if shown("system_log") else log_lines.filter(func(l): return l.get("always", false))
	var rows := log_rows(lines)
	var n := rows.size()
	if n == 0: return Rect2()
	var w := 0.0
	for r in rows: w = maxf(w, float(r.indent) + UiKit.text_width(str(r.text), 16, true))
	var x := 20.0 if not left_handed else 1280.0 - 20.0 - LOG_W   # where _draw_log draws it
	return Rect2(x, LOG_FOOT - (n - 1) * 21.0 - 16.0, minf(w, LOG_W), (n - 1) * 21.0 + 22.0)

## The player panel, one row taller once the Soul bar shows: it draws there, and the whole of it opens Character.
func panel_rect(c) -> Rect2:
	var soul_row: bool = c != null and c.pools.max_soul > 0.0 and shown("soul_bar")
	return Rect2(16, 16, 360, 120 if soul_row else 104)

## The tracker's plate starts this far under the player panel (clear of the status row and the Hollowing meter's
## stops), and stops at the foot, above the log.
const TRACKER_DROP := 52.0
const TRACKER_FOOT := 320.0

## A tracker line's go button hit area: 48 x 48 round the drawn button (P4 §7).
static func go_hit(drawn: Rect2) -> Rect2:
	return Rect2(drawn.get_center() - Vector2(24, 24), Vector2(48, 48))

func role_at(p: Vector2) -> String:
	# The equip prompt's two buttons (clear of every control; the rest of its card lets a tap through).
	var prompt := equip_prompt.role_at(p) if bound() else ""
	if prompt != "": return prompt
	# Where round controls overlap, the nearest centre wins (§7).
	var best := ""
	var best_d := INF
	for tg in hit_targets():
		var d := p.distance_to(tg.center)
		if d < float(tg.r) and d < best_d:
			best = str(tg.role)
			best_d = d
	if best != "": return best
	if minimap_rect.has_point(p) and shown("minimap"): return "minimap"
	var panel := panel_rect(Game.active())
	if panel.has_point(p) and shown("player_panel"): return "portrait"
	var go := ""
	var go_d := INF
	for tp in tracker_paths:
		if (tp.rect as Rect2).has_point(p) and shown("quest_tracker") and p.distance_to((tp.rect as Rect2).get_center()) < go_d:
			go = "path:" + str(tp.target)
			go_d = p.distance_to((tp.rect as Rect2).get_center())
	if go != "": return go
	if tracker_rect.has_point(p) and shown("quest_tracker"): return "tracker"
	if Rect2(0, 704, 1280, 16).has_point(p) and shown("progress_bar"): return "progress"
	if (p.x < 640) != left_handed: return "joystick"
	return "none"

func press(id: int, p: Vector2):
	var role := role_at(p)
	touches[id] = {"role": role, "start": p, "swiped": false}
	# Top-down redesign, Phase 2 (decision 30): Attack and the techniques aim. A touch is read as a tap (on release) or,
	# held or dragged, as an aim (AimGesture); the world shows the aim on the ground while the thumb is down.
	if _aims() and (role == "attack" or role == "skill"):
		touches[id]["gesture"] = AimGesture.new(role, attack_center if role == "attack" else _nearest_slot_center(p))
		if role == "attack": return
	match role:
		"joystick":
			if joystick_id == -999:
				joystick_id = id
				joystick_origin = p
				joystick_pos = p
				player.joystick_engaged = true
		"attack": primary()
		"jump":
			player.jump()
			player.jump_held = true   # S43: held while falling it glides, or from Cloud Stride 1 flies
			player.fly_up = true      # held Jump climbs while flying
		"meditate":
			if bound():
				cultivate_pressed = true
				cultivate_hold = 0.0
			else:
				player.meditate()
		"skill":
			# The nearest drawn slot of the page (ring 1's circles overlap; the nearest centre wins, and an empty slot is
			# not there to win).
			var near_i := -1
			for i in slots.size():
				if _slot_filled(i + skill_page * 4) and (near_i < 0 or p.distance_to(slots[i]) < p.distance_to(slots[near_i])): near_i = i
			if near_i >= 0: touches[id]["slot"] = near_i + skill_page * 4
		"page": scroll_skills(-1)
		"fan": toggle_fan()
		"guard":
			if player.state.flying: player.fly_down = true   # held Evade descends while flying; a tap dashes (S43)
			guard_pressed = true
			guard_hold = 0.0
		"quick:0", "quick:1", "quick:2": use_quick(int(role.right(1)))
		"draught": drink_draught()
		"sense":
			if bound():
				var sr := Game.submit({"type": "sense_pulse"})
				if not sr.ok and sr.has("text"): add_log(str(sr.text), UiKit.MIST)
		"presence": toggle_presence()
		"sphere": toggle_sphere()
		"pet":
			if bound():
				pet_pressed = true
				pet_hold = 0.0
				pet_wheel = false
		"context": use_context()
		"post": keep_post()
		"treasure:0", "treasure:1": use_treasure(int(role.get_slice(":", 1)))
		"swap": swap_weapon()
		"prompt:equip":
			var er := equip_prompt.equip(Game.active())
			if not er.get("ok", false) and er.has("text"): add_log(str(er.text), UiKit.MIST)
		"prompt:close": equip_prompt.dismiss()
		"minimap": open_page.emit("world_map", minimap_place_at(p))
		"portrait": open_page.emit("character", {})
		"tracker": open_page.emit("quests", {})
		"auto_hunt":
			var ac = Game.active()
			var ah := Game.submit({"type": "set_auto_hunt", "on": not Game.world.auto_hunting(ac.id)})
			if not ah.get("ok", false) and ah.has("text"): add_log(str(ah.text), UiKit.MIST)
		"progress": open_page.emit("cultivation", {})
		_:
			if role.begins_with("points:") and bound(): open_points(role.trim_prefix("points:"))
			if role.begins_with("pets:") and bound():
				var parts := role.split(":")
				var res := {}
				match parts[1]:
					"active", "party": open_page.emit("spirit_animals", {})
					"companion": open_page.emit("companions", {})
					"bag": res = Game.submit({"type": "swap_pet_from_bag", "pet": parts[2]})
					"mount": res = Game.submit({"type": "set_mount"})
				if not res.is_empty() and not res.get("ok", false) and res.has("text"): add_log(str(res.text), UiKit.MIST)
			if role.begins_with("path:") and bound():
				var target := role.trim_prefix("path:")
				var pc = Game.active()
				var ap := Game.submit({"type": "auto_path", "target": "" if Game.world.auto_path_target(pc) == target else target})
				if not ap.get("ok", false) and ap.has("text"): add_log(str(ap.text), UiKit.MIST)
			if role.begins_with("icon:"):
				var which := role.trim_prefix("icon:")
				open_page.emit({"menu": "menu", "bag": "inventory", "map": "world_map", "mail": "mail"}[which], {})
				Audio.ui("ui_open")
	# In a fight the open fan is a quick pick: a toggle taken from it folds it again, out of the ring's way.
	if fight and fan_open and role in FAN_ROLE.values(): fan_open = false

## The fan opens and closes (decision 20). At rest the choice is kept: it opens again after the next fight if left open.
func toggle_fan() -> void:
	fan_open = not fan_open
	if not fight: fan_rest_open = fan_open
	Audio.ui("ui_tap")

func drag(id: int, p: Vector2):
	if not touches.has(id): return
	if id == joystick_id:
		var delta = p - joystick_origin
		joystick_pos = p
		player.movement = delta.limit_length(76) / 76 if delta.length() > 9 else Vector2.ZERO
	elif touches[id].has("gesture"):
		(touches[id].gesture as AimGesture).drag(p)
	elif touches[id].role == "pet" and pet_wheel:
		pet_pick = _wheel_pick(p)
	elif touches[id].role == "skill" and not touches[id].swiped:
		var delta = p - touches[id].start
		if absf(delta.y) > 40 and absf(delta.y) > absf(delta.x):
			scroll_skills(-1 if delta.y < 0 else 1)
			touches[id].swiped = true

func release(id: int):
	var info: Dictionary = touches.get(id, {})
	touches.erase(id)
	if id == joystick_id:
		joystick_id = -999
		player.movement = Vector2.ZERO
		player.joystick_engaged = false
		player.reset_sprint()
	if info.get("role", "") == "meditate" and bound():
		if cultivate_hold >= 0.0 and cultivate_pressed:
			cultivate_pressed = false
			tap_cultivate()
		cultivate_pressed = false
	if info.has("gesture"):
		_release_aim(info)
		return
	if info.get("role", "") == "skill" and not info.get("swiped", false) and info.has("slot") and bound():
		_technique_said(player.use_technique(int(info.slot)))
	if info.get("role", "") == "pet" and bound() and pet_pressed:
		pet_pressed = false
		if pet_wheel:
			pet_wheel = false
			if pet_pick >= 0: _pet_wheel_do(str(PET_WHEEL[pet_pick]))
		else:
			open_page.emit("spirit_animals", {})
	if info.get("role", "") == "attack": _attack_up()
	if info.get("role", "") == "jump":
		player.fly_up = false
		player.jump_held = false
	if info.get("role", "") == "guard": player.fly_down = false
	if info.get("role", "") == "guard" and bound() and guard_pressed:
		guard_pressed = false
		if guard_hold <= 0.18:
			_dodge()
		Game.submit({"type": "guard_end"})

## A technique refused says why in the log (no Qi, not ready, the wrong weapon, sealed, only in flight).
func _technique_said(r: Dictionary) -> void:
	if not r.get("ok", false) and r.get("reason", "") in ["no_qi", "cooldown", "wrong_weapon", "sealed", "needs_flight"]:
		add_log({"no_qi": Tx.t("hud.not_enough_qi"), "cooldown": Tx.t("hud.not_ready"), "wrong_weapon": str(r.get("text", Tx.t("hud.wrong_weapon"))), "sealed": Tx.t("hud.your_qi_is_sealed"), "needs_flight": Tx.t("hud.only_in_flight")}[r.reason], UiKit.MIST)

## The player aims on the plane (the top-down room, redesign Phase 2); the side view's facing is only left or right.
func _aims() -> bool:
	return is_instance_valid(player) and player.has_method("aim_attack")

## The drawn technique slot of the page nearest `p` (its aim starts from that button's centre).
func _nearest_slot_center(p: Vector2) -> Vector2:
	var best: Vector2 = slots[0]
	for i in slots.size():
		if _slot_filled(i + skill_page * 4) and p.distance_to(slots[i]) < p.distance_to(best): best = slots[i]
	return best

## Each held Attack or technique touch that aims shows its aim on the ground (the player's preview, the world's drawing).
func _tick_aims(delta: float) -> void:
	if not _aims(): return
	var shown_aim := false
	for id in touches:
		var g = touches[id].get("gesture")
		if g == null: continue
		g.advance(delta)
		if g.kind == "attack": _tick_hold(g)
		if (g.aiming or g.guarding) and not shown_aim:
			player.preview_aim(g.kind, int(touches[id].get("slot", -1)), g.dir(), g.reach_k(), armed(g))
			shown_aim = true
	if not shown_aim: player.aim = {}

## Decision 35: Attack's drag moves are live while the character may attack and is not busy with a harvest tap or a
## channel (decision 42: a context in reach never takes the button).
func _moves_live() -> bool:
	return bound() and tapping.object == "" and channel.object == "" and attack_first()

## What an Attack or technique touch would do if let go now: tap, aim, cancel, or one of Attack's drag moves
## (finisher, plunge, guard) while they are live.
func armed(g: AimGesture) -> String:
	if g.kind != "attack" or not _aims(): return g.release()
	if g.guarding: return "guard"
	if not _moves_live(): return g.release()
	return g.move(not player.motor.grounded, player.plunge_ready())

## Attack held still past `guard_s`: the guard (or the slotted stance) starts on the ground; in the air it waits for
## the landing. A refused guard (a weapon that cannot guard), or a button that is not attacking, leaves the let-go a tap.
func _tick_hold(g: AimGesture) -> void:
	if not g.holding(): return
	if not _moves_live():
		g.refused = true
		return
	if not player.motor.grounded: return
	var got: String = player.hold_guard()
	if got == "":
		g.refused = true
		return
	g.guarding = true
	g.guard_kind = got

## Letting go of an aiming touch: a tap attacks or casts at the soft lock, an aim along its direction, a cancel does
## nothing. Attack's drag moves (decision 35): a finisher strikes the combo's last step along the drag, a plunge drops
## (an aimed blow down if it cannot), and a guard held on the button ends and strikes nothing.
func _release_aim(info: Dictionary) -> void:
	var g: AimGesture = info.gesture
	var what := armed(g)
	player.aim = {}
	if info.role == "attack":
		var may: bool = bound() and Unlocks.is_unlocked(Game.active_id, "attack")
		match what:
			"tap": primary()
			"aim": if may: player.aim_attack(g.dir())
			"finisher": if may: player.finisher(g.dir())
			"plunge":
				if not player.plunge().get("ok", false) and may: player.aim_attack(g.dir())
			"guard": player.release_guard()
		_attack_up()
	elif info.has("slot") and bound():
		match what:
			"tap": _technique_said(player.use_technique(int(info.slot)))
			"aim": _technique_said(player.aim_technique(int(info.slot), g.dir(), g.reach_k()))

## A tap of Dodge: the combat authority's dodge, or the top-down prototype's own dash (redesign Phase 1).
func _dodge() -> void:
	if player.has_method("dodge"): player.dodge()
	else: Game.submit({"type": "dodge", "direction": player.last_axis, "facing": player.facing})

## Where each choice of the pet command wheel sits around the Pet button.
func _wheel_pos(i: int) -> Vector2:
	var a := -PI / 2.0 + TAU * float(i) / float(PET_WHEEL.size())
	return pet_center + Vector2(cos(a), sin(a)) * 104.0

func _wheel_pick(p: Vector2) -> int:
	if p.distance_to(pet_center) < 40.0: return -1
	var best := -1
	var bd := 70.0
	for i in PET_WHEEL.size():
		var d := p.distance_to(_wheel_pos(i))
		if d < bd:
			bd = d
			best = i
	return best

func _pet_wheel_do(choice: String) -> void:
	var res := {}
	match choice:
		"ride": res = Game.submit({"type": "set_mount"})
		"bag": open_page.emit("spirit_animals", {})
		_: res = Game.submit({"type": "pet_command", "command": choice})
	if not res.is_empty() and not res.get("ok", false) and res.has("text"): add_log(str(res.text), UiKit.MIST)

func _draw_pet_wheel(c) -> void:
	if not pet_wheel: return
	draw_circle(pet_center, 152.0, Color(UiKit.PLATE, 0.86))
	draw_arc(pet_center, 152.0, 0, TAU, 64, Color(UiKit.GOLD, 0.6), 2.0)
	var cur := str(Game.pets.commands.get(c.id, "follow"))
	for i in PET_WHEEL.size():
		var id := str(PET_WHEEL[i])
		var pos := _wheel_pos(i)
		var on := i == pet_pick
		var active := id == cur
		ring(pos, 34, on)
		if active: draw_arc(pos, 38, 0, TAU, 32, UiKit.GOLD, 2.0)
		var label := Tx.t("hud.pet_cmd_" + id)
		if id == "ride": label = Tx.t("hud.pet_cmd_dismount") if c.mount_pet != "" and c.riding else Tx.t("hud.pet_cmd_ride")
		UiKit.draw_outlined(self, label, pos + Vector2(-44, 6), 16, UiKit.GOLD if on else (UiKit.PALE_GOLD if active else UiKit.PAPER), HORIZONTAL_ALIGNMENT_CENTER, 88)
	UiKit.draw_outlined(self, Tx.t("hud.pet_cmd_title"), pet_center + Vector2(-150, -162), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 300)

func tap_cultivate() -> void:
	var c = Game.active()
	if c.cultivator.state == "bottleneck" and not c.cultivator.meditating:
		open_page.emit("breakthrough", {})
		return
	player.meditate()

## The Attack button: it attacks, at rest as in a fight (decision 42); a harvest's hold or its tap (begun from the
## context's button) keeps the hands busy. Before the Attack lesson there is no button, and the J and Enter keys use the
## context.
func primary() -> void:
	if not bound():
		player.attack()
		return
	if tapping.object != "" or channel.object != "": return
	if attack_first():
		player.attack()
		attack_pressed = true
		attack_hold = 0.0
	elif not context.is_empty(): use_context()

## Held Attack with a flute plays the melody aura once the family's hold time has passed (S47 v1.1).
func _try_melody() -> void:
	if not bound() or Game.combat.is_playing(Game.active_id): return
	var ch: Dictionary = StatRules.family(Game.active()).get("channel", {})
	if ch.is_empty() or attack_hold < float(ch.get("hold_s", 0.35)): return
	var r := Game.submit({"type": "channel_melody", "on": true})
	if r.ok or str(r.get("reason", "")) == "busy": return   # a busy hand tries again next frame
	attack_pressed = false
	if str(r.get("reason", "")) == "no_composure" and r.has("text"): add_log(str(r.text), UiKit.MIST)

func _attack_up() -> void:
	attack_pressed = false
	attack_hold = 0.0
	if bound() and Game.combat.is_playing(Game.active_id): Game.submit({"type": "channel_melody", "on": false})

## S43 rule 5: an enemy aggroed on the player within 400 makes a fight (the Attack button attacks either way since
## decision 42; Climb and Enter are on the context's own button).
func _enemy_close() -> bool:
	if Game.room_rt == null or not is_instance_valid(player): return false
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("passive", false): continue
		if str(e.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"] and e.plane.distance_to(player.plane) < 400.0: return true
	return false

## The attack button's one rule: once the character may attack it attacks, always. A gathering node, a pickup, a
## person, a door or a ladder beside you never takes it: what the context offers has its own button on ring 2. An
## earlier fix held to this in a fight (a resource under the player had taken the button mid-fight); decision 42 holds
## to it at rest too (mockup 02's context on the big button is retired).
func attack_first() -> bool:
	return bound() and Unlocks.is_unlocked(Game.active_id, "attack")

## A fight now: the P5a rest/fight state (a foe within the fight range, one engaged with you anywhere in the room, which
## is also one attacking you or struck a moment ago, and FIGHT_HOLD_S after).
func _in_fight() -> bool:
	return fight or _fight_now()

## A foe engaged with the player anywhere in the room: turned on them, striking, recovering, fleeing (EnemyState.in_fight).
func _foe_engaged() -> bool:
	if Game.room_rt == null: return false
	return Game.room_rt.living_enemies().any(func(e): return e.team == "enemy" and not e.def.get("passive", false) and e.in_fight())

## The context's own button on ring 2 (decision 42): whatever the world offers in reach, at rest as in a fight, and a
## harvest it began while it waits for its tap.
func _context_shown() -> bool:
	return not context.is_empty() or tapping.object != ""

## S50 Keeping Post: beside a node, out of a fight, the Keep Post button shows. One character is enough: the post works
## while the game is put away, or for an incense stick burnt at it.
func _post_chip() -> bool:
	return bound() and str(context.get("type", "")) in ["herb_patch", "ore_vein", "fishing_spot", "insect_swarm"] and not _in_fight() \
		and Unlocks.is_unlocked(Game.active_id, "keeping_post")

## S50 node plate: beside a gathering node, the Chance a post there would have for its first output (cached).
var _plate_key := ""
var _plate_text := ""
func _node_plate(c) -> String:
	if not str(context.get("type", "")) in ["herb_patch", "ore_vein", "fishing_spot", "insect_swarm"] or not Unlocks.is_unlocked(c.id, "keeping_post"): return ""
	var key := "%s:%d" % [str(context.get("object", "")), int(t)]
	if key != _plate_key and Game.room_rt != null:
		_plate_key = key
		var r: Dictionary = Game.posts.rates_at(c, Game.room_rt.object_def(str(context.get("object", ""))))
		var outs: Array = r.get("outputs", [])
		_plate_text = " · %d%%" % int(round(100.0 * float(outs[0].chance))) if not outs.is_empty() else " · —"
	return _plate_text

func keep_post() -> void:
	if not bound(): return
	var r := Game.submit({"type": "take_post", "object": str(context.get("object", ""))})
	if not r.get("ok", false):
		add_log(str(r.get("text", Tx.t("hud.post_fail"))), UiKit.MIST)
		return
	open_page.emit("posts", {})

## Decision 44: using a place plays its pose first (data/places.json `pose`: open a lid, a letter box or a door; tend a bed
## or a furnace; sit on the mat), for PLACE_POSE_S, then opens its page; a second tap on the context button opens it at
## once. The body keeps the pose while the page it opened is open (seated at the mat through the Cultivation page) and
## rises when it closes (set_blocked). Each pose raises its sound (`place_open`, `place_tend`, `place_sit`).
const PLACE_POSE_S := 0.4
var place_pending: Dictionary = {}   ## {page, args, t}: a page waiting for its place's pose

## The pose of the place `object_id` of the room is (open, tend, sit), or "".
func place_pose_of(object_id: String) -> String:
	if Game.room_rt == null: return ""
	return str(PlaceRules.at_object(Game.room_rt.room_id, object_id).get("pose", ""))

func _play_place_pose(pose: String, page: String, args: Dictionary) -> void:
	place_pending = {"page": page, "args": args, "t": PLACE_POSE_S}
	var at = player.get("plane") if is_instance_valid(player) else null
	if is_instance_valid(player) and player.has_method("play_place_pose"): player.play_place_pose(pose)
	var p: Vector2 = at if at is Vector2 else Vector2.ZERO
	# each id written out, so audio_tests finds it among the sounds
	match pose:
		"open": Audio.world_sound("place_open", p, 0.0)
		"tend": Audio.world_sound("place_tend", p, 0.0)
		"sit": Audio.world_sound("place_sit", p, 0.0)

func _tick_place_pose(delta: float) -> void:
	if place_pending.is_empty(): return
	place_pending.t = float(place_pending.t) - delta
	if float(place_pending.t) <= 0.0: open_place_page()

## Open the page a place's pose is playing before (at once on a second tap); the pose holds while it is open, and ends
## now if no page came up.
func open_place_page() -> void:
	if place_pending.is_empty(): return
	var p := place_pending
	place_pending = {}
	open_page.emit(str(p.page), p.args)
	if not blocked and is_instance_valid(player) and player.has_method("end_place_pose"): player.end_place_pose()

## The context's button: what the world offers in reach (talk, gather, open, enter, climb); while a harvest it began
## shrinks its ring round the button, the tap that lands it.
func use_context() -> void:
	if not place_pending.is_empty():
		open_place_page()   # decision 44: a second tap skips the place's pose
		return
	if tapping.object != "":
		finish_tap(float(tapping.t) / maxf(0.01, float(tapping.ring)))
		return
	if channel.object != "": return
	if str(context.get("type", "")) == "climbable":
		player.climb_hold = 0.0
		var near_c: Dictionary = player.world.geometry.climbable_near(player.plane, player.altitude, 48.0)
		var open: Dictionary = Game.world.climbable_open(Game.active(), near_c) if not near_c.is_empty() else {"ok": true}
		if not open.get("ok", false):
			add_log(str(open.get("text", "")), UiKit.MIST)
			return
		player.authority.climb(near_c)
		return
	if context.has("portal"):
		world.request_portal(str(context.portal))
		return
	if str(context.get("type", "")) == "mercy":
		open_page.emit("mercy", {"enemy": int(context.enemy), "def": str(context.def)})
		return
	_after_interact(Game.submit({"type": "interact", "object": str(context.get("object", ""))}), str(context.get("object", "")))

## S45: "Pick it" at a rare herb (from the Pick / Dig it up choice) starts the ordinary hold and tap.
func begin_harvest(object_id: String) -> void:
	if object_id == "" or not bound(): return
	_after_interact(Game.submit({"type": "interact", "object": object_id, "pick": true}), object_id)

func _after_interact(r: Dictionary, object_id: String) -> void:
	if not r.ok:
		if r.has("text"): add_log(str(r.text), UiKit.MIST)
		return
	if r.has("dialogue"):
		dialogue_requested.emit(r.dialogue)
		return
	if r.has("open_page"):
		var pa := {"object": object_id}
		pa.merge(r.get("page_args", {}), true)
		var pose := place_pose_of(object_id)
		if pose != "":
			_play_place_pose(pose, str(r.open_page), pa)
			return
		open_page.emit(str(r.open_page), pa)
		return
	if str(r.get("minigame", "")) == "fishing":
		fishing_requested.emit(object_id)
		return
	if float(r.get("channel", 0.0)) > 0.0:
		channel = {"object": object_id, "t": 0.0, "dur": float(r.channel), "action": str(r.get("action", "gather")), "tap": r.get("tap", {})}
		if r.get("early", false): add_log(Tx.t("hud.herb_early"), UiKit.MIST)
		return
	if r.has("text") and str(r.text) != "": add_log(str(r.text), UiKit.PAPER)

## S47 dual loadout: trade the weapon in hand for the spare; with no spare, the bag opens to choose one.
func swap_weapon() -> void:
	if not bound(): return
	var r := Game.submit({"type": "swap_loadout"})
	if not r.ok:
		if r.get("reason", "") == "no_spare": open_page.emit("inventory", {})
		elif r.has("text"): add_log(str(r.text), UiKit.MIST)

func use_treasure(slot: int) -> void:
	if not bound(): return
	var tid := str(Game.active().inventory.treasures[slot])
	if tid == "" or Game.active().inventory.count(tid) <= 0:
		open_page.emit("inventory", {})   # an empty Treasure button opens the bag to choose one
		return
	var r := Game.submit({"type": "use_treasure", "slot": slot})
	if not r.ok:
		if r.get("reason", "") == "cooldown": add_log(Tx.t("hud.not_ready_yet"), UiKit.MIST)
		elif r.has("text"): add_log(str(r.text), UiKit.MIST)

func _has_draught() -> bool:
	var c = Game.active()
	return c != null and c.inventory.draught != null

func drink_draught() -> void:
	if not bound(): return
	var r := Game.submit({"type": "drink_draught"})
	if not r.get("ok", false) and str(r.get("text", "")) != "": add_log(str(r.text), UiKit.MIST)

## Decision 45: a tap on quick slot `slot` (0-2) uses what it holds; an empty one opens the Bag, where it is filled.
func use_quick(slot := 0) -> void:
	if not bound(): return
	if str(Game.active().inventory.quick[slot]) == "":
		open_page.emit("inventory", {})   # nothing in it yet: the Bag, where an item is put in Quick-use
		return
	var r := Game.submit({"type": "use_quick", "slot": slot})
	if not r.ok:
		if r.get("reason", "") == "none_left": add_log(Tx.t("hud.no_left") % ContentDB.item_name(str(r.item)), UiKit.MIST)
		elif r.get("reason", "") == "cooldown": add_log(Tx.t("hud.not_ready_yet"), UiKit.MIST)
		elif r.has("text"): add_log(str(r.text), UiKit.MIST)

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

func set_blocked(value: bool) -> void:
	if value and not blocked: _notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	blocked = value
	# Decision 44: the page a place's pose opened has closed: the body rises (a pose still waiting for its page stays).
	if not value and place_pending.is_empty() and is_instance_valid(player) and player.has_method("end_place_pose"): player.end_place_pose()

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
		if event.pressed and not event.canceled: press(event.index, event.position)
		else: release(event.index)
	elif event is InputEventScreenDrag: drag(event.index, event.position)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		mouse_down = event.pressed
		if event.pressed: press(-1, event.position)
		else: release(-1)
	elif event is InputEventMouseMotion and mouse_down: drag(-1, event.position)
	elif event is InputEventKey and not event.echo:
		if not bound():
			if event.pressed:
				match event.physical_keycode:
					KEY_SPACE: player.jump()
					KEY_J: player.attack()
					KEY_M: player.meditate()
					KEY_TAB: scroll_skills(-1)
			return
		var kc: int = event.physical_keycode
		if event.pressed:
			match kc:
				KEY_SPACE: player.jump()
				KEY_J, KEY_ENTER: primary()
				KEY_F: if _context_shown(): use_context()
				KEY_C: if shown("cultivate"): tap_cultivate()
				KEY_K:
					if shown("guard"):
						guard_pressed = true
						guard_hold = 0.0
				KEY_Q: if shown("quick_use"): use_quick()
				KEY_V: if _has_draught(): drink_draught()
				KEY_G: if shown("presence"): toggle_presence()
				KEY_H: if shown("sphere"): toggle_sphere()
				KEY_O: if _post_chip(): keep_post()
				KEY_R: if shown("weapon_swap"): swap_weapon()
				KEY_Z: if shown("treasure_1"): use_treasure(0)
				KEY_X: if shown("treasure_2"): use_treasure(1)
				KEY_TAB: if shown("menu"): open_page.emit("menu", {})
				KEY_I, KEY_B: if shown("bag"): open_page.emit("inventory", {})
				KEY_M: if shown("map"): open_page.emit("world_map", {})
				KEY_L: if shown("quest_tracker"): open_page.emit("quests", {})
				KEY_E: if shown("pet"): open_page.emit("spirit_animals", {})
				KEY_P: if shown("cultivate"): open_page.emit("cultivation", {})
				KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8:
					if shown("skills"): player.use_technique(kc - KEY_1)
		else:
			if kc in [KEY_J, KEY_ENTER]: _attack_up()
			if kc == KEY_K and guard_pressed:
				guard_pressed = false
				if guard_hold <= 0.18: _dodge()
				Game.submit({"type": "guard_end"})

# ------------------------------------------------------------------ events
## World news (the calendar's events, the seasons, the Heaven Ranking's shifts, a treasure born elsewhere) reaches the
## player only once the calendar is theirs (the World menu's unlock, after the Prologue), never while a staged scene
## holds the stage, and only of a place they know: a room they have been in, and in the top-down world never one past
## the prototype's gate. The prototype's QA found a late-game event's toast ("The Drowned Shrine Surfaces · Abbot's
## Sanctum") over a brand-new player's village and the Hollow Night's timer.
func world_news(room := "") -> bool:
	var c = Game.active()
	if c == null or not Unlocks.is_unlocked(c.id, "world_menu"): return false
	if scene_lock or (scenes != null and scenes.get("run") != null): return false
	if room != "" and (not Game.account.visited_rooms.has(room) or QuestAuthority.past_gate(c, room)): return false
	return true

## A calendar event's own room (or the first of its rooms) for world_news: "" when it names none.
func _event_room(ev: Dictionary) -> String:
	if str(ev.get("room", "")) != "": return str(ev.room)
	var rooms: Array = ev.get("rooms", [])
	for r in rooms:
		if Game.account.visited_rooms.has(str(r)) and not QuestAuthority.past_gate(Game.active(), str(r)): return str(r)
	return str(rooms[0]) if not rooms.is_empty() else ""

## S28 v1.2: raise or lower the Sphere (the reason shows in the log when it cannot be raised).
func toggle_sphere() -> void:
	var r := Game.submit({"type": "toggle_sphere"})
	if not r.get("ok", false): add_log(str(r.get("text", Tx.t("hud.sphere_fail"))), UiKit.MIST)

## S28 v1.2: hold or release the Presence (the reason shows in the log when it cannot be held).
func toggle_presence() -> void:
	if not bound(): return
	var r := Game.submit({"type": "toggle_presence"})
	if not r.get("ok", false): add_log(Tx.t("hud.presence_fail_" + str(r.get("reason", "locked"))), UiKit.MIST)

func add_log(text: String, color = UiKit.PAPER, always := false) -> void:
	log_lines.append({"text": text, "t": 0.0, "color": color, "always": always})
	while log_lines.size() > 5: log_lines.pop_front()

func _pet_name(uid: String) -> String:
	var c = Game.active()
	for pt in (c.pets if c else []):
		if str(pt.uid) == uid: return str(pt.name)
	return Tx.t("hud.your_spirit_animal")

## Wind-ups only from bosses and elites, notices only from monsters off screen.
func _caption_worthy(name: String, p: Dictionary) -> bool:
	if name == "attack_started":
		var e = Game.room_rt.enemies.get(int(str(p.get("actor", "0")))) if Game.room_rt and str(p.get("actor", "")).is_valid_int() else null
		return e != null and (e.is_boss() or e.elite)
	if name == "enemy_aggro":
		var e2 = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
		var st = Game.actor_state(Game.active_id)
		return e2 != null and st != null and Game.room_rt.out_of_view(e2.plane, e2.altitude, st)
	return true

## Vibration on phones, when the player allows it (S40 haptics toggle).
func _buzz(ms: int) -> void:
	if Game.account.settings.get("haptics", true) and OS.has_feature("mobile"): Input.vibrate_handheld(ms)

## Does the world in view draw a plate for the way `portal_id` (which says its refusal itself)?
func _way_plate(portal_id: String) -> bool:
	if not is_instance_valid(world) or not "portal_views" in world: return false
	for pv in world.portal_views:
		if is_instance_valid(pv) and str(pv.def.get("id", "")) == portal_id: return true
	return false

## What a spar opponent says at a moment of the spar ("start", "won", "lost"), quoted with their name, or "" when they
## have no line for it (enemies.json `spar_lines`).
static func spar_line(opponent: String, moment: String) -> String:
	var line := str(ContentDB.entry("enemies", opponent).get("spar_lines", {}).get(moment, ""))
	return "" if line == "" else "%s: “%s”" % [ContentDB.name_of("enemies", opponent), line]

func toast(text: String, kind := "unlock", sub := "") -> void:
	toasts.append({"text": text, "t": 0.0, "kind": kind, "sub": sub, "life": 3.2 if sub == "" else 5.0, "from": _from})
	while toasts.size() > 3: toasts.pop_front()

## P6: a moment that takes an event into itself (a breakthrough's unlock, a tribulation's result) takes back the toast
## the HUD made for it; `_from` is the payload of the event being handled while the toast was made.
var _from = null
func drop_toasts_from(p: Dictionary) -> void:
	toasts = toasts.filter(func(tt): return not is_same(tt.get("from"), p))

## Before the quest tracker is revealed (the prologue), a new quest's first step rides under its toast...
func _first_step(qid: String) -> String:
	var c = Game.active()
	if c == null or shown("quest_tracker") or not c.quests.active.has(qid): return ""
	var objs: Array = Game.quest.quest_def(c, qid).get("objectives", [])
	if objs.is_empty(): return ""
	var need := int(objs[0].get("count", 1))
	return str(objs[0].get("text", "")) + ("  0/%d" % need if need > 1 else "")

## ...and each step forward shows as its own toast: "Pick up Herbal Tea  2/3", ticked when done.
func _objective_toast(qid: String) -> void:
	var c = Game.active()
	if c == null or shown("quest_tracker"): return
	var st: Dictionary = c.quests.active.get(qid, {})
	if st.is_empty(): return
	for line in Game.quest.steps_forward(c, qid, objective_seen.get(qid, [])):
		var txt := str(line.text) + ("  %d / %d" % [int(line.have), int(line.need)] if int(line.need) > 1 else "")
		toast(("✓ " if line.done else "") + txt, "quest")
	objective_seen[qid] = (st.progress as Array).duplicate()

func _on_event(name: String, p: Dictionary) -> void:
	_from = p
	_handle(name, p)
	_from = null

func _handle(name: String, p: Dictionary) -> void:
	if not bound(): return
	if CAPTIONS.has(name) and Game.account.settings.get("captions", false) and _caption_worthy(name, p):
		caption = {"text": Tx.t("hud.caption." + str(CAPTIONS[name])), "t": 0.0}
	match name:
		"item_added":
			if str(p.get("actor", "")) == Game.active_id and shown("system_log"):
				add_log(Tx.t("hud.obtained") % [ContentDB.item_name(str(p.item)), int(p.count)], UiKit.quality_color(str(p.get("quality", "common"))))
			# A piece better than the one worn (or for an empty slot): the equip prompt offers it (EquipPrompt).
			if str(p.get("actor", "")) == Game.active_id and shown("bag"): equip_prompt.offer(p)
		"currency_changed":
			if int(p.get("delta", 0)) > 0 and shown("system_log") and str(p.get("source", "")) != "sell":
				add_log("+%d %s" % [int(p.delta), ContentDB.text("currency." + str(p.currency))], UiKit.PALE_GOLD)
		"system_unlocked":
			if p.get("toast", true) and str(p.get("label", "")) != "": toast(Tx.t("hud.new") + str(p.label))
		"secret_art_learned":
			# S43: the first time a movement art is usable, its name and a one-line how-to.
			var art := ContentDB.entry("secret_arts", str(p.get("art", "")))
			if str(p.get("actor", "")) == Game.active_id and not art.is_empty():
				toast(Tx.t("hud.new_art") + str(art.get("name", "")), "unlock", str(art.get("how_to", "")))
		"hud_element_revealed":
			pulses[str(p.element)] = 1.2
		"quest_accepted":
			toast(Tx.t("hud.quest") + str(p.get("name", "")), "quest", _first_step(str(p.get("quest", ""))))
		"quest_completed":
			# What the hand-in took from the bag, under the quest's name: "Gave 5 Willow Moss".
			toast(Tx.t("hud.completed") + str(p.get("name", "")), "quest", Tx.t("hud.gave") % p.gave if str(p.get("gave", "")) != "" else "")
		"objective_progressed":
			if str(p.get("actor", "")) == Game.active_id: _objective_toast(str(p.get("quest", "")))
		"room_entered":
			var room := ContentDB.room(str(p.room))
			var zone := ContentDB.zone_of_room(str(p.room))
			banner = {"text": str(room.get("name", "")), "sub": str(room.get("region_name", zone.get("name", ""))), "t": 0.0}
			channel.object = ""
			# S17: a room's hazards and the attribute that answers them, once per entry.
			for hz in HazardRules.summary(Game.active(), room):
				add_log(Tx.t("hud.hazard") % [hz.name, Tx.t("ui.cultivation." + str(hz.stat)), int(hz.need), int(hz.have)],
					UiKit.BRIGHT_JADE if hz.answered else UiKit.PALE_GOLD)
		"bottleneck_reached":
			toast(Tx.t("hud.bottleneck_tap_cultivate_to_break") if not p.get("major", false) else Tx.t("hud.bottleneck_reached_see_the_cultivation"), "gold")
		"breakthrough_failed":
			add_log(Tx.t("hud.breakthrough_failed") + ContentDB.text("failure." + str(p.failure_id)), UiKit.RED_TEXT)
		"achievement_unlocked":
			toast(Tx.t("hud.achievement") + str(p.get("name", "")), "gold")
		"talisman_crafted":
			if p.get("spoiled", false): add_log(Tx.t("hud.talisman_spoiled"), UiKit.MIST)
		"talisman_used":
			if str(p.get("kind", "")) == "movement": add_log(Tx.t("hud.talisman_used") % ContentDB.item_name(str(p.get("item", ""))), UiKit.PALE_GOLD)
		"relic_restored":
			toast(Tx.t("hud.relic_restored") % ContentDB.item_name(str(p.get("item", ""))), "gold")
		"natal_grew":
			if int(p.get("level", 0)) > 0: add_log(Tx.t("hud.natal_grew") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("level", 0))], UiKit.GOLD)
		"natal_broken":
			toast(Tx.t("hud.natal_broken") % ContentDB.item_name(str(p.get("item", ""))), "danger")
		"item_blooded":
			add_log(Tx.t("hud.item_blooded") % ContentDB.item_name(str(p.get("item", ""))), UiKit.MIST)
		"loadout_swapped":
			add_log(Tx.t("hud.loadout_swapped") % ContentDB.item_name(str(p.get("weapon", ""))), UiKit.PALE_GOLD)
		"sword_released":
			if int(p.get("swarm", 0)) > 0: add_log(Tx.plural("hud.sword_swarm", int(p.swarm)) % int(p.swarm), UiKit.PALE_GOLD)
			else: add_log(Tx.t("hud.sword_released"), UiKit.PALE_GOLD)
		"sword_returned":
			if str(p.get("reason", "")) != "recalled": add_log(Tx.t("hud.swarm_returned" if p.get("swarm", false) else "hud.sword_returned"), UiKit.MIST)
		"sect_role_chosen":
			if str(p.get("actor", "")) == Game.active_id:
				add_log(Tx.t("hud.sect_role_chosen") % str(ContentDB.entry("sect_roles", str(p.sect)).get("variants", {}).get(str(p.role), {}).get("name", "")), UiKit.PALE_GOLD)
		"sect_node_bought":
			if str(p.get("actor", "")) == Game.active_id:
				var br := TrainingSectAuthority.tree_branch(str(p.branch))
				var nodes: Array = br.get("nodes", [])
				var ni := int(p.node) - 1
				add_log(Tx.t("hud.sect_node_bought") % [str(br.get("name", {}).get(str(p.sect), p.branch)), str(nodes[ni].get("desc", "")) if ni >= 0 and ni < nodes.size() else ""], UiKit.PALE_GOLD)
		"path_changed":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.path_blood_on" if p.get("on", false) else "hud.path_blood_off"), UiKit.RED_TEXT)
		"illusion_cast":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.illusion_cast"), UiKit.SOUL_TEXT)
		"illusion_broken":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("reason", "")) in ["struck", "time"]: add_log(Tx.t("hud.illusion_broken"), UiKit.MIST)
		"soul_searched":
			if str(p.get("actor", "")) == Game.active_id:
				var mem := str(p.get("memory", ""))
				add_log(Tx.t("hud.soul_searched") % str(ContentDB.entry("codex", mem).get("title", "")) if mem != "" else Tx.t("hud.soul_searched_none"), UiKit.SOUL_TEXT)
		"melody_changed":
			if str(p.get("actor", "")) == Game.active_id and not p.get("on", false) and str(p.get("reason", "")) in ["composure", "broken"]:
				add_log(Tx.t("hud.melody_spent" if str(p.reason) == "composure" else "hud.melody_broken"), UiKit.MIST)
		"sword_intent_changed":
			if int(p.get("stacks", 0)) >= 10: add_log(Tx.t("hud.sword_intent_full"), UiKit.GOLD)
		"artifact_detonated":
			add_log(Tx.t("hud.detonated") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("targets", 0))], UiKit.RED_TEXT)
		"items_salvaged":
			add_log(Tx.plural("hud.salvaged", (p.get("items", []) as Array).size()) % (p.get("items", []) as Array).size(), UiKit.PALE_GOLD)
		"enhancement_inherited":
			add_log(Tx.t("hud.inherited") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("levels", 0))], UiKit.PALE_GOLD)
		"path_above_found":
			toast(Tx.t("hud.path_above") % [int(p.get("found", 1)), int(p.get("total", 1))], "gold")
		"mail_received":
			if Unlocks.is_unlocked(Game.active_id, "mail"): add_log(Tx.t("hud.a_letter_arrived"), UiKit.PALE_GOLD)
		"bag_full":
			add_log(Tx.t("hud.your_gourd_is_full"), UiKit.RED_TEXT)
		"system_log":
			add_log(str(p.text), UiKit.PAPER)
		"portal_blocked":
			# A shut way says why once, on its own plate at the way (WorldShared.request_portal lights it), not again in the
			# log (the prototype's QA saw "The road beyond is still being drawn." three times at once at the gate). A way with
			# no plate in view logs it, once while it repeats.
			var said := str(p.get("text", ""))
			if said == "" or _way_plate(str(p.get("portal", ""))): pass
			elif not log_lines.is_empty() and str(log_lines[-1].text) == said and float(log_lines[-1].t) < 5.0: log_lines[-1].t = 0.0
			else: add_log(said, UiKit.MIST)
		"field_boss_spawned", "elite_spawned":
			var def := ContentDB.entry("enemies", str(p.def))
			toast(Tx.t("hud.appears") % str(def.get("name", "")), "danger")
		"injury_added":
			add_log(Tx.t("hud.injury_severity") % [str(p.kind).capitalize(), int(p.severity)], UiKit.RED_TEXT)
		"aptitude_revealed":
			toast(Tx.t("hud.aptitude_revealed") % str(p.aptitude).replace("_", " ").capitalize(), "gold")
		"craft_completed":
			add_log(Tx.t("hud.crafted") % [ContentDB.name_of("recipes", str(p.recipe)), str(p.quality).capitalize()], UiKit.quality_color(str(p.quality)))
			if str(p.quality).begins_with("pill_"): toast(Tx.t("hud.rare_pill") % str(p.quality).capitalize(), "gold")
		"player_gravely_wounded":
			_buzz(200)
		"pets_bred":
			toast(Tx.t("hud.pets_bred") % UiKit.span(float(p.get("hours", 24.0)) * 3600.0), "gold")
		"treasure_planted":
			toast(Tx.t("hud.treasure_planted"), "gold")
		"treasure_harvested":
			toast(Tx.t("hud.treasure_harvested") % ContentDB.item_name(str(p.get("item", ""))), "gold")
		"natural_treasure_used":
			toast(Tx.t("hud.treasure_used." + str(p.treasure)), "gold")
		"treasure_used":
			if p.has("charges"): add_log(Tx.plural("hud.talisman_charges", int(p.charges)) % int(p.charges) if int(p.charges) > 0 else Tx.t("hud.talisman_spent"), UiKit.PALE_GOLD)
		# Gap report G1: the heart, the ledger, the flames and debts that come due.
		"heart_demon_changed":
			if str(p.get("source", "")) == "merit_milestone" and str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.merit_milestone") % int(p.value), UiKit.GOLD)
			if p.get("step_crossed", false):
				if float(p.get("delta", 0)) > 0: toast(Tx.t("hud.heart_demons_stir") % int(p.value), "danger")
				else: add_log(Tx.t("hud.heart_demons_calm"), UiKit.BRIGHT_JADE)
		"merit_changed":
			if int(p.get("delta", 0)) > 0: add_log(Tx.t("hud.merit_gained") % int(p.delta), UiKit.PALE_GOLD)
		"sin_changed":
			if int(p.get("delta", 0)) > 0: add_log(Tx.t("hud.sin_gained") % int(p.delta), UiKit.RED_TEXT)
		# S49: alignment and Fame; a young master's challenge opens the Fame tab, where it is answered.
		"alignment_changed":
			if p.get("word_changed", false): toast(Tx.t("hud.alignment_now") % Tx.t("ui.relations.align_" + str(p.word)), "gold")
		"fame_changed":
			if p.get("tier_up", false): toast(Tx.t("hud.fame_tier") % Tx.t("ui.relations.fame_" + str(p.tier)), "unlock")
			elif int(p.get("delta", 0)) < 0: add_log(Tx.t("hud.fame_lost") % -int(p.delta), UiKit.MIST)
			elif int(p.get("delta", 0)) > 0: add_log(Tx.t("hud.fame_gained") % int(p.delta), UiKit.PALE_GOLD)
		"affinity_changed":
			if p.get("heart_up", false): toast(Tx.plural("hud.heart_up", int(p.hearts)) % [ContentDB.name_of("npcs", str(p.npc)), int(p.hearts)], "gold")
		"bond_formed":
			toast(Tx.t("hud.bond_" + str(p.kind)) % ContentDB.name_of("npcs", str(p.npc)), "unlock")
		"grudge_changed":
			var fname := ContentDB.name_of("factions", str(p.faction))
			if p.get("hunted", false) and int(p.get("delta", 0)) > 0: toast(Tx.t("hud.grudge_hunted") % fname, "danger")
			elif int(p.get("value", 0)) == 0: add_log(Tx.t("hud.grudge_settled") % fname, UiKit.BRIGHT_JADE)
			elif int(p.get("delta", 0)) > 0: add_log(Tx.t("hud.grudge_rises") % fname, UiKit.RED_TEXT)
		"hunter_dispatched":
			toast(Tx.t("hud.hunter_found_you") % ContentDB.name_of("enemies", str(p.enemy)), "danger")
		"bounty_taken":
			add_log(Tx.t("hud.bounty_taken") % [ContentDB.name_of("enemies", str(p.bounty)), ContentDB.name_of("rooms", str(p.room))], UiKit.PALE_GOLD)
		"bounty_claimed":
			toast(Tx.t("hud.bounty_claimed") % [ContentDB.name_of("enemies", str(p.bounty)), int(p.reward)], "gold")
		"foe_surrendered":
			if str(p.get("actor", "")) == Game.active_id: open_page.emit("mercy", {"enemy": int(p.enemy), "def": str(p.def)})
		"foe_judged":
			add_log(Tx.t("hud.foe_spared") % ContentDB.name_of("enemies", str(p.def)) if p.get("spared", false) else Tx.t("hud.foe_killed") % ContentDB.name_of("enemies", str(p.def)), UiKit.MIST)
		# S49 world calendar: what is under way, what is coming (a notification a day ahead), season and weather.
		"world_event_started":
			var ev := CalendarRules.event(str(p.event))
			var where := str(p.get("room", ""))
			if str(p.event) == "gathering_trial" and Game.active() != null: where = Game.calendar.trial_room(Game.active())   # your sect's terraces
			if world_news(where if where != "" else _event_room(ev)):
				toast(Tx.t("hud.world_event_started") % str(ev.get("name", p.event)), "gold", ContentDB.name_of("rooms", where) if where != "" else "")
		"world_event_ended":
			var ev3 := CalendarRules.event(str(p.event))
			if world_news(_event_room(ev3)): add_log(Tx.t("hud.world_event_ended") % str(ev3.get("name", p.event)), UiKit.MIST)
		"world_event_scheduled":
			var ev2 := CalendarRules.event(str(p.event))
			if world_news(str(p.get("room", "")) if str(p.get("room", "")) != "" else _event_room(ev2)):
				Notifier.schedule("world_event", str(ev2.get("name", p.event)), str(ev2.get("desc", "")), float(p.start))
		"season_changed":
			if world_news(): toast(Tx.t("hud.season_changed") % ContentDB.name_of("seasons", str(p.season)), "gold")
		"weather_changed":
			if Game.room_rt != null and str(Game.room_rt.def.get("weather", "")) == str(p.region):
				add_log(Tx.t("hud.weather_" + str(p.weather)), UiKit.MIST)
		"treasure_birth_announced":
			if world_news(str(p.room)) or (Game.room_rt != null and Game.room_rt.room_id == str(p.room)):
				add_log(Tx.t("hud.treasure_birth") % [ContentDB.item_name(str(p.item)), ContentDB.name_of("rooms", str(p.room))], UiKit.PALE_GOLD)
		"treasure_claimed":
			toast(Tx.t("hud.treasure_claimed") % ContentDB.item_name(str(p.item)), "gold")
		# S28 v1.2 the Hollow Tide at full: control lost for a moment, allies turned.
		"hollow_seizure":
			if str(p.get("actor", "")) == Game.active_id:
				toast(Tx.t("hud.hollow_seizure"), "quest", Tx.t("hud.hollow_seizure_turned") % int(p.get("turned", 0)) if int(p.get("turned", 0)) > 0 else Tx.t("hud.hollow_seizure_sub"))
		# S50 Keeping Post: a post taken or left, a craft level, a pouch sewn, incense burned.
		"post_taken":
			if str(p.get("actor", "")) == Game.active_id:
				var what := Tx.t("hud.vigil") if str(p.craft) == "vigil" else str(ContentDB.entry("posts", str(p.craft)).get("short", ""))
				add_log(Tx.t("hud.post_taken") % what, UiKit.BRIGHT_JADE)
		"post_left":
			if str(p.get("reason", "")) == "walked": add_log(Tx.t("hud.post_left") % str(Game.character(str(p.actor)).name if Game.character(str(p.actor)) else ""), UiKit.MIST)
		"craft_leveled":
			if str(p.get("actor", "")) == Game.active_id:
				toast(Tx.t("hud.craft_level") % [str(ContentDB.entry("posts", str(p.craft)).get("name", "")), int(p.level)], "gold", Tx.t("hud.craft_level_sub"))
		"pouch_sewn":
			add_log(Tx.t("hud.pouch_sewn") % UiKit.fmt(int(float(p.get("cap", 0.0)))), UiKit.PALE_GOLD)
		"leaf_found":
			if p.get("new_tier", false): toast(Tx.t("hud.leaf_tier") % [ContentDB.name_of("enemies", str(p.enemy)), int(p.tier)], "gold", Tx.t("hud.leaf_sub"))
		"snare_collected":
			if str(p.get("actor", "")) == Game.active_id:
				var n := 0
				for id in p.get("items", {}): n += int(p.items[id])
				add_log(Tx.t("hud.snare_caught") % n if n > 0 else Tx.t("hud.snare_empty"), UiKit.PALE_GOLD if n > 0 else UiKit.MIST)
		"rite_held":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.rite_held") % int(p.wave), "gold", Tx.plural("hud.rite_wisps", int(p.wisps)) % int(p.wisps))
		"post_vow_learned":
			add_log(Tx.t("hud.post_vow_learned") % str(Game.posts.post_vow(str(p.vow)).get("name", "")), UiKit.PALE_GOLD)
		"incense_burned":
			add_log(Tx.t("hud.incense_burned") % UiKit.span(float(p.get("hours", 0.0)) * 3600.0), UiKit.PALE_GOLD)
		# S28 v1.2 Presence: held or let go, a new level, and two Presences meeting.
		"presence_toggled":
			if str(p.get("actor", "")) == Game.active_id:
				var why := str(p.get("reason", "choice"))
				if p.get("on", false): add_log(Tx.t("hud.presence_on") % int(p.get("level", 1)), UiKit.PALE_GOLD)
				elif why == "soul": add_log(Tx.t("hud.presence_soul"), UiKit.RED_TEXT)
				else: add_log(Tx.t("hud.presence_off"), UiKit.MIST)
		"presence_leveled":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.presence_level") % int(p.level), "gold", Tx.t("hud.presence_level_sub"))
		"presence_clash":
			if str(p.get("actor", "")) == Game.active_id:
				add_log(Tx.t("hud.presence_clash_" + str(p.get("winner", "even"))) % str(p.get("name", "")), UiKit.GOLD if str(p.get("winner", "")) == "you" else UiKit.RED_TEXT)
		"sphere_toggled":
			if str(p.get("actor", "")) == Game.active_id:
				var sw := str(p.get("reason", ""))
				if p.get("on", false): add_log(Tx.t("hud.sphere_domain") if p.get("domain", false) else Tx.t("hud.sphere_on") % Tx.t("hud.el_" + str(p.get("element", "none"))), UiKit.PALE_GOLD)
				elif sw == "broken": toast(Tx.t("hud.sphere_broken"), "danger", Tx.t("hud.sphere_broken_sub"))
				elif sw == "qi": add_log(Tx.t("hud.sphere_qi"), UiKit.RED_TEXT)
				else: add_log(Tx.t("hud.sphere_off"), UiKit.MIST)
		"sphere_clash":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("winner", "")) == "you":
				toast(Tx.t("hud.sphere_clash_won") % str(p.get("name", "")), "gold", Tx.t("hud.sphere_clash_won_sub"))
		"presence_clash_ended":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.presence_clash_end"), UiKit.MIST)
		# v1.2 Phase D: the Copperjaw swarm and the lantern defence.
		"swarm_released":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.plural("hud.swarm_released", int(p.get("pop", 0))) % int(p.get("pop", 0)), UiKit.PALE_GOLD)
		"swarm_returned":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.swarm_returned"), UiKit.MIST)
		"swarm_queen":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.swarm_queen"), "gold", Tx.t("hud.swarm_queen_sub"))
		"swarm_fed":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.swarm_fed") % UiKit.span(float(p.get("food", 0)) * 3600.0), UiKit.MIST)
		"lantern_light":
			if str(p.get("actor", "")) == Game.active_id and float(p.get("light", 100.0)) <= 30.0 and int(p.get("near", 0)) > 0:
				add_log(Tx.t("hud.lantern_guttering"), UiKit.RED_TEXT)
		# S43 rule 15: the rooftop thief and the Cloud Steps.
		"chase_started":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.chase_started"), "quest", Tx.t("hud.chase_hint"))
		"thief_caught":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.thief_caught") % float(p.get("seconds", 0.0)), "gold")
		"thief_escaped":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.thief_escaped"), "quest")
		"route_started":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.route_started"), "quest", Tx.plural("hud.route_hint", int(p.get("limit", 60))) % int(p.get("limit", 60)))
		"route_finished":
			if str(p.get("actor", "")) != Game.active_id: pass
			elif not p.get("finished", false): toast(Tx.t("hud.route_failed"), "quest")
			else:
				var medal := str(p.get("medal", ""))
				toast(Tx.t("hud.route_finished") % [float(p.seconds), int(p.rank), int(p.of)], "gold" if medal != "" else "quest",
					Tx.t("hud.route_medal_" + medal) if medal != "" else Tx.t("hud.route_best") % float(p.best))
		"gathering_trial_ranked":
			toast(Tx.plural("hud.trial_ranked", int(p.points)) % [int(p.rank), int(p.of), int(p.points)], "gold" if int(p.rank) <= 3 else "quest")
		"rift_opened":
			toast(Tx.t("hud.rift_opened") % int(p.level), "danger", Tx.t("hud.rift_hint"))
		"young_master_challenge":
			if str(p.get("actor", "")) == Game.active_id:
				toast(Tx.t("hud.jealous_senior") if str(p.get("enemy", "")) == "jealous_senior" else Tx.t("hud.young_master"), "quest")
				open_page.emit("relations", {"tab": "fame"})
		"tower_floor_cleared":
			if str(p.get("actor", "")) == Game.active_id:
				toast(Tx.t("hud.tower_cleared") % int(p.floor), "gold", Tx.t("hud.tower_first") if p.get("first", false) else "")
		"tower_swept":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.plural("hud.tower_swept", int(p.floors)) % int(p.floors), UiKit.PALE_GOLD)
		"activity_chest_ready":
			toast(Tx.plural("hud.activity_ready", int(p.points)) % int(p.points), "gold", Tx.t("hud.activity_ready_hint"))
		"activity_chest_claimed":
			add_log(Tx.plural("hud.activity_claimed", int(p.points)) % int(p.points), UiKit.PALE_GOLD)
		"collection_seal_ready":   # decision 27
			toast(Tx.t("hud.seal_ready") % [Tx.t("ui.codex.page_" + str(p.page)), Tx.t("ui.codex.seal_%d" % int(p.seal))], "gold", Tx.t("hud.seal_ready_hint"))
		"collection_seal_claimed":
			toast(Tx.t("hud.seal_claimed") % [Tx.t("ui.codex.page_" + str(p.page)), Tx.t("ui.codex.seal_%d" % int(p.seal))], "gold",
				UiKit.seal_gift(ContentDB.collection_seal(str(p.page), int(p.seal))))
		"ranking_changed":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("beaten", "")) != "":
				toast(Tx.t("hud.rank_climbed") % str(ContentDB.entry("rankings", str(p.beaten)).get("name", "")), "gold")
			elif str(p.get("actor", "")) == "" and world_news():
				add_log(Tx.t("hud.ranking_shifts"), UiKit.MIST)
		"favour_changed":
			if str(p.get("actor", "")) == Game.active_id:
				if p.get("tier_up", false): toast(Tx.t("hud.favour_tier") % Tx.t("ui.county.tier_" + str(p.tier)), "gold")
				elif int(p.get("delta", 0)) > 0: add_log(Tx.t("hud.favour_up") % int(p.delta), UiKit.PALE_GOLD)
		"relief_donated":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.relief_given") % UiKit.fmt(int(p.silver)), UiKit.PALE_GOLD)
		# S49 territory: the spirit-stone mines (account level: every character hears of them).
		"mine_claimed":
			toast(Tx.t("hud.mine_claimed") % ContentDB.name_of("territory", str(p.mine)), "gold", Tx.t("hud.mine_claimed_sub"))
		"mine_contested":
			var mname := ContentDB.name_of("territory", str(p.mine))
			var rname := str(Game.sect.rival(str(p.sect)).get("name", ""))
			toast(Tx.t("hud.mine_contested") % [rname, mname], "danger", Tx.t("hud.mine_contested_sub") % UiKit.span(float(p.until) - Clock.now_utc()))
			Notifier.schedule("defence", Tx.t("hud.mine_notify_title"), Tx.t("hud.mine_contested") % [rname, mname], Clock.now_utc())
		"mine_defended":
			var dname := ContentDB.name_of("territory", str(p.mine))
			toast(Tx.t("hud.mine_held_you") % dname if str(p.get("by", "")) == "you" else Tx.t("hud.mine_held_guards") % dname, "gold")
		"mine_lost":
			toast(Tx.t("hud.mine_lost") % [str(Game.sect.rival(str(p.sect)).get("name", "")), ContentDB.name_of("territory", str(p.mine))], "danger",
				Tx.plural("hud.mine_lost_sub", int(p.stones)) % int(p.stones) if int(p.get("stones", 0)) > 0 else "")
		"mine_collected":
			add_log(Tx.plural("hud.mine_collected", int(p.stones)) % [int(p.stones), ContentDB.name_of("territory", str(p.mine))], UiKit.PALE_GOLD)
		"pet_commanded":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.pet_commanded") % Tx.t("hud.pet_cmd_" + str(p.command)), UiKit.PALE_GOLD)
		"guqin_played":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.guqin_calm") % int(round(float(p.bonus) * 100.0)), UiKit.BRIGHT_JADE)
		"chess_solved":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.chess_right") if p.get("right", false) else Tx.t("hud.chess_wrong"), UiKit.PALE_GOLD if p.get("right", false) else UiKit.MIST)
		"auto_hunt_changed":
			if str(p.get("actor", "")) == Game.active_id:
				var why := str(p.get("reason", ""))
				if p.get("on", false): add_log(Tx.t("hud.auto_hunt_on"), UiKit.BRIGHT_JADE)
				elif why not in ["off", "path"]: add_log(Tx.t("sim.world.auto_hunt_" + why), UiKit.MIST)
				else: add_log(Tx.t("hud.auto_hunt_off"), UiKit.MIST)
		"auto_path_started":
			# Decision 43: a walk to a place names the place ("the Storehouse"), else the room.
			var dest := str(p.get("name", "")) if str(p.get("name", "")) != "" else ContentDB.name_of("rooms", str(p.target))
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.auto_path_to") % dest, UiKit.PALE_GOLD)
		"auto_path_ended":
			if str(p.get("actor", "")) == Game.active_id and str(p.get("reason", "")) != "cancelled":
				add_log(Tx.t("hud.auto_path_" + str(p.get("reason", "arrived"))), UiKit.PALE_GOLD if str(p.get("reason", "")) == "arrived" else UiKit.MIST)
		"fortune_encounter":
			if str(p.get("actor", "")) == Game.active_id:
				var card := ContentDB.entry("fortune_deck", str(p.card))
				vignette = {"title": str(card.get("name", "")), "text": str(card.get("text", "")), "t": 0.0}   # the fortune_card moment sounds it
		"heavenly_phenomenon":
			if str(p.get("actor", "")) == Game.active_id:
				add_log(Tx.t("hud.phenomenon_" + str(p.get("kind", "cloud"))), UiKit.PALE_GOLD)
		"item_used":
			# A consumable names what it did (UiKit.use_parts): "Herbal Tea: +120 HP over 5 s". It reaches the player before
			# the log is revealed too (the prologue's tea), and the bars it touched flash.
			if str(p.get("actor", "")) == Game.active_id:
				var parts := UiKit.use_parts(p.get("effects", []), p.get("gains", {}))
				if not parts.is_empty():
					var words := PackedStringArray()
					for part in parts: words.append(str(part.text))
					add_log(Tx.t("hud.use.line") % [ContentDB.item_name(str(p.get("item", ""))), " · ".join(words)], parts[0].color, true)
					for part in parts:
						if part.has("pool"): pulses["bar:" + str(part.pool)] = 0.8
		"draught_expired":
			toast(Tx.t("hud.draught_expired") % ContentDB.item_name(str(p.get("item", ""))), "danger")
		"flame_absorbed":
			toast(Tx.t("hud.flame_absorbed") % ContentDB.item_name(str(p.flame)), "gold")
		"recipe_page_found":
			toast(Tx.t("hud.recipe_page") % [ContentDB.name_of("recipes", str(p.recipe)), int(p.held), int(p.total)], "gold")
		"recipe_deduced":
			if p.get("success", false): toast(Tx.t("hud.recipe_deduced") % ContentDB.name_of("recipes", str(p.recipe)), "unlock")
			else: toast(Tx.t("hud.recipe_not_deduced") % ContentDB.name_of("recipes", str(p.recipe)), "danger")
		"experiment_result":
			var res := str(p.get("result", ""))
			if res.begins_with("learned:"): toast(Tx.t("hud.experiment_found") % ContentDB.name_of("recipes", res.trim_prefix("learned:")), "unlock")
			elif res == "murky": add_log(Tx.t("hud.experiment_murky"), UiKit.MIST)
		"guild_exam_started":
			toast(Tx.t("hud.exam_started") % UiKit.span(float(p.get("time_s", 0))), "gold")
		"guild_exam_failed":
			toast(Tx.t("hud.exam_failed"), "danger")
		"commission_completed":
			add_log(Tx.plural("hud.commission_paid", int(p.get("paid", 0))) % int(p.get("paid", 0)) + (" " + Tx.t("hud.commission_capped") if p.get("capped", false) else ""), UiKit.PALE_GOLD)
		"pill_tribulation_result":
			if str(p.after) != str(p.before): toast(Tx.t("hud.tribulation_changed") % Tx.t("ui.quality." + str(p.after)), "gold" if str(p.after) == "pill_soul" else "danger")
			else: toast(Tx.t("hud.tribulation_held"), "gold")
		"pill_soul_flight":
			if not p.get("caught", false): add_log(Tx.t("hud.soul_escaped"), UiKit.MIST)
		"furnace_blast":
			toast(Tx.t("hud.furnace_blast") % int(p.get("durability", 0)), "danger")
		"debt_called":
			toast(Tx.t("hud.debt_" + str(p.debt)), "quest")
		"room_event_flawless":
			toast(Tx.t("hud.flawless") , "gold")
		"room_event_wave":
			if str(p.get("text", "")) != "": add_log(str(p.text), UiKit.PALE_GOLD)
		"room_event_failed":
			if str(p.get("reason", "")) != "": toast(Tx.t("hud.event_failed." + str(p.reason)), "danger")
		# S48: the body ladder, physiques and the core.
		"body_trial_passed":
			toast(Tx.t("hud.body_trial_passed") % [ContentDB.name_of("body_tiers", str(p.tier)), ContentDB.item_name(str(p.get("bath", "")))], "gold")
		"physique_awakened":
			toast(Tx.t("hud.physique_awakened") % ContentDB.name_of("physiques", str(p.physique)), "unlock")
		"core_graded":
			toast(Tx.t("hud.core_graded") % int(p.grade), "gold")
		"tribulation_bolt":
			if str(p.phase) == "strike":
				Audio.play("thunder")
				if p.get("absorbed", false): add_log(Tx.t("hud.bolt_absorbed"), UiKit.PALE_GOLD)
		"tribulation_result":
			if p.get("survived", false): toast(Tx.t("hud.tribulation_survived") % [int(p.bolts) - int(p.struck), int(p.bolts)], "gold")
			else: toast(Tx.t("hud.tribulation_failed"), "danger")
		"fate_offered":
			if str(p.get("actor", "")) == Game.active_id: open_page.emit("fates", {})
		"fate_chosen":
			toast(Tx.t("hud.fate_chosen") % ContentDB.name_of("fates", str(p.card)), "gold")
		"qi_deviation":
			toast(Tx.t("hud.qi_deviation"), "danger", Tx.t("hud.qi_deviation_sub"))
		"inner_art_learned":
			toast(Tx.t("hud.inner_art_learned") % ContentDB.name_of("inner_arts", str(p.art)), "unlock")
		"inner_art_equipped":
			if str(p.art) != "": add_log(Tx.t("hud.inner_art_worn") % ContentDB.name_of("inner_arts", str(p.art)), UiKit.PALE_GOLD)
		"stance_changed":
			add_log(Tx.t("hud.stance_on") % ContentDB.name_of("stances", str(p.stance)) if str(p.stance) != "" else Tx.t("hud.stance_off"), UiKit.PALE_GOLD)
		"vow_taken":
			add_log(Tx.t("hud.vow_taken") % ContentDB.name_of("vows", str(p.vow)), UiKit.PALE_GOLD)
		"vow_broken":
			toast(Tx.t("hud.vow_broken") % ContentDB.name_of("vows", str(p.vow)), "danger")
		"false_realm_changed":
			add_log(Tx.t("hud.false_realm") % ContentDB.realm_label(str(p.realm)) if str(p.realm) != "" else Tx.t("hud.true_realm"), UiKit.MIST)
		"epiphany":
			toast(Tx.t("hud.epiphany"), "gold", Tx.t("hud.epiphany_mastery") % ContentDB.name_of("techniques", str(p.technique)) if str(p.get("technique", "")) != "" else Tx.t("hud.epiphany_sub"))
		"boss_phase":
			if str(p.get("action", "")) == "self_detonate": toast(Tx.t("hud.self_detonate"), "danger", Tx.t("hud.self_detonate_sub"))
		"soul_escaped":
			toast(Tx.t("hud.soul_escaped_death"), "danger")
		"killing_intent_changed":
			if int(p.stacks) >= int(ContentDB.stat_const("killing_intent", {}).get("max", 10)): add_log(Tx.t("hud.killing_intent_full"), UiKit.RED_TEXT)
		"combo_landed":
			add_log(Tx.t("hud.combo") % [ContentDB.name_of("techniques", str(p.first)), ContentDB.name_of("techniques", str(p.second))], UiKit.GOLD)
		# Gap report G2: treasures and talismans.
		"beast_captured":
			add_log(Tx.t("hud.beast_captured") % str(ContentDB.entry("enemies", str(p.def)).get("name", "")), UiKit.PALE_GOLD)
		"treasure_set":
			if str(p.item) != "": add_log(Tx.t("hud.treasure_set") % [ContentDB.item_name(str(p.item)), int(p.slot) + 1], UiKit.PALE_GOLD)
		"pill_soul_awakened":
			toast(Tx.t("hud.pill_soul") % Tx.t("hud.pill_soul_effect." + str(p.effect)), "gold")
		# A spar is a lesson: an opponent with lines of their own (Shen Lian) says what it teaches as it starts and ends.
		"spar_started":
			var said := spar_line(str(p.get("opponent", "")), "start")
			if said != "": toast(Tx.t("hud.spar_begins"), "quest", said)
		"spar_ended":
			var won: bool = p.get("winner", "") == "player"
			toast(Tx.t("hud.spar_won") if won else Tx.t("hud.spar_lost_try_again"), "quest", spar_line(str(p.get("opponent", "")), "won" if won else "lost"))
		"quest_ready":
			# Only a quest that waits to be handed in says so (one that completes itself, like the fair, is done by now).
			if str(Game.active().quests.active.get(str(p.quest), {}).get("state", "")) == "ready":
				toast(Tx.t("hud.ready_to_hand_in") + str(Game.quest.quest_def(Game.active(), str(p.quest)).get("name", "")), "quest")
		"codex_entry_unlocked":
			add_log(Tx.t("hud.codex") + str(ContentDB.entry("codex", str(p.entry)).get("title", "")), UiKit.PALE_GOLD)
		"teleport_discovered":
			toast(Tx.t("hud.teleport_stone_attuned"), "gold")
		"hidden_portal_revealed":
			toast(Tx.t("hud.a_hidden_path_opens"), "gold")
		"herb_ripening":
			add_log(Tx.t("hud.herb_ripening") % ContentDB.item_name(str(p.item)), UiKit.GOLD)
		"herb_harvested":
			if p.get("perfect", false): add_log(Tx.plural("hud.herb_perfect", int(p.age)) % [ContentDB.item_name(str(p.item)), int(p.age)], UiKit.GOLD)
		"seed_found":
			toast(Tx.t("hud.seed_found") % ContentDB.item_name(str(p.seed)), "gold")
		"herb_planted":
			add_log(Tx.t("hud.herb_planted") % ContentDB.item_name(str(p.herb)), UiKit.BRIGHT_JADE)
		"bed_watered":
			add_log(Tx.t("hud.bed_watered") % int(float(p.progress) * 100.0), UiKit.BRIGHT_JADE)
		"bed_enriched":
			toast(Tx.t("hud.bed_enriched") % Tx.t("ui.garden.grade_" + str(p.grade)), "gold")
		"herb_aged":
			toast(Tx.plural("hud.herb_aged", int(p.age)) % [ContentDB.item_name(str(p.herb)), int(p.age)], "gold")
		"spring_bottled":
			add_log(Tx.t("hud.spring_bottled") % int(p.left), UiKit.BRIGHT_JADE)
		"pet_wounded":
			toast(Tx.t("hud.pet_wounded") % _pet_name(str(p.pet)), "danger", Tx.t("hud.pet_wounded_sub"))
		"pet_healed":
			add_log(Tx.t("hud.pet_healed") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
		"bloodline_awakened":
			if int(p.get("step", 1)) >= 2: toast(Tx.t("hud.bloodline_form") % [_pet_name(str(p.pet)), str(p.get("name", ""))], "unlock", Tx.t("hud.bloodline_form_sub"))
			else: toast(Tx.t("hud.bloodline_skill") % [_pet_name(str(p.pet)), str(p.get("name", ""))], "unlock", Tx.t("hud.bloodline_skill_sub"))
		"contract_formed":
			var ck := str(p.get("kind", "equal"))
			toast(Tx.t("hud.contract_formed_" + ck) % _pet_name(str(p.pet)), "unlock", Tx.t("hud.contract_formed_" + ck + "_sub"))
		"contract_offered":
			toast(Tx.t("hud.contract_offered") % _pet_name(str(p.pet)), "unlock", Tx.t("hud.contract_offered_sub"))
		"pet_skill_cast":
			add_log(Tx.t("hud.pet_skill_cast") % [_pet_name(str(p.pet)), str(p.get("skill", ""))], UiKit.PALE_GOLD)
		"beast_suppressed":
			add_log(Tx.t("hud.beast_suppressed") % [_pet_name(str(p.pet)), ContentDB.name_of("enemies", str(p.get("def", "")))], UiKit.MIST)
		"egg_infused":
			add_log(Tx.t("hud.egg_infused_" + str(p.get("kind", "blood"))), UiKit.BRIGHT_JADE)
		"party_changed":
			add_log(Tx.plural("hud.party_changed", int(p.get("count", 1))) % int(p.get("count", 1)), UiKit.MIST)
		"pet_skill_learned":
			var rep := str(p.get("replaced", ""))
			if rep != "": add_log(Tx.t("hud.pet_skill_replaced") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_skill_books", str(p.skill)), ContentDB.name_of("pet_skill_books", rep)], UiKit.PALE_GOLD)
			else: add_log(Tx.t("hud.pet_skill_learned") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_skill_books", str(p.skill))], UiKit.BRIGHT_JADE)
		"pets_fused":
			toast(Tx.t("hud.pets_fused") % _pet_name(str(p.keep)), "gold", Tx.t("hud.pets_fused_sub") % [(p.get("traits", []) as Array).size(), (p.get("skills", []) as Array).size(), int(p.get("purity", 0))])
		"pet_core_formed":
			toast(Tx.t("hud.pet_core_formed") % [_pet_name(str(p.pet)), str(Game.pets.core_grade_def(str(p.get("grade", ""))).get("name", ""))], "unlock", Tx.t("hud.pet_core_formed_sub"))
		"pet_breakthrough":
			if p.get("success", false): add_log(Tx.t("hud.pet_breakthrough_ok") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
			else: toast(Tx.t("hud.pet_breakthrough_fail") % _pet_name(str(p.pet)), "danger", Tx.t("hud.pet_breakthrough_" + ("heart" if str(p.get("lost", "")) == "heart" else "wound")))
		"pet_fed":
			if p.get("trough", false): add_log(Tx.t("hud.trough_fed") % _pet_name(str(p.pet)), UiKit.MIST)
		"arena_battle":
			if p.get("won", false): toast(Tx.t("hud.arena_won") % int(p.get("rank", 11)), "gold", "")
			else: add_log(Tx.t("hud.arena_lost"), UiKit.MIST)
		"arena_rewarded":
			toast(Tx.plural("hud.arena_rewarded", int(p.get("spirit_stone", 0))) % [int(p.get("rank", 11)), int(p.get("spirit_stone", 0))], "gold", "")
		"beast_trial_result":
			if p.get("won", false): toast(Tx.t("hud.trial_won"), "gold", ContentDB.item_name(str(p.get("item", ""))))
			else: toast(Tx.t("hud.trial_lost"), "danger", "")
		"pet_swapped":
			add_log(Tx.t("hud.pet_swapped") % _pet_name(str(p.pet)), UiKit.BRIGHT_JADE)
		"beast_king_spawned":
			toast(Tx.t("hud.beast_king_spawned") % ContentDB.name_of("enemies", str(p.get("king", ""))), "danger", Tx.t("hud.beast_king_spawned_sub"))
		"king_nest_opened":
			toast(Tx.t("hud.king_nest_opened"), "gold", Tx.t("hud.king_nest_opened_sub") % UiKit.span(float(p.get("minutes", 30)) * 60.0))
		"beast_tide_started":
			toast(Tx.t("hud.beast_tide_started"), "danger", Tx.plural("hud.beast_tide_started_sub", int(float(p.get("duration", 90)))) % int(float(p.get("duration", 90))))
		"beast_tide_result":
			if p.get("won", false): toast(Tx.t("hud.beast_tide_won"), "gold", Tx.t("hud.beast_tide_won_sub"))
		"pet_gear_changed":
			if str(p.get("item", "")) != "": add_log(Tx.t("hud.pet_gear") % [_pet_name(str(p.pet)), ContentDB.item_name(str(p.item))], UiKit.MIST)
		"core_devoured":
			add_log(Tx.t("hud.core_devoured") % [_pet_name(str(p.pet)), ContentDB.item_name(str(p.item)), int(float(p.xp))], UiKit.BRIGHT_JADE)
		"cores_sold":
			add_log(Tx.plural("hud.cores_sold", int(p.stones)) % [int(p.count), ContentDB.item_name(str(p.item)), int(p.stones)], UiKit.PALE_GOLD)
		"beast_cleansed":
			toast(Tx.t("hud.beast_cleansed") % ContentDB.name_of("enemies", str(p.def)), "gold", Tx.t("hud.beast_cleansed_sub"))
		"beast_subdued":
			add_log(Tx.t("hud.beast_subdued") % [ContentDB.name_of("enemies", str(p.def)), UiKit.span(float(p.seconds))], UiKit.GOLD)
		"garden_raided":
			toast(Tx.t("hud.raid_" + str(p.kind)) % ContentDB.item_name(str(p.herb)), "danger")
		"rack_started":
			add_log(Tx.t("hud.rack_started") % [int(p.count), ContentDB.item_name(str(p.herb)), UiKit.span(float(p.seconds))], UiKit.BRIGHT_JADE)
		"rack_collected":
			add_log(Tx.t("hud.rack_collected") % [int(p.count), ContentDB.item_name(str(p.herb)), Tx.t("ui.garden.done_" + str(p.kind))], UiKit.BRIGHT_JADE)
		"herb_appraised":
			if p.get("fake", false): toast(Tx.t("hud.herb_fake") % ContentDB.item_name(str(p.item)), "danger")
		"transplant_result":
			if p.get("ok", false): toast(Tx.t("hud.transplanted") % ContentDB.item_name(str(p.herb)), "gold", Tx.t("hud.transplanted_sub"))
			else: toast(Tx.t("hud.transplant_died") % ContentDB.item_name(str(p.herb)), "danger")
		"guardian_spawned":
			toast(Tx.t("hud.guardian") % ContentDB.name_of("enemies", str(p.enemy)), "danger", Tx.t("hud.guardian_sub"))
		"ambush_sprung":
			toast(Tx.t("hud.ambush"), "danger", Tx.t("hud.ambush_concealed") if p.get("concealed", false) else Tx.t("hud.ambush_sub"))
		"meridian_gate_opened":
			toast(Tx.t("hud.meridian_gate_opened") % str(p.get("channel", "")).replace("_", " ").capitalize(), "gold")
		"stability_changed":
			add_log(Tx.t("hud.your_foundation_is") % str(p.get("word", "")).to_lower(), UiKit.MIST)
		"overflow_mailed":
			add_log(Tx.t("hud.no_room_in_your_gourd"), UiKit.PALE_GOLD)
		"egg_hatched":
			toast(Tx.t("hud.the_egg_hatched_a") % ContentDB.name_of("pets", str(p.species)), "gold")
		"bond_changed":
			add_log(Tx.plural("hud.hearts", int(float(p.value))) % [_pet_name(str(p.pet)), int(float(p.value))], UiKit.RED_TEXT)
		"defence_warning":
			toast(Tx.t("hud.raiders_at_the_gates_hold"), "danger")
		"defence_result":
			toast(Tx.t("hud.the_raid_is_beaten_back") if p.get("won", false) else Tx.t("hud.the_raiders_broke_through"), "gold" if p.get("won", false) else "danger")
		"building_upgraded":
			add_log(Tx.t("hud.reached_level") % [ContentDB.name_of("sect_buildings", str(p.building)), int(p.level)], UiKit.PALE_GOLD)
		"prestige_gained":
			if Game.sect.founded(): add_log(Tx.t("hud.prestige") % int(p.amount), UiKit.PALE_GOLD)
		"expedition_returned":
			add_log(Tx.t("hud.expedition_to") % [ContentDB.name_of("expeditions", str(p.region)), Tx.t("hud.returned_with_spoils") if p.get("success", false) else Tx.t("hud.came_back_empty_handed")], UiKit.PALE_GOLD)
		"reputation_changed":
			add_log(Tx.t("hud.reputation") % [str(p.faction).replace("_", " ").capitalize(), int(p.value)], UiKit.MIST)
		"dismounted":
			if str(p.get("reason", "")) == "climb": add_log(Tx.t("hud.dismount_climb"), UiKit.MIST)
			else: add_log(Tx.t("hud.dismounted"), UiKit.RED_TEXT)
		"item_bound":
			toast(Tx.t("hud.item_bound") % ContentDB.item_name(str(p.item)), "gold")
		"binding_interrupted":
			add_log(Tx.t("hud.binding_broken"), UiKit.RED_TEXT)
		"artifact_spirit_awakened":
			toast(Tx.t("hud.spirit_awake") % ContentDB.item_name(str(p.item)), "gold")
		"spirit_affinity_changed":
			# S47: every tenth point of affinity, and the gifts, are worth a line.
			var aff := float(p.get("affinity", 0.0))
			if str(p.get("why", "")) != "use" or int(aff) % 10 == 0:
				add_log(Tx.t("hud.spirit_affinity") % [ContentDB.item_name(str(p.item)), int(aff)], UiKit.SOUL_TEXT)
		"artifact_spirit_grew":
			toast(Tx.t("hud.spirit_grew") % [ContentDB.item_name(str(p.item)), int(p.get("level", 0))], "gold")
		"artifact_spirit_spoke":
			add_log(Tx.t("hud.spirit_says") % [str(ContentDB.item(str(p.item)).get("spirit", {}).get("name", "")), str(p.get("line", ""))], UiKit.SOUL_TEXT)
		"artifact_skill_used":
			if p.get("awakened", false): add_log(Tx.t("hud.awakened_skill") % str(p.get("skill", "")), UiKit.GOLD)
			else: add_log(Tx.t("hud.spirit_skill") % str(p.get("skill", "")), UiKit.SOUL_TEXT)
		"trait_revealed":
			toast(Tx.t("hud.shows_a_trait") % [_pet_name(str(p.pet)), ContentDB.name_of("pet_traits", str(p.trait))], "gold")
		"pet_level_up":
			add_log(Tx.t("hud.reached_level") % [_pet_name(str(p.pet)), int(p.level)], UiKit.PALE_GOLD)
		"pet_retreated":
			add_log(Tx.t("hud.your_spirit_animal_retreats_into"), UiKit.MIST)
		"pet_returned":
			add_log(Tx.t("hud.your_spirit_animal_is_back"), UiKit.MIST)
		"companion_downed":
			add_log(Tx.t("hud.is_down") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.RED_TEXT)
		"companion_revived":
			add_log(Tx.t("hud.is_back_on_their_feet") % ContentDB.name_of("companions", str(p.get("companion", ""))), UiKit.MIST)
		"building_damaged":
			toast(Tx.t("hud.raiders_damaged_your_repair_it") % ContentDB.name_of("sect_buildings", str(p.building)), "danger")
		"zone_ceiling_reached":
			toast(Tx.t("hud.this_land_can_take_you"), "gold")
		"auction_bid_placed":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.auction_bid_placed") % [ContentDB.item_name(str(p.get("item", ""))), int(p.get("bid", 0))], UiKit.PALE_GOLD)
		"auction_outbid":
			if str(p.get("actor", "")) == Game.active_id: add_log(Tx.t("hud.auction_outbid") % ContentDB.item_name(str(p.get("item", ""))), UiKit.MIST)
		"auction_won":
			if str(p.get("actor", "")) == Game.active_id: toast(Tx.t("hud.auction_won") % ContentDB.item_name(str(p.get("item", ""))), "gold")

# ------------------------------------------------------------------ drawing
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

func skill_position(index: float) -> Vector2:
	var low := clampi(int(floor(index)), 0, 2)
	return slots[low].lerp(slots[low + 1], index - low)

## Decision 42: a technique as the Techniques tree's node picture (TechniquePicture), the card's miniature: the whole
## character at x1 in the art's pose in its element's ink, the form's mark beside it and its rank badge. Decision 43: a
## round button TILE px across (TechniquePicture.draw_round: an ink rim, the bright jade ring, the picture cut to the
## circle, the badge inside it). Closed (the weapon in hand cannot use it), a slate ring, the picture dim and a lock;
## cooling, the radial sweep (an ink pie from the top round, the ring dim over the part to wait) and its seconds, then a
## flash of the ring as it is ready again (READY_S); short of Qi, the picture dimmed and a Qi arc along its foot. An
## empty or locked slot is not drawn (G3).
func draw_skill_slot(center: Vector2, slot: int, opacity: float) -> void:
	var rad := TILE * 0.5
	if not bound():
		draw_circle(center, rad, Color(UiKit.INK, opacity))
		draw_arc(center, rad - 3.0, 0.0, TAU, 48, Color(UiKit.BRIGHT_JADE, opacity), TechniquePicture.RING - 1.0, true)
		draw_circle(center, rad - TechniquePicture.RING, Color(UiKit.JADE_SHADOW, opacity))
		return
	if not _slot_filled(slot): return
	var c = Game.active()
	var tid := str(c.cultivator.technique_slots[slot])
	var tdef := ContentDB.entry("techniques", tid)
	var fam := str(StatRules.family(c).get("id", "fists"))
	var closed: bool = str(tdef.get("family", "any")) != "any" and not (str(tdef.family) == fam or (str(tdef.family) == "fists" and fam == "gauntlets"))
	var cd: float = c.pools.cooldown("tech:" + tid)
	var cost: float = Game.combat.technique_cost(c, tdef)
	var short: bool = not closed and cd <= 0.0 and c.pools.max_qi > 0 and c.pools.qi < cost
	var frame := UiKit.HOLLOW if closed else UiKit.BRIGHT_JADE
	TechniquePicture.draw_round(self, center, rad, tid, c, _look(c), frame, 0.45 if closed else (0.72 if short else 1.0), opacity, "hud")
	if closed: TechniquePicture.draw_lock_round(self, center, rad, opacity)
	if cd > 0.0:
		_cooling[tid] = true
		TechniquePicture.draw_cooldown_round(self, center, rad, cd / maxf(0.1, float(tdef.get("cooldown_s", 5))), cd, opacity)
	else:
		if _cooling.has(tid):
			_cooling.erase(tid)
			_ready_at[tid] = t
		if short: TechniquePicture.draw_qi_short_round(self, center, rad, c.pools.qi / maxf(1.0, cost), opacity)
		var since := t - float(_ready_at.get(tid, -99.0))
		if since < READY_S and not closed: TechniquePicture.draw_ready_round(self, center, rad, since / READY_S, opacity, UiKit.reduce_motion())

## Decision 43: the arts seen cooling, and when each was ready again (the HUD's clock), for the ready flash.
var _cooling := {}
var _ready_at := {}

## The character's look for the techniques' pictures, found once a frame.
var _look_now := FrameMemo.new(1, false)
func _look(c) -> Dictionary:
	return _look_now.value(null, func(): return InventoryAuthority.outfit_for(c))

## A cooldown's dark sweep over a ring's face, `frac` of the way round from the top.
func _sweep(center: Vector2, r: float, frac: float, opacity := 1.0) -> void:
	if frac <= 0.02: return
	var pts := PackedVector2Array([center])
	for i in 25: pts.append(center + Vector2.from_angle(-PI / 2 + TAU * frac * (i / 24.0)) * r)
	draw_colored_polygon(pts, Color(UiKit.INK, 0.6 * opacity))

## The techniques of the page on ring 1, at rest as in a fight (decision 42). A page turn slides both pages along the
## arc.
func draw_skill_scroll() -> void:
	if scroll_progress >= 1:
		for i in slots.size():
			var slot := i + skill_page * 4
			if bound() and not _slot_filled(slot): continue
			draw_skill_slot(slots[i], slot, 1.0)
		return
	var tt := scroll_progress * scroll_progress * (3 - 2 * scroll_progress)
	var shift := -scroll_direction * 4.0 * tt
	var old_page := (skill_page + 1) % 2
	for page in 2:
		for i in 4:
			var index := i + shift + (scroll_direction * 4 if page == 1 else 0)
			if index < -0.35 or index > 3.35: continue
			var fade := minf(clampf((index + 0.35) / 0.35, 0, 1), clampf((3.35 - index) / 0.35, 0, 1))
			draw_skill_slot(skill_position(index), i + (old_page if page == 0 else skill_page) * 4, fade)

func bar(r: Rect2, frac: float, fill: Color, label: String, value_text: String, ahead := 0.0, flash := 0.0) -> void:
	draw_rect(r.grow(2), UiKit.INK)
	draw_rect(r, UiKit.BAR_TROUGH)
	if ahead > 0.0 and frac < 1.0:
		var a0 := r.size.x * clampf(frac, 0, 1)
		draw_rect(Rect2(r.position + Vector2(a0, 0), Vector2(r.size.x * clampf(frac + ahead, 0, 1) - a0, r.size.y)), Color(UiKit.BRIGHT_JADE, 0.45))
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0, 1), r.size.y)), fill)
	# A consumable just touched this pool (item_used): the frame glows jade for a moment, full or not.
	if flash > 0.0: draw_rect(r.grow(2), Color(UiKit.BRIGHT_JADE, clampf(flash / 0.8, 0.0, 1.0)), false, 2.0)
	draw_line(r.position + Vector2(1, 2), r.position + Vector2(maxf(1, r.size.x * clampf(frac, 0, 1) - 1), 2), Color(UiKit.PALE_GOLD, 0.35), 2)
	UiKit.draw_text(self, label, r.position + Vector2(-34, 12), 14, UiKit.HUD_LABEL, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	UiKit.draw_outlined(self, value_text, r.position + Vector2(0, r.size.y * 0.5 + 5), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func _draw():
	if not is_instance_valid(player): return
	if not bound():
		_draw_legacy()
		return
	var c = Game.active()
	tracker_rect = Rect2()
	tracker_paths = []
	_draw_player_panel(c)
	_draw_points(c)
	_draw_party(c)
	if shown("quest_tracker"): _draw_tracker(c)
	if shown("minimap") and Game.account.settings.get("minimap", true) and (not is_instance_valid(world) or world.get("hud_minimap") != false): _draw_minimap(c)
	_draw_icon_row(c)
	# S49 auto-hunt: a small toggle, only in rooms where idle Hunt is allowed.
	if _auto_hunt_shown(c):
		var on: bool = Game.world.auto_hunting(c.id)
		ring(auto_center, 26, on)
		if on: draw_arc(auto_center, 29, fmod(t * 3.0, TAU), fmod(t * 3.0, TAU) + PI * 1.2, 24, UiKit.GOLD, 3.0)
		glyph("jian", auto_center + Vector2(0, -4), 32)
		UiKit.draw_outlined(self, Tx.t("hud.auto_hunt"), auto_center + Vector2(-40, 23), 14, UiKit.GOLD if on else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 80)
	purse_rect = Rect2()
	if shown("currency") and not _boss_arena(): _draw_purse()
	_draw_controls(c)
	if shown("progress_bar"): _draw_progress(c)
	_draw_log()
	_draw_boss()
	_draw_top_stack(c)
	equip_prompt.draw(self, Game.account.settings.get("reduce_motion", false))
	_draw_pet_wheel(c)
	# The harvest ring (S45) sits over every other control while it runs.
	if tapping.object != "": _draw_tap_ring()
	for k in ["tap:perfect", "tap:miss"]:
		if pulses.has(k): UiKit.draw_outlined(self, Tx.t("hud." + k.replace(":", "_")), context_center + Vector2(-90, -CTX_R - 58), 22,
			UiKit.GOLD if k == "tap:perfect" else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 180)
	if joystick_id != -999:
		draw_arc(joystick_origin, 76, 0, TAU, 40, Color(1, 1, 1, 0.12), 2)
		draw_circle(joystick_origin + (joystick_pos - joystick_origin).limit_length(76), 18, Color(1, 1, 1, 0.14))
	if not Game.is_revealed("hud:joystick_hint_done") and Game.active().quests.has_flag("prologue_active") and t < 12.0:
		UiKit.draw_outlined(self, Tx.t("hud.drag_on_the_left_half"), Vector2(40, 470), 20, Color(UiKit.PAPER, 0.6 + 0.4 * sin(t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, 560)

func _boss_arena() -> bool:
	return Game.room_rt != null and str(Game.room_rt.def.get("type", "")) == "boss_arena"

## The purse (mockup 02): silver and spirit stones on the currency pill under the icon row, growing leftward for large
## sums; it rests in boss arenas (mockup 01).
## The purse as last drawn (none when it is not): the world's labels keep off it (the prototype's QA saw Artisan Row's
## way plate under it on the Fairground). The status row under the player panel likewise (status_rect).
var purse_rect := Rect2()
var status_rect := Rect2()

func _draw_purse() -> void:
	var silver := UiKit.fmt(Game.economy.balance("silver_tael"))
	var stones := int(Game.account.currencies.get("spirit_stone", 0))
	var sw := UiKit.text_width(silver, 18)
	var w := 38.0 + sw + 16.0
	if stones > 0: w += 34.0 + UiKit.text_width(UiKit.fmt(stones), 18)
	w = maxf(222.0, w)
	var cr := Rect2(1262 - w, 222, w, 34)
	purse_rect = cr
	draw_style_box(UiKit.style("currency_pill"), cr)
	glyph("coin", cr.position + Vector2(20, 17), 32)
	UiKit.draw_text(self, silver, cr.position + Vector2(38, 24), 18, UiKit.PALE_GOLD)
	if stones > 0:
		var sx := 38.0 + sw + 28.0
		glyph("spirit_stone", cr.position + Vector2(sx, 17), 32)
		UiKit.draw_text(self, UiKit.fmt(stones), cr.position + Vector2(sx + 20, 24), 18, UiKit.BRIGHT_JADE)

## The icon row (Menu, Bag, Map, Mail at 56 apart): a count on Mail, and a vermilion ready seal on Menu when something
## waits in the hub (mockup 02).
func _draw_icon_row(c) -> void:
	for ic in icon_row:
		if not shown(ic[0]): continue
		var at: Vector2 = ic[1]
		ring(at, 26, pulses.has("hud:" + ic[0]))
		glyph(ic[0], at, 32)
		if ic[0] == "mail" and Game.mail.unread(c) > 0: UiKit.count_badge(self, at + Vector2(23, -23), Game.mail.unread(c))
		if ic[0] == "menu" and hub_ready(c): UiKit.ready_seal(self, at + Vector2(25, -25))

## Something waits in the hub: the bottleneck is reached, or a day's activity chest is full and not yet opened (the
## Menu's tablets that carry a ready seal, MenuPage.ready_seals).
func hub_ready(c) -> bool:
	return not MenuPage.ready_seals(c).is_empty()

## A number in the corner of a ring (a count, the Presence's level): a dark pill at its lower right (the kit's .k-corner).
func _corner(at: Vector2, s: String, col := UiKit.PAPER) -> void:
	var w := maxf(22.0, UiKit.text_width(s, 14) + 10.0)
	var cen := at + Vector2(21, 21)
	UiKit.pill(self, Rect2(cen - Vector2(w * 0.5, 11), Vector2(w, 22)), UiKit.INK)
	UiKit.draw_text(self, s, Vector2(cen.x - w * 0.5, cen.y + 5), 14, col, HORIZONTAL_ALIGNMENT_CENTER, w)

## The party chips beside the player panel (mockup 01): the animals beside you (the active one first) and the fellow
## disciples, each a 48 px ring with its face, an HP arc and its name under it; then the animals in the Spirit Beast Bag
## (tap to swap one in, never in a fight) and the mount (tap to ride or walk). An animal opens Spirit Animals, a disciple
## Companions.
func _party_chips(c) -> Array:
	var specs: Array = []
	if c == null or not shown("player_panel"): return specs
	var seen := {}
	if shown("pet"):
		var act: Dictionary = Game.pets.active_pet(c)
		if not act.is_empty():
			specs.append({"kind": "active", "uid": str(act.uid), "name": str(act.get("name", ""))})
			seen[str(act.uid)] = true
		for p in Game.pets.party(c):
			if seen.has(str(p.uid)): continue
			specs.append({"kind": "party", "uid": str(p.uid), "name": str(p.get("name", ""))})
			seen[str(p.uid)] = true
	for cid in c.companions.get("active", []):
		specs.append({"kind": "companion", "uid": str(cid), "name": ContentDB.name_of("companions", str(cid))})
	if shown("pet"):
		for uid in c.pet_bag:
			var bp: Dictionary = Game.pets._pet(c, str(uid))
			if bp.is_empty() or seen.has(str(uid)) or str(uid) == c.active_pet: continue
			specs.append({"kind": "bag", "uid": str(uid), "name": str(bp.get("name", ""))})
			seen[str(uid)] = true
		if not Game.pets.mount_pet_of(c).is_empty(): specs.append({"kind": "mount", "uid": str(c.mount_pet), "name": ""})
	for i in specs.size():
		specs[i].center = Vector2(408.0 + i * 60.0, 44.0)
		specs[i].r = 24.0
	return specs

## The party member's body in this room (a pet's or a disciple's ally), or null when it is not out.
func _party_ally(pc: Dictionary):
	if Game.room_rt == null: return null
	var au = (Game.companions.allies if str(pc.kind) == "companion" else Game.pets.allies).get(str(pc.uid))
	return Game.room_rt.enemies.get(int(au)) if au != null else null

func _draw_party(c) -> void:
	for pc in _party_chips(c):
		var cen: Vector2 = pc.center
		var kind := str(pc.kind)
		var a = _party_ally(pc)
		var frac: float = clampf(a.pools.hp / maxf(1.0, a.pools.max_hp), 0.0, 1.0) if a != null else 1.0
		var down: bool = a != null and str(a.ai.get("state", "")) == "downed"
		ring(cen, 24, kind == "mount" and c.riding)
		if kind == "companion":
			_draw_face(cen, str(pc.uid), down)
		else:
			var p: Dictionary = Game.pets._pet(c, str(pc.uid))
			var art := str(ContentDB.entry("pets", str(p.get("species", ""))).get("art", p.get("species", "")))
			UiKit.draw_creature(self, Rect2(cen - Vector2(18, 18), Vector2(36, 36)), art, "idle", t)
			if p.get("wounded", false): down = true   # a Grievous Wound: the ring runs red all round
		if down: draw_arc(cen, 28, 0, TAU, 32, UiKit.RED, 3)
		elif kind in ["active", "party", "companion"]:
			draw_arc(cen, 28, -PI / 2, -PI / 2 + TAU * maxf(frac, 0.001), 32, UiKit.BRIGHT_JADE if frac > 0.3 else UiKit.RED, 3)
		# A name too long for its chip gives its last word ("Reed Otter" is the otter, mockup 01).
		var nm := str(pc.name)
		if UiKit.text_width(nm, 14, true) > 58.0: nm = nm.get_slice(" ", nm.get_slice_count(" ") - 1)
		var col := UiKit.SKY
		if kind == "bag": col = UiKit.MIST
		elif kind == "mount":
			col = UiKit.GOLD if c.riding else UiKit.MIST
			nm = Tx.t("hud.walk") if c.riding else Tx.t("hud.ride")
		UiKit.draw_outlined(self, UiKit.fit(nm, 14, 58, true), cen + Vector2(-30, 42), 14, col, HORIZONTAL_ALIGNMENT_CENTER, 60)

## A fellow disciple's face for their chip: the head of their figure as the game draws them. Decision 42 (no old
## side-view character left in the top-down game): for a top-down character, the top-down figure's head (its idle
## frame three-quarters toward the camera at x FACE_TOP_K, its sheets loading on threads: the chip is empty the frames
## they take; the frame cast for the pictures at 38 px, decision 43, so the chip keeps the head it was framed for); the
## side view's head and shoulders only for a classic side-view character.
func _draw_face(center: Vector2, cid: String, dim := false) -> void:
	var box := Vector2(FACE_BOX, FACE_BOX)
	if Figures.top_down():
		var fig: TopdownFigure = _faces.get("top|" + cid)
		if fig == null:
			fig = TopdownFigure.wearing(_face_outfit(cid), true)
			_faces["top|" + cid] = fig
		if not fig.loaded(): return
		var b := fig.bounds("idle", TopdownDoll.PORTRAIT_ROW, 0, "body", true)   # the bare body: its head under any hair
		var head := Vector2(roundf(b.get_center().x), b.position.y + FACE_TOP_HEAD)   # the head's middle, art px from the feet
		fig.draw(self, (center - head * FACE_TOP_K).round(), "idle", TopdownDoll.PORTRAIT_ROW, 0, Color(1, 1, 1, 0.45 if dim else 1.0), FACE_TOP_K,
			Rect2(center - box * 0.5, box), true)
		return
	if not _faces.has(cid):
		var av = Figures.side_avatar(_face_outfit(cid))
		av.refresh_entries()
		_faces[cid] = av.entries.duplicate()
		av.free()
	for en in _faces[cid]:
		var cell := int(en.cell)
		var off := (cell - 256) * 0.5
		var src := Rect2(Vector2(128.0 + off, cell + 190.0 + off) + FACE_AT - box * 0.5, box)
		draw_texture_rect_region(en.texture, Rect2(center - box * 0.5, box), src, Color(1, 1, 1, 0.45 if dim else 1.0))

## A companion's look for their face: their outfit, its unset pieces a disciple's, no weapon.
func _face_outfit(cid: String) -> Dictionary:
	var o: Dictionary = ContentDB.entry("companions", cid).get("outfit", {}).duplicate()
	for k in ["body", "hair", "shirt", "pants", "shoes", "weapon", "hat", "cape"]:
		if not o.has(k): o[k] = {"body": "light", "hair": "short_knot", "shirt": "disciple", "pants": "loose", "shoes": "boots"}.get(k, "none")
	if not o.has("hair_color"): o.hair_color = 0
	o.weapon = "none"
	return o

func _draw_player_panel(c) -> void:
	if not shown("player_panel"): return
	# The panel grows by one row once the Soul bar exists (Spirit Awakening).
	var soul_row: bool = c.pools.max_soul > 0.0 and shown("soul_bar")
	var r := panel_rect(c)
	draw_style_box(frame_style, r)
	# No portrait roundel (the user's note on the P3 mockups): name, realm and the bars take the panel's width; the
	# bottleneck shows on the Stored Qi bar along the bottom edge.
	UiKit.draw_text(self, c.name, r.position + Vector2(18, 30), 18, UiKit.PAPER)
	if shown("realm_badge"):
		# Concealment's false realm (S48) is the badge the world sees; a veil mark says it is not the true one.
		var badge := ContentDB.realm_label(Game.progression.shown_realm(c), -1 if c.cultivator.false_realm != "" else ProgressionRules.level(c))
		var veiled: bool = c.cultivator.false_realm != ""
		UiKit.draw_text(self, badge, r.position + Vector2(18, 50), 16, UiKit.MIST if veiled else UiKit.PALE_GOLD)
		if veiled: UiKit.draw_text(self, Tx.t("hud.realm_veiled"), r.position + Vector2(24 + UiKit.text_width(badge, 16), 50), 14, UiKit.MIST)
	var y := 60.0
	if shown("hp_bar"):
		# A heal over time still running shows where the bar is going: a pale jade run past the red.
		var coming := 0.0
		for h in Game.combat.hots_of(c.id): coming += float(h.per_s) * float(h.left)
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.hp / maxf(1.0, c.pools.max_hp), UiKit.HP, Tx.t("hud.hp"), "%s / %s" % UiKit.pool_values(c.pools.hp, c.pools.max_hp),
			coming / maxf(1.0, c.pools.max_hp), float(pulses.get("bar:hp", 0.0)))
		y += 18
	# No cultivation, no Qi: the QI bar appears only once a QI pool exists.
	if c.pools.max_qi > 0.0 and shown("qi_bar"):
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.qi / c.pools.max_qi, UiKit.QI, Tx.t("hud.qi"), "%s / %s" % UiKit.pool_values(c.pools.qi, c.pools.max_qi), 0.0, float(pulses.get("bar:qi", 0.0)))
		y += 18
	if soul_row:
		bar(Rect2(r.position.x + 56, r.position.y + y, 288, 14), c.pools.soul / c.pools.max_soul, UiKit.SOUL, Tx.t("hud.sl"), "%s / %s" % UiKit.pool_values(c.pools.soul, c.pools.max_soul), 0.0, float(pulses.get("bar:soul", 0.0)))
	# S48 the Blood path: a thin crimson strip for the blood essence kills have gathered.
	if ProgressionAuthority.walks(c, "blood"):
		var strip := Rect2(r.position.x + 56, r.end.y - 6, 288, 3)
		draw_rect(strip.grow(1), UiKit.INK)
		draw_rect(Rect2(strip.position, Vector2(strip.size.x * clampf(Game.combat.essence_of(c.id) / 100.0, 0.0, 1.0), strip.size.y)), UiKit.BLOOD)
	# Status stack (injuries, stability, toxicity, composure, buffs, statuses).
	var meter: bool = c.pools.hollowing > 0.5
	var icons: Array = []
	for kind in c.cultivator.injuries: icons.append("injury_" + kind)
	if Unlocks.is_unlocked(c.id, "foundation") and c.cultivator.stability != "stable": icons.append("stability_" + c.cultivator.stability)
	if c.cultivator.state == "consolidating": icons.append("consolidating")
	if c.cultivator.toxicity > 0.5 * c.stats.value("toxicity_tolerance") and c.cultivator.toxicity > 5: icons.append("toxicity")
	if c.pools.hollowing > 5 and not meter: icons.append("hollowing")
	if ProgressionRules.heart_demon_steps(c.cultivator) >= 1: icons.append("heart_demon")   # S48: 25 and more
	if Game.combat.killing_intent_stacks(c.id) >= 5: icons.append("buff_attack")               # S48 Killing Intent
	if Game.combat.poison_body_active(c): icons.append("poison_body")                          # S48 the Poison Body
	if Unlocks.is_unlocked(c.id, "composure") and c.pools.composure < 100: icons.append("composure")
	# Timed entries carry their seconds left, drawn under the icon: a status, a buff, a heal over time (the tea's own
	# icon while it works, so a tea drunk at full HP still shows it is running).
	var left := {}
	for s in c.pools.statuses:
		if s.id == "spawn_protection": continue
		var sic := str(ContentDB.entry("status_effects", str(s.id)).get("icon", s.id))
		if not icons.has(sic): icons.append(sic)
		left[sic] = maxf(float(left.get(sic, 0.0)), float(s.get("remaining", 0.0)))
	for m in c.stats.modifiers:
		if float(m.duration) >= 0 and not str(m.source).begins_with("heal:"):
			var ic := "buff_attack" if str(m.stat) in ["physical_attack", "qi_attack"] else ("buff_defense" if "defense" in str(m.stat) else "buff_speed")
			if not icons.has(ic): icons.append(ic)
			left[ic] = maxf(float(left.get(ic, 0.0)), float(m.get("remaining", m.duration)))
	for h in Game.combat.hots_of(c.id):
		var src := str(h.get("source", ""))
		var hic := src.substr(5) if src.begins_with("item:") and SpriteCache.icon_fit(src.substr(5), 24).size() > 0 else "healing_pill"
		if not icons.has(hic): icons.append(hic)
		left[hic] = maxf(float(left.get(hic, 0.0)), float(h.left))
	# Under the panel (mockups 01, 02): the Hollowing meter first once it has risen, then 24 px icons 4 apart.
	var row_y := r.end.y + 8.0
	var x := r.position.x + 4.0
	if meter: x = _draw_hollowing(c, Vector2(r.position.x + 2.0, row_y))
	# What the row holds, for the world's labels to keep off (a Festival Lantern's plate lay over the Hollowing meter).
	status_rect = Rect2(r.position.x, row_y - 2.0, minf(r.end.x, x + 28.0 * icons.size()) - r.position.x, 46.0) if meter or not icons.is_empty() else Rect2()
	for ic in icons.slice(0, 12):
		if x + 24.0 > r.end.x: break
		glyph(ic, Vector2(x + 12, row_y + 12), 24)
		if float(left.get(ic, 0.0)) > 0.0:
			var secs := float(left[ic])
			UiKit.draw_outlined(self, UiKit.span(secs), Vector2(x - 6, row_y + 40), 14, UiKit.PAPER,
				HORIZONTAL_ALIGNMENT_CENTER, 36)
		x += 28
	# S47 Sword Intent: ten pips along the panel's foot while a jian is in hand and Intent is building.
	var stacks := int(Game.combat.sword_intent.get(c.id, {}).get("stacks", 0))
	if stacks > 0 and str(StatRules.family(c).get("id", "")) == "jian":
		for i in 10:
			var pc := Vector2(r.position.x + 130 + i * 21, r.end.y - 7)
			var dia := PackedVector2Array([pc + Vector2(0, -5), pc + Vector2(5, 0), pc + Vector2(0, 5), pc + Vector2(-5, 0)])
			if i < stacks: draw_colored_polygon(dia, UiKit.GOLD if stacks >= 10 else UiKit.MIST)
			draw_polyline(dia + PackedVector2Array([dia[0]]), UiKit.INK, 1.5)

## The Hollowing meter (mockup 02): its stops at Burden and at Seizure, the value, and which way it runs (falling
## faster near the lanterns). Returns where the status icons go on.
func _draw_hollowing(c, at: Vector2) -> float:
	var h: float = c.pools.hollowing
	if _hollow_last >= 0.0 and absf(h - _hollow_last) > 0.0001: _hollow_dir = signf(h - _hollow_last)
	_hollow_last = h
	var burden := float(ContentDB.stat_const("hollowing.burden_at", 50))
	var seize := float(ContentDB.stat_const("hollowing.seizure_at", 100))
	glyph("hollowing", at + Vector2(12, 12), 24)
	var b := Rect2(at.x + 32, at.y + 8, 170, 10)
	draw_rect(b.grow(2), UiKit.INK)
	draw_rect(b, UiKit.BAR_TROUGH)
	draw_rect(Rect2(b.position, Vector2(b.size.x * clampf(h / seize, 0.0, 1.0), b.size.y)), UiKit.HOLLOW if h < burden else UiKit.WARNING)
	var bx := b.position.x + b.size.x * burden / seize
	draw_rect(Rect2(bx - 1, b.position.y - 3, 2, 16), UiKit.PALE_GOLD)
	draw_rect(Rect2(b.end.x - 1, b.position.y - 3, 2, 16), UiKit.RED)
	UiKit.draw_outlined(self, Tx.t("hud.hollow_burden") % int(burden), Vector2(bx - 60, at.y + 34), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 120)
	var x := b.end.x + 8.0
	var v := str(int(round(h)))
	UiKit.draw_outlined(self, v, Vector2(x, at.y + 18), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 40)
	x += UiKit.text_width(v, 16, true) + 4.0
	if _hollow_dir != 0.0:
		var col := UiKit.BRIGHT_JADE if _hollow_dir < 0.0 else UiKit.RED_TEXT
		UiKit.draw_outlined(self, "▼" if _hollow_dir < 0.0 else "▲", Vector2(x, at.y + 18), 14, col, HORIZONTAL_ALIGNMENT_LEFT, 20)
		x += 16.0
		if _hollow_dir < 0.0 and Game.room_rt != null and Game.room_rt.def.get("lantern", false):
			var lw := Tx.t("hud.hollow_lanterns")
			UiKit.draw_outlined(self, lw, Vector2(x, at.y + 18), 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, 90)
			x += UiKit.text_width(lw, 14, true) + 4.0
	return x + 12.0

func _auto_hunt_shown(c) -> bool:
	return c != null and bound() and Unlocks.is_unlocked(c.id, "idle_tasks") and (Game.world.auto_hunting(c.id) or Game.world.auto_hunt_block(c) == "")

## The quest tracker (mockup 02): a plate under the statuses with a gold rule down its left, each quest's title, where
## it leads with a 48 px go button that walks you there (lit while it does), and its objectives; between main quests
## the story's next one first (◇ Next: who gives it and where, or the Level it waits on and where to hunt); it rests in
## boss arenas and stops above the log.
func _draw_tracker(c) -> void:
	var entries: Array = WorldShared.quest_tracker(c)
	if entries.is_empty() or _boss_arena(): return
	var top := panel_rect(c).end.y + TRACKER_DROP
	var here := Game.room_rt.room_id if Game.room_rt else ""
	var rows: Array = []
	var h := 8.0
	for q in entries:
		var goal := str(q.get("target_room", ""))
		var go := goal != "" and goal != here
		var eh := 24.0 + (20.0 if go else 0.0) + 20.0 * (q.lines as Array).size()
		if go: eh = maxf(eh, 52.0)
		if not rows.is_empty() and top + h + eh > TRACKER_FOOT: break
		rows.append({"q": q, "goal": goal, "go": go, "h": eh})
		h += eh + 4.0
	tracker_rect = Rect2(14, top, 342, h)
	draw_rect(tracker_rect, UiKit.PLATE)
	draw_rect(Rect2(tracker_rect.position, Vector2(2, tracker_rect.size.y)), Color(UiKit.GOLD, 0.5))
	var y := top + 4.0
	for row in rows:
		var q: Dictionary = row.q
		var main: bool = QuestAuthority.leads(str(q.kind))
		var col = UiKit.GOLD if main else UiKit.SKY
		var tw := 266.0 if row.go else 318.0
		var mark := "◇ " if str(q.kind) == "next" else ("◆ " if main else "● ")
		UiKit.draw_text(self, UiKit.fit(mark + str(q.name), 18, tw), Vector2(24, y + 20), 18, col, HORIZONTAL_ALIGNMENT_LEFT, tw)
		var ly := y + 24.0
		if row.go:
			# S49 auto-path: a button that walks you to where the quest leads (lit while it is walking you there).
			var br := Rect2(300, y + 2, 48, 48)
			var going: bool = Game.world.auto_path_target(Game.active()) == str(row.goal)
			draw_style_box(UiKit.style("button_secondary", "selected" if going else "normal"), br)
			UiKit.draw_text(self, "➤", br.position + Vector2(0, 31), 18, UiKit.GOLD if going else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, br.size.x)
			tracker_paths.append({"rect": go_hit(br), "target": str(row.goal)})
			# P1: the tracker names where the quest leads (a hunting ground as one).
			var place := WorldAuthority.place_name(str(row.goal))
			if q.get("hunt", false): place = Tx.t("hud.hunt_at") % place
			UiKit.draw_text(self, UiKit.fit("➤ " + place, 14, 262), Vector2(32, ly + 15), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 262)
			ly += 20.0
		for line in q.lines:
			var lw := 262.0 if row.go and ly < y + 52.0 else 314.0
			var count := "%d / %d" % [int(line.have), int(line.need)] if int(line.need) > 1 else ""
			var lc := UiKit.BRIGHT_JADE if line.done else UiKit.PAPER
			UiKit.draw_text(self, tracker_objective(("✓ " if line.done else "· ") + str(line.text), count, lw), Vector2(32, ly + 16), 16, lc, HORIZONTAL_ALIGNMENT_LEFT, lw)
			if count != "": UiKit.draw_text(self, count, Vector2(32, ly + 16), 16, lc, HORIZONTAL_ALIGNMENT_RIGHT, lw)
			ly += 20.0
		y += float(row.h) + 4.0

## B11: an objective beside its count on a tracker line `width` wide: the count keeps its place at the right end and
## the words give way with an ellipsis (the count was appended and cut: "…Shallows  0" for 0/5).
static func tracker_objective(words: String, count: String, width: float) -> String:
	return UiKit.fit(words, 16, width - (UiKit.text_width(count, 16) + 10.0 if count != "" else 0.0))

## S43 rule 15: while a thief runs or a timed route is on, the seconds sit at the top of the screen (first in the top
## centre's stack).
func _draw_run_banner(c, y0: float) -> float:
	if c == null: return y0
	var label := ""
	var secs := 0.0
	var ch: Dictionary = Game.world.chases.get(c.id, {})
	var run: Dictionary = Game.world.runs.get(c.id, {})
	if not ch.is_empty():
		label = Tx.t("hud.chase_banner")
		secs = Game.sim_time - float(ch.start)
	elif not run.is_empty():
		var o: Dictionary = Game.room_rt.object_def(str(run.object)) if Game.room_rt else {}
		if o.is_empty(): return y0
		label = str(o.route.get("name", ""))
		secs = Game.sim_time - float(run.start)
	else:
		return y0
	var text := "%s   %.1f s" % [label, secs]
	var w := UiKit.text_width(text, 22) + 40
	var r := Rect2(640 - w * 0.5, y0, w, 40)
	draw_rect(r, UiKit.PLATE)
	draw_rect(r, Color(UiKit.GOLD, 0.7), false, 1.5)
	UiKit.draw_text(self, text, r.position + Vector2(0, 28), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	return r.end.y + 8.0

func _draw_minimap(c) -> void:
	var r := minimap_rect
	draw_style_box(UiKit.style("minimap_frame"), r)
	var room := Game.room_rt.def if Game.room_rt else {}
	UiKit.draw_text(self, str(room.get("name", "")), r.position + Vector2(12, 19), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24, true, true)
	var inner := Rect2(r.position + Vector2(8, 26), r.size - Vector2(16, 34))
	var b: Array = room.get("bounds", [0, 480, 1280, 480])
	var bw := float(b[2])
	var sx := inner.size.x / bw
	# Screen-space projection: x along the room, y = plane y - altitude, fitted to the
	# room's real extent (highest roof line down to the front of the ground strip).
	var top := 600.0
	var bottom := 700.0
	if Game.room_rt:
		for s0 in Game.room_rt.geometry.surfaces:
			top = minf(top, s0.bounds.position.y - s0.base - 20.0)
			bottom = maxf(bottom, s0.bounds.end.y)
	var sy := inner.size.y / maxf(1.0, bottom - top)
	var to_map := func(pos: Vector2, alt: float) -> Vector2:
		return inner.position + Vector2(pos.x * sx, (pos.y - alt - top) * sy)
	var grid: TopdownRoom = Game.room_rt.topdown if Game.room_rt else null
	if grid != null:
		# Redesign Phase 4: a room on the height grid is drawn as its level map, the whole room fitted in the frame
		# (the plane seen from above); the ways, marks, people and foes below take the same projection.
		var k := minf(inner.size.x / (grid.w * TopdownRoom.TILE), inner.size.y / (grid.h * TopdownRoom.TILE))
		var at0 := inner.position + (inner.size - Vector2(grid.w, grid.h) * TopdownRoom.TILE * k) * 0.5
		to_map = func(pos: Vector2, _alt: float) -> Vector2: return at0 + pos * k
		draw_texture_rect(_grid_map(grid), Rect2(at0, Vector2(grid.w, grid.h) * TopdownRoom.TILE * k), false)
	for s in Game.room_rt.geometry.surfaces if Game.room_rt and grid == null else []:
		if s.disabled: continue
		var y0: Vector2 = to_map.call(Vector2(s.bounds.position.x, s.bounds.position.y), s.base)
		var y1: Vector2 = to_map.call(Vector2(s.bounds.end.x, s.bounds.position.y), s.base)
		if s.is_block:
			# S43: blocks as small squares, climbables as vertical lines, movers as dashed lines.
			var mid := (y0 + y1) * 0.5
			draw_rect(Rect2(mid - Vector2(2.5, 2.5), Vector2(5, 5)), Color(UiKit.SURFACE.map_line, 0.8))
		elif s.moving:
			draw_dashed_line(y0, y1, Color(UiKit.PALE_GOLD, 0.9), 2.0, 3.0)
		else:
			draw_line(y0, y1, Color(UiKit.SURFACE.map_line, 0.55 if s.stratum == "ground" else 0.8), 2)
	for cb in Game.room_rt.geometry.climbables if Game.room_rt else []:
		var ca: Array = cb.at
		var foot: Vector2 = to_map.call(Vector2(float(ca[0]), float(ca[1])), float(cb.bottom_alt))
		var head: Vector2 = to_map.call(Vector2(float(ca[0]), float(ca[1])), float(cb.top_alt))
		draw_line(foot, head, Color(UiKit.GOLD, 0.9), 1.5)
	for p in room.get("portals", []):
		var at: Array = p.at
		var st: Dictionary = WorldShared.portal_state(c, p)
		if st.get("hidden", false): continue
		draw_circle(to_map.call(Vector2(float(at[0]), float(at[1])), 0.0), 4, UiKit.BRIGHT_JADE if st.open else UiKit.HOLLOW)
	# P1 quest direction: the exit toward the tracked quest pulses gold, and a chevron on the frame's edge points
	# the way from where you stand.
	var gs: Dictionary = WorldShared.guide_step(c)
	if not gs.is_empty():
		var gp: Vector2 = to_map.call(Vector2(float(gs.x), float(gs.y)), 0.0)
		draw_arc(gp, 7.0 + sin(t * 5.0) * 1.5, 0, TAU, 14, UiKit.GOLD, 2.0)
		var me: ActorState = Game.actor_state(c.id)
		var dir := signf(float(gs.x) - (me.plane.x if me != null else 0.0))
		if dir == 0.0: dir = 1.0
		var ex := r.end.x - 7.0 if dir > 0.0 else r.position.x + 7.0
		var ey := clampf(gp.y, inner.position.y + 8.0, inner.end.y - 8.0)
		var way := Vector2(dir, 0.0)
		var tip := Vector2(ex, ey)
		if grid != null and me != null:
			# On the height grid the way may lie north or south too: the chevron sits on the frame's edge the way points.
			way = minimap_way(to_map.call(me.plane, 0.0), gp)
			tip = _edge_point(inner.grow(-8.0), inner.get_center(), way)
		tip += way * sin(t * 4.0) * 2.0
		var side := Vector2(-way.y, way.x)
		var chev := PackedVector2Array([tip, tip - way * 9.0 - side * 7.0, tip - way * 9.0 + side * 7.0])
		draw_colored_polygon(chev, UiKit.GOLD)
		draw_polyline(chev + PackedVector2Array([chev[0]]), UiKit.INK, 1.5)
	for o in room.get("objects", []):
		if not WorldShared.object_visible(c, o): continue
		var at2: Array = o.at
		var mp: Vector2 = to_map.call(Vector2(float(at2[0]), float(at2[1])), float(o.get("alt", 0)))
		if o.type == "npc":
			var mk: String = WorldShared.npc_marker(c, str(o.npc))
			draw_circle(mp, 3, UiKit.GOLD if mk in ["main", "ready"] else (UiKit.BRIGHT_JADE if mk == "again" else UiKit.PALE_GOLD))
			if QuestAuthority.marker_calls(mk): draw_arc(mp, 6 + sin(t * 4.0) * 1.5, 0, TAU, 12, UiKit.BRIGHT_JADE if mk == "again" else UiKit.GOLD, 1)
		elif o.type in ["shrine", "qi_spring", "teleport_stone"] and (grid == null or PlaceRules.at_object(Game.room_rt.room_id, str(o.id)).is_empty()):
			draw_rect(Rect2(mp - Vector2(3, 3), Vector2(6, 6)), UiKit.BRIGHT_JADE)
		elif o.type == "treasure_birth":
			# S45: a Spirit Fruit ripening here stands up as a pillar of light on the minimap.
			var pa := 0.55 + 0.25 * sin(t * 3.0)
			draw_rect(Rect2(Vector2(mp.x - 3.0, inner.position.y + 2.0), Vector2(6.0, mp.y - inner.position.y - 2.0)), Color(UiKit.GOLD, pa * 0.35))
			draw_line(Vector2(mp.x, inner.position.y + 2.0), mp, Color(UiKit.PALE_GOLD, pa), 1.5)
			draw_circle(mp, 3.5, UiKit.GOLD)
		elif o.type == "spirit_mine":
			# S49 territory: a mine shows in its holder's colour; yours glints jade.
			var mid := str(o.get("mine", ""))
			var mc := UiKit.BRIGHT_JADE if Game.sect.holds(mid) else Color(str(Game.sect.rival(str(ContentDB.entry("territory", mid).get("sect", ""))).get("color", UiKit.MIST.to_html(false)))).lightened(0.3)
			draw_colored_polygon(PackedVector2Array([mp + Vector2(0, -4), mp + Vector2(4, 0), mp + Vector2(0, 4), mp + Vector2(-4, 0)]), mc)
		elif o.type == "herb_patch" and o.has("ripen"):
			# S45: a rare herb shows as a leaf, gold while ripe, with the time left (or until it ripens).
			var hs: Dictionary = Game.world.herb_state(o)
			var spent: bool = Game.room_rt.objects.get(str(o.id), {}).get("state", "ready") == "depleted"
			var ripe: bool = hs.ripe and not hs.dormant and not spent
			var lc := UiKit.GOLD if ripe else Color(UiKit.HOLLOW, 0.9)
			draw_colored_polygon(PackedVector2Array([mp + Vector2(0, -5), mp + Vector2(3.5, 0), mp + Vector2(0, 4), mp + Vector2(-3.5, 0)]), lc)
			if ripe: draw_arc(mp, 6.5 + sin(t * 5.0), 0, TAU, 12, UiKit.GOLD, 1)
			if not hs.dormant and not spent:
				UiKit.draw_text(self, UiKit.span(float(hs.seconds)), mp + Vector2(-30, 14), 14, lc, HORIZONTAL_ALIGNMENT_CENTER, 60)
	# Decision 43: the room's places, each a small glyph of its kind (TopdownPlaceArt's things, read at a glance); one
	# that has something waiting (a new notice, a letter, a ripe bed, a finished batch) wears a gold spark. A tap near
	# one opens the world map's Places on it, whose card offers the walk there.
	# The marks are worked out twice a second, or as the room changes (the room's map stays put in between).
	_place_look -= get_process_delta_time()
	var mark_room := str(Game.room_rt.room_id) if grid != null else ""
	if _place_look <= 0.0 or mark_room != _place_room:
		minimap_places = place_marks(c, mark_room, to_map, inner.position.y + 6.0) if grid != null else []
		_place_room = mark_room
		_place_look = 0.5
	for mk in minimap_places: TopdownPlaceArt.glyph(self, (mk.at as Vector2).round(), str(mk.kind), bool(mk.wait), t)
	if Game.room_rt and Game.account.settings.get("minimap_monsters", true):
		for e in Game.room_rt.enemies.values():
			if not e.alive or e.hidden: continue
			var ep: Vector2 = to_map.call(e.plane, e.altitude)
			var col = UiKit.SKY if e.team == "ally" else (UiKit.GOLD if e.elite or e.is_boss() else UiKit.RED)
			draw_circle(ep, 2.5, col)
	var pp: Vector2 = to_map.call(player.plane, player.altitude)
	# The arrow points the way the body faces: along x in the side view, any of eight ways on the height grid.
	var fv := Vector2(player.facing, 0) if grid == null or player.get("motor") == null else (player.motor.dir as Vector2).normalized()
	var fs := Vector2(-fv.y, fv.x)
	draw_colored_polygon(PackedVector2Array([pp + fv * 5.0, pp - fv * 3.0 - fs * 4.0, pp - fv * 3.0 + fs * 4.0]), Color.WHITE)

## Decision 43: the places drawn on the minimap this frame ({id, at}), and their states, looked at twice a second.
var minimap_places: Array = []
var _place_states := {}
var _place_look := 0.0
var _place_room := ""

## The room's places on the minimap (decision 43): [{id, kind, at (the map's px, by `to_map`), wait}], each place the
## character sees (PlaceRules.visible); two a few cells apart would overlap on the small map, so the later one steps
## above (not over `top`) or below. `wait`: something waits there (a new notice, a letter, a ripe bed, a ready batch).
func place_marks(c, room_id: String, to_map: Callable, top := -INF) -> Array:
	var out: Array = []
	for pl in PlaceRules.of_room(room_id):
		if not PlaceRules.visible(c, pl): continue
		var at: Vector2 = to_map.call(PlaceRules.point(pl), 0.0)
		for k in 2:
			for other in out:
				if at.distance_to(other.at) < 15.0: at.y += -14.0 if at.y >= float(other.at.y) and at.y - 14.0 > top else 14.0
		if _place_look <= 0.0 or not _place_states.has(str(pl.id)): _place_states[str(pl.id)] = PlaceRules.state(c, pl)
		var ps: Dictionary = _place_states[str(pl.id)]
		var wait := int(ps.get("new", 0)) > 0 or (str(ps.state) in ["ribbon", "growth"] and bool(ps.get("on", false)))
		out.append({"id": str(pl.id), "kind": str(pl.kind), "at": at, "wait": wait})
	return out

## What a tap on the minimap opens the world map on: the Places view on the place nearest the tap (within 16 px of its
## glyph), else the map as it opens.
func minimap_place_at(p: Vector2) -> Dictionary:
	var best := {}
	var best_d := 16.0
	for mp in minimap_places:
		var d := p.distance_to(mp.at)
		if d < best_d:
			best_d = d
			best = {"view": "places", "place": str(mp.id)}
	return best

## Redesign Phase 4: the direction mark's way on a grid room's map, from the player's dot to the goal (east when on it).
static func minimap_way(from: Vector2, to: Vector2) -> Vector2:
	return (to - from).normalized() if from.distance_to(to) > 0.5 else Vector2.RIGHT

## Where a ray from `center` along `way` leaves `r` (the direction mark's place on the map's frame).
static func _edge_point(r: Rect2, center: Vector2, way: Vector2) -> Vector2:
	var k := INF
	if absf(way.x) > 0.001: k = minf(k, ((r.end.x if way.x > 0.0 else r.position.x) - center.x) / way.x)
	if absf(way.y) > 0.001: k = minf(k, ((r.end.y if way.y > 0.0 else r.position.y) - center.y) / way.y)
	return center + way * (k if k < INF else 0.0)

## A room on the height grid as a map, one pixel a cell, made once a room (drawn scaled, nearest): water, the floor by
## its level (higher is paler), and walls and the props' footprints dark.
var _grid_maps: Dictionary = {}
func _grid_map(grid: TopdownRoom) -> Texture2D:
	if _grid_maps.has(grid.id): return _grid_maps[grid.id]
	var img := Image.create(grid.w, grid.h, false, Image.FORMAT_RGBA8)
	for y in grid.h:
		for x in grid.w:
			var l := grid.level(x, y)
			var col := Color(UiKit.SURFACE.map_line, 0.10)
			if l == TopdownRoom.WATER: col = Color(UiKit.SKY, 0.45)
			elif l == TopdownRoom.SOLID: col = Color(UiKit.INK, 0.55)
			elif not grid.stair_at(x, y).is_empty(): col = Color(UiKit.SURFACE.map_line, 0.45)
			else: col = Color(UiKit.SURFACE.map_line, clampf(0.16 + 0.12 * l, 0.16, 0.7))
			img.set_pixel(x, y, col)
	_grid_maps = {grid.id: ImageTexture.create_from_image(img)}
	return _grid_maps[grid.id]

## The harvest ring (S45): it shrinks from wide to the context's button, where the harvest began (decision 42); the gold
## band is the perfect window for your rank.
func _draw_tap_ring() -> void:
	var at := context_center
	var inner := CTX_R - 6.0
	var outer := inner + 70.0
	var f := clampf(float(tapping.t) / maxf(0.01, float(tapping.ring)), 0.0, 1.0)
	var at_f := func(x: float) -> float: return lerpf(outer, inner, clampf(x, 0.0, 1.0))
	var lo: float = at_f.call(float(tapping.target) + float(tapping.window) * 0.5)
	var hi: float = at_f.call(float(tapping.target) - float(tapping.window) * 0.5)
	draw_circle(at, outer + 6.0, Color(UiKit.PLATE, 0.55))
	draw_arc(at, outer + 6.0, 0, TAU, 64, Color(UiKit.GOLD, 0.35), 1.5)
	draw_arc(at, (lo + hi) * 0.5, 0, TAU, 64, Color(UiKit.GOLD, 0.55), maxf(2.0, hi - lo))
	draw_arc(at, lo, 0, TAU, 64, UiKit.GOLD, 1.5)
	draw_arc(at, hi, 0, TAU, 64, UiKit.GOLD, 1.5)
	var in_band := f >= float(tapping.target) - float(tapping.window) * 0.5 and f <= float(tapping.target) + float(tapping.window) * 0.5
	draw_arc(at, at_f.call(f), 0, TAU, 64, UiKit.PALE_GOLD if in_band else UiKit.BRIGHT_JADE, 4)
	UiKit.draw_outlined(self, Tx.t("hud.tap_now"), at + Vector2(-90, -outer - 18), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 180)

## The glyph of what the context offers (talk, gather, enter...), on its own button on ring 2.
func _context_glyph() -> String:
	if context.is_empty() and tapping.object != "": return "gather"
	return {"npc": "talk", "herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "chest": "open", "storage_chest": "open",
		"portal": "enter", "climbable": "enter", "cooking_pot": "cook", "alchemy_furnace": "alchemy", "earth_vent": "alchemy", "forge_anvil": "forge", "star_sight": "gather",
		"chart_table": "forge", "shipyard_slip": "forge", "starsea_dock": "enter", "mercy": "talk", "insect_swarm": "gather",
		"beast_trail": "gather", "ancestral_altar": "open"}.get(str(context.get("type", "")), "open")

## The context button's words under it, as wide as the ring leaves them (CTX_LABEL_W).
const CTX_LABEL_W := 128.0
func context_label_rect() -> Rect2:
	return Rect2(context_center.x - CTX_LABEL_W * 0.5, context_center.y + CTX_R + 2.0, CTX_LABEL_W, 18.0)

## The verb and its target under the context's button (mockup 02: "Talk · Peddler Ning").
func _context_line(c) -> String:
	var verb := str(context.get("label", ""))
	var who := ""
	if str(context.get("npc", "")) != "": who = ContentDB.name_of("npcs", str(context.npc))
	elif context.has("portal") and str(context.get("target", "")) != "": who = ContentDB.name_of("rooms", str(context.target))
	return (Tx.t("hud.context_target") % [verb, who] if who != "" and verb != "" else verb) + _node_plate(c)

func _draw_controls(c) -> void:
	_draw_fan(c)
	_draw_ring2(c)
	# Ring 1: jump, the techniques (out at rest as in a fight, decision 42), dodge.
	if shown("jump"):
		ring(jump_center, JUMP_R, false, 1.0, pulses.has("hud:jump"))
		glyph("jump", jump_center)
	if shown("guard"):
		ring(guard_center, 26, Game.combat.timeline(c.id).guard, 1.0, pulses.has("hud:guard"), guard_pressed)
		glyph("dodge" if Unlocks.is_unlocked(c.id, "dodge_dash") else "guard", guard_center, 32)
		var dcd = c.pools.cooldown("dodge")
		if dcd > 0: draw_arc(guard_center, 22, -PI / 2, -PI / 2 + TAU * (1.0 - dcd / 2.5), 20, UiKit.MIST, 3)
	if shown("skills"): draw_skill_scroll()
	if _page_tab_shown(c): _draw_page_tab()
	# The attack button: the weapon in hand's glyph, always (decision 42: what the world offers has its own button).
	if shown("attack"):
		ring(attack_center, 66, Game.combat.is_busy(c.id) or Game.combat.is_playing(c.id), 1.0, pulses.has("hud:attack"), attack_pressed)
		glyph(attack_glyph(c), attack_center, 64)
	if _aims(): _draw_attack_moves()

## The Attack button's face: the weapon family's glyph, never a context's (decision 42).
func attack_glyph(c) -> String:
	return str(StatRules.family(c).get("hud_glyph", "fist"))

## The thumb on Attack's aiming gesture, or null.
func attack_gesture() -> AimGesture:
	for id in touches:
		var g = touches[id].get("gesture")
		if g != null and g.kind == "attack": return g
	return null

## How strongly an armed move's mark is lit this frame: a slow pulse, steady under Reduce motion.
func armed_glow() -> float:
	return 1.0 if UiKit.reduce_motion() else 0.8 + 0.2 * sin(t * 8.0)

## Decision 35: while a thumb is on Attack in the top-down room the button shows its drag moves. On the ground, once the
## thumb leaves the dead circle, the finisher's line round the button (pulled in near the screen's edges), lit gold
## when the drag crosses it. In the air, when the body can plunge, the Plunge's sector under the button, lit gold when
## the drag is in it. Held still, a ring fills toward the guard; guarding, the button is ringed in jade (gold for a
## stance). The armed move's name stands over the button, above ring 1's gap. Nothing pulses under Reduce motion.
func _draw_attack_moves() -> void:
	var g := attack_gesture()
	if g == null or not _moves_live(): return
	var mv := armed(g)
	var glow := armed_glow()
	var gold := UiKit.GOLD
	var jade := UiKit.BRIGHT_JADE
	var air: bool = not player.motor.grounded
	if not air and g.strayed and not g.guarding:
		var pts := PackedVector2Array()
		for i in 73:
			var d := Vector2.from_angle(TAU * i / 72.0)
			pts.append(g.origin + d * g.long_px(d))
		var lit := mv == "finisher"
		draw_polyline(pts, Color(gold, 0.95 * glow) if lit else Color(UiKit.PAPER, 0.4), 4.0 if lit else 1.5, true)
	if air and player.plunge_ready():
		var half := deg_to_rad(float(TopdownAim.cfg("plunge_deg", 35)))
		var r0 := float(TopdownAim.cfg("plunge_px", 48))
		var r1 := g.edge_room(Vector2.DOWN)
		var sector := PackedVector2Array()
		for i in 13: sector.append(g.origin + Vector2.DOWN.rotated(lerpf(-half, half, i / 12.0)) * r0)
		for i in 13: sector.append(g.origin + Vector2.DOWN.rotated(lerpf(half, -half, i / 12.0)) * r1)
		var lit := mv == "plunge"
		draw_colored_polygon(sector, Color(gold, 0.3 * glow) if lit else Color(UiKit.PAPER, 0.1))
		sector.append(sector[0])
		draw_polyline(sector, Color(gold, 0.95) if lit else Color(UiKit.PAPER, 0.4), 3.0 if lit else 1.5, true)
		var tip := g.origin + Vector2(0, r0 + 18.0)
		draw_colored_polygon(PackedVector2Array([tip + Vector2(-9, -6), tip + Vector2(9, -6), tip + Vector2(0, 5)]), Color(gold, 0.95) if lit else Color(UiKit.PAPER, 0.5))
	var hold_s := float(TopdownAim.cfg("hold_s", 0.18))
	var guard_s := float(TopdownAim.cfg("guard_s", 0.3))
	if g.guarding:
		draw_arc(g.origin, 72.0, 0, TAU, 64, gold if g.guard_kind == "stance" else jade, 5.0)
	elif not g.strayed and not g.refused and g.t > hold_s:
		var k := clampf((g.t - hold_s) / maxf(0.01, guard_s - hold_s), 0.0, 1.0)
		draw_arc(g.origin, 72.0, -PI / 2, -PI / 2 + TAU * k, 48, Color(jade, 0.85), 3.0)
	var word := str({"finisher": "hud.move_finisher", "plunge": "hud.move_plunge"}.get(mv, ""))
	if mv == "guard": word = "hud.move_stance" if g.guard_kind == "stance" else "hud.move_guard"
	if word != "":
		var col := jade if mv == "guard" and g.guard_kind != "stance" else gold
		UiKit.draw_outlined(self, Tx.t(word), g.origin + Vector2(-80, -76), 18, col, HORIZONTAL_ALIGNMENT_CENTER, 160)

## The technique page tab (mockup 01): "1/2" in a small ring; a tap turns the page (so does a swipe on the ring).
func _draw_page_tab() -> void:
	ring(page_center, 24, false, 1.0, pulses.has("hud:technique_page"))
	var one := str(skill_page + 1)
	var w1 := UiKit.text_width(one, 16)
	var x0 := page_center.x - (w1 + UiKit.text_width("/2", 14)) * 0.5
	UiKit.draw_text(self, one, Vector2(x0, page_center.y + 6), 16, UiKit.PALE_GOLD)
	UiKit.draw_text(self, "/2", Vector2(x0 + w1, page_center.y + 6), 14, UiKit.MIST)

## The fan (decision 20; mockups 01 and 02). Closed: one button with a chevron, lit gold when Cultivate is (the
## bottleneck) or a toggle inside is new; the toggles that are on stand pinned beside it on ring 2. Open: a paper fan
## behind the toggles with their names; in a fight a toggle taken from it folds it again.
func _draw_fan(c) -> void:
	var items := _fan_items()
	if items.is_empty(): return
	var gold: bool = c.cultivator.state == "bottleneck"
	if fan_open:
		_draw_paper_fan(items)
		for f in items:
			var at: Vector2 = f.center
			_draw_toggle(c, str(f.id), at)
			var cap := Tx.t("hud.fan_" + str(f.id))
			var lit: bool = str(f.id) == "cultivate" and gold
			var beside: bool = float(f.deg) < 230.0
			if beside and not left_handed: UiKit.draw_outlined(self, cap, Vector2(at.x - 34 - 160, at.y + 5), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 160)
			elif beside: UiKit.draw_outlined(self, cap, Vector2(at.x + 34, at.y + 5), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 160)
			else: UiKit.draw_outlined(self, cap, Vector2(at.x - 80, at.y - 34), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 160)
		ring(fan_center, 26, false, 1.0, false, true)
	else:
		var fresh := FAN_TOGGLES.any(func(id): return pulses.has("hud:" + str(id)))
		ring(fan_center, 26, false, 1.0, gold or fresh)
		var tip := fan_center + Vector2(0, -30)
		var chev := PackedVector2Array([tip + Vector2(-6, 6), tip + Vector2(6, 6), tip + Vector2(0, -1)])
		draw_colored_polygon(PackedVector2Array([tip + Vector2(-8, 7), tip + Vector2(8, 7), tip + Vector2(0, -3)]), UiKit.INK)
		draw_colored_polygon(chev, UiKit.GOLD if gold else UiKit.PALE_GOLD)
	glyph("fan", fan_center, 32, UiKit.GOLD if gold and not fan_open else Color.WHITE)

## The open fan's paper (mockup 02): a sector behind the toggles with its ribs and a pale rim.
func _draw_paper_fan(items: Array) -> void:
	var d0: float = float(items[0].deg) - 5.0
	var d1: float = maxf(float(items[items.size() - 1].deg) + 7.0, d0 + 40.0)   # a fan of one or two still opens like a fan
	var arc := PackedVector2Array()
	for i in 25: arc.append(_on(fan_center, PAPER_R, lerpf(d0, d1, i / 24.0), true))
	var sector := PackedVector2Array([fan_center]) + arc
	draw_colored_polygon(sector, Color(UiKit.PAPER, 0.13))
	for i in items.size() + 1: draw_line(fan_center, _on(fan_center, PAPER_R, lerpf(d0, d1, float(i) / items.size()), true), Color(UiKit.BRONZE, 0.55), 1.5)
	draw_polyline(sector + PackedVector2Array([fan_center]), Color(UiKit.GOLD, 0.55), 2.0)
	draw_polyline(arc, Color(UiKit.PALE_GOLD, 0.5), 3.0)

## One of the fan's toggles, in the open fan or pinned on ring 2: lit while it is on.
func _draw_toggle(c, id: String, at: Vector2) -> void:
	match id:
		"cultivate":
			var gold: bool = c.cultivator.state == "bottleneck"
			ring(at, 26, c.cultivator.meditating, 1.0, gold or pulses.has("hud:cultivate"), cultivate_pressed)
			if gold: draw_arc(at, 32 + sin(t * 4.0) * 2, 0, TAU, 40, Color(UiKit.GOLD, 0.6), 3)
			glyph("cultivate", at, 32, UiKit.GOLD if gold else Color.WHITE)
			if cultivate_pressed and cultivate_hold > 0.1:
				draw_arc(at, 30, -PI / 2, -PI / 2 + TAU * cultivate_hold / 0.6, 30, UiKit.PALE_GOLD, 3)
		"presence":
			# Held, its Soul upkeep runs round it as an arc (mockup 01); its level in the corner.
			var held: bool = Game.field.is_on(c.id)
			ring(at, 26, held, 1.0, pulses.has("hud:presence"))
			if held and c.pools.max_soul > 0.0: draw_arc(at, 31, -PI / 2, -PI / 2 + TAU * clampf(c.pools.soul / c.pools.max_soul, 0.0, 1.0), 32, UiKit.SOUL, 3)
			glyph("presence", at, 32, UiKit.PALE_GOLD if held else Color.WHITE)
			_corner(at, str(Game.field.presence_level(c)))
		"sphere":
			var raised: bool = Game.field.sphere_on(c.id)
			ring(at, 26, raised, 1.0, pulses.has("hud:sphere"))
			glyph("sphere", at, 32, UiKit.PALE_GOLD if raised else Color.WHITE)
		"sense":
			ring(at, 26, false, 1.0, pulses.has("hud:sense"))
			glyph("sense", at, 32)
		"pet":
			ring(at, 26, false, 1.0, pulses.has("hud:pet"), pet_pressed)
			glyph("pet", at, 32)

## Ring 2 beside the fan: the pinned toggles, the healing slot, the Draught, the treasures, the context or the post chip
## and the weapon swap, each where `_ring2` puts it.
func _draw_ring2(c) -> void:
	for it in _ring2(c):
		var at: Vector2 = it.center
		match str(it.role):
			"quick:0", "quick:1", "quick:2": _draw_quick(c, at, int(str(it.role).right(1)))
			"draught": _draw_draught(c, at)
			"treasure:0", "treasure:1": _draw_treasure(c, int(str(it.role).get_slice(":", 1)), at)
			"context":
				# Decision 42: its own button, at rest as in a fight, lit gold; a harvest's hold runs round it.
				context_center = at
				ring(at, CTX_R, false, 1.0, true)
				glyph(_context_glyph(), at, 32)
				if channel.object != "":
					draw_arc(at, CTX_R - 3.0, -PI / 2, -PI / 2 + TAU * clampf(channel.t / maxf(0.01, channel.dur), 0, 1), 32, UiKit.BRIGHT_JADE, 4)
				var lr := context_label_rect()
				UiKit.draw_outlined(self, UiKit.fit(_context_line(c), 14, lr.size.x, true), Vector2(lr.position.x, lr.position.y + 14), 14, UiKit.PALE_GOLD,
					HORIZONTAL_ALIGNMENT_CENTER, lr.size.x)
			"post":
				context_center = at
				var mine: bool = Game.posts.at_post(c) and str(Game.posts.post_of(c).get("object", "")) == str(context.get("object", ""))
				ring(at, 26, mine, 1.0, pulses.has("hud:post"))
				glyph("post", at, 32, UiKit.BRIGHT_JADE if mine else Color.WHITE)
				UiKit.draw_outlined(self, Tx.t("hud.keep_post"), at + Vector2(-60, 44), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 120)
			"swap": _draw_swap(c, at)
			_: _draw_toggle(c, str(it.get("toggle", "")), at)

## A quest step asks for the healing slot: to put something in it, or to use what it holds (Granny's Remedy).
func _quick_asked(c) -> bool:
	return Game.quest.asks_for(c, "use_system", "set_quick_use") or Game.quest.asks_for(c, "use_item", str(c.inventory.quick_use))

## A quick slot (mockup 01's healing slot; decision 45: three of them): the item at its native 32, how many are left in
## the corner, its own cooldown group's shade. While a quest step asks for the first, it glows and names itself as the
## step does ("Quick-use"); empty, a tap opens the Bag.
func _draw_quick(c, at: Vector2, slot := 0) -> void:
	var qid := str(c.inventory.quick[slot])
	var asked := slot == 0 and _quick_asked(c)
	ring(at, 26, false, 1.0, pulses.has("hud:quick_use") or asked)
	if asked: UiKit.draw_outlined(self, Tx.t("hud.quick_use"), at + Vector2(-50, 44), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 100)
	if qid == "": return
	var n: int = c.inventory.count(qid)
	glyph(qid, at, 32, Color(1, 1, 1, 1.0 if n > 0 else 0.4))
	var def := ContentDB.item(qid)
	var cd: float = c.pools.cooldown("item:" + str(def.get("pill", def.get("food", {})).get("group", "utility")))
	if cd > 0: draw_circle(at, 22, Color(UiKit.INK, 0.5))
	_corner(at, str(n), UiKit.PAPER if n > 0 else UiKit.RED_TEXT)

## S44: the Draught slot, with the minutes left before the liquid goes flat.
func _draw_draught(c, at: Vector2) -> void:
	var dr: Dictionary = c.inventory.draught
	ring(at, 26)
	glyph(str(dr.id), at, 32)
	var left: float = Game.inventory.draught_left(c)
	draw_arc(at, 29, -PI / 2, -PI / 2 + TAU * left / float(ContentDB.item(str(dr.id)).get("draught", {}).get("expires_s", 600)), 32, UiKit.BRIGHT_JADE, 3)
	_corner(at, str(int(dr.count)))

func _draw_treasure(c, ti: int, at: Vector2) -> void:
	var tid := _treasure_id(c, ti)
	ring(at, 26, false, 1.0, pulses.has("hud:treasure_%d" % (ti + 1)))
	if tid == "": return
	var tdef: Dictionary = CombatAuthority.treasure_of(tid)
	var short: bool = c.pools.qi < float(tdef.get("qi", 0)) or c.pools.soul < CombatAuthority.treasure_soul_cost(c, tdef)
	glyph(tid, at, 32, Color(1, 1, 1, 0.4 if short else 1.0))
	var tcd: float = c.pools.cooldown("treasure:" + tid)
	if tcd > 0.05:
		_sweep(at, 24.0, clampf(tcd / maxf(1.0, float(tdef.get("cooldown_s", 20))), 0.0, 1.0))
		UiKit.draw_outlined(self, str(int(ceil(tcd))), at + Vector2(-20, 7), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 40)
	if tdef.has("charges"):
		# A talisman treasure shows the charges it has left.
		var ti_bag: int = c.inventory.first_index(tid)
		_corner(at, "×%d" % (int(c.inventory.bag[ti_bag].get("charges", int(tdef.charges))) if ti_bag >= 0 else 0), UiKit.PALE_GOLD)

## S47: the spare weapon's icon under two turning arrows, and which loadout is in hand.
func _draw_swap(c, at: Vector2) -> void:
	var spare = c.inventory.loadout.get("spare")
	ring(at, 26, false, 1.0, pulses.has("hud:weapon_swap"))
	if spare != null: glyph(str(spare.id), at, 32, Color(1, 1, 1, 0.9))
	for side in [-1.0, 1.0]:
		draw_arc(at, 21, PI * (0.15 if side > 0 else 1.15), PI * (0.75 if side > 0 else 1.75), 10, Color(UiKit.PALE_GOLD, 0.9 if spare != null else 0.35), 2.0)
	UiKit.draw_outlined(self, str(c.inventory.loadout.get("active", "a")).to_upper(), at + Vector2(10, 27), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 20)

## The progress edge (mockups 01, 02): the stage's progress along the foot with a stop at each Level; at the
## bottleneck it glows gold, Stored Qi runs as a bright lane along it and the line above says the breakthrough is ready.
func _draw_progress(c) -> void:
	var cu: CultivatorState = c.cultivator
	var r := Rect2(0, 712, 1280, 8)
	var frac := cu.progress_fraction()
	var realm := ContentDB.realm(cu.realm_key)
	var levels := int(realm.get("levels", 1))
	var base := int(realm.get("level", 0))
	var lv := ProgressionRules.level(c)
	if cu.state == "bottleneck":
		draw_polygon(PackedVector2Array([Vector2(0, 660), Vector2(1280, 660), Vector2(1280, 712), Vector2(0, 712)]),
			PackedColorArray([Color(UiKit.GOLD, 0.0), Color(UiKit.GOLD, 0.0), Color(UiKit.PALE_GOLD, 0.3), Color(UiKit.PALE_GOLD, 0.3)]))
		draw_rect(Rect2(0, 710, 1280, 10), UiKit.GOLD)
		draw_rect(Rect2(0, 710, 1280, 3), UiKit.PALE_GOLD)
		if cu.stored_qi > 0: draw_rect(Rect2(0, 710, 1280 * clampf(cu.stored_qi / maxf(1.0, cu.need()), 0, 1), 3), UiKit.PAPER)
		for k in range(1, levels): draw_rect(Rect2(1280.0 * k / levels - 1, 706, 2, 14), UiKit.INK)
		var x := 16.0
		if cu.stored_qi > 0:
			var sq := Tx.t("hud.stored_qi") % UiKit.fmt(cu.stored_qi)
			UiKit.draw_outlined(self, sq, Vector2(x, 700), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 200)
			x += UiKit.text_width(sq, 14, true) + 24.0
		var ready := Tx.t("hud.bottleneck_ready")
		UiKit.draw_outlined(self, ready, Vector2(x, 700), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 520)
		UiKit.draw_outlined(self, Tx.t("hud.bottleneck_tap"), Vector2(x + UiKit.text_width(ready, 16, true) + 6.0, 700), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 240)
		return
	draw_rect(r, Color(UiKit.INK, 0.6))
	var col = UiKit.QI if c.pools.max_qi > 0 else UiKit.PALE_GOLD
	var fx := r.size.x * frac
	draw_rect(Rect2(r.position, Vector2(fx, r.size.y)), col)
	if cu.stored_qi > 0:
		draw_rect(Rect2(0, 710, 1280 * clampf(cu.stored_qi / maxf(1.0, cu.need()), 0, 1), 2), UiKit.PALE_GOLD)
	for k in range(1, levels):
		var sx := 1280.0 * k / levels
		draw_rect(Rect2(sx - 2, 707, 4, 13), UiKit.INK)
		draw_rect(Rect2(sx - 1, 708, 2, 12), UiKit.PALE_GOLD)
		UiKit.draw_outlined(self, Tx.t("hud.level_stop") % (base + k), Vector2(sx - 40, 700), 14, UiKit.PALE_GOLD if base + k == lv + 1 else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 80)
	var pct := "%d%%" % int(frac * 100.0)
	if fx >= 56.0: UiKit.draw_outlined(self, pct, Vector2(fx - 86, 700), 14, col, HORIZONTAL_ALIGNMENT_RIGHT, 80)
	else: UiKit.draw_outlined(self, pct, Vector2(fx + 6, 700), 14, col, HORIZONTAL_ALIGNMENT_LEFT, 80)

func _draw_log() -> void:
	# Above the joystick's half (mockup 01), newest at the foot, outlined, and kept out of the clear zone. Before the log
	# is revealed only the lines that must reach the player (what a consumable did) are drawn.
	var x := 20.0 if not left_handed else 1280.0 - 20.0 - LOG_W
	var lines := log_lines if shown("system_log") else log_lines.filter(func(l): return l.get("always", false))
	var rows := log_rows(lines)
	var n := rows.size()
	for i in n:
		var r: Dictionary = rows[i]
		var col: Color = r.color
		UiKit.draw_outlined(self, str(r.text), Vector2(x + float(r.indent), LOG_FOOT - (n - 1 - i) * 21.0), 16, col, HORIZONTAL_ALIGNMENT_LEFT, LOG_W - float(r.indent))

## The log's rows, newest at the foot: a line longer than the log's width wraps onto a second row, indented (only a
## third row's worth ends in "…"; the prototype's QA read "A drop of blood on Plain Straw Hat: it knows…"), and the
## oldest rows give way so the log never grows past LOG_ROWS toward the tracker.
const LOG_ROWS := 6
const LOG_INDENT := 14.0
func log_rows(lines: Array) -> Array:
	var out: Array = []
	for l in lines:
		var a = 1.0 if float(l.t) < 5.0 else 6.0 - float(l.t)
		var col := Color(l.color, a)
		var text := str(l.text)
		var first := str(UiKit.wrap(text, 16, LOG_W, true)[0])
		out.append({"text": UiKit.fit(first, 16, LOG_W, true), "indent": 0.0, "color": col})
		var rest := text.substr(first.length()).strip_edges()
		if rest != "": out.append({"text": UiKit.fit(rest, 16, LOG_W - LOG_INDENT, true), "indent": LOG_INDENT, "color": col})
	return out.slice(maxi(0, out.size() - LOG_ROWS))

## The top centre (P5a), one thing under another so none covers another, from under the party chips (or under the boss
## bar) down to the clear zone: the room's name as you enter, a room event or a tribulation under way, a fortune card,
## the toasts (408 wide, 8 apart; a toast with no room waits), a caption.
func _draw_top_stack(c) -> void:
	var y := TOP_STACK_BOSS if _boss() != null else TOP_STACK
	y = _draw_run_banner(c, y)
	if not _band_on_top():   # a moment's band there says the same, and the two drawn together read as neither
		y = _draw_banner(y)
		y = _draw_event(c, y)
	y = _draw_tribulation(c, y)
	y = _draw_vignette(y)
	y = _draw_toasts(y)
	_draw_caption(y)

func _draw_banner(y: float) -> float:
	if banner.text == "" or banner.t > 3.4 or not shown("room_banner"): return y
	var a := clampf(banner.t / 0.3, 0, 1) * clampf((3.4 - banner.t) / 0.5, 0, 1)
	var slide := (1.0 - clampf(banner.t / 0.3, 0, 1)) * -12.0
	UiKit.draw_text(self, str(banner.text), Vector2(340, y + 32 + slide), 34, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_CENTER, 600, true, true)
	if str(banner.sub) != "": UiKit.draw_text(self, str(banner.sub), Vector2(340, y + 56 + slide), 16, Color(UiKit.MIST, a), HORIZONTAL_ALIGNMENT_CENTER, 600)
	return y + 68.0

## A fortune encounter (S49): a card that fades in under the room banner, long enough to read, then fades away.
const VIGNETTE_S := 9.0
func _draw_vignette(y0: float) -> float:
	if str(vignette.title) == "" or float(vignette.t) > VIGNETTE_S: return y0
	var tv := float(vignette.t)
	var a := clampf(tv / 0.4, 0, 1) * clampf((VIGNETTE_S - tv) / 0.8, 0, 1)
	var w := 560.0
	var lines: Array = []
	var cur := ""
	for word in str(vignette.text).split(" "):
		var cand: String = word if cur == "" else cur + " " + word
		if UiKit.text_width(cand, 18) > w - 48 and cur != "":
			lines.append(cur)
			cur = word
		else: cur = cand
	lines.append(cur)
	var r := Rect2(640 - w / 2.0, y0, w, 86 + lines.size() * 23)
	draw_style_box(UiKit.style("toast"), r)
	draw_rect(Rect2(r.position + Vector2(0, 0), Vector2(r.size.x, 3)), Color(UiKit.GOLD, 0.8 * a))
	UiKit.draw_text(self, Tx.t("hud.fortune_label"), r.position + Vector2(24, 30), 14, Color(UiKit.GOLD, a))
	UiKit.draw_text(self, str(vignette.title), r.position + Vector2(24, 58), 22, Color(UiKit.PALE_GOLD, a), HORIZONTAL_ALIGNMENT_LEFT, w - 48, true, true)
	var y := r.position.y + 86
	for ln in lines:
		UiKit.draw_text(self, str(ln), Vector2(r.position.x + 24, y), 18, Color(UiKit.PAPER, a))
		y += 23
	return r.end.y + 8.0

func _moment_on_screen() -> bool:
	return is_instance_valid(moments) and moments.screen_busy()

func _band_on_top() -> bool:
	return is_instance_valid(moments) and moments.band_on_top()

## Toasts at the top centre (docs/mockups/20_states: over play, under the chips), 408 wide and 8 apart. The first always
## shows; the next only while it stays above the clear zone, and the rest wait their turn.
func _draw_toasts(y: float) -> float:
	toasts_fit = 0
	if _moment_on_screen(): return y
	for r in toast_rects(y):
		var tt: Dictionary = toasts[toasts_fit]
		var sub := str(tt.get("sub", ""))
		var a := clampf(tt.t / 0.2, 0, 1) * clampf((float(tt.get("life", 3.2)) - tt.t) / 0.4, 0, 1)
		draw_style_box(UiKit.style("toast"), r)
		var col = UiKit.PALE_GOLD if tt.kind in ["unlock", "gold"] else (UiKit.RED_TEXT if tt.kind == "danger" else UiKit.BRIGHT_JADE)
		UiKit.draw_text(self, UiKit.fit(str(tt.text), 20, 376), r.position + Vector2(16, 31), 20, Color(col, a), HORIZONTAL_ALIGNMENT_LEFT, 376)
		var row_y := 58.0
		for row in toast_sub_rows(sub):
			UiKit.draw_text(self, str(row), r.position + Vector2(16, row_y), 18, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_LEFT, 376)
			row_y += TOAST_ROW
		y = r.end.y + 8.0
		toasts_fit += 1
	return y

## A toast's second line, wrapped to two rows at most (a spar's lesson, said whole), the second cut if it must be.
const TOAST_ROW := 22.0
static func toast_sub_rows(sub: String) -> Array:
	if sub == "": return []
	var rows: Array = UiKit.wrap(sub, 18, 376)
	if rows.size() <= 1: return [UiKit.fit(sub, 18, 376)]
	var first := str(rows[0])
	return [first, UiKit.fit(sub.substr(first.length()).strip_edges(), 18, 376)]

## Where the toasts stand from `y` down: the first always, each next only while it ends above the clear zone.
func toast_rects(y: float) -> Array:
	var out: Array = []
	for tt in toasts:
		var rows := toast_sub_rows(str(tt.get("sub", ""))).size()
		var h := 48.0 if rows == 0 else 74.0 + TOAST_ROW * (rows - 1)
		if not out.is_empty() and y + h > CLEAR_ZONE.position.y: break
		out.append(Rect2(436, y, 408, h))
		y += h + 8.0
	return out

func _draw_caption(y: float) -> void:
	if caption.text == "" or float(caption.t) > 2.6: return
	var a := clampf((2.6 - float(caption.t)) / 0.4, 0.0, 1.0)
	var w := 520.0
	draw_rect(Rect2(640 - w / 2.0, y, w, 30), Color(UiKit.INK, 0.55 * a))
	UiKit.draw_text(self, "[" + str(caption.text) + "]", Vector2(640 - w / 2.0, y + 21), 18, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_CENTER, w)

## The boss in the room, if one lives (with two, the one furthest into the fight: the lowest share of its HP).
func _boss() -> EnemyState:
	if Game.room_rt == null: return null
	var boss: EnemyState = null
	for e in Game.room_rt.enemies.values():
		if e.alive and e.is_boss() and e.team == "enemy" and (boss == null or e.pools.hp / maxf(1.0, e.pools.max_hp) < boss.pools.hp / maxf(1.0, boss.pools.max_hp)): boss = e
	return boss

## The boss bar (mockup 01): the name in the display face with its Level and phase, an ember fill on a dark trough, a
## notch at each phase's share of HP (gold once passed, the next one lit) with what it brings under it, and the share
## left on the bar.
func _draw_boss() -> void:
	var boss := _boss()
	if boss == null: return
	var r := Rect2(400, 130, 480, 18)
	var phases: Array = boss.def.get("phases", [])
	var at := int(boss.ai.get("phase", -1))
	var frac := clampf(boss.pools.hp / maxf(1.0, boss.pools.max_hp), 0.0, 1.0)
	var name_s := boss.display_name()
	var sub := Tx.t("hud.boss_phase") % [boss.level, at + 2, phases.size() + 1] if not phases.is_empty() else Tx.t("hud.level_stop") % boss.level
	var nw := UiKit.text_width(name_s, 26, true)
	var x0 := 640.0 - (nw + 10.0 + UiKit.text_width(sub, 16, true)) * 0.5
	UiKit.draw_text(self, name_s, Vector2(x0, 118), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true, true)
	UiKit.draw_outlined(self, sub, Vector2(x0 + nw + 10.0, 117), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 240)
	draw_rect(r.grow(3), UiKit.INK)
	draw_rect(r, Color(UiKit.BLOOD, 0.3))
	var last := 0.0
	for ph in phases:
		if ph.has("below"): last = float(ph.below) if last == 0.0 else minf(last, float(ph.below))
	if last > 0.0: draw_rect(Rect2(r.position, Vector2(r.size.x * last, r.size.y)), Color(UiKit.BLOOD, 0.35))
	var fw := r.size.x * frac
	if fw > 0.5:
		var top := UiKit.WARNING.lerp(UiKit.PALE_GOLD, 0.2)
		var mid := UiKit.WARNING.lerp(UiKit.RED, 0.5)
		var low := UiKit.RED.lerp(UiKit.BRONZE, 0.45)
		var ym := r.position.y + r.size.y * 0.55
		draw_polygon(PackedVector2Array([r.position, r.position + Vector2(fw, 0), Vector2(r.position.x + fw, ym), Vector2(r.position.x, ym)]), PackedColorArray([top, top, mid, mid]))
		draw_polygon(PackedVector2Array([Vector2(r.position.x, ym), Vector2(r.position.x + fw, ym), r.end - Vector2(r.size.x - fw, 0), Vector2(r.position.x, r.end.y)]), PackedColorArray([mid, mid, low, low]))
		draw_line(r.position + Vector2(1, 2), r.position + Vector2(maxf(1.0, fw - 1.0), 2), Color(UiKit.PALE_GOLD, 0.45), 2)
	# Decision 45: a boss that cannot be beaten yet (the first boss awake) shows what its hide holds: the bar under its
	# floor hatched over in stone, the floor's edge marked, and the word under it; blows that reach it glance off.
	var hide := float(boss.ai.get("hp_floor", 0.0))
	if hide > 0.0:
		var hw := r.size.x * hide
		draw_rect(Rect2(r.position, Vector2(hw, r.size.y)), Color(UiKit.INK, 0.5))
		for k in range(0, int(hw) - 4, 7):
			draw_line(Vector2(r.position.x + k, r.end.y - 1), Vector2(r.position.x + k + 6, r.position.y + 1), Color(UiKit.MIST, 0.4), 1.0)
		draw_rect(Rect2(r.position.x + hw - 1.5, r.position.y - 4, 3, r.size.y + 8), UiKit.MIST)
		UiKit.draw_outlined(self, Tx.t("hud.boss_hide"), Vector2(r.position.x, 172), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, hw - 8.0)
	UiKit.draw_outlined(self, "%d%%" % int(round(frac * 100.0)), Vector2(r.position.x, r.position.y + 15), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	# The notches, and under each what the phase brings: the next one's caption always, the others where they fit.
	var nxt := -1
	for i in phases.size():
		if i > at and phases[i].has("below"):
			nxt = i
			break
	var taken: Array = []
	var order: Array = range(phases.size())
	if nxt >= 0:
		order.erase(nxt)
		order.push_front(nxt)
	for i in order:
		var ph: Dictionary = phases[i]
		if not ph.has("below"): continue
		var x := r.position.x + r.size.x * float(ph.below)
		var done: bool = int(i) <= at
		draw_rect(Rect2(x - 2.5, r.position.y - 9, 5, 36), UiKit.INK)
		draw_rect(Rect2(x - 1.5, r.position.y - 8, 3, 34), UiKit.PALE_GOLD)
		var dia := PackedVector2Array([Vector2(x, r.position.y - 16), Vector2(x + 6, r.position.y - 10), Vector2(x, r.position.y - 4), Vector2(x - 6, r.position.y - 10)])
		if i == nxt: draw_circle(Vector2(x, r.position.y - 10), 9.0, Color(UiKit.RED, 0.35))
		draw_colored_polygon(dia, UiKit.GOLD if done else (UiKit.RED if i == nxt else UiKit.DEEP_TEAL))
		draw_polyline(dia + PackedVector2Array([dia[0]]), UiKit.PALE_GOLD, 1.5)
		var cap := Tx.t("hud.boss_notch") % [int(round(float(ph.below) * 100.0)), _phase_words(ph, done)]
		var cw := UiKit.text_width(cap, 14, true)
		# Centred under its notch, or leaning away from a caption already there (ending at the notch, or starting at it).
		for left in [x - cw * 0.5, x + 10.0 - cw, x - 10.0]:
			var cr := Rect2(left - 4.0, 158, cw + 8.0, 18)
			if taken.any(func(o): return (o as Rect2).intersects(cr)): continue
			taken.append(cr)
			UiKit.draw_outlined(self, cap, Vector2(left, 172), 14, UiKit.PALE_GOLD if i == nxt else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw + 4.0)
			break

## What a boss's phase brings, in a few words (a summons names who comes, and is ticked once it has come).
func _phase_words(ph: Dictionary, done: bool) -> String:
	var act := str(ph.get("action", ""))
	if act == "summon":
		var who := str(ph.get("summon", ""))
		if who == "": return Tx.t("hud.phase_help")
		return (Tx.t("hud.phase_summoned") if done else Tx.t("hud.phase_summon")) % ContentDB.name_of("enemies", who)
	if act in ["enrage", "dig_in", "drink_wine", "self_detonate", "awaken"]: return Tx.t("hud.phase_" + act)
	return Tx.t("hud.phase_turn")

## A room event under way (a survival rite, a Temper trial, a siege): its name, the time left and its rule.
func _draw_event(c, y0: float) -> float:
	if Game.room_rt == null or not Game.room_rt.event.get("active", false): return y0
	var ev: Dictionary = Game.room_rt.event
	var rule := ""
	var danger := false
	if float(ev.get("hp_floor", 0.0)) > 0.0:
		rule = Tx.t("hud.event_rule.hp_floor") % int(round(float(ev.hp_floor) * 100))
		danger = c.pools.hp < c.pools.max_hp * (float(ev.hp_floor) + 0.1)
	if not (ev.get("kill_count", {}) as Dictionary).is_empty():
		var foe := Tx.t("hud.event_rule.foes") if str(ev.kill_count.enemy) == "*" else str(ContentDB.entry("enemies", str(ev.kill_count.enemy)).get("name", ""))
		rule = Tx.t("hud.event_rule.kills") % [foe, int(ev.get("kills", 0)), int(ev.kill_count.get("count", 1))]
	elif str(ev.get("win_on_kill", "")) != "" and ev.has("floor"):
		rule = Tx.t("hud.event_rule.guardian") % ContentDB.name_of("enemies", str(ev.win_on_kill))
	elif ev.has("floor"):
		rule = Tx.t("hud.event_rule.survive")
	if ev.has("ground_grace_s"):
		rule = Tx.t("hud.event_rule.ground")
		danger = float(ev.get("ground_s", 0.0)) > 0.0
	# v1.2 the lantern defence: the lantern's light, and a warning when it gutters.
	if ev.get("lantern") is Dictionary and not ev.lantern.is_empty():
		var light := float(ev.get("light", 100.0))
		rule = Tx.t("hud.event_rule.lantern") % int(ceil(light))
		danger = light < 35.0
	var r := Rect2(470, y0, 340, 52 if rule != "" else 34)
	draw_style_box(UiKit.style("toast"), r)
	var left := maxf(0.0, float(ev.get("remaining", 0.0)))
	var ev_name := Tx.t("hud.tower_floor") % int(ev.floor) if ev.has("floor") else ContentDB.text("event." + str(ev.get("id", "")))
	UiKit.draw_text(self, ev_name, r.position + Vector2(14, 23), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 240)
	# Decision 45: an event whose time is only a last resort (`clock: false`, the Hollow Night: it ends when its boss
	# falls) shows no countdown, which would read as a time to hold out for.
	if ev.get("clock", true):
		UiKit.draw_text(self, UiKit.clock(left), r.position + Vector2(r.size.x - 84, 23), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 70)
		var frac := left / maxf(1.0, float(ev.get("duration", 1.0)))
		draw_rect(Rect2(r.position + Vector2(12, 29), Vector2(r.size.x - 24, 3)), Color(UiKit.INK, 0.8))
		draw_rect(Rect2(r.position + Vector2(12, 29), Vector2((r.size.x - 24) * clampf(frac, 0, 1), 3)), UiKit.BRIGHT_JADE)
	if rule != "": UiKit.draw_text(self, rule, r.position + Vector2(14, 46), 14, UiKit.RED_TEXT if danger else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
	return r.end.y + 8.0

## S48 heavenly tribulation: bolts struck and to come, and whether a ring is closing now.
func _draw_tribulation(c, y0: float) -> float:
	var tv: Dictionary = Game.progression.tribulation_view(c.id)
	if tv.is_empty(): return y0
	var r := Rect2(470, y0, 340, 52)
	draw_style_box(UiKit.style("toast"), r)
	UiKit.draw_text(self, Tx.t("hud.tribulation_title"), r.position + Vector2(14, 23), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 200)
	UiKit.draw_text(self, Tx.t("hud.tribulation_count") % [int(tv.index), int(tv.total)], r.position + Vector2(r.size.x - 144, 23), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 130)
	var n := int(tv.total)
	var w := (r.size.x - 28) / maxf(1.0, float(n))
	for i in n:
		var cell := Rect2(r.position.x + 14 + i * w, r.position.y + 32, maxf(2.0, w - 2), 6)
		draw_rect(cell, UiKit.SKY if i < int(tv.index) else (UiKit.GOLD if i == int(tv.index) and not (tv.warn as Dictionary).is_empty() else Color(UiKit.INK, 0.8)))
	if not (tv.warn as Dictionary).is_empty():
		UiKit.draw_text(self, Tx.t("hud.tribulation_move"), r.position + Vector2(14, 51), 16, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 28)
		return r.end.y + 16.0
	return r.end.y + 8.0

## With no character bound (the engine tests' bare player), a plain panel and the cluster's rings.
func _draw_legacy() -> void:
	draw_style_box(frame_style, Rect2(22, 22, 310, 82))
	for row in 2:
		var y = 40 + row * 32
		var amount = player.hp if row == 0 else player.qi
		UiKit.draw_text(self, Tx.t("hud.hp") if row == 0 else Tx.t("hud.qi"), Vector2(38, y + 13), 18, UiKit.HUD_LABEL)
		draw_rect(Rect2(75, y, 237, 16), UiKit.BAR_TROUGH)
		draw_rect(Rect2(77, y + 2, 233 * amount / 100, 12), UiKit.HP if row == 0 else UiKit.QI)
	draw_skill_scroll()
	ring(attack_center, 66, player.attack_time > 0)
	ring(jump_center, JUMP_R)
	ring(fan_center, 26, player.meditating)
