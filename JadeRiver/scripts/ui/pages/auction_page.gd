extends Page
## The Auction Pavilion (S21): today's lots, what each stands at, who holds it and when it closes. A bid below a bidder's
## hidden limit is answered at once; above it, you hold the lot and the item comes by mail when the hammer falls. The
## house premium depends on the path you chose. P5 as the auction stage (docs/page_identity.md row 38; decision 14): a
## black lacquer stage between red curtains, the chosen lot on a pedestal in a cone of light (its slot at twice the size),
## its price, holder and time on the lot board at the left, your two numbered bid paddles at the right, and every lot of
## the day on a small pedestal along the stage's front, a tap bringing it up. The page submits intents only.

const PEDESTAL := Rect2(530, 372, 220, 92)
const LOT := Rect2(570, 220, 140, 140)        # the chosen lot's slot, its icon at 2x
const BOARD := Rect2(128, 168, 344, 232)      # the lot board
const FLOOR_Y := 470.0
const FRONT := Rect2(128, 520, 1024, 152)     # the small pedestals along the stage's front
const SMALL_W := 144.0

var house := "pavilion"
var chosen := ""           # the lot on the pedestal (its id)
var shown_t := -1.0        # when it came up (it slides on over 0.3 s)

func _init() -> void:
	title = Tx.t("ui.auction.title")
	identity = Identity.new("lacquer_black", false, "own", "lit_pedestal_lot_row", 0.3)
	grade_rims = true

## S49: the valley's Saturday auction on Market Street uses the same page (args.house = "valley").
func setup() -> void:
	house = str(args.get("house", args.get("tab", "pavilion")))
	if house != "pavilion": title = Tx.t("ui.auction.valley_title")

func content_rect() -> Rect2:
	return Rect2(BOARD.position, Vector2(FRONT.end.x - BOARD.position.x, FRONT.end.y - BOARD.position.y))

func _lots() -> Array:
	return Game.economy.auction_lots(house).filter(func(l): return not l.get("closed", false))

# ------------------------------------------------------------------ the stage
func draw_surface(_r: Rect2) -> void:
	vshade(Rect2(0, 0, size.x, FLOOR_Y), UiKit.INK, UiKit.SURFACE.lacquer_black)
	ground(Rect2(0, 0, size.x, FLOOR_Y), UiKit.SURFACE.lacquer_black)
	# The stage floor, its boards running away from the front.
	MarketKit.planks(self, Rect2(0, FLOOR_Y, size.x, size.y - FLOOR_Y), UiKit.SURFACE.wood_dark, 96.0)
	vshade(Rect2(0, FLOOR_Y, size.x, 40), Color(UiKit.INK, 0.6), Color(UiKit.INK, 0.0))
	draw_rect(Rect2(0, FRONT.position.y - 14, size.x, 4), Color(UiKit.GOLD, 0.35))
	ground(Rect2(0, FLOOR_Y, size.x, size.y - FLOOR_Y), UiKit.SURFACE.wood_dark)
	# The cone of light from the flies onto the pedestal.
	var k := unfold()
	draw_polygon(PackedVector2Array([Vector2(596, 0), Vector2(684, 0), Vector2(PEDESTAL.end.x + 70, PEDESTAL.end.y), Vector2(PEDESTAL.position.x - 70, PEDESTAL.end.y)]),
		PackedColorArray([Color(UiKit.PALE_GOLD, 0.2 * k), Color(UiKit.PALE_GOLD, 0.2 * k), Color(UiKit.PALE_GOLD, 0.02), Color(UiKit.PALE_GOLD, 0.02)]))
	glow(Rect2(PEDESTAL.position + Vector2(-90, 50), PEDESTAL.size + Vector2(180, 40)), Color(UiKit.PALE_GOLD, 0.22 * k * _halo()))
	# The pedestal: a black lacquer drum banded in brass.
	vshade(PEDESTAL, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.25), UiKit.SURFACE.lacquer_black)
	for by in [PEDESTAL.position.y + 10, PEDESTAL.end.y - 16]: draw_rect(Rect2(PEDESTAL.position.x, by, PEDESTAL.size.x, 6), UiKit.BRONZE)
	rounded(Rect2(PEDESTAL.position.x - 16, PEDESTAL.position.y - 12, PEDESTAL.size.x + 32, 16), 4.0, UiKit.SURFACE.lacquer_black.lerp(UiKit.GOLD, 0.2))
	# The red curtains, drawn back to either side, and the valance along the top.
	for side in [0.0, 1.0]:
		var x0 := 0.0 if side == 0.0 else size.x - 120.0
		for f in 5:
			var fx := x0 + f * 24.0
			hshade(Rect2(fx, 0, 24, size.y), UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.3), UiKit.SURFACE.lacquer.lerp(UiKit.BLOOD, 0.25))
	vshade(Rect2(0, 0, size.x, 30), UiKit.SURFACE.lacquer, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.3))
	for i in 32:
		var cx := 20.0 + i * 40.0
		draw_circle(Vector2(cx, 30), 20.0, UiKit.SURFACE.lacquer, true, -1.0, true)
	draw_rect(Rect2(0, 26, size.x, 3), Color(UiKit.GOLD, 0.6))

## The title on a gilt-edged board hung from the valance.
func title_rect() -> Rect2:
	var w := ceilf(UiKit.text_width(title, UiKit.D_TITLE, true)) + 80.0
	return Rect2(640 - w * 0.5, 52, w, 60)

func draw_title_mount(r: Rect2) -> void:
	for x in [r.position.x + 30, r.end.x - 30]: draw_line(Vector2(x, 30), Vector2(x, r.position.y + 4), UiKit.GOLD, 2.0)
	MarketKit.lacquer_board(self, r, 16.0)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var lots := _lots()
	var board := BOARD
	# Decision 43: a tour's anchors (the lot on its pedestal, the lot board, the front's small pedestals).
	tour_mark("lot", Rect2(LOT.position.x - 20, LOT.position.y, LOT.size.x + 40, PEDESTAL.end.y - LOT.position.y))
	tour_mark("board", BOARD)
	tour_mark("front", FRONT)
	MarketKit.lacquer_board(self, board)
	var x := board.position.x + 24
	var w := board.size.x - 48
	if lots.is_empty():
		para(Rect2(x, board.position.y + 28, w, board.size.y - 40), Tx.t("ui.auction.no_lots"), 18, UiKit.MIST, 6)
		_purse(ch)
		return
	var li := 0
	for i in lots.size():
		if str(lots[i].id) == chosen: li = i
	var l: Dictionary = lots[li]
	chosen = str(l.id)
	var mine: bool = str(l.bidder) == ch.id
	var bidders: Array = Game.economy._au_cfg(house).get("bidders", [])
	var who := Tx.t("ui.auction.you") if mine else (str(bidders[int(l.npc) % bidders.size()]) if str(l.bidder) == "npc" and not bidders.is_empty() else Tx.t("ui.auction.another"))
	var price: int = Game.economy.auction_price(l)
	# The lot board: what it is, what it stands at, who holds it and when it closes.
	text(Vector2(x, board.position.y + 42), _lot_name(l), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
	text(Vector2(x, board.position.y + 82), Tx.t("ui.auction.stands_at") % UiKit.fmt(price), 20, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
	text(Vector2(x, board.position.y + 114), Tx.t("ui.auction.held_by") % who, 16, UiKit.BRIGHT_JADE if mine else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, w)
	text(Vector2(x, board.position.y + 142), Tx.t("ui.auction.closes_in") % UiKit.span(maxf(0.0, float(l.ends) - Clock.now_utc())), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	text(Vector2(x, board.position.y + 170), Tx.t("ui.auction.premium") % int(round(Game.economy.auction_fee(ch, house) * 100.0)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	_purse(ch)
	# The lot on its pedestal, sliding on as it comes up.
	var k := 1.0 if shown_t < 0.0 or UiKit.reduce_motion() else clampf((t - shown_t) / 0.3, 0.0, 1.0)
	k = minf(k, unfold())
	var slide := roundf((1.0 - (1.0 - pow(1.0 - k, 3.0))) * 260.0)
	slot_box(Rect2(LOT.position + Vector2(slide, 0), LOT.size), str(l.item), int(l.count))
	_paddles(ch, l, mine, price)
	# Every lot of the day on a small pedestal along the stage's front.
	var sx := FRONT.get_center().x - lots.size() * SMALL_W * 0.5
	for i in lots.size():
		var lo: Dictionary = lots[i]
		var r := Rect2(sx + i * SMALL_W, FRONT.position.y, SMALL_W - 16, FRONT.size.y)
		var on := i == li
		if on: glow(r.grow(12), Color(UiKit.PALE_GOLD, 0.2 * _halo()))
		var plinth := Rect2(r.position.x + 10, r.position.y + 72, r.size.x - 20, 24)
		vshade(plinth, UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.3), UiKit.SURFACE.lacquer_black)
		draw_rect(Rect2(plinth.position, Vector2(plinth.size.x, 3)), Color(UiKit.GOLD, 0.8 if on else 0.4))
		slot_box(Rect2(roundf(r.get_center().x - SLOT * 0.5), r.position.y - 6, SLOT, SLOT), str(lo.item), int(lo.count), "", "", null, on)
		var lp := UiKit.fmt(Game.economy.auction_price(lo))
		icon_at(Rect2(roundf(r.get_center().x - (UiKit.text_width(lp, 16) + 36) * 0.5), r.position.y + 104, 32, 32), Page.currency_icon("spirit_stone"))
		text(Vector2(r.get_center().x - (UiKit.text_width(lp, 16) + 36) * 0.5 + 36, r.position.y + 126), lp, 16,
			UiKit.BRIGHT_JADE if str(lo.bidder) == ch.id else UiKit.PALE_GOLD)
		region(r, "lot", str(lo.id))

func _lot_name(l: Dictionary) -> String:
	var nm := Tx.t("ui.auction.recipe") % ContentDB.name_of("recipes", str(l.learn)) if str(l.get("learn", "")) != "" else ContentDB.item_name(str(l.item))
	return nm + ("  ×%d" % int(l.count) if int(l.count) > 1 else "")

func _purse(ch) -> void:
	currency_pill(Vector2(BOARD.position.x + 24, BOARD.end.y - 50), "spirit_stone", Game.economy.balance("spirit_stone", ch))

## Your two bid paddles, each with your bidder's number, and the bid it raises under it: the least the lot takes, and
## half again over its price. While you hold the lot the paddles rest.
func _paddles(ch, l: Dictionary, mine: bool, price: int) -> void:
	var number := str(10 + absi(hash(str(ch.id))) % 90)
	var need: int = Game.economy.auction_min_bid(l)
	var big := int(ceil(price * 1.5))
	tour_mark("paddles", Rect2(840, 180, 312, 240))   # decision 43: a tour's anchor
	for p in [[Vector2(920, 236), need, true], [Vector2(1072, 236), big, false]]:
		var c: Vector2 = p[0]
		var lift := 0.0 if mine else -10.0
		draw_line(c + Vector2(0, 40 + lift), c + Vector2(0, 104), UiKit.SURFACE.wood, 10.0)
		draw_circle(c + Vector2(0, lift), 46.0, UiKit.INK, true, -1.0, true)
		draw_circle(c + Vector2(0, lift), 43.0, UiKit.SURFACE.talisman, true, -1.0, true)
		draw_arc(c + Vector2(0, lift), 36.0, 0.0, TAU, 40, UiKit.SURFACE.cinnabar, 3.0, true)
		ground(Rect2(c + Vector2(-30, lift - 30), Vector2(60, 60)), UiKit.SURFACE.talisman)
		text(c + Vector2(-40, lift + 10), number, 26, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, 80, true)
		if not mine:
			btn(Rect2(c.x - 72, c.y + 112, 144, 52), Tx.t("ui.auction.bid") % UiKit.fmt(int(p[1])), "bid", [str(l.id), int(p[1])], bool(p[2]), true, "", 18)
	if mine: text(Vector2(840, 400), Tx.t("ui.auction.you_lead"), 18, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, 312)

func on_action(id: String, data) -> void:
	match id:
		"lot":
			if str(data) != chosen:
				chosen = str(data)
				shown_t = t
		"bid":
			var r := submit({"type": "auction_bid", "lot": str(data[0]), "amount": int(data[1]), "house": house})
			if r.get("outbid", false): flash(Tx.t("ui.auction.outbid_at_once") % UiKit.fmt(int(r.get("bid", 0))))
			elif r.get("top", false): flash(Tx.t("ui.auction.you_lead"))
