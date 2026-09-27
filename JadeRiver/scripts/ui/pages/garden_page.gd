extends Page
## S45 · The herb garden: the beds in this room, each with its field grade, the herb in it, its age and growth.
## Plant a seed, water with bottled spring water, work in Spirit Soil, pour a drop of dew, harvest. Growth runs
## on the clock, so beds keep growing while you are away.
## P5 (docs/page_identity.md row 29): terraced herb beds on the hillside, seen from above. The beds step down the page
## on their stone walls, each herb drawn at its stage with its field's grade on a stake; the water, Spirit Soil and dew
## wait in a basket at the top; the chosen bed's tending on a board at the right. The Racks tab is two drying racks with
## their woven trays over the hillside.

var sel := ""
var rack_herb := ""
var rack_kind := "steamed"
var rack_count := 5

## The hillside inside the window, the terraces' span, the tending board and the basket at the top.
const HILL := Rect2(64, 32, 1152, 656)
const TERRACES := Rect2(96, 188, 744, 484)
const TEND := Rect2(856, 188, 328, 484)
const BASKET := Rect2(376, 108, 760, 68)
## How rich each field's soil looks: the better the field, the darker and wetter its earth.
const RICH := {"low": 0.0, "mid": 0.5, "high": 1.0}

func _init() -> void:
	title = Tx.t("ui.garden.title")
	tabs = [{"id": "beds", "label": Tx.t("ui.garden.beds")}, {"id": "racks", "label": Tx.t("ui.garden.racks")}]
	identity = Identity.new("soil", false, "own", "terraces_stepping_down", 0.3)

func setup() -> void:
	var obj := str(args.get("object", ""))
	if obj != "" and Game.room_rt: sel = Game.room_rt.room_id + ":" + obj

func content_rect() -> Rect2:
	return Rect2(TERRACES.position.x, TERRACES.position.y, TEND.end.x - TERRACES.position.x, TERRACES.size.y)

## The hillside: earth under a green cast, darker toward the foot, with a beam along the top for the tags.
func draw_surface(r: Rect2) -> void:
	var top: Color = UiKit.SURFACE.soil.lerp(UiKit.JADE_SHADOW, 0.35)
	rounded(r.grow(2), 8.0, UiKit.INK)
	vshade(r, top, UiKit.SURFACE.soil)
	ground(r, top)
	for i in 40:
		var p := r.position + Vector2(fposmod(i * 197.0, r.size.x - 24) + 12, fposmod(i * 131.0, r.size.y - 24) + 12)
		draw_line(p, p + Vector2(-3, -7), Color(UiKit.JADE, 0.35), 2.0, true)
		draw_line(p, p + Vector2(3, -6), Color(UiKit.JADE, 0.35), 2.0, true)
	WorkshopKit.beam(self, r.position.x + 20, BASKET.position.x - 16, 102)

func draw_title_mount(r: Rect2) -> void:
	face(r, "timber_sign")

func title_rect() -> Rect2:
	return Rect2(HILL.position.x + 24, HILL.position.y + 12, 300, 56)

func tab_rects() -> Array:
	return [Rect2(104, 116, 120, 48), Rect2(240, 116, 120, 48)]

func draw_tab(r: Rect2, i: int, state: String) -> void:
	WorkshopKit.tag_tab(self, r, str(tabs[i].label), state)

func draw_page() -> void:
	var ch = c()
	if ch == null or Game.room_rt == null: return
	_basket(ch)
	if str(tabs[tab].id) == "racks":
		_racks(ch)
		return
	var keys: Array = Game.crafting.room_beds(ch, Game.room_rt.room_id)
	if keys.is_empty():
		para(Rect2(content.position + Vector2(20, 30), Vector2(content.size.x - 40, 80)), Tx.t("ui.garden.no_beds"), 20, UiKit.MIST)
		return
	if not sel in keys: sel = str(keys[0])
	var n := keys.size()
	var th := minf(168.0, TERRACES.size.y / n)
	for i in n:
		# Each terrace steps in and down from the one above; they settle into place as the page opens.
		var r := Rect2(TERRACES.position.x + i * 24.0, TERRACES.position.y + i * th, TERRACES.size.x - i * 24.0, th - 8)
		move(Vector2(0, (1.0 - unfold()) * (16.0 + 10.0 * i)))
		_terrace(ch, str(keys[i]), r, i)
		move()
		region(r, "sel", str(keys[i]))
	_tend(ch, keys.find(sel) + 1)

## Spring water, Spirit Soil and the Verdant Dew Vial in a low basket across the top, each on its hemp label.
func _basket(ch) -> void:
	rounded(BASKET.grow(3), 10.0, UiKit.INK)
	rounded(BASKET, 9.0, UiKit.SURFACE.straw.lerp(UiKit.SURFACE.wood, 0.4))
	PostKit.weave(self, BASKET.grow(-4), UiKit.SURFACE.straw, 12.0)
	var lw := (BASKET.size.x - 32) / 3.0
	var ds: Dictionary = Game.crafting.dew_state(ch)
	var items := [["spring_water", "%s × %d" % [ContentDB.item_name("spring_water"), ch.inventory.count("spring_water")]],
		["spirit_soil", "%s × %d" % [ContentDB.item_name("spirit_soil"), ch.inventory.count("spirit_soil")]]]
	if ds.has:
		var dew := Tx.t("ui.garden.dew") % [int(ds.dew), int(ds.cap)]
		if int(ds.dew) < int(ds.cap): dew += " · " + Tx.t("ui.garden.next_dew") % UiKit.span(float(ds.next_s))
		items.append(["verdant_dew_vial", dew])
	for i in items.size():
		var lab := Rect2(BASKET.position.x + 8 + i * (lw + 8), BASKET.position.y + 12, lw, 44)
		PostKit.hemp(self, lab)
		icon_at(Rect2(lab.position + Vector2(4, 6), Vector2(32, 32)), str(items[i][0]))
		text(lab.position + Vector2(42, 28), str(items[i][1]), 16, UiKit.JADE_SHADOW if i == 2 else UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, lab.size.x - 48)

## One terrace: its stone wall along the foot, the bed of soil on top with the herb at its stage, the grade on a stake,
## the bed's name, age and growth.
func _terrace(ch, key: String, r: Rect2, i: int) -> void:
	var v: Dictionary = Game.crafting.bed_view(ch, key)
	var bed := Rect2(r.position, Vector2(r.size.x, r.size.y - 22))
	if key == sel: glow(r.grow(14), Color(UiKit.GOLD, 0.35 * _halo()))
	WorkshopKit.bricks(self, Rect2(r.position.x, bed.end.y, r.size.x, 22), 11.0, 36.0)
	WorkshopKit.soil(self, bed, float(RICH.get(str(v.grade), 0.0)))
	if key == sel: draw_rect(bed.grow(2), UiKit.GOLD, false, 2.0)
	# The herb at its stage: shoots, a young plant, grown, ready (with its glow).
	var spot := Rect2(bed.position.x + 16, bed.position.y + 12, 80, 80)
	var frac := float(v.progress)
	if str(v.herb) != "":
		if frac < 0.25:
			for s in 3:
				var base := spot.get_center() + Vector2(-18 + s * 18, 22)
				draw_line(base, base + Vector2(-4, -14), UiKit.BRIGHT_JADE, 3.0, true)
				draw_line(base, base + Vector2(5, -12), UiKit.JADE, 3.0, true)
		elif frac < 0.6: icon_at(Rect2(spot.get_center() - Vector2(16, 16), Vector2(32, 32)), str(v.herb))
		else:
			if v.ready: glow(spot.grow(16), Color(UiKit.GOLD, 0.55 * _halo()))
			icon_at(Rect2(spot.get_center() - Vector2(32, 32), Vector2(64, 64)), str(v.herb))
	# The grade on a stake at the bed's far end.
	var stake := Rect2(bed.end.x - 140, bed.position.y + 10, 124, 30)
	draw_rect(Rect2(stake.get_center().x - 3, stake.end.y - 4, 6, 26), UiKit.SURFACE.wood)
	PostKit.hemp(self, stake)
	text(stake.position + Vector2(0, 21), Tx.t("ui.garden.grade_" + str(v.grade)), 14, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_CENTER, stake.size.x)
	var x := bed.position.x + 112
	var w := bed.size.x - 112 - 156
	text(Vector2(x, bed.position.y + 28), Tx.t("ui.garden.bed") % (i + 1) + ("  ·  " + ContentDB.item_name(str(v.herb)) if str(v.herb) != "" else ""), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, w + 140)
	var cap := str(ContentDB.config("garden").get("field_cap", {}).get(str(v.grade), "earth"))
	if str(v.herb) == "":
		text(Vector2(x, bed.position.y + 52), Tx.t("ui.garden.empty"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w + 140)
		text(Vector2(x, bed.position.y + 74), Tx.t("ui.garden.grows_up_to") % cap.capitalize(), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w + 140)
		return
	text(Vector2(x, bed.position.y + 52), Tx.plural("ui.garden.age", int(v.age)) % int(v.age) + "  ·  " + Tx.t("ui.garden.grows_up_to") % cap.capitalize(), 14,
		UiKit.GOLD if int(v.age) >= 100 else UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, w + 140)
	if bed.size.y >= 104:
		bar(Rect2(x, bed.position.y + 64, w, 26), frac, UiKit.BRIGHT_JADE if frac >= 1.0 else UiKit.JADE, Tx.t("ui.garden.ready") if v.ready else "%d%%" % int(frac * 100.0))
		if not v.ready: text(Vector2(x + w + 12, bed.position.y + 83), Tx.t("ui.garden.ready_in") % UiKit.span(float(v.seconds)), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, 132)

## What can be done with the chosen bed, on the board at the right: harvest, water, dew, soil, or the seeds to plant.
func _tend(ch, n: int) -> void:
	var r := TEND
	WorkshopKit.board(self, r)
	var v: Dictionary = Game.crafting.bed_view(ch, sel)
	text(r.position + Vector2(16, 32), Tx.t("ui.garden.bed") % n + "  ·  " + (ContentDB.item_name(str(v.herb)) if str(v.herb) != "" else Tx.t("ui.garden.empty_short")), 20,
		UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
	text(r.position + Vector2(16, 56), Tx.t("ui.garden.tap_a_bed"), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 32)
	var x := r.position.x + 16
	var w := r.size.x - 32
	var y := r.position.y + 76
	if str(v.herb) == "":
		text(Vector2(x, y + 20), Tx.t("ui.garden.plant"), 18, UiKit.PAPER)
		var seeds: Array = []
		for s in ch.inventory.bag:
			if s != null and str(ContentDB.item(str(s.id)).get("type", "")) == "seed" and not seeds.any(func(e): return str(e.id) == str(s.id)): seeds.append(s)
		if seeds.is_empty(): para(Rect2(x, y + 36, w, 110), Tx.t("ui.garden.no_seeds"), 16, UiKit.MIST, 5)
		for i in seeds.size():
			var sr := Rect2(x + (i % 5) * 60, y + 36 + (i / 5) * 60, 52, 52)
			slot_box(sr, str(seeds[i].id), ch.inventory.count(str(seeds[i].id)), "", "plant", str(seeds[i].id))
	else:
		btn(Rect2(x, y, w, BTN_H_MAIN), Tx.t("ui.garden.harvest"), "harvest", sel, true, bool(v.ready), Tx.t("ui.garden.not_ready"), 22)
		y += 76
		btn(Rect2(x, y, w, BTN_H_STANDARD), Tx.t("ui.garden.water") % ch.inventory.count("spring_water"), "water", sel, false,
			not v.ready and ch.inventory.count("spring_water") > 0, Tx.t("ui.garden.need_water"), 20)
		y += 68
		if Game.crafting.dew_state(ch).has:
			btn(Rect2(x, y, w, BTN_H_STANDARD), Tx.t("ui.garden.pour_dew"), "dew", sel, false, int(Game.crafting.dew_state(ch).dew) > 0, Tx.t("ui.garden.no_dew"), 20)
	var grades: Array = ContentDB.config("garden").get("field_grades", ["low", "mid", "high"])
	if str(v.grade) != str(grades.back()):
		btn(Rect2(x, r.end.y - 72, w, BTN_H_STANDARD), Tx.t("ui.garden.soil"), "soil", sel, false, ch.inventory.count("spirit_soil") > 0, Tx.t("ui.garden.need_soil"), 20)

# ------------------------------------------------------------------ racks
## Two drying racks over the hillside, each a bamboo frame holding a woven tray: steam herbs (their pills carry 30% less
## toxicity) or soak them in rice wine (10% more potency). Below, the board to put herbs on a rack.
func _racks(ch) -> void:
	var top := TERRACES.position.y
	if Game.crafting.tool_power(ch, "alchemy") <= 0.0:
		para(Rect2(content.position + Vector2(20, 30), Vector2(content.size.x - 40, 80)), Tx.t("ui.garden.no_rack"), 20, UiKit.MIST)
		return
	var g: Dictionary = ContentDB.config("garden").get("racks", {})
	var jobs: Array = Game.crafting.racks(ch)
	var now := Clock.now_utc()
	var w := (content.size.x - 24) / 2.0
	for i in int(g.get("slots", 2)):
		var r := Rect2(content.position.x + i * (w + 24), top, w, 164)
		# The frame: two posts and a cross-bar, the tray slung between them.
		for px in [r.position.x + 8, r.end.x - 16]: draw_rect(Rect2(px, r.position.y + 30, 8, r.size.y - 30), UiKit.SURFACE.bamboo.lerp(UiKit.SURFACE.wood, 0.3))
		draw_rect(Rect2(r.position.x, r.position.y + 34, r.size.x, 8), UiKit.SURFACE.bamboo.lerp(UiKit.SURFACE.wood, 0.3))
		text(r.position + Vector2(0, 22), Tx.t("ui.garden.rack") % (i + 1), 20, UiKit.PALE_GOLD)
		var tray := Rect2(r.position.x + 24, r.position.y + 50, r.size.x - 48, 88)
		rounded(tray.grow(3), 8.0, UiKit.INK)
		rounded(tray, 7.0, UiKit.SURFACE.bamboo)
		PostKit.weave(self, tray.grow(-3), UiKit.SURFACE.bamboo.lerp(UiKit.SURFACE.wood, 0.15), 14.0)
		ground(tray, UiKit.SURFACE.bamboo)
		if i >= jobs.size():
			text(tray.position + Vector2(20, 52), Tx.t("ui.garden.rack_free"), 18, UiKit.PAPER_INK)
			continue
		var job: Dictionary = jobs[i]
		slot_box(Rect2(tray.position.x + 8, tray.position.y + 6, SLOT, SLOT), str(job.herb), int(job.count))
		var jw := tray.size.x - 104
		text(tray.position + Vector2(96, 30), Tx.t("ui.garden.rack_job") % [Tx.t("ui.garden.doing_" + str(job.kind)), ContentDB.item_name(str(job.herb))], 16, UiKit.PAPER_INK, HORIZONTAL_ALIGNMENT_LEFT, jw)
		var total := float(g.get(str(job.kind), {}).get("hours", 1)) * 3600.0
		var left := maxf(0.0, float(job.done) - now)
		bar(Rect2(tray.position.x + 96, tray.position.y + 44, jw - 8, 28), 1.0 - left / maxf(1.0, total), UiKit.BRIGHT_JADE,
			Tx.t("ui.garden.ready") if left <= 0.0 else UiKit.span(left))
	var any_done := jobs.any(func(j): return float(j.done) <= now)
	btn(Rect2(content.end.x - 240, top + 176, 240, 48), Tx.t("ui.garden.collect"), "collect", null, true, any_done, Tx.t("ui.garden.nothing_ready"), 20)
	# Start a rack: pick a herb, the kind and how many.
	var r2 := Rect2(content.position.x, top + 236, content.size.x, content.end.y - top - 236)
	WorkshopKit.board(self, r2)
	text(r2.position + Vector2(18, 32), Tx.t("ui.garden.rack_start"), 20, UiKit.PALE_GOLD)
	var x := r2.position.x + 18
	var herbs: Array = []
	for st in ch.inventory.bag:
		if st == null or str(ContentDB.item(str(st.id)).get("type", "")) != "herb" or str(st.get("prep", "")) != "" or st.get("unappraised", false): continue
		if not herbs.has(str(st.id)): herbs.append(str(st.id))
	if herbs.is_empty():
		para(Rect2(r2.position + Vector2(18, 48), Vector2(r2.size.x - 36, 40)), Tx.t("ui.garden.no_herbs"), 18, UiKit.MIST)
		return
	if not rack_herb in herbs: rack_herb = str(herbs[0])
	for h in herbs.slice(0, 12):
		slot_box(Rect2(x, r2.position.y + 44, SLOT, SLOT), str(h), Game.inventory.count_prep(ch, str(h), ""), "", "herb", str(h), str(h) == rack_herb)
		x += SLOT + 8
	var y := r2.position.y + 132
	var kx := r2.position.x + 18
	for kind in ["steamed", "wine"]:
		btn(Rect2(kx, y, 250, 48), Tx.t("ui.garden.kind_" + kind), "kind", kind, rack_kind == kind, true, "", 18)
		kx += 262
	var have := Game.inventory.count_prep(ch, rack_herb, "")
	rack_count = clampi(rack_count, 1, mini(int(g.get("max", 10)), maxi(1, have)))
	btn(Rect2(kx + 10, y, 48, 48), "−", "less", null, false, rack_count > 1, "", 22)
	text(Vector2(kx + 66, y + 32), "× %d" % rack_count, 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 60)
	btn(Rect2(kx + 132, y, 48, 48), "+", "more", null, false, rack_count < mini(int(g.get("max", 10)), have), "", 22)
	var note := Tx.t("ui.garden.kind_note_" + rack_kind)
	if rack_kind == "wine":
		note += "  " + Tx.t("ui.garden.wine_jars") % [int(ceil(rack_count / float(g.get("wine", {}).get("per", 5)))), ch.inventory.count("rice_wine")]
	para(Rect2(r2.position + Vector2(18, 188), Vector2(r2.size.x - 300, 44)), note, 14, UiKit.MIST, 2)
	btn(Rect2(r2.end.x - 258, r2.end.y - 64, 240, 50), Tx.t("ui.garden.start"), "start", null, true,
		jobs.size() < int(g.get("slots", 2)) and have > 0, Tx.t("ui.garden.racks_busy"), 20)

func on_action(id: String, data) -> void:
	match id:
		"collect": submit({"type": "collect_racks"})
		"herb": rack_herb = str(data)
		"kind": rack_kind = str(data)
		"less": rack_count -= 1
		"more": rack_count += 1
		"start": submit({"type": "start_rack", "kind": rack_kind, "herb": rack_herb, "count": rack_count})
		"sel": sel = str(data)
		"plant": submit({"type": "plant_seed", "bed": sel, "seed": str(data)})
		"water": submit({"type": "water_bed", "bed": str(data)})
		"harvest":
			var r := submit({"type": "harvest_bed", "bed": str(data)})
			if r.get("ok", false): flash(Tx.t("ui.garden.harvested") % [ContentDB.item_name(str(r.item)), int(r.count)])
		"dew": submit({"type": "use_dew", "bed": str(data)})
		"soil": submit({"type": "apply_spirit_soil", "bed": str(data)})
	queue_redraw()
