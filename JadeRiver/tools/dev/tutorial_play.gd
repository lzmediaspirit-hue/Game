extends "res://tools/dev/prototype_qa.gd"
## Decision 45 (docs/redesign/tutorials.md "Bugs fixed"): the tutorials played as a player, on the prototype's QA walk
## (tools/dev/prototype_qa.gd: the title, the creator, the opening, the Prologue, the fair, the sect and chapter 2) with
## every guide and tour the coach shows answered by a finger through the game's input path (Input.parse_input_event,
## a touch that also reaches the pages as a mouse click, as on a phone), at the window's own pixels (1280x720, or a
## 20:9 phone's 2400x1080 with the canvas scaled 1.5 between its bars). For each card it meets:
##   - a shot (the first time each step shows) and its layout checked: the card inside the safe area and off its
##     spotlight and the hand, its words at most two lines inside it, its buttons 48 px or more, the anchor found on
##     screen, the hand on screen;
##   - a tour's Next, Skip and Done tapped, in turn at the button's middle and near its edges, at once as the card comes
##     or after a read, now and then twice in quick succession: each must act on the first tap, a double tap must never
##     move two steps nor reach what lies under the card, and a closed tour must stay closed;
##   - a guide followed where it points (between the walk's steps) or put off with Later.
## Every miss is printed as "PLAY BUG" and written to <out>/tutorial_play.json.
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --resolution 1280x720 --path . \
##     res://tools/dev/tutorial_play.tscn -- --out=<dir> [--until=<step>] [--shots]
##     [--from=<saves> --start=<step>] [--only=sweep]
## --shots also keeps the QA walk's own step shots (off by default: only the coach's are taken). The walk's --from and
## --start resume a kept game (tests/prologue_run.gd keeps "Crab Trouble done" and "The River Token" with --keep=; the
## walk's p_night and p_boat start there). --only=sweep plays every lesson the kept game has queued, then each page of
## the Menu once (sweep()). For the phone: -screen 0 2400x1080x24 and --resolution 2400x1080.

var _coach_busy := false
var _seen_keys := {}
var _guides_met := {}
var bugs: Array = []
var met: Array = []
var answers := 0
var qa_shots := false

func _main() -> void:
	qa_shots = "--shots" in OS.get_cmdline_user_args()
	await super._main()

func finish() -> void:
	var f := FileAccess.open(out + "tutorial_play.json", FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"bugs": bugs, "met": met, "answers": answers, "window": str(get_tree().root.size)}, "  "))
		f.close()
	print("PLAY done: %d cards met, %d answered, %d bugs" % [met.size(), answers, bugs.size()])
	await super.finish()

func coach() -> TutorialCoach:
	return main.coach if main != null else null

# ------------------------------------------------------------------ the finger, at the window's pixels
## The canvas point `p` (1280x720) where the window shows it (the phone's scale and bars).
func win(p: Vector2) -> Vector2:
	return get_tree().root.get_final_transform() * p

var _down := {}   ## the fingers on the glass now, by index

func touch(p: Vector2, down: bool, idx := 0) -> void:
	if down: _down[idx] = true
	else: _down.erase(idx)
	var e := InputEventScreenTouch.new()
	e.index = idx
	e.position = win(p)
	e.pressed = down
	Input.parse_input_event(e)

func drag_to(p: Vector2, idx: int) -> void:
	var e := InputEventScreenDrag.new()
	e.index = idx
	e.position = win(p)
	Input.parse_input_event(e)

func shot(name: String, note := "") -> void:
	if qa_shots or name.begins_with("tut_"):
		await super.shot(name, note)
	else:
		notes.append({"shot": "", "room": room(), "note": note})

## Every frame of the walk: a card the coach shows is answered as a player would (a tour at once, it holds the screen;
## a guide's card noted, and followed between the walk's steps).
func frames(k: int) -> void:
	for i in k:
		await get_tree().process_frame
		# Not while the walk's own finger is down (a tap under way): the card is answered once it lifts.
		if _coach_busy or coach() == null or _down.has(0) or _down.has(2) or _down.has(3) or _down.has(5): continue
		var st: Dictionary = coach().state()
		if st.mode == "tour":
			await coach_turn()
		elif st.mode == "guide" and not _guides_met.has(_key(st)):
			_coach_busy = true
			_guides_met[_key(st)] = true
			await look(st)
			_coach_busy = false

func _key(st: Dictionary) -> String:
	var top: Page = main.top_page()
	return "%s|%s|%d|%s|%s" % [st.mode, st.entry, int(st.step), top.page_id if top != null else "-", top.tab_id() if top != null else ""]

func bug(what: String, st := {}) -> void:
	var row := {"what": what, "room": room(), "step": step_now, "coach": _brief(st)}
	bugs.append(row)
	print("PLAY BUG: %s | %s" % [what, str(row.coach)])

func _brief(st: Dictionary) -> Dictionary:
	if st.is_empty(): return {}
	return {"mode": st.mode, "entry": st.entry, "step": st.step, "anchor": st.anchor, "rect": str(st.rect), "card": str(st.card), "line": st.line}

# ------------------------------------------------------------------ a card read
## A card as it shows: its shot (the first time), and its layout held to what a player needs.
func look(first: Dictionary) -> void:
	var k := _key(first)
	if _seen_keys.has(k): return
	_seen_keys[k] = true
	met.append(k)
	# A card waiting for its anchor (TutorialCoach.MISSING_S) is waited for, as the eye waits for it.
	for i in 60:
		if coach().state().mode != first.mode or (coach().state().card as Rect2).size != Vector2.ZERO: break
		await _read(1)
	var seen_card: Rect2 = coach().state().card
	var name := "tut_%s_%s_%d" % [first.mode, first.entry, int(first.step)]
	var top: Page = main.top_page()
	if top != null: name += "_" + top.page_id
	await shot(name, "coach %s: %s" % [k, first.line])
	# Read as the shot shows it (12 frames on): the card must stand where it first showed.
	var st: Dictionary = coach().state()
	if st.mode != first.mode or st.entry != first.entry or st.step != first.step: return
	var safe := Rect2(0, 0, 1280, 720)
	var card: Rect2 = st.card
	var target: Rect2 = st.rect
	if seen_card.size != Vector2.ZERO and card != seen_card: bug("the card moved after it showed (%s to %s)" % [str(seen_card), str(card)], st)
	if card.size == Vector2.ZERO: bug("no card", st)
	elif not safe.encloses(card): bug("the card runs off the screen", st)
	if target.size == Vector2.ZERO: bug("the anchor %s is not found on screen (the card stands alone)" % st.anchor, st)
	elif card.size != Vector2.ZERO and card.intersects(target.grow(2)) and target.get_area() < 0.45 * 1280.0 * 720.0:
		bug("the card covers what it explains", st)   # (a page's whole content leaves the card no clear place)
	var hr: Rect2 = coach().hand_rect(false) if coach()._hand_shown() else Rect2()
	if hr.size != Vector2.ZERO:
		if not safe.encloses(hr): bug("the hand runs off the screen %s" % str(hr), st)
		if card.intersects(hr): bug("the card covers the hand %s" % str(hr), st)
	var lines: Array = coach()._lines()
	if lines.size() > 2: bug("the card's words run to %d lines" % lines.size(), st)
	for ln in lines:
		var w := UiKit.text_width(str(ln), TutorialCoach.TEXT)
		if card.size != Vector2.ZERO and w > card.size.x - 40.0: bug("a line overflows the card (%d px in %d)" % [int(w), int(card.size.x)], st)
	for b in st.buttons:
		var r: Rect2 = st.buttons[b]
		if r.size.y < 48.0 or r.size.x < 48.0: bug("the %s button is under 48 px (%s)" % [b, str(r.size)], st)
		if not card.encloses(r): bug("the %s button is outside its card" % b, st)
	# A guide on the play screen must leave the HUD's controls clear (the player keeps playing under it).
	if st.mode == "guide" and top == null and is_instance_valid(main.hud) and card.size != Vector2.ZERO:
		for tg in main.hud.hit_targets():
			var d := float(tg.drawn)
			var cr := Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0)
			if card.intersects(cr) and not target.intersects(cr): bug("the guide's card covers the HUD's %s" % str(tg.role), st)

# ------------------------------------------------------------------ a tour answered
var _style := 0

## Answer the tour on screen through to its end, the way a player does: read each step, Next; Skip now and then; the
## last Done. Each tap is checked to act the first time.
func coach_turn() -> void:
	_coach_busy = true
	stick(Vector2.ZERO)   # the thumb comes off the stick to read the card
	for guard in 12:
		var st: Dictionary = coach().state()
		if st.mode != "tour": break
		await look(st)
		var n := (TutorialRules.entry(str(st.entry)).get("tour", []) as Array).size()
		var last: bool = int(st.step) + 1 >= n
		_style += 1
		var which := "next"
		if not last and _style % 7 == 3: which = "skip"
		var tr: Dictionary = (TutorialRules.entry(str(st.entry)).tour[int(st.step)] as Dictionary).get("try", {}) if int(st.step) < n else {}
		# A "try it" step: done through its spotlight now and then (the tap tries, the page's own control takes it).
		if not tr.is_empty() and tr.has("tap") and _style % 2 == 0 and (st.rect as Rect2).size != Vector2.ZERO:
			await tap((st.rect as Rect2).get_center())
			await _settle_coach()
			var after: Dictionary = coach().state()
			if after.mode == "tour" and after.entry == st.entry and after.step == st.step: bug("a tap through the try-it spotlight did not move the step on", st)
			continue
		if not st.buttons.has(which): which = "next" if st.buttons.has("next") else str(st.buttons.keys()[0]) if not st.buttons.is_empty() else ""
		if which == "":
			bug("a tour's card with no buttons", st)
			break
		await answer(st, which)
	_coach_busy = false

## Tap the card's `which` at a spot that varies (the middle, near each edge; at once or after a read; now and then a
## quick double tap), and hold the coach to it: the first tap acts, a double tap acts once, and a closed card stays
## closed.
func answer(st: Dictionary, which: String) -> void:
	answers += 1
	var r: Rect2 = st.buttons[which]
	var spots := [r.get_center(), r.position + Vector2(r.size.x * 0.5, 4), r.end - Vector2(r.size.x * 0.5, 4), r.position + Vector2(5, r.size.y * 0.5),
		r.end - Vector2(5, r.size.y * 0.5)]
	var at: Vector2 = spots[_style % spots.size()]
	var double := _style % 5 == 2
	var hold := 2 if _style % 3 != 1 else 9
	if _style % 4 != 0: await _read(24)   # a read first; else at once, as the card comes
	# The card as it stands now, where the finger goes.
	var fresh: Dictionary = coach().state()
	if fresh.mode != st.mode or fresh.entry != st.entry or fresh.step != st.step or not fresh.buttons.has(which): return
	st = fresh
	r = st.buttons[which]
	spots = [r.get_center(), r.position + Vector2(r.size.x * 0.5, 4), r.end - Vector2(r.size.x * 0.5, 4), r.position + Vector2(5, r.size.y * 0.5),
		r.end - Vector2(5, r.size.y * 0.5)]
	at = spots[_style % spots.size()]
	var was_top: Page = main.top_page()
	var was_pages: int = main.pages.size()
	var was_tab: String = was_top.tab_id() if was_top != null else ""
	await _tap_raw(at, hold)
	if double: await _tap_raw(at, 2)
	await _settle_coach()
	var now: Dictionary = coach().state()
	var moved: bool = now.mode != st.mode or now.entry != st.entry or now.step != st.step or now.replay != st.replay
	var how := "%s tap at %s (button %s, %s)" % ["double" if double else "one", str(at), str(r), "held %d frames" % hold]
	if not moved:
		bug("%s did nothing on the first tap: %s" % [which, how], st)
		# A second try, as the player would.
		await _tap_raw(r.get_center(), 2)
		await _settle_coach()
		now = coach().state()
	elif which == "next" and now.mode == st.mode and now.entry == st.entry and int(now.step) > int(st.step) + 1:
		bug("a double tap on Next moved %d steps: %s" % [int(now.step) - int(st.step), how], st)
	if which in ["skip", "done"] or (which == "next" and int(st.step) + 1 >= (TutorialRules.entry(str(st.entry)).tour as Array).size()):
		# Closed: it stays closed, and the tap reached nothing under the card.
		await _read(30)
		var later: Dictionary = coach().state()
		if later.mode == "tour" and later.entry == st.entry: bug("the tour came back after %s: %s" % [which, how], st)
		var top: Page = main.top_page()
		if top != was_top or main.pages.size() != was_pages or (top != null and top.tab_id() != was_tab):
			bug("the tap on %s reached the page or HUD under the card (%s to %s): %s" % [which, was_top.page_id if was_top else "no page", top.page_id if top else "no page", how], st)

## Frames that do not answer the coach (the tap's own).
func _read(k: int) -> void:
	for i in k: await get_tree().process_frame

func _tap_raw(p: Vector2, hold := 2) -> void:
	touch(p, true, 0)
	await _read(hold)
	touch(p, false, 0)
	await _read(1)

func _settle_coach() -> void:
	await _read(3)

# ------------------------------------------------------------------ guides followed between the walk's steps
## The head guide followed to its end, where it points on the HUD and the pages (a place step is left to the walk);
## Later for every third, as a player in a hurry. The pages it opened are closed after.
func follow_guides() -> void:
	if coach() == null: return
	_coach_busy = true
	for guard in 10:
		var st: Dictionary = coach().state()
		if st.mode == "tour":
			_coach_busy = false
			await coach_turn()
			_coach_busy = true
			continue
		if st.mode != "guide": break
		await look(st)
		var cur: Dictionary = coach().current()
		_style += 1
		if _style % 3 == 0 or str(cur.get("at", "")) == "place" or (st.rect as Rect2).size == Vector2.ZERO:
			if st.buttons.has("later"): await answer(st, "later")
			break
		var before := _key(st)
		await _tap_raw((st.rect as Rect2).get_center(), 2)
		await _read(12)
		var now: Dictionary = coach().state()
		if now.mode == "guide" and _key(now) == before and now.entry == st.entry:
			bug("a tap where the guide's hand points did nothing (%s)" % st.anchor, st)
			if st.buttons.has("later"): await answer(st, "later")
			break
	_coach_busy = false
	await close_pages()

## The walk's steps as prototype_qa plays them, with the guides the coach shows followed between them.
func _step_hook() -> void:
	if Game.in_world and main.screen == "world": await follow_guides()

# ------------------------------------------------------------------ the sweep: every lesson a checkpoint holds
## `--only=sweep` (with --from): at rest where the game was kept, every lesson the queue holds, played as a player
## plays it: each guide followed where its hand points (a place's step put off with Later, and every fourth guide put
## off, as a player in a hurry does), each tour answered; then the Menu's pages opened one by one, each first opening's
## tour answered. Ends when the coach has nothing left to show.
func sweep() -> void:
	stick(Vector2.ZERO)
	# A staged scene the checkpoint was kept in (Lu's boat waits on "Talk to Lu"): ended, and the body set in the village
	# at rest (the driver's shortcut, noted; the lessons are what is played).
	for i in 8:
		if main.scenes == null or main.scenes.run == null: break
		main.scenes._finish(true)
		await _read(2)
	if room() != "lf_village":
		say("sweep: set in the village from %s (a driver's shortcut)" % room())
		Game.world.load_room(c(), "lf_village", "", Vector2.ZERO)
		GameEvents.flush()
		await _read(60)
	main.hud.fight_override = false
	var calm := 0
	for round in 80:
		var st := await _card(4.0)
		if st.mode == "":
			calm += 1
			if top_page() != null: await close_pages()
			if calm >= 2: break
			continue
		calm = 0
		if st.mode == "tour":
			await coach_turn()
			continue
		await _follow(st)
	say("sweep: the queue is %s" % str(c().tutorials.get("queue", [])))
	await _menu_pages()
	say("sweep done: %d cards met, %d answered" % [met.size(), answers])

## The coach's card once it shows (a guide or a tour, laid out), or the empty state after `wait_s` seconds of play.
func _card(wait_s_: float) -> Dictionary:
	var start := now_ms()
	while now_ms() - start < wait_s_ * 1000.0:
		await _read(1)
		var st: Dictionary = coach().state()
		if st.mode != "" and (st.card as Rect2).size != Vector2.ZERO: return st
	return coach().state()

var _followed := 0
## One step of a guide, as a player does: its card read and shot, then a tap where the hand points (the lit button,
## tablet, tab or element); a place's step, and every fourth guide, put off with Later. A tap that does nothing moves
## on with Next (an element) or Later.
func _follow(st: Dictionary) -> void:
	_coach_busy = true
	await look(st)
	st = coach().state()
	var cur: Dictionary = coach().current()
	_followed += 1
	if str(cur.get("at", "")) == "place" or (st.rect as Rect2).size == Vector2.ZERO or (_followed % 4 == 0 and int(st.step) == 0):
		if st.buttons.has("later"): await answer(st, "later")
		_coach_busy = false
		return
	var before := _key(st)
	await _tap_raw((st.rect as Rect2).get_center(), 2)
	await _read(20)
	var now: Dictionary = coach().state()
	if now.mode == "guide" and now.entry == st.entry and _key(now) == before:
		# The element's tap opened its card (a piece's Equip): the hand should have moved on to it.
		if str(now.anchor) == str(st.anchor) and now.rect == st.rect:
			bug("a tap where the guide's hand points did nothing (%s)" % st.anchor, st)
			if now.buttons.has("next"): await answer(now, "next")
			elif now.buttons.has("later"): await answer(now, "later")
	_coach_busy = false

## The Menu's pages, each opened from its tablet once: a first opening plays the page's tour.
func _menu_pages() -> void:
	var menu := page_open("menu")
	if menu == null:
		if not await tap_role("icon:menu"): return
		await _read(30)
	menu = page_open("menu")
	if menu == null: return
	var tablets: Array = []
	for r in menu._regions:
		if str(r.id) == "open" and r.enabled and not (str(r.data) in ["exit", "characters"]): tablets.append(str(r.data))
	say("sweep: the Menu's open tablets %s" % str(tablets))
	for pg in tablets:
		menu = page_open("menu")
		if menu == null:
			await tap_role("icon:menu")
			await _read(30)
			menu = page_open("menu")
		if menu == null: break
		await _card(0.6)
		if coach().state().mode == "tour": await coach_turn()
		if not await tap_region(menu, "open", pg): continue
		await _read(10)
		var st := await _card(2.0)
		for i in 6:
			if st.mode == "tour": await coach_turn()
			elif st.mode == "guide": await _follow(st)
			else: break
			st = await _card(1.0)
		# Back to the Menu: the page closed by its own close button.
		var top := top_page()
		if top != null and top.page_id != "menu":
			if not await tap_region(top, "_close"): top.close()
			await _read(12)
	await close_pages()
