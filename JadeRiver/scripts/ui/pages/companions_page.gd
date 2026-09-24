extends Page
## Companions (S26): choose up to two active fellow disciples.

func _init() -> void:
	title = "Companions"

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var roster: Array = ch.companions.get("roster", [])
	var active: Array = ch.companions.get("active", [])
	var r := Rect2(content.position, content.size)
	panel(r)
	if roster.is_empty():
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), "Fellow disciples join you from Qi Kindling 5. Your mentor will introduce them.", 21, UiKit.MIST)
		return
	for i in roster.size():
		var cid := str(roster[i])
		var d := ContentDB.entry("companions", cid)
		var cr := Rect2(r.position.x + 20 + i * 270, r.position.y + 20, 250, 360)
		panel(cr, "minor_panel", "selected" if active.has(cid) else "normal")
		text(cr.position + Vector2(0, 250), str(d.get("name", cid)), 24, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		text(cr.position + Vector2(0, 280), "%s · %s" % [str(d.get("role", "")).capitalize(), str(d.get("element", "")).capitalize()], 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cr.size.x)
		btn(Rect2(cr.position.x + 30, cr.end.y - 64, 190, 50), "Active ✓" if active.has(cid) else "Bring along", "toggle", cid, active.has(cid))

func on_action(id: String, data) -> void:
	if id != "toggle": return
	var active: Array = c().companions.get("active", []).duplicate()
	if active.has(data): active.erase(data)
	else:
		active.append(data)
		while active.size() > 2: active.pop_front()
	submit({"type": "set_active_companions", "ids": active})
