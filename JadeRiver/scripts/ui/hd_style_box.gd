class_name HdStyleBox
extends StyleBox
## A nine-slice from the HD UI kit (tools/ui/build_ui_hd.py): art authored at `scale`
## texels per screen pixel, drawn scaled down with mipmapped linear filtering. The frame
## keeps its screen-pixel margins but is rasterized at the device's own resolution, so it
## stays sharp on phone screens where the canvas is scaled 1.5-3x.

var texture: Texture2D          # a CanvasTexture carrying the linear filter
var size_px := Vector2.ONE      # the source image size in texels
var margins := [8.0, 8.0, 8.0, 8.0]
var scale := 3.0

func _draw(to_canvas_item: RID, rect: Rect2) -> void:
	if texture == null: return
	var s := scale
	# Fixed-size art (no margins) keeps its proportions inside the rect.
	var fixed: bool = margins[0] == 0.0 and margins[1] == 0.0 and margins[2] == 0.0 and margins[3] == 0.0
	var ci := to_canvas_item
	RenderingServer.canvas_item_add_set_transform(ci, Transform2D(Vector2(1.0 / s, 0.0), Vector2(0.0, 1.0 / s), rect.position))
	var dest := Rect2(Vector2.ZERO, rect.size * s)
	if fixed:
		RenderingServer.canvas_item_add_texture_rect_region(ci, dest, texture.get_rid(), Rect2(Vector2.ZERO, size_px))
	else:
		# Margins never exceed the rect, so small boxes shrink their corners evenly. Art with no
		# centre along an axis (a plaque whose margins cover its full height) scales to fit instead.
		var art := size_px / s
		var k := minf(1.0, minf(rect.size.x / maxf(1.0, margins[0] + margins[2]), rect.size.y / maxf(1.0, margins[1] + margins[3])))
		if margins[1] + margins[3] >= art.y - 0.01: k = rect.size.y / art.y
		elif margins[0] + margins[2] >= art.x - 0.01: k = rect.size.x / art.x
		var tl := Vector2(margins[0], margins[1]) * s
		var br := Vector2(margins[2], margins[3]) * s
		if not is_equal_approx(k, 1.0):
			# Shrink the drawn rect's scale instead of distorting the corners.
			RenderingServer.canvas_item_add_set_transform(ci, Transform2D(Vector2(k / s, 0.0), Vector2(0.0, k / s), rect.position))
			dest = Rect2(Vector2.ZERO, rect.size * s / k)
		RenderingServer.canvas_item_add_nine_patch(ci, dest, Rect2(Vector2.ZERO, size_px), texture.get_rid(), tl, br,
			RenderingServer.NINE_PATCH_STRETCH, RenderingServer.NINE_PATCH_STRETCH, true)
	RenderingServer.canvas_item_add_set_transform(ci, Transform2D.IDENTITY)
