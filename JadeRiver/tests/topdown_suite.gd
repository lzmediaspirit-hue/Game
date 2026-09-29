extends RefCounted
## topdown_suite (redesign Phase 1, docs/redesign_top_down_plan.md "As built: Phase 1"): the height-grid room and the
## TopdownMotor's rules on small rooms made for each case, then the prototype room's view: depth-sort order, the
## silhouette, pixel snapping and the camera. rules_tests runs it (`topdown_suite`); the frame budget is perf_tests'
## `_topdown`. `measured` collects the numbers the plan records.

const Tileset := "res://data/topdown/proto_tileset.json"
var t          # the running suite (check, near)
var measured := {}

func grid(rows: Array, extra := {}) -> TopdownRoom:
	var d := {"id": "case", "levels": rows, "spawn": [1, 1]}
	d.merge(extra)
	return TopdownRoom.from_dict(d, JSON.parse_string(FileAccess.get_file_as_string(Tileset)))

## Run the motor `secs` at 60 fps with the stick at `axis`; Jump (or Dash) is pressed on the frames listed.
func run(m: TopdownMotor, secs: float, axis: Vector2, jumps := [], dashes := []) -> Array:
	var ev: Array = []
	for f in roundi(secs * 60.0):
		m.step(1.0 / 60.0, axis, f in jumps, f in dashes)
		ev.append_array(m.drain())
	return ev

func types(ev: Array) -> Array:
	return ev.map(func(e): return str(e.type))

func flat(w := 20, h := 12) -> Array:
	var rows: Array = []
	for y in h: rows.append("0".repeat(w))
	return rows

func run_all(suite) -> void:
	t = suite
	_walk()
	_sprint_carry()
	_jump_levels()
	_falls_and_windows()
	_collision()
	_water_and_gaps()
	_dash()
	_sort_keys()
	_facing()
	_water_skill()
	_roofs()
	_aim_rules()
	_terrain_rules()
	_terrain_v2()
	_square_layout()
	_drag_zones()
	_motor_plunge()
	_finisher_pace()
	_light_rules()
	_view_rules()
	_route_rooms()
	_route_cases()

func _walk() -> void:
	# Decision 42: the stick pushed sprints (the run the sheets draw); a light touch walks at the world's measured pace.
	var m := TopdownMotor.new(grid(flat()), Vector2(80, 192))
	var x0 := m.pos.x
	var to_full := 0.0
	while m.vel.length() < m.sprint - 0.01 and to_full < 1.0:
		m.step(1.0 / 120.0, Vector2.RIGHT)
		to_full += 1.0 / 120.0
	run(m, 1.0, Vector2.RIGHT)
	var speed := m.vel.length()
	var x1 := m.pos.x
	var sprinting := m.running
	var stop_t := 0.0
	while m.vel.length() > 0.0 and stop_t < 1.0:
		m.step(1.0 / 120.0, Vector2.ZERO)
		stop_t += 1.0 / 120.0
	measured.sprint = speed
	measured.accel_s = to_full
	measured.stop_s = stop_t
	measured.stop_units = m.pos.x - x1
	t.check(t.near(speed, 216.0) and sprinting and m.running and to_full <= 0.08 + 1.0 / 120.0 and stop_t <= 0.06 + 1.0 / 120.0 and m.pos.x - x1 < 8.0 and x1 > x0,
		"topdown: the stick pushed sprints %.1f u/s (6.75 tiles/s), full speed in %.3f s, stops in %.3f s over %.1f units" % [speed, to_full, stop_t, m.pos.x - x1])
	var d := TopdownMotor.new(grid(flat()), Vector2(80, 80))
	run(d, 0.5, Vector2(1, 1).normalized())
	var tip := TopdownMotor.new(grid(flat()), Vector2(80, 80))
	run(tip, 0.5, Vector2(0.5, 0))
	measured.tiptoe = tip.vel.length()
	t.check(t.near(d.vel.length(), 216.0) and absf(d.vel.x - d.vel.y) < 0.01 and t.near(tip.vel.length(), 154.0 * 0.45) and not tip.running,
		"topdown: 8-way analog: the diagonal sprints at full speed (%.1f), a light touch (0.5) walks slowly at 45%% of the world's measured walk (%.1f)" % [d.vel.length(), tip.vel.length()])

## Decision 42: the sprint reaches no further in the air than the walk the world was measured at: a running jump and a
## step off a ledge carry the same from a sprint as from a walk, and the dash's long jump keeps its own carry.
func _sprint_carry() -> void:
	# The reference is the walk the world was measured at: the same motor with its push held to the walk.
	var reach := {}
	var top := {}
	var drop := {}
	for kind in ["sprint", "walk"]:
		var r := TopdownMotor.new(grid(flat(30)), Vector2(64, 192))
		if kind == "walk": r.sprint = r.walk
		run(r, 0.4, Vector2.RIGHT)
		var from := r.pos.x
		r.step(1.0 / 60.0, Vector2.RIGHT, true)
		var fastest := 0.0
		while not r.grounded:
			r.step(1.0 / 120.0, Vector2.RIGHT)
			fastest = maxf(fastest, r.vel.length())
		reach[kind] = r.pos.x - from
		top[kind] = fastest
		var o := TopdownMotor.new(_ledge_room(), Vector2(320, 120))
		if kind == "walk": o.sprint = o.walk
		var edge := 0.0
		while o.grounded and o.pos.y < 400.0:
			o.step(1.0 / 120.0, Vector2.DOWN)
			edge = o.pos.y
		while not o.grounded: o.step(1.0 / 120.0, Vector2.DOWN)
		drop[kind] = o.pos.y - edge
	measured.sprint_jump_reach = reach.sprint
	measured.sprint_drop = drop.sprint
	t.check(absf(float(reach.sprint) - float(reach.walk)) < 1.5 and float(top.sprint) <= 154.01 and reach.sprint > 64.0 and reach.sprint < 80.0
		and absf(float(drop.sprint) - float(drop.walk)) < 1.0,
		"topdown: a sprint's running jump carries %.1f units (the measured walk's %.1f), no faster than 154 in the air, and a sprint off a ledge lands %.1f past it (the walk %.1f)"
			% [reach.sprint, reach.walk, drop.sprint, drop.walk])

## Decision 42: auto-path's and auto-hunt's steering (TopdownRoute) in every room with a layout. From where a character
## wakes, a tour of the room: every way out in turn (auto-path's own goals) and about four of its people and things (as
## auto-hunt goes anywhere a foe or a drop is), each leg from where the last ended, the motor stepped as the game steps
## it with the stick fully pushed (so it sprints) and Jump pressed where the way hops a level up. The foot box never
## touches a solid prop (a trunk, a rock, a fence, a hedge, crates, a lantern, a building's wall), every leg the grid's
## own way reaches arrives, no leg stalls against a corner or turns back and forth, and it runs at the sprint.
func _route_rooms() -> void:
	var rooms: Array = []
	for f in DirAccess.get_files_at("res://data/topdown/"):
		if not str(f).ends_with(".json"): continue
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://data/topdown/" + f))
		if d is Dictionary and d.has("levels"): rooms.append(str(f).get_basename())
	rooms.sort()
	var tally := {"legs": 0, "arrived": 0, "unreached": 0, "touches": [], "lost": [], "stalls": [], "flips": [], "walls": 0, "top": 0.0, "frames": 0}
	for rid in rooms:
		var room := TopdownRoom.load_room(rid)
		var goals: Array = []   # [label, point, near]
		for pid in room.def.get("portals", {}):
			goals.append([str(pid), TopdownRoom.cell_point(room.def.portals[pid].at), 14.0])
		var places: Array = room.def.get("place", {}).keys()
		places.sort()
		for i in range(0, places.size(), maxi(1, ceili(places.size() / 4.0))):
			goals.append([str(places[i]), TopdownRoom.cell_point(room.def.place[places[i]]), 10.0])
		var m := TopdownMotor.new(room)
		var route := TopdownRoute.new(room)
		for g in goals:
			var target: Vector2 = g[1]
			if float(g[2]) == 10.0: target = room.spot_near(target, room.floor_at(target), m.pos)
			var from := TopdownRoom.cell_of(m.pos)
			var to := TopdownRoom.cell_of(room.nearest_standable(target))
			if from != to and TopdownRoute.find(room, from, to, true).is_empty():
				# A spot only a running jump reaches (auto-path never takes one); a way out must be reached by the grid's own
				# path search whenever TopdownRoom.find_path reaches it.
				if float(g[2]) == 14.0 and not room.find_path(from, to, true, 100000).is_empty(): tally.lost.append("%s: %s (no way)" % [rid, g[0]])
				tally.unreached += 1
				continue
			tally.legs += 1
			_route_leg(room, m, route, target, float(g[2]), "%s: %s" % [rid, g[0]], tally)
	measured.route = {"rooms": rooms.size(), "legs": tally.legs, "arrived": tally.arrived, "top_speed": snappedf(tally.top, 0.1),
		"wall_frames": tally.walls, "seconds": snappedf(tally.frames / 60.0, 0.1)}
	t.check(rooms.size() >= 25 and tally.legs >= 150 and tally.arrived == tally.legs and (tally.lost as Array).is_empty(),
		"topdown route: auto-path's steering arrives on every leg the grid's way reaches in all %d rooms with a layout (%d of %d legs; %d spots only a running jump reaches; lost %s)"
			% [rooms.size(), tally.arrived, tally.legs, tally.unreached, str((tally.lost as Array).slice(0, 4))])
	t.check((tally.touches as Array).is_empty(),
		"topdown route: its foot box never touches a solid prop, a trunk, rock, fence, hedge, crates, lantern or a building's wall, over %.0f s of legs (%d touches: %s)"
			% [tally.frames / 60.0, (tally.touches as Array).size(), str((tally.touches as Array).slice(0, 4))])
	t.check((tally.stalls as Array).is_empty() and (tally.flips as Array).is_empty() and t.near(float(tally.top), 216.0, 0.5),
		"topdown route: it sprints (%.1f u/s at the most), never stalls against a corner (%s) nor turns back and forth (%s)"
			% [tally.top, str((tally.stalls as Array).slice(0, 4)), str((tally.flips as Array).slice(0, 4))])

## Decision 42: two cases auto-hunt meets. A drop lying in a trunk's footprint is gone for by the nearest spot a body
## stands at, where the body stops (the old steering pushed on into the trunk for good); a body knocked against a trunk,
## off its way, takes the way up again round the trunk without touching it.
func _route_cases() -> void:
	var r := grid(flat(), {"props": [{"kind": "tree_pine", "x": 8, "y": 5}, {"kind": "rock_mossy", "x": 10, "y": 6}]})
	var cases := [["a drop in the trunk's cell", Vector2(3.5, 5.5), Vector2(8.5, 5.5), 24.0], ["knocked against the trunk", Vector2(7.5, 5.5), Vector2(14.5, 5.5), 10.0]]
	var out := []
	for k in cases:
		var m := TopdownMotor.new(r, (k[1] as Vector2) * 32.0)
		if str(k[0]).begins_with("knocked"): m.pos.x = 8.0 * 32.0 - m.half.x - 2.0   # two units off the trunk's west face
		var route := TopdownRoute.new(r)
		var touched := false
		var still := 0
		var tt := 0.0
		while tt < 4.0:
			var axis := route.steer(m.pos, m.z, m.grounded, (k[2] as Vector2) * 32.0, float(k[3]))
			if axis == Vector2.INF or axis == Vector2.ZERO:
				still += 1
				if still > 10: break
				axis = Vector2.ZERO
			for sub in 2:
				m.step(1.0 / 120.0, axis)
				touched = touched or not _prop_touched(r, m).is_empty()
			tt += 1.0 / 60.0
		out.append([k[0], touched, still > 10, snappedf(m.pos.distance_to(r.nearest_standable((k[2] as Vector2) * 32.0)) if str(k[0]).begins_with("a drop") else m.pos.distance_to((k[2] as Vector2) * 32.0), 0.1)])
	t.check(out.all(func(o): return not o[1] and o[2] and float(o[3]) <= 24.0),
		"topdown route: a drop in a trunk's cell is gone for by the spot beside it, where the body stops; a body knocked against a trunk goes round it to its way; neither touches the trunk (%s)" % str(out))

## One leg of the route tour: the motor steered to `target` until it is within `near`, at most the way's length at the
## walk plus six seconds; the touches, stalls and flips it makes go into `tally`.
func _route_leg(room: TopdownRoom, m: TopdownMotor, route: TopdownRoute, target: Vector2, near: float, label: String, tally: Dictionary) -> void:
	var limit := m.pos.distance_to(target) / 150.0 + 8.0
	var tt := 0.0
	var hop := 0.0
	var last := Vector2.ZERO
	var stuck := 0.0
	var flips := 0
	var touched := false
	var stalled := false
	while tt < limit:
		var axis := route.steer(m.pos, m.z, m.grounded and m.sink_t < 0.0, target, near)
		if axis == Vector2.INF:
			tally.arrived += 1
			if flips > 2: tally.flips.append("%s (%d)" % [label, flips])
			return
		var jump := route.jump and hop <= 0.0 and m.grounded
		if jump: hop = 0.5
		if m.grounded and last != Vector2.ZERO and axis != Vector2.ZERO and last.dot(axis) < -0.5: flips += 1
		last = axis
		var was := m.pos
		for sub in 2:
			m.step(1.0 / 120.0, axis, jump and sub == 0)
			var hit := _prop_touched(room, m)
			if not hit.is_empty() and not touched:
				touched = true
				tally.touches.append("%s at %s by %s" % [label, str(hit.cell), hit.kind])
			if m.grounded and _wall_grazed(room, m): tally.walls += 1
		m.drain()
		if m.sink_t >= 0.0:
			tally.lost.append(label + " (in the water)")
			while m.sink_t >= 0.0: m.step(1.0 / 60.0, Vector2.ZERO)
			return
		if m.grounded: tally.top = maxf(float(tally.top), m.vel.length())
		# A stall: pushed on the ground yet hardly moving for a tenth of a second (held against something).
		stuck = stuck + 1.0 / 60.0 if m.grounded and not jump and axis.length() > 0.5 and m.pos.distance_to(was) < 0.5 else 0.0
		if stuck >= 0.1 and not stalled:
			stalled = true
			tally.stalls.append("%s at %s" % [label, str(TopdownRoom.cell_of(m.pos))])
		hop -= 1.0 / 60.0
		tt += 1.0 / 60.0
		tally.frames += 1
	tally.lost.append(label)
	if flips > 2: tally.flips.append("%s (%d)" % [label, flips])

## The solid prop the foot box (grown by a unit) touches at the body's height: {kind, cell}, or {} when none.
func _prop_touched(room: TopdownRoom, m: TopdownMotor) -> Dictionary:
	var g := m.half + Vector2(1, 1)
	for corner in [m.pos - g, Vector2(m.pos.x + g.x, m.pos.y - g.y), Vector2(m.pos.x - g.x, m.pos.y + g.y), m.pos + g]:
		var cp := TopdownRoom.cell_of(corner)
		if not room.inside(cp.x, cp.y) or room.solid[cp.y * room.w + cp.x] != 1: continue
		if float(room.level(cp.x, cp.y)) * TopdownRoom.LEVEL <= m.z + 8.0: continue   # a roof or crates' top it stands on
		for pr in room.props:
			if Rect2i(pr.cell, pr.size).has_point(cp): return {"kind": str(pr.kind), "cell": cp}
	return {}

## The foot box (grown by a unit) against a wall of the terrain (a floor higher than a step), not a prop.
func _wall_grazed(room: TopdownRoom, m: TopdownMotor) -> bool:
	var g := m.half + Vector2(1, 1)
	for corner in [m.pos - g, Vector2(m.pos.x + g.x, m.pos.y - g.y), Vector2(m.pos.x - g.x, m.pos.y + g.y), m.pos + g]:
		var cp := TopdownRoom.cell_of(corner)
		if room.inside(cp.x, cp.y) and room.solid[cp.y * room.w + cp.x] == 0 and room.height_at(corner) > m.z + 8.0 and room.height_at(corner) < INF: return true
	return false

func _jump_levels() -> void:
	var m := TopdownMotor.new(grid(flat()), Vector2(200, 192))
	var ev := run(m, 1.0 / 60.0, Vector2.ZERO, [0])
	var top := 0.0
	var air := 0.0
	while not m.grounded and air < 2.0:
		m.step(1.0 / 120.0, Vector2.ZERO)
		top = maxf(top, m.z)
		air += 1.0 / 120.0
	air += 1.0 / 60.0
	measured.apex = top
	measured.airtime = air
	t.check("jumped" in types(ev) and absf(top - 47.06) < 1.0 and absf(air - 0.47) < 0.03 and t.near(m.apex(), 47.06) and t.near(m.airtime(), 0.4706),
		"topdown: a jump rises %.1f (1.5 levels) and lands after %.3f s" % [top, air])
	# Running, a flat jump carries 2.2 tiles.
	var r := TopdownMotor.new(grid(flat(30)), Vector2(64, 192))
	run(r, 0.4, Vector2.RIGHT)
	var from := r.pos.x
	run(r, 0.6, Vector2.RIGHT, [0])
	var reach := 0.0
	var probe := TopdownMotor.new(grid(flat(30)), Vector2(64, 192))
	run(probe, 0.4, Vector2.RIGHT)
	probe.step(1.0 / 60.0, Vector2.RIGHT, true)
	while not probe.grounded: probe.step(1.0 / 120.0, Vector2.RIGHT)
	reach = probe.pos.x - from
	measured.jump_reach = reach
	t.check(reach > 64.0 and reach < 80.0, "topdown: a running jump carries %.1f units (%.2f tiles)" % [reach, reach / 32.0])
	# One level up with a jump, not two; a wall one level high stops a walk.
	for lv in [1, 2]:
		var rows: Array = []
		for y in 12: rows.append(str(lv).repeat(20) if y < 4 else "0".repeat(20))
		var u := TopdownMotor.new(grid(rows), Vector2(320, 300))
		run(u, 1.2, Vector2.UP)
		var stopped := u.pos.y
		run(u, 1.0, Vector2.UP, [0])
		if lv == 1:
			t.check(absf(stopped - (128.0 + u.half.y)) < 1.0 and u.grounded and u.z == 32.0 and u.pos.y < 128.0,
				"topdown: a one-level face stops a walk at the foot box (%.1f) and a jump lands on top (z %.0f)" % [stopped, u.z])
		else:
			t.check(u.grounded and u.z == 0.0 and u.pos.y >= 128.0, "topdown: a jump does not reach two levels (z %.0f, y %.1f)" % [u.z, u.pos.y])
	# Stairs climb without a jump; the stair's steep side is a wall.
	var st_rows: Array = []
	for y in 12: st_rows.append("1".repeat(20) if y < 4 else "0".repeat(20))
	var st_room := grid(st_rows, {"stairs": [{"x": 8, "y": 4, "w": 3, "h": 2, "from": 0, "to": 1}]})
	var s := TopdownMotor.new(st_room, Vector2(9.5 * 32.0, 9.0 * 32.0))
	var ev2 := run(s, 1.6, Vector2.UP)
	t.check(s.grounded and s.z == 32.0 and s.pos.y < 128.0 and not "jumped" in types(ev2) and not "fell" in types(ev2), "topdown: the stairs walk up a level (z %.0f)" % s.z)
	var side := TopdownMotor.new(st_room, Vector2(12.5 * 32.0, 4.4 * 32.0))
	run(side, 1.0, Vector2.LEFT)
	t.check(side.pos.x > 11.0 * 32.0 and side.z == 0.0, "topdown: the stairs' high side blocks a walk from the level below (x %.1f)" % side.pos.x)

func _ledge_room(lv := 1) -> TopdownRoom:
	var rows: Array = []
	for y in 12: rows.append(str(lv).repeat(20) if y < 6 else "0".repeat(20))
	return grid(rows)

func _falls_and_windows() -> void:
	# Walking off an open edge falls a level, with no cost; the landing reports the fall.
	var m := TopdownMotor.new(_ledge_room(), Vector2(320, 160))
	var ev := run(m, 1.0, Vector2.DOWN)
	var land: Array = ev.filter(func(e): return e.type == "landed")
	t.check("fell" in types(ev) and m.grounded and m.z == 0.0 and not land.is_empty() and absf(float(land[0].fall) - 32.0) < 0.5,
		"topdown: walking off a ledge falls a level and lands (%s)" % str(types(ev)))
	# Coyote time: Jump just after leaving the edge still jumps, from the ledge's height; later it does not.
	for late in [0.0, 0.08, 0.2]:
		var c := TopdownMotor.new(_ledge_room(3), Vector2(320, 185))   # three levels: still falling at 0.2 s
		while c.grounded:
			c.step(1.0 / 120.0, Vector2.DOWN)
		c.drain()
		var steps := roundi(late * 120.0)
		for i in steps: c.step(1.0 / 120.0, Vector2.DOWN)
		c.step(1.0 / 120.0, Vector2.DOWN, true)
		var jumped := "jumped" in types(c.drain())
		t.check(jumped == (late <= 0.1), "topdown: Jump %.2f s after walking off a ledge %s (coyote %.2f s)" % [late, "jumps" if jumped else "does not jump", c.coyote_s])
	measured.coyote_s = TopdownMotor.conf("coyote_s")
	# The buffer: Jump pressed just before landing jumps on landing; pressed too early it is forgotten.
	for early in [0.1, 0.2]:
		var b := TopdownMotor.new(grid(flat()), Vector2(200, 192))
		b.step(1.0 / 60.0, Vector2.ZERO, true)
		var until_land: float = b.airtime() - 1.0 / 60.0 - early
		for i in roundi(until_land * 120.0): b.step(1.0 / 120.0, Vector2.ZERO)
		b.drain()
		b.step(1.0 / 120.0, Vector2.ZERO, true)
		var ev3 := run(b, 0.3, Vector2.ZERO)
		var again := types(ev3).count("jumped") > 0
		t.check(again == (early <= 0.12), "topdown: Jump %.2f s before landing %s (buffer %.2f s)" % [early, "jumps on landing" if again else "is dropped", b.buffer_s])
	measured.buffer_s = TopdownMotor.conf("buffer_s")

func _collision() -> void:
	var rows := flat()
	rows[4] = "0000011111000000000"  + "0"
	var room := grid(rows)
	# Straight into a face: stops at the foot box; diagonally: slides along it.
	var m := TopdownMotor.new(room, Vector2(7.5 * 32.0, 7.0 * 32.0))
	run(m, 1.0, Vector2.UP)
	t.check(absf(m.pos.y - (5.0 * 32.0 + m.half.y)) < 1.0, "topdown: walking into a raised row stops at its south face (y %.1f)" % m.pos.y)
	var d := TopdownMotor.new(room, Vector2(7.5 * 32.0, 5.5 * 32.0))
	var x0 := d.pos.x
	run(d, 0.5, Vector2(1, -1).normalized())
	t.check(d.pos.x - x0 > 40.0 and absf(d.pos.y - (5.0 * 32.0 + d.half.y)) < 1.0, "topdown: a diagonal into a face slides along it (%.1f along)" % (d.pos.x - x0))
	# Corner sliding: heading north with the foot box clipping the row's corner by 4 units, a nudge takes it round.
	var c := TopdownMotor.new(room, Vector2(10.0 * 32.0 + c_half() - 4.0, 7.0 * 32.0))
	run(c, 1.2, Vector2.UP)
	t.check(c.pos.y < 4.0 * 32.0 and c.pos.x >= 10.0 * 32.0 + c.half.x, "topdown: a corner clipped by 4 units slides round (x %.1f, y %.1f)" % [c.pos.x, c.pos.y])
	var far := TopdownMotor.new(room, Vector2(9.5 * 32.0, 7.0 * 32.0))
	run(far, 1.0, Vector2.UP)
	t.check(far.pos.y > 5.0 * 32.0, "topdown: a face met square on is not nudged round (y %.1f)" % far.pos.y)
	# Props block at every height.
	var pr := grid(flat(), {"props": [{"kind": "barrel", "x": 5, "y": 3}]})
	var p := TopdownMotor.new(pr, Vector2(5.5 * 32.0, 6.0 * 32.0))
	run(p, 1.0, Vector2.UP, [30])
	t.check(p.pos.y > 4.0 * 32.0 and pr.level(5, 3) == TopdownRoom.SOLID, "topdown: a prop's footprint blocks, even in a jump (y %.1f)" % p.pos.y)

func c_half() -> float:
	return float((TopdownMotor.conf("box", [16, 10]) as Array)[0]) * 0.5

func _water_room(gap: int) -> TopdownRoom:
	var rows: Array = []
	for y in 12: rows.append("0".repeat(5) + "~".repeat(gap) + "0".repeat(20 - 5 - gap))
	return grid(rows)

func _water_and_gaps() -> void:
	# The bank: walking never enters water.
	var m := TopdownMotor.new(_water_room(3), Vector2(3.0 * 32.0, 6.0 * 32.0))
	run(m, 1.0, Vector2.RIGHT)
	t.check(absf(m.pos.x - (5.0 * 32.0 - m.half.x)) < 1.0 and m.grounded, "topdown: a walk stops at the water's edge (x %.1f)" % m.pos.x)
	# A running jump crosses a one-tile gap; a three-tile gap sinks it and it comes back to the last safe spot.
	for gap in [1, 3]:
		var j := TopdownMotor.new(_water_room(gap), Vector2(3.0 * 32.0, 6.0 * 32.0))
		run(j, 1.0, Vector2.RIGHT)
		var ev := run(j, 1.6, Vector2.RIGHT, [0])
		if gap == 1:
			t.check(j.pos.x > 6.0 * 32.0 and j.grounded and not "splashed" in types(ev), "topdown: a running jump crosses a one-tile gap")
		else:
			t.check("splashed" in types(ev) and "reset" in types(ev) and j.pos.x < 5.0 * 32.0 and j.grounded, "topdown: a jump short of a three-tile gap splashes and returns to the bank (%s)" % str(types(ev)))
	# Dash, then Jump: the long jump clears three tiles.
	var l := TopdownMotor.new(_water_room(3), Vector2(3.5 * 32.0, 6.0 * 32.0))
	run(l, 0.4, Vector2.RIGHT)
	var x0 := l.pos.x
	var ev2 := run(l, 1.5, Vector2.RIGHT, [8], [0])
	var long: Array = ev2.filter(func(e): return e.type == "jumped")
	t.check(not long.is_empty() and bool(long[0].long) and l.pos.x > 8.0 * 32.0 and not "splashed" in types(ev2), "topdown: dash then Jump is a long jump over three tiles of water (x %.1f)" % l.pos.x)
	var lj := TopdownMotor.new(grid(flat(40)), Vector2(64, 192))
	run(lj, 0.4, Vector2.RIGHT)
	lj.step(1.0 / 60.0, Vector2.RIGHT, false, true)
	run(lj, 5.0 / 60.0, Vector2.RIGHT)
	var from := lj.pos.x
	lj.step(1.0 / 60.0, Vector2.RIGHT, true)
	while not lj.grounded: lj.step(1.0 / 120.0, Vector2.RIGHT)
	measured.long_jump = lj.pos.x - from
	t.check(lj.pos.x - from > 128.0, "topdown: a long jump carries %.1f units (%.1f tiles)" % [lj.pos.x - from, (lj.pos.x - from) / 32.0])

func _dash() -> void:
	var m := TopdownMotor.new(grid(flat(30)), Vector2(200, 192))
	var x0 := m.pos.x
	var ev := run(m, 0.3, Vector2.RIGHT, [], [0])
	var dash_units := m.pos.x - x0
	var b := TopdownMotor.new(grid(flat(30)), Vector2(400, 192))
	b.dir = Vector2.RIGHT
	run(b, 0.3, Vector2.ZERO, [], [0])
	var back := 400.0 - b.pos.x
	var again := run(m, 1.0, Vector2.RIGHT, [], [0])
	measured.dash = dash_units
	measured.back_step = back
	t.check("dashed" in types(ev) and dash_units > 96.0 and dash_units < 120.0 and absf(back - 48.0) < 3.0 and not "dashed" in types(again),
		"topdown: a dash covers %.1f (96 dashing, then sprinting), a standing back-step %.1f, and waits out its %.1f s cooldown" % [dash_units, back, m.dash_cooldown])

## Sort keys (plan §1.3): behind a raised row sorts before it, on top of it or in front of it after; ties go to the higher.
func _sort_keys() -> void:
	var r := _ledge_room()   # level 1 on rows 0-5; its last row's south edge is at 6 tiles = 96 art px
	var strip := 96.0
	var behind := r.sort_key(Vector2(160, 5.5 * 32.0), 0.0)   # not possible on this map, but a body at ground height
	var on_top := r.sort_key(Vector2(160, 5.5 * 32.0), 32.0)
	var front := r.sort_key(Vector2(160, 6.5 * 32.0), 0.0)
	var jumping := r.sort_key(Vector2(160, 6.5 * 32.0), 40.0)
	t.check(behind < strip and on_top > strip and front > strip and jumping > front, "topdown: sort keys: behind %.2f < row %.0f < on top %.2f; in front %.2f < in the air %.2f" % [behind, strip, on_top, front, jumping])
	var keys := [behind, on_top, front, jumping]
	t.check(keys.all(func(k): return is_equal_approx(k * 64.0, roundf(k * 64.0))), "topdown: every sort key is a multiple of 1/64 art px")
	var pr := grid(flat(), {"props": [{"kind": "house", "x": 4, "y": 2}]})
	t.check(pr.sort_key(Vector2(6 * 32.0, 1.5 * 32.0), 0.0) < 5 * 16.0 and pr.sort_key(Vector2(6 * 32.0, 5.5 * 32.0), 0.0) > 5 * 16.0,
		"topdown: a body behind the house sorts before its south edge, one in front after")

func _facing() -> void:
	var m := TopdownMotor.new(grid(flat()), Vector2(200, 192))
	var rows: Array = []
	for deg in [0.0, 45.0, 62.0, 82.0, 60.0, 180.0, -90.0, -135.0, 150.0]:
		m.step(1.0 / 60.0, Vector2.from_angle(deg_to_rad(deg)))
		rows.append(m.row)
	t.check(rows == ["e", "se", "se", "s", "se", "w", "n", "nw", "sw"],
		"topdown: facing picks one of 8 rows (S, SE, E, NE, N drawn; NW, W, SW mirrored) with 10° hysteresis (%s)" % str(rows))

# ------------------------------------------------------------------ Phase 2 (decisions 29 and 30)
## Walking stops at the water's edge; walking on water is a special skill (Water Skimming), off by default.
func _water_skill() -> void:
	var off := TopdownMotor.new(_water_room(3), Vector2(3.0 * 32.0, 6.0 * 32.0))
	var ev_off := run(off, 1.5, Vector2.RIGHT)
	var on := TopdownMotor.new(_water_room(3), Vector2(3.0 * 32.0, 6.0 * 32.0))
	on.water_walk = true
	var ev_on := run(on, 1.5, Vector2.RIGHT)
	t.check(not off.water_walk and off.pos.x < 5.0 * 32.0 and not "splashed" in types(ev_off) and on.pos.x > 8.0 * 32.0 and on.grounded and on.z == 0.0 \
		and not "splashed" in types(ev_on) and not "fell" in types(ev_on),
		"topdown: water stops a walk (x %.0f) unless the skill is on, which walks across it on the surface (x %.0f, z %.0f)" % [off.pos.x, on.pos.x, on.z])

## Roofs are floors (decision 29): the storehouse's roof two levels up is a wall from the square, reached from the
## terrace a level below it or from the crates beside it, and dropping off its edge falls to the square.
func _roofs() -> void:
	var room := TopdownRoom.load_room("td_proto_square")
	var sh: Dictionary = room.props.filter(func(q): return q.kind == "storehouse")[0]
	var cell: Vector2i = sh.cell
	var from_terrace := TopdownMotor.new(room, Vector2((cell.x + 1.5) * 32.0, (cell.y - 0.5) * 32.0))
	run(from_terrace, 0.6, Vector2.DOWN)
	var stopped_z := from_terrace.z
	var stopped_y := from_terrace.pos.y
	run(from_terrace, 0.3, Vector2.DOWN, [0])
	while not from_terrace.grounded: from_terrace.step(1.0 / 120.0, Vector2.ZERO)
	from_terrace.drain()
	var on_roof := from_terrace.z
	var roof_key := room.sort_key(from_terrace.pos, from_terrace.z)
	var ev := run(from_terrace, 1.2, Vector2.DOWN)
	var land: Array = ev.filter(func(e): return e.type == "landed")
	measured.roof_drop = float(land[0].fall) if not land.is_empty() else -1.0
	t.check(stopped_z == 32.0 and stopped_y < cell.y * 32.0 and on_roof == 64.0 and roof_key > (cell.y + 3) * 16.0 + 0.5 and "fell" in types(ev)
		and from_terrace.z == 0.0 and from_terrace.grounded and not land.is_empty() and absf(float(land[0].fall) - 64.0) < 1.0,
		"topdown: the roof is a wall from the terrace (z %.0f), a jump lands on it (z %.0f, drawn over the building), and walking off its edge drops %.0f to the square" % [stopped_z, on_roof, measured.roof_drop])
	var crates: Dictionary = room.props.filter(func(q): return q.kind == "crates")[0]
	var cc: Vector2i = crates.cell
	var climber := TopdownMotor.new(room, Vector2((cc.x + 0.5) * 32.0, (cc.y + 2.5) * 32.0))
	run(climber, 0.8, Vector2.UP)
	var blocked := climber.z
	# Tiptoe (stick at half) so a jump lands on a one-tile-deep top instead of carrying over it.
	run(climber, 0.38, Vector2(0, -0.5), [0])
	run(climber, 0.2, Vector2.ZERO)
	var on_crates := climber.z
	run(climber, 0.4, Vector2(-0.5, 0), [0])
	run(climber, 0.2, Vector2.ZERO)
	t.check(blocked == 0.0 and on_crates == 32.0 and climber.z == 64.0 and climber.grounded,
		"topdown: from the square the crates (one level) and then the roof (two) are each a jump up (z %.0f → %.0f → %.0f)" % [blocked, on_crates, climber.z])

## The aim rules (TopdownAim): the height band, the four forms and the gesture a thumb makes on a button.
func _aim_rules() -> void:
	t.check(TopdownAim.compatible(0.0) and TopdownAim.compatible(10.0) and not TopdownAim.compatible(32.0) and not TopdownAim.compatible(-32.0)
		and TopdownAim.compatible(-47.0, true) and not TopdownAim.compatible(-64.0, true),
		"topdown: blows land between compatible heights: a level up or down is out of reach, a jump strike reaches down onto one")
	var o := Vector2.ZERO
	var r := Vector2.RIGHT
	var line_ok := TopdownAim.contains("line", o, r, o, 200.0, 20.0, Vector2(150, 10), 8.0) and not TopdownAim.contains("line", o, r, o, 200.0, 20.0, Vector2(150, 60), 8.0)
	var cone_ok := TopdownAim.contains("cone", o, r, o, 100.0, 0.0, Vector2(60, 50), 8.0) and not TopdownAim.contains("cone", o, r, o, 100.0, 0.0, Vector2(20, 80), 8.0)
	var at := TopdownAim.point_at(o, r, 150.0, 200.0)
	var point_ok := TopdownAim.contains("point", o, r, at, 200.0, 0.0, Vector2(160, 20), 8.0) and not TopdownAim.contains("point", o, r, at, 200.0, 0.0, Vector2(30, 0), 8.0)
	var self_ok := TopdownAim.contains("self", o, r, o, 100.0, 0.0, Vector2(-80, 30), 8.0) and not TopdownAim.contains("self", o, r, o, 100.0, 0.0, Vector2(-120, 30), 8.0)
	var forms := ["updraft_rending_rolling_wave", "flowing_palm", "rising_tide", "hundred_springs_rising", "venom_needles"].map(func(id): return TopdownAim.form_of(ContentDB.entry("techniques", id)))
	t.check(line_ok and cone_ok and point_ok and self_ok and forms == ["line", "cone", "point", "self", "line"],
		"topdown: aim shapes per form: a wave is a line, a flurry a cone, a burst a circle at a point, a domain round the caster, a shot a line (%s)" % str(forms))
	# The thumb: a quick tap, a hold and a drag that aims, a drag back onto the button that cancels; left-handed or not.
	var tap := AimGesture.new("attack", Vector2(1165, 605))
	tap.advance(0.08)
	var aimed := AimGesture.new("attack", Vector2(1165, 605))
	aimed.advance(0.2)
	aimed.drag(Vector2(1165 - 60, 605 - 60))
	var back := AimGesture.new("skill", Vector2(1033, 605), 0)
	back.drag(Vector2(1033, 605 - 90))
	back.drag(Vector2(1033 + 10, 605 - 5))
	var lefty := AimGesture.new("attack", Vector2(1280 - 1165, 605))
	lefty.drag(Vector2(1280 - 1165 + 90, 605))
	var far := AimGesture.new("skill", Vector2(1033, 605), 2)
	far.drag(Vector2(1033, 605 + 200))
	t.check(tap.release() == "tap" and aimed.release() == "aim" and aimed.dir().is_equal_approx(Vector2(-1, -1).normalized()) and back.release() == "cancel"
		and lefty.release() == "aim" and lefty.dir() == Vector2.RIGHT and is_equal_approx(far.reach_k(), 1.0),
		"topdown: a tap is a tap; held and dragged it aims along the drag (%s); back on the button it cancels; the left-handed button aims the same" % str(aimed.dir()))

# ------------------------------------------------------------------ Phase 3 (decisions 33 and 34)
## The terrain rules the room view draws by (TopdownTerrain, art bible §3–§6), on a small room made for them: paths
## take grass's corner-matched edge only from grass on their own level, water its shore case, raised edges their rims,
## contact shade and cast shade, faces their ends and their kind over water, and a prop's shadow only its own floor.
func _terrain_rules() -> void:
	var rows := ["00000000", "01110000", "01110000", "00000000", "~~~~0000", "~~~~0000"]
	var paint := ["ggggpppp", "gbbbgppp", "gbbbgddd", "gddgpddd", "~~~~wsss", "~~~~wsss"]
	var tr := TopdownTerrain.new(grid(rows, {"paint": paint, "props": [{"kind": "lantern", "x": 2, "y": 1}, {"kind": "lantern", "x": 6, "y": 0}]}))
	var edge := tr.top(1, 3)    # dirt with grass to its west on the ground: the grass creeps over its west corners
	var cut := tr.top(2, 3)     # dirt under the planter's grass (a level up) and beside grass on the ground to its east
	var plain := tr.top(6, 3)   # dirt with no grass at any corner
	var shore := tr.water(1, 4)
	t.check(edge == "grass_dirt_1010" and cut == "grass_dirt_0101" and plain in ["dirt", "dirt_b"] and shore.size() == 4 and str(shore[0]) == "shore_01_0" and tr.shore_sides(3, 5) == 2,
		"topdown terrain: a path takes grass's corner edge from its own level only (%s, %s, %s); water under land takes its shore case (%s)" % [edge, cut, plain, str(shore[0])])
	var top_l := tr.overlays(1, 1, 1)
	var foot := tr.overlays(2, 3, 0)
	var east := tr.overlays(4, 1, 0)
	t.check(top_l.has("rim_w") and top_l.has("rim_n") and not top_l.has("rim_e") and foot.has("ao_n") and east.has("shade_w") and tr.overlays(3, 1, 1).has("rim_e"),
		"topdown terrain: a raised top takes its rims (%s), the floor at a face's foot its contact shade (%s) and the floor east of it the cast shade (%s)" % [str(top_l), str(foot), str(east)])
	t.check(tr.face(2, 2, 0, false) == "stone_face_top" and tr.face_ends(1, 2, 1, 0) == ["end_w"] and tr.face_ends(3, 2, 1, 0) == ["end_e"]
		and tr.face(3, 3, 0, true) == "earth_face_top" and tr.face(4, 3, 0, true) == "bank_face_top" and tr.face(4, 4, 0, true) == "wood_face_top",
		"topdown terrain: a planter's face is stone with its ends lit west and shaded east; over water grass keeps its soil, paving takes the embankment, a pier its pilings")
	var up: Array = tr.shadow_pieces(1, 1)
	var up_on_ground: Array = (tr.shadow_pieces(1, 0) + tr.shadow_pieces(2, 0)).filter(func(p): return (p[0] as Rect2).position.x < 64.0)
	var ground: Array = tr.shadow_pieces(0, 0)
	t.check(not up.is_empty() and up_on_ground.is_empty() and not ground.is_empty() and up.all(func(p): return (p[0] as Rect2).position.y >= 16.0 and (p[0] as Rect2).end.y <= 32.0),
		"topdown terrain: a prop's floor shadow lies on its own level's cells, cut to them (%d pieces on the planter, %d beside it on the ground)" % [up.size(), up_on_ground.size()])

## Decision 40, runtime light (art bible §14.2, §14.11): the cast shadows a block and a tall prop throw
## (TopdownShadows, baked once as the room is built) and the look of an area at an hour (TopdownLight).
func _light_rules() -> void:
	var rows := flat(10, 8)
	rows[1] = "0220000000"
	rows[2] = "0220000000"
	var before := TopdownShadows.bakes
	var sh := TopdownShadows.new(grid(rows, {"props": [{"kind": "lantern", "x": 6, "y": 5}]}))
	var edge := TopdownShadows.edge().a
	# The alpha step at (x, y): 1 the body, EDGE the stepped edge, 0 none.
	var step := func(img: Image, x: int, y: int) -> String:
		var a := img.get_pixel(x, y).a
		return "body" if a > 0.9 else ("edge" if absf(a - edge) < 0.02 else ("none" if a < 0.01 else "%.2f" % a))
	var count := func(img: Image, r: Rect2i) -> int:
		var n := 0
		for y in range(r.position.y, r.end.y):
			for x in range(r.position.x, r.end.x): if img.get_pixel(x, y).a > 0.5: n += 1
		return n
	# A 2x2 block two levels high (32 px): its shadow reaches 0.45 x 32 = 14 px east and 0.20 x 32 = 6 px south, a body
	# inside a 2 px stepped edge; nearest the block, over the tiles' own shade, only the edge (east) or nothing (the
	# first row under its face); the floor north and west of it and its own top stay lit.
	var east: Array = [step.call(sh.image, 49, 26), step.call(sh.image, 53, 26), step.call(sh.image, 60, 26), step.call(sh.image, 62, 26)]
	var south: Array = [step.call(sh.image, 30, 48), step.call(sh.image, 30, 49), step.call(sh.image, 30, 51), step.call(sh.image, 30, 54)]
	var lit: bool = [[8, 8], [8, 40], [20, 20], [40, 4]].all(func(q): return sh.image.get_pixel(q[0], q[1]).a < 0.01)
	t.check(TopdownShadows.bakes == before + 1 and east == ["edge", "body", "edge", "none"] and south == ["none", "edge", "body", "none"] and lit,
		"topdown light: a block two levels high casts 0.45 h east and 0.20 h south, a body in a stepped edge, only the edge by the block and nothing on its contact shade, nothing north, west or on its top (east %s, south %s, lit %s)" % [str(east), str(south), lit])
	# One level casts nothing at runtime: that step's shadow is the tiles' own (shade_w, ao_n).
	rows = flat(10, 6)
	rows[1] = "0110000000"
	var low := TopdownShadows.new(grid(rows))
	t.check(count.call(low.image, Rect2i(0, 0, 160, 96)) == 0, "topdown light: a one-level step casts nothing at runtime (its shadow is baked in the tiles)")
	# A stone lantern (32 px tall) lays its silhouette to its south-east, nothing to its west.
	var cast: int = count.call(sh.image, Rect2i(98, 84, 30, 12))
	var west: int = count.call(sh.image, Rect2i(80, 80, 16, 32))
	t.check(cast > 20 and west == 0, "topdown light: a tall prop lays its silhouette on the floor to its south-east (%d px), none to its west (%d)" % [cast, west])
	# Three levels over a one-level step: the shadow lies on the step and falls down its drop onto the ground past it,
	# where the step alone casts nothing.
	rows = flat(10, 6)
	rows[1] = "0331000000"
	var drop := TopdownShadows.new(grid(rows))
	t.check(drop.image.get_pixel(66, 30).a > 0.5 and drop.image.get_pixel(54, 20).a > 0.5 and drop.plane[1 * 10 + 3] == 16,
		"topdown light: a shadow falls down a cliff's drop, longer by the drop (onto the step and past it onto the ground)")
	# The look: the village's midday lifts its lights toward the sun and its darks toward the shadow, within the
	# contract's 4% and +5% saturation at every hour of every area; the marsh's lights lean to the mist; a night room is
	# the story's night in the night tint with its lights; the clock's night outdoors lights the lamps and sends the
	# fireflies out; rain closes the sky; an interior is lamp-lit.
	var day := TopdownLight.look({"backdrop": "valley_day"}, 0.375)
	var marsh := TopdownLight.look({"backdrop": "marsh"}, 0.375)
	var story := TopdownLight.look({"backdrop": "valley_night", "night": true}, 0.375)
	var night := TopdownLight.look({"backdrop": "valley_day"}, 0.87)
	var rain := TopdownLight.look({"backdrop": "valley_day"}, 0.375, "rain")
	var inside := TopdownLight.look({"backdrop": "interior"}, 0.87)
	var within := true
	for area in TopdownLight.AREAS:
		for hour in [0.1, 0.25, 0.375, 0.5, 0.62, 0.75, 0.87]:
			var g: Dictionary = TopdownLight.look({"backdrop": area}, hour).grade
			if float(g.sun) > 0.04 or float(g.shade) > 0.04 or float(g.sat) > 1.05: within = false
	t.check(str(day.hour) == "day" and float(day.lights) == 0.0 and float(day.grade.sun) > 0.0 and float(day.grade.shade) > 0.0 and within
		and marsh.grade.hi == TopdownLight.MIST and float(marsh.grade.sat) < 1.0 and str(story.hour) == "night_story" and float(story.lights) == 1.0
		and story.ambient == TopdownLight.NIGHT and str(night.hour) == "night" and float(night.lights) > 0.0 and float(night.fireflies) > 0.0
		and float(night.motes) == 0.0 and float(rain.motes) == 0.0 and float(rain.clouds) == 0.0 and str(inside.hour) == "lamplit",
		"topdown light: the grade stays within 4%% toward the sun or the shadow and +5%% saturation at every hour; the marsh leans to the mist, a night room is the story's night in #8FA0C8, the clock's night lit by lamps and fireflies, rain without sun, an interior lamp-lit (within %s)" % within)

## Terrain v2 (decision 40, art bible "Terrain v2"): the layers the room view draws. A top's base is its material's
## pattern at the cell's place in it, so neighbours differ and still join; a path under grass lies under the positional
## grass overlay of its corner case; a face's tile follows its column, and its last row over a floor takes the foot
## shade, never over water; water has four frames, its pattern's tile first, a shore cell its side case's overlay, and
## wide water the depth tint; the sun and shade patches lie on a real room's meadows. Every layer is a tile of the atlas.
func _terrain_v2() -> void:
	var rows := ["00000000", "01110000", "01110000", "00000000", "~~~~0000", "~~~~0000"]
	var paint := ["ggggpppp", "gbbbgppp", "gbbbgddd", "gddgpddd", "~~~~wsss", "~~~~wsss"]
	var tr := TopdownTerrain.new(grid(rows, {"paint": paint}))
	var tiles: Dictionary = tr.room.tileset.get("tiles", {})
	var a := tr.top_layers(0, 0, 0)
	var b := tr.top_layers(1, 0, 0)
	var edge := tr.top_layers(1, 3, 0)
	t.check(str(a[0][0]).begins_with("grass_m") and str(b[0][0]).begins_with("grass_m") and a[0][0] != b[0][0]
		and str(edge[0][0]).begins_with("dirt_m") and str(edge[1][0]) == "over_1010_13",
		"terrain v2: tops take their pattern's tile by place (%s, %s); a path under grass takes the positional overlay (%s over %s)" % [a[0][0], b[0][0], edge[1][0], edge[0][0]])
	var planter := tr.face_layers(2, 2, 1, 0, 0)
	var bank := tr.face_layers(0, 3, 0, 0, TopdownRoom.WATER)
	t.check(str(planter[0][0]) == "stone_face_top_v2" and str(planter[-1][0]) == "face_ao" and str(bank[0][0]) == "earth_face_top_v0"
		and not bank.any(func(l): return str(l[0]) == "face_ao") and tr.face(2, 2, 0, false) == "stone_face_top",
		"terrain v2: a face's tile follows its column (%s), with the foot shade over a floor and none over water (%s)" % [planter[0][0], bank[0][0]])
	var w := tr.water_layers(1, 4)
	var names: Array = w.map(func(f): return str(f[0][0]))
	t.check(w.size() == 4 and names.all(func(n): return n.begins_with("water_m")) and str(w[2].back()[0]) == "shorefx_01_2",
		"terrain v2: water draws its pattern in four frames (%s) and a shore cell its side case's overlay (%s)" % [str(names), w[2].back()[0]])
	var lake := ["000000000"]
	for i in 7: lake.append("0~~~~~~~0")
	lake.append("000000000")
	var deep: Array = TopdownTerrain.new(grid(lake)).water_layers(4, 4)[0]
	var square := TopdownTerrain.new(TopdownRoom.load_room("td_proto_square"))
	var tints := {}
	var missing: Array = []
	for y in square.room.h:
		for x in square.room.w:
			var l := square.lv(x, y)
			var layers: Array = square.water_layers(x, y)[1] if l == TopdownRoom.WATER else square.top_layers(x, y, l)
			for layer in layers:
				if not tiles.has(str(layer[0])): missing.append(str(layer[0]))
				if str(layer[0]).begins_with("tint_"): tints[(layer[1] as Color).to_html()] = true
			for k in range(maxi(0, l)):
				for layer in square.face_layers(x, y, l, k, 0):
					if not tiles.has(str(layer[0])): missing.append(str(layer[0]))
	t.check(deep.any(func(l): return str(l[0]).begins_with("tint_")) and tints.size() >= 3 and missing.is_empty(),
		"terrain v2: wide water is tinted deep; Riverside Square has sun, shade and depth tints (%d colours); every layer is in the atlas (%s)" % [tints.size(), str(missing.slice(0, 4))])

## Riverside Square as redesigned for the terrain (decisions 33 and 34): the paved ways lead from the house door, the
## storehouse door and the stairs' foot to the pier; the terrace's dirt path leads from the stairs' head to the rooftop
## jump above the storehouse and up to the shrine; the lotus pond is still water inside a curb; the bamboo, lotus and
## lanterns are placed, the plants animated.
func _square_layout() -> void:
	var room := TopdownRoom.load_room("td_proto_square")
	var find := func(kind: String) -> Dictionary: return room.props.filter(func(q): return q.kind == kind)[0]
	var house: Dictionary = find.call("house")
	var store: Dictionary = find.call("storehouse")
	var door := func(p: Dictionary) -> Vector2i: return Vector2i((p.cell as Vector2i).x + (p.size as Vector2i).x / 2, (p.cell as Vector2i).y + (p.size as Vector2i).y)
	var to_pier := [door.call(house), door.call(store), Vector2i(15, 14)].map(func(c): return _path_reaches(room, c, "psw", func(q): return room.paint_at(q.x, q.y) == "w"))
	var sc: Vector2i = store.cell
	var roof_jump := Vector2i(sc.x + 1, sc.y - 1)
	var shrine: Dictionary = find.call("incense")
	var terrace := [_path_reaches(room, Vector2i(15, 11), "d", func(q): return q == roof_jump), _path_reaches(room, Vector2i(15, 11), "d", func(q): return q == (shrine.cell as Vector2i) + Vector2i(0, 1))]
	measured.layout_routes = to_pier + terrace
	t.check(to_pier.all(func(ok): return ok) and terrace.all(func(ok): return ok),
		"topdown square: paved ways lead from the house door, the storehouse door and the stairs to the pier %s; the terrace path leads to the rooftop jump and the shrine %s" % [str(to_pier), str(terrace)])
	var kinds := {}
	for p in room.props: kinds[p.kind] = int(kinds.get(p.kind, 0)) + 1
	var pond := 0
	for y in range(15, 22):
		for x in range(8, 16):
			if room.is_water(x, y) and not room.is_water(x, y - 1) and room.paint_at(x, y - 1) == "s": pond += 1
	var lotus_in_pond: bool = room.props.any(func(q): return q.kind == "lotus" and room.is_water((q.cell as Vector2i).x, (q.cell as Vector2i).y) and (q.cell as Vector2i).y < 22)
	t.check(pond >= 3 and lotus_in_pond and int(kinds.get("bamboo", 0)) >= 6 and int(kinds.get("lotus", 0)) >= 5 and int(kinds.get("lantern_red", 0)) >= 4
		and int(room.tileset.props.bamboo.get("frames", 1)) == 4 and int(room.tileset.props.lotus.get("frames", 1)) == 4,
		"topdown square: a lotus pond under a curb (%d), %d bamboo, %d lotus, %d red lanterns; bamboo sway and lotus bob in 4 frames" % [pond, int(kinds.get("bamboo", 0)), int(kinds.get("lotus", 0)), int(kinds.get("lantern_red", 0))])

## Does a walk over cells painted with one of `marks` (4-way, on one level, stairs included) from `from` reach a cell
## `goal` accepts (checked on the path's neighbours too, so a pier or a roof's edge counts when the path meets it)?
func _path_reaches(room: TopdownRoom, from: Vector2i, marks: String, goal: Callable) -> bool:
	var seen := {from: true}
	var todo: Array = [from]
	while not todo.is_empty():
		var c: Vector2i = todo.pop_front()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if not room.inside(n.x, n.y) or seen.has(n): continue
			if goal.call(n): return true
			var stairs := not room.stair_at(n.x, n.y).is_empty() or not room.stair_at(c.x, c.y).is_empty()
			if room.level(n.x, n.y) == TopdownRoom.SOLID or not marks.contains(room.paint_at(n.x, n.y)) or (room.level(n.x, n.y) != room.level(c.x, c.y) and not stairs): continue
			seen[n] = true
			todo.append(n)
	return false
## Decision 35, the thumb on Attack: every drag zone is a 48 px target on both layouts, and each drag reads as its move.
func _drag_zones() -> void:
	var dead := float(TopdownAim.cfg("dead_px", 18))
	var zone := float(TopdownAim.cfg("zone_px", 48))
	var zones_ok := true
	var worst := INF
	for origin in [Vector2(1165, 605), Vector2(1280 - 1165, 605)]:
		var probe := AimGesture.new("attack", origin)
		for i in 72:
			var d := Vector2.from_angle(TAU * i / 72.0)
			var line := probe.long_px(d)
			var band := probe.edge_room(d) - line
			worst = minf(worst, minf(band, line - dead))
			zones_ok = zones_ok and band >= zone - 0.01 and line - dead >= zone - 0.01
	var right := AimGesture.new("attack", Vector2(1165, 605))
	measured.finisher_line = {"up": right.long_px(Vector2.UP), "right": right.long_px(Vector2.RIGHT), "down": right.long_px(Vector2.DOWN)}
	var half := deg_to_rad(float(TopdownAim.cfg("plunge_deg", 35)))
	var plunge_w := 2.0 * float(TopdownAim.cfg("plunge_px", 48)) * sin(half)
	var plunge_d := right.edge_room(Vector2.DOWN) - float(TopdownAim.cfg("plunge_px", 48))
	t.check(zones_ok and plunge_w >= 48.0 and plunge_d >= 48.0 and is_equal_approx(right.long_px(Vector2.UP), 120.0),
		"topdown drag moves: the aim's band and the finisher's band are each at least 48 px deep in every direction on both layouts (worst %.0f), the finisher's line 120 px where there is room (%s), the Plunge's sector %.0f px wide and %.0f deep" % [worst, str(measured.finisher_line), plunge_w, plunge_d])
	var at := func(o: Vector2, off: Vector2, secs := 0.05) -> AimGesture:
		var g := AimGesture.new("attack", o)
		g.advance(secs)
		g.drag(o + off)
		return g
	var o := Vector2(1165, 605)
	var lo := Vector2(1280 - 1165, 605)
	var reads := [at.call(o, Vector2(-95, -95)).move(), at.call(o, Vector2(0, -80)).move(), at.call(o, Vector2(70, 0)).move(), at.call(o, Vector2(60, 0)).move(),
		at.call(o, Vector2(0, 60)).move(true, true), at.call(o, Vector2(0, 60)).move(true, false), at.call(o, Vector2(60, 50)).move(true, true),
		at.call(o, Vector2(0, 60)).move(), at.call(o, Vector2(0, 100)).move(), at.call(o, Vector2(-130, 0)).move(true, true),
		at.call(lo, Vector2(-70, 0)).move(), at.call(lo, Vector2(0, 60)).move(true, true)]
	t.check(reads == ["finisher", "aim", "finisher", "aim", "plunge", "aim", "aim", "aim", "finisher", "aim", "finisher", "plunge"],
		"topdown drag moves: a long drag is the finisher (pulled in to 67 px by the right edge), a drag down in the air the Plunge only when it can, a short drag an aim; the left-handed button reads the same (%s)" % str(reads))
	var still := AimGesture.new("attack", o)
	still.advance(0.2)
	var early := still.holding()
	still.advance(0.12)
	var held := still.holding()
	var drift := AimGesture.new("attack", o)
	drift.drag(o + Vector2(25, 0))
	drift.drag(o)
	drift.advance(0.4)
	var skill := AimGesture.new("skill", o, 0)
	skill.advance(0.4)
	var guarding := AimGesture.new("attack", o)
	guarding.advance(0.4)
	guarding.guarding = true
	guarding.drag(o + Vector2(-95, -95))
	var refused := AimGesture.new("attack", o)
	refused.advance(0.4)
	refused.refused = true
	t.check(not early and held and not drift.holding() and not skill.holding() and guarding.move() == "guard" and refused.move() == "tap" and not refused.holding(),
		"topdown drag moves: Attack held still for 0.3 s asks for the guard (not a technique, not after a drift); guarding, any drag stays the guard; a refused guard lets go as a tap")

## The motor's Plunge: straight down at its speed from anywhere in the air, no steering, the impact on the landing.
func _motor_plunge() -> void:
	var m := TopdownMotor.new(grid(flat()), Vector2(160, 192))
	var on_ground := m.plunge(900.0)
	run(m, 0.15, Vector2.ZERO, [0])
	var z0 := m.z
	var x0 := m.pos
	var went := m.plunge(900.0)
	var again := m.plunge(900.0)
	var ev: Array = []
	var secs := 0.0
	while not m.grounded and secs < 1.0:
		ev.append_array(run(m, 1.0 / 60.0, Vector2.RIGHT))
		secs += 1.0 / 60.0
	var landed: Array = ev.filter(func(e): return str(e.type) == "landed")
	measured.plunge_drop = {"from": z0, "secs": snappedf(secs, 0.001)}
	t.check(not on_ground and went and not again and m.grounded and not m.plunging and m.pos.distance_to(x0) < 0.01 and secs <= z0 / 900.0 + 1.0 / 60.0 + 0.001
		and landed.size() == 1 and landed[0].get("plunge", false),
		"topdown: the motor's Plunge drops straight down at 900 (%.0f units in %.3f s), ignores the stick, and lands once with its impact; refused on the ground or twice" % [z0, secs])

## A finisher at once is never a faster way to deal damage than the chain it ends: per second of its step, within 6%
## of the whole chain's, for every weapon family with a chain.
func _finisher_pace() -> void:
	var worst := 0.0
	var who := ""
	for fam in ContentDB.all("weapon_families"):
		var combo: Array = fam.get("combo", [])
		if combo.size() < 2: continue
		var chain := 0.0
		var secs := 0.0
		for s in combo:
			chain += float(s.mult)
			secs += float(s.duration)
		var last: Dictionary = combo.back()
		var ratio := (float(last.mult) / float(last.duration)) / (chain / secs)
		if ratio > worst:
			worst = ratio
			who = str(fam.id)
	measured.finisher_pace = {"worst": snappedf(worst, 0.001), "family": who}
	t.check(worst <= 1.06, "topdown drag moves: a finisher alone deals at most 6%% more a second than its whole chain (worst %.3f, %s)" % [worst, who])

## The prototype room's view: its layout, the silhouette behind the house, sort order and whole-pixel placement.
func run_view(suite, tree: SceneTree) -> void:
	t = suite
	var was: String = Game.active_id
	Game.active_id = ""   # the view alone (the motor's rules), no character or foes: run_fight has those
	var w = TopdownWorld.new()
	tree.root.add_child(w)
	await tree.process_frame
	var room: TopdownRoom = w.room
	var levels := {}
	for l in room.levels: levels[l] = true
	t.check(levels.has(0) and levels.has(1) and levels.has(TopdownRoom.WATER) and room.stairs.size() >= 1 and room.props.any(func(p): return p.kind == "house"),
		"topdown: the prototype square has two levels, water, stairs and a house (%s)" % str(levels.keys()))
	t.check(w.viewport.size == Vector2i(640, 360) and w.container.stretch_shrink == 2 and w.viewport.snap_2d_transforms_to_pixel, "topdown: the world renders at 640x360 shown x2")
	# Phase 3: the water draws its shore cases, the plants sway on their own clocks.
	var water_view = w.viewport.get_children().filter(func(n): return n.get("cells") != null)[0]
	var shores: int = water_view.cells.filter(func(cl): return not str(cl[1][0]).begins_with("water_")).size()
	var swaying: Array = w.sorted.get_children().filter(func(n): return n.get("frames") is int and int(n.frames) == 4 and n.is_processing())
	var phases := {}
	for n in swaying: phases[n.phase] = true
	t.check(w.terrain != null and shores > 40 and swaying.size() >= 10 and phases.size() >= 2,
		"topdown: the room view draws %d shore cells and %d swaying or bobbing plants at %d phases" % [shores, swaying.size(), phases.size()])
	var p = w.player
	var m: TopdownMotor = p.motor
	var house: Dictionary = room.props.filter(func(q): return q.kind == "house")[0]
	var hc: Vector2i = house.cell
	# Behind the house (the lane on its north side): covered, the silhouette shows; in front of it: drawn after it.
	m.place(Vector2((hc.x + 2.5) * 32.0, (hc.y - 1) * 32.0 + 6.0))
	await tree.process_frame
	var house_view = w.sorted.get_children().filter(func(n): return n.get("src") != null and (n.rects[0] as Rect2).size.x > 90)[0]
	t.check(w.is_occluded() and p.position.y < house_view.position.y and m.grounded, "topdown: behind the house the body sorts first and shows its silhouette")
	m.place(Vector2((hc.x + 2.5) * 32.0, (hc.y + house.size.y) * 32.0 + 12.0))
	await tree.process_frame
	t.check(not w.is_occluded() and p.position.y > house_view.position.y, "topdown: in front of the house the body sorts after it, uncovered")
	# Whole pixels: walk a sub-pixel diagonal for a second; the body, its shadow and the camera stay on whole art px.
	m.place(room.spawn + Vector2(0.37, 0.61))
	var ok := true
	for f in 60:
		p.movement = Vector2(0.83, 0.41)
		await tree.physics_frame
		await tree.process_frame
		var body_y: float = p.position.y + (p.screen.y - p.position.y)
		ok = ok and p.position.x == roundf(p.position.x) and body_y == roundf(body_y) and w.camera.position == w.camera.position.round() \
			and is_equal_approx(p.position.y * 64.0, roundf(p.position.y * 64.0)) and w.shadow.position.x == roundf(w.shadow.position.x)
	p.movement = Vector2.ZERO
	t.check(ok and m.pos.x != roundf(m.pos.x), "topdown: the body, shadow and camera sit on whole art px while the motor moves in fractions")
	# The camera keeps to the ground height through a jump (no bobbing) and stays inside the room.
	for f in 90: await tree.process_frame
	var cam_before: Vector2 = w.camera.position
	p.jump()
	var worst := 0.0
	for f in 30:
		await tree.physics_frame
		await tree.process_frame
		worst = maxf(worst, absf(w.camera.position.y - cam_before.y))
	t.check(worst <= 1.0, "topdown: a jump in place does not move the camera (%.0f px)" % worst)
	w.queue_free()
	await tree.process_frame
	Game.active_id = was

# ------------------------------------------------------------------ Phase 2: the fight in the prototype room
var w            # the TopdownWorld under test
var c            # the character
var hud

## Frames of the simulation as the world runs them (the body's step, then Game.tick), at 60 fps.
func frames(n: int) -> void:
	for i in n:
		w.player.physics_step(1.0 / 60.0)
		Game.tick(1.0 / 60.0)

## An empty room, the body at `at` on its floor, whole and ready (no cooldown, no protection, no blow under way).
func fresh(at: Vector2) -> void:
	var rt: RoomRuntime = Game.room_rt
	rt.enemies.clear()
	rt.spawn_slots.clear()
	rt.loot.clear()
	rt.projectiles.clear()
	w.player.motor.place(at)
	w.player.motor.dir = Vector2.DOWN
	w.player.motor.dash_t = 0.0
	w.player.motor.since_dash = 99.0
	w.player.dodge_buffer = 0.0
	w.player.weave = {}
	w.player.physics_step(0.0001)
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.clear()
	for sid in ["spawn_protection", "stun", "slow", "root"]: Game.combat.cure_status(c.id, sid)
	Game.combat.wounded.erase(c.id)
	Game.combat.actors.erase(c.id)
	Game.combat.hitstop = 0.0

## A foe of `def` standing at `p` on the grid's floor, doing nothing until something happens to it.
func foe(def: String, p: Vector2, level := 1) -> EnemyState:
	var e: EnemyState = Game.enemies.spawn_at(def, p, level)
	e.altitude = w.room.height_at(p)
	e.ai.state = "idle"
	e.ai.timer = 99.0
	return e

func hurt(e: EnemyState) -> bool:
	return e.pools.hp < e.pools.max_hp

## The fight on the plane with the real authorities (Combat, Enemies, World) in the prototype room.
func run_fight(suite, tree: SceneTree) -> void:
	t = suite
	var made := {}
	if Game.active() == null and not Game.characters.is_empty(): Game.active_id = str(Game.characters.keys()[0])
	if Game.active() == null:   # a stand-in, as the prototype makes one from the title
		made = Game.submit({"type": "create_character", "slot": 1, "name": "Topdown", "appearance": {"hair": "topknot", "shirt": "disciple"}, "skip_prologue": true})
		Game.submit({"type": "enter_character", "slot": 1})
	c = Game.active()
	if c == null:
		t.check(false, "topdown fight: a character to fight with (%s)" % str(made))
		return
	# The stand-in's kit: bare hands and empty first slots, which the room's loadout fills (this is the suite's last use of
	# the character).
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	for i in 4: c.cultivator.technique_slots[i] = null
	var forced: bool = Unlocks.debug_force_all
	Unlocks.debug_force_all = true
	w = TopdownWorld.new()
	w.sim_frozen = true   # the suite steps the simulation itself
	tree.root.add_child(w)
	await tree.process_frame
	t.check(w.player.bound() and Game.room_rt.topdown == w.room and Game.room_rt.def.get("view") == "topdown" and Game.actor_state(c.id) == w.player.state,
		"topdown: the prototype room runs on the authorities (a RoomRuntime on the grid, the body bound)")
	var slots: Array = c.cultivator.technique_slots.slice(0, 4)
	t.check(slots == ["flowing_palm", "updraft_rending_rolling_wave", "rising_tide", "venom_needles"], "topdown: the stand-in's empty slots take the room's loadout, one technique per aim form (%s)" % str(slots))
	frames(90)
	var kinds := {}
	for e in Game.room_rt.enemies.values(): kinds[e.def_id] = true
	t.check(kinds.has("mudshell_crab") and kinds.has("reedtail_rat") and kinds.has("wild_boarlet") and w.foe_views.size() == Game.room_rt.enemies.size() and w.label_views.size() == Game.room_rt.enemies.size(),
		"topdown: the room's foes spawn by the Enemies authority, each with its figure and a label (%s)" % str(kinds.keys()))
	var base := Vector2(22.5, 19.5) * 32.0
	_foe_facings(base)
	_eight_ways(base)
	_heights()
	_shots(base)
	_push_and_dodge(base)
	_figure(base)
	_figure_moves(base)
	await _chase_and_leash(base)
	await _drops_and_prompt(tree)
	await _hud_aim(tree, base)
	await _drag_moves(tree, base)
	await _allies_on_the_grid(tree, base)
	await _hazards_on_the_grid(tree, base)
	_audit_on_the_grid(base)
	await _combat_feel(tree, base)
	_weave(base)
	_meditate_then_walk(base)
	await _labels_clean(tree, base)
	_eel_turns(base)
	_behind_a_dummy(base)
	w.queue_free()
	if is_instance_valid(hud): hud.queue_free()
	await tree.process_frame
	Unlocks.debug_force_all = forced

## Phase 3: a foe's figure (its sheet in art/topdown/foes/) turns to eight facings, five drawn and three mirrored: where it
## walks, else where it aims in a fight; a death plays once and holds its last frame.
func _foe_facings(base: Vector2) -> void:
	fresh(base)
	var e := foe("wild_boarlet", base + Vector2(80, 0))
	frames(1)
	var fv = w.foe_views.get(e.uid)
	if fv == null:
		t.check(false, "topdown: a foe spawned in the room gets its figure")
		return
	var seen: Array = []
	var west_y := -1.0
	for v in [Vector2(-60, 0), Vector2(40, -40), Vector2(0, 60), Vector2(-40, 40)]:
		e.velocity = v
		e.action = "walk"
		fv.sync(1.0 / 60.0)
		seen.append("%s%s" % [fv.facing, "*" if fv.flip else ""])
		if west_y < 0.0: west_y = fv.src.position.y
	e.velocity = Vector2.ZERO
	e.aim = Vector2(0, -1)
	e.ai.state = "windup"
	e.action = "windup"
	fv.sync(1.0 / 60.0)
	seen.append(fv.facing)
	var acts: Dictionary = w.room.tileset.foes.species.wild_boarlet.actions
	Game.combat._damage_enemy(e, e.pools.max_hp * 10.0, c.id, "physical", "none", false, {})
	fv.sync(0.1)
	fv.sync(2.0)
	var last: Array = acts.death.frames.n.back()
	t.check(seen == ["w*", "ne", "s", "sw*", "n"] and is_equal_approx(west_y, float(acts.walk.frames.e[0][1])) and not e.alive and fv.src.position == Vector2(float(last[0]), float(last[1])),
		"topdown: a foe faces where it walks and where it aims (%s; SW, W and NW mirror SE, E and NE), and its death holds its last frame" % str(seen))
	# Decision 43: an elite takes its species' elite sheet (larger, darker, in a ring of Qi), loaded only for an elite.
	var el: EnemyState = Game.enemies.spawn_at("wild_boarlet", base + Vector2(-80, 0), 1, {"elite": true})
	el.altitude = w.room.height_at(el.plane)
	frames(1)
	var ev = w.foe_views.get(el.uid)
	var sp: Dictionary = w.room.tileset.foes.species.wild_boarlet
	t.check(ev != null and ev.acts == sp.elite.actions and fv.acts == sp.actions and ev.tex != null and ev.tex != fv.tex
		and ev.tex.resource_path == str(sp.elite.atlas) and ev.cell.y > fv.cell.y and ev.shadow_rx > fv.shadow_rx,
		"topdown: an elite foe draws its species' elite sheet, in its larger cell, its shadow wider (%s)" % str(ev.shadow_rx if ev != null else -1.0))

## A blow lands in each of the eight directions it is aimed, and only there.
func _eight_ways(base: Vector2) -> void:
	var landed := 0
	for i in 8:
		fresh(base)
		var dir := Vector2.from_angle(i * PI / 4.0)
		var e := foe("mudshell_crab", base + dir * 34.0)
		var behind := foe("mudshell_crab", base - dir * 34.0)
		var r: Dictionary = w.player.aim_attack(dir)
		frames(30)
		if r.get("ok", false) and hurt(e) and not hurt(behind) and (w.player.motor.dir as Vector2).dot(dir) > 0.99: landed += 1
	measured.hit_dirs = landed
	t.check(landed == 8, "topdown: an aimed blow lands in all eight directions and not behind (%d of 8), the body turned to it" % landed)
	# A tap soft-locks the nearest foe in the cone round the facing.
	fresh(base)
	w.player.motor.dir = Vector2.RIGHT
	var near := foe("mudshell_crab", base + Vector2(40, 30))
	var off := foe("mudshell_crab", base + Vector2(-60, 0))
	w.player.attack()
	var aim: Vector2 = Game.combat.timeline(c.id).aim
	frames(30)
	t.check(aim.is_equal_approx((near.plane - base).normalized()) and hurt(near) and not hurt(off), "topdown: a tap turns to the nearest foe in the cone (%s) and strikes it" % str(aim))

## Heights (decision 29 and the plan's §2.2): a swing does not reach a foe a level up; a jump strike does; a foe does
## not reach down a level either.
func _heights() -> void:
	var at := Vector2(25.5 * 32.0, 12.45 * 32.0)
	fresh(at)
	var up := foe("mudshell_crab", Vector2(25.5 * 32.0, 11.5 * 32.0))
	w.player.aim_attack(Vector2.UP)
	frames(30)
	var ground_miss := not hurt(up)
	fresh(at)
	up = foe("mudshell_crab", Vector2(25.5 * 32.0, 11.5 * 32.0))
	w.player.jump()
	var tries := 0
	while w.player.motor.z < 22.0 and tries < 30:
		frames(1)
		tries += 1
	var r: Dictionary = w.player.aim_attack(Vector2.UP)
	frames(20)
	var air_hit: bool = r.get("air", false) and hurt(up)
	fresh(at)
	var above := foe("wild_boarlet", Vector2(25.5 * 32.0, 11.5 * 32.0), 60)
	above.aim = Vector2.DOWN
	Game.combat.enemy_strike(above, above.def.attacks[0])
	var from_above := _struck_by(above)
	var beside := foe("wild_boarlet", at + Vector2(30, 0), 60)
	beside.aim = Vector2.LEFT
	Game.combat.enemy_strike(beside, beside.def.attacks[0])
	var from_beside := _struck_by(beside)
	GameEvents.flush()
	t.check(ground_miss and air_hit and not from_above and from_beside,
		"topdown: a swing misses a foe a level up, a jump strike hits it, and a foe strikes only on its own level (from above %s, beside %s)" % [str(from_above), str(from_beside)])

## Did `e`'s strike reach the player (landed, missed on the roll, dodged or parried: its hit test passed)?
func _struck_by(e: EnemyState) -> bool:
	for q in GameEvents._queue:
		if str(q[0]) in ["hit_landed", "hit_missed", "hit_dodged", "parried"] and str((q[1] as Dictionary).get("attacker", "")) == str(e.uid): return true
	return false

## Shots fly along the ground plane at the thrower's feet: they strike along the aim, and a face a level up stops them.
func _shots(base: Vector2) -> void:
	fresh(base)
	var dir := Vector2(0.6, 0.8)
	var e := foe("wild_boarlet", base + dir * 110.0)
	var aside := foe("wild_boarlet", base + Vector2(-0.6, 0.8) * 110.0)
	var r: Dictionary = w.player.aim_technique(3, dir)
	var turned := false
	for i in 60:
		frames(1)
		for p in Game.room_rt.projectiles: turned = turned or (p.has("aim") and (p.aim as Vector2).dot(dir) > 0.99)
	t.check(r.get("ok", false) and turned and hurt(e) and not hurt(aside), "topdown: a shot flies along its aim on the plane and strikes there (%s)" % str(r.get("reason", "")))
	fresh(Vector2(30.5 * 32.0, 13.5 * 32.0))
	var ledge := foe("wild_boarlet", Vector2(30.5 * 32.0, 9.5 * 32.0), 60)
	w.player.aim_technique(3, Vector2.UP)
	frames(60)
	t.check(not hurt(ledge) and Game.room_rt.projectiles.is_empty(), "topdown: a shot from the square stops at the terrace's face, the foe on it untouched")
	# A technique's circle lands at its point: the foe there, not the one beside the caster.
	fresh(base)
	var there := foe("wild_boarlet", base + Vector2(100, 0))
	var here := foe("wild_boarlet", base + Vector2(-26, 0))
	var rp: Dictionary = w.player.aim_technique(2, Vector2.RIGHT, 0.5)
	frames(40)
	t.check(rp.get("ok", false) and hurt(there) and not hurt(here) and Game.combat.timeline(c.id).at.distance_to(base + Vector2(100, 0)) < 1.0,
		"topdown: a burst aimed half its reach lands its circle there (%s)" % str(rp.get("reason", "")))

## A knockback drives a foe away along the plane; the dodge's i-frames slip a blow; hit-stop holds the fight.
func _push_and_dodge(base: Vector2) -> void:
	fresh(base)
	var e := foe("wild_boarlet", base + Vector2(20, 20), 60)
	var from := e.plane
	Game.combat._player_hits_enemy(c, Game.combat.player_view(c), e, {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1, 1], "knockback": 60, "never_miss": true, "source": "test"}, 1)
	var stop := Game.combat.hitstop
	var held: bool = Game.combat.hold_for_hitstop(1.0 / 60.0)
	for i in 8: Game.enemies.tick(1.0 / 60.0)
	var moved := e.plane - from
	measured.knockback = moved.length()
	t.check(stop > 0.0 and held and moved.length() > 30.0 and moved.normalized().dot(Vector2(1, 1).normalized()) > 0.95,
		"topdown: a blow's hit-stop holds the fight (%.2f s) and its knockback drives the foe away on the plane (%.0f units along %s)" % [stop, moved.length(), str(moved.normalized())])
	fresh(base)
	var striker := foe("wild_boarlet", base + Vector2(30, 0), 60)
	striker.aim = Vector2.LEFT
	w.player.dodge()
	var dashed: bool = w.player._dash
	frames(1)
	var hp0: float = c.pools.hp
	Game.combat.enemy_strike(striker, striker.def.attacks[0])
	var again: Dictionary = Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1, "moves": false})
	t.check(dashed and c.pools.hp == hp0 and str(again.get("reason", "")) == "cooldown" and Game.combat.forced_motion(c.id).is_empty(),
		"topdown: the dodge is Combat's (its i-frames slip the blow, its 2.5 s cooldown holds) and the motor's dash carries it")

## Decision 37's full set in the fight (the bow batch): each family strikes in its own drawn pose (the heavy sabre
## two-handed, the bow's draw, the bell's toll on its first steps, the flute at the lips, the brush writing its third,
## the fan thrown), a blow in the air plays the air strike, a dash attack the dash slash (a thrust family its lunging
## thrust), a parried blow the parry's deflection, the finisher armed on Attack the charge's held wind-up, the flute's
## held melody loops its note's frames, and a staged scene holds the body in a story gesture; nothing is a stand-in.
func _figure_moves(base: Vector2) -> void:
	var p = w.player
	fresh(base)
	var play := func(fam: String, action: String, air := false, step := {}) -> String:
		var tl: Dictionary = Game.combat.timeline(c.id)
		tl.action = action
		tl.family = fam
		tl.technique = ""
		tl.combo = 0
		tl.t = 0.05
		tl.duration = 0.6
		tl.hit_at = 0.3
		tl.air_attack = air
		tl.step = step
		p.sync(0.0)
		var got := str(p.pose)
		Game.combat.actors.erase(c.id)
		return got
	var own := [play.call("heavy_sabre", "swing_1"), play.call("heavy_sabre", "swing_3"), play.call("bow", "bow"),
		play.call("bell", "swing_1"), play.call("bell", "swing_3"), play.call("flute", "attack"), play.call("brush", "swing_3"),
		play.call("fan", "swing_3", false, {"throw": {"speed": 520}}), play.call("jian", "swing_1")]
	var air := [play.call("jian", "swing_2", true), play.call("bow", "bow", true)]
	p.dash_attack = true
	p.dash_combo = 0
	var dash := [play.call("jian", "swing_1"), play.call("fists", "punch_1"), play.call("spear", "thrust_1")]
	p.dash_attack = false
	p.dash_combo = -1
	t.check(own == ["two_hand_swing_1", "two_hand_swing_3", "bow_draw", "bell_toll", "swing_3", "flute_play", "brush_write", "fan_throw", "swing_1"]
		and air == ["air_strike", "bow_draw"] and dash == ["dash_slash", "dash_slash", "thrust_3"],
		"topdown figure: each family strikes in its own drawn pose, in the air the air strike, out of a dash the dash slash or a lunging thrust (%s, %s, %s)" % [str(own), str(air), str(dash)])
	# The parry, the armed finisher, the held melody, a staged gesture.
	fresh(base)
	p.parried()
	p.sync(0.0)
	var parry := [str(p.pose), p.parry_t > 0.0]
	frames(30)
	p.sync(0.0)
	parry.append(str(p.pose))
	p.aim = {"move": "finisher"}
	p.sync(0.0)
	var charge := str(p.pose)
	p.aim = {}
	Game.combat.melody[c.id] = {"next": 9.0}
	var loop := CombatFeel.melody_loop()
	var melody := {}
	for i in 12:
		p.sync(0.05)
		melody[p.frame] = str(p.pose)
	Game.combat.melody.erase(c.id)
	var in_loop := melody.keys().all(func(k): return int(k) >= int(loop[0]) and int(k) <= int(loop[1])) and melody.size() == int(loop[1]) - int(loop[0]) + 1 \
		and melody.values().all(func(v): return v == "flute_play")
	p.stage_pose = "salute"
	p.sync(0.0)
	p.sync(2.0)
	var gesture := [str(p.pose), p.frame]
	p.stage_pose = ""
	p.sync(0.0)
	t.check(parry == ["parry_deflect", true, "idle"] and charge == "charge_hold" and in_loop and gesture == ["salute", 2] and str(p.pose) == "idle"
		and (TopdownFigure.manifest().get("stand_ins", []) as Array).is_empty(),
		"topdown figure: a parry deflects then settles, the armed finisher holds the charge, the melody loops its note, a staged salute holds (%s, %s, %s, %s)" % [str(parry), charge, str(melody), str(gesture)])

## Phase 3 (decision 32): the body is the real character. Its figure wears the character's look and gear from the save
## and dresses again when the gear changes; each state plays its drawn action in the body's facing: a blow its family's
## own pose with the hit frame on the hit, a technique without a pose the hand-seal cast, a back-step the dodge, the
## wounded body the knock-down; every facing row draws, the west three as mirrors of the east.
func _figure(base: Vector2) -> void:
	fresh(base)
	var p = w.player
	var fig: TopdownFigure = p.figure
	var want: Dictionary = InventoryAuthority.outfit_for(c)
	var worn := {}
	for l in fig.layers: worn[str(l.cat)] = str(l.item)
	var dressed := true
	for cat in ["body", "hair", "shirt", "pants", "shoes"]:
		var item := str(want.get(cat, "none"))
		dressed = dressed and (worn.get(cat, "") == item or fig.missing.has("%s:%s" % [cat, item]))
	t.check(fig.outfit == want and dressed and worn.get("body", "") == "light" and worn.get("hair", "") == str(want.hair),
		"topdown figure: the body wears the character's look and gear from the save (%s; not drawn yet %s)" % [str(worn), str(fig.missing)])
	Game.inventory.apply_add(c.id, "training_jian", 1, "topdown_suite")
	Game.submit({"type": "equip", "index": c.inventory.first_index("training_jian")})
	var armed := fig.layers.filter(func(l): return l.cat == "weapon").map(func(l): return str(l.item))
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	p.refresh_outfit()
	t.check(not armed.is_empty() and armed.all(func(n): return n == "sword") and fig.layers.all(func(l): return l.cat != "weapon"),
		"topdown figure: equipping the training jian dresses the figure in the jian's layers at once, and bare hands again without it (%s)" % str(armed))
	# The states and their actions (from rest: the last suite's dodge has run out).
	var seen := {}
	p.motor.dash_t = 0.0
	p.motor.vel = Vector2.ZERO
	p.sync(0.0)
	seen.idle = p.pose
	p.movement = Vector2.RIGHT
	frames(12)
	p.sync(0.05)
	seen.walk = [p.pose, p.motor.row]
	p.movement = Vector2.ZERO
	fresh(base)
	p.movement = Vector2(0.5, 0)   # decision 42: a light touch walks, the stick pushed runs
	frames(12)
	p.sync(0.05)
	seen.light = p.pose
	p.movement = Vector2.ZERO
	fresh(base)
	p.aim_attack(Vector2.RIGHT, false)
	var tl: Dictionary = Game.combat.timeline(c.id)
	frames(1)
	p.sync(0.0)
	var early := [p.pose, p.frame]
	while float(tl.t) < float(tl.hit_at) + 0.01 and Game.combat.is_busy(c.id): frames(1)
	p.sync(0.0)
	seen.blow = [early, p.pose, p.frame, str(tl.action)]
	fresh(base)
	var silent: Array = ContentDB.all("techniques").filter(func(e): return e.get("action") == null)
	tl = Game.combat.timeline(c.id)
	tl.action = "swing_3"
	tl.technique = str(silent[0].id) if not silent.is_empty() else ""
	tl.t = 0.05
	tl.duration = 0.6
	tl.hit_at = 0.3
	p.sync(0.0)
	seen.technique = p.pose
	Game.combat.actors.erase(c.id)
	fresh(base)
	p.dodge()
	frames(2)
	p.sync(0.0)
	seen.back_step = p.pose
	fresh(base)
	Game.combat.wounded[c.id] = {"cause": "topdown_suite", "timer": 0.0, "no_penalty": true, "grace": 0.0}
	p.sync(0.0)
	p.sync(1.0)
	seen.wounded = [p.pose, p.frame]
	Game.combat.wounded.erase(c.id)
	fresh(base)
	p.jump()
	frames(3)
	p.sync(0.0)
	seen.jump = [p.pose, p.frame]
	frames(40)
	var drawn := true
	for row in ["s", "se", "e", "ne", "n", "nw", "w", "sw"]:
		var box: Rect2 = fig.bounds("walk", row, 2)
		drawn = drawn and box.size.x >= 10.0 and box.size.y >= 41.0 and box.size.y <= 58.0   # decision 43: 46 px
	var e_box: Rect2 = fig.bounds("idle", "e", 0)
	var w_box: Rect2 = fig.bounds("idle", "w", 0)
	var mirrored: bool = is_equal_approx(w_box.position.x, -e_box.end.x) and w_box.size == e_box.size
	var hit := TopdownFigure.hit_frame(str(seen.blow[1]))
	t.check(seen.idle == "idle" and seen.walk == ["run", "e"] and seen.light == "walk" and seen.blow[1] == seen.blow[3] and seen.blow[3] == "punch_1" and int(seen.blow[0][1]) < hit
		and int(seen.blow[2]) == hit and seen.technique == "cast" and seen.back_step == "dodge" and seen.wounded == ["knockdown", 4]
		and seen.jump[0] == "jump" and int(seen.jump[1]) <= 1 and drawn and mirrored,
		"topdown figure: each state plays its drawn action and every facing draws, the west mirrored (%s, rows drawn %s, mirrored %s)" % [str(seen), str(drawn), str(mirrored)])
	# A villager in the same style (TopdownPlaces.Person): the NPC's own outfit, its rest row, turning in the eight rows,
	# walking, and a meditating one facing the camera from every row.
	var v: TopdownPlaces.Figure = w.add_villager("aunt_ping", base + Vector2(60, 0), "se")
	var person: TopdownPlaces.Person = v.art
	var rest := [person.row, person.action, person.figure.missing.is_empty(), person.figure.outfit.get("shirt", "")]
	person.look(Vector2(-1, -1))
	var turned := person.row
	person.play("walk")
	person._process(0.3)
	var walking := [person.action, TopdownFigure.frame_at(person.action, person.t)]
	var sitter := TopdownPlaces.Person.new({"npc": "aunt_ping", "pose": "meditate", "row": "ne"})
	var faces := TopdownFigure.frame_of(sitter.action, sitter.row, 0) == TopdownFigure.frame_of("meditate", "s", 0)
	sitter.free()
	v.queue_free()
	t.check(rest[0] == "se" and rest[1] == "idle" and rest[2] and str(rest[3]) == str(ContentDB.entry("npcs", "aunt_ping").outfit.get("shirt", ""))
		and turned == "nw" and walking[0] == "walk" and int(walking[1]) > 0 and faces,
		"topdown villager: drawn by the figure in their own outfit, at rest in their row, turning in eight rows, walking, a meditation facing the camera (%s, %s, %s, %s)" % [str(rest), turned, str(walking), str(faces)])

## Foes chase on the grid, give up past the leash, wait beneath a roof they cannot reach, and a jumper hops a level.
func _chase_and_leash(base: Vector2) -> void:
	fresh(base)
	var boar := foe("wild_boarlet", base + Vector2(150, 0), 60)
	boar.ai.timer = 0.0
	boar.threat[c.id] = 1.0
	frames(60)
	var closer := boar.plane.distance_to(w.player.motor.pos)
	t.check(closer < 110.0 and str(boar.ai.state) in ["aggro", "windup", "attack", "recover"], "topdown: a boarlet that noticed the player chases it on the plane (%.0f units off)" % closer)
	fresh(base)
	var far := foe("wild_boarlet", base + Vector2(640, 0), 60)
	far.spawn_point = base
	far.ai.state = "aggro"
	far.ai.timer = 5.0
	w.player.motor.place(far.plane + Vector2(40, 0))
	frames(2)
	t.check(str(far.ai.state) == "return", "topdown: past its 600 leash a foe gives up and goes home (%s)" % str(far.ai.state))
	# On the storehouse roof, out of a ground-bound boarlet's reach: it waits beneath, then goes home healing.
	var sh: Dictionary = w.room.props.filter(func(q): return q.kind == "storehouse")[0]
	var roof := (Vector2(sh.cell) + Vector2(1.5, 1.5)) * 32.0
	fresh(roof)
	var under := foe("wild_boarlet", roof + Vector2(0, 96), 60)
	under.ai.state = "aggro"
	under.ai.timer = 5.0
	under.threat[c.id] = 1.0
	frames(120)
	var waiting := float(under.ai.get("unreach", 0.0)) > 1.0 and under.altitude == 0.0 and str(under.ai.state) == "aggro"
	frames(300)
	t.check(w.player.motor.z == 64.0 and waiting and str(under.ai.state) in ["return", "idle"],
		"topdown: a ground-bound foe waits beneath a roof it cannot reach, then gives up and goes home (%s, waited %s, z %.0f)" % [str(under.ai.state), str(waiting), under.altitude])
	# A jumper (the rat) hops the terrace's edge to reach the player on it.
	fresh(Vector2(30.5 * 32.0, 10.0 * 32.0))
	var rat := foe("reedtail_rat", Vector2(30.5 * 32.0, 13.5 * 32.0), 60)
	rat.ai.state = "aggro"
	rat.ai.timer = 5.0
	rat.threat[c.id] = 1.0
	var hopped := false
	for i in 240:
		frames(1)
		hopped = hopped or not rat.hop.is_empty()
		if rat.altitude >= 32.0 and rat.hop.is_empty(): break
	t.check(hopped and rat.altitude == 32.0, "topdown: a rat (a jumper) hops a level up to the terrace to reach the player (z %.0f)" % rat.altitude)

## A slain foe's loot falls where it died on the plane (a rat on the terrace, far above the side view's walk strip),
## the body picks it up, and a better piece is offered by the equip popup.
func _drops_and_prompt(tree: SceneTree) -> void:
	var spot := Vector2(24.5 * 32.0, 7.5 * 32.0)
	fresh(spot + Vector2(0, 90))
	var dropped: Array = []
	for i in 6:
		var rat := foe("reedtail_rat", spot)
		Game.combat._damage_enemy(rat, rat.pools.max_hp * 10.0, c.id, "physical", "none", false, {})
		Game.tick(1.0 / 60.0)
		dropped = Game.room_rt.loot.duplicate()
		if not dropped.is_empty(): break
	var where_ok := not dropped.is_empty() and dropped.all(func(l): return absf(float(l.y) - spot.y) < 10.0 and float(l.alt) == 32.0)
	t.check(where_ok and w.loot_layer.get_child_count() >= dropped.size(), "topdown: a rat's loot falls where it died on the terrace (%d drops at y %s)" % [dropped.size(), str(dropped.map(func(l): return int(l.y)))])
	hud = load("res://scripts/hud.gd").new()
	hud.player = w.player
	hud.world = w
	tree.root.add_child(hud)
	await tree.process_frame
	fresh(spot)
	Game.world._drop_loot(c, {"items": [], "coins": 0, "equipment": [{"level": 1, "min_quality": "fine"}]}, spot + Vector2(10, 0), 32.0, "enemy")
	var uid := -1
	for l in Game.room_rt.loot: uid = int((l.instance as Dictionary).get("uid", -1))
	frames(40)
	t.check(Game.room_rt.loot.is_empty() and (hud.equip_prompt.queue.has(uid) or int(hud.equip_prompt.current.get("uid", -2)) == uid),
		"topdown: the body picks up a dropped piece and the equip popup offers it (loot left %d, uid %d, queue %s, current %s)" % [Game.room_rt.loot.size(), uid, str(hud.equip_prompt.queue), str(hud.equip_prompt.current.get("uid", -1))])

## The HUD drives it (decision 30): Attack held and dragged aims (the arrow shows, it snaps to a foe near the line) and
## strikes that way on release; a technique shows its form; back on the button cancels; the fight ring comes out.
func _hud_aim(tree: SceneTree, base: Vector2) -> void:
	fresh(base)
	hud.set_state(true)
	var foe_near := foe("wild_boarlet", base + Vector2.from_angle(deg_to_rad(-8.0)) * 60.0)
	var foe_wide := foe("wild_boarlet", base + Vector2.from_angle(deg_to_rad(90.0)) * 60.0)
	var ac: Vector2 = hud.attack_center
	hud.press(7, ac)
	hud.drag(7, ac + Vector2(90, 0))
	hud._tick_aims(0.2)
	var shown: Dictionary = w.player.aim.duplicate()
	hud.release(7)
	var snapped: Vector2 = Game.combat.timeline(c.id).aim
	frames(30)
	t.check(str(shown.get("kind", "")) == "attack" and shown.get("target") == foe_near and snapped.is_equal_approx((foe_near.plane - base).normalized()) and hurt(foe_near) and not hurt(foe_wide) and w.player.aim.is_empty(),
		"topdown: Attack held and dragged right aims, snaps to the foe 8° off the line, and strikes it on release (%s, %s, aim %s, hurt %s/%s)" % [str(shown.get("kind", "")), str(shown.get("target") == foe_near), str(snapped), str(hurt(foe_near)), str(hurt(foe_wide))])
	fresh(base)
	hud.set_state(true)
	foe("wild_boarlet", base + Vector2(0, 60), 60)
	hud.press(8, ac)
	hud.drag(8, ac + Vector2(0, -90))
	hud._tick_aims(0.2)
	hud.release(8)
	var up_aim: Vector2 = Game.combat.timeline(c.id).aim
	t.check(up_aim.is_equal_approx(Vector2.UP), "topdown: with no foe near the line, the blow goes exactly where it was dragged (%s)" % str(up_aim))
	var forms: Array = []
	for s in 4:
		var sc: Vector2 = hud.slots[s]
		hud.press(20 + s, sc)
		hud.drag(20 + s, sc + Vector2(-80, 0))
		hud._tick_aims(0.2)
		forms.append(str(w.player.aim.get("form", "")))
		hud.drag(20 + s, sc)
		var cd: int = c.pools.cooldowns.size()
		hud.release(20 + s)
		if c.pools.cooldowns.size() != cd: forms.append("cast!")
	t.check(forms == ["cone", "line", "point", "line"], "topdown: each technique shows its form while aimed, and dragged back onto its button it cancels (%s)" % str(forms))
	hud.set_state(false)
	fresh(base)
	hud.fight_override = null
	hud._settled = false
	hud._tick_fight(0.1)
	var rest: bool = hud.fight
	foe("wild_boarlet", base + Vector2(200, 0), 60)
	hud._tick_fight(0.1)
	t.check(not rest and hud.fight, "topdown: the HUD's rest and fight ring follows the room's foes")

# ------------------------------------------------------------------ decision 35: Attack's drag moves in the fight
## Through the HUD, in the prototype room: a long drag strikes the combo's finisher at once (mid-chain it comes next, in
## place of the steps between); a drag down in the air plunges and lands with its strike; held still, Attack guards
## (the parry window, then the family's damage cut) or enters a slotted stance; each shows on the button and the ground;
## the poses fall back to the stand-in cells while the sheet has none; left-handed and Reduce motion work the same.
func _drag_moves(tree: SceneTree, base: Vector2) -> void:
	var ac: Vector2 = hud.attack_center
	var fam := StatRules.family(c)
	var last: int = (fam.combo as Array).size() - 1
	var tl: Dictionary
	# The finisher: a long drag up-left strikes the chain's last step at once, the ground's arrow gold while armed.
	fresh(base)
	hud.set_state(true)
	var ahead := foe("wild_boarlet", base + Vector2(-1, -1).normalized() * 40.0)
	hud.press(30, ac)
	hud.drag(30, ac + Vector2(-95, -95))
	hud._tick_aims(0.1)
	var armed_as: String = hud.armed(hud.attack_gesture())
	var shown := str(w.player.aim.get("move", ""))
	await tree.process_frame   # the button draws its lit line and the word
	hud.release(30)
	tl = Game.combat.timeline(c.id)
	var step := [int(tl.combo), str(tl.action)]
	frames(50)
	t.check(armed_as == "finisher" and shown == "finisher" and step == [last, str(fam.combo[last].action)] and hurt(ahead),
		"topdown drag moves: a long drag strikes the combo's finisher at once along it (%s, %s, step %s, hurt %s)" % [armed_as, shown, str(step), str(hurt(ahead))])
	# Mid-chain: a tap starts the first step; a long drag while it plays brings the finisher next, skipping the middle.
	fresh(base)
	hud.set_state(true)
	foe("wild_boarlet", base + Vector2(0, -40))
	hud.press(31, ac)
	hud.release(31)
	frames(3)
	hud.press(32, ac)
	hud.drag(32, ac + Vector2(0, -130))
	hud._tick_aims(0.05)
	hud.release(32)
	var seen: Array = []
	for i in 120:
		tl = Game.combat.timeline(c.id)
		if str(tl.action) != "" and (seen.is_empty() or seen.back() != int(tl.combo)): seen.append(int(tl.combo))
		frames(1)
	t.check(seen == [0, last], "topdown drag moves: a finisher asked for mid-chain comes after the step under way, in place of the ones between (%s)" % str(seen))
	# The Plunge: in the air a drag down drops the body; the landing strikes and stuns round it, the art's cooldown holds.
	var had: bool = c.cultivator.secret_arts.has("plunge")
	if not had: c.cultivator.secret_arts.append("plunge")
	fresh(base)
	hud.set_state(true)
	var below := foe("wild_boarlet", base + Vector2(24, 0))
	below.pools.max_hp = 1.0e15   # it lives through the strike whatever the character's level, so its stun shows
	below.pools.hp = below.pools.max_hp
	w.player.jump()
	frames(8)
	var z0: float = w.player.motor.z
	var ready: bool = w.player.plunge_ready()
	hud.press(40, ac)
	hud.drag(40, ac + Vector2(0, 70))
	hud._tick_aims(0.05)
	armed_as = hud.armed(hud.attack_gesture())
	shown = str(w.player.aim.get("move", ""))
	await tree.process_frame
	hud.release(40)
	var dropping: bool = w.player.motor.plunging
	frames(1)
	w.player.sync(0.0)
	var drop_pose := [str(w.player.anim), str(w.player.pose), int(w.player.frame)]
	var n := 0
	while not w.player.motor.grounded and n < 30:
		frames(1)
		n += 1
	frames(1)
	w.player.sync(0.0)
	var land_pose := [str(w.player.anim), str(w.player.pose), int(w.player.frame)]
	var hit := TopdownFigure.hit_frame("plunge")
	var poses_ok: bool = drop_pose[0] == "plunge" and drop_pose[1] == "plunge" and int(drop_pose[2]) < hit and land_pose == ["plunge_land", "plunge", hit]
	measured.plunge = {"from": snappedf(z0, 0.1), "frames": n}
	t.check(ready and armed_as == "plunge" and shown == "plunge" and dropping and hurt(below) and below.pools.has_status("stun") and c.pools.cooldown("plunge") > 3.0 and poses_ok,
		"topdown drag moves: a drag down in the air plunges from z %.0f, lands in %d frames and strikes and stuns the foe beside it; the figure dives in the plunge and holds its impact frame (%s, %s; ready %s, %s/%s, dropped %s, hurt %s, stun %s, cooldown %.1f)" % [z0, n, str(drop_pose), str(land_pose),
			str(ready), armed_as, shown, str(dropping), str(hurt(below)), str(below.pools.has_status("stun")), c.pools.cooldown("plunge")])
	# Without the art (or on its cooldown) a drag down in the air stays an aimed air blow.
	c.cultivator.secret_arts.erase("plunge")
	fresh(base)
	hud.set_state(true)
	w.player.jump()
	frames(8)
	hud.press(41, ac)
	hud.drag(41, ac + Vector2(0, 70))
	hud._tick_aims(0.05)
	armed_as = hud.armed(hud.attack_gesture())
	hud.release(41)
	tl = Game.combat.timeline(c.id)
	t.check(armed_as == "aim" and not w.player.motor.plunging and bool(tl.get("air_attack", false)) and (tl.aim as Vector2).is_equal_approx(Vector2.DOWN),
		"topdown drag moves: without the Plunge art a drag down in the air is an aimed air blow (%s)" % armed_as)
	if had: c.cultivator.secret_arts.append("plunge")
	# The guard: held still, Attack guards; a blow in the parry window is parried, a later one is cut by the family's
	# guard; letting go ends the guard and strikes nothing.
	fresh(base)
	hud.set_state(true)
	w.player.motor.face(Vector2.RIGHT)
	frames(1)
	var striker := foe("wild_boarlet", base + Vector2(30, 0), maxi(1, ProgressionRules.level(c)))   # blows that matter at any level
	striker.aim = Vector2.LEFT
	hud.press(50, ac)
	hud._tick_aims(0.2)
	var not_yet: bool = Game.combat.timeline(c.id).guard
	hud._tick_aims(0.15)
	var g: AimGesture = hud.attack_gesture()
	tl = Game.combat.timeline(c.id)
	var guarding: bool = g != null and g.guarding and g.guard_kind == "guard" and tl.guard and str(w.player.aim.get("move", "")) == "guard"
	await tree.process_frame
	var hp0: float = c.pools.hp
	Game.combat.enemy_strike(striker, striker.def.attacks[0])
	var parried: bool = c.pools.hp == hp0 and str(striker.ai.state) == "stagger"
	# The mean of the blows that land, with no crits, so an evaded blow or a lucky one cannot tip it.
	striker.stats.crit_chance = 0.0
	var blows := func(times: int) -> float:
		var lost := 0.0
		var landed := 0
		for i in times:
			c.pools.hp = c.pools.max_hp
			Game.combat.wounded.erase(c.id)
			c.pools.invulnerable = 0.0
			Game.combat.timeline(c.id).dodge_t = 0.0
			Game.combat.timeline(c.id).guard_t = 1.0
			Game.combat.enemy_strike(striker, striker.def.attacks[0])
			if c.pools.hp < c.pools.max_hp:
				lost += c.pools.max_hp - c.pools.hp
				landed += 1
		return lost / maxf(1.0, float(landed))
	var guarded: float = blows.call(8)
	hud.release(50)
	tl = Game.combat.timeline(c.id)
	var ended: bool = not tl.guard and str(tl.action) == ""
	var open: float = blows.call(8)
	measured.guard = {"guarded": snappedf(guarded, 0.1), "open": snappedf(open, 0.1), "ratio": snappedf(guarded / maxf(1.0, open), 0.01)}
	t.check(not not_yet and guarding and parried and ended and open > 0.0 and guarded < open * 0.9,
		"topdown drag moves: Attack held still guards at 0.3 s, parries a blow in the window, cuts later ones (%.0f a landed blow against %.0f open), and let go it ends and strikes nothing" % [guarded, open])
	# The stance: with a counter-stance slotted and ready, the hold enters it (the technique's cooldown, its stance).
	fresh(base)
	hud.set_state(true)
	var tid := "silkworm_riposte"
	var kept = c.cultivator.technique_slots[3]
	if not c.cultivator.techniques_known.has(tid): Game.apply_effects(c.id, [{"kind": "learn_technique", "technique": tid}], "topdown_suite")
	var eq: Dictionary = Game.submit({"type": "equip_technique", "slot": 3, "id": tid})
	hud.press(51, ac)
	hud._tick_aims(0.35)
	g = hud.attack_gesture()
	var kind := g.guard_kind if g != null else ""
	frames(20)
	tl = Game.combat.timeline(c.id)
	var in_stance: bool = float(tl.stance) > 0.0 and tl.guard and c.pools.cooldown("tech:" + tid) > 0.0
	hud.release(51)
	var out: bool = not Game.combat.timeline(c.id).guard
	Game.submit({"type": "equip_technique", "slot": 3, "id": str(kept)})
	t.check(eq.get("ok", false) and kind == "stance" and in_stance and out,
		"topdown drag moves: with a counter-stance slotted the hold enters it (%s, %s)" % [kind, str(eq.get("reason", ""))])
	# The guard pose: the figure's own guard (2 frames, held), drawn in its facing, and idle again once it ends.
	fresh(base)
	Game.submit({"type": "guard_start"})
	w.player.sync(0.0)
	w.player.sync(0.3)
	var drawn := [str(w.player.pose), int(w.player.frame)]
	var guard_box: Rect2 = w.player.figure.bounds("guard", w.player.motor.row, int(w.player.frame))
	Game.submit({"type": "guard_end"})
	w.player.sync(0.0)
	var after := [str(w.player.pose), int(w.player.frame)]
	t.check(drawn == ["guard", 1] and guard_box.size.y > 30.0 and after == ["idle", 0],
		"topdown drag moves: the guard draws the figure's guard pose while held and idle once let go (%s, %s, %s)" % [str(drawn), str(guard_box), str(after)])
	# Left-handed: the button moves to the left; a drag to the left edge is the finisher, back on the button cancels.
	hud.left_handed = true
	hud._layout()
	var lc: Vector2 = hud.attack_center
	fresh(base)
	hud.set_state(true)
	hud.press(60, lc)
	hud.drag(60, lc + Vector2(-70, 0))
	hud._tick_aims(0.05)
	var left_armed: String = hud.armed(hud.attack_gesture())
	hud.drag(60, lc + Vector2(5, 0))
	var cancel: String = hud.armed(hud.attack_gesture())
	hud.release(60)
	var idle: bool = str(Game.combat.timeline(c.id).action) == ""
	hud.left_handed = false
	hud._layout()
	# Reduce motion: the armed marks hold still (no pulse), and the button still draws them.
	var was: bool = bool(Game.account.settings.get("reduce_motion", false))
	Game.account.settings["reduce_motion"] = true
	hud.press(61, ac)
	hud.drag(61, ac + Vector2(-95, -95))
	hud._tick_aims(0.05)
	var g1: float = hud.armed_glow()
	hud.t += 0.37
	var g2: float = hud.armed_glow()
	await tree.process_frame
	hud.drag(61, ac)
	hud.release(61)
	Game.account.settings["reduce_motion"] = was
	t.check(lc.x < 640.0 and left_armed == "finisher" and cancel == "cancel" and idle and g1 == 1.0 and g2 == 1.0,
		"topdown drag moves: left-handed the finisher reads the same and a drag back cancels (%s, %s); under Reduce motion the armed marks hold still" % [left_armed, cancel])


# ------------------------------------------------------------------ Phase 4, third part: the gaps closed
## What the camera shows (the room as drawn, a ridge on its north edge included, the body always in view) and the rules
## that ask it (a foe's respawn out of view, on both axes); flat marks on a raised floor; things put on a floor; the
## ways' reach turned with their direction; the minimap's direction mark on the plane.
func _view_rules() -> void:
	var rows := flat(60, 40)
	rows[0] = "2".repeat(60)
	rows[1] = "2".repeat(60)
	var room := grid(rows)
	var drawn := room.drawn_rect()
	t.check(drawn.position.y == -32.0 and drawn.end == Vector2(960, 640), "topdown view: a ridge on the room's first rows draws 32 px over its top, and the camera may show it (%s)" % str(drawn))
	var ridge := Vector2(30.5, 0.5) * 32.0
	var feet := TopdownWorld.to_screen(ridge, 64.0)
	var shown := Rect2(room.camera_for(ridge, 64.0) - TopdownRoom.VIEW * 0.5, TopdownRoom.VIEW)
	t.check(shown.has_point(feet) and shown.has_point(feet - Vector2(0, 46)),
		"topdown view: standing on the ridge at the room's very top the camera keeps the whole body in view (feet %s, view %s)" % [str(feet), str(shown)])
	var mid := Vector2(30.0, 20.0) * 32.0
	var small := grid(flat(10, 8))
	t.check(room.camera_for(mid, 0.0) == TopdownWorld.to_screen(mid, 0.0) + Vector2(0, -14) and small.camera_for(Vector2(40, 40), 0.0) == Vector2(80, 64),
		"topdown view: mid-room the camera frames the feet 14 px low (the 46 px body's middle); a room smaller than the view is centred")
	# Out of view (a foe's respawn): the camera's rect on both axes, not the distance across alone.
	var rt := RoomRuntime.new()
	rt.topdown = room
	var side := RoomRuntime.new()
	var st := ActorState.new()
	st.plane = mid
	var south := mid + Vector2(0, 560)
	t.check(rt.out_of_view(south, 0.0, st, 60.0) and not side.out_of_view(south, 0.0, st, 60.0) and not rt.out_of_view(mid + Vector2(300, 150), 0.0, st, 60.0)
		and rt.out_of_view(mid + Vector2(760, 0), 0.0, st, 60.0),
		"topdown view: a spot 17 tiles straight south is out of the camera's view (the side view's rule, across only, saw it), one 10 tiles off is in it, one 24 across is out")
	# Flat marks: on a terrace over its row and under the bodies on it (the old rule put a decal 12 px up, under the row).
	var terrace := grid(["1111", "1111", "1111", "0000", "0000", "0000"])
	var on := Vector2(1.5, 1.5) * 32.0
	var mark := terrace.decal_key(on, 32.0, 12.0)
	var low := Vector2(1.5, 4.5) * 32.0
	t.check(mark > 32.0 and mark < terrace.sort_key(on, 32.0) and terrace.sort_key(on, 32.0) - 12.0 < 32.0 and terrace.decal_key(low, 0.0, 12.0) < terrace.sort_key(low + Vector2(0, -6), 0.0),
		"topdown sort: a mark flat on a terrace sorts over the terrace's row (%.3f > 32) and under a body on it (%.3f); on the ground under a body standing in it" % [mark, terrace.sort_key(on, 32.0)])
	# Things put in the room land on a floor: in the water on the bank beside it, asked for on a level on that level.
	var shore := grid(["0000~~~~0000", "0000~~~~0000", "0000~~~~0000", "111111111111"])
	var wet := Vector2(5.5, 1.5) * 32.0
	var put := shore.place_near(wet, 0.0)
	var up := shore.place_near(Vector2(1.5, 2.5) * 32.0, 32.0)
	t.check(shore.standable(TopdownRoom.cell_of(put)) and shore.floor_at(put) == 0.0 and put.distance_to(wet) <= 64.0 and TopdownRoom.cell_of(up).y == 3,
		"topdown place: a thing put in the water lands on the bank beside it (%s), one asked for a level up lands on that level (%s)" % [str(put), str(up)])
	# A way's reach turns with its direction: along its edge or doorway, a tile across.
	var ways := TopdownRoom.from_dict({"id": "case", "levels": flat(20, 12), "spawn": [1, 1],
		"portals": {"east": {"at": [19, 6], "dir": "e", "span": 3}, "hall": {"at": [8, 4], "dir": "n", "span": 2}}}, {})
	var reach := {}
	for p in ways.merge_def({"portals": [{"id": "east", "type": "edge"}, {"id": "hall", "type": "door"}]}).portals: reach[str(p.id)] = p.reach
	t.check(reach.get("east") == [32.0, 48.0] and reach.get("hall") == [32.0, 32.0],
		"topdown ways: an east edge reaches a tile across and half its three tiles along; a door's two tiles likewise (%s)" % str(reach))
	# The minimap's direction mark: toward a way that lies south it points south, from the frame's bottom edge.
	var hud_script = load("res://scripts/hud.gd")
	var way: Vector2 = hud_script.minimap_way(Vector2(10, 10), Vector2(10, 40))
	var edge: Vector2 = hud_script._edge_point(Rect2(0, 0, 100, 50), Vector2(50, 25), way)
	t.check(way == Vector2(0, 1) and edge == Vector2(50, 50), "topdown minimap: the direction mark points south to a way south, on the frame's bottom edge (%s at %s)" % [str(way), str(edge)])

## The companion of the character in the room (spawned again after `fresh` clears the room).
func _ally() -> EnemyState:
	Game.companions._spawn_all(c)
	return Game.room_rt.enemies.get(int(Game.companions.allies.get("lan_yue", -1)))

## A companion on the grid (AllyBrain steering by TopdownBrain): it comes in on the player's floor, follows onto the
## terrace by the grid's way (the stairs, or a hop a level up as the player jumps), blinks to a landing stage there is
## no way onto on foot, strikes only a foe on its own height and is struck only on its own height. Its figure is the
## stand-in (the side view's own avatar at half size), sorted with the room and standing on its floor; a spirit animal
## and a foe the sheet does not draw get theirs too.
func _allies_on_the_grid(tree: SceneTree, base: Vector2) -> void:
	fresh(base)
	var had: Array = c.companions.active.duplicate()
	if not c.companions.roster.has("lan_yue"): c.companions.roster.append("lan_yue")
	c.companions.active = ["lan_yue"]
	var a := _ally()
	if a == null:
		t.check(false, "topdown allies: a companion to follow (%s)" % str(Game.companions.allies))
		return
	frames(1)
	await tree.process_frame
	var fv = w.foe_views.get(a.uid)
	var standing: bool = fv != null and fv.art is TopdownPlaces.Person and not fv.art.shadow and fv.position.y == w.room.sort_key(a.plane, a.altitude) \
		and fv.position.y + fv.art.position.y == TopdownWorld.to_screen(a.plane, a.altitude).round().y
	t.check(is_equal_approx(a.altitude, w.room.floor_at(a.plane)) and w.room.free_at(a.plane, a.altitude, 8.0) and standing and w.label_views.has(a.uid),
		"topdown allies: a companion comes in on a free spot of the player's floor, drawn in the top-down style in its outfit, sorted at its key, on its floor, with its label")
	# Onto the terrace: the player goes up, the companion follows by the grid's way (no blink).
	var up := Vector2(26.5, 9.5) * 32.0
	w.player.motor.place(up)
	w.player.physics_step(0.0001)
	var hopped := false
	var stairs := false
	var blinked := false
	var stride := 0.0
	var was := a.plane
	for i in 420:
		frames(1)
		hopped = hopped or not a.hop.is_empty()
		stairs = stairs or not w.room.stair_at(TopdownRoom.cell_of(a.plane).x, TopdownRoom.cell_of(a.plane).y).is_empty()
		blinked = blinked or float(a.ai.get("blink_t", 0.0)) > 0.0
		stride = maxf(stride, a.plane.distance_to(was))
		was = a.plane
		if a.altitude == 32.0 and a.hop.is_empty() and a.plane.distance_to(up) < 140.0: break
	t.check(a.altitude == 32.0 and a.plane.distance_to(up) < 140.0 and (hopped or stairs) and not blinked and stride < 12.0,
		"topdown allies: the companion follows the player up onto the terrace by the grid's way (hop %s, stairs %s, no blink, longest step %.1f, z %.0f)" % [str(hopped), str(stairs), stride, a.altitude])
	# Onto the far landing stage (a long jump over the water): no way on foot, so it blinks there after 2 s, on its floor.
	fresh(Vector2(22.5, 21.5) * 32.0)
	a = _ally()
	var stage := Vector2(25.5, 26.5) * 32.0
	w.player.motor.place(stage)
	w.player.physics_step(0.0001)
	var blink_s := -1.0
	for i in 600:
		frames(1)
		if blink_s < 0.0 and float(a.ai.get("blink_t", 0.0)) > 0.0: blink_s = i / 60.0
		if blink_s >= 0.0 and i / 60.0 > blink_s + 0.2: break
	t.check(blink_s >= 2.0 and a.plane.distance_to(stage) < 64.0 and w.room.standable(TopdownRoom.cell_of(a.plane)) and a.altitude == 0.0,
		"topdown allies: with no way onto the landing stage on foot it blinks to the player after %.1f s, onto the stage's floor" % blink_s)
	# Its blows reach only a foe on its own height; a foe's blow reaches it only on its own height.
	fresh(base)
	a = _ally()
	a.plane = Vector2(26.5 * 32.0, 392.0)
	a.altitude = 0.0
	var above := foe("wild_boarlet", Vector2(26.5 * 32.0, 380.0))
	var level := foe("wild_boarlet", a.plane + Vector2(30, 0))
	t.check(above.altitude == 32.0 and not AllyBrain.in_reach(w.room, a, above, 60.0, 0.0, 26.0) and AllyBrain.in_reach(null, a, above, 60.0, 0.0, 26.0)
		and AllyBrain.in_reach(w.room, a, level, 60.0, 0.0, 26.0),
		"topdown allies: a foe on the terrace 12 units off is out of its reach (the side view's rule reached it), one on its level is in it")
	var biter := foe("wild_boarlet", Vector2(26.5, 12.5) * 32.0)
	biter.aim = Vector2.UP
	a.plane = biter.plane + Vector2(0, -29.0)
	a.altitude = 32.0
	a.pools.hp = a.pools.max_hp
	var bite: Dictionary = biter.def.attacks[0]
	Game.combat._enemy_hits_allies(biter, bite, Game.combat.enemy_view(biter))
	var spared: bool = a.pools.hp == a.pools.max_hp
	biter.plane = Vector2(26.5, 14.5) * 32.0
	a.plane = biter.plane + Vector2(0, -29.0)
	a.altitude = 0.0
	Game.combat._enemy_hits_allies(biter, bite, Game.combat.enemy_view(biter))
	t.check(spared and a.pools.hp < a.pools.max_hp, "topdown allies: a foe's blow from the square spares a companion on the terrace above and reaches one on its own level")
	# A fight on one level: the companion closes and strikes.
	fresh(base)
	a = _ally()
	var prey := foe("wild_boarlet", a.plane + Vector2(90, 0))
	frames(180)
	t.check(hurt(prey), "topdown allies: the companion closes on a foe on its own level and strikes it (hp %.0f / %.0f)" % [prey.pools.hp, prey.pools.max_hp])
	# A spirit animal and a foe the grid's sheet does not draw yet (a pebble imp) get stand-ins too, not the crab; Old
	# Snapper, drawn for the grid since, takes its own rows.
	fresh(base)
	var pet := EnemyState.new()
	pet.uid = Game.room_rt.uid()
	pet.def_id = "spirit_fox"
	pet.def = {"name": "Fox", "art": {"creature": "wild_boarlet"}, "half_width": 16, "height": 30, "ally": true}
	pet.team = "ally"
	pet.plane = base + Vector2(-40, 0)
	Game.room_rt.enemies[pet.uid] = pet
	w._add_foe(pet)
	var imp := foe("pebble_imp", base + Vector2(60, 0))
	w._add_foe(imp)
	var snapper := foe("old_snapper", base + Vector2(60, 60))
	w._add_foe(snapper)
	var pv = w.foe_views.get(pet.uid)
	var iv = w.foe_views.get(imp.uid)
	var sv = w.foe_views.get(snapper.uid)
	t.check(pv != null and pv.art is EnemyView and pv.art.sprite != null and iv != null and iv.art is EnemyView and iv.art.sprite != null and iv.art.sprite.creature_id == "pebble_imp",
		"topdown allies: a spirit animal and a pebble imp (no rows in the grid's sheet) are drawn by their own creature sheets as stand-ins")
	t.check(sv != null and sv.art == null and not (sv.acts as Dictionary).is_empty(), "topdown: Old Snapper is drawn by its own rows of the grid's foe sheet, not a stand-in")
	fresh(base)
	c.companions.active = had
	Game.companions._spawn_all(c)

## Hazards and weather on the grid: their spots fall all round on the plane at their floor's height; a strike reaches
## only its own level; a gust carries the body; the view sorts each spot's parts with the room (a ring over the terrace
## it lies on and under the bodies on it, a bolt at its spot's key) and draws the washes and marks on the overlay under
## the names.
func _hazards_on_the_grid(tree: SceneTree, base: Vector2) -> void:
	var edge := Vector2(26.5, 12.5) * 32.0
	fresh(edge)
	var rt: RoomRuntime = Game.room_rt
	var st: ActorState = Game.actor_state(c.id)
	var spots: Array = Game.world._hazard_spots(rt, st, {"kind": "strike", "count": 24, "spread": 320}, Rng.keyed(7, "hazard_test"))
	var on_floor := spots.all(func(sp): return w.room.standable(TopdownRoom.cell_of(Vector2(float(sp[0]), float(sp[1])))) and float(sp[2]) == w.room.floor_at(Vector2(float(sp[0]), float(sp[1]))))
	var deep := spots.any(func(sp): return absf(float(sp[1]) - st.plane.y) > 60.0)
	var raised := spots.any(func(sp): return float(sp[2]) == 32.0)
	t.check(spots.size() == 24 and on_floor and deep and raised, "topdown hazards: strikes fall all round on the plane (deeper than the side view's strip), on floors, at their floor's height")
	var h := ContentDB.entry("hazards", "lightning")
	var struck: Array = []
	var grab := func(n: String, p: Dictionary) -> void:
		if n == "hazard_struck": struck.append(p)
	GameEvents.event.connect(grab)
	var hs := {"phase": "active", "t": 0.0, "dur": 0.5, "spots": [[edge.x, edge.y - 40.0, 32.0]], "dir": 1, "pulse": 0.0, "inside": false}
	Game.world._hazard_enter(c, rt, st, h, hs, Rng.keyed(7, "hazard_a"), false)
	GameEvents.flush()
	var over := struck.is_empty()
	hs.spots = [[edge.x, edge.y + 20.0, 0.0]]
	Game.world._hazard_enter(c, rt, st, h, hs, Rng.keyed(7, "hazard_b"), false)
	GameEvents.flush()
	GameEvents.event.disconnect(grab)
	t.check(over and struck.size() == 1, "topdown hazards: a bolt on the terrace 40 units off does not strike a body on the square below; one on its own floor does")
	c.pools.hp = c.pools.max_hp
	# A gust carries the body on the plane (the World authority's drift, as on the side view's body).
	fresh(base)
	rt.hazard_drift = Vector2(120, 0)
	var x0: float = w.player.motor.pos.x
	for i in 30: w.player.physics_step(1.0 / 60.0)
	rt.hazard_drift = Vector2.ZERO
	var carried: float = w.player.motor.pos.x - x0
	t.check(carried > 50.0, "topdown hazards: a gust carries the body on the plane (%.0f units in 0.5 s)" % carried)
	# The view: each spot's parts sort with the room; washes and marks stay on the overlay, under the names.
	fresh(base)
	var hv := HazardView.new()
	hv.world = w
	hv.room = w.room
	hv.sorted_layer = w.sorted
	w.overlay.add_child(hv)
	var high := Vector2(26.5, 9.5) * 32.0
	var low := Vector2(22.5, 17.5) * 32.0
	rt.hazards["lightning"] = {"phase": "warn", "t": 0.5, "dur": 2.0, "spots": [[high.x, high.y, 32.0], [low.x, low.y, 0.0]], "dir": 1, "pulse": 0.0, "inside": false}
	await tree.process_frame
	await tree.process_frame
	var pieces: Array = hv.pieces.filter(func(pc): return pc.visible)
	var rings: Array = pieces.filter(func(pc): return str(pc.part.kind) == "strike")
	var bolts: Array = pieces.filter(func(pc): return str(pc.part.kind) == "bolt")
	var marks: Array = hv._parts(rt).filter(func(pt): return pt.mark)
	var ring_hi: Array = rings.filter(func(pc): return float(pc.part.z) == 32.0)
	var ring_lo: Array = rings.filter(func(pc): return float(pc.part.z) == 0.0)
	var row_key := (floorf(high.y / 32.0) + 1.0) * 16.0
	var sorted_ok: bool = rings.size() == 2 and bolts.size() == 2 and ring_hi.size() == 1 and ring_lo.size() == 1 \
		and ring_hi[0].position.y > row_key and ring_hi[0].position.y < w.room.sort_key(high, 32.0) and ring_lo[0].position.y < w.room.sort_key(low, 0.0) \
		and bolts.all(func(pc): return pc.position.y == w.room.sort_key(pc.part.p, float(pc.part.z))) and pieces.all(func(pc): return pc.get_parent() == w.sorted)
	t.check(sorted_ok and marks.size() == 2 and not hv.ground.visible and hv.air.z_index < WorldLabels.LABEL_Z and hv.get_parent() == w.overlay and hv.squash > 2.0,
		"topdown hazards: the rings sort with the room (over the terrace's row, under a body on it) and the bolts at their spots' keys; the washes and the two marks draw on the overlay under the names")
	rt.hazards.erase("lightning")
	var made: Array = hv.pieces.duplicate()
	hv.queue_free()
	await tree.process_frame
	t.check(made.all(func(pc): return not is_instance_valid(pc) or pc.is_queued_for_deletion()), "topdown hazards: the room's hazard view takes its sorted parts with it")
	# The heavens' bolt strikes a circle on the grid (the side view's flattened strip missed a body 60 south of it).
	fresh(base)
	var res: Dictionary = Game.combat.apply_tribulation_strike(c, base + Vector2(0, -60), 80.0, 45.0)
	var res2: Dictionary = Game.combat.apply_tribulation_strike(c, base + Vector2(0, -100), 80.0, 45.0)
	c.pools.hp = c.pools.max_hp
	t.check(res.get("hit", false) and not res2.get("hit", false), "topdown hazards: a tribulation bolt 60 units north strikes within its ring of 80; one 100 off does not")
	# Burning ground (a foe's blow) burns only on its own floor.
	fresh(Vector2(26.5, 11.5) * 32.0)
	Game.combat.ground_fires.clear()
	var hp0: float = c.pools.hp
	Game.combat.ground_fires.append({"x": edge.x, "y": edge.y - 10.0, "alt": 0.0, "r": 70.0, "t": 5.0, "tick": 0.0, "pct": 0.1, "source": "test"})
	Game.combat._tick_ground_fires(0.1)
	var unburnt: bool = c.pools.hp == hp0
	Game.combat.ground_fires[0].alt = 32.0
	Game.combat.ground_fires[0].tick = 0.0
	Game.combat._tick_ground_fires(0.1)
	var burnt: bool = c.pools.hp < hp0
	Game.combat.ground_fires.clear()
	c.pools.hp = c.pools.max_hp
	t.check(unburnt and burnt, "topdown hazards: burning ground on the square does not burn a body on the terrace above; on its own floor it does")

## The other places where the grid used the side view's x-only or walk-strip rules (the plan's "As built" lists them).
func _audit_on_the_grid(base: Vector2) -> void:
	var rt: RoomRuntime = Game.room_rt
	var st: ActorState = Game.actor_state(c.id)
	# Respawn out of view against the camera: near the west wall the camera shows x 0-1280, so a spot 768 east is in
	# view (the old rule said 700 across was enough) and the foe waits; one past the view's east edge comes back.
	var west := Vector2(3.5, 14.5) * 32.0
	var east := Vector2(27.5, 14.5) * 32.0
	var far_east := Vector2(46.5, 14.5) * 32.0
	fresh(west)
	var slot := {"spec": {"enemy": "wild_boarlet", "points": [[east.x, east.y]]}, "index": 0, "point": east, "uid": 0, "timer": 0.0, "held": false, "entry": false}
	var slot2 := {"spec": {"enemy": "wild_boarlet", "points": [[far_east.x, far_east.y]]}, "index": 1, "point": far_east, "uid": 0, "timer": 0.0, "held": false, "entry": false}
	var in_view: Vector2 = Game.enemies._spawn_point(slot)
	var out_view: Vector2 = Game.enemies._spawn_point(slot2)
	var shown := foe("wild_boarlet", east)
	t.check(not in_view.is_finite() and out_view == far_east and absf(east.x - st.plane.x) >= 700.0 and not hud._caption_worthy("enemy_aggro", {"enemy": shown.uid}),
		"topdown audit: by the west wall a spot 24 tiles east is on the camera (the old rule, 700 across, called it off screen): no respawn there and no off-screen notice; one past the view's edge respawns")
	# The ways: reached only on their own floor, along and across as they are turned.
	fresh(Vector2(26.5, 12.4) * 32.0)
	var door := {"id": "test_door", "at": [26.5 * 32.0, 11.5 * 32.0], "dir": [0, -1], "reach": [32.0, 32.0], "alt": 32.0}
	var from_below: bool = Game.world.portal_near(c, door)
	var side_rule: bool = Game.world.portal_near(c, {"at": door.at})
	w.player.motor.place(Vector2(26.5, 11.5) * 32.0)
	w.player.physics_step(0.0001)
	t.check(not from_below and side_rule and Game.world.portal_near(c, door), "topdown audit: a way on the terrace is not taken from the square below its face (the old reach was), and is on the terrace")
	# Pickups: a drop on the terrace's edge is not drawn in from the square below; a spill over a ledge stays on its floor.
	fresh(Vector2(26.5, 12.4) * 32.0)
	Game.world._drop_loot(c, {"items": [{"item": "rat_tail", "count": 1}], "coins": 0, "equipment": []}, Vector2(26.5, 11.6) * 32.0, 32.0, "enemy")
	frames(40)
	var left: bool = rt.loot.size() == 1 and float(rt.loot[0].alt) == 32.0
	w.player.motor.place(Vector2(26.5, 11.4) * 32.0)
	w.player.physics_step(0.0001)
	frames(40)
	var spill: Vector3 = WorldAuthority._loot_spot(rt, Vector2(26.5, 11.9) * 32.0, 32.0, 0.0, 22.0)
	t.check(left and rt.loot.is_empty() and spill.z == 32.0 and spill.y < 12.0 * 32.0,
		"topdown audit: a drop on the terrace's edge is not picked up from the square below (the old reach, 60 up, took it), and is on the terrace; a spill over the ledge lies on its own floor")
	# Auto-path arrives only on the goal's own floor, not under it on the square below.
	fresh(Vector2(26.5, 12.4) * 32.0)
	var pilot := Autopilot.new(w.player)
	var goal := Vector2(26.5, 11.7) * 32.0
	var going: Vector2 = pilot._toward_grid(goal, 30.0)
	w.player.motor.place(Vector2(26.5, 11.3) * 32.0)
	w.player.physics_step(0.0001)
	t.check(going != Vector2.INF and pilot._toward_grid(goal, 30.0) == Vector2.INF, "topdown audit: auto-path is not there under a terrace spot 22 units off on the plane, only on the terrace")
	# The names: the nearest keep their rows by the distance on the plane, not across.
	fresh(base)
	var north := foe("wild_boarlet", base + Vector2(0, -150))
	w._add_foe(north)
	(w.label_views[north.uid] as EnemyView).sync(north, 0.0)
	var mine: Array = WorldShared.label_views(w, w.player_feet(), Vector2.ONE).filter(func(v): return v.id == "e%d" % north.uid)
	t.check(not mine.is_empty() and absf(float(mine[0].near) - 150.0) < 4.0, "topdown audit: a foe's name straight north of the player is 150 off for the label order (across it was 0)")
	# A foe picks its ranged or its close blow by the distance on the plane.
	var rogue := foe("rogue_cultivator", base + Vector2(0, -300))
	var pick: int = EnemyBrain._choose_attack(Game.enemies, rogue, rogue.def.attacks)
	t.check(float(rogue.def.attacks[pick].hitbox.x[1]) > 200.0, "topdown audit: a rogue cultivator 300 north throws its sword Qi (across the distance was 0 and it chose its thrust)")
	# A rare herb's guardian wakes by the approach on the plane.
	t.check(not Game.world._guardian_wakes({"at": [base.x, base.y - 600.0], "alt": 0.0}, st) and Game.world._guardian_wakes({"at": [base.x, base.y - 300.0], "alt": 0.0}, st),
		"topdown audit: a herb's guardian wakes for a body 300 off on the plane, not 600 straight north (across it was 0)")
	# Things the rules put in the room land on its floors: a spar partner, a summoned add, an ambush.
	var by_water := Vector2(25.5, 22.5) * 32.0
	fresh(by_water)
	Game.quest.start_spar(c, "sparring_disciple")
	var partner: EnemyState = null
	for e in rt.living_enemies():
		if e.def.get("spar", false): partner = e
	var summoner := foe("wild_boarlet", by_water)
	Game.enemies.enemy_attack_release(summoner, {"summon": "wild_boarlet"})
	frames(1)
	Game.world.spring_ambush(c, {"enemy": "wild_boarlet", "count": 2, "level": [1, 1]})
	var placed: Array = rt.living_enemies().filter(func(e): return e != summoner)
	var on_floors: bool = placed.size() >= 5 and placed.all(func(e): return w.room.standable(TopdownRoom.cell_of(e.plane)) and e.altitude == w.room.floor_at(e.plane))
	t.check(partner != null and on_floors, "topdown audit: a spar partner, two summoned adds and an ambush all land on floors of the grid, at their height (%d placed)" % placed.size())
	Game.combat.end_spar(c.id)
	Game.world.ambush_cd.erase(c.id)
	fresh(base)
# ------------------------------------------------------------------ decision 38: the combat feel
## Names of the effect sheets TopdownFx is playing now (their files' base names).
func _fx_now() -> Array:
	return w.tfx.nodes.filter(func(n): return is_instance_valid(n)).map(func(n): return (n.tex as Texture2D).resource_path.get_file().get_basename())

## A foe of `def` at `p` that lives through anything (its blows and flinches still show).
func sturdy(def: String, p: Vector2) -> EnemyState:
	var e := foe(def, p, 60)
	e.pools.max_hp = 1.0e15
	e.pools.hp = e.pools.max_hp
	return e

## Decision 42 · animation canceling: basic attack, technique, basic attack in one flow, with the stand-in's bare hands
## and its first technique. The technique, pressed in the step's anticipation, waits in the buffer and cuts the step's
## recovery the frame its active frames end; the step's blow landed on its own hit frame and none before it. The basic
## attack, pressed in the technique's wind-up, waits likewise and cuts the technique's recovery once its active frames
## have played, after the technique's own blow landed on its hit; it is the chain's second step. The figure takes each
## new action's pose from its first frame. Straight to Combat, a technique in a step's active window is refused (busy)
## and the step goes on: nothing cuts a blow before it lands.
func _weave(base: Vector2) -> void:
	fresh(base)
	c.pools.qi = c.pools.max_qi
	var p = w.player
	var target := sturdy("wild_boarlet", base + Vector2(34, 0))
	var tl: Dictionary = Game.combat.timeline(c.id)
	var tech_id := str(c.cultivator.technique_slots[0])
	var tph := CombatFeel.technique_phases(ContentDB.entry("techniques", tech_id))
	var hp := target.pools.hp
	p.aim_attack(Vector2.RIGHT)
	var step := {"hit_at": float(tl.hit_at), "duration": float(tl.duration), "cut": CombatFeel.weave_from(tl, "technique", c), "action": str(tl.action)}
	frames(1)
	var r1: Dictionary = p.aim_technique(0, Vector2.RIGHT, 0.4)
	var waited1: bool = not r1.get("ok", false) and str(p.weave.get("kind", "")) == "technique"
	var seen := {"step_hit": -1.0, "cut1": -1.0, "tech_hit": -1.0, "cut2": -1.0, "waited2": false, "combo2": -9, "poses": []}
	var stage := 0      # 0 the first step, 1 the technique, 2 the second step
	var prev_t := float(tl.t)
	var clock := 1.0 / 60.0
	for i in 150:
		frames(1)
		p.sync(1.0 / 60.0)
		clock += 1.0 / 60.0
		var hurt_now: bool = target.pools.hp < hp
		hp = target.pools.hp
		if stage == 0 and str(tl.technique) == tech_id:
			stage = 1
			seen.cut1 = prev_t
			seen.at_cut1 = clock
			seen.poses.append([p.pose, p.frame, p.action_phase])
			p.attack()   # pressed in the technique's wind-up: it waits for the technique's cut
			seen.waited2 = str(p.weave.get("kind", "")) == "attack" and str(tl.technique) == tech_id
		elif stage == 1 and str(tl.technique) == "" and str(tl.action) != "":
			stage = 2
			seen.cut2 = prev_t
			seen.at_cut2 = clock
			seen.combo2 = int(tl.combo)
			seen.action2 = str(tl.action)
			seen.poses.append([p.pose, p.frame, p.action_phase])
			break
		elif hurt_now and stage == 0 and float(seen.step_hit) < 0.0: seen.step_hit = float(tl.t)
		elif hurt_now and stage == 1 and float(seen.tech_hit) < 0.0: seen.tech_hit = float(tl.t)
		prev_t = float(tl.t)
	var f := 1.0 / 60.0 + 0.0001
	var basic_cut := float(tph.anticipation) + float(tph.active) + float(tph.recovery) * float(CombatFeel.weave_cfg().get("basic_after", 0.0))
	measured.weave = {"step": step, "technique": {"hit_at": snappedf(float(tph.hit_at), 0.001), "duration": snappedf(float(tph.duration), 0.001),
		"cut": snappedf(basic_cut, 0.001)}, "cut1": snappedf(float(seen.cut1), 0.001), "cut2": snappedf(float(seen.cut2), 0.001),
		"three_starts_s": snappedf(float(seen.get("at_cut2", 0.0)), 0.001), "unwoven_s": snappedf(float(step.duration) + float(tph.duration), 0.001)}
	var p1: Array = seen.poses[0] if seen.poses.size() > 0 else ["", -1, ""]
	var p2: Array = seen.poses[1] if seen.poses.size() > 1 else ["", -1, ""]
	t.check(waited1 and float(seen.step_hit) >= float(step.hit_at) - 0.0001 and float(seen.step_hit) < float(step.hit_at) + f
		and float(seen.cut1) >= float(step.cut) - 0.0001 and float(seen.cut1) < float(step.cut) + f and float(seen.cut1) < float(step.duration) - 0.05,
		"topdown weave: a technique pressed in a step's anticipation waits, the step's blow lands on its hit frame (%.3f s, hit at %.3f) and none before, and the technique cuts the step's recovery the frame it begins (%.3f s of %.3f)"
			% [float(seen.step_hit), float(step.hit_at), float(seen.cut1), float(step.duration)])
	t.check(seen.waited2 and float(seen.tech_hit) >= float(tph.hit_at) - 0.0001 and float(seen.tech_hit) < float(tph.hit_at) + f
		and float(seen.cut2) >= basic_cut - 0.0001 and float(seen.cut2) < basic_cut + f and float(seen.cut2) < float(tph.duration) - 0.05
		and int(seen.combo2) == 1 and str(seen.get("action2", "")) == "punch_2",
		"topdown weave: a basic attack pressed in the technique's wind-up waits, the technique's blow lands on its hit (%.3f s, at %.3f), and the attack cuts its recovery after its active frames (%.3f s of %.3f) as the chain's second step (%s)"
			% [float(seen.tech_hit), float(tph.hit_at), float(seen.cut2), float(tph.duration), str(seen.get("action2", ""))])
	t.check(p1[0] != step.action and int(p1[1]) == 0 and str(p1[2]) == "anticipation" and p2[0] == "punch_2" and int(p2[1]) == 0 and str(p2[2]) == "anticipation"
		and float(seen.get("at_cut2", 99.0)) < float(step.duration) + float(tph.duration) - 0.2,
		"topdown weave: the figure takes each new action's pose from its first frame at the cut (%s, %s); basic, technique, basic begin within %.2f s, not %.2f"
			% [str(p1), str(p2), float(seen.get("at_cut2", 0.0)), float(step.duration) + float(tph.duration)])
	# Straight to Combat, a technique in the step's active window is refused and the step goes on to land.
	fresh(base)
	c.pools.qi = c.pools.max_qi
	target = sturdy("wild_boarlet", base + Vector2(34, 0))
	tl = Game.combat.timeline(c.id)   # fresh() starts a new timeline
	p.aim_attack(Vector2.RIGHT)
	var n := 0
	while CombatFeel.phase_of(tl, c) != "active" and n < 60:
		frames(1)
		n += 1
	var early_hurt := hurt(target) and float(tl.t) < float(tl.hit_at)
	var r2: Dictionary = Game.submit({"type": "use_technique", "slot": 0, "facing": 1, "aim": Vector2.RIGHT, "aimed": false, "dist": -1.0})
	var still_step: bool = str(tl.technique) == "" and str(tl.action) == str(step.action)
	frames(20)
	t.check(str(r2.get("reason", "")) == "busy" and still_step and not early_hurt and hurt(target) and CombatFeel.weave(tl, "technique", c) == "free",
		"topdown weave: a technique sent in a step's active window is refused (%s), the step lands its blow, and no cut comes before it" % str(r2.get("reason", "")))
	p.weave = {}

## Decision 42, a bug from the prototype: after meditating, walking kept meditation's seated pose. Moving now ends the
## meditation at once and the figure runs (a light touch walks); a jump rises from the seat too.
func _meditate_then_walk(base: Vector2) -> void:
	var p = w.player
	var seen := {}
	for band in [1.0, 0.5]:
		fresh(base)
		p.movement = Vector2.ZERO
		var r: Dictionary = Game.submit({"type": "start_meditation"})
		frames(2)
		p.sync(1.0 / 60.0)
		seen["sat_%s" % band] = [r.get("ok", false), c.cultivator.meditating, p.pose]
		p.movement = Vector2.RIGHT * band
		frames(8)
		p.sync(1.0 / 60.0)
		seen["moved_%s" % band] = [c.cultivator.meditating, p.pose]
		p.movement = Vector2.ZERO
	fresh(base)
	Game.submit({"type": "start_meditation"})
	frames(2)
	p.jump()
	frames(3)
	p.sync(1.0 / 60.0)
	seen.jumped = [c.cultivator.meditating, p.pose]
	frames(40)
	t.check(seen["sat_1.0"] == [true, true, "meditate"] and seen["sat_0.5"] == [true, true, "meditate"] and seen["moved_1.0"] == [false, "run"]
		and seen["moved_0.5"] == [false, "walk"] and seen.jumped == [false, "jump"],
		"topdown: moving ends meditation at once and the figure runs, or walks at a light touch, never sliding in the seated pose; a jump rises from it (%s)" % str(seen))

## Decision 38 (CombatFeel, TopdownFx): a blow's hit-stop by its weight; the cancel rule (a dodge drops a blow in its
## anticipation, is refused in its active window and waits in a buffer for its late recovery); the lunge and the dash
## attack; the step's smear in its direction with its contact on the hit, the technique forms, the impact marks, the
## foe's tell, the dust and the held guard, all in the world's sorted layer; the eight directions (three mirrored); the
## struck foe's flash and hop; and under Reduce motion no hit-stop, kick or shake.
func _combat_feel(_tree: SceneTree, base: Vector2) -> void:
	var fam: Dictionary = StatRules.family(c)
	var tl: Dictionary
	# Weight: the first step of a chain against the dragged (charged) finisher.
	fresh(base)
	var dummy := sturdy("wild_boarlet", base + Vector2(30, 0))
	tl = Game.combat.timeline(c.id)
	tl.family = str(fam.id)
	tl.combo = 0
	tl.charged = false
	var blow := {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1, 1], "never_miss": true, "source": "basic"}
	var pv: Dictionary = Game.combat.player_view(c)
	Game.combat._player_hits_enemy(c, pv, dummy, blow, 1)
	var light: float = Game.combat.hitstop
	Game.combat.hitstop = 0.0
	tl.charged = true
	Game.combat._player_hits_enemy(c, pv, dummy, blow, 1)
	var heavy: float = Game.combat.hitstop
	tl.charged = false
	var f := 1.0 / 60.0
	measured.hitstop_frames = {"step_1": snappedf(light / f, 0.1), "charged": snappedf(heavy / f, 0.1)}
	t.check(heavy > light and light >= 3 * f - 0.001 and light <= 5 * f + 0.001 and heavy >= 8 * f - 0.001,
		"topdown feel: a first step holds %.0f frames, the dragged finisher %.0f (a crit two more)" % [light / f, heavy / f])
	# The cancel rule.
	fresh(base)
	var target := sturdy("wild_boarlet", base + Vector2(30, 0))
	w.player.aim_attack(Vector2.RIGHT)
	frames(1)
	var ph0 := CombatFeel.phase_of(Game.combat.timeline(c.id), c)
	var r0: Dictionary = Game.submit({"type": "dodge", "direction": Vector2.LEFT, "facing": 1, "moves": false})
	frames(40)
	var dropped: bool = ph0 == "anticipation" and r0.get("ok", false) and not hurt(target) and str(Game.combat.timeline(c.id).action) == ""
	fresh(base)
	target = sturdy("wild_boarlet", base + Vector2(30, 0))
	w.player.aim_attack(Vector2.RIGHT)
	var n := 0
	while CombatFeel.phase_of(Game.combat.timeline(c.id), c) != "active" and n < 60:
		frames(1)
		n += 1
	var r1: Dictionary = Game.submit({"type": "dodge", "direction": Vector2.LEFT, "facing": 1, "moves": false})
	w.player.dodge()   # the player's own dodge waits in the buffer for the cancel point
	var buffered: float = w.player.dodge_buffer
	var went := false
	for i in 30:
		frames(1)
		if c.pools.cooldown("dodge") > 0.0:
			went = true
			break
	var ph := CombatFeel.phases(fam, 0, 1.0 + c.stats.value("attack_speed"))
	measured.phases = {"family": str(fam.id), "anticipation": snappedf(float(ph.anticipation), 0.001), "active": snappedf(float(ph.active), 0.001),
		"recovery": snappedf(float(ph.recovery), 0.001), "cancel_from": snappedf(float(ph.cancel_from), 0.001)}
	t.check(dropped and str(r1.get("reason", "")) == "committed" and buffered > 0.0 and went and hurt(target),
		"topdown feel: a dodge drops a blow in its anticipation (%s), is refused in its active window (%s) and waits in the buffer until it may cancel (%s)" % [ph0, str(r1.get("reason", "")), str(went)])
	# The lunge: a step carries the body toward its aim; out of a dash it is a dash attack.
	fresh(base)
	var from: Vector2 = w.player.motor.pos
	w.player.aim_attack(Vector2.RIGHT)
	frames(12)
	var lunged: float = w.player.motor.pos.x - from.x
	fresh(base)
	w.player.dodge()
	frames(3)
	var r2: Dictionary = w.player.aim_attack(Vector2.RIGHT)
	var dash_attack: bool = w.player.dash_attack and w.player.motor.dash_t <= 0.0
	measured.lunge = snappedf(lunged, 0.1)
	t.check(r2.get("ok", false) and lunged >= CombatFeel.lunge(str(fam.id), 0) * 0.8 and dash_attack,
		"topdown feel: a step lunges %.0f units along its aim, and one out of a dash is a dash attack that ends the dash" % lunged)
	# The effects, each in the world's sorted layer.
	fresh(base)
	w.tfx.clear()
	GameEvents.flush()
	w.player.motor.face(Vector2.RIGHT)
	target = sturdy("wild_boarlet", base + Vector2(30, 0))
	w.player.aim_attack(Vector2.RIGHT)
	GameEvents.flush()
	var smear: Array = w.tfx.nodes.filter(func(x): return (x.tex as Texture2D).resource_path.ends_with("melee_%s.png" % str(fam.id)))
	var lead: float = float(Game.combat.timeline(c.id).hit_at) - 1.0 / (CombatFeel.smear_fps(str(fam.id)) * (1.0 + c.stats.value("attack_speed")))
	var smear_ok: bool = smear.size() == 1 and smear[0].row == 0 and not smear[0].flip and smear[0].get_parent() == w.sorted \
		and absf(-float(smear[0].t) - lead) < 0.002 and float(smear[0].position.y) > w.room.sort_key(w.player.motor.pos, w.player.motor.z)
	frames(40)
	GameEvents.flush()
	var names: Array = _fx_now()
	t.check(smear_ok and names.has("impact_e"),
		"topdown feel: a step plays its family's smear toward its aim in the sorted layer, its contact on the hit (lead %.3f s), and the blow leaves its impact mark (%s)" % [lead, str(names)])
	var forms_seen := {}
	for slot in 4:
		fresh(base)
		w.tfx.clear()
		sturdy("wild_boarlet", base + Vector2(0, 60))
		c.pools.qi = c.pools.max_qi
		var tr: Dictionary = w.player.aim_technique(slot, Vector2.DOWN, 0.5)
		GameEvents.flush()
		var form := str(ContentDB.entry("techniques", str(c.cultivator.technique_slots[slot])).get("vfx", {}).get("anim", ""))
		forms_seen[form] = "refused: " + str(tr.get("reason", "")) if not tr.get("ok", false) else "none"
		for nm in _fx_now():
			if str(nm).begins_with("form_" + form): forms_seen[form] = str(nm)
	t.check(forms_seen.size() == 4 and forms_seen.values().all(func(v): return str(v).begins_with("form_")),
		"topdown feel: each slotted technique plays its form's ground-plane sheet (%s)" % str(forms_seen))
	# A foe's tell, a dash's dust, the held guard.
	fresh(base)
	w.tfx.clear()
	var striker := sturdy("wild_boarlet", base + Vector2(30, 0))
	EnemyBrain.wind_up(Game.enemies, striker, striker.def.attacks, striker.def.attacks[0])
	GameEvents.flush()
	var told: bool = _fx_now().has("common")
	w.player.dodge()
	for ev in w.player.physics_step(1.0 / 60.0): w._feedback(ev)
	var dusted: bool = _fx_now().has("dust")
	Game.submit({"type": "guard_start"})
	w._hold_marks()
	var guard_on: bool = w.tfx.guard_node != null and is_instance_valid(w.tfx.guard_node)
	Game.submit({"type": "guard_end"})
	w._hold_marks()
	t.check(told and dusted and guard_on and w.tfx.guard_node == null, "topdown feel: a foe's wind-up shows its tell, a dash kicks dust, and a guard holds its wall of qi while it lasts")
	# The eight directions, the west three mirrored.
	var dirs: Array = []
	for i in 8: dirs.append(TopdownFx.dir_of(Vector2.from_angle(i * PI / 4.0)))
	t.check(dirs == [["e", false], ["se", false], ["s", false], ["se", true], ["e", true], ["ne", true], ["n", false], ["ne", false]],
		"topdown feel: an effect takes the nearest of eight directions, drawing E, SE, S, NE and N and mirroring the west three (%s)" % str(dirs))
	# The struck foe: white, then tinted; a knockback hops it; the effects freeze in a hit-stop.
	fresh(base)
	var struck := sturdy("wild_boarlet", base + Vector2(30, 0))
	GameEvents.flush()
	var view = w.foe_views.get(struck.uid)
	Game.combat._player_hits_enemy(c, Game.combat.player_view(c), struck, {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1, 1],
		"never_miss": true, "knockback": 60, "source": "basic"}, 1)
	view.sync(0.0)
	var white0: float = view.white
	var top := 0.0
	for i in 12:
		Game.enemies.tick(1.0 / 60.0)
		view.sync(1.0 / 60.0)
		top = maxf(top, view.hop)
	w.tfx.clear()
	var sm = w.tfx.smear("", str(fam.id), "step_1", Vector2.RIGHT, base, 0.0, -1.0)
	w.held = true
	w._sync(0.1)
	var froze: bool = sm != null and absf(float(sm.t)) < 0.001
	w.held = false
	w._sync(0.1)
	var ran: bool = sm != null and float(sm.t) > 0.09
	t.check(white0 == 1.0 and view.white == 0.0 and top >= 2.0 and froze and ran,
		"topdown feel: a struck foe flashes white, then tinted, a knockback hops it %.0f px, and a hit-stop freezes the effects with the fight" % top)
	# Reduce motion: no hit-stop, no kick, no shake.
	var was: bool = bool(Game.account.settings.get("reduce_motion", false))
	Game.account.settings["reduce_motion"] = true
	var rig := ShakeRig.new()
	rig.kick(Vector2.RIGHT, 6.0)
	rig.add(0.2, 4.0)
	var still: Vector2 = rig.offset(0.01)
	w.sim_frozen = false
	Game.combat.hitstop = 0.1
	w._physics_process(1.0 / 60.0)
	var off_held: bool = w.held
	var off_stop: float = Game.combat.hitstop
	Game.account.settings["reduce_motion"] = was
	Game.combat.hitstop = 0.1
	w._physics_process(1.0 / 60.0)
	var on_held: bool = w.held
	w.sim_frozen = true
	Game.combat.hitstop = 0.0
	var rig2 := ShakeRig.new()
	rig2.kick(Vector2.RIGHT, 6.0)
	var kicked: Vector2 = rig2.offset(0.01)
	t.check(still == Vector2.ZERO and not off_held and off_stop == 0.0 and on_held and kicked.x < -1.0,
		"topdown feel: under Reduce motion there is no hit-stop, kick or shake; without it a hit-stop holds the fight and a kick knocks the view along the blow (%s)" % str(kicked))

# ------------------------------------------------------------------ the prototype's QA: a clean field, the eel's turn
## The field stays clean (docs/redesign/prototype_qa.md): a foe at rest far from the player shows no plate and no bar;
## the soft-locked target shows its full plate over a compact HP bar; an elite always shows its plate; a foe in a fight
## (aggroed, or struck) shows it, and it stays ENGAGED_S after the fight; a foe far above the player's Level keeps its
## danger mark with no plate; a crowd of foes in a fight shows plates that never touch. Each label sits on the top-down
## figure's head (the foe sheet's `top`), not at the side view's height.
func _labels_clean(tree: SceneTree, base: Vector2) -> void:
	fresh(base)
	var calm := foe("reedtail_rat", base + Vector2(-40, -150))
	var ahead := foe("mudshell_crab", base + Vector2(0, 56))
	var strong := foe("reedtail_rat", base + Vector2(40, -150), ProgressionRules.level(c) + 10)
	var crowned := foe("wild_boarlet", base + Vector2(150, 30))
	crowned.elite = true
	frames(2)
	for i in 3: await tree.process_frame
	var lv := func(e: EnemyState): return w.label_views.get(e.uid)
	var box := func(e: EnemyState) -> Rect2: return lv.call(e).label_box if lv.call(e) != null else Rect2()
	var plate := func(e: EnemyState) -> bool: return lv.call(e) != null and lv.call(e).plate_shown(e)
	t.check(not plate.call(calm) and box.call(calm).size == Vector2.ZERO and plate.call(ahead) and lv.call(ahead).focused and box.call(ahead).size.y > 20.0
		and plate.call(crowned) and not plate.call(strong) and box.call(strong).size.y > 0.0,
		"topdown labels: at rest a foe shows nothing, the soft-locked target its plate over its HP bar, an elite its plate, a foe far above the Level its danger mark alone (calm %s, target %s, strong %s)" % [str(box.call(calm)), str(box.call(ahead)), str(box.call(strong))])
	calm.ai.state = "aggro"
	lv.call(calm).sync(calm, 0.05)
	var in_fight: bool = plate.call(calm) and lv.call(calm).shows_hp_bar(calm)
	calm.ai.state = "idle"
	lv.call(calm).sync(calm, 1.0)
	var after: bool = plate.call(calm)
	lv.call(calm).sync(calm, EnemyView.ENGAGED_S)
	t.check(in_fight and after and not plate.call(calm), "topdown labels: a foe in a fight with the player shows its plate and HP bar, and its plate a few seconds after the fight")
	# The label on the figure's head: the foe sheet's top over its feet, not the side view's height; an elite's on its
	# own larger figure's (decision 43).
	var sheet: Dictionary = w.room.tileset.foes.species
	var eel: EnemyState = Game.enemies.spawn_at("hollowed_eel", base + Vector2(-300, 200), 1)
	var big: EnemyState = Game.enemies.spawn_at("mudshell_crab", base + Vector2(-260, 150), 1, {"elite": true})
	frames(1)
	var eel_top: float = lv.call(eel).figure_top if lv.call(eel) != null else -1.0
	var big_top: float = lv.call(big).figure_top if lv.call(big) != null else -1.0
	t.check(is_equal_approx(lv.call(ahead).figure_top, float(sheet.mudshell_crab.top) * TopdownRoom.ART) and is_equal_approx(eel_top, float(sheet.hollowed_eel.top) * TopdownRoom.ART)
		and is_equal_approx(big_top, float(sheet.mudshell_crab.elite.top) * TopdownRoom.ART) and big_top > lv.call(ahead).figure_top,
		"topdown labels: a foe's label sits on its top-down figure's head, the hovering eel's and an elite's too (crab %.0f, the elite crab %.0f; eel %.0f over its feet, its side-view height %.0f)" % [lv.call(ahead).figure_top, big_top, eel_top, eel.height()])
	Game.room_rt.enemies.erase(eel.uid)
	Game.room_rt.enemies.erase(big.uid)
	# A crowd in a fight: every plate shows, none touching.
	fresh(base)
	var crowd: Array = []
	for i in 7: crowd.append(foe("reedtail_rat", w.room.nearest_standable(base + Vector2(-60 + i * 20, 40 + (i % 2) * 10))))
	for e in crowd: e.ai.state = "aggro"
	frames(2)
	for i in 3: await tree.process_frame
	var laid: Dictionary = w.layout_labels()
	var shown := crowd.filter(func(e): return plate.call(e)).size()
	var foe_items: Array = laid.items.filter(func(it): return str(it.kind) == "foe")
	# No plate covers the player's own body (a villager's plate under their feet, a foe's over its head just in front).
	var body := Rect2(w.feet_on_screen() + Vector2(-14, -64), Vector2(28, 64))
	var on_body: Array = laid.items.filter(func(it): return Rect2((it.rect as Rect2).position + laid.offsets.get(it.id, Vector2.ZERO), (it.rect as Rect2).size).intersects(body))
	t.check(on_body.is_empty(), "topdown labels: no plate is laid over the player's body (%s)" % str(on_body.map(func(it): return it.id)))
	t.check(shown == crowd.size() and foe_items.size() >= crowd.size() and WorldLabels.touching(foe_items, laid.offsets).is_empty(),
		"topdown labels: seven foes clustered in a fight show their plates, and no two touch (%d shown, %d laid out of %s; %s)" % [shown, foe_items.size(),
			str(laid.items.map(func(it): return str(it.kind))), str(WorldLabels.touching(foe_items, laid.offsets))])
	# A plate the layout puts half a box aside is drawn there (its view draws at label_offset.x) and keeps reporting its
	# box at no offset (the QA's crowd plates were laid aside but drawn where they stood).
	var lv0 = lv.call(crowd[0])
	var at_rest: Rect2 = lv0.label_box
	lv0.label_offset = Vector2(40.0, 0.0)
	lv0.tag.queue_redraw()
	await tree.process_frame
	var aside_box: Rect2 = lv0.label_box
	lv0.label_offset = Vector2.ZERO
	t.check(at_rest.size.x > 0.0 and aside_box.is_equal_approx(at_rest),
		"topdown labels: a plate laid aside keeps reporting its box at no offset, as the layout pass reads it (%s, %s)" % [str(at_rest), str(aside_box)])
	for e in crowd: e.ai.state = "idle"
	# A door's chevron keeps other plates off it (Granny Liu's plate lay under her hut door's arrow).
	fresh(base)
	var by_door := foe("mudshell_crab", base + Vector2(0, 56))
	frames(2)
	for i in 3: await tree.process_frame
	var dl = lv.call(by_door)
	var pv := PortalView.new()
	pv.label_only = true
	pv.setup({"id": "qa_door", "type": "door", "at": [0, 0], "to": ""}, {})
	pv.position = dl.position
	pv.door_top = (dl.label_box as Rect2).get_center().y + 7.0   # the chevron right over the crab's plate
	w.overlay.add_child(pv)
	pv.set_process(false)   # after entering the tree (its _ready turns processing on)
	pv.state = {"open": true, "text": ""}
	w.portal_views.append(pv)
	pv.tag.queue_redraw()
	await tree.process_frame
	var xf: Transform2D = w.overlay.get_global_transform_with_canvas()
	var arrow := Rect2(xf * (pv.position + pv.arrow_box.position), pv.arrow_box.size)
	var laid_door: Dictionary = w.layout_labels()
	var crab_id := "e%d" % by_door.uid
	var crab_at: Array = laid_door.items.filter(func(it): return str(it.id) == crab_id)
	var crab_rect := Rect2((crab_at[0].rect as Rect2).position + laid_door.offsets.get(crab_id, Vector2.ZERO), (crab_at[0].rect as Rect2).size) if not crab_at.is_empty() else Rect2()
	t.check(pv.arrow_box.size.x > 0.0 and crab_rect.size.x > 0.0 and not crab_rect.intersects(arrow),
		"topdown labels: a plate keeps off a door's chevron (the arrow %s, the plate %s)" % [str(arrow), str(crab_rect)])
	w.portal_views.erase(pv)
	pv.free()
	# A way at the room's edge with a long line (the prototype's gate: "The road beyond is still being drawn.") keeps
	# its whole plate inside the room, so on the screen (it ran off the right edge at the Marsh Edge).
	var edge := PortalView.new()
	edge.label_only = true
	edge.setup({"id": "qa_edge", "type": "edge", "at": [2032, 400], "to": ""}, {"bounds": [0, 0, 2048, 900]})
	tree.root.add_child(edge)
	edge.set_process(false)   # after entering the tree (its _ready turns processing on): the state is the test's
	edge.state = {"open": false, "text": Tx.t("sim.world.road_being_drawn")}
	edge.near = true
	for i in 3:
		edge.tag.queue_redraw()
		await tree.process_frame
	var plate_x := Vector2(edge.position.x + edge.label_box.position.x, edge.position.x + edge.label_box.end.x)
	t.check(edge.label_box.size.x > 200.0 and plate_x.x >= 0.0 and plate_x.y <= 2048.0,
		"topdown labels: a way's long plate at the room's edge stays wholly inside the room (%s of 2048)" % str(plate_x))
	edge.free()

## A thing as tall as a body (Guo's training dummy) standing just in front of the player hides them no longer: it counts
## for the silhouette test, so the body shows through it (the prototype's QA lost the player behind the dummy); a low
## thing (a jar) and a flat one never do.
func _behind_a_dummy(base: Vector2) -> void:
	fresh(base)
	var made: Array = []
	var hidden := {}
	for kind in ["training_dummy", "jar"]:
		var o := {"id": "qa_" + kind, "type": kind, "at": [base.x, base.y + 6.0], "alt": w.room.height_at(base)}
		var art := ObjectView.new()
		art.mode = "art"
		art.setup(o)
		var fig := TopdownPlaces.Figure.new(w.room, o, art, null)
		w.sorted.add_child(fig)
		w.player.motor.place(base)
		w.player.physics_step(1.0 / 60.0)
		w.player.sync(0.0)
		hidden[kind] = w.is_occluded()
		fig.free()
	t.check(hidden.training_dummy and not hidden.jar,
		"topdown: a body just behind a training dummy shows its silhouette through it, a low jar hides nothing (%s)" % str(hidden))

## The hollowed eel turns as other foes do (the tutorial foes' art QA): it glides along the river by its velocity and
## lunges at its target along its aim on the grid, so its figure faces where it goes, not its spawn row.
func _eel_turns(base: Vector2) -> void:
	fresh(base)
	var eel: EnemyState = Game.enemies.spawn_at("hollowed_eel", base + Vector2(-200, 0), 1)
	eel.ai.state = "idle"
	eel.ai.timer = 0.4
	frames(2)
	var fv = w.foe_views.get(eel.uid)
	if fv == null:
		t.check(false, "topdown: the hollowed eel has its figure")
		return
	var gliding := ""
	var lunging := ""
	for i in 90:
		frames(1)
		fv.sync(1.0 / 60.0)
		if gliding == "" and eel.velocity.length() > 1.0: gliding = fv.facing
		if str(eel.ai.state) == "windup": lunging = "%s %s" % [fv.facing, str(eel.aim.round())]
	t.check(gliding in ["e", "ne", "se"] and lunging.begins_with("e") and eel.aim.x > 0.9,
		"topdown: the hollowed eel faces east as it glides toward the player to its east (%s) and lunges along its aim at them (%s)" % [gliding, lunging])
	Game.room_rt.enemies.erase(eel.uid)

