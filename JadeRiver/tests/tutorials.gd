extends Node
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
##      for a system that lives at places, to one that opens the page it teaches; else to the nearest thing it names.
## In-game tests never use the Max Tester save. Run headless:  godot --headless --path . res://tests/tutorials.tscn

const TALKS := ["dialogue", "gift", "mercy", "fates", "revival", "welcome"]   ## pages the coach waits out: no tour
const PROLOGUE_HUD := ["joystick", "context", "bag", "room_banner", "minimap", "quest_tracker", "jump", "currency", "quick_use",
	"hp_bar", "player_panel", "attack", "damage_numbers", "system_log", "enemy_hp_bars", "elite_marker", "menu"]
## HUD parts not taught by a tour of their own: the Prologue's quests teach them, or a guide leads through them (the map
## and the mail buttons are the first steps of their guides), or a bar that shows itself.
const HUD_TAUGHT_ELSEWHERE := ["map", "mail", "soul_bar", "treasure_2", "realm_badge", "progress_bar", "cultivate"]

var checks := 0
var failures := 0
var main: Node
var verbose := false

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)
	elif verbose:
		print("ok: ", what)

func _ready() -> void:
	verbose = "--verbose" in OS.get_cmdline_user_args()
	call_deferred("_main")

func run_root() -> String:
	return "user://test_runs/tutorials_%d/" % OS.get_process_id()

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
	await _anchors()
	main.queue_free()
	await get_tree().process_frame
	_remove_tree(run_root())
	print("tutorials: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

func _remove_tree(dir: String) -> void:
	if not DirAccess.dir_exists_absolute(dir): return
	for d in DirAccess.get_directories_at(dir): _remove_tree(dir + d + "/")
	for f in DirAccess.get_files_at(dir): DirAccess.remove_absolute(dir + f)
	DirAccess.remove_absolute(dir)

func frames(n: int) -> void:
	for i in n: await get_tree().process_frame

func c():
	return Game.active()

func coach() -> TutorialCoach:
	return main.coach

## A tap at `p` through the real input: the coach, the HUD's touches and the pages' regions all see it.
func tap(p: Vector2) -> void:
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = pressed
		ev.position = p
		ev.global_position = p
		get_viewport().push_input(ev, true)
		await frames(2)

func tap_button(which: String) -> void:
	var b: Dictionary = coach().state().buttons
	if b.has(which): await tap((b[which] as Rect2).get_center())
	await frames(3)

## A fresh character in the top-down game, on these saves, every staged scene seen (nothing holds the stage), standing
## at rest; `known`: every tutorial but those named counted guided and seen.
func fresh(but: Array) -> void:
	main.close_all_pages()
	if main.screen == "world": main._unmount_world()
	Game.boot()
	Game.autosave_enabled = false
	for s in Game.characters.keys(): Game.submit({"type": "delete_character", "slot": int(str(s).trim_prefix("c"))})
	Game.submit({"type": "create_character", "slot": 1, "name": "Tutee", "appearance": {"hair": "topknot"}, "view": "topdown"})
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
	# The ones still to come in later builds are listed; the prototype's all have theirs.
	var later := ["sense", "presence", "sphere", "treasure_1", "weapon_swap"]
	var now: Array = []
	for x in untaught:
		if not later.any(func(l): return str(x).begins_with(str(l) + " ")): now.append(x)
	check(now.is_empty(),
		"every HUD control the prototype reaches has its lesson (%s; later: %s)" % [str(untaught), str(later)])
	# Every page of PAGES has a tour, but the talks and events.
	var bare: Array = []
	for id in pages:
		if str(id) in TALKS: continue
		var has := false
		for e in TutorialRules.entries():
			if TutorialRules.same_page(str(e.page), str(id)) and not (e.tour as Array).is_empty(): has = true
		if not has: bare.append(id)
	check(bare.is_empty(), "every page of PAGES has a tour, but the talks and events (%s)" % str(bare))
	# Page tours have 3 to 6 steps; the HUD's 1 to 3.
	var sizes: Array = []
	for e in TutorialRules.entries():
		var n := (e.tour as Array).size()
		var hud := TutorialRules.hud_entry(e)
		if n > 0 and (n > (3 if hud else 6) or (n < 3 and not hud)): sizes.append(str(e.id))
	check(sizes.is_empty(), "every page tour has 3 to 6 steps, a HUD tour 1 to 3 (%s)" % str(sizes))

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
	Game.progression._levels_gained(ch, 0, lv)
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
	await frames(3)
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
	await frames(3)
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
	await frames(3)
	var sp: Page = main.top_page()
	if coach().state().mode == "tour": await tap_button("skip")
	var rp: Rect2 = sp.tour_rect("replay_tutorials")
	check(rp.size.x > 0, "Settings → Controls has Replay tutorials")
	await tap(rp.get_center())
	await frames(3)
	check(ch.tutorials.seen.is_empty(), "Replay tutorials clears every tour seen (%d left)" % ch.tutorials.seen.size())
	main.close_all_pages()
	await frames(2)
	main.open_page("mail", {})
	await frames(3)
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
	await frames(4)
	check(coach().state().mode == "tour" and coach().state().entry == "character", "the Character page's tour starts on its first opening")
	await tap_button("next")
	await tap_button("next")
	check(coach().state().step == 2 and int(ch.tutorials.at.get("character", 0)) == 2, "two steps on (%s)" % str(ch.tutorials.at))
	main.close_all_pages()
	await frames(2)
	Game.save_all()
	main._unmount_world()
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
	await frames(4)
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
