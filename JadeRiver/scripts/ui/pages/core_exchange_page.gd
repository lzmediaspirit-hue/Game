extends Page
## S46 · The Core Exchange at the Beast Hall: fixed Spirit Stones for beast cores by tier, up to 60 a day; and a place
## to rest your animals, which mends any Grievous Wound.

func _init() -> void:
	title = Tx.t("ui.cores.title")
	frame_rect = Rect2(170, 70, 940, 580)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var prices: Dictionary = ContentDB.config("pet_growth").get("cores", {}).get("price", {})
	var top := Rect2(content.position, Vector2(content.size.x, 70))
	panel(top)
	text(top.position + Vector2(18, 30), Tx.t("ui.cores.today") % Game.pets.exchange_left(ch), 19, UiKit.PALE_GOLD)
	para(Rect2(top.position + Vector2(18, 40), Vector2(top.size.x - 300, 30)), Tx.t("ui.cores.prices") % [int(prices.get("low", 1)), int(prices.get("mid", 3)),
		int(prices.get("high", 8)), int(prices.get("peak", 20))], 15, UiKit.MIST, 1)
	var wounded: bool = ch.pets.any(func(p): return Game.pets.ensure_fields(p).get("wounded", false))
	btn(Rect2(top.end.x - 260, top.position.y + 12, 244, 46), Tx.t("ui.cores.rest"), "rest", null, wounded, wounded, Tx.t("ui.cores.none_wounded"), 18)
	var cores: Array = []
	for st in ch.inventory.bag:
		if st == null or not ContentDB.item(str(st.id)).get("core", {}).has("tier") or cores.has(str(st.id)): continue
		cores.append(str(st.id))
	var r := Rect2(content.position.x, top.end.y + 12, content.size.x, content.end.y - top.end.y - 12)
	panel(r)
	if cores.is_empty():
		para(Rect2(r.position + Vector2(18, 24), Vector2(r.size.x - 36, 80)), Tx.t("ui.cores.none"), 18, UiKit.MIST)
		return
	list("cores", r.grow(-10), cores.size(), 66, func(i: int, rr: Rect2):
		var id: String = cores[i]
		var cd: Dictionary = ContentDB.item(id).core
		slot_box(Rect2(rr.position.x + 6, rr.position.y + 5, 56, 56), id, ch.inventory.count(id))
		text(rr.position + Vector2(76, 28), ContentDB.item_name(id), 18, UiKit.PAPER)
		text(rr.position + Vector2(76, 52), Tx.t("ui.cores.each") % int(prices.get(str(cd.tier), 1)), 15, UiKit.MIST)
		btn(Rect2(rr.end.x - 300, rr.position.y + 10, 140, 44), Tx.t("ui.cores.sell_one"), "sell", [id, 1], false, true, "", 17)
		btn(Rect2(rr.end.x - 150, rr.position.y + 10, 140, 44), Tx.t("ui.cores.sell_all"), "sell", [id, ch.inventory.count(id)], true, true, "", 17)
	)

func on_action(id: String, data) -> void:
	match id:
		"sell":
			var r := submit({"type": "sell_cores", "item": str(data[0]), "count": int(data[1])})
			if r.get("ok", false): flash(Tx.t("ui.cores.sold") % [int(r.count), int(r.stones)])
		"rest":
			if submit({"type": "rest_pets"}).get("ok", false): flash(Tx.t("ui.cores.rested"))
	queue_redraw()
