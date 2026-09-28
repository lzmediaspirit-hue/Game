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
##      its lanterns and doorways over the story's night, which stays night with Settings' extras off.
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
	print("topdown_tutorial: %d checks, %d failures" % [checks, failures])
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

## The Humming Token (chapter 2's second step): the mentor's quest after Strange Tracks, five Hollowed Boarlets on the
## Marsh Edge (the grey boarlets where the patches were), handed in on the peak; then the tracker's Next is Mei Qing's
## Errand at Artisan Row.
func step_humming_token() -> void:
	accept(sect_at("mentor"), "the_humming_token")
	check(travel("rm_marsh_edge"), "to the Marsh Edge for the grey boarlets (room %s)" % room())
	check(fight("hollowed_boarlet", 5, 400.0) >= 5, "five Hollowed Boarlets beaten on the Marsh Edge")
	check(travel(sect_at("peak")), "back to the mentor's peak (room %s)" % room())
	hand_in(sect_at("mentor"), "the_humming_token")
	GameEvents.flush()
	var nx: Array = Game.quest.tracker(c())
	check(not nx.is_empty() and str(nx[0].get("quest", "")) == "mei_qings_errand" and str(nx[0].get("target_room", "")) == "sf_artisan_row",
		"after The Humming Token the tracker's Next is Mei Qing's Errand at Artisan Row (%s)" % str(nx.slice(0, 1)))

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
	var figures := probe.sorted.get_children().filter(func(f): return f is TopdownPlaces.Figure and not f.is_queued_for_deletion())
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
	var t0 := Time.get_ticks_msec()
	var people: Array = []
	for o in ContentDB.room("lf_village").get("objects", []):
		if str(o.get("type", "")) == "npc": people.append(TopdownPlaces.Person.new(o))
	var waiting := people.size()
	while waiting > 0 and Time.get_ticks_msec() - t0 < 5000:
		await get_tree().process_frame
		warm.tick()   # as main.gd does each frame
		waiting = people.filter(func(p): return not p.figure.loaded()).size()
	var ms := Time.get_ticks_msec() - t0
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
		for fs in ev.get("fixed_spawns", []): foes.append(str(fs.enemy))
		var undrawn: Array = foes.filter(func(e):
			return not species.has(e) or dirs.size() != 5 or FOE_ACTIONS.any(func(a): return dirs.any(func(d): return (species[e].actions.get(a, {}).get("frames", {}).get(d, []) as Array).is_empty())))
		check(undrawn.is_empty(), "%s: every foe it spawns has its own top-down figure, every action in five drawn facings (undrawn %s)" % [rid, str(undrawn)])

# ------------------------------------------------------------------ 7: the real view drives the body
## The character's own view (a live TopdownWorld, bound, as main.gd mounts it) moves the body on the grid: the context
## button offers a talk beside a person; auto-path (the tracker's go button) walks it to the Trial Tower's doorway and
## in through the door, and back on the Fairground out through its east edge into Artisan Row, the view following.
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
	check(_auto_path(w, "sf_trial_tower", 40.0), "auto-path walks the body across the Fairground to the Trial Tower's doorway and in (room %s)" % room())
	_drop_view(w)
	check(go("entry") and room() == "sf_fairground", "back out of the tower onto the grid")
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

## Every cell reached on foot from `from` (the TopdownMotor's rules, as tools/data/topdown_rooms.py checks them):
## walking and stairs, any drop, a jump up to one level, and a running jump over a tile of water or a drop.
static func reach(grid: TopdownRoom, from: Vector2i) -> Dictionary:
	var seen := {from: true}
	var queue: Array = [from]
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
	while not queue.is_empty():
		var cur: Vector2i = queue.pop_front()
		var h0 := grid.cell_floor(cur)
		for d in dirs:
			var nx: Vector2i = cur + d
			if not seen.has(nx) and grid.cell_floor(nx) - h0 <= TopdownRoom.LEVEL + 0.5:
				seen[nx] = true
				queue.append(nx)
			var far_c: Vector2i = cur + d * 2
			var mid := grid.level(nx.x, nx.y)
			var gap: bool = mid == TopdownRoom.WATER or (grid.cell_floor(nx) < INF and grid.cell_floor(nx) < h0 - 8.0)
			if gap and not seen.has(far_c) and grid.cell_floor(far_c) - h0 <= 8.0:
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
