# Tiny software rasterizer over an Image: scanline polygons, circles, ellipses, thick lines,
# arcs and curves, plus a 1px outline pass. No anti-aliasing — every shape is crisp pixel art.
class_name Painter
extends RefCounted

var img: Image
var w: int
var h: int
var _row: Image
static var _colors := {}


func _init(width: int, height: int) -> void:
	w = maxi(1, width)
	h = maxi(1, height)
	img = Image.create(w, h, false, Image.FORMAT_RGBA8)
	_row = Image.create(w, 1, false, Image.FORMAT_RGBA8)


static func col(c) -> Color:
	if c is Color:
		return c
	if not _colors.has(c):
		_colors[c] = Color.html(c)
	return _colors[c]


static func shade(c, k: float) -> Color:
	var a := col(c)
	return a.lerp(Color.WHITE, k) if k >= 0.0 else a.lerp(Color.BLACK, -k)


static func mix(a, b, t: float) -> Color:
	return col(a).lerp(col(b), t)


func span(y: int, x0: int, x1: int, c: Color) -> void:
	if y < 0 or y >= h:
		return
	x0 = maxi(0, x0)
	x1 = mini(w - 1, x1)
	if x1 < x0:
		return
	if c.a >= 0.999:
		img.fill_rect(Rect2i(x0, y, x1 - x0 + 1, 1), c)
	else:
		_row.fill_rect(Rect2i(0, 0, x1 - x0 + 1, 1), c)
		img.blend_rect(_row, Rect2i(0, 0, x1 - x0 + 1, 1), Vector2i(x0, y))


func rect(x: float, y: float, rw: float, rh: float, c) -> void:
	var cc := col(c)
	var x0 := int(floor(x)); var y0 := int(floor(y))
	var x1 := int(ceil(x + rw)) - 1; var y1 := int(ceil(y + rh)) - 1
	if cc.a >= 0.999:
		var r := Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1).intersection(Rect2i(0, 0, w, h))
		if r.size.x > 0 and r.size.y > 0:
			img.fill_rect(r, cc)
	else:
		for yy in range(y0, y1 + 1):
			span(yy, x0, x1, cc)


func px(x: float, y: float, c) -> void:
	var xi := int(x); var yi := int(y)
	if xi >= 0 and yi >= 0 and xi < w and yi < h:
		img.set_pixel(xi, yi, col(c))


# Even-odd scanline fill, sampling at pixel centres. pts = flat [x0,y0,x1,y1,...]
func poly(pts: Array, c) -> void:
	var cc := col(c)
	var n := pts.size() / 2
	if n < 3:
		return
	var ymin := INF; var ymax := -INF
	for i in n:
		ymin = minf(ymin, pts[i * 2 + 1]); ymax = maxf(ymax, pts[i * 2 + 1])
	var ya := maxi(0, int(floor(ymin))); var yb := mini(h - 1, int(ceil(ymax)))
	var xs := PackedFloat32Array()
	for y in range(ya, yb + 1):
		var sy := y + 0.5
		xs.clear()
		for i in n:
			var ax: float = pts[i * 2]; var ay: float = pts[i * 2 + 1]
			var j := (i + 1) % n
			var bx: float = pts[j * 2]; var by: float = pts[j * 2 + 1]
			if (ay <= sy and by > sy) or (by <= sy and ay > sy):
				xs.append(ax + (sy - ay) / (by - ay) * (bx - ax))
		xs.sort()
		var k := 0
		while k + 1 < xs.size():
			span(y, int(ceil(xs[k] - 0.5)), int(floor(xs[k + 1] - 0.5)), cc)
			k += 2


func circ(cx: float, cy: float, r: float, c) -> void:
	ell(cx, cy, r, r, c)


func ell(cx: float, cy: float, rx: float, ry: float, c, rot := 0.0) -> void:
	if rx <= 0 or ry <= 0:
		return
	var cc := col(c)
	if absf(rot) > 0.01:
		var pts := []
		for i in 24:
			var a := TAU * i / 24.0
			var ex := cos(a) * rx; var ey := sin(a) * ry
			pts.append(cx + ex * cos(rot) - ey * sin(rot))
			pts.append(cy + ex * sin(rot) + ey * cos(rot))
		poly(pts, cc)
		return
	var ya := int(floor(cy - ry)); var yb := int(ceil(cy + ry))
	for y in range(ya, yb + 1):
		var dy := (y + 0.5 - cy) / ry
		if absf(dy) > 1.0:
			continue
		var dx := rx * sqrt(1.0 - dy * dy)
		span(y, int(ceil(cx - dx - 0.5)), int(floor(cx + dx - 0.5)), cc)


func line(x0: float, y0: float, x1: float, y1: float, lw: float, c, round_cap := true) -> void:
	var cc := col(c)
	var d := Vector2(x1 - x0, y1 - y0)
	var L := d.length()
	var hw := maxf(0.5, lw / 2.0)
	if L < 0.01:
		circ(x0, y0, hw, cc)
		return
	var nrm := Vector2(-d.y, d.x) / L * hw
	poly([x0 + nrm.x, y0 + nrm.y, x1 + nrm.x, y1 + nrm.y, x1 - nrm.x, y1 - nrm.y, x0 - nrm.x, y0 - nrm.y], cc)
	if round_cap and lw >= 2.0:
		circ(x0, y0, hw, cc)
		circ(x1, y1, hw, cc)


func polyline(pts: Array, lw: float, c) -> void:
	for i in range(0, pts.size() - 2, 2):
		line(pts[i], pts[i + 1], pts[i + 2], pts[i + 3], lw, c)


func arc(cx: float, cy: float, r: float, a0: float, a1: float, lw: float, c) -> void:
	var pts := []
	var steps := maxi(6, int(absf(a1 - a0) * r / 2.0))
	for i in steps + 1:
		var a := lerpf(a0, a1, float(i) / steps)
		pts.append(cx + cos(a) * r); pts.append(cy + sin(a) * r)
	polyline(pts, lw, c)


func quad(x0: float, y0: float, qx: float, qy: float, x1: float, y1: float, lw: float, c) -> void:
	var pts := []
	for i in 13:
		var t := i / 12.0
		var a := Vector2(x0, y0).lerp(Vector2(qx, qy), t)
		var b := Vector2(qx, qy).lerp(Vector2(x1, y1), t)
		var q := a.lerp(b, t)
		pts.append(q.x); pts.append(q.y)
	polyline(pts, lw, c)


func bezier(x0: float, y0: float, c1x: float, c1y: float, c2x: float, c2y: float, x1: float, y1: float, lw: float, c) -> void:
	var pts := []
	for i in 17:
		var t := i / 16.0
		var q := Vector2(x0, y0).bezier_interpolate(Vector2(c1x, c1y), Vector2(c2x, c2y), Vector2(x1, y1), t)
		pts.append(q.x); pts.append(q.y)
	polyline(pts, lw, c)


# closed bezier-bounded shape (used for karst peaks) — sampled into a polygon
func bezier_shape(segments: Array, c) -> void:
	# segments: [x0,y0, then repeated [c1x,c1y,c2x,c2y,x,y]...]
	var pts := [segments[0], segments[1]]
	var cur := Vector2(segments[0], segments[1])
	var i := 2
	while i + 5 < segments.size() + 0:
		var c1 := Vector2(segments[i], segments[i + 1]); var c2 := Vector2(segments[i + 2], segments[i + 3]); var e := Vector2(segments[i + 4], segments[i + 5])
		for k in range(1, 13):
			var q := cur.bezier_interpolate(c1, c2, e, k / 12.0)
			pts.append(q.x); pts.append(q.y)
		cur = e
		i += 6
	poly(pts, c)


func outline(c) -> void:
	var cc := col(c)
	var src := img.duplicate()
	for y in h:
		for x in w:
			if src.get_pixel(x, y).a > 0.0:
				continue
			if (x > 0 and src.get_pixel(x - 1, y).a > 0.0) or (x < w - 1 and src.get_pixel(x + 1, y).a > 0.0) \
					or (y > 0 and src.get_pixel(x, y - 1).a > 0.0) or (y < h - 1 and src.get_pixel(x, y + 1).a > 0.0):
				img.set_pixel(x, y, cc)


func texture() -> ImageTexture:
	return ImageTexture.create_from_image(img)
