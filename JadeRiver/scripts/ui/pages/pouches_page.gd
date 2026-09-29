extends Page
## S50 Keeping Post (V10): Tailor Xun sews a character's Qiankun pouch one tier deeper, one category at a time.
## A pouch has four compartments per category; a post stops filling a category when it is full.
## P5 (docs/page_identity.md row 44, the Post family): the tailor's chalked patterns on a bolt of cloth. Each category
## is a drawstring pouch chalked at its tier's size, the next tier dashed round it and its four compartments ruled
## inside, in two staggered rows; a bamboo ruler lies slantwise across a corner. Sewing runs a stitch round the pattern.

const CATS := ["ore", "herb", "fish", "insect", "material", "critter", "wisp"]
const CAT_ICON := {"ore": "copper_ore", "herb": "willow_moss", "fish": "river_minnow", "insect": "glowfly", "material": "hemp_cord",
	"critter": "jade_frog", "wisp": "spirit_wisp"}
## The patterns: four on the first row, three on the second set half a pitch in.
const CARD := Vector2(224, 232)
const PITCH := 240.0
const ROWS := [Vector2(160, 184), Vector2(280, 424)]
const STITCH_S := 0.4

var sewn := {}   # category -> page time its stitch started

func _init() -> void:
	title = Tx.t("ui.pouches.title")
	modal = true
	frame_rect = WINDOW_LARGE
	identity = Identity.new("cloth", false, "own", "chalk_patterns_staggered", 0.3)

func content_rect() -> Rect2:
	return Rect2(160, 136, 960, 512)

## The cutting cloth: a bolt of jade cloth with its selvage, a faint chalked grid and the bamboo ruler.
func draw_surface(r: Rect2) -> void:
	rounded(r.grow(2), 12.0, UiKit.INK)
	rounded(r, 10.0, UiKit.SURFACE.cloth)
	ground(r, UiKit.SURFACE.cloth)
	for x in range(int(r.position.x) + 40, int(r.end.x), 40):
		draw_line(Vector2(x, r.position.y + 12), Vector2(x, r.end.y - 12), Color(UiKit.PAPER, 0.04), 1.0)
	draw_rect(Rect2(r.position.x + 8, r.end.y - 22, r.size.x - 16, 6), Color(UiKit.JADE_SHADOW, 0.9))   # the selvage
	var o := Vector2(996, 636)
	var d := Vector2.from_angle(-0.5)
	var n := d.orthogonal() * 14.0
	draw_colored_polygon(PackedVector2Array([o - n, o - n + d * 150, o + n + d * 150, o + n]), UiKit.SURFACE.bamboo)
	for i in 15:
		var p := o - n + d * (8.0 + i * 10.0)
		draw_line(p, p + n.normalized() * (10.0 if i % 5 == 0 else 5.0), UiKit.PAPER_INK, 1.5)

func title_rect() -> Rect2:
	return Rect2(160, 72, 380, 56)

## The title on a hemp tag pinned to the cloth.
func draw_title_mount(r: Rect2) -> void:
	PostKit.hemp(self, r)
	draw_circle(Vector2(r.position.x + 14, r.get_center().y), 4.0, UiKit.SURFACE.peg_dark)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	para(Rect2(560, 70, 360, 60), Tx.t("ui.pouches.note") % str(ch.name), 14, UiKit.MIST, 3)
	currency_pill(Vector2(928, 82), "silver_tael", Game.economy.balance("silver_tael", ch))
	var rows: Array = ContentDB.config("posts").get("sewing", [])
	for i in CATS.size():
		var row: Vector2 = ROWS[0 if i < 4 else 1]
		_pattern(ch, str(CATS[i]), Rect2(row + Vector2(PITCH * (i if i < 4 else i - 4), 0), CARD), rows)
		tour_mark("pouches", Rect2(row + Vector2(PITCH * (i if i < 4 else i - 4), 0), CARD))   # decision 43: a tour's anchor

## A pattern's size across at `tier` of `tiers`: a deeper pouch is chalked larger.
static func size_of(tier: int, tiers: int) -> float:
	return 52.0 + 44.0 * float(tier) / maxf(1.0, float(tiers))

## One pouch: its chalk pattern at its tier's size, the next tier dashed round it, then its words and Sew.
func _pattern(ch, cat: String, r: Rect2, rows: Array) -> void:
	var tier := int(Game.posts.pouch(ch, cat).get("tier", 0))
	var s := size_of(tier, rows.size())
	var at := Vector2(r.get_center().x, r.position.y + 58)
	var chalk := Color(UiKit.PAPER, 0.7)
	_bag(at, s, chalk, unfold(), false)
	if tier < rows.size(): _bag(at, s + 10.0, Color(UiKit.PAPER, 0.35), 1.0, true)
	if sewn.has(cat):   # the stitch running round the new pattern
		var k := clampf((t - float(sewn[cat])) / STITCH_S, 0.0, 1.0)
		if k < 1.0 and not UiKit.reduce_motion(): _bag(at, s, UiKit.PALE_GOLD, k, true)
	icon_at(Rect2(at + Vector2(-16, s * 0.1 - 12), Vector2(32, 32)), str(CAT_ICON[cat]))
	var tier_name := Tx.t("ui.pouches.unsewn") if tier == 0 else str(rows[tier - 1].name)
	text(Vector2(r.position.x, r.position.y + 124), "%s · %s" % [Tx.t("ui.pouches.cat_" + cat), tier_name], 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	text(Vector2(r.position.x, r.position.y + 144), Tx.t("ui.pouches.holds") % [UiKit.fmt(int(Game.posts.capacity(ch, cat))), UiKit.fmt(int(Game.posts.held(ch, cat)))],
		14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	if tier >= rows.size():
		text(Vector2(r.position.x, r.position.y + 170), Tx.t("ui.pouches.finest"), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		return
	var nx: Dictionary = rows[tier]
	var parts: Array = []
	for need in nx.items: parts.append("%d %s" % [int(need.count), ContentDB.item_name(str(need.item))])
	var line := Tx.t("ui.pouches.next") % [str(nx.name), UiKit.fmt(int(nx.cap) * 4)] + " · " + Tx.t("ui.pouches.cost_list") % [UiKit.fmt(int(nx.taels)), ", ".join(parts)]
	para(Rect2(r.position.x, r.position.y + 148, r.size.x, 36), line, 14, UiKit.BRIGHT_JADE, 2)
	btn(Rect2(r.get_center().x - 60, r.end.y - 48, 120, 48), Tx.t("ui.pouches.sew"), "sew", cat, true, true, "", 18)

## A drawstring pouch in chalk, `s` px across, centred at `at`: the gathered neck, the round body, the four
## compartments ruled inside. `k` draws that share of the outline (the opening, a stitch); `dashed` for the next tier.
func _bag(at: Vector2, s: float, col: Color, k: float, dashed: bool) -> void:
	var pts := PackedVector2Array()
	var h := s * 0.5
	pts.append(at + Vector2(-h * 0.45, -h))
	for i in 25:   # the body: from the neck's left, bulging round the bottom to its right
		var a := deg_to_rad(150.0 + 240.0 * float(i) / 24.0)
		pts.append(at + Vector2(cos(a) * h, -sin(a) * h * 0.9 + h * 0.1))
	pts.append(at + Vector2(h * 0.45, -h))
	var n := maxi(2, int(pts.size() * clampf(k, 0.0, 1.0)))
	var line := pts.slice(0, n)
	if dashed:
		for i in range(0, line.size() - 1, 2): draw_line(line[i], line[i + 1], col, 2.0, true)
	else:
		draw_polyline(line, col, 2.0, true)
	if dashed or k < 1.0: return
	draw_line(at + Vector2(-h * 0.55, -h - 4), at + Vector2(h * 0.55, -h - 4), col, 2.0, true)   # the drawstring
	draw_line(at + Vector2(0, -h * 0.55), at + Vector2(0, h * 0.95), Color(col, col.a * 0.5), 1.0)
	draw_line(at + Vector2(-h * 0.9, h * 0.2), at + Vector2(h * 0.9, h * 0.2), Color(col, col.a * 0.5), 1.0)

func on_action(id: String, data) -> void:
	if id == "sew":
		var r := submit({"type": "sew_pouch", "category": str(data)})
		if r.get("ok", false):
			sewn[str(data)] = t
			flash(Tx.t("ui.pouches.sewn") % UiKit.fmt(int(r.cap)))
