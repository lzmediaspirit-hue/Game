extends Page
## Training sect (S20): rank, contribution, promotion trials, missions and the sect shop.

func _init() -> void:
	title = Tx.t("ui.training_sect.sect")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var ts: Dictionary = ch.training_sect
	var r := Rect2(content.position, content.size)
	panel(r)
	if str(ts.get("id", "")) == "":
		para(Rect2(r.position + Vector2(30, 30), r.size - Vector2(60, 60)), Tx.t("ui.training_sect.you_are_unaffiliated_the_jade"), 22, UiKit.PAPER)
		return
	var sect := ContentDB.entry("sects", str(ts.id))
	text(r.position + Vector2(30, 50), str(sect.get("full_name", sect.get("name", ""))), 32, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	var ranks: Dictionary = ContentDB.config("sect_ranks")
	var rank_name := str(ts.get("rank", "")).replace("_", " ").capitalize()
	text(r.position + Vector2(30, 90), Tx.t("ui.training_sect.rank") % rank_name, 22)
	currency_pill(r.position + Vector2(30, 110), "contribution", int(ts.get("contribution", 0)))
	var order: Array = ranks.get("order", [])
	var i := order.find(str(ts.get("rank", "")))
	var y := r.position.y + 180
	for j in order.size():
		var rk: Dictionary = ranks.ranks[j]
		var done := j <= i
		text(Vector2(r.position.x + 30, y), ("◆ " if done else "◇ ") + str(rk.name), 20, UiKit.GOLD if done else UiKit.MIST)
		if j == i + 1:
			var ok := RequirementRules.passes(rk.get("requires", {}), Game.ctx(ch))
			text(Vector2(r.position.x + 300, y), RequirementRules.first_failure_text(rk.get("requires", {}), Game.ctx(ch)) if not ok else Tx.t("ui.training_sect.ready"), 17, UiKit.PAPER if ok else UiKit.MIST)
			btn(Rect2(r.position.x + 640, y - 30, 220, 46), Tx.t("ui.training_sect.promotion_trial"), "promote", null, true, ok, Tx.t("ui.training_sect.not_yet"))
		y += 40
	btn(Rect2(r.end.x - 260, r.end.y - 76, 230, 56), Tx.t("ui.training_sect.sect_shop"), "shop", null, false, Unlocks.is_unlocked(ch.id, "contribution_shop"), Unlocks.locked_text("contribution_shop"))
	btn(Rect2(r.end.x - 520, r.end.y - 76, 230, 56), Tx.t("ui.training_sect.missions"), "missions")

func on_action(id: String, _data) -> void:
	match id:
		"promote": submit({"type": "take_promotion_trial"})
		"shop": navigate.emit("shop", {"shop": str(c().training_sect.get("id", "jade_sect"))})
		"missions": navigate.emit("notice_board", {})
