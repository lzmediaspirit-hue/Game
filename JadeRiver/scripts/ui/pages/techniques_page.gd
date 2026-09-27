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
## (tree_tabs, tree_view, node_needs, lost_arts_view, lost_unread) and submits intents only.

const Avatar = preload("res://scripts/avatar.gd")
const LEFT := Rect2(12, 70, 216, 580)
const MID := Rect2(236, 70, 660, 580)
const RIGHT := Rect2(904, 70, 364, 580)
const CHART := Rect2(241, 75, 650, 570)     # the tree's window on its chart
const VIS := Rect2(241, 127, 650, 518)      # the part of it under the chart's head strip
const DOCK := Rect2(0, 656, 1280, 64)
var rail_tone := UiKit.SURFACE.cloth.lerp(UiKit.SURFACE.space, 0.6)   # the lacquer rail at its lightest
const FAM_W := 600.0                        # a family's column: three lanes 200 apart
const LANE := 200.0
const ROW_H := 132.0                        # a ring's row
const NOTE_H := 80.0                        # the notables' band after an act's last ring
const GATE_TOP := 24.0                      # the gate row (the Dao arts) at the chart's top
const CARD := Vector2(190, 115)
const PIC := 76.0
const FEET := Vector2(120, 646)
const ROMAN := ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]
const KINDS := {"technique": "ui.techniques.kind_technique", "inner": "ui.techniques.kind_inner", "secret": "ui.techniques.kind_secret"}

static var last_tab := ""     # the page opens on the tab of the art last chosen
var sel := ""                 # the chosen node, art, lost art or secret art
var view := Vector2.ZERO      # the chart's offset in view
var goal := Vector2.ZERO      # where the view is gliding to
var lost_act := 1             # the Lost Arts leaf shown (0: the lineages)
var drawer := false           # the reading shows the Inner Arts and stances
var picked_art := ""          # an Inner Art chosen to wear: tap a slot
var doll: Node2D              # the character under the chooser
var pic: Node2D               # the character in the chosen art's pose
var _laid := ""               # the tree laid out in _items
var _rz := {}                 # the Realisations pool: {total, spent, free}
var _realised_here := 0       # nodes realised on this tree
var _items: Array = []        # the tree laid out: [{id, kind, at, state, ...}]
var _by := {}                 # id -> item
var _size := Vector2.ZERO     # the chart's size
var _rows := {}               # ring -> row top; "n<act>" -> the notables' band
var _dirty := true
var _pan := false
var _learned_i := -1

func _init() -> void:
	title = Tx.t("ui.techniques.techniques")
	frame_rect = WINDOW_SCREEN
	identity = Identity.new("space", false, "own", "seal_rail_chart_three_panels_dock", 0.3)

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
	for k in ["doll", "pic"]:
		var a := Avatar.new()
		a.visible = false
		a.externally_timed = k == "pic"
		add_child(a)
		set(k, a)
	_dress()
	var want := last_tab
	if want == "" and ch != null:
		var first = ch.cultivator.technique_slots[0] if not ch.cultivator.technique_slots.is_empty() else null
		want = TechniqueTreeRules.tree_of_element(str(ContentDB.entry("techniques", str(first)).get("element", "none"))) if first != null else "water"
	for i in tabs.size():
		if str(tabs[i].id) == want and str(tabs[i].get("locked", "")) == "": tab = i
	if args.has("tab"): last_tab = str(args.tab)

func _dress() -> void:
	if c() == null: return
	for a in [doll, pic]:
		a.outfit = InventoryAuthority.outfit_for(c())
		a.last_key = ""
	doll.play("idle")

func on_event(name: String, _p: Dictionary) -> void:
	if name == "equipment_changed": _dress()
	for k in ["tree_", "technique_", "lost_", "dao", "realm", "item_", "inner_art", "stance", "level", "breakthrough"]:
		if name.begins_with(k): _dirty = true
	queue_redraw()

func _tab_id() -> String:
	return str(tabs[tab].id) if tab < tabs.size() else ""

func _is_tree() -> bool:
	return not _tab_id() in ["lost", "secret", ""]

# ------------------------------------------------------------------ input: the chart pans under a finger
func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_pan = event.pressed and _is_tree() and CHART.has_point(event.position) and confirm.is_empty()
	elif event is InputEventMouseButton and event.pressed and _is_tree() and CHART.has_point(event.position) and event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
		_glide(view + Vector2(0, -90.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 90.0), true)
		accept_event()
		return
	elif event is InputEventMouseMotion and _pan and event.button_mask & MOUSE_BUTTON_MASK_LEFT and (event.position - _press_pos).length() > 10.0:
		_dragged = true
		_pressed = -1
		_glide(view - event.relative, true)
	super._gui_input(event)

func _process(delta: float) -> void:
	super._process(delta)
	if view != goal: view = goal if UiKit.reduce_motion() or view.distance_to(goal) < 1.0 else view.lerp(goal, minf(1.0, delta * 12.0))

## Move the view (clamped to the chart); `now` skips the glide (a drag).
func _glide(to: Vector2, now := false) -> void:
	goal = Vector2(clampf(to.x, 0.0, maxf(0.0, _size.x - CHART.size.x)), clampf(to.y, 0.0, maxf(0.0, _size.y - CHART.size.y)))
	if now: view = goal

## Centre the view on a family's column, at the rows around `ring` (its first by default).
func _jump(fam_i: int, y := -1.0, now := false) -> void:
	var at_y: float = y if y >= 0.0 else float(_rows.get(TechniqueTreeRules.first_ring(_tab_id()), 0.0)) - (VIS.position.y - CHART.position.y) - 1.0
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
	for d in Game.progression.tree_dao_arts(ch, tree): _by[str(d.id)].state = str(d.state)
	_rz = Game.progression.realisations(ch)
	_realised_here = 0
	for tb in Game.progression.tree_tabs(ch):
		if str(tb.tree) == tree: _realised_here = int(tb.realised)

func _lay_out(ch, tree: String) -> void:
	_laid = tree
	_items.clear()
	_by.clear()
	var T = TechniqueTreeRules
	var fams: Array = T.sectors()
	var y := GATE_TOP + ROW_H + 16.0
	_rows = {}
	for r in range(T.first_ring(tree), T.edge_ring(int(T.config().get("act_open", 3))) + 1):
		_rows[r] = y
		y += ROW_H
		if T.is_edge(r):
			_rows["n%d" % T.act_of(r)] = y
			y += NOTE_H
	_size = Vector2(fams.size() * FAM_W, y + 24.0)
	var taken := {}
	var col := func(fam: String) -> float: return fams.find(fam) * FAM_W + FAM_W * 0.5
	var place := func(it: Dictionary, fam: String, ring: int, lanes: Array) -> void:
		for ln in lanes:
			if taken.has("%s|%d|%d" % [fam, ring, ln]): continue
			taken["%s|%d|%d" % [fam, ring, ln]] = true
			it.at = Vector2(col.call(fam) + ln * LANE, float(_rows.get(ring, GATE_TOP)))
			break
		if not it.has("at"): it.at = Vector2(col.call(fam) + 2.0 * LANE, float(_rows.get(ring, GATE_TOP)))
	# The open acts' nodes from the cells themselves, keystones first so they take their lane before the arts.
	var add := func(it: Dictionary) -> void:
		_items.append(it)
		_by[str(it.id)] = it
	var open_act := int(T.config().get("act_open", 3))
	for act in range(1, open_act + 1):
		for kin in ["voice", "edges", "reach", "distance"]:
			var k: String = T.keystone_at(tree, kin, act)
			if k == "" or not _rows.has(T.edge_ring(act)): continue
			var kit := {"id": k, "kind": "keystone", "kin": kin, "family": str(T.kin_sectors(kin)[0]), "ring": T.edge_ring(act)}
			place.call(kit, kit.family, kit.ring, [1, -1, 0])
			add.call(kit)
	for f in fams:
		for ring in _rows:
			if str(ring).begins_with("n"): continue
			add.call({"id": T.passage(tree, f, ring), "kind": "passage", "family": f, "ring": ring, "at": Vector2(col.call(f), float(_rows[ring]) - 9.0)})
			var cl: Dictionary = T.cell(tree, f, ring)
			var side := -1 if int(ring) % 2 == 0 else 1
			for slot in ["o", "p"]:
				for id in cl[slot]:
					var it := {"id": str(id), "kind": "art", "family": f, "ring": ring}
					place.call(it, f, ring, [0, side, -side] if slot == "o" else [side, -side, 0])
					add.call(it)
			if T.is_edge(ring):
				add.call({"id": T.notable(tree, f, T.act_of(ring)), "kind": "notable", "family": f, "ring": ring, "at": Vector2(col.call(f), float(_rows["n%d" % T.act_of(ring)]) + 32.0)})
	for d in Game.progression.tree_dao_arts(ch, tree):
		var it2 := {"id": str(d.id), "kind": "dao", "family": str(d.family), "dao": str(d.dao), "dao_tier": int(d.tier), "ring": 0, "state": str(d.state)}
		place.call(it2, it2.family, 0, [-1, 1, 0])
		add.call(it2)
	for it in _items:
		var kind := str(it.kind)
		var pts: Array = []
		match kind:
			"passage":
				# In from the ring before (from under its act's notable after an act's last ring), or from the gate.
				var r := int(it.ring)
				var up := Vector2(it.at.x, GATE_TOP + 62.0)
				if _rows.has(r - 1): up = _by[T.notable(tree, str(it.family), T.act_of(r - 1)) if T.is_edge(r - 1) else T.passage(tree, str(it.family), r - 1)].at
				pts = [up, it.at]
			"notable":
				pts = [_by[T.passage(tree, str(it.family), int(it.ring))].at, it.at]
				if fams.find(str(it.family)) + 1 < fams.size(): it.chan = true
			"dao": pts = [Vector2(it.at.x, it.at.y + PIC * 0.5), Vector2(col.call(str(it.family)), it.at.y + PIC * 0.5)]
			_:
				var pa: Vector2 = _by[T.passage(tree, str(it.family) if kind == "art" else str(T.kin_sectors(str(it.kin))[0]), int(it.ring))].at
				pts = [pa, Vector2(it.at.x, pa.y), it.at - Vector2(0, 3)]
		it.route = pts
		var box := Rect2(it.at, Vector2.ZERO)
		for pt in pts: box = box.expand(pt)
		if it.get("chan", false): box = box.expand(it.at + Vector2(FAM_W, 0))
		if not kind in ["passage", "notable"]:
			box = box.merge(Rect2(it.at - Vector2(CARD.x * 0.5, 0), CARD))
			it.name = str(ContentDB.entry("techniques", str(it.id)).get("name", it.id))
		it.box = box.grow(14)
	if goal == Vector2.ZERO and view == Vector2.ZERO: _jump(0, -1.0, true)

## A node as the character stands to it, asked of the authority when it is first drawn after a change: its state, why
## it is closed, its cost and what learning it takes; with its tag and a learned art's tier.
func _state(it: Dictionary) -> Dictionary:
	if not it.has("state"): it.merge(Game.progression.tree_node(c(), str(it.id)), true)
	if not it.has("tag") or it.get("tag_of", "") != str(it.state) + str(it.get("why", "")):
		it.tag = _tag(it)
		it.tag_of = str(it.state) + str(it.get("why", ""))
	it.tier = int(c().cultivator.mastery.get(str(it.id), {}).get("tier", 1))
	return it

func _slot(id: String) -> String:
	return str(TechniqueTreeRules.home(id).get("slot", "o"))

## The screen point of a chart point.
func _on_screen(p: Vector2) -> Vector2:
	return (CHART.position - view + p).round()

func _fam_at_view() -> String:
	var fams: Array = TechniqueTreeRules.sectors()
	return str(fams[clampi(int((view.x + CHART.size.x * 0.5) / FAM_W), 0, fams.size() - 1)]) if not fams.is_empty() else "any"

# ------------------------------------------------------------------ the surface: ground, chart, rail
## The ground and, on a tree tab, the chart with what is in view (drawn here, under the title and the seals, so the
## rail and the panels' rims close over the chart's edges), then the rail.
func draw_surface(r: Rect2) -> void:
	draw_rect(r, UiKit.SURFACE.space)
	ground(r, UiKit.SURFACE.space)
	glow(Rect2(MID.position - Vector2(80, 40), MID.size + Vector2(160, 80)), Color(UiKit.JADE_SHADOW, 0.22))
	face(MID, "carved_panel")
	if c() != null and _is_tree():
		if _dirty: _refresh()
		_chart()
		for m in [Rect2(0, 0, 1280, MID.position.y), Rect2(0, MID.end.y, 1280, 720 - MID.end.y), Rect2(0, 0, MID.position.x, 720), Rect2(MID.end.x, 0, 1280 - MID.end.x, 720)]:
			draw_rect(m, UiKit.SURFACE.space)
		face(MID, "carved_panel", "frame")
	_band(Rect2(0, 0, 1280, 64), rail_tone, UiKit.SURFACE.space)
	draw_line(Vector2(0, 64), Vector2(1280, 64), UiKit.GOLD, 1.0)
	draw_line(Vector2(0, 65.5), Vector2(1280, 65.5), UiKit.INK, 2.0)
	ground(Rect2(0, 0, 1280, 64), rail_tone)

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
	draw_texture_rect(UiKit.hd_texture("tech_seal", str(tabs[i].id)), Rect2(c0 - Vector2(22, 22), Vector2(44, 44)), false, UiKit.HOLLOW if state == "disabled" else Color.WHITE)
	text(Vector2(r.position.x - 12, r.position.y + 57), str(tabs[i].label), 14, UiKit.PALE_GOLD if state == "selected" else (UiKit.HOLLOW if state == "disabled" else UiKit.MIST),
		HORIZONTAL_ALIGNMENT_CENTER, r.size.x + 24)

# ------------------------------------------------------------------ the chart
## The element's own chart under the tree (the Water tab a tide chart: depth contours between the rings, currents
## down between the lanes, sounded on the right), then the routes, the passages and notables, and the cards in view.
func _chart() -> void:
	var tree := _tab_id()
	var el := str(TechniqueTreeRules.tree_def(tree).get("element", "none"))
	var ec := SpriteCache.element_color(el)
	ground(CHART, UiKit.SURFACE.space)
	glow(Rect2(CHART.position + Vector2(-60, 40), CHART.size + Vector2(120, 80)), Color(ec, 0.07))
	var ox := fposmod(view.x, FAM_W)
	for k in 3:
		for lane in [-0.3, 0.3]:
			var x: float = CHART.position.x - ox + (k + 0.5 + lane * 0.5) * FAM_W
			if x < CHART.position.x or x > CHART.end.x: continue
			var pts := PackedVector2Array()
			for s in 16:
				var yy := CHART.position.y + s * CHART.size.y / 15.0
				pts.append(Vector2(x + sin((yy + view.y) * 0.011 + k) * 12.0, yy))
			draw_polyline(pts, Color(ec, 0.1), 1.2, true)
	for key in _rows:
		var yy := float(_rows[key]) - 24.0 - view.y + CHART.position.y
		if yy < CHART.position.y or yy > CHART.end.y or str(key).begins_with("n"): continue
		var pts2 := PackedVector2Array()
		for s in 27: pts2.append(Vector2(CHART.position.x + s * 25.0, yy + sin((s * 25.0 + view.x) * 0.02) * 3.0))
		draw_polyline(pts2, Color(UiKit.MIST, 0.16), 1.0, true)
	var vr := Rect2(view, CHART.size)
	# Routes first (the passage line down each column, a passage to the arts of its ring, an act's last passage to its
	# notable, the notables' channels, a kin group's passage to its keystone), then the passages and notables.
	draw_set_transform(CHART.position - view)
	var fams: Array = TechniqueTreeRules.sectors()
	var seen: Array = _items.filter(func(it): return vr.intersects(it.box))
	for it in seen: _state(it)
	for it in seen:
		_route(it.route, _state_col(it), str(it.state) == "locked", str(it.kind) in ["art", "keystone"])
		if it.get("chan", false): _route([it.at, it.at + Vector2(FAM_W, 0)], Color(UiKit.GOLD, 0.45), true)
	for it in seen:
		if str(it.kind) == "passage": _diamond(it.at, 7.0, it)
		elif str(it.kind) == "notable": _diamond(it.at, 13.0, it)
	# Each family's gate: its weapon's sign in a ring at the column's head.
	for i in fams.size():
		var g := Vector2(i * FAM_W + FAM_W * 0.5, GATE_TOP + 38.0)
		if not vr.has_point(g): continue
		draw_circle(g, 26.0, UiKit.INK, true, -1.0, true)
		draw_circle(g, 24.0, UiKit.SURFACE.cloth, true, -1.0, true)
		draw_circle(g, 24.0, UiKit.GOLD, false, 2.0, true)
	draw_set_transform(Vector2.ZERO)
	var aid := "chart"
	_areas[aid] = {"rect": VIS, "max": 0.0, "active": true}
	for i in fams.size():
		var g2 := _on_screen(Vector2(i * FAM_W + FAM_W * 0.5, GATE_TOP + 38.0))
		if VIS.has_point(g2): icon_at(Rect2(g2 - Vector2(16, 16), Vector2(32, 32)), _fam_icon(str(fams[i])))
	for it in seen:
		var s := _on_screen(it.at)
		if str(it.kind) in ["passage", "notable"]:
			if VIS.has_point(s): region(Rect2(s - Vector2(10, 10), Vector2(20, 20)), "node", str(it.id))
			continue
		var rect := Rect2(s - Vector2(CARD.x * 0.5, 0), CARD)
		if rect.intersects(CHART): _card(it, rect)
	_areas[aid].active = false
	_chart_labels(ec)

## The ring soundings down the chart's right edge; the head strip over the chart: the rings in view, the family in view
## on its plaque, Learned (the next learned art) and Let all go (the tree's reset).
func _chart_labels(_ec: Color) -> void:
	var T = TechniqueTreeRules
	var lo := 99
	var hi := 0
	for key in _rows:
		if str(key).begins_with("n"): continue
		var y := float(_rows[key]) - view.y + CHART.position.y
		if y + 60 < VIS.position.y or y > VIS.end.y - 20: continue
		lo = mini(lo, int(key))
		hi = maxi(hi, int(key))
		var g := str(T.ring_row(int(key)).get("grade", "common"))
		if y + 14 >= VIS.position.y and y + 64 <= VIS.end.y:
			text(Vector2(VIS.end.x - 66, y + 40), ROMAN[int(key)], 26, Color(UiKit.MIST, 0.85), HORIZONTAL_ALIGNMENT_CENTER, 60, true)
			text(Vector2(VIS.end.x - 72, y + 60), Tx.t("ui.techniques.grade_" + g), 14, UiKit.grade_color(g), HORIZONTAL_ALIGNMENT_CENTER, 72)
	var head := Rect2(CHART.position, Vector2(CHART.size.x, VIS.position.y - CHART.position.y))
	_band(head, UiKit.SURFACE.cloth, UiKit.SURFACE.space)
	draw_line(Vector2(head.position.x, head.end.y), head.end, Color(UiKit.GOLD, 0.6), 1.0)
	ground(head, UiKit.SURFACE.cloth)
	var plq := Rect2(VIS.position.x + 176, 80, 250, 34)
	face(plq, "jade_label")
	inked(Vector2(plq.position.x, plq.position.y + 25), Tx.t("ui.techniques.arts_of_" + _fam_at_view()) % str(tabs[tab].label), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plq.size.x)
	if hi >= lo: text(Vector2(VIS.position.x + 12, 104), Tx.t("ui.techniques.act_rings") % [ROMAN[T.act_of(lo)], ROMAN[lo], ROMAN[hi]], 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 172)
	btn(Rect2(VIS.end.x - 216, 77, 86, 48), Tx.t("ui.techniques.next_learned"), "next_learned", null, false, not _learned().is_empty(), Tx.t("ui.techniques.none_learned"), 16)
	btn(Rect2(VIS.end.x - 124, 77, 120, 48), Tx.t("ui.techniques.let_all_go"), "reset", _tab_id(), false, _realised_here > 0, Tx.t("sim.tree.nothing"), 16)

func _state_col(it: Dictionary) -> Color:
	match str(it.get("state", "")):
		"realised", "taught": return UiKit.BRIGHT_JADE
		"open": return UiKit.GOLD
	return UiKit.HOLLOW

## A route through `pts` (chart space) in the colour of the node it leads to; dashed while that node is locked, with an
## arrowhead into a card.
func _route(pts: Array, col: Color, dashed: bool, arrow := false) -> void:
	for i in pts.size() - 1:
		var a: Vector2 = pts[i]
		var b: Vector2 = pts[i + 1]
		draw_line(a, b, UiKit.INK, 5.0)
		if dashed: draw_dashed_line(a, b, col, 2.4, 6.0)
		else: draw_line(a, b, col, 2.4, true)
	if arrow:
		var tip: Vector2 = pts[-1]
		draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-5, -8), tip + Vector2(5, -8)]), col)

## A passage (a small diamond) or a notable (a large one, an anchor of the act): jade when realised, gold ringed when
## open, slate when locked; the chosen one haloed.
func _diamond(at: Vector2, r: float, it: Dictionary) -> void:
	var st := str(it.state)
	var fill: Color = UiKit.JADE if st == "realised" else (UiKit.SURFACE.cloth if st == "open" else UiKit.SURFACE.space)
	var pts := PackedVector2Array([at + Vector2(0, -r), at + Vector2(r, 0), at + Vector2(0, r), at + Vector2(-r, 0)])
	if sel == str(it.id): glow(Rect2(at - Vector2(r, r) * 2.4, Vector2(r, r) * 4.8), Color(UiKit.PALE_GOLD, 0.5))
	draw_colored_polygon(pts, fill)
	pts.append(pts[0])
	draw_polyline(pts, UiKit.INK, 4.0, true)
	draw_polyline(pts, UiKit.PAPER if st == "realised" else _state_col(it), 1.6, true)
	if str(it.kind) == "notable": draw_circle(at, r * 0.35, _state_col(it), true, -1.0, true)

## A node card: the art's emblem in its frame (jade learned, gold open, slate locked, a keystone in a gold double frame),
## its name and its state under it. Only words wholly inside the chart are written.
func _card(it: Dictionary, rect: Rect2) -> void:
	var id := str(it.id)
	var st := str(it.state)
	var learned := st in ["realised", "taught"]
	var p := Rect2(rect.position + Vector2((CARD.x - PIC) * 0.5, 0), Vector2(PIC, PIC))
	if sel == id: glow(p.grow(22), Color(UiKit.PALE_GOLD, 0.45))
	rounded(p.grow(1), 5.0, UiKit.INK)
	rounded(p, 4.0, _state_col(it) if sel != id else UiKit.PALE_GOLD)
	rounded(p.grow(-2), 3.0, UiKit.INK)
	if str(it.kind) == "keystone": draw_rect(p.grow(3), UiKit.GOLD, false, 1.5)
	icon_at(p.grow(-6), id, Color.WHITE if st != "locked" else UiKit.MIST)
	if learned:
		var tier := int(it.tier)
		var d := p.end - Vector2(4, 4)
		draw_colored_polygon(PackedVector2Array([d + Vector2(0, -11), d + Vector2(11, 0), d + Vector2(0, 11), d + Vector2(-11, 0)]), UiKit.JADE_SHADOW)
		text(d + Vector2(-11, 5), str(tier), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 22)
	var name_r := Rect2(rect.position + Vector2(0, 78), Vector2(CARD.x, 18))
	if VIS.encloses(name_r):
		ground(name_r.grow(4), UiKit.SURFACE.space)
		text(Vector2(rect.position.x, rect.position.y + 92), str(it.name), 16, UiKit.PALE_GOLD if sel == id else (UiKit.PAPER if st != "locked" else UiKit.HOLLOW), HORIZONTAL_ALIGNMENT_CENTER, CARD.x)
	var tag := str(it.tag)
	var tw := UiKit.text_width(tag, 14) + 22.0
	var tr := Rect2(rect.get_center().x - tw * 0.5, rect.position.y + 96, tw, 19)
	if VIS.encloses(tr):
		rounded(tr, 9.0, UiKit.INK)
		rounded(tr.grow(-1), 8.0, _state_col(it))
		rounded(tr.grow(-2), 7.0, UiKit.SURFACE.cloth if learned else UiKit.SURFACE.space)
		ground(tr, UiKit.SURFACE.cloth if learned else UiKit.SURFACE.space)
		text(Vector2(tr.position.x, tr.position.y + 15), tag, 14, UiKit.BRIGHT_JADE if learned else (UiKit.PALE_GOLD if st == "open" else UiKit.MIST), HORIZONTAL_ALIGNMENT_CENTER, tw)
	region(Rect2(rect.position.x + 20, rect.position.y, CARD.x - 40, CARD.y), "node", id)

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
	draw_texture_rect(UiKit.hd_texture("tech_seal", seal), Rect2(24, 80, 34, 34), false)
	heading(Vector2(66, 106), name, 150)
	if mark: _rz_mark(Vector2(33, 127))
	text(Vector2(26 + (16 if mark else 0), 132), a, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 196)
	text(Vector2(26, 152), b, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 196)

## The character under the chooser.
func _figure() -> void:
	glow(Rect2(FEET + Vector2(-80, -12), Vector2(160, 28)), Color(UiKit.BRIGHT_JADE, 0.25))
	doll.draw_on(self, FEET, 2.0)

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
	var here := _fam_at_view()
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
	var r := Rect2(RIGHT.position.x + 20, 80, 324, 34)
	face(r, "jade_label")
	inked(Vector2(r.position.x, r.position.y + 25), name, 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	ground(Rect2(RIGHT.position, Vector2(RIGHT.size.x, 60)).grow(-4), UiKit.SURFACE.cloth)
	rich(Rect2(RIGHT.position.x + 16, 118, 332, 20), runs, 14, true)

## The picture: the character in the art's pose on its element's ground, in a gold frame.
func _picture(t: Dictionary, action := "") -> void:
	var r := Rect2(922, 142, 150, 150)
	rounded(r.grow(2), 5.0, UiKit.INK)
	rounded(r, 4.0, UiKit.GOLD)
	rounded(r.grow(-3), 3.0, UiKit.INK)
	var ec := SpriteCache.element_color(str(t.get("element", "none")))
	glow(Rect2(r.position + Vector2(-10, 10), Vector2(170, 150)), Color(ec, 0.35))
	draw_line(Vector2(r.position.x + 6, r.end.y - 16), Vector2(r.end.x - 6, r.end.y - 16), Color(ec, 0.6), 1.5)
	pic.play(action if action != "" else _pose(t))
	pic.elapsed = 0.3
	# A stroke reaches forward, so its figure stands back to keep the blade in the frame; a still one stands centred.
	pic.draw_on(self, Vector2(r.position.x + (75.0 if str(pic.action) in ["idle", "meditate"] else 44.0), r.end.y - 18), 1.0)

## The body pose an art is shown in: its own action, or a combo step of the family's (the free hand's, of the weapon in
## hand), when every layer the character wears has it; else the idle stance.
func _pose(t: Dictionary) -> String:
	var pose := str(t.get("vfx", {}).get("pose", t.get("action", "idle")))
	if pose.begins_with("combo_"):
		var fam := str(t.get("family", "any"))
		if fam == "any": fam = str(StatRules.family(c()).get("id", "fists"))
		var combo: Array = ContentDB.entry("weapon_families", fam).get("combo", [])
		pose = str(combo[mini(int(pose.right(1)) - 1, combo.size() - 1)].action) if not combo.is_empty() else "idle"
	for cat in pic.outfit:
		var item: Dictionary = Wardrobe.parts.get(cat, {}).get(str(pic.outfit[cat]), {}) if cat in Wardrobe.CATEGORIES else {}
		for layer in item.get("layers", []):
			if not layer.animations.has(pose): return "idle"
	return pose

## The facts beside the picture: the emblem, its form and element or family, then the numbers.
func _facts(id: String, t: Dictionary, lines: Array) -> void:
	icon_at(Rect2(1090, 142, 64, 64), id)
	var form := str(t.get("form", t.get("template", "")))
	text(Vector2(1164, 164), Tx.t("ui.techniques.form_" + form) if form != "" else Tx.t("ui.techniques.kind_technique"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 96)
	text(Vector2(1164, 184), Tx.t("ui.techniques.fam_" + str(t.get("family", "any"))) if str(t.get("family", "any")) != "any" else str(tabs[tab].label) if _is_tree() else "", 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 96)
	for i in lines.size(): rich(Rect2(1090, 214 + i * 22, 170, 20), lines[i], 16)

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
	_rule(370)
	if known: _read_known(ch, t, it)
	else: _read_learn(ch, t, it)

func _kind_line(t: Dictionary) -> String:
	match str(t.get("kind", "")):
		"keystone": return Tx.t("ui.techniques.keystone_of") % ContentDB.text("technique.kin." + str(t.get("kin", "voice")))
		"dao": return Tx.t("ui.techniques.dao_art")
	return Tx.t("ui.techniques.path_art_of" if str(t.get("path", "")) != "" else "ui.techniques.orthodox_of") % Tx.t("ui.techniques.fam_" + str(t.get("family", "any")))

func _rule(y: float) -> void:
	draw_line(Vector2(916, y), Vector2(1256, y), Color(UiKit.GOLD, 0.6), 1.0)

## An art not yet learned: its prerequisites ticked and crossed, the cost, and Learn naming the Realisations it spends.
func _read_learn(ch, t: Dictionary, it: Dictionary) -> void:
	heading(Vector2(920, 400), Tx.t("ui.techniques.prerequisites"), 330)
	var y := 410.0
	if str(it.get("kind", "")) == "dao":
		_need(y, "dao", Tx.t("ui.techniques.dao_tier") % [ContentDB.name_of("daos", str(it.dao)), int(it.dao_tier)], "%d / %d" % [int(ch.cultivator.daos.get(str(it.dao), {}).get("tier", 0)), int(it.dao_tier)], false)
		_rule(518)
		para(Rect2(920, 520, 332, 110), Tx.t("ui.techniques.dao_taught"), 16, UiKit.MIST)
		return
	for n in Game.progression.node_needs(ch, sel):
		_need(y, str(n.kind), _need_text(n), _need_value(ch, n), bool(n.ok))
		y += 36.0
	_rule(518)
	heading(Vector2(920, 548), Tx.t("ui.techniques.cost"), 70)
	var rz: Dictionary = Game.progression.realisations(ch)
	var total := int(it.get("total", TechniqueTreeRules.cost(sel)))
	_rz_mark(Vector2(1000, 538))
	rich(Rect2(1012, 528, 250, 20), [[str(total) + " ", UiKit.PALE_GOLD], [Tx.t("ui.techniques.realisations_of") % int(rz.free), UiKit.MIST]], 16)
	rich(Rect2(1000, 550, 250, 20), [[str(int(round(Game.combat.technique_cost(ch, t)))) + " ", UiKit.QI], [Tx.t("ui.techniques.qi_each"), UiKit.MIST]], 16)
	_learn_btn(it, total)

## Learn: primary, naming what it spends; closed, it carries the lock and says why under it.
func _learn_btn(it: Dictionary, total: int) -> void:
	var ok := str(it.get("state", "")) == "open"
	var why := "" if ok else Tx.t("sim.tree." + str(it.get("why", "route")))
	btn(Rect2(950, 574, 272, 52), Tx.plural("ui.techniques.learn_for", total) % total, "learn", sel, true, ok, why, 22)
	if not ok: text(Vector2(916, 642), why, 14, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_CENTER, 340)

func _rz_mark(at: Vector2) -> void:
	draw_colored_polygon(PackedVector2Array([at + Vector2(0, -7), at + Vector2(7, 0), at + Vector2(0, 7), at + Vector2(-7, 0)]), UiKit.PALE_GOLD)
	draw_colored_polygon(PackedVector2Array([at + Vector2(0, -5), at + Vector2(5, 0), at + Vector2(0, 5), at + Vector2(-5, 0)]), UiKit.JADE)

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
		else Tx.t("ui.techniques.gives_cost") % [roundi(-float(k.get("passage_cost", -0.02)) * 100), str(tabs[tab].label), fam])
	para(Rect2(920, 150, 332, 120), what + " " + Tx.t("ui.techniques.notable_help" if notable else "ui.techniques.passage_help"), 16, UiKit.PAPER)
	_rule(370)
	if str(it.state) == "realised":
		heading(Vector2(920, 400), Tx.t("ui.techniques.realised"), 330)
		para(Rect2(920, 416, 332, 80), Tx.t("ui.techniques.let_go_help"), 16, UiKit.MIST)
		btn(Rect2(950, 574, 272, 52), Tx.t("ui.techniques.let_go_for") % int(it.cost), "let_go", sel, false, true, "", 20)
		return
	heading(Vector2(920, 400), Tx.t("ui.techniques.prerequisites"), 330)
	var y := 410.0
	for n in Game.progression.node_needs(ch, sel):
		_need(y, str(n.kind), _need_text(n), _need_value(ch, n), bool(n.ok))
		y += 36.0
	_rule(518)
	heading(Vector2(920, 548), Tx.t("ui.techniques.cost"), 70)
	_rz_mark(Vector2(1000, 538))
	rich(Rect2(1012, 528, 250, 20), [[str(int(it.cost)) + " ", UiKit.PALE_GOLD], [Tx.t("ui.techniques.realisations_of") % int(_rz.get("free", 0)), UiKit.MIST]], 16)
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
	face(plq, "jade_label")
	inked(Vector2(plq.position.x, plq.position.y + 25), Tx.t("ui.techniques.act_title") % [ROMAN[lost_act], Tx.t("ui.techniques.act_name_%d" % lost_act)], 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plq.size.x)
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
	face(plq, "jade_label")
	inked(Vector2(plq.position.x, plq.position.y + 25), Tx.t("ui.techniques.lineages"), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plq.size.x)
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
			if tid != null: icon_at(r.grow(-2), str(tid))
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
func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"_tab":
			sel = ""
			drawer = false
			goal = Vector2.ZERO
			view = Vector2.ZERO
			_dirty = true
			last_tab = str(data)
		"family": _jump(int(data))
		"node":
			sel = str(data)
			drawer = false
			if _is_tree(): last_tab = _tab_id()
		"next_learned":
			var learned := _learned()
			if learned.is_empty(): return
			_learned_i = (_learned_i + 1) % learned.size()
			var it: Dictionary = learned[_learned_i]
			sel = str(it.id)
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
				sel = str(cur)
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
