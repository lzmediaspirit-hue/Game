extends Page
## Relations (S49), under Character: what the world remembers of you. Karma (merit, sin, the righteous-demonic
## alignment, recent deeds and named debts), Bonds (Dao Companion, master, sworn siblings), Grudges (factions
## that want you dead) and Fame (the named tier, what it opens, and a young master's challenge when one waits).
## P5 (docs/page_identity.md row 42, the Bonds family; no mockup, drawn from its row): the karma steelyard. On the
## whitewashed wall a timber rafter carries the title and the four tabs as tally tags; from its hook hangs your fame's
## plaque, and under it the steelyard's beam, merit's gold weight at its right end and sin's black one at its left,
## tilted toward righteous or demonic by the alignment, the recent deeds cut as notches along it. Each tab's boards hang
## from the beam: on red thread the bonds, on black thread the grudges, on hemp cords the ledger and the name. The beam
## settles to its tilt as the page opens (0.35 s, damped) and the weights sway; under Reduce motion it is drawn at its
## tilt, still.

const MERIT := UiKit.GOLD
const SIN := UiKit.RED_TEXT

const RAFTER := 60.0
const PIVOT := Vector2(640, 184)      # where the beam hangs from the hook
const HALF_BEAM := 480.0
const TILT := 0.05                    # the beam's tilt at full alignment, in radians
const BOARDS_Y := 300.0               # the boards' tops

func _init() -> void:
	title = Tx.t("ui.relations.title")
	tabs = [{"id": "karma", "label": Tx.t("ui.relations.tab_karma")}, {"id": "bonds", "label": Tx.t("ui.relations.tab_bonds")},
		{"id": "grudges", "label": Tx.t("ui.relations.tab_grudges")}, {"id": "fame", "label": Tx.t("ui.relations.tab_fame")}]
	identity = Identity.new("plaster", false, "own", "steelyard_beam_threads", 0.35)

func content_rect() -> Rect2:
	return Rect2(88, BOARDS_Y, 1104, frame_rect.end.y - 16 - BOARDS_Y)

## The whitewashed wall and the dark rafter across its top.
func draw_surface(r: Rect2) -> void:
	BondsKit.wall(self, r, 0.0)
	var rafter := Rect2(r.position, Vector2(r.size.x, RAFTER))
	vshade(Rect2(rafter.position.x, rafter.end.y, rafter.size.x, 20), Color(UiKit.INK, 0.3), Color(UiKit.INK, 0.0))
	rounded(rafter, 6.0, UiKit.SURFACE.wood_dark)
	vshade(rafter.grow(-3), UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark)
	for k in range(6, int(RAFTER) - 4, 5): draw_rect(Rect2(rafter.position.x + 8, rafter.position.y + k, rafter.size.x - 16, 1), Color(UiKit.INK, 0.15))
	draw_rect(Rect2(rafter.position.x, rafter.end.y - 3, rafter.size.x, 3), UiKit.INK)
	ground(rafter, UiKit.SURFACE.wood)

func title_rect() -> Rect2:
	return Rect2(92, 38, 300, 48)

## Decision 43: the "?" beside the title (the tabs and purses take the row left of the close button).
func help_rect() -> Rect2:
	var tr := title_rect()
	return Rect2(tr.end.x + 12, roundf(tr.get_center().y - 26), 52, 52)

## The title cut into the rafter: a sunk panel lined in bronze.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(1), 5.0, Color(UiKit.BRONZE, 0.8))
	rounded(r, 4.0, UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.4))

## The tabs are tally tags nailed along the rafter, right of the title and left of the close button.
func tab_rects() -> Array:
	var out: Array = []
	var x := frame_rect.end.x - 88.0
	for i in range(tabs.size() - 1, -1, -1):
		var w := maxf(112.0, UiKit.text_width(str(tabs[i].label), 20) + 40.0)
		x -= w
		out.push_front(Rect2(x, 38, w, 48))
		x -= 8.0
	return out

## A tally tag: timber with a nail at its head, the open one red lacquer rimmed in gold.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	var lit := state == "selected"
	rounded(r.grow(2), 6.0, UiKit.INK)
	if lit: rounded(r.grow(1), 5.0, UiKit.GOLD)
	var col: Color = UiKit.SURFACE.lacquer if lit else UiKit.SURFACE.wood
	rounded(r, 4.0, col)
	ground(r, col)
	draw_circle(Vector2(r.get_center().x, r.position.y + 7), 3.0, UiKit.BRONZE, true, -1.0, true)
	text(Vector2(r.position.x, r.position.y + 34), str(tabs[i].label), 20, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	_steelyard(ch)
	tour_mark("beam", Rect2(PIVOT.x - 420, 150, 840, 150))   # decision 43: the steelyard, a tour's anchor
	match str(tabs[tab].id):
		"karma": _karma(ch)
		"bonds": _bonds(ch)
		"grudges": _grudges(ch)
		"fame": _fame(ch)

# ------------------------------------------------------------------ the steelyard
## The beam's tilt now: the alignment's, reached through a damped swing over the opening.
func _tilt(ch) -> float:
	var target := TILT * clampf(ch.relations.alignment / 100.0, -1.0, 1.0)
	var k := unfold()
	return target + 0.09 * (1.0 - k) * cos(k * PI * 2.5)

## Where the beam passes over `x`, on its top edge.
func _beam_at(ch, x: float) -> Vector2:
	return Vector2(x, PIVOT.y - 7.0 + (x - PIVOT.x) * tan(_tilt(ch)))

## The hook with your fame's plaque, the beam tilted by merit against sin with the recent deeds notched along it, and
## the two weights hung from its ends with what they weigh.
func _steelyard(ch) -> void:
	var r: RelationsState = ch.relations
	var tier: Dictionary = Game.relations.fame_tier(ch)
	# The hook and the plaque of your name.
	draw_line(Vector2(PIVOT.x, frame_rect.position.y + RAFTER), Vector2(PIVOT.x, 104), UiKit.INK, 3.0, true)
	var plaque := Rect2(PIVOT.x - 90, 104, 180, 40)
	rounded(plaque.grow(2), 5.0, UiKit.INK)
	rounded(plaque.grow(1), 4.0, UiKit.GOLD)
	rounded(plaque, 3.0, UiKit.SURFACE.lacquer)
	ground(plaque, UiKit.SURFACE.lacquer)
	text(Vector2(plaque.position.x, plaque.position.y + 27), Tx.t("ui.relations.fame_" + str(tier.get("id", "unknown"))), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x)
	draw_arc(Vector2(PIVOT.x, plaque.end.y + 12), 10.0, -PI * 0.5, PI * 1.2, 16, UiKit.INK, 4.0, true)
	draw_arc(Vector2(PIVOT.x, plaque.end.y + 12), 10.0, -PI * 0.5, PI * 1.2, 16, UiKit.BRONZE, 2.0, true)
	# The beam, turned about its pivot.
	var a := _tilt(ch)
	move(PIVOT, a)
	rounded(Rect2(-HALF_BEAM - 2, -9, HALF_BEAM * 2 + 4, 18), 7.0, UiKit.INK)
	vshade(Rect2(-HALF_BEAM, -7, HALF_BEAM * 2, 14), UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark)
	for k in range(-11, 12):   # the graduations
		draw_line(Vector2(k * 40.0, -7), Vector2(k * 40.0, -2 if k % 5 != 0 else 2), Color(UiKit.GOLD, 0.7), 1.5, true)
	# Recent deeds as notches: merit to the right of the pivot, sin to the left, the newest nearest.
	var right := 0
	var left := 0
	for e in r.ledger.slice(0, 16):
		var good := int(e.get("merit", 0)) > 0
		var nx := (60.0 + 26.0 * (right if good else left)) * (1.0 if good else -1.0)
		if good: right += 1
		else: left += 1
		draw_colored_polygon(PackedVector2Array([Vector2(nx - 5, 7), Vector2(nx + 5, 7), Vector2(nx, -1)]), MERIT if good else UiKit.BLOOD)
	draw_circle(Vector2.ZERO, 9.0, UiKit.INK, true, -1.0, true)
	draw_circle(Vector2.ZERO, 6.5, UiKit.BRONZE, true, -1.0, true)
	move()
	# The weights on their cords: merit's gold at the right end, sin's black at the left, what each weighs over its end.
	var sway := 0.0 if UiKit.reduce_motion() else sin(t * 1.3) * 3.0
	for side: float in [1.0, -1.0]:
		var end := PIVOT + Vector2.from_angle(a) * HALF_BEAM * side * 0.94
		var top := end + Vector2(0, 7)
		var hang := top + Vector2(sway * side, 22)
		draw_line(top, hang, UiKit.INK, 2.0, true)
		var body := PackedVector2Array([hang + Vector2(-12, 0), hang + Vector2(12, 0), hang + Vector2(22, 36), hang + Vector2(-22, 36)])
		draw_colored_polygon(PackedVector2Array([body[0] + Vector2(-2, -2), body[1] + Vector2(2, -2), body[2] + Vector2(2, 2), body[3] + Vector2(-2, 2)]), UiKit.INK)
		draw_colored_polygon(body, MERIT if side > 0.0 else UiKit.SURFACE.lacquer_black)
		draw_line(hang + Vector2(-16, 10), hang + Vector2(16, 10), Color(UiKit.PALE_GOLD, 0.5) if side > 0.0 else Color(UiKit.BRONZE, 0.7), 1.5, true)
		var words := "%s %d" % [Tx.t("ui.relations.merit") if side > 0.0 else Tx.t("ui.relations.sin"), r.merit if side > 0.0 else r.sin]
		text(Vector2(end.x - 100, end.y - 22), words, 20, BondsKit.INK, HORIZONTAL_ALIGNMENT_CENTER, 200)
		text(Vector2(end.x - 100, end.y - 46), Tx.t("ui.relations.align_righteous") if side > 0.0 else Tx.t("ui.relations.align_demonic"), 14, BondsKit.SOFT_INK,
			HORIZONTAL_ALIGNMENT_CENTER, 200)
	# The reading, left of the hook.
	var word := Game.relations.alignment_word(ch)
	text(Vector2(PIVOT.x - 120 - 260, 136), "%s  %+d" % [Tx.t("ui.relations.align_" + word), r.alignment], 22, _align_ink(r.alignment), HORIZONTAL_ALIGNMENT_RIGHT, 260, true)

## The alignment's word on the whitewash: blood-red toward demonic, jade toward righteous.
func _align_ink(v: int) -> Color:
	if v <= -20: return UiKit.BLOOD
	if v >= 20: return UiKit.JADE_SHADOW
	return BondsKit.INK

## A board hung from the beam by two threads of `cord` (red for bonds, black for grudges, hemp for the rest).
func _hung(ch, r: Rect2, cord: Color) -> void:
	var reach := HALF_BEAM * 0.94 - 36.0   # inside the weights
	for x in [clampf(r.position.x + 40.0, PIVOT.x - reach, PIVOT.x + reach), clampf(r.end.x - 40.0, PIVOT.x - reach, PIVOT.x + reach)]:
		BondsKit.thread(self, _beam_at(ch, x) + Vector2(0, 14), Vector2(x, r.position.y + 10), cord, 0.0, 2.5)
	BondsKit.board(self, r, cord)

## The hemp cords the ledger and the name hang by.
const CORD := UiKit.BRONZE

# ------------------------------------------------------------------ Karma
func _karma(ch) -> void:
	var r: RelationsState = ch.relations
	var left := Rect2(content.position, Vector2(520, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	_hung(ch, left, CORD)
	_hung(ch, right, CORD)
	var x := left.position.x + 24
	var y := left.position.y + 48
	heading(Vector2(x, y), Tx.t("ui.relations.ledger"), left.size.x - 48)
	y += 18
	var step := int(Game.relations.cfg().get("merit_step", 100))
	var ready := ProgressionRules.merit_step(ch) > 0
	var used := r.merit_used.has(ProgressionRules.great_realm(ch.cultivator.realm_key))
	var line := Tx.t("ui.relations.merit_ready") if ready else (Tx.t("ui.relations.merit_used") if used else Tx.t("ui.relations.merit_short") % [step - r.merit, step])
	y += para(Rect2(x, y, left.size.x - 48, 66), line, 16, UiKit.BRIGHT_JADE if ready else UiKit.PAPER, 3) + 8
	para(Rect2(x, y, left.size.x - 48, 44), Tx.t("ui.relations.sin_note"), 16, UiKit.MIST, 2)
	# The alignment scale: demonic on the left, righteous on the right.
	y = left.position.y + 212
	heading(Vector2(x, y), Tx.t("ui.relations.alignment"), left.size.x - 48)
	y += 18
	var word := Game.relations.alignment_word(ch)
	text(Vector2(x, y + 20), Tx.t("ui.relations.align_" + word), 22, _align_color(r.alignment), HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	_rtext(left.end.x - 24, y + 20, "%+d" % r.alignment, 20, UiKit.PAPER)
	y += 30
	var scale := Rect2(x, y, left.size.x - 48, 22)
	_alignment_scale(scale, r.alignment)
	para(Rect2(x, y + 28, left.size.x - 48, left.end.y - y - 36), Tx.t("ui.relations.alignment_note"), 16, UiKit.MIST, 3)
	# Right: the Fortune meter (S49), recent deeds, then named debts.
	x = right.position.x + 24
	y = right.position.y + 48
	heading(Vector2(x, y), Tx.t("ui.relations.fortune"), right.size.x - 48)
	var meter := Game.relations.fortune_meter(ch)
	var met := 0
	for k in r.fortune.get("seen", {}): met += int(r.fortune.seen[k])
	bar(Rect2(x, y + 14, right.size.x - 48, 26), meter, UiKit.GOLD,
		Tx.t("ui.relations.fortune_ready") if meter >= 1.0 else Tx.t("ui.relations.fortune_in") % UiKit.span(Game.relations.fortune_ready_in(ch), false))
	text(Vector2(x, y + 62), fit(Tx.t("ui.relations.fortune_note") % met, 16, right.size.x - 48), 16, UiKit.MIST)
	y += 104
	heading(Vector2(x, y), Tx.t("ui.relations.recent"), right.size.x - 48)
	y += 12
	var debts: Array = r.debts.keys()
	var deeds_h := right.end.y - y - 16 - (40 + debts.size() * 30 if not debts.is_empty() else 0)
	if r.ledger.is_empty():
		para(Rect2(x, y + 4, right.size.x - 48, 60), Tx.t("ui.relations.no_deeds"), 18, UiKit.MIST, 3)
	else:
		list("deeds", Rect2(x, y + 4, right.size.x - 40, deeds_h), r.ledger.size(), 40, func(i: int, rr: Rect2):
			var e: Dictionary = r.ledger[i]
			var name := _deed_name(str(e.get("reason", "")), int(e.get("merit", 0)) > 0)
			var amt := ""
			var col := MERIT
			if int(e.get("merit", 0)) != 0: amt = Tx.t("ui.relations.merit_amt") % int(e.merit)
			if int(e.get("sin", 0)) != 0:
				amt = Tx.t("ui.relations.sin_amt") % int(e.sin)
				col = SIN
			text(rr.position + Vector2(0, 24), fit(name, 18, rr.size.x - 150), 18, UiKit.PAPER)
			_rtext(rr.end.x - 8, rr.position.y + 24, amt, 18, col)
		)
	if not debts.is_empty():
		y = right.end.y - 20 - debts.size() * 30
		heading(Vector2(x, y - 12), Tx.t("ui.relations.debts"), right.size.x - 48)
		y += 8
		for id in debts:
			var d: Dictionary = r.debts[id]
			text(Vector2(x, y + 14), fit(Tx.t("ui.cultivation.debt_" + str(id)), 18, right.size.x - 180), 18, UiKit.PAPER)
			_rtext(right.end.x - 24, y + 14, Tx.t("ui.cultivation.debt_settled") if d.get("paid", false) else Tx.t("ui.cultivation.debt_open"), 16,
				UiKit.MIST if d.get("paid", false) else UiKit.PALE_GOLD)
			y += 30

## Text whose right edge sits at x.
func _rtext(x: float, y: float, s: String, size: int, col: Color) -> void:
	text(Vector2(x - 400, y), s, size, col, HORIZONTAL_ALIGNMENT_RIGHT, 400)

func _deed_name(reason: String, good: bool) -> String:
	var dd := ContentDB.entry("karma", reason)
	if not dd.is_empty(): return str(dd.get("name", reason))
	return Tx.t("ui.relations.deed_good") if good else Tx.t("ui.relations.deed_bad")

func _align_color(v: int) -> Color:
	if v <= -20: return SIN
	if v >= 20: return MERIT
	return UiKit.PAPER

## A bar from -100 to +100: dark red to the left of centre, gold to the right, with a marker at the value.
func _alignment_scale(r: Rect2, v: int) -> void:
	draw_style_box(UiKit.style("bar_shell"), r)
	var inner := r.grow_individual(-6, -5, -6, -5)
	var mid := inner.position.x + inner.size.x * 0.5
	draw_rect(Rect2(inner.position, Vector2(inner.size.x * 0.5, inner.size.y)), Color(SIN, 0.28))
	draw_rect(Rect2(Vector2(mid, inner.position.y), Vector2(inner.size.x * 0.5, inner.size.y)), Color(MERIT, 0.28))
	draw_line(Vector2(mid, inner.position.y - 2), Vector2(mid, inner.end.y + 2), Color(UiKit.PAPER, 0.5), 1.5)
	var px := mid + inner.size.x * 0.5 * clampf(v / 100.0, -1.0, 1.0)
	draw_rect(Rect2(minf(mid, px), inner.position.y, absf(px - mid), inner.size.y), _align_color(v) if v != 0 else UiKit.PAPER)
	draw_circle(Vector2(px, inner.get_center().y), 8, UiKit.PAPER)
	draw_circle(Vector2(px, inner.get_center().y), 5, _align_color(v))

# ------------------------------------------------------------------ Bonds
func _bonds(ch) -> void:
	var r: RelationsState = ch.relations
	var cols := [["dao_companion", str(r.bonds.get("dao_companion", ""))], ["master", str(r.bonds.get("master", ""))],
		["sworn", ", ".join((r.bonds.get("sworn", []) as Array).map(func(id): return ContentDB.name_of("npcs", str(id))))]]
	var gap := 16.0
	var friends_w := 380.0
	var w := (content.size.x - friends_w - gap * 3) / 3.0
	for i in 3:
		var kind: String = cols[i][0]
		var who: String = cols[i][1]
		var box := Rect2(content.position.x + i * (w + gap), content.position.y, w, content.size.y)
		_hung(ch, box, BondsKit.THREAD)
		var x := box.position.x + 20
		heading(Vector2(x, box.position.y + 48), Tx.t("ui.relations.bond_" + kind), w - 40)
		if who == "":
			text(Vector2(x, box.position.y + 92), Tx.t("ui.relations.bond_none"), 20, UiKit.MIST)
		else:
			text(Vector2(x, box.position.y + 92), fit(who if kind == "sworn" else ContentDB.name_of("npcs", who), 22, w - 40), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
		para(Rect2(x, box.position.y + 110, w - 40, box.size.y - 124), Tx.t("ui.relations.bond_" + kind + "_note"), 16, UiKit.MIST, 9)
	# At the right: everyone who knows you well enough to have hearts.
	var low := Rect2(content.end.x - friends_w, content.position.y, friends_w, content.size.y)
	_hung(ch, low, BondsKit.THREAD)
	heading(Vector2(low.position.x + 20, low.position.y + 48), Tx.t("ui.relations.friends"), low.size.x - 40)
	var rows: Array = []
	for id in r.affinity:
		if int(r.affinity[id].get("points", 0)) > 0: rows.append(str(id))
	rows.sort_custom(func(a, b): return int(r.affinity[a].points) > int(r.affinity[b].points))
	if rows.is_empty():
		para(Rect2(low.position.x + 20, low.position.y + 64, low.size.x - 40, 80), Tx.t("ui.relations.no_friends"), 18, UiKit.MIST, 3)
		return
	list("friends", Rect2(low.position.x + 20, low.position.y + 64, low.size.x - 30, low.size.y - 80), rows.size(), 40, func(row: int, rr: Rect2):
		text(Vector2(rr.position.x, rr.position.y + 24), fit(ContentDB.name_of("npcs", rows[row]), 18, rr.size.x - 150), 18, UiKit.PAPER)
		UiKit.draw_hearts(self, Vector2(rr.end.x - 132, rr.position.y + 17), r.hearts_of(rows[row]), 5, 9.0)
	)

# ------------------------------------------------------------------ Grudges
func _grudges(ch) -> void:
	var r: RelationsState = ch.relations
	var box := Rect2(content.position, content.size)
	_hung(ch, box, BondsKit.GRUDGE)
	var x := box.position.x + 28
	heading(Vector2(x, box.position.y + 48), Tx.t("ui.relations.grudges"), box.size.x - 56)
	var rows: Array = []
	for f in ContentDB.all("factions"):
		if int(r.grudges.get(str(f.id), 0)) > 0: rows.append(f)
	if rows.is_empty():
		para(Rect2(x, box.position.y + 68, box.size.x - 56, 60), Tx.t("ui.relations.no_grudges"), 20, UiKit.MIST, 2)
	else:
		list("grudges", Rect2(x, box.position.y + 64, box.size.x - 48, box.size.y - 136), rows.size(), 96, func(i: int, rr: Rect2):
			var f: Dictionary = rows[i]
			var v := int(r.grudges.get(str(f.id), 0))
			var th := int(f.get("threshold", 30))
			panel(rr, "minor_panel", "selected" if v >= th else "normal")
			text(rr.position + Vector2(16, 32), fit(str(f.name), 20, 300), 20, UiKit.PAPER)
			text(rr.position + Vector2(16, 60), Tx.t("ui.relations.hunted") if v >= th else Tx.t("ui.relations.grudge_below") % th, 16,
				SIN if v >= th else UiKit.MIST)
			var bar_r := Rect2(rr.position.x + 330, rr.position.y + 16, rr.size.x - 330 - 470, 26)
			bar(bar_r, v / 100.0, SIN, str(v))
			var tx: float = bar_r.position.x + 6 + (bar_r.size.x - 12) * th / 100.0
			draw_line(Vector2(tx, bar_r.position.y - 3), Vector2(tx, bar_r.end.y + 3), UiKit.PALE_GOLD, 2)
			var bx := rr.end.x - 454
			var bm: Dictionary = f.get("blood_money", {})
			if not bm.is_empty():
				btn(Rect2(bx, rr.position.y + 18, 216, 56), Tx.plural("ui.relations.pay", int(bm.amount)) % int(bm.amount), "pay", [str(f.id), "blood_money"], false,
					Game.economy.balance(str(bm.currency), ch) >= int(bm.amount), Tx.t("sim.relations.cannot_pay") % int(bm.amount), 18)
			if str(f.get("duel", "")) != "":
				btn(Rect2(bx + 226, rr.position.y + 18, 216, 56), Tx.t("ui.relations.duel") % ContentDB.name_of("enemies", str(f.duel)), "pay", [str(f.id), "duel"], true, true, "", 16)
			elif str(f.get("quest", "")) != "":
				para(Rect2(bx + 230, rr.position.y + 16, 212, 64), Tx.t("ui.relations.settle_quest") % ContentDB.name_of("quests", str(f.quest)), 16, UiKit.PALE_GOLD, 3)
			elif not f.get("story", {}).is_empty():
				para(Rect2(bx + 230, rr.position.y + 16, 212, 64), Tx.t("ui.relations.settle_story"), 16, UiKit.MIST, 3)
		)
	para(Rect2(x, box.end.y - 64, box.size.x - 56, 48), Tx.t("ui.relations.grudges_note"), 16, UiKit.MIST, 2)

# ------------------------------------------------------------------ Fame
func _fame(ch) -> void:
	var r: RelationsState = ch.relations
	var left := Rect2(content.position, Vector2(560, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	_hung(ch, left, CORD)
	_hung(ch, right, CORD)
	var x := left.position.x + 24
	var y := left.position.y + 48
	var tier: Dictionary = Game.relations.fame_tier(ch)
	var nxt: Dictionary = Game.relations.next_fame_tier(ch)
	heading(Vector2(x, y), Tx.t("ui.relations.your_name"), left.size.x - 200)
	_rtext(left.end.x - 24, y, Tx.t("ui.relations.fame_value") % r.fame, 20, UiKit.PAPER)
	y += 20
	if nxt.is_empty():
		bar(Rect2(x, y, left.size.x - 48, 26), 1.0, UiKit.GOLD, Tx.t("ui.relations.fame_top"))
	else:
		var lo := int(tier.get("min", 0))
		var hi := int(nxt.get("min", 1))
		bar(Rect2(x, y, left.size.x - 48, 26), float(r.fame - lo) / maxf(1.0, float(hi - lo)), UiKit.GOLD,
			Tx.t("ui.relations.fame_next") % [hi - r.fame, Tx.t("ui.relations.fame_" + str(nxt.id))])
	y += 40
	# The ladder: each tier and what it brings; the reached ones bright, yours marked.
	for t2 in Game.relations.cfg().get("fame_tiers", []):
		var got: bool = r.fame >= int(t2.get("min", 0))
		if str(t2.id) == str(tier.get("id", "")): draw_rect(Rect2(x - 10, y, left.size.x - 28, 30), Color(UiKit.GOLD, 0.12))
		text(Vector2(x, y + 21), Tx.t("ui.relations.fame_" + str(t2.id)), 18, UiKit.GOLD if got else UiKit.MIST)
		text(Vector2(x + 130, y + 21), fit(Tx.t("ui.relations.fame_brings_" + str(t2.id)), 16, left.size.x - 178), 16, UiKit.PAPER if got else UiKit.MIST)
		y += 32
	para(Rect2(x, y + 6, left.size.x - 48, left.end.y - y - 14), Tx.t("ui.relations.fame_note"), 16, UiKit.MIST, 2)
	# Right: a challenge waiting here, or how young masters find you.
	x = right.position.x + 24
	y = right.position.y + 48
	heading(Vector2(x, y), Tx.t("ui.relations.challenges"), right.size.x - 48)
	y += 16
	var chal: Dictionary = Game.relations.challenge_of(ch)
	if chal.is_empty():
		var need := int(Game.relations.cfg().get("young_master", {}).get("fame", 150))
		para(Rect2(x, y + 4, right.size.x - 48, 160), Tx.t("ui.relations.no_challenge") if r.fame >= need else Tx.t("ui.relations.challenge_later") % need, 18, UiKit.MIST, 6)
		return
	var card := Rect2(x, y, right.size.x - 48, right.end.y - y - 18)
	panel(card, "minor_panel", "selected")
	var cx := card.position.x + 18
	var name := ContentDB.name_of("enemies", str(chal.enemy))
	text(Vector2(cx, card.position.y + 34), fit(name, 22, card.size.x - 150), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	_rtext(card.end.x - 18, card.position.y + 34, Tx.t("ui.arena.lv") % int(chal.level), 16, UiKit.MIST)
	# A young master (Fame), or a jealous senior drawn by a heavenly phenomenon (S49).
	var jealous := str(chal.enemy) == "jealous_senior"
	para(Rect2(cx, card.position.y + 48, card.size.x - 36, 92), Tx.t("ui.relations.jealous_line") if jealous else Tx.t("ui.relations.challenge_line"), 16, UiKit.PAPER, 4)
	var win := _fame_of("jealous_humbled" if jealous else "young_master_humbled") + _fame_of("public_spar_won")
	var lose := _fame_of("jealous_lost" if jealous else "young_master_lost") + _fame_of("public_spar_lost")
	para(Rect2(cx, card.end.y - 110, card.size.x - 36, 44), Tx.t("ui.relations.challenge_stakes") % [win, -lose, -_fame_of("challenge_declined")], 16, UiKit.MIST, 2)
	var bw := (card.size.x - 36 - 12) / 2.0
	btn(Rect2(cx, card.end.y - 60, bw, 48), Tx.t("ui.relations.accept"), "answer", true, true)
	btn(Rect2(cx + bw + 12, card.end.y - 60, bw, 48), Tx.t("ui.relations.decline"), "answer", false)

func _fame_of(deed: String) -> int:
	return int(ContentDB.entry("karma", deed).get("fame", 0))

func on_action(id: String, data) -> void:
	match id:
		"pay":
			var res := submit({"type": "pay_grudge", "faction": str(data[0]), "method": str(data[1])})
			if res.get("ok", false) and str(data[1]) == "duel":
				close()
				return
		"answer":
			var res := submit({"type": "answer_challenge", "accept": bool(data)})
			if res.get("ok", false) and bool(data):
				close()
				return
	queue_redraw()
