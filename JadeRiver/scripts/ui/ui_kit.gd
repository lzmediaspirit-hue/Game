class_name UiKit
extends RefCounted
## Art tokens (Part 9.2), fonts and nine-slice styles from data/ui_assets.json.
## Typography (S24 style): pages set words and figures in Cormorant Garamond (semi-bold
## for text, bold for display headers, lining figures). Numbers drawn over the world
## (damage numbers, HUD counters, outlined labels) use Pixelify Sans to match the
## pixel art. Both are anti-aliased and rasterized at the device's resolution
## (canvas_items stretch), so text stays crisp at any phone scale.

const INK := Color("071015")
const RIVER_NIGHT := Color("0a2027")
const DEEP_TEAL := Color("0d3035")
const JADE_SHADOW := Color("15514f")
const JADE := Color("2c9e8f")
const BRIGHT_JADE := Color("67d6bd")
const BRONZE := Color("9a6a35")
const GOLD := Color("e5b84c")
const PALE_GOLD := Color("ffe6a1")
const PAPER := Color("e8e1cf")
const MIST := Color("afc9d1")
const RED := Color("e45858")
const QI := Color("32bed1")
const SOUL := Color("9b78d1")
const HOLLOW := Color("87949a")

static var _display: Font
static var _text: Font
static var _body: Font
static var _styles: Dictionary = {}
static var _numeric: Dictionary = {}
static var _num_re: RegEx
## Cormorant sits smaller on its body than Pixelify: at 1.2x the requested size it matches
## the widths the layouts were drawn for, with a taller x-height.
const WORD_SCALE := 1.2

static var _symbols: FontFile

## Check marks, stars and arrows Cormorant and Pixelify lack (a renamed DejaVu subset).
static func symbols_font() -> FontFile:
	if _symbols == null:
		_symbols = load("res://art/fonts/JadeRiverSymbols.ttf")
		_symbols.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	return _symbols

static func _cormorant(weight: int, spacing := 0) -> Font:
	var base: FontFile = load("res://art/fonts/CormorantGaramond.ttf")
	base.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	base.hinting = TextServer.HINTING_LIGHT
	base.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO
	base.fallbacks = [symbols_font()]
	var fv := FontVariation.new()
	fv.base_font = base
	fv.variation_opentype = {"wght": weight}
	# Lining figures: Cormorant's default old-style 0 reads as the letter o ("Lv 0").
	fv.opentype_features = {TextServerManager.get_primary_interface().name_to_tag("lnum"): 1}
	if spacing != 0: fv.spacing_glyph = spacing
	return fv

## Headers, titles and plaques.
static func display_font() -> Font:
	if _display == null: _display = _cormorant(700)
	return _display

## Labels, names, paragraphs and buttons.
static func text_font() -> Font:
	if _text == null: _text = _cormorant(650)
	return _text

## Numbers: Pixelify Sans, smoothed so its pixel strokes scale evenly on any screen.
static func body_font() -> Font:
	if _body == null:
		var f: FontFile = load("res://art/fonts/PixelifySans.ttf")
		f.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		f.hinting = TextServer.HINTING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		f.fallbacks = [symbols_font()]
		_body = f
	return _body

## True for strings of digits and signs only ("84/84", "+12%", "3 / 28").
static func is_numeric(s: String) -> bool:
	if _numeric.has(s): return _numeric[s]
	if _num_re == null: _num_re = RegEx.create_from_string("^[0-9\\s.,:/%+\\-−×()#]+$")
	if _numeric.size() > 4000: _numeric.clear()
	_numeric[s] = _num_re.search(s) != null
	return _numeric[s]

static func font_for(_s: String, display := false) -> Font:
	return display_font() if display else text_font()

## The size a string is drawn at: Cormorant scales up to match the layout grid.
static func size_for(_s: String, size: int, _display := false) -> int:
	return int(round(size * WORD_SCALE))

static func text_scale() -> float:
	var s := int(Game.account.settings.get("text_size", 1)) if Game else 1
	return [0.9, 1.0, 1.15][clampi(s, 0, 2)]

## Nine-slice StyleBoxTexture for a kit asset and state.
static func style(asset: String, state := "normal", content_margin := -1.0) -> StyleBox:
	var key := asset + ":" + state + ":" + str(content_margin)
	if _styles.has(key): return _styles[key]
	var hd := _hd_style(asset, state, content_margin)
	if hd:
		_styles[key] = hd
		return hd
	var e: Dictionary = ContentDB.config("ui_assets").get(asset, {})
	var path := str(e.get(state, e.get("normal", "")))
	var texture: Texture2D = SpriteCache.tex(path)
	if texture == null:
		var flat := StyleBoxFlat.new()
		flat.bg_color = RIVER_NIGHT
		flat.border_color = JADE
		flat.set_border_width_all(2)
		_styles[key] = flat
		return flat
	var sb := StyleBoxTexture.new()
	sb.texture = texture
	var m: Array = e.get("margins", [8, 8, 8, 8])
	sb.texture_margin_left = float(m[0])
	sb.texture_margin_top = float(m[1])
	sb.texture_margin_right = float(m[2])
	sb.texture_margin_bottom = float(m[3])
	var cm := content_margin if content_margin >= 0 else maxf(8.0, float(m[0]) * 0.6)
	sb.content_margin_left = cm
	sb.content_margin_right = cm
	sb.content_margin_top = cm * 0.6
	sb.content_margin_bottom = cm * 0.6
	_styles[key] = sb
	return sb

## The HD kit's version of an asset (data/ui_assets_hd.json), or null when it has none.
static func _hd_style(asset: String, state: String, content_margin: float) -> StyleBox:
	var kit: Dictionary = ContentDB.config("ui_assets_hd")
	var e: Dictionary = kit.get(asset, {})
	var path := str(e.get(state, e.get("normal", "")))
	var image: Texture2D = SpriteCache.tex(path)
	if image == null: return null
	var ct := CanvasTexture.new()
	ct.diffuse_texture = image
	ct.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	var sb := HdStyleBox.new()
	sb.texture = ct
	sb.size_px = image.get_size()
	sb.scale = float(kit.get("scale", 3))
	var m: Array = e.get("margins", [8, 8, 8, 8])
	sb.margins = [float(m[0]), float(m[1]), float(m[2]), float(m[3])]
	var cm := content_margin if content_margin >= 0 else maxf(8.0, float(m[0]) * 0.6)
	sb.content_margin_left = cm
	sb.content_margin_right = cm
	sb.content_margin_top = cm * 0.6
	sb.content_margin_bottom = cm * 0.6
	return sb

static func draw_text(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0, shadow := true, display := false) -> void:
	var f := font_for(text, display)
	var px := size_for(text, size, display)
	if shadow:
		# A soft two-step drop shadow reads on painted backgrounds without a hard black edge.
		ci.draw_string(f, pos + Vector2(0, 2), text, align, width, px, Color(0, 0, 0, 0.55 * color.a))
		ci.draw_string(f, pos + Vector2(1, 1), text, align, width, px, Color(0, 0, 0, 0.45 * color.a))
	ci.draw_string(f, pos, text, align, width, px, color)

## World labels (names, damage numbers, prompts) over painted scenes: bold face, a thin ink
## outline and a soft shadow, so serifs stay sharp instead of drowning in a heavy stroke.
static func draw_outlined(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_CENTER, width := 200.0) -> void:
	var numeric := is_numeric(text)
	var f := body_font() if numeric else display_font()
	var px := size if numeric else int(round(size * WORD_SCALE))
	ci.draw_string_outline(f, pos + Vector2(0, 2), text, align, width, px, 5, Color(0, 0, 0, 0.3 * color.a))
	ci.draw_string_outline(f, pos, text, align, width, px, 3 if not numeric else 4, Color(INK, 0.92 * color.a))
	ci.draw_string(f, pos, text, align, width, px, color)

static var _plate: StyleBoxFlat

## A world nameplate: name (and an optional second line) on a soft translucent ink plate,
## centred on x = 0 with the name's baseline at `y`. Returns the plate's rect.
static func draw_nameplate(ci: CanvasItem, name_text: String, sub: String, y: float, color := PAPER, sub_color := MIST, size := 16) -> Rect2:
	if _plate == null:
		_plate = StyleBoxFlat.new()
		_plate.bg_color = Color(0.02, 0.06, 0.075, 0.62)
		_plate.set_corner_radius_all(7)
		_plate.border_color = Color(0.9, 0.75, 0.4, 0.22)
		_plate.set_border_width_all(1)
		_plate.anti_aliasing = true
	var sub_size := size - 3
	var w := text_width(name_text, size, true)
	if sub != "": w = maxf(w, text_width(sub, sub_size))
	var h := size * WORD_SCALE + (sub_size * WORD_SCALE + 2 if sub != "" else 0.0)
	var rect := Rect2(-w * 0.5 - 9, y - size * WORD_SCALE * 0.95, w + 18, h + 7)
	_plate.bg_color.a = 0.62 * color.a
	ci.draw_style_box(_plate, rect)
	draw_text(ci, name_text, Vector2(-w * 0.5 - 20, y), size, color, HORIZONTAL_ALIGNMENT_CENTER, w + 40, true, true)
	if sub != "":
		draw_text(ci, sub, Vector2(-w * 0.5 - 20, y + sub_size * WORD_SCALE + 2), sub_size, sub_color, HORIZONTAL_ALIGNMENT_CENTER, w + 40, true)
	return rect

static var _widths: Dictionary = {}   # measured widths, so labels drawn every frame are measured once

static func text_width(text: String, size: int, display := false) -> float:
	var key := "%d|%s|%s" % [size, "d" if display else "b", text]
	if _widths.has(key): return float(_widths[key])
	if _widths.size() > 4000: _widths.clear()
	var w: float = font_for(text, display).get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size_for(text, size, display)).x
	_widths[key] = w
	return w

static func quality_color(q: String) -> Color:
	return Color(str(ContentDB.config("grades").get("quality_colors", {}).get(q, "#e8e1cf")))

static func grade_color(g: String) -> Color:
	return Color(str(ContentDB.config("grades").get("grade_colors", {}).get(g, "#e8e1cf")))

static func badge_color(kind: String) -> Color:
	return {"grey": Color("8c969a"), "green": Color("67d67a"), "white": PAPER, "orange": Color("f0a040"), "red": RED}.get(kind, PAPER)

## A stat modifier (an affix, a title, a physique) as a line: "+24 accuracy", "+3% physical attack", "-10% fire power".
static func affix_text(a: Dictionary) -> String:
	var v := float(a.get("value", 0.0))
	var stat := str(a.get("stat", ""))
	var pct := str(a.get("op", "flat")) != "flat" or _stat_is_percent(stat)
	var mag := ("%d%%" % int(round(absf(v) * 100))) if pct else fmt(absf(v))
	var label := stat.replace("_", " ")
	var el := str((a.get("condition", {}) as Dictionary).get("element", "")) if a.get("condition") is Dictionary else ""
	if el != "" and stat == "elemental_power": label = el + " power"
	elif el != "": label = el + " " + label
	return "%s%s %s" % ["-" if v < 0.0 else "+", mag, label]

static func _stat_is_percent(stat: String) -> bool:
	for s in ContentDB.stat_const("stats", []):
		if str(s.get("id", "")) == stat: return str(s.get("format", "")) == "percent"
	return false

## A countdown: "m:ss" under an hour, "h:mm:ss" past it, "Nd Nh" past a day.
static func clock(seconds: float) -> String:
	var s := maxi(0, int(ceil(seconds)))
	if s >= 86400: return Tx.t("ui.clock_days") % [s / 86400, (s % 86400) / 3600]
	if s >= 3600: return "%d:%02d:%02d" % [s / 3600, (s % 3600) / 60, s % 60]
	return "%d:%02d" % [s / 60, s % 60]

static func fmt(n: float) -> String:
	var v := int(round(n))
	var s := str(absi(v))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if v < 0 else "") + s + out

## Pale-gold key-pattern corner jewels used on HUD panels drawn procedurally.
static func draw_frame(ci: CanvasItem, rect: Rect2, asset := "minor_panel", state := "normal") -> void:
	ci.draw_style_box(style(asset, state), rect)
