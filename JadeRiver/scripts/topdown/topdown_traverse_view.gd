class_name TopdownTraverseView
extends RefCounted
## T1 (docs/architecture/topdown_mechanics.md): the room view's side of the traversal (TopdownTraverse): each raft on
## the water riding its run on the room's clock, each climbable face hung with its vine, rope, ladder or chain, and
## each updraft's column of rising spray, drawn from the traversal sheet (art/topdown/traverse.png, built by
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
	return out

## Falling Leaf Glide's leaf of qi spread over a gliding body, its feet at `feet` on `canvas` (the player's _draw).
static func draw_glide(canvas: CanvasItem, feet: Vector2) -> void:
	if sheet() == null: return
	var r := src("glide", int(Time.get_ticks_msec() / 160))
	canvas.draw_texture_rect_region(sheet(), Rect2(feet + Vector2(-roundf(r.size.x * 0.5), -53.0), r.size), r)

## A raft on the water: its deck where the room's clock has carried it, bobbing a px on the water's clock. Its key is
## its deck's north edge, so a body standing on the deck draws over it and one on the bank north of it under it.
class RaftView extends TopdownWorld.Sorted:
	var tr: TopdownTraverse
	var raft: Dictionary
	var at := Vector2.INF
	var frame := 0
	func _init(w, t: TopdownTraverse, r: Dictionary) -> void:
		super(w)
		tr = t
		raft = r
		rects.append(Rect2())
		_place()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		_place()
	func _place() -> void:
		var deck := tr.raft_rect(raft)
		var p := (TopdownWorld.to_screen(deck.position, float(raft.z))).round()
		var f := int(Time.get_ticks_msec() / 500) % 2
		if p == at and f == frame: return
		at = p
		frame = f
		key(floorf(p.y))
		rects[0] = Rect2(p, deck.size / TopdownRoom.ART + Vector2(0, 6))
		queue_redraw()
	func _draw() -> void:
		var r := TopdownTraverseView.src("raft_2x2", frame)
		draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(at - position, r.size), r)

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
