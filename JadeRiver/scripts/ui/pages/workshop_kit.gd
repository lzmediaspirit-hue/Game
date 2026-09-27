class_name WorkshopKit
extends RefCounted
## P5 · The Workshop family's shared pieces (docs/page_identity.md §2, "The workshop": worked timber and tools on `wood`,
## `wood_dark`, `ember` and `SURFACE.soil`): the Crafts, Workshop and Garden pages draw their own layouts from these.
## Every piece draws on the page it is given, from tokens, and names the ground its words sit on (Page.ground).

## The page's back wall: dark timber planks filling the window, with an ink edge (every page of the family stands on it).
static func wall(pg: Page, r: Rect2) -> void:
	pg.rounded(r.grow(2), 8.0, UiKit.INK)
	PostKit.planks(pg, r, 72.0, true, UiKit.SURFACE.wood_dark)
	pg.ground(r, UiKit.SURFACE.wood_dark)

## A worked board laid on the wall (the Crafts' controls, the Workshop's bench, the Garden's supply shelf): dark timber
## with its grain across and a bronze edge. Words on it read on `wood_dark`.
static func board(pg: Page, r: Rect2) -> void:
	pg.rounded(r.grow(2), 6.0, UiKit.INK)
	pg.rounded(r, 5.0, UiKit.SURFACE.wood_dark)
	var y := r.position.y + 9.0
	while y < r.end.y - 6.0:
		pg.draw_line(Vector2(r.position.x + 8, y), Vector2(r.end.x - 8, y), Color(UiKit.INK, 0.14), 1.0)
		y += 13.0
	pg.draw_rect(r.grow(-3), Color(UiKit.BRONZE, 0.55), false, 2.0)
	pg.ground(r, UiKit.SURFACE.wood_dark)

## A brick face in `r` (the hearth, the terraces' walls): courses of `SURFACE.stone` with ink mortar, each course offset
## by half a brick. Words on it read on `stone`.
static func bricks(pg: Page, r: Rect2, course := 24.0, brick := 56.0) -> void:
	pg.draw_rect(r, UiKit.SURFACE.stone)
	var row := 0
	var y := r.position.y
	while y < r.end.y:
		var h := minf(course, r.end.y - y)
		pg.draw_rect(Rect2(r.position.x, y, r.size.x, 2), Color(UiKit.INK, 0.45))
		pg.draw_rect(Rect2(r.position.x, y + 2, r.size.x, 2), Color(UiKit.PAPER, 0.06))
		var x := r.position.x + (brick * 0.5 if row % 2 else 0.0)
		while x < r.end.x:
			if x > r.position.x: pg.draw_rect(Rect2(x, y, 2, h), Color(UiKit.INK, 0.4))
			x += brick
		y += course
		row += 1
	pg.ground(r, UiKit.SURFACE.stone)

## Flames rising from `base` across `w` px: tongues of the fire's colour over a lit core, taller with `heat` (0-1); they
## flicker with `t` unless Reduce motion or the battery saver holds them (their height is the heat, which stays).
static func fire(pg: Page, base: Vector2, w: float, heat: float, col: Color, t: float) -> void:
	var still: bool = UiKit.reduce_motion() or bool(Game.account.settings.get("battery_saver", false))
	pg.glow(Rect2(base - Vector2(w * 0.9, w * 0.5), Vector2(w * 1.8, w * 0.9)), Color(col, 0.35 + 0.3 * heat))
	var n := 5
	for layer in 2:
		var tint: Color = col if layer == 0 else col.lerp(UiKit.PALE_GOLD, 0.7)
		var k := 1.0 if layer == 0 else 0.55
		for i in n:
			var f := (i + 0.5) / n
			var cx := base.x + (f - 0.5) * w * 0.8 * k
			var sway := 0.0 if still else sin(t * 7.0 + i * 1.9) * 3.0
			var hgt := (18.0 + 40.0 * heat) * k * (1.0 - absf(f - 0.5) * 0.9) * (1.0 if still else 0.85 + 0.15 * sin(t * 9.0 + i * 2.3))
			var half := w / n * 0.62 * k
			pg.draw_colored_polygon(PackedVector2Array([Vector2(cx - half, base.y), Vector2(cx - half * 0.4, base.y - hgt * 0.55),
				Vector2(cx + sway, base.y - hgt), Vector2(cx + half * 0.4, base.y - hgt * 0.55), Vector2(cx + half, base.y)]), Color(tint, 0.9))

## A bed of soil in `r` (a garden plot): `SURFACE.soil`, darker and wetter the richer the field (`wet`, 0-1), its rows
## ridged across it and a stone kerb round it. Words on it read on `soil`.
static func soil(pg: Page, r: Rect2, wet: float) -> void:
	pg.rounded(r.grow(3), 5.0, UiKit.SURFACE.stone)
	var col: Color = UiKit.SURFACE.soil.lerp(UiKit.SURFACE.wood, 0.18 * (1.0 - clampf(wet, 0.0, 1.0)))
	pg.rounded(r, 4.0, col)
	var y := r.position.y + 12.0
	while y < r.end.y - 6.0:
		pg.draw_line(Vector2(r.position.x + 8, y - 3), Vector2(r.end.x - 8, y - 3), Color(UiKit.SURFACE.wood, 0.45), 3.0)
		pg.draw_line(Vector2(r.position.x + 8, y), Vector2(r.end.x - 8, y), Color(UiKit.INK, 0.35), 2.0)
		y += 16.0
	pg.ground(r, col)

## A wooden peg with its cord knot at `c` (a tag's peg, a tool's hook).
static func peg(pg: Page, c: Vector2) -> void:
	pg.draw_circle(c + Vector2(0, 1.5), 5.5, Color(UiKit.INK, 0.6), true, -1.0, true)
	pg.draw_circle(c, 5.0, UiKit.SURFACE.peg, true, -1.0, true)
	pg.draw_circle(c - Vector2(1.5, 1.5), 1.6, Color(UiKit.PAPER, 0.5), true, -1.0, true)

## A tab as a wooden tag hung from a peg on the beam: the chosen one warm and its label inked, a locked one dim.
static func tag_tab(pg: Page, r: Rect2, label: String, state: String) -> void:
	pg.draw_line(Vector2(r.get_center().x, r.position.y - 10), Vector2(r.get_center().x, r.position.y + 4), UiKit.SURFACE.hemp, 2.0, true)
	peg(pg, Vector2(r.get_center().x, r.position.y - 10))
	pg.face(r, "timber_tag", "selected" if state == "selected" else "normal")
	if state == "selected": pg.inked(r.position + Vector2(0, 31), label, 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, false)
	else: pg.text(r.position + Vector2(0, 31), label, 20, UiKit.HOLLOW if state == "disabled" else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## The beam the tags hang from, across `x0`..`x1` at `y`.
static func beam(pg: Page, x0: float, x1: float, y: float) -> void:
	pg.rounded(Rect2(x0, y - 7, x1 - x0, 14), 4.0, UiKit.INK)
	pg.rounded(Rect2(x0 + 1, y - 6, x1 - x0 - 2, 12), 4.0, UiKit.SURFACE.wood)
	pg.draw_line(Vector2(x0 + 4, y - 4), Vector2(x1 - 4, y - 4), Color(UiKit.PALE_GOLD, 0.12), 2.0)
