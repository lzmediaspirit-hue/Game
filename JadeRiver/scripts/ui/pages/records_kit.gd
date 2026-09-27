class_name RecordsKit
extends RefCounted
## P5 · The Records family's shared pieces (docs/page_identity.md §2, "Records": paper and ink, `scroll`, `PAPER_INK`,
## `BLOOD` seals): the Dialogue strip, the Quests board, the Mail's letter case, the Notice Board and the Codex draw their
## own layouts from these. Every piece draws on the page it is given, from tokens and the HD kit's paper faces, and names
## the ground its words sit on (Page.ground, Page.face), so the ui_suite measures them.

## Ink on paper, each a token or a mix of two, measured on the paper by the ui_suite.
static var INK := UiKit.PAPER_INK
static var BROWN := UiKit.PAPER_INK.lerp(UiKit.BRONZE, 0.45)
static var FADED := UiKit.PAPER_INK.lerp(UiKit.HOLLOW, 0.5)
static var RED_INK := UiKit.BLOOD.lerp(UiKit.INK, 0.15)
static var JADE_INK := UiKit.JADE_SHADOW
static var NEXT_INK := UiKit.BRONZE.lerp(UiKit.INK, 0.3)
## The paper where the light falls (the top of a sheet).
static var PAPER_LIT := UiKit.SURFACE.scroll.lerp(UiKit.PAPER, 0.5)

## Dark timber with the grain every 3 px and a plank seam every `seam` px, in a bronze-lined frame (the Quests board, the
## Mail's desk). `across` runs the grain sideways (a board hung on a wall) or down (a desk seen from above).
static func timber(pg: Page, r: Rect2, base: Color, across := true, seam := 74.0) -> void:
	pg.rounded(r.grow(2), 8.0, UiKit.INK)
	pg.rounded(r, 6.0, base)
	var span := r.size.y if across else r.size.x
	var k := 2.0
	while k < span:
		var line := Rect2(r.position.x + 10, r.position.y + k, r.size.x - 20, 1) if across else Rect2(r.position.x + k, r.position.y + 10, 1, r.size.y - 20)
		pg.draw_rect(line, Color(UiKit.INK, 0.16))
		k += 3.0
	k = seam
	while k < span - 12.0:
		var s := Rect2(r.position.x + 10, r.position.y + k, r.size.x - 20, 2) if across else Rect2(r.position.x + k, r.position.y + 10, 2, r.size.y - 20)
		pg.draw_rect(s, Color(UiKit.BRONZE, 0.22))
		k += seam
	# The frame: an ink edge, a bronze fillet, a dark inner line.
	pg.draw_rect(r.grow(-10), Color(UiKit.INK, 0.5), false, 2.0)
	pg.draw_rect(r.grow(-11), Color(UiKit.BRONZE, 0.9), false, 2.0)
	pg.draw_rect(r.grow(-13), Color(UiKit.INK, 0.6), false, 2.0)
	pg.ground(r, base)

## A pin's head (bronze, or gold for the story and the reading slip) with its shadow.
static func pin(pg: Page, at: Vector2, gold := false) -> void:
	pg.draw_circle(at + Vector2(2, 3), 6.5, Color(UiKit.INK, 0.45), true, -1.0, true)
	pg.draw_circle(at, 7.5, UiKit.INK, true, -1.0, true)
	pg.draw_circle(at, 6.0, UiKit.GOLD if gold else UiKit.BRONZE, true, -1.0, true)
	pg.draw_circle(at + Vector2(-1.5, -1.5), 2.5, UiKit.PALE_GOLD if gold else UiKit.BRONZE.lerp(UiKit.PALE_GOLD, 0.5), true, -1.0, true)

## A paper slip torn off its pad: the HD `paper_slip` face with its torn teeth along the top (a steady pattern from where
## the slip hangs). `lit` rings it in pale gold (the one being read).
static func slip(pg: Page, r: Rect2, lit := false) -> void:
	if lit: pg.rounded(r.grow_individual(3, -2, 3, 3), 4.0, UiKit.PALE_GOLD)
	pg.face(Rect2(r.position + Vector2(0, 4), r.size - Vector2(0, 4)), "paper_slip")
	var pts := PackedVector2Array([Vector2(r.position.x + 1, r.position.y + 6)])
	var x := r.position.x + 1.0
	var i := int(r.position.x * 7.0 + r.position.y * 3.0)
	while x < r.end.x - 1.0:
		x = minf(r.end.x - 1.0, x + 7.0 + float(i % 5))
		pts.append(Vector2(x, r.position.y + float([1, 4, 0, 5, 2, 3][i % 6])))
		i += 3
	pts.append(Vector2(r.end.x - 1, r.position.y + 6))
	pg.draw_colored_polygon(pts, PAPER_LIT)

## A band across a slip's head (the story's red, a side quest's jade, a mission's bronze) with its words inked on it.
static func head(pg: Page, r: Rect2, col: Color, words: String, size := 14) -> void:
	pg.vshade(r, col.lerp(UiKit.RED, 0.25) if col == UiKit.BLOOD else col.lerp(UiKit.PAPER, 0.12), col)
	pg.draw_rect(Rect2(r.position.x, r.end.y - 2, r.size.x, 2), Color(UiKit.GOLD, 0.8))
	pg.ground(r, col)
	pg.text(r.position + Vector2(12, r.size.y * 0.5 + size * 0.36), words, size, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)

## A plank nailed to the board with its words carved in (a group's name and its count). Returns its rect.
static func plank(pg: Page, at: Vector2, words: String, count := "", h := 34.0) -> Rect2:
	var w := UiKit.text_width(words, 16) + (UiKit.text_width(count, 16) + 10.0 if count != "" else 0.0) + 24.0
	var r := Rect2(at, Vector2(w, h))
	pg.rounded(r.grow(1), 4.0, UiKit.INK)
	pg.vshade(r, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.2), UiKit.SURFACE.wood.lerp(UiKit.INK, 0.15))
	pg.draw_rect(r.grow(-2), Color(UiKit.BRONZE, 0.9), false, 1.5)
	pg.ground(r, UiKit.SURFACE.wood.lerp(UiKit.INK, 0.15))
	pg.text(r.position + Vector2(12, h * 0.5 + 6), words, 16, UiKit.PALE_GOLD)
	if count != "": pg.text(Vector2(r.end.x - 12 - UiKit.text_width(count, 16), r.position.y + h * 0.5 + 6), count, 16, UiKit.PAPER)
	return r

## A seal stamped in red ink: a ring with its word across it (a finished slip, a claimed parcel, a taken bounty).
static func stamp(pg: Page, c: Vector2, word: String, radius := 26.0) -> void:
	pg.draw_arc(c, radius, 0.0, TAU, 40, Color(UiKit.BLOOD, 0.85), 3.0, true)
	pg.draw_arc(c, radius - 5.0, 0.0, TAU, 40, Color(UiKit.BLOOD, 0.6), 1.5, true)
	pg.text(Vector2(c.x - radius, c.y + 6), word, 16 if radius >= 24.0 else 14, RED_INK, HORIZONTAL_ALIGNMENT_CENTER, radius * 2.0)

## A red wax seal (an unread letter), or its broken half once read.
static func wax(pg: Page, c: Vector2, broken := false) -> void:
	if broken:
		pg.draw_colored_polygon(PackedVector2Array([c + Vector2(-2, -15), c + Vector2(-15, -6), c + Vector2(-15, 7), c + Vector2(-4, 15), c + Vector2(2, 4), c + Vector2(-3, -3)]),
			Color(UiKit.BLOOD.lerp(UiKit.PAPER, 0.35), 0.8))
		return
	pg.draw_circle(c + Vector2(1, 2), 15.0, Color(UiKit.INK, 0.3), true, -1.0, true)
	pg.draw_circle(c, 15.0, UiKit.BLOOD.lerp(UiKit.INK, 0.25), true, -1.0, true)
	pg.draw_circle(c + Vector2(-1, -1), 12.5, UiKit.BLOOD, true, -1.0, true)
	var d := 6.0
	pg.draw_polyline(PackedVector2Array([c + Vector2(0, -d), c + Vector2(d, 0), c + Vector2(0, d), c + Vector2(-d, 0), c + Vector2(0, -d)]), Color(UiKit.PALE_GOLD, 0.7), 2.0, true)

## Hemp string tied round a parcel or an envelope: one line across, one down at `knot_x`, and a bow (or the loose ends,
## untied, once what it held was taken).
static func string_tie(pg: Page, r: Rect2, knot_x: float, tied := true) -> void:
	var col := UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.55)
	var y := r.get_center().y
	if tied:
		pg.draw_line(Vector2(r.position.x, y), Vector2(r.end.x, y), col, 3.0, true)
		pg.draw_line(Vector2(knot_x, r.position.y), Vector2(knot_x, r.end.y), col, 3.0, true)
	for side in [-1.0, 1.0]:
		var loop := PackedVector2Array()
		for i in 13:
			var a := TAU * float(i) / 12.0
			loop.append(Vector2(knot_x + side * (14.0 + cos(a) * 12.0), y + sin(a) * 8.0))
		if tied: pg.draw_polyline(loop, col, 2.5, true)
		else: pg.draw_line(Vector2(knot_x, y), Vector2(knot_x + side * 22.0, y + 14.0), Color(col, 0.7), 2.5, true)
	pg.draw_circle(Vector2(knot_x, y), 4.5, col, true, -1.0, true)
