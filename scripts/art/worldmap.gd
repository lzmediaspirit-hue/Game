# Painted Jade River valley for the World Map. Pure geography — dots, routes and labels are
# drawn by the UI from data so states, sizes and future regions never require repainting.
class_name WorldMapArt
extends RefCounted

const C = preload("res://scripts/data/content.gd")
static var _tex: Texture2D


static func texture() -> Texture2D:
	if _tex == null:
		_tex = _paint(480, 270)
	return _tex


static func _paint(w: int, h: int) -> Texture2D:
	var x := Painter.new(w, h)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	# land
	for yy in h:
		var t := float(yy) / h
		x.span(yy, 0, w - 1, Painter.mix("#2c4a44", "#3e6a4a", t))
	# distant mountains along the top
	for i in 26:
		var cx := rng.randf() * w
		var bh := 40.0 + rng.randf() * 50
		var ww := 14.0 + rng.randf() * 18
		var base := 70.0 + rng.randf() * 20
		x.bezier_shape([cx - ww, base, cx - ww * 0.8, base - bh * 0.7, cx - ww * 0.4, base - bh, cx, base - bh, cx + ww * 0.4, base - bh, cx + ww * 0.8, base - bh * 0.7, cx + ww, base], Painter.mix("#4a6e78", "#6a8e98", rng.randf()))
	x.rect(0, 62, w, 18, Color(0.85, 0.9, 0.88, 0.25))
	# cliffs / forest masses
	for i in 240:
		var fx := rng.randf() * w
		var fy := 70 + rng.randf() * (h - 70)
		x.circ(fx, fy, 3 + rng.randf() * 6, Painter.mix("#1f4a34", "#2f6a40", rng.randf()))
	for i in 120:
		var fx2 := rng.randf() * w
		var fy2 := 80 + rng.randf() * (h - 80)
		x.circ(fx2, fy2, 1.5 + rng.randf() * 2, "#4f8a4a")
	# the S-shaped jade river
	var river := [0, 150, 40, 158, 90, 170, 130, 176, 170, 164, 205, 150, 240, 140, 270, 142, 300, 150, 330, 146, 355, 128, 375, 105, 395, 80, 420, 55, 450, 30, 480, 20]
	x.polyline(river, 18, "#2a7a80")
	x.polyline(river, 12, "#3fa8a8")
	x.polyline(river, 4, "#8fe0d8")
	for i in 60:
		var k := rng.randi() % (river.size() / 2 - 1)
		var px: float = river[k * 2] + rng.randf() * 20
		var py: float = river[k * 2 + 1] + rng.randf() * 6 - 3
		x.rect(px, py, 3, 1, "#c8f4ee")
	# bamboo grove patch
	for i in 70:
		var bx := 260 + rng.randf() * 60
		var by := 110 + rng.randf() * 40
		x.rect(bx, by, 1, 6 + rng.randf() * 5, Painter.mix("#5a9a4a", "#9ad070", rng.randf()))
	# waterfalls from the eastern cliffs
	for fx3 in [345, 360, 400]:
		x.rect(fx3, 90, 3, 40, "#cfeff0")
		x.rect(fx3 + 1, 90, 1, 40, "#ffffff")
	# cloud bank around Cloudrest and the monastery peak
	for i in 30:
		x.ell(300 + rng.randf() * 180, 50 + rng.randf() * 60, 10 + rng.randf() * 12, 3 + rng.randf() * 3, Color(0.92, 0.95, 0.95, 0.55))
	x.bezier_shape([370, 70, 380, 40, 390, 20, 400, 14, 410, 20, 420, 40, 430, 70], "#3a4a5a")
	# settlements: tiny roofs and lanterns
	for a in C.MAP_AREAS:
		var mp: Array = C.AREAS[a].mapPos
		var sx: float = mp[0] * w
		var sy: float = mp[1] * h
		var n := 5 if C.AREAS[a].type == "town" else 2
		for k in n:
			var hx := sx - 16 + rng.randf() * 32
			var hy := sy - 14 + rng.randf() * 12
			x.rect(hx - 4, hy, 8, 4, "#4a3a2e")
			x.poly([hx - 6, hy + 1, hx, hy - 4, hx + 6, hy + 1], "#232628")
			x.rect(hx - 1, hy + 1, 2, 2, "#ffc060")
	# pagoda at the monastery
	var mp2: Array = C.AREAS.monastery.mapPos
	var px2: float = mp2[0] * w
	var py2: float = mp2[1] * h
	for t in 4:
		x.rect(px2 - 6 + t, py2 - 6 - t * 6, 12 - t * 2, 5, "#2a2230")
		x.poly([px2 - 10 + t, py2 - 6 - t * 6, px2, py2 - 11 - t * 6, px2 + 10 - t, py2 - 6 - t * 6], "#141018")
	# stone bridge near town
	x.rect(60, 158, 26, 3, "#9a9e9a")
	# inked frame vignette
	for i in 6:
		var a := 0.12 - i * 0.018
		x.rect(i, i, w - i * 2, 1, Color(0, 0, 0, a * 3))
		x.rect(i, h - 1 - i, w - i * 2, 1, Color(0, 0, 0, a * 3))
		x.rect(i, i, 1, h - i * 2, Color(0, 0, 0, a * 3))
		x.rect(w - 1 - i, i, 1, h - i * 2, Color(0, 0, 0, a * 3))
	return x.texture()
