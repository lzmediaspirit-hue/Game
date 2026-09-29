extends TopdownFigure
## Decision 42's quality study, option C: the game's compositor (TopdownFigure, unchanged) with sheets drawn at a
## density `px` times the world's. Each layer is drawn at 1/`density` scale into a world viewport rendered at the
## screen's resolution (1280x720, the camera at zoom 2), so one figure px lands on one screen px over tiles still drawn
## two screen px to the art px. A study only: the game never loads this script.

var density := 2.0

## Draw the figure with its feet at `feet`, as TopdownFigure.draw does, at 1/density scale.
func draw(ci: CanvasItem, feet: Vector2, action: String, row: String, i: int, tint := Color.WHITE) -> void:
	if not loaded(): return
	var fm := frame_of(action, row, i)
	var k := fm.x * 6
	var s := 1.0 / density
	ci.draw_set_transform(feet, 0.0, Vector2(-s, s) if fm.y == 1 else Vector2(s, s))
	for l in layers:
		var r: PackedInt32Array = l.rects
		if r[k + 2] == 0: continue
		ci.draw_texture_rect_region(l.tex, Rect2(r[k + 4], r[k + 5], r[k + 2], r[k + 3]), Rect2(r[k], r[k + 1], r[k + 2], r[k + 3]), tint)
	ci.draw_set_transform(Vector2.ZERO)

## What the figure covers from its feet, in the world's art px.
func bounds(action: String, row: String, i: int) -> Rect2:
	var b := super.bounds(action, row, i)
	return Rect2(b.position / density, b.size / density)
