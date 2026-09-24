extends Page
## Shops (S21, S39, Part 9.11): browse and buy, sell from the bag, buy back. Prices
## come from the Economy authority; a stale price is refused and re-shown.

var shop_id := ""
var sel_buy := -1
var sel_sell := -1
var qty := 1

func _init() -> void:
	title = "Shop"
	tabs = [{"id": "buy", "label": "Buy"}, {"id": "sell", "label": "Sell"}, {"id": "buyback", "label": "Buy back"}]

func setup() -> void:
	shop_id = str(args.get("shop", "old_ma"))
	if page_id == "library": shop_id = "jade_sect" if str(c().training_sect.get("id", "")) == "jade_sect" else "cloud_sect"
	title = str(ContentDB.entry("shops", shop_id).get("name", "Shop"))

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var shop := ContentDB.entry("shops", shop_id)
	var currency := str(shop.get("currency", "silver_tael"))
	var x := content.end.x
	for cur in ([currency] if currency != "silver_tael" else []) + ["silver_tael"]:
		var w := UiKit.text_width(UiKit.fmt(Game.economy.balance(cur, ch)), 18) + 52
		x -= w + 8
		currency_pill(Vector2(x, frame_rect.position.y + 88), cur, Game.economy.balance(cur, ch))
	match str(tabs[tab].id):
		"buy": _buy(ch)
		"sell": _sell(ch)
		"buyback": _buyback(ch)

func _buy(ch) -> void:
	var stock: Array = Game.economy.stock(ch, shop_id)
	var left := Rect2(content.position.x, content.position.y, 700, content.size.y)
	panel(left)
	list("stock", left.grow(-10), stock.size(), 76, func(i: int, rr: Rect2):
		var s: Dictionary = stock[i]
		panel(rr, "minor_panel", "selected" if sel_buy == i else ("disabled" if str(s.locked) != "" else "normal"))
		slot_box(Rect2(rr.position + Vector2(8, 5), Vector2(62, 62)), str(s.item))
		text(rr.position + Vector2(84, 30), ContentDB.item_name(str(s.item)) + ("  ↻" if s.get("rotating", false) else ""), 20, UiKit.PAPER if str(s.locked) == "" else UiKit.HOLLOW)
		text(rr.position + Vector2(84, 56), str(s.locked) if str(s.locked) != "" else str(ContentDB.item(str(s.item)).get("desc", "")).left(60), 15, UiKit.MIST)
		text(rr.position + Vector2(0, 42), "%s %s" % [UiKit.fmt(int(s.price)), {"silver_tael": "taels", "spirit_stone": "stones", "contribution": "contrib."}.get(str(s.currency), "")], 19, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 16)
		region(rr, "pick", i, str(s.locked) == "", str(s.locked))
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	if sel_buy < 0 or sel_buy >= stock.size():
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), "Tap an item to buy. Shops refresh one rotating item each dawn.", 19, UiKit.MIST)
		return
	var it: Dictionary = stock[sel_buy]
	var def := ContentDB.item(str(it.item))
	slot_box(Rect2(right.position + Vector2(24, 24), Vector2(72, 72)), str(it.item))
	para(Rect2(right.position + Vector2(110, 24), Vector2(right.size.x - 130, 60)), ContentDB.item_name(str(it.item)), 22, UiKit.grade_color(str(def.get("grade", "plain"))), 2)
	para(Rect2(right.position + Vector2(24, 110), Vector2(right.size.x - 48, 150)), str(def.get("desc", "")), 18)
	var stackable := int(def.get("stack", 1)) > 1
	if stackable:
		btn(Rect2(right.position.x + 24, right.end.y - 150, 60, 52), "−", "qty", -1)
		text(Vector2(right.position.x + 90, right.end.y - 114), str(qty), 24, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 80)
		btn(Rect2(right.position.x + 176, right.end.y - 150, 60, 52), "+", "qty", 1)
		btn(Rect2(right.position.x + 244, right.end.y - 150, 80, 52), "×10", "qty", 10)
	var total := int(it.price) * (qty if stackable else 1)
	text(Vector2(right.position.x + 24, right.end.y - 82), "Total: %s" % UiKit.fmt(total), 20, UiKit.PALE_GOLD)
	var afford := Game.economy.balance(str(it.currency), ch) >= total
	btn(Rect2(right.end.x - 224, right.end.y - 72, 200, 56), "Buy", "buy", null, true, afford, "Not enough %s" % ContentDB.text("currency." + str(it.currency)))

func _sell(ch) -> void:
	var bag: Array = ch.inventory.bag
	var idx: Array = []
	for i in bag.size():
		if bag[i] != null: idx.append(i)
	var left := Rect2(content.position.x, content.position.y, 700, content.size.y)
	panel(left)
	list("sell", left.grow(-10), idx.size(), 70, func(j: int, rr: Rect2):
		var i := int(idx[j])
		var s: Dictionary = bag[i]
		var price := LootRules.sell_price(str(s.id), s if ContentDB.is_equipment(str(s.id)) else null)
		panel(rr, "minor_panel", "selected" if sel_sell == i else ("disabled" if price <= 0 else "normal"))
		slot_box(Rect2(rr.position + Vector2(8, 3), Vector2(60, 60)), str(s.id), int(s.get("count", 1)), str(s.get("quality", "")))
		text(rr.position + Vector2(84, 40), ContentDB.item_name(str(s.id)), 19, UiKit.PAPER if price > 0 else UiKit.HOLLOW)
		text(rr.position + Vector2(0, 40), ("%s each" % UiKit.fmt(price)) if price > 0 else "Cannot sell", 17, UiKit.PALE_GOLD if price > 0 else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 16)
		region(rr, "pick_sell", i, price > 0, "This cannot be sold")
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	if sel_sell < 0 or sel_sell >= bag.size() or bag[sel_sell] == null:
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), "Sell for a quarter of an item's value. Anything sold can be bought back today.", 19, UiKit.MIST)
		return
	var s2: Dictionary = bag[sel_sell]
	slot_box(Rect2(right.position + Vector2(24, 24), Vector2(72, 72)), str(s2.id), int(s2.get("count", 1)))
	text(right.position + Vector2(110, 60), ContentDB.item_name(str(s2.id)), 21)
	btn(Rect2(right.position.x + 24, right.end.y - 140, right.size.x - 48, 54), "Sell one", "sell", 1)
	if int(s2.get("count", 1)) > 1: btn(Rect2(right.position.x + 24, right.end.y - 76, right.size.x - 48, 54), "Sell all (%d)" % int(s2.count), "sell", int(s2.count), true)

func _buyback(ch) -> void:
	var bb: Array = Game.account.economy.get("buyback", [])
	var r := Rect2(content.position, content.size)
	panel(r)
	if bb.is_empty(): text(r.position + Vector2(0, 80), "Nothing sold today.", 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	list("bb", r.grow(-10), bb.size(), 70, func(i: int, rr: Rect2):
		var e: Dictionary = bb[i]
		var ent: Dictionary = e.get("entry", {})
		panel(rr)
		slot_box(Rect2(rr.position + Vector2(8, 3), Vector2(60, 60)), str(ent.get("id", "")), int(ent.get("count", 1)))
		text(rr.position + Vector2(84, 40), ContentDB.item_name(str(ent.get("id", ""))), 19)
		btn(Rect2(rr.end.x - 230, rr.position.y + 8, 210, 48), "Buy back · %s" % UiKit.fmt(int(e.price)), "buyback", i)
	)

func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"pick":
			sel_buy = int(data)
			qty = 1
		"pick_sell": sel_sell = int(data)
		"qty": qty = clampi(qty + int(data), 1, 99)
		"buy":
			var stock: Array = Game.economy.stock(ch, shop_id)
			var it: Dictionary = stock[sel_buy]
			var n := qty if int(ContentDB.item(str(it.item)).get("stack", 1)) > 1 else 1
			var r := submit({"type": "buy", "shop": shop_id, "item": str(it.item), "count": n, "price": int(it.price)})
			if r.get("ok", false):
				Audio.play("coin", "UI")
				flash("Bought %s ×%d" % [ContentDB.item_name(str(it.item)), n])
		"sell":
			if submit({"type": "sell", "index": sel_sell, "count": int(data)}).get("ok", false):
				Audio.play("coin", "UI")
				if ch.inventory.bag[sel_sell] == null: sel_sell = -1
		"buyback": submit({"type": "buyback", "index": int(data)})
		"_tab":
			sel_buy = -1
			sel_sell = -1
