# Root scene: pixel world in a low-res SubViewport scaled to the screen, with the HUD, touch
# controls, menus and title screen layered on top at full resolution.
extends Control

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

var vp: SubViewport
var view: TextureRect
var world
var hud
var touch
var menus
var title
var _keys_prev := {}
var in_game := false
var _kb_moving := false


func _ready() -> void:
	theme = UI.theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vp = SubViewport.new()
	vp.size = Vector2i(480, 270)
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	vp.snap_2d_transforms_to_pixel = true
	add_child(vp)
	world = load("res://scripts/world/world.gd").new()
	vp.add_child(world)
	view = TextureRect.new()
	view.texture = vp.get_texture()
	view.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	view.stretch_mode = TextureRect.STRETCH_SCALE
	view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(view)
	hud = load("res://scripts/ui/hud.gd").new()
	hud.world = world
	add_child(hud)
	touch = load("res://scripts/ui/touch.gd").new()
	touch.world = world
	touch.hud = hud
	add_child(touch)
	menus = load("res://scripts/ui/menus.gd").new()
	menus.world = world
	menus.hud = hud
	add_child(menus)
	title = load("res://scripts/ui/title.gd").new()
	add_child(title)
	title.enter.connect(_enter)
	hud.open_page.connect(func(pg): menus.open(pg))
	menus.to_title.connect(_to_title)
	world.toast.connect(func(t, k): hud.toast(t, k))
	world.dialogue.connect(func(n, l, m): menus.show_dialogue(n, l, m))
	world.station.connect(_on_station)
	world.died.connect(func(): menus.open("death"))
	world.threat.connect(func():
		if hud.mode == "cultivation":
			hud.set_mode("combat"))
	world.area_loaded.connect(func(id):
		if C.AREAS[id].type == "field" and hud.mode == "cultivation" and not world.is_safe_spot():
			hud.set_mode("combat"))
	Game.event.connect(_on_event)
	get_viewport().size_changed.connect(_on_resize)
	_show_game(false)
	_on_resize()


func _on_resize() -> void:
	var s := get_viewport_rect().size
	var aspect := s.x / maxf(1.0, s.y)
	var w := clampi(int(round(270.0 * aspect)), 400, 720)
	if vp.size.x != w:
		vp.size = Vector2i(w, 270)
		world.view_w = w
		if in_game and world.area_id != "":
			world.load_area(world.area_id, world.pl.x, world.pl.d)


func _show_game(on: bool) -> void:
	in_game = on
	view.visible = on
	hud.visible = on
	touch.visible = on
	title.visible = not on
	world.paused = not on


func _enter(slot: int) -> void:
	Game.select(slot)
	var p: Dictionary = Game.p
	_show_game(true)
	hud.set_mode("combat")
	var area: String = p.area if C.AREAS.has(p.area) and p.area != "trial" else "jr_town"
	world.load_area(area, float(p.x), float(p.depth))
	hud.toast("Welcome, %s. %s" % [p.name, R.objective(p).text], "quest")
	if p.assignment != null:
		var y := R.assignment_yield(p, Game.now())
		hud.toast("%s has run %d min — collect it on the Gathering page." % [R.ASSIGN[p.assignment.kind].name, y.minutes], "info")


func _to_title() -> void:
	if world.area_id != "" and world.A.type != "trial":
		Game.p.x = world.pl.x
		Game.p.depth = world.pl.d
	Game.save_now()
	world.area_id = ""
	_show_game(false)
	title.show_slots()


func _on_station(type: String) -> void:
	match type:
		"forge", "furnace", "research":
			menus.open("workshop", {"station": type})
		"chest":
			menus.open("storage")
		"shop":
			menus.open("shop")
		"board":
			menus.open("board")
		"shrine":
			menus.open("shrine")
		"rest":
			menus.open("rest")


func _on_event(kind: String, data: Dictionary) -> void:
	match kind:
		"levelup":
			hud.toast("Level up! You are now level %d." % data.level, "quest")
		"breakthrough":
			hud.toast("Breakthrough — %s realm!" % C.REALMS[data.realm].name, "quest")
		"mastery":
			hud.toast("%s mastery rank %d — check the Skills page." % [S.cap(data.family), data.rank], "quest")
		"proflevel":
			hud.toast("%s reached Lv %d." % [S.cap(data.prof), data.level], "quest")
		"soul":
			hud.toast("Soul milestone: %s — %s" % [data.milestone.name, data.milestone.desc], "quest")
		"chapter":
			hud.toast("Chapter complete!", "quest")


# ---------------------------------------------------------------- keyboard
func _key(k: Key) -> bool:
	return Input.is_physical_key_pressed(k)


func _pressed_edge(name: String, down: bool) -> bool:
	var was: bool = _keys_prev.get(name, false)
	_keys_prev[name] = down
	return down and not was


func _physics_process(_d: float) -> void:
	if not in_game:
		return
	var ctl: Ctl = world.ctl
	var menu_open: bool = menus.is_open()
	var mv := Vector2.ZERO
	if _key(KEY_A) or _key(KEY_LEFT): mv.x -= 1
	if _key(KEY_D) or _key(KEY_RIGHT): mv.x += 1
	if _key(KEY_W) or _key(KEY_UP): mv.y -= 1
	if _key(KEY_S) or _key(KEY_DOWN): mv.y += 1
	var kb_active := mv != Vector2.ZERO
	if touch.stick_id < 0 and not menu_open:
		if kb_active:
			ctl.move = mv.normalized()
			_kb_moving = true
		elif _kb_moving:
			ctl.move = Vector2.ZERO
			_kb_moving = false
	var guard_key := _key(KEY_L) or _key(KEY_SHIFT)
	if not touch._held("guard") and not touch._held("attack"):
		ctl.guard = guard_key and not menu_open
	if _pressed_edge("tab", _key(KEY_TAB)) and not menu_open:
		hud.set_mode("cultivation" if hud.mode == "combat" else "combat")
	if _pressed_edge("esc", _key(KEY_ESCAPE)):
		if menus.dlg.visible:
			menus._end_dialogue()
		elif menus.frame.visible:
			menus.back()
		else:
			menus.open("hub")
	if _pressed_edge("map", _key(KEY_M)) and not menu_open:
		menus.open("map")
	if _pressed_edge("bag", _key(KEY_B)) and not menu_open:
		menus.open("inventory")
	if _pressed_edge("enter", _key(KEY_ENTER)) and menus.dlg.visible:
		menus.dlg_i += 1
		if menus.dlg_i >= menus.dlg_lines.size():
			menus._end_dialogue()
		else:
			menus._dlg_render()
	if menu_open:
		return
	if _pressed_edge("jump", _key(KEY_SPACE)): ctl.jump = true
	if _pressed_edge("atk", _key(KEY_J)): ctl.attack = true
	if _pressed_edge("dash", _key(KEY_K)): ctl.dash = true
	if _pressed_edge("int", _key(KEY_F) or _key(KEY_E)): ctl.interact = true
	if _pressed_edge("a1", _key(KEY_1) or _key(KEY_U)): ctl.arts[0] = true
	if _pressed_edge("a2", _key(KEY_2) or _key(KEY_I)): ctl.arts[1] = true
	if _pressed_edge("a3", _key(KEY_3) or _key(KEY_O)): ctl.arts[2] = true
	if _pressed_edge("p1", _key(KEY_Q)): ctl.pills[0] = true
	if _pressed_edge("p2", _key(KEY_R)): ctl.pills[1] = true
	if _pressed_edge("med", _key(KEY_G)): ctl.meditate = true


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED:
		if in_game and world.area_id != "" and world.A.type != "trial":
			Game.p.x = world.pl.x
			Game.p.depth = world.pl.d
		Game.save_now()
