extends Control
## Sky panorama (S17 layer 1, Part 9.2): layered parallax backdrops from
## data/backdrops.json, each layer tiled horizontally and anchored at its bottom
## edge. Rooms name a backdrop id; the painted v0.13 images stay as fallbacks
## (forest, cave, sanctuary). The Jade River runs through every outdoor panorama.

var world: Node2D
var image: Texture2D
var time := 0.0
var biome_images: Dictionary = {}
var current := ""
var layers: Array = []          # [{tex, parallax, bottom}]
var sky_top := Color("9fc3c7")
var sky_horizon := Color("e8e1cf")
var fade_from: Array = []
var fade_t := 0.0
var tint := Color.WHITE

const FALLBACK := {"valley_day": "forest", "valley_dusk": "sanctuary", "valley_night": "sanctuary", "marsh": "forest",
	"bamboo": "forest", "quarry": "forest", "mist_peak": "forest", "gorge": "forest", "cave": "cave", "sect_jade": "forest",
	"sect_cloud": "forest", "interior": "sanctuary"}

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	image = load("res://art/environment/sanctuary-v3.png")
	var atlas: Texture2D = load("res://art/environment/biomes-v6.png")
	for biome in ["forest", "cave"]:
		var texture := AtlasTexture.new()
		texture.atlas = atlas
		texture.region = Rect2(0, 0 if biome == "forest" else atlas.get_height() / 2, atlas.get_width(), atlas.get_height() / 2)
		biome_images[biome] = texture
	biome_images["sanctuary"] = image
	set_backdrop("valley_day")

func set_backdrop(id: String) -> void:
	if id == current: return
	fade_from = layers.duplicate()
	fade_t = 1.0 if not layers.is_empty() else 0.0
	current = id
	layers.clear()
	var e: Dictionary = ContentDB.config("backdrops").get(id, {})
	for l in e.get("layers", []):
		var tex := SpriteCache.tex(str(l.get("file", "")))
		if tex: layers.append({"tex": tex, "parallax": float(l.get("parallax", 0.0)), "bottom": float(l.get("bottom", 720))})
	sky_top = Color(str(e.get("sky", "#9fc3c7")))
	sky_horizon = Color(str(e.get("horizon", "#e8e1cf")))

func _process(delta: float) -> void:
	time += delta
	if fade_t > 0.0: fade_t = maxf(0.0, fade_t - delta / 0.6)
	if is_instance_valid(world):
		var want := str(world.map_data.get("background", "valley_day"))
		if want != current: set_backdrop(want)
		tint = Color("8fa0c8") if bool(world.room_def.get("night", false)) else Color.WHITE
	queue_redraw()

func _draw() -> void:
	var view := get_viewport_rect().size
	var cam := Vector2(640, 360)
	if is_instance_valid(world) and world.camera: cam = world.camera.position
	if layers.is_empty():
		_draw_painted(view, cam)
	else:
		_draw_layers(layers, view, cam, 1.0)
		if fade_t > 0.0 and not fade_from.is_empty(): _draw_layers(fade_from, view, cam, fade_t)
	# Translucent mist planes add near/far depth without seams.
	if is_instance_valid(world):
		for i in 3:
			var y := 420 + i * 110 - cam.y * (0.12 + i * 0.06)
			var points := PackedVector2Array()
			for x in range(-100, 1500, 60):
				points.append(Vector2(x, y + sin(x * 0.007 + time * 0.08 + i - cam.x * 0.0002) * 22))
			points.append(Vector2(1500, 900))
			points.append(Vector2(-100, 900))
			draw_colored_polygon(points, Color(0.5, 0.77, 0.78, 0.035))

func _draw_layers(ls: Array, view: Vector2, cam: Vector2, alpha: float) -> void:
	# Sky gradient behind everything.
	var steps := 12
	for i in steps:
		var f := float(i) / steps
		draw_rect(Rect2(0, view.y * f, view.x, view.y / steps + 1), Color(sky_top.lerp(sky_horizon, f), alpha) * Color(tint, 1.0))
	var vy := (cam.y - 600.0) * 0.12
	for l in ls:
		var tex: Texture2D = l.tex
		var w := float(tex.get_width())
		var h := float(tex.get_height())
		var off := fposmod(-(cam.x - 640.0) * float(l.parallax), w)
		var top := float(l.bottom) - h - vy * float(l.parallax) * 2.0
		var x := off - w
		while x < view.x:
			draw_texture_rect(tex, Rect2(x, top, w, h), false, Color(tint.r, tint.g, tint.b, alpha))
			x += w

func _draw_painted(view: Vector2, cam: Vector2) -> void:
	var scenery: Texture2D = biome_images.get(str(FALLBACK.get(current, "forest")), image)
	var shift := (cam - Vector2(640, 360)) * Vector2(0.055, 0.10)
	var factor := maxf((view.x + 400) / scenery.get_width(), (view.y + 180) / scenery.get_height())
	var drawn := scenery.get_size() * factor
	var margin := (drawn - view) * 0.5
	shift.x = clampf(shift.x, -margin.x, margin.x)
	shift.y = clampf(shift.y, -margin.y, margin.y)
	draw_texture_rect(scenery, Rect2((view - drawn) / 2 - shift, drawn), false, tint)
	if not is_instance_valid(world):
		draw_rect(Rect2(Vector2.ZERO, view), Color(0.015, 0.04, 0.065, 0.25))
