extends RefCounted
## What a room draws, headless (tests/visibility_suite.gd, tests/room_sweep.gd): every piece of art `world.gd` puts in
## the room, in its draw order, and the alpha of its pixels. The views say where and at what depth they draw
## (SpriteCache.prop_rect, Terrain.building_pieces and sort_z, SceneryProp, DecorView.make_prop, ObjectView.depth,
## PortalView.art_for); this only lists them in the order `_build_room` adds them. A layer is
## {what, kind, id, z, order, pieces: [{tex, rect, src, flip}], fills: [Rect2], cond}: a piece is a texture region drawn
## over `rect` in room px (mirrored with `flip`); a fill is a rect drawn solid (a platform's deck, a block, a figure).
## `cond` marks a layer that shows only at times (an object with visible_if or hidden_if, a hidden way).

const Terrain = preload("res://scripts/terrain.gd")

static var _images: Dictionary = {}

## A texture's pixels, decompressed (cached by resource path).
static func image(tex: Texture2D) -> Image:
	if tex == null: return null
	var key := tex.resource_path if tex.resource_path != "" else str(tex.get_instance_id())
	if not _images.has(key):
		var img: Image = tex.get_image()
		if img != null:
			img = img.duplicate()
			if img.is_compressed(): img.decompress()
		_images[key] = img
	return _images[key]

## A prop's frame of `state` (or its first state) drawn with its anchor at `pos`: {tex, rect, src, flip}, {} with no art.
static func prop_piece(id: String, state: String, pos: Vector2, flip := false) -> Dictionary:
	var e := SpriteCache.prop(id)
	if e.is_empty(): return {}
	var states: Dictionary = e.get("states", {})
	var st: Dictionary = states.get(state, states.values()[0] if not states.is_empty() else {})
	var fw := float(e.frame[0])
	var rect := SpriteCache.prop_rect(id, pos)
	if flip: rect.position.x = 2.0 * pos.x - rect.end.x
	return {"tex": SpriteCache.tex(str(e.get("file", ""))), "rect": rect, "src": Rect2(int(st.get("col", 0)) * fw, 0, fw, float(e.frame[1])), "flip": flip}

## The alpha a piece draws at room point `p` (0 outside it).
static func alpha(piece: Dictionary, p: Vector2) -> float:
	var r: Rect2 = piece.rect
	if not r.has_point(p) or r.size.x <= 0.0 or r.size.y <= 0.0: return 0.0
	var img := image(piece.tex)
	if img == null: return 0.0
	var src: Rect2 = piece.src
	var u := (p.x - r.position.x) / r.size.x
	if piece.get("flip", false): u = 1.0 - u
	var v := (p.y - r.position.y) / r.size.y
	var x := clampi(int(src.position.x + u * src.size.x), 0, img.get_width() - 1)
	var y := clampi(int(src.position.y + v * src.size.y), 0, img.get_height() - 1)
	return img.get_pixel(x, y).a

## The part of a piece's region with any opaque pixel, in the region's own px (Rect2i() when it is blank or missing).
static func used(piece: Dictionary) -> Rect2i:
	var img := image(piece.get("tex"))
	if img == null: return Rect2i()
	var src := Rect2i(piece.src).intersection(Rect2i(0, 0, img.get_width(), img.get_height()))
	if src.size.x <= 0 or src.size.y <= 0: return Rect2i()
	return img.get_region(src).get_used_rect()

## Every layer of room `def` (compiled into `geo`), in draw order.
static func layers(def: Dictionary, geo: ZoneGeometry) -> Array:
	var out: Array = []
	var add := func(l: Dictionary) -> void:
		l.order = out.size()
		for k in ["pieces", "fills"]: if not l.has(k): l[k] = []
		out.append(l)
	if def.has("wall"):
		var w: Dictionary = def.wall
		add.call({"what": "the back wall", "kind": "wall", "id": "wall", "z": -2100,
			"fills": [Rect2(-40, float(w.get("top", 150)), geo.bounds.size.x + 80, float(w.get("bottom", 640)) - float(w.get("top", 150)))]})
	for s in geo.surfaces:
		var l := {"what": "surface " + s.id, "kind": "surface", "id": s.id, "z": Terrain.sort_z(s, geo, false), "cracked": s.cracked}
		if s.kind == "roof":
			var tv = Terrain.new()
			tv.surface = s
			tv.generated = true
			for spec in def.get("surfaces", []):
				if str(spec.id) == s.id: tv.art = str(spec.get("art", ""))
			l.pieces = tv.building_pieces()
			tv.free()
			for p in l.pieces: p.flip = false
		else:
			l.fills = _surface_fills(s)
			for b in def.get("blocks", []):
				if s.is_block and str(b.id) == s.id: l.prop = str(Terrain.BLOCK_PROPS.get(str(b.get("kind", "crate")), ""))
		add.call(l)
	for spec in def.get("scenery", []):
		if spec.get("art", "props") == "none": continue
		var pos := Vector2(float(spec.position[0]), float(spec.position[1]))
		var piece := {}
		if spec.has("prop"):
			piece = prop_piece(str(spec.prop), str(spec.get("state", "idle")), pos, bool(spec.get("flip", false)))
		elif spec.has("cell"):
			piece = SceneryProp.cell_piece(spec)
			piece.rect = Rect2(pos + (piece.rect as Rect2).position, (piece.rect as Rect2).size)
			piece.tex = SceneryProp.ATLAS
			piece.flip = bool(spec.get("flip", false))
		add.call({"what": "scenery " + str(spec.get("id", "")), "kind": "scenery", "id": str(spec.get("id", "")), "z": SceneryProp.depth(spec),
			"pieces": [piece] if not piece.is_empty() else [], "prop": str(spec.get("prop", "")), "blocks": spec.get("blocks", true) and spec.has("footprint"), "def": spec})
	for d in def.get("decor", []):
		var v := DecorView.make_prop(d)
		var piece := prop_piece(v.prop_id, v.state, v.position, v.flip)
		add.call({"what": "decor %s at %s" % [str(d.prop), str(d.at)], "kind": "decor", "id": str(d.prop), "z": v.z_index, "pieces": [piece] if not piece.is_empty() else [], "def": d})
		v.free()
	for o in def.get("objects", []):
		if str(o.type) == "decor": continue
		var at := Vector2(float(o.at[0]), float(o.at[1]) - float(o.get("alt", 0)))
		var l := {"what": "%s %s" % [str(o.type), str(o.id)], "kind": "npc" if str(o.type) == "npc" else "object", "id": str(o.id),
			"z": ObjectView.depth(o, geo), "def": o, "cond": o.has("visible_if") or o.has("hidden_if") or o.has("chase") or str(o.type) == "egg_nest"}
		if str(o.type) == "npc":
			l.fills = [Rect2(at + Vector2(-14, -58), Vector2(28, 58))]   # the figure's body
		else:
			l.prop = ObjectView.prop_of(o)
			var piece := prop_piece(str(l.prop), "idle", at, bool(o.get("flip", false))) if str(l.prop) not in ["", "none"] else {}
			if not piece.is_empty(): l.pieces = [piece]
		add.call(l)
	for p in def.get("portals", []):
		var pv := PortalView.new()
		pv.setup(p, def)
		var on_wall := pv.shows == "wall"
		var art := PortalView.art_for(p, true, pv.shows)
		var l := {"what": "%s way %s" % [str(p.get("type", "edge")), str(p.id)], "kind": "portal", "id": str(p.id), "z": pv.z_index, "def": p,
			"art": art, "art_closed": PortalView.art_for(p, false, pv.shows), "entrance": pv.shows, "door_top": pv.door_top,
			"label_y": pv.position.y + ((pv.door_top - 30.0) if str(p.get("type", "edge")) == "door" else -150.0), "cond": str(p.get("type", "")) == "hidden"}
		if art != "":
			var piece := prop_piece(art, "idle", pv.position)
			if not piece.is_empty(): l.pieces = [piece]
		elif on_wall:
			l.pieces = [prop_piece("door", "closed", pv.position + Vector2(0, pv.wall_y))]
		pv.free()
		add.call(l)
	return out

## What a surface other than a roof draws solid: its top face (the walkable deck) and, for a surface with a face down to
## the ground (a terrace, a chimney, a pillar, a town wall, a block), that face. Flat ground draws under every figure.
static func _surface_fills(s: WalkSurface) -> Array:
	if s.kind in ["ladder"] or (s.stratum == "ground" and s.base == 0 and s.rise == 0): return []
	var r := s.bounds
	var top := Rect2(r.position.x, r.position.y - s.height_at(r.position), r.size.x, r.size.y)
	if s.kind in ["ground", "chimney", "stone_pillar", "walltop", "block"] and s.base > 0:
		return [top.merge(Rect2(r.position.x, r.end.y - s.base, r.size.x, s.base))]
	return [top]

## Every layer drawn over `l` (a greater depth, or the same depth and added later) with art at `p`.
static func covering(all: Array, l: Dictionary, p: Vector2, threshold := 0.5) -> Dictionary:
	for m in all:
		# A block drawn with the thing's own art (a training stump's block) shows it; a person moves out of the way.
		# A cracked slab or wall hides what waits under it until it is broken (a secret, not a thing lost).
		if m.get("cracked", false): continue
		if m == l or m.get("cond", false) or m.kind in ["npc"] or (str(m.get("prop", "")) != "" and m.get("prop") == l.get("prop")): continue
		if int(m.z) < int(l.z) or (int(m.z) == int(l.z) and int(m.order) < int(l.order)): continue
		for f in m.fills:
			if (f as Rect2).has_point(p): return m
		for piece in m.pieces:
			if alpha(piece, p) >= threshold: return m
	return {}
