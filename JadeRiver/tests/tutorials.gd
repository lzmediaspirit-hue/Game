extends "res://tests/lib/suite.gd"
## tutorials (roadmap decision 43, docs/redesign/tutorials.md): every newly unlocked system teaches itself. On the real
## shell (main.tscn, the HUD, the pages and the coach over them), with a top-down character of its own saves:
##   1. the data: every entry's page is one of main.gd PAGES (tutorials.json's page map is current), every line is a
##      string that wraps to at most two lines on the coach's card at the largest text size, every unlock that opens a
##      page (and every HUD control after the Prologue) has an entry with a guide and a tour, and every page of PAGES
##      has a tour but the talks and events (which the coach waits out);
##   2. the anchors: every tour step's anchor, and every guide step's, is found on its page (or the HUD) as it opens,
##      on its tab, inside the screen;
##   3. the foundation path end to end: a fresh character past the Prologue gains its first foundation points (a Level,
##      through the Progression authority); the hand and the "!" badge point at the HUD's Menu button; a tap there opens
##      the Menu, where the hand points at Cultivation; then the Foundation tab; then the +1 (a point spent through it);
##      then the tour of the tab runs to its end; the rest of the points are spent; nothing is left queued;
##   4. no guide or tour shows in a fight, a staged scene or a talk: it waits, then shows;
##   5. save and load keep the progress: a tour stopped part way resumes at its step, and seen and guided stay; a save
##      from before the tutorials knows what it has (no flood of lessons);
##   6. two unlocks at once queue one after the other, by priority; Later passes a guide by;
##   7. a page's "?" plays its tour again (not recorded), and Settings' Replay tutorials clears what was seen;
##   8. a place step leads the direction mark to the systems-as-places table's place (data/places.json, PlaceRules.home)
##      for a system that lives at places, to one that opens the page it teaches; else to the nearest thing it names;
##   9. decision 44, the late HUD powers (Spirit Sense, the Presence, the Sphere, treasures, the weapon swap): each has a
##      guide and a tour (1); every anchor of them is found once the power is unlocked, on a character at its realm;
##      Spirit Sense end to end (the hand on the fan, then on its button, the tour, a pulse through the spotlight, done);
##      the treasures' tour first and its guide on to the Bag, the Sphere's guide on to the Dao tab after its tour, the
##      weapon swap's guide to a spare in the Bag before its tour; a save from before them knows the powers it has;
##  10. decision 45, the card under a thumb (docs/redesign/tutorials.md "Bugs fixed"), through the phone's own input path
##      (a touch at the window's pixels, which the engine also turns into a mouse click): Done, Skip and Later on the
##      first tap, at an edge, held while the hand bobs, as the card fades in; a double tap acts once and reaches nothing
##      under the card; a page's tour waits for the page to come in; a tab's tour resumes on its tab; a HUD lesson keeps
##      the screen; the next lesson waits a moment; every finger stays the HUD's or the coach's to its release; a fight, a
##      reload and a room change mid-tour; Back skips a tour; cards keep clear of the HUD and the thumbs, and of a tall
##      anchor; the gear guide's hand moves on to Equip; the Cultivate tour lights the folded fan; and the coach's cost.
## In-game tests never use the Max Tester save. Run headless:  godot --headless --path . res://tests/tutorials.tscn

const TALKS := ["dialogue", "gift", "mercy", "fates", "revival", "welcome"]   ## pages the coach waits out: no tour
const PROLOGUE_HUD := ["joystick", "context", "bag", "room_banner", "minimap", "quest_tracker", "jump", "currency", "quick_use",
	"hp_bar", "player_panel", "attack", "damage_numbers", "system_log", "enemy_hp_bars", "elite_marker", "menu"]
## HUD parts not taught by a tour of their own: the Prologue's quests teach them, or a guide leads through them (the map
## and the mail buttons are the first steps of their guides), or a bar that shows itself.
const HUD_TAUGHT_ELSEWHERE := ["map", "mail", "realm_badge", "progress_bar", "cultivate"]
## Decision 44: the late HUD powers, each by its unlock (tools/data/story.py), the HUD role of its control, the realm it
## opens at, the unlocks its lesson's HUD needs besides its own (the panel's bars, the Menu, the Bag, the techniques)
## and the game event its "try it" waits for ("" where it is used only in a fight).
const LATE := {
	"sense": {"unlock": "spirit_sense", "role": "sense", "realm": "spirit_awakening_1", "event": "spirit_sense_pulsed", "with": ["spirit_sense"]},
	"presence": {"unlock": "presence", "role": "presence", "realm": "will_manifest_1", "event": "presence_toggled", "with": ["spirit_sense", "presence"]},
	"sphere": {"unlock": "sphere", "role": "sphere", "realm": "sphere_lord_1", "event": "sphere_toggled", "with": ["spirit_sense", "presence", "dao_tree", "sphere"]},
	"treasure": {"unlock": "treasures", "role": "treasure:0", "realm": "heart_tempering_1", "event": "", "with": ["treasures"]},
	"weapon_swap": {"unlock": "dual_loadout", "role": "swap", "realm": "heart_tempering_1", "event": "loadout_swapped", "with": ["dual_loadout"]},
}
const LATE_BASE := ["bag", "jump", "quick_use", "attack", "menu", "cultivate", "cultivation", "technique_slots_2", "guard", "qi_pool", "navigation"]

var main: Node

## With --verbose, every check that passes is printed too ("ok: ...").
func _init() -> void:
	echo_passes = true

func _main() -> void:
	var folder := run_root()
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(folder)
	Clock.simulate(1789997760.0)
	Game.boot()
	Game.autosave_enabled = false
	_data()
	await _foundation_path()
	await _never_in_the_way()
	await _queue()
	await _replay()
	await _places()
	await _save_and_load()
	_legacy()
	await _sense_path()
	await _late_lessons()
	await _late_legacy()
	await _thumb()
	await _anchors()
	end_suite()

func frames(n: int) -> void:
	for i in n: await get_tree().process_frame

func c():
	return Game.active()

func coach() -> TutorialCoach:
	return main.coach

## A tap at `p` through the real input: the coach, the HUD's touches and the pages' regions all see it. A page it opens
## is let come in (Page.settled: the coach waits for it). A card closed a moment ago guards its place against the second
## tap of a double tap (decision 45): a tap of its own waits that out first.
func tap(p: Vector2) -> void:
	await unguarded()
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = pressed
		ev.position = p
		ev.global_position = p
		get_viewport().push_input(ev, true)
		await frames(2)
	await settle()

## The coach's double-tap guard over (TutorialCoach.GUARD_S of real time).
func unguarded() -> void:
	for i in 2000:
		if coach().guarded() <= 0.0: return
		await get_tree().process_frame

## The page on top has come in (its opening motion over), so the coach may show on it.
func settle() -> void:
	for i in 2000:
		var top: Page = main.top_page()
		if top == null or top.settled(): break
		await get_tree().process_frame
	await frames(2)

## Tap the card's `which` (a card waits a moment, TutorialCoach.MISSING_S, for an anchor not on screen yet).
func tap_button(which: String) -> void:
	for i in 3000:
		if coach().state().mode == "" or coach().state().buttons.has(which): break
		await get_tree().process_frame
	var b: Dictionary = coach().state().buttons
	if b.has(which): await tap((b[which] as Rect2).get_center())
	await frames(3)

## A fresh character in the top-down game, on these saves, every staged scene seen (nothing holds the stage), standing
## at rest; `known`: every tutorial but those named counted guided and seen.
func fresh(but: Array) -> void:
	main.close_all_pages()
	if main.screen == "world": main.unmount_world()
	Game.boot()
	Game.autosave_enabled = false
	for s in Game.characters.keys(): Game.submit({"type": "delete_character", "slot": int(str(s).trim_prefix("c"))})
	Game.submit({"type": "create_character", "slot": 1, "name": "Tutee", "appearance": {"hair": "topknot"}})
	var ch = Game.character("c1")
	for row in ContentDB.all("scenes"): ch.quests.scenes[str(row.id)] = {"done": true}
	know_all_but(ch, but)
	main.enter_world(1)
	await frames(6)
	at_rest()
	main.close_all_pages()
	await frames(4)

## The HUD at rest now: no foe near, and the fight's hold (HUD.FIGHT_HOLD_S) over.
func at_rest() -> void:
	main.hud.fight_override = false
	main.hud.fight_left = 0.0
	main.hud.fight = false

func know_all_but(ch, but: Array) -> void:
	for e in TutorialRules.entries():
		if str(e.id) in but: continue
		ch.tutorials.guided[str(e.id)] = 1
		ch.tutorials.seen[str(e.id)] = 1

func unlock(ids: Array) -> void:
	for u in ids: Unlocks.force_unlock(c().id, str(u))
	GameEvents.flush()

# ------------------------------------------------------------------ 1: the data
func _data() -> void:
	var pages: Dictionary = load("res://scripts/main.gd").PAGES
	var map: Dictionary = ContentDB.config("tutorials").get("page_scripts", {})
	var stale: Array = []
	for id in pages:
		if str(pages[id]).get_file().get_basename() != str(map.get(id, "")): stale.append(id)
	check(stale.is_empty() and map.size() == pages.size(), "tutorials.json's page map is main.gd's PAGES (stale: %s)" % str(stale))
	var bad: Array = []
	var keep_size = Game.account.settings.get("text_size", 1)
	Game.account.settings["text_size"] = 2
	var lines := 0
	for e in TutorialRules.entries():
		if not (str(e.page) in pages or str(e.page) == "hud"): bad.append("%s: page %s" % [e.id, e.page])
		var keys: Array = (e.get("tour", []) as Array).map(func(s): return str(s.text))
		for st in e.get("chain", []):
			if st.has("text"): keys.append(str(st.text))
			if st.has("name"): keys.append(str(st.name))
		if e.has("hint"): keys.append(str(e.hint))
		for k in keys:
			if not ContentDB.strings.has(k):
				bad.append("%s: no string %s" % [e.id, k])
				continue
			if str(k).begins_with("ui.tutorial."):
				lines += 1
				var n := UiKit.wrap(Tx.t(k), TutorialCoach.TEXT, TutorialCoach.TEXT_W).size()
				if n > 2: bad.append("%s: %s wraps to %d lines" % [e.id, k, n])
	Game.account.settings["text_size"] = keep_size
	check(bad.is_empty() and lines > 150, "every tutorial's page is a page, and each of its %d lines a string of at most two lines on the card at the largest text size (%s)" % [lines, str(bad.slice(0, 6))])
	# Every unlock that opens a page has a guide leading there and a tour of it.
	var missing: Array = []
	var tabs := {"foundation": ["cultivation", "foundation"], "dao": ["cultivation", "dao"], "seclusion": ["cultivation", "seclusion"],
		"guild": ["crafts", "guild"], "formations": ["workshop", "formations"], "talisman": ["crafts", "talisman"], "equipment": ["inventory", ""],
		"breakthrough": ["breakthrough", ""]}
	var opened := 0
	for u in ContentDB.all("unlocks"):
		for r in u.get("reveals", []):
			if not str(r).begins_with("page:"): continue
			opened += 1
			var pg := str(r).trim_prefix("page:")
			var at: Array = tabs.get(pg, [pg, ""])
			var guided := false
			for e in TutorialRules.entries():
				if (e.get("chain", []) as Array).is_empty(): continue
				if str(e.trigger.get("unlock", "")) == str(u.id) or (TutorialRules.same_page(str(e.page), str(at[0])) and (str(at[1]) == "" or str(e.tab) == str(at[1]))): guided = true
			var toured := TutorialRules.tour_for(str(at[0]), str(at[1])) != ""
			if not (guided and toured): missing.append("%s (%s): guide %s, tour %s" % [pg, u.id, guided, toured])
	check(missing.is_empty() and opened > 20, "every unlock that opens a page (%d) has a guide to it and a tour of it (%s)" % [opened, str(missing)])
	# Every HUD control that opens after the Prologue is taught: a HUD tour, or the first step of its system's guide.
	var untaught: Array = []
	for u in ContentDB.all("unlocks"):
		for r in u.get("reveals", []):
			var el := str(r).trim_prefix("hud:")
			if not str(r).begins_with("hud:") or el in PROLOGUE_HUD or el in HUD_TAUGHT_ELSEWHERE: continue
			var taught := false
			for e in TutorialRules.entries():
				if str(e.trigger.get("unlock", "")) == str(u.id) and (TutorialRules.hud_entry(e) or not (e.chain as Array).is_empty()): taught = true
			if not taught: untaught.append("%s (%s)" % [el, u.id])
	check(untaught.is_empty(), "every HUD control that opens after the Prologue has its lesson, the late powers too (%s)" % str(untaught))
	# Decision 44: every late HUD power has a guide and a tour. The guide comes from its unlock, and its hand is on the
	# control (a tap there plays the tour) or, for a control only a fight shows, the tour comes first and lights where it
	# comes out. The tour has 2 to 4 steps, lights the control and, for a power used out of a fight, has a "try it" that
	# ends when it is used. The entries are counted known by a save from before them (`since`).
	var late_bad: Array = []
	for id in LATE:
		var e := TutorialRules.entry(str(id))
		var want: Dictionary = LATE[id]
		var tour: Array = e.get("tour", [])
		var at := TutorialRules.tour_at(e)
		var lit := tour.any(func(s): return str(s.anchor).get_slice("|", 0) == str(want.role))
		var tried := str(want.event) == "" or tour.any(func(s): return str(s.get("try", {}).get("event", "")) == str(want.event))
		var pointed := false
		if at >= 0: pointed = str((e.chain[at] as Dictionary).anchor).get_slice("|", 0) == str(want.role)
		elif not tour.is_empty(): pointed = str(tour[0].anchor) == str(want.role)
		if e.is_empty() or not TutorialRules.hud_entry(e) or str(e.trigger.get("unlock", "")) != str(want.unlock) or (e.chain as Array).is_empty() \
				or tour.size() < 2 or tour.size() > 4 or not lit or not tried or not pointed or int(e.get("since", 0)) != TutorialRules.version():
			late_bad.append("%s (control step %d, lit %s, tried %s, pointed %s)" % [id, at, lit, tried, pointed])
	check(late_bad.is_empty() and TutorialRules.version() == 2,
		"every late HUD power (%s) has a guide from its unlock to its control and a tour of 2 to 4 steps that lights it and waits for its use (%s)" % [", ".join(LATE.keys()), str(late_bad)])
	# Every page of PAGES has a tour, but the talks and events.
	var bare: Array = []
	for id in pages:
		if str(id) in TALKS: continue
		var has := false
		for e in TutorialRules.entries():
			if TutorialRules.same_page(str(e.page), str(id)) and not (e.tour as Array).is_empty(): has = true
		if not has: bare.append(id)
	check(bare.is_empty(), "every page of PAGES has a tour, but the talks and events (%s)" % str(bare))
	# Page tours have 3 to 6 steps; the HUD's 1 to 4.
	var sizes: Array = []
	for e in TutorialRules.entries():
		var n := (e.tour as Array).size()
		var hud := TutorialRules.hud_entry(e)
		if n > 0 and (n > (4 if hud else 6) or (n < 3 and not hud)): sizes.append(str(e.id))
	check(sizes.is_empty(), "every page tour has 3 to 6 steps, a HUD tour 1 to 4 (%s)" % str(sizes))

# ------------------------------------------------------------------ 3: the foundation path, end to end
func _foundation_path() -> void:
	await fresh(["foundation"])
	unlock(["menu", "cultivate", "cultivation", "quick_use", "navigation", "foundation"])
	var ch = c()
	await frames(4)
	check(Game.tutorials.head(ch) == "" and coach().state().mode == "", "no guide before the first points (queue %s)" % str(ch.tutorials.queue))
	# The first Level of the path: the Progression authority grants its foundation points.
	ch.cultivator.realm_key = "bone_forging_1"
	var lv := ProgressionRules.level(ch)
	Game.progression.levels_gained(ch, 0, lv)
	GameEvents.flush()
	var pts: int = ch.cultivator.unspent_meridian_points
	await frames(4)
	var st := coach().state()
	var menu_btn: Rect2 = main.hud.tour_rect("icon:menu")
	check(pts > 0 and Game.tutorials.head(ch) == "foundation", "the first foundation points (%d) queue the foundation guide (%s)" % [pts, str(ch.tutorials.queue)])
	check(st.mode == "guide" and st.anchor == "icon:menu" and st.on_hud and st.rect == menu_btn and menu_btn.size.x > 0 and coach().hand_rect().size.x > 0,
		"the hand and the badge point at the HUD's Menu button (%s at %s; hand %s)" % [st.anchor, str(st.rect), str(coach().hand_rect())])
	check(str(st.line) == Tx.t("ui.tutorial.foundation.hint") and st.buttons.has("later"), "its card says why, with Later (%s)" % st.line)
	await tap(menu_btn.get_center())
	await frames(4)
	st = coach().state()
	check(main.top_page() != null and main.top_page().page_id == "menu", "a tap on the Menu button opens the Menu (%s)" % (main.top_page().page_id if main.top_page() else "none"))
	var tablet: Rect2 = main.top_page().tour_rect("open:cultivation") if main.top_page() else Rect2()
	check(st.mode == "guide" and st.anchor == "open:cultivation" and st.rect == tablet and tablet.size.x > 0,
		"the hand points at Cultivation's tablet (%s at %s; the card: %s)" % [st.anchor, str(st.rect), st.line])
	await tap(tablet.get_center())
	await frames(6)
	st = coach().state()
	var cp: Page = main.top_page()
	check(cp != null and cp.page_id == "cultivation", "Cultivation opens (%s)" % (cp.page_id if cp else "none"))
	check(st.mode == "guide" and st.anchor == "tab:foundation" and cp != null and st.rect == cp.tour_rect("tab:foundation"),
		"the hand points at the Foundation tab (%s, %s)" % [st.anchor, st.line])
	if cp != null: await tap(cp.tour_rect("tab:foundation").get_center())
	await frames(4)
	st = coach().state()
	check(cp != null and cp.tab_id() == "foundation" and st.mode == "guide" and st.anchor == "meridian" and st.rect == cp.tour_rect("meridian"),
		"on the tab, the hand points at the +1 to spend on (%s: %s)" % [st.anchor, st.line])
	# The spotlight's +1: a point spent through the page.
	var before: int = ch.cultivator.unspent_meridian_points
	if cp != null: await tap(cp.tour_rect("meridian:body").get_center())
	await frames(4)
	st = coach().state()
	check(ch.cultivator.unspent_meridian_points == before - 1 and ch.tutorials.guided.has("foundation") and not ch.tutorials.queue.has("foundation"),
		"a point spent through the +1 ends the guide (%d left; guided %s)" % [ch.cultivator.unspent_meridian_points, str(ch.tutorials.guided.get("foundation"))])
	check(st.mode == "tour" and st.entry == "foundation" and st.step == 0 and st.rect.size.x > 0, "then the Foundation tab's tour starts, its first anchor lit (%s)" % str(st))
	# The tour, step by step to its end: each step's anchor lit, its words on the card, Next.
	var n: int = (TutorialRules.entry("foundation").tour as Array).size()
	var lit := 0
	for i in n:
		st = coach().state()
		if st.mode == "tour" and st.step == i and st.rect.size.x > 0 and str(st.line) != "": lit += 1
		await tap_button("next")
	st = coach().state()
	check(lit == n and ch.tutorials.seen.has("foundation") and st.mode == "", "the tour ran its %d steps, each anchor lit, and is seen (%d lit; %s)" % [n, lit, str(st)])
	# The rest of the points, spent.
	var guard := 0
	while ch.cultivator.unspent_meridian_points > 0 and guard < 60 and cp != null:
		await tap(cp.tour_rect("meridian:agility").get_center())
		guard += 1
	await frames(4)
	check(ch.cultivator.unspent_meridian_points == 0 and main.hud.point_badges(ch).is_empty() and ch.tutorials.queue.is_empty() and coach().state().mode == "",
		"every point is spent, the badge is gone and nothing waits (%d; %s)" % [ch.cultivator.unspent_meridian_points, str(ch.tutorials.queue)])
	main.close_all_pages()
	await frames(3)

# ------------------------------------------------------------------ 4: never in a fight, a scene or a talk
func _never_in_the_way() -> void:
	await fresh(["mail", "character"])
	unlock(["quick_use", "mail"])
	await frames(4)
	var ch = c()
	check(Game.tutorials.head(ch) == "mail" and coach().state().mode == "guide", "the mail guide shows at rest (%s)" % str(coach().state().mode))
	main.hud.fight_override = true
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "combat", "a foe near: the guide waits (%s)" % str(coach().state()))
	at_rest()
	# Blows traded a moment ago: still a fight for the Combat authority.
	Game.combat.timeline(ch.id)["fight_t"] = Game.sim_time
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "combat", "just after blows: it waits (%s)" % str(coach().state().waiting))
	Game.combat.timeline(ch.id)["fight_t"] = -999.0
	# A staged scene holding the stage.
	main.hud.set_scene_lock(true)
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "scene", "a staged scene: it waits (%s)" % str(coach().state().waiting))
	main.hud.set_scene_lock(false)
	await frames(3)
	check(coach().state().mode == "guide", "the scene over, it shows again")
	# A talk: the dialogue page.
	var talk := Game.submit({"type": "talk", "npc": "aunt_ping"})
	main.open_page("dialogue", {"convo": talk.get("dialogue", {"lines": ["..."], "speaker": "aunt_ping"})})
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "dialogue", "a talk: it waits (%s)" % str(coach().state().waiting))
	main.close_all_pages()
	await frames(3)
	# A page's own tour does not start in a fight either.
	Game.submit({"type": "tutorial_done", "id": "mail", "stage": "guide", "skipped": true})
	main.hud.fight_override = true
	main.open_page("character", {})
	await settle()
	check(coach().state().mode == "" and not ch.tutorials.seen.has("character"), "a page opened in a fight shows no tour (%s)" % str(coach().state()))
	at_rest()
	await frames(3)
	check(coach().state().mode == "tour" and coach().state().entry == "character", "the fight over, its tour starts (%s)" % str(coach().state().entry))
	main.close_all_pages()
	await frames(3)

# ------------------------------------------------------------------ 6: the queue
func _queue() -> void:
	await fresh(["mail", "map"])
	unlock(["quick_use", "mail", "world_menu"])
	await frames(3)
	var ch = c()
	check(ch.tutorials.queue == ["map", "mail"] and coach().state().entry == "map", "two unlocks at once queue one after the other, by priority (%s; shown %s)" % [str(ch.tutorials.queue), coach().state().entry])
	await tap_button("later")
	check(coach().state().mode == "" and coach().state().waiting == "rest", "after Later, the next guide waits a moment (%s)" % coach().state().waiting)
	await card_up("guide")
	check(ch.tutorials.guided.get("map", 0) == 2 and coach().state().entry == "mail" and coach().state().anchor == "icon:mail",
		"Later passes the map's guide by, and the mail's shows next (%s)" % str(coach().state()))
	await tap((coach().state().rect as Rect2).get_center())
	await frames(4)
	check(main.top_page() != null and main.top_page().page_id == "mail" and ch.tutorials.guided.has("mail") and coach().state().mode == "tour",
		"the Mail opens from the lit button, its guide done and its tour started (%s)" % str(coach().state()))
	await tap_button("skip")
	check(ch.tutorials.seen.get("mail", 0) == 2 and coach().state().mode == "", "Skip ends a tour, seen")
	main.close_all_pages()
	await frames(3)
	# A HUD control's tour: on the play screen, dimmed, the HUD's touches held but for the card.
	ch.tutorials.guided.erase("guard")
	ch.tutorials.seen.erase("guard")
	unlock(["guard"])
	await frames(4)
	var st: Dictionary = coach().state()
	var guard_btn: Rect2 = main.hud.tour_rect("guard")
	var away := InputEventMouseButton.new()
	away.position = Vector2(300, 400)
	away.pressed = true
	var on_next := InputEventMouseButton.new()
	on_next.position = (st.buttons.get("next", Rect2()) as Rect2).get_center()
	on_next.pressed = true
	check(st.mode == "tour" and st.entry == "guard" and st.on_hud and st.rect == guard_btn and guard_btn.size.x > 0 and coach().holds(away) and coach().holds(on_next),
		"a HUD tour lights the control on the play screen and holds the HUD's touches (%s)" % str(st))
	for i in 3: await tap_button("next")
	check(ch.tutorials.seen.has("guard") and ch.tutorials.guided.has("guard") and not ch.tutorials.queue.has("guard") and not coach().holds(away),
		"played through, it is seen and the HUD is free again")

# ------------------------------------------------------------------ 7: "?" and Replay
func _replay() -> void:
	var ch = c()
	main.open_page("mail", {})
	await settle()
	var mp: Page = main.top_page()
	var help: Rect2 = mp.tour_rect("help")
	check(help.size.x > 0 and coach().state().mode == "", "a page with a tour has its ?, and a seen tour does not play by itself")
	await tap(help.get_center())
	await frames(3)
	check(coach().state().mode == "tour" and coach().state().entry == "mail" and coach().state().replay == "mail", "the ? plays the page's tour again (%s)" % str(coach().state()))
	await tap_button("next")
	check(coach().state().step == 1 and not ch.tutorials.at.has("mail"), "a tour played again is not recorded")
	main.close_all_pages()
	await frames(3)
	check(coach().state().mode == "", "closing the page ends it")
	main.open_page("settings", {"tab": "controls"})
	await settle()
	var sp: Page = main.top_page()
	if coach().state().mode == "tour": await tap_button("skip")
	var rp: Rect2 = sp.tour_rect("replay_tutorials")
	check(rp.size.x > 0, "Settings → Controls has Replay tutorials")
	await tap(rp.get_center())
	await frames(3)
	check(ch.tutorials.seen.is_empty(), "Replay tutorials clears every tour seen (%d left)" % ch.tutorials.seen.size())
	await frames(10)
	check(coach().state().mode == "", "and Settings, open now, does not start its own tour under the finger: every tour waits for its page's next opening (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)
	main.open_page("mail", {})
	await settle()
	check(coach().state().mode == "tour" and coach().state().entry == "mail" and coach().state().replay == "", "the Mail's tour plays on its next opening (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)

# ------------------------------------------------------------------ 8: places
func _places() -> void:
	await fresh(["notice_board"])
	var ch = c()
	ch.quests.flags["prologue_done"] = true   # the board opens after the fair: the village's board is up by then
	unlock(["notice_board"])
	await frames(4)
	var e := TutorialRules.entry("notice_board")
	var st := coach().state()
	var spot: Dictionary = coach().spot((e.chain as Array)[0])
	check(Game.tutorials.head(ch) == "notice_board" and st.mode == "guide" and str(spot.get("room", "")) != "",
		"the notice board's guide leads to a place (%s: %s)" % [st.mode, str(spot)])
	var from := str(ch.position.get("room", ""))
	if PlaceRules.system_of("notice_board") != "":
		# Decision 43's table has the notice boards: the guide leads to the place a walk there takes (PlaceRules.home), one
		# the character sees (the village's board goes up only after the prologue) by a way open to it.
		var row := TutorialRules.place("notice_board", ch)
		check(str(spot.get("place", "")) == str(row.get("id", "-")) and str(spot.room) == str(row.room) and str(spot.object) == str(row.object)
			and PlaceRules.visible(ch, row) and (str(row.room) == from or not Game.world.route(ch, from, str(row.room)).is_empty()),
			"it is the systems-as-places table's notice board a walk there takes, one standing for the character (%s from %s)" % [str(spot), from])
	else:
		var ok_nearest := true
		var n_best := Game.world.route(ch, from, str(spot.room)).size() if str(spot.room) != from else 0
		for sp in TutorialRules.place_spots((e.chain as Array)[0]):
			var way: Array = Game.world.route(ch, from, str(sp[0])) if str(sp[0]) != from else []
			if (str(sp[0]) == from or not way.is_empty()) and (way.size() if str(sp[0]) != from else 0) < n_best: ok_nearest = false
		check(ok_nearest, "it is the nearest notice board by the ways open (%s from %s)" % [str(spot.room), from])
	check(Game.world.guide_target(ch) == str(spot.room) or str(spot.room) == from, "the direction mark leads there first (%s)" % Game.world.guide_target(ch))
	# The systems-as-places table (data/places.json) leads every place step whose system or page lives at places, to a
	# place that opens the very page the tutorial teaches.
	var used := 0
	var wrong: Array = []
	for te in TutorialRules.entries():
		for s in te.get("chain", []):
			if str(s.get("at", "")) != "place" or PlaceRules.system_of(str(s.get("place", ""))) == "": continue
			used += 1
			var prow := TutorialRules.place(str(s.place), ch)
			if prow.is_empty() or str(prow.get("page", "")) != str(te.get("page", "")): wrong.append("%s: %s" % [te.id, str(prow.get("id", "none"))])
	check(ContentDB.lists.has("places") and used >= 5 and wrong.is_empty(),
		"the systems-as-places table's rows lead the place steps of the systems that live at places, each to its page (%d; %s)" % [used, str(wrong)])
	await tap_button("later")
	check(Game.world.guide_target(ch) != str(spot.room) or str(spot.room) == from, "the guide passed by, the mark leads back to the story")

# ------------------------------------------------------------------ 5: save and load
func _save_and_load() -> void:
	await fresh(["character"])
	unlock(["quick_use", "character_menu"])
	var ch = c()
	main.open_page("character", {})
	await settle()
	check(coach().state().mode == "tour" and coach().state().entry == "character", "the Character page's tour starts on its first opening")
	await tap_button("next")
	await tap_button("next")
	check(coach().state().step == 2 and int(ch.tutorials.at.get("character", 0)) == 2, "two steps on (%s)" % str(ch.tutorials.at))
	main.close_all_pages()
	await frames(2)
	Game.save_all()
	main.unmount_world()
	Game.boot()
	Game.autosave_enabled = false
	main.enter_world(1)
	await frames(6)
	at_rest()
	main.close_all_pages()
	ch = c()
	check(ch.tutorials.get("seen", {}).has("menu") and not ch.tutorials.seen.has("character") and int(ch.tutorials.at.get("character", -1)) == 2 and ch.tutorials.guided.size() > 10,
		"after a reload the progress is kept (at %s; %d guided)" % [str(ch.tutorials.get("at")), ch.tutorials.get("guided", {}).size()])
	main.open_page("character", {})
	await settle()
	check(coach().state().mode == "tour" and coach().state().entry == "character" and coach().state().step == 2, "the tour resumes at its step (%s)" % str(coach().state()))
	for i in 5: await tap_button("next")
	check(ch.tutorials.seen.has("character") and not ch.tutorials.at.has("character"), "and ends seen")
	main.close_all_pages()
	await frames(2)

## A save from before the tutorials: what the character already has counts as known, nothing queued.
func _legacy() -> void:
	var ch = c()
	for u in ["menu", "cultivation", "mail", "world_menu", "character_menu", "technique_slots_2"]: Unlocks.force_unlock(ch.id, u)
	var snap: Dictionary = ch.snapshot()
	snap.erase("tutorials")
	var old := GameCharacter.new()
	old.restore(snap)
	check(old.tutorials.get("legacy", false), "a save from before the tutorials restores as legacy")
	var keep = Game.characters[ch.id]
	Game.characters[ch.id] = old
	Game.tutorials.evaluate(old)
	check(old.tutorials.queue.is_empty() and old.tutorials.guided.has("mail") and old.tutorials.seen.has("techniques") and not old.tutorials.has("legacy"),
		"it knows what it has: nothing queued, its systems guided and seen (%s)" % str(old.tutorials.queue))
	Game.characters[ch.id] = keep

# ------------------------------------------------------------------ 9: the late HUD powers (decision 44)
## A fresh character at the realm that opens the late power `id` (LATE), at rest with the fan open, its pools full, the
## HUD's usual parts open, and every tutorial but that power's known; the power itself still shut.
func late_fresh(id: String) -> void:
	await fresh([id])
	var ch = c()
	ch.cultivator.realm_key = str(LATE[id].realm)
	unlock(LATE_BASE)
	Game.progression.apply_learn_technique(ch.id, "flowing_palm")
	ch.cultivator.technique_slots[0] = "flowing_palm"
	StatRules.rebuild(ch, Game.account)
	ch.pools.hp = ch.pools.max_hp
	ch.pools.qi = ch.pools.max_qi
	ch.pools.soul = ch.pools.max_soul
	main.hud.fan_rest_open = true
	main.hud.fan_open = true
	await frames(3)

func _press(at: Vector2) -> InputEventMouseButton:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.position = at
	ev.pressed = true
	return ev

## Spirit Sense, end to end: a Spirit Awakening character at rest with the fan folded gains Spirit Sense (its unlock).
## The hand and the "!" point at the fan that holds it, with the guide's card and Later; it waits in a fight. A tap
## opens the fan and the hand moves to Spirit Sense's own button. A tap there is the coach's (no pulse) and plays the
## tour: the button lit, then the SL bar, then "try it" with the hand. A tap through the spotlight pulses Spirit Sense
## (Soul spent, 6 s to wait), and the lesson is done, nothing left queued.
func _sense_path() -> void:
	await late_fresh("sense")
	var ch = c()
	main.hud.fan_rest_open = false
	main.hud.fan_open = false
	await frames(3)
	check(Game.tutorials.head(ch) == "" and coach().state().mode == "" and not main.hud.shown("sense"), "no lesson before Spirit Sense opens (%s)" % str(ch.tutorials.queue))
	unlock(["spirit_sense"])
	await frames(4)
	var st := coach().state()
	var fan: Rect2 = main.hud.tour_rect("fan")
	check(Game.tutorials.head(ch) == "sense" and st.mode == "guide" and st.on_hud and st.rect == fan and fan.size.x > 0 and coach().hand_rect().size.x > 0
		and str(st.line) == Tx.t("ui.tutorial.go.fan") % Tx.t("hud.fan_sense") and st.buttons.has("later") and not coach().control,
		"Spirit Sense opens: the hand and the badge point at the folded fan that holds it, the card says to open it, with Later (%s)" % str(st))
	main.hud.fight_override = true
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "combat", "a foe near: the lesson waits (%s)" % str(coach().state().waiting))
	at_rest()
	await frames(3)
	check(coach().state().mode == "guide" and coach().state().entry == "sense", "at rest again, it shows again")
	await tap(fan.get_center())
	await frames(3)
	st = coach().state()
	var sense_btn: Rect2 = main.hud.tour_rect("sense")
	check(main.hud.fan_open and st.mode == "guide" and st.rect == sense_btn and sense_btn.size.x > 0 and coach().control and str(st.line) == Tx.t("ui.tutorial.sense.hint"),
		"a tap opens the fan, and the hand moves to Spirit Sense's own button, the card saying what is new (%s)" % str(st))
	var soul0: float = ch.pools.soul
	await tap(sense_btn.get_center())
	await frames(3)
	st = coach().state()
	check(st.mode == "tour" and st.entry == "sense" and st.step == 0 and st.rect == sense_btn and is_equal_approx(ch.pools.soul, soul0) and ch.pools.cooldown("sense") <= 0.0,
		"a tap on it is the coach's (no pulse yet) and plays the tour, the button lit (%s)" % str(st))
	check(coach().holds(_press(Vector2(300, 400))) and coach().holds(_press(sense_btn.get_center())), "the tour dims the play screen and holds its touches")
	await tap_button("next")
	st = coach().state()
	var soul_bar: Rect2 = main.hud.tour_rect("soul")
	check(st.step == 1 and st.rect == soul_bar and soul_bar.size.x > 0 and main.hud.panel_rect(ch).encloses(soul_bar), "then the SL bar on the panel, what a pulse costs (%s)" % str(st))
	await tap_button("next")
	st = coach().state()
	check(st.step == 2 and st.rect == sense_btn and coach().hand_rect().size.x > 0 and st.buttons.has("next") and not coach().holds(_press(sense_btn.get_center())),
		"the last step: try it, the hand on the button and its spotlight open to a tap (%s)" % str(st))
	await tap(sense_btn.get_center())
	await frames(4)
	st = coach().state()
	check(ch.pools.soul <= soul0 - 5.0 and ch.pools.cooldown("sense") > 0.0 and ch.tutorials.seen.get("sense", 0) == 1 and ch.tutorials.guided.has("sense")
		and not ch.tutorials.queue.has("sense") and st.mode == "",
		"used through the spotlight: Spirit Sense pulses (Soul %d to %d, %.1f s to wait) and the lesson is done, nothing queued (%s)" % [int(soul0), int(ch.pools.soul), ch.pools.cooldown("sense"), str(ch.tutorials.queue)])

## Every late power's lesson, on a character at the realm that opens it, the power just unlocked: its guide is queued;
## every anchor of its guide and its tour is found as the player meets it (the power's own control with the fan open,
## the fan while it is folded; a treasure's place at rest; Swap once a spare is set; the pages' steps as they open).
## Then the lessons that are not Spirit Sense's shape: the treasures' tour first (the button comes out only in a fight)
## and its guide on to the Bag; the Sphere's guide on after its tour to the Dao tab; the weapon swap's guide to the Bag
## first (a spare to set), then its control and tour, used.
func _late_lessons() -> void:
	var miss: Array = []
	var found := 0
	var queued: Array = []
	for id in LATE:
		await late_fresh(str(id))
		var ch = c()
		var want: Dictionary = LATE[id]
		for it in [["practice_bell", 1], ["iron_jian", 2]]: Game.inventory.apply_add(ch.id, str(it[0]), int(it[1]), "test")
		unlock(want.with)
		await frames(3)
		if Game.tutorials.head(ch) != str(id): queued.append("%s: %s" % [id, str(ch.tutorials.queue)])
		coach().set_process(false)
		coach().visible = false
		var e := TutorialRules.entry(str(id))
		var chain: Array = e.chain
		for i in chain.size():
			var s: Dictionary = chain[i]
			found += 1
			if s.get("tour", false) and str(id) == "weapon_swap":
				Game.submit({"type": "set_spare_weapon", "index": ch.inventory.first_index("iron_jian")})
				main.close_all_pages()
				await frames(3)
			match str(s.at):
				"hud":
					main.close_all_pages()
					await frames(2)
					var first := str(s.anchor).get_slice("|", 0)
					if main.hud.tour_rect(first).size.x <= 0 or _hud_find(str(s.anchor)).size.x <= 0: miss.append("%s chain hud: %s" % [id, s.anchor])
					if str(s.anchor).contains("|fan"):
						main.hud.fan_open = false
						await frames(2)
						found += 1
						if _hud_find(str(s.anchor)) != main.hud.tour_rect("fan") or main.hud.tour_rect("fan").size.x <= 0: miss.append("%s chain hud, the fan folded: %s" % [id, s.anchor])
						main.hud.fan_open = true
						await frames(2)
				"page":
					var pg := await _open(str(s.page), str(s.get("tab", "")))
					if pg == null or _page_find(pg, str(s.anchor)).size.x <= 0: miss.append("%s chain %s/%s: %s" % [id, s.page, s.get("tab", ""), s.anchor])
		main.close_all_pages()
		await frames(2)
		for s in e.tour:
			found += 1
			var first := str(s.anchor).get_slice("|", 0)
			if main.hud.tour_rect(first).size.x <= 0 or not Rect2(0, 0, 1280, 720).encloses(main.hud.tour_rect(first)): miss.append("%s tour: %s" % [id, s.anchor])
		coach().set_process(true)
		coach().visible = true
	for m in miss: print("  tutorials: late missing ", m)
	check(queued.is_empty(), "each late power's unlock queues its lesson (%s)" % str(queued))
	check(miss.is_empty() and found >= 25, "every anchor of the late powers' guides and tours (%d) is found once the power is unlocked (%d missing: %s)" % [found, miss.size(), str(miss)])
	await _treasure_lesson()
	await _sphere_lesson()
	await _swap_lesson()

## The treasures: the button comes out only in a fight, so the tour plays first at rest, lighting where it will come
## out, then the Qi bar and the Bag; the guide then leads to the Bag and points at the treasure in it (Next ends it).
func _treasure_lesson() -> void:
	await late_fresh("treasure")
	var ch = c()
	Game.inventory.apply_add(ch.id, "practice_bell", 1, "test")
	unlock(["treasures"])
	await frames(4)
	var st := coach().state()
	var spot: Rect2 = main.hud.tour_rect("treasure:0")
	check(st.mode == "tour" and st.entry == "treasure" and st.step == 0 and st.rect == spot and spot.size.x > 0 and not main.hud.hit_targets().any(func(tg): return str(tg.role) == "treasure:0"),
		"Treasures open: the tour plays at rest, lighting where the button comes out in a fight (%s)" % str(st))
	await tap_button("next")
	check(coach().state().rect == main.hud.tour_rect("qi") and main.hud.tour_rect("qi").size.x > 0, "then the Qi bar a use costs (%s)" % str(coach().state().rect))
	await tap_button("next")
	await tap_button("next")
	st = coach().state()
	check(ch.tutorials.seen.has("treasure") and ch.tutorials.queue.has("treasure") and st.mode == "guide" and st.anchor == "icon:bag" and str(st.line) == Tx.t("ui.tutorial.treasure.hint"),
		"the tour seen, the guide goes on: the hand on the Bag (%s)" % str(st))
	await tap((st.rect as Rect2).get_center())
	await frames(6)
	st = coach().state()
	var bp: Page = main.top_page()
	check(bp != null and bp.page_id == "inventory" and st.mode == "guide" and bp.tour_rect("treasure_item").size.x > 0 and st.rect == bp.tour_rect("treasure_item") and st.buttons.has("next"),
		"in the Bag, the hand points at the treasure to set on the button (%s)" % str(st))
	await tap_button("next")
	check(ch.tutorials.guided.has("treasure") and ch.tutorials.queue.is_empty() and coach().state().mode == "", "Next ends the guide, nothing left queued (%s)" % str(ch.tutorials.queue))
	main.close_all_pages()
	await frames(2)

## The Sphere: the hand on its button, a tap plays the tour, and once it is seen the guide goes on through the Menu and
## Cultivation to the Dao tab, where the Sphere's Dao grows; the tab open, the guide is done.
func _sphere_lesson() -> void:
	await late_fresh("sphere")
	var ch = c()
	unlock(["spirit_sense", "presence", "dao_tree", "sphere"])
	await frames(4)
	var btn: Rect2 = main.hud.tour_rect("sphere")
	var st := coach().state()
	check(st.mode == "guide" and st.entry == "sphere" and st.rect == btn and btn.size.x > 0 and coach().control, "the Sphere opens: the hand on its button in the fan (%s)" % str(st))
	await tap(btn.get_center())
	await frames(3)
	check(coach().state().mode == "tour" and coach().state().entry == "sphere" and not Game.field.sphere_on(ch.id), "a tap plays its tour, the Sphere not raised by it")
	await tap_button("next")
	check(coach().state().rect == main.hud.tour_rect("qi"), "then the Qi bar it spends")
	await tap_button("next")
	await tap_button("next")
	st = coach().state()
	check(ch.tutorials.seen.has("sphere") and ch.tutorials.queue.has("sphere") and st.mode == "guide" and st.anchor == "icon:menu" and str(st.line) == Tx.t("ui.tutorial.sphere.page"),
		"the tour seen, the guide goes on to the Menu (%s)" % str(st))
	await tap((st.rect as Rect2).get_center())
	await frames(4)
	st = coach().state()
	check(main.top_page() != null and main.top_page().page_id == "menu" and st.anchor == "open:cultivation", "then Cultivation's tablet (%s)" % str(st))
	await tap((st.rect as Rect2).get_center())
	await frames(6)
	st = coach().state()
	var cp: Page = main.top_page()
	check(cp != null and cp.page_id == "cultivation" and st.mode == "guide" and st.anchor == "tab:dao" and st.rect == cp.tour_rect("tab:dao"), "then the Dao tab (%s)" % str(st))
	if cp != null: await tap(cp.tour_rect("tab:dao").get_center())
	await frames(4)
	check(cp != null and cp.tab_id() == "dao" and ch.tutorials.guided.has("sphere") and ch.tutorials.queue.is_empty(), "the Dao tab open, the guide is done (%s)" % str(ch.tutorials.queue))
	main.close_all_pages()
	await frames(2)

## The weapon swap: Swap shows only once a spare weapon is set, so the guide leads to the Bag first and points at a
## weapon, then at Set as spare; the Bag closed, the hand is on Swap; its tap plays the tour, and a swap through the
## spotlight ends it, the other weapon in hand.
func _swap_lesson() -> void:
	await late_fresh("weapon_swap")
	var ch = c()
	Game.inventory.apply_add(ch.id, "iron_jian", 2, "test")
	Game.submit({"type": "equip", "index": ch.inventory.first_index("iron_jian")})
	unlock(["dual_loadout"])
	await frames(4)
	var st := coach().state()
	check(st.mode == "guide" and st.entry == "weapon_swap" and st.anchor == "icon:bag" and main.hud.tour_rect("swap").size.x <= 0, "Weapon swap opens: no Swap yet, the hand on the Bag (%s)" % str(st))
	await tap((st.rect as Rect2).get_center())
	await frames(6)
	st = coach().state()
	var bp: Page = main.top_page()
	check(bp != null and bp.page_id == "inventory" and st.mode == "guide" and st.rect == bp.tour_rect("weapon") and bp.tour_rect("weapon").size.x > 0, "in the Bag, the hand on a weapon (%s)" % str(st))
	if bp != null: await tap(bp.tour_rect("weapon").get_center())
	await frames(3)
	st = coach().state()
	check(bp != null and st.rect == bp.tour_rect("spare") and bp.tour_rect("spare").size.x > 0, "chosen, the hand on Set as spare (%s)" % str(st))
	if bp != null: await tap(bp.tour_rect("spare").get_center())
	await frames(3)
	check(ch.inventory.loadout.get("spare") != null, "the spare is set through it")
	main.close_all_pages()
	await frames(4)
	st = coach().state()
	var swap: Rect2 = main.hud.tour_rect("swap")
	check(st.mode == "guide" and st.rect == swap and swap.size.x > 0 and coach().control and str(st.line) == Tx.t("ui.tutorial.weapon_swap.ready"), "the Bag closed, the hand is on Swap (%s)" % str(st))
	await tap(swap.get_center())
	await frames(3)
	check(coach().state().mode == "tour" and coach().state().entry == "weapon_swap", "its tap plays the tour")
	await tap_button("next")
	await tap_button("next")
	var held = ch.inventory.equipped.get("weapon")
	await tap(swap.get_center())
	await frames(4)
	check(ch.inventory.equipped.get("weapon") != held and ch.tutorials.seen.get("weapon_swap", 0) == 1 and ch.tutorials.queue.is_empty() and coach().state().mode == "",
		"a swap through the spotlight ends it, the other weapon in hand (%s)" % str(coach().state()))

## A save from before these lessons (its record at version 1) counts what it already has as known: a Heart Tempering
## character with Treasures and the weapon swap open gets neither lesson, while the same record at version 2 does.
func _late_legacy() -> void:
	await late_fresh("treasure")
	var ch = c()
	unlock(["treasures", "dual_loadout"])
	var rec: Dictionary = ch.tutorials.duplicate(true)
	for id in ["treasure", "weapon_swap"]:
		rec.guided.erase(id)
		rec.seen.erase(id)
	rec.queue = []
	rec.erase("v")
	ch.tutorials = rec.duplicate(true)
	Game.tutorials.evaluate(ch)
	check(ch.tutorials.queue.is_empty() and ch.tutorials.seen.has("treasure") and ch.tutorials.guided.has("weapon_swap") and int(ch.tutorials.get("v", 0)) == 2,
		"a save from before the late lessons knows the powers it has: nothing queued, its record brought to version 2 (%s)" % str(ch.tutorials.queue))
	rec["v"] = 2
	ch.tutorials = rec.duplicate(true)
	Game.tutorials.evaluate(ch)
	check(ch.tutorials.queue.has("treasure") and ch.tutorials.queue.has("weapon_swap"), "a current record is taught them (%s)" % str(ch.tutorials.queue))
	ch.tutorials.queue = []
	for id in ["treasure", "weapon_swap"]:
		ch.tutorials.guided[id] = 1
		ch.tutorials.seen[id] = 1

# ------------------------------------------------------------------ 10: decision 45, the card under a thumb
## Decision 45 (docs/redesign/tutorials.md "Bugs fixed"): the bugs a player met on a phone, each held here through the
## phone's own input path: a touch at the window's pixels (Input.parse_input_event), which the engine also turns into
## a mouse click, as on Android.
func _thumb() -> void:
	await _first_tap()
	await _later_while_bobbing()
	await _double_tap()
	await _while_coming()
	await _tab_tour_on_its_tab()
	await _replay_then_skip()
	await _lesson_keeps_screen()
	await _fingers_kept()
	await _fight_room_reload()
	await _back_skips()
	await _placement()
	await _cost()

## A finger down or up at the canvas point `p`, through the phone's path.
func finger(p: Vector2, down: bool, idx := 0) -> void:
	var e := InputEventScreenTouch.new()
	e.index = idx
	e.position = get_tree().root.get_final_transform() * p
	e.pressed = down
	Input.parse_input_event(e)

func finger_to(p: Vector2, idx := 0) -> void:
	var e := InputEventScreenDrag.new()
	e.index = idx
	e.position = get_tree().root.get_final_transform() * p
	Input.parse_input_event(e)

## A finger's tap through the phone's path: down, `hold` frames, up.
func touch_tap(p: Vector2, hold := 2, idx := 0) -> void:
	finger(p, true, idx)
	await frames(hold + 1)
	finger(p, false, idx)
	await frames(3)

## The coach showing a card in mode `m` (laid out, not waiting for its anchor), within a second of real time.
func card_up(m := "tour", guard_out := true) -> void:
	for i in 5000:
		var st := coach().state()
		if st.mode == m and (st.card as Rect2).size != Vector2.ZERO: break
		await get_tree().process_frame
	if guard_out: await unguarded()   # a card closed a moment ago (the check before) guards its place

## A page tour on its own (its guide counted done), the page opened and come in.
func page_tour(id: String, page: String, unlocks: Array, args := {}) -> Page:
	await fresh([id])
	unlock(unlocks)
	var ch = c()
	ch.tutorials.guided[id] = 1
	ch.tutorials.queue.erase(id)
	main.open_page(page, args)
	await settle()
	await card_up()
	return main.top_page()

## Done and Skip act on the first tap. The buttons are a thumb's targets (48 px and more, their touch targets past
## them); held, one shows pressed and waits for the release, which may roll off its edge; the phone's two events for
## the one tap (the touch, and the click made from it) act once.
func _first_tap() -> void:
	await page_tour("mail", "mail", ["quick_use", "mail"])
	var ch = c()
	var st := coach().state()
	var b: Rect2 = st.buttons.get("next", Rect2())
	var hit: Rect2 = st.hits.get("next", Rect2())
	check(st.mode == "tour" and st.entry == "mail" and b.size.y >= 48.0 and b.size.x >= 48.0 and hit.encloses(b.grow(6.0)),
		"a card's buttons are a thumb's targets: 48 px and more, touch targets past them (%s in %s)" % [str(b), str(hit)])
	var at := b.position + Vector2(8, b.size.y - 3)
	finger(at, true)
	await frames(3)
	var held := coach().state()
	check(held.pressed == "next" and held.step == 0, "held, Next shows pressed and waits for the release (%s, step %d)" % [held.pressed, held.step])
	finger(at + Vector2(0, 14), false)   # the thumb rolls a little as it lifts
	await frames(3)
	check(coach().state().step == 1 and int(ch.tutorials.at.get("mail", -1)) == 1,
		"Next acts once on its release, rolled off its edge, the touch and its click one tap (step %d, at %s)" % [coach().state().step, str(ch.tutorials.at)])
	# A release far off the button lets it go.
	b = coach().state().buttons.get("next", Rect2())
	finger(b.get_center(), true)
	await frames(2)
	finger(b.get_center() + Vector2(0, 90), false)
	await frames(3)
	check(coach().state().step == 1 and coach().state().pressed == "", "a finger that slides well off the button lets it go (step %d)" % coach().state().step)
	for i in 2: await tap_button("next")
	st = coach().state()
	var done: Rect2 = st.buttons.get("next", Rect2())
	check(st.step == 3 and st.buttons.size() == 1, "the last step has Done alone (%s)" % str(st.buttons.keys()))
	await touch_tap(done.end - Vector2(4, 4))   # at its corner
	check(coach().state().mode == "" and ch.tutorials.seen.get("mail", 0) == 1 and not ch.tutorials.at.has("mail"), "Done closes the tour on the first tap, at its corner (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)
	await page_tour("character", "character", ["quick_use", "character_menu"])
	ch = c()
	var skip: Rect2 = coach().state().buttons.get("skip", Rect2())
	await touch_tap(skip.position + Vector2(3, skip.size.y * 0.5))   # at its left edge
	check(coach().state().mode == "" and ch.tutorials.seen.get("character", 0) == 2, "Skip closes the tour on the first tap, at its edge (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)

## A guide's card stands still while its hand bobs (it was placed round the bobbing hand, and moved under the thumb),
## and Later puts the guide off on the first tap, however long it is held.
func _later_while_bobbing() -> void:
	# The Quests' guide: the hand under the tracker, the card under the hand (where it was placed round the bob).
	await fresh(["quests"])
	unlock(["quick_use", "navigation"])
	await card_up("guide")
	var ch = c()
	var hand0: Rect2 = coach().hand_rect(false)
	var card0: Rect2 = coach().state().card
	check(coach().state().entry == "quests" and hand0.size.x > 0 and card0.position.y > hand0.end.y, "the Quests' guide: its card under the hand (%s, hand %s)" % [str(card0), str(hand0)])
	var hands := {}
	var moved := false
	for i in 12:
		coach().t += 0.07   # the hand's bob through its swing
		await frames(1)
		hands[coach().hand_rect().position.y] = true
		if coach().state().card != card0: moved = true
	check(coach().state().mode == "guide" and hands.size() > 2 and not moved, "a guide's card stands still while its hand bobs (%d hand places, card %s)" % [hands.size(), str(coach().state().card)])
	var later: Rect2 = coach().state().buttons.get("later", Rect2())
	var at := later.position + Vector2(later.size.x * 0.5, later.size.y - 2)
	finger(at, true)
	for i in 9:
		coach().t += 0.07
		await frames(1)
	finger(at, false)
	await frames(3)
	check(coach().state().mode == "" and ch.tutorials.guided.get("quests", 0) == 2 and ch.tutorials.queue.is_empty(), "Later puts the guide off on the first tap, held while the hand bobs (%s)" % str(coach().state()))

## A double tap on Done acts once: the second tap reaches nothing under the card (the HUD's control there, the page's
## region), and the tour stays closed.
func _double_tap() -> void:
	await fresh(["guard"])
	unlock(["attack", "guard"])
	await card_up()
	var ch = c()
	await tap_button("next")
	await card_up()
	var st := coach().state()
	var p: Vector2 = (st.buttons.get("next", Rect2()) as Rect2).get_center()
	var under: String = main.hud.role_at(p)
	main.hud.touches.clear()
	finger(p, true)
	await frames(2)
	finger(p, false)
	await frames(1)
	finger(p, true)   # the second tap, a moment after
	await frames(2)
	var reached: bool = not main.hud.touches.is_empty()
	finger(p, false)
	await frames(20)
	check(st.entry == "guard" and st.step == 1 and not reached and coach().state().mode == "" and ch.tutorials.seen.get("guard", 0) == 1,
		"a double tap on a HUD tour's Done closes it once, and its second tap never reaches the HUD under it (%s there; reached %s; %s)" % [under, reached, str(coach().state())])
	# On a page: the second tap is the coach's, never the page's region under the card.
	var pg := await page_tour("character", "character", ["quick_use", "character_menu"])
	ch = c()
	for i in 4:
		if coach().state().buttons.size() == 1: break
		await tap_button("next")
	await card_up()
	var done: Vector2 = (coach().state().buttons.get("next", Rect2()) as Rect2).get_center()
	if pg != null: pg._press_pos = Vector2(-1, -1)
	finger(done, true)
	await frames(2)
	finger(done, false)
	await frames(1)
	finger(done, true)
	await frames(2)
	var page_took: bool = pg != null and pg._press_pos.distance_to(done) < 1.0
	finger(done, false)
	await frames(20)
	check(pg != null and not page_took and main.top_page() == pg and coach().state().mode == "" and ch.tutorials.seen.get("character", 0) == 1,
		"a double tap on a page tour's Done closes it once, and its second tap never reaches the page under it (page took it %s; %s)" % [page_took, str(coach().state())])
	main.close_all_pages()
	await frames(2)

## A page's tour waits for the page to come in (its parts slide into place), then its card stands still from its first
## frame: a tap as it fades in acts.
func _while_coming() -> void:
	await fresh(["character"])
	unlock(["quick_use", "character_menu"])
	var ch = c()
	ch.tutorials.guided["character"] = 1
	await unguarded()
	main.open_page("character", {})
	await frames(1)
	check(coach().state().mode == "" and coach().state().waiting == "opening", "a page's tour waits while the page comes in (%s)" % str(coach().state().waiting))
	await settle()
	await card_up("tour", false)
	var first: Rect2 = coach().state().card
	var alpha := coach().card_alpha()
	var nxt: Rect2 = coach().state().buttons.get("next", Rect2())
	finger(nxt.get_center(), true)
	await frames(2)
	finger(nxt.get_center(), false)
	await frames(3)
	check(alpha < 1.0 and first.size.x > 0 and coach().state().step == 1, "a tap on the card as it fades in acts (alpha %.2f, step %d)" % [alpha, coach().state().step])
	await card_up()
	var c1: Rect2 = coach().state().card
	await frames(30)
	check(coach().state().card == c1, "its card stands still once shown (%s, then %s)" % [str(c1), str(coach().state().card)])
	main.close_all_pages()
	await frames(2)

## A tab's tour under way resumes on its own tab, not on another (it lit nothing there, the card alone in the middle).
func _tab_tour_on_its_tab() -> void:
	await fresh(["foundation"])
	unlock(["menu", "cultivate", "cultivation", "quick_use", "navigation", "foundation"])
	var ch = c()
	ch.tutorials.guided["foundation"] = 1
	ch.tutorials.at["foundation"] = 2
	main.open_page("cultivation", {"tab": "overview"})
	await settle()
	await frames(4)
	var cp: Page = main.top_page()
	check(cp != null and cp.tab_id() == "overview" and coach().state().mode == "", "the Foundation tab's tour under way does not show on the Overview tab (%s)" % str(coach().state()))
	if cp != null: await touch_tap(cp.tour_rect("tab:foundation").get_center())
	await card_up()
	var st := coach().state()
	check(cp != null and cp.tab_id() == "foundation" and st.mode == "tour" and st.entry == "foundation" and st.step == 2 and (st.rect as Rect2).size.x > 0,
		"on its tab it resumes at its step, its anchor lit (%s)" % str(st))
	main.close_all_pages()
	await frames(2)

## A tour played again from "?" and skipped stays closed: no other tour takes its place on that opening (one tour an
## opening), and a tab's tour under way waits for the next.
func _replay_then_skip() -> void:
	await fresh(["foundation"])
	unlock(["menu", "cultivate", "cultivation", "quick_use", "navigation", "foundation"])
	var ch = c()
	ch.tutorials.guided["foundation"] = 1
	ch.tutorials.at["foundation"] = 1
	main.open_page("cultivation", {"tab": "overview"})
	await settle()
	await frames(4)
	var cp: Page = main.top_page()
	check(cp != null and coach().state().mode == "" and cp.tour_rect("help").size.x > 0, "on the Overview tab nothing plays by itself, and it has its ? (%s)" % str(coach().state()))
	if cp != null: await touch_tap(cp.tour_rect("help").get_center())
	await card_up()
	check(coach().state().replay == "cultivation", "its ? plays the page's tour again (%s)" % str(coach().state()))
	await tap_button("skip")
	await frames(20)
	check(coach().state().mode == "", "Skip on the tour played again closes it, and nothing takes its place (%s)" % str(coach().state()))
	await unguarded()
	if cp != null: await touch_tap(cp.tour_rect("tab:foundation").get_center())
	await frames(10)
	check(cp != null and cp.tab_id() == "foundation" and coach().state().mode == "", "on that opening, the Foundation tab's tour under way waits (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)
	main.open_page("cultivation", {"tab": "foundation"})
	await settle()
	await card_up()
	check(coach().state().entry == "foundation" and coach().state().step == 1 and ch.tutorials.seen.get("foundation", 0) == 0, "and resumes at its step on the next (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)

## A HUD lesson under way keeps the screen when a guide of a higher priority is queued behind it (the card no longer
## vanished under the thumb for the Menu's guide); the guide shows once it is done.
func _lesson_keeps_screen() -> void:
	await fresh(["guard", "menu"])
	unlock(["attack", "guard"])
	await card_up()
	var ch = c()
	unlock(["menu"])
	await frames(4)
	var st := coach().state()
	check(ch.tutorials.queue.front() == "menu" and st.mode == "tour" and st.entry == "guard" and st.step == 0,
		"a HUD lesson under way keeps the screen when the Menu's guide (a higher priority) is queued (%s; %s)" % [str(ch.tutorials.queue), str(st)])
	await tap_button("next")
	check(coach().state().entry == "guard" and coach().state().step == 1, "and goes on to its next step (%s)" % str(coach().state()))
	await tap_button("next")
	await card_up("guide")
	check(coach().state().entry == "menu" and ch.tutorials.seen.has("guard"), "then the Menu's guide shows (%s)" % str(coach().state()))

## Every finger is the HUD's or the coach's from its press to its release: a thumb on the stick that slides over a
## guide's card walks on and lets go (the stick was cut off and walked on alone), and a press the coach took is never the
## HUD's, wherever it lifts.
func _fingers_kept() -> void:
	await fresh(["mail"])
	unlock(["quick_use", "mail"])
	await card_up("guide")
	var later: Rect2 = coach().state().buttons.get("later", Rect2())
	var stick := Vector2(200, 560)
	finger(stick, true, 1)
	await frames(2)
	var engaged: bool = main.hud.joystick_id == 1
	finger_to(later.get_center(), 1)
	await frames(2)
	var moving: bool = main.hud.player.movement.length() > 0.5
	finger(later.get_center(), false, 1)
	await frames(3)
	check(engaged and moving and main.hud.joystick_id == -999 and main.hud.player.movement == Vector2.ZERO and coach().state().mode == "guide",
		"a thumb on the stick slides over a guide's card and keeps walking, and lets go where it lifts (engaged %s, moving %s, stick %d)" % [engaged, moving, main.hud.joystick_id])
	await fresh(["guard"])
	unlock(["attack", "guard"])
	await card_up()
	main.hud.touches.clear()
	finger(Vector2(300, 300), true, 2)   # on the dim: the coach's
	await frames(2)
	finger_to(main.hud.attack_center, 2)
	await frames(2)
	finger(main.hud.attack_center, false, 2)
	await frames(3)
	check(main.hud.touches.is_empty() and coach().state().mode == "tour" and coach().state().step == 0,
		"a press the tour took is never the HUD's, dragged and lifted over Attack (%s)" % str(main.hud.touches.keys()))

## A fight, a room change or a reload mid-tour: the card waits (a tap where it was is the HUD's, and moves nothing on),
## then comes back at its step.
func _fight_room_reload() -> void:
	await fresh(["guard"])
	unlock(["attack", "guard"])
	await card_up()
	var ch = c()
	await tap_button("next")
	await card_up()
	var nxt: Vector2 = (coach().state().buttons.get("next", Rect2()) as Rect2).get_center()
	main.hud.fight_override = true
	await frames(3)
	await touch_tap(nxt)
	check(coach().state().mode == "" and coach().state().waiting == "combat" and int(ch.tutorials.at.get("guard", -1)) == 1 and not ch.tutorials.seen.has("guard"),
		"a fight mid-tour: the card waits, and a tap where it was moves nothing on (%s)" % str(ch.tutorials.at))
	at_rest()
	await card_up()
	check(coach().state().entry == "guard" and coach().state().step == 1, "the fight over, it is back at its step (%s)" % str(coach().state()))
	# A save and a reload mid-tour: it resumes at its step.
	Game.save_all()
	main.unmount_world()
	Game.boot()
	Game.autosave_enabled = false
	main.enter_world(1)
	await frames(6)
	at_rest()
	main.close_all_pages()
	await card_up()
	check(coach().state().entry == "guard" and coach().state().step == 1, "after a reload, the HUD tour resumes at its step (%s)" % str(coach().state()))
	await tap_button("next")
	# A room change mid page tour: the pages close, and the tour resumes at its step on the page's next opening.
	await page_tour("character", "character", ["quick_use", "character_menu"])
	ch = c()
	await tap_button("next")
	var from := str(ch.position.get("room", ""))
	var to := ""
	for p in ContentDB.room(from).get("portals", []):
		if str(p.get("to", "")) != "" and not ContentDB.room(str(p.to)).is_empty(): to = str(p.to)
	Game.world.load_room(ch, to, "", Vector2.ZERO)
	GameEvents.flush()
	await frames(6)
	check(to != "" and main.top_page() == null and coach().state().mode == "" and int(ch.tutorials.at.get("character", -1)) == 1,
		"a room change mid-tour closes its page and keeps its step (%s to %s; %s)" % [from, to, str(ch.tutorials.at)])
	at_rest()
	main.open_page("character", {})
	await settle()
	await card_up()
	check(coach().state().entry == "character" and coach().state().step == 1, "it resumes at its step on the page's next opening (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)

## The phone's Back (and Escape) while a tour dims a page skips the tour and keeps the page (it closed the page under the
## tour, and the tour came back on the page's next opening); with no tour, Back closes the page as before.
func _back_skips() -> void:
	var pg := await page_tour("character", "character", ["quick_use", "character_menu"])
	var ch = c()
	main.go_back()
	await frames(3)
	check(main.top_page() == pg and coach().state().mode == "" and ch.tutorials.seen.get("character", 0) == 2, "Back during a tour skips it and keeps its page (%s)" % str(coach().state()))
	main.go_back()
	await frames(3)
	check(main.top_page() == null, "Back again closes the page")
	pg = await page_tour("mail", "mail", ["quick_use", "mail"])
	ch = c()
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE
	esc.physical_keycode = KEY_ESCAPE
	esc.pressed = true
	Input.parse_input_event(esc)
	await frames(3)
	check(main.top_page() == pg and coach().state().mode == "" and ch.tutorials.seen.get("mail", 0) == 2, "Escape during a tour skips it and keeps its page (%s)" % str(coach().state()))
	main.close_all_pages()
	await frames(2)

## Cards keep clear and point true: a guide's card on the play screen keeps off what the HUD shows and off the thumbs'
## places (it sat over the Talk button); a guide waits while the HUD fades back in after a scene; a card keeps off a
## tall anchor (the Cultivation stair); the gear guide's hand moves on to Equip once the piece is chosen; the Cultivate
## tour lights the fan while it is folded.
func _placement() -> void:
	await fresh(["mail"])
	unlock(["quick_use", "mail"])
	await card_up("guide")
	var st := coach().state()
	var over: Array = []
	for r in main.hud.obstacle_rects():
		if (r as Rect2).intersects(st.rect): continue
		if (st.card as Rect2).intersects(r): over.append(str(r))
	for z in TutorialCoach.THUMBS:
		if (st.card as Rect2).intersects(z): over.append("thumbs %s" % str(z))
	check(st.mode == "guide" and over.is_empty(), "a guide's card on the play screen keeps off what the HUD shows and the thumbs' places (card %s over %s)" % [str(st.card), str(over)])
	main.hud.modulate.a = 0.5
	await frames(3)
	check(coach().state().mode == "" and coach().state().waiting == "scene", "a guide waits while the HUD fades back in after a scene (%s)" % coach().state().waiting)
	main.hud.modulate.a = 1.0
	await card_up("guide")
	check(coach().state().mode == "guide", "and shows once it is back")
	# The Cultivation stair: too tall for any side.
	await fresh(["cultivation"])
	unlock(["menu", "cultivate", "cultivation", "quick_use", "navigation"])
	c().tutorials.guided["cultivation"] = 1
	main.open_page("cultivation", {"tab": "overview"})
	await settle()
	await card_up()
	await tap_button("next")
	await card_up()
	st = coach().state()
	check(st.entry == "cultivation" and st.anchor == "stair" and (st.rect as Rect2).size.y > 400 and not (st.card as Rect2).intersects(st.rect),
		"a card keeps off a tall anchor, tight over or under it (%s by the stair %s)" % [str(st.card), str(st.rect)])
	main.close_all_pages()
	await frames(2)
	# The gear guide: the Bag, the piece, then Equip.
	await fresh(["gear"])
	unlock(["bag", "quick_use", "equipment", "weapons"])
	Game.inventory.apply_add(c().id, "training_short_blade", 1, "test")
	GameEvents.flush()
	await card_up("guide")
	await touch_tap((coach().state().rect as Rect2).get_center())
	await settle()
	await card_up("guide")
	var bp: Page = main.top_page()
	var piece: Rect2 = coach().state().rect
	check(bp != null and bp.page_id == "inventory" and piece == bp.tour_rect("gear") and piece.size.x > 0, "the gear guide's hand is on the new piece in the Bag (%s)" % str(coach().state()))
	await touch_tap(piece.get_center())
	await frames(4)
	var eq: Rect2 = bp.tour_rect("equip") if bp != null else Rect2()
	check(eq.size.x > 0 and coach().state().rect == eq, "chosen, the hand moves on to Equip (%s; Equip %s)" % [str(coach().state().rect), str(eq)])
	await touch_tap(eq.get_center())
	await frames(4)
	check(c().tutorials.guided.has("gear") and not c().tutorials.queue.has("gear"), "Equip ends the guide (%s)" % str(c().tutorials.queue))
	main.close_all_pages()
	await frames(2)
	# The Cultivate tour with the fan folded.
	await fresh(["cultivate"])
	main.hud.fan_rest_open = false
	main.hud.fan_open = false
	unlock(["cultivate"])
	await card_up()
	st = coach().state()
	var fan: Rect2 = main.hud.tour_rect("fan")
	check(st.entry == "cultivate" and st.step == 0 and fan.size.x > 0 and st.rect == fan, "the Cultivate tour lights the fan while it is folded (%s; fan %s)" % [str(st.rect), str(fan)])
	await tap_button("skip")
	main.hud.fan_rest_open = true

## What the coach costs a frame: hidden (nothing queued) on the play screen and over a page, next to nothing; showing,
## its lookups made once a frame (the HUD's targets, a page's tours) and its card drawn again only when it changes.
func _cost() -> void:
	await fresh([])
	var us := func() -> int:
		var ts: Array = []
		for i in 120:
			var t0 := Time.get_ticks_usec()
			coach()._process(1.0 / 60.0)
			ts.append(Time.get_ticks_usec() - t0)
		ts.sort()
		return int(ts[60])
	var idle: int = us.call()
	main.open_page("inventory", {})
	await settle()
	var over_page: int = us.call()
	check(coach().state().mode == "" and idle < 100 and over_page < 200,
		"hidden, the coach costs next to nothing a frame: %d us on the play screen, %d us over a page (531 us over a page before decision 45)" % [idle, over_page])
	check(is_same(TutorialRules.tours_for("inventory", ""), TutorialRules.tours_for("inventory", "")), "a page's tours are worked out once, not each frame")
	main.close_all_pages()
	await frames(2)
	await fresh(["guard"])
	unlock(["attack", "guard"])
	await card_up()
	check(is_same(main.hud.tour_targets(), main.hud.tour_targets()), "the HUD's targets are counted once a frame for the coach's anchors")
	for i in 5000:   # the card faded in
		if coach().card_alpha() >= 1.0: break
		await get_tree().process_frame
	await frames(2)
	var draws := {"n": 0}
	var count := func(): draws.n += 1
	coach()._card_view.draw.connect(count)
	for i in 20:
		coach().t += 0.05
		await frames(1)
	coach()._card_view.draw.disconnect(count)
	check(int(draws.n) == 0, "a card that does not change is not drawn again while the ring pulses (%d drawings in 20 frames)" % int(draws.n))
	await tap_button("skip")

# ------------------------------------------------------------------ 2: the anchors
## Every tour step's anchor and every guide step's is found where it is shown, the page opened as the player meets it
## (every system open, a sect joined, a letter carrying something, gear in the bag, points to spend), on its tab.
func _anchors() -> void:
	await fresh([])
	coach().set_process(false)
	coach().visible = false
	var ch = c()
	Unlocks.debug_force_all = true
	_rich(ch)
	var miss: Array = []
	var seen := 0
	for e in TutorialRules.entries():
		# Decision 44's late powers: _late_lessons finds theirs on a character at the realm that opens each.
		if int(e.get("since", 1)) > 1: continue
		if TutorialRules.hud_entry(e):
			for s in e.tour:
				seen += 1
				if _hud_find(str(s.anchor)).size.x <= 0: miss.append("hud %s: %s" % [e.id, s.anchor])
			continue
		for s in e.get("chain", []):
			seen += 1
			match str(s.at):
				"hud": if _hud_find(str(s.anchor)).size.x <= 0: miss.append("%s chain hud: %s" % [e.id, s.anchor])
				"page":
					var pg := await _open(str(s.page), str(s.get("tab", "")))
					if pg == null or _page_find(pg, str(s.anchor)).size.x <= 0: miss.append("%s chain %s/%s: %s" % [e.id, s.page, s.get("tab", ""), s.anchor])
				"place": if TutorialRules.place_spots(s).is_empty(): miss.append("%s chain place %s: nothing matches" % [e.id, s.get("place", "")])
		if (e.tour as Array).is_empty(): continue
		var pg := await _open(str(e.page), str(e.tab))
		if pg == null:
			miss.append("%s: page %s did not open" % [e.id, e.page])
			continue
		for s in e.tour:
			seen += 1
			if _page_find(pg, str(s.anchor)).size.x <= 0 and (await _find_shut(pg, str(s.anchor))).size.x <= 0: miss.append("%s/%s: %s" % [e.page, pg.tab_id(), s.anchor])
			var tr: Dictionary = s.get("try", {})
			if tr.has("tab"):
				for i in pg.tabs.size():
					if str(pg.tabs[i].id) == str(tr.tab): pg.tab = i
				pg.queue_redraw()
				await frames(2)
	Unlocks.debug_force_all = false
	for m in miss: print("  tutorials: missing ", m)
	check(miss.is_empty() and seen > 200, "every tour and guide anchor (%d) is found on its page or the HUD as it shows (%d missing: %s)" % [seen, miss.size(), str(miss.slice(0, 8))])
	main.close_all_pages()
	coach().set_process(true)
	coach().visible = true

## What the pages show once the character has come far: gear in the bag, a letter carrying something, a sect joined,
## an animal and a friend, points to spend, and the skills slotted.
func _rich(ch) -> void:
	for it in [["iron_jian", 2], ["healing_pill", 3], ["herbal_tea", 3], ["spirit_stone_shard", 5]]: Game.inventory.apply_add(ch.id, str(it[0]), int(it[1]), "test")
	ch.cultivator.unspent_meridian_points = 3
	Game.mail.apply_send(ch.id, "welcome_gift", [{"item": "healing_pill", "count": 3}], {})
	Game.training.apply_join(ch.id, "jade_sect")
	Game.progression.apply_learn_technique(ch.id, "flowing_palm")
	ch.cultivator.technique_slots[0] = "flowing_palm"
	for s in ContentDB.all("teleport_stones"): Game.account.teleports[str(s.id)] = true
	GameEvents.flush()

func _hud_find(names: String) -> Rect2:
	for n in names.split("|", false):
		var r: Rect2 = main.hud.tour_rect(n)
		if r.size.x > 0 and Rect2(0, 0, 1280, 720).intersects(r): return r
	return Rect2()

func _page_find(pg: Page, names: String) -> Rect2:
	for n in names.split("|", false):
		var r := pg.tour_rect(n)
		if r.size.x > 0 and Rect2(0, 0, 1280, 720).intersects(r): return r
	return Rect2()

## An anchor that shows only while something is still shut (the Menu's dim tablet): found with the systems as they are.
func _find_shut(pg: Page, names: String) -> Rect2:
	Unlocks.debug_force_all = false
	pg.queue_redraw()
	await frames(2)
	var r := _page_find(pg, names)
	Unlocks.debug_force_all = true
	pg.queue_redraw()
	await frames(2)
	return r

## The page `id` open on top, on `tab` when given (with the context it needs to open), drawn.
func _open(id: String, tab: String) -> Page:
	var top: Page = main.top_page()
	if top != null and top.page_id == id and (tab == "" or top.tab_id() == tab): return top
	main.close_all_pages()
	await frames(1)
	var a: Dictionary = {"shop": {"shop": "old_ma", "npc": "old_ma"}, "library": {}, "fishing": {"object": "fish_9"},
		"transfer_array": {"object": "array_ja_gate"}, "teleport": {}}.get(id, {}).duplicate()
	if tab != "": a["tab"] = tab
	main.open_page(id, a)
	await frames(3)
	var pg: Page = main.top_page()
	if pg != null and tab != "" and pg.tab_id() != tab:
		for i in pg.tabs.size():
			if str(pg.tabs[i].id) == tab: pg.tab = i
		pg.queue_redraw()
		await frames(2)
	return pg
