extends Page
## Currency exchange (S21/S39): each zone's clerk trades its everyday currency with the tier below at a 20%
## spread (rates in currencies.json "exchange"). The pairs come from currencies.json "zone_pairs".

func _init() -> void:
	title = Tx.t("ui.exchange.exchange")
	modal = true
	frame_rect = Rect2(320, 150, 640, 420)

func _pairs() -> Array:
	var zone := str(ContentDB.zone_of_room(Game.room_rt.room_id if Game.room_rt else "").get("id", "jade_river_valley"))
	var all: Dictionary = ContentDB.config("currencies").get("zone_pairs", {})
	return all.get(zone, [["silver_tael", "spirit_stone"]])

func draw_page() -> void:
	var ch = c()
	var x := content.position.x
	var y := content.position.y + 10
	var pairs := _pairs()
	for pair in pairs:
		var lo := str(pair[0])
		var hi := str(pair[1])
		currency_pill(Vector2(x, y), lo, Game.economy.balance(lo, ch))
		currency_pill(Vector2(x + 300, y), hi, Game.economy.balance(hi, ch))
		y += 50
		var rate := float(ContentDB.config("currencies").get("exchange", {}).get(lo + ">" + hi, 0.01))
		var amounts := [500, 2500] if pairs.size() == 1 else [500]
		for amt in amounts:
			var back := maxi(1, int(round(amt * rate)))
			btn(Rect2(x, y, 280, 50), Tx.t("ui.exchange.pay_for") % [UiKit.fmt(amt), currency_name(lo), currency_name(hi)], "ex", [lo, hi, amt])
			btn(Rect2(x + 300, y, 280, 50), Tx.t("ui.exchange.pay_for") % [UiKit.fmt(back), currency_name(hi), currency_name(lo)], "ex", [hi, lo, back])
			y += 60
		y += 10
	para(Rect2(Vector2(x, y), Vector2(content.size.x, 60)), Tx.t("ui.exchange.rate_note"), 18, UiKit.MIST)

func on_action(id: String, data) -> void:
	if id == "ex":
		var r := submit({"type": "exchange_currency", "from": str(data[0]), "to": str(data[1]), "amount": int(data[2])})
		if r.get("ok", false): flash(Tx.t("ui.exchange.received") % int(r.received))
