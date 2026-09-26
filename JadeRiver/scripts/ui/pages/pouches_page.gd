extends Page
## S50 Keeping Post (V10): Tailor Xun sews a character's Qiankun pouch one tier deeper, one category at a time.
## A pouch has four compartments per category; a post stops filling a category when it is full.

const CATS := ["ore", "herb", "fish", "insect"]
const CAT_ICON := {"ore": "copper_ore", "herb": "willow_moss", "fish": "river_minnow", "insect": "glowfly"}

func _init() -> void:
	title = Tx.t("ui.pouches.title")
	modal = true
	frame_rect = Rect2(200, 70, 880, 580)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x - 230, 50)), Tx.t("ui.pouches.note") % str(ch.name), 16, UiKit.MIST, 3)
	currency_pill(Vector2(content.end.x - 210, y + 6), "silver_tael", Game.economy.balance("silver_tael", ch))
	y += 72
	var rows: Array = ContentDB.config("posts").get("sewing", [])
	for cat in CATS:
		var r := Rect2(x, y, content.size.x, 90)
		panel(r)
		icon_at(Rect2(r.position + Vector2(14, 24), Vector2(44, 44)), str(CAT_ICON[cat]))
		var p: Dictionary = Game.posts.pouch(ch, cat)
		var tier := int(p.get("tier", 0))
		var tier_name := Tx.t("ui.pouches.unsewn") if tier == 0 else str(rows[tier - 1].name)
		text(r.position + Vector2(72, 36), "%s · %s" % [Tx.t("ui.pouches.cat_" + cat), tier_name], 20, UiKit.PAPER)
		text(r.position + Vector2(72, 66), Tx.t("ui.pouches.holds") % [UiKit.fmt(int(Game.posts.capacity(ch, cat))), UiKit.fmt(int(Game.posts.held(ch, cat)))], 16, UiKit.MIST)
		if tier >= rows.size():
			text(r.position + Vector2(r.size.x - 20, 52), Tx.t("ui.pouches.finest"), 17, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 260)
		else:
			var nx: Dictionary = rows[tier]
			var need: Dictionary = nx.items[0] if not (nx.items as Array).is_empty() else {}
			var cost := Tx.t("ui.pouches.cost") % [UiKit.fmt(int(nx.taels)), int(need.get("count", 0)), ContentDB.item_name(str(need.get("item", "")))]
			text(r.position + Vector2(380, 36), Tx.t("ui.pouches.next") % [str(nx.name), UiKit.fmt(int(nx.cap) * 4)], 16, UiKit.BRIGHT_JADE)
			text(r.position + Vector2(380, 66), fit(cost, 15, 260), 15, UiKit.MIST)
			btn(Rect2(r.end.x - 160, r.position.y + 22, 144, 52), Tx.t("ui.pouches.sew"), "sew", cat, true)
		y += 96

func on_action(id: String, data) -> void:
	if id == "sew":
		var r := submit({"type": "sew_pouch", "category": str(data)})
		if r.get("ok", false): flash(Tx.t("ui.pouches.sewn") % UiKit.fmt(int(r.cap)))
