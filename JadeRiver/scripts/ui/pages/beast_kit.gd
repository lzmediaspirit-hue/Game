class_name BeastKit
extends RefCounted
## P5 · The Beasts family's shared pieces (docs/page_identity.md §2, "Beasts": straw and rough timber, `straw`, `wood`,
## `sand`, `clay`): Spirit Animals, the Core Exchange and the Beast Arena draw their own layouts from these. Every piece
## draws on the page it is given, from tokens, and names the ground its words sit on (Page.ground), so the ui_suite
## measures them.

## Rough timber over `r` (the Beast Hall's wall, a fence rail): boards of uneven width running down, each seam dark, with
## a knot here and there. Words on it read on `wood`.
static func timber(pg: Page, r: Rect2, seed_ := 0) -> void:
	var face: Color = UiKit.SURFACE.wood
	pg.draw_rect(r, face)
	var x := r.position.x
	var k := 0
	while x < r.end.x - 4.0:
		var w := 44.0 + 30.0 * HashNoise.scatter(seed_, k)
		var board := Rect2(x, r.position.y, minf(w, r.end.x - x), r.size.y)
		pg.draw_rect(Rect2(board.position.x + 3, board.position.y, board.size.x * 0.4, board.size.y), Color(face.lerp(UiKit.BRONZE, 0.18), 0.6))
		for g in 3:   # the grain
			var gx := board.position.x + board.size.x * (0.2 + 0.28 * g + 0.1 * HashNoise.scatter(seed_ + 7, k * 3 + g))
			pg.draw_line(Vector2(gx, board.position.y), Vector2(gx, board.end.y), Color(UiKit.SURFACE.wood_dark, 0.35), 1.0)
		if HashNoise.scatter(seed_ + 3, k) > 0.45:
			var knot := Vector2(board.position.x + board.size.x * (0.3 + 0.4 * HashNoise.scatter(seed_ + 5, k)), r.position.y + r.size.y * HashNoise.scatter(seed_ + 9, k))
			pg.draw_circle(knot, 5.0, UiKit.SURFACE.wood_dark, true, -1.0, true)
			pg.draw_arc(knot, 8.0, 0.0, TAU, 20, Color(UiKit.SURFACE.wood_dark, 0.5), 1.5, true)
		x += w
		pg.draw_rect(Rect2(x - 2, r.position.y, 3, r.size.y), UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.4))
		k += 1
	pg.ground(r, face.lerp(UiKit.BRONZE, 0.18))

## Straw over `r` (a stall's bedding, the resting corner): the straw fill with loose stalks lying every way over it.
## Words on it read on `straw`, in PAPER_INK.
static func straw(pg: Page, r: Rect2, seed_ := 0, stalks := -1) -> void:
	var base: Color = UiKit.SURFACE.straw
	pg.rounded(r, 10.0, base)
	var n := stalks if stalks >= 0 else int(r.size.x * r.size.y / 180.0)
	for i in n:
		var at := r.position + Vector2(8, 6) + Vector2((r.size.x - 16) * HashNoise.scatter(seed_, i * 2), (r.size.y - 12) * HashNoise.scatter(seed_, i * 2 + 1))
		var dir := Vector2.from_angle((HashNoise.scatter(seed_ + 1, i) - 0.5) * 1.4 + (PI if i % 2 == 0 else 0.0))
		var ln := 8.0 + 12.0 * HashNoise.scatter(seed_ + 2, i)
		var col := base.lerp(UiKit.PALE_GOLD, 0.35) if i % 3 == 0 else base.lerp(UiKit.BRONZE, 0.45)
		pg.draw_line(at, at + dir * ln, col, 1.5, true)
	pg.ground(r, base)

## A rough board with words cut into it (a name board, the title's sign): two planks, a nail at each end. Words on it
## are PALE_GOLD or PAPER on `wood`. Returns the board.
static func board(pg: Page, r: Rect2) -> Rect2:
	pg.rounded(r.grow(2), 4.0, UiKit.INK)
	pg.vshade(r, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.22), UiKit.SURFACE.wood)
	if r.size.y >= 40.0: pg.draw_rect(Rect2(r.position.x, r.get_center().y - 1, r.size.x, 2), Color(UiKit.SURFACE.wood_dark, 0.8))
	for nx in [r.position.x + 8.0, r.end.x - 8.0]:
		pg.draw_circle(Vector2(nx, r.position.y + 8), 2.5, UiKit.SURFACE.peg_dark, true, -1.0, true)
		pg.draw_circle(Vector2(nx - 0.6, r.position.y + 7.4), 1.0, UiKit.BRONZE, true, -1.0, true)
	pg.ground(r, UiKit.SURFACE.wood)
	return r

## A board hung from a beam by two ropes (the page's title sign): the ropes from `top` down to the board's shoulders.
static func hung_board(pg: Page, r: Rect2, top: float) -> void:
	for x in [r.position.x + 30.0, r.end.x - 30.0]:
		pg.draw_line(Vector2(x, top), Vector2(x, r.position.y + 4), UiKit.SURFACE.hemp.lerp(UiKit.BRONZE, 0.5), 3.0, true)
	board(pg, r)

## A bar on paper (the bestiary leaf's level and bloodline): a pale trough in a bronze line, the fill, and the stops
## (`stops`, fractions) as bronze ticks crowned with a small diamond.
static func paper_bar(pg: Page, r: Rect2, frac: float, fill: Color, stops: Array = []) -> void:
	pg.rounded(r.grow(2), 4.0, UiKit.BRONZE.lerp(UiKit.INK, 0.35))
	pg.rounded(r, 3.0, UiKit.SURFACE.scroll_edge.lerp(UiKit.PAPER, 0.4))
	if frac > 0.0: pg.rounded(Rect2(r.position, Vector2(maxf(6.0, r.size.x * clampf(frac, 0.0, 1.0)), r.size.y)), 3.0, fill)
	for s in stops:
		var x: float = r.position.x + r.size.x * float(s)
		pg.draw_rect(Rect2(x - 1, r.position.y - 4, 2, r.size.y + 8), UiKit.BRONZE.lerp(UiKit.INK, 0.35))
		var c := Vector2(x, r.position.y - 8)
		pg.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -6), c + Vector2(6, 0), c + Vector2(0, 6), c + Vector2(-6, 0)]), UiKit.BRONZE)
		pg.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -4.5), c + Vector2(4.5, 0), c + Vector2(0, 4.5), c + Vector2(-4.5, 0)]), UiKit.SURFACE.scroll.lerp(UiKit.PAPER, 0.5))

## A heap of Spirit Stones spilled on the floor (the Core Exchange's spout): up to fifteen stones from `at`, the bottom
## row five across, each the currency's own icon at 32 px on whole pixels; `falling` more hang in the air above it on the
## way down from `from`.
static func stones(pg: Page, at: Vector2, n: int, from := Vector2.ZERO, falling := 0) -> void:
	var icon := Page.currency_icon("spirit_stone")
	var k := 0
	for row in 5:
		for i in 5 - row:
			if k >= mini(n, 15): break
			var p := at + Vector2((i - (4 - row) * 0.5) * 22.0 + (HashNoise.scatter(3, k) - 0.5) * 6.0, -row * 13.0)
			pg.icon_at(Rect2(p.round() - Vector2(16, 16), Vector2(32, 32)), icon)
			k += 1
	for j in falling:
		var f := (j + 1.0) / (falling + 1.0)
		var p := from.lerp(at + Vector2(0, -70), f) + Vector2(0, -sin(PI * f) * 18.0)
		pg.icon_at(Rect2(p.round() - Vector2(16, 16), Vector2(32, 32)), icon)
