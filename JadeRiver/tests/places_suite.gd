extends RefCounted
## places_suite (decision 43, docs/redesign/systems_as_places.md "As built"): the systems that live at places in the
## world (data/places.json, PlaceRules). rules_tests runs it (`places_suite`) on saves of its own, with a top-down
## character of its own. It checks:
##   - the table: every place stands in a room on the height grid, its object is in the room as the game builds it (an
##     added one too, on its cell's floor), what its sight blocks is blocked, its user's cell is reached by auto-path;
##   - each place opens its page: walked up to (the user's cell), the context button's verb opens the page the table
##     names (a keeper talks and offers the trade; a shrine heals);
##   - the remote rules: Storage, the Garden's tending and the Crafts queue open from anywhere only after their first
##     use at a place and their milestone (a pouch from Tailor Xun, the first harvest, Qi Unfurling), and never before;
##   - the map marks: the world map's Places view marks the area of every place, the minimap has a mark for every
##     place of the room, and a tap on one opens the map's Places on it;
##   - the travel: the Menu's entry of a system that lives at a place says where ("At the Storehouse") and opens its
##     card, whose Travel starts the walk: through the rooms, then on to the place's user's cell, where it ends;
##   - the unlock order: a system first used in the prologue or the tutorial has its home place on their path, and no
##     place's cells cut a way or a thing of its room off.

var t   # the running suite (check)
var c

func run_all(suite, tree: SceneTree) -> void:
	t = suite
	var folder: String = suite.run_root() + "places_suite/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Game.boot()
	Game.autosave_enabled = false
	Game.submit({"type": "create_character", "slot": 1, "name": "Places", "view": "topdown"})
	c = Game.character("c1")
	Game.active_id = c.id
	Unlocks.grant_prologue(c.id)
	c.quests.flags["prologue_done"] = true
	for sc in ContentDB.all("scenes"): c.quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	_table()
	_opens_pages()
	_poses(tree)
	_remote_rules()
	await _marks(tree)
	_travel()
	_unlock_order()

func check(ok: bool, what: String) -> void:
	t.check(ok, what)

## Enter a room of the world on the grid, the body standing at `at` (world units) on its floor.
func enter(room: String, at: Vector2) -> void:
	Game.world.load_room(c, room, "", at)
	GameEvents.flush()
	var st := ActorState.new()
	st.plane = at
	st.altitude = Game.room_rt.topdown.floor_at(at) if Game.room_rt.topdown != null else 0.0
	Game.bind_movement(c.id, st)

# ------------------------------------------------------------------ the table
func _table() -> void:
	var rows: Array = PlaceRules.all()
	var bad: Array = []
	var kinds := PlaceRules.kinds()
	for r in rows:
		var room := TopdownRoom.load_room(str(r.room))
		var def := room.merge_def(ContentDB.room(str(r.room)))
		var obj := {}
		for o in def.get("objects", []):
			if str(o.get("id", "")) == str(r.object): obj = o
		var stand := Vector2i(int(r.stand[0]), int(r.stand[1]))
		var why := ""
		if room.w == 0: why = "no layout"
		elif obj.is_empty() or not obj.has("at"): why = "object %s not in the room as built" % str(r.object)
		elif str(r.page) != "" and not str(r.page) in load("res://scripts/main.gd").PAGES: why = "page %s unknown" % str(r.page)
		elif not kinds.has(str(r.kind)): why = "kind %s unknown" % str(r.kind)
		elif not str(r.rule) in ["both", "earned", "place"]: why = "rule %s" % str(r.rule)
		elif not room.standable(stand): why = "its user's cell %s is not standable" % str(stand)
		elif r.get("added", false) and absf(float(obj.get("alt", -1.0)) - room.floor_at(PlaceRules.point(r))) > 0.5: why = "an added object off its floor"
		for s in PlaceRules.solids(str(r.room)):
			for y in (s as Rect2i).size.y:
				for x in (s as Rect2i).size.x:
					if room.level(s.position.x + x, s.position.y + y) != TopdownRoom.SOLID: why = "a sight's cell not blocked"
		# auto-path's own rules reach the user's cell from the room's spawn and every way in
		for p in def.get("portals", []):
			if not p.has("arrive"): continue
			var from := TopdownRoom.cell_of(Vector2(float(p.arrive[0]), float(p.arrive[1])))
			if from != stand and TopdownRoute.find(room, from, stand, true).is_empty(): why = "auto-path does not reach it from way %s" % str(p.id)
		if why != "": bad.append("%s: %s" % [r.id, why])
	check(rows.size() >= 20 and bad.is_empty(), "places: every place stands in a room on the grid, its object built there, its sight's cells blocked, its user's cell reached by auto-path from every way in (%d places; %s)" % [rows.size(), str(bad)])
	# The study's prototype set: a board with papers, a stall with its keeper, the storehouse, beds, a furnace, a
	# teleport stone, a meditation mat, a letter box.
	var have := {}
	for r in rows: have[str(r.kind)] = true
	var want := ["notice_board", "stall", "storehouse", "garden_bed", "furnace", "teleport_stone", "meditation_mat", "letter_box", "shrine"]
	check(want.all(func(k): return have.has(k)), "places: the study's prototype set is built (%s)" % str(have.keys()))
	# The added things are in their rooms as the game builds them, and nowhere in the side view.
	var lf := TopdownRoom.load_room("lf_village")
	var lf_def := lf.merge_def(ContentDB.room("lf_village"))
	var added := (lf_def.objects as Array).filter(func(o): return o.has("place")).map(func(o): return str(o.type))
	check("letter_box" in added and "meditation_mat" in added and not (ContentDB.room("lf_village").objects as Array).any(func(o): return o.has("place")),
		"places: the letter box and the meditation mat are added to Lotus Ferry on the grid, not to its side view (%s)" % str(added))

# ------------------------------------------------------------------ each place opens its page
func _opens_pages() -> void:
	for s in ["mail", "notice_board", "storage", "alchemy", "herb_garden", "teleport_stones", "cooking", "smithing", "cultivation", "shop", "shrines"]:
		Unlocks.force_unlock(c.id, s)
	var bad: Array = []
	for r in PlaceRules.all():
		# A sect's places, as one of its disciples (the other sect's grounds are not theirs to walk).
		c.training_sect = {"id": str(r.get("sect", "")) if str(r.get("sect", "")) != "" else "jade_sect", "rank": "outer", "contribution": 0}
		enter(str(r.room), PlaceRules.stand_point(r))
		var ctx: Dictionary = Game.world.query_context(c)
		var res: Dictionary = Game.world.interact(c, str(r.object))
		var got := ""
		if res.has("open_page"): got = str(res.open_page)
		elif res.has("dialogue"):
			for ch in res.dialogue.get("choices", []):
				if ch.has("shop"): got = "shop"
		elif res.get("ok", false) and str(r.page) == "": got = ""
		var want := str(r.page)
		if not res.get("ok", false) or got != want: bad.append("%s: %s (%s)" % [r.id, got, str(res.get("reason", res.get("text", "")))])
		elif str(ctx.get("object", "")) != str(r.object): bad.append("%s: the context button offers %s" % [r.id, str(ctx.get("object", ctx.get("portal", "")))])
	check(bad.is_empty(), "places: walked up to (its user's cell), the context button's verb at every place opens the page the table names, a keeper's talk offers the trade (%s)" % str(bad))
	# The verbs: the letter box is read, the mat is sat on.
	var lb := {"type": "letter_box"}
	var mat := {"type": "meditation_mat"}
	check(Game.world.verb(lb) == Tx.t("sim.world.read") and Game.world.verb(mat) == Tx.t("sim.world.sit"), "places: the letter box's verb is Read, the mat's Sit")

# ------------------------------------------------------------------ decision 44: the place poses
## Using a place plays its pose before its page (the HUD): the storehouse's and the letter box's `open`, a garden bed's
## and a furnace's `tend`, the mat's `sit`; the page opens after the pose (HUD.PLACE_POSE_S, snappy: at most half a
## second), at once on a second tap of the context button; the body holds the pose while the page is open and rises
## when it closes; a place with no pose (a notice board, a shop) opens its page at once. Walked up to and pressed, each
## still reaches its page.
func _poses(tree: SceneTree) -> void:
	var hud = load("res://scripts/hud.gd").new()
	tree.root.add_child(hud)
	hud.visible = false
	var src := GDScript.new()
	# the player's fields a page blocking the HUD lets go of (HUD._notification), and the place pose's two calls
	src.source_code = "extends Node2D\nvar actor_id := \"\"\nvar plane := Vector2.ZERO\nvar movement := Vector2.ZERO\nvar joystick_engaged := false\nvar posed: Array = []\nfunc reset_sprint() -> void:\n\tpass\nfunc play_place_pose(p: String) -> void:\n\tposed.append(p)\nfunc end_place_pose() -> void:\n\tposed.append(\"end\")\n"
	src.reload()
	var stub = src.new()
	stub.actor_id = c.id
	hud.player = stub
	var asked: Array = []
	# as main.gd does: a page opened blocks the HUD until it closes
	hud.open_page.connect(func(pg: String, _a: Dictionary):
		asked.append(pg)
		hud.set_blocked(true))
	var want_of := {"storehouse": "open", "letter_box": "open", "garden_bed": "tend", "furnace": "tend", "meditation_mat": "sit"}
	var bad: Array = []
	var tried := {}
	for r in PlaceRules.all():
		var want := str(want_of.get(str(r.kind), ""))
		if str(r.get("pose", "")) != want: bad.append("%s: pose %s" % [r.id, r.get("pose", "")])
		if tried.has(str(r.kind)) or str(r.page) == "": continue
		tried[str(r.kind)] = true
		c.training_sect = {"id": str(r.get("sect", "")) if str(r.get("sect", "")) != "" else "jade_sect", "rank": "outer", "contribution": 0}
		enter(str(r.room), PlaceRules.stand_point(r))
		if not Game.world.interact(c, str(r.object)).has("open_page"):
			tried.erase(str(r.kind))   # a keeper's talk, a shrine's blessing: no page of its own to pose before
			continue
		for skip in [false, true]:
			asked.clear()
			stub.posed.clear()
			hud.set_blocked(false)
			stub.posed.clear()
			hud.after_interact(Game.world.interact(c, str(r.object)), str(r.object))
			if want == "":
				if asked != [str(r.page)]: bad.append("%s: no pose, page %s" % [r.id, str(asked)])
				break
			if not asked.is_empty() or stub.posed != [want]: bad.append("%s: pose first (%s, %s)" % [r.id, str(stub.posed), str(asked)])
			if skip:
				hud.use_context()   # the second tap
			else:
				hud.tick_place_pose(hud.PLACE_POSE_S * 0.5)
				if not asked.is_empty(): bad.append("%s: page before the pose ends" % r.id)
				hud.tick_place_pose(hud.PLACE_POSE_S * 0.5 + 0.01)
			if asked != [str(r.page)]: bad.append("%s: page after the pose (skip %s): %s" % [r.id, skip, str(asked)])
			if stub.posed.has("end"): bad.append("%s: rose while the page is open" % r.id)
			hud.set_blocked(false)
			if stub.posed.back() != "end": bad.append("%s: did not rise as the page closed" % r.id)
	hud.queue_free()
	check(bad.is_empty() and tried.size() >= 8 and hud.PLACE_POSE_S <= 0.5,
		"places: using a place plays its pose (open, tend, sit) then opens its page (%.1f s, a second tap at once), held while it is open; a place with no pose opens at once (%d kinds; %s)" % [hud.PLACE_POSE_S, tried.size(), str(bad.slice(0, 4))])

# ------------------------------------------------------------------ the remote rules
func _remote_rules() -> void:
	# Storage: bound to its place until a first use there and Tailor Xun's pouch.
	c.quests.flags.erase(PlaceRules.USED + "storage")
	c.cultivator.unlocked.erase("pouch_sewing")
	var bound0 := PlaceRules.bound(c, "storage")
	enter("sf_market", PlaceRules.stand_point(PlaceRules.get_place("sf_storehouse")))
	Game.world.interact(c, "storage_sf")
	var used := PlaceRules.used(c, "storage")
	var still := PlaceRules.bound(c, "storage")
	Unlocks.force_unlock(c.id, "pouch_sewing")
	var freed := PlaceRules.remote_open(c, "storage") and not PlaceRules.bound(c, "storage")
	check(PlaceRules.rule("storage") == "earned" and bound0 and used and still and freed,
		"places: Storage opens at its storehouse first; from anywhere only after a first use there and Tailor Xun's pouch (bound %s, used %s, still %s, freed %s)" % [bound0, used, still, freed])
	# The Garden's tending: a bed is tended in its own room until the first harvest there, then from anywhere.
	c.quests.flags.erase(PlaceRules.USED + "herb_garden")
	var key := "ja_herb_terraces:bed_0"
	var seed := ""
	for it in ContentDB.all("items"):
		if (it.get("seed", {}) as Dictionary).has("family"):
			seed = str(it.id)
			break
	enter("sf_market", Vector2(20 * 32, 17 * 32))
	var away0: String = Game.crafting.bed_check(c, key)
	enter("ja_herb_terraces", PlaceRules.stand_point(PlaceRules.get_place("ja_garden")))
	var rec: Dictionary = Game.crafting.bed_record(c, key)
	rec.herb = str(ContentDB.config("garden").get("families", {}).values()[0].get("10", ""))
	rec.progress = 1.0
	rec.updated = Clock.now_utc()
	var harvest: Dictionary = Game.crafting.harvest_bed(c, key)
	enter("sf_market", Vector2(20 * 32, 17 * 32))
	var away1: String = Game.crafting.bed_check(c, key)
	check(PlaceRules.rule("herb_garden") == "earned" and away0 == Tx.t("sim.crafting.bed_elsewhere") and harvest.get("ok", false) and away1 == "" and seed != "",
		"places: a bed is tended where it grows until the first harvest there, then from anywhere (before %s, harvest %s, after %s)" % [away0, str(harvest.get("ok", false)), away1])
	# The Crafts queue: a batch is queued at a furnace until Qi Unfurling (and a first batch queued at one).
	c.quests.flags.erase(PlaceRules.USED + "alchemy")
	Unlocks.force_unlock(c.id, "auto_refine")
	c.cultivator.realm_key = "qi_kindling_8"
	var recipe := "healing_pill"
	if not c.crafting.recipes.has(recipe): c.crafting.recipes.append(recipe)
	for inp in ContentDB.entry("recipes", recipe).get("inputs", []): Game.inventory.apply_add(c.id, str(inp.item), int(inp.count) * 4, "test")
	c.crafting.auto_queue = []
	enter("sf_market", Vector2(20 * 32, 17 * 32))
	var q0: Dictionary = Game.crafting.queue_auto(c, recipe, 1)
	enter("sf_artisan_row", PlaceRules.stand_point(PlaceRules.get_place("sf_furnace")))
	var q1: Dictionary = Game.crafting.queue_auto(c, recipe, 1)
	enter("sf_market", Vector2(20 * 32, 17 * 32))
	var q2: Dictionary = Game.crafting.queue_auto(c, recipe, 1)   # used, but below Qi Unfurling
	c.cultivator.realm_key = "qi_unfurling_1"
	var q3: Dictionary = Game.crafting.queue_auto(c, recipe, 1)
	check(not q0.get("ok", false) and q1.get("ok", false) and not q2.get("ok", false) and q3.get("ok", false),
		"places: the Crafts queue is filled at a furnace until a first batch there and Qi Unfurling, then from anywhere (away %s, at the furnace %s, away below QU %s, away at QU %s)"
		% [str(q0.get("ok")), str(q1.get("ok")), str(q2.get("ok")), str(q3.get("ok"))])
	c.crafting.auto_queue = []
	c.cultivator.realm_key = "qi_kindling_5"
	# "both" and "place" systems: the letter box's Mail is in the Menu too; a shop only at its keeper.
	check(PlaceRules.remote_open(c, "mail") and not PlaceRules.remote_open(c, "shop") and not PlaceRules.bound(c, "mail"),
		"places: Mail (both) opens from anywhere and a shop (place) only at its keeper")

# ------------------------------------------------------------------ the marks
func _marks(tree: SceneTree) -> void:
	var map = load("res://scripts/ui/pages/map_page.gd").new()
	map.visible = false
	tree.root.add_child(map)
	map.page_id = "world_map"
	var missing: Array = []
	for r in PlaceRules.all():
		c.training_sect = {"id": str(r.get("sect", "")) if str(r.get("sect", "")) != "" else "jade_sect", "rank": "outer", "contribution": 0}
		map.args = {"place": str(r.id)}
		map.setup()
		var m: Dictionary = map.model(c)
		var placed: Dictionary = map.place_marks(c, m)
		var rid := str(m.z.node_of.get(str(r.room), ""))
		if map.view != "places" or not placed.marks.has("place:" + rid) or str(m.get("place", {}).get("id", "")) != str(r.id): missing.append(str(r.id))
	check(missing.is_empty(), "places: the world map's Places view marks the area of every place, and opened on a place chooses it (%s)" % str(missing))
	map.queue_free()
	# The minimap: a mark for every place of the room, and a tap near one opens the map's Places on it.
	var hud = load("res://scripts/hud.gd").new()
	hud.visible = false
	hud.process_mode = Node.PROCESS_MODE_DISABLED
	tree.root.add_child(hud)
	var lost: Array = []
	for room in ["lf_village", "sf_market", "sf_artisan_row", "ja_gate_street", "ja_herb_terraces", "lf_old_ma_store"]:
		var marks: Array = hud.place_marks(c, room, func(p: Vector2, _a: float) -> Vector2: return p * 0.1)
		var ids := marks.map(func(mk): return str(mk.id))
		for r in PlaceRules.of_room(room):
			if PlaceRules.visible(c, r) and not str(r.id) in ids: lost.append(str(r.id))
		hud.minimap_places = marks
		for mk in marks:
			if str(hud.minimap_place_at(mk.at + Vector2(3, 2)).get("place", "")) != str(mk.id) and marks.filter(func(o): return (o.at as Vector2).distance_to(mk.at) < 16.0).size() == 1: lost.append("tap:" + str(mk.id))
	check(lost.is_empty(), "places: the minimap marks every place of its room with its glyph, and a tap on one opens the map's Places on it (%s)" % str(lost))
	hud.queue_free()

# ------------------------------------------------------------------ the travel
func _travel() -> void:
	c.cultivator.unlocked.erase("pouch_sewing")
	c.quests.flags.erase(PlaceRules.USED + "storage")
	enter("sf_market", Vector2(30 * 32, 17 * 32))
	var menu = load("res://scripts/ui/pages/menu_page.gd").new()
	var line: String = menu.line_of(c, "storage")
	menu.on_action("open", "storage")
	var carded: bool = str(menu.card.get("system", "")) == "storage"
	var pl := PlaceRules.home(c, "storage")
	# The card's Travel: the walk through the rooms, then on inside the place's room to its user's cell.
	var r: Dictionary = Game.submit({"type": "auto_path", "target": "", "place": str(pl.id)})
	var first: Dictionary = Game.world.auto_path_step(c)
	menu.free()
	var way := Game.world.route(c, "sf_market", str(pl.room))
	enter(str(pl.room), Vector2(10 * 32, 20 * 32))
	GameEvents.flush()
	var going := Game.world.auto_path_target(c) == str(pl.room)
	var step: Dictionary = Game.world.auto_path_step(c)
	var sp := PlaceRules.stand_point(pl)
	var got := {"reached": false}   # a lambda sets what it holds, never a local it captured
	var hear := func(n: String, p: Dictionary) -> void:
		if n == "place_reached" and str(p.get("place", "")) == str(pl.id): got.reached = true
	GameEvents.event.connect(hear)
	Game.world.auto_path_arrive(c)
	GameEvents.flush()
	GameEvents.event.disconnect(hear)
	check(line == str(pl.where) and line == "At the Storehouse" and carded and r.get("ok", false) and first.has("portal") and not way.is_empty() and going
		and str(step.get("place", "")) == str(pl.id) and Vector2(float(step.x), float(step.y)) == sp and Game.world.auto_path_target(c) == "" and got.reached,
		"places: the Menu's Storage says where it lives (%s) and opens its card; Travel walks through the rooms (first %s) and on to the storehouse's user's cell (%s), where it ends" % [line, str(first), str(step)])
	# Standing in the place's room already, the walk goes straight to it.
	var r2: Dictionary = Game.submit({"type": "auto_path", "target": "", "place": str(pl.id)})
	var step2: Dictionary = Game.world.auto_path_step(c)
	Game.submit({"type": "auto_path", "target": ""})
	# The grid's own route (auto-path's rules, round everything on the way) reaches it from the village's lane.
	var room: TopdownRoom = Game.room_rt.topdown
	var cells := TopdownRoute.find(room, TopdownRoom.cell_of(Vector2(10 * 32, 20 * 32)), TopdownRoom.cell_of(sp), true)
	check(r2.get("ok", false) and str(step2.get("place", "")) == str(pl.id) and not cells.is_empty(),
		"places: from inside its room the walk goes straight to the place, by the grid's route (%d cells)" % cells.size())
	# Once remote access is earned the Menu opens Storage itself.
	Unlocks.force_unlock(c.id, "pouch_sewing")
	PlaceRules.note_use(Game, c, "storage")
	var menu2 = load("res://scripts/ui/pages/menu_page.gd").new()
	var went := []
	menu2.navigate.connect(func(page, _a): went.append(page))
	menu2.on_action("open", "storage")
	check(went == ["storage"] and menu2.card.is_empty() and menu2.line_of(c, "storage") == "", "places: with remote access earned the Menu's Storage opens the page (%s)" % str(went))
	menu2.free()

# ------------------------------------------------------------------ the unlock order
func _unlock_order() -> void:
	var rooms: Array = ContentDB.config("places").get("tutorial_rooms", [])
	var bad: Array = []
	for u in ContentDB.all("unlocks"):
		var rows := PlaceRules.of_system(str(u.id))
		if rows.is_empty(): continue
		var early: bool = u.get("prologue", false) or str(u.id) in ["mail", "notice_board", "shop"]
		if not early: continue
		var home := rows.filter(func(r): return r.get("home", false))
		if home.is_empty() or not str(home[0].room) in rooms: bad.append(str(u.id))
		if rows.any(func(r): return str(r.rule) == "earned"): bad.append(str(u.id) + " earned")
	check(bad.is_empty(), "places: every system of the prologue and the tutorial has its home place on their path and is never bound to it (%s)" % str(bad))
