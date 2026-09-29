extends Page
## Crafts (S15, S16): cooking, alchemy and the forge share one recipe book.
## Forging plays a short timing mini-game (three strikes into the glowing band). Alchemy plays the five-screen furnace
## (S15/S44): Ingredients and Furnace in the recipe panel, then Extraction, Fusion and Condensation full width from the
## refine the authority keeps (and the pill tribulation as a sixth). The authority scores every screen and rolls the quality.

var CRAFTS := [["cooking", Tx.t("ui.crafts.cooking")], ["alchemy", Tx.t("ui.crafts.alchemy")], ["smithing", Tx.t("ui.crafts.forge")], ["formations", Tx.t("ui.crafts.arrays")],
	["talisman", Tx.t("ui.crafts.talismans")], ["guild", Tx.t("ui.crafts.guild")], ["star_charting", Tx.t("ui.crafts.charts")], ["shipwright", Tx.t("ui.crafts.vessels")]]
## The unlock behind a tab when it is not the craft's own id (S44: the Alchemist Guild; the Guild tab opens with any guild).
const TAB_UNLOCK := {"guild": "alchemist_guild"}
## Page ids that open the Crafts page on one tab.
const PAGE_TAB := {"cooking": "cooking", "alchemy": "alchemy", "forge": "smithing", "arrays": "formations", "talisman": "talisman", "guild": "guild",
	"charts": "star_charting", "vessels": "shipwright"}
## S44: the alchemy list's own rows ahead of the recipes.
const EXPERIMENT := "__experiment"
var exp_herbs: Array = []          # the herbs chosen for an experiment
## The Starsea crafts (S16) take no mini-game: the chart or the hull is made in one go.
const DIRECT := {"cooking": "cook", "formations": "inscribe", "star_charting": "chart_route", "shipwright": "build_vessel"}

var sel := ""
var guild_craft := ""   # the guild shown on the Guild tab (its craft id)
var count := 1
var game_on := false
## S44 pill tribulation and the Pill Soul's flight: {stage: "bolts"|"soul", times[], window, t0 (ms), next, results[], catch_at}.
var trib: Dictionary = {}
var needle := 0.0
var needle_dir := 1.0
var scores: Array = []
var band := Vector2(0.45, 0.62)
var fire := "charcoal"
var subst: Dictionary = {}         # S44 Alchemy Dao tier 5: {from, to}, one herb standing in for another
## The five-screen furnace: which of the recipe panel's two screens shows, the array chosen for the furnace, the hand's
## side of the screen being played ({stage, t, ...}), whether the fan is held, and the controls that act on the press
## (the fan is held; the array's turn and Condense are timed), drawn this frame.
var screen := "ingredients"
var array := "water"
var play: Dictionary = {}
var fanning := false
var hot_rects: Dictionary = {}
var preview_rs: Dictionary = {}    # a refine drawn for a preview (--open-page=alchemy:__extraction); nothing is sent
## The Forge's upkeep modes (S47): forging from recipes, then Enhance, Inherit, Salvage and Reroll.
const FORGE_MODES := ["recipes", "enhance", "inherit", "salvage", "reroll", "natal"]
var forge_mode := "recipes"
var pick_uid := -1                 # the piece chosen in Enhance and Reroll, and Inherit's source
var to_uid := -1                   # Inherit's target
var picked: Dictionary = {}        # Salvage: uid -> true
var essence := 0
## S47 talisman tracing: the stroke path shown on paper, and the path the brush takes over it.
var trace_on := false
var trace_rect := Rect2()
var trace_pts: Array = []
var trace_t0 := 0.0
## The fires under a furnace (gap report G1), in the order the selector shows them.
const FIRES := ["charcoal", "earth_fire", "beast_fire", "heavenly_flame"]
## P5 (docs/page_identity.md row 18, mockup 15): where the step strip, the hearth and the controls stand in the window.
const STRIP := Rect2(96, 172, 1088, 60)
const HEARTH := Rect2(96, 244, 568, 428)
const SIDE := Rect2(680, 244, 504, 428)
const BLOCK_H := 88.0
## How hot each trade keeps its fire while nothing is played (the rest bank their embers under a plate, paper or chart).
const HEAT := {"cooking": 0.55, "alchemy": 0.4, "smithing": 0.8}
var puff_at := -9.0   # when a craft last came out of its vessel (the puff, 0.4 s)

func _init() -> void:
	title = Tx.t("ui.crafts.crafts")
	identity = Identity.new("wood_dark", false, "own", "vessel_over_fire_step_strip", 0.3)

func setup() -> void:
	var ch = c()
	tabs = []
	for cr in CRAFTS:
		# The Starsea tabs stay hidden until Sage 3 opens them, so the valley page is unchanged.
		if cr[0] in ["star_charting", "shipwright"] and not Unlocks.is_unlocked(ch.id, "star_charting"): continue
		var key := str(TAB_UNLOCK.get(cr[0], cr[0]))
		var open: bool = Unlocks.is_unlocked(ch.id, key) or (cr[0] == "guild" and not Game.crafting.guilds_open(ch).is_empty())
		tabs.append({"id": cr[0], "label": cr[1], "locked": "" if open else Unlocks.locked_text(key)})
	var want := -1
	for i in tabs.size():
		if str(tabs[i].id) == str(PAGE_TAB.get(page_id, "")): want = i
	# A page opened for one recipe (a quest link, or a preview: --open-page=alchemy:healing_pill).
	var pick := str(args.get("tab", ""))
	# The Guild tab shows the guild of the master who opened it (Smith Bao: the Forge Guild), or one named by a preview
	# (--open-page=guild:guild_smithing).
	for g in Game.crafting.guilds_open(ch):
		if str(g.get("master", "")) == str(args.get("npc", "")) or "guild_" + str(g.craft) == pick: guild_craft = str(g.craft)
	if ContentDB.has_entry("recipes", pick) or pick == EXPERIMENT: sel = pick
	if pick == "__tribulation":   # a preview of the tribulation screen (--open-page=alchemy:__tribulation); nothing is refined
		sel = "soul_soothing_pill"
		trib = {"stage": "bolts", "times": [0.2, 0.5, 1.0, 1.9, 2.8], "window": 0.22, "t0": Time.get_ticks_msec(), "next": 2, "results": [true, false], "preview": true}
	if pick in ["__furnace", "__extraction", "__scorched", "__fusion", "__fusion_turn", "__condensation"]:
		# Previews of the furnace's screens (--open-page=alchemy:__fusion); a preview plays nothing out.
		sel = "healing_pill"
		if pick == "__furnace": screen = "furnace"
		else: _preview(pick.trim_prefix("__"))
	var rs := Game.crafting.refine_session(ch)
	if not rs.is_empty():
		# A refine left burning when the page closed: pick it up where it was.
		sel = str(rs.recipe)
		count = int(rs.count)
		fire = str(rs.fire)
		array = str(rs.array)
		subst = (rs.substitute as Dictionary).duplicate()
	if pick in FORGE_MODES:   # --open-page=forge:enhance (a preview shows the first piece chosen)
		forge_mode = pick
		var gear := _gear(ch)
		if not gear.is_empty() and pick in ["enhance", "reroll", "natal"]: pick_uid = int(gear[0].inst.get("uid", -1))
	if want >= 0: tab = want
	else:
		for i in tabs.size():
			if str(tabs[i].locked) == "":
				tab = i
				break

func recipes_for(ch, craft: String) -> Array:
	var out: Array = []
	for r in ContentDB.all("recipes"):
		if str(r.craft) == craft and Game.crafting.knows(ch, str(r.id)): out.append(r)
	return out

func _process(delta: float) -> void:
	super._process(delta)
	if not trib.is_empty():
		# A bolt or a fleeing Soul that goes by unanswered counts as missed.
		var el := _trib_elapsed()
		if str(trib.stage) == "bolts" and int(trib.next) < (trib.times as Array).size() and el > float(trib.times[int(trib.next)]) + float(trib.window):
			_trib_answer(99.0)
		elif str(trib.stage) == "soul" and el > float(trib.catch_at) + float(trib.window):
			_trib_catch(99.0)
		queue_redraw()
	if not tabs.is_empty() and str(tabs[tab].id) == "alchemy": _tick_furnace(delta)
	if game_on:
		needle += needle_dir * delta * (0.9 + scores.size() * 0.35)
		if needle > 1.0:
			needle = 1.0
			needle_dir = -1.0
		elif needle < 0.0:
			needle = 0.0
			needle_dir = 1.0

## P5 (docs/page_identity.md row 18, mockup 15): the hearth. The trade's vessel stands centred over its fire on a brick
## hearth, its ingredients on the rim above it; the steps run as a strip across the top; the controls at the right change
## with the step and nothing else moves. The Forge's upkeep and the Guild lay their lists on the workshop wall instead.
func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var craft := str(tabs[tab].id)
	hot_rects.clear()
	# Decision 43: a tour's anchors (the recipe strip, the hearth where the work is done, the board beside it).
	tour_mark("strip", STRIP)
	tour_mark("hearth", HEARTH)
	tour_mark("side", SIDE)
	if str(tabs[tab].get("locked", "")) != "":
		para(Rect2(content.position + Vector2(30, 30), content.size - Vector2(60, 60)), str(tabs[tab].locked), 22, UiKit.MIST)
		return
	if craft == "guild":
		_guild(ch, content)
		return
	_strip(ch, craft)
	if craft == "smithing" and forge_mode != "recipes":
		_forge(ch, content)
		return
	var live := craft == "alchemy" and (not _session().is_empty() or not trib.is_empty())
	_hearth(ch, craft, live)
	WorkshopKit.board(self, SIDE)
	if live: _furnace_live()
	else: _recipe_view(ch, craft)

func content_rect() -> Rect2:
	return Rect2(STRIP.position.x, HEARTH.position.y, STRIP.size.x, HEARTH.size.y)

## The workshop's back wall of dark planks, and the beam the trades' tags hang from.
func draw_surface(r: Rect2) -> void:
	WorkshopKit.wall(self, r)
	WorkshopKit.beam(self, r.position.x + 20, r.end.x - 20, 102)

func draw_title_mount(r: Rect2) -> void:
	face(r, "timber_sign")

func draw_tab(r: Rect2, i: int, state: String) -> void:
	WorkshopKit.tag_tab(self, r, str(tabs[i].label), state)

## The craft button's word for each trade.
func _verb(craft: String) -> String:
	return {"cooking": Tx.t("ui.crafts.cook"), "alchemy": Tx.t("ui.crafts.to_furnace"), "smithing": Tx.t("ui.crafts.forge"), "formations": Tx.t("ui.crafts.etch"),
		"talisman": Tx.t("ui.crafts.write"), "star_charting": Tx.t("ui.crafts.chart"), "shipwright": Tx.t("ui.crafts.build")}.get(craft, "")

## The chosen recipe, when it is this trade's.
func _chosen(craft: String) -> Dictionary:
	var rec := ContentDB.entry("recipes", sel)
	return rec if not rec.is_empty() and str(rec.get("craft", "")) == craft else {}

## The steps across the top, [id, name, the one thing it asks]: the furnace's screens, or a recipe, its materials and
## the making.
func _steps(ch, craft: String) -> Array:
	var rec := _chosen(craft)
	if craft == "alchemy":
		var rs := _session()
		var recipe := str(rs.get("recipe", sel))
		var ids: Array = _screens(recipe) if ContentDB.has_entry("recipes", recipe) else ["ingredients", "furnace", "extraction", "fusion", "condensation"]
		if not trib.is_empty() and not ids.has("tribulation"): ids.append("tribulation")
		var out: Array = []
		for id in ids:
			var sub := Tx.t("ui.crafts.sub_" + str(id)) if not str(id) in ["ingredients", "furnace"] else ""
			if str(id) == "furnace": sub = Tx.t("ui.crafts.fire_" + str(rs.get("fire", fire)))
			elif str(id) == "ingredients":
				sub = Tx.t("ui.crafts.sub_choose")
				var roles: Array = rec.get("roles", [])
				var i := roles.find("principal")
				if i >= 0: sub = Tx.t("ui.crafts.sub_leads") % ContentDB.item_name(str(rec.inputs[i].item))
			out.append([str(id), _screen_label(str(id)), sub])
		return out
	var met := 0
	for inp in rec.get("inputs", []):
		if ch.inventory.count(str(inp.item)) >= int(inp.count) * count: met += 1
	return [["recipe", Tx.t("ui.crafts.step_recipe"), ContentDB.item_name(str(rec.outputs[0].item)) if not rec.is_empty() else Tx.t("ui.crafts.sub_choose")],
		["materials", Tx.t("ui.crafts.step_materials"), Tx.t("ui.crafts.sub_at_hand") % [met, (rec.inputs as Array).size()] if not rec.is_empty() else ""],
		["make", _verb(craft), Tx.t("ui.crafts.sub_make_" + craft)]]

func _step_now(ch, craft: String, steps: Array) -> int:
	if craft == "alchemy":
		var rs := _session()
		var cur := "tribulation" if not trib.is_empty() else (str(rs.get("stage", "")) if not rs.is_empty() else screen)
		for i in steps.size():
			if str(steps[i][0]) == cur: return i
		return 0
	var rec := _chosen(craft)
	if rec.is_empty(): return 0
	if game_on or trace_on: return 2
	for inp in rec.inputs:
		if ch.inventory.count(str(inp.item)) < int(inp.count) * count: return 1
	return 2

## The strip across the top: each step's seal (done, now, to come), its name and what it asks; the Forge keeps its six
## modes there.
func _strip(ch, craft: String) -> void:
	WorkshopKit.board(self, STRIP)
	if craft == "smithing":
		var mw := (STRIP.size.x - 16) / FORGE_MODES.size()
		for i in FORGE_MODES.size():
			var m: String = FORGE_MODES[i]
			btn(Rect2(STRIP.position.x + 8 + i * mw + 2, STRIP.position.y + 6, mw - 4, 48), Tx.t("ui.forge." + m), "forge_mode", m, forge_mode == m, true, "", 18)
		return
	var steps := _steps(ch, craft)
	var at := _step_now(ch, craft, steps)
	var w := STRIP.size.x / steps.size()
	for i in steps.size():
		var x := STRIP.position.x + i * w
		var dot := Vector2(x + 24, STRIP.position.y + 30)
		var col: Color = UiKit.JADE if i < at else (UiKit.GOLD if i == at else UiKit.SURFACE.wood_dark)
		if i == at: glow(Rect2(dot - Vector2(24, 24), Vector2(48, 48)), Color(UiKit.GOLD, 0.45 * _halo()))
		draw_circle(dot, 13.0, UiKit.INK, true, -1.0, true)
		draw_circle(dot, 11.0, col, true, -1.0, true)
		if i > at: draw_arc(dot, 10.0, 0, TAU, 24, Color(UiKit.HOLLOW, 0.7), 2.0, true)
		ground(Rect2(dot - Vector2(9, 9), Vector2(18, 18)), col)
		text(dot + Vector2(-12, 5), "✓" if i < at else str(i + 1), 14, UiKit.MIST if i > at else UiKit.INK, HORIZONTAL_ALIGNMENT_CENTER, 24)
		var name_col: Color = UiKit.BRIGHT_JADE if i < at else (UiKit.PALE_GOLD if i == at else UiKit.PAPER)
		text(Vector2(x + 44, STRIP.position.y + 26), str(steps[i][1]), 18, name_col, HORIZONTAL_ALIGNMENT_LEFT, w - 56)
		text(Vector2(x + 44, STRIP.position.y + 46), str(steps[i][2]), 14, UiKit.PAPER if i == at else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w - 56)
		if i > 0:
			var ax := x - 4.0
			var ay := STRIP.position.y + 30
			draw_colored_polygon(PackedVector2Array([Vector2(ax - 5, ay - 6), Vector2(ax + 3, ay), Vector2(ax - 5, ay + 6)]), UiKit.JADE if i <= at else Color(UiKit.HOLLOW, 0.6))

## The fire's colour: the furnace's chosen fire, else the hearth's embers.
func _fire_col(craft: String) -> Color:
	if craft != "alchemy": return UiKit.SURFACE.ember
	return {"heavenly_flame": UiKit.SKY, "beast_fire": UiKit.RED, "earth_fire": UiKit.SURFACE.flame}.get(str(_session().get("fire", fire)), UiKit.SURFACE.ember) as Color

## The hearth: a dark recess over a brick hearth with its fire mouth, the vessel standing on the slab over the fire, and
## on the brick the array (alchemy) or the trade's rank at the left and the fire at the right.
func _hearth(ch, craft: String, live: bool) -> void:
	var h := HEARTH
	var recess: Color = UiKit.SURFACE.wood_dark.lerp(UiKit.INK, 0.45)
	rounded(h.grow(2), 6.0, UiKit.INK)
	vshade(h, recess, UiKit.INK)
	ground(h, recess)
	var block := Rect2(h.position.x, h.end.y - BLOCK_H, h.size.x, BLOCK_H)
	var cx := h.get_center().x
	var heat := float(HEAT.get(craft, 0.12))
	if live and str(play.get("stage", "")) == "extraction": heat = float(play.get("heat", 0.3))
	var fcol := _fire_col(craft)
	glow(Rect2(cx - 240, block.position.y - 170, 480, 280), Color(fcol, (0.12 + 0.2 * heat) * _halo()))
	WorkshopKit.bricks(self, block)
	var mouth := Rect2(cx - 96, block.position.y + 22, 192, BLOCK_H - 22)
	draw_colored_polygon(PostKit.arch(mouth, 30.0), UiKit.SURFACE.furnace_mouth)
	WorkshopKit.fire(self, Vector2(cx, block.end.y - 4), 164.0, heat, fcol, t)
	draw_rect(Rect2(h.position.x, block.position.y - 4, h.size.x, 8), UiKit.SURFACE.stone.lerp(UiKit.PAPER, 0.18))
	draw_rect(Rect2(h.position.x, block.position.y + 4, h.size.x, 2), Color(UiKit.INK, 0.6))
	var arr := str(_session().get("array", array))
	if craft == "alchemy" and (live or screen == "furnace"): _array_ring(Vector2(cx, block.position.y), arr)
	# The vessel settles onto its fire as the page opens; a finished craft lifts out of it in a puff.
	if not (craft == "talisman" and trace_on): _vessel(ch, craft, Vector2(cx, block.position.y + 2 - 28.0 * (1.0 - unfold())))
	var pk := (t - puff_at) / 0.4
	if pk >= 0.0 and pk < 1.0 and not UiKit.reduce_motion():
		for i in 3: glow(Rect2(Vector2(cx - 60 + i * 40, block.position.y - 200 - 60 * pk) - Vector2(30, 30) * (1.0 + pk), Vector2(60, 60) * (1.0 + pk)), Color(UiKit.PAPER, 0.45 * (1.0 - pk)))
	var side_w := cx - 96 - h.position.x - 24
	var prof: Dictionary = ch.professions.get(craft, {"rank": "apprentice", "xp": 0})
	var left := Tx.t("ui.crafts.array_" + arr) if craft == "alchemy" and (live or screen == "furnace") else "%s · %s" % [str(prof.rank).capitalize(), UiKit.fmt(float(prof.xp))]
	text(Vector2(h.position.x + 16, block.end.y - 18), left, 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, side_w)
	if craft == "alchemy": text(Vector2(cx + 104, block.end.y - 18), Tx.t("ui.crafts.fire_" + str(_session().get("fire", fire))), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, side_w)

## The array set under the furnace: three rings seen from the side, water's in Qi blue, flame's in ember.
func _array_ring(c0: Vector2, arr: String) -> void:
	var col: Color = UiKit.QI if arr == "water" else UiKit.SURFACE.ember
	move(c0, 0.0, Vector2(1.0, 0.16))
	for ring in [[230.0, 0.75], [180.0, 0.45], [128.0, 0.6]]: draw_arc(Vector2.ZERO, float(ring[0]), 0, TAU, 64, Color(col, float(ring[1])), 4.0, true)
	for a in 8: draw_circle(Vector2.from_angle(a * TAU / 8.0) * 230.0, 18.0, Color(col, 0.85))
	move()

## A prop from the world standing with its foot at `base`, at a whole scale.
func _prop(id: String, state: String, base: Vector2, k: float) -> void:
	move(base, 0.0, Vector2(k, k))
	SpriteCache.draw_prop(self, id, state, 0.0 if UiKit.reduce_motion() else t, Vector2.ZERO)
	move()

## Each trade's vessel over the fire: the pot, your furnace, the anvil, the plate, the paper, the chart table, the hull.
func _vessel(ch, craft: String, base: Vector2) -> void:
	var box := Rect2(base - Vector2(96, 192), Vector2(192, 192))
	match craft:
		"cooking": _prop("cooking_pot", "steam", base, 3.0)
		"smithing": _prop("forge_anvil", "sparks" if game_on else "idle", base, 2.0)
		"star_charting": _prop("star_chart_table", "idle", base, 2.0)
		"alchemy":
			var fu: Dictionary = Game.crafting.furnace_of(ch)
			if str(fu.get("id", "")) == "" or SpriteCache.draw_icon(self, box, str(fu.id)) == Rect2(): _prop("alchemy_furnace", "lit", base, 3.0)
		"talisman":
			var paper := Rect2(base - Vector2(64, 176), Vector2(128, 172))
			rounded(paper.grow(3), 3.0, UiKit.SURFACE.talisman_edge)
			rounded(paper, 2.0, UiKit.SURFACE.talisman)
			var rec := _chosen(craft)
			var tpl := _template(paper.grow(-16)) if not rec.is_empty() and rec.get("traced", false) else PackedVector2Array()
			if tpl.size() > 1: draw_polyline(tpl, UiKit.SURFACE.cinnabar_ink, 5.0, true)
		_:
			var rec2 := _chosen(craft)
			icon_at(box, str(rec2.outputs[0].item) if not rec2.is_empty() else "blank_plate")

## The recipe's ingredients along the rim above the vessel: each in its slot with its name and what you hold of it; in
## the furnace also its role, its nature, what stands in and what Spirit Sense tells (a tap on a slot that can take a
## stand-in swaps it).
func _rim(ch, craft: String) -> void:
	var rec := _chosen(craft)
	if rec.is_empty(): return
	var alch := craft == "alchemy"
	var inputs: Array = Game.crafting.inputs_with(sel, subst) if alch else rec.inputs
	var roles: Array = rec.get("roles", [])
	var can_swap: bool = alch and int(ch.cultivator.daos.get("alchemy", {}).get("tier", 0)) >= int(Game.crafting.upkeep("substitute_tier", 5))
	var n := maxi(1, inputs.size())
	var cw := minf(132.0, (HEARTH.size.x - 32) / n)
	var x0 := HEARTH.get_center().x - cw * n * 0.5
	for i in inputs.size():
		var inp: Dictionary = inputs[i]
		var cx := x0 + cw * (i + 0.5)
		var sr := Rect2(cx - SLOT * 0.5, HEARTH.position.y + 12, SLOT, SLOT)
		var have: int = ch.inventory.count(str(inp.item))
		var need := int(inp.count) * count
		slot_box(sr, str(inp.item))
		text(Vector2(cx - cw * 0.5 + 2, sr.end.y + 20), ContentDB.item_name(str(inp.item)), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, cw - 4)
		text(Vector2(cx - cw * 0.5 + 2, sr.end.y + 40), "%d / %d" % [have, need], 16, UiKit.BRIGHT_JADE if have >= need else UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_CENTER, cw - 4)
		if not alch: continue
		var bits: Array = []
		if i < roles.size(): bits.append(Tx.t("ui.crafts.role_" + str(roles[i])))
		var nat := str(ContentDB.item(str(inp.item)).get("nature", ""))
		if nat in ["hot", "cold"]: bits.append(Tx.t("ui.crafts.nature_" + nat))
		var orig := str(rec.inputs[i].item)
		if orig != str(inp.item): bits.append(Tx.t("ui.crafts.stands_in") % ContentDB.item_name(orig))
		bits.append_array(_sense_bits(ch, str(inp.item)))
		var swappable: bool = can_swap and str(ContentDB.item(orig).get("type", "")) == "herb" and not Game.crafting.substitutes_for(ch, sel, orig).is_empty() \
				and (subst.is_empty() or str(subst.get("from", "")) == orig)
		if swappable:
			bits.append(Tx.t("ui.crafts.swap"))
			region(sr, "swap", orig)
		text(Vector2(cx - cw * 0.5 + 2, sr.end.y + 58), " · ".join(bits), 14, UiKit.PALE_GOLD if orig != str(inp.item) or swappable else UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, cw - 4)

## The card's head: what the recipe makes, in its slot, and its name in its grade's colour.
func _card_head(rec: Dictionary, n := 0) -> void:
	var out := str(rec.outputs[0].item)
	slot_box(Rect2(SIDE.position + Vector2(16, 14), Vector2(SLOT, SLOT)), out, n)
	text(SIDE.position + Vector2(108, 40), ContentDB.item_name(out), 22, UiKit.grade_color(str(rec.get("grade", "plain"))), HORIZONTAL_ALIGNMENT_LEFT, SIDE.size.x - 124)

## The bronze rule under the card.
func _divider() -> void:
	draw_line(Vector2(SIDE.position.x + 16, SIDE.position.y + 104), Vector2(SIDE.end.x - 16, SIDE.position.y + 104), Color(UiKit.BRONZE, 0.6), 2.0)

## The card at the top of the controls: what the chosen recipe makes, or where to begin. Returns where the step's
## controls start.
func _card(ch, craft: String) -> float:
	var s := SIDE
	var rec := _chosen(craft)
	if rec.is_empty():
		para(Rect2(s.position + Vector2(20, 16), Vector2(s.size.x - 40, 84)), (Tx.t("ui.crafts.choose_a_recipe_stand_near") % {"cooking": Tx.t("ui.crafts.cooking_pot"), "alchemy": Tx.t("ui.crafts.furnace_word"),
			"smithing": Tx.t("ui.crafts.forge_word"), "star_charting": Tx.t("ui.crafts.chart_table"), "shipwright": Tx.t("ui.crafts.slipway")}[craft]) if not craft in ["formations", "talisman"] \
			else Tx.t("ui.crafts.choose_a_plate_to_etch") if craft == "formations" else Tx.t("ui.crafts.choose_a_talisman"), 18, UiKit.MIST, 3)
	else:
		var out := str(rec.outputs[0].item)
		_card_head(rec, int(rec.outputs[0].count))
		var clash: Dictionary = Game.crafting.conflict_in(Game.crafting.inputs_with(sel, subst)) if craft == "alchemy" else {}
		if not clash.is_empty() and (ch.crafting.get("known_conflicts", []) as Array).has(str(clash.id)):
			para(Rect2(s.position + Vector2(108, 50), Vector2(s.size.x - 124, 44)), Tx.t("ui.crafts.conflict_warning"), 16, UiKit.RED_TEXT, 2)
		else:
			para(Rect2(s.position + Vector2(108, 50), Vector2(s.size.x - 124, 44)), str(ContentDB.item(out).get("desc", "")), 16, UiKit.MIST, 2)
	_divider()
	return s.position.y + 112

## The recipe views: the rim over the vessel, the card, and at the right the recipe book (or the furnace's fire and
## array, the strike band, the tracing), the batch and the craft button at its foot.
func _recipe_view(ch, craft: String) -> void:
	var s := SIDE
	var alch := craft == "alchemy"
	var recipes := recipes_for(ch, craft)
	# S44: the alchemy list also holds the experiment bench and the ancient recipes you have pages of.
	var extra: Array = []
	if alch:
		if Unlocks.is_unlocked(ch.id, "experiments"): extra.append(EXPERIMENT)
		extra.append_array(Game.crafting.ancient_in_progress(ch))
	var special := alch and (sel == EXPERIMENT or extra.has(sel))
	var rec: Dictionary = {} if special else _chosen(craft)
	if craft == "talisman" and trace_on: _draw_trace()
	elif not rec.is_empty(): _rim(ch, craft)
	elif alch and not special: _auto(ch, Rect2(HEARTH.position, Vector2(HEARTH.size.x, 200)))
	var y := s.position.y + 112 if special else _card(ch, craft)
	if alch and screen == "furnace" and not rec.is_empty():
		_furnace_screen(ch, Rect2(s.position.x, y, s.size.x, s.end.y - y))
		return
	if trace_on:
		para(Rect2(s.position.x + 20, y + 12, s.size.x - 40, 90), Tx.t("ui.crafts.trace_hint"), 18, UiKit.MIST, 4)
		btn(Rect2(s.end.x - 216, s.end.y - 72, 200, 56), Tx.t("ui.crafts.stop_tracing"), "trace_cancel", null, false, true, "", 18)
		return
	var foot := s.end.y - 80
	if game_on:
		text(Vector2(s.position.x + 24, y + 28), Tx.t("ui.crafts.sub_make_smithing"), 18, UiKit.PALE_GOLD)
		_draw_minigame(Rect2(s.position.x + 24, y + 48, s.size.x - 48, 60))
	else:
		list("rec", Rect2(s.position.x + 12, y, s.size.x - 20, foot - y - 8), extra.size() + recipes.size(), 56, func(i: int, rr: Rect2):
			if i < extra.size():
				var xid: String = extra[i]
				panel(rr, "minor_panel", "selected" if sel == xid else "normal")
				if xid == EXPERIMENT:
					slot_box(Rect2(rr.position + Vector2(4, 4), Vector2(SLOT_SMALL, SLOT_SMALL)), "murky_pill")
					text(rr.position + Vector2(60, 33), Tx.t("ui.crafts.experiment"), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 70)
				else:
					var xr := ContentDB.entry("recipes", xid)
					slot_box(Rect2(rr.position + Vector2(4, 4), Vector2(SLOT_SMALL, SLOT_SMALL)), "manual_page")
					text(rr.position + Vector2(60, 23), ContentDB.item_name(str(xr.outputs[0].item)), 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 70)
					text(rr.position + Vector2(60, 43), Tx.t("ui.crafts.pages_held") % [Game.crafting.pages_held(ch, xid), int(xr.get("fragments", 1))], 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 70)
				region(rr, "sel", xid)
				return
			var r: Dictionary = recipes[i - extra.size()]
			var out := str(r.outputs[0].item)
			var why := Game.crafting.recipe_check(ch, str(r.id), 1, craft)
			panel(rr, "minor_panel", "selected" if sel == str(r.id) else "normal")
			slot_box(Rect2(rr.position + Vector2(4, 4), Vector2(SLOT_SMALL, SLOT_SMALL)), out)
			text(rr.position + Vector2(60, 33), ContentDB.item_name(out), 18, UiKit.PAPER if why == "" else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, rr.size.x - 70)
			region(rr, "sel", str(r.id))
		)
	if special:
		if sel == EXPERIMENT: _experiment(ch, foot)
		else: _deduce(ch, foot)
		return
	if rec.is_empty(): return
	if craft in ["cooking", "alchemy", "formations"] and not game_on:
		btn(Rect2(s.position.x + 16, foot + 12, 48, 56), "−", "count", -1)
		text(Vector2(s.position.x + 64, foot + 48), "×%d" % count, 22, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 56)
		btn(Rect2(s.position.x + 120, foot + 12, 48, 56), "+", "count", 1)
	var why2 := Game.crafting.recipe_check(ch, sel, count, craft, Game.crafting.inputs_with(sel, subst) if alch else [])
	var queue := alch and Unlocks.is_unlocked(ch.id, "auto_refine") and not game_on
	var mw := 172.0 if queue else 220.0
	btn(Rect2(s.end.x - 16 - mw, foot + 8, mw, BTN_H_MAIN), Tx.t("ui.crafts.strike") if game_on else _verb(craft), "strike" if game_on else "craft", null, true, why2 == "" or game_on, why2)
	if queue: btn(Rect2(s.end.x - 16 - mw - 136, foot + 12, 128, 56), Tx.t("ui.crafts.queue_batch"), "queue", null, false, why2 == "", why2)

# ------------------------------------------------------------------ the Forge's upkeep (S47)
## Every piece of equipment you have: worn first, then the bag.
func _gear(ch) -> Array:
	var out: Array = []
	for sl in ch.inventory.equipped:
		var e = ch.inventory.equipped[sl]
		if e != null and ContentDB.is_equipment(str(e.id)): out.append({"inst": e, "worn": true})
	if ch.inventory.furnace != null: out.append({"inst": ch.inventory.furnace, "worn": true})   # the furnace slot (S44)
	for it in ch.inventory.bag:
		if it != null and it.has("uid") and ContentDB.is_equipment(str(it.id)): out.append({"inst": it, "worn": false})
	return out

func _find(ch, uid: int) -> Dictionary:
	for g in _gear(ch):
		if int(g.inst.get("uid", -2)) == uid: return g.inst
	return {}

func _gear_name(inst: Dictionary) -> String:
	var lv := int(inst.get("enhance", 0))
	return ContentDB.item_name(str(inst.id)) + (" +%d" % lv if lv > 0 else "")

func _forge(ch, area: Rect2) -> void:
	var gear := _gear(ch)
	var list_r := Rect2(area.position.x, area.position.y, 420, area.size.y)
	panel(list_r)
	list("gear", list_r.grow(-8), gear.size(), 64, func(i: int, rr: Rect2):
		var g: Dictionary = gear[i]
		var inst: Dictionary = g.inst
		var uid := int(inst.get("uid", -1))
		var chosen: bool = uid == pick_uid or uid == to_uid or picked.has(uid)
		var usable: bool = not (forge_mode == "salvage" and (g.worn or inst.get("bound", false) or ch.inventory.locked.has(uid)))
		panel(rr, "minor_panel", "selected" if chosen else ("normal" if usable else "disabled"))
		slot_box(Rect2(rr.position + Vector2(6, 7), Vector2(SLOT_SMALL, SLOT_SMALL)),str(inst.id), 0, str(inst.get("quality", "")))
		var grade := str(ContentDB.item(str(inst.id)).get("grade", "plain"))
		text(rr.position + Vector2(66, 28), fit(_gear_name(inst), 18, rr.size.x - 150), 18, UiKit.grade_color(grade) if usable else UiKit.HOLLOW)
		var sub := (Tx.t("ui.forge.in_furnace_slot") if ContentDB.item(str(inst.id)).has("furnace") else Tx.t("ui.forge.worn")) if g.worn else ""
		if float(inst.get("pity", 0.0)) > 0.0: sub += ("  " if sub != "" else "") + Tx.t("ui.forge.pity") % int(round(float(inst.pity) * 100))
		if ch.inventory.locked.has(uid): sub += ("  " if sub != "" else "") + Tx.t("ui.forge.locked_item")
		if inst.get("awakened", false): sub += ("  " if sub != "" else "") + Tx.t("ui.forge.awakened_tag")
		text(rr.position + Vector2(66, 50), sub, 14, UiKit.MIST)
		if forge_mode == "salvage" and picked.has(uid): text(rr.position + Vector2(rr.size.x - 34, 38), "✓", 22, UiKit.BRIGHT_JADE)
		region(rr, "gear", uid, usable, Tx.t("ui.forge.cannot_salvage"))
	)
	var right := Rect2(list_r.end.x + 20, area.position.y, area.end.x - list_r.end.x - 20, area.size.y)
	panel(right)
	match forge_mode:
		"enhance": _forge_enhance(ch, right)
		"inherit": _forge_inherit(ch, right)
		"salvage": _forge_salvage(ch, right)
		"reroll": _forge_reroll(ch, right)
		"natal": _forge_natal(ch, right)

func _piece_header(r: Rect2, inst: Dictionary) -> float:
	slot_box(Rect2(r.position + Vector2(24, 24), Vector2(SLOT, SLOT)),str(inst.id), 0, str(inst.get("quality", "")))
	text(r.position + Vector2(110, 56), _gear_name(inst), 22, UiKit.grade_color(str(ContentDB.item(str(inst.id)).get("grade", "plain"))))
	text(r.position + Vector2(110, 84), str(inst.get("quality", "common")).capitalize(), 16, UiKit.MIST)
	return r.position.y + 120

func _cost_line(r: Rect2, y: float, item_id: String, need: int) -> float:
	var have: int = c().inventory.count(item_id)
	slot_box(Rect2(r.position.x + 24, y, SLOT_SMALL, SLOT_SMALL),item_id)
	text(Vector2(r.position.x + 80, y + 30), "%s  %d / %d" % [ContentDB.item_name(item_id), have, need], 18, UiKit.BRIGHT_JADE if have >= need else UiKit.RED_TEXT)
	return y + 50

func _forge_enhance(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty():
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.enhance_help"), 20, UiKit.MIST)
		return
	var y := _piece_header(r, inst)
	if int(inst.get("enhance", 0)) >= 10:
		text(Vector2(r.position.x + 24, y + 20), Tx.t("ui.forge.max"), 20, UiKit.GOLD)
		_awaken_section(ch, r, inst, y + 36)
		return
	var risky := int(inst.get("enhance", 0)) >= int(Game.crafting.upkeep("risky_from", 5))
	if not risky: essence = 0
	var chance: float = Game.crafting.enhance_chance(inst, essence)
	text(Vector2(r.position.x + 24, y + 22), Tx.t("ui.forge.chance") % [int(inst.get("enhance", 0)) + 1, int(round(chance * 100))], 20, UiKit.PAPER)
	y += 30
	if float(inst.get("pity", 0.0)) > 0.0:
		text(Vector2(r.position.x + 24, y + 20), Tx.t("ui.forge.pity_line") % int(round(float(inst.pity) * 100)), 16, UiKit.PALE_GOLD)
		y += 26
	var cost: Dictionary = Game.crafting.enhance_cost(inst)
	y = _cost_line(r, y + 8, str(cost.metal), int(cost.count))
	if int(cost.shards) > 0: y = _cost_line(r, y, "spirit_stone_shard", int(cost.shards))
	text(Vector2(r.position.x + 24, y + 24), Tx.plural("ui.forge.taels", int(cost.taels)) % int(cost.taels), 18, UiKit.BRIGHT_JADE if Game.economy.balance("silver_tael") >= int(cost.taels) else UiKit.RED_TEXT)
	y += 36
	if risky:
		text(Vector2(r.position.x + 24, y + 24), Tx.t("ui.forge.essence") % [essence, int(round(essence * float(Game.crafting.upkeep("essence_step", 0.025)) * 100))], 18, UiKit.PAPER)
		btn(Rect2(r.end.x - 164, y, 56, 44), "−", "essence", -1)
		btn(Rect2(r.end.x - 84, y, 56, 44), "+", "essence", 1, false, essence < int(Game.crafting.upkeep("essence_max", 4)) and ch.inventory.count("refining_essence") > essence)
	var why: String = Game.crafting.enhance_check(ch, inst, essence)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.enhance"), "do_enhance", null, true, why == "", why)
	# A furnace (S44): each level steadies its heat 1%; a blast costs it durability, mended here.
	if str(ContentDB.item(str(inst.id)).get("slot", "")) == "tool_furnace":
		var dur := int(inst.get("durability", 100))
		text(Vector2(r.position.x + 24, r.end.y - 96), Tx.t("ui.forge.furnace_line") % [dur, int(inst.get("enhance", 0))], 16, UiKit.MIST if dur > 0 else UiKit.RED_TEXT)
		if dur < 100:
			var mc: Dictionary = Game.crafting.mend_cost(inst)
			var mwhy := "" if ch.inventory.count(str(mc.metal)) >= int(mc.count) else Tx.t("sim.crafting.needs_2") % [int(mc.count), ContentDB.item_name(str(mc.metal))]
			btn(Rect2(r.end.x - 474, r.end.y - 76, 220, 58), Tx.t("ui.forge.mend") % [int(mc.count), ContentDB.item_name(str(mc.metal))], "do_mend", null, false, mwhy == "", mwhy, 18)

## S47 weapon awakening: a +10 weapon of Heaven grade or better wakes here with a Weapon Soul Crystal, once the Dao of
## its family has reached Explanation. The skill it would gain, what it still needs, and the button.
func _awaken_section(ch, r: Rect2, inst: Dictionary, y: float) -> void:
	if not CraftingAuthority.awaken_grade_ok(str(inst.id)): return
	var sk := CraftingAuthority.awakened_skill(str(inst.id))
	if sk.is_empty(): return
	var x := r.position.x + 24
	var w := r.size.x - 48
	if inst.get("awakened", false):
		y += para(Rect2(x, y + 6, w, 60), Tx.plural("ui.forge.awakened_line", int(sk.get("every_hits", 12))) % [str(sk.get("name", "")), int(sk.get("every_hits", 12))], 18, UiKit.GOLD, 2)
		return
	heading(Vector2(x, y + 34), Tx.t("ui.forge.awaken_title"), w)
	y += 44
	y += para(Rect2(x, y + 4, w, 60), Tx.plural("ui.forge.awaken_skill", int(sk.get("every_hits", 12))) % [str(sk.get("name", "")), int(sk.get("every_hits", 12))], 18, UiKit.PALE_GOLD, 2)
	var fam := ContentDB.entry("weapon_families", str(ContentDB.item(str(inst.id)).get("family", "")))
	var dao := str(fam.get("dao", ""))
	var tier := int(ch.cultivator.daos.get(dao, {}).get("tier", 0))
	var have: int = ch.inventory.count("weapon_soul_crystal")
	for row in [[tier >= 4, Tx.t("ui.forge.awaken_need_dao") % [ContentDB.name_of("daos", dao), tier]],
			[have > 0, Tx.t("ui.forge.awaken_need_crystal") % have],
			[Game.crafting.station_near(ch, ["forge_anvil"]), Tx.t("ui.forge.awaken_need_forge")]]:
		text(Vector2(x, y + 22), ("✓ " if row[0] else "· ") + str(row[1]), 18, UiKit.BRIGHT_JADE if row[0] else UiKit.MIST)
		y += 26
	var why: String = Game.crafting.awaken_check(ch, inst)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.awaken"), "do_awaken", null, true, why == "", why)

func _forge_inherit(ch, r: Rect2) -> void:
	var from := _find(ch, pick_uid)
	var to := _find(ch, to_uid)
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 60)), Tx.t("ui.forge.inherit_help"), 18, UiKit.MIST)
	var y := r.position.y + 90
	for pair in [[Tx.t("ui.forge.from"), from], [Tx.t("ui.forge.to"), to]]:
		text(Vector2(r.position.x + 24, y + 30), str(pair[0]), 18, UiKit.MIST)
		var inst: Dictionary = pair[1]
		if inst.is_empty(): text(Vector2(r.position.x + 120, y + 30), Tx.t("ui.forge.choose_left"), 18, UiKit.HOLLOW)
		else:
			slot_box(Rect2(r.position.x + 110, y + 3, SLOT_SMALL, SLOT_SMALL), str(inst.id), 0, str(inst.get("quality", "")))
			text(Vector2(r.position.x + 166, y + 32), _gear_name(inst), 18, UiKit.PAPER)
		y += 64
	var why := ""
	var moved := 0
	if from.is_empty() or to.is_empty(): why = Tx.t("ui.forge.choose_both")
	else:
		moved = int(from.get("enhance", 0)) - int(Game.crafting.upkeep("inherit_loss", 2))
		if str(ContentDB.item(str(from.id)).get("slot", "")) != str(ContentDB.item(str(to.id)).get("slot", "")): why = Tx.t("sim.crafting.inherit_same_slot")
		elif moved <= int(to.get("enhance", 0)): why = Tx.t("sim.crafting.inherit_nothing")
	if why == "":
		var stones := moved * int(Game.crafting.upkeep("inherit_stones_per_level", 2))
		text(Vector2(r.position.x + 24, y + 26), Tx.plural("ui.forge.inherit_preview", stones) % [moved, stones], 20, UiKit.PAPER)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.inherit"), "do_inherit", null, true, why == "", why)
	btn(Rect2(r.position.x + 24, r.end.y - 76, 160, 58), Tx.t("ui.forge.clear"), "clear_pick")

func _forge_salvage(ch, r: Rect2) -> void:
	var pv: Dictionary = Game.crafting.salvage_preview(ch, picked.keys())
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 60)), Tx.t("ui.forge.salvage_help"), 18, UiKit.MIST)
	var y := r.position.y + 96
	text(Vector2(r.position.x + 24, y), Tx.plural("ui.forge.salvage_count", pv.items.size()) % pv.items.size(), 20, UiKit.PAPER)
	y += 16
	for item_id in pv.returns:
		slot_box(Rect2(r.position.x + 24, y, SLOT_SMALL, SLOT_SMALL),str(item_id), int(pv.returns[item_id]))
		text(Vector2(r.position.x + 80, y + 30), "%s ×%d" % [ContentDB.item_name(str(item_id)), int(pv.returns[item_id])], 18, UiKit.BRIGHT_JADE)
		y += 50
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.salvage"), "do_salvage", null, true, not pv.items.is_empty(), Tx.t("ui.forge.choose_pieces"))

func _forge_reroll(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty():
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.reroll_help"), 20, UiKit.MIST)
		return
	var y := _piece_header(r, inst)
	var affs: Array = inst.get("affixes", [])
	if affs.is_empty():
		text(Vector2(r.position.x + 24, y + 20), Tx.t("sim.crafting.no_affixes"), 18, UiKit.MIST)
		return
	var lock := int(inst.get("locked_affix", -1))
	var pending: Array = inst.get("pending_affixes", [])
	var colw := (r.size.x - 48) / (2.0 if not pending.is_empty() else 1.0)
	if not pending.is_empty():
		text(Vector2(r.position.x + 24, y + 8), Tx.t("ui.forge.old_roll"), 16, UiKit.MIST)
		text(Vector2(r.position.x + 24 + colw, y + 8), Tx.t("ui.forge.new_roll"), 16, UiKit.MIST)
		y += 14
	for i in affs.size():
		var locked := i == lock
		text(Vector2(r.position.x + 24, y + 30), ("🔒 " if locked else "✦ ") + UiKit.affix_text(affs[i]), 18, UiKit.GOLD if locked else UiKit.PALE_GOLD)
		if pending.is_empty():
			btn(Rect2(r.end.x - 164, y + 2, 140, 42), Tx.t("ui.forge.unlock") if locked else Tx.t("ui.forge.lock"), "lock_affix", -1 if locked else i, locked, true, "", 16)
		elif i < pending.size():
			text(Vector2(r.position.x + 24 + colw, y + 30), "✦ " + UiKit.affix_text(pending[i]), 18, UiKit.BRIGHT_JADE)
		y += 48
	if not pending.is_empty():
		btn(Rect2(r.position.x + 24, r.end.y - 76, 200, 58), Tx.t("ui.forge.keep_old"), "choose", "old")
		btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.take_new"), "choose", "new", true)
		return
	var cost: Dictionary = Game.crafting.reroll_cost(inst, ch)
	if cost.get("free", false):
		text(Vector2(r.position.x + 24, y + 34), Tx.t("ui.forge.free_reroll"), 18, UiKit.BRIGHT_JADE)   # S10 Insight 25
	else:
		y = _cost_line(r, y + 10, "refining_essence", int(cost.essence))
		text(Vector2(r.position.x + 24, y + 24), Tx.plural("ui.forge.taels", int(cost.taels)) % int(cost.taels) + (("  " + Tx.t("ui.forge.lock_doubles")) if lock >= 0 else ""), 18,
			UiKit.BRIGHT_JADE if Game.economy.balance("silver_tael") >= int(cost.taels) else UiKit.RED_TEXT)
	var why2: String = Game.crafting.reroll_check(ch, inst)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.reroll"), "do_reroll", null, true, why2 == "", why2)

## S47 natal treasure: flag one weapon, feed it ore, and re-forge it when it breaks or reaches its band's cap.
func _forge_natal(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty() or str(ContentDB.item(str(inst.id)).get("slot", "")) != "weapon":
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.natal_help"), 20, UiKit.MIST)
		return
	var y := _piece_header(r, inst)
	if not inst.get("natal", false):
		para(Rect2(r.position.x + 24, y, r.size.x - 48, 120), Tx.t("ui.forge.natal_help"), 18, UiKit.MIST)
		btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.make_natal"), "natal_flag", null, true, Unlocks.is_unlocked(ch.id, "natal"), Unlocks.locked_text("natal"))
		return
	var lv := int(inst.get("natal_level", 0))
	var xp := float(inst.get("natal_xp", 0.0))
	var steps: Array = ContentDB.stat_const("natal.xp_levels", [50])
	var nxt := float(steps[mini(lv, steps.size() - 1)])
	bar(Rect2(r.position.x + 24, y, r.size.x - 48, 24), 1.0 if lv >= 10 else xp / maxf(1.0, nxt), UiKit.GOLD,
		Tx.t("ui.forge.natal_level") % [lv, int(xp), int(nxt)] if lv < 10 else Tx.t("ui.forge.natal_full"))
	y += 40
	text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_ilv") % [int(inst.get("ilv_eff", inst.get("ilv", 1))), Game.inventory.natal_cap(inst)], 18, UiKit.PAPER)
	y += 26
	var demand: float = Game.combat.natal_demand(inst)
	var spirit: float = StatRules.attribute(ch, "spirit")
	text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_demand") % [int(demand), int(spirit)], 18, UiKit.BRIGHT_JADE if spirit >= demand else UiKit.RED_TEXT)
	y += 26
	if inst.get("broken", false):
		text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_broken"), 18, UiKit.RED_TEXT)
		y += 26
	# Feed: the best ore in the bag, one or five at a time.
	var ore := ""
	for it in ch.inventory.bag:
		if it == null or str(ContentDB.item(str(it.id)).get("type", "")) != "ore" or str(it.id) == "spirit_stone_shard": continue
		if ore == "" or StatRules.grade_index(str(ContentDB.item(str(it.id)).grade)) > StatRules.grade_index(str(ContentDB.item(ore).grade)): ore = str(it.id)
	if ore != "":
		slot_box(Rect2(r.position.x + 24, y + 6, SLOT_SMALL, SLOT_SMALL), ore, ch.inventory.count(ore))
		btn(Rect2(r.position.x + 80, y + 6, 130, 44), Tx.t("ui.forge.feed") % 1, "natal_feed", [ore, 1], false, not inst.get("broken", false), "", 16)
		btn(Rect2(r.position.x + 220, y + 6, 130, 44), Tx.t("ui.forge.feed") % 5, "natal_feed", [ore, 5], false, not inst.get("broken", false) and ch.inventory.count(ore) >= 5, "", 16)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.reforge"), "natal_reforge", null, true)

# ------------------------------------------------------------------ talisman tracing (S47)
func _template(r: Rect2) -> PackedVector2Array:
	var out := PackedVector2Array()
	var tal := ContentDB.entry("talismans", str(ContentDB.entry("recipes", sel).outputs[0].item))
	for p in tal.get("strokes", []): out.append(r.position + Vector2(float(p[0]), float(p[1])) * r.size)
	return out

## The talisman's paper laid over the hearth in the vessel's place, its stroke to trace.
func _draw_trace() -> void:
	var side := HEARTH.size.y - BLOCK_H - 40
	trace_rect = Rect2(HEARTH.get_center().x - side / 2.0, HEARTH.position.y + 20, side, side)
	draw_rect(trace_rect, UiKit.SURFACE.talisman)
	draw_rect(trace_rect, UiKit.SURFACE.talisman_edge, false, 3.0)
	var tpl := _template(trace_rect)
	if tpl.size() > 1:
		draw_polyline(tpl, Color(UiKit.SURFACE.cinnabar_ink, 0.35), 14.0)
		draw_circle(tpl[0], 9, Color(UiKit.SURFACE.cinnabar_ink, 0.7))
	if trace_pts.size() > 1: draw_polyline(PackedVector2Array(trace_pts), UiKit.SURFACE.brush_ink, 7.0)

## How the stroke went: its mean and worst distance from the path (as a share of the paper), whether it began at
## the red dot and ran to the end, and its pace. A stroke that strays too far or stops short is broken.
func _finish_trace() -> void:
	var tpl := _template(trace_rect)
	var cfg: Dictionary = ContentDB.config("talismans").get("trace", {})
	var side := maxf(1.0, trace_rect.size.x)
	var total := 0.0
	var worst := 0.0
	var far_t := 0.0
	var lens: Array = [0.0]
	for i in range(1, tpl.size()): lens.append(float(lens[-1]) + tpl[i - 1].distance_to(tpl[i]))
	var start_t := -1.0
	for p in trace_pts:
		var best := INF
		var best_t := 0.0
		for i in range(1, tpl.size()):
			var q: Vector2 = Geometry2D.get_closest_point_to_segment(p, tpl[i - 1], tpl[i])
			var dd: float = (p as Vector2).distance_to(q)
			if dd < best:
				best = dd
				best_t = float(lens[i - 1]) + tpl[i - 1].distance_to(q)
		total += best
		worst = maxf(worst, best)
		far_t = maxf(far_t, best_t)
		if start_t < 0.0: start_t = best_t
	var mean := total / maxf(1.0, trace_pts.size()) / side
	var length := maxf(1.0, float(lens[-1]))
	var broken := worst / side > float(cfg.get("break_at", 0.24)) or start_t > length * 0.12 or far_t < length * 0.9 or trace_pts.size() < 8
	var secs := Time.get_ticks_msec() / 1000.0 - trace_t0
	var pace := 1.0 if secs >= float(cfg.get("min_s", 0.6)) and secs <= float(cfg.get("max_s", 5.0)) else 0.85
	var score := clampf(1.0 - 0.5 * mean / float(cfg.get("tolerance", 0.09)), 0.0, 1.0) * pace
	var r := submit({"type": "trace_talisman", "recipe": sel, "score": score, "broken": broken})
	trace_on = false
	trace_pts = []
	if r.get("ok", false):
		Audio.play("technique", "UI")
		puff_at = t
		flash(Tx.t("ui.crafts.quality_made") % [str(r.quality).replace("_", " ").capitalize(), int(r.count)])
	elif str(r.get("text", "")) != "": flash(str(r.text))

func _gui_input(event: InputEvent) -> void:
	# The furnace's timed controls act the moment they are pressed; the fan works while it is held.
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and confirm.is_empty() and not tabs.is_empty() \
			and str(tabs[tab].id) == "alchemy":
		if not event.pressed: fanning = false
		else:
			for id in hot_rects:
				if (hot_rects[id] as Rect2).has_point(event.position):
					if id == "fan": fanning = true
					else: _hot(str(id))
					accept_event()
					return
	if trace_on and str(tabs[tab].id) == "talisman":
		if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed and trace_rect.has_point(event.position):
				trace_pts = [event.position]
				trace_t0 = Time.get_ticks_msec() / 1000.0
				accept_event()
				return
			if not event.pressed and not trace_pts.is_empty():
				_finish_trace()
				accept_event()
				return
		elif event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_LEFT and not trace_pts.is_empty():
			trace_pts.append(event.position)
			queue_redraw()
			accept_event()
			return
	super._gui_input(event)

func _auto(ch, right: Rect2) -> void:
	var q: Array = ch.crafting.get("auto_queue", [])
	if q.is_empty(): return
	var y := right.position.y + 30
	text(Vector2(right.position.x + 24, y), Tx.t("ui.crafts.auto_refine_batches"), 20, UiKit.GOLD)
	for b in q:
		y += 30
		var left := int(float(b.done_utc) - Clock.now_utc())
		text(Vector2(right.position.x + 24, y), "%s ×%d · %s" % [ContentDB.item_name(str(ContentDB.entry("recipes", str(b.recipe)).outputs[0].item)), int(b.count), Tx.t("ui.crafts.batch_ready") if left <= 0 else UiKit.span(left)], 18)
	btn(Rect2(right.position.x + 24, y + 20, 200, 50), Tx.t("ui.crafts.collect"), "collect", null, true)

# ------------------------------------------------------------------ S44 experiments, Deduce and the guild
## The experiment bench (S44): the herbs you carry laid along the rim to choose from; what it is and whether the mix was
## tried at the right, Experiment at the foot.
func _experiment(ch, foot: float) -> void:
	var s := SIDE
	para(Rect2(s.position + Vector2(20, 12), Vector2(s.size.x - 40, 88)), Tx.t("ui.crafts.experiment_help"), 14, UiKit.MIST, 4)
	_divider()
	var herbs: Array = []
	for it in ContentDB.all("items"):
		if str(it.get("type", "")) == "herb" and ch.inventory.count(str(it.id)) > 0: herbs.append(str(it.id))
	var area := Rect2(HEARTH.position.x + 12, HEARTH.position.y + 12, HEARTH.size.x - 20, 168)
	if herbs.is_empty(): para(area.grow(-8), Tx.t("ui.crafts.experiment_no_herbs"), 18, UiKit.HOLLOW)
	var cols := 5
	var cell := (area.size.x - GUTTER) / cols
	list("herbs", area, ceili(herbs.size() / float(cols)), 88, func(row: int, rr: Rect2):
		for k in cols:
			var i := row * cols + k
			if i >= herbs.size(): break
			var h: String = herbs[i]
			var hr := Rect2(rr.position.x + k * cell, rr.position.y, cell - 6, rr.size.y)
			panel(hr, "minor_panel", "selected" if exp_herbs.has(h) else "normal")
			slot_box(Rect2(hr.get_center().x - SLOT_SMALL * 0.5, hr.position.y + 6, SLOT_SMALL, SLOT_SMALL), h, ch.inventory.count(h))
			text(Vector2(hr.position.x + 2, hr.position.y + 72), ContentDB.item_name(h), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, hr.size.x - 4)
			region(hr, "exp_herb", h)
	)
	var why := ""
	if exp_herbs.size() < 2: why = Tx.t("sim.crafting.experiment_count")
	else:
		var seen: Dictionary = Game.crafting.experiment_logged(CraftingAuthority.experiment_key(exp_herbs))
		if not seen.is_empty(): why = Tx.t("sim.crafting.experiment_tried") % Game.crafting.experiment_result_text(seen)
	var tw := s.size.x - 32 - 236
	para(Rect2(s.position.x + 16, foot + 6, tw, 40), Tx.plural("ui.crafts.experiment_log", Game.account.experiments.size()) % Game.account.experiments.size(), 14, UiKit.MIST, 2)
	if why != "" and exp_herbs.size() >= 2: text(Vector2(s.position.x + 16, foot + 64), why, 14, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, tw)
	btn(Rect2(s.end.x - 16 - 220, foot + 8, 220, BTN_H_MAIN), Tx.t("ui.crafts.experiment_go"), "experiment", null, true, why == "", why)

## Deduce (S44): an ancient recipe you hold pages of, its ingredients on the rim, the chance and Deduce at the foot.
func _deduce(ch, foot: float) -> void:
	var s := SIDE
	var rec := ContentDB.entry("recipes", sel)
	var out := str(rec.outputs[0].item)
	var held: int = Game.crafting.pages_held(ch, sel)
	text(s.position + Vector2(20, 34), ContentDB.item_name(out), 22, UiKit.grade_color(str(rec.get("grade", "plain"))), HORIZONTAL_ALIGNMENT_LEFT, s.size.x - 190)
	text(Vector2(s.end.x - 180, s.position.y + 34), Tx.t("ui.crafts.pages_held") % [held, int(rec.get("fragments", 1))], 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 164)
	para(Rect2(s.position + Vector2(20, 44), Vector2(s.size.x - 40, 58)), Tx.t("ui.crafts.deduce_help"), 14, UiKit.MIST, 3)
	_divider()
	_rim(ch, "alchemy")
	var chance: float = Game.crafting.deduce_chance(ch, sel)
	text(Vector2(s.position.x + 16, foot + 46), Tx.t("ui.crafts.deduce_chance") % int(round(chance * 100)), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, s.size.x - 32 - 236)
	var why := ""
	for inp in rec.inputs:
		if ch.inventory.count(str(inp.item)) < int(inp.count): why = Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))
	btn(Rect2(s.end.x - 16 - 220, foot + 8, 220, BTN_H_MAIN), Tx.t("ui.crafts.deduce"), "deduce", null, true, why == "", why)

func _guild(ch, content_r: Rect2) -> void:
	var open: Array = Game.crafting.guilds_open(ch)
	if open.is_empty(): return
	if not open.any(func(g): return str(g.craft) == guild_craft): guild_craft = str(open[0].craft)
	var craft := guild_craft
	var g: Dictionary = Game.crafting.guild_def(craft)
	# One button per open guild along the strip.
	WorkshopKit.board(self, STRIP)
	var bw := minf(260.0, (STRIP.size.x - 16.0 - 12.0 * (open.size() - 1)) / open.size())
	for i in open.size():
		btn(Rect2(STRIP.position.x + 8 + i * (bw + 12), STRIP.position.y + 6, bw, 48), str(open[i].name), "guild_pick", str(open[i].craft),
			str(open[i].craft) == craft, true, "", 18)
	var top := content_r.position.y
	var left := Rect2(content_r.position.x, top, 540, content_r.end.y - top)
	var right := Rect2(left.end.x + 20, top, content_r.end.x - left.end.x - 20, left.size.y)
	panel(left)
	panel(right)
	var rank: String = Game.crafting.guild_rank(ch, craft)
	var ranks: Array = g.get("ranks", [])
	text(left.position + Vector2(20, 34), str(g.name), 22, UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true)
	text(left.position + Vector2(20, 34), _rank_name(craft, rank) if rank != "" else Tx.t("ui.guild.no_rank"), 16,
		UiKit.GOLD if rank != "" else UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, left.size.x - 40)
	var nxt: Dictionary = Game.crafting.next_guild_rank(ch, craft)
	var ex: Dictionary = ch.crafting.get("guild_exam", {})
	var ch_h := (left.size.y - 52.0) / maxf(1.0, ranks.size()) - 6.0
	var y := left.position.y + 48
	for rk in ranks:
		var card := Rect2(left.position.x + 12, y, left.size.x - 24, ch_h)
		var passed: bool = _rank_at_least(craft, rank, str(rk.id))
		panel(card, "minor_panel", "selected" if passed else "normal")
		text(card.position + Vector2(14, 26), _rank_name(craft, str(rk.id)), 20, UiKit.PALE_GOLD if passed else UiKit.PAPER)
		text(card.position + Vector2(14, 48), fit(_exam_task(rk), 16, card.size.x - 28), 16, UiKit.MIST)
		var rew := Tx.t("ui.guild.reward_title") % str(ContentDB.entry("titles", str(rk.get("title", ""))).get("name", ""))
		for e in rk.get("rewards", []):
			if str(e.get("kind", "")) == "learn_recipe": rew += " · " + ContentDB.name_of("recipes", str(e.recipe))
			elif str(e.get("kind", "")) == "grant_item": rew += " · %s ×%d" % [ContentDB.item_name(str(e.item)), int(e.get("count", 1))]
		text(card.position + Vector2(14, 70), fit(rew, 14, card.size.x - 28), 14, UiKit.PALE_GOLD)
		var status_y := card.end.y - 14
		if passed:
			text(Vector2(card.position.x, status_y), Tx.t("ui.guild.passed"), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, card.size.x - 16)
		elif not ex.is_empty() and str(ex.craft) == craft and str(ex.rank) == str(rk.id):
			var left_s: float = Game.crafting.exam_left(ch)
			text(Vector2(card.position.x, status_y), Tx.t("ui.guild.exam_running") % [int(ex.made), int(rk.count), int(left_s / 60.0), int(left_s) % 60], 16,
				UiKit.GOLD, HORIZONTAL_ALIGNMENT_RIGHT, card.size.x - 16)
		elif str(nxt.get("id", "")) == str(rk.id):
			var why: String = Game.crafting.exam_block(ch, rk)
			if why == "" and not ex.is_empty(): why = Tx.t("sim.crafting.exam_running")
			btn(Rect2(card.end.x - 176, card.end.y - 56, 164, 48), Tx.t("ui.guild.start_exam"), "exam", str(rk.id), true, why == "", why, 16)
			if str(rk.get("hall", "")) != "" and why != "":
				text(card.position + Vector2(14, card.size.y - 12), fit(why, 14, card.size.x - 210), 14, UiKit.MIST)
		y += ch_h + 6
	# The commission board.
	text(right.position + Vector2(20, 34), Tx.t("ui.guild.commissions"), 20, UiKit.PAPER)
	if rank == "":
		para(Rect2(right.position + Vector2(20, 52), Vector2(right.size.x - 40, 80)), Tx.t("ui.guild.commissions_locked"), 16, UiKit.MIST)
		return
	var paid: int = Game.crafting.commission_paid_today(ch, craft)
	var cap: int = Game.crafting.commission_cap(ch, craft)
	text(right.position + Vector2(20, 58), Tx.t("ui.guild.cap_line") % [paid, cap], 16, UiKit.MIST)
	var oy := right.position.y + 72
	var orders: Array = Game.crafting.commissions(ch, craft)
	var oh := minf(110.0, (right.end.y - oy - 8.0) / maxf(1.0, orders.size()) - 8.0)
	for o in orders:
		var card2 := Rect2(right.position.x + 12, oy, right.size.x - 24, oh)
		panel(card2, "minor_panel", "disabled" if o.get("done", false) else ("selected" if o.get("accepted", false) else "normal"))
		slot_box(Rect2(card2.position + Vector2(10, 13), Vector2(SLOT_SMALL, SLOT_SMALL)), str(o.item))
		text(card2.position + Vector2(72, 28), fit("%s ×%d" % [ContentDB.item_name(str(o.item)), int(o.count)], 18, card2.size.x - 84), 18, UiKit.PAPER)
		text(card2.position + Vector2(72, 50), Tx.plural("ui.guild.pay", int(o.pay)) % int(o.pay), 16, UiKit.GOLD)
		if o.get("done", false):
			text(card2.position + Vector2(72, card2.size.y - 14), Tx.t("ui.guild.delivered"), 16, UiKit.BRIGHT_JADE)
		elif not o.get("accepted", false):
			btn(Rect2(card2.end.x - 148, card2.end.y - 46, 136, 38), Tx.t("ui.guild.accept"), "c_accept", str(o.id), false, true, "", 16)
		else:
			var have := 0
			for s2 in ch.inventory.bag:
				if s2 != null and str(s2.id) == str(o.item): have += int(s2.get("count", 1))
			var ok2 := have >= int(o.count)
			var missing := Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item))
			btn(Rect2(card2.end.x - 296, card2.end.y - 46, 136, 38), Tx.t("ui.guild.deliver_taels"), "c_taels", str(o.id), true, ok2, missing, 14)
			btn(Rect2(card2.end.x - 148, card2.end.y - 46, 136, 38), Tx.t("ui.guild.deliver_contribution"), "c_contrib", str(o.id), false, ok2, missing, 14)
		oy += oh + 8

## A rank's name in its guild ("Forge Adept"): the badge's own name.
func _rank_name(craft: String, rank: String) -> String:
	var rk: Dictionary = Game.crafting.guild_rank_def(craft, rank)
	return str(ContentDB.entry("titles", str(rk.get("title", ""))).get("name", Tx.t("ui.guild.rank_" + rank)))

## What an exam asks for, in one line.
func _exam_task(rk: Dictionary) -> String:
	var mins := UiKit.span(float(rk.time_s))
	if rk.has("recipe"):
		var item := ContentDB.item_name(str(ContentDB.entry("recipes", str(rk.recipe)).outputs[0].item))
		if str(rk.get("quality", "common")) == "common": return Tx.t("ui.guild.exam_task_count") % [item, int(rk.count), mins]
		return Tx.t("ui.guild.exam_task") % [item, int(rk.count), str(rk.quality).capitalize(), mins]
	return Tx.t("ui.guild.exam_task_grade") % [int(rk.count), str(rk.get("grade", "")).capitalize(), str(rk.quality).capitalize(), mins]

func _rank_at_least(craft: String, have: String, want: String) -> bool:
	var ids: Array = []
	for rk in Game.crafting.guild_def(craft).get("ranks", []): ids.append(str(rk.id))
	return have != "" and ids.find(have) >= ids.find(want)

func _trib_elapsed() -> float:
	return (Time.get_ticks_msec() - int(trib.get("t0", 0))) / 1000.0

func _trib_answer(timing: float) -> void:
	if trib.get("preview", false): return
	var r := submit({"type": "tribulation_shield", "bolt": int(trib.next), "timing": timing})
	(trib.results as Array).append(bool(r.get("held", false)))
	trib.next = int(trib.next) + 1
	Audio.play("hit" if r.get("held", false) else "hurt", "UI")
	if str(r.get("pending", "")) == "soul":
		trib = {"stage": "soul", "catch_at": float(r.catch_at), "window": float(r.window), "t0": Time.get_ticks_msec(), "results": trib.results}
		flash(Tx.t("ui.crafts.soul_flees"))
	elif int(r.get("left", 1)) == 0 and r.has("quality"):
		trib = {}
		flash(Tx.t("ui.crafts.quality_made") % [str(r.quality).replace("_", " ").capitalize(), int(r.get("count", 0))])

func _trib_catch(timing: float) -> void:
	var r := submit({"type": "catch_pill_soul", "timing": timing})
	trib = {}
	if r.get("ok", false):
		flash(Tx.t("ui.crafts.soul_caught") if r.get("caught", false) else Tx.t("ui.crafts.soul_lost"))

## The sky over the furnace: each bolt's ring closes on its strike; raise the shield as it lands. Then the Soul
## streaks across; catch it as it crosses the mark.
func _draw_tribulation(r: Rect2) -> void:
	# A storm sky: darker at the top, the furnace's glow below.
	for k in 8:
		var band := Rect2(r.position.x, r.position.y + k * r.size.y / 8.0, r.size.x, r.size.y / 8.0 + 1)
		draw_rect(band, (UiKit.SURFACE.sky_top as Color).lerp(UiKit.SURFACE.sky_bottom, k / 7.0))
	draw_rect(r, Color(UiKit.GOLD, 0.35), false, 1.0)
	var el := _trib_elapsed()
	var ground := r.end.y - 34
	if str(trib.stage) == "bolts":
		var times: Array = trib.times
		text(Vector2(r.position.x + 14, r.position.y + 26), Tx.t("ui.crafts.stage_tribulation") % [mini(int(trib.next) + 1, times.size()), times.size()], 18, UiKit.PALE_GOLD)
		for i in times.size():
			var cx := r.position.x + (i + 0.5) * r.size.x / times.size()
			var cloud := Vector2(cx, r.position.y + 58)
			var node := Vector2(cx, ground)
			draw_circle(cloud + Vector2(-12, 2), 12, UiKit.SURFACE.cloud)
			draw_circle(cloud + Vector2(8, 0), 15, UiKit.SURFACE.cloud_lit)
			draw_circle(cloud + Vector2(20, 5), 10, UiKit.SURFACE.cloud)
			if i < (trib.results as Array).size():
				# Answered: a shield arc that held, or the bolt that got through.
				if trib.results[i]:
					draw_arc(node, 26, PI, TAU, 24, UiKit.BRIGHT_JADE, 4)
				else:
					_bolt(cloud + Vector2(0, 14), node, UiKit.RED_TEXT)
				continue
			draw_circle(node, 7, Color(UiKit.GOLD, 0.8))
			var until := float(times[i]) - el
			if i == int(trib.next) and until < 1.2:
				# The telegraph: a ring closing on the strike, the sky flickering as it comes.
				var rad := 12.0 + maxf(0.0, until) * 60.0
				draw_arc(node, rad, 0, TAU, 32, Color(UiKit.SKY, 0.9), 3)
				if until < 0.25: _bolt(cloud + Vector2(0, 14), node, Color(UiKit.SKY, 0.9))
	else:
		text(Vector2(r.position.x + 14, r.position.y + 26), Tx.t("ui.crafts.stage_soul"), 18, UiKit.PALE_GOLD)
		var mark_x := r.position.x + r.size.x * 0.7
		r = Rect2(r.position.x, r.position.y + 40, r.size.x, r.size.y - 40)
		draw_line(Vector2(mark_x, r.position.y + 10), Vector2(mark_x, r.end.y - 10), Color(UiKit.GOLD, 0.8), 2)
		var f := clampf(el / maxf(0.1, float(trib.catch_at)), 0.0, 1.6) * 0.7
		var p := Vector2(r.position.x + r.size.x * f, r.position.y + r.size.y * 0.5 + sin(el * 9.0) * 22.0)
		draw_circle(p, 12, UiKit.SURFACE.soul_spark)
		draw_circle(p, 20, Color(UiKit.SURFACE.glow, 0.3))

## A jagged bolt from a cloud to the ground.
func _bolt(a: Vector2, b: Vector2, col: Color) -> void:
	var pts := PackedVector2Array([a])
	for k in range(1, 6):
		var t := k / 6.0
		pts.append(a.lerp(b, t) + Vector2(10.0 if k % 2 == 0 else -10.0, 0))
	pts.append(b)
	draw_polyline(pts, col, 3.0)

func _draw_minigame(r: Rect2) -> void:
	draw_rect(r, UiKit.BAR_TROUGH)
	draw_rect(Rect2(r.position.x + r.size.x * band.x, r.position.y, r.size.x * (band.y - band.x), r.size.y), Color(UiKit.GOLD, 0.55))
	var nx := r.position.x + r.size.x * needle
	draw_rect(Rect2(nx - 3, r.position.y - 6, 6, r.size.y + 12), UiKit.PAPER)
	for i in scores.size():
		draw_circle(Vector2(r.position.x + 12 + i * 22, r.end.y + 16), 7, UiKit.JADE if float(scores[i]) > 0.6 else UiKit.RED)

func on_event(name: String, p: Dictionary) -> void:
	# A reroll or a lock changes the piece in front of you: its affix lines are drawn again.
	if name in ["affixes_rerolled", "affix_locked"]: queue_redraw()
	if name == "craft_step_result":
		flash({"perfect": Tx.t("ui.crafts.perfect"), "good": Tx.t("ui.crafts.good"), "miss": Tx.t("ui.crafts.miss")}.get(str(p.get("grade", "miss")), ""))
	queue_redraw()

func on_action(id: String, data) -> void:
	var ch = c()
	var craft := str(tabs[tab].id)
	match id:
		"sel":
			if not trib.is_empty() or not _session().is_empty(): return   # the heavens (and a lit furnace) do not wait while you browse
			sel = str(data)
			count = 1
			game_on = false
			subst = {}
			screen = "ingredients"
		"exp_herb":
			var h := str(data)
			if exp_herbs.has(h): exp_herbs.erase(h)
			elif exp_herbs.size() < 4: exp_herbs.append(h)
		"experiment":
			var rx := submit({"type": "start_experiment", "herbs": exp_herbs})
			if rx.get("ok", false):
				Audio.play("alchemy", "UI")
				exp_herbs = []
			elif str(rx.get("text", "")) != "": flash(str(rx.text))
		"deduce":
			var rd := submit({"type": "deduce_recipe", "recipe": sel})
			if rd.get("ok", false) and rd.get("success", false): sel = ""
			elif str(rd.get("text", "")) != "": flash(str(rd.text))
		"exam":
			var re := submit({"type": "take_guild_exam", "craft": guild_craft, "rank": str(data)})
			if not re.get("ok", false) and str(re.get("text", "")) != "": flash(str(re.text))
		"guild_pick": guild_craft = str(data)
		"c_accept": submit({"type": "accept_commission", "id": str(data)})
		"c_taels", "c_contrib":
			var rc := submit({"type": "deliver_commission", "id": str(data), "pay": "taels" if id == "c_taels" else "contribution"})
			if not rc.get("ok", false) and str(rc.get("text", "")) != "": flash(str(rc.text))
		"swap":
			# Cycle through the herbs that could stand in for this one, then back to the recipe's own.
			var options: Array = Game.crafting.substitutes_for(ch, sel, str(data))
			var at := options.find(str(subst.get("to", ""))) if str(subst.get("from", "")) == str(data) else -1
			subst = {} if at + 1 >= options.size() else {"from": str(data), "to": str(options[at + 1])}
		"count": count = clampi(count + int(data), 1, int(Game.crafting.furnace_of(ch).get("batch", 10)) if craft == "alchemy" else 10)
		"fire": fire = str(data)
		"trace_cancel":
			trace_on = false
			trace_pts = []
		"craft":
			if craft == "talisman":
				# Inks and spirit paper are simply made; a talisman is traced.
				if ContentDB.entry("recipes", sel).get("traced", false):
					trace_on = true
					trace_pts = []
				else:
					var rt := submit({"type": "trace_talisman", "recipe": sel})
					if rt.get("ok", false): flash(Tx.t("ui.crafts.made") % int(rt.count))
				return
			if craft == "alchemy":
				screen = "furnace"   # Ingredients done: on to the furnace, its fire and its array
				return
			if DIRECT.has(craft):
				var r := submit({"type": DIRECT[craft], "recipe": sel, "count": count if craft in ["cooking", "formations"] else 1})
				if r.get("ok", false):
					puff_at = t
					Audio.play("cook" if craft == "cooking" else "forge", "UI")
					flash({"cooking": Tx.t("ui.crafts.cooked"), "formations": Tx.t("ui.crafts.etched"), "star_charting": Tx.t("ui.crafts.charted"),
						"shipwright": Tx.t("ui.crafts.built")}[craft] % int(r.count))
			else:
				game_on = true
				scores = []
				needle = 0.0
				needle_dir = 1.0
				band = Vector2(0.4 + Rng.stream(c().id, "minigame").randf() * 0.2, 0.0)
				band.y = band.x + 0.16 * _band_mult(craft)
		"strike":
			# Crafting scores the strike (craft_step_result); the page only reports where it landed.
			var mid := (band.x + band.y) * 0.5
			var st := submit({"type": "craft_step", "recipe": sel, "craft": "smithing", "offset": needle - mid})
			scores.append(float(st.get("score", 0.0)))
			Audio.play("forge", "UI")
			if scores.size() >= int(ContentDB.curve("craft_step.steps", 3)):
				game_on = false
				_refine_done(submit({"type": "forge", "recipe": sel}))
			else:
				band.x = 0.25 + Rng.stream(c().id, "minigame").randf() * 0.5
				band.y = band.x + 0.14 * _band_mult(craft)
		"to_ingredients": screen = "ingredients"
		"arr": array = str(data)
		"light":
			var rl := submit({"type": "start_refine", "recipe": sel, "count": count, "fire": fire, "array": array, "substitute": subst})
			if rl.get("ok", false):
				Audio.play("alchemy", "UI")
				play = {}
		"speck":
			if play.get("stage", "") == "extraction" and not (play.gone as Dictionary).has(int(data)):
				play.gone[int(data)] = true
				play.taps = int(play.taps) + 1
				Audio.ui("ui_tap")
		"orb":
			if play.get("phase", "") == "merge" and not (play.order as Array).has(int(data)):
				(play.order as Array).append(int(data))
				Audio.play("alchemy", "UI")
				if (play.order as Array).size() >= (_session().herbs as Array).size():
					play.phase = "turn"
					play.t = -float(_fg("extraction").get("ready_s", 1.2))
		"retry_herb": play = {}
		"put_out": ask(Tx.t("ui.crafts.put_out_ask"), "put_out_yes", null, true)
		"put_out_yes":
			if not preview_rs.is_empty():
				preview_rs = {}
			elif submit({"type": "cancel_refine"}).get("ok", false):
				flash(Tx.t("ui.crafts.fire_out"))
			play = {}
			fanning = false
			screen = "ingredients"
		"queue":
			if submit({"type": "queue_auto_refine", "recipe": sel, "count": count}).get("ok", false):
				flash(Tx.t("ui.crafts.batch_queued"))
		"collect":
			submit({"type": "collect_auto_refine"})
		"_tab":
			sel = ""
			game_on = false
			trace_on = false
			screen = "ingredients"
			fanning = false
			if not _session().is_empty(): sel = str(_session().recipe)   # a lit furnace keeps its recipe
		"forge_mode":
			forge_mode = str(data)
			pick_uid = -1
			to_uid = -1
			picked = {}
			essence = 0
		"gear":
			var uid := int(data)
			match forge_mode:
				"salvage":
					if picked.has(uid): picked.erase(uid)
					else: picked[uid] = true
				"inherit":
					if pick_uid < 0 or pick_uid == uid: pick_uid = uid if pick_uid != uid else -1
					else: to_uid = uid if to_uid != uid else -1
				_:
					pick_uid = uid
					essence = 0
		"clear_pick":
			pick_uid = -1
			to_uid = -1
		"essence": essence = clampi(essence + int(data), 0, int(Game.crafting.upkeep("essence_max", 4)))
		"do_awaken":
			var ra := submit({"type": "awaken_weapon", "uid": pick_uid})
			if ra.get("ok", false): flash(Tx.t("ui.forge.awakened_flash") % str(ra.get("skill", "")))
		"do_enhance":
			var r3 := submit({"type": "enhance", "uid": pick_uid, "essence": essence})
			if r3.get("ok", false):
				Audio.play("forge", "UI")
				flash(Tx.t("ui.forge.enhanced") % int(r3.level) if r3.success else Tx.t("ui.forge.failed") % int(round(float(r3.pity) * 100)))
				essence = 0
			elif str(r3.get("text", "")) != "": flash(str(r3.text))
		"do_mend":
			var rm := submit({"type": "mend_furnace", "uid": pick_uid})
			if rm.get("ok", false):
				Audio.play("forge", "UI")
				flash(Tx.t("ui.forge.mended"))
			elif str(rm.get("text", "")) != "": flash(str(rm.text))
		"do_inherit":
			var r4 := submit({"type": "inherit_enhancement", "from": pick_uid, "to": to_uid})
			if r4.get("ok", false):
				Audio.play("forge", "UI")
				flash(Tx.t("ui.forge.inherited") % int(r4.levels))
				pick_uid = -1
				to_uid = -1
			elif str(r4.get("text", "")) != "": flash(str(r4.text))
		"do_salvage":
			var r5 := submit({"type": "salvage", "items": picked.keys()})
			if r5.get("ok", false):
				Audio.play("forge", "UI")
				flash(Tx.plural("ui.forge.salvaged", (r5.items as Array).size()) % (r5.items as Array).size())
				picked = {}
		"lock_affix": submit({"type": "lock_affix", "uid": pick_uid, "affix": int(data)})
		"do_reroll":
			var r6 := submit({"type": "reroll_affixes", "uid": pick_uid})
			if r6.get("ok", false): Audio.play("forge", "UI")
			elif str(r6.get("text", "")) != "": flash(str(r6.text))
		"choose": submit({"type": "choose_affixes", "uid": pick_uid, "keep": str(data)})
		"natal_flag":
			var r7 := submit({"type": "flag_natal", "uid": pick_uid})
			if not r7.get("ok", false) and str(r7.get("text", "")) != "": flash(str(r7.text))
		"natal_feed":
			var r8 := submit({"type": "feed_natal", "uid": pick_uid, "item": str(data[0]), "count": int(data[1])})
			if r8.get("ok", false): Audio.play("forge", "UI")
		"natal_reforge":
			var r9 := submit({"type": "reforge_natal", "uid": pick_uid})
			if r9.get("ok", false):
				Audio.play("forge", "UI")
				flash(Tx.t("ui.forge.reforged"))
			elif str(r9.get("text", "")) != "": flash(str(r9.text))

# ------------------------------------------------------------------ the five-screen furnace (S15, S44)
## The refine being played: the authority's, or a preview's.
func _session() -> Dictionary:
	if not preview_rs.is_empty(): return preview_rs
	return Game.crafting.refine_session(c()) if c() != null else {}

func _fg(part: String) -> Dictionary:
	return Game.crafting.furnace_game().get(part, {})

## The screens a recipe goes through: a liquid has no Condensation; Heaven grade and up may meet the tribulation.
func _screens(recipe_id: String) -> Array:
	var r := ContentDB.entry("recipes", recipe_id)
	var out := ["ingredients", "furnace", "extraction", "fusion"]
	if not r.get("liquid", false): out.append("condensation")
	if StatRules.grade_index(str(r.get("grade", "plain"))) >= StatRules.grade_index("heaven"): out.append("tribulation")
	return out

func _screen_label(id: String) -> String:
	match id:
		"extraction": return Tx.t("ui.crafts.stage_1")
		"fusion": return Tx.t("ui.crafts.stage_2")
		"condensation": return Tx.t("ui.crafts.stage_3")
	return Tx.t("ui.crafts.screen_" + id)

## What Spirit Sense tells of one herb slot: the sealed roots the batch would use (sound, dyed, or cannot tell).
func _sense_bits(ch, item: String) -> Array:
	if not Unlocks.is_unlocked(ch.id, "spirit_sense") or str(ContentDB.item(item).get("type", "")) != "herb": return []
	var out: Array = []
	var sealed := 0
	var fakes := 0
	for e in Game.crafting.sense_herbs(ch, sel, count, subst):
		if str(e.item) != item: continue
		sealed += int(e.sealed)
		fakes = -1 if int(e.fakes) < 0 else fakes + int(e.fakes)
	if sealed > 0:
		if fakes < 0: out.append(Tx.t("ui.crafts.sense_sealed") % sealed)
		elif fakes > 0: out.append(Tx.t("ui.crafts.sense_fake") % fakes)
		else: out.append(Tx.t("ui.crafts.sense_sound") % sealed)
	return out

## Screen 2 · the Furnace, at the right under the card: the furnace you carry, the fire under it (G1) and the array set
## beneath it (drawn round the furnace's foot on the hearth).
func _furnace_screen(ch, r: Rect2) -> void:
	var x := r.position.x + 16
	var w := r.size.x - 32
	var y := r.position.y
	var fu: Dictionary = Game.crafting.furnace_of(ch)
	if fu.get("cracked", false):
		text(Vector2(x, y + 18), ContentDB.item_name(str(fu.id)), 18, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, w)
		text(Vector2(x, y + 40), Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(fu.id)), 16, UiKit.RED_TEXT, HORIZONTAL_ALIGNMENT_LEFT, w)
	elif str(fu.get("id", "")) != "":
		text(Vector2(x, y + 18), ContentDB.item_name(str(fu.id)) + ("" if str(fu.get("element", "")) == "" else "  ·  " + Tx.t("ui.crafts.furnace_element") % str(fu.element).capitalize()), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w)
		text(Vector2(x, y + 40), Tx.t("ui.crafts.furnace_stats") % [int(fu.get("batch", 1)), int(round(float(fu.get("band", 0.0)) * 100)),
			int(round(float(fu.get("filter", 0.0)) * 100)), int(round(float(fu.get("yield", 0.0)) * 100))], 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	else:
		text(Vector2(x, y + 28), Tx.t("ui.crafts.no_furnace"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w)
	# The fire, and how wide it (with the furnace, your control and the array) makes the heat band.
	var have: Array = Game.crafting.fires_available(ch)
	if not fire in have: fire = "charcoal"
	var need_fire := str(ContentDB.entry("recipes", sel).get("fire", ""))
	if need_fire != "" and need_fire in have: fire = need_fire   # a pill that takes only one fire (S48)
	y += 70
	text(Vector2(x, y), Tx.t("ui.crafts.fire"), 16, UiKit.GOLD)
	var band_w: float = Game.crafting.heat_band(ch, fire, sel, array, subst)
	text(Vector2(x + 120, y), Tx.t("ui.crafts.heat_band") % int(round(band_w * 100)), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, w - 120)
	var fw := (w - 24) / 4.0
	for i in FIRES.size():
		var f: String = FIRES[i]
		btn(Rect2(x + i * (fw + 8), y + 8, fw, 48), Tx.t("ui.crafts.fire_" + f), "fire", f, fire == f, f in have, Tx.t("ui.crafts.fire_" + f + "_locked"), 16)
	# The array: the one that answers the principal herb widens every heat band.
	y += 76
	var suits: String = Game.crafting.suited_array(sel, subst)
	text(Vector2(x, y), Tx.t("ui.crafts.array"), 16, UiKit.GOLD)
	if suits != "": text(Vector2(x + 120, y), Tx.t("ui.crafts.array_suits") % Tx.t("ui.crafts.array_" + suits), 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, w - 120)
	var aw := (w - 8) / 2.0
	for i in 2:
		var a: String = ["water", "flame"][i]
		btn(Rect2(x + i * (aw + 8), y + 8, aw, 48), Tx.t("ui.crafts.array_" + a), "arr", a, array == a, true, "", 18)
	para(Rect2(x, y + 60, w, 40), Tx.t("ui.crafts.array_hint_" + ({"water": "hot", "flame": "cold"}.get(suits, "neutral") as String)), 14, UiKit.MIST, 2)
	btn(Rect2(x, r.end.y - 64, 200, 56), Tx.t("ui.crafts.back_ingredients"), "to_ingredients", null, false, true, "", 18)
	var why: String = Game.crafting.refine_block(ch, sel, count, fire, subst)
	btn(Rect2(r.end.x - 16 - 240, r.end.y - 72, 240, BTN_H_MAIN), Tx.t("ui.crafts.light"), "light", null, true, why == "", why)

## Screens 3-6, once the furnace is lit: the batch on the card, the step's name and what to do at the right with its
## timed control at the foot; the screen itself is played on the hearth, over the furnace.
func _furnace_live() -> void:
	var rs := _session()
	var recipe := str(rs.get("recipe", sel))
	var s := SIDE
	var stage := "tribulation" if not trib.is_empty() else str(rs.get("stage", "extraction"))
	var rec := ContentDB.entry("recipes", recipe)
	_card_head(rec)
	if not rs.is_empty():
		text(s.position + Vector2(108, 66), Tx.t("ui.crafts.batch_line") % [int(rs.count), Tx.t("ui.crafts.fire_" + str(rs.fire)), Tx.t("ui.crafts.array_" + str(rs.array))],
			16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, s.size.x - 124)
	_divider()
	var ids := _screens(recipe)
	if not ids.has(stage): ids.append(stage)
	heading(Vector2(s.position.x + 16, s.position.y + 140), "%d · %s" % [ids.find(stage) + 1, _screen_label(stage)], s.size.x - 32)
	var body := Rect2(s.position.x + 16, s.position.y + 156, s.size.x - 32, s.size.y - 156 - 96)
	if not rs.is_empty() and trib.is_empty() and not play.get("scorched", false):
		btn(Rect2(s.position.x + 16, s.end.y - 76, 180, 60), Tx.t("ui.crafts.put_out"), "put_out", null, false, true, "", 18)
	match stage:
		"extraction": _screen_extraction(rs, body)
		"fusion": _screen_fusion(rs, body)
		"condensation": _screen_condensation(rs, body)
		"tribulation":
			_draw_tribulation(Rect2(HEARTH.position.x + 4, HEARTH.position.y + 4, HEARTH.size.x - 8, 150))
			para(body, Tx.t("ui.crafts.sub_tribulation"), 18, UiKit.PAPER, 3)
			_hot_btn(HOT, Tx.t("ui.crafts.shield") if str(trib.stage) == "bolts" else Tx.t("ui.crafts.catch"), "trib")

## Where the step's timed control stands: the foot of the controls, at the right.
const HOT := Rect2(1184 - 16 - 240, 672 - 92, 240, 76)

## A control that acts on the press (the fan, the array's turn, Condense, the shield), drawn like a primary button.
func _hot_btn(rect: Rect2, label: String, id: String, held := false) -> void:
	draw_style_box(UiKit.style("button_primary", "pressed" if held else "normal"), rect)
	UiKit.draw_inked(self, label, rect.position + Vector2(0, rect.size.y * 0.5 + 8) + (Vector2(1, 2) if held else Vector2.ZERO), 22, UiKit.PALE_GOLD,
		HORIZONTAL_ALIGNMENT_CENTER, rect.size.x)
	hot_rects[id] = rect

## Where a herb's band sits at time `t` (its centre, as a share of the gauge from the bottom).
static func _band_mid(herb: Dictionary, t: float) -> float:
	return float(herb.centre) + float(herb.sway) * sin(TAU * maxf(0.0, t) / maxf(0.5, float(herb.period)) + float(herb.phase))

## The furnace's mouth on the hearth, where the screens are played: over the vessel's top.
func _mouth() -> Vector2:
	return Vector2(HEARTH.get_center().x, HEARTH.position.y + 206)

## Screen 3 · Extraction: the herbs on the rim in the order they go in, the heat gauge with its swaying band at the
## hearth's left, the impurities rising from the furnace's mouth; the hint, the herb's time and the fan at the right.
func _screen_extraction(rs: Dictionary, body: Rect2) -> void:
	var herbs: Array = rs.herbs
	var i := mini(int(rs.at), herbs.size() - 1)
	var herb: Dictionary = herbs[i]
	var k := _fg("extraction")
	var secs := float(k.get("seconds", 5.0))
	var pt := float(play.get("t", -1.0))
	var h := HEARTH
	# The herbs on the rim.
	var cw := minf(132.0, (h.size.x - 112) / maxf(1.0, herbs.size()))
	for j in herbs.size():
		var hb: Dictionary = herbs[j]
		var cx := h.position.x + 96 + cw * (j + 0.5)
		var sr := Rect2(cx - SLOT * 0.5, h.position.y + 12, SLOT, SLOT)
		slot_box(sr, str(hb.item), 0, "", "", null, j == i)
		text(Vector2(cx - cw * 0.5 + 2, sr.end.y + 20), ContentDB.item_name(str(hb.item)), 14, UiKit.PAPER if j <= i else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, cw - 4)
		var st := Tx.t("ui.crafts.herb_waiting")
		var col := UiKit.HOLLOW
		if j < (rs.extraction as Array).size():
			st = "%d%%" % int(round(float(rs.extraction[j]) * 100))
			col = UiKit.BRIGHT_JADE
		elif j == i and play.get("scorched", false):
			st = Tx.t("ui.crafts.scorched")
			col = UiKit.RED_TEXT
		elif j == i:
			# Hot herbs sit their band high on the gauge, cold ones low (S44).
			st = Tx.t("ui.crafts.herb_in_fire") + (" · " + Tx.t("ui.crafts.nature_" + str(hb.nature)) if str(hb.nature) in ["hot", "cold"] else "")
			col = UiKit.GOLD
		text(Vector2(cx - cw * 0.5 + 2, sr.end.y + 40), st, 14, col, HORIZONTAL_ALIGNMENT_CENTER, cw - 4)
	# The heat gauge: the gold band sways; the heat rises while the flame is fanned.
	var g := Rect2(h.position.x + 28, h.position.y + 44, 44, h.size.y - BLOCK_H - 84)
	text(Vector2(g.position.x - 16, g.position.y - 12), Tx.t("ui.crafts.heat"), 16, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, g.size.x + 32)
	draw_rect(g.grow(4), UiKit.INK)
	draw_rect(g, UiKit.BAR_TROUGH)
	var heat := float(play.get("heat", 0.3))
	var mid := _band_mid(herb, pt)
	var half := float(herb.width) * 0.5
	var inside := absf(heat - mid) <= half
	draw_rect(Rect2(g.position.x, g.end.y - g.size.y * (mid + half), g.size.x, g.size.y * half * 2.0), Color(UiKit.GOLD, 0.75 if inside else 0.45))
	draw_rect(Rect2(g.position.x + 12, g.end.y - g.size.y * heat, g.size.x - 24, g.size.y * heat), Color(UiKit.SURFACE.ember, 0.9))
	draw_rect(Rect2(g.position.x - 6, g.end.y - g.size.y * heat - 2, g.size.x + 12, 4), UiKit.PAPER)
	draw_rect(g, Color(UiKit.BRONZE, 0.9), false, 2.0)
	text(Vector2(g.position.x - 16, g.end.y + 22), Tx.t("ui.crafts.cool"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, g.size.x + 32)
	# The impurities rising from the furnace's mouth, to be tapped away.
	var centre := _mouth()
	var rad := 70.0
	var gone: Dictionary = play.get("gone", {})
	var specks: Array = herb.specks
	for j in specks.size():
		var sp: Dictionary = specks[j]
		if gone.has(j) or pt < float(sp.t) or pt > float(sp.t) + float(k.get("speck_s", 1.2)): continue
		var at := centre + Vector2((float(sp.x) - 0.5) * rad * 1.6, (float(sp.y) - 0.5) * rad * 1.6)
		var a := 0.3 if sp.get("faint", false) else 1.0
		draw_circle(at, 22, Color(UiKit.GOLD, 0.25 * a))
		draw_circle(at, 18, Color(UiKit.SURFACE.ash, 0.4 * a))
		draw_circle(at, 13, Color(UiKit.SURFACE.cinder, a))
		region(Rect2(at - Vector2(26, 26), Vector2(52, 52)), "speck", j)
	if pt < 0.0 and not play.get("scorched", false):
		text(Vector2(centre.x - 150, centre.y + 12), Tx.t("ui.crafts.ready"), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 300, true)
	# At the right: what to do, and the herb's time in the fire.
	if play.get("scorched", false):
		para(Rect2(body.position, Vector2(body.size.x, 90)), Tx.t("ui.crafts.scorched_retry") if play.get("retry", false) else Tx.t("ui.crafts.scorched_none"), 16, UiKit.PAPER, 4)
		if play.get("retry", false): btn(Rect2(body.end.x - 200, SIDE.end.y - 76, 200, 60), Tx.t("ui.crafts.try_again"), "retry_herb", null, true, true, "", 18)
		btn(Rect2(body.position.x, SIDE.end.y - 76, 180, 60), Tx.t("ui.crafts.put_out"), "put_out", null, false, true, "", 18)
		return
	para(Rect2(body.position, Vector2(body.size.x, 66)), Tx.t("ui.crafts.extract_hint"), 16, UiKit.PAPER, 3)
	bar(Rect2(body.position.x, body.position.y + 82, body.size.x, 30), clampf(pt / secs, 0.0, 1.0), UiKit.JADE, ContentDB.item_name(str(herb.item)))
	_hot_btn(HOT, Tx.t("ui.crafts.fan"), "fan", fanning)

## A herb's place on the Fusion ring: the recipe's order is not the ring's.
func _ring_slot(rs: Dictionary, j: int) -> int:
	var keys: Array = []
	for h in rs.herbs: keys.append((str(h.item) + str(rs.recipe)).hash())
	var sorted_keys := keys.duplicate()
	sorted_keys.sort()
	return sorted_keys.find(keys[j])

static func _nature_color(nature: String) -> Color:
	return UiKit.WARNING if nature == "hot" else (UiKit.SKY if nature == "cold" else UiKit.BRIGHT_JADE)

## Screen 4 · Fusion: the essences circle the furnace's mouth, placed apart from their order; tap them into the core in
## the recipe's order, then turn the array as the needle crosses each mark (at the right).
func _screen_fusion(rs: Dictionary, body: Rect2) -> void:
	var herbs: Array = rs.herbs
	var merged: Array = play.get("order", [])
	var turning := str(play.get("phase", "merge")) == "turn"
	var core := _mouth() - Vector2(0, 30)
	var orbit := 128.0
	var glow_k := 0.15 + 0.6 * merged.size() / maxf(1.0, herbs.size())
	for gi in 4: draw_circle(core, 56 - gi * 12, Color(UiKit.SURFACE.glow, glow_k * (0.25 + gi * 0.2)))
	draw_arc(core, 56, 0, TAU, 48, Color(UiKit.GOLD, 0.9), 3.0, true)
	for j in herbs.size():
		var h: Dictionary = herbs[j]
		var ang := -PI * 0.5 + PI / herbs.size() + TAU * _ring_slot(rs, j) / herbs.size()
		var at := core + Vector2(cos(ang) * orbit * 1.35, sin(ang) * orbit * 0.9)
		var col := _nature_color(str(h.nature))
		if merged.has(j):
			draw_arc(at, 34, 0, TAU, 32, Color(col, 0.35), 2.0, true)
			continue
		draw_circle(at, 38, Color(UiKit.INK, 0.55))
		draw_circle(at, 38, Color(col, 0.28))
		draw_arc(at, 38, 0, TAU, 32, col, 3.0, true)
		icon_at(Rect2(at - Vector2(32, 32), Vector2(64, 64)), str(ContentDB.item(str(h.item)).get("icon", h.item)))
		region(Rect2(at - Vector2(42, 42), Vector2(84, 84)), "orb", j, not turning)
	if turning and float(play.get("t", 0.0)) < 0.0:
		text(Vector2(core.x - 150, core.y + 12), Tx.t("ui.crafts.ready"), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 300, true)
	para(Rect2(body.position, Vector2(body.size.x, 44)), Tx.t("ui.crafts.turn_hint") if turning else Tx.t("ui.crafts.fuse_hint"), 16, UiKit.PAPER, 2)
	# The essences merged so far, in the order they went in.
	text(Vector2(body.position.x, body.position.y + 64), Tx.t("ui.crafts.merged"), 16, UiKit.GOLD)
	for n in merged.size():
		var h2: Dictionary = herbs[int(merged[n])]
		slot_box(Rect2(body.position.x + 110 + n * 52, body.position.y + 44, SLOT_SMALL, SLOT_SMALL), str(h2.item))
	# The array's turns: a needle crosses the bar; each mark wants a turn as it passes.
	var bar_r := Rect2(body.position.x, body.end.y - 30, body.size.x, 26)
	var arr := str(play.get("array", rs.array))
	text(Vector2(body.position.x, bar_r.position.y - 10), Tx.t("ui.crafts.array_" + arr), 16, _nature_color("cold" if arr == "water" else "hot"))
	draw_rect(bar_r, UiKit.BAR_TROUGH)
	var offs: Array = play.get("offs", [])
	var marks: Array = rs.marks
	var win := float(_fg("fusion").get("window", 0.1))
	for m in marks.size():
		var mxp := bar_r.position.x + bar_r.size.x * float(marks[m])
		var mc := UiKit.GOLD
		if m < offs.size(): mc = UiKit.BRIGHT_JADE if absf(float(offs[m])) <= win else UiKit.RED
		draw_rect(Rect2(mxp - bar_r.size.x * win * 0.5, bar_r.position.y, bar_r.size.x * win, bar_r.size.y), Color(mc, 0.3))
		draw_rect(Rect2(mxp - 2, bar_r.position.y - 6, 4, bar_r.size.y + 12), mc)
	if turning:
		var f := clampf(float(play.get("t", 0.0)) / float(_fg("fusion").get("seconds", 3.6)), 0.0, 1.0)
		draw_rect(Rect2(bar_r.position.x + bar_r.size.x * f - 3, bar_r.position.y - 8, 6, bar_r.size.y + 16), UiKit.PAPER)
		_hot_btn(HOT, Tx.t("ui.crafts.turn"), "turn")
	draw_rect(bar_r, Color(UiKit.BRONZE, 0.9), false, 2.0)

## Screen 5 · Condensation: over the furnace the ring closes on the pill; condense as it meets the outline.
func _screen_condensation(rs: Dictionary, body: Rect2) -> void:
	var k := _fg("condensation")
	var secs := float(k.get("seconds", 2.4))
	var pt := float(play.get("t", -1.0))
	var centre := _mouth() - Vector2(0, 50)
	var rp := 46.0
	var rs0 := 118.0
	var rad := rp + (rs0 - rp) * (1.0 - clampf(pt, 0.0, secs) / secs)
	if pt > secs: rad = rp - (pt - secs) / maxf(0.05, float(k.get("late", 0.2))) * rp * 0.45
	var off := pt - secs
	var col := UiKit.PAPER
	if absf(off) <= float(k.get("perfect", 0.08)): col = UiKit.GOLD
	elif off > 0.0: col = UiKit.RED
	var out := str(ContentDB.entry("recipes", str(rs.recipe)).outputs[0].item)
	draw_arc(centre, rs0, 0, TAU, 64, Color(UiKit.HOLLOW, 0.4), 1.5, true)
	for g in 3: draw_circle(centre, rp + 26 - g * 9, Color(UiKit.SURFACE.glow, (0.05 + 0.12 * clampf(pt / secs, 0.0, 1.0)) * (g + 1)))
	icon_at(Rect2(centre - Vector2(32, 32), Vector2(64, 64)), str(ContentDB.item(out).get("icon", out)))
	draw_arc(centre, rp, 0, TAU, 48, Color(UiKit.PALE_GOLD, 0.8), 2.0, true)
	if pt >= 0.0: draw_arc(centre, maxf(4.0, rad), 0, TAU, 64, col, 4.0, true)
	else: text(Vector2(centre.x - 150, centre.y - rp - 30), Tx.t("ui.crafts.ready"), 30, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 300, true)
	para(body, Tx.t("ui.crafts.condense_hint"), 16, UiKit.PAPER, 4)
	_hot_btn(HOT, Tx.t("ui.crafts.condense"), "condense")

## A preview's refine: Healing Pill, one herb extracted; nothing is sent, and time stands still.
func _preview(stage: String) -> void:
	var r := ContentDB.entry("recipes", sel)
	var herbs: Array = []
	for i in (r.inputs as Array).size():
		var item := str(r.inputs[i].item)
		herbs.append({"item": item, "role": str(r.roles[i]), "nature": str(ContentDB.item(item).get("nature", "")), "count": int(r.inputs[i].count) * 2,
			"centre": 0.58 if i == 0 else 0.5, "sway": 0.14, "period": 3.2, "phase": 0.4 + i, "width": 0.22,
			"specks": [{"t": 0.6, "x": 0.34, "y": 0.42, "faint": false}, {"t": 0.9, "x": 0.64, "y": 0.6, "faint": true}]})
	var order: Array = []
	for i in herbs.size(): order.append(i)
	var st := "fusion" if stage.begins_with("fusion") else ("extraction" if stage == "scorched" else stage)
	preview_rs = {"recipe": sel, "count": 2, "fire": "charcoal", "array": "water", "substitute": {}, "herbs": herbs, "order": order,
		"marks": [0.34, 0.7], "liquid": false, "stage": st, "at": 1 if st == "extraction" else herbs.size(),
		"extraction": [0.92] if st == "extraction" else [0.92, 0.81], "fusion": 0.0, "preview": true}
	match stage:
		"extraction": play = {"stage": "extraction", "herb": 1, "t": 1.2, "heat": 0.5, "inside": 0.9, "taps": 0, "gone": {}, "frozen": true}
		"scorched": play = {"stage": "extraction", "herb": 1, "t": 5.0, "heat": 0.9, "inside": 0.4, "taps": 0, "gone": {}, "frozen": true,
			"sent": true, "scorched": true, "retry": true}
		"fusion": play = {"stage": "fusion", "phase": "merge", "order": [0], "t": 0.0, "offs": [], "array": "water", "frozen": true}
		"fusion_turn": play = {"stage": "fusion", "phase": "turn", "order": [0, 1], "t": 1.9, "offs": [0.03], "array": "flame", "frozen": true}
		"condensation": play = {"stage": "condensation", "t": 1.9, "frozen": true}

## The hand's side of the screen being played: timers, the heat, marks gone by, a ring gone too far.
func _tick_furnace(delta: float) -> void:
	var rs := _session()
	if rs.is_empty() or not trib.is_empty() or play.get("frozen", false): return
	var ready := float(_fg("extraction").get("ready_s", 1.2))
	match str(rs.stage):
		"extraction":
			if str(play.get("stage", "")) != "extraction" or int(play.get("herb", -1)) != int(rs.at):
				play = {"stage": "extraction", "herb": int(rs.at), "t": -ready, "heat": 0.3, "inside": 0.0, "taps": 0, "gone": {}}
				fanning = false
			if play.get("scorched", false) or play.get("sent", false): return
			play.t = float(play.t) + delta
			if float(play.t) < 0.0: return
			var k := _fg("extraction")
			var herb: Dictionary = rs.herbs[int(rs.at)]
			play.heat = clampf(float(play.heat) + (float(k.get("rise_per_s", 0.6)) if fanning else -float(k.get("fall_per_s", 0.45))) * delta, 0.0, 1.0)
			if absf(float(play.heat) - _band_mid(herb, float(play.t))) <= float(herb.width) * 0.5: play.inside = float(play.inside) + delta
			var secs := float(k.get("seconds", 5.0))
			if float(play.t) >= secs:
				play.sent = true
				fanning = false
				var r := submit({"type": "refine_input", "step": "extraction", "value": {"herb": int(rs.at), "held": float(play.inside) / secs, "taps": int(play.taps)}})
				if r.get("scorched", false):
					play.scorched = true
					play.retry = bool(r.get("retry", false))
					flash(str(r.get("text", "")))
					Audio.play("hurt", "UI")
				elif r.get("ok", false): Audio.play("alchemy", "UI")
		"fusion":
			if str(play.get("stage", "")) != "fusion":
				play = {"stage": "fusion", "phase": "merge", "order": [], "t": 0.0, "offs": [], "array": str(rs.array)}
			if str(play.phase) != "turn" or play.get("sent", false): return
			play.t = float(play.t) + delta
			var kf := _fg("fusion")
			var f := float(play.t) / float(kf.get("seconds", 3.6))
			var marks: Array = rs.marks
			var offs: Array = play.offs
			# A mark the needle has gone well past unanswered counts as missed.
			while offs.size() < marks.size() and f > float(marks[offs.size()]) + float(kf.get("window", 0.1)): offs.append(99.0)
			if offs.size() >= marks.size(): _send_fusion(rs)
		"condensation":
			if str(play.get("stage", "")) != "condensation": play = {"stage": "condensation", "t": -ready}
			if play.get("sent", false): return
			play.t = float(play.t) + delta
			var kc := _fg("condensation")
			# Nothing pressed as the ring shrinks inside the pill: too late, it cracks.
			if float(play.t) - float(kc.get("seconds", 2.4)) > float(kc.get("late", 0.2)) + 0.1: _send_condense(float(play.t) - float(kc.get("seconds", 2.4)))

## A timed control pressed.
func _hot(id: String) -> void:
	var rs := _session()
	match id:
		"trib":
			var el := _trib_elapsed()
			if str(trib.get("stage", "")) == "bolts" and int(trib.next) < (trib.times as Array).size():
				_trib_answer(el - float(trib.times[int(trib.next)]))
			elif str(trib.get("stage", "")) == "soul":
				_trib_catch(el - float(trib.catch_at))
		"turn":
			if rs.is_empty() or str(play.get("phase", "")) != "turn" or float(play.get("t", -1.0)) < 0.0 or play.get("sent", false) or play.get("frozen", false): return
			var marks: Array = rs.marks
			var offs: Array = play.offs
			if offs.size() >= marks.size(): return
			offs.append(float(play.t) / float(_fg("fusion").get("seconds", 3.6)) - float(marks[offs.size()]))
			play.array = "flame" if str(play.array) == "water" else "water"
			Audio.play("technique", "UI")
			if offs.size() >= marks.size(): _send_fusion(rs)
		"condense":
			if rs.is_empty() or float(play.get("t", -1.0)) < 0.0 or play.get("sent", false) or play.get("frozen", false): return
			_send_condense(float(play.t) - float(_fg("condensation").get("seconds", 2.4)))

func _send_fusion(rs: Dictionary) -> void:
	play.sent = true
	var r := submit({"type": "refine_input", "step": "fusion", "value": {"order": play.order, "marks": play.offs}})
	if not r.get("ok", false):
		play = {}
		if str(r.get("reason", "")) == "blast": screen = "ingredients"
		return
	if r.has("quality") or r.has("pending"): _refine_done(r)   # a liquid is done at Fusion
	elif not r.get("in_order", true): flash(Tx.t("ui.crafts.out_of_order"))

func _send_condense(offset: float) -> void:
	play.sent = true
	var r := submit({"type": "refine_input", "step": "condensation", "value": {"offset": offset}})
	if r.get("cracked", false):
		flash(str(r.get("text", "")))
		Audio.play("hurt", "UI")
		play = {}
		screen = "ingredients"
		return
	_refine_done(r)

## What came out of the furnace (or the forge): the pills, or the tribulation that must be met first.
func _refine_done(r2: Dictionary) -> void:
	play = {}
	screen = "ingredients"
	if r2.get("ok", false) and str(r2.get("pending", "")) == "tribulation":
		# S44: Heaven-grade Halo or Soul: the heavens test the pill before it is yours.
		trib = {"stage": "bolts", "times": r2.bolts, "window": float(r2.window), "t0": Time.get_ticks_msec(), "next": 0, "results": [],
			"quality": str(r2.quality)}
		flash(Tx.t("ui.crafts.tribulation_begins"))
	elif r2.get("ok", false):
		puff_at = t
		var made := Tx.t("ui.crafts.quality_made") % [str(r2.quality).replace("_", " ").capitalize(), int(r2.count)]
		if int(r2.get("marks", 0)) > 0: made += " · " + Tx.plural("ui.crafts.marks", int(r2.marks)) % int(r2.marks)
		flash(made)

func _band_mult(craft: String) -> float:
	return Game.crafting.band_mult(c(), fire) if craft == "alchemy" else 1.0
