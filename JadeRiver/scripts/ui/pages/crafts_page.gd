extends Page
## Crafts (S15, S16): cooking, alchemy and the forge share one recipe book.
## Alchemy and forging play a short timing mini-game (three strikes into the
## glowing band); its scores go to the authority, which rolls the quality.

const CRAFTS := [["cooking", "Cooking"], ["alchemy", "Alchemy"], ["smithing", "Forge"], ["formations", "Arrays"]]

var sel := ""
var count := 1
var game_on := false
var needle := 0.0
var needle_dir := 1.0
var scores: Array = []
var band := Vector2(0.45, 0.62)

func _init() -> void:
	title = "Crafts"

func setup() -> void:
	var ch = c()
	tabs = []
	for cr in CRAFTS:
		tabs.append({"id": cr[0], "label": cr[1], "locked": "" if Unlocks.is_unlocked(ch.id, cr[0]) else Unlocks.locked_text(cr[0])})
	var want = {"cooking": 0, "alchemy": 1, "forge": 2, "arrays": 3}.get(page_id, -1)
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
		para(Rect2(right.position + Vector2(24, 30), right.size - Vector2(48, 60)), ("Choose a recipe. Stand near a %s to craft." % {"cooking": "cooking pot", "alchemy": "furnace", "smithing": "forge"}[craft]) if craft != "formations" else "Choose a plate to etch. Array plates are one-use formations you carry.", 19, UiKit.MIST)
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
	if craft != "smithing":
		btn(Rect2(right.position.x + 24, right.end.y - 140, 56, 50), "−", "count", -1)
		text(Vector2(right.position.x + 84, right.end.y - 104), "×%d" % count, 22, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 70)
		btn(Rect2(right.position.x + 158, right.end.y - 140, 56, 50), "+", "count", 1)
	var why2 := Game.crafting.recipe_check(ch, sel, count, craft)
	if game_on: _draw_minigame(Rect2(right.position.x + 24, right.end.y - 210, right.size.x - 48, 60))
	var label = {"cooking": "Cook", "alchemy": "Refine", "smithing": "Forge", "formations": "Etch"}[craft]
	btn(Rect2(right.end.x - 244, right.end.y - 76, 220, 58), "Strike!" if game_on else label, "strike" if game_on else "craft", null, true, why2 == "" or game_on, why2)
	if craft == "alchemy" and Unlocks.is_unlocked(ch.id, "auto_refine") and not game_on:
		btn(Rect2(right.end.x - 474, right.end.y - 76, 220, 58), "Queue batch", "queue", null, false, why2 == "", why2)

func _auto(ch, right: Rect2) -> void:
	var q: Array = ch.crafting.get("auto_queue", [])
	if q.is_empty(): return
	var y := right.position.y + 120
	text(Vector2(right.position.x + 24, y), "Auto-refine batches", 19, UiKit.GOLD)
	for b in q:
		y += 30
		var left := int(float(b.done_utc) - Clock.now_utc())
		text(Vector2(right.position.x + 24, y), "%s ×%d · %s" % [ContentDB.item_name(str(ContentDB.entry("recipes", str(b.recipe)).outputs[0].item)), int(b.count), "ready" if left <= 0 else "%dm" % (left / 60 + 1)], 17)
	btn(Rect2(right.position.x + 24, y + 20, 200, 50), "Collect", "collect", null, true)

func _draw_minigame(r: Rect2) -> void:
	draw_rect(r, Color(0.05, 0.08, 0.09))
	draw_rect(Rect2(r.position.x + r.size.x * band.x, r.position.y, r.size.x * (band.y - band.x), r.size.y), Color(UiKit.GOLD, 0.55))
	var nx := r.position.x + r.size.x * needle
	draw_rect(Rect2(nx - 3, r.position.y - 6, 6, r.size.y + 12), UiKit.PAPER)
	for i in scores.size():
		draw_circle(Vector2(r.position.x + 12 + i * 22, r.end.y + 16), 7, UiKit.JADE if float(scores[i]) > 0.6 else UiKit.RED)

func on_action(id: String, data) -> void:
	var ch = c()
	var craft := str(tabs[tab].id)
	match id:
		"sel":
			sel = str(data)
			count = 1
			game_on = false
		"count": count = clampi(count + int(data), 1, 10)
		"craft":
			if craft in ["cooking", "formations"]:
				var r := submit({"type": "cook" if craft == "cooking" else "inscribe", "recipe": sel, "count": count})
				if r.get("ok", false):
					Audio.play("cook" if craft == "cooking" else "forge", "UI")
					flash(("Cooked %d" if craft == "cooking" else "Etched %d") % int(r.count))
			else:
				game_on = true
				scores = []
				needle = 0.0
				needle_dir = 1.0
				band = Vector2(0.4 + randf() * 0.2, 0.0)
				band.y = band.x + 0.16
		"strike":
			var mid := (band.x + band.y) * 0.5
			scores.append(clampf(1.0 - absf(needle - mid) / 0.3, 0.0, 1.0))
			Audio.play("forge" if craft == "smithing" else "alchemy", "UI")
			if scores.size() >= 3:
				game_on = false
				var r2 := submit({"type": "refine" if craft == "alchemy" else "forge", "recipe": sel, "count": count, "scores": scores})
				if r2.get("ok", false): flash("%s quality · %d made" % [str(r2.quality).capitalize(), int(r2.count)])
			else:
				band.x = 0.25 + randf() * 0.5
				band.y = band.x + 0.14
		"queue":
			if submit({"type": "queue_auto_refine", "recipe": sel, "count": count}).get("ok", false):
				flash("Batch queued.")
		"collect":
			submit({"type": "collect_auto_refine"})
		"_tab":
			sel = ""
			game_on = false
