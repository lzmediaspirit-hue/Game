extends "res://tests/tutorial_order.gd"
## topdown_tutorial (redesign Phase 4, docs/redesign_top_down_plan.md "As built: Phase 4"): the tutorial walk of
## tests/tutorial_order.gd, every step and every invariant of it, played by a character made for the top-down world.
## Every room that has a layout (tools/data/topdown_rooms.py: the Prologue, Lotus Ferry, the Reed Shallows, the Willow
## Path and Stoneford to the Fairground, where the sect is chosen) is entered on the height grid through the World
## authority, the rest stay side-view. Phase 4's second part ("As built: Phase 4, second part") carries the grid on
## through chapter 2's first stretch: the walk's Entry Trial, the Jade Sect's grounds, the Marsh Edge's Strange Tracks
## and The Humming Token, and then, from the fair (a checkpoint kept as both recruiters are met), the same stretch as a
## Cloud Sect disciple on the Cloud Sect's grounds, with the Cloud Steps run on the grid. On top of tutorial_order's
## invariants (the HP bar before fights, doors shown, the hut door open, quest talks closing, the tracker never blank
## and leading to the real next place), held through both sects' stretches:
##   1. each room of the walk is on the grid exactly when it has a layout, and every such room of the tutorial is
##      entered on it;
##   2. each layout places every NPC, object, way and spawn of its side-view room, on a floor a body can stand on, and
##      everything is reached on foot (walking, stairs, drops, a jump a level up, a running jump over a tile) from
##      every way into the room and from where a character wakes in it;
##   3. every spot the walk stands at in a room on the grid is reached on foot from where the character came in;
##   4. the top-down view builds each room of the walk (a live TopdownWorld, the character's own view, as main.gd
##      mounts it): a figure and a label for every person, every thing, and a mark and a plate for every way;
##   5. the character's spot is saved and loaded on the grid: a save taken in a room on the grid resumes there;
##   6. every person of those rooms is drawn in the top-down style (TopdownPlaces.Person, decision 32), fully dressed,
##      and turns to the player at their side, then back to their rest;
##   7. the character's own view drives the body: a talk offered, auto-path through a door and out through an edge;
##   8. a room's people are drawn within a moment of it while the page scripts still warm up, and every way's reach
##      is turned with its direction;
##   9. every foe the rooms of the tutorial and chapter 2's stretch spawn, their events' foes too (the night's minnows
##      and eel), has its own top-down figure (every action in five drawn facings), none the view's stand-in; and
##      after The Humming Token the tracker's Next is Mei Qing's Errand at Artisan Row;
##  10. the story is staged (decision 39, data/scenes.json): every scene of the tutorial plays to its end on a
##      SceneDirector with no view as the walk comes to it, the walk's own deeds doing what its hand-offs ask (the
##      stump punched, the tea drunk, the crab driven off, the door walked through), and its cuts count on the play clock,
##      where the first hour's pacing (invariant 14) still holds;
##  11. decision 40's runtime light on every room the view builds: its cast shadows baked once as it is built and never
##      again while it plays, its particles under their caps by day and at the clock's night, and a night room lit by
##      its lanterns and doorways over the story's night, which stays night with Settings' extras off;
##  12. the end of the prototype (decision 41): the story played on to The First Current, the lessons inside the
##      prototype next, then the tracker's first entry is the prototype's end, leading nowhere, and every way off the
##      grid is closed by a gate that says why (the Marsh Edge's road east, the Trial Tower's door): no route,
##      auto-path or hop through one; the tracker never leads to herbs the player cannot pick yet.
## Run headless:  godot --headless --path . res://tests/topdown_tutorial.tscn [-- --verbose]

const TUTORIAL_ROOMS := ["lf_fishers_hut", "lf_village", "lf_old_ma_store", "lf_granny_liu_hut", "lf_reed_shallows", "lf_village_night",
	"lf_lu_boat", "wp_east", "wp_west", "sf_gate", "sf_market", "sf_artisan_row", "sf_fairground"]
## Chapter 2's stretch (Phase 4's second part), the rooms each sect's disciple walks from the sect choice to The Humming
## Token: the Entry Trial, the sect's gate, Weapon Hall, training yard and halls up to the mentor's peak, the Marsh Edge.
const CHAPTER2_ROOMS := {
	"jade": ["sf_trial_jade", "ja_gate_street", "ja_weapon_hall", "ja_pavilion_rooftops", "ja_east_terrace", "ja_herb_terraces",
		"ja_elder_hu_peak", "rm_marsh_edge"],
	"cloud": ["sf_trial_cloud", "cm_cliff_stair", "cm_sword_court", "cm_weapon_hall", "cm_array_court", "cm_elder_sung_peak", "rm_marsh_edge"]}
const FOE_ACTIONS := ["idle", "walk", "windup", "attack", "hurt", "death"]

var grid_rooms := {}          # rooms entered on the grid
var wrong_view: Array = []    # rooms entered in the other view than their layout says
var far: Array = []           # spots stood at that are not reached on foot from where the room was entered
var reach_here := {}          # cell -> true: reached on foot from where the character came into this room
var reach_room := ""
var probe: TopdownWorld = null
var probe_misses: Array = []
var people_misses: Array = []   # people not drawn in the top-down style, or wearing a piece with no top-down layer
var light_misses: Array = []    # decision 40: a room baked more than once, particles over a cap, a night without its lights
var light_rooms := 0
var night_rooms := 0

func _main() -> void:
	add_child(views)
	create_extra = {"view": "topdown"}
	GameEvents.event.connect(_on_grid_event)
	await _people_stream()
	scene_director = SceneDirector.new()
	scene_director.pages_override = false
	add_child(scene_director)
	scene_director.set_process(false)
	_layouts()
	run()
	_chapter2()
	_to_the_gate()
	_scenes_played()
	_save_on_the_grid()
	_walk_on_the_grid()
	check(wrong_view.is_empty(), "every room of the walk was on the grid exactly when it has a layout (%s)" % str(wrong_view))
	var missed := TUTORIAL_ROOMS.filter(func(r): return not grid_rooms.has(r))
	check(missed.is_empty(), "every room of the tutorial to the sect choice was played on the grid (%d rooms; missed %s)" % [grid_rooms.size(), str(missed)])
	for sid in CHAPTER2_ROOMS:
		missed = CHAPTER2_ROOMS[sid].filter(func(r): return not grid_rooms.has(r))
		check(missed.is_empty(), "every room of chapter 2's stretch for a %s disciple was played on the grid (missed %s)" % [sid, str(missed)])
	check(far.is_empty(), "every spot the walk stood at on the grid is reached on foot from where it came in (%s)" % str(far.slice(0, 8)))
	check(probe_misses.is_empty(), "the top-down view built every room of the walk: a figure and a label for each person and thing, a mark and a plate for each way (%s)" % str(probe_misses.slice(0, 6)))
	check(people_misses.is_empty(), "every person of the walk's rooms on the grid is drawn in the top-down style, every piece of their outfit with its layer (%s)" % str(people_misses.slice(0, 6)))
	check(light_rooms >= TUTORIAL_ROOMS.size() and night_rooms >= 1 and light_misses.is_empty(),
		"decision 40: every room the view built (%d, %d at night) baked its cast shadows once and never while it played, kept its particles under their caps by day and by night, and a night room is lit by its lights, and stays night with the extras off (%s)" % [light_rooms, night_rooms, str(light_misses.slice(0, 6))])
	if is_instance_valid(probe): probe.free()
	free_hud_probe()
	end_suite()

# ------------------------------------------------------------------ 10: the staged scenes
## Each step of the walk comes to the stage: what a scene staged is played out before the walk goes on (as a cut holds
## the player in the game), and a hand-off waits for the walk's next deed.
func submit(i: Dictionary) -> Dictionary:
	settle_scenes()
	var r := super(i)
	settle_scenes()
	return r

func hit_object(id: String, times: int) -> void:
	settle_scenes()
	super(id, times)
	settle_scenes()

func _watch_fight() -> void:
	super()
	scene_director.advance(0.05)
	settle_scenes()

## Every scene of the tutorial was played to its end, none skipped; the stage is clear.
func _scenes_played() -> void:
	var done := {}
	for f in scene_director.finished: done[str(f.scene)] = not f.skipped
	var missed: Array = ContentDB.all("scenes").filter(func(r): return r.get("tutorial", false) and not done.get(str(r.id), false)).map(func(r): return str(r.id))
	check(missed.is_empty() and scene_director.run == null, "every staged scene of the tutorial played to its end as the walk came to it (%d played; missed %s)" % [done.size(), str(missed)])
	check(not Game.paused, "no scene holds the game still after the walk")

# ------------------------------------------------------------------ 9: chapter 2's stretch, for both sects
## Past tutorial_order's walk (the Jade Sect's, to Strange Tracks): The Humming Token. Then the same stretch as a Cloud
## Sect disciple, from the fair: the checkpoint kept as both recruiters were met, the Cloud Sect joined, its Entry Trial,
## Shen Lian's spar, the chores on the Cliff Stair, the Cloud Steps, its Weapon Hall, Strange Tracks for Elder Sung on
## his far peak and The Humming Token; the walk's invariants after every step and over the whole of it.
func _chapter2() -> void:
	step_humming_token()
	invariants("The Humming Token")
	step_mei_qing()
	invariants("Mei Qing's Errand")
	step_grey_at_the_edges()
	invariants("Grey at the Edges")
	check(resume_checkpoint(run_root() + "cp/fair/", run_root() + "cloud/"), "back at the fair from the checkpoint kept as both recruiters were met (room %s)" % room())
	sect = "cloud"
	join_sect()
	invariants("The Recruitment Fair (Cloud)")
	step_entry_trial()
	invariants("Entry Trial (Cloud)")
	step_fish_gutting_fists()
	invariants("Fish-Gutting Fists (Cloud)")
	step_chores()
	invariants("A Disciple's Chores (Cloud)")
	step_weapon_hall()
	invariants("The Weapon Hall (Cloud)")
	_cloud_steps()
	step_strange_tracks()
	invariants("Strange Tracks (Cloud)")
	step_humming_token()
	invariants("The Humming Token (Cloud)")
	walk_held("both sects' stretches")

## Both recruiters met: a checkpoint of the run, the second sect's stretch starts from it.
func keep(label: String) -> void:
	super.keep(label)
	if label == "Both recruiters met": save_checkpoint(run_root() + "cp/fair/")

## The Humming Token (chapter 2's second step), decision 42: under way where Strange Tracks ended (the token hummed at
## the third patch), five Hollowed Boarlets on the Marsh Edge (the grey boarlets where the patches were), and the mentor
## comes down to the marsh for the hand-in (the scene `mentor_descends_*`), gone again after; then the tracker's Next is
## Mei Qing's Errand at the Marsh Edge, where she tends the watchers at the post. No walk up the peak and back.
func step_humming_token() -> void:
	check(room() == "rm_marsh_edge" and c().quests.is_active("the_humming_token"), "The Humming Token under way at the Marsh Edge, where Strange Tracks ended (room %s)" % room())
	check(fight("hollowed_boarlet", 5, 400.0) >= 5, "five Hollowed Boarlets beaten on the Marsh Edge")
	GameEvents.flush()
	settle_scenes()
	var mentor := sect_at("mentor")
	var head: Array = Game.quest.tracker(c()).filter(func(e): return str(e.get("quest", "")) == "the_humming_token")
	check(not npc_object(mentor).is_empty() and not head.is_empty() and str(head[0].get("target_room", "")) == room(),
		"the fifth boarlet down, %s has come down to the Marsh Edge for the hand-in, and the tracker says so (%s)" % [mentor, str(head.slice(0, 1))])
	hand_in(mentor, "the_humming_token")
	GameEvents.flush()
	settle_scenes()
	check(npc_object(mentor).is_empty() and room() == "rm_marsh_edge", "handed in where the fight was, the mentor is gone again (room %s)" % room())
	var nx: Array = Game.quest.tracker(c())
	check(not nx.is_empty() and str(nx[0].get("quest", "")) == "mei_qings_errand" and str(nx[0].get("target_room", "")) == "rm_marsh_edge"
		and not npc_object("mei_qing").is_empty(),
		"after The Humming Token the tracker's Next is Mei Qing's Errand here, at the watch post where she tends the watchers (%s)" % str(nx.slice(0, 1)))

## Mei Qing's Errand, decision 42: taken, gathered and handed in at the Marsh Edge's watch post (willow moss from the
## reed frogs while herbs are not open yet, grey hides from the Hollowed Boarlets): no carrying to Artisan Row and back.
## Grey at the Edges follows, to the mentor's peak.
func step_mei_qing() -> void:
	check(room() == "rm_marsh_edge", "at the Marsh Edge for Mei Qing (room %s)" % room())
	accept("mei_qing", "mei_qings_errand")
	invariants("Mei Qing's Errand taken")
	# Herb gathering opens at Bone Forging 4 (Eyes for Qi): until then the moss comes from the reed frogs, and the
	# tracker leads to them, never to the herb patches the player cannot pick yet (the Willow Path's).
	var errand: Array = Game.quest.tracker(c()).filter(func(e): return str(e.get("quest", "")) == "mei_qings_errand")
	var lead := str(errand[0].get("target_room", "")) if not errand.is_empty() else ""
	var takes := false
	for o in ContentDB.room(lead).get("objects", []):
		if str(o.get("item", "")) == "willow_moss" and Game.world.object_visible(c(), o) and (not o.has("requires") or RequirementRules.passes(o.requires, Game.ctx())): takes = true
	var drops := false
	for sp in ContentDB.room(lead).get("spawns", []):
		if LootRules.drops_item(str(ContentDB.entry("enemies", str(sp.enemy)).get("loot", sp.enemy)), "willow_moss"): drops = true
	check(lead == "rm_marsh_edge" and (takes or drops),
		"Mei Qing's willow moss leads where it can be had, here (%s), never to herbs the player cannot pick yet" % lead)
	var frogs := 0
	for i in 30:
		if c().inventory.count("willow_moss") >= 5: break
		frogs += fight("reed_frog", 1, 120.0)   # the walk picks up what each fight drops
	check(c().inventory.count("willow_moss") >= 5, "five Willow Moss from the Marsh Edge's reed frogs on the grid (%d, %d frogs)" % [c().inventory.count("willow_moss"), frogs])
	var hides := 0
	for i in 20:
		if c().inventory.count("grey_hide") >= 3: break
		hides += fight("hollowed_boarlet", 1, 120.0)   # the walk picks up what each fight drops
	check(c().inventory.count("grey_hide") >= 3, "three Grey Hides from the Marsh Edge's Hollowed Boarlets (%d, %d fights)" % [c().inventory.count("grey_hide"), hides])
	hand_in("mei_qing", "mei_qings_errand")
	check(room() == "rm_marsh_edge" and c().quests.is_active("grey_at_the_edges"),
		"handed in at the watch post, and Grey at the Edges under way, to report to the mentor (room %s)" % room())

## Grey at the Edges, decision 42: the first walk up through the sect's grounds, from the marsh by the watch post's array
## to the gate's and on foot from there (the mentor's peak does not know the token yet), with something on the way in the
## rooms between (a spar offered, two elders overheard, the gardener's favour: the scenes play as the walk comes to them);
## the tea taken up, the report made, and the peak's array keyed to the token: the way down is one array.
func step_grey_at_the_edges() -> void:
	var peak := sect_at("peak")
	var r: Array = Game.world.route(c(), room(), peak)
	check(not r.is_empty() and str(r[0].get("array", "")) != "" and r.slice(1).all(func(s): return str(s.get("array", "")) == ""),
		"the first way up takes the watch post's array to the gate and walks the grounds from there (%s)" % str(r.map(func(s): return s.to)))
	var favour := "ja_herb_terraces" if sect == "jade" else "cm_array_court"
	check(travel(favour), "up through the grounds to the gardener (room %s)" % room())
	accept(own("gardener"), "tea_for_the_elder")
	check(c().inventory.count("lotus_root_tea") >= 1, "the gardener's tea to carry up")
	check(travel(peak), "on up to the mentor's peak (room %s)" % room())
	talk(sect_at("mentor"))
	GameEvents.flush()
	check(c().quests.is_done("grey_at_the_edges"), "Grey at the Edges reported to the mentor")
	hand_in(sect_at("mentor"), "tea_for_the_elder")
	settle_scenes()
	var played := {}
	for f in scene_director.finished: played[str(f.scene)] = true
	var on_way: Array = ["yard_spar_jade", "terrace_talk_jade", "gardener_favour_jade", "mentor_peak_jade"] if sect == "jade" else \
		["court_spar_cloud", "gardener_favour_cloud", "array_court_talk_cloud", "mentor_peak_cloud"]
	check(on_way.all(func(id): return played.has(id)), "something on the way in each room of the first walk up, and the mentor's word at the top (%s)" % str(on_way.filter(func(id): return not played.has(id))))
	var down: Array = Game.world.route(c(), peak, "rm_marsh_edge")
	check(down.size() == 1 and str(down[0].get("array", "")) != "", "the peak's array knows the token now: the way down to the marsh is one array (%s)" % str(down))

## Strange Tracks on the grid: the steward's lesson at the gate (the scene `array_lesson_*`) taken, the gate's array to
## the Marsh Edge's watch post, a breath instead of ten rooms on foot.
func step_strange_tracks() -> void:
	var taken := arrays_taken.size()
	super()
	check(arrays_taken.slice(taken).has("%s > rm_marsh_edge" % sect_at("gate")),
		"to the marsh by the gate's transfer array, as the steward shows it (%s)" % str(arrays_taken.slice(taken)))

## The character's own sect's person of a role both sects have (the gardener: Ji or Ren).
func own(role: String) -> String:
	return "jade_" + role if sect == "jade" else "cloud_" + role

# ------------------------------------------------------------------ decision 42: the sect's transfer arrays
var arrays_taken: Array = []   ## "<from room> > <to room>" for each array the walk took

## On the grid the walk goes the way the tracker's go button goes (Game.world.route): through the ways, and onto the
## sect's transfer array where the route takes one (walked to, tapped, the destination chosen from its choices).
func travel(target: String) -> bool:
	if room() == target: return true
	var r: Array = Game.world.route(c(), room(), target) if Game.room_rt != null and Game.room_rt.topdown != null else []
	if r.is_empty() or not r.any(func(s): return str(s.get("array", "")) != ""): return super(target)
	for s in r:
		if str(s.room) != room(): return false
		if str(s.get("array", "")) != "":
			if not take_array(str(s.portal), str(s.array)): return false
		elif not go(str(s.portal)): return false
	return room() == target

## Tapped, the array opens its travel picker (decision 42: its own page, not a talk), which offers what the World
## authority's view of it lists; the destination's button submits array_travel.
func take_array(node: String, to: String) -> bool:
	var from := room()
	var tap := interact(node)
	var dests: Array = Game.world.array_view(c(), node).get("destinations", []) if str(tap.get("open_page", "")) == "transfer_array" else []
	var pick: Array = dests.filter(func(d): return str(d.id) == to)
	check(not pick.is_empty(), "the %s in %s opens its travel picker offering %s among where it goes (%s)" % [node, from, to, str(dests.map(func(d): return d.name))])
	if pick.is_empty(): return false
	play_s += TAP_S
	var res := submit({"type": "array_travel", "from": node, "to": to})
	if res.get("ok", false): place(Vector2(float(c().position.x), float(c().position.y)))
	arrays_taken.append("%s > %s" % [from, room()])
	return res.get("ok", false)

# ------------------------------------------------------------------ 11: the end of the prototype (decision 41)
## Past The Humming Token, the rest of the story inside the prototype on the grid: Mei Qing's Errand (willow moss from
## the Marsh Edge's reed frogs, since herbs open only at Bone Forging 4, and grey hides from its Hollowed Boarlets,
## handed in at Artisan Row), Grey at the Edges (reported to the mentor), the wait for Bone Forging 7 (hunted on the
## grid; a test shortcut here) and The First Current (Lu, the Lotus Ferry's Qi spring). The story's next quest (Bandits
## on the Road, on the Caravan Road) is played past the prototype's gate: the lessons on offer inside the prototype lead
## first, and then the tracker's first entry is the prototype's end, "The Tale Rests Here", the road beyond still being
## drawn, leading nowhere (no target, no mark). At the prototype's last way east, the Marsh Edge's road to the Grey
## Pools, the gate is shut and says why: walked into, no route, no auto-path, no hop through it; the view stands the
## gate in the way.
func _to_the_gate() -> void:
	check(room() == "rm_marsh_edge", "the Cloud disciple at the Marsh Edge after The Humming Token (room %s)" % room())
	# The gate at the Marsh Edge's east way: shut, walked into it says why, no route or auto-path goes through it.
	var east: Dictionary = Game.room_rt.portal_def("east")
	var gs: Dictionary = Game.world.portal_state(c(), east)
	check(gs.get("gate", false) and not gs.get("open", true) and str(gs.get("text", "")) == Tx.t("sim.world.road_being_drawn"),
		"the Marsh Edge's way east to the Grey Pools is closed by the prototype's gate, and says so (%s)" % str(gs))
	stand_by({"at": east.at, "alt": east.get("alt", 0.0)}, Vector2.ZERO, 0.0)
	var walked := submit({"type": "use_portal", "portal": "east"})
	check(not walked.get("ok", false) and str(walked.get("text", "")) == Tx.t("sim.world.road_being_drawn") and room() == "rm_marsh_edge",
		"walked into, the gate stays shut and says the road beyond is still being drawn (%s)" % str(walked))
	check(Game.world.route(c(), "rm_marsh_edge", "rm_grey_pools").is_empty() and not submit({"type": "auto_path", "target": "rm_grey_pools"}).get("ok", false),
		"no route and no auto-path go through the gate")
	var w := _live_view()
	var gates := w.sorted.get_children().filter(func(n): return n is TopdownGate and not n.is_queued_for_deletion())
	for g in gates: g._process(0.0)
	check(gates.size() >= 2 and gates.all(func(g): return g.visible and str(g.def.get("id", "")) == "east"),
		"the view stands the gate in the way east, drawn post by post down the edge (%d pieces)" % gates.size())
	_drop_view(w)
	step_mei_qing()
	invariants("Mei Qing's Errand (Cloud)")
	step_grey_at_the_edges()
	invariants("Grey at the Edges (Cloud)")
	# The story waits on Bone Forging 7 for The First Current (Lu, the Lotus Ferry's Qi spring): a hunt on the grid.
	var wait: Array = Game.quest.tracker(c())
	check(not wait.is_empty() and str(wait[0].get("quest", "")) == "the_first_current" and wait[0].get("hunt", false)
		and TopdownRoom.has_layout(str(wait[0].get("target_room", ""))), "then the story waits on a Level, hunted on the grid (%s)" % str(wait.slice(0, 1)))
	check(climb_to("bone_forging_7"), "Bone Forging 7 (a test shortcut for the hunt: realm %s)" % c().cultivator.realm_key)
	var taken := arrays_taken.size()
	check(travel("lf_village") and arrays_taken.size() == taken + 1, "to Lu at the Lotus Ferry docks, down the peak by its array to the watch post (room %s; %s)" % [room(), str(arrays_taken.slice(taken))])
	accept("lu_boatman", "the_first_current")
	var spring: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("type", "")) == "qi_spring")
	stand_by(spring[0], Vector2(-20, 10), 0.0)
	submit({"type": "start_meditation"})
	step(32.0)
	submit({"type": "stop_meditation"})
	hand_in("lu_boatman", "the_first_current")
	invariants("The First Current")
	# The story's next quest (Bandits on the Road, on the Caravan Road) is past the gate. The lessons on offer inside the
	# prototype still come first (Eyes for Qi, the Outer Trial), never one past it (Stone and Sweat, at the quarry).
	var lessons: Array = []
	for i in 8:
		var nx := Game.quest.story_next(c())
		if nx.get("gate", false) or nx.is_empty(): break
		var ld := ContentDB.entry("quests", str(nx.get("quest", "")))
		lessons.append(str(ld.get("id", "")))
		check(str(ld.get("kind", "")) == "guided" and not Game.quest.beyond_prototype(c(), ld) and TopdownRoom.has_layout(str(nx.get("target_room", ""))),
			"past the story's end a lesson inside the prototype comes next: %s at %s" % [str(ld.get("id", "")), str(nx.get("target_room", ""))])
		# A test shortcut: the lesson as done (its play is the fields' and the sect's, as the side-view walk plays them).
		c().quests.offered.erase(str(ld.id))
		c().quests.done[str(ld.id)] = 1
		GameEvents.flush()
	check(lessons.has("eyes_for_qi") and not lessons.has("stone_and_sweat"), "the lessons on offer inside the prototype led first, none past the gate (%s)" % str(lessons))
	var tr: Array = Game.quest.tracker(c())
	var head: Dictionary = tr[0] if not tr.is_empty() else {}
	check(head.get("gate", false) and str(head.get("name", "")) == Tx.t("sim.quest.tale_rests") and str(head.get("target_room", "x")) == ""
		and (head.get("lines", []) as Array).any(func(l): return str(l.text) == Tx.t("sim.world.road_being_drawn")),
		"with the story's next quest past the gate, the tracker's first entry is the prototype's end, leading nowhere (%s)" % str(head))
	check(Game.world.guide_target(c()) == "" and Game.world.guide_step(c()).is_empty(), "the direction mark leads nowhere past the gate (%s)" % Game.world.guide_target(c()))
	var side := Game.quest.story_next(c())
	check(side.get("gate", false), "the Quests page's Next slip is the prototype's end too (%s)" % str(side.get("name", "")))
	keep("The prototype's end")

## A test shortcut past the Levels the fields are hunted for (the hunting is played in chapter 2's fights): the realm's
## bar filled and broken through as the HUD asks, to `realm`.
func climb_to(realm: String) -> bool:
	for i in 60:
		if ProgressionRules.at_least(c().cultivator.realm_key, realm): break
		var cu = c().cultivator
		if cu.state == "consolidating":
			cu.consolidation_left = 0.01
			step(0.5)
		elif cu.state != "bottleneck":
			Game.progression.apply_progress(c().id, 0.0, "test_shortcut", 1.0)
			step(0.2)
		else:
			submit({"type": "start_breakthrough", "support_items": []})
			step(4.0)
	return ProgressionRules.at_least(c().cultivator.realm_key, realm)

## The Cloud Steps on the grid: touch the starting stone on the Cliff Stair, climb the grand stair and the ledges to the
## bell on the top ledge (the route's finish is its route_finish object, where the layout puts it), and the run ends.
func _cloud_steps() -> void:
	check(travel("cm_cliff_stair"), "to the Cliff Stair for the Cloud Steps (room %s)" % room())
	var done := {"finished": false}
	var heard := func(n: String, p: Dictionary): if n == "route_finished": done.finished = p.get("finished", true)
	GameEvents.event.connect(heard)
	check(interact("cloud_steps_stone").get("ok", false), "the Cloud Steps begin at their stone")
	var bell: Dictionary = Game.room_rt.object_def("cloud_steps_bell")
	stand_by(bell, Vector2.ZERO, float(bell.get("alt", 0.0)))
	step(0.5)
	GameEvents.event.disconnect(heard)
	check(bool(done.finished), "the Cloud Steps run ends at the bell on the top ledge, reached on foot")

# ------------------------------------------------------------------ 1, 3, 4: each room entered
func _on_grid_event(n: String, p: Dictionary) -> void:
	if n != "room_entered" or c() == null or str(p.get("actor", "")) != str(c().id) or Game.room_rt == null: return
	var rid := room()
	var on_grid: bool = Game.room_rt.topdown != null
	if on_grid != TopdownRoom.has_layout(rid): wrong_view.append("%s (grid %s)" % [rid, str(on_grid)])
	reach_room = ""
	if not on_grid:
		if is_instance_valid(probe): probe.free()
		probe = null
		return
	grid_rooms[rid] = true
	reach_room = rid
	reach_here = reach(Game.room_rt.topdown, TopdownRoom.cell_of(Vector2(float(c().position.x), float(c().position.y))))
	_probe_view()

## Stand at a spot, as tutorial_order does; on the grid it must be reached on foot from where the room was entered.
func place(p: Vector2, alt := 0.0) -> void:
	super.place(p, alt)
	if Game.room_rt == null or Game.room_rt.topdown == null or reach_room != room(): return
	var cell := TopdownRoom.cell_of(st.plane)
	if not reach_here.has(cell) and far.size() < 20: far.append("%s %s" % [room(), str(cell)])

## 4: the character's own top-down view (unbound: the walk moves the body) built on the room just entered.
func _probe_view() -> void:
	var bakes := TopdownShadows.bakes
	if not is_instance_valid(probe):
		var was: String = Game.active_id
		Game.active_id = ""   # the view alone: the walk keeps the body (its own ActorState) bound
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
	# The room's own people and things (decision 43's extras at work are figures with no label and no part in the room).
	var figures := probe.sorted.get_children().filter(func(f): return f is TopdownPlaces.Figure and f.twin != null and not f.is_queued_for_deletion())
	var marks := probe.floor_layer.get_children().filter(func(m): return m is TopdownPlaces.WayMark and not m.is_queued_for_deletion())
	var ok: bool = probe.room == Game.room_rt.topdown and probe.npc_views.size() == npcs.size() and probe.object_views.size() == things.size() \
		and figures.size() == npcs.size() + things.size() and probe.portal_views.size() == (def.get("portals", []) as Array).size() \
		and marks.size() == probe.portal_views.size() and probe.hud_minimap
	if not ok: probe_misses.append("%s: npcs %d/%d things %d/%d figures %d ways %d/%d marks %d" % [room(), probe.npc_views.size(), npcs.size(),
		probe.object_views.size(), things.size(), figures.size(), probe.portal_views.size(), (def.get("portals", []) as Array).size(), marks.size()])
	for f in figures:
		if str(f.def.get("type", "")) != "npc": continue
		if not f.art is TopdownPlaces.Person: people_misses.append("%s: %s is not a top-down figure" % [room(), f.def.id])
		elif not (f.art.figure.missing as Array).is_empty(): people_misses.append("%s: %s lacks %s" % [room(), f.def.npc, str(f.art.figure.missing)])
	_probe_light(bakes)

## 8: decision 40 on the room just built: one bake of its cast shadows; eight seconds of its air at midday and at the
## clock's night (the probe's camera on its spawn) stay under the caps and bake nothing again; a night room is the
## story's night, lit by its lights (their pools baked) with the flames over it.
func _probe_light(bakes_before: int) -> void:
	var rid := room()
	var a: TopdownAtmosphere = probe.atmosphere
	light_rooms += 1
	if TopdownShadows.bakes != bakes_before + 1: light_misses.append("%s: %d bakes to build it" % [rid, TopdownShadows.bakes - bakes_before])
	if probe.shadows == null or probe.shadows.room != probe.room: light_misses.append("%s: no shadows for the room" % rid)
	var baked := TopdownShadows.bakes
	probe.camera.position = TopdownWorld.to_screen(probe.room.spawn, 0.0)
	for hour in [0.375, 0.87]:
		TopdownLight.debug_hour = hour
		a.refresh()
		var most := 0
		var over := {}
		for i in 240:
			a._process(1.0 / 30.0)
			most = maxi(most, a.particle_count())
			for kind in TopdownLight.PARTICLES:
				if a._count(kind) > int(TopdownLight.PARTICLES[kind].cap): over[kind] = true
		if most > TopdownLight.MAX_PARTICLES or not over.is_empty(): light_misses.append("%s at %.2f: %d particles (over %s)" % [rid, hour, most, str(over.keys())])
	TopdownLight.debug_hour = -1.0
	a.refresh()
	if TopdownShadows.bakes != baked: light_misses.append("%s: baked again while it played" % rid)
	if bool(Game.room_rt.def.get("night", false)):
		night_rooms += 1
		var lamps := a.lights.filter(func(l): return str(l[0]) in ["lantern", "lantern_red"]).size()
		if str(a.now.hour) != "night_story" or not a.night.visible or lamps == 0 or a._pools_room != probe.room.id or float(a.now.lights) <= 0.0:
			light_misses.append("%s: night %s, layer %s, %d lamps, pools of %s" % [rid, str(a.now.hour), str(a.night.visible), lamps, a._pools_room])
		# Settings' "Light and particles" off (weak phones): no grade, clouds or particles, and the night stays night.
		var was = Game.account.settings.get("world_extras", true)
		Game.account.settings["world_extras"] = false
		a.refresh()
		a._process(1.0 / 30.0)
		if a.grade_layer.visible or a.clouds.visible or a.particle_count() > 0 or not a.night.visible or str(a.now.hour) != "night_story":
			light_misses.append("%s with the extras off: grade %s, clouds %s, %d particles, night %s" % [rid, str(a.grade_layer.visible), str(a.clouds.visible), a.particle_count(), str(a.night.visible)])
		Game.account.settings["world_extras"] = was
		a.refresh()

# ------------------------------------------------------------------ 8: the people draw with the room
## A room's people draw within a moment of it, whatever the pages are doing. From the title screen on the game compiles
## every page script on a loading thread (main.gd, PageWarmer), and while one compiles every other load waits for it:
## asked for all at once, they held a villager's sheets back for seconds after launch (the reported late villagers).
## Warmed one at a time as the title does now, the first run's pages still compiling, Lotus Ferry's people (drawn in
## the top-down style, TopdownPlaces.Person) are all drawn within a moment of the room being populated.
func _people_stream() -> void:
	var warm := PageWarmer.new(load("res://scripts/main.gd").PAGES.values())
	warm.tick()   # as the title starts it
	await get_tree().process_frame
	# Timed on the suite's own clock, with its share of a CPU asked for while it times (tests/lib/suite.gd).
	ask_for_cpu()
	var t0 := now_us()
	var people: Array = []
	for o in ContentDB.room("lf_village").get("objects", []):
		if str(o.get("type", "")) == "npc": people.append(TopdownPlaces.Person.new(o))
	var waiting := people.size()
	while waiting > 0 and now_us() - t0 < 5000000:
		await get_tree().process_frame
		warm.tick()   # as main.gd does each frame
		waiting = people.filter(func(p): return not p.figure.loaded()).size()
	var ms := (now_us() - t0) / 1000
	usual_cpu()
	var left := warm.queue.size()
	for p in people: p.free()
	while warm.tick(): await get_tree().process_frame   # the rest of the pages, before the walk
	check(people.size() >= 6 and waiting == 0 and ms < 1500 and left > 0,
		"Lotus Ferry's %d people are all drawn %d ms after the room is populated while the pages still warm up (%d page scripts still to compile)" % [people.size(), ms, left])

# ------------------------------------------------------------------ 2: the layouts
## Every layout of the tutorial and of chapter 2's stretch: each thing of its side-view room placed on a floor, and
## reached on foot from every way in and from its spawn; every foe it spawns, its event's too, drawn for the grid.
func _layouts() -> void:
	var rooms: Array = TUTORIAL_ROOMS.duplicate()
	for sid in CHAPTER2_ROOMS:
		for rid in CHAPTER2_ROOMS[sid]: if not rooms.has(rid): rooms.append(rid)
	for rid in rooms:
		check(TopdownRoom.has_layout(rid), "%s has a top-down layout" % rid)
		if not TopdownRoom.has_layout(rid): continue
		var grid := TopdownRoom.load_room(rid)
		var side := ContentDB.room(rid)
		var def := grid.merge_def(side)
		var place_d: Dictionary = grid.def.get("place", {})
		var ways: Dictionary = grid.def.get("portals", {})
		var unplaced: Array = side.get("objects", []).filter(func(o): return not place_d.has(str(o.id))).map(func(o): return str(o.id))
		unplaced.append_array(side.get("portals", []).filter(func(p): return not ways.has(str(p.id))).map(func(p): return "way " + str(p.id)))
		if (grid.def.get("spawns", []) as Array).size() != (side.get("spawns", []) as Array).size(): unplaced.append("spawns")
		check(unplaced.is_empty(), "%s: the layout places every NPC, object, way and spawn of the room (unplaced %s)" % [rid, str(unplaced)])
		var starts: Array = [TopdownRoom.cell_of(grid.spawn)]
		for p in def.get("portals", []): starts.append(TopdownRoom.cell_of(Vector2(float(p.arrive[0]), float(p.arrive[1]))))
		var bad: Array = []
		for s in starts:
			if not grid.standable(s):
				bad.append("start %s on no floor" % str(s))
				continue
			var r := reach(grid, s)
			for o in def.get("objects", []):
				var at := Vector2(float(o.at[0]), float(o.at[1]))
				if not str(o.get("type", "")) in ["fishing_spot", "rift_tear", "insect_swarm"] and not grid.standable(TopdownRoom.cell_of(at)): bad.append("%s on no floor" % o.id)
				var spot := TopdownRoom.cell_of(grid.spot_near(at, float(o.alt), at))
				if not r.has(spot): bad.append("%s from %s" % [o.id, str(s)])
			for p in def.get("portals", []):
				if not r.has(TopdownRoom.cell_of(Vector2(float(p.at[0]), float(p.at[1])))): bad.append("way %s from %s" % [p.id, str(s)])
				# Its reach is turned with it: a tile across the way, along it half its span (WorldAuthority.portal_near).
				var across := 1 if float(p.dir[0]) == 0.0 else 0
				if float(p.reach[across]) != TopdownRoom.TILE or float(p.reach[1 - across]) < TopdownRoom.TILE * 0.5: bad.append("way %s reach %s" % [p.id, str(p.reach)])
			for sp in def.get("spawns", []):
				for q in sp.get("points", []):
					if not grid.standable(TopdownRoom.cell_of(Vector2(float(q[0]), float(q[1])))): bad.append("a %s spawn on no floor" % sp.enemy)
		check(bad.is_empty(), "%s: everything stands on a floor and is reached on foot from every way in and from the spawn (%s)" % [rid, str(bad.slice(0, 6))])
		var species: Dictionary = grid.tileset.get("foes", {}).get("species", {})
		var dirs: Array = grid.tileset.get("foes", {}).get("dirs", [])
		var foes: Array = side.get("spawns", []).map(func(sp): return str(sp.enemy))
		var ev: Dictionary = side.get("event", {})
		if ev.has("wave"): foes.append(str(ev.wave.enemy))
		for fs in ev.get("fixed_spawns", []) + ev.get("waves", []) + ev.get("timed_spawns", []): foes.append(str(fs.enemy))
		check(rid != "lf_village_night" or foes.has("hollowed_eel") and foes.has("hollow_minnow"), "%s: the night's minnows and its eel are among the foes checked (%s)" % [rid, str(foes)])
		var undrawn: Array = foes.filter(func(e):
			return not species.has(e) or dirs.size() != 5 or FOE_ACTIONS.any(func(a): return dirs.any(func(d): return (species[e].actions.get(a, {}).get("frames", {}).get(d, []) as Array).is_empty())))
		check(undrawn.is_empty(), "%s: every foe it spawns has its own top-down figure, every action in five drawn facings (undrawn %s)" % [rid, str(undrawn)])

# ------------------------------------------------------------------ 7: the real view drives the body
## The character's own view (a live TopdownWorld, bound, as main.gd mounts it) moves the body on the grid: the context
## button offers a talk beside a person; auto-path (the tracker's go button) walks it to the Cloud Sect's road and in
## through its door (the Trial Tower's door is the prototype's gate), and back on the Fairground out through its east
## edge into Artisan Row, the view following.
func _walk_on_the_grid() -> void:
	var w := _live_view()
	var shen: Dictionary = npc_object("shen_lian")
	var at := Vector2(float(shen.at[0]), float(shen.at[1]))
	w.player.motor.place(w.room.spot_near(at, float(shen.alt), at + Vector2(-40, 0)))
	w.player.physics_step(1.0 / 60.0)
	w._update_context()
	check(str(w.context.get("type", "")) == "npc" and str(w.context.get("npc", "")) == "shen_lian", "on the grid the context button offers a talk beside Shen Lian (%s)" % str(w.context))
	# Her figure turns to the player at her west side, in the top-down style, and back to her rest when he walks off.
	var fig: TopdownPlaces.Figure = null
	for f in w.sorted.get_children():
		if f is TopdownPlaces.Figure and str(f.def.get("id", "")) == str(shen.id): fig = f
	var turned := ""
	var back := ""
	if fig != null and fig.art is TopdownPlaces.Person:
		fig._process(0.0)
		turned = fig.art.row
		w.player.motor.place(w.room.spawn)
		w.player.physics_step(1.0 / 60.0)
		w._update_context()
		fig._process(0.0)
		back = fig.art.row if not fig.twin.focus else "still focused"
	check(turned == "w" and fig.art.action == fig.art.stand and back == fig.art.rest and back != "w",
		"Shen Lian's top-down figure turns west to the player talking to her, and back to her rest (%s) when he walks off (turned %s, back %s)" % [fig.art.rest if fig else "-", turned, back])
	# Decision 41: the Trial Tower has no top-down layout yet, so its door is the prototype's gate: no auto-path to it.
	check(not submit({"type": "auto_path", "target": "sf_trial_tower"}).get("ok", false) and Game.world.portal_state(c(), Game.room_rt.portal_def("tower")).get("gate", false),
		"the Trial Tower's door is closed by the prototype's gate, and auto-path finds no way in")
	check(_auto_path(w, "cm_cliff_stair", 40.0), "auto-path walks the body across the Fairground to the Cloud Sect's road and in through its door (room %s)" % room())
	# Decision 42: the tracker's go button takes the sect's transfer array where its route does: the body walks to the
	# node and steps onto it, and comes out on the far one (up to the mentor's peak and back down to the gate).
	var rides: Array = []
	var heard := func(n: String, p: Dictionary): if n == "array_travelled": rides.append(str(p.get("to_room", "")))
	GameEvents.event.connect(heard)
	check(_auto_path(w, "cm_elder_sung_peak", 40.0) and rides == ["cm_elder_sung_peak"] and w.room.id == "cm_elder_sung_peak",
		"auto-path walks the body to the Cliff Stair's transfer array and up to Elder Sung's peak on it, the view following (room %s; %s)" % [room(), str(rides)])
	check(_auto_path(w, "cm_cliff_stair", 40.0) and rides.size() == 2 and w.room.id == "cm_cliff_stair",
		"and back down to the gate on the peak's array (room %s; %s)" % [room(), str(rides)])
	GameEvents.event.disconnect(heard)
	_drop_view(w)
	check(go("stoneford") and room() == "sf_fairground", "back down the road onto the Fairground")
	w = _live_view()
	check(_auto_path(w, "sf_artisan_row", 40.0) and w.room == Game.room_rt.topdown and w.room.id == "sf_artisan_row",
		"auto-path walks out through the Fairground's east edge into Artisan Row, and the view builds it (room %s)" % room())
	_drop_view(w)

## The view gone, the walk's own body is the one the authorities move again.
func _drop_view(w: TopdownWorld) -> void:
	w.free()
	if st != null: Game.bind_movement(Game.active_id, st)

func _live_view() -> TopdownWorld:
	var w := TopdownWorld.new()
	w.live = true
	w.sim_frozen = true   # the walk steps it
	add_child(w)
	return w

## Auto-path to `target`, stepping the view's body and the simulation as the world does, until it arrives.
func _auto_path(w: TopdownWorld, target: String, limit_s: float) -> bool:
	if not submit({"type": "auto_path", "target": target}).get("ok", false): return false
	var t := 0.0
	var dt := 1.0 / 60.0
	while room() != target and t < limit_s:
		w.player.physics_step(dt)
		Game.tick(dt)
		GameEvents.flush()
		if room() != target: w._check_portals(dt)
		t += dt
	play_s += t
	return room() == target

## Every cell reached on foot from `from` (the TopdownMotor's rules, as tools/data/topdown_rooms.py's Grid checks them):
## walking and stairs, any drop, a jump up as many whole levels as its apex and mantle climb (one today: 32.5 with the
## half unit TopdownRoute allows), and a running jump over a tile of water or a drop past a step. The step and the jump
## are data/movement.json's `topdown`, read as the motor reads them (TopdownMotor.conf) and as the Grid does.
static func reach(grid: TopdownRoom, from: Vector2i) -> Dictionary:
	var step := float(TopdownMotor.conf("step_up", 8.0))
	var impulse := float(TopdownMotor.conf("impulse", 400.0))
	var apex := impulse * impulse / (2.0 * float(TopdownMotor.conf("gravity", 1700.0)))
	var hop := TopdownRoom.LEVEL * floorf((apex + float(TopdownMotor.conf("mantle", 12.0))) / TopdownRoom.LEVEL) + 0.5
	var seen := {from: true}
	var queue: Array = [from]
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
	while not queue.is_empty():
		var cur: Vector2i = queue.pop_front()
		var h0 := grid.cell_floor(cur)
		for d in dirs:
			var nx: Vector2i = cur + d
			if not seen.has(nx) and grid.cell_floor(nx) - h0 <= hop:
				seen[nx] = true
				queue.append(nx)
			var far_c: Vector2i = cur + d * 2
			var mid := grid.level(nx.x, nx.y)
			var gap: bool = mid == TopdownRoom.WATER or (grid.cell_floor(nx) < INF and grid.cell_floor(nx) < h0 - step)
			if gap and not seen.has(far_c) and grid.cell_floor(far_c) - h0 <= step:
				seen[far_c] = true
				queue.append(far_c)
	return seen

# ------------------------------------------------------------------ 5: saved and loaded on the grid
## A save taken on the grid resumes on the grid: the spot, the room, the view (after the walk, back at the Fairground).
func _save_on_the_grid() -> void:
	check(travel("sf_fairground"), "back to the Fairground on the grid (room %s)" % room())
	var here := room()
	var at: Vector2 = st.plane
	for i in 3: step(0.05)   # the World authority keeps the spot the save takes
	Game.save_all()
	var saved: Dictionary = c().position.duplicate()
	Game.boot()
	Game.autosave_enabled = false
	check(submit({"type": "enter_character", "slot": 1}).ok and submit({"type": "enter_world"}).ok, "the character enters the world again from its save")
	st = null
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(c().view == "topdown" and room() == here and Game.room_rt.topdown != null and Vector2(float(c().position.x), float(c().position.y)).distance_to(at) < 20.0,
		"a save taken on the grid resumes on the grid at the same spot (%s at %s; saved %s)" % [room(), str(Vector2(float(c().position.x), float(c().position.y))), str(saved)])
