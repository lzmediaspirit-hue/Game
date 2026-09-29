extends "res://tools/dev/topdown_capture.gd"
## Decision 42 ("less monotone walking between places in the sect quest"): screenshots of what the sect stretch has now,
## played in the game with its own SceneDirector, into docs/redesign/feedback/sect/: for each sect, the steward's lesson
## at the gate's transfer array, the array's choice of where to go, the arrival at the Marsh Edge's watch post in a
## column of light, the token humming at the third grey patch, the mentor coming down to the marsh for The Humming
## Token, and the first walk up through the sect's grounds with something on the way in each room (a spar offered, two
## elders overheard, the gardener's favour) to the mentor's word at the top and his peak's array.
## It starts from topdown_tutorial's checkpoints after the Weapon Hall (run it first with
## `-- --keep="The Weapon Hall,The Weapon Hall (Cloud)"`), and moves the story on between the shots as the walk would
## (the quests' own talks), or sets it where a shot needs it (the boarlets' count, Mei Qing's moss and hides).
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --resolution 1280x720 --path . \
##     res://tools/dev/sect_capture.tscn

const SECT_OUT := "res://docs/redesign/feedback/sect/"
const SECT := {
	"jade": {"cp": "the_weapon_hall", "gate": "ja_gate_street", "array": "array_ja_gate", "array_cell": Vector2(8, 22),
		"lesson": "array_lesson_jade", "mentor": "npc_elder_hu_marsh", "descends": "mentor_descends_jade", "peak": "ja_elder_hu_peak",
		"elder": "npc_elder_hu", "peak_scene": "mentor_peak_jade", "peak_array": "array_ja_peak", "peak_cell": Vector2(9, 25)},
	"cloud": {"cp": "the_weapon_hall_(cloud)", "gate": "cm_cliff_stair", "array": "array_cm_gate", "array_cell": Vector2(9, 26),
		"lesson": "array_lesson_cloud", "mentor": "npc_elder_sung_marsh", "descends": "mentor_descends_cloud", "peak": "cm_elder_sung_peak",
		"elder": "npc_elder_sung", "peak_scene": "mentor_peak_cloud", "peak_array": "array_cm_peak", "peak_cell": Vector2(11, 27)}}

func _main() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SECT_OUT))
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	for sect in ["jade", "cloud"]:
		await run_sect(sect)
	print("sect_capture: done")
	get_tree().quit()

func run_sect(sect: String) -> void:
	var s: Dictionary = SECT[sect]
	var tag := "a_jade_" if sect == "jade" else "b_cloud_"
	var src := "user://tutorial_cp/%s/" % str(s.cp)
	var saves := "user://sect_capture_%s/" % sect
	DirAccess.make_dir_recursive_absolute(saves)
	for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
	for f in DirAccess.get_files_at(src): DirAccess.copy_absolute(src + f, saves + f)
	main.close_all_pages()
	Saves.use_folder(saves)
	Game.boot()
	Game.autosave_enabled = false
	for i in 3600:
		if main.PAGES.values().all(func(q): return ResourceLoader.load_threaded_get_status(str(q)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS): break
		await get_tree().process_frame
	main.enter_topdown_tutorial(false)
	await frames(30)
	var c = Game.active()
	print("  capture %s: %s in %s, strange_tracks %s" % [sect, str(c.id) if c else "?", Game.room_rt.room_id if Game.room_rt else "?", str(c.quests.is_active("strange_tracks"))])
	# Out of the Weapon Hall to the gate: the steward stops you and shows the transfer array.
	if Game.room_rt.room_id != str(s.gate):
		Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
		await frames(20)
	if Game.room_rt.room_id != str(s.gate):
		Game.submit({"type": "use_portal", "portal": "west", "crossing": true})
		await frames(20)
	await scene_at(str(s.lesson), "say", 1.6, "transfer array")
	await shot(tag + "01_the_steward_shows_the_array", SECT_OUT)
	await scene_at(str(s.lesson), "handoff", 1.0)
	await shot(tag + "02_step_onto_the_array", SECT_OUT)
	# On the array: where it goes (the watch post, the gate's twin; the peak's is not keyed yet).
	await at_spot(s.array_cell, 30)
	var r := Game.submit({"type": "interact", "object": str(s.array)})
	main.open_page("dialogue", {"convo": r.get("dialogue", {})})
	await frames(240)
	await shot(tag + "03_the_array_asks_where_to", SECT_OUT)
	main.close_all_pages()
	await until_idle()
	Game.submit({"type": "array_travel", "from": str(s.array), "to": "array_marsh"})
	await frames(9)
	await shot(tag + "04_out_at_the_watch_post", SECT_OUT)
	await frames(60)
	if sect == "jade":
		await at_spot(Vector2(8, 16), 60)
		await shot(tag + "05_the_watch_post", SECT_OUT)
	# The three grey patches: at the third the token hums, and the boarlets rise where they were.
	for id in ["grey_patch_0", "grey_patch_1", "grey_patch_2"]:
		var o: Dictionary = Game.room_rt.object_def(id)
		w.player.motor.place(w.room.spot_near(Vector2(float(o.at[0]), float(o.at[1])), 0.0, Vector2(float(o.at[0]) - 30, float(o.at[1]))))
		await frames(4)
		Game.submit({"type": "interact", "object": id})
		main.close_all_pages()
		await frames(4)
	await scene_at("grey_rises", "say", 1.2, "Grey shapes")
	await shot(tag + "06_the_token_hums", SECT_OUT)
	await until_idle()
	# The fifth boarlet down (set, not fought): the mentor comes down to the marsh for the hand-in.
	Game.room_rt.enemies.clear()
	Game.room_rt.spawn_slots.clear()
	await at_spot(Vector2(12, 14), 20)
	var st: Dictionary = c.quests.active.get("the_humming_token", {})
	if not st.is_empty():
		st.progress[0] = 5
		Game.quest._check_ready(c, "the_humming_token")
	GameEvents.flush()
	await scene_at(str(s.descends), "emote", 0.1)
	await shot(tag + "07_the_mentor_comes_down", SECT_OUT)
	await scene_at(str(s.descends), "say", 1.4, "hum")
	await shot(tag + "08_the_mentor_at_the_marsh", SECT_OUT)
	await until_idle()
	await choose(str(s.mentor), "hand_in", "the_humming_token")
	main.close_all_pages()
	await until_idle()
	# Mei Qing at the watch post: her errand taken, gathered (set) and handed in where she stands.
	await choose("npc_mei_qing_marsh", "accept", "mei_qings_errand")
	main.close_all_pages()
	if sect == "jade":
		await at_spot(Vector2(6, 18), 40)
		await shot(tag + "09_mei_qing_at_the_watch_post", SECT_OUT)
	Game.inventory.apply_add(c.id, "willow_moss", 5, "capture")
	Game.inventory.apply_add(c.id, "grey_hide", 3, "capture")
	GameEvents.flush()
	await choose("npc_mei_qing_marsh", "hand_in", "mei_qings_errand")
	main.close_all_pages()
	await until_idle()
	# Grey at the Edges: back to the gate by the watch post's array, and the first walk up the grounds.
	await at_spot(Vector2(4, 18), 20)
	var back := Game.submit({"type": "array_travel", "from": "array_marsh", "to": str(s.array)})
	if not back.get("ok", false): print("  capture: the watch post's array refused: %s" % str(back))
	await frames(30)
	if sect == "jade":
		await walk_to("ja_pavilion_rooftops", "east")
		await scene_at("yard_spar_jade", "say", 1.4, "One round")
		await shot(tag + "10_on_the_way_a_spar_offered", SECT_OUT)
		await until_quiet()
		await walk_to("ja_east_terrace", "east")
		await scene_at("terrace_talk_jade", "say", 1.4, "shrine")
		await shot(tag + "11_on_the_way_elders_overheard", SECT_OUT)
		await until_quiet()
		await walk_to("ja_herb_terraces", "east")
		await scene_at("gardener_favour_jade", "say", 1.4, "lotus")
		await shot(tag + "12_on_the_way_the_gardeners_favour", SECT_OUT)
		await until_quiet()
		await choose("npc_jade_gardener", "accept", "tea_for_the_elder")
		main.close_all_pages()
		await walk_to(str(s.peak), "peak_path")
	else:
		await walk_to("cm_sword_court", "east")
		await scene_at("court_spar_cloud", "say", 1.4, "poles")
		await shot(tag + "10_on_the_way_a_spar_offered", SECT_OUT)
		await until_quiet()
		await walk_to("cm_array_court", "east")
		await scene_at("gardener_favour_cloud", "say", 1.4, "lotus")
		await shot(tag + "11_on_the_way_the_gardeners_favour", SECT_OUT)
		await until_quiet()
		await choose("npc_cloud_gardener", "accept", "tea_for_the_elder")
		main.close_all_pages()
		await scene_at("array_court_talk_cloud", "say", 1.4, "shrine")
		await shot(tag + "12_on_the_way_elders_overheard", SECT_OUT)
		await until_quiet()
		await walk_to(str(s.peak), "peak_path")
	# The report at the top, and the peak's array keyed to the token.
	var e: Dictionary = Game.room_rt.object_def(str(s.elder))
	w.player.motor.place(w.room.spot_near(Vector2(float(e.at[0]), float(e.at[1])), float(e.get("alt", 0.0)), Vector2(float(e.at[0]) - 40, float(e.at[1]) + 20)))
	await frames(6)
	Game.submit({"type": "interact", "object": str(s.elder)})
	main.close_all_pages()
	await scene_at(str(s.peak_scene), "say", 1.2, "array")
	await shot(tag + "13_the_mentor_keys_his_array", SECT_OUT)
	await until_idle()
	await at_spot(s.peak_cell, 30)
	var r2 := Game.submit({"type": "interact", "object": str(s.peak_array)})
	main.open_page("dialogue", {"convo": r2.get("dialogue", {})})
	await frames(240)
	await shot(tag + "14_the_peaks_array", SECT_OUT)
	main.close_all_pages()
	await frames(10)

## Through a way of this room into the next, as the walk would (the next room's live scene begins on arrival).
func walk_to(room_id: String, portal: String) -> void:
	if Game.room_rt.room_id == room_id: return
	Game.submit({"type": "use_portal", "portal": portal, "crossing": true})
	await frames(24)

## Until the scene playing (live or cut) is over or waits on the player.
func until_quiet(limit := 900) -> void:
	for i in limit:
		var r = main.scenes.run
		if r == null or str(r.mode) == "hand": return
		await frames(1)
