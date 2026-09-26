class_name ShellScreens
extends RefCounted
## Title, character selection and creator (S23, S27, S35, Part 9.6 "Game shell").
## Each screen is a frameless Page drawn over the river backdrop.

const Avatar = preload("res://scripts/avatar.gd")


class TitleScreen extends Page:
	signal chosen(action: String)

	func _init() -> void:
		frameless = true
		page_id = "title"

	func draw_page() -> void:
		var pulse := 0.5 + 0.5 * sin(t * 2.2)
		draw_rect(Rect2(0, 0, 1280, 720), Color(0.01, 0.04, 0.05, 0.25))
		UiKit.draw_text(self, Tx.t("shell.jade_river"), Vector2(0, 250), 104, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 1280, true, true)
		UiKit.draw_text(self, Tx.t("shell.a_cultivator_journey_down_the"), Vector2(0, 302), 28, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 1280, true, true)
		draw_line(Vector2(440, 326), Vector2(840, 326), UiKit.BRONZE, 2)
		for i in 3:
			draw_rect(Rect2(626 + i * 12, 320, 6, 6), UiKit.GOLD)
		var has_chars := not Game.characters.is_empty()
		btn(Rect2(490, 420, 300, 64), Tx.t("shell.continue") if has_chars else Tx.t("shell.begin"), "start", null, true, true, "", 26)
		btn(Rect2(490, 500, 300, 56), Tx.t("shell.settings"), "settings")
		if OS.get_name() not in ["Android", "iOS", "Web"]:
			btn(Rect2(490, 570, 300, 56), Tx.t("shell.quit"), "quit")
		text(Vector2(0, 700), Tx.t("shell.v1_0_jade_river_valley"), 16, Color(UiKit.MIST, 0.6 + 0.2 * pulse), HORIZONTAL_ALIGNMENT_CENTER, 1280)
		if OS.has_feature("max_test"): text(Vector2(0, 672), Tx.t("shell.max_test_build"), 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, 1280)

	func on_action(id: String, _data) -> void:
		chosen.emit(id)


class SelectionScreen extends Page:
	signal enter(slot: int)
	signal create(slot: int)
	signal back

	const PER_PAGE := 4
	var chosen := 1
	var page := 0
	var avatars: Dictionary = {}

	func _init() -> void:
		frameless = true
		page_id = "selection"

	func setup() -> void:
		chosen = maxi(1, int(Game.account.active_slot))
		page = (chosen - 1) / PER_PAGE
		_rebuild_avatars()

	func _rebuild_avatars() -> void:
		for a in avatars.values(): a.queue_free()
		avatars.clear()
		for i in PER_PAGE:
			var slot := page * PER_PAGE + i + 1
			var ch = Game.character("c%d" % slot)
			if ch == null: continue
			var av = Avatar.new()
			av.outfit = InventoryAuthority.outfit_for(ch)
			av.position = Vector2(_card(i).get_center().x, _card(i).position.y + 250)
			av.scale = Vector2.ONE * 1.6
			add_child(av)
			avatars[slot] = av

	func _card(i: int) -> Rect2:
		return Rect2(96 + i * 276, 150, 256, 420)

	func draw_page() -> void:
		UiKit.draw_text(self, Tx.t("shell.jade_river"), Vector2(0, 70), 54, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 1280, true, true)
		text(Vector2(0, 116), Tx.t("shell.choose_your_disciple"), 24, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 1280, true)
		var rules: Array = ContentDB.config("account_rules").get("slots", [])
		for i in PER_PAGE:
			var slot := page * PER_PAGE + i + 1
			var r := _card(i)
			var ch = Game.character("c%d" % slot)
			var unlocked := slot <= Game.account.slots_unlocked
			draw_style_box(UiKit.style("major_window" if slot == chosen and ch != null else "minor_panel"), r)
			if ch != null:
				text(r.position + Vector2(0, 312), str(ch.name), 26, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				text(r.position + Vector2(0, 342), ContentDB.realm_label(ch.cultivator.realm_key), 18, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				var sect_name := ContentDB.name_of("sects", str(ch.training_sect.get("id", ""))) if str(ch.training_sect.get("id", "")) != "" else ContentDB.text("ui.unaffiliated")
				text(r.position + Vector2(0, 368), sect_name, 17, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				var status := ""
				if ch.cultivator.state == "bottleneck": status = Tx.t("shell.at_a_bottleneck")
				elif not ch.cultivator.injuries.is_empty(): status = Tx.t("shell.injured")
				elif not ch.idle_task.is_empty(): status = Tx.t("shell.idle") % str(ch.idle_task.get("task", "")).capitalize()
				if status != "": text(r.position + Vector2(0, 396), status, 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				region(r, "select", slot)
			elif unlocked:
				text(r.position + Vector2(0, 190), "+", 86, UiKit.GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, true)
				text(r.position + Vector2(0, 260), Tx.t("shell.create_disciple"), 24, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				region(r, "create", slot)
			else:
				_lock_icon(r.get_center() - Vector2(6, 60))
				var why := Tx.t("shell.locked")
				for rule in rules:
					if int(rule.slot) == slot:
						why = RequirementRules.first_failure_text(rule.get("requires", {}), {"char": null, "account": Game.account, "room": {}})
				text(r.position + Vector2(0, 220), Tx.t("shell.slot") % slot, 22, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
				para(Rect2(r.position + Vector2(24, 236), Vector2(r.size.x - 48, 80)), why, 17, UiKit.HOLLOW)
		var pages := int(ceil(float(AccountState.MAX_SLOTS) / PER_PAGE))
		if page > 0: btn(Rect2(24, 330, 56, 72), "◀", "page", -1, false, true, "", 20)
		if page < pages - 1: btn(Rect2(1200, 330, 56, 72), "▶", "page", 1, false, true, "", 20)
		for p in pages:
			draw_circle(Vector2(620 + p * 20, 596), 5, UiKit.GOLD if p == page else UiKit.HOLLOW)
		if Game.character("c%d" % chosen) != null:
			btn(Rect2(465, 620, 350, 64), Tx.t("shell.enter_world"), "enter", chosen, true, true, "", 26)
			btn(Rect2(1010, 632, 170, 48), Tx.t("shell.delete"), "delete", chosen)
		btn(Rect2(96, 632, 150, 48), Tx.t("shell.title"), "back")

	func on_action(id: String, data) -> void:
		match id:
			"select":
				if int(data) == chosen: enter.emit(chosen)
				chosen = int(data)
			"create": create.emit(int(data))
			"enter": enter.emit(int(data))
			"page":
				page = clampi(page + int(data), 0, int(ceil(float(AccountState.MAX_SLOTS) / PER_PAGE)) - 1)
				_rebuild_avatars()
			"delete":
				var ch = Game.character("c%d" % int(data))
				ask(Tx.t("shell.delete_this_cannot_be_undone") % (ch.name if ch else Tx.t("shell.this_disciple")), "delete_yes", data, true)
			"delete_yes":
				submit({"type": "delete_character", "slot": int(data)})
				_rebuild_avatars()
			"back": back.emit()


class CreatorScreen extends Page:
	signal created(slot: int)
	signal cancelled

	const ROWS := ["hair", "shirt", "pants", "shoes", "origin"]
	var LABELS := {"hair": Tx.t("shell.hair"), "shirt": Tx.t("shell.robe"), "pants": Tx.t("shell.trousers"), "shoes": Tx.t("shell.shoes"), "origin": Tx.t("shell.origin")}
	var slot := 1
	var draft: Dictionary = {}
	var origin := "fishers_child"
	var preview
	var name_field: LineEdit
	var skip_prologue := false
	var dye_buttons: Array = [0, 1, 2, 3, 4, 5]
	var rng := RandomNumberGenerator.new()

	func _init() -> void:
		frameless = true
		page_id = "creator"

	func setup() -> void:
		slot = int(args.get("slot", 1))
		var rules: Dictionary = ContentDB.config("account_rules").get("creator", {})
		draft = {"body": "light", "hair": str(rules.get("hair", ["topknot"])[1]), "hair_color": 0, "shirt": "disciple", "pants": "loose",
			"shoes": "slippers", "hat": "none", "cape": "none", "weapon": "none"}
		preview = Avatar.new()
		preview.outfit = draft
		preview.position = Vector2(330, 500)
		preview.scale = Vector2.ONE * 3.0
		add_child(preview)
		preview.play("idle")
		name_field = LineEdit.new()
		name_field.max_length = int(ContentDB.config("account_rules").get("name_max", 24))
		name_field.placeholder_text = Tx.t("shell.your_name")
		name_field.position = Vector2(820, 128)
		name_field.size = Vector2(360, 46)
		name_field.add_theme_font_override("font", UiKit.text_font())
		name_field.add_theme_font_size_override("font_size", 24)
		name_field.add_theme_color_override("font_color", UiKit.PAPER)
		name_field.add_theme_stylebox_override("normal", UiKit.style("slot"))
		name_field.add_theme_stylebox_override("focus", UiKit.style("selected_slot_glow"))
		add_child(name_field)

	func options(row: String) -> Array:
		var rules: Dictionary = ContentDB.config("account_rules").get("creator", {})
		match row:
			"hair": return rules.get("hair", Wardrobe.parts.hair.keys())
			"shirt": return rules.get("robe", ["disciple"])
			"pants": return rules.get("trousers", ["loose"])
			"shoes": return rules.get("shoes", ["slippers"])
			"origin": return ContentDB.all("origins").map(func(o): return str(o.id))
		return []

	func value(row: String) -> String:
		return origin if row == "origin" else str(draft.get(row, ""))

	func label_of(row: String, v: String) -> String:
		if row == "origin": return ContentDB.name_of("origins", v)
		return str(Wardrobe.parts.get(row, {}).get(v, {}).get("label", v.capitalize()))

	func cycle(row: String, dir: int) -> void:
		var opts := options(row)
		if opts.is_empty(): return
		var i := opts.find(value(row))
		var v := str(opts[posmod(i + dir, opts.size())])
		if row == "origin": origin = v
		else:
			draft[row] = v
			preview.outfit = draft.duplicate()
			preview.last_key = ""

	func set_hair_dye(i: int) -> void:
		draft.hair_color = i
		preview.outfit = draft.duplicate()
		preview.last_key = ""

	func randomize_look() -> void:
		rng.randomize()
		for row in ROWS:
			var opts := options(row)
			var v := str(opts[rng.randi_range(0, opts.size() - 1)])
			if row == "origin": origin = v
			else: draft[row] = v
		draft.hair_color = rng.randi_range(0, 5)
		preview.outfit = draft.duplicate()
		preview.last_key = ""

	func draw_page() -> void:
		UiKit.draw_text(self, Tx.t("shell.create_disciple_2"), Vector2(0, 74), 48, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 1280, true, true)
		draw_style_box(UiKit.style("major_window"), Rect2(120, 110, 420, 520))
		draw_ellipse_shadow(Vector2(330, 500))
		var panel_r := Rect2(600, 104, 610, 530)
		draw_style_box(UiKit.style("major_window"), panel_r)
		text(Vector2(640, 160), Tx.t("shell.name"), 24, UiKit.GOLD)
		var y := 190.0
		for row in ROWS:
			text(Vector2(640, y + 34), LABELS[row], 22, UiKit.GOLD)
			btn(Rect2(800, y + 4, 52, 46), "◀", "prev", row, false, true, "", 16)
			text(Vector2(860, y + 36), label_of(row, value(row)), 21, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 270)
			btn(Rect2(1136, y + 4, 52, 46), "▶", "next", row, false, true, "", 16)
			y += 58
		text(Vector2(640, y + 32), Tx.t("shell.hair_dye"), 22, UiKit.GOLD)
		for i in 6:
			var col := Color(str(Wardrobe.parts._colors.hair[i].hex))
			var r := Rect2(800 + i * 64, y + 6, 50, 42)
			draw_rect(r, col)
			draw_rect(r, UiKit.GOLD if int(draft.hair_color) == i else UiKit.INK, false, 3 if int(draft.hair_color) == i else 2)
			region(r, "dye", i)
		y += 58
		var od := ContentDB.entry("origins", origin)
		para(Rect2(640, y, 540, 60), str(od.get("desc", od.get("description", ""))), 17, UiKit.MIST, 2)
		if Game.characters.size() >= 1 and bool(ContentDB.config("account_rules").get("skip_prologue_allowed", true)):
			var box := Rect2(640, 578, 30, 30)
			draw_style_box(UiKit.style("slot"), box)
			if skip_prologue: draw_rect(box.grow(-8), UiKit.JADE)
			text(Vector2(680, 600), Tx.t("shell.skip_the_prologue_start_at"), 17, UiKit.PAPER)
			region(Rect2(636, 574, 420, 38), "skip")
		btn(Rect2(160, 646, 150, 54), Tx.t("shell.back"), "back")
		btn(Rect2(330, 646, 170, 54), Tx.t("shell.randomize"), "random")
		btn(Rect2(880, 646, 300, 60), Tx.t("shell.begin"), "begin", null, true, true, "", 26)

	func draw_ellipse_shadow(p: Vector2) -> void:
		draw_set_transform(p, 0, Vector2(1, 0.25))
		draw_circle(Vector2.ZERO, 70, Color(0, 0, 0, 0.35))
		draw_set_transform(Vector2.ZERO)

	func on_action(id: String, data) -> void:
		match id:
			"prev": cycle(str(data), -1)
			"next": cycle(str(data), 1)
			"dye": set_hair_dye(int(data))
			"random": randomize_look()
			"skip": skip_prologue = not skip_prologue
			"back": cancelled.emit()
			"begin":
				var nm := name_field.text.strip_edges()
				if nm == "":
					flash(Tx.t("shell.please_enter_a_name"))
					name_field.grab_focus()
					return
				var r := submit({"type": "create_character", "slot": slot, "name": nm, "origin": origin, "skip_prologue": skip_prologue,
					"appearance": {"hair": draft.hair, "hair_color": draft.hair_color, "shirt": draft.shirt, "pants": draft.pants, "shoes": draft.shoes}})
				if r.get("ok", false): created.emit(slot)
