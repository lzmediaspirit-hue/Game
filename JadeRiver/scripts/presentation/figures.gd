class_name Figures
extends RefCounted
## Decision 45, phase 2 (S4, DUP-03): the one factory for the figure of a character that a page, a card, a chip or a
## view draws. A character who plays the top-down game is drawn as the top-down figure (TopdownDoll over TopdownFigure);
## a classic side-view character (decision 41's fallback setting) as the side view's layered Avatar. The pages asked
## `TopdownDoll.new() if TopdownDoll.shown(ch) else Avatar.new()` and forked again to dress, place and draw it; they
## ask here now, and either figure takes the calls a page makes: outfit, play, facing, draw_on.
##
## Retiring the side view: every Avatar is made in the SIDE VIEW section at the end of this file. Delete that section,
## let `top_down` answer true and `for_view` make the doll, and drop the `side_*` arguments; the side view's own world
## (player.gd, NpcView, EnemyView) goes with its files.

## True when `ch` (the active character when null) plays the top-down game, so its figure is the top-down one.
static func top_down(ch = null) -> bool:
	if ch == null: ch = Game.active()
	return ch != null and str(ch.view) == "topdown"

## An undressed figure of `ch` (the active character when null): the page dresses it (dress) and plays it.
static func for_character(ch = null) -> Node2D:
	return for_view(top_down(ch))

## An undressed figure for a view: the top-down doll when `top`, else the side view's avatar.
static func for_view(top: bool) -> Node2D:
	return TopdownDoll.new() if top else side_avatar()

## A figure wearing `o`, its feet at its position, drawn as `ch` (the active character when null) is: the top-down doll
## facing `facing_row` at `top_px` screen px an art px (a whole number), else the side view's avatar at `side_k`.
static func for_outfit(o: Dictionary, side_k: float, top_px: int, ch = null, facing_row := TopdownDoll.PORTRAIT_ROW) -> Node2D:
	if top_down(ch):
		var d := TopdownDoll.wearing(o, facing_row)
		d.scale = Vector2.ONE * top_px
		return d
	var a := side_avatar(o)
	a.scale = Vector2.ONE * side_k
	return a

## A friend's head and shoulders for a chip, wearing `o` (a Dictionary, else the defaults): the top-down doll (its unset
## pieces a villager's) cut to `top_clip`, or the side view's avatar fitted into `side_box`.
static func chip(o, top_clip: Rect2, side_box: Vector2, ch = null) -> Node2D:
	if top_down(ch):
		var d := TopdownDoll.wearing(TopdownFigure.DialoguePage.full_outfit(o if o is Dictionary else {}))
		d.clip = top_clip
		return d
	var a := side_avatar((o as Dictionary).duplicate() if o is Dictionary else null)
	a.thumbnail_size = side_box
	return a

## Dress a figure of either kind in `o`.
static func dress(fig: Node2D, o: Dictionary) -> void:
	fig.set("outfit", o)
	if not fig is TopdownDoll: fig.set("last_key", "")

## `top` for the top-down doll, `side` for the side view's avatar: what a page offsets or scales by the figure's kind.
static func pick(fig, top, side):
	return top if fig is TopdownDoll else side

## Draw `fig` on `ci` among the page's own drawing: the top-down doll with its feet at `top_at`, `top_px` screen px an art
## px; the side view's avatar at `side_at`, `side_k`. Nothing when there is no figure.
static func draw_on(fig, ci: CanvasItem, top_at: Vector2, top_px: float, side_at: Vector2, side_k: float) -> void:
	if not is_instance_valid(fig): return
	if fig is TopdownDoll: fig.draw_on(ci, top_at, top_px)
	else: fig.draw_on(ci, side_at, side_k)

# ------------------------------------------------------------------ SIDE VIEW (retire with decision 41's fallback)
const _AVATAR = preload("res://scripts/avatar.gd")

## The side view's layered avatar, wearing `o` when one is given (else its own default, set when it enters the tree).
## The side view's world makes its bodies with it too (player.gd, NpcView, EnemyView).
static func side_avatar(o = null) -> Node2D:
	var a = _AVATAR.new()
	if o != null: a.outfit = o
	return a
