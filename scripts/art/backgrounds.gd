# Procedural parallax valley backgrounds, floors and back rails for each area theme.
class_name Backgrounds
extends RefCounted

const VIEW_H := 270
const BASE_Y := 180.0

const THEMES := {
	"town": {"sky": ["#324e5e", "#7fa4a4", "#b8c8b4"], "far": "#6d8e98", "far2": "#88a8ac", "mid": "#3d6452", "mid2": "#2c4c40", "water": "#3f8a8e", "water2": "#6ab8b4", "light": "#ffc060", "floor": "#6c706a", "floor2": "#5a5e58", "rail": "#7a7e76", "mist": "#d8e4dc"},
	"outskirts": {"sky": ["#2e4a5c", "#76a0a6", "#b4c8bc"], "far": "#688a96", "far2": "#86a6ac", "mid": "#3a6250", "mid2": "#2a4a3e", "water": "#3a8a90", "water2": "#6ab8b8", "light": "#ffc060", "floor": "#6a6c66", "floor2": "#575a54", "rail": "#767a72", "mist": "#d4e2dc"},
	"lantern": {"sky": ["#141428", "#3a2a4a", "#6a4058"], "far": "#2e3050", "far2": "#3e3a5a", "mid": "#23303a", "mid2": "#1a242c", "water": "#1e3448", "water2": "#3a5a7a", "light": "#ff9a40", "floor": "#5a5046", "floor2": "#4a4238", "rail": "#5e544a", "mist": "#6a5a78", "night": true, "lanterns": true},
	"bamboo": {"sky": ["#2c4a3e", "#6f9a80", "#b0cca8"], "far": "#5a8270", "far2": "#76a08a", "mid": "#2e5a3a", "mid2": "#224a2c", "water": "#3a7a6a", "water2": "#5aa890", "light": "#ffd070", "floor": "#5a5e44", "floor2": "#4a4e36", "rail": "#6a5a38", "mist": "#cfe4cc", "bamboo": true},
	"cloudrest": {"sky": ["#7a9ab4", "#bcd0dc", "#eef0ea"], "far": "#9ab0c0", "far2": "#b8c8d0", "mid": "#5a7a6a", "mid2": "#46645a", "water": "#6aa8c0", "water2": "#a8d8e8", "light": "#ffd890", "floor": "#8a8e8a", "floor2": "#767a76", "rail": "#9a9e98", "mist": "#f4f6f4", "blossom": true},
	"monastery": {"sky": ["#140e1c", "#34243e", "#5a3a58"], "far": "#2a2236", "far2": "#3a2e46", "mid": "#1e1a26", "mid2": "#16121c", "water": "#241e36", "water2": "#4a3a6a", "light": "#c070ff", "floor": "#48444c", "floor2": "#3a363e", "rail": "#4e4a54", "mist": "#5a4a6a", "night": true, "wind": true},
	"trial": {"sky": ["#041a1a", "#0c3a36", "#1a6a5a"], "far": "#0e4a44", "far2": "#16605a", "mid": "#0a3a34", "mid2": "#08302a", "water": "#1a8a78", "water2": "#5fe0c8", "light": "#9ff0e0", "floor": "#1e5a50", "floor2": "#164a42", "rail": "#2a7a6a", "mist": "#5fe0c8", "night": true},
}


static func theme(id: String) -> Dictionary:
	return THEMES.get(id, THEMES.town)


static func _sh(c, k: float) -> Color:
	return Painter.shade(c, k)


static func _mix(a, b, t: float) -> Color:
	return Painter.mix(a, b, t)


# Dithered banded sky gradient.
static func _sky(x: Painter, stops: Array) -> void:
	var bands := 18
	for y in x.h:
		var t := float(y) / x.h
		var a = stops[0] if t < 0.5 else stops[1]
		var b = stops[1] if t < 0.5 else stops[2]
		var tt := t * 2.0 if t < 0.5 else (t - 0.5) * 2.0
		var q := floorf(tt * bands) / bands
		var frac := tt * bands - floorf(tt * bands)
		var c1 := _mix(a, b, q)
		var c2 := _mix(a, b, minf(1.0, q + 1.0 / bands))
		x.span(y, 0, x.w - 1, c1)
		if frac > 0.5:
			for xx in range(y % 2, x.w, 2):
				x.img.set_pixel(xx, y, c2)


static func _karst(x: Painter, cx: float, base: float, w: float, h: float, c, rng: RandomNumberGenerator, trees) -> void:
	x.bezier_shape([cx - w, base,
		cx - w * 0.9, base - h * 0.6, cx - w * 0.55, base - h * 1.02, cx - w * 0.1, base - h,
		cx + w * 0.4, base - h * 0.98, cx + w * 0.7, base - h * 0.55, cx + w, base], c)
	for i in int(w / 3):
		var sx := cx - w * 0.6 + rng.randf() * w * 1.2
		var sy := base - h * (0.2 + rng.randf() * 0.55)
		x.rect(sx, sy, 1, 6 + rng.randf() * 14, _sh(c, -0.12))
	if trees != null:
		for i in int(w / 2.5):
			x.circ(cx - w * 0.5 + rng.randf() * w, base - h * (0.74 + rng.randf() * 0.26), 1.5 + rng.randf() * 2.5, trees)


static func _pagoda(x: Painter, cx: float, by: float, w: float, tiers: int, wall, roof, light, rng: RandomNumberGenerator) -> void:
	var y := by
	var ww := w
	for t in tiers:
		var th := 7.0 + (tiers - t)
		x.rect(cx - ww / 2, y - th, ww, th, wall)
		for i in int(ww / 4):
			if rng.randf() < 0.7:
				x.rect(cx - ww / 2 + 1.5 + i * 4, y - th + 2, 2, 3, light)
		y -= th
		var ew := ww / 2 + 5
		x.poly([cx - ew - 2, y + 1, cx - ew, y - 1, cx - ww / 2 + 1, y - 4, cx + ww / 2 - 1, y - 4, cx + ew, y - 1, cx + ew + 2, y + 1, cx + ww / 2, y - 1, cx - ww / 2, y - 1], roof)
		y -= 4
		ww *= 0.78
	x.line(cx, y, cx, y - 5, 1, roof)


static func _house(x: Painter, cx: float, by: float, w: float, h: float, wall, roof, light, rng: RandomNumberGenerator) -> void:
	x.rect(cx - w / 2, by - h, w, h, wall)
	for i in int(w / 6):
		x.rect(cx - w / 2 + 2 + i * 6, by - h + 3, 3, 4, light if rng.randf() < 0.65 else _sh(wall, -0.3))
	x.poly([cx - w / 2 - 5, by - h + 1, cx - w / 2 + 2, by - h - 6, cx + w / 2 - 2, by - h - 6, cx + w / 2 + 5, by - h + 1], roof)
	x.rect(cx - w / 2 - 1, by - 2, w + 2, 2, _sh(wall, -0.35))


# Returns {layers: [{tex, f, fy, falls?}], theme}
static func build(theme_id: String, level_w: int, view_w: int, seed_n := 7) -> Dictionary:
	var T := theme(theme_id)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_n * 131 + level_w
	var layers := []
	var night: bool = T.get("night", false)
	# sky
	var sky := Painter.new(view_w, VIEW_H)
	_sky(sky, T.sky)
	if night:
		for i in 110:
			sky.px(rng.randf() * view_w, rng.randf() * 110, "#ffffff" if rng.randf() < 0.3 else "#a8a8c8")
		sky.circ(view_w * 0.8, 40, 12, "#f0e8d0"); sky.circ(view_w * 0.8 + 4, 37, 11, T.sky[0])
	else:
		sky.circ(view_w * 0.2, 58, 16, _mix(T.sky[2], "#ffffff", 0.5))
	for i in 8:
		var cx := rng.randf() * view_w
		var cy := 30 + rng.randf() * 70
		for j in 5:
			sky.ell(cx + j * 9 - 18, cy + (rng.randf() - 0.5) * 4, 10 + rng.randf() * 8, 3 + rng.randf() * 2, _mix(T.sky[1], T.mist, 0.5))
	layers.append({"tex": sky.texture(), "f": 0.0, "fy": 0.02})
	# far peaks
	var fw := int(view_w + (level_w - view_w) * 0.06) + 40
	var far := Painter.new(fw, VIEW_H)
	for i in int(fw / 40.0) + 1:
		_karst(far, i * 40 + rng.randf() * 30, 150, 18 + rng.randf() * 20, 60 + rng.randf() * 70, _mix(T.far2, T.sky[1], 0.35), rng, null)
	for i in int(fw / 34.0) + 1:
		_karst(far, i * 34 + rng.randf() * 30, 160, 14 + rng.randf() * 18, 40 + rng.randf() * 60, T.far, rng, _sh(T.far, -0.1))
	far.rect(0, 128, fw, 34, Color(Painter.col(T.mist), 0.45))
	layers.append({"tex": far.texture(), "f": 0.06, "fy": 0.05})
	# mid cliffs with pagodas + waterfalls
	var mw := int(view_w + (level_w - view_w) * 0.2) + 40
	var mid := Painter.new(mw, VIEW_H)
	var falls := []
	for i in int(mw / 70.0) + 1:
		var cx := i * 70 + rng.randf() * 40
		var h := 70 + rng.randf() * 60
		var ww := 24 + rng.randf() * 26
		_karst(mid, cx, 172, ww, h, T.mid, rng, _sh(T.mid, 0.12))
		if rng.randf() < 0.55:
			_pagoda(mid, cx - 4, 172 - h * 0.62, 14 + rng.randf() * 8, 2 + rng.randi() % 3, _sh(T.mid2, -0.2), "#1a1418" if night else "#2a2a2e", T.light, rng)
		if rng.randf() < 0.5:
			var fx := cx + ww * 0.2
			var fy := 172 - h * 0.55
			var fh := h * 0.5
			mid.rect(fx, fy, 4, fh, _mix(T.water2, "#ffffff", 0.5)); mid.rect(fx + 1, fy, 1, fh, "#ffffff")
			falls.append(Rect2(fx, fy, 4, fh))
		for k in 3:
			if rng.randf() < 0.6:
				_house(mid, cx + (rng.randf() - 0.5) * ww, 172 - h * (0.15 + rng.randf() * 0.35), 10 + rng.randf() * 8, 5 + rng.randf() * 4, _sh(T.mid2, -0.15), "#262628", T.light, rng)
	mid.rect(0, 150, mw, 30, Color(Painter.col(T.mist), 0.35))
	if T.get("blossom", false):
		for i in int(mw / 6.0):
			mid.circ(rng.randf() * mw, 90 + rng.randf() * 70, 1.5 + rng.randf() * 2, "#f4eef0" if rng.randf() < 0.5 else "#f0d8e4")
	layers.append({"tex": mid.texture(), "f": 0.2, "fy": 0.12, "falls": falls})
	# near: river, bridge, docks / bamboo
	var nw := int(view_w + (level_w - view_w) * 0.42) + 40
	var near := Painter.new(nw, VIEW_H)
	var water_top := 138.0
	if T.get("bamboo", false):
		for i in int(nw / 5.0):
			var bx := rng.randf() * nw
			var bw := 2 + rng.randf() * 3
			var c := _mix(T.mid, "#9ac070", rng.randf() * 0.5)
			near.rect(bx, 20 + rng.randf() * 40, bw, 170, c)
			for j in 6:
				near.rect(bx - 0.5, 40 + j * 22 + rng.randf() * 8, bw + 1, 1.5, _sh(c, -0.3))
			if rng.randf() < 0.4:
				for l in 4:
					near.ell(bx + (rng.randf() - 0.3) * 12, 30 + rng.randf() * 80 + l * 5, 6, 1.4, _sh(c, 0.1), (rng.randf() - 0.5) * 0.8)
		near.rect(0, water_top + 6, nw, 40, T.water)
	else:
		near.rect(0, water_top, nw, 50, T.water)
		for i in int(nw / 3.0):
			near.rect(rng.randf() * nw, water_top + 2 + rng.randf() * 34, 3 + rng.randf() * 8, 1, T.water2)
		for i in int(nw / 46.0) + 1:
			var hx := i * 46 + rng.randf() * 20
			if rng.randf() < 0.7:
				_house(near, hx, water_top + 2, 18 + rng.randf() * 16, 10 + rng.randf() * 8, "#3a2a24" if night else "#4a3a2e", "#161214" if night else "#23262a", T.light, rng)
			if rng.randf() < 0.18:
				_pagoda(near, hx, water_top + 2, 16, 3, "#3a2e28", "#1e2024", T.light, rng)
			if rng.randf() < 0.5:
				for k in 4:
					near.rect(hx - 2 + rng.randf() * 6, water_top + 5 + k * 5, 3, 1, T.light)
		for i in int(nw / 700.0) + 1:
			var bx := 180 + i * 700 + rng.randf() * 200
			near.rect(bx, water_top - 12, 150, 6, "#7a7e7a")
			for a in 3:
				var ax := bx + 18 + a * 44
				near.poly([ax - 2, water_top - 6, ax + 26, water_top - 6, ax + 26, water_top + 8, ax - 2, water_top + 8], "#6a6e6a")
				near.ell(ax + 12, water_top + 8, 10, 10, T.water)
			for k in 19:
				near.rect(bx + k * 8, water_top - 16, 1.5, 4, "#8a8e8a")
			near.rect(bx, water_top - 16, 150, 1.5, "#9a9e9a")
			for k in 4:
				near.circ(bx + 10 + k * 42, water_top - 19, 1.5, T.light)
		for i in int(nw / 260.0) + 1:
			var bx2 := rng.randf() * nw
			var by := water_top + 12 + rng.randf() * 20
			near.poly([bx2 - 10, by, bx2 + 12, by, bx2 + 8, by + 4, bx2 - 7, by + 4], "#3a2418"); near.rect(bx2 - 3, by - 6, 8, 6, "#5a3a24")
			if rng.randf() < 0.5:
				near.line(bx2 + 2, by, bx2 + 2, by - 22, 1, "#3a2418"); near.poly([bx2 + 3, by - 21, bx2 + 14, by - 8, bx2 + 3, by - 6], "#c8b890")
	if T.get("wind", false):
		for i in int(nw / 8.0):
			near.line(rng.randf() * nw, 60 + rng.randf() * 110, rng.randf() * nw, 60 + rng.randf() * 110, 1, Color(0.54, 0.42, 0.69, 0.25))
	if T.get("lanterns", false):
		for i in int(nw / 30.0):
			var lx := rng.randf() * nw
			var ly := 40 + rng.randf() * 70
			near.line(lx, ly - 8, lx, ly - 2, 1, "#2a1a1a"); near.ell(lx, ly, 2.2, 2.8, "#e04030"); near.rect(lx - 0.5, ly - 1, 1, 2, "#ffd070")
	layers.append({"tex": near.texture(), "f": 0.42, "fy": 0.25})
	return {"layers": layers, "theme": T}


# Floor strip for the whole level: stone slabs in perspective rows, moss, cracks.
static func floor_tex(theme_id: String, level_w: int, seed_n := 3) -> ImageTexture:
	var T := theme(theme_id)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_n * 97 + level_w
	var h := int(VIEW_H - BASE_Y + 30)
	var x := Painter.new(level_w, h)
	x.rect(0, 0, level_w, h, T.floor2)
	var y := 0.0
	var row := 0
	var bamboo: bool = T.get("bamboo", false)
	while y < h:
		var rh := 7.0 + row * 1.6
		var xx := -rng.randf() * 20
		var sw := 22.0 + row * 3
		while xx < level_w:
			var ww := sw * (0.8 + rng.randf() * 0.5)
			var c := _mix(T.floor, _sh(T.floor, 0.08 if rng.randf() < 0.5 else -0.08), rng.randf())
			x.rect(xx + 1, y + 1, ww - 1, rh - 1, c)
			x.rect(xx + 1, y + 1, ww - 1, 1, _sh(c, 0.12))
			if rng.randf() < 0.18:
				x.rect(xx + 3 + rng.randf() * (ww - 8), y + 2 + rng.randf() * (rh - 4), 2 + rng.randf() * 4, 1, _sh(c, -0.25))
			if rng.randf() < (0.35 if bamboo else 0.12):
				x.circ(xx + rng.randf() * ww, y + rh - 1, 1 + rng.randf() * 1.5, "#4a7a34" if bamboo else "#4a6a3a")
			xx += ww
		y += rh
		row += 1
	if theme_id == "trial":
		for i in level_w / 10:
			x.px(rng.randf() * level_w, rng.randf() * h, "#9ff0e0")
	x.rect(0, 0, level_w, 3, Color(0, 0, 0, 0.25))
	return x.texture()


# Balustrade along depth 0, with gaps (little piers) at fishing spots.
static func rail(theme_id: String, level_w: int, gaps: Array) -> Dictionary:
	var T := theme(theme_id)
	var h := 24
	var x := Painter.new(level_w, h)
	var lanterns := []
	var wood := theme_id == "bamboo"
	var dark := theme_id == "monastery"
	var in_gap := func(px: float) -> bool:
		for g in gaps:
			if absf(px - g) < 22:
				return true
		return false
	var hi := _sh(T.rail, 0.15)
	var lo := _sh(T.rail, -0.18)
	var baluster: Color = Painter.col("#7a6a3a") if wood else Painter.col(T.rail)
	var seg_start := -1
	for px in level_w + 1:
		var gap: bool = px == level_w or in_gap.call(px)
		if not gap and seg_start < 0:
			seg_start = px
		if gap and seg_start >= 0:
			x.rect(seg_start, 4, px - seg_start, 3, hi)
			x.rect(seg_start, h - 6, px - seg_start, 6, lo)
			for bx in range(seg_start, px):
				if bx % 64 < 6:
					x.rect(bx, 2, 1, h - 2, _sh(T.rail, 0.2) if bx % 64 < 1 else _sh(T.rail, -0.1))
				elif not dark and bx % 8 < 3:
					x.rect(bx, 7, 1, h - 13, baluster)
				elif dark:
					x.rect(bx, 7, 1, h - 13, _sh(T.rail, -0.05))
			seg_start = -1
	for px in range(32, level_w, 192):
		if in_gap.call(px):
			continue
		x.rect(px - 3, 0, 7, h, _sh(T.rail, -0.05)); x.rect(px - 4, 0, 9, 3, _sh(T.rail, 0.2))
		lanterns.append(px)
	for g in gaps:
		x.rect(g - 20, h - 6, 40, 6, "#5a3a24")
		for i in 5:
			x.rect(g - 20 + i * 8, h - 6, 1, 6, "#3a2418")
	return {"tex": x.texture(), "lanterns": lanterns}
