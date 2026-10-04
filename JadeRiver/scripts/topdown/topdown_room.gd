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
## Decision 43: the people (the player, the villagers, a companion in their outfit) are drawn this many times the
## 38 art px they were first drawn at: about 46 art px from sole to crown. What is sized against a person follows it.
const PEOPLE := 1.2
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
## T1: the side view's rafts, updrafts and climbable faces on this grid (a TopdownTraverse, made by TopdownTraverse.of
## from the layout's `traverse`; untyped, so this class never names it and none of its queries count it).
var traverse = null

## A room's layout from `dir` (data/topdown/; a review room the tools draw sits outside data/, which ships).
static func load_room(room_id: String, dir := DIR) -> TopdownRoom:
	var d = JSON.parse_string(FileAccess.get_file_as_string(dir + room_id + ".json"))
	var ts = JSON.parse_string(FileAccess.get_file_as_string(DIR + "proto_tileset.json"))
	if ts is Dictionary: ts["foes"] = foes()
	return from_dict(d if d is Dictionary else {}, ts if ts is Dictionary else {})

static var _foes = null
## Decision 43: the foes' index (data/topdown/foes.json, built by tools/art/topdown/build_foes.py: a sheet, a cell and
## the frames of every action per species, an elite's rows beside its own), read once and laid into the tile set as its
## `foes`.
static func foes() -> Dictionary:
	if _foes == null:
		var f = JSON.parse_string(FileAccess.get_file_as_string(DIR + "foes.json"))
		_foes = f if f is Dictionary else {}
	return _foes

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
	# Decision 43: a place's sight blocks its cells as a prop's footprint does (a stall's counter, the Storehouse's shed).
	for s in PlaceRules.solids(r.id):
		for y in (s as Rect2i).size.y:
			for x in (s as Rect2i).size.x:
				if r.inside(s.position.x + x, s.position.y + y): r.solid[(s.position.y + y) * r.w + s.position.x + x] = 1
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

## The depth-sort key of a mark lying flat on the floor at `p` (height `z`), `half` art px deep (a hazard's ring, a
## circle of runes): under every body standing on it or behind it, over the floor it lies on. On a raised floor that
## is just past the floor's own row (its south edge, before the bodies on it at +0.25); on the ground it is the mark's
## north edge. Multiples of 1/64, as every key.
func decal_key(p: Vector2, z: float, half := 12.0) -> float:
	var ground := height_at(p)
	if ground > 0.0 and ground < INF and z >= ground - 1.0: return south_edge(p) + 0.125
	return floorf((p.y / ART - half) * 64.0) / 64.0

## The room's size in art px.
func art_size() -> Vector2:
	return Vector2(w, h) * TILE / ART

# ------------------------------------------------------------------ Phase 4: what the camera shows
## The world view in art px (TopdownWorld's SubViewport): 1280 x 720 world units.
const VIEW := Vector2(640, 360)
## A body's figure over its feet in art px (the character's 46 px, decision 43, and a little head room), for keeping it
## in view.
const BODY_PX := Vector2(20, 52)

var _drawn := Rect2()
## Where the room draws, in art px: the floor's rect, and above it the tops of raised floors near the north edge (a
## ridge of level 2 on the first row draws 32 px above the room's top), which the camera may show.
func drawn_rect() -> Rect2:
	if _drawn.has_area(): return _drawn
	var top := 0.0
	for y in h:
		if float(y) * TILE / ART - 9.0 * LEVEL / ART > top: break   # no level can reach above the top from here on
		for x in w:
			var l := level(x, y)
			if l > 0 and l != SOLID: top = minf(top, (float(y) * TILE - float(l) * LEVEL) / ART)
	_drawn = Rect2(0.0, top, float(w) * TILE / ART, float(h) * TILE / ART - top)
	return _drawn

## Decision 43: what the camera may show, the drawn room and the land past its edges its layout's `vista` opens
## (TopdownVista draws it; tools/data/topdown_life.py sets how far past each edge).
func shown_rect() -> Rect2:
	var b := drawn_rect()
	for v in def.get("vista", []):
		var pad := float(v.get("pad", 0))
		match str(v.get("edge", "")):
			"n": b = b.grow_individual(0.0, pad, 0.0, 0.0)
			"s": b = b.grow_individual(0.0, 0.0, 0.0, pad)
			"w": b = b.grow_individual(pad, 0.0, 0.0, 0.0)
			"e": b = b.grow_individual(0.0, 0.0, pad, 0.0)
	return b

## The camera's centre (art px) for a goal `t` (art px): inside the drawn room (and the vista past its edges, decision
## 43), and a room smaller than the view is centred. `keep` (art px) always stays in view, the camera moving past the
## room's drawn edge only as far as it must: the body standing on a ridge at the room's very edge.
func camera_goal(t: Vector2, keep := Rect2()) -> Vector2:
	var b := shown_rect()
	var half := VIEW * 0.5
	var c := Vector2(b.get_center().x if b.size.x <= VIEW.x else clampf(t.x, b.position.x + half.x, b.end.x - half.x),
		b.get_center().y if b.size.y <= VIEW.y else clampf(t.y, b.position.y + half.y, b.end.y - half.y))
	if keep.has_area():
		c.x = clampf(c.x, keep.end.x - half.x, keep.position.x + half.x)
		c.y = clampf(c.y, keep.end.y - half.y, keep.position.y + half.y)
	return c

## The camera's goal for a body at `p` whose ground underfoot is `z`, moving at `vel` (TopdownWorld's camera, plan
## §1.1): its feet on that ground plus the look-ahead, 12 art px up, the body kept in view.
func camera_for(p: Vector2, z: float, vel := Vector2.ZERO) -> Vector2:
	var feet := Vector2(p.x, p.y - z) / ART
	var t := feet + vel * float(TopdownMotor.conf("camera_look_ahead", 0.2)) / ART + Vector2(0, -14)
	return camera_goal(t, Rect2(feet - Vector2(BODY_PX.x * 0.5, BODY_PX.y), BODY_PX + Vector2(0, 8)))

## What the camera shows with a body at `p` on the floor at `z`, at rest: a rect in world units on the screen's plane
## (x, and y lifted by height), 1280 x 720 as the 640 x 360 view is.
func view_rect(p: Vector2, z: float) -> Rect2:
	return Rect2(camera_for(p, z) * ART - VIEW, VIEW * 2.0)

# ------------------------------------------------------------------ Phase 4: placing things on the floor
## The nearest point to `p` a body can stand at on the floor at height `z` (within 8 of it), searching `rings` tiles
## out; else the nearest standable point. Things put into the room by the rules (a spar partner, a summoned add, an
## ambush, a guardian, a companion beside you) land on a floor, never in a wall, the water or on another level.
func place_near(p: Vector2, z: float, rings := 4) -> Vector2:
	var c0 := cell_of(p)
	if standable(c0) and absf(floor_at(p) - z) <= 8.0 and free_at(p, floor_at(p), 8.0): return p
	for r in range(1, rings + 1):
		var best := Vector2.INF
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r: continue
				var q := (Vector2(c0 + Vector2i(dx, dy)) + Vector2(0.5, 0.5)) * TILE
				if not standable(cell_of(q)) or absf(floor_at(q) - z) > 8.0: continue
				if best == Vector2.INF or q.distance_to(p) < best.distance_to(p): best = q
		if best != Vector2.INF: return best
	return nearest_standable(p)

# ------------------------------------------------------------------ T1: a room event's points on the grid
## docs/architecture/topdown_mechanics.md, "Set pieces on the grid". One rule for every room event begun in a room on
## the grid (WorldRoomEvents.start_event passes each through grid_event): a set piece's waves, a Temper trial, a Trial
## Tower floor, the Beast Trial Grove, the sect's defence and a mine's, a rift, a treasure birth, the heart demons.
## The side view calls their foes to points in its own room; here each point is, in order:
##   1. the room's own event, which merge_def already set on the layout's cells (`on_grid`), as it is;
##   2. the layout's cells for the event: its `stage` row (cells dealt out point by point, in the event's order), else
##      the layout's `event` cells group by group (wave, waves, fixed, timed: the room's event, or the one set piece
##      begun there, as at the Scripture Well);
##   3. else the side view's point mapped across the room (as far across and as deep as it stands in the side-view room,
##      a cell and a half in from the edges), or a point already on the grid's plane (`on_plane`: a rift round the
##      player, a birth round its tree), moved to the nearest open cell (open_cell_near) the player walks to.

## A room event with its points on this grid (`from`: where the player stands; `side_bounds`: the side-view room's
## [x, y, w, h], RoomRuntime's `side_bounds`). Marked `on_grid`: passed again, it is as it is.
func grid_event(ev: Dictionary, from := Vector2.INF, side_bounds: Array = []) -> Dictionary:
	if ev.get("on_grid", false): return ev
	var out := ev.duplicate(true)
	var ctx := _event_ctx(from, side_bounds, bool(out.get("on_plane", false)))
	var row = def.get("stage", {}).get(str(out.get("id", "")))
	if row is Array and not ctx.plane: ctx.flat = row
	var lay: Dictionary = def.get("event", {}) if (ctx.flat as Array).is_empty() and not ctx.plane else {}
	if out.get("wave") is Dictionary:
		out.wave.points = _event_cells(out.wave.get("points", []), lay.get("wave", []), ctx)
	var groups: Array = lay.get("waves", [])
	for i in (out.get("waves", []) as Array).size():
		out.waves[i].points = _event_cells(out.waves[i].get("points", []), groups[i] if i < groups.size() else [], ctx)
	for key in [["fixed_spawns", "fixed"], ["timed_spawns", "timed"]]:
		var cells: Array = lay.get(key[1], [])
		var rows: Array = out.get(key[0], [])
		for i in rows.size():
			rows[i].at = _event_cells([rows[i].get("at", [0, 0])], [cells[i]] if i < cells.size() else [], ctx, true)[0]
	out.on_grid = true
	return out

## Loose points by the same rule (the heart demons a Reflection brings): mapped from the side view unless `plane`.
func grid_points(pts: Array, from := Vector2.INF, side_bounds: Array = [], plane := false) -> Array:
	return _event_cells(pts, [], _event_ctx(from, side_bounds, plane))

func _event_ctx(from: Vector2, side_bounds: Array, plane: bool) -> Dictionary:
	return {"reach": reached_from(cell_of(from)) if from.is_finite() else {}, "taken": {}, "bounds": side_bounds, "plane": plane,
		"flat": [], "dealt": 0}

## A group's points on the grid: the layout's `cells` for the group (all of them, as merge_def lays a room's own event;
## `each`: one for one), else the stage's cells dealt out in order, else each point mapped and set on open ground.
func _event_cells(pts: Array, cells: Array, ctx: Dictionary, each := false) -> Array:
	if not cells.is_empty() and not each: return cell_points(cells)
	var out: Array = []
	for i in pts.size():
		var q: Vector2
		if not cells.is_empty(): q = cell_point(cells[mini(i, cells.size() - 1)])
		elif not (ctx.flat as Array).is_empty():
			q = cell_point(ctx.flat[int(ctx.dealt) % (ctx.flat as Array).size()])
			ctx.dealt = int(ctx.dealt) + 1
		else:
			var p := Vector2(float(pts[i][0]), float(pts[i][1]))
			if not bool(ctx.plane): p = side_point(p, ctx.bounds)
			q = open_cell_near(p, ctx.reach, ctx.taken)
			var qc := cell_of(q)
			for dy in range(-1, 2):
				for dx in range(-1, 2): ctx.taken[qc + Vector2i(dx, dy)] = true   # the event's next point a cell apart
		out.append([q.x, q.y])
	return out

## A side-view point mapped onto this grid: as far across and as deep as it stands in the side-view room (`bounds`, its
## [x, y, w, h]), a cell and a half in from the grid's edges (a foe is never called onto the room's rim).
func side_point(p: Vector2, bounds: Array) -> Vector2:
	var b := Rect2(float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])) if bounds.size() == 4 else Rect2(0, 480, 1280, 480)
	var f := ((p - b.position) / b.size).clamp(Vector2.ZERO, Vector2.ONE)
	return Vector2(1.5 + f.x * float(w - 3), 1.5 + f.y * float(h - 3)) * TILE

## Every cell a body walks to from `from` (walking, stairs, drops and a hop a level up, as find_path and auto-path go):
## a set of Vector2i.
func reached_from(from: Vector2i) -> Dictionary:
	var seen := {}
	if cell_floor(from) == INF: return seen
	seen[from] = true
	var queue: Array = [from]
	var head := 0
	while head < queue.size():
		var c: Vector2i = queue[head]
		head += 1
		var h0 := cell_floor(c)
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if seen.has(n): continue
			var h1 := cell_floor(n)
			if h1 == INF or h1 - h0 > LEVEL + 0.5: continue
			seen[n] = true
			queue.append(n)
	return seen

## The open cell nearest a ground point where a room event sets a foe: a floor (no wall, prop or water), not a stair, at
## least three cells from every way in or out, in `reach` (the cells the player walks to; empty: anywhere) and not in
## `taken` (the event's other points, kept a cell apart). Its centre, or the nearest standable point when none is open.
func open_cell_near(p: Vector2, reach: Dictionary, taken: Dictionary) -> Vector2:
	var c0 := cell_of(p.clamp(Vector2.ZERO, Vector2(w - 1, h - 1) * TILE + Vector2.ONE * (TILE - 1.0)))
	var ways: Array = []
	for pid in def.get("portals", {}):
		var at: Array = def.portals[pid].get("at", [0, 0])
		ways.append(Vector2(float(at[0]), float(at[1])))
	for r in maxi(w, h):
		var best := Vector2i(-1, -1)
		var best_d := INF
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r: continue
				var c := c0 + Vector2i(dx, dy)
				if not standable(c) or not stair_at(c.x, c.y).is_empty() or taken.has(c): continue
				if not reach.is_empty() and not reach.has(c): continue
				if ways.any(func(a): return maxf(absf(a.x - float(c.x)), absf(a.y - float(c.y))) < 3.0): continue
				var d := (Vector2(c) + Vector2(0.5, 0.5)).distance_to(p / TILE)
				if d < best_d:
					best_d = d
					best = c
		if best.x >= 0: return (Vector2(best) + Vector2(0.5, 0.5)) * TILE
	return nearest_standable(p)

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
	# The four corners in turn, each read straight off the grid (every foe asks this several times a tick, and a chase's
	# clear line a dozen times more: the list and the calls it made were most of the foes' steering).
	var top := z + step
	return _corner_free(p + Vector2(-radius, -radius), top) and _corner_free(p + Vector2(radius, -radius), top) \
		and _corner_free(p + Vector2(-radius, radius), top) and _corner_free(p + Vector2(radius, radius), top)

## A corner of `free_at`: inside the room, on neither a wall nor the water, its floor no higher than `top` (the cell's
## `level` and `height_at`, read once).
func _corner_free(c: Vector2, top: float) -> bool:
	var cx := floori(c.x / TILE)
	var cy := floori(c.y / TILE)
	if cx < 0 or cy < 0 or cx >= w or cy >= h: return false
	var i := cy * w + cx
	var l: int
	if top_of[i] > 0: l = int(props[top_of[i] - 1].top)
	elif solid[i] == 1: return false
	else: l = levels[i]
	if l == SOLID or l == WATER: return false
	if stair_of[i] > 0: return height_at(c) <= top
	return float(l) * LEVEL <= top

## Is the straight line from `a` to `b` walkable for a body of `radius` on the floor at `z` (TopdownBrain.line_clear):
## every 10 units along it, its box free (`free_at`) and no drop under it. The corners read in place (a chase asks this
## of every foe that runs at the player, each tick).
func line_clear(a: Vector2, b: Vector2, z: float, radius: float) -> bool:
	var n := ceili(a.distance_to(b) / 10.0)
	var top := z + 8.0
	var low := z - 8.0
	var c0 := Vector2(-radius, -radius)
	var c1 := Vector2(radius, -radius)
	var c2 := Vector2(-radius, radius)
	var c3 := Vector2(radius, radius)
	for i in range(1, n + 1):
		var p := a.lerp(b, float(i) / float(n))
		if not (_corner_free(p + c0, top) and _corner_free(p + c1, top) and _corner_free(p + c2, top) and _corner_free(p + c3, top)): return false
		if height_at(p) < low: return false
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

## The ground under a body at `p` and height `z`: its floor while it stands on it, the floor below while it is in the
## air over one; its own height where nothing is under it (the camera's ground, an ally's owner's floor).
func ground_under(p: Vector2, z: float) -> float:
	var g := height_at(p)
	return g if g < INF and g <= z + 1.0 else z

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

## What shows a way where it is (docs/tutorial_order.md): "building" (in the
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
## the standable spot within three tiles of it, its floor within `tol` of `z` (auto-hunt asks for the foe's own floor),
## nearest `from`; else the nearest spot.
func spot_near(p: Vector2, z: float, from: Vector2, tol := 40.0) -> Vector2:
	var c0 := cell_of(p)
	var best := Vector2.INF
	for dy in range(-3, 4):
		for dx in range(-3, 4):
			var c := c0 + Vector2i(dx, dy)
			if dx * dx + dy * dy > 9 or not standable(c): continue
			var q := (Vector2(c) + Vector2(0.5, 0.5)) * TILE
			if absf(floor_at(q) - z) > tol: continue
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
##   routes   object id -> [[cell x, cell y, seconds], ...]: a rooftop thief's run over the grid;
##   areas    [{kind, rect: [x, y, w, h] in cells, ...}]: a hazard's pools and currents on the plane.
## A timed route (the Cloud Steps) finishes at its room's route_finish object, where the layout places it.
func merge_def(side: Dictionary) -> Dictionary:
	var out := side.duplicate(true)
	for k in SIDE_ONLY: out.erase(k)
	out.view = "topdown"
	# T1: the side-view room's own bounds, which a room event's side-view points are mapped across (grid_event).
	out.side_bounds = side.get("bounds", [0, 480, 1280, 480])
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
		# The reach round it that counts as at the way (WorldAuthority.portal_near): half its span along the edge or the
		# doorway (a doorway's own width, an edge's span) and a tile across it, turned with the way; its floor's height
		# within half a level.
		var span := float(lay.get("span", 2 if str(p.get("type", "edge")) in ["door"] else 3))
		var along := span * TILE * 0.5
		p.reach = [along if dir.x == 0.0 else TILE, TILE if dir.x == 0.0 else along]
		p.erase("press_up")
		p.erase("arrive_offset")
		p.erase("arrive_dy")
	var spawn_cells: Array = def.get("spawns", [])
	var specs: Array = out.get("spawns", [])
	for i in mini(specs.size(), spawn_cells.size()):
		specs[i].points = cell_points(spawn_cells[i])
		specs[i].erase("surface")
	# A hazard's areas (a pool, a current; HazardRules.areas) in cells, as world rects on the plane.
	if def.has("areas"):
		out.areas = (def.areas as Array).map(func(a):
			var r: Array = a.rect
			var wa: Dictionary = (a as Dictionary).duplicate(true)
			wa.rect = [float(r[0]) * TILE, float(r[1]) * TILE, float(r[2]) * TILE, float(r[3]) * TILE]
			return wa)
	var ev: Dictionary = out.get("event", {})
	var lay_ev: Dictionary = def.get("event", {})
	if not ev.is_empty() and not lay_ev.is_empty():
		ev.on_grid = true   # T1: its points are the layout's own cells (WorldRoomEvents sets them as they are)
		if ev.has("wave") and lay_ev.has("wave"): ev.wave.points = cell_points(lay_ev.wave)
		var fixed: Array = lay_ev.get("fixed", [])
		for i in mini((ev.get("fixed_spawns", []) as Array).size(), fixed.size()):
			var fp := cell_point(fixed[i])
			ev.fixed_spawns[i].at = [fp.x, fp.y]
		# Several waves (each its own cells, in order) and the timed spawns (a cell each), as the Hollow Night has them.
		var waves: Array = lay_ev.get("waves", [])
		for i in mini((ev.get("waves", []) as Array).size(), waves.size()): ev.waves[i].points = cell_points(waves[i])
		var timed: Array = lay_ev.get("timed", [])
		for i in mini((ev.get("timed_spawns", []) as Array).size(), timed.size()):
			var tp := cell_point(timed[i])
			ev.timed_spawns[i].at = [tp.x, tp.y]
	# Decision 43 (systems as places): the objects the places table adds to this room (a letter box, a meditation mat),
	# each on its cell's floor (data/places.json; PlaceRules).
	var added := PlaceRules.added_objects(id)
	if not added.is_empty():
		if not out.has("objects"): out.objects = []
		for o in added:
			o.alt = floor_at(Vector2(float(o.at[0]), float(o.at[1])))
			out.objects.append(o)
	return out

# ------------------------------------------------------------------ S12c: the paths above, and the brinks
## The Paths Above ledge (S43) whose top a body stands on at `p`, height `z`: its side-view surface id (the layout's
## `above`, tools/content/rooms/engine.py: the raised shape named for it, only its movement art climbs onto), "" when
## none. The Achievement authority finds it when a body lands there (`landed`'s surface).
func ledge_at(p: Vector2, z: float) -> String:
	var above: Dictionary = def.get("above", {})
	if above.is_empty(): return ""
	var c := cell_of(p)
	for sid in above:
		var a: Dictionary = above[sid]
		var r: Array = a.rect
		if Rect2i(int(r[0]), int(r[1]), int(r[2]), int(r[3])).has_point(c) and absf(z - float(a.level) * LEVEL) < 0.5 \
				and absf(height_at(p) - z) < 0.5: return str(sid)
	return ""

## How far under the room's lowest floor a fall out of it ends (the side view's void altitude, 250 under its lowest
## surface: S43 rule 6).
const VOID_DROP := 250.0
var _brinks = null           ## the columns whose south edge is a brink (1), found once
var _brink_depth := 0.0      ## world units past the south edge the void runs (the vista's drop)
var _void_z := INF

## Is the ground point `p` past a brink: south of the room's last row, in a column whose edge falls away into the sea
## of cloud or the star field's void (the layout's south vista `cloud_sea`, which TopdownVista draws), off the lanes of
## the ways that leave by that edge, as far as the vista shows? No floor is there: a body falls out of the room
## (TopdownMotor). The room's own queries (height_at, find_path, standable) never count it: outside the room is its edge.
func brink_at(p: Vector2) -> bool:
	if p.y < float(h) * TILE or p.x < 0.0 or p.x >= float(w) * TILE: return false
	if _brinks == null: _find_brinks()
	return p.y < float(h) * TILE + _brink_depth and (_brinks as PackedByteArray)[floori(p.x / TILE)] == 1

## The height at which a body past a brink has fallen out of the room: VOID_DROP under its lowest floor.
func void_z() -> float:
	if _void_z == INF:
		var low := INF
		for i in levels.size(): low = minf(low, WATER_Z if levels[i] == WATER else float(levels[i]) * LEVEL)
		_void_z = (low if low < INF else 0.0) - VOID_DROP
	return _void_z

func _find_brinks() -> void:
	var b := PackedByteArray()
	b.resize(w)
	_brinks = b
	for v in def.get("vista", []):
		if str(v.get("edge", "")) == "s" and str(v.get("kind", "")) == "cloud_sea": _brink_depth = maxf(TILE * 2.0, float(v.get("pad", 0)) * ART)
	if _brink_depth <= 0.0: return
	var lanes := {}
	var ways: Dictionary = def.get("portals", {})
	for pid in ways:
		if str((ways[pid] as Dictionary).get("dir", "")) != "s": continue
		for c in TopdownFoliage.portal_lane(ways[pid]): lanes[c.x] = true
	for x in w:
		var l := level(x, h - 1)
		if l != SOLID and l != WATER and not lanes.has(x): b[x] = 1
	_brinks = b
