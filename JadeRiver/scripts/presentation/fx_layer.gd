class_name FxLayer
extends Node2D
## Transient effects and floating numbers driven by events (S36): hit sparks
## tinted by element, damage numbers (crits larger and gold, soul violet, Qi teal),
## slash arcs, dust, rings, breakthrough spirals, meditation motes, projectiles.
## Presentation only: nothing here changes game state.

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
				draw_circle(e.pos, float(e.radius) * (0.5 + k), Color(c, 0.5 * (1.0 - k)))
			"text":
				var a2 := 1.0 if k < 0.7 else 1.0 - (k - 0.7) / 0.3
				UiKit.draw_outlined(self, e.text, e.pos + Vector2(-200, 0), int(e.size), Color(c, a2), HORIZONTAL_ALIGNMENT_CENTER, 400)

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
		"bamboo":
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), UiKit.INK, 6)
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), Color("8cc05a"), 4)
		"talisman":
			draw_rect(Rect2(pos - Vector2(6, 10), Vector2(12, 20)), Color("e8d99a"))
			draw_rect(Rect2(pos - Vector2(3, 5), Vector2(6, 8)), UiKit.RED)
		_:
			var col := SpriteCache.element_color(str(p.get("element", "none")))
			if str(p.art).begins_with("soul"): col = UiKit.SOUL
			draw_circle(pos, 12, Color(col, 0.35))
			draw_circle(pos, 8, Color(col, 0.8))
			draw_circle(pos, 4, Color(1, 1, 1, 0.9))
			for i in 4:
				draw_rect(Rect2((pos + Vector2(-dir * (10 + i * 7), sin(float(p.travelled) * 0.1 + i) * 4)).snapped(Vector2(2, 2)), Vector2(4, 4)), Color(col, 0.6 - i * 0.12))
