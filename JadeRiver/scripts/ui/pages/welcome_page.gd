extends Page
## Welcome back (S07/S23): what seclusion or the idle task earned while away.

func _init() -> void:
	title = Tx.t("ui.welcome.welcome_back")
	modal = true
	frame_rect = Rect2(260, 90, 760, 560)

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
	if float(w.get("halo", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.pill_halo"), "+%d%%" % int(round(float(w.halo) * 100.0))])
	if int(w.get("coins", 0)) > 0:
		var cur_key := "ui.welcome.spirit_stones" if str(w.get("coin_currency", "")) == "spirit_stone" else "ui.welcome.silver_taels"
		rows.append([Tx.t(cur_key), "+%s" % UiKit.fmt(int(w.coins))])
	for it in w.get("items", []):
		rows.append([ContentDB.item_name(str(it.get("item", it.get("id", "")))), "×%d" % int(it.get("count", 1))])
	if bool(args.get("capped", false)): rows.append([Tx.t("ui.welcome.time_limit_reached"), Tx.t("ui.welcome.extend_it_with_retreat_rooms")])
	# S50 Keeping Post: the Return Ledger of the post this character kept.
	var led: Dictionary = args.get("post", {})
	if not led.is_empty():
		var craft := ContentDB.entry("posts", str(led.get("craft", "")))
		rows.append([Tx.t("ui.welcome.post_at") % [str(craft.get("short", "")), str(ContentDB.room(str(led.get("room", ""))).get("name", ""))],
			Tx.t("ui.welcome.post_hours") % [_dur(float(led.get("hours", 0.0)) * 3600.0), int(round(float(led.get("diligence", 0.52)) * 100.0))]])
		var lv_txt := "+%s" % UiKit.fmt(int(float(led.get("exp", 0.0))))
		if int(led.get("level", 1)) > int(led.get("level_before", 1)): lv_txt += "  " + Tx.t("ui.welcome.level_up") % int(led.level)
		rows.append([Tx.t("ui.welcome.craft_exp") % str(craft.get("short", "")), lv_txt])
		for id in led.get("items", {}):
			rows.append([ContentDB.item_name(str(id)), "×%s" % UiKit.fmt(int(led.items[id]))])
		for cat in led.get("full", {}):
			rows.append([Tx.t("ui.welcome.pouch_full") % Tx.t("ui.pouches.cat_" + str(cat)), Tx.t("ui.welcome.full_after") % _dur(float(led.full[cat]) * 3600.0)])
	if rows.is_empty(): rows.append([Tx.t("ui.welcome.nothing_gathered"), Tx.t("ui.welcome.set_seclusion_or_an_idle")])
	for r in rows:
		text(Vector2(content.position.x + 20, y + 24), str(r[0]), 21, UiKit.PAPER)
		text(Vector2(content.position.x, y + 24), str(r[1]), 21, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, content.size.x - 20)
		y += 36
	if not args.get("post", {}).is_empty() and not (args.post.get("items", {}) as Dictionary).is_empty():
		btn(Rect2(content.get_center().x - 260, content.end.y - 60, 250, 58), Tx.t("ui.welcome.to_storehouse"), "store", null, true)
		btn(Rect2(content.get_center().x + 10, content.end.y - 60, 250, 58), Tx.t("ui.welcome.keep_in_pouch"), "ok")
	else:
		btn(Rect2(content.get_center().x - 120, content.end.y - 60, 240, 58), Tx.t("ui.welcome.collect"), "ok", null, true)

func _dur(s: float) -> String:
	var h := int(s / 3600.0)
	var m := int(fmod(s, 3600.0) / 60.0)
	return Tx.t("ui.welcome.dh_02dm") % [h, m] if h > 0 else Tx.t("ui.welcome.minutes") % m

func on_action(id: String, _data) -> void:
	if id == "store":
		submit({"type": "send_to_storehouse", "character": Game.active_id})
		close()
	if id == "ok": close()
