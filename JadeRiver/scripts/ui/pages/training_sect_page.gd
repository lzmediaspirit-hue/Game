extends Page
## Training sect (S20): rank, contribution, promotion trials, missions and the sect shop.
## P5 (docs/page_identity.md row 25): the Sect Hall's seats seen from its door. The floor of dark timber recedes between
## red-lacquered pillars to the master's dais at the top centre; the ranks are rows of cushions, nearer rows lower, each
## coloured by its rank; your seat is lit with you sitting on it, and the next rank's row is lit with what it asks and
## the Promotion trial on a board at the right. Missions and the Sect Shop are the hall's two side doors. The Role tab
## turns to the teaching boards on the side walls: the signature line's two variants on the left, the sect tree on the
## right. The rows settle from the dais forward as the page opens; under Reduce motion the page only fades in.

const SectKit = preload("res://scripts/ui/pages/sect_kit.gd")

## The hall in one-point perspective: the back wall round the dais, and the scale of each row of seats (the nearest 1).
const BACK := Rect2(470, 112, 340, 170)
const FRONT_Y := 688.0
const VP_Y := 0.0          # where the rows of seats would meet, far past the dais
const SEATS := 5           # cushions in a row
const ROW_W := 800.0       # a row's width at the front
## Each rank's cushion colour, from the lowest to the Sect Master's (tokens and their mixes).
static var RANK_COL := [UiKit.HOLLOW, UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.5), UiKit.JADE, UiKit.JADE.lerp(UiKit.GOLD, 0.5), UiKit.GOLD,
	UiKit.GOLD.lerp(UiKit.PALE_GOLD, 0.5), UiKit.PALE_GOLD, UiKit.PALE_GOLD]
const NEXT_CARD := Rect2(836, 116, 356, 124)
const DOOR_L := [96.0, 216.0]    # the Missions door's span on the left wall (x)
const DOOR_R := [1064.0, 1184.0] # the Sect Shop's on the right

var figs := {}

func _init() -> void:
	title = Tx.t("ui.training_sect.sect")
	identity = Identity.new("wood_dark", false, "own", "hall_seats_one_point", 0.3)

func setup() -> void:
	var ch = c()
	var joined: bool = ch != null and str(ch.training_sect.get("id", "")) != ""
	var role_ok: bool = joined and RequirementRules.passes({"all": [{"kind": "sect_rank_at_least", "rank": str(ContentDB.config("sect_roles").get("role_rank", "outer_disciple"))}]}, Game.ctx(ch))
	tabs = [{"id": "rank", "label": Tx.t("ui.training_sect.rank_tab")},
		{"id": "role", "label": Tx.t("ui.training_sect.role_tab"), "locked": "" if role_ok else Tx.t("sim.training_sect.role_rank")}]
	# The hall is the sect's own: its full name is the title (the Menu calls it the Sect).
	if joined:
		var sect := ContentDB.entry("sects", str(ch.training_sect.id))
		title = str(sect.get("full_name", sect.get("name", title)))

# ------------------------------------------------------------------ the hall
func draw_surface(r: Rect2) -> void:
	var wall := UiKit.SURFACE.wood_dark
	draw_rect(r, UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.35))
	# The side walls and the ceiling's beams, the floor, the back wall round the dais.
	var tl := r.position
	var tr := Vector2(r.end.x, r.position.y)
	var bl := Vector2(r.position.x, FRONT_Y)
	var br := Vector2(r.end.x, FRONT_Y)
	var btl := BACK.position
	var btr := Vector2(BACK.end.x, BACK.position.y)
	var bbl := Vector2(BACK.position.x, BACK.end.y)
	var bbr := BACK.end
	draw_colored_polygon(PackedVector2Array([tl, btl, bbl, bl]), wall.lerp(UiKit.INK, 0.15))
	draw_colored_polygon(PackedVector2Array([tr, br, bbr, btr]), wall.lerp(UiKit.INK, 0.15))
	draw_colored_polygon(PackedVector2Array([tl, tr, btr, btl]), wall.lerp(UiKit.INK, 0.45))
	for i in range(1, 6):
		var k := float(i) / 6.0
		draw_line(tl.lerp(tr, k), btl.lerp(btr, k), Color(UiKit.INK, 0.4), 3.0, true)
	var floor_pts := PackedVector2Array([bbl, bbr, br, bl])
	draw_polygon(floor_pts, PackedColorArray([wall.lerp(UiKit.INK, 0.3), wall.lerp(UiKit.INK, 0.3), wall, wall]))
	for i in range(0, 13):
		var k := float(i) / 12.0
		draw_line(bbl.lerp(bbr, k), bl.lerp(br, k), Color(UiKit.INK, 0.28), 1.0, true)
	ground(Rect2(bl.x, BACK.end.y, br.x - bl.x, FRONT_Y - BACK.end.y), wall)
	# The back wall and the master's dais with its screen.
	vshade(BACK, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.25), UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.5))
	var screen := Rect2(BACK.get_center().x - 90, BACK.position.y + 56, 180, 70)
	rounded(screen.grow(3), 4.0, UiKit.GOLD.lerp(UiKit.BRONZE, 0.5))
	vshade(screen, UiKit.SURFACE.scroll.lerp(UiKit.GOLD, 0.25), UiKit.SURFACE.scroll.lerp(UiKit.BRONZE, 0.35))
	for x in range(int(screen.position.x) + 45, int(screen.end.x), 45): draw_rect(Rect2(x, screen.position.y, 2, screen.size.y), Color(UiKit.BRONZE, 0.7))
	var dais := Rect2(BACK.position.x + 40, BACK.end.y - 22, BACK.size.x - 80, 22)
	draw_colored_polygon(PackedVector2Array([dais.position, Vector2(dais.end.x, dais.position.y), dais.end + Vector2(18, 0), Vector2(dais.position.x - 18, dais.end.y)]), UiKit.SURFACE.wood)
	draw_rect(Rect2(dais.position, Vector2(dais.size.x, 2)), Color(UiKit.GOLD, 0.6))
	glow(Rect2(BACK.get_center().x - 200, BACK.position.y - 30, 400, 220), Color(UiKit.GOLD, 0.16 * _halo()))
	# The red pillars: a pair flanking the dais, and a pair at the door we look in by.
	for x in [BACK.position.x - 8.0, BACK.end.x - 4.0]: SectKit.pillar(self, Rect2(x, BACK.position.y - 30, 12, BACK.size.y + 34))
	for x in [r.position.x + 6.0, r.end.x - 26.0]: SectKit.pillar(self, Rect2(x, r.position.y + 8, 20, FRONT_Y - r.position.y - 8))
	_doors()

## The scale of a row `j` rows back from the front (0 the nearest, 7 the dais), and where it stands.
static func _scale(j: float) -> float:
	return 1.0 / (1.0 + 0.18 * j)

static func _row_y(j: float) -> float:
	return VP_Y + (FRONT_Y - 12.0 - VP_Y) * _scale(j)

## The two side doors: Missions on the left wall, the Sect Shop on the right, each a dark doorway in a lacquer frame with
## its name on a plaque above.
func _doors() -> void:
	for d in [[DOOR_L, true], [DOOR_R, false]]:
		var q := _door_quad(d[0], d[1])
		draw_colored_polygon(q, UiKit.SURFACE.lacquer)
		var inner := PackedVector2Array([q[0].lerp(q[2], 0.08), q[1].lerp(q[3], 0.08), q[2].lerp(q[0], 0.04), q[3].lerp(q[1], 0.04)])
		draw_colored_polygon(inner, UiKit.INK.lerp(UiKit.SURFACE.wood_dark, 0.3))
		glow(Rect2(q[0].x + (q[1].x - q[0].x) * 0.2 - 10, q[1].y + 40, absf(q[1].x - q[0].x) * 0.8, 120), Color(UiKit.PALE_GOLD, 0.12 * _halo()))

## A door's corners on its wall (top near, top far, foot far, foot near), from its span along the wall.
func _door_quad(span: Array, left: bool) -> PackedVector2Array:
	var near_x: float = span[0] if left else span[1]
	var far_x: float = span[1] if left else span[0]
	var top := func(x: float) -> float: return lerpf(frame_rect.position.y, BACK.position.y, absf(x - (frame_rect.position.x if left else frame_rect.end.x)) / absf(BACK.position.x - frame_rect.position.x))
	var foot := func(x: float) -> float: return lerpf(FRONT_Y, BACK.end.y, absf(x - (frame_rect.position.x if left else frame_rect.end.x)) / absf(BACK.position.x - frame_rect.position.x))
	var h := func(x: float, f: float) -> float: return lerpf(foot.call(x), top.call(x), f)
	return PackedVector2Array([Vector2(near_x, h.call(near_x, 0.58)), Vector2(far_x, h.call(far_x, 0.58)), Vector2(far_x, foot.call(far_x)), Vector2(near_x, foot.call(near_x))])

func title_rect() -> Rect2:
	return Rect2(440, 40, 400, 56)

func draw_title_mount(r: Rect2) -> void:
	SectKit.title_board(self, r)

## The tabs are two lacquer placards hung at the hall's upper left.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	SectKit.lacquer(self, r, state == "selected")
	text(r.position + Vector2(0, 31), str(tabs[i].label), 20, UiKit.PALE_GOLD if state == "selected" else (UiKit.HOLLOW if state == "disabled" else UiKit.PAPER),
		HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var live := {}
	if str(tabs[tab].id) == "role":
		_role(ch)
	else:
		_rank(ch, live)
	SectKit.hide_rest(figs, live if confirm.is_empty() else {})

# ------------------------------------------------------------------ the Rank tab: the seats
func _rank(ch, live: Dictionary) -> void:
	var ts: Dictionary = ch.training_sect
	if str(ts.get("id", "")) == "":
		var board := Rect2(360, 360, 560, 150)
		SectKit.lacquer(self, board)
		para(Rect2(board.position + Vector2(24, 20), board.size - Vector2(48, 40)), Tx.t("ui.training_sect.you_are_unaffiliated_the_jade"), 22, UiKit.PAPER)
		return
	var ranks: Dictionary = ContentDB.config("sect_ranks")
	var order: Array = ranks.get("order", [])
	var mine := order.find(str(ts.get("rank", "")))
	var k := unfold()
	# Your standing, on a tablet hung under the title board.
	var st := Rect2(96, 176, 300, 40)
	SectKit.lacquer(self, st)
	var regard := int(ts.get("reputation", {}).get(str(ts.id), 0))
	var stand := "%s · %s" % [ContentDB.rank_name(str(ts.get("rank", ""))), Tx.t("ui.training_sect.regard") % regard]
	text(st.position + Vector2(0, 27), stand, 18, UiKit.PAPER if regard >= 0 else UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_CENTER, st.size.x)
	currency_pill(Vector2(st.position.x, st.end.y + 10), "contribution", int(ts.get("contribution", 0)))
	# The rows of seats, from the dais forward: the held ranks full, the rest dim, the next one lit.
	for j in range(order.size() - 1, -1, -1):
		var a := clampf(k * 1.6 - (float(j) / order.size()) * 0.6, 0.0, 1.0) if k < 1.0 else 1.0
		_row(j, order, mine, a)
	# You, on your seat.
	if mine >= 0:
		var seat := _seat(mine, SEATS / 2)
		var fig := SectKit.figure(self, figs, "you", InventoryAuthority.outfit_for(ch), 0.5 if mine >= 2 else 1.0, ch)
		SectKit.show(fig, Vector2(seat.get_center().x, seat.position.y + seat.size.y * 0.45), live, "you", clampf(k * 2.0 - 0.5, 0.0, 1.0), "meditate")
	_next(ch, order, ranks, mine)
	_door_words(ch)

## A rank's row: its cushions across the floor at its depth in its colour, its name at the left; the dais is the Sect
## Master's single seat.
func _row(j: int, order: Array, mine: int, a: float) -> void:
	var s := _scale(float(j))
	var y := _row_y(float(j))
	var held := j <= mine
	var next := j == mine + 1
	var col: Color = RANK_COL[mini(j, RANK_COL.size() - 1)]
	if next: glow(Rect2(640 - ROW_W * 0.55 * s, y - 50 * s, ROW_W * 1.1 * s, 80 * s), Color(UiKit.PALE_GOLD, 0.35 * a * _halo()))
	var n := 1 if j == order.size() - 1 else SEATS
	for i in n:
		var r := _seat(j, i)
		var shade: Color = col if held or next else col.lerp(UiKit.SURFACE.wood_dark, 0.6)
		draw_colored_polygon(_cushion(r), Color(UiKit.INK, 0.5 * a))
		draw_colored_polygon(_cushion(r.grow(-1.5 * s)), Color(shade, a))
		draw_line(Vector2(r.position.x + r.size.x * 0.2, r.position.y + r.size.y * 0.35), Vector2(r.end.x - r.size.x * 0.2, r.position.y + r.size.y * 0.35), Color(UiKit.PAPER, 0.25 * a), 1.0, true)
		if j == mine and i == SEATS / 2: glow(r.grow(18 * s), Color(UiKit.PALE_GOLD, 0.5 * a * _halo()))
	var name := ContentDB.rank_name(str(order[j]))
	var size := 16 if s > 0.45 else 14
	var lx := 640.0 - ROW_W * 0.5 * s - 16.0
	if a > 0.5: text(Vector2(lx - 220, y + 6), name, size, UiKit.PALE_GOLD if j == mine else (UiKit.GOLD if held or next else UiKit.MIST), HORIZONTAL_ALIGNMENT_RIGHT, 220)

## The cushion `i` of row `j`: its footprint on the floor.
func _seat(j: int, i: int) -> Rect2:
	var s := _scale(float(j))
	var y := _row_y(float(j))
	var n := SEATS if j < 7 else 1
	var w := ROW_W * s / n
	var x0 := 640.0 - (w * n) * 0.5 if n > 1 else 640.0 - w * 0.12
	var cw := w * 0.64 if n > 1 else w * 0.24
	return Rect2(x0 + i * w + (w - cw) * 0.5 if n > 1 else x0, y - 26.0 * s, cw, 30.0 * s)

## A cushion seen from the door: a rounded quad, wider at its near edge.
func _cushion(r: Rect2) -> PackedVector2Array:
	var inset := r.size.x * 0.08
	return PackedVector2Array([r.position + Vector2(inset, 0), Vector2(r.end.x - inset, r.position.y), Vector2(r.end.x, r.end.y - r.size.y * 0.3), r.end - Vector2(r.size.x * 0.1, 0),
		Vector2(r.position.x + r.size.x * 0.1, r.end.y), Vector2(r.position.x, r.end.y - r.size.y * 0.3)])

## The next rank on a lacquer board at the right: what it asks and its Promotion trial.
func _next(ch, order: Array, ranks: Dictionary, mine: int) -> void:
	if mine + 1 >= order.size(): return
	var rk: Dictionary = ranks.ranks[mine + 1]
	var ok := RequirementRules.passes(rk.get("requires", {}), Game.ctx(ch))
	var r := NEXT_CARD
	SectKit.lacquer(self, r)
	text(r.position + Vector2(16, 28), Tx.t("ui.training_sect.next_rank") % str(rk.name), 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
	text(r.position + Vector2(16, 52), Tx.t("ui.training_sect.ready") if ok else RequirementRules.first_failure_text(rk.get("requires", {}), Game.ctx(ch)), 16,
		UiKit.BRIGHT_JADE if ok else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
	btn(Rect2(r.position.x + 16, r.end.y - 60, r.size.x - 32, BTN_H), Tx.t("ui.training_sect.promotion_trial"), "promote", null, true, ok, Tx.t("ui.training_sect.not_yet"))
	# A leader from the board down to the lit row.
	var y := _row_y(float(mine + 1))
	draw_line(Vector2(r.position.x + 30, r.end.y), Vector2(640.0 + ROW_W * 0.5 * _scale(float(mine + 1)), y - 10), Color(UiKit.PALE_GOLD, 0.35), 1.5, true)

## The side doors' names on their plaques, and their taps: Missions to the Notice Board, the Sect Shop to its stall.
func _door_words(ch) -> void:
	var shop_ok := Unlocks.is_unlocked(ch.id, "contribution_shop")
	for d in [[DOOR_L, true, "missions", Tx.t("ui.training_sect.missions"), true, ""], [DOOR_R, false, "shop", Tx.t("ui.training_sect.sect_shop"), shop_ok, Unlocks.locked_text("contribution_shop")]]:
		var q := _door_quad(d[0], d[1])
		var box := Rect2(minf(q[0].x, q[1].x), minf(q[0].y, q[1].y), absf(q[1].x - q[0].x), maxf(q[2].y, q[3].y) - minf(q[0].y, q[1].y))
		var plaque := Rect2(box.get_center().x - 70, box.position.y + 34, 140, 36)
		SectKit.lacquer(self, plaque, _is_pressed(str(d[2])))
		text(plaque.position + Vector2(0, 24), str(d[3]), 18, UiKit.PALE_GOLD if d[4] else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x)
		if not d[4]: _lock_icon(plaque.position + Vector2(plaque.size.x - 20, 4))
		region(box.merge(plaque), str(d[2]), null, d[4], str(d[5]))

# ------------------------------------------------------------------ the Role tab: the teaching boards
## S48 sect role variants: the signature line's damage or support variant, and the sect tree bought with contribution.
func _role(ch) -> void:
	var ts: Dictionary = ch.training_sect
	var sid := str(ts.get("id", ""))
	var roles := ContentDB.entry("sect_roles", sid)
	var cfg: Dictionary = ContentDB.config("sect_roles")
	var r := Rect2(content.position, content.size)
	if roles.is_empty():
		SectKit.timber(self, r)
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.training_sect.you_are_unaffiliated_the_jade"), 22, UiKit.PAPER)
		return
	var left := Rect2(r.position, Vector2(470, r.size.y))
	SectKit.timber(self, left)
	var names: Array = []
	for tid in roles.get("signature", []): names.append(ContentDB.name_of("techniques", str(tid)))
	para(Rect2(left.position + Vector2(20, 14), Vector2(left.size.x - 40, 50)), Tx.t("ui.training_sect.signature_line") % ", ".join(names), 18, UiKit.PALE_GOLD, 2)
	var role := str(ts.get("role", ""))
	var y := left.position.y + 70
	for key in ["damage", "support"]:
		var v: Dictionary = roles.get("variants", {}).get(key, {})
		var vr := Rect2(left.position.x + 16, y, left.size.x - 32, 150)
		var mine: bool = role == str(key)
		SectKit.lacquer(self, vr, mine)
		text(vr.position + Vector2(16, 30), "%s · %s" % [Tx.t("ui.training_sect." + key), str(v.get("name", ""))], 20, UiKit.GOLD if mine else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
		para(Rect2(vr.position + Vector2(16, 42), Vector2(vr.size.x - 32, 60)), str(v.get("desc", "")), 16, UiKit.MIST, 3)
		btn(Rect2(vr.end.x - 150, vr.end.y - 50, 136, 40), Tx.t("ui.training_sect.chosen") if mine else Tx.t("ui.training_sect.choose"), "role", key, not mine, not mine, "", 16)
		y += 162
	var note := Tx.t("ui.training_sect.switch_cost") % int(cfg.get("switch_cost", 50)) if role != "" else ""
	var sup := int(round((Game.combat.sect_support_mult(ch) - 1.0) * 100.0))
	if sup > 0: note += ("  " if note != "" else "") + Tx.t("ui.training_sect.support_scaling") % sup
	para(Rect2(left.position.x + 20, y, left.size.x - 40, 44), note, 16, UiKit.MIST, 2)
	# The tree: three branches of five nodes, bought in order, as lacquer tablets on the right wall's board.
	var right := Rect2(left.end.x + 14, r.position.y, r.size.x - left.size.x - 14, r.size.y)
	SectKit.timber(self, right)
	text(right.position + Vector2(20, 34), Tx.t("ui.training_sect.tree"), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	currency_pill(right.position + Vector2(right.size.x - 210, 8), "contribution", int(ts.get("contribution", 0)))
	var branches: Array = cfg.get("tree", {}).get("branches", [])
	var tree: Dictionary = ts.get("tree", {})
	var colw := (right.size.x - 40 - 16 * (branches.size() - 1)) / float(maxi(1, branches.size()))
	for bi in branches.size():
		var b: Dictionary = branches[bi]
		var x := right.position.x + 20 + bi * (colw + 16)
		text(Vector2(x, right.position.y + 76), str(b.get("name", {}).get(sid, b.id)), 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, colw, true)
		var lvl := int(tree.get(str(b.id), 0))
		var nodes: Array = b.get("nodes", [])
		var nh := (right.end.y - right.position.y - 104) / float(maxi(1, nodes.size()))
		for ni in nodes.size():
			var nd: Dictionary = nodes[ni]
			var nr := Rect2(x, right.position.y + 90 + ni * nh, colw, nh - 8)
			var owned := ni < lvl
			SectKit.lacquer(self, nr, owned)
			# B18: three lines where no Buy button takes the foot (the owned mark sits in the top corner), else two.
			var buy := not owned and ni == lvl
			para(Rect2(nr.position + Vector2(10, 4), Vector2(nr.size.x - (38 if owned else 20), nr.size.y - (30 if buy else 8))), str(nd.get("desc", "")), 14,
				UiKit.PAPER if owned else UiKit.MIST, 2 if buy else 3)
			if owned:
				text(Vector2(nr.end.x - 24, nr.position.y + 20), "✓", 18, UiKit.BRIGHT_JADE)
			elif ni == lvl:
				var why := ""
				if nd.has("rank") and not RequirementRules.passes({"all": [{"kind": "sect_rank_at_least", "rank": str(nd.rank)}]}, Game.ctx(ch)):
					why = Tx.t("req.sect_rank") % ContentDB.rank_name(str(nd.rank))
				elif int(ts.get("contribution", 0)) < int(nd.get("cost", 0)): why = Tx.t("sim.training_sect.not_enough_contribution") % int(nd.get("cost", 0))
				btn(Rect2(nr.end.x - 86, nr.end.y - 32, 78, 28), Tx.t("ui.training_sect.buy") % int(nd.get("cost", 0)), "node", str(b.id), true, why == "", why, 14)

func on_action(id: String, _data) -> void:
	match id:
		"role": submit({"type": "set_sect_role", "role": str(_data)})
		"node": submit({"type": "buy_sect_node", "branch": str(_data)})
		"promote": submit({"type": "take_promotion_trial"})
		"shop": navigate.emit("shop", {"shop": str(c().training_sect.get("id", "jade_sect"))})
		"missions": navigate.emit("notice_board", {})
