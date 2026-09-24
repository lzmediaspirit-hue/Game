# Title: three disciple slots on the river docks, plus the Create Disciple screen.
extends Control

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")

signal enter(slot: int)

var bg: TextureRect
var content: Control
var create_slot := -1
var c_name := "New Disciple"
var c_hair := "plum_bob"
var c_clothes := "river_traveler"
var c_weapon := "spear"
var c_pose := "idle"
var name_edit: LineEdit
var anim_t := 0.0
var preview: TextureRect


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg = TextureRect.new()
	bg.texture = _backdrop()
	bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var shade := ColorRect.new()
	shade.color = Color(0, 0.03, 0.05, 0.25)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	content = Control.new()
	content.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(content)
	show_slots()


func _backdrop() -> Texture2D:
	var b := Backgrounds.build("lantern", 480, 480, 11)
	var img := Image.create(480, 270, false, Image.FORMAT_RGBA8)
	for L in b.layers:
		var li: Image = L.tex.get_image()
		img.blend_rect(li, Rect2i(0, 0, 480, 270), Vector2i.ZERO)
	# wooden docks on the water
	var p := Painter.new(480, 270)
	p.img = img
	p.w = 480
	p.h = 270
	for i in 3:
		var cx := 110 + i * 130
		p.rect(cx - 55, 212, 110, 58, "#4a3222")
		for k in 12:
			p.rect(cx - 55 + k * 9.2, 212, 1, 58, "#2e1e14")
		p.rect(cx - 55, 212, 110, 2, "#7a5a3a")
		for sx in [-55, 51]:
			p.rect(cx + sx, 196, 5, 74, "#3a2618")
	for lx in [40, 440]:
		p.rect(lx - 2, 150, 4, 70, "#2a1a10")
		p.rect(lx - 6, 142, 12, 14, "#c0392b")
		p.rect(lx - 4, 144, 8, 10, "#ffd070")
	return ImageTexture.create_from_image(p.img)


func _process(d: float) -> void:
	anim_t += d * 6.0
	if preview != null and is_instance_valid(preview):
		var fr := int(anim_t) % Sprites.frames(c_pose)
		preview.texture = Sprites.humanoid(_look(), c_pose, fr, 1.0).tex


func _look() -> Dictionary:
	var fake := {"look": {"hair": c_hair, "clothes": c_clothes}, "equip": {"hat": null, "gourd": null}}
	return Sprites.player_look(fake)


# ---------------------------------------------------------------- slots
func show_slots() -> void:
	UI.clear(content)
	preview = null
	var root := UI.vbox(14)
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.offset_left = 40
	root.offset_right = -40
	root.offset_top = 24
	root.offset_bottom = -20
	content.add_child(root)
	var head := UI.hbox(10)
	var tv := UI.vbox(0)
	tv.add_child(UI.title("JADE RIVER", 64))
	tv.add_child(UI.label("The Broken Seal  ·  Choose your disciple", 24, UI.CREAM))
	head.add_child(tv)
	head.add_child(UI.spacer(0, 0, true))
	root.add_child(head)
	if Game.notice != "":
		root.add_child(UI.label(Game.notice, 17, Color("#ffe08a"), HORIZONTAL_ALIGNMENT_LEFT, true))
	var cards := UI.hbox(30)
	cards.alignment = BoxContainer.ALIGNMENT_CENTER
	UI.expand(cards, true, true)
	root.add_child(cards)
	for i in 3:
		cards.add_child(_card(i))


func _card(i: int) -> Control:
	var p = Game.save.slots[i]
	var pnl := UI.panel(Color(0.06, 0.11, 0.12, 0.82), UI.GOLD if p != null else UI.GOLD_D, 16)
	pnl.custom_minimum_size = Vector2(340, 440)
	var v := UI.vbox(8)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	pnl.add_child(v)
	if p == null:
		v.add_child(UI.spacer(0, 60))
		var b := UI.button("＋", func(): show_create(i), 64, "gold", 140)
		b.custom_minimum_size = Vector2(140, 140)
		var c := CenterContainer.new()
		c.add_child(b)
		v.add_child(c)
		v.add_child(UI.title("Create Disciple", 26))
		return pnl
	v.add_child(UI.icon(Sprites.humanoid(Sprites.player_look(p), "idle", 0, 2.0).tex, 190))
	v.add_child(UI.title(p.name, 28))
	var st := UI.vbox(2)
	st.add_child(UI.label("Lv %d  ·  %s" % [p.level, S.realm_name(p)], 19, UI.CREAM, HORIZONTAL_ALIGNMENT_CENTER))
	st.add_child(UI.label("%s  ·  %s" % [C.ITEMS[p.equip.weapon].name, C.AREAS.get(p.area, C.AREAS.jr_town).name], 17, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
	v.add_child(st)
	var h := UI.hbox(8)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	var enter_b := UI.button("ENTER WORLD", func(): enter.emit(i), 22, "gold", 220)
	h.add_child(enter_b)
	var del := UI.button("🗑", func(): _confirm_delete(i), 20, "normal", 56)
	h.add_child(del)
	v.add_child(h)
	return pnl


func _confirm_delete(i: int) -> void:
	var cd := ConfirmationDialog.new()
	cd.dialog_text = "Delete %s forever? Shared storage is kept." % Game.save.slots[i].name
	cd.confirmed.connect(func():
		Game.delete_character(i)
		show_slots())
	add_child(cd)
	cd.popup_centered()


# ---------------------------------------------------------------- create
func show_create(i: int) -> void:
	create_slot = i
	c_name = "New Disciple"
	_render_create()


func _render_create() -> void:
	UI.clear(content)
	var root := UI.vbox(10)
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.offset_left = 30
	root.offset_right = -30
	root.offset_top = 16
	root.offset_bottom = -16
	content.add_child(root)
	var head := UI.hbox(10)
	head.add_child(UI.button("‹  Back", show_slots, 20, "normal", 120))
	var t := UI.title("CREATE DISCIPLE", 44)
	UI.expand(t)
	head.add_child(t)
	root.add_child(head)
	var row := UI.hbox(24)
	UI.expand(row, true, true)
	root.add_child(row)
	# preview
	var left := UI.vbox(10)
	UI.expand(left, true, true)
	var pv := UI.panel(Color(0, 0, 0, 0.25), UI.GOLD_D, 10)
	UI.expand(pv, true, true)
	var cc := CenterContainer.new()
	preview = UI.icon(null, 380)
	cc.add_child(preview)
	pv.add_child(cc)
	left.add_child(pv)
	var poses := UI.hbox(10)
	poses.alignment = BoxContainer.ALIGNMENT_CENTER
	for ps in [["idle", "Idle"], ["run", "Run"], ["attack", "Attack"], ["sit", "Meditate"]]:
		var pn: String = ps[0]
		poses.add_child(UI.button(ps[1], func():
			c_pose = pn
			_render_create(), 18, "tab_on" if c_pose == pn else "tab", 120))
	left.add_child(poses)
	row.add_child(left)
	# options
	var opt := UI.panel(UI.PANEL, UI.GOLD, 16)
	opt.custom_minimum_size.x = 640
	var ov := UI.vbox(10)
	opt.add_child(ov)
	var nh := UI.hbox(10)
	nh.add_child(UI.label("Name", 22, UI.GOLD))
	name_edit = LineEdit.new()
	name_edit.text = c_name
	name_edit.max_length = 16
	name_edit.add_theme_font_size_override("font_size", 22)
	name_edit.custom_minimum_size = Vector2(420, 48)
	name_edit.text_changed.connect(func(s): c_name = s)
	nh.add_child(name_edit)
	ov.add_child(nh)
	ov.add_child(UI.label("Hair", 22, UI.GOLD))
	var hr := UI.hbox(10)
	for hd in C.HAIR:
		var hid: String = hd.id
		var l := _look()
		l.hair = hid
		l.hairColor = Sprites.HAIR_COLORS[hid]
		var b := UI.icon_button(_head(l), hd.name, func():
			c_hair = hid
			_render_create(), 96, 16)
		if hid == c_hair:
			b.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
		hr.add_child(b)
	ov.add_child(hr)
	ov.add_child(UI.label("Clothes", 22, UI.GOLD))
	var cr := UI.hbox(10)
	for cd in C.CLOTHES:
		var cid: String = cd.id
		var l2 := _look()
		l2.main = cd.main
		l2.trim = cd.trim
		l2.under = cd.under
		l2.sash = cd.sash
		var b2 := UI.icon_button(Sprites.humanoid(l2, "idle", 0).tex, cd.name, func():
			c_clothes = cid
			_render_create(), 96, 16)
		if cid == c_clothes:
			b2.add_theme_stylebox_override("normal", UI.box(UI.PANEL3, UI.GOLD, 3, 6, 8))
		cr.add_child(b2)
	ov.add_child(cr)
	ov.add_child(UI.label("Starting Weapon", 22, UI.GOLD))
	var wr := UI.hbox(14)
	for wd in [["sword", "Sword", "Balanced damage\nMedium reach, faster"], ["spear", "Spear", "Higher damage\nLong reach"]]:
		var wid: String = wd[0]
		var b3 := UI.icon_button(Icons.get_icon(wid), "%s — %s" % [wd[1], wd[2]], func():
			c_weapon = wid
			_render_create(), 70, 16)
		b3.icon_alignment = HORIZONTAL_ALIGNMENT_LEFT
		b3.vertical_icon_alignment = VERTICAL_ALIGNMENT_CENTER
		b3.custom_minimum_size = Vector2(290, 90)
		if wid == c_weapon:
			b3.add_theme_stylebox_override("normal", UI.box(Color("#2a2410"), UI.GOLD, 3, 6, 8))
		wr.add_child(b3)
	ov.add_child(wr)
	ov.add_child(UI.label("Both support any discipline. Your other weapon family can be trained later.", 15, UI.DIM, HORIZONTAL_ALIGNMENT_CENTER))
	var br := UI.hbox(16)
	br.alignment = BoxContainer.ALIGNMENT_CENTER
	br.add_child(UI.button("CANCEL", show_slots, 22, "normal", 200))
	br.add_child(UI.button("CREATE DISCIPLE", func():
		Game.create_character(create_slot, c_name, c_hair, c_clothes, c_weapon)
		enter.emit(create_slot), 22, "gold", 300))
	ov.add_child(br)
	row.add_child(opt)


func _head(look: Dictionary) -> Texture2D:
	var spr := Sprites.humanoid(look, "idle", 0)
	return ImageTexture.create_from_image(spr.tex.get_image().get_region(Rect2i(4, 0, 32, 30)))
