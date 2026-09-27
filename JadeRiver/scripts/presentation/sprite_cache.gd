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
## 32 renders of them, 32 HUD glyphs).
const ICON_PX := [64, 48, 32]
static var _renders: Dictionary = {}
## The ui_suite's record of every icon drawn, [{id, rect, art, scale}]; null (off) in play.
static var draw_log = null

## Every render of an icon: art px -> texture. An HD icon lists its native renders in the manifest as
## `<id>@<px>`, each drawn 1:1 at that many px (or a whole multiple); a legacy icon has only its PNG, which holds
## its art at 2 screen px per art px (32 art px in a 64 px PNG, 16 for a HUD glyph, 12 for a status icon).
static func icon_renders(id: String) -> Dictionary:
	if _renders.has(id): return _renders[id]
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	var key := icon_key(id)
	var out := {}
	for px in ICON_PX:
		var t := tex(str(manifest.get("%s@%d" % [key, px], "")))
		if t: out[px] = t
	if out.is_empty():
		var t := tex(str(manifest.get(key, "")))
		if t: out[int(t.get_width() * 0.5)] = t
	_renders[id] = out
	return out

## True when the icon is drawn in the HD style (its family has been converted).
static func icon_hd(id: String) -> bool:
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	return ICON_PX.any(func(px): return manifest.has("%s@%d" % [icon_key(id), px]))

## How an icon is drawn in a `box` px square: the render and whole-number scale that give the largest size not over
## the box (the larger native render on a tie), or the smallest render at 1x when none fits.
## {tex, art, scale, px: the drawn size}; {} when it has no art.
static func icon_fit(id: String, box: float) -> Dictionary:
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
	var anchor := Vector2(float(e.anchor[0]), float(e.anchor[1]))
	var src := Rect2(col * fw, 0, fw, fh)
	if flip:
		ci.draw_set_transform(pos, 0.0, Vector2(-1, 1))
		ci.draw_texture_rect_region(texture, Rect2(-anchor, Vector2(fw, fh)), src, modulate)
		ci.draw_set_transform(Vector2.ZERO)
	else:
		ci.draw_texture_rect_region(texture, Rect2(pos - anchor, Vector2(fw, fh)), src, modulate)
	return true

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
