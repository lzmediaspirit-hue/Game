extends "res://tests/prologue_run.gd"
## topdown_peaks (R4, the room engine's peaks; docs/architecture/room_engine.md): the peaks played on the height grid by
## a top-down character, through the eleven rooms the room engine laid out from the side view: the Crane Cliffs (the
## Cliff Faces, the Sky Ledges), Mist Peak (the Misty Slopes, the Forgotten Monastery, the Ascension Gate), Summit Ridge
## (the Windswept Ridge, the Frozen Shrine), the Hidden Vale (the Vale Gate, the Sect Grounds, the Back Mountain) and the
## Hidden Grotto. Test shortcuts carry a new character to the peaks (the story before chapter 10 done, Heaven Glimpse 3,
## a sturdy body, so the fights are the rooms' and not the balance's) and set it down on the Cliff Faces, as if up from
## the Echo Cliffs. From there it is played through the World authority, as topdown_chapter3 plays chapter 3:
##   1. each room is entered on the grid, the climb through its ways from the room before (no gate on the way), and the
##      top-down view builds it: a figure for every person and thing, a mark for every way;
##   2. in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump over a gap) reaches every NPC, object,
##      herb, place and way from the room's spawn and from every way in;
##   3. the story on the peaks: Above the Mist's five Stormwing Hawks on the Sky Ledges; A Wider Sky's meditation by
##      the heaven insight stone in the Forgotten Monastery, its hidden stair shown by Spirit Sense and taken; Beyond the
##      Valley to the Frozen Shrine, Lu's journal page there; The Ascension Gate's Gate Guardian on the summit arena,
##      Act I's end, and the way up to the Azure Expanse closed by the prototype's gate while it has no layout;
##   4. the Hidden Vale: its teleport stone sets a body down on the grid; a sect founded, the Sect Grounds' raid comes
##      in on the grid's floor; the Back Mountain opened by the sect's level; the Hidden Grotto's rope back up to Crane
##      Falls.
## Run headless:  godot --headless --path . res://tests/topdown_peaks.tscn [-- --verbose]

const CLIMB := ["cc_cliff_faces", "cc_sky_ledges", "mp_misty_slopes", "mp_forgotten_monastery", "sr_windswept_ridge", "sr_frozen_shrine",
	"mp_ascension_gate"]
const VALE := ["hv_vale_gate", "hv_sect_grounds", "hv_back_mountain", "hg_hidden_grotto"]
const PEAKS := ["above_the_mist", "a_wider_sky", "beyond_the_valley", "the_ascension_gate", "farewells"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("peaks/")
	_to_the_peaks()
	_the_climb()
	_the_gate()
	_the_vale()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to the peaks
## The story before chapter 10 done (its prologue and main quests, the lessons), the prologue's systems and scenes,
## Heaven Glimpse 3 with Spirit Sense and a sturdy body (a test shortcut: the walk is about the rooms), on the Cliff
## Faces' east way.
func _to_the_peaks() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	c().quests.flags["night_survived"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c().training_sect = {"id": "jade_sect", "rank": "core_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		var kind := str(q.get("kind", ""))
		if str(q.id) in PEAKS: continue
		if (kind in ["prologue", "main"] and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 9))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("heaven_glimpse_3")
	for u in ["spirit_sense", "hidden_portals", "teleport_stones", "your_sect"]: Unlocks.force_unlock(cid, u)
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 60000.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 900000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 30000.0, "source": "test:sturdy"}])
	_whole()
	GameEvents.event.connect(_on_room)
	Game.world.load_room(c(), "cc_cliff_faces", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "cc_cliff_faces" and Game.room_rt.topdown != null and ProgressionRules.at_least(c().cultivator.realm_key, "heaven_glimpse_3"),
		"at the peaks' door: the Cliff Faces on the grid, Heaven Glimpse 3 (room %s, realm %s)" % [room(), c().cultivator.realm_key])

## A realm set outright (a test shortcut), its unlocks and offers evaluated.
func _realm(key: String) -> void:
	c().cultivator.realm_key = key
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(c().id)
	GameEvents.flush()
	_whole()

## Stats rebuilt (the sturdy body's modifiers among them) and the body whole again between the fights.
func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp
	Game.combat.wounded.erase(c().id)

# ------------------------------------------------------------------ 1, 2: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not (rid in CLIMB or rid in VALE) or entered.has(rid): return
	entered[rid] = Game.room_rt.topdown != null
	if Game.room_rt.topdown == null: return
	_walks(rid)
	_view(rid)

## 2: auto-path reaches every thing and way from the spawn and every way in.
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
			var at := Vector2(float(o.at[0]), float(o.at[1]))
			var c0 := TopdownRoom.cell_of(at)
			var alt := float(o.get("alt", 0.0))
			var ok := false
			for dy in range(-3, 4):
				for dx in range(-3, 4):
					var q := c0 + Vector2i(dx, dy)
					if dx * dx + dy * dy <= 9 and seen.has(q) and absf(grid.cell_floor(q) - alt) <= 48.0: ok = true
			if not ok: walk_misses.append("%s: %s from %s" % [rid, str(o.id), str(s)])
		for w in def.get("portals", []):
			if not seen.has(TopdownRoom.cell_of(Vector2(float(w.at[0]), float(w.at[1])))): walk_misses.append("%s: way %s from %s" % [rid, str(w.id), str(s)])

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

# ------------------------------------------------------------------ 3: the story on the peaks
## A quest's steps done, waiting to be handed in (or done on its own).
func _steps_done(q: String) -> bool:
	return c().quests.is_done(q) or str(c().quests.active.get(q, {}).get("state", "")) == "ready"

## The tracker's entry for `quest` leads to `target`, a room on the grid.
func _leads(quest: String, target: String) -> bool:
	for e in Game.quest.tracker(c()):
		if str(e.get("quest", "")) == quest: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target) and not e.get("gate", false)
	return false

## Is the way `pid` of this room closed by the prototype's gate (its line said), and is that because its room has no
## layout yet?
func _gated(pid: String) -> bool:
	var gs: Dictionary = Game.world.portal_state(c(), Game.room_rt.portal_def(pid))
	return gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn")

func _the_climb() -> void:
	# Above the Mist: the Sky Ledges' hawks.
	Game.quest.apply_start(c().id, "above_the_mist")
	GameEvents.flush()
	check(_leads("above_the_mist", "cc_sky_ledges"), "Above the Mist leads to the Sky Ledges, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	check(travel("cc_sky_ledges") and Game.room_rt.topdown != null, "west along the Cliff Faces to the Sky Ledges, on the grid (room %s)" % room())
	var hawks := 0
	for i in 12:
		if hawks >= 5: break
		_whole()
		hawks += fight("stormwing_hawk", 1, 90.0)
	check(hawks >= 5 and _steps_done("above_the_mist"), "five Stormwing Hawks defeated on the Sky Ledges (%d; Above the Mist %s)" % [hawks, str(c().quests.active.get("above_the_mist", {}))])
	# Up the mountain: the Misty Slopes and the Forgotten Monastery (Spirit Awakening opened the way west), A Wider Sky
	# under way.
	Game.quest.apply_start(c().id, "a_wider_sky")
	GameEvents.flush()
	check(_leads("a_wider_sky", "mp_forgotten_monastery"), "A Wider Sky leads to the Forgotten Monastery, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	var rooms: Array = [room()]
	for rid in ["mp_misty_slopes", "mp_forgotten_monastery"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["cc_sky_ledges", "mp_misty_slopes", "mp_forgotten_monastery"], "up through the Misty Slopes to the Forgotten Monastery, room by room on the grid (%s)" % str(rooms))
	# A Wider Sky: meditate by the heaven insight stone.
	var stone: Dictionary = Game.room_rt.object_def("heaven_insight")
	stand_by(stone, Vector2(-30, 10), 0.0)
	Game.room_rt.enemies.clear()   # a test shortcut: the monastery's lanterns and sentinels are not the point here
	var guard := 0
	while (Game.combat.is_stunned(c().id) or Game.combat.is_busy(c().id)) and guard < 60:
		guard += 1
		step(0.1)
	var med := submit({"type": "start_meditation"})
	step(123.0)
	submit({"type": "stop_meditation"})
	GameEvents.flush()
	check(_steps_done("a_wider_sky"), "A Wider Sky: meditated by the heaven insight stone in the monastery's garden (%s; %s)" % [str(c().quests.active.get("a_wider_sky", {})), str(med)])
	# The hidden stair: Spirit Sense shows the cellar door in the west wing's retaining wall, and it is taken.
	var cellar: Dictionary = Game.room_rt.portal_def("hidden_cellar")
	place(Vector2(float(cellar.arrive[0]), float(cellar.arrive[1])))
	c().pools.max_soul = maxf(c().pools.max_soul, 100.0)
	c().pools.soul = c().pools.max_soul
	var pulse := submit({"type": "sense_pulse"})
	check(c().quests.has_flag(WorldPortals.seen_flag("mp_forgotten_monastery", "hidden_cellar")), "Spirit Sense shows the hidden cellar's door in the monastery's retaining wall (%s)" % str(pulse))
	var stair: Dictionary = Game.room_rt.portal_def("hidden_stair")
	var through := go("hidden_cellar")
	check(through and room() == "mp_forgotten_monastery" and st.plane.distance_to(Vector2(float(stair.at[0]), float(stair.at[1]))) <= 3.0 * TopdownRoom.TILE,
		"down the hidden cellar and up the hidden stair by the hall, on the grid (room %s, at %s)" % [room(), str(st.plane)])
	# Over the Windswept Ridge (Heaven Glimpse opened the monastery's west gate) to the Frozen Shrine: Beyond the Valley.
	Game.quest.apply_start(c().id, "beyond_the_valley")
	GameEvents.flush()
	check(_leads("beyond_the_valley", "sr_frozen_shrine"), "Beyond the Valley leads to the Frozen Shrine, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	rooms = [room()]
	for rid in ["sr_windswept_ridge", "sr_frozen_shrine"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["mp_forgotten_monastery", "sr_windswept_ridge", "sr_frozen_shrine"], "over the Windswept Ridge to the Frozen Shrine, on the grid (%s)" % str(rooms))
	GameEvents.flush()
	check(_steps_done("beyond_the_valley"), "Beyond the Valley: Lu's map followed to the Frozen Shrine (%s)" % str(c().quests.active.get("beyond_the_valley", {})))
	var before: int = c().inventory.count("lu_journal_page")
	var page := interact("journal_frozen")
	check(page.get("ok", false) and c().inventory.count("lu_journal_page") > before, "Lu's journal page taken at the trail's edge by the Frozen Shrine (%s)" % str(page))

func _the_gate() -> void:
	# The Ascension Gate: the Gate Guardian waits on the summit's arena while the quest is under way.
	c().quests.done["farewells"] = 1
	Game.quest.apply_start(c().id, "the_ascension_gate")
	GameEvents.flush()
	_whole()
	check(travel("mp_ascension_gate") and Game.room_rt.topdown != null, "west from the Frozen Shrine to the Ascension Gate, on the grid (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var boss: Array = []
	for i in 20:
		boss = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "gate_guardian")
		if not boss.is_empty(): break
		step(0.5)
	check(boss.size() == 1 and grid.standable(TopdownRoom.cell_of(boss[0].plane)), "the Gate Guardian stands on the arena's floor, on the grid (%s)" % str(boss.map(func(e): return e.plane)))
	for e in boss: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.2)   # a test shortcut: the fight is the arena's, not the balance's
	check(fight("gate_guardian", 1, 300.0, 0.0, true) >= 1, "the Gate Guardian defeated on the summit's arena")
	GameEvents.flush()
	check(c().quests.is_done("the_ascension_gate"), "Act I complete on the grid: the Ascension Gate")
	check(_gated("ascend") == not TopdownRoom.has_layout("ae_landing"),
		"the way up through the cliff to the Azure Expanse is closed by the prototype's gate exactly while Cloudgate Port has no layout")

# ------------------------------------------------------------------ 4: the Hidden Vale and the Grotto
func _the_vale() -> void:
	# The Hidden Vale's teleport stone sets a body down on the grid, in front of the stone.
	Game.account.teleports["hidden_vale"] = true
	Game.inventory.apply_add(c().id, "spirit_stone_shard", 50, "peaks_suite")
	var tp := submit({"type": "teleport", "stone": "hidden_vale"})
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(tp.get("ok", false) and room() == "hv_vale_gate" and Game.room_rt.topdown != null and Game.room_rt.topdown.standable(TopdownRoom.cell_of(st.plane)),
		"the Hidden Vale's teleport stone sets a body down on the Vale Gate's grid (%s; room %s)" % [str(tp), room()])
	check(_gated("path") == not TopdownRoom.has_layout("cf_falls_pool"), "the Vale Gate's road west to Crane Falls is gated exactly while the Falls Pool has no layout")
	# A sect founded and grown (a test shortcut), its raid on the Sect Grounds comes in on the grid's floor.
	var made := submit({"type": "found_sect", "name": "Peak Test Sect", "emblem": [0, 0]})
	Game.account.sect["level"] = 6
	Game.account.sect["next_defence_utc"] = 0.0
	check(made.get("ok", false) and travel("hv_sect_grounds") and Game.room_rt.topdown != null, "east into the Sect Grounds, on the grid (%s; room %s)" % [str(made), room()])
	var raid := submit({"type": "start_defence"})
	var grid: TopdownRoom = Game.room_rt.topdown
	var raiders := {}
	for i in 40:
		step(0.5)
		for e in Game.room_rt.living_enemies(): raiders[e.uid] = e
		if raiders.size() >= 3: break
	var astray: Array = raiders.values().filter(func(e): return not grid.standable(TopdownRoom.cell_of(e.spawn_point)))
	check(raid.get("ok", false) and not raiders.is_empty() and astray.is_empty(),
		"the sect's raid comes in on the Sect Grounds' floor, every raider inside the room (%d; astray %s; %s)" % [raiders.size(), str(astray.map(func(e): return e.spawn_point)), str(raid)])
	Game.room_rt.event.active = false   # a test shortcut: the raid's fight is the defence's, not the rooms'
	Game.room_rt.enemies.clear()
	GameEvents.flush()
	_whole()
	check(travel("hv_back_mountain") and Game.room_rt.topdown != null, "the sect's level opens the Back Mountain, on the grid (room %s)" % room())
	# The Hidden Grotto: a fortune's fall (a test shortcut), and its rope back up to Crane Falls.
	Game.world.load_room(c(), "hg_hidden_grotto", "")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "hg_hidden_grotto" and Game.room_rt.topdown != null, "in the Hidden Grotto, on the grid (room %s)" % room())
	if TopdownRoom.has_layout("cf_behind_falls"):
		check(go("way_up") and room() == "cf_behind_falls" and Game.room_rt.topdown != null, "up the rope out of the grotto to behind Crane Falls, on the grid (room %s)" % room())
	else:
		check(_gated("way_up"), "the grotto's rope up to Crane Falls is gated while Behind the Falls has no layout")

# ------------------------------------------------------------------ 1, 2: over the rooms
func _the_rooms() -> void:
	var missed := (CLIMB + VALE).filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of the peaks was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room of the peaks auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room of the peaks: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
