extends RefCounted
## P5 · The sect family's shared pieces (docs/page_identity.md §2, "The sect": red-lacquered pillars and dark timber,
## bronze and red paper): the Menu, Your Sect, the Sect and the Characters pages draw their own layouts from these. Every
## piece draws on the page it is given, from tokens, and names the ground its words sit on (Page.ground), so the
## ui_suite measures them. The figures (sect disciples, your characters) are the live Avatar at whole art pixels.

const Avatar = preload("res://scripts/avatar.gd")
const DialoguePage = preload("res://scripts/ui/pages/dialogue_page.gd")

## A red-lacquered pillar filling `r`: the round shaft shaded across, a gilt capital and base.
static func pillar(pg: Page, r: Rect2) -> void:
	pg.draw_rect(r.grow_individual(1, 0, 1, 0), Color(UiKit.INK, 0.8))
	var dark: Color = UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.35)
	var lit: Color = UiKit.SURFACE.lacquer.lerp(UiKit.RED, 0.45)
	var half := Rect2(r.position, Vector2(r.size.x * 0.4, r.size.y))
	pg.hshade(half, dark, lit)
	pg.hshade(Rect2(half.end.x, r.position.y, r.size.x - half.size.x, r.size.y), lit, UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.15))
	for y in [r.position.y, r.end.y - 8.0]:
		var cap := Rect2(r.position.x - 3, y, r.size.x + 6, 8)
		pg.rounded(cap.grow(1), 2.0, UiKit.INK)
		pg.vshade(cap, UiKit.PALE_GOLD, UiKit.BRONZE)

## A red lacquer board framed in gold (a plaque, a tag's back, a title's mount): words on it read on `lacquer`.
static func lacquer(pg: Page, r: Rect2, lit := false, radius := 4.0) -> void:
	pg.rounded(Rect2(r.position + Vector2(0, 3), r.size).grow(1), radius + 1.0, Color(UiKit.INK, 0.45))
	pg.rounded(r.grow(1), radius + 1.0, UiKit.INK)
	pg.rounded(r, radius, UiKit.PALE_GOLD if lit else UiKit.GOLD.lerp(UiKit.BRONZE, 0.5))
	var face := r.grow(-2)
	pg.vshade(face, UiKit.SURFACE.lacquer.lerp(UiKit.RED, 0.12), UiKit.SURFACE.lacquer.lerp(UiKit.INK, 0.2))
	pg.draw_rect(Rect2(face.position + Vector2(2, 1), Vector2(face.size.x - 4, 1)), Color(UiKit.PAPER, 0.18))
	pg.ground(r, UiKit.SURFACE.lacquer.lerp(UiKit.RED, 0.12))

## A hanging title board: a lacquer plaque on two cords from the top of `r`, the title inked on it by Page.
static func title_board(pg: Page, r: Rect2) -> void:
	for x in [r.position.x + 40.0, r.end.x - 40.0]:
		pg.draw_line(Vector2(x, r.position.y - 14), Vector2(x, r.position.y + 4), UiKit.GOLD.lerp(UiKit.BRONZE, 0.4), 2.0, true)
		pg.draw_circle(Vector2(x, r.position.y - 14), 3.0, UiKit.BRONZE, true, -1.0, true)
	lacquer(pg, r, false, 6.0)
	pg.draw_rect(r.grow(-6), Color(UiKit.GOLD, 0.55), false, 1.0)

## Dark timber boards across `r` (a hall's wall, a teaching board): the face with its seams and grain; words on it read
## on `wood_dark`.
static func timber(pg: Page, r: Rect2, pitch := 88.0) -> void:
	PostKit.planks(pg, r, pitch, true, UiKit.SURFACE.wood_dark)
	pg.ground(r, UiKit.SURFACE.wood_dark)

## A figure kept on the page: the live Avatar for `key`, made once with `outfit` at `scale` (whole art pixels: the sheets
## are 2 screen px an art px, so 0.5 draws 1 px an art px and 1.0 draws 2). Show it standing at `feet` with `show`; hide
## the ones not shown this frame with `hide_rest`.
static func figure(pg: Page, figs: Dictionary, key: String, outfit: Dictionary, scale: float) -> Node2D:
	if not figs.has(key):
		var d := Avatar.new()
		d.outfit = DialoguePage.full_outfit(outfit)
		d.scale = Vector2.ONE * scale
		pg.add_child(d)
		d.play("idle")
		figs[key] = d
	return figs[key]

static func show(d: Node2D, feet: Vector2, live: Dictionary, key: String, alpha := 1.0, action := "idle", facing := 1) -> void:
	d.position = feet.round()
	d.visible = alpha > 0.0
	d.modulate = Color(1, 1, 1, alpha)
	d.set("facing", facing)
	d.call("play", action)
	live[key] = true

static func hide_rest(figs: Dictionary, live: Dictionary) -> void:
	for k in figs:
		if not live.has(k): (figs[k] as Node2D).visible = false

## A sect disciple's look (an NPC of your own sect, who has no outfit of its own): the disciple's robe and a hair colour
## and style chosen by their name, so each reads as someone.
static func disciple_outfit(name: String) -> Dictionary:
	var h := absi(hash(name))
	var hairs: Array = ["short_knot", "topknot", "ponytail", "long_tied", "high_pony", "flowing"]
	return {"shirt": "disciple", "hair": hairs[(h / 7) % hairs.size()], "hair_color": h % 6}

static var _small: Dictionary = {}

## `tex` (or its `region`) scaled by `k` once, smoothly, and kept: pixel art shown small (the courtyard's
## buildings and backdrop) keeps its shapes instead of dropping every other pixel. Null when the art has no image.
static func scaled(tex: Texture2D, region: Rect2i, k: float) -> Texture2D:
	if tex == null: return null
	var key := "%s|%s|%.3f" % [tex.resource_path, str(region), k]
	if not _small.has(key):
		var img := tex.get_image()
		if img == null:
			_small[key] = null
			return null
		if img.is_compressed(): img.decompress()
		if region.size.x > 0: img = img.get_region(region)
		# Halving is a box filter (fast); any other scale halves while it can, then blends the rest.
		var w := maxi(1, int(round(img.get_width() * k)))
		var h := maxi(1, int(round(img.get_height() * k)))
		while img.get_width() >= w * 2 and img.get_height() >= h * 2: img.shrink_x2()
		if img.get_width() != w or img.get_height() != h: img.resize(w, h, Image.INTERPOLATE_BILINEAR)
		_small[key] = ImageTexture.create_from_image(img)
	return _small[key]

static var _used: Dictionary = {}

## The part of `tex` its art covers (its opaque bounds), kept: a scaffold stands where the building will.
static func used_rect(tex: Texture2D) -> Rect2:
	if tex == null: return Rect2()
	var key := tex.get_rid().get_id()
	if not _used.has(key):
		var img := tex.get_image()
		_used[key] = Rect2(img.get_used_rect()) if img != null else Rect2()
	return _used[key]
