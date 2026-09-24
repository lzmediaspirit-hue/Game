extends Page
## Currency exchange (S21/S39): taels ↔ Spirit Stones at a 20% spread.

func _init() -> void:
	title = "Exchange"
	modal = true
	frame_rect = Rect2(320, 150, 640, 420)

func draw_page() -> void:
	var ch = c()
	var x := content.position.x
	currency_pill(Vector2(x, content.position.y + 10), "silver_tael", Game.economy.balance("silver_tael", ch))
	currency_pill(Vector2(x + 260, content.position.y + 10), "spirit_stone", Game.economy.balance("spirit_stone", ch))
	para(Rect2(content.position + Vector2(0, 70), Vector2(content.size.x, 60)), "100 taels buy 1 Spirit Stone, less a 20% fee. Stones sell for 100 taels less the fee.", 18, UiKit.MIST)
	var y := content.position.y + 150
	for amt in [500, 2500]:
		btn(Rect2(x, y, 280, 54), "%s taels → stones" % UiKit.fmt(amt), "ex", ["silver_tael", "spirit_stone", amt])
		btn(Rect2(x + 300, y, 280, 54), "%d stones → taels" % (amt / 100), "ex", ["spirit_stone", "silver_tael", amt / 100])
		y += 66

func on_action(id: String, data) -> void:
	if id == "ex":
		var r := submit({"type": "exchange_currency", "from": str(data[0]), "to": str(data[1]), "amount": int(data[2])})
		if r.get("ok", false): flash("Received %d" % int(r.received))
