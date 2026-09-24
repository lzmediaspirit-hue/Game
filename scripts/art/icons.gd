# Procedural pixel icons for items, skills and UI, painted at 32×32 and cached as textures.
class_name Icons
extends RefCounted

const C = preload("res://scripts/data/content.gd")
const OUT := "#0e0a07"
static var _cache := {}


static func get_icon(id: String, tint = null) -> Texture2D:
	var k := id + "|" + str(tint)
	if not _cache.has(k):
		var p := Painter.new(32, 32)
		_paint(p, id, tint)
		p.outline(OUT)
		_cache[k] = p.texture()
	return _cache[k]


static func item(id: String) -> Texture2D:
	var d: Dictionary = C.ITEMS.get(id, {})
	if d.is_empty():
		return get_icon("lock")
	return get_icon(d.icon, d.get("tint", null))


static func ability(id: String) -> Texture2D:
	return get_icon(C.ABILITIES[id].icon if C.ABILITIES.has(id) else "lock")


static func _sh(c, k: float) -> Color:
	return Painter.shade(c, k)


static func _leaf(x: Painter, cx: float, cy: float, r: float, c) -> void:
	x.ell(cx, cy, r, r / 2.2, c, -0.6)
	x.line(cx - r * 0.7, cy + r * 0.5, cx + r * 0.6, cy - r * 0.4, 0.9, _sh(c, -0.35))


static func _figure(x: Painter, pose: int) -> void:
	var c := "#101a1c"
	x.circ(12, 9, 3.4, c)
	if pose == 0:
		x.line(12, 12, 14, 20, 3.4, c); x.line(14, 20, 8, 28, 2.6, c); x.line(14, 20, 20, 27, 2.6, c); x.line(13, 14, 20, 14, 2.2, c)
	else:
		x.line(12, 12, 12, 21, 3.4, c); x.line(12, 21, 8, 28, 2.6, c); x.line(12, 21, 17, 28, 2.6, c); x.line(12, 14, 6, 18, 2.2, c); x.line(12, 14, 18, 18, 2.2, c)


static func _swoosh(x: Painter, c, kind: String) -> void:
	match kind:
		"arc":
			x.arc(14, 16, 12, -1.4, 1.2, 3.2, c); x.arc(14, 16, 12, -1.4, 1.2, 1.2, "#ffffff")
		"line":
			x.poly([10, 14, 31, 16, 10, 18], c); x.line(12, 16, 30, 16, 1, "#ffffff")
		"ring":
			x.arc(16, 16, 12, 0, 6.3, 2.6, c); x.arc(16, 16, 7, 0, 6.3, 1.4, "#ffffff")
		"wave":
			x.quad(8, 28, 22, 20, 24, 3, 4, c)


static func _pill(x: Painter, t) -> void:
	x.rect(8, 11, 16, 17, t); x.rect(8, 11, 4, 17, _sh(t, 0.3)); x.rect(7, 7, 18, 5, _sh(t, -0.35)); x.rect(11, 4, 10, 4, "#d9b25c")
	x.poly([16, 15, 20, 19, 16, 23, 12, 19], "#f0d890"); x.poly([16, 17, 18, 19, 16, 21, 14, 19], t)


static func _pick(x: Painter, t) -> void:
	x.line(6, 28, 20, 10, 2.6, "#7a4a22")
	x.quad(6, 10, 18, 2, 29, 12, 3.4, t)


static func _scroll(x: Painter) -> void:
	x.rect(7, 6, 18, 20, "#e8d8a8"); x.rect(5, 4, 22, 4, "#8a5a2e"); x.rect(5, 24, 22, 4, "#8a5a2e")
	for y in [11, 15, 19]:
		x.line(10, y, 22, y, 1, "#8a6a40")


static func _realm(x: Painter) -> void:
	for pr in [[-0.8, "#3fb89a"], [0.8, "#3fb89a"], [-0.4, "#6fe0c0"], [0.4, "#6fe0c0"], [0.0, "#bff5e6"]]:
		x.ell(16 + pr[0] * 8, 16, 4, 10, pr[1], pr[0])
	x.ell(16, 26, 11, 3, "#1f6b5a")


static func _paint(x: Painter, id: String, tint) -> void:
	var t = tint if tint != null else "#cfd8de"
	match id:
		"sword":
			x.line(7, 25, 24, 8, 3.2, _sh(t, -0.25)); x.line(7, 25, 23, 9, 1.2, _sh(t, 0.35))
			x.poly([24, 8, 27, 4, 26, 9], _sh(t, 0.3))
			x.line(5, 21, 11, 27, 2.6, "#d9b25c"); x.line(3, 29, 7, 25, 3, "#6b3a1e"); x.circ(3, 29, 1.8, "#d9b25c")
		"spear":
			x.line(3, 29, 22, 10, 2.4, "#7a4a22"); x.line(3, 29, 21, 11, 1, "#b07a3c")
			x.poly([20, 12, 29, 3, 24, 14], _sh(t, -0.15)); x.poly([21, 11, 29, 3, 23, 12], _sh(t, 0.35))
			x.rect(18, 12, 4, 3, "#d9b25c"); x.line(19, 14, 16, 20, 2, "#1f8a6e"); x.circ(16, 21, 1.8, "#1f8a6e")
		"hat":
			x.poly([2, 22, 16, 8, 30, 22], "#c9a45a"); x.poly([6, 20, 16, 10, 26, 20], "#e2c27a"); x.line(8, 20, 24, 20, 1, "#8a6a30"); x.rect(15, 22, 2, 7, "#1f8a6e")
		"crown":
			x.poly([6, 22, 8, 12, 12, 18, 16, 8, 20, 18, 24, 12, 26, 22], "#3fd1b0"); x.rect(6, 21, 20, 4, "#1f8a6e"); x.circ(16, 16, 2, "#d9b25c")
		"gourd":
			x.circ(16, 22, 8, "#b5652e"); x.circ(16, 11, 5, "#c7773a"); x.circ(13, 20, 2.5, _sh("#c7773a", 0.3)); x.rect(14, 3, 4, 4, "#6b3a1e"); x.line(10, 15, 22, 15, 2, "#c0392b")
		"pick":
			_pick(x, "#c9833f")
		"pick2":
			_pick(x, "#cfe0ea")
		"kit":
			x.rect(6, 12, 18, 14, "#8a5a2e"); x.rect(6, 12, 18, 4, "#a8733c"); x.arc(22, 10, 7, PI, PI * 1.9, 2.4, "#cfd8de"); _leaf(x, 10, 10, 5, "#5fbf4a")
		"rod":
			x.line(4, 29, 26, 4, 2, "#c9b26a"); x.line(26, 4, 28, 22, 1, "#e8e0cc"); x.ell(28, 24, 2, 3, "#d8453a")
		"ore":
			x.poly([4, 26, 8, 14, 16, 10, 22, 16, 20, 27], _sh(t, -0.25)); x.poly([8, 14, 16, 10, 22, 16, 13, 18], _sh(t, 0.25))
			x.poly([16, 27, 20, 16, 26, 12, 30, 20, 28, 28], _sh(t, -0.1)); x.poly([20, 16, 26, 12, 30, 20, 24, 19], _sh(t, 0.35))
			x.circ(11, 21, 1.2, _sh(t, 0.6)); x.circ(25, 23, 1, _sh(t, 0.6))
		"ingot":
			x.poly([3, 24, 8, 12, 26, 12, 30, 24], _sh(t, -0.2)); x.poly([8, 12, 26, 12, 24, 16, 10, 16], _sh(t, 0.35)); x.poly([3, 24, 10, 16, 24, 16, 30, 24], t); x.line(11, 19, 20, 19, 1, _sh(t, 0.5))
		"herb":
			x.line(16, 30, 16, 10, 1.6, "#3f7a2a"); _leaf(x, 11, 16, 7, "#4fa83a"); _leaf(x, 21, 12, 7, "#5fbf4a"); _leaf(x, 12, 24, 6, "#3f8f30"); x.circ(23, 6, 2.5, "#f2f0e0"); x.circ(23, 6, 1, "#e8c040")
		"lotus":
			x.ell(16, 26, 13, 4, "#2f7a4a")
			for pr in [[-0.9, "#f2e6ee"], [0.9, "#f2e6ee"], [-0.45, "#fbf4f8"], [0.45, "#fbf4f8"], [0.0, "#ffffff"]]:
				x.ell(16 + pr[0] * 9, 16, 4, 9, pr[1], pr[0])
			x.circ(16, 19, 3, "#e8c040")
		"ginseng":
			x.ell(16, 21, 5, 8, "#e0c08a"); x.line(13, 26, 8, 30, 1.6, "#c9a46a"); x.line(19, 26, 24, 30, 1.6, "#c9a46a"); x.line(16, 13, 16, 6, 1.2, "#3f7a2a")
			_leaf(x, 11, 7, 5, "#4fa83a"); _leaf(x, 21, 6, 5, "#5fbf4a"); x.circ(16, 4, 2, "#d8453a")
		"fish":
			x.ell(15, 17, 11, 6, t); x.ell(15, 19, 9, 3, _sh(t, 0.45)); x.poly([24, 17, 31, 10, 30, 24], _sh(t, -0.2)); x.circ(8, 15, 1.4, "#101010"); x.line(12, 12, 18, 11, 1, _sh(t, -0.3))
		"eel":
			x.bezier(3, 20, 10, 8, 18, 30, 29, 12, 5, t); x.bezier(3, 20, 10, 8, 18, 30, 29, 12, 1.5, _sh(t, 0.5)); x.circ(28, 12, 1.2, "#101010")
		"dust":
			x.ell(16, 25, 12, 5, "#b8d8f0"); x.poly([6, 25, 16, 10, 26, 25], "#d8eeff"); x.poly([11, 22, 16, 13, 20, 22], "#ffffff")
			for q in [[6, 8], [26, 6], [28, 16], [4, 16]]:
				x.rect(q[0], q[1], 1, 3, "#ffffff"); x.rect(q[0] - 1, q[1] + 1, 3, 1, "#ffffff")
		"hide":
			x.poly([4, 10, 10, 6, 22, 6, 28, 10, 26, 26, 20, 23, 12, 23, 6, 26], "#8a5a34"); x.poly([8, 11, 12, 9, 20, 9, 24, 11, 22, 20, 10, 20], "#a8744a")
		"core":
			x.circ(16, 16, 10, "#5a1e6e"); x.circ(16, 16, 7, "#b04adf"); x.circ(13, 13, 3, "#f0c8ff")
		"crystal":
			x.poly([10, 28, 7, 14, 12, 4, 17, 14, 15, 28], _sh(t, -0.15)); x.poly([12, 4, 17, 14, 12, 16], _sh(t, 0.5))
			x.poly([16, 28, 17, 12, 22, 7, 27, 14, 24, 28], t); x.poly([22, 7, 27, 14, 22, 15], _sh(t, 0.55))
			x.poly([3, 28, 5, 20, 8, 18, 10, 28], _sh(t, -0.3)); x.poly([24, 28, 27, 20, 30, 22, 29, 28], _sh(t, -0.3))
		"pill":
			_pill(x, t)
		"potion":
			_pill(x, "#3a9ad8")
		"fragment":
			x.poly([6, 8, 18, 4, 26, 12, 22, 28, 8, 24], "#3a8a7a"); x.poly([9, 10, 17, 7, 22, 13, 16, 16], "#6fe0c8"); x.line(12, 18, 18, 24, 1, "#d9b25c")
		"coin":
			x.circ(16, 16, 12, "#b8862e"); x.circ(16, 16, 10, "#e8b84a"); x.circ(13, 13, 4, "#f8e090"); x.rect(13, 13, 6, 6, "#b8862e"); x.rect(14, 14, 4, 4, "#e8b84a")
		"insight":
			x.circ(16, 16, 12, "#1a3a4a"); x.arc(16, 16, 9, 0, 4.5, 3, "#9fdcff"); x.arc(16, 16, 4, 3, 7, 2.5, "#ffffff")
		"meridian":
			x.poly([16, 3, 29, 16, 16, 29, 3, 16], "#1a3a3a")
			var q := [16, 5, 27, 16, 16, 27, 5, 16, 16, 5]
			x.polyline(q, 1, "#3fd1b0")
			for i in 4:
				x.circ(q[i * 2], q[i * 2 + 1], 3, "#3fd1b0")
		"essence":
			x.circ(16, 18, 9, "#1f6b8a"); x.poly([16, 3, 24, 16, 16, 27, 8, 16], "#5fd8f0"); x.poly([16, 7, 20, 16, 16, 22, 12, 16], "#e0fbff")
		"lock":
			x.arc(16, 13, 6, PI, TAU, 3, "#9aa3a8"); x.rect(7, 13, 18, 14, "#c8ccd0"); x.rect(7, 13, 18, 3, "#e8ecf0"); x.rect(15, 18, 2, 5, "#303438")
		"map":
			x.poly([3, 7, 11, 4, 21, 7, 29, 4, 29, 26, 21, 29, 11, 26, 3, 29], "#e8d8a8"); x.poly([11, 4, 21, 7, 21, 29, 11, 26], "#d8c890")
			x.bezier(5, 20, 12, 10, 18, 26, 27, 10, 2, "#3a9ad8"); x.circ(22, 12, 2, "#d8453a"); x.poly([6, 10, 9, 6, 12, 10], "#3f8f5a")
		"menu":
			for y in [8, 15, 22]:
				x.rect(5, y, 4, 4, "#e8e0cc"); x.rect(11, y, 16, 4, "#e8e0cc")
		"bag":
			x.ell(16, 20, 11, 9, "#8a5a2e"); x.rect(8, 9, 16, 8, "#a8733c"); x.arc(16, 9, 5, PI, TAU, 2, "#6b3a1e"); x.rect(13, 15, 6, 5, "#d9b25c")
		"book":
			x.rect(5, 5, 22, 23, "#8a3a1e"); x.rect(8, 5, 19, 21, "#e8d8a8"); x.rect(5, 5, 4, 23, "#6b2a12")
			x.circ(18, 12, 3, "#3a2a1a"); x.line(18, 14, 18, 21, 2.4, "#3a2a1a"); x.line(18, 17, 14, 14, 1.6, "#3a2a1a"); x.line(18, 17, 22, 19, 1.6, "#3a2a1a"); x.line(18, 21, 15, 25, 1.6, "#3a2a1a"); x.line(18, 21, 21, 25, 1.6, "#3a2a1a")
		"journal":
			x.rect(5, 4, 22, 24, "#8a5a2e"); x.rect(7, 6, 18, 20, "#c8a060"); x.poly([12, 12, 16, 8, 20, 12, 18, 16, 14, 16], "#8a5a2e"); x.rect(20, 24, 3, 7, "#c0392b")
		"anvil":
			x.poly([4, 12, 26, 12, 30, 9, 30, 15, 22, 18, 10, 18, 6, 15], "#6f7880"); x.poly([4, 12, 26, 12, 29, 10, 6, 10], "#aab4bc")
			x.rect(12, 18, 8, 6, "#50585e"); x.rect(8, 24, 16, 4, "#3a4046"); x.line(20, 3, 26, 9, 3, "#8a5a2e"); x.rect(16, 1, 7, 5, "#aab4bc")
			for q in [[8, 6], [5, 8], [10, 4]]:
				x.rect(q[0], q[1], 2, 2, "#ffb040")
		"gather":
			_pick(x, "#c9833f"); _leaf(x, 22, 22, 7, "#4fa83a"); _leaf(x, 26, 16, 5, "#5fbf4a")
		"cultivate":
			x.circ(16, 16, 14, "#0f3a34"); x.arc(16, 18, 11, 3.6, 5.8, 2, "#3fd1b0"); x.circ(16, 9, 3.6, "#e8fff8"); x.poly([16, 12, 22, 20, 26, 25, 6, 25, 10, 20], "#bff5e6"); x.ell(16, 25, 10, 3, "#bff5e6")
		"character":
			x.circ(16, 14, 8, "#f0c8a0"); x.ell(16, 9, 10, 6, "#6a2048"); x.rect(8, 24, 16, 8, "#1f6b5a"); x.circ(13, 15, 1.2, "#301010"); x.circ(19, 15, 1.2, "#301010"); x.poly([16, 1, 20, 6, 12, 6], "#6a2048")
		"gear":
			for i in 8:
				var a := i / 8.0 * TAU
				x.rect(16 + cos(a) * 11 - 2.5, 16 + sin(a) * 11 - 2.5, 5, 5, "#c8ccd0")
			x.circ(16, 16, 10, "#c8ccd0"); x.circ(16, 16, 4, "#303438")
		"scroll":
			_scroll(x)
		"quest":
			_scroll(x); x.rect(14, 10, 4, 8, "#d8453a"); x.rect(14, 20, 4, 3, "#d8453a")
		"class":
			x.poly([16, 3, 27, 9, 25, 22, 16, 29, 7, 22, 5, 9], "#8a3a1e"); x.poly([16, 7, 23, 11, 22, 20, 16, 25, 10, 20, 9, 11], "#d9b25c"); x.line(12, 12, 20, 20, 2, "#8a3a1e"); x.line(20, 12, 12, 20, 2, "#8a3a1e")
		"realm":
			_realm(x)
		"shield":
			x.poly([16, 3, 27, 7, 25, 20, 16, 29, 7, 20, 5, 7], "#3a4a52"); x.poly([16, 6, 24, 9, 22, 19, 16, 25, 10, 19, 8, 9], "#c8ccd0"); x.line(16, 7, 16, 24, 1.5, "#3a4a52")
		"jump":
			x.poly([16, 3, 28, 16, 21, 16, 21, 29, 11, 29, 11, 16, 4, 16], "#6fd0ff"); x.poly([16, 6, 24, 15, 18, 15, 18, 27, 14, 27, 14, 15, 8, 15], "#bfefff")
		"close":
			x.line(7, 7, 25, 25, 4, "#e8d8a8"); x.line(25, 7, 7, 25, 4, "#e8d8a8")
		"step":
			for q in [[10, 18], [16, 22], [22, 14]]:
				x.quad(4, q[0], 4 + q[1], q[0] - 4, 4 + q[1], q[0] + 2, 2.4, "#8ff0d8")
		"art":
			x.circ(16, 16, 11, "#1a4aa8"); x.circ(16, 16, 7, "#4a9aff"); x.circ(13, 13, 3, "#dff0ff"); x.arc(16, 16, 13, 0.5, 2.5, 1.6, "#9fd8ff")
		"nova":
			x.circ(16, 16, 12, "#10306a"); x.arc(16, 16, 10, 0, 5, 3, "#4a9aff"); x.arc(16, 16, 5, 2, 7, 2, "#bfe0ff")
		"mend":
			_realm(x); x.circ(16, 18, 3, "#e8c040")
		"bolt":
			x.poly([4, 16, 20, 10, 18, 14, 30, 16, 18, 18, 20, 22], "#6fb0ff"); x.circ(24, 16, 4, "#dff0ff")
		"dragon":
			x.bezier(4, 26, 10, 4, 22, 30, 28, 8, 4.5, "#c8ccd0"); x.poly([26, 4, 31, 8, 26, 12], "#ffffff"); x.circ(27, 8, 1, "#d8453a")
		"crescent":
			_swoosh(x, "#6ff0d0", "arc"); _figure(x, 0)
		"lunge", "thrust":
			_swoosh(x, "#6ff0d0", "line"); _figure(x, 0)
		"parry":
			_swoosh(x, "#d9b25c", "arc"); _figure(x, 1)
		"combo":
			_swoosh(x, "#8fb0ff", "arc"); _figure(x, 0)
		"wave":
			_swoosh(x, "#6ff0d0", "wave"); _figure(x, 0)
		"spin":
			_swoosh(x, "#d9b25c", "ring"); _figure(x, 1)
		"potion_red":
			_pill(x, "#d8453a")
		_:
			x.circ(16, 16, 10, "#555555")
