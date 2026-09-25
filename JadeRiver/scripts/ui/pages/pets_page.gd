extends Page
## Spirit animals (S22): roster, active animal, role, bond and feeding.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.pets.spirit_animals")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var left := Rect2(content.position.x, content.position.y, 330, content.size.y)
	panel(left)
	if ch.pets.is_empty():
		para(Rect2(left.position + Vector2(20, 20), left.size - Vector2(40, 40)), Tx.t("ui.pets.no_spirit_animals_yet_hermit"), 19, UiKit.MIST)
	# Open on the active animal (or the first one) instead of an empty panel.
	if not ch.pets.is_empty() and not ch.pets.any(func(p): return str(p.uid) == sel):
		sel = ch.active_pet if ch.active_pet != "" else str(ch.pets[0].uid)
	var eggs_h := 150.0 if not ch.eggs.is_empty() else 0.0
	list("pets", Rect2(left.position, left.size - Vector2(0, eggs_h)).grow(-10), ch.pets.size(), 70, func(i: int, rr: Rect2):
		var p: Dictionary = ch.pets[i]
		panel(rr, "minor_panel", "selected" if sel == str(p.uid) else "normal")
		creature_at(Rect2(rr.position + Vector2(6, 4), Vector2(62, 60)), _art(p))
		text(rr.position + Vector2(76, 30), str(p.name) + ("  ◆" if ch.active_pet == str(p.uid) else ("  ◇" if ch.party_pets.has(str(p.uid)) else "")), 20)
		text(rr.position + Vector2(76, 54), Tx.t("ui.pets.lv") % [ContentDB.name_of("pets", str(p.species)), int(p.level), str(p.role).capitalize()], 15, UiKit.MIST)
		region(rr, "sel", str(p.uid))
	)
	if eggs_h > 0.0: _eggs(ch, Rect2(left.position.x + 10, left.end.y - eggs_h, left.size.x - 20, eggs_h - 10))
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
	var form_tint: Dictionary = Game.pets.form_of(pet)
	creature_at(stage.grow_individual(-8, -8, -8, -14), _art(pet), "walk" if ch.active_pet == sel else "idle",
		Color.WHITE.lerp(Color(str(form_tint.get("tint", "#ffffff"))), 0.5) if not form_tint.is_empty() else Color.WHITE)
	heading(right.position + Vector2(24, 44), str(pet.name), colw)
	var stage_name := str(Game.pets.stage_def(str(pet.get("stage", "hatchling"))).get("name", Tx.t("ui.pets.hatchling")))
	var branch := str(pet.get("branch", ""))
	var rarity: Dictionary = Game.pets.rarity_def(str(pet.get("rarity", "common")))
	text(right.position + Vector2(24, 80), fit("%s · %s · %s · %s" % [str(sp.get("name", "")), str(sp.get("element", "")).capitalize(), branch if branch != "" else stage_name,
		str(rarity.get("name", ""))], 18, colw), 18, UiKit.MIST)
	bar(Rect2(px, right.position.y + 96, colw, 28), float(pet.get("bond", 0.0)) / 10.0, UiKit.RED, Tx.t("ui.pets.bond_1f_10") % float(pet.get("bond", 0.0)))
	var need := float(ContentDB.curve("pet_xp.base", 20)) * pow(int(pet.level), float(ContentDB.curve("pet_xp.per_level_pow", 1.5)))
	bar(Rect2(px, right.position.y + 130, colw, 24), float(pet.get("xp", 0.0)) / need, UiKit.GOLD, Tx.t("ui.pets.level") % [int(pet.level), int(pet.get("xp", 0.0)), int(need)])
	text(right.position + Vector2(24, 180), fit(Tx.t("ui.pets.skills") + ", ".join(sp.get("skills", [])), 16, colw), 16)
	text(right.position + Vector2(24, 204), fit(Tx.t("ui.pets.favourite_foods") + ", ".join((sp.get("favourite_foods", []) as Array).map(func(f): return ContentDB.item_name(str(f)))), 16, colw), 16, UiKit.MIST)
	var shown: Array = Game.pets.revealed_traits(pet).map(func(t): return ContentDB.name_of("pet_traits", str(t)))
	while shown.size() < int(ContentDB.config("pet_growth").get("traits_per_pet", 3)): shown.append("?")
	text(right.position + Vector2(24, 228), fit(Tx.t("ui.pets.traits") + " · ".join(shown), 16, colw), 16, UiKit.PALE_GOLD)
	# S46 bloodline: purity, and growth and aptitude once it is a Juvenile; a Grievous Wound in red.
	Game.pets.ensure_fields(pet)
	var blood := Tx.t("ui.pets.purity") % int(pet.get("purity", 0))
	var apt_line := Tx.t("ui.pets.aptitude_hidden")
	if Game.pets.aptitude_known(pet):
		var apt: Dictionary = pet.get("aptitude", {})
		blood += "  ·  " + Tx.t("ui.pets.growth") % float(pet.get("growth", 1.0))
		apt_line = Tx.t("ui.pets.aptitude") % [float(apt.get("hp", 1.0)), float(apt.get("attack", 1.0)), float(apt.get("defence", 1.0)), float(apt.get("speed", 1.0))]
	if pet.get("variant", false): blood += "  ·  " + Tx.t("ui.pets.variant")
	text(right.position + Vector2(24, 252), fit(blood, 16, colw), 16, UiKit.BRIGHT_JADE)
	text(right.position + Vector2(24, 274), fit(apt_line, 15, colw), 15, UiKit.MIST)
	# The contract, the awakened skill or form, and Resonance while it sits beside you.
	var bond_line := Tx.t("ui.pets.contract_" + str(pet.get("contract", "master")))
	var form: Dictionary = Game.pets.form_of(pet)
	var skill: Dictionary = Game.pets.bloodline_skill(pet)
	if not form.is_empty(): bond_line += "  ·  " + Tx.t("ui.pets.form") % str(form.get("name", ""))
	elif not skill.is_empty(): bond_line += "  ·  " + Tx.t("ui.pets.bloodline_skill") % str(skill.get("name", ""))
	var res := Game.pets.resonance(ch) if Game.pets.party(ch).any(func(q): return str(q.uid) == sel) else 0.0
	if res > 0.0: bond_line += "  ·  " + Tx.t("ui.pets.resonance") % int(round(res * 100.0))
	text(right.position + Vector2(24, 296), fit(bond_line, 15, colw), 15, UiKit.PALE_GOLD)
	var y := right.position.y + 312
	if pet.get("wounded", false):
		text(right.position + Vector2(24, 320), fit(Tx.t("ui.pets.wounded"), 15, colw), 15, UiKit.RED)
		y += 20
	var roles := ["combat", "gatherer", "cultivation"]
	if Game.pets.mountable(pet): roles.append("mount")
	if Unlocks.is_unlocked(ch.id, "herb_garden"): roles.append("guard")   # S45: watches the garden while you are away
	var bw := (colw - 8.0 * (roles.size() - 1)) / roles.size()
	for role in roles:
		btn(Rect2(px + roles.find(role) * (bw + 8), y, bw, 46), fit(Tx.t("ui.pets.role_" + role), 15, bw - 10), "role", role, str(pet.role) == role, true, "", 15)
	y += 60
	# Set active; Beside You once the Soul commands more than one (S46); a contract when one is open.
	var aw := (colw - 16.0) / 3.0
	btn(Rect2(px, y, aw, 50), fit(Tx.t("ui.pets.set_active") if ch.active_pet != sel else Tx.t("ui.pets.rest"), 17, aw - 12), "active", sel, ch.active_pet != sel, true, "", 17)
	var cap: int = Game.pets.command_capacity(ch)
	if cap > 1 and ch.active_pet != sel:
		var beside: bool = ch.party_pets.has(sel)
		var room_left: bool = beside or Game.pets.party(ch).size() < cap
		btn(Rect2(px + aw + 8, y, aw, 50), fit(Tx.t("ui.pets.send_home") if beside else Tx.t("ui.pets.beside"), 17, aw - 12), "party", not beside, beside, room_left,
			Tx.t("ui.pets.capacity_full") % cap, 17)
	var ctr := ""
	if Game.pets.equal_contract_open(ch, pet): ctr = "equal"
	elif str(pet.get("contract", "master")) == "master" and ch.inventory.count(str(ContentDB.config("pet_growth").get("contracts", {}).get("blood", {}).get("item", ""))) > 0: ctr = "blood"
	if ctr != "":
		btn(Rect2(px + 2.0 * (aw + 8), y, aw, 50), fit(Tx.t("ui.pets.contract_btn_" + ctr), 17, aw - 12), "contract", ctr, ctr == "equal", true, "", 17)
	btn(Rect2(stage.position.x, stage.end.y + 8, stage.size.x, 38), Tx.t("ui.pets.unlock") if pet.get("locked", false) else Tx.t("ui.pets.lock"),
		"lock", sel, false, true, "", 16)
	_growth(ch, pet, Rect2(stage.position.x, stage.end.y + 56, stage.size.x, right.end.y - stage.end.y - 70))
	var foods: Array = (sp.get("favourite_foods", []) as Array).filter(func(f): return ch.inventory.count(str(f)) > 0)
	for f in ["roast_fish", "ember_pepper_broth"]:
		if ch.inventory.count(f) > 0 and not foods.has(f): foods.append(f)
	var x := px
	for f in foods:
		if x + 60 > px + colw: break
		slot_box(Rect2(x, y + 84, 60, 60), str(f), ch.inventory.count(str(f)), "", "feed", str(f))
		x += 68
	# S46: cores of the animal's own element, to devour for growth.
	var cores: Array = []
	for st in ch.inventory.bag:
		if st == null: continue
		var cd: Dictionary = ContentDB.item(str(st.id)).get("core", {})
		if cd.has("tier") and str(cd.element) == str(sp.get("element", "")) and not cores.has(str(st.id)): cores.append(str(st.id))
	for cid in cores:
		if x + 60 > px + colw: break
		slot_box(Rect2(x, y + 84, 60, 60), str(cid), ch.inventory.count(str(cid)), "", "devour", str(cid))
		x += 68
	if not foods.is_empty() or not cores.is_empty(): text(Vector2(px, y + 76), Tx.t("ui.pets.tap_food_to_feed"), 16, UiKit.MIST)
	_breeding(ch, pet, Rect2(px, y + 156, colw, right.end.y - y - 170))

## Breeding (S22): two Adults of one family; shows the gate that is closed, or a button per partner.
func _breeding(ch, pet: Dictionary, r: Rect2) -> void:
	var partners: Array = Game.pets.breed_partners(ch, pet)
	if partners.is_empty() or r.size.y < 40: return
	text(r.position + Vector2(0, 18), Tx.t("ui.pets.breed_with"), 17, UiKit.GOLD)
	var why: String = Game.pets.breeding_blocked(ch)
	if why != "":
		para(Rect2(r.position + Vector2(0, 26), Vector2(r.size.x, 48)), why, 16, UiKit.MIST, 2)
		return
	var x := r.position.x
	for o in partners.slice(0, 2):
		var bw := (r.size.x - 10) / 2.0
		btn(Rect2(x, r.position.y + 28, bw, 44), fit(str(o.name), 17, bw - 16), "breed", str(o.uid), false, true, "", 17)
		x += bw + 10

## Incubating eggs with the time left, or a Hatch button when one is ready.
func _eggs(ch, r: Rect2) -> void:
	panel(r, "minor_panel")
	text(r.position + Vector2(12, 24), Tx.t("ui.pets.eggs"), 17, UiKit.GOLD)
	var x := r.position.x + 12
	var each := (r.size.x - 24.0) / maxf(1.0, float(ch.eggs.size()))
	for i in ch.eggs.size():
		var egg: Dictionary = ch.eggs[i]
		slot_box(Rect2(x, r.position.y + 30, 50, 50), "spirit_egg", 0, str(egg.get("rarity", "")) if egg.get("bred", false) else "")
		var left_s := float(egg.hatch_utc) - Clock.now_utc()
		if left_s <= 0.0:
			btn(Rect2(x + 58, r.position.y + 32, minf(120.0, each - 66.0), 46), Tx.t("ui.pets.hatch"), "hatch", i, true)
		else:
			var hl := Tx.t("ui.pets.hatches_in") if each >= 200.0 else Tx.t("ui.pets.hatches_short")
			text(Vector2(x + 58, r.position.y + 62), fit(hl % ceili(left_s / 3600.0), 16, each - 64.0), 16, UiKit.MIST)
		# S46 incubation input: your blood, a core to steer the element, essence blood to reroll a trait.
		if i == 0:
			var used: Array = egg.get("inputs", [])
			var bw := (r.size.x - 24 - 16) / 3.0
			var core := _steering_core(ch, egg)
			var reroll_item := str(ContentDB.config("pet_growth").get("incubation", {}).get("reroll_item", ""))
			var opts := [["blood", "", not used.has("blood") and float(ch.cooldowns.get("essence_blood", 0.0)) <= Clock.now_utc()],
				["element", core, not used.has("element") and core != "" and not egg.get("bred", false)],
				["reroll", "", not used.has("reroll") and ch.inventory.count(reroll_item) > 0]]
			for k in opts.size():
				var o: Array = opts[k]
				btn(Rect2(r.position.x + 12 + k * (bw + 8), r.position.y + 88, bw, 44), fit(Tx.t("ui.pets.egg_" + str(o[0])) + (" ✓" if used.has(str(o[0])) else ""), 15, bw - 10),
					"infuse", [i, str(o[0]), str(o[1])], false, bool(o[2]), Tx.t("ui.pets.egg_" + str(o[0]) + "_why"), 15)
		x += each

## Next stage: each gate ticked or not, then Evolve (or the two branches at Adult).
func _growth(ch, pet: Dictionary, r: Rect2) -> void:
	var nx: Dictionary = Game.pets.next_stage(pet)
	if nx.is_empty():
		para(r, Tx.t("ui.pets.fully_grown_for_this_land"), 16, UiKit.MIST)
		return
	text(r.position + Vector2(0, 18), Tx.t("ui.pets.next") % str(nx.get("name", "")), 18, UiKit.GOLD)
	var y := r.position.y + 30
	for g in Game.pets.evolve_gates(ch, pet):
		text(Vector2(r.position.x, y + 18), ("✓ " if g.ok else "· ") + str(g.text), 16, UiKit.BRIGHT_JADE if g.ok else UiKit.MIST)
		y += 24
	var ready: bool = Game.pets.can_evolve(ch, pet)
	y += 8
	if nx.get("branch", false):
		for b in ContentDB.entry("pets", str(pet.species)).get("branches", []):
			btn(Rect2(r.position.x, y, r.size.x, 42), str(b), "evolve", str(b), ready, ready, Tx.t("ui.pets.not_ready_yet"), 17)
			y += 48
	else:
		btn(Rect2(r.position.x, y, r.size.x, 46), Tx.t("ui.pets.evolve"), "evolve", "", true, ready, Tx.t("ui.pets.not_ready_yet"))

## The first core in the bag whose element some other egg answers (to steer this one).
func _steering_core(ch, egg: Dictionary) -> String:
	var own := str(ContentDB.entry("pets", str(egg.get("species", ""))).get("element", ""))
	var els := {}
	for r in ContentDB.config("eggs").get("species", []): els[str(ContentDB.entry("pets", str(r.species)).get("element", ""))] = true
	for st in ch.inventory.bag:
		if st == null: continue
		var el := str(ContentDB.item(str(st.id)).get("core", {}).get("element", ""))
		if el != "" and el != own and els.has(el): return str(st.id)
	return ""

func _art(p: Dictionary) -> String:
	return str(ContentDB.entry("pets", str(p.species)).get("art", p.species))

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"role": submit({"type": "set_pet_role", "pet": sel, "role": str(data)})
		"active": submit({"type": "set_active_pet", "pet": "" if c().active_pet == sel else sel})
		"feed": submit({"type": "feed_pet", "pet": sel, "item": str(data)})
		"devour":
			var dv := submit({"type": "devour_core", "pet": sel, "item": str(data)})
			if dv.get("ok", false): flash(Tx.t("ui.pets.devoured") % int(dv.xp))
		"lock": submit({"type": "lock_pet", "pet": str(data)})
		"evolve": submit({"type": "evolve_pet", "pet": sel, "branch": str(data)})
		"breed": submit({"type": "breed", "a": sel, "b": str(data)})
		"hatch": submit({"type": "hatch_egg", "index": int(data)})
		"party": submit({"type": "set_party", "pet": sel, "on": bool(data)})
		"contract": submit({"type": "offer_contract", "pet": sel, "kind": str(data)})
		"infuse": submit({"type": "incubate_input", "egg": int(data[0]), "kind": str(data[1]), "item": str(data[2])})
