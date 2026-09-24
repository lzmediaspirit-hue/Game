extends Page
## Techniques (S09, Part 9.8): known techniques with mastery, the equipped slots,
## and secret arts. Tap a technique, then a slot, to equip it.

var picked := ""

func _init() -> void:
	title = "Techniques"
	tabs = [{"id": "combat", "label": "Combat"}, {"id": "secret", "label": "Secret Arts"}]

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cu: CultivatorState = ch.cultivator
	if str(tabs[tab].id) == "secret":
		var r := Rect2(content.position, content.size)
		panel(r)
		var arts: Array = cu.secret_arts if cu.get("secret_arts") != null else []
		if arts.is_empty(): text(r.position + Vector2(0, 80), "No secret arts yet.", 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		for i in arts.size():
			var d := ContentDB.entry("secret_arts", str(arts[i]))
			text(r.position + Vector2(24, 44 + i * 64), str(d.get("name", arts[i])), 22, UiKit.PALE_GOLD)
			text(r.position + Vector2(24, 68 + i * 64), str(d.get("desc", "")), 16, UiKit.MIST)
		return
	# Equipped slots across the top.
	var n := ProgressionRules.technique_slot_count(ch)
	for i in 8:
		var r2 := Rect2(content.position.x + i * 92, content.position.y, 80, 80)
		var tid = cu.technique_slots[i] if i < cu.technique_slots.size() else null
		if i >= n:
			draw_style_box(UiKit.style("slot", "disabled"), r2)
			_lock_icon(r2.get_center() - Vector2(6, 8))
			region(r2, "slot", i, false, "More slots open with your realm")
		else:
			slot_box(r2, "", 0, "", "", null)
			if tid != null: icon_at(r2.grow(-8), str(tid))
			region(r2, "slot", i)
		text(Vector2(r2.position.x, r2.end.y + 18), str(i + 1), 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 80)
	if picked != "": text(Vector2(content.position.x + 760, content.position.y + 48), "Tap a slot to equip", 18, UiKit.GOLD)
	var list_r := Rect2(content.position.x, content.position.y + 116, content.size.x, content.size.y - 116)
	panel(list_r)
	var known: Array = cu.techniques_known
	if known.is_empty():
		para(Rect2(list_r.position + Vector2(24, 24), list_r.size - Vector2(48, 48)), "No techniques learned. At Qi Kindling your training hall master will teach you your first.", 20, UiKit.MIST)
		return
	list("tech", list_r.grow(-12), known.size(), 96, func(i: int, rr: Rect2):
		var tid := str(known[i])
		var d := ContentDB.entry("techniques", tid)
		var m: Dictionary = cu.mastery.get(tid, {"tier": 1, "points": 0.0})
		panel(rr, "minor_panel", "selected" if picked == tid else "normal")
		icon_at(Rect2(rr.position + Vector2(12, 12), Vector2(64, 64)), tid)
		text(rr.position + Vector2(92, 32), str(d.get("name", tid)), 22, UiKit.PAPER)
		text(rr.position + Vector2(92, 56), "%s · %s · QI %d · %ds" % [str(d.get("family", "")).capitalize(), str(d.get("element", "none")).capitalize(), int(d.get("qi_cost", 0)), int(d.get("cooldown_s", 0))], 15, UiKit.MIST)
		text(rr.position + Vector2(92, 80), str(d.get("desc", "")).left(90), 15, UiKit.PAPER)
		var tier := int(m.get("tier", 1))
		bar(Rect2(rr.end.x - 330, rr.position.y + 14, 200, 26), float(m.get("points", 0.0)) / ProgressionRules.mastery_needed(tier), UiKit.GOLD, "Tier %d" % tier)
		if tier >= 3 and tier < 6: btn(Rect2(rr.end.x - 120, rr.position.y + 10, 104, 40), "Rank up", "rank", tid)
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
