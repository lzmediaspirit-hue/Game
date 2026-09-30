extends RefCounted
## Decision 43, the living world (docs/redesign/art_bible.md §14.13): the rules of what lives in a room on the grid.
## rules_tests runs it with topdown_suite and the foliage suite.
##   - Work loops: on every room with people at work, each loop keeps to its person's leash (standing on their floor),
##     moves between its spots, stops and turns to the player at their side, and a person whose marker calls goes back to
##     their own spot and stays there, so the talk and the marker are where the quest's tracker points.
##   - Critters: they come into the view, flee a body that comes near and are dropped once off screen; the pools stay
##     bounded (critters, the sorted nodes they borrow, puffs, bits, motes) however hard they are pushed.
##   - The grass parts round the bodies (the foliage shader's pushes; a walk-through plant leans), the washing and the
##     banners turn on the wind's clock.
##   - Interiors hang their walls and let the sun in; the vista opens the camera past a room's edge.

var t   # the running suite (check)
var measured := {}

func run_all(suite) -> void:
	t = suite
	_work_rules()
	_stop_for_talk()
	_drawn_work()

## Decision 44: the work is drawn. Every step of a loop that wears tools plays an action one of its tools is drawn in
## (or a place's crouch, idle or the walk they carry them in), the stand-ins are gone (no combat pose, kneel or cast for
## work, no weapon for the woodcutter), and a blow lands on its action's contact frame on every cycle: run for a minute
## at 60 frames a second, every chop and hammer hit falls on the drawn contact frame. A smith stopped by the player keeps
## the hammer in hand (the work pose's rest frame).
func _drawn_work() -> void:
	var loops: Dictionary = TopdownLife.data().get("loops", {})
	var tools: Dictionary = TopdownFigure.manifest().get("items", {}).get("tool", {})
	var bad: Array = []
	for k in loops:
		var lp: Dictionary = loops[k]
		var worn: Array = lp.get("tools", [])
		var steps: Array = (lp.get("at", []) as Array).duplicate()
		for v in (lp.get("steps", {}) as Dictionary).values(): steps.append_array(v)
		steps.append([str(lp.get("walk", "walk")), 0.0])
		for st in steps:
			var a := str(st[0])
			if TopdownFigure.is_work(a) and not worn.any(func(tl): return (tools.get(str(tl), {}).get("actions", []) as Array).has(a)):
				bad.append("%s: %s holds no tool it wears" % [k, a])
			if not worn.is_empty() and a in ["kneel", "cast", "guard", "two_hand_swing_3", "swing_3", "brush_write"]:
				bad.append("%s: stand-in %s" % [k, a])
	if str(loops.get("chop", {}).get("weapon", "")) != "": bad.append("chop wears a weapon")
	t.check(bad.is_empty() and tools.size() >= 10, "life: every work step plays a drawn work action holding a tool its loop wears, no stand-ins (%d tools; %s)" % [tools.size(), str(bad.slice(0, 4))])
	# The blows on their contact frames, every cycle.
	var hits := {"chop": 0, "hammer": 0}
	var off: Array = []
	var cases := [["lf_village", "x_woodcutter", "chop"], ["sf_artisan_row", "npc_smith_bao", "hammer"]]
	for cs in cases:
		var life := TopdownLife.room_life(str(cs[0]))
		var entry: Dictionary = {}
		for e in life.get("extras", []):
			if str(e.id) == str(cs[1]): entry = e
		if entry.is_empty(): entry = life.get("work", {}).get(str(cs[1]), {})
		if entry.is_empty():
			off.append("no %s" % cs[1])
			continue
		var w := TopdownWork.new(entry, loops, TopdownRoom.cell_point(entry.spots[0]), 0.0, str(cs[1]))
		for i in 3600:
			w.advance(1.0 / 60.0, Vector2.INF, false, false)
			if not w.hit: continue
			hits[cs[2]] += 1
			var want := TopdownFigure.hit_frame(w.action)
			if w.frame() != want or w.step_cue != str(cs[2]): off.append("%s: hit on frame %d of %s (contact %d, cue %s)" % [cs[1], w.frame(), w.action, want, w.step_cue])
	t.check(off.is_empty() and int(hits.chop) >= 25 and int(hits.hammer) >= 15,
		"life: the woodcutter's chops (%d) and the smith's hammer blows (%d) in a minute each land on their action's drawn contact frame (%s)" % [hits.chop, hits.hammer, str(off.slice(0, 3))])
	# Stopped by the player at the anvil: the hammer stays in hand, the work pose's rest frame.
	var smith: Dictionary = TopdownLife.room_life("sf_artisan_row").get("work", {}).get("npc_smith_bao", {})
	var held := false
	if not smith.is_empty():
		var w2 := TopdownWork.new(smith, loops, TopdownRoom.cell_point(smith.spots[0]), 0.0, "npc_smith_bao")
		for i in 40:
			w2.advance(0.05, Vector2.INF, false, false)
		var was := w2.action
		w2.advance(0.05, w2.pos + Vector2(30, 0), true, false)
		held = was == "work_hammer" and w2.action == "work_hammer" and w2.frame() == TopdownFigure.rest_frame("work_hammer")
	t.check(held, "life: a smith stopped by the player at the anvil keeps the hammer in hand (the work pose's rest frame)")

## Every loop of every room, run for two minutes with no one about: never past its leash, always on its floor, moving
## between its spots; its spots within the World authority's talk reach of the person's own spot less a body.
func _work_rules() -> void:
	var loops: Dictionary = TopdownLife.data().get("loops", {})
	var leash := float(TopdownLife.data().get("leash", 2.5)) * TopdownRoom.TILE
	var bad: Array = []
	var moved := 0
	var total := 0
	var acts := {}
	for rid in TopdownLife.data().get("rooms", {}):
		var life: Dictionary = TopdownLife.room_life(rid)
		if not life.has("work") and not life.has("extras"): continue
		var room := TopdownRoom.load_room(rid)
		var entries: Array = []
		for oid in life.get("work", {}):
			var home := TopdownRoom.cell_point(room.def.place[oid])
			entries.append([str(oid), life.work[oid], home])
		for e in life.get("extras", []): entries.append([str(e.id), e, TopdownRoom.cell_point(e.spots[0])])
		for en in entries:
			total += 1
			var home: Vector2 = en[2]
			var z: float = room.floor_at(home)
			var w := TopdownWork.new(en[1], loops, home, z, str(en[0]))
			var far := 0.0
			var off := 0
			var start := w.pos
			var went := 0.0
			for i in 1200:
				w.advance(0.1, Vector2.INF, false, false)
				far = maxf(far, w.pos.distance_to(home))
				went = maxf(went, w.pos.distance_to(start))
				acts[w.action] = true
				if absf(room.height_at(w.pos) - z) > 8.0 or not room.standable(TopdownRoom.cell_of(w.pos)): off += 1
			if far > leash + 1.0: bad.append("%s %s: %.0f from its spot" % [rid, en[0], far])
			if off > 0: bad.append("%s %s: %d frames off its floor" % [rid, en[0], off])
			for s in w.spots:
				if (s[0] as Vector2).distance_to(home) > 110.0 - 28.0: bad.append("%s %s: a spot past the talk's reach" % [rid, en[0]])
			if w.moves() and went > 16.0: moved += 1
			for s in w.spots:
				for st in s[2]:
					if TopdownFigure.resolve(str(st[0])) != str(st[0]): bad.append("%s %s: no pose %s" % [rid, en[0], st[0]])
	measured.workers = total
	measured.moving = moved
	t.check(bad.is_empty() and total >= 40 and moved >= 25,
		"life: %d people at work keep to their leash on their own floor for two minutes, %d walking between spots, every pose drawn (%s)" % [total, moved, str(bad.slice(0, 4))])
	t.check(acts.size() >= 14, "life: the loops play %d poses of the figures' own (sweep, forms, kneel, stir, chop, cast...)" % acts.size())

## At the player's side a worker stops and turns to the player; once the player leaves they take up the work again. A
## person whose marker calls walks back to their own spot and stays there.
func _stop_for_talk() -> void:
	var loops: Dictionary = TopdownLife.data().get("loops", {})
	var room := TopdownRoom.load_room("lf_village")
	var life := TopdownLife.room_life("lf_village")
	var oid := "npc_aunt_ping_lane"
	var home := TopdownRoom.cell_point(room.def.place[oid])
	var w := TopdownWork.new(life.work[oid], loops, home, 0.0, oid)
	for i in 80: w.advance(0.1, Vector2.INF, false, false)
	var at := w.pos
	var player := at + Vector2(40, 0)
	for i in 30: w.advance(0.1, player, true, false)
	var still := w.pos.distance_to(at) < 0.01 and w.action == "idle" and w.row == "e"
	# Near but not offered: still stops for the player close by.
	var w2 := TopdownWork.new(life.work[oid], loops, home, 0.0, oid)
	for i in 40: w2.advance(0.1, Vector2.INF, false, false)
	var at2 := w2.pos
	for i in 30: w2.advance(0.1, at2 + Vector2(0, 50), false, false)
	var noticed := w2.pos.distance_to(at2) < 0.01 and w2.row == "s"
	# The player gone: the work goes on (it moves again within the loop's own time).
	var went := 0.0
	for i in 200:
		w.advance(0.1, Vector2.INF, false, false)
		went = maxf(went, w.pos.distance_to(at))
	t.check(still and noticed and went > 16.0,
		"life: a worker stops and turns to the player at their side (%s) or close by (%s), then works on (%.0f moved)" % [still, noticed, went])
	# The marker calls: back to the own spot within seconds, and there for good.
	var q := TopdownWork.new(life.work[oid], loops, home, 0.0, oid)
	for i in 55: q.advance(0.1, Vector2.INF, false, false)
	var back := -1
	var strayed := 0.0
	for i in 400:
		q.advance(0.1, Vector2.INF, false, true)
		var d := q.pos.distance_to(q.spots[0][0])
		if back < 0 and d <= TopdownWork.ARRIVE: back = i
		if back >= 0: strayed = maxf(strayed, d)
	t.check(back >= 0 and back < 100 and strayed <= TopdownWork.ARRIVE and (q.spots[0][0] as Vector2).distance_to(home) < 40.0,
		"life: someone whose marker calls walks back to their own spot (%.1f s) and stays there (%.1f units at most)" % [back * 0.1, strayed])

## The view: critters come, flee and go, the pools stay bounded, the grass parts, the washing and banners follow the
## wind; an interior's walls and sun; the vista past a sect's edge; the people at work carry their labels with them.
func run_view(suite, tree: SceneTree) -> void:
	t = suite
	var was: String = Game.active_id
	var hour := TopdownLight.debug_hour
	TopdownLight.debug_hour = 0.375
	Game.active_id = ""
	var w = TopdownWorld.new()
	w.room_id = "lf_village"
	tree.root.add_child(w)
	await tree.process_frame
	var life: TopdownLife = w.life
	var p = w.player
	p.motor.place(Vector2(33.5, 27.0) * TopdownRoom.TILE)
	await _frames(tree, 90)
	var kinds := {}
	for c in life.critters: kinds[str(c.kind)] = int(kinds.get(str(c.kind), 0)) + 1
	measured.village = kinds
	t.check(life.critters.size() >= 5 and kinds.has("hen") and (kinds.has("sparrow") or kinds.has("butterfly")) and life.pool.size() == TopdownLife.GROUND_POOL,
		"life view: Lotus Ferry's view fills with critters at midday (%s), the ones on the ground in %d pooled sorted nodes" % [str(kinds), life.pool.size()])
	# A sparrow on the ground flees the player walking up to it, and is dropped once it has flown off the view.
	var bird := _put(life, "sparrow", p.motor.pos + Vector2(120, 0))
	bird.state = "ground"
	var fled0: int = life.fled
	var drop0: int = life.dropped
	p.motor.place(p.motor.pos + Vector2(100, 0))
	var flew := false
	for i in 400:
		await _frames(tree, 1)
		if str(bird.state) == "flee": flew = true
		if not life.critters.has(bird): break
	t.check(flew and not life.critters.has(bird) and life.fled > fled0 and life.dropped > drop0,
		"life view: a sparrow flies off from the player coming near (%s) and is dropped once off screen (%s)" % [flew, not life.critters.has(bird)])
	# A hen scatters from the player and settles again near home; a fish darts off in a ring.
	var hen: TopdownLife.Critter = null
	for c in life.critters:
		if str(c.kind) == "hen": hen = c
	var scattered := false
	var home_ok := true
	if hen != null:
		p.motor.place(hen.g + Vector2(20, 0))
		for i in 90:
			await _frames(tree, 1)
			if str(hen.state) == "flee": scattered = true
			if (hen.g as Vector2).distance_to(hen.home) > 200.0: home_ok = false
	t.check(scattered and home_ok, "life view: a hen scatters from the player (%s) and keeps near home (%s)" % [scattered, home_ok])
	# The pools hold however hard they are pushed.
	for i in 200:
		life._add_wild(["sparrow", "butterfly", "fish", "dragonfly"][i % 4], life._view())
		life._puff("smoke", Vector2(500, 300))
		life._bits(Vector2(500, 300), Vector2.UP, [Color.WHITE], 4)
	await tree.process_frame
	t.check(life.critters.size() <= TopdownLife.MAX_CRITTERS and life.puffs.size() <= TopdownLife.MAX_PUFFS and life.bits.size() <= TopdownLife.MAX_BITS
		and life.pool.size() == TopdownLife.GROUND_POOL and life.pool.filter(func(n): return n.critter != null).size() <= TopdownLife.GROUND_POOL,
		"life view: pushed hard, the pools hold (%d critters of %d, %d puffs of %d, %d bits of %d, %d sorted nodes)" % [life.critters.size(), TopdownLife.MAX_CRITTERS,
			life.puffs.size(), TopdownLife.MAX_PUFFS, life.bits.size(), TopdownLife.MAX_BITS, life.pool.size()])
	# Off to the room's far end: the critters left behind off screen are dropped, none lingers off screen.
	var before: Array = life.critters.duplicate()
	p.motor.place(Vector2(66.5, 20.5) * TopdownRoom.TILE)
	w._settle_camera()
	await _frames(tree, 30)
	var view: Rect2 = life._view().grow(TopdownLife.DROP_PX + 4.0)
	var off := func(c): return c.home_id < 0 and str(c.state) != "land" and not view.has_point((c.s as Vector2) - Vector2(0, float(c.z)))
	var left := before.filter(func(c): return life.critters.has(c) and off.call(c)).size()
	var gone := before.filter(func(c): return not life.critters.has(c)).size()
	var outside := life.critters.filter(off)
	t.check(left == 0 and gone > 0 and outside.is_empty(), "life view: past the room's far end the old view's critters are dropped (%d gone), none lingers off screen" % gone)
	# The grass parts: the foliage shader holds the player's feet among its pushes; a walk-through plant leans aside.
	var mat := TopdownFoliage.sway_material()
	var arr: PackedVector4Array = mat.get_shader_parameter("bodies")
	var n := int(mat.get_shader_parameter("body_count"))
	var feet: Vector2 = p.screen
	var pushed := n >= 1 and arr.size() == TopdownLife.MAX_BODIES and Vector2(arr[0].x, arr[0].y).distance_to(feet) < 2.0
	var plant = life.plants.filter(func(q): return q.kind in ["tall_grass", "cattails"])[0] if not life.plants.is_empty() else null
	var leaned := false
	if plant != null:
		var r: Rect2 = plant.rects[0]
		p.motor.place(Vector2(r.position.x + 4.0, r.end.y - 3.0) * TopdownRoom.ART)
		w._settle_camera()
		await _frames(tree, 6)
		leaned = plant.bend != 0
	t.check(pushed and leaned, "life view: the grass parts round the player (the shader's push at the feet: %s) and a tall plant leans aside (%s)" % [pushed, leaned])
	# The washing and the banners turn on the wind's clock, faster in a gust.
	var line = life.windy.filter(func(q): return q.kind == "laundry_line")
	var ph0 := TopdownLife.wind_phase
	await _frames(tree, 30)
	t.check(not line.is_empty() and TopdownLife.wind_phase > ph0 and line[0].frame == TopdownLife.wind_frame(line[0].frames, line[0].frame_ms, line[0].phase),
		"life view: the washing on its line turns on the wind's clock (%d windy props)" % life.windy.size())
	# The people at work: the extras work with no label; a sound's cue is raised for any listener.
	var extras: Array = life.workers.filter(func(f): return f.twin == null)
	var heard := []
	life.cue_raised.connect(func(nm, _at): heard.append(nm))
	life.raise_cue("test", p.motor.pos)
	t.check(extras.size() == 2 and heard == ["test"], "life view: the village's two extras work with no label (%d), and a cue is raised for a listener" % extras.size())
	# The living world's own cost a frame.
	var t0 := Time.get_ticks_usec()
	for i in 60: life._process(1.0 / 60.0)
	measured.life_ms = (Time.get_ticks_usec() - t0) / 60000.0
	t.check(float(measured.life_ms) < 1.5, "life view: the living world's own work is %.3f ms a frame in Lotus Ferry" % float(measured.life_ms))
	w.queue_free()
	await tree.process_frame
	await _interior(tree)
	await _vista(tree)
	await _labels(tree)
	TopdownLight.debug_hour = hour
	Game.active_id = was

## Granny Liu's hut: her furnishings, the herbs on her wall, the sun through her window in a shaft with dust in it, and
## her cat asleep by the shrine.
func _interior(tree: SceneTree) -> void:
	var w = TopdownWorld.new()
	w.room_id = "lf_granny_liu_hut"
	tree.root.add_child(w)
	await tree.process_frame
	w.player.motor.place(Vector2(8.5, 9.0) * TopdownRoom.TILE)
	await _frames(tree, 20)
	var life: TopdownLife = w.life
	var kinds := {}
	for pr in w.room.props: kinds[str(pr.kind)] = true
	var cat := life.critters.filter(func(c): return str(c.kind) == "cat")
	t.check(kinds.has("stove") and kinds.has("cabinet") and kinds.has("bed") and life.hangings.size() >= 3 and life.shafts.size() >= 1
		and not life.motes.is_empty() and life.hang_node != null and cat.size() == 1 and str(cat[0].state) in ["sleep", "sit"],
		"life view: Granny Liu's hut is furnished (%d props), hangs %d things on its wall, lets the sun in (%d shafts, %d motes) and keeps a cat" % [w.room.props.size(),
			life.hangings.size(), life.shafts.size(), life.motes.size()])
	w.queue_free()
	await tree.process_frame

## A peak's vista: the camera shows past its south edge into the cloud, as far as the layout's pad, and no further.
func _vista(tree: SceneTree) -> void:
	var room := TopdownRoom.load_room("ja_elder_hu_peak")
	var drawn := room.drawn_rect()
	var shown := room.shown_rect()
	var south := Vector2(20.5, 25.5) * TopdownRoom.TILE
	var cam := room.camera_for(south, 0.0)
	var bottom := cam.y + TopdownRoom.VIEW.y * 0.5
	t.check(shown.end.y > drawn.end.y and bottom > drawn.end.y + 32.0 and bottom <= shown.end.y + 0.5,
		"life view: at a peak's south edge the camera looks %.0f px past it into the cloud (the pad's %.0f)" % [bottom - drawn.end.y, shown.end.y - drawn.end.y])
	var w = TopdownWorld.new()
	w.room_id = "ja_elder_hu_peak"
	tree.root.add_child(w)
	await tree.process_frame
	var vista: TopdownVista = w.life.vista
	t.check(vista != null and vista.get_parent() == w.viewport and vista.get_index() < w.floor_layer.get_index() and vista.edges.size() == 2 and vista.tex != null,
		"life view: the vista is drawn under the room (%d edges)" % (vista.edges.size() if vista != null else 0))
	w.queue_free()
	await tree.process_frame

## A villager at work carries the name and marker over them: their label view follows their figure.
func _labels(tree: SceneTree) -> void:
	var w = TopdownWorld.new()
	w.room_id = "lf_village"
	tree.root.add_child(w)
	await tree.process_frame
	var room: TopdownRoom = w.room
	var side = JSON.parse_string(FileAccess.get_file_as_string("res://data/rooms/lf_village.json"))
	var o: Dictionary = {}
	for ob in side.objects:
		if str(ob.id) == "npc_uncle_guo": o = (ob as Dictionary).duplicate(true)
	var at := TopdownRoom.cell_point(room.def.place.npc_uncle_guo)
	o.at = [at.x, at.y]
	o.alt = 0.0
	var made := TopdownPlaces.person(room, o, w.sorted, w.overlay, w.player)
	var fig = made[1]
	fig.work = TopdownWork.new(TopdownLife.room_life("lf_village").work.npc_uncle_guo, TopdownLife.data().loops, at, 0.0, "npc_uncle_guo")
	w.player.motor.place(Vector2(60.5, 20.5) * TopdownRoom.TILE)
	var moved := 0.0
	var follows := true
	for i in 600:
		await _frames(tree, 1)
		moved = maxf(moved, (fig.plane as Vector2).distance_to(at))
		if (made[0].position as Vector2).distance_to(fig.plane) > 0.5: follows = false
	t.check(moved > 16.0 and follows, "life view: Uncle Guo at his forms moves between his spots (%.0f) and his name and marker go with him (%s)" % [moved, follows])
	w.queue_free()
	await tree.process_frame

func _put(life: TopdownLife, kind: String, g: Vector2) -> TopdownLife.Critter:
	var cr: TopdownLife.Critter = life._critter(kind, g)
	cr.alpha = 1.0
	return cr

func _frames(tree: SceneTree, n: int) -> void:
	for i in n:
		await tree.physics_frame
		await tree.process_frame
