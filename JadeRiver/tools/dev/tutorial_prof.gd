extends Node
## Decision 45 (docs/redesign/tutorials.md "Bugs fixed", "The lag"): what the tutorial coach costs a frame, hidden and
## showing, on a character some hours in (the HUD's usual systems open, techniques slotted, gear in the bag), the coach
## swapped for one that times its own _process and drawing (the card's too) and the parts of its frame:
##   A hidden on the play screen, B hidden over the Bag, C a guide on the Menu button, D a HUD tour (the guard's),
##   E a page tour (the Bag's); and the authority's poll (every guide, and the passing states only). Not a test: the
## figures are this machine's (a phone's CPU is several times slower); the tutorials suite holds the hidden coach to
## its bound.
##   godot --headless --path . res://tools/dev/tutorial_prof.tscn

class ProfCoach extends TutorialCoach:
	var proc_us: Array = []
	var draw_us: Array = []
	var _d := 0
	func _process(delta: float) -> void:
		var t0 := Time.get_ticks_usec()
		super._process(delta)
		proc_us.append(Time.get_ticks_usec() - t0)
		draw_us.append(_d)
		_d = 0
	func _draw() -> void:
		var t0 := Time.get_ticks_usec()
		super._draw()
		_d += Time.get_ticks_usec() - t0
	func _draw_card(ci) -> void:
		var t0 := Time.get_ticks_usec()
		super._draw_card(ci)
		_d += Time.get_ticks_usec() - t0
	var parts := {}
	func _acc(k: String, us: int) -> void:
		parts[k] = int(parts.get(k, 0)) + us
	func blocked(ch) -> String:
		var t0 := Time.get_ticks_usec()
		var r := super.blocked(ch)
		_acc("blocked", Time.get_ticks_usec() - t0)
		return r
	func _page_tour(ch, rec: Dictionary, top: Page) -> String:
		var t0 := Time.get_ticks_usec()
		var r := super._page_tour(ch, rec, top)
		_acc("page_tour", Time.get_ticks_usec() - t0)
		return r
	func _resolve(delta: float) -> void:
		var t0 := Time.get_ticks_usec()
		super._resolve(delta)
		_acc("resolve", Time.get_ticks_usec() - t0)
	func _find(names: String, hud_side: bool) -> Rect2:
		var t0 := Time.get_ticks_usec()
		var r := super._find(names, hud_side)
		_acc("find", Time.get_ticks_usec() - t0)
		return r
	func _layout() -> void:
		var t0 := Time.get_ticks_usec()
		super._layout()
		_acc("layout", Time.get_ticks_usec() - t0)
	func _hud_lesson(ch, e: Dictionary, top: Page, pid: String, tab: String, delta: float) -> bool:
		var t0 := Time.get_ticks_usec()
		var r := super._hud_lesson(ch, e, top, pid, tab, delta)
		_acc("hud_lesson(incl resolve)", Time.get_ticks_usec() - t0)
		return r

var main: Node
var pc: ProfCoach

func _ready() -> void:
	call_deferred("_main")

func frames(n: int) -> void:
	for i in n: await get_tree().process_frame

func c():
	return Game.active()

func _main() -> void:
	var folder := "user://test_runs/tutorial_prof_%d/" % OS.get_process_id()
	DirAccess.make_dir_recursive_absolute(folder)
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(folder)
	Clock.simulate(1789997760.0)
	Game.boot()
	Game.autosave_enabled = false
	for i in 3600:
		if main.pages_warm(): break
		await get_tree().process_frame
	# The coach swapped for one that times itself.
	var old: TutorialCoach = main.coach
	pc = ProfCoach.new()
	pc.main = main
	old.get_parent().add_child(pc)
	old.queue_free()
	main.coach = pc
	await fresh([])
	main.hud.coach = pc
	_rich()
	await frames(30)
	var res := {}
	res["A idle, play screen"] = await measure()
	main.open_page("inventory", {})
	await frames(30)
	res["B idle, Bag open"] = await measure()
	main.close_all_pages()
	await frames(10)
	# A guide on the HUD: the first foundation points.
	_forget(["foundation"])
	c().cultivator.unspent_meridian_points = 3
	Game.tutorials.evaluate(c())
	await frames(10)
	res["C guide on the Menu button (%s)" % pc.state().entry] = await measure()
	var hb: Array = []
	var hh: Array = []
	var fb: Array = []
	for i in 50:
		var t0 := Time.get_ticks_usec()
		var b = main.hud.frame_badges()
		var t1 := Time.get_ticks_usec()
		main.hud.hit_targets(b)
		var t2 := Time.get_ticks_usec()
		main.hud.point_badges(c())
		var t3 := Time.get_ticks_usec()
		fb.append(t1 - t0)
		hb.append(t2 - t1)
		hh.append(t3 - t2)
	hb.sort(); hh.sort(); fb.sort()
	print("PROF hud: frame_badges %d us, hit_targets(badges) %d us, point_badges %d us" % [fb[25], hb[25], hh[25]])
	Game.submit({"type": "tutorial_done", "id": "foundation", "stage": "guide", "skipped": true})
	# A HUD tour: the guard.
	_forget(["guard"])
	Game.tutorials.evaluate(c())
	await frames(10)
	res["D HUD tour (%s %s)" % [pc.state().mode, pc.state().entry]] = await measure()
	pc.press("skip")
	await frames(5)
	# A page tour: the Bag's.
	_forget(["bag"])
	main.open_page("inventory", {})
	await frames(10)
	res["E page tour (%s %s)" % [pc.state().mode, pc.state().entry]] = await measure()
	pc.press("skip")
	main.close_all_pages()
	await frames(5)
	# The authority's poll, an early character with most lessons still ahead.
	var st: Dictionary = c().tutorials
	var keep := st.duplicate(true)
	st.guided.clear()
	st.seen.clear()
	st.queue = []
	var ev: Array = []
	for i in 40:
		var t0 := Time.get_ticks_usec()
		Game.tutorials.evaluate(c())
		ev.append(Time.get_ticks_usec() - t0)
		st.guided.clear()
		st.seen.clear()
		st.queue = []
	c().tutorials = keep
	ev.sort()
	print("PROF evaluate (all): median %d us, p90 %d us" % [ev[20], ev[36]])
	if Game.tutorials.get("PASSING") != null:
		var ev2: Array = []
		for i in 40:
			var t0 := Time.get_ticks_usec()
			Game.tutorials.evaluate(c(), Game.tutorials.PASSING)
			ev2.append(Time.get_ticks_usec() - t0)
			st.guided.clear()
			st.seen.clear()
			st.queue = []
		ev2.sort()
		print("PROF evaluate (the 0.5 s poll, passing kinds): median %d us, p90 %d us" % [ev2[20], ev2[36]])
	var tf: Array = []
	for i in 60:
		var t0 := Time.get_ticks_usec()
		TutorialRules.tour_for("inventory", "")
		tf.append(Time.get_ticks_usec() - t0)
	tf.sort()
	print("PROF a page's ? (TutorialRules.tour_for, each page drawing): median %d us" % tf[30])
	for k in res: print("PROF %s: %s" % [k, res[k]])
	main.queue_free()
	await frames(3)
	get_tree().quit()

## N frames of the game loop: the coach's _process and _draw, median and mean us a frame.
func measure(n := 400) -> String:
	pc.proc_us.clear()
	pc.draw_us.clear()
	pc.parts.clear()
	await frames(n)
	var parts := ""
	for k in pc.parts: parts += " %s=%d" % [k, int(pc.parts[k]) / maxi(1, pc.proc_us.size())]
	var p: Array = pc.proc_us.duplicate()
	var d: Array = pc.draw_us.duplicate()
	var tot: Array = []
	for i in p.size(): tot.append(int(p[i]) + int(d[i]))
	p.sort()
	d.sort()
	tot.sort()
	var mean := 0.0
	for v in tot: mean += float(v)
	mean /= maxf(1.0, tot.size())
	return parts + " | process median %d us, draw median %d us, total median %d us, mean %.0f us, p90 %d us (%d frames)" % [p[p.size() / 2], d[d.size() / 2], tot[tot.size() / 2], mean, tot[int(tot.size() * 0.9)], tot.size()]

func fresh(but: Array) -> void:
	main.close_all_pages()
	if main.screen == "world": main.unmount_world()
	Game.boot()
	Game.autosave_enabled = false
	for s in Game.characters.keys(): Game.submit({"type": "delete_character", "slot": int(str(s).trim_prefix("c"))})
	Game.submit({"type": "create_character", "slot": 1, "name": "Tutee", "appearance": {"hair": "topknot"}, "view": "topdown"})
	var ch = Game.character("c1")
	for row in ContentDB.all("scenes"): ch.quests.scenes[str(row.id)] = {"done": true}
	for e in TutorialRules.entries():
		if str(e.id) in but: continue
		ch.tutorials.guided[str(e.id)] = 1
		ch.tutorials.seen[str(e.id)] = 1
	main.enter_world(1)
	await frames(6)
	main.hud.fight_override = false
	main.hud.fight_left = 0.0
	main.hud.fight = false
	main.close_all_pages()
	await frames(4)

func _forget(ids: Array) -> void:
	for id in ids:
		c().tutorials.guided.erase(id)
		c().tutorials.seen.erase(id)
		c().tutorials.at.erase(id)

## A character some hours in: the HUD's usual systems open, techniques learned and slotted, gear in the bag.
func _rich() -> void:
	var ch = c()
	for u in ["move", "bag", "navigation", "jump", "shop", "quick_use", "attack", "loot", "menu", "cultivate", "cultivation", "codex",
			"equipment", "weapons", "technique_slots_2", "foundation", "guard", "qi_pool", "mail", "world_menu", "character_menu"]:
		Unlocks.force_unlock(ch.id, u)
	ch.cultivator.realm_key = "bone_forging_3"
	Game.progression.apply_learn_technique(ch.id, "flowing_palm")
	ch.cultivator.technique_slots[0] = "flowing_palm"
	StatRules.rebuild(ch, Game.account)
	for it in [["iron_jian", 2], ["healing_pill", 3], ["herbal_tea", 3]]: Game.inventory.apply_add(ch.id, str(it[0]), int(it[1]), "test")
	GameEvents.flush()
	for id in ch.tutorials.queue.duplicate(): Game.submit({"type": "tutorial_done", "id": str(id), "stage": "guide", "skipped": true})
