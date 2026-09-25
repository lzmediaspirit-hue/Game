extends Page
## Your own sect (S25): found it, build and upgrade, recruit NPC disciples and send
## expeditions. Timers run offline.

var name_field: LineEdit

func _init() -> void:
	title = Tx.t("ui.your_sect.your_sect")
	tabs = [{"id": "hall", "label": Tx.t("ui.your_sect.buildings")}, {"id": "disciples", "label": Tx.t("ui.your_sect.disciples")}, {"id": "expeditions", "label": Tx.t("ui.your_sect.expeditions")}]

func setup() -> void:
	if not Game.sect.founded():
		name_field = LineEdit.new()
		name_field.max_length = 20
		name_field.placeholder_text = Tx.t("ui.your_sect.sect_name")
		name_field.position = Vector2(440, 300)
		name_field.size = Vector2(400, 50)
		name_field.add_theme_font_override("font", UiKit.body_font())
		name_field.add_theme_font_size_override("font_size", 24)
		name_field.add_theme_stylebox_override("normal", UiKit.style("slot"))
		add_child(name_field)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var r := Rect2(content.position, content.size)
	panel(r)
	var s: Dictionary = Game.sect.sect()
	if s.is_empty():
		para(Rect2(r.position + Vector2(30, 30), Vector2(r.size.x - 60, 120)), Tx.t("ui.your_sect.the_hidden_vale_beyond_crane"), 22)
		btn(Rect2(540, 380, 200, 56), Tx.t("ui.your_sect.found"), "found", null, true, Unlocks.is_unlocked(ch.id, "your_sect"), Unlocks.locked_text("your_sect"))
		return
	text(r.position + Vector2(30, 44), Tx.t("ui.your_sect.level_prestige") % [str(s.name), int(s.level), UiKit.fmt(int(s.prestige))], 24, UiKit.PALE_GOLD)
	match str(tabs[tab].id):
		"hall":
			var bs: Array = ContentDB.all("sect_buildings")
			list("b", Rect2(r.position + Vector2(10, 64), r.size - Vector2(20, 74)), bs.size(), 70, func(i: int, rr: Rect2):
				var b: Dictionary = bs[i]
				var lv := Game.sect.level_building(str(b.id))
				var hurt: bool = s.get("damaged", {}).has(str(b.id))
				panel(rr, "minor_panel", "disabled" if hurt else "normal")
				text(rr.position + Vector2(20, 30), str(b.name), 20)
				text(rr.position + Vector2(20, 54), Tx.t("ui.your_sect.damaged_in_a_raid_output") if hurt else Tx.t("ui.your_sect.level_needs_sect_level") % [lv, int(b.get("sect_level", 1))], 15, UiKit.RED if hurt else UiKit.MIST)
				if hurt:
					btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 48), Tx.t("ui.your_sect.repair"), "repair", str(b.id), true)
					return
				var cost: Dictionary = Game.sect.building_cost(str(b.id), lv + 1)
				if not cost.is_empty(): text(rr.position + Vector2(360, 42), Tx.t("ui.your_sect.taels") % [UiKit.fmt(int(cost.get("silver_tael", 0))), "".join((cost.get("materials", {}) as Dictionary).keys().map(func(m): return " · %d %s" % [int(cost.materials[m]), ContentDB.item_name(str(m))]))], 16, UiKit.PALE_GOLD)
				btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 48), Tx.t("ui.your_sect.build") if lv == 0 else Tx.t("ui.your_sect.upgrade"), "upgrade", str(b.id))
			)
		"disciples":
			var cands: Array = s.get("candidates", [])
			var ds: Array = s.get("disciples", [])
			text(r.position + Vector2(30, 90), Tx.t("ui.your_sect.disciples_2") % ds.size(), 20)
			var y := r.position.y + 110
			for d in ds:
				text(Vector2(r.position.x + 30, y + 22), Tx.t("ui.your_sect.lv") % [str(d.get("name", "")), int(d.get("level", 1)), _traits(d)], 17)
				y += 30
			text(Vector2(r.position.x + 30, y + 30), Tx.t("ui.your_sect.candidates_today"), 20, UiKit.GOLD)
			y += 40
			for i in cands.size():
				var cd: Dictionary = cands[i]
				text(Vector2(r.position.x + 30, y + 30), Tx.t("ui.your_sect.strength_spirit_craft") % [str(cd.get("name", "")), int(cd.get("strength", 1)), int(cd.get("spirit", 1)), int(cd.get("craft", 1)), _traits(cd)], 17)
				btn(Rect2(r.end.x - 190, y + 4, 160, 44), Tx.t("ui.your_sect.recruit"), "recruit", i)
				y += 52
		"expeditions":
			var exs: Array = ContentDB.all("expeditions")
			var y2 := r.position.y + 80
			for e in exs:
				text(Vector2(r.position.x + 30, y2 + 24), Tx.t("ui.your_sect.danger") % [str(e.name), int(e.danger_level)], 18)
				var x := r.end.x - 20
				for h in e.get("hours", []):
					x -= 100
					btn(Rect2(x, y2, 90, 40), "%dh" % int(h), "send", [str(e.id), int(h)])
				y2 += 50
			for i in s.get("expeditions", []).size():
				var ex: Dictionary = s.expeditions[i]
				var left := int(float(ex.done_utc) - Clock.now_utc())
				text(Vector2(r.position.x + 30, y2 + 24), "%s: %s" % [ContentDB.name_of("expeditions", str(ex.region)), "back" if left <= 0 else Tx.t("ui.your_sect.dm_left") % (left / 60 + 1)], 17, UiKit.MIST)
				if left <= 0: btn(Rect2(r.end.x - 190, y2, 160, 40), Tx.t("ui.your_sect.collect"), "collect", i, true)
				y2 += 46

## Disciples carry one trait id (older saves may hold a list).
func _traits(d: Dictionary) -> String:
	var tr = d.get("trait", d.get("traits", []))
	var ids: Array = tr if tr is Array else [tr]
	return ", ".join(ids.map(func(t): return str(t).replace("_", " ").capitalize()))

func on_action(id: String, data) -> void:
	match id:
		"found":
			if name_field and submit({"type": "found_sect", "name": name_field.text.strip_edges()}).get("ok", false):
				name_field.queue_free()
				name_field = null
		"upgrade": submit({"type": "upgrade_building", "building": str(data)})
		"repair": submit({"type": "repair_building", "building": str(data)})
		"recruit": submit({"type": "recruit_disciple", "index": int(data)})
		"send":
			var ds: Array = Game.sect.sect().get("disciples", [])
			var ids: Array = []
			for d in ds.slice(0, 2): ids.append(d.get("id", d.get("name", "")))
			submit({"type": "send_expedition", "region": str(data[0]), "hours": int(data[1]), "disciples": ids})
		"collect": submit({"type": "collect_expedition", "index": int(data)})
