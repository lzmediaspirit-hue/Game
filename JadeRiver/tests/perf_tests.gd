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
	var per := await _frames(120, Callable())
	print("crowd: %d monsters, %.2f ms per frame" % [Game.room_rt.living_enemies().size(), per])
	check(per < 16.6, "a frame with fifteen monsters fits the 60 fps budget (%.2f ms)" % per)
	# P6e (docs/moments_design.md §7.3): the same crowd under the major breakthrough, then with a Sword Swarm and a Cursive
	# Storm cast every tenth of a second, each striking as many foes as many times as it does. The frame, MomentView and
	# FxLayer included, stays in budget; the FX cap holds; the view's own share is printed.
	var w = main.world
	var mv: MomentView = main.moments
	var spent := [0, 0]   # usec in MomentView.advance, most FX alive
	var view := func(i: int) -> void:
		var t1 := Time.get_ticks_usec()
		mv.advance(1.0 / 60.0)
		spent[0] += Time.get_ticks_usec() - t1
	var storm := func(i: int) -> void:
		view.call(i)
		if i % 6 != 0: return
		for tech in ["sword_swarm", "cursive_storm"]:
			var t := ContentDB.entry("techniques", tech)
			w._cast(tech, 1, UiKit.GOLD)
			for e in Game.room_rt.living_enemies().slice(0, int(t.max_targets)):
				for h in int(t.hits):
					w._on_event("hit_landed", {"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "amount": 12400, "type": "qi", "crit": h == 1,
						"element": str(t.element), "x": e.plane.x, "y": e.plane.y, "alt": 60.0, "source": "tech:" + tech})
		spent[1] = maxi(spent[1], w.fx.fx.size())
	mv.set_process(false)
	mv.preview("breakthrough_major")
	var per_m := await _frames(120, view)
	print("crowd under the breakthrough: %.2f ms per frame (%+.2f ms), MomentView.advance %.3f ms of it" % [per_m, per_m - per, spent[0] / 120000.0])
	mv.clear()
	mv.preview("breakthrough_major")
	var per2 := await _frames(120, storm)
	mv.set_process(true)
	print("with a sword swarm too: %.2f ms per frame, %d FX at most" % [per2, spent[1]])
	check(per_m < 16.6 and per2 < 16.6 and spent[1] <= 160, "the crowd under the breakthrough and a sword swarm fits the budget (%.2f, %.2f ms) and the FX cap (%d)" % [per_m, per2, spent[1]])

## Mean ms per frame over `n` ticked and drawn frames; `each` (frame index) runs at the start of each.
func _frames(n: int, each: Callable) -> float:
	var t0 := Time.get_ticks_usec()
	for i in n:
		if each.is_valid(): each.call(i)
		Game.tick(1.0 / 60.0)
		await get_tree().process_frame
	return (Time.get_ticks_usec() - t0) / 1000.0 / n
