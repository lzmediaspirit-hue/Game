extends Page
## Relations (S49), under Character: what the world remembers of you. Karma (merit, sin, the righteous-demonic
## alignment, recent deeds and named debts), Bonds (Dao Companion, master, sworn siblings), Grudges (factions
## that want you dead) and Fame (the named tier, what it opens, and a young master's challenge when one waits).

const MERIT := Color("e8c872")
const SIN := Color("e07a7a")

func _init() -> void:
	title = Tx.t("ui.relations.title")
	tabs = [{"id": "karma", "label": Tx.t("ui.relations.tab_karma")}, {"id": "bonds", "label": Tx.t("ui.relations.tab_bonds")},
		{"id": "grudges", "label": Tx.t("ui.relations.tab_grudges")}, {"id": "fame", "label": Tx.t("ui.relations.tab_fame")}]

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"karma": _karma(ch)
		"bonds": _bonds(ch)
		"grudges": _grudges(ch)
		"fame": _fame(ch)

# ------------------------------------------------------------------ Karma
func _karma(ch) -> void:
	var r: RelationsState = ch.relations
	var left := Rect2(content.position, Vector2(520, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	var x := left.position.x + 24
	var y := left.position.y + 40
	heading(Vector2(x, y), Tx.t("ui.relations.ledger"), left.size.x - 48)
	y += 22
	# Merit and sin side by side, large.
	var half := (left.size.x - 48 - 16) / 2.0
	for i in 2:
		var box := Rect2(x + i * (half + 16), y, half, 92)
		panel(box, "minor_panel")
		text(box.position + Vector2(16, 30), Tx.t("ui.relations.merit") if i == 0 else Tx.t("ui.relations.sin"), 17, UiKit.MIST)
		text(box.position + Vector2(16, 76), str(r.merit if i == 0 else r.sin), 36, MERIT if i == 0 else SIN, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	y += 108
	var step := int(Game.relations.cfg().get("merit_step", 100))
	var ready := ProgressionRules.merit_step(ch) > 0
	var used := r.merit_used.has(ProgressionRules.great_realm(ch.cultivator.realm_key))
	var line := Tx.t("ui.relations.merit_ready") if ready else (Tx.t("ui.relations.merit_used") if used else Tx.t("ui.relations.merit_short") % [step - r.merit, step])
	para(Rect2(x, y - 6, left.size.x - 48, 48), line, 16, UiKit.BRIGHT_JADE if ready else UiKit.MIST, 2)
	y += 52
	para(Rect2(x, y - 6, left.size.x - 48, 48), Tx.t("ui.relations.sin_note"), 16, UiKit.MIST, 2)
	y += 78
	# The alignment scale: demonic on the left, righteous on the right.
	heading(Vector2(x, y), Tx.t("ui.relations.alignment"), left.size.x - 48)
	y += 22
	var word := Game.relations.alignment_word(ch)
	text(Vector2(x, y + 20), Tx.t("ui.relations.align_" + word), 22, _align_color(r.alignment), HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	_rtext(left.end.x - 24, y + 20, "%+d" % r.alignment, 20, UiKit.PAPER)
	y += 34
	var scale := Rect2(x, y, left.size.x - 48, 22)
	_alignment_scale(scale, r.alignment)
	y += 30
	text(Vector2(x, y + 14), Tx.t("ui.relations.align_demonic"), 14, UiKit.MIST)
	_rtext(scale.end.x, y + 14, Tx.t("ui.relations.align_righteous"), 14, UiKit.MIST)
	para(Rect2(x, y + 24, left.size.x - 48, left.end.y - y - 30), Tx.t("ui.relations.alignment_note"), 15, UiKit.MIST, 3)
	# Right: recent deeds, then named debts.
	x = right.position.x + 24
	y = right.position.y + 40
	heading(Vector2(x, y), Tx.t("ui.relations.recent"), right.size.x - 48)
	y += 16
	var debts: Array = r.debts.keys()
	var deeds_h := right.size.y - 70 - (40 + debts.size() * 30 if not debts.is_empty() else 0)
	if r.ledger.is_empty():
		para(Rect2(x, y + 4, right.size.x - 48, 60), Tx.t("ui.relations.no_deeds"), 17, UiKit.MIST, 3)
	else:
		list("deeds", Rect2(x, y + 4, right.size.x - 40, deeds_h), r.ledger.size(), 36, func(i: int, rr: Rect2):
			var e: Dictionary = r.ledger[i]
			var name := _deed_name(str(e.get("reason", "")), int(e.get("merit", 0)) > 0)
			var amt := ""
			var col := MERIT
			if int(e.get("merit", 0)) != 0: amt = Tx.t("ui.relations.merit_amt") % int(e.merit)
			if int(e.get("sin", 0)) != 0:
				amt = Tx.t("ui.relations.sin_amt") % int(e.sin)
				col = SIN
			text(rr.position + Vector2(0, 24), fit(name, 17, rr.size.x - 150), 17, UiKit.PAPER)
			_rtext(rr.end.x - 8, rr.position.y + 24, amt, 17, col)
		)
	if not debts.is_empty():
		y = right.end.y - 24 - debts.size() * 30
		heading(Vector2(x, y - 12), Tx.t("ui.relations.debts"), right.size.x - 48)
		y += 8
		for id in debts:
			var d: Dictionary = r.debts[id]
			text(Vector2(x, y + 14), fit(Tx.t("ui.cultivation.debt_" + str(id)), 17, right.size.x - 180), 17, UiKit.PAPER)
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
	var w := (content.size.x - gap * 2) / 3.0
	var top_h := 250.0
	for i in 3:
		var kind: String = cols[i][0]
		var who: String = cols[i][1]
		var box := Rect2(content.position.x + i * (w + gap), content.position.y, w, top_h)
		panel(box)
		var x := box.position.x + 22
		heading(Vector2(x, box.position.y + 40), Tx.t("ui.relations.bond_" + kind), w - 44)
		if who == "":
			text(Vector2(x, box.position.y + 90), Tx.t("ui.relations.bond_none"), 21, UiKit.MIST)
		else:
			text(Vector2(x, box.position.y + 90), fit(who if kind == "sworn" else ContentDB.name_of("npcs", who), 21, w - 44), 21, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
		para(Rect2(x, box.position.y + 106, w - 44, top_h - 116), Tx.t("ui.relations.bond_" + kind + "_note"), 15, UiKit.MIST, 5)
	# Below: everyone who knows you well enough to have hearts.
	var low := Rect2(content.position.x, content.position.y + top_h + gap, content.size.x, content.size.y - top_h - gap)
	panel(low)
	heading(Vector2(low.position.x + 22, low.position.y + 40), Tx.t("ui.relations.friends"), low.size.x - 44)
	var rows: Array = []
	for id in r.affinity:
		if int(r.affinity[id].get("points", 0)) > 0: rows.append(str(id))
	rows.sort_custom(func(a, b): return int(r.affinity[a].points) > int(r.affinity[b].points))
	if rows.is_empty():
		para(Rect2(low.position.x + 22, low.position.y + 56, low.size.x - 44, 60), Tx.t("ui.relations.no_friends"), 17, UiKit.MIST, 2)
		return
	var colw := (low.size.x - 44) / 2.0
	list("friends", Rect2(low.position.x + 22, low.position.y + 56, low.size.x - 34, low.size.y - 66), int(ceil(rows.size() / 2.0)), 38, func(row: int, rr: Rect2):
		for k in 2:
			var j := row * 2 + k
			if j >= rows.size(): break
			var x := rr.position.x + k * colw
			text(Vector2(x, rr.position.y + 24), fit(ContentDB.name_of("npcs", rows[j]), 18, colw - 170), 18, UiKit.PAPER)
			UiKit.draw_hearts(self, Vector2(x + colw - 160, rr.position.y + 17), r.hearts_of(rows[j]), 5, 9.0)
	)

# ------------------------------------------------------------------ Grudges
func _grudges(ch) -> void:
	var r: RelationsState = ch.relations
	var box := Rect2(content.position, content.size)
	panel(box)
	var x := box.position.x + 28
	heading(Vector2(x, box.position.y + 40), Tx.t("ui.relations.grudges"), box.size.x - 56)
	var rows: Array = []
	for f in ContentDB.all("factions"):
		if int(r.grudges.get(str(f.id), 0)) > 0: rows.append(f)
	if rows.is_empty():
		para(Rect2(x, box.position.y + 64, box.size.x - 56, 60), Tx.t("ui.relations.no_grudges"), 19, UiKit.MIST, 2)
	else:
		list("grudges", Rect2(x, box.position.y + 60, box.size.x - 48, box.size.y - 160), rows.size(), 96, func(i: int, rr: Rect2):
			var f: Dictionary = rows[i]
			var v := int(r.grudges.get(str(f.id), 0))
			var th := int(f.get("threshold", 30))
			panel(rr, "minor_panel", "selected" if v >= th else "normal")
			text(rr.position + Vector2(16, 32), fit(str(f.name), 20, 300), 20, UiKit.PAPER)
			text(rr.position + Vector2(16, 60), Tx.t("ui.relations.hunted") if v >= th else Tx.t("ui.relations.grudge_below") % th, 15,
				SIN if v >= th else UiKit.MIST)
			var bar_r := Rect2(rr.position.x + 330, rr.position.y + 16, rr.size.x - 330 - 470, 26)
			bar(bar_r, v / 100.0, SIN, str(v))
			var tx: float = bar_r.position.x + 6 + (bar_r.size.x - 12) * th / 100.0
			draw_line(Vector2(tx, bar_r.position.y - 3), Vector2(tx, bar_r.end.y + 3), UiKit.PALE_GOLD, 2)
			var bx := rr.end.x - 454
			var bm: Dictionary = f.get("blood_money", {})
			if not bm.is_empty():
				btn(Rect2(bx, rr.position.y + 18, 216, 56), Tx.t("ui.relations.pay") % int(bm.amount), "pay", [str(f.id), "blood_money"], false,
					Game.economy.balance(str(bm.currency), ch) >= int(bm.amount), Tx.t("sim.relations.cannot_pay") % int(bm.amount), 17)
			if str(f.get("duel", "")) != "":
				btn(Rect2(bx + 226, rr.position.y + 18, 216, 56), Tx.t("ui.relations.duel") % ContentDB.name_of("enemies", str(f.duel)), "pay", [str(f.id), "duel"], true, true, "", 16)
			elif str(f.get("quest", "")) != "":
				para(Rect2(bx + 230, rr.position.y + 16, 212, 64), Tx.t("ui.relations.settle_quest") % ContentDB.name_of("quests", str(f.quest)), 15, UiKit.PALE_GOLD, 3)
			elif not f.get("story", {}).is_empty():
				para(Rect2(bx + 230, rr.position.y + 16, 212, 64), Tx.t("ui.relations.settle_story"), 15, UiKit.MIST, 3)
		)
	para(Rect2(x, box.end.y - 96, box.size.x - 56, 80), Tx.t("ui.relations.grudges_note"), 16, UiKit.MIST, 3)

# ------------------------------------------------------------------ Fame
func _fame(ch) -> void:
	var r: RelationsState = ch.relations
	var left := Rect2(content.position, Vector2(560, content.size.y))
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(left)
	panel(right)
	var x := left.position.x + 24
	var y := left.position.y + 40
	var tier: Dictionary = Game.relations.fame_tier(ch)
	var nxt: Dictionary = Game.relations.next_fame_tier(ch)
	heading(Vector2(x, y), Tx.t("ui.relations.your_name"), left.size.x - 48)
	y += 58
	text(Vector2(x, y), Tx.t("ui.relations.fame_" + str(tier.get("id", "unknown"))), 34, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	_rtext(left.end.x - 24, y, Tx.t("ui.relations.fame_value") % r.fame, 20, UiKit.PAPER)
	y += 22
	if nxt.is_empty():
		bar(Rect2(x, y, left.size.x - 48, 26), 1.0, UiKit.GOLD, Tx.t("ui.relations.fame_top"))
	else:
		var lo := int(tier.get("min", 0))
		var hi := int(nxt.get("min", 1))
		bar(Rect2(x, y, left.size.x - 48, 26), float(r.fame - lo) / maxf(1.0, float(hi - lo)), UiKit.GOLD,
			Tx.t("ui.relations.fame_next") % [hi - r.fame, Tx.t("ui.relations.fame_" + str(nxt.id))])
	y += 44
	# The ladder: each tier and what it brings; the reached ones bright.
	for t2 in Game.relations.cfg().get("fame_tiers", []):
		var got: bool = r.fame >= int(t2.get("min", 0))
		text(Vector2(x, y + 18), Tx.t("ui.relations.fame_" + str(t2.id)), 18, UiKit.GOLD if got else UiKit.HOLLOW)
		text(Vector2(x + 130, y + 18), fit(Tx.t("ui.relations.fame_brings_" + str(t2.id)), 16, left.size.x - 178), 16, UiKit.PAPER if got else UiKit.HOLLOW)
		y += 32
	para(Rect2(x, y + 4, left.size.x - 48, left.end.y - y - 12), Tx.t("ui.relations.fame_note"), 15, UiKit.MIST, 3)
	# Right: a challenge waiting here, or how young masters find you.
	x = right.position.x + 24
	y = right.position.y + 40
	heading(Vector2(x, y), Tx.t("ui.relations.challenges"), right.size.x - 48)
	y += 24
	var chal: Dictionary = Game.relations.challenge_of(ch)
	if chal.is_empty():
		var need := int(Game.relations.cfg().get("young_master", {}).get("fame", 150))
		para(Rect2(x, y, right.size.x - 48, 160), Tx.t("ui.relations.no_challenge") if r.fame >= need else Tx.t("ui.relations.challenge_later") % need, 17, UiKit.MIST, 6)
		return
	var card := Rect2(x, y, right.size.x - 48, right.end.y - y - 20)
	panel(card, "minor_panel", "selected")
	var cx := card.position.x + 18
	var name := ContentDB.name_of("enemies", str(chal.enemy))
	text(Vector2(cx, card.position.y + 36), fit(name, 22, card.size.x - 36), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(cx, card.position.y + 64), Tx.t("ui.arena.lv") % int(chal.level), 16, UiKit.MIST)
	para(Rect2(cx, card.position.y + 80, card.size.x - 36, 130), Tx.t("ui.relations.challenge_line"), 18, UiKit.PAPER, 5)
	var win := _fame_of("young_master_humbled") + _fame_of("public_spar_won")
	var lose := _fame_of("young_master_lost") + _fame_of("public_spar_lost")
	para(Rect2(cx, card.end.y - 150, card.size.x - 36, 60), Tx.t("ui.relations.challenge_stakes") % [win, -lose, -_fame_of("challenge_declined")], 16, UiKit.MIST, 3)
	var bw := (card.size.x - 36 - 12) / 2.0
	btn(Rect2(cx, card.end.y - 72, bw, 54), Tx.t("ui.relations.accept"), "answer", true, true)
	btn(Rect2(cx + bw + 12, card.end.y - 72, bw, 54), Tx.t("ui.relations.decline"), "answer", false)

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
