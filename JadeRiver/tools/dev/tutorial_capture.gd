extends "res://tools/dev/topdown_capture.gd"
## Decision 43 (docs/redesign/tutorials.md): the unlock tutorials' coach at the phone layout (the 1280 x 720 canvas a
## phone scales), into docs/redesign/feedback/tutorials/. A top-down character on the capture's own saves (never the Max
## Tester's), in Lotus Ferry's village at midday with the story's scenes seen:
##   foundation_1 … : its first foundation points, step by step: the hand and the "!" on the Menu button, the Menu with
##                    the hand on Cultivation, the Foundation tab, the +1, then each step of the tab's tour;
##   techniques_1 … : the Techniques page's tour on its first opening;
##   quests_1 …     : the Quests page's tour on its first opening (the tracker's guide first).
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/tutorial_capture.tscn

const FEEDBACK := "res://docs/redesign/feedback/tutorials/"
const CAP_SAVES := "user://tutorial_capture_saves/"
const UNLOCKS := ["move", "bag", "navigation", "jump", "shop", "quick_use", "attack", "loot", "menu", "cultivate", "cultivation",
	"codex", "equipment", "weapons", "technique_slots_2", "foundation"]

func _main() -> void:
	DirAccess.make_dir_recursive_absolute(CAP_SAVES)
	for f in DirAccess.get_files_at(CAP_SAVES): DirAccess.remove_absolute(CAP_SAVES + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FEEDBACK))
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(CAP_SAVES)
	Game.boot()
	Game.autosave_enabled = false
	await _topdown_game(FEEDBACK)
	await frames(30)
	await _stage()
	await _foundation()
	await _techniques()
	await _quests()
	print("tutorial_capture: done")
	get_tree().quit()

## Every scene seen, the Prologue's systems open and every tutorial but the three shown counted as known, in the
## village by the lane.
func _stage() -> void:
	var c = Game.active()
	for row in ContentDB.all("scenes"): c.quests.scenes[str(row.id)] = {"done": true}
	for i in 8:
		if main.scenes.run == null: break
		main.scenes._finish(true)
		await frames(2)
	for e in TutorialRules.entries():
		if str(e.id) in ["foundation", "techniques", "quests"]: continue
		c.tutorials.guided[str(e.id)] = 1
		c.tutorials.seen[str(e.id)] = 1
	c.tutorials.guided["quests"] = 1   # the Quests page's tour on its opening, not its guide
	for u in UNLOCKS: Unlocks.force_unlock(c.id, u)
	for q in ["morning_tide", "a_quiet_river"]:
		c.quests.active.erase(q)
		c.quests.done[q] = 1
	Game.world.load_room(c, "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	main.close_all_pages()
	await frames(40)
	main.hud.fight_override = false

func _clear() -> void:
	main.hud.toasts = []
	main.hud.log_lines = []
	main.hud.pulses = {}
	main.hud.banner.t = 99.0

func _snap(name: String) -> void:
	_clear()
	await frames(12)
	await shot(name, FEEDBACK)
	var st: Dictionary = main.coach.state()
	print("tutorial_capture: %s %s %s step %d at %s: %s" % [name, st.mode, st.entry, int(st.step), str(st.rect), str(st.line)])

## The first foundation points, from the HUD to the node and the tab's tour.
func _foundation() -> void:
	var c = Game.active()
	c.cultivator.realm_key = "bone_forging_1"
	Game.progression._levels_gained(c, 0, ProgressionRules.level(c))
	GameEvents.flush()
	await frames(20)
	await _snap("foundation_1_hud")
	main.open_page("menu", {})
	await frames(30)
	await _snap("foundation_2_menu")
	main.open_page("cultivation", {})
	await frames(30)
	await _snap("foundation_3_tab")
	var cp: Page = main.top_page()
	for i in cp.tabs.size():
		if str(cp.tabs[i].id) == "foundation": cp.tab = i
	cp.queue_redraw()
	await frames(20)
	await _snap("foundation_4_node")
	Game.submit({"type": "open_meridian", "channel": "body"})
	GameEvents.flush()
	await frames(20)
	var n: int = (TutorialRules.entry("foundation").tour as Array).size()
	for i in n:
		await _snap("foundation_%d_tour_%d" % [5 + i, i + 1])
		main.coach.press("next")
		await frames(4)
	main.close_all_pages()
	await frames(10)

## The Techniques page's tour on its first opening.
func _techniques() -> void:
	main.open_page("techniques", {})
	await frames(200)
	var n: int = (TutorialRules.entry("techniques").tour as Array).size()
	for i in n:
		await _snap("techniques_%d" % (i + 1))
		main.coach.press("next")
		await frames(6)
	main.close_all_pages()
	await frames(10)

## The Quests page's tour on its first opening.
func _quests() -> void:
	main.open_page("quests", {})
	await frames(40)
	var n: int = (TutorialRules.entry("quests").tour as Array).size()
	for i in n:
		await _snap("quests_%d" % (i + 1))
		main.coach.press("next")
		await frames(6)
	main.close_all_pages()
	await frames(10)
