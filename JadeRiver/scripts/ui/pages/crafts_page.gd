extends Page
## Crafts (S15, S16): cooking, alchemy and the forge share one recipe book.
## Alchemy and forging play a short timing mini-game (three strikes into the
## glowing band); its scores go to the authority, which rolls the quality.

var CRAFTS := [["cooking", Tx.t("ui.crafts.cooking")], ["alchemy", Tx.t("ui.crafts.alchemy")], ["smithing", Tx.t("ui.crafts.forge")], ["formations", Tx.t("ui.crafts.arrays")],
	["star_charting", Tx.t("ui.crafts.charts")], ["shipwright", Tx.t("ui.crafts.vessels")]]
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
## The fires under a furnace (gap report G1), in the order the selector shows them.
const FIRES := ["charcoal", "earth_fire", "beast_fire", "heavenly_flame"]

func _init() -> void:
	title = Tx.t("ui.crafts.crafts")

func setup() -> void:
	var ch = c()
	tabs = []
	for cr in CRAFTS:
		tabs.append({"id": cr[0], "label": cr[1], "locked": "" if Unlocks.is_unlocked(ch.id, cr[0]) else Unlocks.locked_text(cr[0])})
	var want = {"cooking": 0, "alchemy": 1, "forge": 2, "arrays": 3, "charts": 4, "vessels": 5}.get(page_id, -1)
	# The Starsea tabs stay hidden until Sage 3 opens them, so the valley page is unchanged.
	if not Unlocks.is_unlocked(ch.id, "star_charting"):
		tabs = tabs.slice(0, 4)
		if want >= 4: want = -1
	# A page opened for one recipe (a quest link, or a preview: --open-page=alchemy:healing_pill).
	var pick := str(args.get("tab", ""))
	if ContentDB.has_entry("recipes", pick): sel = pick
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
	var list_r := Rect2(content.position.x, content.position.y, 420, content.size.y)
	panel(list_r)
	var recipes := recipes_for(ch, craft)
	var prof: Dictionary = ch.professions.get(craft, {"rank": "apprentice", "xp": 0})
	text(Vector2(list_r.position.x + 16, list_r.end.y - 14), "%s · %s" % [str(prof.rank).capitalize(), UiKit.fmt(float(prof.xp))], 16, UiKit.MIST)
	list("rec", Rect2(list_r.position + Vector2(8, 8), list_r.size - Vector2(16, 40)), recipes.size(), 62, func(i: int, rr: Rect2):
		var r: Dictionary = recipes[i]
		var out := str(r.outputs[0].item)
		var why := Game.crafting.recipe_check(ch, str(r.id), 1, craft)
		panel(rr, "minor_panel", "selected" if sel == str(r.id) else "normal")
		slot_box(Rect2(rr.position + Vector2(6, 4), Vector2(50, 50)), out)
		text(rr.position + Vector2(66, 36), ContentDB.item_name(out), 18, UiKit.PAPER if why == "" else UiKit.MIST)
		region(rr, "sel", str(r.id))
	)
	var right := Rect2(list_r.end.x + 20, content.position.y, content.end.x - list_r.end.x - 20, content.size.y)
	panel(right)
	if sel == "" or ContentDB.entry("recipes", sel).is_empty() or str(ContentDB.entry("recipes", sel).craft) != craft:
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), (Tx.t("ui.crafts.choose_a_recipe_stand_near") % {"cooking": Tx.t("ui.crafts.cooking_pot"), "alchemy": "furnace", "smithing": "forge",
			"star_charting": Tx.t("ui.crafts.chart_table"), "shipwright": Tx.t("ui.crafts.slipway")}[craft]) if craft != "formations" else Tx.t("ui.crafts.choose_a_plate_to_etch"), 19, UiKit.MIST)
		if craft == "alchemy": _auto(ch, right)
		return
	var rec := ContentDB.entry("recipes", sel)
	var out2 := str(rec.outputs[0].item)
	slot_box(Rect2(right.position + Vector2(24, 24), Vector2(72, 72)), out2, int(rec.outputs[0].count))
	text(right.position + Vector2(110, 56), ContentDB.item_name(out2), 24, UiKit.grade_color(str(rec.get("grade", "plain"))))
	text(right.position + Vector2(110, 84), fit(str(ContentDB.item(out2).get("desc", "")), 16, right.size.x - 130), 16, UiKit.MIST)
	var y := right.position.y + 120
	for inp in rec.inputs:
		var have = ch.inventory.count(str(inp.item))
		var need := int(inp.count) * count
		slot_box(Rect2(right.position.x + 24, y, 52, 52), str(inp.item))
		text(Vector2(right.position.x + 90, y + 34), "%s  %d / %d" % [ContentDB.item_name(str(inp.item)), have, need], 18, UiKit.BRIGHT_JADE if have >= need else UiKit.RED)
		y += 60
	if craft in ["cooking", "alchemy", "formations"]:
		btn(Rect2(right.position.x + 24, right.end.y - 140, 56, 50), "−", "count", -1)
		text(Vector2(right.position.x + 84, right.end.y - 104), "×%d" % count, 22, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 70)
		btn(Rect2(right.position.x + 158, right.end.y - 140, 56, 50), "+", "count", 1)
	if craft == "alchemy":
		# The furnace you carry and the fire under it (G1).
		var fu: Dictionary = Game.crafting.furnace_of(ch)
		if str(fu.get("id", "")) != "":
			text(Vector2(right.position.x + 232, right.end.y - 122), ContentDB.item_name(str(fu.id)), 17, UiKit.PALE_GOLD)
			text(Vector2(right.position.x + 232, right.end.y - 100), Tx.t("ui.crafts.furnace_stats") % [int(fu.get("batch", 1)), int(round(float(fu.get("band", 0.0)) * 100)),
				int(round(float(fu.get("yield", 0.0)) * 100))], 15, UiKit.MIST)
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
	var label = {"cooking": Tx.t("ui.crafts.cook"), "alchemy": Tx.t("ui.crafts.refine"), "smithing": Tx.t("ui.crafts.forge"), "formations": Tx.t("ui.crafts.etch"),
		"star_charting": Tx.t("ui.crafts.chart"), "shipwright": Tx.t("ui.crafts.build")}[craft]
	btn(Rect2(right.end.x - 244, right.end.y - 76, 220, 58), Tx.t("ui.crafts.strike") if game_on else label, "strike" if game_on else "craft", null, true, why2 == "" or game_on, why2)
	if craft == "alchemy" and Unlocks.is_unlocked(ch.id, "auto_refine") and not game_on:
		btn(Rect2(right.end.x - 474, right.end.y - 76, 220, 58), Tx.t("ui.crafts.queue_batch"), "queue", null, false, why2 == "", why2)

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

func _draw_minigame(r: Rect2) -> void:
	draw_rect(r, Color(0.05, 0.08, 0.09))
	draw_rect(Rect2(r.position.x + r.size.x * band.x, r.position.y, r.size.x * (band.y - band.x), r.size.y), Color(UiKit.GOLD, 0.55))
	var nx := r.position.x + r.size.x * needle
	draw_rect(Rect2(nx - 3, r.position.y - 6, 6, r.size.y + 12), UiKit.PAPER)
	for i in scores.size():
		draw_circle(Vector2(r.position.x + 12 + i * 22, r.end.y + 16), 7, UiKit.JADE if float(scores[i]) > 0.6 else UiKit.RED)

func on_event(name: String, p: Dictionary) -> void:
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
		"count": count = clampi(count + int(data), 1, int(Game.crafting.furnace_of(ch).get("batch", 10)) if craft == "alchemy" else 10)
		"fire": fire = str(data)
		"craft":
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
				band.y = band.x + 0.16 * _band_mult(craft)
		"strike":
			# Crafting scores the strike (craft_step_result); the page only reports where it landed.
			var mid := (band.x + band.y) * 0.5
			# The band drawn is the band scored: the authority widens its tolerance by the same fire.
			var st := submit({"type": "craft_step", "recipe": sel, "craft": "alchemy" if craft == "alchemy" else "smithing", "offset": needle - mid,
				"fire": fire})
			scores.append(float(st.get("score", 0.0)))
			Audio.play("forge" if craft == "smithing" else "alchemy", "UI")
			if scores.size() >= int(ContentDB.curve("craft_step.steps", 3)):
				game_on = false
				var r2 := submit({"type": "refine" if craft == "alchemy" else "forge", "recipe": sel, "count": count, "fire": fire})
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

func _band_mult(craft: String) -> float:
	return Game.crafting.band_mult(c(), fire) if craft == "alchemy" else 1.0
