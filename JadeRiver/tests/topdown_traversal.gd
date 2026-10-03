extends "res://tests/prologue_run.gd"
## topdown_traversal (T1, docs/architecture/topdown_mechanics.md): the side view's traversal and set pieces, played on the
## height grid by a top-down character through the real view (a live TopdownWorld: its player's motor stepped frame by
## frame as the world steps it, then Game.tick), each mechanic in the converted room that needs it:
##   1. set pieces: every room event a set piece starts in a room with a layout sets its foes on the grid's open floors,
##      reached on foot from the player, inside the room (the summit's by its stage, the rest by their mapped points),
##      however the room is sized; so do a rift and a treasure birth, made from where things stand on the grid;
##   2. rafts: the Grey Pools' log raft boarded from the jetty carries its rider across the grey pool to the west bank
##      (mover_boarded), the loop raft round the east pool and back, the hermit's raft across his pond; never a splash;
##   3. Leaf on the Wind, the lesson played on the grid: the vine climbed to the spray ledge (no blow while on it), a
##      glide from the ledge over the falls' spray to the lotus rock, and back up on the spray's updraft to the ledge a
##      jump cannot reach; the two glides count, and Elder Hu takes it;
##   4. the rope up the falls ledge's east face and back down; a sealed climbable stays shut;
##   5. Skipping Stones: Water Skimming across the hermit's pond counts, the mist lotus picked, the hermit takes it;
##   6. Swallow Dart and the Cloud Ladder Step in the Falls Pool: three darts along the stick holding the height, three
##      second jumps, each lesson's objectives done on the grid (their librarian waits in the library, past the gate);
##   7. Wall-Step off the cliff's face and a bounce off a drum laid on the grid, each its art_used.
## Run headless:  godot --headless --path . res://tests/topdown_traversal.tscn [-- --verbose]

const BEFORE := ["prologue", "main"]
const PLAYED := ["leaf_on_the_wind", "swallow_dart", "cloud_ladder", "skipping_stones", "between_two_walls"]
const DT := 1.0 / 60.0

var w: TopdownWorld = null
var arts: Dictionary = {}     # art -> times art_used was heard
var boarded: Array = []       # movers boarded
var climbs: Array = []        # [event, climbable, end]

func _main() -> void:
	create_extra = {"view": "topdown"}
	start_new("traverse/")
	GameEvents.event.connect(_heard)
	_shortcut()
	_world()
	for part in [_set_pieces, _rafts, _leaf_on_the_wind, _rope, _skipping_stones, _dart_and_ladder, _wall_and_bounce]:
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
		p.physics_step(DT)
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
## point it waits at, 0 for its rest: a loop comes back), then step off walking `off` (default `on`).
func _ride(id: String, from: Vector2, on: Vector2, end: int, off := Vector2.ZERO) -> void:
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
	frames(int(0.25 / DT), on)   # well onto the deck
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
		"%s: carried its rider %d units to the end of its run, standing on the deck, no splash" % [id, int(start.distance_to(m.pos))])
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
	# The art as Between Two Walls teaches it (a test shortcut: that lesson is the Echo Cliffs', past the gate).
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
