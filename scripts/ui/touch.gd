# Multi-touch controls drawn and hit-tested directly from InputEventScreenTouch/Drag, so the
# stick, Attack, Jump and arts all work at once. Mouse works too (emulate_touch_from_mouse).
extends Control

const C = preload("res://scripts/data/content.gd")

var world
var hud
var touches := {}           # index → {role, start: Vector2, pos: Vector2, swiped}
var stick_base := Vector2.ZERO
var stick_knob := Vector2.ZERO
var stick_id := -1
var buttons := {}           # role → {c: Vector2, r: float}
var _pressed := {}          # role → frames (visual feedback)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func _settings() -> Dictionary:
	return Game.settings if not Game.save.is_empty() else {}


func _layout() -> void:
	var s: float = float(_settings().get("button_scale", 1.0))
	var W := size.x
	var H := size.y
	var left: bool = _settings().get("left_handed", false)
	var f := func(dx: float, dy: float) -> Vector2:
		return Vector2(dx * s if left else W - dx * s, H - dy * s)
	buttons = {}
	var cult: bool = hud != null and hud.mode == "cultivation"
	buttons.jump = {"c": f.call(346, 80) if not cult else f.call(560, 80), "r": 40 * s}
	if not cult:
		buttons.attack = {"c": f.call(112, 128), "r": 64 * s}
		buttons.guard = {"c": f.call(112, 222), "r": 22 * s}
		buttons.art0 = {"c": f.call(250, 80), "r": 40 * s}
		buttons.step = {"c": f.call(252, 196), "r": 38 * s}
		buttons.art1 = {"c": f.call(190, 300), "r": 36 * s}
		buttons.art2 = {"c": f.call(82, 300), "r": 36 * s}
	if world != null and not world.prompt.is_empty():
		buttons.interact = {"c": f.call(392, 214) if not cult else f.call(560, 214), "r": 38 * s}
	var ms_right: float = hud.mode_switch_right() if hud != null else W * 0.5 + 170
	buttons.pill0 = {"c": Vector2(ms_right + 36, H - 44), "r": 26}
	buttons.pill1 = {"c": Vector2(ms_right + 96, H - 44), "r": 26}


func _stick_zone(p: Vector2) -> bool:
	var left: bool = _settings().get("left_handed", false)
	var in_x := p.x > size.x * 0.58 if left else p.x < size.x * 0.42
	return in_x and p.y > size.y * 0.32


func _hit(p: Vector2) -> String:
	var best := ""
	var bd := INF
	for role in buttons:
		var b: Dictionary = buttons[role]
		var d := p.distance_to(b.c)
		if d <= b.r + 10 and d < bd:
			bd = d
			best = role
	return best


func _input(e: InputEvent) -> void:
	if not is_visible_in_tree() or world == null:
		return
	if e is InputEventScreenTouch:
		var p: Vector2 = get_global_transform_with_canvas().affine_inverse() * e.position
		if e.pressed:
			_layout()
			var role := _hit(p)
			if role == "" and _stick_zone(p) and stick_id < 0:
				role = "stick"
				stick_id = e.index
				stick_base = p
				stick_knob = p
			if role != "":
				touches[e.index] = {"role": role, "start": p, "pos": p, "swiped": false}
				_press(role)
				get_viewport().set_input_as_handled()
		else:
			if touches.has(e.index):
				_release(touches[e.index].role)
				touches.erase(e.index)
			if e.index == stick_id:
				stick_id = -1
				world.ctl.move = Vector2.ZERO
	elif e is InputEventScreenDrag:
		if not touches.has(e.index):
			return
		var p2: Vector2 = get_global_transform_with_canvas().affine_inverse() * e.position
		var t: Dictionary = touches[e.index]
		t.pos = p2
		if t.role == "stick":
			var v := p2 - stick_base
			var r := 70.0 * float(_settings().get("button_scale", 1.0))
			if v.length() > r:
				stick_base = p2 - v.normalized() * r   # base follows the thumb
				v = v.normalized() * r
			stick_knob = stick_base + v
			var m := v / r
			world.ctl.move = m if m.length() > 0.18 else Vector2.ZERO
		elif t.role == "attack" and not t.swiped:
			var dv: Vector2 = p2 - t.start
			if absf(dv.x) > 34 and absf(dv.x) > absf(dv.y):
				t.swiped = true
				world.ctl.dash_dir = 1 if dv.x > 0 else -1
			elif dv.y < -34:
				t.swiped = true
				world.ctl.guard = true
		get_viewport().set_input_as_handled()


func _press(role: String) -> void:
	_pressed[role] = 8
	var c: Ctl = world.ctl
	match role:
		"attack": c.attack = true
		"jump": c.jump = true
		"step": c.dash = true
		"guard": c.guard = true
		"art0": c.arts[0] = true
		"art1": c.arts[1] = true
		"art2": c.arts[2] = true
		"interact": c.interact = true
		"pill0": c.pills[0] = true
		"pill1": c.pills[1] = true


func _release(role: String) -> void:
	if role == "guard" or role == "attack":
		world.ctl.guard = false


func _process(_d: float) -> void:
	for k in _pressed.keys():
		_pressed[k] -= 1
		if _pressed[k] <= 0:
			_pressed.erase(k)
	queue_redraw()


func _draw() -> void:
	if world == null or Game.p.is_empty():
		return
	_layout()
	var fnt := UI.font()
	# stick
	var show: bool = _settings().get("show_stick", true)
	if stick_id >= 0:
		draw_circle(stick_base, 74, Color(0, 0, 0, 0.28))
		draw_arc(stick_base, 74, 0, TAU, 40, Color(1, 1, 1, 0.35), 3)
		draw_circle(stick_knob, 34, Color(1, 1, 1, 0.3))
		draw_arc(stick_knob, 34, 0, TAU, 30, Color(1, 1, 1, 0.55), 2)
	elif show:
		var left: bool = _settings().get("left_handed", false)
		var anchor := Vector2(size.x - 160 if left else 160, size.y - 150)
		draw_circle(anchor, 74, Color(0, 0, 0, 0.18))
		draw_arc(anchor, 74, 0, TAU, 40, Color(1, 1, 1, 0.22), 3)
		draw_circle(anchor, 30, Color(1, 1, 1, 0.14))
		for a in [0.0, PI / 2, PI, PI * 1.5]:
			var d := Vector2(cos(a), sin(a))
			var tip := anchor + d * 60
			draw_colored_polygon(PackedVector2Array([tip, tip - d * 10 + Vector2(-d.y, d.x) * 7, tip - d * 10 - Vector2(-d.y, d.x) * 7]), Color(1, 1, 1, 0.3))
	var p: Dictionary = Game.p
	for role in buttons:
		var b: Dictionary = buttons[role]
		var c: Vector2 = b.c
		var r: float = b.r
		var tex: Texture2D = null
		var label := ""
		var frac := 0.0
		var locked := false
		var ring := UI.GOLD_D
		match role:
			"attack":
				var w: Dictionary = C.ITEMS[p.equip.weapon]
				tex = Icons.get_icon(w.icon, w.get("tint", null))
				label = "Attack"
				ring = UI.GOLD
			"jump":
				tex = Icons.get_icon("jump")
				label = "Jump"
			"step":
				tex = Icons.get_icon("step")
				label = "Step"
				frac = world.step_cd / 42.0
			"guard":
				tex = Icons.get_icon("shield")
			"interact":
				tex = Icons.get_icon(_prompt_icon())
				label = str(world.prompt.label)
				ring = UI.JADE
			"pill0", "pill1":
				var i := int(role.substr(4))
				var id: String = p.quickslots[i] if i < p.quickslots.size() else ""
				tex = Icons.item(id) if id != "" else null
				var n := int(p.items.get(id, 0))
				label = str(n)
				locked = n == 0
			_:
				var i2 := int(role.substr(3))
				var id2 = p.abilities.slots[i2]
				if id2 == null:
					tex = Icons.get_icon("lock")
					label = "Empty"
					locked = true
				else:
					var a: Dictionary = C.ABILITIES[id2]
					tex = Icons.ability(id2)
					label = a.name
					if world.art_cd.has(id2):
						frac = float(world.art_cd[id2]) / (float(a.cd) * 60.0)
					var cost := int(ceil(float(a.qi) * float(world.st.get("art_cost", 1.0))))
					locked = int(p.qi) < cost or (a.source == "weapon" and a.family != world.st.get("family", ""))
		var down := _pressed.has(role) or _held(role)
		draw_circle(c, r + 4, Color(0, 0, 0, 0.45))
		draw_circle(c, r, Color("#0f2e2c") if not down else Color("#1f5a50"))
		draw_arc(c, r, 0, TAU, 48, ring, 3 if role != "attack" else 4)
		if tex != null:
			var ts := r * (1.25 if role != "attack" else 1.15)
			draw_texture_rect(tex, Rect2(c - Vector2(ts, ts) / 2, Vector2(ts, ts)), false, Color(1, 1, 1, 0.45 if locked else 1.0))
		if frac > 0:
			draw_circle(c, r - 2, Color(0, 0, 0, 0.45))
			draw_arc(c, r - 3, -PI / 2, -PI / 2 + TAU * clampf(frac, 0, 1), 32, Color(1, 1, 1, 0.7), 4)
		if role == "attack":
			for sgn in [-1, 1]:
				var ac: Vector2 = c + Vector2(sgn * (r + 20), 0)
				draw_colored_polygon(PackedVector2Array([ac + Vector2(sgn * 10, 0), ac + Vector2(-sgn * 4, -12), ac + Vector2(-sgn * 4, 12)]), Color(1, 1, 1, 0.5))
		if label != "":
			var fs := 17 if role != "attack" else 21
			if role.begins_with("pill"):
				draw_string(fnt, c + Vector2(r * 0.2, r * 0.95), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)
			else:
				var ww := 200.0
				draw_string_outline(fnt, c + Vector2(-ww / 2, r + fs + 2), label, HORIZONTAL_ALIGNMENT_CENTER, ww, fs, 5, Color(0, 0, 0, 0.9))
				draw_string(fnt, c + Vector2(-ww / 2, r + fs + 2), label, HORIZONTAL_ALIGNMENT_CENTER, ww, fs, Color("#f4ecd4"))


func _held(role: String) -> bool:
	for t in touches.values():
		if t.role == role:
			return true
	return false


func _prompt_icon() -> String:
	var pr: Dictionary = world.prompt
	match pr.get("kind", ""):
		"npc": return "scroll"
		"portal": return "map"
		"station":
			var t: String = pr.obj.type
			return {"forge": "anvil", "furnace": "potion", "research": "book", "chest": "bag", "shop": "coin", "board": "quest", "shrine": "cultivate", "rest": "cultivate", "seal": "meridian"}.get(t, "scroll")
		"node":
			var n: Dictionary = pr.obj
			return {"mining": "pick", "herbalism": "herb", "fishing": "rod"}.get(n.def.prof, "gather")
		"rune": return "meridian"
	return "scroll"
