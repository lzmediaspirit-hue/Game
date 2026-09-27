class_name PostKit
extends RefCounted
## P5 · The Post family's shared pieces (docs/page_identity.md §2, "The post": bamboo, hemp and basketry): the Roll-Call,
## Works, Welcome Back and Pouches pages draw their own layouts from these. Every piece draws on the page it is given,
## from tokens, and names the ground its words sit on (Page.ground), so the ui_suite measures them.

## A rect with an arched top rising `rise` px (a name tablet, a tablet's window, a cage): its outline as a polygon.
static func arch(r: Rect2, rise: float, steps := 18) -> PackedVector2Array:
	var pts := PackedVector2Array([Vector2(r.position.x, r.end.y)])
	for i in steps + 1:
		var a := PI + PI * float(i) / float(steps)
		pts.append(Vector2(r.get_center().x + cos(a) * r.size.x * 0.5, r.position.y + rise + sin(a) * rise))
	pts.append(r.end)
	return pts

## Basketry: woven strips across `r` with gaps, so what lies behind shows through (a basket, the winnowing tray).
static func weave(pg: Page, r: Rect2, col: Color, pitch := 16.0) -> void:
	var y := r.position.y
	while y < r.end.y:
		pg.draw_rect(Rect2(r.position.x, y, r.size.x, 4), col)
		pg.draw_rect(Rect2(r.position.x, y + 4, r.size.x, 1), Color(UiKit.INK, 0.35))
		y += pitch
	var x := r.position.x + 6.0
	while x < r.end.x:
		pg.draw_rect(Rect2(x, r.position.y, 4, r.size.y), col.lerp(UiKit.INK, 0.15))
		x += pitch + 4.0

## A paper tag tied on with a string: the big count and the small word after it ("400 full", "0 /40"). Returns its rect.
static func tag(pg: Page, at: Vector2, big: String, small: String, full := false) -> Rect2:
	var w := UiKit.text_width(big, 26) + UiKit.text_width(small, 14) + 34.0
	var r := Rect2(at, Vector2(w, 40))
	var paper: Color = UiKit.SURFACE.talisman.lerp(UiKit.RED, 0.12) if full else UiKit.SURFACE.talisman
	pg.rounded(r.grow(2), 6.0, UiKit.BLOOD if full else UiKit.SURFACE.talisman_edge)
	pg.rounded(r, 5.0, paper)
	pg.ground(r, paper)
	pg.draw_circle(r.position + Vector2(10, 20), 3.0, UiKit.SURFACE.peg_dark)
	pg.text(r.position + Vector2(18, 30), big, 26, UiKit.BLOOD if full else UiKit.PAPER_INK)
	pg.text(r.position + Vector2(22 + UiKit.text_width(big, 26), 30), small, 14, UiKit.BLOOD if full else UiKit.PAPER_INK)
	return r

## A hemp label or slip with a fine bronze edge: words on it are PAPER_INK.
static func hemp(pg: Page, r: Rect2) -> void:
	pg.rounded(r.grow(1), 4.0, UiKit.BRONZE)
	pg.rounded(r, 3.0, UiKit.SURFACE.hemp)
	pg.draw_rect(Rect2(r.position.x + 2, r.end.y - 4, r.size.x - 4, 2), Color(UiKit.BRONZE, 0.3))
	pg.ground(r, UiKit.SURFACE.hemp)

## A light diagonal lattice screen over `r` (a locked compartment of the curio cabinet).
static func lattice(pg: Page, r: Rect2, col: Color, pitch := 44.0) -> void:
	pg.draw_rect(r, Color(UiKit.INK, 0.25))
	var span := r.size.x + r.size.y
	var k := 0.0
	while k < span:
		for dir in [1.0, -1.0]:
			var a := Vector2(r.position.x + k, r.position.y) if dir > 0.0 else Vector2(r.end.x - k, r.position.y)
			var b := a + Vector2(-r.size.y * dir, r.size.y)
			# clip the diagonal to the rect
			var t0 := 0.0
			var t1 := 1.0
			var dx := b.x - a.x
			if dx != 0.0:
				var ta := (r.position.x - a.x) / dx
				var tb := (r.end.x - a.x) / dx
				t0 = maxf(t0, minf(ta, tb))
				t1 = minf(t1, maxf(ta, tb))
			if t1 > t0: pg.draw_line(a.lerp(b, t0), a.lerp(b, t1), col, 3.0, true)
		k += pitch
	pg.draw_rect(r, col.lerp(UiKit.INK, 0.3), false, 3.0)

## Planks of timber (dark by default) across `r` with their seams and grain (the Roll-Call's board, the Welcome table).
static func planks(pg: Page, r: Rect2, pitch := 96.0, vertical := true, col: Color = UiKit.SURFACE.wood_dark) -> void:
	pg.rounded(r, 10.0, col)
	var n := int((r.size.x if vertical else r.size.y) / pitch)
	for i in range(1, n + 1):
		var p := (r.position.x if vertical else r.position.y) + i * pitch
		if vertical: pg.draw_rect(Rect2(p, r.position.y + 6, 2, r.size.y - 12), Color(UiKit.SURFACE.peg_dark, 0.6))
		else: pg.draw_rect(Rect2(r.position.x + 6, p, r.size.x - 12, 2), Color(UiKit.SURFACE.peg_dark, 0.6))
	for i in int((r.size.x if vertical else r.size.y) / 11.0):
		var p := (r.position.x if vertical else r.position.y) + 5.0 + i * 11.0
		var c := Color(UiKit.INK, 0.10 if i % 3 else 0.18)
		if vertical: pg.draw_line(Vector2(p, r.position.y + 10), Vector2(p, r.end.y - 10), c, 1.0)
		else: pg.draw_line(Vector2(r.position.x + 10, p), Vector2(r.end.x - 10, p), c, 1.0)
	pg.draw_rect(r.grow(-2), UiKit.SURFACE.peg_dark, false, 4.0)
	pg.draw_rect(r.grow(-6), Color(UiKit.GOLD, 0.35), false, 1.0)

## A dashed outline through `pts` (a place where something will stand: an empty peg, a basket not yet set down).
static func dashed(pg: Page, pts: PackedVector2Array, col: Color, dash := 8.0) -> void:
	for j in pts.size() - 1:
		var a: Vector2 = pts[j]
		var b: Vector2 = pts[j + 1]
		var n := a.distance_to(b)
		var d := 0.0
		while d < n:
			pg.draw_line(a.lerp(b, d / n), a.lerp(b, minf(1.0, (d + dash) / n)), col, 2.0, true)
			d += dash * 2.0

## A small vermilion seal with a tick: something waits here (a full pouch, points to spend).
static func ready_seal(pg: Page, c: Vector2) -> void:
	pg.draw_circle(c, 13.0, UiKit.INK, true, -1.0, true)
	pg.draw_circle(c, 11.0, UiKit.SURFACE.cinnabar, true, -1.0, true)
	pg.draw_polyline(PackedVector2Array([c + Vector2(-5, 0), c + Vector2(-1, 4), c + Vector2(6, -5)]), UiKit.PALE_GOLD, 2.5, true)
