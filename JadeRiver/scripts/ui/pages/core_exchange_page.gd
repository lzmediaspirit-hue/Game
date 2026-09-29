extends Page
## S46 · The Core Exchange at the Beast Hall: fixed Spirit Stones for beast cores by tier, up to 60 a day; and a place
## to rest your animals, which mends any Grievous Wound.
## P5 (docs/page_identity.md row 34; the Beasts family, §2): the Beast Hall's core urn and its tally stick. On the rough
## timber wall, your cores stand on shelves at the left, a shelf a tier; the glazed urn in the middle takes the chosen
## one, and the Spirit Stones spill from its spout at the right; the day's bamboo tally runs across the foot, a notch a
## stone paid; the straw bed in the corner rests the animals. A sold core drops into the urn and a stone clinks out of
## the spout (0.3 s). The page submits intents only.

const SHELF := Rect2(160, 136, 352 + GUTTER, 432)   # the shelves: a row of cores a plank, 72 apart
const PER_SHELF := 5
const URN := Rect2(548, 176, 200, 236)
const MOUTH := Vector2(640, 212)
const SPOUT := Vector2(726, 356)
const HEAP := Vector2(900, 424)
const BED := Rect2(868, 470, 252, 124)
const TALLY := Rect2(160, 616, 680, 24)
const TIERS := ["low", "mid", "high", "peak"]

var chosen := ""          # the core at the urn's mouth
var drop := {}            # the sold core on its way into the urn (MarketKit.fly)
var clink := {}           # the stone on its way out of the spout

func _init() -> void:
	title = Tx.t("ui.cores.title")
	frame_rect = WINDOW_LARGE
	identity = Identity.new("wood", false, "own", "urn_shelf_spout_tally", 0.3)

func content_rect() -> Rect2:
	return frame_rect.grow(-24)

func draw_surface(r: Rect2) -> void:
	rounded(r.grow(3), 8.0, UiKit.INK)
	BeastKit.timber(self, r, 34)
	draw_rect(r.grow(-6), Color(UiKit.SURFACE.wood_dark, 0.9), false, 4.0)
	# The hall's floor: a band of trodden straw along the foot, darker than the bed's.
	vshade(Rect2(r.position.x + 6, r.end.y - 72, r.size.x - 12, 66), Color(UiKit.SURFACE.soil, 0.0), Color(UiKit.SURFACE.soil, 0.7))
	ground(r, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.18))

func title_rect() -> Rect2:
	return Rect2(frame_rect.get_center().x - 180, frame_rect.position.y + 16, 360, 52)

func draw_title_mount(r: Rect2) -> void:
	BeastKit.hung_board(self, r, frame_rect.position.y + 2)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cores := _cores(ch)
	if not cores.has(chosen): chosen = cores[0] if not cores.is_empty() else ""
	tour_mark("shelves", SHELF)   # decision 43: a tour's anchors
	tour_mark("urn", URN)
	tour_mark("tally", TALLY)
	_shelves(ch, cores)
	_urn(ch)
	_spout(ch)
	_bed(ch)
	_tally(ch)
	MarketKit.flight(self, drop)
	MarketKit.flight(self, clink)

## The cores you carry, by tier (low to peak), each tier's in the bag's order.
func _cores(ch) -> Array:
	var out: Array = []
	for tier in TIERS:
		for st in ch.inventory.bag:
			if st == null: continue
			var cd: Dictionary = ContentDB.item(str(st.id)).get("core", {})
			if str(cd.get("tier", "")) == tier and not out.has(str(st.id)): out.append(str(st.id))
	return out

## The shelves: a plank per row, each tier starting a new one with its name and price cut on a board at its end.
func _shelves(ch, cores: Array) -> void:
	var prices: Dictionary = ContentDB.config("pet_growth").get("cores", {}).get("price", {})
	# The shelving: two uprights and a plank for each row it holds, whether or not a core stands on it.
	for x in [SHELF.position.x - 12, SHELF.position.x + SHELF.size.x - GUTTER]:
		vshade(Rect2(x, SHELF.position.y - 4, 8, SHELF.size.y + 4), UiKit.SURFACE.wood_dark, UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.3))
	for k in int(SHELF.size.y / 72.0):
		var plank := Rect2(SHELF.position.x - 12, SHELF.position.y + k * 72 + 56, SHELF.size.x - GUTTER + 20, 12)
		vshade(plank, UiKit.SURFACE.wood.lerp(UiKit.BRONZE, 0.35), UiKit.SURFACE.wood_dark)
		draw_rect(Rect2(plank.position.x, plank.end.y, plank.size.x, 3), Color(UiKit.INK, 0.35))
	if cores.is_empty():
		BeastKit.board(self, Rect2(SHELF.position.x, SHELF.position.y + 8, 344, 112))
		para(Rect2(SHELF.position.x + 18, SHELF.position.y + 24, 308, 90), Tx.t("ui.cores.none"), 16, UiKit.PAPER)
		return
	var rows: Array = []   # [tier, [core ids]]
	for tier in TIERS:
		var of: Array = cores.filter(func(id): return str(ContentDB.item(id).core.tier) == tier)
		var k := 0
		while k < of.size():
			rows.append([tier, of.slice(k, k + PER_SHELF), k == 0])
			k += PER_SHELF
	list("shelf", SHELF, rows.size(), 72, func(i: int, rr: Rect2):
		var row: Array = rows[i]
		var x := rr.position.x
		for id in row[1]:
			var r := Rect2(x, rr.end.y - 60, 48, 48)
			slot_box(r, str(id), ch.inventory.count(str(id)), "", "pick", str(id), chosen == str(id))
			x += 54
		if row[2]:   # the tier's board at the shelf's right end
			var b := BeastKit.board(self, Rect2(rr.end.x - 80, rr.position.y + 4, 80, 40))
			text(b.position + Vector2(0, 18), Tx.t("ui.cores.tier_" + str(row[0])), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, b.size.x)
			text(b.position + Vector2(0, 35), Tx.t("ui.cores.each_short") % int(prices.get(str(row[0]), 1)), 14, UiKit.PAPER,
				HORIZONTAL_ALIGNMENT_CENTER, b.size.x)
	)

## The urn, the chosen core at its mouth, and the deal under it: its name, count and price, Sell one and Sell all.
func _urn(ch) -> void:
	var rise := (1.0 - unfold()) * 24.0
	draw_texture_rect(UiKit.hd_texture("core_urn"), Rect2(URN.position + Vector2(0, rise), URN.size), false)
	if chosen == "":
		para(Rect2(URN.position.x - 30, URN.end.y + 24, URN.size.x + 60, 80), Tx.t("ui.cores.urn_empty"), 16, UiKit.MIST)
		return
	var cd: Dictionary = ContentDB.item(chosen).core
	var price := int(ContentDB.config("pet_growth").get("cores", {}).get("price", {}).get(str(cd.tier), 1))
	var n: int = ch.inventory.count(chosen)
	if drop.is_empty() or t - float(drop.t0) >= float(drop.dur):
		var bob := 0.0 if UiKit.reduce_motion() else sin(t * 2.0) * 2.0
		icon_at(Rect2(MOUTH + Vector2(-32, -76 + bob), Vector2(64, 64)), chosen)
	var y := URN.end.y + 26
	text(Vector2(URN.position.x - 60, y), ContentDB.item_name(chosen), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, URN.size.x + 120)
	text(Vector2(URN.position.x - 60, y + 22), Tx.t("ui.cores.deal") % [n, Tx.plural("ui.cores.each", price) % price], 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, URN.size.x + 120)
	var left: int = Game.pets.exchange_left(ch)
	var can := left >= price
	var why := Tx.t("sim.pet.exchange_cap")
	btn(Rect2(URN.position.x - 40, y + 36, 132, BTN_H), Tx.t("ui.cores.sell_one"), "sell", [chosen, 1], false, can, why, 18)
	btn(Rect2(URN.position.x + 108, y + 36, 132, BTN_H), Tx.t("ui.cores.sell_all"), "sell", [chosen, n], true, can, why, 18)

## The spout's side: your Spirit Stones, what the Exchange will still pay today, the prices, and the heap of stones.
func _spout(ch) -> void:
	var x := 800.0
	currency_pill(Vector2(x, 132), "spirit_stone", Game.economy.balance("spirit_stone", ch))
	var prices: Dictionary = ContentDB.config("pet_growth").get("cores", {}).get("price", {})
	var left: int = Game.pets.exchange_left(ch)
	para(Rect2(x, 180, 320, 50), Tx.plural("ui.cores.today", left) % left, 16, UiKit.PALE_GOLD, 2)
	para(Rect2(x, 230, 320, 50), Tx.plural("ui.cores.prices", int(prices.get("peak", 20))) % [int(prices.get("low", 1)), int(prices.get("mid", 3)),
		int(prices.get("high", 8)), int(prices.get("peak", 20))], 14, UiKit.MIST, 2)
	var paid: int = int(ContentDB.config("pet_growth").get("cores", {}).get("daily_cap", 60)) - left
	# The stones that came out of the spout today, heaped under it on the floor.
	BeastKit.stones(self, HEAP, 6 + int(paid / 5.0), SPOUT + Vector2(14, 6), 2)

## The straw bed in the corner: the wounded animals lying in it, and Rest your animals.
func _bed(ch) -> void:
	BeastKit.straw(self, BED, 5)
	var hurt: Array = ch.pets.filter(func(p): return p.get("wounded", false))
	var x := BED.position.x + 12
	for p in hurt.slice(0, 4):
		creature_at(Rect2(x, BED.position.y + 6, 56, 48), str(ContentDB.entry("pets", str(p.species)).get("art", p.species)), "idle")
		x += 60
	if hurt.is_empty():
		text(Vector2(BED.position.x, BED.position.y + 40), fit(Tx.t("ui.cores.bed_empty"), 14, BED.size.x - 16), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, BED.size.x)
	var wounded := not hurt.is_empty()
	btn(Rect2(BED.position.x + 16, BED.end.y - 60, BED.size.x - 32, BTN_H), Tx.t("ui.cores.rest"), "rest", null, wounded, wounded, Tx.t("ui.cores.none_wounded"), 18)

## The day's tally: a bamboo stick with a notch for every Spirit Stone the Exchange may pay, cut dark as it pays them.
func _tally(ch) -> void:
	var cap := int(ContentDB.config("pet_growth").get("cores", {}).get("daily_cap", 60))
	var paid := cap - int(Game.pets.exchange_left(ch))
	text(Vector2(TALLY.position.x, TALLY.position.y - 10), Tx.t("ui.cores.tally") % [paid, cap], 14, UiKit.PALE_GOLD)
	rounded(TALLY.grow(2), 12.0, UiKit.INK)
	rounded(TALLY, 11.0, UiKit.SURFACE.bamboo)
	draw_rect(Rect2(TALLY.position.x + 8, TALLY.position.y + 3, TALLY.size.x - 16, 4), Color(UiKit.PAPER, 0.3))
	for node in [0.33, 0.66]:   # the bamboo's nodes
		draw_rect(Rect2(TALLY.position.x + TALLY.size.x * node, TALLY.position.y, 3, TALLY.size.y), UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.3))
	var step := (TALLY.size.x - 24.0) / float(maxi(1, cap))
	for i in cap:
		var nx := TALLY.position.x + 12 + i * step + step * 0.5
		var cut := i < paid
		draw_line(Vector2(nx, TALLY.position.y + 5), Vector2(nx, TALLY.end.y - 5), UiKit.SURFACE.wood_dark if cut else Color(UiKit.SURFACE.wood, 0.35), 3.0 if cut else 1.5)

func on_action(id: String, data) -> void:
	match id:
		"pick": chosen = str(data)
		"sell":
			var r := submit({"type": "sell_cores", "item": str(data[0]), "count": int(data[1])})
			if r.get("ok", false):
				flash(Tx.plural("ui.cores.sold", int(r.stones)) % [int(r.count), int(r.stones)])
				drop = MarketKit.fly(self, str(data[0]), MOUTH + Vector2(0, -44), MOUTH + Vector2(0, 8), 0.3)
				clink = MarketKit.fly(self, Page.currency_icon("spirit_stone"), SPOUT, HEAP + Vector2(0, -24), 0.3, 30.0)
				clink.t0 = t + 0.3
		"rest":
			if submit({"type": "rest_pets"}).get("ok", false): flash(Tx.t("ui.cores.rested"))
	queue_redraw()
