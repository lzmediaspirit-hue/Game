extends "res://tests/prologue_run.gd"
## topdown_traversal (T1, docs/architecture/topdown_mechanics.md): the side view's traversal and set pieces, played on the
## height grid by a top-down character through the real view (a live TopdownWorld: its player's motor stepped frame by
## frame as the world steps it, then Game.tick), each mechanic in the converted room that needs it:
##   1. set pieces: every room event a set piece starts in a room with a layout sets its foes on the grid's open floors,
##      reached on foot from the player, inside the room (the summit's by its stage, the rest by their mapped points),
##      however the room is sized; so do a rift, a treasure birth and the sect's raid, on the grid's own floors;
##   2. rafts: the Grey Pools' log raft boarded from the jetty carries its rider across the grey pool to the west bank
##      (mover_boarded), the loop raft round the east pool and back, the hermit's raft across his pond; never a splash;
##   3. Leaf on the Wind, the lesson played on the grid: the vine climbed to the spray ledge (no blow while on it), a
##      glide from the ledge over the falls' spray to the lotus rock, and back up on the spray's updraft to the ledge a
##      jump cannot reach; the two glides count, and Elder Hu takes it;
##   4. the rope up the falls ledge's east face and back down; a sealed climbable stays shut;
##   5. Skipping Stones: Water Skimming across the hermit's pond counts, the mist lotus picked, the hermit takes it;
##   6. Swallow Dart and the Cloud Ladder Step in the Falls Pool: three darts along the stick holding the height, three
##      second jumps, each lesson's objectives done on the grid (their librarian waits in the library);
##   7. Wall-Step off the cliff's face and a bounce off a drum laid on the grid, each its art_used;
##   8. a lift laid at the cliff's foot carries its rider up to the top and goes back without it; rotten boards hold a
##      foot, give way into the water and come back;
##   9. a current pushes a body standing in it; a flood rises on a boss's phase, sends the body to dry floor, and falls;
##  10. flight: Jump held takes to the air (Wings of Cloud's objective), climbs, holds, lands on Evade held, ends out
##      of QI, and glides where flight is refused;
##  11. a mount: the rider goes at its pace, steps down to climb the rope and is back on at its top, kicks off no wall;
##  12. the Plunge off the Pavilion Rooftops' roof, the Outer Trial's objective counted.
## T2, the Act I rooms' own rows (the to-do's items 1-13):
##  13. Cloud Lung's air distance: a flight north counts as one east does;
##  14. the sealed ladders as hatches over the flights: Old Ma's storeroom and the Fisher's Hut's loft (The Runaway
##      Kite), the two libraries' galleries (sect rank);
##  15. the Reed Shallows' three driftwood logs and Bend Shore's ferry ridden;
##  16. the Fairground's drum, the Whispering Bamboo's bent culm and the Grey Pools' lotus leaf bounce a body up a level;
##  17. the Jade trial's two lifts and the quarry's crane carry their rider up; the Cloud trial's planks give way into the
##      pool, hold under a sprint, and the trial bell is rung from its ledge;
##  18. the Tunnels' rotten planks over their spike pits: a sprint crosses, a stop drops the body to the spikes;
##  19. the Flooded Gate's plank and drain, the Hall of Lanterns' swinging lantern ridden, the Serpent's and the Abbot's
##      floods, the Rapids' current and its hazard's areas;
##  20. the Echo Cliffs' shaft climbed with three Wall-Step kicks, Between Two Walls counting them;
##  21. the Frozen Shrine's ice and icicle shelves, the monastery's rotten floor, the Windswept Ridge's wind;
##  22. Breath Control's swim in the Drowned Grotto, its thirty seconds of breath;
##  23. the shallows' slow on the Flooded Gate's court;
##  24. the rooftop chases at Gate Street and the Stoneford market played on the grid.
## T3, Act II onward and T2's leftovers (the to-do's items 14-17):
##  25. the Lower Pit's cracked slab: the shards sealed under it, a hop holds it, a Plunge breaks it and strikes below;
##  26. Frostpine Climb's and Rimefrost Summit's ice;
##  27. no-flight: the rooms that forbid it, an interior and a dungeon glide; a flight into a no_flight volume comes down;
##  28. low gravity: a floor laid on the Falls Pool, its jade switch turned through the World authority, a jump higher;
##  29. the Starsea's four docks: each voyage played on the grid, its crossing's deck and its port both laid out;
##      the Shipwrights' Yard's chart table and slipway open their pages;
##  30. the light of the late zones: the tomb and the Clan Hearth lamp-lit, the star field starlit, its star lanterns lit;
##  31. the Jellyfish Shallows' wade, and Spirit Sense showing the Smugglers' Cove's crack;
##  32. the swim's stroke: a pull and a glide, each pull's wake;
##  33. the drum gives as it launches a body;
##  34. the Hall of Lanterns' circling lantern goes round upright and carries its rider up;
##  35. the monastery's rotten floor stays gone over a body under it, and comes back once it steps out;
##  36. the Tunnels' pits open beside their planks: the spikes strike, the planks do not;
##  37. the wind pushes harder by a drop on a diagonal;
##  38. a flier high over its floor is drawn over the crowns south of it;
##  39. the star field's end (R9's rooms): the Orbit Ruins' low-gravity rows under their switches, the Inverted Hall's
##      switch turned with its own interact and its high gallery climbed in the light air; the Nebula Leviathan crossing
##      its lagoon; the starlit areas, the Wardens' lamps lit, the void under the brinks, star-water, the crossing's deck.
## Run headless:  godot --headless --path . res://tests/topdown_traversal.tscn [-- --verbose] [-- --only=<part>]

const BEFORE := ["prologue", "main"]
const PLAYED := ["leaf_on_the_wind", "swallow_dart", "cloud_ladder", "skipping_stones", "between_two_walls"]
const DT := 1.0 / 60.0

var w: TopdownWorld = null
var arts: Dictionary = {}     # art -> times art_used was heard
var boarded: Array = []       # movers boarded
var climbs: Array = []        # [event, climbable, end]
var systems: Dictionary = {}  # T3: system -> times system_used was heard
var flight_ends: Array = []   # T3: the reasons flight_ended was heard with
var struck: Dictionary = {}   # T3: hazard -> times hazard_struck was heard
var motor_events: Array = []  # T3: what the body's motor did, frame by frame (frames())

func _main() -> void:
	start_new("traverse/")
	GameEvents.event.connect(_heard)
	_shortcut()
	_world()
	for part in [_set_pieces, _rafts, _leaf_on_the_wind, _rope, _skipping_stones, _dart_and_ladder, _wall_and_bounce,
			_lift_and_boards, _current_and_flood, _flight, _mount, _plunge,
			# T2: the Act I rooms' rows
			_air_distance, _sealed_ladders, _act1_rafts, _bounces, _trials_and_crane, _tunnels, _drowned_shrine, _echo_shaft,
			_peaks, _swim, _shallows, _chases,
			# T3: Act II onward, and T2's leftovers
			_cracked_slab, _rimefrost_ice, _no_flight, _low_gravity, _starsea, _late_light, _sky_sea_leftovers, _swim_stroke,
			_bounce_gives, _upright_lanterns, _returning_boards, _open_spikes, _wind_diagonals, _flier_over_crowns, _star_field]:
		if _wanted(part.get_method()): part.call()
	if is_instance_valid(w): w.free()
	end_suite()

## `-- --only=<text>`: only the parts whose name holds the text (a part's checks need none of the others').
func _wanted(part: String) -> bool:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--only="): return part.contains(str(a).trim_prefix("--only="))
	return true

func _heard(n: String, p: Dictionary) -> void:
	if c() == null or str(p.get("actor", "")) != str(c().id): return
	match n:
		"art_used": arts[str(p.get("art", ""))] = int(arts.get(str(p.get("art", "")), 0)) + 1
		"mover_boarded": boarded.append(str(p.get("mover", "")))
		"climb_started": climbs.append(["started", str(p.get("climbable", "")), ""])
		"climb_finished": climbs.append(["finished", str(p.get("climbable", "")), str(p.get("end", ""))])
		"system_used": systems[str(p.get("system", ""))] = int(systems.get(str(p.get("system", "")), 0)) + 1
		"flight_ended": flight_ends.append(str(p.get("reason", "")))
		"hazard_struck": struck[str(p.get("hazard", ""))] = int(struck.get(str(p.get("hazard", "")), 0)) + 1

# ------------------------------------------------------------------ the shortcut and the view
## The story before chapter 4 done (its lessons too, but the ones played here), a Jade Sect disciple at Qi Kindling 9
## with a sturdy body, on Elder Hu's peak (topdown_chapter4's shortcut).
func _shortcut() -> void:
	Unlocks.grant_prologue(c().id)
	c().quests.flags["prologue_done"] = true
	c().quests.flags["night_survived"] = true
	for sc in ContentDB.all("scenes"): c().quests.scenes[str(sc.id)] = {"done": true, "skipped": true}
	c().training_sect = {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	for q in ContentDB.all("quests"):
		var chap := str(q.get("chapter", ""))
		var kind := str(q.get("kind", ""))
		if str(q.id) in PLAYED: continue
		if (kind in BEFORE and (chap in ["", "prologue"] or (chap.is_valid_int() and int(chap) <= 3))) or kind == "guided":
			c().quests.offered.erase(str(q.id))
			c().quests.active.erase(str(q.id))
			c().quests.done[str(q.id)] = 1
	_realm("qi_kindling_9")
	c().set_meta("extra_modifiers", [{"stat": "max_hp", "op": "flat", "value": 20000.0, "source": "test:sturdy"},
		{"stat": "physical_defense", "op": "flat", "value": 800.0, "source": "test:sturdy"}])
	_whole()
	Game.world.load_room(c(), "ja_elder_hu_peak", "")
	GameEvents.flush()
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(room() == "ja_elder_hu_peak" and Game.room_rt.topdown != null, "on Elder Hu's peak on the grid, Qi Kindling 9 (room %s)" % room())

func _realm(key: String) -> void:
	c().cultivator.realm_key = key
	c().cultivator.state = "cultivating"
	Unlocks.evaluate(c().id)
	GameEvents.flush()
	_whole()

func _whole() -> void:
	Game.combat.refresh_stats(c().id)
	c().pools.hp = c().pools.max_hp
	c().pools.qi = c().pools.max_qi
	Game.combat.wounded.erase(c().id)

## The character's own top-down view (main.gd mounts it so): its player bound to the character, stepped here frame by
## frame. The walk's own body (`st`) is the player's, so a talk or a portal and the motor stand at the same spot.
func _world() -> void:
	w = TopdownWorld.new()
	w.live = true
	add_child(w)
	w.set_physics_process(false)
	w.set_process(false)
	st = w.player.state
	check(w.player.bound() and Game.actor_state(c().id) == w.player.state, "the top-down view's body is the character's")

## Into a room through the World authority (a test shortcut past the walk there: topdown_chapter4 walks the road), the
## view following it.
func enter(rid: String, portal := "") -> bool:
	Game.world.load_room(c(), rid, portal)
	GameEvents.flush()
	st = w.player.state
	_sync()
	return room() == rid and Game.room_rt.topdown != null and w.room == Game.room_rt.topdown

## The motor stood where the walk's body stands (after a talk, a portal or a place()).
func _sync() -> void:
	w.player.motor.place(st.plane)
	w.player.physics_step(0.0001)

## Stand the body at a cell's centre (fractions allowed) on its floor.
func stand(cell: Vector2) -> void:
	w.player.motor.place(TopdownRoom.cell_point([cell.x, cell.y]))
	w.player.physics_step(0.0001)
	Game.tick(0.0001)   # the World authority keeps the character's spot from the body

## Frames of the game as the world runs them: the body's step under the stick (and Jump held), then the simulation.
## `each` (optional) is called after every frame and stops the run when it returns true.
func frames(n: int, axis := Vector2.ZERO, held := false, each := Callable()) -> int:
	var p = w.player
	for i in n:
		p.movement = axis
		p.joystick_engaged = axis != Vector2.ZERO
		p.jump_held = held
		motor_events.append_array(p.physics_step(DT))
		Game.tick(DT)
		GameEvents.flush()
		if each.is_valid() and each.call(): return i + 1
	p.movement = Vector2.ZERO
	p.joystick_engaged = false
	p.jump_held = false
	return n

func motor() -> TopdownMotor:
	return w.player.motor

func trav() -> TopdownTraverse:
	return TopdownTraverse.of(Game.room_rt.topdown)

# ------------------------------------------------------------------ 1: set pieces on the grid
## Every set piece with a room event whose rite circle stands in a room with a layout: started there, every point of it
## stands on open ground inside the room, reached on foot from the player, and the foes it calls stand on floors.
func _set_pieces() -> void:
	var rooms := {}
	for rid in ContentDB.rooms:
		if not TopdownRoom.has_layout(str(rid)): continue
		for o in ContentDB.room(str(rid)).get("objects", []):
			if str(o.get("type", "")) == "rite_circle" and not ContentDB.entry("set_pieces", str(o.get("event", ""))).get("room_event", {}).is_empty():
				rooms[str(o.event)] = rooms.get(str(o.event), []) + [str(rid)]
	var played := []
	for sp_id in rooms:
		for rid in rooms[sp_id]:
			check(enter(rid), "to %s on the grid for %s" % [rid, sp_id])
			var circle: Array = Game.room_rt.def.get("objects", []).filter(func(o): return str(o.get("event", "")) == sp_id)
			stand(TopdownRoom.cell_of(Vector2(float(circle[0].at[0]), float(circle[0].at[1]))) + Vector2i(0, 1))
			_whole()
			Game.world.start_room_event(c(), ContentDB.entry("set_pieces", sp_id).room_event)   # start_set_piece's own call
			var bad := _event_points_off()
			check(Game.room_rt.event.get("active", false) and bad.is_empty(), "%s in %s: every point on open ground the player walks to (%s)" % [sp_id, rid, str(bad)])
			# The foes it calls, each where it first stands (a trial lost on the ground releases them).
			var seen := {}
			var watch := func():
				_whole()
				for e in Game.room_rt.living_enemies():
					if e.summoned and not seen.has(e.uid): seen[e.uid] = e.plane
				return false
			frames(int(16.0 / DT), Vector2.ZERO, false, watch)
			var off: Array = seen.values().filter(func(p): return not _on_floor(p))
			check(not seen.is_empty() and off.is_empty(), "%s in %s: its %d foes stand on the grid's floors (%s)" % [sp_id, rid, seen.size(), str(off)])
			played.append(sp_id + "@" + rid)
	check(played.size() >= 5, "the set pieces in rooms on the grid (%s)" % str(played))
	# The summit's stage: Heaven's Cleansing's guardians come up over the south rim, at the layout's own cells.
	check(enter("cp_cleansing_summit"), "to the Cleansing Summit")
	Game.world.start_room_event(c(), ContentDB.entry("set_pieces", "heavens_cleansing").room_event)
	var pts: Array = Game.room_rt.event.get("waves", [{}])[0].get("points", [])
	check(pts.map(func(q): return TopdownRoom.cell_of(Vector2(float(q[0]), float(q[1])))) == [Vector2i(9, 26), Vector2i(31, 26)],
		"Heaven's Cleansing calls its guardians to the summit's stage, the south rim (%s)" % str(pts))
	# A set piece begun where the layout keeps the room's event cells (the Scripture Well's Riverbreath Trial): its cells.
	check(enter("ds_scripture_well"), "to the Scripture Well")
	Game.world.start_room_event(c(), ContentDB.entry("set_pieces", "riverbreath_trial").room_event)
	var well: Array = Game.room_rt.event.get("waves", [{}])[0].get("points", [])
	check(well == TopdownRoom.cell_points(Game.room_rt.topdown.def.get("event", {}).get("wave", [])) and not well.is_empty(),
		"the Riverbreath Trial's drowned rise on the Scripture Well's own event cells (%s)" % str(well))
	# A Trial Tower floor (fixed spawns and a guardian, written for the side view) on the tower's grid, by the same rule.
	check(enter("sf_fairground"), "to the Fairground, the tower's foot")
	c().tower = {"cleared": 4}
	var tw: Dictionary = Game.world.climb_tower(c(), 5)
	GameEvents.flush()   # the view follows into the tower
	var tower_off := _event_points_off()
	check(tw.get("ok", false) and room() == "sf_trial_tower" and Game.room_rt.topdown != null and tower_off.is_empty()
		and (Game.room_rt.event.get("fixed_spawns", []) as Array).size() >= 2, "a Trial Tower floor's foes on the tower's open floor (%s; %s)" % [str(tw), str(tower_off)])
	st = w.player.state
	# A room smaller than the side view's points: the Jade Body trial's x 2300 on the 1920-wide Sword Court is inside it.
	var jade: Dictionary = ContentDB.entry("set_pieces", "jade_body_trial").room_event
	check(enter("cm_sword_court"), "to the Cloud Sect's Sword Court")
	stand(Vector2(30, 20))
	Game.world.start_room_event(c(), jade)
	var mapped: Array = Game.room_rt.event.get("waves", [{}])[0].get("points", [])
	var wide: Array = jade.wave.points.filter(func(q): return float(q[0]) > Game.room_rt.topdown.w * TopdownRoom.TILE)
	check(not wide.is_empty() and mapped.size() == jade.wave.points.size() and mapped.all(func(q): return _open(q)),
		"a side-view point past the room's edge (x %s) is mapped inside it, on open ground (%s)" % [str(wide.map(func(q): return q[0])), str(mapped)])
	# The pole trial on the grid: a pole's top is off the ground (the trial runs on), the court's floor is the ground.
	var lost := {"why": ""}
	var hear := func(n: String, p: Dictionary): if n == "room_event_failed" and str(p.get("event", "")) == "jade_body_trial": lost.why = str(p.get("reason", ""))
	GameEvents.event.connect(hear)
	var pole := Vector2i(-1, -1)
	for x in Game.room_rt.topdown.w:
		for y in Game.room_rt.topdown.h:
			if pole.x < 0 and Game.room_rt.topdown.level(x, y) >= 2 and Game.room_rt.topdown.level(x, y) < TopdownRoom.SOLID: pole = Vector2i(x, y)
	stand(Vector2(pole))
	frames(int(12.0 / DT), Vector2.ZERO, false, func(): _whole(); return false)
	var held_on: bool = Game.room_rt.event.get("active", false) and lost.why == ""
	stand(Vector2(pole) + Vector2(0, 3))
	frames(int(5.0 / DT), Vector2.ZERO, false, func(): _whole(); return lost.why != "")
	GameEvents.event.disconnect(hear)
	check(pole.x >= 0 and held_on and lost.why == "ground", "the pole trial on the grid: on a pole's top (%s) it runs on, on the court's floor it is lost (%s)" % [str(pole), lost.why])
	# A rift made round the player on the grid: its foes come either side of the player on the grid's floors.
	check(enter("rm_grey_pools", "west"), "to the Grey Pools")
	stand(Vector2(33, 14))
	var ev := {"id": "spatial_rift", "duration": 60.0, "on_plane": true, "waves": [{"enemy": "hollowed_boarlet", "every_s": 5.0, "max": 3,
		"points": [[st.plane.x - 360.0, st.plane.y], [st.plane.x + 360.0, st.plane.y]]}]}
	Game.world.start_room_event(c(), ev)
	var rift: Array = Game.room_rt.event.get("waves", [{}])[0].get("points", [])
	check(rift.size() == 2 and rift.all(func(q): return _open(q)) and absf(float(rift[0][0]) - (st.plane.x - 360.0)) <= 96.0,
		"a rift's foes come either side of the player, on open ground (%s)" % str(rift))
	Game.world.load_room(c(), "rm_grey_pools", "west")   # leaves the event behind
	GameEvents.flush()
	# The sect's raid (SectAuthority.start_defence's event, its side-view points past the room's east edge) by the same rule.
	if TopdownRoom.has_layout("hv_sect_grounds"):
		check(enter("hv_sect_grounds"), "to the Sect Grounds")
		var cfg := ContentDB.config("defence")
		var raid := {"id": "sect_defence", "duration": 60.0, "wave": (cfg.get("waves", [{}])[0] as Dictionary).duplicate(true)}
		raid.wave["points"] = cfg.get("points", [[400, 860]])
		Game.world.start_room_event(c(), raid)
		var raid_off := _event_points_off()
		check(Game.room_rt.event.get("active", false) and raid_off.is_empty() and not (Game.room_rt.event.wave.points as Array).is_empty(),
			"the sect's raid comes in on the Sect Grounds' open floor (%s; off %s)" % [str(Game.room_rt.event.wave.points), str(raid_off)])
		Game.world.load_room(c(), "hv_sect_grounds", "")
		GameEvents.flush()

## The event's points that are not open ground the player walks to.
func _event_points_off() -> Array:
	var ev: Dictionary = Game.room_rt.event
	var pts: Array = []
	for wv in ev.get("waves", []): pts += wv.get("points", [])
	for sp in ev.get("fixed_spawns", []): pts.append(sp.at)
	for ts in ev.get("timed_spawns", []): pts.append(ts.at)
	var grid: TopdownRoom = Game.room_rt.topdown
	var reach := grid.reached_from(TopdownRoom.cell_of(w.player.motor.pos))
	return pts.filter(func(q): return not _open(q) or not reach.has(TopdownRoom.cell_of(Vector2(float(q[0]), float(q[1])))))

func _open(q: Array) -> bool:
	var grid: TopdownRoom = Game.room_rt.topdown
	var c0 := TopdownRoom.cell_of(Vector2(float(q[0]), float(q[1])))
	return grid.inside(c0.x, c0.y) and grid.standable(c0)

func _on_floor(p: Vector2) -> bool:
	var grid: TopdownRoom = Game.room_rt.topdown
	var c0 := TopdownRoom.cell_of(p)
	return grid.inside(c0.x, c0.y) and (grid.standable(c0) or grid.height_at(p) < INF)

# ------------------------------------------------------------------ 2: rafts
func _rafts() -> void:
	check(enter("rm_grey_pools", "west"), "to the Grey Pools on the grid")
	var tr := trav()
	check(tr != null and tr.rafts.size() == 2, "the Grey Pools float the side view's two log rafts (%s)" % str(tr.rafts.map(func(r): return r.id) if tr != null else []))
	_ride("log_raft_a", Vector2(19, 21), Vector2.LEFT, 1)
	_ride("log_raft_loop", Vector2(45.5, 17), Vector2.DOWN, 0, Vector2.UP)
	check(enter("rm_hermit_stilt_house", "stairs"), "to the Hermit's Stilt House on the grid")
	_ride("pond_raft", Vector2(12, 7), Vector2.RIGHT, 1)

## Board raft `id` from `from` (a cell on its landing) walking `on`, ride it to the end of its run (`end`: the path's
## point it waits at, 0 for its rest: a loop comes back), then step off walking `off` (default `on`). T2: `deep`, how long
## the body walks on once aboard (a deck a cell deep, a driftwood log or a plank, is boarded only just).
func _ride(id: String, from: Vector2, on: Vector2, end: int, off := Vector2.ZERO, deep := 0.25) -> void:
	var tr := trav()
	var r := tr.raft(id)
	var m := motor()
	if r.is_empty():
		check(false, "raft %s in %s" % [id, room()])
		return
	# Wait on the landing for the raft to come to rest there, at the start of its wait.
	stand(from)
	var mv: Dictionary = r.mover
	var total := 0.0
	var pts: Array = [Vector2.ZERO] + (mv.path as Array).map(func(q): return Vector2(float(q[0]), float(q[1])))
	if str(mv.mode) == "loop": pts.append(Vector2.ZERO)
	for i in range(1, pts.size()): total += (pts[i] as Vector2).distance_to(pts[i - 1])
	var leg := total / float(mv.speed)
	var cycle := (leg + float(mv.wait_s)) * (1.0 if str(mv.mode) == "loop" else 2.0)
	frames(int((cycle + 1.0) / DT), Vector2.ZERO, false, func(): return fposmod(tr.time, cycle) < 0.05)
	var start := m.pos
	var seen := boarded.size()
	frames(int(0.5 / DT), on, false, func(): return m.ride == id)
	frames(int(deep / DT), on)   # well onto the deck
	frames(int(0.12 / DT))         # T2: the stick let go, the body comes to a stop on it
	var deck := tr.raft_rect(r)
	check(m.ride == id and deck.has_point(m.pos) and boarded.slice(seen).has(id), "%s: boarded from its landing (%s; heard %s)" % [id, str(m.ride), str(boarded.slice(seen))])
	# Carried: stand still while it runs; never a splash nor a sink, the body moving with the deck.
	var dry := {"ok": true, "moved": false}
	var rel := m.pos - deck.position
	var target: Vector2 = (r.rest as Rect2).position + (pts[end] as Vector2)
	var arrived := func():
		if m.sink_t >= 0.0 or not m.grounded: dry.ok = false
		var d := tr.raft_rect(r)
		if d.position.distance_to(deck.position) > 8.0: dry.moved = true
		return bool(dry.moved) and d.position.distance_to(target) < 0.5
	frames(int((leg + float(mv.wait_s) + 2.0) / DT), Vector2.ZERO, false, arrived)
	var now := tr.raft_rect(r)
	check(bool(dry.ok) and m.ride == id and (m.pos - now.position).distance_to(rel) < 2.0 and now.position.distance_to(target) < 0.5,
		"%s: carried its rider %d units to the end of its run, standing on the deck, no splash (dry %s, ride %s, slid %.1f, off its end %.1f)"
			% [id, int(start.distance_to(m.pos)), str(dry.ok), m.ride, (m.pos - now.position).distance_to(rel), now.position.distance_to(target)])
	frames(int(0.9 / DT), off if off != Vector2.ZERO else on)
	var cp := TopdownRoom.cell_of(m.pos)
	check(m.ride == "" and m.grounded and m.sink_t < 0.0 and not Game.room_rt.topdown.is_water(cp.x, cp.y),
		"%s: stepped off onto the far landing (cell %s)" % [id, str(cp)])

# ------------------------------------------------------------------ 3: Leaf on the Wind on the grid
func _leaf_on_the_wind() -> void:
	check(c().quests.offered.has("leaf_on_the_wind") or Game.quest.can_offer(c(), ContentDB.entry("quests", "leaf_on_the_wind")), "Leaf on the Wind is on offer")
	check(enter("ja_elder_hu_peak"), "to Elder Hu")
	accept("elder_hu", "leaf_on_the_wind")
	check(Game.combat.knows_art(c(), "glide"), "Falling Leaf Glide learned as it is accepted")
	check(enter("cf_falls_pool", "west"), "to the Falls Pool on the grid")
	var tr := trav()
	var vine := tr.climb("falls_vine")
	var up: Dictionary = tr.updrafts[0] if tr != null and not tr.updrafts.is_empty() else {}
	check(not vine.is_empty() and str(vine.kind) == "vine" and not up.is_empty(), "the Falls Pool has its vine and the falls' updraft on the grid")
	var m := motor()
	# The vine: held toward the face at its foot, the body climbs to the spray ledge (3 levels up: no jump reaches it).
	stand(Vector2(34, 8))
	climbs.clear()
	frames(int(0.5 / DT), Vector2.UP, false, func(): return not m.climbing.is_empty())
	check(not m.climbing.is_empty() and Game.combat.climbing(c().id), "held toward the vine, the body climbs on (Combat sees it climbing)")
	var hit := Game.submit({"type": "basic_attack", "facing": 1, "aim": Vector2.UP})
	check(not hit.get("ok", false), "no blow on the vine (%s)" % str(hit.get("reason", "")))
	w.player.sync(DT)
	check(w.player.pose == w.player.CLIMB_POSE and m.row == "n", "it climbs in the hang pose, facing the face (%s, %s)" % [w.player.pose, m.row])
	frames(int(3.0 / DT), Vector2.UP, false, func(): return m.climbing.is_empty())
	check(m.grounded and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5 and climbs.any(func(e): return e[0] == "finished" and e[1] == "falls_vine" and e[2] == "top"),
		"up the vine onto the spray ledge, three levels up (z %.0f; %s)" % [m.z, str(climbs)])
	# Glide 1: off the ledge's west end over the falls' spray to the lotus rock; the spray lifts the glider on the way.
	stand(Vector2(30.4, 6.6))
	var rock := Rect2(Vector2(22, 11) * TopdownRoom.TILE, Vector2(4, 4) * TopdownRoom.TILE).grow(-6.0)
	var g0 := int(arts.get("glide", 0))
	var lifted := _glide_to(rock, Vector2(-1, 1).normalized())
	check(int(arts.get("glide", 0)) == g0 + 1 and lifted, "a glide off the ledge counts, and the falls' spray lifts the glider (%d)" % int(arts.get("glide", 0)))
	check(m.grounded and m.sink_t < 0.0 and rock.has_point(m.pos) and absf(m.z - TopdownRoom.LEVEL) < 0.5,
		"the glide carries the body over the pool to the lotus rock (%s, z %.0f)" % [str(TopdownRoom.cell_of(m.pos)), m.z])
	# Off the ledge's south side, clear of the spray, a jump without the glide falls short into the pool (and back to the
	# last safe spot).
	stand(Vector2(32.5, 7))
	var splash := {"hit": false}
	frames(1, Vector2.DOWN)
	w.player.jump()
	frames(int(2.5 / DT), Vector2.DOWN, false, func(): splash.hit = splash.hit or m.sink_t >= 0.0; return m.grounded and m.sink_t < 0.0 and splash.hit)
	check(bool(splash.hit), "a jump off the ledge without the glide, clear of the spray, falls short into the pool")
	# Glide 2: from the lotus rock up the falls' spray to the ledge a jump cannot reach (level 3 from level 1).
	stand(Vector2(25.0, 11.4))
	var ledge := Rect2(Vector2(30, 6) * TopdownRoom.TILE, Vector2(5, 2) * TopdownRoom.TILE).grow(-4.0)
	check(m.apex() + TopdownRoom.LEVEL + m.mantle < 3.0 * TopdownRoom.LEVEL, "a jump from the rock does not reach the ledge (apex %.0f)" % m.apex())
	var rose := _glide_to(ledge, Vector2(1, -0.6).normalized())
	check(rose and m.grounded and ledge.grow(5.0).has_point(m.pos) and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5,
		"the updraft carries a glide up the falls' spray onto the spray ledge (%s, z %.0f)" % [str(TopdownRoom.cell_of(m.pos)), m.z])
	GameEvents.flush()
	check(str(c().quests.active.get("leaf_on_the_wind", {}).get("state", "")) == "ready", "Leaf on the Wind's two glides done on the grid (%s)" % str(c().quests.active.get("leaf_on_the_wind", {})))
	check(enter("ja_elder_hu_peak"), "back to Elder Hu")
	hand_in("elder_hu", "leaf_on_the_wind")

## Jump along `way` with Jump held: the glide starts as the body comes down, steered at `goal`'s middle; once over it
## Jump is let go and the body comes down on it. True when an updraft lifted the body on the way.
func _glide_to(goal: Rect2, way: Vector2) -> bool:
	var m := motor()
	var p = w.player
	var lifted := {"up": false}
	frames(2, way)
	p.jump()
	var each := func():
		if not m.gliding: pass
		elif m.vz > 0.0 and not m.updraft_here().is_empty(): lifted.up = true
		return m.grounded
	for i in int(6.0 / DT):
		var over := goal.has_point(m.pos)
		var aim := (goal.get_center() - m.pos).normalized() if not over else Vector2.ZERO
		if frames(1, aim if i > 4 else way, not over, each) == 1 and m.grounded: break
	return bool(lifted.up)

# ------------------------------------------------------------------ 4: the rope, and a shut climbable
func _rope() -> void:
	check(enter("cf_falls_pool", "west"), "to the Falls Pool")
	var m := motor()
	var rope := trav().climb("falls_step_rope")
	stand(Vector2(14.4, 7.0))
	climbs.clear()
	frames(int(0.6 / DT), Vector2.LEFT, false, func(): return not m.climbing.is_empty())
	frames(int(3.0 / DT), Vector2.LEFT, false, func(): return m.climbing.is_empty())
	check(not rope.is_empty() and m.grounded and absf(m.z - 2.0 * TopdownRoom.LEVEL) < 0.5, "up the rope onto the falls ledge (z %.0f)" % m.z)
	# Down again from its top: the stick held over the edge toward the foot.
	frames(int(0.6 / DT), Vector2.RIGHT, false, func(): return not m.climbing.is_empty())
	frames(int(3.0 / DT), Vector2.RIGHT, false, func(): return m.climbing.is_empty())
	check(m.grounded and absf(m.z) < 0.5 and climbs.any(func(e): return e[2] == "foot"), "and down it again to its foot (%s)" % str(climbs))
	# A jump off the face lets go: the body drops back to the foot's floor.
	frames(int(0.6 / DT), Vector2.LEFT, false, func(): return not m.climbing.is_empty())
	frames(int(0.3 / DT), Vector2.LEFT)
	w.player.jump()
	frames(int(1.5 / DT), Vector2.ZERO, false, func(): return m.grounded)
	check(m.climbing.is_empty() and m.grounded and absf(m.z) < 0.5 and climbs.any(func(e): return e[2] == "jump"), "a jump on the rope lets go, down to its foot")
	# A sealed climbable (its side-view row's requires) stays shut on the grid and says why.
	var row: Dictionary = ContentDB.room("cf_falls_pool").climbables.filter(func(cl): return str(cl.id) == "falls_step_rope")[0]
	row["requires"] = {"all": [{"kind": "flag", "flag": "t1_never"}]}
	stand(Vector2(14.4, 7.0))
	frames(int(0.8 / DT), Vector2.LEFT)
	check(m.climbing.is_empty(), "a sealed climbable stays shut on the grid (the World authority's climbable_open)")
	row.erase("requires")

# ------------------------------------------------------------------ 5: Skipping Stones
func _skipping_stones() -> void:
	_realm("qi_unfurling_8")
	check(enter("rm_hermit_stilt_house", "stairs"), "to the hermit's on the grid")
	accept("hermit_yao", "skipping_stones")
	check(Game.combat.knows_art(c(), "water_skimming"), "Water Skimming learned as Skipping Stones is accepted")
	_sync()
	var m := motor()
	var s0 := int(arts.get("water_skimming", 0))
	stand(Vector2(9.4, 13.5))
	frames(int(1.2 / DT), Vector2.RIGHT)
	check(int(arts.get("water_skimming", 0)) > s0 and m.sink_t < 0.0, "running out over the pond is Water Skimming (heard %d)" % int(arts.get("water_skimming", 0)))
	check(interact("pond_lotus").get("ok", false) or c().inventory.count("mist_lotus") > 0, "the mist lotus on the pond's rock")
	for i in 30:
		if c().inventory.count("mist_lotus") > 0: break
		step(0.5)
		interact("pond_lotus")
	GameEvents.flush()
	check(str(c().quests.active.get("skipping_stones", {}).get("state", "")) == "ready", "Skipping Stones done on the grid (%s)" % str(c().quests.active.get("skipping_stones", {})))
	hand_in("hermit_yao", "skipping_stones")

# ------------------------------------------------------------------ 6: Swallow Dart and the Cloud Ladder Step
func _dart_and_ladder() -> void:
	check(enter("cf_falls_pool", "west"), "to the Falls Pool for the air's arts")
	var m := motor()
	if not c().quests.is_active("swallow_dart"): submit({"type": "accept_quest", "quest": "swallow_dart"})
	check(Game.combat.knows_art(c(), "air_dash"), "Swallow Dart learned as its lesson is accepted")
	var darts := 0
	for i in 3:
		c().pools.cooldowns.erase("dodge")
		stand(Vector2(40, 22))
		frames(1, Vector2.RIGHT)
		w.player.jump()
		frames(int(0.18 / DT), Vector2.RIGHT)
		var x0 := m.pos.x
		var z0 := m.z
		w.player.dodge()
		frames(int(0.2 / DT), Vector2.RIGHT)
		if m.pos.x - x0 > 80.0 and absf(m.z - z0) < 6.0: darts += 1
		frames(int(1.5 / DT), Vector2.ZERO, false, func(): return m.grounded)
	GameEvents.flush()
	check(darts == 3 and str(c().quests.active.get("swallow_dart", {}).get("state", "")) == "ready",
		"three Swallow Darts along the stick, the height held, Swallow Dart's objective done on the grid (%d; %s)" % [darts, str(c().quests.active.get("swallow_dart", {}))])
	if not c().quests.is_active("cloud_ladder"): submit({"type": "accept_quest", "quest": "cloud_ladder"})
	check(Game.combat.knows_art(c(), "double_jump"), "the Cloud Ladder Step learned as its lesson is accepted")
	var higher := 0
	for i in 3:
		stand(Vector2(40, 22))
		w.player.jump()
		frames(int(0.2 / DT))
		var before := m.peak
		w.player.jump()
		var top := {"z": 0.0}
		frames(int(1.5 / DT), Vector2.ZERO, false, func(): top.z = maxf(top.z, m.z); return m.grounded)
		if float(top.z) > m.apex() + 20.0 and float(top.z) > before: higher += 1
	GameEvents.flush()
	check(higher == 3 and str(c().quests.active.get("cloud_ladder", {}).get("state", "")) == "ready",
		"three second jumps in the air reach past a jump's apex, the Cloud Ladder's objective done on the grid (%d; %s)" % [higher, str(c().quests.active.get("cloud_ladder", {}))])

# ------------------------------------------------------------------ 7: Wall-Step and a bounce
func _wall_and_bounce() -> void:
	var m := motor()
	# The art as Between Two Walls teaches it (a test shortcut: that lesson is the Echo Cliffs').
	Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "wall_step"}], "test")
	check(Game.combat.knows_art(c(), "wall_step"), "Wall-Step learned")
	var w0 := int(arts.get("wall_step", 0))
	stand(Vector2(40, 6.4))   # under the cliff (level 4) on the shore
	frames(int(0.3 / DT), Vector2.UP)   # up against its face
	w.player.jump()
	frames(int(0.12 / DT), Vector2.UP)
	var z0 := m.z
	w.player.jump()
	frames(1, Vector2.UP)
	check(m.wall_kicks == 1 and m.vz > 0.0 and int(arts.get("wall_step", 0)) == w0 + 1, "Wall-Step kicks off the cliff's face pushed into (kicks %d, z %.0f from %.0f)" % [m.wall_kicks, m.z, z0])
	frames(int(1.5 / DT), Vector2.ZERO, false, func(): return m.grounded)
	# A drum: a bounce laid on the grid where the body stands launches it straight back up when it lands there.
	var tr := trav()
	var cell := TopdownRoom.cell_of(m.pos)
	tr.bounces.append({"id": "t1_drum", "kind": "bounce", "rect": Rect2(Vector2(cell) * TopdownRoom.TILE, Vector2.ONE * TopdownRoom.TILE),
		"z": m.z, "speed": float(TopdownTraverse.conf("bounce_speed", 528.0))})
	var b0 := int(arts.get("bounce", 0))
	var top := {"z": m.z}
	var ground := m.z
	w.player.jump()
	frames(int(1.2 / DT), Vector2.ZERO, false, func(): top.z = maxf(top.z, m.z); return false)
	tr.bounces.pop_back()
	check(int(arts.get("bounce", 0)) > b0 and float(top.z) - ground > m.apex() + 20.0, "a landing on a bounce launches the body higher than its jump (%.0f over %.0f)" % [float(top.z) - ground, m.apex()])

# ------------------------------------------------------------------ 8: a lift, rotten boards
## The Falls Pool, for the parts that lay their own rows on its grid (each part stands alone under --only).
func _falls_pool() -> bool:
	return room() == "cf_falls_pool" or enter("cf_falls_pool", "west")

## Water Skimming set aside for a part that wants a body the water takes (a skimmer runs on it), and T2's Breath Control
## (a swimmer swims it; the realm the parts reach knows it): the arts that were known.
func _unskim() -> Array:
	var had: Array = ["water_skimming", "breath_control"].filter(func(a): return c().cultivator.secret_arts.has(a))
	for a in had: c().cultivator.secret_arts.erase(a)
	return had

func _reskim(had: Array) -> void:
	for a in had:
		if not c().cultivator.secret_arts.has(a): c().cultivator.secret_arts.append(a)

## A lift (a crane's basket, a trial's plank) laid at the foot of the Falls Pool's cliff (level 4): boarded from the
## shore it sets off, carries its rider up four levels to the cliff's top, the rider steps off onto the cliff, and the
## lift goes back down without it. Rotten boards over the pool's edge hold a foot, give way under it into the water
## (the body back on its last safe spot) and are back after their time.
func _lift_and_boards() -> void:
	check(_falls_pool(), "to the Falls Pool for a lift and rotten boards")
	var skim := _unskim()
	var m := motor()
	var tr := trav()
	var L := TopdownRoom.LEVEL
	tr.rafts.append({"id": "t1_lift", "kind": "lift", "rest": Rect2(40.0 * 32.0, 6.0 * 32.0, 64.0, 64.0), "z": 0.0,
		"mover": {"surface": "t1_lift", "path": [[0.0, 0.0, 4.0 * L]], "speed": 64.0, "wait_s": 1.5, "mode": "trigger", "trigger_t": -1.0}})
	var lift: Dictionary = tr.rafts.back()
	var seen := boarded.size()
	stand(Vector2(40.5, 6.5))
	frames(2)
	check(m.ride == "t1_lift" and boarded.slice(seen).has("t1_lift") and float(lift.mover.trigger_t) >= 0.0,
		"stepping onto a lift boards it and sets it off (%s; heard %s)" % [m.ride, str(boarded.slice(seen))])
	frames(int(2.3 / DT), Vector2.ZERO, false, func(): return tr.deck_z(lift) >= 4.0 * L - 0.01)
	frames(2)   # the body's step follows the deck the clock has raised
	check(m.grounded and absf(m.z - 4.0 * L) < 1.0 and m.sink_t < 0.0, "the lift carries its rider up four levels (z %.0f)" % m.z)
	frames(int(0.5 / DT), Vector2.UP)
	var cp := TopdownRoom.cell_of(m.pos)
	check(cp.y <= 5 and m.grounded and absf(m.z - 4.0 * L) < 1.0 and m.ride == "", "stepped off the lift onto the cliff's top (cell %s, z %.0f)" % [str(cp), m.z])
	frames(int(4.0 / DT), Vector2.ZERO, false, func(): return float(lift.mover.trigger_t) < 0.0)
	check(tr.deck_z(lift) < 0.5 and absf(m.z - 4.0 * L) < 1.0, "the lift went back down without its rider, who stays on the cliff (deck %.0f)" % tr.deck_z(lift))
	tr.rafts.erase(lift)
	# Rotten boards over the pool's edge (row 9: water to x 37, the shore from 38).
	tr.crumbles.append({"id": "t1_boards", "kind": "crumble", "rect": Rect2(36.0 * 32.0, 9.0 * 32.0, 64.0, 32.0), "z": 0.0,
		"break_s": 0.8, "return_s": 2.0, "start": -1.0})
	var boards: Dictionary = tr.crumbles.back()
	stand(Vector2(38.5, 9.0))
	frames(int(0.6 / DT), Vector2.LEFT, false, func(): return not tr.crumble_at(m.pos).is_empty())
	frames(int(0.15 / DT))
	check(m.grounded and absf(m.z) < 0.5 and tr.crumble_state(boards) == "giving" and Game.room_rt.topdown.is_water(TopdownRoom.cell_of(m.pos).x, TopdownRoom.cell_of(m.pos).y),
		"rotten boards over the water hold a foot, and start to give way (%s, z %.0f)" % [tr.crumble_state(boards), m.z])
	var safe := m.safe   # the last spot on the shore (never the boards over the water)
	var fell := {"sank": false}
	frames(int(2.0 / DT), Vector2.ZERO, false, func(): fell.sank = bool(fell.sank) or m.sink_t >= 0.0; return bool(fell.sank) and m.grounded and m.sink_t < 0.0)
	check(bool(fell.sank) and m.grounded and m.pos.distance_to(safe) < 1.0 and not Game.room_rt.topdown.is_water(TopdownRoom.cell_of(m.pos).x, TopdownRoom.cell_of(m.pos).y),
		"the boards gave way into the water; the body is back on its last safe spot (%s, sank %s)" % [str(TopdownRoom.cell_of(m.pos)), str(fell.sank)])
	frames(int(2.5 / DT))
	check(tr.crumble_state(boards) == "whole" and absf(m.floor_at(boards.rect.get_center())) < 0.5, "the boards are back after their time")
	tr.crumbles.erase(boards)
	_reskim(skim)

# ------------------------------------------------------------------ 9: a current, rising water
## A current over the Falls Pool's shore pushes a body standing in it (not one in the air); a flood laid there rises on
## its side-view volume's script (a boss's phase, through the World authority), sends the body standing in it to the
## nearest dry floor, holds, and goes back down.
func _current_and_flood() -> void:
	check(_falls_pool(), "to the Falls Pool for a current and rising water")
	var skim := _unskim()
	var m := motor()
	var tr := trav()
	var area := Rect2(44.0 * 32.0, 12.0 * 32.0, 7.0 * 32.0, 3.0 * 32.0)   # the shore east of the pool
	tr.currents.append({"id": "t1_current", "kind": "current", "rect": area, "push": Vector2(-60.0, 0.0)})
	stand(Vector2(48.5, 13.0))
	var x0 := m.pos.x
	frames(int(1.0 / DT))
	check(x0 - m.pos.x > 40.0 and x0 - m.pos.x < 80.0 and m.grounded, "a current pushes a body standing in it (%.0f units in a second)" % (x0 - m.pos.x))
	tr.currents.pop_back()
	tr.floods.append({"id": "t1_flood", "kind": "flood", "rect": area, "top": TopdownRoom.LEVEL, "goal": {}, "level": -INF,
		"rises": [{"event": "boss_phase", "match": {"boss": "t1_flood"}, "to": 32, "over_s": 1.0, "hold_s": 1.5, "back_to": 0}]})
	var flood: Dictionary = tr.floods.back()
	stand(Vector2(47.5, 13.0))
	check(absf(m.floor_at(area.get_center())) < 0.5, "the flood's cells are dry ground at rest")
	GameEvents.emit_event("boss_phase", {"boss": "t1_flood", "action": "t1"})
	GameEvents.flush()
	var wet := {"sank": false}
	frames(int(1.5 / DT), Vector2.ZERO, false, func(): wet.sank = bool(wet.sank) or m.sink_t >= 0.0; return false)
	check(tr.flood_k(flood) >= 1.0 and m.floor_at(area.get_center()) == TopdownRoom.WATER_Z, "a boss's phase raises the flood over its cells")
	frames(int(1.0 / DT), Vector2.ZERO, false, func(): return m.grounded and m.sink_t < 0.0)
	check(bool(wet.sank) and m.grounded and m.sink_t < 0.0 and not area.has_point(m.pos) and absf(m.z) < 0.5,
		"the body the water rose over is back on the nearest dry floor (%s)" % str(TopdownRoom.cell_of(m.pos)))
	frames(int(3.0 / DT), Vector2.ZERO, false, func(): return flood.goal.is_empty())
	check(tr.flood_k(flood) == 0.0 and absf(m.floor_at(area.get_center())) < 0.5, "the water goes back down after its hold")
	tr.floods.erase(flood)
	_reskim(skim)

# ------------------------------------------------------------------ 10: flight
## Cloud Stride's flight on the grid: Jump held as the body comes down takes to the air (Wings of Cloud's first
## objective), held it climbs past any jump to its ceiling, let go it holds its height as it flies along the stick,
## Evade held brings it down to land; out of QI it falls; where flight is refused the same hold glides.
func _flight() -> void:
	_realm("cloud_stride_1")
	check(_falls_pool(), "to the Falls Pool to fly")
	if not Game.combat.knows_art(c(), "glide"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "falling_leaf_glide"}], "test")
	if not c().quests.is_active("wings_of_cloud"): submit({"type": "accept_quest", "quest": "wings_of_cloud"})
	GameEvents.flush()
	check(c().quests.is_active("wings_of_cloud") and Unlocks.is_unlocked(c().id, "flight"), "at Cloud Stride 1, Wings of Cloud accepted opens flight")
	var m := motor()
	stand(Vector2(40, 22))
	w.player.jump()
	frames(int(1.6 / DT), Vector2.ZERO, true)
	var prog: Array = c().quests.active.get("wings_of_cloud", {}).get("progress", [0])
	check(m.flying and Game.combat.is_flying(c().id) and st.flying and m.z > m.apex() + 40.0,
		"Jump held as the body comes down takes to the air, and climbs past a jump (z %.0f, apex %.0f)" % [m.z, m.apex()])
	check(int(prog[0]) >= 1, "Wings of Cloud's 'take to the air' is done on the grid (%s)" % str(prog))
	var p0 := m.pos
	var z0 := m.z
	frames(int(0.5 / DT), Vector2.RIGHT)
	check(m.flying and absf(m.z - z0) < 1.0 and m.pos.x - p0.x > 60.0, "let go, the flier holds its height and flies along the stick (%.0f units, z %.0f to %.0f)" % [m.pos.x - p0.x, z0, m.z])
	w.player.fly_down = true
	frames(int(4.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	w.player.fly_down = false
	frames(2)
	check(m.grounded and not m.flying and not Game.combat.is_flying(c().id) and not st.flying, "Evade held brings the flier down; landing ends the flight")
	# Out of QI the flight ends and the body falls.
	_whole()
	stand(Vector2(40, 22))
	w.player.jump()
	frames(int(0.6 / DT), Vector2.ZERO, true)
	var flew := m.flying
	c().pools.qi = 0.0
	frames(int(3.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	check(flew and m.grounded and not m.flying and not Game.combat.is_flying(c().id), "out of QI the flight ends and the body comes down")
	_whole()
	# Where flight is refused (an interior, a sect's grounds, a room that forbids it) the same hold glides.
	Game.room_rt.def["no_flight"] = true
	stand(Vector2(40, 22))
	w.player.jump()
	var glid := {"on": false}
	frames(int(0.6 / DT), Vector2.ZERO, true, func(): glid.on = bool(glid.on) or st.gliding; return false)
	check(not m.flying and not Game.combat.is_flying(c().id) and bool(glid.on), "where flight is refused the hold glides instead (flying %s, glided %s, knows %s)" % [str(m.flying), str(glid.on), str(Game.combat.knows_art(c(), "glide"))])
	frames(int(2.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	Game.room_rt.def.erase("no_flight")

# ------------------------------------------------------------------ 11: a mount
## A ground mount on the grid: the rider goes at its pace (PetAuthority.mount_speed), steps down to climb the rope and
## back on at its top (PetAuthority's climb_started / climb_finished, heard from the grid's climb), and kicks off no wall.
func _mount() -> void:
	check(_falls_pool(), "to the Falls Pool to ride")
	var m := motor()
	c().cultivator.unlocked["mounts"] = true   # a test shortcut: the Beast Hall's Mount slot opens later in the story
	Game.pets.apply_grant(c().id, "riverstone_ox")
	var ox: Dictionary = c().pets.back()
	check(Game.submit({"type": "set_mount", "pet": ox.uid}).get("ok", false) and c().riding, "the Riverstone Ox in the Mount slot, ridden")
	Game.submit({"type": "set_mount", "on": false})
	stand(Vector2(34, 22))
	frames(int(0.6 / DT), Vector2.RIGHT)
	var walked := m.pos.x - TopdownRoom.cell_point([34, 22]).x
	Game.submit({"type": "set_mount", "on": true})
	stand(Vector2(34, 22))
	frames(int(0.6 / DT), Vector2.RIGHT)
	var rode := m.pos.x - TopdownRoom.cell_point([34, 22]).x
	var k := rode / maxf(1.0, walked)
	check(absf(k - Game.pets.mount_speed(c())) < 0.15, "the ox carries its rider at its pace on the grid (x%.2f, the mount's x%.2f; %.0f walked, %.0f rode)" % [k, Game.pets.mount_speed(c()), walked, rode])
	if not Game.combat.knows_art(c(), "wall_step"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "wall_step"}], "test")
	frames(1)
	check(Game.combat.knows_art(c(), "wall_step") and not m.wall_step, "no Wall-Step kick from a ground mount")
	# The rope: the rider steps down to climb it, and back on at the landing.
	var off := {"all_the_way": true}   # off the ox for every frame on the rope
	stand(Vector2(14.4, 7.0))
	frames(int(0.6 / DT), Vector2.LEFT, false, func(): return not m.climbing.is_empty())
	frames(int(3.0 / DT), Vector2.LEFT, false, func():
		if not m.climbing.is_empty() and not Game.pets.mount_of(c()).is_empty(): off.all_the_way = false
		return m.climbing.is_empty())
	frames(2)
	check(bool(off.all_the_way) and m.grounded and absf(m.z - 2.0 * TopdownRoom.LEVEL) < 0.5 and not Game.pets.mount_of(c()).is_empty(),
		"the rider steps down to climb the rope and is back on the ox at its top (z %.0f)" % m.z)
	Game.submit({"type": "set_mount", "on": false})
	c().cultivator.unlocked.erase("mounts")

# ------------------------------------------------------------------ 12: the Plunge from a roof
## The Outer Trial's "Climb a roof and Plunge to the practice ground", on the Pavilion Rooftops' grid: off the roof's
## south edge (walked off the eaves), the Plunge drops the body straight down, and the objective counts it.
func _plunge() -> void:
	check(enter("ja_pavilion_rooftops", "west"), "to the Pavilion Rooftops on the grid")
	var m := motor()
	if not Game.combat.knows_art(c(), "plunge"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "plunge"}], "test")
	# The trial again, its spars won (a test shortcut: the shortcut took chapter 1 as done).
	c().quests.done.erase("outer_trial")
	c().quests.active["outer_trial"] = {"state": "active", "progress": [3, 0], "accepted_tick": 0}
	c().pools.cooldowns.erase("plunge")
	stand(Vector2(44, 8))   # west of the roof's stair (x 48-50)
	check(absf(m.z - 2.0 * TopdownRoom.LEVEL) < 0.5, "on the pavilion's roof (z %.0f)" % m.z)
	frames(int(0.8 / DT), Vector2.DOWN, false, func(): return not m.grounded)   # off the eaves
	frames(2, Vector2.DOWN)
	var r: Dictionary = w.player.plunge()
	var dropped := {"fast": false}
	frames(int(1.5 / DT), Vector2.ZERO, false, func(): dropped.fast = bool(dropped.fast) or m.vz < -600.0; return m.grounded)
	GameEvents.flush()
	var prog: Array = c().quests.active.get("outer_trial", {}).get("progress", [0, 0])
	check(r.get("ok", false) and bool(dropped.fast) and m.grounded and absf(m.z) < 0.5 and int(prog[1]) >= 1,
		"off the roof the Plunge drops straight down, and the Outer Trial counts it on the grid (%s; %s; fast %s, z %.0f, grounded %s)" % [str(r), str(prog), str(dropped.fast), m.z, str(m.grounded)])

# ================================================================== T2: the Act I rooms' rows (topdown_mechanics.md)
## Frames until `cond` holds (at most `secs`), the stick at `axis`: true when it held.
func until(secs: float, cond: Callable, axis := Vector2.ZERO, held := false) -> bool:
	return frames(int(secs / DT), axis, held, cond) < int(secs / DT) or cond.call()

# ------------------------------------------------------------------ 13: Cloud Lung's air distance on the grid
## Wings of Cloud's last leftover on the grid: flight north counts toward Cloud Lung as flight east does (CombatFlight's
## air distance reads the plane's speed on the grid, not the side view's x alone).
func _air_distance() -> void:
	_realm("cloud_stride_1")
	check(_falls_pool(), "to the Falls Pool to fly for Cloud Lung")
	if not c().quests.is_active("wings_of_cloud") and not c().quests.is_done("wings_of_cloud"): submit({"type": "accept_quest", "quest": "wings_of_cloud"})
	GameEvents.flush()
	var m := motor()
	var gained := {}
	for way in [Vector2.UP, Vector2.RIGHT]:
		_whole()
		stand(Vector2(40, 22))
		w.player.jump()
		frames(int(0.9 / DT), Vector2.ZERO, true)   # up to the flight's ceiling
		var a0 := float(c().cultivator.lifetime_stats.get("air_metres", 0.0))
		var p0 := m.pos
		frames(int(0.8 / DT), way)
		gained[way] = [float(c().cultivator.lifetime_stats.get("air_metres", 0.0)) - a0, m.pos.distance_to(p0), m.flying]
		w.player.fly_down = true
		frames(int(4.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
		w.player.fly_down = false
		frames(2)
	var north: Array = gained[Vector2.UP]
	var east: Array = gained[Vector2.RIGHT]
	check(bool(north[2]) and float(north[0]) > 0.0 and float(north[1]) > 60.0,
		"a flight north counts toward Cloud Lung on the grid, where the side view's x alone counts nothing (%.2f m over %.0f units)" % [float(north[0]), float(north[1])])
	check(absf(float(north[0]) - float(east[0])) < maxf(float(east[0]), 0.01) * 0.25, "as much as the same flight east (%.2f m north, %.2f m east)" % [float(north[0]), float(east[0])])

# ------------------------------------------------------------------ 14: sealed ladders as hatches
## The side view's sealed ladders on the grid: a hatch over the loft's or the gallery's flight, shut while the World
## authority's climbable_open refuses the side view's climbable (its `requires`), and open once the quest or the rank is
## there: Old Ma's storeroom and the Fisher's Hut's loft (The Runaway Kite), the two libraries' galleries (sect rank).
func _sealed_ladders() -> void:
	var kite_done: bool = c().quests.done.has("the_runaway_kite")
	c().quests.done.erase("the_runaway_kite")
	for row in [["lf_old_ma_store", "exit", "storeroom_ladder", Vector2(4, 6), 2.0], ["lf_fishers_hut", "exit", "loft_ladder", Vector2(13, 6), 2.0]]:
		check(enter(str(row[0]), str(row[1])), "to %s on the grid" % row[0])
		_hatch_climb(str(row[2]), row[3], 0.0, false, "before The Runaway Kite")
		c().quests.done["the_runaway_kite"] = 1
		_hatch_climb(str(row[2]), row[3], float(row[4]), true, "once The Runaway Kite is done")
		c().quests.done.erase("the_runaway_kite")
	if kite_done: c().quests.done["the_runaway_kite"] = 1
	var rank := str(c().training_sect.get("rank", ""))
	for lib in [["ja_library", 7], ["cm_cloud_library", 19]]:
		check(enter(str(lib[0]), "exit"), "to %s on the grid" % lib[0])
		var x := int(lib[1])
		c().training_sect.rank = "service_disciple"
		_hatch_climb("floor_2_ladder", Vector2(x, 14), 0.0, false, "for a Service Disciple")
		c().training_sect.rank = "outer_disciple"
		_hatch_climb("floor_2_ladder", Vector2(x, 14), 2.0, true, "for an Outer Disciple")
		_hatch_climb("floor_3_ladder", Vector2(x, 7), 2.0, false, "the second, for an Outer Disciple")
		c().training_sect.rank = "inner_disciple"
		_hatch_climb("floor_3_ladder", Vector2(x, 7), 1.0, true, "for an Inner Disciple")
	c().training_sect.rank = rank

## From `cell` south of a hatch's flight, the stick pushed north for two seconds: the body ends `levels` up (open) or
## stays at the flight's foot (shut), and the hatch says so.
func _hatch_climb(id: String, cell: Vector2, levels: float, open: bool, why: String) -> void:
	var m := motor()
	var tr := trav()
	var h: Dictionary = {}
	for x in tr.hatches if tr != null else []:
		if str(x.id) == id: h = x
	stand(cell)
	var z0 := m.z
	frames(int(0.6 / DT))   # the hatch is asked as the room is entered and every half second
	frames(int(2.0 / DT), Vector2.UP)
	var up := (m.z - z0) / TopdownRoom.LEVEL
	if open: check(not h.is_empty() and not bool(h.shut) and absf(up - levels) < 0.1, "%s in %s: the hatch is open %s, up the flight %.1f levels" % [id, room(), why, up])
	else: check(not h.is_empty() and bool(h.shut) and up < 0.5 and str(h.text) != "", "%s in %s: the hatch is shut %s (%s), the body stays at the flight's foot (up %.1f)" % [id, room(), why, str(h.get("text", "")), up])

# ------------------------------------------------------------------ 15: Reed Shallows' driftwood and Bend Shore's ferry
func _act1_rafts() -> void:
	var skim := _unskim()
	check(enter("lf_reed_shallows", "west"), "to the Reed Shallows on the grid")
	check(trav() != null and trav().rafts.size() == 3, "the Reed Shallows float the side view's three driftwood logs")
	_ride("driftwood_a", Vector2(14, 22), Vector2.DOWN, 1, Vector2.UP, 0.04)
	_ride("driftwood_b", Vector2(45, 22), Vector2.DOWN, 1, Vector2.UP, 0.04)
	_ride("driftwood_c", Vector2(50, 22), Vector2.DOWN, 1, Vector2.UP, 0.04)
	check(enter("dw_bend_shore", "east"), "to Bend Shore on the grid")
	_ride("ferry_boat", Vector2(32, 25.5), Vector2.RIGHT, 1)
	_reskim(skim)

# ------------------------------------------------------------------ 16: bounces
## The Fairground's drum, the Whispering Bamboo's bent culm and the Grey Pools' lotus leaf: a landing on each launches the
## body higher than its jump, and steered it comes down a level or two up (the hall's roof, the knoll, the lily ledge).
func _bounces() -> void:
	for row in [["sf_fairground", "west", "fair_drum_bounce", Vector2(36, 10), Vector2.UP, 2.0],
			["bg_whispering_bamboo", "west", "bent_bamboo_bounce", Vector2(42, 7), Vector2.UP, 1.0],
			["rm_grey_pools", "west", "lily_bounce", Vector2(44, 9), Vector2.RIGHT, 1.0]]:
		check(enter(str(row[0]), str(row[1])), "to %s on the grid" % row[0])
		var m := motor()
		stand(row[3])
		var z0 := m.z
		var b0 := int(arts.get("bounce", 0))
		w.player.jump()
		var top := {"z": m.z, "bounced": false}
		frames(int(3.0 / DT), Vector2.ZERO, false, func():
			if int(arts.get("bounce", 0)) > b0: top.bounced = true
			return bool(top.bounced))
		frames(int(2.0 / DT), row[4], false, func(): top.z = maxf(float(top.z), m.z); return m.grounded)
		frames(int(0.1 / DT))
		check(bool(top.bounced) and float(top.z) - z0 > m.apex() + 20.0 and m.grounded and absf(m.z - z0 - float(row[5]) * TopdownRoom.LEVEL) < 0.5,
			"%s: a landing on it bounces the body up (%.0f over its jump's %.0f), steered onto the floor %d level(s) up (z %.0f from %.0f)" % [row[2], float(top.z) - z0, m.apex(), int(row[5]), m.z, z0])

# ------------------------------------------------------------------ 17: the Entry Trials' lifts and planks, the quarry's crane
func _trials_and_crane() -> void:
	check(enter("sf_trial_jade", "entry"), "to the Jade Sect's Entry Trial on the grid")
	_lift("plank_1", Vector2(12, 9), Vector2.UP, 2.0)
	_lift("plank_2", Vector2(19, 7), Vector2.UP, 3.0)
	check(enter("sq_quarry_rim", "south"), "to the Quarry Rim on the grid")
	_lift("crane_lift", Vector2(16, 9), Vector2.UP, 2.0)
	# The Cloud Sect's trial: its plank walk over the cliff pool is the side view's crumbling ledge.
	check(enter("sf_trial_cloud", "entry"), "to the Cloud Sect's Entry Trial on the grid")
	var skim := _unskim()
	var m := motor()
	var tr := trav()
	var planks: Dictionary = tr.crumbles[0] if not tr.crumbles.is_empty() else {}
	stand(Vector2(15, 5))
	check(absf(m.z - 2.0 * TopdownRoom.LEVEL) < 0.5, "on the plank walk over the cliff pool, two levels up (z %.0f)" % m.z)
	var fell := {"sank": false}
	frames(int(3.0 / DT), Vector2.ZERO, false, func(): fell.sank = bool(fell.sank) or m.sink_t >= 0.0; return bool(fell.sank) and m.grounded and m.sink_t < 0.0)
	var cp := TopdownRoom.cell_of(m.pos)
	check(bool(fell.sank) and tr.crumble_state(planks) == "broken" and m.grounded and not Rect2(planks.rect).has_point(m.pos),
		"a second on the planks and they give way into the pool; the body is back on dry rock (%s, z %.0f)" % [str(cp), m.z])
	frames(int(5.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(planks) == "whole")
	check(tr.crumble_state(planks) == "whole", "the planks are back after their time")
	# Run across them from the ledge, a hop up onto the top ledge at the far end: they hold under a running foot.
	stand(Vector2(9, 5))
	var sank := {"any": false}
	_run_leg(TopdownRoom.cell_point([19, 5]), 3.0 * TopdownRoom.LEVEL, 3.0, func(): sank.any = bool(sank.any) or m.sink_t >= 0.0; return false)
	check(not bool(sank.any) and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5, "run across at a sprint, the planks hold, and a hop up reaches the bell's ledge (z %.0f)" % m.z)
	var bell: Dictionary = Game.room_rt.object_def("trial_bell")
	stand(TopdownRoom.cell_of(Vector2(float(bell.at[0]), float(bell.at[1]))) + Vector2i(-1, 0))
	var rung := Game.submit({"type": "interact", "object": "trial_bell"})
	GameEvents.flush()
	check(rung.get("ok", false) and c().quests.flags.get("trial_climbed", false), "the trial bell rung from its ledge on the grid (%s)" % str(rung.get("reason", "")))
	_reskim(skim)

## Ride lift `id` from its rest (`cell` on its deck, boarded as it rests there) up `levels`, and step off along `off`.
func _lift(id: String, cell: Vector2, off: Vector2, levels: float) -> void:
	var tr := trav()
	var m := motor()
	var lift := tr.raft(id)
	if lift.is_empty():
		check(false, "lift %s in %s" % [id, room()])
		return
	var base := float(lift.z)
	if str(lift.mover.mode) != "trigger": until(12.0, func(): return tr.deck_z(lift) <= base + 0.01 and tr.raft_offset(lift, tr.time + 0.4).length() < 0.01 and absf(_geo_z(tr, lift, tr.time + 0.4)) < 0.01)
	var seen := boarded.size()
	stand(cell)
	frames(2)
	check(m.ride == id and boarded.slice(seen).has(id), "%s: boarded on its rest in %s (%s)" % [id, room(), m.ride])
	until(8.0, func(): return tr.deck_z(lift) >= base + levels * TopdownRoom.LEVEL - 0.01)
	frames(2)
	var rode := m.z
	frames(int(0.5 / DT), off)
	check(absf(rode - base - levels * TopdownRoom.LEVEL) < 1.0 and m.grounded and m.ride == "" and absf(m.z - base - levels * TopdownRoom.LEVEL) < 1.0,
		"%s: it carries its rider %d levels up, who steps off onto the floor there (z %.0f)" % [id, int(levels), m.z])

## A deck's rise at the room's clock `t` (a lift's path's height).
func _geo_z(tr: TopdownTraverse, r: Dictionary, t: float) -> float:
	var saved := tr.time
	tr.time = t
	var z := tr.deck_z(r) - float(r.z)
	tr.time = saved
	return z

# ------------------------------------------------------------------ 18: the Tunnels' boards and spike pits
## The Mudwater Tunnels' two spike pits across the track, each under three rotten planks that are the track's floor: run
## over at a sprint they hold; stood on, one gives way and the body falls into the pit, where the side view's spikes strike
## it (the World authority's hazard volume, its numbers the side view's) and it is back on dry track; the plank comes back.
func _tunnels() -> void:
	check(enter("mh_tunnels", "west"), "to the Mudwater Tunnels on the grid")
	var tr := trav()
	var m := motor()
	check(tr.crumbles.size() == 6 and tr.hazards.size() == 2, "the Tunnels lay the side view's six rotten planks and its two spike pits (%d, %d)" % [tr.crumbles.size(), tr.hazards.size()])
	_whole()
	stand(Vector2(15, 13))
	var dry := {"ok": true}
	frames(int(2.0 / DT), Vector2.RIGHT, false, func(): dry.ok = bool(dry.ok) and m.sink_t < 0.0; return m.pos.x > 27.0 * TopdownRoom.TILE)
	check(bool(dry.ok) and m.grounded and absf(m.z) < 0.5 and m.pos.x > 26.0 * TopdownRoom.TILE, "a sprint along the track crosses the first pit's planks before they give way (x %.0f)" % (m.pos.x / TopdownRoom.TILE))
	var hp0: float = c().pools.hp
	var struck := {"n": 0}
	var hear := func(n: String, p: Dictionary): if n == "hazard_struck" and str(p.get("hazard", "")) == "spike_traps": struck.n = int(struck.n) + 1
	GameEvents.event.connect(hear)
	stand(Vector2(35.5, 13))
	var board: Dictionary = tr.crumble_at(m.pos)
	var fell := {"sank": false}
	frames(int(3.0 / DT), Vector2.ZERO, false, func(): fell.sank = bool(fell.sank) or m.sink_t >= 0.0; return bool(fell.sank) and m.grounded and m.sink_t < 0.0)
	GameEvents.flush()
	GameEvents.event.disconnect(hear)
	check(not board.is_empty() and bool(fell.sank) and int(struck.n) >= 1 and c().pools.hp < hp0 and c().pools.has_status("bleed"),
		"stood on, a plank gives way and the spikes strike the body in the pit (%d strikes, hp %.0f to %.0f, bleeding %s)" % [int(struck.n), hp0, c().pools.hp, str(c().pools.has_status("bleed"))])
	var cp := TopdownRoom.cell_of(m.pos)
	check(m.grounded and absf(m.z) < 0.5 and not Rect2(board.rect).has_point(m.pos) and Game.room_rt.topdown.standable(cp), "the body is back on dry track by the pit (%s)" % str(cp))
	frames(int(5.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(board) == "whole")
	check(tr.crumble_state(board) == "whole" and absf(m.floor_at(Rect2(board.rect).get_center())) < 0.5, "the plank is back after its time")
	_whole()

# ------------------------------------------------------------------ 19: the Drowned Shrine and the gorge
func _drowned_shrine() -> void:
	var skim := _unskim()
	var m := motor()
	# The Flooded Gate: a plank across the sunk gate, and the drain pulling a wading body west along the court.
	check(enter("ds_flooded_gate", "west"), "to the Flooded Gate on the grid")
	check(trav().rafts.size() == 3 and trav().currents.size() == 2, "the Flooded Gate floats the side view's three planks and runs its two currents")
	_ride("float_plank_0", Vector2(15, 19), Vector2.RIGHT, 1, Vector2.RIGHT, 0.04)
	stand(Vector2(40, 23))
	var x0 := m.pos.x
	frames(int(1.0 / DT))
	check(x0 - m.pos.x > 40.0 and x0 - m.pos.x < 80.0 and m.grounded, "the drain pulls a body standing in the court's south rows west (%.0f units a second)" % (x0 - m.pos.x))
	# The Hall of Lanterns: lantern_0 swings in under the gallery's edge and carries its rider out over the rubble.
	check(enter("ds_hall_of_lanterns", "west"), "to the Hall of Lanterns on the grid")
	var tr := trav()
	var lan := tr.raft("lantern_0")
	check(tr.rafts.size() == 5 and not lan.is_empty(), "the Hall of Lanterns hangs the side view's five lanterns")
	stand(Vector2(12, 1.5))
	var seen := boarded.size()
	until(4.0, func(): return m.ride == "lantern_0")
	var span := {"lo": INF, "hi": -INF, "level": true}
	frames(int(3.2 / DT), Vector2.ZERO, false, func():
		span.lo = minf(float(span.lo), m.pos.x)
		span.hi = maxf(float(span.hi), m.pos.x)
		span.level = bool(span.level) and m.ride == "lantern_0" and absf(m.z - TopdownRoom.LEVEL) < 0.5
		return false)
	check(boarded.slice(seen).has("lantern_0") and bool(span.level) and float(span.hi) - float(span.lo) > 50.0,
		"the lantern swings in under the gallery's edge and carries its rider along its arc over the rubble, a level up (%.0f units)" % (float(span.hi) - float(span.lo)))
	until(4.0, func(): return m.pos.x < 13.0 * TopdownRoom.TILE)
	frames(int(0.4 / DT), Vector2.LEFT)
	check(m.ride == "" and m.grounded and absf(m.z - TopdownRoom.LEVEL) < 0.5 and m.pos.x < 13.0 * TopdownRoom.TILE, "back off it onto the gallery")
	# The two floods: a boss's phase raises the river a level over the floor; the body is sent to dry floor (a rock, a
	# gallery), which stays dry; it falls again.
	_flood_room("dw_serpents_shallows", "shore", "serpent_flood", Vector2(40, 17), "field_boss_defeated")
	_flood_room("ds_abbots_sanctum", "west", "sanctum_flood", Vector2(20, 12), "")
	# The Rapids: the current hazard's areas on the grid's strand and white water, and the white water's pull.
	check(enter("wg_rapids_terraces", "west"), "to the Rapids Terraces on the grid")
	var areas := HazardRules.areas(ContentDB.entry("hazards", "current"), Game.room_rt.def)
	var on_grid: bool = areas.size() == 3 and areas.all(func(a): return Rect2(HazardRules.rect(a)).end.x <= Game.room_rt.topdown.w * TopdownRoom.TILE and Rect2(HazardRules.rect(a)).end.y <= Game.room_rt.topdown.h * TopdownRoom.TILE)
	var strand := Rect2(HazardRules.rect(areas[0])) if not areas.is_empty() else Rect2()
	var c0 := TopdownRoom.cell_of(strand.get_center())
	check(on_grid and Game.room_rt.topdown.standable(c0) and absf(Game.room_rt.topdown.floor_at(strand.get_center())) < 0.5,
		"the Rapids' current hazard has its areas on the grid: the strand's shallows and the white water (%s)" % str(areas.map(func(a): return a.rect)))
	check(trav().currents.size() == 1, "the white water's current on the grid")
	_reskim(skim)

## In flood room `rid`: a boss's phase raises the water a level over the floor in its rect, the body standing at `cell` is
## sent to the nearest dry floor and the raised floors in it stay dry; `ends` (or its hold) brings it back down.
func _flood_room(rid: String, way: String, id: String, cell: Vector2, ends: String) -> void:
	check(enter(rid, way), "to %s on the grid" % rid)
	var m := motor()
	var tr := trav()
	var f: Dictionary = {}
	for x in tr.floods:
		if str(x.id) == id: f = x
	if f.is_empty():
		check(false, "flood %s in %s" % [id, rid])
		return
	var raised := Vector2i(-1, -1)   # a floor a level up inside the flood's rect
	var r: Rect2 = f.rect
	for cy in range(int(r.position.y / TopdownRoom.TILE), int(r.end.y / TopdownRoom.TILE)):
		for cx in range(int(r.position.x / TopdownRoom.TILE), int(r.end.x / TopdownRoom.TILE)):
			if raised.x < 0 and Game.room_rt.topdown.level(cx, cy) == 1 and Game.room_rt.topdown.stair_at(cx, cy).is_empty(): raised = Vector2i(cx, cy)
	stand(cell)
	check(absf(m.z) < 0.5 and r.has_point(m.pos), "standing on the floor the flood lies over in %s" % rid)
	GameEvents.emit_event("boss_phase", {"boss": "t2", "action": "flood"})
	GameEvents.flush()
	var wet := {"sank": false}
	frames(int(6.0 / DT), Vector2.ZERO, false, func(): wet.sank = bool(wet.sank) or m.sink_t >= 0.0; return bool(wet.sank) and m.grounded and m.sink_t < 0.0)
	frames(int(4.0 / DT), Vector2.ZERO, false, func(): return tr.flood_k(f) >= 1.0)
	frames(int(2.0 / DT), Vector2.ZERO, false, func(): return m.grounded and m.sink_t < 0.0)   # the water risen over it again
	var put := m.z
	var cp := TopdownRoom.cell_of(m.pos)
	var dry_floor: float = m.floor_at(TopdownRoom.cell_point([raised.x, raised.y]))
	check(tr.flood_k(f) >= 1.0 and bool(wet.sank) and m.grounded and m.floor_at(m.pos) > TopdownRoom.WATER_Z and put <= TopdownRoom.LEVEL + 0.5
		and absf(dry_floor - TopdownRoom.LEVEL) < 0.5,
		"%s: the boss's phase floods the floor a level deep, the body is on dry floor within a level of it again (%s, z %.0f), the raised floor %s stays dry" % [id, str(cp), put, str(raised)])
	if ends != "":
		GameEvents.emit_event(ends, {"boss": "t2"})
		GameEvents.flush()
	frames(int(22.0 / DT), Vector2.ZERO, false, func(): return f.goal.is_empty())
	check(tr.flood_k(f) == 0.0 and absf(m.floor_at(TopdownRoom.cell_point([cell.x, cell.y]))) < 0.5, "%s: the water falls back%s" % [id, (" when " + ends) if ends != "" else " after its hold"])

# ------------------------------------------------------------------ 20: the Echo Cliffs' Wall-Step shaft
## Between Two Walls on the grid: in the shaft between the Echo Cliffs' two rock walls, a jump and three Wall-Step kicks
## (off each face in turn, pushed into) carry the body up to the vultures' nest at the shaft's head, three levels over
## its floor; the lesson's three kicks count.
func _echo_shaft() -> void:
	_realm("heart_tempering_4")
	check(enter("wg_echo_cliffs", "west"), "to the Echo Cliffs on the grid")
	if not Game.combat.knows_art(c(), "wall_step"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "wall_step"}], "test")
	c().quests.done.erase("between_two_walls")
	if not c().quests.is_active("between_two_walls"): submit({"type": "accept_quest", "quest": "between_two_walls"})
	GameEvents.flush()
	var m := motor()
	var floor0 := 3.0 * TopdownRoom.LEVEL
	stand(Vector2(30.6, 4.8))   # in the shaft's last row under the nest, nearer its west wall
	check(absf(m.z - floor0) < 0.5 and c().quests.is_active("between_two_walls"), "in the shaft between the two walls, Between Two Walls under way (z %.0f)" % m.z)
	var k0 := int(arts.get("wall_step", 0))
	frames(1, Vector2.LEFT)
	w.player.jump()
	# Each kick pushed into a face and a little north (the face is the push's main way), toward the nest.
	var sides := [Vector2(-1, -0.4).normalized(), Vector2(1, -0.4).normalized(), Vector2(-1, -0.4).normalized()]
	for i in 3:
		var side: Vector2 = sides[i]
		frames(int(0.6 / DT), side, false, func(): return _near_wall(Vector2(signf(side.x), 0.0)))
		w.player.jump()
		frames(1, side)
	var top := {"z": m.z}
	frames(int(2.0 / DT), Vector2.UP, false, func(): top.z = maxf(float(top.z), m.z); return m.grounded)
	frames(int(0.2 / DT))
	GameEvents.flush()
	var prog: Array = c().quests.active.get("between_two_walls", {}).get("progress", [0])
	check(int(arts.get("wall_step", 0)) - k0 == 3 and m.grounded and absf(m.z - 6.0 * TopdownRoom.LEVEL) < 0.5 and TopdownRoom.cell_of(m.pos).y <= 4,
		"three Wall-Step kicks up the shaft carry the body onto the nest at its head, three levels up (kicks %d, z %.0f, %s)" % [int(arts.get("wall_step", 0)) - k0, m.z, str(TopdownRoom.cell_of(m.pos))])
	check(int(prog[0]) >= 3, "Between Two Walls' three kicks counted on the grid (%s)" % str(prog))

## The body is within a Wall-Step's reach of the face along `side`.
func _near_wall(side: Vector2) -> bool:
	var m := motor()
	var probe := m.pos + side * (float(TopdownMotor.conf("traverse.wall_reach", 12.0)) + m.half.x - 2.0)
	return m.floor_at(probe) > m.z + m.mantle or Game.room_rt.topdown.level(TopdownRoom.cell_of(probe).x, TopdownRoom.cell_of(probe).y) == TopdownRoom.SOLID

# ------------------------------------------------------------------ 21: the peaks: crumbling floors, ice and wind
func _peaks() -> void:
	var m := motor()
	check(enter("sr_frozen_shrine", "east"), "to the Frozen Shrine on the grid")
	var tr := trav()
	check(tr.ices.size() == 2 and tr.crumbles.size() == 3, "the Frozen Shrine glazes its court and lays its three icicle shelves")
	# Ice: a sprint let go slides on across the court; on the terrace's plain floor it stops at once.
	var slide := []
	for cell in [Vector2(20, 8), Vector2(44, 11)]:
		stand(cell)
		frames(int(0.6 / DT), Vector2.RIGHT)
		var x1 := m.pos.x
		frames(int(1.2 / DT))
		slide.append(m.pos.x - x1)
	check(float(slide[0]) > 40.0 and float(slide[1]) < 12.0, "on the court's ice a sprint let go slides on (%.0f units), on the plain terrace it stops (%.0f)" % [slide[0], slide[1]])
	# An icicle shelf off the court's west side: it holds a moment, cracks, and drops the body a level onto the terrace.
	var ice: Dictionary = tr.crumbles[0]
	stand(Vector2(13, 6))
	var z0 := m.z
	frames(int(2.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(ice) == "broken" and m.grounded)
	frames(int(0.3 / DT))
	check(absf(z0 - 3.0 * TopdownRoom.LEVEL) < 0.5 and absf(m.z - 2.0 * TopdownRoom.LEVEL) < 0.5 and m.sink_t < 0.0, "an icicle shelf cracks under a foot and drops it a level onto the terrace (z %.0f to %.0f)" % [z0, m.z])
	# The monastery's rotten floors: the west wing's raised floor gives way a level onto the terrace under it.
	check(enter("mp_forgotten_monastery", "east"), "to the Forgotten Monastery on the grid")
	tr = trav()
	var wf: Dictionary = tr.crumbles[0]
	stand(Vector2(21, 7))
	z0 = m.z
	frames(int(2.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(wf) == "broken" and m.grounded)
	frames(int(0.3 / DT))
	check(absf(z0 - 4.0 * TopdownRoom.LEVEL) < 0.5 and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5 and m.grounded,
		"the west wing's rotten floor gives way and drops the body a level (z %.0f to %.0f)" % [z0, m.z])
	stand(Vector2(21, 12))
	frames(int(5.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(wf) == "whole")
	check(tr.crumble_state(wf) == "whole" and absf(m.floor_at(TopdownRoom.cell_point([21, 7])) - 4.0 * TopdownRoom.LEVEL) < 0.5, "the floor is back after its time")
	# The Windswept Ridge: its wind pushes a body standing on the trail west while it blows strong.
	check(enter("sr_windswept_ridge", "east"), "to the Windswept Ridge on the grid")
	tr = trav()
	var wv: Dictionary = tr.winds[0] if not tr.winds.is_empty() else {}
	stand(Vector2(40, 16))
	until(5.0, func(): return not wv.is_empty() and fposmod(tr.time + float(wv.phase), float(wv.cycle)) < 0.05)
	stand(Vector2(40, 16))
	var x0 := m.pos.x
	frames(int(1.0 / DT))
	var blown := x0 - m.pos.x
	check(blown > 50.0 and blown < 140.0 and m.grounded, "the ridge's wind pushes a body standing on the trail west while it blows strong (%.0f units a second)" % blown)

# ------------------------------------------------------------------ 22: Breath Control's swim
## In the Drowned Grotto: without Breath Control the pool's bank stops a walking body (T1's rule); with it the body walks
## in and swims at the swim's pace, its chest above the water, hauls out on the far bank, and sinks only when its breath
## is out (thirty seconds), back on its last safe spot.
func _swim() -> void:
	var skim := _unskim()
	var had: bool = c().cultivator.secret_arts.has("breath_control")
	c().cultivator.secret_arts.erase("breath_control")
	check(enter("ds_drowned_grotto", "entry"), "to the Drowned Grotto on the grid")
	var m := motor()
	stand(Vector2(9, 12))
	frames(int(0.8 / DT), Vector2.DOWN)
	check(not m.swimming and m.sink_t < 0.0 and TopdownRoom.cell_of(m.pos).y <= 12, "without Breath Control the pool's bank stops a walking body")
	Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "breath_control"}], "test")
	check(Game.combat.knows_art(c(), "breath_control"), "Breath Control learned")
	stand(Vector2(9, 12))
	frames(int(0.8 / DT), Vector2.DOWN, false, func(): return m.swimming)
	frames(int(0.3 / DT), Vector2.DOWN)
	check(m.swimming and m.sink_t < 0.0 and absf(m.z - TopdownRoom.WATER_Z) < 0.5, "with it the body walks into the pool and swims (z %.0f)" % m.z)
	var x0 := m.pos.x
	frames(int(0.5 / DT), Vector2.RIGHT)
	var pace := (m.pos.x - x0) / 0.5
	check(m.swimming and pace > 0.45 * m.sprint and pace < 0.75 * m.sprint, "it swims at the swim's pace (%.0f units a second, the sprint's %.0f)" % [pace, m.sprint])
	w.player.sync(DT)
	check(w.player.anim in ["walk", "idle"], "the swimmer strokes in the walk's own frames, cut at the water's line (%s)" % w.player.anim)
	frames(int(1.5 / DT), Vector2.UP, false, func(): return not m.swimming)
	frames(int(0.2 / DT), Vector2.UP)
	check(not m.swimming and m.grounded and m.z > -0.5 and m.sink_t < 0.0, "it hauls out onto the bank (z %.0f)" % m.z)
	stand(Vector2(9, 12))
	frames(int(1.0 / DT), Vector2.DOWN, false, func(): return m.swimming)
	var t0 := tr_time()
	var sank := {"at": -1.0}
	frames(int(34.0 / DT), Vector2.ZERO, false, func():
		if m.sink_t >= 0.0 and float(sank.at) < 0.0: sank.at = tr_time()
		return float(sank.at) >= 0.0 and m.grounded and m.sink_t < 0.0)
	check(float(sank.at) - t0 > 28.0 and float(sank.at) - t0 < 31.5 and m.grounded and not m.swimming and m.z > -0.5,
		"its breath lasts the side view's thirty seconds, then it sinks and is back on the bank (%.1f s)" % (float(sank.at) - t0))
	if not had: c().cultivator.secret_arts.erase("breath_control")
	_reskim(skim)

func tr_time() -> float:
	return trav().time if trav() != null else Game.room_rt.geometry.time

# ------------------------------------------------------------------ 23: the shallows' slow
## The Drowned Shrine's flagstones under shallow water (the tile set's `flood`) are waded at the side view's 0.7 of the
## pace; a Water Sphere's frozen ground walks them at full pace.
func _shallows() -> void:
	check(enter("ds_flooded_gate", "west"), "to the Flooded Gate's court on the grid")
	var m := motor()
	var run := func(cell: Vector2) -> float:
		stand(cell)
		frames(int(0.3 / DT), Vector2.RIGHT)
		var x0 := m.pos.x
		frames(int(0.5 / DT), Vector2.RIGHT)
		return (m.pos.x - x0) / 0.5
	var dry: float = run.call(Vector2(4, 9))
	var wade: float = run.call(Vector2(36, 15))
	w.player.state.frozen_ground = true
	var frozen: float = run.call(Vector2(36, 15))
	w.player.state.frozen_ground = false
	check(absf(wade / dry - 0.7) < 0.05 and absf(frozen / dry - 1.0) < 0.05,
		"wading the flooded court goes at %.2f of the dry walk's pace (the side view's 0.7), frozen ground at %.2f" % [wade / dry, frozen / dry])

# ------------------------------------------------------------------ 24: the rooftop chases
## The rooftop thief on the grid, at Gate Street and the Stoneford market: his run is the layout's route over the roofs,
## every waypoint on a floor at its height. Then the chase played: spoken to, he runs; the body runs his route after him
## roof to roof (each leg a walk, a drop, a hop a level up or a running jump over a gap) and catches him at a pause.
func _chases() -> void:
	for row in [["ja_gate_street", "thief_ja"], ["sf_market", "thief_sf"]]:
		var rid := str(row[0])
		var oid := str(row[1])
		check(enter(rid, ""), "to %s on the grid" % rid)
		var o: Dictionary = Game.room_rt.object_def(oid)
		var route: Array = o.chase.route
		var grid: TopdownRoom = Game.room_rt.topdown
		var bad := []
		var high := 0.0
		for i in route.size():
			var q := Vector2(float(route[i][0]), float(route[i][1]))
			high = maxf(high, float(route[i][2]))
			if not grid.standable(TopdownRoom.cell_of(q)) or absf(grid.floor_at(q) - float(route[i][2])) > 0.5: bad.append(i)
		check(bad.is_empty() and high >= TopdownRoom.LEVEL, "%s's run is over the grid's roofs (up to %d levels), every waypoint on a floor at its height (%s)" % [oid, int(high / TopdownRoom.LEVEL), str(bad)])
		# Played: he runs once spoken to; the body runs his route after him, roof to roof (a hop up where the next floor is
		# a level up, a running jump where a gap lies before a floor no lower), and catches him at a pause, at his height.
		c().cooldowns.erase("chase_" + oid)
		var caught := {"yes": false, "s": 0.0}
		var hear := func(n: String, p: Dictionary):
			if n == "thief_caught" and str(p.get("object", "")) == oid:
				caught.yes = true
				caught.s = float(p.get("seconds", 0.0))
		GameEvents.event.connect(hear)
		stand(TopdownRoom.cell_of(Vector2(float(route[0][0]), float(route[0][1]))) + Vector2i(0, 1))
		var started := Game.submit({"type": "interact", "object": oid})
		GameEvents.flush()
		var legs := 0
		for i in range(1, route.size()):
			if bool(caught.yes): break
			if _run_leg(Vector2(float(route[i][0]), float(route[i][1])), float(route[i][2]), 4.0, func(): return bool(caught.yes)): legs += 1
		GameEvents.flush()
		GameEvents.event.disconnect(hear)
		check(started.get("ok", false) and bool(caught.yes) and not Game.world.chases.has(c().id),
			"%s: the chase played on the grid, the thief caught over the roofs at his height after %.1f s (%d legs run; %s)" % [oid, float(caught.s), legs, str(started.get("reason", ""))])

## Run the body to `target` on the floor at `tz` (at most `secs`): the stick toward it, a hop where the floor ahead is a
## level up, a running jump where a gap or a drop lies ahead and the target is no lower. True when it arrived (or `stop`).
func _run_leg(target: Vector2, tz: float, secs: float, stop: Callable) -> bool:
	var m := motor()
	for i in int(secs / DT):
		if stop.call(): return true
		var to := target - m.pos
		if to.length() < 12.0 and absf(m.z - tz) < 4.0 and m.grounded: return true
		var axis := to.normalized()
		if m.grounded:
			var fa := m.floor_at(m.pos + axis * 22.0)
			if (fa > m.z + m.step_up and fa <= m.z + TopdownRoom.LEVEL + m.mantle) or (fa < m.z - m.step_up and tz >= m.z - m.step_up): w.player.jump()
		frames(1, axis)
	return false

# ================================================================== T3: Act II onward, and T2's leftovers (topdown_mechanics.md)
## The Plunge art known and ready (a test shortcut: the Outer Trial teaches it).
func _plunge_ready() -> void:
	if not Game.combat.knows_art(c(), "plunge"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "plunge"}], "test")
	c().pools.cooldowns.erase("plunge")

# ------------------------------------------------------------------ 25: the Lower Pit's cracked slab
## The side view's cracked slab on the Lower Pit's floor (Act I's last mechanic): a level over the floor, the spirit stone
## shards sealed under it (hidden, the context offers nothing); walked into, it stops the body at its foot; a hop lands on
## it and it holds; a Plunge from over it breaks it and falls on through to strike on the floor under it (the side view's
## rule 10), and the shards show and are taken. It is whole again on the next visit, as the side view's.
func _cracked_slab() -> void:
	check(enter("sq_lower_pit", "west"), "to the Lower Pit on the grid")
	var m := motor()
	var tr := trav()
	check(tr != null and tr.cracks.size() == 1, "the Lower Pit lays the side view's cracked slab")
	var slab: Dictionary = tr.cracks[0]
	var r: Rect2 = slab.rect
	var shard: Dictionary = Game.room_rt.object_def("pit_shard")
	var at := Vector2(float(shard.at[0]), float(shard.at[1]))
	c().quests.flags.erase("pit_shard")
	_whole()
	check(not bool(slab.broken) and tr.sealed(at) and not Game.world.object_visible(c(), shard) and absf(float(slab.z) - TopdownRoom.LEVEL) < 0.5,
		"the shards lie sealed under the whole slab, a level over the pit's floor, and do not show")
	var west := TopdownRoom.cell_of(r.position) - Vector2i(2, 0)
	stand(Vector2(west.x, west.y))
	frames(int(0.6 / DT), Vector2.RIGHT)
	check(m.grounded and absf(m.z) < 0.5 and m.pos.x < r.position.x, "walked into, the slab stops the body at its foot (x %.0f, its edge %.0f)" % [m.pos.x, r.position.x])
	stand(Vector2(west.x, west.y))
	w.player.jump()
	frames(int(1.2 / DT), Vector2.RIGHT, false, func(): return m.grounded and m.z > 1.0)
	frames(2)
	check(m.grounded and absf(m.z - float(slab.z)) < 0.5 and not bool(slab.broken) and r.has_point(m.pos), "a hop lands on the slab, and a plain landing holds it (z %.0f)" % m.z)
	_plunge_ready()
	var hits := int(systems.get("plunge_strike", 0))
	w.player.jump()
	frames(int(0.12 / DT))
	var pr: Dictionary = w.player.plunge()
	var through := {"cracked": false}
	frames(int(1.0 / DT), Vector2.ZERO, false, func():
		through.cracked = bool(through.cracked) or motor_events.any(func(e): return str(e.type) == "cracked")
		return m.grounded)
	frames(int(0.2 / DT))
	GameEvents.flush()
	check(pr.get("ok", false) and bool(slab.broken) and bool(through.cracked) and m.grounded and absf(m.z) < 0.5 and int(systems.get("plunge_strike", 0)) > hits,
		"a Plunge from over it breaks the slab and falls on through, striking on the floor under it (%s; z %.0f, strikes %d)" % [str(pr), m.z, int(systems.get("plunge_strike", 0)) - hits])
	check(not tr.sealed(at) and Game.world.object_visible(c(), shard), "the shards show where the slab was")
	stand(TopdownRoom.cell_of(at) + Vector2i(0, 1))
	var before: int = c().inventory.count("spirit_stone_shard")
	var took := Game.submit({"type": "interact", "object": "pit_shard"})
	GameEvents.flush()
	check(took.get("ok", false) and c().inventory.count("spirit_stone_shard") == before + 3, "and the three spirit stone shards are taken (%s)" % str(took))
	check(enter("sq_lower_pit", "west") and not bool(trav().cracks[0].broken), "on the next visit the slab is whole again (the side view's break lasts the visit)")

# ------------------------------------------------------------------ 26: Rimefrost's ice
## Frostpine Climb's and Rimefrost Summit's ice (R6's rooms, the side view's ice volumes and their traction): a sprint
## let go on it slides on, off it the body stops at once.
func _rimefrost_ice() -> void:
	var m := motor()
	for row in [["rf_frostpine_climb", "west", "frostpine_ice", Vector2(47, 6), Vector2(36, 6)],
			["rf_rimefrost_summit", "west", "summit_ice", Vector2(16, 19), Vector2(36, 19)]]:
		check(enter(str(row[0]), str(row[1])), "to %s on the grid" % row[0])
		var tr := trav()
		var side_t := 0.0
		for v in ContentDB.room(str(row[0])).get("volumes", []):
			if str(v.get("id", "")) == str(row[2]): side_t = float(v.get("traction", 0.0))
		check(tr != null and tr.ices.size() == 1 and str(tr.ices[0].id) == str(row[2]) and absf(float(tr.ices[0].traction) - side_t * 0.755) < 0.5,
			"%s lays the side view's ice, its traction the side view's (%.0f)" % [row[0], side_t])
		var slide := []
		for cell in [row[3], row[4]]:
			stand(cell)
			frames(int(0.6 / DT), Vector2.RIGHT)
			var x1 := m.pos.x
			frames(int(1.2 / DT))
			slide.append(m.pos.x - x1)
		check(float(slide[0]) > 40.0 and float(slide[1]) < 12.0, "%s: on its ice a sprint let go slides on (%.0f units), off it the body stops (%.0f)" % [row[0], slide[0], slide[1]])

# ------------------------------------------------------------------ 27: no-flight
## Wherever the side view forbids flight the grid does too, with its feedback: in a room that forbids it (the
## Windbridge), an interior and a dungeon the hold glides instead; a side-view no_flight volume's cells (a `no_flight`
## row, laid here on the Falls Pool's shore: no room's side view has one yet) end a flight flown into them, as Combat's
## tick ends the side view's (flight_ended "no_flight", the body comes down), and the hold glides there.
func _no_flight() -> void:
	_realm("cloud_stride_1")
	if not Game.combat.knows_art(c(), "glide"): Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "falling_leaf_glide"}], "test")
	if not Unlocks.is_unlocked(c().id, "flight"): Unlocks.force_unlock(c().id, "flight")
	var m := motor()
	# R9's no-flight rooms beside them: the Inverted Hall, the Leviathan's Maw and the Starsea's crossing.
	for rid in ["gc_windbridge", "lf_old_ma_store", "mh_tunnels", "or_inverted_hall", "nd_leviathans_maw", "ss_starsea_crossing"]:
		check(enter(rid), "to %s on the grid" % rid)
		_whole()
		w.player.jump()
		var glid := {"on": false}
		frames(int(0.6 / DT), Vector2.ZERO, true, func(): glid.on = bool(glid.on) or st.gliding; return false)
		frames(int(2.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
		check(not Game.combat.flight_allowed(c().id) and not m.flying and bool(glid.on), "%s (%s): flight is refused, the hold glides" % [rid, ContentDB.room(rid).get("type", "")])
	check(_falls_pool(), "to the Falls Pool to fly into a no-flight volume")
	var tr := trav()
	var area := Rect2(46.0 * 32.0, 17.0 * 32.0, 6.0 * 32.0, 9.0 * 32.0)
	tr.no_flights.append({"id": "t3_no_flight", "kind": "no_flight", "rect": area})
	_whole()
	stand(Vector2(40, 22))
	w.player.jump()
	frames(int(0.9 / DT), Vector2.ZERO, true)
	var flew := m.flying and Game.combat.is_flying(c().id)
	var ends := flight_ends.size()
	frames(int(3.0 / DT), Vector2.RIGHT, false, func(): return not m.flying)
	GameEvents.flush()
	var inside := area.has_point(m.pos)
	frames(int(3.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	check(flew and not m.flying and not Game.combat.is_flying(c().id) and inside and flight_ends.slice(ends).has("no_flight") and m.grounded,
		"flown into a no-flight volume, the flight ends there (%s) and the body comes down (z %.0f)" % [str(flight_ends.slice(ends)), m.z])
	_whole()
	stand(Vector2(48, 22))
	w.player.jump()
	var glid2 := {"on": false}
	frames(int(0.6 / DT), Vector2.ZERO, true, func(): glid2.on = bool(glid2.on) or st.gliding; return false)
	frames(int(2.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	check(not m.flying and bool(glid2.on), "inside it the hold glides instead")
	tr.no_flights.clear()
	_whole()

# ------------------------------------------------------------------ 28: low gravity and its switches
## The Orbit Ruins' low gravity (the side view's low_gravity volumes, live while their jade switch holds them): a row laid
## on the Falls Pool's shore (the Ruins' rooms are R9's), off until its switch is turned through the World authority
## (toggle_gravity, the switch's own call), then a standing jump climbs to the side view's 1/0.45 of its height and hangs
## longer; turned again, gravity is back.
func _low_gravity() -> void:
	check(_falls_pool(), "to the Falls Pool for a low-gravity floor")
	var skim := _unskim()
	var m := motor()
	var tr := trav()
	var area := Rect2(44.0 * 32.0, 12.0 * 32.0, 7.0 * 32.0, 3.0 * 32.0)
	tr.lowgs.append({"id": "t3_lowg", "kind": "low_gravity", "rect": area, "gravity": 0.45, "switch": "t3_switch", "invert": false, "off": true})
	var g: Dictionary = tr.lowgs.back()
	var jump := func() -> Array:
		stand(Vector2(47.5, 13.0))
		var top := {"z": m.z, "t": 0}
		w.player.jump()
		top.t = frames(int(3.0 / DT), Vector2.ZERO, false, func(): top.z = maxf(float(top.z), m.z); return m.grounded and m.z < 0.5)
		return [float(top.z), float(top.t) * DT]
	var off: Array = jump.call()
	var r1 := Game.world.toggle_gravity(c(), "t3_switch")
	GameEvents.flush()
	check(r1.get("ok", false) and not bool(g.off) and absf(tr.gravity_at(area.get_center()) - 0.45) < 0.001 and int(systems.get("gravity_switch", 0)) >= 1,
		"the jade switch turned, the floor's low gravity is live (%s)" % str(r1))
	var on: Array = jump.call()
	check(absf(float(off[0]) - m.apex()) < 3.0 and absf(float(on[0]) - m.apex() / 0.45) < 6.0 and float(on[1]) > float(off[1]) * 1.4,
		"there a standing jump climbs %.0f units to the light air's %.0f (the side view's 1/0.45), and hangs %.2f s for %.2f s" % [off[0], on[0], on[1], off[1]])
	Game.world.toggle_gravity(c(), "t3_switch")
	GameEvents.flush()
	var back: Array = jump.call()
	check(bool(g.off) and absf(float(back[0]) - m.apex()) < 3.0, "turned again, gravity is back (%.0f)" % back[0])
	tr.lowgs.erase(g)
	Game.room_rt.objects.erase("t3_switch")
	_reskim(skim)

# ------------------------------------------------------------------ 29: the Starsea docks
## The Starsea's four docks on the grid (the Shipwrights' Yard's, R6's; the Broken Pier's, the Launch's and the Arrival
## Quay's, R8's): a top-down character with a vessel and the route's chart at Sage 3 sets sail with the dock's own call
## (the context's interact). The voyage plays on the grid: the crossing's event for the vessel's time, its foes come
## aboard onto the deck's floors, and the port is made at the far pier. All four routes are sailed.
func _starsea() -> void:
	Unlocks.force_unlock(c().id, "starsea")
	for k in ["cloud_skiff", "star_chart_wreck", "star_chart_lantern"]:
		if c().inventory.count(k) == 0: Game.inventory.apply_add(c().id, k, 1, "test")
	# The yard's chart table and slipway (the voyage's preparations, R8's "played on pages"): the side view's own pages,
	# opened by their objects on the grid.
	check(enter("ae_shipyard"), "to the Shipwrights' Yard on the grid")
	for u in ["star_charting", "shipwright"]:
		if not Unlocks.is_unlocked(c().id, u): Unlocks.force_unlock(c().id, u)   # a test shortcut: Sage 3's systems
	for row in [["chart_table_cloudgate", "charts"], ["slip_cloudgate", "vessels"]]:
		var o: Dictionary = Game.room_rt.object_def(str(row[0]))
		var oat := Vector2(float(o.at[0]), float(o.at[1]))
		var sp := Game.room_rt.topdown.spot_near(oat, float(o.get("alt", 0.0)), oat)
		stand(Vector2(sp.x / TopdownRoom.TILE - 0.5, sp.y / TopdownRoom.TILE - 0.5))
		var pr := Game.submit({"type": "interact", "object": str(row[0])})
		check(pr.get("ok", false) and str(pr.get("open_page", "")) == str(row[1]), "the yard's %s opens its page (%s) from the grid" % [row[0], str(pr)])
	var foes_seen := false
	var rows: Array = [["ae_shipyard", "dock_cloudgate"], ["sw_broken_pier", "dock_wreck"], ["sw_starsea_launch", "dock_launch"], ["lh_arrival_quay", "dock_lantern"]]
	for row in rows:
		var rid := str(row[0])
		check(enter(rid), "to %s's Starsea dock on the grid" % rid)
		var dock: Dictionary = Game.room_rt.object_def(str(row[1]))
		var v := ContentDB.entry("voyages", str(dock.get("route", "")))
		var at := Vector2(float(dock.at[0]), float(dock.at[1]))
		var grid: TopdownRoom = Game.room_rt.topdown
		var spot := grid.spot_near(at, float(dock.get("alt", 0.0)), at)
		stand(Vector2(spot.x / TopdownRoom.TILE - 0.5, spot.y / TopdownRoom.TILE - 0.5))
		var r := Game.submit({"type": "interact", "object": str(row[1])})
		GameEvents.flush()
		st = w.player.state
		_sync()
		var secs := float(v.base_s) / float(ContentDB.item(Game.world.best_vessel(c())).get("vessel", {}).get("speed", 1.0))
		check(r.get("ok", false) and room() == str(v.crossing) and Game.room_rt.topdown != null and Game.room_rt.event.get("active", false)
			and absf(float(Game.room_rt.event.remaining) - secs) < 1.0,
			"%s: the skiff sets sail, the crossing's deck on the grid, its event under way for the voyage's %d s (%s)" % [v.id, int(secs), str(r)])
		if not foes_seen:
			var deck: TopdownRoom = Game.room_rt.topdown
			var seen := {}
			frames(int(24.0 / DT), Vector2.ZERO, false, func():
				_whole()
				for e in Game.room_rt.living_enemies(): if e.summoned: seen[e.uid] = e.plane
				return seen.size() >= 2)
			var off := seen.values().filter(func(p): return not deck.standable(TopdownRoom.cell_of(p)))
			check(seen.size() >= 2 and off.is_empty(), "%s: its foes come aboard onto the deck's floors (%d, %d off)" % [v.id, seen.size(), off.size()])
			foes_seen = true
		Game.room_rt.event.remaining = 0.01
		frames(3)
		GameEvents.flush()
		st = w.player.state
		_sync()
		check(room() == str(v.to) and Game.room_rt.topdown != null and not Game.world.voyages.has(c().id), "%s: the crossing makes port at %s on the grid" % [v.id, v.to])
		_whole()

# ------------------------------------------------------------------ 30: the light of the late zones
## R7's and R8's rooms lit as their side view is: the tomb's halls and the Clan Hearth's cavern lamp-lit whatever the
## hour; the Lantern Star Field's rooms (and the star field's past it) starlit at noon; Lanternfall's star lanterns burn.
func _late_light() -> void:
	for row in [["ts_sealed_gate", "lamplit"], ["ir_clan_hearth", "lamplit"], ["lh_arrival_quay", "night_story"], ["sw_broken_pier", "night_story"],
			["wn_nest_cliffs", "night_story"], ["ir_hold_gate", "day"]]:
		var def: Dictionary = ContentDB.room(str(row[0]))
		check(str(TopdownLight.look(def, 0.375).hour) == str(row[1]), "%s at noon: %s (%s)" % [row[0], row[1], TopdownLight.look(def, 0.375).hour])
	check(enter("lh_arrival_quay"), "to the Arrival Quay on the grid")
	var lanterns: int = Game.room_rt.topdown.props.filter(func(p): return str(p.kind) == "star_lantern").size()
	var lit: int = w.atmosphere.lights.filter(func(l): return str(l[0]) == "star").size()
	check(lanterns > 0 and lit == lanterns, "the quay's %d star lanterns each give their starlight (%d)" % [lanterns, lit])

# ------------------------------------------------------------------ 31: the shoals' wade and the cove's crack
## R8's two played by shortcut: the Jellyfish Shallows' wading floors slow the walk as the side view's shallows do
## (T2's rule); Spirit Sense's pulse at the Gunners' Battery shows the crack into the Smugglers' Cove on the grid.
func _sky_sea_leftovers() -> void:
	check(enter("dr_jellyfish_shallows", "west"), "to the Jellyfish Shallows on the grid")
	var m := motor()
	var run := func(cell: Vector2) -> float:
		stand(cell)
		frames(int(0.3 / DT), Vector2.RIGHT)
		var x0 := m.pos.x
		frames(int(0.5 / DT), Vector2.RIGHT)
		return (m.pos.x - x0) / 0.5
	var dry: float = run.call(Vector2(51, 12))
	var wade: float = run.call(Vector2(36, 12))
	check(absf(wade / dry - 0.7) < 0.05, "wading the shallows goes at %.2f of the dry walk's pace (the side view's 0.7)" % (wade / dry))
	check(enter("bm_gunners_battery", "west"), "to the Gunners' Battery on the grid")
	for u in ["spirit_sense", "hidden_portals"]:
		if not Unlocks.is_unlocked(c().id, u): Unlocks.force_unlock(c().id, u)
	var flag := WorldPortals.seen_flag("bm_gunners_battery", "cove")
	c().quests.flags.erase(flag)
	var cove: Dictionary = Game.room_rt.portal_def("cove")
	check(Game.world.portal_state(c(), cove).get("hidden", false), "the crack into the cove is hidden until sensed")
	stand(Vector2(43, 5))   # where the crack sets a body down, at the cliff's foot
	c().pools.soul = maxf(c().pools.soul, 50.0)
	c().pools.cooldowns.erase("sense")
	var r := Game.submit({"type": "sense_pulse"})
	GameEvents.flush()
	check(r.get("ok", false) and c().quests.has_flag(flag) and not Game.world.portal_state(c(), cove).get("hidden", false),
		"Spirit Sense's pulse on the grid shows it (%s)" % str(r))

# ------------------------------------------------------------------ 32: the swim's stroke
## T2's swimmer is the walk cut at the water's line; its stroke now has a rhythm: a pull every `swim_stroke_s` while it
## moves (the walk's frames run once through, its pace surging), then a glide on the walk's rest frame, and each pull
## leaves a ring on the water.
func _swim_stroke() -> void:
	var skim := _unskim()   # a skimmer would run on the water; Breath Control is learned again below
	Game.apply_effects(c().id, [{"kind": "learn_secret_art", "art": "breath_control"}], "test")
	check(enter("ds_drowned_grotto", "entry"), "to the Drowned Grotto to swim")
	var m := motor()
	stand(Vector2(9, 12))
	frames(int(1.0 / DT), Vector2.DOWN, false, func(): return m.swimming)
	var pull := {}
	var glide := {}
	var rest := TopdownFigure.rest_frame("walk")
	frames(int(0.3 / DT), Vector2.DOWN)   # out into the pool's middle
	motor_events.clear()
	var look := func():
		w.player.sync(DT)
		if w.player.anim == "walk":
			var k := m.stroke_t / m.swim_stroke
			if k < 0.5: pull[w.player.frame] = true
			elif k > 0.6: glide[w.player.frame] = true
		return false
	for way in [Vector2.RIGHT, Vector2.LEFT, Vector2.RIGHT, Vector2.LEFT]: frames(int(0.5 / DT), way, false, look)   # to and fro across it
	var strokes := motor_events.filter(func(e): return str(e.type) == "stroked").size()
	var wakes: int = w.fx.items.filter(func(it): return str(it.kind) == "wake").size()
	for e in motor_events: w.feedback(e)
	wakes = w.fx.items.filter(func(it): return str(it.kind) == "wake").size() - wakes
	check(m.swimming and strokes >= 2 and strokes <= 3 and wakes == strokes, "two seconds' swim is %d strokes, each leaving its wake (%d)" % [strokes, wakes])
	check(pull.size() >= 3 and glide.keys() == [rest], "the pull runs the walk's frames (%s), the glide holds its rest frame (%s)" % [str(pull.keys()), str(glide.keys())])
	c().cultivator.secret_arts.erase("breath_control")
	_reskim(skim)

# ------------------------------------------------------------------ 33: a bounce that gives
## The Fairground's drum, as it launches a body: its skin pressed in, then springing back, then at rest (BounceView).
func _bounce_gives() -> void:
	check(enter("sf_fairground", "west"), "to the Fairground's drum")
	var m := motor()
	var view = null
	for n in w.sorted.get_children():
		if n is TopdownTraverseView.BounceView and str(n.b.id) == "fair_drum_bounce": view = n
	stand(Vector2(36, 10))
	var b0 := int(arts.get("bounce", 0))
	w.player.jump()
	var seen := []
	frames(int(3.0 / DT), Vector2.ZERO, false, func():
		if view != null and (seen.is_empty() or seen.back() != view.frame_now()): seen.append(view.frame_now())
		return int(arts.get("bounce", 0)) > b0 and seen.back() == 0 and seen.size() > 1)
	frames(int(2.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	check(view != null and seen == [0, 1, 2, 0], "the drum's skin gives as it launches the body: at rest, pressed, springing back, at rest (%s)" % str(seen))

# ------------------------------------------------------------------ 34: lanterns that go round upright
## The Hall of Lanterns' circling lanterns go round upright as the side view's do: east-west along the plane and up and
## down a radius's twice (their deck rising and falling), never along the plane north and south; a body standing on
## the lid rides it up.
func _upright_lanterns() -> void:
	check(enter("ds_hall_of_lanterns", "west"), "to the Hall of Lanterns")
	var tr := trav()
	var m := motor()
	var l: Dictionary = tr.raft("lantern_1")
	var r2 := 2.0 * float(l.mover.radius)
	var ys := {}
	var lo := INF
	var hi := -INF
	var t0 := tr.time
	for i in 44:
		var t := t0 + float(i) * 0.1
		var keep := tr.time
		tr.time = t
		ys[roundf(tr.raft_rect(l).position.y)] = true
		lo = minf(lo, tr.deck_z(l))
		hi = maxf(hi, tr.deck_z(l))
		tr.time = keep
	check(ys.size() == 1 and absf(lo - float(l.z)) < 1.0 and absf(hi - float(l.z) - r2) < 2.0,
		"lantern_1 goes round upright: one row on the plane, its deck from %.0f up to %.0f (its round %.0f)" % [lo, hi, r2])
	until(6.0, func(): return tr.deck_z(l) < float(l.z) + 1.0)
	m.z = 200.0
	stand(Vector2(16.5, 1.5))
	var z0 := m.z
	var top := {"z": m.z}
	frames(int(2.3 / DT), Vector2.ZERO, false, func(): top.z = maxf(float(top.z), m.z); return false)
	check(absf(z0 - float(l.z)) < 1.0 and float(top.z) - z0 > r2 - 6.0 and m.ride == "lantern_1", "a body on its lid rides it up and round (z %.0f up to %.0f)" % [z0, top.z])

# ------------------------------------------------------------------ 35: returning boards
## The monastery's rotten floor: gone under a body, it does not come back over the body still standing under it (it would
## lift the body onto it); once the body has stepped out from under it, it comes back.
func _returning_boards() -> void:
	check(enter("mp_forgotten_monastery", "east"), "to the Forgotten Monastery's rotten floor")
	var tr := trav()
	var m := motor()
	var wf: Dictionary = tr.crumbles[0]
	stand(Vector2(21, 7))
	frames(int(2.5 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(wf) == "broken" and m.grounded)
	frames(int(0.3 / DT))
	var dropped := m.z
	frames(int((float(wf.return_s) + 1.5) / DT))
	check(absf(dropped - 3.0 * TopdownRoom.LEVEL) < 0.5 and tr.crumble_state(wf) == "broken" and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5,
		"past their time the boards stay gone over the body under them, not lifting it (z %.0f, %s)" % [m.z, tr.crumble_state(wf)])
	frames(int(1.5 / DT), Vector2.LEFT, false, func(): return not Rect2(wf.rect).has_point(m.pos))   # west, onto the terrace (the flight is south)
	frames(int(0.6 / DT))
	check(tr.crumble_state(wf) == "whole" and absf(m.z - 3.0 * TopdownRoom.LEVEL) < 0.5, "stepped out from under them, the boards come back (%s; the body at %s, z %.0f)" % [tr.crumble_state(wf), str(TopdownRoom.cell_of(m.pos)), m.z])

# ------------------------------------------------------------------ 36: the pits open beside their planks
## The Tunnels' spike pits open beside their planks, as the side view's pit lies round its planks: a body standing on the
## spikes beside the track is struck; on the whole planks over the pit it is not.
func _open_spikes() -> void:
	check(enter("mh_tunnels", "west"), "to the Tunnels' spike pits")
	var tr := trav()
	var m := motor()
	var pit: Dictionary = tr.hazards[0]
	var open := 0
	var r: Rect2 = pit.rect
	for y in range(int(r.position.y / 32.0), int(r.end.y / 32.0)):
		for x in range(int(r.position.x / 32.0), int(r.end.x / 32.0)):
			if not tr.spikes_at((Vector2(x, y) + Vector2(0.5, 0.5)) * 32.0).is_empty(): open += 1
	check(open == 12, "each pit lies open a row either side of its planks (%d open cells)" % open)
	_whole()
	Game.combat.cure_status(c().id, "spawn_protection")
	var n0 := int(struck.get("spike_traps", 0))
	stand(Vector2(21, 13))
	frames(int(1.0 / DT), Vector2.ZERO, false, func(): return tr.crumble_state(tr.crumble_at(m.pos)) != "whole")
	var on_planks := int(struck.get("spike_traps", 0)) - n0
	stand(Vector2(22, 11))
	frames(int(0.5 / DT))
	GameEvents.flush()
	var on_spikes := int(struck.get("spike_traps", 0)) - n0 - on_planks
	check(on_planks == 0 and on_spikes >= 1 and m.grounded, "on the planks the body is clear; on the spikes beside them it is struck (%d, %d)" % [on_planks, on_spikes])
	_whole()

# ------------------------------------------------------------------ 37: the wind's edge on the diagonals
## The Windswept Ridge's wind pushes harder within `wind_edge` of a drop along any of the eight ways round the body (T2
## looked along the four axes only): at a spot whose only drop near it is on a diagonal, the push is its edge factor's.
func _wind_diagonals() -> void:
	check(enter("sr_windswept_ridge", "east"), "to the Windswept Ridge's wind")
	var tr := trav()
	var m := motor()
	var wv: Dictionary = tr.winds[0]
	var grid: TopdownRoom = Game.room_rt.topdown
	var edge := m.wind_edge
	var diag := Vector2.INF
	var flat := Vector2.INF
	var r: Rect2 = wv.rect
	for y in range(int(r.position.y / 32.0), int(r.end.y / 32.0)):
		for x in range(int(r.position.x / 32.0), int(r.end.x / 32.0)):
			var p := (Vector2(x, y) + Vector2(0.5, 0.5)) * 32.0
			if not grid.standable(Vector2i(x, y)) or not grid.stair_at(x, y).is_empty(): continue
			var z := grid.height_at(p)
			var drops := []
			for d in TopdownMotor.WIND_AXES: drops.append(grid.height_at(p + (d as Vector2) * edge) < z - m.step_up)
			var axis := drops.slice(0, 4).has(true)
			var diagonal := drops.slice(4).has(true)
			if diagonal and not axis and diag == Vector2.INF: diag = Vector2(x, y)
			if not diagonal and not axis and flat == Vector2.INF: flat = Vector2(x, y)
	check(diag != Vector2.INF and flat != Vector2.INF, "the ridge has a spot whose only near drop is diagonal (%s) and one with none (%s)" % [str(diag), str(flat)])
	if diag == Vector2.INF or flat == Vector2.INF: return
	stand(flat)
	var plain := m.wind_push().length() / maxf(0.001, tr.wind_strength(wv))
	stand(diag)
	var near := m.wind_push().length() / maxf(0.001, tr.wind_strength(wv))
	check(absf(plain - (wv.push as Vector2).length()) < 0.5 and absf(near - plain * float(wv.edge_factor)) < 0.5,
		"by a drop on the diagonal the wind pushes %.0f, its edge factor's %.1f times the open ridge's %.0f" % [near, float(wv.edge_factor), plain])

# ------------------------------------------------------------------ 38: a flier over the crowns
## T1's leftover: a flier high over its floor is drawn over the crowns and roofs south of it within its height (its sort
## key carried that far south), never behind a tree it flies above.
func _flier_over_crowns() -> void:
	_realm("cloud_stride_1")
	if not Unlocks.is_unlocked(c().id, "flight"): Unlocks.force_unlock(c().id, "flight")
	check(_falls_pool(), "to the Falls Pool to fly over the trees")
	var m := motor()
	var grid: TopdownRoom = Game.room_rt.topdown
	_whole()
	stand(Vector2(40, 22))
	w.player.jump()
	frames(int(1.6 / DT), Vector2.ZERO, true)
	w.player.sync(DT)
	var above := m.z - grid.height_at(m.pos)
	var lift: float = w.player.position.y - grid.sort_key(m.pos, m.z)
	check(m.flying and above >= 96.0 and absf(lift - above / TopdownRoom.ART) < 0.1,
		"flying %.0f units up, the body is drawn %.1f art px further south than its feet (over the crowns below it)" % [above, lift])
	w.player.fly_down = true
	frames(int(4.0 / DT), Vector2.ZERO, false, func(): return m.grounded)
	w.player.fly_down = false
	frames(2)
	w.player.sync(DT)
	check(m.grounded and absf(w.player.position.y - grid.sort_key(m.pos, m.z)) < 0.01, "landed, it is keyed at its feet again")

# ------------------------------------------------------------------ 39: the star field's end (R9's rooms)
## R9's rooms on the grid: the Orbit Ruins' four low-gravity rows, each the side view's volume under its own jade
## switch; in the Inverted Hall the east switch turned with its own interact, so a standing jump at the high gallery's
## foot climbs onto it, which it cannot in the heavy air; the Nebula Leviathan (a flier, as in the side view) crosses its
## lagoon's water to a body on an islet; and the star field's light: starlit at noon, the Wardens' lamps and caged stars
## lit, the islands' brinks over the void, the nebula's and the Starsea's water star-water, the crossing's streaks.
func _star_field() -> void:
	for row in [["or_tumbling_stair", "west", ["lowg_stair"]], ["or_orbit_garden", "west", ["lowg_garden"]],
			["or_inverted_hall", "entry", ["lowg_hall_a", "lowg_hall_b"]]]:
		check(enter(str(row[0]), str(row[1])), "to %s on the grid" % row[0])
		var tr := trav()
		var ids: Array = tr.lowgs.map(func(g): return str(g.id))
		var sw: Array = tr.lowgs.map(func(g): return str(g.switch))
		var objs: Array = sw.filter(func(s): return not Game.room_rt.object_def(s).is_empty())
		check(ids == row[2] and tr.lowgs.all(func(g): return bool(g.off) and absf(float(g.gravity) - 0.45) < 0.001) and objs.size() == sw.size(),
			"%s: its low-gravity rows %s, each off under its own jade switch (%s)" % [row[0], str(ids), str(sw)])
		if str(row[0]) == "or_tumbling_stair":
			check(w.life.vista.void_sky and w.life.vista.edges.any(func(e): return str(e.kind) == "cloud_sea"),
				"the Tumbling Stair's brink falls into the starry void (its cloud_sea edge, in a void area)")
	# The Inverted Hall: the high gallery three levels up the back wall (31-41, 1-4), its stair at 35-37. At its foot
	# west of the stair a standing jump pressed north falls back in the heavy air and climbs onto it in the light.
	var m := motor()
	var tr2 := trav()
	var leap := func() -> float:
		_whole()
		stand(Vector2(32, 5))
		w.player.jump()
		frames(int(1.8 / DT), Vector2.UP, false, func(): return m.grounded and m.vz <= 0.0 and m.z > 1.0)
		frames(int(0.3 / DT))
		return m.z
	var heavy: float = leap.call()
	var o: Dictionary = Game.room_rt.object_def("switch_hall_b")
	var oat := Vector2(float(o.at[0]), float(o.at[1]))
	var sp := Game.room_rt.topdown.spot_near(oat, float(o.get("alt", 0.0)), oat)
	stand(Vector2(sp.x / TopdownRoom.TILE - 0.5, sp.y / TopdownRoom.TILE - 0.5))
	var n0 := int(systems.get("gravity_switch", 0))
	var r := Game.submit({"type": "interact", "object": "switch_hall_b"})
	GameEvents.flush()
	check(r.get("ok", false) and absf(tr2.gravity_at(Vector2(32.5, 5.5) * TopdownRoom.TILE) - 0.45) < 0.001 and int(systems.get("gravity_switch", 0)) == n0 + 1,
		"the Inverted Hall's east switch turned from the grid with its own interact: the air over the hall's east half is light (%s)" % str(r))
	var light: float = leap.call()
	check(heavy < TopdownRoom.LEVEL * 3.0 - 0.5 and absf(light - TopdownRoom.LEVEL * 3.0) < 0.5,
		"a standing jump at the high gallery's foot falls back in the heavy air (z %.0f) and climbs onto it in the light (z %.0f)" % [heavy, light])
	stand(Vector2(sp.x / TopdownRoom.TILE - 0.5, sp.y / TopdownRoom.TILE - 0.5))
	Game.submit({"type": "interact", "object": "switch_hall_b"})
	GameEvents.flush()
	check(absf(tr2.gravity_at(Vector2(32.5, 5.5) * TopdownRoom.TILE) - 1.0) < 0.001, "turned back, the air is heavy again")
	# The Leviathan's Maw: the Leviathan (the side view's flier) goes straight over its lagoon's water.
	if not Unlocks.is_unlocked(c().id, "field_bosses"): Unlocks.force_unlock(c().id, "field_bosses")   # a test shortcut
	check(enter("nd_leviathans_maw", "west"), "to the Leviathan's Maw on the grid")
	var grid: TopdownRoom = Game.room_rt.topdown
	var boss: EnemyState = null
	frames(int(10.0 / DT), Vector2.ZERO, false, func(): return Game.room_rt.living_enemies().any(func(e): return e.def_id == "nebula_leviathan"))
	for e in Game.room_rt.living_enemies(): if e.def_id == "nebula_leviathan": boss = e
	check(boss != null, "the Nebula Leviathan is in its lagoon")
	if boss != null:
		# It turns on the body standing on the shoal; then, set over the lagoon (a test shortcut, as `stand` is) with the
		# body veiled from it, it gives up and flies home to the shoal straight over the water, frame by frame.
		Game.combat.cure_status(c().id, "spawn_protection")   # the room's welcome, which no foe sees through
		stand(Vector2(44, 12))
		frames(int(1.0 / DT), Vector2.ZERO, false, func():
			_whole()
			c().pools.invulnerable = 5.0   # a test shortcut: its blows are not what is watched
			return str(boss.ai.state) != "idle")
		var fought := str(boss.ai.state) != "idle"
		stand(Vector2(8, 13))   # back along the causeway, out of its reach
		Game.combat.apply_status(c().id, "veiled", 30.0, 1.0)
		boss.plane = Vector2(47.5, 22.5) * TopdownRoom.TILE   # over the lagoon south of the shoal
		var trail := {"wet": 0, "step": 0.0, "last": boss.plane}
		var home := frames(int(10.0 / DT), Vector2.ZERO, false, func():
			_whole()
			var bc := TopdownRoom.cell_of(boss.plane)
			if grid.inside(bc.x, bc.y) and grid.is_water(bc.x, bc.y): trail.wet = int(trail.wet) + 1
			trail.step = maxf(float(trail.step), boss.plane.distance_to(trail.last))
			trail.last = boss.plane
			return boss.plane.distance_to(boss.spawn_point) < 12.0)
		c().pools.invulnerable = 0.0
		Game.combat.cure_status(c().id, "veiled")
		check(fought and int(trail.wet) * DT > 1.0 and float(trail.step) < 4.0 and boss.plane.distance_to(boss.spawn_point) < 12.0,
			"the Leviathan (a flier, as in the side view) flies over its lagoon's water to its shoal: %.1f s over the water, %.1f s in all, never more than %.1f units a frame" % [int(trail.wet) * DT, home * DT, trail.step])
	# The star field's light and water.
	for row in [["wc_citadel_gate", "night_story", true], ["or_tumbling_stair", "night_story", true], ["ar_war_camp", "night_story", true],
			["nd_nebula_verge", "night_story", true], ["ss_starsea_crossing", "night_story", true], ["lt_wick_gate", "lamplit", false]]:
		var def: Dictionary = ContentDB.room(str(row[0]))
		check(str(TopdownLight.look(def, 0.375).hour) == str(row[1]) and bool(TopdownLight.area_of(def).get("void", false)) == bool(row[2]),
			"%s at noon: %s (%s), %s" % [row[0], row[1], TopdownLight.look(def, 0.375).hour, "past the star field's edge" if row[2] else "lamp-lit inside"])
	check(enter("wc_citadel_gate"), "to the Citadel Gate on the grid")
	var lamps: int = Game.room_rt.topdown.props.filter(func(p): return str(p.kind) in ["warden_lamp", "lantern_cage"]).size()
	var lit: int = w.atmosphere.lights.filter(func(l): return str(l[0]) == "star").size()
	check(lamps > 0 and lit == lamps, "the Citadel Gate's %d Warden lamps and caged stars each give their starlight (%d)" % [lamps, lit])
	var star_water := func() -> Array:
		var out := [null, null]
		for n in w.sorted.get_children():
			if n.is_queued_for_deletion(): continue   # the last room's, let go at the frame's end
			if n is TopdownTraverseView.StarWaterView: out[0] = n
			if n is TopdownTraverseView.VoyageView: out[1] = n
		return out
	check(enter("nd_nebula_verge"), "to the Nebula Verge on the grid")
	var nv: Array = star_water.call()
	check(nv[0] != null and not nv[0].runs.is_empty() and nv[0].stars.size() > 10 and nv[1] == null,
		"the nebula's water is star-water: its wash over %d runs, %d stars in it" % [nv[0].runs.size() if nv[0] else 0, nv[0].stars.size() if nv[0] else 0])
	check(enter("ss_starsea_crossing"), "to the Starsea crossing's deck on the grid")
	var sv: Array = star_water.call()
	check(sv[0] != null and sv[1] != null and not sv[1].streaks.is_empty() and w.life.vista.void_sky,
		"the crossing's water streams past the hull (%d streaks) and is star-water, the Starsea glinting all round" % [sv[1].streaks.size() if sv[1] else 0])
	check(_falls_pool(), "back to the Falls Pool")
	check(star_water.call()[0] == null and not w.life.vista.void_sky, "the Falls Pool's water is the river's own")
