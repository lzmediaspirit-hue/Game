class_name TopdownRoute
extends RefCounted
## Decision 42 · how auto-path and auto-hunt steer a body on the height grid (the Autopilot drives the stick with it):
## round every solid prop (a tree's trunk, a rock, a fence, a hedge, crates, a lantern), a building's walls and the
## water's bank, smoothly and without jitter against a corner, at the sprint the stick's full push gives.
##   - The way: A* over the room's cells by TopdownRoom.find_path's own rules (walking, stairs, drops, a hop a level up;
##     8-way without cutting a corner), so it reaches exactly what find_path reaches and the rooms' reach checks
##     (tools/data/topdown_rooms.py) still speak for it; a cell beside anything that blocks costs a little more
##     (`HUG`), so it keeps to the open lane where there is one. A binary heap keeps it quick on the biggest rooms.
##   - The line: the stick aims at the farthest cell of the way ahead (up to `LOOK`) that a straight line reaches on one
##     floor with the body's foot box, grown by `MARGIN`, clear of every cell that blocks at every point of the line.
##     The grid's steps pull into straight runs and a corner is rounded with the margin to spare. Where no line is
##     clear (a push left the body hugging a wall, a diagonal step onto the side of a stair), it goes by a waypoint it
##     keeps until it is there: its own cell's centre, or the side cell that turns the diagonal into two straight steps.
##     A hop up or a drop is aimed at straight, the hop pressed from the cell before the face (`jump`).
##   - The aim is looked for again every `REAIM_FRAMES` frames, as the way's head changes, or as the body comes to it.

const LOOK := 8          ## cells of the way ahead the line may reach
const MARGIN := 6.0      ## world units kept between the foot box and anything that blocks
const HUG := 0.5         ## the extra cost of a cell beside a prop, a wall or the water
const NEAR_MARGIN := 2.0 ## the margin a line to the very next cell may make do with (a lane a cell wide)
const VIA_STICK := 0.5   ## the stick's push toward a waypoint close at hand: the light touch's careful walk (movement.json tiptoe_axis)
const REAIM_FRAMES := 3
const REPLAN_FRAMES := 15   ## a way lost (a push off it, no way at all) is searched again at most this often

var room: TopdownRoom
var path: Array = []           ## the cells of the way still ahead
var goal_cell := Vector2i(-1, -1)
var jump := false              ## press Jump this frame: the way hops a level up from the cell the body stands in
var aim := Vector2.INF         ## the point the stick aims at
var half := Vector2(8, 5)      ## the foot box's half size (movement.json topdown.box)
var _via := Vector2.INF        ## a waypoint kept until the body is there (no clear line to the way ahead)
var _head := Vector2i(-99, -99)
var _reaim := 0
var _replan := 0
var _no_way := false           ## the last search found no way (searched again only every REPLAN_FRAMES)
var _hop := false

func _init(r: TopdownRoom = null) -> void:
	room = r
	var box: Array = TopdownMotor.conf("box", [16, 10])
	half = Vector2(float(box[0]), float(box[1])) * 0.5

## The stick for a body at `pos` (height `z`, `grounded` or in the air) heading for `target`: a unit vector, ZERO when
## there is no way there, or INF when it is there (within `near` on the plane, on the target's own floor). `jump` says
## whether to press Jump.
func steer(pos: Vector2, z: float, grounded: bool, target: Vector2, near: float) -> Vector2:
	jump = false
	var spot := room.nearest_standable(target)
	# There: within reach of the target, or of the spot a body stands at nearest a target no body can stand on (a drop by
	# a trunk), on its own floor.
	if (pos.distance_to(target) <= near or pos.distance_to(spot) <= minf(near, 8.0)) and absf(z - room.floor_at(spot)) <= 8.0: return Vector2.INF
	if not grounded and aim != Vector2.INF:   # in the air: keep to the hop's or the drop's aim
		var va := aim - pos
		return va.normalized() if va.length() > 0.5 else Vector2.INF
	var cell := TopdownRoom.cell_of(pos)
	var tc := TopdownRoom.cell_of(spot)
	var at := path.find(cell)
	if at >= 0: path = path.slice(at + 1)
	_replan -= 1
	var off := (path.is_empty() and cell != tc) or (not path.is_empty() and _cheb(cell, path[0]) > 1)
	if tc != goal_cell or (off and (_replan <= 0 or not _no_way)):
		goal_cell = tc
		path = find(room, cell, tc, true)
		_no_way = path.is_empty() and cell != tc
		_replan = REPLAN_FRAMES
		_reaim = 0
	if path.is_empty() and cell != tc and not clear(pos, spot, z):
		aim = Vector2.INF
		return Vector2.ZERO   # no way there from here: stand rather than walk into a wall
	var head: Vector2i = path[0] if not path.is_empty() else tc
	_reaim -= 1
	if head != _head or _reaim <= 0 or aim == Vector2.INF or pos.distance_to(aim) <= 6.0:
		if head != _head: _via = Vector2.INF
		_head = head
		_reaim = REAIM_FRAMES
		aim = _aim(pos, z, cell, spot)
	jump = _hop
	var v := aim - pos
	if v.length() <= 0.5: return Vector2.INF
	# Going by a waypoint close at hand, or coming to the spot, the stick eases to the walk band, so the body does not
	# swing past it.
	return v.normalized() * (VIA_STICK if (_via != Vector2.INF or aim == spot) and v.length() < 24.0 else 1.0)

func _aim(pos: Vector2, z: float, cell: Vector2i, spot: Vector2) -> Vector2:
	_hop = false
	if path.is_empty():
		# In the goal's own cell (or no way needed): straight to the spot.
		return spot
	var best := Vector2.INF
	var floor0 := room.cell_floor(cell) if room.cell_floor(cell) < INF else z
	for i in mini(path.size(), LOOK):
		var c: Vector2i = path[i]
		var prev: Vector2i = cell if i == 0 else path[i - 1]
		var step := step_rise(room, prev, c, floor0 if i == 0 else INF)
		var rise := step.x
		if rise > step.y or rise < -8.0:
			# A hop up or a drop: aimed at straight once it is the next cell (the hop pressed from the cell before the
			# face); the line stops before it otherwise.
			if i == 0:
				_via = Vector2.INF
				_hop = rise > 8.0
				return centre(c)
			break
		var p := spot if i == path.size() - 1 and c == goal_cell else centre(c)
		if clear(pos, p, z): best = p
		else:
			# The next cell alone may be reached with the box only NEAR_MARGIN clear (a turn into a lane a cell wide).
			if i == 0 and clear(pos, p, z, NEAR_MARGIN): best = p
			break
	if best != Vector2.INF:
		_via = Vector2.INF
		return best
	# No clear line to the way ahead: a waypoint kept until the body is there.
	if _via != Vector2.INF and pos.distance_to(_via) > 4.0: return _via
	var c0: Vector2i = path[0]
	var vias: Array = []
	if c0.x != cell.x and c0.y != cell.y:
		for side in [Vector2i(c0.x, cell.y), Vector2i(cell.x, c0.y)]:
			if room.cell_floor(side) < INF and absf(room.cell_floor(side) - floor0) <= 16.5: vias.append(centre(side))
	for v in vias:
		if clear(pos, v, z) and clear(v, centre(c0), room.floor_at(v)):
			_via = v
			return v
	_via = centre(cell) if pos.distance_to(centre(cell)) > 4.0 else centre(c0)
	return _via

## A straight line from `from` to `to` on one floor (height `z` at the start): at every point along it the foot box,
## grown by MARGIN, touches no prop, no water and no wall higher than a step, nor leaves the room; the floor under the
## point never jumps by more than a step; and on a stair the motor's own rule holds (no corner of the box higher than a
## step over the floor it stands on).
func clear(from: Vector2, to: Vector2, z: float, margin := MARGIN) -> bool:
	var d := to - from
	var n := maxi(1, ceili(d.length() / maxf(1.0, margin)))   # points a margin apart: the box between two is within one's
	var hz := z
	var box := half + Vector2(margin, margin)
	var last := PackedInt32Array([-1, -1, -1, -1])
	var last_z := INF
	for k in range(1, n + 1):
		var p := from + d * (float(k) / float(n))
		var fz := room.height_at(p)
		if fz == INF or fz == TopdownRoom.WATER_Z or absf(fz - hz) > 8.0: return false
		hz = fz
		var x0 := floori((p.x - box.x) / TopdownRoom.TILE)
		var x1 := floori((p.x + box.x) / TopdownRoom.TILE)
		var y0 := floori((p.y - box.y) / TopdownRoom.TILE)
		var y1 := floori((p.y + box.y) / TopdownRoom.TILE)
		if x0 == last[0] and x1 == last[1] and y0 == last[2] and y1 == last[3] and fz == last_z: continue
		last = PackedInt32Array([x0, x1, y0, y1])
		last_z = fz
		for cy in [y0, y1]:
			for cx in [x0, x1]:
				if _blocks(cx, cy, p, fz): return false
	return true

## Does cell (cx, cy) block a body whose feet are at `p` on the floor `z`: outside the room, a prop's footprint (or its
## walls under a top higher than a step), the water, a floor higher than a step; a stair by the motor's own rule at the
## box's corners.
func _blocks(cx: int, cy: int, p: Vector2, z: float) -> bool:
	var l := room.level(cx, cy)
	if l == TopdownRoom.SOLID or l == TopdownRoom.WATER: return true
	if room.stair_at(cx, cy).is_empty(): return float(l) * TopdownRoom.LEVEL > z + 8.0
	for q in [p - half, Vector2(p.x + half.x, p.y - half.y), Vector2(p.x - half.x, p.y + half.y), p + half]:
		if TopdownRoom.cell_of(q) == Vector2i(cx, cy) and room.height_at(q) > z + 8.0: return true
	return false

static func centre(c: Vector2i) -> Vector2:
	return (Vector2(c) + Vector2(0.5, 0.5)) * TopdownRoom.TILE

static func _cheb(a: Vector2i, b: Vector2i) -> int:
	return maxi(absi(a.x - b.x), absi(a.y - b.y))

## A* from cell `a` to `b` by TopdownRoom.find_path's rules (the same cells reached), with HUG on cells beside anything
## that blocks, on a binary heap. The cells after `a` up to `b`; [] when there is no way (or a == b).
static func find(r: TopdownRoom, a: Vector2i, b: Vector2i, jump: bool) -> Array:
	if a == b or r.cell_floor(b) == INF or not r.inside(a.x, a.y): return []
	var w := r.w
	var n := r.w * r.h
	var g := PackedFloat32Array()
	g.resize(n)
	g.fill(INF)
	var came := PackedInt32Array()
	came.resize(n)
	came.fill(-1)
	var closed := PackedByteArray()
	closed.resize(n)
	var ai := a.y * w + a.x
	var bi := b.y * w + b.x
	g[ai] = 0.0
	var heap: Array = [[_octile(a, b), ai]]
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]
	while not heap.is_empty():
		var top: Array = _pop(heap)
		var ci: int = top[1]
		if closed[ci] == 1: continue
		closed[ci] = 1
		if ci == bi:
			var out: Array = []
			var k := bi
			while k != ai and k >= 0:
				out.push_front(Vector2i(k % w, k / w))
				k = came[k]
			return out
		var cur := Vector2i(ci % w, ci / w)
		var h0 := r.cell_floor(cur)
		if h0 == INF: h0 = r.floor_at(centre(cur))   # the start may be a cell the search would not enter
		for d in dirs:
			var nx: Vector2i = cur + d
			if not r.inside(nx.x, nx.y): continue
			var ni := nx.y * w + nx.x
			if closed[ni] == 1: continue
			var h1 := r.cell_floor(nx)
			if h1 == INF: continue
			if d.x != 0 and d.y != 0 and (r.cell_floor(Vector2i(cur.x + d.x, cur.y)) > h0 + 8.0 or r.cell_floor(Vector2i(cur.x, cur.y + d.y)) > h0 + 8.0): continue
			var step := step_rise(r, cur, nx, h0)
			var rise := step.x
			var cost := 1.414 if d.x != 0 and d.y != 0 else 1.0
			if rise > step.y:
				if not jump or rise > TopdownRoom.LEVEL + 0.5: continue
				cost += 2.0
			elif rise < -8.0: cost += 1.0
			if _beside_block(r, nx, h1): cost += HUG
			var ng := g[ci] + cost
			if ng < g[ni]:
				g[ni] = ng
				came[ni] = ci
				_push(heap, [ng + _octile(nx, b), ni])
	return []

## The rise a body meets stepping from cell `a` to its neighbour `b` (x) and the most it takes without a hop (y): between
## the cells' centres, up to 16.5 up or down a stair along its rise (stairs rise northward) and a step (8) elsewhere; onto
## or off a stair from its side, at the edge between the cells, where the motor's step (8) holds (a stair's side is a
## wall where it has risen more than a step). `h0` stands for a's floor when a's own is not one a body walks (INF: a's).
static func step_rise(r: TopdownRoom, a: Vector2i, b: Vector2i, h0 := INF) -> Vector2:
	var ha := r.cell_floor(a) if h0 == INF else h0
	var hb := r.cell_floor(b)
	var sa := not r.stair_at(a.x, a.y).is_empty()
	var sb := not r.stair_at(b.x, b.y).is_empty()
	if not (sa or sb): return Vector2(hb - ha, 8.0)
	if a.x == b.x: return Vector2(hb - ha, 16.5)
	var edge := (centre(a) + centre(b)) * 0.5
	var ea := r.height_at(edge + (centre(a) - edge).normalized() * 0.5) if sa else ha
	var eb := r.height_at(edge + (centre(b) - edge).normalized() * 0.5) if sb else hb
	return Vector2(eb - ea, 8.0)

## A cell with anything that blocks a body on its floor among its eight neighbours (a stair rising beside it does not).
static func _beside_block(r: TopdownRoom, c: Vector2i, h: float) -> bool:
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			if dx == 0 and dy == 0: continue
			var l := r.level(c.x + dx, c.y + dy)
			if l == TopdownRoom.SOLID or l == TopdownRoom.WATER: return true
			if float(l) * TopdownRoom.LEVEL > h + 8.0 and r.stair_at(c.x + dx, c.y + dy).is_empty(): return true
	return false

static func _octile(a: Vector2i, b: Vector2i) -> float:
	var dx := absi(a.x - b.x)
	var dy := absi(a.y - b.y)
	return float(maxi(dx, dy)) + 0.414 * float(mini(dx, dy))

static func _push(heap: Array, item: Array) -> void:
	heap.append(item)
	var i := heap.size() - 1
	while i > 0:
		var p := (i - 1) / 2
		if float(heap[p][0]) <= float(item[0]): break
		heap[i] = heap[p]
		i = p
	heap[i] = item

static func _pop(heap: Array) -> Array:
	var top: Array = heap[0]
	var last: Array = heap.pop_back()
	if heap.is_empty(): return top
	var i := 0
	var n := heap.size()
	while true:
		var l := i * 2 + 1
		if l >= n: break
		var m := l
		if l + 1 < n and float(heap[l + 1][0]) < float(heap[l][0]): m = l + 1
		if float(heap[m][0]) >= float(last[0]): break
		heap[i] = heap[m]
		i = m
	heap[i] = last
	return top
