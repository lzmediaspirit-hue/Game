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
	for r in tr.rafts: out.append(LanternView.new(world, tr, r) if str(r.kind) == "lantern" else RaftView.new(world, tr, r))
	for c in tr.climbs: out.append(ClimbView.new(world, c))
	for u in tr.updrafts: out.append(SprayView.new(world, u))
	for c in tr.crumbles: out.append(BoardsView.new(world, tr, c))
	for f in tr.floods: out.append(FloodView.new(world, tr, f))
	# T2 (topdown_mechanics.md): the hatches, the bounces, the ice and the wind.
	for h in tr.hatches: out.append(HatchView.new(world, h))
	for b in tr.bounces: out.append(BounceView.new(world, b))
	for i in tr.ices: out.append(IceView.new(world, i))
	for wv in tr.winds: out.append(WindView.new(world, tr, wv))
	return out

## T2 · the ring of water round a swimmer's chest (the player's _draw), its feet at `feet` on the water's line.
static func draw_ripple(canvas: CanvasItem, feet: Vector2) -> void:
	if sheet() == null: return
	var r := src("ripple", int(Time.get_ticks_msec() / 300))
	canvas.draw_texture_rect_region(sheet(), Rect2(feet + Vector2(-roundf(r.size.x * 0.5), -4.0), r.size), r)

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
	## T2: a raft row's `look` and the deck each piece of its sprite covers (art px): the log raft and the lift two cells
	## square, the driftwood three cells by one, the planks two by one.
	const LOOKS := {"raft": ["raft_2x2", Vector2(32, 32)], "lift": ["lift_2x2", Vector2(32, 32)],
		"driftwood": ["driftwood", Vector2(48, 16)], "plank": ["plank", Vector2(32, 16)]}
	var tr: TopdownTraverse
	var raft: Dictionary
	var sprite := "raft_2x2"
	var piece := Vector2(32, 32)
	var bobs := true
	var at := Vector2.INF
	var frame := 0
	var size := Vector2.ZERO
	func _init(w, t: TopdownTraverse, r: Dictionary) -> void:
		super(w)
		tr = t
		raft = r
		var look: Array = LOOKS.get(str(r.get("look", "lift" if str(r.kind) == "lift" else "raft")), LOOKS.raft)
		sprite = str(look[0])
		piece = look[1]
		bobs = str(r.kind) == "raft"
		rects.append(Rect2())
		_place()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		_place()
	func _place() -> void:
		var deck := tr.raft_rect(raft)
		var p := (TopdownWorld.to_screen(deck.position, tr.deck_z(raft))).round()
		var f := (int(Time.get_ticks_msec() / 500) % 2) if bobs else 0
		if p == at and f == frame: return
		at = p
		frame = f
		size = deck.size / TopdownRoom.ART
		key(floorf(deck.position.y / TopdownRoom.ART))
		rects[0] = Rect2(p, size + Vector2(0, 6))
		queue_redraw()
	func _draw() -> void:
		var r := TopdownTraverseView.src(sprite, frame)
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
		# T2: boards that were the floor itself leave a hole when they go: the pit and its spikes, the pool's water, or
		# the shadow of the floor below.
		if state == "broken":
			if not bool(c.get("flush", false)): return
			var hole := {"pit": "pit", "water": "hole_water"}.get(str(c.hole), "gap") as String
			var g := TopdownTraverseView.src(hole)
			for p in cells: draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(p - position, g.size), g)
			return
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
		# T2: only over the cells whose floor is under the water now, row by row in runs (a dais or a gallery the water
		# does not reach stays dry), a lit line along each run's north edge where the cell north of it is dry.
		var r: Rect2 = f.rect
		var room: TopdownRoom = world.room
		var c0 := TopdownRoom.cell_of(r.position)
		var c1 := TopdownRoom.cell_of(r.end - Vector2.ONE)
		var under := func(cx: int, cy: int) -> bool:
			if not room.inside(cx, cy) or cx < c0.x or cx > c1.x or cy < c0.y or cy > c1.y: return false
			var fz := room.cell_floor(Vector2i(cx, cy))
			return room.is_water(cx, cy) or (fz < INF and fz < level - 0.5)
		for cy in range(c0.y, c1.y + 1):
			var cx := c0.x
			while cx <= c1.x:
				if not under.call(cx, cy):
					cx += 1
					continue
				var start := cx
				while cx <= c1.x and under.call(cx, cy): cx += 1
				var p := TopdownWorld.to_screen(Vector2(start, cy) * TopdownRoom.TILE, level).round() - position
				var sz := Vector2(float(cx - start), 1.0) * T
				draw_rect(Rect2(p, sz), DEEP)
				for lx in range(start, cx):
					if not under.call(lx, cy - 1): draw_rect(Rect2(p + Vector2((lx - start) * T, 0), Vector2(T, 1.0)), LIT)

# ------------------------------------------------------------------ T2 (topdown_mechanics.md)
## A sealed hatch across a flight's foot while the side view's climbable it stands for is shut (TopdownTraverse.hatches,
## `shut` the player's from climbable_open): a lattice gate with its paper seals standing on the floor at the flight's
## south edge, in two-cell pieces; gone once it opens. Keyed just before that edge, so a body in front draws over it.
class HatchView extends TopdownWorld.Sorted:
	var h: Dictionary
	var shut := false
	var at := Vector2.ZERO
	var width := 0.0
	func _init(w, hatch: Dictionary) -> void:
		super(w)
		h = hatch
		var r: Rect2 = hatch.rect
		var foot: float = w.room.height_at(Vector2(r.get_center().x, r.end.y - 1.0))
		at = TopdownWorld.to_screen(Vector2(r.position.x, r.end.y), foot).round()
		width = r.size.x / TopdownRoom.ART
		key(floorf(r.end.y / TopdownRoom.ART) - 0.5)
		rects.append(Rect2(at - Vector2(0, 26), Vector2(width, 26)))
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		if bool(h.shut) != shut:
			shut = bool(h.shut)
			queue_redraw()
	func _draw() -> void:
		if not shut: return
		var r := TopdownTraverseView.src("seal_gate")
		var x := 0.0
		while x < width - 0.5:
			draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(at - position + Vector2(x, -r.size.y + 2.0), r.size), r)
			x += r.size.x

## A bounce (TopdownTraverse.bounces) drawn as its look on its floor: the Fairground's drum, the Grey Pools' lotus leaf,
## the Whispering Bamboo's bent culm, centred on its cells with its foot on their south edge. Keyed at its north edge,
## as a deck.
class BounceView extends TopdownWorld.Sorted:
	var sprite := "drum"
	var at := Vector2.ZERO
	func _init(w, b: Dictionary) -> void:
		super(w)
		sprite = str(b.get("look", "drum"))
		var r: Rect2 = b.rect
		var sz := TopdownTraverseView.src(sprite).size
		at = TopdownWorld.to_screen(Vector2(r.get_center().x, r.end.y), float(b.z)).round() - Vector2(roundf(sz.x * 0.5), sz.y)
		key(floorf(r.position.y / TopdownRoom.ART))
		rects.append(Rect2(at, sz))
	func _draw() -> void:
		var r := TopdownTraverseView.src(sprite)
		draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(at - position, r.size), r)

## A lantern hung from the vault (TopdownTraverse.rafts of kind `lantern`): where the room's clock has swung it, its lid
## a deck at its level and its glowing body under it, on a chain up to the point it hangs from (over its rest for a
## swing, over its circle's middle for a circle), the chain's links every other pixel. Keyed at the deck's north edge,
## as a raft.
class LanternView extends TopdownWorld.Sorted:
	var tr: TopdownTraverse
	var raft: Dictionary
	var at := Vector2.INF
	var pivot := Vector2.ZERO
	var frame := 0
	func _init(w, t: TopdownTraverse, r: Dictionary) -> void:
		super(w)
		tr = t
		raft = r
		var rest: Rect2 = r.rest
		var hub := rest.get_center() + (Vector2(0, float(r.mover.radius)) if str(r.mover.mode) == "circle" else Vector2.ZERO)
		var high := float(r.mover.length) if str(r.mover.mode) == "swing" else 3.0 * TopdownRoom.LEVEL
		pivot = TopdownWorld.to_screen(hub, float(r.z) + high).round()
		rects.append(Rect2())
		_place()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		_place()
	func _place() -> void:
		var deck := tr.raft_rect(raft)
		var p := TopdownWorld.to_screen(deck.position, tr.deck_z(raft)).round()
		var f := int(Time.get_ticks_msec() / 600) % 2
		if p == at and f == frame: return
		at = p
		frame = f
		key(floorf(deck.position.y / TopdownRoom.ART))
		rects[0] = Rect2(Vector2(minf(p.x, pivot.x), pivot.y), Vector2(absf(p.x - pivot.x) + 32.0, p.y - pivot.y + 52.0))
		queue_redraw()
	func _draw() -> void:
		var top := at - position + Vector2(16, 14)
		var from := pivot - position
		var n := int(maxf(absf(top.x - from.x), absf(top.y - from.y)))
		for i in range(0, n, 2):
			var q := from.lerp(top, float(i) / float(maxi(1, n))).round()
			draw_rect(Rect2(q, Vector2(1, 1)), Color(0.36, 0.40, 0.42) if (i / 2) % 2 == 0 else Color(0.22, 0.26, 0.28))
		var r := TopdownTraverseView.src("lantern", frame)
		draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2(at - position, r.size), r)

## Ice glazed over a volume's cells (TopdownTraverse.ices): the sheen on every floor cell at its own height, its glint
## moving between the two frames on its own clock. Keyed at its north edge, flat on the floor.
class IceView extends TopdownWorld.Sorted:
	var cells: Array = []
	var frame := -1
	func _init(w, i: Dictionary) -> void:
		super(w)
		var r: Rect2 = i.rect
		var room: TopdownRoom = w.room
		var c0 := TopdownRoom.cell_of(r.position)
		var c1 := TopdownRoom.cell_of(r.end - Vector2.ONE)
		for cy in range(c0.y, c1.y + 1):
			for cx in range(c0.x, c1.x + 1):
				if not room.standable(Vector2i(cx, cy)) or not room.stair_at(cx, cy).is_empty(): continue
				cells.append([TopdownWorld.to_screen(Vector2(cx, cy) * TopdownRoom.TILE, room.cell_floor(Vector2i(cx, cy))).round(), (cx * 7 + cy * 3) % 2])
		key(floorf(r.position.y / TopdownRoom.ART))
		rects.clear()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		var f := int(Time.get_ticks_msec() / 900) % 2
		if f != frame:
			frame = f
			queue_redraw()
	func _draw() -> void:
		for c in cells:
			var r := TopdownTraverseView.src("ice", frame + int(c[1]))
			draw_texture_rect_region(TopdownTraverseView.sheet(), Rect2((c[0] as Vector2) - position, r.size), r)

## The wind over a volume's cells (TopdownTraverse.winds): curls of snow and grit blown along its push across the floor,
## more of them and faster while it blows strong, a few drifting in the breeze, each at the floor's height where it is.
## Over everything in the cells it crosses (keyed at the volume's south edge).
class WindView extends TopdownWorld.Sorted:
	var tr: TopdownTraverse
	var wv: Dictionary
	var motes: Array = []   ## [x0, y, phase] in world units
	func _init(w, t: TopdownTraverse, wind: Dictionary) -> void:
		super(w)
		tr = t
		wv = wind
		var r: Rect2 = wind.rect
		var n := int(clampf(r.size.x * r.size.y / (TopdownRoom.TILE * TopdownRoom.TILE * 14.0), 4.0, 48.0))
		for i in n:
			motes.append([r.position.x + fposmod(float(i) * 97.0, r.size.x), r.position.y + fposmod(float(i) * 61.0 + 13.0, r.size.y), float(i % 7) / 7.0])
		key(r.end.y / TopdownRoom.ART)
		rects.clear()
	func _ready() -> void:
		set_process(true)
	func _process(_d: float) -> void:
		queue_redraw()
	func _draw() -> void:
		var r: Rect2 = wv.rect
		var k := tr.wind_strength(wv)
		var push: Vector2 = wv.push
		var dir := signf(push.x) if absf(push.x) > 0.01 else 1.0
		var t := Time.get_ticks_msec() / 1000.0
		var room: TopdownRoom = world.room
		for i in motes.size():
			var m: Array = motes[i]
			if k < 0.9 and i % 3 != 0: continue   # the breeze carries a few
			var run := fposmod(float(m[0]) - r.position.x + dir * t * (220.0 if k >= 0.9 else 70.0) + float(m[2]) * r.size.x, r.size.x)
			var p := Vector2(r.position.x + run, float(m[1]))
			var fz := room.height_at(p)
			if fz == INF: continue
			var s := TopdownTraverseView.src("wind", int(t * 8.0 + float(i)) % 3)
			var dst := Rect2(TopdownWorld.to_screen(p, maxf(fz, 0.0) + 10.0).round() - position, s.size)
			if dir < 0.0: dst = Rect2(dst.position + Vector2(s.size.x, 0), Vector2(-s.size.x, s.size.y))
			draw_texture_rect_region(TopdownTraverseView.sheet(), dst, s)
