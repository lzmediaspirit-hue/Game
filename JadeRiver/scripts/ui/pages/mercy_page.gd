extends Page
## Mercy (S49, Part 8): a named foe has thrown down their weapon. Spare them (merit; some remember it) or finish them
## (sin; some have kin who will come looking).

func _init() -> void:
	modal = true
	title = Tx.t("ui.mercy.title")
	frame_rect = Rect2(300, 150, 680, 400)

func draw_page() -> void:
	var def := str(args.get("def", args.get("tab", "")))   # --open-page=mercy:def passes it as the tab
	var x := content.position.x + 20
	var y := content.position.y + 10
	text(Vector2(x, y + 30), ContentDB.name_of("enemies", def), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	para(Rect2(x, y + 48, content.size.x - 40, 90), Tx.t("ui.mercy.line"), 19, UiKit.PAPER, 3)
	var spare := ContentDB.entry("karma", "spared_foe")
	var kill := ContentDB.entry("karma", "killed_yielded")
	var bw := (content.size.x - 40 - 16) / 2.0
	var by := content.end.y - 120
	text(Vector2(x, by - 10), Tx.t("ui.mercy.spare_cost") % int(spare.get("merit", 0)), 16, Color("e8c872"))
	text(Vector2(x + bw + 16, by - 10), Tx.t("ui.mercy.kill_cost") % int(kill.get("sin", 0)), 16, Color("e07a7a"))
	btn(Rect2(x, by, bw, 58), Tx.t("ui.mercy.spare"), "judge", true, true)
	btn(Rect2(x + bw + 16, by, bw, 58), Tx.t("ui.mercy.kill"), "judge", false)
	para(Rect2(x, content.end.y - 50, content.size.x - 40, 44), Tx.t("ui.mercy.note"), 15, UiKit.MIST, 2)

func on_action(id: String, data) -> void:
	if id == "judge":
		if submit({"type": "judge_foe", "enemy": int(args.get("enemy", 0)), "spare": bool(data)}).get("ok", false): close()
	queue_redraw()
