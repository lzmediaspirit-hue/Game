class_name FoeSheets
extends RefCounted
## The creatures' drawings away from the room (S12b): a page's or the HUD's creature (the bestiary, the pets, the beast
## pages, a bounty's target, a pet's party chip) is its species' top-down sheet (decision 43: art/topdown/foes/, indexed
## by data/topdown/foes.json, built by tools/art/topdown/build_foes.py), the sheet the room draws it with. The side
## view's creature sheets (art/creatures, CreatureSprite) went with it in S12b.

## Pages show a creature three-quarters toward the camera, as the room's foes stand when they idle.
const PAGE_ROW := "se"

## A species' look in the index ({} when it has no top-down sheet): its atlas, cell, feet, height and actions.
static func look(species: String) -> Dictionary:
	return TopdownRoom.foes().get("species", {}).get(species, {})

static func has_sheet(species: String) -> bool:
	return not look(species).is_empty()

## The sheet a species is drawn from ("" when it has none).
static func atlas(species: String) -> String:
	return str(look(species).get("atlas", ""))

## The cell of `action`'s frame at `t` seconds in facing `row` (the index's mirrored rows drawn from their pair), and
## whether that row is mirrored.
static func frame(species: String, action: String, row: String, t: float) -> Dictionary:
	var sh := TopdownRoom.foes()
	var lk := look(species)
	var acts: Dictionary = lk.get("actions", {})
	var a: Dictionary = acts.get(action, acts.get("idle", {}))
	var mirror: Dictionary = sh.get("mirror", {})
	var list: Array = a.get("frames", {}).get(str(mirror.get(row, row)), [[0, 0]])
	var i := int(t * float(a.get("fps", 6)))
	var at: Array = list[i % list.size() if a.get("loop", true) else mini(i, list.size() - 1)]
	var c: Array = lk.get("cell", [48, 40])
	return {"src": Rect2(float(at[0]), float(at[1]), float(c[0]), float(c[1])), "flip": mirror.has(row)}

## The part of its cell a creature stands in, from the index alone (no sheet read back): as tall as its idle figure
## rises over its feet (`top`), as wide as the cell either side of its feet, so its feet sit in the middle.
static func figure_box(species: String) -> Rect2:
	var lk := look(species)
	var c: Array = lk.get("cell", [48, 40])
	var f: Array = lk.get("foot", [24, 27])
	var top := float(lk.get("top", f[1]))
	var half := maxf(float(f[0]), float(c[0]) - float(f[0]))
	return Rect2(float(f[0]) - half, float(f[1]) - top, half * 2.0, top)

## One frame of a creature fitted into `rect`, its feet on the rect's bottom edge, `action` animated by `t`, facing
## `row`. True while its sheet loads (the slot waits); false when the creature has no top-down sheet.
static func draw(ci: CanvasItem, rect: Rect2, species: String, action := "idle", t := 0.0, modulate := Color.WHITE, row := PAGE_ROW) -> bool:
	var path := atlas(species)
	if path == "": return false
	var texture: Texture2D = SpriteCache.tex_sliced(path)
	if texture == null: return SpriteCache.loading(path)   # still loading: keep the slot empty
	var f := frame(species, action, row, t)
	var src: Rect2 = f.src
	var used := figure_box(species)
	var s := minf(rect.size.x / maxf(1.0, used.size.x), rect.size.y / maxf(1.0, used.size.y))
	s = floorf(s * 2.0) / 2.0 if s >= 1.0 else s
	var mid := used.position.x + used.size.x * 0.5   # the feet's column
	if f.flip: mid = src.size.x - mid
	var origin := (Vector2(rect.get_center().x - mid * s, rect.end.y - used.end.y * s)).round()
	if f.flip:
		ci.draw_set_transform(Vector2(origin.x + src.size.x * s, origin.y), 0.0, Vector2(-1, 1))
		ci.draw_texture_rect_region(texture, Rect2(Vector2.ZERO, src.size * s), src, modulate)
		ci.draw_set_transform(Vector2.ZERO)
	else:
		ci.draw_texture_rect_region(texture, Rect2(origin, src.size * s), src, modulate)
	return true
