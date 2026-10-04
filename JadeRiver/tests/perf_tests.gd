extends "res://tests/lib/suite.gd"
## Performance (Part 7 · Quality gates): room load under 0.3 s, page open under
## 0.15 s, and a frame with 15 monsters inside the 60 fps budget. Headless on a
## desktop this measures CPU work (simulation, scene building, page setup and
## drawing), not the GPU; it is a regression gate, not the on-phone test. It holds on a shared, loaded machine: every
## figure is the game's own time at the machine's full speed, the least of interleaved rounds (see "measuring on a
## shared machine" below). The budgets are the gate's own.
## Run:  godot --headless --path . res://tests/perf_tests.tscn

const MainScript = preload("res://scripts/main.gd")

var main: Node

func _main() -> void:
	var share := ask_for_cpu()
	var queued0 := queued_us()
	var wall0 := Time.get_ticks_usec()
	for k in 5: _cal_best = mini(_cal_best, _calibrate())
	# techniques.json first, on the heap as the boot leaves it (ContentDB reads the table at boot): its defaults took half
	# as long again on a heap the rooms and pages had churned, and the gate compares them with the engine's parse.
	_techniques_json()
	var folder := run_root() + "saves/"
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
	# The page scripts warm one at a time from launch (PageWarmer); the gates below time rooms and pages once they are in,
	# as a player meets them after the title screen.
	var t0 := Time.get_ticks_msec()
	while not main.pages_warm(): await get_tree().process_frame
	print("pages warm %d ms after the world is entered" % (Time.get_ticks_msec() - t0))
	await _rooms()
	await _pages()
	await _crowd()
	await _techniques()
	await _topdown()
	print("measured in %d rounds at the machine's full speed, on the game's own clock (%s; %s): %.0f s in all, %.0f s of it waiting for a CPU other processes held"
		% [ROUNDS, clock_name(), share, (Time.get_ticks_usec() - wall0) / 1e6, (queued_us() - queued0) / 1e6])
	end_suite()

# ------------------------------------------------------------------ measuring on a shared machine (audit 45, BUG-10)
## The gate runs beside other work. Other processes hold the machine's CPUs for seconds at a time (under a steady load a
## fixed piece of script work took 4 to 6 times its wall time, its time on a CPU about the same), and a core busy
## elsewhere slows this one's own work by a third or more. The single timings failed 1 to 5 of the 18 checks on such a
## machine and none when it was quiet. So every figure here is
##   - timed on the game's own clock, `now_us`: the wall clock less the time the main thread stood in the run queue,
##     ready while other processes held every CPU (Linux counts it per thread, /proc/thread-self/schedstat; elsewhere it
##     is the wall clock). All the game does counts: its work, its waits on its own workers, its frames;
##   - taken at the machine's full speed: the same fixed piece of work (_calibrate) is timed beside each sample (each
##     frame of a window), and a sample when it took over SLOW_MACHINE times the fastest seen does not count, unless too
##     few are left to count;
##   - taken in ROUNDS interleaved rounds (every room once, then every room again; the crowd, the breakthrough and the
##     storm in turn; a room entered afresh each round), and the least is the figure: a busy machine only ever adds.
## Samples are left out, never scaled: no figure is less than a timing the gate took. Where the system lets it, the main
## thread also asks for a fair share of a CPU (the suite base's ask_for_cpu), and its clock is the base's now_us.
const ROUNDS := 3
const SLOW_MACHINE := 1.3
var _cal_best := 1 << 30

## The µs a fixed piece of script work takes now on the game's own clock: the machine's speed at this moment. The work
## is script arithmetic and a walk through a 4 MB table in a scrambled order, so a CPU slowed by a busy neighbour on its
## core and one whose memory another process is thrashing both show (the game's own work leans on both).
const CAL_TABLE := 1 << 20
var _cal_table := PackedInt32Array()

func _calibrate() -> int:
	if _cal_table.is_empty():
		# One cycle through every slot, in a scrambled order (a fixed stride coprime to the size, then shuffled by bits).
		_cal_table.resize(CAL_TABLE)
		var order := PackedInt32Array()
		order.resize(CAL_TABLE)
		for j in CAL_TABLE: order[j] = (j * 999331) & (CAL_TABLE - 1)
		for j in CAL_TABLE: _cal_table[order[j]] = order[(j + 1) & (CAL_TABLE - 1)]
	var t0 := now_us()
	var acc := 0
	var at := 0
	for j in 3000:
		acc = (acc * 31 + j) % 1000003
		at = _cal_table[at]
	return now_us() - t0 + (acc & 0) + (at & 0)

## Whether the machine runs at its full speed now: the fixed work takes at most SLOW_MACHINE times the fastest seen.
func _full_speed() -> bool:
	var cal := _calibrate()
	_cal_best = mini(_cal_best, cal)
	return cal <= _cal_best * SLOW_MACHINE

## The figure of [[ms, at full speed, ...], ...]: the least taken at full speed, or the least of all when none was.
func _least(samples: Array) -> float:
	return float(_least_sample(samples)[0])

## The sample `_least` takes its figure from.
func _least_sample(samples: Array) -> Array:
	var fast: Array = []
	var any: Array = []
	for s in samples:
		if any.is_empty() or float(s[0]) < float(any[0]): any = s
		if bool(s[1]) and (fast.is_empty() or float(s[0]) < float(fast[0])): fast = s
	return fast if not fast.is_empty() else any

## Appends a sample to `into[key]` (made on first use).
func _add(into: Dictionary, key, ms: float, fast: bool) -> void:
	if not into.has(key): into[key] = []
	into[key].append([ms, fast])

## The key of the largest figure.
func _slowest(ms: Dictionary) -> String:
	var out := ""
	for k in ms:
		if out == "" or float(ms[k]) > float(ms[out]): out = str(k)
	return out

## Mean ms per frame over `n` ticked and drawn frames, those at the machine's full speed; `each` (frame index) runs at the
## start of each. After each frame the machine's speed is taken, and a frame on which it ran slow is left out (with
## fewer than half kept, every frame counts). The window is always `n` frames, so what it plays is the same.
func _frames(n: int, each: Callable) -> float:
	var all: Array = []
	var kept: Array = []
	for i in n:
		var t0 := now_us()
		if each.is_valid(): each.call(i)
		Game.tick(1.0 / 60.0)
		await get_tree().process_frame
		var ms := (now_us() - t0) / 1000.0
		all.append(ms)
		if _full_speed(): kept.append(ms)
	var use: Array = kept if kept.size() >= n / 2 else all
	var total := 0.0
	for ms in use: total += float(ms)
	return total / use.size()

## The median ms of `n` ticked and drawn frames at the machine's own full speed (a busy runner's spikes left out); `each`
## (frame index) runs at the start of each. A frame on which the machine ran slow (_full_speed) is left out, unless a
## technique picture was being made then (a worker's share of the CPU counts against the page); the window runs on, up
## to three times `n` frames, until at least half of `n` are kept (else every frame counts). `slow_left_out` says how
## many; `window_wall_us` and `window_own_us` are the window's wall and own-clock µs.
var slow_left_out := 0
var making_frames := 0   ## frames of the last window on which a technique picture was being made
var window_wall_us := 0
var window_own_us := 0

func _median_frames(n: int, each: Callable) -> float:
	var frames: Array = []   # [ms, at full speed, a picture being made]
	var kept := 0
	var i := 0
	window_wall_us = 0
	window_own_us = 0
	while i < n or (kept < n / 2 and i < n * 3):
		var w0 := Time.get_ticks_usec()
		var t0 := now_us()
		if each.is_valid(): each.call(i)
		Game.tick(1.0 / 60.0)
		await get_tree().process_frame
		var own := now_us() - t0
		window_own_us += own
		window_wall_us += Time.get_ticks_usec() - w0
		var fast := _full_speed()
		var making := not TechniquePicture._pending.is_empty()
		frames.append([own / 1000.0, fast, making])
		if making or fast: kept += 1
		i += 1
	var ts: Array = []
	for f in frames:
		if bool(f[2]) or bool(f[1]): ts.append(float(f[0]))
	if ts.size() < n / 2: ts = frames.map(func(f): return float(f[0]))
	slow_left_out = frames.size() - ts.size()
	making_frames = frames.filter(func(f): return bool(f[2])).size()
	ts.sort()
	return float(ts[ts.size() / 2])

# ------------------------------------------------------------------ techniques.json at scale
## P13a techniques at scale (docs/technique_plan.md §7): techniques.json on disk, read and expanded at today's size and
## at v1.5's (a fixture of 4,350 rows made from today's under new ids), and the trees' index. Each round parses and
## expands v1.5's rows, builds the index and reads today's file. Every round's rows are kept until the last round is
## timed, then let go outside every timing: rows filled in on memory the round before had just let go took half as long
## again (the boot fills them in on fresh memory), and the v1.5 fixture takes tens of ms to free, which otherwise fell
## into whatever was timed next.
func _techniques_json() -> void:
	var path := "res://data/techniques.json"
	var kb := FileAccess.get_file_as_bytes(path).size() / 1024.0
	# The v1.5 fixture, made once outside every timing.
	var src: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
	var rows: Array = src.entries
	var fixture := {"schema_version": 1, "defaults": src.defaults, "entries": []}
	var i := 0
	while (fixture.entries as Array).size() < 4350:
		var e: Dictionary = (rows[i % rows.size()] as Dictionary).duplicate(true)
		e.id = "%s_v%d" % [e.id, i / rows.size()]
		fixture.entries.append(e)
		i += 1
	var text := JSON.stringify(fixture)
	var n_rows := rows.size()
	fixture = {}
	rows = []
	src = {}
	var s := {}   # figure -> samples
	var margins: Array = []   # [defaults less twice the parse and 20 ms, at full speed, parse, defaults] a round
	var kept: Array = []      # every round's rows, let go after the last
	for r in ROUNDS:
		var fast := _full_speed()
		var t1 := now_us()
		var parsed: Dictionary = JSON.parse_string(text)
		var parse := (now_us() - t1) / 1000.0
		var memo := {}
		for e in parsed.entries: ContentDB.expand(e, parsed.defaults, memo)
		var whole := (now_us() - t1) / 1000.0
		fast = _full_speed() and fast
		# The check's own figure is the round's margin: its defaults against twice its parse, both of the same round.
		margins.append([whole - parse - (2.0 * parse + 20.0), fast, parse, whole - parse])
		_add(s, "parse", parse, fast)
		_add(s, "v15", whole, fast)
		kept.append([parsed, memo])
		fast = _full_speed()
		var t2 := now_us()
		TechniqueTreeRules._built = null
		TechniqueTreeRules.cell("water", "any", 1)
		var index := (now_us() - t2) / 1000.0
		_add(s, "index", index, _full_speed() and fast)
		fast = _full_speed()
		var t0 := now_us()
		var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(path))
		var memo_now := {}
		for e in data.entries: ContentDB.expand(e, data.defaults, memo_now)
		var now := (now_us() - t0) / 1000.0
		_add(s, "now", now, _full_speed() and fast)
		kept.append([data, memo_now])
	kept.clear()
	var ms_now := _least(s.now)
	var ms_v15 := _least(s.v15)
	var ms_index := _least(s.index)
	var best: Array = _least_sample(margins)
	var ms_parse := float(best[2])
	var ms_defaults := float(best[3])
	print("techniques.json: %d rows, %.0f KB (%.0f B a row); read and expanded in %.0f ms; v1.5's 4,350 rows (%.0f KB) in %.0f ms (%.0f of it parsing); the trees' index in %.1f ms"
		% [n_rows, kb, kb * 1024.0 / n_rows, ms_now, text.length() / 1024.0, ms_v15, _least(s.parse), ms_index])
	check(kb < 1100.0, "techniques.json stays under 1.1 MB (%.0f KB)" % kb)
	# Measured against the engine's own JSON parse on the same machine, so a slow or busy runner does not fail it: filling
	# in the defaults costs at most twice the parse (the round with the least margin), and the whole stays under 0.4 s.
	check(float(best[0]) <= 0.0 and ms_v15 < 400.0 and ms_index < 80.0,
		"v1.5's 4,350 rows load in %.0f ms (defaults %.0f ms against a %.0f ms parse) and the trees index in %.1f ms" % [ms_v15, ms_defaults, ms_parse, ms_index])

# ------------------------------------------------------------------ rooms and pages
## Every room: the authority load plus the scene rebuild it triggers. Each round loads every room once; a room's figure
## is the least of its loads.
func _rooms() -> void:
	var c = Game.active()
	var ids: Array = ContentDB.rooms.keys().map(func(k): return str(k))
	ids.sort()
	var s := {}
	var first := {}
	for r in ROUNDS:
		for rid in ids:
			var fast := _full_speed()
			var t0 := now_us()
			Game.world.load_room(c, rid, "")
			GameEvents.flush()
			await get_tree().process_frame
			var t := (now_us() - t0) / 1000.0
			_add(s, rid, t, _full_speed() and fast)
			if r == 0: first[rid] = t
	var ms := {}
	var total := 0.0
	for rid in ids:
		ms[rid] = _least(s[rid])
		total += float(ms[rid])
	var worst_room := _slowest(ms)
	var worst := float(ms[worst_room])
	print("rooms: %d loaded, average %.0f ms, slowest %s %.0f ms (the first round's slowest %s %.0f ms)"
		% [ids.size(), total / ids.size(), worst_room, worst, _slowest(first), float(first[_slowest(first)])])
	check(worst < 300.0, "every room loads in under 0.3 s (slowest %s: %.0f ms)" % [worst_room, worst])

## Every page: open, set up and draw its first frame. Each round opens every page once.
func _pages() -> void:
	var ids: Array = []
	for id in MainScript.PAGES:
		if not str(id) in ["dialogue", "revival", "welcome", "shop", "fishing", "teleport"]: ids.append(str(id))   # need a context to open
	var s := {}
	for r in ROUNDS:
		for id in ids:
			var fast := _full_speed()
			var t0 := now_us()
			main.open_page(id, {})
			await get_tree().process_frame
			_add(s, id, (now_us() - t0) / 1000.0, _full_speed() and fast)
			main.close_all_pages()
			await get_tree().process_frame
	var ms := {}
	for id in ids: ms[id] = _least(s[id])
	var worst_page := _slowest(ms)
	var worst := float(ms[worst_page])
	print("pages: slowest %s %.0f ms" % [worst_page, worst])
	check(worst < 150.0, "every page opens in under 0.15 s (slowest %s: %.0f ms)" % [worst_page, worst])

# ------------------------------------------------------------------ the crowd
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
	# P6e (docs/moments_design.md §7.3): the same crowd under the major breakthrough, then with a Sword Swarm and a Cursive
	# Storm cast every tenth of a second, each striking as many foes as many times as it does. The frame, MomentView and
	# FxLayer included, stays in budget; the FX cap holds; the view's own share is printed. Each round plays the crowd,
	# the breakthrough over it and the storm in turn, the effects let die out between rounds.
	var w = main.world
	var mv: MomentView = main.moments
	var spent := [0, 0]   # usec in MomentView.advance this window, most FX alive
	var view := func(i: int) -> void:
		var t1 := now_us()
		mv.advance(1.0 / 60.0)
		spent[0] += now_us() - t1
	var storm := func(i: int) -> void:
		view.call(i)
		if i % 6 != 0: return
		for tech in ["sword_swarm", "cursive_storm"]:
			var t := ContentDB.entry("techniques", tech)
			# The cast and its hits as Combat announces them, played by the world view (TopdownWorld, CombatFx).
			GameEvents.emit_event("attack_started", {"actor": c.id, "technique": tech, "facing": 1})
			for e in Game.room_rt.living_enemies().slice(0, int(t.max_targets)):
				for h in int(t.hits):
					GameEvents.emit_event("hit_landed", {"attacker": c.id, "target": str(e.uid), "target_kind": "enemy", "amount": 12400, "type": "qi", "crit": h == 1,
						"element": str(t.element), "x": e.plane.x, "y": e.plane.y, "alt": 60.0, "source": "tech:" + tech})
			GameEvents.flush()
		spent[1] = maxi(spent[1], w.fx_layer().fx.size())
	var per := INF
	var per_m := INF
	var per2 := INF
	var advance_ms := INF
	for r in ROUNDS:
		if r > 0: await _fx_die_out(w)
		per = minf(per, await _frames(120, Callable()))
		mv.set_process(false)
		mv.preview("breakthrough_major")
		spent[0] = 0
		per_m = minf(per_m, await _frames(120, view))
		advance_ms = minf(advance_ms, spent[0] / 120000.0)
		mv.clear()
		mv.preview("breakthrough_major")
		per2 = minf(per2, await _frames(120, storm))
		mv.clear()
		mv.set_process(true)
	print("crowd: %d monsters, %.2f ms per frame" % [Game.room_rt.living_enemies().size(), per])
	check(per < 16.6, "a frame with fifteen monsters fits the 60 fps budget (%.2f ms)" % per)
	print("crowd under the breakthrough: %.2f ms per frame (%+.2f ms), MomentView.advance %.3f ms of it" % [per_m, per_m - per, advance_ms])
	print("with a sword swarm too: %.2f ms per frame, %d FX at most" % [per2, spent[1]])
	check(per_m < 16.6 and per2 < 16.6 and spent[1] <= 160, "the crowd under the breakthrough and a sword swarm fits the budget (%.2f, %.2f ms) and the FX cap (%d)" % [per_m, per2, spent[1]])
	await _fx_die_out(w)

## Frames, untimed, until the world's effects have played out (at most four seconds).
func _fx_die_out(w) -> void:
	for i in 240:
		if w.fx_layer().fx.is_empty(): return
		Game.tick(1.0 / 60.0)
		await get_tree().process_frame

# ------------------------------------------------------------------ the Techniques page
## P13a: the emblems composed at run time from the atlas, and the Techniques page opened on a character who knows sixty
## composed arts; P13b: its biggest tree dragged; decision 42: its redraws.
func _techniques() -> void:
	# Emblems: a hundred composed arts at 64 px and at 48 (the HUD ring's), each composed once and then held. Each round
	# composes them afresh.
	var ids: Array = []
	for t in ContentDB.all("techniques"):
		if ids.size() >= 100: break
		if SpriteCache.composable(str(t.id)): ids.append(str(t.id))
	var s := {}
	for r in ROUNDS:
		SpriteCache._emblems.clear()
		SpriteCache._renders.clear()
		for px in [64, 48]:
			var fast := _full_speed()
			var t3 := now_us()
			for id in ids: SpriteCache.emblem(str(id), px)
			_add(s, px, (now_us() - t3) / 1000.0 / maxf(1.0, ids.size()), _full_speed() and fast)
		var fast_held := _full_speed()
		var t4 := now_us()
		for id in ids: SpriteCache.emblem(str(id), 64)
		_add(s, "held", (now_us() - t4) / 1000.0 / maxf(1.0, ids.size()), _full_speed() and fast_held)
	var per := {64: _least(s[64]), 48: _least(s[48])}
	var held := _least(s.held)
	print("emblems: composed in %.2f ms at 64 px, %.2f ms at 48; held, %.4f ms" % [per[64], per[48], held])
	check(ids.size() == 100 and float(per[64]) < 6.0 and float(per[48]) < 4.0 and held < 0.05, "an emblem composes in under 6 ms at 64 px (%.2f) and 4 at 48 (%.2f), then is held" % [per[64], per[48]])
	# The Techniques page on a character with sixty composed arts known (twelve in the list at once), its emblems composed
	# afresh each round.
	var cu = Game.active().cultivator
	var known_was: Array = cu.techniques_known.duplicate()
	for id in ids.slice(0, 60): cu.techniques_known.append(str(id))
	var pages: Array = []
	for r in ROUNDS:
		SpriteCache._emblems.clear()
		SpriteCache._renders.clear()
		var fast := _full_speed()
		var t5 := now_us()
		main.open_page("techniques", {})
		await get_tree().process_frame
		pages.append([(now_us() - t5) / 1000.0, _full_speed() and fast])
		main.close_all_pages()
		await get_tree().process_frame
	cu.techniques_known = known_was
	var ms_page := _least(pages)
	print("techniques page with sixty composed arts: %.0f ms" % ms_page)
	check(ms_page < 150.0, "the Techniques page opens in under 0.15 s with sixty composed arts known (%.0f ms)" % ms_page)
	# P13b: the biggest tree's tab, dragged across its whole width and depth, draws only what is in view: a dragged frame
	# costs about what a still one does (the tree's size does not show) and stays inside a 30 fps frame on the runner.
	var biggest := ""
	var most := 0
	for tree in TechniqueTreeRules.trees():
		var n := TechniqueTreeRules.nodes_of(tree).filter(func(nid): return TechniqueTreeRules.act_of(int(TechniqueTreeRules.node(nid).get("ring", 99))) <= 3).size()
		if n > most:
			biggest = tree
			most = n
	var still := INF
	var ms_pan := INF
	var drawn := 0
	var laid := 0
	for r in ROUNDS:
		main.open_page("techniques", {"tab": biggest})
		await get_tree().process_frame
		var pg = main.top_page()
		still = minf(still, await _frames(60, Callable()))
		ms_pan = minf(ms_pan, await _frames(120, func(k: int): pg.glide(Vector2(k * 64.0, (k % 30) * 40.0), true)))
		drawn = maxi(drawn, pg._regions.filter(func(x): return x.id == "node").size())
		laid = pg._items.size()
		main.close_all_pages()
		await get_tree().process_frame
	print("techniques page, the %s tree (%d nodes): %.2f ms a frame dragged, %.2f still; %d nodes in view" % [biggest, laid, ms_pan, still, drawn])
	check(laid >= 250 and drawn < 40 and ms_pan - still < 5.0 and ms_pan < 33.3,
		"the biggest tree's tab (%s, %d nodes) draws only what is in view (%d): dragged %.2f ms a frame against %.2f still" % [biggest, laid, drawn, ms_pan, still])
	await _techniques_redraws(biggest)

## Decision 42 (the Techniques tree "feels a bit laggy"): the page is drawn again only when something on it changes and
## its chart is tiles kept drawn, which a drag only moves. For a top-down character (the game's), with an art chosen so
## its preview casts: while only the preview moves, neither the page nor a tile is drawn again and a frame costs about
## what the world's alone does; a finger dragging across the biggest tree draws a few tiles a frame and the page again
## only as the drag starts and ends, its frame within 2 ms of the world's alone. Medians of frames at the machine's own
## speed (_median_frames), so a busy runner's spikes and slow stretches do not decide it (the page drawn every frame, as
## before, cost 2.5-4 ms a frame here: about 15 on a phone). Each round times the world alone, then opens the page,
## casts and drags; each figure is the least of its rounds, each count the most.
func _techniques_redraws(tree: String) -> void:
	var ch = Game.active()
	var view_was := str(ch.view)
	ch.view = "topdown"
	var base := INF
	var casting := INF
	var dragging := INF
	var slow := [0, 0, 0]
	var making := [0, 0, 0]
	var page_casting := 0
	var layers_casting := 0
	var page_drag := 0
	var tiles_most := 0
	var tiles_cap := 0
	var top_ok := true
	for r in ROUNDS:
		base = minf(base, await _median_frames(90, Callable()))
		slow[0] += slow_left_out
		making[0] += making_frames
		main.open_page("techniques", {"tab": tree})
		for i in 30: await get_tree().process_frame   # its opening fade, the preview built, the tiles in view drawn
		var pg = main.top_page()
		var art := ""
		for it in pg._items:
			if str(it.kind) == "art" and Rect2(pg.view, pg.CHART.size).intersects(it.box):
				art = str(it.id)
				break
		pg.on_action("node", art)
		for i in 30: await get_tree().process_frame
		var d0: int = pg.draw_count
		var l0: int = pg.layer_draws
		casting = minf(casting, await _median_frames(120, Callable()))
		slow[1] += slow_left_out
		making[1] += making_frames
		page_casting = maxi(page_casting, pg.draw_count - d0)
		layers_casting = maxi(layers_casting, pg.layer_draws - l0)
		top_ok = top_ok and pg.stage.caster is TopdownDoll and not pg.stage.foes.is_empty() and pg.stage.art == art
		# A finger down on the chart, moved every frame (left and right, up and down), and lifted.
		var at := Vector2(560, 360)
		var press := func(down: bool) -> void:
			var ev := InputEventMouseButton.new()
			ev.button_index = MOUSE_BUTTON_LEFT
			ev.pressed = down
			ev.position = at
			pg._gui_input(ev)
		press.call(true)
		var d1: int = pg.draw_count
		var tiles := [pg.tile_draws, 0]   # the count a frame ago, the most drawn in one frame
		var drag := func(i: int) -> void:
			tiles[1] = maxi(int(tiles[1]), int(pg.tile_draws) - int(tiles[0]))
			tiles[0] = pg.tile_draws
			var rel := Vector2(-16.0 if (i / 60) % 2 == 0 else 16.0, -6.0 if (i / 30) % 2 == 0 else 6.0)
			at += rel
			var ev := InputEventMouseMotion.new()
			ev.button_mask = MOUSE_BUTTON_MASK_LEFT
			ev.position = at
			ev.relative = rel
			pg._gui_input(ev)
		dragging = minf(dragging, await _median_frames(120, drag))
		slow[2] += slow_left_out
		making[2] += making_frames
		page_drag = maxi(page_drag, pg.draw_count - d1)
		tiles_most = maxi(tiles_most, int(tiles[1]))
		tiles_cap = pg.TILES_A_FRAME * 3 + 3   # the tiles in view a frame, their three layers, and one ahead
		press.call(false)
		main.close_all_pages()
		await get_tree().process_frame
	ch.view = view_was
	print("techniques page (top-down): %.2f ms a frame with the preview casting, %.2f dragged, %.2f the world alone; the page drawn %d times in 120 casting frames and %d dragged, %d layers casting, at most %d tiles a frame dragged; frames left out with the machine slow: %d, %d, %d; with a picture being made: %d, %d, %d"
		% [casting, dragging, base, page_casting, page_drag, layers_casting, tiles_most, slow[1], slow[2], slow[0], making[1], making[2], making[0]])
	check(top_ok and page_casting == 0 and layers_casting == 0 and casting - base < 1.5,
		"decision 42: with its preview casting the Techniques page is not drawn again (%d, %d layers) and a frame costs about the world's alone (%.2f against %.2f ms)" % [page_casting, layers_casting, casting, base])
	check(page_drag <= 3 and tiles_most <= tiles_cap and dragging - base < 2.0,
		"decision 42: a drag across the %s tree draws the page %d times and at most %d tiles a frame, %.2f ms a frame against the world's %.2f" % [tree, page_drag, tiles_most, dragging, base])

# ------------------------------------------------------------------ the living world
## Decision 43: the room on view with its living world and without it (TopdownLife.enabled), `LIFE_ROUNDS` short rounds
## each way in turn (with, without; then without, with), each after a few frames to settle, `each` driving the body.
## A round's figure is its median frame. Returns [ms a frame with it, without it (each the least of its rounds, since a
## busy runner's load only ever adds to a round), the difference (the median of the rounds' differences, each round's
## two halves run back to back, so a load that comes and goes falls on both alike: the shared test machine swung a
## round's median by 5 ms either way, more than the living world's whole cost), its own work in ms a frame (median)].
## Its own work is the game's count (TopdownLife.spent_us, on the wall clock), put on the game's own clock by the
## window's share of own time in its wall time.
const LIFE_ROUNDS := 6
## The living world's own work may take this share of a 60 fps frame (16.6 ms), measured headless on the test machine.
const LIFE_OWN_SHARE := 0.06
func _life_ab(w, each: Callable) -> Array:
	var on: Array = []
	var off: Array = []
	var own: Array = []
	var diffs: Array = []
	for r in LIFE_ROUNDS:
		for with_life in ([true, false] if r % 2 == 0 else [false, true]):
			TopdownLife.enabled = with_life
			w.build_room()
			w.place_player()
			w.settle_camera()
			for k in 12:
				if each.is_valid(): each.call(k)
				Game.tick(1.0 / 60.0)
				await get_tree().process_frame
			var us := TopdownLife.spent_us
			var f0 := Engine.get_process_frames()
			var ms := await _median_frames(60, each)
			if with_life:
				on.append(ms)
				var share := float(window_own_us) / maxf(1.0, float(window_wall_us))
				own.append((TopdownLife.spent_us - us) * share / 1000.0 / maxf(1.0, float(Engine.get_process_frames() - f0)))
			else: off.append(ms)
		diffs.append(float(on[-1]) - float(off[-1]))
	TopdownLife.enabled = true
	w.build_room()
	w.place_player()
	w.settle_camera()
	await get_tree().process_frame   # the room drawn as built before anything else moves the world on
	on.sort()
	off.sort()
	own.sort()
	diffs.sort()
	return [float(on[0]), float(off[0]), (float(diffs[LIFE_ROUNDS / 2 - 1]) + float(diffs[LIFE_ROUNDS / 2])) / 2.0, float(own[own.size() / 2])]

## The living world's cost in a room: its difference to the frame within a ms and a seventh of the frame without it, and
## its own work within LIFE_OWN_SHARE of a 60 fps frame.
func _life_check(what: String, ab: Array) -> void:
	print("topdown world: %s with the living world %.2f ms a frame, without %.2f ms (the least of %d interleaved rounds); a round's difference %.2f ms (median); its own work %.3f ms a frame"
		% [what, ab[0], ab[1], LIFE_ROUNDS, ab[2], ab[3]])
	check(float(ab[2]) < 1.0 + float(ab[1]) * 0.15 and float(ab[3]) < 16.6 * LIFE_OWN_SHARE,
		"the living world costs %s at most a ms and a seventh of its frame (%.2f ms against %.2f without it) and its own work stays under %d%% of a 60 fps frame (%.3f ms)"
		% [what, ab[2], ab[1], roundi(LIFE_OWN_SHARE * 100.0), ab[3]])

# ------------------------------------------------------------------ the top-down world
## Redesign Phase 1: the top-down prototype room under the HUD (its rules are rules_tests' topdown_suite). It mounts
## inside the room-load gate and holds the 60 fps budget while the body walks a circle and jumps. Each round mounts the
## room afresh, walks, then fights (below).
func _topdown() -> void:
	var mounts: Array = []
	var per := INF
	var per_fight := INF
	var nodes := 0
	var foes := 1 << 30
	var peak := {"fx": 0}
	for r in ROUNDS:
		if r > 0:
			main.return_to_selection()
			await get_tree().process_frame
		var fast := _full_speed()
		var t0 := now_us()
		main.enter_topdown_proto(false)
		await get_tree().process_frame
		mounts.append([(now_us() - t0) / 1000.0, _full_speed() and fast])
		var p = main.world.player
		var drive := func(i: int) -> void:
			p.movement = Vector2.from_angle(i * 0.05)
			if i % 40 == 0: p.jump()
		per = minf(per, await _frames(120, drive))
		nodes = main.world.sorted.get_child_count()
		# Phase 2: fifteen foes fighting the player, with its blows and techniques (the forms from art/fx/) going off.
		var w = main.world
		var kinds := ["mudshell_crab", "reedtail_rat", "wild_boarlet"]
		p.motor.place(Vector2(22.5, 18.5) * 32.0)
		for i in 15:
			var at: Vector2 = p.motor.pos + Vector2.from_angle(TAU * i / 15.0) * (70.0 + 12.0 * (i % 3))
			var e: EnemyState = Game.enemies.spawn_at(kinds[i % 3], at, 5)
			if e == null: continue
			e.altitude = w.room.height_at(at)
			e.threat[Game.active_id] = 1.0
		# Decision 38: the effects counted are the overlay's (numbers, rings) and the ground-plane sheets TopdownFx plays in
		# the world (smears, forms, impacts, marks, dust), every blow and technique drawn with its hit-stop and camera kick.
		var fight := func(i: int) -> void:
			peak.fx = maxi(int(peak.fx), w.effects.fx.size() + w.tfx.nodes.size())
			p.movement = Vector2.from_angle(i * 0.07) * 0.3
			Game.active().pools.hp = Game.active().pools.max_hp
			Game.combat.wounded.erase(Game.active_id)
			if i % 20 == 0: p.aim_attack(Vector2.from_angle(i * 0.4))
			if i % 45 == 10:
				Game.active().pools.cooldowns.clear()
				p.aim_technique((i / 45) % 4, Vector2.from_angle(i * 0.3), 0.6)
		per_fight = minf(per_fight, await _frames(180, fight))
		foes = mini(foes, Game.room_rt.living_enemies().size())
	var ms := _least(mounts)
	print("topdown prototype: mounted in %.0f ms (the first round %.0f), %.2f ms per frame, %d sorted nodes" % [ms, float(mounts[0][0]), per, nodes])
	check(main.world is TopdownWorld and ms < 300.0 and per < 16.6, "the top-down prototype room mounts in under 0.3 s (%.0f ms) and runs at 60 fps (%.2f ms)" % [ms, per])
	print("topdown prototype: %d foes fighting, %.2f ms per frame, %d effects at once at most" % [foes, per_fight, int(peak.fx)])
	check(foes >= 15 and int(peak.fx) > 0 and per_fight < 16.6, "the top-down room holds 60 fps with %d foes and the fight's effects (%.2f ms)" % [foes, per_fight])
	main.return_to_selection()
	await get_tree().process_frame
	await _lotus_ferry()
	await _marsh_edge()

## Phase 4: a top-down character's own game (the title's hidden entry, on its own saves): out of the Fisher's Hut into
## Lotus Ferry, the view rebuilt on the grid with the village's people, things and ways, then a walk through it. Each
## round makes the character afresh and takes it out of the hut.
func _lotus_ferry() -> void:
	var saves: String = main.get_script().TOPDOWN_SAVES
	var loads: Array = []
	var per_walk := INF
	var built := 0
	var ok := true
	var walk := Callable()
	for r in ROUNDS:
		if r > 0:
			main.return_to_selection()
			await get_tree().process_frame
		DirAccess.make_dir_recursive_absolute(saves)
		for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
		main.enter_topdown_tutorial(true)
		await get_tree().process_frame
		var fast := _full_speed()
		var t1 := now_us()
		Game.submit({"type": "use_portal", "portal": "exit", "crossing": true})
		await get_tree().process_frame
		loads.append([(now_us() - t1) / 1000.0, _full_speed() and fast])
		var walker = main.world.player
		walk = func(i: int) -> void: walker.movement = Vector2.from_angle(i * 0.04)
		per_walk = minf(per_walk, await _frames(120, walk))
		built = main.world.npc_views.size() + main.world.object_views.size() + main.world.portal_views.size()
		ok = ok and main.world is TopdownWorld and main.world.live and Game.room_rt.room_id == "lf_village"
	var ms_room := _least(loads)
	print("topdown world: Lotus Ferry entered in %.0f ms (the first round %.0f; %d people, things and ways), %.2f ms per frame" % [ms_room, float(loads[0][0]), built, per_walk])
	check(ok and ms_room < 300.0 and per_walk < 16.6,
		"a top-down character's Lotus Ferry loads in under 0.3 s (%.0f ms, %d built) and runs at 60 fps (%.2f ms)" % [ms_room, built, per_walk])
	# Decision 43: the living world's cost in Lotus Ferry (the busiest room: critters, 7 people at work and 2 extras,
	# smoke, the grass's pushes, the vistas), against the same room built without it, interleaved so the machine's
	# load falls on both alike; and its own work a frame (its step, its drawing, the loops).
	_life_check("Lotus Ferry", await _life_ab(main.world, walk))

## Phase 4's second part: chapter 2's region, its Marsh Edge (the stretch's widest room, with the most foes) entered
## through the World authority, then its own kinds of foe, fifteen in all, turned on the player there. Each round enters
## the room afresh (its own foes back) and tops the foes up to fifteen.
func _marsh_edge() -> void:
	var saves: String = main.get_script().TOPDOWN_SAVES
	var loads: Array = []
	var per_marsh := INF
	var marsh_foes := 1 << 30
	var ok := true
	var mw = null
	var hold := Callable()
	for r in ROUNDS:
		var fast := _full_speed()
		var t2 := now_us()
		Game.world.load_room(Game.active(), "rm_marsh_edge", "west")
		GameEvents.flush()
		await get_tree().process_frame
		loads.append([(now_us() - t2) / 1000.0, _full_speed() and fast])
		mw = main.world
		var marsh_kinds := ["marsh_leech", "reed_frog", "hollowed_boarlet", "reed_otter"]
		for i in maxi(0, 15 - Game.room_rt.living_enemies().size()):
			var at: Vector2 = mw.room.nearest_standable(mw.player.motor.pos + Vector2.from_angle(TAU * i / 15.0) * (80.0 + 12.0 * (i % 3)))
			var e: EnemyState = Game.enemies.spawn_at(marsh_kinds[i % 4], at, 5)
			if e == null: continue
			e.altitude = mw.room.height_at(at)
			e.threat[Game.active_id] = 1.0
		var room_world = mw
		hold = func(i: int) -> void:
			room_world.player.movement = Vector2.from_angle(i * 0.05) * 0.4
			Game.active().pools.hp = Game.active().pools.max_hp
			Game.combat.wounded.erase(Game.active_id)
			if i % 20 == 0: room_world.player.aim_attack(Vector2.from_angle(i * 0.4))
		per_marsh = minf(per_marsh, await _frames(150, hold))
		marsh_foes = mini(marsh_foes, Game.room_rt.living_enemies().size())
		ok = ok and mw is TopdownWorld and Game.room_rt.room_id == "rm_marsh_edge"
	var ms_marsh := _least(loads)
	print("topdown world: the Marsh Edge entered in %.0f ms (the first round %.0f), %d foes fighting at %.2f ms per frame" % [ms_marsh, float(loads[0][0]), marsh_foes, per_marsh])
	check(ok and ms_marsh < 300.0 and marsh_foes >= 15 and per_marsh < 16.6,
		"chapter 2's Marsh Edge loads in under 0.3 s (%.0f ms) and holds 60 fps with %d of its foes fighting (%.2f ms)" % [ms_marsh, marsh_foes, per_marsh])
	# Decision 43: the same fight with its living world and without it (the grass parting round the foes, frogs, fish,
	# dragonflies, the watchers at work, the marsh's vista), interleaved.
	_life_check("the Marsh Edge's fight", await _life_ab(mw, hold))
	main.return_to_selection()
	await get_tree().process_frame
	for f in DirAccess.get_files_at(saves): DirAccess.remove_absolute(saves + f)
