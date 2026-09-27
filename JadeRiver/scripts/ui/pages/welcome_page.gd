extends Page
## Welcome back (S07/S23): what seclusion or the idle task earned while away.
## P5 (docs/page_identity.md row 12, the Post family): the incense coil that burned while you were away, and the haul in a
## round bamboo winnowing tray. The coil's burnt length is the time away out of the cap, the glowing tip now, the unburnt
## rest what more the cap would have held; the goods lie in the tray, the rest of the ledger on a hemp slip beside it,
## and the two choices under the tray.

const COIL := Vector2(296, 316)
const COIL_R := Vector2(26, 128)   # the spiral's inner and outer radius
const TURNS := 4.0
const TRAY := Vector2(660, 330)
const TRAY_R := 190.0
const SLIP := Rect2(868, 136, 264, 424)
## The goods' places in the tray: its centre, a ring of six and a ring of twelve turned half a place.
const RINGS := [[0.0, 1, 0.0], [80.0, 6, 0.0], [152.0, 12, 0.5]]

func _init() -> void:
	title = Tx.t("ui.welcome.welcome_back")
	modal = true
	frame_rect = WINDOW_LARGE
	identity = Identity.new("wood_dark", false, "own", "coil_beside_round_tray", OPEN_MOTION_MAX)

func content_rect() -> Rect2:
	return Rect2(160, 136, 960, 512)

## A low table of dark planks.
func draw_surface(r: Rect2) -> void:
	PostKit.planks(self, r, 120.0, false)
	ground(r, UiKit.SURFACE.wood_dark)

func title_rect() -> Rect2:
	return Rect2(440, 64, 400, 56)

func draw_title_mount(r: Rect2) -> void:
	PostKit.hemp(self, r)

## The time away, and the cap the coil holds (idle_cap_h and the sect's bonus, as the account authority caps it).
func _away() -> Array:
	var cap := float(ContentDB.curve("idle_cap_h", 12)) + float(Game.sect.idle_cap_bonus())
	return [float(args.get("hours", 0.0)), cap]

## The share of the coil burnt: the time away out of the cap.
func burnt() -> float:
	var away := _away()
	return clampf(float(away[0]) / maxf(0.01, float(away[1])), 0.0, 1.0)

## The goods [item, count] and the other lines [label, value] of the summary and the post's Return Ledger.
func ledger() -> Dictionary:
	var w: Dictionary = args.get("gains", {})
	var goods: Array = []
	var rows: Array = []
	if float(w.get("qp", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.realm_progress"), "+%s" % UiKit.fmt(float(w.qp))])
	if float(w.get("stored_qi", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.stored_qi"), "+%s" % UiKit.fmt(float(w.stored_qi))])
	if float(w.get("body_xp", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.body_training"), "+%s" % UiKit.fmt(float(w.body_xp))])
	if float(w.get("insight", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.insight"), "+%s" % UiKit.fmt(float(w.insight))])
	if float(w.get("halo", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.pill_halo"), "+%d%%" % int(round(float(w.halo) * 100.0))])
	if int(w.get("coins", 0)) > 0:
		var cur_key := "ui.welcome.spirit_stones" if str(w.get("coin_currency", "")) == "spirit_stone" else "ui.welcome.silver_taels"
		rows.append([Tx.t(cur_key), "+%s" % UiKit.fmt(int(w.coins))])
	for it in w.get("items", []): goods.append([str(it.get("item", it.get("id", ""))), int(it.get("count", 1))])
	# S50 Keeping Post: the Return Ledger of the post this character kept.
	var led: Dictionary = args.get("post", {})
	if not led.is_empty() and str(led.get("kind", "")) == "vigil":
		rows.append([Tx.t("ui.welcome.vigil_at") % str(ContentDB.room(str(led.get("room", ""))).get("name", "")),
			Tx.t("ui.welcome.post_hours") % [UiKit.span(float(led.get("hours", 0.0)) * 3600.0), int(round(float(led.get("diligence", 0.4)) * 100.0))]])
		rows.append([Tx.t("ui.welcome.vigil_kills"), "%s · %d%%" % [UiKit.fmt(int(led.get("kills", 0))), int(round(100.0 * float(led.get("alive", 1.0))))]])
		if int(led.get("food_used", 0)) > 0: rows.append([Tx.t("ui.welcome.vigil_food") % ContentDB.item_name(str(led.food)), "×%d" % int(led.food_used)])
		if float(led.get("qp", 0.0)) > 0.0: rows.append([Tx.t("ui.welcome.realm_progress"), "+%s" % UiKit.fmt(float(led.qp))])
		if int(led.get("coins", 0)) > 0: rows.append([Page.currency_name(str(led.coin_currency)), "+%s" % UiKit.fmt(int(led.coins))])
		for id in led.get("leaves", {}): rows.append([Tx.t("ui.welcome.leaf") % ContentDB.name_of("enemies", str(id)), "×%d" % int(led.leaves[id])])
	elif not led.is_empty():
		var craft := ContentDB.entry("posts", str(led.get("craft", "")))
		rows.append([Tx.t("ui.welcome.post_at") % [str(craft.get("short", "")), str(ContentDB.room(str(led.get("room", ""))).get("name", ""))],
			Tx.t("ui.welcome.post_hours") % [UiKit.span(float(led.get("hours", 0.0)) * 3600.0), int(round(float(led.get("diligence", 0.52)) * 100.0))]])
		var lv_txt := "+%s" % UiKit.fmt(int(float(led.get("exp", 0.0))))
		if int(led.get("level", 1)) > int(led.get("level_before", 1)): lv_txt += "  " + Tx.t("ui.welcome.level_up") % int(led.level)
		rows.append([Tx.t("ui.welcome.craft_exp") % str(craft.get("short", "")), lv_txt])
	for id in led.get("items", {}): goods.append([str(id), int(led.items[id])])
	for cat in led.get("full", {}):
		rows.append([Tx.t("ui.welcome.pouch_full") % Tx.t("ui.pouches.cat_" + str(cat)), Tx.t("ui.welcome.full_after") % UiKit.span(float(led.full[cat]) * 3600.0)])
	if rows.is_empty() and goods.is_empty(): rows.append([Tx.t("ui.welcome.nothing_gathered"), Tx.t("ui.welcome.set_seclusion_or_an_idle")])
	return {"goods": goods, "rows": rows}

func draw_page() -> void:
	var away := _away()
	var L := ledger()
	_coil(burnt() * unfold())
	var cx := COIL.x - 150.0
	text(Vector2(cx, 494), Tx.t("ui.welcome.you_were_away") % UiKit.span(float(away[0]) * 3600.0), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 300)
	text(Vector2(cx, 520), Tx.t("ui.welcome.coil_holds") % UiKit.span(float(away[1]) * 3600.0), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 300)
	if bool(args.get("capped", false)):
		para(Rect2(cx, 532, 300, 44), Tx.t("ui.welcome.time_limit_reached") + " · " + Tx.t("ui.welcome.extend_it_with_retreat_rooms"), 14, UiKit.WARNING, 2)
	_tray(L.goods)
	_slip(L.rows)
	var post: Dictionary = args.get("post", {})
	if not post.is_empty() and not (post.get("items", {}) as Dictionary).is_empty():
		btn(Rect2(TRAY.x - 240, 584, 232, 56), Tx.t("ui.welcome.to_storehouse"), "store", null, true)
		btn(Rect2(TRAY.x + 8, 584, 232, 56), Tx.t("ui.welcome.keep_in_pouch"), "ok")
	else:
		btn(Rect2(TRAY.x - 120, 584, 240, 56), Tx.t("ui.welcome.collect"), "ok", null, true)

## The incense coil on its bronze dish, burnt from its outer end inward: `burnt` of its length is ash, the tip glows.
func _coil(burnt: float) -> void:
	draw_circle(COIL, COIL_R.y + 22.0, UiKit.INK, true, -1.0, true)
	draw_circle(COIL, COIL_R.y + 18.0, UiKit.BRONZE.lerp(UiKit.INK, 0.35), true, -1.0, true)
	draw_arc(COIL, COIL_R.y + 12.0, 0.0, TAU, 64, Color(UiKit.GOLD, 0.35), 2.0, true)
	var n := 240
	var pts := PackedVector2Array()
	for i in n + 1:   # from the outer end inward
		var k := float(i) / float(n)
		var a := -PI * 0.5 + TURNS * TAU * (1.0 - k)
		pts.append(COIL + Vector2.from_angle(a) * lerpf(COIL_R.y, COIL_R.x, k))
	var cut := clampi(int(round(burnt * n)), 0, n)
	draw_polyline(pts, UiKit.INK, 13.0, true)
	if cut < n: draw_polyline(pts.slice(cut), UiKit.BRONZE, 9.0, true)
	if cut > 0: draw_polyline(pts.slice(0, cut + 1), UiKit.SURFACE.ash, 9.0, true)
	var tip: Vector2 = pts[cut]
	if cut > 0 and cut < n:
		glow(Rect2(tip - Vector2(28, 28), Vector2(56, 56)), Color(UiKit.SURFACE.ember, 0.9 if Game.account.settings.get("flashes", true) else 0.27))
		draw_circle(tip, 6.0, UiKit.SURFACE.ember, true, -1.0, true)
		draw_circle(tip, 3.0, UiKit.SURFACE.flame, true, -1.0, true)

## The round winnowing tray, woven and bound, with the haul heaped in it; a tap on a thing names it.
func _tray(goods: Array) -> void:
	draw_circle(TRAY + Vector2(0, 8), TRAY_R + 6.0, Color(UiKit.INK, 0.5), true, -1.0, true)
	draw_circle(TRAY, TRAY_R, UiKit.SURFACE.bamboo.lerp(UiKit.SURFACE.wood, 0.45), true, -1.0, true)
	for i in 16:
		var rr := TRAY_R - 14.0 - i * 11.5
		if rr < 8.0: break
		for j in 24:   # the weave: short strands over and under, turned a half step each ring
			var a0 := TAU * (float(j) + (0.5 if i % 2 else 0.0)) / 24.0
			draw_arc(TRAY, rr, a0, a0 + TAU / 48.0, 4, UiKit.SURFACE.bamboo if j % 2 else UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.25), 6.0, true)
	draw_arc(TRAY, TRAY_R - 6.0, 0.0, TAU, 96, UiKit.SURFACE.bamboo.lerp(UiKit.PAPER, 0.25), 12.0, true)
	for j in 36:   # the binding round the rim
		var p := TRAY + Vector2.from_angle(TAU * j / 36.0) * (TRAY_R - 6.0)
		draw_line(p - (p - TRAY).normalized() * 7.0, p + (p - TRAY).normalized() * 7.0, UiKit.SURFACE.wood, 3.0, true)
	var places: Array = []
	for ring in RINGS:
		for j in int(ring[1]): places.append(TRAY + Vector2.from_angle(-PI * 0.5 + TAU * (j + float(ring[2])) / float(ring[1])) * float(ring[0]))
	for i in mini(goods.size(), places.size()):
		var drop := 0.0
		if not UiKit.reduce_motion():   # goods drop into the tray one after another, 0.05 s apart
			drop = -24.0 * (1.0 - clampf((opened - 0.05 * i) / 0.2, 0.0, 1.0))
		draw_set_transform(Vector2(0, drop))
		slot_box(Rect2((places[i] as Vector2) - Vector2(SLOT, SLOT) * 0.5, Vector2(SLOT, SLOT)), str(goods[i][0]), int(goods[i][1]), "", "item", goods[i])
		draw_set_transform(Vector2.ZERO)
	if goods.size() > places.size():
		text(TRAY + Vector2(-100, TRAY_R + 24), Tx.t("ui.welcome.more_goods") % (goods.size() - places.size()), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 200)

## The rest of the ledger on a hemp slip beside the tray: a line each, the label over its value.
func _slip(rows: Array) -> void:
	if rows.is_empty(): return
	PostKit.hemp(self, SLIP)
	text(SLIP.position + Vector2(12, 28), Tx.t("ui.welcome.ledger"), 18, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, SLIP.size.x - 24)
	draw_rect(Rect2(SLIP.position + Vector2(8, 40), Vector2(SLIP.size.x - 16, 2)), Color(UiKit.BRONZE, 0.7))
	list("rows", Rect2(SLIP.position + Vector2(12, 48), SLIP.size - Vector2(20, 56)), rows.size(), 48, func(i: int, rr: Rect2):
		text(rr.position + Vector2(0, 16), str(rows[i][0]), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x)
		text(rr.position + Vector2(0, 38), str(rows[i][1]), 16, UiKit.JADE_SHADOW, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x)
	)

func on_action(id: String, data) -> void:
	match id:
		"store":
			submit({"type": "send_to_storehouse", "character": Game.active_id})
			close()
		"ok": close()
		"item": flash("%s ×%s" % [ContentDB.item_name(str(data[0])), UiKit.fmt(int(data[1]))])
