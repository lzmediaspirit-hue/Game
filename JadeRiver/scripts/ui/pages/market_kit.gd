class_name MarketKit
extends RefCounted
## P5 · The Market family's shared pieces (docs/page_identity.md §2, "The market": brass fittings and paper price tags on
## trade timber and black lacquer): the Shop, Storage, Exchange, County Hall and Auction pages draw their own layouts
## from these. "Your bag" beside the Shop's stall and the Storage's chest is a patch of the Bag's own heaven (decision 24),
## drawn from the Bag's shared sky pieces (inventory_page.gd). Every piece draws on the page it is given, from tokens, and
## names the ground its words sit on (Page.ground), so the ui_suite measures them.

const BagPage = preload("res://scripts/ui/pages/inventory_page.gd")
## The gourd's spaces as the Bag floats them: a 76 px slot and its gap across.
const PITCH := 80.0

## Timber boards over `r` (a stall's wall, a counter's front, a chest): the face with a dark seam every `pitch` px,
## running down the boards (`vertical`) or along them.
static func planks(pg: Page, r: Rect2, face: Color, pitch: float, vertical := true) -> void:
	pg.draw_rect(r, face)
	var seam: Color = face.lerp(UiKit.INK, 0.45)
	var at := (r.position.x if vertical else r.position.y) + pitch
	var stop := r.end.x if vertical else r.end.y
	while at < stop - 2.0:
		if vertical:
			pg.draw_rect(Rect2(at, r.position.y, 2, r.size.y), seam)
			pg.draw_rect(Rect2(at + 2, r.position.y, 1, r.size.y), Color(face.lerp(UiKit.PAPER, 0.15), 0.5))
		else:
			pg.draw_rect(Rect2(r.position.x, at, r.size.x, 2), seam)
			pg.draw_rect(Rect2(r.position.x, at + 2, r.size.x, 1), Color(face.lerp(UiKit.PAPER, 0.15), 0.5))
		at += pitch

## Brass fittings on the four corners of `r`: an angle of brass along each edge with two studs.
static func brass(pg: Page, r: Rect2, leg := 22.0) -> void:
	for c in [[r.position, 1.0, 1.0], [Vector2(r.end.x, r.position.y), -1.0, 1.0], [Vector2(r.position.x, r.end.y), 1.0, -1.0], [r.end, -1.0, -1.0]]:
		var p: Vector2 = c[0]
		var dx: float = c[1]
		var dy: float = c[2]
		var pts := PackedVector2Array([p, p + Vector2(dx * leg, 0), p + Vector2(dx * leg, dy * 6), p + Vector2(dx * 6, dy * 6), p + Vector2(dx * 6, dy * leg), p + Vector2(0, dy * leg)])
		pg.draw_colored_polygon(pts, UiKit.BRONZE)
		pts.append(pts[0])
		pg.draw_polyline(pts, UiKit.GOLD, 1.0, true)
		for s in [Vector2(dx * (leg - 6), dy * 3), Vector2(dx * 3, dy * (leg - 6))]:
			pg.draw_circle(p + s, 1.8, UiKit.PALE_GOLD, true, -1.0, true)

## A board of black lacquer framed by a brass hairline, with brass on its corners: words on it read on lacquer_black.
static func lacquer_board(pg: Page, r: Rect2, leg := 22.0) -> void:
	pg.rounded(r.grow(2), 5.0, UiKit.INK)
	pg.vshade(r, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.08), UiKit.SURFACE.lacquer_black)
	pg.draw_rect(r.grow(-4), Color(UiKit.GOLD, 0.55), false, 1.0)
	brass(pg, r, leg)
	pg.ground(r, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.08))

## A paper price tag tied on under a ware, centred on `cx` from `y`: the currency's coin and the price in ink. Returns it.
static func price_tag(pg: Page, cx: float, y: float, currency: String, amount: int) -> Rect2:
	var s := UiKit.fmt(amount)
	var w := ceilf(UiKit.text_width(s, 18)) + 50.0
	var r := Rect2(roundf(cx - w * 0.5), y, w, 36)
	pg.draw_line(Vector2(cx, y - 6), Vector2(cx, y + 2), UiKit.SURFACE.talisman_edge, 2.0)
	pg.rounded(r.grow(2), 5.0, UiKit.SURFACE.talisman_edge)
	pg.rounded(r, 4.0, UiKit.SURFACE.talisman)
	pg.ground(r, UiKit.SURFACE.talisman)
	pg.icon_at(Rect2(r.position + Vector2(4, 2), Vector2(32, 32)), Page.currency_icon(currency))
	pg.text(r.position + Vector2(38, 25), s, 18, UiKit.PAPER_INK)
	return r

## "Your bag" beside another page: a patch of the gourd's heaven over `r` (the night, its stars, the light from the gourd's
## mouth when `mouth_x` is given, and the sea of cloud along the foot), as the Bag page draws it (decision 24).
static func heaven(pg: Page, r: Rect2, stars: Array, mouth_x := -1.0, spread := 1.0) -> void:
	BagPage.night(pg, r)
	pg.glow(Rect2(r.position + Vector2(-r.size.x * 0.2, r.size.y * 0.2), Vector2(r.size.x * 1.4, r.size.y * 0.6)), Color(UiKit.QI, 0.07))
	BagPage.draw_stars(pg, stars)
	if mouth_x >= 0.0: BagPage.mouth_light(pg, mouth_x, r.size.y * 0.8, spread)
	BagPage.cloud_sea(pg, r, r.end.y - 100.0)
	pg.ground(r, UiKit.SURFACE.sky)
	pg.ground(Rect2(r.position.x, r.end.y - 64, r.size.x, 64), UiKit.SURFACE.sea)

## The gourd's spaces (or any things) floating in the heaven, `cols` across in rows `pitch` apart from `view`'s top-left,
## scrolling as `area`: `entry(i)` gives the thing in space i (a bag entry) or null for an empty space. A thing is a slot
## with its grade rim and a tap `action`; `chosen` is lit; `under(i, rect)` draws what sits under a thing (a price).
static func sky_grid(pg: Page, area: String, view: Rect2, cols: int, pitch: float, n: int, entry: Callable, action: String, chosen: int,
		under := Callable()) -> void:
	pg.list(area, view, ceili(n / float(cols)), pitch, func(row: int, rr: Rect2):
		for col in cols:
			var i := row * cols + col
			if i >= n: return
			var r := Rect2(rr.position + Vector2(col * PITCH, 0), Vector2(Page.SLOT, Page.SLOT))
			var s = entry.call(i)
			if s == null:
				BagPage.empty_space(pg, r)
				continue
			BagPage.float_shadow(pg, r)
			pg.slot_box(r, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), action, i, chosen == i)
			if under.is_valid(): under.call(i, r)
	)

## A thing on its way (a bought ware to the counter, a stored thing across to the chest, coins through the slot): its icon
## from `from` to `to` over `dur` s from `t0`, lifted along an arc `lift` px high. Decoration: none under Reduce motion.
static func flight(pg: Page, f: Dictionary) -> void:
	if f.is_empty() or UiKit.reduce_motion(): return
	var k := (pg.t - float(f.t0)) / float(f.dur)
	if k < 0.0 or k >= 1.0: return
	var e := 1.0 - pow(1.0 - k, 2.0)
	var at: Vector2 = (f.from as Vector2).lerp(f.to, e) - Vector2(0, sin(PI * e) * float(f.get("lift", 0.0)))
	pg.icon_at(Rect2(at.round() - Vector2(32, 32), Vector2(64, 64)), str(f.item))

static func fly(pg: Page, item: String, from: Vector2, to: Vector2, dur: float, lift := 0.0) -> Dictionary:
	return {"item": item, "from": from, "to": to, "t0": pg.t, "dur": dur, "lift": lift}
