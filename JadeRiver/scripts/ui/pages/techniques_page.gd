extends Page
## Techniques (P13b; docs/page_identity.md row 15, the way family; mockups 06_techniques_tree, 06_techniques_tree_learned
## and 06_techniques_lost_unknown; roadmap decisions 11, 12, 18 and 19; docs/technique_plan.md §4.10). The whole screen:
## a lacquer rail of element seals across the top (one tab a tree, then Lost Arts and Secret Arts), three carved jade-teal
## panels between (the chooser, the tree, the reading) and the loadout dock across the foot. A tree tab is one huge tree
## of the element, every family side by side on the element's own chart: dragged to pan, the chooser jumps to a family,
## Learned jumps from one learned art to the next; only what is in view is drawn. The reading shows the chosen node:
## its picture (the character in the art's pose), what it does, its prerequisites ticked and crossed, and Learn naming
## the Realisations it spends; a learned art its mastery, its slot, Rank Up and Let go. Lost Arts is an album, one leaf
## an art: a found art pasted in (a manual not yet read has Read), every other leaf sealed alike and only counted
## (decision 19). The dock holds Ring I and II, the Inner Arts and the stance; a tap on an Inner Art or the stance opens
## the drawer of known Inner Arts and stances in the reading. The page reads the Progression authority's views
## (tree_tabs, tree_node, tree_dao_arts, node_needs, lost_arts_view, lost_unread) and submits intents only. Under the chooser the
## character casts the chosen art at a pack of foes (TechniquePreview); each card's picture is the character doing the
## art on its element's ground, the art's emblem in its corner.
##
## Decision 42 (the tree "feels a bit laggy"): the page is drawn only when something on it changes (Page.redraw_on_change),
## never every frame for nothing, and the chart is drawn apart from it, behind it: in tiles of the chart's own space (half
## a family's column, two rings deep, TILE), each in three layers (the ground and the routes, the passages and gates, the
## cards), drawn once and kept. A drag or a glide only moves the sheets that hold them; a tile is drawn as it comes near
## the view (a few a frame), and again only when what it shows changes (a node chosen or learned; a card's picture is
## painted into its place with no draw again, TechniquePicture). The cards' words (each written only while wholly inside
## the chart) and the ring numerals at the chart's edge are layers of their own, drawn again only when what they write
## changes. The trees' shapes are laid out a family at a time in the frames the page stands idle (ShapeJob), so a tab
## opens on a shape already made. A top-down character is drawn as the top-down game draws it (decision 42): the cards'
## and the reading's pictures (TechniquePicture, the look the HUD's buttons and the loadout bar share) and the preview's
## caster (TopdownDoll); the side view's avatar only for a classic side-view character.

const LEFT := Rect2(12, 70, 216, 580)
const MID := Rect2(236, 70, 660, 580)
const RIGHT := Rect2(904, 70, 364, 580)
const CHART := Rect2(241, 75, 650, 570)     # the tree's window on its chart
const VIS := CHART                         # where a card's words may be written
const HEAD := 31.0                          # the plaque's depth over the chart: a family's first row starts under it
const DOCK := Rect2(0, 656, 1280, 64)
var rail_tone := UiKit.SURFACE.cloth.lerp(UiKit.SURFACE.space, 0.6)   # the lacquer rail at its lightest
const FAM_W := 600.0                        # a family's column: three lanes 200 apart
const LANE := 200.0
const ROW_H := 139.0                        # a ring's row
const NOTE_H := 80.0                        # the notables' band after an act's last ring
const GATE_TOP := 24.0                      # the gate row (the Dao arts) at the chart's top
const CARD := Vector2(190, 115)
const PIC := 76.0
const STAGE := Rect2(16, 466, 208, 180)     # the preview under the chooser, inside the chooser's panel
const ROMAN := ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
const KINDS := {"technique": "ui.techniques.kind_technique", "inner": "ui.techniques.kind_inner", "secret": "ui.techniques.kind_secret"}

static var last_tab := ""     # the page opens on the tab of the art last chosen
var sel := ""                 # the chosen node, art, lost art or secret art
var view := Vector2.ZERO      # the chart's offset in view
var goal := Vector2.ZERO      # where the view is gliding to
var lost_act := 1             # the Lost Arts leaf shown (0: the lineages)
var drawer := false           # the reading shows the Inner Arts and stances
var picked_art := ""          # an Inner Art chosen to wear: tap a slot
var stage: TechniquePreview  # under the chooser: the character casting the chosen art at a pack of imps
var pic: Node2D               # the character in the chosen art's pose
var _laid := ""               # the tree laid out in _items
var _rz := {}                 # the Realisations pool: {total, spent, free}
var _realised_here := 0       # nodes realised on this tree
var _items: Array = []        # the tree laid out: [{id, kind, at, state, ...}]
var _by := {}                 # id -> item
var _trees := {}              # tree -> its laid-out copies {of, items, by}, kept while the page is open
var _size := Vector2.ZERO     # the chart's size
var _rows := {}               # ring -> row top; "n<act>" -> the notables' band
var _dirty := true
var _pan := false
var _learned_i := -1
var _fam := {}                # the weapon family in hand (StatRules.family), found once a dressing
var _pic_gen := -1            # TechniquePicture.generation the tiles were drawn in (a sheet started again: draw them again)
var top := false              # the character is a top-down one: its pictures are the top-down figure (decision 42)
## The chart apart from the page (decision 42): the page's ground behind everything, the chart's clip over MID and its
## three sheets of tiles, and the ring numerals' strip.
const TILE := Vector2(300, 278)          # a tile: half a family's column (FAM_W), two rings deep
const TILE_AHEAD := Vector2(300, 278)    # tiles this far out of view are drawn ahead of a drag, one a frame
const PIC_K := 3                         # the reading's top-down figure, screen px an art px
var _back: Control                       # the page's ground, drawn behind the page and the chart
var _clip: Control                       # the chart's window (MID), clipping its sheets
var _sheets: Array = []                  # the routes, the marks and the cards: each holds every tile's layer
var _rings: Layer                        # the ring numerals down the chart's right edge
var _tiles := {}                         # Vector2i -> {rect, bounds, items, gates, nodes: [3 Layers or null], dirty: [3 bools]}
var _regions_view := Vector2(-1, -1)     # the view the chart's tap regions were laid for
var _labels_key := ""                    # what the page's words over the chart say (the family and rings in view)
var _rings_y := -1.0
var _tend_view := Vector2(-1, -1)        # the view the tiles were last tended for
var layer_draws := 0                     ## the layers drawn apart from the page so far, and of them the tiles' (perf_tests)
var tile_draws := 0
var _warm_i := 0                         # the nodes asked ahead so far (_warm_states), in _warm_order
var _warm_order: Array = []
var _tiles_stale := true                 # some tile waits to be drawn (again)
var _labels_layer: Layer                 # the family in view on its plaque and the act's rings, over the chart
var _here := ""                          # the family the chooser lights (the one in view once the view is at rest)
var _words_layer: Layer                  # the cards' names and tags, in the chart's space, over the cards
var _words: Array = []                   # what it writes: [node, name?, tag?] (_words_in_view)
var _words_key := ""
var _words_view := Vector2(-1, -1)

func _init() -> void:
	title = Tx.t("ui.techniques.techniques")
	frame_rect = WINDOW_SCREEN
	identity = Identity.new("space", false, "own", "seal_rail_chart_three_panels_dock", 0.3)
	redraw_on_change = true
	dims_world = false   # the ground (_back) covers the screen, under the chart

func content_rect() -> Rect2:
	return Rect2(LEFT.position, RIGHT.end - LEFT.position)

func setup() -> void:
	var ch = c()
	tabs = []
	for tb in (Game.progression.tree_tabs(ch) if ch != null else []):
		var lv := int(TechniqueTreeRules.ring_row(TechniqueTreeRules.first_ring(str(tb.tree))).get("level", 0))
		tabs.append({"id": str(tb.tree), "label": str(tb.name), "locked": "" if bool(tb.open) else Tx.t("ui.techniques.tree_opens") % lv})
	tabs.append({"id": "lost", "label": Tx.t("ui.techniques.lost_arts")})
	tabs.append({"id": "secret", "label": Tx.t("ui.techniques.secret_arts")})
	_layers()
	if pic == null or top != Figures.top_down(ch):
		if pic != null: pic.queue_free()
		top = Figures.top_down(ch)
		pic = Figures.for_view(top)
		pic.externally_timed = not top   # the side view's avatar is posed by the page (_pose_pic), the doll plays
		pic.visible = false
		add_child(pic)
	_dress()
	var want := _first_tab(ch)
	for i in tabs.size():
		if str(tabs[i].id) == want and str(tabs[i].get("locked", "")) == "": tab = i
	if args.has("tab"): last_tab = str(args.tab)

func _dress() -> void:
	if c() == null: return
	Figures.dress(pic, InventoryAuthority.outfit_for(c()))
	_fam = {}
	_stale_tiles()
	queue_redraw()
	if stage == null: return
	stage.dress(pic.outfit.duplicate(), top)
	stage.restart()

## The ground behind the page and the chart's window with its sheets and the rings' strip, made once.
func _layers() -> void:
	if _back != null: return
	_back = Control.new()
	_back.show_behind_parent = true
	_back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_back.size = Vector2(1280, 720)
	_back.draw.connect(_draw_back)
	add_child(_back)
	move_child(_back, 0)
	_clip = Control.new()
	_clip.show_behind_parent = true
	_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_clip.clip_contents = true
	_clip.position = MID.position
	_clip.size = MID.size
	add_child(_clip)
	move_child(_clip, 1)
	for k in 3:
		var sheet := Node2D.new()
		_clip.add_child(sheet)
		_sheets.append(sheet)
	_words_layer = Layer.new(self, "words")
	_clip.add_child(_words_layer)
	_rings = Layer.new(self, "rings")
	_clip.add_child(_rings)
	_labels_layer = Layer.new(self, "labels")
	add_child(_labels_layer)

## The live preview, built the frame after the page opens (its character, imps and effects layer are not needed for the
## page's first frame, which is all but transparent while the page fades in).
func _build_stage() -> void:
	stage = TechniquePreview.new()
	stage.position = STAGE.position
	stage.size = STAGE.size
	add_child(stage)
	_dress()

func on_event(name: String, _p: Dictionary) -> void:
	if name == "equipment_changed": _dress()
	for k in ["tree_", "technique_", "lost_", "dao", "realm", "item_", "inner_art", "stance", "level", "breakthrough"]:
		if name.begins_with(k): _dirty = true
	queue_redraw()

## One of the page's layers drawn apart from it (a chart tile's layer, the cards' words, the rings' strip, the labels over
## the chart): it asks the page to draw it.
class Layer extends Node2D:
	var page
	var kind := ""           ## "tile" (its `layer`: 0 the ground and routes, 1 the passages and gates, 2 the cards), "words", "rings" or "labels"
	var key := Vector2i.ZERO
	var layer := 0
	func _init(pg, k: String, tile := Vector2i.ZERO, which := 0) -> void:
		page = pg
		kind = k
		key = tile
		layer = which
	func _draw() -> void:
		page._draw_layer(self)

func _tab_id() -> String:
	return str(tabs[tab].id) if tab < tabs.size() else ""

func _is_tree() -> bool:
	return not _tab_id() in ["lost", "secret", ""]

# ------------------------------------------------------------------ input: the chart pans under a finger
## A pan moves the chart's sheets only (the page is not drawn again for it); a tap after one finds the cards where they
## are now (_sync_chart_regions).
func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_pan = event.pressed and _is_tree() and CHART.has_point(event.position) and confirm.is_empty()
	elif event is InputEventMouseButton and event.pressed and _is_tree() and CHART.has_point(event.position) and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		_glide(view + Vector2(0, -90.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 90.0), true)
		accept_event()
		return
	elif event is InputEventMouseMotion and _pan and event.button_mask & MOUSE_BUTTON_MASK_LEFT and (_dragged or (event.position - _press_pos).length() > 10.0):
		if not _dragged: queue_redraw()   # the card pressed is let go
		_dragged = true
		_pressed = -1
		_glide(view - event.relative, true)
		accept_event()
		return
	if event is InputEventMouseButton: _sync_chart_regions()
	super._gui_input(event)

## The page's first frame draws its frame, rail, chooser and the chart's tiles in view; the preview is built on the
## next, and the cards' pictures are begun from then on, a few a frame, and painted off the main thread
## (TechniquePicture). Each frame the chart's sheets follow the view, the tiles near it are drawn (_tend_tiles), the page
## is drawn again only when its words over the chart change, and an idle frame lays out a little of a tree not yet laid
## out (_warm_shapes). When the pictures' atlas starts a sheet again, the tiles and the page are drawn again.
func _process(delta: float) -> void:
	super._process(delta)
	if TechniquePicture.generation != _pic_gen:
		if _pic_gen >= 0:
			_stale_tiles()
			queue_redraw()
		_pic_gen = TechniquePicture.generation
	if stage == null and _open_frame >= 0 and Engine.get_process_frames() > _open_frame and c() != null: _build_stage()
	if c() == null: return
	if _dirty and _is_tree():
		_refresh()
		queue_redraw()
	if view != goal: view = goal if UiKit.reduce_motion() or view.distance_to(goal) < 1.0 else view.lerp(goal, minf(1.0, delta * 12.0))
	_clip.visible = _is_tree()
	_labels_layer.visible = _is_tree() and confirm.is_empty()
	if not _is_tree(): return
	_follow_view()
	var busy := _tend_tiles()
	if not busy and not _pan and view == goal and _open_frame >= 0 and Engine.get_process_frames() - _open_frame > 2:
		if not _warm_states(1500): _warm_shapes()

## The chart's sheets moved to the view (whole px), the rings' strip drawn again when the rows moved, the page when its
## words over the chart change, and the tap regions laid again once the view has come to rest.
func _follow_view() -> void:
	var at := (CHART.position - MID.position - view).round()
	for sheet in _sheets: sheet.position = at
	_words_layer.position = at
	if _open_frame >= 0 and (view != _words_view or _words_key == ""):
		_words_view = view
		var words := _words_in_view()
		var key := "|" + ",".join(words.map(func(w): return "%s%d%d" % [str(w[0].id), int(w[1]), int(w[2])]))
		if key != _words_key:
			_words_key = key
			_words = words
			_words_layer.queue_redraw()
	if view.y != _rings_y:
		_rings_y = view.y
		_rings.queue_redraw()
	if _labels() != _labels_key:
		_labels_key = _labels()
		_labels_layer.queue_redraw()
	if view == goal and not _pan:
		if _here != _fam_at_view(): queue_redraw()   # the chooser lights the family the view came to rest on
		if _regions_view != view: _sync_chart_regions()

## What the page writes over the chart for this view: the family in view (the plaque, the chooser's lit row) and the
## rings in view (the act's line).
func _labels() -> String:
	var r := _rings_in_view()
	return "%s|%s|%d|%d" % [_tab_id(), _fam_at_view(), r.x, r.y]

## The first and last ring whose row is in view (lo > hi when none).
func _rings_in_view() -> Vector2i:
	var lo := 99
	var hi := 0
	for key in _rows:
		if str(key).begins_with("n"): continue
		var y := float(_rows[key]) - view.y + CHART.position.y
		if y + 60 < VIS.position.y + HEAD or y > VIS.end.y - 20: continue
		lo = mini(lo, int(key))
		hi = maxi(hi, int(key))
	return Vector2i(lo, hi)

## Move the view (clamped to the chart); `now` skips the glide (a drag).
func _glide(to: Vector2, now := false) -> void:
	goal = Vector2(clampf(to.x, 0.0, maxf(0.0, _size.x - CHART.size.x)), clampf(to.y, 0.0, maxf(0.0, _size.y - CHART.size.y)))
	if now: view = goal

## Centre the view on a family's column, at the rows around `ring` (its first by default).
func _jump(fam_i: int, y := -1.0, now := false) -> void:
	var at_y: float = y if y >= 0.0 else float(_rows.get(TechniqueTreeRules.first_ring(_tab_id()), 0.0)) - HEAD
	_glide(Vector2(fam_i * FAM_W + FAM_W * 0.5 - CHART.size.x * 0.5, at_y), now)

# ------------------------------------------------------------------ the tree laid out
## The tree of this tab laid out once (its shape does not change): each family a column of three lanes (the orthodox
## art on the passage line, the path art beside it, alternating side by ring, the kin group's keystone at an act's last
## ring on its first family's right), the Dao arts at the gate, a notable under each act's last ring; each node's route
## in and the box it and its route fill. What the character has made of it (each node's state, what learning it takes)
## is asked of the Progression authority node by node as a node comes into view (_state), and forgotten when something
## changes.
func _refresh() -> void:
	_dirty = false
	var ch = c()
	var tree := _tab_id()
	if ch == null or not _is_tree(): return
	if _laid != tree: _lay_out(ch, tree)
	for it in _items:
		if str(it.kind) != "dao": it.erase("state")
	_warm_i = 0
	for d in Game.progression.tree_dao_arts(ch, tree): _by[str(d.id)].state = str(d.state)
	_rz = Game.progression.realisations(ch)
	_realised_here = 0
	for tb in Game.progression.tree_tabs(ch):
		if str(tb.tree) == tree: _realised_here = int(tb.realised)
	_stale_tiles()

## The tab's tree on this page: its shape (_shape, laid out once a run and kept across opens) copied node by node so
## what this page learns of each node stays its own, then the character's Dao arts at the gate.
func _lay_out(ch, tree: String) -> void:
	_laid = tree
	var shape := _shape(tree)
	_rows = shape.rows
	_size = shape.size
	var kept: Dictionary = _trees.get(tree, {})
	if not kept.is_empty() and is_same(kept.of, shape):   # a tab shown before on this page: its copies again
		_items = kept.items
		_by = kept.by
	else:
		_items = []
		_by = {}
		for it0 in shape.items:
			var it: Dictionary = (it0 as Dictionary).duplicate()
			_items.append(it)
			_by[str(it.id)] = it
		var taken: Dictionary = (shape.taken as Dictionary).duplicate()
		for d in Game.progression.tree_dao_arts(ch, tree):
			var it2 := {"id": str(d.id), "kind": "dao", "family": str(d.family), "dao": str(d.dao), "dao_tier": int(d.tier), "ring": 0, "state": str(d.state)}
			_place(it2, it2.family, 0, [-1, 1, 0], taken, _rows)
			_route_box(it2, tree, _by, _rows)
			_items.append(it2)
			_by[str(it2.id)] = it2
		_trees[tree] = {"of": shape, "items": _items, "by": _by}
	if goal == Vector2.ZERO and view == Vector2.ZERO: _jump(0, -1.0, true)
	_cut_tiles()
	if _back != null: _back.queue_redraw()   # the chart's glow takes the tree's element

## The shape of the tab the page would open on, built ahead (main.gd calls this as the world mounts and as a room is
## entered, under their fades), so the page's first opening does not build it.
static func warm(ch) -> void:
	if ch == null: return
	var want := _first_tab(ch)
	if want in TechniqueTreeRules.trees(): _shape(want)

## The tab the page opens on: the art last chosen's, else the tree of the first slotted art's element (Water without one).
static func _first_tab(ch) -> String:
	if last_tab != "" or ch == null: return last_tab
	var first = ch.cultivator.technique_slots[0] if not ch.cultivator.technique_slots.is_empty() else null
	return TechniqueTreeRules.tree_of_element(str(ContentDB.entry("techniques", str(first)).get("element", "none"))) if first != null else "water"

## A tree's shape, the same for every character: {items, rows, size, taken}, laid out the first time a page shows the
## tree and kept (a new techniques list, after a reload, lays it out again). Its items are never written: a page works
## on its own copies.
static var _shapes := {}

static var _jobs := {}          # tree -> the ShapeJob laying it out, a family at a time

static func _shape(tree: String) -> Dictionary:
	var list: Array = ContentDB.all("techniques")
	var open_act := int(TechniqueTreeRules.config().get("act_open", 3))
	if _shapes.has(tree) and is_same(_shapes[tree].of, list) and int(_shapes[tree].act) == open_act: return _shapes[tree]
	var job: ShapeJob = _jobs.get(tree)
	if job == null or not is_same(job.list, list) or job.open_act != open_act: job = ShapeJob.new(tree, list, open_act)
	while not job.step(-1): pass
	_jobs.erase(tree)
	_shapes[tree] = job.result()
	return _shapes[tree]

## What the character has made of the tree's nodes, asked of the authority a few at a time (within `budget_us`) in the
## frames the page stands idle, nearest the view first, so a drag finds the nodes it brings into view already asked
## (a node's state costs the authority a learning plan). False once every node is asked.
func _warm_states(budget_us: int) -> bool:
	if _warm_i >= _items.size(): return false
	var t0 := Time.get_ticks_usec()
	if _warm_i == 0:   # nearest the view first
		var mid := view + CHART.size * 0.5
		var keyed: Array = []
		for i in _items.size(): keyed.append([(_items[i].at as Vector2).distance_squared_to(mid), i])
		keyed.sort()
		_warm_order = keyed.map(func(k): return k[1])
	while _warm_i < _items.size() and Time.get_ticks_usec() - t0 < budget_us:
		_state(_items[_warm_order[_warm_i]])
		_warm_i += 1
	return true

## A little of a tree not yet laid out, in a frame the page stands idle (within 2 ms), so a tab opens on its shape made.
func _warm_shapes() -> void:
	var list: Array = ContentDB.all("techniques")
	var open_act := int(TechniqueTreeRules.config().get("act_open", 3))
	for tree in TechniqueTreeRules.trees():
		if _shapes.has(tree) and is_same(_shapes[tree].of, list) and int(_shapes[tree].act) == open_act: continue
		var job: ShapeJob = _jobs.get(tree)
		if job == null or not is_same(job.list, list) or job.open_act != open_act:
			job = ShapeJob.new(tree, list, open_act)
			_jobs[tree] = job
		if job.step(2000):
			_jobs.erase(tree)
			_shapes[tree] = job.result()
		return

static func _col(fam: String) -> float:
	return ShapeJob._col(fam)

static func _place(it: Dictionary, fam: String, ring: int, lanes: Array, taken: Dictionary, rows: Dictionary) -> void:
	ShapeJob._place(it, fam, ring, lanes, taken, rows)

static func _route_box(it: Dictionary, tree: String, by: Dictionary, rows: Dictionary) -> void:
	ShapeJob._route_box(it, tree, by, rows)

## A tree's shape laid out in steps (_shape runs it through at once; an idle frame runs a step of it): the rows and the
## keystones first, then a family a step, then each node's route and box.
class ShapeJob:
	var tree := ""
	var list: Array = []
	var open_act := 3
	var fams: Array = []
	var rows := {}
	var items: Array = []
	var by := {}
	var taken := {}
	var y := 0.0
	var fi := 0          # the next family to lay out
	var ri := 0          # the next node to route

	func _init(t: String, of: Array, act: int) -> void:
		tree = t
		list = of
		open_act = act
		var T = TechniqueTreeRules
		fams = T.sectors()
		y = GATE_TOP + ROW_H + 16.0
		for r in range(T.first_ring(tree), T.edge_ring(open_act) + 1):
			rows[r] = y
			y += ROW_H
			if T.is_edge(r):
				rows["n%d" % T.act_of(r)] = y
				y += NOTE_H
		# The open acts' nodes from the cells themselves, keystones first so they take their lane before the arts.
		for a in range(1, open_act + 1):
			for kin in ["voice", "edges", "reach", "distance"]:
				var k: String = T.keystone_at(tree, kin, a)
				if k == "" or not rows.has(T.edge_ring(a)): continue
				var kit := {"id": k, "kind": "keystone", "kin": kin, "family": str(T.kin_sectors(kin)[0]), "ring": T.edge_ring(a)}
				_place(kit, kit.family, kit.ring, [1, -1, 0], taken, rows)
				_add(kit)

	func _add(it: Dictionary) -> void:
		items.append(it)
		by[str(it.id)] = it

	## One step within `budget_us` (-1: to the end); true once the shape is whole.
	func step(budget_us: int) -> bool:
		var T = TechniqueTreeRules
		var t0 := Time.get_ticks_usec()
		while fi < fams.size():
			var f := str(fams[fi])
			fi += 1
			for ring in rows:
				if str(ring).begins_with("n"): continue
				_add({"id": T.passage(tree, f, ring), "kind": "passage", "family": f, "ring": ring, "at": Vector2(_col(f), float(rows[ring]) - 9.0)})
				var cl: Dictionary = T.cell(tree, f, ring)
				var side := -1 if int(ring) % 2 == 0 else 1
				for slot in ["o", "p"]:
					for id in cl[slot]:
						var it := {"id": str(id), "kind": "art", "family": f, "ring": ring}
						_place(it, f, ring, [0, side, -side] if slot == "o" else [side, -side, 0], taken, rows)
						_add(it)
				if T.is_edge(ring):
					_add({"id": T.notable(tree, f, T.act_of(ring)), "kind": "notable", "family": f, "ring": ring, "at": Vector2(_col(f), float(rows["n%d" % T.act_of(ring)]) + 32.0)})
			if budget_us >= 0 and Time.get_ticks_usec() - t0 >= budget_us: return false
		while ri < items.size():
			_route_box(items[ri], tree, by, rows)
			ri += 1
			if budget_us >= 0 and ri % 24 == 0 and Time.get_ticks_usec() - t0 >= budget_us: return false
		return true

	func result() -> Dictionary:
		return {"of": list, "act": open_act, "items": items, "rows": rows, "size": Vector2(fams.size() * FAM_W, y + 24.0), "taken": taken}

	## A family's column centre on the chart.
	static func _col(fam: String) -> float:
		return TechniqueTreeRules.sectors().find(fam) * FAM_W + FAM_W * 0.5

	## A node into the first free lane of its family's ring (else two lanes out).
	static func _place(it: Dictionary, fam: String, ring: int, lanes: Array, taken: Dictionary, rows: Dictionary) -> void:
		for ln in lanes:
			if taken.has("%s|%d|%d" % [fam, ring, ln]): continue
			taken["%s|%d|%d" % [fam, ring, ln]] = true
			it.at = Vector2(ShapeJob._col(fam) + ln * LANE, float(rows.get(ring, GATE_TOP)))
			break
		if not it.has("at"): it.at = Vector2(ShapeJob._col(fam) + 2.0 * LANE, float(rows.get(ring, GATE_TOP)))

	## A node's route in (from its passage, the ring before or the gate), the box it and its route fill, and a card's name.
	static func _route_box(it: Dictionary, tree: String, by: Dictionary, rows: Dictionary) -> void:
		var T = TechniqueTreeRules
		var fams: Array = T.sectors()
		var kind := str(it.kind)
		var pts: Array = []
		match kind:
			"passage":
				# In from the ring before (from under its act's notable after an act's last ring), or from the gate.
				var r := int(it.ring)
				var up := Vector2(it.at.x, GATE_TOP + 62.0)
				if rows.has(r - 1): up = by[T.notable(tree, str(it.family), T.act_of(r - 1)) if T.is_edge(r - 1) else T.passage(tree, str(it.family), r - 1)].at
				pts = [up, it.at]
			"notable":
				pts = [by[T.passage(tree, str(it.family), int(it.ring))].at, it.at]
				if fams.find(str(it.family)) + 1 < fams.size(): it.chan = true
			"dao": pts = [Vector2(it.at.x, it.at.y + PIC * 0.5), Vector2(ShapeJob._col(str(it.family)), it.at.y + PIC * 0.5)]
			_:
				var pa: Vector2 = by[T.passage(tree, str(it.family) if kind == "art" else str(T.kin_sectors(str(it.kin))[0]), int(it.ring))].at
				pts = [pa, Vector2(it.at.x, pa.y), it.at - Vector2(0, 3)]
		it.route = pts
		var box := Rect2(it.at, Vector2.ZERO)
		for pt in pts: box = box.expand(pt)
		if it.get("chan", false): box = box.expand(it.at + Vector2(FAM_W, 0))
		if not kind in ["passage", "notable"]:
			box = box.merge(Rect2(it.at - Vector2(CARD.x * 0.5, 0), CARD))
			it.name = str(ContentDB.entry("techniques", str(it.id)).get("name", it.id))
		it.box = box.grow(14)

## A node as the character stands to it, asked of the authority when it is first drawn after a change: its state, why
## it is closed, its cost and what learning it takes; with its tag and a learned art's tier.
func _state(it: Dictionary) -> Dictionary:
	if not it.has("state"): it.merge(Game.progression.tree_node(c(), str(it.id)), true)
	if not it.has("tag") or it.get("tag_of", "") != str(it.state) + str(it.get("why", "")):
		it.tag = _tag(it)
		it.tag_of = str(it.state) + str(it.get("why", ""))
	it.tier = int(c().cultivator.mastery.get(str(it.id), {}).get("tier", 1))
	return it

## The screen point of a chart point.
func _on_screen(p: Vector2) -> Vector2:
	return (CHART.position - view + p).round()

func _fam_at_view() -> String:
	var fams: Array = TechniqueTreeRules.sectors()
	return str(fams[clampi(int((view.x + CHART.size.x * 0.5) / FAM_W), 0, fams.size() - 1)]) if not fams.is_empty() else "any"

# ------------------------------------------------------------------ the surface: ground, chart, rail
## The ground (drawn behind the page by _back, under the chart: the ground itself, the glow round the tree's panel, the
## panel, the tree's element glow) is only named here for the words on it; on a tree tab the page writes over the chart
## (the family in view on its plaque, the act's rings, Learned and Let all go), lays the chart's tap regions, and closes
## the panel's frame over it; then the rail.
func draw_surface(r: Rect2) -> void:
	ground(r, UiKit.SURFACE.space)
	if text_log != null: text_log.append({"rect": MID, "s": "", "button": Rect2(), "ground": "carved_panel:normal"})
	if c() != null and _is_tree():
		if _dirty: _refresh()
		ground(CHART, UiKit.SURFACE.space)
		_chart_regions()
		if text_log != null: _log_chart()
		_chart_labels()
		face(MID, "carved_panel", "frame")
	_band(Rect2(0, 0, 1280, 64), rail_tone, UiKit.SURFACE.space)
	draw_line(Vector2(0, 64), Vector2(1280, 64), UiKit.GOLD, 1.0)
	draw_line(Vector2(0, 65.5), Vector2(1280, 65.5), UiKit.INK, 2.0)
	ground(Rect2(0, 0, 1280, 64), rail_tone)

## The page's ground behind the page and the chart: the screen, the glow round the tree's panel and the panel, and on a
## tree tab the tree's element glow.
func _draw_back() -> void:
	var r := frame_rect
	_back.draw_rect(r, UiKit.SURFACE.space)
	Page.glow_on(_back, Rect2(MID.position - Vector2(80, 40), MID.size + Vector2(160, 80)), Color(UiKit.JADE_SHADOW, 0.22))
	_back.draw_style_box(UiKit.style("carved_panel"), MID)
	if _is_tree():
		var ec := SpriteCache.element_color(str(TechniqueTreeRules.tree_def(_tab_id()).get("element", "none")))
		Page.glow_on(_back, Rect2(CHART.position + Vector2(-60, 40), CHART.size + Vector2(120, 80)), Color(ec, 0.07))

func _band(r: Rect2, top: Color, foot: Color) -> void:
	draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]), PackedColorArray([top, top, foot, foot]))

func title_rect() -> Rect2:
	return Rect2(8, 6, 196, 52)

func draw_title_mount(_r: Rect2) -> void:
	pass

func tab_rects() -> Array:
	var out: Array = []
	for i in tabs.size():
		var x := 214.0 + i * 62.0 if i < tabs.size() - 2 else 916.0 + (i - tabs.size() + 2) * 82.0
		out.append(Rect2(x, 2, 62 if i < tabs.size() - 2 else 78, 60))
	return out

## An element seal: its disc with the element's glyph, its name under it; the chosen one lit gold, a locked one dim.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	var c0 := Vector2(r.get_center().x, r.position.y + 22)
	if state == "selected":
		glow(Rect2(c0 - Vector2(34, 34), Vector2(68, 68)), Color(UiKit.PALE_GOLD, 0.35 if not UiKit.reduce_motion() else 0.1))
		draw_circle(c0, 24.0, UiKit.PALE_GOLD, false, 3.0, true)
	var seal := hd_tex("tech_seal", str(tabs[i].id))
	if seal: draw_texture_rect(seal, Rect2(c0 - Vector2(22, 22), Vector2(44, 44)), false, UiKit.HOLLOW if state == "disabled" else Color.WHITE)
	text(Vector2(r.position.x - 12, r.position.y + 57), str(tabs[i].label), 14, UiKit.PALE_GOLD if state == "selected" else (UiKit.HOLLOW if state == "disabled" else UiKit.MIST),
		HORIZONTAL_ALIGNMENT_CENTER, r.size.x + 24)

# ------------------------------------------------------------------ the chart, in tiles
## The tree's chart cut into tiles (TILE: two a family's column, two rings deep, so a tab's first frame draws about
## twice what is in view, not four times), each holding the nodes whose place falls in it, the gates on it, and what its
## nodes and their routes cover. Its three layers are made when it is first drawn.
func _cut_tiles() -> void:
	for key in _tiles:
		for n in _tiles[key].nodes:
			if n != null: n.queue_free()
	_tiles.clear()
	var nx := ceili(_size.x / TILE.x)
	var ny := ceili(_size.y / TILE.y)
	for tx in nx:
		for ty in ny:
			var rect := Rect2(Vector2(tx, ty) * TILE, TILE)
			_tiles[Vector2i(tx, ty)] = {"rect": rect, "bounds": rect, "items": [], "gates": [], "nodes": [null, null, null], "dirty": [true, true, true]}
	for it in _items:
		var key := Vector2i(clampi(floori(it.at.x / TILE.x), 0, nx - 1), clampi(floori(it.at.y / TILE.y), 0, ny - 1))
		var tile: Dictionary = _tiles[key]
		tile.items.append(it)
		tile.bounds = (tile.bounds as Rect2).merge(it.box)
	var fams: Array = TechniqueTreeRules.sectors()
	for i in fams.size():
		var g := Vector2(i * FAM_W + FAM_W * 0.5, GATE_TOP + 38.0)
		_tiles[Vector2i(clampi(floori(g.x / TILE.x), 0, nx - 1), clampi(floori(g.y / TILE.y), 0, ny - 1))].gates.append(i)
	_regions_view = Vector2(-1, -1)
	_tiles_stale = true

## Every tile drawn again (what the character has made of the tree changed), and the cards' words.
func _stale_tiles() -> void:
	for key in _tiles: _tiles[key].dirty = [true, true, true]
	_words_key = ""
	_tiles_stale = true

## The tiles holding node `id` drawn again (it was chosen, or no longer is): its passages and cards.
func _stale_node(id: String) -> void:
	if not _by.has(id): return
	var it: Dictionary = _by[id]
	for key in _tiles:
		if (_tiles[key].items as Array).has(it):
			_tiles[key].dirty[1] = true
			_tiles[key].dirty[2] = true
	_words_key = ""
	_tiles_stale = true

## The tiles the view needs, drawn a few a frame so no frame draws a whole screenful (a tab's first frames fill its chart
## in, nearest the view's middle first): up to TILES_A_FRAME stale tiles in view, then, once none waits, one of those
## just out of view (ahead of a drag); tiles farther out wait until they come near. True while a tile near the view
## still waits.
const TILES_A_FRAME := 4
func _tend_tiles() -> bool:
	if _open_frame < 0: return true   # the page's first frame is drawn alone; the chart from the next
	if view == _tend_view and not _tiles_stale: return false
	_tend_view = view
	_tiles_stale = false
	var vr := Rect2(view, CHART.size)
	var ahead := vr.grow_individual(TILE_AHEAD.x, TILE_AHEAD.y, TILE_AHEAD.x, TILE_AHEAD.y)
	var mid := vr.get_center()
	var now: Array = []     # [distance², key] of stale tiles in view
	var soon: Array = []    # of stale tiles just out of it
	for key in _tiles:
		var tile: Dictionary = _tiles[key]
		var bounds: Rect2 = tile.bounds
		# (A tile drawn stays shown: out of the chart's window the renderer leaves it out, and one hidden would be drawn
		# again as it is shown.)
		if not bounds.intersects(ahead) or not (tile.dirty as Array).has(true): continue
		(now if bounds.intersects(vr) else soon).append([(tile.rect as Rect2).get_center().distance_squared_to(mid), key])
	now.sort()
	soon.sort()
	var picked: Array = now.slice(0, TILES_A_FRAME)
	if now.is_empty(): picked = soon.slice(0, 1)
	for pk in picked:
		var key: Vector2i = pk[1]
		var tile: Dictionary = _tiles[key]
		for k in 3:
			if not tile.dirty[k]: continue
			if tile.nodes[k] == null:
				tile.nodes[k] = Layer.new(self, "tile", key, k)
				_sheets[k].add_child(tile.nodes[k])
			tile.dirty[k] = false
			tile.nodes[k].queue_redraw()
	var waiting := now.size() + soon.size() > picked.size()
	if waiting: _tiles_stale = true
	return waiting

## A layer drawn apart from the page: the rings' strip, the cards' words, or one of a tile's three layers.
func _draw_layer(cv: Layer) -> void:
	layer_draws += 1
	if cv.kind == "tile": tile_draws += 1
	if c() == null: return
	if cv.kind == "rings":
		_draw_rings(cv)
		return
	if cv.kind == "words":
		_draw_words(cv)
		return
	if cv.kind == "labels":
		_draw_labels(cv)
		return
	var tile: Dictionary = _tiles.get(cv.key, {})
	if tile.is_empty(): return
	var items: Array = tile.items
	for it in items: _state(it)
	match cv.layer:
		0: _draw_ground_routes(cv, tile)
		1:
			for it in items:
				if str(it.kind) == "passage": _diamond(cv, it.at, 7.0, it)
				elif str(it.kind) == "notable": _diamond(cv, it.at, 13.0, it)
			for i in tile.gates:
				var g := Vector2(int(i) * FAM_W + FAM_W * 0.5, GATE_TOP + 38.0)
				cv.draw_circle(g, 26.0, UiKit.INK, true, -1.0, true)
				cv.draw_circle(g, 24.0, UiKit.SURFACE.cloth, true, -1.0, true)
				cv.draw_circle(g, 24.0, UiKit.GOLD, false, 2.0, true)
				SpriteCache.draw_icon(cv, Rect2(g - Vector2(16, 16), Vector2(32, 32)), _fam_icon(str(TechniqueTreeRules.sectors()[int(i)])))
		2:
			for it in items:
				if not str(it.kind) in ["passage", "notable"]:
					if not _card(cv, it, Rect2(it.at - Vector2(CARD.x * 0.5, 0), CARD)):   # a picture waits its turn
						tile.dirty[2] = true
						_tiles_stale = true

## A tile's ground and routes: the element's chart (the Water tab a tide chart: currents down between the lanes and
## depth contours between the rings, in the chart's own space), then each node's route in, in the colour of the node it
## leads to, and the notables' channels.
func _draw_ground_routes(cv: Layer, tile: Dictionary) -> void:
	var rect: Rect2 = tile.rect
	var el := str(TechniqueTreeRules.tree_def(_tab_id()).get("element", "none"))
	var ec := SpriteCache.element_color(el)
	var col := int(rect.position.x / FAM_W)
	for lane in [-0.3, 0.3]:
		var x: float = (col + 0.5 + float(lane) * 0.5) * FAM_W
		if x < rect.position.x or x >= rect.end.x: continue
		var pts := PackedVector2Array()
		for s in 16:
			var yy := rect.position.y + s * rect.size.y / 15.0
			pts.append(Vector2(x + sin(yy * 0.011 + col) * 12.0, yy))
		cv.draw_polyline(pts, Color(ec, 0.1), 1.2, true)
	for key in _rows:
		if str(key).begins_with("n"): continue
		var yy := float(_rows[key]) - 24.0
		if yy < rect.position.y or yy >= rect.end.y: continue
		var pts2 := PackedVector2Array()
		for s in int(rect.size.x / 25.0) + 1: pts2.append(Vector2(rect.position.x + s * 25.0, yy + sin((rect.position.x + s * 25.0) * 0.02) * 3.0))
		cv.draw_polyline(pts2, Color(UiKit.MIST, 0.16), 1.0, true)
	for it in tile.items:
		_route(cv, it.route, _state_col(it), str(it.state) == "locked", str(it.kind) in ["art", "keystone"])
		if it.get("chan", false): _route(cv, [it.at, it.at + Vector2(FAM_W, 0)], Color(UiKit.GOLD, 0.45), true)

## The ring soundings down the chart's right edge, each written only while it is wholly inside the chart.
func _draw_rings(cv: Layer) -> void:
	for key in _rows:
		if str(key).begins_with("n"): continue
		var y := float(_rows[key]) - view.y + CHART.position.y
		if y + 14 < VIS.position.y + HEAD or y + 64 > VIS.end.y: continue
		var g := str(TechniqueTreeRules.ring_row(int(key)).get("grade", "common"))
		UiKit.draw_text(cv, ROMAN[int(key)], Vector2(VIS.end.x - 66, y + 40) - MID.position, 26, Color(UiKit.MIST, 0.85), HORIZONTAL_ALIGNMENT_CENTER, 60, true, true)
		UiKit.draw_text(cv, UiKit.fit(Tx.t("ui.techniques.grade_" + g), 14, 72), Vector2(VIS.end.x - 72, y + 60) - MID.position, 14, UiKit.grade_color(g), HORIZONTAL_ALIGNMENT_CENTER, 72)

## The chart's tap regions for this view: a card's, a passage's and a notable's in view, inside the chart. The page lays
## them as it draws; a tap after a pan lays them again first (_sync_chart_regions).
func _chart_regions() -> void:
	_regions_view = view
	_areas["chart"] = {"rect": VIS, "max": 0.0, "active": true}
	var n0 := _regions.size()
	var vr := Rect2(view, CHART.size)
	tour_marks.erase("open_node")
	for it in _items:
		if not vr.intersects(it.box): continue
		var s := _on_screen(it.at)
		if str(it.kind) in ["passage", "notable"]:
			if VIS.has_point(s): region(Rect2(s - Vector2(10, 10), Vector2(20, 20)), "node", str(it.id))
			continue
		var rect := Rect2(s - Vector2(CARD.x * 0.5, 0), CARD)
		if rect.intersects(CHART): region(Rect2(rect.position.x + 20, rect.position.y, CARD.x - 40, CARD.y), "node", str(it.id))
		# Decision 43: the first card in view that may be learned now is the one the Realisation guide points at.
		if not tour_marks.has("open_node") and VIS.encloses(rect) and str(_state(it).get("state", "")) == "open": tour_mark("open_node", rect)
	for i in range(n0, _regions.size()): _regions[i].chart = true
	_areas["chart"].active = false

## The chart's regions laid again for the view it stands at now, without drawing the page.
func _sync_chart_regions() -> void:
	if not _is_tree() or c() == null or _regions_view == view: return
	_regions = _regions.filter(func(r): return not r.get("chart", false))
	_chart_regions()

## The words the chart's tiles write, named for the ui_suite as if the page wrote them (only those wholly inside the
## chart): each card's name and tag in view, and the ring soundings.
func _log_chart() -> void:
	var vr := Rect2(view, CHART.size)
	for it in _items:
		if str(it.kind) in ["passage", "notable"] or not vr.intersects(it.box): continue
		_state(it)
		var rect := Rect2(_on_screen(it.at) - Vector2(CARD.x * 0.5, 0), CARD)
		var st := str(it.state)
		var learned := st in ["realised", "taught"]
		var name_r := Rect2(rect.position + Vector2(0, 78), Vector2(CARD.x, 18))
		if VIS.encloses(name_r):
			ground(name_r.grow(4), UiKit.SURFACE.space)
			var nm := fit(str(it.name), 16, CARD.x)
			_log_text(Vector2(rect.position.x, rect.position.y + 92), nm, 16, HORIZONTAL_ALIGNMENT_CENTER, CARD.x, false, Rect2(),
				UiKit.PALE_GOLD if sel == str(it.id) else (UiKit.PAPER if st != "locked" else UiKit.HOLLOW))
		var tag := str(it.tag)
		var tw := UiKit.text_width(tag, 14) + (22.0 if learned else 36.0)
		var tr := Rect2(rect.get_center().x - tw * 0.5, rect.position.y + 96, tw, 19)
		if VIS.encloses(tr):
			ground(tr, UiKit.SURFACE.cloth if learned else UiKit.SURFACE.space)
			var mark := 0.0 if learned else 14.0
			_log_text(Vector2(tr.position.x + mark, tr.position.y + 15), fit(tag, 14, tw - mark), 14, HORIZONTAL_ALIGNMENT_CENTER, tw - mark, false, Rect2(),
				UiKit.BRIGHT_JADE if learned else (UiKit.PALE_GOLD if st == "open" else UiKit.MIST))
	for key in _rows:
		if str(key).begins_with("n"): continue
		var y := float(_rows[key]) - view.y + CHART.position.y
		if y + 14 < VIS.position.y + HEAD or y + 64 > VIS.end.y: continue
		var g := str(TechniqueTreeRules.ring_row(int(key)).get("grade", "common"))
		_log_text(Vector2(VIS.end.x - 66, y + 40), ROMAN[int(key)], 26, HORIZONTAL_ALIGNMENT_CENTER, 60, true, Rect2(), Color(UiKit.MIST, 0.85))
		_log_text(Vector2(VIS.end.x - 72, y + 60), fit(Tx.t("ui.techniques.grade_" + g), 14, 72), 14, HORIZONTAL_ALIGNMENT_CENTER, 72, false, Rect2(), UiKit.grade_color(g))

## Over the chart's head, at the right: Learned (the next learned art) and Let all go (the tree's reset). The family in
## view on its plaque and the act's rings in view are the labels layer's (_draw_labels), written again as the view moves
## without drawing the page; they are named here for the ui_suite.
func _chart_labels() -> void:
	btn(Rect2(VIS.end.x - 207, 78, 84, 28), Tx.t("ui.techniques.next_learned"), "next_learned", null, false, not _learned().is_empty(), Tx.t("ui.techniques.none_learned"), 14)
	btn(Rect2(VIS.end.x - 119, 78, 114, 28), Tx.t("ui.techniques.let_all_go"), "reset", _tab_id(), false, _realised_here > 0, Tx.t("sim.tree.nothing"), 14)
	if text_log == null: return
	var pl := _plaque_words()
	ground(PLAQUE, UiKit.SURFACE.cloth)
	_log_text(Vector2(PLAQUE.position.x, PLAQUE.get_center().y + int(pl[1]) * 0.36), str(pl[0]), int(pl[1]), HORIZONTAL_ALIGNMENT_CENTER, PLAQUE.size.x, true, Rect2(), UiKit.PALE_GOLD, true)
	var act := _act_words()
	if act != "": _log_text(Vector2(VIS.position.x + 14, 98), fit(act, 14, 116), 14, HORIZONTAL_ALIGNMENT_LEFT, 116, false, Rect2(), UiKit.PAPER)

const PLAQUE := Rect2(376, 78, 302, 28)   # the family in view, over the chart (VIS.position.x + 135)

## The plaque's words for the view and their size: "<Family> arts of <Element>", stepped down to fit.
func _plaque_words() -> Array:
	var full := Tx.t("ui.techniques.arts_of_" + _fam_at_view()) % str(tabs[tab].label)
	var size := 22
	while size > 16 and UiKit.text_width(full, size, true) > PLAQUE.size.x - 56: size -= 2
	return [fit(full, size, PLAQUE.size.x, true), size]

## "Act I · rings I–IV": the act and the rings in view ("" when no ring's row is in view).
func _act_words() -> String:
	var r := _rings_in_view()
	if r.y < r.x: return ""
	return Tx.t("ui.techniques.act_rings") % [ROMAN[TechniqueTreeRules.act_of(r.x)], ROMAN[r.x], ROMAN[r.y]]

## The labels layer: the family in view on its plaque, and the act's rings in view (drawn over the chart and the page).
func _draw_labels(cv: Layer) -> void:
	if not _is_tree() or c() == null: return
	_name_plaque_on(cv, PLAQUE, Tx.t("ui.techniques.arts_of_" + _fam_at_view()) % str(tabs[tab].label))
	var act := _act_words()
	if act != "": UiKit.draw_text(cv, UiKit.fit(act, 14, 116), Vector2(VIS.position.x + 14, 98), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 116)

## A name on its plaque on any canvas item (the labels layer's family in view): _name_plaque's look.
func _name_plaque_on(cv: CanvasItem, r: Rect2, name: String) -> void:
	Page.glow_on(cv, r.grow(6), Color(UiKit.INK, 0.5))
	Page.rounded_on(cv, r.grow(1), 4.0, UiKit.INK)
	Page.rounded_on(cv, r, 3.0, UiKit.GOLD)
	Page.rounded_on(cv, r.grow(-1.5), 2.0, UiKit.SURFACE.cloth)
	var size := 22
	while size > 16 and UiKit.text_width(name, size, true) > r.size.x - 56: size -= 2
	var w := minf(UiKit.text_width(name, size, true), r.size.x - 56)
	for sx in [-1.0, 1.0]:
		var d := r.get_center() + Vector2(sx * (w * 0.5 + 16), 0)
		cv.draw_colored_polygon(PackedVector2Array([d + Vector2(0, -5), d + Vector2(5, 0), d + Vector2(0, 5), d + Vector2(-5, 0)]), UiKit.GOLD)
	UiKit.draw_inked(cv, UiKit.fit(name, size, r.size.x, true), Vector2(r.position.x, r.get_center().y + size * 0.36), size, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)

## A name on its plaque (the tree's family in view, the reading's art): jade in a gold rim, a gold diamond at each end.
func _name_plaque(r: Rect2, name: String) -> void:
	glow(r.grow(6), Color(UiKit.INK, 0.5))
	rounded(r.grow(1), 4.0, UiKit.INK)
	rounded(r, 3.0, UiKit.GOLD)
	rounded(r.grow(-1.5), 2.0, UiKit.SURFACE.cloth)
	var size := 22
	while size > 16 and UiKit.text_width(name, size, true) > r.size.x - 56: size -= 2
	var w := minf(UiKit.text_width(name, size, true), r.size.x - 56)
	for sx in [-1.0, 1.0]:
		var d := r.get_center() + Vector2(sx * (w * 0.5 + 16), 0)
		draw_colored_polygon(PackedVector2Array([d + Vector2(0, -5), d + Vector2(5, 0), d + Vector2(0, 5), d + Vector2(-5, 0)]), UiKit.GOLD)
	inked(Vector2(r.position.x, r.get_center().y + size * 0.36), name, size, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func _state_col(it: Dictionary) -> Color:
	match str(it.get("state", "")):
		"realised", "taught": return UiKit.BRIGHT_JADE
		"open": return UiKit.GOLD
	return UiKit.HOLLOW

## A route through `pts` (chart space) on `cv` in the colour of the node it leads to; dashed while that node is locked,
## with an arrowhead into a card.
func _route(cv: CanvasItem, pts: Array, col: Color, dashed: bool, arrow := false) -> void:
	for i in pts.size() - 1:
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		cv.draw_line(a, b, UiKit.INK, 5.0)
		if dashed: cv.draw_dashed_line(a, b, col, 2.4, 6.0)
		else: cv.draw_line(a, b, col, 2.4, true)
	if arrow:
		var tip: Vector2 = pts[-1]
		cv.draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-5, -8), tip + Vector2(5, -8)]), col)

## A passage (a small diamond) or a notable (a large one, an anchor of the act) on `cv`: jade when realised, gold ringed
## when open, slate when locked; the chosen one haloed.
func _diamond(cv: CanvasItem, at: Vector2, r: float, it: Dictionary) -> void:
	var st := str(it.state)
	var fill: Color = UiKit.JADE if st == "realised" else (UiKit.SURFACE.cloth if st == "open" else UiKit.SURFACE.space)
	var pts := PackedVector2Array([at + Vector2(0, -r), at + Vector2(r, 0), at + Vector2(0, r), at + Vector2(-r, 0)])
	if sel == str(it.id): Page.glow_on(cv, Rect2(at - Vector2(r, r) * 2.4, Vector2(r, r) * 4.8), Color(UiKit.PALE_GOLD, 0.5))
	cv.draw_colored_polygon(pts, fill)
	pts.append(pts[0])
	cv.draw_polyline(pts, UiKit.INK, 4.0, true)
	cv.draw_polyline(pts, UiKit.PAPER if st == "realised" else _state_col(it), 1.6, true)
	if str(it.kind) == "notable": cv.draw_circle(at, r * 0.35, _state_col(it), true, -1.0, true)

## A node card on `cv` (a tile's cards layer, in the chart's space): the art's picture (TechniquePicture, the one look
## the HUD's buttons and the loadout bar share: the character large in the art's pose in its element's ink on a starry
## ground, its form's marks round it, a learned art's rank badge) in its frame (jade learned, gold open, slate locked, a
## keystone in a gold double frame; a locked art's picture in a grey ink); its name and its state are the words layer's.
## False while its picture waits its turn to be begun (the tile is drawn again next frame).
func _card(cv: CanvasItem, it: Dictionary, rect: Rect2) -> bool:
	var id := str(it.id)
	var st := str(it.state)
	var learned := st in ["realised", "taught"]
	var p := Rect2(rect.position + Vector2((CARD.x - PIC) * 0.5, 0), Vector2(PIC, PIC))
	if sel == id: Page.glow_on(cv, p.grow(22), Color(UiKit.PALE_GOLD, 0.45))
	if str(it.kind) == "keystone": cv.draw_rect(p.grow(3), UiKit.GOLD, false, 1.5)
	return TechniquePicture.draw(cv, p.grow(1), id, c(), pic.outfit, _state_col(it) if sel != id else UiKit.PALE_GOLD, 1.0, 1.0, "tree",
		st == "locked", int(it.tier) if learned else 0)

## Where a card's name and its tag are written (chart space): [name, tag], kept with the node until its tag changes.
func _word_rects(it: Dictionary) -> Array:
	if it.get("wr_of", null) == it.tag: return it.wr
	var rect := Rect2(it.at - Vector2(CARD.x * 0.5, 0), CARD)
	var tw := UiKit.text_width(str(it.tag), 14) + (22.0 if str(it.state) in ["realised", "taught"] else 36.0)
	it.wr = [Rect2(rect.position + Vector2(0, 78), Vector2(CARD.x, 18)), Rect2(rect.get_center().x - tw * 0.5, rect.position.y + 96, tw, 19)]
	it.wr_of = it.tag
	return it.wr

## The words the chart writes for this view: each card's name and tag wholly inside it, as [node, name?, tag?].
func _words_in_view() -> Array:
	var out: Array = []
	var vr := Rect2(view, CHART.size)
	var inside := Rect2(VIS.position - CHART.position + view, VIS.size)
	var seen: Array = []
	for key in _tiles:
		if (_tiles[key].bounds as Rect2).intersects(vr): seen.append_array(_tiles[key].items)
	for it in seen:
		if str(it.kind) in ["passage", "notable"] or not vr.intersects(it.box): continue
		_state(it)
		var wr := _word_rects(it)
		var n: bool = inside.encloses(wr[0])
		var t: bool = inside.encloses(wr[1])
		if n or t: out.append([it, n, t])
	return out

## The cards' words (a layer in the chart's space, over the cards): a card's name and its tag, each only while wholly
## inside the chart (drawn again when that changes, not as the view moves).
func _draw_words(cv: Layer) -> void:
	for w in _words:
		var it: Dictionary = w[0]
		var id := str(it.id)
		var st := str(it.state)
		var learned := st in ["realised", "taught"]
		var wr := _word_rects(it)
		if w[1]:
			UiKit.draw_text(cv, UiKit.fit(str(it.name), 16, CARD.x), Vector2(wr[0].position.x, wr[0].position.y + 14), 16,
				UiKit.PALE_GOLD if sel == id else (UiKit.PAPER if st != "locked" else UiKit.HOLLOW), HORIZONTAL_ALIGNMENT_CENTER, CARD.x)
		if not w[2]: continue
		var tr: Rect2 = wr[1]
		Page.rounded_on(cv, tr, 9.0, UiKit.INK)
		Page.rounded_on(cv, tr.grow(-1), 8.0, _state_col(it))
		Page.rounded_on(cv, tr.grow(-2), 7.0, UiKit.SURFACE.cloth if learned else UiKit.SURFACE.space)
		var mark := 0.0 if learned else 14.0
		if st == "open": _rz_mark_on(cv, Vector2(tr.position.x + 14, tr.get_center().y), 0.8)
		elif not learned: _lock_on(cv, Vector2(tr.position.x + 8, tr.position.y + 3), 0.8)
		UiKit.draw_text(cv, UiKit.fit(str(it.tag), 14, tr.size.x - mark), Vector2(tr.position.x + mark, tr.position.y + 15), 14,
			UiKit.BRIGHT_JADE if learned else (UiKit.PALE_GOLD if st == "open" else UiKit.MIST), HORIZONTAL_ALIGNMENT_CENTER, tr.size.x - mark)

## An art's form at its impact frame (its sheet in its element's row at its tier's band), the whole cell fitted into `r`
## at `most` scale and centred on it: the reading's picture (`async`: once the sheet is in from its loading thread).
func _form_still(t: Dictionary, r: Rect2, most: float, alpha: float, async := false) -> void:
	var a := FxLayer.form_spec(str(t.get("vfx", {}).get("anim", "")))
	if a.is_empty(): return
	if async and SpriteCache.tex_async(str(a.file)) == null:
		_waiting = true   # drawn again once its sheet is in from its loading thread
		return
	var cell := Vector2(float(a.cell[0]), float(a.cell[1]))
	var k := minf(most, minf((r.size.x - 2.0) / cell.x, (r.size.y - 2.0) / cell.y))
	var at := r.get_center() - (cell * 0.5 - Vector2(float(a.anchor[0]), float(a.anchor[1]))) * k
	var row := FxLayer.form_row(str(t.get("element", "none")), FxLayer.band_of(int(t.get("vfx", {}).get("tier", 1))))
	FxLayer.draw_form_on(self, a, at, int(a.impact), row, 1, k, alpha)

## The words under a card: Learned, what learning it spends, or why it is closed.
func _tag(it: Dictionary) -> String:
	match str(it.state):
		"realised", "taught": return Tx.t("ui.techniques.learned")
		"open": return Tx.t("ui.techniques.to_learn") % int(it.get("total", it.get("cost", 0)))
	if str(it.kind) == "dao": return Tx.t("ui.techniques.dao_tier") % [ContentDB.name_of("daos", str(it.dao)), int(it.dao_tier)]
	if str(it.kind) == "keystone" and str(it.why) in ["source", "route", "level"]: return Tx.t("ui.techniques.keystone")
	if str(it.why) == "path": return Tx.t("ui.techniques.path_" + str(ContentDB.entry("techniques", str(it.id)).get("path", "")))
	if str(it.why) == "realisations": return Tx.t("ui.techniques.to_learn") % int(it.get("total", 0))
	return Tx.t("ui.techniques.why_" + str(it.why)) if str(it.why) in ["level", "act_locked", "gate"] else Tx.t("ui.techniques.locked")

func _fam_icon(fam: String) -> String:
	return "meridian" if fam == "any" else str(ContentDB.entry("weapon_families", fam).get("hud_glyph", fam))

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if _dirty and _is_tree(): _refresh()
	# Decision 43: a tour's anchors (the tree's window, the reading and the loadout dock).
	tour_mark("chart", CHART)
	tour_mark("reading", RIGHT)
	tour_mark("dock", DOCK)
	for pr in [LEFT, RIGHT]: face(pr, "carved_panel")
	_figure()   # under the chooser, which is laid over its feet
	match _tab_id():
		"lost": _chooser_lost(ch)
		"secret": _chooser_secret(ch)
		_: _chooser_tree(ch)
	if _tab_id() == "lost": _board(ch)
	elif _tab_id() == "secret": _mat(ch)
	if drawer: _drawer(ch)
	elif _tab_id() == "lost": _read_lost(ch)
	elif _tab_id() == "secret": _read_secret(ch)
	else: _read_node(ch)
	_dock(ch)

## The chooser's head: a seal, the tab's name and two lines under it.
func _head(seal: String, name: String, a: String, b: String, mark := false) -> void:
	var tx := hd_tex("tech_seal", seal)
	if tx: draw_texture_rect(tx, Rect2(24, 80, 34, 34), false)
	heading(Vector2(66, 106), name, 150)
	if mark: _rz_mark(Vector2(33, 127))
	text(Vector2(26 + (16 if mark else 0), 132), a, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 196)
	text(Vector2(26, 152), b, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 196)

## The character under the chooser, casting the chosen art (TechniquePreview) at a pack of imps; alone when nothing
## castable is chosen. It draws itself over the page (its own nodes), so it is hidden while a question is asked.
func _figure() -> void:
	if stage == null: return
	stage.show_art(_preview_art(), c())
	stage.visible = confirm.is_empty()
	var f := stage.feet()
	glow(Rect2(f + Vector2(-60, -10), Vector2(120, 22)), Color(UiKit.BRIGHT_JADE, 0.25))

## The art the preview casts: the chosen art when it is a technique the page may show (a tree's art, one the character
## knows, or a lost art found); a passage, an Inner Art, a secret art or an art still unknown (decision 19) casts nothing.
func _preview_art() -> String:
	if drawer or sel == "" or not ContentDB.has_entry("techniques", sel): return ""
	var ch = c()
	if ch.cultivator.techniques_known.has(sel): return sel
	if _is_tree(): return sel if _by.has(sel) and str(_by[sel].kind) in ["art", "keystone", "dao"] else ""
	if _tab_id() == "lost":
		for a in _found(ch, lost_act, Game.progression.lost_arts_view(ch)):
			if str(a.id) == sel and str(a.kind) == "technique": return sel
	return ""

## A chooser row: its icon in a well, its name and a value, the line under it and a thin bar.
func _row(rr: Rect2, icon: String, name: String, value: String, line: String, frac: float, on: bool, locked := false) -> void:
	if on: glow(rr.grow(8), Color(UiKit.GOLD, 0.25))
	rounded(rr, 5.0, UiKit.PALE_GOLD if on else Color(UiKit.GOLD, 0.35))
	rounded(rr.grow(-1 if not on else -2), 4.0, UiKit.SURFACE.cloth)
	ground(rr, UiKit.SURFACE.cloth)
	var well := Rect2(rr.position + Vector2(6, 6), Vector2(40, 40))
	rounded(well, 4.0, UiKit.INK)
	icon_at(well.grow(-4), icon, UiKit.MIST if locked else Color.WHITE)
	text(rr.position + Vector2(54, 18), name, 16, UiKit.PALE_GOLD if on else (UiKit.MIST if locked else UiKit.PAPER), HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 60 - UiKit.text_width(value, 14))
	text(Vector2(rr.end.x - 8 - UiKit.text_width(value, 14), rr.position.y + 17), value, 14, UiKit.PAPER)
	text(rr.position + Vector2(54, 36), line, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 62)
	var b := Rect2(rr.position + Vector2(54, 42), Vector2(rr.size.x - 62, 5))
	draw_rect(b, UiKit.INK)
	draw_rect(Rect2(b.position, Vector2(b.size.x * clampf(frac, 0.0, 1.0), b.size.y)), UiKit.JADE)

## A tree tab's chooser: the Realisations to place, then each family with its Dao as its bar (the free hand's is the
## tab's element Dao), Learned and Let all go, and the character.
func _chooser_tree(ch) -> void:
	var tree := _tab_id()
	var rz: Dictionary = _rz if not _rz.is_empty() else {"free": 0, "total": 0}
	_head(tree, str(tabs[tab].label), Tx.t("ui.techniques.to_place") % [int(rz.free), int(rz.total)], Tx.t("ui.techniques.families_daos"), true)
	var fams: Array = TechniqueTreeRules.sectors()
	_here = _fam_at_view()
	var here := _here
	var el_dao := str(TechniqueTreeRules.tree_def(tree).get("dao", ""))
	list("fams", Rect2(20, 164, 208, 280), fams.size(), 56, func(i: int, rr: Rect2):
		var fam := str(fams[i])
		var dao := el_dao if fam == "any" else str(ContentDB.entry("weapon_families", fam).get("dao", ""))
		var d: Dictionary = ch.cultivator.daos.get(dao, {"tier": 0, "insight": 0.0})
		var need := ProgressionRules.dao_next_need(int(d.get("tier", 0)))
		var line := Tx.t("ui.techniques.dao_line") % [ContentDB.name_of("daos", dao), int(d.get("tier", 0))] if dao != "" else Tx.t("ui.techniques.no_dao")
		_row(rr, _fam_icon(fam), Tx.t("ui.techniques.fam_" + fam),
			"%s / %s" % [UiKit.fmt(float(d.get("insight", 0.0))), UiKit.fmt(need)] if dao != "" and need > 0.0 else "", line, float(d.get("insight", 0.0)) / maxf(1.0, need), fam == here)
		region(rr, "family", i))
	var below := fams.size() - 5 - int(float(scroll.get("fams", 0.0)) / 56.0)
	if below > 0: text(Vector2(26, 462), Tx.t("ui.techniques.more_below") % below, 14, UiKit.MIST)

func _learned() -> Array:
	var known: Array = c().cultivator.techniques_known
	return _items.filter(func(it): return str(it.kind) in ["art", "keystone", "dao"] and known.has(str(it.id)))

# ------------------------------------------------------------------ the reading
## The reading's name plaque and the line under it.
func _plaque(name: String, runs: Array) -> void:
	ground(Rect2(RIGHT.position, Vector2(RIGHT.size.x, 60)).grow(-4), UiKit.SURFACE.cloth)
	_name_plaque(Rect2(RIGHT.position.x + 20, 80, 324, 30), name)
	rich(Rect2(RIGHT.position.x + 16, 118, 332, 20), runs, 14, true)

## The picture: the character in the art's pose on its element's ground, in a gold frame. A technique's is its card's
## look at the reading's size (TechniquePicture: the whole figure at x3); the other pictures (a lost art's, a secret
## art's) keep the figure over the element's glow.
func _picture(t: Dictionary, action := "") -> void:
	var r := Rect2(922, 142, 150, 150)
	if action == "" and ContentDB.has_entry("techniques", str(t.get("id", ""))):
		if not TechniquePicture.draw(self, r.grow(2), str(t.id), c(), pic.outfit, UiKit.GOLD, 1.0, 1.0, "reading"): _waiting = true
		return
	rounded(r.grow(2), 5.0, UiKit.INK)
	rounded(r, 4.0, UiKit.GOLD)
	rounded(r.grow(-3), 3.0, UiKit.INK)
	var ec := SpriteCache.element_color(str(t.get("element", "none")))
	glow(Rect2(r.position + Vector2(-10, 10), Vector2(170, 150)), Color(ec, 0.35))
	draw_line(Vector2(r.position.x + 6, r.end.y - 16), Vector2(r.end.x - 6, r.end.y - 16), Color(ec, 0.6), 1.5)
	pic.play(action if action != "" else _pose(t))
	if top:
		# Decision 42: the top-down figure at a whole PIC_K; a stroke stands back to keep its reach in the frame.
		_pose_pic(str(pic.action))
		if not pic.figure.loaded(): _waiting = true   # its sheets are still coming in from their loading threads
		pic.draw_on(self, Vector2(r.position.x + (75.0 if pic.hold == 0 else 58.0), r.end.y - 14), PIC_K)
	else:
		pic.elapsed = 0.3
		# A stroke reaches forward, so its figure stands back to keep the blade in the frame; a still one stands centred.
		pic.draw_on(self, Vector2(r.position.x + (75.0 if str(pic.action) in ["idle", "meditate"] else 44.0), r.end.y - 18), 1.0)
	if action == "": _form_still(t, r.grow(-4), 1.0, 0.85, true)

## The top-down picture's pose: a blow held on the frame it lands, in profile toward the right as the preview casts it;
## a stance or a sitting on its first frame, three-quarters toward the camera.
func _pose_pic(pose: String) -> void:
	pic.play(pose)
	var still: bool = str(pic.action) in ["idle", "meditate", "kneel", "salute"]
	pic.row = "se" if still else "e"
	pic.hold = 0 if still else maxi(1, TopdownFigure.hit_frame(str(pic.action)))

## The body pose an art is shown in: the top-down pose a fight casts it in (TechniquePreview.top_pose) for a top-down
## character, the side view's (TechniquePreview.pose_of) for a classic one.
func _pose(t: Dictionary) -> String:
	if _fam.is_empty(): _fam = StatRules.family(c())
	return TechniquePreview.top_pose(t, c(), _fam) if top else TechniquePreview.pose_of(t, c(), pic.outfit)

## The facts beside the picture: the emblem, its form and element or family, then the numbers.
func _facts(id: String, t: Dictionary, lines: Array) -> void:
	icon_at(Rect2(1090, 142, 64, 64), id)
	var form := str(t.get("form", t.get("template", "")))
	text(Vector2(1164, 164), Tx.t("ui.techniques.form_" + form) if form != "" else Tx.t("ui.techniques.kind_technique"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 96)
	text(Vector2(1164, 184), Tx.t("ui.techniques.fam_" + str(t.get("family", "any"))) if str(t.get("family", "any")) != "any" else str(tabs[tab].label) if _is_tree() else "", 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 96)
	for i in lines.size():   # a line too long for the column steps down a size
		var w: float = (lines[i] as Array).reduce(func(acc, run): return acc + UiKit.text_width(str(run[0]), 16), 0.0)
		rich(Rect2(1090, 214 + i * 22, 174, 20), lines[i], 16 if w <= 150.0 else 14)

## The chosen node of a tree (or any art chosen in the dock): what it is, what it does, and what learning it takes or
## what it has become.
func _read_node(ch) -> void:
	if sel == "" or (not _by.has(sel) and not ContentDB.has_entry("techniques", sel)):
		_plaque(str(tabs[tab].label), [[Tx.t("ui.techniques.choose_node"), UiKit.MIST]])
		para(Rect2(922, 160, 330, 400), Tx.t("ui.techniques.tree_help"), 16, UiKit.PAPER)
		return
	var it: Dictionary = _state(_by[sel]) if _by.has(sel) else {}
	var kind := str(it.get("kind", "art"))
	if kind in ["passage", "notable"]:
		_read_step(ch, it)
		return
	var t := ContentDB.entry("techniques", sel)
	var known: bool = ch.cultivator.techniques_known.has(sel)
	var ring := int(t.get("ring", it.get("ring", 1)))
	var g := str(t.get("grade", "common"))
	var what := Tx.t("ui.techniques.learned") if known else _kind_line(t)
	var runs: Array = [[what + " · ", UiKit.BRIGHT_JADE if known else UiKit.GOLD], [Tx.t("ui.techniques.ring_n") % ROMAN[clampi(ring, 0, 13)] + ", ", UiKit.GOLD], [Tx.t("ui.techniques.grade_" + g), UiKit.grade_color(g)]]
	if known and str(t.get("source", "")) != "" and not ContentDB.has_entry("lost_arts", sel): runs.append([" · " + ContentDB.text("technique_source." + str(t.source)), UiKit.BRIGHT_JADE])
	_plaque(str(t.get("name", sel)), runs)
	_picture(t)
	var cost := int(round(Game.combat.technique_cost(ch, t)))
	var lines: Array = [[[Tx.t("ui.techniques.qi") % cost, UiKit.QI], [" · " + UiKit.span(float(t.get("cooldown_s", 0))), UiKit.PAPER]]]
	if int(t.get("max_targets", 0)) > 0: lines.append([[Tx.plural("ui.techniques.hits", int(t.get("hits", 1))) % int(t.get("hits", 1)) + (" · " + Tx.t("ui.techniques.foes") % int(t.max_targets) if int(t.max_targets) > 1 else ""), UiKit.PAPER]])
	if bool(t.get("heavy", false)): lines.append([[Tx.t("ui.techniques.heavy"), UiKit.MIST]])
	elif known: lines.append([[Tx.plural("ui.techniques.used", int(ch.cultivator.technique_use.get(sel, 0))) % int(ch.cultivator.technique_use.get(sel, 0)), UiKit.MIST]])
	_facts(sel, t, lines)
	para(Rect2(920, 302, 332, 64), TechniqueTreeRules.describe(t), 16, UiKit.PAPER, 3)
	_rule(362)
	if known: _read_known(ch, t, it)
	else: _read_learn(ch, t, it)

func _kind_line(t: Dictionary) -> String:
	match str(t.get("kind", "")):
		"keystone": return Tx.t("ui.techniques.keystone_of") % ContentDB.text("technique.kin." + str(t.get("kin", "voice")))
		"dao": return Tx.t("ui.techniques.dao_art")
	return Tx.t("ui.techniques.path_art_of" if str(t.get("path", "")) != "" else "ui.techniques.orthodox_of") % Tx.t("ui.techniques.fam_" + str(t.get("family", "any")))

## A section's name in the reading (Prerequisites, Cost): gold, in the display face, without a rule under it.
func _section(pos: Vector2, s: String) -> void:
	text(pos, s, 22, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 140, true)

func _rule(y: float) -> void:
	draw_line(Vector2(916, y), Vector2(1256, y), Color(UiKit.GOLD, 0.6), 1.0)

## An art not yet learned: its prerequisites ticked and crossed, the cost, and Learn naming the Realisations it spends.
func _read_learn(ch, t: Dictionary, it: Dictionary) -> void:
	_section(Vector2(920, 388), Tx.t("ui.techniques.prerequisites"))
	var y := 396.0
	if str(it.get("kind", "")) == "dao":
		_need(y, "dao", Tx.t("ui.techniques.dao_tier") % [ContentDB.name_of("daos", str(it.dao)), int(it.dao_tier)], "%d / %d" % [int(ch.cultivator.daos.get(str(it.dao), {}).get("tier", 0)), int(it.dao_tier)], false)
		_rule(506)
		para(Rect2(920, 520, 332, 110), Tx.t("ui.techniques.dao_taught"), 16, UiKit.MIST)
		return
	for n in Game.progression.node_needs(ch, sel):
		_need(y, str(n.kind), _need_text(n), _need_value(ch, n), bool(n.ok))
		y += 36.0
	_rule(506)
	_section(Vector2(920, 530), Tx.t("ui.techniques.cost"))
	var rz: Dictionary = Game.progression.realisations(ch)
	var total := int(it.get("total", TechniqueTreeRules.cost(sel)))
	_rz_mark(Vector2(1000, 523))
	rich(Rect2(1012, 513, 250, 20), [[str(total) + " ", UiKit.PALE_GOLD], [Tx.t("ui.techniques.realisations_of") % int(rz.free), UiKit.MIST]], 16)
	rich(Rect2(1000, 535, 250, 20), [[str(int(round(Game.combat.technique_cost(ch, t)))) + " ", UiKit.QI], [Tx.t("ui.techniques.qi_each"), UiKit.MIST]], 16)
	_learn_btn(it, total)

## Learn: primary, naming what it spends when it can; closed, plain Learn with the lock, and why in gold under it.
func _learn_btn(it: Dictionary, total: int) -> void:
	var ok := str(it.get("state", "")) == "open"
	var why := "" if ok else Tx.t("sim.tree." + str(it.get("why", "route")))
	btn(Rect2(950, 562, 272, 52), Tx.plural("ui.techniques.learn_for", total) % total if ok else Tx.t("ui.techniques.learn"), "learn", sel, true, ok, why, 22)
	if not ok: text(Vector2(916, 632), why, 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 340)

func _rz_mark(at: Vector2, k := 1.0) -> void:
	_rz_mark_on(self, at, k)

## The Realisations mark (a jade diamond in gold) on any canvas item.
static func _rz_mark_on(cv: CanvasItem, at: Vector2, k := 1.0) -> void:
	cv.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -7) * k, at + Vector2(7, 0) * k, at + Vector2(0, 7) * k, at + Vector2(-7, 0) * k]), UiKit.PALE_GOLD)
	cv.draw_colored_polygon(PackedVector2Array([at + Vector2(0, -5) * k, at + Vector2(5, 0) * k, at + Vector2(0, 5) * k, at + Vector2(-5, 0) * k]), UiKit.JADE)

## Page._lock_icon on any canvas item.
static func _lock_on(cv: CanvasItem, p: Vector2, k := 1.0) -> void:
	cv.draw_rect(Rect2(p + Vector2(0, 6) * k, Vector2(12, 9) * k), UiKit.BRONZE)
	cv.draw_arc(p + Vector2(6, 6) * k, 4 * k, PI, TAU, 8, UiKit.BRONZE, 2 * k)

## A prerequisite row: its sign, what it asks, how far along, and a tick or a cross.
func _need(y: float, kind: String, what: String, value: String, ok: bool) -> void:
	icon_at(Rect2(918, y, 32, 32), {"ring": "cultivation", "source": "quest", "path": "dao", "dao": "dao", "gate": "techniques"}.get(kind, "meridian"))
	text(Vector2(958, y + 22), what, 16 if UiKit.text_width(what, 16) <= 214.0 else 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 214)
	text(Vector2(1172, y + 22), value, 16, UiKit.BRIGHT_JADE if ok else UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_RIGHT, 56)
	var m := Vector2(1242, y + 16)
	if ok:
		draw_polyline(PackedVector2Array([m + Vector2(-6, 0), m + Vector2(-2, 5), m + Vector2(7, -6)]), UiKit.BRIGHT_JADE, 2.5, true)
	else:
		draw_line(m + Vector2(-5, -5), m + Vector2(5, 5), UiKit.RED_TEXT, 2.5, true)
		draw_line(m + Vector2(5, -5), m + Vector2(-5, 5), UiKit.RED_TEXT, 2.5, true)

func _need_text(n: Dictionary) -> String:
	match str(n.kind):
		"ring": return Tx.t("ui.techniques.need_ring") % [ROMAN[int(n.ring)], int(n.arg)]
		"gate": return Tx.t("ui.techniques.need_gate") % Tx.t("ui.techniques.fam_" + str(n.arg))
		"path": return Tx.t("ui.techniques.need_path") % Tx.t("ui.techniques.pathname_" + str(n.arg))
		"source": return ContentDB.text("technique_source." + str(n.arg))
	var inner := TechniqueTreeRules.node(str(n.arg))
	var fam := Tx.t("ui.techniques.fam_" + str(inner.get("family", "any")))
	if str(TechniqueTreeRules.node(sel).get("kind", "")) == "keystone": fam = ContentDB.text("technique.kin." + str(TechniqueTreeRules.node(sel).get("kin", "voice")))
	return Tx.t("ui.techniques.need_passage") % [ROMAN[int(inner.get("ring", 1))], fam]

func _need_value(ch, n: Dictionary) -> String:
	if str(n.kind) == "ring": return "%d / %d" % [ProgressionRules.level(ch), int(n.arg)]
	return "1 / 1" if bool(n.ok) else "0 / 1"

## A passage or a notable: the small passive it gives, what it needs, and Realise; realised, Let go.
func _read_step(ch, it: Dictionary) -> void:
	var fam := Tx.t("ui.techniques.fam_" + str(it.family))
	var ring := int(it.ring)
	var g := str(TechniqueTreeRules.ring_row(ring).get("grade", "common"))
	var notable := str(it.kind) == "notable"
	var nm := Tx.t("ui.techniques.notable_name") % [ROMAN[TechniqueTreeRules.act_of(ring)], fam] if notable else Tx.t("ui.techniques.passage_name") % [ROMAN[ring], fam]
	_plaque(nm, [[Tx.t("ui.techniques.of_tree") % str(tabs[tab].label) + " · ", UiKit.GOLD], [Tx.t("ui.techniques.ring_n") % ROMAN[ring] + ", ", UiKit.GOLD], [Tx.t("ui.techniques.grade_" + g), UiKit.grade_color(g)]])
	var k: Dictionary = TechniqueTreeRules.config().get("passives", {})
	var what := Tx.t("ui.techniques.gives_damage") % [roundi(float(k.get("notable", 0.03)) * 100), str(tabs[tab].label), fam] if notable \
		else (Tx.t("ui.techniques.gives_damage") % [roundi(float(k.get("passage_power", 0.01)) * 100), str(tabs[tab].label), fam] if ring % 2 == 1
		else Tx.t("ui.techniques.gives_cost") % [str(tabs[tab].label), fam, roundi(-float(k.get("passage_cost", -0.02)) * 100)])
	para(Rect2(920, 150, 332, 120), what + " " + Tx.t("ui.techniques.notable_help" if notable else "ui.techniques.passage_help"), 16, UiKit.PAPER)
	_rule(362)
	if str(it.state) == "realised":
		heading(Vector2(920, 400), Tx.t("ui.techniques.realised"), 330)
		para(Rect2(920, 416, 332, 80), Tx.t("ui.techniques.let_go_help"), 16, UiKit.MIST)
		btn(Rect2(950, 574, 272, 52), Tx.t("ui.techniques.let_go_for") % int(it.cost), "let_go", sel, false, true, "", 20)
		return
	_section(Vector2(920, 388), Tx.t("ui.techniques.prerequisites"))
	var y := 396.0
	for n in Game.progression.node_needs(ch, sel):
		_need(y, str(n.kind), _need_text(n), _need_value(ch, n), bool(n.ok))
		y += 36.0
	_rule(506)
	_section(Vector2(920, 530), Tx.t("ui.techniques.cost"))
	_rz_mark(Vector2(1000, 523))
	rich(Rect2(1012, 513, 250, 20), [[str(int(it.cost)) + " ", UiKit.PALE_GOLD], [Tx.t("ui.techniques.realisations_of") % int(_rz.get("free", 0)), UiKit.MIST]], 16)
	_learn_btn(it, int(it.cost))

## A learned art: its mastery, where it is slotted, Slot or Unslot, Rank Up and (a realised one) Let go.
func _read_known(ch, t: Dictionary, it: Dictionary) -> void:
	var m: Dictionary = ch.cultivator.mastery.get(sel, {"tier": 1, "points": 0.0})
	var tier := int(m.get("tier", 1))
	heading(Vector2(920, 400), Tx.t("ui.techniques.mastery"), 120)
	for i in 6:
		var d := Vector2(1062 + i * 20, 393)
		var pts := PackedVector2Array([d + Vector2(0, -8), d + Vector2(8, 0), d + Vector2(0, 8), d + Vector2(-8, 0)])
		draw_colored_polygon(pts, UiKit.BRIGHT_JADE if i < tier else UiKit.INK)
		pts.append(pts[0])
		draw_polyline(pts, UiKit.JADE, 1.2, true)
	text(Vector2(1186, 400), Tx.t("ui.techniques.tier") % tier, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 66)
	var need := ProgressionRules.mastery_needed(tier)
	bar(Rect2(920, 412, 332, 26), float(m.get("points", 0.0)) / need, UiKit.JADE, Tx.t("ui.techniques.practice") % [UiKit.fmt(float(m.get("points", 0.0))), UiKit.fmt(need)])
	para(Rect2(920, 446, 332, 40), Tx.t("ui.techniques.next_tier") % [tier + 1, UiKit.fmt(need)] if tier < 6 else Tx.t("ui.techniques.top_tier"), 14, UiKit.MIST, 2)
	_rule(490)
	var at := _slot_of(ch, sel)
	heading(Vector2(920, 524), Tx.t("ui.techniques.slotted"), 110)
	text(Vector2(1030, 520), Tx.t("ui.techniques.slot_at") % [ROMAN[at / 4 + 1], at % 4 + 1] if at >= 0 else Tx.t("ui.techniques.not_slotted"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 222)
	text(Vector2(1030, 540), Tx.t("ui.techniques.or_tap_slot"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 222)
	var n := ProgressionRules.technique_slot_count(ch)
	btn(Rect2(920, 568, 156, 56), Tx.t("ui.techniques.unslot") if at >= 0 else Tx.t("ui.techniques.slot"), "slot_sel", sel, true, at >= 0 or n > 0, Tx.t("ui.techniques.more_slots_open_with_your"), 22)
	btn(Rect2(1086, 568, 166 if str(it.get("state", "")) != "realised" else 80, 56), Tx.t("ui.techniques.rank_up"), "rank", sel, false, tier >= 3 and tier < 6,
		Tx.t("ui.techniques.rank_from") if tier < 3 else Tx.t("ui.techniques.top_tier"), 20)
	if str(it.get("state", "")) == "realised": btn(Rect2(1172, 568, 80, 56), Tx.t("ui.techniques.let_go"), "let_go", sel, false, at < 0, Tx.t("sim.tree.slotted"), 18)

func _slot_of(ch, id: String) -> int:
	return ch.cultivator.technique_slots.find(id)

# ------------------------------------------------------------------ Lost Arts: the album
## The found cards of an act, the unread manuals among them, as the page shows them.
func _found(ch, act: int, v: Dictionary) -> Array:
	var out: Array = []
	for a in v.get("acts", []):
		if int(a.act) == act: out.append_array(a.arts)
	for card in Game.progression.lost_unread(ch):
		if int(card.act) == act: out.append(card)
	return out

func _lost_counts(ch, v: Dictionary, act: int) -> Vector2i:
	for a in v.get("acts", []):
		if int(a.act) == act: return Vector2i(_found(ch, act, v).size(), int(a.total))
	return Vector2i.ZERO

func _chooser_lost(ch) -> void:
	var v: Dictionary = Game.progression.lost_arts_view(ch)
	_head("lost", Tx.t("ui.techniques.lost_arts"), Tx.t("ui.techniques.found_only"), Tx.t("ui.techniques.acts_reached"))
	var acts: Array = v.get("acts", [])
	var y := 164.0
	for a in acts:
		var n := _lost_counts(ch, v, int(a.act))
		var rr := Rect2(20, y, 200, 52)
		_row(rr, "world_map", Tx.t("ui.techniques.act_n") % ROMAN[int(a.act)], "%d / %d" % [n.x, n.y], Tx.t("ui.techniques.act_name_%d" % int(a.act)), float(n.x) / maxf(1.0, n.y), lost_act == int(a.act))
		region(rr, "lost_act", int(a.act))
		y += 56.0
	var lins: Array = v.get("lineages", [])
	var all_lins: int = (ContentDB.config("lost_arts").get("lineages", []) as Array).size()
	var lr := Rect2(20, y, 200, 52)
	_row(lr, "codex", Tx.t("ui.techniques.lineages"), "%d / %d" % [lins.size(), all_lins], Tx.t("ui.techniques.lost_schools"), float(lins.size()) / maxf(1.0, all_lins), lost_act == 0)
	region(lr, "lost_act", 0)
	y += 56.0
	if acts.size() < 5:
		var kr := Rect2(20, y, 200, 52)
		_row(kr, "lock", Tx.t("ui.techniques.acts_later") % [ROMAN[acts.size() + 1], ROMAN[5]], "", Tx.t("ui.techniques.not_reached"), 0.0, false, true)

## The album's leaf for the chosen act: its count, the found arts pasted in, every other leaf sealed alike.
func _board(ch) -> void:
	var v: Dictionary = Game.progression.lost_arts_view(ch)
	if lost_act == 0:
		_lineages(v)
		return
	var n := _lost_counts(ch, v, lost_act)
	var found := _found(ch, lost_act, v)
	var plq := Rect2(MID.get_center().x - 160, 76, 320, 34)
	_name_plaque(Rect2(plq.position.x, 78, plq.size.x, 30), Tx.t("ui.techniques.act_title") % [ROMAN[lost_act], Tx.t("ui.techniques.act_name_%d" % lost_act)])
	ground(Rect2(MID.position, Vector2(MID.size.x, 48)), UiKit.SURFACE.cloth)
	text(Vector2(256, 98), Tx.t("ui.techniques.n_found") % [n.x, n.y], 14, UiKit.PAPER)
	text(Vector2(700, 98), Tx.t("ui.techniques.n_sealed") % (n.y - n.x), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 180)
	var leaves := n.y
	list("album", Rect2(252, 112, 636, 488), ceili(leaves / 5.0), 120, func(row: int, rr: Rect2):
		for k in 5:
			var i := row * 5 + k
			if i >= leaves: return
			var at := Vector2(rr.position.x + 24 + k * 122, rr.position.y)
			var p := Rect2(at, Vector2(PIC, PIC))
			if i < found.size(): _leaf(found[i], p)
			else:
				_sealed(p)
				region(Rect2(at - Vector2(20, 0), Vector2(116, 116)), "sealed", lost_act))
	para(Rect2(252, 604, 628, 34), Tx.t("ui.techniques.more_in_world") % (n.y - n.x) if n.y > n.x else Tx.t("ui.techniques.all_found"), 22, UiKit.PAPER, 1, true)

## A found art on its leaf: its emblem, its name and Unread or Learned.
func _leaf(card: Dictionary, p: Rect2) -> void:
	var on := sel == str(card.id)
	if on: glow(p.grow(22), Color(UiKit.PALE_GOLD, 0.45))
	rounded(p.grow(1), 5.0, UiKit.INK)
	rounded(p, 4.0, UiKit.PALE_GOLD if on else (UiKit.GOLD if card.get("unread", false) else UiKit.JADE))
	rounded(p.grow(-2), 3.0, UiKit.INK)
	_art_icon(str(card.id), str(card.kind), p.grow(-6))
	ground(Rect2(p.position - Vector2(22, -78), Vector2(120, 44)), UiKit.SURFACE.cloth)
	text(Vector2(p.position.x - 22, p.position.y + 94), str(card.name), 16, UiKit.PALE_GOLD if on else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 120)
	var tag := Tx.t("ui.techniques.unread") if card.get("unread", false) else Tx.t("ui.techniques.learned")
	var tw := UiKit.text_width(tag, 14) + 22.0
	var tr := Rect2(p.get_center().x - tw * 0.5, p.position.y + 99, tw, 19)
	rounded(tr, 9.0, UiKit.GOLD if card.get("unread", false) else UiKit.JADE)
	rounded(tr.grow(-1), 8.0, UiKit.SURFACE.cloth)
	text(Vector2(tr.position.x, tr.position.y + 15), tag, 14, UiKit.PALE_GOLD if card.get("unread", false) else UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, tw)
	region(Rect2(p.position - Vector2(20, 0), Vector2(116, 116)), "lost", str(card.id))

## A sealed leaf: the same for every art not yet found (decision 19), gold thread crossed under a red seal.
func _sealed(p: Rect2) -> void:
	rounded(p.grow(1), 5.0, UiKit.INK)
	rounded(p, 4.0, Color(UiKit.GOLD, 0.35))
	rounded(p.grow(-2), 3.0, UiKit.SURFACE.cloth)
	var c0 := p.get_center()
	draw_line(Vector2(p.position.x + 6, c0.y), Vector2(p.end.x - 6, c0.y), UiKit.BRONZE, 2.0)
	draw_line(Vector2(c0.x, p.position.y + 6), Vector2(c0.x, p.end.y - 6), UiKit.BRONZE, 2.0)
	draw_circle(c0, 11.0, UiKit.INK, true, -1.0, true)
	draw_circle(c0, 9.5, UiKit.BLOOD, true, -1.0, true)
	draw_circle(c0 - Vector2(2, 2), 4.0, UiKit.RED, true, -1.0, true)

func _art_icon(id: String, kind: String, r: Rect2) -> void:
	if kind == "technique" and SpriteCache.draw_icon(self, r, id) != Rect2(): return
	draw_texture_rect(UiKit.hd_texture("tech_seal", "secret" if kind == "secret" else ("soul" if kind == "inner" else "lost")), Rect2(r.get_center() - Vector2(22, 22), Vector2(44, 44)), false)

func _lineages(v: Dictionary) -> void:
	var lins: Array = v.get("lineages", [])
	var plq := Rect2(MID.get_center().x - 160, 76, 320, 34)
	_name_plaque(Rect2(plq.position.x, 78, plq.size.x, 30), Tx.t("ui.techniques.lineages"))
	ground(MID.grow(-6), UiKit.SURFACE.cloth)
	if lins.is_empty():
		para(Rect2(272, 140, 590, 80), Tx.t("ui.techniques.no_lineage"), 18, UiKit.MIST)
		return
	list("lineages", Rect2(256, 120, 628, 500), lins.size(), 160, func(i: int, rr: Rect2):
		var l: Dictionary = lins[i]
		heading(rr.position + Vector2(12, 30), str(l.name), rr.size.x - 24)
		para(Rect2(rr.position + Vector2(12, 42), Vector2(rr.size.x - 24, 44)), str(l.rule), 16, UiKit.PAPER, 2)
		text(rr.position + Vector2(12, 106), Tx.plural("ui.techniques.pieces_found", int(l.found)) % int(l.found), 16, UiKit.BRIGHT_JADE)
		text(rr.position + Vector2(12, 130), ", ".join((l.arts as Array).map(func(a): return str(a.name))), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 24))

## A found lost art in the reading: what it is and does, and Read for a manual not yet read, Slot or Wear for the rest.
func _read_lost(ch) -> void:
	var v: Dictionary = Game.progression.lost_arts_view(ch)
	var card := {}
	for a in _found(ch, lost_act, v):
		if str(a.id) == sel: card = a
	if card.is_empty():
		_plaque(Tx.t("ui.techniques.lost_arts"), [[Tx.t("ui.techniques.found_only"), UiKit.MIST]])
		para(Rect2(922, 160, 330, 400), Tx.t("ui.techniques.lost_help"), 16, UiKit.PAPER)
		return
	var kind := str(card.kind)
	var unread: bool = card.get("unread", false)
	_plaque(str(card.name), [[Tx.t("ui.techniques.lost_line") % [Tx.t(KINDS.get(kind, "ui.techniques.kind_technique")), ROMAN[int(card.act)]] + " · ", UiKit.GOLD],
		[Tx.t("ui.techniques.found_unread") if unread else Tx.t("ui.techniques.found_learned"), UiKit.PALE_GOLD if unread else UiKit.BRIGHT_JADE]])
	var t := ContentDB.entry("techniques", str(card.id)) if kind == "technique" else {"element": str(card.element)}
	_picture(t, "meditate" if kind == "inner" else ("idle" if kind == "secret" else ""))
	_art_icon(str(card.id), kind, Rect2(1090, 142, 64, 64))
	text(Vector2(1164, 164), Tx.t(KINDS.get(kind, "ui.techniques.kind_technique")), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 96)
	text(Vector2(1164, 184), Tx.t("ui.techniques.passive") if kind == "inner" else (Tx.t("ui.techniques.known") if kind == "secret" else Tx.t("ui.techniques.heavy_short")), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 96)
	para(Rect2(920, 302, 332, 70), str(card.desc), 16, UiKit.PAPER, 3)
	_rule(380)
	if unread:
		heading(Vector2(920, 412), Tx.t("ui.techniques.manual"), 330)
		para(Rect2(920, 428, 332, 80), Tx.t("ui.techniques.read_help") % ContentDB.item_name(str(card.item)), 16, UiKit.PAPER)
		btn(Rect2(950, 564, 272, 54), Tx.t("ui.techniques.read"), "read", str(card.item), true)
		return
	if kind == "inner":
		var worn: int = ch.cultivator.inner_arts.find(str(card.id))
		var open := ProgressionRules.inner_art_slot_count(ch.cultivator.realm_key)
		heading(Vector2(920, 412), Tx.t("ui.techniques.worn_head"), 330)
		text(Vector2(920, 440), Tx.t("ui.techniques.worn_in") % (worn + 1) if worn >= 0 else Tx.t("ui.techniques.not_worn") % [_worn_count(ch), open], 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 332)
		btn(Rect2(950, 564, 272, 54), Tx.t("ui.techniques.take_off") if worn >= 0 else Tx.t("ui.techniques.wear"), "wear", str(card.id), true, worn >= 0 or _free_inner(ch) >= 0, Tx.t("ui.techniques.no_free_inner"))
	elif kind == "technique":
		var at := _slot_of(ch, str(card.id))
		heading(Vector2(920, 412), Tx.t("ui.techniques.slotted"), 330)
		text(Vector2(920, 440), Tx.t("ui.techniques.slot_at") % [ROMAN[at / 4 + 1], at % 4 + 1] if at >= 0 else Tx.t("ui.techniques.not_slotted"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 332)
		btn(Rect2(950, 564, 272, 54), Tx.t("ui.techniques.unslot") if at >= 0 else Tx.t("ui.techniques.slot"), "slot_sel", str(card.id), true)
	para(Rect2(920, 470, 332, 80), Tx.t("ui.techniques.lost_help"), 14, UiKit.MIST, 3)

func _worn_count(ch) -> int:
	return (ch.cultivator.inner_arts as Array).filter(func(a): return str(a) != "").size()

func _free_inner(ch) -> int:
	for i in ProgressionRules.inner_art_slot_count(ch.cultivator.realm_key):
		if i >= ch.cultivator.inner_arts.size() or str(ch.cultivator.inner_arts[i]) == "": return i
	return -1

# ------------------------------------------------------------------ Secret Arts: the practice mat
func _chooser_secret(ch) -> void:
	var arts: Array = ch.cultivator.secret_arts
	_head("secret", Tx.t("ui.techniques.secret_arts"), Tx.t("ui.techniques.n_known") % arts.size(), Tx.t("ui.techniques.secret_help"))

## The known Secret Arts laid on a woven mat, one footwork line each; the chosen one read at the right.
func _mat(ch) -> void:
	for i in 22: draw_line(Vector2(252 + i * 30, 84), Vector2(252 + i * 30, 636), Color(UiKit.GOLD, 0.05), 6.0)
	ground(MID.grow(-6), UiKit.SURFACE.cloth)
	var arts: Array = ch.cultivator.secret_arts
	if arts.is_empty():
		text(Vector2(252, 160), Tx.t("ui.techniques.no_secret_arts_yet"), 20, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 628)
		return
	list("secret", Rect2(252, 84, 636, 552), arts.size(), 64, func(i: int, rr: Rect2):
		var d := ContentDB.entry("secret_arts", str(arts[i]))
		var on := sel == str(arts[i])
		rounded(rr, 5.0, UiKit.PALE_GOLD if on else Color(UiKit.GOLD, 0.3))
		rounded(rr.grow(-1), 4.0, UiKit.SURFACE.cloth)
		draw_texture_rect(UiKit.hd_texture("tech_seal", "secret"), Rect2(rr.position + Vector2(10, 8), Vector2(44, 44)), false)
		text(rr.position + Vector2(64, 26), str(d.get("name", arts[i])), 20, UiKit.PALE_GOLD)
		text(rr.position + Vector2(64, 48), str(d.get("desc", "")), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 76)
		region(rr, "secret_art", str(arts[i])))

func _read_secret(ch) -> void:
	if not ch.cultivator.secret_arts.has(sel):
		_plaque(Tx.t("ui.techniques.secret_arts"), [[Tx.t("ui.techniques.secret_help"), UiKit.MIST]])
		return
	var d := ContentDB.entry("secret_arts", sel)
	_plaque(str(d.get("name", sel)), [[Tx.t("ui.techniques.kind_secret"), UiKit.GOLD]])
	_picture({"element": "none"}, "idle")
	para(Rect2(920, 302, 332, 120), str(d.get("desc", "")), 16, UiKit.PAPER)
	if sel != "concealment": return
	# S48: Concealment can show a false realm, up to two great realms lower.
	_rule(420)
	var choices: Array = [""] + Game.progression.false_realm_choices(ch)
	list("realms", Rect2(920, 432, 340, 208), choices.size(), 56, func(i: int, rr: Rect2):
		var key := str(choices[i])
		btn(Rect2(rr.position, Vector2(rr.size.x, 48)), Tx.t("ui.techniques.true_realm") if key == "" else ContentDB.realm_label(key), "false_realm", key, ch.cultivator.false_realm == key, true, "", 16))

# ------------------------------------------------------------------ the drawer: Inner Arts and stances
func _drawer(ch) -> void:
	_plaque(Tx.t("ui.techniques.inner_arts"), [[Tx.t("ui.techniques.tap_a_slot_to_wear") if picked_art != "" else Tx.t("ui.techniques.drawer_help"), UiKit.MIST]])
	btn(Rect2(1180, 140, 72, 48), Tx.t("ui.techniques.close_drawer"), "drawer", null, false, true, "", 16)
	var cu: CultivatorState = ch.cultivator
	var n := ProgressionRules.inner_art_slot_count(cu.realm_key)
	if cu.inner_arts_known.is_empty(): para(Rect2(920, 196, 332, 90), Tx.t("ui.techniques.no_inner_arts") if n > 0 else Tx.t("sim.progression.inner_arts_locked"), 16, UiKit.MIST)
	list("arts", Rect2(916, 196, 344, 200), cu.inner_arts_known.size(), 64, func(i: int, rr: Rect2):
		var aid := str(cu.inner_arts_known[i])
		var d := ContentDB.entry("inner_arts", aid)
		rounded(rr, 5.0, UiKit.PALE_GOLD if picked_art == aid else Color(UiKit.GOLD, 0.3))
		rounded(rr.grow(-1), 4.0, UiKit.SURFACE.cloth)
		text(rr.position + Vector2(12, 24), str(d.get("name", aid)) + ("  ·  " + Tx.t("ui.techniques.worn") if aid in cu.inner_arts else ""), 18, UiKit.PALE_GOLD if aid in cu.inner_arts else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 24)
		text(rr.position + Vector2(12, 48), str(d.get("desc", "")), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 24)
		region(rr, "pick_art", aid))
	heading(Vector2(920, 428), Tx.t("ui.techniques.stances"), 330)
	var can := Unlocks.is_unlocked(ch.id, "stances")
	var fam := str(StatRules.family(ch).get("id", "fists"))
	var stances: Array = ContentDB.all("stances")
	list("stances", Rect2(916, 440, 344, 200), stances.size(), 64, func(i: int, rr: Rect2):
		var st: Dictionary = stances[i]
		var on := str(cu.stances.get(str(st.family), "")) == str(st.id)
		var here := str(st.family) == fam
		text(rr.position + Vector2(8, 22), str(st.get("name", "")) + "  ·  " + Tx.t("ui.techniques.fam_" + str(st.family)) if TechniqueTreeRules.sectors().has(str(st.family)) else str(st.get("name", "")),
			16, UiKit.PALE_GOLD if on and here else (UiKit.PAPER if here else UiKit.MIST), HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 112)
		text(rr.position + Vector2(8, 44), str(st.get("desc", "")), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 112)
		var known := ProgressionRules.stance_known(ch, st)   # Willow Leaf Parry needs its technique; one held can still be let go
		btn(Rect2(rr.end.x - 96, rr.position.y + 4, 92, 48), Tx.t("ui.techniques.stance_on") if on else Tx.t("ui.techniques.stance_off"), "stance", str(st.id), on, can and (known or on),
			Unlocks.locked_text("stances") if not can else ("" if known else Tx.t("sim.progression.stance_needs_technique") % ContentDB.name_of("techniques", str(st.technique))), 16))

# ------------------------------------------------------------------ the dock
## Ring I and Ring II (the four slots each, the weapon in hand's bar and the 1/2 swap), the Inner Arts and the stance for
## the weapon in hand, and the tab's line of verse.
func _dock(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	_band(DOCK, UiKit.SURFACE.cloth, UiKit.SURFACE.space)
	draw_line(Vector2(0, DOCK.position.y), Vector2(1280, DOCK.position.y), UiKit.GOLD, 1.0)
	ground(DOCK, UiKit.SURFACE.cloth)
	var n := ProgressionRules.technique_slot_count(ch)
	var weapon = ch.inventory.equipped.get("weapon")
	var target := sel != "" and cu.techniques_known.has(sel)
	for ring in 2:
		var x0 := 104.0 + ring * 318.0
		_dock_label(x0 - 6, Tx.t("ui.techniques.ring_label") % ROMAN[ring + 1], ContentDB.item_name(str(weapon.id)) if ring == 0 and weapon != null else (Tx.t("ui.techniques.swap_line") if ring == 1 else Tx.t("ui.techniques.bare_hands")))
		for k in 4:
			var i := ring * 4 + k
			var r := Rect2(x0 + k * 56, 662, 52, 52)
			var tid = cu.technique_slots[i] if i < cu.technique_slots.size() else null
			_dock_slot(r, i >= n, tid != null and str(tid) == sel, target and i < n and (tid == null or str(tid) != sel))
			# Decision 42: a slotted art shows the tree's picture of it, as the HUD's button does (TechniquePicture).
			if tid != null and str(tid) != "" and not TechniquePicture.draw(self, r.grow(-2), str(tid), ch, pic.outfit, UiKit.BRIGHT_JADE, 1.0, 1.0, "dock"):
				_waiting = true   # its turn to be begun comes in a later frame
			text(r.position + Vector2(4, 15), str(k + 1), 14, UiKit.PALE_GOLD)
			region(r, "slot", i, i < n, Tx.t("ui.techniques.more_slots_open_with_your"))
	var open := ProgressionRules.inner_art_slot_count(cu.realm_key)
	_dock_label(730, Tx.t("ui.techniques.inner_arts"), Tx.t("ui.techniques.worn_of") % [_worn_count(ch), 4])
	for i in 4:
		var r2 := Rect2(736 + i * 56, 662, 52, 52)
		var art := str(cu.inner_arts[i]) if i < cu.inner_arts.size() else ""
		_dock_slot(r2, i >= open, false, picked_art != "" and i < open)
		if art != "": draw_texture_rect(UiKit.hd_texture("tech_seal", "soul"), r2.grow(-4), false)
		region(r2, "art_slot", i, i < open, Tx.t("ui.techniques.inner_slot_locked") % ContentDB.name_of("realms", _slot_realm(i)))
	var fam := str(StatRules.family(ch).get("id", "fists"))
	var st := str(cu.stances.get(fam, ""))
	_dock_label(1030, Tx.t("ui.techniques.stance"), Tx.t("ui.techniques.stance_of") % [Tx.t("ui.techniques.fam_" + fam) if TechniqueTreeRules.sectors().has(fam) else fam, ContentDB.name_of("stances", st) if st != "" else Tx.t("ui.techniques.none")])
	var sr := Rect2(1036, 662, 52, 52)
	_dock_slot(sr, false, false, false)
	icon_at(sr.grow(-10), _fam_icon(fam), Color.WHITE if st != "" else UiKit.HOLLOW)
	region(sr, "drawer")
	draw_line(Vector2(1096, 664), Vector2(1096, 712), Color(UiKit.GOLD, 0.4), 1.0)
	para(Rect2(1104, 664, 170, 54), Tx.t("ui.techniques.verse_" + _tab_id()), 14, UiKit.MIST, 3, true)

func _dock_label(right: float, a: String, b: String) -> void:
	text(Vector2(right - 150, 676), a, 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 150)
	text(Vector2(right - 150, 694), b, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 150)

## A dock slot: dark jade in a gold hairline; the chosen art's slot lit gold, a slot it may go to lit jade, a closed one dim.
func _dock_slot(r: Rect2, closed: bool, on: bool, target: bool) -> void:
	if on: glow(r.grow(12), Color(UiKit.PALE_GOLD, 0.45))
	elif target: glow(r.grow(10), Color(UiKit.BRIGHT_JADE, 0.3))
	rounded(r.grow(1), 6.0, UiKit.INK)
	rounded(r, 5.0, UiKit.PALE_GOLD if on else (UiKit.BRIGHT_JADE if target else Color(UiKit.GOLD, 0.25 if closed else 0.7)))
	rounded(r.grow(-1.5), 4.0, UiKit.SURFACE.space if closed else UiKit.SURFACE.cloth)
	if closed: _lock_icon(r.get_center() - Vector2(6, 8))

## The realm that opens Inner Art slot `i` (slots.json rows: [realm, slots open from it]).
func _slot_realm(i: int) -> String:
	for row in ContentDB.config("inner_arts").get("slots", []):
		if int(row[1]) > i: return str(row[0])
	return "spirit_awakening_1"

# ------------------------------------------------------------------ actions
## Choose node `id`: the tiles holding the one let go and the one chosen are drawn again.
func _choose(id: String) -> void:
	if id == sel: return
	_stale_node(sel)
	sel = id
	_stale_node(sel)

func on_action(id: String, data) -> void:
	var ch = c()
	queue_redraw()
	match id:
		"_tab":
			_choose("")
			drawer = false
			goal = Vector2.ZERO
			view = Vector2.ZERO
			_dirty = true
			last_tab = str(data)
		"family": _jump(int(data))
		"node":
			_choose(str(data))
			drawer = false
			if _is_tree(): last_tab = _tab_id()
		"next_learned":
			var learned := _learned()
			if learned.is_empty(): return
			_learned_i = (_learned_i + 1) % learned.size()
			var it: Dictionary = learned[_learned_i]
			_choose(str(it.id))
			drawer = false
			_glide(it.at - CHART.size * 0.5 + Vector2(0, CARD.y * 0.5))
		"learn":
			var it2: Dictionary = _state(_by[str(data)]) if _by.has(str(data)) else {}
			for nid in it2.get("learn", [str(data)]):
				if not submit({"type": "realise_node", "node": str(nid)}).get("ok", false): break
			Audio.ui("ui_confirm")
		"let_go": submit({"type": "unrealise_node", "node": str(data)})
		"reset": ask(Tx.t("ui.techniques.reset_ask") % str(tabs[tab].label), "reset_yes", data, true)
		"reset_yes": submit({"type": "reset_tree", "tree": str(data)})
		"slot":
			var cur = ch.cultivator.technique_slots[int(data)]
			if sel != "" and ch.cultivator.techniques_known.has(sel) and (cur == null or str(cur) != sel):
				submit({"type": "equip_technique", "slot": int(data), "id": sel})
			elif cur != null:
				_choose(str(cur))
				drawer = false
		"slot_sel":
			var at := _slot_of(ch, str(data))
			if at >= 0: submit({"type": "unequip_technique", "slot": at})
			else:
				var n := ProgressionRules.technique_slot_count(ch)
				var free := -1
				for i in n:
					if ch.cultivator.technique_slots[i] == null and TechniqueTreeRules.heavy_fits(ch.cultivator.technique_slots, i, str(data)):
						free = i
						break
				if free >= 0: submit({"type": "equip_technique", "slot": free, "id": str(data)})
				else: flash(Tx.t("ui.techniques.tap_a_slot_to_equip"))
		"rank": submit({"type": "rank_up_technique", "id": str(data)})
		"lost_act":
			lost_act = int(data)
			sel = ""
		"lost", "secret_art": sel = str(data)
		"sealed": flash(Tx.t("ui.techniques.sealed"))
		"read":
			var idx: int = ch.inventory.first_index(str(data))
			if idx >= 0: submit({"type": "use_item", "index": idx, "confirm": true})
		"wear":
			var worn: int = ch.cultivator.inner_arts.find(str(data))
			submit({"type": "equip_inner_art", "slot": worn if worn >= 0 else _free_inner(ch), "art": "" if worn >= 0 else str(data)})
		"drawer": drawer = not drawer
		"pick_art": picked_art = "" if picked_art == str(data) else str(data)
		"false_realm": submit({"type": "set_false_realm", "realm": str(data)})
		"art_slot":
			var cur_art := str(ch.cultivator.inner_arts[int(data)]) if int(data) < ch.cultivator.inner_arts.size() else ""
			if picked_art != "":
				submit({"type": "equip_inner_art", "slot": int(data), "art": picked_art})
				picked_art = ""
			elif cur_art != "" and drawer:
				submit({"type": "equip_inner_art", "slot": int(data), "art": ""})
			else: drawer = true
		"stance":
			var st := ContentDB.entry("stances", str(data))
			var on := str(ch.cultivator.stances.get(str(st.family), "")) == str(data)
			submit({"type": "set_stance", "family": str(st.family), "stance": "" if on else str(data)})
