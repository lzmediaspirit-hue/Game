# In-field HUD: vitals, objective chip, minimap, Map/Menu, Combat ↔ Cultivation switch,
# cultivation tray, boss bar and toasts. Touch combat buttons live in touch.gd.
extends Control

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

signal open_page(page: String)

var world
var mode := "combat"
var portrait: TextureRect
var name_l: Label
var hp_bar
var qi_bar
var xp_l: Label
var realm_l: Label
var insight_l: Label
var mer_box: HBoxContainer
var quest_btn: Button
var quest_l: Label
var quest_sub: Label
var area_l: Label
var minimap: Control
var mode_combat: Button
var mode_cult: Button
var tray: Control
var med_btn: Button
var med_sub: Label
var boss_box: Control
var boss_name: Label
var boss_bar
var toasts: VBoxContainer
var vitals: PanelContainer
var _last_look := ""


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	# ---- vitals (top-left)
	vitals = UI.panel(UI.PANEL, UI.GOLD, 10)
	vitals.position = Vector2(14, 12)
	add_child(vitals)
	var vh := UI.hbox(12)
	vitals.add_child(vh)
	var pf := UI.panel(Color("#0a1a1a"), UI.GOLD_D, 2)
	portrait = UI.icon(null, 76)
	pf.add_child(portrait)
	vh.add_child(pf)
	var vv := UI.vbox(4)
	vh.add_child(vv)
	var top := UI.hbox(10)
	name_l = UI.label("", 21, UI.CREAM)
	top.add_child(name_l)
	vv.add_child(top)
	hp_bar = UI.bar(1, Color("#d8413a"), 250, 16)
	qi_bar = UI.bar(1, Color("#3aa8e0"), 250, 16)
	vv.add_child(hp_bar)
	vv.add_child(qi_bar)
	var xrow := UI.hbox(8)
	xp_l = UI.label("", 15, UI.DIM)
	xrow.add_child(xp_l)
	mer_box = UI.hbox(3)
	xrow.add_child(mer_box)
	vv.add_child(xrow)
	var realm_v := UI.vbox(2)
	realm_v.alignment = BoxContainer.ALIGNMENT_CENTER
	var ri := UI.icon(Icons.get_icon("realm"), 40)
	realm_v.add_child(ri)
	realm_l = UI.label("", 16, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER)
	realm_v.add_child(realm_l)
	insight_l = UI.label("", 14, Color("#9fdcff"), HORIZONTAL_ALIGNMENT_CENTER)
	realm_v.add_child(insight_l)
	vh.add_child(realm_v)
	# ---- quest chip
	quest_btn = Button.new()
	quest_btn.focus_mode = Control.FOCUS_NONE
	quest_btn.add_theme_stylebox_override("normal", UI.box(Color(UI.PANEL, 0.92), UI.GOLD_D, 2, 8, 10))
	quest_btn.add_theme_stylebox_override("hover", UI.box(Color(UI.PANEL2, 0.95), UI.GOLD, 2, 8, 10))
	quest_btn.add_theme_stylebox_override("pressed", UI.box(Color(UI.PANEL2, 0.95), UI.GOLD, 2, 8, 10))
	quest_btn.pressed.connect(func(): open_page.emit("journal"))
	add_child(quest_btn)
	var qh := UI.hbox(8)
	qh.mouse_filter = Control.MOUSE_FILTER_IGNORE
	qh.position = Vector2(10, 6)
	quest_btn.add_child(qh)
	qh.add_child(UI.icon(Icons.get_icon("quest"), 34))
	var qv := UI.vbox(0)
	qv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	quest_l = UI.label("", 18, Color("#ffe08a"))
	quest_sub = UI.label("", 14, UI.CREAM)
	qv.add_child(quest_l)
	qv.add_child(quest_sub)
	qh.add_child(qv)
	# ---- area + minimap (top-right)
	var mm := UI.panel(UI.PANEL, UI.GOLD, 10)
	mm.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	mm.name = "Minimap"
	add_child(mm)
	var mv := UI.vbox(4)
	mm.add_child(mv)
	area_l = UI.label("", 20, UI.CREAM)
	mv.add_child(area_l)
	minimap = Minimap.new()
	minimap.custom_minimum_size = Vector2(380, 34)
	mv.add_child(minimap)
	var btns := UI.hbox(10)
	btns.name = "TopButtons"
	btns.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	add_child(btns)
	btns.add_child(UI.icon_button(Icons.get_icon("map"), "Map", func(): open_page.emit("map"), 60, 16))
	btns.add_child(UI.icon_button(Icons.get_icon("menu"), "Menu", func(): open_page.emit("hub"), 60, 16))
	# ---- boss bar
	boss_box = UI.vbox(2)
	boss_box.visible = false
	add_child(boss_box)
	boss_name = UI.title("", 22)
	boss_box.add_child(boss_name)
	boss_bar = UI.bar(1, Color("#c0302a"), 460, 16)
	boss_box.add_child(boss_bar)
	# ---- mode switch (bottom-centre)
	var ms := UI.hbox(0)
	ms.name = "ModeSwitch"
	add_child(ms)
	mode_combat = UI.button("  Combat", func(): set_mode("combat"), 20, "tab_on", 150)
	mode_combat.icon = Icons.get_icon("class")
	mode_combat.expand_icon = true
	mode_combat.add_theme_constant_override("icon_max_width", 30)
	mode_cult = UI.button("  Cultivation", func(): set_mode("cultivation"), 20, "tab", 170)
	mode_cult.icon = Icons.get_icon("insight")
	mode_cult.expand_icon = true
	mode_cult.add_theme_constant_override("icon_max_width", 30)
	for b in [mode_combat, mode_cult]:
		b.custom_minimum_size.y = 56
		ms.add_child(b)
	# ---- cultivation tray
	tray = Control.new()
	tray.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tray.visible = false
	add_child(tray)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.name = "Grid"
	tray.add_child(grid)
	for e in [["cultivate", "Cultivation", "cultivation"], ["bag", "Inventory", "inventory"], ["book", "Skills", "skills"], ["gather", "Gathering", "gathering"], ["anvil", "Workshop", "workshop"], ["journal", "Journal", "journal"]]:
		var b := UI.icon_button(Icons.get_icon(e[0]), e[1], func(): open_page.emit(e[2]), 86, 17)
		b.custom_minimum_size = Vector2(118, 104)
		grid.add_child(b)
	var medv := UI.vbox(2)
	medv.name = "Med"
	tray.add_child(medv)
	med_btn = UI.icon_button(Icons.get_icon("cultivate"), "Meditate", func(): world.ctl.meditate = true, 100, 20)
	med_btn.custom_minimum_size = Vector2(170, 120)
	medv.add_child(med_btn)
	med_sub = UI.label("", 15, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER)
	medv.add_child(med_sub)
	# ---- toasts
	toasts = UI.vbox(6)
	toasts.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(toasts)


func set_mode(m: String) -> void:
	mode = m
	if world:
		world.mode = m
		if m == "combat" and world.pl.state == "sit":
			world.try_meditate()
	mode_combat.add_theme_stylebox_override("normal", UI.box(Color("#2a2410"), UI.GOLD, 2, 12, 16) if m == "combat" else UI.box(Color("#0f2424"), Color("#2f5a50"), 2, 12, 16))
	mode_cult.add_theme_stylebox_override("normal", UI.box(Color("#2a2410"), UI.GOLD, 2, 12, 16) if m == "cultivation" else UI.box(Color("#0f2424"), Color("#2f5a50"), 2, 12, 16))
	tray.visible = m == "cultivation"


func toast(text: String, kind := "info") -> void:
	var col: Color = {"err": Color("#ff9a8a"), "quest": Color("#ffe08a"), "loot": Color("#bfffd0"), "ok": UI.CREAM}.get(kind, UI.CREAM)
	var p := UI.panel(Color(0, 0, 0, 0.6), Color(col, 0.6), 8)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := UI.label(text, 17, col, HORIZONTAL_ALIGNMENT_LEFT, true)
	l.custom_minimum_size.x = 420
	p.add_child(l)
	toasts.add_child(p)
	while toasts.get_child_count() > 4:
		var old := toasts.get_child(0)
		toasts.remove_child(old)
		old.queue_free()
	var tw := create_tween()
	tw.tween_interval(3.2 if kind != "quest" else 5.5)
	tw.tween_property(p, "modulate:a", 0.0, 0.6)
	tw.tween_callback(p.queue_free)


func _process(_d: float) -> void:
	if world == null or Game.p.is_empty():
		return
	var p: Dictionary = Game.p
	var st: Dictionary = world.st if not world.st.is_empty() else S.stats(p)
	var W := size.x
	var H := size.y
	# layout
	quest_btn.position = Vector2(14, vitals.position.y + vitals.size.y + 8)
	quest_btn.size = Vector2(maxf(300, quest_l.get_minimum_size().x + 70), 58)
	var mm: Control = get_node("Minimap")
	mm.position = Vector2(W - mm.size.x - 14, 12)
	var tb: Control = get_node("TopButtons")
	tb.position = Vector2(W - tb.size.x - 14, mm.position.y + mm.size.y + 8)
	var ms: Control = get_node("ModeSwitch")
	ms.position = Vector2(W * 0.42 - ms.size.x * 0.5, H - ms.size.y - 16)
	var grid: Control = tray.get_node("Grid")
	var left: bool = Game.settings.get("left_handed", false)
	grid.position = Vector2(14 if left else W - grid.size.x - 14, H - grid.size.y - 14)
	var medv: Control = tray.get_node("Med")
	medv.position = Vector2((grid.position.x + grid.size.x + 16) if left else (grid.position.x - medv.size.x - 16), H - medv.size.y - 60)
	boss_box.position = Vector2(W * 0.5 - 230, 16)
	toasts.position = Vector2(W * 0.5 - 220, H * 0.34)
	# vitals
	var lk := str(Sprites.player_look(p))
	if lk != _last_look:
		_last_look = lk
		portrait.texture = _portrait_tex(p)
	var cult := mode == "cultivation"
	name_l.text = ("Lv %d · %s" % [p.level, S.realm_name(p)]) if cult else ("Lv %d   %s" % [p.level, p.name])
	hp_bar.set_value(float(p.hp) / float(st.max_hp), "%d/%d" % [p.hp, st.max_hp])
	qi_bar.set_value(float(p.qi) / float(st.max_qi), "%d/%d" % [p.qi, st.max_qi])
	if cult:
		xp_l.text = "Essence %d" % p.essence
		insight_l.text = "Insight %d" % p.insight
		if mer_box.get_child_count() != 6 or frame_mer != p.meridians.size():
			frame_mer = p.meridians.size()
			UI.clear(mer_box)
			for i in 6:
				var dot := ColorRect.new()
				dot.custom_minimum_size = Vector2(12, 12)
				dot.color = UI.JADE if i < p.meridians.size() else (UI.GOLD_D if i < S.meridian_cap(p.realm) else Color("#2a3a3a"))
				mer_box.add_child(dot)
		mer_box.visible = true
	else:
		xp_l.text = "XP %d%%" % int(100.0 * p.xp / S.xp_to_next(p.level))
		insight_l.text = ""
		mer_box.visible = false
	realm_l.text = S.realm_name(p)
	# objective chip
	var ob := R.objective(p)
	var prog = ob.progress
	var chip: String = ob.get("chip", "")
	if prog != null and ob.step != null and ob.step.type in ["kill", "have", "craft"]:
		quest_l.text = "%s %d/%d" % [chip if chip != "" else ob.short, prog.have, prog.need]
	else:
		quest_l.text = ob.short
	quest_sub.text = ob.text
	# area + minimap
	area_l.text = C.AREAS[world.area_id].name if world.area_id != "" else ""
	minimap.data = world.minimap()
	minimap.queue_redraw()
	# boss bar
	var b = world.boss
	boss_box.visible = b != null and b.alive and world.arena_locked
	if boss_box.visible:
		boss_name.text = b.def.name
		boss_bar.set_value(b.hp / b.max_hp, "%d / %d" % [int(b.hp), int(b.max_hp)])
	# meditate availability
	if cult:
		var safe: bool = world.is_safe_spot()
		med_btn.disabled = not safe and world.pl.state != "sit"
		med_sub.text = "Stop" if world.pl.state == "sit" else ("Safe here" if safe else ("Unsafe near enemies" if world.A.type != "town" else ""))
		if world.A.type == "field" and not safe and world.pl.state != "sit":
			med_sub.text = "Find a shrine, away from enemies"


var frame_mer := -1


func mode_switch_right() -> float:
	var ms: Control = get_node("ModeSwitch")
	return ms.position.x + ms.size.x


func _portrait_tex(p: Dictionary) -> Texture2D:
	var spr := Sprites.humanoid(Sprites.player_look(p), "idle", 0)
	var img: Image = spr.tex.get_image()
	var crop := img.get_region(Rect2i(4, 0, 32, 30))
	return ImageTexture.create_from_image(crop)


class Minimap extends Control:
	var data := {}

	func _draw() -> void:
		if data.is_empty():
			return
		var w := size.x
		var y := size.y * 0.55
		draw_rect(Rect2(0, 2, w, size.y - 4), Color(0, 0, 0, 0.35))
		draw_line(Vector2(6, y), Vector2(w - 6, y), Color("#5f9a90"), 3)
		var v: Array = data.view
		draw_rect(Rect2(6 + v[0] * (w - 12), 4, (v[1] - v[0]) * (w - 12), size.y - 8), Color(1, 1, 1, 0.08))
		for po in data.portals:
			var px: float = 6 + po[0] * (w - 12)
			draw_rect(Rect2(px - 3, y - 9, 6, 12), Color("#6a6e6a") if po[1] else UI.JADE)
		for o in data.others:
			draw_circle(Vector2(6 + o * (w - 12), y), 4, UI.GOLD)
		for n in data.nodes:
			var nx: float = 6 + n[0] * (w - 12)
			var col: Color = {"mining": Color("#d08a4a"), "herbalism": Color("#6fe08a"), "fishing": Color("#6fb8ff")}.get(n[2], Color.WHITE)
			if not n[1]:
				col = col.darkened(0.6)
			draw_rect(Rect2(nx - 2, y - 11, 4, 4), col)
		for e in data.enemies:
			draw_circle(Vector2(6 + e[0] * (w - 12), y), 6 if e[1] else 4, Color("#e04a3a"))
		var pxp: float = 6 + data.player * (w - 12)
		draw_circle(Vector2(pxp, y), 7, Color("#3a2410"))
		draw_circle(Vector2(pxp, y), 5, Color("#ffd040"))
