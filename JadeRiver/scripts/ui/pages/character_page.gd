extends Page
## Character (S10, S11, S34): overview, stats with Combat Power, aptitude and titles.

const Avatar = preload("res://scripts/avatar.gd")
const STATS := [["max_hp", "Max HP"], ["max_qi", "Max QI"], ["max_soul", "Max Soul"], ["physical_attack", "Physical attack"],
	["qi_attack", "Qi attack"], ["physical_defense", "Physical defence"], ["qi_resistance", "Qi resistance"], ["accuracy", "Accuracy"],
	["evasion", "Evasion"], ["crit_chance", "Critical chance"], ["crit_damage", "Critical damage"], ["attack_speed", "Attack speed"],
	["move_speed", "Move speed"], ["hp_regen", "HP regen"], ["qi_regen", "QI regen"], ["drop_rate", "Drop rate"]]

var doll: Node2D

func _init() -> void:
	title = "Character"
	tabs = [{"id": "overview", "label": "Overview"}, {"id": "stats", "label": "Stats"}, {"id": "aptitude", "label": "Aptitude"}, {"id": "titles", "label": "Titles"}]

func setup() -> void:
	doll = Avatar.new()
	doll.outfit = InventoryAuthority.outfit_for(c())
	doll.position = Vector2(300, 520)
	doll.scale = Vector2.ONE * 2.4
	add_child(doll)

func _process(delta: float) -> void:
	super._process(delta)
	if is_instance_valid(doll): doll.visible = str(tabs[tab].id) == "overview"

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position, content.size)
	panel(r)
	match str(tabs[tab].id):
		"overview":
			var x := r.position.x + 480
			text(Vector2(x, r.position.y + 50), str(ch.name), 34, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
			text(Vector2(x, r.position.y + 86), ContentDB.realm_label(ch.cultivator.realm_key), 20, UiKit.GOLD)
			var sect_id := str(ch.training_sect.get("id", ""))
			text(Vector2(x, r.position.y + 116), (ContentDB.name_of("sects", sect_id) + " · " + str(ch.training_sect.get("rank", "")).replace("_", " ").capitalize()) if sect_id != "" else "Unaffiliated", 18, UiKit.MIST)
			text(Vector2(x, r.position.y + 150), "Origin: %s" % ContentDB.name_of("origins", ch.cultivator.origin), 18, UiKit.MIST)
			text(Vector2(x, r.position.y + 210), "Combat Power", 20, UiKit.MIST)
			text(Vector2(x, r.position.y + 256), UiKit.fmt(StatRules.combat_power(ch)), 44, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, -1, true)
			if ch.cultivator.active_title != "": text(Vector2(x, r.position.y + 300), "Title: %s" % ContentDB.name_of("titles", ch.cultivator.active_title), 19, UiKit.BRIGHT_JADE)
		"stats":
			for i in STATS.size():
				var s: Array = STATS[i]
				var col := i / 8
				var row := i % 8
				var v = ch.stats.value(s[0])
				var shown := UiKit.fmt(v) if absf(v) >= 10.0 or s[0] in ["max_hp", "max_qi", "max_soul"] else ("%.1f%%" % (v * 100.0) if s[0] in ["crit_chance", "crit_damage", "drop_rate"] else "%.2f" % v)
				text(Vector2(r.position.x + 40 + col * 520, r.position.y + 50 + row * 48), s[1], 20, UiKit.MIST)
				text(Vector2(r.position.x + 40 + col * 520, r.position.y + 50 + row * 48), shown, 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 440)
		"aptitude":
			var y := r.position.y + 40
			for k in ch.cultivator.aptitude:
				var a: Dictionary = ch.cultivator.aptitude[k]
				text(Vector2(r.position.x + 40, y), str(k).replace("_", " ").capitalize(), 21)
				text(Vector2(r.position.x + 400, y), str(a.get("value", "")).capitalize() if a.get("revealed", false) else "Unknown (revealed as you grow)", 20, UiKit.PALE_GOLD if a.get("revealed", false) else UiKit.HOLLOW)
				y += 44
		"titles":
			var titles: Array = ch.cultivator.titles
			if titles.is_empty(): text(r.position + Vector2(0, 80), "Earn titles from achievements and quests.", 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
			for i in titles.size():
				var tid := str(titles[i])
				var tr := Rect2(r.position.x + 30, r.position.y + 20 + i * 64, 600, 56)
				btn(tr, ContentDB.name_of("titles", tid), "title", tid, ch.cultivator.active_title == tid)

func on_action(id: String, data) -> void:
	if id == "title": submit({"type": "set_title", "title": str(data)})
