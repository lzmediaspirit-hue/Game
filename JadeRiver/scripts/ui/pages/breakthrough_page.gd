extends Page
## Breakthrough dialog (S05): requirements with their fixes, support items that
## lower the risk, risk word and success chance, then the 3 s channel.

var supports: Array = []

func _init() -> void:
	title = Tx.t("ui.breakthrough.breakthrough")

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
		text(left.position + Vector2(24, 76), Tx.t("ui.breakthrough.trial") % ContentDB.text("event." + str(q.event)), 19, UiKit.SOUL)
	var y := left.position.y + 100
	if not q.major:
		para(Rect2(left.position.x + 24, y, 590, 100), Tx.t("ui.breakthrough.a_minor_step_within_the"), 20)
	for r in q.get("results", []):
		var ok: bool = r.ok
		draw_circle(Vector2(left.position.x + 36, y + 16), 10, UiKit.JADE if ok else (UiKit.RED if r.hard else Color("f0a040")))
		if ok: draw_line(Vector2(left.position.x + 31, y + 16), Vector2(left.position.x + 36, y + 21), UiKit.INK, 2)
		text(Vector2(left.position.x + 58, y + 22), str(r.text), 19, UiKit.PAPER)
		text(Vector2(left.position.x + 58, y + 44), (Tx.t("ui.breakthrough.required") if r.hard else Tx.t("ui.breakthrough.soft_raises_risk_if_unmet")) + " · " + str(r.cause).capitalize(), 15, UiKit.MIST)
		var fix := str(r.get("fix", ""))
		if not ok and fix.begins_with("page:"): btn(Rect2(left.end.x - 130, y + 4, 110, 40), Tx.t("ui.breakthrough.go"), "fix", fix.trim_prefix("page:"))
		y += 58
	# S48 Core Forging: into Cloud Stride the core forms, and how it was prepared sets its purity grade.
	if str(q.from) == "heart_tempering_9": _core_checklist(ch, Rect2(left.position.x + 24, y + 6, left.size.x - 48, left.end.y - y - 16))
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(24, 40), Tx.t("ui.breakthrough.support"), right.size.x - 48)
	var cands := support_candidates(ch)
	if cands.is_empty(): text(right.position + Vector2(24, 80), Tx.t("ui.breakthrough.no_support_items"), 18, UiKit.HOLLOW)
	for i in cands.size():
		var r2 := Rect2(right.position.x + 24 + (i % 4) * 76, right.position.y + 60 + (i / 4) * 76, 66, 66)
		slot_box(r2, str(cands[i]), ch.inventory.count(str(cands[i])), "", "support", str(cands[i]), supports.has(cands[i]))
	var yy := right.end.y - 210
	for reason in q.get("reasons", []):
		text(Vector2(right.position.x + 24, yy), "· " + str(reason), 16, UiKit.MIST)
		yy += 22
	var risk_col = {"none": UiKit.JADE, "low": UiKit.JADE, "moderate": Color("f0a040"), "high": UiKit.RED, "severe": UiKit.RED}.get(str(q.risk), UiKit.PAPER)
	text(Vector2(right.position.x + 24, right.end.y - 96), Tx.t("ui.breakthrough.risk") % str(q.risk).capitalize(), 24, risk_col, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	text(Vector2(right.position.x + 24, right.end.y - 70), Tx.t("ui.breakthrough.success") % int(float(q.success) * 100), 19, UiKit.PAPER)
	btn(Rect2(right.end.x - 250, right.end.y - 76, 226, 58), Tx.t("ui.breakthrough.break_through"), "go", null, true, bool(q.can), str(q.blocked))

func _core_checklist(ch, r: Rect2) -> void:
	var pts: Array = Game.progression.core_forging_points(ch)
	var met := 0
	for pt in pts:
		if pt.met: met += 1
	var flawless: bool = ch.quests.has_flag("cleansing_flawless")
	var best := ProgressionRules.core_grade(met, flawless)
	text(r.position + Vector2(0, 20), Tx.t("ui.breakthrough.core_forging") % best, 19, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x)
	var y := r.position.y + 30
	var step := minf(24.0, (r.end.y - y) / float(pts.size() + (1 if flawless else 0)))
	for pt in pts:
		var ok: bool = pt.met
		draw_circle(Vector2(r.position.x + 8, y + step * 0.5), 6, UiKit.JADE if ok else Color(UiKit.MIST, 0.35))
		text(Vector2(r.position.x + 22, y + step * 0.5 + 6), Tx.t("ui.breakthrough.core." + str(pt.id)), 16, UiKit.PAPER if ok else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)
		y += step
	if flawless: text(Vector2(r.position.x + 22, y + step * 0.5 + 6), Tx.t("ui.breakthrough.core.flawless"), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24)

func on_action(id: String, data) -> void:
	match id:
		"support":
			if supports.has(data): supports.erase(data)
			elif supports.size() < 3: supports.append(data)
		"fix": navigate.emit(str(data), {})
		"go":
			var r := submit({"type": "start_breakthrough", "support_items": supports})
			if r.get("ok", false): close()
