class_name TechniquePicture
extends RefCounted
## Decision 42 (the prototype APK's feedback): an art's picture as the Techniques tree's node cards compose it
## (techniques_page.gd `_card_picture`): the character in the art's pose (TechniquePreview.pose_of; the Avatar's still of
## that pose, drawn at half its 256 px cell so each art pixel is one screen pixel) on its element's ground with the
## card's glow, in the tree's frame (bright jade: an art that is ready), and the art's emblem in the top left corner. The
## HUD's technique buttons and the Techniques page's loadout bar draw it at a button's size, where the card shows the
## figure whole: the figure is framed from its head down, a light rim round it so it reads on the dark ground at a
## thumb's size, and the emblem is a round seal of its 32 px render's middle (the card's emblem is 32 px across, too
## big for a button), which tells two arts of one pose apart.
##
## States read over any picture: the cooldown's ink sweep with its seconds; short of Qi, the picture dimmed and a Qi
## strip along its foot filled as far as the pool reaches the cost; closed (the weapon in hand cannot use it), a slate
## frame, the picture dim and a lock in the corner.

const Avatar = preload("res://scripts/avatar.gd")
const FEET := Vector2(128, 190)   # where the still's feet stand in its 256 px square (Avatar.still_image)
const STILL_K := 0.5              # the still's scale: an art pixel to a screen pixel (the art is authored at x2)
const SEAL := 20                  # the corner seal's size: the middle 16 px of the emblem's 32 px render in a 2 px rim
const HELD := 64                  # stills kept (a full cache starts again)
static var _stills: Dictionary = {}   # outfit|pose -> {tex, rim, box}: the still, its silhouette, the figure's box (px)
static var _composed_at := -1         # the frame that last composed a still: one a frame, so no frame stalls
static var _seals: Dictionary = {}    # art -> its round seal (ImageTexture)
static var _boxes: Dictionary = {}    # radius|colour -> StyleBoxFlat
static var _glow: GradientTexture2D
## Tests: each picture drawn, [{id, rect, where}] (null: off, as SpriteCache.draw_log).
static var draw_log = null

## The still of `outfit` in `pose` ({tex, box}), composed at most one a frame; {} until it is. `now` composes at once.
static func still(outfit: Dictionary, pose: String, now := false) -> Dictionary:
	var key := str(outfit) + "|" + pose
	if _stills.has(key): return _stills[key]
	var frame := Engine.get_process_frames()
	if not now and _composed_at == frame: return {}
	_composed_at = frame
	var a = Avatar.new()
	a.outfit = outfit
	a.play(pose)
	a.elapsed = 0.3
	var img: Image = a.still_image()
	a.free()
	# The figure's silhouette in white, for its rim.
	var white := Image.create(img.get_width(), img.get_height(), false, Image.FORMAT_RGBA8)
	white.fill(Color.WHITE)
	var sil := Image.create(img.get_width(), img.get_height(), false, Image.FORMAT_RGBA8)
	sil.blit_rect_mask(white, img, Rect2i(Vector2i.ZERO, img.get_size()), Vector2i.ZERO)
	if _stills.size() >= HELD: _stills.clear()
	_stills[key] = {"tex": ImageTexture.create_from_image(img), "rim": ImageTexture.create_from_image(sil), "box": img.get_used_rect()}
	return _stills[key]

## True when every art of `ids` has its still for `outfit` (a caller may wait on it; the tests do).
static func stills_ready(ids: Array, who, outfit: Dictionary) -> bool:
	return ids.all(func(id): return _stills.has(str(outfit) + "|" + TechniquePreview.pose_of(ContentDB.entry("techniques", str(id)), who, outfit)))

## Technique `tid`'s picture filling `r`, its frame included. `who` is the character (a family art's pose), `outfit` its
## look; `frame` the frame's colour, `k` the picture's brightness (a closed or short art is dimmed), `a` the opacity
## (a page turn's fade). `where` names the caller in the draw log.
static func draw(ci: CanvasItem, r: Rect2, tid: String, who, outfit: Dictionary, frame := UiKit.BRIGHT_JADE, k := 1.0, a := 1.0, where := "") -> void:
	var t := ContentDB.entry("techniques", tid)
	var ec := SpriteCache.element_color(str(t.get("element", "none")))
	rounded(ci, r, 5.0, Color(UiKit.INK, a))
	rounded(ci, r.grow(-1.0), 4.0, Color(frame, a))
	var p := r.grow(-3.0)
	rounded(ci, p, 3.0, Color(UiKit.INK, a))
	if t.is_empty(): return   # an art no longer in the book: the empty frame
	# The ground, as the card's: the element's dark over ink, and its glow round the figure's middle.
	var top := Color(ec.darkened(0.55), a)
	var foot := Color(UiKit.INK, a)
	ci.draw_polygon(PackedVector2Array([p.position, Vector2(p.end.x, p.position.y), p.end, Vector2(p.position.x, p.end.y)]), PackedColorArray([top, top, foot, foot]))
	ci.draw_texture_rect(_glow_tex(), Rect2(p.position + p.size * Vector2(0.11, 0.42), p.size * Vector2(0.78, 0.56)), false, Color(ec, 0.3 * a * k))
	var st := still(outfit, TechniquePreview.pose_of(t, who, outfit))
	if not st.is_empty():
		_figure(ci, p, st, Color(Color.WHITE.lerp(ec.lightened(0.3), 0.3) * Color(k, k, k), a), Color(ec.lightened(0.55), 0.7 * a * k))
		_seal(ci, p, tid, Color(k, k, k, a))
	else:
		# Until the still is composed (a frame or two), the emblem stands in, as on the card.
		SpriteCache.draw_icon(ci, p, tid, Color(k, k, k, a))
	if draw_log != null: draw_log.append({"id": tid, "rect": r, "where": where, "figure": not st.is_empty(), "frame": frame, "k": k})

## The figure at an art pixel a screen pixel, a little right of the middle (clear of the seal) with its feet on the
## card's horizon when it fits, else framed from its head down; a 1 px rim of `rim` round it; cut to the picture.
static func _figure(ci: CanvasItem, p: Rect2, st: Dictionary, tint: Color, rim: Color) -> void:
	var box: Rect2i = st.box
	if box.size.x <= 0: return
	var origin := Vector2(roundf(p.get_center().x + 3.0 - FEET.x * STILL_K), p.end.y - 6.0 - FEET.y * STILL_K)
	var head := origin.y + box.position.y * STILL_K
	if head < p.position.y + 3.0: origin.y += p.position.y + 3.0 - head
	origin.y = roundf(origin.y)
	var inner := p.grow(-1.0)
	for d in [Vector2(-1, 0), Vector2(1, 0), Vector2(0, -1), Vector2(0, 1)]:
		var ring := Rect2(origin + d, Vector2(256, 256) * STILL_K).intersection(inner)
		if ring.size.x > 0.0 and ring.size.y > 0.0:
			ci.draw_texture_rect_region(st.rim, ring, Rect2((ring.position - origin - d) / STILL_K, ring.size / STILL_K), rim)
	var shown := Rect2(origin, Vector2(256, 256) * STILL_K).intersection(inner)
	if shown.size.x <= 0.0 or shown.size.y <= 0.0: return
	ci.draw_texture_rect_region(st.tex, shown, Rect2((shown.position - origin) / STILL_K, shown.size / STILL_K), tint)

## The art's emblem as a round seal in the top left corner (SEAL px across, at 1x): the middle of its 32 px render in a
## gold rim and an ink edge, composed once an art.
static func _seal(ci: CanvasItem, p: Rect2, tid: String, tint: Color) -> void:
	var tex: Texture2D = _seals.get(tid)
	if tex == null:
		var f := SpriteCache.icon_fit(tid, 32.0)
		if f.is_empty(): return
		var src: Image = (f.tex as Texture2D).get_image()
		if src == null: return
		if src.is_compressed(): src.decompress()
		src.convert(Image.FORMAT_RGBA8)
		var img := Image.create(SEAL, SEAL, false, Image.FORMAT_RGBA8)
		var off := Vector2i((src.get_width() - SEAL) / 2, (src.get_height() - SEAL) / 2)
		var mid := Vector2(SEAL, SEAL) * 0.5 - Vector2(0.5, 0.5)
		for y in SEAL:
			for x in SEAL:
				var d := Vector2(x, y).distance_to(mid)
				if d > SEAL * 0.5: continue
				if d > SEAL * 0.5 - 1.0: img.set_pixel(x, y, UiKit.INK)
				elif d > SEAL * 0.5 - 2.0: img.set_pixel(x, y, UiKit.GOLD)
				else: img.set_pixel(x, y, src.get_pixel(off.x + x, off.y + y))
		tex = ImageTexture.create_from_image(img)
		if _seals.size() >= HELD: _seals.clear()
		_seals[tid] = tex
	ci.draw_texture_rect(tex, Rect2(p.position + Vector2(1, 1), Vector2(SEAL, SEAL)), false, tint)

## The cooldown over a picture in `r`: an ink sweep over the `frac` still to wait, from the top round, cut to the
## picture, its edge a pale gold hand; the seconds left in the middle.
static func draw_cooldown(ci: CanvasItem, r: Rect2, frac: float, seconds: float, a := 1.0) -> void:
	var p := r.grow(-3.0)
	var f := clampf(frac, 0.0, 1.0)
	if f > 0.02:
		var c := p.get_center()
		var reach := p.size.length()
		var pie := PackedVector2Array([c])
		for i in 33: pie.append(c + Vector2.from_angle(-PI / 2.0 + TAU * f * (i / 32.0)) * reach)
		var box := PackedVector2Array([p.position, Vector2(p.end.x, p.position.y), p.end, Vector2(p.position.x, p.end.y)])
		for poly in Geometry2D.intersect_polygons(pie, box): ci.draw_colored_polygon(poly, Color(UiKit.INK, 0.72 * a))
		var hand := Vector2.from_angle(-PI / 2.0 + TAU * f)
		var half := p.size * 0.5
		ci.draw_line(c, c + hand * minf(half.x / maxf(0.001, absf(hand.x)), half.y / maxf(0.001, absf(hand.y))), Color(UiKit.PALE_GOLD, 0.85 * a), 1.5)
	UiKit.draw_outlined(ci, str(int(ceil(seconds))), Vector2(r.get_center().x - 20.0, r.get_center().y + 8.0), 22, Color(UiKit.PAPER, a), HORIZONTAL_ALIGNMENT_CENTER, 40)
	if draw_log != null: draw_log.append({"state": "cooldown", "rect": r, "frac": f})

## Short of Qi: a strip along the picture's foot, the pool's reach toward the cost in Qi blue on an ink trough.
static func draw_qi_short(ci: CanvasItem, r: Rect2, frac: float, a := 1.0) -> void:
	var p := r.grow(-3.0)
	var strip := Rect2(p.position.x + 2.0, p.end.y - 7.0, p.size.x - 4.0, 5.0)
	ci.draw_rect(strip.grow(1.0), Color(UiKit.INK, a))
	ci.draw_rect(Rect2(strip.position, Vector2(strip.size.x * clampf(frac, 0.0, 1.0), strip.size.y)), Color(UiKit.QI, a))
	if draw_log != null: draw_log.append({"state": "qi", "rect": r, "frac": clampf(frac, 0.0, 1.0)})

## Closed: a lock in the lower right corner, bronze on an ink plate.
static func draw_lock(ci: CanvasItem, r: Rect2, a := 1.0) -> void:
	if draw_log != null: draw_log.append({"state": "lock", "rect": r})
	var at := r.end - Vector2(19, 21)
	rounded(ci, Rect2(at - Vector2(3, 3), Vector2(20, 22)), 4.0, Color(UiKit.INK, 0.85 * a))
	ci.draw_arc(at + Vector2(7, 7), 4.5, PI, TAU, 10, Color(UiKit.BRONZE, a), 2.5)
	ci.draw_rect(Rect2(at + Vector2(0, 7), Vector2(14, 10)), Color(UiKit.BRONZE, a))
	ci.draw_rect(Rect2(at + Vector2(6, 10), Vector2(2, 4)), Color(UiKit.INK, a))

static func rounded(ci: CanvasItem, rect: Rect2, radius: float, col: Color) -> void:
	var key := "%d|%s" % [int(radius), col.to_html()]
	if not _boxes.has(key):
		var sb := StyleBoxFlat.new()
		sb.bg_color = col
		sb.set_corner_radius_all(int(radius))
		sb.anti_aliasing = true
		if _boxes.size() > 256: _boxes.clear()
		_boxes[key] = sb
	ci.draw_style_box(_boxes[key], rect)

static func _glow_tex() -> GradientTexture2D:
	if _glow == null:
		var g := Gradient.new()
		g.set_color(0, Color.WHITE)
		g.set_color(1, Color(1, 1, 1, 0))
		_glow = GradientTexture2D.new()
		_glow.gradient = g
		_glow.fill = GradientTexture2D.FILL_RADIAL
		_glow.fill_from = Vector2(0.5, 0.5)
		_glow.fill_to = Vector2(0.5, 0.0)
		_glow.width = 128
		_glow.height = 128
	return _glow
