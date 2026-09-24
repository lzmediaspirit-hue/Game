extends Page
## Settings (S35, Part 9.6): audio, controls, display, accessibility, notifications, data.

const SLIDERS := [["music", "Music"], ["ambience", "Ambience"], ["sfx", "Effects"], ["ui", "Interface"]]
const TOGGLES := [["left_handed", "Left-handed controls"], ["screen_shake", "Screen shake"], ["damage_numbers", "Damage numbers"],
	["notifications", "Notifications"], ["minimap", "Show minimap"], ["auto_pickup", "Auto pick-up"]]

func _init() -> void:
	title = "Settings"
	tabs = [{"id": "audio", "label": "Audio"}, {"id": "controls", "label": "Controls"}, {"id": "access", "label": "Accessibility"}, {"id": "data", "label": "Data"}]

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
			para(Rect2(x, y + 20, 900, 120), "Keyboard: arrows/WASD move · Space jump · J attack or talk · F interact · K guard (tap to dodge) · C cultivate (hold for the Cultivation page) · Q quick-use · 1–8 techniques · Tab menu · I bag · M map · L quests.", 18, UiKit.MIST)
		"access":
			text(Vector2(x, y + 32), "Text size", 22)
			for i in 3:
				btn(Rect2(x + 220 + i * 150, y + 4, 140, 50), ["Small", "Normal", "Large"][i], "text_size", i, int(setting("text_size", 1)) == i)
			y += 70
			for tg in TOGGLES.slice(3, 6):
				_toggle(Vector2(x, y), tg[0], tg[1])
				y += 60
		"data":
			var acc := Game.account
			text(Vector2(x, y + 30), "Account: %s" % acc.account_id, 20, UiKit.MIST)
			text(Vector2(x, y + 64), "Characters: %d / %d slots" % [Game.characters.size(), acc.slots_unlocked], 20, UiKit.MIST)
			btn(Rect2(x, y + 100, 260, 56), "Save now", "save", null, true)
			para(Rect2(x, y + 180, 900, 100), "Saves are written every few seconds and when the app is paused. A backup of each file is kept and used automatically if a save is damaged.", 18, UiKit.MIST)

func _toggle(p: Vector2, key: String, label: String) -> void:
	var on := bool(setting(key, key != "left_handed"))
	text(p + Vector2(0, 32), label, 22)
	var r := Rect2(p.x + 360, p.y + 6, 110, 44)
	draw_style_box(UiKit.style("button_secondary", "pressed" if on else "normal"), r)
	text(r.position + Vector2(0, 30), "On" if on else "Off", 20, UiKit.PALE_GOLD if on else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	region(r, "toggle", key)

func on_action(id: String, data) -> void:
	match id:
		"vol": set_setting(str(data[0]), float(data[1]))
		"toggle": set_setting(str(data), not bool(setting(str(data), str(data) != "left_handed")))
		"text_size": set_setting("text_size", int(data))
		"save":
			var err := Game.save_all()
			flash("Saved." if err == OK else "Could not save (error %d)." % err)
