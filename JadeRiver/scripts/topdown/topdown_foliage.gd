class_name TopdownFoliage
extends Node2D
## Terrain v2, third part (decision 40; docs/redesign/art_bible.md "Foliage and decor"): a room's ground cover and its
## trees' canopies, for TopdownWorld.
##   - The scatter: small pieces of ground cover (tall grass, ferns, wild flowers, pebbles, mushrooms, reeds, the litter
##     under trees) laid by a hash of the room and the cell, per biome (the cell's paint mark), from the rules in
##     data/topdown/decor.json (tools/art/topdown/build_decor.py). Never on a path, paving or granite, a way out and its
##     lane, the spawn, a stair's head or foot, or anyone's or anything's spot; never blocking (ground cover has no
##     collision). The pieces are drawn inside the floor's own chunks (FloorView) and raised rows (StripView), after
##     the tiles and before the props' shadows, so a tree's shade lies over them: no node per piece. The pieces that stir
##     sway a pixel on the GPU (a shader on those chunks), each at its own phase, with no redraw.
##   - The canopies: a tree's crown (the manifest's `canopy`) is an overhang laid over its trunk, sorted just after it,
##     so it covers whoever walks under it and never anything in front of it. It fades to FADE_A while the player or a
##     foe stands under it, and back when they leave; a canopy that sways plays its frames on its trunk's clock.
## The scatter is a pure function of the room, cached by the room's id, so a room always looks the same.

const T := 16.0
const DECOR := "res://data/topdown/decor.json"
const FADE_A := 0.35          ## a canopy's opacity while someone stands under it (plan §1.2: overhangs fade to 35%)
const FADE_S := 0.25          ## seconds to fade out or back
const SWAY_PERIOD := 0.65     ## seconds per frame of the ground cover's four-frame sway

static var _manifest: Dictionary = {}
static var _cache: Dictionary = {}
static var _sway_mat: ShaderMaterial

var world
var room: TopdownRoom
var tex: Texture2D
var items: Array = []           ## [foot x, foot y (art px, on the ground), sprite index, level, phase]
var rects: Array = []           ## per sprite index: [src Rect2, foot Vector2, sway rows]
var by_chunk: Dictionary = {}   ## Vector2i (chunk's first cell) -> item indices on the ground, back to front
var by_row: Dictionary = {}     ## row -> item indices on raised floors of that row
var canopies: Array = []        ## the Canopy nodes in the sorted layer

func _init(w = null) -> void:
	name = "Foliage"
	world = w
	if w == null: return
	room = w.room
	var m := manifest()
	if m.is_empty(): return
	tex = load(str(m.get("sheet", "")))
	var names: Array = (m.sprites as Dictionary).keys()
	names.sort()
	for n in names:
		var sp: Dictionary = m.sprites[n]
		var r: Array = sp.rect
		rects.append([Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3])), Vector2(float(sp.foot[0]), float(sp.foot[1])), int(sp.get("sway", 0))])
	items = scatter(room)
	var chunk: Vector2i = TopdownWorld.CHUNK
	for k in items.size():
		var it: Array = items[k]
		var c := Vector2i(floori(float(it[0]) / T), floori(float(it[1]) / T))
		if int(it[3]) == 0:
			var key := Vector2i((c.x / chunk.x) * chunk.x, (c.y / chunk.y) * chunk.y)
			if not by_chunk.has(key): by_chunk[key] = []
			by_chunk[key].append(k)
		else:
			if not by_row.has(c.y): by_row[c.y] = []
			by_row[c.y].append(k)

static func manifest() -> Dictionary:
	if _manifest.is_empty() and FileAccess.file_exists(DECOR):
		var d = JSON.parse_string(FileAccess.get_file_as_string(DECOR))
		_manifest = d if d is Dictionary else {}
	return _manifest

## After the room's floor, rows and props are built: a canopy over each tree's trunk, and the sway on the chunks and
## rows that hold swaying pieces. Returns the nodes it added, for the room to clear with its own.
func build() -> Array:
	var out: Array = [self]
	for p in room.props:
		var art: Dictionary = p.art
		if not art.has("canopy"): continue
		var cv := Canopy.new(world, p)
		world.sorted.add_child(cv)
		canopies.append(cv)
		out.append(cv)
	var mat := sway_material()
	for n in world.viewport.get_children():
		if n.get("chunk") is Rect2i and n.material == null and _sways(by_chunk.get((n.chunk as Rect2i).position, [])): n.material = mat
	for n in world.sorted.get_children():
		if n.get("levels") is Dictionary and n.get("row") is int and n.material == null and _sways(by_row.get(int(n.row), [])): n.material = mat
	set_process(not canopies.is_empty())
	return out

func _sways(list: Array) -> bool:
	for k in list:
		if int(rects[int(items[k][2])][2]) > 0: return true
	return false

## The shader that sways a piece's upper part a pixel east and back (0, 1, 1, 0 over four frames): the part is drawn
## with a colour whose blue carries its phase and whose alpha is whole (a tile's tint never is), and is drawn white.
static func sway_material() -> ShaderMaterial:
	if _sway_mat == null:
		_sway_mat = ShaderMaterial.new()
		_sway_mat.shader = Shader.new()
		_sway_mat.shader.code = """shader_type canvas_item;
uniform float period = %s;
void vertex() {
	if (COLOR.a > 0.999 && COLOR.b < 0.99) {
		float f = mod(floor(TIME / period + COLOR.b * 4.0), 4.0);
		VERTEX.x += (f > 0.5 && f < 2.5) ? 1.0 : 0.0;
		COLOR = vec4(1.0);
	}
}
""" % str(SWAY_PERIOD)
	return _sway_mat

## The ground cover of a floor chunk (FloorView), after its tiles and before the props' shadows.
func draw_floor(ci: CanvasItem, chunk: Rect2i) -> void:
	for k in by_chunk.get(chunk.position, []): _draw_item(ci, k, 0.0)

## The ground cover on a raised row's tops (StripView), lifted as that row draws them.
func draw_row(ci: CanvasItem, row: int, lift: float) -> void:
	for k in by_row.get(row, []): _draw_item(ci, k, -float(items[k][3]) * T - lift)

func _draw_item(ci: CanvasItem, k: int, dy: float) -> void:
	var it: Array = items[k]
	var r: Array = rects[int(it[2])]
	var src: Rect2 = r[0]
	var at := Vector2(float(it[0]), float(it[1]) + dy) - (r[1] as Vector2)
	var sway := int(r[2])
	if sway <= 0:
		ci.draw_texture_rect_region(tex, Rect2(at, src.size), src)
		return
	var still := Vector2(src.size.x, src.size.y - sway)
	ci.draw_texture_rect_region(tex, Rect2(at + Vector2(0, sway), still), Rect2(src.position + Vector2(0, sway), still))
	ci.draw_texture_rect_region(tex, Rect2(at, Vector2(src.size.x, sway)), Rect2(src.position, Vector2(src.size.x, sway)), Color(1, 1, float(it[4]), 1))

# ------------------------------------------------------------------ the scatter
## The room's ground cover: [foot x, foot y, sprite index, level, phase] per piece, back to front. A pure function of
## the room, cached by its id and size.
static func scatter(r: TopdownRoom) -> Array:
	var ck := "%s:%d:%d:%d" % [r.id, r.w, r.h, r.props.size()]
	if _cache.has(ck): return _cache[ck]
	var m := manifest()
	var out: Array = []
	if m.is_empty():
		return out
	# Looked up once: each sprite by index (rect, foot), each set as sprite indices, each biome by its paint byte.
	var names: Array = (m.sprites as Dictionary).keys()
	names.sort()
	var index := {}
	var size: Array = []
	var foot_x: Array = []
	for i in names.size():
		index[names[i]] = i
		var sp: Dictionary = m.sprites[names[i]]
		size.append(Vector2(float(sp.rect[2]), float(sp.rect[3])))
		foot_x.append(float(sp.foot[0]))
	var sets := {}
	for k in m.sets: sets[k] = (m.sets[k] as Array).map(func(n): return int(index[n]))
	var bio: Array = []
	bio.resize(128)
	for mark in m.biomes: bio[str(mark).unicode_at(0)] = m.biomes[mark]
	var seed := 0
	for ch in r.id: seed = (seed * 31 + ch.unicode_at(0)) & 0xFFFF
	seed += 911
	var n_cells := r.w * r.h
	var clear := PackedByteArray()
	clear.resize(n_cells)
	for c in clear_cells(r):
		if r.inside(c.x, c.y): clear[c.y * r.w + c.x] = 1
	var litter := litter_cells(r)
	var lshare := float((m.get("litter", {}) as Dictionary).get("share", 0.5))
	var chunk: Vector2i = TopdownWorld.CHUNK
	var keys := PackedInt64Array()
	var raw: Array = []
	for y in r.h:
		for x in r.w:
			var i := y * r.w + x
			var l := r.levels[i]
			if l < 0 or clear[i] == 1 or r.solid[i] == 1 or r.stair_of[i] > 0: continue
			var pb := r.paint[i]
			var b = bio[pb] if pb < 128 else null
			if b == null: continue
			var lit: String = litter.get(Vector2i(x, y), "") if not litter.is_empty() else ""
			if lit == "blight": continue   # round a dead tree the Hollowing has drained the ground
			var picks: Array = []
			var hsh := TopdownTerrain.h01(x, y, seed)
			if lit != "" and hsh < lshare:
				picks.append(lit)
				if TopdownTerrain.h01(x, y, seed + 1) < 0.35: picks.append(lit)
			elif b.has("shore") and hsh < float(b.shore) and _shore(r, x, y):
				picks.append("reeds")
			elif b.has("patch") and TopdownTerrain.vnoise(x / float(b.patch.scale), y / float(b.patch.scale), seed + 2) > float(b.patch.above):
				for n in 1 + int(TopdownTerrain.h01(x, y, seed + 3) * float(b.patch.count)): picks.append(str(b.patch.set))
			elif hsh < float(b.share):
				picks.append(_weighted(b.sets, TopdownTerrain.h01(x, y, seed + 4)))
			for n in picks.size():
				var list: Array = sets.get(picks[n], [])
				if list.is_empty(): continue
				var k := int(list[int(TopdownTerrain.h01(x, y, seed + 10 + n) * list.size())])
				var sz: Vector2 = size[k]
				var fx: float = foot_x[k]
				# The foot inside the cell, the piece never above the cell's top edge, and inside its floor chunk
				# sideways (a chunk's pieces draw with its tiles).
				var px := x * T + 2.0 + floorf(TopdownTerrain.h01(x, y, seed + 20 + n) * 12.0)
				var c0 := float((x / chunk.x) * chunk.x) * T
				px = clampf(px, c0 + fx, minf(c0 + chunk.x * T, r.w * T) - (sz.x - fx))
				var py := maxf(y * T + 15.0 - floorf(TopdownTerrain.h01(x, y, seed + 30 + n) * maxf(0.0, 16.0 - sz.y)), y * T + sz.y - 1.0)
				keys.append((int(py) << 32) | (int(px) << 16) | raw.size())
				raw.append([int(px), int(py), k, l, snappedf(TopdownTerrain.h01(x, y, seed + 40 + n) * 0.96, 0.01)])
	# Back to front by the foot's row, then west to east (a native sort of packed keys).
	keys.sort()
	for key in keys: out.append(raw[key & 0xFFFF])
	_cache[ck] = out
	return out

static func _weighted(list: Array, h: float) -> String:
	var total := 0.0
	for e in list: total += float(e[1])
	var acc := 0.0
	for e in list:
		acc += float(e[1]) / total
		if h < acc: return str(e[0])
	return str(list.back()[0]) if not list.is_empty() else ""

static func _shore(r: TopdownRoom, x: int, y: int) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if r.is_water(x + d.x, y + d.y): return true
	return false

## The cells kept clear of ground cover: round the spawn, every person's and thing's spot, each way out's lane from
## its doorway or edge to where one arrives (as wide as its span), the heads and feet of the stairs, and the foes'
## spawn points (decor.json `clear`: the rings).
static func clear_cells(r: TopdownRoom) -> Dictionary:
	var ring: Dictionary = manifest().get("clear", {})
	var out := {}
	var d: Dictionary = r.def
	_ring(out, TopdownRoom.cell_of(r.spawn), int(ring.get("spawn", 1)))
	for id in d.get("place", {}):
		_ring(out, TopdownRoom.cell_of(TopdownRoom.cell_point(d.place[id])), int(ring.get("place", 1)))
	for id in d.get("portals", {}):
		for c in portal_lane(d.portals[id]): _ring(out, c, int(ring.get("portal", 1)))
	for st in r.stairs:
		var rc: Rect2i = st.rect
		for x in range(rc.position.x - 1, rc.end.x + 1):
			out[Vector2i(x, rc.end.y)] = true
			out[Vector2i(x, rc.position.y - 1)] = true
	var foes: Array = []
	for list in d.get("spawns", []): foes.append_array(list.get("points", []) if list is Dictionary else list)
	var ev: Dictionary = d.get("event", {})
	foes.append_array(ev.get("wave", []))
	foes.append_array(ev.get("fixed", []))
	for list in ev.get("waves", []): foes.append_array(list)
	foes.append_array(ev.get("timed", []))
	for q in foes: _ring(out, TopdownRoom.cell_of(TopdownRoom.cell_point(q)), int(ring.get("foe", 0)))
	return out

## A way out's lane: the cells from its doorway or edge cell in to where one arrives, as wide as its span.
static func portal_lane(p: Dictionary) -> Array:
	var at := TopdownRoom.cell_of(TopdownRoom.cell_point(p.at))
	var dir: Vector2 = TopdownRoom.DIRS.get(str(p.get("dir", "s")), Vector2.DOWN)
	var arrive := TopdownRoom.cell_of(TopdownRoom.cell_point(p.arrive)) if p.has("arrive") else at - Vector2i(dir * 2.0)
	var half := int(ceilf(float(p.get("span", 2)) * 0.5))
	var out: Array = []
	var side := Vector2i(int(absf(dir.y)), int(absf(dir.x)))
	var steps := maxi(absi(arrive.x - at.x), absi(arrive.y - at.y))
	for k in steps + 2:
		var c := at - Vector2i(dir) * k
		for s in range(-half, half + 1): out.append(c + side * s)
	return out

static func _ring(out: Dictionary, c: Vector2i, n: int) -> void:
	for y in range(c.y - n, c.y + n + 1):
		for x in range(c.x - n, c.x + n + 1): out[Vector2i(x, y)] = true

## The cells round each tree that take its litter (the manifest's `litter` per prop kind), within the rules' radius.
static func litter_cells(r: TopdownRoom) -> Dictionary:
	var rad := float((manifest().get("litter", {}) as Dictionary).get("radius", 2.5))
	var out := {}
	for p in r.props:
		var set := str((p.art as Dictionary).get("litter", ""))
		if set == "": continue
		var mid := Vector2(p.cell) + Vector2(p.size) * 0.5
		for y in range(floori(mid.y - rad - 1), ceili(mid.y + rad) + 1):
			for x in range(floori(mid.x - rad - 1), ceili(mid.x + rad) + 1):
				if Vector2(x + 0.5, y + 0.5).distance_to(mid + Vector2(0.4, 0.3)) <= rad and not out.has(Vector2i(x, y)): out[Vector2i(x, y)] = set
	return out

# ------------------------------------------------------------------ the canopies
func _process(delta: float) -> void:
	var p = world.player
	var body := Rect2(p.screen.x - 5, p.screen.y - 34, 10, 30)
	var vs := Vector2(world.viewport.size)
	var view := Rect2(world.camera.position - vs * 0.5, vs).grow(T * 2.0)
	for cv in canopies:
		if not is_instance_valid(cv) or not cv.area.intersects(view): continue
		cv.tick()
		var under: bool = p.position.y < cv.position.y and cv.box.intersects(body)
		if not under:
			for uid in world.foe_views:
				var fv = world.foe_views[uid]
				if is_instance_valid(fv) and fv.visible and fv.position.y < cv.position.y and cv.box.intersects(Rect2(fv.feet.x - 7, fv.feet.y - 24, 14, 22)):
					under = true
					break
		cv.modulate.a = move_toward(cv.modulate.a, FADE_A if under else 1.0, delta * (1.0 - FADE_A) / FADE_S)

## A tree's crown over its trunk: laid at the manifest's `canopy.at` from the footprint's south-west corner on the
## floor the tree stands on, sorted just after the trunk (its key + 1/64). It never blocks and never counts for the
## silhouette (it fades instead). `box` is the part that hides a body under it (screen art px).
class Canopy extends TopdownWorld.Sorted:
	var src: Rect2
	var at: Vector2
	var box: Rect2
	var area: Rect2
	var cell: Vector2i          ## its trunk's footprint corner (north-west cell) and the floor it stands on
	var level := 0
	var frames := 1
	var frame_ms := 0
	var phase := 0
	var frame := 0
	func _init(w, p: Dictionary) -> void:
		super(w)
		var c: Dictionary = (p.art as Dictionary).canopy
		var rr: Array = c.rect
		src = Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3]))
		cell = p.cell
		level = int(p.level)
		var ground := TopdownRoom.WATER_Z / TopdownRoom.ART * -1.0 if level < 0 else -level * T
		var sw := Vector2(cell.x * T, (cell.y + (p.size as Vector2i).y) * T).round()
		at = Vector2(sw.x + float(c.at[0]), sw.y + ground + float(c.at[1]))
		var b: Array = c.get("box", [0, 0, rr[2], rr[3]])
		box = Rect2(at + Vector2(float(b[0]), float(b[1])), Vector2(float(b[2]), float(b[3])))
		area = Rect2(at, src.size)
		frames = int(c.get("frames", 1))
		frame_ms = int(c.get("frame_ms", 0))
		phase = (cell.x * 3 + cell.y * 5) % maxi(1, frames)
		key(sw.y + 0.5 + 1.0 / 64.0)
	func tick() -> void:
		if frames <= 1 or frame_ms <= 0: return
		var f := (int(Time.get_ticks_msec() / frame_ms) + phase) % frames
		if f != frame:
			frame = f
			queue_redraw()
	func _draw() -> void:
		draw_texture_rect_region(world.atlas("props"), Rect2(at - position, src.size), Rect2(src.position + Vector2(src.size.x * frame, 0), src.size))
