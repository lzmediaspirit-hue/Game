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
	list("pets", left.grow(-10), ch.pets.size(), 70, func(i: int, rr: Rect2):
		var p: Dictionary = ch.pets[i]
		panel(rr, "minor_panel", "selected" if sel == str(p.uid) else "normal")
		text(rr.position + Vector2(18, 30), str(p.name) + ("  ◆" if ch.active_pet == str(p.uid) else ""), 20)
		text(rr.position + Vector2(18, 54), "%s · Lv %d · %s" % [ContentDB.name_of("pets", str(p.species)), int(p.level), str(p.role).capitalize()], 15, UiKit.MIST)
		region(rr, "sel", str(p.uid))
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	var pet := {}
	for p in ch.pets:
		if str(p.uid) == sel: pet = p
	if pet.is_empty(): return
	var sp := ContentDB.entry("pets", str(pet.species))
	heading(right.position + Vector2(24, 44), str(pet.name), right.size.x - 48)
	text(right.position + Vector2(24, 80), "%s · %s · %s" % [str(sp.get("name", "")), str(sp.get("element", "")).capitalize(), str(pet.get("stage", "hatchling")).capitalize()], 18, UiKit.MIST)
	bar(Rect2(right.position.x + 24, right.position.y + 100, 400, 30), float(pet.get("bond", 0.0)) / 10.0, UiKit.RED, "Bond %.1f / 10" % float(pet.get("bond", 0.0)))
	text(right.position + Vector2(24, 170), "Skills: " + ", ".join(sp.get("skills", [])), 16)
	text(right.position + Vector2(24, 196), "Favourite foods: " + ", ".join((sp.get("favourite_foods", []) as Array).map(func(f): return ContentDB.item_name(str(f)))), 16, UiKit.MIST)
	var y := right.position.y + 230
	for role in ["combat", "gatherer", "cultivation"]:
		btn(Rect2(right.position.x + 24 + ["combat", "gatherer", "cultivation"].find(role) * 170, y, 160, 48), role.capitalize(), "role", role, str(pet.role) == role)
	y += 70
	btn(Rect2(right.position.x + 24, y, 240, 52), "Set active" if ch.active_pet != sel else "Rest", "active", sel, ch.active_pet != sel)
	var foods: Array = (sp.get("favourite_foods", []) as Array).filter(func(f): return ch.inventory.count(str(f)) > 0)
	for f in ["roast_fish", "ember_pepper_broth"]:
		if ch.inventory.count(f) > 0 and not foods.has(f): foods.append(f)
	var x := right.position.x + 24
	for f in foods:
		slot_box(Rect2(x, y + 80, 60, 60), str(f), ch.inventory.count(str(f)), "", "feed", str(f))
		x += 68
	if not foods.is_empty(): text(Vector2(right.position.x + 24, y + 74), "Tap food to feed", 16, UiKit.MIST)

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"role": submit({"type": "set_pet_role", "pet": sel, "role": str(data)})
		"active": submit({"type": "set_active_pet", "pet": "" if c().active_pet == sel else sel})
		"feed": submit({"type": "feed_pet", "pet": sel, "item": str(data)})
