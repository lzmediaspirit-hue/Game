class_name Page
extends Control
## Base for every full page and modal (Part 9.3/9.4): a major window frame with a
## title band, optional tabs, a close button and a content area. Pages draw
## immediately in `draw_page()` with helpers that also register tap regions, so a
## page is data → drawing → `on_action(id, data)` → Game.submit(intent).
## Pages never change game state themselves; they submit intents and redraw on events.

signal closed(page: Page)
signal navigate(page: String, args: Dictionary)

## The smallest tap target on a side, in screen px (P4, `docs/ui_style_guide.md`).
const MIN_TAP := 48.0
## The item slot (P4b): a 64 px icon at 1:1 (an HD icon, or a legacy icon's 32 art px at 2x) inside a 6 px inset.
const SLOT := 76.0
## The small slot, for an item named in a list row: a 32 px icon (an HD icon's native 32, a legacy one at 1x).
const SLOT_SMALL := 44.0
## The spacing grid (P4, docs/ui_style_guide.md §2): positions and sizes in steps of 8, the half step 4 inside a dense
## component. Every window stays inside SAFE_AREA and is one of the standard six, but for the one painting that fills the
## screen (WINDOW_SCREEN, the world map of decision 25), whose frame is the screen's edge.
## Test hooks, GRID, SAFE_AREA and WINDOWS: rules_tests holds every page to them.
const GRID := 8.0
const SAFE_AREA := Rect2(48, 24, 1184, 672)
const WINDOW_FULL := Rect2(64, 32, 1152, 656)
const WINDOW_LARGE := Rect2(128, 56, 1024, 608)
const WINDOW_MEDIUM := Rect2(256, 72, 768, 576)
const WINDOW_SMALL := Rect2(288, 152, 704, 416)
const WINDOW_CONFIRM := Rect2(384, 248, 512, 224)
const WINDOW_DIALOGUE := Rect2(48, 464, 1184, 232)
const WINDOW_SCREEN := Rect2(0, 0, 1280, 720)
const WINDOWS := [WINDOW_FULL, WINDOW_LARGE, WINDOW_MEDIUM, WINDOW_SMALL, WINDOW_CONFIRM, WINDOW_DIALOGUE, WINDOW_SCREEN]
## Content insets (the HD window's nine-slice margin at the sides), the title band and the tab row.
const INSET := 32.0
const TOP := 80.0
const TOP_BARE := 24.0
const BOTTOM := 24.0
const TAB_H := 48.0
const TAB_GAP := 8.0
const TAB_MIN_W := 120.0
## Lists: the gap under each row and the scroll gutter at the right.
const ROW_GAP := 4.0
const GUTTER := 8.0
## Gaps: between related controls, and the padding inside a card.
const GAP := 8.0
const PAD := 16.0
## Button heights: compact and in rows, standard, a page's main action.
const BTN_H := 48.0
const BTN_H_STANDARD := 56.0
const BTN_H_MAIN := 64.0

## P5 page identity (docs/page_identity.md §8). A page that is a thing from the world declares it in `_init`; Page then
## draws the page's own surface (draw_surface) in place of the shared window, its title on the page's own mount
## (draw_title_mount at title_rect) and its tabs in the page's own form (tab_rects, draw_tab), lays its content out in
## content_rect, and plays its opening (unfold). Whatever the identity, Page keeps the shared parts: the dimmed world,
## the close button at the window's top right, Esc and a tap outside, primary buttons with inked labels and the inked
## title lettering, the text tokens, the type scale, the 48 px targets, the confirm dialog and the toast. A page with
## no identity keeps the shared major_window, plaque and tabs as they were.
class Identity:
	var surface: String      ## the SURFACE key of the page's material: the ground under its words where it names none
	var framed: bool         ## true: the shared major_window stays round the surface; false: the surface is the window
	var title_mount: String  ## "plaque", the shared title plaque; "own", the page's mount (draw_title_mount)
	var signature: String    ## the layout signature of docs/page_identity.md §3 as an id; no two pages share one
	var open_s: float        ## the opening motion's length, at most OPEN_MOTION_MAX
	func _init(surface_key: String, framed_: bool, mount: String, signature_: String, open_s_ := 0.25) -> void:
		surface = surface_key
		framed = framed_
		title_mount = mount
		signature = signature_
		open_s = open_s_

## page_identity §6: an opening lasts 0.35 s at most, and a tap during it finishes it.
const OPEN_MOTION_MAX := 0.35

var page_id := ""
var title := ""
var tabs: Array = []            # [{id, label, locked?: text}]
var tab := 0
var args: Dictionary = {}
var modal := false              # small centred dialog instead of the full window
var frameless := false          # shell screens draw their own layout over the backdrop
var identity: Identity = null   # P5: the page's own identity, or null for the shared window
var grade_rims := false         # P5: slots ring every item in its grade's colour and mark a quality with a gem
var frame_rect := WINDOW_FULL
var content := Rect2()
var t := 0.0
var opened := 0.0               # seconds since the page opened (a tap sets it past the opening)
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
var _open_frame := -1           # the process frame it first drew in (first_draw)
var _stepped := false           # it has had a process step (see _draw)
## Decision 43 (docs/redesign/tutorials.md): the named places a tour points at, so a tour never leans on a node path.
## Every tap region is one by its action ("meridian", and "meridian:body" for the one with that data), every tab is
## "tab:<id>", and "close", "help", "title", "content" and "window" name the shared parts (tour_rect); a page names
## anything else it wants shown with tour_mark(). The marks are made again with each drawing.
var tour_marks: Dictionary = {}
## Decision 42 (the Techniques page's lag): a page that draws the same until something changes sets this, and is drawn
## again only on a change: an input, a game event, its toast, and the frames its opening loads art in (PAINT_FRAMES).
## Every other page is drawn every frame.
var redraw_on_change := false
const PAINT_FRAMES := 3
## Art the last drawing left out while it loads (an icon, an HD face, a creature sheet): such a page is drawn again the
## next frame, until it is in.
var _waiting := false
var draw_count := 0             ## how many times it has been drawn (perf_tests: a page that redraws only on a change)
## A page whose own surface covers the whole screen may leave out the dim over the play screen (the Techniques page,
## whose chart is drawn behind the page, under it).
var dims_world := true

func _ready() -> void:
	_born = Engine.get_process_frames()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	GameEvents.event.connect(_on_game_event)
	if modal and frame_rect == WINDOW_FULL: frame_rect = WINDOW_SMALL
	if identity != null: modulate.a = open_alpha()   # it fades in from its first frame, drawn before its first step or after
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
	content = content_rect()

## Where the page draws: its window, and anything it pins beyond it (the Dialogue's offered quest above its strip).
## The ui_suite holds every word and button inside it.
func window_rect() -> Rect2:
	return frame_rect

## The content area: inside the shared window, under the title and the tabs. A page with its own surface gives its own.
func content_rect() -> Rect2:
	var top := TOP if title != "" else TOP_BARE
	if not tabs.is_empty(): top += TAB_H + TAB_GAP
	return Rect2(frame_rect.position.x + INSET, frame_rect.position.y + top, frame_rect.size.x - INSET * 2.0, frame_rect.size.y - top - BOTTOM)

func _process(delta: float) -> void:
	_stepped = true
	t += delta
	opened += delta
	if identity != null: modulate.a = open_alpha()
	var toasting := toast_t > 0.0
	if toasting:
		toast_t -= delta
	if not redraw_on_change or toasting or _waiting or _open_frame < 0 or Engine.get_process_frames() - _open_frame < PAINT_FRAMES: queue_redraw()

## How far the page's opening has run, 0 to 1 over `dur` s (the identity's open_s by default), eased out: a page moves
## its parts by (1 - unfold()). Under Reduce motion nothing moves, so it is 1 from the first frame and the page only
## fades in (docs/moments_design.md §4.6); a tap sets it to 1 (page_identity §6).
func unfold(dur := -1.0) -> float:
	if identity == null or UiKit.reduce_motion(): return 1.0
	var k := clampf(opened / maxf(0.01, dur if dur > 0.0 else identity.open_s), 0.0, 1.0)
	return 1.0 - pow(1.0 - k, 3.0)

## The page's alpha while it opens: over its opening, or over MOTION_FADE_S under Reduce motion.
func open_alpha() -> float:
	return clampf(opened / maxf(0.01, UiKit.MOTION_FADE_S if UiKit.reduce_motion() else identity.open_s), 0.0, 1.0)

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
	# A page that fades in is not shown before its first step (its alpha is 0): the drawing its opening asks for is left
	# to the one that step asks for, in the same frame, so it is not drawn twice as it opens.
	if identity != null and not _stepped: return
	if _open_frame < 0: _open_frame = Engine.get_process_frames()
	draw_count += 1
	_waiting = false
	_regions.clear()
	_areas.clear()
	tour_marks.clear()
	HdStyleBox.base = Transform2D.IDENTITY
	if text_log != null: text_log.clear()
	_layout()
	if frameless:
		draw_page()
		if not confirm.is_empty(): _draw_confirm()
		_draw_toast()
		return
	# Dim the play screen behind the page.
	if dims_world: draw_rect(Rect2(Vector2.ZERO, size), Color(UiKit.DIM, 0.55 if modal else 0.72))
	if identity == null or identity.framed: draw_style_box(UiKit.style("major_window"), frame_rect)
	if identity != null: draw_surface(frame_rect)
	if title != "":
		var mount := title_rect()
		if identity == null or identity.title_mount == "plaque":
			draw_style_box(UiKit.style("title_plaque"), mount)
			inked(mount.position + Vector2(0, 42), title, 34, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, mount.size.x)
		else:
			# The page's own mount under the shared lettering: the title inked, stepping down the display scale to fit.
			draw_title_mount(mount)
			var ts := UiKit.D_TITLE
			while ts > UiKit.D_SUB and UiKit.text_width(title, ts, true) > mount.size.x - 24: ts -= 4
			inked(mount.position + Vector2(0, mount.size.y * 0.5 + ts * 0.42), title, ts, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, mount.size.x)
	var close_rect := Rect2(frame_rect.end.x - 72, frame_rect.position.y + 16, 52, 52)
	_register(close_rect, "_close", null, true, "", "button")
	draw_style_box(UiKit.style("close_button", "pressed" if _is_pressed("_close") else "normal"), close_rect)
	_draw_x(close_rect.get_center(), 11, UiKit.PAPER)
	if not tabs.is_empty(): _draw_tabs()
	draw_page()
	_draw_help()
	if not confirm.is_empty(): _draw_confirm()
	_draw_toast()

## Decision 43: the "?" beside the close button, while the page (on its tab) has a tour: a tap plays it again.
func _draw_help() -> void:
	if TutorialRules.tour_for(page_id, tab_id()) == "" or c() == null: return
	var r := help_rect()
	_register(r, "_help", null, true, "", "button")
	# A round jade button rimmed in gold, like the close button's face, with its "?" inked.
	var cc := r.get_center()
	var pressed := _is_pressed("_help")
	draw_circle(cc, 25.0, UiKit.INK, true, -1.0, true)
	draw_circle(cc, 23.0, UiKit.GOLD.lerp(UiKit.BRONZE, 0.35), true, -1.0, true)
	draw_circle(cc, 20.0, UiKit.JADE_SHADOW.lerp(UiKit.INK, 0.45 if pressed else 0.2), true, -1.0, true)
	draw_circle(cc + Vector2(-5, -6), 9.0, Color(UiKit.JADE, 0.2), true, -1.0, true)
	UiKit.draw_inked(self, "?", Vector2(r.position.x, cc.y + 10 + (2 if pressed else 0)), 26, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## Where the "?" sits: left of the close button. A page whose own parts stand there gives another place.
func help_rect() -> Rect2:
	return Rect2(frame_rect.end.x - 132, frame_rect.position.y + 16, 52, 52)

## Whether a tour may dim the page now: a page that is a game in play (fishing, the guqin) waits until it rests.
func tour_ready() -> bool:
	return true

## Decision 45: the page has come in (drawn, its opening motion over, at most OPEN_MOTION_MAX), so its tour anchors
## stand where they will stay. The tutorial coach waits for it: a card shown on the first frame stood alone in the
## middle, then jumped beside its anchor as the page drew and slid in, and a tap on where it had been did nothing.
func settled() -> bool:
	return draw_count > 0 and (identity == null or UiKit.reduce_motion() or opened >= minf(identity.open_s, OPEN_MOTION_MAX))

## The id of the tab shown ("" for a page with none).
func tab_id() -> String:
	return str(tabs[tab].get("id", "")) if tab >= 0 and tab < tabs.size() else ""

## Decision 43: name a place on the page for a tour (added to any of that name already made this drawing).
func tour_mark(name: String, rect: Rect2) -> void:
	tour_marks[name] = (tour_marks[name] as Rect2).merge(rect) if tour_marks.has(name) else rect

## A tour's anchor on this page, as it was last drawn: a mark the page named, a shared part, a tab, or the tap regions of
## an action ("id" all of them together, "id:data" one). Rect2() when the page shows no such thing now.
func tour_rect(name: String) -> Rect2:
	if tour_marks.has(name): return tour_marks[name]
	match name:
		"close": return Rect2() if frameless else Rect2(frame_rect.end.x - 72, frame_rect.position.y + 16, 52, 52)
		"help": return help_rect() if _regions.any(func(r): return r.id == "_help") else Rect2()
		"title": return title_rect() if title != "" and not frameless else Rect2()
		"content": return content
		"window": return window_rect()
	if name == "tabs":
		var all := Rect2()
		var trs := tab_rects()
		for i in mini(tabs.size(), trs.size()):
			if tab_shown(i): all = (trs[i] as Rect2) if all.size == Vector2.ZERO else all.merge(trs[i])
		return all
	if name.begins_with("tab:"):
		var rects := tab_rects()
		for i in tabs.size():
			if str(tabs[i].get("id", "")) == name.trim_prefix("tab:") and tab_shown(i) and i < rects.size(): return rects[i]
		return Rect2()
	var id := name.get_slice(":", 0)
	var one := name.contains(":")
	var want := name.substr(id.length() + 1)
	var out := Rect2()
	for r in _regions:
		if str(r.id) != id or r.kind == "scroll": continue
		if one and not (r.data is String or r.data is StringName or r.data is int) or (one and str(r.data) != want): continue
		out = (r.rect as Rect2) if out.size == Vector2.ZERO else out.merge(r.rect)
	return out

func _draw_toast() -> void:
	if toast_t > 0.0 and toast != "":
		var w := minf(760.0, UiKit.text_width(toast, 20) + 60)
		var r := Rect2(640 - w * 0.5, minf(frame_rect.end.y, 696) - 72, w, 48)
		draw_style_box(UiKit.style("toast"), r)
		UiKit.draw_text(self, toast, r.position + Vector2(0, 30), 20, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, w)

func _draw_x(center: Vector2, r: float, col: Color) -> void:
	draw_line(center - Vector2(r, r), center + Vector2(r, r), UiKit.INK, 6)
	draw_line(center - Vector2(r, -r), center + Vector2(r, -r), UiKit.INK, 6)
	draw_line(center - Vector2(r, r), center + Vector2(r, r), col, 3)
	draw_line(center - Vector2(r, -r), center + Vector2(r, -r), col, 3)

func _draw_tabs() -> void:
	var rects := tab_rects()
	for i in tabs.size():
		if not tab_shown(i): continue
		var tb: Dictionary = tabs[i]
		var r: Rect2 = rects[i]
		var locked := str(tb.get("locked", "")) != ""
		var state := "selected" if i == tab else ("disabled" if locked else "normal")
		if identity == null:
			draw_style_box(UiKit.style("tab", state), r)
			UiKit.draw_text(self, str(tb.label), r.position + Vector2(0, 31), 20, UiKit.PALE_GOLD if i == tab else (UiKit.HOLLOW if locked else UiKit.PAPER),
				HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
		else:
			draw_tab(r, i, state)
		if locked: lock_icon(r.position + Vector2(r.size.x - 16, 8))
		_register(r, "_tab", i, not locked, str(tb.get("locked", "")), "button")

# ------------------------------------------------------------------ P5: what a page with its own identity overrides
## Where the tabs sit: a row under the title, each as wide as its label (TAB_MIN_W at least) and TAB_H tall.
func tab_rects() -> Array:
	var out: Array = []
	var x := frame_rect.position.x + INSET
	for tb in tabs:
		var w := maxf(TAB_MIN_W, UiKit.text_width(str(tb.label), 20) + 40)
		out.append(Rect2(x, frame_rect.position.y + (TOP if title != "" else TOP_BARE), w, TAB_H))
		x += w + TAB_GAP
	return out

## Whether tab `i` hangs now (a page may keep one off the row while it has nowhere to lead).
func tab_shown(_i: int) -> bool:
	return true

## A tab in the page's own form (state: normal, selected or disabled). Page keeps its target, lock and reason.
func draw_tab(r: Rect2, i: int, state: String) -> void:
	draw_style_box(UiKit.style("tab", state), r)
	text(r.position + Vector2(0, 31), str(tabs[i].label), 20, UiKit.PALE_GOLD if state == "selected" else (UiKit.HOLLOW if state == "disabled" else UiKit.PAPER),
		HORIZONTAL_ALIGNMENT_CENTER, r.size.x)

## The page's own material inside the window rect `r`: by default a flat fill of the identity's SURFACE colour.
func draw_surface(r: Rect2) -> void:
	draw_rect(r, UiKit.SURFACE[identity.surface])
	ground(r, UiKit.SURFACE[identity.surface])

## Where the title's mount sits: the shared plaque centred at the window's top.
func title_rect() -> Rect2:
	return Rect2(frame_rect.position.x + frame_rect.size.x * 0.5 - 220, frame_rect.position.y + 10, 440, 60)

## The page's own mount for the title (the lettering is Page's, inked).
func draw_title_mount(r: Rect2) -> void:
	face(r, "title_plaque")

## The colour under the words drawn inside `rect` from here on: the lightest tone of the surface there. A page with its
## own surface names each ground as it draws it, and the ui_suite measures every word on the ground it sits on.
func ground(rect: Rect2, col: Color) -> void:
	if text_log != null: text_log.append({"rect": rect, "s": "", "button": Rect2(), "ground": col})

## A face from the HD kit that words sit on (a tag, a plaque): drawn, and named as their ground (`asset:state`).
func face(rect: Rect2, asset: String, state := "normal") -> void:
	draw_style_box(UiKit.style(asset, state), rect)
	if text_log != null: text_log.append({"rect": rect, "s": "", "button": Rect2(), "ground": "%s:%s" % [asset, state]})

static var _rounds: Dictionary = {}
static var _glows: Dictionary = {}

## A filled rounded rectangle with anti-aliased corners (a surface's rim, a slip), cached per radius and colour.
func rounded(rect: Rect2, radius: float, col: Color) -> void:
	rounded_on(self, rect, radius, col)

## rounded() on any canvas item (a page's layer that draws apart from the page: the Techniques chart's tiles).
static func rounded_on(ci: CanvasItem, rect: Rect2, radius: float, col: Color) -> void:
	var key := "%d|%s" % [int(radius), col.to_html()]
	if not _rounds.has(key):
		var sb := StyleBoxFlat.new()
		sb.bg_color = col
		sb.set_corner_radius_all(int(radius))
		sb.anti_aliasing = true
		_rounds[key] = sb
	ci.draw_style_box(_rounds[key], rect)

## A soft radial glow of `col` fading out to the rect's edge (an ellipse in a wide rect): a lit centre, a dais, a shadow.
func glow(rect: Rect2, col: Color) -> void:
	glow_on(self, rect, col)

## glow() on any canvas item.
static func glow_on(ci: CanvasItem, rect: Rect2, col: Color) -> void:
	var key := col.to_html()
	if not _glows.has(key):
		var g := Gradient.new()
		g.set_color(0, col)
		g.set_color(1, Color(col, 0.0))
		var tex := GradientTexture2D.new()
		tex.gradient = g
		tex.fill = GradientTexture2D.FILL_RADIAL
		tex.fill_from = Vector2(0.5, 0.5)
		tex.fill_to = Vector2(0.5, 0.0)
		tex.width = 128
		tex.height = 128
		_glows[key] = tex
	ci.draw_texture_rect(_glows[key], rect, false)

## Bright glows at 0.3 of their alpha with Settings › Bright flashes off (page_identity §6).
func halo_k() -> float:
	return 1.0 if Game.account.settings.get("flashes", true) else 0.3

## A slow pulse for a live mark's glow; none under Reduce motion.
func _pulse() -> float:
	return 0.0 if UiKit.reduce_motion() else sin(t * 4.0)

## A world event's plum blossom (the World map, the Calendar): gold with a red heart under way, violet with a pale
## heart when it is coming.
func _blossom(c: Vector2, live: bool, k: float) -> void:
	var col := UiKit.GOLD if live else UiKit.SOUL
	if live: glow(Rect2(c - Vector2.ONE * 20.0 * k, Vector2.ONE * 40.0 * k), Color(UiKit.GOLD, (0.35 + 0.1 * _pulse()) * halo_k()))
	for layer in [[5.1, UiKit.INK], [4.5, col]]:
		for i in 5: draw_circle(c + Vector2.from_angle(-PI * 0.5 + i * TAU / 5.0) * 6.0 * k, float(layer[0]) * k, layer[1], true, -1.0, true)
	draw_circle(c, 2.5 * k, UiKit.BLOOD if live else UiKit.PAPER, true, -1.0, true)

## Draw what follows moved by `pos`, turned by `rot` and scaled by `scl` (a part in motion); the HD faces move with it.
## `move()` with no arguments puts it back. Regions stay where the part comes to rest (page_identity §8.5).
func move(pos := Vector2.ZERO, rot := 0.0, scl := Vector2.ONE) -> void:
	draw_set_transform(pos, rot, scl)
	HdStyleBox.base = Transform2D(rot, scl, 0.0, pos)

## A vertical gradient over `r` from `top` to `bottom` (a desk, a wall, a paper's shade).
func vshade(r: Rect2, top: Color, bottom: Color) -> void:
	draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]), PackedColorArray([top, top, bottom, bottom]))

## A horizontal gradient over `r` from `left` to `right` (a gutter's shadow, a page's edge).
func hshade(r: Rect2, left: Color, right: Color) -> void:
	draw_polygon(PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)]), PackedColorArray([left, right, right, left]))

var _way := {}   # the last route asked for: key -> regions it crosses (a route is walked once per choice)

## How many regions the way to `room` crosses from where the character stands, by the portals open to it; 0 when there
## is none (or it stands there). The Calendar's and the Quests' Go there walk it by the auto_path intent.
func regions_away(ch, room: String) -> int:
	if ch == null or room == "": return 0
	var from := str(ch.position.get("room", ""))
	var key := "%s|%s|%d" % [room, from, Game.account.visited_rooms.size()]
	if not _way.has(key):
		var regions := {}
		for s in Game.world.route(ch, from, room): regions[str(ContentDB.room(str(s.to)).get("region", ""))] = true
		_way = {key: regions.size()}
	return int(_way[key])

## Why Go there is shut for `room`: the character stands there, or no way leads there.
func go_reason(ch, room: String) -> String:
	return Tx.t("sim.world.auto_path_here") if ch != null and str(ch.position.get("room", "")) == room else Tx.t("sim.world.auto_path_none")

func lock_icon(p: Vector2, k := 1.0) -> void:
	draw_rect(Rect2(p + Vector2(0, 6) * k, Vector2(12, 9) * k), UiKit.BRONZE)
	draw_arc(p + Vector2(6, 6) * k, 4 * k, PI, TAU, 8, UiKit.BRONZE, 2 * k)

## Button: registers a tap region. Disabled buttons still answer taps with their reason. An `icon` stands at 32 px before
## the label (or alone, centred, with no label).
func btn(rect: Rect2, label: String, id: String, data = null, primary := false, enabled := true, reason := "", size := 22, icon := "") -> void:
	var state := "normal"
	if not enabled: state = "disabled"
	elif _is_pressed(id, data): state = "pressed"
	draw_style_box(UiKit.style("button_primary" if primary else "button_secondary", state), rect)
	var off := Vector2(1, 2) if state == "pressed" else Vector2.ZERO
	var col := UiKit.PALE_GOLD if primary else UiKit.PAPER
	if not enabled: col = UiKit.HOLLOW
	# A long label steps its size down the type scale to sit inside the button (and clear the lock icon) rather than
	# touch the frame.
	var iw := 38.0 if icon != "" else 0.0   # the icon and its gap
	var room := rect.size.x - (44.0 if not enabled and reason != "" else (10.0 if icon != "" else 20.0)) - iw
	if label != "" and label.length() * size * 0.6 > room:   # only a label that could overflow is measured
		# B21: words are never drawn under UiKit.MIN_SIZE, so the steps stop there and a label still too long is shortened.
		while size > UiKit.MIN_SIZE and UiKit.text_width(label, size) > room: size = UiKit.step_down(size)
		label = fit(label, size, room)
	# The label's span: the whole face, or after the icon with the two centred together.
	var lx := rect.position.x
	var lw := rect.size.x
	if icon != "":
		var tw := UiKit.text_width(label, size) if label != "" else -8.0
		var x0 := roundf(rect.get_center().x - (iw + tw) * 0.5)
		icon_at(Rect2(Vector2(x0, roundf(rect.get_center().y - 16.0)) + off, Vector2(32, 32)), icon, Color.WHITE if enabled else Color(1, 1, 1, 0.45))
		lx = x0 + iw
		lw = maxf(tw, 1.0)
	var at := Vector2(lx, rect.position.y + rect.size.y * 0.5 + size * 0.35)
	# Decision 10 (option C): a primary label, in every state, carries a 2 px ink outline on the bright jade face.
	if label != "":
		if primary: UiKit.draw_inked(self, label, at + off, size, col, HORIZONTAL_ALIGNMENT_CENTER, lw)
		else: UiKit.draw_text(self, label, at + off, size, col, HORIZONTAL_ALIGNMENT_CENTER, lw)
		if text_log != null: _log_text(at, label, size, HORIZONTAL_ALIGNMENT_CENTER, lw, false, rect, col, primary)
	if not enabled and reason != "": lock_icon(rect.position + Vector2(rect.size.x - 20, 6))
	_register(rect, id, data, enabled, reason, "button")

## Invisible tap region (rows, cards, map nodes).
func region(rect: Rect2, id: String, data = null, enabled := true, reason := "") -> void:
	_register(rect, id, data, enabled, reason, "region")

func _register(rect: Rect2, id: String, data, enabled: bool, reason: String, kind: String) -> void:
	# P4: every tap target is at least MIN_TAP on each side. Smaller art keeps its look and gains a margin of hit
	# area round its centre; `full` keeps that rect before any scroll clipping, and `art` the drawn one, for the ui_suite.
	var art := rect
	if rect.size.x < MIN_TAP or rect.size.y < MIN_TAP:
		var grown := Vector2(maxf(rect.size.x, MIN_TAP), maxf(rect.size.y, MIN_TAP))
		rect = Rect2(rect.get_center() - grown * 0.5, grown)
	var full := rect
	# Regions inside a scroll area are clipped to it.
	for aid in _areas:
		var a: Dictionary = _areas[aid]
		if a.get("active", false):
			rect = rect.intersection(a.rect)
			if rect.size.x <= 0 or rect.size.y <= 0: return
	_regions.append({"rect": rect, "full": full, "art": art, "id": id, "data": data, "enabled": enabled, "reason": reason, "kind": kind})

func _is_pressed(id: String, data = null) -> bool:
	if _pressed < 0 or _pressed >= _prev_regions.size(): return false
	var r: Dictionary = _prev_regions[_pressed]
	return r.id == id and (data == null or r.data == data)

var _prev_regions: Array = []

## A line of text. Given a width, it never runs past it: a longer line ends in an ellipsis (B18).
func text(pos: Vector2, s: String, size := 20, col := UiKit.PAPER, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0, display := false) -> void:
	if width > 0.0: s = fit(s, size, width, display)
	UiKit.draw_text(self, s, pos, size, col, align, width, true, display)
	if text_log != null: _log_text(pos, s, size, align, width, display, Rect2(), col)

## A title on the plaque (decision 10): the words with a 2 px ink outline (UiKit.draw_inked), shortened to `width`.
func inked(pos: Vector2, s: String, size: int, col := UiKit.PALE_GOLD, align := HORIZONTAL_ALIGNMENT_CENTER, width := -1.0, display := true) -> void:
	if width > 0.0: s = fit(s, size, width, display)
	UiKit.draw_inked(self, s, pos, size, col, align, width, display)
	if text_log != null: _log_text(pos, s, size, align, width, display, Rect2(), col, true)

## Words in several colours wrapped to `rect`'s width, `runs` [[text, Color], ...] (a lead phrase and its line, an
## item's quality, grade and kind), each line from the left or `centred`. Words past the rect's foot are not drawn.
## Returns the height used.
func rich(rect: Rect2, runs: Array, size := 18, centred := false) -> float:
	var lh := UiKit.line_height(size)
	var gap := UiKit.text_width("a b", size) - UiKit.text_width("ab", size)
	var lines: Array = [[]]   # each line's words: [word, colour, x from the line's start, width]
	var x := 0.0
	for run in runs:
		for w in str(run[0]).split(" ", false):
			var ww := UiKit.text_width(w, size)
			if x > 0.0 and x + ww > rect.size.x:
				lines.append([])
				x = 0.0
			lines[-1].append([w, run[1], x, ww])
			x += ww + gap
	for i in lines.size():
		var y := rect.position.y + size * UiKit.text_scale() + i * lh
		if y > rect.end.y + 2: return i * lh
		var ln: Array = lines[i]
		var shift := (rect.size.x - float(ln[-1][2]) - float(ln[-1][3])) * 0.5 if centred and not ln.is_empty() else 0.0
		for w in ln: text(Vector2(rect.position.x + shift + float(w[2]), y), w[0], size, w[1])
	return lines.size() * lh

## The ui_suite's record of the words a page drew, [{rect, s}]; null (off) in play.
var text_log = null

func _log_text(pos: Vector2, s: String, size: int, align: int, width: float, display: bool, button := Rect2(), col := Color.TRANSPARENT, outlined := false) -> void:
	var w := UiKit.text_width(s, size, display)
	var px := float(UiKit.size_for(s, size, display))
	var x := pos.x
	if width > 0.0 and align == HORIZONTAL_ALIGNMENT_CENTER: x += (width - w) * 0.5
	elif width > 0.0 and align == HORIZONTAL_ALIGNMENT_RIGHT: x += width - w
	# P4: the size asked for, so the ui_suite can hold every word to the type scale; P5: the colour, and whether it is
	# outlined in ink (measured on INK), so it can measure each word on its ground.
	text_log.append({"rect": Rect2(x, pos.y - px * 0.7, w, px * 0.9), "s": s, "button": button, "size": size, "display": display, "col": col, "outlined": outlined})

## `s` shortened with an ellipsis so it fits `width` at `size` (UiKit.fit).
func fit(s: String, size: int, width: float, display := false) -> String:
	return UiKit.fit(s, size, width, display)

func heading(pos: Vector2, s: String, width := 400.0) -> void:
	# A long heading steps down the display scale, 26 to 22, to fit its width, and past that ends in an ellipsis.
	var size := 26
	if UiKit.text_width(s, size, true) > width: size = 22
	s = fit(s, size, width, true)
	UiKit.draw_text(self, s, pos, size, UiKit.GOLD, HORIZONTAL_ALIGNMENT_LEFT, width, true, true)
	if text_log != null: _log_text(pos, s, size, HORIZONTAL_ALIGNMENT_LEFT, width, true, Rect2(), UiKit.GOLD)
	draw_line(pos + Vector2(0, 8), pos + Vector2(minf(width, UiKit.text_width(s, size, true) + 30), 8), UiKit.BRONZE, 2)

## Word-wrapped paragraph. Returns the height used.
func para(rect: Rect2, s: String, size := 18, col := UiKit.PAPER, max_lines := -1, display := false) -> float:
	var lines := _wrap(s, size, rect.size.x, display)
	var lh := UiKit.line_height(size)
	var y := rect.position.y + size * UiKit.text_scale()
	var n := 0
	for i in lines.size():
		if max_lines > 0 and n >= max_lines: break
		if y > rect.end.y + 2: break
		var ln := str(lines[i])
		# B18: a paragraph cut short by its line count or its height ends its last line with an ellipsis.
		var cut := (max_lines > 0 and n + 1 >= max_lines) or y + lh > rect.end.y + 2
		if cut and lines.slice(i + 1).any(func(rest): return str(rest).strip_edges() != ""): ln = fit(ln + "…", size, rect.size.x, display)
		UiKit.draw_text(self, ln, Vector2(rect.position.x, y), size, col, HORIZONTAL_ALIGNMENT_LEFT, -1.0, true, display)
		if text_log != null: _log_text(Vector2(rect.position.x, y), ln, size, HORIZONTAL_ALIGNMENT_LEFT, -1.0, display, Rect2(), col)
		y += lh
		n += 1
	return n * lh

func _wrap(s: String, size: int, width: float, display := false) -> Array:
	return UiKit.wrap(s, size, width, display)

## The words on a bar (Page.bar): a caption on the type scale that sits inside a 22 px bar.
const BAR_LABEL := 16

func bar(rect: Rect2, frac: float, col: Color, label := "") -> void:
	draw_style_box(UiKit.style("bar_shell"), rect)
	var inner := rect.grow_individual(-6, -5, -6, -5)
	draw_rect(inner, UiKit.BAR_TROUGH)
	draw_rect(Rect2(inner.position, Vector2(inner.size.x * clampf(frac, 0.0, 1.0), inner.size.y)), col)
	draw_rect(Rect2(inner.position, Vector2(inner.size.x * clampf(frac, 0.0, 1.0), 2)), col.lightened(0.35))
	if label != "":
		UiKit.draw_outlined(self, label, rect.position + Vector2(0, rect.size.y * 0.5 + 6), BAR_LABEL, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x)
		if text_log != null: _log_text(rect.position + Vector2(0, rect.size.y * 0.5 + 6), label, BAR_LABEL, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, false, rect, UiKit.PAPER, true)

func panel(rect: Rect2, asset := "minor_panel", state := "normal") -> void:
	draw_style_box(UiKit.style(asset, state), rect)
	if text_log != null: text_log.append({"rect": rect, "s": "", "button": Rect2(), "panel": true, "ground": "%s:%s" % [asset, state]})

## Item slot with icon, count, quality edge and state overlays. Use SLOT (a 64 px icon) or SLOT_SMALL (32): the icon
## is drawn at a whole-number scale in the 6 px inset, so another size only adds margin round it.
func slot_box(rect: Rect2, item_id: String, count := 0, quality := "", id := "", data = null, selected := false, locked := false) -> void:
	draw_style_box(UiKit.style("slot", "pressed" if (id != "" and _is_pressed(id, data)) else "normal"), rect)
	if item_id != "":
		var inner := rect.grow(-6)
		if quality.begins_with("pill_"): _pill_glow(rect, quality)
		else: _grade_halo(rect, item_id)
		if first_draw() and not SpriteCache.icon_loaded(item_id, minf(inner.size.x, inner.size.y)): SpriteCache.icon_prefetch(item_id)
		elif SpriteCache.draw_icon(self, inner, item_id) == Rect2():
			draw_rect(inner, UiKit.DEEP_TEAL)
			text(inner.position + Vector2(0, inner.size.y * 0.6), ContentDB.item_name(item_id).left(3), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, inner.size.x)
		var graded := quality != "" and quality != "plain" and quality != "common"
		if grade_rims:
			# P5 (mockups 07, 09 v2): every item wears its grade on the rim, so a full grid sorts itself by eye; a rolled
			# quality is a gem in the corner (a pill keeps its glow and mark).
			draw_rect(rect.grow(-3), UiKit.grade_color(str(ContentDB.item(item_id).get("grade", "plain"))), false, 2)
			if graded and not quality.begins_with("pill_"): _gem(rect.position + Vector2(11, 11), UiKit.quality_color(quality))
		elif graded:
			draw_rect(rect.grow(-3), UiKit.quality_color(quality), false, 2)
		if count > 1:
			UiKit.draw_outlined(self, str(count), rect.end - Vector2(rect.size.x, 5), 18, UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, rect.size.x - 5)
		if locked: lock_icon(rect.position + (Vector2(5, rect.size.y - 21) if grade_rims else Vector2(4, 4)))
	if selected: draw_style_box(UiKit.style("selected_slot_glow"), rect.grow(4))
	if id != "": region(rect, id, data)

## A quality gem: a small diamond in the quality's colour with an ink edge.
func _gem(c: Vector2, col: Color) -> void:
	for layer in [[7.5, UiKit.INK], [5.5, col]]:
		var r: float = layer[0]
		draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r), c + Vector2(r, 0), c + Vector2(0, r), c + Vector2(-r, 0)]), layer[1])
	draw_circle(c + Vector2(-1.5, -1.5), 1.2, Color(UiKit.PAPER, 0.8))

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

## P4b: a soft steady halo in the grade's colour behind an item of Mystic grade and above (the soft glow of the icon
## study's Style B, drawn by the slot rather than baked into the icon).
func _grade_halo(rect: Rect2, item_id: String) -> void:
	var g := str(ContentDB.item(item_id).get("grade", "plain"))
	if StatRules.grade_index(g) < StatRules.grade_index("mystic"): return
	var col := UiKit.grade_color(g)
	for i in 3:
		draw_circle(rect.get_center(), rect.size.x * (0.30 + 0.06 * i), Color(col.r, col.g, col.b, 0.11 - 0.03 * i))

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

## An icon centred in `rect` at the largest whole-number scale of its art that fits (SpriteCache.draw_icon):
## give 32 or 64 for an item, 32 for a HUD glyph, 24 for a status icon.
func icon_at(rect: Rect2, icon_id: String, modulate := Color.WHITE) -> void:
	if first_draw() and not SpriteCache.icon_loaded(icon_id, minf(rect.size.x, rect.size.y)):
		SpriteCache.icon_prefetch(icon_id)
		_waiting = true
		return
	SpriteCache.draw_icon(self, rect, icon_id, modulate)

## The frame a page that fades in opens on (it is all but transparent; it may draw more than once in it, as the events of
## a catch-up step ask): art not yet in memory (icons, creature sheets, HD faces asked for by hd_tex) is asked of a
## loading thread and drawn from the next frame, by when it is in memory or nearly, so opening a page never waits on a
## screenful of files (perf_tests: every page opens in under 0.15 s).
func first_draw() -> bool:
	return identity != null and (_open_frame < 0 or Engine.get_process_frames() == _open_frame)

## An HD kit texture (UiKit.hd_texture), or null on the first frame while it loads.
func hd_tex(asset: String, state := "normal") -> Texture2D:
	var tx: Texture2D = UiKit.hd_texture_async(asset, state) if first_draw() else UiKit.hd_texture(asset, state)
	if tx == null: _waiting = true
	return tx

## One creature-sheet frame fitted into `rect`, feet on its bottom edge. `action`
## loops with the page clock. Returns false when the creature has no sheet.
func creature_at(rect: Rect2, creature_id: String, action := "idle", modulate := Color.WHITE) -> bool:
	var file := str(SpriteCache.creature(creature_id).get("file", ""))
	if first_draw() and SpriteCache.loading(file) and SpriteCache.tex_async(file) == null:   # still loading: the slot waits
		_waiting = true
		return true
	return UiKit.draw_creature(self, rect, creature_id, action, t, modulate)

func currency_pill(pos: Vector2, currency: String, amount: int) -> float:
	var s := UiKit.fmt(amount)
	var w := UiKit.text_width(s, 18) + 54
	var r := Rect2(pos, Vector2(w, 34))
	face(r, "currency_pill")   # P5: its words are read on the pill, wherever it sits
	icon_at(Rect2(pos + Vector2(4, 1), Vector2(32, 32)), currency_icon(currency))
	text(pos + Vector2(40, 24), s, 18, UiKit.PALE_GOLD)
	return w

## The icon of a currency (currencies.json; taels show the silver coin).
static func currency_icon(currency: String) -> String:
	if currency == "silver_tael": return "coin"
	for cdef in ContentDB.config("currencies").get("currencies", []):
		if str(cdef.get("id", "")) == currency: return str(cdef.get("icon", "coin"))
	return "coin"

static func currency_name(currency: String) -> String:
	for cdef in ContentDB.config("currencies").get("currencies", []):
		if str(cdef.get("id", "")) == currency: return str(cdef.get("name", currency))
	return currency

## Scrolling list: calls draw_row(i, rect) for rows inside `rect`; drag or wheel to scroll.
func list(area: String, rect: Rect2, count: int, row_h: float, draw_row: Callable) -> void:
	var total := count * row_h
	var max_scroll := maxf(0.0, total - rect.size.y)
	var off := clampf(float(scroll.get(area, 0.0)), 0.0, max_scroll)
	scroll[area] = off
	_areas[area] = {"rect": rect, "max": max_scroll, "active": false, "pitch": row_h}
	_regions.append({"rect": rect, "id": "_scroll", "data": area, "enabled": true, "reason": "", "kind": "scroll"})
	var first := int(off / row_h)
	var last := mini(count - 1, int((off + rect.size.y) / row_h))
	_areas[area].active = true
	for i in range(first, last + 1):
		var y := rect.position.y + i * row_h - off
		var rr := Rect2(rect.position.x, y, rect.size.x - GUTTER, row_h - ROW_GAP)
		if rr.position.y < rect.position.y - 1 or rr.end.y > rect.end.y + 1: continue
		draw_row.call(i, rr)
	_areas[area].active = false
	if max_scroll > 0:
		var track := Rect2(rect.end.x - 4, rect.position.y, 4, rect.size.y)
		draw_rect(track, Color(UiKit.PAPER, 0.08))
		var h := maxf(24.0, rect.size.y * rect.size.y / total)
		draw_rect(Rect2(track.position.x, rect.position.y + (rect.size.y - h) * off / max_scroll, 4, h), UiKit.JADE)

func ask(text_: String, id: String, data = null, danger := false) -> void:
	confirm = {"text": text_, "id": id, "data": data, "danger": danger}

func _draw_confirm() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(UiKit.INK, 0.5))
	var r := WINDOW_CONFIRM
	draw_style_box(UiKit.style("major_window"), r)
	para(Rect2(r.position + Vector2(INSET, INSET), Vector2(r.size.x - INSET * 2.0, 104)), str(confirm.text), 22)
	btn(Rect2(r.position.x + INSET, r.end.y - 80, 192, BTN_H_STANDARD), Tx.t("ui.page.cancel"), "_confirm_no")
	btn(Rect2(r.end.x - INSET - 192, r.end.y - 80, 192, BTN_H_STANDARD), Tx.t("ui.page.confirm"), "_confirm_yes", null, true)

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

## The tap that opened the page (a HUD button, handled in the HUD's _input) goes on to the page just made, in the same
## frame; it and its release are not the page's (its release, outside the window, closed the Mail as it opened: the
## Mail button stands right of the window, decision 43's guide found it).
var _born := -1
var _stray := false

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and Engine.get_process_frames() == _born:
			_stray = true
			accept_event()
			return
		if not event.pressed and _stray:
			_stray = false
			accept_event()
			return
	if redraw_on_change and (event is InputEventMouseButton or (event is InputEventMouseMotion and event.button_mask != 0)): queue_redraw()
	_prev_regions = _regions.duplicate()
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and event.pressed:
			var a := _scroll_area_at(event.position)
			if a != "": scroll[a] = float(scroll.get(a, 0.0)) + (-60.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 60.0)
			accept_event()
			return
		if event.button_index != MOUSE_BUTTON_LEFT: return
		if event.pressed:
			opened = maxf(opened, OPEN_MOTION_MAX)   # a tap finishes the opening (page_identity §6 rule 1)
			_pressed = _hit(event.position)
			_press_pos = event.position
			_dragged = false
			_drag_area = _scroll_area_at(event.position)
			_drag_last = event.position.y
		else:
			var idx := _hit(event.position)
			if idx >= 0 and idx == _pressed and not _dragged: activate(_prev_regions[idx])
			elif _pressed < 0 and confirm.is_empty() and not frameless and not window_rect().has_point(event.position) and not _dragged: close()
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

func activate(r: Dictionary) -> void:
	var id := str(r.id)
	if not r.enabled:
		if str(r.reason) != "": flash(str(r.reason))
		Audio.ui("ui_error")
		return
	Audio.ui("ui_tab" if id == "_tab" else "ui_tap")   # decision 43: a tab turns like a page
	match id:
		"_close": close()
		"_help": navigate.emit("_tour", {"page": page_id, "tab": tab_id()})
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
		queue_redraw()
		if not confirm.is_empty(): confirm = {}
		elif frameless: return
		else: close()
		get_viewport().set_input_as_handled()
