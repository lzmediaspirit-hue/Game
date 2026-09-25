extends Page
## Notice board (S19/S20): today's sect missions, open side quests nearby and field
## boss timers. S49: a second tab posts the town's bounties on named targets.

func _init() -> void:
	title = Tx.t("ui.notice.notice_board")
	tabs = [{"id": "board", "label": Tx.t("ui.notice.tab_board")}, {"id": "bounties", "label": Tx.t("ui.notice.tab_bounties")}]

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if str(tabs[tab].id) == "bounties":
		_bounties(ch)
		return
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

## S49: the town's bounties on named targets. Take two at a time, each once a day; the target waits in its room.
func _bounties(ch) -> void:
	var r := Rect2(content.position, content.size)
	panel(r)
	var rows: Array = Game.relations.fcfg().get("bounties", [])
	var mine: Array = ch.relations.bounties.map(func(b): return str(b.get("id", "")))
	var y := r.position.y + 16
	for b in rows:
		var row := Rect2(r.position.x + 18, y, r.size.x - 36, 138)
		panel(row, "minor_panel", "selected" if mine.has(str(b.id)) else "normal")
		var x := row.position.x + 18
		text(Vector2(x, row.position.y + 34), ContentDB.name_of("enemies", str(b.target)), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
		text(Vector2(x + 250, row.position.y + 34), fit(ContentDB.name_of("factions", str(b.faction)) + "  ·  " + ContentDB.name_of("rooms", str(b.room)), 16, row.size.x - 520), 16, UiKit.MIST)
		para(Rect2(x, row.position.y + 46, row.size.x - 300, 60), str(b.get("text", "")), 16, UiKit.PAPER, 2)
		var rw: Dictionary = b.get("reward", {})
		currency_pill(Vector2(x, row.end.y - 36), str(rw.get("currency", "silver_tael")), int(rw.get("amount", 0)))
		var ok_realm := ProgressionRules.at_least(ch.cultivator.realm_key, str(b.get("realm", "")))
		var bx := row.end.x - 250
		if mine.has(str(b.id)):
			text(Vector2(bx, row.position.y + 76), Tx.t("ui.notice.bounty_hunting"), 18, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, 230)
		else:
			btn(Rect2(bx, row.position.y + 44, 230, 54), Tx.t("ui.notice.take_bounty"), "bounty", str(b.id), true, ok_realm,
				Tx.t("req.reach") % ContentDB.name_of("realms", str(b.get("realm", ""))), 18)
		y += 148

func on_action(id: String, data) -> void:
	if id == "bounty": submit({"type": "take_bounty", "id": str(data)})
	queue_redraw()
