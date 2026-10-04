class_name TopdownVista
extends Node2D
## Decision 43, the living world (docs/redesign/art_bible.md §14.13): the land past a room's edge, drawn under the room
## over the backdrop, where the camera may look past the edge (the layout's `vista`, from tools/data/topdown_life.py;
## TopdownRoom.shown_rect lets the camera that far).
##   - North: a sky paling toward the horizon and, rising behind the room's ridge, far ranges in layers that slide
##     slower than the room as the camera pans (parallax): karst peaks past a sect, the valley's hills, the marsh's line
##     of trees and its reeds.
##   - South: the river going on under its far bank; or a drop: the room's edge falls away in a cliff of fluted rock
##     (the terrain's own face tiles, lip and all) into a sea of cloud with peaks standing out of it, the way down a
##     path's stairs where a way leaves by that edge.
##   - All round (a boat on the river): the water going on.
## The strips are art/topdown/vista.png (tools/art/topdown/build_life.py); the layer's factors are PARALLAX. It redraws
## only when the camera has moved a pixel or the water's frame turns, and draws nothing where no vista is.

const T := 16.0
## How far each layer follows the camera (0 stands still on the screen's far horizon, 1 moves with the room).
const PARALLAX := {"peaks_far": 0.1, "peaks_mid": 0.25, "cloud_sea": 0.45, "hills_far": 0.12, "hills_near": 0.3,
	"marsh_trees": 0.15, "marsh_reeds": 0.4, "river_bank": 0.55}
## The sky over a north vista, top to horizon, in bands (the night layer darkens it after dark).
const SKY := [Color("8fb4c8"), Color("a3c2d2"), Color("b6cfda"), Color("c8dbe1"), Color("d8e5e6")]
const HAZE := Color("d4e2e4")
const DEEP := Color(0.047, 0.106, 0.2, 0.31)   ## the water's depth tint past the edge (§14.2's #0C1B33 at 0.31)
## The sea of cloud drifts with the wind (TopdownLife.WIND), this many px a second at its calm, faster in a gust.
const CLOUD_DRIFT := 2.5
## T3: past the Lantern Star Field (TopdownLight's areas with `void`) an island's brink falls into the starry void, not
## a sea of cloud: these bands, darker down, the stars over them on a lattice of STAR px sliding by STAR_K, a nebula's
## haze across; the Starsea's water past a crossing's deck has the same stars glinting in it.
const VOID := [Color("1d1a46"), Color("17143c"), Color("110f32"), Color("0c0b26"), Color("08071b")]
const NEBULA := Color(0.48, 0.32, 0.72, 0.08)
const STAR := 12
const STAR_K := 0.2

var world
var room: TopdownRoom
var edges: Array = []
var tex: Texture2D
var strips: Dictionary = {}
var _cam := Vector2.INF
var _frame := -1
var _drift := 0.0
var _drawn_drift := -1
var void_sky := false   ## T3: the room's area is past the star field's edge (the void under its brinks)

func _init(w) -> void:
	world = w
	room = w.room
	name = "Vista"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	edges = room.def.get("vista", [])
	var live: bool = w.live and Game.room_rt != null and Game.room_rt.topdown == room   # the def TopdownAtmosphere reads
	void_sky = bool(TopdownLight.area_of(Game.room_rt.def if live else room.def).get("void", false))
	var a := TopdownLife.art()
	strips = a.get("vistas", {})
	if not edges.is_empty() and a.has("vista_sheet"): tex = load(str(a.vista_sheet))
	set_process(not edges.is_empty())

func _process(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	var c: Vector2 = world.camera.position.round()
	var f := int(Time.get_ticks_msec() / 250) % 4
	_drift += delta * CLOUD_DRIFT * (1.0 + TopdownLife.gust)
	var dr := int(_drift)
	if c != _cam or (f != _frame and (_has_water() or void_sky)) or (dr != _drawn_drift and _has_cloud() and not void_sky):
		_cam = c
		_frame = f
		_drawn_drift = dr
		queue_redraw()
	TopdownLife.spent_us += Time.get_ticks_usec() - t0
	TopdownLife.spent_parts.draw += Time.get_ticks_usec() - t0

func _has_cloud() -> bool:
	return edges.any(func(e): return str(e.kind) == "cloud_sea")

func _has_water() -> bool:
	return edges.any(func(e): return str(e.kind) in ["river", "water"])

func _view() -> Rect2:
	var vs := Vector2(world.viewport.size)
	return Rect2(world.camera.position - vs * 0.5, vs).grow(T)

func _draw() -> void:
	if edges.is_empty() or tex == null: return
	var t0 := Time.get_ticks_usec()
	var view := _view()
	var dr := room.drawn_rect()
	for e in edges:
		match str(e.edge):
			"n": _north(str(e.kind), dr, view)
			"s": _south(str(e.kind), view)
			"all": _water(view, Rect2(Vector2.ZERO, room.art_size()), true)
	TopdownLife.spent_us += Time.get_ticks_usec() - t0
	TopdownLife.spent_parts.draw += Time.get_ticks_usec() - t0

## The layout's reach past `edge` (art px).
func _pad(edge: String) -> float:
	for e in edges:
		if str(e.edge) == edge: return float(e.get("pad", 0))
	return 0.0

## A strip laid across the view with its bottom at `bottom`, sliding by its parallax factor (or `k`).
func _strip(name: String, bottom: float, view: Rect2, k := -1.0) -> void:
	if not strips.has(name): return
	var r: Array = strips[name]
	var w := float(r[2])
	var h := float(r[3])
	if k < 0.0: k = float(PARALLAX.get(name, 0.3))
	# The strip is fixed to the camera less its factor: a far one hardly moves on the screen as the camera pans; the sea
	# of cloud drifts on the wind besides.
	var base := roundf(world.camera.position.x * (1.0 - k)) + (float(_drawn_drift) * (1.0 + k) if name == "cloud_sea" else 0.0)
	var x := base + floorf((view.position.x - base) / w) * w
	while x < view.end.x:
		draw_texture_rect_region(tex, Rect2(x, bottom - h, w, h), Rect2(float(r[0]), float(r[1]), w, h))
		x += w

func _north(kind: String, dr: Rect2, view: Rect2) -> void:
	var top := dr.position.y + 12.0   # the layers' feet hide under the ridge's top
	if view.position.y > top: return
	# The sky in bands, bluer high and paler at the horizon.
	var span := maxf(1.0, top - view.position.y)
	var y := view.position.y
	var band := ceilf(span / SKY.size())
	for i in SKY.size():
		draw_rect(Rect2(view.position.x, y, view.size.x, minf(band, top - y) + 1.0), SKY[i])
		y += band
		if y >= top: break
	match kind:
		"peaks":
			_strip("peaks_far", top + 2.0, view)
			_strip("peaks_mid", top + 8.0, view)
		"hills":
			_strip("hills_far", top, view)
			_strip("hills_near", top + 6.0, view)
		"marsh":
			_strip("marsh_trees", top, view)
			_strip("marsh_reeds", top + 6.0, view)

func _south(kind: String, view: Rect2) -> void:
	var bottom := room.h * T
	if view.end.y < bottom: return
	var v2: Dictionary = room.tileset.get("v2", {})
	match kind:
		"river":
			_water(view, Rect2(Vector2.ZERO, room.art_size()), false)
			_strip("river_bank", bottom + T * 2.0 + 36.0, view)
		"cloud_sea":
			# Below the cliff, the haze deepening down, far peaks standing out of a sea of cloud, nearer ones out of its
			# nearer bank; then the cliff over them.
			var pad := _pad("s")
			var y := bottom
			if void_sky:
				# T3: past the star field's edge the brink falls into the void: dark bands, a nebula's haze, the stars.
				# Its dark deepening down from the cliff's foot in steps of 4 px (fixed to the room, so the steps hold still as
				# the camera pans), the nebula's haze across it, densest in its middle.
				var deep := pad + T * 2.0
				while y < view.end.y:
					var k := clampf((y - bottom) / deep, 0.0, 1.0) * (VOID.size() - 1)
					draw_rect(Rect2(view.position.x, y, view.size.x, 4.0), (VOID[int(k)] as Color).lerp(VOID[mini(int(k) + 1, VOID.size() - 1)], k - floorf(k)))
					y += 4.0
				for i in 3: draw_rect(Rect2(view.position.x, bottom + pad * (0.35 + 0.1 * i), view.size.x, pad * (0.5 - 0.2 * i)), NEBULA)
				_stars(Rect2(view.position.x, bottom + T, view.size.x, view.end.y - bottom - T))
			else:
				for i in SKY.size():
					draw_rect(Rect2(view.position.x, y, view.size.x, pad / SKY.size() + 1.0), SKY[SKY.size() - 1 - i].lerp(HAZE, 0.5))
					y += pad / SKY.size()
				_strip("peaks_far", bottom + pad + 34.0, view)
				_strip("cloud_sea", bottom + pad + 18.0, view)
				_strip("peaks_mid", bottom + pad + 52.0, view)
				_strip("cloud_sea", bottom + pad + 34.0, view, 0.65)
			var faces: Dictionary = v2.get("faces", {}).get("rock", {})
			var lanes := _lanes("s")
			var x0 := maxi(0, floori(view.position.x / T))
			var x1 := mini(room.w, ceili(view.end.x / T))
			for x in range(x0, x1):
				var l := room.levels[(room.h - 1) * room.w + x]
				if l < 0: continue
				var at := Vector2(x * T, bottom - l * T)
				if lanes.has(x):
					# The way down: the path's stairs going on into the haze.
					for k in 2: world.blit(self, "stairs", at + Vector2(0, k * T), T)
					continue
				if faces.is_empty(): continue
				world.blit_layer(self, [str(faces.top[posmod(x, 4)]), Color.WHITE], at)
				world.blit_layer(self, [str(faces.body[posmod(x, 4)]), Color.WHITE], at + Vector2(0, T))
			# The cliff's foot, and the stairs', lost in the cloud (or the void's dark): stepped bands, thicker down.
			var foot: Color = VOID[0] if void_sky else HAZE
			for k in 4:
				draw_rect(Rect2(view.position.x, bottom + T * 1.5 + k * 3.0, view.size.x, 3.0), Color(foot, 0.3 + k * 0.2))

## T3: the void's stars over `area` (art px): one at most in each STAR px square of a lattice that slides by STAR_K as
## the camera pans, most a single pale speck, a few brighter crosses, some twinkling on the water's clock.
func _stars(area: Rect2, k := STAR_K, glint := 1.0, skip := Rect2()) -> void:
	var off := Vector2(roundf(world.camera.position.x * (1.0 - k)), roundf(world.camera.position.y * (1.0 - k)))
	var x0 := floori((area.position.x - off.x) / STAR)
	var x1 := ceili((area.end.x - off.x) / STAR)
	var y0 := floori((area.position.y - off.y) / STAR)
	var y1 := ceili((area.end.y - off.y) / STAR)
	var f := maxi(0, _frame)
	for gy in range(y0, y1):
		for gx in range(x0, x1):
			var h := posmod((gx * 73856093) ^ (gy * 19349663), 1009)
			if h % 5 != 0: continue
			var p := off + Vector2(gx * STAR + (h >> 3) % (STAR - 2), gy * STAR + (h >> 5) % (STAR - 2))
			if not area.has_point(p) or skip.has_point(p): continue
			var a := glint * (0.55 if (h >> 2) % 3 == 0 else 0.85)
			if (h >> 4) % 4 == f % 4: a *= 0.45   # a twinkle
			var c := Color(0.86, 0.92, 1.0, a) if (h >> 6) % 3 else Color(1.0, 0.9, 0.74, a)
			draw_rect(Rect2(p, Vector2.ONE), c)
			if h % 35 == 0:
				for d in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]: draw_rect(Rect2(p + d, Vector2.ONE), Color(c, a * 0.5))

## The columns of the room's `edge` a way leaves by (its lane, as wide as its span).
func _lanes(edge: String) -> Dictionary:
	var out := {}
	for pid in room.def.get("portals", {}):
		var p: Dictionary = room.def.portals[pid]
		if str(p.get("dir", "")) != edge: continue
		for c in TopdownFoliage.portal_lane(p): out[c.x] = true
	return out

## The water going on past the room: its own pattern's tiles on the water's clock, deepening away from the land,
## everywhere in the view outside `inside` (or only past its south edge when `all` is off).
func _water(view: Rect2, inside: Rect2, all: bool) -> void:
	var wv: Dictionary = room.tileset.get("v2", {}).get("water", {})
	if wv.is_empty(): return
	var m: Dictionary = wv.macro
	var frames: Array = m.frames
	var f := maxi(0, _frame)
	var x0 := floori(view.position.x / T)
	var x1 := ceili(view.end.x / T)
	var y0 := floori(view.position.y / T) if all else room.h
	var y1 := ceili(view.end.y / T) if all else room.h + 2
	for y in range(y0, y1):
		for x in range(x0, x1):
			var at := Vector2(x * T, y * T - TopdownRoom.WATER_Z / TopdownRoom.ART)
			if inside.has_point(Vector2(x * T + 1.0, y * T + 1.0)): continue
			var name := str(frames[f][posmod(y, int(m.h)) * int(m.w) + posmod(x, int(m.w))])
			world.blit_layer(self, [name, Color.WHITE], at)
			draw_rect(Rect2(at, Vector2(T, T)), DEEP)
	# T3: the Starsea's water past the star field's edge: the stars glinting in it, dimmer than over the void.
	if void_sky and all: _stars(view, 0.5, 0.6, inside)
