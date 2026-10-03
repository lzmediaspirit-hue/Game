class_name HazardView
extends Node2D
## S17 · The room's hazards, drawn from RoomRuntime state in their Part 9 states: a quiet tell,
## a warning (a broken amber border and a "!" mark, so it reads without colour), the active
## blow and the cooldown. Presentation only: nothing here changes game state.
##
## What it draws comes in three kinds, and each view puts them where they belong:
##   - the screen's washes and weather (rain, fog, snow, a gust's lines, a storm's flash, the chill, the Presence's dark
##     edges) and the warning marks: on `air`, over the room and under the HUD (the side view's own layer; on the
##     top-down overlay under the names, the aim and the effects);
##   - parts lying flat on the ground at a spot (a strike's ring, a scorch, rubble, a pool, a current, a shelter's warm
##     ring, a boss's blast ring);
##   - parts standing up from a spot (a falling rock, a bolt, springing spikes, a dust cloud).
## The side view draws the flat parts on `ground` (under everyone) and the upright ones on `air`. The top-down view
## (redesign Phase 4) sorts each part with the room in its pixel viewport (`sorted_layer`): a flat part just over the
## floor it lies on and under whoever stands on it (TopdownRoom.decal_key), an upright one at its spot's own key, so a
## wall or a terrace in front hides it and a body in front stands over it. There the ground is seen whole, so a ring
## is drawn as the circle it strikes (`squash`), where the side view flattens it into its strip.

const AMBER := Color("e8a33c")
const DUST := Color("b39a78")
const GRIT := Color("8a6f52")
const ROCK := [Color("3a3530"), Color("6b6159"), Color("958a7c"), Color("c2b6a3")]
const BOLT := Color("f4f7ff")
const GLOW := Color("8fd6ff")
const SNOW := Color("eef4fa")
const FROST := Color("bcd8ee")
const HOLLOW_GREY := Color("a3aab0")
const GAS := Color("b7c95a")

var world
var ground := Node2D.new()   # on the ground, under everyone standing in it
var air := Node2D.new()      # over the room
var t := 0.0
var impacts: Array = []      # {kind, pos (lifted), p (on the plane), z, t, dur}: dust, rubble and scorch left behind
var last_phase: Dictionary = {}
## Redesign Phase 4, set by the top-down view before it adds this: its room and the Y-sorted layer of its pixel
## viewport, where each part tied to a spot is one node (`pieces`) at its sort key.
var room: TopdownRoom = null
var sorted_layer: Node2D = null
var pieces: Array = []
## A ring's depth for its width: the side view's walk strip flattens rings on the ground to 0.42 of their width (and
## the rest to their own shares); the top-down plane is seen whole, so they are drawn round (1 / 0.42).
var squash := 1.0

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ground.z_as_relative = false
	ground.z_index = -1850
	air.z_as_relative = false
	air.z_index = 3900
	if sorted_layer != null:
		ground.visible = false   # its parts sort in the viewport
		air.z_index = WorldLabels.LABEL_Z - 150   # over the room, under the names, the aim, the effects and the HUD
		squash = 1.0 / 0.42
	add_child(ground)
	add_child(air)
	ground.draw.connect(_draw_ground)
	air.draw.connect(_draw_air)

func _exit_tree() -> void:
	for pc in pieces:
		if is_instance_valid(pc): pc.queue_free()
	pieces.clear()

## A ring's depth: `k` of its width `r` in the side view's strip, the whole circle on the top-down plane.
func _ry(r: float, k: float) -> float:
	return r * minf(1.0, k * squash)

func _process(delta: float) -> void:
	t += delta
	var rt: RoomRuntime = Game.room_rt
	if rt == null: return
	for hid in rt.hazards:
		var hs: Dictionary = rt.hazards[hid]
		if str(last_phase.get(hid, "")) != str(hs.phase):
			var was := str(last_phase.get(hid, ""))
			last_phase[hid] = str(hs.phase)
			_on_phase(str(hid), hs, was)
	_track_tribulation(delta)
	for i in range(impacts.size() - 1, -1, -1):
		impacts[i].t = float(impacts[i].t) + delta
		if float(impacts[i].t) >= float(impacts[i].dur): impacts.remove_at(i)
	# A room without hazards draws only while a tribulation is under way (or its scorch marks fade).
	var busy := not rt.hazards.is_empty() or not impacts.is_empty() or not _trib_state().is_empty() or _detonating(rt)
	if busy or drawn:
		ground.queue_redraw()
		air.queue_redraw()
		if sorted_layer != null: _place_pieces(rt)
	drawn = busy

## Sounds and after-effects at the moment a hazard turns.
func _on_phase(hid: String, hs: Dictionary, was: String) -> void:
	var h := ContentDB.entry("hazards", hid)
	var phase := str(hs.phase)
	if phase == "active" and was != "active":
		match hid:
			"wind_gust": Audio.play("gust")
			"current": Audio.play("surge")
			"fog": pass
			"cold": Audio.play("frost")
			"poison_mist": Audio.play("hiss")
			"sandstorm": Audio.play("gust")
			"quicksand": Audio.play("surge")
			"star_wind": Audio.play("gust")
			"deep_water": Audio.play("surge")
			"presence": Audio.play("frost")
	if str(h.get("kind", "")) == "strike" and phase == "cooldown" and was == "active":
		for sp in hs.spots:
			var p := Vector2(float(sp[0]), float(sp[1]))
			var z := float(sp[2])
			if hid == "falling_rocks":
				_impact("dust", p, z, 0.7)
				_impact("rubble", p, z, 2.6)
				Audio.play("rockfall")
			elif hid == "spike_traps":
				_impact("spikes", p, z, 0.9)
				Audio.play("break")
			else:
				_impact("scorch", p, z, 3.0)
				Audio.play("thunder")
		if world and _near_player(hs.spots, 260.0): world.add_shake(0.2)

## Something a blow left at a spot (on the plane at height z) for `dur` seconds.
func _impact(kind: String, p: Vector2, z: float, dur: float) -> void:
	impacts.append({"kind": kind, "pos": Vector2(p.x, p.y - z), "p": p, "z": z, "t": 0.0, "dur": dur})

# ------------------------------------------------------------------ S48 heavenly tribulation
var trib_strike := {}     # the last bolt's flash: {x, y, t}
var drawn := false        # something was drawn last frame (so a quiet room clears once)

## A bolt's ring closes for a second, then the flash, drawn with the lightning hazard's art (Progression owns the rite).
func _trib_state() -> Dictionary:
	var c = Game.active()
	if c == null: return {}
	var tv: Dictionary = Game.progression.tribulation_view(c.id)
	if not tv.is_empty() and not (tv.warn as Dictionary).is_empty():
		var w: Dictionary = tv.warn
		return {"phase": "warn", "t": float(tv.warn_s) - float(w.left), "dur": float(tv.warn_s), "spots": [_trib_spot(float(w.x), float(w.y))], "radius": float(tv.radius)}
	if not trib_strike.is_empty() and float(trib_strike.t) < 0.35:
		return {"phase": "active", "t": float(trib_strike.t), "dur": 0.35, "spots": [_trib_spot(float(trib_strike.x), float(trib_strike.y))], "radius": 80.0}
	return {}

## A bolt's spot [x, y, height]: on the ground in the side view, on the grid's floor there.
func _trib_spot(x: float, y: float) -> Array:
	return [x, y, room.floor_at(Vector2(x, y)) if room != null else 0.0]

func _track_tribulation(delta: float) -> void:
	var c = Game.active()
	if not trib_strike.is_empty(): trib_strike.t = float(trib_strike.t) + delta
	if c == null: return
	var tv: Dictionary = Game.progression.tribulation_view(c.id)
	var warn: Dictionary = tv.get("warn", {})
	# The ring vanished this frame: the bolt fell where it was.
	if warn.is_empty() and last_phase.has("_trib") and not (last_phase._trib as Dictionary).is_empty():
		var w0: Dictionary = last_phase._trib
		trib_strike = {"x": float(w0.x), "y": float(w0.y), "t": 0.0}
		var sp := _trib_spot(float(w0.x), float(w0.y))
		_impact("scorch", Vector2(float(w0.x), float(w0.y)), float(sp[2]), 3.0)
		if world: world.add_shake(0.35)
	last_phase["_trib"] = warn.duplicate()

func _detonating(rt: RoomRuntime) -> bool:
	for e in rt.living_enemies():
		if str(e.ai.get("state", "")) == "detonating": return true
	return false

func _near_player(spots: Array, r: float) -> bool:
	if world == null or world.player == null: return false
	for sp in spots:
		if world.player.plane.distance_to(Vector2(float(sp[0]), float(sp[1]))) <= r: return true
	return false

# ------------------------------------------------------------------ helpers
func _view() -> Rect2:
	var c: Vector2 = world.screen_center() if world and world.camera else Vector2(640, 600)
	return Rect2(c - Vector2(640, 360), Vector2(1280, 720))

static func _px(ci: CanvasItem, p: Vector2, s: float, c: Color) -> void:
	ci.draw_rect(Rect2(p.snapped(Vector2(2, 2)), Vector2(s, s)), c)

static func _ellipse(ci: CanvasItem, center: Vector2, rx: float, ry: float, c: Color) -> void:
	ci.draw_set_transform(center, 0.0, Vector2(1.0, ry / maxf(1.0, rx)))
	ci.draw_circle(Vector2.ZERO, rx, c)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

## A broken border: the hostile-area pattern (Part 9) that reads without colour.
static func _dashed(ci: CanvasItem, center: Vector2, rx: float, ry: float, c: Color, spin := 0.0, dashes := 14, width := 2.0, ink := false) -> void:
	for i in dashes:
		var a0 := spin + TAU * i / dashes
		var a1 := a0 + TAU / dashes * 0.55
		var pts := PackedVector2Array()
		for k in 5:
			var a := lerpf(a0, a1, k / 4.0)
			pts.append((center + Vector2(cos(a) * rx, sin(a) * ry)).snapped(Vector2(2, 2)))
		if ink: ci.draw_polyline(pts, Color(UiKit.INK, c.a * 0.7), width + 3.0)
		ci.draw_polyline(pts, c, width)

## The warning mark: an amber diamond with "!".
static func _mark(ci: CanvasItem, p: Vector2, a: float) -> void:
	p = p.snapped(Vector2(2, 2))
	var d := PackedVector2Array([p + Vector2(0, -13), p + Vector2(13, 0), p + Vector2(0, 13), p + Vector2(-13, 0)])
	ci.draw_colored_polygon(PackedVector2Array([d[0] + Vector2(0, -2), d[1] + Vector2(2, 0), d[2] + Vector2(0, 2), d[3] + Vector2(-2, 0)]), Color(UiKit.INK, a))
	ci.draw_colored_polygon(d, Color(AMBER, a))
	ci.draw_rect(Rect2(p + Vector2(-2, -8), Vector2(4, 10)), Color(UiKit.INK, a))
	ci.draw_rect(Rect2(p + Vector2(-2, 4), Vector2(4, 4)), Color(UiKit.INK, a))

static func _chevrons(ci: CanvasItem, p: Vector2, dir: int, a: float) -> void:
	for k in 3:
		var x := p.x + dir * k * 14.0
		var pts := PackedVector2Array([Vector2(x - dir * 6, p.y - 10), Vector2(x + dir * 4, p.y), Vector2(x - dir * 6, p.y + 10)])
		ci.draw_polyline(pts, Color(UiKit.INK, a * 0.8), 6.0)
		ci.draw_polyline(pts, Color(AMBER, a), 3.0)

static func _phase_k(hs: Dictionary) -> float:
	return clampf(float(hs.t) / maxf(0.001, float(hs.dur)), 0.0, 1.0)

func _player_pos() -> Vector2:
	return world.feet() if world and world.player else Vector2.ZERO

# ------------------------------------------------------------------ the parts tied to a spot
## Every part of the room's hazards tied to a spot on the ground, in the order the side view draws them: {kind, p (on
## the plane), z (the floor under it), flat (lies on the floor, else stands up from it), half (a flat part's depth in
## world units), side ("ground" or "air": the side view's layer), mark (a warning mark: always on `air`)} and what it
## draws (the hazard, its phase state, the spot or area, the impact).
func parts(rt: RoomRuntime) -> Array:
	var out: Array = []
	var add := func(kind: String, p: Vector2, z: float, flat: bool, half: float, side: String, extra: Dictionary) -> void:
		var part := {"kind": kind, "p": p, "z": z, "flat": flat, "half": half, "side": side, "mark": kind == "mark"}
		part.merge(extra)
		out.append(part)
	for im in impacts:
		var flat: bool = str(im.kind) in ["rubble", "scorch"]
		add.call("impact", im.p, float(im.z), flat, 20.0, "air" if im.kind == "dust" else "ground", {"im": im})
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		match str(h.get("kind", "")):
			"strike":
				var r := float(h.get("radius", 60))
				for sp in hs.spots:
					var p := Vector2(float(sp[0]), float(sp[1]))
					add.call("strike", p, float(sp[2]), true, _ry(r, 0.42), "ground", {"hid": str(hid), "h": h, "hs": hs, "sp": sp})
					if hid == "spike_traps" and hs.phase == "active": add.call("spikes", p, float(sp[2]), false, 0.0, "ground", {"hs": hs, "sp": sp, "r": r})
			"flow", "pool":
				var areas := HazardRules.areas(h, rt.def)
				for ai in areas.size():
					var c := HazardRules.rect(areas[ai]).get_center()
					add.call(str(h.kind), c, _floor(c), true, HazardRules.rect(areas[ai]).size.y * 0.5, "ground", {"hid": str(hid), "h": h, "hs": hs, "a": areas[ai], "ai": ai})
			"aura":
				if hid == "cold" and hs.phase in ["warn", "active"]:
					for o in rt.def.get("objects", []):
						if not str(o.get("type", "")) in h.get("shelter", []): continue
						var at := Vector2(float(o.at[0]), float(o.at[1]))
						add.call("shelter", at, _floor(at), true, _ry(_shelter_r(), 0.4), "ground", {})
	var ts := _trib_state()
	if not ts.is_empty():
		var sp0: Array = ts.spots[0]
		var tp := Vector2(float(sp0[0]), float(sp0[1]))
		add.call("strike", tp, float(sp0[2]), true, _ry(float(ts.radius), 0.42), "ground", {"hid": "lightning", "h": {"radius": float(ts.radius)}, "hs": ts, "sp": sp0})
	# S48: a boss burning its nascent soul shows the ring of the coming blast.
	for e in rt.living_enemies():
		if str(e.ai.get("state", "")) != "detonating": continue
		var rad := float(e.ai.get("detonation", {}).get("radius", 280))
		add.call("detonation", e.plane, _floor(e.plane), true, _ry(rad, 0.42), "ground", {"rad": rad})
	# Standing up from the ground (the side view's air layer), and the warning marks over their spots.
	if not ts.is_empty(): add.call("bolt", Vector2(float(ts.spots[0][0]), float(ts.spots[0][1])), float(ts.spots[0][2]), false, 0.0, "air", {"hs": ts, "sp": ts.spots[0]})
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		for si in (hs.spots as Array).size():
			var sp: Array = hs.spots[si]
			var p := Vector2(float(sp[0]), float(sp[1]))
			match str(hid):
				"falling_rocks": add.call("rock", p, float(sp[2]), false, 0.0, "air", {"hs": hs, "sp": sp, "si": si})
				"lightning": add.call("bolt", p, float(sp[2]), false, 0.0, "air", {"hs": hs, "sp": sp})
			if hs.phase == "warn" and str(hid) in ["falling_rocks", "lightning", "spike_traps"]:
				add.call("mark", p, float(sp[2]), false, 0.0, "air", {"hid": str(hid), "at": Vector2(p.x, p.y - float(sp[2])) + Vector2(0, -128)})
		if str(h.get("kind", "")) == "pool" and hs.phase == "warn":
			for a in HazardRules.areas(h, rt.def):
				var c := HazardRules.rect(a).get_center()
				add.call("mark", c, _floor(c), false, 0.0, "air", {"at": Vector2(c.x, c.y - _floor(c)) + Vector2(0, -96)})
	if ts.get("phase", "") == "warn":
		var sp1: Array = ts.spots[0]
		add.call("mark", Vector2(float(sp1[0]), float(sp1[1])), float(sp1[2]), false, 0.0, "air", {"hid": "lightning", "at": Vector2(float(sp1[0]), float(sp1[1]) - float(sp1[2])) + Vector2(0, -128)})
	return out

## The floor under a point: the ground in the side view, the grid's floor on the height grid.
func _floor(p: Vector2) -> float:
	return room.floor_at(p) if room != null else 0.0

func _shelter_r() -> float:
	return float(ContentDB.stat_const("hazard.shelter_radius", 220))

## Draw one part on `ci` (world units, y lifted by height).
func _draw_part(ci: CanvasItem, part: Dictionary) -> void:
	match str(part.kind):
		"impact": _draw_impact(ci, part.im)
		"strike": _ground_strike(ci, str(part.hid), part.h, part.hs, part.sp)
		"spikes":
			var sp: Array = part.sp
			_spikes(ci, Vector2(float(sp[0]), float(sp[1]) - float(sp[2])), float(part.r), minf(1.0, _phase_k(part.hs) * 3.0))
		"flow": _ground_flow(ci, part.h, part.hs, part.a)
		"pool": _ground_pool(ci, str(part.hid), part.hs, part.a, int(part.ai))
		"shelter":
			var at := Vector2(part.p.x, part.p.y - float(part.z))
			_dashed(ci, at, _shelter_r(), _ry(_shelter_r(), 0.4), Color(UiKit.PALE_GOLD, 0.55), t * 0.6, 20)
		"detonation":
			var c := Vector2(part.p.x, part.p.y - float(part.z))
			var rad := float(part.rad)
			var pulse := 0.6 + 0.4 * sin(t * 12.0)
			_ellipse(ci, c, rad, _ry(rad, 0.42), Color(0.35, 0.05, 0.1, 0.22))
			_dashed(ci, c, rad, _ry(rad, 0.42), Color(AMBER, pulse), t * 3.0, 18, 3.0, true)
		"rock": _rock_spot(ci, part.hs, part.sp, int(part.si))
		"bolt": _bolt_spot(ci, part.hs, part.sp, _view())
		"mark": _mark(ci, part.at, 0.7 + 0.3 * sin(t * (14.0 if str(part.get("hid", "")) == "lightning" else 12.0)))

# ------------------------------------------------------------------ the top-down view: parts sorted with the room
## One part in the top-down view's pixel viewport: a node at its sort key (x on the spot's art px) holding a canvas at
## half scale placed back so it draws in world units, as the side view's layers do.
class Piece extends Node2D:
	var view
	var part: Dictionary = {}
	var paint := Node2D.new()
	func _init(v) -> void:
		view = v
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		paint.scale = Vector2(0.5, 0.5)
		paint.draw.connect(func(): view._draw_part(paint, part))
		add_child(paint)
	func show_part(p: Dictionary, key: float) -> void:
		part = p
		position = Vector2(roundf(float(p.p.x) / TopdownRoom.ART), key)
		paint.position = -position
		visible = true
		paint.queue_redraw()

## Sort this frame's parts into the viewport (the marks stay on the overlay): a flat part just over the floor it lies
## on (TopdownRoom.decal_key, its depth as the mark's), an upright one at its spot's key. Nodes are kept and reused.
func _place_pieces(rt: RoomRuntime) -> void:
	var list := parts(rt).filter(func(pt): return not pt.mark)
	while pieces.size() < list.size():
		var pc := Piece.new(self)
		sorted_layer.add_child(pc)
		pieces.append(pc)
	for i in pieces.size():
		var pc: Piece = pieces[i]
		if i >= list.size():
			pc.visible = false
			continue
		var pt: Dictionary = list[i]
		var key := room.decal_key(pt.p, float(pt.z), float(pt.half) / TopdownRoom.ART) if pt.flat else room.sort_key(pt.p, float(pt.z))
		pc.show_part(pt, key)

# ------------------------------------------------------------------ ground layer (the side view)
func _draw_ground() -> void:
	var rt: RoomRuntime = Game.room_rt
	if rt == null or sorted_layer != null: return
	for part in parts(rt):
		if part.side == "ground": _draw_part(ground, part)

## What a blow left behind: dust rising, rubble, spikes sinking back, a scorch.
func _draw_impact(ci: CanvasItem, im: Dictionary) -> void:
	var k := float(im.t) / float(im.dur)
	match str(im.kind):
		"rubble":
			for i in 7:
				_px(ci, im.pos + Vector2((HashNoise.scatter(i, 3) - 0.5) * 70, (HashNoise.scatter(i, 4) - 0.5) * _ry(22.0, 1.0)), 4 + 2 * int(HashNoise.scatter(i, 5) * 2), Color(ROCK[1 + i % 3], 1.0 - k))
		"spikes":
			_spikes(ci, im.pos, 52.0, 1.0 - k)
		"scorch":
			_ellipse(ci, im.pos, 34, _ry(34.0, 12.0 / 34.0), Color(0.08, 0.06, 0.05, 0.55 * (1.0 - k)))
			for i in 5:
				if HashNoise.scatter(i + int(t * 6), 7) < 0.5: _px(ci, im.pos + Vector2((HashNoise.scatter(i, 8) - 0.5) * 50, (HashNoise.scatter(i, 9) - 0.5) * _ry(14.0, 1.0)), 2, Color(AMBER, 1.0 - k))
		"dust":
			for i in 6:
				var ang := TAU * i / 6.0 + 0.4
				var p: Vector2 = im.pos + Vector2(cos(ang) * 50.0 * k, -absf(sin(ang)) * 24.0 * k - 6.0)
				ci.draw_circle(p.snapped(Vector2(2, 2)), 8.0 + 10.0 * k, Color(DUST, 0.7 * (1.0 - k)))

func _ground_strike(ci: CanvasItem, hid: String, h: Dictionary, hs: Dictionary, sp: Array) -> void:
	var r := float(h.get("radius", 60))
	var k := _phase_k(hs)
	var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
	match str(hs.phase):
		"tell":
			if hid == "falling_rocks": _ellipse(ci, at, r * 0.5, _ry(r, 0.2), Color(0, 0, 0, 0.12 * k))
			if hid == "spike_traps":
				# Grit shivers over the pressure plate.
				for i in 8:
					var j := Vector2((HashNoise.scatter(i, 121) - 0.5) * r * 1.4, (HashNoise.scatter(i, 122) - 0.5) * _ry(r, 0.5))
					_px(ci, at + j + Vector2(0, -2.0 * float(int(t * 18.0 + i) % 2)), 2, Color(GRIT, 0.8 * k))
		"warn":
			var pulse := 0.65 + 0.35 * sin(t * 14.0)
			_ellipse(ci, at, r * (0.45 + 0.55 * k), _ry(r, 0.42) * (0.45 + 0.55 * k), Color(0.05, 0.03, 0.02, 0.18 + 0.2 * k))
			_dashed(ci, at, r, _ry(r, 0.42), Color(AMBER, pulse), t * (2.0 if hid == "falling_rocks" else -3.0), 14, 3.0, true)
			if hid == "lightning":
				for i in 6:
					if HashNoise.scatter(i + int(t * 20), 11) < 0.4:
						_px(ci, at + Vector2((HashNoise.scatter(i, 12) - 0.5) * r * 1.6, (HashNoise.scatter(i, 13) - 0.5) * _ry(r, 0.6)), 2, GLOW)
		"active":
			_ellipse(ci, at, r, _ry(r, 0.42), Color(0.05, 0.03, 0.02, 0.4))

## Bronze spikes springing from the floor, `rise` 0..1 of their height.
func _spikes(ci: CanvasItem, at: Vector2, r: float, rise: float) -> void:
	if rise <= 0.0: return
	for i in 9:
		var p := at + Vector2((float(i % 3) - 1.0) * r * 0.55 + (HashNoise.scatter(i, 131) - 0.5) * 8.0, (float(i / 3) - 1.0) * _ry(r, 0.22))
		var ht := (22.0 + 10.0 * HashNoise.scatter(i, 132)) * rise
		var base := p.snapped(Vector2(2, 2))
		ci.draw_colored_polygon(PackedVector2Array([base + Vector2(-5, 0), base + Vector2(0, -ht - 2), base + Vector2(5, 0)]), UiKit.INK)
		ci.draw_colored_polygon(PackedVector2Array([base + Vector2(-3, 0), base + Vector2(0, -ht), base + Vector2(3, 0)]), Color("b8873e"))
		ci.draw_line(base + Vector2(-1, -2), base + Vector2(0, -ht + 2), Color("ecc27a"), 1.0)

## A current across its area: streaks running with it, whitecaps along a surge, chevrons upstream in the warning.
func _ground_flow(ci: CanvasItem, h: Dictionary, hs: Dictionary, a: Dictionary) -> void:
	var active: bool = hs.phase == "active"
	var warn: bool = hs.phase == "warn"
	var k := _phase_k(hs)
	var r := HazardRules.rect(a)
	r.position.y -= _floor(r.get_center())
	var flow := float(a.get("current", -60)) * (float(h.get("surge", 2.0)) if active else 1.0)
	var n := int(r.size.x / (40.0 if active else 70.0))
	for i in n:
		var speed := absf(flow) * (0.8 + 0.4 * HashNoise.scatter(i, 21))
		var x := r.position.x + fposmod(HashNoise.scatter(i, 22) * r.size.x + signf(flow) * t * speed, r.size.x)
		var y := r.position.y + 6 + HashNoise.scatter(i, 23) * (r.size.y - 12)
		var ln := (10.0 + 14.0 * HashNoise.scatter(i, 24)) * (1.6 if active else 1.0)
		ci.draw_rect(Rect2(Vector2(x, y).snapped(Vector2(2, 2)), Vector2(ln, 2)), Color(SNOW, 0.55 if active else 0.3))
	if active or warn:
		# Whitecaps along the surge.
		for i in int(r.size.x / 120.0):
			var cx := r.position.x + fposmod(HashNoise.scatter(i, 25) * r.size.x + signf(flow) * t * absf(flow), r.size.x)
			var cy := r.position.y + 10 + HashNoise.scatter(i, 26) * (r.size.y - 20)
			var s := 4.0 + 4.0 * (k if warn else 1.0)
			_px(ci, Vector2(cx, cy), s, Color(SNOW, 0.8))
			_px(ci, Vector2(cx + s, cy + 2), s * 0.5, Color(SNOW, 0.6))
	if warn:
		var up := r.end.x - 30 if flow < 0 else r.position.x + 30
		_chevrons(ci, Vector2(up, r.get_center().y), int(signf(flow)), 0.6 + 0.4 * sin(t * 12.0))

## A pool's area in its phase: a thicket's reach, a Hollow puddle's wisps, quicksand's swirl, a vent's mist.
func _ground_pool(ci: CanvasItem, hid: String, hs: Dictionary, a: Dictionary, ai: int) -> void:
	var phase := str(hs.phase)
	var k := _phase_k(hs)
	var inside_player := _player_pos()
	var r := HazardRules.rect(a)
	var lift := _floor(r.get_center())
	var c := r.get_center() - Vector2(0, lift)
	match hid:
		"thorns":
			# Constant: a faint broken border marks the thicket's reach; torn cane when you push through.
			_dashed(ci, c, r.size.x * 0.55, r.size.y * 0.6, Color(AMBER, 0.35), 0.0, 12)
			if r.has_point(Vector2(inside_player.x, inside_player.y + lift)):
				for i in 4:
					if HashNoise.scatter(i + int(t * 10), 31) < 0.5: _px(ci, inside_player + Vector2((HashNoise.scatter(i, 32) - 0.5) * 30, -20 - HashNoise.scatter(i, 33) * 40), 2, Color(UiKit.RED, 0.9))
		"hollow_puddle":
			for i in 5:
				if HashNoise.scatter(i + int(t * 3), 41 + ai) < 0.5:
					_px(ci, c + Vector2((HashNoise.scatter(i, 42) - 0.5) * r.size.x * 0.8, (HashNoise.scatter(i, 43) - 0.5) * r.size.y * 0.6), 2, Color(HOLLOW_GREY, 0.6))
			if phase == "warn" or phase == "active":
				_dashed(ci, c, r.size.x * 0.62, r.size.y * 0.75, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), t * 1.5, 12, 3.0, true)
			if phase == "warn":
				for i in 6:
					var life := fposmod(t * 1.6 + HashNoise.scatter(i, 44), 1.0)
					var p := c + Vector2((HashNoise.scatter(i, 45) - 0.5) * r.size.x * 0.7, (HashNoise.scatter(i, 46) - 0.5) * r.size.y * 0.5 - life * 10.0 * (0.5 + k))
					ci.draw_arc(p.snapped(Vector2(2, 2)), 2.0 + 2.0 * life, 0, TAU, 8, Color(HOLLOW_GREY, 1.0 - life), 2.0)
			elif phase == "active":
				for i in 5:
					var pts := PackedVector2Array()
					var bx := c.x + (HashNoise.scatter(i, 47) - 0.5) * r.size.x * 0.7
					var tall := 34.0 + 26.0 * HashNoise.scatter(i, 48)
					for s in 8:
						var f := s / 7.0
						pts.append(Vector2(bx + sin(t * 5.0 + i + f * 4.0) * 6.0 * f, c.y - f * tall).snapped(Vector2(2, 2)))
					ci.draw_polyline(pts, Color(HOLLOW_GREY, 0.75 * (1.0 - k * 0.5)), 2.0)
					ci.draw_polyline(pts, Color(UiKit.SOUL, 0.25), 4.0)
		"quicksand":
			# A slow swirl of sand grains; the warning speeds it up, the active phase drags it inward.
			var spin: float = float({"tell": 0.6, "warn": 1.4, "active": 2.6, "cooldown": 0.8}.get(phase, 0.6))
			_ellipse(ci, c, r.size.x * 0.5, r.size.y * 0.5, Color(0.42, 0.3, 0.18, 0.18 + (0.18 if phase == "active" else 0.0)))
			for i in 22:
				var ang := t * spin + TAU * HashNoise.scatter(i, 141)
				var rad := fposmod(HashNoise.scatter(i, 142) - t * spin * 0.08, 1.0)
				var p := c + Vector2(cos(ang) * r.size.x * 0.48 * rad, sin(ang) * r.size.y * 0.48 * rad)
				_px(ci, p, 2, Color("8a6440", 0.85) if i % 3 else Color("e8c890", 0.9))
			if phase == "warn" or phase == "active":
				_dashed(ci, c, r.size.x * 0.56, r.size.y * 0.62, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), t * 1.2, 12, 3.0, true)
		"poison_mist":
			var vent := Vector2(c.x, r.end.y - lift - 14)
			var puffs: int = int({"tell": 2, "warn": 5, "active": 14, "cooldown": 3}.get(phase, 2))
			var reach: float = float({"tell": 22.0, "warn": 40.0 + 20.0 * k, "active": 90.0, "cooldown": 60.0 * (1.0 - k)}.get(phase, 20.0))
			var alpha: float = float({"tell": 0.25, "warn": 0.4, "active": 0.35, "cooldown": 0.3 * (1.0 - k)}.get(phase, 0.2))
			for i in int(puffs):
				var life := fposmod(t * 0.5 + HashNoise.scatter(i, 51), 1.0)
				var spread := r.size.x * 0.45 if phase == "active" else 14.0
				var p := vent + Vector2((HashNoise.scatter(i, 52) - 0.5) * 2.0 * spread + sin(t + i) * 6.0, -life * float(reach))
				var rad := 6.0 + 14.0 * life * (1.6 if phase == "active" else 1.0)
				ci.draw_circle(p.snapped(Vector2(2, 2)), rad, Color(GAS, float(alpha) * (1.0 - life * 0.6)))
			if phase == "warn" or phase == "active":
				_dashed(ci, c, r.size.x * 0.55, r.size.y * 0.6, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), -t * 1.5, 12, 3.0, true)

# ------------------------------------------------------------------ air layer
## The screen's washes and weather (both views), then the parts standing up from a spot (the side view: the top-down
## view sorts them with the room) and the warning marks over them (both).
func _draw_air() -> void:
	var rt: RoomRuntime = Game.room_rt
	if rt == null: return
	var view := _view()
	var tsa := _trib_state()
	if not tsa.is_empty(): _lightning_wash(tsa, view)
	_air_weather(rt, view)
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		match str(hid):
			"lightning": _lightning_wash(hs, view)
			"wind_gust": _air_gust(rt, hs, view)
			"fog": _air_fog(rt, h, hs, view)
			"cold": _air_cold(rt, hs, view)
			"sandstorm": _air_sandstorm(rt, hs, view)
			"scorching_heat": _air_heat(rt, h, hs, view)
			"star_wind": _air_star_wind(hs, view)
			"deep_water": _air_deep_water(rt, hs, view)
			"presence": _air_presence(hs, view)
	for part in parts(rt):
		if part.side == "air" and (part.mark or sorted_layer == null): _draw_part(air, part)

## A falling rock over its spot: grit trickling in the tell, the rock shaking high up in the warning, its fall.
func _rock_spot(ci: CanvasItem, hs: Dictionary, sp: Array, si: int) -> void:
	var k := _phase_k(hs)
	var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
	match str(hs.phase):
		"tell":
			for i in 5:
				var life := fposmod(t * 1.2 + HashNoise.scatter(i, 61 + si), 1.0)
				_px(ci, at + Vector2((HashNoise.scatter(i, 62) - 0.5) * 24, -340 + life * 300), 2, Color(GRIT, 0.8 * k))
		"warn":
			_rock(ci, at + Vector2(sin(t * 40.0) * 2.0 * k, -330), 1.0)
		"active":
			var f := minf(1.0, k / 0.8)
			var y := lerpf(-330.0, -18.0, f * f)
			for j in 4:
				_px(ci, at + Vector2(-10 + j * 6, y - 26 - 14 * j - 10 * HashNoise.scatter(j, 63)), 2, Color(DUST, 0.7 - 0.15 * j))
			_rock(ci, at + Vector2(0, y), 1.0)

## A falling boulder, 1.5 times the size of the shape below: ink rim, lit upper left.
func _rock(ci: CanvasItem, p: Vector2, a: float) -> void:
	p = p.snapped(Vector2(2, 2))
	var sc := 1.5
	var pts := func(arr: Array) -> PackedVector2Array:
		var out := PackedVector2Array()
		for q in arr: out.append((p + (q as Vector2) * sc).snapped(Vector2(2, 2)))
		return out
	var shape := [Vector2(-14, -4), Vector2(-8, -14), Vector2(6, -16), Vector2(15, -6), Vector2(13, 8), Vector2(2, 14), Vector2(-10, 11), Vector2(-16, 3)]
	var rim: Array = []
	for q in shape: rim.append((q as Vector2) * 1.16)
	ci.draw_colored_polygon(pts.call(rim), Color(UiKit.INK, a))
	ci.draw_colored_polygon(pts.call(shape), Color(ROCK[1], a))
	ci.draw_colored_polygon(pts.call([Vector2(-12, -4), Vector2(-7, -12), Vector2(4, -13), Vector2(-2, -3)]), Color(ROCK[2], a))
	ci.draw_colored_polygon(pts.call([Vector2(4, 4), Vector2(13, 6), Vector2(2, 13), Vector2(-6, 9)]), Color(ROCK[0], a))
	ci.draw_rect(Rect2(p + Vector2(-9, -15), Vector2(6, 2)), Color(ROCK[3], a))

## Lightning's hold on the whole view: the sky darkening in the tell and the warning, the flash as it strikes.
func _lightning_wash(hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	match str(hs.phase):
		"tell":
			air.draw_rect(view, Color(0.04, 0.06, 0.14, 0.16 * k))
			if HashNoise.scatter(int(t * 7.0), 71) < 0.12: air.draw_rect(Rect2(view.position, Vector2(view.size.x, 140)), Color(GLOW, 0.08))
		"warn":
			air.draw_rect(view, Color(0.04, 0.06, 0.14, 0.16))
		"active":
			var bright := 0.3 if Game.account.settings.get("flashes", true) else 0.08
			air.draw_rect(view, Color(1, 1, 1, bright * (1.0 - k)))

## A bolt over its spot: a crackling column in the warning, the bolt itself from the top of the view as it strikes.
func _bolt_spot(ci: CanvasItem, hs: Dictionary, sp: Array, view: Rect2) -> void:
	var k := _phase_k(hs)
	var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
	match str(hs.phase):
		"warn":
			var y := view.position.y
			while y < at.y - 20:
				if HashNoise.scatter(int(y) + int(t * 18.0), 72) < 0.5: _px(ci, Vector2(at.x + (HashNoise.scatter(int(y), 73) - 0.5) * 6, y), 2 + 2 * int(k > 0.5), Color(GLOW, 0.4 + 0.5 * k))
				y += 12.0
		"active":
			var pts := PackedVector2Array()
			var seed_i := int(at.x) + int(at.y) * 7
			var steps := 14
			for i in steps + 1:
				var f := float(i) / steps
				var jx := 0.0 if i == 0 or i == steps else (HashNoise.scatter(seed_i + i, 74) - 0.5) * 34.0
				pts.append(Vector2(at.x + jx, lerpf(view.position.y - 20, at.y, f)).snapped(Vector2(2, 2)))
			ci.draw_polyline(pts, Color(GLOW, 0.45), 10.0)
			ci.draw_polyline(pts, BOLT, 4.0)
			for b in 2:
				var from: Vector2 = pts[4 + b * 5]
				var fork := PackedVector2Array([from, from + Vector2((24 + 10 * b) * (1 if b == 0 else -1), 30), from + Vector2((30 + 12 * b) * (1 if b == 0 else -1), 58)])
				ci.draw_polyline(fork, Color(BOLT, 0.8), 2.0)
			ci.draw_circle(at, 26.0 * (1.0 - k) + 6.0, Color(BOLT, 0.6))

func _air_gust(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var dir := float(hs.dir)
	var phase := str(hs.phase)
	var count: int = int({"tell": 6, "warn": 16, "active": 44, "cooldown": int(24 * (1.0 - k))}.get(phase, 4))
	var speed: float = float({"tell": 160.0, "warn": 280.0, "active": 620.0, "cooldown": 300.0}.get(phase, 120.0))
	var material := str(rt.def.get("ground", {}).get("material", "earth"))
	var fleck: Color = SNOW if material == "snow" else (DUST if material in ["earth", "sand", "rock"] else Color("7fae5a"))
	for i in int(count):
		var sp := float(speed) * (0.7 + 0.6 * HashNoise.scatter(i, 81))
		var x := view.position.x - 60 + fposmod(HashNoise.scatter(i, 82) * (view.size.x + 120) + dir * t * sp, view.size.x + 120)
		var y := view.position.y + 70 + HashNoise.scatter(i, 83) * (view.size.y - 150) + sin(t * 3.0 + i) * 8.0
		if i % 3 == 0:
			# Wind lines: a pale core over a darker trail, so they read on snow and sand alike.
			var ln := (22.0 + 40.0 * HashNoise.scatter(i, 84)) * (1.6 if phase == "active" else 1.0)
			var at := Vector2(x - (ln if dir > 0 else 0.0), y).snapped(Vector2(2, 2))
			air.draw_rect(Rect2(at + Vector2(0, 2), Vector2(ln, 2)), Color(0.18, 0.24, 0.3, 0.3))
			air.draw_rect(Rect2(at, Vector2(ln, 2)), Color(SNOW, 0.8))
		else:
			var sz := 2 + 2 * int(HashNoise.scatter(i, 85) * 2)
			_px(air, Vector2(x, y + 2), sz, Color(0.12, 0.14, 0.16, 0.45))
			_px(air, Vector2(x, y), sz, Color(fleck, 0.95))
	if phase == "warn":
		var edge := view.position.x + 40 if dir > 0 else view.end.x - 40
		_chevrons(air, Vector2(edge, view.get_center().y - 60), int(dir), 0.6 + 0.4 * sin(t * 12.0))

## The sandstorm: the gust's lines and grit, inside a brown haze that thickens to a wall.
func _air_sandstorm(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var haze: float = float({"tell": 0.06 * k, "warn": 0.06 + 0.14 * k, "active": 0.28, "cooldown": 0.28 * (1.0 - k)}.get(str(hs.phase), 0.0))
	if haze > 0.0:
		air.draw_rect(view, Color(0.62, 0.46, 0.28, haze))
		# A darker wall of sand rolling in from upwind during the warning.
		if hs.phase == "warn":
			var dir := float(hs.dir)
			var w := view.size.x * 0.35 * k
			var x0 := view.position.x if dir > 0 else view.end.x - w
			air.draw_rect(Rect2(x0, view.position.y, w, view.size.y), Color(0.5, 0.36, 0.2, 0.25))
	_air_gust(rt, hs, view)

## Scorching heat: shimmer lines rising off the sand, then the full glare of the sun.
func _air_heat(rt: RoomRuntime, h: Dictionary, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var glare: float = float({"tell": 0.05 * k, "warn": 0.05 + 0.1 * k, "active": 0.18, "cooldown": 0.18 * (1.0 - k)}.get(phase, 0.0))
	if glare > 0.0: air.draw_rect(view, Color(1.0, 0.86, 0.55, glare))
	var lines: int = int({"tell": 6, "warn": 12, "active": 20, "cooldown": 8}.get(phase, 4))
	for i in lines:
		var x := view.position.x + HashNoise.scatter(i, 151) * view.size.x
		var y := view.end.y - 60 - fposmod(HashNoise.scatter(i, 152) * 300.0 + t * 40.0, 320.0)
		var pts := PackedVector2Array()
		for j in 7:
			pts.append(Vector2(x + j * 10.0, y + sin(t * 6.0 + i + j * 0.9) * 3.0).snapped(Vector2(2, 2)))
		air.draw_polyline(pts, Color(1.0, 0.95, 0.8, 0.28), 2.0)
	if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

## The Starsea's star wind: motes of starlight stream sideways, then the gust tears jade Qi
## motes off the player and carries them downwind.
func _air_star_wind(hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var n: int = int({"tell": 18, "warn": 36, "active": 70, "cooldown": 24}.get(phase, 10))
	var speed: float = float({"warn": 260.0, "active": 900.0}.get(phase, 80.0))
	var tail: float = float({"warn": 18.0, "active": 70.0}.get(phase, 4.0))
	if phase == "active": air.draw_rect(view, Color(0.55, 0.62, 0.95, 0.08))
	for i in n:
		var x := view.end.x - fposmod(HashNoise.scatter(i, 211) * (view.size.x + 200.0) + t * speed * (0.7 + 0.6 * HashNoise.scatter(i, 212)), view.size.x + 200.0) + 100.0
		var y := view.position.y + 40.0 + HashNoise.scatter(i, 213) * (view.size.y - 80.0)
		var p := Vector2(x, y).snapped(Vector2(2, 2))
		var a := (0.35 + 0.5 * HashNoise.scatter(i, 214)) * (1.0 - k if phase == "cooldown" else 1.0)
		if tail > 6.0: air.draw_line(p, p + Vector2(tail * (0.6 + HashNoise.scatter(i, 215)), 0), Color(0.75, 0.84, 1.0, a * 0.5), 2.0)
		air.draw_rect(Rect2(p, Vector2(2, 2)), Color(0.92, 0.96, 1.0, a))
	if phase == "active":
		var pp := _player_pos() + Vector2(0, -60)
		for i in 10:
			var f := fposmod(t * 1.4 + HashNoise.scatter(i, 216), 1.0)
			var q := pp + Vector2(-f * 240.0 - 10.0, sin(t * 5.0 + i) * 20.0 * f + (HashNoise.scatter(i, 217) - 0.5) * 60.0)
			air.draw_rect(Rect2(q.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(0.55, 0.95, 0.8, 0.8 * (1.0 - f)))
	if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

## Deep water (Breath Control): the whole room under a blue wash with drifting caustics; bubble
## columns rise from the air pockets, and the breath streams from the player once it runs short.
func _air_deep_water(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var phase := str(hs.phase)
	air.draw_rect(view, Color(0.2, 0.42, 0.62, 0.22))
	for i in 14:
		var x := view.position.x + fposmod(HashNoise.scatter(i, 231) * view.size.x + t * 18.0 * (0.5 + HashNoise.scatter(i, 232)), view.size.x)
		var y := view.position.y + 60.0 + HashNoise.scatter(i, 233) * (view.size.y - 200.0)
		var pts := PackedVector2Array()
		for j in 6:
			pts.append(Vector2(x + j * 14.0, y + sin(t * 1.6 + i + j * 0.8) * 4.0).snapped(Vector2(2, 2)))
		air.draw_polyline(pts, Color(0.75, 0.92, 1.0, 0.18), 2.0)
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) != "air_pocket": continue
		var at: Array = o.get("at", [0, 0])
		for k in 8:
			var f := fposmod(t * 0.7 + k / 8.0, 1.0)
			var p := Vector2(float(at[0]) + sin(t * 3.0 + k) * 8.0, float(at[1]) - 20.0 - f * 420.0)
			air.draw_circle(p.snapped(Vector2(2, 2)), 3.0 + 3.0 * (1.0 - f), Color(0.85, 0.97, 1.0, 0.7 * (1.0 - f)))
	if phase in ["warn", "active"]:
		var pp := _player_pos() + Vector2(8, -86)
		for k in 5:
			var f2 := fposmod(t * 1.8 + k / 5.0, 1.0)
			air.draw_circle((pp + Vector2(sin(t * 5.0 + k) * 5.0, -f2 * 90.0)).snapped(Vector2(2, 2)), 3.0, Color(0.9, 0.98, 1.0, 0.8 * (1.0 - f2)))
		if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

## The Presence of the eight seats: violet rings close in on the player, the edges of sight darken
## and bars of weight press down while it lands.
func _air_presence(hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var weight: float = float({"tell": 0.2 * k, "warn": 0.2 + 0.5 * k, "active": 1.0, "cooldown": 1.0 - k}.get(phase, 0.0))
	var pp := _player_pos() + Vector2(0, -50)
	var violet := Color(0.62, 0.52, 0.95)
	# darkened edges of sight
	for j in 4:
		var inset := 30.0 * j
		var a := 0.10 * weight
		air.draw_rect(Rect2(view.position + Vector2(inset, inset), Vector2(view.size.x - 2 * inset, 30)), Color(0.12, 0.08, 0.22, a))
		air.draw_rect(Rect2(view.position.x + inset, view.end.y - inset - 30, view.size.x - 2 * inset, 30), Color(0.12, 0.08, 0.22, a))
		air.draw_rect(Rect2(view.position.x + inset, view.position.y + inset, 30, view.size.y - 2 * inset), Color(0.12, 0.08, 0.22, a))
		air.draw_rect(Rect2(view.end.x - inset - 30, view.position.y + inset, 30, view.size.y - 2 * inset), Color(0.12, 0.08, 0.22, a))
	# rings closing in (three at a time), tighter while it lands
	var rmin: float = 120.0 if phase == "active" else 200.0
	for i in 3:
		var f := fposmod(t * (0.6 if phase != "active" else 1.3) + i / 3.0, 1.0)
		var r := lerpf(520.0, rmin, f)
		_dashed(air, pp, r, r * 0.42, Color(violet, 0.55 * weight * (0.4 + 0.6 * f)), t * 0.4 + i, 22, 3.0, true)
	if phase == "active":
		for i in 6:
			var x := pp.x - 90.0 + i * 36.0
			var y0 := pp.y - 120.0 - 20.0 * HashNoise.scatter(i, 221)
			var y1 := y0 + 40.0 + 30.0 * fposmod(t * 2.0 + HashNoise.scatter(i, 222), 1.0)
			air.draw_line(Vector2(x, y0).snapped(Vector2(2, 2)), Vector2(x, y1).snapped(Vector2(2, 2)), Color(UiKit.INK, 0.5), 7.0)
			air.draw_line(Vector2(x, y0).snapped(Vector2(2, 2)), Vector2(x, y1).snapped(Vector2(2, 2)), Color(violet, 0.8), 3.0)
	if phase == "warn": _mark(air, pp + Vector2(36, -100), 0.7 + 0.3 * sin(t * 12.0))

func _air_fog(rt: RoomRuntime, h: Dictionary, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var c = Game.active()
	var seen := HazardRules.effect_scale(c.stats.value(str(h.answer)), float(HazardRules.need(h, rt.def))) if c else 1.0
	var weight: float = float({"tell": 0.35 * k, "warn": 0.35 + 0.65 * k, "active": 1.0, "cooldown": 1.0 - k}.get(phase, 0.0))
	var dense := 0.35 + 0.65 * seen   # Spirit sees through: the fog stays thin for those who answer it
	var p := _player_pos()
	var n := 10 if phase == "tell" else 26
	for i in n:
		var x := view.position.x - 100 + fposmod(HashNoise.scatter(i, 91) * (view.size.x + 200) + t * (12.0 + 10.0 * HashNoise.scatter(i, 92)), view.size.x + 200)
		var low: bool = phase == "tell" or i % 3 == 0
		var y := view.end.y - 90 - HashNoise.scatter(i, 93) * 60 if low else view.position.y + 80 + HashNoise.scatter(i, 94) * (view.size.y - 160)
		var at := Vector2(x, y)
		if phase == "active" and at.distance_to(p + Vector2(0, -50)) < 150.0: continue
		_ellipse(air, at, 120.0 + 60.0 * HashNoise.scatter(i, 95), 44.0 + 20.0 * HashNoise.scatter(i, 96), Color(0.9, 0.93, 0.95, 0.15 * float(weight) * dense))
	if phase == "warn": _mark(air, p + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

func _air_cold(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var flakes: int = int({"tell": 50, "warn": 80, "active": 130, "cooldown": 40}.get(phase, 30))
	var slant: float = float({"warn": 60.0, "active": 260.0}.get(phase, 20.0))
	var fall: float = float({"active": 220.0}.get(phase, 60.0))
	for i in int(flakes):
		var x := view.position.x + fposmod(HashNoise.scatter(i, 101) * view.size.x + t * float(slant) * (0.7 + 0.6 * HashNoise.scatter(i, 102)), view.size.x)
		var y := view.position.y + fposmod(HashNoise.scatter(i, 103) * view.size.y + t * float(fall) * (0.6 + 0.8 * HashNoise.scatter(i, 104)), view.size.y)
		if phase == "active" and i % 2 == 0:
			air.draw_line(Vector2(x, y + 2), Vector2(x - 14, y - 8), Color(0.3, 0.42, 0.55, 0.35), 2.0)
			air.draw_line(Vector2(x, y), Vector2(x - 14, y - 10), Color(SNOW, 0.85), 2.0)
		else:
			_px(air, Vector2(x, y + 2), 2, Color(0.3, 0.42, 0.55, 0.35))
			_px(air, Vector2(x, y), 2, Color(SNOW, 0.9))
	# The blast chills the whole view; frost creeps in from the edges before it and holds while it blows.
	var chill: float = float({"warn": 0.08 * k, "active": 0.14, "cooldown": 0.14 * (1.0 - k)}.get(phase, 0.0))
	if chill > 0.0: air.draw_rect(view, Color(0.62, 0.78, 0.95, chill))
	var frost: float = float({"warn": 0.45 * k, "active": 0.55, "cooldown": 0.55 * (1.0 - k)}.get(phase, 0.0))
	if float(frost) > 0.0:
		for side in 4:
			for i in 16:
				var f := i / 16.0
				var depth := 18.0 + 46.0 * HashNoise.scatter(i + side * 17, 105) * (0.4 + frost)
				var r: Rect2
				match side:
					0: r = Rect2(view.position.x + f * view.size.x, view.position.y, view.size.x / 16.0 + 2, depth)
					1: r = Rect2(view.position.x + f * view.size.x, view.end.y - depth, view.size.x / 16.0 + 2, depth)
					2: r = Rect2(view.position.x, view.position.y + f * view.size.y, depth, view.size.y / 16.0 + 2)
					_: r = Rect2(view.end.x - depth, view.position.y + f * view.size.y, depth, view.size.y / 16.0 + 2)
				air.draw_rect(r, Color(FROST, float(frost)))
	if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

## S49 weather (calendar): rain slants across the view, fog drifts low, a storm adds rain and far lightning.
func _air_weather(rt: RoomRuntime, view: Rect2) -> void:
	if str(rt.def.get("weather", "")) == "": return
	var w: String = Game.calendar.weather_here()
	if w in ["rain", "storm"]:
		air.draw_rect(view, Color(0.35, 0.42, 0.5, 0.10 if w == "rain" else 0.16))   # the sky closes in
		var n := 110 if w == "rain" else 160
		var fall := 900.0 if w == "rain" else 1150.0
		var slant := 120.0 if w == "rain" else 320.0
		for i in n:
			var x := view.position.x + fposmod(HashNoise.scatter(i, 201) * view.size.x + t * slant, view.size.x)
			var y := view.position.y + fposmod(HashNoise.scatter(i, 202) * view.size.y + t * fall * (0.8 + 0.4 * HashNoise.scatter(i, 203)), view.size.y)
			var d := Vector2(slant, fall).normalized() * (14.0 + 8.0 * HashNoise.scatter(i, 204))
			air.draw_line(Vector2(x, y), Vector2(x, y) + d, Color(0.78, 0.86, 0.95, 0.5), 1.6)
	if w == "storm":
		# Far lightning: a short sheet of light every few seconds.
		var cyc := fposmod(t, 6.3)
		if cyc < 0.12 or (cyc > 0.25 and cyc < 0.32): air.draw_rect(view, Color(0.85, 0.9, 1.0, 0.18))
	if w == "fog":
		for i in 18:
			var x := view.position.x - 100 + fposmod(HashNoise.scatter(i, 211) * (view.size.x + 200) + t * (10.0 + 8.0 * HashNoise.scatter(i, 212)), view.size.x + 200)
			var y := view.end.y - 120 - HashNoise.scatter(i, 213) * (view.size.y * 0.55)
			_ellipse(air, Vector2(x, y), 150.0 + 60.0 * HashNoise.scatter(i, 214), 50.0 + 20.0 * HashNoise.scatter(i, 215), Color(0.9, 0.93, 0.95, 0.10))
