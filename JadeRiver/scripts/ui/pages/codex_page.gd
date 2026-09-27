extends Page
## Codex, Collection book, the Old Scrolls, Achievements, Paths Above and Seasons (S19, S32, S34, S43, S45, P10) in one
## page. P5 (docs/page_identity.md row 26, mockups 18 and 18_scrolls, decision 11): the field book, a bound book open on
## the reading desk, its sections silk ribbons standing out of the top edge (the open one's name inked on it, the
## page's title) and its curled corners turning the leaves. The Collection is a naturalist's field book, a spread for
## each collection page: each beast a drawing on squared paper taped in, its count on an ink bar, and the page's two
## seals with their gifts (decision 27), claimed with the one intent the page sends, claim_collection_seal.
## The Old Scrolls look like nothing else in the game: a black stone rubbing mounted as a hanging scroll, inked from the
## top down as the account climbs, each rung glossed in vermilion with our realms that stand on it, and the chosen
## rung's note pinned beside it. Apart from a seal's claim the page reads only.

const BOOK := Rect2(52, 76, 1176, 612)
const SPINE := 640.0
const LEFT_X := 96.0      # the left page's words, 500 wide
const RIGHT_X := 684.0    # the right page's words
const TEXT_W := 500.0
const HEAD_Y := 112.0     # the running heads' line
const PER_SPREAD := 4     # beasts on a Collection spread, two a page
const ROWS_PAGE := 6      # achievements and paths above on a page
const TURN_S := 0.35      # a leaf turning (page_identity §6)
const RUB := Rect2(96, 132, 408, 540)   # the Old Scrolls' rubbing
const SHEET := Rect2(792, 112, 432, 576)

var sel := ""
var leaf := {}            # tab id -> the spread open
var contents := false     # the Collection's contents on the right page
var rung := -1            # the Old Scrolls' chosen rung, and which of our realms on it
var rung_realm := ""
var turned_at := 0.0      # when the last leaf turned (or a rung was dabbed)
var stamped := {}         # "page:seal" -> when its claim stamped it (decision 27)
const STAMP_S := 0.3      # a claimed seal dabbed in

## Ink on paper (page_identity §7: the Records family's, RecordsKit), measured on the paper.
var INK := RecordsKit.INK
var BROWN := RecordsKit.BROWN
var FADED := RecordsKit.FADED
var RED_INK := RecordsKit.RED_INK
var JADE_INK := RecordsKit.JADE_INK
var NEXT_INK := RecordsKit.NEXT_INK
var PAGE_TOP := UiKit.PAPER.lerp(UiKit.PALE_GOLD, 0.15)

static var _spreads: Array = []   # the Collection's spreads: {page, beasts, part, parts}
static var _pages: Array = []     # the collection pages in book order: {id, beasts}
static var _lives := {}           # enemy -> the first room it spawns in

func _init() -> void:
	tabs = [{"id": "codex", "label": Tx.t("ui.codex.codex")}, {"id": "collection", "label": Tx.t("ui.codex.collection")},
		{"id": "old_scrolls", "label": Tx.t("ui.codex.old_scrolls")}, {"id": "achievements", "label": Tx.t("ui.codex.achievements")},
		{"id": "paths_above", "label": Tx.t("ui.codex.paths_above")}, {"id": "seasons", "label": Tx.t("ui.codex.seasons")}]
	title = str(tabs[0].label)
	identity = Identity.new("scroll", false, "own", "book_spread_ribbons", OPEN_MOTION_MAX)

func setup() -> void:
	for i in tabs.size():
		if str(tabs[i].id) == page_id: tab = i
	_build()
	# The Collection opens at the first page with a seal to claim, else at the first page still being filled.
	var claim := -1
	var filling := -1
	for i in _spreads.size():
		var pg: Dictionary = _spreads[i]
		if claim < 0 and int(pg.part) == 0 and [1, 2].any(func(n): return Game.accounts.seal_progress(pg.page, n).open): claim = i
		if filling < 0 and not Game.account.collection_pages_done.has(pg.page) and pg.beasts.any(func(e): return _kills(e) > 0): filling = i
	if claim >= 0 or filling >= 0: leaf["collection"] = claim if claim >= 0 else filling
	turned_at = t

func content_rect() -> Rect2:
	return BOOK

func _id() -> String:
	return str(tabs[tab].id)

# ------------------------------------------------------------------ the desk, the book and the ribbons
func draw_surface(_r: Rect2) -> void:
	title = str(tabs[tab].label)   # the open section's ribbon carries the title
	if _id() == "old_scrolls":
		_wall()
		return
	vshade(Rect2(0, 0, 1280, 720), Color(UiKit.SURFACE.wood_dark, 0.92), Color(UiKit.SURFACE.soil, 0.96))
	for x in range(180, 1280, 182): draw_rect(Rect2(x, 0, 2, 720), Color(UiKit.INK, 0.18))
	rounded(Rect2(34, 64, 1212, 650), 12.0, Color(UiKit.GOLD, 0.35))
	rounded(Rect2(36, 66, 1208, 646), 10.0, UiKit.SURFACE.cloth)
	# The page block's edges, then the two pages with their shade and the gutter.
	for i in 4:
		var edge := UiKit.SURFACE.scroll if i % 2 == 0 else UiKit.SURFACE.scroll_edge.lerp(UiKit.BRONZE, 0.3)
		draw_rect(Rect2(44 + i * 2, 80, 2, 606), edge)
		draw_rect(Rect2(1228 + i * 2, 80, 2, 606), edge)
		draw_rect(Rect2(54, 688 + i * 2, 1172, 2), edge)
	for x in [BOOK.position.x, SPINE]: vshade(Rect2(x, BOOK.position.y, BOOK.size.x * 0.5, BOOK.size.y), PAGE_TOP, UiKit.SURFACE.scroll)
	ground(BOOK, UiKit.SURFACE.scroll)
	hshade(Rect2(52, 76, 64, 612), Color(UiKit.BRONZE, 0.14), Color(UiKit.BRONZE, 0.0))
	hshade(Rect2(1164, 76, 64, 612), Color(UiKit.BRONZE, 0.0), Color(UiKit.BRONZE, 0.14))
	hshade(Rect2(598, 76, 42, 612), Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.4))
	hshade(Rect2(640, 76, 46, 612), Color(UiKit.INK, 0.4), Color(UiKit.INK, 0.0))
	for f in [[170, 640, 60], [540, 190, 40], [1010, 660, 70], [1170, 160, 44], [790, 350, 30]]:
		glow(Rect2(f[0] - f[2] * 0.5, f[1] - f[2] * 0.5, f[2], f[2]), Color(UiKit.BRONZE, 0.16))

## The Old Scrolls hang on the reading room's wall.
func _wall() -> void:
	vshade(Rect2(0, 0, 1280, 720), Color(UiKit.SURFACE.wood_dark.lerp(UiKit.BLOOD, 0.08), 0.94), Color(UiKit.SURFACE.soil, 0.96))
	for y in range(0, 720, 5): draw_rect(Rect2(0, y, 1280, 1), Color(UiKit.PAPER, 0.012))

func tab_rects() -> Array:
	var out: Array = []
	var x := 76.0
	for tb in tabs:
		var w := maxf(110.0, UiKit.text_width(str(tb.label), 22, true) + 40.0)
		out.append(Rect2(x, 32, w, TAB_H))
		x += w + TAB_GAP
	return out

func title_rect() -> Rect2:
	return tab_rects()[tab]

func _ribbon_col(id: String) -> Color:
	match id:
		"codex": return UiKit.JADE_SHADOW
		"collection": return UiKit.BLOOD.lerp(UiKit.INK, 0.15)
		"old_scrolls": return UiKit.BRONZE.lerp(UiKit.INK, 0.25)
		"achievements": return UiKit.BRONZE.lerp(UiKit.INK, 0.45)
		"paths_above": return UiKit.SKY.lerp(UiKit.INK, 0.62)
	return UiKit.HEART.lerp(UiKit.INK, 0.4)

## A silk ribbon standing out of the book's top edge, its free end cut in a V; it runs under the pages.
func _ribbon(r: Rect2, id: String, top: float, foot: float) -> void:
	var col := _ribbon_col(id)
	var pts := PackedVector2Array([Vector2(r.position.x, top), Vector2(r.get_center().x, top + 12), Vector2(r.end.x, top), Vector2(r.end.x, foot), Vector2(r.position.x, foot)])
	draw_colored_polygon(pts, col)
	hshade(Rect2(r.position.x, top + 12, r.size.x * 0.3, foot - top - 12), Color(UiKit.INK, 0.22), Color(UiKit.INK, 0.0))
	hshade(Rect2(r.end.x - r.size.x * 0.4, top + 12, r.size.x * 0.4, foot - top - 12), Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.25))
	vshade(Rect2(r.position.x, foot - 10, r.size.x, 10), Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.25))
	ground(Rect2(r.position.x, top + 12, r.size.x, foot - top - 12), col)

## The open section's ribbon hangs longer; on the Collection a narrow bookmark of it lies into the spread.
func draw_title_mount(r: Rect2) -> void:
	var book := _id() != "old_scrolls"
	_ribbon(r, _id(), 0.0, BOOK.position.y if book else 88.0)
	if _id() == "collection":
		var bx := r.position.x + 62
		draw_colored_polygon(PackedVector2Array([Vector2(bx, 76), Vector2(bx + 24, 76), Vector2(bx + 24, 132), Vector2(bx + 12, 124), Vector2(bx, 132)]), _ribbon_col("collection"))
		hshade(Rect2(bx, 76, 8, 50), Color(UiKit.INK, 0.25), Color(UiKit.INK, 0.0))

func draw_tab(r: Rect2, i: int, state: String) -> void:
	if state == "selected": return   # the title mount is the open ribbon
	_ribbon(r, str(tabs[i].id), 8.0, BOOK.position.y if _id() != "old_scrolls" else 80.0)
	text(Vector2(r.position.x, 66), str(tabs[i].label), 18, UiKit.HOLLOW if state == "disabled" else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match _id():
		"codex": _codex()
		"collection": _collection()
		"old_scrolls": _scrolls(ch)
		"achievements": _achievements()
		"paths_above": _paths_above(ch)
		"seasons": _seasons()
	if _id() != "old_scrolls": _turning()

## A running head on each page: the left's section and the right's.
func _heads(left: String, left_r: String, right: String, right_r: String) -> void:
	text(Vector2(LEFT_X, HEAD_Y), left.to_upper(), 14, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 300)
	text(Vector2(LEFT_X + 200, HEAD_Y), left_r, 14, BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 300)
	text(Vector2(RIGHT_X, HEAD_Y), right.to_upper(), 14, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 300)
	text(Vector2(RIGHT_X + 200, HEAD_Y), right_r, 14, BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 300)

## A ruled line in ink, fading out to the right.
func _rule(x: float, y: float, w: float, a := 0.7) -> void:
	hshade(Rect2(x, y, w, 2), Color(BROWN, a), Color(BROWN, 0.0))

## An ink-drawn bar: a pencil outline, a wash to `frac`, an ink diamond at its end (filled once reached, gold while next)
## and, with `stop`, a smaller ink diamond at that share (a stop passed).
func _ink_bar(r: Rect2, frac: float, gold := false, stop := -1.0) -> void:
	draw_rect(r, Color(UiKit.PAPER, 0.4))
	draw_rect(Rect2(r.position, Vector2(r.size.x * clampf(frac, 0.0, 1.0), r.size.y)), UiKit.BRONZE.lerp(UiKit.GOLD, 0.35) if gold else UiKit.JADE_SHADOW.lerp(UiKit.JADE, 0.35))
	draw_rect(r, INK, false, 2.0)
	if stop > 0.0 and stop < 1.0: _diamond(Vector2(r.position.x + r.size.x * stop, r.position.y + r.size.y * 0.5), 6.0, INK)
	_diamond(Vector2(r.end.x, r.position.y), 7.0, INK if frac >= 1.0 else UiKit.GOLD)

func _diamond(p: Vector2, s: float, fill: Color) -> void:
	var d := PackedVector2Array([p + Vector2(0, -s), p + Vector2(s, 0), p + Vector2(0, s), p + Vector2(-s, 0)])
	draw_colored_polygon(d, fill)
	d.append(d[0])
	draw_polyline(d, INK, 2.0, true)

## The leaves turn with the curled corners: the spread before and after, and the two page numbers at the foot.
func _turn(count: int, back: String, on: String) -> void:
	var k := int(leaf.get(_id(), 0))
	text(Vector2(52, 680), str(2 * k + 1), 22, BROWN, HORIZONTAL_ALIGNMENT_CENTER, 588, true)
	text(Vector2(640, 680), str(2 * k + 2), 22, BROWN, HORIZONTAL_ALIGNMENT_CENTER, 588, true)
	if k > 0:
		_curl(Vector2(52, 632), true)
		text(Vector2(116, 680), "◂ " + back, 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 200)
		region(Rect2(64, 632, 248, 56), "leaf", -1)
	if k < count - 1:
		_curl(Vector2(1172, 632), false)
		text(Vector2(964, 680), on + " ▸", 16, BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 200)
		region(Rect2(968, 632, 248, 56), "leaf", 1)

## A page corner curled up: the cover under it and the lifted flap.
func _curl(p: Vector2, left: bool) -> void:
	var s := 56.0
	var a := p + (Vector2(0, 0) if left else Vector2(s, 0))
	var b := p + (Vector2(s, s) if left else Vector2(0, s))
	var foot := p + (Vector2(0, s) if left else Vector2(s, s))
	draw_colored_polygon(PackedVector2Array([a, foot, b]), UiKit.SURFACE.cloth)
	draw_colored_polygon(PackedVector2Array([a + Vector2(3, 3) * (1 if left else -1) + Vector2(0, 2), b + Vector2(3, 3), p + (Vector2(s, 0) if left else Vector2(0, 0)) + Vector2(3, 3)]), Color(UiKit.INK, 0.3))
	draw_polygon(PackedVector2Array([a, b, p + (Vector2(s, 0) if left else Vector2(0, 0))]), PackedColorArray([UiKit.SURFACE.scroll_edge, PAGE_TOP, UiKit.SURFACE.scroll]))

## A leaf turning over the spread (0.35 s) after a turn, a new section or the opening; none under Reduce motion.
func _turning() -> void:
	var p := (t - turned_at) / TURN_S
	if UiKit.reduce_motion() or p >= 1.0 or p < 0.0: return
	var e := 1.0 - pow(1.0 - p, 3.0)
	var edge := lerpf(BOOK.end.x, BOOK.position.x, e)
	var r := Rect2(minf(edge, SPINE), BOOK.position.y - 6.0 * sin(e * PI), absf(edge - SPINE), BOOK.size.y)
	vshade(r, PAGE_TOP, UiKit.SURFACE.scroll)
	if edge > SPINE: hshade(r, Color(UiKit.INK, 0.3), Color(UiKit.INK, 0.0))
	else: hshade(r, Color(UiKit.INK, 0.0), Color(UiKit.INK, 0.3))
	draw_line(Vector2(edge, r.position.y), Vector2(edge, r.end.y), Color(UiKit.BRONZE, 0.5), 2.0)

# ------------------------------------------------------------------ the Codex: its contents and the entry read
func _codex() -> void:
	var entries: Array = ContentDB.all("codex").filter(func(e): return not str(e.id).begins_with("old_scrolls"))
	if sel == "" or not Game.account.codex.has(sel) or str(sel).begins_with("old_scrolls"):
		sel = ""
		for e0 in entries:
			if Game.account.codex.has(str(e0.id)):
				sel = str(e0.id)
				break
	var known: int = entries.filter(func(e): return Game.account.codex.has(str(e.id))).size()
	_heads(Tx.t("ui.codex.head_codex"), Tx.t("ui.codex.entries_count") % [known, entries.size()], "", "")
	list("codex", Rect2(LEFT_X - 8, 128, TEXT_W + 16, 496), entries.size(), 48, func(i: int, rr: Rect2):
		var e: Dictionary = entries[i]
		var is_known: bool = Game.account.codex.has(str(e.id))
		if is_known and sel == str(e.id):   # the one selection style: a gold wash and the vermilion marker
			var wash := UiKit.SURFACE.scroll.lerp(UiKit.GOLD, 0.3)
			rounded(rr, 4.0, wash)
			ground(rr, wash)
			draw_rect(Rect2(rr.position.x, rr.position.y + 6, 4, rr.size.y - 12), RED_INK)
		text(rr.position + Vector2(16, 31), str(e.title) if is_known else "? ? ?", 18, INK if is_known else FADED, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 28)
		region(rr, "sel", str(e.id), is_known, Tx.t("ui.codex.not_yet_discovered"))
	)
	if sel == "":
		para(Rect2(RIGHT_X, 140, TEXT_W, 80), Tx.t("ui.codex.of_entries_discovered") % [known, entries.size()], 20, BROWN)
		return
	var e2 := ContentDB.entry("codex", sel)
	text(Vector2(RIGHT_X, 154), str(e2.get("title", "")), 30, INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W, true)
	_rule(RIGHT_X, 170, TEXT_W)
	var y := 186.0 + para(Rect2(RIGHT_X, 186, TEXT_W, 300), str(e2.get("body", "")), 18, INK) + 16.0
	# P12: under Realms, the par character at your Level, the yardstick every foe of that Level is set against.
	if sel == "realms":
		var lv := ProgressionRules.level(c())
		var p := StatRules.par(lv)
		text(Vector2(RIGHT_X, y + 12), Tx.t("ui.codex.par_title") % ContentDB.realm_label(c().cultivator.realm_key, lv), 20, RED_INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
		para(Rect2(RIGHT_X, y + 22, TEXT_W, 624 - y - 22), Tx.t("ui.codex.par_body") % ["%.2f" % float(p.get("might", 1.0)),
			UiKit.short(float(p.get("attack", 0))), UiKit.short(float(p.get("basic", 0))), UiKit.short(float(p.get("technique", 0))),
			UiKit.short(float(p.get("technique_crit", 0))), UiKit.short(float(p.get("max_hp", 0))), UiKit.short(float(p.get("cp", 0)))], 16, BROWN)
	# S44: the experiment log, shared by every character on the account.
	if sel == "experiments":
		for ex in Game.account.experiments.slice(maxi(0, Game.account.experiments.size() - 10)):
			if y > 600: break
			var names: Array = []
			for h in ex.get("herbs", []): names.append(ContentDB.item_name(str(h)))
			text(Vector2(RIGHT_X, y + 12), " + ".join(names) + "  →  " + Game.crafting.experiment_result_text(ex), 16,
				JADE_INK if str(ex.get("result", "")).begins_with("learned:") else BROWN, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
			y += 24

# ------------------------------------------------------------------ the Collection: the field book
static func _build() -> void:
	if not _spreads.is_empty(): return
	var by := {}
	for e in ContentDB.all("enemies"):
		var col = e.get("collection")
		if not col is Dictionary: continue
		if not by.has(str(col.page)):
			by[str(col.page)] = []
			_pages.append({"id": str(col.page), "beasts": by[str(col.page)]})
		by[str(col.page)].append(e)
	for pg in _pages:
		var parts := int(ceil(pg.beasts.size() / float(PER_SPREAD)))
		for k in parts: _spreads.append({"page": pg.id, "beasts": pg.beasts.slice(k * PER_SPREAD, (k + 1) * PER_SPREAD), "part": k, "parts": parts})
	for rid in ContentDB.rooms:
		for sp in ContentDB.room(rid).get("spawns", []):
			if not _lives.has(str(sp.get("enemy", ""))): _lives[str(sp.get("enemy", ""))] = str(rid)

func _kills(e: Dictionary) -> int:
	return int(Game.account.collection.get(str(e.id), 0))

func _fill(e: Dictionary) -> int:
	return int(e.collection.get("kills_to_fill", 50))

func _master(e: Dictionary) -> int:
	return int(e.collection.get("kills_to_master", _fill(e)))

func _page_name(id: String) -> String:
	return Tx.t("ui.codex.page_" + id)

static func _lv(e: Dictionary) -> Array:
	var lv = e.get("level", 1)
	return [int(lv[0]), int(lv[-1])] if lv is Array else [int(lv), int(lv)]

func _collection() -> void:
	var k := clampi(int(leaf.get("collection", 0)), 0, _spreads.size() - 1)
	var sp: Dictionary = _spreads[k]
	var beasts: Array = []
	for pg in _pages:
		if pg.id == sp.page: beasts = pg.beasts
	var all_beasts: Array = []
	for pg in _pages: all_beasts.append_array(pg.beasts)
	var filled: int = all_beasts.filter(func(e): return _kills(e) >= _fill(e)).size()
	var pidx: int = _pages.map(func(pg): return pg.id).find(sp.page)
	var lo := 999
	var hi := 0
	for e in beasts:
		lo = mini(lo, int(_lv(e)[0]))
		hi = maxi(hi, int(_lv(e)[1]))
	_heads(Tx.t("ui.codex.head_collection"), Tx.t("ui.codex.page_of") % [pidx + 1, _pages.size()], _page_name(sp.page),
		Tx.t("ui.codex.monster_level") % ("%d–%d" % [lo, hi] if hi > lo else str(lo)))
	# The whole book: the cards filled and the next stop (the Collector's title), and the Contents.
	text(Vector2(LEFT_X, 146), Tx.t("ui.codex.cards_filled"), 16, INK)
	var x := LEFT_X + UiKit.text_width(Tx.t("ui.codex.cards_filled"), 16) + 8
	text(Vector2(x, 147), str(filled), 22, INK)
	text(Vector2(x + UiKit.text_width(str(filled), 22) + 4, 146), "/ %d" % all_beasts.size(), 16, BROWN)
	var stop := {}
	for a in ContentDB.all("achievements"):
		if str(a.get("event", "")) == "collection_card_filled" and int(a.get("count", 1)) > filled and (stop.is_empty() or int(a.count) < int(stop.count)): stop = a
	_ink_bar(Rect2(LEFT_X, 158, 330, 18), filled / float(int(stop.get("count", all_beasts.size()))), true)
	if not stop.is_empty() and stop.has("title"):
		var gift := ", ".join((ContentDB.entry("titles", str(stop.title)).get("modifiers", []) as Array).map(func(m): return UiKit.affix_text(m)))
		text(Vector2(LEFT_X, 204), Tx.t("ui.codex.next_title") % [int(stop.count), ContentDB.name_of("titles", str(stop.title)), gift], 16, NEXT_INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
	else:
		text(Vector2(LEFT_X, 204), Tx.t("ui.codex.pages_sealed") % [Game.account.collection_pages_done.size(), _pages.size()], 16, NEXT_INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
	var cb := Rect2(458, 128, 138, 48)
	rounded(cb, 4.0, INK.lerp(UiKit.PAPER, 0.45) if contents else Color(INK, 0.55))
	rounded(cb.grow(-2), 3.0, UiKit.SURFACE.scroll.lerp(UiKit.GOLD, 0.3) if contents else PAGE_TOP)
	ground(cb, UiKit.SURFACE.scroll)
	for i in 3: draw_rect(Rect2(cb.position.x + 14, cb.position.y + 17 + i * 6, 18, 2), INK)
	text(Vector2(cb.position.x + 40, cb.position.y + 30), Tx.t("ui.codex.contents"), 16, INK)
	region(cb, "contents")
	_rule(LEFT_X, 216, TEXT_W)
	# The page: its name, how many beasts and when a card fills, its two seals.
	text(Vector2(LEFT_X, 256), _page_name(sp.page), 30, INK, HORIZONTAL_ALIGNMENT_LEFT, 300, true)
	var nx := LEFT_X + minf(300.0, UiKit.text_width(_page_name(sp.page), 30, true)) + 12
	text(Vector2(nx, 252), Tx.plural("ui.codex.beasts_fill", beasts.size()) % [beasts.size(), _fill(beasts[0])], 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 506 - nx)
	for n in [1, 2]: _seal(Rect2(512 + (n - 1) * 44, 226, 34, 34), sp.page, n)
	for i in sp.beasts.size():
		if contents and i >= 2: break
		var at := Vector2(LEFT_X, 276 + i * 180) if i < 2 else Vector2(RIGHT_X, 128 + (i - 2) * 176)
		_beast(sp.beasts[i], at)
	if contents: _contents()
	else: _page_seals(sp.page)
	_turn(_spreads.size(), _page_name(_spreads[maxi(0, k - 1)].page), _page_name(_spreads[mini(_spreads.size() - 1, k + 1)].page))

## One field-book entry: the beast drawn on squared paper and taped in (a shadow while not yet met), its name, rank,
## nature and levels, a note, what it drops, and its count on an ink bar to the card's fill.
func _beast(e: Dictionary, at: Vector2) -> void:
	var kills := _kills(e)
	var met := kills > 0
	var spec := Rect2(at, Vector2(188, 132))
	rounded(spec.grow(1), 2.0, Color(INK, 0.7))
	draw_rect(spec, UiKit.PAPER.lerp(UiKit.PALE_GOLD, 0.2))
	for gx in range(16, 188, 16): draw_rect(Rect2(spec.position.x + gx, spec.position.y, 1, spec.size.y), Color(UiKit.JADE_SHADOW, 0.12))
	for gy in range(16, 132, 16): draw_rect(Rect2(spec.position.x, spec.position.y + gy, spec.size.x, 1), Color(UiKit.JADE_SHADOW, 0.12))
	draw_rect(spec.grow(-4), Color(INK, 0.45), false, 1.0)
	var art = e.get("art", {})
	var cid := str(art.get("creature", "")) if art is Dictionary else ""
	var fig := Rect2(spec.position + Vector2(12, 8), spec.size - Vector2(24, 30))
	if cid == "" or not creature_at(fig, cid, "idle", Color.WHITE if met else Color(INK, 0.28)):
		if met: icon_at(Rect2(spec.get_center() - Vector2(32, 40), Vector2(64, 64)), str(e.get("loot_icon", "boss_skull")))
	for gx in range(int(spec.position.x) + 14, int(spec.end.x) - 14, 12): draw_rect(Rect2(gx, spec.end.y - 22, 8, 2), Color(INK, 0.55))
	for tp in [[spec.position + Vector2(-12, 2), -0.4], [spec.end - Vector2(28, 8), -0.4]]:
		draw_set_transform(tp[0], tp[1])
		draw_rect(Rect2(0, 0, 44, 16), Color(UiKit.SURFACE.bridge, 0.75))
		draw_set_transform(Vector2.ZERO)
	var fill := _fill(e)
	if kills >= fill:   # the card is filled: its mark stamped on the drawing (the fill, then the mark for seal II)
		var st := Rect2(spec.end.x - 58, spec.position.y + 10, 50, 50)
		_stamp(st)
		var mark := _master(e) if kills >= _master(e) else fill
		text(Vector2(st.position.x, st.position.y + 34), str(mark), 22 if mark < 100 else 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, st.size.x)
	var tx := at.x + 204
	var tw := TEXT_W - 204
	var lv: Array = _lv(e)
	var lv_s := Tx.t("ui.codex.lv") % ("%d–%d" % lv if lv[1] > lv[0] else str(lv[0]))
	if not met:
		text(Vector2(tx, at.y + 28), "? ? ?", 30, FADED, HORIZONTAL_ALIGNMENT_LEFT, tw, true)
		var home := str(_lives.get(str(e.id), ""))
		text(Vector2(tx, at.y + 54), Tx.t("ui.codex.lives_at") % ContentDB.name_of("rooms", home) if Game.account.visited_rooms.has(home) else Tx.t("ui.codex.not_met"), 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, tw)
	else:
		text(Vector2(tx, at.y + 28), str(e.name), 30 if UiKit.text_width(str(e.name), 30, true) <= tw else 26, INK, HORIZONTAL_ALIGNMENT_LEFT, tw, true)
		var sub := lv_s
		if int(e.get("beast_rank", 0)) > 0:   # S46: a beast's rank and nature (demonic and Hollowed ones are tamed differently)
			sub = Tx.t("ui.codex.rank_nature") % [int(e.beast_rank), Tx.t("ui.codex.nature_" + str(e.get("nature", "spirit")))] + " · " + lv_s
		text(Vector2(tx, at.y + 54), sub, 16, RED_INK if str(e.get("nature", "")) == "demonic" else BROWN, HORIZONTAL_ALIGNMENT_LEFT, tw)
		var note := Tx.t("ui.codex.tamed_into") % ContentDB.name_of("pets", str(e.tame_species)) if str(e.get("tame_species", "")) != "" \
			else (Tx.t("ui.codex.tameable") if e.get("tameable", false) else "")
		if note != "": para(Rect2(tx, at.y + 60, tw, 40), note, 16, INK, 2)
		var dx := tx
		text(Vector2(dx, at.y + 128), Tx.t("ui.codex.drops"), 16, BROWN)
		dx += UiKit.text_width(Tx.t("ui.codex.drops"), 16) + 6
		for d in (e.get("drops", []) as Array).slice(0, 2):
			if dx > tx + tw - 60: break
			dx = roundf(dx)
			icon_at(Rect2(dx, at.y + 106, 32, 32), str(d.item))
			var nm := ContentDB.item_name(str(d.item))
			text(Vector2(dx + 34, at.y + 128), nm, 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, tx + tw - dx - 34)
			dx += 34 + minf(UiKit.text_width(nm, 16), tx + tw - dx - 34) + 12
	var cnt := str(kills) if kills >= fill else "%d / %d" % [kills, fill]
	text(Vector2(at.x, at.y + 162), cnt, 22, INK)
	if kills >= fill: text(Vector2(at.x + UiKit.text_width(cnt, 22) + 8, at.y + 161), Tx.t("ui.codex.defeated_word"), 16, BROWN)
	# A filled card's bar runs on to its mark for seal II (decision 27), the fill a stop on it.
	var master := _master(e)
	if kills >= fill: _ink_bar(Rect2(at.x + 150, at.y + 148, TEXT_W - 150, 18), kills / float(master), true, fill / float(master))
	else: _ink_bar(Rect2(at.x + 150, at.y + 148, TEXT_W - 150, 18), kills / float(fill))

## A vermilion stamp with its paper rim (`k` fades it in).
func _stamp(r: Rect2, k := 1.0) -> void:
	rounded(r, 6.0, Color(UiKit.BLOOD, 0.9 * k))
	ground(r, UiKit.BLOOD)
	draw_rect(r.grow(-3), Color(UiKit.PAPER, 0.6 * k), false, 2.0)

## A page's seal `n` (decision 27, mockup 18): stamped in vermilion with its numeral once claimed (dabbed in over
## STAMP_S after the claim); a dashed vermilion outline while it waits, glowing once it can be claimed; a faded brown
## outline for seal II until seal I is claimed.
func _seal(r: Rect2, page: String, n: int) -> void:
	var pr: Dictionary = Game.accounts.seal_progress(page, n)
	var num := Tx.t("ui.codex.seal_%d" % n)
	var size := 14 if r.size.x < 30 else (18 if r.size.x < 48 else 26)
	if pr.claimed:
		var k := clampf((t - float(stamped.get("%s:%d" % [page, n], -9.0))) / STAMP_S, 0.0, 1.0)
		if UiKit.reduce_motion(): k = 1.0
		var sr := Rect2(r.get_center() - r.size * (1.5 - 0.5 * k) * 0.5, r.size * (1.5 - 0.5 * k))
		_stamp(sr, k)
		text(Vector2(sr.position.x, sr.get_center().y + size * 0.36), num, size, Color(UiKit.PAPER, k), HORIZONTAL_ALIGNMENT_CENTER, sr.size.x, true)
		return
	var col := RED_INK if pr.after_ok else BROWN
	if pr.open: glow(r.grow(r.size.x * 0.35), Color(UiKit.GOLD, 0.35 + 0.25 * _pulse()))
	for s in [[r.position, Vector2(r.end.x, r.position.y)], [Vector2(r.end.x, r.position.y), r.end], [r.end, Vector2(r.position.x, r.end.y)], [Vector2(r.position.x, r.end.y), r.position]]:
		draw_dashed_line(s[0], s[1], Color(col, 0.75 if pr.after_ok else 0.5), 3.0, 6.0)
	text(Vector2(r.position.x, r.get_center().y + size * 0.36), num, size, col, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)

## The page's seals (decision 27, mockup 18): each with its rule, its gift, its cards on an ink bar, and Claim once
## earned (the Account authority's claim_collection_seal); a claimed seal is stamped and says so.
func _page_seals(page: String) -> void:
	_rule(RIGHT_X, 476, TEXT_W)
	text(Vector2(RIGHT_X, 504), Tx.t("ui.codex.seal_head"), 26, INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W, true)
	for n in [1, 2]:
		var pr: Dictionary = Game.accounts.seal_progress(page, n)
		var y := 514.0 + 60.0 * int(n - 1)
		_seal(Rect2(RIGHT_X + 4, y + 2, 50, 50), page, n)
		var tx := RIGHT_X + 70
		var rule_s := Tx.t("ui.codex.seal_rule") % int(pr.mark) if int(pr.mark) > 0 else Tx.t("ui.codex.seal_rule_mixed")
		if n == 2: rule_s = Tx.t("ui.codex.seal_after") % [rule_s, Tx.t("ui.codex.seal_1")]
		text(Vector2(tx, y + 16), rule_s, 18, INK if pr.after_ok else BROWN, HORIZONTAL_ALIGNMENT_LEFT, 300)
		var gift_w := TEXT_W - 70
		if pr.open:   # Claim stands at the row's end in place of its count
			btn(Rect2(RIGHT_X + TEXT_W - 112, y + 4, 112, 48), Tx.t("ui.codex.claim"), "claim_seal", [page, n], true, true, "", 18)
			gift_w -= 124
		elif pr.claimed: text(Vector2(tx + 300, y + 16), Tx.t("ui.codex.sealed"), 16, RED_INK, HORIZONTAL_ALIGNMENT_RIGHT, TEXT_W - 370)
		else: text(Vector2(tx + 300, y + 16), Tx.t("ui.codex.seal_cards" if n == 1 else "ui.codex.seal_cards_studied") % [int(pr.done), int(pr.cards)], 14, BROWN, HORIZONTAL_ALIGNMENT_RIGHT, TEXT_W - 370)
		text(Vector2(tx, y + 36), UiKit.seal_gift(ContentDB.collection_seal(page, n), false), 16, JADE_INK, HORIZONTAL_ALIGNMENT_LEFT, gift_w)
		_ink_bar(Rect2(tx, y + 44, 280, 12), int(pr.got) / float(maxi(1, int(pr.need))), pr.claimed)
		if not pr.open: text(Vector2(tx + 292, y + 56), "%s / %s" % [UiKit.fmt(int(pr.got)), UiKit.fmt(int(pr.need))], 16, INK if pr.after_ok else BROWN, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W - 362)

## Contents: every page of the book in two columns, its cards filled and its seal; a tap turns to it.
func _contents() -> void:
	for i in _pages.size():
		var pg: Dictionary = _pages[i]
		var r := Rect2(RIGHT_X + (i % 2) * 256, 140 + (i / 2) * 60, 244, 52)
		var at: int = _spreads.map(func(s): return s.page).find(pg.id)
		var n: int = pg.beasts.filter(func(e): return _kills(e) >= _fill(e)).size()
		var here: bool = str(_spreads[int(leaf.get("collection", 0))].page) == pg.id
		if here:
			rounded(r, 4.0, UiKit.SURFACE.scroll.lerp(UiKit.GOLD, 0.3))
			ground(r, UiKit.SURFACE.scroll.lerp(UiKit.GOLD, 0.3))
		_rule(r.position.x, r.end.y, r.size.x, 0.35)
		text(Vector2(r.position.x + 8, r.position.y + 33), _page_name(pg.id), 16, INK, HORIZONTAL_ALIGNMENT_LEFT, 160)
		text(Vector2(r.end.x - 76, r.position.y + 33), "%d / %d" % [n, pg.beasts.size()], 14, BROWN, HORIZONTAL_ALIGNMENT_RIGHT, 44)
		_seal(Rect2(r.end.x - 26, r.position.y + 14, 22, 22), pg.id, 2 if Game.account.collection_seals.has(pg.id + ":1") else 1)
		region(r, "goto", at)

# ------------------------------------------------------------------ Achievements and Paths Above: rows on the pages
func _rows_spread(count: int) -> Array:
	var k := clampi(int(leaf.get(_id(), 0)), 0, maxi(0, int(ceil(count / float(ROWS_PAGE * 2))) - 1))
	leaf[_id()] = k
	return range(k * ROWS_PAGE * 2, mini(count, (k + 1) * ROWS_PAGE * 2))

## Row `j` of a spread of `n` rows: the first half down the left page, the rest down the right.
func _row_at(j: int, n: int, top: float, pitch: float) -> Vector2:
	var half := int(ceil(n / 2.0))
	return Vector2(LEFT_X if j < half else RIGHT_X, top + (j % half) * pitch)

func _achievements() -> void:
	var list_a: Array = ContentDB.all("achievements")
	var done_n: int = list_a.filter(func(a): return Game.account.achievements.done.has(str(a.id))).size()
	_heads(Tx.t("ui.codex.head_achievements"), "%d / %d" % [done_n, list_a.size()], Tx.t("ui.codex.head_achievements"), "")
	var spread := _rows_spread(list_a.size())
	for j in spread.size():
		var a: Dictionary = list_a[spread[j]]
		var p := _row_at(j, spread.size(), 132, 80)
		var done: bool = Game.account.achievements.done.has(str(a.id))
		var n := int(Game.account.achievements.counters.get(str(a.id), 0))
		text(p + Vector2(0, 26), str(a.name), 20, INK, HORIZONTAL_ALIGNMENT_LEFT, 300)
		if a.has("title"): text(p + Vector2(300, 26), Tx.t("ui.codex.title") % ContentDB.name_of("titles", str(a.title)), 16, RED_INK, HORIZONTAL_ALIGNMENT_RIGHT, 200)
		text(p + Vector2(0, 52), str(a.get("desc", "")), 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 380)
		if done:
			text(p + Vector2(380, 52), Tx.t("ui.codex.complete"), 16, JADE_INK, HORIZONTAL_ALIGNMENT_RIGHT, 120)
			var ar := Rect2(p.x - 30, p.y + 10, 20, 20)
			_stamp(ar)
			draw_rect(ar.grow(-6), Color(UiKit.PAPER, 0.7), false, 3.0)
		elif int(a.get("count", 1)) > 1: text(p + Vector2(380, 52), "%d / %d" % [n, int(a.count)], 16, INK, HORIZONTAL_ALIGNMENT_RIGHT, 120)
		_rule(p.x, p.y + 70, TEXT_W, 0.3)
	_turn(int(ceil(list_a.size() / float(ROWS_PAGE * 2))), Tx.t("ui.codex.turn_back"), Tx.t("ui.codex.turn_on"))

## S43 "Paths Above": every optional ledge that only a later movement art reaches, and whether you have stood on it.
func _paths_above(ch) -> void:
	var rows: Array = ContentDB.all("paths_above")
	_heads(Tx.t("ui.codex.head_paths_above"), "", Tx.t("ui.codex.head_paths_above"), "")
	text(Vector2(LEFT_X, 144), Tx.t("ui.codex.paths_above_intro") % [Game.account.paths_above.size(), rows.size()], 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
	var spread := _rows_spread(rows.size())
	for j in spread.size():
		var e: Dictionary = rows[spread[j]]
		var p := _row_at(j, spread.size(), 160, 76)
		var found: bool = Game.account.paths_above.has(str(e.id))
		var known: bool = Game.combat.knows_art(ch, str(e.art)) or Unlocks.is_unlocked(ch.id, str(e.art))
		var seen: bool = found or Game.account.visited_rooms.has(str(e.room))
		text(p + Vector2(0, 26), str(e.room_name) if seen else "? ? ?", 20, INK if seen else FADED, HORIZONTAL_ALIGNMENT_LEFT, 260)
		var status := Tx.t("ui.codex.paths_above_found") % str(e.reward) if found else (Tx.t("ui.codex.paths_above_open") if known else Tx.t("ui.codex.paths_above_later"))
		text(p + Vector2(260, 26), status, 16, RED_INK if found else (INK if known else FADED), HORIZONTAL_ALIGNMENT_RIGHT, 240)
		text(p + Vector2(0, 52), Tx.t("ui.codex.paths_above_needs") % [str(e.art_name), int(e.height)], 16, JADE_INK if known else FADED, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
		_rule(p.x, p.y + 66, TEXT_W, 0.3)
	_turn(int(ceil(rows.size() / float(ROWS_PAGE * 2))), Tx.t("ui.codex.turn_back"), Tx.t("ui.codex.turn_on"))

## S45 season calendar: which rare herbs flower in which season, and when each ripens. A place shows once visited.
func _seasons() -> void:
	var now := Clock.now_utc()
	var cur := HerbRules.season(now)
	var rares: Array = []
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if o.get("type", "") == "herb_patch" and o.has("ripen"): rares.append({"room": str(rid), "o": o})
	rares.sort_custom(func(a, b): return str(a.o.item) < str(b.o.item))
	_heads(Tx.t("ui.codex.head_seasons"), "", Tx.t("ui.codex.head_seasons"), "")
	text(Vector2(LEFT_X, 146), Tx.t("ui.codex.season_now") % [ContentDB.name_of("seasons", cur), UiKit.span(HerbRules.season_left_s(now))], 16, RED_INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W)
	var seasons: Array = ContentDB.all("seasons")
	var y := 184.0
	for i in seasons.size():
		var sd: Dictionary = seasons[i]
		if i == 2: y = 136.0
		var x := LEFT_X if i < 2 else RIGHT_X
		var now_s := str(sd.id) == cur
		text(Vector2(x, y + 22), str(sd.name), 26, RED_INK if now_s else INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W, true)
		if now_s: draw_rect(Rect2(x, y + 30, UiKit.text_width(str(sd.name), 26, true), 2), RED_INK)
		y += 34.0 + para(Rect2(x, y + 34, TEXT_W, 44), str(sd.get("desc", "")), 16, BROWN, 2) + 6.0
		for rn in rares:
			if str(rn.o.get("season", "")) == str(sd.id): y = _rare_line(rn, Vector2(x, y), TEXT_W)
		y += 12.0
	_rule(RIGHT_X, y, TEXT_W)
	text(Vector2(RIGHT_X, y + 32), Tx.t("ui.codex.no_season"), 22, INK, HORIZONTAL_ALIGNMENT_LEFT, TEXT_W, true)
	var col := 0
	var y2 := y + 46.0
	for rn in rares:
		if str(rn.o.get("season", "")) != "": continue
		_rare_line(rn, Vector2(RIGHT_X + col * 256.0, y2), 240.0)
		col += 1
		if col == 2:
			col = 0
			y2 += 46.0

func _rare_line(rn: Dictionary, at: Vector2, w: float) -> float:
	var o: Dictionary = rn.o
	icon_at(Rect2(at.x, at.y - 2, 32, 32), str(o.item))
	var seen: bool = Game.account.visited_rooms.has(str(rn.room))
	text(at + Vector2(38, 13), ContentDB.item_name(str(o.item)), 16, INK, HORIZONTAL_ALIGNMENT_LEFT, w - 38)
	var rp: Dictionary = o.get("ripen", {})
	var where := str(ContentDB.room(str(rn.room)).get("name", "")) if seen else "? ? ?"
	text(at + Vector2(38, 31), Tx.plural("ui.codex.ripens", int(rp.get("every_days", 1))) % [where, Tx.t("ui.herb.phase_" + str(rp.get("phase", "dawn"))), int(rp.get("every_days", 1))],
		14, BROWN, HORIZONTAL_ALIGNMENT_LEFT, w - 38)
	return at.y + 44

# ------------------------------------------------------------------ the Old Scrolls: the rubbing on its hanging scroll
## The old ladder's rungs in order, each with our realms that stand on it: [{name, realms: [{great, id, half, known}]}].
func _rungs() -> Array:
	var out: Array = []
	for e in ContentDB.all("codex"):
		if not str(e.id).begins_with("old_scrolls_") or str(e.get("rung", "")) == "": continue
		if out.is_empty() or str(out[-1].name) != str(e.rung): out.append({"name": str(e.rung), "realms": []})
		out[-1].realms.append({"great": str(e.id).trim_prefix("old_scrolls_"), "id": str(e.id), "half": str(e.get("half", "")), "known": Game.account.codex.has(str(e.id))})
	return out

func _scrolls(ch) -> void:
	var rungs := _rungs()
	var inked: int = rungs.filter(func(r): return r.realms.any(func(m): return m.known)).size()
	var you := ProgressionRules.great_realm(ch.cultivator.realm_key)
	if rung < 0 or rung >= inked:
		rung = inked - 1
		rung_realm = ""
		for i in inked:
			for m in rungs[i].realms:
				if m.great == you:
					rung = i
					rung_realm = you
	if rung >= 0 and rung_realm == "":
		for m in rungs[rung].realms:
			if m.known: rung_realm = m.great
	# The mount: brocade, silk, the two rods with their jade caps.
	var mount := Rect2(64, 104, 688, 592)
	glow(mount.grow(30), Color(UiKit.INK, 0.6))
	vshade(mount, UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.3), UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.55))
	_lattice(mount, 12.0, Color(UiKit.GOLD, 0.2))
	vshade(Rect2(80, 120, 656, 560), PAGE_TOP, UiKit.SURFACE.scroll)
	ground(Rect2(80, 120, 656, 560), UiKit.SURFACE.scroll)
	for rod in [Rect2(52, 96, 712, 16), Rect2(52, 690, 712, 20)]:
		rounded(rod, 8.0, UiKit.SURFACE.wood_dark)
		rounded(Rect2(rod.position + Vector2(2, 2), Vector2(rod.size.x - 4, rod.size.y * 0.4)), 5.0, UiKit.SURFACE.wood)
		for cx in [rod.position.x, rod.end.x]:
			draw_circle(Vector2(cx, rod.get_center().y + 2), 12.0, Color(UiKit.INK, 0.5), true, -1.0, true)
			draw_circle(Vector2(cx, rod.get_center().y), 11.0, UiKit.JADE_SHADOW, true, -1.0, true)
			draw_circle(Vector2(cx - 3, rod.get_center().y - 4), 5.0, UiKit.BRIGHT_JADE, true, -1.0, true)
	# The rubbing: bare paper, the ink tamped over the reached rungs from the top down.
	draw_rect(RUB, UiKit.PAPER.lerp(UiKit.SURFACE.scroll, 0.6))
	ground(RUB, UiKit.SURFACE.scroll)
	var pitch := minf(48.0, 440.0 / maxf(1.0, inked))
	var y0 := RUB.position.y + 54.0
	var ink_h := 54.0 + inked * pitch + 20.0 if inked > 0 else 0.0
	if inked > 0:
		var ink := Rect2(RUB.position, Vector2(RUB.size.x, ink_h - 26.0))
		draw_rect(ink, UiKit.SURFACE.rubbing)
		vshade(Rect2(ink.position.x, ink.end.y, ink.size.x, 26), UiKit.SURFACE.rubbing, Color(UiKit.SURFACE.rubbing, 0.0))
		ground(ink, UiKit.SURFACE.rubbing)
		for g in [[0.2, 0.15, 0.3, UiKit.HOLLOW], [0.75, 0.4, 0.35, UiKit.HOLLOW], [0.4, 0.7, 0.4, UiKit.INK], [0.85, 0.85, 0.3, UiKit.HOLLOW]]:
			var gc := Vector2(ink.position.x + ink.size.x * g[0], ink.position.y + ink.size.y * g[1])
			glow(Rect2(gc - Vector2(ink.size.x, ink.size.y) * g[2] * 0.5, Vector2(ink.size.x, ink.size.y) * g[2]), Color(g[3], 0.35))
		for i in 160:   # the paper's tooth through the ink, from a steady scatter
			var sx := fposmod(i * 97.13, ink.size.x)
			var sy := fposmod(i * 57.71 + i * i * 0.37, ink.size.y)
			draw_rect(Rect2(ink.position.x + sx, ink.position.y + sy, 1.5, 1.5), Color(UiKit.PAPER, 0.08))
		# The stone's rails, its cloud band, its chips and its crack, recorded in the ink.
		for rx in [ink.position.x + 14, ink.end.x - 17]:
			for yy in range(int(ink.position.y), int(ink.end.y), 60): draw_rect(Rect2(rx, yy, 3, 54), Color(UiKit.PAPER, 0.45))
		for row in 2:
			for k in range(0, 15):
				var cx := ink.position.x + 34 + k * 26 + row * 13
				if cx < ink.end.x - 30: draw_arc(Vector2(cx, ink.position.y + 30 + row * 15), 10.5, PI, TAU, 10, Color(UiKit.PAPER, 0.6), 2.5, true)
		for chip in [[40, 128, 7], [330, 236, 5], [360, 244, 3], [70, 402, 6], [300, 470, 4]]:
			if chip[1] < ink.size.y - 20: draw_circle(ink.position + Vector2(chip[0], chip[1]), chip[2], Color(UiKit.PAPER, 0.7), true, -1.0, true)
		if ink.size.y > 260:
			draw_line(ink.position + Vector2(250, 150), ink.position + Vector2(382, 220), Color(UiKit.PAPER, 0.35), 2.0, true)
			draw_line(ink.position + Vector2(381, 220), ink.position + Vector2(408, 282), Color(UiKit.PAPER, 0.25), 2.0, true)
	# The rungs reached, carved pale; the newest dabbed in as the page opens.
	var dab := 1.0 if UiKit.reduce_motion() else clampf((t - turned_at) / 0.4, 0.0, 1.0)
	for i in inked:
		var cy := y0 + i * pitch + pitch * 0.5
		var nm := str(rungs[i].name).to_upper()
		var size := 26
		while size > 22 and UiKit.text_width(nm, size, true) > RUB.size.x - 56: size -= 4
		var disp := UiKit.text_width(nm, size, true) <= RUB.size.x - 56
		if not disp: size = 18
		UiKit.draw_text(self, nm, Vector2(RUB.position.x, cy + size * 0.35 + 1), size, Color(UiKit.INK, 0.6), HORIZONTAL_ALIGNMENT_CENTER, RUB.size.x, true, disp)
		text(Vector2(RUB.position.x, cy + size * 0.35), nm, size, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, RUB.size.x, disp)
		for xx in range(int(RUB.position.x) + 18, int(RUB.end.x) - 18, 46): draw_rect(Rect2(xx, cy + pitch * 0.5 - 1, 40, 2), Color(UiKit.PAPER, 0.5))
		if i == inked - 1 and dab < 1.0: draw_rect(Rect2(RUB.position.x, cy - pitch * 0.5, RUB.size.x, pitch), Color(UiKit.PAPER.lerp(UiKit.SURFACE.scroll, 0.6), 1.0 - dab))
		region(Rect2(RUB.position.x + 18, cy - pitch * 0.5, RUB.size.x - 36, pitch), "rung", i)
		if i == rung: _ring(Vector2(RUB.get_center().x, cy), UiKit.text_width(nm, size, disp) * 0.5 + 20.0, pitch * 0.46)
		_gloss(rungs[i].realms, cy, pitch, you)
	# Below: the carving only felt through the bare paper, and the ink pad where the work stopped.
	var fy := RUB.position.y + ink_h + 10.0
	for j in rungs.size() - inked:
		if fy + j * 22 > RUB.end.y - 14: break
		var inset: float = [60.0, 110.0, 80.0, 110.0][j % 4]
		rounded(Rect2(RUB.position.x + inset, fy + j * 22, RUB.size.x - inset * 2.0 + (j % 3) * 10.0, 10), 3.0, Color(UiKit.PAPER, 0.55))
		draw_rect(Rect2(RUB.position.x + inset, fy + j * 22 + 8, RUB.size.x - inset * 2.0, 2), Color(UiKit.BRONZE, 0.18))
	if inked < rungs.size(): _dauber(Vector2(RUB.end.x - 70, minf(RUB.end.y - 30, RUB.position.y + ink_h + 40)))
	text(Vector2(522, 158), Tx.t("ui.codex.our_realms").to_upper(), 14, BROWN)
	if inked == 0: para(Rect2(522, 190, 200, 200), Tx.t("ui.codex.none_rubbed"), 14, BROWN)
	elif inked < rungs.size(): para(Rect2(538, y0 + inked * pitch + 24, 190, 100), Tx.t("ui.codex.rest_rubbed"), 14, BROWN)
	_note(rungs)

## The scholar's vermilion gloss beside a rung: our realms on it, with which half, "you" by your own; one not reached
## yet is "? ? ?".
func _gloss(realms: Array, cy: float, pitch: float, you: String) -> void:
	var x := 538.0
	if realms.size() == 1: draw_rect(Rect2(518, cy - 1, 12, 2), RED_INK)
	else:
		for s in [[Vector2(528, cy - 16), Vector2(528, cy + 16)], [Vector2(528, cy - 16), Vector2(534, cy - 18)], [Vector2(528, cy + 16), Vector2(534, cy + 18)]]:
			draw_line(s[0], s[1], RED_INK, 2.0, true)
	var one_line := realms.size() > 1 and pitch < 44.0
	var lines: Array = []
	for m in realms:
		var nm := ContentDB.name_of("realms", str(m.great) + "_1") if ContentDB.has_entry("realms", str(m.great) + "_1") else ContentDB.name_of("realms", str(m.great))
		nm = nm.rstrip("0123456789").strip_edges()
		lines.append([nm if m.known else "? ? ?", Tx.t("ui.codex.half_" + str(m.half)) if str(m.half) != "" and realms.size() > 1 else "", m.known, m.great == you])
	for li in lines.size():
		var ln: Array = lines[li]
		var y := cy + 6.0 if realms.size() == 1 or one_line else cy - 4.0 + li * 20.0
		var size := 14 if one_line else 16
		var lx := x + (0.0 if not one_line else li * 96.0)
		var room := 190.0 if not one_line else 90.0
		text(Vector2(lx, y), ln[0], size, RED_INK if ln[2] else FADED, HORIZONTAL_ALIGNMENT_LEFT, room)
		var nx := lx + minf(room, UiKit.text_width(ln[0], size)) + 6.0
		if ln[1] != "" and not one_line:
			text(Vector2(nx, y), ln[1], 14, BROWN, HORIZONTAL_ALIGNMENT_LEFT, 734 - nx)
			nx += UiKit.text_width(ln[1], 14) + 6.0
		if ln[3] and nx + 36 < 734:
			var tag := Rect2(nx, y - 14, UiKit.text_width(Tx.t("ui.codex.you"), 14) + 12, 18)
			rounded(tag, 3.0, UiKit.BLOOD)
			ground(tag, UiKit.BLOOD)
			text(Vector2(tag.position.x + 6, y), Tx.t("ui.codex.you"), 14, UiKit.PAPER)

## The vermilion ring round the chosen rung.
func _ring(c: Vector2, rx: float, ry: float) -> void:
	var pts := PackedVector2Array()
	for i in 49: pts.append(c + Vector2(cos(i * TAU / 48.0 - 0.05) * rx, sin(i * TAU / 48.0) * ry).rotated(-0.05))
	draw_polyline(pts, Color(UiKit.RED, 0.9), 3.0, true)

## The ink pad: a dark pad and the cloth ball resting on it.
func _dauber(p: Vector2) -> void:
	draw_set_transform(p, 0.0, Vector2(1.0, 0.36))
	draw_circle(Vector2(0, 20), 44.0, Color(UiKit.INK, 0.45), true, -1.0, true)
	draw_circle(Vector2.ZERO, 42.0, UiKit.SURFACE.rubbing.lerp(UiKit.HOLLOW, 0.25), true, -1.0, true)
	draw_set_transform(Vector2.ZERO)
	draw_circle(p + Vector2(0, -16), 22.0, UiKit.PAPER.lerp(UiKit.HOLLOW, 0.45), true, -1.0, true)
	draw_circle(p + Vector2(-6, -22), 10.0, UiKit.PAPER.lerp(UiKit.HOLLOW, 0.2), true, -1.0, true)
	rounded(Rect2(p + Vector2(-12, -44), Vector2(24, 14)), 6.0, UiKit.SURFACE.bridge.lerp(UiKit.BRONZE, 0.3))

## A diagonal lattice over `r` (the brocade), both ways, clipped to it.
func _lattice(r: Rect2, step: float, col: Color) -> void:
	for dir in [1.0, -1.0]:
		var c0 := -r.size.y
		while c0 < r.size.x:
			var x_a := maxf(0.0, c0)
			var x_b := minf(r.size.x, c0 + r.size.y)
			if x_b > x_a:
				var a := Vector2(x_a, x_a - c0)
				var b := Vector2(x_b, x_b - c0)
				if dir < 0.0:
					a.x = r.size.x - a.x
					b.x = r.size.x - b.x
				draw_line(r.position + a, r.position + b, col, 1.5)
			c0 += step * 2.0

## The chosen rung's note, pinned beside the scroll on a sheet with a printed vermilion frame.
func _note(rungs: Array) -> void:
	glow(SHEET.grow(24), Color(UiKit.INK, 0.55))
	vshade(SHEET, PAGE_TOP, UiKit.SURFACE.scroll)
	ground(SHEET, UiKit.SURFACE.scroll)
	draw_rect(SHEET.grow(-14), Color(UiKit.BLOOD, 0.7), false, 2.0)
	draw_rect(SHEET.grow(-19), Color(UiKit.BLOOD, 0.45), false, 1.0)
	draw_circle(Vector2(SHEET.get_center().x, SHEET.position.y + 12), 8.0, UiKit.JADE_SHADOW, true, -1.0, true)
	draw_circle(Vector2(SHEET.get_center().x - 2, SHEET.position.y + 10), 3.5, UiKit.BRIGHT_JADE, true, -1.0, true)
	var x := SHEET.position.x + 40
	var w := SHEET.size.x - 80
	var y := SHEET.position.y + 52
	if rung >= 0:
		var e := ContentDB.entry("codex", "old_scrolls_" + rung_realm)
		var half := str(e.get("half", ""))
		text(Vector2(x, y), str(e.get("title", "")).to_upper(), 14, RED_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
		text(Vector2(x, y + 42), str(rungs[rung].name), 34, INK, HORIZONTAL_ALIGNMENT_LEFT, w, true)
		if half != "": text(Vector2(x, y + 68), Tx.t("ui.codex.note_" + half), 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, w)
		draw_rect(Rect2(x, y + 84, w, 2), Color(UiKit.BLOOD, 0.45))
		var used := para(Rect2(x, y + 98, w, 200), str(e.get("body", "")), 20, INK, 6)
		text(Vector2(x, y + 128 + used), _facts(rung_realm), 16, BROWN, HORIZONTAL_ALIGNMENT_LEFT, w)
		y = minf(y + 150 + used, SHEET.end.y - 204)
	draw_rect(Rect2(x, y, w, 2), Color(UiKit.BLOOD, 0.45))
	var head := ContentDB.entry("codex", "old_scrolls")
	text(Vector2(x, y + 28), str(head.get("title", "")).to_upper(), 14, RED_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
	if Game.account.codex.has("old_scrolls"): para(Rect2(x, y + 38, w, 110), str(head.get("body", "")), 16, INK, 5)
	var seal := Rect2(x, SHEET.end.y - 62, 26, 26)
	rounded(seal, 4.0, Color(UiKit.BLOOD, 0.9))
	draw_rect(seal.grow(-3), Color(UiKit.PAPER, 0.6), false, 1.5)
	text(Vector2(x + 38, SHEET.end.y - 43), Tx.t("ui.codex.tap_rung"), 14, BROWN, HORIZONTAL_ALIGNMENT_LEFT, w - 38)

## A great realm's levels, its steps and its years (realms.json), as the note writes them.
func _facts(great: String) -> String:
	var rows: Array = ContentDB.all("realms").filter(func(r): return str(r.get("realm", "")) == great)
	if rows.is_empty(): return ""
	var first := int(rows[0].level)
	var last := int(rows[-1].level) + int(rows[-1].get("levels", 1)) - 1
	var lv := Tx.t("ui.codex.scroll_levels") % [first, last] if last > first else Tx.t("ui.codex.scroll_level") % first
	var key := "ui.codex.scroll_orders" if rows[0].get("order_style", false) else "ui.codex.scroll_stages"
	var steps := Tx.plural(key, rows.size())
	if steps.contains("%d"): steps = steps % rows.size()
	var yrs := int(rows[0].get("max_years", 0))
	return " · ".join([lv, steps, Tx.t("ui.codex.scroll_years") % UiKit.fmt(yrs) if yrs > 0 else Tx.t("ui.codex.scroll_endless")])

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"_tab":
			sel = ""
			contents = false
			turned_at = t
		"leaf":
			leaf[_id()] = int(leaf.get(_id(), 0)) + int(data)
			turned_at = t
		"contents": contents = not contents
		"claim_seal":   # decision 27: the Account authority grants the seal's gift; the page stamps it in
			if submit({"type": "claim_collection_seal", "page": str(data[0]), "seal": int(data[1])}).get("ok", false):
				stamped["%s:%d" % [data[0], int(data[1])]] = t
		"goto":
			leaf["collection"] = int(data)
			contents = false
			turned_at = t
		"rung":
			# A tap on the chosen rung turns to the next of our realms reached on it; another rung shows its latest.
			var realms: Array = _rungs()[int(data)].realms.filter(func(m): return m.known).map(func(m): return m.great)
			if int(data) == rung and realms.size() > 1: rung_realm = realms[(realms.find(rung_realm) + 1) % realms.size()]
			else: rung_realm = realms[-1]
			rung = int(data)
