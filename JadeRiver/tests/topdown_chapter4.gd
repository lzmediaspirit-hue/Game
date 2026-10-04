extends "res://tests/prologue_run.gd"
## topdown_chapter4 (R1, the room engine's main-path batch; docs/architecture/room_engine.md): chapter 4 of the story
## played on the height grid by a top-down character, through the rooms the room engine laid out from the side view on
## the road east past the Marsh Edge: the Grey Pools, the Sunken Causeway, the Whispering Bamboo, the Thicket Heart,
## the Falls Pool, the Pilgrim Stairs and the Cleansing Summit, and the rooms beside that road (the Hermit's Stilt
## House, Greyreed Hamlet, Behind the Falls). Test shortcuts carry a new character to chapter 4's door (the story
## before it done, a Jade Sect disciple at Qi Kindling 9, a sturdy body, so the fights are the rooms' and not the
## balance's). From there it is played through the World authority, as topdown_chapter3 plays chapter 3:
##   1. each room is entered on the grid through its ways from the room before, and the top-down
##      view builds it: a figure for every person and thing, a mark for every way;
##   2. in each, auto-path (TopdownRoute.reach: a hop up a level, no running jump over a gap) reaches every NPC, object,
##      herb, place and way from the room's spawn and from every way in;
##   3. the story: Toward Cleansing Peak from Elder Hu, walked from his peak through the marsh, the grove and Crane Falls
##      to the Pilgrim Stairs, three Stone Guardians, handed in; The Rite, Heaven's Cleansing passed in the summit's rite
##      circle (its guardians called to the summit's south rim), handed in; the tracker leading into these rooms;
##   4. beside the road: the hermit's house up its boardwalk, Lu's journal page behind the falls (a hidden way shown),
##      and Greyreed Hamlet's Grey Roofs (the grey lanterns cleansed on the hall's and the granary's roofs, reached up
##      their crate stacks) and Cleansing the Well;
##   5. past chapter 4 the story waits on The Shrine Surfaces, played at the Drowned Shrine on the grid, and every way
##      out of these rooms leads into a room laid out on the grid (decision 41's gate went in S12a).
## Run headless:  godot --headless --path . res://tests/topdown_chapter4.tscn [-- --verbose]

const ROOMS := ["rm_grey_pools", "rm_sunken_causeway", "bg_whispering_bamboo", "bg_thicket_heart", "cf_falls_pool", "cp_pilgrim_stairs",
	"cp_cleansing_summit"]
const ASIDE := ["rm_hermit_stilt_house", "cf_behind_falls", "gh_hamlet_square"]
const BEFORE := ["prologue", "main"]   # the story's kinds done before chapter 4 (a test shortcut)
const CHAPTER4 := ["toward_cleansing_peak", "the_rite"]

var entered := {}            # room -> on the grid when entered
var walk_misses: Array = []  # what auto-path does not reach, by room
var view_misses: Array = []  # what the view did not build, by room
var probe: TopdownWorld = null

func _main() -> void:
	start_new("ch4/")
	_to_chapter4()
	GameEvents.event.connect(_on_room)
	_toward_cleansing_peak()
	_the_rite()
	_beside_the_road()
	_the_rooms()
	_past_the_chapter()
	if is_instance_valid(probe): probe.free()
	end_suite()

# ------------------------------------------------------------------ the shortcut to chapter 4
## The story before chapter 4 done (its prologue and main quests to Gu's Cargo, the lessons on the way), the prologue's
## systems and scenes, a Jade Sect disciple at Qi Kindling 9 with a sturdy body (a test shortcut: the walk is about the
## rooms), on Elder Hu's peak.
func _to_chapter4() -> void:
	var cid: String = c().id
	Unlocks.grant_prologue(cid)
	c().quests.flags["prologue_done"] = true
	c().quests.flags["night_survived"] = true   # the Hollow Night's, which opens Lotus Ferry's west gate both ways
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c().training_sect = {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		var kind := str(q.get("kind", ""))
		if (kind in BEFORE and not str(q.id) in CHAPTER4 and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 3))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("qi_kindling_9")
	c().set_meta("extra_modifiers", [{"stat": "physical_attack", "op": "flat", "value": 1500.0, "source": "test:sturdy"},
		{"stat": "max_hp", "op": "flat", "value": 20000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 800.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "ja_elder_hu_peak", "")
	GameEvents.flush()
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "ja_elder_hu_peak" and Game.room_rt.topdown != null and ProgressionRules.at_least(c().cultivator.realm_key, "qi_kindling_9"),
		"at chapter 4's door: Elder Hu's peak on the grid, Qi Kindling 9 (room %s, realm %s)" % [room(), c().cultivator.realm_key])

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
	if not (rid in ROOMS or rid in ASIDE) or entered.has(rid): return
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
	# A person hidden at this hour or by the story (the hamlet's trader before Market Day) has no figure while hidden.
	var shown: Array = npcs.filter(func(o): return Game.world.object_visible(c(), o))
	var ok: bool = probe.room == Game.room_rt.topdown and probe.npc_views.size() >= shown.size() and probe.object_views.size() == things.size() \
		and figures.size() >= shown.size() + things.size() and probe.portal_views.size() == (def.get("portals", []) as Array).size() \
		and marks.size() == probe.portal_views.size()
	if not ok: view_misses.append("%s: npcs %d/%d things %d/%d figures %d ways %d/%d marks %d" % [rid, probe.npc_views.size(), shown.size(),
		probe.object_views.size(), things.size(), figures.size(), probe.portal_views.size(), (def.get("portals", []) as Array).size(), marks.size()])

# ------------------------------------------------------------------ 3: the story
## A quest's steps done, waiting to be handed in.
func _steps_done(q: String) -> bool:
	return str(c().quests.active.get(q, {}).get("state", "")) == "ready"

## The tracker's entry for `quest` leads to `target`, a room on the grid.
func _leads(quest: String, target: String) -> bool:
	for e in Game.quest.tracker(c()):
		if str(e.get("quest", "")) == quest: return str(e.get("target_room", "")) == target and TopdownRoom.has_layout(target)
	return false

func _toward_cleansing_peak() -> void:
	var waiting: Array = Game.quest.story_waiting(c(), QuestAuthority.STORY_KINDS)
	check(not waiting.is_empty() and str(waiting[0].id) == "toward_cleansing_peak" and TopdownRoom.has_layout(str(waiting[0].get("target_room", ""))),
		"chapter 4's first quest, Toward Cleansing Peak, waits on the grid (%s)" % str(waiting.slice(0, 1).map(func(q): return str(q.id))))
	accept("elder_hu", "toward_cleansing_peak")
	check(_leads("toward_cleansing_peak", "cp_pilgrim_stairs"), "Toward Cleansing Peak leads to the Pilgrim Stairs, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 1)))
	# The road east, room by room: down from the sect to the Marsh Edge, through the Grey Pools and over the Sunken
	# Causeway, through the Bamboo Grove to Crane Falls, and up to the Pilgrim Stairs.
	var rooms: Array = []
	for rid in ["rm_marsh_edge"] + ROOMS.slice(0, 6):
		_whole()
		if travel(rid): rooms.append(room())
	check(rooms == ["rm_marsh_edge"] + ROOMS.slice(0, 6), "the road east walked room by room on the grid to the Pilgrim Stairs (%s)" % str(rooms))
	check(Game.room_rt.topdown != null and room() == "cp_pilgrim_stairs", "at the Pilgrim Stairs on the grid (room %s)" % room())
	check(fight("stone_guardian", 3, 600.0) >= 3, "three Stone Guardians defeated on the Pilgrim Stairs")
	_whole()
	check(_steps_done("toward_cleansing_peak") or c().quests.is_done("toward_cleansing_peak"), "Toward Cleansing Peak's steps done")
	check(travel("ja_elder_hu_peak"), "back to Elder Hu on his peak (room %s)" % room())
	hand_in("elder_hu", "toward_cleansing_peak")

func _the_rite() -> void:
	accept("elder_hu", "the_rite")
	check(_leads("the_rite", "cp_cleansing_summit"), "The Rite leads to the Cleansing Summit, on the grid (%s)" % str(Game.quest.tracker(c()).slice(0, 1)))
	check(travel("cp_cleansing_summit") and Game.room_rt.topdown != null, "up the Pilgrim Stairs to the Cleansing Summit, on the grid (room %s)" % room())
	var won := {"ok": false}
	var heard := func(n: String, p: Dictionary): if n == "room_event_completed" and str(p.get("event", "")) == "heavens_cleansing": won.ok = true
	GameEvents.event.connect(heard)
	var began := interact("rite_cleansing")
	check(began.get("ok", false) and Game.room_rt.event.get("active", false), "the rite circle begins Heaven's Cleansing (%s)" % str(began))
	# The guardians it calls stand on the summit's south rim, on the grid (the side view's points, read as cells).
	var spawned: Array = []
	for i in 50:
		_whole()
		step(1.0)
		for e in Game.room_rt.living_enemies():
			if e.def_id == "stone_guardian" and not spawned.has(e.uid): spawned.append(e.uid)
		if not Game.room_rt.event.get("active", false): break
	GameEvents.event.disconnect(heard)
	var grid: TopdownRoom = Game.room_rt.topdown
	check(not spawned.is_empty(), "Heaven's Cleansing calls its Stone Guardians onto the summit (%d)" % spawned.size())
	check(won.ok, "Heaven's Cleansing is won, its time out with the body standing")
	check(_steps_done("the_rite") or c().quests.is_done("the_rite"), "Heaven's Cleansing passed in the summit's rite circle (the rite %s)" % str(c().quests.active.get("the_rite", {})))
	check(grid.standable(TopdownRoom.cell_of(Vector2(300, 860))) and grid.standable(TopdownRoom.cell_of(Vector2(1000, 860))),
		"the rite's guardians are called to open ground on the summit's rim")
	_whole()
	check(travel("ja_elder_hu_peak"), "back down to Elder Hu (room %s)" % room())
	hand_in("elder_hu", "the_rite")
	check(CHAPTER4.all(func(q): return c().quests.is_done(q)), "chapter 4 done on the grid")

# ------------------------------------------------------------------ 4: beside the road
func _beside_the_road() -> void:
	# The hermit's house, up the boardwalk from the Sunken Causeway.
	check(travel("rm_hermit_stilt_house") and Game.room_rt.topdown != null, "up the boardwalk to the Hermit's Stilt House (room %s)" % room())
	check(not npc_object("hermit_yao").is_empty(), "Hermit Yao keeps at the foot of his ladder")
	# Behind the Falls: the hidden way shown (Spirit Sense's flag, a test shortcut), Lu's journal page on the low ledge.
	Game.quest.apply_flag(c().id, "seen_cf_falls_pool_behind")
	check(travel("cf_behind_falls") and Game.room_rt.topdown != null, "in behind Crane Falls by the ledge at the cliff's foot (room %s)" % room())
	var page := interact("journal_falls")
	check(page.get("ok", false) and c().inventory.count("lu_journal_page") >= 1, "Lu's journal page taken from the low ledge behind the falls (%s)" % str(page))
	# Greyreed Hamlet opens at Heart Tempering 1 (a test shortcut): Grey Roofs and Cleansing the Well.
	_realm("heart_tempering_1")
	check(travel("gh_hamlet_square") and Game.room_rt.topdown != null, "north over the Grey Pools' boardwalk into Greyreed Hamlet (room %s)" % room())
	# Grey Roofs is the hamlet's roofs (E5b: the Grey Pools' Hollowed, Levels 7 to 12, were far under its realm).
	accept("hamlet_elder_gao", "grey_roofs")
	for f in ["grey_lantern_hall", "grey_lantern_granary"]:
		var o: Dictionary = Game.room_rt.object_def(f)
		var r := interact(f)
		check(r.get("ok", false) and c().quests.has_flag(f) and st.altitude >= 63.0,
			"the grey lantern %s cleansed on its roof, reached up the crate stack (%s; at %.0f)" % [f, str(r), st.altitude])
	hand_in("hamlet_elder_gao", "grey_roofs")
	accept("hamlet_elder_gao", "cleansing_the_well")
	var well := interact("well_cleanse")
	check(well.get("ok", false) and c().quests.has_flag("well_cleansed"), "the hamlet's well cleansed in the square (%s)" % str(well))
	hand_in("hamlet_elder_gao", "cleansing_the_well")

# ------------------------------------------------------------------ 1, 2: over the rooms
func _the_rooms() -> void:
	var missed := (ROOMS + ASIDE).filter(func(r): return not entered.get(r, false))
	check(missed.is_empty(), "every room of chapter 4's road and beside it was entered on the grid (%d; missed %s)" % [entered.size(), str(missed)])
	check(walk_misses.is_empty(), "in every room of chapter 4 auto-path reaches every thing and way from the spawn and every way in (%s)" % str(walk_misses.slice(0, 6)))
	check(view_misses.is_empty(), "the top-down view built every room of chapter 4: a figure for each person and thing, a mark for each way (%s)" % str(view_misses.slice(0, 4)))

# ------------------------------------------------------------------ 5: past chapter 4
func _past_the_chapter() -> void:
	var waiting: Array = Game.quest.story_waiting(c(), QuestAuthority.STORY_KINDS)
	check(not waiting.is_empty() and str(waiting[0].id) == "the_shrine_surfaces" and TopdownRoom.has_layout("ds_flooded_gate"),
		"past chapter 4 the story waits on The Shrine Surfaces, the Drowned Shrine on the grid (%s)" % str(waiting.slice(0, 1).map(func(q): return str(q.id))))
	# Every way out of these rooms leads into a room laid out on the grid.
	var wrong: Array = []
	for rid in ROOMS + ASIDE:
		Game.world.load_room(c(), rid, "")
		GameEvents.flush()
		for p in Game.room_rt.def.get("portals", []):
			if not TopdownRoom.has_layout(str(p.get("to", ""))): wrong.append("%s:%s" % [rid, str(p.id)])
	check(wrong.is_empty(), "every way out of chapter 4's rooms leads into a room laid out on the grid (wrong %s)" % str(wrong.slice(0, 4)))
