# UI kit: jade / ink / gold theme and small constructors used by every screen.
class_name UI
extends RefCounted

const INK := Color("#0b1416")
const PANEL := Color("#0f2626")
const PANEL2 := Color("#153434")
const PANEL3 := Color("#1c4040")
const GOLD := Color("#d9b25c")
const GOLD_D := Color("#8a6a30")
const JADE := Color("#3fd1b0")
const JADE_D := Color("#1f6b5a")
const CREAM := Color("#f0e6cc")
const DIM := Color("#8fa8a0")
const RED := Color("#e0564a")
const BLUE := Color("#3a9ad8")
const GREEN := Color("#6fe08a")

static var _theme: Theme
static var _font: Font
static var _font_title: Font


static func font() -> Font:
	if _font == null:
		var f := SystemFont.new()
		f.font_names = PackedStringArray(["Alegreya Sans", "Philosopher", "Palatino Linotype", "Book Antiqua", "Georgia", "Noto Serif", "DejaVu Serif", "serif"])
		f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		_font = f
	return _font


static func title_font() -> Font:
	if _font_title == null:
		var f := SystemFont.new()
		f.font_names = PackedStringArray(["Cinzel", "Trajan Pro", "Palatino Linotype", "Georgia", "Noto Serif", "DejaVu Serif", "serif"])
		f.font_weight = 700
		_font_title = f
	return _font_title


static func box(bg: Color, border: Color, bw := 2, radius := 6, pad := 10) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(bw)
	s.set_corner_radius_all(radius)
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.6
	s.content_margin_bottom = pad * 0.6
	s.shadow_color = Color(0, 0, 0, 0.35)
	s.shadow_size = 2
	return s


static func theme() -> Theme:
	if _theme != null:
		return _theme
	var t := Theme.new()
	t.default_font = font()
	t.default_font_size = 20
	t.set_color("font_color", "Label", CREAM)
	t.set_color("font_color", "Button", CREAM)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", GOLD)
	t.set_color("font_disabled_color", "Button", Color(0.55, 0.6, 0.58))
	t.set_color("font_focus_color", "Button", CREAM)
	t.set_stylebox("normal", "Button", box(PANEL2, GOLD_D, 2, 6, 12))
	t.set_stylebox("hover", "Button", box(PANEL3, GOLD, 2, 6, 12))
	t.set_stylebox("pressed", "Button", box(Color("#0a1c1c"), GOLD, 2, 6, 12))
	t.set_stylebox("disabled", "Button", box(Color("#162222"), Color("#3a4a44"), 2, 6, 12))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_stylebox("panel", "PanelContainer", box(Color(PANEL, 0.97), GOLD, 2, 8, 14))
	t.set_stylebox("panel", "Panel", box(Color(PANEL, 0.97), GOLD, 2, 8, 14))
	t.set_stylebox("normal", "LineEdit", box(Color("#081414"), GOLD_D, 2, 4, 10))
	t.set_stylebox("focus", "LineEdit", box(Color("#081414"), GOLD, 2, 4, 10))
	t.set_color("font_color", "LineEdit", Color("#d8c8ff"))
	t.set_color("caret_color", "LineEdit", GOLD)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0)
	t.set_stylebox("panel", "ScrollContainer", sb)
	var grab := box(GOLD_D, GOLD_D, 0, 3, 0)
	t.set_stylebox("grabber", "VScrollBar", grab)
	t.set_stylebox("grabber_highlight", "VScrollBar", box(GOLD, GOLD, 0, 3, 0))
	t.set_stylebox("grabber_pressed", "VScrollBar", box(GOLD, GOLD, 0, 3, 0))
	t.set_stylebox("scroll", "VScrollBar", box(Color(0, 0, 0, 0.3), Color(0, 0, 0, 0), 0, 3, 3))
	t.set_constant("separation", "HBoxContainer", 10)
	t.set_constant("separation", "VBoxContainer", 8)
	t.set_constant("h_separation", "GridContainer", 8)
	t.set_constant("v_separation", "GridContainer", 8)
	_theme = t
	return t


# ---------------------------------------------------------------- constructors
static func label(text: String, size := 20, color := CREAM, align := HORIZONTAL_ALIGNMENT_LEFT, wrap := false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = align
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = 60
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func title(text: String, size := 34) -> Label:
	var l := label(text, size, GOLD, HORIZONTAL_ALIGNMENT_CENTER)
	l.add_theme_font_override("font", title_font())
	l.add_theme_color_override("font_outline_color", Color("#1a0e04"))
	l.add_theme_constant_override("outline_size", 6)
	return l


static func button(text: String, cb: Callable, size := 20, kind := "normal", min_w := 0.0) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", size)
	b.custom_minimum_size = Vector2(min_w, 48)
	b.focus_mode = Control.FOCUS_NONE
	if kind == "gold":
		b.add_theme_stylebox_override("normal", box(Color("#3a2c10"), GOLD, 3, 8, 14))
		b.add_theme_stylebox_override("hover", box(Color("#4a3814"), Color("#ffe08a"), 3, 8, 14))
		b.add_theme_stylebox_override("pressed", box(Color("#2a1e08"), GOLD, 3, 8, 14))
		b.add_theme_color_override("font_color", Color("#ffe8b0"))
	elif kind == "jade":
		b.add_theme_stylebox_override("normal", box(Color("#12453c"), JADE, 2, 8, 14))
		b.add_theme_stylebox_override("hover", box(Color("#18574c"), Color("#8ff0d8"), 2, 8, 14))
		b.add_theme_stylebox_override("pressed", box(Color("#0c3029"), JADE, 2, 8, 14))
	elif kind == "tab":
		b.add_theme_stylebox_override("normal", box(Color("#0f2424"), Color("#2f5a50"), 2, 12, 16))
		b.add_theme_stylebox_override("hover", box(Color("#143030"), GOLD_D, 2, 12, 16))
	elif kind == "tab_on":
		b.add_theme_stylebox_override("normal", box(Color("#2a2410"), GOLD, 2, 12, 16))
		b.add_theme_stylebox_override("hover", box(Color("#2a2410"), GOLD, 2, 12, 16))
		b.add_theme_color_override("font_color", Color("#ffe8b0"))
	elif kind == "flat":
		b.add_theme_stylebox_override("normal", box(Color(0, 0, 0, 0.25), Color(0, 0, 0, 0), 0, 6, 8))
		b.add_theme_stylebox_override("hover", box(Color(1, 1, 1, 0.06), GOLD_D, 1, 6, 8))
	if cb.is_valid():
		b.pressed.connect(cb)
	return b


static func icon(tex: Texture2D, size := 40.0) -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = Vector2(size, size)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func icon_button(tex: Texture2D, text: String, cb: Callable, size := 56.0, font_size := 16) -> Button:
	var b := Button.new()
	b.icon = tex
	b.text = text
	b.expand_icon = true
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	b.add_theme_font_size_override("font_size", font_size)
	b.add_theme_constant_override("icon_max_width", int(size * 0.62))
	b.custom_minimum_size = Vector2(size, size + (font_size + 4 if text != "" else 0))
	b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	b.focus_mode = Control.FOCUS_NONE
	if cb.is_valid():
		b.pressed.connect(cb)
	return b


static func hbox(sep := 10) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


static func vbox(sep := 8) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


static func panel(bg := PANEL, border := GOLD, pad := 14) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", box(Color(bg, 0.96), border, 2, 8, pad))
	return p


static func sub_panel(pad := 10) -> PanelContainer:
	return panel(Color("#0b1e1e"), Color("#2f5a50"), pad)


static func spacer(w := 0.0, h := 0.0, expand := false) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w, h)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if expand:
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		c.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return c


static func sep_line(color := GOLD_D) -> ColorRect:
	var r := ColorRect.new()
	r.color = color
	r.custom_minimum_size = Vector2(10, 2)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


static func bar(frac: float, color: Color, w := 200.0, h := 14.0, text := "") -> Control:
	var b := Bar.new()
	b.frac = frac
	b.color = color
	b.text = text
	b.custom_minimum_size = Vector2(w, h)
	return b


static func scroll(child: Control, min_h := 200.0) -> ScrollContainer:
	var s := ScrollContainer.new()
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	s.custom_minimum_size.y = min_h
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	child.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(child)
	return s


static func clear(n: Node) -> void:
	for c in n.get_children():
		n.remove_child(c)
		c.queue_free()


static func expand(c: Control, h := true, v := false) -> Control:
	if h:
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if v:
		c.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return c


class Bar extends Control:
	var frac := 1.0
	var color := Color.RED
	var text := ""

	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, Color(0, 0, 0, 0.55))
		var f := clampf(frac, 0, 1)
		if f > 0:
			draw_rect(Rect2(1, 1, (size.x - 2) * f, size.y - 2), color)
			draw_rect(Rect2(1, 1, (size.x - 2) * f, maxf(1, (size.y - 2) * 0.35)), color.lightened(0.25))
		draw_rect(r, Color(0, 0, 0, 0.8), false, 1)
		if text != "":
			var fnt := UI.font()
			var fs := int(size.y * 0.85)
			draw_string(fnt, Vector2(0, size.y * 0.5 + fs * 0.36), text, HORIZONTAL_ALIGNMENT_CENTER, size.x, fs, Color.WHITE)

	func set_value(f: float, t := "") -> void:
		if f != frac or t != text:
			frac = f
			text = t
			queue_redraw()
