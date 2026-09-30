class_name TopdownFx
extends RefCounted
## Decision 38 · the combat's effects in the top-down world: every smear, technique form, impact mark, guard, parry,
## foe's tell and swipe, and every dust puff, played from the ground-plane sheets of data/fx_topdown.json
## (tools/art/fx/build_fx_topdown.py) inside the 640x360 world viewport, at art resolution, sorted with the bodies.
## Only the feel comes from the reference game; the look is wuxia (the sheets' look rule).
##
## Each effect is a node in the world's sorted layer: an upright one (a smear, a pillar, a bolt) keys just in front of
## the body at its anchor (just behind it when it faces away from the camera); a flat one (a ring, a domain) keys at
## its north edge, so every body standing in it draws over it. A sheet is drawn in one of its five drawn directions,
## the west three mirrored, at a whole scale (1 art px = 1 viewport px, or 2 or 3 for a wide technique), its impact
## frame on the blow's hit. Effects freeze during a hit-stop with the fight (`advance` is not called).

const DIR8 := ["e", "se", "s", "sw", "w", "nw", "n", "ne"]
const FACING_AWAY := ["n", "ne", "nw"]
const MAX_NODES := 72

var world                     ## TopdownWorld
var nodes: Array = []         ## the live effect nodes
var pending_smear: Dictionary = {}   ## actor -> its smear node still waiting for its hit (a cancelled blow drops it)
var guard_node: FxSprite = null
var charge_node: FxSprite = null
var bolts: BoltLayer

func _init(w) -> void:
	world = w
	bolts = BoltLayer.new(self)
	w.sorted.add_child(bolts)

static func cfg() -> Dictionary:
	return ContentDB.config("fx_topdown")

static var _white: ShaderMaterial
## A struck body's white flash: one material every flashing body shares, and none on the others, so the bodies still
## batch (the side-view game's flash shader, SpriteCache.flash_material, held at full white).
static func white_material() -> ShaderMaterial:
	if _white == null:
		_white = SpriteCache.new_flash_material()
		_white.set_shader_parameter("flash", 1.0)
	return _white

## The nearest of the eight directions to `v`: [the drawn direction, mirrored?] (W, SW and NW draw E, SE and NE
## mirrored).
static func dir_of(v: Vector2) -> Array:
	if v.length() < 0.01: v = Vector2.DOWN
	var i := posmod(roundi(v.angle() / (PI / 4.0)), 8)
	var d: String = DIR8[i]
	var m: Dictionary = cfg().get("mirror", {"w": "e", "sw": "se", "nw": "ne"})
	return [str(m.get(d, d)), m.has(d)]

static func dir_index(d: String) -> int:
	return maxi(0, (cfg().get("dirs", ["e", "se", "s", "ne", "n"]) as Array).find(d))

## The sheet of a directed or round set of sheets ({dir: sheet} or {"all": sheet}) for direction `d`.
static func sheet_for(sheets: Dictionary, d: String) -> Dictionary:
	return sheets.get(d, sheets.get("all", {})) if sheets != null else {}

## A point on the plane at height z, in the viewport's art px.
static func art(p: Vector2, z: float) -> Vector2:
	return (Vector2(p.x, p.y - z) / TopdownRoom.ART).round()

## The sort key of an effect at `p`, height z: upright ones just in front of a body there (behind it when facing
## away), flat ones at their north edge (`north` art px up).
func key_of(p: Vector2, z: float, flat := false, north := 0.0, away := false) -> float:
	var k: float = world.room.sort_key(p, z)
	if flat: return k - north - 0.02
	return k - 0.03 if away else k + 0.03

## Play frames of `sheet` row `row`. o: at (art px, the anchor), key, flip, scale, fps, frames, delay, start, loop,
## travel (art px over its life), alpha.
func play(sheet: Dictionary, row: int, o: Dictionary) -> FxSprite:
	if sheet.is_empty() or not sheet.has("file"): return null
	var n := FxSprite.new()
	n.tex = SpriteCache.tex(str(sheet.file))
	if n.tex == null: return null
	n.cell = Vector2(float(sheet.cell[0]), float(sheet.cell[1]))
	n.anchor = Vector2(float(sheet.anchor[0]), float(sheet.anchor[1]))
	n.row = row
	n.at = o.get("at", Vector2.ZERO)
	n.flip = bool(o.get("flip", false))
	n.k = float(o.get("scale", 1.0))
	n.fps = float(o.get("fps", 12.0))
	n.frames = int(o.get("frames", 1))
	n.t = -float(o.get("delay", 0.0)) + float(o.get("start", 0.0))
	n.loop = bool(o.get("loop", false))
	n.travel = o.get("travel", Vector2.ZERO)
	n.position = Vector2(0, float(o.get("key", 0.0)))
	n.life = float(o.get("life", float(n.frames) / n.fps))
	world.sorted.add_child(n)
	nodes.append(n)
	# A cap on effects at once (a crowd's blows): the oldest one-shot goes first.
	if nodes.size() > MAX_NODES:
		for old in nodes:
			if is_instance_valid(old) and not old.loop:
				nodes.erase(old)
				old.queue_free()
				break
	return n

## Advance every effect (not during a hit-stop); drop the finished ones.
func advance(delta: float) -> void:
	for n in nodes.duplicate():
		if not is_instance_valid(n):
			nodes.erase(n)
			continue
		n.t += delta
		if not n.loop and n.t >= n.life:
			nodes.erase(n)
			n.queue_free()
		else:
			n.queue_redraw()
	bolts.queue_redraw()

## Stop and drop every effect (a room left behind).
func clear() -> void:
	for n in nodes:
		if is_instance_valid(n): n.queue_free()
	nodes.clear()
	pending_smear.clear()
	guard_node = null
	charge_node = null

## When a sheet's impact frame lands on a hit `windup` seconds away: a delay when the hit is later than the sheet's
## lead, a start part-way in when it is sooner.
static func timing(impact: int, fps: float, windup: float) -> Dictionary:
	if windup < 0.0: return {}
	var lead := windup - float(impact) / fps
	return {"delay": lead} if lead >= 0.0 else {"start": -lead}

# ------------------------------------------------------------------ the family's smears
## A combo step's smear (decision 38): the family's sheet, the move's row in the blow's direction, its contact frame
## on the hit, played at the family's smear rate. move: step_1..3, charged (the dragged finisher), dash, air.
func smear(actor: String, family: String, move: String, aim: Vector2, at: Vector2, z: float, windup: float, speed := 1.0) -> FxSprite:
	var m: Dictionary = cfg().get("melee", {})
	var fam: Dictionary = m.get("families", {}).get(family, m.get("families", {}).get("fists", {}))
	var moves: Array = m.get("moves", [])
	var mi := maxi(0, moves.find(move))
	var dm := dir_of(aim)
	var fps := CombatFeel.smear_fps(family) * speed   # played as fast as the step (its attack speed)
	var o := {"at": art(at, z), "key": key_of(at, z, false, 0.0, str(dm[0]) in FACING_AWAY), "flip": dm[1], "scale": float(fam.get("scale", 1)),
		"fps": fps, "frames": int(m.get("frames", 6))}
	o.merge(timing(int(m.get("impact", 1)), fps, windup))
	var n := play(fam, mi * 5 + dir_index(str(dm[0])), o)
	if n != null and actor != "": pending_smear[actor] = n
	return n

## A blow cancelled before its hit (a dodge out of its anticipation): its smear never plays.
func cancel(actor: String) -> void:
	var n = pending_smear.get(actor)
	pending_smear.erase(actor)
	if n != null and is_instance_valid(n) and n.t < 0.0:
		nodes.erase(n)
		n.queue_free()

# ------------------------------------------------------------------ technique forms
## A technique's form (decision 38: every form redrawn on the ground plane): the sheet of its direction, its element's
## row at its tier's band, anchored at the caster's feet or the target point, scaled by whole steps to the reach, its
## impact frame on the hit; a wave's crest travels along the reach.
func form(t: Dictionary, at: Vector2, z: float, aim: Vector2, target: Vector2, target_z: float, windup: float, reach: float) -> FxSprite:
	var name := str(t.get("vfx", {}).get("anim", t.get("form", "")))
	var a: Dictionary = cfg().get("forms", {}).get(name, {})
	if a.is_empty(): return null
	var dm := dir_of(aim)
	var sheet := sheet_for(a.get("sheets", {}), str(dm[0]))
	var band := FxLayer.band_of(int(t.get("vfx", {}).get("tier", 1)))
	var row := FxLayer.form_row(str(t.get("element", "none")), band)
	var span := float(a.get("span", 32))
	var k := 1.0
	if str(a.get("size", "")) == "reach": k = clampf(roundf(reach / TopdownRoom.ART / span), 1.0, 3.0)
	var on_target := str(a.get("at", "")) == "target"
	var p := target if on_target else at
	var pz := target_z if on_target else z
	var flat := str(a.get("layer", "")) == "floor"
	var o := {"at": art(p, pz), "key": key_of(p, pz, flat, span * k, str(dm[0]) in FACING_AWAY), "flip": dm[1], "scale": k,
		"fps": float(a.fps), "frames": int(a.frames)}
	if str(a.get("size", "")) == "travel":
		var d := aim.normalized() if aim.length() > 0.01 else Vector2.RIGHT
		o.travel = (d * maxf(0.0, reach / TopdownRoom.ART - span * k)).round()
	o.merge(timing(int(a.impact), float(a.fps), windup))
	return play(sheet, row, o)

# ------------------------------------------------------------------ impacts, marks, dust
## A blow's mark where it landed: the impact sheet of the blow's direction (attacker to target), its weight's rows and
## the element's colours.
func impact(at: Vector2, z: float, dir: Vector2, weight: String, element: String) -> FxSprite:
	var im: Dictionary = cfg().get("impact", {})
	var dm := dir_of(dir)
	var wi := maxi(0, (im.get("weights", ["light", "heavy", "finisher"]) as Array).find(str(CombatFeel.weight(weight).get("impact", "light"))))
	var row := wi * (cfg().get("elements", []) as Array).size() + FxLayer.form_row(element, 0)
	return play(sheet_for(im.get("sheets", {}), str(dm[0])), row, {"at": art(at, z), "key": key_of(at, z) + 0.01, "flip": dm[1],
		"fps": float(im.get("fps", 20)), "frames": int(im.get("frames", 6))})

## One of the shared marks (guard, parry, swipe, plunge, charge, tell) at `at`, facing `dir`.
func mark(name: String, at: Vector2, z: float, dir := Vector2.DOWN, delay := 0.0) -> FxSprite:
	var c: Dictionary = cfg().get("common", {})
	var mk: Dictionary = c.get("marks", {}).get(name, {})
	if mk.is_empty(): return null
	var dm := dir_of(dir)
	var row := int(mk.row) + (dir_index(str(dm[0])) if mk.get("dirs", false) else 0)
	var flat := name == "plunge"
	return play(c, row, {"at": art(at, z), "key": key_of(at, z, flat, 30.0 if flat else 0.0, str(dm[0]) in FACING_AWAY), "flip": dm[1] and mk.get("dirs", false),
		"fps": float(mk.fps), "frames": int(mk.frames), "loop": bool(mk.get("loop", false)), "delay": delay})

## Dust on the floor: a dash's kick-off, a skid behind a knocked body, a landing, a step.
func dust(kind: String, at: Vector2, z: float, dir := Vector2.DOWN) -> FxSprite:
	var d: Dictionary = cfg().get("dust", {})
	var kd: Dictionary = d.get("kinds", {}).get(kind, {})
	if kd.is_empty(): return null
	var dm := dir_of(dir)
	var row := int(kd.row) + (dir_index(str(dm[0])) if kd.get("dirs", false) else 0)
	return play(d, row, {"at": art(at, z), "key": key_of(at, z, true, 8.0), "flip": dm[1] and kd.get("dirs", false),
		"fps": float(d.get("fps", 16)), "frames": int(d.get("frames", 6))})

## Decision 45: a story art's effect (data/fx_topdown.json `story`, tools/art/fx/story_arts.py): the first boss's
## awakening (the river boiling) and the elders' arts (Granny Liu's talisman array, Old Ma's palm of force, Lu's water
## dragon), anchored on the floor at `at` (world units), at a whole scale; a flat one (an array on the ground) under the
## bodies standing in it, an upright one (a dragon, a palm) in front of the body there.
func story(name: String, at: Vector2, k := 1.0, flip := false) -> FxSprite:
	var s: Dictionary = cfg().get("story", {}).get("arts", {}).get(name, {})
	if s.is_empty() or world.room == null: return null
	var h: float = world.room.height_at(at)
	var z := h if h < INF else 0.0
	var flat := str(s.get("layer", "")) == "floor"
	var scale := maxf(1.0, roundf(k))
	return play(s.get("sheet", {}), 0, {"at": art(at, z), "key": key_of(at, z, flat, float(s.get("north", 40)) * scale),
		"scale": scale, "fps": float(s.get("fps", 12)), "frames": int(s.get("frames", 1)), "flip": flip})

## A looping mark held while a state lasts (the guard, the charge of a dragged finisher): shown at `at` facing `dir`
## while `on`, following the body; dropped when it ends.
func hold(which: String, on: bool, at: Vector2, z: float, dir: Vector2) -> void:
	var n: FxSprite = guard_node if which == "guard" else charge_node
	if not on:
		if n != null and is_instance_valid(n):
			nodes.erase(n)
			n.queue_free()
		n = null
	else:
		var dm := dir_of(dir)
		if n == null or not is_instance_valid(n) or n.flip != bool(dm[1]) or n.get_meta("dir", "") != str(dm[0]):
			if n != null and is_instance_valid(n):
				nodes.erase(n)
				n.queue_free()
			n = mark(which, at, z, dir)
			if n != null: n.set_meta("dir", str(dm[0]))
		if n != null:
			n.at = art(at, z)
			n.position.y = key_of(at, z, false, 0.0, str(dm[0]) in FACING_AWAY)
	if which == "guard": guard_node = n
	else: charge_node = n

## One effect: a sheet's row played frame by frame at `at` (the anchor, art px), mirrored by `flip`, scaled by `k`,
## sorted at its key (position.y) and drawn back to its screen row.
class FxSprite extends Node2D:
	var tex: Texture2D
	var cell := Vector2.ONE
	var anchor := Vector2.ZERO
	var row := 0
	var at := Vector2.ZERO
	var flip := false
	var k := 1.0
	var fps := 12.0
	var frames := 1
	var t := 0.0
	var life := 1.0
	var loop := false
	var travel := Vector2.ZERO
	func _init() -> void:
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func frame() -> int:
		var f := int(maxf(0.0, t) * fps)
		return f % frames if loop else mini(f, frames - 1)
	func _draw() -> void:
		if t < 0.0 or tex == null: return
		var along := travel * clampf(t / maxf(life, 0.001), 0.0, 1.0)
		draw_set_transform((at + along.round()) - position, 0.0, Vector2(-k if flip else k, k))
		draw_texture_rect_region(tex, Rect2(-anchor, cell), Rect2(Vector2(frame() * cell.x, row * cell.y), cell))
		draw_set_transform(Vector2.ZERO)

## The techniques' thrown forms in flight (arc, volley, seeker, return): each projectile of a technique drawn as its
## form's bolt loop, in its direction of flight, at the thrower's feet on the plane; drawn over the room, as a shot in
## the air is.
class BoltLayer extends Node2D:
	var fx
	func _init(owner) -> void:
		fx = owner
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		position = Vector2(0, 1.0e5)
	func _draw() -> void:
		if Game.room_rt == null: return
		for p in Game.room_rt.projectiles:
			if float(p.get("delay", 0.0)) > 0.0 or not p.has("aim") or not str(p.get("art", "")).begins_with("qi_") or not p.has("technique"): continue
			var t := ContentDB.entry("techniques", str(p.technique))
			var b: Dictionary = TopdownFx.cfg().get("forms", {}).get(str(t.get("vfx", {}).get("anim", "")), {}).get("bolt", {})
			if b.is_empty(): continue
			var dm := TopdownFx.dir_of(p.aim)
			var sheet := TopdownFx.sheet_for(b.get("sheets", {}), str(dm[0]))
			var tex := SpriteCache.tex(str(sheet.get("file", "")))
			if tex == null: continue
			var cell := Vector2(float(sheet.cell[0]), float(sheet.cell[1]))
			var anchor := Vector2(float(sheet.anchor[0]), float(sheet.anchor[1]))
			var band := FxLayer.band_of(int(t.get("vfx", {}).get("tier", 1)))
			var row := FxLayer.form_row(str(p.get("element", t.get("element", "none"))), band)
			var f := int(float(p.get("travelled", 0.0)) / 24.0) % int(b.frames)
			draw_set_transform(TopdownFx.art(Vector2(float(p.x), float(p.y)), float(p.get("feet", 0.0))) - position, 0.0, Vector2(-1 if dm[1] else 1, 1))
			draw_texture_rect_region(tex, Rect2(-anchor, cell), Rect2(Vector2(f * cell.x, row * cell.y), cell))
		draw_set_transform(Vector2.ZERO)
