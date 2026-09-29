extends Page
## Currency exchange (S21/S39): each zone's clerk trades its everyday currency with the tier below at a 20% spread (rates
## in currencies.json "exchange"; the pairs from "zone_pairs"). P5 as the money-changer's barred window (docs/page_identity.md
## row 33; decision 14): a black lacquer counter wall with the rate board above, the brass bars of the window in the middle
## with the changer's coin trays behind them and a coin slot at its foot; your purses on the near side of the counter and
## the trades under the slot. Coins slide through the slot on a trade. The page submits intents only.

const WINDOW := Rect2(352, 222, 576, 140)     # the barred window, the changer's trays behind it
const SLOT_Y := 372.0

var coins := {}            # the coins on their way through the slot (MarketKit.fly)

func _init() -> void:
	title = Tx.t("ui.exchange.exchange")
	modal = true
	frame_rect = WINDOW_MEDIUM
	identity = Identity.new("lacquer_black", false, "own", "barred_window_coin_slot", 0.25)

func _pairs() -> Array:
	var zone := str(ContentDB.zone_of_room(Game.room_rt.room_id if Game.room_rt else "").get("id", "jade_river_valley"))
	var all: Dictionary = ContentDB.config("currencies").get("zone_pairs", {})
	return all.get(zone, [["silver_tael", "spirit_stone"]])

func _rate(lo: String, hi: String) -> float:
	return float(ContentDB.config("currencies").get("exchange", {}).get(lo + ">" + hi, 0.01))

func content_rect() -> Rect2:
	return Rect2(frame_rect.position + Vector2(INSET, 336), Vector2(frame_rect.size.x - INSET * 2.0, frame_rect.size.y - 336 - BOTTOM))

# ------------------------------------------------------------------ the wall, the window and the counter
func draw_surface(r: Rect2) -> void:
	rounded(r.grow(3), 8.0, UiKit.INK)
	vshade(r, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.06), UiKit.SURFACE.lacquer_black)
	draw_rect(r.grow(-6), Color(UiKit.GOLD, 0.4), false, 1.0)
	MarketKit.brass(self, r.grow(-2), 30.0)
	ground(r, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.06))
	# The window: a timber frame round the changer's dim booth, the coin trays on its sill.
	var w := WINDOW
	rounded(w.grow(14), 6.0, UiKit.SURFACE.wood_dark)
	draw_rect(w.grow(14), Color(UiKit.SURFACE.wood, 0.9), false, 3.0)
	vshade(w, UiKit.INK, UiKit.SURFACE.space)
	glow(Rect2(w.position + Vector2(w.size.x * 0.25, 10), Vector2(w.size.x * 0.5, w.size.y)), Color(UiKit.PALE_GOLD, 0.12))
	var pairs := _pairs()
	var curs: Array = []
	for p in pairs:
		for cur in p:
			if not cur in curs: curs.append(cur)
	var tw := (w.size.x - 40) / curs.size()
	for i in curs.size():
		var tray := Rect2(w.position.x + 20 + i * tw + 8, w.end.y - 44, tw - 16, 30)
		rounded(tray, 4.0, UiKit.BRONZE)
		draw_rect(tray.grow(-3), UiKit.SURFACE.wood_dark)
		for k in 5:
			var at := Vector2(roundf(tray.position.x + 8 + k * (tray.size.x - 48) / 4.0), tray.position.y - 20 + (k % 2) * 6)
			icon_at(Rect2(at, Vector2(32, 32)), Page.currency_icon(str(curs[i])))
	# The brass bars, each lit on its left.
	var x := w.position.x + 24.0
	while x < w.end.x - 10.0:
		draw_rect(Rect2(x - 4, w.position.y, 8, w.size.y), UiKit.BRONZE)
		draw_rect(Rect2(x - 3, w.position.y, 2, w.size.y), UiKit.PALE_GOLD.lerp(UiKit.GOLD, 0.5))
		x += 44.0
	draw_rect(Rect2(w.position.x, w.position.y + 40, w.size.x, 6), UiKit.BRONZE)
	draw_rect(Rect2(w.position.x, w.position.y + 40, w.size.x, 2), UiKit.GOLD)
	# The counter's lip and the coin slot at the window's foot.
	vshade(Rect2(r.position.x + 6, SLOT_Y + 4, r.size.x - 12, 16), UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark)
	var slot := Rect2(w.get_center().x - 90, SLOT_Y + 2, 180, 12)
	rounded(slot.grow(4), 6.0, UiKit.GOLD)
	rounded(slot, 5.0, UiKit.INK)

## The rate board over the window: the title on a timber board with brass corners.
func title_rect() -> Rect2:
	return Rect2(frame_rect.position.x + frame_rect.size.x * 0.5 - 200, frame_rect.position.y + 14, 400, 56)

func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(2), 5.0, UiKit.INK)
	MarketKit.planks(self, r, UiKit.SURFACE.wood, 14.0, false)
	MarketKit.brass(self, r, 16.0)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	var pairs := _pairs()
	var fx := frame_rect.position.x
	var mid := frame_rect.get_center().x
	# The rates, chalked on the board's lower rail: one line a pair.
	var y := frame_rect.position.y + 96
	tour_mark("rates", Rect2(fx + INSET, y - 22, frame_rect.size.x - INSET * 2.0, 26 * pairs.size() + 8))   # decision 43
	for pair in pairs:
		var lo := str(pair[0])
		var hi := str(pair[1])
		var back := _rate(hi, lo)
		text(Vector2(fx, y), Tx.t("ui.exchange.rate_line") % [currency_name(hi), UiKit.fmt(int(back)), currency_name(lo)], 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, frame_rect.size.x)
		y += 26
	# Your purses on the near side of the counter.
	var curs: Array = []
	for p in pairs:
		for cur in p:
			if not cur in curs: curs.append(cur)
	var widths: Array = curs.map(func(cur): return UiKit.text_width(UiKit.fmt(Game.economy.balance(cur, ch)), 18) + 54 + 16)
	var px: float = mid - float(widths.reduce(func(a, b): return a + b, 0.0)) * 0.5 + 8.0
	for i in curs.size():
		currency_pill(Vector2(roundf(px), SLOT_Y + 32), str(curs[i]), Game.economy.balance(str(curs[i]), ch))
		tour_mark("purses", Rect2(Vector2(roundf(px), SLOT_Y + 32), Vector2(float(widths[i]) - 16, 34)))   # decision 43
		px += float(widths[i])
	# The trades under the slot: one row an amount, the lower currency up and the higher back down.
	y = SLOT_Y + 84
	for pair in pairs:
		var lo := str(pair[0])
		var hi := str(pair[1])
		var rate := _rate(lo, hi)
		for amt in ([500, 2500] if pairs.size() == 1 else [500]):
			var back := maxi(1, int(round(amt * rate)))
			btn(Rect2(mid - 336, y, 328, BTN_H + 4), Tx.t("ui.exchange.pay_for") % [UiKit.fmt(amt), currency_name(lo), currency_name(hi)], "ex", [lo, hi, amt], true)
			btn(Rect2(mid + 8, y, 328, BTN_H + 4), Tx.t("ui.exchange.pay_for") % [UiKit.fmt(back), currency_name(hi), currency_name(lo)], "ex", [hi, lo, back])
			y += 60
	para(Rect2(fx + INSET, y + 4, frame_rect.size.x - INSET * 2.0, frame_rect.end.y - y - 12), Tx.t("ui.exchange.rate_note"), 16, UiKit.MIST, 2)
	MarketKit.flight(self, coins)

func on_action(id: String, data) -> void:
	if id == "ex":
		var r := submit({"type": "exchange_currency", "from": str(data[0]), "to": str(data[1]), "amount": int(data[2])})
		if r.get("ok", false):
			flash(Tx.t("ui.exchange.received") % int(r.received))
			coins = MarketKit.fly(self, Page.currency_icon(str(data[0])), Vector2(frame_rect.get_center().x, SLOT_Y + 50), Vector2(frame_rect.get_center().x, WINDOW.end.y - 40), 0.25)
