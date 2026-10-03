extends "res://tests/prologue_run.gd"
## topdown_skysea (R8; docs/architecture/room_engine.md, "The sky-sea zones (R8)"): the twenty rooms of the late game's
## sky-sea zones the room engine laid out from the side view (the Skyport Wreck, Lanternfall Harbor, the Drifting Shoals,
## Blackmast Haven and the Wyrmnest Isles), and their main quests, chapters 15 to 19, played on the height grid by a
## top-down character. Test shortcuts carry a new character along the story to each chapter with the story before it
## done, at the realm it asks, with a sturdy body (the fights are the rooms', not the balance's); quests are taken and
## handed in where they stand (their givers are often off the grid). What the grid has no part in yet is a shortcut too,
## and says so: the Starsea crossings (a voyage loads the far room), the chart table and the slipway in the Shipwrights'
## Yard, the Trial Hall, the jades' attunement, Presence training, taming and the egg's warming. Played through the World
## authority:
##   1. each room is entered on the grid, and the top-down view builds it (a figure for every person and thing, a mark
##      for every way); in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump) reaches every NPC,
##      object and way from the spawn and every way in;
##   2. The Skyport Wreck (ch 15): set down on the Broken Pier by its dock over the clouds; the pirates fought on the old
##      port's road; east to the Pirate Deck: Gu in chains on the junk's deck, freed for the Black Ledger, the pirates'
##      strongbox opened on the stern castle;
##   3. Lu's Last Page and Stars Beyond (ch 16): up to the Riven Peak, Lu's page on its knoll, a star reading at the stone
##      on the highest crag; on to the Starsea Launch, Warden He and the launch ring on its dais;
##   4. The Lantern Run and Crystal and Jade (ch 17): the Arrival Quay (the Wardens' skiff gated while the Citadel has no
##      layout), the Harbor Market's exchange, the Star Chandlery's furnace and the Tidelight Inn through their doors, the
##      stair to the Lantern Heart gated while it has no layout;
##   5. Salt of the Stars, Will Manifest and A Presence of One's Own (ch 17): the star jellyfish thinned wading the
##      Jellyfish Shallows, Old Bo's planters on his hulk's deck, the comet sparrows hunted on the Sparrow Reefs, the
##      insight stone on the Driftglass Bank;
##   6. The Purser's Ledger, Gunners' Battery and The Admiral (ch 18): east from the harbour through the Shoals to the
##      Blackmast Docks on foot; the pirates cut down on the boardwalk, Deckhand Mo found; the battery's three cannons
##      spiked behind its parapet, its gunners silenced, the purser found on his ledge in the Smugglers' Cove (the crack
##      shown, as Spirit Sense shows it); Admiral Voss defeated on his flagship's deck, his seal taken, his strongbox opened;
##   7. Star-Tier Beasts, A Hollowed Brood and The Last Egg (ch 19): the skiff from the Moored Hulks to the Nest Cliffs'
##      pier, Tamer Qiu; the Hollowed wyrmlings put to rest on the Eggshell Terraces, whose grey puddles are the layout's
##      areas; the Guardian's Crown's chest on its summit; the Hatching Cave through the cleft, the Brood Guardian
##      defeated and the last egg taken beside its nest.
## Run headless:  godot --headless --path . res://tests/topdown_skysea.tscn [-- --verbose]

const SKY_ROOMS := ["sw_broken_pier", "sw_pirate_deck", "sw_riven_peak", "sw_starsea_launch", "lh_arrival_quay",
	"lh_harbor_market", "lh_star_chandlery", "lh_tidelight_inn", "dr_jellyfish_shallows", "dr_moored_hulks", "dr_sparrow_reefs",
	"dr_driftglass_bank", "bm_blackmast_docks", "bm_gunners_battery", "bm_smugglers_cove", "bm_flagship_deck", "wn_nest_cliffs",
	"wn_eggshell_terraces", "wn_guardians_crown", "wn_hatching_cave"]
const TESTED := ["the_skyport_wreck", "lus_last_page", "stars_beyond", "the_lantern_run", "crystal_and_jade", "salt_of_the_stars",
	"will_manifest", "a_presence_of_ones_own", "the_pursers_ledger", "gunners_battery", "the_admiral", "star_tier_beasts",
	"a_hollowed_brood", "the_last_egg"]
const LV := TopdownRoom.LEVEL

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("r8/")
	_story_to(15)
	GameEvents.event.connect(_on_room)
	_skyport_wreck()
	_riven_peak()
	_lanternfall()
	_shoals()
	_blackmast()
	_wyrmnest()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcuts
## The story's prologue and main quests before chapter `upto` done (but the ones this suite plays), the prologue's
## systems and scenes, the sturdy body; the field bosses unlocked.
func _story_to(upto: int) -> void:
	var cid: String = c().id
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

## The realm a chapter asks (a test shortcut).
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
	check(ready and r.get("ok", false) and c().quests.is_done(qid), "%s: %s (state %s, steps %s)" % [qid, what,
		str(c().quests.active.get(qid, {}).get("state", "done" if c().quests.is_done(qid) else "?")), str(_steps(qid))])

## A quest whose last steps are off the grid stood done (a test shortcut; what the grid plays is checked before it).
func _finish(qid: String) -> void:
	c().quests.offered.erase(qid)
	c().quests.active.erase(qid)
	c().quests.done[qid] = 1
	GameEvents.flush()

## A quest's steps so far.
func _steps(qid: String) -> Array:
	return c().quests.active.get(qid, {}).get("progress", [])

## Some of an item, as a test shortcut gives it (a drop the loot tables roll, a chart off the grid).
func _give(item: String, n := 1) -> void:
	Game.inventory.apply_add(c().id, item, n, "skysea_suite")
	GameEvents.flush()

## A system used, as its page would say (a test shortcut for what has no part on the grid).
func _used(system: String) -> void:
	GameEvents.emit_event("system_used", {"actor": c().id, "system": system})
	GameEvents.flush()

## A boss weakened first (a test shortcut: the fight is the room's, not the balance's), then fought on the grid.
func _boss(def_id: String, limit := 300.0) -> int:
	_whole()
	for e in Game.room_rt.living_enemies():
		if e.def_id == def_id: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.1)
	return fight(def_id, 1, limit, 0.0, true)

## The loaded room's object's floor height (world units) and cell.
func _alt(oid: String) -> float:
	return float(Game.room_rt.object_def(oid).get("alt", 0.0))

func _cell(oid: String) -> Vector2i:
	var o: Dictionary = Game.room_rt.object_def(oid)
	return TopdownRoom.cell_of(Vector2(float(o.at[0]), float(o.at[1]))) if o.has("at") else Vector2i(-1, -1)

## Is the way `pid` of the loaded room closed by the prototype's gate?
func _gated(pid: String) -> bool:
	var gs: Dictionary = Game.world.portal_state(c(), Game.room_rt.portal_def(pid))
	return gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn")

# ------------------------------------------------------------------ 1: each room as it is entered
func _on_room(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	if not rid in SKY_ROOMS or entered.has(rid): return
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

# ------------------------------------------------------------------ 2: The Skyport Wreck (chapter 15)
func _skyport_wreck() -> void:
	_realm("sage_sovereign_1")
	_take("the_skyport_wreck")
	_give("star_chart_wreck")   # Navigator Sun's chart table and Shipwright Lao's slipway are in the Shipwrights' Yard,
	_give("cloud_skiff")        # off the grid; the Wreck Run's crossing too: the voyage loads the far room
	check(_load("sw_broken_pier"), "the Wreck Run makes port at the Broken Pier, on the grid (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var at := TopdownRoom.cell_of(st.plane)
	var dock := _cell("dock_wreck")
	check(at.x <= 8 and dock.y >= grid.h - 2 and absi(dock.x - at.x) <= 4,
		"set down on the pier by the skiffs' dock at its end over the clouds (at %s, the dock %s)" % [str(at), str(dock)])
	check(_steps("the_skyport_wreck").size() >= 3 and int(_steps("the_skyport_wreck")[2]) >= 1, "the Skyport Wreck reached (%s)" % str(_steps("the_skyport_wreck")))
	var chests := [_alt("chest_ledge_mv_1"), _alt("chest_cloud_mv")]
	check(chests.all(func(a): return a >= 3.0 * LV - 1.0), "the chests the pirates stripped from the wreck lie on its broken decks, three levels up (%s)" % str(chests))
	check(fight("starsea_pirate", 2, 120.0) >= 2, "the pirates fought on the old port's road, on the grid")
	_give("ledger_page", 3)   # the pages the pirates carry: their drops are the loot table's
	check(go("east") and room() == "sw_pirate_deck", "east along the road to the Pirate Deck (room %s)" % room())
	var gu := npc_object("gu_in_chains")
	check(not gu.is_empty() and float(gu.get("alt", 0.0)) >= 3.0 * LV - 1.0, "Gu sits in chains on the junk's deck, three levels over the quay (%s)" % str(gu.get("alt", "-")))
	check(talk_choose("gu_in_chains", "effects", "Break his chains") and c().quests.has_flag("gu_freed") and c().inventory.count("black_ledger") >= 1,
		"Gu freed on the deck, the Black Ledger his price")
	var box := interact("pirate_strongbox")
	check(box.get("ok", false) and _alt("pirate_strongbox") >= 4.0 * LV - 1.0, "the pirates' strongbox opened on the stern castle (alt %.0f; %s)" % [_alt("pirate_strongbox"), str(box)])
	_done("the_skyport_wreck", "the Black Ledger kept")
	_whole()

# ------------------------------------------------------------------ 3: Lu's Last Page, Stars Beyond (chapter 16)
func _riven_peak() -> void:
	_story_to(16)
	_realm("sage_sovereign_2")
	_take("lus_last_page")
	check(go("east") and room() == "sw_riven_peak", "on east and up to the Riven Peak (room %s)" % room())
	var page := interact("journal_riven")
	check(page.get("ok", false) and c().quests.has_flag("journal_riven") and _alt("journal_riven") >= 2.0 * LV - 1.0,
		"Lu's last page taken on the knoll where the stars are clearest (%s)" % str(page))
	var steps := _steps("lus_last_page")
	check(steps.size() >= 2 and int(steps[0]) >= 1 and int(steps[1]) >= 1, "Lu's Last Page: the peak climbed and the page found (%s)" % str(steps))
	_finish("lus_last_page")   # its last step is Trial Master Wen's, in the Trial Hall off the grid
	Unlocks.force_unlock(c().id, "star_charting")
	var sight := interact("sight_riven_b")
	check(sight.get("ok", false) and _alt("sight_riven_b") >= 5.0 * LV - 1.0, "a star reading taken at the stone on the peak's highest crag (alt %.0f; %s)" % [_alt("sight_riven_b"), str(sight)])
	_take("stars_beyond")
	_give("star_chart_lantern")   # charted at a chart table, off the grid
	check(go("east") and room() == "sw_starsea_launch", "east to the Starsea Launch (room %s)" % room())
	talk("launch_warden_he")
	var ring := interact("launch_ring")
	check(ring.get("ok", false) and _alt("launch_ring") >= 2.0 * LV - 1.0, "the launch ring stands on its dais over the terrace (alt %.0f)" % _alt("launch_ring"))
	_done("stars_beyond", "Warden He asked where the ring points")

# ------------------------------------------------------------------ 4: The Lantern Run, Crystal and Jade (chapter 17)
func _lanternfall() -> void:
	_story_to(17)
	_realm("sage_sovereign_3")
	_take("the_lantern_run")
	check(_load("lh_arrival_quay"), "the Lantern Run makes port at the Arrival Quay, on the grid (room %s)" % room())
	talk("harbormaster_lin")
	GameEvents.flush()
	check(c().quests.is_done("the_lantern_run"), "The Lantern Run: reported to the harbourmaster on the quay, done")
	_take("crystal_and_jade")
	check(_gated("warden_skiff") == not TopdownRoom.has_layout("wc_citadel_gate"),
		"the Wardens' skiff to the Citadel is closed by the prototype's gate while the Citadel has no layout")
	check(go("east") and room() == "lh_harbor_market", "east along the quay to the Harbor Market (room %s)" % room())
	talk("clerk_yu")
	Unlocks.force_unlock(c().id, "currency_exchange")
	var ex := interact("exchange_lh")
	check(str(ex.get("open_page", "")) == "exchange", "the exchange counter by Clerk Yu opens the exchange (%s)" % str(ex))
	_used("exchange")   # the exchange's page is the HUD's
	check(_gated("lantern_stair") == not TopdownRoom.has_layout("lt_wick_gate"),
		"the stair to the Lantern Heart is closed by the prototype's gate while it has no layout")
	check(go("chandlery_door") and room() == "lh_star_chandlery", "in through the Star Chandlery's door (room %s)" % room())
	Unlocks.force_unlock(c().id, "alchemy")
	var furnace := interact("furnace_lh")
	check(str(furnace.get("open_page", "")) == "alchemy", "Chandler Shu's furnace opens alchemy (%s)" % str(furnace))
	check(not talk("lanternwright_han").is_empty(), "a word with Lanternwright Han at his bench")
	check(go("entry") and room() == "lh_harbor_market" and go("inn_door") and room() == "lh_tidelight_inn",
		"out to the street and in through the Tidelight Inn's door (room %s)" % room())
	check(not talk("innkeeper_fei").is_empty(), "a word with Innkeeper Fei at her counter")
	check(go("entry") and room() == "lh_harbor_market" and go("west") and room() == "lh_arrival_quay", "back out and west to the quay (room %s)" % room())
	talk("warden_xiao")
	_done("crystal_and_jade", "the exchange found, the Warden met")

# ------------------------------------------------------------------ 5: the Drifting Shoals (chapter 17)
func _shoals() -> void:
	_take("salt_of_the_stars")
	for i in 4: _used("attune_jade")   # the jades' attunement is the Character page's
	check(go("east") and room() == "lh_harbor_market" and go("east") and room() == "dr_jellyfish_shallows",
		"through the market and on east into the Jellyfish Shallows (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var wading := 0
	for y in grid.h:
		for x in grid.w:
			if grid.paint_at(x, y) == "h": wading += 1
	check(wading > 200, "the shallows between the islets are a floor a body wades (%d cells)" % wading)
	check(fight("star_jellyfish", 6, 300.0) >= 6, "the star jellyfish thinned wading the shallows, on the grid")
	_done("salt_of_the_stars", "the jellyfish thinned, the shards gathered")
	check(go("east") and room() == "dr_moored_hulks", "on east to the Moored Hulks (room %s)" % room())
	_realm("will_manifest_1")
	_take("will_manifest")
	_done("will_manifest", "Will Manifest reached by Old Bo's fire")
	var beds := [_alt("bed_dr_0"), _alt("bed_dr_1"), _alt("shrine_dr_hulks")]
	check(beds.all(func(a): return a >= 2.0 * LV - 1.0), "Old Bo's planters and the shrine stand on his hulk's deck (%s)" % str(beds))
	check(not talk("hulk_keeper_bo").is_empty(), "a word with Old Bo")
	_take("a_presence_of_ones_own")
	_used("presence")
	check(go("east") and room() == "dr_sparrow_reefs", "on east to the Sparrow Reefs (room %s)" % room())
	check(fight("comet_sparrow", 5, 300.0) >= 5, "the comet sparrows hunted among the reefs, on the grid")
	var steps := _steps("a_presence_of_ones_own")
	check(steps.size() >= 2 and int(steps[1]) >= 5, "A Presence of One's Own: the sparrows hunted (%s)" % str(steps))
	_finish("a_presence_of_ones_own")   # Presence's training is the HUD's
	check(go("east") and room() == "dr_driftglass_bank", "on east to the Driftglass Bank (room %s)" % room())
	Unlocks.force_unlock(c().id, "insight_sites")
	var lens := interact("insight_star")
	check(lens.get("ok", false), "the driftglass lens on the bank answers (%s)" % str(lens))

# ------------------------------------------------------------------ 6: Blackmast Haven (chapter 18)
func _blackmast() -> void:
	_story_to(18)
	_realm("will_manifest_1")
	_take("the_pursers_ledger")
	check(_load("lh_arrival_quay"), "back at the Arrival Quay (room %s)" % room())
	talk("harbormaster_lin")
	for step_to in [["east", "lh_harbor_market"], ["east", "dr_jellyfish_shallows"], ["east", "dr_moored_hulks"], ["east", "dr_sparrow_reefs"],
			["east", "dr_driftglass_bank"], ["east", "bm_blackmast_docks"]]:
		if not go(str(step_to[0])) or room() != str(step_to[1]): break
	check(room() == "bm_blackmast_docks", "on foot east from the harbour through the Shoals to the Blackmast Docks (room %s)" % room())
	check(fight("starsea_pirate", 6, 300.0) >= 6, "the Admiral's pirates cut down on the docks, on the grid")
	talk("deckhand_mo")
	_done("the_pursers_ledger", "Deckhand Mo found")
	_realm("will_manifest_2")   # the battery's last step, a breakthrough
	_take("gunners_battery")
	check(go("east") and room() == "bm_gunners_battery", "east to the Gunners' Battery (room %s)" % room())
	var spiked := 0
	for i in 3:
		if interact("cannon_%d" % i).get("ok", false) and c().quests.has_flag("cannon_spiked_%d" % i): spiked += 1
	var rows: Array = [0, 1, 2].map(func(i): return _cell("cannon_%d" % i).y)
	check(spiked == 3, "the battery's three cannons spiked behind the parapet (rows %s)" % str(rows))
	check(fight("pirate_gunner", 4, 300.0) >= 4, "the Admiral's gunners silenced, on the grid")
	c().quests.flags["seen_bm_gunners_battery_cove"] = true   # Spirit Sense shows the crack (a test shortcut)
	check(go("cove") and room() == "bm_smugglers_cove", "through the crack at the cliff's foot into the Smugglers' Cove (room %s)" % room())
	var purser := npc_object("gu_the_purser")
	check(not purser.is_empty() and float(purser.get("alt", 0.0)) >= LV - 1.0, "Gu, the purser now, hides on the ledge at the cave's back (%s)" % str(purser.get("alt", "-")))
	talk("gu_the_purser")
	check(go("entry") and room() == "bm_gunners_battery", "back out to the battery (room %s)" % room())
	_done("gunners_battery", "the battery silenced, the purser found")
	_take("the_admiral")
	check(go("east") and room() == "bm_flagship_deck", "up the gangway to the Flagship Deck (room %s)" % room())
	step(1.0)
	var voss := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "admiral_voss")
	check(voss.size() == 1 and Game.room_rt.topdown.standable(TopdownRoom.cell_of(voss[0].spawn_point)), "Admiral Voss waits on his open deck")
	check(_boss("admiral_voss") >= 1, "Admiral Voss defeated on his flagship's deck")
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	GameEvents.flush()
	_done("the_admiral", "the Admiral's seal taken")
	var chest := interact("chest_1")
	check(chest.get("ok", false), "the Admiral's strongbox opened at the bow (%s)" % str(chest))

# ------------------------------------------------------------------ 7: the Wyrmnest Isles (chapter 19)
func _wyrmnest() -> void:
	_story_to(19)
	_realm("will_manifest_2")
	_take("star_tier_beasts")
	check(_load("dr_moored_hulks"), "back at the Moored Hulks (room %s)" % room())
	check(go("wyrm_skiff") and room() == "wn_nest_cliffs", "the skiff from the hulks' pier to the Nest Cliffs (room %s)" % room())
	var at := TopdownRoom.cell_of(st.plane)
	check(at.x <= 8 and at.y >= 20, "set down on the Nest Cliffs' pier by its skiff (at %s)" % str(at))
	check(not talk("tamer_qiu").is_empty(), "a word with Tamer Qiu by the shrine")
	_finish("star_tier_beasts")   # taming is the Spirit Animals page's
	_take("a_hollowed_brood")
	check(go("east") and room() == "wn_eggshell_terraces", "east to the Eggshell Terraces (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var pools: Array = Game.room_rt.topdown.def.get("areas", []).filter(func(a): return str(a.get("kind", "")) == "hollow_puddle")
	var dry := pools.all(func(a):
		var r: Array = a.rect
		for y in range(int(r[1]), int(r[1]) + int(r[3])):
			for x in range(int(r[0]), int(r[0]) + int(r[2])):
				if not grid.standable(Vector2i(x, y)): return false
		return true)
	check(pools.size() == 3 and dry, "the Hollowed brood's three grey puddles lie on the terraces' floor, the layout's areas (%d)" % pools.size())
	check(fight("hollowed_wyrmling", 6, 300.0) >= 6, "the Hollowed wyrmlings put to rest on the terraces, on the grid")
	var incense: int = c().inventory.first_index("lantern_incense")
	check(incense >= 0 and submit({"type": "use_item", "index": incense, "confirm": true}).get("ok", false), "Lantern Incense burned to draw the grey out")
	_done("a_hollowed_brood", "the brood put to rest")
	_take("the_last_egg")
	check(go("east") and room() == "wn_guardians_crown", "east to the Guardian's Crown (room %s)" % room())
	var chest := interact("chest_8")
	check(chest.get("ok", false) and _alt("chest_8") >= 4.0 * LV - 1.0, "the guardians' chest opened on the crown's summit (alt %.0f)" % _alt("chest_8"))
	check(go("cave") and room() == "wn_hatching_cave", "through the cleft in the cliff into the Hatching Cave (room %s)" % room())
	check(_boss("nest_guardian") >= 1, "the Brood Guardian defeated before the nest")
	var egg := _cell("last_egg")
	var got := interact("last_egg")
	check(got.get("ok", false) and c().inventory.count("wyrm_egg") >= 1 and _alt("last_egg") >= LV - 1.0,
		"the last star-wyrm egg taken beside its nest on the hollow (at %s; %s)" % [str(egg), str(got)])
	_used("egg_incubated")   # the egg's warming is the Spirit Animals page's
	_done("the_last_egg", "the last egg warmed")
	check(go("entry") and room() == "wn_guardians_crown", "out of the cave to the crown (room %s)" % room())

# ------------------------------------------------------------------ 1, over the twenty rooms
func _the_rooms() -> void:
	var missed := SKY_ROOMS.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of the sky-sea zones was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
