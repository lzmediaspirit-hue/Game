extends "res://tests/prologue_run.gd"
## topdown_chapter3 (audit 45 §6.1, E1: the room engine's first rooms; docs/architecture/room_engine.md): chapter 3 of
## the story played on the height grid by a top-down character, through the six rooms the room engine laid out from
## the side view: the Caravan Road, the Mudwater Hideout (the Stockade, the Tunnels, the Loot Cave, Big Toad Tan's Boss
## Den) and Bend Shore. Test shortcuts carry a new character to chapter 3's door (the story before it done, the
## prologue's systems, Qi Kindling 6, and a sturdy body, so the fights are the rooms' and not the balance's). From
## there it is played through the World authority, as topdown_tutorial plays the chapters before it:
##   1. each room of the chapter is entered on the grid through its ways from the room before (no gate on the way), and
##      the top-down view builds it: a figure for every person and thing, a mark for every way;
##   2. in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump over a gap) reaches every NPC, object,
##      herb, place and way from the room's spawn and from every way in;
##   3. the story: Bandits on the Road from Guard Hou, ten Mudwater Bandits on the Caravan Road, handed in; The Caravan
##      Road from Elder Gu, six more and the Hideout's key; the Mudwater Hideout, its four rooms walked to Big Toad Tan
##      and handed in; Gu's Cargo, the cart escorted to Bend Shore; the tracker leading into these rooms on the way;
##   4. past chapter 3 the story's next quest (Toward Cleansing Peak, at the Pilgrim Stairs) is played past the
##      prototype's gate: the tracker's first entry is the prototype's end, and Bend Shore's ways west, to the Serpent's
##      Shallows and to the Drowned Shrine lead onto the grid (R2: tests/topdown_drowned_shrine.gd), none gated.
## Run headless:  godot --headless --path . res://tests/topdown_chapter3.tscn [-- --verbose]

const ROOMS := ["cr_caravan_road", "mh_stockade", "mh_tunnels", "mh_loot_cave", "mh_boss_den", "dw_bend_shore"]
const BEFORE := ["prologue", "main"]   # the story's kinds done before chapter 3 (a test shortcut)
const CHAPTER3 := ["bandits_on_the_road", "the_caravan_road", "mudwater_hideout", "gus_cargo"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("ch3/")
	_to_chapter3()
	GameEvents.event.connect(_on_room)
	_bandits()
	_the_caravan_road()
	_the_hideout()
	_gus_cargo()
	_the_rooms()
	_past_the_chapter()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to chapter 3
## The story before chapter 3 done (its prologue and main quests, The First Current the last), the prologue's systems
## and scenes, Qi Kindling 6, a sturdy body (a test shortcut: the walk is about the rooms), at Stoneford Gate.
func _to_chapter3() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		if str(q.get("kind", "")) in BEFORE and not str(q.id) in CHAPTER3 and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 3)):
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("qi_kindling_6")
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 900.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 9000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 400.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "sf_gate", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "sf_gate" and Game.room_rt.topdown != null and ProgressionRules.at_least(c().cultivator.realm_key, "qi_kindling_6"),
		"at chapter 3's door: Stoneford Gate on the grid, Qi Kindling 6 (room %s, realm %s)" % [room(), c().cultivator.realm_key])

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

# ------------------------------------------------------------------ 1, 2: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not rid in ROOMS or entered.has(rid): return
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
	# A person hidden at this hour (the peddler sets out his mat only after dark) has no figure while hidden.
	var shown: Array = npcs.filter(func(o): return Game.world.object_visible(c(), o))
	var ok: bool = probe.room == Game.room_rt.topdown and probe.npc_views.size() >= shown.size() and probe.object_views.size() == things.size() \
		and figures.size() >= shown.size() + things.size() and probe.portal_views.size() == (def.get("portals", []) as Array).size() \
		and marks.size() == probe.portal_views.size()
	if not ok: view_misses.append("%s: npcs %d/%d things %d/%d figures %d ways %d/%d marks %d" % [rid, probe.npc_views.size(), shown.size(),
		probe.object_views.size(), things.size(), figures.size(), probe.portal_views.size(), (def.get("portals", []) as Array).size(), marks.size()])

# ------------------------------------------------------------------ 3: the story
## The tracker's first entry leads to `target`, a room on the grid.
func _leads(quest: String, target: String) -> bool:
	var tr: Array = Game.quest.tracker(c())
	for e in tr:
		if str(e.get("quest", "")) == quest: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target)
	return false

func _bandits() -> void:
	accept("guard_hou", "bandits_on_the_road")
	check(_leads("bandits_on_the_road", "cr_caravan_road"), "Bandits on the Road leads to the Caravan Road, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 1)))
	check(travel("cr_caravan_road") and Game.room_rt.topdown != null, "to the Caravan Road on the grid, west from the Fairground (room %s)" % room())
	check(fight("mudwater_bandit", 10, 900.0) >= 10, "ten Mudwater Bandits defeated on the Caravan Road")
	_whole()
	check(travel("sf_gate"), "back to Guard Hou at Stoneford Gate (room %s)" % room())
	hand_in("guard_hou", "bandits_on_the_road")

func _the_caravan_road() -> void:
	_realm("qi_kindling_7")
	check(travel("sf_artisan_row"), "to Elder Gu on Artisan Row (room %s)" % room())
	accept("elder_gu", "the_caravan_road")
	check(travel("cr_caravan_road"), "back on the Caravan Road (room %s)" % room())
	check(fight("mudwater_bandit", 6, 600.0) >= 6, "six more Mudwater Bandits")
	var kt := 0
	while c().inventory.count("mudwater_key") < 1 and kt < 40:
		fight("mudwater_bandit", 1, 60.0)
		kt += 1
		_whole()
	check(c().inventory.count("mudwater_key") >= 1, "the Hideout's key drops (%d more fights)" % kt)
	check(travel("sf_artisan_row"), "back to Elder Gu (room %s)" % room())
	hand_in("elder_gu", "the_caravan_road")

func _the_hideout() -> void:
	check(travel("sf_gate"), "to Guard Hou for the Hideout (room %s)" % room())
	accept("guard_hou", "mudwater_hideout")
	check(travel("cr_caravan_road") and travel("mh_stockade"), "the key opens the Stockade's gate north of the road (room %s)" % room())
	var rooms: Array = [room()]
	for rid in ["mh_tunnels", "mh_loot_cave", "mh_boss_den"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["mh_stockade", "mh_tunnels", "mh_loot_cave", "mh_boss_den"], "the Hideout walked room by room to the Boss Den (%s)" % str(rooms))
	_whole()
	for e in Game.room_rt.living_enemies():
		if e.def_id == "big_toad_tan": e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.2)   # a test shortcut: the fight is the den's, not the balance's
	check(fight("big_toad_tan", 1, 300.0, 0.0, true) >= 1, "Big Toad Tan defeated in his den")
	_whole()
	check(go("exit") and room() == "cr_caravan_road", "out of the den by its way back to the Caravan Road (room %s)" % room())
	check(travel("sf_gate"), "back to Guard Hou (room %s)" % room())
	hand_in("guard_hou", "mudwater_hideout")

func _gus_cargo() -> void:
	check(travel("sf_artisan_row"), "to Elder Gu for his cargo (room %s)" % room())
	accept("elder_gu", "gus_cargo")
	check(_leads("gus_cargo", "dw_bend_shore") or _leads("gus_cargo", "cr_caravan_road"), "Gu's Cargo leads west, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 1)))
	check(travel("dw_bend_shore") and Game.room_rt.topdown != null, "the cart escorted to Bend Shore, on the grid (room %s)" % room())
	GameEvents.flush()
	if c().quests.is_active("gus_cargo"):
		check(travel("sf_artisan_row"), "back to Elder Gu (room %s)" % room())
		hand_in("elder_gu", "gus_cargo")
	check(c().quests.is_done("gus_cargo"), "Gu's Cargo done")

# ------------------------------------------------------------------ 1, 2: over the six rooms
func _the_rooms() -> void:
	var missed := ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of chapter 3 was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room of chapter 3 auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room of chapter 3: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))

# ------------------------------------------------------------------ 4: the prototype's end past chapter 3
func _past_the_chapter() -> void:
	var waiting: Array = Game.quest.story_waiting(c(), QuestAuthority.STORY_KINDS)
	check(not waiting.is_empty() and str(waiting[0].id) == "toward_cleansing_peak" and Game.quest.beyond_prototype(c(), waiting[0]),
		"past chapter 3 the story's next quest is Toward Cleansing Peak, past the prototype's gate (%s)" % str(waiting.slice(0, 1).map(func(q): return str(q.id))))
	# The lessons inside the prototype first (a test shortcut: done as they come, and those under way), then the
	# prototype's end.
	for i in 12:
		for q in c().quests.active.keys().duplicate():
			if str(Game.quest.quest_def(c(), str(q)).get("kind", "")) == "guided":
				c().quests.active.erase(q)
				c().quests.done[str(q)] = 1
		var nx := Game.quest.story_next(c())
		if nx.get("gate", false) or nx.is_empty(): break
		c().quests.offered.erase(str(nx.get("quest", "")))
		c().quests.done[str(nx.get("quest", ""))] = 1
		GameEvents.flush()
	var tr: Array = Game.quest.tracker(c())
	var head: Dictionary = tr[0] if not tr.is_empty() else {}
	check(head.get("gate", false) and str(head.get("name", "")) == Tx.t("sim.quest.tale_rests") and str(head.get("target_room", "x")) == "",
		"then the tracker's first entry is the prototype's end, leading nowhere (%s)" % str(head))
	check(travel("dw_bend_shore"), "at Bend Shore (room %s)" % room())
	var gated: Array = []
	for pid in ["west", "shallows", "shrine"]:
		var way: Dictionary = Game.room_rt.portal_def(pid)
		var gs: Dictionary = Game.world.portal_state(c(), way)
		if gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn"): gated.append(pid)
	check(gated.is_empty(), "Bend Shore's ways west, to the Serpent's Shallows and to the Drowned Shrine lead onto the grid (R2), none closed by the prototype's gate (%s)" % str(gated))
