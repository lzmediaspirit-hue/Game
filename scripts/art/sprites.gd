# Procedural chibi pixel sprites. Each (look, pose, frame, scale) is painted once and cached.
class_name Sprites
extends RefCounted

const C = preload("res://scripts/data/content.gd")
const OUT := "#120c0a"
const W := 40
const H := 52
const FX := 20.0
const FY := 50.0
static var _cache := {}

const HAIR_COLORS := {"topknot": "#2a1a1c", "windswept": "#6a2050", "silver_tail": "#d8dce6", "plum_bob": "#6e2250"}

const LOOKS := {
	"raider": {"skin": "#d8a880", "hair": "topknot", "hairColor": "#1a1414", "main": "#5a3a28", "trim": "#3a2418", "under": "#2a2220", "sash": "#9c2a2a", "mask": "#1a1616", "scarf": "#b03030"},
	"archer": {"skin": "#d8a880", "hair": "hood", "hairColor": "#3a4a2a", "main": "#4a5a34", "trim": "#2a3420", "under": "#2a2a20", "sash": "#7a5a2a", "mask": "#1a1616", "scarf": "#6a7a3a"},
	"heavy": {"skin": "#c89070", "hair": "bald", "hairColor": "#1a1414", "main": "#3a3c46", "trim": "#8a8e98", "under": "#22242a", "sash": "#6b3a1e", "bulky": true},
	"captain": {"skin": "#d0a078", "hair": "topknot", "hairColor": "#101010", "main": "#1c2230", "trim": "#c9a54a", "under": "#101418", "sash": "#b03030", "mask": "#101010", "scarf": "#c03030", "hat": "conical_dark"},
	"acolyte": {"skin": "#c8b0a0", "hair": "hood", "hairColor": "#1a1020", "main": "#1e1628", "trim": "#8a4ad0", "under": "#120c18", "sash": "#8a4ad0", "mask": "#120c18"},
	"qiu": {"skin": "#e0c0a0", "hair": "silver_tail", "hairColor": "#e8e8f0", "main": "#1a1024", "trim": "#d9b25c", "under": "#3a1a4a", "sash": "#d9b25c", "beard": "#e8e8f0"},
	"echo": {"skin": "#9ff0e0", "hair": "topknot", "hairColor": "#3fd1b0", "main": "#2a8a78", "trim": "#bff5e6", "under": "#1a5a50", "sash": "#bff5e6"},
	"wen": {"skin": "#e8c8a8", "hair": "topknot", "hairColor": "#e8e8ec", "main": "#4a6a6a", "trim": "#d9b25c", "under": "#dcd4c0", "sash": "#8a6a30", "beard": "#f0f0f4"},
	"suyin": {"skin": "#f0d0b0", "hair": "bun", "hairColor": "#1a1418", "main": "#5a3a7a", "trim": "#e0c070", "under": "#e8e0f0", "sash": "#e0c070"},
	"tao": {"skin": "#d8b090", "hair": "bald", "hairColor": "#1a1414", "main": "#7a4a28", "trim": "#e0c070", "under": "#e8d8b8", "sash": "#c0392b", "beard": "#3a3030"},
	"merchant": {"skin": "#e8c0a0", "hair": "topknot", "hairColor": "#2a1a1c", "main": "#8a6a30", "trim": "#e0c070", "under": "#e8e0cc", "sash": "#9c2a2a", "hat": "straw"},
}

# bob, back/front leg offsets, back/front arm angles (0 = forward), lean, lift, tuck
const POSES := {
	"idle": [{"bob": 0, "lb": -2, "lf": 3, "ab": 1.9, "af": 0.9}, {"bob": 1, "lb": -2, "lf": 3, "ab": 1.95, "af": 0.95}],
	"run": [{"bob": 0, "lb": -6, "lf": 6, "ab": 2.4, "af": 0.3, "lift": 1}, {"bob": -1, "lb": -2, "lf": 2, "ab": 1.8, "af": 1.0},
		{"bob": 0, "lb": 6, "lf": -6, "ab": 1.0, "af": 1.9, "lift": 2}, {"bob": -1, "lb": 2, "lf": -2, "ab": 1.6, "af": 1.2}],
	"attack": [{"bob": 0, "lb": -4, "lf": 5, "ab": 2.4, "af": -1.1, "lean": -1}, {"bob": 0, "lb": -6, "lf": 7, "ab": 2.2, "af": 0.05, "lean": 2}, {"bob": 0, "lb": -5, "lf": 6, "ab": 2.0, "af": 0.6, "lean": 1}],
	"cast": [{"bob": 0, "lb": -3, "lf": 4, "ab": 2.0, "af": -0.2, "lean": 1}],
	"jump": [{"bob": -1, "lb": -4, "lf": 4, "ab": 2.6, "af": -0.4, "lift": 3, "tuck": 1}],
	"fall": [{"bob": 0, "lb": -3, "lf": 5, "ab": 2.8, "af": -0.8}],
	"dash": [{"bob": 1, "lb": -8, "lf": 8, "ab": 2.9, "af": 2.6, "lean": 3}],
	"guard": [{"bob": 1, "lb": -4, "lf": 5, "ab": 1.4, "af": -0.6, "lean": -1}],
	"hurt": [{"bob": 0, "lb": -1, "lf": 3, "ab": 2.8, "af": 2.4, "lean": -3, "hurt": 1}],
	"sit": [{"sit": 1}],
	"dead": [{"dead": 1}],
	"talk": [{"bob": 0, "lb": -2, "lf": 3, "ab": 1.9, "af": 0.2}],
}


static func player_look(p: Dictionary) -> Dictionary:
	var c: Dictionary = C.CLOTHES[0]
	for x in C.CLOTHES:
		if x.id == p.look.clothes:
			c = x
	var hat = null
	if p.equip.hat == "straw_hat":
		hat = "straw"
	elif p.equip.hat == "jade_crown":
		hat = "crown"
	return {"skin": "#f2cfa8", "hair": p.look.hair, "hairColor": HAIR_COLORS.get(p.look.hair, "#6e2250"),
		"main": c.main, "trim": c.trim, "under": c.under, "sash": c.sash, "hat": hat, "gourd": p.equip.gourd != null, "eyes": "#8a1a24"}


static func frames(pose: String) -> int:
	return POSES.get(pose, POSES.idle).size()


static func _f(pose: String, frame: int) -> Dictionary:
	var arr: Array = POSES.get(pose, POSES.idle)
	return arr[frame % arr.size()]


# front-hand position (sprite-local, facing right) for weapon placement
static func hand_at(pose: String, frame: int, scale := 1.0) -> Dictionary:
	var f := _f(pose, frame)
	if f.has("sit"):
		return {"x": FX + 5 * scale, "y": FY - 10 * scale, "a": -0.15}
	if f.has("dead"):
		return {}
	var sx: float = 2.0 + f.get("lean", 0)
	var sy: float = -24.0 + f.get("bob", 0)
	var a: float = f.af
	return {"x": FX + (sx + cos(a) * 8) * scale, "y": FY + (sy + sin(a) * 8) * scale, "a": a}


static func humanoid(look: Dictionary, pose := "idle", frame := 0, scale := 1.0) -> Dictionary:
	var k := "%s|%s|%d|%.2f" % [str(look), pose, frame % frames(pose), scale]
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(int(W * scale) + 2, int(H * scale) + 2)
	var f := _f(pose, frame)
	var t := Transform2D(0, Vector2(scale, scale), 0, Vector2(1, 1))
	var q := _Scaled.new(x, t)
	if f.has("sit"):
		_sit(q, look)
	elif f.has("dead"):
		_dead(q, look)
	else:
		_standing(q, look, f)
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": FX * scale + 1, "ay": FY * scale + 1}
	_cache[k] = out
	return out


# Wraps a Painter with a uniform scale so sprite code can stay in base coordinates.
class _Scaled:
	var p: Painter
	var s: float
	var o: Vector2

	func _init(painter: Painter, t: Transform2D) -> void:
		p = painter
		s = t.get_scale().x
		o = t.origin

	func _pts(a: Array) -> Array:
		var r := []
		for i in a.size():
			r.append(a[i] * s + (o.x if i % 2 == 0 else o.y))
		return r

	func poly(a: Array, c) -> void: p.poly(_pts(a), c)
	func circ(cx, cy, r, c) -> void: p.circ(cx * s + o.x, cy * s + o.y, r * s, c)
	func ell(cx, cy, rx, ry, c, rot := 0.0) -> void: p.ell(cx * s + o.x, cy * s + o.y, rx * s, ry * s, c, rot)
	func rect(x, y, w, h, c) -> void: p.rect(x * s + o.x, y * s + o.y, w * s, h * s, c)
	func line(x0, y0, x1, y1, w, c) -> void: p.line(x0 * s + o.x, y0 * s + o.y, x1 * s + o.x, y1 * s + o.y, w * s, c)
	func quad(x0, y0, qx, qy, x1, y1, w, c) -> void: p.quad(x0 * s + o.x, y0 * s + o.y, qx * s + o.x, qy * s + o.y, x1 * s + o.x, y1 * s + o.y, w * s, c)
	func arc(cx, cy, r, a0, a1, w, c) -> void: p.arc(cx * s + o.x, cy * s + o.y, r * s, a0, a1, w * s, c)


static func _sh(c, k: float) -> Color:
	return Painter.shade(c, k)


static func _hair_back(x, l: Dictionary, hx: float, hy: float, flow: float) -> void:
	var hc = l.hairColor
	match l.hair:
		"plum_bob", "topknot":
			x.quad(hx - 2, hy - 8, hx - 12, hy - 9 + flow, hx - 11, hy + 4 + flow, 3.4, hc)
		"silver_tail":
			x.quad(hx - 3, hy - 4, hx - 13, hy + 2 + flow, hx - 10, hy + 14 + flow, 4, hc)
		"windswept":
			for i in 3:
				x.poly([hx - 3, hy - 6 + i * 3, hx - 13, hy - 8 + i * 4 + flow, hx - 4, hy - 2 + i * 3], hc)


static func _hair_front(x, l: Dictionary, hx: float, hy: float) -> void:
	var hc = l.hairColor
	if l.hair == "bald":
		x.ell(hx, hy - 3.5, 6.6, 3.4, _sh(l.skin, -0.08))
		return
	if l.hair == "hood":
		var pts := []
		for i in 13:
			var a := PI * (0.95 + 1.2 * i / 12.0)
			pts.append(hx - 0.5 + cos(a) * 8.2); pts.append(hy - 0.5 + sin(a) * 8.2)
		pts.append(hx - 7); pts.append(hy + 5)
		x.poly(pts, l.main)
		x.poly([hx - 8, hy, hx - 12, hy + 7, hx - 6, hy + 6], l.main)
		return
	# cap of hair over the top of the head (keeps the eyes clear)
	var cap := []
	for i in 13:
		var a2 := PI * (0.97 + 1.06 * i / 12.0)
		cap.append(hx + cos(a2) * 7.8); cap.append(hy - 1.6 + sin(a2) * 7.8)
	x.poly(cap, hc)
	x.poly([hx + 1, hy - 7, hx + 8, hy - 2.5, hx + 7.4, hy + 0.5, hx + 5.6, hy - 1.6, hx + 3, hy - 1.2], hc)
	x.poly([hx - 7, hy - 3, hx - 5, hy + 6, hx - 3, hy - 1], hc)
	if l.hair == "topknot" or l.hair == "plum_bob":
		x.circ(hx - 1, hy - 9, 2.8, hc)
		x.rect(hx - 2.5, hy - 7.5, 3, 1.4, "#3fd1b0" if l.hair == "plum_bob" else "#d9b25c")
	if l.hair == "bun":
		x.circ(hx - 3, hy - 8, 3.4, hc)
		x.line(hx - 7, hy - 10, hx + 1, hy - 7, 1, "#d9b25c")
	if l.hair == "windswept":
		x.poly([hx - 2, hy - 8, hx + 3, hy - 12, hx + 2, hy - 7], hc)
	if l.hair == "silver_tail":
		x.circ(hx - 4, hy - 6, 2.6, hc)
	x.line(hx - 3, hy - 6, hx + 2, hy - 7.5, 1, _sh(hc, 0.35))


static func _hat(x, l: Dictionary, hx: float, hy: float) -> void:
	match l.get("hat"):
		"straw":
			x.poly([hx - 12, hy - 4, hx, hy - 13, hx + 12, hy - 4], "#c9a45a"); x.poly([hx - 8, hy - 5, hx, hy - 11, hx + 8, hy - 5], "#e2c27a")
		"conical_dark":
			x.poly([hx - 12, hy - 4, hx, hy - 13, hx + 12, hy - 4], "#1a1a1e"); x.poly([hx - 8, hy - 5, hx, hy - 11, hx + 8, hy - 5], "#34343a")
		"crown":
			x.rect(hx - 3, hy - 12, 6, 3, "#3fd1b0"); x.rect(hx - 1, hy - 14, 2, 2, "#d9b25c")


static func _face(x, l: Dictionary, hx: float, hy: float, hurt: bool) -> void:
	if l.has("mask"):
		x.rect(hx - 1, hy + 3, 9, 4, l.mask)
	var ec = l.get("eyes", "#2a1414")
	if hurt:
		x.line(hx + 1.5, hy - 0.5, hx + 3.5, hy + 1.5, 1, ec); x.line(hx + 3.5, hy - 0.5, hx + 1.5, hy + 1.5, 1, ec)
	else:
		x.rect(hx + 1.6, hy - 0.2, 1.8, 3, ec); x.rect(hx + 5, hy - 0.2, 1.6, 3, ec)
		x.rect(hx + 1.6, hy - 0.2, 0.9, 0.9, "#ffffff"); x.rect(hx + 5, hy - 0.2, 0.8, 0.8, "#ffffff")
	if l.has("beard"):
		x.poly([hx - 1, hy + 4, hx + 7, hy + 4, hx + 3, hy + 11], l.beard)
	elif not l.has("mask"):
		x.rect(hx + 3.6, hy + 4.4, 1.6, 0.8, _sh(l.skin, -0.35))
		x.rect(hx + 0.5, hy + 3, 1.6, 1, "#f0a0a0")


static func _standing(x, l: Dictionary, f: Dictionary) -> void:
	var bob: float = f.get("bob", 0)
	var lean: float = f.get("lean", 0)
	var lift: int = f.get("lift", 0)
	var tuck := 3.0 if f.has("tuck") else 0.0
	var hip_y := FY - 12 + bob * 0.5
	var bulk := 2.0 if l.get("bulky", false) else 0.0
	var shoe := "#1e1614"
	var back := _sh(l.main, -0.3)
	var lb: float = f.lb
	var lf: float = f.lf
	var ab: float = f.ab
	var af: float = f.af
	x.line(FX - 1, hip_y, FX + lb, FY - 2 - (2 if lift == 2 else 0) - tuck, 3.4 + bulk, _sh(l.under, -0.25))
	x.rect(FX + lb - 1.5, FY - 3 - (2 if lift == 2 else 0) - tuck, 4, 2.4, shoe)
	var sx := FX + 2 + lean
	var sy := FY - 24 + bob
	x.line(sx - 3, sy, sx - 3 + cos(ab) * 7, sy + sin(ab) * 7, 3.2 + bulk, back)
	if l.has("scarf"):
		x.quad(sx - 1, sy - 2, sx - 10, sy - 3 + bob, sx - 13, sy + 3 + bob * 2, 2.6, l.scarf)
	var hem := FY - 8 + bob * 0.3
	x.poly([sx - 6 - bulk, sy - 1, sx + 4 + bulk, sy - 1, FX + 6 + bulk + lean * 0.5, hem, FX - 8 - bulk - (2 if lift else 0), hem + 1], l.main)
	x.poly([FX - 6 - bulk, hip_y - 2, FX - 11 - bulk - lift, hem + 2, FX - 4, hem], _sh(l.main, -0.15))
	x.poly([sx + 1, sy, sx + 4 + bulk, sy, FX + 5 + bulk + lean * 0.5, hem, FX + 1, hem], l.under)
	x.line(sx + 1, sy, FX + 1, hem, 1, l.trim)
	x.line(FX - 8 - bulk, hem + 1, FX + 6 + bulk, hem, 1.2, l.trim)
	x.rect(sx - 6 - bulk, sy + 7, 11 + bulk * 2, 2.6, l.sash)
	x.rect(sx - 1, sy + 7, 2, 2.6, _sh(l.sash, 0.35))
	if l.get("gourd", false):
		x.circ(sx - 6, sy + 12, 2.2, "#b5652e"); x.circ(sx - 6, sy + 9.5, 1.4, "#c7773a")
	x.line(FX + 1, hip_y, FX + lf, FY - 2 - (2 if lift == 1 else 0) - tuck, 3.4 + bulk, l.under)
	x.rect(FX + lf - 1.5, FY - 3 - (2 if lift == 1 else 0) - tuck, 4.4, 2.4, shoe)
	var hx := FX + 1 + lean
	var hy := FY - 32 + bob
	_hair_back(x, l, hx, hy, bob)
	x.circ(hx, hy, 7.2, l.skin)
	x.rect(hx - 2, hy + 5.5, 4, 3, _sh(l.skin, -0.15))
	_face(x, l, hx, hy, f.has("hurt"))
	_hair_front(x, l, hx, hy)
	_hat(x, l, hx, hy)
	x.poly([sx - 3, sy - 2, sx + 1, sy + 3, sx + 4, sy - 2], l.trim)
	x.line(sx, sy, sx + cos(af) * 7, sy + sin(af) * 7, 3.4 + bulk, l.main)
	x.circ(sx + cos(af) * 8.4, sy + sin(af) * 8.4, 1.8, l.skin)


static func _sit(x, l: Dictionary) -> void:
	var hy := FY - 23
	x.ell(FX, FY - 3, 11, 3.6, _sh(l.under, -0.2))
	x.poly([FX - 7, FY - 16, FX + 7, FY - 16, FX + 10, FY - 4, FX - 10, FY - 4], l.main)
	x.poly([FX - 2, FY - 16, FX + 3, FY - 16, FX + 2, FY - 5, FX - 1, FY - 5], l.under)
	x.rect(FX - 7, FY - 11, 14, 2.4, l.sash)
	x.ell(FX, FY - 5, 5, 2, l.skin)
	_hair_back(x, l, FX, hy, 2)
	x.circ(FX, hy, 7.2, l.skin)
	x.line(FX - 4.5, hy + 1, FX - 1.5, hy + 1, 1, "#2a1414"); x.line(FX + 1.5, hy + 1, FX + 4.5, hy + 1, 1, "#2a1414")
	if l.has("beard"):
		x.poly([FX - 3, hy + 4, FX + 3, hy + 4, FX, hy + 10], l.beard)
	var capc = l.skin if l.hair == "bald" else l.hairColor
	var cap := []
	for i in 13:
		var a := PI + PI * i / 12.0
		cap.append(FX + cos(a) * 7.6); cap.append(hy - 1.5 + sin(a) * 7.6)
	x.poly(cap, capc)
	if l.hair in ["topknot", "plum_bob", "bun"]:
		x.circ(FX, hy - 9, 2.8, l.hairColor)
	if l.hair != "bald" and l.hair != "hood":
		x.poly([FX - 7.4, hy - 2, FX - 6, hy + 6, FX - 4.5, hy - 1], l.hairColor)
		x.poly([FX + 7.4, hy - 2, FX + 6, hy + 6, FX + 4.5, hy - 1], l.hairColor)
	_hat(x, l, FX, hy)


static func _dead(x, l: Dictionary) -> void:
	var y := FY - 4
	x.ell(FX - 2, y, 12, 3.6, l.main)
	x.line(FX + 6, y, FX + 14, y + 1, 3, l.under)
	x.circ(FX - 14, y - 1, 5.6, l.skin)
	x.ell(FX - 16, y - 3, 5, 4, l.skin if l.hair == "bald" else l.hairColor)


# ---------------------------------------------------------------- beasts & sentinel
static func beast(kind: String, frame := 0, pose := "run") -> Dictionary:
	var k := "beast|%s|%d|%s" % [kind, frame % 4, pose]
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(48, 34)
	var spirit := kind == "spirit_wolf"
	var fur := "#2a2438" if spirit else "#6a6a70"
	var belly := "#4a3a6a" if spirit else "#a8a8ae"
	var eye := "#d070ff" if spirit else "#f0d040"
	var ax := 24.0
	var ay := 32.0
	if pose == "dead":
		x.ell(ax, ay - 4, 15, 4, fur); x.circ(ax + 14, ay - 5, 4, fur)
	else:
		var ph := frame % 4
		var sw: float = [4, 1, -4, -1][ph]
		var lunge := 3.0 if pose == "attack" else 0.0
		x.quad(ax - 12, ay - 14, ax - 22, ay - 20 + ph, ax - 20, ay - 10, 3.4, fur)
		x.line(ax - 9, ay - 10, ax - 9 - sw, ay - 1, 2.8, _sh(fur, -0.25)); x.line(ax + 8, ay - 10, ax + 8 + sw, ay - 1, 2.8, _sh(fur, -0.25))
		x.ell(ax, ay - 14, 13, 6, fur); x.ell(ax + 1, ay - 11, 10, 3, belly)
		x.line(ax - 7, ay - 10, ax - 7 + sw, ay - 1, 3, fur); x.line(ax + 10, ay - 10, ax + 10 - sw, ay - 1, 3, fur)
		var hx := ax + 14 + lunge
		var hy := ay - 18 - (1 if pose == "attack" else 0)
		x.ell(hx, hy, 6, 5, fur); x.poly([hx + 2, hy - 2, hx + 11, hy + 1, hx + 3, hy + 4], fur)
		x.poly([hx - 4, hy - 3, hx - 2, hy - 10, hx + 1, hy - 4], _sh(fur, -0.2))
		x.rect(hx + 2, hy - 2, 2, 1.6, eye)
		if pose == "attack":
			x.poly([hx + 4, hy + 3, hx + 11, hy + 2, hx + 5, hy + 6], "#8a2020")
		if spirit:
			for i in 3:
				x.poly([ax - 6 + i * 6, ay - 19, ax - 3 + i * 6, ay - 26 - i, ax + i * 6, ay - 19], "#6a3aa0")
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": ax, "ay": ay}
	_cache[k] = out
	return out


static func sentinel(frame := 0, pose := "idle") -> Dictionary:
	var k := "sentinel|%d|%s" % [frame % 2, pose]
	if _cache.has(k):
		return _cache[k]
	var x := Painter.new(80, 96)
	var ax := 40.0
	var ay := 94.0
	var bob := 4.0 if pose == "attack" else float(frame % 2)
	if pose == "dead":
		for i in 12:
			x.line(ax - 30 + i * 4, ay - 3, ax - 26 + i * 5, ay - 12 + (i % 3) * 3, 2.4, "#8a9a4a" if i % 2 else "#6a7a3a")
	else:
		for dx in [-10, 10]:
			for i in 4:
				x.line(ax + dx - 3 + i * 2, ay - 26, ax + dx - 4 + i * 2.5, ay - 1, 2, "#7a8a3a" if i % 2 else "#5a6a2a")
		x.ell(ax, ay - 46 + bob, 20, 24, "#6a7a3a")
		for i in 9:
			x.line(ax - 18 + i * 4.5, ay - 66 + bob, ax - 16 + i * 4, ay - 24 + bob, 1.6, "#8a9a4a" if i % 2 else "#4a5a24")
		x.rect(ax - 20, ay - 44 + bob, 40, 4, "#8a5a2a")
		x.ell(ax + 2, ay - 76 + bob, 11, 10, "#7a8a3a")
		for i in 6:
			x.line(ax - 6 + i * 3, ay - 84 + bob, ax - 9 + i * 4, ay - 94 + bob + (i % 2) * 3, 1.8, "#9aaa5a")
		x.rect(ax + 1, ay - 78 + bob, 3, 3, "#e8ff70"); x.rect(ax + 7, ay - 78 + bob, 3, 3, "#e8ff70")
		var ar := -1.2 if pose == "attack" else 0.8
		x.line(ax + 12, ay - 58 + bob, ax + 12 + cos(ar) * 22, ay - 58 + bob + sin(ar) * 22, 7, "#5a6a2a")
		x.line(ax - 14, ay - 58 + bob, ax - 20, ay - 36 + bob, 7, "#4a5a24")
	x.outline(OUT)
	var out := {"tex": x.texture(), "ax": ax, "ay": ay}
	_cache[k] = out
	return out
