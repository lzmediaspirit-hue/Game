extends Page
## Crafts (S15, S16): cooking, alchemy and the forge share one recipe book.
## Alchemy and forging play a short timing mini-game (three strikes into the
## glowing band); its scores go to the authority, which rolls the quality.

var CRAFTS := [["cooking", Tx.t("ui.crafts.cooking")], ["alchemy", Tx.t("ui.crafts.alchemy")], ["smithing", Tx.t("ui.crafts.forge")], ["formations", Tx.t("ui.crafts.arrays")],
	["talisman", Tx.t("ui.crafts.talismans")], ["guild", Tx.t("ui.crafts.guild")], ["star_charting", Tx.t("ui.crafts.charts")], ["shipwright", Tx.t("ui.crafts.vessels")]]
## The unlock behind a tab when it is not the craft's own id (S44: the Alchemist Guild).
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
var count := 1
var game_on := false
var needle := 0.0
var needle_dir := 1.0
var scores: Array = []
var band := Vector2(0.45, 0.62)
var fire := "charcoal"
var subst: Dictionary = {}         # S44 Alchemy Dao tier 5: {from, to}, one herb standing in for another
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

func _init() -> void:
	title = Tx.t("ui.crafts.crafts")

func setup() -> void:
	var ch = c()
	tabs = []
	for cr in CRAFTS:
		# The Starsea tabs stay hidden until Sage 3 opens them, so the valley page is unchanged.
		if cr[0] in ["star_charting", "shipwright"] and not Unlocks.is_unlocked(ch.id, "star_charting"): continue
		var key := str(TAB_UNLOCK.get(cr[0], cr[0]))
		tabs.append({"id": cr[0], "label": cr[1], "locked": "" if Unlocks.is_unlocked(ch.id, key) else Unlocks.locked_text(key)})
	var want := -1
	for i in tabs.size():
		if str(tabs[i].id) == str(PAGE_TAB.get(page_id, "")): want = i
	# A page opened for one recipe (a quest link, or a preview: --open-page=alchemy:healing_pill).
	var pick := str(args.get("tab", ""))
	if ContentDB.has_entry("recipes", pick) or pick == EXPERIMENT: sel = pick
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
	if game_on:
		needle += needle_dir * delta * (0.9 + scores.size() * 0.35)
		if needle > 1.0:
			needle = 1.0
			needle_dir = -1.0
		elif needle < 0.0:
			needle = 0.0
			needle_dir = 1.0

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var craft := str(tabs[tab].id)
	if str(tabs[tab].get("locked", "")) != "":
		para(Rect2(content.position + Vector2(30, 30), content.size - Vector2(60, 60)), str(tabs[tab].locked), 21, UiKit.MIST)
		return
	if craft == "smithing":
		var mw := (content.size.x) / FORGE_MODES.size()
		for i in FORGE_MODES.size():
			var m: String = FORGE_MODES[i]
			btn(Rect2(content.position.x + i * mw + 2, content.position.y, mw - 4, 46), Tx.t("ui.forge." + m), "forge_mode", m, forge_mode == m, true, "", 18)
		if forge_mode != "recipes":
			_forge(ch, Rect2(content.position.x, content.position.y + 56, content.size.x, content.size.y - 56))
			return
	if craft == "guild":
		_guild(ch, content)
		return
	var top := 56.0 if craft == "smithing" else 0.0
	var list_r := Rect2(content.position.x, content.position.y + top, 420, content.size.y - top)
	panel(list_r)
	var recipes := recipes_for(ch, craft)
	# S44: the alchemy list also holds the experiment bench and the ancient recipes you have pages of.
	var extra: Array = []
	if craft == "alchemy":
		if Unlocks.is_unlocked(ch.id, "experiments"): extra.append(EXPERIMENT)
		extra.append_array(Game.crafting.ancient_in_progress(ch))
	var prof: Dictionary = ch.professions.get(craft, {"rank": "apprentice", "xp": 0})
	text(Vector2(list_r.position.x + 16, list_r.end.y - 14), "%s · %s" % [str(prof.rank).capitalize(), UiKit.fmt(float(prof.xp))], 16, UiKit.MIST)
	list("rec", Rect2(list_r.position + Vector2(8, 8), list_r.size - Vector2(16, 40)), extra.size() + recipes.size(), 62, func(i: int, rr: Rect2):
		if i < extra.size():
			var xid: String = extra[i]
			panel(rr, "minor_panel", "selected" if sel == xid else "normal")
			if xid == EXPERIMENT:
				slot_box(Rect2(rr.position + Vector2(6, 4), Vector2(50, 50)), "murky_pill")
				text(rr.position + Vector2(66, 36), Tx.t("ui.crafts.experiment"), 18, UiKit.PALE_GOLD)
			else:
				var xr := ContentDB.entry("recipes", xid)
				slot_box(Rect2(rr.position + Vector2(6, 4), Vector2(50, 50)), "manual_page")
				text(rr.position + Vector2(66, 28), ContentDB.item_name(str(xr.outputs[0].item)), 18, UiKit.GOLD)
				text(rr.position + Vector2(66, 50), Tx.t("ui.crafts.pages_held") % [Game.crafting.pages_held(ch, xid), int(xr.get("fragments", 1))], 14, UiKit.MIST)
			region(rr, "sel", xid)
			return
		var r: Dictionary = recipes[i - extra.size()]
		var out := str(r.outputs[0].item)
		var why := Game.crafting.recipe_check(ch, str(r.id), 1, craft)
		panel(rr, "minor_panel", "selected" if sel == str(r.id) else "normal")
		slot_box(Rect2(rr.position + Vector2(6, 4), Vector2(50, 50)), out)
		text(rr.position + Vector2(66, 36), ContentDB.item_name(out), 18, UiKit.PAPER if why == "" else UiKit.MIST)
		region(rr, "sel", str(r.id))
	)
	var right := Rect2(list_r.end.x + 20, list_r.position.y, content.end.x - list_r.end.x - 20, list_r.size.y)
	panel(right)
	if craft == "alchemy" and sel == EXPERIMENT:
		_experiment(ch, right)
		return
	if craft == "alchemy" and extra.has(sel):
		_deduce(ch, right)
		return
	if sel == "" or ContentDB.entry("recipes", sel).is_empty() or str(ContentDB.entry("recipes", sel).craft) != craft:
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), (Tx.t("ui.crafts.choose_a_recipe_stand_near") % {"cooking": Tx.t("ui.crafts.cooking_pot"), "alchemy": "furnace", "smithing": "forge",
			"star_charting": Tx.t("ui.crafts.chart_table"), "shipwright": Tx.t("ui.crafts.slipway")}[craft]) if not craft in ["formations", "talisman"] else Tx.t("ui.crafts.choose_a_plate_to_etch") if craft == "formations" else Tx.t("ui.crafts.choose_a_talisman"), 19, UiKit.MIST)
		if craft == "alchemy": _auto(ch, right)
		return
	var rec := ContentDB.entry("recipes", sel)
	var out2 := str(rec.outputs[0].item)
	slot_box(Rect2(right.position + Vector2(24, 24), Vector2(72, 72)), out2, int(rec.outputs[0].count))
	text(right.position + Vector2(110, 56), ContentDB.item_name(out2), 24, UiKit.grade_color(str(rec.get("grade", "plain"))))
	para(Rect2(right.position + Vector2(110, 68), Vector2(right.size.x - 130, 44)), str(ContentDB.item(out2).get("desc", "")), 16, UiKit.MIST, 2)
	var alch := craft == "alchemy"
	var y := right.position.y + (118 if alch else 124)
	var inputs: Array = Game.crafting.inputs_with(sel, subst) if alch else rec.inputs
	var roles: Array = rec.get("roles", [])
	var can_swap: bool = alch and int(ch.cultivator.daos.get("alchemy", {}).get("tier", 0)) >= int(Game.crafting.upkeep("substitute_tier", 5))
	for i in inputs.size():
		var inp: Dictionary = inputs[i]
		var have = ch.inventory.count(str(inp.item))
		var need := int(inp.count) * count
		slot_box(Rect2(right.position.x + 24, y, 48 if alch else 52, 48 if alch else 52), str(inp.item))
		var name_y := y + 22 if alch else y + 34
		text(Vector2(right.position.x + 90, name_y), "%s  %d / %d" % [ContentDB.item_name(str(inp.item)), have, need], 18, UiKit.BRIGHT_JADE if have >= need else UiKit.RED)
		if alch:
			# S44: each slot's role, the herb's nature, and what stands in for what.
			var bits: Array = []
			if i < roles.size(): bits.append(Tx.t("ui.crafts.role_" + str(roles[i])))
			var nat := str(ContentDB.item(str(inp.item)).get("nature", ""))
			if nat in ["hot", "cold"]: bits.append(Tx.t("ui.crafts.nature_" + nat))
			var orig := str(rec.inputs[i].item)
			if orig != str(inp.item): bits.append(Tx.t("ui.crafts.stands_in") % ContentDB.item_name(orig))
			text(Vector2(right.position.x + 90, y + 42), "  ·  ".join(bits), 14, UiKit.PALE_GOLD if orig != str(inp.item) else UiKit.MIST)
			if can_swap and str(ContentDB.item(orig).get("type", "")) == "herb" and not Game.crafting.substitutes_for(ch, sel, orig).is_empty() \
					and (subst.is_empty() or str(subst.get("from", "")) == orig):
				btn(Rect2(right.end.x - 118, y + 4, 94, 40), Tx.t("ui.crafts.swap"), "swap", orig, false, true, "", 16)
		y += 54 if alch else 60
	if alch:
		var clash: Dictionary = Game.crafting.conflict_in(inputs)
		if not clash.is_empty() and (ch.crafting.get("known_conflicts", []) as Array).has(str(clash.id)):
			text(Vector2(right.end.x - 24 - UiKit.text_width(Tx.t("ui.crafts.conflict_warning"), 15), right.position.y + 118 - 6), Tx.t("ui.crafts.conflict_warning"), 15, UiKit.RED)
	if craft in ["cooking", "alchemy", "formations"]:
		btn(Rect2(right.position.x + 24, right.end.y - 140, 56, 50), "−", "count", -1)
		text(Vector2(right.position.x + 84, right.end.y - 104), "×%d" % count, 22, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 70)
		btn(Rect2(right.position.x + 158, right.end.y - 140, 56, 50), "+", "count", 1)
	if craft == "alchemy":
		# The furnace you carry and the fire under it (G1).
		var fu: Dictionary = Game.crafting.furnace_of(ch)
		if fu.get("cracked", false):
			text(Vector2(right.position.x + 232, right.end.y - 122), ContentDB.item_name(str(fu.id)), 17, UiKit.RED)
			text(Vector2(right.position.x + 232, right.end.y - 100), Tx.t("sim.crafting.furnace_cracked") % ContentDB.item_name(str(fu.id)), 15, UiKit.RED)
		elif str(fu.get("id", "")) != "":
			text(Vector2(right.position.x + 232, right.end.y - 122), ContentDB.item_name(str(fu.id)) + ("" if str(fu.get("element", "")) == "" else "  ·  " + Tx.t("ui.crafts.furnace_element") % str(fu.element).capitalize()), 17, UiKit.PALE_GOLD)
			text(Vector2(right.position.x + 232, right.end.y - 100), Tx.t("ui.crafts.furnace_stats") % [int(fu.get("batch", 1)), int(round(float(fu.get("band", 0.0)) * 100)),
				int(round(float(fu.get("filter", 0.0)) * 100)), int(round(float(fu.get("yield", 0.0)) * 100))], 15, UiKit.MIST)
		else:
			text(Vector2(right.position.x + 232, right.end.y - 110), Tx.t("ui.crafts.no_furnace"), 15, UiKit.MIST)
		if not game_on:
			var have: Array = Game.crafting.fires_available(ch)
			if not fire in have: fire = "charcoal"
			var fw := (right.size.x - 48 - 24) / 4.0
			for i in FIRES.size():
				var f: String = FIRES[i]
				var fr := Rect2(right.position.x + 24 + i * (fw + 8), right.end.y - 212, fw, 50)
				btn(fr, Tx.t("ui.crafts.fire_" + f), "fire", f, fire == f, f in have, Tx.t("ui.crafts.fire_" + f + "_locked"), 17)
	var why2 := Game.crafting.recipe_check(ch, sel, count, craft)
	if game_on: _draw_minigame(Rect2(right.position.x + 24, right.end.y - 210, right.size.x - 48, 60))
	if craft == "talisman" and trace_on:
		_draw_trace(right)
		return
	var label = {"cooking": Tx.t("ui.crafts.cook"), "alchemy": Tx.t("ui.crafts.refine"), "smithing": Tx.t("ui.crafts.forge"), "formations": Tx.t("ui.crafts.etch"),
		"talisman": Tx.t("ui.crafts.write"), "star_charting": Tx.t("ui.crafts.chart"), "shipwright": Tx.t("ui.crafts.build")}[craft]
	btn(Rect2(right.end.x - 244, right.end.y - 76, 220, 58), Tx.t("ui.crafts.strike") if game_on else label, "strike" if game_on else "craft", null, true, why2 == "" or game_on, why2)
	if craft == "alchemy" and Unlocks.is_unlocked(ch.id, "auto_refine") and not game_on:
		btn(Rect2(right.end.x - 474, right.end.y - 76, 220, 58), Tx.t("ui.crafts.queue_batch"), "queue", null, false, why2 == "", why2)

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
	list("gear", list_r.grow(-8), gear.size(), 62, func(i: int, rr: Rect2):
		var g: Dictionary = gear[i]
		var inst: Dictionary = g.inst
		var uid := int(inst.get("uid", -1))
		var chosen: bool = uid == pick_uid or uid == to_uid or picked.has(uid)
		var usable: bool = not (forge_mode == "salvage" and (g.worn or inst.get("bound", false) or ch.inventory.locked.has(uid)))
		panel(rr, "minor_panel", "selected" if chosen else ("normal" if usable else "disabled"))
		slot_box(Rect2(rr.position + Vector2(6, 4), Vector2(50, 50)), str(inst.id), 0, str(inst.get("quality", "")))
		var grade := str(ContentDB.item(str(inst.id)).get("grade", "plain"))
		text(rr.position + Vector2(66, 28), fit(_gear_name(inst), 17, rr.size.x - 150), 17, UiKit.grade_color(grade) if usable else UiKit.HOLLOW)
		var sub := (Tx.t("ui.forge.in_furnace_slot") if ContentDB.item(str(inst.id)).has("furnace") else Tx.t("ui.forge.worn")) if g.worn else ""
		if float(inst.get("pity", 0.0)) > 0.0: sub += ("  " if sub != "" else "") + Tx.t("ui.forge.pity") % int(round(float(inst.pity) * 100))
		if ch.inventory.locked.has(uid): sub += ("  " if sub != "" else "") + Tx.t("ui.forge.locked_item")
		text(rr.position + Vector2(66, 50), sub, 14, UiKit.MIST)
		if forge_mode == "salvage" and picked.has(uid): text(rr.position + Vector2(rr.size.x - 34, 38), "✓", 24, UiKit.BRIGHT_JADE)
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
	slot_box(Rect2(r.position + Vector2(24, 24), Vector2(72, 72)), str(inst.id), 0, str(inst.get("quality", "")))
	text(r.position + Vector2(110, 56), _gear_name(inst), 24, UiKit.grade_color(str(ContentDB.item(str(inst.id)).get("grade", "plain"))))
	text(r.position + Vector2(110, 84), str(inst.get("quality", "common")).capitalize(), 16, UiKit.MIST)
	return r.position.y + 120

func _cost_line(r: Rect2, y: float, item_id: String, need: int) -> float:
	var have: int = c().inventory.count(item_id)
	slot_box(Rect2(r.position.x + 24, y, 44, 44), item_id)
	text(Vector2(r.position.x + 80, y + 30), "%s  %d / %d" % [ContentDB.item_name(item_id), have, need], 17, UiKit.BRIGHT_JADE if have >= need else UiKit.RED)
	return y + 50

func _forge_enhance(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty():
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.enhance_help"), 19, UiKit.MIST)
		return
	var y := _piece_header(r, inst)
	if int(inst.get("enhance", 0)) >= 10:
		text(Vector2(r.position.x + 24, y + 20), Tx.t("ui.forge.max"), 19, UiKit.GOLD)
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
	text(Vector2(r.position.x + 24, y + 24), Tx.t("ui.forge.taels") % int(cost.taels), 17, UiKit.BRIGHT_JADE if Game.economy.balance("silver_tael") >= int(cost.taels) else UiKit.RED)
	y += 36
	if risky:
		text(Vector2(r.position.x + 24, y + 24), Tx.t("ui.forge.essence") % [essence, int(round(essence * float(Game.crafting.upkeep("essence_step", 0.025)) * 100))], 17, UiKit.PAPER)
		btn(Rect2(r.end.x - 164, y, 56, 44), "−", "essence", -1)
		btn(Rect2(r.end.x - 84, y, 56, 44), "+", "essence", 1, false, essence < int(Game.crafting.upkeep("essence_max", 4)) and ch.inventory.count("refining_essence") > essence)
	var why: String = Game.crafting.enhance_check(ch, inst, essence)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.enhance"), "do_enhance", null, true, why == "", why)
	# A furnace (S44): each level steadies its heat 1%; a blast costs it durability, mended here.
	if str(ContentDB.item(str(inst.id)).get("slot", "")) == "tool_furnace":
		var dur := int(inst.get("durability", 100))
		text(Vector2(r.position.x + 24, r.end.y - 96), Tx.t("ui.forge.furnace_line") % [dur, int(inst.get("enhance", 0))], 16, UiKit.MIST if dur > 0 else UiKit.RED)
		if dur < 100:
			var mc: Dictionary = Game.crafting.mend_cost(inst)
			var mwhy := "" if ch.inventory.count(str(mc.metal)) >= int(mc.count) else Tx.t("sim.crafting.needs_2") % [int(mc.count), ContentDB.item_name(str(mc.metal))]
			btn(Rect2(r.end.x - 474, r.end.y - 76, 220, 58), Tx.t("ui.forge.mend") % [int(mc.count), ContentDB.item_name(str(mc.metal))], "do_mend", null, false, mwhy == "", mwhy, 18)

func _forge_inherit(ch, r: Rect2) -> void:
	var from := _find(ch, pick_uid)
	var to := _find(ch, to_uid)
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 60)), Tx.t("ui.forge.inherit_help"), 17, UiKit.MIST)
	var y := r.position.y + 90
	for pair in [[Tx.t("ui.forge.from"), from], [Tx.t("ui.forge.to"), to]]:
		text(Vector2(r.position.x + 24, y + 30), str(pair[0]), 18, UiKit.MIST)
		var inst: Dictionary = pair[1]
		if inst.is_empty(): text(Vector2(r.position.x + 120, y + 30), Tx.t("ui.forge.choose_left"), 17, UiKit.HOLLOW)
		else:
			slot_box(Rect2(r.position.x + 110, y, 50, 50), str(inst.id), 0, str(inst.get("quality", "")))
			text(Vector2(r.position.x + 172, y + 32), _gear_name(inst), 18, UiKit.PAPER)
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
		text(Vector2(r.position.x + 24, y + 26), Tx.t("ui.forge.inherit_preview") % [moved, stones], 19, UiKit.PAPER)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.inherit"), "do_inherit", null, true, why == "", why)
	btn(Rect2(r.position.x + 24, r.end.y - 76, 160, 58), Tx.t("ui.forge.clear"), "clear_pick")

func _forge_salvage(ch, r: Rect2) -> void:
	var pv: Dictionary = Game.crafting.salvage_preview(ch, picked.keys())
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 60)), Tx.t("ui.forge.salvage_help"), 17, UiKit.MIST)
	var y := r.position.y + 96
	text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.salvage_count") % pv.items.size(), 19, UiKit.PAPER)
	y += 16
	for item_id in pv.returns:
		slot_box(Rect2(r.position.x + 24, y, 44, 44), str(item_id), int(pv.returns[item_id]))
		text(Vector2(r.position.x + 80, y + 30), "%s ×%d" % [ContentDB.item_name(str(item_id)), int(pv.returns[item_id])], 17, UiKit.BRIGHT_JADE)
		y += 50
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.salvage"), "do_salvage", null, true, not pv.items.is_empty(), Tx.t("ui.forge.choose_pieces"))

func _forge_reroll(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty():
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.reroll_help"), 19, UiKit.MIST)
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
	var cost: Dictionary = Game.crafting.reroll_cost(inst)
	y = _cost_line(r, y + 10, "refining_essence", int(cost.essence))
	text(Vector2(r.position.x + 24, y + 24), Tx.t("ui.forge.taels") % int(cost.taels) + (("  " + Tx.t("ui.forge.lock_doubles")) if lock >= 0 else ""), 17,
		UiKit.BRIGHT_JADE if Game.economy.balance("silver_tael") >= int(cost.taels) else UiKit.RED)
	var why2: String = Game.crafting.reroll_check(ch, inst)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.reroll"), "do_reroll", null, true, why2 == "", why2)

## S47 natal treasure: flag one weapon, feed it ore, and re-forge it when it breaks or reaches its band's cap.
func _forge_natal(ch, r: Rect2) -> void:
	var inst := _find(ch, pick_uid)
	if inst.is_empty() or str(ContentDB.item(str(inst.id)).get("slot", "")) != "weapon":
		para(Rect2(r.position + Vector2(24, 30), r.size - Vector2(48, 60)), Tx.t("ui.forge.natal_help"), 19, UiKit.MIST)
		return
	var y := _piece_header(r, inst)
	if not inst.get("natal", false):
		para(Rect2(r.position.x + 24, y, r.size.x - 48, 120), Tx.t("ui.forge.natal_help"), 17, UiKit.MIST)
		btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.make_natal"), "natal_flag", null, true, Unlocks.is_unlocked(ch.id, "natal"), Unlocks.locked_text("natal"))
		return
	var lv := int(inst.get("natal_level", 0))
	var xp := float(inst.get("natal_xp", 0.0))
	var steps: Array = ContentDB.stat_const("natal.xp_levels", [50])
	var nxt := float(steps[mini(lv, steps.size() - 1)])
	bar(Rect2(r.position.x + 24, y, r.size.x - 48, 24), 1.0 if lv >= 10 else xp / maxf(1.0, nxt), UiKit.GOLD,
		Tx.t("ui.forge.natal_level") % [lv, int(xp), int(nxt)] if lv < 10 else Tx.t("ui.forge.natal_full"))
	y += 40
	text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_ilv") % [int(inst.get("ilv_eff", inst.get("ilv", 1))), Game.inventory.natal_cap(inst)], 17, UiKit.PAPER)
	y += 26
	var demand: float = Game.combat.natal_demand(inst)
	var spirit: float = StatRules.attribute(ch, "spirit")
	text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_demand") % [int(demand), int(spirit)], 17, UiKit.BRIGHT_JADE if spirit >= demand else UiKit.RED)
	y += 26
	if inst.get("broken", false):
		text(Vector2(r.position.x + 24, y), Tx.t("ui.forge.natal_broken"), 18, UiKit.RED)
		y += 26
	# Feed: the best ore in the bag, one or five at a time.
	var ore := ""
	for it in ch.inventory.bag:
		if it == null or str(ContentDB.item(str(it.id)).get("type", "")) != "ore" or str(it.id) == "spirit_stone_shard": continue
		if ore == "" or StatRules.grade_index(str(ContentDB.item(str(it.id)).grade)) > StatRules.grade_index(str(ContentDB.item(ore).grade)): ore = str(it.id)
	if ore != "":
		slot_box(Rect2(r.position.x + 24, y + 6, 44, 44), ore, ch.inventory.count(ore))
		btn(Rect2(r.position.x + 80, y + 6, 130, 44), Tx.t("ui.forge.feed") % 1, "natal_feed", [ore, 1], false, not inst.get("broken", false), "", 16)
		btn(Rect2(r.position.x + 220, y + 6, 130, 44), Tx.t("ui.forge.feed") % 5, "natal_feed", [ore, 5], false, not inst.get("broken", false) and ch.inventory.count(ore) >= 5, "", 16)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.forge.reforge"), "natal_reforge", null, true)

# ------------------------------------------------------------------ talisman tracing (S47)
func _template(r: Rect2) -> PackedVector2Array:
	var out := PackedVector2Array()
	var tal := ContentDB.entry("talismans", str(ContentDB.entry("recipes", sel).outputs[0].item))
	for p in tal.get("strokes", []): out.append(r.position + Vector2(float(p[0]), float(p[1])) * r.size)
	return out

func _draw_trace(right: Rect2) -> void:
	var side := minf(right.size.x - 48, right.size.y - 150)
	trace_rect = Rect2(right.position.x + (right.size.x - side) / 2.0, right.position.y + 110, side, side)
	draw_rect(trace_rect, Color("efe3c2"))
	draw_rect(trace_rect, Color("8a6a3a"), false, 3.0)
	var tpl := _template(trace_rect)
	if tpl.size() > 1:
		draw_polyline(tpl, Color(0.75, 0.2, 0.18, 0.35), 14.0)
		draw_circle(tpl[0], 9, Color(0.75, 0.2, 0.18, 0.7))
	if trace_pts.size() > 1: draw_polyline(PackedVector2Array(trace_pts), Color("1c1a18"), 7.0)
	text(Vector2(right.position.x + 24, right.end.y - 24), Tx.t("ui.crafts.trace_hint"), 17, UiKit.MIST)
	btn(Rect2(right.end.x - 164, right.position.y + 40, 140, 46), Tx.t("ui.crafts.stop_tracing"), "trace_cancel", null, false, true, "", 16)

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
		flash(Tx.t("ui.crafts.quality_made") % [str(r.quality).replace("_", " ").capitalize(), int(r.count)])
	elif str(r.get("text", "")) != "": flash(str(r.text))

func _gui_input(event: InputEvent) -> void:
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
	var y := right.position.y + 120
	text(Vector2(right.position.x + 24, y), Tx.t("ui.crafts.auto_refine_batches"), 19, UiKit.GOLD)
	for b in q:
		y += 30
		var left := int(float(b.done_utc) - Clock.now_utc())
		text(Vector2(right.position.x + 24, y), "%s ×%d · %s" % [ContentDB.item_name(str(ContentDB.entry("recipes", str(b.recipe)).outputs[0].item)), int(b.count), "ready" if left <= 0 else "%dm" % (left / 60 + 1)], 17)
	btn(Rect2(right.position.x + 24, y + 20, 200, 50), Tx.t("ui.crafts.collect"), "collect", null, true)

# ------------------------------------------------------------------ S44 experiments, Deduce and the guild
func _experiment(ch, r: Rect2) -> void:
	para(Rect2(r.position + Vector2(24, 20), Vector2(r.size.x - 48, 70)), Tx.t("ui.crafts.experiment_help"), 17, UiKit.MIST)
	var herbs: Array = []
	for it in ContentDB.all("items"):
		if str(it.get("type", "")) == "herb" and ch.inventory.count(str(it.id)) > 0: herbs.append(str(it.id))
	var cols := 5
	for i in herbs.size():
		var h: String = herbs[i]
		var hr := Rect2(r.position.x + 24 + (i % cols) * 108, r.position.y + 96 + (i / cols) * 96, 96, 86)
		panel(hr, "minor_panel", "selected" if exp_herbs.has(h) else "normal")
		slot_box(Rect2(hr.position + Vector2(23, 6), Vector2(50, 50)), h, ch.inventory.count(h))
		text(hr.position + Vector2(0, 76), fit(ContentDB.item_name(h), 13, 94), 13, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 96)
		region(hr, "exp_herb", h)
	var y := r.position.y + 96 + ceili(herbs.size() / float(cols)) * 96 + 10
	if herbs.is_empty(): para(Rect2(r.position.x + 24, r.position.y + 100, r.size.x - 48, 60), Tx.t("ui.crafts.experiment_no_herbs"), 17, UiKit.HOLLOW)
	var why := ""
	if exp_herbs.size() < 2: why = Tx.t("sim.crafting.experiment_count")
	else:
		var seen: Dictionary = Game.crafting.experiment_logged(CraftingAuthority.experiment_key(exp_herbs))
		if not seen.is_empty(): why = Tx.t("sim.crafting.experiment_tried") % Game.crafting.experiment_result_text(seen)
	if why != "" and exp_herbs.size() >= 2: text(Vector2(r.position.x + 24, y + 20), why, 16, UiKit.GOLD)
	text(Vector2(r.position.x + 24, r.end.y - 96), Tx.t("ui.crafts.experiment_log") % Game.account.experiments.size(), 15, UiKit.MIST)
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.crafts.experiment_go"), "experiment", null, true, why == "", why)

func _deduce(ch, r: Rect2) -> void:
	var rec := ContentDB.entry("recipes", sel)
	var out := str(rec.outputs[0].item)
	slot_box(Rect2(r.position + Vector2(24, 24), Vector2(72, 72)), out)
	text(r.position + Vector2(110, 56), ContentDB.item_name(out), 24, UiKit.grade_color(str(rec.get("grade", "plain"))))
	var held: int = Game.crafting.pages_held(ch, sel)
	text(r.position + Vector2(110, 84), Tx.t("ui.crafts.pages_held") % [held, int(rec.get("fragments", 1))], 16, UiKit.MIST)
	para(Rect2(r.position + Vector2(24, 116), Vector2(r.size.x - 48, 90)), Tx.t("ui.crafts.deduce_help"), 17, UiKit.MIST)
	var y := r.position.y + 210
	for inp in rec.inputs:
		y = _cost_line(r, y, str(inp.item), int(inp.count))
	var chance: float = Game.crafting.deduce_chance(ch, sel)
	text(Vector2(r.position.x + 24, y + 26), Tx.t("ui.crafts.deduce_chance") % int(round(chance * 100)), 19, UiKit.PAPER)
	var why := ""
	for inp in rec.inputs:
		if ch.inventory.count(str(inp.item)) < int(inp.count): why = Tx.t("sim.crafting.missing") % ContentDB.item_name(str(inp.item))
	btn(Rect2(r.end.x - 244, r.end.y - 76, 220, 58), Tx.t("ui.crafts.deduce"), "deduce", null, true, why == "", why)

func _guild(ch, content_r: Rect2) -> void:
	var left := Rect2(content_r.position.x, content_r.position.y, 520, content_r.size.y)
	var right := Rect2(left.end.x + 20, left.position.y, content_r.end.x - left.end.x - 20, left.size.y)
	panel(left)
	panel(right)
	var rank: String = Game.crafting.guild_rank(ch, "alchemy")
	text(left.position + Vector2(24, 44), Tx.t("ui.guild.title"), 24, UiKit.PAPER)
	text(left.position + Vector2(24, 72), Tx.t("ui.guild.rank_" + rank) if rank != "" else Tx.t("ui.guild.no_rank"), 17, UiKit.GOLD if rank != "" else UiKit.MIST)
	var y := left.position.y + 96
	for rk in Game.crafting.guild_def("alchemy").get("ranks", []):
		var card := Rect2(left.position.x + 16, y, left.size.x - 32, 156)
		var passed: bool = _rank_at_least(rank, str(rk.id))
		panel(card, "minor_panel", "selected" if passed else "normal")
		text(card.position + Vector2(16, 30), Tx.t("ui.guild.rank_" + str(rk.id)), 20, UiKit.PALE_GOLD if passed else UiKit.PAPER)
		para(Rect2(card.position.x + 16, card.position.y + 40, card.size.x - 32, 40), Tx.t("ui.guild.exam_task") % [ContentDB.item_name(str(ContentDB.entry("recipes", str(rk.recipe)).outputs[0].item)),
			int(rk.count), str(rk.quality).capitalize(), int(float(rk.time_s) / 60.0)], 15, UiKit.MIST, 2)
		var rew := Tx.t("ui.guild.reward_title") % Tx.t("ui.guild.rank_" + str(rk.id))
		for e in rk.get("rewards", []):
			if str(e.get("kind", "")) == "learn_recipe": rew += " · " + ContentDB.name_of("recipes", str(e.recipe))
		text(card.position + Vector2(16, 104), fit(rew, 15, card.size.x - 32), 15, UiKit.PALE_GOLD)
		var nxt: Dictionary = Game.crafting.next_guild_rank(ch, "alchemy")
		var ex: Dictionary = ch.crafting.get("guild_exam", {})
		if passed:
			text(card.position + Vector2(16, 138), Tx.t("ui.guild.passed"), 16, UiKit.BRIGHT_JADE)
		elif not ex.is_empty() and str(ex.rank) == str(rk.id):
			var left_s: float = Game.crafting.exam_left(ch)
			text(card.position + Vector2(16, 138), Tx.t("ui.guild.exam_running") % [int(ex.made), int(rk.count), int(left_s / 60.0), int(left_s) % 60], 16, UiKit.GOLD)
		elif str(nxt.get("id", "")) == str(rk.id):
			btn(Rect2(card.end.x - 186, card.end.y - 54, 170, 44), Tx.t("ui.guild.start_exam"), "exam", str(rk.id), true, ex.is_empty(), Tx.t("sim.crafting.exam_running"), 17)
		y += 166
	# The commission board.
	text(right.position + Vector2(24, 44), Tx.t("ui.guild.commissions"), 22, UiKit.PAPER)
	if rank == "":
		para(Rect2(right.position + Vector2(24, 64), Vector2(right.size.x - 48, 80)), Tx.t("ui.guild.commissions_locked"), 17, UiKit.MIST)
		return
	var paid: int = Game.crafting.commission_paid_today(ch)
	var cap: int = Game.crafting.commission_cap(ch)
	text(right.position + Vector2(24, 72), Tx.t("ui.guild.cap_line") % [paid, cap], 15, UiKit.MIST)
	var oy := right.position.y + 90
	for o in Game.crafting.commissions(ch):
		var card2 := Rect2(right.position.x + 16, oy, right.size.x - 32, 110)
		panel(card2, "minor_panel", "disabled" if o.get("done", false) else ("selected" if o.get("accepted", false) else "normal"))
		slot_box(Rect2(card2.position + Vector2(10, 10), Vector2(50, 50)), str(o.item))
		text(card2.position + Vector2(72, 30), "%s ×%d" % [ContentDB.item_name(str(o.item)), int(o.count)], 18, UiKit.PAPER)
		text(card2.position + Vector2(72, 54), Tx.t("ui.guild.pay") % int(o.pay), 15, UiKit.GOLD)
		if o.get("done", false):
			text(card2.position + Vector2(72, 92), Tx.t("ui.guild.delivered"), 15, UiKit.BRIGHT_JADE)
		elif not o.get("accepted", false):
			btn(Rect2(card2.end.x - 150, card2.end.y - 50, 138, 42), Tx.t("ui.guild.accept"), "c_accept", str(o.id), false, true, "", 16)
		else:
			var have := 0
			for s2 in ch.inventory.bag:
				if s2 != null and str(s2.id) == str(o.item): have += int(s2.count)
			var ok2 := have >= int(o.count)
			btn(Rect2(card2.end.x - 300, card2.end.y - 50, 138, 42), Tx.t("ui.guild.deliver_taels"), "c_taels", str(o.id), true, ok2, Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item)), 15)
			btn(Rect2(card2.end.x - 150, card2.end.y - 50, 138, 42), Tx.t("ui.guild.deliver_contribution"), "c_contrib", str(o.id), false, ok2, Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item)), 15)
		oy += 120

func _rank_at_least(have: String, want: String) -> bool:
	var ids: Array = []
	for rk in Game.crafting.guild_def("alchemy").get("ranks", []): ids.append(str(rk.id))
	return have != "" and ids.find(have) >= ids.find(want)

func _draw_minigame(r: Rect2) -> void:
	# The alchemy strikes are the furnace's stages (S15): Extraction, Fusion, Condensation.
	if str(tabs[tab].id) == "alchemy":
		var stage := mini(scores.size() + 1, 3)
		var label := Tx.t("ui.crafts.stage_%d" % stage)
		var shift: float = Game.crafting.nature_shift(sel, subst)
		if stage == 1 and absf(shift) > 0.001: label += "  ·  " + Tx.t("ui.crafts.band_high" if shift > 0.0 else "ui.crafts.band_low")
		text(Vector2(r.position.x, r.position.y - 12), label, 16, UiKit.PALE_GOLD)
	draw_rect(r, Color(0.05, 0.08, 0.09))
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
			sel = str(data)
			count = 1
			game_on = false
			subst = {}
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
			var re := submit({"type": "take_guild_exam", "craft": "alchemy", "rank": str(data)})
			if not re.get("ok", false) and str(re.get("text", "")) != "": flash(str(re.text))
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
			if DIRECT.has(craft):
				var r := submit({"type": DIRECT[craft], "recipe": sel, "count": count if craft in ["cooking", "formations"] else 1})
				if r.get("ok", false):
					Audio.play("cook" if craft == "cooking" else "forge", "UI")
					flash({"cooking": Tx.t("ui.crafts.cooked"), "formations": Tx.t("ui.crafts.etched"), "star_charting": Tx.t("ui.crafts.charted"),
						"shipwright": Tx.t("ui.crafts.built")}[craft] % int(r.count))
			else:
				game_on = true
				scores = []
				needle = 0.0
				needle_dir = 1.0
				band = Vector2(0.4 + Rng.stream(c().id, "minigame").randf() * 0.2, 0.0)
				var width := 0.16 * _band_mult(craft)
				# S44: hot herbs drive the Extraction band up the bar, cold herbs draw it down.
				if craft == "alchemy": band.x = clampf(band.x + Game.crafting.nature_shift(sel, subst), 0.04, 0.96 - width)
				band.y = band.x + width
		"strike":
			# Crafting scores the strike (craft_step_result); the page only reports where it landed.
			var mid := (band.x + band.y) * 0.5
			# The band drawn is the band scored: the authority widens its tolerance by the same fire.
			var st := submit({"type": "craft_step", "recipe": sel, "craft": "alchemy" if craft == "alchemy" else "smithing", "offset": needle - mid,
				"fire": fire})
			scores.append(float(st.get("score", 0.0)))
			Audio.play("forge" if craft == "smithing" else "alchemy", "UI")
			if scores.size() >= (Game.crafting.steps_for(sel) if craft == "alchemy" else int(ContentDB.curve("craft_step.steps", 3))):
				game_on = false
				var r2 := submit({"type": "refine" if craft == "alchemy" else "forge", "recipe": sel, "count": count, "fire": fire, "substitute": subst})
				if r2.get("ok", false):
					var made := Tx.t("ui.crafts.quality_made") % [str(r2.quality).replace("_", " ").capitalize(), int(r2.count)]
					if int(r2.get("marks", 0)) > 0: made += " · " + Tx.t("ui.crafts.marks") % int(r2.marks)
					flash(made)
				elif str(r2.get("text", "")) != "": flash(str(r2.text))
			else:
				band.x = 0.25 + Rng.stream(c().id, "minigame").randf() * 0.5
				band.y = band.x + 0.14 * _band_mult(craft)
		"queue":
			if submit({"type": "queue_auto_refine", "recipe": sel, "count": count}).get("ok", false):
				flash(Tx.t("ui.crafts.batch_queued"))
		"collect":
			submit({"type": "collect_auto_refine"})
		"_tab":
			sel = ""
			game_on = false
			trace_on = false
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
				flash(Tx.t("ui.forge.salvaged") % (r5.items as Array).size())
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

func _band_mult(craft: String) -> float:
	return Game.crafting.band_mult(c(), fire) if craft == "alchemy" else 1.0
