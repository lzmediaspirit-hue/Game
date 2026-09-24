class_name CreatureSprite
extends Node2D
## Draws one creature sheet (data/creature_art.json): rows are actions, columns
## frames, right-facing art mirrored for facing left. Anchor = ground contact.
## Until a creature's art exists, a simple element-tinted silhouette stands in.

var creature_id := ""
var action := "idle"
var t := 0.0
var facing := 1
var fallback_size := Vector2(40, 40)
var fallback_color := Color("8a7a58")
var mat: ShaderMaterial

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mat = SpriteCache.new_flash_material()
	material = mat

func set_flash(v: float) -> void:
	if mat: mat.set_shader_parameter("flash", clampf(v, 0.0, 1.0))

func set_fade(v: float) -> void:
	if mat: mat.set_shader_parameter("fade", clampf(v, 0.0, 1.0))

func set_tint(c: Color) -> void:
	if mat: mat.set_shader_parameter("tint", c)

func play(next: String, restart := false) -> void:
	if next != action or restart:
		action = next
		t = 0.0

func frame_count(act: String) -> int:
	var e := SpriteCache.creature(creature_id)
	return int(e.get("actions", {}).get(act, {}).get("frames", 1))

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	var e := SpriteCache.creature(creature_id)
	var texture: Texture2D = SpriteCache.tex(str(e.get("file", ""))) if not e.is_empty() else null
	if texture == null:
		_draw_fallback()
		return
	var acts: Dictionary = e.actions
	var a: Dictionary = acts.get(action, acts.get("idle", {}))
	var frames := int(a.get("frames", 1))
	var idx := int(t * float(a.get("fps", 8)))
	idx = idx % frames if a.get("loop", false) else mini(idx, frames - 1)
	var cell := float(e.cell)
	var anchor := Vector2(float(e.anchor[0]), float(e.anchor[1]))
	var src := Rect2(idx * cell, int(a.get("row", 0)) * cell, cell, cell)
	if facing < 0:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(-1, 1))
	draw_texture_rect_region(texture, Rect2(-anchor, Vector2(cell, cell)), src)
	draw_set_transform(Vector2.ZERO)

func _draw_fallback() -> void:
	var s := fallback_size
	var bob := sin(t * 5.0) * 2.0 if action in ["idle", "walk"] else 0.0
	var lunge := 8.0 * facing if action == "attack" else (-4.0 * facing if action == "windup" else 0.0)
	var body := Rect2(Vector2(-s.x * 0.5 + lunge, -s.y + bob), s)
	draw_rect(body.grow(2), Color("071015"))
	draw_rect(body, fallback_color)
	draw_rect(Rect2(body.position + Vector2(2, 2), Vector2(s.x - 4, s.y * 0.35)), fallback_color.lightened(0.25))
	var eye_x := body.get_center().x + facing * s.x * 0.25
	draw_rect(Rect2(eye_x - 2, body.position.y + s.y * 0.3, 4, 4), Color("f4ecd5"))
	if action == "death":
		set_fade(1.0 - clampf(t, 0.0, 1.0))
