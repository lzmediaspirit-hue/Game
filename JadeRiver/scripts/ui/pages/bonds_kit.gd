class_name BondsKit
extends RefCounted
## P5 · The Bonds family's shared pieces (docs/page_identity.md §2, "Bonds": whitewash and red thread, `SURFACE.plaster`,
## `RED` thread, `HEART`): the Companions' garden wall, the Relations' steelyard hung on the same wall, and the Gift's
## tags draw from these. Every piece draws on the page it is given, from tokens, and names the ground its words sit on.

## Ink on the whitewash, each a token or a mix of two, measured on the plaster by the ui_suite.
static var INK := UiKit.PAPER_INK
static var SOFT_INK := UiKit.PAPER_INK.lerp(UiKit.JADE_SHADOW, 0.5)
## The red thread of a bond, the black thread of a grudge, and the pink of a liked gift's tag.
static var THREAD := UiKit.RED.lerp(UiKit.BLOOD, 0.4)
static var GRUDGE := UiKit.INK
static var TAG := UiKit.HEART.lerp(UiKit.PAPER, 0.4)
## The coping's tiles.
static var TILE := UiKit.JADE_SHADOW
static var TILE_LIT := UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.35)

## A whitewashed garden wall over the window rect `r`: the plaster with the wash's faint streaks, a coping of
## JADE_SHADOW tiles `coping` px deep along the top casting its shadow down the wall (none at 0: the Relations hang a
## timber rafter there). Names the plaster as the ground.
static func wall(pg: Page, r: Rect2, coping := 60.0) -> void:
	pg.rounded(r.grow(2), 8.0, UiKit.INK)
	pg.rounded(r, 6.0, UiKit.SURFACE.plaster)
	var body := Rect2(r.position + Vector2(0, coping), r.size - Vector2(0, coping))
	pg.ground(body, UiKit.SURFACE.plaster)
	# The wash laid on in broad strokes: a few lighter and darker streaks, steady from the rect.
	var i := int(r.position.x) % 7
	var x := r.position.x + 30.0
	while x < r.end.x - 60.0:
		var w := 60.0 + float((i * 37) % 90)
		pg.hshade(Rect2(x, body.position.y, w * 0.5, body.size.y - 8.0), Color(UiKit.MIST, 0.0), Color(UiKit.MIST, 0.10))
		pg.hshade(Rect2(x + w * 0.5, body.position.y, w * 0.5, body.size.y - 8.0), Color(UiKit.MIST, 0.10), Color(UiKit.MIST, 0.0))
		x += w + 40.0 + float((i * 53) % 70)
		i += 1
	if coping <= 0.0: return
	# The coping: a dark ridge, the tile rolls and a row of round tile ends along its eave, its shadow on the wall.
	var cop := Rect2(r.position, Vector2(r.size.x, coping))
	pg.vshade(Rect2(cop.position.x, cop.end.y, cop.size.x, 22), Color(UiKit.INK, 0.28), Color(UiKit.INK, 0.0))
	pg.rounded(cop, 6.0, TILE.lerp(UiKit.INK, 0.3))
	pg.draw_rect(Rect2(cop.position.x, cop.position.y, cop.size.x, 8), TILE.lerp(UiKit.INK, 0.55))
	var tx := cop.position.x + 10.0
	while tx < cop.end.x - 4.0:
		pg.draw_rect(Rect2(tx, cop.position.y + 8, 12, coping - 22), TILE)
		pg.draw_rect(Rect2(tx + 2, cop.position.y + 8, 3, coping - 22), TILE_LIT)
		tx += 20.0
	var ex := cop.position.x + 16.0
	while ex < cop.end.x - 8.0:
		pg.draw_circle(Vector2(ex, cop.end.y - 8), 9.0, UiKit.INK, true, -1.0, true)
		pg.draw_circle(Vector2(ex, cop.end.y - 8), 7.5, TILE_LIT, true, -1.0, true)
		pg.draw_circle(Vector2(ex, cop.end.y - 8), 3.0, TILE, true, -1.0, true)
		ex += 20.0
	pg.ground(cop, TILE.lerp(UiKit.INK, 0.3))

## A thread from `a` to `b` sagging `sag` px at its middle (red for a bond, black for a grudge, hemp for a cord).
static func thread(pg: Page, a: Vector2, b: Vector2, col: Color, sag := 6.0, width := 2.5) -> void:
	var pts := PackedVector2Array()
	for i in 17:
		var k := float(i) / 16.0
		pts.append(a.lerp(b, k) + Vector2(0, sin(k * PI) * sag))
	pg.draw_polyline(pts, Color(UiKit.INK, 0.35), width + 1.5, true)
	pg.draw_polyline(pts, col, width, true)

## The thread's y at `k` (0 to 1) along a thread drawn from `a` to `b` with `sag`.
static func on_thread(a: Vector2, b: Vector2, sag: float, k: float) -> Vector2:
	return a.lerp(b, k) + Vector2(0, sin(k * PI) * sag)

## A knot on the red thread: a heart tied (a figure-eight of two loops with a bead), or a slack loop still to tie. `k`
## scales a knot being tied (0 to 1).
static func knot(pg: Page, c: Vector2, tied: bool, k := 1.0) -> void:
	if not tied:
		pg.draw_arc(c + Vector2(0, -3), 6.0, 0.0, TAU, 20, Color(THREAD, 0.55), 2.0, true)
		return
	for side in [-1.0, 1.0]:
		pg.draw_circle(c + Vector2(side * 5.0, -2.0) * k, 6.0 * k, UiKit.INK, true, -1.0, true)
	for side in [-1.0, 1.0]:
		pg.draw_circle(c + Vector2(side * 5.0, -2.0) * k, 4.6 * k, UiKit.HEART, true, -1.0, true)
	pg.draw_circle(c + Vector2(0, 2) * k, 4.0 * k, THREAD, true, -1.0, true)
	pg.draw_circle(c + Vector2(-6.0, -4.0) * k, 1.4 * k, Color(UiKit.PAPER, 0.7), true, -1.0, true)

## A paper lantern on its cord: lit (red paper glowing, `glow_k` of its halo) or dark, hung with its top at `top`.
static func lantern(pg: Page, top: Vector2, lit: bool, glow_k := 1.0) -> void:
	var body := Rect2(top + Vector2(-15, 8), Vector2(30, 34))
	if lit: pg.glow(body.grow(26 * glow_k), Color(UiKit.GOLD, 0.45 * glow_k * pg.halo_k()))
	pg.draw_line(top, top + Vector2(0, 8), UiKit.INK, 2.0, true)
	pg.rounded(Rect2(body.position.x + 6, body.position.y - 3, 18, 5), 2.0, UiKit.INK)
	pg.rounded(Rect2(body.position.x + 6, body.end.y - 2, 18, 5), 2.0, UiKit.INK)
	pg.rounded(body.grow(1.5), 12.0, UiKit.INK)
	pg.rounded(body, 11.0, UiKit.RED.lerp(UiKit.GOLD, 0.25 * glow_k) if lit else UiKit.SURFACE.stone.lerp(UiKit.RED, 0.25))
	for dx in [-7.0, 0.0, 7.0]:
		pg.draw_line(Vector2(body.get_center().x + dx, body.position.y + 2), Vector2(body.get_center().x + dx, body.end.y - 2), Color(UiKit.INK, 0.3), 1.0, true)
	pg.draw_line(Vector2(body.get_center().x, body.end.y + 3), Vector2(body.get_center().x, body.end.y + 12), THREAD if lit else Color(UiKit.INK, 0.5), 2.0, true)

## A tablet of dark timber hung on the wall by two cords from `hang_y` (the Relations' boards under the beam, hung on
## red or black thread): a bronze-lined board whose words are PAPER and MIST. Names the timber as the ground.
static func board(pg: Page, r: Rect2, cord: Color, hang_y := -1.0) -> void:
	if hang_y >= 0.0:
		for x in [r.position.x + 36.0, r.end.x - 36.0]:
			thread(pg, Vector2(x, hang_y), Vector2(x, r.position.y + 6), cord, 0.0, 2.5)
	pg.rounded(Rect2(r.position + Vector2(3, 5), r.size), 6.0, Color(UiKit.INK, 0.35))
	pg.rounded(r.grow(2), 7.0, UiKit.INK)
	pg.vshade(r, BOARD_LIT, UiKit.SURFACE.wood_dark)
	pg.draw_rect(r.grow(-4), Color(UiKit.BRONZE, 0.7), false, 1.5)
	for x in [r.position.x + 36.0, r.end.x - 36.0]:
		pg.draw_circle(Vector2(x, r.position.y + 10), 4.0, UiKit.GOLD, true, -1.0, true)
	pg.ground(r, BOARD_LIT)

## The board's timber where the light falls (its top): the ground its words are measured on.
static var BOARD_LIT := UiKit.SURFACE.wood_dark.lerp(UiKit.SURFACE.wood, 0.12)
