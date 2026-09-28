class_name TopdownShadows
extends RefCounted
## Decision 40, runtime light (docs/redesign/art_bible.md §14.2, §14.11): the cast shadows of a room on the height
## grid, baked once when the room is built (never per frame) into one texture in ground art px (x, depth y), and drawn
## by three kinds of node in `SHADOW`: on the water, on the ground floor (level 0) and on each raised row's tops.
##
## The sun stands in the north-west; a point h art px high casts at TopdownLight.SUN_STEP x h (+0.45 h, +0.20 h). What
## casts:
##   - a tall prop (TopdownLight.CASTS): its sprite's silhouette, each pixel as high as it stands over the footprint's
##     middle, laid on the floor along the sun's step. Stamps are cached per prop kind;
##   - a building or crate stack with a standable top: a block of its footprint up to its top;
##   - the grid, from two levels up: each cell is a column up to its floor (water half a level down), and a run of
##     cells with an east, south or south-east neighbour at least GRID_MIN_H lower throws the sweep of its block along
##     the sun's step onto every floor that much lower. A one-level step's shadow is the tiles' own (`shade_w`, `ao_n`).
## Each floor takes only the shadows of what stands higher than it, so a shadow falls down a cliff's drop, longer by the
## drop; it never lies on a face (faces are shaded already) or on a body.
##
## A shadow is two steps (§14.2, no blur, no dither): its body at SHADOW_BODY and a 2 px stepped edge at SHADOW_EDGE;
## the texture holds 1.0 for the body and SHADOW_EDGE / SHADOW_BODY for the edge. Where it falls on baked shade, the
## total stays at or under 0.6: the first px under a face (`ao_n`) takes none, the next px and the NEAR_PX east of a
## higher west cell (`shade_w`) and a prop's own floor shadow take only the edge; on the water it is at most 0.25.

const T := 16
const NONE := -9999
const BODY := Color(1, 1, 1, 1)
## Rooms baked since the game started (tests: one bake per room built, none per frame).
static var bakes := 0
static var _stamps: Dictionary = {}   ## "atlas|kind|dh" -> [full Image, body Image, offset from the footprint's south-west corner, top]
static var _sheets: Dictionary = {}   ## atlas path -> its Image (read once)
static var _material: ShaderMaterial
static var _water_material: ShaderMaterial
static var _shader: Shader

var room: TopdownRoom
var image: Image                      ## the shadow on every floor, in ground art px: alpha 1 its body, EDGE its edge
var texture: ImageTexture
var ms := 0.0                         ## how long the bake took
var plane := PackedInt32Array()       ## each cell's floor as a receiver (art px of height; water -8), NONE for none
var shaded := PackedByteArray()       ## 1 where a floor cell may hold shadow (it was under a sweep or a stamp)
var _height := PackedInt32Array()     ## each cell's height as a caster (art px)
var _touched: Dictionary = {}         ## plane -> PackedInt32Array of cell indices to take from that plane's pass
var _ovals: Dictionary = {}           ## plane -> [Rect2i]: the props' own floor shadows on it (the edge's alpha under them)
var _atlas := ""                      ## the props atlas the stamps are read from
var _runs: Dictionary = {}            ## "water", "ground", row -> its runs (runs())
var _below := PackedInt32Array()      ## each cell's lowest east, south or south-east neighbour (art px of height)

static func edge() -> Color:
	return Color(1, 1, 1, TopdownLight.SHADOW_EDGE / TopdownLight.SHADOW_BODY)

func _init(r: TopdownRoom) -> void:
	var t0 := Time.get_ticks_usec()
	room = r
	bakes += 1
	_atlas = str(r.tileset.get("atlas", {}).get("props", ""))
	_heights()
	var jobs := {}
	_grid_jobs(jobs)
	_prop_jobs(jobs)
	image = Image.create(maxi(1, r.w * T), maxi(1, r.h * T), false, Image.FORMAT_RGBA8)
	_run(jobs)
	texture = ImageTexture.create_from_image(image)
	ms = (Time.get_ticks_usec() - t0) / 1000.0

# ------------------------------------------------------------------ the bake
func _heights() -> void:
	var n := room.w * room.h
	_height.resize(n)
	plane.resize(n)
	shaded.resize(n)
	for y in room.h:
		for x in room.w:
			var i := y * room.w + x
			var l := room.levels[i]
			var z := -8 if l == TopdownRoom.WATER else l * T
			_height[i] = z
			plane[i] = z
			if room.stair_of[i] > 0:
				_height[i] = roundi(room.height_at(Vector2((x + 0.5) * TopdownRoom.TILE, (y + 0.5) * TopdownRoom.TILE)) / TopdownRoom.ART)
				plane[i] = NONE
	for p in room.props:
		if int(p.top) < 0: continue
		var c: Vector2i = p.cell
		var s: Vector2i = p.size
		for y in range(c.y, c.y + s.y):
			for x in range(c.x, c.x + s.x):
				if not room.inside(x, y): continue
				_height[y * room.w + x] = int(p.top) * T
				plane[y * room.w + x] = NONE
	_below.resize(n)
	var w := room.w
	for y in room.h:
		for x in w:
			var i := y * w + x
			var m := 1 << 20
			if x + 1 < w: m = mini(m, _height[i + 1])
			if y + 1 < room.h:
				m = mini(m, _height[i + w])
				if x + 1 < w: m = mini(m, _height[i + w + 1])
			_below[i] = m

func _job(jobs: Dictionary, p: int, job: Array) -> void:
	if not jobs.has(p): jobs[p] = []
	jobs[p].append(job)

func _touch(p: int, i: int) -> void:
	if not _touched.has(p): _touched[p] = PackedInt32Array()
	_touched[p].append(i)

## Is this run a building's or crate stack's block (a prop's standable top), which casts at any height?
func _is_block(x: int, y: int) -> bool:
	return room.inside(x, y) and room.top_of[y * room.w + x] > 0

## Runs of cells of one height along each row; a run with an east, south or south-east neighbour GRID_MIN_H or more
## under it is swept onto every floor its sweep reaches that it stands that far over (a building's block: any lower
## neighbour, any lower floor).
func _grid_jobs(jobs: Dictionary) -> void:
	var k := TopdownLight.SUN_STEP
	for y in room.h:
		var x := 0
		while x < room.w:
			var h := _height[y * room.w + x]
			var x1 := x + 1
			while x1 < room.w and _height[y * room.w + x1] == h: x1 += 1
			# It casts when an east, south or south-east neighbour lies at least `least` under it (a drop of two levels,
			# or any drop from a building's block); a lesser step's shadow is the tiles' own.
			var least := 1 if _is_block(x, y) else TopdownLight.GRID_MIN_H
			var casts := false
			for cx in range(x, x1):
				if _below[y * room.w + cx] <= h - least:
					casts = true
					break
			if casts:
				var reach := h + 8
				var found := {}
				for cy in range(y, mini(room.h, y + 2 + ceili(reach * k.y / T))):
					for cx in range(x, mini(room.w, x1 + 1 + ceili(reach * k.x / T))):
						var i := cy * room.w + cx
						var p := plane[i]
						if p == NONE or h - p < least: continue
						var len := h - p
						if cx * T >= x1 * T + len * k.x or cy * T >= (y + 1) * T + len * k.y: continue
						found[p] = true
						_touch(p, i)
				for p in found: _job(jobs, p, [0, x * T, y * T, (x1 - x) * T, T, h - p])
			x = x1

## The tall props: each one's silhouette laid on the floor it stands on and, further along the sun's way, on every lower
## floor it reaches; a canopy over a higher floor beside it lays only what stands over that floor. Each prop's own floor
## shadow (the prop sheet's sprite) is noted, to keep the total under it at the cap.
func _prop_jobs(jobs: Dictionary) -> void:
	var k := TopdownLight.SUN_STEP
	for p in room.props:
		var art: Dictionary = p.art
		var c: Vector2i = p.cell
		var sw := Vector2i(c.x * T, (c.y + (p.size as Vector2i).y) * T)
		if art.has("shadow_rect") and int(p.level) >= 0:
			var sr: Array = art.shadow_rect
			var sa: Array = art.get("shadow_at", [0, 0])
			var q0 := int(p.level) * T
			if not _ovals.has(q0): _ovals[q0] = []
			_ovals[q0].append(Rect2i(sw + Vector2i(int(sa[0]), int(sa[1])), Vector2i(int(sr[2]), int(sr[3]))))
		if int(p.top) >= 0 or int(p.level) < 0 or not str(p.kind) in TopdownLight.CASTS: continue
		var base := int(p.level) * T
		var st := _stamp(str(p.kind), art, 0, _atlas)
		if st.is_empty(): continue
		var box := Rect2i(sw + (st[2] as Vector2i), (st[0] as Image).get_size())
		var far := box.merge(Rect2i(box.position + Vector2i((Vector2(base + 8, base + 8) * k).round()), box.size))
		var planes := {}
		for cy in range(maxi(0, floori(far.position.y / float(T))), mini(room.h, ceili(far.end.y / float(T)))):
			for cx in range(maxi(0, floori(far.position.x / float(T))), mini(room.w, ceili(far.end.x / float(T)))):
				var q := plane[cy * room.w + cx]
				if q != NONE and q < base + int(st[3]): planes[q] = true
		for q in planes:
			var s := st
			var at := box.position
			if q <= base: at += Vector2i((Vector2(base - q, base - q) * k).round())
			else:
				s = _stamp(str(p.kind), art, q - base, _atlas)
				if s.is_empty(): continue
				at = sw + (s[2] as Vector2i)
			var r := Rect2i(at, (s[0] as Image).get_size())
			var any := false
			for cy in range(maxi(0, floori(r.position.y / float(T))), mini(room.h, ceili(r.end.y / float(T)))):
				for cx in range(maxi(0, floori(r.position.x / float(T))), mini(room.w, ceili(r.end.x / float(T)))):
					if plane[cy * room.w + cx] != q: continue
					_touch(q, cy * room.w + cx)
					any = true
			if any: _job(jobs, q, [1, s[0], s[1], at])

## Each floor's pass on a scratch image: every shape's edge, then every body over them, then the cap where the tiles
## bake shade of their own (the first px under a face cleared, the next and the strip east of a higher west cell and
## the props' own floor shadows kept to the edge); then its own cells copied into the room's.
func _run(jobs: Dictionary) -> void:
	if jobs.is_empty(): return
	var w := image.get_width()
	var h := image.get_height()
	var scratch := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var edge_img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	edge_img.fill(edge())
	for p in jobs:
		scratch.fill(Color(0, 0, 0, 0))
		for body in [false, true]:
			for j in jobs[p]:
				if int(j[0]) == 0: _sweep(scratch, int(j[1]), int(j[2]), int(j[3]), int(j[4]), float(j[5]), body)
				else:
					var img: Image = j[2] if body else j[1]
					scratch.blit_rect_mask(img, img, Rect2i(Vector2i.ZERO, img.get_size()), j[3])
		var cells: PackedInt32Array = _touched.get(p, PackedInt32Array())
		if p >= 0:
			for i in cells:
				var cx := i % room.w
				var cy := i / room.w
				var at := Vector2i(cx * T, cy * T)
				if cx > 0 and _height[i - 1] > p and plane[i - 1] != NONE:
					scratch.blit_rect_mask(edge_img, scratch, Rect2i(at, Vector2i(TopdownLight.NEAR_PX, T)), at)
				if cy > 0 and _height[i - room.w] > p:
					scratch.fill_rect(Rect2i(at, Vector2i(T, 1)), Color(0, 0, 0, 0))
					scratch.blit_rect_mask(edge_img, scratch, Rect2i(at + Vector2i(0, 1), Vector2i(T, 1)), at + Vector2i(0, 1))
			for r in _ovals.get(p, []):
				var rr: Rect2i = (r as Rect2i).intersection(Rect2i(0, 0, w, h))
				if rr.has_area(): scratch.blit_rect_mask(edge_img, scratch, rr, rr.position)
		for i in cells:
			if shaded[i] == 1: continue
			shaded[i] = 1
			var at := Vector2i((i % room.w) * T, (i / room.w) * T)
			image.blit_rect(scratch, Rect2i(at, Vector2i(T, T)), at)

## The sweep of the rect (x0, y0, w, h) along the sun's step for `length` px of height, row by row: each pixel whose
## centre the moving rect covers. With `body`, the sweep of the rect drawn SHADOW_RIM_PX in from its east and south
## sides at the body's alpha (the rest of the shape is its stepped edge). The first row south of the rect is the
## tiles' contact shade's, and takes none.
static func _sweep(img: Image, x0: int, y0: int, w: int, h: int, length: float, body: bool) -> void:
	var k := TopdownLight.SUN_STEP
	var rim := TopdownLight.SHADOW_RIM_PX if body else 0
	var bw := w - rim
	var bh := h - rim
	var rows := bh + ceili(length * k.y)
	var col := BODY if body else edge()
	for i in rows:
		if i == h: continue
		var yc := i + 0.5
		var t0 := maxf(0.0, (yc - bh) / k.y)
		var t1 := minf(length, yc / k.y)
		if t1 < t0: continue
		var xa := ceili(t0 * k.x - 0.5)
		var xb := floori(bw + t1 * k.x - 0.5)
		if xb >= xa: img.fill_rect(Rect2i(x0 + xa, y0 + i, xb - xa + 1, 1), col)

## A prop's silhouette on the ground (cached per kind and height over its floor `dh`): every opaque pixel of its sprite
## (the first frame) stands as high as it is over the footprint's middle row, and lies that far along the sun's step
## from the footprint's middle. [the whole shape at the edge's alpha, its body (SHADOW_RIM_PX in from every side), the
## offset from the footprint's south-west corner, the sprite's height]; [] when the prop has no sprite.
static func _stamp(kind: String, art: Dictionary, dh: int, atlas: String) -> Array:
	var key := "%s|%s|%d" % [atlas, kind, dh]
	if _stamps.has(key): return _stamps[key]
	var out: Array = []
	var sheet := _props_sheet(atlas)
	var rr: Array = art.get("rect", [])
	if sheet != null and rr.size() == 4:
		var k := TopdownLight.SUN_STEP
		var origin: Array = art.get("origin", [0, 16])
		var fp: Array = art.get("footprint", [1, 1])
		var half := float(fp[1]) * T * 0.5
		var ref := float(origin[1]) - half
		var sw := int(rr[2])
		var sh := int(rr[3])
		var data := sheet.get_region(Rect2i(int(rr[0]), int(rr[1]), sw, sh)).get_data()
		var pts := PackedInt32Array()
		var lo := Vector2i(1 << 20, 1 << 20)
		var hi := Vector2i(-(1 << 20), -(1 << 20))
		for sy in sh:
			var t := maxf(0.0, ref - (sy + 0.5))
			if dh > 0:
				if t <= dh: continue
				t -= dh
			var gy := floori(-half + t * k.y)
			for sx in sw:
				if data[(sy * sw + sx) * 4 + 3] < 128: continue
				var gx := floori(sx + 0.5 - float(origin[0]) + t * k.x)
				pts.append(gx)
				pts.append(gy)
				lo = Vector2i(mini(lo.x, gx), mini(lo.y, gy))
				hi = Vector2i(maxi(hi.x, gx), maxi(hi.y, gy))
		if not pts.is_empty():
			var size := hi - lo + Vector2i.ONE
			var mask := PackedByteArray()
			mask.resize(size.x * size.y)
			for i in range(0, pts.size(), 2): mask[(pts[i + 1] - lo.y) * size.x + pts[i] - lo.x] = 1
			var core := _erode(mask, size, TopdownLight.SHADOW_RIM_PX)
			var full := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
			var body := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
			var e := edge()
			for y in size.y:
				for x in size.x:
					if mask[y * size.x + x] == 0: continue
					full.set_pixel(x, y, e)
					if core[y * size.x + x] == 1: body.set_pixel(x, y, BODY)
			out = [full, body, lo, maxi(0, int(ref))]
	_stamps[key] = out
	return out

## The pixels of `mask` (size w x h, 1 = set) whose every neighbour within `r` px across and down is set too: a min
## filter along the rows, then down the columns.
static func _erode(mask: PackedByteArray, size: Vector2i, r: int) -> PackedByteArray:
	var across := PackedByteArray()
	across.resize(mask.size())
	for y in size.y:
		for x in size.x:
			var ok := 1
			for d in range(-r, r + 1):
				var xx := x + d
				if xx < 0 or xx >= size.x or mask[y * size.x + xx] == 0:
					ok = 0
					break
			across[y * size.x + x] = ok
	var out := PackedByteArray()
	out.resize(mask.size())
	for y in size.y:
		for x in size.x:
			var ok := 1
			for d in range(-r, r + 1):
				var yy := y + d
				if yy < 0 or yy >= size.y or across[yy * size.x + x] == 0:
					ok = 0
					break
			out[y * size.x + x] = ok
	return out

## The props atlas as an image, read once per path.
static func _props_sheet(path: String) -> Image:
	if not _sheets.has(path):
		var img: Image = null
		var tex = load(path) if path != "" and ResourceLoader.exists(path) else null
		if tex is Texture2D: img = (tex as Texture2D).get_image()
		if img != null:
			if img.is_compressed(): img.decompress()
			img.convert(Image.FORMAT_RGBA8)
		_sheets[path] = img
	return _sheets[path]

# ------------------------------------------------------------------ drawing
## The runs of shadowed cells of a floor, as [dest (room art px on screen), src (in the texture)]: `which` is "water"
## (drawn half a level down), "ground" (level 0) or a row index (that row's raised tops, each at its level's lift).
func runs(which) -> Array:
	if _runs.is_empty():
		# One pass over the room: each run of shadowed cells of one floor along a row, filed by where it is drawn.
		_runs = {"water": [], "ground": []}
		for y in room.h:
			var x := 0
			while x < room.w:
				var i := y * room.w + x
				var p := plane[i]
				if shaded[i] != 1 or p == NONE:
					x += 1
					continue
				var x1 := x + 1
				while x1 < room.w and shaded[i + x1 - x] == 1 and plane[i + x1 - x] == p: x1 += 1
				var lift := 8.0 if p < 0 else -float(p)
				var key = "water" if p < 0 else ("ground" if p == 0 else y)
				if not _runs.has(key): _runs[key] = []
				_runs[key].append([Rect2(x * T, y * T + lift, (x1 - x) * T, T), Rect2(x * T, y * T, (x1 - x) * T, T)])
				x = x1
	return _runs.get(which, [])

## A node that lays the runs of `which` in SHADOW; `origin` is where it sits in its parent (a raised row's strip sits at
## its sort key). Null when there is nothing to lay.
func view(which, origin := Vector2.ZERO) -> Node2D:
	var list := runs(which)
	if list.is_empty(): return null
	var v := Shade.new()
	v.texture = texture
	v.list = list
	v.origin = origin
	v.material = shade_material(str(which) == "water")
	return v

## The cast shadow's material: SHADOW at the texture's step (body or edge) x the alpha; the water's caps it at 0.25.
## One material for every floor node (one for the water's), so the hour's strength is one parameter.
static func shade_material(water := false) -> ShaderMaterial:
	if water and _water_material != null: return _water_material
	if not water and _material != null: return _material
	var m := ShaderMaterial.new()
	m.shader = shade_shader()
	var c := TopdownLight.SHADOW
	m.set_shader_parameter("tint", Vector3(c.r, c.g, c.b))
	m.set_shader_parameter("alpha", TopdownLight.WATER_SHADOW if water else TopdownLight.SHADOW_BODY)
	if water: _water_material = m
	else: _material = m
	return m

## The hour's strength of the sun's shadows (faint under the moon), on both materials.
static func set_strength(k: float) -> void:
	shade_material(false).set_shader_parameter("alpha", TopdownLight.SHADOW_BODY * k)
	shade_material(true).set_shader_parameter("alpha", TopdownLight.WATER_SHADOW * k)

static func shade_shader() -> Shader:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = "shader_type canvas_item;\nuniform vec3 tint = vec3(0.141, 0.122, 0.31);\nuniform float alpha = 0.41;\n" \
			+ "void fragment() {\n\tCOLOR = vec4(tint, texture(TEXTURE, UV).a * alpha * COLOR.a);\n}\n"
	return _shader

class Shade extends Node2D:
	var texture: Texture2D
	var list: Array = []
	var origin := Vector2.ZERO
	func _init() -> void:
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func _draw() -> void:
		for r in list: draw_texture_rect_region(texture, Rect2((r[0] as Rect2).position - origin, (r[0] as Rect2).size), r[1])
