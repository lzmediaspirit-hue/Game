extends Page
## Your own sect (S25): found it, build and upgrade, recruit NPC disciples and send
## expeditions. Timers run offline. S49 territory: the spirit-stone mines your sect holds or could take.

var name_field: LineEdit

func _init() -> void:
	title = Tx.t("ui.your_sect.your_sect")
	tabs = [{"id": "hall", "label": Tx.t("ui.your_sect.buildings")}, {"id": "disciples", "label": Tx.t("ui.your_sect.disciples")}, {"id": "expeditions", "label": Tx.t("ui.your_sect.expeditions")},
		{"id": "territory", "label": Tx.t("ui.your_sect.territory")}]

func setup() -> void:
	if not Game.sect.founded():
		name_field = LineEdit.new()
		name_field.max_length = 20
		name_field.placeholder_text = Tx.t("ui.your_sect.sect_name")
		name_field.position = Vector2(440, 300)
		name_field.size = Vector2(400, 50)
		name_field.add_theme_font_override("font", UiKit.text_font())
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
				text(Vector2(r.position.x + 30, y2 + 24), "%s: %s" % [ContentDB.name_of("expeditions", str(ex.region)), Tx.t("ui.your_sect.back") if left <= 0 else Tx.t("ui.your_sect.dm_left") % (left / 60 + 1)], 17, UiKit.MIST)
				if left <= 0: btn(Rect2(r.end.x - 190, y2, 160, 40), Tx.t("ui.your_sect.collect"), "collect", i, true)
				y2 += 46
		"territory":
			_draw_territory(r, s)

## S49 territory: every mine, who holds it, what waits in its carts, and when its old holder comes back.
func _draw_territory(r: Rect2, s: Dictionary) -> void:
	text(Vector2(r.position.x, r.position.y + 44), Tx.t("ui.your_sect.mines_held") % [Game.sect.mines().size(), Game.sect.mine_cap()], 18, UiKit.MIST,
		HORIZONTAL_ALIGNMENT_RIGHT, r.size.x - 30)
	var ms: Array = ContentDB.all("territory")
	var now := Clock.now_utc()
	var cap_h := float(ContentDB.config("territory").get("cap_hours", 24))
	var max_guards := int(ContentDB.config("territory").get("contest", {}).get("max_guards", 3))
	list("mines", Rect2(r.position + Vector2(10, 64), r.size - Vector2(20, 74)), ms.size(), 104, func(i: int, rr: Rect2):
		var m: Dictionary = ms[i]
		var id := str(m.id)
		var mine: bool = Game.sect.holds(id)
		var st: Dictionary = Game.sect.mines().get(id, {})
		var contested := bool(st.get("contested", false))
		panel(rr, "minor_panel", "selected" if contested else "normal")
		# The banner that flies over it: yours, or the holder's.
		var rv: Dictionary = Game.sect.rival(str(m.sect))
		var banner := "banner_your_sect" if mine else str(rv.get("banner", ""))
		var e := SpriteCache.prop(banner)
		var tx: Texture2D = SpriteCache.tex(str(e.get("file", ""))) if not e.is_empty() else null
		if tx: draw_texture_rect_region(tx, Rect2(rr.position + Vector2(14, 8), Vector2(48, 88)), Rect2(0, 4, 48, 88))
		var x0 := rr.position.x + 80
		text(Vector2(x0, rr.position.y + 28), str(m.name), 21, UiKit.PALE_GOLD if mine else UiKit.PAPER)
		var rate := Tx.t("ui.your_sect.rate_one") if int(m.rate) == 1 else Tx.t("ui.your_sect.rate") % int(m.rate)
		text(Vector2(x0, rr.position.y + 50), Tx.t("ui.your_sect.mine_meta") % [ContentDB.name_of("rooms", str(m.room)), int(m.level), rate,
			int(m.get("sect_level", 1))], 15, UiKit.MIST)
		if mine:
			var cap := int(cap_h * float(m.rate))
			var stored := Game.sect.mine_stored(id, now)
			text(Vector2(x0, rr.position.y + 74), Tx.t("ui.your_sect.mine_yours") % [stored, cap], 17, UiKit.BRIGHT_JADE)
			var when := Tx.t("ui.your_sect.mine_contested") % [str(rv.get("name", "")), _span(float(st.until) - now)] if contested \
				else Tx.t("ui.your_sect.mine_next") % _span(float(st.get("contest", now)) - now)
			text(Vector2(x0 + 250, rr.position.y + 74), when, 16, UiKit.RED if contested else UiKit.MIST)
			var gs: Array = st.get("guards", [])
			var names: Array = gs.map(func(d): return str(s.disciples[int(d)].get("name", "")) if int(d) < s.disciples.size() else "")
			text(Vector2(x0, rr.position.y + 95), Tx.t("ui.your_sect.mine_guards") % [", ".join(names) if not names.is_empty() else Tx.t("ui.your_sect.no_guards"),
				int(round(Game.sect.guard_chance(id) * 100.0))], 14, UiKit.MIST)
			btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.collect"), "mine_collect", id, stored > 0, stored > 0)
			var free := _free_disciple()
			if gs.size() < max_guards:
				btn(Rect2(rr.end.x - 330, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.post_guard"), "mine_guard", [id, free], false, free >= 0,
					Tx.t("ui.your_sect.no_free_disciple"))
			if not gs.is_empty():
				btn(Rect2(rr.end.x - 330, rr.position.y + 56, 150, 42), Tx.t("ui.your_sect.recall_guard"), "mine_guard", [id, int(gs[gs.size() - 1])])
			if contested: btn(Rect2(rr.end.x - 170, rr.position.y + 56, 150, 42), Tx.t("ui.your_sect.go"), "mine_go", str(m.room), true)
		else:
			text(Vector2(x0, rr.position.y + 74), Tx.t("ui.your_sect.mine_held_by") % str(rv.get("name", "")), 17, Color(str(rv.get("color", "#AFC9D1"))).lightened(0.35))
			para(Rect2(x0, rr.position.y + 80, rr.size.x - 300, 22), str(rv.get("desc", "")), 14, UiKit.MIST, 1)
			var why: String = Game.sect.assault_block(c(), id)
			btn(Rect2(rr.end.x - 170, rr.position.y + 8, 150, 42), Tx.t("ui.your_sect.go"), "mine_go", str(m.room), why == "", true)
			if why != "": text(Vector2(rr.end.x - 360, rr.position.y + 74), why, 14, UiKit.RED, HORIZONTAL_ALIGNMENT_RIGHT, 340)
	)

## The first disciple free to stand guard (not away on an expedition, not guarding another mine), or -1.
func _free_disciple() -> int:
	var busy := Game.sect.guarding()
	var ds: Array = Game.sect.sect().get("disciples", [])
	for i in ds.size():
		if busy.has(i) or Game.sect._on_expedition(i): continue
		return i
	return -1

func _span(sec: float) -> String:
	var m := int(ceil(maxf(0.0, sec) / 60.0))
	if m >= 1440: return Tx.t("ui.calendar.span_dh") % [m / 1440, (m % 1440) / 60]
	if m >= 60: return Tx.t("ui.calendar.span_hm") % [m / 60, m % 60]
	return Tx.t("ui.calendar.span_m") % maxi(1, m)

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
			# Up to two disciples who are home: not away on another expedition, not guarding a mine.
			var busy := Game.sect.guarding()
			var ids: Array = []
			for i in Game.sect.sect().get("disciples", []).size():
				if ids.size() < 2 and not busy.has(i) and not Game.sect._on_expedition(i): ids.append(i)
			submit({"type": "send_expedition", "region": str(data[0]), "hours": int(data[1]), "disciples": ids})
		"collect": submit({"type": "collect_expedition", "index": int(data)})
		"mine_collect": submit({"type": "collect_mine", "mine": str(data)})
		"mine_guard": submit({"type": "guard_mine", "mine": str(data[0]), "index": int(data[1])})
		"mine_go":
			if submit({"type": "auto_path", "target": str(data)}).get("ok", false): close()
