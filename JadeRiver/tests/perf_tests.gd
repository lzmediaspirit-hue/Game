extends Node
## Performance (Part 7 · Quality gates): room load under 0.3 s, page open under
## 0.15 s, and a frame with 15 monsters inside the 60 fps budget. Headless on a
## desktop this measures CPU work (simulation, scene building, page setup and
## drawing), not the GPU; it is a regression gate, not the on-phone test.
## Run:  godot --headless --path . res://tests/perf_tests.tscn

const MainScript = preload("res://scripts/main.gd")

var checks := 0
var failures := 0
var main: Node

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var folder := "user://perf_saves/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	Unlocks.debug_force_all = true
	Game.submit({"type": "create_character", "slot": 1, "name": "Perf", "appearance": {"hair": "topknot"}})
	main.enter_world(1)
	for i in 5: await get_tree().process_frame
	await _rooms()
	await _pages()
	await _crowd()
	print("perf_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## Every room: the authority load plus the scene rebuild it triggers.
func _rooms() -> void:
	var c = Game.active()
	var worst := 0.0
	var worst_room := ""
	var total := 0.0
	var ids: Array = ContentDB.rooms.keys()
	ids.sort()
	for rid in ids:
		var t0 := Time.get_ticks_usec()
		Game.world.load_room(c, str(rid), "")
		GameEvents.flush()
		await get_tree().process_frame
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		total += ms
		if ms > worst:
			worst = ms
			worst_room = str(rid)
	print("rooms: %d loaded, average %.0f ms, slowest %s %.0f ms" % [ids.size(), total / ids.size(), worst_room, worst])
	check(worst < 300.0, "every room loads in under 0.3 s (slowest %s: %.0f ms)" % [worst_room, worst])

## Every page: open, set up and draw its first frame.
func _pages() -> void:
	var worst := 0.0
	var worst_page := ""
	for id in MainScript.PAGES:
		if str(id) in ["dialogue", "revival", "welcome", "shop", "fishing", "teleport"]: continue   # need a context to open
		var t0 := Time.get_ticks_usec()
		main.open_page(str(id), {})
		await get_tree().process_frame
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		if ms > worst:
			worst = ms
			worst_page = str(id)
		main.close_all_pages()
		await get_tree().process_frame
	print("pages: slowest %s %.0f ms" % [worst_page, worst])
	check(worst < 150.0, "every page opens in under 0.15 s (slowest %s: %.0f ms)" % [worst_page, worst])

## Fifteen monsters around the player: frame time over two seconds of play.
func _crowd() -> void:
	var c = Game.active()
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	await get_tree().process_frame
	var st: ActorState = Game.actor_state(c.id)
	var spawned := 0
	for i in 15:
		if Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(120 + i * 40, (i % 3) * 20 - 20), 5) != null: spawned += 1
	GameEvents.flush()
	await get_tree().process_frame
	check(spawned == 15, "fifteen monsters spawned (%d)" % spawned)
	var frames := 120
	var t0 := Time.get_ticks_usec()
	for i in frames:
		Game.tick(1.0 / 60.0)
		await get_tree().process_frame
	var per := (Time.get_ticks_usec() - t0) / 1000.0 / frames
	print("crowd: %d monsters, %.2f ms per frame" % [Game.room_rt.living_enemies().size(), per])
	check(per < 16.6, "a frame with fifteen monsters fits the 60 fps budget (%.2f ms)" % per)
