class_name TopdownPlaceArt
extends Node2D
## Decision 43, systems as places (docs/redesign/systems_as_places.md, "As built"): what the world draws at a place
## (data/places.json, PlaceRules), in the room's pixel viewport, one art px a px, in the palette of
## tools/art/topdown/palette.py with the sun in the north-west (art bible §14), original art drawn here pixel by pixel,
## nearest-neighbour. Three uses:
##   - "object": a thing the places table adds to a room, drawn whole as its Figure's art (TopdownPlaces): the letter box
##     (a red ribbon and its flag up while a letter waits), the meditation mat (the Qi mist over it, thicker as the room's
##     Qi is denser);
##   - "overlay": what an object of the side view shows as a place, a child of its Figure over its prop: the notice
##     board's papers (one per bounty, request and mission) and a gold "!" while one is new; the furnace's smoke while a
##     batch is in it and a jade wisp when one is ready; a ripe bed's glints;
##   - "sight": a structure round a place, sorted with the room at its footprint's south edge (its `solid` cells block):
##     the Storehouse's shed (its shelves' sacks by what the storehouse holds), a stall's counter with its wares, and the
##     stall's awning behind its keeper.
## Under Reduce motion the state stays and the motion stops (still smoke, a steady glow).

const WOOD := [Color("24150b"), Color("3f2616"), Color("623e23"), Color("875a33"), Color("ab7a47"), Color("cb9c64"), Color("e2bf8a")]
const DARK := [Color("1a1009"), Color("311f12"), Color("4e331e"), Color("6e4b2b"), Color("90683d")]
const ROOF := [Color("141a1f"), Color("222b32"), Color("323e46"), Color("46545c"), Color("5e6d74"), Color("7d8c90"), Color("a3b0b0")]
const PLASTER := [Color("6e685b"), Color("9a917d"), Color("bdb39c"), Color("d6ceb8"), Color("e8e1cf"), Color("f6f1e3")]
const RED := [Color("35101a"), Color("641b26"), Color("962a2f"), Color("c23d37"), Color("de5a45"), Color("f2866a")]
const GOLD := [Color("6e4a1c"), Color("a8772f"), Color("e5b84c"), Color("ffe6a1"), Color("fff8e2")]
const REED := [Color("2a2a12"), Color("46461c"), Color("6c6a2a"), Color("98923e"), Color("c4bc62")]
const EARTH := [Color("261811"), Color("3e271b"), Color("583a27"), Color("745035"), Color("916a47"), Color("ae875e"), Color("c9a77c")]
const JADE := [Color("15514f"), Color("2c9e8f"), Color("67d6bd"), Color("c8f4e6")]
const CLOTH := {"stoneford_general": [Color("15514f"), Color("2c9e8f"), Color("67d6bd")], "stoneford_tea": [Color("641b26"), Color("c23d37"), Color("f2866a")]}
const INK := Color("071015")
const LINE := Color("0e1a1e")
const SHADOW := Color(0.141, 0.122, 0.31, 0.41)
const BOARD := Color("7a4f2c")          ## the notice board's cork, as its prop has it
const BOARD_DARK := Color("58371f")
const QI := Color("32bed1")

var place: Dictionary = {}
var def: Dictionary = {}                ## the object's definition (an added thing's, or the side view's object)
var kind := ""                          ## letter_box, meditation_mat, board, furnace, bed, shed, stall_front, stall_back
var t := 0.0
var hit_flash := 0.0                    ## a Figure copies its label twin's into its art
var focus := false
var rects: Array = []                   ## what a sight covers on screen, for the silhouette test
var size_cells := Vector2i.ONE
var bed_key := ""                       ## a bed's "room:object"
var st: Dictionary = {}                 ## PlaceRules.state, looked at a few times a second
var _look := 0.0

static func motion() -> bool:
	return not UiKit.reduce_motion()

# ------------------------------------------------------------------ making them
## The art of an added thing (its object's `place` names its row): drawn whole as its Figure's art.
static func object(o: Dictionary) -> TopdownPlaceArt:
	var a := TopdownPlaceArt.new()
	a.def = o
	a.place = PlaceRules.get_place(str(o.get("place", "")))
	a.kind = str(o.get("type", ""))
	a.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return a

## The sights and overlays of a room's places, made as TopdownPlaces builds the room: overlays onto the objects'
## Figures (`figures`: object id -> Figure; they go with them), sights into `sorted`. Returns the sights made.
static func build(room: TopdownRoom, room_id: String, sorted: Node2D, figures: Dictionary) -> Array:
	var made: Array = []
	for r in PlaceRules.of_room(room_id):
		var art: Dictionary = r.get("art", {})
		match str(art.get("kind", "")):
			"shed":
				made.append(_sight(room, r, "shed", art.cells, sorted))
			"stall":
				made.append(_sight(room, r, "stall_front", art.cells, sorted))
				# The awning and its rack stand behind the keeper, a row back, sorted at that row's north edge.
				var back: Array = (art.cells as Array).duplicate()
				back[1] = int(back[1]) - 1
				made.append(_sight(room, r, "stall_back", back, sorted, true))
		var overlay: String = {"papers": "board", "smoke": "furnace", "growth": "bed"}.get(str(r.get("state", "")), "")
		if overlay == "": continue
		for oid in (r.get("beds", [r.object]) if overlay == "bed" else [r.object]):
			var fig = figures.get(str(oid))
			if fig == null or not is_instance_valid(fig): continue
			var o := TopdownPlaceArt.new()
			o.place = r
			o.def = fig.def
			o.kind = overlay
			o.bed_key = room_id + ":" + str(oid)
			o.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			o.position = fig.art.position
			fig.add_child(o)   # it goes with its Figure when the room is left
	return made

## A sight on its cells [x, y, w, h]: sorted at the footprint's south edge (`north`: its north edge, for what stands
## behind a keeper), drawn from the middle of its south edge on the floor there (the ground's level; a place's cells are
## the ground's, never a prop's top).
static func _sight(room: TopdownRoom, r: Dictionary, what: String, cells: Array, sorted: Node2D, north := false) -> TopdownPlaceArt:
	var a := TopdownPlaceArt.new()
	a.place = r
	a.kind = what
	a.size_cells = Vector2i(int(cells[2]), int(cells[3]))
	a.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var sw := Vector2(float(cells[0]) * 16.0, float(int(cells[1]) + int(cells[3])) * 16.0)
	var lv: int = room.levels[(int(cells[1]) + int(cells[3]) - 1) * room.w + int(cells[0])] if room.inside(int(cells[0]), int(cells[1]) + int(cells[3]) - 1) else 0
	var ground := float(maxi(lv, 0)) * 16.0
	var feet := Vector2(roundf(sw.x + size_px(a.size_cells).x * 0.5), sw.y - ground)
	# Whole art px: a key a body standing in front of the footprint (its foot box clear of the solid cells) sorts after.
	a.position = Vector2(feet.x, float(int(cells[1])) * 16.0 if north else sw.y)
	a.set_meta("feet_dy", feet.y - a.position.y - (12.0 if north else 0.0))
	var w := float(a.size_cells.x * 16)
	if what == "shed": a.rects = [Rect2(feet + Vector2(-w * 0.5 - 2, -70), Vector2(w + 4, 70))]
	sorted.add_child(a)
	return a

static func size_px(cells: Vector2i) -> Vector2:
	return Vector2(cells) * 16.0

# ------------------------------------------------------------------ the frame
func _process(delta: float) -> void:
	t += delta
	_look -= delta
	if _look <= 0.0:
		_look = 0.25
		var c = Game.active()
		if c != null and not place.is_empty():
			if kind == "bed":
				var v: Dictionary = Game.crafting.bed_view(c, bed_key)
				st = {"on": v.ready, "n": 1 if v.ready else 0}
			else:
				st = PlaceRules.state(c, place)
	queue_redraw()

func _px(p: Vector2, w: float, h: float, col: Color) -> void:
	draw_rect(Rect2(p.round(), Vector2(w, h)), col)

func _draw() -> void:
	var o := Vector2(0.0, float(get_meta("feet_dy", 0.0)))   # the footprint's south edge on the floor, for a sight
	match kind:
		"letter_box": _letter_box(Vector2.ZERO)
		"meditation_mat": _mat(Vector2.ZERO)
		"board": _board_papers()
		"furnace": _furnace_smoke()
		"bed": _bed_glints()
		"shed": _shed(o)
		"stall_front": _stall_front(o)
		"stall_back": _stall_back(o)

# ------------------------------------------------------------------ the letter box
## A post box of red-lacquered wood on a dark post over a stone footing, under a little roof of grey tile, a slot in its
## face and a paper plaque over it; a courier post carries a jade pennant beside it. While a letter waits its flag stands
## up on its east side, a red ribbon is tied round it with a bow, and a gold glint turns over its roof; with none the
## flag lies folded along its side.
func _letter_box(f: Vector2) -> void:
	var waiting := bool(st.get("on", false))
	# The floor shadow, to the south-east, and the stone footing.
	_px(f + Vector2(-5, -1), 14, 3, SHADOW)
	_px(f + Vector2(-4, -3), 8, 3, ROOF[3])
	_px(f + Vector2(-4, -3), 8, 1, ROOF[5])
	_px(f + Vector2(3, -3), 1, 3, ROOF[1])
	# The post.
	_px(f + Vector2(-2, -17), 4, 14, DARK[2])
	_px(f + Vector2(-2, -17), 1, 14, DARK[4])
	_px(f + Vector2(1, -17), 1, 14, LINE)
	# The box: 16 wide, 13 high; its face lit on the west, its east side in shade, an ink line round it.
	var b := f + Vector2(-8, -30)
	_px(b + Vector2(-1, -1), 18, 15, INK)
	_px(b, 16, 13, RED[2])
	_px(b, 2, 13, RED[4])
	_px(b + Vector2(2, 0), 11, 1, RED[3])
	_px(b + Vector2(13, 0), 3, 13, RED[1])
	_px(b + Vector2(0, 12), 16, 1, RED[1])
	# The paper plaque (its name in ink) and the slot under it; the brass latch.
	_px(b + Vector2(4, 2), 7, 4, PLASTER[4])
	_px(b + Vector2(4, 5), 7, 1, PLASTER[2])
	_px(b + Vector2(6, 3), 1, 2, INK)
	_px(b + Vector2(8, 3), 1, 1, INK)
	_px(b + Vector2(8, 4), 2, 1, INK)
	_px(b + Vector2(3, 8), 9, 1, INK)
	_px(b + Vector2(3, 9), 9, 1, RED[1])
	_px(b + Vector2(7, 10), 2, 2, GOLD[2])
	_px(b + Vector2(7, 10), 1, 1, GOLD[3])
	# Its roof of grey tile: a lit lip over a shadow line, a rib every 3 px, the ends swept up.
	_px(b + Vector2(-3, -5), 22, 4, ROOF[3])
	_px(b + Vector2(-3, -5), 22, 1, ROOF[5])
	for k in range(0, 22, 3): _px(b + Vector2(-3 + k, -4), 1, 3, ROOF[1])
	_px(b + Vector2(-4, -6), 2, 2, ROOF[4])
	_px(b + Vector2(18, -6), 2, 2, ROOF[4])
	_px(b + Vector2(-4, -7), 1, 1, GOLD[2])
	_px(b + Vector2(19, -7), 1, 1, GOLD[2])
	_px(b + Vector2(-3, -1), 22, 1, Color(SHADOW, 0.7))
	if str(def.get("post", "")) == "courier":
		# A courier post's jade pennant on a thin staff to the east, clear of the courier beside it.
		_px(f + Vector2(12, -42), 1, 42, DARK[3])
		_px(f + Vector2(11, -1), 3, 1, DARK[1])
		var wave := roundf(sin(t * 3.0)) if motion() else 0.0
		for k in 7: _px(f + Vector2(13, -42 + k), 8 - k, 1, JADE[1] if k % 2 else JADE[2])
		_px(f + Vector2(20 + wave, -41), 1, 2, JADE[3])
		_px(f + Vector2(11, -43), 3, 1, GOLD[2])
	# The flag on its east side: up while a letter waits, folded down along the side when none does.
	if waiting:
		var flick := roundf(sin(t * 5.0)) if motion() else 0.0
		_px(b + Vector2(16, -8), 1, 14, DARK[3])
		_px(b + Vector2(17, -8), 6 + flick, 4, RED[4])
		_px(b + Vector2(17, -8), 6 + flick, 1, RED[5])
		_px(b + Vector2(17, -5), 6 + flick, 1, RED[2])
		# The ribbon round the box, a bow on its face, the tails hanging.
		_px(b + Vector2(0, 6), 16, 2, RED[4])
		_px(b + Vector2(0, 6), 16, 1, RED[5])
		_px(b + Vector2(5, 5), 2, 4, RED[3])
		_px(b + Vector2(9, 5), 2, 4, RED[3])
		_px(b + Vector2(7, 6), 2, 2, RED[5])
		var sway := 1.0 if motion() and fmod(t, 1.2) < 0.6 else 0.0
		_px(b + Vector2(6, 9), 1, 4 + sway, RED[3])
		_px(b + Vector2(9, 9), 1, 3, RED[4])
		# A gold glint turning over the roof, so a waiting letter reads from across the square.
		var g := 0.6 + 0.4 * sin(t * 3.0) if motion() else 1.0
		var gc := b + Vector2(8, -12)
		_px(gc, 1, 1, Color(GOLD[4], g))
		_px(gc + Vector2(-1, 0), 3, 1, Color(GOLD[3], g * 0.8))
		_px(gc + Vector2(0, -1), 1, 3, Color(GOLD[3], g * 0.8))
		_px(gc + Vector2(-2, 0), 5, 1, Color(GOLD[2], g * 0.35))
		_px(gc + Vector2(0, -2), 1, 5, Color(GOLD[2], g * 0.35))
	else:
		_px(b + Vector2(16, 3), 1, 7, DARK[3])
		_px(b + Vector2(16, 7), 3, 4, RED[2])
		_px(b + Vector2(16, 7), 1, 4, RED[3])

# ------------------------------------------------------------------ the meditation mat
## A round mat of woven cattail (24 x 12), its rings of weave lit on the north-west rim, with a cushion of faded red on
## it; Qi mist drifts up over it, the motes thicker as the room's Qi is denser (the spring beside it), and a faint ring of
## it lies on the mat.
func _mat(f: Vector2) -> void:
	var rows := [[-5, 8], [-4, 10], [-3, 11], [-2, 12], [-1, 12], [0, 12], [1, 11], [2, 10], [3, 8], [4, 5]]
	_px(f + Vector2(-9, 4), 20, 2, Color(SHADOW, 0.8))   # its shade to the south-east
	for rw in rows:
		var y: int = rw[0]
		var hw: int = rw[1]
		_px(f + Vector2(-hw, y), hw * 2, 1, REED[3] if y < -2 else (REED[2] if y < 2 else REED[1]))
	# The weave: rings of darker straw every third row, and the stitches between.
	for rw in rows:
		var y: int = rw[0]
		var hw: int = rw[1] - 1
		if (y + 5) % 3 == 0: _px(f + Vector2(-hw, y), hw * 2, 1, REED[1] if y >= 0 else REED[2])
		for x in range(-hw + ((y + 5) & 1), hw, 3): _px(f + Vector2(x, y), 1, 1, REED[4] if y < 0 else REED[3])
	_px(f + Vector2(-10, -4), 7, 1, REED[4])            # the lit rim to the north-west
	_px(f + Vector2(-6, -5), 6, 1, REED[4])
	# The cushion: a round zafu of faded red, lit on its top.
	_px(f + Vector2(-5, -6), 10, 5, RED[1])
	_px(f + Vector2(-4, -7), 8, 2, RED[3])
	_px(f + Vector2(-4, -7), 3, 1, RED[4])
	_px(f + Vector2(-5, -2), 10, 1, RED[0])
	_px(f + Vector2(-1, -5), 2, 1, RED[2])
	if not bool(st.get("on", false)): return
	# The Qi mist: motes drifting up and round, more of them the denser the room's Qi.
	var n := clampi(int(round(float(st.get("n", 1.0)) * 8.0)), 8, 18)
	for i in n:
		var ph := fmod(t * 0.3 + i * 0.37, 1.0) if motion() else float(i) / float(n)
		var a := TAU * (i * 0.618)
		var p := f + Vector2(cos(a + t * 0.5 * float(motion())) * (6.0 + float(i % 3) * 4.0), -3.0 - ph * 32.0)
		var fade := sin(ph * PI)
		_px(p, 2, 2, Color(QI.lerp(JADE[3], 0.35), 0.95 * fade))
		_px(p, 1, 1, Color(Color.WHITE, 0.9 * fade))
	# The ring of it lying on the mat.
	var pulse := 0.4 + 0.15 * sin(t * 2.0) if motion() else 0.45
	_px(f + Vector2(-11, -1), 22, 1, Color(JADE[2], pulse))
	_px(f + Vector2(-9, 2), 18, 1, Color(JADE[2], pulse * 0.8))
	_px(f + Vector2(-12, 0), 1, 2, Color(JADE[2], pulse))
	_px(f + Vector2(11, 0), 1, 2, Color(JADE[2], pulse))

# ------------------------------------------------------------------ the notice board's papers
## Over the board's cork: one paper for each bounty, request and mission posted (six at most), pinned in two rows;
## while one is new since the character last read it, a gold "!" bobs over the board's roof.
func _board_papers() -> void:
	var face := Rect2(-12, -29, 24, 20)
	_px(face.position, face.size.x, face.size.y, BOARD)
	for y in [face.position.y + 6, face.position.y + 13]: _px(Vector2(face.position.x, y), face.size.x, 1, BOARD_DARK)
	_px(face.position, face.size.x, 1, Color(INK, 0.5))   # the frame's shade on the cork
	var n := mini(int(st.get("n", 0)), 6)
	var spots := [Vector2(-10, -27), Vector2(-3, -28), Vector2(4, -27), Vector2(-9, -19), Vector2(-2, -18), Vector2(5, -19)]
	for i in n:
		var p: Vector2 = face.position + (spots[i] - face.position)
		_px(p + Vector2(1, 1), 6, 7, Color(INK, 0.35))
		_px(p, 6, 7, PLASTER[4])
		_px(p + Vector2(0, 6), 6, 1, PLASTER[2])
		_px(p + Vector2(5, 0), 1, 7, PLASTER[3])
		_px(p + Vector2(1, 2), 4, 1, PLASTER[0])
		_px(p + Vector2(1, 4), 3, 1, PLASTER[0])
		_px(p + Vector2(2, -1), 2, 1, RED[3] if i % 2 == 0 else RED[2])   # its pin
	if int(st.get("new", 0)) <= 0: return
	var bob := roundf(sin(t * 3.5) * 1.5) if motion() else 0.0
	var c := Vector2(0, -52 + bob)
	_px(c + Vector2(-2, -1), 5, 11, INK)
	_px(c + Vector2(-1, 0), 3, 6, GOLD[2])
	_px(c + Vector2(-1, 0), 1, 6, GOLD[3])
	_px(c + Vector2(-1, 7), 3, 2, GOLD[2])
	_px(c + Vector2(-1, 7), 1, 1, GOLD[3])

# ------------------------------------------------------------------ the furnace's smoke
## While a batch is in the furnace (the auto-refine queue, a refine left burning) smoke rises from its top in puffs; when
## one is ready to take a jade wisp curls over it.
func _furnace_smoke() -> void:
	if not bool(st.get("on", false)) and int(st.get("new", 0)) <= 0: return
	var top := Vector2(0, -40)
	for i in 5:
		var ph := fmod(t * 0.45 + i * 0.2, 1.0) if motion() else i * 0.2
		var p := top + Vector2(sin(ph * 5.0 + i) * 2.0 + ph * 5.0, -ph * 26.0)
		var r := 1.0 + ph * 3.0
		var a := 0.6 * (1.0 - ph)
		_px(p - Vector2(r, r * 0.8), r * 2.0, r * 1.6, Color(PLASTER[2], a))
		_px(p - Vector2(r - 1.0, r * 0.8), maxf(1.0, r * 2.0 - 2.0), 1, Color(PLASTER[5], a))
	if int(st.get("new", 0)) > 0:
		# The wisp: a small curl of jade light over the lid.
		for k in 8:
			var a2 := t * 3.0 + k * 0.7 if motion() else k * 0.7
			var q := top + Vector2(cos(a2) * (5.0 - k * 0.5), -10.0 - k * 1.6 + sin(a2) * 1.5)
			_px(q, 1, 1, Color(JADE[2].lerp(JADE[3], k / 8.0), 0.95))

# ------------------------------------------------------------------ a ripe bed's glints
func _bed_glints() -> void:
	if not bool(st.get("on", false)): return
	for i in 3:
		var ph := fmod(t * 0.6 + i * 0.33, 1.0) if motion() else i * 0.33
		var p := Vector2(-9.0 + i * 9.0, -8.0 - ph * 14.0)
		var a := sin(ph * PI)
		_px(p, 1, 1, Color(GOLD[4], a))
		_px(p + Vector2(-1, 0), 3, 1, Color(GOLD[3], a * 0.5))
		_px(p + Vector2(0, -1), 1, 3, Color(GOLD[3], a * 0.5))

# ------------------------------------------------------------------ the Storehouse's shed
## A lean-to storehouse of dark timber on the footprint (three cells by two): a roof of grey glazed tile over an open
## front, its courses lapping, its ribs lit on the west, its corners and ridge ends swept up and tipped in gold; inside, a
## back wall of boards and a shelf of jars. Sacks stand in it by how much the storehouse holds (none; one, two, then a
## third on the shelf as it fills), a crate once anything is stored. A name board hangs from the beam. The storehouse
## chest stands in front of it, so the sacks stand at its sides, clear of the chest.
func _shed(f: Vector2) -> void:
	var hw := float(size_cells.x * 16) * 0.5
	var held := int(st.get("n", 0))
	var sacks := 0 if held <= 0 else (1 if held <= 6 else (2 if held <= 16 else 3))
	# The floor shadow to the south-east.
	_px(f + Vector2(-hw + 3, 0), hw * 2.0, 2, SHADOW)
	_px(f + Vector2(hw, -34), 3, 34, SHADOW)
	# The back wall seen through the open front: dark boards, a lit seam every 5 px; the earth floor.
	_px(f + Vector2(-hw + 2, -36), hw * 2.0 - 4.0, 34, DARK[1])
	for x in range(int(-hw) + 4, int(hw) - 3, 5): _px(f + Vector2(x, -36), 1, 34, DARK[2])
	_px(f + Vector2(-hw + 2, -36), hw * 2.0 - 4.0, 3, Color(INK, 0.45))   # the eave's shade inside
	_px(f + Vector2(-hw + 2, -3), hw * 2.0 - 4.0, 3, EARTH[2])
	_px(f + Vector2(-hw + 2, -3), hw * 2.0 - 4.0, 1, EARTH[1])
	# The shelf across the back, lit on its top, with its jars and (once anything is stored) a crate.
	_px(f + Vector2(-hw + 3, -22), hw * 2.0 - 6.0, 2, WOOD[3])
	_px(f + Vector2(-hw + 3, -22), hw * 2.0 - 6.0, 1, WOOD[5])
	_px(f + Vector2(-hw + 3, -20), hw * 2.0 - 6.0, 1, WOOD[1])
	for x in [-hw + 5, -hw + 10]:
		_px(f + Vector2(x, -29), 4, 7, EARTH[4])
		_px(f + Vector2(x, -29), 1, 7, EARTH[5])
		_px(f + Vector2(x + 1, -30), 2, 1, EARTH[2])
		if x > -hw + 6: _px(f + Vector2(x + 1, -30), 2, 1, RED[2])
	if held > 0:
		_px(f + Vector2(hw - 11, -29), 7, 7, WOOD[4])
		_px(f + Vector2(hw - 11, -29), 7, 1, WOOD[6])
		_px(f + Vector2(hw - 11, -26), 7, 1, WOOD[2])
		_px(f + Vector2(hw - 5, -29), 1, 7, WOOD[2])
	# The sacks: on the floor at the west and the east side, then one on the shelf.
	var spots := [Vector2(-hw + 3, -2), Vector2(hw - 11, -2), Vector2(-4, -22)]
	for k in sacks: _sack(f + spots[k], k)
	# The two front posts and the beam under the eave.
	for x in [-hw + 1, hw - 4]:
		_px(f + Vector2(x, -38), 3, 38, WOOD[2])
		_px(f + Vector2(x, -38), 1, 38, WOOD[4])
		_px(f + Vector2(x + 2, -38), 1, 38, LINE)
	_px(f + Vector2(-hw, -40), hw * 2.0, 3, WOOD[2])
	_px(f + Vector2(-hw, -40), hw * 2.0, 1, WOOD[4])
	_px(f + Vector2(-hw, -38), hw * 2.0, 1, WOOD[1])
	# The roof: the plane from the eave up to the ridge, courses lapping every 6 px (a lit lip over a shadow line), cover
	# ribs every 4 px lit on the west; round tile ends along the eave; the far strip beyond the ridge a step lighter.
	var eave := -40.0
	var ridge := -66.0
	_px(f + Vector2(-hw - 3, ridge), hw * 2.0 + 6.0, eave - ridge, ROOF[2])
	for x in range(int(-hw) - 3, int(hw) + 3, 4):
		_px(f + Vector2(x, ridge + 1), 1, eave - ridge - 1, ROOF[4])
		_px(f + Vector2(x + 1, ridge + 1), 1, eave - ridge - 1, ROOF[3])
		_px(f + Vector2(x + 3, ridge + 1), 1, eave - ridge - 1, ROOF[1])
	for y in range(int(ridge) + 6, int(eave), 6):
		_px(f + Vector2(-hw - 3, y), hw * 2.0 + 6.0, 1, ROOF[0])
		_px(f + Vector2(-hw - 3, y - 1), hw * 2.0 + 6.0, 1, ROOF[5])
	_px(f + Vector2(-hw - 2, ridge - 3), hw * 2.0 + 4.0, 3, ROOF[4])
	_px(f + Vector2(-hw - 2, ridge - 3), hw * 2.0 + 4.0, 1, ROOF[6])
	# The ridge and its curled, gold-tipped ends; the eave's corners swept up.
	_px(f + Vector2(-hw - 4, ridge - 1), hw * 2.0 + 8.0, 3, ROOF[1])
	_px(f + Vector2(-hw - 4, ridge - 1), hw * 2.0 + 8.0, 1, ROOF[5])
	for s in [-1.0, 1.0]:
		var ex: float = (hw + 5.0) * s
		_px(f + Vector2(ex - 1.0, ridge - 4), 2, 3, ROOF[2])
		_px(f + Vector2(ex - 1.0, ridge - 5), 2, 1, GOLD[2])
		_px(f + Vector2((hw + 3.0) * s - 1.0, eave - 3), 2, 3, ROOF[3])
		_px(f + Vector2((hw + 3.0) * s - 1.0, eave - 4), 2, 1, ROOF[5])
	for x in range(int(-hw) - 2, int(hw) + 3, 4):
		_px(f + Vector2(x, eave - 1), 3, 2, ROOF[4])
		_px(f + Vector2(x, eave - 1), 1, 1, ROOF[6])
	_px(f + Vector2(-hw - 2, eave + 1), hw * 2.0 + 4.0, 1, Color(SHADOW, 0.8))
	# The name board hung from the beam: ink strokes on paper, a red seal.
	_px(f + Vector2(-7, -38), 14, 7, INK)
	_px(f + Vector2(-6, -37), 12, 5, PLASTER[4])
	_px(f + Vector2(-6, -33), 12, 1, PLASTER[2])
	_px(f + Vector2(-4, -36), 1, 3, INK)
	_px(f + Vector2(-2, -36), 2, 1, INK)
	_px(f + Vector2(-1, -35), 1, 2, INK)
	_px(f + Vector2(2, -36), 1, 3, INK)
	_px(f + Vector2(3, -35), 1, 1, INK)
	_px(f + Vector2(4, -34), 1, 1, RED[3])

func _sack(p: Vector2, k: int) -> void:
	var col: Color = [EARTH[5], PLASTER[2], EARTH[4]][k % 3]
	_px(p + Vector2(0, -9), 8, 9, col)
	_px(p + Vector2(0, -9), 2, 9, col.lightened(0.15))
	_px(p + Vector2(6, -9), 2, 9, col.darkened(0.25))
	_px(p + Vector2(0, -1), 8, 1, col.darkened(0.35))
	_px(p + Vector2(2, -11), 4, 2, col.darkened(0.1))
	_px(p + Vector2(2, -10), 4, 1, WOOD[1])   # the tie
	if k == 0: _px(p + Vector2(3, -6), 2, 2, RED[3])   # a red seal on the rice sack

# ------------------------------------------------------------------ a stall
## The front of a stall: a counter of dark wood across its cells, lit on its top, with the keeper's wares set out on it
## (jars, a bolt of cloth, a basket, bowls), a cloth valance in the shop's colour along its front.
func _stall_front(f: Vector2) -> void:
	var hw := float(size_cells.x * 16) * 0.5
	var cloth: Array = CLOTH.get(_shop(), CLOTH.stoneford_general)
	_px(f + Vector2(-hw + 3, 0), hw * 2.0, 2, SHADOW)
	_px(f + Vector2(hw, -14), 3, 14, SHADOW)
	# The counter: its front face 16 px high (waist high on a keeper), its top a floor 16 px up across the cell's depth,
	# so the keeper standing behind it shows from the waist.
	_px(f + Vector2(-hw, -16), hw * 2.0, 16, WOOD[2])
	for x in range(int(-hw) + 3, int(hw), 6): _px(f + Vector2(x, -16), 1, 16, WOOD[1])
	_px(f + Vector2(-hw, -1), hw * 2.0, 1, WOOD[0])
	_px(f + Vector2(-hw, -16), 1, 16, WOOD[4])
	_px(f + Vector2(hw - 1, -16), 1, 16, LINE)
	_px(f + Vector2(-hw, -30), hw * 2.0, 14, WOOD[4])
	for x in range(int(-hw) + 5, int(hw), 8): _px(f + Vector2(x, -30), 1, 14, WOOD[3])
	_px(f + Vector2(-hw, -30), hw * 2.0, 1, WOOD[6])
	_px(f + Vector2(-hw, -17), hw * 2.0, 1, WOOD[5])
	# The valance: scalloped cloth hung along the counter's lip.
	for x in range(int(-hw), int(hw), 6):
		_px(f + Vector2(x, -16), 6, 4, cloth[1])
		_px(f + Vector2(x, -16), 6, 1, cloth[2])
		_px(f + Vector2(x + 1, -12), 4, 1, cloth[0])
	# The wares on the top, left to right, standing on its middle.
	var x0 := -hw + 3.0
	var top := -21.0
	_jar(f + Vector2(x0, top), EARTH[4])
	_jar(f + Vector2(x0 + 6, top - 2), EARTH[3])
	# a bolt of cloth
	_px(f + Vector2(x0 + 12, top - 4), 9, 4, cloth[1])
	_px(f + Vector2(x0 + 12, top - 4), 9, 1, cloth[2])
	_px(f + Vector2(x0 + 20, top - 4), 1, 4, cloth[0])
	# a basket of buns
	_px(f + Vector2(x0 + 24, top - 3), 8, 3, REED[2])
	_px(f + Vector2(x0 + 24, top - 3), 8, 1, REED[4])
	for k in 3: _px(f + Vector2(x0 + 25 + k * 2, top - 5), 2, 2, PLASTER[5] if k % 2 == 0 else PLASTER[4])
	# a stack of bowls
	for k in 3:
		_px(f + Vector2(x0 + 35, top - 2 - k * 2), 6, 2, PLASTER[3] if k % 2 else PLASTER[4])
		_px(f + Vector2(x0 + 35, top - 2 - k * 2), 6, 1, JADE[1] if k == 2 else PLASTER[5])
	# a price slip on a stick
	_px(f + Vector2(hw - 3, top - 10), 1, 8, DARK[3])
	_px(f + Vector2(hw - 5, top - 14), 5, 4, PLASTER[4])
	_px(f + Vector2(hw - 4, top - 13), 3, 1, RED[3])

func _jar(p: Vector2, col: Color) -> void:
	_px(p + Vector2(0, -4), 5, 5, col)
	_px(p + Vector2(0, -4), 1, 5, col.lightened(0.2))
	_px(p + Vector2(1, -6), 3, 2, col.darkened(0.2))
	_px(p + Vector2(1, -6), 3, 1, RED[2])

## The back of a stall, behind its keeper: two poles and an awning of striped cloth in the shop's colour, its edge
## scalloped and stirring, and a rack of goods hung under it.
func _stall_back(f: Vector2) -> void:
	var hw := float(size_cells.x * 16) * 0.5
	var cloth: Array = CLOTH.get(_shop(), CLOTH.stoneford_general)
	for x in [-hw + 1, hw - 3]:
		_px(f + Vector2(x, -46), 2, 46, DARK[2])
		_px(f + Vector2(x, -46), 1, 46, DARK[4])
		_px(f + Vector2(x - 1, -1), 4, 1, Color(SHADOW, 0.8))
	# The rack between the poles: a bar with bundles and a gourd hung from it.
	_px(f + Vector2(-hw + 2, -34), hw * 2.0 - 4.0, 1, DARK[3])
	for k in 5:
		var x := -hw + 6.0 + k * 8.0
		_px(f + Vector2(x, -33), 1, 3, DARK[2])
		_px(f + Vector2(x - 1, -30), 4, 5, [REED[3], EARTH[4], cloth[1], REED[2], EARTH[5]][k])
	# The awning: stripes across it, lit at its front edge, scalloped.
	var stir := roundf(sin(t * 1.7)) if motion() else 0.0
	for y in range(-58, -46):
		for x in range(int(-hw) - 3, int(hw) + 3):
			var stripe := int(floor((x + hw + 3.0) / 6.0)) % 2 == 0
			_px(f + Vector2(x, y), 1, 1, (cloth[1] if stripe else PLASTER[4]).darkened(0.12 * float(y + 58) / 12.0))
	_px(f + Vector2(-hw - 3, -58), hw * 2.0 + 6.0, 1, cloth[2])
	for x in range(int(-hw) - 3, int(hw) + 3, 6):
		var stripe2 := int(floor((x + hw + 3.0) / 6.0)) % 2 == 0
		_px(f + Vector2(x + 1, -46), 4, 2 + (stir if x % 12 == 0 else 0.0), cloth[0] if stripe2 else PLASTER[2])
	_px(f + Vector2(-hw - 3, -45), hw * 2.0 + 6.0, 1, Color(SHADOW, 0.5))

func _shop() -> String:
	var n := ContentDB.entry("npcs", str(place.get("keeper", "")))
	for s in n.get("services", []):
		if str(s).begins_with("shop:"): return str(s).trim_prefix("shop:")
	return ""
