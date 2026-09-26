class_name Page
extends Control
## Base for every full page and modal (Part 9.3/9.4): a major window frame with a
## title band, optional tabs, a close button and a content area. Pages draw
## immediately in `draw_page()` with helpers that also register tap regions, so a
## page is data → drawing → `on_action(id, data)` → Game.submit(intent).
## Pages never change game state themselves; they submit intents and redraw on events.

signal closed(page: Page)
signal navigate(page: String, args: Dictionary)

const SAFE := Rect2(48, 24, 1184, 672)

var page_id := ""
var title := ""
var tabs: Array = []            # [{id, label, locked?: text}]
var tab := 0
var args: Dictionary = {}
var modal := false              # small centred dialog instead of the full window
var frameless := false          # shell screens draw their own layout over the backdrop
var frame_rect := Rect2(64, 32, 1152, 656)
var content := Rect2()
var t := 0.0
var toast := ""
var toast_t := 0.0
var confirm: Dictionary = {}    # {text, id, data, danger}
var scroll: Dictionary = {}     # area id -> px offset

var _regions: Array = []        # {rect, id, data, enabled, reason, kind}
var _pressed := -1
var _press_pos := Vector2.ZERO
var _drag_area := ""
var _drag_last := 0.0
var _dragged := false
var _areas: Dictionary = {}     # area id -> {rect, max}

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	GameEvents.event.connect(_on_game_event)
	if modal and frame_rect == Rect2(64, 32, 1152, 656): frame_rect = Rect2(290, 170, 700, 380)
	_layout()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_game_event): GameEvents.event.disconnect(_on_game_event)

func open(a: Dictionary) -> void:
	args = a
	setup()
	# After setup: some pages build their tabs there (crafts, workshop).
	if a.has("tab"):
		for i in tabs.size():
			if str(tabs[i].id) == str(a.tab): tab = i
	queue_redraw()

## Virtual hooks.
func setup() -> void: pass
func draw_page() -> void: pass
func on_action(_id: String, _data) -> void: pass
func on_event(_name: String, _p: Dictionary) -> void: queue_redraw()

func _on_game_event(name: String, p: Dictionary) -> void:
	on_event(name, p)

func _layout() -> void:
	var top := 84.0 if title != "" else 24.0
	if not tabs.is_empty(): top += 44.0
	content = Rect2(frame_rect.position.x + 28, frame_rect.position.y + top, frame_rect.size.x - 56, frame_rect.size.y - top - 24)

func _process(delta: float) -> void:
	t += delta
	if toast_t > 0.0:
		toast_t -= delta
	queue_redraw()

func c():
	return Game.active()

func close() -> void:
	Audio.ui("ui_back")
	closed.emit(self)

func flash(text: String) -> void:
	toast = text
	toast_t = 2.4

## Submit an intent; show its failure text. Returns the result.
func submit(intent: Dictionary) -> Dictionary:
	var r := Game.submit(intent)
	if not r.get("ok", false):
		var why := str(r.get("text", str(r.get("reason", "")).replace("_", " ").capitalize()))
		if why != "": flash(why)
		Audio.ui("ui_error")
	return r

# ------------------------------------------------------------------ drawing
func _draw() -> void:
	_regions.clear()
	_areas.clear()
	_layout()
	if frameless:
		draw_page()
		if not confirm.is_empty(): _draw_confirm()
		_draw_toast()
		return
	# Dim the play screen behind the page.
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.01, 0.03, 0.04, 0.55 if modal else 0.72))
	draw_style_box(UiKit.style("major_window"), frame_rect)
	if title != "":
		var plaque := Rect2(frame_rect.position.x + frame_rect.size.x * 0.5 - 220, frame_rect.position.y + 10, 440, 60)
		draw_style_box(UiKit.style("title_plaque"), plaque)
		UiKit.draw_text(self, title, plaque.position + Vector2(0, 42), 34, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, plaque.size.x, true, true)
	var close_rect := Rect2(frame_rect.end.x - 70, frame_rect.position.y + 14, 52, 52)
	_register(close_rect, "_close", null, true, "", "button")
	draw_style_box(UiKit.style("close_button", "pressed" if _is_pressed("_close") else "normal"), close_rect)
	_draw_x(close_rect.get_center(), 11, UiKit.PAPER)
	if not tabs.is_empty(): _draw_tabs()
	draw_page()
	if not confirm.is_empty(): _draw_confirm()
	_draw_toast()

func _draw_toast() -> void:
	if toast_t > 0.0 and toast != "":
		var w := minf(760.0, UiKit.text_width(toast, 20) + 60)
		var r := Rect2(640 - w * 0.5, minf(frame_rect.end.y, 690) - 70, w, 46)
		draw_style_box(UiKit.style("toast"), r)
		UiKit.draw_text(self, toast, r.position + Vector2(0, 30), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, w)

func _draw_x(center: Vector2, r: float, col: Color) -> void:
	draw_line(center - Vector2(r, r), center + Vector2(r, r), UiKit.INK, 6)
	draw_line(center - Vector2(r, -r), center + Vector2(r, -r), UiKit.INK, 6)
	draw_line(center - Vector2(r, r), center + Vector2(r, r), col, 3)
	draw_line(center - Vector2(r, -r), center + Vector2(r, -r), col, 3)

func _draw_tabs() -> void:
	var x := frame_rect.position.x + 32
	var y := frame_rect.position.y + (84.0 if title != "" else 20.0)
	for i in tabs.size():
		var tb: Dictionary = tabs[i]
		var w := maxf(118.0, UiKit.text_width(str(tb.label), 20) + 40)
		var r := Rect2(x, y, w, 40)
		var locked := str(tb.get("locked", "")) != ""
		draw_style_box(UiKit.style("tab", "selected" if i == tab else ("disabled" if locked else "normal")), r)
		UiKit.draw_text(self, str(tb.label), r.position + Vector2(0, 27), 20, UiKit.PALE_GOLD if i == tab else (UiKit.HOLLOW if locked else UiKit.PAPER),
			HORIZONTAL_ALIGNMENT_CENTER, w)
		if locked: _lock_icon(r.position + Vector2(w - 16, 8))
		_register(r, "_tab", i, not locked, str(tb.get("locked", "")), "button")
		x += w + 6

func _lock_icon(p: Vector2) -> void:
	draw_rect(Rect2(p + Vector2(0, 6), Vector2(12, 9)), UiKit.BRONZE)
	draw_arc(p + Vector2(6, 6), 4, PI, TAU, 8, UiKit.BRONZE, 2)

## Button: registers a tap region. Disabled buttons still answer taps with their reason.
func btn(rect: Rect2, label: String, id: String, data = null, primary := false, enabled := true, reason := "", size := 22) -> void:
	var state := "normal"
	if not enabled: state = "disabled"
	elif _is_pressed(id, data): state = "pressed"
	draw_style_box(UiKit.style("button_primary" if primary else "button_secondary", state), rect)
	var off := Vector2(1, 2) if state == "pressed" else Vector2.ZERO
	var col := UiKit.PALE_GOLD if primary else UiKit.PAPER
	if not enabled: col = UiKit.HOLLOW
	# A long label steps its size down to sit inside the button (and clear the lock icon) rather than touch the frame.
	var room := rect.size.x - (44.0 if not enabled and reason != "" else 20.0)
	if label.length() * size * 0.6 > room:   # only a label that could overflow is measured
		while size > 13 and UiKit.text_width(label, size) > room: size -= 1
	UiKit.draw_text(self, label, rect.position + off + Vector2(0, rect.size.y * 0.5 + size * 0.35), size, col, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x)
	if not enabled and reason != "": _lock_icon(rect.position + Vector2(rect.size.x - 20, 6))
	_register(rect, id, data, enabled, reason, "button")

## Invisible tap region (rows, cards, map nodes).
func region(rect: Rect2, id: String, data = null, enabled := true, reason := "") -> void:
	_register(rect, id, data, enabled, reason, "region")

func _register(rect: Rect2, id: String, data, enabled: bool, reason: String, kind: String) -> void:
	# Regions inside a scroll area are clipped to it.
	for aid in _areas:
		var a: Dictionary = _areas[aid]
		if a.get("active", false):
			rect = rect.intersection(a.rect)
			if rect.size.x <= 0 or rect.size.y <= 0: return
	_regions.append({"rect": rect, "id": id, "data": data, "enabled": enabled, "reason": reason, "kind": kind})

func _is_pressed(id: String, data = null) -> bool:
	if _pressed < 0 or _pressed >= _prev_regions.size(): return false
	var r: Dictionary = _prev_regions[_pressed]
	return r.id == id and (data == null or r.data == data)

var _prev_regions: Array = []

func text(pos: Vector2, s: String, size := 20, col := UiKit.PAPER, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0, display := false) -> void:
	UiKit.draw_text(self, s, pos, size, col, align, width, true, display)

## `s` shortened with an ellipsis so it fits `width` at `size`.
func fit(s: String, size: int, width: float) -> String:
	if UiKit.text_width(s, size) <= width: return s
	var n := s.length()
	while n > 1 and UiKit.text_width(s.left(n) + "…", size) > width: n -= 1
	return s.left(n).strip_edges() + "…"

func heading(pos: Vector2, s: String, width := 400.0) -> void:
	UiKit.draw_text(self, s, pos, 26, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, width, true, true)
	draw_line(pos + Vector2(0, 8), pos + Vector2(minf(width, UiKit.text_width(s, 26, true) + 30), 8), UiKit.BRONZE, 2)

## Word-wrapped paragraph. Returns the height used.
func para(rect: Rect2, s: String, size := 19, col := UiKit.PAPER, max_lines := -1) -> float:
	var lines := _wrap(s, size, rect.size.x)
	var lh := UiKit.line_height(size)
	var y := rect.position.y + size * UiKit.text_scale()
	var n := 0
	for ln in lines:
		if max_lines > 0 and n >= max_lines: break
		if y > rect.end.y + 2: break
		UiKit.draw_text(self, ln, Vector2(rect.position.x, y), size, col)
		y += lh
		n += 1
	return n * lh

func _wrap(s: String, size: int, width: float) -> Array:
	var out: Array = []
	for raw in s.split("\n"):
		var cur := ""
		for w in raw.split(" "):
			var cand := w if cur == "" else cur + " " + w
			if UiKit.text_width(cand, size) > width and cur != "":
				out.append(cur)
				cur = w
			else:
				cur = cand
		out.append(cur)
	return out

func bar(rect: Rect2, frac: float, col: Color, label := "") -> void:
	draw_style_box(UiKit.style("bar_shell"), rect)
	var inner := rect.grow_individual(-6, -5, -6, -5)
	draw_rect(inner, Color(0.02, 0.05, 0.06))
	draw_rect(Rect2(inner.position, Vector2(inner.size.x * clampf(frac, 0.0, 1.0), inner.size.y)), col)
	draw_rect(Rect2(inner.position, Vector2(inner.size.x * clampf(frac, 0.0, 1.0), 2)), col.lightened(0.35))
	if label != "": UiKit.draw_outlined(self, label, rect.position + Vector2(0, rect.size.y * 0.5 + 7), 17, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x)

func panel(rect: Rect2, asset := "minor_panel", state := "normal") -> void:
	draw_style_box(UiKit.style(asset, state), rect)

## Item slot with icon, count, quality edge and state overlays.
func slot_box(rect: Rect2, item_id: String, count := 0, quality := "", id := "", data = null, selected := false, locked := false) -> void:
	draw_style_box(UiKit.style("slot", "pressed" if (id != "" and _is_pressed(id, data)) else "normal"), rect)
	if item_id != "":
		var tex := SpriteCache.icon(item_id)
		var inner := rect.grow(-6)
		if quality.begins_with("pill_"): _pill_glow(rect, quality)
		if tex: draw_texture_rect(tex, inner, false)
		else:
			draw_rect(inner, UiKit.DEEP_TEAL)
			text(inner.position + Vector2(0, inner.size.y * 0.6), ContentDB.item_name(item_id).left(3), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, inner.size.x)
		if quality != "" and quality != "plain" and quality != "common":
			draw_rect(rect.grow(-3), UiKit.quality_color(quality), false, 2)
		if count > 1:
			UiKit.draw_outlined(self, str(count), rect.end - Vector2(rect.size.x, 5), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, rect.size.x - 5)
		if locked: _lock_icon(rect.position + Vector2(4, 4))
	if selected: draw_style_box(UiKit.style("selected_slot_glow"), rect.grow(4))
	if id != "": region(rect, id, data)

## Pill marks (G1): one short gold line per mark along the slot's foot, 0-9.
func pill_marks(rect: Rect2, marks: int) -> void:
	if marks <= 0: return
	var w := 3.0
	var gap := 2.0
	var total := marks * w + (marks - 1) * gap
	var x0 := rect.get_center().x - total * 0.5
	for i in marks:
		var lr := Rect2(x0 + i * (w + gap), rect.end.y - 12, w, 7)
		draw_rect(lr.grow(1), Color(UiKit.INK, 0.8))
		draw_rect(lr, UiKit.GOLD)

## Pill Grain, Halo and Soul (S15): a soft pulsing halo behind the icon and a corner mark
## (dot, ring, star) so the quality reads without relying on colour.
func _pill_glow(rect: Rect2, quality: String) -> void:
	var col := UiKit.quality_color(quality)
	var c := rect.get_center()
	var pulse := 0.5 + 0.5 * sin(t * 2.4)
	for i in 4:
		draw_circle(c, rect.size.x * (0.34 + 0.05 * i), Color(col.r, col.g, col.b, (0.16 - 0.035 * i) * (0.7 + 0.3 * pulse)))
	var m := rect.position + Vector2(11, 11)
	match quality:
		"pill_grain": draw_circle(m, 3.5, col)
		"pill_halo": draw_arc(m, 4.5, 0.0, TAU, 16, col, 2.0)
		"pill_soul":
			for a in 4:
				draw_line(m - Vector2.from_angle(a * PI / 4.0) * 5.0, m + Vector2.from_angle(a * PI / 4.0) * 5.0, col, 1.6)

func icon_at(rect: Rect2, icon_id: String) -> void:
	var tex := SpriteCache.icon(icon_id)
	if tex: draw_texture_rect(tex, rect, false)

## One creature-sheet frame fitted into `rect`, feet on its bottom edge. `action`
## loops with the page clock. Returns false when the creature has no sheet.
func creature_at(rect: Rect2, creature_id: String, action := "idle", modulate := Color.WHITE) -> bool:
	return UiKit.draw_creature(self, rect, creature_id, action, t, modulate)

func currency_pill(pos: Vector2, currency: String, amount: int) -> float:
	var s := UiKit.fmt(amount)
	var w := UiKit.text_width(s, 18) + 52
	var r := Rect2(pos, Vector2(w, 34))
	draw_style_box(UiKit.style("currency_pill"), r)
	icon_at(Rect2(pos + Vector2(8, 5), Vector2(24, 24)), {"silver_tael": "coin", "spirit_stone": "spirit_stone", "contribution": "contribution"}.get(currency, "coin"))
	text(pos + Vector2(38, 24), s, 18, UiKit.PALE_GOLD)
	return w

## Scrolling list: calls draw_row(i, rect) for rows inside `rect`; drag or wheel to scroll.
func list(area: String, rect: Rect2, count: int, row_h: float, draw_row: Callable) -> void:
	var total := count * row_h
	var max_scroll := maxf(0.0, total - rect.size.y)
	var off := clampf(float(scroll.get(area, 0.0)), 0.0, max_scroll)
	scroll[area] = off
	_areas[area] = {"rect": rect, "max": max_scroll, "active": false}
	_regions.append({"rect": rect, "id": "_scroll", "data": area, "enabled": true, "reason": "", "kind": "scroll"})
	var first := int(off / row_h)
	var last := mini(count - 1, int((off + rect.size.y) / row_h))
	_areas[area].active = true
	for i in range(first, last + 1):
		var y := rect.position.y + i * row_h - off
		var rr := Rect2(rect.position.x, y, rect.size.x - 10, row_h - 4)
		if rr.position.y < rect.position.y - 1 or rr.end.y > rect.end.y + 1: continue
		draw_row.call(i, rr)
	_areas[area].active = false
	if max_scroll > 0:
		var track := Rect2(rect.end.x - 6, rect.position.y, 4, rect.size.y)
		draw_rect(track, Color(1, 1, 1, 0.08))
		var h := maxf(24.0, rect.size.y * rect.size.y / total)
		draw_rect(Rect2(track.position.x, rect.position.y + (rect.size.y - h) * off / max_scroll, 4, h), UiKit.JADE)

func ask(text_: String, id: String, data = null, danger := false) -> void:
	confirm = {"text": text_, "id": id, "data": data, "danger": danger}

func _draw_confirm() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0, 0, 0, 0.5))
	var r := Rect2(390, 250, 500, 220)
	draw_style_box(UiKit.style("major_window"), r)
	para(Rect2(r.position + Vector2(34, 30), Vector2(432, 110)), str(confirm.text), 21)
	btn(Rect2(r.position.x + 40, r.end.y - 76, 190, 54), Tx.t("ui.page.cancel"), "_confirm_no")
	btn(Rect2(r.end.x - 230, r.end.y - 76, 190, 54), Tx.t("ui.page.confirm"), "_confirm_yes", null, true)

# ------------------------------------------------------------------ input
func _hit(p: Vector2) -> int:
	var regs := _prev_regions
	if not confirm.is_empty():
		for i in range(regs.size() - 1, -1, -1):
			if str(regs[i].id).begins_with("_confirm") and (regs[i].rect as Rect2).has_point(p): return i
		return -1
	for i in range(regs.size() - 1, -1, -1):
		if (regs[i].rect as Rect2).has_point(p) and regs[i].kind != "scroll": return i
	return -1

func _scroll_area_at(p: Vector2) -> String:
	for r in _prev_regions:
		if r.kind == "scroll" and (r.rect as Rect2).has_point(p): return str(r.data)
	return ""

func _gui_input(event: InputEvent) -> void:
	_prev_regions = _regions.duplicate()
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and event.pressed:
			var a := _scroll_area_at(event.position)
			if a != "": scroll[a] = float(scroll.get(a, 0.0)) + (-60.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 60.0)
			accept_event()
			return
		if event.button_index != MOUSE_BUTTON_LEFT: return
		if event.pressed:
			_pressed = _hit(event.position)
			_press_pos = event.position
			_dragged = false
			_drag_area = _scroll_area_at(event.position)
			_drag_last = event.position.y
		else:
			var idx := _hit(event.position)
			if idx >= 0 and idx == _pressed and not _dragged: _activate(_prev_regions[idx])
			elif _pressed < 0 and confirm.is_empty() and not frameless and not frame_rect.has_point(event.position) and not _dragged: close()
			_pressed = -1
			_drag_area = ""
		accept_event()
	elif event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_LEFT:
		if _drag_area != "" and (event.position - _press_pos).length() > 10.0:
			_dragged = true
			scroll[_drag_area] = float(scroll.get(_drag_area, 0.0)) - (event.position.y - _drag_last)
			_drag_last = event.position.y
			_pressed = -1
		accept_event()

func _activate(r: Dictionary) -> void:
	var id := str(r.id)
	if not r.enabled:
		if str(r.reason) != "": flash(str(r.reason))
		Audio.ui("ui_error")
		return
	Audio.ui("ui_tap")
	match id:
		"_close": close()
		"_tab":
			tab = int(r.data)
			scroll.clear()
			on_action("_tab", tabs[tab].id)
		"_confirm_no": confirm = {}
		"_confirm_yes":
			var cf := confirm
			confirm = {}
			on_action(str(cf.id), cf.data)
		_: on_action(id, r.data)

func _unhandled_key_input(event: InputEvent) -> void:
	if event.pressed and not event.echo and event.keycode in [KEY_ESCAPE]:
		if not confirm.is_empty(): confirm = {}
		elif frameless: return
		else: close()
		get_viewport().set_input_as_handled()
