extends Page
## Cultivation (S04–S10, Part 9.6): Overview with the realm, progress, stability and
## bottleneck; Foundation (body and meridians); Heart (what the past costs: heart demons, karma,
## a hollow foundation, residue and pill resistance, gap report G1); Methods; Dao; Seclusion.

func _init() -> void:
	title = Tx.t("ui.cultivation.cultivation")

func setup() -> void:
	var ch = c()
	tabs = [{"id": "overview", "label": Tx.t("ui.cultivation.overview")},
		{"id": "foundation", "label": Tx.t("ui.cultivation.foundation"), "locked": "" if Unlocks.is_unlocked(ch.id, "foundation") else Unlocks.locked_text("foundation")},
		{"id": "body", "label": Tx.t("ui.cultivation.body_tab")},
		{"id": "heart", "label": Tx.t("ui.cultivation.heart")},
		{"id": "vows", "label": Tx.t("ui.cultivation.vows"), "locked": "" if Unlocks.is_unlocked(ch.id, "vows") else Unlocks.locked_text("vows")},
		{"id": "methods", "label": Tx.t("ui.cultivation.methods")},
		{"id": "dao", "label": Tx.t("ui.cultivation.dao"), "locked": "" if Unlocks.is_unlocked(ch.id, "dao_tree") else Unlocks.locked_text("dao_tree")},
		{"id": "seclusion", "label": Tx.t("ui.cultivation.seclusion"), "locked": "" if Unlocks.is_unlocked(ch.id, "seclusion") else Unlocks.locked_text("seclusion")}]
	if page_id == "seclusion" and Unlocks.is_unlocked(ch.id, "seclusion"): tab = 7
	if page_id == "heart": tab = 3
	if page_id == "body": tab = 2

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"overview": _overview(ch)
		"foundation": _foundation(ch)
		"body": _body(ch)
		"heart": _heart(ch)
		"vows": _vows(ch)
		"methods": _methods(ch)
		"dao": _dao(ch)
		"seclusion": _seclusion(ch)

func _overview(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var left := Rect2(content.position.x, content.position.y, 520, content.size.y)
	panel(left)
	var x := left.position.x + 24
	var y := left.position.y + 20
	draw_style_box(UiKit.style("realm_badge"), Rect2(x, y, 90, 90))
	text(Vector2(x, y + 58), str(ProgressionRules.level(ch)), 32, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 90, true)
	text(Vector2(x + 110, y + 36), ContentDB.text("realm." + cu.realm_key), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(x + 110, y + 70), Tx.t("ui.cultivation.level") % [ProgressionRules.level(ch), str(cu.state).capitalize()], 19, UiKit.MIST)
	y += 120
	var frac := cu.progress_fraction()
	var col := UiKit.GOLD if cu.state == "bottleneck" else UiKit.JADE
	bar(Rect2(x, y, 470, 36), frac, col, Tx.t("ui.cultivation.qp") % [UiKit.fmt(cu.qp), UiKit.fmt(cu.need())])
	y += 50
	if cu.stored_qi > 0.0:
		text(Vector2(x, y + 20), Tx.t("ui.cultivation.stored_qi") % [UiKit.fmt(cu.stored_qi), UiKit.fmt(ProgressionRules.stored_qi_cap(ch))], 18, UiKit.QI)
		y += 30
	var method := ProgressionRules.method(cu.method_id)
	var rows := [[Tx.t("ui.cultivation.method"), ContentDB.name_of("methods", cu.method_id) if cu.method_id != "" else Tx.t("ui.cultivation.none")],
		[Tx.t("ui.cultivation.energy"), str(cu.energy_type).replace("_", " ").capitalize() if cu.energy_type != "none" else Tx.t("ui.cultivation.body_only")],
		[Tx.t("ui.cultivation.stability"), str(cu.stability).capitalize()],
		[Tx.t("ui.cultivation.body_level"), "%d (%d%%)" % [cu.body_level, int(100.0 * cu.body_xp / maxf(1.0, ProgressionRules.body_xp_needed(cu.body_level)))]],
		[Tx.t("ui.cultivation.toxicity"), "%d / %d" % [int(cu.toxicity), int(ch.stats.value("toxicity_tolerance"))]],
		[Tx.t("ui.cultivation.injuries"), Tx.t("ui.cultivation.none") if cu.injuries.is_empty() else ", ".join(cu.injuries.keys()).capitalize()]]
	if cu.energy_type == "true_qi": rows.append([Tx.t("ui.cultivation.purity"), Tx.t("ui.cultivation.grade") % cu.purity])
	if method.is_empty() and cu.realm_key == "mortal": rows[0][1] = Tx.t("ui.cultivation.not_yet_learned")
	# Rows share the space above the buttons (Purity joins them at Cloud Stride).
	var step := minf(32.0, (left.end.y - 92.0 - y) / float(rows.size()))
	var fs := 19 if step >= 28.0 else 17
	for r in rows:
		text(Vector2(x, y + step * 0.7), str(r[0]), fs, UiKit.MIST)
		text(Vector2(x + 180, y + step * 0.7), str(r[1]), fs, UiKit.PAPER)
		y += step
	var medit: bool = cu.meditating
	btn(Rect2(x, left.end.y - 78, 220, 58), Tx.t("ui.cultivation.stop") if medit else Tx.t("ui.cultivation.meditate"), "meditate", null, not medit, Unlocks.is_unlocked(ch.id, "cultivate"),
		Unlocks.locked_text("cultivate"))
	btn(Rect2(x + 240, left.end.y - 78, 230, 58), Tx.t("ui.cultivation.breakthrough"), "breakthrough", null, cu.state == "bottleneck",
		Unlocks.is_unlocked(ch.id, "breakthrough"), Unlocks.locked_text("breakthrough"))
	# Right: what the next breakthrough needs.
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	var q: Dictionary = Game.progression.query_breakthrough(ch)
	heading(right.position + Vector2(24, 40), Tx.t("ui.cultivation.next") % ContentDB.name_of("realms", str(q.get("to", ""))), right.size.x - 48)
	var yy := right.position.y + 70
	if not q.get("major", false):
		para(Rect2(right.position.x + 24, yy, right.size.x - 48, 120), Tx.t("ui.cultivation.a_minor_step_fill_the"), 19, UiKit.PAPER)
	else:
		for r in q.get("results", []):
			var ok: bool = r.ok
			draw_circle(Vector2(right.position.x + 36, yy + 14), 9, UiKit.JADE if ok else (UiKit.RED if r.hard else Color("f0a040")))
			text(Vector2(right.position.x + 56, yy + 20), str(r.text), 18, UiKit.PAPER if ok else UiKit.PALE_GOLD)
			text(Vector2(right.position.x + 56, yy + 40), (Tx.t("ui.cultivation.required") if r.hard else Tx.t("ui.cultivation.lowers_risk")) + " · " + str(r.cause).capitalize(), 14, UiKit.MIST)
			yy += 52
		text(Vector2(right.position.x + 24, right.end.y - 40), Tx.t("ui.cultivation.risk_success") % [str(q.risk).capitalize(), int(float(q.success) * 100)], 20, UiKit.GOLD)

func _foundation(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	text(r.position + Vector2(24, 40), Tx.t("ui.cultivation.unspent_meridian_points") % cu.unspent_meridian_points, 22, UiKit.PALE_GOLD)
	var names := {"body": Tx.t("ui.cultivation.body"), "agility": Tx.t("ui.cultivation.agility"), "essence": Tx.t("ui.cultivation.essence"), "spirit": Tx.t("ui.cultivation.spirit"), "insight": Tx.t("ui.cultivation.insight")}
	var desc := {"body": Tx.t("ui.cultivation.hp_defence_body_training"), "agility": Tx.t("ui.cultivation.speed_evasion_accuracy"), "essence": Tx.t("ui.cultivation.qi_qi_attack"), "spirit": Tx.t("ui.cultivation.soul_sense_will"),
		"insight": Tx.t("ui.cultivation.insight_mastery_crafting")}
	var y := r.position.y + 70
	for k in names:
		var v := int(cu.meridians.get(k, 0))
		text(Vector2(r.position.x + 24, y + 30), names[k], 24, UiKit.PAPER)
		text(Vector2(r.position.x + 170, y + 30), str(desc[k]), 17, UiKit.MIST)
		bar(Rect2(r.position.x + 470, y + 8, 360, 30), v / 100.0, UiKit.JADE, "%d" % v)
		btn(Rect2(r.position.x + 850, y + 2, 120, 44), "+1", "meridian", k, true, cu.unspent_meridian_points > 0, Tx.t("ui.cultivation.no_points_to_spend"))
		y += 64
	var free := not ProgressionRules.at_least(cu.realm_key, "qi_unfurling_1")
	btn(Rect2(r.position.x + 24, r.end.y - 70, 420, 52), Tx.t("ui.cultivation.reset_free") if free else Tx.t("ui.cultivation.reset_meridian_reversal_pill"), "reset_meridians")

## Body (S48): the body level and the four rungs of the ladder, each with its level, Temper trial and bath.
func _body(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := content
	panel(r)
	var x := r.position.x + 24
	var y := r.position.y + 20
	var here := ProgressionRules.body_tier_index(cu)
	text(Vector2(x, y + 30), Tx.t("ui.cultivation.mortal_body") if here == 0 else ContentDB.name_of("body_tiers", cu.body_tier), 28, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 300, true)
	var need := ProgressionRules.body_xp_needed(cu.body_level)
	bar(Rect2(x + 320, y + 8, 440, 32), cu.body_xp / maxf(1.0, need), UiKit.JADE, Tx.t("ui.cultivation.body_level_bar") % [cu.body_level, int(100.0 * cu.body_xp / maxf(1.0, need))])
	text(Vector2(x, y + 64), Tx.t("ui.cultivation.body_hint"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 48)
	y += 84
	var tiers := ContentDB.all("body_tiers")
	var gap := 14.0
	var cw := (r.size.x - 48 - gap * (tiers.size() - 1)) / float(tiers.size())
	for i in tiers.size():
		var t: Dictionary = tiers[i]
		var cr := Rect2(x + i * (cw + gap), y, cw, r.end.y - y - 20)
		var reached := i < here
		panel(cr, "minor_panel", "selected" if i == here else ("normal" if reached else "disabled"))
		if i == here: draw_rect(cr.grow(-3), Color(UiKit.GOLD, 0.8), false, 2.0)   # the next rung
		var cx := cr.position.x + 16
		var cy := cr.position.y + 36
		text(Vector2(cx, cy), str(t.get("name", "")), 22, UiKit.PALE_GOLD if reached or i == here else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw - 110, true)
		if reached: text(Vector2(cr.end.x - 106, cy - 2), Tx.t("ui.cultivation.reached"), 15, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		elif i == here: text(Vector2(cr.end.x - 106, cy - 2), Tx.t("ui.cultivation.next_rung"), 15, UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 90)
		cy += 22
		var checks := [[Tx.t("ui.cultivation.body_need_level") % int(t.need), cu.body_level >= int(t.need)],
			[Tx.t("ui.cultivation.body_need_trial"), str(t.id) in cu.body_trials],
			[ContentDB.item_name(str(t.bath)), str(t.id) in cu.body_baths]]
		for chk in checks:
			var done: bool = reached or chk[1]
			draw_circle(Vector2(cx + 7, cy + 12), 7, UiKit.JADE if done else Color(UiKit.MIST, 0.35))
			text(Vector2(cx + 22, cy + 18), str(chk[0]), 16, UiKit.PAPER if done else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, cw - 46)
			cy += 26
		cy += 6
		cy += para(Rect2(cx, cy, cw - 32, 110), str(t.get("trial_text", "")), 15, UiKit.MIST, 5) + 8
		para(Rect2(cx, cy, cw - 32, cr.end.y - cy - 10), str(t.get("gift_text", "")), 16, UiKit.BRIGHT_JADE if reached else UiKit.PAPER, 4)

## Vows (S48): each forbids one thing while held and gives a steady gift; letting one go breaks it.
func _vows(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := content
	panel(r)
	para(Rect2(r.position.x + 24, r.position.y + 14, r.size.x - 48, 50), Tx.t("ui.cultivation.vows_intro") % int(ContentDB.config("vows").get("break_heart_demon", 15)), 17, UiKit.MIST, 2)
	var vows := ContentDB.all("vows")
	var top := r.position.y + 74
	var h := (r.end.y - top - 12) / float(maxi(1, vows.size()))
	for i in vows.size():
		var v: Dictionary = vows[i]
		var held := str(v.id) in cu.vows
		var vr := Rect2(r.position.x + 20, top + i * h, r.size.x - 40, h - 10)
		panel(vr, "minor_panel", "selected" if held else "normal")
		var mid := vr.size.y * 0.5
		text(vr.position + Vector2(18, mid + 8), str(v.get("name", "")), 22, UiKit.PALE_GOLD if held else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 200, true)
		text(vr.position + Vector2(230, mid - 4), str(v.get("desc", "")), 17, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, vr.size.x - 440)
		text(vr.position + Vector2(230, mid + 20), str(v.get("gift_text", "")), 16, UiKit.BRIGHT_JADE if held else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, vr.size.x - 440)
		if held:
			btn(Rect2(vr.end.x - 190, vr.position.y + (vr.size.y - 46) * 0.5, 172, 46), Tx.t("ui.cultivation.break_vow"), "vow_off", str(v.id), false, true, "", 18)
		else:
			btn(Rect2(vr.end.x - 190, vr.position.y + (vr.size.y - 46) * 0.5, 172, 46), Tx.t("ui.cultivation.take_vow"), "vow_on", str(v.id), true, true, "", 18)

## Heart (G1): the meter, the ledger, the foundation and what the pills have left behind.
func _heart(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var left := Rect2(content.position.x, content.position.y, 540, content.size.y)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(left)
	panel(right)
	var x := left.position.x + 24
	var y := left.position.y + 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.heart_demons"), left.size.x - 48)
	y += 26
	var hb := Rect2(x, y, left.size.x - 48, 30)
	# Red once it adds a risk step at great breakthroughs (25 and more, S48); a dull rose below that.
	bar(hb, cu.heart_demon / 100.0, Color("d0283c") if ProgressionRules.heart_demon_steps(cu) > 0 else Color("7a4a56"), "%d / 100" % int(cu.heart_demon))
	for k in [25, 50, 75]:
		var tx: float = hb.position.x + hb.size.x * float(k) / 100.0
		draw_line(Vector2(tx, hb.position.y - 4), Vector2(tx, hb.end.y + 4), Color(UiKit.PALE_GOLD, 0.7), 2)
	y += 62
	var steps := ProgressionRules.heart_demon_steps(cu)
	para(Rect2(x, y - 20, left.size.x - 48, 70), Tx.t("ui.cultivation.heart_demon_steps") % steps if steps > 0 else Tx.t("ui.cultivation.heart_calm"), 17,
		UiKit.RED if steps > 0 else UiKit.MIST, 3)
	y += 70
	heading(Vector2(x, y), Tx.t("ui.cultivation.karma"), left.size.x - 48)
	y += 40
	text(Vector2(x, y), Tx.t("ui.cultivation.merit") % cu.merit, 21, UiKit.PALE_GOLD)
	text(Vector2(x + 250, y), Tx.t("ui.cultivation.sin") % cu.sin, 21, Color("e07a7a"))
	y += 28
	var merit_ready := ProgressionRules.merit_step(cu) > 0
	text(Vector2(x, y), Tx.t("ui.cultivation.merit_ready") if merit_ready else Tx.t("ui.cultivation.merit_not_ready") % int(ContentDB.stat_const("karma", {}).get("merit_step", 100)),
		16, UiKit.BRIGHT_JADE if merit_ready else UiKit.MIST)
	y += 34
	for id in cu.debts:
		var d: Dictionary = cu.debts[id]
		text(Vector2(x, y), Tx.t("ui.cultivation.debt_" + str(id)), 17, UiKit.PAPER)
		text(Vector2(left.end.x - 24, y), Tx.t("ui.cultivation.debt_settled") if d.get("paid", false) else Tx.t("ui.cultivation.debt_open"), 16,
			UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, -1)
		y += 26
	# S48 fates: the cards chosen at major breakthroughs, and one waiting to be chosen.
	if not cu.fates.is_empty() or not cu.fate_offer.is_empty():
		y += 16
		heading(Vector2(x, y + 20), Tx.t("ui.cultivation.fates"), left.size.x - 48)
		y += 44
		if not cu.fate_offer.is_empty():
			btn(Rect2(x, y, left.size.x - 48, 44), Tx.t("ui.cultivation.choose_fate"), "fates", null, true, true, "", 19)
			y += 52
		var names: Array = []
		for rec in cu.fates: names.append(ContentDB.name_of("fates", str(rec.get("id", ""))))
		if not names.is_empty(): para(Rect2(x, y - 14, left.size.x - 48, maxf(24.0, left.end.y - y)), ", ".join(names), 16, UiKit.PAPER, 3)
	# Right: foundation, residue, resistance.
	x = right.position.x + 24
	y = right.position.y + 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.foundation_share"), right.size.x - 48)
	y += 26
	var share := ProgressionRules.foundation_share(cu)
	var hollow_at := float(ContentDB.stat_const("pill_life", {}).get("hollow_share", 0.3))
	var fb := Rect2(x, y, right.size.x - 48, 30)
	bar(fb, share, Color("c8923e") if share > hollow_at else UiKit.JADE, "%d%%" % int(round(share * 100)))
	var hx := fb.position.x + fb.size.x * hollow_at
	draw_line(Vector2(hx, fb.position.y - 4), Vector2(hx, fb.end.y + 4), UiKit.RED, 2)
	y += 60
	para(Rect2(x, y - 20, right.size.x - 48, 60), Tx.t("ui.cultivation.foundation_hollow") if share > hollow_at else Tx.t("ui.cultivation.foundation_sound"), 16,
		Color("e0a860") if share > hollow_at else UiKit.MIST, 2)
	y += 56
	heading(Vector2(x, y), Tx.t("ui.cultivation.residue"), right.size.x - 48)
	y += 36
	var pen := int(round(ProgressionRules.residue_penalty(cu) * 100))
	text(Vector2(x, y), Tx.t("ui.cultivation.residue_value") % [cu.residue, pen] if pen > 0 else Tx.t("ui.cultivation.residue_harmless") % cu.residue, 18,
		UiKit.PAPER if pen == 0 else Color("e0a860"))
	y += 44
	heading(Vector2(x, y), Tx.t("ui.cultivation.pill_resistance"), right.size.x - 48)
	y += 36
	if cu.pill_resistance.is_empty():
		text(Vector2(x, y), Tx.t("ui.cultivation.no_resistance"), 17, UiKit.MIST)
	for fam in cu.pill_resistance:
		text(Vector2(x, y), Tx.t("ui.cultivation.family_" + str(fam)), 18, UiKit.PAPER)
		var rr: Dictionary = cu.pill_resistance[fam]
		text(Vector2(right.end.x - 24, y), Tx.t("ui.cultivation.resistance_row") % [int(rr.get("count", 0)), int(rr.get("doses", 0)),
			int(round(ProgressionRules.resistance_factor(cu, str(fam)) * 100))], 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, -1)
		y += 28

func _methods(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	if cu.methods_known.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.cultivation.you_know_no_cultivation_method"), 21, UiKit.MIST)
		return
	list("methods", r.grow(-14), cu.methods_known.size(), 110, func(i: int, rr: Rect2):
		var mid := str(cu.methods_known[i])
		var m := ProgressionRules.method(mid)
		var active := mid == cu.method_id
		panel(rr, "minor_panel", "selected" if active else "normal")
		text(rr.position + Vector2(20, 34), ContentDB.name_of("methods", mid), 24, UiKit.PALE_GOLD if active else UiKit.PAPER)
		text(rr.position + Vector2(20, 64), Tx.t("ui.cultivation.affinity_rate_2f_capacity_2f") % [str(m.get("grade", "")).capitalize(),
			str(m.get("affinity", "none")).capitalize(), float(m.get("rate", 1.0)), float(m.get("capacity", 1.0)), ContentDB.name_of("realms", str(m.get("ceiling", "")))], 16, UiKit.MIST)
		text(rr.position + Vector2(20, 90), Tx.t("ui.cultivation.compatibility") % ProgressionRules.method_compatibility(ch, mid).capitalize(), 16, UiKit.BRIGHT_JADE)
		if not active: btn(Rect2(rr.end.x - 170, rr.position.y + 26, 150, 50), Tx.t("ui.cultivation.switch"), "switch", mid)
		else: text(Vector2(rr.end.x - 170, rr.position.y + 58), Tx.t("ui.cultivation.active"), 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 150)
	)

func _dao(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	var ids: Array = cu.daos.keys()
	if ids.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.cultivation.no_dao_insight_yet_use"), 21, UiKit.MIST)
		return
	var tiers := [Tx.t("ui.cultivation.unaware"), Tx.t("ui.cultivation.observation"), Tx.t("ui.cultivation.imitation"), Tx.t("ui.cultivation.reliable_execution"), Tx.t("ui.cultivation.explanation"), Tx.t("ui.cultivation.adaptation"), Tx.t("ui.cultivation.original_application")]
	list("daos", r.grow(-14), ids.size(), 76, func(i: int, rr: Rect2):
		var d := str(ids[i])
		var st: Dictionary = cu.daos[d]
		var tier := int(st.get("tier", 0))
		text(rr.position + Vector2(20, 32), ContentDB.name_of("daos", d), 22, UiKit.PAPER)
		text(rr.position + Vector2(20, 60), tiers[clampi(tier, 0, tiers.size() - 1)], 16, UiKit.GOLD)
		var ins := float(st.get("insight", 0.0))
		var need := float(ContentDB.curve("dao_tiers", [0, 100, 400, 1200, 3000, 8000, 20000])[mini(tier + 1, 6)])
		bar(Rect2(rr.position.x + 330, rr.position.y + 18, 520, 30), ins / maxf(1.0, need), UiKit.SOUL, Tx.t("ui.cultivation.insight_2") % [UiKit.fmt(ins), UiKit.fmt(need)])
		if Unlocks.is_unlocked(ch.id, "contemplate"):
			btn(Rect2(rr.end.x - 170, rr.position.y + 12, 150, 44), Tx.t("ui.cultivation.contemplate"), "contemplate", d)
	)

func _seclusion(ch) -> void:
	var r := Rect2(content.position.x, content.position.y, content.size.x, content.size.y)
	panel(r)
	var room: Dictionary = Game.room_rt.def if Game.room_rt else {}
	var cap := Game.progression.seclusion_cap(room)
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 90)), Tx.t("ui.cultivation.choose_what_to_cultivate_while") % int(cap), 19, UiKit.PAPER)
	var foci := [["accumulate", Tx.t("ui.cultivation.accumulate"), Tx.t("ui.cultivation.realm_progress"), "seclusion"], ["temper_body", Tx.t("ui.cultivation.temper_body"), Tx.t("ui.cultivation.body_training"), "seclusion"],
		["heal", Tx.t("ui.cultivation.heal"), Tx.t("ui.cultivation.treat_injuries"), "seclusion"], ["contemplate", Tx.t("ui.cultivation.contemplate"), Tx.t("ui.cultivation.dao_insight"), "insight_sites"],
		["refine_qi", Tx.t("ui.cultivation.refine_qi"), Tx.t("ui.cultivation.purity"), "refine_qi"], ["nourish_soul", Tx.t("ui.cultivation.nourish_soul"), Tx.t("ui.cultivation.soul"), "nourish_soul"],
		["settle_foundation", Tx.t("ui.cultivation.settle_foundation"), Tx.t("ui.cultivation.settle_foundation_desc"), "seclusion"]]
	# S44: a medicinal bath takes the seclusion slot at a Bath station.
	var bath_item := _bath_item(ch)
	foci.append(["bath", Tx.t("ui.cultivation.bath"), Tx.t("ui.cultivation.bath_desc") % [ContentDB.item_name(bath_item), ch.inventory.count(bath_item)]
		if bath_item != "" else Tx.t("ui.cultivation.bath_none"), "medicinal_bath"])
	var cur := str(ch.seclusion.get("focus", ""))
	for i in foci.size():
		var f: Array = foci[i]
		var rr := Rect2(r.position.x + 24 + (i % 3) * 330, r.position.y + 120 + (i / 3) * 130, 310, 112)
		var ok := Unlocks.is_unlocked(ch.id, f[3])
		panel(rr, "minor_panel", "selected" if cur == f[0] else ("disabled" if not ok else "normal"))
		text(rr.position + Vector2(20, 40), f[1], 24, UiKit.PAPER if ok else UiKit.HOLLOW)
		text(rr.position + Vector2(20, 72), f[2], 17, UiKit.MIST)
		region(rr, "focus", f[0], ok, Unlocks.locked_text(f[3]))
	if cur != "":
		text(Vector2(r.position.x + 24, r.end.y - 30), Tx.t("ui.cultivation.set_close_the_game_and") % cur.replace("_", " ").capitalize(), 19, UiKit.BRIGHT_JADE)

## The strongest bath in the bag, or "".
func _bath_item(ch) -> String:
	var best := ""
	for s in ch.inventory.bag:
		if s != null and ContentDB.item(str(s.id)).has("bath"):
			if best == "" or StatRules.grade_index(str(ContentDB.item(str(s.id)).get("grade", "plain"))) > StatRules.grade_index(str(ContentDB.item(best).get("grade", "plain"))):
				best = str(s.id)
	return best

func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"meditate":
			if submit({"type": "toggle_meditation"}).get("ok", false): close()
		"breakthrough": navigate.emit("breakthrough", {})
		"fates": navigate.emit("fates", {})
		"vow_on": submit({"type": "set_vow", "vow": str(data), "on": true})
		"vow_off": ask(Tx.t("ui.cultivation.break_vow_confirm") % [ContentDB.name_of("vows", str(data)), int(ContentDB.config("vows").get("break_heart_demon", 15))], "vow_break", data, true)
		"vow_break": submit({"type": "set_vow", "vow": str(data), "on": false})
		"meridian": submit({"type": "open_meridian", "channel": str(data)})
		"reset_meridians": ask(Tx.t("ui.cultivation.reset_all_meridian_points"), "reset_yes")
		"reset_yes": submit({"type": "reset_meridians"})
		"switch":
			var cost := Game.progression.method_switch_preview(ch, false)
			ask(Tx.t("ui.cultivation.switch_method_you_lose_qp") % UiKit.fmt(cost), "switch_yes", data)
		"switch_yes": submit({"type": "switch_method", "id": str(data)})
		"contemplate":
			submit({"type": "set_contemplate", "dao": str(data)})
			flash(Tx.t("ui.cultivation.contemplating_in_seclusion") % ContentDB.name_of("daos", str(data)))
		"focus":
			if str(data) == "bath":
				var rb := submit({"type": "start_bath", "item": _bath_item(ch)})
				if rb.get("ok", false): flash(Tx.t("ui.cultivation.seclusion_set"))
				elif str(rb.get("text", "")) != "": flash(str(rb.text))
				return
			if submit({"type": "enter_seclusion", "focus": str(data)}).get("ok", false): flash(Tx.t("ui.cultivation.seclusion_set"))
