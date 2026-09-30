class_name TutorialCoach
extends Control
## Decision 43 · the coach (docs/redesign/tutorials.md): every newly unlocked system teaches itself. Over the HUD and the
## pages (its own canvas layer, under the fade), it shows what data/tutorials.json says, where the Tutorial authority's
## queue has come to:
##   - a guide: a hand and a pulsing ring (with a "!" badge on a HUD button) on the next thing to tap, from the HUD
##     button (or a place in the world, with the direction mark leading there) to the page, its tab and the element,
##     each step found from what is on screen (TutorialRules.chain_step), with a small card and Later;
##   - a tour: the screen dimmed but for a spotlight on each anchor in turn, a card with the line, Next and Skip; a step
##     with a "try it" lets taps through its spotlight and moves on when it is done.
## It never starts or shows in a fight, a staged scene, a moment or a talk; it waits. One tour plays an opening of a
## page, one guide at a time. Anchors are names the pages and the HUD give (Page.tour_rect, HUD.tour_rect), never node
## paths. Progress goes to the authority through intents (tutorial_step, tutorial_done, tutorial_replay), so it is saved
## per character and resumes after a reload. A tour played again from a page's "?" is not recorded.

const CARD_W := 560.0         ## a tour's card
const TEXT := 20              ## the card's line (UiKit.T_BODY), at most two lines on a phone
const TEXT_W := CARD_W - 48.0
const BTN_W := 136.0
const BTN_H := 48.0
const PAD := 20.0
const MISSING_S := 0.4        ## an anchor not found this long: the card stands alone, in the middle
const HIDE_ON := ["dialogue", "gift", "revival", "fates", "mercy", "welcome"]   ## talks and events: the coach waits
const HAND := ["....##......", "...#WW#.....", "...#WW#.....", "...#WW#.....", "...#WW###...", "...#WW#WW##.", ".###WW#WW#W#",
	"#WW#WWWWWWW#", "#WWWWWWWWWW#", "#WWWWWWWWWW#", ".#WWWWWWWWW#", ".#WWWWWWWW#.", "..#WWWWWWW#.", "...#WWWWW#..", "...#SSSSS#..", "...#######.."]
const HAND_K := 3.0           ## screen px an art px (nearest neighbour)

var main: Node = null         ## the shell (main.gd): its screen, pages, HUD, world and scenes
var mode := ""                ## "", "guide" or "tour"
var entry_id := ""            ## the entry shown
var step := 0                 ## its step (the chain's or the tour's)
var on_hud := false           ## the anchor is the HUD's
var target := Rect2()         ## the anchor on screen now (Rect2() when not found)
var card := Rect2()
var buttons: Dictionary = {}  ## "next", "skip", "later" -> Rect2
var line := ""                ## the card's words now
var why_hidden := ""          ## what the coach waits on ("combat", "scene", "moment", "dialogue", …; "" when free)
var replay := ""              ## a tour played again from "?" (not saved) …
var replay_step := 0
var replay_page: Page = null  ## … on this opening of its page
var t := 0.0
var _missing := 0.0
var _toured: Dictionary = {}  ## page instance id -> true: a tour played (or was skipped) on that opening
var _tried := false           ## the step's try-it was done
var _tab_was := ""
var _hand: ImageTexture = null       ## the finger up (under the anchor)
var _hand_down: ImageTexture = null  ## the finger down (over it)
var _pressed := ""
var _in_hole := false
var _goal := ""               ## the room the direction mark was asked to lead to (tutorial_goal)
var control := false          ## the guide points at a HUD power's own control: a tap there plays its tour (_control_live)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	GameEvents.event.connect(_on_game_event)
	_hand = _hand_texture(false)
	_hand_down = _hand_texture(true)

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_game_event): GameEvents.event.disconnect(_on_game_event)

## The pointing hand, drawn from HAND (ink edge, paper hand, a jade sleeve), its finger up or turned down.
static func _hand_texture(down: bool) -> ImageTexture:
	var img := Image.create(HAND[0].length(), HAND.size(), false, Image.FORMAT_RGBA8)
	for y in HAND.size():
		for x in (HAND[y] as String).length():
			var ch := (HAND[y] as String)[x]
			if ch == "#": img.set_pixel(x, y, UiKit.INK)
			elif ch == "W": img.set_pixel(x, y, UiKit.PAPER)
			elif ch == "S": img.set_pixel(x, y, UiKit.JADE)
	if down: img.flip_y()
	return ImageTexture.create_from_image(img)

# ------------------------------------------------------------------ what shows
func _process(delta: float) -> void:
	t += delta
	var was := mode
	_update(delta)
	if mode != "" or was != "": queue_redraw()

## The character's state and what is on screen decide what shows, every frame.
func _update(delta: float) -> void:
	var c = Game.active()
	var top: Page = main.top_page() if main != null and main.has_method("top_page") else null
	if main == null or str(main.get("screen")) != "world" or c == null:
		_show("", "", 0)
		return
	why_hidden = blocked(c)
	if why_hidden != "":
		_show("", "", 0)
		return
	var pid := top.page_id if top != null else ""
	var tab := top.tab_id() if top != null else ""
	# 1. A tour played again from the page's "?" (or Settings), while its page stays open.
	if replay != "":
		if top != null and top == replay_page:
			_show("tour", replay, replay_step)
			_resolve(delta)
			return
		replay = ""
	var head: String = Game.tutorials.head(c)
	var he := TutorialRules.entry(head)
	# 2. The head guide at its element on this page (the node to spend on): before the page's own tour. (A HUD power's
	# guide is its lesson's, step 4.)
	if head != "" and top != null and not TutorialRules.hud_entry(he) and TutorialRules.chain_home(he, pid, tab) and _element_step(he):
		_show("guide", head, (he.chain as Array).size() - 1)
		_resolve(delta)
		return
	# A guide whose page (and tab) is open now is done, whether it led there or the player came first: its tour, if
	# unseen, plays next.
	if top != null:
		for q in (c.tutorials.get("queue", []) as Array).duplicate():
			if _arrived(TutorialRules.entry(str(q)), pid, tab): Game.submit({"type": "tutorial_done", "id": str(q), "stage": "guide"})
		head = Game.tutorials.head(c)
		he = TutorialRules.entry(head)
	# 3. A tour of the page on top: one in progress, else an unseen one on its first opening.
	if top != null:
		var tour := _page_tour(c, top, pid, tab)
		if tour != "":
			_show("tour", tour, Game.tutorials.step_of(c, tour))
			_resolve(delta)
			return
	# 4. The head guide: a HUD control's lesson (its tour with no page open, and a HUD power's guide round it), else the
	# chain's step for what is on screen.
	if head != "":
		if TutorialRules.hud_entry(he):
			if _hud_lesson(c, he, top, pid, tab, delta): return
		else:
			var i := TutorialRules.chain_step(he, pid, tab)
			if i >= 0:
				_show("guide", head, i)
				_resolve(delta)
				return
	_show("", "", 0)

## Why the coach waits now ("" when it may show): not in a fight (a foe near or blows traded), a staged scene, a
## moment, a talk or an event page, a page's own question, or the game held still.
func blocked(c) -> String:
	var hud = main.get("hud")
	if Game.paused: return "paused"
	if Game.combat.in_combat(c): return "combat"
	if is_instance_valid(hud) and hud.bound() and hud.fight: return "combat"
	if is_instance_valid(hud) and (hud.scene_lock or hud.moment_lock): return "scene" if hud.scene_lock else "moment"
	var sd = main.get("scenes")
	if is_instance_valid(sd) and sd.get("run") != null: return "scene"
	for p in main.get("pages"):
		if is_instance_valid(p) and str(p.page_id) in HIDE_ON: return "dialogue"
	var top: Page = main.top_page()
	if top != null and not top.confirm.is_empty(): return "confirm"
	if top != null and not top.tour_ready(): return "busy"
	return ""

## The chain ends on an element of the entry's own page to use (the node to spend on), not only at the page.
func _element_step(e: Dictionary) -> bool:
	var chain: Array = e.get("chain", [])
	return not chain.is_empty() and bool((chain.back() as Dictionary).get("element", false))

## A guide has come home: its page is on top, on its tab when it names one, and it has no element step left to show. A
## HUD power's comes home once its tour is seen and the page (and tab) that manages the power is open.
func _arrived(e: Dictionary, pid: String, tab: String) -> bool:
	if e.is_empty() or _element_step(e): return false
	if TutorialRules.hud_entry(e):
		var goal := TutorialRules.chain_goal(e)
		return not goal.is_empty() and Game.tutorials.seen(Game.active(), str(e.id)) and TutorialRules.same_page(pid, str(goal[0])) \
			and (str(goal[1]) == "" or str(goal[1]) == tab)
	return TutorialRules.same_page(pid, str(e.get("page", ""))) and (str(e.get("tab", "")) == "" or str(e.tab) == tab)

## A HUD control's lesson, at the head of the queue (decision 44 for the late powers). Its tour plays on the play screen
## (no page open) once started, or at once when no control step comes first (TutorialRules.tour_at). Before that, the
## guide leads to the control and points at it: a tap there plays the tour (_control_live). After the tour, the guide
## leads on to the page that manages the power. Returns whether something shows.
func _hud_lesson(c, e: Dictionary, top: Page, pid: String, tab: String, delta: float) -> bool:
	var id := str(e.id)
	var toured: bool = Game.tutorials.seen(c, id)
	if not toured and (Game.tutorials.in_progress(c, id) or TutorialRules.tour_at(e) < 0):
		if top != null: return false
		_show("tour", id, Game.tutorials.step_of(c, id))
		_resolve(delta)
		return true
	var at := TutorialRules.tour_at(e)
	var control_on := at >= 0 and top == null and _find(str(((e.chain as Array)[at] as Dictionary).get("anchor", "")), true).size != Vector2.ZERO
	var i := TutorialRules.lesson_step(e, pid, tab, toured, control_on)
	if i < 0: return false
	_show("guide", id, i)
	_resolve(delta)
	return true

## The guide's hand is on a HUD power's own control (not the fan that holds it): a tap there plays its tour. Found once
## a frame (_resolve).
func _control_live() -> bool:
	if mode != "guide" or not current().get("tour", false) or target.size == Vector2.ZERO or main == null: return false
	var hud = main.get("hud")
	var first := str(current().get("anchor", "")).get_slice("|", 0)
	return is_instance_valid(hud) and hud.tour_rect(first).size != Vector2.ZERO

## The tour to show on the page on top: one in progress on this page, else the first unseen one for it and its tab, if
## no tour has played on this opening yet.
func _page_tour(c, top: Page, pid: String, tab: String) -> String:
	for e in TutorialRules.entries():
		var id := str(e.id)
		if Game.tutorials.in_progress(c, id) and not Game.tutorials.seen(c, id) and TutorialRules.same_page(str(e.get("page", "")), pid):
			return id
	# One tour an opening; none by itself while every system is forced open (the Max Tester, previews): the "?" still plays.
	if _toured.has(top.get_instance_id()) or Unlocks.debug_force_all: return ""
	for id in TutorialRules.tours_for(pid, tab):
		if Game.tutorials.seen(c, str(id)): continue
		# A tab's own tour waits for its system (a craft's tab shows only why it is shut until then).
		var e := TutorialRules.entry(str(id))
		var gate := str(e.get("trigger", {}).get("unlock", ""))
		if str(e.get("tab", "")) != "" and gate != "" and not Unlocks.is_unlocked(c.id, gate): continue
		return str(id)
	return ""

func _show(m: String, id: String, i: int) -> void:
	if m != mode or id != entry_id or i != step:
		_tried = false
		_missing = 0.0
		_pressed = ""
	# A tour dimming the play screen takes the controls: whatever the thumbs held (the stick, a guard) is let go.
	if m == "tour" and mode != "tour" and main != null and main.top_page() == null:
		var hud = main.get("hud")
		if is_instance_valid(hud): hud.notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	mode = m
	entry_id = id
	step = i
	# A "go to the place" step leads the direction mark (and the World map's lantern) there while it shows.
	var goal := ""
	if m == "guide":
		var st := current()
		if str(st.get("at", "")) == "place": goal = str(spot(st).get("room", ""))
	if goal != _goal and Game.active() != null:
		_goal = goal
		Game.submit({"type": "tutorial_goal", "room": goal})
	if m == "":
		target = Rect2()
		card = Rect2()
		buttons = {}
		line = ""
		control = false

## The step's data: a tour step, or the chain's step.
func current() -> Dictionary:
	var e := TutorialRules.entry(entry_id)
	if e.is_empty(): return {}
	var list: Array = e.get("tour", []) if mode == "tour" else e.get("chain", [])
	return list[step] if step >= 0 and step < list.size() else {}

## Find the step's anchor on screen, its words and the card's place; move a step on whose "try it" is done.
func _resolve(delta: float) -> void:
	var st := current()
	if st.is_empty():
		_finish(false)
		return
	var e := TutorialRules.entry(entry_id)
	on_hud = mode == "guide" and str(st.get("at", "")) in ["hud", "place"] or mode == "tour" and bool(st.get("hud", TutorialRules.hud_entry(e)))
	target = _find(str(st.get("anchor", "")), on_hud)
	if mode == "guide" and str(st.get("at", "")) == "place": target = _place_target(st)
	_missing = 0.0 if target.size != Vector2.ZERO else _missing + delta
	control = _control_live()
	line = _words(e, st)
	var top: Page = main.top_page()
	# A "try it" on a tab: the tab chosen.
	var tr: Dictionary = st.get("try", {})
	if tr.has("tab") and top != null and top.tab_id() == str(tr.tab): _tried = true
	if _tried:
		_tried = false
		_next()
		return
	_layout()

## An anchor's rect on screen: the first of `a|b|…` found, on the HUD or on the page on top.
func _find(names: String, hud_side: bool) -> Rect2:
	for n in names.split("|", false):
		var r := Rect2()
		if hud_side:
			var hud = main.get("hud")
			if is_instance_valid(hud): r = hud.tour_rect(n)
		else:
			var top: Page = main.top_page()
			if top != null: r = top.tour_rect(n)
		if r.size != Vector2.ZERO and Rect2(0, 0, 1280, 720).intersects(r): return r.intersection(Rect2(0, 0, 1280, 720))
	return Rect2()

## Where a place step leads now ({room, object, name}), found again as the character changes rooms.
var _spot_key := ""
var _spot := {}
func spot(st: Dictionary) -> Dictionary:
	var c = Game.active()
	var key := "%s|%d|%s" % [entry_id, step, str(c.position.get("room", "")) if c != null else ""]
	if key != _spot_key:
		_spot_key = key
		_spot = TutorialRules.place_for(c, st)
	return _spot

## A place's thing in the world, where the room shows it now (its label's spot over it); Rect2() in another room.
func _place_target(st: Dictionary) -> Rect2:
	var pl := spot(st)
	var w = main.get("world")
	if pl.is_empty() or Game.room_rt == null or str(Game.room_rt.room_id) != str(pl.get("room", "")) or not is_instance_valid(w): return Rect2()
	var obj := str(pl.get("object", ""))
	for views in [w.get("object_views"), w.get("npc_views")]:
		if views is Dictionary and (views as Dictionary).has(obj) and is_instance_valid(views[obj]):
			var at: Vector2 = (views[obj] as CanvasItem).get_global_transform_with_canvas().origin
			return Rect2(at - Vector2(28, 56), Vector2(56, 64))
	return Rect2()

## The card's words: the tour step's own line, or the chain step's (its own, or the entry's hint on the first, or the
## plain "Tap X." and "Open the X tab." with the names the step gives).
func _words(e: Dictionary, st: Dictionary) -> String:
	if st.has("text"): return Tx.t(str(st.text))
	match str(st.get("at", "")):
		"hud": return Tx.t(str(e.get("hint", "ui.tutorial.go.open")))
		"place":
			var hint := Tx.t(str(e.get("hint", ""))) if str(e.get("hint", "")) != "" else ""
			var pl := spot(st)
			if pl.is_empty() or (Game.room_rt != null and str(Game.room_rt.room_id) == str(pl.room)): return hint
			return Tx.t("ui.tutorial.go.place") % str(pl.get("name", Tx.t("ui.tutorial.go.there")))
		"page":
			var nm := Tx.t(str(st.get("name", ""))) if str(st.get("name", "")) != "" else ""
			if str(st.get("anchor", "")).begins_with("tab:"): return Tx.t("ui.tutorial.go.tab") % nm
			return Tx.t("ui.tutorial.go.entry") % nm
	return ""

# ------------------------------------------------------------------ moving on
func _next() -> void:
	var e := TutorialRules.entry(entry_id)
	if mode == "guide":
		# The chain's last step done (its element used, or Next): the guide is done, and its page's tour plays next.
		var chain: Array = e.get("chain", [])
		if step >= chain.size() - 1:
			Game.submit({"type": "tutorial_done", "id": entry_id, "stage": "guide"})
			_show("", "", 0)
		return
	var n := (e.get("tour", []) as Array).size()
	if step + 1 >= n:
		_finish(false)
		return
	if replay != "":
		replay_step += 1
	else:
		Game.submit({"type": "tutorial_step", "tour": entry_id, "step": step + 1})
	Audio.ui("ui_tap")

## The tour ends (played through, or skipped): recorded as seen (a replay only ends), and no other plays on this opening.
func _finish(skipped: bool) -> void:
	var top: Page = main.top_page() if main != null else null
	if top != null: _toured[top.get_instance_id()] = true
	if replay != "":
		replay = ""
	elif mode == "tour":
		Game.submit({"type": "tutorial_done", "id": entry_id, "stage": "tour", "skipped": skipped})
	elif mode == "guide":
		Game.submit({"type": "tutorial_done", "id": entry_id, "stage": "guide", "skipped": skipped})
	_show("", "", 0)

## The page's "?" (and Settings' Replay): play the tour for the page on top and its tab again from its first step.
func replay_tour(page_id: String, tab := "") -> bool:
	var id := TutorialRules.tour_for(page_id, tab)
	var top: Page = main.top_page() if main != null else null
	if id == "" or top == null: return false
	replay = id
	replay_step = 0
	replay_page = top
	return true

func _on_game_event(name: String, p: Dictionary) -> void:
	if mode == "": return
	var tr: Dictionary = current().get("try", {})
	if str(tr.get("event", "")) == name and (not p.has("actor") or str(p.actor) == Game.active_id): _tried = true

# ------------------------------------------------------------------ input
## Whether the coach keeps a HUD touch from the HUD: in a dimmed tour everything but the spotlight (when it lets taps
## through); in a guide only its card's buttons.
func holds(event: InputEvent) -> bool:
	if mode == "" or not visible: return false
	if not (event is InputEventMouseButton or event is InputEventScreenTouch or event is InputEventScreenDrag or event is InputEventMouseMotion): return false
	return _has_point(event.position)

func _dims() -> bool:
	return mode == "tour"

## The spotlight lets taps through to what is under it when the step asks for a try (or a guide points there).
func _passes(p: Vector2) -> bool:
	if target.size == Vector2.ZERO or not target.grow(8).has_point(p): return false
	return mode == "guide" or not current().get("try", {}).is_empty()

func _has_point(p: Vector2) -> bool:
	if mode == "": return false
	for b in buttons.values():
		if (b as Rect2).has_point(p): return true
	# A HUD power's control under the guide's hand: the tap is the coach's, and plays the power's tour.
	if control and target.grow(8).has_point(p): return true
	if not _dims(): return false
	return not _passes(p)

func _input(event: InputEvent) -> void:
	# A tap through the spotlight on a "tap" try moves the step on (the page takes the tap too).
	if mode == "" or not (event is InputEventMouseButton or event is InputEventScreenTouch): return
	if (event is InputEventMouseButton and event.button_index != MOUSE_BUTTON_LEFT): return
	var inside := _passes(event.position)
	if event.pressed: _in_hole = inside
	elif inside and _in_hole and current().get("try", {}).get("tap", false): _tried = true

func _gui_input(event: InputEvent) -> void:
	if not (event is InputEventMouseButton or event is InputEventScreenTouch): return
	if event is InputEventMouseButton and event.button_index != MOUSE_BUTTON_LEFT: return
	var hit := ""
	for k in buttons:
		if (buttons[k] as Rect2).has_point(event.position): hit = str(k)
	if hit == "" and control and target.grow(8).has_point(event.position): hit = "control"
	if event.pressed:
		_pressed = hit
	else:
		if hit != "" and hit == _pressed: press(hit)
		_pressed = ""
	accept_event()

## A card button: Next, Skip (the tour) or Later (the guide); or the HUD power's control the guide points at, whose tap
## plays its tour.
func press(which: String) -> void:
	match which:
		"next": _next()
		"control":
			if control:
				Audio.ui("ui_tap")
				Game.submit({"type": "tutorial_step", "tour": entry_id, "step": 0})
		"skip", "later":
			Audio.ui("ui_back")
			_finish(true)

# ------------------------------------------------------------------ layout
## The card's lines: wrapped at TEXT_W (at most two lines, the tutorials suite holds every line to it).
func _lines() -> Array:
	return UiKit.wrap(line, TEXT, TEXT_W)

## A tour's card: the words over the step count, Skip and Next. A guide's: one row, the words and its buttons beside them
## (Later, and Next on the element to use), as narrow as its words.
func _layout() -> void:
	var lines := _lines()
	var text_h := lines.size() * UiKit.line_height(TEXT)
	var names: Array = ["skip", "next"]
	if mode == "tour" and step + 1 >= (TutorialRules.entry(entry_id).get("tour", []) as Array).size(): names = ["next"]   # the last: Done alone
	if mode != "tour":
		names = ["later"]
		# The element at the chain's end (the node to spend on) may be passed over with Next, to the page's tour.
		var e := TutorialRules.entry(entry_id)
		if _element_step(e) and step == (e.get("chain", []) as Array).size() - 1: names = ["next", "later"]
	var sz: Vector2
	if mode == "tour":
		sz = Vector2(CARD_W, PAD + text_h + 12.0 + BTN_H + PAD)
	else:
		var tw := 0.0
		for ln in lines: tw = maxf(tw, UiKit.text_width(str(ln), TEXT))
		sz = Vector2(24.0 + ceilf(tw) + 16.0 + names.size() * (BTN_W + 12.0) + 8.0, maxf(text_h, BTN_H) + PAD * 2.0)
	card = _card_place(sz)
	buttons = {}
	var x := card.end.x - PAD
	var y := card.end.y - PAD - BTN_H if mode == "tour" else card.get_center().y - BTN_H * 0.5
	for i in range(names.size() - 1, -1, -1):
		x -= BTN_W
		buttons[names[i]] = Rect2(x, y, BTN_W, BTN_H)
		x -= 12.0

## Where the card stands: of the places round the anchor (under, over, beside) and in the screen's thirds, the first that
## keeps inside the safe area, off the anchor and the hand, and off the page's title, close and "?" (the one that covers
## them least); in the lower middle with no anchor.
func _card_place(sz: Vector2) -> Rect2:
	var safe := Rect2(24, 16, 1232, 688)
	var mid := Rect2(Vector2(640 - sz.x * 0.5, 452), sz)
	if target.size == Vector2.ZERO: return mid
	var avoid: Array = []
	var top: Page = main.top_page() if main != null else null
	if top != null and not on_hud:
		for n in ["close", "help", "title"]:
			var r := top.tour_rect(n)
			if r.size != Vector2.ZERO: avoid.append(r)
	var hr := hand_rect() if _hand_shown() else Rect2()
	if hr.size != Vector2.ZERO: avoid.append(hr)
	var cx := clampf(target.get_center().x - sz.x * 0.5, safe.position.x, safe.end.x - sz.x)
	var cy := clampf(target.get_center().y - sz.y * 0.5, safe.position.y, safe.end.y - sz.y)
	var gap := 14.0
	var below := (hr.end.y if hr.size != Vector2.ZERO and hr.position.y > target.position.y else target.end.y) + gap
	var above := (hr.position.y if hr.size != Vector2.ZERO and hr.position.y < target.position.y else target.position.y) - gap - sz.y
	var tries := [Vector2(cx, below), Vector2(cx, above), Vector2(target.position.x - gap - sz.x, cy), Vector2(target.end.x + gap, cy),
		mid.position, Vector2(640 - sz.x * 0.5, 96), Vector2(safe.position.x, safe.end.y - sz.y), Vector2(safe.end.x - sz.x, safe.end.y - sz.y)]
	var best := Rect2()
	var best_cost := INF
	for i in tries.size():
		var r := Rect2(tries[i], sz)
		if not safe.encloses(r) or r.intersects(target.grow(6)): continue
		var cost := float(i)
		for a in avoid: cost += (r.intersection(a) as Rect2).get_area() * 0.05
		if cost < best_cost:
			best_cost = cost
			best = r
	return best if best.size != Vector2.ZERO else Rect2(Vector2(640 - sz.x * 0.5, 80 if target.get_center().y > 360 else 720 - 80 - sz.y), sz)

## The hand shows where something is to be tapped: every guide step, and a tour step with a "try it".
func _hand_shown() -> bool:
	return target.size != Vector2.ZERO and (mode == "guide" or not (current().get("try", {}) as Dictionary).is_empty())

## Where the hand stands: over the anchor with its finger down, or under it with its finger up near the screen's top,
## bobbing toward it (still under Reduce motion).
func hand_rect() -> Rect2:
	if target.size == Vector2.ZERO: return Rect2()
	var hs := Vector2(HAND[0].length(), HAND.size()) * HAND_K
	var bob := 0.0 if UiKit.reduce_motion() else roundf(sin(t * 5.0) * 4.0)
	var down := target.position.y - hs.y - 8 > 0 and target.get_center().y > 200.0
	var x := clampf(target.get_center().x - hs.x * 0.4, 0, 1280 - hs.x)
	if down: return Rect2(Vector2(x, target.position.y - hs.y - 4 - bob), hs)
	return Rect2(Vector2(x, target.end.y + 4 + bob), hs)

# ------------------------------------------------------------------ drawing
func _draw() -> void:
	if mode == "": return
	var pulse := 0.0 if UiKit.reduce_motion() else 0.5 + 0.5 * sin(t * 4.0)
	if _dims():
		var hole := target.grow(8) if target.size != Vector2.ZERO else Rect2(640, 360, 0, 0)
		var dim := Color(UiKit.DIM, 0.66)
		draw_rect(Rect2(0, 0, 1280, hole.position.y), dim)
		draw_rect(Rect2(0, hole.end.y, 1280, 720 - hole.end.y), dim)
		draw_rect(Rect2(0, hole.position.y, hole.position.x, hole.size.y), dim)
		draw_rect(Rect2(hole.end.x, hole.position.y, 1280 - hole.end.x, hole.size.y), dim)
	if target.size != Vector2.ZERO:
		var ring := target.grow(8.0 + pulse * 3.0)
		if on_hud and absf(target.size.x - target.size.y) < 4.0:
			# A round HUD control: a round ring, and on a guide the pulsing "!" badge at its top right.
			var rc := target.get_center()
			var rr := target.size.x * 0.5 + 6.0 + pulse * 3.0
			draw_arc(rc, rr + 1.0, 0.0, TAU, 48, Color(UiKit.INK, 0.8), 6.0, true)
			draw_arc(rc, rr, 0.0, TAU, 48, Color(UiKit.GOLD, 0.75 + 0.25 * pulse), 3.0, true)
		else:
			draw_rect(ring.grow(2), Color(UiKit.INK, 0.8), false, 5.0)
			draw_rect(ring, Color(UiKit.GOLD, 0.75 + 0.25 * pulse), false, 3.0)
		if mode == "guide" and on_hud:
			var bc := Vector2(target.end.x, target.position.y)
			draw_circle(bc, 12.0 + pulse * 1.5, UiKit.INK, true, -1.0, true)
			draw_circle(bc, 10.0 + pulse * 1.5, UiKit.RED, true, -1.0, true)
			UiKit.draw_text(self, "!", bc + Vector2(-10, 6), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 20)
		if _hand_shown():
			var hr := hand_rect()
			draw_texture_rect(_hand_down if hr.position.y < target.position.y else _hand, hr, false)
	_draw_card()

func _draw_card() -> void:
	if card.size == Vector2.ZERO: return
	draw_style_box(UiKit.style("minor_panel"), card)
	var lines := _lines()
	var lh := UiKit.line_height(TEXT)
	var y := card.position.y + PAD + TEXT * UiKit.text_scale() if mode == "tour" else card.get_center().y - lines.size() * lh * 0.5 + TEXT * UiKit.text_scale() - 2.0
	for ln in lines:
		UiKit.draw_text(self, str(ln), Vector2(card.position.x + 24, y), TEXT, UiKit.PAPER)
		y += lh
	if mode == "tour":
		var n := (TutorialRules.entry(entry_id).get("tour", []) as Array).size()
		UiKit.draw_text(self, "%d / %d" % [step + 1, n], Vector2(card.position.x + 24, card.end.y - PAD - 16), 16, UiKit.MIST)
	for k in buttons:
		var r: Rect2 = buttons[k]
		var primary: bool = k == "next"
		draw_style_box(UiKit.style("button_primary" if primary else "button_secondary", "pressed" if _pressed == k else "normal"), r)
		var label := Tx.t("ui.tutorial." + str(k))
		if k == "next" and mode == "tour" and step + 1 >= (TutorialRules.entry(entry_id).get("tour", []) as Array).size(): label = Tx.t("ui.tutorial.done")
		if primary: UiKit.draw_inked(self, label, Vector2(r.position.x, r.get_center().y + 7), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		else: UiKit.draw_text(self, label, Vector2(r.position.x, r.get_center().y + 7), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

# ------------------------------------------------------------------ for tests and captures
## What the coach shows now: {mode, entry, step, anchor, rect, on_hud, card, buttons, line, waiting}.
func state() -> Dictionary:
	return {"mode": mode, "entry": entry_id, "step": step, "anchor": str(current().get("anchor", "")), "rect": target, "on_hud": on_hud,
		"card": card, "buttons": buttons.duplicate(), "line": line, "waiting": why_hidden, "replay": replay}
