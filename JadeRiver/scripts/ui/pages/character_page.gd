extends Page
## Character (S10, S11, S18, S34), P5 as the jade-slip record (docs/page_identity.md row 13, mockup 09 v2): the
## cultivator's life kept on bound jade slips, as a sect keeps its disciples' records. The whole window is one mat of
## vertical slips bound by two gold cords, the title and the tabs jade tags knotted to the upper cord. The figure stands
## full-length on the first slips, washed lighter as if painted there, with the eight worn slots down the slips either
## side (decision 8) and who walks beside; the register is written across the rest: realm, sect and title, origin, the
## pools, offence and defence in ruled columns, and the titles as honours (decision 16): red lacquer tablets, each with
## its motif on a gilt boss and its gift inscribed in gold, the worn one in a gilded frame. Aptitude, Attunement and
## Wardrobe are written on the same slips.

## The figure at a whole number of screen px per art px (sheets are 2 px per art px, so 2.5 is 5 each), feet on the slips.
const FIGURE_SCALE := 2.5
## Decision 42: a top-down character's figure (TopdownDoll) at 6 screen px an art px, and a friend's face in a chip at 1.
const TOP_SCALE := 5      # decision 43: the 46 px figure at x5 stands as tall as the 38 px one did at x6
const FEET := Vector2(278, 528)
## The worn slots down the slips either side of the figure (each 76 px slot's top-left).
const WORN := {"hat": Vector2(100, 170), "robe": Vector2(100, 284), "trousers": Vector2(100, 398), "boots": Vector2(100, 512),
	"weapon": Vector2(398, 170), "gourd": Vector2(398, 284), "cape": Vector2(398, 398), "talisman": Vector2(398, 512)}
const PAINTED := Rect2(64, 32, 440, 656)   # the figure's slips, washed lighter
const SLIP_W := 40.0
const CORDS := [92.0, 682.0]
const REG := 520.0                          # the register's left edge
## The register's two ruled columns: [stat, the words that name it].
const OFFENCE := [["physical_attack", "ui.character.physical_attack"], ["qi_attack", "ui.character.qi_attack"], ["soul_attack", "ui.character.soul_attack"],
	["accuracy", "ui.character.accuracy"], ["crit_chance", "ui.character.critical_chance"], ["crit_damage", "ui.character.critical_damage"],
	["attack_speed", "ui.character.attack_speed"]]
const DEFENCE := [["physical_defense", "ui.character.physical_defence"], ["qi_resistance", "ui.character.qi_resistance"], ["soul_defense", "ui.character.soul_defence"],
	["evasion", "ui.character.evasion"], ["will", "ui.character.will"], ["regen", "ui.character.regen"], ["move_speed", "ui.character.move_speed"]]
## The honours: three to a row, two rows; five tablets and the button to the next five (or six, when that is all).
const HONOUR := Vector2(216, 48)
const HONOUR_GAP := 10.0
const HONOURS_SHOWN := 5
## A title's motif (build_ui_hd.py MOTIFS), by the stat its gift raises: its family, as a sign on the gilt boss.
const MOTIF := {"physical_attack": "blade", "qi_attack": "blade", "fist_attack": "blade", "crit_chance": "blade", "pressure": "blade",
	"physical_defense": "shield", "evasion": "shield", "will": "shield", "hollow_ward": "shield", "max_hp": "pearl", "max_soul": "pearl",
	"move_speed": "cloud", "essence": "peak", "spirit": "peak", "fortune": "peak", "accumulation_rate": "lotus", "coin_find": "coin",
	"drop_rate": "coin", "crafting_control": "cauldron", "crafting_perception": "cauldron", "mining_power": "cauldron"}

var doll: Node2D
var mates: Array = []                       # the companions' small figures in the chips beside the figure
var title_page := 0

func _init() -> void:
	title = Tx.t("ui.character.character")
	tabs = [{"id": "overview", "label": Tx.t("ui.character.overview")}, {"id": "aptitude", "label": Tx.t("ui.character.aptitude")},
		{"id": "attunement", "label": Tx.t("ui.character.attunement")}, {"id": "wardrobe", "label": Tx.t("ui.character.wardrobe")}]
	identity = Identity.new("cloth", false, "own", "slip_mat_whole_two_cords", OPEN_MOTION_MAX)
	grade_rims = true

func content_rect() -> Rect2:
	return Rect2(96, 112, 1088, 552)

func setup() -> void:
	# Decision 42: the character as its game draws it: the top-down figure for a top-down character, three-quarters
	# toward the camera; the side view's for a classic one.
	doll = Figures.for_outfit(InventoryAuthority.outfit_for(c()), FIGURE_SCALE, TOP_SCALE)
	doll.position = FEET
	add_child(doll)
	for cid in (c().companions.get("active", []) as Array):
		var out = ContentDB.entry("companions", str(cid)).get("outfit")
		var m := Figures.chip(out, Rect2(-14, -40, 28, 30), Vector2(26, 30))   # the head and shoulders, inside the chip
		add_child(m)
		mates.append(m)

func _process(delta: float) -> void:
	super._process(delta)
	var id := str(tabs[tab].id)
	if is_instance_valid(doll): doll.visible = id in ["overview", "wardrobe"]
	for m in mates:
		if is_instance_valid(m): m.visible = id == "overview"

# ------------------------------------------------------------------ the page's own surface
## The mat: vertical jade slips on an ink backing, fanned open from a bundle as the page opens; the figure's slips
## washed lighter; two gold cords with their knots.
func draw_surface(r: Rect2) -> void:
	rounded(r.grow(2), 18.0, UiKit.INK)
	var spread := lerpf(0.3, 1.0, unfold())
	var n := int(ceil(r.size.x / SLIP_W))
	# The slips the figure stands on are washed lighter, as if painted: on the tabs that show the figure.
	var figure := str(tabs[tab].id) in ["overview", "wardrobe"]
	for i in n:
		var x := r.position.x + i * SLIP_W * spread
		var painted := figure and x < PAINTED.end.x - 1.0
		rounded(Rect2(x + 1, r.position.y + 1, minf(SLIP_W - 2.0, r.end.x - x - 1.0), r.size.y - 2), 8.0,
			UiKit.SURFACE.cloth.lerp(UiKit.SURFACE.cloth_wash, 0.35) if painted else UiKit.SURFACE.cloth)
	if figure:
		glow(Rect2(Vector2(290, 392) - Vector2(240, 330), Vector2(480, 660)), UiKit.SURFACE.cloth_wash)
		for i in n:
			var x := r.position.x + i * SLIP_W * spread
			if x > PAINTED.end.x: break
			draw_rect(Rect2(x + SLIP_W - 1.0, r.position.y + 8, 2, r.size.y - 16), Color(UiKit.INK, 0.55))
	for i in n:
		var x := r.position.x + i * SLIP_W * spread
		draw_line(Vector2(x + 2, r.position.y + 8), Vector2(x + 2, r.end.y - 8), Color(UiKit.BRIGHT_JADE, 0.1), 1.0)
	ground(r, UiKit.SURFACE.cloth)
	if figure: ground(PAINTED, UiKit.SURFACE.cloth_wash)
	for y in CORDS:
		draw_rect(Rect2(56, y + 7, 1168, 3), Color(UiKit.INK, 0.4))
		draw_rect(Rect2(56, y - 1, 1168, 8), UiKit.INK)
		for k in 3: draw_rect(Rect2(57, y + k * 2, 1166, 2), [UiKit.PALE_GOLD, UiKit.GOLD, UiKit.BRONZE][k])
		for x in [60.0, 1220.0]:
			draw_circle(Vector2(x, y + 3), 10.5, UiKit.INK, true, -1.0, true)
			draw_circle(Vector2(x, y + 3), 9.0, UiKit.GOLD, true, -1.0, true)
			draw_circle(Vector2(x - 3, y), 3.0, UiKit.PALE_GOLD, true, -1.0, true)

func title_rect() -> Rect2:
	return Rect2(180, 40, 220, 50)

## Decision 43: the "?" beside the title (the tabs and purses take the row left of the close button).
func help_rect() -> Rect2:
	var tr := title_rect()
	return Rect2(tr.end.x + 12, roundf(tr.get_center().y - 26), 52, 52)

## The title on a jade tag knotted to the upper cord.
func draw_title_mount(r: Rect2) -> void:
	draw_line(Vector2(r.get_center().x, r.end.y - 4), Vector2(r.get_center().x, CORDS[0] + 2), UiKit.GOLD, 3.0)
	face(r, "jade_label")

func tab_rects() -> Array:
	var out: Array = []
	var x := REG
	for tb in tabs:
		var w := UiKit.text_width(str(tb.label), 20) + 40
		out.append(Rect2(x, 40, w, TAB_H))
		x += w + TAB_GAP
	return out

## The tabs are jade tags on the cord; the open one is the lit jade.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	face(r, "jade_tag", "selected" if state == "selected" else "normal")
	if state == "selected": inked(r.position + Vector2(0, 31), str(tabs[i].label), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, false)
	else: text(r.position + Vector2(0, 31), str(tabs[i].label), 20, UiKit.HOLLOW if state == "disabled" else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

# ------------------------------------------------------------------ drawing
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	match str(tabs[tab].id):
		"overview": _overview(ch)
		"aptitude": _aptitude(ch, content)
		"attunement": _attunement(ch, content)
		"wardrobe": _wardrobe(ch, content)

func _overview(ch) -> void:
	# Decision 43: a tour's anchors (the figure's slips, the register and the titles).
	tour_mark("figure", PAINTED)
	tour_mark("register", Rect2(REG - 8, 112, 684, 430))
	tour_mark("titles", Rect2(REG - 8, 540, 684, 140))
	# The name written down the figure's slips, the figure's shadow, the worn slots either side, who walks beside.
	text(Vector2(196, 138), str(ch.name), 22, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 180, true)
	var sect_id := str(ch.training_sect.get("id", ""))
	if sect_id != "": text(Vector2(186, 158), Tx.t("ui.character.of_sect") % ContentDB.name_of("sects", sect_id), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 200)
	glow(Rect2(FEET + Vector2(-68, 20), Vector2(160, 24)), Color(UiKit.INK, 0.35))
	draw_worn(self, ch, WORN, "worn", UiKit.PAPER)
	_party(ch)
	_record(ch)
	_titles(ch)

## The worn slots at `at` (slot -> the 76 px slot's top-left), each with its name under it, round the figure (decision
## 8): the self family's slots, for the Character page and the Bag. A closed slot shows its lock and answers a tap with
## what opens it; an empty one glows jade while the bag holds a piece the character may wear there. A tap on an open slot
## is region `id` with the slot's name. `ringed` is the slot the Bag's card is about (the one tapped, or the one a
## chosen piece would go in): a dashed gold ring round it and its name in pale gold.
static func draw_worn(pg: Page, ch, at: Dictionary, id: String, name_col: Color, ringed := "") -> void:
	for slot in at:
		var r := Rect2(at[slot], Vector2(SLOT, SLOT))
		var inst = ch.inventory.equipped.get(slot)
		var why := locked_reason(ch, slot)
		var col := name_col
		if inst != null:
			pg.slot_box(r, str(inst.id), 1, str(inst.get("quality", "")), id, slot)
		else:
			pg.draw_style_box(UiKit.style("slot", "disabled" if why != "" else "normal"), r)
			if why != "":
				pg.lock_icon(r.get_center() - Vector2(8.4, 11.0), 1.4)
				col = UiKit.HOLLOW
			elif wearable_in_bag(ch, slot) != "":
				# A hint, not a selection: a jade edge and halo (the selection glow is gold).
				for k in 3: pg.draw_rect(r.grow(2.0 + k * 3.0), Color(UiKit.BRIGHT_JADE, 0.3 - k * 0.09), false, 3.0)
				pg.draw_rect(r.grow(1), UiKit.BRIGHT_JADE, false, 2.0)
				col = UiKit.BRIGHT_JADE
			pg.region(r, id, slot, why == "", why)
		if slot == ringed:
			var g := r.grow(6)
			pg.draw_rect(g.grow(2), Color(UiKit.GOLD, 0.25), false, 4.0)
			for e in [[g.position, Vector2(g.end.x, g.position.y)], [Vector2(g.end.x, g.position.y), g.end], [g.end, Vector2(g.position.x, g.end.y)],
					[Vector2(g.position.x, g.end.y), g.position]]:
				pg.draw_dashed_line(e[0], e[1], UiKit.GOLD, 2.0, 5.0)
			col = UiKit.PALE_GOLD
		pg.text(Vector2(r.position.x - 8, r.end.y + 18), Tx.t("ui.inventory." + slot), 14, col, HORIZONTAL_ALIGNMENT_CENTER, SLOT + 16)

## Why a worn slot is closed to `ch`, or "" when it is open (the weapon slot always is: bare fists until one is worn).
static func locked_reason(ch, slot: String) -> String:
	match slot:
		"cape": return "" if Unlocks.is_unlocked(ch.id, "cape_slot") else Tx.t("ui.inventory.cape_slot_opens_at_heaven")
		"talisman": return "" if Unlocks.is_unlocked(ch.id, "spirit_sense") else Tx.t("ui.inventory.soul_talisman_slot_opens_at")
	return ""

## A piece in the bag for `slot` that `ch` may put on (its id), or "".
static func wearable_in_bag(ch, slot: String) -> String:
	for s in ch.inventory.bag:
		if s == null: continue
		var def := ContentDB.item(str(s.id))
		if str(def.get("slot", "")) == slot and RequirementRules.passes(def.get("requires", {}), Game.ctx(ch)): return str(s.id)
	return ""

## Who walks beside: the active spirit animal and companions in small round chips, their names under them.
func _party(ch) -> void:
	var pet: Dictionary = Game.pets.active_pet(ch)
	var names: Array = []
	if not pet.is_empty(): names.append(str(pet.name))
	names.append_array((ch.companions.get("active", []) as Array).map(func(cid): return ContentDB.name_of("companions", str(cid))))
	if names.is_empty(): return
	text(Vector2(184, 580), Tx.t("ui.character.beside_you"), 14, UiKit.PAPER)
	var x := 184.0 + UiKit.text_width(Tx.t("ui.character.beside_you"), 14) + 26.0
	for i in names.size():
		var cen := Vector2(x + i * 44.0, 574)
		draw_circle(cen, 20.0, UiKit.INK, true, -1.0, true)
		draw_circle(cen, 18.0, UiKit.DEEP_TEAL, true, -1.0, true)
		draw_arc(cen, 19.0, 0.0, TAU, 32, Color(UiKit.GOLD, 0.6), 1.5, true)
		if i == 0 and not pet.is_empty():
			creature_at(Rect2(cen - Vector2(14, 14), Vector2(28, 28)), str(ContentDB.entry("pets", str(pet.species)).get("art", pet.species)))
		else:
			var mi := i - (0 if pet.is_empty() else 1)
			if mi < mates.size() and is_instance_valid(mates[mi]): mates[mi].position = cen + Figures.pick(mates[mi], Vector2(0, 28), Vector2(0, 2))
	text(Vector2(184, 616), " · ".join(names), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 212)

## The register written across the slips: name, realm and Level with its stage pips, sect, rank and worn title, origin,
## Combat Power and Relations, the pools, and offence and defence in ruled columns.
func _record(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	text(Vector2(REG, 140), str(ch.name), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 360, true)
	var realm := ContentDB.text("realm." + cu.realm_key)
	var bw := UiKit.text_width(realm, 16) + 20
	face(Rect2(REG, 152, bw, 26), "realm_badge")
	text(Vector2(REG + 10, 170), realm, 16, UiKit.PALE_GOLD)
	var lv := ProgressionRules.level(ch)
	var lv_s := Tx.t("ui.character.level") % lv
	text(Vector2(REG + bw + 12, 171), lv_s, 18, UiKit.PAPER)
	var px := REG + bw + 24 + UiKit.text_width(lv_s, 18)
	var r := ContentDB.realm(cu.realm_key)
	var steps := int(r.get("levels", 1))
	if steps > 1:
		# The stage's Levels as pips: those passed in gold, this one pale gold, the rest dim.
		for i in steps:
			var at := lv - int(r.get("level", 0))
			rounded(Rect2(px + i * 26, 161, 22, 8).grow(1.5), 5.0, UiKit.INK)
			rounded(Rect2(px + i * 26, 161, 22, 8), 4.0, UiKit.GOLD if i < at else (UiKit.PALE_GOLD if i == at else Color(UiKit.GOLD, 0.25)))
		px += steps * 26 + 8
	if cu.false_realm != "": text(Vector2(px, 171), Tx.t("ui.character.shown_as") % ContentDB.realm_label(cu.false_realm), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 880 - px)
	var sect_id := str(ch.training_sect.get("id", ""))
	var runs: Array = [[(ContentDB.name_of("sects", sect_id) + " · " + ContentDB.rank_name(str(ch.training_sect.get("rank", "")))) if sect_id != "" else Tx.t("ui.character.unaffiliated"), UiKit.PAPER]]
	if cu.active_title != "": runs.append_array([["·", UiKit.MIST], ["◆", UiKit.GOLD], [ContentDB.name_of("titles", cu.active_title), UiKit.BRIGHT_JADE]])
	rich(Rect2(REG, 186, 380, 24), runs, 18)
	# Combat Power and Relations at the right; the age under them.
	text(Vector2(900, 120), Tx.t("ui.character.combat_power"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 140)
	text(Vector2(900, 152), UiKit.fmt(StatRules.combat_power(ch)), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 140, true)
	btn(Rect2(1052, 108, 136, 48), Tx.t("ui.character.relations"), "relations", null, false, true, "", 18)
	# S49: the Relations page (karma, bonds, grudges, Fame) lives under Character.
	var fame := Tx.t("ui.relations.fame_" + str(Game.relations.fame_tier(ch).get("id", "unknown"))) + " · " + Tx.t("ui.relations.align_" + Game.relations.alignment_word(ch))
	text(Vector2(1188 - maxf(136.0, UiKit.text_width(fame, 14)), 174), fame, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, maxf(136.0, UiKit.text_width(fame, 14)))
	# S49 lifespan as flavour: your age and the most years your realm grants (never a clock).
	var span := ProgressionRules.lifespan_of(ch)
	var age := ProgressionRules.age_of(ch, Clock.now_utc())
	text(Vector2(900, 204), Tx.t("ui.character.age_span") % [age, UiKit.fmt(span)] if span > 0 else Tx.t("ui.character.age_endless") % age, 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 288)
	# The origin and what it gave: its own words where they fit the line, else what it gave in short.
	var origin := ContentDB.entry("origins", cu.origin)
	var oname := str(origin.get("name", cu.origin))
	var odesc := "· " + str(origin.get("desc", ""))
	if UiKit.text_width(oname + " " + odesc, 16) > 668:
		var gave: Array = (origin.get("bonus", {}) as Dictionary).keys().map(func(k): return "+%d %s" % [int(origin.bonus[k]), str(k).capitalize()])
		if str(origin.get("element_nudge", "")) != "": gave.append(Tx.t("ui.character.leans_to") % str(origin.element_nudge))
		odesc = "· " + ", ".join(gave)
	text(Vector2(REG, 234), oname, 16, UiKit.GOLD)
	var ow := UiKit.text_width(oname + " ", 16)
	text(Vector2(REG + ow, 234), odesc, 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 668 - ow)
	# The pools (Qi and Soul once the character has them).
	var y := 246.0
	for p in [[ch.pools.hp, ch.pools.max_hp, UiKit.HP, "ui.character.hp_bar"], [ch.pools.qi, ch.pools.max_qi, UiKit.QI, "ui.character.qi_bar"],
			[ch.pools.soul, ch.pools.max_soul, UiKit.SOUL, "ui.character.soul_bar"]]:
		if float(p[1]) <= 0.0: continue
		bar(Rect2(REG, y, 668, 26), float(p[0]) / maxf(1.0, float(p[1])), p[2], Tx.t(str(p[3])) % UiKit.pool_values(float(p[0]), float(p[1])))
		y += 30
	_column(ch, Vector2(REG, 340), Tx.t("ui.character.offence"), OFFENCE)
	_column(ch, Vector2(864, 340), Tx.t("ui.character.defence"), DEFENCE)

## A ruled column of the register: its heading on a bronze rule, then a stat to a row, its value at the right.
func _column(ch, at: Vector2, head: String, rows: Array) -> void:
	text(at + Vector2(0, 22), head, 22, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, 324, true)
	draw_line(at + Vector2(0, 30), at + Vector2(324, 30), UiKit.BRONZE, 2.0)
	for i in rows.size():
		var y := at.y + 32 + i * 22
		text(Vector2(at.x, y + 16), Tx.t(str(rows[i][1])), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 214)
		text(Vector2(at.x + 214, y + 16), stat_shown(ch, str(rows[i][0])), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 110)
		draw_line(Vector2(at.x, y + 21), Vector2(at.x + 324, y + 21), Color(UiKit.GOLD, 0.25), 1.0)

## A stat as the register writes it: counts grouped, chances and damage as percents, attack speed as a bonus, and
## HP and Qi regeneration together.
static func stat_shown(ch, stat: String) -> String:
	if stat == "regen": return "%.1f%% · %.1f%%" % [ch.stats.value("hp_regen") * 100.0, ch.stats.value("qi_regen") * 100.0]
	return stat_text(stat, ch.stats.value(stat))

## A stat's value `v` as the register writes it (the Bag's card writes its changes the same way).
static func stat_text(stat: String, v: float) -> String:
	match stat:
		"crit_chance": return "%.1f%%" % (v * 100.0)
		"crit_damage": return "%d%%" % int(round(v * 100.0))
		"attack_speed": return "%+d%%" % int(round(v * 100.0))
	return UiKit.fmt(v)

## The titles as honours (decision 16): each a red lacquer tablet with its motif on a gilt boss, its name and its gift
## inscribed in gold on a sunk band; the worn one first, in a gilded frame and marked with the gold ◆. A tap wears one.
## Five at a time, and a button that turns to the next five.
func _titles(ch) -> void:
	var cu: CultivatorState = ch.cultivator
	var held: Array = cu.titles.filter(func(tid): return str(tid) == cu.active_title) + cu.titles.filter(func(tid): return str(tid) != cu.active_title)
	text(Vector2(REG, 566), Tx.t("ui.character.titles"), 22, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
	if held.is_empty():
		text(Vector2(REG, 612), Tx.t("ui.character.earn_titles_from_achievements_and"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, 668)
		return
	text(Vector2(REG + UiKit.text_width(Tx.t("ui.character.titles"), 22, true) + 16, 564), Tx.t("ui.character.titles_count") % [held.size(), ContentDB.all("titles").size()],
		14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 500)
	var per := HONOURS_SHOWN if held.size() > HONOURS_SHOWN + 1 else HONOURS_SHOWN + 1
	var pages := int(ceil(held.size() / float(per)))
	var first := (title_page % pages) * per
	for i in per:
		if first + i >= held.size(): break
		var tid := str(held[first + i])
		_honour(Rect2(Vector2(REG + (i % 3) * (HONOUR.x + HONOUR_GAP), 574 + (i / 3) * (HONOUR.y + 6)), HONOUR), tid, tid == cu.active_title)
	if pages > 1:
		var rest := held.size() - first - per
		btn(Rect2(Vector2(REG + 2 * (HONOUR.x + HONOUR_GAP), 628), HONOUR), Tx.t("ui.character.titles_more") % rest if rest > 0 else Tx.t("ui.character.titles_first"),
			"titles_more", null, false, true, "", 18)

## One honour: the tablet, the motif's boss, the name (the worn one after a gold ◆) and the gift inscribed on its band.
func _honour(r: Rect2, tid: String, worn: bool) -> void:
	face(r, "honour_tablet", "selected" if worn else "normal")
	var mods: Array = ContentDB.entry("titles", tid).get("modifiers", [])
	var motif := str(MOTIF.get(str(mods[0].get("stat", "")), "star")) if not mods.is_empty() else "star"
	draw_texture_rect(UiKit.hd_texture("honour_seal", motif), Rect2(r.position + Vector2(8, 8), Vector2(32, 32)), false)
	var x := r.position.x + 48
	var w := r.end.x - 8 - x
	var name := ContentDB.name_of("titles", tid)
	if worn:
		text(Vector2(x, r.position.y + 20), "◆", 14, UiKit.GOLD)
		x += UiKit.text_width("◆ ", 14)
		w = r.end.x - 8 - x
	text(Vector2(x, r.position.y + 20), name, 16 if UiKit.text_width(name, 16) <= w else 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
	var gift := ", ".join(mods.map(func(m): return UiKit.affix_text(m)))
	if gift != "":
		var band := Rect2(r.position.x + 46, r.position.y + 26, r.size.x - 54, 17)
		rounded(band, 3.0, Color(UiKit.INK, 0.4))
		draw_line(band.position + Vector2(3, band.size.y), band.end - Vector2(3, 0), Color(UiKit.GOLD, 0.3), 1.0)
		ground(band, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.4))
		text(band.position + Vector2(6, 13), gift, 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, band.size.x - 12)
	region(r, "title", tid)

## S47 wardrobe: for each slot, any look you have ever worn can stand in for the piece's own.
const WARDROBE_SLOTS := [["robe", "shirt"], ["trousers", "pants"], ["boots", "shoes"], ["hat", "hat"], ["weapon", "weapon"]]
func _wardrobe(ch, r: Rect2) -> void:
	if not Unlocks.is_unlocked(ch.id, "wardrobe"):
		para(Rect2(r.position.x + 424, r.position.y + 40, r.size.x - 440, 200), Unlocks.locked_text("wardrobe"), 20, UiKit.HOLLOW)
		return
	var x := r.position.x + 424
	var y := r.position.y + 34
	y += para(Rect2(x, y - 18, r.end.x - x, 48), Tx.t("ui.character.wardrobe_help"), 18, UiKit.MIST, 2)
	for pair in WARDROBE_SLOTS:
		var slot: String = pair[0]
		var cat: String = pair[1]
		var looks: Array = []
		for k in Game.account.wardrobe_unlocked:
			if str(k).begins_with(cat + ":"): looks.append(str(k).get_slice(":", 1))
		looks.sort()
		var cur := str(ch.inventory.appearance_override.get(slot, ""))
		text(Vector2(x, y + 34), Tx.t("ui.character.wardrobe_" + slot), 18, UiKit.PALE_GOLD)
		var bx := x + 130.0
		btn(Rect2(bx, y + 4, 120, 48), Tx.t("ui.character.own_look"), "look", [slot, ""], cur == "", true, "", 16)
		bx += 128
		for lk in looks:
			if bx + 120 > r.end.x - 20: break
			btn(Rect2(bx, y + 4, 120, 48), str(lk).replace("_", " ").capitalize(), "look", [slot, lk], cur == lk, true, "", 16)
			bx += 128
		y += 58

## S18 attunement: the four jades of the zone you stand in (or the first zone that asks for
## attunement), what raising each costs, and how the total compares with each region's need.
func _attunement(ch, r: Rect2) -> void:
	var here := str(ContentDB.zone_of_room(str(ch.position.get("room", ""))).get("id", ""))
	var zone_id := ""
	for z in ContentDB.all("zones"):
		if z.get("attunement") is Dictionary and (zone_id == "" or str(z.id) == here): zone_id = str(z.id)
	if zone_id == "":
		para(r.grow(-40), Tx.t("ui.character.no_attunement_yet"), 20, UiKit.HOLLOW)
		return
	var zone := ContentDB.zone(zone_id)
	var att: Dictionary = zone.attunement
	var x := r.position.x + 36
	heading(Vector2(x, r.position.y + 48), "%s · %s" % [str(att.get("name", "")), str(zone.get("name", ""))], r.size.x - 72)
	var total: float = Game.progression.attunement_value(ch, zone_id) if here == zone_id else float(ch.cultivator.attunement.get(zone_id, 0.0))
	var line := Tx.t("ui.character.attunement_total") % int(total)
	if here == zone_id:
		var need: float = Game.progression.attunement_required(str(ch.position.get("room", "")))
		var f: Dictionary = Game.progression.attunement_factors(ch)
		line += "   " + Tx.t("ui.character.attunement_here") % [int(need), int(round(float(f.dealt) * 100.0)), int(round(float(f.taken) * 100.0))]
	text(Vector2(x, r.position.y + 84), fit(line, 20, r.size.x - 72), 20, UiKit.MIST)
	var unlocked := Unlocks.is_unlocked(ch.id, str(att.get("unlock", "")))
	var shard := str(att.get("shard", ""))
	icon_at(Rect2(r.end.x - 250, r.position.y + 26, 36, 36), shard)
	text(Vector2(r.end.x - 206, r.position.y + 52), "%s × %s" % [ContentDB.item_name(shard), UiKit.fmt(ch.inventory.count(shard))], 18, UiKit.PALE_GOLD)
	var levels: Array = Game.progression.jade_levels(ch, zone_id)
	var jades: Array = att.get("jades", [])
	var cw := (r.size.x - 72 - 3 * 16) / 4.0
	for i in jades.size():
		var jr := Rect2(x + i * (cw + 16), r.position.y + 104, cw, 236)
		panel(jr, "minor_panel")
		icon_at(Rect2(jr.position.x + (cw - 88) / 2.0, jr.position.y + 12, 88, 88), "ward_" + str(jades[i].id))
		text(Vector2(jr.position.x, jr.position.y + 128), str(jades[i].name), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cw)
		var lv := int(levels[i]) if i < levels.size() else 0
		var top := int(att.get("jade_max", 15))
		bar(Rect2(jr.position.x + 14, jr.position.y + 142, cw - 28, 20), float(lv) / maxf(1.0, top), UiKit.QI, Tx.t("ui.character.jade_level") % [lv, top])
		if lv >= top:
			text(Vector2(jr.position.x, jr.position.y + 204), Tx.t("ui.character.jade_full"), 18, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, cw)
		else:
			var cost: int = Game.progression.jade_cost(zone_id, lv)
			var can: bool = unlocked and ch.inventory.count(shard) >= cost
			btn(Rect2(jr.position.x + 14, jr.position.y + 174, cw - 28, 48), Tx.plural("ui.character.raise_jade", cost) % cost, "attune", [zone_id, i], false, can,
				Unlocks.locked_text(str(att.get("unlock", ""))) if not unlocked else Tx.t("ui.character.needs_more_shards"), 18)
	# What each region asks for, ticked when the total meets it.
	var y := r.position.y + 366
	text(Vector2(x, y), Tx.t("ui.character.regions_ask"), 18, UiKit.GOLD)
	y += 4
	var col := 0
	for reg in zone.get("regions", []):
		if not reg.has("attunement"): continue
		var met := total >= float(reg.attunement)
		var at := Vector2(x + col * ((r.size.x - 72) / 2.0), y + 30)
		text(at, fit(("✓ " if met else "· ") + "%s  %d" % [str(reg.name), int(reg.attunement)], 18, (r.size.x - 72) / 2.0 - 12), 18, UiKit.BRIGHT_JADE if met else UiKit.MIST)
		col += 1
		if col == 2:
			col = 0
			y += 26

func on_action(id: String, data) -> void:
	if id == "relations": navigate.emit("relations", {})
	if id == "worn": navigate.emit("inventory", {"tab": str(data)})   # a worn slot opens the Bag on it
	if id == "title": submit({"type": "set_title", "title": str(data)})
	if id == "titles_more": title_page += 1
	if id == "attune": submit({"type": "attune_jade", "zone": str(data[0]), "index": int(data[1])})
	if id == "look":
		submit({"type": "set_appearance", "slot": str(data[0]), "look": str(data[1])})
		if is_instance_valid(doll): doll.outfit = InventoryAuthority.outfit_for(c())

## Aptitude (S08, S48): the hidden rolls as they are revealed, the root they name, and the physiques earned.
func _aptitude(ch, r: Rect2) -> void:
	var cu: CultivatorState = ch.cultivator
	var left := Rect2(r.position.x, r.position.y, 560, r.size.y)
	var right := Rect2(left.end.x + 20, r.position.y, r.end.x - left.end.x - 20, r.size.y)
	panel(left)
	panel(right)
	var x := left.position.x + 24
	var y := left.position.y + 20
	var root := ProgressionRules.root_name(cu)
	if root != "":
		text(Vector2(x, y + 30), Tx.t("ui.character.root." + root), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 48, true)
		y += 40
		y += para(Rect2(x, y, left.size.x - 48, 60), Tx.t("ui.character.root_desc." + root), 16, UiKit.MIST, 2) + 10
	else:
		text(Vector2(x, y + 30), Tx.t("ui.character.root_hidden"), 20, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 48)
		y += 52
	var reveal := {"physique": "bone_forging_4", "spirit_aptitude": "spirit_awakening_1", "comprehension": ""}
	var order: Array = []
	for k in ["physique", "spirit_aptitude", "comprehension"]:
		if cu.aptitude.has(k): order.append(k)
	var elements: Array = []
	for k in cu.aptitude:
		if str(k).begins_with("element_"): elements.append(str(k))
	elements.sort()
	order.append_array(elements)
	for k in order:
		var a: Dictionary = cu.aptitude[k]
		var key := str(k)
		var label := Tx.t("ui.character.apt." + key) if not key.begins_with("element_") else Tx.t("ui.character.apt_element") % key.trim_prefix("element_").capitalize()
		text(Vector2(x, y + 24), label, 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 260)
		if a.get("revealed", false):
			var v := float(a.get("value", 0.0))
			text(Vector2(x + 280, y + 24), "%s%d%%" % ["+" if v >= 0.0 else "-", int(round(absf(v) * 100))], 20, UiKit.BRIGHT_JADE if v > 0.0 else (UiKit.RED_TEXT if v < 0.0 else UiKit.PAPER))
		else:
			var at := str(reveal.get(key, "bone_forging_7"))
			text(Vector2(x + 280, y + 24), Tx.t("ui.character.apt_hidden_at") % ContentDB.name_of("realms", at) if at != "" else Tx.t("ui.character.unknown_revealed_as_you_grow"), 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, left.size.x - 330)
		y += 34
	# Physiques: earned by deeds; the ones not yet earned say how.
	var rx := right.position.x + 24
	var ry := right.position.y + 44
	heading(Vector2(rx, ry), Tx.t("ui.character.physiques"), right.size.x - 48)
	ry += 16
	for ph in ContentDB.all("physiques"):
		if str(ph.get("milestone", "")) != "" and not str(ph.id) in cu.physiques: continue
		var have := str(ph.id) in cu.physiques
		text(Vector2(rx, ry + 26), str(ph.get("name", "")), 20, UiKit.PALE_GOLD if have else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
		if have:
			var gift := str(ph.get("gift_text", ""))
			text(Vector2(rx, ry + 48), gift, 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
			var gw := UiKit.text_width(gift + "  ", 16)
			text(Vector2(rx + gw, ry + 48), str(ph.get("drawback_text", "")), 16, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, maxf(40.0, right.size.x - 48 - gw))
		else:
			var prog := ""
			if ph.has("count"): prog = "  (%s / %s)" % [UiKit.fmt(float(cu.lifetime_stats.get(str(ph.earned), 0.0))), UiKit.fmt(float(ph.count))]
			text(Vector2(rx, ry + 48), str(ph.get("earned_text", "")) + prog, 16, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_LEFT, right.size.x - 48)
		ry += 62
