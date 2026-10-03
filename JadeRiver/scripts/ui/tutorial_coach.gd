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
##
## Decision 45 (the "Bugs fixed" section of the note): the card is a thumb's to answer on a phone.
##   - The card stands still for its step: it waits for its page to come in (Page.settled) and for its anchor (MISSING_S),
##     is placed once, from the hand at rest (never its bob), and moves again only when its anchor moves further than
##     MOVE_PX, never while a finger is down on it. Its places keep off what the HUD shows and the thumbs' places.
##   - After the player closes a card, another lesson waits REST_S on the same screen (a queue's next guide came up at
##     once in the same place, and read as a Later that did nothing); a HUD lesson on screen keeps it until it ends.
##   - Its buttons are BTN_H tall and their touch targets HIT_PAD past them; a button acts on its finger's release,
##     within SLOP of it, and shows pressed while held. A phone's touch arrives twice (the touch and the mouse click made
##     from it): it is taken once, as the touch.
##   - A tap that closes a card guards the card's place for GUARD_S: the second tap of a double tap reaches nothing
##     under it (a page's slot, the HUD). A card taken away while a finger is on it (a fight, a scene) keeps that
##     finger's drags and release (holds).
##   - Every finger the coach took is its own to the end (its drags and its release never reach the HUD), and one it did
##     not take is never cut off (a thumb on the stick sliding over a guide's card keeps walking and lets go).
##   - It costs next to nothing hidden, and little showing: what it looks up is looked up once a frame or once a step
##     (HUD.tour_targets, TutorialRules.tours_for), and its card is a child drawn again only when it changes.

const CARD_W := 560.0         ## a tour's card
const TEXT := 20              ## the card's line (the type scale's body size), at most two lines on a phone
const TEXT_W := CARD_W - 48.0
const GUIDE_W := 400.0        ## a guide's words wrap this narrow when they still fit two lines
const BTN_W := 136.0
const BTN_H := 56.0           ## a card's button, drawn (a thumb's target: the house's 48 px and more)
const HIT_PAD := 8.0          ## its touch target this much past it (two side by side share the gap between them)
const SLOP := 24.0            ## a release this far off the button still presses it (a thumb rolls as it lifts)
const GUARD_S := 0.35         ## after a tap closes a card, a tap on its place is the coach's (a double tap acts once)
const FADE_S := 0.12          ## a new card fades in (its buttons live from its first frame)
const MOVE_PX := 12.0         ## the card keeps its place for its step unless its anchor moves further than this
const REST_S := 1.2           ## after the player closes a card, another lesson waits this long on the same screen
const PAD := 20.0
const MISSING_S := 0.4        ## an anchor not found this long: the card stands alone, in the middle
const HIDE_ON := ["dialogue", "gift", "revival", "fates", "mercy", "welcome"]   ## talks and events: the coach waits
const HAND := ["....##......", "...#WW#.....", "...#WW#.....", "...#WW#.....", "...#WW###...", "...#WW#WW##.", ".###WW#WW#W#",
	"#WW#WWWWWWW#", "#WWWWWWWWWW#", "#WWWWWWWWWW#", ".#WWWWWWWWW#", ".#WWWWWWWW#.", "..#WWWWWWW#.", "...#WWWWW#..", "...#SSSSS#..", "...#######.."]
const HAND_K := 3.0           ## screen px an art px (nearest neighbour)
const SCREEN := Rect2(0, 0, 1280, 720)
const SAFE := Rect2(24, 16, 1232, 688)
## Where the thumbs rest on the play screen (the stick's side, and the right thumb's cluster of Attack, the techniques
## and the rings): a guide's card keeps off them, so a thumb going to walk or strike never lands on its Later.
const THUMBS := [Rect2(0, 440, 560, 280), Rect2(900, 330, 380, 390)]

var main: Node = null         ## the shell (main.gd): its screen, pages, HUD, world and scenes
var mode := ""                ## "", "guide" or "tour"
var entry_id := ""            ## the entry shown
var step := 0                 ## its step (the chain's or the tour's)
var on_hud := false           ## the anchor is the HUD's
var target := Rect2()         ## the anchor on screen now (Rect2() when not found)
var card := Rect2()
var buttons: Dictionary = {}  ## "next", "skip", "later" -> Rect2, as drawn
var hits: Dictionary = {}     ## the same -> Rect2, their touch targets
var line := ""                ## the card's words now
var why_hidden := ""          ## what the coach waits on ("combat", "scene", "moment", "dialogue", …; "" when free)
var replay := ""              ## a tour played again from "?" (not saved) …
var replay_step := 0
var replay_page: Page = null  ## … on this opening of its page
var t := 0.0
var _missing := 0.0
var _toured: Dictionary = {}  ## page instance id -> true: a tour played (or was skipped) on that opening
var _tried := false           ## the step's try-it was done
var _hand: ImageTexture = null       ## the finger up (under the anchor)
var _hand_down: ImageTexture = null  ## the finger down (over it)
var _pressed := ""            ## the button a finger holds down now ("" none)
var _press_idx := -2          ## that finger (a touch's index; -1 the mouse)
var _in_hole := -2            ## the finger pressed in a try-it spotlight (a "tap" try), -2 none
var _goal := ""               ## the room the direction mark was asked to lead to (tutorial_goal)
var control := false          ## the guide points at a HUD power's own control: a tap there plays its tour (_control_live)
var _shown_t := 0.0           ## how long this step has shown (the card's fade)
var _laid := ""               ## the step the card was laid out for ("" none yet), its words, text size and side
var _laid_line := ""
var _laid_scale := 1.0
var _laid_hud := false
var _laid_at := Rect2()       ## the anchor it was placed round
var _words_key := ""          ## the step and state its words were found for
var _guard_t := 0.0           ## the double tap's guard: how long it lasts yet, and where
var _guard_rect := Rect2()
var _held: Dictionary = {}    ## finger index (-1 the mouse) -> true: a press the coach took, so its drags and release are its too
var _rest_t := 0.0            ## the rest after a card closed (_present): how long yet, the lesson closed, the page then
var _rest_entry := ""
var _rest_top := 0
var _rest_char := 0
var _lines_key := ""
var _lines_cache: Array = []
var _card_view: Control = null

## The card, drawn on a child of its own: drawn again only when what it shows changes (its words, place, buttons, the
## one held down, its fade), while the coach's own drawing (the dim, the ring's pulse, the hand's bob) moves each frame.
class CardView extends Control:
	var coach: TutorialCoach
	var _card := Rect2()
	var _line := ""
	var _entry := ""
	var _step := -1
	var _pressed := ""
	var _alpha := -1.0
	var _n := -1
	func _ready() -> void:
		set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func refresh() -> void:
		var a := coach.card_alpha() if coach.mode != "" else 0.0
		if coach.card != _card or coach.line != _line or coach.entry_id != _entry or coach.step != _step or coach._pressed != _pressed \
				or a != _alpha or coach.buttons.size() != _n:
			_card = coach.card
			_line = coach.line
			_entry = coach.entry_id
			_step = coach.step
			_pressed = coach._pressed
			_alpha = a
			_n = coach.buttons.size()
			queue_redraw()
	func _draw() -> void:
		coach._draw_card(self)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	GameEvents.event.connect(_on_game_event)
	_hand = _hand_texture(false)
	_hand_down = _hand_texture(true)
	_card_view = CardView.new()
	_card_view.coach = self
	add_child(_card_view)

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
	if _guard_t > 0.0: _guard_t = maxf(0.0, _guard_t - delta)
	if _rest_t > 0.0: _rest_t = maxf(0.0, _rest_t - delta)
	var was_mode := mode
	var was_step := step
	var was_target := target
	_update(delta)
	if mode == "" and was_mode == "": return   # hidden, and was: nothing to draw
	if mode != "":
		_shown_t += delta
		# The ring pulses and the hand bobs: the coach's own drawing moves each frame (under Reduce motion only on a change).
		if not UiKit.reduce_motion() or mode != was_mode or step != was_step or target != was_target: queue_redraw()
	else:
		queue_redraw()
	if _card_view != null: _card_view.refresh()

## The character's state and what is on screen decide what shows, every frame.
func _update(delta: float) -> void:
	var c = Game.active() if main != null else null
	if c == null or main.screen != "world":
		why_hidden = ""
		_guard_t = 0.0
		_show("", "", 0)
		return
	var top: Page = main.top_page()
	# Nothing queued, none under way, no page and no replay: hidden at once (the record looked at as it is).
	if top == null and replay == "" and mode == "" and _empty(c.tutorials.get("queue")) and _empty(c.tutorials.get("at")):
		why_hidden = ""
		return
	var rec: Dictionary = Game.tutorials.state(c)
	# Nothing queued, no tour under way, none played again, and none this page could still play: nothing shows, and
	# nothing more is asked (a hidden coach costs next to nothing a frame).
	if replay == "" and (rec.queue as Array).is_empty() and (rec.at as Dictionary).is_empty() and (top == null or _page_tour(c, rec, top) == ""):
		why_hidden = ""
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
			_present("tour", replay, replay_step, delta)
			return
		replay = ""
	var head := _head(rec)
	var he := TutorialRules.entry(head)
	# 2. The head guide at its element on this page (the node to spend on): before the page's own tour. (A HUD power's
	# guide is its lesson's, step 4.)
	if head != "" and top != null and not TutorialRules.hud_entry(he) and TutorialRules.chain_home(he, pid, tab) and _element_step(he):
		_present("guide", head, (he.chain as Array).size() - 1, delta)
		return
	# A guide whose page (and tab) is open now is done, whether it led there or the player came first: its tour, if
	# unseen, plays next.
	if top != null:
		for q in (rec.queue as Array).duplicate():
			if _arrived(TutorialRules.entry(str(q)), pid, tab): Game.submit({"type": "tutorial_done", "id": str(q), "stage": "guide"})
		head = _head(rec)
		he = TutorialRules.entry(head)
	# 3. A tour of the page on top: one in progress on this page (on its tab), else an unseen one on its first opening.
	if top != null:
		var tour := _page_tour(c, rec, top)
		if tour != "":
			_present("tour", tour, int(rec.at.get(tour, 0)), delta)
			return
	# 4. The head guide: a HUD control's lesson (its tour with no page open, and a HUD power's guide round it), else the
	# chain's step for what is on screen.
	if head != "":
		if TutorialRules.hud_entry(he):
			if _hud_lesson(c, he, top, pid, tab, delta): return
		else:
			var i := TutorialRules.chain_step(he, pid, tab)
			if i >= 0:
				_present("guide", head, i, delta)
				return
	_show("", "", 0)

static func _empty(v) -> bool:
	return v == null or ((v is Array or v is Dictionary) and v.is_empty())

## The guide at the head of the queue, but a HUD lesson whose tour is under way keeps the screen until it ends (decision
## 45: a guide queued behind it with a higher priority, the Menu's say, no longer takes the card from under the thumb).
func _head(rec: Dictionary) -> String:
	var q: Array = rec.queue
	if q.is_empty(): return ""
	# The HUD lesson's tour on screen now (its first step too), and one under way.
	if mode == "tour" and replay == "" and q.has(entry_id) and not rec.seen.has(entry_id) and TutorialRules.hud_entry(TutorialRules.entry(entry_id)): return entry_id
	if not (rec.at as Dictionary).is_empty():
		for id in q:
			if rec.at.has(id) and not rec.seen.has(id) and TutorialRules.hud_entry(TutorialRules.entry(str(id))): return str(id)
	return str(q[0])

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
	# The HUD still fading back in after a scene's cut: a guide waits for it (its hand and badge on a faded button).
	if is_instance_valid(hud) and hud.modulate.a < 0.95 and main.top_page() == null: return "scene"
	for p in main.get("pages"):
		if is_instance_valid(p) and str(p.page_id) in HIDE_ON: return "dialogue"
	var top: Page = main.top_page()
	if top != null and not top.confirm.is_empty(): return "confirm"
	if top != null and not top.tour_ready(): return "busy"
	# A page still coming in (its parts sliding into place): its card waits the moment, so it never jumps under a thumb.
	if top != null and not top.settled(): return "opening"
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
		_present("tour", id, Game.tutorials.step_of(c, id), delta)
		return true
	var at := TutorialRules.tour_at(e)
	var control_on := at >= 0 and top == null and _find(str(((e.chain as Array)[at] as Dictionary).get("anchor", "")), true).size != Vector2.ZERO
	var i := TutorialRules.lesson_step(e, pid, tab, toured, control_on)
	if i < 0: return false
	_present("guide", id, i, delta)
	return true

## The guide's hand is on a HUD power's own control (not the fan that holds it): a tap there plays its tour. Found once
## a frame (_resolve).
func _control_live() -> bool:
	if mode != "guide" or not current().get("tour", false) or target.size == Vector2.ZERO or main == null: return false
	var hud = main.get("hud")
	var first := str(current().get("anchor", "")).get_slice("|", 0)
	return is_instance_valid(hud) and hud.tour_rect(first).size != Vector2.ZERO

## The tour to show on the page on top, if no tour has played on this opening yet: one in progress on this page (on its
## own tab, decision 45: a tab's tour resumed on another tab lit nothing), else the first unseen one for it and its tab.
func _page_tour(c, rec: Dictionary, top: Page) -> String:
	if _toured.has(top.get_instance_id()): return ""
	var pid := top.page_id
	var tab := top.tab_id()
	for id in rec.at:
		if rec.seen.has(id): continue
		var e := TutorialRules.entry(str(id))
		if TutorialRules.hud_entry(e) or not TutorialRules.same_page(str(e.get("page", "")), pid): continue
		if str(e.get("tab", "")) != "" and str(e.tab) != tab: continue
		return str(id)
	# None by itself while every system is forced open (the Max Tester, previews): the "?" still plays.
	if Unlocks.debug_force_all: return ""
	for id in TutorialRules.tours_for(pid, tab):
		if rec.seen.has(id): continue
		# A tab's own tour waits for its system (a craft's tab shows only why it is shut until then).
		var e := TutorialRules.entry(str(id))
		var gate := str(e.get("trigger", {}).get("unlock", ""))
		if str(e.get("tab", "")) != "" and gate != "" and not Unlocks.is_unlocked(c.id, gate): continue
		return str(id)
	return ""

## Show step `i` of `id` in mode `m` and find its anchor, words and card; but after the player closed a card, another
## lesson waits a moment (REST_S) while the screen is the same (decision 45: with lessons queued, a Later brought the next
## guide at once in the same place, its hand on the same Menu button, and read as a Later that did nothing).
func _present(m: String, id: String, i: int, delta: float) -> void:
	if mode == "" and _rest_t > 0.0 and id != _rest_entry and _top_id() == _rest_top and _char_id() == _rest_char:
		why_hidden = "rest"
		_show("", "", 0)
		return
	_show(m, id, i)
	_resolve(delta)

func _char_id() -> int:
	var c = Game.active()
	return c.get_instance_id() if c is Object else 0

func _top_id() -> int:
	var top: Page = main.top_page() if main != null else null
	return top.get_instance_id() if top != null else 0

## The player closed the card of `id`: a moment's rest before another lesson on this screen.
func _rest_after(id: String) -> void:
	_rest_t = REST_S
	_rest_entry = id
	_rest_top = _top_id()
	_rest_char = _char_id()

func _show(m: String, id: String, i: int) -> void:
	if m == "" and mode == "" and _goal == "": return   # hidden, and was
	if m != mode or id != entry_id or i != step:
		_tried = false
		_missing = 0.0
		_shown_t = 0.0
		_in_hole = -2
		_pressed = ""
		_press_idx = -2
		# A new step's card is laid out afresh, once its anchor is found (_resolve).
		card = Rect2()
		buttons = {}
		hits = {}
		_laid = ""
		_words_key = ""
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
		hits = {}
		line = ""
		control = false
		_laid = ""

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
	var found := _find(str(st.get("anchor", "")), on_hud)
	if mode == "guide" and str(st.get("at", "")) == "place": found = _place_target(st)
	_missing = 0.0 if found.size != Vector2.ZERO else _missing + delta
	# An anchor not found yet (a page's first drawing, a HUD button coming in) is waited for a moment before the card
	# stands alone, so it never shows in the middle and then jumps beside its anchor; one lost a moment after it was
	# found keeps its last place.
	if found.size == Vector2.ZERO and _missing < MISSING_S:
		if card.size == Vector2.ZERO: return
	else:
		target = found
	control = _control_live()
	# The card's words, found again only when the step, the control's state or the room changes.
	var wk := "%s|%s|%d|%s|%s" % [mode, entry_id, step, control, str(Game.room_rt.room_id) if Game.room_rt != null else ""]
	if wk != _words_key:
		_words_key = wk
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
	var hud = main.get("hud") if hud_side else null
	var top: Page = null if hud_side else main.top_page()
	for n in names.split("|", false):
		var r := Rect2()
		if hud_side:
			if is_instance_valid(hud): r = hud.tour_rect(n)
		elif top != null:
			r = top.tour_rect(n)
		if r.size != Vector2.ZERO and SCREEN.intersects(r): return r.intersection(SCREEN)
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
		"hud":
			# A HUD power's control folded away in the fan: the hand is on the fan, and the card says to open it.
			if st.get("tour", false) and not control and str(st.get("name", "")) != "": return Tx.t("ui.tutorial.go.fan") % Tx.t(str(st.name))
			return Tx.t(str(e.get("hint", "ui.tutorial.go.open")))
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
	_forget_closed()

## The pages closed since are let go of (the opening a tour was played on, the replay's page).
func _forget_closed() -> void:
	for id in _toured.keys():
		if not is_instance_id_valid(int(id)): _toured.erase(id)

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
	# Settings' Replay tutorials: every page's tour plays again from its next opening, not the one open now.
	if name == "tutorials_replayed" and main != null and main.top_page() != null: _toured[main.top_page().get_instance_id()] = true
	if mode == "": return
	var tr: Dictionary = current().get("try", {})
	if str(tr.get("event", "")) == name and (not p.has("actor") or str(p.actor) == Game.active_id): _tried = true

# ------------------------------------------------------------------ input
## Whether the coach keeps a HUD touch from the HUD: a press on the card (and in a dimmed tour anywhere but a try-it's
## spotlight), and then that finger's drags and release; a finger it did not take stays the HUD's to the end.
func holds(event: InputEvent) -> bool:
	if not visible: return false
	var idx := -1
	if event is InputEventScreenTouch or event is InputEventScreenDrag: idx = event.index
	elif not (event is InputEventMouseButton or event is InputEventMouseMotion): return false
	if event is InputEventScreenTouch or event is InputEventMouseButton:
		if event.pressed:
			var mine := (mode != "" or _guard_t > 0.0) and _has_point(event.position)
			if mine: _held[idx] = true
			else: _held.erase(idx)
			return mine
		var was := _held.has(idx)
		_held.erase(idx)
		return was
	return _held.has(idx)

func _dims() -> bool:
	return mode == "tour"

## A step whose card waits for its anchor (MISSING_S): nothing drawn yet, and nothing taken.
func _pending() -> bool:
	return mode != "" and card.size == Vector2.ZERO

## The spotlight lets taps through to what is under it when the step asks for a try (or a guide points there).
func _passes(p: Vector2) -> bool:
	if target.size == Vector2.ZERO or not target.grow(8).has_point(p): return false
	return mode == "guide" or not current().get("try", {}).is_empty()

func _has_point(p: Vector2) -> bool:
	# The second tap of a double tap on a card just closed: the coach's, so it reaches nothing under it.
	if _guard_t > 0.0 and _guard_rect.has_point(p): return true
	if mode == "" or _pending(): return false
	for b in hits.values():
		if (b as Rect2).has_point(p): return true
	# The card itself (its words, its margin) over a page: a tap on it never reaches what it hides. (On the play screen a
	# guide's card lets a thumb through, to the stick under it; it is placed clear of the HUD's controls, _card_place.)
	if card.has_point(p) and (_dims() or main.top_page() != null): return true
	# A HUD power's control under the guide's hand: the tap is the coach's, and plays the power's tour.
	if control and target.grow(8).has_point(p): return true
	if not _dims(): return false
	return not _passes(p)

func _input(event: InputEvent) -> void:
	# A tap through the spotlight on a "tap" try moves the step on (the page takes the tap too). One finger's press and
	# release (the touch; a phone's mouse click made from it is the same tap).
	if mode == "": return
	var idx := -3
	if event is InputEventScreenTouch: idx = event.index
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.device != InputEvent.DEVICE_ID_EMULATION: idx = -1
	if idx == -3: return
	var inside := _passes(event.position)
	if event.pressed: _in_hole = idx if inside else -2
	elif inside and _in_hole == idx and current().get("try", {}).get("tap", false): _tried = true

func _gui_input(event: InputEvent) -> void:
	var idx := -3
	if event is InputEventScreenTouch or event is InputEventScreenDrag: idx = event.index
	elif event is InputEventMouseButton or event is InputEventMouseMotion:
		# A phone's touch comes as the touch and as a mouse click made from it: taken once, as the touch.
		if event.device == InputEvent.DEVICE_ID_EMULATION:
			accept_event()
			return
		if event is InputEventMouseButton and event.button_index != MOUSE_BUTTON_LEFT: return
		idx = -1
	if idx == -3: return
	if event is InputEventScreenTouch or event is InputEventMouseButton:
		if event.pressed: _finger_down(idx, event.position)
		else: _finger_up(idx, event.position)
	accept_event()

## A finger down on the coach: the button under it held (shown pressed), unless it is the second tap of a double tap.
func _finger_down(idx: int, p: Vector2) -> void:
	if _guard_t > 0.0 and _guard_rect.has_point(p):
		_pressed = ""
		_press_idx = -2
		return
	var which := _hit(p)
	_pressed = which
	_press_idx = idx if which != "" else -2

## The finger that holds a button lifts: the button acts if it lifts on it (or within SLOP of it).
func _finger_up(idx: int, p: Vector2) -> void:
	if idx != _press_idx or _pressed == "": return
	var which := _pressed
	var r: Rect2 = target.grow(8.0) if which == "control" else hits.get(which, Rect2())
	_pressed = ""
	_press_idx = -2
	if r.size == Vector2.ZERO or not r.grow(SLOP).has_point(p): return
	var closes: bool = which in ["skip", "later"] or (which == "next" and (mode == "guide" or step + 1 >= _tour_size()))
	var old := card
	press(which)
	# A tap that closed the card: the second of a double tap is the coach's (it must not reach the page or HUD under it).
	if closes and old.size != Vector2.ZERO: _guard(old)

## How long the double tap's guard lasts yet (0 when none): tests wait it out before a tap of their own.
func guarded() -> float:
	return _guard_t

func _guard(r: Rect2) -> void:
	_guard_t = GUARD_S
	_guard_rect = r.grow(HIT_PAD + 8.0)

## The button (or the HUD power's control) under a point: "" for none.
func _hit(p: Vector2) -> String:
	for k in hits:
		if (hits[k] as Rect2).has_point(p): return str(k)
	if control and target.grow(8).has_point(p): return "control"
	return ""

## The phone's Back (and Escape) while a tour dims the screen: it skips the tour (it was the page under it that
## closed, and the tour came back on its next opening). True when it did; a guide leaves Back to the page.
func back() -> bool:
	if mode != "tour" or _pending(): return false
	press("skip")
	return true

func _unhandled_key_input(event: InputEvent) -> void:
	if event.pressed and not event.echo and event.keycode == KEY_ESCAPE and back(): get_viewport().set_input_as_handled()

## A card button: Next, Skip (the tour) or Later (the guide); or the HUD power's control the guide points at, whose tap
## plays its tour.
func press(which: String) -> void:
	var id := entry_id
	match which:
		"next":
			_next()
			if mode == "": _rest_after(id)
		"control":
			if control:
				Audio.ui("ui_tap")
				Game.submit({"type": "tutorial_step", "tour": entry_id, "step": 0})
		"skip", "later":
			Audio.ui("ui_back")
			_finish(true)
			_rest_after(id)

func _tour_size() -> int:
	return (TutorialRules.entry(entry_id).get("tour", []) as Array).size()

# ------------------------------------------------------------------ layout
## The card's lines: wrapped at TEXT_W (at most two lines, the tutorials suite holds every line to it), once for its words
## and text size.
func card_lines() -> Array:
	var key := "%s|%s|%s" % [line, UiKit.text_scale(), mode]
	if key != _lines_key:
		_lines_key = key
		_lines_cache = UiKit.wrap(line, TEXT, TEXT_W)
		# A guide's card, beside its button on the play screen, is kept narrow when its words still fit two lines (a wide
		# one sat over the tracker's go button).
		if mode == "guide":
			var narrow := UiKit.wrap(line, TEXT, GUIDE_W)
			if narrow.size() <= 2: _lines_cache = narrow
	return _lines_cache

## A tour's card: the words over the step count, Skip and Next. A guide's: one row, the words and its buttons beside them
## (Later, and Next on the element to use), as narrow as its words. Laid out once for its step and words, and again only
## when its anchor moves (MOVE_PX) or comes under it; never while a finger holds one of its buttons.
func _layout() -> void:
	# The same step, words and text size as laid out: kept, unless its anchor moved (never under a finger).
	var same: bool = _laid != "" and _laid_line == line and _laid_scale == UiKit.text_scale() and _laid_hud == on_hud
	if same and _pressed != "": return
	var moved := target.position.distance_to(_laid_at.position) > MOVE_PX or target.end.distance_to(_laid_at.end) > MOVE_PX \
		or (target.size == Vector2.ZERO) != (_laid_at.size == Vector2.ZERO)
	if same and not moved: return
	var names: Array = ["skip", "next"]
	if mode == "tour" and step + 1 >= _tour_size(): names = ["next"]   # the last: Done alone
	if mode != "tour":
		names = ["later"]
		# The element at the chain's end (the node to spend on) may be passed over with Next, to the page's tour.
		var e := TutorialRules.entry(entry_id)
		if _element_step(e) and step == (e.get("chain", []) as Array).size() - 1: names = ["next", "later"]
	_laid = "%s|%s|%d" % [mode, entry_id, step]
	_laid_line = line
	_laid_scale = UiKit.text_scale()
	_laid_hud = on_hud
	_laid_at = target
	var lines := card_lines()
	var text_h := lines.size() * UiKit.line_height(TEXT)
	var sz: Vector2
	if mode == "tour":
		sz = Vector2(CARD_W, PAD + text_h + 12.0 + BTN_H + PAD)
	else:
		var tw := 0.0
		for ln in lines: tw = maxf(tw, UiKit.text_width(str(ln), TEXT))
		sz = Vector2(24.0 + ceilf(tw) + 16.0 + names.size() * (BTN_W + 12.0) + 8.0, maxf(text_h, BTN_H) + PAD * 2.0)
	card = _card_place(sz)
	buttons = {}
	hits = {}
	var x := card.end.x - PAD
	var y := card.end.y - PAD - BTN_H if mode == "tour" else card.get_center().y - BTN_H * 0.5
	for i in range(names.size() - 1, -1, -1):
		x -= BTN_W
		var r := Rect2(x, y, BTN_W, BTN_H)
		buttons[names[i]] = r
		# Its touch target: HIT_PAD past it, the gap to a neighbour shared (6 px each).
		var left := 6.0 if i > 0 else HIT_PAD
		var right := 6.0 if i < names.size() - 1 else HIT_PAD
		hits[names[i]] = Rect2(r.position - Vector2(left, HIT_PAD), r.size + Vector2(left + right, HIT_PAD * 2.0))
		x -= 12.0

## Where the card stands: of the places round the anchor (under, over, beside) and in the screen's thirds, the first that
## keeps inside the safe area, off the anchor and the hand (at rest), and off the page's title, close and "?" (the one that
## covers them least); in the lower middle with no anchor.
func _card_place(sz: Vector2) -> Rect2:
	var safe := SAFE
	var mid := Rect2(Vector2(640 - sz.x * 0.5, 452), sz)
	if target.size == Vector2.ZERO: return mid
	var avoid: Array = []   # [rect, weight]: what each covered pixel costs
	var top: Page = main.top_page() if main != null else null
	if top != null and not on_hud:
		for n in ["close", "help", "title"]:
			var r := top.tour_rect(n)
			if r.size != Vector2.ZERO: avoid.append([r, 0.05])
	var hr := hand_rect(false) if hand_shown() else Rect2()
	if hr.size != Vector2.ZERO: avoid.append([hr.grow(4), 0.05])
	# On the play screen, clear of what the HUD shows (its controls, a guide's card sat over the Talk button; its plates,
	# the equip prompt, the log), and a guide's (the player plays on under it) off the thumbs' places: the stick's and the
	# right thumb's cluster.
	var hud = main.get("hud") if main != null else null
	if top == null and is_instance_valid(hud) and hud.has_method("obstacle_rects"):
		for r in hud.obstacle_rects():
			if not (r as Rect2).intersects(target): avoid.append([(r as Rect2).grow(4), 0.03])
		if mode == "guide":
			for zone in THUMBS:
				var z: Rect2 = zone
				if bool(hud.get("left_handed")): z.position.x = 1280.0 - z.end.x   # the stick on the right
				avoid.append([z, 0.02])
	var cx := clampf(target.get_center().x - sz.x * 0.5, safe.position.x, safe.end.x - sz.x)
	var cy := clampf(target.get_center().y - sz.y * 0.5, safe.position.y, safe.end.y - sz.y)
	var gap := 14.0
	var below := (hr.end.y + 4.0 if hr.size != Vector2.ZERO and hr.position.y > target.position.y else target.end.y) + gap
	var above := (hr.position.y - 4.0 if hr.size != Vector2.ZERO and hr.position.y < target.position.y else target.position.y) - gap - sz.y
	var tries := [Vector2(cx, below), Vector2(cx, above), Vector2(target.position.x - gap - sz.x, cy), Vector2(target.end.x + gap, cy),
		mid.position, Vector2(640 - sz.x * 0.5, 96), Vector2(safe.position.x, safe.end.y - sz.y), Vector2(safe.end.x - sz.x, safe.end.y - sz.y),
		Vector2(safe.position.x, safe.position.y), Vector2(safe.end.x - sz.x, safe.position.y)]
	var best := Rect2()
	var best_cost := INF
	for i in tries.size():
		var r := Rect2(tries[i], sz)
		if not safe.encloses(r) or r.intersects(target.grow(6)): continue
		var cost := float(i)
		for a in avoid: cost += (r.intersection(a[0]) as Rect2).get_area() * float(a[1])
		if cost < best_cost:
			best_cost = cost
			best = r
	if best.size != Vector2.ZERO: return best
	# Nothing clear of a tall anchor inside the safe area (the Cultivation stair): tight over or under it, to the screen's
	# edge; else (a page's whole content, the Techniques chart) the place, of those and the safe area's corners and
	# edges, that covers the least of it.
	for y in [target.position.y - 6.0 - sz.y, target.end.y + 6.0]:
		var r := Rect2(Vector2(cx, y), sz)
		if SCREEN.encloses(r) and not r.intersects(target): return r
	var least := Rect2()
	var least_a := INF
	for x in [safe.position.x, cx, safe.end.x - sz.x]:
		for y in [safe.position.y, cy, safe.end.y - sz.y]:
			var r := Rect2(Vector2(x, y), sz)
			var a := r.intersection(target).get_area()
			for av in avoid: a += (r.intersection(av[0]) as Rect2).get_area() * 0.5
			if a < least_a:
				least_a = a
				least = r
	return least

## The hand shows where something is to be tapped: every guide step, and a tour step with a "try it".
func hand_shown() -> bool:
	return target.size != Vector2.ZERO and (mode == "guide" or not (current().get("try", {}) as Dictionary).is_empty())

## Where the hand stands: over the anchor with its finger down, or under it with its finger up near the screen's top,
## bobbing toward it (still under Reduce motion, and at rest for the card's place: `bob` false).
func hand_rect(bob := true) -> Rect2:
	if target.size == Vector2.ZERO: return Rect2()
	var hs := Vector2(HAND[0].length(), HAND.size()) * HAND_K
	var dy := 0.0 if UiKit.reduce_motion() or not bob else roundf(sin(t * 5.0) * 4.0)
	var down := target.position.y - hs.y - 8 > 0 and target.get_center().y > 200.0
	var x := clampf(target.get_center().x - hs.x * 0.4, 0, 1280 - hs.x)
	if down: return Rect2(Vector2(x, maxf(0.0, target.position.y - hs.y - 4 - dy)), hs)
	return Rect2(Vector2(x, target.end.y + 4 + dy), hs)

## The card's alpha as it comes (1 once it is in; Reduce motion shows it at once).
func card_alpha() -> float:
	if UiKit.reduce_motion(): return 1.0
	return snappedf(clampf(_shown_t / FADE_S, 0.0, 1.0), 0.25)

# ------------------------------------------------------------------ drawing
func _draw() -> void:
	if mode == "" or _pending(): return
	var pulse := 0.0 if UiKit.reduce_motion() else 0.5 + 0.5 * sin(t * 4.0)
	# A thin anchor (a bar of the panel, its neighbours 4 px off) is lit close round, so the next bar stays dim.
	var margin := 8.0 if target.size.y >= 24.0 else 3.0
	if _dims():
		var hole := target.grow(margin) if target.size != Vector2.ZERO else Rect2(640, 360, 0, 0)
		var dim := Color(UiKit.DIM, 0.66)
		draw_rect(Rect2(0, 0, 1280, hole.position.y), dim)
		draw_rect(Rect2(0, hole.end.y, 1280, 720 - hole.end.y), dim)
		draw_rect(Rect2(0, hole.position.y, hole.position.x, hole.size.y), dim)
		draw_rect(Rect2(hole.end.x, hole.position.y, 1280 - hole.end.x, hole.size.y), dim)
	_draw_ghost()
	if target.size != Vector2.ZERO:
		var ring := target.grow(margin + pulse * (3.0 if margin > 4.0 else 1.0))
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
			var bc := Vector2(minf(target.end.x, 1280.0 - 15.0), maxf(target.position.y, 15.0))   # kept on screen (Swap at the edge)
			draw_circle(bc, 12.0 + pulse * 1.5, UiKit.INK, true, -1.0, true)
			draw_circle(bc, 10.0 + pulse * 1.5, UiKit.RED, true, -1.0, true)
			UiKit.draw_text(self, "!", bc + Vector2(-10, 6), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 20)
		if hand_shown():
			var hr := hand_rect()
			draw_texture_rect(_hand_down if hr.position.y < target.position.y else _hand, hr, false)

## A tour step's ghost (decision 44): the control it lights is not on the play screen now (a Treasure button comes out
## only in a fight), so it is drawn faint where it will stand, with the treasure it holds.
func _draw_ghost() -> void:
	var role := str(current().get("ghost", ""))
	if role == "" or target.size == Vector2.ZERO or not on_hud: return
	var hud = main.get("hud")
	if not is_instance_valid(hud) or hud.tour_targets().any(func(tg): return str(tg.role) == role): return
	var at := target.get_center()
	var tex := UiKit.hd_texture("hud_ring_52", "normal")
	if tex != null:
		var half := 26.0 + UiKit.HUD_RING_PAD   # HUD.ring at r 26
		draw_texture_rect(tex, Rect2(at - Vector2(half, half), Vector2(half, half) * 2.0), false, Color(1, 1, 1, 0.8))
	var c = Game.active()
	if c != null and role.begins_with("treasure:"):
		var tid := str(c.inventory.treasures[int(role.get_slice(":", 1))])
		if tid != "" and c.inventory.count(tid) > 0: SpriteCache.draw_icon(self, Rect2(at - Vector2(16, 16), Vector2(32, 32)), tid, Color(1, 1, 1, 0.8))

## The card on `ci` (the coach's CardView): its panel, words, step count and buttons, the one held shown pressed.
func _draw_card(ci: CanvasItem) -> void:
	if mode == "" or card.size == Vector2.ZERO: return
	var a := card_alpha()
	ci.modulate.a = a
	ci.draw_style_box(UiKit.style("minor_panel"), card)
	var lines := card_lines()
	var lh := UiKit.line_height(TEXT)
	var y := card.position.y + PAD + TEXT * UiKit.text_scale() if mode == "tour" else card.get_center().y - lines.size() * lh * 0.5 + TEXT * UiKit.text_scale() - 2.0
	for ln in lines:
		UiKit.draw_text(ci, str(ln), Vector2(card.position.x + 24, y), TEXT, UiKit.PAPER)
		y += lh
	var n := _tour_size()
	if mode == "tour":
		UiKit.draw_text(ci, "%d / %d" % [step + 1, n], Vector2(card.position.x + 24, card.end.y - PAD - 18), 16, UiKit.MIST)
	for k in buttons:
		var r: Rect2 = buttons[k]
		var primary: bool = k == "next"
		var held: bool = _pressed == k
		ci.draw_style_box(UiKit.style("button_primary" if primary else "button_secondary", "pressed" if held else "normal"), r)
		var label := Tx.t("ui.tutorial." + str(k))
		if k == "next" and mode == "tour" and step + 1 >= n: label = Tx.t("ui.tutorial.done")
		var ly := r.get_center().y + 7 + (2.0 if held else 0.0)
		if primary: UiKit.draw_inked(ci, label, Vector2(r.position.x, ly), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		else: UiKit.draw_text(ci, label, Vector2(r.position.x, ly), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

# ------------------------------------------------------------------ for tests and captures
## What the coach shows now: {mode, entry, step, anchor, rect, on_hud, card, buttons, hits, line, waiting, replay,
## pressed}.
func state() -> Dictionary:
	return {"mode": mode, "entry": entry_id, "step": step, "anchor": str(current().get("anchor", "")), "rect": target, "on_hud": on_hud,
		"card": card, "buttons": buttons.duplicate(), "hits": hits.duplicate(), "line": line, "waiting": why_hidden, "replay": replay,
		"pressed": _pressed}
