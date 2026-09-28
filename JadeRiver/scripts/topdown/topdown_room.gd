class_name TopdownRoom
extends RefCounted
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1.2): a room as a height grid. Each 16-art-px cell
## (32 world units) holds a level (0–9, one level = one tile = 32 units of height) or water (-1); stairs rise across
## a rect; props stand on footprints that block. A prop with a `top` (a building's roof, a stack of crates) is a raised
## floor that many levels over its ground: a wall from below, a surface to stand on (decision 29). Queries are in world
## units on the ground plane (x, depth y) with the height z, the same model as ActorState (plane + altitude). The
## side-view rooms do not use it. Phase 2 adds the room's foes (`spawns`, in tiles) and a path search on the grid.

const TILE := 32.0
const LEVEL := 32.0
const ART := 2.0          ## world units per art px
const WATER := -1
const WATER_Z := -16.0    ## the water's surface: half a level under the ground, so a narrow gap still shows water
const SOLID := 99
const DIR := "res://data/topdown/"

var id := ""
var title := ""
var w := 0
var h := 0
var levels := PackedInt32Array()
var paint := PackedByteArray()
var solid := PackedByteArray()
var stair_of := PackedInt32Array()   ## index into stairs + 1, 0 = none
var top_of := PackedInt32Array()     ## index into props + 1 for a prop with a standable top, 0 = none
var stairs: Array = []               ## {rect: Rect2i, from, to}
var props: Array = []                ## {kind, cell: Vector2i, size: Vector2i, level, art: Dictionary}
var spawn := Vector2.ZERO            ## world units
var tileset: Dictionary = {}
var def: Dictionary = {}             ## the room's own file, for its spawns and kind

static func load_room(room_id: String) -> TopdownRoom:
	var d = JSON.parse_string(FileAccess.get_file_as_string(DIR + room_id + ".json"))
	var ts = JSON.parse_string(FileAccess.get_file_as_string(DIR + "proto_tileset.json"))
	return from_dict(d if d is Dictionary else {}, ts if ts is Dictionary else {})

static var _layouts: Dictionary = {}
## Phase 4: a room of the world redrawn on the grid has a layout of its own id in data/topdown/ (built by
## tools/data/topdown_rooms.py); the rooms without one stay side-view.
static func has_layout(room_id: String) -> bool:
	if not _layouts.has(room_id): _layouts[room_id] = room_id != "" and not room_id.begins_with("td_") and FileAccess.file_exists(DIR + room_id + ".json")
	return bool(_layouts[room_id])

static func from_dict(d: Dictionary, ts: Dictionary = {}) -> TopdownRoom:
	var r := TopdownRoom.new()
	r.id = str(d.get("id", ""))
	r.title = str(d.get("name", r.id))
	r.tileset = ts
	var rows: Array = d.get("levels", [])
	r.h = rows.size()
	r.w = str(rows[0]).length() if r.h > 0 else 0
	r.levels.resize(r.w * r.h)
	r.paint.resize(r.w * r.h)
	r.solid.resize(r.w * r.h)
	r.stair_of.resize(r.w * r.h)
	r.top_of.resize(r.w * r.h)
	r.def = d
	var paint_rows: Array = d.get("paint", [])
	for y in r.h:
		for x in r.w:
			var ch := str(rows[y])[x]
			r.levels[y * r.w + x] = WATER if ch == "~" else int(ch)
			r.paint[y * r.w + x] = str(paint_rows[y]).unicode_at(x) if y < paint_rows.size() else 103
	for s in d.get("stairs", []):
		r.stairs.append({"rect": Rect2i(int(s.x), int(s.y), int(s.w), int(s.h)), "from": int(s.from), "to": int(s.to)})
		for y in int(s.h):
			for x in int(s.w): r.stair_of[(int(s.y) + y) * r.w + int(s.x) + x] = r.stairs.size()
	for p in d.get("props", []):
		var art: Dictionary = ts.get("props", {}).get(str(p.kind), {})
		var fp: Array = art.get("footprint", [1, 1])
		var cell := Vector2i(int(p.x), int(p.y))
		var base := r.levels[(cell.y + int(fp[1]) - 1) * r.w + cell.x]
		r.props.append({"kind": str(p.kind), "cell": cell, "size": Vector2i(int(fp[0]), int(fp[1])), "level": base, "art": art,
			"top": base + int(art.top) if art.has("top") else -1, "door": p.get("door", [])})
		if art.get("solid", true):
			for y in int(fp[1]):
				for x in int(fp[0]):
					if not r.inside(cell.x + x, cell.y + y): continue
					r.solid[(cell.y + y) * r.w + cell.x + x] = 1
					if art.has("top"): r.top_of[(cell.y + y) * r.w + cell.x + x] = r.props.size()
	var sp: Array = d.get("spawn", [1, 1])
	r.spawn = Vector2((float(sp[0]) + 0.5) * TILE, (float(sp[1]) + 0.5) * TILE)
	return r

func inside(cx: int, cy: int) -> bool:
	return cx >= 0 and cy >= 0 and cx < w and cy < h

## The cell's level for standing: SOLID outside the room and under a blocking prop, a prop's top where it has one, -1
## for water.
func level(cx: int, cy: int) -> int:
	if not inside(cx, cy): return SOLID
	if top_of[cy * w + cx] > 0: return int(props[top_of[cy * w + cx] - 1].top)
	if solid[cy * w + cx] == 1: return SOLID
	return levels[cy * w + cx]

## The prop whose top this cell is ({} when none).
func top_at(cx: int, cy: int) -> Dictionary:
	return props[top_of[cy * w + cx] - 1] if inside(cx, cy) and top_of[cy * w + cx] > 0 else {}

func is_water(cx: int, cy: int) -> bool:
	return inside(cx, cy) and solid[cy * w + cx] == 0 and levels[cy * w + cx] == WATER

func paint_at(cx: int, cy: int) -> String:
	return char(paint[cy * w + cx]) if inside(cx, cy) else ""

func stair_at(cx: int, cy: int) -> Dictionary:
	return stairs[stair_of[cy * w + cx] - 1] if inside(cx, cy) and stair_of[cy * w + cx] > 0 else {}

static func cell_of(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / TILE), floori(p.y / TILE))

## The top of the floor under a ground point, in world units (INF where nothing can stand). Stairs rise linearly from
## their south edge (`from`) to their north edge (`to`).
func height_at(p: Vector2) -> float:
	var cp := cell_of(p)
	var st := stair_at(cp.x, cp.y)
	if not st.is_empty():
		var r: Rect2i = st.rect
		var k := clampf((float(r.end.y) * TILE - p.y) / (float(r.size.y) * TILE), 0.0, 1.0)
		return lerpf(float(st.from), float(st.to), k) * LEVEL
	var l := level(cp.x, cp.y)
	return INF if l == SOLID else WATER_Z if l == WATER else float(l) * LEVEL

## The ground point's cell: the south edge of what the point stands on, in art px. A raised level sorts by the south
## edge of its own row; stairs by the south edge of the whole flight (plan §1.3); a prop's top just past the prop's own
## key (its footprint's south edge + 0.5), so a body on a roof draws over the building.
func south_edge(p: Vector2) -> float:
	var cp := cell_of(p)
	var top := top_at(cp.x, cp.y)
	if not top.is_empty(): return float((top.cell as Vector2i).y + (top.size as Vector2i).y) * TILE / ART + 0.5
	var st := stair_at(cp.x, cp.y)
	return float((st.rect as Rect2i).end.y if not st.is_empty() else cp.y + 1) * TILE / ART

## The depth-sort key of a body at ground point `p` and height `z`, in art px (plan §1.3 and research §4.2): its ground
## y, raised just past the south edge of the raised floor it stands on or above; ties go to the higher body. Keys are
## multiples of 1/64 so the draw offset that undoes them stays exact.
func sort_key(p: Vector2, z: float) -> float:
	var key := p.y / ART
	var ground := height_at(p)
	if ground > 0.0 and ground < INF and z >= ground - 1.0: key = maxf(key, south_edge(p) + 0.25)
	return (floorf(key * 16.0) + clampf(floorf(z / LEVEL), 0.0, 3.0) * 0.25) / 16.0

## The room's size in art px.
func art_size() -> Vector2:
	return Vector2(w, h) * TILE / ART

# ------------------------------------------------------------------ Phase 2: foes on the grid
## The room as the simulation's RoomRuntime def (WorldAuthority.enter_grid_room): its id, name and kind, and its spawns
## with their points moved from tiles to world units (cell centres).
func runtime_def() -> Dictionary:
	var out := {"id": id, "name": title, "type": str(def.get("type", "field")), "region": str(def.get("region", "")), "view": "topdown",
		"bounds": [0, 0, w * TILE, h * TILE], "spawn_point": [spawn.x, spawn.y], "spawns": []}
	for sp in def.get("spawns", []):
		var spec: Dictionary = (sp as Dictionary).duplicate(true)
		spec.points = (sp.get("points", []) as Array).map(func(q): return [(float(q[0]) + 0.5) * TILE, (float(q[1]) + 0.5) * TILE])
		out.spawns.append(spec)
	return out

## Where a body of `radius` may stand at height `z` (a foe's footing): every corner of its box on a floor no higher than
## `z + step`, never water, a prop or the room's edge.
func free_at(p: Vector2, z: float, radius: float, step := 8.0) -> bool:
	for c in [p + Vector2(-radius, -radius), p + Vector2(radius, -radius), p + Vector2(-radius, radius), p + Vector2(radius, radius)]:
		var cp := cell_of(c)
		var l := level(cp.x, cp.y)
		if l == SOLID or l == WATER or height_at(c) > z + step: return false
	return true

## A path of cells from `a` to `b` for a foe that walks, climbs stairs, drops down any edge and (with `jump`) hops one
## level up: A* on the 8-way grid without cutting corners. Returns the cells after `a` up to `b`; [] when there is none.
func find_path(a: Vector2i, b: Vector2i, jump: bool, limit := 700) -> Array:
	if a == b or cell_floor(b) == INF: return []
	var open := {a: 0.0}
	var came := {}
	var g := {a: 0.0}
	var n := 0
	while not open.is_empty() and n < limit:
		n += 1
		var cur: Vector2i = a
		var best := INF
		for k in open:
			if float(open[k]) < best:
				best = float(open[k])
				cur = k
		if cur == b:
			var path: Array = [b]
			while came.has(path[0]) and came[path[0]] != a: path.push_front(came[path[0]])
			return path
		open.erase(cur)
		var h0 := cell_floor(cur)
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]:
			var nx: Vector2i = cur + d
			var h1 := cell_floor(nx)
			if h1 == INF: continue
			if d.x != 0 and d.y != 0 and (cell_floor(Vector2i(cur.x + d.x, cur.y)) > h0 + 8.0 or cell_floor(Vector2i(cur.x, cur.y + d.y)) > h0 + 8.0): continue
			var rise := h1 - h0
			var on_stairs := not stair_at(nx.x, nx.y).is_empty() or not stair_at(cur.x, cur.y).is_empty()
			var cost := 1.414 if d.x != 0 and d.y != 0 else 1.0
			if rise > (16.5 if on_stairs else 8.0):
				if not jump or rise > LEVEL + 0.5: continue
				cost += 2.0
			elif rise < -8.0: cost += 1.0
			var ng: float = float(g[cur]) + cost
			if ng < float(g.get(nx, INF)):
				g[nx] = ng
				came[nx] = cur
				open[nx] = ng + Vector2(nx - b).length()
	return []

## A cell's floor at its centre for the path search: INF where no foe may stand (a prop, the room's edge, water).
func cell_floor(c: Vector2i) -> float:
	var l := level(c.x, c.y)
	if l == SOLID or l == WATER: return INF
	return height_at((Vector2(c) + Vector2(0.5, 0.5)) * TILE)

# ------------------------------------------------------------------ Phase 4: a room of the world on the grid
## Keys of a side-view room that describe its strip (surfaces, painted art, the side camera); a room on the grid keeps
## everything else of its side-view definition (ids, NPCs, quests' objects, portals and their rules, foes, events).
const SIDE_ONLY := ["surfaces", "blocks", "climbables", "volumes", "movers", "scenery", "decor", "wall", "areas", "camera", "districts",
	"custom_ground", "vertical", "terrain"]
## The way a portal is taken, outward from the room: a door in a building's front is walked into northward, an
## interior's door southward, an edge through its side.
const DIRS := {"n": Vector2.UP, "s": Vector2.DOWN, "e": Vector2.RIGHT, "w": Vector2.LEFT}

## A layout's cell (x, y; fractions allowed) as a ground point: the cell's centre.
static func cell_point(at: Array) -> Vector2:
	return Vector2((float(at[0]) + 0.5) * TILE, (float(at[1]) + 0.5) * TILE)

## Cells as [x, y] ground points (a spawn's list).
static func cell_points(cells: Array) -> Array:
	var out: Array = []
	for q in cells:
		var p := cell_point(q)
		out.append([p.x, p.y])
	return out

## The floor under a point for something set on it (an object, a foe's spawn): 0 where nothing can stand.
func floor_at(p: Vector2) -> float:
	var z := height_at(p)
	return 0.0 if z == INF else maxf(z, 0.0)

## Can a body stand on this cell (no prop's wall, no water, inside the room)?
func standable(c: Vector2i) -> bool:
	var l := level(c.x, c.y)
	return l != SOLID and l != WATER

## The nearest point a body can stand at: `p` itself when its cell is standable, else the centre of the nearest
## standable cell (a saved spot or a shrine's step that falls in a wall or the water).
func nearest_standable(p: Vector2) -> Vector2:
	var c0 := cell_of(p)
	if standable(c0): return p
	for r in range(1, maxi(w, h)):
		var best := Vector2.INF
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r or not standable(c0 + Vector2i(dx, dy)): continue
				var q := (Vector2(c0 + Vector2i(dx, dy)) + Vector2(0.5, 0.5)) * TILE
				if best == Vector2.INF or q.distance_to(p) < best.distance_to(p): best = q
		if best != Vector2.INF: return best
	return spawn

## What shows a way where it is (the top-down view's PortalView.entrance, docs/tutorial_order.md): "building" (in the
## doorway under a building's door art: a prop's `door` columns, the row under its footprint), "wall" (a gap in an
## interior's front wall at the room's edge), "edge" (walked out through the room's side), "" (nothing shows it).
func entrance(portal_id: String) -> String:
	var lay: Dictionary = def.get("portals", {}).get(portal_id, {})
	if lay.is_empty(): return ""
	var c := cell_of(cell_point(lay.at))
	var d: Vector2 = DIRS.get(str(lay.get("dir", "s")), Vector2.DOWN)
	if d == Vector2.UP:
		for p in props:
			var door: Array = p.door
			var pc: Vector2i = p.cell
			if door.size() == 2 and c.y == pc.y + (p.size as Vector2i).y and c.x >= pc.x + int(door[0]) and c.x <= pc.x + int(door[1]): return "building"
		return ""
	var out := c + Vector2i(d)
	if inside(out.x, out.y): return ""
	# At the room's edge: an interior's door is a gap in its wall (raised cells on both sides of the way).
	var side := Vector2i(int(d.y), int(d.x))
	for k in [2, -2]:
		var s: Vector2i = c + side * k
		if inside(s.x, s.y) and levels[s.y * w + s.x] > levels[c.y * w + c.x]: return "wall"
	return "edge"

## Where a body stands to reach a thing at `p` at height `z` (the World authority answers within 48 of its height):
## the standable spot within three tiles of it, its floor within 40 of `z`, nearest `from`; else the nearest spot.
func spot_near(p: Vector2, z: float, from: Vector2) -> Vector2:
	var c0 := cell_of(p)
	var best := Vector2.INF
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			var c := c0 + Vector2i(dx, dy)
			if dx * dx + dy * dy > 9 or not standable(c): continue
			var q := (Vector2(c) + Vector2(0.5, 0.5)) * TILE
			if absf(floor_at(q) - z) > 40.0: continue
			if best == Vector2.INF or q.distance_to(from) < best.distance_to(from): best = q
	return best if best != Vector2.INF else nearest_standable(p)

## The stand-in geometry of a room on the grid: one ground surface over the whole room, so every rule that asks the
## side view's geometry (the ground under a point, a free spot) has an answer; heights come from the grid.
func geometry_def() -> Dictionary:
	return {"bounds": [0, 0, w * TILE, h * TILE], "surfaces": [{"id": "grid", "rect": [0, 0, w * TILE, h * TILE], "stratum": "ground"}]}

## The RoomRuntime definition of a room of the world on the grid: its side-view definition (every id, rule, NPC,
## object, portal, spawn and event kept) with the places taken from the layout, in world units on the grid's plane:
##   place    object id -> cell: where it stands; its `alt` is the floor there (a roof, a loft, a terrace);
##   portals  portal id -> {at: the doorway or edge cell, dir: n/s/e/w (the way it is walked into), arrive: the cell
##            the body arrives on (default a tile and a half inside), span: tiles along the edge it covers};
##   spawns   one list of cells per side-view spawn, in order; event {wave, fixed}: the room event's spawn cells;
##   routes   object id -> [[cell x, cell y, seconds], ...]: a rooftop thief's run over the grid.
## A timed route (the Cloud Steps) finishes at its room's route_finish object, where the layout places it.
func merge_def(side: Dictionary) -> Dictionary:
	var out := side.duplicate(true)
	for k in SIDE_ONLY: out.erase(k)
	out.view = "topdown"
	out.bounds = [0, 0, w * TILE, h * TILE]
	out.spawn_point = [spawn.x, spawn.y]
	var place: Dictionary = def.get("place", {})
	var routes: Dictionary = def.get("routes", {})
	var finish := {}
	for o in out.get("objects", []):
		var id := str(o.get("id", ""))
		if place.has(id):
			var p := cell_point(place[id])
			o.at = [p.x, p.y]
			o.alt = floor_at(p)
			if str(o.get("type", "")) == "route_finish": finish = o
		if o.has("chase") and routes.has(id):
			var route: Array = []
			for q in routes[id]:
				var rp := cell_point(q)
				route.append([rp.x, rp.y, floor_at(rp), float(q[2]) if (q as Array).size() > 2 else 0.5])
			o.chase.route = route
	for o in out.get("objects", []):
		if not finish.is_empty() and o.get("route") is Dictionary and (o.route as Dictionary).has("finish"):
			o.route.finish.at = finish.at
			o.route.finish.alt = finish.alt
	var ways: Dictionary = def.get("portals", {})
	for p in out.get("portals", []):
		var lay: Dictionary = ways.get(str(p.get("id", "")), {})
		if lay.is_empty(): continue
		var at := cell_point(lay.at)
		var dir: Vector2 = DIRS.get(str(lay.get("dir", "s")), Vector2.DOWN)
		var arrive := cell_point(lay.arrive) if lay.has("arrive") else at - dir * TILE * 1.5
		p.at = [at.x, at.y]
		p.dir = [dir.x, dir.y]
		p.arrive = [arrive.x, arrive.y]
		p.alt = floor_at(at)
		# The reach round it that counts as at the way (WorldAuthority.PORTAL_RADIUS, 64 x 44): a doorway's own width, an
		# edge's span.
		var span := float(lay.get("span", 2 if str(p.get("type", "edge")) in ["door"] else 3))
		p.radius_scale = maxf(0.5, span * TILE * 0.5 / 44.0)
		p.erase("press_up")
		p.erase("arrive_offset")
		p.erase("arrive_dy")
	var spawn_cells: Array = def.get("spawns", [])
	var specs: Array = out.get("spawns", [])
	for i in mini(specs.size(), spawn_cells.size()):
		specs[i].points = cell_points(spawn_cells[i])
		specs[i].erase("surface")
	var ev: Dictionary = out.get("event", {})
	var lay_ev: Dictionary = def.get("event", {})
	if not ev.is_empty() and not lay_ev.is_empty():
		if ev.has("wave") and lay_ev.has("wave"): ev.wave.points = cell_points(lay_ev.wave)
		var fixed: Array = lay_ev.get("fixed", [])
		for i in mini((ev.get("fixed_spawns", []) as Array).size(), fixed.size()):
			var fp := cell_point(fixed[i])
			ev.fixed_spawns[i].at = [fp.x, fp.y]
	return out
