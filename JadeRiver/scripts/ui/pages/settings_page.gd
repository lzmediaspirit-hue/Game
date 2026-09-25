extends Page
## Settings (S35, Part 9.6): audio, controls, display, accessibility, notifications, data.

var SLIDERS := [["music", Tx.t("ui.settings.music")], ["ambience", Tx.t("ui.settings.ambience")], ["sfx", Tx.t("ui.settings.effects")], ["ui", Tx.t("ui.settings.interface")]]
var TOGGLES := [["left_handed", Tx.t("ui.settings.left_handed_controls")], ["screen_shake", Tx.t("ui.settings.screen_shake")], ["damage_numbers", Tx.t("ui.settings.damage_numbers")],
	["notifications", Tx.t("ui.settings.notifications")], ["minimap", Tx.t("ui.settings.show_minimap")], ["auto_pickup", Tx.t("ui.settings.auto_pick_up")]]

func _init() -> void:
	title = Tx.t("ui.settings.settings")
	tabs = [{"id": "audio", "label": Tx.t("ui.settings.audio")}, {"id": "controls", "label": Tx.t("ui.settings.controls")}, {"id": "access", "label": Tx.t("ui.settings.accessibility")}, {"id": "data", "label": Tx.t("ui.settings.data")}]

func setting(key: String, default):
	return Game.account.settings.get(key, default)

func set_setting(key: String, value) -> void:
	Game.submit({"type": "set_setting", "key": key, "value": value})
	Game.save_all()

func draw_page() -> void:
	var x := content.position.x + 40
	var y := content.position.y + 20
	match str(tabs[tab].id):
		"audio":
			for s in SLIDERS:
				var v := float(setting(s[0], 0.7))
				text(Vector2(x, y + 32), s[1], 22)
				for step in 11:
					var r := Rect2(x + 220 + step * 56, y + 8, 48, 36)
					var on := step <= int(round(v * 10))
					draw_style_box(UiKit.style("slot", "pressed" if on else "normal"), r)
					if on: draw_rect(r.grow(-8), UiKit.JADE)
					region(r, "vol", [s[0], step / 10.0])
				y += 64
		"controls":
			for tg in TOGGLES.slice(0, 3):
				_toggle(Vector2(x, y), tg[0], tg[1])
				y += 60
			para(Rect2(x, y + 20, 900, 120), Tx.t("ui.settings.keyboard_arrows_wasd_move_space"), 18, UiKit.MIST)
		"access":
			text(Vector2(x, y + 32), Tx.t("ui.settings.text_size"), 22)
			for i in 3:
				btn(Rect2(x + 220 + i * 150, y + 4, 140, 50), [Tx.t("ui.settings.small"), Tx.t("ui.settings.normal"), Tx.t("ui.settings.large")][i], "text_size", i, int(setting("text_size", 1)) == i)
			y += 70
			for tg in TOGGLES.slice(3, 6):
				_toggle(Vector2(x, y), tg[0], tg[1])
				y += 60
		"data":
			var acc := Game.account
			text(Vector2(x, y + 30), Tx.t("ui.settings.account") % acc.account_id, 20, UiKit.MIST)
			text(Vector2(x, y + 64), Tx.t("ui.settings.characters_slots") % [Game.characters.size(), acc.slots_unlocked], 20, UiKit.MIST)
			btn(Rect2(x, y + 100, 260, 56), Tx.t("ui.settings.save_now"), "save", null, true)
			para(Rect2(x, y + 180, 900, 100), Tx.t("ui.settings.saves_are_written_every_few"), 18, UiKit.MIST)

func _toggle(p: Vector2, key: String, label: String) -> void:
	var on := bool(setting(key, key != "left_handed"))
	text(p + Vector2(0, 32), label, 22)
	var r := Rect2(p.x + 360, p.y + 6, 110, 44)
	draw_style_box(UiKit.style("button_secondary", "pressed" if on else "normal"), r)
	text(r.position + Vector2(0, 30), Tx.t("ui.settings.on") if on else Tx.t("ui.settings.off"), 20, UiKit.PALE_GOLD if on else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	region(r, "toggle", key)

func on_action(id: String, data) -> void:
	match id:
		"vol": set_setting(str(data[0]), float(data[1]))
		"toggle": set_setting(str(data), not bool(setting(str(data), str(data) != "left_handed")))
		"text_size": set_setting("text_size", int(data))
		"save":
			var err := Game.save_all()
			flash(Tx.t("ui.settings.saved") if err == OK else Tx.t("ui.settings.could_not_save_error") % err)
