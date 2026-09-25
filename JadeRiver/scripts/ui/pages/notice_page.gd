extends Page
## Notice board (S19/S20): today's sect missions, open side quests nearby and field
## boss timers.

func _init() -> void:
	title = Tx.t("ui.notice.notice_board")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position.x, content.position.y, content.size.x * 0.5 - 10, content.size.y)
	var right := Rect2(left.end.x + 20, content.position.y, left.size.x, content.size.y)
	panel(left)
	panel(right)
	heading(left.position + Vector2(20, 40), Tx.t("ui.notice.sect_missions"), left.size.x - 40)
	var y := left.position.y + 60
	if ch.quests.daily.is_empty():
		para(Rect2(left.position.x + 20, y, left.size.x - 40, 100), Tx.t("ui.notice.missions_open_at_bone_forging") if not Unlocks.is_unlocked(ch.id, "daily_missions") else Tx.t("ui.notice.all_of_today_missions_are"), 18, UiKit.MIST)
	for q in ch.quests.daily:
		var d: Dictionary = ch.quests.daily[q]
		var st: Dictionary = ch.quests.active.get(q, {})
		var o: Dictionary = d.objectives[0]
		var have := int(st.get("progress", [0])[0]) if not st.is_empty() else 0
		text(Vector2(left.position.x + 20, y + 24), str(d.name), 19)
		text(Vector2(left.position.x + 20, y + 46), "%s (%d/%d)" % [str(o.get("text", "")), have, int(o.get("count", 1))], 16, UiKit.MIST)
		y += 60
	heading(right.position + Vector2(20, 40), Tx.t("ui.notice.requests"), right.size.x - 40)
	var yy := right.position.y + 60
	for qid in ch.quests.offered:
		var d2 := ContentDB.entry("quests", qid)
		if d2.is_empty() or str(d2.get("kind", "")) != "side" or not Game.quest.can_offer(ch, d2): continue
		text(Vector2(right.position.x + 20, yy + 24), str(d2.name), 19)
		text(Vector2(right.position.x + 20, yy + 46), Tx.t("ui.notice.ask") % ContentDB.name_of("npcs", str(d2.giver)), 16, UiKit.MIST)
		yy += 60
		if yy > right.end.y - 60: break
