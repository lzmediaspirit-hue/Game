class_name SpriteCache
extends RefCounted
## Shared texture cache and drawing helpers for props, creatures and icons.
## All art is authored at native pixel scale 2 and drawn at 1× with nearest filtering.

static var _textures: Dictionary = {}
static var _flash_material: ShaderMaterial

static func tex(path: String) -> Texture2D:
	if path == "": return null
	if not _textures.has(path):
		_textures[path] = load(path) if ResourceLoader.exists(path) else null
	return _textures[path]

static var _slice_frame := -1
static var _slice_us := 0
const SLICE_BUDGET_US := 12000

## Pages ask for sheets this way: sheets not yet in memory load within a 12 ms budget per frame
## and the rest wait for the next frame (returning null, with `loading(path)` true), so opening a
## page full of creatures never stalls a frame.
static func tex_sliced(path: String) -> Texture2D:
	if path == "" or _textures.has(path): return tex(path)
	var frame := Engine.get_process_frames()
	if frame != _slice_frame:
		_slice_frame = frame
		_slice_us = 0
	if _slice_us >= SLICE_BUDGET_US: return null
	var t0 := Time.get_ticks_usec()
	var texture := tex(path)
	_slice_us += Time.get_ticks_usec() - t0
	return texture

## A sheet loaded on a loading thread: null until it is in memory (asked for on the first call), then the sheet.
static func tex_async(path: String) -> Texture2D:
	if path == "" or _textures.has(path): return tex(path)
	match ResourceLoader.load_threaded_get_status(path):
		ResourceLoader.THREAD_LOAD_LOADED:
			_textures[path] = ResourceLoader.load_threaded_get(path)
			return _textures[path]
		ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:   # not asked for yet
			if not ResourceLoader.exists(path) or ResourceLoader.load_threaded_request(path) != OK: return tex(path)
		ResourceLoader.THREAD_LOAD_FAILED: return tex(path)
	return null

static func loading(path: String) -> bool:
	return path != "" and not _textures.has(path)

static func prop(id: String) -> Dictionary:
	return ContentDB.config("prop_art").get(id, {})

static func creature(id: String) -> Dictionary:
	return ContentDB.config("creature_art").get(id, {})

## An item without its own drawing borrows the one named by its `icon` field.
static func icon_key(id: String) -> String:
	return id if ContentDB.config("icon_manifest").has(id) else str(ContentDB.item(id).get("icon", ""))

static func icon_path(id: String) -> String:
	return str(ContentDB.config("icon_manifest").get(icon_key(id), ""))

static func icon(id: String) -> Texture2D:
	return tex(icon_path(id))

# ------------------------------------------------------------------ crisp icons
## The art sizes an HD icon can be rendered at natively (tools/icons: 64 items, equipment and techniques, 48 and
## 32 renders of them, 32 HUD glyphs, 24 status icons and markers, and a 12 render of a status icon).
const ICON_PX := [64, 48, 32, 24, 12]
## Every native render a drawing may list (`<id>@<px>`): ICON_PX, and 96 for the Works cabinet's objects (P5, mockup
## 14 v4; tools/icons/families/works.py).
const RENDER_PX := [96, 64, 48, 32, 24, 12]
## The sizes a technique's emblem is composed at (the emblem atlas's sheets).
const EMBLEM_PX := [64, 48, 32]
static var _renders: Dictionary = {}
## The ui_suite's record of every icon drawn, [{id, rect, art, scale}]; null (off) in play.
static var draw_log = null

## Every render of an icon: art px -> texture. An HD icon lists its native renders in the manifest as
## `<id>@<px>`, each drawn 1:1 at that many px (or a whole multiple); a legacy icon has only its PNG, which holds
## its art at 2 screen px per art px (32 art px in a 64 px PNG).
static func icon_renders(id: String) -> Dictionary:
	if _renders.has(id): return _renders[id]
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	var key := icon_key(id)
	var out := {}
	for px in RENDER_PX:
		var t := tex(str(manifest.get("%s@%d" % [key, px], "")))
		if t: out[px] = t
	if out.is_empty():
		var t := tex(str(manifest.get(key, "")))
		if t: out[int(t.get_width() * 0.5)] = t
	if out.is_empty() and composable(id):
		for px in EMBLEM_PX:
			var e := emblem(id, px)
			if e: out[px] = e
	_renders[id] = out
	return out

## True when the icon is drawn in the HD style (its family has been converted, or it is a composed emblem).
static func icon_hd(id: String) -> bool:
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	return RENDER_PX.any(func(px): return manifest.has("%s@%d" % [icon_key(id), px])) or composable(id)

## How an icon is drawn in a `box` px square: the render and whole-number scale that give the largest size not over
## the box (the larger native render on a tie), or the smallest render at 1x when none fits.
## {tex, art, scale, px: the drawn size}; {} when it has no art.
static func icon_fit(id: String, box: float) -> Dictionary:
	if composable(id) and not _renders.has(id):
		# A composed emblem is composed at the one size the box takes, not at all three.
		var art := _emblem_px(box)
		var k := maxi(1, int(floor(box / float(art) + 0.001)))
		var e := emblem(id, art)
		return {} if e == null else {"tex": e, "art": art, "scale": k, "px": art * k}
	var renders := icon_renders(id)
	var best := {}
	for art in renders:
		var k := int(floor(box / float(art) + 0.001))
		if k >= 1 and (best.is_empty() or art * k > int(best["px"]) or (art * k == int(best["px"]) and art > int(best["art"]))):
			best = {"tex": renders[art], "art": art, "scale": k, "px": art * k}
	if best.is_empty() and not renders.is_empty():
		var art: int = renders.keys().min()
		best = {"tex": renders[art], "art": art, "scale": 1, "px": art}
	return best

## The emblem size a `box` px square takes: the one whose whole-number scale fills the most of it (the smallest when none
## fits).
static func _emblem_px(box: float) -> int:
	var art := 0
	var k := 0
	for px in EMBLEM_PX:
		var kk := int(floor(box / float(px) + 0.001))
		if kk >= 1 and (art == 0 or px * kk > art * k):
			art = px
			k = kk
	return art if art != 0 else int(EMBLEM_PX.min())

## True when icon `id` is in memory for a `box` px square: its renders loaded, or its emblem composed at that size.
static func icon_loaded(id: String, box: float) -> bool:
	if composable(id) and not _renders.has(id): return _emblems.has("%s@%d" % [id, _emblem_px(box)])
	return _renders.has(id)

## Icon `id`'s renders asked of loading threads (icon_renders then finds them in memory); a composed emblem has none.
static func icon_prefetch(id: String) -> void:
	if composable(id): return
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	var key := icon_key(id)
	for px in RENDER_PX: tex_async(str(manifest.get("%s@%d" % [key, px], "")))
	tex_async(str(manifest.get(key, "")))

## True when drawing icon `id` in a `box` px square composes nothing (a baked icon, or an emblem already composed at
## that size): a page may hold back an emblem not yet composed for a later frame.
static func icon_ready(id: String, box: float) -> bool:
	return not composable(id) or _renders.has(id) or _emblems.has("%s@%d" % [id, _emblem_px(box)])

## Draw icon `id` centred in `rect` on whole pixels at a whole-number scale of its art (icon_fit), never a filtered
## or fractional scale. `box` overrides the size asked for (the HUD's technique ring asks 64 of a legacy icon, its
## 32 art px at 2x, and 48 of an HD one, its native 48). Returns the drawn rect, Rect2() when there is no art.
## Every icon on a page, the HUD and the world is drawn through here.
static func draw_icon(ci: CanvasItem, rect: Rect2, id: String, modulate := Color.WHITE, box := -1.0) -> Rect2:
	var f := icon_fit(id, box if box > 0.0 else minf(rect.size.x, rect.size.y))
	if f.is_empty(): return Rect2()
	var s := float(f["px"])
	var r := Rect2((rect.get_center() - Vector2(s, s) * 0.5).round(), Vector2(s, s))
	ci.draw_texture_rect(f["tex"], r, false, modulate)
	if draw_log != null: draw_log.append({"id": id, "rect": r, "art": int(f["art"]), "scale": s / float(f["art"])})
	return r

## Draw one prop frame with its anchor at `pos`. Returns false when the art is missing.
static func draw_prop(ci: CanvasItem, id: String, state: String, t: float, pos: Vector2, flip := false, modulate := Color.WHITE) -> bool:
	var e := prop(id)
	if e.is_empty(): return false
	var texture := tex(str(e.file))
	if texture == null: return false
	var states: Dictionary = e.get("states", {})
	var st: Dictionary = states.get(state, {})
	if st.is_empty() and not states.is_empty(): st = states.values()[0]
	var fw := int(e.frame[0])
	var fh := int(e.frame[1])
	var frames := int(st.get("frames", 1))
	var col := int(st.get("col", 0)) + (int(t * float(st.get("fps", 6))) % frames if frames > 1 else 0)
	var src := Rect2(col * fw, 0, fw, fh)
	if flip:
		ci.draw_set_transform(pos, 0.0, Vector2(-1, 1))
		ci.draw_texture_rect_region(texture, prop_rect(id, Vector2.ZERO), src, modulate)
		ci.draw_set_transform(Vector2.ZERO)
	else:
		ci.draw_texture_rect_region(texture, prop_rect(id, pos), src, modulate)
	return true

## Where draw_prop draws a prop's frame with its anchor at `pos` (unflipped; a flip mirrors it about `pos.x`).
## Rect2() when it has no art.
static func prop_rect(id: String, pos: Vector2) -> Rect2:
	var e := prop(id)
	if e.is_empty(): return Rect2()
	return Rect2(pos - Vector2(float(e.anchor[0]), float(e.anchor[1])), Vector2(float(e.frame[0]), float(e.frame[1])))

static func prop_size(id: String) -> Vector2:
	var e := prop(id)
	return Vector2(float(e.frame[0]), float(e.frame[1])) if not e.is_empty() else Vector2.ZERO

## Tile a repeating prop/tile texture over `rect` (frame `col`).
static func draw_tiled(ci: CanvasItem, id: String, rect: Rect2, t := 0.0, modulate := Color.WHITE) -> bool:
	var e := prop(id)
	if e.is_empty(): return false
	var texture := tex(str(e.file))
	if texture == null: return false
	var fw := float(e.frame[0])
	var fh := float(e.frame[1])
	var st: Dictionary = e.get("states", {}).values()[0] if not e.get("states", {}).is_empty() else {}
	var frames := int(st.get("frames", 1))
	var col := int(st.get("col", 0)) + (int(t * float(st.get("fps", 5))) % frames if frames > 1 else 0)
	var y := rect.position.y
	while y < rect.end.y - 0.01:
		var h := minf(fh, rect.end.y - y)
		var x := rect.position.x
		while x < rect.end.x - 0.01:
			var w := minf(fw, rect.end.x - x)
			ci.draw_texture_rect_region(texture, Rect2(x, y, w, h), Rect2(col * fw, 0, w, h), modulate)
			x += fw
		y += fh
	return true

static func flash_material() -> ShaderMaterial:
	if _flash_material == null:
		var sh := Shader.new()
		sh.code = """shader_type canvas_item;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 tint : source_color = vec4(1.0);
uniform float fade : hint_range(0.0, 1.0) = 1.0;
void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	c.rgb = mix(c.rgb * tint.rgb, vec3(1.0), flash);
	c.a *= fade;
	COLOR = c;
}"""
		_flash_material = ShaderMaterial.new()
		_flash_material.shader = sh
	return _flash_material

static func new_flash_material() -> ShaderMaterial:
	var m := flash_material().duplicate() as ShaderMaterial
	return m

static func element_color(el: String) -> Color:
	var colors: Dictionary = ContentDB.config("elements").get("colors", {})
	return Color(str(colors.get(CombatRules.parent_element(el), colors.get(el, "#e8e1cf"))))

# ------------------------------------------------------------------ P13a composed technique emblems
## Every technique without a baked emblem (all but today's 56 arts) is composed from the emblem atlas (technique_plan
## §3.9, tools/icons/emblem_atlas.py): the element's disc under its grade's or kind's rim, the form's mark with its key
## colours swapped for the element's (or the path's), the path's stamp and a lost art's tear. Composed once per id and
## size, then kept (the plan's 256 held; a full cache starts again).
static var _emblems: Dictionary = {}
static var _sheets: Dictionary = {}
static var _pals: Dictionary = {}
const EMBLEMS_HELD := 256

static func composable(id: String) -> bool:
	return not ContentDB.config("icon_manifest").has(id) and ContentDB.has_entry("techniques", id) and ContentDB.config("emblem_atlas").has("cells")

## The layers of a technique's emblem: {base, mark, stamp, element, path}; the atlas builder's rule (emblem_atlas.spec)
## from the tables its index carries.
static func emblem_spec(t: Dictionary) -> Dictionary:
	var A := ContentDB.config("emblem_atlas")
	var el := str(A.get("element_of", {}).get(str(t.get("element", "none")), str(t.get("element", "none"))))
	var kind := str(t.get("kind", ""))
	var rim := str({"keystone": "keystone", "dao": "dao"}.get(kind, str(t.get("grade", "common"))))
	var mark := "form:" + str(t.form) if t.has("form") else str(A.get("templates", {}).get(str(t.get("template", "")), ""))
	var fam := str(A.get("kin_family", {}).get(str(t.get("kin", "voice")), "any")) if kind == "keystone" else str(t.get("family", "any"))
	var path := str(t.get("path", "")) if not kind in ["keystone", "dao"] else ""
	return {"base": "base:%s:%s%s" % [el, rim, ":torn" if kind == "lost" else ""], "mark": "%s:%s" % [mark, "any" if mark.begins_with("hand:") else fam],
		"stamp": "stamp:" + path if path != "" else "", "element": el, "path": path}

## True when every layer of the technique's emblem is in the atlas.
static func emblem_whole(id: String) -> bool:
	var cells: Dictionary = ContentDB.config("emblem_atlas").get("cells", {})
	var s := emblem_spec(ContentDB.entry("techniques", id))
	return cells.has(s.base) and cells.has(s.mark) and (str(s.stamp) == "" or cells.has(s.stamp)) and (not str(s.base).ends_with(":torn") or cells.has("tear"))

## The emblem of technique `id` at `px` art px (64, 48 or 32), or null.
static func emblem(id: String, px: int) -> Texture2D:
	var key := "%s@%d" % [id, px]
	if _emblems.has(key): return _emblems[key]
	var img := emblem_image(id, px)
	if img == null: return null
	var out := ImageTexture.create_from_image(img)
	if _emblems.size() >= EMBLEMS_HELD * 3: _emblems.clear()
	_emblems[key] = out
	return out

## The composed emblem as an Image (the tests read its pixels), or null.
static func emblem_image(id: String, px: int) -> Image:
	var A := ContentDB.config("emblem_atlas")
	var sheet := _sheet(px)
	var s := emblem_spec(ContentDB.entry("techniques", id))
	var cells: Dictionary = A.get("cells", {})
	if sheet == null or not cells.has(s.base) or not cells.has(s.mark): return null
	var data := sheet.get_region(_cell(cells[s.base], px)).get_data()
	var mark := sheet.get_region(_cell(cells[s.mark], px)).get_data()
	var pal := _palette(A, str(s.element), str(s.path))
	for i in range(0, mark.size(), 4):
		if mark[i + 3] == 0: continue
		var c: int = pal.get((mark[i] << 16) | (mark[i + 1] << 8) | mark[i + 2], (mark[i] << 16) | (mark[i + 1] << 8) | mark[i + 2])
		data[i] = (c >> 16) & 255
		data[i + 1] = (c >> 8) & 255
		data[i + 2] = c & 255
		data[i + 3] = 255
	if str(s.stamp) != "" and cells.has(s.stamp):
		var st := sheet.get_region(_cell(cells[s.stamp], px)).get_data()
		for i in range(0, st.size(), 4):
			if st[i + 3] > 0:
				for j in 4: data[i + j] = st[i + j]
	if str(s.base).ends_with(":torn") and cells.has("tear"):
		var tear := sheet.get_region(_cell(cells["tear"], px)).get_data()
		for i in range(0, tear.size(), 4):
			if tear[i + 3] > 0:
				for j in 4: data[i + j] = 0
	return Image.create_from_data(px, px, false, Image.FORMAT_RGBA8, data)

static func _cell(at: Array, px: int) -> Rect2i:
	return Rect2i(int(at[0]) * px, int(at[1]) * px, px, px)

## The atlas at `px` as an Image: imported as an Image (its .import says so), so it is read on the CPU, headless too.
static func _sheet(px: int) -> Image:
	if not _sheets.has(px):
		var path := str(ContentDB.config("emblem_atlas").get("files", {}).get(str(px), ""))
		var res = load(path) if path != "" and ResourceLoader.exists(path) else null
		var img: Image = res if res is Image else (res.get_image() if res is Texture2D else null)
		if img:
			img = img.duplicate()
			img.decompress()
			img.convert(Image.FORMAT_RGBA8)
		_sheets[px] = img
	return _sheets[px]

## Key colour -> the element's colour (a path art's mark takes the path's levels over its element's).
static func _palette(A: Dictionary, el: String, path: String) -> Dictionary:
	var key := el + "|" + path
	if _pals.has(key): return _pals[key]
	var P: Dictionary = A.get("palettes", {})
	var mark: Array = (P.get(el, {}).get("mark", []) as Array).duplicate()
	if P.has("path:" + path):
		var levels: Array = P["path:" + path]
		for i in mini(levels.size(), mark.size()): mark[i] = levels[i]
	var out := {}
	for pair in [[P.get("key_mark", []), mark], [P.get("key_steel", []), P.get(el, {}).get("steel", [])]]:
		for i in mini((pair[0] as Array).size(), (pair[1] as Array).size()):
			out[_rgb24(str(pair[0][i]))] = _rgb24(str(pair[1][i]))
	_pals[key] = out
	return out

static func _rgb24(hex: String) -> int:
	return Color.html(hex).to_rgba32() >> 8
