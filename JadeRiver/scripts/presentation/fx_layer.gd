class_name FxLayer
extends Node2D
## Transient effects and floating numbers driven by events (S36): hit sparks
## tinted by element, damage numbers (crits larger and gold, soul violet, Qi teal),
## slash arcs, dust, rings, breakthrough spirals, meditation motes, projectiles.
## Presentation only: nothing here changes game state.

const ARRAY_COLOURS := {"guard": Color("8aebee"), "killing": Color("e45858"), "binding": Color("b18de2")}   # as their plates are engraved

var fx: Array = []          # {kind, pos, t, dur, color, facing, text, size, vel, z}
var numbers_enabled := true

func _ready() -> void:
	z_index = 4000
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func add(kind: String, pos: Vector2, extra := {}) -> void:
	var e := {"kind": kind, "pos": pos, "t": 0.0, "dur": float(extra.get("dur", 0.4)), "color": extra.get("color", UiKit.PAPER),
		"facing": int(extra.get("facing", 1)), "text": str(extra.get("text", "")), "size": int(extra.get("size", 20)),
		"vel": extra.get("vel", Vector2.ZERO), "radius": float(extra.get("radius", 30))}
	fx.append(e)
	if fx.size() > 160: fx.pop_front()

func number(pos: Vector2, text: String, color: Color, size := 22, crit := false) -> void:
	if not numbers_enabled: return
	add("number", pos + Vector2(randf_range(-10, 10), 0), {"text": text, "color": color, "size": size + (8 if crit else 0), "dur": 1.0,
		"vel": Vector2(randf_range(-12, 12), -70.0 if not crit else -90.0)})

func _process(delta: float) -> void:
	for e in fx.duplicate():
		e.t = float(e.t) + delta
		e.pos = e.pos + e.vel * delta
		if e.kind == "number": e.vel = e.vel * (1.0 - delta * 1.5)
		if float(e.t) >= float(e.dur): fx.erase(e)
	queue_redraw()

func _draw() -> void:
	# S48 Array Plates laid in a fight are drawn from Combat's state, on the ground under everything else.
	if Game.combat:
		for a in Game.combat.arrays: _draw_array(a)
	# Projectiles live in the RoomRuntime and are drawn from state.
	if Game.room_rt:
		for p in Game.room_rt.projectiles:
			if float(p.get("delay", 0.0)) > 0.0: continue
			_draw_projectile(p)
	for e in fx:
		var k: float = float(e.t) / maxf(0.001, float(e.dur))
		var c: Color = e.color
		match str(e.kind):
			"number":
				var a := 1.0 if k < 0.6 else 1.0 - (k - 0.6) / 0.4
				UiKit.draw_outlined(self, e.text, e.pos + Vector2(-100, 0), int(e.size), Color(c, a), HORIZONTAL_ALIGNMENT_CENTER, 200)
			"spark":
				for i in 8:
					var ang := i * TAU / 8.0 + 0.3
					var r1 := 6.0 + 22.0 * k
					var p1: Vector2 = e.pos + Vector2(cos(ang), sin(ang) * 0.7) * r1
					draw_rect(Rect2(p1.snapped(Vector2(2, 2)), Vector2(4, 4) * (1.0 - k) + Vector2(2, 2)), Color(c, 1.0 - k))
				draw_circle(e.pos, 10.0 * (1.0 - k), Color(1, 1, 1, 0.8 * (1.0 - k)))
			"slash":
				var f := float(e.facing)
				var pts := PackedVector2Array()
				for i in 9:
					var ang := lerpf(-1.1, 1.0, i / 8.0)
					pts.append(e.pos + Vector2(cos(ang) * f, sin(ang)) * float(e.radius))
				draw_polyline(pts, Color(c, 1.0 - k), 6.0 * (1.0 - k) + 2.0)
				draw_polyline(pts, Color(1, 1, 1, 0.7 * (1.0 - k)), 2.0)
			"dust":
				for i in 5:
					var off := Vector2((i - 2) * 9.0 * (1.0 + k), -6.0 * k * (1 + i % 2))
					draw_circle(e.pos + off, 6.0 * (1.0 - k) + 2.0, Color(0.75, 0.68, 0.55, 0.6 * (1.0 - k)))
			"ring":
				draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
				draw_arc(Vector2.ZERO, float(e.radius) * (0.3 + k), 0, TAU, 40, Color(c, 1.0 - k), 4.0)
				draw_set_transform(Vector2.ZERO)
			"note":
				# A musical note of the flute's melody (S47 v1.1): rises, sways and fades.
				var sway := sin(float(e.t) * 5.0 + float(e.radius)) * 6.0
				_draw_note(e.pos + Vector2(sway, 0), c, 1.0 if k < 0.5 else 1.0 - (k - 0.5) * 2.0, float(e.size) / 20.0)
			"wave":
				draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
				draw_arc(Vector2.ZERO, float(e.radius) * k, 0, TAU, 48, Color(c, 0.9 * (1.0 - k)), 8.0 * (1.0 - k) + 2.0)
				draw_set_transform(Vector2.ZERO)
			"spiral":
				for i in 24:
					var ang := i * 0.55 + k * 8.0
					var r := 10.0 + i * 4.0 * k
					draw_rect(Rect2((e.pos + Vector2(cos(ang), sin(ang) * 0.5) * r - Vector2(0, i * 5.0 * k)).snapped(Vector2(2, 2)), Vector2(4, 4)), Color(c, 1.0 - k))
			"motes":
				for i in 6:
					var ph := fmod(k + i / 6.0, 1.0)
					var p2: Vector2 = e.pos + Vector2(sin(i * 2.1 + ph * 4.0) * 26.0, -ph * 70.0)
					draw_rect(Rect2(p2.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(c, 0.8 * (1.0 - ph)))
			"flash":
				var bright := 0.5 if Game.account.settings.get("flashes", true) else 0.15
				draw_circle(e.pos, float(e.radius) * (0.5 + k), Color(c, bright * (1.0 - k)))
			"pagoda":
				# A jade pagoda falls over the foe and holds it; it fades as the prison lifts.
				var drop := minf(1.0, k * 8.0)
				var pp: Vector2 = e.pos + Vector2(0, -150.0 * (1.0 - drop))
				var fade2 := 0.9 if k < 0.85 else (1.0 - k) / 0.15 * 0.9
				for i in 4:
					var w := 44.0 - i * 8.0
					var y := -i * 26.0
					draw_rect(Rect2(pp + Vector2(-w * 0.5 + 4, y - 22), Vector2(w - 8, 18)), Color(0.75, 0.2, 0.2, fade2 * 0.8))
					draw_colored_polygon(PackedVector2Array([pp + Vector2(-w * 0.5 - 6, y - 22), pp + Vector2(w * 0.5 + 6, y - 22), pp + Vector2(w * 0.5 - 4, y - 30),
						pp + Vector2(-w * 0.5 + 4, y - 30)]), Color(c, fade2))
				draw_rect(Rect2(pp + Vector2(-2, -128), Vector2(4, 12)), Color(UiKit.GOLD, fade2))
			"seal_slam":
				var land := minf(1.0, k * 4.0)
				var sp2: Vector2 = e.pos + Vector2(0, -200.0 * (1.0 - land) - 40.0)
				if k < 0.5:
					draw_rect(Rect2(sp2 - Vector2(34, 24), Vector2(68, 48)), Color(c, 0.9))
					draw_rect(Rect2(sp2 - Vector2(22, 12), Vector2(44, 24)), Color(0.8, 0.2, 0.2, 0.9))
				if land >= 1.0:
					var kk := (k - 0.25) / 0.75
					draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
					draw_arc(Vector2.ZERO, float(e.radius) * kk, 0, TAU, 48, Color(c, 0.9 * (1.0 - kk)), 10.0 * (1.0 - kk) + 2.0)
					draw_set_transform(Vector2.ZERO)
			"talisman_wave":
				# The talisman's stroke: a long blade of light across the room in front of you.
				var f2 := float(e.get("facing", 1))
				var len2 := float(e.radius) * minf(1.0, k * 3.0)
				var a3 := 1.0 - k
				draw_rect(Rect2(e.pos + Vector2(0 if f2 > 0 else -len2, -10), Vector2(len2, 20)), Color(c, 0.35 * a3))
				draw_rect(Rect2(e.pos + Vector2(0 if f2 > 0 else -len2, -4), Vector2(len2, 8)), Color(1, 1, 0.9, 0.9 * a3))
			"pill_cloud":
				# A Halo or Soul pill forms (G1): a coloured cloud boils up over the furnace, then thins away.
				var fade := 1.0 if k < 0.7 else 1.0 - (k - 0.7) / 0.3
				for i in 14:
					var ang := i * 2.39996 + k * 1.6
					var rr := 18.0 + (i % 5) * 11.0 + 20.0 * k
					var pc: Vector2 = e.pos + Vector2(cos(ang) * rr * 1.5, sin(ang) * rr * 0.45 - 40.0 * k)
					draw_circle(pc, 16.0 + (i % 3) * 6.0 + 10.0 * k, Color(c, 0.22 * fade))
				for i in 10:
					var ph := fmod(k * 2.0 + i / 10.0, 1.0)
					var sp: Vector2 = e.pos + Vector2(sin(i * 1.7 + ph * 5.0) * 60.0, -20.0 - ph * 90.0)
					draw_rect(Rect2(sp.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(1.0, 0.95, 0.75, 0.9 * fade * (1.0 - ph)))
			"heaven_cloud":
				# S49 heavenly phenomenon: auspicious clouds gather high over the room and pour light down on you.
				var grow := minf(1.0, k * 3.0)
				var fade2 := 1.0 if k < 0.75 else 1.0 - (k - 0.75) / 0.25
				var top: Vector2 = e.pos + Vector2(0, -320)
				draw_rect(Rect2(e.pos + Vector2(-34.0 * grow, -300), Vector2(68.0 * grow, 300)), Color(1.0, 0.93, 0.7, 0.12 * fade2))
				draw_rect(Rect2(e.pos + Vector2(-12.0 * grow, -300), Vector2(24.0 * grow, 300)), Color(1.0, 0.97, 0.85, 0.2 * fade2))
				_cloud_bank(top, 620.0 * (0.4 + 0.6 * grow), 70.0, c, Color(1.0, 0.98, 0.9), 0.9 * fade2, 3, float(e.t))
				for i in 14:
					var ph := fmod(float(e.t) * 0.35 + i / 14.0, 1.0)
					var mp: Vector2 = e.pos + Vector2((_hash(i, 5) - 0.5) * 90.0, -ph * 300.0)
					draw_rect(Rect2(mp.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(1.0, 0.95, 0.75, 0.9 * fade2 * (1.0 - ph)))
			"heaven_storm":
				# A tribulation's sky: a dark bank low over the room, lit from inside, and bolts that fall near you.
				var grow2 := minf(1.0, k * 4.0)
				var fade3 := 1.0 if k < 0.8 else 1.0 - (k - 0.8) / 0.2
				var top2: Vector2 = e.pos + Vector2(0, -300)
				var beat := int(float(e.t) * 3.0)
				var lit := fmod(float(e.t) * 3.0, 1.0) < 0.3
				_cloud_bank(top2, 820.0 * (0.4 + 0.6 * grow2), 80.0, Color(0.2, 0.21, 0.29), Color(0.55, 0.62, 0.8) if lit else Color(0.34, 0.36, 0.46), fade3, 7, float(e.t))
				if lit:
					var bx := (_hash(beat, 11) - 0.5) * 420.0
					var pts2 := PackedVector2Array()
					var yy := -290.0
					var xx := bx
					while yy < 0.0:
						pts2.append(e.pos + Vector2(xx, yy))
						yy += 40.0 + _hash(beat * 7 + int(yy), 12) * 30.0
						xx += (_hash(beat * 13 + int(yy), 13) - 0.5) * 50.0
					pts2.append(e.pos + Vector2(xx, 0))
					draw_polyline(pts2, Color(c, 0.35 * fade3), 7.0)
					draw_polyline(pts2, Color(0.95, 0.97, 1.0, 0.95 * fade3), 2.0)
			"text":
				var a2 := 1.0 if k < 0.7 else 1.0 - (k - 0.7) / 0.3
				UiKit.draw_outlined(self, e.text, e.pos + Vector2(-200, 0), int(e.size), Color(c, a2), HORIZONTAL_ALIGNMENT_CENTER, 400)

## A soft bank of cloud: many flattened, overlapping puffs (a shadowed underside, a lit top) that drift slowly.
func _cloud_bank(center: Vector2, width: float, height: float, base: Color, lit: Color, alpha: float, salt: int, t: float) -> void:
	for layer in 2:
		for i in 34:
			var u := _hash(i, salt) - 0.5
			var rx := 34.0 + _hash(i, salt + 1) * 46.0
			var arch := (1.0 - absf(u) * 2.0) * height * 0.6
			var at: Vector2 = center + Vector2(u * width + sin(t * 0.5 + i) * 6.0, (_hash(i, salt + 2) - 0.5) * height * 0.4 - arch * 0.5)
			if layer == 1:
				at += Vector2(0, -rx * 0.22)
				rx *= 0.7
			draw_set_transform(at, 0.0, Vector2(1.0, 0.46))
			draw_circle(Vector2.ZERO, rx, Color(base if layer == 0 else lit, (0.3 if layer == 0 else 0.16) * alpha))
	draw_set_transform(Vector2.ZERO)

## An array on the ground: two rings of the array's colour, eight trigram strokes between them and a slow turn.
func _draw_array(a: Dictionary) -> void:
	var kind := str(a.kind)
	var col: Color = ARRAY_COLOURS.get(kind, ARRAY_COLOURS.guard)
	var at := Vector2(float(a.x), float(a.y))
	var r := float(a.radius)
	var fade := clampf(float(a.t), 0.0, 1.0)
	var spin := float(Time.get_ticks_msec()) / 1000.0 * (1.4 if kind == "killing" else 0.6)
	draw_set_transform(at, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, r, Color(col, 0.08 * fade))
	draw_arc(Vector2.ZERO, r, 0, TAU, 64, Color(col, 0.75 * fade), 3.0)
	draw_arc(Vector2.ZERO, r * 0.72, 0, TAU, 48, Color(col, 0.5 * fade), 2.0)
	for i in 8:
		var ang := spin + TAU * i / 8.0
		var p0 := Vector2(cos(ang), sin(ang)) * r * 0.76
		var p1 := Vector2(cos(ang), sin(ang)) * r * 0.94
		var side := Vector2(-sin(ang), cos(ang)) * 6.0
		draw_line(p0 + side, p1 + side, Color(col, 0.85 * fade), 2.0)
		if i % 2 == 0: draw_line(p0 - side, p1 - side, Color(col, 0.85 * fade), 2.0)
	# The heart of each array: trigram bars (guarding), four blades pointing in (killing), a chain turning (binding).
	match kind:
		"killing":
			for i in 4:
				var ang := -spin * 0.5 + TAU * i / 4.0 + PI / 4.0
				var u := Vector2(cos(ang), sin(ang))
				var w := Vector2(-u.y, u.x) * r * 0.08
				draw_colored_polygon(PackedVector2Array([u * r * 0.6 + w, u * r * 0.6 - w, u * r * 0.12]), Color(col, 0.7 * fade))
		"binding":
			for i in 12:
				var ang := -spin + TAU * i / 12.0
				draw_arc(Vector2(cos(ang), sin(ang)) * r * 0.45, r * 0.06, 0, TAU, 12, Color(col, 0.8 * fade), 2.0)
		_:
			for i in 8:
				var ang := spin * 0.5 + TAU * i / 8.0
				var u := Vector2(cos(ang), sin(ang)) * r * 0.42
				var w := Vector2(-sin(ang), cos(ang)) * r * 0.09
				draw_line(u + w, u - w, Color(col, 0.8 * fade), 3.0)
			draw_circle(Vector2.ZERO, r * 0.06, Color(UiKit.PALE_GOLD, 0.9 * fade))
	draw_set_transform(Vector2.ZERO)

## A quaver: an ink-edged oval head, a stem and a flag, drawn on the 2-pixel grid.
func _draw_note(at: Vector2, col: Color, alpha: float, sc: float) -> void:
	var head := at.snapped(Vector2(2, 2))
	draw_set_transform(head, -0.35, Vector2(1.0, 0.72) * sc)
	draw_circle(Vector2.ZERO, 6.0, Color(UiKit.INK, alpha))
	draw_circle(Vector2.ZERO, 4.2, Color(col, alpha))
	draw_set_transform(Vector2.ZERO)
	var top := head + Vector2(5, -20) * sc
	draw_line(head + Vector2(5, -2) * sc, top, Color(UiKit.INK, alpha), 3.0 * sc)
	draw_line(head + Vector2(5, -2) * sc, top, Color(col, alpha), 1.4 * sc)
	draw_line(top, top + Vector2(7, 6) * sc, Color(UiKit.INK, alpha), 3.0 * sc)
	draw_line(top, top + Vector2(7, 6) * sc, Color(col, alpha), 1.4 * sc)

static func _hash(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

func _draw_projectile(p: Dictionary) -> void:
	var pos := Vector2(float(p.x), float(p.y) - float(p.alt)).snapped(Vector2(2, 2))
	var dir := float(p.dir)
	match str(p.get("art", "arrow")):
		"arrow":
			draw_line(pos + Vector2(-dir * 18, 0), pos + Vector2(dir * 12, 0), Color("d6b779"), 2)
			draw_colored_polygon(PackedVector2Array([pos + Vector2(dir * 18, 0), pos + Vector2(dir * 8, -4), pos + Vector2(dir * 8, 4)]), Color("d9e3cb"))
			draw_line(pos + Vector2(-dir * 18, -4), pos + Vector2(-dir * 10, 0), Color("b8cbb7"), 2)
			draw_line(pos + Vector2(-dir * 18, 4), pos + Vector2(-dir * 10, 0), Color("b8cbb7"), 2)
		"pebble", "boulder":
			var r := 6.0 if p.art == "pebble" else 12.0
			draw_circle(pos, r + 2, UiKit.INK)
			draw_circle(pos, r, Color("9a8c78"))
			draw_rect(Rect2(pos + Vector2(-r * 0.4, -r * 0.5), Vector2(4, 4)), Color("c8bca6"))
		"ice_shard":
			var tip := pos + Vector2(dir * 12, 0)
			draw_colored_polygon(PackedVector2Array([tip, pos + Vector2(0, -5), pos + Vector2(-dir * 10, 0), pos + Vector2(0, 5)]), Color("9fd8ff"))
			draw_polyline(PackedVector2Array([tip, pos + Vector2(0, -5), pos + Vector2(-dir * 10, 0), pos + Vector2(0, 5), tip]), UiKit.INK, 2)
			draw_line(pos + Vector2(-dir * 4, -1), tip, Color("e8f7ff"), 2)
			for i in 3:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 6), (i - 1) * 3)).snapped(Vector2(2, 2)), Vector2(2, 2)), Color("dff3ff"))
		"sand_crescent":
			# The Tomb King's thrown crescent of sand: a curved blade of gold grit with a dusty trail.
			var arc := PackedVector2Array()
			for i in 9:
				var a := lerpf(-1.2, 1.2, i / 8.0)
				arc.append((pos + Vector2(dir * cos(a) * 16.0, sin(a) * 22.0)).snapped(Vector2(2, 2)))
			draw_polyline(arc, UiKit.INK, 8.0)
			draw_polyline(arc, Color("d9a54a"), 5.0)
			draw_polyline(arc, Color("ffe6a1"), 2.0)
			for i in 5:
				draw_rect(Rect2((pos + Vector2(-dir * (12 + i * 8), sin(float(p.travelled) * 0.08 + i * 1.7) * 10.0)).snapped(Vector2(2, 2)), Vector2(4, 4)),
					Color("c9a06a", 0.7 - i * 0.12))
		"moon_crescent":
			# S47 the Moon Spirit's skill: a thin crescent of pale moonlight skimming forward, with a silver wake.
			draw_circle(pos, 32, Color(0.75, 0.9, 1.0, 0.16))
			var moon := PackedVector2Array()
			for i in 13:
				var a := lerpf(-1.3, 1.3, i / 12.0)
				moon.append((pos + Vector2(dir * cos(a) * 24.0, sin(a) * 36.0)).snapped(Vector2(2, 2)))
			draw_polyline(moon, UiKit.INK, 9.0)
			draw_polyline(moon, Color("9fc8f0"), 6.0)
			draw_polyline(moon, Color("f2f8ff"), 2.0)
			for i in 4:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 9), sin(float(p.travelled) * 0.07 + i * 1.9) * 12.0)).snapped(Vector2(2, 2)), Vector2(2, 2)),
					Color(0.85, 0.95, 1.0, 0.8 - i * 0.18))
		"bamboo":
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), UiKit.INK, 6)
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), Color("8cc05a"), 4)
		"talisman":
			draw_rect(Rect2(pos - Vector2(6, 10), Vector2(12, 20)), Color("e8d99a"))
			draw_rect(Rect2(pos - Vector2(3, 5), Vector2(6, 8)), UiKit.RED)
		"flying_sword":
			# S47: the released jian, point first, with a pale streak behind it.
			for k in 4:
				draw_line(pos + Vector2(-dir * (20 + k * 10), 0), pos + Vector2(-dir * (28 + k * 10), 0), Color(0.8, 0.95, 1.0, 0.5 - k * 0.12), 3)
			draw_line(pos + Vector2(-dir * 16, 0), pos + Vector2(dir * 14, 0), Color("2b2f33"), 5)
			draw_line(pos + Vector2(-dir * 14, 0), pos + Vector2(dir * 14, 0), Color("dfe8ee"), 3)
			draw_colored_polygon(PackedVector2Array([pos + Vector2(dir * 14, -2), pos + Vector2(dir * 14, 2), pos + Vector2(dir * 20, 0)]), Color("f4fbff"))
			draw_line(pos + Vector2(-dir * 16, -6), pos + Vector2(-dir * 16, 6), Color("b5892f"), 3)
			draw_line(pos + Vector2(-dir * 17, 0), pos + Vector2(-dir * 24, 0), Color("5a3a22"), 3)
		"note":
			# The flute's note: a jade-lit quaver with a short trail of motes (S47 v1.1).
			draw_circle(pos, 13, Color(0.55, 0.95, 0.85, 0.22))
			for i in 3:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 8), sin(float(p.travelled) * 0.09 + i * 1.3) * 5.0)).snapped(Vector2(2, 2)), Vector2(4, 4)),
					Color(0.7, 1.0, 0.9, 0.6 - i * 0.18))
			_draw_note(pos + Vector2(0, sin(float(p.travelled) * 0.06) * 3.0), Color("8fe8cf"), 1.0, 1.0)
		"fan":
			# The thrown fan (S47 v1.1): an open folding fan spinning edge-over-edge, with a wind streak.
			var spin := float(p.travelled) * 0.05 * dir
			for i in 3:
				draw_line(pos + Vector2(-dir * (18 + i * 9), -6 + i * 6), pos + Vector2(-dir * (30 + i * 9), -6 + i * 6), Color(0.9, 0.96, 1.0, 0.45 - i * 0.12), 2)
			var ribs := PackedVector2Array([pos])
			for i in 9:
				var a := spin + lerpf(-1.2, 1.2, i / 8.0)
				ribs.append(pos + Vector2(cos(a), sin(a)) * 16.0)
			draw_colored_polygon(ribs, Color("e9dcc0"))
			draw_polyline(ribs + PackedVector2Array([pos]), UiKit.INK, 2.0)
			for i in 5:
				var a2 := spin + lerpf(-1.2, 1.2, i / 4.0)
				draw_line(pos, pos + Vector2(cos(a2), sin(a2)) * 15.0, Color("8a5a34"), 1.0)
			draw_arc(pos, 11.0, spin - 1.2, spin + 1.2, 8, Color("b0373a"), 2.0)
			draw_circle(pos, 3, Color("5a3a22"))
		"needle":
			draw_line(pos + Vector2(-dir * 12, 0), pos + Vector2(dir * 8, 0), UiKit.INK, 3)
			draw_line(pos + Vector2(-dir * 12, 0), pos + Vector2(dir * 8, 0), Color("e8eef0"), 1)
			draw_rect(Rect2(pos + Vector2(-dir * 14 - 1, -1), Vector2(3, 3)), UiKit.RED)
		"knife":
			var tip2 := pos + Vector2(dir * 12, 0)
			draw_colored_polygon(PackedVector2Array([tip2, pos + Vector2(0, -4), pos + Vector2(-dir * 6, 0), pos + Vector2(0, 4)]), Color("c9d2d6"))
			draw_polyline(PackedVector2Array([tip2, pos + Vector2(0, -4), pos + Vector2(-dir * 6, 0), pos + Vector2(0, 4), tip2]), UiKit.INK, 2)
			draw_line(pos + Vector2(-dir * 6, 0), pos + Vector2(-dir * 12, 0), Color("6b4a2a"), 3)
			draw_arc(pos + Vector2(-dir * 14, 0), 3, 0, TAU, 8, UiKit.RED, 2)
		"pellet":
			draw_circle(pos, 7, UiKit.INK)
			draw_circle(pos, 5, Color("2a2a30"))
			draw_rect(Rect2(pos + Vector2(-5, -1), Vector2(10, 2)), UiKit.RED)
			draw_rect(Rect2(pos + Vector2(-dir * 2, -9), Vector2(3, 3)), Color("ffd76a"))
		_:
			var col := SpriteCache.element_color(str(p.get("element", "none")))
			if str(p.art).begins_with("soul"): col = UiKit.SOUL
			draw_circle(pos, 12, Color(col, 0.35))
			draw_circle(pos, 8, Color(col, 0.8))
			draw_circle(pos, 4, Color(1, 1, 1, 0.9))
			for i in 4:
				draw_rect(Rect2((pos + Vector2(-dir * (10 + i * 7), sin(float(p.travelled) * 0.1 + i) * 4)).snapped(Vector2(2, 2)), Vector2(4, 4)), Color(col, 0.6 - i * 0.12))
