extends "res://tests/prologue_run.gd"
## topdown_sunscar (R7, the room engine's Act II batch; docs/architecture/room_engine.md, "Nine Peaks to the Tomb of
## Sunscar (R7)"): chapters 13 and 14 played on the height grid by a top-down character, through the twenty rooms the
## room engine laid out from the side view: Nine Peaks (the Alliance Gate, the Hall of Nine, the Auction Pavilion, the
## Presence Terrace, the Trial Hall), the Gale Canyons (the Canyon Mouth, the Kite Winds, the Harpy Roosts, the
## Windbridge), Ironroot Hold (the Hold Gate, the Clan Hearth, the Ancestor Hall), the Sunscar Desert (the Glass Dunes,
## the Scorpion Flats, the Oasis of Bones, the Worm Sea) and the Tomb of Sunscar (the Sealed Gate, the Hall of Sand
## Kings, the Mirror Crypt, the Throne of the Tomb King). Test shortcuts carry a new character there (the story before
## chapter 13 done, Sage 2, a sturdy body with a scholar's Insight, so the fights are the rooms' and not the balance's)
## and set it down off the sky-ship at the Alliance Gate (that way open, Cloudgate Port's Skydock on the grid). From
## there it is played through the World authority, as topdown_peaks plays the peaks:
##   1. each room is entered on the grid through its ways from the room before, and the top-down view builds it: a
##      figure for every person and thing, a mark for every way;
##   2. in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump over a gap) reaches every NPC, object,
##      herb, place and way from the room's spawn and from every way in;
##   3. chapter 13: Nine Seats (the envoy heard, an Alliance seat taken, Elder Zhong), the Auction Pavilion's block, the
##      Trial Hall and back, The Canyon Toll (the tollkeeper, the veiled brigands broken across the canyons, over the
##      Windbridge to the Hold), Ironroot Blood (the warden's test of root, the Matriarch, the Ancestor Hall's tablets);
##   4. chapter 14: Glass and Bone (the desert road, the Scorpion Flats' scorpions, the bone-reader at the oasis), The
##      Sealed Gate (the dune worms' shards of the sun seal, the portal in the Worm Sea, the gate's lock read), Sovereign,
##      and The Tomb King (the Hall of Sand Kings, Lu's page in the Mirror Crypt, the Tomb King on his throne, the sun
##      seal kept from the Grey Pilgrim, the old stair out to the Worm Sea).
## The side view's mechanics with no top-down counterpart yet (the canyons' wind gusts and kite updrafts, the Windbridge's
## no-flight rule, the quicksand's pull) are T1's: the walk crosses those rooms on foot.
## Run headless:  godot --headless --path . res://tests/topdown_sunscar.tscn [-- --verbose]

const PEAKS := ["np_alliance_gate", "np_hall_of_nine", "np_auction_pavilion", "np_presence_terrace", "np_trial_hall"]
const CANYONS := ["gc_canyon_mouth", "gc_kite_winds", "gc_harpy_roosts", "gc_windbridge"]
const HOLD := ["ir_hold_gate", "ir_clan_hearth", "ir_ancestor_hall"]
const DESERT := ["sd_glass_dunes", "sd_scorpion_flats", "sd_oasis_of_bones", "sd_worm_sea"]
const TOMB := ["ts_sealed_gate", "ts_hall_of_sand_kings", "ts_mirror_crypt", "ts_throne"]
const STORY := ["nine_seats", "going_once", "the_canyon_toll", "ironroot_blood", "glass_and_bone", "the_sealed_gate",
	"sovereign", "the_tomb_king"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	start_new("sunscar/")
	_to_nine_peaks()
	_nine_peaks()
	_the_canyons()
	_the_hold()
	_the_desert()
	_the_tomb()
	_the_rooms()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to Nine Peaks
## The story before chapter 13 done (its prologue and main quests, the guided ones), the prologue's systems and scenes,
## Sage 2 with a sturdy body and a scholar's Insight (a test shortcut: the walk is about the rooms), off the sky-ship at
## the Alliance Gate.
func _to_nine_peaks() -> void:
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
		if (kind in ["prologue", "main"] and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 12))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("sage_2")
	for u in ["teleport_stones", "auction_house", "smithing", "attack", "qi_springs", "spirit_sense"]: Unlocks.force_unlock(cid, u)
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 90000.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 1500000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 50000.0, "source": "test:sturdy"},
		{"stat": "insight", "op": "flat", "value": 200.0, "source": "test:scholar"}])
	_whole()
	GameEvents.event.connect(_on_room)
	Game.world.load_room(c(), "np_alliance_gate", "ferry")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "np_alliance_gate" and Game.room_rt.topdown != null and ProgressionRules.at_least(c().cultivator.realm_key, "sage_2"),
		"off the sky-ship at the Alliance Gate, on the grid, Sage 2 (room %s, realm %s)" % [room(), c().cultivator.realm_key])
	check(_leads_on("ferry"),
		"the Alliance Gate's sky-ship leads back to Cloudgate Port's Skydock, on the grid")

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
	if not rid in PEAKS + CANYONS + HOLD + DESERT + TOMB or entered.has(rid): return
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

## The tracker's entry for `quest` leads to `target`, a room on the grid.
func _leads(quest: String, target: String) -> bool:
	for e in Game.quest.tracker(c()):
		if str(e.get("quest", "")) == quest: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target)
	return false

## The way `pid` of this room leads into a room laid out on the grid, as every room is (decision 41's gate, which shut a
## way into a room with no layout yet, went in S12a).
func _leads_on(pid: String) -> bool:
	return TopdownRoom.has_layout(str(Game.room_rt.portal_def(pid).get("to", "")))

## Walk room by room to `target`; the rooms passed, in order.
func _walk(target: String) -> Array:
	var rooms: Array = [room()]
	_whole()
	if travel(target): rooms.append(room())
	return rooms

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

# ------------------------------------------------------------------ 3: chapter 13
func _nine_peaks() -> void:
	# Nine Seats: the Hall of Nine, the envoy heard, an Alliance seat taken, Elder Zhong.
	_start("nine_seats")
	check(_leads("nine_seats", "np_hall_of_nine"), "Nine Seats leads to the Hall of Nine, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	check(travel("np_hall_of_nine") and Game.room_rt.topdown != null, "east from the Alliance Gate to the Hall of Nine, on the grid (room %s)" % room())
	var heard := talk("envoy_lanshi")
	var seat := talk_choose("envoy_lanshi", "effects", "Alliance seat")
	check(not heard.is_empty() and seat and c().quests.has_flag("path_alliance") and _steps_done("nine_seats"),
		"Nine Seats: the envoy heard before the Hall of Nine and an Alliance seat taken (%s)" % str(c().quests.active.get("nine_seats", {})))
	hand_in("elder_zhong", "nine_seats")
	# The Auction Pavilion: its door off the court, the block opens the auction's page.
	var into := go("pavilion_door")
	var block := interact("auction_block")
	check(into and room() == "np_auction_pavilion" and Game.room_rt.topdown != null and block.get("ok", false) and str(block.get("open_page", "")) == "auction",
		"through the Auction Pavilion's door on the grid, the auction block opens the auction (room %s; %s)" % [room(), str(block)])
	check(go("entry") and room() == "np_hall_of_nine", "out of the Auction Pavilion back to the Hall of Nine (room %s)" % room())
	# The Presence Terrace and its Trial Hall.
	check(travel("np_presence_terrace") and Game.room_rt.topdown != null, "east to the Presence Terrace, on the grid (room %s)" % room())
	var trial := go("trial_door")
	check(trial and room() == "np_trial_hall" and Game.room_rt.topdown != null and go("entry") and room() == "np_presence_terrace",
		"into the Trial Hall off the Presence Terrace and back, on the grid (room %s)" % room())

func _the_canyons() -> void:
	# The Canyon Toll: the tollkeeper, the veiled brigands broken, over the Windbridge to the Hold.
	_start("the_canyon_toll")
	check(_leads("the_canyon_toll", "gc_canyon_mouth"), "The Canyon Toll leads to the Canyon Mouth, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	check(travel("gc_canyon_mouth") and Game.room_rt.topdown != null, "down the Presence Terrace's road to the Canyon Mouth, its toll open now (room %s)" % room())
	var toll := talk("tollkeeper_bai")
	check(not toll.is_empty(), "the tollkeeper asked at the Canyon Mouth who pays in shards")
	var brigands := _hunt("canyon_brigand", 6, ["gc_canyon_mouth", "gc_windbridge", "gc_canyon_mouth", "gc_windbridge"])
	check(brigands >= 6, "six veiled brigands broken in the canyons, on the grid (%d)" % brigands)
	var rooms := _walk("ir_hold_gate")
	GameEvents.flush()
	check(rooms.back() == "ir_hold_gate" and Game.room_rt.topdown != null and _steps_done("the_canyon_toll"),
		"over the Windbridge to Ironroot Hold's gate: The Canyon Toll's steps done (%s; %s)" % [str(rooms), str(c().quests.active.get("the_canyon_toll", {}))])
	hand_in("ironroot_warden", "the_canyon_toll")

func _the_hold() -> void:
	# Ironroot Blood: the warden's test of root, the Matriarch, the ancestors' tablets.
	_start("ironroot_blood")
	var won := spar_with(func(): return _spar_service("ironroot_warden"))
	check(won, "the warden's test of root won in the Hold Gate's yard, on the grid")
	check(travel("ir_clan_hearth") and Game.room_rt.topdown != null, "through the gatehouse into the Clan Hearth's cavern, on the grid (room %s)" % room())
	var met := talk("matriarch_tie")
	check(not met.is_empty(), "the Matriarch met at the Clan Hearth's fire")
	var into := go("hall_door")
	var tablets := interact("ancestral_tablets")
	GameEvents.flush()
	check(into and room() == "ir_ancestor_hall" and tablets.get("ok", false) and c().quests.has_flag("tablets_honoured"),
		"the forge's door into the Ancestor Hall, the iron-root tablets honoured (room %s; %s)" % [room(), str(tablets)])
	check(go("entry") and room() == "ir_clan_hearth", "back out to the Clan Hearth (room %s)" % room())
	check(_steps_done("ironroot_blood"), "Ironroot Blood's steps done (%s)" % str(c().quests.active.get("ironroot_blood", {})))
	hand_in("matriarch_tie", "ironroot_blood")

# ------------------------------------------------------------------ 4: chapter 14
func _the_desert() -> void:
	# Glass and Bone: the desert road, the scorpions, the bone-reader at the Oasis of Bones.
	_realm("sage_3")
	_start("glass_and_bone")
	check(_leads("glass_and_bone", "sd_oasis_of_bones"), "Glass and Bone leads down the desert road to the Oasis of Bones, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 2)))
	var rooms := [room()]
	for rid in ["sd_glass_dunes", "sd_scorpion_flats", "sd_oasis_of_bones"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["ir_clan_hearth", "sd_glass_dunes", "sd_scorpion_flats", "sd_oasis_of_bones"],
		"down the desert road over the Glass Dunes and the Scorpion Flats to the Oasis of Bones, room by room on the grid (%s)" % str(rooms))
	var stung := _hunt("sandstorm_scorpion", 6, ["sd_scorpion_flats", "sd_glass_dunes", "sd_scorpion_flats"])
	check(stung >= 6, "six sandstorm scorpions cleared from the caravan road, on the grid (%d)" % stung)
	check(travel("sd_oasis_of_bones"), "back to the Oasis of Bones (room %s)" % room())
	var read := talk("bone_reader_xiu")
	check(not read.is_empty() and _steps_done("glass_and_bone"), "the bone-reader asked about the Pilgrim's caravan (%s)" % str(c().quests.active.get("glass_and_bone", {})))
	hand_in("bone_reader_xiu", "glass_and_bone")
	# The oasis's stone attunes, its spring and shrine by the water.
	var stone := interact("stone_sunscar")
	check(stone.get("ok", false), "the Oasis of Bones' teleport stone answers on the grid (%s)" % str(stone))

func _the_tomb() -> void:
	# The Sealed Gate: the worms' shards, the portal in the Worm Sea, the lock read.
	_start("the_sealed_gate")
	var shards: int = c().inventory.count("sun_seal_shard")
	var worms := 0
	if travel("sd_worm_sea"):
		for i in 16:
			if c().inventory.count("sun_seal_shard") >= 3: break
			_whole()
			worms += fight("dune_worm", 1, 60.0)
	var got: int = c().inventory.count("sun_seal_shard") - shards
	check(room() == "sd_worm_sea" and worms >= 1 and got >= 1, "dune worms fought on the Worm Sea's grid give up the sun seal's shards (%d worms, %d shards)" % [worms, got])
	if c().inventory.count("sun_seal_shard") < 3:
		Game.inventory.apply_add(c().id, "sun_seal_shard", 3 - c().inventory.count("sun_seal_shard"), "sunscar_suite")   # a test shortcut: the dice
	GameEvents.flush()
	var down := go("tomb")
	check(down and room() == "ts_sealed_gate" and Game.room_rt.topdown != null, "down the portal half drowned in the Worm Sea's sand into the Sealed Gate, on the grid (room %s)" % room())
	var sealed: bool = not Game.world.portal_state(c(), Game.room_rt.portal_def("east")).get("open", true)
	var gate := interact("tomb_gate")
	GameEvents.flush()
	check(sealed and gate.get("ok", false) and c().quests.has_flag("tomb_gate_opened") and Game.world.portal_state(c(), Game.room_rt.portal_def("east")).get("open", false),
		"the bronze doors sealed until the sun lock is fitted and read, then open (%s)" % str(gate))
	check(_steps_done("the_sealed_gate"), "The Sealed Gate's steps done (%s)" % str(c().quests.active.get("the_sealed_gate", {})))
	check(travel("sd_oasis_of_bones"), "back up the stair and over the Worm Sea to the oasis (room %s)" % room())
	hand_in("bone_reader_xiu", "the_sealed_gate")
	# Sovereign: the breakthrough by the water (a test shortcut sets the realm).
	_start("sovereign")
	_realm("sage_sovereign_1")
	GameEvents.event.emit("realm_changed", {"actor": c().id, "realm": "sage_sovereign_1"})
	GameEvents.flush()
	if not c().quests.is_done("sovereign") and _steps_done("sovereign"): hand_in("bone_reader_xiu", "sovereign")
	check(c().quests.is_done("sovereign") or _steps_done("sovereign"), "Sovereign: Sage Sovereign 1 at the Oasis of Bones (%s)" % str(c().quests.active.get("sovereign", {})))
	# The Tomb King: the Hall of Sand Kings, Lu's page, the King on his throne, the seal kept.
	_start("the_tomb_king")
	var rooms := [room()]
	for rid in ["sd_worm_sea", "ts_sealed_gate", "ts_hall_of_sand_kings", "ts_mirror_crypt"]:
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["sd_oasis_of_bones", "sd_worm_sea", "ts_sealed_gate", "ts_hall_of_sand_kings", "ts_mirror_crypt"],
		"into the tomb through the Sealed Gate and the Hall of Sand Kings to the Mirror Crypt, room by room on the grid (%s)" % str(rooms))
	var page := interact("journal_tomb")
	GameEvents.flush()
	check(page.get("ok", false) and c().quests.has_flag("journal_tomb"), "Lu's page found at the foot of the sand king's sarcophagus (%s)" % str(page))
	_whole()
	check(travel("ts_throne") and Game.room_rt.topdown != null, "east into the Throne of the Tomb King, on the grid (room %s)" % room())
	var grid: TopdownRoom = Game.room_rt.topdown
	var king: Array = []
	for i in 20:
		king = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "tomb_king")
		if not king.is_empty(): break
		step(0.5)
	check(king.size() == 1 and grid.standable(TopdownRoom.cell_of(king[0].plane)), "the Tomb King rises on the sand floor before his throne, on the grid (%s)" % str(king.map(func(e): return e.plane)))
	for e in king: e.pools.hp = minf(e.pools.hp, e.pools.max_hp * 0.2)   # a test shortcut: the fight is the arena's, not the balance's
	check(fight("tomb_king", 1, 300.0, 0.0, true) >= 1, "the Tomb King of Sunscar defeated on his throne's floor")
	GameEvents.flush()
	check(c().inventory.count("sunscar_seal") >= 1, "the sun seal taken up from where the King fell")
	var kept := talk_choose("grey_pilgrim", "effects", "I keep the seal")
	GameEvents.flush()
	check(kept and c().quests.has_flag("seal_kept") and _steps_done("the_tomb_king"), "the seal kept from the Grey Pilgrim: The Tomb King's steps done (%s)" % str(c().quests.active.get("the_tomb_king", {})))
	var out := go("exit")
	check(out and room() == "sd_worm_sea" and Game.room_rt.topdown != null and Game.room_rt.topdown.standable(TopdownRoom.cell_of(st.plane)),
		"up the old stair out of the throne hall to the Worm Sea, on the grid (room %s)" % room())
	check(travel("sd_oasis_of_bones"), "back to the Oasis of Bones (room %s)" % room())
	hand_in("bone_reader_xiu", "the_tomb_king")

# ------------------------------------------------------------------ 1, 2: over the rooms
func _the_rooms() -> void:
	var all: Array = PEAKS + CANYONS + HOLD + DESERT + TOMB
	var missed := all.filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of Nine Peaks, the canyons, the Hold, the desert and the tomb was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))
