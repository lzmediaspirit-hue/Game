class_name TopdownTerrain
extends RefCounted
## Top-down redesign, Phase 3 (docs/redesign/art_bible.md §3–§6, decision 33): which tiles the room view draws on each
## cell, from the room's height grid and paint and the tile set's manifest. The rules are the art bible's; the pixels
## are the atlas's (tools/art/topdown/build_tiles.py), so new art changes rows, not code.
##   - Tops: a paint mark's tops, picked per cell. Grass creeps over a path or paving on the same level: a path cell's
##     corner is grass when any cell sharing that corner is grass, and the cell takes its corner-matched tile (§6).
##   - Water: the shore's side-matched tile (bit 1 N, 2 E, 4 S, 8 W = land) in the frame of the moment (§6, §7).
##   - Light: rims where a neighbour drops away, contact shade at a face's foot, the shade a higher west neighbour
##     casts, a face's lit west end and shaded east end, the stairs' cheeks (§3, §5).
##   - Prop shadows: each prop's floor shadow (a sprite in the prop sheet), cut to the cells of the level it stands on,
##     so each floor draws its own piece and a body standing in it is never tinted (§3, §8).

const T := 16.0

var room: TopdownRoom
var paint: Dictionary
var auto: Dictionary
var _pieces: Dictionary = {}   ## Vector2i(row, level) -> [[dest, src], ...]: prop shadows cut to that row's cells

func _init(r: TopdownRoom) -> void:
	room = r
	paint = r.tileset.get("paint", {})
	auto = r.tileset.get("autotile", {})
	for p in r.props: _cut_shadow(p)

## The grid's level of a cell (a prop's top is a sprite, not the grid); `out` outside the room.
func lv(x: int, y: int, out := 99) -> int:
	return room.levels[y * room.w + x] if room.inside(x, y) else out

func _mark(x: int, y: int) -> Dictionary:
	return paint.get(room.paint_at(x, y), {})

func _stairs(x: int, y: int) -> bool:
	return not room.stair_at(x, y).is_empty()

## The level the cell shows at the edge north of it: a stair's height where it meets it, water -1, 99 outside.
func edge_level(x: int, y: int) -> int:
	if not room.inside(x, y): return 99
	if _stairs(x, y): return floori(room.height_at(Vector2((x + 0.5) * TopdownRoom.TILE, y * TopdownRoom.TILE + 0.5)) / TopdownRoom.LEVEL + 0.01)
	return lv(x, y)

## The top tile of a cell: a path's corner-matched edge where grass on its level touches it, else a fixed variant.
func top(x: int, y: int) -> String:
	var info := _mark(x, y)
	if info.is_empty(): info = paint.get("g", {})
	var under := str(info.get("under", ""))
	if under != "":
		var l := lv(x, y)
		var key := ""
		for c in [Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)]:
			var g := "0"
			for ox in [c.x - 1, c.x]:
				for oy in [c.y - 1, c.y]:
					if _mark(x + ox, y + oy).get("grass", false) and lv(x + ox, y + oy) == l: g = "1"
			key += g
		if key != "0000": return str(auto.get(under, {}).get("tiles", {}).get(key, "grass_a"))
	var names: Array = info.get("top", ["grass_a"])
	return str(names[(x * 7 + y * 13 + (x * y) % 5) % names.size()])

## The land round a water cell: bit 1 N, 2 E, 4 S, 8 W.
func shore_sides(x: int, y: int) -> int:
	var bits := 0
	for s in [[1, Vector2i(0, -1)], [2, Vector2i(1, 0)], [4, Vector2i(0, 1)], [8, Vector2i(-1, 0)]]:
		var n: Vector2i = Vector2i(x, y) + s[1]
		if room.inside(n.x, n.y) and lv(n.x, n.y) != TopdownRoom.WATER: bits |= int(s[0])
	return bits

## A water cell's tiles for the four frames of the water's clock.
func water(x: int, y: int) -> Array:
	return auto.get("shore", {}).get("tiles", {}).get("%02d" % shore_sides(x, y), ["water_0", "water_1", "water_2", "water_3"])

## The light overlays on the top of a cell standing at level `l`.
func overlays(x: int, y: int, l: int) -> Array:
	var out: Array = []
	if edge_level(x - 1, y) < l: out.append("rim_w")
	if edge_level(x + 1, y) < l: out.append("rim_e")
	if room.inside(x, y - 1) and lv(x, y - 1) < l and not _stairs(x, y - 1): out.append("rim_n")
	if lv(x, y - 1, -9) > l and not _stairs(x, y - 1): out.append("ao_n")
	if lv(x - 1, y, -9) > l: out.append("shade_w")
	return out

## The face tile `k` rows under a top (0: the first, under the lip); over water a bank unless the mark keeps its own.
func face(x: int, y: int, k: int, over_water: bool) -> String:
	var info := _mark(x, y)
	var kind := str(info.get("face", "stone"))
	if over_water and not info.get("keep_face", false): kind = str(room.tileset.get("bank_face", "bank"))
	if k == 0: return kind + "_face_top"
	var below: Array = info.get("face_below", []) if kind == str(info.get("face", "")) else []
	return str(below[x % below.size()]) if not below.is_empty() else kind + "_face"

## The ends of face row `k` under a top at level `l`: lit where it turns the west corner, shaded at the east.
func face_ends(x: int, y: int, l: int, k: int) -> Array:
	var out: Array = []
	if edge_level(x - 1, y) < l - k: out.append("end_w")
	if edge_level(x + 1, y) < l - k: out.append("end_e")
	return out

## The pieces of prop shadows on row `row`'s floor at `level`: [dest (art px on the ground, before the level's lift),
## src (in the prop sheet)].
func shadow_pieces(row: int, level: int) -> Array:
	return _pieces.get(Vector2i(row, level), [])

func _cut_shadow(p: Dictionary) -> void:
	var art: Dictionary = p.art
	if not art.has("shadow_rect") or int(p.level) < 0: return
	var sr: Array = art.shadow_rect
	var sa: Array = art.get("shadow_at", [0, 0])
	var cell: Vector2i = p.cell
	var src := Rect2(float(sr[0]), float(sr[1]), float(sr[2]), float(sr[3]))
	var dest := Rect2(cell.x * T + float(sa[0]), (cell.y + (p.size as Vector2i).y) * T + float(sa[1]), src.size.x, src.size.y)
	var l := int(p.level)
	for cy in range(floori(dest.position.y / T), ceili(dest.end.y / T)):
		for cx in range(floori(dest.position.x / T), ceili(dest.end.x / T)):
			if lv(cx, cy, -99) != l or _stairs(cx, cy): continue
			var piece := dest.intersection(Rect2(cx * T, cy * T, T, T))
			if piece.size.x <= 0.0 or piece.size.y <= 0.0: continue
			var key := Vector2i(cy, l)
			if not _pieces.has(key): _pieces[key] = []
			_pieces[key].append([piece, Rect2(src.position + piece.position - dest.position, piece.size)])
