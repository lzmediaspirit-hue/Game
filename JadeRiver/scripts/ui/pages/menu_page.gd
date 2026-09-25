extends Page
## Main hub (Part 9.6 · Core hub/menu pages). Locked entries stay visible, dimmed,
## and explain their unlock on tap.

var ENTRIES := [
	["character", Tx.t("ui.menu.character"), "character", "character_menu"],
	["cultivation", Tx.t("ui.menu.cultivation"), "cultivation", "cultivation"],
	["techniques", Tx.t("ui.menu.techniques"), "techniques", "technique_slots_2"],
	["inventory", Tx.t("ui.menu.bag"), "bag", "bag"],
	["quests", Tx.t("ui.menu.quests"), "quest", "navigation"],
	["world_map", Tx.t("ui.menu.map"), "world_map", "world_menu"],
	["training_sect", Tx.t("ui.menu.sect"), "sect", "sect_choice"],
	["your_sect", Tx.t("ui.menu.your_sect"), "account", "your_sect"],
	["spirit_animals", Tx.t("ui.menu.spirit_animals"), "spirit_animals", "spirit_animals"],
	["companions", Tx.t("ui.menu.companions"), "characters", "companions"],
	["crafts", Tx.t("ui.menu.crafts"), "crafts", "herb_gathering"],
	["workshop", Tx.t("ui.menu.workshop"), "formation", "appraisal"],
	["characters", Tx.t("ui.menu.characters"), "characters", "idle_tasks"],
	["codex", Tx.t("ui.menu.codex"), "codex", "codex"],   # Collection and Achievements are Codex tabs
	["mail", Tx.t("ui.menu.mail"), "mail", "mail"],
	["emotes", Tx.t("ui.menu.emotes"), "talk", ""],
	["settings", Tx.t("ui.menu.settings"), "settings", ""],
	["exit", Tx.t("ui.menu.save_exit"), "back", ""],
]

func _init() -> void:
	title = Tx.t("ui.menu.menu")

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var cols := 6
	var cw := (content.size.x - 20) / cols
	var ch_h := 150.0
	for i in ENTRIES.size():
		var e: Array = ENTRIES[i]
		var r := Rect2(content.position.x + (i % cols) * cw + 6, content.position.y + 10 + (i / cols) * (ch_h + 12), cw - 12, ch_h)
		var locked: bool = e[3] != "" and not Unlocks.is_unlocked(ch.id, e[3])
		draw_style_box(UiKit.style("minor_panel", "disabled" if locked else ("pressed" if _is_pressed("open", e[0]) else "normal")), r)
		var ic := Rect2(r.get_center().x - 32, r.position.y + 18, 64, 64)
		icon_at(ic, e[2])
		if locked:
			draw_rect(ic, Color(0.02, 0.05, 0.06, 0.55))
			_lock_icon(ic.end - Vector2(16, 18))
		text(Vector2(r.position.x, r.position.y + 112), e[1], 20, UiKit.HOLLOW if locked else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		if e[0] == "mail" and not locked and Game.mail.unread(ch) > 0:
			draw_circle(r.position + Vector2(r.size.x - 18, 18), 11, UiKit.RED)
			text(r.position + Vector2(r.size.x - 30, 25), str(mini(99, Game.mail.unread(ch))), 14, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 24)
		region(r, "open", e[0], not locked, Unlocks.locked_text(e[3]) if locked else "")
	var y := content.end.y - 40
	text(Vector2(content.position.x, y), "%s · %s" % [ch.name, ContentDB.realm_label(ch.cultivator.realm_key)], 20, UiKit.MIST)
	var x := content.end.x - 10
	for cur in ["contribution", "spirit_stone", "silver_tael"]:
		if cur == "contribution" and str(ch.training_sect.get("id", "")) == "": continue
		var amt := Game.economy.balance(cur, ch)
		var w := UiKit.text_width(UiKit.fmt(amt), 18) + 52
		x -= w + 8
		currency_pill(Vector2(x, y - 26), cur, amt)

func on_action(id: String, data) -> void:
	if id == "exit_yes":
		navigate.emit("_exit", {})
		return
	if id != "open": return
	if data == "exit":
		ask(Tx.t("ui.menu.save_and_return_to_character"), "exit_yes")
		return
	navigate.emit(str(data), {})

func on_event(name: String, _p: Dictionary) -> void:
	queue_redraw()
