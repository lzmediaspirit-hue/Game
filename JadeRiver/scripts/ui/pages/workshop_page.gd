extends Page
## Workshop (S16): the crafts that are not station recipes. Formations, appraisal,
## the infirmary, the puppet bench, manual restoration and teaching. Each tab
## unlocks with its system; the NPC who opened the page picks the tab.

var TABS := [["formations", Tx.t("ui.workshop.formations"), "formations"], ["appraisal", Tx.t("ui.workshop.appraisal"), "appraisal"], ["healing", Tx.t("ui.workshop.infirmary"), "healing"],
	["puppetry", Tx.t("ui.workshop.puppets"), "puppetry"], ["research", Tx.t("ui.workshop.research"), "research"], ["teaching", Tx.t("ui.workshop.teaching"), "teaching"]]
const NPC_TAB := {"elder_gu": "appraisal", "old_pan": "appraisal", "tinkerer_yu": "puppetry", "jade_librarian": "research",
	"cloud_librarian": "research", "jade_physician": "healing", "cloud_physician": "healing", "jade_formation_elder": "formations",
	"cloud_formation_elder": "formations", "elder_hu": "teaching", "elder_sung": "teaching"}

func _init() -> void:
	title = Tx.t("ui.workshop.workshop")

func setup() -> void:
	var ch = c()
	tabs = []
	for tb in TABS:
		tabs.append({"id": tb[0], "label": tb[1], "locked": "" if Unlocks.is_unlocked(ch.id, tb[2]) else Unlocks.locked_text(tb[2])})
	var want := str(args.get("tab", NPC_TAB.get(str(args.get("npc", "")), "formations" if page_id == "formations" else "")))
	tab = 0
	for i in tabs.size():
		if str(tabs[i].id) == want:
			tab = i
			return
	for i in tabs.size():
		if str(tabs[i].locked) == "":
			tab = i
			return

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	if str(tabs[tab].get("locked", "")) != "":
		para(Rect2(content.position + Vector2(30, 30), content.size - Vector2(60, 60)), str(tabs[tab].locked), 21, UiKit.MIST)
		return
	match str(tabs[tab].id):
		"formations": _formations(ch)
		"appraisal": _appraisal(ch)
		"healing": _healing(ch)
		"puppetry": _puppets(ch)
		"research": _research(ch)
		"teaching": _teaching(ch)

func _rank_line(ch, craft: String, pos: Vector2) -> void:
	var p: Dictionary = ch.professions.get(craft, {"rank": "apprentice", "xp": 0})
	text(pos, "%s · %s" % [str(p.rank).capitalize(), UiKit.fmt(float(p.xp))], 16, UiKit.MIST)

func _formations(ch) -> void:
	var left := Rect2(content.position, Vector2(560, content.size.y))
	panel(left)
	heading(left.position + Vector2(20, 44), Tx.t("ui.workshop.blueprints"), 520)
	var rows := ContentDB.all("formations")
	# Blueprints scroll once there are more than fit (five in the valley).
	list("blueprints", Rect2(left.position.x + 14, left.position.y + 70, left.size.x - 28, left.size.y - 100), rows.size(), 128, func(i: int, rr: Rect2):
		var bp: Dictionary = rows[i]
		var ok := Unlocks.is_unlocked(ch.id, str(bp.get("unlock", "formations")))
		var r := Rect2(rr.position, Vector2(rr.size.x, 118))
		panel(r, "minor_panel")
		text(r.position + Vector2(16, 32), str(bp.name), 21, UiKit.PAPER if ok else UiKit.MIST)
		para(Rect2(r.position + Vector2(16, 42), Vector2(330, 60)), str(bp.get("desc", "")), 16, UiKit.MIST, 2)
		var need := int(bp.get("nodes", 3)) * int(bp.get("fuel_per_node", 1))
		text(r.position + Vector2(16, 108), Tx.t("ui.workshop.nodes") % [int(bp.nodes), need, ContentDB.item_name(str(bp.fuel))], 15, UiKit.PALE_GOLD)
		btn(Rect2(r.end.x - 160, r.position.y + 34, 144, 50), Tx.t("ui.workshop.place"), "place", str(bp.id), true, ok, Unlocks.locked_text(str(bp.get("unlock", "formations"))))
	)
	_rank_line(ch, "formations", Vector2(left.position.x + 16, left.end.y - 14))
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(20, 44), Tx.t("ui.workshop.standing_formations"), right.size.x - 40)
	var live: Array = Game.workshop.active_formations(ch)
	if live.is_empty():
		para(Rect2(right.position + Vector2(24, 70), right.size - Vector2(48, 90)), Tx.t("ui.workshop.none_stand_where_you_cultivate"), 18, UiKit.MIST)
	var yy := right.position.y + 70
	for i in live.size():
		var f: Dictionary = live[i]
		var hours := maxf(0.0, (float(f.until_utc) - Clock.now_utc()) / 3600.0)
		var r2 := Rect2(right.position.x + 14, yy, right.size.x - 28, 70)
		panel(r2, "minor_panel")
		text(r2.position + Vector2(14, 30), str(ContentDB.entry("formations", str(f.type)).get("name", f.type)), 19)
		text(r2.position + Vector2(14, 56), Tx.t("ui.workshop.1f_h_of_fuel") % [ContentDB.room(str(f.room)).get("name", f.room), hours], 15, UiKit.MIST)
		btn(Rect2(r2.end.x - 120, r2.position.y + 12, 106, 46), Tx.t("ui.workshop.dispel"), "dispel", i)
		yy += 80

func _appraisal(ch) -> void:
	var r := Rect2(content.position, content.size)
	panel(r)
	heading(r.position + Vector2(20, 44), Tx.t("ui.workshop.unknown_goods"), r.size.x - 40)
	var has_tool: bool = Game.crafting.tool_power(ch, "appraisal") > 0.0
	para(Rect2(r.position + Vector2(24, 60), Vector2(r.size.x - 48, 60)),
		Tx.t("ui.workshop.look_closely_real_jade_is") + (Tx.t("ui.workshop.your_loupe_is_ready") if has_tool else Tx.t("ui.workshop.you_need_an_appraiser_loupe")), 18, UiKit.MIST)
	var items: Array = []
	for i in ch.inventory.bag.size():
		var s = ch.inventory.bag[i]
		if s != null and str(ContentDB.item(str(s.id)).get("use_action", "")) == "appraise": items.append(i)
	if items.is_empty():
		para(Rect2(r.position + Vector2(24, 140), Vector2(r.size.x - 48, 60)), Tx.t("ui.workshop.nothing_to_appraise_curios_turn"), 18, UiKit.MIST)
	var x := r.position.x + 24
	for idx in items:
		var s2: Dictionary = ch.inventory.bag[idx]
		slot_box(Rect2(x, r.position.y + 140, 84, 84), str(s2.id), int(s2.get("count", 1)))
		btn(Rect2(x - 6, r.position.y + 234, 96, 46), Tx.t("ui.workshop.appraise"), "appraise", idx, true, has_tool, Tx.t("ui.workshop.needs_a_loupe"))
		x += 110
	_rank_line(ch, "appraisal", Vector2(r.position.x + 16, r.end.y - 14))

func _healing(ch) -> void:
	var r := Rect2(content.position, content.size)
	panel(r)
	heading(r.position + Vector2(20, 44), Tx.t("ui.workshop.the_infirmary"), r.size.x - 40)
	var p := ContentDB.entry("professions", "healing")
	var h: Dictionary = ch.crafting.get("healing", {})
	var today := Clock.reset_day(Clock.now_utc())
	var treated := int(h.get("treated", 0)) if int(h.get("day", -1)) == today else 0
	var left := int(p.get("patients_per_day", 5)) - treated
	para(Rect2(r.position + Vector2(24, 64), Vector2(r.size.x - 48, 90)),
		Tx.t("ui.workshop.guide_your_qi_through_the") % [int(float(p.get("qi_cost_pct", 0.15)) * 100), int(p.get("contribution", 20)), maxi(0, left)], 18)
	var here: bool = Game.workshop.npc_here(ch, p.get("npcs", []))
	btn(Rect2(r.position.x + 24, r.position.y + 170, 260, 56), Tx.t("ui.workshop.treat_a_patient"), "treat", null, true, here and left > 0, Tx.t("ui.workshop.patients_wait_in_the_sect") if not here else Tx.t("ui.workshop.no_more_patients_today"))
	_rank_line(ch, "healing", Vector2(r.position.x + 16, r.end.y - 14))

func _puppets(ch) -> void:
	var p := ContentDB.entry("professions", "puppetry")
	var left := Rect2(content.position, Vector2(560, content.size.y))
	panel(left)
	heading(left.position + Vector2(20, 44), Tx.t("ui.workshop.blueprints"), 520)
	var here: bool = Game.workshop.npc_here(ch, p.get("npcs", []))
	var y := left.position.y + 70
	for b in p.get("blueprints", []):
		var r := Rect2(left.position.x + 14, y, left.size.x - 28, 130)
		panel(r, "minor_panel")
		text(r.position + Vector2(16, 32), str(b.name), 21)
		var need := ""
		for inp in b.inputs: need += "%d %s  " % [int(inp.count), ContentDB.item_name(str(inp.item))]
		text(r.position + Vector2(16, 60), need, 15, UiKit.PALE_GOLD)
		var yl := ""
		for yy in b.get("yield", []): yl += "%d %s/h  " % [int(yy.per_hour), ContentDB.item_name(str(yy.item))]
		text(r.position + Vector2(16, 88), Tx.t("ui.workshop.gathers") + yl, 15, UiKit.MIST)
		btn(Rect2(r.end.x - 160, r.position.y + 40, 144, 50), Tx.t("ui.workshop.build"), "build", str(b.id), true, here, Tx.t("ui.workshop.build_at_tinkerer_yu_bench"))
		y += 140
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	heading(right.position + Vector2(20, 44), Tx.t("ui.workshop.your_puppets"), right.size.x - 40)
	var ps: Array = ch.crafting.get("puppets", [])
	var yy2 := right.position.y + 70
	for pu in ps:
		text(Vector2(right.position.x + 24, yy2 + 20), str(Game.workshop.blueprint(str(pu.blueprint)).get("name", pu.blueprint)), 19)
		yy2 += 34
	var got: Array = Game.workshop.puppet_yield(ch)
	var summary := ""
	for g in got: summary += "%d %s  " % [int(g.count), ContentDB.item_name(str(g.item))]
	para(Rect2(right.position.x + 24, yy2 + 10, right.size.x - 48, 80), Tx.t("ui.workshop.waiting") + (summary if summary != "" else Tx.t("ui.workshop.nothing_yet")), 17, UiKit.MIST)
	btn(Rect2(right.position.x + 24, right.end.y - 80, 220, 54), Tx.t("ui.workshop.collect"), "collect", null, true, not got.is_empty(), Tx.t("ui.workshop.nothing_gathered_yet"))
	_rank_line(ch, "puppetry", Vector2(left.position.x + 16, left.end.y - 14))

func _research(ch) -> void:
	var p := ContentDB.entry("professions", "research")
	var r := Rect2(content.position, content.size)
	panel(r)
	heading(r.position + Vector2(20, 44), Tx.t("ui.workshop.restore_a_damaged_manual"), r.size.x - 40)
	para(Rect2(r.position + Vector2(24, 64), Vector2(r.size.x - 48, 90)), Tx.t("ui.workshop.water_worms_and_time_eat"), 18, UiKit.MIST)
	var x := r.position.x + 24
	for inp in p.get("inputs", []):
		slot_box(Rect2(x, r.position.y + 150, 84, 84), str(inp.item), ch.inventory.count(str(inp.item)))
		text(Vector2(x, r.position.y + 256), Tx.t("ui.workshop.need") % int(inp.count), 15, UiKit.MIST)
		x += 110
	var here: bool = Game.workshop.npc_here(ch, p.get("npcs", []))
	btn(Rect2(r.position.x + 24, r.position.y + 290, 240, 56), Tx.t("ui.workshop.restore"), "restore", null, true, here, Tx.t("ui.workshop.use_the_library_bench"))
	_rank_line(ch, "research", Vector2(r.position.x + 16, r.end.y - 14))

func _teaching(ch) -> void:
	var r := Rect2(content.position, content.size)
	panel(r)
	heading(r.position + Vector2(20, 44), Tx.t("ui.workshop.teach_your_sect_disciples"), r.size.x - 40)
	var daos: Array = Game.workshop.teachable_daos(ch)
	if not Game.sect.founded():
		para(Rect2(r.position + Vector2(24, 64), Vector2(r.size.x - 48, 90)), Tx.t("ui.workshop.found_your_own_sect_first"), 18, UiKit.MIST)
		return
	para(Rect2(r.position + Vector2(24, 64), Vector2(r.size.x - 48, 60)),
		(Tx.t("ui.workshop.you_can_teach") + ", ".join(daos.map(func(d): return ContentDB.name_of("daos", str(d))))) if not daos.is_empty() else Tx.t("ui.workshop.reach_explanation_in_a_dao"), 18, UiKit.MIST)
	var ds: Array = Game.account.sect.get("disciples", [])
	list("teach", Rect2(r.position + Vector2(16, 130), Vector2(r.size.x - 32, r.size.y - 170)), ds.size(), 64, func(i: int, rr: Rect2):
		var d: Dictionary = ds[i]
		panel(rr, "minor_panel")
		text(rr.position + Vector2(16, 38), Tx.t("ui.workshop.lv") % [str(d.get("name", Tx.t("ui.workshop.disciple"))), int(d.get("level", 1))], 19)
		btn(Rect2(rr.end.x - 150, rr.position.y + 7, 136, 48), Tx.t("ui.workshop.teach"), "teach", i, true, not daos.is_empty(), Tx.t("ui.workshop.no_dao_at_explanation"))
	)

func on_action(id: String, data) -> void:
	match id:
		"place":
			var r := submit({"type": "place_formation", "formation": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.workshop.formation_placed_h_of_fuel") % int(r.get("hours", 0)))
		"dispel": submit({"type": "remove_formation", "index": int(data)})
		"appraise":
			var r2 := submit({"type": "appraise_item", "index": int(data)})
			if r2.get("ok", false): flash(str(r2.get("text", "")))
		"treat":
			var r3 := submit({"type": "treat_patient"})
			if r3.get("ok", false): flash(str(r3.get("text", "")))
		"build":
			if submit({"type": "build_puppet", "blueprint": str(data)}).get("ok", false): flash(Tx.t("ui.workshop.the_puppet_stirs_and_sets"))
		"collect": submit({"type": "collect_puppets"})
		"restore":
			var r4 := submit({"type": "restore_manual"})
			if r4.get("ok", false): flash(str(r4.get("text", "")))
		"teach":
			var r5 := submit({"type": "teach_disciple", "index": int(data)})
			if r5.get("ok", false): flash(Tx.t("ui.workshop.lesson_given"))
	queue_redraw()
