class_name TopdownGate
extends Node2D
## Decision 41, the end of the prototype: the closed gate at a way from a room on the height grid into a room with no
## top-down layout yet (WorldAuthority.prototype_gate). A road barrier of the valley stands across the way: timber
## posts with red-lacquered caps, two rails and a cross-brace, a red cord hung with paper talismans and a small notice
## board. The way's plate (PortalView) and a touch say "The road beyond is still being drawn."
## Drawn in the room's pixel viewport (one art px per px, the palette of tools/art/topdown/palette.py, the sun from the
## north-west), sorted with the room. A way north or south (a doorway, an arch in a wall) gets one barrier across it; a
## way east or west (an edge) one down the screen, in pieces a post apart, each sorted at its own post's foot so a body
## beside it is before or behind the right part.

const WOOD := [Color("46291f"), Color("683f28"), Color("8b5b34"), Color("ad7b46"), Color("cb9c63")]
const DARK := Color("1e1219")
const LINE := Color("0e1a1e")
const RED := [Color("661a2e"), Color("922636"), Color("bd3b3c"), Color("d95b49")]
const PAPER := [Color("b8b0ae"), Color("d3cbbd"), Color("e7e0cf"), Color("f6f1e3")]
const INK := Color("241f2f")
const SHADOW := Color(0.141, 0.122, 0.31, 0.41)
const POST_H := 20          ## a post's height in art px (a body stands about 30)
const RAILS := [14, 7]      ## the rails' heights over the floor

var def: Dictionary = {}
var across := true          ## the barrier runs across the screen (a way north or south), else down it
var half := 16              ## half its length along the way, art px
var seg := -1               ## a piece of a barrier down the screen: the post it ends at (0 the north end), -1 whole
var rects: Array = []       ## what it covers on screen, for the silhouette test (never hides the body: left empty)
var feet := Vector2.ZERO    ## the way's point on screen, art px

## The pieces of the gate at a way: one across it, or one a post apart down the screen.
static func make(room: TopdownRoom, p: Dictionary) -> Array:
	var d: Array = p.get("dir", [0, -1])
	var a: Array = p.get("at", [0, 0])
	var reach: Array = p.get("reach", [TopdownRoom.TILE, TopdownRoom.TILE])
	var run_across := absf(float(d[1])) >= absf(float(d[0]))
	var span := float(reach[0] if run_across else reach[1]) * 2.0 / TopdownRoom.ART   # art px along the way
	var out: Array = []
	if run_across:
		out.append(TopdownGate.new(room, p, true, int(span * 0.5) + 2, -1))
	else:
		var posts := maxi(2, int(round(span / 16.0)) + 1)
		for k in posts: out.append(TopdownGate.new(room, p, false, int(span * 0.5), k))
	return out

func _init(room: TopdownRoom, p: Dictionary, run_across: bool, half_len: int, piece: int) -> void:
	def = p
	across = run_across
	half = half_len
	seg = piece
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var a: Array = p.get("at", [0, 0])
	var d: Array = p.get("dir", [0, -1])
	var alt := float(p.get("alt", 0.0))
	var at := Vector2(float(a[0]), float(a[1]))
	# An edge's barrier stands a little inside the room's last column, so it is drawn whole on the room's floor.
	if not across: at.x -= float(d[0]) * 6.0
	feet = TopdownWorld.to_screen(at, alt).round()
	var key_at := at
	if not across: key_at.y += (_post_y(seg) - 0.0) * TopdownRoom.ART
	position = Vector2(feet.x, room.sort_key(key_at, alt))

## A post's offset down the screen from the way's point (a barrier down the screen), art px.
func _post_y(k: int) -> float:
	var posts := maxi(2, int(round(half * 2.0 / 16.0)) + 1)
	return -half + float(k) * (half * 2.0) / float(posts - 1)

func _process(_d: float) -> void:
	var c = Game.active()
	visible = c != null and bool(WorldShared.portal_state(c, def).get("gate", false))

func _draw() -> void:
	var o := Vector2(0, feet.y - position.y)   # the floor under the way, in this node's space
	if across: _draw_across(o)
	else: _draw_down(o)

func _px(p: Vector2, w: float, h: float, col: Color) -> void:
	draw_rect(Rect2(p.round(), Vector2(w, h)), col)

## A timber post standing at `f` (its foot): lit on its west face, a lacquered cap, the ink line on its east side.
func _post(f: Vector2) -> void:
	_px(f + Vector2(-3, -1), 7, 2, SHADOW)
	_px(f + Vector2(0, 0), 5, 1, SHADOW)
	_px(f + Vector2(-2, -POST_H), 4, POST_H, WOOD[1])
	_px(f + Vector2(-2, -POST_H), 1, POST_H, WOOD[3])
	_px(f + Vector2(-1, -POST_H), 1, POST_H, WOOD[2])
	_px(f + Vector2(2, -POST_H), 1, POST_H, LINE)
	_px(f + Vector2(-2, -1), 4, 1, WOOD[0])
	# The cap: red lacquer, lit on the west.
	_px(f + Vector2(-3, -POST_H - 3), 6, 3, RED[1])
	_px(f + Vector2(-3, -POST_H - 3), 2, 2, RED[3])
	_px(f + Vector2(-2, -POST_H - 4), 4, 1, RED[2])
	_px(f + Vector2(3, -POST_H - 3), 1, 3, LINE)

## A rail from x0 to x1 at height h over the floor at y (across the screen), 2 px deep, lit on top.
func _rail(y: float, x0: float, x1: float, h: int) -> void:
	_px(Vector2(x0, y - h - 1), x1 - x0, 1, WOOD[4])
	_px(Vector2(x0, y - h), x1 - x0, 1, WOOD[2])
	_px(Vector2(x0, y - h + 1), x1 - x0, 1, WOOD[0])

## A plank from a to b, two px thick (the cross-brace).
func _plank(a: Vector2, b: Vector2) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		var q := a.lerp(b, float(i) / float(maxi(1, n))).round()
		_px(q, 1, 1, WOOD[3])
		_px(q + Vector2(0, 1), 1, 1, WOOD[1])

## A red cord sagging from a to b with paper talismans hung along it every `every` px.
func _cord(a: Vector2, b: Vector2, sag: float, every: int) -> void:
	var n := int(absf(b.x - a.x)) if absf(b.x - a.x) > absf(b.y - a.y) else int(absf(b.y - a.y))
	for i in n + 1:
		var f := float(i) / float(maxi(1, n))
		var q := a.lerp(b, f) + Vector2(0, sag * 4.0 * f * (1.0 - f))
		_px(q.round(), 1, 1, RED[2] if i % 3 else RED[1])
		if i > 2 and i < n - 2 and i % every == every / 2:
			# A zigzag paper strip (a shide) and its shade.
			var s := q.round() + Vector2(0, 1)
			_px(s, 2, 2, PAPER[3])
			_px(s + Vector2(1, 2), 2, 2, PAPER[2])
			_px(s + Vector2(0, 4), 2, 2, PAPER[3])
			_px(s + Vector2(2, 2), 1, 2, PAPER[0])

## The notice board: a small paper-faced board with two ink columns, framed in dark wood, at `c` (its top middle).
func _board(c: Vector2) -> void:
	_px(c + Vector2(-6, 0), 12, 9, DARK)
	_px(c + Vector2(-5, 1), 10, 7, PAPER[2])
	_px(c + Vector2(-5, 1), 10, 1, PAPER[3])
	_px(c + Vector2(-5, 7), 10, 1, PAPER[1])
	for x in [-3, 1]:
		_px(c + Vector2(x, 2), 1, 4, INK)
		_px(c + Vector2(x + 1, 3), 1, 1, INK)
	_px(c + Vector2(4, 2), 1, 1, RED[2])   # the seal's red stamp

## Across the screen: a post at each end, the rails and the brace between them, the cord over them and the board.
func _draw_across(o: Vector2) -> void:
	var x0 := -float(half)
	var x1 := float(half)
	# Its shadow on the floor, falling to the south-east from the sun in the north-west.
	_px(o + Vector2(x0 + 2, 1), x1 - x0, 2, SHADOW)
	_plank(o + Vector2(x0 + 2, -RAILS[1]), o + Vector2(x1 - 2, -RAILS[0]))
	_plank(o + Vector2(x0 + 2, -RAILS[0]), o + Vector2(x1 - 2, -RAILS[1]))
	for h in RAILS: _rail(o.y, o.x + x0, o.x + x1, h)
	_post(o + Vector2(x0, 0))
	_post(o + Vector2(x1, 0))
	_cord(o + Vector2(x0, -POST_H + 1), o + Vector2(x1, -POST_H + 1), 4.0, 7)
	_board(o + Vector2(0, -RAILS[0] - 5))

## Down the screen (an east or west edge): this piece's post, and the rails and cord from the post before it (north).
func _draw_down(o: Vector2) -> void:
	var y1 := _post_y(seg)
	var here := o + Vector2(0, y1)
	if seg > 0:
		var y0 := _post_y(seg - 1)
		var top := o + Vector2(0, y0)
		_px(Vector2(o.x + 1, top.y + 1), 2, y1 - y0, SHADOW)
		for h in RAILS:
			_px(Vector2(o.x - 1, top.y - h - 1), 1, y1 - y0, WOOD[4])
			_px(Vector2(o.x, top.y - h - 1), 1, y1 - y0, WOOD[2])
			_px(Vector2(o.x + 1, top.y - h), 1, y1 - y0, WOOD[0])
		_cord(top + Vector2(0, -POST_H + 1), here + Vector2(0, -POST_H + 1), 1.0, 6)
	_post(here)
	# The notice board hangs on the middle post, facing the room.
	var posts := maxi(2, int(round(half * 2.0 / 16.0)) + 1)
	if seg == posts / 2: _board(here + Vector2(-float(def.get("dir", [1, 0])[0]) * 4.0, -RAILS[0] - 5))
