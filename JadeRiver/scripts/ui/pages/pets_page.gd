extends Page
## Spirit animals (S22): roster, active animal, role, bond and feeding.

var sel := ""

func _init() -> void:
	title = "Spirit Animals"

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position.x, content.position.y, 420, content.size.y)
	panel(left)
	if ch.pets.is_empty():
		para(Rect2(left.position + Vector2(20, 20), left.size - Vector2(40, 40)), "No spirit animals yet. Hermit Yao in the Reed Marsh looks after orphaned young ones.", 19, UiKit.MIST)
	# Open on the active animal (or the first one) instead of an empty panel.
	if not ch.pets.is_empty() and not ch.pets.any(func(p): return str(p.uid) == sel):
		sel = ch.active_pet if ch.active_pet != "" else str(ch.pets[0].uid)
	list("pets", left.grow(-10), ch.pets.size(), 70, func(i: int, rr: Rect2):
		var p: Dictionary = ch.pets[i]
		panel(rr, "minor_panel", "selected" if sel == str(p.uid) else "normal")
		creature_at(Rect2(rr.position + Vector2(6, 4), Vector2(62, 60)), _art(p))
		text(rr.position + Vector2(76, 30), str(p.name) + ("  ◆" if ch.active_pet == str(p.uid) else ""), 20)
		text(rr.position + Vector2(76, 54), "%s · Lv %d · %s" % [ContentDB.name_of("pets", str(p.species)), int(p.level), str(p.role).capitalize()], 15, UiKit.MIST)
		region(rr, "sel", str(p.uid))
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	var pet := {}
	for p in ch.pets:
		if str(p.uid) == sel: pet = p
	if pet.is_empty(): return
	var sp := ContentDB.entry("pets", str(pet.species))
	var px := right.position.x + 24
	var colw := right.size.x - 290   # left column; the right column holds the portrait and growth
	var stage := Rect2(right.end.x - 230, right.position.y + 18, 206, 148)
	draw_style_box(UiKit.style("slot"), stage)
	creature_at(stage.grow_individual(-8, -8, -8, -14), _art(pet), "walk" if ch.active_pet == sel else "idle")
	heading(right.position + Vector2(24, 44), str(pet.name), colw)
	var stage_name := str(Game.pets.stage_def(str(pet.get("stage", "hatchling"))).get("name", "Hatchling"))
	var branch := str(pet.get("branch", ""))
	text(right.position + Vector2(24, 80), fit("%s · %s · %s" % [str(sp.get("name", "")), str(sp.get("element", "")).capitalize(), branch if branch != "" else stage_name], 18, colw), 18, UiKit.MIST)
	bar(Rect2(px, right.position.y + 96, colw, 28), float(pet.get("bond", 0.0)) / 10.0, UiKit.RED, "Bond %.1f / 10" % float(pet.get("bond", 0.0)))
	var need := float(ContentDB.curve("pet_xp.base", 20)) * pow(int(pet.level), float(ContentDB.curve("pet_xp.per_level_pow", 1.5)))
	bar(Rect2(px, right.position.y + 130, colw, 24), float(pet.get("xp", 0.0)) / need, UiKit.GOLD, "Level %d · %d / %d" % [int(pet.level), int(pet.get("xp", 0.0)), int(need)])
	text(right.position + Vector2(24, 180), fit("Skills: " + ", ".join(sp.get("skills", [])), 16, colw), 16)
	text(right.position + Vector2(24, 204), fit("Favourite foods: " + ", ".join((sp.get("favourite_foods", []) as Array).map(func(f): return ContentDB.item_name(str(f)))), 16, colw), 16, UiKit.MIST)
	var shown: Array = Game.pets.revealed_traits(pet).map(func(t): return ContentDB.name_of("pet_traits", str(t)))
	while shown.size() < int(ContentDB.config("pet_growth").get("traits_per_pet", 3)): shown.append("?")
	text(right.position + Vector2(24, 228), fit("Traits: " + " · ".join(shown), 16, colw), 16, UiKit.PALE_GOLD)
	var y := right.position.y + 248
	var roles := ["combat", "gatherer", "cultivation"]
	var bw := (colw - 16) / 3.0
	for role in roles:
		btn(Rect2(px + roles.find(role) * (bw + 8), y, bw, 46), role.capitalize(), "role", role, str(pet.role) == role, true, "", 17)
	y += 60
	btn(Rect2(px, y, 220, 50), "Set active" if ch.active_pet != sel else "Rest", "active", sel, ch.active_pet != sel)
	var res := Game.pets.resonance(ch) if ch.active_pet == sel else 0.0
	if res > 0.0: text(Vector2(px + 236, y + 32), "Resonance +%d%%" % int(round(res * 100.0)), 17, UiKit.BRIGHT_JADE)
	_growth(ch, pet, Rect2(stage.position.x, stage.end.y + 14, stage.size.x, right.end.y - stage.end.y - 28))
	var foods: Array = (sp.get("favourite_foods", []) as Array).filter(func(f): return ch.inventory.count(str(f)) > 0)
	for f in ["roast_fish", "ember_pepper_broth"]:
		if ch.inventory.count(f) > 0 and not foods.has(f): foods.append(f)
	var x := px
	for f in foods:
		if x + 60 > px + colw: break
		slot_box(Rect2(x, y + 84, 60, 60), str(f), ch.inventory.count(str(f)), "", "feed", str(f))
		x += 68
	if not foods.is_empty(): text(Vector2(px, y + 76), "Tap food to feed", 16, UiKit.MIST)

## Next stage: each gate ticked or not, then Evolve (or the two branches at Adult).
func _growth(ch, pet: Dictionary, r: Rect2) -> void:
	var nx: Dictionary = Game.pets.next_stage(pet)
	if nx.is_empty():
		para(r, "Fully grown for this land.", 16, UiKit.MIST)
		return
	text(r.position + Vector2(0, 18), "Next: %s" % str(nx.get("name", "")), 18, UiKit.GOLD)
	var y := r.position.y + 30
	for g in Game.pets.evolve_gates(ch, pet):
		text(Vector2(r.position.x, y + 18), ("✓ " if g.ok else "· ") + str(g.text), 16, UiKit.BRIGHT_JADE if g.ok else UiKit.MIST)
		y += 24
	var ready: bool = Game.pets.can_evolve(ch, pet)
	y += 8
	if nx.get("branch", false):
		for b in ContentDB.entry("pets", str(pet.species)).get("branches", []):
			btn(Rect2(r.position.x, y, r.size.x, 42), str(b), "evolve", str(b), ready, ready, "Not ready yet", 17)
			y += 48
	else:
		btn(Rect2(r.position.x, y, r.size.x, 46), "Evolve", "evolve", "", true, ready, "Not ready yet")

func _art(p: Dictionary) -> String:
	return str(ContentDB.entry("pets", str(p.species)).get("art", p.species))

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"role": submit({"type": "set_pet_role", "pet": sel, "role": str(data)})
		"active": submit({"type": "set_active_pet", "pet": "" if c().active_pet == sel else sel})
		"feed": submit({"type": "feed_pet", "pet": sel, "item": str(data)})
		"evolve": submit({"type": "evolve_pet", "pet": sel, "branch": str(data)})
