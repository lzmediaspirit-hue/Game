class_name TopdownFigure
extends RefCounted
## Top-down redesign, Phase 3 (decision 32): the game's real character drawn in the 3/4 view, for the player and the
## villagers alike. It composites the layers the side view's avatar wears (body, shoes, trousers, shirt, cape, hair, hat,
## weapon; parts.json's names, dyes and hair colours) from the sheets tools/art/topdown/build_character.py draws, as
## data/topdown/character.json lays them out: per item, one section per band (back, mid, head, front) with its z,
## and per section one rect [x, y, w, h, ox, oy] per frame, (ox, oy) from the feet. Facings S, SE, E, NE and N are
## drawn; SW, W and NW mirror SE, E and NE. Meditation faces the camera only (its other facings redirect to S).
## The bow and the later weapon families (heavy sabre, fan, flute, brush, bell) have no top-down layer yet: an outfit
## that asks for one lists it in `missing` and draws without it (redesign plan, "As built: Phase 3, third part").

const MANIFEST := "res://data/topdown/character.json"
const CATEGORIES := ["body", "shoes", "pants", "shirt", "cape", "hair", "hat", "weapon"]
const DialoguePage = preload("res://scripts/ui/pages/dialogue_page.gd")

static var _man: Dictionary = {}

var outfit: Dictionary = {}
var layers: Array = []     ## {z, tex, rects: PackedInt32Array, hidden, cat, item}, sorted by z
var missing: Array = []    ## "cat:item" the outfit wears that has no top-down layer

## The manifest, read once; every section's rects as a PackedInt32Array.
static func manifest() -> Dictionary:
	if _man.is_empty():
		var d = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		if d is Dictionary:
			for cat in d.items:
				for name in d.items[cat]:
					for sec in d.items[cat][name].sections: sec.rects = PackedInt32Array(sec.rects)
			_man = d
	return _man

## A figure wearing `o` (an outfit as InventoryAuthority.outfit_for or an NPC's `outfit` gives it).
static func wearing(o: Dictionary) -> TopdownFigure:
	var f := TopdownFigure.new()
	f.set_outfit(o)
	return f

## A villager's figure: the NPC's outfit, its unset pieces as the side view fills them (DialoguePage.full_outfit).
static func for_npc(npc_id: String) -> TopdownFigure:
	return wearing(DialoguePage.full_outfit(ContentDB.entry("npcs", npc_id).get("outfit", {})))

func set_outfit(o: Dictionary) -> void:
	outfit = o.duplicate()
	layers.clear()
	missing.clear()
	var items: Dictionary = manifest().get("items", {})
	for cat in CATEGORIES:
		var name := str(o.get(cat, "none"))
		if name == "none" or name == "": continue
		var item: Dictionary = items.get(cat, {}).get(name, {})
		if item.is_empty():
			missing.append("%s:%s" % [cat, name])
			continue
		var tex: Texture2D = Wardrobe.texture(str(item.sheets[_variant(cat, item.sheets)]))
		for sec in item.sections:
			layers.append({"z": int(sec.z), "tex": tex, "rects": sec.rects, "hidden": sec.hidden, "cat": cat, "item": name})
	layers.sort_custom(func(a, b): return a.z < b.z)

## The sheet an item wears: its hair colour or dye, the undyed original for a dye it was not drawn in (the side view's
## rule, avatar.gd sheet_index).
func _variant(cat: String, sheets: Dictionary) -> String:
	var key := "none"
	if cat == "hair": key = str(clampi(int(outfit.get("hair_color", 0)), 0, maxi(0, sheets.size() - 1)))
	elif cat in ["shirt", "pants"]: key = str(outfit.get(cat + "_dye", "none"))
	if sheets.has(key): return key
	return "none" if sheets.has("none") else str(sheets.keys()[0])

## A side-view action name (a technique's pose, an old strike family) as the top-down action it plays.
static func resolve(action: String) -> String:
	var man := manifest()
	if (man.actions as Dictionary).has(action): return action
	return str((man.aliases as Dictionary).get(action, "idle"))

static func spec(action: String) -> Dictionary:
	var acts: Dictionary = manifest().actions
	return acts.get(resolve(action), acts.idle)

## The drawn frame for `action` in facing `row` at frame `i`: x the frame's index in every section, y 1 when the
## facing mirrors a drawn one.
static func frame_of(action: String, row: String, i: int) -> Vector2i:
	var man := manifest()
	var a := spec(action)
	var mirror: bool = (man.mirror as Dictionary).has(row)
	var drawn := str((man.mirror as Dictionary).get(row, row))
	if a.has("facing"):
		drawn = str(a.facing)
		mirror = false
	if not (a.start as Dictionary).has(drawn): drawn = "s"
	return Vector2i(int(a.start[drawn]) + clampi(i, 0, int(a.frames) - 1), 1 if mirror else 0)

## The frame a strike lands on (the last frame for an action without one).
static func hit_frame(action: String) -> int:
	var a := spec(action)
	return int(a.hit) if int(a.hit) >= 0 else int(a.frames) - 1

## The frame `t` seconds into `action` at its own rate (a loop wraps, a one-shot holds its last frame).
static func frame_at(action: String, t: float) -> int:
	var a := spec(action)
	var i := int(maxf(0.0, t) * float(a.fps))
	return i % int(a.frames) if bool(a.loop) else mini(i, int(a.frames) - 1)

## A strike's frame on Combat's clock: the drawn blow lands on its hit frame the moment the hit does (`hit_at`).
static func strike_frame(action: String, t: float, duration: float, hit_at: float) -> int:
	var a := spec(action)
	var n := int(a.frames)
	var hit := int(a.hit)
	if hit < 0 or hit_at <= 0.0 or duration <= hit_at: return clampi(int(t / maxf(0.01, duration) * n), 0, n - 1)
	if t < hit_at: return clampi(int(t / hit_at * hit), 0, hit - 1)
	return clampi(hit + int((t - hit_at) / (duration - hit_at) * (n - hit)), hit, n - 1)

## Draw the figure with its feet at `feet` on `ci`.
func draw(ci: CanvasItem, feet: Vector2, action: String, row: String, i: int, tint := Color.WHITE) -> void:
	var fm := frame_of(action, row, i)
	var k := fm.x * 6
	ci.draw_set_transform(feet, 0.0, Vector2(-1, 1) if fm.y == 1 else Vector2.ONE)
	for l in layers:
		var r: PackedInt32Array = l.rects
		if r[k + 2] == 0: continue
		ci.draw_texture_rect_region(l.tex, Rect2(r[k + 4], r[k + 5], r[k + 2], r[k + 3]), Rect2(r[k], r[k + 1], r[k + 2], r[k + 3]), tint)
	ci.draw_set_transform(Vector2.ZERO)

## What the figure covers on screen in that frame, from its feet (for occlusion tests and labels).
func bounds(action: String, row: String, i: int) -> Rect2:
	var fm := frame_of(action, row, i)
	var k := fm.x * 6
	var out := Rect2()
	for l in layers:
		var r: PackedInt32Array = l.rects
		if r[k + 2] == 0: continue
		var box := Rect2(r[k + 4], r[k + 5], r[k + 2], r[k + 3])
		if fm.y == 1: box.position.x = -box.end.x
		out = box if out.size == Vector2.ZERO else out.merge(box)
	return out
