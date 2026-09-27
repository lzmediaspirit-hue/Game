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
	_jump_levels()
	_falls_and_windows()
	_collision()
	_water_and_gaps()
	_dash()
	_sort_keys()
	_facing()

func _walk() -> void:
	var m := TopdownMotor.new(grid(flat()), Vector2(80, 192))
	var x0 := m.pos.x
	var to_full := 0.0
	while m.vel.length() < m.walk - 0.01 and to_full < 1.0:
		m.step(1.0 / 120.0, Vector2.RIGHT)
		to_full += 1.0 / 120.0
	run(m, 1.0, Vector2.RIGHT)
	var speed := m.vel.length()
	var x1 := m.pos.x
	var stop_t := 0.0
	while m.vel.length() > 0.0 and stop_t < 1.0:
		m.step(1.0 / 120.0, Vector2.ZERO)
		stop_t += 1.0 / 120.0
	measured.walk = speed
	measured.accel_s = to_full
	measured.stop_s = stop_t
	measured.stop_units = m.pos.x - x1
	t.check(t.near(speed, 154.0) and to_full <= 0.08 + 1.0 / 120.0 and stop_t <= 0.06 + 1.0 / 120.0 and m.pos.x - x1 < 6.0 and x1 > x0,
		"topdown: walk %.1f u/s (4.8 tiles/s), full speed in %.3f s, stops in %.3f s over %.1f units" % [speed, to_full, stop_t, m.pos.x - x1])
	var d := TopdownMotor.new(grid(flat()), Vector2(80, 80))
	run(d, 0.5, Vector2(1, 1).normalized())
	var tip := TopdownMotor.new(grid(flat()), Vector2(80, 80))
	run(tip, 0.5, Vector2(0.5, 0))
	measured.tiptoe = tip.vel.length()
	t.check(t.near(d.vel.length(), 154.0) and absf(d.vel.x - d.vel.y) < 0.01 and t.near(tip.vel.length(), 154.0 * 0.45),
		"topdown: 8-way analog: the diagonal walks at full speed (%.1f), a stick at 0.5 tiptoes at 45%% (%.1f)" % [d.vel.length(), tip.vel.length()])

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
		"topdown: a dash covers %.1f (96 dashing, then walking), a standing back-step %.1f, and waits out its %.1f s cooldown" % [dash_units, back, m.dash_cooldown])

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
	for deg in [0.0, 45.0, 60.0, 40.0, 180.0, -90.0, -135.0]:
		m.step(1.0 / 60.0, Vector2.from_angle(deg_to_rad(deg)))
		rows.append(m.row)
	t.check(rows == ["e", "e", "s", "s", "w", "n", "n"], "topdown: facing picks S/E/N/W with 20° hysteresis on diagonals (%s)" % str(rows))

## The prototype room's view: its layout, the silhouette behind the house, sort order and whole-pixel placement.
func run_view(suite, tree: SceneTree) -> void:
	t = suite
	var w = TopdownWorld.new()
	tree.root.add_child(w)
	await tree.process_frame
	var room: TopdownRoom = w.room
	var levels := {}
	for l in room.levels: levels[l] = true
	t.check(levels.has(0) and levels.has(1) and levels.has(TopdownRoom.WATER) and room.stairs.size() >= 1 and room.props.any(func(p): return p.kind == "house"),
		"topdown: the prototype square has two levels, water, stairs and a house (%s)" % str(levels.keys()))
	t.check(w.viewport.size == Vector2i(640, 360) and w.container.stretch_shrink == 2 and w.viewport.snap_2d_transforms_to_pixel, "topdown: the world renders at 640x360 shown x2")
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
