class_name TopdownDoll
extends Node2D
## Decision 42 ("no old side-view character is left anywhere in the top-down game"): the top-down character as a page
## shows it, in place of the side view's layered Avatar: the Techniques page's caster and pictures, the Character page's
## and the Bag's figure, a speaker in the dialogue strip, a friend in a moon gate, a merchant behind the counter.
## TopdownFigure draws it (the layer sets under art/topdown/character/, the full set in every action): one action in one
## of the eight facings on the doll's own clock, its feet at the node's origin. Pixels stay nearest-neighbour at a whole
## scale: the node's own (a page keeps it whole), or the `px` a page passes to draw_on when it draws the doll among its
## own layers. Its sheets load on threads, so no page waits on them (the doll appears the frame they are in), and it
## redraws only when its drawn frame changes (an idle's four frames a second), never every frame for nothing.
##
## `shown()` says which figure a page draws: this one whenever the character shown plays the top-down game (the active
## one, or the one a card is for); the side view's Avatar only for a classic side-view character (decision 41's
## fallback setting).

## A portrait's facing: three-quarters toward the camera, turned to the right.
const PORTRAIT_ROW := "se"

var figure: TopdownFigure
var action := "idle"
var row := PORTRAIT_ROW
var t := 0.0                  ## seconds into the action
var hold := -1                ## a frame held still, else -1: the action's own clock
var externally_timed := false ## its clock is stepped by its owner (step), not by _process
var shadow := false           ## a soft blob under its feet
var tint := Color.WHITE
var clip := Rect2()           ## what of it is drawn, in its own space from its feet (none: all of it)
var _drawn := -1              ## the frame its own canvas holds (-1: none drawn yet)
var _in := false              ## every sheet it wears is in memory

## What it wears (an outfit as InventoryAuthority.outfit_for or DialoguePage.full_outfit gives it).
var outfit: Dictionary:
	get: return figure.outfit
	set(o):
		if o == figure.outfit: return
		figure.set_outfit(o)
		_in = false
		_drawn = -1
		queue_redraw()

## The side view's facing (1 right, -1 left), as a row three-quarters toward the camera.
var facing: int:
	get: return -1 if row in ["sw", "w", "nw"] else 1
	set(f):
		row = "se" if f >= 0 else "sw"
		queue_redraw()

## True when the character shown plays the top-down game: `ch`, or the active character.
static func shown(ch = null) -> bool:
	if ch == null: ch = Game.active()
	return ch != null and str(ch.view) == "topdown"

## A doll wearing `o`, facing `row`, its sheets loading on threads.
static func wearing(o: Dictionary, facing_row := PORTRAIT_ROW) -> TopdownDoll:
	var d := TopdownDoll.new()
	d.figure = TopdownFigure.wearing(o, true)
	d.row = facing_row
	return d

## The figure a page shows wearing `o`, its feet at its position: this doll at `top_k` (a whole number) when `ch` (the
## active character by default) plays the top-down game, else the side view's Avatar at `side_k`. Either takes the
## Avatar's calls a page makes: outfit, play, facing, draw_on.
static func figure_for(o: Dictionary, side_k: float, top_k: int, ch = null, facing_row := PORTRAIT_ROW) -> Node2D:
	if shown(ch):
		var d := wearing(o, facing_row)
		d.scale = Vector2.ONE * top_k
		return d
	var a = load("res://scripts/avatar.gd").new()
	a.outfit = o
	a.scale = Vector2.ONE * side_k
	return a

## Dress a page's figure (this doll or the side view's Avatar) in `o`.
static func dress(fig: Node2D, o: Dictionary) -> void:
	fig.set("outfit", o)
	if not fig is TopdownDoll: fig.set("last_key", "")

func _init() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if figure == null: figure = TopdownFigure.wearing({}, true)

## Play `a` from its start (a side-view name plays as its top-down action, TopdownFigure.resolve).
func play(a: String) -> void:
	var next := TopdownFigure.resolve(a)
	if next == action: return
	action = next
	t = 0.0
	queue_redraw()

## The frame it shows now.
func frame() -> int:
	return hold if hold >= 0 else TopdownFigure.frame_at(action, t)

## Its clock moved on by `dt` (an owner that times it: the Techniques preview).
func step(dt: float) -> void:
	t += dt
	_refresh()

func _process(delta: float) -> void:
	if not externally_timed: t += delta
	_refresh()

## A redraw only when what it shows changes: its sheets came in, or its frame moved on.
func _refresh() -> void:
	if not _in:
		_in = figure.loaded()
		if not _in: return
	if frame() != _drawn: queue_redraw()

func _draw() -> void:
	_drawn = frame() if _in else -1
	if shadow:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.32))
		draw_circle(Vector2.ZERO, 8.0, Color(0, 0, 0, 0.3))
		draw_circle(Vector2.ZERO, 5.5, Color(0, 0, 0, 0.2))
		draw_set_transform(Vector2.ZERO)
	figure.draw(self, Vector2.ZERO, action, row, frame(), tint, 1.0, clip)

## Draw it on `ci` (a page that lays it among its own drawing) with its feet at `at`, `px` screen px an art px (a whole
## number), every layer multiplied by `mod`, cropped to `clip` (ci's space) when one is given.
func draw_on(ci: CanvasItem, at: Vector2, px := 1.0, mod := Color.WHITE, clip := Rect2()) -> void:
	if not _in: _in = figure.loaded()
	figure.draw(ci, at.round(), action, row, frame(), tint * mod, px, clip)

## What it covers in art px from its feet, in the frame it shows.
func bounds() -> Rect2:
	return figure.bounds(action, row, frame())
