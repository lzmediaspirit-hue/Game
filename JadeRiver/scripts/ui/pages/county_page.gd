extends Page
## The County Hall (S49 mortal kingdom): county favour and its tiers; today's three county jobs from the magistrate's
## board, or the relief fund, where silver for the county's poor earns merit and favour. P5 as the magistrate's bench
## (docs/page_identity.md row 37; decision 14): the hall's back wall with its painted screen of sea and sun and the plaque
## over it; the county favour as a cinnabar banner hanging at the left, its tiers written on the banner's paper; the high
## desk across the foot with its warrant tube, gavel and seal, and the relief box on its right. Today's jobs are three
## warrant sticks standing in the tube, the chosen one drawn up and its warrant hung at the right to read; the relief fund
## is read from the box. The tabs are the hall's two red placards. The page submits intents only.

const DESK_Y := 540.0
const TUBE := Rect2(470, 492, 152, 80)        # the warrant tube on the desk
const STICK_W := 48.0
const READ := Rect2(712, 112, 472, 256)       # the warrant (or the relief ledger) hung to read
const BANNER := Rect2(96, 116, 300, 316)
const BOX := Rect2(940, 452, 224, 92)         # the relief box on the desk's right

var chosen := -1           # the warrant stick drawn up
var drawn_t := -1.0        # when it was drawn (it slides up over 0.2 s)

func _init() -> void:
	title = Tx.t("ui.county.title")
	tabs = [{"id": "jobs", "label": Tx.t("ui.county.jobs")}, {"id": "relief", "label": Tx.t("ui.county.relief")}]
	identity = Identity.new("wood_dark", false, "own", "bench_warrant_tube_banner", 0.25)

func setup() -> void:
	if str(args.get("tab", "")) == "relief": tab = 1
	if c() != null: submit({"type": "county_jobs"})   # the board is read: today's jobs are posted and taken

func content_rect() -> Rect2:
	return READ

# ------------------------------------------------------------------ the hall
func draw_surface(_r: Rect2) -> void:
	MarketKit.planks(self, Rect2(0, 0, size.x, DESK_Y), UiKit.SURFACE.wood_dark, 64.0)
	vshade(Rect2(0, 0, size.x, 120), Color(UiKit.INK, 0.5), Color(UiKit.INK, 0.0))
	ground(Rect2(0, 0, size.x, DESK_Y), UiKit.SURFACE.wood_dark)
	# The painted screen behind the bench: waves under a red sun, in a lacquer frame.
	var scr := Rect2(420, 124, 276, 392)
	rounded(scr.grow(10), 4.0, UiKit.SURFACE.lacquer_black)
	draw_rect(scr.grow(6), Color(UiKit.GOLD, 0.6), false, 2.0)
	vshade(scr, UiKit.SURFACE.almanac, UiKit.SURFACE.scroll)
	draw_circle(scr.position + Vector2(scr.size.x * 0.5, 96), 38.0, Color(UiKit.RED, 0.8), true, -1.0, true)
	for i in 10:
		var wy := scr.position.y + 170 + i * 22
		var wave := PackedVector2Array()
		for k in 29: wave.append(Vector2(scr.position.x + k * scr.size.x / 28.0, wy + sin(k * 0.9 + i * 1.3) * 6.0))
		draw_polyline(wave, UiKit.SURFACE.water.lerp(UiKit.JADE, i * 0.05), 3.0, true)
	vshade(Rect2(scr.position.x, scr.end.y - 70, scr.size.x, 70), Color(UiKit.SURFACE.water, 0.0), Color(UiKit.SURFACE.water, 0.6))
	_banner_cloth()
	# The high desk: its black lacquer top, and a cinnabar cloth hung down its front between lacquer ends.
	vshade(Rect2(40, DESK_Y, 1200, 40), UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.18), UiKit.SURFACE.lacquer_black)
	draw_rect(Rect2(40, DESK_Y, 1200, 2), Color(UiKit.GOLD, 0.5))
	draw_rect(Rect2(40, DESK_Y + 40, 1200, size.y - DESK_Y - 40), UiKit.SURFACE.lacquer_black)
	var cloth := Rect2(160, DESK_Y + 40, 960, size.y - DESK_Y - 40)
	vshade(cloth, UiKit.SURFACE.cinnabar, UiKit.SURFACE.lacquer)
	for x in range(int(cloth.position.x) + 60, int(cloth.end.x), 120): draw_rect(Rect2(x, cloth.position.y, 3, cloth.size.y), Color(UiKit.INK, 0.15))
	draw_rect(Rect2(cloth.position.x, cloth.position.y + 10, cloth.size.x, 3), Color(UiKit.GOLD, 0.7))
	MarketKit.brass(self, Rect2(40, DESK_Y, 1200, size.y - DESK_Y), 30.0)
	ground(Rect2(40, DESK_Y, 1200, size.y - DESK_Y), UiKit.SURFACE.lacquer_black)

## The favour banner's cloth: a cinnabar hanging on a rod with tassels, its paper field sewn on.
func _banner_cloth() -> void:
	var b := BANNER
	draw_line(Vector2(b.position.x - 16, b.position.y - 4), Vector2(b.end.x + 16, b.position.y - 4), UiKit.SURFACE.wood, 8.0)
	for x in [b.position.x - 16, b.end.x + 16]: draw_circle(Vector2(x, b.position.y - 4), 7.0, UiKit.GOLD, true, -1.0, true)
	var cloth := PackedVector2Array([b.position, Vector2(b.end.x, b.position.y), Vector2(b.end.x, b.end.y), Vector2(b.get_center().x, b.end.y + 20), Vector2(b.position.x, b.end.y)])
	draw_colored_polygon(cloth, UiKit.SURFACE.cinnabar)
	cloth.append(cloth[0])
	draw_polyline(cloth, UiKit.GOLD, 2.0, true)
	for x in [b.position.x + 30, b.end.x - 30]:
		draw_line(Vector2(x, b.end.y), Vector2(x, b.end.y + 34), UiKit.GOLD, 2.0)
		draw_circle(Vector2(x, b.end.y + 36), 5.0, UiKit.SURFACE.cinnabar, true, -1.0, true)
	var paper := Rect2(b.position.x + 14, b.position.y + 56, b.size.x - 28, b.size.y - 70)
	draw_rect(paper, UiKit.SURFACE.scroll)
	draw_rect(paper, UiKit.SURFACE.scroll_edge, false, 2.0)
	ground(paper, UiKit.SURFACE.scroll)

## The title on a black lacquer plaque over the screen.
func title_rect() -> Rect2:
	return Rect2(424, 40, 432, 60)

func draw_title_mount(r: Rect2) -> void:
	face(r, "market_plate")

## The tabs are the hall's red lacquer placards, on their poles at the upper left.
func tab_rects() -> Array:
	return [Rect2(96, 40, 144, 56), Rect2(252, 40, 144, 56)]

func draw_tab(r: Rect2, i: int, state: String) -> void:
	var on := state == "selected"
	if on: glow(r.grow(14), Color(UiKit.GOLD, 0.25 * _halo()))
	rounded(r.grow(2), 4.0, UiKit.INK)
	vshade(r, UiKit.SURFACE.lacquer.lerp(UiKit.BLOOD, 0.35 if on else 0.1), UiKit.SURFACE.lacquer)
	draw_rect(r.grow(-4), Color(UiKit.GOLD, 0.9 if on else 0.45), false, 1.5)
	ground(r, UiKit.SURFACE.lacquer)
	var label := str(tabs[i].label)
	if on: inked(r.position + Vector2(0, 35), label, 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, false)
	else: text(r.position + Vector2(0, 35), label, 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	# Decision 43: a tour's anchors (the favour banner, the warrant tube, the warrant hung to read).
	tour_mark("banner", BANNER)
	tour_mark("tube", TUBE)
	tour_mark("warrant", READ)
	_banner(ch)
	var jobs: Array = ch.relations.mortal.get("jobs", [])
	if chosen < 0 or chosen >= jobs.size():
		chosen = 0
		for i in jobs.size():
			if not ch.quests.done.has(str(jobs[i])):
				chosen = i
				break
	_desk(ch, jobs)
	_warrant_sheet()
	if str(tabs[tab].id) == "jobs": _job(ch, jobs)
	else: _relief(ch)

## The banner's paper: the tier held now, the favour to the next, and every tier with what it brings, sealed once held.
func _banner(ch) -> void:
	var b := BANNER
	inked(Vector2(b.position.x, b.position.y + 38), Tx.t("ui.county.favour"), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, b.size.x, true)
	var x := b.position.x + 28
	var w := b.size.x - 56
	var y := b.position.y + 92
	var tier: Dictionary = Game.relations.favour_tier(ch)
	var nxt: Dictionary = Game.relations.next_favour_tier(ch)
	var fav: int = Game.relations.favour(ch)
	text(Vector2(x, y), Tx.t("ui.county.tier_" + str(tier.get("id", "stranger"))), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 96)
	text(Vector2(x, y), Tx.t("ui.county.favour_pts") % fav, 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_RIGHT, w)
	y += 12
	if not nxt.is_empty():
		var lo := int(tier.get("min", 0))
		var hi := int(nxt.min)
		bar(Rect2(x - 6, y, w + 12, 24), float(fav - lo) / float(maxi(1, hi - lo)), UiKit.GOLD, Tx.t("ui.county.to_next") % [hi - fav, Tx.t("ui.county.tier_" + str(nxt.id))])
	y += 44
	for t2 in Game.relations.mcfg().get("favour_tiers", []):
		var got: bool = fav >= int(t2.get("min", 0))
		var seal := Vector2(x + 8, y - 6)
		draw_circle(seal, 8.0, UiKit.BLOOD, got, 2.0, true)
		if got: draw_circle(seal, 3.0, UiKit.SURFACE.scroll, true, -1.0, true)
		text(Vector2(x + 24, y), Tx.t("ui.county.tier_" + str(t2.id)), 16, UiKit.BLOOD if got else UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 104)
		text(Vector2(x, y), Tx.t("ui.county.favour_pts") % int(t2.get("min", 0)), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_RIGHT, w)
		text(Vector2(x + 24, y + 18), Tx.t("ui.county.brings_" + str(t2.id)), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 24)
		y += 40

## The desk's things: the gavel and the seal, the warrant tube with a stick for each of today's jobs (the chosen one drawn
## up), and the relief box.
func _desk(ch, jobs: Array) -> void:
	# The gavel block and the seal.
	var strike := 0.0
	if drawn_t >= 0.0 and not UiKit.reduce_motion() and t - drawn_t < 0.2 and chosen < jobs.size() and ch.quests.done.has(str(jobs[chosen])):
		strike = sin((t - drawn_t) / 0.2 * PI) * 10.0
	rounded(Rect2(330, DESK_Y - 22 - strike, 84, 30), 4.0, UiKit.SURFACE.wood)
	draw_rect(Rect2(330, DESK_Y - 22 - strike, 84, 4), Color(UiKit.PALE_GOLD, 0.3))
	rounded(Rect2(656, DESK_Y - 30, 34, 34), 4.0, UiKit.GOLD)
	rounded(Rect2(662, DESK_Y - 44, 22, 16), 3.0, UiKit.BRONZE)
	# The tube, its sticks standing in it.
	for i in jobs.size():
		var done: bool = ch.quests.done.has(str(jobs[i]))
		var up := 0.0
		if i == chosen and str(tabs[tab].id) == "jobs":
			up = 40.0 * (clampf((t - drawn_t) / 0.2, 0.0, 1.0) if drawn_t >= 0.0 and not UiKit.reduce_motion() else 1.0)
		var sx := TUBE.position.x + 4 + i * (STICK_W + 2)
		var top := 180.0 - up
		var stick := Rect2(sx + 6, top, STICK_W - 12, TUBE.position.y + 10 - top)
		vshade(stick, UiKit.SURFACE.bamboo, UiKit.SURFACE.bamboo.lerp(UiKit.BRONZE, 0.35))
		draw_rect(Rect2(stick.position, Vector2(stick.size.x, 30)), UiKit.GOLD if done else UiKit.RED)
		draw_rect(stick, Color(UiKit.INK, 0.6), false, 1.0)
		var slip := Rect2(stick.position.x, top + 60, stick.size.x, 60)
		ground(slip, UiKit.SURFACE.bamboo)
		text(Vector2(stick.position.x, top + 82), str(i + 1), 20, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, stick.size.x)
		text(Vector2(stick.position.x, top + 106), "✓" if done else _progress(ch, str(jobs[i])), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, stick.size.x)
		region(Rect2(sx, top, STICK_W, TUBE.position.y - top), "stick", i)
	# The tube: a lacquered cylinder lit from the left, banded in brass, its round mouth ringed in gold.
	var half := TUBE.size.x * 0.5
	hshade(Rect2(TUBE.position, Vector2(half, TUBE.size.y)), UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.15), UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.4))
	hshade(Rect2(TUBE.position + Vector2(half, 0), Vector2(half, TUBE.size.y)), UiKit.SURFACE.lacquer_black.lerp(UiKit.BRONZE, 0.4), UiKit.SURFACE.lacquer_black)
	for by in [TUBE.position.y + 14, TUBE.end.y - 16]: draw_rect(Rect2(TUBE.position.x, by, TUBE.size.x, 6), UiKit.BRONZE)
	var rim := PackedVector2Array()
	for i in 33: rim.append(Vector2(TUBE.get_center().x + cos(i * TAU / 32.0) * half, TUBE.position.y + sin(i * TAU / 32.0) * 8.0))
	draw_polyline(rim, UiKit.GOLD, 2.5, true)
	glow(Rect2(TUBE.position.x - 10, TUBE.end.y - 6, TUBE.size.x + 20, 16), Color(UiKit.INK, 0.5))
	# The relief box: a slotted camphor box with its word on a brass plate; a tap reads the fund.
	var relief := str(tabs[tab].id) == "relief"
	if relief: glow(BOX.grow(20), Color(UiKit.GOLD, 0.25 * _halo()))
	rounded(BOX, 4.0, UiKit.SURFACE.wood)
	MarketKit.planks(self, BOX.grow(-4), UiKit.SURFACE.wood, 22.0, false)
	draw_rect(Rect2(BOX.get_center().x - 40, BOX.position.y + 6, 80, 8), UiKit.INK)
	MarketKit.brass(self, BOX, 18.0)
	var plate := Rect2(BOX.position.x + 20, BOX.position.y + 26, BOX.size.x - 40, 40)
	rounded(plate, 4.0, UiKit.SURFACE.lacquer_black)
	draw_rect(plate.grow(-2), Color(UiKit.GOLD, 0.7), false, 1.0)
	ground(plate, UiKit.SURFACE.lacquer_black)
	text(plate.position + Vector2(0, 27), Tx.t("ui.county.relief"), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plate.size.x)
	if not relief: region(BOX, "_tab", 1)

func _progress(ch, qid: String) -> String:
	var def := Game.quest.quest_def(ch, qid)
	var objs: Array = def.get("objectives", [])
	if objs.is_empty(): return ""
	var st: Dictionary = ch.quests.active.get(qid, {})
	return "%d/%d" % [int((st.get("progress", [0]) as Array)[0]) if not st.is_empty() else 0, int(objs[0].get("count", 1))]

## The paper hung at the right to read: a warrant, or the relief ledger.
func _warrant_sheet() -> void:
	rounded(Rect2(READ.position + Vector2(4, 6), READ.size), 3.0, Color(UiKit.INK, 0.45))
	draw_rect(READ, UiKit.SURFACE.scroll)
	draw_rect(READ.grow(-6), Color(UiKit.BLOOD, 0.5), false, 1.5)
	for x in [READ.position.x + 30, READ.end.x - 30]: draw_circle(Vector2(x, READ.position.y + 4), 4.0, UiKit.BRONZE, true, -1.0, true)
	ground(READ, UiKit.SURFACE.scroll)

## The chosen job's warrant: what the county asks, how far along it is and what it pays; the county's note at its foot.
func _job(ch, jobs: Array) -> void:
	var x := READ.position.x + 24
	var w := READ.size.x - 48
	var y := READ.position.y + 40
	if jobs.is_empty():
		para(Rect2(x, y, w, 80), Tx.t("ui.county.no_jobs"), 18, UiKit.PAPER_INK, 3)
	else:
		var qid := str(jobs[chosen])
		var def := Game.quest.quest_def(ch, qid)
		var done: bool = ch.quests.done.has(qid)
		text(Vector2(x, y), Tx.t("ui.county.today") + " · %d / %d" % [chosen + 1, jobs.size()], 14, UiKit.BLOOD, HORIZONTAL_ALIGNMENT_LEFT, w)
		text(Vector2(x, y + 30), str(def.get("name", qid)), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - (90 if done else 0))
		var objs: Array = def.get("objectives", [])
		if not objs.is_empty():
			var o: Dictionary = objs[0]
			var st: Dictionary = ch.quests.active.get(qid, {})
			var have := int((st.get("progress", [0]) as Array)[0]) if not st.is_empty() else (int(o.get("count", 1)) if done else 0)
			text(Vector2(x, y + 60), "%s  %d / %d" % [str(o.get("text", "")), have, int(o.get("count", 1))], 18, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
		var silver := 0
		for rw in def.get("rewards", []):
			if str(rw.get("kind", "")) == "grant_currency": silver = int(rw.get("amount", 0))
		text(Vector2(x, y + 86), Tx.t("ui.county.pays") % [silver, int(Game.relations.mcfg().get("reward", {}).get("favour", 10))], 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
		if done:
			var stamp := Vector2(READ.end.x - 64, READ.position.y + 60)
			draw_arc(stamp, 30.0, 0.0, TAU, 32, UiKit.BLOOD, 3.0, true)
			text(Vector2(stamp.x - 30, stamp.y + 7), Tx.t("ui.county.done"), 18, UiKit.BLOOD, HORIZONTAL_ALIGNMENT_CENTER, 60)
	para(Rect2(x, READ.end.y - 94, w, 84), Tx.t("ui.county.note"), 14, UiKit.PAPER_INK, 4)

## The relief ledger: what the fund is for, and each size of gift with Give, once a day each.
func _relief(ch) -> void:
	var x := READ.position.x + 24
	var w := READ.size.x - 48
	var y := READ.position.y + 38
	text(Vector2(x, y), Tx.t("ui.county.relief_title"), 22, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
	y += 10 + para(Rect2(x, y + 8, w, 40), Tx.t("ui.county.relief_note"), 14, UiKit.PAPER_INK, 2)
	var given: Dictionary = ch.relations.mortal.get("donated", {})
	var today := Clock.reset_day(Clock.now_utc())
	for d in Game.relations.mcfg().get("donations", []):
		var row := Rect2(x, y, w, 52)
		draw_line(Vector2(x, row.position.y), Vector2(row.end.x, row.position.y), Color(UiKit.BLOOD, 0.35), 1.0)
		text(row.position + Vector2(0, 22), Tx.t("ui.county.give") % UiKit.fmt(int(d.silver)), 18, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 176)
		var merit := int(ContentDB.entry("karma", str(d.get("deed", ""))).get("merit", 0))
		text(row.position + Vector2(0, 43), Tx.t("ui.county.gives_back") % [merit, int(d.get("favour", 0))], 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 176)
		var gave: bool = int(given.get(str(d.id), -1)) == today
		var can: bool = not gave and Game.economy.balance("silver_tael") >= int(d.silver)
		btn(Rect2(row.end.x - 160, row.position.y + 3, 160, BTN_H), Tx.t("ui.county.given") if gave else Tx.t("ui.county.donate"), "donate", str(d.id), true, can,
			Tx.t("ui.county.given_today") if gave else Tx.t("ui.county.need_silver") % UiKit.fmt(int(d.silver)), 20)
		y += 54

func on_action(id: String, data) -> void:
	match id:
		"stick":
			if str(tabs[tab].id) != "jobs": tab = 0
			chosen = int(data)
			drawn_t = t
		"donate":
			var r := submit({"type": "donate_relief", "tier": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.county.thanks"))
	queue_redraw()
