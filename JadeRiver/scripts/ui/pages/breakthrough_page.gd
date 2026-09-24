extends Page
## Breakthrough dialog (S05): requirements with their fixes, support items that
## lower the risk, risk word and success chance, then the 3 s channel.

var supports: Array = []

func _init() -> void:
	title = "Breakthrough"

func support_candidates(ch) -> Array:
	var out: Array = []
	for s in ch.inventory.bag:
		if s != null and ContentDB.item(str(s.id)).has("support") and not out.has(str(s.id)): out.append(str(s.id))
	return out

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var q: Dictionary = Game.progression.query_breakthrough(ch, supports)
	var left := Rect2(content.position.x, content.position.y, 640, content.size.y)
	panel(left)
	text(left.position + Vector2(24, 44), "%s  →  %s" % [ContentDB.name_of("realms", str(q.from)), ContentDB.name_of("realms", str(q.to))], 28, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	if str(q.get("event", "")) != "":
		text(left.position + Vector2(24, 76), "Trial: %s" % ContentDB.text("event." + str(q.event)), 19, UiKit.SOUL)
	var y := left.position.y + 100
	if not q.major:
		para(Rect2(left.position.x + 24, y, 590, 100), "A minor step within the realm. No requirements and no risk once the progress bar is full.", 20)
	for r in q.get("results", []):
		var ok: bool = r.ok
		draw_circle(Vector2(left.position.x + 36, y + 16), 10, UiKit.JADE if ok else (UiKit.RED if r.hard else Color("f0a040")))
		if ok: draw_line(Vector2(left.position.x + 31, y + 16), Vector2(left.position.x + 36, y + 21), UiKit.INK, 2)
		text(Vector2(left.position.x + 58, y + 22), str(r.text), 19, UiKit.PAPER)
		text(Vector2(left.position.x + 58, y + 44), ("Required" if r.hard else "Soft: raises risk if unmet") + " · " + str(r.cause).capitalize(), 15, UiKit.MIST)
		var fix := str(r.get("fix", ""))
		if not ok and fix.begins_with("page:"): btn(Rect2(left.end.x - 130, y + 4, 110, 40), "Go", "fix", fix.trim_prefix("page:"))
		y += 58
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(24, 40), "Support", right.size.x - 48)
	var cands := support_candidates(ch)
	if cands.is_empty(): text(right.position + Vector2(24, 80), "No support items.", 18, UiKit.HOLLOW)
	for i in cands.size():
		var r2 := Rect2(right.position.x + 24 + (i % 4) * 76, right.position.y + 60 + (i / 4) * 76, 66, 66)
		slot_box(r2, str(cands[i]), ch.inventory.count(str(cands[i])), "", "support", str(cands[i]), supports.has(cands[i]))
	var yy := right.end.y - 210
	for reason in q.get("reasons", []):
		text(Vector2(right.position.x + 24, yy), "· " + str(reason), 16, UiKit.MIST)
		yy += 22
	var risk_col = {"none": UiKit.JADE, "low": UiKit.JADE, "moderate": Color("f0a040"), "high": UiKit.RED, "severe": UiKit.RED}.get(str(q.risk), UiKit.PAPER)
	text(Vector2(right.position.x + 24, right.end.y - 96), "Risk: %s" % str(q.risk).capitalize(), 24, risk_col, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(right.position.x + 24, right.end.y - 70), "Success %d%%" % int(float(q.success) * 100), 19, UiKit.PAPER)
	btn(Rect2(right.end.x - 250, right.end.y - 76, 226, 58), "Break Through", "go", null, true, bool(q.can), str(q.blocked))

func on_action(id: String, data) -> void:
	match id:
		"support":
			if supports.has(data): supports.erase(data)
			elif supports.size() < 3: supports.append(data)
		"fix": navigate.emit(str(data), {})
		"go":
			var r := submit({"type": "start_breakthrough", "support_items": supports})
			if r.get("ok", false): close()
