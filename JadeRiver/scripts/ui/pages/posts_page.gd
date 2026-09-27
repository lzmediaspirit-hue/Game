extends Page
## S50 Keeping Post (V10): the Roll-Call. Every character's post, rates and pouch; settle one or all into the
## Storehouse, burn Hour Incense at a post, switch to someone. Crafts: the active character's craft levels, Finesse
## and tools, and the Chance and Abundance bars of the node in reach. Storehouse: the account's bulk store.
## P5 (docs/page_identity.md row 14, mockups 13 and 13_first, decision 11): the sect's duty board. Each character is a
## wooden name tablet hung from the peg rail, their own figure in its window (standing while played, seated at rest),
## a band at its foot saying how the post stands; a tap turns the tablet over to show the post's numbers. Under each,
## on the shelf, the pouch as a woven vessel filled to its level with the goods themselves and a paper tag with the
## count, and under that one big Settle and a Switch. Settle all, the Storehouse cabinet and the Apprentice Bench stand
## at the right; Board, Crafts and Vows hang as tags on the beam, and the Storehouse's and the Bench's plaques open
## their full views. Soonest full first.

const Avatar = preload("res://scripts/avatar.gd")
const BEAM := Rect2(72, 40, 1136, 60)
const BOARD := Rect2(64, 32, 1152, 656)
const TABLET := Vector2(180, 252)
const TABLET_TOP := 132.0
const PITCH := 196.0
const SHOWN := 4
const WIN := Rect2(28, 22, 124, 110)   # the window, inside a tablet
const VESSEL_TOP := 416.0
const SHELF_Y := 528.0
const CAB := Rect2(868, 208, 344, 288)
const TURN_S := 0.25
## The figure in a window: 3 screen px an art px (the sheets are 2 px an art px), the feet below the window's foot.
const FIG_SCALE := 1.5
const FIG_FEET := Vector2(62, 140)
## The vessel a category's goods are kept in.
const VESSEL := {"fish": "creel", "insect": "cage", "critter": "cage", "wisp": "cage"}

var page_at := 0           # the first tablet shown, when more than SHOWN hang
var turned := {}           # character id -> true while its tablet shows its back
var turn_t := {}           # character id -> page time the tablet began to turn
var figs := {}             # character id -> {mask, doll}

func _init() -> void:
	title = Tx.t("ui.posts.title")
	tabs = [{"id": "roll", "label": Tx.t("ui.posts.tab_board")}, {"id": "crafts", "label": Tx.t("ui.posts.tab_crafts")},
		{"id": "store", "label": Tx.t("ui.posts.tab_store")}, {"id": "bench", "label": Tx.t("ui.posts.tab_bench")},
		{"id": "vows", "label": Tx.t("ui.posts.tab_vows")}]
	identity = Identity.new("wood_dark", false, "own", "tablets_rail_over_vessels", 0.3)

func setup() -> void:
	var ch = c()
	if ch != null and not Unlocks.is_unlocked(ch.id, "apprentice_bench"): tabs[3]["locked"] = Unlocks.locked_text("apprentice_bench")
	var want := str(args.get("tab", ""))
	for i in tabs.size():
		if str(tabs[i].id) == want: tab = i

## The board's left, under the rail: where the tablets hang, or the tab's own view.
func content_rect() -> Rect2:
	return Rect2(80, 112, 776, 568)

# ------------------------------------------------------------------ the board
func draw_surface(_r: Rect2) -> void:
	PostKit.planks(self, BOARD)
	ground(BOARD, UiKit.SURFACE.wood_dark)
	rounded(BEAM, 4.0, UiKit.SURFACE.peg_dark)
	rounded(BEAM.grow(-2), 3.0, UiKit.SURFACE.wood)
	draw_rect(Rect2(BEAM.position.x + 2, BEAM.end.y - 6, BEAM.size.x - 4, 4), Color(UiKit.INK, 0.45))
	# The Storehouse: a cabinet of drawers under a tiled roof (its plaque is the Storehouse tab).
	var roof := PackedVector2Array([Vector2(CAB.position.x + 20, 184), Vector2(CAB.end.x - 20, 184), Vector2(CAB.end.x + 10, CAB.position.y + 6), Vector2(CAB.position.x - 10, CAB.position.y + 6)])
	draw_colored_polygon(roof, UiKit.SURFACE.cloth)
	for x in range(int(CAB.position.x) - 6, int(CAB.end.x) + 8, 16): draw_line(Vector2(x, 186), Vector2(x, CAB.position.y + 4), Color(UiKit.INK, 0.5), 2.0)
	rounded(Rect2(CAB.position.x + 26, 178, CAB.size.x - 52, 8), 4.0, UiKit.SURFACE.silk)
	rounded(CAB, 4.0, UiKit.SURFACE.peg_dark)
	rounded(CAB.grow(-3), 3.0, UiKit.SURFACE.wood)
	ground(CAB, UiKit.SURFACE.wood)
	# The Bench: a work table (its plaque is the Bench tab).
	draw_rect(Rect2(CAB.position.x, CAB.end.y + 124, CAB.size.x, 8), UiKit.SURFACE.wood)
	draw_rect(Rect2(CAB.position.x, CAB.end.y + 124, CAB.size.x, 3), UiKit.SURFACE.peg)

func title_rect() -> Rect2:
	return Rect2(440, 34, 400, 72)

## The title cut into a gilt cartouche on the beam.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(6), 22.0, UiKit.GOLD.lerp(UiKit.INK, 0.4))
	rounded(r.grow(4), 20.0, UiKit.GOLD)
	rounded(r, 18.0, UiKit.SURFACE.peg_dark.lerp(UiKit.SURFACE.wood_dark, 0.5))

## Board, Crafts and Vows are tags on the beam; the Storehouse and the Bench are their plaques at the right.
func tab_rects() -> Array:
	var out: Array = []
	var x := 88.0
	for tb in tabs:
		match str(tb.id):
			"store": out.append(Rect2(CAB.position.x + 12, CAB.position.y + 12, 196, 48))
			"bench": out.append(Rect2(CAB.position.x + 12, CAB.end.y + 12, 156, 48))
			_:
				var w := UiKit.text_width(str(tb.label), 18) + 32
				out.append(Rect2(x, 46, w, 48))
				x += w + 8
	return out

func draw_tab(r: Rect2, i: int, state: String) -> void:
	var sel := state == "selected"
	rounded(r.grow(2), 6.0, UiKit.PALE_GOLD if sel else UiKit.SURFACE.peg_dark)
	rounded(r, 5.0, UiKit.SURFACE.peg_dark if str(tabs[i].id) in ["store", "bench"] else UiKit.SURFACE.wood)
	ground(r, UiKit.SURFACE.wood)
	var col := UiKit.PALE_GOLD if sel else (UiKit.HOLLOW if state == "disabled" else UiKit.PAPER)
	var big := str(tabs[i].id) in ["store", "bench"]
	text(r.position + Vector2(0, 31), str(tabs[i].label), 20 if big else 18, col, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

func draw_page() -> void:
	_draw_right()
	match str(tabs[tab].id):
		"roll": _draw_roll()
		"crafts": _draw_crafts()
		"store": _draw_store()
		"bench": _draw_bench()
		"vows": _draw_vows()

func _process(delta: float) -> void:
	super._process(delta)
	_place_figures()

# ------------------------------------------------------------------ Roll-Call: the tablets
## The rows, soonest full first: the one you play, then those full (longest idle first), filling, and without a post.
func rows() -> Array:
	if _rows_frame == Engine.get_process_frames() and not _rows.is_empty(): return _rows
	var rs: Array = Game.posts.roll_call()
	var key := func(r: Dictionary) -> float:
		if r.active: return -1e12
		if (r.post as Dictionary).is_empty(): return 1e12
		return float(r.fill_h) * 1000.0 - float(r.since_h) if float(r.fill_h) < INF else 1e11
	rs.sort_custom(func(a, b): return key.call(a) < key.call(b))
	_rows = rs
	_rows_frame = Engine.get_process_frames()
	return rs

var _rows: Array = []
var _rows_frame := -1

## A row's state: "play", "full", "fill", "vigil" or "none".
static func state_of(row: Dictionary) -> String:
	if row.active: return "play"
	if (row.post as Dictionary).is_empty(): return "none"
	if str(row.post.get("kind", "")) == "vigil": return "vigil"
	return "full" if float(row.fill_h) <= 0.0 else "fill"

## What a row's pouch holds against what it can: [held, capacity] over the categories its post fills.
static func fill_of(row: Dictionary) -> Array:
	return [float(row.pouch), float(row.get("cap", 0.0))]

func _tablet_rect(i: int) -> Rect2:
	var drop := (1.0 - unfold()) * -28.0   # the tablets swing down onto their pegs as the board opens
	return Rect2(88 + PITCH * i, TABLET_TOP + drop, TABLET.x, TABLET.y)

func _draw_roll() -> void:
	var rs := rows()
	page_at = clampi(page_at, 0, maxi(0, rs.size() - 1) / SHOWN * SHOWN)
	draw_rect(Rect2(80, 112, 776, 8), UiKit.SURFACE.wood)
	draw_rect(Rect2(80, 118, 776, 3), Color(UiKit.INK, 0.5))
	draw_rect(Rect2(76, SHELF_Y, 784, 16), UiKit.SURFACE.wood)
	draw_rect(Rect2(76, SHELF_Y, 784, 4), UiKit.SURFACE.peg)
	draw_rect(Rect2(76, SHELF_Y + 16, 784, 5), Color(UiKit.INK, 0.4))
	var shown := rs.slice(page_at, page_at + SHOWN)
	# A new player's board (Keeping Post not yet done, few on the rail) teaches the loop in a pinned note.
	var first: bool = rs.size() <= 2 and c() != null and not (c().quests.done as Dictionary).has("keeping_post")
	for i in SHOWN:
		var cx := 88 + PITCH * i + TABLET.x * 0.5
		draw_circle(Vector2(cx, 116), 9.0, UiKit.SURFACE.peg, true, -1.0, true)
		draw_circle(Vector2(cx - 2, 113), 3.0, UiKit.PALE_GOLD, true, -1.0, true)
		if i < shown.size(): _column(shown[i], i)
		elif i == shown.size() and first: _first_note(i)
		elif i >= shown.size() and not first: _empty_peg(i)
	if rs.size() > SHOWN:
		btn(Rect2(80, 624, 48, 48), "‹", "page", -SHOWN, false, page_at > 0, "", 22)
		btn(Rect2(136, 624, 48, 48), "›", "page", SHOWN, false, page_at + SHOWN < rs.size(), "", 22)
	var ch = c()
	var here := str(Game.room_rt.room_id) if Game.room_rt != null else ""
	if ch != null and here != "" and Game.posts.vigil_allowed(here):
		btn(Rect2(616, 624, 240, 48), Tx.t("ui.posts.keep_vigil"), "vigil", null, false, Unlocks.is_unlocked(ch.id, "keeping_post"), Unlocks.locked_text("keeping_post"), 18)
	text(Vector2(196 if rs.size() > SHOWN else 84, 664), Tx.t("ui.posts.board_hint"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 408)

## One character's column: the tablet on its cord, the vessel on the shelf, the actions under it.
func _column(row: Dictionary, i: int) -> void:
	var r := _tablet_rect(i)
	var cx := r.get_center().x
	var st := state_of(row)
	draw_line(Vector2(cx, 118), Vector2(cx, r.position.y + 14), UiKit.BLOOD, 3.0, true)
	var id := str(row.id)
	var k := clampf((t - float(turn_t.get(id, -9.0))) / TURN_S, 0.0, 1.0)
	var back: bool = turned.get(id, false)
	if k < 1.0 and not UiKit.reduce_motion():
		# The tablet turns over on its cord: it narrows to its edge and opens on the other face.
		var sx := absf(cos(k * PI))
		if k < 0.5: back = not back
		draw_set_transform(Vector2(cx * (1.0 - sx), 0), 0.0, Vector2(maxf(0.02, sx), 1.0))
	if back: _back(row, r)
	else: _front(row, r, st)
	draw_set_transform(Vector2.ZERO)
	region(r, "turn", id)
	if not back: _vessel_row(row, cx, st)
	var tassel := {"play": UiKit.GOLD, "full": UiKit.BLOOD, "fill": UiKit.JADE}.get(st, UiKit.HOLLOW) as Color
	draw_rect(Rect2(cx - 5, r.end.y + 2, 10, 20), tassel)
	draw_rect(Rect2(cx - 5, r.end.y + 2, 10, 4), tassel.lightened(0.3))
	_actions(row, cx, st)

## The tablet's face: its window with the figure, the name, the craft, the place and the band.
func _front(row: Dictionary, r: Rect2, st: String) -> void:
	var body := PostKit.arch(r, 34.0)
	draw_colored_polygon(body, UiKit.SURFACE.bridge)
	for x in range(int(r.position.x) + 8, int(r.end.x) - 4, 12): draw_line(Vector2(x, r.position.y + 30), Vector2(x, r.end.y - 4), Color(UiKit.SURFACE.board_line, 0.08), 1.0)
	draw_polyline(body + PackedVector2Array([body[0]]), UiKit.SURFACE.talisman_edge, 3.0, true)
	ground(r, UiKit.SURFACE.bridge)
	draw_circle(Vector2(r.get_center().x, r.position.y + 12), 5.0, UiKit.SURFACE.peg_dark, true, -1.0, true)
	var turn := r.position + Vector2(r.size.x - 18, 40)   # the sign that it turns
	draw_arc(turn, 8.0, -PI * 0.2, PI * 1.4, 12, Color(UiKit.PAPER_INK, 0.6), 2.5, true)
	draw_colored_polygon(PackedVector2Array([turn + Vector2(6, -8), turn + Vector2(10, -1), turn + Vector2(2, -2)]), Color(UiKit.PAPER_INK, 0.6))
	var w := Rect2(r.position + WIN.position, WIN.size)
	var win := PostKit.arch(w, 58.0)
	draw_colored_polygon(win, _sky(row, st))
	var ground_col := _land(row)
	if st == "play": glow(w.grow(-8), Color(UiKit.PALE_GOLD, 0.9))
	else: draw_rect(Rect2(w.position.x + 2, w.end.y - 30, w.size.x - 4, 28), ground_col)
	draw_polyline(win + PackedVector2Array([win[0]]), UiKit.SURFACE.talisman_edge, 3.0, true)
	var x := r.position.x
	text(Vector2(x, r.position.y + 156), str(row.name), 20, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	var p: Dictionary = row.post
	var line := Tx.t("ui.posts.no_post_short") if st == "play" else ""
	var icon := ""
	if str(p.get("kind", "")) == "vigil":
		line = Tx.t("ui.posts.vigil_short")
		icon = "post"
	elif not p.is_empty():
		var craft := ContentDB.entry("posts", str(p.get("craft", "")))
		line = "%s %d" % [str(craft.get("short", craft.get("name", ""))), int(row.rates.get("level", 1))]
		icon = str(craft.get("icon", ""))
	var lw := UiKit.text_width(line, 16) + (40.0 if icon != "" else 0.0)
	var lx := r.get_center().x - lw * 0.5
	if icon != "":
		draw_circle(Vector2(lx + 16, r.position.y + 176), 17.0, UiKit.SURFACE.cloth, true, -1.0, true)
		draw_arc(Vector2(lx + 16, r.position.y + 176), 17.0, 0.0, TAU, 24, UiKit.SURFACE.talisman_edge, 2.0, true)
		icon_at(Rect2(lx, r.position.y + 160, 32, 32), icon)
	text(Vector2(lx + (40.0 if icon != "" else 0.0), r.position.y + 182), line, 16, UiKit.JADE_SHADOW if icon != "" else UiKit.PAPER_INK)
	var room := str(p.get("room", "")) if not p.is_empty() else str(Game.character(str(row.id)).position.get("room", ""))
	text(Vector2(x + 6, r.position.y + 206), str(ContentDB.room(room).get("name", "")), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, r.size.x - 12)
	var band := Rect2(x + 6, r.end.y - 40, r.size.x - 12, 34)
	var bc: Color = {"play": UiKit.GOLD, "full": UiKit.BLOOD, "fill": UiKit.JADE_SHADOW, "vigil": UiKit.SURFACE.lacquer}.get(st, UiKit.SURFACE.stone)
	rounded(band, 4.0, bc)
	ground(band, bc)
	text(Vector2(band.position.x, band.position.y + 24), _band_text(row, st), 16, UiKit.PAPER_INK if st == "play" else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, band.size.x)

## What the band says: playing, full and how long idle, full in how long, on vigil, or no post.
func _band_text(row: Dictionary, st: String) -> String:
	match st:
		"play": return "▶ " + Tx.t("ui.posts.playing_now")
		"full": return Tx.t("ui.posts.band_full") % UiKit.span(float(row.get("idle_h", 0.0)) * 3600.0)
		"fill": return Tx.t("ui.posts.full_in") % UiKit.span(float(row.fill_h) * 3600.0) if float(row.fill_h) < INF else Tx.t("ui.posts.band_working")
		"vigil": return Tx.t("ui.posts.band_vigil") % UiKit.span(float(row.since_h) * 3600.0)
	return Tx.t("ui.posts.band_none")

## The window's sky: lamp-lit for the one you play, else the day over the post's ground.
func _sky(row: Dictionary, st: String) -> Color:
	if st == "play": return UiKit.GOLD.lerp(UiKit.SURFACE.bridge, 0.4)
	return UiKit.MIST.lerp(UiKit.PAPER, 0.35)

func _land(row: Dictionary) -> Color:
	match _cat(row):
		"fish": return UiKit.SURFACE.water
		"ore": return UiKit.SURFACE.stone
		"": return UiKit.SURFACE.bridge.lerp(UiKit.BRONZE, 0.4)
	return UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.35)

## The first category a row's post fills ("" without one).
func _cat(row: Dictionary) -> String:
	var goods := _goods(row)
	return Game.posts.category_of(str(goods[0])) if not goods.is_empty() else ""

## The tablet's back: what the post yields, its chance, the incense to burn.
func _back(row: Dictionary, r: Rect2) -> void:
	var body := PostKit.arch(r, 34.0)
	draw_colored_polygon(body, UiKit.SURFACE.wood)
	draw_polyline(body + PackedVector2Array([body[0]]), Color(UiKit.GOLD, 0.6), 3.0, true)
	ground(r, UiKit.SURFACE.wood)
	var x := r.position.x + 14
	var w := r.size.x - 28
	text(Vector2(r.position.x, r.position.y + 44), str(row.name), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	var rt: Dictionary = row.rates
	var p: Dictionary = row.post
	if p.is_empty():
		para(Rect2(x, r.position.y + 64, w, 120), Tx.t("ui.posts.no_post"), 16, UiKit.PAPER)
		return
	var y := r.position.y + 58
	if str(p.get("kind", "")) == "vigil":
		text(Vector2(x, y + 18), Tx.t("ui.posts.kills_h") % UiKit.fmt(int(float(rt.get("kills_h", 0.0)))), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, w)
		if int(rt.get("sweep", 0)) > 0: text(Vector2(x, y + 42), Tx.t("ui.posts.sweep") % int(rt.sweep), 16, UiKit.PALE_GOLD)
		text(Vector2(x, y + 66), Tx.t("ui.posts.in_pouch") % UiKit.fmt(int(row.pouch)), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, w)
	else:
		text(Vector2(x, y + 16), Tx.t("ui.posts.level_short") % int(rt.get("level", 1)) + " · " + Tx.t("ui.posts.finesse_short") % UiKit.fmt(int(float(rt.get("finesse", 0.0)))), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, w)
		var k := 0
		for id in rt.get("items", {}):
			if k >= 2: break
			icon_at(Rect2(x, y + 26 + k * 36, 32, 32), str(id))
			text(Vector2(x + 38, y + 48 + k * 36), Tx.t("ui.posts.per_hour") % UiKit.fmt(snappedf(float(rt.items[id]), 0.1)), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, w - 38)
			k += 1
		var first := ""
		for id in rt.get("items", {}):
			first = str(id)
			break
		var nd := Game.posts.node_def(first)
		if not nd.is_empty():
			var yv := PostRules.yield_of(float(rt.get("finesse", 0.0)), float(nd.get("toughness", 1.0)))
			if float(yv.chance) < 1.0: bar(Rect2(x, y + 104, w, 24), float(yv.chance), UiKit.BRIGHT_JADE, Tx.t("ui.posts.chance") % int(round(float(yv.chance) * 100.0)))
			else: bar(Rect2(x, y + 104, w, 24), float(yv.abundance_progress), UiKit.GOLD, Tx.t("ui.posts.abundance") % int(yv.abundance))
	if not row.active:
		var inc := _incense()
		btn(Rect2(x, r.end.y - 58, w, 48), Tx.t("ui.posts.incense"), "incense", str(row.id), false, inc != "", Tx.t("ui.posts.no_incense"), 18)

## The vessel on the shelf under a tablet, filled to its level, and its paper tag.
func _vessel_row(row: Dictionary, cx: float, st: String) -> void:
	var v := Rect2(cx - 64, VESSEL_TOP, 128, 112)
	if st == "none" or (row.post as Dictionary).is_empty():
		var ghost := PostKit.arch(Rect2(v.position.x + 6, v.position.y + 20, 116, 92), 0.0, 2)
		PostKit.dashed(self, ghost + PackedVector2Array([ghost[0]]), Color(UiKit.SURFACE.bridge, 0.45), 6.0)
		icon_at(Rect2(cx - 16, v.position.y + 48, 32, 32), "post")
		return
	if st == "vigil": return
	var f := fill_of(row)
	var frac := clampf(float(f[0]) / maxf(1.0, float(f[1])), 0.0, 1.0)
	var goods := _goods(row)
	var kind := str(VESSEL.get(_cat(row), "basket"))
	if st == "full": glow(Rect2(v.position - Vector2(32, 24), v.size + Vector2(64, 40)), Color(UiKit.PALE_GOLD, 0.45))
	_vessel(kind, v, frac, goods, st == "play")
	var full := st == "full"
	PostKit.tag(self, Vector2(cx + 2, VESSEL_TOP + 70), UiKit.fmt(int(f[0])), Tx.t("ui.posts.tag_full") if full else "/" + UiKit.fmt(int(f[1])), full)
	if poured.has(str(row.id)) and not UiKit.reduce_motion():   # the catch lifting out toward the Storehouse
		var k := (t - float(poured[str(row.id)][0])) / 0.4
		if k < 1.0: UiKit.draw_outlined(self, "+" + UiKit.fmt(int(poured[str(row.id)][1])), Vector2(cx - 20, VESSEL_TOP - 10 - 30 * k), 22, UiKit.BRIGHT_JADE)

var poured := {}   # character id -> [page time, count] of the last settle

## A woven vessel: a basket (herbs, ores, materials), a creel (fish) or a cage (insects, critters, wisps), the goods
## heaped inside to `frac` of its height and showing through the weave; the lid and a pause mark while you play.
func _vessel(kind: String, v: Rect2, frac: float, goods: Array, paused: bool) -> void:
	var inner := Rect2(v.position.x + 12, v.position.y + 28, v.size.x - 24, v.size.y - 32)
	var dark := UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.4)
	match kind:
		"creel":
			draw_colored_polygon(_ellipse(v.get_center() + Vector2(0, 14), Vector2(62, 44)), dark)
			draw_arc(v.get_center() + Vector2(0, 10), 64.0, PI * 1.05, PI * 1.95, 24, UiKit.BLOOD, 4.0, true)
		"cage": draw_colored_polygon(PostKit.arch(inner.grow_individual(4, 8, 4, 4), 36.0), Color(UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.6), 0.9))
		_: draw_colored_polygon(PackedVector2Array([v.position + Vector2(0, 28), v.position + Vector2(v.size.x, 28), v.end - Vector2(14, 0), Vector2(v.position.x + 14, v.end.y)]), dark)
	# The goods, heaped from the floor up to the level.
	if not goods.is_empty():
		var rows_n := int(ceil(frac * 4.0))
		for ry in rows_n:
			for cx in 4:
				var gid := str(goods[(ry + cx) % goods.size()])
				var gx := inner.position.x + 2 + cx * 22 + (ry % 2) * 8
				var gy := inner.end.y - 34 - ry * 20
				icon_at(Rect2(gx, gy, 32, 32), gid)
	var cane := UiKit.SURFACE.board_edge
	match kind:
		"creel":
			for i in 9:
				var a := v.position + Vector2(-8 + i * 18, 30)
				draw_line(a, a + Vector2(40, 80), Color(cane, 0.85), 3.0, true)
				draw_line(a + Vector2(40, 0), a + Vector2(0, 80), Color(UiKit.SURFACE.peg, 0.85), 3.0, true)
			draw_rect(Rect2(v.get_center().x - 28, v.position.y + 14, 56, 18), UiKit.SURFACE.peg)
			rounded(Rect2(v.get_center().x - 34, v.position.y + 10, 68, 8), 4.0, UiKit.SURFACE.board)
		"cage":
			for i in 10:
				var bx := inner.position.x + 2 + i * 10.5
				draw_line(Vector2(bx, inner.position.y + (26.0 - 20.0 * sin(PI * i / 9.0))), Vector2(bx, v.end.y - 6), cane, 3.0)
			draw_arc(Vector2(v.get_center().x, inner.position.y + 44), 54.0, PI * 1.08, PI * 1.92, 20, cane, 4.0, true)
			rounded(Rect2(v.position.x, v.end.y - 10, v.size.x, 10), 3.0, UiKit.SURFACE.wood)
			draw_circle(Vector2(v.get_center().x, v.position.y + 10), 7.0, UiKit.SURFACE.peg, true, -1.0, true)
		_:
			PostKit.weave(self, Rect2(v.position.x + 4, v.position.y + 34, v.size.x - 8, v.size.y - 36), cane, 17.0)
			rounded(Rect2(v.position.x - 4, v.position.y + 22, v.size.x + 8, 12), 6.0, UiKit.SURFACE.board)
			draw_rect(Rect2(v.position.x + 14, v.end.y - 6, v.size.x - 28, 6), UiKit.SURFACE.wood)
	if paused:
		draw_colored_polygon(_ellipse(Vector2(v.get_center().x, v.position.y + 22), Vector2(72, 12)), UiKit.SURFACE.board.lerp(UiKit.SURFACE.wood, 0.4))
		var pc := Vector2(v.get_center().x - 20, v.position.y + 70)
		draw_circle(pc, 18.0, Color(UiKit.SURFACE.peg_dark, 0.9), true, -1.0, true)
		draw_rect(Rect2(pc + Vector2(-7, -8), Vector2(5, 16)), UiKit.PAPER)
		draw_rect(Rect2(pc + Vector2(2, -8), Vector2(5, 16)), UiKit.PAPER)

## What a post brings in, the most first.
func _goods(row: Dictionary) -> Array:
	var items: Dictionary = row.rates.get("items", {})
	var ids := items.keys()
	ids.sort_custom(func(a, b): return float(items[a]) > float(items[b]))
	return ids

func _ellipse(c0: Vector2, r: Vector2) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in 28: pts.append(c0 + Vector2(cos(TAU * i / 28.0) * r.x, sin(TAU * i / 28.0) * r.y))
	return pts

## Under the vessel: one big Settle and the Switch figure, or a word for the one you play.
func _actions(row: Dictionary, cx: float, st: String) -> void:
	if st == "play":
		para(Rect2(cx - 90, 566, 180, 48), Tx.t("ui.posts.paused_play") if not (row.post as Dictionary).is_empty() else Tx.t("ui.posts.first_basket"), 16, UiKit.MIST, 2)
		return
	var goods := _goods(row)
	if st == "none":
		btn(Rect2(cx - 28, 560, 56, 56), "", "switch", int(row.slot), false, true, "", 18)
		icon_at(Rect2(cx - 16, 572, 32, 32), "characters")
		return
	var label := Tx.t("ui.posts.settle") if st == "full" or int(row.pouch) <= 0 else Tx.t("ui.posts.settle_n") % UiKit.fmt(int(row.pouch))
	btn(Rect2(cx - 90, 560, 116, 56), label, "settle", str(row.id), st == "full", true, "", 20)
	btn(Rect2(cx + 34, 560, 56, 56), "", "switch", int(row.slot), false, true, "", 18)
	icon_at(Rect2(cx + 46, 572, 32, 32), "characters")
	if st == "fill" and not goods.is_empty() and float(row.rates.items[goods[0]]) > 0.0:
		text(Vector2(cx - 90, 638), Tx.t("ui.posts.per_hour_of") % [UiKit.fmt(snappedf(float(row.rates.items[goods[0]]), 0.1)), ContentDB.item_name(str(goods[0]))], 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 180)

## A peg with no one on it yet: the tablet's outline, dashed.
func _empty_peg(i: int) -> void:
	var r := _tablet_rect(i)
	var pts := PostKit.arch(r, 34.0)
	PostKit.dashed(self, pts + PackedVector2Array([pts[0]]), Color(UiKit.SURFACE.bridge, 0.35), 10.0)

## A new player's board: a note pinned where more tablets will hang, teaching the loop in three steps.
func _first_note(i: int) -> void:
	var r := Rect2(88 + PITCH * i, 128, PITCH * (SHOWN - i) - 16, 400)
	draw_rect(r.grow(2), Color(UiKit.INK, 0.4))
	draw_rect(r, UiKit.SURFACE.talisman)
	ground(r, UiKit.SURFACE.talisman)
	draw_circle(Vector2(r.get_center().x, r.position.y + 14), 6.0, UiKit.HOLLOW, true, -1.0, true)
	var x := r.position.x + 24
	UiKit.draw_text(self, Tx.t("ui.posts.first_title"), Vector2(x, r.position.y + 58), 26, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true, true)
	if text_log != null: _log_text(Vector2(x, r.position.y + 58), Tx.t("ui.posts.first_title"), 26, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true, Rect2(), UiKit.PAPER_INK)
	para(Rect2(x, r.position.y + 70, r.size.x - 48, 44), Tx.t("ui.posts.first_sub"), 16, UiKit.PAPER_INK, 2)
	for s in 3:
		var y := r.position.y + 132 + s * 84
		draw_circle(Vector2(x + 24, y + 24), 24.0, UiKit.SURFACE.cloth, true, -1.0, true)
		draw_arc(Vector2(x + 24, y + 24), 24.0, 0.0, TAU, 32, UiKit.SURFACE.talisman_edge, 3.0, true)
		icon_at(Rect2(x + 8, y + 8, 32, 32), ["post", "characters", "storehouse"][s])
		draw_circle(Vector2(x + 4, y + 4), 11.0, UiKit.BLOOD, true, -1.0, true)
		text(Vector2(x - 7, y + 9), str(s + 1), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 22)
		text(Vector2(x + 62, y + 20), Tx.t("ui.posts.first_step%d" % (s + 1)), 18, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 100)
		text(Vector2(x + 62, y + 42), Tx.t("ui.posts.first_step%d_sub" % (s + 1)), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 100)

## The figures in the tablets' windows: the live Avatar of each character shown, clipped to its window's arch and
## turned with its tablet, standing while played and seated at rest (the registered idle and meditate poses).
class Mask extends Node2D:
	var poly := PackedVector2Array()
	func _draw() -> void:
		if poly.size() > 2: draw_colored_polygon(poly, Color.WHITE)

func _place_figures() -> void:
	var live := {}
	if str(tabs[tab].id) == "roll" and confirm.is_empty():
		var rs := rows()
		for i in mini(SHOWN, rs.size() - page_at):
			var row: Dictionary = rs[page_at + i]
			var id := str(row.id)
			var k := clampf((t - float(turn_t.get(id, -9.0))) / TURN_S, 0.0, 1.0)
			var back: bool = turned.get(id, false)
			var sx := 1.0
			if k < 1.0 and not UiKit.reduce_motion():
				sx = absf(cos(k * PI))
				if k < 0.5: back = not back
			if back: continue
			live[id] = true
			if not figs.has(id): figs[id] = _figure(id)
			var r := _tablet_rect(i)
			var f: Dictionary = figs[id]
			var m: Mask = f.mask
			m.visible = true
			m.position = Vector2(r.get_center().x, r.position.y).round()
			m.scale = Vector2(maxf(0.02, sx), 1.0)
			m.poly = PostKit.arch(Rect2(WIN.position + Vector2(-TABLET.x * 0.5, 0) + Vector2(3, 3), WIN.size - Vector2(6, 5)), 55.0)
			var d: Node2D = f.doll
			d.position = WIN.position + Vector2(-TABLET.x * 0.5, 0) + FIG_FEET
			d.play("idle" if state_of(row) in ["play", "fill"] else "meditate")
			m.queue_redraw()
	for id in figs:
		if not live.has(id): (figs[id].mask as Node2D).visible = false

func _figure(id: String) -> Dictionary:
	var m := Mask.new()
	m.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	add_child(m)
	var d := Avatar.new()
	d.outfit = InventoryAuthority.outfit_for(Game.character(id))
	d.scale = Vector2.ONE * FIG_SCALE
	m.add_child(d)
	return {"mask": m, "doll": d}

## The shortest Hour Incense the active character carries ("" when none).
func _incense() -> String:
	var ch = c()
	if ch == null: return ""
	for id in ["hour_incense_1", "hour_incense_2", "hour_incense_4", "hour_incense_12", "hour_incense_24", "hour_incense_72", "wandering_incense"]:
		if ch.inventory.count(id) > 0: return id
	return ""

# ------------------------------------------------------------------ the right: Settle all, the Storehouse, the Bench
func _draw_right() -> void:
	var ch = c()
	var rs := rows()
	var goods := 0
	var ready := false
	for row in rs:
		if row.active or (row.post as Dictionary).is_empty(): continue
		goods += int(row.pouch)
		ready = ready or state_of(row) == "full"
	btn(Rect2(CAB.position.x, 112, CAB.size.x, 64), Tx.t("ui.posts.settle_all_n") % UiKit.fmt(goods), "settle_all", null, true, true, "", 22)
	if ready: PostKit.ready_seal(self, Vector2(CAB.end.x - 8, 112))
	text(Vector2(CAB.end.x - 132, CAB.position.y + 42), Tx.t("ui.posts.take_50"), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 120)
	var ids: Array = Game.account.storehouse.keys()
	ids.sort_custom(func(a, b): return int(Game.account.storehouse[a]) > int(Game.account.storehouse[b]))
	for i in 8:
		var sr := Rect2(CAB.position.x + 12 + (i % 4) * 82, CAB.position.y + 68 + (i / 4) * 82, SLOT, SLOT)
		if i < ids.size():
			slot_box(sr, str(ids[i]), 0, "", "withdraw", str(ids[i]))
			UiKit.draw_outlined(self, UiKit.fmt(int(Game.account.storehouse[ids[i]])), sr.end - Vector2(sr.size.x, 5), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, sr.size.x - 5)
		else:
			slot_box(sr, "")
			draw_arc(sr.get_center() + Vector2(0, 4), 12.0, PI, TAU, 10, Color(UiKit.JADE, 0.35), 2.0, true)
	if ids.is_empty(): text(Vector2(CAB.position.x + 12, CAB.end.y - 20), Tx.t("ui.posts.store_empty"), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, CAB.size.x - 24)
	elif ch != null and Unlocks.is_unlocked(ch.id, "seal_scripts"):
		var auto := bool(Game.posts.works().get("auto_settle", false))
		btn(Rect2(CAB.position.x + 12, CAB.end.y - 60, CAB.size.x - 24, 48), Tx.t("ui.posts.auto_settle_on") if auto else Tx.t("ui.posts.auto_settle_off"),
			"option", ["auto_settle", not auto], auto, true, "", 18)
	# The Bench: a work table with what the apprentices made.
	var by := CAB.end.y + 12
	if ch == null: return
	if not Unlocks.is_unlocked(ch.id, "apprentice_bench"):
		para(Rect2(CAB.position.x + 12, by + 60, CAB.size.x - 24, 60), Unlocks.locked_text("apprentice_bench"), 16, UiKit.PAPER, 3)
		return
	var free: int = Game.posts.bench_points_free(ch)
	if free > 0: text(Vector2(CAB.position.x + 180, by + 32), Tx.plural("ui.posts.points_to_spend", free) % free, 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, 150)
	var b: Dictionary = Game.posts.bench(ch)
	var cur := str(b.slots[0]) if not (b.slots as Array).is_empty() else ""
	if cur != "":
		icon_at(Rect2(CAB.position.x + 8, by + 52, 64, 64), cur)
		var made := int(float(b.stock.get(cur, 0.0)))
		var cap := int(Game.posts.bench_capacity(ch))
		PostKit.tag(self, Vector2(CAB.position.x + 76, by + 66), UiKit.fmt(made), "/" + UiKit.fmt(cap), made >= cap)
	else:
		text(Vector2(CAB.position.x + 12, by + 90), Tx.t("ui.posts.bench_idle"), 18, UiKit.PAPER)
	btn(Rect2(CAB.end.x - 132, by + 56, 128, 52), Tx.t("ui.posts.bench_collect"), "bench_collect", null, true, true, "", 20)
	var lv: int = Game.posts.total_craft_levels(ch)
	var next_pt := (lv / 5 + 1) * 5
	var next_app := 60 if lv < 60 else 150
	bar(Rect2(CAB.position.x + 24, by + 124, CAB.size.x - 48, 22), float(lv) / float(next_app), UiKit.JADE, Tx.t("ui.posts.craft_levels") % lv)
	text(Vector2(CAB.position.x, by + 164), Tx.t("ui.posts.bench_next") % [next_pt, next_app], 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, CAB.size.x)

# ------------------------------------------------------------------ Crafts
func _draw_crafts() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position, Vector2(420, content.size.y))
	var list_crafts: Array = Game.posts.crafts()
	var step := minf(96.0, (left.size.y + 6.0) / maxf(1.0, float(list_crafts.size())))
	var y := left.position.y
	for cd in list_crafts:
		var craft := str(cd.id)
		var r := Rect2(left.position.x, y, left.size.x, step - 6.0)
		panel(r)
		icon_at(Rect2(r.position + Vector2(10, 8), Vector2(32, 32)), str(cd.get("icon", "")))
		var known: bool = Game.posts.craft_known(ch, craft)
		text(r.position + Vector2(52, 28), str(cd.name), 18, UiKit.PAPER if known else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 130)
		if not known:
			text(r.position + Vector2(52, 52), Unlocks.locked_text(str(cd.get("unlock", craft))), 14, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 64)
			y += step
			continue
		var info := PostRules.level_info(Game.posts.xp(ch, craft))
		text(Vector2(r.end.x - 90, r.position.y + 28), Tx.t("ui.posts.level_short") % int(info.level), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 76)
		bar(Rect2(r.position + Vector2(52, 36), Vector2(r.size.x - 66, 22)), float(info.into) / maxf(1.0, float(info.need)), UiKit.JADE,
			"%s / %s" % [UiKit.fmt(int(info.into)), UiKit.fmt(int(info.need))])
		var tool: Dictionary = Game.posts.tool_of(ch, craft)
		var tool_name := ContentDB.item_name(str(tool.item)) if not tool.is_empty() else Tx.t("ui.posts.bare_hands")
		var line := Tx.t("ui.posts.finesse_line") % [UiKit.fmt(int(Game.posts.finesse_of(ch, craft))), tool_name]
		if craft == "rites": line += "  ·  " + Tx.t("ui.posts.charge") % int(Game.posts.rite_charge(ch))
		if craft == "snaring": line += "  ·  " + Tx.plural("ui.posts.snares_out", (Game.posts.snares(ch) as Array).size()) % (Game.posts.snares(ch) as Array).size()
		text(r.position + Vector2(52, minf(r.size.y - 9.0, 78.0)), line, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 64)   # I9: clear of the frame
		y += step
	var right := Rect2(left.end.x + 16, content.position.y, content.end.x - left.end.x - 16, content.size.y)
	panel(right)
	_draw_node_info(ch, right.grow(-16))

## Post Info for the node in reach: each output's Chance bar (jade) or, once full, its Abundance bar (gold).
func _draw_node_info(ch, r: Rect2) -> void:
	var o := {}
	if Game.world != null and Game.room_rt != null:
		var ctx: Dictionary = Game.world.query_context(ch)
		if ctx.has("object"): o = Game.room_rt.object_def(str(ctx.object))
	if o.is_empty() or Game.posts.craft_of_object(o) == "":
		var here := str(Game.room_rt.room_id) if Game.room_rt != null else ""
		if here != "" and Game.posts.vigil_allowed(here):
			_draw_vigil_info(ch, r, here)
			return
		heading(r.position + Vector2(0, 24), Tx.t("ui.posts.node_info"), r.size.x)
		para(Rect2(r.position + Vector2(0, 44), Vector2(r.size.x, r.size.y - 44)), Tx.t("ui.posts.node_info_none"), 18, UiKit.MIST)
		return
	var rates: Dictionary = Game.posts.rates_at(ch, o)
	heading(r.position + Vector2(0, 24), Tx.t("ui.posts.at_this_node"), r.size.x)
	text(r.position + Vector2(0, 62), Tx.t("ui.posts.finesse_dil") % [UiKit.fmt(int(float(rates.get("finesse", 0.0)))), int(round(float(rates.get("diligence", 0.52)) * 100.0))], 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x)
	var y := r.position.y + 80
	var lv: int = Game.posts.level(ch, Game.posts.craft_of_object(o))
	for out in Game.posts.outputs_of(o):
		icon_at(Rect2(r.position.x, y, 32, 32), str(out.item))
		text(Vector2(r.position.x + 40, y + 20), ContentDB.item_name(str(out.item)), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 40)
		y += 36
		if int(out.gate) > lv:
			text(Vector2(r.position.x + 40, y + 16), Tx.t("ui.posts.gate") % int(out.gate), 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 40)
			y += 30
			continue
		var yv := PostRules.yield_of(float(rates.get("finesse", 0.0)), float(out.toughness))
		if float(yv.chance) < 1.0:
			bar(Rect2(r.position.x + 40, y, r.size.x - 40, 24), float(yv.chance), UiKit.BRIGHT_JADE, Tx.t("ui.posts.chance") % int(round(float(yv.chance) * 100.0)))
		else:
			bar(Rect2(r.position.x + 40, y, r.size.x - 40, 24), float(yv.abundance_progress), UiKit.GOLD, Tx.t("ui.posts.abundance") % int(yv.abundance))
		y += 28
		text(Vector2(r.position.x + 40, y + 16), Tx.t("ui.posts.next_at") % UiKit.fmt(int(float(yv.next_finesse))), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 40)
		y += 30
		if y > r.end.y - 40: break

## Vigil Info for the room: kills an hour and what limits them, the Sweep tier, blows landed, and how long the
## character would last on the provisions it carries.
func _draw_vigil_info(ch, r: Rect2, room: String) -> void:
	var pr: Dictionary = Game.posts.vigil_profile(ch, room)
	heading(r.position + Vector2(0, 24), Tx.t("ui.posts.vigil_info"), r.size.x)
	if pr.is_empty(): return
	var y := r.position.y + 62
	var rows_v := [
		[Tx.t("ui.posts.v_kills"), UiKit.fmt(int(float(pr.kills_h)))],
		[Tx.t("ui.posts.v_limit"), Tx.t("ui.posts.v_spawn") if float(pr.spawn_h) < float(pr.fighter_h) else Tx.t("ui.posts.v_blade")],
		[Tx.t("ui.posts.v_hit"), "%d%% · %s" % [int(round(100.0 * float(pr.hit))), UiKit.fmt(int(float(pr.avg_hit)))]],
		[Tx.t("ui.posts.v_sweep"), Tx.t("ui.posts.v_sweep_val") % [int(pr.sweep_tier), float(pr.sweep)]],
		[Tx.t("ui.posts.v_dil"), "%d%%" % int(round(100.0 * float(pr.diligence)))],
		[Tx.t("ui.posts.v_taken"), "%s / %s" % [UiKit.fmt(int(float(pr.dmg_h))), UiKit.fmt(int(float(pr.regen_h)))]],
		[Tx.t("ui.posts.v_food"), (ContentDB.item_name(str(pr.food)) + " ×%d" % int(pr.food_count)) if str(pr.food) != "" else Tx.t("ui.posts.v_no_food")],
	]
	var sv := PostRules.survivability(ch.pools.max_hp, float(pr.dmg_h), float(pr.regen_h), float(pr.heal_each), int(pr.food_count), 12.0)
	rows_v.append([Tx.t("ui.posts.v_alive"), "%d%%" % int(round(100.0 * float(sv.alive)))])
	for row in rows_v:
		text(Vector2(r.position.x, y + 18), str(row[0]), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x * 0.6)
		text(Vector2(r.position.x, y + 18), str(row[1]), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, r.size.x)
		y += 32

# ------------------------------------------------------------------ Apprentice Bench (V10c)
func _draw_bench() -> void:
	var ch = c()
	if ch == null: return
	if not Unlocks.is_unlocked(ch.id, "apprentice_bench"):
		para(Rect2(content.position + Vector2(0, 20), Vector2(content.size.x, 80)), Unlocks.locked_text("apprentice_bench"), 18, UiKit.HOLLOW)
		return
	Game.submit({"type": "settle_works", "part": "bench"})
	var b: Dictionary = Game.posts.bench(ch)
	var x := content.position.x
	var y := content.position.y
	para(Rect2(Vector2(x, y), Vector2(content.size.x, 50)), Tx.t("ui.posts.bench_note") % UiKit.fmt(int(Game.posts.bench_capacity(ch))), 16, UiKit.MIST, 2)
	y += 56
	text(Vector2(x, y + 30), Tx.t("ui.posts.bench_points") % Game.posts.bench_points_free(ch), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 220)
	var bx := x + 232
	for k in ["speed", "capacity", "exp"]:
		btn(Rect2(bx, y, 176, 48), Tx.t("ui.posts.bench_" + k) % int(b.points.get(k, 0)), "bench_point", k, false, Game.posts.bench_points_free(ch) > 0, Tx.t("ui.posts.no_points_text"), 16)
		bx += 184
	y += 64
	for i in Game.posts.apprentices(ch):
		var cur := str(b.slots[i]) if i < b.slots.size() else ""
		var r := Rect2(x, y, content.size.x, 80)
		panel(r)
		text(r.position + Vector2(16, 30), Tx.t("ui.posts.apprentice") % (i + 1), 18, UiKit.PAPER)
		if cur != "":
			icon_at(Rect2(r.position + Vector2(176, 8), Vector2(64, 64)), cur)
			text(r.position + Vector2(252, 32), ContentDB.item_name(cur), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 440)
			text(r.position + Vector2(252, 60), Tx.t("ui.posts.bench_rate") % [snappedf(Game.posts.bench_rate_of(ch, cur), 0.1), UiKit.fmt(int(float(b.stock.get(cur, 0.0))))], 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 440)
		else:
			text(r.position + Vector2(180, 46), Tx.t("ui.posts.bench_idle"), 18, UiKit.HOLLOW)
		btn(Rect2(r.end.x - 170, r.position.y + 16, 154, 48), Tx.t("ui.posts.bench_change"), "bench_next", [i, cur], false, true, "", 18)
		y += 88
	para(Rect2(Vector2(x, y + 6), Vector2(content.size.x, 60)), Tx.t("ui.posts.bench_more") % [Game.posts.total_craft_levels(ch)], 16, UiKit.MIST, 2)

## The next component this character may set an apprentice to (by Level), after `cur` ("" = idle).
func _next_component(ch, cur: String) -> String:
	var opts: Array = [""]
	for cp in ContentDB.config("posts").get("bench", {}).get("components", []):
		if ProgressionRules.level(ch) >= int(cp.get("gate", 1)): opts.append(str(cp.item))
	var i := opts.find(cur)
	return str(opts[(i + 1) % opts.size()])

# ------------------------------------------------------------------ Post Vows (V10c)
func _draw_vows() -> void:
	var ch = c()
	if ch == null: return
	if not Unlocks.is_unlocked(ch.id, "ancestral_rites"):
		para(Rect2(content.position + Vector2(0, 20), Vector2(content.size.x, 80)), Unlocks.locked_text("ancestral_rites"), 18, UiKit.HOLLOW)
		return
	var wisps := Game.inventory.count_owned(ch, "spirit_wisp")
	para(Rect2(content.position, Vector2(content.size.x - 140, 50)), Tx.t("ui.posts.vows_note"), 16, UiKit.MIST, 2)
	icon_at(Rect2(content.end.x - 120, content.position.y + 4, 32, 32), "spirit_wisp")
	text(Vector2(content.end.x - 80, content.position.y + 28), UiKit.fmt(wisps), 20, UiKit.PALE_GOLD)
	var held: Array = Game.posts.held_vows(ch)
	var vows: Array = ContentDB.config("posts").get("post_vows", [])
	list("vows", Rect2(content.position + Vector2(0, 60), content.size - Vector2(0, 60)), vows.size(), 80, func(i: int, r: Rect2):
		var v: Dictionary = vows[i]
		var id := str(v.id)
		panel(r, "minor_panel", "selected" if held.has(id) else "normal")
		text(r.position + Vector2(16, 30), str(v.name), 18, UiKit.PALE_GOLD if held.has(id) else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 230)
		text(r.position + Vector2(16, 58), str(v.text), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 230)
		if not Game.account.post_vows.has(id):
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_learn") % int(v.cost), "vow_learn", id, false, wisps >= int(v.cost), Tx.t("ui.posts.vow_need"), 16)
		elif held.has(id):
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_drop"), "vow_off", id, false, true, "", 16)
		else:
			btn(Rect2(r.end.x - 196, r.position.y + 14, 180, 48), Tx.t("ui.posts.vow_hold"), "vow_on", id, true, held.size() < 2, Tx.t("sim.posts.vows_full"), 16)
	)

# ------------------------------------------------------------------ Storehouse: the whole cabinet
func _draw_store() -> void:
	var ids: Array = Game.account.storehouse.keys()
	ids.sort()
	var ch = c()
	para(Rect2(content.position, Vector2(content.size.x, 50)), Tx.t("ui.posts.store_note"), 16, UiKit.MIST, 2)
	# V10d: Auto-Settle for the account; the Granary Seal for this character's post.
	if ch != null and Unlocks.is_unlocked(ch.id, "seal_scripts"):
		var auto := bool(Game.posts.works().get("auto_settle", false))
		btn(Rect2(content.position.x, content.position.y + 56, 240, 48), Tx.t("ui.posts.auto_settle_on") if auto else Tx.t("ui.posts.auto_settle_off"),
			"option", ["auto_settle", not auto], auto, true, "", 16)
	if ch != null and Game.posts.favour_sum("granary_seal") > 0.0:
		var gran := bool(Game.posts.post_of(ch).get("granary", false))
		btn(Rect2(content.position.x + 256, content.position.y + 56, 250, 48), Tx.t("ui.posts.granary_on") if gran else Tx.t("ui.posts.granary_off"),
			"option", ["granary", not gran], gran, Game.posts.has_post(ch), Tx.t("sim.posts.mirror_needs_post"), 16)
	if ids.is_empty():
		text(content.position + Vector2(0, 150), Tx.t("ui.posts.store_empty"), 20, UiKit.HOLLOW)
		return
	var cols := 8
	var cell := 96.0
	var area := Rect2(content.position + Vector2(0, 116), Vector2(content.size.x, content.size.y - 116))
	var nrows := int(ceil(ids.size() / float(cols)))
	list("store", area, nrows, SLOT + 36, func(ri: int, rr: Rect2):
		for k in cols:
			var idx := ri * cols + k
			if idx >= ids.size(): break
			var id := str(ids[idx])
			var sr := Rect2(rr.position + Vector2(k * cell + (cell - SLOT) * 0.5, 0), Vector2(SLOT, SLOT))
			slot_box(sr, id, 0, "", "withdraw", id)
			UiKit.draw_outlined(self, UiKit.fmt(int(Game.account.storehouse[id])), sr.position + Vector2(0, sr.size.y + 20), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, sr.size.x)
	)

# ------------------------------------------------------------------ actions
func on_action(id: String, data) -> void:
	match id:
		"turn":
			turned[str(data)] = not turned.get(str(data), false)
			turn_t[str(data)] = t
		"page": page_at = maxi(0, page_at + int(data))
		"settle_all":
			var r := submit({"type": "settle_all"})
			if r.get("ok", false): flash(Tx.plural("ui.posts.settled_n", (r.get("ledgers", []) as Array).size()) % (r.get("ledgers", []) as Array).size())
		"settle":
			var before := 0
			for row in Game.posts.roll_call():
				if str(row.id) == str(data): before = int(row.pouch)
			var r := submit({"type": "settle_post", "character": str(data)})
			if r.get("ok", false):
				submit({"type": "send_to_storehouse", "character": str(data)})
				poured[str(data)] = [t, before]
				flash(Tx.t("ui.posts.settled_one"))
		"incense":
			var inc := _incense()
			if inc == "": return
			var r := submit({"type": "burn_incense", "character": str(data), "item": inc})
			if r.get("ok", false): flash(Tx.t("ui.posts.incense_burned") % UiKit.span(float(r.hours) * 3600.0))
		"switch": navigate.emit("_switch", {"slot": int(data)})
		"bench_collect":
			var r := submit({"type": "bench_collect"})
			if r.get("ok", false): flash(Tx.t("ui.posts.bench_collected"))
		"bench_point": submit({"type": "bench_point", "kind": str(data)})
		"bench_next": submit({"type": "bench_assign", "slot": int(data[0]), "item": _next_component(c(), str(data[1]))})
		"vow_learn": submit({"type": "learn_post_vow", "vow": str(data)})
		"vow_on": submit({"type": "pledge_post_vow", "vow": str(data), "on": true})
		"vow_off": submit({"type": "pledge_post_vow", "vow": str(data), "on": false})
		"option": submit({"type": "set_post_option", "key": str(data[0]), "on": bool(data[1])})
		"vigil":
			var r := submit({"type": "take_vigil"})
			if r.get("ok", false): flash(Tx.t("ui.posts.vigil_taken"))
		"withdraw":
			var r := submit({"type": "withdraw_storehouse", "item": str(data), "count": 50})
			if r.get("ok", false): flash(Tx.t("ui.posts.withdrew") % [int(r.count), ContentDB.item_name(str(data))])
