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

static func prop(id: String) -> Dictionary:
	return ContentDB.config("prop_art").get(id, {})

static func creature(id: String) -> Dictionary:
	return ContentDB.config("creature_art").get(id, {})

## An item without its own drawing borrows the one named by its `icon` field.
static func icon_path(id: String) -> String:
	var manifest: Dictionary = ContentDB.config("icon_manifest")
	if manifest.has(id): return str(manifest[id])
	return str(manifest.get(str(ContentDB.item(id).get("icon", "")), ""))

static func icon(id: String) -> Texture2D:
	return tex(icon_path(id))

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
