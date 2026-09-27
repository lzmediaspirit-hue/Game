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
	_water_skill()
	_roofs()
	_aim_rules()

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
	if Game.active() == null:   # a stand-in, as the prototype makes one from the title
		var slot := 1
		while Game.character("c%d" % slot) != null: slot += 1
		Game.submit({"type": "create_character", "slot": slot, "name": "Topdown", "appearance": {"hair": "topknot", "shirt": "disciple"}, "skip_prologue": true})
		Game.submit({"type": "enter_character", "slot": slot})
	c = Game.active()
	if c == null:
		t.check(false, "topdown fight: a character to fight with")
		return
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
		"topdown: the room's foes spawn by the Enemies authority, each with a placeholder figure and a label (%s)" % str(kinds.keys()))
	var base := Vector2(22.5, 19.5) * 32.0
	_eight_ways(base)
	_heights()
	_shots(base)
	_push_and_dodge(base)
	await _chase_and_leash(base)
	await _drops_and_prompt(tree)
	await _hud_aim(tree, base)
	w.queue_free()
	if is_instance_valid(hud): hud.queue_free()
	await tree.process_frame
	Unlocks.debug_force_all = forced

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
	var hp0: float = c.pools.hp
	Game.combat.enemy_strike(above, above.def.attacks[0])
	var hp1: float = c.pools.hp
	var beside := foe("wild_boarlet", at + Vector2(30, 0), 60)
	beside.aim = Vector2.LEFT
	Game.combat.enemy_strike(beside, beside.def.attacks[0])
	t.check(ground_miss and air_hit and hp1 == hp0 and c.pools.hp < hp1,
		"topdown: a swing misses a foe a level up, a jump strike hits it, and a foe strikes only on its own level (%.0f, %.0f → %.0f)" % [hp0, hp1, c.pools.hp])

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

