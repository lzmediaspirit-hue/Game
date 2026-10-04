class_name Figures
extends RefCounted
## Decision 45, phase 2 (S4, DUP-03): the one factory for the figure of a character that a page, a card, a chip or a
## view draws: the top-down figure (TopdownDoll over TopdownFigure), the game's only character since the side view's
## layered Avatar retired (S12a). The pages ask here to make, dress, place and draw it.

## An undressed figure: the page dresses it (dress) and plays it.
static func for_character() -> TopdownDoll:
	return TopdownDoll.new()

## A figure wearing `o`, its feet at its position, facing `facing_row`, `px` screen px an art px (a whole number).
static func for_outfit(o: Dictionary, px: int, facing_row := TopdownDoll.PORTRAIT_ROW) -> TopdownDoll:
	var d := TopdownDoll.wearing(o, facing_row)
	d.scale = Vector2.ONE * px
	return d

## A friend's head and shoulders for a chip, wearing `o` (a Dictionary, else the defaults; its unset pieces a
## villager's), cut to `clip`.
static func chip(o, clip: Rect2) -> TopdownDoll:
	var d := TopdownDoll.wearing(TopdownFigure.DialoguePage.full_outfit(o if o is Dictionary else {}))
	d.clip = clip
	return d

## Dress a figure in `o`.
static func dress(fig: TopdownDoll, o: Dictionary) -> void:
	fig.outfit = o

## Draw `fig` on `ci` among the page's own drawing, its feet at `at`, `px` screen px an art px. Nothing when there is no
## figure.
static func draw_on(fig, ci: CanvasItem, at: Vector2, px: float) -> void:
	if is_instance_valid(fig): fig.draw_on(ci, at, px)
