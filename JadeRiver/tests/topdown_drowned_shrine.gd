extends "res://tests/prologue_run.gd"
## topdown_drowned_shrine (R2; docs/architecture/room_engine.md, "The Drowned Shrine and Whitewater Gorge"): the ten rooms
## the room engine laid out from the side view south and west of Bend Shore, played on the height grid by a top-down
## character. Test shortcuts carry a new character to Bend Shore with the story before chapter 5 done, at Heart
## Tempering 1 (the realm the shrine and the gorge ask), with a sturdy body (the fights are the rooms', not the
## balance's); quests are taken and handed in where they stand (their givers are the sects' mentors, far off). From
## there it is played through the World authority:
##   1. each room is entered on the grid through its ways from the room before, and the top-down view builds it (a
##      figure for every person and thing, a mark for every way); in each, auto-path (TopdownRoute.reach: a hop up a
##      level, no running jump) reaches every NPC, object, herb, place and way from the spawn and every way in;
##   2. the Serpent's Shallows, south of Bend Shore's ford: the Riverbed Serpent, its field boss, defeated on the grid
##      (The Riverbed Serpent), and back to Bend Shore up the river by the way east;
##   3. the Drowned Shrine, down Bend Shore's steps (chapter 5): The Shrine Surfaces (the Flooded Gate reached); Lu's
##      Handwriting (the four inscriptions read in the Hall of Lanterns); The Riverbreath Trial (the stone ring's trial
##      held at the Scripture Well, its drowned rising on the grid's own cells, TopdownRoom.grid_event); the flooded
##      shaft down to the Drowned Grotto and back (Breath Control); The Drowned Abbot (his four bells rung, the Abbot
##      defeated) and up the Sanctum's stair to Bend Shore;
##   4. Whitewater Gorge, Bend Shore's way west: the Gorge Mouth, the Rapids Terraces, the cave behind their waterfall
##      (its hidden way once found) and back, the Echo Cliffs, whose way west to Crane Cliffs stays closed by the
##      prototype's gate while Crane Cliffs has no layout.
## Run headless:  godot --headless --path . res://tests/topdown_drowned_shrine.tscn [-- --verbose]

const ROOMS := ["dw_serpents_shallows", "ds_flooded_gate", "ds_hall_of_lanterns", "ds_scripture_well", "ds_drowned_grotto",
	"ds_abbots_sanctum", "wg_gorge_mouth", "wg_rapids_terraces", "wg_waterfall_cave", "wg_echo_cliffs"]
const SHRINE := ["the_shrine_surfaces", "lus_handwriting", "the_riverbreath_trial", "the_drowned_abbot"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("r2/")
	_to_the_bend()
	GameEvents.event.connect(_on_room)
	_the_shallows()
	_the_shrine()
	_the_gorge()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to Bend Shore
## The story before chapter 5 done (its prologue and main quests to chapter 4), the prologue's systems and scenes,
## Heart Tempering 1, a sturdy body (a test shortcut: the walk is about the rooms), at Bend Shore.
func _to_the_bend() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		if str(q.get("kind", "")) in ["prologue", "main"] and not str(q.id) in SHRINE and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 4)):
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	c().cultivator.realm_key = "heart_tempering_1"
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(cid)
	Unlocks.force_unlock(cid, "field_bosses")
	GameEvents.flush()
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 1400.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 14000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 700.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "dw_bend_shore", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "dw_bend_shore" and Game.room_rt.topdown != null and ProgressionRules.at_least(c().cultivator.realm_key, "heart_tempering_1"),
		"at Bend Shore on the grid, Heart Tempering 1 (room %s, realm %s)" % [room(), c().cultivator.realm_key])

## Stats rebuilt (the sturdy body's modifiers among them) and the body whole again between the fights.
func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp

## A quest taken where the character stands (a test shortcut: its giver is a sect's mentor, far off).
func _take(qid: String) -> void:
	Game.quest.apply_start(c().id, qid)
	GameEvents.flush()
	check(c().quests.is_active(qid), "%s under way" % qid)

## A quest whose steps are done, handed in where the character stands (a test shortcut, as `_take`).
func _done(qid: String, what: String) -> void:
	GameEvents.flush()
	var ready: bool = str(c().quests.active.get(qid, {}).get("state", "")) == "ready"
	var r: Dictionary = Game.quest.hand_in(c(), qid) if ready else {}
	GameEvents.flush()
	check(ready and r.get("ok", false) and c().quests.is_done(qid), "%s: %s (state %s)" % [qid, what, str(c().quests.active.get(qid, {}).get("state", "done" if c().quests.is_done(qid) else "?"))])

## A boss weakened first (a test shortcut: the fight is the room's, not the balance's), then fought on the grid.
func _boss(def_id: String) -> int:
	_whole()
	for e in Game.room_rt.living_enemies():
		if e.def_id == def_id: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.15)
	return fight(def_id, 1, 300.0, 0.0, true)

# ------------------------------------------------------------------ 1: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not rid in ROOMS or entered.has(rid): return
	entered[rid] = Game.room_rt.topdown != null
	if Game.room_rt.topdown == null: return
	_walks(rid)
	_view(rid)

## Auto-path reaches every thing and way from the spawn and every way in.
func _walks(rid: String) -> void:
	var grid: TopdownRoom = Game.room_rt.topdown
	var def: Dictionary = Game.room_rt.def
	var starts: Array = [TopdownRoom.cell_of(grid.spawn)]
	for w in def.get("portals", []):
		if w.has("arrive"): starts.append(TopdownRoom.cell_of(Vector2(float(w.arrive[0]), float(w.arrive[1]))))
	for s in starts:
		var seen := {}
		for cell in TopdownRoute.reach(grid, s, true): seen[cell] = true
		for o in def.get("objects", []):
			if str(o.get("type", "")) == "decor" or not o.has("at"): continue
			var c0 := TopdownRoom.cell_of(Vector2(float(o.at[0]), float(o.at[1])))
			var alt := float(o.get("alt", 0.0))
			var ok := false
			for dy in range(-3, 4):
				for dx in range(-3, 4):
					var q := c0 + Vector2i(dx, dy)
					if dx * dx + dy * dy <= 9 and seen.has(q) and absf(grid.cell_floor(q) - alt) <= 48.0: ok = true
			if not ok: walk_misses.append("%s: %s from %s" % [rid, str(o.id), str(s)])
		for w in def.get("portals", []):
			if not seen.has(TopdownRoom.cell_of(Vector2(float(w.at[0]), float(w.at[1])))): walk_misses.append("%s: way %s from %s" % [rid, str(w.id), str(s)])

## The character's own top-down view built on the room: a figure for every person and thing, a mark for every way.
func _view(rid: String) -> void:
	if not is_instance_valid(probe):
		var was: String = Game.active_id
		Game.active_id = ""   # the view alone: the walk keeps the body bound
		probe = TopdownWorld.new()
		probe.live = true
		probe.sim_frozen = true
		add_child(probe)
		probe.set_process(false)
		probe.set_physics_process(false)
		Game.active_id = was
	else:
		probe.room = Game.room_rt.topdown
		probe._build_room()
	var def: Dictionary = Game.room_rt.def
	var npcs: Array = def.get("objects", []).filter(func(o): return str(o.get("type", "")) == "npc")
	var things: Array = def.get("objects", []).filter(func(o): return not str(o.get("type", "")) in ["npc", "decor"])
	var figures := probe.sorted.get_children().filter(func(f): return f is TopdownPlaces.Figure and f.twin != null and not f.is_queued_for_deletion())
	var marks := probe.floor_layer.get_children().filter(func(m): return m is TopdownPlaces.WayMark and not m.is_queued_for_deletion())
	var shown: Array = npcs.filter(func(o): return Game.world.object_visible(c(), o))
	var ok: bool = probe.room == Game.room_rt.topdown and probe.npc_views.size() >= shown.size() and probe.object_views.size() == things.size() \
		and figures.size() >= shown.size() + things.size() and probe.portal_views.size() == (def.get("portals", []) as Array).size() \
		and marks.size() == probe.portal_views.size()
	if not ok: view_misses.append("%s: npcs %d/%d things %d/%d figures %d ways %d/%d marks %d" % [rid, probe.npc_views.size(), shown.size(),
		probe.object_views.size(), things.size(), figures.size(), probe.portal_views.size(), (def.get("portals", []) as Array).size(), marks.size()])

# ------------------------------------------------------------------ 2: the Serpent's Shallows
func _the_shallows() -> void:
	check(go("shallows") and room() == "dw_serpents_shallows" and Game.room_rt.topdown != null,
		"south across Bend Shore's ford into the Serpent's Shallows, on the grid (room %s)" % room())
	_take("the_riverbed_serpent")
	step(1.0)
	var king := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "riverbed_serpent")
	var grid: TopdownRoom = Game.room_rt.topdown
	var at: Vector2i = TopdownRoom.cell_of(king[0].plane) if king.size() == 1 else Vector2i(-1, -1)
	check(king.size() == 1 and grid.standable(at) and grid.paint_at(at.x, at.y) in ["h", "a"],
		"the Riverbed Serpent surfaces in the shallows, on the wading floor or a sandbar (cell %s, paint %s)" % [str(at), grid.paint_at(at.x, at.y)])
	check(_boss("riverbed_serpent") >= 1, "the Riverbed Serpent defeated in its shallows")
	_done("the_riverbed_serpent", "the serpent's core taken")
	_whole()
	check(go("east") and room() == "dw_bend_shore", "back up the river to Bend Shore by the Shallows' way east (room %s)" % room())

# ------------------------------------------------------------------ 3: the Drowned Shrine
func _the_shrine() -> void:
	_take("the_shrine_surfaces")
	check(go("shrine") and room() == "ds_flooded_gate", "down Bend Shore's steps into the Drowned Shrine's Flooded Gate (room %s)" % room())
	_done("the_shrine_surfaces", "the Flooded Gate reached")
	_take("lus_handwriting")
	check(go("east") and room() == "ds_hall_of_lanterns", "east through the gate to the Hall of Lanterns (room %s)" % room())
	var read := 0
	for o in Game.room_rt.def.get("objects", []):
		if str(o.id).begins_with("inscription_") and Game.world.object_visible(c(), o) and interact(str(o.id)).get("ok", false): read += 1
	check(read == 4, "Lu's four inscriptions read in the hall, its galleries climbed for two of them (%d)" % read)
	_done("lus_handwriting", "Lu's inscriptions found")
	_take("the_riverbreath_trial")
	check(go("east") and room() == "ds_scripture_well", "on to the Scripture Well (room %s)" % room())
	var began := interact("rite_riverbreath")
	step(4.0)
	var grid: TopdownRoom = Game.room_rt.topdown
	var risen := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "drowned_acolyte" and e.summoned)
	check(began.get("ok", false) and not risen.is_empty() and risen.all(func(e): return grid.standable(TopdownRoom.cell_of(e.plane)) and absf(e.altitude - grid.floor_at(e.plane)) < 1.0),
		"the stone ring's trial begins, its drowned rising on the grid's floor by the well (%s; %s)" % [str(began), str(risen.map(func(e): return TopdownRoom.cell_of(e.plane)))])
	var t0: float = Game.sim_time
	while not ("riverbreath_trial" in c().cultivator.events_passed) and Game.sim_time - t0 < 120.0:
		_whole()
		fight("drowned_acolyte", 1, 5.0)
		step(0.5)
	check("riverbreath_trial" in c().cultivator.events_passed, "the well held: the inheritance accepts you")
	_done("the_riverbreath_trial", "Lu's trial passed")
	# The flooded shaft down to the Drowned Grotto (Breath Control, a secret art: a test shortcut) and back up.
	if not "breath_control" in c().cultivator.secret_arts: c().cultivator.secret_arts.append("breath_control")
	check(go("grotto") and room() == "ds_drowned_grotto", "down the flooded shaft to the Drowned Grotto (room %s)" % room())
	check(interact("chest_grotto").get("ok", false), "the grotto's chest opened on its ledge")
	check(go("entry") and room() == "ds_scripture_well", "up the shaft to the Scripture Well (room %s)" % room())
	_take("the_drowned_abbot")
	check(go("east") and room() == "ds_abbots_sanctum", "east into the Abbot's Sanctum (room %s)" % room())
	var rung := 0
	for i in 4:
		if interact("small_bell_%d" % i).get("ok", false): rung += 1
	check(rung == 4, "the Abbot's four bells rung on their platforms (%d)" % rung)
	check(_boss("drowned_abbot") >= 1, "the Drowned Abbot defeated in his sanctum")
	_done("the_drowned_abbot", "the Abbot silenced")
	_whole()
	check(go("exit") and room() == "dw_bend_shore", "up the Sanctum's stair to Bend Shore (room %s)" % room())

# ------------------------------------------------------------------ 4: Whitewater Gorge
func _the_gorge() -> void:
	check(go("west") and room() == "wg_gorge_mouth", "west from Bend Shore into the Gorge Mouth (room %s)" % room())
	check(go("west") and room() == "wg_rapids_terraces", "up the gorge to the Rapids Terraces (room %s)" % room())
	Game.quest.apply_flag(c().id, WorldPortals.seen_flag("wg_rapids_terraces", "cave"))   # found behind the falls (a test shortcut)
	check(go("cave") and room() == "wg_waterfall_cave", "behind the waterfall into its cave (room %s)" % room())
	check(interact("chest_1").get("ok", false), "the cave's chest opened on the high ledge")
	check(go("entry") and room() == "wg_rapids_terraces", "out through the falls to the terraces (room %s)" % room())
	check(go("west") and room() == "wg_echo_cliffs", "on to the Echo Cliffs (room %s)" % room())
	var way: Dictionary = Game.room_rt.portal_def("west")
	var gs: Dictionary = Game.world.portal_state(c(), way)
	var gated: bool = gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn")
	check(gated != TopdownRoom.has_layout("cc_cliff_faces"), "the Echo Cliffs' way west to Crane Cliffs is closed by the prototype's gate while Crane Cliffs has no layout (%s)" % str(gs))

# ------------------------------------------------------------------ 1, over the ten rooms
func _the_rooms() -> void:
	var missed := ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room south and west of Bend Shore was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
