extends RefCounted
## Terrain v2's third part (decision 40; docs/redesign/art_bible.md "Foliage and decor"): the foliage and decor rules,
## on every room with a layout. rules_tests runs it with topdown_suite.
##   - The scatter keeps off every path, paving and built floor, the water, the props, the stairs, each way out's
##     lane, the spawn and every person's and thing's spot; it is the same on every build; the outdoor rooms are dense.
##   - A tree's trunk blocks (a body walking into it stops); its canopy blocks nothing.
##   - The decor draws are batched: the pieces are drawn inside the floor's chunks and rows (no node per piece), the
##     swaying ones on the GPU; a canopy sorts just after its trunk and fades while the player is under it.

var t   # the running suite (check)
var measured := {}

const PATHS := "dpswtl"   # the marks no ground cover grows on: paths, paving, granite, planks, roofs, walls

func rooms() -> Array:
	var out: Array = []
	for f in DirAccess.get_files_at("res://data/topdown/"):
		if not f.ends_with(".json"): continue
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/" + f))
		if d is Dictionary and d.has("levels") and not str(d.get("id", "")).begins_with("td_"): out.append(f.get_basename())
	out.sort()
	return out

func run_all(suite) -> void:
	t = suite
	_scatter_rules()
	_trunks_and_canopies()

## Every piece of every room's ground cover: on a floor it grows on, off the paths, props, stairs and water, and clear
## of the spawn, every spot and every way's lane (checked here from the layout itself, not the scatter's own rules).
func _scatter_rules() -> void:
	var bad: Array = []
	var dense: Array = []
	var total := 0
	var outdoor := 0
	var marks := {}
	for rid in rooms():
		var room := TopdownRoom.load_room(rid)
		var items := TopdownFoliage.scatter(room)
		total += items.size()
		var keep := {}
		keep[TopdownRoom.cell_of(room.spawn)] = "spawn"
		for oid in room.def.get("place", {}): keep[TopdownRoom.cell_of(TopdownRoom.cell_point(room.def.place[oid]))] = "spot " + str(oid)
		for pid in room.def.get("portals", {}):
			var p: Dictionary = room.def.portals[pid]
			keep[TopdownRoom.cell_of(TopdownRoom.cell_point(p.at))] = "way " + str(pid)
			if p.has("arrive"): keep[TopdownRoom.cell_of(TopdownRoom.cell_point(p.arrive))] = "way in " + str(pid)
		for it in items:
			var c := Vector2i(floori(float(it[0]) / 16.0), floori(float(it[1]) / 16.0))
			var i := c.y * room.w + c.x
			var mark := room.paint_at(c.x, c.y)
			marks[mark] = true
			var why := ""
			if not room.inside(c.x, c.y): why = "outside"
			elif mark in PATHS: why = "on '%s'" % mark
			elif room.levels[i] < 0: why = "on the water"
			elif room.solid[i] == 1: why = "under a prop"
			elif room.stair_of[i] > 0: why = "on the stairs"
			elif keep.has(c): why = "on " + str(keep[c])
			if why != "": bad.append("%s %s: %s" % [rid, str(c), why])
		var grass := 0
		for k in room.w * room.h:
			if char(room.paint[k]) in "gfm" and room.levels[k] >= 0: grass += 1
		if grass > 400:
			outdoor += 1
			if items.size() < grass / 5: dense.append("%s (%d pieces on %d meadow cells)" % [rid, items.size(), grass])
	measured.decor_pieces = total
	t.check(bad.is_empty(), "foliage: no ground cover on a path, paving, the water, a prop, the stairs, the spawn, a spot or a way (%s)" % str(bad.slice(0, 4)))
	t.check(outdoor >= 15 and dense.is_empty() and total > 8000, "foliage: the %d outdoor rooms are covered, %d pieces in all (thin: %s)" % [outdoor, total, str(dense)])
	# The same on every build: a second room of the same id, freshly read, scatters the same pieces.
	var a := TopdownFoliage.scatter(TopdownRoom.load_room("lf_village"))
	TopdownFoliage._cache.clear()
	var b := TopdownFoliage.scatter(TopdownRoom.load_room("lf_village"))
	t.check(a.size() > 300 and a == b, "foliage: Lotus Ferry's scatter is a pure function of the room (%d pieces, the same twice)" % a.size())
	# The litter under trees, the reeds on shores and the dense tall-grass patches all appear.
	var sprites: Array = (TopdownFoliage.manifest().sprites as Dictionary).keys()
	sprites.sort()
	var kinds := {}
	for it in a: kinds[str(sprites[int(it[2])]).get_slice("_", 0)] = true
	var shore := {}
	for it in TopdownFoliage.scatter(TopdownRoom.load_room("lf_reed_shallows")): shore[str(sprites[int(it[2])]).get_slice("_", 0)] = true
	t.check(kinds.has("litter") and kinds.has("tuft") and kinds.has("flower") and (shore.has("reeds") or shore.has("cattail")),
		"foliage: Lotus Ferry has litter under its trees, tufts and flowers, the Reed Shallows reeds on its shore (%s; %s)" % [str(kinds.keys()), str(shore.keys())])

## Trunks block and canopies do not, in every room; a body walking into a trunk stops at it.
func _trunks_and_canopies() -> void:
	var open: Array = []
	var shut: Array = []
	var trees := 0
	var kinds := {}
	for rid in rooms():
		var room := TopdownRoom.load_room(rid)
		var owned := {}
		for p in room.props:
			for y in (p.size as Vector2i).y:
				for x in (p.size as Vector2i).x: owned[(p.cell as Vector2i) + Vector2i(x, y)] = true
		for p in room.props:
			var art: Dictionary = p.art
			if not art.get("foliage", false): continue
			kinds[p.kind] = true
			var c: Vector2i = p.cell
			if art.get("solid", true) and room.level(c.x, c.y) != TopdownRoom.SOLID: open.append("%s %s %s" % [rid, p.kind, str(c)])
			if not art.get("solid", true) and room.level(c.x, c.y) == TopdownRoom.SOLID and not owned.has(c): shut.append("%s %s" % [rid, p.kind])
			if not art.has("canopy"): continue
			trees += 1
			# Under the canopy (the cells north of the trunk, beside it), a plain floor stays a floor.
			for y in range(c.y - 3, c.y + 1):
				for x in range(c.x - 2, c.x + 3):
					var q := Vector2i(x, y)
					if q == c or owned.has(q) or not room.inside(x, y) or room.levels[y * room.w + x] < 0: continue
					if not room.standable(q): shut.append("%s under the %s at %s" % [rid, p.kind, str(c)])
	t.check(open.is_empty() and trees >= 100, "foliage: %d trees stand in the rooms, every trunk, bush, hedge, fence and rock blocks (%s)" % [trees, str(open.slice(0, 3))])
	t.check(shut.is_empty(), "foliage: canopies, tall grass, cattails, ferns and lotus pads block nothing (%s)" % str(shut.slice(0, 3)))
	t.check(kinds.size() >= 20, "foliage: %d kinds of the kit are placed in the rooms" % kinds.size())
	# A body walking east into a trunk stops west of it.
	var room := TopdownRoom.load_room("lf_village")
	var tree: Dictionary = room.props.filter(func(q): return q.kind == "tree_camphor")[0]
	var tc: Vector2i = tree.cell
	var m := TopdownMotor.new(room, (Vector2(tc) + Vector2(-1.5, 0.5)) * TopdownRoom.TILE)
	for f in 90: m.step(1.0 / 60.0, Vector2.RIGHT)
	t.check(m.pos.x < tc.x * TopdownRoom.TILE, "foliage: a body walking into a camphor's trunk stops at it (%.0f < %.0f)" % [m.pos.x, tc.x * TopdownRoom.TILE])

## The room view: the decor drawn inside the floor's chunks (no node per piece), the sway on the GPU, the canopies over
## their trunks, and a canopy fading while the player stands under it and coming back when they leave.
func run_view(suite, tree: SceneTree) -> void:
	t = suite
	var was: String = Game.active_id
	Game.active_id = ""
	var w = TopdownWorld.new()
	w.room_id = "lf_village"
	tree.root.add_child(w)
	await tree.process_frame
	await tree.process_frame
	var fol: TopdownFoliage = w.foliage
	var nodes: int = w.viewport.get_child_count() + w.sorted.get_child_count()
	var swaying: int = w.viewport.get_children().filter(func(n): return n.get("chunk") is Rect2i and n.material == TopdownFoliage.sway_material()).size()
	measured.view = {"pieces": fol.items.size(), "nodes": nodes, "canopies": fol.canopies.size(), "swaying_chunks": swaying}
	t.check(fol.items.size() > 300 and nodes < fol.items.size() / 4 and swaying > 0,
		"foliage view: Lotus Ferry's %d pieces of ground cover draw inside its floor chunks and rows (%d nodes in all), the swaying ones in %d chunks on the GPU" % [fol.items.size(), nodes, swaying])
	var trunks := {}
	for n in w.sorted.get_children():
		if n.get("src") != null and n.get("frames") != null and not n is TopdownFoliage.Canopy: trunks[n.position.y] = true
	var after := fol.canopies.filter(func(cv): return trunks.has(cv.position.y - 1.0 / 64.0))
	t.check(fol.canopies.size() >= 10 and after.size() == fol.canopies.size() and fol.canopies.all(func(cv): return (cv.rects as Array).is_empty()),
		"foliage view: %d canopies sort just after their trunks and never call the silhouette" % fol.canopies.size())
	# Under a camphor's canopy (north of its trunk): the canopy fades; away from it, it comes back.
	var cv = fol.canopies.filter(func(q): return q.level == 0 and q.box.size.x > 70)[0]
	var p = w.player
	var feet: Vector2 = Vector2(cv.box.get_center().x, cv.position.y - 20.0)
	p.motor.place(Vector2(feet.x, feet.y) * TopdownRoom.ART)
	for f in 40:
		await tree.physics_frame
		await tree.process_frame
	var under: float = cv.modulate.a
	p.motor.place(Vector2(feet.x, cv.position.y + 60.0) * TopdownRoom.ART)
	for f in 40:
		await tree.physics_frame
		await tree.process_frame
	var back: float = cv.modulate.a
	t.check(is_equal_approx(under, TopdownFoliage.FADE_A) and is_equal_approx(back, 1.0),
		"foliage view: a canopy fades to %.2f while the player is under it and comes back (%.2f)" % [under, back])
	w.queue_free()
	await tree.process_frame
	Game.active_id = was
