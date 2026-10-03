class_name TopdownTraverseView
extends RefCounted
## T1 (docs/architecture/topdown_mechanics.md): the room view's side of the traversal (TopdownTraverse): each raft on
## the water riding its run on the room's clock (and each lift's deck rising and falling), each climbable face hung
## with its vine, rope, ladder or chain, each updraft's column of rising spray, rotten boards giving way, and a flood's
## water rising over its cells, drawn from the traversal sheet (art/topdown/traverse.png, built by
## tools/art/topdown/build_traverse.py, its manifest data/topdown/traverse_art.json), in the sorted layer by the grid's
## keys. The glide's leaf over the body is the player's to draw (`draw_glide`). Nearest neighbour, whole art px.

const ART_PATH := "res://data/topdown/traverse_art.json"
const T := 16.0
static var _art = null
static var _sheet: Texture2D = null

## The manifest's sprites, read once: name -> {rect: [x, y, frame w, h], frames}.
static func art() -> Dictionary:
	if _art == null:
		var d = JSON.parse_string(FileAccess.get_file_as_string(ART_PATH))
		_art = d.get("sprites", {}) if d is Dictionary else {}
		_sheet = load(str(d.get("sheet", ""))) if d is Dictionary else null
	return _art

static func sheet() -> Texture2D:
	art()
	return _sheet

## A sprite's source rect for frame `f`.
static func src(name: String, f := 0) -> Rect2:
	var s: Dictionary = art().get(name, {})
	var r: Array = s.get("rect", [0, 0, 1, 1])
	return Rect2(float(r[0]) + float(r[2]) * float(posmod(f, maxi(1, int(s.get("frames", 1))))), float(r[1]), float(r[2]), float(r[3]))

## The views of the room's traversal, to add to the world's sorted layer ([] when its layout has none).
static func build(world) -> Array:
	var tr := TopdownTraverse.of(world.room)
	var out: Array = []
	if tr == null or tr.is_empty() or sheet() == null: return out
	for r in tr.rafts: out.append(RaftView.new(world, tr, r))
	for c in tr.climbs: out.append(ClimbView.new(world, c))
	for u in tr.updrafts: out.append(SprayView.new(world, u))
	for c in tr.crumbles: out.append(BoardsView.new(world, tr, c))
	for f in tr.floods: out.append(FloodView.new(world, tr, f))
	return out

## Falling Leaf Glide's leaf of qi spread over a gliding body, its feet at `feet` on `canvas` (the player's _draw).
static func draw_glide(canvas: CanvasItem, feet: Vector2) -> void:
	if sheet() == null: return
	var r := src("glide", int(Time.get_ticks_msec() / 160))
	canvas.draw_texture_rect_region(sheet(), Rect2(feet + Vector2(-roundf(r.size.x * 0.5), -53.0), r.size), r)

## Flight's cloud of qi under a flying body's feet (the player's _draw), drifting between its frames.
static func draw_cloud(canvas: CanvasItem, feet: Vector2) -> void:
	if sheet() == null: return
	var r := src("cloud", int(Time.get_ticks_msec() / 220))
	canvas.draw_texture_rect_region(sheet(), Rect2(feet + Vector2(-roundf(r.size.x * 0.5), -4.0), r.size), r)

## A raft on the water (or a lift's deck): where the room's clock has carried it, a raft bobbing a px on the water's
## clock, a lift at its deck's height now; a deck larger than two cells is laid in two-cell pieces. Its key is the
## deck's north edge on the plane, so a body standing on the deck draws over it and one north of it under it.
class RaftView extends TopdownWorld.Sorted:
	var tr: TopdownTraverse
	var raft: Dictionary
	var sprite := "raft_2x2"
	var at := Vector2.INF
	var frame := 0
	var size := Vector2.ZERO
	func _init(w, t: TopdownTraverse, r: Dictionary) -> void:
		super(w)
		tr = t
		raft = r
		sprite = "lift_2x2" if str(r.kind) == "lift" else "raft_2x2"
		rects.append(Rect2())
		_place()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		_place()
	func _place() -> void:
		var deck := tr.raft_rect(raft)
		var p := (TopdownWorld.to_screen(deck.position, tr.deck_z(raft))).round()
		var f := (int(Time.get_ticks_msec() / 500) % 2) if sprite == "raft_2x2" else 0
		if p == at and f == frame: return
		at = p
		frame = f
		size = deck.size / TopdownRoom.ART
		key(floorf(deck.position.y / TopdownRoom.ART))
		rects[0] = Rect2(p, size + Vector2(0, 6))
		queue_redraw()
	func _draw() -> void:
		var r := TopdownTraverseView.src(sprite, frame)
		var piece := Vector2(2.0, 2.0) * T
		var y := 0.0
		while y < size.y - 0.5:
			var x := 0.0
			while x < size.x - 0.5:
				draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(at - position + Vector2(x, y), r.size), r)
				x += piece.x
			y += piece.y

## A climbable face hung with its kind's tiles: on a south face down the face from the lip to the floor (the top tile at
## the lip, the middle ones a level each, the foot on the floor); on an east or west side, hanging at the edge from
## the top floor down to the foot's. Its key is just after the raised row's own, so a body on the face draws over it.
class ClimbView extends TopdownWorld.Sorted:
	var kind := "vine"
	var x := 0.0
	var lip := 0.0
	var foot := 0.0
	func _init(w, c: Dictionary) -> void:
		super(w)
		kind = str(c.kind)
		var top: Vector2 = c.top
		var ft: Vector2 = c.foot
		var d: Vector2 = c.dir
		var tc := TopdownRoom.cell_of(top)
		if absf(d.y) > 0.5:
			# A south face (or a north one, seen from behind: drawn the same, on the row in front).
			var row := maxi(tc.y, TopdownRoom.cell_of(ft).y)
			x = float(tc.x) * T
			lip = float(row) * T - float(c.top_z) / TopdownRoom.ART
			foot = float(row) * T - float(c.foot_z) / TopdownRoom.ART
			key(float(c.front_key))
		else:
			# A side: it hangs at the edge between the cells, from the top floor's middle row down to the foot's.
			x = (float(tc.x) + (0.5 if d.x < 0.0 else -0.5)) * T
			lip = float(tc.y) * T + T * 0.5 - float(c.top_z) / TopdownRoom.ART
			foot = float(tc.y) * T + T * 0.5 - float(c.foot_z) / TopdownRoom.ART
			key(float(c.front_key))   # in front of the raised floor's whole side in this column
		rects.append(Rect2(x, lip - 2.0, T, foot - lip + 4.0))
	func _draw() -> void:
		var tex := TopdownTraverseView.sheet()
		var lift := position.y
		var y := lip - 2.0
		draw_texture_rect_region(tex, Rect2(Vector2(x, y - lift), Vector2(T, T)), TopdownTraverseView.src(kind + "_top"))
		y += T
		while y < foot - T - 2.0:
			draw_texture_rect_region(tex, Rect2(Vector2(x, y - lift), Vector2(T, T)), TopdownTraverseView.src(kind + "_mid"))
			y += T
		draw_texture_rect_region(tex, Rect2(Vector2(x, foot - T + 2.0 - lift), Vector2(T, T)), TopdownTraverseView.src(kind + "_foot"))

## An updraft's column of rising spray over its cells: a column on every other cell, each rising from the water's
## surface to the updraft's top, the frames turning on its own clock (each column at its own phase). Its key is the
## column's south edge: a body in the spray shows through its mist.
class SprayView extends TopdownWorld.Sorted:
	var cols: Array = []   ## [screen x, water y, height, phase]
	var frame := -1
	func _init(w, u: Dictionary) -> void:
		super(w)
		var r: Rect2 = u.rect
		var top := float(u.hi) / TopdownRoom.ART
		var c0 := TopdownRoom.cell_of(r.position)
		var c1 := TopdownRoom.cell_of(r.end - Vector2.ONE)
		for cy in range(c0.y, c1.y + 1):
			for cx in range(c0.x, c1.x + 1):
				if (cx + cy) % 2 != 0: continue
				var water := float(cy + 1) * T - TopdownRoom.WATER_Z / TopdownRoom.ART
				cols.append([float(cx) * T, water, top + T * 0.5, (cx * 3 + cy * 5) % 4])
		key(r.end.y / TopdownRoom.ART)
		rects.clear()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		var f := int(Time.get_ticks_msec() / 120) % 4
		if f != frame:
			frame = f
			queue_redraw()
	func _draw() -> void:
		var tex := TopdownTraverseView.sheet()
		var lift := position.y
		for c in cols:
			var r := TopdownTraverseView.src("spray", frame + int(c[3]))
			var h := float(c[2])
			var y := float(c[1]) - h
			while y < float(c[1]) - 0.5:
				var part := minf(r.size.y, float(c[1]) - y)
				draw_texture_rect_region(tex, Rect2(Vector2(float(c[0]), y - lift), Vector2(r.size.x, part)), Rect2(r.position, Vector2(r.size.x, part)))
				y += r.size.y

## Rotten boards over a pit, a cell each: whole, split and sagging while they give under a foot, gone (the pit showing)
## until they are back, on the room's clock (TopdownTraverse.crumble_state). Keyed at their north edge, as a deck.
class BoardsView extends TopdownWorld.Sorted:
	var tr: TopdownTraverse
	var c: Dictionary
	var state := ""
	var cells: Array = []
	func _init(w, t: TopdownTraverse, cr: Dictionary) -> void:
		super(w)
		tr = t
		c = cr
		var r: Rect2 = cr.rect
		var c0 := TopdownRoom.cell_of(r.position)
		var c1 := TopdownRoom.cell_of(r.end - Vector2.ONE)
		for cy in range(c0.y, c1.y + 1):
			for cx in range(c0.x, c1.x + 1):
				cells.append(TopdownWorld.to_screen(Vector2(cx, cy) * TopdownRoom.TILE, float(cr.z)).round())
		key(floorf(r.position.y / TopdownRoom.ART))
		rects.clear()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		var s := tr.crumble_state(c)
		if s != state:
			state = s
			queue_redraw()
	func _draw() -> void:
		if state == "broken": return
		var r := TopdownTraverseView.src("boards", 1 if state == "giving" else 0)
		for p in cells: draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(p - position, r.size), r)

## A flood's water over its cells at the height it has risen to now (nothing while it lies at rest), a sheet of the
## water's colour with a lit line along its north edge. Keyed just before its north edge, so a body wading in it draws
## over it.
class FloodView extends TopdownWorld.Sorted:
	const DEEP := Color(0.16, 0.36, 0.46, 0.62)
	const LIT := Color(0.62, 0.84, 0.86, 0.75)
	var tr: TopdownTraverse
	var f: Dictionary
	var level := -INF
	func _init(w, t: TopdownTraverse, fl: Dictionary) -> void:
		super(w)
		tr = t
		f = fl
		key(floorf((fl.rect as Rect2).position.y / TopdownRoom.ART) - 0.25)
		rects.clear()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		var k := tr.flood_k(f)
		var z := roundf(lerpf(TopdownRoom.WATER_Z, float(f.top), k)) if k > 0.0 else -INF
		if z != level:
			level = z
			queue_redraw()
	func _draw() -> void:
		if level == -INF: return
		var r: Rect2 = f.rect
		var p := TopdownWorld.to_screen(r.position, level).round() - position
		var sz := (r.size / TopdownRoom.ART).round()
		draw_rect(Rect2(p, sz), DEEP)
		draw_rect(Rect2(p, Vector2(sz.x, 1.0)), LIT)
