class_name HazardView
extends Node2D
## S17 · The room's hazards, drawn from RoomRuntime state in their Part 9 states: a quiet tell,
## a warning (a broken amber border and a "!" mark, so it reads without colour), the active
## blow and the cooldown. Presentation only: nothing here changes game state.

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
var impacts: Array = []      # {kind, pos, t, dur}: dust, rubble and scorch left behind
var last_phase: Dictionary = {}

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ground.z_as_relative = false
	ground.z_index = -1850
	air.z_as_relative = false
	air.z_index = 3900
	add_child(ground)
	add_child(air)
	ground.draw.connect(_draw_ground)
	air.draw.connect(_draw_air)

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
	var busy := not rt.hazards.is_empty() or not impacts.is_empty() or not _trib_state().is_empty()
	if busy or drawn:
		ground.queue_redraw()
		air.queue_redraw()
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
			var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
			if hid == "falling_rocks":
				impacts.append({"kind": "dust", "pos": at, "t": 0.0, "dur": 0.7})
				impacts.append({"kind": "rubble", "pos": at, "t": 0.0, "dur": 2.6})
				Audio.play("rockfall")
			elif hid == "spike_traps":
				impacts.append({"kind": "spikes", "pos": at, "t": 0.0, "dur": 0.9})
				Audio.play("break")
			else:
				impacts.append({"kind": "scorch", "pos": at, "t": 0.0, "dur": 3.0})
				Audio.play("thunder")
		if world and _near_player(hs.spots, 260.0): world.shake = maxf(world.shake, 0.2)

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
		return {"phase": "warn", "t": float(tv.warn_s) - float(w.left), "dur": float(tv.warn_s), "spots": [[float(w.x), float(w.y), 0.0]], "radius": float(tv.radius)}
	if not trib_strike.is_empty() and float(trib_strike.t) < 0.35:
		return {"phase": "active", "t": float(trib_strike.t), "dur": 0.35, "spots": [[float(trib_strike.x), float(trib_strike.y), 0.0]], "radius": 80.0}
	return {}

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
		impacts.append({"kind": "scorch", "pos": Vector2(float(w0.x), float(w0.y)), "t": 0.0, "dur": 3.0})
		if world: world.shake = maxf(world.shake, 0.35)
	last_phase["_trib"] = warn.duplicate()

func _near_player(spots: Array, r: float) -> bool:
	if world == null or world.player == null: return false
	for sp in spots:
		if world.player.plane.distance_to(Vector2(float(sp[0]), float(sp[1]))) <= r: return true
	return false

# ------------------------------------------------------------------ helpers
func _view() -> Rect2:
	var c: Vector2 = world.camera.get_screen_center_position() if world and world.camera else Vector2(640, 600)
	return Rect2(c - Vector2(640, 360), Vector2(1280, 720))

static func _h(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

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
	return world.player.position if world and world.player else Vector2.ZERO

# ------------------------------------------------------------------ ground layer
func _draw_ground() -> void:
	var rt: RoomRuntime = Game.room_rt
	if rt == null: return
	for im in impacts:
		var k := float(im.t) / float(im.dur)
		match str(im.kind):
			"rubble":
				for i in 7:
					_px(ground, im.pos + Vector2((_h(i, 3) - 0.5) * 70, (_h(i, 4) - 0.5) * 22), 4 + 2 * int(_h(i, 5) * 2), Color(ROCK[1 + i % 3], 1.0 - k))
			"spikes":
				_spikes(ground, im.pos, 52.0, 1.0 - k)
			"scorch":
				_ellipse(ground, im.pos, 34, 12, Color(0.08, 0.06, 0.05, 0.55 * (1.0 - k)))
				for i in 5:
					if _h(i + int(t * 6), 7) < 0.5: _px(ground, im.pos + Vector2((_h(i, 8) - 0.5) * 50, (_h(i, 9) - 0.5) * 14), 2, Color(AMBER, 1.0 - k))
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		match str(h.get("kind", "")):
			"strike": _ground_strike(str(hid), h, hs)
			"flow": _ground_flow(rt, h, hs)
			"pool": _ground_pool(rt, str(hid), h, hs)
			"aura": _ground_aura(rt, str(hid), h, hs)
	var ts := _trib_state()
	if not ts.is_empty(): _ground_strike("lightning", {"radius": float(ts.radius)}, ts)

func _ground_strike(hid: String, h: Dictionary, hs: Dictionary) -> void:
	var r := float(h.get("radius", 60))
	var k := _phase_k(hs)
	for sp in hs.spots:
		var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
		match str(hs.phase):
			"tell":
				if hid == "falling_rocks": _ellipse(ground, at, r * 0.5, r * 0.2, Color(0, 0, 0, 0.12 * k))
				if hid == "spike_traps":
					# Grit shivers over the pressure plate.
					for i in 8:
						var j := Vector2((_h(i, 121) - 0.5) * r * 1.4, (_h(i, 122) - 0.5) * r * 0.5)
						_px(ground, at + j + Vector2(0, -2.0 * float(int(t * 18.0 + i) % 2)), 2, Color(GRIT, 0.8 * k))
			"warn":
				var pulse := 0.65 + 0.35 * sin(t * 14.0)
				_ellipse(ground, at, r * (0.45 + 0.55 * k), r * 0.42 * (0.45 + 0.55 * k), Color(0.05, 0.03, 0.02, 0.18 + 0.2 * k))
				_dashed(ground, at, r, r * 0.42, Color(AMBER, pulse), t * (2.0 if hid == "falling_rocks" else -3.0), 14, 3.0, true)
				if hid == "lightning":
					for i in 6:
						if _h(i + int(t * 20), 11) < 0.4:
							_px(ground, at + Vector2((_h(i, 12) - 0.5) * r * 1.6, (_h(i, 13) - 0.5) * r * 0.6), 2, GLOW)
			"active":
				_ellipse(ground, at, r, r * 0.42, Color(0.05, 0.03, 0.02, 0.4))
				if hid == "spike_traps": _spikes(ground, at, r, minf(1.0, k * 3.0))

## Bronze spikes springing from the floor, `rise` 0..1 of their height.
func _spikes(ci: CanvasItem, at: Vector2, r: float, rise: float) -> void:
	if rise <= 0.0: return
	for i in 9:
		var p := at + Vector2((float(i % 3) - 1.0) * r * 0.55 + (_h(i, 131) - 0.5) * 8.0, (float(i / 3) - 1.0) * r * 0.22)
		var ht := (22.0 + 10.0 * _h(i, 132)) * rise
		var base := p.snapped(Vector2(2, 2))
		ci.draw_colored_polygon(PackedVector2Array([base + Vector2(-5, 0), base + Vector2(0, -ht - 2), base + Vector2(5, 0)]), UiKit.INK)
		ci.draw_colored_polygon(PackedVector2Array([base + Vector2(-3, 0), base + Vector2(0, -ht), base + Vector2(3, 0)]), Color("b8873e"))
		ci.draw_line(base + Vector2(-1, -2), base + Vector2(0, -ht + 2), Color("ecc27a"), 1.0)

func _ground_flow(rt: RoomRuntime, h: Dictionary, hs: Dictionary) -> void:
	var active: bool = hs.phase == "active"
	var warn: bool = hs.phase == "warn"
	var k := _phase_k(hs)
	for a in HazardRules.areas(h, rt.def):
		var r := HazardRules.rect(a)
		var flow := float(a.get("current", -60)) * (float(h.get("surge", 2.0)) if active else 1.0)
		var n := int(r.size.x / (40.0 if active else 70.0))
		for i in n:
			var speed := absf(flow) * (0.8 + 0.4 * _h(i, 21))
			var x := r.position.x + fposmod(_h(i, 22) * r.size.x + signf(flow) * t * speed, r.size.x)
			var y := r.position.y + 6 + _h(i, 23) * (r.size.y - 12)
			var ln := (10.0 + 14.0 * _h(i, 24)) * (1.6 if active else 1.0)
			ground.draw_rect(Rect2(Vector2(x, y).snapped(Vector2(2, 2)), Vector2(ln, 2)), Color(SNOW, 0.55 if active else 0.3))
		if active or warn:
			# Whitecaps along the surge.
			for i in int(r.size.x / 120.0):
				var cx := r.position.x + fposmod(_h(i, 25) * r.size.x + signf(flow) * t * absf(flow), r.size.x)
				var cy := r.position.y + 10 + _h(i, 26) * (r.size.y - 20)
				var s := 4.0 + 4.0 * (k if warn else 1.0)
				_px(ground, Vector2(cx, cy), s, Color(SNOW, 0.8))
				_px(ground, Vector2(cx + s, cy + 2), s * 0.5, Color(SNOW, 0.6))
		if warn:
			var up := r.end.x - 30 if flow < 0 else r.position.x + 30
			_chevrons(ground, Vector2(up, r.get_center().y), int(signf(flow)), 0.6 + 0.4 * sin(t * 12.0))

func _ground_pool(rt: RoomRuntime, hid: String, h: Dictionary, hs: Dictionary) -> void:
	var phase := str(hs.phase)
	var k := _phase_k(hs)
	var inside_player := _player_pos()
	for ai in HazardRules.areas(h, rt.def).size():
		var a: Dictionary = HazardRules.areas(h, rt.def)[ai]
		var r := HazardRules.rect(a)
		var c := r.get_center()
		match hid:
			"thorns":
				# Constant: a faint broken border marks the thicket's reach; torn cane when you push through.
				_dashed(ground, c, r.size.x * 0.55, r.size.y * 0.6, Color(AMBER, 0.35), 0.0, 12)
				if r.has_point(Vector2(inside_player.x, inside_player.y)):
					for i in 4:
						if _h(i + int(t * 10), 31) < 0.5: _px(ground, inside_player + Vector2((_h(i, 32) - 0.5) * 30, -20 - _h(i, 33) * 40), 2, Color(UiKit.RED, 0.9))
			"hollow_puddle":
				for i in 5:
					if _h(i + int(t * 3), 41 + ai) < 0.5:
						_px(ground, c + Vector2((_h(i, 42) - 0.5) * r.size.x * 0.8, (_h(i, 43) - 0.5) * r.size.y * 0.6), 2, Color(HOLLOW_GREY, 0.6))
				if phase == "warn" or phase == "active":
					_dashed(ground, c, r.size.x * 0.62, r.size.y * 0.75, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), t * 1.5, 12, 3.0, true)
				if phase == "warn":
					for i in 6:
						var life := fposmod(t * 1.6 + _h(i, 44), 1.0)
						var p := c + Vector2((_h(i, 45) - 0.5) * r.size.x * 0.7, (_h(i, 46) - 0.5) * r.size.y * 0.5 - life * 10.0 * (0.5 + k))
						ground.draw_arc(p.snapped(Vector2(2, 2)), 2.0 + 2.0 * life, 0, TAU, 8, Color(HOLLOW_GREY, 1.0 - life), 2.0)
				elif phase == "active":
					for i in 5:
						var pts := PackedVector2Array()
						var bx := c.x + (_h(i, 47) - 0.5) * r.size.x * 0.7
						var tall := 34.0 + 26.0 * _h(i, 48)
						for s in 8:
							var f := s / 7.0
							pts.append(Vector2(bx + sin(t * 5.0 + i + f * 4.0) * 6.0 * f, c.y - f * tall).snapped(Vector2(2, 2)))
						ground.draw_polyline(pts, Color(HOLLOW_GREY, 0.75 * (1.0 - k * 0.5)), 2.0)
						ground.draw_polyline(pts, Color(UiKit.SOUL, 0.25), 4.0)
			"quicksand":
				# A slow swirl of sand grains; the warning speeds it up, the active phase drags it inward.
				var spin: float = float({"tell": 0.6, "warn": 1.4, "active": 2.6, "cooldown": 0.8}.get(phase, 0.6))
				_ellipse(ground, c, r.size.x * 0.5, r.size.y * 0.5, Color(0.42, 0.3, 0.18, 0.18 + (0.18 if phase == "active" else 0.0)))
				for i in 22:
					var ang := t * spin + TAU * _h(i, 141)
					var rad := fposmod(_h(i, 142) - t * spin * 0.08, 1.0)
					var p := c + Vector2(cos(ang) * r.size.x * 0.48 * rad, sin(ang) * r.size.y * 0.48 * rad)
					_px(ground, p, 2, Color("8a6440", 0.85) if i % 3 else Color("e8c890", 0.9))
				if phase == "warn" or phase == "active":
					_dashed(ground, c, r.size.x * 0.56, r.size.y * 0.62, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), t * 1.2, 12, 3.0, true)
			"poison_mist":
				var vent := Vector2(c.x, r.end.y - 14)
				var puffs: int = int({"tell": 2, "warn": 5, "active": 14, "cooldown": 3}.get(phase, 2))
				var reach: float = float({"tell": 22.0, "warn": 40.0 + 20.0 * k, "active": 90.0, "cooldown": 60.0 * (1.0 - k)}.get(phase, 20.0))
				var alpha: float = float({"tell": 0.25, "warn": 0.4, "active": 0.35, "cooldown": 0.3 * (1.0 - k)}.get(phase, 0.2))
				for i in int(puffs):
					var life := fposmod(t * 0.5 + _h(i, 51), 1.0)
					var spread := r.size.x * 0.45 if phase == "active" else 14.0
					var p := vent + Vector2((_h(i, 52) - 0.5) * 2.0 * spread + sin(t + i) * 6.0, -life * float(reach))
					var rad := 6.0 + 14.0 * life * (1.6 if phase == "active" else 1.0)
					ground.draw_circle(p.snapped(Vector2(2, 2)), rad, Color(GAS, float(alpha) * (1.0 - life * 0.6)))
				if phase == "warn" or phase == "active":
					_dashed(ground, c, r.size.x * 0.55, r.size.y * 0.6, Color(AMBER, 0.55 + 0.45 * sin(t * 12.0)), -t * 1.5, 12, 3.0, true)

func _ground_aura(rt: RoomRuntime, hid: String, h: Dictionary, hs: Dictionary) -> void:
	# Cold: shelters show a warm ring while a blast is coming or blowing.
	if hid != "cold" or not (hs.phase in ["warn", "active"]): return
	var r := float(ContentDB.stat_const("hazard.shelter_radius", 220))
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) in h.get("shelter", []):
			var at: Array = o.get("at", [0, 0])
			_dashed(ground, Vector2(float(at[0]), float(at[1])), r, r * 0.4, Color(UiKit.PALE_GOLD, 0.55), t * 0.6, 20)

# ------------------------------------------------------------------ air layer
func _draw_air() -> void:
	var rt: RoomRuntime = Game.room_rt
	if rt == null: return
	var view := _view()
	for im in impacts:
		if str(im.kind) != "dust": continue
		var k := float(im.t) / float(im.dur)
		for i in 6:
			var ang := TAU * i / 6.0 + 0.4
			var p: Vector2 = im.pos + Vector2(cos(ang) * 50.0 * k, -absf(sin(ang)) * 24.0 * k - 6.0)
			air.draw_circle(p.snapped(Vector2(2, 2)), 8.0 + 10.0 * k, Color(DUST, 0.7 * (1.0 - k)))
	var tsa := _trib_state()
	if not tsa.is_empty(): _air_lightning({}, tsa, view)
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		match str(hid):
			"falling_rocks": _air_rocks(h, hs)
			"lightning": _air_lightning(h, hs, view)
			"wind_gust": _air_gust(rt, hs, view)
			"fog": _air_fog(rt, h, hs, view)
			"cold": _air_cold(rt, hs, view)
			"sandstorm": _air_sandstorm(rt, hs, view)
			"scorching_heat": _air_heat(rt, h, hs, view)
			"star_wind": _air_star_wind(hs, view)
			"deep_water": _air_deep_water(rt, hs, view)
			"presence": _air_presence(hs, view)
			"spike_traps":
				if hs.phase == "warn":
					for sp in hs.spots: _mark(air, Vector2(float(sp[0]), float(sp[1]) - float(sp[2])) + Vector2(0, -128), 0.7 + 0.3 * sin(t * 12.0))
		if str(h.get("kind", "")) == "pool" and hs.phase == "warn":
			for a in HazardRules.areas(h, rt.def):
				_mark(air, HazardRules.rect(a).get_center() + Vector2(0, -96), 0.7 + 0.3 * sin(t * 12.0))

func _air_rocks(h: Dictionary, hs: Dictionary) -> void:
	var k := _phase_k(hs)
	for si in hs.spots.size():
		var sp: Array = hs.spots[si]
		var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
		match str(hs.phase):
			"tell":
				for i in 5:
					var life := fposmod(t * 1.2 + _h(i, 61 + si), 1.0)
					_px(air, at + Vector2((_h(i, 62) - 0.5) * 24, -340 + life * 300), 2, Color(GRIT, 0.8 * k))
			"warn":
				_rock(at + Vector2(sin(t * 40.0) * 2.0 * k, -330), 1.0)
				_mark(air, at + Vector2(0, -128), 0.7 + 0.3 * sin(t * 12.0))
			"active":
				var f := minf(1.0, k / 0.8)
				var y := lerpf(-330.0, -18.0, f * f)
				for j in 4:
					_px(air, at + Vector2(-10 + j * 6, y - 26 - 14 * j - 10 * _h(j, 63)), 2, Color(DUST, 0.7 - 0.15 * j))
				_rock(at + Vector2(0, y), 1.0)

## A falling boulder, 1.5 times the size of the shape below: ink rim, lit upper left.
func _rock(p: Vector2, a: float) -> void:
	p = p.snapped(Vector2(2, 2))
	var sc := 1.5
	var pts := func(arr: Array) -> PackedVector2Array:
		var out := PackedVector2Array()
		for q in arr: out.append((p + (q as Vector2) * sc).snapped(Vector2(2, 2)))
		return out
	var shape := [Vector2(-14, -4), Vector2(-8, -14), Vector2(6, -16), Vector2(15, -6), Vector2(13, 8), Vector2(2, 14), Vector2(-10, 11), Vector2(-16, 3)]
	var rim: Array = []
	for q in shape: rim.append((q as Vector2) * 1.16)
	air.draw_colored_polygon(pts.call(rim), Color(UiKit.INK, a))
	air.draw_colored_polygon(pts.call(shape), Color(ROCK[1], a))
	air.draw_colored_polygon(pts.call([Vector2(-12, -4), Vector2(-7, -12), Vector2(4, -13), Vector2(-2, -3)]), Color(ROCK[2], a))
	air.draw_colored_polygon(pts.call([Vector2(4, 4), Vector2(13, 6), Vector2(2, 13), Vector2(-6, 9)]), Color(ROCK[0], a))
	air.draw_rect(Rect2(p + Vector2(-9, -15), Vector2(6, 2)), Color(ROCK[3], a))

func _air_lightning(h: Dictionary, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	match str(hs.phase):
		"tell":
			air.draw_rect(view, Color(0.04, 0.06, 0.14, 0.16 * k))
			if _h(int(t * 7.0), 71) < 0.12: air.draw_rect(Rect2(view.position, Vector2(view.size.x, 140)), Color(GLOW, 0.08))
		"warn":
			air.draw_rect(view, Color(0.04, 0.06, 0.14, 0.16))
			for sp in hs.spots:
				var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
				var y := view.position.y
				while y < at.y - 20:
					if _h(int(y) + int(t * 18.0), 72) < 0.5: _px(air, Vector2(at.x + (_h(int(y), 73) - 0.5) * 6, y), 2 + 2 * int(k > 0.5), Color(GLOW, 0.4 + 0.5 * k))
					y += 12.0
				_mark(air, at + Vector2(0, -128), 0.7 + 0.3 * sin(t * 14.0))
		"active":
			var bright := 0.3 if Game.account.settings.get("flashes", true) else 0.08
			air.draw_rect(view, Color(1, 1, 1, bright * (1.0 - k)))
			for sp in hs.spots:
				var at := Vector2(float(sp[0]), float(sp[1]) - float(sp[2]))
				var pts := PackedVector2Array()
				var seed_i := int(at.x) + int(at.y) * 7
				var steps := 14
				for i in steps + 1:
					var f := float(i) / steps
					var jx := 0.0 if i == 0 or i == steps else (_h(seed_i + i, 74) - 0.5) * 34.0
					pts.append(Vector2(at.x + jx, lerpf(view.position.y - 20, at.y, f)).snapped(Vector2(2, 2)))
				air.draw_polyline(pts, Color(GLOW, 0.45), 10.0)
				air.draw_polyline(pts, BOLT, 4.0)
				for b in 2:
					var from: Vector2 = pts[4 + b * 5]
					var fork := PackedVector2Array([from, from + Vector2((24 + 10 * b) * (1 if b == 0 else -1), 30), from + Vector2((30 + 12 * b) * (1 if b == 0 else -1), 58)])
					air.draw_polyline(fork, Color(BOLT, 0.8), 2.0)
				air.draw_circle(at, 26.0 * (1.0 - k) + 6.0, Color(BOLT, 0.6))

func _air_gust(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var dir := float(hs.dir)
	var phase := str(hs.phase)
	var count: int = int({"tell": 6, "warn": 16, "active": 44, "cooldown": int(24 * (1.0 - k))}.get(phase, 4))
	var speed: float = float({"tell": 160.0, "warn": 280.0, "active": 620.0, "cooldown": 300.0}.get(phase, 120.0))
	var material := str(rt.def.get("ground", {}).get("material", "earth"))
	var fleck: Color = SNOW if material == "snow" else (DUST if material in ["earth", "sand", "rock"] else Color("7fae5a"))
	for i in int(count):
		var sp := float(speed) * (0.7 + 0.6 * _h(i, 81))
		var x := view.position.x - 60 + fposmod(_h(i, 82) * (view.size.x + 120) + dir * t * sp, view.size.x + 120)
		var y := view.position.y + 70 + _h(i, 83) * (view.size.y - 150) + sin(t * 3.0 + i) * 8.0
		if i % 3 == 0:
			# Wind lines: a pale core over a darker trail, so they read on snow and sand alike.
			var ln := (22.0 + 40.0 * _h(i, 84)) * (1.6 if phase == "active" else 1.0)
			var at := Vector2(x - (ln if dir > 0 else 0.0), y).snapped(Vector2(2, 2))
			air.draw_rect(Rect2(at + Vector2(0, 2), Vector2(ln, 2)), Color(0.18, 0.24, 0.3, 0.3))
			air.draw_rect(Rect2(at, Vector2(ln, 2)), Color(SNOW, 0.8))
		else:
			var sz := 2 + 2 * int(_h(i, 85) * 2)
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
		var x := view.position.x + _h(i, 151) * view.size.x
		var y := view.end.y - 60 - fposmod(_h(i, 152) * 300.0 + t * 40.0, 320.0)
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
		var x := view.end.x - fposmod(_h(i, 211) * (view.size.x + 200.0) + t * speed * (0.7 + 0.6 * _h(i, 212)), view.size.x + 200.0) + 100.0
		var y := view.position.y + 40.0 + _h(i, 213) * (view.size.y - 80.0)
		var p := Vector2(x, y).snapped(Vector2(2, 2))
		var a := (0.35 + 0.5 * _h(i, 214)) * (1.0 - k if phase == "cooldown" else 1.0)
		if tail > 6.0: air.draw_line(p, p + Vector2(tail * (0.6 + _h(i, 215)), 0), Color(0.75, 0.84, 1.0, a * 0.5), 2.0)
		air.draw_rect(Rect2(p, Vector2(2, 2)), Color(0.92, 0.96, 1.0, a))
	if phase == "active":
		var pp := _player_pos() + Vector2(0, -60)
		for i in 10:
			var f := fposmod(t * 1.4 + _h(i, 216), 1.0)
			var q := pp + Vector2(-f * 240.0 - 10.0, sin(t * 5.0 + i) * 20.0 * f + (_h(i, 217) - 0.5) * 60.0)
			air.draw_rect(Rect2(q.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(0.55, 0.95, 0.8, 0.8 * (1.0 - f)))
	if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

## Deep water (Breath Control): the whole room under a blue wash with drifting caustics; bubble
## columns rise from the air pockets, and the breath streams from the player once it runs short.
func _air_deep_water(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var phase := str(hs.phase)
	air.draw_rect(view, Color(0.2, 0.42, 0.62, 0.22))
	for i in 14:
		var x := view.position.x + fposmod(_h(i, 231) * view.size.x + t * 18.0 * (0.5 + _h(i, 232)), view.size.x)
		var y := view.position.y + 60.0 + _h(i, 233) * (view.size.y - 200.0)
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
			var y0 := pp.y - 120.0 - 20.0 * _h(i, 221)
			var y1 := y0 + 40.0 + 30.0 * fposmod(t * 2.0 + _h(i, 222), 1.0)
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
		var x := view.position.x - 100 + fposmod(_h(i, 91) * (view.size.x + 200) + t * (12.0 + 10.0 * _h(i, 92)), view.size.x + 200)
		var low: bool = phase == "tell" or i % 3 == 0
		var y := view.end.y - 90 - _h(i, 93) * 60 if low else view.position.y + 80 + _h(i, 94) * (view.size.y - 160)
		var at := Vector2(x, y)
		if phase == "active" and at.distance_to(p + Vector2(0, -50)) < 150.0: continue
		_ellipse(air, at, 120.0 + 60.0 * _h(i, 95), 44.0 + 20.0 * _h(i, 96), Color(0.9, 0.93, 0.95, 0.15 * float(weight) * dense))
	if phase == "warn": _mark(air, p + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))

func _air_cold(rt: RoomRuntime, hs: Dictionary, view: Rect2) -> void:
	var k := _phase_k(hs)
	var phase := str(hs.phase)
	var flakes: int = int({"tell": 50, "warn": 80, "active": 130, "cooldown": 40}.get(phase, 30))
	var slant: float = float({"warn": 60.0, "active": 260.0}.get(phase, 20.0))
	var fall: float = float({"active": 220.0}.get(phase, 60.0))
	for i in int(flakes):
		var x := view.position.x + fposmod(_h(i, 101) * view.size.x + t * float(slant) * (0.7 + 0.6 * _h(i, 102)), view.size.x)
		var y := view.position.y + fposmod(_h(i, 103) * view.size.y + t * float(fall) * (0.6 + 0.8 * _h(i, 104)), view.size.y)
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
				var depth := 18.0 + 46.0 * _h(i + side * 17, 105) * (0.4 + frost)
				var r: Rect2
				match side:
					0: r = Rect2(view.position.x + f * view.size.x, view.position.y, view.size.x / 16.0 + 2, depth)
					1: r = Rect2(view.position.x + f * view.size.x, view.end.y - depth, view.size.x / 16.0 + 2, depth)
					2: r = Rect2(view.position.x, view.position.y + f * view.size.y, depth, view.size.y / 16.0 + 2)
					_: r = Rect2(view.end.x - depth, view.position.y + f * view.size.y, depth, view.size.y / 16.0 + 2)
				air.draw_rect(r, Color(FROST, float(frost)))
	if phase == "warn": _mark(air, _player_pos() + Vector2(36, -150), 0.7 + 0.3 * sin(t * 12.0))
