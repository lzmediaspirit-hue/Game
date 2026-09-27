class_name TopdownRoom
extends RefCounted
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1.2): a room as a height grid. Each 16-art-px cell
## (32 world units) holds a level (0–9, one level = one tile = 32 units of height) or water (-1); stairs rise across
## a rect; props stand on footprints that block. Queries are in world units on the ground plane (x, depth y) with the
## height z, the same model as ActorState (plane + altitude). The side-view rooms do not use it.

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
var stairs: Array = []               ## {rect: Rect2i, from, to}
var props: Array = []                ## {kind, cell: Vector2i, size: Vector2i, level, art: Dictionary}
var spawn := Vector2.ZERO            ## world units
var tileset: Dictionary = {}

static func load_room(room_id: String) -> TopdownRoom:
	var d = JSON.parse_string(FileAccess.get_file_as_string(DIR + room_id + ".json"))
	var ts = JSON.parse_string(FileAccess.get_file_as_string(DIR + "proto_tileset.json"))
	return from_dict(d if d is Dictionary else {}, ts if ts is Dictionary else {})

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
		r.props.append({"kind": str(p.kind), "cell": cell, "size": Vector2i(int(fp[0]), int(fp[1])), "level": r.levels[(cell.y + int(fp[1]) - 1) * r.w + cell.x], "art": art})
		if art.get("solid", true):
			for y in int(fp[1]):
				for x in int(fp[0]):
					if r.inside(cell.x + x, cell.y + y): r.solid[(cell.y + y) * r.w + cell.x + x] = 1
	var sp: Array = d.get("spawn", [1, 1])
	r.spawn = Vector2((float(sp[0]) + 0.5) * TILE, (float(sp[1]) + 0.5) * TILE)
	return r

func inside(cx: int, cy: int) -> bool:
	return cx >= 0 and cy >= 0 and cx < w and cy < h

## The cell's level for standing: SOLID outside the room and under a blocking prop, -1 for water.
func level(cx: int, cy: int) -> int:
	if not inside(cx, cy) or solid[cy * w + cx] == 1: return SOLID
	return levels[cy * w + cx]

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
## edge of its own row; stairs by the south edge of the whole flight (plan §1.3).
func south_edge(p: Vector2) -> float:
	var cp := cell_of(p)
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
