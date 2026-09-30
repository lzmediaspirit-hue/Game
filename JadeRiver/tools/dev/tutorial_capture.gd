extends "res://tools/dev/topdown_capture.gd"
## Decision 43 (docs/redesign/tutorials.md): the unlock tutorials' coach at the phone layout (the 1280 x 720 canvas a
## phone scales), into docs/redesign/feedback/tutorials/. A top-down character on the capture's own saves (never the Max
## Tester's), in Lotus Ferry's village at midday with the story's scenes seen:
##   foundation_1 … : its first foundation points, step by step: the hand and the "!" on the Menu button, the Menu with
##                    the hand on Cultivation, the Foundation tab, the +1, then each step of the tab's tour;
##   techniques_1 … : the Techniques page's tour on its first opening;
##   quests_1 …     : the Quests page's tour on its first opening (the tracker's guide first).
## With `-- --late` (decision 44), the late HUD powers' lessons into feedback/tutorials/late_powers/ instead, the
## character brought to the realm that opens each: the treasures and the weapon swap (Heart Tempering 1), Spirit Sense
## (Spirit Awakening 1), the Presence (Will Manifest 1) and the Sphere (Sphere Lord 1); each guide's steps and each tour
## step (see _late_powers).
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
	if "--late" in OS.get_cmdline_user_args():
		await _late_powers()
	else:
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

func _snap(name: String, dir := FEEDBACK) -> void:
	_clear()
	await frames(12)
	await shot(name, dir)
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

## Decision 44: the late HUD powers' lessons, in the order the realms open them. Each: the power's lesson made unseen,
## the character at its realm (pools full, the fan open), the power unlocked; then its guide and tour, step by step:
##   treasure_1 … : the tour at rest (where the button comes out in a fight, the Qi bar, the Bag), the Bag's button and
##                  the treasure in the Bag;
##   weapon_swap_1 … : the Bag's button, a weapon in the Bag, Set as spare, the hand on Swap, the tour;
##   sense_1 … : the hand on the folded fan, then on Spirit Sense in the open fan, the tour;
##   presence_1 … : the hand on the Presence, the tour;
##   sphere_1 … : the hand on the Sphere, the tour, then the Menu's button, Cultivation's tablet and the Dao tab.
const LATE := "res://docs/redesign/feedback/tutorials/late_powers/"
func _late_powers() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(LATE))
	var c = Game.active()
	for e in TutorialRules.entries():
		c.tutorials.guided[str(e.id)] = 1
		c.tutorials.seen[str(e.id)] = 1
	c.tutorials.queue = []
	for u in ["qi_pool", "guard", "technique_slots_2", "attack", "jump"]: Unlocks.force_unlock(c.id, u)
	Game.progression.apply_learn_technique(c.id, "flowing_palm")
	c.cultivator.technique_slots[0] = "flowing_palm"
	c.cultivator.realm_key = "heart_tempering_1"
	StatRules.rebuild(c, Game.account)
	Game.inventory.apply_add(c.id, "iron_jian", 2, "capture")
	Game.submit({"type": "equip", "index": c.inventory.first_index("iron_jian")})
	GameEvents.flush()
	await frames(240)   # the new technique's moment passes
	main.hud.equip_prompt.dismiss()
	# The treasures (Heart Tempering 1): the tour first, then the guide to the Bag.
	await _late_open("treasure", "heart_tempering_1", ["treasures"])
	Game.inventory.apply_add(c.id, "practice_bell", 1, "capture")
	await _late_tour("treasure", 1)
	await _late_snap("treasure_4_guide_bag")
	main.open_page("inventory", {})
	await frames(30)
	await _late_snap("treasure_5_guide_item")
	main.coach.press("next")
	main.close_all_pages()
	await frames(10)
	# The weapon swap (Heart Tempering 1): the guide to a spare in the Bag, then the hand on Swap and its tour.
	await _late_open("weapon_swap", "heart_tempering_1", ["dual_loadout"])
	await _late_snap("weapon_swap_1_guide_bag")
	main.open_page("inventory", {})
	await frames(30)
	await _late_snap("weapon_swap_2_guide_weapon")
	var bp: Page = main.top_page()
	bp.on_action("bag", c.inventory.first_index("iron_jian"))
	bp.queue_redraw()
	await frames(10)
	await _late_snap("weapon_swap_3_guide_spare")
	bp.on_action("spare", null)
	main.close_all_pages()
	await frames(20)
	await _late_snap("weapon_swap_4_guide_swap")
	main.coach.press("control")
	await frames(4)
	await _late_tour("weapon_swap", 5)
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	await frames(10)
	# Spirit Sense (Spirit Awakening 1): the hand on the folded fan, then on its button; the tour; a pulse.
	main.hud.fan_rest_open = false
	main.hud.fan_open = false
	await _late_open("sense", "spirit_awakening_1", ["spirit_sense"])
	await _late_snap("sense_1_guide_fan")
	main.hud.toggle_fan()
	await frames(6)
	await _late_snap("sense_2_guide_button")
	main.coach.press("control")
	await frames(4)
	await _late_tour("sense", 3)
	Game.submit({"type": "sense_pulse"})
	GameEvents.flush()
	await frames(10)
	# The Presence (Will Manifest 1).
	await _late_open("presence", "will_manifest_1", ["presence"])
	await _late_snap("presence_1_guide")
	main.coach.press("control")
	await frames(4)
	await _late_tour("presence", 2)
	Game.submit({"type": "toggle_presence", "on": false})
	GameEvents.flush()
	await frames(10)
	# The Sphere (Sphere Lord 1): its tour, then the guide on to the Dao tab.
	await _late_open("sphere", "sphere_lord_1", ["dao_tree", "sphere"])
	await _late_snap("sphere_1_guide")
	main.coach.press("control")
	await frames(4)
	await _late_tour("sphere", 2)
	await _late_snap("sphere_5_guide_menu")
	main.open_page("menu", {})
	await frames(30)
	await _late_snap("sphere_6_guide_cultivation")
	main.open_page("cultivation", {})
	await frames(30)
	await _late_snap("sphere_7_guide_dao")
	main.close_all_pages()
	await frames(10)

## The late power `id`'s lesson unseen and the character at `realm`, its pools full, at rest; then `unlocks` opened.
func _late_open(id: String, realm: String, unlocks: Array) -> void:
	var c = Game.active()
	for k in ["guided", "seen", "at"]: c.tutorials[k].erase(id)
	c.tutorials.queue.erase(id)
	c.cultivator.realm_key = realm
	StatRules.rebuild(c, Game.account)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.soul = c.pools.max_soul
	main.hud.fight_override = false
	for u in unlocks: Unlocks.force_unlock(c.id, str(u))
	GameEvents.flush()
	await frames(20)

## Each step of `id`'s tour, from shot number `first`, Next after each (the last, Done).
func _late_tour(id: String, first: int) -> void:
	var n: int = (TutorialRules.entry(id).tour as Array).size()
	for i in n:
		await _late_snap("%s_%d_tour_%d" % [id, first + i, i + 1])
		main.coach.press("next")
		await frames(6)

func _late_snap(name: String) -> void:
	# The pools kept full and the fight's hold off, so every shot shows the lesson at rest.
	var c = Game.active()
	c.pools.qi = c.pools.max_qi
	c.pools.soul = c.pools.max_soul
	await _snap(name, LATE)

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
