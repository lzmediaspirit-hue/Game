extends "res://tests/prologue_run.gd"
## topdown_sect_halls (E1's batch R3; docs/architecture/room_engine.md): the fourteen rooms the room engine laid out from
## the side view in its third batch, played on the height grid by a top-down character: the sects' insides (the Jade
## Alchemy Hall, both Libraries, both Retreat Rooms, both Cave Abodes) and the Cloud Sect's Herb Terraces; Stoneford's
## County Hall, Trial Tower and Beast Trial Grove; Stonewall Quarry's rim, lower pit and collapsed tunnel. Test
## shortcuts carry a new character past chapter 3 (its story done, the systems these rooms hold open, a sturdy body);
## from there it is played through the World authority:
##   1. each room is entered on the grid through its ways from its neighbours (no gate on the way), and every way of it
##      leads onto the grid and back; the top-down view builds it: a figure for every person and thing, a mark for
##      every way;
##   2. in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump over a gap) reaches every NPC, object,
##      herb, place and way from the room's spawn and from every way in;
##   3. the systems: every thing that opens a page (the libraries' shelves, the seclusion mats, the county's board and
##      relief box, the tower's stele) opens it from where a body stands by it; the places these rooms add (the Alchemy
##      Hall's furnace, the abodes' beds) open theirs from their user's cell;
##   4. the trials: a Trial Tower floor climbed on the grid, its foes standing on the arena's floor where auto-path
##      reaches them, and cleared; a guardian floor's guardian on the floor; the Grove's trial begun with a spirit beast,
##      its waves coming onto floor that auto-path reaches;
##   5. the quarry's lesson: Stone and Sweat leads to the Quarry Rim on the grid, its copper mined and its Rock Beetles
##      defeated there.
## Run headless:  godot --headless --path . res://tests/topdown_sect_halls.tscn [-- --verbose]

const ROOMS := ["ja_alchemy_hall", "ja_library", "ja_retreat", "ja_cave_abode", "cm_cloud_library", "cm_herb_terraces",
	"cm_retreat", "cm_cave_abode", "sf_county_hall", "sf_trial_tower", "sf_beast_grove", "sq_quarry_rim", "sq_lower_pit",
	"sq_collapsed_tunnel"]
const JADE := ["ja_alchemy_hall", "ja_library", "ja_retreat", "ja_cave_abode"]
const CLOUD := ["cm_cloud_library", "cm_herb_terraces", "cm_retreat", "cm_cave_abode"]
const TOWN := ["sf_county_hall", "sf_trial_tower", "sf_beast_grove", "sq_quarry_rim", "sq_lower_pit", "sq_collapsed_tunnel"]
const BEFORE := ["prologue", "main"]
## The systems these rooms' things wait on (a test shortcut: open, so each thing answers).
const SYSTEMS := ["alchemy", "herb_garden", "seclusion", "medicinal_bath", "qi_springs", "natural_treasures", "ancestral_rites",
	"mining", "spirit_animals", "retreat_room", "herb_gathering", "beast_snaring", "teleport_stones"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var page_misses: Array = []  # a thing that did not open its page
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("sect_halls/")
	_past_chapter3()
	GameEvents.event.connect(_on_room)
	_sect("jade_sect", JADE)
	_sect("cloud_sect", CLOUD)
	_town()
	_rooms()
	_places()
	_tower()
	_grove()
	_stone_and_sweat()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut past chapter 3
## The story to the end of chapter 3 done (the Entry Trial and the Mentor's Gift among it), the prologue's systems and
## scenes, the systems these rooms hold, Qi Kindling 7, a sturdy body (a test shortcut: the walk is about the rooms).
func _past_chapter3() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		if str(q.get("kind", "")) in BEFORE and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 3)):
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	for qid in ["entry_trial", "the_mentors_gift"]: c().quests.done[qid] = 1
	c().cultivator.realm_key = "qi_kindling_7"
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(cid)
	for s in SYSTEMS: Unlocks.force_unlock(cid, s)
	GameEvents.flush()
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 900.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 9000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 400.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "sf_fairground", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "sf_fairground" and Game.room_rt.topdown != null, "past chapter 3, on the Fairground on the grid (room %s)" % room())

func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp

# ------------------------------------------------------------------ 1: into each room, through its ways
## A disciple of `sect` walks into each of its rooms from the sect's grounds, and out through every way and back.
func _sect(sect: String, rooms: Array) -> void:
	c().training_sect = {"id": sect, "rank": "outer", "contribution": 0}
	GameEvents.flush()
	if room() != "sf_fairground": travel("sf_fairground")
	for rid in rooms:
		_whole()
		check(travel(rid) and Game.room_rt.topdown != null, "%s: walked in on the grid from the %s's grounds (room %s)" % [rid, sect, room()])
		_ways(rid)
	travel("sf_fairground")

## Stoneford's rooms and the quarry's: the County Hall from the gate, the tower from the Fairground, the grove from
## Market Street, the quarry up the Quarry Road, the tunnel once its hidden way has shown itself.
func _town() -> void:
	Game.quest.apply_flag(c().id, WorldPortals.seen_flag("sq_lower_pit", "tunnel"))
	for rid in TOWN:
		_whole()
		check(_enter(rid) and Game.room_rt.topdown != null, "%s: walked in on the grid (room %s)" % [rid, room()])
		_ways(rid)

## Into a room: through the rooms' ways (travel), or an instanced room (the tower, the grove: no route runs through
## one) by its way from the room before it.
const INSTANCED := {"sf_trial_tower": ["sf_fairground", "tower"], "sf_beast_grove": ["sf_market", "grove"]}
func _enter(rid: String) -> bool:
	if not INSTANCED.has(rid) or room() == rid: return travel(rid)
	return travel(str(INSTANCED[rid][0])) and go(str(INSTANCED[rid][1])) and room() == rid

## Every way of the room opens (no gate) onto a room on the grid, and its way back returns here.
func _ways(rid: String) -> void:
	if room() != rid: return
	var shut: Array = []
	for p in ContentDB.room(rid).get("portals", []):
		var to := str(p.get("to", ""))
		var gs: Dictionary = Game.world.portal_state(c(), Game.room_rt.portal_def(str(p.id)))
		if gs.get("gate", false) or not TopdownRoom.has_layout(to):
			shut.append("%s (gate)" % str(p.id))
			continue
		if not go(str(p.id)) or room() != to or Game.room_rt.topdown == null:
			shut.append("%s -> %s" % [str(p.id), room()])
			travel(rid)
			continue
		if not go(str(p.get("to_portal", ""))) or room() != rid: shut.append("%s back (%s)" % [str(p.id), room()])
		if room() != rid: travel(rid)
	check(shut.is_empty(), "%s: every way leads onto the grid, ungated, and back (%s)" % [rid, str(shut)])

# ------------------------------------------------------------------ 2, 3: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not rid in ROOMS or entered.has(rid): return
	entered[rid] = Game.room_rt.topdown != null
	if Game.room_rt.topdown == null: return
	_walks(rid)
	_view(rid)
	_pages(rid)

## 2: auto-path reaches every thing and way from the spawn and every way in.
func _walks(rid: String) -> void:
	var grid: TopdownRoom = Game.room_rt.topdown
	var def: Dictionary = Game.room_rt.def
	for s in _starts():
		var seen := {}
		for cell in TopdownRoute.reach(grid, s, true): seen[cell] = true
		for o in def.get("objects", []):
			if str(o.get("type", "")) == "decor" or not o.has("at"): continue
			if not _reached(grid, seen, Vector2(float(o.at[0]), float(o.at[1])), float(o.get("alt", 0.0))):
				walk_misses.append("%s: %s from %s" % [rid, str(o.id), str(s)])
		for w in def.get("portals", []):
			if not seen.has(TopdownRoom.cell_of(Vector2(float(w.at[0]), float(w.at[1])))): walk_misses.append("%s: way %s from %s" % [rid, str(w.id), str(s)])

## The cells a body comes into the loaded room at: its spawn and where each way sets it down.
func _starts() -> Array:
	var grid: TopdownRoom = Game.room_rt.topdown
	var out: Array = [TopdownRoom.cell_of(grid.spawn)]
	for w in Game.room_rt.def.get("portals", []):
		if w.has("arrive"): out.append(TopdownRoom.cell_of(Vector2(float(w.arrive[0]), float(w.arrive[1]))))
	return out

## A cell within three of `at`, at its height, that auto-path reaches (`seen`).
func _reached(grid: TopdownRoom, seen: Dictionary, at: Vector2, alt: float) -> bool:
	var c0 := TopdownRoom.cell_of(at)
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			var q := c0 + Vector2i(dx, dy)
			if dx * dx + dy * dy <= 9 and seen.has(q) and absf(grid.cell_floor(q) - alt) <= 48.0: return true
	return false

## 1: the character's own top-down view built on the room: a figure for every person and thing, a mark for every way.
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
		probe.build_room()
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

## 3: every thing of the room that opens a page opens it, from where a body stands by it on the grid.
func _pages(rid: String) -> void:
	var back: Vector2 = st.plane if st != null else Vector2.ZERO
	for o in Game.room_rt.def.get("objects", []):
		if not o.has("open_page") or not Game.world.object_visible(c(), o): continue
		var r := interact(str(o.id))
		if not r.get("ok", false) or str(r.get("open_page", "")) != str(o.open_page):
			page_misses.append("%s: %s (%s)" % [rid, str(o.id), str(r.get("open_page", r.get("text", r.get("reason", ""))))])
	place(back)

func _rooms() -> void:
	var missed := ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of the batch was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
	check(page_misses.is_empty() and entered.size() == ROOMS.size(),
		"every thing that opens a page (the shelves, the mats, the county's board and box, the tower's stele) opens it from beside it (%s)" % str(page_misses.slice(0, 4)))

# ------------------------------------------------------------------ 3: the places
## The places these rooms hold (the Alchemy Hall's furnace, the abodes' beds), each walked up to (its user's cell) as a
## disciple of its sect: the context button offers it, and it opens the page the table names.
func _places() -> void:
	var bad: Array = []
	var seen: Array = []
	for r in PlaceRules.all():
		if not str(r.room) in ROOMS: continue
		seen.append(str(r.id))
		c().training_sect = {"id": str(r.get("sect", "")) if str(r.get("sect", "")) != "" else "jade_sect", "rank": "outer", "contribution": 0}
		if not travel(str(r.room)):
			bad.append("%s: no way to %s" % [r.id, r.room])
			continue
		place(PlaceRules.stand_point(r))
		var ctx: Dictionary = Game.world.query_context(c())
		var res: Dictionary = Game.world.interact(c(), str(r.object))
		if str(ctx.get("object", "")) != str(r.object) or str(res.get("open_page", "")) != str(r.page):
			bad.append("%s: %s, %s" % [r.id, str(ctx.get("object", ctx.get("portal", ""))), str(res.get("open_page", res.get("text", "")))])
	check(bad.is_empty() and seen.has("ja_furnace") and seen.has("ja_abode_garden") and seen.has("cm_abode_garden"),
		"the places in these rooms (%s): walked up to, the context button offers each and it opens its page (%s)" % [str(seen), str(bad)])

# ------------------------------------------------------------------ 4: the trials
## Every living foe of the loaded room stands on a floor cell that auto-path reaches from every way in.
func _foes_on_floor() -> Array:
	var grid: TopdownRoom = Game.room_rt.topdown
	var off: Array = []
	var reach: Array = []
	for s in _starts():
		var seen := {}
		for cell in TopdownRoute.reach(grid, s, true): seen[cell] = true
		reach.append(seen)
	for e in Game.room_rt.living_enemies():
		if e.team == "ally": continue
		var cell := TopdownRoom.cell_of(e.plane)
		if not grid.standable(cell) or reach.any(func(seen): return not seen.has(cell)): off.append("%s at %s" % [e.def_id, str(cell)])
	return off

func _tower() -> void:
	c().training_sect = {"id": "jade_sect", "rank": "outer", "contribution": 0}
	travel("sf_fairground")
	c().tower = {}
	var r: Dictionary = Game.world.climb_tower(c(), 1)
	GameEvents.flush()
	var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.team != "ally")
	var off := _foes_on_floor()
	check(r.get("ok", false) and room() == "sf_trial_tower" and Game.room_rt.topdown != null and Game.room_rt.event.get("active", false) and foes.size() >= 2 and off.is_empty(),
		"the Trial Tower: floor 1 climbed on the grid, its %d foes on the arena's floor where auto-path reaches them (%s; %s)" % [foes.size(), str(r), str(off)])
	place(Game.room_rt.topdown.spawn)
	for e in foes:
		Game.combat.apply_execute(e, c().id)
		GameEvents.flush()
	check(Game.world.tower_cleared(c()) == 1 and not Game.room_rt.event.get("active", false), "every foe down: floor 1 is cleared on the grid")
	c().tower["cleared"] = 4
	travel("sf_fairground")
	r = Game.world.climb_tower(c(), 5)
	GameEvents.flush()
	var row: Dictionary = Game.world.tower_floor(5)
	var guardian: Array = Game.room_rt.living_enemies().filter(func(e): return e.def_id == str(row.get("guardian", "")))
	off = _foes_on_floor()
	check(r.get("ok", false) and str(row.get("kind", "")) == "guardian" and guardian.size() == 1 and off.is_empty(),
		"a guardian floor (5): its guardian %s and escorts stand on the floor where auto-path reaches them (%s)" % [str(row.get("guardian", "")), str(off)])
	Game.world.end_event(c(), Game.room_rt, true)
	GameEvents.flush()
	travel("sf_fairground")

func _grove() -> void:
	check(_enter("sf_beast_grove") and Game.room_rt.topdown != null, "to the Beast Trial Grove on the grid (room %s)" % room())
	Game.pets.apply_grant(c().id, "mist_wolf")
	var wolf: Dictionary = c().pets.back()
	wolf.level = 30
	c().active_pet = str(wolf.uid)
	Game.pets.spawn(c())
	c().cooldowns.erase("grove_day")
	var r: Dictionary = Game.world.start_beast_trial(c())
	var grid: TopdownRoom = Game.room_rt.topdown
	var bad: Array = []
	for w in Game.room_rt.event.get("waves", []):
		for p in w.get("points", []):
			var cell := TopdownRoom.cell_of(Vector2(float(p[0]), float(p[1])))
			if not grid.standable(cell): bad.append(str(cell))
	check(r.get("ok", false) and Game.room_rt.event.get("pet_trial", false) and bad.is_empty() and not (Game.room_rt.event.get("waves", []) as Array).is_empty(),
		"the Grove's trial begun on the grid with a spirit beast: its waves' points on the grove's floor (%s; %s)" % [str(r), str(bad)])
	place(grid.spawn)
	step(3.0)
	var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.team != "ally")
	var off := _foes_on_floor()
	check(not foes.is_empty() and off.is_empty(), "its first wave comes onto floor auto-path reaches (%d foes; %s)" % [foes.size(), str(off)])
	Game.world.end_event(c(), Game.room_rt, true)
	GameEvents.flush()

# ------------------------------------------------------------------ 5: the quarry's lesson
func _stone_and_sweat() -> void:
	Game.quest.apply_start(c().id, "stone_and_sweat")
	GameEvents.flush()
	var entry: Array = Game.quest.tracker(c()).filter(func(q): return str(q.get("quest", "")) == "stone_and_sweat")
	check(not entry.is_empty() and not entry[0].get("gate", false) and str(entry[0].get("target_room", "")) == "sq_quarry_rim",
		"Stone and Sweat leads to the Quarry Rim, inside the prototype now (%s)" % str(entry.slice(0, 1)))
	check(travel("sq_quarry_rim") and Game.room_rt.topdown != null, "up the Quarry Road to the rim on the grid (room %s)" % room())
	var got := 0
	var tries := 0
	while got < 5 and tries < 12:
		tries += 1
		var any := false
		for o in Game.room_rt.def.get("objects", []):
			if str(o.get("type", "")) != "ore_vein" or str(o.get("item", "")) != "copper_ore": continue
			if Game.room_rt.objects.get(str(o.id), {"state": "ready"}).get("state", "ready") != "ready": continue
			any = true
			var r := interact(str(o.id))
			if not r.get("ok", false): continue
			step(float(r.get("channel", 1.5)) + 0.1)
			var done := submit({"type": "complete_node", "object": str(o.id)})
			if done.get("ok", false): got += int(done.count)
		if not any: step(30.0)
	check(got >= 5, "five copper mined at the rim's face (%d)" % got)
	_whole()
	check(fight("rock_beetle", 5, 300.0) >= 5, "five Rock Beetles defeated in the yard")
	var q: Dictionary = c().quests.active.get("stone_and_sweat", {})
	var prog: Array = q.get("progress", [])
	check(prog.size() >= 2 and int(prog[0]) >= 5 and int(prog[1]) >= 5, "its copper and its beetles counted (%s)" % str(prog))
