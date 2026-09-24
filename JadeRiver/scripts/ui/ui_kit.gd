class_name UiKit
extends RefCounted
## Art tokens (Part 9.2), fonts and nine-slice styles from data/ui_assets.json.
## Display headers use Cormorant Garamond; body text, labels and numbers use
## Pixelify Sans (Part 9.2 · Typography).

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
static var _body: Font
static var _styles: Dictionary = {}

static func display_font() -> Font:
	if _display == null:
		var fv := FontVariation.new()
		var base: FontFile = load("res://art/fonts/CormorantGaramond.ttf")
		base.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
		fv.base_font = base
		fv.variation_opentype = {"wght": 600}
		_display = fv
	return _display

static func body_font() -> Font:
	if _body == null:
		var f: FontFile = load("res://art/fonts/PixelifySans.ttf")
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.hinting = TextServer.HINTING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		_body = f
	return _body

static func text_scale() -> float:
	var s := int(Game.account.settings.get("text_size", 1)) if Game else 1
	return [0.9, 1.0, 1.15][clampi(s, 0, 2)]

## Nine-slice StyleBoxTexture for a kit asset and state.
static func style(asset: String, state := "normal", content_margin := -1.0) -> StyleBox:
	var key := asset + ":" + state + ":" + str(content_margin)
	if _styles.has(key): return _styles[key]
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

static func draw_text(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0, shadow := true, display := false) -> void:
	var f := display_font() if display else body_font()
	if shadow: ci.draw_string(f, pos + Vector2(0, 2), text, align, width, size, Color(0, 0, 0, 0.85 * color.a))
	ci.draw_string(f, pos, text, align, width, size, color)

static func draw_outlined(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_CENTER, width := 200.0) -> void:
	var f := body_font()
	ci.draw_string_outline(f, pos, text, align, width, size, 4, Color(INK, color.a))
	ci.draw_string(f, pos, text, align, width, size, color)

static func text_width(text: String, size: int, display := false) -> float:
	return (display_font() if display else body_font()).get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x

static func quality_color(q: String) -> Color:
	return Color(str(ContentDB.config("grades").get("quality_colors", {}).get(q, "#e8e1cf")))

static func grade_color(g: String) -> Color:
	return Color(str(ContentDB.config("grades").get("grade_colors", {}).get(g, "#e8e1cf")))

static func badge_color(kind: String) -> Color:
	return {"grey": Color("8c969a"), "green": Color("67d67a"), "white": PAPER, "orange": Color("f0a040"), "red": RED}.get(kind, PAPER)

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
