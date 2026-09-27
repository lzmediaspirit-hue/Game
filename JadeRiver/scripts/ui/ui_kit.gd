class_name UiKit
extends RefCounted
## Art tokens (Part 9.2), fonts and nine-slice styles from data/ui_assets.json.
## Typography (S24 style): words are set in Source Serif 4 (semi-bold for text, bold for
## world labels, small optical size so strokes hold up on a phone) and headings in
## Cormorant Garamond Bold. Numbers drawn over the world (damage numbers, HUD counters,
## outlined labels) use Pixelify Sans to match the pixel art. All are anti-aliased and
## rasterized at the device's resolution (canvas_items stretch), so text stays crisp at
## any phone scale. Settings > Accessibility > Text size scales every word.

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
## P6 moments: the three colours that moved out of world.gd with their rows, named here for the style guide to rename.
const HEAVEN_CLOUD := Color("f5c86a")   # a realm phenomenon's auspicious clouds
const HEAVEN_BOLT := Color("9fc4ff")    # a tribulation's lightning
const BODY := Color("f0a060")           # the body ladder
## P4 (docs/ui_style_guide.md §1.5, §10): the roles the palette above left to literals. RED, SOUL and JADE are fills;
## words take RED_TEXT, SOUL_TEXT and BRIGHT_JADE, which pass 4.5:1 on the lightest page fill.
const RED_TEXT := Color("e87070")      # negative words: danger, unmet needs, costs, sin
const SOUL_TEXT := Color("a586d6")     # Soul words
const WARNING := Color("f0a040")       # a soft need, moderate risk, a meter past its mark
const HP := Color("c2474f")            # the player's HP fill
const BLOOD := Color("b3202e")         # the Blood path, the heart demon, the boss trough
const HEART := Color("e05a6e")         # affection
const SKY := Color("8fd3ff")           # allies, side quests, tribulation bolts
const HUD_LABEL := Color("d5bd85")     # the HUD's bar labels
const PAPER_INK := Color("2b2118")     # words on paper
const BAR_TROUGH := Color("17242c")    # bar troughs
## Plates over the world (the tracker, nameplates, banners): at 0.72 MIST still reads 4.5:1 over a white sky.
const PLATE := Color(0.02, 0.06, 0.075, 0.72)
## The world dimmed behind a page (at 0.72, or 0.55 behind a modal).
const DIM := Color(0.01, 0.03, 0.04)
## Drawn page surfaces (the map scroll, the Go board, the zither, talisman paper, the tribulation sky, the furnace):
## their own materials, named here so no page carries a colour literal.
## P5 (docs/page_identity.md §7): the materials of the pages that take their own identity, each a mix of two tokens
## (`a` + t `b`, written beside it) so no new hue enters; P5 added `cloth_wash` (the Character page's painted slips).
## The talisman's red ink and the zither's strings, which held the names `cinnabar` and `silk` before §7 gave them out,
## are `cinnabar_ink` and `qin_silk`.
const SURFACE := {
	"scroll": Color("e8dcbc"), "scroll_edge": Color("d9ccaa"), "sky_scroll": Color("e2ebee"), "sky_scroll_edge": Color("c9d6dc"),
	"route": Color(0.35, 0.25, 0.12, 0.55), "mountain": Color(0.35, 0.42, 0.40, 0.35), "isle": Color(0.42, 0.48, 0.60, 0.55),
	"isle_grass": Color(0.45, 0.62, 0.50, 0.8), "wind": Color(0.25, 0.45, 0.5, 0.6), "node_unseen": Color(0.45, 0.42, 0.36),
	"node_planned": Color(0.62, 0.68, 0.72, 0.8), "node_planned_rim": Color(0.3, 0.34, 0.38, 0.6),
	"talisman": Color("efe3c2"), "talisman_edge": Color("8a6a3a"), "brush_ink": Color("1c1a18"), "cinnabar_ink": Color(0.75, 0.2, 0.18),
	"board": Color("d8ad6c"), "board_edge": Color("c99a58"), "board_line": Color("4a3218"),
	"stone_black": Color("1c1b20"), "stone_white": Color("f1ece0"), "stone_white_rim": Color("6f6a5e"),
	"wood": Color("5a3620"), "wood_dark": Color("3b2416"), "bridge": Color("d8c08a"), "peg": Color("b8894a"), "peg_dark": Color("1b1410"),
	"hui": Color("12352d"), "qin_silk": Color("efe3c2"),
	"sky_top": Color(0.03, 0.04, 0.09), "sky_bottom": Color(0.086, 0.082, 0.118), "cloud": Color(0.18, 0.2, 0.3), "cloud_lit": Color(0.22, 0.24, 0.34),
	"ember": Color(0.95, 0.45, 0.18), "flame": Color(0.95, 0.75, 0.18), "furnace_mouth": Color(0.08, 0.05, 0.04),
	"ash": Color(0.5, 0.48, 0.44), "cinder": Color(0.12, 0.1, 0.1), "glow": Color(1.0, 0.85, 0.45), "soul_spark": Color(1.0, 0.95, 0.7),
	"map_line": Color(0.85, 0.92, 0.9),
	"gourd": Color("b4853d"),            # BRONZE + 0.35 GOLD
	"gourd_dark": Color("584227"),       # BRONZE + 0.45 INK
	"space": Color("0a1e23"),            # DEEP_TEAL + 0.55 INK
	"lacquer": Color("541720"),          # BLOOD + 0.55 INK
	"lacquer_black": Color("161918"),    # INK + 0.10 BRONZE
	"river_lacquer": Color("0c2a2f"),    # RIVER_NIGHT + 0.20 JADE_SHADOW
	"bamboo": Color("b9ba8b"),           # bridge + 0.18 JADE
	"hemp": Color("d1bda1"),             # PAPER + 0.30 BRONZE
	"almanac": Color("e7d5a8"),          # PAPER + 0.30 GOLD
	"cinnabar": Color("cc3c43"),         # RED + 0.50 BLOOD
	"rubbing": Color("171f22"),          # INK + 0.07 PAPER
	"stone": Color("4d595e"),            # HOLLOW + 0.45 INK
	"plaster": Color("dadbd0"),          # PAPER + 0.25 MIST
	"cloth": Color("0f3435"),            # JADE_SHADOW + 0.45 INK
	"cloth_wash": Color("1a605c"),       # JADE_SHADOW + 0.20 JADE: the figure's slips, washed lighter
	"silk": Color("3b6b66"),             # JADE_SHADOW + 0.18 PAPER
	"sand": Color("c5ab8a"),             # PAPER + 0.45 BRONZE
	"straw": Color("c8aa75"),            # bridge + 0.25 BRONZE
	"soil": Color("2b1e16"),             # wood_dark + 0.30 INK
	"water": Color("185660"),            # QI + 0.60 INK
	"clay": Color("ac663e"),             # BRONZE + 0.25 RED
	"sky": Color("0d2b2d"),              # JADE_SHADOW + 0.58 INK: the Bag's night at its lightest behind words
	"sea": Color("27484e"),              # DEEP_TEAL + 0.16 MIST: the sea of cloud under the Bag's sky, at its lightest
}
## Where each text colour is drawn (docs/ui_style_guide.md §1.4): [the token's name, the fills under it, the smallest
## size it is drawn at there]. "@page" stands for the five page fills (major_window, minor_panel, slot, toast, currency_pill); a
## fill "asset:state" is that state of the HD kit ("minor_panel:disabled" and "tab:disabled" are the derived dim, and
## "minimap_frame:header" the band that holds the room name); a fill ending "@ink" carries words drawn with an ink
## outline (draw_inked, draw_outlined), which are measured on INK. The ui_suite measures every pair on the kit's own
## art: 4.5:1, or 3:1 where the colour is only drawn at 20 px and up. Grade and quality colours are measured on "@page".
const TEXT_ON := [
	[&"PAPER", ["@page", "tab", "button_secondary", "button_secondary:pressed", "minor_panel:disabled"], 14],
	[&"MIST", ["@page"], 14],
	[&"PALE_GOLD", ["@page", "tab:selected", "minimap_frame:header", "realm_badge"], 14],
	[&"PALE_GOLD", ["button_primary@ink", "button_primary:pressed@ink", "title_plaque@ink"], 14],
	[&"GOLD", ["@page"], 14],
	[&"BRIGHT_JADE", ["@page"], 14],
	[&"QI", ["@page"], 14],
	[&"HOLLOW", ["@page", "tab:disabled", "minor_panel:disabled", "button_secondary:disabled"], 14],
	[&"HOLLOW", ["button_primary:disabled@ink"], 14],
	[&"RED_TEXT", ["@page"], 14],
	[&"SOUL_TEXT", ["@page"], 14],
	[&"WARNING", ["@page"], 14],
	[&"SKY", ["@page"], 14],
	[&"HUD_LABEL", ["minor_panel"], 14],
	[&"PAPER_INK", ["dialogue_box"], 20],
	# P5 (docs/page_identity.md §7): words on the pages' own surfaces ("surface:<key>", a flat SURFACE colour) and on
	# their tags and tablets. The ui_suite also measures every word a page with its own surface draws on what it sits on.
	[&"PAPER", ["surface:cloth", "surface:cloth_wash", "jade_tag", "honour_tablet", "honour_tablet:selected"], 14],
	[&"MIST", ["surface:cloth"], 14],
	[&"PALE_GOLD", ["surface:cloth", "surface:cloth_wash", "honour_tablet", "honour_tablet:selected"], 14],
	[&"PALE_GOLD", ["jade_tag:selected@ink", "jade_label@ink"], 14],
	[&"GOLD", ["surface:cloth", "honour_tablet", "honour_tablet:selected"], 14],
	[&"BRIGHT_JADE", ["surface:cloth"], 14],
	[&"HOLLOW", ["surface:cloth"], 20],
	# The Bag's sky (decision 24): its night and sea of cloud, the floating tokens and the item card.
	[&"PAPER", ["surface:sky", "surface:sea", "sky_token", "sky_card"], 14],
	[&"MIST", ["surface:sky", "surface:sea", "sky_token", "sky_card"], 14],
	[&"PALE_GOLD", ["surface:sky", "surface:sea", "sky_token:selected", "sky_card"], 14],
	[&"PALE_GOLD", ["sky_token:selected@ink"], 14],
	[&"GOLD", ["surface:sky", "sky_card"], 14],
	[&"BRIGHT_JADE", ["surface:sky", "sky_card"], 14],
	[&"HOLLOW", ["surface:sky", "sky_token"], 14],
	[&"RED_TEXT", ["sky_card"], 14],
	[&"SOUL_TEXT", ["sky_card"], 14],
	[&"WARNING", ["sky_card"], 14],
	# The Post family (Roll-Call, Works, Welcome Back, Pouches): the board and tray in dark timber, a tablet's back, the
	# pale name tablets, the hemp labels and slips, the paper tags.
	[&"PAPER", ["surface:wood_dark", "surface:wood"], 14],
	[&"MIST", ["surface:wood_dark", "surface:wood"], 14],
	[&"PALE_GOLD", ["surface:wood_dark", "surface:wood"], 14],
	[&"GOLD", ["surface:wood_dark"], 14],
	[&"BRIGHT_JADE", ["surface:wood_dark", "surface:wood"], 14],
	[&"RED_TEXT", ["surface:wood_dark"], 14],
	[&"HOLLOW", ["surface:wood_dark"], 14],
	[&"WARNING", ["surface:wood_dark"], 14],
	[&"PAPER_INK", ["surface:bridge", "surface:hemp", "surface:talisman"], 14],
	[&"JADE_SHADOW", ["surface:bridge", "surface:hemp"], 14],
	[&"BLOOD", ["surface:talisman"], 14],
	# The Records family (Dialogue, Quests, Mail, Notice Board): ink on the paper strip, the mission slips, the envelopes,
	# the open letter and the posters; the red heads and seals; the brick of the town wall.
	[&"PAPER_INK", ["surface:scroll", "paper_slip", "envelope", "envelope:selected", "letter_sheet", "poster"], 14],
	[&"BLOOD", ["surface:scroll", "paper_slip", "letter_sheet", "poster"], 14],
	[&"JADE_SHADOW", ["surface:scroll", "paper_slip", "letter_sheet"], 14],
	[&"PALE_GOLD", ["surface:lacquer"], 14],
	[&"PAPER", ["surface:stone", "surface:lacquer"], 14],
	[&"PALE_GOLD", ["surface:stone"], 14],
	# The Market family (Shop, Storage, Exchange, County Hall, Auction): black lacquer and the sign boards, the red lacquer
	# placards and ribbons, the stall's counter plank, the warrant sticks and the favour banner's paper.
	[&"PAPER", ["surface:lacquer_black", "market_plate", "surface:lacquer"], 14],
	[&"MIST", ["surface:lacquer_black", "market_plate", "surface:lacquer"], 14],
	[&"PALE_GOLD", ["surface:lacquer_black", "market_plate", "surface:lacquer"], 14],
	[&"GOLD", ["surface:lacquer_black", "market_plate", "surface:lacquer"], 14],
	[&"BRIGHT_JADE", ["surface:lacquer_black"], 14],
	[&"HOLLOW", ["surface:lacquer_black"], 14],
	[&"RED_TEXT", ["surface:lacquer_black"], 14],
	[&"PAPER_INK", ["surface:board", "surface:bamboo", "surface:scroll"], 14],
	[&"BLOOD", ["surface:scroll"], 14],
	# The Bonds family (Companions, Gift, Relations): ink on the whitewash, the gift tray's red lacquer.
	[&"PAPER_INK", ["surface:plaster"], 14],
	[&"JADE_SHADOW", ["surface:plaster"], 14],
	[&"BLOOD", ["surface:plaster"], 14],
	[&"PAPER", ["gift_tray"], 14],
	[&"MIST", ["gift_tray"], 14],
	[&"PALE_GOLD", ["gift_tray"], 14],
	[&"GOLD", ["gift_tray"], 14],
]

## Settings > Accessibility > Reduce motion (docs/moments_design.md §4.6): slides, wipes, rises, swings and flips become
## fades of MOTION_FADE_S; decoration that only moves goes. Pages read it through Page.unfold and their opening fade.
const MOTION_FADE_S := 0.2

static func reduce_motion() -> bool:
	return Game != null and Game.account != null and bool(Game.account.settings.get("reduce_motion", false))

static var _display: Font
static var _text: Font
static var _label: Font
static var _body: Font
static var _styles: Dictionary = {}
static var _numeric: Dictionary = {}
static var _num_re: RegEx
## Cormorant sits small on its body: headings draw at 1.2x the requested size.
const WORD_SCALE := 1.2
## Source Serif at 1.0x spans about the widths the layouts were drawn for (Cormorant at 1.2x),
## with a taller x-height and twice the stroke weight.
const TEXT_SCALE := 1.0
## Headings below this size are set in the bold serif: Cormorant's hairlines fade when small.
const DISPLAY_MIN := 22
## The type scale (docs/ui_style_guide.md §3): words at 14, 16, 18, 20 and 22; display (Cormorant) at 22, 26, 30 and 34.
const T_HINT := 14
const T_CAPTION := 16
const T_ROW := 18
const T_BODY := 20
const T_BUTTON := 22
const D_SUB := 22
const D_HEADING := 26
const D_DISPLAY := 30
const D_TITLE := 34
const WORD_SCALE_STEPS := [14, 16, 18, 20, 22]
const DISPLAY_STEPS := [22, 26, 30, 34]

## True when `size` is a step of the scale (a display size only when set in Cormorant, from 22 up).
static func on_scale(size: int, display := false) -> bool:
	return size in (DISPLAY_STEPS if display and size >= DISPLAY_MIN else WORD_SCALE_STEPS)

## The next step down the word scale (never under MIN_SIZE).
static func step_down(size: int) -> int:
	for i in range(WORD_SCALE_STEPS.size() - 1, -1, -1):
		if WORD_SCALE_STEPS[i] < size: return WORD_SCALE_STEPS[i]
	return MIN_SIZE

## Settings text_size 0/1/2.
const TEXT_SIZES := [0.92, 1.0, 1.12]
## No word or figure is set smaller than this (before the text size setting): below it a phone blurs it.
const MIN_SIZE := 14

static var _symbols: FontFile

## Check marks, stars and arrows the word fonts and Pixelify lack (a renamed DejaVu subset).
static func symbols_font() -> FontFile:
	if _symbols == null:
		_symbols = load("res://art/fonts/JadeRiverSymbols.ttf")
		_symbols.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	return _symbols

## A variable font pinned to `axes` ({"wght": 600, "opsz": 14}). Axis keys must be OpenType
## tags: a plain "wght" string key is silently ignored and leaves the font at its default.
static func _variable(path: String, axes: Dictionary, spacing := 0) -> Font:
	var base: FontFile = load(path)
	base.antialiasing = TextServer.FONT_ANTIALIASING_GRAY
	base.hinting = TextServer.HINTING_LIGHT
	base.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_AUTO
	base.fallbacks = [symbols_font()]
	var ts := TextServerManager.get_primary_interface()
	var fv := FontVariation.new()
	fv.base_font = base
	var tagged := {}
	for k in axes: tagged[ts.name_to_tag(k)] = axes[k]
	fv.variation_opentype = tagged
	# Lining figures: old-style 0 reads as the letter o ("Lv 0").
	fv.opentype_features = {ts.name_to_tag("lnum"): 1}
	if spacing != 0: fv.spacing_glyph = spacing
	return fv

## Headers, titles and plaques.
static func display_font() -> Font:
	if _display == null: _display = _variable("res://art/fonts/CormorantGaramond.ttf", {"wght": 700})
	return _display

## Labels, names, paragraphs and buttons.
static func text_font() -> Font:
	if _text == null: _text = _variable("res://art/fonts/SourceSerif4.ttf", {"wght": 600, "opsz": 14})
	return _text

## World labels, small headings and nameplates: bold, to hold against painted scenes.
static func label_font() -> Font:
	if _label == null: _label = _variable("res://art/fonts/SourceSerif4.ttf", {"wght": 700, "opsz": 14})
	return _label

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

## True for strings of digits and signs only ("84/84", "+12%", "3 / 28"), and numbers shortened by `short` ("18.2K").
static func is_numeric(s: String) -> bool:
	if _numeric.has(s): return _numeric[s]
	if _num_re == null: _num_re = RegEx.create_from_string("^[0-9\\s.,:/%+\\-−×()#]+[KMBT]?$")
	if _numeric.size() > 4000: _numeric.clear()
	_numeric[s] = _num_re.search(s) != null
	return _numeric[s]

static func _cormorant_at(size: int, display: bool) -> bool:
	return display and size >= DISPLAY_MIN

static func font_for(_s: String, display := false, size := 99) -> Font:
	if _cormorant_at(size, display): return display_font()
	return label_font() if display else text_font()

## The size a string is drawn at: the layout size, scaled to the font and the player's text size.
static func size_for(_s: String, size: int, display := false) -> int:
	return int(round(maxi(size, MIN_SIZE) * (WORD_SCALE if _cormorant_at(size, display) else TEXT_SCALE) * text_scale()))

## Settings > Text size as a multiplier.
static func text_scale() -> float:
	if Game == null or Game.account == null: return 1.0
	return TEXT_SIZES[clampi(int(Game.account.settings.get("text_size", 1)), 0, 2)]

## Line height for `size` in a page layout, following the text size setting.
static func line_height(size: int) -> float:
	return size * 1.3 * text_scale()

## Nine-slice StyleBoxTexture for a kit asset and state.
static func style(asset: String, state := "normal", content_margin := -1.0) -> StyleBox:
	var key := asset + ":" + state + ":" + str(content_margin)
	if _styles.has(key): return _styles[key]
	var derived := DERIVED_TINT.has(state) and not _has_state(asset, state)
	_styles[key] = _derived_style(asset, state, content_margin) if derived else _kit_style(asset, state, content_margin)
	return _styles[key]

## States neither kit draws for an asset (minor_panel is drawn only `normal`) are made from its normal art, so a
## selected or disabled row still reads as one (B3): selected wears the kit's selected glow, disabled is dimmed,
## pressed is darkened a little.
const DERIVED_TINT := {"selected": Color.WHITE, "disabled": Color(0.5, 0.56, 0.58, 0.8), "pressed": Color(0.82, 0.86, 0.86)}

static func _has_state(asset: String, state: String) -> bool:
	return (ContentDB.config("ui_assets_hd").get(asset, {}) as Dictionary).has(state) or (ContentDB.config("ui_assets").get(asset, {}) as Dictionary).has(state)

static func _derived_style(asset: String, state: String, content_margin: float) -> StyleBox:
	var base := _kit_style(asset, "normal", content_margin)   # a fresh box: the cached normal one stays untinted
	var tint: Color = DERIVED_TINT[state]
	if base is HdStyleBox: base.modulate = tint
	elif base is StyleBoxTexture: base.modulate_color = tint
	if state != "selected": return base
	var lb := LayeredBox.new()
	lb.layers = [[base, 0.0], [style("selected_slot_glow"), 3.0]]
	for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]: lb.set_content_margin(side, base.get_content_margin(side))
	return lb

## Style boxes drawn one over another, each on the rect grown by its own margin.
class LayeredBox extends StyleBox:
	var layers: Array = []   # [[StyleBox, grow px]]
	func _draw(to_canvas_item: RID, rect: Rect2) -> void:
		for l in layers: (l[0] as StyleBox).draw(to_canvas_item, rect.grow(float(l[1])))

static func _kit_style(asset: String, state: String, content_margin: float) -> StyleBox:
	var hd := _hd_style(asset, state, content_margin)
	if hd: return hd
	var e: Dictionary = ContentDB.config("ui_assets").get(asset, {})
	var path := str(e.get(state, e.get("normal", "")))
	var texture: Texture2D = SpriteCache.tex(path)
	if texture == null:
		var flat := StyleBoxFlat.new()
		flat.bg_color = RIVER_NIGHT
		flat.border_color = JADE
		flat.set_border_width_all(2)
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

static var _hd_textures: Dictionary = {}

## Fixed-size HD art (margins 0, such as `hud_ring_<size>`) as a linear-filtered texture, for callers that scale it or
## fade it (draw_texture_rect with a modulate). Null when the kit has no such asset.
static func hd_texture(asset: String, state := "normal") -> Texture2D:
	var key := asset + ":" + state
	if not _hd_textures.has(key):
		var sb := _hd_style(asset, state, -1.0)
		_hd_textures[key] = (sb as HdStyleBox).texture if sb is HdStyleBox else null
	return _hd_textures[key]

## The HUD ring sizes the HD kit draws (face diameters, tools/ui/build_ui_hd.py HUD_RING_SIZES) and the pad round each.
const HUD_RINGS := [132, 64, 52, 48]
const HUD_RING_PAD := 14.0

static func draw_text(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0, shadow := true, display := false) -> void:
	var f := font_for(text, display, size)
	var px := size_for(text, size, display)
	if shadow and color.get_luminance() > 0.4:
		# A soft two-step drop shadow reads on painted backgrounds without a hard black edge. Ink on paper takes none (P5:
		# a black shadow under dark words only smudges them).
		ci.draw_string(f, pos + Vector2(0, 2), text, align, width, px, Color(0, 0, 0, 0.55 * color.a))
		ci.draw_string(f, pos + Vector2(1, 1), text, align, width, px, Color(0, 0, 0, 0.45 * color.a))
	ci.draw_string(f, pos, text, align, width, px, color)

## World labels (names, damage numbers, prompts) over painted scenes: bold face, a thin ink
## outline and a soft shadow, so serifs stay sharp instead of drowning in a heavy stroke.
## Numbers are drawn in Pixelify Sans only from this size up (damage numbers, large counts). Smaller, its 5 reads as
## an S and its 2 as a Z (the P2 review, G2), so bar values and slot counts use the bold serif's lining figures.
const PIXEL_NUMERALS_MIN := 20

static func draw_outlined(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PAPER, align := HORIZONTAL_ALIGNMENT_CENTER, width := 200.0) -> void:
	var pixel := size >= PIXEL_NUMERALS_MIN and is_numeric(text)
	var f := body_font() if pixel else label_font()
	var px := int(round(maxi(size, MIN_SIZE) * text_scale())) if pixel else size_for(text, size)
	ci.draw_string_outline(f, pos + Vector2(0, 2), text, align, width, px, 5, Color(0, 0, 0, 0.3 * color.a))
	ci.draw_string_outline(f, pos, text, align, width, px, 3 if not pixel else 4, Color(INK, 0.92 * color.a))
	ci.draw_string(f, pos, text, align, width, px, color)

## Words on a bright face: primary button labels and titles on the plaque (decision 10, option C of
## docs/mockups/00b_button_faces.png). The face stays the bright jade the mockups approved; a 2 px ink outline under the
## letters carries the contrast, so the words read against ink (PALE_GOLD 15.6:1, a disabled HOLLOW 6.2:1) however
## light the enamel behind them.
const INK_OUTLINE := 2

static func draw_inked(ci: CanvasItem, text: String, pos: Vector2, size: int, color := PALE_GOLD, align := HORIZONTAL_ALIGNMENT_CENTER, width := -1.0, display := false) -> void:
	var f := font_for(text, display, size)
	var px := size_for(text, size, display)
	ci.draw_string_outline(f, pos + Vector2(0, 2), text, align, width, px, INK_OUTLINE + 2, Color(INK, 0.35 * color.a))
	ci.draw_string_outline(f, pos, text, align, width, px, INK_OUTLINE, Color(INK, color.a))
	ci.draw_string(f, pos, text, align, width, px, color)

static var _plate: StyleBoxFlat

## A world nameplate: name (and an optional second line) on a soft translucent ink plate,
## centred on x = 0 with the name's baseline at `y`. Returns the plate's rect.
static func draw_nameplate(ci: CanvasItem, name_text: String, sub: String, y: float, color := PAPER, sub_color := MIST, size := 16) -> Rect2:
	if _plate == null:
		_plate = StyleBoxFlat.new()
		_plate.bg_color = PLATE
		_plate.set_corner_radius_all(7)
		_plate.border_color = Color(GOLD, 0.22)
		_plate.set_border_width_all(1)
		_plate.anti_aliasing = true
	var sub_size := step_down(size)
	var w := text_width(name_text, size, true)
	if sub != "": w = maxf(w, text_width(sub, sub_size))
	var name_px := float(size_for(name_text, size, true))
	var sub_px := float(size_for(sub, sub_size)) if sub != "" else 0.0
	var h := name_px + (sub_px + 2 if sub != "" else 0.0)
	var rect := Rect2(-w * 0.5 - 10, y - name_px * 0.95, w + 20, h + 8)
	_plate.bg_color.a = PLATE.a * color.a
	ci.draw_style_box(_plate, rect)
	draw_text(ci, name_text, Vector2(-w * 0.5 - 20, y), size, color, HORIZONTAL_ALIGNMENT_CENTER, w + 40, true, true)
	if sub != "":
		draw_text(ci, sub, Vector2(-w * 0.5 - 20, y + sub_px + 2), sub_size, sub_color, HORIZONTAL_ALIGNMENT_CENTER, w + 40, true)
	return rect

static var _widths: Dictionary = {}   # measured widths, so labels drawn every frame are measured once

static func text_width(text: String, size: int, display := false) -> float:
	var key := "%d|%s|%.2f|%s" % [size, "d" if display else "b", text_scale(), text]
	if _widths.has(key): return float(_widths[key])
	if _widths.size() > 4000: _widths.clear()
	var w: float = font_for(text, display, size).get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size_for(text, size, display)).x
	_widths[key] = w
	return w

static var _fitted: Dictionary = {}   # fitted lines drawn every frame are shortened once

## `s` shortened with an ellipsis so it fits `width` at `size`, measured at the size it is drawn (never under MIN_SIZE).
static func fit(s: String, size: int, width: float, display := false) -> String:
	if text_width(s, size, display) <= width: return s
	var key := "%d|%s|%d|%.2f|%s" % [size, display, int(width), text_scale(), s]
	if _fitted.has(key): return _fitted[key]
	var n := s.length()
	while n > 1 and text_width(s.left(n) + "…", size, display) > width: n -= 1
	if _fitted.size() > 2000: _fitted.clear()
	_fitted[key] = s.left(n).strip_edges() + "…"
	return _fitted[key]

static func quality_color(q: String) -> Color:
	return Color(str(ContentDB.config("grades").get("quality_colors", {}).get(q, "#e8e1cf")))

static func grade_color(g: String) -> Color:
	return Color(str(ContentDB.config("grades").get("grade_colors", {}).get(g, "#e8e1cf")))

static func badge_color(kind: String) -> Color:
	return {"grey": HOLLOW, "green": BRIGHT_JADE, "white": PAPER, "orange": WARNING, "red": RED_TEXT}.get(kind, PAPER)

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

## A Codex page seal's gift in one line (decision 27): its stats, then a Bestiary Leaf and, when `named`, whose.
static func seal_gift(rule: Dictionary, named := true) -> String:
	var parts: Array = (rule.get("modifiers", []) as Array).map(func(m): return affix_text(m))
	for e in rule.get("effects", []):
		if str(e.get("kind", "")) == "add_leaf": parts.append(Tx.t("ui.codex.gift_leaf") % ContentDB.name_of("enemies", str(e.enemy)) if named else Tx.t("ui.codex.gift_leaf_plain"))
	return " · ".join(parts)

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

## A time left in words: "2 d 5 h", "1 h 6 m", "12 m", "45 s" (Tx.span, the one style for every wait, cooldown and
## duration; I14). The ticking countdowns the player races keep `clock`.
static func span(seconds: float, days := true) -> String:
	return Tx.span(seconds, days)

## What a consumable did, in words (item_used's `effects` and `gains`, from InventoryAuthority.apply_use): one part per
## effect, each {text, color, pool}. The HUD joins them into its log line, the world floats the first ones over the
## player, and the status row carries what runs on. A heal at full HP says so rather than nothing.
static func use_parts(effects: Array, gains: Dictionary) -> Array:
	var out: Array = []
	for e in effects:
		var kind := str(e.get("kind", ""))
		match kind:
			"heal":
				var gives := float(e.get("gives", 0.0))
				if gives < 1.0: out.append({"text": Tx.t("hud.use.full") % Tx.t("hud.use.pool.hp"), "color": MIST, "pool": "hp"})
				elif float(e.get("over_s", 0.0)) > 0.0:
					out.append({"text": Tx.t("hud.use.gain_over") % [fmt(gives), Tx.t("hud.use.pool.hp"), span(float(e.over_s))], "color": BRIGHT_JADE, "pool": "hp", "float": Tx.t("hud.use.gain") % [fmt(gives), Tx.t("hud.use.pool.hp")]})
				else: out.append({"text": Tx.t("hud.use.gain") % [fmt(gives), Tx.t("hud.use.pool.hp")], "color": BRIGHT_JADE, "pool": "hp", "float": Tx.t("hud.use.gain") % [fmt(gives), Tx.t("hud.use.pool.hp")]})
			"restore":
				var pool := str(e.get("pool", "qi"))
				var d := float(gains.get(pool, 0.0))
				var col: Color = {"qi": QI, "soul": SOUL_TEXT, "hollowing": PAPER}.get(pool, BRIGHT_JADE)
				if absf(d) < 0.5: out.append({"text": Tx.t("hud.use.full" if pool != "hollowing" else "hud.use.clear") % Tx.t("hud.use.pool." + pool), "color": MIST, "pool": pool})
				elif d < 0.0: out.append({"text": Tx.t("hud.use.drop") % [fmt(-d), Tx.t("hud.use.pool." + pool)], "color": col, "pool": pool, "float": Tx.t("hud.use.drop") % [fmt(-d), Tx.t("hud.use.pool." + pool)]})
				else: out.append({"text": Tx.t("hud.use.gain") % [fmt(d), Tx.t("hud.use.pool." + pool)], "color": col, "pool": pool, "float": Tx.t("hud.use.gain") % [fmt(d), Tx.t("hud.use.pool." + pool)]})
			"buff":
				var v := float(e.get("value", 0.0))
				# A share (pct ops, and flat rates under 1: regen, insight, cultivation) reads as a percent.
				var num := ("%+d%%" % int(round(v * 100.0))) if str(e.get("op", "flat")) != "flat" or absf(v) < 1.0 else "%+.0f" % v
				out.append({"text": Tx.t("hud.use.timed") % [Tx.t("hud.use.stat." + str(e.stat)) + " " + num, span(float(e.get("duration", 60)))], "color": PALE_GOLD,
					"float": Tx.t("hud.use.stat." + str(e.stat)) + " " + num})
			"status":
				out.append({"text": Tx.t("hud.use.timed") % [Tx.t("hud.use.status." + str(e.status)), span(float(e.get("duration", 1)))], "color": PALE_GOLD,
					"float": Tx.t("hud.use.status." + str(e.status))})
			"cure_status": out.append({"text": Tx.t("hud.use.cured") % Tx.t("hud.use.status." + str(e.status)), "color": BRIGHT_JADE})
			"cure_injury": out.append({"text": Tx.t("hud.use.eased") % Tx.t("hud.use.injury." + str(e.injury)), "color": BRIGHT_JADE})
			"progress", "body_xp", "soul":
				out.append({"text": Tx.t("hud.use." + kind) % fmt(float(e.get("amount", 0))), "color": QI if kind == "progress" else (BODY if kind == "body_xp" else SOUL_TEXT),
					"float": "+" + fmt(float(e.get("amount", 0)))})
			"heart_demon", "toxicity":
				var a := float(e.get("amount", 0))
				out.append({"text": Tx.t("hud.use." + kind) % (("-" if a < 0.0 else "+") + fmt(absf(a))), "color": BRIGHT_JADE if a < 0.0 else RED_TEXT})
			"longevity": out.append({"text": Tx.plural("hud.use.longevity", int(e.get("amount", 0))) % int(e.get("amount", 0)), "color": PALE_GOLD})
			"reset_meridians", "settle_consolidation", "grain_blessing": out.append({"text": Tx.t("hud.use." + kind), "color": PALE_GOLD})
	# What moved a bar leads (the heal before the cure it came with), then the rest in the item's order.
	return out.filter(func(x): return x.has("pool")) + out.filter(func(x): return not x.has("pool"))

## A pool's value and its most as shown, rounded and grouped alike (I11: the HUD cut and did not group, "31750/31750",
## where the Stats tab said 31,751). A value is never shown above its most, and a sliver of life never as 0.
## P12: a bar of 100,000 or more shows `short` ("427K/427K").
static func pool_values(cur: float, most: float) -> Array:
	var f := short if most >= 100000.0 else fmt
	return [f.call(minf(ceilf(cur), roundf(most))), f.call(most)]

## Numbers over the world shortened to three figures from 10,000 (docs/ui_style_guide.md §4 rule 3, mockup 01):
## "18.2K", "123K", "1.25M"; under 10,000 grouped as `fmt` writes them. P12: the units are string keys (ui.num.*), so a
## translation can count in its own (万, 亿).
const SHORT_UNITS := [[1e12, "t"], [1e9, "b"], [1e6, "m"], [1e3, "k"]]

static func short(n: float) -> String:
	var a := absf(roundf(n))
	if a < 10000.0: return fmt(n)
	for u in SHORT_UNITS:
		# Three figures are rounded first, so 999,960 reads 1.00M rather than 1000K.
		if a >= float(u[0]) * 0.9995:
			var v := a / float(u[0])
			var d := 0 if v >= 99.95 else (1 if v >= 9.995 else 2)
			return ("-" if n < 0.0 else "") + ("%." + str(d) + "f") % v + Tx.t("ui.num." + str(u[1]))
	return fmt(n)

## A grouped number ("118,803"); from ten million on, `short` ("12.5M"), as pages show them (research §6.5).
static func fmt(n: float) -> String:
	if absf(n) >= 10000000.0: return short(n)
	var v := int(round(n))
	var s := str(absi(v))
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return ("-" if v < 0 else "") + s + out

## Pale-gold key-pattern corner jewels used on HUD panels drawn procedurally.
## One frame of a creature sheet fitted into `rect` (feet on its bottom edge), animated by `t`. False while loading.
static func draw_creature(ci: CanvasItem, rect: Rect2, creature_id: String, action := "idle", t := 0.0, modulate := Color.WHITE) -> bool:
	var e := SpriteCache.creature(creature_id)
	var texture: Texture2D = SpriteCache.tex_sliced(str(e.get("file", ""))) if not e.is_empty() else null
	if texture == null: return SpriteCache.loading(str(e.get("file", "")))   # still loading: keep the slot empty
	var acts: Dictionary = e.get("actions", {})
	var a: Dictionary = acts.get(action, acts.get("idle", {}))
	var frames := maxi(1, int(a.get("frames", 1)))
	var idx := int(t * float(a.get("fps", 6))) % frames
	var cell := float(e.cell)
	var row := int(a.get("row", 0))
	# Fit the drawn pixels of the first frame (not the mostly empty cell), in half steps.
	var baked: Array = e.get("bounds", {}).get(str(row), [])
	var used := Rect2(baked[0], baked[1], baked[2], baked[3]) if baked.size() == 4 else _creature_bounds(creature_id, texture, Rect2i(0, row * int(cell), int(cell), int(cell)))
	var s := minf(rect.size.x / maxf(1.0, used.size.x), rect.size.y / maxf(1.0, used.size.y))
	s = floorf(s * 2.0) / 2.0 if s >= 1.0 else s
	var origin := Vector2(rect.get_center().x - (used.position.x + used.size.x * 0.5) * s, rect.end.y - used.end.y * s)
	var src := Rect2(idx * cell, row * cell, cell, cell)
	ci.draw_texture_rect_region(texture, Rect2(origin, Vector2(cell, cell) * s), src, modulate)
	return true

static var _bounds: Dictionary = {}

## Fallback for sheets without baked bounds (tools/art/pixel.py writes them): reads the sheet back once.
static func _creature_bounds(key: String, texture: Texture2D, cell: Rect2i) -> Rect2:
	var k := "%s:%d" % [key, cell.position.y]
	if not _bounds.has(k):
		var img := texture.get_image()
		var r := img.get_region(cell).get_used_rect() if img else Rect2i()
		_bounds[k] = Rect2(r) if r.size.x > 0 else Rect2(Vector2.ZERO, Vector2(cell.size))
	return _bounds[k]

## A row of hearts (S49 affinity): `filled` of `total`, each `r` px across half its width; left edge at pos.x,
## vertical centre at pos.y.
static func draw_hearts(ci: CanvasItem, pos: Vector2, filled: int, total: int, r := 10.0) -> void:
	for i in total:
		var c := pos + Vector2(r + i * r * 2.5, 0)
		_heart(ci, c, r + 1.5, Color(INK, 0.85))
		_heart(ci, c, r, HEART if i < filled else Color(HEART.darkened(0.6), 0.9))
		if i < filled: ci.draw_circle(c + Vector2(-r * 0.45, -r * 0.4), r * 0.18, Color(1, 1, 1, 0.55))

static func _heart(ci: CanvasItem, c: Vector2, r: float, col: Color) -> void:
	ci.draw_circle(c + Vector2(-r * 0.48, -r * 0.22), r * 0.56, col)
	ci.draw_circle(c + Vector2(r * 0.48, -r * 0.22), r * 0.56, col)
	ci.draw_colored_polygon(PackedVector2Array([c + Vector2(-r * 1.02, -r * 0.08), c + Vector2(r * 1.02, -r * 0.08), c + Vector2(0, r * 0.98)]), col)
