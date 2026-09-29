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

const CARD_W := 560.0
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
var _tried := false           ## the step's "try it" was done
var _tab_was := ""
var _hand: ImageTexture = null
var _pressed := ""
var _in_hole := false
var _goal := ""               ## the room the direction mark was asked to lead to (tutorial_goal)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	GameEvents.event.connect(_on_game_event)
	_hand = _hand_texture()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_game_event): GameEvents.event.disconnect(_on_game_event)

## The pointing hand, drawn from HAND (ink edge, paper hand, a jade sleeve).
static func _hand_texture() -> ImageTexture:
	var img := Image.create(HAND[0].length(), HAND.size(), false, Image.FORMAT_RGBA8)
	for y in HAND.size():
		for x in (HAND[y] as String).length():
			var ch := (HAND[y] as String)[x]
			if ch == "#": img.set_pixel(x, y, UiKit.INK)
			elif ch == "W": img.set_pixel(x, y, UiKit.PAPER)
			elif ch == "S": img.set_pixel(x, y, UiKit.JADE)
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
	# 2. The head guide at its element on this page (the node to spend on): before the page's own tour.
	if head != "" and top != null and TutorialRules.chain_home(he, pid, tab) and _element_step(he):
		_show("guide", head, (he.chain as Array).size() - 1)
		_resolve(delta)
		return
	# A guide whose page (and tab) is open now is done: its tour, if unseen, plays next.
	if head != "" and top != null and _arrived(he, pid, tab):
		Game.submit({"type": "tutorial_done", "id": head, "stage": "guide"})
		head = Game.tutorials.head(c)
		he = TutorialRules.entry(head)
	# 3. A tour of the page on top: one in progress, else an unseen one on its first opening.
	if top != null:
		var tour := _page_tour(c, top, pid, tab)
		if tour != "":
			_show("tour", tour, Game.tutorials.step_of(c, tour))
			_resolve(delta)
			return
	# 4. The head guide: a HUD tour with no page open, else the chain's step for what is on screen.
	if head != "":
		if TutorialRules.hud_entry(he):
			if top == null:
				_show("tour", head, Game.tutorials.step_of(c, head))
				_resolve(delta)
				return
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
	return ""

func _element_step(e: Dictionary) -> bool:
	var chain: Array = e.get("chain", [])
	return not chain.is_empty() and str((chain.back() as Dictionary).get("at", "")) == "page" and TutorialRules.same_page(str(chain.back().page), str(e.page))

## A guide has come home: its page is on top, on its tab when it names one, and it has no element step left to show.
func _arrived(e: Dictionary, pid: String, tab: String) -> bool:
	if e.is_empty() or TutorialRules.hud_entry(e) or _element_step(e): return false
	return TutorialRules.same_page(pid, str(e.get("page", ""))) and (str(e.get("tab", "")) == "" or str(e.tab) == tab)

## The tour to show on the page on top: one in progress on this page, else the first unseen one for it and its tab, if
## no tour has played on this opening yet.
func _page_tour(c, top: Page, pid: String, tab: String) -> String:
	for e in TutorialRules.entries():
		var id := str(e.id)
		if Game.tutorials.in_progress(c, id) and not Game.tutorials.seen(c, id) and TutorialRules.same_page(str(e.get("page", "")), pid):
			return id
	if _toured.has(top.get_instance_id()): return ""
	for id in TutorialRules.tours_for(pid, tab):
		if not Game.tutorials.seen(c, str(id)): return str(id)
	return ""

func _show(m: String, id: String, i: int) -> void:
	if m != mode or id != entry_id or i != step:
		_tried = false
		_missing = 0.0
		_pressed = ""
	mode = m
	entry_id = id
	step = i
	# A "go to the place" step leads the direction mark (and the World map's lantern) there while it shows.
	var goal := ""
	if m == "guide":
		var st := current()
		if str(st.get("at", "")) == "place": goal = str(TutorialRules.place(str(st.get("place", ""))).get("room", ""))
	if goal != _goal and Game.active() != null:
		_goal = goal
		Game.submit({"type": "tutorial_goal", "room": goal})
	if m == "":
		target = Rect2()
		card = Rect2()
		buttons = {}
		line = ""

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
	if mode == "guide" and str(st.get("at", "")) == "place": target = _place_target(str(st.get("place", "")))
	_missing = 0.0 if target.size != Vector2.ZERO else _missing + delta
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

## A place's thing in the world, where the room shows it now (its label's spot over it); Rect2() in another room.
func _place_target(place_id: String) -> Rect2:
	var pl := TutorialRules.place(place_id)
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
			var pl := TutorialRules.place(str(st.get("place", "")))
			return Tx.t("ui.tutorial.go.place") % str(pl.get("name", Tx.t(str(st.get("name", "ui.tutorial.go.there")))))
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
	if event.pressed:
		_pressed = hit
	else:
		if hit != "" and hit == _pressed: press(hit)
		_pressed = ""
	accept_event()

## A card button: Next, Skip (the tour) or Later (the guide).
func press(which: String) -> void:
	match which:
		"next": _next()
		"skip", "later":
			Audio.ui("ui_back")
			_finish(true)

# ------------------------------------------------------------------ layout
func _layout() -> void:
	var lines := UiKit.wrap(line, TEXT, TEXT_W)
	var h := PAD + lines.size() * UiKit.line_height(TEXT) + 12.0 + BTN_H + PAD
	var sz := Vector2(CARD_W if mode == "tour" else 440.0, h)
	card = _card_place(sz)
	buttons = {}
	var y := card.end.y - PAD - BTN_H
	if mode == "tour":
		buttons["next"] = Rect2(card.end.x - PAD - BTN_W, y, BTN_W, BTN_H)
		buttons["skip"] = Rect2(card.end.x - PAD * 1.5 - BTN_W * 2.0, y, BTN_W, BTN_H)
	else:
		buttons["later"] = Rect2(card.end.x - PAD - BTN_W, y, BTN_W, BTN_H)
		# The element at the chain's end (the node to spend on) may be passed over with Next, to the page's tour.
		var e := TutorialRules.entry(entry_id)
		if _element_step(e) and step == (e.get("chain", []) as Array).size() - 1:
			buttons["next"] = Rect2(card.end.x - PAD * 1.5 - BTN_W * 2.0, y, BTN_W, BTN_H)

## Where the card stands: under the anchor, else over it, else beside it, inside the safe area and clear of it (and of
## the hand); in the middle of the lower half with no anchor.
func _card_place(sz: Vector2) -> Rect2:
	var safe := Rect2(24, 16, 1232, 688)
	if target.size == Vector2.ZERO: return Rect2(Vector2(640 - sz.x * 0.5, 440), sz)
	var keep := target.grow(8.0 + HAND.size() * HAND_K)
	var cx := clampf(target.get_center().x - sz.x * 0.5, safe.position.x, safe.end.x - sz.x)
	var cy := clampf(target.get_center().y - sz.y * 0.5, safe.position.y, safe.end.y - sz.y)
	var tries := [Vector2(cx, keep.end.y + 4), Vector2(cx, keep.position.y - sz.y - 4),
		Vector2(keep.position.x - sz.x - 4, cy), Vector2(keep.end.x + 4, cy)]
	for p in tries:
		var r := Rect2(p, sz)
		if safe.encloses(r) and not r.intersects(target.grow(6)): return r
	# Nowhere clear: the half of the screen away from the anchor.
	return Rect2(Vector2(640 - sz.x * 0.5, 80 if target.get_center().y > 360 else 720 - 80 - sz.y), sz)

## Where the hand points from, and which way: under the anchor pointing up, or over it pointing down, bobbing.
func hand_rect() -> Rect2:
	if target.size == Vector2.ZERO: return Rect2()
	var hs := Vector2(HAND[0].length(), HAND.size()) * HAND_K
	var bob := 0.0 if UiKit.reduce_motion() else roundf(sin(t * 5.0) * 5.0)
	var up := target.get_center().y > 200.0 or target.end.y + hs.y + 12 > 720
	var x := clampf(target.get_center().x - hs.x * 0.3, 0, 1280 - hs.x)
	if up: return Rect2(Vector2(x, target.position.y - hs.y - 6 - bob), hs)   # over it, the finger down
	return Rect2(Vector2(x, target.end.y + 6 + bob), hs)

# ------------------------------------------------------------------ drawing
func _draw() -> void:
	if mode == "": return
	var pulse := 0.0 if UiKit.reduce_motion() else 0.5 + 0.5 * sin(t * 4.0)
	if _dims():
		var hole := target.grow(8) if target.size != Vector2.ZERO else Rect2(640, 360, 0, 0)
		var dim := Color(UiKit.DIM, 0.62)
		draw_rect(Rect2(0, 0, 1280, hole.position.y), dim)
		draw_rect(Rect2(0, hole.end.y, 1280, 720 - hole.end.y), dim)
		draw_rect(Rect2(0, hole.position.y, hole.position.x, hole.size.y), dim)
		draw_rect(Rect2(hole.end.x, hole.position.y, 1280 - hole.end.x, hole.size.y), dim)
	if target.size != Vector2.ZERO:
		var ring := target.grow(8.0 + pulse * 3.0)
		draw_rect(ring.grow(2), Color(UiKit.INK, 0.8), false, 5.0)
		draw_rect(ring, Color(UiKit.GOLD, 0.75 + 0.25 * pulse), false, 3.0)
		if mode == "guide" and on_hud:
			# The pulsing badge on the HUD button: a vermilion "!" at its top right.
			var bc := Vector2(target.end.x - 2, target.position.y + 2)
			draw_circle(bc, 12.0 + pulse * 1.5, UiKit.INK, true, -1.0, true)
			draw_circle(bc, 10.0 + pulse * 1.5, UiKit.RED, true, -1.0, true)
			UiKit.draw_text(self, "!", bc + Vector2(-10, 6), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 20)
		var hr := hand_rect()
		var up := hr.position.y < target.position.y
		draw_texture_rect(_hand, Rect2(hr.position + Vector2(0, hr.size.y) if up else hr.position, Vector2(hr.size.x, -hr.size.y) if up else hr.size), false)
	_draw_card()

func _draw_card() -> void:
	if card.size == Vector2.ZERO: return
	draw_style_box(UiKit.style("minor_panel"), card)
	var y := card.position.y + PAD + TEXT * UiKit.text_scale()
	for ln in UiKit.wrap(line, TEXT, TEXT_W):
		UiKit.draw_text(self, str(ln), Vector2(card.position.x + 24, y), TEXT, UiKit.PAPER)
		y += UiKit.line_height(TEXT)
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
