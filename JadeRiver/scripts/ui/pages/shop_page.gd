extends Page
## Shops (S21, S39, Part 9.11), P5 as the merchant's own stall (docs/page_identity.md row 8, mockup 17; decisions 11, 14
## and 24). A red and cream awning with the shop's name on a lacquer sign; the merchant behind the counter at the left with
## her nameplate and her bark; the wares on plank shelves, each on a jade mat with a paper price tag (five a shelf, two
## shelves in view, the rest a drag away); the deal laid on the counter plank (the ware, what it does, how many, the
## total, Buy); the purses on the counter's front. Beside the stall "your bag": the gourd's spaces five across, each with
## what it sells for, and Sell under them, on the stall's own timber wall under the same awning (roadmap decision 42:
## one background for the shop and the bag; decision 24 had drawn it as a patch of the gourd's heaven). Buying and
## selling face each other with no tabs; buy-back is a small token in the bag's header (decision 11: no column), which
## turns the same spaces to the last sales, each with its buy-back price.
## Prices come from the Economy authority; a stale price is refused and re-shown. The page submits intents only.

const BagPage = preload("res://scripts/ui/pages/inventory_page.gd")
const DialoguePage = preload("res://scripts/ui/pages/dialogue_page.gd")
const Avatar = preload("res://scripts/avatar.gd")
const SKY := Rect2(808, 0, 472, 720)          # the bag's side beside the stall
const WARES := Rect2(232, 108, 568, 336)      # the shelves: five wares a shelf, two in view
const WARE := Vector2(110, 168)
const PER_SHELF := 5
const COUNTER_Y := 452.0
const FRONT_Y := 616.0
const FEET := Vector2(146, 520)
const TOP_SCALE := 6      # decision 42: a top-down merchant (TopdownDoll), screen px an art px
const BAG_AT := Vector2(812, 164)             # the gourd's spaces
const BAG_COLS := 5
const BAG_PITCH := 104.0                      # a space and its price under it
const BAG_ROWS := 4

var shop_id := ""
var npc := ""
var sel_buy := -1
var sel_sell := -1
var sel_back := -1
var sold := false          # the bag's side shows the last sales, to buy back
var qty := 1
var doll: Node2D           # the merchant, drawn behind her counter
var bark := ""
var bought := {}           # the ware on its way down to the counter (MarketKit.fly)

func _init() -> void:
	title = Tx.t("ui.shop.shop")
	identity = Identity.new("wood_dark", false, "own", "stall_awning_bag_beside", 0.25)
	grade_rims = true

func setup() -> void:
	shop_id = str(args.get("shop", args.get("tab", "old_ma")))   # (--open-page=shop:<id> for previews)
	if page_id == "library": shop_id = "jade_sect" if str(c().training_sect.get("id", "")) == "jade_sect" else "cloud_sect"
	title = str(ContentDB.entry("shops", shop_id).get("name", Tx.t("ui.shop.shop")))
	npc = str(args.get("npc", ""))
	if npc == "":
		for n in ContentDB.all("npcs"):
			if ("shop:" + shop_id) in n.get("services", []):
				npc = str(n.id)
				break
	var who := ContentDB.entry("npcs", npc)
	if not who.is_empty():
		# Decision 42: the merchant as the game draws them: the top-down figure in the top-down game.
		doll = TopdownDoll.new() if TopdownDoll.shown() else Avatar.new()
		doll.visible = false
		TopdownDoll.dress(doll, DialoguePage.full_outfit(who.get("outfit", {})))
		doll.set("facing", 1)
		add_child(doll)
		doll.play("idle")
		var barks: Array = who.get("barks", [])
		if not barks.is_empty(): bark = str(barks[int(Clock.reset_day(Clock.now_utc()) / 86400.0) % barks.size()])

func content_rect() -> Rect2:
	return Rect2(WARES.position, Vector2(WARES.size.x, FRONT_Y - WARES.position.y))

# ------------------------------------------------------------------ the stall and the heaven
func draw_surface(_r: Rect2) -> void:
	# The stall's back wall of dark boards between its two posts, shadowed under the awning.
	MarketKit.planks(self, Rect2(26, 84, 764, COUNTER_Y - 84), UiKit.SURFACE.wood_dark, 58.0)
	vshade(Rect2(26, 84, 764, 80), Color(UiKit.INK, 0.55), Color(UiKit.INK, 0.0))
	ground(Rect2(26, 84, 764, COUNTER_Y - 84), UiKit.SURFACE.wood_dark)
	for x in [8.0, 790.0]: hshade(Rect2(x, 40, 18, 680), UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.3), UiKit.SURFACE.wood)
	# The shelves' planks under each row of wares, as far as the shelves scroll.
	var off := float(scroll.get("wares", 0.0))
	for row in 3:
		var y := WARES.position.y + row * WARE.y - fmod(off, WARE.y) + 158.0
		if y > WARES.position.y + 20 and y < COUNTER_Y - 6:
			draw_rect(Rect2(226, y + 5, 568, 5), Color(UiKit.INK, 0.4))
			vshade(Rect2(226, y, 568, 8), UiKit.SURFACE.peg, UiKit.SURFACE.wood)
	# Decision 42 (the user: "when in trading I want the shop and player bag background to be the same"): the bag's side
	# is the stall's own timber wall under the same awning, where it was a patch of the gourd's night sky.
	MarketKit.planks(self, Rect2(SKY.position.x, 84, SKY.size.x - 8.0, 720 - 84), UiKit.SURFACE.wood_dark, 58.0)
	vshade(Rect2(SKY.position.x, 84, SKY.size.x - 8.0, 80), Color(UiKit.INK, 0.55), Color(UiKit.INK, 0.0))
	vshade(Rect2(SKY.position.x, 560, SKY.size.x - 8.0, 160), Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.35))
	ground(Rect2(SKY.position.x, 84, SKY.size.x - 8.0, 720 - 84), UiKit.SURFACE.wood_dark)
	hshade(Rect2(1272, 40, 8, 680), UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.3))
	# The awning: red and cream stripes and a scalloped valance over the stall and the bag's side, dropping into place as
	# the stall opens.
	var drop := roundf((1.0 - unfold()) * -24.0)
	for i in 28:
		var x := 8.0 + i * 46.0
		var col: Color = UiKit.BLOOD if i % 2 == 0 else UiKit.SURFACE.talisman
		var w := minf(46.0, 1272.0 - x)
		if w <= 0.0: break
		draw_rect(Rect2(x, drop, w, 76), col)
		var sc := PackedVector2Array()
		for k in 13: sc.append(Vector2(x + w * 0.5 + cos(PI * k / 12.0) * w * 0.5, 76 + drop + sin(PI * k / 12.0) * 22.0))
		draw_colored_polygon(sc, col.lerp(UiKit.INK, 0.08))
	vshade(Rect2(8, drop, 1264, 30), Color(UiKit.INK, 0.25), Color(UiKit.INK, 0.0))
	draw_rect(Rect2(8, 74 + drop, 1264, 2), Color(UiKit.INK, 0.3))
	# The merchant standing behind her counter (her own layers, at 2.5 as the self family's figures).
	if is_instance_valid(doll):
		if doll is TopdownDoll: doll.draw_on(self, FEET + Vector2(0, -56), TOP_SCALE)   # risen to show her above the counter
		else: doll.draw_on(self, FEET, 2.5)
	# The counter plank, its lip and its front.
	vshade(Rect2(8, COUNTER_Y, 800, 148), UiKit.SURFACE.board, UiKit.SURFACE.board_edge)
	for y in range(int(COUNTER_Y) + 12, int(COUNTER_Y) + 146, 23): draw_rect(Rect2(8, y, 800, 1), Color(UiKit.SURFACE.board_line, 0.12))
	draw_rect(Rect2(8, COUNTER_Y, 800, 3), Color(UiKit.PALE_GOLD, 0.45))
	ground(Rect2(8, COUNTER_Y, 800, 148), UiKit.SURFACE.board)
	vshade(Rect2(0, FRONT_Y - 16, 824, 16), UiKit.SURFACE.talisman_edge, UiKit.SURFACE.wood)
	MarketKit.planks(self, Rect2(8, FRONT_Y, 800, 104), UiKit.SURFACE.wood_dark, 100.0)
	vshade(Rect2(8, FRONT_Y, 800, 16), Color(UiKit.INK, 0.45), Color(UiKit.INK, 0.0))
	ground(Rect2(8, FRONT_Y, 800, 104), UiKit.SURFACE.wood_dark)

## The shop's name on a black lacquer sign hung from the awning.
func title_rect() -> Rect2:
	return Rect2(168, 20, 488, 60)

func draw_title_mount(r: Rect2) -> void:
	for x in [r.position.x + 40, r.end.x - 40]: draw_line(Vector2(x, 0), Vector2(x, r.position.y + 6), UiKit.SURFACE.peg_dark, 3.0)
	face(r, "market_plate")

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var shop := ContentDB.entry("shops", shop_id)
	var currency := str(shop.get("currency", "silver_tael"))
	var stock: Array = Game.economy.stock(ch, shop_id)
	# Decision 43: a tour's anchors (the shelves, the counter plank, the purses on its front, and the bag's side).
	tour_mark("wares", WARES)
	tour_mark("counter", Rect2(40, COUNTER_Y, 760, FRONT_Y - COUNTER_Y))
	tour_mark("purse", Rect2(40, FRONT_Y, 760, 80))
	tour_mark("bag_side", SKY)
	_merchant()
	_shelves(ch, stock)
	_counter(ch, stock)
	_front(ch, shop, currency)
	if sold: _sold(ch)
	else: _bag(ch)
	MarketKit.flight(self, bought)

## The merchant behind her counter: her nameplate, her figure and her bark in a bubble that pops as the stall opens.
func _merchant() -> void:
	var who := ContentDB.entry("npcs", npc)
	if who.is_empty(): return
	var plate := Rect2(68, 112, 156, 56)
	face(plate, "market_plate")
	text(plate.position + Vector2(0, 25), str(who.get("name", npc)), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plate.size.x)
	text(plate.position + Vector2(0, 45), str(who.get("title", "")), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, plate.size.x)
	if bark == "": return
	var w := minf(160.0, ceilf(UiKit.text_width(bark, 16)) + 28.0)
	var lines := _wrap(bark, 16, w - 28.0).size()
	var b := Rect2(64, 186, w, 20.0 + lines * UiKit.line_height(16))
	var k := unfold()
	var tail := b.position + Vector2(34, b.size.y + 12)
	draw_set_transform(tail * (1.0 - k), 0.0, Vector2.ONE * k)
	rounded(b.grow(2), 14.0, UiKit.SURFACE.talisman_edge)
	rounded(b, 13.0, UiKit.SURFACE.talisman)
	draw_colored_polygon(PackedVector2Array([b.position + Vector2(30, b.size.y - 1), b.position + Vector2(48, b.size.y - 1), b.position + Vector2(34, b.size.y + 12)]), UiKit.SURFACE.talisman)
	draw_set_transform(Vector2.ZERO)
	ground(b, UiKit.SURFACE.talisman)
	para(Rect2(b.position + Vector2(14, 8), b.size - Vector2(28, 8)), bark, 16, UiKit.PAPER_INK)

## The wares on their shelves: each on a jade mat, its price tag tied under it and its name below; the rotating ones
## flagged "today"; the chosen one lit gold.
func _shelves(ch, stock: Array) -> void:
	if stock.is_empty(): return
	list("wares", WARES, ceili(stock.size() / float(PER_SHELF)), WARE.y, func(row: int, rr: Rect2):
		for col in PER_SHELF:
			var i := row * PER_SHELF + col
			if i >= stock.size(): return
			_ware(ch, stock[i], i, Rect2(rr.position + Vector2(col * WARE.x, 0), WARE))
	)

func _ware(_ch, s: Dictionary, i: int, r: Rect2) -> void:
	var locked := str(s.locked) != ""
	if sel_buy == i:
		glow(r.grow(10), Color(UiKit.GOLD, 0.22 * _halo()))
		draw_rect(r.grow(-1), UiKit.GOLD, false, 2.0)
	var mat := Rect2(r.position + Vector2(15, 2), Vector2(80, 80))
	rounded(Rect2(mat.position + Vector2(0, 3), mat.size), 6.0, Color(UiKit.INK, 0.35))
	vshade(mat, UiKit.JADE_SHADOW.lerp(UiKit.DEEP_TEAL, 0.3), UiKit.DEEP_TEAL)
	draw_rect(mat.grow(-1), Color(UiKit.BRIGHT_JADE, 0.25), false, 2.0)
	slot_box(Rect2(mat.position + Vector2(2, 2), Vector2(SLOT, SLOT)), str(s.item), 0, "", "", null, false, locked)
	MarketKit.price_tag(self, r.get_center().x, r.position.y + 84, str(s.currency), int(s.price))
	var nm := ContentDB.item_name(str(s.item))
	rich(Rect2(r.position.x + 3, r.position.y + 118, r.size.x - 6, 40), [[nm, UiKit.HOLLOW if locked else UiKit.PAPER]], 14, true)
	if s.get("rotating", false):
		var tg := Rect2(r.position + Vector2(-2, 0), Vector2(ceilf(UiKit.text_width(Tx.t("ui.shop.today"), 14)) + 16, 22))
		rounded(tg, 3.0, UiKit.SURFACE.lacquer)
		ground(tg, UiKit.SURFACE.lacquer)
		text(tg.position + Vector2(8, 16), Tx.t("ui.shop.today"), 14, UiKit.PAPER)
	region(r, "pick", i, not locked, str(s.locked))

## The deal on the counter plank: the chosen ware on its cloth, what it is and does, how many, the total and Buy.
func _counter(ch, stock: Array) -> void:
	if sel_buy < 0 or sel_buy >= stock.size():
		para(Rect2(72, COUNTER_Y + 30, 680, 90), Tx.t("ui.shop.tap_an_item_to_buy"), 20, UiKit.PAPER_INK, 3)
		return
	var it: Dictionary = stock[sel_buy]
	var def := ContentDB.item(str(it.item))
	var cloth := Rect2(44, COUNTER_Y + 14, 116, 116)
	rounded(Rect2(cloth.position + Vector2(0, 4), cloth.size), 6.0, Color(UiKit.INK, 0.3))
	vshade(cloth, UiKit.JADE_SHADOW, UiKit.DEEP_TEAL)
	draw_rect(cloth.grow(-2), Color(UiKit.GOLD, 0.55), false, 3.0)
	if bought.is_empty() or t - float(bought.t0) >= float(bought.dur) or UiKit.reduce_motion():
		icon_at(Rect2(cloth.position + Vector2(26, 26), Vector2(64, 64)), str(it.item))
	var x := 168.0
	text(Vector2(x, COUNTER_Y + 36), ContentDB.item_name(str(it.item)), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, 296)
	var grade := str(def.get("grade", "plain"))
	draw_circle(Vector2(x + 6, COUNTER_Y + 56), 6.0, UiKit.PAPER_INK, true, -1.0, true)
	draw_circle(Vector2(x + 6, COUNTER_Y + 56), 4.5, UiKit.grade_color(grade), true, -1.0, true)
	text(Vector2(x + 18, COUNTER_Y + 61), Tx.t("ui.shop.grade_hold") % [grade.capitalize(), ch.inventory.count(str(it.item))], 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, 278)
	para(Rect2(x, COUNTER_Y + 70, 292, 66), str(def.get("desc", "")), 16, UiKit.PAPER_INK, 3)
	var stackable := int(def.get("stack", 1)) > 1
	var n := qty if stackable else 1
	if stackable:
		btn(Rect2(476, COUNTER_Y + 12, 56, 56), "−", "qty", -1)
		text(Vector2(532, COUNTER_Y + 50), str(qty), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 56)
		btn(Rect2(588, COUNTER_Y + 12, 56, 56), "+", "qty", 1)
		btn(Rect2(652, COUNTER_Y + 12, 88, 56), "×10", "qty", 10)
	var total := int(it.price) * n
	var have: int = Game.economy.balance(str(it.currency), ch)
	icon_at(Rect2(476, COUNTER_Y + 80, 32, 32), Page.currency_icon(str(it.currency)))
	text(Vector2(514, COUNTER_Y + 104), UiKit.fmt(total), 22, UiKit.PAPER_INK)
	text(Vector2(476, COUNTER_Y + 132), Tx.t("ui.shop.left_after") % UiKit.fmt(have - total) if have >= total else Tx.t("ui.shop.not_enough") % currency_name(str(it.currency)),
		14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, 110)
	btn(Rect2(592, COUNTER_Y + 78, 200, 60), Tx.t("ui.shop.buy_n") % n if stackable else Tx.t("ui.shop.buy"), "buy", null, true, have >= total,
		Tx.t("ui.shop.not_enough") % currency_name(str(it.currency)))

## The purses on the counter's front, the shop's own coin first and ringed, and what its prices are in.
func _front(ch, shop: Dictionary, currency: String) -> void:
	var x := 72.0
	var purses: Array = [currency]
	for cur in ["silver_tael", "spirit_stone"]:
		if not cur in purses and (cur == "silver_tael" or Game.economy.balance(cur, ch) > 0): purses.append(cur)
	for cur in purses:
		if cur == currency: glow(Rect2(x - 14, FRONT_Y + 14, UiKit.text_width(UiKit.fmt(Game.economy.balance(cur, ch)), 18) + 82, 62), Color(UiKit.GOLD, 0.3 * _halo()))
		x += currency_pill(Vector2(x, FRONT_Y + 28), cur, Game.economy.balance(cur, ch)) + 16.0
		if x > 500.0: break
	text(Vector2(552, FRONT_Y + 38), Tx.t("ui.shop.prices_in") % currency_name(currency), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 240)
	if shop.has("rotation"): text(Vector2(552, FRONT_Y + 62), Tx.t("ui.shop.marked_change"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 240)

## The bag's header in the heaven: the gourd's token (lit while it shows) and the buy-back token.
func _tokens(ch) -> void:
	var inv: InventoryState = ch.inventory
	var used := "%d / %d" % [inv.bag.size() - inv.free_slots(), inv.capacity()]
	var bb: Array = Game.account.economy.get("buyback", [])
	var a := Rect2(BAG_AT.x, 96, ceilf(UiKit.text_width(Tx.t("ui.shop.your_bag"), 18) + UiKit.text_width(used, 16)) + 48, TAB_H)
	BagPage.token(self, a, Tx.t("ui.shop.your_bag"), used, not sold)
	region(a, "bag_side", false)
	var bl := Tx.t("ui.shop.buy_back")
	var b := Rect2(0, 96, ceilf(UiKit.text_width(bl, 18) + UiKit.text_width(str(bb.size()), 16)) + 48, TAB_H)
	b.position.x = BAG_AT.x + BAG_COLS * MarketKit.PITCH - 4 - b.size.x
	BagPage.token(self, b, bl, str(bb.size()), sold)
	region(b, "bag_side", true)

## "Your bag": the gourd's spaces, each with what it sells for, and the chosen one's Sell on the sea of cloud.
func _bag(ch) -> void:
	_tokens(ch)
	var bag: Array = ch.inventory.bag
	text(Vector2(BAG_AT.x + 2, 158), Tx.t("ui.shop.tap_to_sell"), 14, UiKit.MIST)
	MarketKit.sky_grid(self, "bag", Rect2(BAG_AT + Vector2(0, 8), Vector2(BAG_COLS * MarketKit.PITCH + GUTTER - 4, BAG_ROWS * BAG_PITCH)), BAG_COLS, BAG_PITCH,
		bag.size(), func(i): return bag[i], "pick_sell", sel_sell, func(i: int, r: Rect2):
			var s: Dictionary = bag[i]
			var price := LootRules.sell_price(str(s.id), s if ContentDB.is_equipment(str(s.id)) else null)
			if price <= 0:
				text(Vector2(r.position.x, r.end.y + 18), Tx.t("ui.shop.cannot_sell"), 14, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				return
			_tael(Vector2(r.get_center().x - UiKit.text_width(UiKit.fmt(price), 14) * 0.5 - 4, r.end.y + 13))
			text(Vector2(r.position.x + 5, r.end.y + 18), UiKit.fmt(price), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x))
	var foot := 600.0
	if sel_sell < 0 or sel_sell >= bag.size() or bag[sel_sell] == null:
		para(Rect2(BAG_AT.x, foot + 6, 396, 60), Tx.t("ui.shop.sell_for_a_quarter_of"), 16, UiKit.PAPER, 2)
		text(Vector2(BAG_AT.x, foot + 76), Tx.t("ui.shop.sales_pay") % currency_name("silver_tael"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 396)
		return
	var s2: Dictionary = bag[sel_sell]
	var price2 := LootRules.sell_price(str(s2.id), s2 if ContentDB.is_equipment(str(s2.id)) else null)
	var n := int(s2.get("count", 1))
	icon_at(Rect2(BAG_AT.x, foot + 8, 32, 32), str(s2.id))
	text(Vector2(BAG_AT.x + 40, foot + 22), ContentDB.item_name(str(s2.id)), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 124 if n > 1 else 244)
	text(Vector2(BAG_AT.x + 40, foot + 42), Tx.t("ui.shop.n_each") % [n, UiKit.fmt(price2)], 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 124)
	var right := BAG_AT.x + BAG_COLS * MarketKit.PITCH - 4
	if n > 1:
		btn(Rect2(right - 228, foot + 2, 110, 52), Tx.t("ui.shop.sell_one_for") % UiKit.fmt(price2), "sell", 1, false, true, "", 18)
		btn(Rect2(right - 110, foot + 2, 110, 52), Tx.t("ui.shop.sell_all_for") % [n, UiKit.fmt(price2 * n)], "sell", n, true, true, "", 18)
	else:
		btn(Rect2(right - 110, foot + 2, 110, 52), Tx.t("ui.shop.sell_one_for") % UiKit.fmt(price2), "sell", 1, true, true, "", 18)
	text(Vector2(BAG_AT.x, foot + 76), Tx.t("ui.shop.sales_pay") % currency_name("silver_tael"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 396)

## The last sales, floating where the bag was: each with what buying it back costs, and Buy back under them.
func _sold(ch) -> void:
	_tokens(ch)
	var bb: Array = Game.account.economy.get("buyback", [])
	text(Vector2(BAG_AT.x + 2, 158), Tx.t("ui.shop.tap_to_buy_back"), 14, UiKit.MIST)
	if bb.is_empty():
		para(Rect2(BAG_AT.x, 200, 396, 90), Tx.t("ui.shop.nothing_sold"), 18, UiKit.MIST, 4)
		return
	MarketKit.sky_grid(self, "sold", Rect2(BAG_AT + Vector2(0, 8), Vector2(BAG_COLS * MarketKit.PITCH + GUTTER - 4, BAG_ROWS * BAG_PITCH)), BAG_COLS, BAG_PITCH,
		bb.size(), func(i): return bb[i].get("entry", {}), "pick_back", sel_back, func(i: int, r: Rect2):
			_tael(Vector2(r.get_center().x - UiKit.text_width(UiKit.fmt(int(bb[i].price)), 14) * 0.5 - 4, r.end.y + 13))
			text(Vector2(r.position.x + 5, r.end.y + 18), UiKit.fmt(int(bb[i].price)), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x))
	var foot := 600.0
	if sel_back < 0 or sel_back >= bb.size():
		para(Rect2(BAG_AT.x, foot + 6, 396, 60), Tx.t("ui.shop.buy_back_hint"), 16, UiKit.PAPER, 2)
		return
	var e: Dictionary = bb[sel_back]
	var ent: Dictionary = e.get("entry", {})
	icon_at(Rect2(BAG_AT.x, foot + 8, 32, 32), str(ent.get("id", "")))
	var q := str(ent.get("quality", ""))
	text(Vector2(BAG_AT.x + 40, foot + 22), ContentDB.item_name(str(ent.get("id", ""))), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 170)
	text(Vector2(BAG_AT.x + 40, foot + 42), ("%s · " % q.capitalize() if q != "" else "") + "×%d" % int(ent.get("count", 1)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 170)
	var right := BAG_AT.x + BAG_COLS * MarketKit.PITCH - 4
	btn(Rect2(right - 180, foot + 2, 180, 52), Tx.t("ui.shop.buy_back_2") % UiKit.fmt(int(e.price)), "buyback", sel_back, true,
		Game.economy.balance("silver_tael", ch) >= int(e.price), Tx.t("ui.shop.not_enough") % currency_name("silver_tael"), 18)

## A tael's small gold mark before a price under a space.
func _tael(c: Vector2) -> void:
	draw_circle(c, 5.5, UiKit.INK, true, -1.0, true)
	draw_circle(c, 4.5, UiKit.GOLD, true, -1.0, true)
	draw_rect(Rect2(c - Vector2(1.5, 1.5), Vector2(3, 3)), UiKit.BRONZE)

# ------------------------------------------------------------------ taps
func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"pick":
			sel_buy = int(data)
			qty = 1
		"pick_sell": sel_sell = int(data)
		"pick_back": sel_back = int(data)
		"bag_side":
			sold = bool(data)
			sel_back = -1
		"qty": qty = clampi(qty + int(data), 1, 99)
		"buy":
			var stock: Array = Game.economy.stock(ch, shop_id)
			var it: Dictionary = stock[sel_buy]
			var n := qty if int(ContentDB.item(str(it.item)).get("stack", 1)) > 1 else 1
			var r := submit({"type": "buy", "shop": shop_id, "item": str(it.item), "count": n, "price": int(it.price), "learn": str(it.get("learn", ""))})
			if r.get("ok", false):
				Audio.play("coin", "UI")
				flash(Tx.t("ui.shop.bought") % [ContentDB.item_name(str(it.item)), n])
				var off := float(scroll.get("wares", 0.0))
				var at := WARES.position + Vector2((sel_buy % PER_SHELF) * WARE.x + 55, (sel_buy / PER_SHELF) * WARE.y + 44 - off)
				bought = MarketKit.fly(self, str(it.item), at, Vector2(102, COUNTER_Y + 72), 0.25)
		"sell":
			if submit({"type": "sell", "index": sel_sell, "count": int(data)}).get("ok", false):
				Audio.play("coin", "UI")
				if ch.inventory.bag[sel_sell] == null: sel_sell = -1
		"buyback":
			if submit({"type": "buyback", "index": int(data)}).get("ok", false):
				Audio.play("coin", "UI")
				sel_back = -1
