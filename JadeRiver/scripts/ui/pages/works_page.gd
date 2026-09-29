extends Page
## S50 Keeping Post (V10d): the account web behind the posts. Arts: the active character's Post Arts, bought with
## points from its craft levels. Seals: Seal Scripts inscribed with Storehouse goods. Steles: Guardian Steles raised
## with silver and ore. Favours: the Magistrate's Favours, earned once each with silver and tribute. Furnace: the
## Calcination Furnace's salt lines. Flags: Formation Flags over posts. Mirror: the Mirror of Echoes' slots.
## P5 (docs/page_identity.md row 23, mockup 14 v4, decisions 21 and 26): the curio cabinet. The seven works are seven
## objects in the compartments of an irregular bamboo shelf (tools/icons/families/works.py, drawn at their native 96),
## each with its state on a hanging hemp label, a locked one dark behind a lattice screen with what opens it; the
## compartments are the tabs. The chosen work's list lies on the tray below (the Seal Scripts five rows at once), and
## what the works add, the Storehouse and the silver are written on the inventory slip at the right.

const WALL := Rect2(64, 32, 1152, 656)
const CABINET := Rect2(86, 96, 754, 256)
const TRAY := Rect2(86, 360, 754, 320)
const SLIP := Rect2(856, 96, 344, 584)
const ROW := 56.0
## Each work's compartment (in the tabs' order) and its object.
const CELLS := {"arts": Rect2(94, 104, 168, 116), "seals": Rect2(270, 104, 214, 116), "steles": Rect2(492, 104, 150, 116),
	"flags": Rect2(650, 104, 182, 116), "furnace": Rect2(94, 228, 250, 116), "favours": Rect2(352, 228, 240, 116), "mirror": Rect2(600, 228, 232, 116)}
const OBJECT := {"arts": "work_post_arts", "seals": "work_seal", "steles": "work_stele", "favours": "work_favour", "furnace": "work_furnace",
	"flags": "work_flag", "mirror": "work_mirror"}
const GATE := {"arts": "post_arts", "seals": "seal_scripts", "steles": "guardian_steles", "favours": "magistrates_favours", "furnace": "calcination",
	"flags": "formation_flags", "mirror": "mirror_of_echoes"}

func _init() -> void:
	title = Tx.t("ui.works.title")
	tabs = [{"id": "arts", "label": Tx.t("ui.works.tab_arts")}, {"id": "seals", "label": Tx.t("ui.works.tab_seals")},
		{"id": "steles", "label": Tx.t("ui.works.tab_steles")}, {"id": "favours", "label": Tx.t("ui.works.tab_favours")},
		{"id": "furnace", "label": Tx.t("ui.works.tab_furnace")}, {"id": "flags", "label": Tx.t("ui.works.tab_flags")},
		{"id": "mirror", "label": Tx.t("ui.works.tab_mirror")}]
	identity = Identity.new("bamboo", false, "own", "curio_shelf_tray_slip", 0.25)

func setup() -> void:
	# A work not yet open is a dark compartment behind its lattice that says what opens it (page_identity §1).
	var ch = c()
	for tb in tabs:
		if ch != null and not Unlocks.is_unlocked(ch.id, str(GATE[tb.id])): tb["locked"] = Unlocks.locked_text(str(GATE[tb.id]))
	var want := str(args.get("tab", ""))
	for i in tabs.size():
		if str(tabs[i].id) == want: tab = i

func content_rect() -> Rect2:
	return Rect2(TRAY.position.x + 12, TRAY.position.y + 36, TRAY.size.x - 24, TRAY.size.y - 40)

# ------------------------------------------------------------------ the cabinet
## The wall of green bamboo slats, the cabinet's frame, its shelves and the tray.
func draw_surface(_r: Rect2) -> void:
	var wall: Color = UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.78)
	rounded(WALL.grow(2), 8.0, UiKit.INK)
	rounded(WALL, 6.0, wall)
	ground(WALL, wall)
	for x in range(int(WALL.position.x) + 22, int(WALL.end.x), 24): draw_rect(Rect2(x, WALL.position.y + 8, 2, WALL.size.y - 16), Color(UiKit.INK, 0.25))
	draw_rect(WALL.grow(-9), UiKit.SURFACE.bamboo, false, 2.0)
	rounded(CABINET.grow(2), 5.0, UiKit.INK)
	rounded(CABINET, 4.0, UiKit.SURFACE.bamboo)
	for x in range(int(CABINET.position.x) + 30, int(CABINET.end.x), 31): draw_rect(Rect2(x, CABINET.position.y, 1, CABINET.size.y), Color(UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.5), 0.35))
	draw_rect(Rect2(CABINET.position.x + 4, 221, CABINET.size.x - 8, 6), UiKit.SURFACE.wood)
	rounded(TRAY.grow(2), 7.0, UiKit.INK)
	rounded(TRAY, 6.0, UiKit.SURFACE.wood_dark)
	draw_rect(TRAY.grow(-3), UiKit.SURFACE.wood, false, 3.0)
	ground(TRAY, UiKit.SURFACE.wood_dark)

func title_rect() -> Rect2:
	return Rect2(300, 36, 340, 56)

## The title on a bamboo plaque hung above the cabinet.
func draw_title_mount(r: Rect2) -> void:
	rounded(r.grow(2), 5.0, UiKit.INK)
	rounded(r, 4.0, UiKit.SURFACE.bamboo)
	draw_rect(r.grow(-3), UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.3), false, 2.0)

func tab_rects() -> Array:
	return tabs.map(func(tb): return CELLS[tb.id])

## A compartment: its object at its native 96, the state on a hemp label; the open one lit, a locked one behind a lattice.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	var id := str(tabs[i].id)
	if state == "selected": glow(r.grow(12), Color(UiKit.GOLD, 0.5))
	rounded(r, 3.0, UiKit.SURFACE.wood_dark)
	glow(Rect2(r.position + Vector2(0, r.size.y * 0.3), Vector2(r.size.x, r.size.y * 0.8)), Color(UiKit.SURFACE.wood, 0.8))
	var lift := -4.0 * unfold() if state == "selected" else 0.0   # the chosen object lifts out of its place
	var locked := state == "disabled"
	icon_at(Rect2(r.get_center().x - 48, r.position.y + 2 + lift, 96, 96), str(OBJECT[id]), UiKit.PAPER.lerp(UiKit.HOLLOW, 0.5) if locked else Color.WHITE)
	if id == "furnace" and not locked: _furnace_salt(r)
	if locked: PostKit.lattice(self, r, UiKit.SURFACE.bamboo)
	draw_rect(r, UiKit.PALE_GOLD if state == "selected" else UiKit.SURFACE.bamboo.lerp(UiKit.INK, 0.25), false, 2.0)
	var line := str(tabs[i].locked) if locked else _state_line(id)
	var lh := 60.0 if locked else 42.0
	var lab := Rect2(r.position.x + 8, r.end.y - lh - 4, r.size.x - 16, lh)
	PostKit.hemp(self, lab)
	text(lab.position + Vector2(8 + (18.0 if locked else 0.0), 17), str(tabs[i].label), 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, lab.size.x - 30)
	if locked:
		_lock_icon(lab.position + Vector2(8, 3))
		para(Rect2(lab.position + Vector2(8, 20), Vector2(lab.size.x - 14, 38)), line, 14, UiKit.PAPER_INK, 2)
	else:
		text(lab.position + Vector2(8, 36), line, 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, lab.size.x - 14)
	if not locked and _ready_now(id): PostKit.ready_seal(self, Vector2(r.end.x - 20, r.position.y + 18))

## The furnace's last salt beside it, as it made it.
func _furnace_salt(r: Rect2) -> void:
	for sd in ContentDB.config("posts").get("salts", []):
		if Game.posts.salt_line(str(sd.id)).get("on", false):
			icon_at(Rect2(r.end.x - 90, r.position.y + 6, 64, 64), str(sd.id))
			return

## What a work's label says: its state in a line.
func _state_line(id: String) -> String:
	var ch = c()
	if ch == null: return ""
	match id:
		"arts": return Tx.plural("ui.works.s_points", Game.posts.art_points_free(ch)) % Game.posts.art_points_free(ch)
		"seals": return Tx.t("ui.works.s_seals") % _seals_ready()
		"steles":
			var best := ""
			for cr in Game.posts.crafts():
				if best == "" or Game.posts.stele_level(str(cr.id)) > Game.posts.stele_level(best): best = str(cr.id)
			if best == "" or Game.posts.stele_level(best) <= 0: return Tx.t("ui.works.s_none_raised")
			return Tx.t("ui.works.s_stele") % [str(Game.posts.craft_def(best).get("short", best)), Game.posts.stele_level(best)]
		"flags":
			var fl: Array = Game.posts.flags()
			if fl.is_empty(): return Tx.t("ui.works.s_none_planted")
			return Tx.t("ui.works.s_flags") % [fl.size(), int(ContentDB.config("posts").get("flags", {}).get("max", 2)), str(ContentDB.room(str(fl[0].room)).get("name", ""))]
		"furnace":
			for sd in ContentDB.config("posts").get("salts", []):
				var ln: Dictionary = Game.posts.salt_line(str(sd.id))
				if ln.get("on", false): return Tx.t("ui.works.s_line") % [ContentDB.item_name(str(sd.id)), UiKit.fmt(int(ln.get("refined", 0))), UiKit.fmt(PostRules.calcination_rank_need(int(ln.rank)))]
			return Tx.t("ui.works.s_no_line")
		"favours":
			var all: Array = ContentDB.config("posts").get("favours", [])
			return Tx.t("ui.works.s_favours") % [all.filter(func(f): return Game.posts.has_favour(str(f.id))).size(), all.size()]
		"mirror":
			if Game.posts.mirror_level() <= 0: return Tx.t("ui.works.mirror_unbuilt")
			return Tx.t("ui.works.s_mirror") % [Game.posts.mirror_level(), Game.posts.mirror_slots().filter(func(s): return not (s as Dictionary).is_empty()).size(), Game.posts.mirror_slot_count()]
	return ""

## The Seal Scripts the Storehouse can pay for now.
func _seals_ready() -> int:
	var n := 0
	for sd in ContentDB.config("posts").get("seals", []):
		if Game.posts.seal_level(str(sd.id)) >= int(sd.get("max", 10)): continue
		var cost: Dictionary = Game.posts.seal_next_cost(str(sd.id))
		if int(Game.account.storehouse.get(str(cost.item), 0)) >= int(cost.count): n += 1
	return n

## Something waits in this work: points to spend, a seal the Storehouse can pay for.
func _ready_now(id: String) -> bool:
	var ch = c()
	return ch != null and ((id == "arts" and Game.posts.art_points_free(ch) > 0) or (id == "seals" and _seals_ready() > 0))

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	tour_mark("cabinet", CABINET)   # decision 43: a tour's anchors
	tour_mark("tray", TRAY)
	tour_mark("slip", SLIP)
	_draw_slip()
	var id := str(tabs[tab].id)
	heading(TRAY.position + Vector2(16, 28), Tx.t("ui.works.head_" + id), 260)
	match id:
		"arts": _draw_arts()
		"seals": _draw_seals()
		"steles": _draw_steles()
		"favours": _draw_favours()
		"furnace": _draw_furnace()
		"flags": _draw_flags()
		"mirror": _draw_mirror()

## The tray's note beside the heading, up to `right` (clear of a work's header buttons).
func _note(s: String, right := TRAY.end.x - 16) -> void:
	var x := TRAY.position.x + 24 + minf(260.0, UiKit.text_width(Tx.t("ui.works.head_" + str(tabs[tab].id)), 26, true))
	text(Vector2(x, TRAY.position.y + 27), s, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, right - x)

func _area(top := 36.0) -> Rect2:
	return Rect2(TRAY.position.x + 12, TRAY.position.y + top, TRAY.size.x - 20, TRAY.size.y - top - 6)

## A locked tab's reason; true when the tab is open.
func _gate(unlock_id: String) -> bool:
	var ch = c()
	if ch == null: return false
	if Unlocks.is_unlocked(ch.id, unlock_id): return true
	para(Rect2(content.position + Vector2(4, 12), Vector2(content.size.x - 8, 80)), Unlocks.locked_text(unlock_id), 18, UiKit.HOLLOW)
	return false

## An effect line: `fmt` with the value, if the format takes one.
func _effect(fmt: String, v: float) -> String:
	if not "%s" in fmt: return fmt
	var step := (0.01 if v < 10.0 else 0.1) if "%%" in fmt else 0.001   # percents to 2 places, Flow and Windfall to 3
	var shown := str(snappedf(v, step))
	return fmt % shown

## A tray row's left: its icon, name and the line under it.
func _row(rr: Rect2, icon: String, name: String, lit: bool, sub: String, sub_col := UiKit.MIST, room := 380.0) -> void:
	draw_rect(Rect2(rr.position.x, rr.end.y + 1, rr.size.x, 1), Color(UiKit.BRONZE, 0.4))
	if icon != "": icon_at(Rect2(rr.position + Vector2(2, 10), Vector2(32, 32)), icon)
	text(rr.position + Vector2(44, 21), name, 18, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, room)
	text(rr.position + Vector2(44, 43), sub, 14, sub_col, HORIZONTAL_ALIGNMENT_LEFT, room)

## A cost in its well: the thing, what the Storehouse holds against what it takes, its name.
func _cost(at: Vector2, item: String, have: int, need: int) -> void:
	slot_box(Rect2(at, Vector2(SLOT_SMALL, SLOT_SMALL)), item)
	text(at + Vector2(52, 19), "%s / %s" % [UiKit.fmt(have), UiKit.fmt(need)], 16, UiKit.BRIGHT_JADE if have >= need else UiKit.RED_TEXT)
	text(at + Vector2(52, 39), ContentDB.item_name(item), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 96)

func _btn_at(rr: Rect2, back := 0.0) -> Rect2:
	return Rect2(rr.end.x - 132 - back, rr.position.y + 2, 128, 48)

# ------------------------------------------------------------------ Post Arts
func _draw_arts() -> void:
	if not _gate("post_arts"): return
	var ch = c()
	_note(Tx.t("ui.works.art_points") % Game.posts.art_points_free(ch), TRAY.end.x - 224)
	var cost := int(ContentDB.config("posts").get("arts", {}).get("reset_taels", 1000))
	btn(Rect2(TRAY.end.x - 216, TRAY.position.y + 6, 204, 48), Tx.t("ui.works.art_reset") % UiKit.fmt(cost), "art_reset", null, false,
		not Game.posts.arts(ch).is_empty(), Tx.t("ui.works.no_arts"), 16)
	var arts: Array = ContentDB.config("posts").get("post_arts", [])
	list("arts", _area(60), arts.size(), ROW, func(i: int, rr: Rect2):
		var a: Dictionary = arts[i]
		var id := str(a.id)
		var lv := Game.posts.art_level(ch, id)
		var mx := int(a.get("max", 1))
		var line := _effect(str(a.text), Game.posts._curve_of(a, lv)) if lv > 0 else Tx.t("ui.works.not_learned")
		if lv < mx: line += "   " + Tx.t("ui.works.next") % _effect(str(a.text), Game.posts._curve_of(a, lv + 1))
		_row(rr, "", "%s · %s" % [str(a.name), Tx.t("ui.works.level_of") % [lv, mx]], lv > 0, line, UiKit.BRIGHT_JADE if lv > 0 else UiKit.MIST, rr.size.x - 190)
		if lv < mx:
			btn(_btn_at(rr), Tx.t("ui.works.learn"), "art", id, true, Game.posts.art_points_free(ch) > 0, Tx.t("sim.posts.no_art_points"), 18)
	)

# ------------------------------------------------------------------ Seal Scripts (decision 26: five rows at once)
func _draw_seals() -> void:
	if not _gate("seal_scripts"): return
	var ch = c()
	_note(Tx.t("ui.works.seals_note_short"))
	var seals: Array = ContentDB.config("posts").get("seals", [])
	list("seals", _area(), seals.size(), ROW, func(i: int, rr: Rect2):
		var sd: Dictionary = seals[i]
		var id := str(sd.id)
		var lv := Game.posts.seal_level(id)
		var mx := int(sd.get("max", 10))
		var craft := str(sd.get("craft", ""))
		var eff := Game.posts._curve_of(sd, lv)
		var what := Tx.t("ui.works.seal_" + str(sd.gives[0])) % str(snappedf(eff, 0.1))
		if craft != "": what += " · " + Tx.t("ui.works.seal_yours") % Game.posts.seal_effective(ch, sd)
		_row(rr, str(ContentDB.entry("posts", craft).get("icon", "")) if craft != "" else str(sd.ladder[0]), str(sd.name), lv > 0,
			Tx.t("ui.works.level_of") % [lv, mx] + " · " + what)
		if lv >= mx:
			text(Vector2(rr.end.x - 200, rr.position.y + 32), Tx.t("ui.works.deepest"), 16, UiKit.PALE_GOLD)
			return
		var cost: Dictionary = Game.posts.seal_next_cost(id)
		var have := int(Game.account.storehouse.get(str(cost.item), 0))
		_cost(rr.position + Vector2(430, 4), str(cost.item), have, int(cost.count))
		btn(_btn_at(rr), Tx.t("ui.works.inscribe"), "seal", id, true, have >= int(cost.count),
			Tx.t("sim.posts.needs_stored") % [int(cost.count), ContentDB.item_name(str(cost.item))], 20)
	)

# ------------------------------------------------------------------ Guardian Steles
func _draw_steles() -> void:
	if not _gate("guardian_steles"): return
	var ch = c()
	_note(Tx.t("ui.works.steles_note_short"))
	var crafts: Array = Game.posts.crafts()
	var mx := int(ContentDB.config("posts").get("steles", {}).get("max", 40))
	list("steles", _area(), crafts.size(), ROW, func(i: int, rr: Rect2):
		var cr: Dictionary = crafts[i]
		var craft := str(cr.id)
		var lv := Game.posts.stele_level(craft)
		_row(rr, str(cr.get("icon", "")), Tx.t("ui.works.stele_of") % str(cr.name), lv > 0,
			Tx.t("ui.works.level_of") % [lv, mx] + " · " + Tx.t("ui.works.stele_power") % str(snappedf(Game.posts.stele_power(craft), 0.1)), UiKit.MIST, 300)
		if lv >= mx:
			text(Vector2(rr.end.x - 200, rr.position.y + 32), Tx.t("ui.works.highest"), 16, UiKit.PALE_GOLD)
			return
		var cost := PostRules.stele_cost(lv)
		var have := int(Game.account.storehouse.get(str(cost.item), 0))
		var can := have >= int(cost.count) and Game.economy.balance("silver_tael", ch) >= int(cost.taels)
		text(Vector2(rr.position.x + 340, rr.position.y + 32), Tx.t("ui.works.taels") % UiKit.fmt(int(cost.taels)), 16, UiKit.PAPER)
		_cost(rr.position + Vector2(430, 4), str(cost.item), have, int(cost.count))
		btn(_btn_at(rr), Tx.t("ui.works.raise"), "stele", craft, true, can, Tx.t("ui.works.cannot_pay"), 20)
	)

# ------------------------------------------------------------------ Magistrate's Favours
func _draw_favours() -> void:
	if not _gate("magistrates_favours"): return
	var ch = c()
	_note(Tx.t("ui.works.favours_note_short"))
	var favours: Array = ContentDB.config("posts").get("favours", [])
	list("favours", _area(), favours.size(), 72, func(i: int, r: Rect2):
		var f: Dictionary = favours[i]
		var id := str(f.id)
		var held := Game.posts.has_favour(id)
		_row(r, "", str(f.name), held, str(f.text), UiKit.MIST, r.size.x - 200)
		if held:
			text(Vector2(r.end.x - 128, r.position.y + 32), Tx.t("ui.works.granted"), 18, UiKit.PALE_GOLD)
			return
		var parts: Array = [Tx.t("ui.works.taels") % UiKit.fmt(int(f.taels))]
		var can := Game.economy.balance("silver_tael", ch) >= int(f.taels)
		for need in f.get("items", []):
			var have := int(Game.account.storehouse.get(str(need.item), 0))
			parts.append("%s %s (%s)" % [UiKit.fmt(int(need.count)), ContentDB.item_name(str(need.item)), UiKit.fmt(have)])
			if have < int(need.count): can = false
		text(r.position + Vector2(44, 63), Tx.t("ui.works.tribute") % ", ".join(parts), 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 200)
		btn(Rect2(r.end.x - 132, r.position.y + 10, 128, 48), Tx.t("ui.works.seek"), "favour", id, true, can, Tx.t("ui.works.cannot_pay"), 20)
	)

# ------------------------------------------------------------------ the Calcination Furnace
func _draw_furnace() -> void:
	if not _gate("calcination"): return
	Game.submit({"type": "settle_works", "part": "furnace"})
	_note(Tx.t("ui.works.furnace_note_short"))
	var salts: Array = ContentDB.config("posts").get("salts", [])
	list("furnace", _area(), salts.size(), 72, func(i: int, rr: Rect2):
		var sd: Dictionary = salts[i]
		var id := str(sd.id)
		var ln: Dictionary = Game.posts.salt_line(id)
		var rank := int(ln.rank)
		var on: bool = ln.get("on", false)
		if not Game.posts.line_open(id):
			_row(rr, id, "%s · %s" % [ContentDB.item_name(id), Tx.t("ui.works.rank") % rank], false, Tx.t("sim.posts.line_closed") % int(PostRules.rule_calc("open_rank", 3)), UiKit.HOLLOW)
			return
		var parts: Array = []
		for inp in sd.get("inputs", []):
			parts.append("%d %s (%s)" % [PostRules.calcination_cost(rank, int(inp.qty)), ContentDB.item_name(str(inp.item)), UiKit.fmt(int(Game.account.storehouse.get(str(inp.item), 0)))])
		_row(rr, id, "%s · %s" % [ContentDB.item_name(id), Tx.t("ui.works.rank") % rank], on,
			Tx.t("ui.works.every") % UiKit.span(float(sd.get("cycle_s", 900))) + ": " + ", ".join(parts), UiKit.MIST, rr.size.x - 330)
		text(rr.position + Vector2(44, 63), Tx.t("ui.works.fire") % [UiKit.fmt(int(ln.get("fire", 0))), PostRules.calcination_fire(rank),
			UiKit.fmt(int(ln.get("refined", 0))), UiKit.fmt(PostRules.calcination_rank_need(rank))], 14, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 330)
		btn(Rect2(rr.end.x - 296, rr.position.y + 10, 156, 48), Tx.t("ui.works.bank_line") if on else Tx.t("ui.works.light_line"), "line", [id, not on], not on, true, "", 16)
		btn(Rect2(rr.end.x - 132, rr.position.y + 10, 128, 48), Tx.t("ui.works.refine"), "refine", id, false, int(ln.get("fire", 0)) > 0, Tx.t("sim.posts.no_fire"), 18)
	)

# ------------------------------------------------------------------ Formation Flags
func _draw_flags() -> void:
	if not _gate("formation_flags"): return
	var ch = c()
	var fl: Dictionary = ContentDB.config("posts").get("flags", {})
	var here := str(ch.position.get("room", ""))
	var cost := UiKit.fmt(int(fl.get("plant_taels", 500)))
	_note(Tx.plural("ui.works.flags_note_short", int(fl.get("max", 2))) % int(fl.get("max", 2)), TRAY.end.x - 420)
	btn(Rect2(TRAY.end.x - 412, TRAY.position.y + 6, 196, 48), Tx.t("ui.works.plant_plain") % cost, "plant", "plain", true, true, "", 16)
	btn(Rect2(TRAY.end.x - 208, TRAY.position.y + 6, 196, 48), Tx.t("ui.works.plant_deep") % cost, "plant", "deep", false, true, "", 16)
	var list_flags: Array = Game.posts.flags()
	if list_flags.is_empty():
		para(Rect2(content.position + Vector2(4, 40), Vector2(content.size.x - 8, 60)), Tx.t("ui.works.no_flags") % str(ContentDB.room(here).get("name", here)), 18, UiKit.HOLLOW)
		return
	list("flags", _area(60), list_flags.size(), ROW, func(i: int, rr: Rect2):
		var f: Dictionary = list_flags[i]
		var kind := str(f.kind)
		var lv := int(f.get("level", 0))
		var eff := Tx.t("ui.works.flag_eff_" + kind) % str(snappedf(PostRules.flag_value(kind, lv), 0.1))
		_row(rr, "", "%s · %s" % [Tx.t("ui.works.flag_" + kind), str(ContentDB.room(str(f.room)).get("name", ""))], str(f.room) == here,
			Tx.t("ui.works.level_of") % [lv, int(fl.get("max_level", 20))] + " · " + eff, UiKit.MIST, 330)
		var nc := PostRules.flag_cost(lv)
		if not nc.is_empty() and lv < int(fl.get("max_level", 20)):
			var have := int(Game.account.storehouse.get(str(nc.salt), 0))
			_cost(rr.position + Vector2(330, 4), str(nc.salt), have, int(nc.salt_count))
			btn(_btn_at(rr, 136), Tx.t("ui.works.raise"), "flag_raise", i, true, have >= int(nc.salt_count), Tx.t("ui.works.cannot_pay"), 18)
		btn(_btn_at(rr), Tx.t("ui.works.uproot"), "flag_uproot", i, false, true, "", 18)
	)

# ------------------------------------------------------------------ the Mirror of Echoes
func _draw_mirror() -> void:
	if not _gate("mirror_of_echoes"): return
	var ch = c()
	Game.submit({"type": "settle_works", "part": "mirror"})
	var lv := Game.posts.mirror_level()
	if lv <= 0:
		_note(Tx.t("ui.works.mirror_note_short"))
		para(Rect2(content.position + Vector2(4, 12), Vector2(content.size.x - 8, 60)), Tx.t("ui.works.mirror_unbuilt"), 18, UiKit.HOLLOW)
		return
	var share := Game.posts.art_sum(ch, "echo_share") * (1.0 + float(ContentDB.config("posts").get("mirror", {}).get("per_level", 0.05)) * lv)
	_note(Tx.t("ui.works.mirror_level") % [lv, str(snappedf(share, 0.1))])
	var slots: Array = Game.posts.mirror_slots()
	list("mirror", _area(), Game.posts.mirror_slot_count(), 72, func(i: int, r: Rect2):
		var sl: Dictionary = slots[i] if i < slots.size() else {}
		_row(r, "", Tx.t("ui.works.mirror_slot") % (i + 1) + ("" if sl.is_empty() else " · " + str(sl.get("name", ""))), not sl.is_empty(),
			Tx.t("ui.works.mirror_empty") if sl.is_empty() else "", UiKit.HOLLOW, r.size.x - 260)
		var k := 0
		for id in sl.get("items", {}):
			if k >= 3: break
			icon_at(Rect2(r.position.x + 44 + k * 140, r.position.y + 30, 32, 32), str(id))
			text(Vector2(r.position.x + 80 + k * 140, r.position.y + 52), Tx.t("ui.posts.per_hour") % UiKit.fmt(snappedf(float(sl.items[id]), 0.1)), 14, UiKit.PAPER)
			k += 1
		btn(Rect2(r.end.x - 236, r.position.y + 10, 232, 48), Tx.t("ui.works.mirror_inscribe") % str(ch.name), "echo", i, true,
			Game.posts.art_level(ch, "echo_sampling") > 0 and Game.posts.has_post(ch), Tx.t("sim.posts.needs_echo"), 16)
	)

# ------------------------------------------------------------------ the inventory slip: what the works add
func _draw_slip() -> void:
	var ch = c()
	PostKit.hemp(self, SLIP)
	if ch == null: return
	var x := SLIP.position.x + 16
	var w := SLIP.size.x - 32
	UiKit.draw_text(self, Tx.t("ui.works.slip_title"), Vector2(x, SLIP.position.y + 34), 26, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true, true)
	if text_log != null: _log_text(Vector2(x, SLIP.position.y + 34), Tx.t("ui.works.slip_title"), 26, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true, Rect2(), UiKit.PAPER_INK)
	text(Vector2(x, SLIP.position.y + 56), Tx.t("ui.works.slip_for") % str(ch.name), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
	draw_rect(Rect2(SLIP.position.x, SLIP.position.y + 66, SLIP.size.x, 2), UiKit.BRONZE)
	var y := SLIP.position.y + 76
	var idle: Array = []
	for cr in Game.posts.crafts():
		var craft := str(cr.id)
		var parts: Array = []
		if Game.posts.stele_level(craft) > 0: parts.append(Tx.t("ui.works.adds_stele") % [str(snappedf(Game.posts.stele_power(craft), 0.1)), Game.posts.stele_level(craft)])
		var fin := Game.posts.seal_sum(ch, "finesse_flat", craft)
		if fin > 0.0: parts.append(Tx.t("ui.works.adds_seal") % str(snappedf(fin, 0.1)))
		if parts.is_empty():
			idle.append(str(cr.get("short", cr.name)))
			continue
		if y > SLIP.position.y + 300: continue
		y = _slip_line(Vector2(x, y), str(cr.get("icon", "")), str(cr.name), " · ".join(parts), w)
	var every: Array = []
	for key in ["craft_diligence", "finesse_pct", "capacity_pct"]:
		var v := Game.posts.art_sum(ch, key) + (Game.posts.seal_sum(ch, key) if key != "finesse_pct" else 0.0) + (Game.posts.favour_sum(key) if key == "craft_diligence" else 0.0)
		if v > 0.0: every.append(Tx.t("ui.works.adds_" + key) % str(snappedf(v, 0.01)))
	if not idle.is_empty(): y = _slip_line(Vector2(x, y), "", ", ".join(idle), Tx.t("ui.works.adds_nothing"), w)
	y = _slip_line(Vector2(x, y), "post", Tx.t("ui.works.every_post"), " · ".join(every) if not every.is_empty() else Tx.t("ui.works.adds_nothing"), w)
	var room := Game.posts.work_room(ch)
	var fd := Game.posts.flag_sum(room, "craft_diligence")
	var ff := Game.posts.flag_sum(room, "finesse_pct")
	if fd > 0.0 or ff > 0.0:
		var fp: Array = []
		if fd > 0.0: fp.append(Tx.t("ui.works.adds_craft_diligence") % str(snappedf(fd, 0.01)))
		if ff > 0.0: fp.append(Tx.t("ui.works.adds_finesse_pct") % str(snappedf(ff, 0.01)))
		y = _slip_line(Vector2(x, y), "", Tx.t("ui.works.posts_at") % str(ContentDB.room(room).get("name", "")), " · ".join(fp), w)
	# The Storehouse and the silver the works are paid with.
	var sy := SLIP.end.y - 216
	draw_rect(Rect2(SLIP.position.x, sy, SLIP.size.x, 2), UiKit.BRONZE)
	text(Vector2(x, sy + 26), Tx.t("ui.works.in_store"), 16, UiKit.PAPER_INK)
	var ids: Array = Game.account.storehouse.keys()
	ids.sort_custom(func(a, b): return int(Game.account.storehouse[a]) > int(Game.account.storehouse[b]))
	for i in mini(6, ids.size()):
		slot_box(Rect2(x + i * 52, sy + 36, 48, 48), str(ids[i]))
		UiKit.draw_outlined(self, UiKit.fmt(int(Game.account.storehouse[ids[i]])), Vector2(x + i * 52, sy + 82), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 46)
	if ids.is_empty(): text(Vector2(x, sy + 64), Tx.t("ui.posts.store_empty"), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w)
	currency_pill(Vector2(x, sy + 100), "silver_tael", Game.economy.balance("silver_tael", ch))
	para(Rect2(x, sy + 144, w, 60), Tx.t("ui.works.slip_note"), 14, UiKit.PAPER_INK, 3)

## One line of the slip: a glyph, what it is about and what the works add to it. Returns the next line's top.
func _slip_line(at: Vector2, icon: String, head: String, line: String, w: float) -> float:
	if icon != "": icon_at(Rect2(at, Vector2(32, 32)), icon)
	text(at + Vector2(40, 18), head, 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, w - 40)
	var h := para(Rect2(at + Vector2(40, 24), Vector2(w - 40, 36)), line, 14, UiKit.PAPER_INK, 2)
	return at.y + maxf(48.0, 28.0 + h + 8.0)

# ------------------------------------------------------------------ actions
func on_action(id: String, data) -> void:
	match id:
		"art":
			var r := submit({"type": "learn_post_art", "art": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.learned") % int(r.level))
		"art_reset":
			var r := submit({"type": "reset_post_arts"})
			if r.get("ok", false): flash(Tx.t("ui.works.arts_forgotten"))
		"seal":
			var r := submit({"type": "inscribe_seal", "seal": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.inscribed") % int(r.level))
		"stele":
			var r := submit({"type": "raise_stele", "craft": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.raised") % int(r.level))
		"favour":
			var r := submit({"type": "seek_favour", "favour": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.favour_granted"))
		"line": submit({"type": "calcine_line", "line": str(data[0]), "on": bool(data[1])})
		"refine":
			var r := submit({"type": "refine_line", "line": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.refined") % [int(r.salts), ContentDB.item_name(str(data)), int(r.rank)])
		"plant":
			var r := submit({"type": "plant_flag", "kind": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.planted"))
		"flag_raise": submit({"type": "raise_flag", "index": int(data)})
		"flag_uproot": submit({"type": "uproot_flag", "index": int(data)})
		"echo":
			var r := submit({"type": "echo_inscribe", "slot": int(data)})
			if r.get("ok", false): flash(Tx.t("ui.works.echoed"))
