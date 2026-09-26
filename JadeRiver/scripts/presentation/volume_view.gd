class_name VolumeView
extends Node2D
## S43 volumes made visible: an updraft's rising streaks, wind lines that pulse with the gusts, a current's
## ripples, rising water's surface, a bounce pad's skin and an ice sheet's glaze. Still deep and shallow water are drawn by the
## room's water areas; crumble and no_flight have no look of their own (the boards and the room show them).
var zone: ZoneGeometry
var volume: Dictionary = {}

static func make(z: ZoneGeometry, v: Dictionary) -> VolumeView:
	var view := VolumeView.new()
	view.zone = z
	view.volume = v
	var r: Rect2 = v.rect
	view.z_index = -1980 if str(v.kind) in ["current", "rising_water", "ice"] else 1500 + int(r.end.y)
	return view

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	var r: Rect2 = volume.rect
	var t := Time.get_ticks_msec() / 1000.0
	match str(volume.kind):
		"updraft": _updraft(r, t)
		"wind": _wind(r, t)
		"current": _current(r, t)
		"rising_water": _rising(r, t)
		"bounce": _bounce(r, t)
		"ice": _ice(r, t)

## A pale glaze on the ground where the footing slides (the v1.1 traction rule), with slow glints across it.
func _ice(r: Rect2, t: float) -> void:
	var lo := maxf(0.0, float(volume.get("lo", 0.0)))
	var sheet := Rect2(r.position.x, r.position.y - lo, r.size.x, r.size.y)
	draw_rect(sheet, Color(0.5, 0.75, 0.95, 0.34))
	draw_rect(Rect2(sheet.position, Vector2(sheet.size.x, 3)), Color(0.88, 0.96, 1.0, 0.75))
	draw_rect(Rect2(sheet.position + Vector2(0, sheet.size.y - 3), Vector2(sheet.size.x, 3)), Color(0.32, 0.52, 0.72, 0.6))
	for i in 7:
		var k := fposmod(t * 0.06 + i * 0.143, 1.0)
		var x := sheet.position.x + sheet.size.x * k
		var y := sheet.position.y + sheet.size.y * fposmod(i * 0.41, 1.0)
		draw_line(Vector2(x - 26, y + 8), Vector2(x + 26, y - 8), Color(1, 1, 1, 0.6), 2.0)

## Pale streaks climbing from the ground to the updraft's top, drifting at different speeds.
func _updraft(r: Rect2, t: float) -> void:
	var lo := maxf(0.0, float(volume.lo))
	var hi := float(volume.hi)
	var foot := r.end.y - 20.0
	for i in 9:
		var x := r.position.x + r.size.x * (0.08 + 0.84 * fposmod(i * 0.37, 1.0))
		var speed := 0.35 + 0.1 * (i % 3)
		var k := fposmod(t * speed + i * 0.21, 1.0)
		var alt := lerpf(lo, hi, k)
		var y := foot - alt
		var a := sin(k * PI) * 0.65
		draw_line(Vector2(x + sin(t * 2.0 + i) * 3.0, y), Vector2(x + sin(t * 2.0 + i + 0.6) * 3.0, y - 30.0), Color(0.92, 0.98, 1.0, a), 2.5)
	for j in 3:
		var leaf_k := fposmod(t * 0.22 + j * 0.33, 1.0)
		var p := Vector2(r.position.x + r.size.x * (0.3 + 0.2 * j) + sin(t * 3.0 + j) * 10.0, foot - lerpf(lo, hi, leaf_k))
		draw_circle(p, 2.5, Color(0.55, 0.8, 0.5, sin(leaf_k * PI) * 0.7))

## Wind: streaks that race downwind while the gust is strong and idle along in the calm.
func _wind(r: Rect2, t: float) -> void:
	var push: Array = volume.get("push", [0, 0])
	var dir := signf(float(push[0])) if absf(float(push[0])) > 0.0 else 1.0
	var k := zone.wind_strength(volume) if zone else 1.0
	var n := 10 if k >= 1.0 else 4
	for i in n:
		var row := fposmod(i * 0.618, 1.0)
		var y := r.position.y + r.size.y * row - 60.0 - 80.0 * fposmod(i * 0.41, 1.0)
		var span := r.size.x
		var x := r.position.x + fposmod(t * 420.0 * k * dir + i * 377.0, span)
		var len := 40.0 + 50.0 * k
		draw_line(Vector2(x, y), Vector2(x - dir * len, y + 2.0), Color(0.95, 0.97, 1.0, 0.18 + 0.25 * k), 1.5)

## A current: chevrons on the water pointing downstream.
func _current(r: Rect2, t: float) -> void:
	var push: Array = volume.get("push", [0, 0])
	var dir := signf(float(push[0])) if absf(float(push[0])) > 0.0 else 1.0
	var cy := r.position.y + r.size.y * 0.5
	for i in int(r.size.x / 120.0):
		var x := r.position.x + fposmod(i * 120.0 + t * 60.0 * dir, r.size.x)
		var a := Vector2(x, cy + sin(i * 1.7) * r.size.y * 0.25)
		draw_line(a, a + Vector2(-dir * 10.0, -6.0), Color(0.9, 0.97, 1.0, 0.45), 2.0)
		draw_line(a, a + Vector2(-dir * 10.0, 6.0), Color(0.9, 0.97, 1.0, 0.45), 2.0)

## Rising water: the flood's surface drawn at its current height, with a bright rim and ripples.
func _rising(r: Rect2, t: float) -> void:
	var hi := float(volume.hi)
	if hi <= 0.0: return
	var top := Rect2(r.position.x, r.position.y - hi, r.size.x, r.size.y)
	draw_rect(Rect2(top.position, Vector2(r.size.x, r.size.y + hi)), Color(0.22, 0.45, 0.55, 0.45))
	draw_rect(Rect2(top.position, Vector2(r.size.x, 3)), Color(0.85, 0.95, 1.0, 0.7))
	for i in int(r.size.x / 90.0):
		var x := r.position.x + i * 90.0 + sin(t * 1.5 + i) * 20.0
		draw_line(Vector2(x, top.position.y + 14.0 + (i % 3) * 20.0), Vector2(x + 30.0, top.position.y + 14.0 + (i % 3) * 20.0), Color(0.85, 0.95, 1.0, 0.35), 2.0)

## A bounce pad: a taut, pale skin on top that shivers.
func _bounce(r: Rect2, t: float) -> void:
	var top := float(volume.hi) - 10.0
	var c := Vector2(r.get_center().x, r.get_center().y - top)
	var wob := 1.0 + sin(t * 8.0) * 0.04
	draw_arc(c, r.size.x * 0.32 * wob, 0.0, TAU, 28, Color(1.0, 0.95, 0.8, 0.75), 2.0)
	draw_arc(c, r.size.x * 0.18 * wob, 0.0, TAU, 20, Color(1.0, 0.95, 0.8, 0.5), 1.5)
