class_name WayKit
extends RefCounted
## P5 · The way family's shared pieces (docs/page_identity.md §2, "The way": stone, sky and starlight, `sky_top` /
## `sky_bottom`, `SURFACE.stone`, `GOLD` light). Cultivation climbs its stair under the night, Breakthrough stands its
## stone gate against the sky, Revival burns its lamp in a stone niche and Fates fans its sticks under the stars; each
## draws its own layout from these (Techniques, the family's first, keeps its own rail and panels). Every piece draws on
## the page it is given, from tokens, and names the ground its words sit on (Page.ground), so the ui_suite measures them.

const BagPage = preload("res://scripts/ui/pages/inventory_page.gd")

## The night over `r`, sky_top deepening to sky_bottom, with `stars` scattered steadily (the Bag's shared stars, kept
## out of `clear`). Words on it are measured on sky_top, its lightest behind them.
static func night(pg: Page, r: Rect2, n := 90, clear: Array = []) -> void:
	pg.vshade(r, UiKit.SURFACE.sky_top, UiKit.SURFACE.sky_bottom)
	stars(pg, r.grow(-4), n, clear)
	pg.ground(r, UiKit.SURFACE.sky_top)

## `n` stars scattered steadily over `area` (the same every time), the bright ones kept out of `clear`.
static func stars(pg: Page, area: Rect2, n: int, clear: Array = []) -> void:
	BagPage.draw_stars(pg, BagPage.scatter_stars(n, area, clear))

## Coursed stone over `r` (a pillar, a beam, a niche's wall): blocks `course` px high, each a little lighter or darker
## than `face`, the joints in ink and every other course set half a block over. No words sit on it.
static func stone(pg: Page, r: Rect2, face: Color, course := 28.0, block := 64.0) -> void:
	pg.draw_rect(r, face.lerp(UiKit.INK, 0.5))
	var row := 0
	var y := r.position.y
	while y < r.end.y - 0.5:
		var h := minf(course, r.end.y - y)
		var x := r.position.x - (block * 0.5 if row % 2 == 1 else 0.0)
		var i := 0
		while x < r.end.x - 0.5:
			var b := Rect2(maxf(x, r.position.x) + 1.0, y + 1.0, minf(x + block, r.end.x) - maxf(x, r.position.x) - 2.0, h - 2.0)
			if b.size.x > 1.0:
				var tone := HashNoise.scatter(row * 31 + i, 5) - 0.5
				var col := face.lerp(UiKit.PAPER if tone > 0.0 else UiKit.INK, absf(tone) * 0.16)
				pg.draw_rect(b, col)
				pg.draw_rect(Rect2(b.position, Vector2(b.size.x, 1.0)), Color(UiKit.PAPER, 0.08))
			x += block
			i += 1
		y += course
		row += 1

## A cut-stone tablet (HD `stone_tablet`): dark while it waits, gold-leafed when `lit`. Its words are measured on it.
static func tablet(pg: Page, r: Rect2, lit: bool) -> void:
	pg.face(r, "stone_tablet", "selected" if lit else "normal")

## A red cord from `a` to `b` with its ink edge, and a knot where it ties on at `b`.
static func cord(pg: Page, a: Vector2, b: Vector2) -> void:
	pg.draw_line(a, b, UiKit.INK, 4.0, true)
	pg.draw_line(a, b, UiKit.RED, 2.0, true)
	pg.draw_circle(b, 3.5, UiKit.INK, true, -1.0, true)
	pg.draw_circle(b, 2.5, UiKit.RED, true, -1.0, true)

## A flame standing on `at` (its foot), `h` tall: a teardrop with an ember body, a flame-gold heart and an ink edge, so
## it reads on any ground. `sway` leans its tip (-1..1).
static func flame(pg: Page, at: Vector2, h: float, sway := 0.0) -> void:
	var w := h * 0.3
	for layer in [[1.0, 2.0, UiKit.INK], [1.0, 0.0, UiKit.SURFACE.ember], [0.55, 0.0, UiKit.SURFACE.flame]]:
		var k: float = layer[0]
		var e: float = layer[1]
		var r := w * k + e
		var c := at + Vector2(0, -w)
		var pts := PackedVector2Array()
		for j in 13:   # the round foot, from the right through the bottom to the left
			var a := PI * float(j) / 12.0
			pts.append(c + Vector2(cos(a), sin(a)) * r)
		pts.append(c + Vector2(sway * w * 0.8, -(h - w) * (0.55 + 0.45 * k) - e))
		pg.draw_colored_polygon(pts, layer[2])
