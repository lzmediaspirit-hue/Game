extends Page
## S50 Keeping Post (V10): Tailor Xun sews a character's Qiankun pouch one tier deeper, one category at a time.
## A pouch has four compartments per category; a post stops filling a category when it is full.

const CATS := ["ore", "herb", "fish", "insect", "material", "critter", "wisp"]
const CAT_ICON := {"ore": "copper_ore", "herb": "willow_moss", "fish": "river_minnow", "insect": "glowfly", "material": "hemp_cord",
	"critter": "jade_frog", "wisp": "spirit_wisp"}

func _init() -> void:
	title = Tx.t("ui.pouches.title")
	modal = true
	frame_rect = Rect2(140, 40, 1000, 640)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x - 230, 50)), Tx.t("ui.pouches.note") % str(ch.name), 16, UiKit.MIST, 3)
	currency_pill(Vector2(content.end.x - 210, y + 6), "silver_tael", Game.economy.balance("silver_tael", ch))
	y += 72
	var rows: Array = ContentDB.config("posts").get("sewing", [])
	var colw := (content.size.x - 12.0) / 2.0
	for i in CATS.size():
		var cat: String = CATS[i]
		var r := Rect2(x + (i % 2) * (colw + 12.0), y + (i / 2) * 104.0, colw, 96)
		panel(r)
		icon_at(Rect2(r.position + Vector2(10, 10), Vector2(36, 36)), str(CAT_ICON[cat]))
		var p: Dictionary = Game.posts.pouch(ch, cat)
		var tier := int(p.get("tier", 0))
		var tier_name := Tx.t("ui.pouches.unsewn") if tier == 0 else str(rows[tier - 1].name)
		text(r.position + Vector2(56, 28), "%s · %s" % [Tx.t("ui.pouches.cat_" + cat), tier_name], 17, UiKit.PAPER)
		text(r.position + Vector2(56, 52), Tx.t("ui.pouches.holds") % [UiKit.fmt(int(Game.posts.capacity(ch, cat))), UiKit.fmt(int(Game.posts.held(ch, cat)))], 14, UiKit.MIST)
		if tier >= rows.size():
			text(r.position + Vector2(56, 80), Tx.t("ui.pouches.finest"), 15, UiKit.PALE_GOLD)
		else:
			var nx: Dictionary = rows[tier]
			var parts: Array = []
			for need in nx.items: parts.append("%d %s" % [int(need.count), ContentDB.item_name(str(need.item))])
			var cost := Tx.t("ui.pouches.cost_list") % [UiKit.fmt(int(nx.taels)), ", ".join(parts)]
			text(r.position + Vector2(56, 80), fit(Tx.t("ui.pouches.next") % [str(nx.name), UiKit.fmt(int(nx.cap) * 4)] + " · " + cost, 13, colw - 190), 13, UiKit.BRIGHT_JADE)
			btn(Rect2(r.end.x - 118, r.position.y + 24, 106, 48), Tx.t("ui.pouches.sew"), "sew", cat, true, true, "", 18)

func on_action(id: String, data) -> void:
	if id == "sew":
		var r := submit({"type": "sew_pouch", "category": str(data)})
		if r.get("ok", false): flash(Tx.t("ui.pouches.sewn") % UiKit.fmt(int(r.cap)))
