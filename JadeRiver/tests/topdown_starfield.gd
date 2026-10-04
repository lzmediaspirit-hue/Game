extends "res://tests/prologue_run.gd"
## topdown_starfield (R9, the room engine's last batch; docs/architecture/room_engine.md, "The star field's end (R9)"):
## the Lantern Star Field's last zones played on the height grid by a top-down character, through the twenty-one rooms
## the room engine laid out from the side view: the Starsea's two crossings, the Star Warden Citadel (the Citadel Gate,
## the Wardens' Hall, the Observatory, the Presence Court), the Orbit Ruins (the Tumbling Stair, the Orbit Garden, the
## Golem Foundry, the Inverted Hall), the Ashen Reach (the Cinder Fields, the Ashborn Palisade, the War Camp, Kharn's
## Pyre), the Nebula Deep (the Nebula Verge, the Eel Currents, the Crab Grottoes, the Leviathan's Maw) and the Lantern
## Heart (the Wick Gate, the Hall of Burning Stars, the Flame Heart). Test shortcuts carry a new character there (the
## story before chapter 17 done, a sturdy body, the Field's attunement) and set its realm as the story asks; from there
## it is played through the World authority, as topdown_sunscar plays chapters 13 and 14:
##   1. each room is entered on the grid through its ways from the room before (or by the voyage, for a crossing), and
##      the top-down view builds it: a figure for every person and thing, a mark for every way;
##   2. in each, auto-path (TopdownRoute.reach) reaches every NPC, object and way from the room's spawn and every way in;
##   3. the Starsea's crossings: the Wreck Run and the Lantern Run sailed both ways, each from its dock on the grid (R6's
##      Shipwrights' Yard, R8's Broken Pier, Starsea Launch and Arrival Quay), the waves boarding over the bow onto the
##      deck's own cells, the vessel making port; The Lantern Run's first step;
##   4. chapter 20: The Citadel (the Wardens' skiff from the Arrival Quay, Warden-Commander Yao in his hall), The Aspirant
##      (Shen Lian's spar in the Presence Court), The Observatory (the great scope, Stargazer Ming), Sphere Lord, The
##      Orbit Ruins (the hermit, a jade gravity switch, three gravity golems, the Inverted Hall);
##   5. chapter 21: Cinder Fields (the ash skiff, six raiders, Warden Hu Jin), Kharn's Pyre (the envoy heard, Kharn
##      kneeling on his pyre's floor and spared), the tide skiff to the Tidebreak Bastion and back;
##   6. chapter 22: Lu's Lantern (through the Drone Hive into the Nebula Deep, Lu's star notes in the Crab Grottoes, up the
##      stair above the harbour to the Flame Heart and its flame), The Leviathan's Maw (the Leviathan on its shoal).
## The side view's mechanics with no top-down counterpart yet are T-batches': the gravity switches' low gravity (the switch
## turns and counts, the air does not lighten on the grid), the Inverted Hall's and the Maw's no-flight rule, the
## Leviathan's swim and the crossings' star wind; the walk crosses those rooms on foot.
## Run headless:  godot --headless --path . res://tests/topdown_starfield.tscn [-- --verbose]

const CROSSINGS := ["ss_starsea_crossing", "ss_lantern_crossing"]
const CITADEL := ["wc_citadel_gate", "wc_wardens_hall", "wc_observatory", "wc_presence_court"]
const RUINS := ["or_tumbling_stair", "or_orbit_garden", "or_golem_foundry", "or_inverted_hall"]
const REACH := ["ar_cinder_fields", "ar_ashborn_palisade", "ar_war_camp", "ar_kharns_pyre"]
const DEEP := ["nd_nebula_verge", "nd_eel_currents", "nd_crab_grottoes", "nd_leviathans_maw"]
const HEART := ["lt_wick_gate", "lt_hall_of_burning_stars", "lt_flame_heart"]
const STORY := ["the_lantern_run", "the_citadel", "the_aspirant", "the_observatory", "sphere_lord", "a_sphere_of_ones_own",
	"the_orbit_ruins", "cinder_fields", "kharns_pyre", "the_tide_breaks", "star_warden", "the_leviathans_maw", "lus_lantern"]
const FIELD := "lantern_star_field"

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	start_new("starfield/")
	_to_the_field()
	_crossings()
	_citadel()
	_orbit_ruins()
	_ashen_reach()
	_nebula_deep()
	_lantern_heart()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to the Field
## The story before chapter 17 done (its prologue and main quests, the guided ones; the Field's chapters 17 to 19 too,
## all but the steps played here), the prologue's systems and scenes, a sturdy body with a scholar's Insight (a test
## shortcut: the walk is about the rooms), the Field's attunement, a vessel and the Lantern Run's chart.
func _to_the_field() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	c().quests.flags["night_survived"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c().training_sect = {"id": "jade_sect", "rank": "core_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		var kind := str(q.get("kind", ""))
		if str(q.id) in STORY: continue
		if (kind in ["prologue", "main"] and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 19))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("sage_sovereign_3")
	for u in ["teleport_stones", "smithing", "attack", "qi_springs", "spirit_sense", "starsea", "presence"]: Unlocks.force_unlock(cid, u)
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 900000.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 15000000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 500000.0, "source": "test:sturdy"},
		{"stat": "insight", "op": "flat", "value": 400.0, "source": "test:scholar"}])
	for item in ["cloud_skiff", "star_chart_wreck", "star_chart_lantern"]: Game.inventory.apply_add(cid, item, 1, "starfield_suite")
	_attune(90.0)
	_whole()
	GameEvents.event.connect(_on_room)

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

## The Field's attunement raised by its jades (a test shortcut: the shards a player gathers over the zones).
func _attune(need: float) -> void:
	var guard := 0
	while float(c().cultivator.attunement.get(FIELD, 0.0)) < need and guard < 120:
		var lv: Array = Game.progression.jade_levels(c(), FIELD)
		var lowest := lv.find(lv.min())
		var cost: int = Game.progression.jade_cost(FIELD, int(lv[lowest]))
		var shard := str(ContentDB.zone(FIELD).get("attunement", {}).get("shard", "star_shard"))
		if c().inventory.count(shard) < cost: Game.inventory.apply_add(c().id, shard, cost, "starfield_suite")
		if not submit({"type": "attune_jade", "zone": FIELD, "index": lowest}).get("ok", false): break
		guard += 1

# ------------------------------------------------------------------ 1, 2: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not rid in CROSSINGS + CITADEL + RUINS + REACH + DEEP + HEART or entered.has(rid): return
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
			# S12c: a thing on a path above stands on a ledge only its movement art climbs onto (topdown_traversal lands there).
			if grid.ledge_at(Vector2(float(o.at[0]), float(o.at[1])), float(o.get("alt", 0.0))) != "": continue
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

# ------------------------------------------------------------------ helpers of the story
## A quest's steps done, waiting to be handed in (or done on its own).
func _steps_done(q: String) -> bool:
	return c().quests.is_done(q) or str(c().quests.active.get(q, {}).get("state", "")) == "ready"

## A quest under way (started outright where nobody stands to offer it: a test shortcut).
func _start(q: String) -> void:
	if not (c().quests.is_active(q) or c().quests.is_done(q)): Game.quest.apply_start(c().id, q)
	GameEvents.flush()

## A quest's objective's progress.
func _objective(q: String, i: int) -> int:
	return int(c().quests.active.get(q, {}).get("progress", [0, 0, 0, 0, 0, 0])[i]) if not c().quests.is_done(q) else 99

## A quest done outright (a test shortcut, for the steps another suite plays: the Tide battle is topdown_story_rooms').
func _done(q: String) -> void:
	c().quests.offered.erase(q)
	c().quests.active.erase(q)
	c().quests.done[q] = 1

## The tracker's entry for `quest` leads to `target`, a room on the grid.
func _leads(quest: String, target: String) -> bool:
	for e in Game.quest.tracker(c()):
		if str(e.get("quest", "")) == quest: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target)
	return false

## The way `pid` of this room leads into a room laid out on the grid, as every room is (decision 41's gate, which shut a
## way into a room with no layout yet, went in S12a).
func _leads_on(pid: String) -> bool:
	return TopdownRoom.has_layout(str(Game.room_rt.portal_def(pid).get("to", "")))

## Fight `def_id` across `rooms` (each walked into on the grid) until `count` have fallen; the tally.
func _hunt(def_id: String, count: int, rooms: Array, per_room_s := 120.0) -> int:
	var killed := 0
	for rid in rooms:
		if killed >= count: break
		if not travel(rid): continue
		for i in 8:
			if killed >= count: break
			_whole()
			var k := fight(def_id, 1, per_room_s / 4.0)
			killed += k
			if k == 0 and Game.room_rt.living_enemies().filter(func(e): return e.def_id == def_id).is_empty(): break
	return killed

## The living foes of `def_id` in the room, waiting up to `wait_s` for them to come.
func _foes(def_id: String, wait_s := 10.0) -> Array:
	var out: Array = []
	var t := 0.0
	while t <= wait_s:
		out = Game.room_rt.living_enemies().filter(func(e): return e.def_id == def_id)
		if not out.is_empty(): break
		step(0.5)
		t += 0.5
	return out

# ------------------------------------------------------------------ 3: the Starsea's crossings
## A voyage sailed from its dock: the dock used on the grid of its room, the crossing's deck on the grid, its waves
## boarding onto the deck's own cells (the layout's event), the vessel making port when the crossing's time runs out.
func _sail(dock_room: String, dock: String, route: String, crossing: String, foe: String, port: String) -> void:
	Game.world.apply_teleport(c().id, dock_room)
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	var o: Dictionary = Game.room_rt.object_def(dock)
	check(Game.room_rt.topdown != null and str(o.get("route", "")) == route,
		"%s: %s's dock on the grid, charted for the %s (room %s)" % [route, dock_room, route, room()])
	var r := interact(dock)
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	var grid: TopdownRoom = Game.room_rt.topdown if Game.room_rt else null
	check(r.get("ok", false) and room() == crossing and grid != null and Game.room_rt.event.get("active", false),
		"%s sailed from the dock: the crossing's deck on the grid, the voyage under way (%s; room %s)" % [route, str(r), room()])
	if grid == null: return
	var spawn: Vector2 = grid.spawn
	check(grid.standable(TopdownRoom.cell_of(spawn)) and grid.floor_at(spawn) >= 0.0, "%s: the body set down on the deck" % crossing)
	var boarders := _foes(foe, 24.0)
	check(not boarders.is_empty() and boarders.all(func(e): return grid.standable(TopdownRoom.cell_of(e.plane))),
		"%s: the %s board onto the deck's own cells (%s)" % [crossing, foe, str(boarders.map(func(e): return TopdownRoom.cell_of(e.plane)))])
	Game.room_rt.event.remaining = 0.01
	step(0.2)
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == port and not Game.world.voyages.has(c().id), "%s: the vessel makes port at %s (room %s)" % [crossing, port, room()])

func _crossings() -> void:
	# Every dock of the Starsea: R6's Shipwrights' Yard and R8's Broken Pier, Starsea Launch and Arrival Quay.
	_sail("ae_shipyard", "dock_cloudgate", "wreck_run", "ss_starsea_crossing", "starsea_pirate", "sw_broken_pier")
	_sail("sw_broken_pier", "dock_wreck", "wreck_run_home", "ss_starsea_crossing", "starsea_pirate", "ae_shipyard")
	_sail("lh_arrival_quay", "dock_lantern", "lantern_run_home", "ss_lantern_crossing", "comet_sparrow", "sw_starsea_launch")
	_start("the_lantern_run")
	_sail("sw_starsea_launch", "dock_launch", "lantern_run", "ss_lantern_crossing", "comet_sparrow", "lh_arrival_quay")
	GameEvents.flush()
	check(_objective("the_lantern_run", 0) >= 1, "The Lantern Run: sailed from the Starsea Launch to the Arrival Quay (%s)" % str(c().quests.active.get("the_lantern_run", {})))
	_done("the_lantern_run")

# ------------------------------------------------------------------ 4: chapter 20, the Citadel and the Orbit Ruins
func _citadel() -> void:
	# The Citadel: the Wardens' skiff from the Arrival Quay, Yao in his hall.
	_realm("will_manifest_3")
	_start("the_citadel")
	check(go("warden_skiff") and room() == "wc_citadel_gate" and Game.room_rt.topdown != null,
		"the Wardens' skiff from the Arrival Quay to the Citadel Gate, on the grid (room %s)" % room())
	check(_leads_on("skiff"),
		"the Citadel's skiff leads back to Lanternfall's Arrival Quay, on the grid")
	var into := go("hall_door")
	var yao := talk("warden_commander_yao")
	GameEvents.flush()
	check(into and room() == "wc_wardens_hall" and not yao.is_empty() and _steps_done("the_citadel"),
		"through the Wardens' Hall's door: Warden-Commander Yao reported to (%s)" % str(c().quests.active.get("the_citadel", {})))
	if not c().quests.is_done("the_citadel"): hand_in("warden_commander_yao", "the_citadel")
	# The Aspirant: Shen Lian's spar in the Presence Court.
	_start("the_aspirant")
	check(_leads("the_aspirant", "wc_presence_court"), "The Aspirant leads to the Presence Court, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	check(go("entry") and travel("wc_presence_court") and Game.room_rt.topdown != null, "out of the hall and west to the Presence Court (room %s)" % room())
	var won := false
	for i in 3:
		_whole()
		won = spar_with(func(): return _spar_service("shen_lian_warden"))
		if won: break
	GameEvents.flush()
	check(won and _steps_done("the_aspirant"), "Shen Lian beaten in a spar on the Presence Court's round floor")
	check(travel("wc_wardens_hall"), "back east and into the Wardens' Hall (room %s)" % room())
	if not c().quests.is_done("the_aspirant") and _steps_done("the_aspirant"): hand_in("warden_commander_yao", "the_aspirant")
	_done("the_aspirant")
	# The Observatory: Presence level 5 (a test shortcut for its training), the great scope and Stargazer Ming.
	var guard := 0
	while Game.field.presence_level(c()) < 5 and guard < 40:
		Game.field.apply_presence_xp(c().id, 40.0, "starfield_suite")
		guard += 1
	_start("the_observatory")
	check(travel("wc_observatory") and Game.room_rt.topdown != null, "east to the Citadel Gate and through the Observatory's door (room %s)" % room())
	var scope := interact("great_scope")
	GameEvents.flush()
	check(scope.get("ok", false) and c().quests.has_flag("observed_sphere"), "the great scope on its dais looked into (%s)" % str(scope))
	var ming := talk("stargazer_ming")
	GameEvents.flush()
	check(not ming.is_empty() and _steps_done("the_observatory"), "Stargazer Ming told what was seen (%s)" % str(c().quests.active.get("the_observatory", {})))
	if not c().quests.is_done("the_observatory") and _steps_done("the_observatory"): hand_in("stargazer_ming", "the_observatory")
	# Sphere Lord (a test shortcut sets the realm).
	_start("sphere_lord")
	_realm("sphere_lord_1")
	GameEvents.event.emit("realm_changed", {"actor": c().id, "realm": "sphere_lord_1"})
	GameEvents.flush()
	for q in ["sphere_lord", "a_sphere_of_ones_own"]: _done(q)

func _orbit_ruins() -> void:
	_start("the_orbit_ruins")
	check(travel("wc_citadel_gate") and _leads("the_orbit_ruins", "or_orbit_garden"),
		"The Orbit Ruins leads to the Orbit Garden, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	var rooms := [room()]
	for rid in ["or_tumbling_stair", "or_orbit_garden"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["wc_citadel_gate", "or_tumbling_stair", "or_orbit_garden"],
		"past the Warden line, over the Tumbling Stair to the Orbit Garden, room by room on the grid (%s)" % str(rooms))
	var hermit := talk("orbit_hermit")
	GameEvents.flush()
	check(not hermit.is_empty() and _objective("the_orbit_ruins", 0) >= 1, "the Orbit Hermit found in his garden")
	var sw := interact("switch_garden")
	GameEvents.flush()
	check(sw.get("ok", false) and _objective("the_orbit_ruins", 1) >= 1, "a jade gravity switch pressed down in its ring of stone (%s)" % str(sw))
	interact("switch_garden")
	var golems := _hunt("gravity_golem", 3, ["or_golem_foundry", "or_tumbling_stair", "or_golem_foundry"], 160.0)
	check(golems >= 3 or _objective("the_orbit_ruins", 2) >= 3, "three gravity golems broken, on the grid (%d)" % golems)
	check(travel("or_golem_foundry") and go("hall") and room() == "or_inverted_hall" and Game.room_rt.topdown != null,
		"through the door sunk in the Foundry's house into the Inverted Hall, on the grid (room %s)" % room())
	GameEvents.flush()
	check(c().quests.is_done("the_orbit_ruins") or _steps_done("the_orbit_ruins"), "The Orbit Ruins' steps done (%s)" % str(c().quests.active.get("the_orbit_ruins", {})))
	var chest := interact("chest_gallery")
	check(chest.get("ok", false), "the chest on the Inverted Hall's high gallery reached up its flight (%s)" % str(chest))
	check(go("entry") and room() == "or_golem_foundry", "back out to the Golem Foundry (room %s)" % room())
	_done("the_orbit_ruins")

# ------------------------------------------------------------------ 5: chapter 21, the Ashen Reach
func _ashen_reach() -> void:
	_start("cinder_fields")
	check(travel("wc_citadel_gate") and go("ash_skiff") and room() == "ar_cinder_fields" and Game.room_rt.topdown != null,
		"the Wardens' skiff from the Citadel Gate to the Cinder Fields, on the grid (room %s)" % room())
	var raiders := _hunt("ashborn_raider", 6, ["ar_cinder_fields", "ar_ashborn_palisade", "ar_cinder_fields", "ar_ashborn_palisade"])
	check(raiders >= 6 or _objective("cinder_fields", 1) >= 6, "six Ashborn raiders driven back on the burnt plain (%d)" % raiders)
	check(travel("ar_cinder_fields"), "back to the Wardens' landing (room %s)" % room())
	var hu := talk("warden_hu_jin")
	GameEvents.flush()
	check(not hu.is_empty() and _steps_done("cinder_fields"), "Warden Hu Jin reported to at the landing (%s)" % str(c().quests.active.get("cinder_fields", {})))
	_done("cinder_fields")
	# Kharn's Pyre: the envoy heard in the war camp, Kharn kneeling on his pyre's floor, and spared.
	_start("kharns_pyre")
	var rooms := [room()]
	for rid in ["ar_ashborn_palisade", "ar_war_camp"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["ar_cinder_fields", "ar_ashborn_palisade", "ar_war_camp"],
		"through the palisade's gate to the War Camp, room by room on the grid (%s)" % str(rooms))
	var veyla := talk("ashborn_envoy_veyla")
	GameEvents.flush()
	check(not veyla.is_empty() and _objective("kharns_pyre", 0) >= 1, "the Ashborn envoy heard on the parley ground")
	_whole()
	check(travel("ar_kharns_pyre") and Game.room_rt.topdown != null, "past the camp's guards to Kharn's Pyre, on the grid (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var kharn: Array = _foes("general_kharn")
	check(kharn.size() == 1 and grid.standable(TopdownRoom.cell_of(kharn[0].plane)), "General Kharn waits on his pyre's floor (%s)" % str(kharn.map(func(e): return e.plane)))
	var tries := 0
	while not kharn.is_empty() and kharn[0].alive and not kharn[0].ai.get("surrendered", false) and tries < 24:
		_whole()
		if tries >= 2 and kharn[0].pools.hp > kharn[0].pools.max_hp * 0.25: kharn[0].pools.hp = kharn[0].pools.max_hp * 0.25   # a test shortcut
		fight("general_kharn", 1, 15.0, 0.0, true)
		tries += 1
	check(not kharn.is_empty() and kharn[0].ai.get("surrendered", false), "Kharn kneels at a fifth of his health")
	var judged := submit({"type": "judge_foe", "enemy": kharn[0].uid if not kharn.is_empty() else 0, "spare": true})
	GameEvents.flush()
	check(judged.get("ok", false) and _steps_done("kharns_pyre"), "and is spared: Kharn's Pyre's steps done (%s)" % str(judged))
	_done("kharns_pyre")
	# The tide skiff to the Tidebreak Bastion and back (the Tide battle is topdown_story_rooms').
	_start("the_tide_breaks")
	check(travel("wc_citadel_gate") and go("tide_skiff") and room() == "tf_tidebreak_bastion" and Game.room_rt.topdown != null,
		"the Wardens' skiff from the Citadel Gate to the Tidebreak Bastion, on the grid (room %s)" % room())
	check(_leads_on("skiff") and go("skiff") and room() == "wc_citadel_gate", "and the Bastion's skiff back to the Citadel, open on the grid (room %s)" % room())
	for q in ["the_tide_breaks", "star_warden"]: _done(q)
	_realm("sphere_lord_2")

# ------------------------------------------------------------------ 6: chapter 22, the Nebula Deep and the Lantern Heart
func _nebula_deep() -> void:
	_start("lus_lantern")
	check(go("tide_skiff") and travel("tf_drone_hive") and room() == "tf_drone_hive", "back over the grey fields to the Drone Hive (room %s)" % room())
	check(_leads_on("east"), "the Hive's way east into the Nebula Deep is open on the grid")
	var rooms := [room()]
	for rid in ["nd_nebula_verge", "nd_eel_currents", "nd_crab_grottoes"]:
		_whole()
		if travel(rid): rooms.append(room())
	GameEvents.flush()
	check(rooms == ["tf_drone_hive", "nd_nebula_verge", "nd_eel_currents", "nd_crab_grottoes"],
		"into the Nebula Deep, along the Verge and over the Eel Currents' causeways to the Crab Grottoes, room by room on the grid (%s)" % str(rooms))
	check(_objective("lus_lantern", 0) >= 1, "Lu's Lantern: the Nebula Deep reached")
	var notes := interact("lus_star_notes")
	GameEvents.flush()
	check(notes.get("ok", false) and c().quests.has_flag("lus_notes_found"), "Lu's star notes found in their shell in the grotto (%s)" % str(notes))
	# The Leviathan's Maw: the Leviathan on its shoal in the lagoon.
	_start("the_leviathans_maw")
	_whole()
	check(travel("nd_leviathans_maw") and Game.room_rt.topdown != null, "east into the Leviathan's Maw, on the grid (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var lev: Array = _foes("nebula_leviathan")
	check(lev.size() == 1 and grid.standable(TopdownRoom.cell_of(lev[0].plane)), "the Nebula Leviathan surfaces on the shoal in the Maw (%s)" % str(lev.map(func(e): return TopdownRoom.cell_of(e.plane))))
	for e in lev: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.2)   # a test shortcut: the fight is the arena's, not the balance's
	var killed := 0
	for i in 6:
		if killed >= 1: break
		_whole()
		killed += fight("nebula_leviathan", 1, 60.0, 0.0, true)
	GameEvents.flush()
	check(killed >= 1 and _steps_done("the_leviathans_maw"), "the Nebula Leviathan brought down on its shoal (%d)" % killed)
	_done("the_leviathans_maw")

func _lantern_heart() -> void:
	# Up the stair above the harbour.
	Game.world.apply_teleport(c().id, "lh_harbor_market")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(go("lantern_stair") and room() == "lt_wick_gate" and Game.room_rt.topdown != null,
		"up the stair above the harbour to the Wick Gate, on the grid (room %s)" % room())
	check(_leads_on("stair"),
		"the Wick Gate's stair leads down to the Harbor Market, on the grid")
	var rooms := [room()]
	for rid in ["lt_hall_of_burning_stars", "lt_flame_heart"]:
		_whole()
		if travel(rid): rooms.append(room())
	GameEvents.flush()
	check(rooms == ["lt_wick_gate", "lt_hall_of_burning_stars", "lt_flame_heart"],
		"through the Hall of Burning Stars to the Flame Heart, room by room on the grid (%s)" % str(rooms))
	var flame := interact("heart_flame")
	GameEvents.flush()
	check(flame.get("ok", false) and c().quests.has_flag("heart_flame_taken") and _steps_done("lus_lantern"),
		"a spark of the first lantern's flame taken before its cage: Lu's Lantern's steps done (%s)" % str(c().quests.active.get("lus_lantern", {})))
	var chest := interact("chest_ledge_mv_1")
	check(chest.get("ok", false), "the chest on the Flame Heart's ledge reached up its flight (%s)" % str(chest))

# ------------------------------------------------------------------ 1, 2: over the rooms
func _the_rooms() -> void:
	var all: Array = CROSSINGS + CITADEL + RUINS + REACH + DEEP + HEART
	var missed := all.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of the crossings, the Citadel, the Ruins, the Reach, the Deep and the Heart was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
