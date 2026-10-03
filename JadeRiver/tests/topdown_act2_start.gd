extends "res://tests/prologue_run.gd"
## topdown_act2_start (R6, the room engine's Act II start; docs/architecture/room_engine.md, "Act II's first zones
## (R6)"): chapter 11, Act II's first chapter, played on the height grid by a top-down character through the rooms the
## room engine laid out from the side view: Cloudgate Port (the Arrival Terrace, the Port Market, the Wayfarers' Inn,
## the Skydock, the Condensing Hall, the Shipwrights' Yard) and the Thunderhorn Plains (the Stormgrass Verge, the
## Herders' Camp, the Thunderhorn Flats, the Lightning Scar); then a walk on through chapter 12's rooms (Rimefrost
## Heights, Mirrorwater Lake). Test shortcuts carry a new character to the Ascension Gate with Act I done (the story to
## chapter 10, Heaven Glimpse 3, a sturdy body, so the fights are the rooms' and not the balance's). From there it is
## played through the World authority:
##   1. the crossing: up through the Ascension Gate's cliff to the Arrival Terrace, on the grid on both sides, and back
##      down and up again;
##   2. each room is entered on the grid through its ways from the room before, and the top-down view builds it (a
##      figure for every person and thing, a mark for every way); in each, auto-path (TopdownRoute.reach: a hop up a
##      level, no running jump over a gap) reaches every NPC, object, herb, place and way from the spawn and every way
##      in;
##   3. chapter 11: Through the Gate (the toll warden at the gate's foot), A Sky Full of Toll Roads (the Factor in the
##      market, the free broker in the inn), Storm in the Blood (the town gate east sealed till it is under way; four
##      jades attuned, six Spark Weasels on the Stormgrass Verge, the shards), Horns for the Furnace (three thunderhorn
##      horns from the Flats, past the Herders' Camp, to the alchemist in the Condensing Hall off the Skydock), Sage;
##   4. on past chapter 11: the Lightning Scar's way east opens to a Sage, up through Rimefrost Heights to the summit
##      and the hermit's ice cave (its hidden way found); the Skydock's lake ferry to Mirrorwater Lake, along the shore,
##      the shallows (Toad's Hollow off them), the causeway to the Lake Shrine; the Nine Peaks ferry is the prototype's
##      gate exactly while Nine Peaks has no layout.
## Run headless:  godot --headless --path . res://tests/topdown_act2_start.tscn [-- --verbose]

const PORT := ["ae_landing", "ae_port_market", "ae_wayfarers_inn", "ae_skydock", "ae_condensing_hall", "ae_shipyard"]
const PLAINS := ["tp_stormgrass_verge", "tp_herders_camp", "tp_thunderhorn_flats", "tp_lightning_scar"]
const HEIGHTS := ["rf_frostpine_climb", "rf_snow_ape_ledges", "rf_rimefrost_summit", "rf_hermits_ice_cave"]
const LAKE := ["ml_reedless_shore", "ml_mirror_shallows", "ml_toads_hollow", "ml_sentinel_causeway", "ml_lake_shrine"]
const CH11 := ["through_the_gate", "a_sky_full_of_toll_roads", "storm_in_the_blood", "horns_for_the_furnace", "sage"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("act2/")
	_to_the_gate()
	_the_crossing()
	_the_port()
	_the_plains()
	_the_furnace()
	_beyond()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to the Ascension Gate
## The story before chapter 11 done (its prologue and main quests, the lessons), the prologue's systems and scenes,
## Heaven Glimpse 3 with Spirit Sense and a sturdy body (a test shortcut: the walk is about the rooms), on the Ascension
## Gate's summit.
func _to_the_gate() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	c().quests.flags["night_survived"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c().training_sect = {"id": "jade_sect", "rank": "core_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		var kind := str(q.get("kind", ""))
		if str(q.id) in CH11: continue
		if (kind in ["prologue", "main"] and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 10))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("heaven_glimpse_3")
	for u in ["spirit_sense", "hidden_portals", "teleport_stones"]: Unlocks.force_unlock(cid, u)
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 60000.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 900000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 30000.0, "source": "test:sturdy"}])
	_whole()
	GameEvents.event.connect(_on_room)
	Game.world.load_room(c(), "mp_ascension_gate", "east")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "mp_ascension_gate" and Game.room_rt.topdown != null and c().quests.is_done("the_ascension_gate"),
		"Act I done, at the Ascension Gate on the grid (room %s)" % room())

## A realm set outright (a test shortcut), its unlocks and offers evaluated, the realm's change told (a quest's realm
## step counts it).
func _realm(key: String) -> void:
	var from: String = c().cultivator.realm_key
	c().cultivator.realm_key = key
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(c().id)
	GameEvents.emit_event("realm_changed", {"actor": c().id, "from": from, "to": key, "major": false, "level": ProgressionRules.level(c())})
	GameEvents.flush()
	_whole()

## Stats rebuilt (the sturdy body's modifiers among them) and the body whole again between the fights.
func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp
	Game.combat.wounded.erase(c().id)

## Is the way `pid` of this room closed by the prototype's gate (its line said), as for a room with no layout?
func _gated(pid: String) -> bool:
	var gs: Dictionary = Game.world.portal_state(c(), Game.room_rt.portal_def(pid))
	return gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn")

## Is the way `pid` of this room open to walk through now?
func _open(pid: String) -> bool:
	return Game.world.portal_state(c(), Game.room_rt.portal_def(pid)).get("open", false)

## A quest's steps done, waiting to be handed in (or done on its own).
func _steps_done(q: String) -> bool:
	return c().quests.is_done(q) or str(c().quests.active.get(q, {}).get("state", "")) == "ready"

## A quest taken from its giver where they stand, or (a test shortcut) where the character stands.
func _take(npc: String, q: String) -> void:
	if not c().quests.is_active(q) and not c().quests.is_done(q):
		if npc_object(npc).is_empty() or not talk_choose(npc, "accept", q):
			Game.quest.apply_start(c().id, q)
	GameEvents.flush()
	check(c().quests.is_active(q) or c().quests.is_done(q), "%s under way" % q)

## A quest handed in to its hand-in where they stand (else, a test shortcut, where the character stands).
func _give(npc: String, q: String, what: String) -> void:
	GameEvents.flush()
	var ready := _steps_done(q)
	if ready and not c().quests.is_done(q) and (npc_object(npc).is_empty() or not talk_choose(npc, "hand_in", q)):
		Game.quest.hand_in(c(), q)
	GameEvents.flush()
	check(ready and c().quests.is_done(q), "%s: %s (%s)" % [q, what, str(c().quests.active.get(q, {}).get("state", "done" if c().quests.is_done(q) else "?"))])

## Walk into a room by its way from here, on the grid.
func _walk(pid: String, to: String, what: String) -> void:
	_whole()
	check(go(pid) and room() == to and Game.room_rt.topdown != null, "%s, on the grid (room %s)" % [what, room()])

# ------------------------------------------------------------------ 2: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not (rid in PORT or rid in PLAINS or rid in HEIGHTS or rid in LAKE) or entered.has(rid): return
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

# ------------------------------------------------------------------ 1: the crossing
func _the_crossing() -> void:
	check(not _gated("ascend") and _open("ascend"), "the Ascension Gate's way up to the Azure Expanse is open to a top-down character, its room on the grid")
	_walk("ascend", "ae_landing", "up through the Ascension Gate onto Cloudgate's Arrival Terrace")
	var grid: TopdownRoom = Game.room_rt.topdown
	var gate: Dictionary = Game.room_rt.portal_def("gate")
	check(grid.standable(TopdownRoom.cell_of(st.plane)) and st.plane.distance_to(Vector2(float(gate.arrive[0]), float(gate.arrive[1]))) <= 2.0 * TopdownRoom.TILE,
		"set down on the gate's dais under its archway, on the grid's floor (at %s)" % str(st.plane))
	_walk("gate", "mp_ascension_gate", "back down through the gate to the Ascension Gate's summit")
	_walk("ascend", "ae_landing", "and up again to the Arrival Terrace")

# ------------------------------------------------------------------ 3: chapter 11 in the port and on the plains
func _the_port() -> void:
	_take("warden_cao", "through_the_gate")
	var r := talk("warden_cao")
	GameEvents.flush()
	check(not r.is_empty() and c().quests.is_done("through_the_gate"), "Through the Gate: the toll warden spoken with at the gate's foot (%s)" % str(c().quests.active.get("through_the_gate", {})))
	_take("warden_cao", "a_sky_full_of_toll_roads")
	_walk("east", "ae_port_market", "east along the terrace into the Port Market")
	check(not _open("east"), "the town gate east to the Thunderhorn Plains is sealed till Storm in the Blood")
	check(not talk("factor_ruan").is_empty(), "the Alliance factor spoken with at the factors' hall")
	_walk("inn_door", "ae_wayfarers_inn", "in at the Wayfarers' Inn's door")
	check(not talk("broker_mu").is_empty(), "the free broker found at the inn's far table")
	_give("broker_mu", "a_sky_full_of_toll_roads", "the Factor and the broker both heard")
	_take("broker_mu", "storm_in_the_blood")
	for i in 4: submit({"type": "attune_jade", "zone": "azure_expanse", "index": i})
	GameEvents.flush()
	_walk("entry", "ae_port_market", "out of the inn into the market")
	check(_open("east"), "Storm in the Blood under way: the town gate east opens")

func _the_plains() -> void:
	_walk("east", "tp_stormgrass_verge", "east through the town gate onto the Stormgrass Verge")
	var weasels := 0
	for i in 16:
		if weasels >= 6: break
		_whole()
		weasels += fight("spark_weasel", 1, 90.0)
	var short: int = 10 - c().inventory.count("storm_shard")
	if short > 0: Game.inventory.apply_add(c().id, "storm_shard", short, "act2_suite")   # a test shortcut: the drops' dice
	GameEvents.flush()
	check(weasels >= 6 and _steps_done("storm_in_the_blood"), "six Spark Weasels defeated on the Verge, the jades attuned, the shards in hand (%d; %s)" % [weasels, str(c().quests.active.get("storm_in_the_blood", {}))])
	check(travel("ae_wayfarers_inn") and room() == "ae_wayfarers_inn", "back west through the market to the inn (room %s)" % room())
	_give("broker_mu", "storm_in_the_blood", "the storm in the blood answered")
	# Horns for the Furnace: the alchemist in the Condensing Hall, off the Skydock past the Arrival Terrace.
	check(travel("ae_condensing_hall") and room() == "ae_condensing_hall", "west through the terrace to the Skydock and in at the Condensing Hall (room %s)" % room())
	_take("alchemist_fen", "horns_for_the_furnace")
	check(travel("tp_thunderhorn_flats") and room() == "tp_thunderhorn_flats", "out across the Verge and the Herders' Camp to the Thunderhorn Flats (room %s)" % room())
	var rhinos := 0
	for i in 12:
		if rhinos >= 3: break
		_whole()
		rhinos += fight("thunderhorn_rhino", 1, 120.0, 0.0, true)
	var need: int = 3 - c().inventory.count("thunder_horn")
	if need > 0: Game.inventory.apply_add(c().id, "thunder_horn", need, "act2_suite")   # a test shortcut: the drops' dice
	GameEvents.flush()
	check(rhinos >= 3 and _steps_done("horns_for_the_furnace"), "thunderhorns hunted on the Flats, three horns taken (%d; %s)" % [rhinos, str(c().quests.active.get("horns_for_the_furnace", {}))])
	_walk("east", "tp_lightning_scar", "on east to the Lightning Scar")
	check(not _open("east"), "the Lightning Scar's way east to Rimefrost is sealed below Sage")

func _the_furnace() -> void:
	check(travel("ae_condensing_hall") and room() == "ae_condensing_hall", "back west over the plains and the port to the Condensing Hall (room %s)" % room())
	_give("alchemist_fen", "horns_for_the_furnace", "the horns pressed into the pill")
	_take("alchemist_fen", "sage")
	_realm("sage_1")   # a test shortcut: the breakthrough's own rules are the cultivation suites'
	_give("alchemist_fen", "sage", "a Sage, by the alchemist's furnace")
	check(CH11.all(func(q): return c().quests.is_done(q)), "chapter 11 played through on the grid (%s)" % str(CH11.filter(func(q): return not c().quests.is_done(q))))
	_walk("entry", "ae_skydock", "out to the Skydock")
	_walk("west", "ae_shipyard", "west to the Shipwrights' Yard")
	_walk("east", "ae_skydock", "back to the Skydock")

# ------------------------------------------------------------------ 4: on past chapter 11
func _beyond() -> void:
	# Up through Rimefrost Heights (a Sage now) to the summit and the hermit's cave (found by Spirit Sense: a shortcut).
	check(travel("tp_lightning_scar") and room() == "tp_lightning_scar" and _open("east"), "back to the Lightning Scar: its way east opens to a Sage (room %s)" % room())
	_walk("east", "rf_frostpine_climb", "east up onto Frostpine Climb's snow")
	_walk("east", "rf_snow_ape_ledges", "up the three tiers to the Snow Ape Ledges")
	_walk("east", "rf_rimefrost_summit", "on to Rimefrost Summit")
	Game.quest.apply_flag(c().id, WorldPortals.seen_flag("rf_rimefrost_summit", "ice_cave"))
	_walk("ice_cave", "rf_hermits_ice_cave", "into the hermit's ice cave through the cleft in the crags")
	_walk("entry", "rf_rimefrost_summit", "back out onto the summit")
	# The lake ferry from the Skydock (The Mirror Remembers under way: a shortcut), along the lake to its shrine.
	for q in ["shards_for_sale", "frost_and_silence"]: c().quests.done[q] = 1
	_realm("sage_2")
	Game.quest.apply_start(c().id, "the_mirror_remembers")
	GameEvents.flush()
	check(travel("ae_skydock") and room() == "ae_skydock", "back down to the Skydock (room %s)" % room())
	_walk("lake_ferry", "ml_reedless_shore", "aboard the lake ferry and down at the Reedless Shore's jetty")
	_walk("east", "ml_mirror_shallows", "east along the shore to the Mirror Shallows")
	_walk("hollow", "ml_toads_hollow", "in at Toad's Hollow's mouth in the bluff")
	_walk("entry", "ml_mirror_shallows", "back out to the shallows")
	_walk("east", "ml_sentinel_causeway", "on to the Sentinel Causeway")
	_walk("east", "ml_lake_shrine", "across the causeway to the Lake Shrine's island")
	var mirror := interact("mirror_altar")
	check(mirror.get("ok", false) and c().quests.has_flag("mirror_vision_seen"), "the shrine's bronze mirror looked into (%s)" % str(mirror))
	# The frontier: the Nine Peaks ferry (its quest done: a shortcut) is the prototype's gate while Nine Peaks has no layout.
	c().quests.done["the_mirror_remembers"] = 1
	c().quests.active.erase("the_mirror_remembers")
	check(travel("ae_skydock") and room() == "ae_skydock", "home by the ferry to the Skydock (room %s)" % room())
	check(_gated("peaks_ferry") == not TopdownRoom.has_layout("np_alliance_gate"),
		"the Nine Peaks ferry is closed by the prototype's gate exactly while Nine Peaks has no layout")

# ------------------------------------------------------------------ 2: over the rooms
func _the_rooms() -> void:
	var all: Array = PORT + PLAINS + HEIGHTS + LAKE
	var missed := all.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of Cloudgate Port, the Thunderhorn Plains, Rimefrost Heights and Mirrorwater Lake was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
