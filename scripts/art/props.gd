# Pre-rendered props: raised decks/stairs, stations, resource nodes, portals and runes.
class_name Props
extends RefCounted

const OUT := "#120c0a"
static var _cache := {}


static func _sh(c, k: float) -> Color:
	return Painter.shade(c, k)


# Deck sprite: top face (depth span) + solid front face, or a bridge slab with pillars.
# Place at screen (x0, BASE_Y + d0 - maxH - top).
static func deck(s: Dictionary, theme_id: String) -> Dictionary:
	var k := "deck|%s|%s" % [s.id, theme_id]
	if _cache.has(k):
		return _cache[k]
	var T := Backgrounds.theme(theme_id)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(s.x0) * 7 + int(s.d0)
	var w := int(s.x1 - s.x0)
	var dh := int(s.d1 - s.d0)
	var top := 12
	var out: Dictionary
	if s.kind == "stair":
		out = _stair(s, T, top)
	else:
		var H := int(s.h0)
		var x := Painter.new(w, top + dh + H)
		var style: String = s.style
		var plank: Color
		match style:
			"roof": plank = Painter.col("#b58e5c")
			"bridge": plank = Painter.col("#b89868")
			"jade": plank = Painter.col("#2a8a78")
			_: plank = Painter.mix(T.floor, "#c8c0a8", 0.35)
		x.rect(0, top, w, dh, plank)
		if style == "stone" or style == "jade":
			var yy := 0
			while yy < dh:
				var xx := -8 if (yy / 7) % 2 else 0
				while xx < w:
					x.rect(xx, top + yy, 15, 6, plank if rng.randf() < 0.5 else _sh(plank, 0.06))
					x.rect(xx, top + yy, 15, 1, _sh(plank, 0.14))
					xx += 16
				yy += 7
		else:
			for xx in range(0, w, 6):
				x.rect(xx, top, 1, dh, _sh(plank, -0.14))
				if rng.randf() < 0.2:
					x.rect(xx + 2, top + rng.randf() * dh, 2, 1, _sh(plank, 0.2))
			x.rect(0, top, w, 1, _sh(plank, 0.25))
		if s.rails.back:
			var rc := "#7a4a2a" if style == "bridge" else "#6a4a2a"
			for xx in range(2, w, 10):
				x.rect(xx, top - 7, 2, 8, rc)
			x.rect(0, top - 8, w, 2, "#9a5a30" if style == "bridge" else "#7a5a34")
		var fy := top + dh
		if s.solid:
			var face: Color = Painter.col("#4a2e22") if style == "roof" else (Painter.col("#185a50") if style == "jade" else _sh(T.floor, -0.22))
			x.rect(0, fy, w, H, face)
			if style == "roof":
				x.rect(0, fy, w, 5, "#2a2a30")
				for xx in range(0, w, 4):
					x.rect(xx, fy + 4, 3, 2, "#3a3a42")
				for xx in range(8, w, 30):
					x.rect(xx, fy + 6, 4, H - 6, "#6a2a1e")
				for xx in range(18, w - 10, 30):
					var wh := mini(12, H - 18)
					if wh > 2:
						x.rect(xx, fy + 12, 10, wh, T.light); x.rect(xx + 4, fy + 12, 1, wh, "#6a2a1e")
			else:
				var yy2 := fy + 2
				while yy2 < fy + H:
					var xx2 := -10 if ((yy2 - fy) / 8) % 2 else 0
					while xx2 < w:
						x.rect(xx2 + 1, yy2, 18, 7, face if rng.randf() < 0.5 else _sh(face, 0.08))
						x.rect(xx2 + 1, yy2, 18, 1, _sh(face, 0.18))
						xx2 += 20
					yy2 += 8
				if T.get("bamboo", false):
					for i in w / 10:
						x.circ(rng.randf() * w, fy + rng.randf() * H, 1.5, "#3a6a2a")
			x.rect(0, fy, w, 1, _sh(plank, 0.3))
		else:
			x.rect(0, fy, w, 6, "#5a3a24"); x.rect(0, fy + 5, w, 2, "#3a2418")
			for xx in range(30, w - 10, 90):
				x.rect(xx, fy + 6, 7, H - 6, "#6a6e6a"); x.rect(xx, fy + 6, 2, H - 6, "#8a8e8a")
			x.rect(0, top, w, 3, Color(0, 0, 0, 0.25))
		if s.rails.front:
			for xx in range(2, w, 10):
				x.rect(xx, fy - 6, 2, 7, "#7a4a2a")
			x.rect(0, fy - 7, w, 2, "#b06a38")
			for xx in range(40, w, 120):
				x.ell(xx, fy - 12, 2.5, 3, "#e04030"); x.rect(xx - 0.5, fy - 13, 1, 2, "#ffd070")
		out = {"tex": x.texture(), "top": top, "maxh": H}
	_cache[k] = out
	return out


static func _stair(s: Dictionary, T: Dictionary, top: int) -> Dictionary:
	var w := int(s.x1 - s.x0)
	var dh := int(s.d1 - s.d0)
	var H := int(maxf(s.h0, s.h1))
	var x := Painter.new(w, top + dh + H)
	var n := maxi(3, int(round(w / 7.0)))
	var up: bool = s.h1 > s.h0
	var stone: Color = Painter.mix(T.floor, "#c8c0a8", 0.3) if s.style == "stone" else Painter.col("#a88858")
	for i in n:
		var t := (i + 0.5) / n
		var hh: float = lerpf(s.h0, s.h1, t)
		var sx := float(i) / n * w
		var sw := float(w) / n + 1
		var ty := top + H - hh
		x.rect(sx, ty, sw, dh, _sh(stone, (i % 2) * 0.05))
		x.rect(sx, ty, sw, 1, _sh(stone, 0.22))
		x.rect(sx, ty + dh, sw, hh, _sh(stone, -0.28))
		x.rect(sx if up else sx + sw - 1, ty, 1, dh, _sh(stone, -0.15))
	if s.rails.front:
		x.line(0.0 if up else float(w), top + H - s.h0 + dh - 6, float(w) if up else 0.0, top + H - maxf(s.h0, s.h1) + dh - 6, 1.5, "#7a4a2a")
	return {"tex": x.texture(), "top": top, "maxh": H}


# ---------------------------------------------------------------- stations
static func station(type: String) -> Dictionary:
	var k := "st|" + type
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(64, 64)
	var ax := 32.0
	var ay := 62.0
	match type:
		"shrine", "rest":
			var big := type == "shrine"
			var b1 := 32.0 if big else 24.0
			x.rect(ax - 14, ay - 6, 28, 6, "#6a6e6a"); x.rect(ax - 12, ay - 8, 24, 3, "#8a8e8a")
			x.rect(ax - 8, ay - b1, 16, b1 - 8, "#7a7e7a")
			x.rect(ax - 5, ay - b1 + 4, 10, 8, "#1a3a34")
			x.circ(ax, ay - b1 + 8, 2.5, "#5fe0c8")
			x.poly([ax - 15, ay - b1, ax, ay - b1 - (12 if big else 9), ax + 15, ay - b1], "#2a2a30")
			x.poly([ax - 12, ay - b1 - 1, ax, ay - b1 - (9 if big else 7), ax + 12, ay - b1 - 1], "#3a3a44")
			if big:
				x.line(ax - 20, ay - 2, ax - 20, ay - 30, 2, "#9c2a2a"); x.rect(ax - 24, ay - 30, 8, 12, "#9c2a2a"); x.rect(ax - 22, ay - 27, 4, 5, "#d9b25c")
			else:
				x.line(ax + 13, ay - 8, ax + 13, ay - 16, 1, "#a88858"); x.circ(ax + 13, ay - 17, 1, "#ff8040")
		"forge":
			x.rect(ax - 20, ay - 36, 26, 36, "#6a4a3a")
			for yy in range(int(ay) - 34, int(ay), 5):
				for xx in range(int(ax) - 20 + ((yy / 5) % 2) * 3, int(ax) + 6, 6):
					x.rect(xx, yy, 5, 4, "#7a5a44" if yy % 10 else "#5a3a2e")
			x.rect(ax - 14, ay - 18, 14, 12, "#1a0a06"); x.rect(ax - 12, ay - 14, 10, 8, "#ff7020"); x.rect(ax - 10, ay - 12, 6, 5, "#ffd040")
			x.rect(ax - 16, ay - 46, 10, 10, "#4a3a34")
			x.poly([ax + 8, ay - 14, ax + 26, ay - 14, ax + 28, ay - 17, ax + 6, ay - 17], "#8a949c"); x.rect(ax + 12, ay - 14, 8, 8, "#50585e"); x.rect(ax + 9, ay - 6, 14, 6, "#3a4046")
			x.line(ax + 24, ay - 24, ax + 18, ay - 18, 2, "#8a5a2e"); x.rect(ax + 22, ay - 28, 6, 4, "#aab4bc")
		"furnace":
			x.line(ax - 12, ay, ax - 8, ay - 10, 2.5, "#6a4a2a"); x.line(ax + 12, ay, ax + 8, ay - 10, 2.5, "#6a4a2a"); x.line(ax, ay, ax, ay - 10, 2.5, "#6a4a2a")
			x.ell(ax, ay - 20, 16, 12, "#a8742e"); x.ell(ax, ay - 24, 14, 5, "#c89040"); x.ell(ax, ay - 25, 10, 3, "#3a2a1a")
			x.rect(ax - 17, ay - 22, 34, 2, "#d9b25c"); x.circ(ax, ay - 16, 3, "#6a4a1a"); x.rect(ax - 6, ay - 10, 12, 4, "#ff7020")
		"research":
			x.rect(ax - 18, ay - 16, 36, 4, "#6a3a1e"); x.rect(ax - 16, ay - 12, 3, 12, "#4a2a14"); x.rect(ax + 13, ay - 12, 3, 12, "#4a2a14")
			x.rect(ax - 14, ay - 22, 10, 6, "#e8d8a8"); x.rect(ax - 14, ay - 22, 10, 1, "#8a5a2e"); x.rect(ax - 2, ay - 24, 8, 8, "#3a78d8"); x.rect(ax - 1, ay - 26, 6, 3, "#d9b25c")
			x.rect(ax + 8, ay - 26, 6, 10, "#8a3a1e"); x.rect(ax + 9, ay - 25, 4, 8, "#b85a2e")
		"chest":
			x.rect(ax - 14, ay - 16, 28, 16, "#7a4a24"); x.rect(ax - 14, ay - 20, 28, 6, "#8a5a2e"); x.rect(ax - 14, ay - 15, 28, 2, "#d9b25c"); x.rect(ax - 2, ay - 16, 4, 5, "#d9b25c")
			x.rect(ax - 14, ay - 20, 2, 20, "#d9b25c"); x.rect(ax + 12, ay - 20, 2, 20, "#d9b25c")
		"shop":
			x.rect(ax - 24, ay - 14, 48, 14, "#6a3a1e"); x.rect(ax - 24, ay - 16, 48, 3, "#8a5a2e")
			x.line(ax - 22, ay - 16, ax - 22, ay - 44, 2, "#4a2a14"); x.line(ax + 22, ay - 16, ax + 22, ay - 44, 2, "#4a2a14")
			for i in 8:
				x.poly([ax - 26 + i * 6.5, ay - 44, ax - 20 + i * 6.5, ay - 44, ax - 20 + i * 6.5, ay - 38, ax - 23 + i * 6.5, ay - 36, ax - 26 + i * 6.5, ay - 38], "#e8e0cc" if i % 2 else "#b03030")
			var goods := ["#d8453a", "#3a78d8", "#e8b03a", "#5fbf4a", "#b58ae8"]
			for i in 5:
				x.rect(ax - 20 + i * 8, ay - 22, 5, 6, goods[i]); x.rect(ax - 19 + i * 8, ay - 24, 3, 2, "#d9b25c")
			x.ell(ax - 12, ay - 32, 3, 4, "#e04030"); x.ell(ax + 12, ay - 32, 3, 4, "#e04030")
		"board":
			x.line(ax - 14, ay, ax - 14, ay - 34, 3, "#5a3a24"); x.line(ax + 14, ay, ax + 14, ay - 34, 3, "#5a3a24")
			x.rect(ax - 17, ay - 36, 34, 24, "#7a5a34"); x.rect(ax - 15, ay - 34, 30, 20, "#5a3a24")
			x.rect(ax - 13, ay - 32, 9, 11, "#e8d8a8"); x.rect(ax - 2, ay - 31, 8, 9, "#f0e0b8"); x.rect(ax + 8, ay - 33, 6, 12, "#e8d8a8"); x.rect(ax - 10, ay - 30, 3, 1, "#b03030")
			x.poly([ax - 20, ay - 36, ax, ay - 44, ax + 20, ay - 36], "#2a2a30")
		"seal":
			x.ell(ax, ay - 4, 22, 5, "#5a5e5a"); x.ell(ax, ay - 6, 18, 4, "#7a7e7a")
			x.rect(ax - 8, ay - 26, 16, 20, "#6a6e6a"); x.rect(ax - 10, ay - 28, 20, 4, "#8a8e8a")
			x.arc(ax, ay - 16, 5, 0, 6.3, 1.4, "#3fd1b0"); x.rect(ax + 12, ay - 22, 10, 16, "#8a8e8a")
			for i in 4:
				x.rect(ax + 14, ay - 20 + i * 3.5, 6, 1, "#303438")
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": ax, "ay": ay}
	_cache[k] = out
	return out


# ---------------------------------------------------------------- nodes
static func node(sprite: String, tint, ready: bool) -> Dictionary:
	var k := "nd|%s|%s|%s" % [sprite, str(tint), ready]
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(32, 32)
	match sprite:
		"vein":
			x.poly([3, 30, 6, 18, 14, 12, 24, 14, 29, 22, 29, 30], "#5a5a5e"); x.poly([6, 18, 14, 12, 24, 14, 18, 18], "#7a7a80")
			if ready:
				for q in [[12, 20, 3.0], [20, 23, 2.6], [15, 26, 2.0], [23, 18, 2.0]]:
					x.circ(q[0], q[1], q[2], tint); x.circ(q[0] - 0.8, q[1] - 0.8, q[2] * 0.45, _sh(tint, 0.5))
		"crystal":
			x.poly([6, 30, 10, 26, 24, 26, 27, 30], "#4a4a50")
			if ready:
				x.poly([9, 27, 8, 16, 12, 8, 15, 16, 14, 27], _sh(tint, -0.15)); x.poly([15, 27, 16, 12, 21, 4, 25, 13, 23, 27], tint)
				x.poly([21, 4, 25, 13, 21, 14], _sh(tint, 0.55)); x.poly([12, 8, 15, 16, 12, 17], _sh(tint, 0.5))
			else:
				x.poly([12, 27, 13, 22, 17, 21, 18, 27], _sh(tint, -0.5))
		"herb":
			x.ell(16, 29, 10, 2.5, "#3a2a1a")
			if ready:
				for i in 6:
					x.ell(8 + i * 3.2, 22 - (i % 2) * 4, 3.5, 7, "#4fa83a" if i % 2 else "#3f8f30", (i - 2.5) * 0.25)
				for q in [[10, 13], [18, 11], [23, 16]]:
					x.circ(q[0], q[1], 2, "#f4f0e0"); x.px(q[0], q[1], "#e8c040")
			else:
				for i in 4:
					x.line(10 + i * 4, 29, 10 + i * 4, 26, 1.2, "#5a6a2a")
		"lotus":
			x.ell(16, 27, 14, 4, "#2a5a6a"); x.ell(10, 26, 7, 2.5, "#2f7a4a"); x.ell(22, 27, 6, 2.2, "#3a8a54")
			if ready:
				for q in [[-0.8, "#f0d0e0"], [0.8, "#f0d0e0"], [-0.4, "#fbf0f6"], [0.4, "#fbf0f6"], [0.0, "#ffffff"]]:
					x.ell(16 + q[0] * 6, 19, 2.6, 6, q[1], q[0])
				x.circ(16, 22, 1.6, "#e8c040")
		"ginseng":
			x.ell(16, 29, 9, 2.4, "#3a2a1a")
			if ready:
				x.line(16, 28, 16, 12, 1.2, "#3f7a2a")
				for q in [[10, 16, -0.5], [22, 15, 0.5], [12, 22, -0.3], [20, 22, 0.3]]:
					x.ell(q[0], q[1], 5, 2.2, "#4fa83a", q[2])
				for q in [[15, 9], [17, 8], [16, 11]]:
					x.circ(q[0], q[1], 1.6, "#d8453a")
			else:
				x.line(16, 28, 16, 24, 1.2, "#5a6a2a")
		"fish":
			x.ell(16, 26, 13, 4, "#5ab0c0" if ready else "#3a7a8a")
			if ready:
				x.arc(16, 26, 6, 3.4, 6.0, 1, "#dff8ff"); x.arc(16, 26, 10, 3.6, 5.8, 1, "#a8e0f0"); x.ell(20, 25, 3, 1.2, "#f0a050")
	if sprite != "fish":
		x.outline(OUT)
	var out := {"tex": x.texture(), "ax": 16.0, "ay": 30.0}
	_cache[k] = out
	return out


static func portal(locked: bool) -> Dictionary:
	var k := "portal|%s" % locked
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(48, 72)
	var ax := 24.0
	var ay := 70.0
	x.rect(ax - 20, ay - 60, 8, 60, "#7a7e7a"); x.rect(ax + 12, ay - 60, 8, 60, "#7a7e7a")
	x.rect(ax - 24, ay - 66, 48, 7, "#2a2a30"); x.rect(ax - 20, ay - 60, 40, 4, "#9c2a2a")
	x.ell(ax, ay - 30, 12, 28, "#2a2a34" if locked else "#3fd1b0")
	if not locked:
		x.ell(ax, ay - 30, 7, 22, "#bff5e6")
	else:
		x.arc(ax, ay - 34, 4, PI, TAU, 2, "#9aa3a8"); x.rect(ax - 5, ay - 34, 10, 8, "#c8ccd0")
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": ax, "ay": ay}
	_cache[k] = out
	return out


static func glyph(x: Painter, kind: String, cx: float, cy: float, c) -> void:
	match kind:
		"water":
			for i in 3:
				x.quad(cx - 5, cy - 4 + i * 4, cx, cy - 7 + i * 4, cx + 5, cy - 4 + i * 4, 1.4, c)
		"wood":
			x.line(cx, cy - 6, cx, cy + 6, 1.4, c); x.line(cx - 5, cy - 2, cx + 5, cy - 2, 1.4, c); x.line(cx, cy, cx - 5, cy + 5, 1.4, c); x.line(cx, cy, cx + 5, cy + 5, 1.4, c)
		"fire":
			x.poly([cx, cy - 7, cx + 5, cy + 4, cx, cy + 1, cx - 5, cy + 4], c)
		_:
			x.line(cx - 5, cy + 5, cx + 5, cy + 5, 1.6, c); x.line(cx, cy - 6, cx, cy + 5, 1.4, c); x.line(cx - 4, cy - 1, cx + 4, cy - 1, 1.4, c)


static func rune(kind: String, lit: bool) -> Dictionary:
	var k := "rune|%s|%s" % [kind, lit]
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(24, 32)
	x.poly([5, 31, 4, 12, 12, 3, 20, 12, 19, 31], "#4a7a70" if lit else "#6a6e6a")
	x.poly([5, 12, 12, 3, 12, 31, 5, 31], "#3a6a60" if lit else "#5a5e5a")
	glyph(x, kind, 12, 18, "#bff5e6" if lit else "#2a2e2e")
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": 12.0, "ay": 31.0}
	_cache[k] = out
	return out


static func glyph_tex(kind: String) -> Texture2D:
	var k := "glyph|" + kind
	if not _cache.has(k):
		var x := Painter.new(16, 16)
		glyph(x, kind, 8, 8, "#bff5e6")
		_cache[k] = x.texture()
	return _cache[k]
