extends Page
## The Auction Pavilion (S21): today's lots, what each stands at, who holds it and when it closes.
## A bid below a bidder's hidden limit is answered at once; above it, you hold the lot and the
## item comes by mail when the hammer falls. The house premium depends on the path you chose.

func _init() -> void:
	title = Tx.t("ui.auction.title")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position, content.size)
	panel(r)
	currency_pill(r.position + Vector2(24, 14), "spirit_stone", Game.economy.balance("spirit_stone", ch))
	text(r.position + Vector2(260, 44), Tx.t("ui.auction.premium") % int(round(Game.economy.auction_fee(ch) * 100.0)), 18, UiKit.MIST)
	var lots: Array = Game.economy.auction_lots().filter(func(l): return not l.get("closed", false))
	if lots.is_empty():
		para(Rect2(r.position + Vector2(40, 90), r.size - Vector2(80, 120)), Tx.t("ui.auction.no_lots"), 20, UiKit.HOLLOW)
		return
	var bidders: Array = ContentDB.config("auction").get("bidders", [])
	list("lots", Rect2(r.position.x + 16, r.position.y + 64, r.size.x - 32, r.size.y - 80), lots.size(), 96, func(i: int, rr: Rect2):
		var l: Dictionary = lots[i]
		var mine: bool = str(l.bidder) == ch.id
		panel(rr, "minor_panel", "selected" if mine else "normal")
		slot_box(Rect2(rr.position + Vector2(12, 12), Vector2(72, 72)), str(l.item), int(l.count))
		text(rr.position + Vector2(100, 34), fit(ContentDB.item_name(str(l.item)) + ("  ×%d" % int(l.count) if int(l.count) > 1 else ""), 21, rr.size.x * 0.4), 21)
		var left_s := maxf(0.0, float(l.ends) - Clock.now_utc())
		text(rr.position + Vector2(100, 62), Tx.t("ui.auction.closes_in") % [int(left_s / 3600.0), int(fmod(left_s, 3600.0) / 60.0)], 16, UiKit.MIST)
		var who := Tx.t("ui.auction.you") if mine else (str(bidders[int(l.npc) % bidders.size()]) if str(l.bidder) == "npc" and not bidders.is_empty() else Tx.t("ui.auction.another"))
		var price: int = Game.economy.auction_price(l)
		text(Vector2(rr.position.x + rr.size.x * 0.45, rr.position.y + 34), Tx.t("ui.auction.stands_at") % UiKit.fmt(price), 20, UiKit.PALE_GOLD)
		text(Vector2(rr.position.x + rr.size.x * 0.45, rr.position.y + 62), fit(Tx.t("ui.auction.held_by") % who, 16, rr.size.x * 0.3), 16, UiKit.BRIGHT_JADE if mine else UiKit.MIST)
		if not mine:
			var need: int = Game.economy.auction_min_bid(l)
			var bw := 150.0
			btn(Rect2(rr.end.x - 2 * bw - 24, rr.position.y + 22, bw, 52), Tx.t("ui.auction.bid") % UiKit.fmt(need), "bid", [str(l.id), need], true, true, "", 18)
			var big := int(ceil(price * 1.5))
			btn(Rect2(rr.end.x - bw - 12, rr.position.y + 22, bw, 52), Tx.t("ui.auction.bid") % UiKit.fmt(big), "bid", [str(l.id), big], false, true, "", 18)
	)

func on_action(id: String, data) -> void:
	if id == "bid":
		var r := submit({"type": "auction_bid", "lot": str(data[0]), "amount": int(data[1])})
		if r.get("outbid", false): flash(Tx.t("ui.auction.outbid_at_once") % UiKit.fmt(int(r.get("bid", 0))))
		elif r.get("top", false): flash(Tx.t("ui.auction.you_lead"))
