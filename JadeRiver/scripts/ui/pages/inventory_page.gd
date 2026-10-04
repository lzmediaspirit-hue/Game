extends Page
## Bag (S14, Part 9.6), P5 as concept B, the heaven in the gourd (docs/page_identity.md row 3; mockups 07_bag_b,
## 07_bag_b_card, 07_bag_b_pill and 08_bag_b_empty; decisions 8, 15 and 24). No gourd is drawn and no frame: the page
## is the world inside the character's Spirit Gourd, a night sky over a sea of cloud with far islands, and a bigger
## gourd is a wider heaven (more stars and islands, light from its mouth once it is large). What is carried floats in it
## as one grid ten across, five rows in view and the next fading into the cloud, the next gourd's spaces locked at its
## end; the Key Pouch, the kinds and Sort are floating jade tokens. The figure stands on its own island with the eight
## worn slots riding a gold orbit round it (the self family's CharacterPage.draw_worn). A tapped thing opens a small card
## beside its space: what it is, what it does or what wearing it would make of your own totals (StatRules.equip_change),
## and two or three actions, the rest under "···". The page submits intents only.

const CharacterPage = preload("res://scripts/ui/pages/character_page.gd")
const COLS := 10
const PITCH := 80.0                        # a 76 px slot and its gap
const IN_VIEW := 5                         # rows in view; the next fades into the cloud
const FIELD := Vector2(412, 176)           # the grid's top-left
const FIELD_W := COLS * PITCH - 4.0
const TOKEN_Y := 50.0                      # the tabs and purses, level with the close button
const KIND_Y := 112.0
## The worn slots riding the orbit round the figure (each 76 px slot's top-left); the orbit runs through their centres.
const WORN := {"hat": Vector2(113, 192), "weapon": Vector2(279, 192), "robe": Vector2(67, 310), "gourd": Vector2(325, 310),
	"trousers": Vector2(67, 426), "cape": Vector2(325, 426), "boots": Vector2(113, 544), "talisman": Vector2(279, 544)}
const ORBIT := Vector2(234, 406)
const ORBIT_R := Vector2(134, 224)
const FEET := Vector2(228, 598)
const TOP_SCALE := 5      # the character's figure (TopdownDoll), screen px an art px (decision 43: 46 px at x5)
const CARD_W := 312.0
const CARD_IN := CARD_W - 28.0
const KINDS := ["all", "gear", "pills", "materials", "other"]
const POUCH_ICON := "mudwater_key"
## The card's comparison names these (the Character register's own words, and the pools).
const POOLS := [["max_hp", "ui.inventory.max_hp"], ["max_qi", "ui.inventory.max_qi"], ["max_soul", "ui.inventory.max_soul"],
	["combat_power", "ui.character.combat_power"]]
## Far islands in the order a growing gourd adds them: [centre, width, depth (0 near .. 1 far)].
const ISLES := [[Vector2(1196, 672), 112.0, 0.35], [Vector2(40, 684), 88.0, 0.5], [Vector2(1262, 330), 60.0, 0.8],
	[Vector2(350, 146), 72.0, 0.65], [Vector2(1090, 708), 96.0, 0.55]]

var sel := {}          # {"bag": index} | {"slot": name} | {"key": index}
var kind := "all"      # the kind the grid shows
var more := false      # the card's "···" actions shown
var sort_by := "type"
var doll: TopdownDoll  # the figure, drawn among the page's own layers (Figures.draw_on), under the card
var tier := 0          # how far up the gourd ladder: the sky grows with it
var stars: Array = []  # [position, radius, colour, bright]
var anchor := Rect2()  # the chosen thing's space as drawn this frame
var change: Array = [] # StatRules.equip_change for the chosen piece, kept until the bag or the stats change
var change_of := -1

func _init() -> void:
	title = Tx.t("ui.inventory.bag")
	tabs = [{"id": "bag", "label": Tx.t("ui.inventory.spirit_gourd")}, {"id": "key", "label": Tx.t("ui.inventory.key_pouch")}]
	identity = Identity.new("sky", false, "own", "open_sky_grid_orbit", 0.3)
	grade_rims = true

func content_rect() -> Rect2:
	return Rect2(FIELD, Vector2(FIELD_W + GUTTER, 512))

func setup() -> void:
	var ch = c()
	# Decision 42: the character as the game draws it.
	if not is_instance_valid(doll):
		doll = Figures.for_character()
		doll.visible = false
		add_child(doll)
	if ch == null: return
	_refresh_doll()
	tier = maxi(0, (ch.inventory.capacity() - ch.inventory.bonus_slots - InventoryState.base_capacity()) / 5)
	# A few burn bright with a cross of light, but never among the words and spaces.
	stars = scatter_stars(150 + tier * 50, Rect2(0, 0, 1280, 640), [Rect2(FIELD - Vector2(12, 72), Vector2(FIELD_W + 32, 600)), Rect2(56, 40, 320, 80)])
	# Opened on a worn slot (from the Character page) or on a thing in the bag.
	if WORN.has(str(args.get("tab", ""))) and ch.inventory.equipped.get(str(args.tab)) != null: sel = {"slot": str(args.tab)}
	if args.has("index"): sel = {"bag": int(args.index)}

func _refresh_doll() -> void:
	if c() == null or not is_instance_valid(doll): return
	Figures.dress(doll, InventoryAuthority.outfit_for(c()))
	doll.play("idle")

func on_event(name: String, _p: Dictionary) -> void:
	if name in ["equipment_changed", "item_added", "item_removed"]: _refresh_doll()
	if name in ["equipment_changed", "item_added", "item_removed", "bag_changed", "stats_changed"]: change_of = -1
	queue_redraw()

# ------------------------------------------------------------------ the sky's pieces, shared (page_identity §8.6)
## "Your bag" beside another page (the Shop, the Storage; decision 24) is a patch of this same heaven, drawn from these.

## `n` stars scattered steadily over `area`, [position, radius, colour, bright]; the bright ones keep out of `clear`.
static func scatter_stars(n: int, area: Rect2, clear: Array) -> Array:
	var out: Array = []
	for i in n:
		var s := HashNoise.scatter(i, 3)
		var at := area.position + Vector2(HashNoise.scatter(i, 1) * area.size.x, pow(HashNoise.scatter(i, 2), 1.35) * area.size.y)
		var bright := s > 0.985 and not clear.any(func(r): return (r as Rect2).has_point(at))
		out.append([at, 1.4 if s > 0.9 else (1.0 if s > 0.6 else 0.7),
			Color([UiKit.PALE_GOLD, UiKit.PAPER, UiKit.MIST][0 if s > 0.8 else (1 if s > 0.4 else 2)], 0.25 + HashNoise.scatter(i, 4) * 0.6), bright])
	return out

## The night over `r`: deepening from INK to the gourd's jade-dark and down to the sky's lightest.
static func night(pg: Page, r: Rect2) -> void:
	var half := roundf(r.size.y * 0.5)
	pg.vshade(Rect2(r.position, Vector2(r.size.x, half)), UiKit.INK, UiKit.SURFACE.space)
	pg.vshade(Rect2(r.position.x, r.position.y + half, r.size.x, r.size.y - half), UiKit.SURFACE.space, UiKit.SURFACE.sky)

static func draw_stars(pg: Page, stars: Array) -> void:
	for s in stars:
		if s[3]:
			pg.glow(Rect2(s[0] - Vector2(7, 7), Vector2(14, 14)), Color(UiKit.PALE_GOLD, 0.8))
			pg.draw_line(s[0] - Vector2(7, 0), s[0] + Vector2(7, 0), Color(UiKit.PAPER, 0.7), 1.0)
			pg.draw_line(s[0] - Vector2(0, 7), s[0] + Vector2(0, 7), Color(UiKit.PAPER, 0.7), 1.0)
		else: pg.draw_circle(s[0], s[1], s[2], true, -1.0, true)

## Light falling from the gourd's mouth far above, two shafts spreading down from `top` (x, the shafts' centre) to `foot` (y).
static func mouth_light(pg: Page, x: float, foot: float, spread := 1.0) -> void:
	for sh in [[-60.0, 60.0, -230.0, 310.0, foot], [-10.0, 20.0, -90.0, 100.0, foot * 0.8125]]:
		pg.draw_polygon(PackedVector2Array([Vector2(x + sh[0], -10), Vector2(x + sh[1], -10), Vector2(x + sh[3] * spread, sh[4]), Vector2(x + sh[2] * spread, sh[4])]),
			PackedColorArray([Color(UiKit.PALE_GOLD, 0.1), Color(UiKit.PALE_GOLD, 0.1), Color(UiKit.PALE_GOLD, 0.0), Color(UiKit.PALE_GOLD, 0.0)]))

## The sea of cloud along the foot of `r` (the band from `top` down): a pale wash and three soft banks.
static func cloud_sea(pg: Page, r: Rect2, top: float) -> void:
	var w := r.size.x
	for sea in [[0.14, 74.0, 0.415, 84.0, UiKit.PAPER, 0.12], [0.59, 92.0, 0.57, 98.0, UiKit.PAPER, 0.13], [0.906, 64.0, 0.46, 70.0, UiKit.MIST, 0.12]]:
		var c := Vector2(r.position.x + w * float(sea[0]), top + float(sea[1]))
		var sz := Vector2(w * float(sea[2]), float(sea[3]))
		pg.glow(Rect2(c - sz * 0.5, sz), Color(sea[4], sea[5]))
	pg.vshade(Rect2(r.position.x, top, w, r.end.y - top), Color(UiKit.SURFACE.silk, 0.0), Color(UiKit.SURFACE.silk, 0.26))

## A thing's space in the sky: an empty one lets the sky show through; a locked one (the next gourd's) is dark with its lock.
static func empty_space(pg: Page, r: Rect2) -> void:
	pg.rounded(r, 5.0, Color(UiKit.SURFACE.space, 0.55))
	pg.draw_rect(r.grow(-1.5), Color(UiKit.JADE, 0.45), false, 1.5)

static func locked_space(pg: Page, r: Rect2) -> void:
	pg.rounded(r, 6.0, Color(UiKit.INK, 0.45))
	pg.draw_rect(r.grow(-1), Color(UiKit.HOLLOW, 0.2), false, 1.0)
	pg.lock_icon(r.get_center() - Vector2(8.4, 11.0), 1.4)

## The ink shadow a floating thing casts on the cloud below its space.
static func float_shadow(pg: Page, r: Rect2) -> void:
	pg.glow(Rect2(r.position + Vector2(-8, 46), Vector2(92, 46)), Color(UiKit.INK, 0.55))

# ------------------------------------------------------------------ the sky
## The world inside the gourd over the whole screen: night deepening to the gourd's jade-dark, the lights of the sky,
## its stars, light from the mouth far above once the gourd is large, far islands, the sea of cloud, the figure's island
## and the orbit its worn slots ride.
func draw_surface(_r: Rect2) -> void:
	var w := size.x
	night(self, Rect2(Vector2.ZERO, size))
	for gl in [[Vector2(700, -60), Vector2(728, 420), UiKit.PALE_GOLD, 0.14], [Vector2(1040, 250), Vector2(868, 504), UiKit.SOUL, 0.12],
			[Vector2(330, 180), Vector2(784, 448), UiKit.QI, 0.08], [Vector2(760, 520), Vector2(1260, 588), UiKit.JADE, 0.1]]:
		glow(Rect2(gl[0] - gl[1] * 0.5, gl[1]), Color(gl[2], gl[3]))
	draw_stars(self, stars)
	if tier >= 3: mouth_light(self, 700.0, 640.0)
	var far: Array = ISLES.slice(0, clampi(tier, 1, ISLES.size()))
	far.sort_custom(func(a, b): return a[2] > b[2])
	for i in far.size(): island(self, far[i][0], far[i][1], far[i][2], i + 1)
	cloud_sea(self, Rect2(Vector2.ZERO, size), 620.0)
	ground(Rect2(Vector2.ZERO, size), UiKit.SURFACE.sky)
	ground(Rect2(0, size.y - 64, w, 64), UiKit.SURFACE.sea)
	# The figure's own island, its shadow, and the gold orbit through the worn slots.
	glow(Rect2(FEET + Vector2(-120, -8), Vector2(240, 60)), Color(UiKit.JADE, 0.12))
	island(self, FEET + Vector2(4, 4), 188.0, 0.0, 0)
	var ring := PackedVector2Array()
	for i in 97: ring.append(ORBIT + Vector2(sin(i * TAU / 96.0), -cos(i * TAU / 96.0)) * ORBIT_R)
	draw_polyline(ring, Color(UiKit.GOLD, 0.16), 7.0, true)
	for i in 144: draw_circle(ORBIT + Vector2(sin(i * TAU / 144.0), -cos(i * TAU / 144.0)) * ORBIT_R, 1.0, Color(UiKit.GOLD, 0.75), true, -1.0, true)

## A floating rock `w` wide centred on `at`: a gently domed top and a jagged underside tapering to a point. Far ones
## (depth towards 1) are smaller in the eye, hazier and carry pines, the big ones a pavilion; depth 0 is the figure's,
## with a lit jade top to stand on.
static func island(pg: Page, at: Vector2, w: float, depth: float, k: int) -> void:
	var a := 1.0 - depth * 0.55
	var top := PackedVector2Array()
	var outline := PackedVector2Array()
	var cols := PackedColorArray()
	for i in 10:
		var t := i / 9.0
		top.append(at + Vector2(w * (t - 0.5), -sin(PI * t) * w * 0.07 - (HashNoise.scatter(k * 31 + i, 5) - 0.5) * w * 0.02))
	outline.append_array(top)
	for i in range(8, 0, -1):
		var u := i / 9.0
		outline.append(at + Vector2(w * (u - 0.5) + (HashNoise.scatter(k * 31 + i, 6) - 0.5) * w * 0.05, sin(PI * u) * w * 0.62 * (0.55 + HashNoise.scatter(k * 31 + i, 7) * 0.45)))
	var rock_top: Color = UiKit.SURFACE.silk.lerp(UiKit.SURFACE.sky, depth * 0.5)
	for i in outline.size(): cols.append(Color(rock_top if i < 10 else UiKit.SURFACE.space, a))
	pg.glow(Rect2(at + Vector2(-w * 0.6, w * 0.16), Vector2(w * 1.2, w * 0.32)), Color(UiKit.JADE, 0.05 + (1.0 - depth) * 0.05))
	pg.draw_polygon(outline, cols)
	outline.append(outline[0])
	pg.draw_polyline(outline, Color(UiKit.BRIGHT_JADE, (0.18 + (1.0 - depth) * 0.2) * a), 1.0, true)
	if depth == 0.0:
		var face := PackedVector2Array()
		var fc := PackedColorArray()
		for i in 48:
			var p := at + Vector2(cos(i * TAU / 48.0) * w * 0.5, 2.0 + sin(i * TAU / 48.0) * w * 0.075)
			face.append(p)
			fc.append(UiKit.JADE.lerp(UiKit.JADE_SHADOW, clampf((p.y - at.y + w * 0.075) / (w * 0.15), 0.0, 1.0)))
		pg.draw_polygon(face, fc)
		face.append(face[0])
		pg.draw_polyline(face, UiKit.BRIGHT_JADE, 1.5, true)
		return
	pg.draw_polyline(top, Color(UiKit.JADE, a), maxf(2.0, w * 0.035), true)
	for t in maxi(1, roundi(w / 60.0)):
		var tx := at.x - w * 0.3 + HashNoise.scatter(k * 7 + t, 8) * w * 0.6
		var th := w * (0.12 + HashNoise.scatter(k * 7 + t, 9) * 0.08)
		var tree := PackedVector2Array([Vector2(tx, at.y - th), Vector2(tx + th * 0.35, at.y - 1), Vector2(tx - th * 0.35, at.y - 1)])
		pg.draw_colored_polygon(tree, Color(UiKit.JADE_SHADOW, a))
		tree.append(tree[0])
		pg.draw_polyline(tree, Color(UiKit.BRIGHT_JADE, 0.35 * a), 1.0, true)
	if w > 110.0:
		var px := at.x + w * 0.12
		var pw := w * 0.2
		pg.draw_rect(Rect2(px - pw * 0.3, at.y - pw * 0.5, pw * 0.6, pw * 0.5), Color(UiKit.SURFACE.wood_dark, a))
		pg.draw_colored_polygon(PackedVector2Array([Vector2(px - pw * 0.62, at.y - pw * 0.46), Vector2(px + pw * 0.62, at.y - pw * 0.46),
			Vector2(px + pw * 0.4, at.y - pw * 0.8), Vector2(px - pw * 0.4, at.y - pw * 0.8)]), Color(UiKit.BRONZE, a))
		pg.draw_circle(Vector2(px, at.y - pw * 0.25), pw * 0.09, Color(UiKit.GOLD, a), true, -1.0, true)

func title_rect() -> Rect2:
	return Rect2(68, 44, ceilf(UiKit.text_width(title, UiKit.D_TITLE, true)) + 24, 48)

## Decision 43: the "?" beside the title (the tabs and purses take the row left of the close button).
func help_rect() -> Rect2:
	var tr := title_rect()
	return Rect2(tr.end.x + 12, roundf(tr.get_center().y - 26), 52, 52)

## No mount: the title floats in the night, a little ink behind it.
func draw_title_mount(r: Rect2) -> void:
	glow(r.grow(16), Color(UiKit.INK, 0.45))

func tab_rects() -> Array:
	var n := _pouch_count()
	var w0 := ceilf(UiKit.text_width(str(tabs[0].label), 18)) + 40
	var w1 := ceilf(UiKit.text_width(str(tabs[1].label), 18) + UiKit.text_width(n, 16)) + 82
	return [Rect2(FIELD.x, TOKEN_Y, w0, TAB_H), Rect2(FIELD.x + w0 + 16, TOKEN_Y, w1, TAB_H)]

func draw_tab(r: Rect2, i: int, state: String) -> void:
	token(self, r, str(tabs[i].label), _pouch_count() if i == 1 else "", state == "selected", state == "disabled", POUCH_ICON if i == 1 else "")

func _pouch_count() -> String:
	return str(c().inventory.key_items.size()) if c() != null else ""

## A jade token floating in the sky (a tab, a kind): its label and count; the chosen one lit, its label inked.
static func token(pg: Page, r: Rect2, label: String, count: String, on: bool, dim := false, icon := "") -> void:
	if on: pg.glow(r.grow(12), Color(UiKit.GOLD, 0.22))
	pg.face(r, "sky_token", "selected" if on else "normal")
	var x := r.position.x + 20
	if icon != "":
		pg.icon_at(Rect2(x - 4, r.position.y + 8, 32, 32), icon)
		x += 34
	var y := r.position.y + 31
	if on: pg.inked(Vector2(x, y), label, 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, false)
	else: pg.text(Vector2(x, y), label, 18, UiKit.HOLLOW if dim else UiKit.PAPER)
	if count != "": pg.text(Vector2(x + UiKit.text_width(label, 18) + 8, y), count, 16, UiKit.PALE_GOLD if on else (UiKit.HOLLOW if dim else UiKit.MIST))

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var inv: InventoryState = ch.inventory
	anchor = Rect2()
	region(Rect2(frame_rect.position.x, KIND_Y - 8, frame_rect.size.x, frame_rect.end.y - KIND_Y + 8), "sky")   # a tap on open sky puts the card away
	var gourd = inv.equipped.get("gourd")
	text(Vector2(70, 110), Tx.t("ui.inventory.heaven_of") % (ContentDB.item_name(str(gourd.id)) if gourd != null else Tx.t("ui.inventory.spirit_gourd")), 14, UiKit.MIST)
	_purses(ch)
	# The figure on its island, then the worn slots riding in along the orbit as the page opens.
	glow(Rect2(FEET + Vector2(-64, -10), Vector2(128, 22)), Color(UiKit.INK, 0.45))
	Figures.draw_on(doll, self, FEET, TOP_SCALE)
	var ringed := str(sel.get("slot", ""))
	var chosen = selected_item()
	if sel.has("bag") and chosen != null: ringed = str(ContentDB.item(str(chosen.id)).get("slot", ""))
	draw_set_transform_matrix(Transform2D((unfold() - 1.0) * 0.6, ORBIT) * Transform2D(0.0, -ORBIT))
	CharacterPage.draw_worn(self, ch, WORN, "slot", UiKit.MIST, ringed)
	draw_set_transform_matrix(Transform2D.IDENTITY)
	if sel.has("slot"): anchor = Rect2(WORN[str(sel.slot)], Vector2(SLOT, SLOT))
	var spaces := _spaces(ch)
	var bag := str(tabs[tab].id) == "bag"
	if bag:
		var x := FIELD.x
		for k in KINDS:
			var label := Tx.t("ui.inventory.kind_" + k)
			var n := kind_count(inv, k)
			var r := Rect2(x, KIND_Y, ceilf(UiKit.text_width(label, 18) + UiKit.text_width(str(n), 16)) + 48, TAB_H)
			token(self, r, label, str(n), kind == k, n == 0)
			region(r, "kind", k)
			x = r.end.x + 8
		btn(Rect2(FIELD.x + FIELD_W - 96, KIND_Y, 96, BTN_H), Tx.t("ui.inventory.sort"), "sort", null, false, true, "", 20)
	var foot := _grid(ch, spaces)
	if not bag and spaces.is_empty(): text(FIELD + Vector2(0, 40), Tx.t("ui.inventory.no_key_items"), 20, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, FIELD_W)
	var card := _place_card(ch, chosen, foot) if chosen != null and anchor != Rect2() else {}
	# The line under the grid gives way to a card that needs its room; the empty state's hint gives way to any card.
	if bag and (card.is_empty() or (card.rect as Rect2).end.y < foot + 8): _space_line(ch, foot + 30)
	if bag and card.is_empty() and kind == "all" and ceili(spaces.size() / float(COLS)) <= 3: _hint(ch, foot + 62)
	if not card.is_empty(): _draw_card(card)

## Silver taels and Spirit Stones, and the rarer purses once they hold something, right to left beside the close button.
func _purses(ch) -> void:
	var shown: Array = []   # [currency, amount, width], the everyday ones first; the rarest give way when room is short
	for cur in ["silver_tael", "spirit_stone", "sage_crystal", "star_jade"]:
		var amt: int = Game.economy.balance(cur, ch)
		if amt > 0 or cur in ["spirit_stone", "silver_tael"]: shown.append([cur, amt, ceilf(UiKit.text_width(UiKit.fmt(amt), 18)) + 66])
	var x := frame_rect.end.x - 88.0
	while shown.size() > 1 and shown.reduce(func(t, p): return t + float(p[2]), 0.0) > x - (tab_rects()[-1] as Rect2).end.x - 4.0: shown.pop_back()
	for i in range(shown.size() - 1, -1, -1):
		x -= float(shown[i][2])
		currency_pill(Vector2(x, TOKEN_Y + 7), str(shown[i][0]), int(shown[i][1]))

## What the grid shows: bag indices (every space and then the next gourd's, locked, as -1; or only the chosen kind's
## things) for the Spirit Gourd, key item indices for the Key Pouch.
func _spaces(ch) -> Array:
	var inv: InventoryState = ch.inventory
	if str(tabs[tab].id) == "key": return range(inv.key_items.size())
	var out: Array = []
	for i in inv.bag.size():
		if kind == "all" or (inv.bag[i] != null and InventoryAuthority.bag_kind(str(inv.bag[i].id)) == kind): out.append(i)
	if kind == "all":
		for k in _next(ch)[1]: out.append(-1)
	return out

## The next gourd up the ladder and how many more spaces it holds ([{}, 0] at the top).
func _next(ch) -> Array:
	var nx := InventoryAuthority.next_gourd(ch)
	return [nx, int(nx.gourd.bag) - (ch.inventory.capacity() - ch.inventory.bonus_slots) if not nx.is_empty() else 0]

func kind_count(inv: InventoryState, k: String) -> int:
	return inv.bag.filter(func(s): return s != null and (k == "all" or InventoryAuthority.bag_kind(str(s.id)) == k)).size()

## The grid, rising from the cloud as the page opens: the rows in view, and the next fading into the cloud below them
## (drag the grid to bring it up). Returns the foot of what shows.
func _grid(ch, spaces: Array) -> float:
	var rows := ceili(spaces.size() / float(COLS))
	var view := Rect2(FIELD, Vector2(FIELD_W + GUTTER, mini(rows, IN_VIEW) * PITCH))
	draw_set_transform(Vector2(0, roundf((1.0 - unfold()) * 48.0)))
	list("grid", view, rows, PITCH, func(row: int, rr: Rect2): _row(ch, spaces, row, rr.position, true))
	var off := float(scroll.get("grid", 0.0))
	var nxt := ceili((off + view.size.y) / PITCH - 0.01)
	var foot := view.end.y
	if nxt < rows:
		var y := FIELD.y + nxt * PITCH - off
		_row(ch, spaces, nxt, Vector2(FIELD.x, y), false)
		vshade(Rect2(FIELD.x - 8, y - 6, FIELD_W + 16, PITCH + 2), Color(UiKit.SURFACE.sky, 0.0), Color(UiKit.SURFACE.sky, 0.9))
		foot = y + PITCH - 4
	draw_set_transform(Vector2.ZERO)
	return foot

## One row of spaces from `at`; `live` rows take taps (the fading one does not).
func _row(ch, spaces: Array, row: int, at: Vector2, live: bool) -> void:
	var inv: InventoryState = ch.inventory
	var key := str(tabs[tab].id) == "key"
	var id := "key" if key else "bag"
	for col in COLS:
		var k := row * COLS + col
		if k >= spaces.size(): return
		var i: int = spaces[k]
		var r := Rect2(at + Vector2(col * PITCH, 0), Vector2(SLOT, SLOT))
		var s = null if i < 0 else (inv.key_items[i] if key else inv.bag[i])
		if i < 0:
			# One of the next gourd's spaces: locked, and a tap names the gourd that opens it.
			locked_space(self, r)
			if live: region(r, "next_space", null, false, _next_line(ch))
		elif s == null:
			# An empty space: the sky shows through it.
			empty_space(self, r)
			if live: region(r, id, i)
		else:
			float_shadow(self, r)
			var chosen := int(sel.get(id, -1)) == i
			slot_box(r, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), id if live else "", i, chosen,
				not key and inv.locked.has(int(s.get("uid", -1))))
			# Decision 43: the first piece of gear in view is the one the first-gear guide points at.
			if not key and live and not tour_marks.has("gear") and InventoryAuthority.bag_kind(str(s.id)) == "gear": tour_mark("gear", r)
			# Decision 44: the first weapon (a spare to set) and the first treasure in view, for the weapon swap's and the
			# treasures' guides.
			if not key and live:
				var sdef := ContentDB.item(str(s.id))
				if not tour_marks.has("weapon") and str(sdef.get("slot", "")) == "weapon": tour_mark("weapon", r)
				if not tour_marks.has("treasure_item") and sdef.has("treasure"): tour_mark("treasure_item", r)
			if not key:
				pill_marks(r, int(s.get("marks", 0)))
				if inv.new_items.has(str(s.id)): draw_circle(r.position + Vector2(SLOT - 8, 8), 5, UiKit.BRIGHT_JADE)
			if chosen and live: anchor = r

## "Space 41 / 55" and, while a bigger gourd exists, what it holds.
func _space_line(ch, y: float) -> void:
	var inv: InventoryState = ch.inventory
	text(Vector2(FIELD.x, y), Tx.t("ui.inventory.space"), 16, UiKit.MIST)
	var x := FIELD.x + UiKit.text_width(Tx.t("ui.inventory.space") + " ", 16)
	var used := "%d / %d" % [inv.bag.size() - inv.free_slots(), inv.capacity()]
	text(Vector2(x, y + 1), used, 22, UiKit.PALE_GOLD)
	x += UiKit.text_width(used, 22) + 18
	var line := _next_line(ch)
	if line == "": return
	lock_icon(Vector2(x, y - 15))
	text(Vector2(x + 20, y), line, 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, FIELD.x + FIELD_W - x - 20)

func _next_line(ch) -> String:
	var nx: Array = _next(ch)
	if (nx[0] as Dictionary).is_empty(): return ""
	return Tx.plural("ui.inventory.next_gourd", int(nx[1])) % [ContentDB.item_name(str(nx[0].id)), int(nx[0].gourd.bag), int(nx[1])]

## The empty state (mockup 08_bag_b_empty): while the gourd is small the open sky under the grid says how things come
## in, what to do with loose finds, and to tap a thing, with the piece that fits an empty slot and what opens the rest.
func _hint(ch, y: float) -> void:
	var find := ""
	for s in ch.inventory.bag:
		if s != null and InventoryAuthority.bag_kind(str(s.id)) in ["materials", "other"] and LootRules.sell_price(str(s.id)) > LootRules.sell_price(find):
			find = str(s.id)
	var fits := ""
	for slot in WORN:
		var piece := CharacterPage.wearable_in_bag(ch, slot) if ch.inventory.equipped.get(slot) == null and CharacterPage.locked_reason(ch, slot) == "" else ""
		if piece != "" and fits == "": fits = " " + Tx.t("ui.inventory.hint_fits") % [ContentDB.item_name(piece), Tx.t("ui.inventory." + slot).to_lower()]
	var box := Rect2(FIELD.x, y, FIELD_W, 60)
	for ln in [[Tx.t("ui.inventory.hint_walk_lead"), Tx.t("ui.inventory.hint_walk")],
			[Tx.t("ui.inventory.hint_sell_lead"), Tx.plural("ui.inventory.hint_sell", LootRules.sell_price(find)) % [ContentDB.item_name(find), LootRules.sell_price(find)] if find != "" else Tx.t("ui.inventory.hint_sell_plain")],
			[Tx.t("ui.inventory.hint_tap_lead"), Tx.t("ui.inventory.hint_tap") + fits]]:
		box.position.y += rich(box, [["✦", UiKit.GOLD], [ln[0], UiKit.PALE_GOLD], [ln[1], UiKit.PAPER]], 18, true) + 10
	var later: Array = WORN.keys().filter(func(sl): return CharacterPage.locked_reason(ch, sl) != "").map(func(sl): return Tx.t("ui.inventory.later_" + sl))
	if not later.is_empty():
		rich(Rect2(box.position + Vector2(128, 8), Vector2(FIELD_W - 256, 60)), [[Tx.t("ui.inventory.opens_later"), UiKit.GOLD], [", ".join(later) + ".", UiKit.MIST]], 16, true)

# ------------------------------------------------------------------ the card
func selected_item():
	var inv: InventoryState = c().inventory
	if sel.has("bag"):
		var i := int(sel.bag)
		return inv.bag[i] if i >= 0 and i < inv.bag.size() else null
	if sel.has("slot"): return inv.equipped.get(str(sel.slot))
	if sel.has("key"):
		var k := int(sel.key)
		return inv.key_items[k] if k >= 0 and k < inv.key_items.size() else null
	return null

## Where the chosen thing's card goes (decision 15), as tall as its rows: {rect, side, rows}. It opens below the space on
## the grid's top row, to its right from the grid's first columns (and beside the orbit for a worn piece), else to its
## left; it keeps above the line under the grid while it fits there.
func _place_card(ch, s: Dictionary, foot: float) -> Dictionary:
	var rows := _card_rows(ch, s, ContentDB.item(str(s.id)))
	var h := 26.0
	for rw in rows: h += float(rw.h)
	var a := anchor
	var side := "left"
	var r := Rect2(a.position.x - 14 - CARD_W, a.get_center().y - h * 0.5, CARD_W, h)
	if not sel.has("slot") and a.position.y < FIELD.y + PITCH * 0.5:
		side = "below"
		r.position = Vector2(clampf(a.end.x - CARD_W, FIELD.x, FIELD.x + FIELD_W - CARD_W), a.end.y + 12)
	elif sel.has("slot") or a.position.x < FIELD.x + 4 * PITCH:
		side = "right"
		r.position.x = maxf(a.end.x + 14, FIELD.x)
	var low := foot + 4.0
	if (r.end.y if side == "below" else h + FIELD.y - 8) > low: low = frame_rect.end.y - 4.0
	r.position = Vector2(r.position.x, clampf(r.position.y, FIELD.y - 8, maxf(FIELD.y - 8, low - h))).round()
	return {"rect": r, "side": side, "rows": rows}

## The card: a small jade slip with a pointer to its space, and its rows top down.
func _draw_card(card: Dictionary) -> void:
	var r: Rect2 = card.rect
	var side := str(card.side)
	var a := anchor
	glow(r.grow(22), Color(UiKit.BRIGHT_JADE, 0.12))
	glow(Rect2(r.position + Vector2(-10, 24), r.size + Vector2(20, 12)), Color(UiKit.INK, 0.55))
	face(r, "sky_card")
	region(r, "_card")   # a tap on the card stays on it
	var tip := {"left": Vector2(r.end.x - 1, clampf(a.get_center().y, r.position.y + 18, r.end.y - 18)),
		"right": Vector2(r.position.x + 1, clampf(a.get_center().y, r.position.y + 18, r.end.y - 18)),
		"below": Vector2(clampf(a.get_center().x, r.position.x + 18, r.end.x - 18), r.position.y + 1)}[side] as Vector2
	var n: Vector2 = {"left": Vector2.RIGHT, "right": Vector2.LEFT, "below": Vector2.UP}[side]
	var t := Vector2(-n.y, n.x) * 9.0
	draw_colored_polygon(PackedVector2Array([tip - t - n * 3.0, tip + n * 9.0, tip + t - n * 3.0]), UiKit.SURFACE.sky.lerp(UiKit.SURFACE.space, (tip.y - r.position.y) / r.size.y))
	draw_polyline(PackedVector2Array([tip - t, tip + n * 9.0, tip + t]), Color(UiKit.BRIGHT_JADE, 0.65), 1.5, true)
	var p := r.position + Vector2(14, 12)
	for rw in card.rows:
		(rw.draw as Callable).call(p)
		p.y += float(rw.h)

## The card's rows, top down, each {h, draw(top-left)}: the head (icon, name, quality, grade, kind and item level), what
## it does or what it would change, what else is true of it, and its actions.
func _card_rows(ch, s: Dictionary, def: Dictionary) -> Array:
	var id := str(s.id)
	var q := str(s.get("quality", ""))
	var grade := str(def.get("grade", "plain"))
	var nm := ContentDB.item_name(id) + (" +%d" % int(s.enhance) if int(s.get("enhance", 0)) > 0 else "")
	var n := int(s.get("count", 1))
	var sub: Array = [[q.capitalize(), UiKit.quality_color(q)]] if q != "" else []
	sub.append_array([[grade.capitalize(), UiKit.grade_color(grade)], [_kind_word(def), UiKit.MIST], [Tx.t("ui.inventory.ilv") % int(s.get("ilv", def.get("ilv", 1))), UiKit.MIST]])
	var head: Array = []
	for part in sub: head.append_array([["·", UiKit.MIST], part] if not head.is_empty() else [part])
	var rows: Array = [{"h": 50.0, "draw": func(p: Vector2):
		icon_at(Rect2(p + Vector2(0, 4), Vector2(32, 32)), id)
		var nw := minf(UiKit.text_width(nm, 20), CARD_IN - 42 - (44 if n > 1 else 0))
		text(p + Vector2(42, 18), nm, 20, UiKit.quality_color(q) if q != "" else UiKit.grade_color(grade), HORIZONTAL_ALIGNMENT_LEFT, nw + 1)
		if n > 1: text(p + Vector2(50 + nw, 18), "×%d" % n, 16, UiKit.MIST)
		rich(Rect2(p + Vector2(42, 24), Vector2(CARD_IN - 42, 20)), head, 14)}]
	rows.append({"h": 12.0, "draw": func(p: Vector2): draw_polyline_colors(PackedVector2Array([p + Vector2(0, 5), p + Vector2(34, 5), p + Vector2(CARD_IN - 34, 5),
		p + Vector2(CARD_IN, 5)]), PackedColorArray([Color(UiKit.BRONZE, 0.0), UiKit.BRONZE, UiKit.BRONZE, Color(UiKit.BRONZE, 0.0)]), 1.0)})
	if def.has("slot") and str(def.slot) in InventoryState.SLOTS:
		rows.append_array(_compare_rows(ch, s, str(def.slot), sel.has("slot")))
	elif def.has("slot"):
		var gives: Array = StatRules.instance_modifiers(str(def.slot), s, ch.cultivator.energy_type, ch).map(func(m): return UiKit.affix_text(m))
		if not gives.is_empty(): rows.append(_note(" · ".join(gives), UiKit.BRIGHT_JADE, 16))
	elif str(def.get("desc", "")) != "":
		rows.append(_note(str(def.desc), UiKit.PAPER, 16))
	var affixes: Array = s.get("affixes", []).map(func(af): return UiKit.affix_text(af))
	if not affixes.is_empty(): rows.append(_note(Tx.t("ui.inventory.rolled") % " · ".join(affixes), UiKit.PALE_GOLD))
	for ln in _facts(ch, s, def): rows.append(_runs(ln) if ln[0] is Array else _note(ln[0], ln[1]))
	rows.append_array(_relic_rows(ch, s, def))
	rows.append_array(_action_rows(ch, s, def))
	return rows

## What the piece does for your own totals (StatRules.equip_change): for one in the bag, what wearing it in place of the
## worn one would make of them; for the one worn, what it adds (against the slot left empty). The three the card can name
## that change most, and Combat Power, each as it would be (as it is, for the worn one) with the change beside it.
func _compare_rows(ch, s: Dictionary, slot: String, worn: bool) -> Array:
	if change_of != int(s.get("uid", -1)):
		change = StatRules.equip_change(ch, slot, null if worn else s)
		change_of = int(s.get("uid", -1))
	var shown: Array = card_rows(change)
	if shown.all(func(rw): return absf(float(rw.after) - float(rw.before)) < 0.0005): return []
	var now = ch.inventory.equipped.get(slot)
	var head := Tx.t("ui.inventory.it_gives") if worn else (Tx.t("ui.inventory.against") % ContentDB.item_name(str(now.id)) if now != null
		else Tx.t("ui.inventory.against_empty") % Tx.t("ui.inventory." + slot).to_lower())
	return [_note(head, UiKit.GOLD), {"h": shown.size() * 22.0 + 6.0, "draw": func(p: Vector2):
		for i in shown.size():
			var rw: Dictionary = shown[i]
			var d := (float(rw.before) - float(rw.after)) * (1.0 if worn else -1.0)
			var y := p.y + 17 + i * 22
			var v := CharacterPage.stat_text(str(rw.stat), float(rw.before if worn else rw.after))
			text(Vector2(p.x, y), Tx.t(stat_key(str(rw.stat))), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, CARD_IN - 98 - UiKit.text_width(v, 16))
			text(Vector2(p.x, y), v, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, CARD_IN - 88)
			if absf(d) >= 0.0005:
				text(Vector2(p.x, y), ("▲ " if d > 0.0 else "▼ ") + CharacterPage.stat_text(str(rw.stat), absf(d)).trim_prefix("+"), 16,
					UiKit.BRIGHT_JADE if d > 0.0 else UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_RIGHT, CARD_IN)}]

## Of a StatRules.equip_change, the rows a card names: the three that change most among the stats it has words for, then
## Combat Power (the HUD's equip prompt names the first and the last).
static func card_rows(change: Array) -> Array:
	return change.filter(func(rw): return stat_key(str(rw.stat)) != "" and str(rw.stat) != "combat_power").slice(0, 3) + [change[-1]]

## The words the card names a stat by: the Character register's own, the pools and Combat Power; "" for the rest.
static func stat_key(stat: String) -> String:
	for row in CharacterPage.OFFENCE + CharacterPage.DEFENCE + POOLS:
		if str(row[0]) == stat: return str(row[1])
	return ""

## A piece's kind in its head: a weapon's family, a worn piece's slot, else its type.
static func _kind_word(def: Dictionary) -> String:
	if str(def.get("slot", "")) in InventoryState.SLOTS and str(def.slot) != "weapon": return Tx.t("ui.inventory." + str(def.slot))
	return str(def.get("family", def.get("slot", def.get("type", ""))) if def.has("slot") else def.get("type", "")).replace("_", " ").capitalize()

## The other things true of it, as notes [text, colour] or runs [[text, colour], ...]: a furnace's batch and wear, a
## natal treasure's growth, an awakened weapon's skill, a forge's pity; a pill's toxicity against yours, its potency,
## marks and Halo, what resistance leaves of it; a rack's work, an appraisal still to make; a treasure's cost, a flight
## vessel's saving; and what quick-use holds beside a thing you could put there.
func _facts(ch, s: Dictionary, def: Dictionary) -> Array:
	var out: Array = []
	var id := str(s.id)
	var q := str(s.get("quality", ""))
	if def.has("furnace"):
		var fs: Dictionary = def.furnace
		var band := float(fs.get("band", 0.0)) + float(Game.crafting.upkeep("furnace_band_per_level", 0.01)) * int(s.get("enhance", 0))
		out.append([Tx.t("ui.crafts.furnace_stats") % [int(fs.get("batch", 1)), int(round(band * 100)), int(round(float(fs.get("filter", 0.0)) * 100)),
			int(round(float(fs.get("yield", 0.0)) * 100))], UiKit.BRIGHT_JADE])
		out.append([Tx.t("ui.inventory.furnace_durability") % int(s.get("durability", 100)), UiKit.BRIGHT_JADE])
		if str(fs.get("element", "")) != "": out.append([Tx.t("ui.crafts.furnace_element") % str(fs.element).capitalize(), UiKit.PALE_GOLD])
	if s.get("natal", false):
		out.append([Tx.t("ui.forge.natal_broken") if s.get("broken", false) else Tx.t("ui.inventory.natal_line") % [int(s.get("natal_level", 0)), int(s.get("ilv_eff", s.get("ilv", 1)))],
			UiKit.RED_TEXT if s.get("broken", false) else UiKit.GOLD])
	if s.get("awakened", false):
		var ak := CraftingAuthority.awakened_skill(id)
		out.append([Tx.plural("ui.forge.awakened_line", int(ak.get("every_hits", 12))) % [str(ak.get("name", "")), int(ak.get("every_hits", 12))], UiKit.GOLD])
	if float(s.get("pity", 0.0)) > 0.0: out.append([Tx.t("ui.forge.pity_line") % int(round(float(s.pity) * 100)), UiKit.GOLD])
	var pill: Dictionary = def.get("pill", {})
	if pill.has("toxicity"):
		out.append([[Tx.t("ui.inventory.toxicity"), UiKit.MIST], [str(int(round(float(pill.toxicity) * InventoryAuthority.pill_toxicity_mult(s)))), UiKit.RED_TEXT],
			[Tx.t("ui.inventory.tox_yours") % int(ch.cultivator.toxicity), UiKit.MIST]])
	if not pill.is_empty() and q != "":
		out.append([Tx.t("ui.inventory.potency") % int(round(InventoryAuthority.pill_potency(s) * 100.0)), UiKit.quality_color(q)])
		if int(s.get("marks", 0)) > 0: out.append([Tx.plural("ui.inventory.pill_marks", int(s.marks)) % [int(s.marks), int(s.marks) * 2], UiKit.GOLD])
		if q == "pill_halo": out.append([Tx.t("ui.inventory.halo_charge") % int(round(float(s.get("halo", 0.0)) * 100.0)), UiKit.PALE_GOLD])
	if str(s.get("prep", "")) != "": out.append([Tx.t("ui.inventory.prep_" + str(s.prep)), UiKit.BRIGHT_JADE])
	if s.get("unappraised", false): out.append([Tx.t("ui.inventory.unappraised"), UiKit.GOLD])
	var fam := ProgressionRules.pill_family(def)
	if fam != "" and not pill.is_empty():
		out.append([Tx.t("ui.inventory.ignores_resistance") if q == "pill_grain"
			else Tx.t("ui.inventory.resistance") % [Tx.t("ui.cultivation.family_" + fam), int(round(ProgressionRules.resistance_factor(ch.cultivator, fam) * 100.0))], UiKit.MIST])
	var tr := CombatAuthority.treasure_of(id)
	if not tr.is_empty():
		var soul := int(CombatAuthority.treasure_soul_cost(ch, tr))
		out.append([Tx.plural("ui.inventory.treasure_charges", int(s.get("charges", int(tr.charges)))) % int(s.get("charges", int(tr.charges))) if tr.has("charges")
			else (Tx.t("ui.inventory.treasure_cost_soul") % [int(tr.get("qi", 0)), soul, UiKit.span(float(tr.get("cooldown_s", 0)))] if soul > 0
			else Tx.t("ui.inventory.treasure_cost") % [int(tr.get("qi", 0)), UiKit.span(float(tr.get("cooldown_s", 0)))]), UiKit.PALE_GOLD if tr.has("charges") else UiKit.BRIGHT_JADE])
	if def.has("flight"):
		out.append([Tx.t("ui.inventory.vessel_stats") % int(round((1.0 - float(def.flight.get("qi_mult", 1.0))) * 100.0)), UiKit.BRIGHT_JADE])
		if str(ch.inventory.vessel) == id: out.append([Tx.t("ui.inventory.vessel_ridden"), UiKit.PALE_GOLD])
	# Decision 45: what the three quick slots hold, beside a thing that could go in one.
	if sel.has("bag") and def.has("use") and Unlocks.is_unlocked(ch.id, "quick_use") and ch.inventory.quick.any(func(q): return str(q) != "" and str(q) != id):
		var held: Array = []
		for k in ch.inventory.quick.size():
			var qu := str(ch.inventory.quick[k])
			held.append(Tx.t("ui.inventory.quick_slot_holds") % [k + 1, ContentDB.item_name(qu) if qu != "" else Tx.t("ui.inventory.quick_empty"),
				ch.inventory.count(qu)] if qu != "" else Tx.t("ui.inventory.quick_slot_empty") % (k + 1))
		out.append([Tx.t("ui.inventory.quick_holds_all") % " · ".join(held), UiKit.MIST])
	return out

## S14 relics: a sealed one offers Bind (a channel a hit breaks); a bound one with a spirit shows its affinity and, in
## hand, the contest, a gift and a meal (S47 Artifact Spirit depth).
func _relic_rows(ch, s: Dictionary, def: Dictionary) -> Array:
	if not def.get("relic", false): return []
	var target := {"slot": str(sel.slot)} if sel.has("slot") else {"index": int(sel.get("bag", -1))}
	var prog: float = Game.inventory.binding_progress(ch.id)
	if s.get("sealed", false):
		var secs := float(ContentDB.stat_const("binding", {}).get("seconds", {}).get(str(def.get("grade", "common")), 10))
		return [_note(Tx.t("ui.inventory.sealed_bind_it_to_wake"), UiKit.RED_TEXT), _bar(prog, UiKit.JADE, Tx.t("ui.inventory.binding")) if prog >= 0.0
			else _buttons([[Tx.t("ui.inventory.bind_s") % UiKit.span(secs), "bind", target, true, Unlocks.is_unlocked(ch.id, "binding"), Unlocks.locked_text("binding"), 0.0]])]
	var spirit := str(s.get("spirit", ""))
	if spirit == "": return []
	var sp: Dictionary = def.get("spirit", {})
	var awake := spirit == "awake"
	var aff := float(s.get("spirit_affinity", 0.0))
	var need := int(InventoryAuthority.spirit_cfg().get("wake_affinity", 30))
	var rows: Array = [_note(Tx.t("ui.inventory.spirit_awake") % str(def.get("unique", "")) if awake else Tx.t("ui.inventory.spirit_sleeps_named") % str(sp.get("name", "")),
		UiKit.PALE_GOLD if awake else UiKit.SOUL_TEXT), _bar(aff / 100.0, UiKit.SOUL, Tx.t("ui.inventory.spirit_affinity") % [int(aff), int(s.get("spirit_level", 0))])]
	if awake and not StatRules.spirit_controlled(ch, s): rows.append(_note(Tx.t("ui.inventory.spirit_refuses") % int(sp.get("control", 0)), UiKit.RED_TEXT))
	elif not awake: rows.append(_note(Tx.t("ui.inventory.spirit_wakes_line") % [need, ContentDB.name_of("rooms", str(sp.get("wake_room", "")))], UiKit.MIST))
	if not (sel.has("slot") and str(sel.slot) == "weapon"): return rows
	if not awake: rows.append(_buttons([[Tx.t("ui.inventory.subdue_short") % int(round(Game.inventory.spirit_chance(ch, str(s.id)) * 100.0)), "subdue", target, true, aff >= need, "", 0.0]]))
	var gift := _best_gift(ch, sp)
	var foods: Array = Game.inventory.devour_candidates(ch)
	rows.append(_buttons([[Tx.t("ui.inventory.gift_item") % ContentDB.item_name(gift) if gift != "" else Tx.t("ui.inventory.gift_none"), "gift_spirit", gift, false, gift != "", "", 0.0]]))
	rows.append(_buttons([[Tx.t("ui.inventory.devour_item") % ContentDB.item_name(str(ch.inventory.bag[int(foods[0])].id)) if not foods.is_empty() else Tx.t("ui.inventory.devour_none"),
		"devour", int(foods[0]) if not foods.is_empty() else -1, false, not foods.is_empty(), "", 0.0]]))
	return rows

## The gift the spirit would like most that is in the bag: its favourite first, then the richest.
func _best_gift(ch, sp: Dictionary) -> String:
	var fav := str(sp.get("favourite", ""))
	if fav != "" and ch.inventory.count(fav) > 0: return fav
	var best := ""
	var worth := 0.0
	var gifts: Dictionary = InventoryAuthority.spirit_cfg().get("gifts", {})
	for g in gifts:
		if ch.inventory.count(str(g)) > 0 and float(gifts[g]) > worth:
			best = str(g)
			worth = float(gifts[g])
	return best

## The card's actions: the one the thing is for (primary) and its partner, then "···" for the rest (Lock, Discard,
## Self-detonate, Appraise), which a thing with no action of its own shows at once. A worn piece: Unequip, and the spare
## weapon's Swap. A key item: Ride or Play.
func _action_rows(ch, s: Dictionary, def: Dictionary) -> Array:
	var id := str(s.id)
	if sel.has("key"):
		if def.has("flight"):
			var riding := str(ch.inventory.vessel) == id
			return [_buttons([[Tx.t("ui.inventory.stop_riding") if riding else Tx.t("ui.inventory.ride_in_flight"), "vessel", "" if riding else id, not riding,
				Unlocks.is_unlocked(ch.id, "flight"), Unlocks.locked_text("flight"), 0.0]])]
		if str(def.get("use_action", "")) != "": return [_buttons([[Tx.t("ui.inventory.play") if str(def.use_action) == "guqin" else Tx.t("ui.inventory.use"), "use_key", null, true, true, "", 0.0]])]
		return []
	if sel.has("slot"):
		var rows: Array = []
		var spare = ch.inventory.loadout.get("spare")
		if str(sel.slot) == "weapon" and spare != null:
			rows.append(_note(Tx.t("ui.inventory.spare_weapon") % ContentDB.item_name(str(spare.id)), UiKit.PALE_GOLD))
			rows.append(_buttons([[Tx.t("ui.inventory.swap_now"), "swap", null, true, true, "", 0.0], [Tx.t("ui.inventory.spare_out"), "spare_out", null, false, true, "", 0.0]]))
		rows.append(_buttons([[Tx.t("ui.inventory.unequip"), "unequip", null, false, str(sel.slot) != "gourd", Tx.t("ui.inventory.the_spirit_gourd_holds_your"), 0.0]]))
		return rows
	var main: Array = []   # [label, id, data, primary, enabled, reason, width (0 shares what is left)]
	var quick_row: Array = []   # decision 45: Quick 1-3 under a usable thing
	if def.has("restores"): main.append([Tx.t("ui.inventory.restore_relic"), "restore", null, true, true, "", 0.0])
	elif def.has("slot"):
		var ctx := Game.ctx(ch)
		main.append([Tx.t("ui.inventory.set_furnace") if def.has("furnace") else Tx.t("ui.inventory.equip"), "equip", null, true, RequirementRules.passes(def.get("requires", {}), ctx),
			RequirementRules.first_failure_text(def.get("requires", {}), ctx), 0.0])
		if str(def.slot) == "weapon": main.append([Tx.t("ui.inventory.set_spare"), "spare", null, false, Unlocks.is_unlocked(ch.id, "dual_loadout"), Unlocks.locked_text("dual_loadout"), 112.0])
	elif def.has("use"):
		var verb := Tx.t("ui.inventory.use")
		if def.has("raw"): verb = Tx.t("ui.inventory.absorb") if def.has("core") else Tx.t("ui.inventory.eat_raw")
		elif str(def.get("use_action", "")) == "absorb_flame": verb = Tx.t("ui.inventory.absorb")
		elif str(def.get("use_action", "")) == "bath": verb = Tx.t("ui.inventory.bathe")
		main.append([verb, "use", null, true, true, "", 0.0])
		# Decision 45: the three quick slots under it, each a toggle (lit where it holds this thing; a tap on it clears it).
		for k in ch.inventory.quick.size():
			var here := str(ch.inventory.quick[k]) == id
			quick_row.append([Tx.t("ui.inventory.in_quick_n") % (k + 1) if here else Tx.t("ui.inventory.quick_n") % (k + 1), "quick", k, here,
				Unlocks.is_unlocked(ch.id, "quick_use"), Tx.t("ui.inventory.quick_use_is_not_unlocked"), 0.0])
	elif def.has("treasure"):
		# G2: a treasure art is set in one of the HUD's two Treasure buttons; tapping its own slot clears it.
		for k in 2:
			var here := str(ch.inventory.treasures[k]) == id
			var slot_id := "treasures" if k == 0 else "treasure_slot_2"
			main.append([Tx.t("ui.inventory.in_treasure") % (k + 1) if here else Tx.t("ui.inventory.treasure_n") % (k + 1), "treasure", k, here,
				Unlocks.is_unlocked(ch.id, slot_id), Unlocks.locked_text(slot_id), 0.0])
	var locked: bool = ch.inventory.locked.has(int(s.get("uid", -1)))
	var rest: Array = [[Tx.t("ui.inventory.unlock") if locked else Tx.t("ui.inventory.lock"), "lock", null, false, true, "", 0.0],
		[Tx.t("ui.inventory.discard"), "discard", null, false, def.get("type", "") != "key", "", 0.0]]
	# S47 self-detonation: a spare artifact bursts for damage by its grade and is gone (confirmed first).
	if (ContentDB.is_equipment(id) or def.has("treasure")) and not def.has("furnace") and Unlocks.is_unlocked(ch.id, "treasures"):
		rest.append([Tx.t("ui.inventory.detonate"), "detonate", null, false, not locked, Tx.t("ui.forge.locked_item"), 0.0])
	if s.get("unappraised", false): rest.push_front([Tx.t("ui.inventory.appraise"), "appraise", null, false, true, "", 0.0])
	if main.is_empty():
		main = rest.slice(0, 2)
		rest = rest.slice(2)
	if not rest.is_empty(): main.append(["···", "more", null, false, true, "", float(BTN_H)])
	var rows: Array = [_buttons(main)]
	if not quick_row.is_empty(): rows.append(_buttons(quick_row))
	if more:
		for i in range(0, rest.size(), 2): rows.append(_buttons(rest.slice(i, i + 2)))
	return rows

## A row of the card's words wrapped to its width (14, or `size`).
func _note(s: String, col: Color, size := 14) -> Dictionary:
	return {"h": _wrap(s, size, CARD_IN).size() * UiKit.line_height(size) + 4.0, "draw": func(p: Vector2): para(Rect2(p, Vector2(CARD_IN, 400)), s, size, col)}

## A row of words in several colours, [[text, colour], ...], at 14.
func _runs(runs: Array) -> Dictionary:
	var all := " ".join(runs.map(func(r): return str(r[0])))
	return {"h": _wrap(all, 14, CARD_IN).size() * UiKit.line_height(14) + 4.0, "draw": func(p: Vector2): rich(Rect2(p, Vector2(CARD_IN, 400)), runs, 14)}

func _bar(frac: float, col: Color, label: String) -> Dictionary:
	return {"h": 34.0, "draw": func(p: Vector2): bar(Rect2(p + Vector2(0, 4), Vector2(CARD_IN, 26)), frac, col, label)}

## A row of the card's buttons, [label, id, data, primary, enabled, reason, width] each; width 0 shares what is left.
func _buttons(list: Array) -> Dictionary:
	var fixed := 0.0
	var shared := 0
	for b in list:
		fixed += float(b[6])
		if float(b[6]) <= 0.0: shared += 1
	var each := (CARD_IN - fixed - GAP * (list.size() - 1)) / maxf(1.0, shared)
	return {"h": BTN_H + 8.0, "draw": func(p: Vector2):
		var x := p.x
		for b in list:
			var bw := float(b[6]) if float(b[6]) > 0.0 else each
			btn(Rect2(x, p.y + 8, bw, BTN_H), str(b[0]), str(b[1]), b[2], bool(b[3]), bool(b[4]), str(b[5]), 20 if bool(b[3]) or str(b[1]) == "more" else 16)
			x += bw + GAP}

# ------------------------------------------------------------------ taps
func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"sky":
			sel = {}
			more = false
		"kind":
			kind = str(data)
			sel = {}
			scroll["grid"] = 0.0
		"more": more = not more
		"bind":
			var br := submit(({"type": "bind_item"} as Dictionary).merged(data))
			if br.get("ok", false): flash(Tx.t("ui.inventory.binding_hold_still"))
		"subdue":
			var sr := submit(({"type": "subdue_spirit"} as Dictionary).merged(data))
			if sr.get("ok", false): flash(Tx.t("ui.inventory.the_spirit_wakes_and_answers") if sr.get("awake", false) else Tx.t("ui.inventory.the_spirit_throws_you_off"))
		"gift_spirit": submit({"type": "gift_spirit", "item": str(data)})
		"devour":
			var dr := submit({"type": "devour_gear", "index": int(data)})
			if dr.get("ok", false): flash(Tx.t("ui.inventory.spirit_devoured") % ContentDB.item_name(str(dr.get("ate", ""))))
		"bag":
			var s = ch.inventory.bag[int(data)]
			sel = {"bag": int(data)} if s != null else {}
			more = false
			if s != null: submit({"type": "mark_item_seen", "item": str(s.id)})
		"slot":
			sel = {"slot": str(data)}
			more = false
		"key":
			sel = {"key": int(data)}
			more = false
		"sort": submit({"type": "sort_bag", "by": sort_by})
		"equip":
			if submit({"type": "equip", "index": int(sel.bag)}).get("ok", false): sel = {}
		"unequip":
			if submit({"type": "unequip", "slot": str(sel.slot)}).get("ok", false): sel = {}
		"use":
			var r := submit({"type": "use_item", "index": int(sel.bag)})
			if r.get("ok", false) and str(r.get("open_page", "")) != "":
				navigate.emit(str(r.open_page), {})
				return
			if not r.get("ok", false) and r.get("reason", "") == "confirm":
				ask(str(r.get("text", Tx.t("ui.inventory.use_it_anyway"))), "use_confirm", int(sel.bag))
		"use_confirm": submit({"type": "use_item", "index": int(data), "confirm": true})
		"use_key":
			var rk := submit({"type": "use_item", "key": int(sel.key)})
			if rk.get("ok", false) and str(rk.get("open_page", "")) != "": navigate.emit(str(rk.open_page), {})
		"appraise":
			var ar := submit({"type": "appraise_item", "index": int(sel.bag)})
			if ar.get("ok", false): flash(str(ar.get("text", "")))
		"spare":
			if submit({"type": "set_spare_weapon", "index": int(sel.bag)}).get("ok", false):
				flash(Tx.t("ui.inventory.spare_set"))
				sel = {}
		"spare_out": submit({"type": "set_spare_weapon", "index": -1})
		"restore":
			var rr := submit({"type": "restore_relic", "index": int(sel.bag)})
			if rr.get("ok", false): sel = {}
			elif str(rr.get("text", "")) != "": flash(str(rr.text))
		"swap": submit({"type": "swap_loadout"})
		"detonate":
			var dr := submit({"type": "self_detonate", "index": int(sel.bag)})
			if not dr.get("ok", false) and dr.get("reason", "") == "confirm": ask(str(dr.get("text", "")), "detonate_yes", int(sel.bag), true)
			elif not dr.get("ok", false) and str(dr.get("text", "")) != "": flash(str(dr.text))
		"detonate_yes":
			if submit({"type": "self_detonate", "index": int(data), "confirm": true}).get("ok", false): sel = {}
		"quick":
			# Decision 45: Quick 1-3; the slot already holding this thing clears, another takes it (out of any other slot).
			var s = selected_item()
			var k := int(data) if data != null else 0
			if s != null: submit({"type": "set_quick_use", "slot": k, "item": "" if str(ch.inventory.quick[k]) == str(s.id) else str(s.id)})
		"lock": submit({"type": "lock_item", "index": int(sel.bag)})
		"treasure":
			var st = selected_item()
			if st != null:
				var k := int(data)
				submit({"type": "set_treasure", "slot": k, "item": "" if str(ch.inventory.treasures[k]) == str(st.id) else str(st.id)})
		"vessel": submit({"type": "choose_vessel", "item": str(data)})
		"discard":
			var s2 = selected_item()
			if s2 != null: ask(Tx.t("ui.inventory.discard_2") % [ContentDB.item_name(str(s2.id)), int(s2.get("count", 1))], "discard_yes", int(sel.bag), true)
		"discard_yes":
			var s3 = ch.inventory.bag[int(data)]
			if s3 != null and submit({"type": "discard", "index": int(data), "count": int(s3.get("count", 1))}).get("ok", false): sel = {}
		"_tab":
			sel = {}
			more = false
