extends Page
## S45 · The herb garden: the beds in this room, each with its field grade, the herb in it, its age and growth.
## Plant a seed, water with bottled spring water, work in Spirit Soil, pour a drop of dew, harvest. Growth runs
## on the clock, so beds keep growing while you are away.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.garden.title")

func setup() -> void:
	var obj := str(args.get("object", ""))
	if obj != "" and Game.room_rt: sel = Game.room_rt.room_id + ":" + obj

func draw_page() -> void:
	var ch = c()
	if ch == null or Game.room_rt == null: return
	var keys: Array = Game.crafting.room_beds(ch, Game.room_rt.room_id)
	if keys.is_empty():
		para(Rect2(content.position + Vector2(20, 30), Vector2(content.size.x - 40, 80)), Tx.t("ui.garden.no_beds"), 20, UiKit.MIST)
		return
	if not sel in keys: sel = str(keys[0])
	_supplies(ch, Rect2(content.position, Vector2(content.size.x, 56)))
	var top := content.position.y + 66
	var gap := 16.0
	var n := keys.size()
	var cw := minf(360.0, (content.size.x - gap * (n - 1)) / float(n))
	var left := content.position.x + (content.size.x - (cw * n + gap * (n - 1))) * 0.5
	for i in n:
		_bed_card(ch, str(keys[i]), Rect2(left + i * (cw + gap), top, cw, 300), i)
	_actions(ch, Rect2(content.position.x, top + 316, content.size.x, content.end.y - top - 316), keys.find(sel) + 1)

## Spring water, Spirit Soil and the Verdant Dew Vial across the top.
func _supplies(ch, r: Rect2) -> void:
	panel(r)
	var x := r.position.x + 18
	for id in ["spring_water", "spirit_soil"]:
		icon_at(Rect2(x, r.position.y + 10, 36, 36), id)
		text(Vector2(x + 44, r.position.y + 35), "%s × %d" % [ContentDB.item_name(id), ch.inventory.count(id)], 18, UiKit.PAPER)
		x += 320
	var ds: Dictionary = Game.crafting.dew_state(ch)
	if ds.has:
		icon_at(Rect2(x, r.position.y + 10, 36, 36), "verdant_dew_vial")
		var dew := Tx.t("ui.garden.dew") % [int(ds.dew), int(ds.cap)]
		if int(ds.dew) < int(ds.cap): dew += "  ·  " + Tx.t("ui.garden.next_dew") % UiKit.clock(float(ds.next_s))
		text(Vector2(x + 44, r.position.y + 35), dew, 18, UiKit.BRIGHT_JADE)

func _bed_card(ch, key: String, r: Rect2, i: int) -> void:
	var v: Dictionary = Game.crafting.bed_view(ch, key)
	panel(r, "minor_panel", "selected" if key == sel else "normal")
	if key == sel: draw_rect(r.grow(-4), Color(UiKit.GOLD, 0.8), false, 2.0)
	region(r, "sel", key)
	text(r.position + Vector2(18, 32), Tx.t("ui.garden.bed") % (i + 1), 21, UiKit.PALE_GOLD)
	var grade := Tx.t("ui.garden.grade_" + str(v.grade))
	text(Vector2(r.end.x - 178, r.position.y + 32), grade, 17, UiKit.GOLD if str(v.grade) != "low" else UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 160)
	var cap := str(ContentDB.config("garden").get("field_cap", {}).get(str(v.grade), "earth"))
	text(r.position + Vector2(18, 56), Tx.t("ui.garden.grows_up_to") % cap.capitalize(), 15, UiKit.MIST)
	if str(v.herb) == "":
		para(Rect2(r.position + Vector2(18, 100), Vector2(r.size.x - 36, 80)), Tx.t("ui.garden.empty"), 18, UiKit.MIST, 3)
		return
	slot_box(Rect2(r.position.x + 18, r.position.y + 76, 72, 72), str(v.herb))
	para(Rect2(r.position + Vector2(102, 82), Vector2(r.size.x - 120, 50)), ContentDB.item_name(str(v.herb)), 18, UiKit.PAPER, 2)
	text(r.position + Vector2(102, 144), Tx.t("ui.garden.age") % int(v.age), 16, UiKit.GOLD if int(v.age) >= 100 else UiKit.MIST)
	var frac := float(v.progress)
	bar(Rect2(r.position.x + 18, r.position.y + 170, r.size.x - 36, 30), frac, UiKit.BRIGHT_JADE if frac >= 1.0 else UiKit.JADE,
		Tx.t("ui.garden.ready") if v.ready else "%d%%" % int(frac * 100.0))
	if not v.ready: text(r.position + Vector2(18, 226), Tx.t("ui.garden.ready_in") % UiKit.clock(float(v.seconds)), 16, UiKit.MIST)

## What can be done with the selected bed.
func _actions(ch, r: Rect2, n: int) -> void:
	panel(r)
	var v: Dictionary = Game.crafting.bed_view(ch, sel)
	var head := Tx.t("ui.garden.bed") % n + "  ·  " + (ContentDB.item_name(str(v.herb)) if str(v.herb) != "" else Tx.t("ui.garden.empty_short"))
	text(r.position + Vector2(18, 32), head, 19, UiKit.PALE_GOLD)
	text(Vector2(r.end.x - 418, r.position.y + 32), Tx.t("ui.garden.tap_a_bed"), 15, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, 400)
	var x := r.position.x + 18
	var y := r.position.y + 52
	var h := 50.0
	if str(v.herb) == "":
		text(Vector2(x, y + 32), Tx.t("ui.garden.plant"), 18, UiKit.PAPER)
		x += 140
		var any := false
		for s in ch.inventory.bag:
			if s == null or str(ContentDB.item(str(s.id)).get("type", "")) != "seed": continue
			any = true
			slot_box(Rect2(x, y, h, h), str(s.id), int(s.get("count", 1)), "", "plant", str(s.id))
			x += h + 10
		if not any: para(Rect2(Vector2(x, y + 8), Vector2(r.end.x - x - 18, h)), Tx.t("ui.garden.no_seeds"), 17, UiKit.MIST, 2)
	else:
		var w := 210.0
		btn(Rect2(x, y, w, h), Tx.t("ui.garden.harvest"), "harvest", sel, true, bool(v.ready), Tx.t("ui.garden.not_ready"), 19)
		x += w + 14
		btn(Rect2(x, y, w, h), Tx.t("ui.garden.water") % ch.inventory.count("spring_water"), "water", sel, false,
			not v.ready and ch.inventory.count("spring_water") > 0, Tx.t("ui.garden.need_water"), 19)
		x += w + 14
		var ds: Dictionary = Game.crafting.dew_state(ch)
		if ds.has:
			btn(Rect2(x, y, w, h), Tx.t("ui.garden.pour_dew"), "dew", sel, false, int(ds.dew) > 0, Tx.t("ui.garden.no_dew"), 19)
			x += w + 14
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	if str(v.grade) != str(grades.back()):
		btn(Rect2(r.end.x - 250, y, 232, h), Tx.t("ui.garden.soil"), "soil", sel, false, ch.inventory.count("spirit_soil") > 0, Tx.t("ui.garden.need_soil"), 19)

func on_action(id: String, data) -> void:
	match id:
		"sel": sel = str(data)
		"plant": submit({"type": "plant_seed", "bed": sel, "seed": str(data)})
		"water": submit({"type": "water_bed", "bed": str(data)})
		"harvest":
			var r := submit({"type": "harvest_bed", "bed": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.garden.harvested") % [ContentDB.item_name(str(r.item)), int(r.count)])
		"dew": submit({"type": "use_dew", "bed": str(data)})
		"soil": submit({"type": "apply_spirit_soil", "bed": str(data)})
	queue_redraw()
