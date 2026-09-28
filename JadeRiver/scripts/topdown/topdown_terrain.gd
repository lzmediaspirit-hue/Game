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
## Terrain v2 (decision 40, art bible "Terrain v2"): the room view draws each cell as layers (`top_layers`,
## `face_layers`, `water_layers`), each [tile, colour]. `top()`, `face()`, `water()` and `overlays()` keep the Phase 3
## contract (the TileSet's tiles); the layers are what breaks the 16 px grid:
##   - a top's base is its material's macro pattern at the cell's place in it (x mod w, y mod h), so tiles join
##     seamlessly and nothing repeats every 16 px;
##   - a path under grass takes the positional grass overlay of its corner case (the grass pattern's own pixels there);
##   - a decal, picked by a hash of the cell from the mark's `decals` ([set, share], in order);
##   - the sun and shade patches: a low-frequency noise over the room's corners, where all four cells round a corner
##     are tops of one level whose mark takes `tone`, laid as positional tint masks drawn in the manifest's colours;
##   - faces pick their pattern's tile by column (the first row, then two body rows that repeat downward), and the
##     last row over a floor takes the foot shade (`face_ao`);
##   - water: the water pattern's tile in the frame of the moment, the depth tints two and four cells from land
##     (distance counted over the eight neighbours), the shore overlay of its side case, foam where land touches only
##     a corner, and ripples under a pier's pilings.
## Every pick is a pure function of the room (its id seeds the hashes), so a room always looks the same.

const T := 16.0
const TONE_SUN := 0.58      ## the corner noise over which a sun patch lies
const TONE_SHADE := 0.4     ## and under which a shade patch lies
const DEEP := 2             ## cells from land where the water turns deep, and deeper
const DEEPER := 4

var room: TopdownRoom
var paint: Dictionary
var auto: Dictionary
var v2: Dictionary
var seed := 0
var _pieces: Dictionary = {}   ## Vector2i(row, level) -> [[dest, src], ...]: prop shadows cut to that row's cells
var _tone := PackedByteArray() ## per corner ((w + 1) x (h + 1)): bit 1 sun, bit 2 shade
var _deep := PackedByteArray() ## per corner: the least distance to land of the cells round it (0 by land)
var _dist := PackedInt32Array() ## per cell: water's distance to land (0 on land)
var _tint: Dictionary = {}     ## tint kind -> Color
var _info: Array = []          ## per cell: its paint mark's entry (looked up once)
var _empty := {}
var _plan: Array = []          ## per cell: how its mark draws in v2 {tiles, w, h, decals [[names, share]], under}
var _grass := PackedByteArray() ## per cell: 1 when its mark is grass that creeps over paths
var _over_by: Array = []       ## corner key as an int (TL 8, TR 4, BL 2, BR 1) -> the grass overlays by place
var _mask_by: Array = []       ## corner key as an int -> the tint masks by place

func _init(r: TopdownRoom) -> void:
	room = r
	paint = r.tileset.get("paint", {})
	auto = r.tileset.get("autotile", {})
	v2 = r.tileset.get("v2", {})
	_info.resize(r.w * r.h)
	for i in r.w * r.h: _info[i] = paint.get(char(r.paint[i]), _empty)
	for ch in r.id: seed = (seed * 31 + ch.unicode_at(0)) & 0xFFFF
	for k in v2.get("tint", {}):
		var c: Array = v2.tint[k]
		_tint[k] = Color(float(c[0]), float(c[1]), float(c[2]), float(c[3]))
	for p in r.props: _cut_shadow(p)
	if not v2.is_empty():
		_plans()
		_tones()
		_water_depth()

## Terrain v2: per cell, what its mark draws (looked up once, so drawing a room is a few array reads per cell).
func _plans() -> void:
	var by_mark := {}
	var n := room.w * room.h
	_plan.resize(n)
	_grass.resize(n)
	for i in n:
		var info: Dictionary = _info[i] if not (_info[i] as Dictionary).is_empty() else paint.get("g", {})
		_grass[i] = 1 if info.get("grass", false) else 0
		if not by_mark.has(info):
			var m: Dictionary = v2.get("macro", {}).get(str(info.get("macro", "grass")), {})
			var decals: Array = []
			for d in info.get("decals", []):
				var names: Array = v2.get("decals", {}).get(str(d[0]), [])
				if not names.is_empty(): decals.append([names, float(d[1])])
			by_mark[info] = {"tiles": m.get("tiles", []), "w": int(m.get("w", 1)), "h": int(m.get("h", 1)), "decals": decals,
				"under": str(info.get("under", "")) != ""}
		_plan[i] = by_mark[info]
	for k in 16:
		var key := "%d%d%d%d" % [(k >> 3) & 1, (k >> 2) & 1, (k >> 1) & 1, k & 1]
		_over_by.append(v2.get("over", {}).get(key, []))
		_mask_by.append(v2.get("tint_mask", {}).get(key, []))

## The grid's level of a cell (a prop's top is a sprite, not the grid); `out` outside the room.
func lv(x: int, y: int, out := 99) -> int:
	return room.levels[y * room.w + x] if room.inside(x, y) else out

func _mark(x: int, y: int) -> Dictionary:
	return _info[y * room.w + x] if room.inside(x, y) else _empty

func _stairs(x: int, y: int) -> bool:
	return room.inside(x, y) and room.stair_of[y * room.w + x] > 0

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
		var key := grass_key(x, y)
		if key != "0000": return str(auto.get(under, {}).get("tiles", {}).get(key, "grass_a"))
	var names: Array = info.get("top", ["grass_a"])
	return str(names[(x * 7 + y * 13 + (x * y) % 5) % names.size()])

## A path cell's grass corners (TL TR BL BR): "1" where grass on its own level shares that corner.
func grass_key(x: int, y: int) -> String:
	var l := lv(x, y)
	var key := ""
	for c in [Vector2i(0, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(1, 1)]:
		var g := "0"
		for ox in [c.x - 1, c.x]:
			for oy in [c.y - 1, c.y]:
				if _mark(x + ox, y + oy).get("grass", false) and lv(x + ox, y + oy) == l: g = "1"
		key += g
	return key

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

# ------------------------------------------------------------------ Terrain v2 (decision 40)
## A hash of integer coordinates to [0, 1) (the tile builder's own, tools/art/topdown/canvas.py `h01`).
static func h01(x: int, y: int, s: int) -> float:
	var n := (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
	n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
	return float((n ^ (n >> 16)) & 0xFFFF) / 65536.0

## Value noise over the plane from that hash (smoothstep between lattice points).
static func vnoise(x: float, y: float, s: int) -> float:
	var x0 := floori(x)
	var y0 := floori(y)
	var tx := x - x0
	var ty := y - y0
	tx = tx * tx * (3.0 - 2.0 * tx)
	ty = ty * ty * (3.0 - 2.0 * ty)
	var a := lerpf(h01(x0, y0, s), h01(x0 + 1, y0, s), tx)
	var b := lerpf(h01(x0, y0 + 1, s), h01(x0 + 1, y0 + 1, s), tx)
	return lerpf(a, b, ty)

## A layer the room view draws: a tile and the colour it is drawn in (white, or a tint for a mask).
func _layer(name: String, c := Color.WHITE) -> Array:
	return [name, c]

## A material's macro tile at a cell: its place in the pattern (x mod w, y mod h).
func macro(kind: String, x: int, y: int) -> String:
	var m: Dictionary = v2.get("macro", {}).get(kind, {})
	if m.is_empty(): return ""
	var w := int(m.w)
	var h := int(m.h)
	return str(m.tiles[posmod(y, h) * w + posmod(x, w)])

## The sun and shade patches: a corner is eligible when the four cells round it are tops of one level, off the stairs,
## whose marks take `tone`; the patches lie where a low-frequency noise of the corner is high (sun) or low (shade).
func _tones() -> void:
	var cw := room.w + 1
	_tone.resize(cw * (room.h + 1))
	var lvl := PackedInt32Array()   # per cell: its level where it can take a tone, else -99
	lvl.resize(room.w * room.h)
	for i in room.w * room.h:
		lvl[i] = room.levels[i] if room.levels[i] >= 0 and room.stair_of[i] == 0 and _info[i].get("tone", false) else -99
	for cy in range(1, room.h):
		for cx in range(1, room.w):
			var l0 := lvl[(cy - 1) * room.w + cx - 1]
			if l0 < 0 or lvl[(cy - 1) * room.w + cx] != l0 or lvl[cy * room.w + cx - 1] != l0 or lvl[cy * room.w + cx] != l0: continue
			var n := 0.65 * vnoise(cx / 7.0, cy / 7.0, seed) + 0.35 * vnoise(cx / 3.0, cy / 3.0, seed + 1)
			_tone[cy * cw + cx] = (1 if n > TONE_SUN else 0) | (2 if n < TONE_SHADE else 0)

## Each water cell's distance to land over its eight neighbours (land 0; the room's edge does not count as land, so
## a river runs on past it), and each corner's least distance of the cells round it (outside the room counts as far).
func _water_depth() -> void:
	var w := room.w
	_dist.resize(w * room.h)
	var q := PackedInt32Array()
	for i in w * room.h:
		var land := room.levels[i] != TopdownRoom.WATER
		_dist[i] = 0 if land else 999
		if land: q.append(i)
	var head := 0
	while head < q.size():
		var i := q[head]
		head += 1
		var cx := i % w
		var cy := i / w
		var d := _dist[i] + 1
		for oy in range(maxi(0, cy - 1), mini(room.h, cy + 2)):
			for ox in range(maxi(0, cx - 1), mini(w, cx + 2)):
				if _dist[oy * w + ox] > d:
					_dist[oy * w + ox] = d
					q.append(oy * w + ox)
	var cw := w + 1
	_deep.resize(cw * (room.h + 1))
	for cy in room.h + 1:
		for cx in cw:
			var least := 255
			for c in 4:
				var x := cx - 1 + (c & 1)
				var y := cy - 1 + (c >> 1)
				if x >= 0 and y >= 0 and x < w and y < room.h: least = mini(least, _dist[y * w + x])
			_deep[cy * cw + cx] = least

## The corner key of a cell as an int (TL 8, TR 4, BL 2, BR 1) from a per-corner byte array: a corner counts where
## its byte has a bit of `mask`, or with `at_least` where it is at least that.
func _ckey(arr: PackedByteArray, x: int, y: int, mask: int, at_least := 0) -> int:
	var c0 := y * (room.w + 1) + x
	var c2 := c0 + room.w + 1
	if at_least > 0:
		return (8 if arr[c0] >= at_least else 0) | (4 if arr[c0 + 1] >= at_least else 0) | (2 if arr[c2] >= at_least else 0) | (1 if arr[c2 + 1] >= at_least else 0)
	return (8 if arr[c0] & mask else 0) | (4 if arr[c0 + 1] & mask else 0) | (2 if arr[c2] & mask else 0) | (1 if arr[c2 + 1] & mask else 0)

## grass_key as an int (TL 8, TR 4, BL 2, BR 1).
func _gkey(x: int, y: int) -> int:
	var l := room.levels[y * room.w + x]
	var k := 0
	for c in 4:
		var bit := 8 >> c
		var cx := x + (c & 1)
		var cy := y + (c >> 1)
		for oy in [cy - 1, cy]:
			for ox in [cx - 1, cx]:
				if ox >= 0 and oy >= 0 and ox < room.w and oy < room.h and _grass[oy * room.w + ox] and room.levels[oy * room.w + ox] == l:
					k |= bit
	return k

## A positional tint mask for a corner key (an int) at a cell, in a tint's colour.
func _tint_layer(key: int, x: int, y: int, kind: String) -> Array:
	return [_mask_by[key][(y & 3) * 4 + (x & 3)], _tint.get(kind, Color(1, 1, 1, 0))]

## The layers of a cell's top at level `l`, bottom to top: the base (its macro tile, or under grass the path's with
## the positional grass overlay), a decal, the sun and shade patches, the light overlays (rims, contact and cast
## shade).
func top_layers(x: int, y: int, l: int) -> Array:
	if v2.is_empty():
		return [_layer(top(x, y))] + overlays(x, y, l).map(func(o): return _layer(o))
	var pl: Dictionary = _plan[y * room.w + x]
	var out: Array = []
	var key := _gkey(x, y) if pl.under else 0
	var tiles: Array = pl.tiles
	var base := str(tiles[(y % int(pl.h)) * int(pl.w) + x % int(pl.w)]) if not tiles.is_empty() else top(x, y)
	if key == 15:
		out.append([macro("grass", x, y), Color.WHITE])
	elif key != 0:
		out.append([base, Color.WHITE])
		out.append([_over_by[key][(y & 3) * 4 + (x & 3)], Color.WHITE])
	else:
		out.append([base, Color.WHITE])
		var hsh := h01(x, y, seed + 5)
		var acc := 0.0
		for d in pl.decals:
			acc += float(d[1])
			if hsh < acc:
				var names: Array = d[0]
				out.append([names[int(h01(x, y, seed + 6) * names.size())], Color.WHITE])
				break
	if not _tone.is_empty():
		var sun := _ckey(_tone, x, y, 1)
		if sun: out.append(_tint_layer(sun, x, y, "sun"))
		var shade := _ckey(_tone, x, y, 2)
		if shade: out.append(_tint_layer(shade, x, y, "shade"))
	for o in overlays(x, y, l): out.append([o, Color.WHITE])
	return out

## The layers of face row `k` under the top of cell (x, y) at level `l`, the level in front being `south` (-1 water):
## the face's tile from its pattern by column (row 0 the first, with its lip; the body rows repeat downward), its
## lit or shaded end where it turns a corner, and on its last row over a floor the foot shade.
func face_layers(x: int, y: int, l: int, k: int, south: int) -> Array:
	var over_water := south + k + 1 == 0
	var name := face(x, y, k, over_water)
	var kind := name.trim_suffix("_top").trim_suffix("_face")
	var f: Dictionary = v2.get("faces", {}).get(kind, {})
	if not f.is_empty() and name == kind + ("_face_top" if k == 0 else "_face"):
		name = str(f.top[posmod(x, 4)]) if k == 0 else str(f.body[posmod(k - 1, 2) * 4 + posmod(x, 4)])
	var out: Array = [_layer(name)]
	for e in face_ends(x, y, l, k): out.append(_layer(e))
	if k == l - south - 1 and south >= 0 and v2.has("face_ao"): out.append(_layer(str(v2.face_ao)))
	return out

## The layers of a water cell in each of the water's four frames: the water pattern's tile, the depth tints, the
## shore overlay of its side case, foam where land touches only a corner, ripples under a pier's pilings.
func water_layers(x: int, y: int) -> Array:
	var wv: Dictionary = v2.get("water", {})
	if wv.is_empty():
		return water(x, y).map(func(n): return [_layer(str(n))])
	var still: Array = []
	var deep := _ckey(_deep, x, y, 0, DEEP)
	if deep: still.append(_tint_layer(deep, x, y, "deep"))
	var deeper := _ckey(_deep, x, y, 0, DEEPER)
	if deeper: still.append(_tint_layer(deeper, x, y, "deeper"))
	var sides := shore_sides(x, y)
	var frames: Array = []
	var m: Dictionary = wv.macro
	for f in 4:
		var out: Array = [_layer(str(m.frames[f][posmod(y, int(m.h)) * int(m.w) + posmod(x, int(m.w))]))]
		out.append_array(still)
		if sides: out.append(_layer(str(wv.shore["%02d" % sides][f])))
		for c in [["ne", Vector2i(1, -1), 1, 2], ["nw", Vector2i(-1, -1), 1, 8], ["se", Vector2i(1, 1), 4, 2], ["sw", Vector2i(-1, 1), 4, 8]]:
			var at: Vector2i = Vector2i(x, y) + (c[1] as Vector2i)
			if sides & int(c[2]) == 0 and sides & int(c[3]) == 0 and room.inside(at.x, at.y) and lv(at.x, at.y) != TopdownRoom.WATER:
				out.append(_layer(str(wv.corner[c[0]][f])))
		if y > 0 and lv(x, y - 1) != TopdownRoom.WATER and room.paint[(y - 1) * room.w + x] == 119:   # "w", a pier
			out.append(_layer(str(wv.ripple[f])))
		frames.append(out)
	return frames
