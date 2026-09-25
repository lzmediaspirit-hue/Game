extends Page
## Welcome back (S07/S23): what seclusion or the idle task earned while away.

func _init() -> void:
	title = Tx.t("ui.welcome.welcome_back")
	modal = true
	frame_rect = Rect2(300, 130, 680, 460)

func draw_page() -> void:
	var w: Dictionary = args.get("gains", {})
	var y := content.position.y + 10
	var minutes := float(args.get("hours", 0.0)) * 60.0
	text(Vector2(content.position.x, y + 24), Tx.t("ui.welcome.you_were_away") % _dur(minutes * 60.0), 22, UiKit.MIST)
	y += 50
	var rows: Array = []
	if float(w.get("qp", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.realm_progress"), "+%s" % UiKit.fmt(float(w.qp))])
	if float(w.get("stored_qi", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.stored_qi"), "+%s" % UiKit.fmt(float(w.stored_qi))])
	if float(w.get("body_xp", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.body_training"), "+%s" % UiKit.fmt(float(w.body_xp))])
	if float(w.get("insight", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.insight"), "+%s" % UiKit.fmt(float(w.insight))])
	if int(w.get("coins", 0)) > 0: rows.append([Tx.t("ui.welcome.silver_taels"), "+%s" % UiKit.fmt(int(w.coins))])
	for it in w.get("items", []):
		rows.append([ContentDB.item_name(str(it.get("item", it.get("id", "")))), "×%d" % int(it.get("count", 1))])
	if bool(args.get("capped", false)): rows.append([Tx.t("ui.welcome.time_limit_reached"), Tx.t("ui.welcome.extend_it_with_retreat_rooms")])
	if rows.is_empty(): rows.append([Tx.t("ui.welcome.nothing_gathered"), Tx.t("ui.welcome.set_seclusion_or_an_idle")])
	for r in rows:
		text(Vector2(content.position.x + 20, y + 24), str(r[0]), 21, UiKit.PAPER)
		text(Vector2(content.position.x, y + 24), str(r[1]), 21, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, content.size.x - 20)
		y += 36
	btn(Rect2(content.get_center().x - 120, content.end.y - 60, 240, 58), Tx.t("ui.welcome.collect"), "ok", null, true)

func _dur(s: float) -> String:
	var h := int(s / 3600.0)
	var m := int(fmod(s, 3600.0) / 60.0)
	return Tx.t("ui.welcome.dh_02dm") % [h, m] if h > 0 else Tx.t("ui.welcome.minutes") % m

func on_action(id: String, _data) -> void:
	if id == "ok": close()
