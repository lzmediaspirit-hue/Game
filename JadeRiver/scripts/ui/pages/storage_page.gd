extends Page
## Shared storage (S23), P5 as the storehouse chest (docs/page_identity.md row 19; decisions 14 and 24): an iron-bound
## camphor chest with its lid thrown open over the right two-thirds, the account's things in its tray and the Treasury's
## added spaces (sect_buildings.json treasury `storage_slots_per_level`) as a second tray below a partition; beside it at
## the left "your bag" is a patch of the gourd's heaven, lit from the gourd's mouth, as the Bag page draws it. A tap moves
## a thing across: into the chest from the gourd, back into the gourd from the chest. The lid swings open as the page
## opens and a moved thing arcs across. The page submits intents only.

const BagPage = preload("res://scripts/ui/pages/inventory_page.gd")
const SKY := Rect2(0, 0, 432, 720)            # the gourd's heaven
const GOURD_AT := Vector2(78, 176)            # the gourd's spaces, four across
const GOURD_COLS := 4
const GOURD_ROWS := 6
const CHEST := Rect2(448, 212, 760, 468)      # the chest's body under its raised lid
const LID := Rect2(448, 32, 760, 184)
const TRAY_AT := Vector2(508, 244)            # the tray's spaces, eight across
const TRAY_COLS := 8
const TRAY_ROWS := 4
const BASE := 40                              # the chest's own spaces (AccountAuthority.storage_size)

var stars: Array = []
var moved := {}            # the thing on its way across (MarketKit.fly)

func _init() -> void:
	title = Tx.t("ui.storage.storage")
	identity = Identity.new("lacquer_black", false, "own", "open_chest_lid_gourd_beside", 0.3)
	grade_rims = true

func setup() -> void:
	stars = BagPage.scatter_stars(80, SKY, [Rect2(40, 90, 380, 600)])

func content_rect() -> Rect2:
	return Rect2(TRAY_AT, Vector2(TRAY_COLS * MarketKit.PITCH + GUTTER - 4, TRAY_ROWS * MarketKit.PITCH))

# ------------------------------------------------------------------ the heaven and the chest
func draw_surface(_r: Rect2) -> void:
	vshade(Rect2(432, 0, size.x - 432, size.y), UiKit.SURFACE.lacquer_black, UiKit.INK)
	ground(Rect2(432, 0, size.x - 432, size.y), UiKit.SURFACE.lacquer_black)
	MarketKit.heaven(self, SKY, stars, 216.0, 0.6)
	# The chest's body: camphor boards bound by bronze bands, the tray sunk inside it.
	glow(Rect2(CHEST.position + Vector2(-40, CHEST.size.y - 40), Vector2(CHEST.size.x + 80, 90)), Color(UiKit.INK, 0.6))
	MarketKit.planks(self, CHEST, UiKit.SURFACE.wood, 38.0, false)
	vshade(Rect2(CHEST.position, Vector2(CHEST.size.x, 24)), Color(UiKit.INK, 0.5), Color(UiKit.INK, 0.0))
	for bx in [CHEST.position.x + 12, CHEST.end.x - 36]:
		draw_rect(Rect2(bx, CHEST.position.y, 24, CHEST.size.y), UiKit.BRONZE)
		draw_rect(Rect2(bx + 2, CHEST.position.y, 3, CHEST.size.y), Color(UiKit.GOLD, 0.5))
		for y in range(int(CHEST.position.y) + 30, int(CHEST.end.y), 64): draw_circle(Vector2(bx + 12, y), 3.0, UiKit.PALE_GOLD, true, -1.0, true)
	draw_rect(Rect2(CHEST.position.x, CHEST.end.y - 20, CHEST.size.x, 20), UiKit.BRONZE)
	draw_rect(Rect2(CHEST.position.x, CHEST.end.y - 20, CHEST.size.x, 2), Color(UiKit.GOLD, 0.6))
	ground(CHEST, UiKit.SURFACE.wood)
	var tray := Rect2(TRAY_AT - Vector2(20, 20), Vector2(TRAY_COLS * MarketKit.PITCH + 36, TRAY_ROWS * MarketKit.PITCH + 32))
	rounded(tray.grow(3), 6.0, UiKit.INK)
	vshade(tray, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.35), UiKit.SURFACE.lacquer)
	ground(tray, UiKit.SURFACE.lacquer)
	# The lid, swung up from the chest's back edge as the page opens.
	var k := unfold()
	draw_set_transform(Vector2(0, LID.end.y * (1.0 - k)), 0.0, Vector2(1.0, maxf(0.05, k)))
	draw_texture_rect(UiKit.hd_texture("storehouse_lid", "normal"), LID, false)
	draw_set_transform(Vector2.ZERO)

## The title on a brass plate fixed to the lid's lining.
func title_rect() -> Rect2:
	var w := ceilf(UiKit.text_width(title, UiKit.D_TITLE, true)) + 72.0
	return Rect2(LID.get_center().x - w * 0.5, LID.position.y + 60, w, 56)

func draw_title_mount(r: Rect2) -> void:
	if unfold() < 0.99: return
	rounded(r.grow(2), 6.0, UiKit.INK)
	vshade(r, UiKit.GOLD, UiKit.BRONZE)
	draw_rect(r.grow(-4), Color(UiKit.PALE_GOLD, 0.5), false, 1.0)
	for p in [r.position + Vector2(10, 10), Vector2(r.end.x - 10, r.position.y + 10), Vector2(r.position.x + 10, r.end.y - 10), r.end - Vector2(10, 10)]:
		draw_circle(p, 3.0, UiKit.SURFACE.wood_dark, true, -1.0, true)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var items: Array = Game.account.storage.get("items", [])
	var bag: Array = ch.inventory.bag
	tour_mark("gourd", SKY)   # decision 43: a tour's anchors
	tour_mark("chest", CHEST)
	var cap: int = Game.accounts.storage_size()
	# The gourd's side: its token, the hint and its spaces.
	var inv: InventoryState = ch.inventory
	var used := "%d / %d" % [inv.bag.size() - inv.free_slots(), inv.capacity()]
	var gourd = inv.equipped.get("gourd")
	var gl := ContentDB.item_name(str(gourd.id)) if gourd != null else Tx.t("ui.inventory.spirit_gourd")
	BagPage.token(self, Rect2(GOURD_AT.x, 88, ceilf(UiKit.text_width(gl, 18) + UiKit.text_width(used, 16)) + 48, TAB_H), gl, used, true)
	text(Vector2(GOURD_AT.x + 2, 158), Tx.t("ui.storage.tap_to_store"), 14, UiKit.MIST)
	MarketKit.sky_grid(self, "bag", Rect2(GOURD_AT, Vector2(GOURD_COLS * MarketKit.PITCH + GUTTER - 4, GOURD_ROWS * MarketKit.PITCH)), GOURD_COLS,
		MarketKit.PITCH, bag.size(), func(i): return bag[i], "deposit", -1)
	# The chest's tray: its own spaces, then the Treasury's tray below a partition.
	var extra := maxi(0, cap - BASE)
	var base_rows := ceili(mini(cap, BASE) / float(TRAY_COLS))
	var rows := base_rows + (1 + ceili(extra / float(TRAY_COLS)) if extra > 0 else 0)
	var view := Rect2(TRAY_AT, Vector2(TRAY_COLS * MarketKit.PITCH + GUTTER - 4, TRAY_ROWS * MarketKit.PITCH))
	list("store", view, rows, MarketKit.PITCH, func(row: int, rr: Rect2):
		if extra > 0 and row == base_rows:
			_partition(rr, extra)
			return
		var first := row * TRAY_COLS if row < base_rows else BASE + (row - base_rows - 1) * TRAY_COLS
		var last := mini(cap, BASE) if row < base_rows else cap
		for col in TRAY_COLS:
			var i := first + col
			if i >= last: return
			var r := Rect2(rr.position + Vector2(col * MarketKit.PITCH, 0), Vector2(SLOT, SLOT))
			if i >= items.size() or items[i] == null:
				rounded(r, 5.0, Color(UiKit.INK, 0.35))
				draw_rect(r.grow(-1.5), Color(UiKit.GOLD, 0.25), false, 1.0)
				continue
			var s: Dictionary = items[i]
			slot_box(r, str(s.id), int(s.get("count", 1)), str(s.get("quality", "")), "withdraw", i)
	)
	# The chest's front: how full it is and what the Treasury adds.
	var fy := CHEST.end.y - 44
	text(Vector2(TRAY_AT.x - 12, fy), Tx.t("ui.storage.chest_holds") % [items.size(), cap], 18, UiKit.PAPER)
	var lvl: int = Game.sect.level_building("treasury") if Game.sect.founded() else 0
	var per := int(ContentDB.entry("sect_buildings", "treasury").get("output", {}).get("storage_slots_per_level", 0))
	var line := Tx.t("ui.storage.treasury_adds") % [lvl, extra] if extra > 0 else Tx.t("ui.storage.treasury_would") % per
	text(Vector2(TRAY_AT.x + 250, fy), line, 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, TRAY_COLS * MarketKit.PITCH - 246)
	# The hasp on the chest's front.
	var hasp := Rect2(CHEST.get_center().x - 18, CHEST.end.y - 40, 36, 30)
	rounded(hasp, 4.0, UiKit.BRONZE)
	draw_rect(hasp.grow(-3), Color(UiKit.GOLD, 0.6), false, 1.0)
	draw_circle(hasp.get_center(), 4.0, UiKit.INK, true, -1.0, true)
	MarketKit.flight(self, moved)

## The partition between the chest's own tray and the Treasury's: a camphor board with the Treasury's word on it.
func _partition(rr: Rect2, extra: int) -> void:
	var b := Rect2(rr.position.x - 20, rr.position.y + 16, rr.size.x + 32, 44)
	vshade(b, UiKit.SURFACE.wood, UiKit.SURFACE.wood_dark)
	draw_rect(Rect2(b.position, Vector2(b.size.x, 2)), Color(UiKit.GOLD, 0.5))
	ground(b, UiKit.SURFACE.wood_dark)
	text(b.position + Vector2(24, 29), Tx.t("ui.storage.treasury_tray") % extra, 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, b.size.x - 48)

# ------------------------------------------------------------------ taps
func on_action(id: String, data) -> void:
	var ch = c()
	match id:
		"deposit":
			var s = ch.inventory.bag[int(data)]
			if s != null and submit({"type": "deposit", "index": int(data), "count": 999}).get("ok", false):
				var off := float(scroll.get("bag", 0.0))
				var from := GOURD_AT + Vector2((int(data) % GOURD_COLS) * MarketKit.PITCH + 38, (int(data) / GOURD_COLS) * MarketKit.PITCH + 38 - off)
				moved = MarketKit.fly(self, str(s.id), from, TRAY_AT + Vector2(320, 120), 0.2, 90.0)
		"withdraw":
			var items: Array = Game.account.storage.get("items", [])
			var it = items[int(data)] if int(data) < items.size() else null
			if it != null and submit({"type": "withdraw", "index": int(data)}).get("ok", false):
				moved = MarketKit.fly(self, str(it.id), TRAY_AT + Vector2(320, 120), GOURD_AT + Vector2(150, 200), 0.2, 90.0)
