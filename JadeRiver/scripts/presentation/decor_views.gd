class_name DecorView
extends Node2D
## Non-interactive room art: decor props (depth-sorted with actors), water areas
## and interior walls. `kind` selects what to draw.

var kind := "prop"          # prop | water | wall | river
var prop_id := ""
var state := "idle"
var flip := false
var rect := Rect2()
var t := 0.0
var tile := ""
var tint := Color.WHITE
var animated := false

static func make_prop(d: Dictionary) -> DecorView:
	var v := DecorView.new()
	v.kind = "prop"
	v.prop_id = str(d.prop)
	v.state = str(d.get("state", "idle"))
	v.flip = bool(d.get("flip", false))
	var at: Array = d.get("at", [0, 0])
	v.position = Vector2(float(at[0]), float(at[1]) - float(d.get("alt", 0)))
	match str(d.get("layer", "play")):
		"back": v.z_index = -1900
		"front": v.z_index = 3000
		"far": v.z_index = -2050
		_: v.z_index = 1500 + int(float(at[1]))
	if d.has("tint"): v.tint = Color(str(d.tint))
	var st: Dictionary = SpriteCache.prop(v.prop_id).get("states", {}).get(v.state, {})
	v.animated = int(st.get("frames", 1)) > 1
	return v

static func make_area(kind_name: String, r: Rect2, tile_id: String, z: int) -> DecorView:
	var v := DecorView.new()
	v.kind = kind_name
	v.rect = r
	v.tile = tile_id
	v.z_index = z
	v.animated = kind_name in ["water", "river"]
	return v

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	set_process(animated)

func _process(delta: float) -> void:
	t += delta
	queue_redraw()

func _draw() -> void:
	match kind:
		"prop":
			SpriteCache.draw_prop(self, prop_id, state, t, Vector2.ZERO, flip, tint)
		"water", "river":
			if not SpriteCache.draw_tiled(self, tile, rect, t):
				draw_rect(rect, Color("1e5a64"))
			# Pale foam line where water meets the bank.
			for x in range(int(rect.position.x), int(rect.end.x), 8):
				var y := rect.position.y + sin(x * 0.05 + t * 2.0) * 2.0
				draw_rect(Rect2(x, y, 6, 2), Color(0.85, 0.95, 0.95, 0.5))
		"wall":
			if not SpriteCache.draw_tiled(self, tile, rect):
				draw_rect(rect, Color("3b2c22"))
			draw_rect(Rect2(rect.position.x, rect.end.y - 8, rect.size.x, 8), Color("2a1e16"))
			draw_rect(Rect2(rect.position.x, rect.end.y - 10, rect.size.x, 2), Color("8c6a48"))
