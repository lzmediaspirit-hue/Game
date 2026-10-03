extends "res://tests/prologue_run.gd"
## topdown_story_rooms (R5; docs/architecture/room_engine.md, "The story's rooms and the Tidebreak Front (R5)"): the ten
## rooms the room engine laid out from the side view for the story's own events and the Tidebreak Front, played on the
## height grid by a top-down character. Test shortcuts carry a new character along the story to each event with the
## story before it done, at the realm the event asks, with a sturdy body (the fights are the rooms', not the balance's);
## quests are taken and handed in where they stand (their givers are often far off). A room the grid does not reach yet
## (the Alliance Gate, the Trial Hall, the Citadel) is skipped by loading the room after it. Played through the World
## authority:
##   1. each room is entered on the grid, and the top-down view builds it (a figure for every person and thing, a mark
##      for every way); in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump) reaches every NPC,
##      object and way from the spawn and every way in;
##   2. the Trial of Reflections (The Heart Trial): the circle on Elder Hu's peak, the Reflection standing on the
##      arena's floor at its own cell, defeated; back to the peak;
##   3. Gu's Warehouse (Gu's Warehouse): in through the trade house's door from Artisan Row, the strongbox on the
##      strongroom's dais opened, Elder Gu defeated at his office for the ledger; out again;
##   4. the Siege of Two Sects (The Siege): the war gong on Gate Street; the Behemoth and the boarlets come out of the
##      grey north of the wall, on the grid's floor at the room's own cells; the wall held; back to Gate Street;
##   5. the Sect War (The Gate Holds): the pirates and the turncoats come down the junk's gangways at their cells, Comet
##      Captain Rao drops at his, and falls; the way back to the Alliance Gate is gated while it has no layout;
##   6. the Presence Trial: the phantoms at the court's west, east and south, the ninth Presence before the ninth seat;
##      borne to the end;
##   7. the Tidebreak Bastion (The Tide Breaks): its bell rung; on the wall's terrace the great lantern stands on its
##      dais, the Tide comes at both ends, a Warden beside the lantern relights it, the foes near it drain it; held to
##      the end, and back to the Bastion;
##   8. the grey fields: east through the Greyfall Breach and the Hollow Wake (Lu's journal page taken) to the Drone Hive
##      (its chest on the hive mound's crown; its way east gated while the Nebula Deep has no layout), and back to the
##      Breach for Greyfall: Shen Lian in the breach, its bell rung, the stand's waves out of the grey north of the wall
##      on the room's own cells (TopdownRoom.grid_event), held.
## Run headless:  godot --headless --path . res://tests/topdown_story_rooms.tscn [-- --verbose]

const ROOMS := ["si_trial_of_reflections", "si_gus_warehouse", "si_siege", "si_sect_war", "si_presence_trial", "tf_tidebreak_bastion",
	"si_tide_battle", "tf_greyfall_breach", "tf_hollow_wake", "tf_drone_hive"]
const TESTED := ["the_heart_trial", "gus_warehouse", "the_rift", "the_siege", "the_gate_holds", "the_presence_trial", "the_tide_breaks",
	"greyfall"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("r5/")
	_story_to(6)
	GameEvents.event.connect(_on_room)
	_reflections()
	_warehouse()
	_siege()
	_sect_war()
	_presence()
	_tide()
	_grey_fields()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcuts
## The story's prologue and main quests before chapter `upto` done (but the ones this suite plays), the prologue's
## systems and scenes, the sturdy body; the field bosses unlocked.
func _story_to(upto: int) -> void:
	var cid: String = c().id
	if upto <= 6:
		Unlocks.grant_prologue(cid)
		c().quests.flags["prologue_done"] = true
		for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		if str(q.get("kind", "")) in ["prologue", "main"] and not str(q.id) in TESTED and not c().quests.is_done(str(q.id)) \
				and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) < upto)):
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(cid)
	Unlocks.force_unlock(cid, "field_bosses")
	GameEvents.flush()
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 9000.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 400000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 9000.0, "source": "test:sturdy"}])
	_whole()

## The realm an event asks (a test shortcut).
func _realm(key: String) -> void:
	c().cultivator.realm_key = key
	Unlocks.evaluate(c().id)
	GameEvents.flush()
	_whole()

## Stats rebuilt (the sturdy body's modifiers among them) and the body whole again.
func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp
	Game.combat.wounded.erase(c().id)

## Into a room straight (a test shortcut: the way there is off the grid), standing where it sets a body down.
func _load(rid: String, portal := "") -> bool:
	Game.world.load_room(c(), rid, portal)
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	return room() == rid and Game.room_rt.topdown != null

## A quest taken where the character stands (a test shortcut: its giver is elsewhere).
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
func _boss(def_id: String, limit := 300.0) -> int:
	_whole()
	for e in Game.room_rt.living_enemies():
		if e.def_id == def_id: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.1)
	return fight(def_id, 1, limit, 0.0, true)

## The room's event held for `seconds`, the body kept whole each second (the fight is the balance's; the room's spawns
## are what is tested).
func _hold(seconds: float) -> void:
	var t := 0.0
	while t < seconds and Game.room_rt.event.get("active", false):
		_whole()
		step(1.0)
		t += 1.0

## The event's clock run down (a test shortcut) and stepped to its end; true if it was won.
func _run_out(event: String) -> bool:
	if Game.room_rt.event.get("active", false): Game.room_rt.event.remaining = 1.0
	_hold(4.0)
	return event in c().cultivator.events_passed

## The cells of the loaded layout's event under `key` (waves: wave `i`'s), as cells.
func _event_cells(key: String, i := -1) -> Array:
	var ev: Dictionary = Game.room_rt.topdown.def.get("event", {})
	var raw: Array = ev.get(key, [])
	if i >= 0: raw = raw[i] if i < raw.size() else []
	return raw.map(func(q): return TopdownRoom.cell_of(TopdownRoom.cell_point(q)))

## The event's foes of `def_id` spawned so far: each where it spawned on a cell a body stands on, at the grid's floor,
## within a cell of one of `cells`. Returns [count, all ok, their spawn cells].
func _spawned_at(def_id: String, cells: Array) -> Array:
	var grid: TopdownRoom = Game.room_rt.topdown
	var foes := Game.room_rt.living_enemies().filter(func(e): return e.def_id == def_id and e.summoned)
	var at: Array = foes.map(func(e): return TopdownRoom.cell_of(e.spawn_point))
	var ok := not foes.is_empty()
	for k in foes.size():
		var c0: Vector2i = at[k]
		ok = ok and grid.standable(c0) and cells.any(func(q): return absi(q.x - c0.x) <= 1 and absi(q.y - c0.y) <= 1)
	return [foes.size(), ok, at]

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

## Is the way `pid` of the loaded room closed by the prototype's gate?
func _gated(pid: String) -> bool:
	var gs: Dictionary = Game.world.portal_state(c(), Game.room_rt.portal_def(pid))
	return gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn")

# ------------------------------------------------------------------ 2: the Trial of Reflections
func _reflections() -> void:
	_realm("heart_tempering_9")
	check(_load("ja_elder_hu_peak"), "on Elder Hu's peak on the grid, Heart Tempering 9 (room %s)" % room())
	_take("the_heart_trial")
	var began := interact("rite_reflection")
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(began.get("ok", false) and room() == "si_trial_of_reflections" and Game.room_rt.topdown != null,
		"the circle on the peak opens the Trial of Reflections, on the grid (%s; room %s)" % [str(began), room()])
	var got := _spawned_at("the_reflection", _event_cells("fixed"))
	check(got[0] == 1 and got[1], "the Reflection stands on the arena's floor at its own cell, across from the way in (%s)" % str(got))
	check(_boss("the_reflection") >= 1 and "heart_trial" in c().cultivator.events_passed, "the Reflection defeated in its mirrored arena: the Heart Trial passed")
	_done("the_heart_trial", "the trial won")
	_whole()
	check(go("exit") and room() == "ja_elder_hu_peak", "out of the trial to Elder Hu's peak (room %s)" % room())

# ------------------------------------------------------------------ 3: Gu's Warehouse
func _warehouse() -> void:
	_story_to(8)
	_realm("spirit_awakening_8")
	check(_load("sf_artisan_row"), "on Artisan Row on the grid (room %s)" % room())
	_take("gus_warehouse")
	check(go("warehouse_door") and room() == "si_gus_warehouse", "through the trade house's door into Gu's Warehouse, on the grid (room %s)" % room())
	var vault := interact("gus_vault")
	var alt := float(Game.room_rt.object_def("gus_vault").get("alt", 0.0))
	check(vault.get("ok", false) and alt >= 3.0 * TopdownRoom.LEVEL - 1.0, "Gu's strongbox opened on the strongroom's dais up the east loft (alt %.0f; %s)" % [alt, str(vault)])
	step(1.0)
	var gu := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "elder_gu")
	check(gu.size() == 1 and TopdownRoom.cell_of(gu[0].spawn_point).x >= 32, "Elder Gu waits at his office in the east (%s)" % str(gu.map(func(e): return TopdownRoom.cell_of(e.spawn_point))))
	# Gu cannot be beaten here: he holds his ground, calls his hired blades, and flees through a Tide rift, the ledger
	# dropped as he goes.
	_whole()
	fight("elder_gu", 1, 75.0, 0.0, true)
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	GameEvents.flush()
	check(Game.room_rt.living_enemies().all(func(e): return e.def_id != "elder_gu") and c().inventory.count("smuggler_ledger") >= 1,
		"Elder Gu held off in his warehouse until he fled, his ledger taken")
	_done("gus_warehouse", "the warehouse raided")
	_whole()
	check(go("entry") and room() == "sf_artisan_row", "out through the door to Artisan Row (room %s)" % room())

# ------------------------------------------------------------------ 4: the Siege of Two Sects
func _siege() -> void:
	_story_to(9)
	_realm("heaven_glimpse_2")
	check(_load("ja_gate_street"), "on Gate Street on the grid (room %s)" % room())
	_take("the_siege")
	var began := interact("siege_gong_ja")
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(began.get("ok", false) and room() == "si_siege" and Game.room_rt.topdown != null, "the war gong opens the Siege of Two Sects, on the grid (%s; room %s)" % [str(began), room()])
	var wall_row := 12
	var beast := _spawned_at("hollow_behemoth", _event_cells("fixed"))
	check(beast[0] == 1 and beast[1] and beast[2][0].y < wall_row, "the Hollow Behemoth stands on the road in the grey north of the wall (%s)" % str(beast))
	_hold(8.0)
	var boars := _spawned_at("hollowed_boarlet", _event_cells("wave"))
	check(boars[0] >= 2 and boars[1] and boars[2].all(func(q): return q.y < wall_row), "the boarlets come in waves out of the grey north of the wall, at the room's cells (%s)" % str(boars))
	check(_run_out("siege_of_two_sects"), "the wall held to the end: the siege survived")
	_done("the_siege", "the siege survived")
	_whole()
	check(go("exit") and room() == "ja_gate_street", "back down the road to Gate Street (room %s)" % room())

# ------------------------------------------------------------------ 5: the Sect War
func _sect_war() -> void:
	_story_to(15)
	_realm("sage_sovereign_2")
	_take("the_gate_holds")
	var began := Game.quest.start_set_piece(c(), "sect_war")   # the war gong is at the Alliance Gate, off the grid
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(began.get("ok", false) and room() == "si_sect_war" and Game.room_rt.topdown != null, "the Sect War at the Alliance Gate, on the grid (%s; room %s)" % [str(began), room()])
	_hold(14.0)
	var pirates := _spawned_at("starsea_pirate", _event_cells("waves", 0))
	var turncoats := _spawned_at("nine_peaks_disciple", _event_cells("waves", 1))
	check(pirates[1] and turncoats[1], "the pirates and the turncoat disciples come down the junk's gangways at the room's cells (%s; %s)" % [str(pirates), str(turncoats)])
	_hold(30.0)
	var rao := _spawned_at("pirate_captain", _event_cells("timed"))
	check(rao[0] == 1 and rao[1], "Comet Captain Rao drops from the junk's rail at his cell (%s)" % str(rao))
	check(_boss("pirate_captain") >= 1 and "sect_war" in c().cultivator.events_passed, "the captain falls: the Gate holds")
	Game.quest.apply_flag(c().id, "ledger_burned")   # the Black Ledger's choice is Elder Zhong's, at the Gate
	_done("the_gate_holds", "the Gate held")
	_whole()
	check(_gated("exit") == not TopdownRoom.has_layout("np_alliance_gate"),
		"the way back to the Alliance Gate is closed by the prototype's gate while the Gate has no layout")

# ------------------------------------------------------------------ 6: the Presence Trial
func _presence() -> void:
	_story_to(16)
	_realm("sage_sovereign_3")
	_take("the_presence_trial")
	var began := Game.quest.start_set_piece(c(), "presence_trial")   # its circle is in the Trial Hall, off the grid
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(began.get("ok", false) and room() == "si_presence_trial" and Game.room_rt.topdown != null, "the Presence Trial's court, on the grid (%s; room %s)" % [str(began), room()])
	_hold(16.0)
	var phantoms := _spawned_at("presence_phantom", _event_cells("waves", 0))
	check(phantoms[0] >= 1 and phantoms[1], "the phantoms come at the court's west, east and south cells (%s)" % str(phantoms))
	_hold(32.0)
	var ninth := _spawned_at("ninth_presence", _event_cells("timed"))
	var seat: Vector2i = _event_cells("timed")[0]
	check(ninth[0] == 1 and ninth[1] and seat.y <= 9, "the ninth Presence rises before the ninth seat (%s)" % str(ninth))
	check(_run_out("presence_trial") and c().quests.has_flag("presence_trial_passed"), "the Presence of the eight borne to the end: the trial passed")
	_done("the_presence_trial", "the trial passed")
	_whole()

# ------------------------------------------------------------------ 7: the Tidebreak Bastion and the Tide battle
func _tide() -> void:
	_story_to(21)
	_realm("sphere_lord_1")
	_take("the_tide_breaks")
	check(_load("tf_tidebreak_bastion"), "at the Tidebreak Bastion on the grid (room %s)" % room())
	check(_gated("skiff") == not TopdownRoom.has_layout("wc_citadel_gate"), "the skiff to the Citadel is closed by the prototype's gate while the Citadel has no layout")
	var began := interact("tide_horn")
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(began.get("ok", false) and room() == "si_tide_battle" and Game.room_rt.topdown != null, "the Bastion's bell rung: the Tide battle on the wall's terrace, on the grid (%s; room %s)" % [str(began), room()])
	var lamp: Dictionary = Game.room_rt.object_def("great_lantern")
	var grid: TopdownRoom = Game.room_rt.topdown
	var lamp_at := Vector2(float(lamp.at[0]), float(lamp.at[1]))
	check(float(lamp.get("alt", 0.0)) >= TopdownRoom.LEVEL - 1.0, "the great lantern burns on its dais against the wall (alt %.0f)" % float(lamp.get("alt", 0.0)))
	_hold(24.0)
	var drones := _spawned_at("hollow_drone", _event_cells("waves", 0))
	var west: bool = drones[2].any(func(q): return q.x < 10)
	var east: bool = drones[2].any(func(q): return q.x > grid.w - 10)
	check(drones[1] and (west or east), "the drones come at the terrace's ends, at the room's cells (%s)" % str(drones))
	# The lantern: every foe near it drains it; a Warden beside it, not striking, with no foe near, relights it.
	for e in Game.room_rt.living_enemies(): Game.enemies.release(e)
	Game.room_rt.event.light = 50.0
	place(grid.spot_near(lamp_at, float(lamp.get("alt", 0.0)), lamp_at + Vector2(0, 40)), float(lamp.get("alt", 0.0)))
	step(2.0)
	var lit := float(Game.room_rt.event.get("light", 0.0))
	check(lit > 50.0 and st.plane.distance_to(lamp_at) <= 120.0, "standing beside the lantern on its dais with no foe near relights it (light %.1f, %.0f from it)" % [lit, st.plane.distance_to(lamp_at)])
	var near := Game.enemies.spawn_at("hollow_drone", grid.nearest_standable(lamp_at + Vector2(64, 96)), 92)
	place(grid.nearest_standable(lamp_at + Vector2(-400, 200)))
	Game.room_rt.event.light = 50.0
	step(1.0)
	var dim := float(Game.room_rt.event.get("light", 100.0))
	check(near != null and dim < 50.0, "a foe beside the lantern drains it (light %.1f)" % dim)
	check(_run_out("hollow_tide_battle"), "the lantern kept lit to the end: the Tide breaks")
	_done("the_tide_breaks", "the Tide held")
	_whole()
	check(go("exit") and room() == "tf_tidebreak_bastion", "back from the wall to the Bastion's yard (room %s)" % room())

# ------------------------------------------------------------------ 8: the grey fields and Greyfall
func _grey_fields() -> void:
	check(go("east") and room() == "tf_greyfall_breach", "east from the Bastion to the Greyfall Breach (room %s)" % room())
	check(go("east") and room() == "tf_hollow_wake", "on through the breach and the grey to the Hollow Wake (room %s)" % room())
	check(interact("journal_wake").get("ok", false) and c().quests.has_flag("journal_wake"), "Lu's journal page taken from its rack in the Wake")
	check(go("east") and room() == "tf_drone_hive", "on to the Drone Hive (room %s)" % room())
	var chest := interact("chest_5")
	check(chest.get("ok", false) and float(Game.room_rt.object_def("chest_5").get("alt", 0.0)) >= 2.0 * TopdownRoom.LEVEL - 1.0,
		"the hive mound climbed to the chest on its crown (%s)" % str(chest))
	check(_gated("east") == not TopdownRoom.has_layout("nd_nebula_verge"), "the Hive's way east into the Nebula Deep is closed by the prototype's gate while it has no layout")
	check(go("west") and room() == "tf_hollow_wake" and go("west") and room() == "tf_greyfall_breach", "back west through the Wake to the Breach (room %s)" % room())
	_story_to(22)
	_realm("sphere_lord_3")
	_take("greyfall")
	Game.world.load_room(c(), "tf_greyfall_breach", "west")   # Shen Lian at his post once the quest is under way
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	var shen: Dictionary = npc_object("shen_lian_breach")
	var grid: TopdownRoom = Game.room_rt.topdown
	var wall_row := 13
	check(not shen.is_empty() and TopdownRoom.cell_of(Vector2(float(shen.at[0]), float(shen.at[1]))).y == wall_row + 1,
		"Shen Lian holds the breach in the outer wall (%s)" % str(shen.get("at", [])))
	talk("shen_lian_breach")
	var began := interact("greyfall_stand")
	_hold(18.0)
	var drones := _spawned_at("hollow_drone", _event_cells("waves", 0))
	var wyrms := _spawned_at("hollowed_wyrmling", _event_cells("waves", 1))
	check(began.get("ok", false) and drones[1] and wyrms[1] and (drones[2] + wyrms[2]).all(func(q): return q.y < wall_row),
		"the Breach's bell rung: the Tide comes all at once out of the grey north of the wall, at the room's cells (%s; %s; %s)" % [str(began), str(drones), str(wyrms)])
	check(_run_out("greyfall_stand") and c().quests.has_flag("shen_lian_taken"), "the stand held beside Shen Lian, until the grey closed over him")
	var q: Dictionary = c().quests.active.get("greyfall", {})
	var prog: Array = q.get("progress", [])
	check(prog.size() >= 4 and int(prog[1]) >= 1 and int(prog[2]) >= 1 and int(prog[3]) >= 1, "Greyfall's steps at the Breach done: the Breach reached, Shen Lian found, the stand held (%s)" % str(prog))

# ------------------------------------------------------------------ 1, over the ten rooms
func _the_rooms() -> void:
	var missed := ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every story room and the Tidebreak Front's were entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
