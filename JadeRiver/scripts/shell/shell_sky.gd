class_name ShellSky
extends Control
## The sky behind the title, the character selection and the creator (S12a, decision 45: the side view's river
## backdrop is retired): far karst peaks standing out of a sea of cloud that drifts on the wind, in the top-down
## world's own vista strips (art/topdown/vista.png, the strips TopdownVista lays past a room's edge) and its sky bands.
## Drawn at two screen px an art px, nearest-neighbour, as the rooms are; it redraws only when the cloud has drifted a
## whole art px. main.gd hides it while a world is mounted.

const PX := 2.0                 ## screen px an art px
const DRIFT := 3.0              ## art px a second the nearest cloud drifts
## The layers back to front: [strip, its bottom in art px from the top of the 360 art px screen, how fast it drifts as
## a share of DRIFT]. The far peaks stand still; the cloud between them and the nearer peaks drifts.
const LAYERS := [["peaks_far", 214.0, 0.0], ["cloud_sea", 226.0, 0.35], ["peaks_mid", 250.0, 0.1], ["cloud_sea", 266.0, 0.6],
	["cloud_sea", 300.0, 0.8], ["cloud_sea", 336.0, 1.0], ["cloud_sea", 372.0, 1.2]]

var tex: Texture2D
var strips: Dictionary = {}
var t := 0.0
var _drawn := -1

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var a := TopdownLife.art()
	strips = a.get("vistas", {})
	if a.has("vista_sheet"): tex = load(str(a.vista_sheet))

func _process(delta: float) -> void:
	if not visible: return
	t += delta
	var step := int(t * DRIFT)
	if step != _drawn:
		_drawn = step
		queue_redraw()

func _draw() -> void:
	var view := get_viewport_rect().size / PX
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(PX, PX))
	# The sky in bands, bluer high and paler toward the horizon behind the far peaks.
	var sky: Array = TopdownVista.SKY
	var band := ceilf(190.0 / sky.size())
	for i in sky.size():
		draw_rect(Rect2(0, i * band, view.x, band + 1.0), sky[i])
	# Under the horizon the haze of the cloud sea, deepening down to the screen's foot.
	draw_rect(Rect2(0, 190, view.x, view.y - 190), TopdownVista.HAZE)
	if tex != null:
		for l in LAYERS: _strip(str(l[0]), float(l[1]), float(l[2]) * DRIFT * t, view.x)
	draw_set_transform(Vector2.ZERO)

## A strip tiled across the screen with its bottom at `bottom`, slid `shift` art px east (wrapped to its width).
func _strip(name: String, bottom: float, shift: float, width: float) -> void:
	if not strips.has(name): return
	var r: Array = strips[name]
	var w := float(r[2])
	var h := float(r[3])
	var x := fposmod(floorf(shift), w) - w
	while x < width:
		draw_texture_rect_region(tex, Rect2(x, bottom - h, w, h), Rect2(float(r[0]), float(r[1]), w, h))
		x += w
