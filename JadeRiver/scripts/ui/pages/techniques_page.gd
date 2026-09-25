extends Page
## Techniques (S09, Part 9.8): known techniques with mastery, the equipped slots,
## and secret arts. Tap a technique, then a slot, to equip it.

var picked := ""
var picked_art := ""

func _init() -> void:
	title = Tx.t("ui.techniques.techniques")
	tabs = [{"id": "combat", "label": Tx.t("ui.techniques.combat")}, {"id": "inner", "label": Tx.t("ui.techniques.inner_arts")},
		{"id": "secret", "label": Tx.t("ui.techniques.secret_arts")}]

## The realm that opens Inner Art slot `i` (slots.json rows: [realm, slots open from it]).
func _slot_realm(i: int) -> String:
	for row in ContentDB.config("inner_arts").get("slots", []):
		if int(row[1]) > i: return str(row[0])
	return "spirit_awakening_1"

## Inner Arts and stances (S48): the slots across the top, the arts known below, a stance for each weapon family.
func _inner(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var n := ProgressionRules.inner_art_slot_count(cu.realm_key)
	var fam := str(StatRules.family(ch).get("id", "fists"))
	for i in 4:
		var r2 := Rect2(content.position.x + i * 250, content.position.y, 236, 70)
		var art := str(cu.inner_arts[i]) if i < cu.inner_arts.size() else ""
		if i >= n:
			draw_style_box(UiKit.style("slot", "disabled"), r2)
			text(r2.position + Vector2(0, 42), Tx.t("ui.techniques.inner_slot_locked") % ContentDB.name_of("realms", _slot_realm(i)), 15, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r2.size.x)
			continue
		panel(r2, "minor_panel", "selected" if picked_art != "" else "normal")
		if art == "":
			text(r2.position + Vector2(0, 42), Tx.t("ui.techniques.inner_slot_empty"), 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, r2.size.x)
		else:
			var d := ContentDB.entry("inner_arts", art)
			var sleeping := str(d.get("family", "")) != "" and str(d.family) != fam
			text(r2.position + Vector2(14, 30), str(d.get("name", art)), 18, UiKit.MIST if sleeping else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r2.size.x - 28)
			text(r2.position + Vector2(14, 54), Tx.t("ui.techniques.inner_sleeping") % str(d.family).replace("_", " ") if sleeping else fit(str(d.get("desc", "")), 14, r2.size.x - 28), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r2.size.x - 28)
		region(r2, "art_slot", i)
	var y0 := content.position.y + 86
	var left := Rect2(content.position.x, y0, content.size.x * 0.56, content.end.y - y0)
	var right := Rect2(left.end.x + 16, y0, content.end.x - left.end.x - 16, content.end.y - y0)
	panel(left)
	panel(right)
	if cu.inner_arts_known.is_empty():
		para(Rect2(left.position + Vector2(20, 20), left.size - Vector2(40, 40)), Tx.t("ui.techniques.no_inner_arts") if n > 0 else Tx.t("sim.progression.inner_arts_locked"), 18, UiKit.MIST)
	else:
		var top := 12.0
		if picked_art != "":
			text(Vector2(left.position.x + 20, left.position.y + 28), Tx.t("ui.techniques.tap_a_slot_to_wear"), 16, UiKit.GOLD)
			top = 40.0
		list("arts", Rect2(left.position.x + 10, left.position.y + top, left.size.x - 20, left.size.y - top - 10), cu.inner_arts_known.size(), 64, func(i: int, rr: Rect2):
			var aid := str(cu.inner_arts_known[i])
			var d := ContentDB.entry("inner_arts", aid)
			var worn := aid in cu.inner_arts
			panel(rr, "minor_panel", "selected" if picked_art == aid else "normal")
			text(rr.position + Vector2(14, 26), str(d.get("name", aid)) + ("  ·  " + Tx.t("ui.techniques.worn") if worn else ""), 18, UiKit.PALE_GOLD if worn else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 28)
			text(rr.position + Vector2(14, 50), fit(str(d.get("desc", "")), 15, rr.size.x - 28), 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 28)
			region(rr, "pick_art", aid)
		)
	# Stances: one per weapon family, held only with that weapon in hand.
	var sx := right.position.x + 18
	var sy := right.position.y + 36
	heading(Vector2(sx, sy), Tx.t("ui.techniques.stances"), right.size.x - 36)
	sy += 14
	var can := Unlocks.is_unlocked(ch.id, "stances")
	var step := minf(58.0, (right.end.y - sy - 8) / float(maxi(1, ContentDB.all("stances").size())))
	for st in ContentDB.all("stances"):
		var on := str(cu.stances.get(str(st.family), "")) == str(st.id)
		var here := str(st.family) == fam
		text(Vector2(sx, sy + 20), str(st.get("name", "")) + "  ·  " + str(st.family).replace("_", " ").capitalize(), 17, UiKit.PALE_GOLD if on and here else (UiKit.PAPER if here else UiKit.MIST), HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 150)
		text(Vector2(sx, sy + 40), fit(str(st.get("desc", "")), 14, right.size.x - 150), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 150)
		btn(Rect2(right.end.x - 116, sy + 6, 100, 38), Tx.t("ui.techniques.stance_on") if on else Tx.t("ui.techniques.stance_off"), "stance", str(st.id), on, can, Unlocks.locked_text("stances"), 16)
		sy += step

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cu: CultivatorState = ch.cultivator
	if str(tabs[tab].id) == "inner":
		_inner(ch)
		return
	if str(tabs[tab].id) == "secret":
		var r := Rect2(content.position, content.size)
		panel(r)
		var arts: Array = cu.secret_arts if cu.get("secret_arts") != null else []
		if arts.is_empty(): text(r.position + Vector2(0, 80), Tx.t("ui.techniques.no_secret_arts_yet"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		for i in arts.size():
			var d := ContentDB.entry("secret_arts", str(arts[i]))
			text(r.position + Vector2(24, 44 + i * 64), str(d.get("name", arts[i])), 22, UiKit.PALE_GOLD)
			text(r.position + Vector2(24, 68 + i * 64), str(d.get("desc", "")), 16, UiKit.MIST)
			# S48: Concealment can show a false realm, up to two great realms lower.
			if str(arts[i]) == "concealment":
				var choices: Array = [""] + Game.progression.false_realm_choices(ch)
				var bx := r.end.x - 24.0
				for j in range(choices.size() - 1, -1, -1):
					var key := str(choices[j])
					var label := Tx.t("ui.techniques.true_realm") if key == "" else ContentDB.realm_label(key)
					var w := maxf(120.0, UiKit.text_width(label, 16) + 28.0)
					bx -= w
					btn(Rect2(bx, r.position.y + 26 + i * 64, w, 40), label, "false_realm", key, cu.false_realm == key, true, "", 16)
					bx -= 8.0
		return
	# Equipped slots across the top.
	var n := ProgressionRules.technique_slot_count(ch)
	for i in 8:
		var r2 := Rect2(content.position.x + i * 92, content.position.y, 80, 80)
		var tid = cu.technique_slots[i] if i < cu.technique_slots.size() else null
		if i >= n:
			draw_style_box(UiKit.style("slot", "disabled"), r2)
			_lock_icon(r2.get_center() - Vector2(6, 8))
			region(r2, "slot", i, false, Tx.t("ui.techniques.more_slots_open_with_your"))
		else:
			slot_box(r2, "", 0, "", "", null)
			if tid != null: icon_at(r2.grow(-8), str(tid))
			region(r2, "slot", i)
		text(Vector2(r2.position.x, r2.end.y + 18), str(i + 1), 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 80)
	if picked != "": text(Vector2(content.position.x + 760, content.position.y + 48), Tx.t("ui.techniques.tap_a_slot_to_equip"), 18, UiKit.GOLD)
	var list_r := Rect2(content.position.x, content.position.y + 116, content.size.x, content.size.y - 116)
	panel(list_r)
	var known: Array = cu.techniques_known
	if known.is_empty():
		para(Rect2(list_r.position + Vector2(24, 24), list_r.size - Vector2(48, 48)), Tx.t("ui.techniques.no_techniques_learned_at_qi"), 20, UiKit.MIST)
		return
	list("tech", list_r.grow(-12), known.size(), 96, func(i: int, rr: Rect2):
		var tid := str(known[i])
		var d := ContentDB.entry("techniques", tid)
		var m: Dictionary = cu.mastery.get(tid, {"tier": 1, "points": 0.0})
		panel(rr, "minor_panel", "selected" if picked == tid else "normal")
		icon_at(Rect2(rr.position + Vector2(12, 12), Vector2(64, 64)), tid)
		text(rr.position + Vector2(92, 32), str(d.get("name", tid)), 22, UiKit.PAPER)
		var g := str(d.get("grade", "common"))
		text(rr.position + Vector2(92 + UiKit.text_width(str(d.get("name", tid)), 22) + 14, 32), Tx.t("ui.techniques.grade_" + g), 15, UiKit.grade_color(g))
		text(rr.position + Vector2(92, 56), Tx.t("ui.techniques.qi_ds") % [str(d.get("family", "")).capitalize(), str(d.get("element", "none")).capitalize(), int(d.get("qi_cost", 0)), int(d.get("cooldown_s", 0))], 15, UiKit.MIST)
		text(rr.position + Vector2(92, 80), fit(str(d.get("desc", "")), 15, rr.size.x - 110), 15, UiKit.PAPER)
		var tier := int(m.get("tier", 1))
		bar(Rect2(rr.end.x - 330, rr.position.y + 14, 200, 26), float(m.get("points", 0.0)) / ProgressionRules.mastery_needed(tier), UiKit.GOLD, Tx.t("ui.techniques.tier") % tier)
		if tier >= 3 and tier < 6: btn(Rect2(rr.end.x - 120, rr.position.y + 10, 104, 40), Tx.t("ui.techniques.rank_up"), "rank", tid)
		region(rr, "pick", tid)
	)

func on_action(id: String, data) -> void:
	match id:
		"pick": picked = "" if picked == str(data) else str(data)
		"slot":
			var ch = c()
			var cur = ch.cultivator.technique_slots[int(data)]
			if picked != "":
				submit({"type": "equip_technique", "slot": int(data), "id": picked})
				picked = ""
			elif cur != null:
				submit({"type": "unequip_technique", "slot": int(data)})
		"rank": submit({"type": "rank_up_technique", "id": str(data)})
		"pick_art": picked_art = "" if picked_art == str(data) else str(data)
		"false_realm": submit({"type": "set_false_realm", "realm": str(data)})
		"art_slot":
			var cu = c().cultivator
			var cur_art := str(cu.inner_arts[int(data)]) if int(data) < cu.inner_arts.size() else ""
			if picked_art != "":
				submit({"type": "equip_inner_art", "slot": int(data), "art": picked_art})
				picked_art = ""
			elif cur_art != "":
				submit({"type": "equip_inner_art", "slot": int(data), "art": ""})
		"stance":
			var st := ContentDB.entry("stances", str(data))
			var on := str(c().cultivator.stances.get(str(st.family), "")) == str(data)
			submit({"type": "set_stance", "family": str(st.family), "stance": "" if on else str(data)})
