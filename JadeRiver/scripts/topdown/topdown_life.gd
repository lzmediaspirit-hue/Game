class_name TopdownLife
extends Node2D
## Decision 43, the living world (docs/redesign/art_bible.md §14.13): what lives and moves in a room on the grid, for
## TopdownWorld, over the tiles, the foliage (§14.12) and the runtime light (§14.11). Every number is in the const block
## below; the room's own content is data/topdown/life.json (tools/data/topdown_life.py) and its art art/topdown/life.png
## (tools/art/topdown/build_life.py).
##   - One wind for the whole room (`gust`, `wind_phase`): the grass sways with it, smoke drifts along it, banners, the
##     washing and the paper lanterns flap and swing on its clock, faster in a gust.
##   - Critters that notice the player: sparrows fly in, hop and peck, and fly off when a body comes near; butterflies
##     by the flowers and dragonflies over the water flutter up and away; fish glide under the water, rise in rings and
##     dart off; frogs sit and call at the marsh's edge and leap into the water; the village's hens scatter, its cat
##     wakes and walks off, its dog comes to greet you. They are cheap: a capped pool of plain records (no physics, no
##     node each: the ones on the ground borrow one of GROUND_POOL sorted nodes, the rest draw on three shared layers),
##     spawned round the view from the room's area table and its own animals, and dropped once off screen.
##   - People at work (TopdownWork on the room's figures, and a few extras with no part in the story); their cues
##     raise dust, splashes, steam, chips and sparks.
##   - Grass that parts: every body in view (the player, foes, people walking) is a push the foliage's sway shader
##     bends the ground cover away from, rustling faster under a sprint; the walk-through plants (tall grass, cattails)
##     lean aside; a slash over grass throws a few cut blades.
##   - Smoke and fire: chimney smoke over the houses, incense threads at shrines and burners, steam and sparks over the
##     cook fires, the stoves, furnaces and forges.
##   - Interiors: what hangs on the back wall, the sun falling through the windows in shafts onto the floor with dust
##     motes turning in them.
##   - The vista past the room's edge (TopdownVista).
## Settings' "Light and particles" off keeps the critters (fewer) and the work, and drops the smoke, dust and motes;
## Reduce motion halves them.

const DATA := "res://data/topdown/life.json"
const ART := "res://data/topdown/life_art.json"
const T := 16.0

# ------------------------------------------------------------------ the numbers (retune here)
## The wind blows toward the east-south-east, as the cloud shade glides (TopdownLight.CLOUD_DRIFT); its gust (0..1)
## rises and falls on two slow waves. The wind's clock (banners, washing, lanterns) runs at CALM a second, more in a gust.
const WIND := Vector2(0.894, 0.447)
const CALM := 0.65
const GUSTY := 0.9
## A ground critter's sprites by its pose (CritterNode._pose): a hen's brown ones follow its white ones.
const POSES := {
	"sparrow": ["sparrow_stand", "sparrow_hop", "sparrow_peck"],
	"frog": ["frog_sit", "frog_leap"],
	"hen": ["hen_stand", "hen_walk", "hen_peck", "hen_flap", "hen_brown_stand", "hen_brown_walk", "hen_brown_peck", "hen_brown_flap"],
	"cat": ["cat_sit", "cat_sleep", "cat_walk"],
	"dog": ["dog_lie", "dog_sit", "dog_trot"],
}
## The contact shadow's half-width under each (art px).
const BLOB_RX := {"hen": 5.0, "cat": 6.0, "dog": 7.0, "frog": 3.0, "sparrow": 2.0}
## The props that flower (butterflies keep to them).
const FLOWERING := ["bush_azalea", "tree_peach", "tree_plum", "shrub", "pot_orchid", "tree_ribbons"]
## The props whose frames turn on the wind's clock, not their own.
const WINDY := ["banner_jade", "banner_cloud", "laundry_line", "lantern_red"]
## The walk-through plants a body leans aside.
const PLANTS := ["tall_grass", "cattails", "reeds", "grey_reeds"]
## The props that lie flat on the floor and hide no one behind them (no silhouette).
const FLAT := ["mat"]
## Caps: critters at once, the sorted nodes the ones on the ground borrow, puffs of smoke and steam, cut blades, chips
## and sparks, dust motes in the window shafts, and the bodies the grass parts for.
const MAX_CRITTERS := 24
const GROUND_POOL := 12
const MAX_PUFFS := 40
const MAX_BITS := 32
const MAX_MOTES := 18
const MAX_BODIES := 8
## A critter within this many art px of a body flees (x SPRINT_K under a running body); the dog comes instead.
const FLEE := {"sparrow": 34.0, "butterfly": 20.0, "dragonfly": 24.0, "fish": 22.0, "frog": 26.0, "hen": 28.0, "cat": 30.0}
const SPRINT_K := 1.5
## The critters that live on the ground (they borrow a sorted node), and the states a critter moves fast in (stepped
## every frame; the calm ones every CALM_EVERY frames, a dragonfly's darts every other).
const GROUNDED := {"hen": true, "cat": true, "dog": true, "frog": true}
const FAST := {"flee": true, "land": true, "leap": true, "trot": true, "walk": true}
const CALM_EVERY := 3
## The view's margin: critters spawn inside it and are dropped past DROP_PX of it; animals wake and sleep with their
## home within ANIMAL_PX of the view.
const MARGIN := 24.0
const DROP_PX := 56.0
const ANIMAL_PX := 96.0
## Seconds between tries to add a critter, and the kinds' speeds (art px a second).
const SPAWN_S := 0.5
const SPEED := {"sparrow_fly": 70.0, "sparrow_hop": 14.0, "butterfly": 14.0, "butterfly_flee": 40.0, "dragonfly": 22.0,
	"dragonfly_dart": 90.0, "fish": 6.0, "fish_flee": 55.0, "hen": 9.0, "hen_flee": 55.0, "cat": 16.0, "dog": 34.0}
## Smoke: a chimney's puff every CHIMNEY_S, rising at RISE px a second, drifting DRIFT px a second along the wind (more in
## a gust), living PUFF_LIFE seconds; its colour, and steam's.
const CHIMNEY_S := 0.55
const RISE := 11.0
const DRIFT := 5.0
const PUFF_LIFE := [3.2, 4.6]
const SMOKE := Color(0.88, 0.9, 0.92, 0.78)
const STEAM := Color(0.96, 0.97, 0.97, 0.5)
const DUST := Color(0.78, 0.66, 0.5, 0.55)
## The sun through a window: its beam's and its patch's strength (added), and the patch's place from the window by its
## height over the floor (a steep, stylised fall so the patch lies well into the room).
const SHAFT_A := 0.1
const PATCH_A := 0.24
const SHAFT_FALL := Vector2(0.55, 1.25)
## A cue's sound (Audio.world_sound, silent until the bank has it; `cue_raised` is emitted for any other listener) at
## most this often for each name.
const SOUND_GAP := 0.3

signal cue_raised(name: String, at: Vector2)

static var _data: Dictionary = {}
static var _art: Dictionary = {}
static var _tex: Texture2D
static var gust := 0.0          ## the wind's gust now (0..1)
static var wind_phase := 0.0    ## the wind's clock (seconds at the calm rate): banners, washing and lanterns turn on it
static var clock := 0.0
## The living world on (perf_tests turns it off to measure a room against itself without it, interleaved).
static var enabled := true
## Its own work so far, in µs: each frame's step and the drawing of its layers and critters (perf_tests reads it).
static var spent_us := 0
## The same by part (µs): the frame's step, the layers' and critters' drawing, the work loops.
static var spent_parts := {"step": 0, "draw": 0, "work": 0}

var world
var room: TopdownRoom
var def: Dictionary = {}
var life: Dictionary = {}       ## the room's entry of life.json
var area := ""
var rng := RandomNumberGenerator.new()
var extras_on := true
var critters: Array = []
var pool: Array = []            ## the GROUND_POOL sorted nodes (free ones have no critter)
var puffs: Array = []
var bits: Array = []
var motes: Array = []
var emitters: Array = []        ## {kind, at: screen art px, t}
var shafts: Array = []          ## {beam: PackedVector2Array, patch: Rect2, window: Rect2}
var plants: Array = []          ## walk-through plant PropViews
var windy: Array = []           ## PropViews on the wind's clock
var workers: Array = []         ## figures with a work loop
var hangings: Array = []        ## [sprite, Vector2 at]
var ground_cells := PackedVector2Array()   ## cell centres (world units) sparrows land on
var flower_cells := PackedVector2Array()   ## by flowers: butterflies
var water_cells := PackedVector2Array()    ## water: fish; with land beside: dragonflies
var shore_cells := PackedVector2Array()
var frog_cells := PackedVector2Array()     ## land at the water's edge: frogs
var spawned := 0                ## every critter added in this room (tests)
var fled := 0                   ## every critter that fled (tests)
var dropped := 0                ## every critter dropped off screen (tests)
var _spawn_t := 0.0
var _sounds: Dictionary = {}
var _fresh := true
var _cam := Vector2.INF
var _sig_w := -1
var _sig_f := -1
var _sig_a := -1
var _tick := 0
var animals: Array = []         ## the room's animals: [kind, home (world units), home on screen]
var _awake := {}                ## index into animals -> true while it is about
var _sig_light := 0
var vista: TopdownVista
# The layers.
var water_layer: Layer
var floor_layer: Layer
var air: Layer
var light_layer: Layer
var hang_node: Hangings

func _init(w) -> void:
	world = w
	name = "Life"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

static func data() -> Dictionary:
	if _data.is_empty() and FileAccess.file_exists(DATA):
		var d = JSON.parse_string(FileAccess.get_file_as_string(DATA))
		_data = d if d is Dictionary else {}
	return _data

static func art() -> Dictionary:
	if _art.is_empty() and FileAccess.file_exists(ART):
		var d = JSON.parse_string(FileAccess.get_file_as_string(ART))
		_art = d if d is Dictionary else {}
	return _art

static func sheet() -> Texture2D:
	if _tex == null and not art().is_empty(): _tex = load(str(art().get("sheet", "")))
	return _tex

## The room's entry of life.json ({} for a room with nothing of its own).
static func room_life(room_id: String) -> Dictionary:
	return (data().get("rooms", {}) as Dictionary).get(room_id, {})

## The wind's gust at time `t` (0..1): two slow waves, calm most of the time.
static func gust_at(t: float) -> float:
	var g := 0.5 + 0.5 * sin(t * 0.37) * sin(t * 1.13 + 1.7)
	return clampf((g - 0.35) / 0.65, 0.0, 1.0)

## A windy prop's frame now (banners, washing, red lanterns): the wind's clock at the prop's own phase.
static func wind_frame(frames: int, frame_ms: int, phase: int) -> int:
	return (int(wind_phase * 1000.0 / maxf(1.0, float(frame_ms))) + phase) % maxi(1, frames)

# ------------------------------------------------------------------ the room
## Built with the room (TopdownWorld._build_room), after its figures: returns the nodes it adds, for the room to clear.
func build(figures: Dictionary) -> Array:
	room = world.room
	def = Game.room_rt.def if world.live and Game.room_rt != null and Game.room_rt.topdown == room else room.def
	life = room_life(room.id)
	area = str(def.get("backdrop", "")) if not bool(def.get("night", false)) else "valley_night"
	rng.seed = hash(room.id) ^ 0x51f3
	extras_on = TopdownAtmosphere.extras_on()
	var out: Array = [self]
	# The layers: the shadows of things in the air on the floor, the air over everything sorted, the sun's shafts added
	# over it (the fish and rings over the water and the vista are under the floor: under_nodes).
	floor_layer = Layer.new(self, "floor")
	world.floor_layer.add_child(floor_layer)
	out.append(floor_layer)
	air = Layer.new(self, "air")
	air.z_index = 50
	add_child(air)
	light_layer = Layer.new(self, "light")
	light_layer.z_index = 55
	var add := CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	light_layer.material = add
	add_child(light_layer)
	for i in GROUND_POOL:
		var n := CritterNode.new(world)
		n.visible = false
		world.sorted.add_child(n)
		pool.append(n)
		out.append(n)
	_collect()
	_attach_work(figures)
	for e in life.get("extras", []): out.append_array(_extra(e))
	_hangings()
	if not hangings.is_empty():
		hang_node = Hangings.new(world, self)
		world.sorted.add_child(hang_node)
		out.append(hang_node)
	if not GameEvents.event.is_connected(_on_event): GameEvents.event.connect(_on_event)
	_fresh = true
	return out

## The vista past the room's edge and the water's layer (fish, rings) go under the floor: TopdownWorld lays them in its
## list of floor nodes (the vista over the backdrop, the water's layer over the water's chunks and their shade).
func under_nodes() -> Array:
	if vista == null:
		vista = TopdownVista.new(world)
		water_layer = Layer.new(self, "water")
	return [vista, water_layer]

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

## Where the room's critters can be and what in it smokes, the plants that part and the props on the wind's clock.
func _collect() -> void:
	var cells := places(room, area)
	ground_cells = cells[0]
	flower_cells = cells[1]
	water_cells = cells[2]
	shore_cells = cells[3]
	frog_cells = cells[4]
	for a in life.get("animals", []):
		var home := TopdownRoom.cell_point([a[1], a[2]])
		animals.append([str(a[0]), home, TopdownWorld.to_screen(home, room.floor_at(home))])
	# Emitters: chimneys over houses, incense at burners, fire and steam at stoves and forges; the furnishings'.
	for p in room.props:
		var kind := str(p.kind)
		var a: Dictionary = p.art
		var rr: Array = a.get("rect", [0, 0, 16, 16])
		var origin: Array = a.get("origin", [0, 16])
		var c: Vector2i = p.cell
		var ground := 8.0 if int(p.level) < 0 else -float(p.level) * T
		var top_left := Vector2(c.x * T - float(origin[0]), float(c.y + (p.size as Vector2i).y) * T + ground - float(origin[1]))
		match kind:
			"house", "storehouse":
				# Not every house has its fire lit: a hash of its place.
				if TopdownTerrain.h01(c.x, c.y, 43) < 0.7: emitters.append({"kind": "smoke", "at": top_left + Vector2(float(rr[2]) * 0.72, 8.0), "t": rng.randf()})
			"incense": emitters.append({"kind": "incense", "at": top_left + Vector2(8, 9), "t": 0.0})
			"shrine_small": emitters.append({"kind": "incense", "at": top_left + Vector2(12, 17), "t": 0.0})
			"stove": emitters.append({"kind": "steam", "at": top_left + Vector2(9, 5), "t": rng.randf()})
			"forge": emitters.append({"kind": "forge", "at": top_left + Vector2(13, 6), "t": rng.randf()})
	for n in world.sorted.get_children():
		if n is TopdownWorld.PropView:
			if n.kind in WINDY: windy.append(n)
			if n.kind in PLANTS: plants.append(n)
	for o in def.get("objects", []) if world.live else []:
		if not o.has("at"): continue
		var at := TopdownWorld.to_screen(Vector2(float(o.at[0]), float(o.at[1])), float(o.get("alt", 0.0))).round()
		match str(o.get("type", "")):
			"cooking_pot": emitters.append({"kind": "cook", "at": at + Vector2(0, -10), "t": 0.0})
			"alchemy_furnace": emitters.append({"kind": "forge", "at": at + Vector2(0, -22), "t": 0.0})
			"shrine": emitters.append({"kind": "incense", "at": at + Vector2(0, -14), "t": 0.0})

static var _places := {}
## Where a room's critters can be, cell centres (world units): [ground (sparrows), by flowers (butterflies), water
## (fish), water by land (dragonflies), land at the water's edge (frogs)]. A pure function of the room (a hash picks the
## frogs' edge cells outside the marsh), found once and kept by the room's id.
static func places(r: TopdownRoom, area_name: String) -> Array:
	var ck := "%s:%d:%s" % [r.id, r.props.size(), area_name]
	if _places.has(ck): return _places[ck]
	var ground := PackedVector2Array()
	var flower := PackedVector2Array()
	var water := PackedVector2Array()
	var shore := PackedVector2Array()
	var frog := PackedVector2Array()
	var flowers := {}
	for p in r.props:
		var c: Vector2i = p.cell
		if str(p.kind) in FLOWERING:
			for dy in range(-1, 3):
				for dx in range(-1, (p.size as Vector2i).x + 1): flowers[c + Vector2i(dx, dy)] = true
	# Paint marks by their byte: g d p f b s m w, and decision 44's a (sand), n and k (snow).
	var on_ground := {103: true, 100: true, 112: true, 102: true, 98: true, 115: true, 109: true, 119: true, 97: true, 110: true, 107: true}
	var marsh := area_name == "marsh"
	for y in r.h:
		for x in r.w:
			var i := y * r.w + x
			var pt := r.paint[i]
			var cp := Vector2((x + 0.5) * TopdownRoom.TILE, (y + 0.5) * TopdownRoom.TILE)
			if r.levels[i] == TopdownRoom.WATER:
				if r.solid[i] == 1: continue
				water.append(cp)
				if _by(r, x, y, false): shore.append(cp)
				continue
			if r.solid[i] == 1 or r.stair_of[i] > 0: continue
			if on_ground.has(pt): ground.append(cp)
			if pt == 102 or pt == 98 or flowers.has(Vector2i(x, y)): flower.append(cp)
			if (pt == 103 or pt == 109 or pt == 102) and _by(r, x, y, true) and (pt == 109 or marsh or TopdownTerrain.h01(x, y, 77) < 0.5):
				frog.append(cp)
	_places[ck] = [ground, flower, water, shore, frog]
	return _places[ck]

## Has the cell a side neighbour that is water (`water`), or land (not)?
static func _by(r: TopdownRoom, x: int, y: int, water: bool) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var nx: int = x + d.x
		var ny: int = y + d.y
		if not r.inside(nx, ny): continue
		if water == (r.levels[ny * r.w + nx] == TopdownRoom.WATER and r.solid[ny * r.w + nx] == 0): return true
	return false

## The work loops of the room's people (life.json `work`); a quest's staged people keep theirs while a scene has them.
func _attach_work(figures: Dictionary) -> void:
	workers.clear()
	var loops: Dictionary = data().get("loops", {})
	for oid in life.get("work", {}):
		var fig = figures.get(oid)
		if fig == null or not is_instance_valid(fig) or not fig.art is TopdownPlaces.Person: continue
		var w: Dictionary = life.work[oid]
		fig.work = TopdownWork.new(w, loops, fig.plane, float(fig.def.get("alt", 0.0)), str(oid))
		_wear(fig.art, str(loops.get(str(w.loop), {}).get("weapon", "")))
		workers.append(fig)

## An extra at work: a figure in its own outfit with a loop, no label and no talk.
func _extra(e: Dictionary) -> Array:
	var loops: Dictionary = data().get("loops", {})
	var s0: Array = e.spots[0]
	var at := TopdownRoom.cell_point(s0)
	var z: float = room.floor_at(at)
	var o := {"id": str(e.id), "type": "npc", "outfit": e.outfit, "at": [at.x, at.y], "alt": z, "row": str(s0[2]) if s0.size() > 2 else "s"}
	var person := TopdownPlaces.Person.new(o)
	var fig := TopdownPlaces.Figure.new(room, o, person, null, world.player)
	fig.work = TopdownWork.new(e, loops, at, z, str(e.id))
	_wear(person, str(loops.get(str(e.loop), {}).get("weapon", "")))
	world.sorted.add_child(fig)
	workers.append(fig)
	return [fig]

## A loop's weapon worn (a disciple's training sword, the woodcutter's chopper), its sheets asked for on threads.
static func _wear(person, weapon: String) -> void:
	if weapon == "" or str(person.figure.outfit.get("weapon", "none")) == weapon: return
	var o: Dictionary = person.figure.outfit.duplicate()
	o.weapon = weapon
	person.figure.set_outfit(o)
	person.figure.lazy = true
	for l in person.figure.layers: Wardrobe.texture_async(str(l.path))

## What hangs on an interior's back wall and the sun's shafts through its windows.
func _hangings() -> void:
	hangings.clear()
	shafts.clear()
	var sp: Dictionary = art().get("sprites", {})
	for h in life.get("hangings", []):
		var key := "hang_" + str(h[0])
		if not sp.has(key): continue
		var at := Vector2(float(h[1]), float(h[2]))
		hangings.append([key, at])
		if str(h[0]) != "window": continue
		var size: Array = sp[key].size
		var win := Rect2(at, Vector2(float(size[0]), float(size[1])))
		# The patch the sun lays on the floor from the window at its height over the floor (the wall's foot at y 16).
		var hgt := 16.0 - win.get_center().y
		var patch := Rect2(win.position + Vector2(SHAFT_FALL.x * hgt, 16.0 + SHAFT_FALL.y * hgt - win.position.y - 4.0), Vector2(win.size.x, 9.0))
		patch.position = patch.position.round()
		var beam := PackedVector2Array([win.position, Vector2(win.end.x, win.position.y), Vector2(patch.end.x, patch.position.y),
			patch.end, Vector2(patch.position.x, patch.end.y), Vector2(win.position.x, win.end.y)])
		beam = Geometry2D.convex_hull(beam)
		shafts.append({"beam": beam, "patch": patch, "window": win})

# ------------------------------------------------------------------ each frame
func _process(delta: float) -> void:
	if room == null: return
	var t0 := Time.get_ticks_usec()
	clock += delta
	gust = gust_at(clock)
	wind_phase += delta * (CALM + GUSTY * gust) / (CALM + GUSTY * 0.5)
	var view := _view()
	# A room just entered, or the camera jumped (a way taken, a spot placed): its view fills with life at once.
	if _cam.distance_to(view.get_center()) > 160.0: _fresh = true
	_cam = view.get_center()
	_bodies(view)
	_bend(view)
	_step_critters(delta, view)
	_spawn_critters(delta, view)
	_step_puffs(delta, view)
	_step_work(delta)
	_step_motes(delta)
	_fresh = false
	_redraw_layers(view)
	# The foliage's sway shader: the gust and the bodies it parts for (each sent only when it has changed).
	var mat := TopdownFoliage.sway_material()
	var g := snappedf(gust, 0.005)
	if g != _sent_gust:
		_sent_gust = g
		mat.set_shader_parameter("gust", g)
	var arr := PackedVector4Array()
	arr.resize(MAX_BODIES)
	for j in _body_s.size():
		arr[j] = Vector4(_body_s[j].x, _body_s[j].y, 8.0, float(_body_run[j]))
	if arr != _sent_bodies:
		_sent_bodies = arr
		mat.set_shader_parameter("bodies", arr)
	if _body_s.size() != _sent_count:
		_sent_count = _body_s.size()
		mat.set_shader_parameter("body_count", _sent_count)
	spent_us += Time.get_ticks_usec() - t0
	spent_parts.step += Time.get_ticks_usec() - t0

## Each layer redraws only when what it shows has changed on the pixel grid (a signature of its items' whole-pixel
## places and frames), and once more to clear what it showed: most frames most of them hold still.
func _redraw_layers(view: Rect2) -> void:
	var sig_w := 0
	var sig_f := 0
	var sig_a := 0
	var busy_a := false
	for cr: Critter in critters:
		var s: Vector2 = cr.s
		var k := cr.kind
		var at := Vector2i((s - Vector2(0, cr.z)).round())
		var f := int(cr.t * 20.0)
		if k == "fish": sig_w = sig_w * 31 + at.x * 7 + at.y * 13 + int(cr.t * (10.0 if cr.state == "flee" else 4.0)) % 3 + int(cr.alpha * 8.0)
		elif cr.z >= 2.0 and not (k == "sparrow" and cr.state == "ground"):
			sig_f = sig_f * 31 + at.x * 7 + at.y * 13
			sig_a = sig_a * 31 + at.x * 7 + at.y * 13 + f
			busy_a = true
	for p in puffs:
		var at := Vector2i((p.at as Vector2).round())
		var k := float(p.t) / float(p.life)
		if str(p.kind) == "ring": sig_w = sig_w * 31 + at.x + at.y * 3 + int(k * 4.0)
		else: sig_a = sig_a * 31 + at.x * 7 + at.y * 13 + int(k * 24.0)
	for b in bits: sig_a = sig_a * 31 + int((b.at as Vector2).x) * 7 + int((b.at as Vector2).y) * 13
	busy_a = busy_a or not bits.is_empty()
	for e in emitters:
		if str(e.kind) == "incense" and view.grow(24.0).has_point(e.at):
			sig_a = sig_a * 31 + int(clock * 12.0) + int(gust * 4.0)   # a thread sways on its own clock
	if sig_w != _sig_w: water_layer.queue_redraw()
	if sig_f != _sig_f: floor_layer.queue_redraw()
	if sig_a != _sig_a: air.queue_redraw()
	_sig_w = sig_w
	_sig_f = sig_f
	_sig_a = sig_a
	if not shafts.is_empty() and (not motes.is_empty() or _sig_light != 1):
		light_layer.queue_redraw()
		_sig_light = 1

func _view() -> Rect2:
	var vs := Vector2(world.viewport.size) if world.viewport != null else Vector2(640, 360)
	var c: Vector2 = world.camera.position if world.camera != null else vs * 0.5
	return Rect2(c - vs * 0.5, vs)

## The bodies in view the critters and the grass answer: the player, the foes, the people walking about.
## Packed, at most MAX_BODIES, the player first when there is one: `_body_g` ground points (world units), `_body_s` feet on
## screen (art px), `_body_z` height over the ground under them, `_body_run` 0 standing, 1 walking, 2 running.
func _bodies(view: Rect2) -> void:
	_body_g.clear()
	_body_s.clear()
	_body_z.clear()
	_body_run.clear()
	_has_player = false
	var near := view.grow(16.0)
	var p = world.player
	if p != null and p.get("motor") != null:
		var m: TopdownMotor = p.motor
		var v := m.vel.length()
		_body(m.pos, p.screen, m.z - room.ground_under(m.pos, m.z), 2 if m.running and v > 60.0 else (1 if v > 12.0 else 0))
		_has_player = true
	if Game.room_rt != null:
		for uid in world.foe_views:
			if _body_g.size() >= MAX_BODIES: break
			var fv = world.foe_views[uid]
			if not is_instance_valid(fv) or not fv.visible or not near.has_point(fv.feet): continue
			var e: EnemyState = Game.room_rt.enemies.get(uid)
			if e == null or not e.alive: continue
			var ev := e.velocity.length()
			_body(e.plane, fv.feet, 0.0, 2 if ev > 120.0 else (1 if ev > 8.0 else 0))
	for fig in workers:
		if _body_g.size() >= MAX_BODIES: break
		if not is_instance_valid(fig) or fig.work == null or not fig.work.walking or not near.has_point(fig.feet): continue
		_body(fig.plane, fig.feet, 0.0, 2 if fig.work.action == "run" else 1)

func _body(g: Vector2, s: Vector2, z: float, run: int) -> void:
	_body_g.append(g)
	_body_s.append(s)
	_body_z.append(z)
	_body_run.append(run)

## The walk-through plants lean aside from a body among them (and shiver under a runner).
func _bend(view: Rect2) -> void:
	for pv in plants:
		if not is_instance_valid(pv): continue
		var r: Rect2 = pv.rects[0]
		if not r.intersects(view.grow(8.0)):
			continue
		var bend := 0
		var foot := Rect2(r.position.x - 4.0, r.end.y - 14.0, r.size.x + 8.0, 16.0)
		for j in _body_s.size():
			var s := _body_s[j]
			if _body_z[j] > 12.0 or not foot.has_point(s): continue
			bend = 1 if s.x < r.get_center().x else -1
			if _body_run[j] == 2 and int(clock * 12.0) % 2 == 0: bend *= 2
			break
		if bend != pv.bend:
			pv.bend = bend
			pv.queue_redraw()

# ------------------------------------------------------------------ critters
func critter_count(kind := "") -> int:
	if kind == "": return critters.size()
	return critters.filter(func(c): return str(c.kind) == kind).size()

## How many of each wild kind this room wants in view now: its area's table (the room's own overrides), the day-only
## kinds asleep after dark, fewer with the extras off or under Reduce motion.
func wanted(kind: String) -> int:
	var table: Dictionary = (data().get("critters", {}) as Dictionary).get(area, (data().get("critters", {}) as Dictionary).get("", {}))
	var n := int(table.get(kind, 0))
	if n <= 0: return 0
	var hour := str(world.atmosphere.now.get("hour", "day")) if world.atmosphere != null and not world.atmosphere.now.is_empty() else "day"
	if kind in data().get("day_only", []) and hour in ["night", "night_story"]: return 0
	if kind == "frog" and hour in ["night", "night_story"]: n += 1
	if not extras_on or UiKit.reduce_motion(): n = maxi(1, n / 2)
	return n

func _spawn_critters(delta: float, view: Rect2) -> void:
	_spawn_t -= delta
	# The animals of the room: awake while their home is near the view.
	var near_view := view.grow(ANIMAL_PX)
	for i in animals.size():
		var a: Array = animals[i]
		if near_view.has_point(a[2]) and not _awake.has(i) and critters.size() < MAX_CRITTERS: _add_animal(str(a[0]), a[1], i)
	if _spawn_t > 0.0 and not _fresh: return
	_spawn_t = SPAWN_S
	var tries := 8 if _fresh else 1
	for kind in ["sparrow", "butterfly", "dragonfly", "fish", "frog"]:
		for k in tries:
			var n := wanted(kind)
			var have := critters.filter(func(c): return str(c.kind) == kind).size()
			if kind == "sparrow": have = critters.filter(func(c): return str(c.kind) == kind and c.lead).size()
			if have >= n or critters.size() >= MAX_CRITTERS: break
			_add_wild(kind, view)

## A new wild critter round the view (the first frame of a room fills its view at once); none past the cap.
func _add_wild(kind: String, view: Rect2) -> void:
	if critters.size() >= MAX_CRITTERS: return
	match kind:
		"sparrow":
			var c := _pick(ground_cells, view.grow(-MARGIN))
			if c.x == INF or _body_near(c, FLEE.sparrow * 2.0): return
			var n := 2 + rng.randi() % 3
			var lead_side := -1.0 if rng.randf() < 0.5 else 1.0
			for i in n:
				if critters.size() >= MAX_CRITTERS: break
				var g := room.nearest_standable(c + Vector2(rng.randf_range(-24, 24), rng.randf_range(-16, 16)))
				var cr := _critter("sparrow", g)
				cr.lead = i == 0
				if _fresh:
					cr.state = "ground"
				else:
					# Flying in: from past the view's side, gliding down to where it lands.
					cr.state = "land"
					cr.z = 60.0 + rng.randf() * 20.0
					var side := -1.0 if (lead_side < 0.0) else 1.0
					cr.g = g + Vector2(side * (200.0 + rng.randf() * 40.0), -40.0 - rng.randf() * 30.0) * TopdownRoom.ART
					cr.target = g
				cr.face = 1 if rng.randf() < 0.5 else -1
		"butterfly":
			var c := _pick(flower_cells, view.grow(-MARGIN))
			if c.x == INF: return
			var cr := _critter("butterfly", c)
			cr.anchor = c
			cr.z = 6.0 + rng.randf() * 8.0
			cr.variant = ["white", "gold", "blue", "coral"][rng.randi() % 4]
		"dragonfly":
			var c := _pick(shore_cells, view.grow(-MARGIN))
			if c.x == INF: return
			var cr := _critter("dragonfly", c)
			cr.anchor = c
			cr.z = 8.0 + rng.randf() * 6.0
		"fish":
			var c := _pick(water_cells, view.grow(-MARGIN))
			if c.x == INF: return
			var cr := _critter("fish", c + Vector2(rng.randf_range(-10, 10), rng.randf_range(-10, 10)))
			cr.anchor = c
			cr.floor = TopdownRoom.WATER_Z
			cr.v = Vector2.from_angle(rng.randf() * TAU) * SPEED.fish
		"frog":
			var c := _pick(frog_cells, view.grow(-MARGIN))
			if c.x == INF or _body_near(c, FLEE.frog * 2.0): return
			var cr := _critter("frog", c + Vector2(rng.randf_range(-8, 8), rng.randf_range(-6, 6)))
			cr.state = "sit"
			# It faces the water it will leap into.
			var cc := TopdownRoom.cell_of(c)
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				if room.is_water(cc.x + d.x, cc.y + d.y): cr.water = Vector2(d)
			cr.face = 1 if cr.water.x >= 0.0 else -1

func _add_animal(kind: String, home: Vector2, id: int) -> void:
	if critters.size() >= MAX_CRITTERS: return
	var base := kind.get_slice("_", 0)
	var cr := _critter(base, home)
	_awake[id] = true
	cr.variant = kind
	cr.home = home
	cr.hs = animals[id][2]
	cr.home_id = id
	cr.state = {"hen": "wander", "cat": "sleep", "dog": "lie"}.get(base, "wander")
	cr.face = 1 if (id & 1) == 0 else -1

func _critter(kind: String, g: Vector2) -> Critter:
	var cr := Critter.new()
	cr.kind = kind
	cr.g = g
	cr.floor = room.floor_at(g)
	cr.t = rng.randf() * 3.0
	cr.alpha = 0.0 if not _fresh else 1.0
	cr.s = TopdownWorld.to_screen(g, cr.floor)
	cr.anchor = g
	cr.target = g
	critters.append(cr)
	spawned += 1
	return cr

## A random cell of `list` whose centre lies in `r`; INF when none is found in a few tries.
func _pick(list: PackedVector2Array, r: Rect2) -> Vector2:
	if list.is_empty(): return Vector2.INF
	for i in 10:
		var c := list[rng.randi() % list.size()]
		if r.has_point(TopdownWorld.to_screen(c, room.floor_at(c))): return c
	return Vector2.INF

## Is a body within `px` art px of ground point `g` (0 when none): the distance to the nearest.
func _body_near(g: Vector2, px: float) -> bool:
	return _nearest(g).x < px

## The nearest body to ground point `g`: Vector3(its distance in art px, the away direction's x, y), and whether it runs
## in `last_run`.
var last_run := false
var last_player := false
var _body_g := PackedVector2Array()
var _body_s := PackedVector2Array()
var _body_z := PackedFloat32Array()
var _body_run := PackedByteArray()
var _has_player := false
## What the shared sway material was last sent (by whichever room's life): sent again only when it changes.
static var _sent_gust := -1.0
static var _sent_bodies := PackedVector4Array()
static var _sent_count := -1
func _nearest(g: Vector2) -> Vector3:
	var best := Vector3(INF, 0, 0)
	last_run = false
	last_player = false
	var bi := -1
	var bd := INF
	for i in _body_g.size():
		var d2 := g.distance_squared_to(_body_g[i])
		if d2 < bd:
			bd = d2
			bi = i
	if bi < 0: return best
	var d := g - _body_g[bi]
	var away := d.normalized() if d.length() > 0.1 else Vector2.RIGHT
	last_run = _body_run[bi] == 2
	last_player = bi == 0 and _has_player
	return Vector3(d.length() / TopdownRoom.ART, away.x, away.y)

func _step_critters(delta: float, view: Rect2) -> void:
	var keep: Array = []
	_tick += 1
	var near_view := view.grow(DROP_PX)
	var home_view := view.grow(ANIMAL_PX + DROP_PX)
	for i in critters.size():
		var cr: Critter = critters[i]
		# A calm critter steps on one frame in CALM_EVERY (its share of the list), that much further: under a pixel a step
		# at its pace, the same on the pixel grid at a third of the cost; one on the move (fleeing, landing, leaping,
		# trotting) steps every frame, a dragonfly (darting) every other.
		cr.skip += delta
		if (i + _tick) % (2 if cr.kind == "dragonfly" else CALM_EVERY) != 0 and not (cr.state in FAST):
			keep.append(cr)
			continue
		var dt := cr.skip
		cr.skip = 0.0
		cr.t = cr.t + dt
		cr.st = cr.st + dt
		cr.alpha = minf(1.0, cr.alpha + dt * 2.0)
		var alive := true
		match cr.kind:
			"sparrow": alive = _sparrow(cr, dt)
			"butterfly", "dragonfly": alive = _insect(cr, dt)
			"fish": alive = _fish(cr, dt)
			"frog": alive = _frog(cr, dt)
			"hen": _hen(cr, dt)
			"cat": _cat(cr, dt)
			"dog": _dog(cr, dt)
		var s := TopdownWorld.to_screen(cr.g, cr.floor)
		cr.s = s
		# Dropped once well off the view (an animal with its home far from it).
		if cr.home_id >= 0:
			if not home_view.has_point(cr.hs): alive = false
		elif not near_view.has_point(s - Vector2(0, cr.z)) and cr.state != "land":
			alive = false
		if not alive:
			dropped += 1
			_release(cr)
			if cr.home_id >= 0: _awake.erase(cr.home_id)
			continue
		keep.append(cr)
		_seat(cr)
	critters = keep

## A critter on the ground borrows a sorted node (so a house hides it); one in the air or the water draws on a layer.
func _seat(cr: Critter) -> void:
	var on_ground := cr.state == "ground" if cr.kind == "sparrow" else cr.kind in GROUNDED
	if on_ground and cr.node == null:
		for n in pool:
			if n.critter == null:
				cr.node = n
				n.critter = cr
				n.visible = true
				break
	elif not on_ground and cr.node != null:
		_release(cr)
	if cr.node != null: cr.node.sync(room)

func _release(cr: Critter) -> void:
	if cr.node != null and is_instance_valid(cr.node):
		cr.node.critter = null
		cr.node.visible = false
	cr.node = null

func _flee_from(cr: Critter) -> Vector3:
	var near := _nearest(cr.g)
	var r := float(FLEE.get(cr.kind, 24.0)) * (SPRINT_K if last_run else 1.0)
	return near if near.x < r else Vector3(INF, 0, 0)

func _sparrow(cr: Critter, delta: float) -> bool:
	match cr.state:
		"land":
			var to: Vector2 = cr.target
			var d: Vector2 = to - cr.g
			var sp := SPEED.sparrow_fly * TopdownRoom.ART
			if d.length() < sp * delta:
				cr.g = to
				cr.z = 0.0
				cr.state = "ground"
				cr.st = 0.0
			else:
				cr.g += d.normalized() * sp * delta
				cr.z = clampf(d.length() / TopdownRoom.ART * 0.3, 1.0, cr.z)   # gliding down as it comes in
				cr.face = 1 if d.x >= 0.0 else -1
		"ground":
			var f := _flee_from(cr)
			if f.x < INF:
				_flee(cr, Vector2(f.y, f.z), "sparrow")
				# The flock goes up together.
				for o in critters:
					if o != cr and str(o.kind) == "sparrow" and str(o.state) == "ground" and (o.g as Vector2).distance_to(cr.g) < 90.0:
						_flee(o, Vector2(f.y, f.z).rotated(rng.randf_range(-0.5, 0.5)), "")
				return true
			# Hop a step now and then, peck between.
			if cr.st > 0.6 + fmod(cr.t * 0.37, 0.8):
				cr.st = 0.0
				var hop := Vector2(rng.randf_range(-1, 1), rng.randf_range(-0.6, 0.6)).normalized() * SPEED.sparrow_hop * 0.4 * TopdownRoom.ART
				var to := cr.g + hop
				if room.standable(TopdownRoom.cell_of(to)) and absf(room.floor_at(to) - cr.floor) < 4.0:
					cr.g = to
					cr.face = 1 if hop.x >= 0.0 else -1
					cr.hop_t = 0.18
			cr.hop_t = maxf(0.0, cr.hop_t - delta)
		"flee":
			cr.g += cr.v * delta
			cr.z = cr.z + 46.0 * delta
	return true

func _flee(cr: Critter, away: Vector2, sound: String) -> void:
	cr.state = "flee"
	cr.st = 0.0
	fled += 1
	var sp: float = SPEED.get(cr.kind + "_flee", SPEED.get(cr.kind + "_fly", 50.0))
	cr.v = (away + Vector2(0, -0.3)).normalized() * sp * TopdownRoom.ART
	cr.face = 1 if away.x >= 0.0 else -1
	if sound != "": raise_cue(sound + "_flee", cr.g)

func _insect(cr: Critter, delta: float) -> bool:
	var dart := cr.kind == "dragonfly"
	if cr.state == "flee":
		cr.g += cr.v * delta
		cr.z = cr.z + 18.0 * delta
		return cr.st < 3.0
	var f := _flee_from(cr)
	if f.x < INF:
		_flee(cr, Vector2(f.y, f.z), "")
		return true
	var anchor: Vector2 = cr.anchor
	if dart:
		# Hover, then dart to a new place over the water near its anchor.
		if cr.st > 1.1 + fmod(cr.t, 0.9):
			cr.st = 0.0
			cr.target = anchor + Vector2(rng.randf_range(-40, 40), rng.randf_range(-24, 24))
		var to: Vector2 = cr.target
		var d := to - cr.g
		var sp := (SPEED.dragonfly_dart if d.length() > 6.0 else SPEED.dragonfly) * TopdownRoom.ART * 0.5
		cr.g += d.limit_length(sp * delta)
		if absf(d.x) > 1.0: cr.face = 1 if d.x > 0.0 else -1
		cr.z = 9.0 + sin(cr.t * 3.0) * 2.0
	else:
		# Flutter on a loose loop round the flowers, bobbing.
		var a := cr.t * 0.9 + float(hash(cr.variant) % 7)
		var to := anchor + Vector2(cos(a) * 18.0 + sin(a * 2.3) * 8.0, sin(a * 1.3) * 12.0) * TopdownRoom.ART
		var d := to - cr.g
		cr.g += d.limit_length(SPEED.butterfly * TopdownRoom.ART * delta)
		if absf(d.x) > 1.0: cr.face = 1 if d.x > 0.0 else -1
		cr.z = 8.0 + sin(cr.t * 2.1) * 4.0 + sin(cr.t * 7.0) * 1.0
	return true

func _fish(cr: Critter, delta: float) -> bool:
	if cr.state == "flee":
		cr.g += cr.v * delta
		cr.v = cr.v * (1.0 - delta * 1.5)
		if cr.v.length() < 20.0: cr.state = "swim"
	else:
		var f := _flee_from(cr)
		if f.x < INF:
			_flee(cr, Vector2(f.y, f.z), "fish")
			_ring(cr.g)
			return true
		# Glide, turning slowly; rise now and then in a ring.
		cr.v = cr.v.rotated(sin(cr.t * 0.7 + float(hash(str(cr.g.x)) % 5)) * 0.6 * delta)
		if cr.st > 5.0 + fmod(cr.t * 1.7, 5.0):
			cr.st = 0.0
			_ring(cr.g)
	var to: Vector2 = cr.g + cr.v * delta
	var c := TopdownRoom.cell_of(to)
	if room.is_water(c.x, c.y): cr.g = to
	else: cr.v = -cr.v
	if cr.v.length() > 0.1: cr.face = 1 if cr.v.x >= 0.0 else -1
	return true

func _frog(cr: Critter, delta: float) -> bool:
	match cr.state:
		"sit":
			var f := _flee_from(cr)
			if f.x < INF:
				cr.state = "leap"
				cr.st = 0.0
				fled += 1
				var w: Vector2 = cr.water if cr.water != Vector2.ZERO else Vector2(f.y, f.z)
				cr.v = w * 34.0 * TopdownRoom.ART
				cr.face = 1 if w.x >= 0.0 else -1
				raise_cue("frog_leap", cr.g)
		"leap":
			cr.g += cr.v * delta
			cr.z = maxf(0.0, sin(clampf(cr.st / 0.45, 0.0, 1.0) * PI) * 9.0)
			if cr.st >= 0.45:
				_ring(cr.g)
				raise_cue("frog_plop", cr.g)
				return false
	return true

func _hen(cr: Critter, delta: float) -> void:
	var f := _flee_from(cr)
	if f.x < INF and cr.state != "flee":
		cr.state = "flee"
		cr.st = 0.0
		fled += 1
		cr.v = Vector2(f.y, f.z) * SPEED.hen_flee * TopdownRoom.ART
		raise_cue("hen_flap", cr.g)
	match cr.state:
		"flee":
			_walk_home(cr, cr.v, delta)
			if cr.st > 0.7:
				cr.state = "wander"
				cr.st = 0.0
		"wander":
			if cr.st > 1.8:
				cr.st = 0.0
				cr.state = "peck"
			var home: Vector2 = cr.home
			var to: Vector2 = home + Vector2(sin(cr.t * 0.4 + float(cr.home_id % 5)), cos(cr.t * 0.31)) * 26.0 * TopdownRoom.ART
			var d := to - cr.g
			_walk_home(cr, d.limit_length(SPEED.hen * TopdownRoom.ART), delta)
		"peck":
			if cr.st > 1.4:
				cr.st = 0.0
				cr.state = "wander"

func _cat(cr: Critter, delta: float) -> void:
	var near := _nearest(cr.g)
	match cr.state:
		"sleep":
			if near.x < 44.0 and last_player:
				cr.state = "sit"
				cr.st = 0.0
				raise_cue("cat_wake", cr.g)
		"sit":
			if near.x < FLEE.cat * (SPRINT_K if last_run else 1.0):
				cr.state = "walk"
				cr.st = 0.0
				fled += 1
				cr.v = Vector2(near.y, near.z) * SPEED.cat * TopdownRoom.ART
			elif near.x > 90.0 and cr.st > 3.0:
				cr.state = "home"
		"walk":
			_walk_home(cr, cr.v, delta)
			if cr.st > 1.6:
				cr.state = "sit"
				cr.st = 0.0
		"home":
			var d: Vector2 = cr.home - cr.g
			if d.length() < 3.0:
				cr.state = "sleep"
			else:
				_walk_home(cr, d.limit_length(SPEED.cat * 0.6 * TopdownRoom.ART), delta)
			if near.x < 44.0: cr.state = "sit"

func _dog(cr: Critter, delta: float) -> void:
	var near := _nearest(cr.g)
	var player_near := near.x < 70.0 and last_player
	match cr.state:
		"lie":
			if player_near:
				cr.state = "sit"
				cr.st = 0.0
		"sit":
			if near.x > 26.0 and near.x < 70.0 and cr.st > 0.8 and last_player:
				cr.state = "trot"
				cr.st = 0.0
				raise_cue("dog_bark", cr.g)
			elif near.x > 110.0 and cr.st > 2.0:
				cr.state = "home"
		"trot":
			# To the player, stopping short to sit and wag.
			var toward := -Vector2(near.y, near.z)
			if near.x < 22.0 or not last_player or cr.g.distance_to(cr.home) > 110.0 * TopdownRoom.ART:
				cr.state = "sit"
				cr.st = 0.0
			else:
				_walk_home(cr, toward * SPEED.dog * TopdownRoom.ART, delta)
		"home":
			var d: Vector2 = cr.home - cr.g
			if d.length() < 3.0:
				cr.state = "lie"
			else:
				_walk_home(cr, d.limit_length(SPEED.dog * 0.6 * TopdownRoom.ART), delta)
			if player_near: cr.state = "sit"

## An animal steps along `v` (world units a second) where a body may stand on its floor, turning back where it may not.
func _walk_home(cr: Critter, v: Vector2, delta: float) -> void:
	var to: Vector2 = cr.g + v * delta
	# The floor is asked only when the step crosses into another cell.
	var same := TopdownRoom.cell_of(to) == TopdownRoom.cell_of(cr.g)
	if same or (room.standable(TopdownRoom.cell_of(to)) and absf(room.floor_at(to) - cr.floor) < 4.0):
		cr.g = to
	else:
		cr.v = -cr.v
	if absf(v.x) > 0.5: cr.face = 1 if v.x > 0.0 else -1
	cr.moving = v.length() > 1.0

## A ripple where something breaks the water.
func _ring(g: Vector2) -> void:
	if puffs.size() >= MAX_PUFFS: return
	puffs.append({"kind": "ring", "at": TopdownWorld.to_screen(g, TopdownRoom.WATER_Z).round(), "t": 0.0, "life": 0.8})

# ------------------------------------------------------------------ smoke, steam, sparks and dust
func _step_puffs(delta: float, view: Rect2) -> void:
	var drift := WIND * (DRIFT + DRIFT * 1.6 * gust)
	for e in emitters:
		if not view.grow(48.0).has_point(e.at): continue
		e.t = float(e.t) - delta
		if float(e.t) > 0.0: continue
		match str(e.kind):
			"smoke":
				e.t = CHIMNEY_S * (1.0 if extras_on else 2.0)
				_puff("smoke", e.at + Vector2(rng.randf_range(-1, 1), 0))
			"steam", "cook":
				e.t = 0.7
				_puff("steam", e.at + Vector2(rng.randf_range(-3, 3), 0))
				if str(e.kind) == "cook" and rng.randf() < 0.6: _spark(e.at + Vector2(rng.randf_range(-3, 3), 6), Color("ffb060"))
			"forge":
				e.t = 0.45
				_puff("smoke", e.at + Vector2(rng.randf_range(-2, 2), -2))
				_spark(e.at + Vector2(rng.randf_range(-4, 4), 0), Color("ffc070"))
			"incense": e.t = 999.0   # drawn as a thread, not puffs
	for i in range(puffs.size() - 1, -1, -1):
		var p: Dictionary = puffs[i]
		p.t = float(p.t) + delta
		if str(p.kind) in ["smoke", "steam", "dust"]:
			var k := float(p.t) / float(p.life)
			p.at += (Vector2(0, -RISE * (1.0 - k * 0.4)) + drift * (0.3 + k)) * delta
		if float(p.t) >= float(p.life): puffs.remove_at(i)
	for i in range(bits.size() - 1, -1, -1):
		var b: Dictionary = bits[i]
		b.t = float(b.t) + delta
		b.at += (b.v as Vector2) * delta
		b.v = (b.v as Vector2) + Vector2(0, float(b.get("g", 140.0))) * delta
		if float(b.t) >= float(b.life): bits.remove_at(i)

func _puff(kind: String, at: Vector2) -> void:
	if not extras_on and kind != "smoke": return
	var cap := MAX_PUFFS if not UiKit.reduce_motion() else MAX_PUFFS / 2
	if puffs.size() >= cap: return
	var life: float = rng.randf_range(float(PUFF_LIFE[0]), float(PUFF_LIFE[1])) * (0.6 if kind == "dust" else 1.0)
	puffs.append({"kind": kind, "at": at, "t": 0.0, "life": life, "seed": rng.randi() % 7})

func _spark(at: Vector2, col: Color, n := 1, up := 30.0) -> void:
	for i in n:
		if bits.size() >= MAX_BITS: return
		bits.append({"at": at, "v": Vector2(rng.randf_range(-14, 14), -rng.randf_range(up * 0.6, up)), "t": 0.0, "life": rng.randf_range(0.35, 0.7),
			"col": col, "g": 60.0, "glow": true})

## Cut blades, chips, drops: a few bits thrown from `at` along `dir`, falling back.
func _bits(at: Vector2, dir: Vector2, cols: Array, n: int) -> void:
	if not extras_on: n = maxi(1, n / 2)
	for i in n:
		if bits.size() >= MAX_BITS: return
		var v := dir.rotated(rng.randf_range(-0.8, 0.8)) * rng.randf_range(20, 46) + Vector2(0, -rng.randf_range(24, 44))
		bits.append({"at": at + Vector2(rng.randf_range(-3, 3), rng.randf_range(-2, 2)), "v": v, "t": 0.0, "life": rng.randf_range(0.4, 0.7),
			"col": cols[i % cols.size()], "g": 150.0})

# ------------------------------------------------------------------ work
## The cues of the people at work: dust off a broom, a splash at the tub, steam at the pot, chips off the block,
## sparks off the anvil and the forge, a ring where a line is cast.
func _step_work(delta: float) -> void:
	for fig in workers:
		if not is_instance_valid(fig) or fig.work == null or not fig.visible: continue
		var w: TopdownWork = fig.work
		var dir := Vector2.from_angle(deg_to_rad(float(TopdownMotor.ROW_ANGLES.get(w.row, 90.0))))
		var front: Vector2 = (fig.feet as Vector2) + dir * Vector2(10, 5)
		var cue := w.step_cue
		if w.cue != "": raise_cue("work_" + w.cue, fig.plane)
		if w.hit:
			match cue:
				"chop":
					_bits(front + Vector2(0, -3), dir, [Color("e2be88"), Color("ad7b46"), Color("cb9c63")], 5)
					raise_cue("work_chop_hit", fig.plane)
				"hammer":
					_spark(front + Vector2(0, -6), Color("ffd070"), 5, 44.0)
					raise_cue("work_hammer_hit", fig.plane)
		if not extras_on: continue
		var tick := fmod(w.t, 0.5) < delta
		match cue:
			"sweep":
				if tick: _puff("dust", front + Vector2(rng.randf_range(-3, 3), 0))
			"scrub":
				if tick: _bits(front + Vector2(4, -2), Vector2.UP, [Color("a9e6c9"), Color("e9fbf1")], 2)
			"stir":
				if tick: _puff("steam", front + Vector2(0, -10))
			"stoke":
				if tick: _spark(front + Vector2(0, -10), Color("ffc070"), 2, 36.0)
			"pick", "grind":
				if fmod(w.t, 0.9) < delta: _bits(front, Vector2.UP, [Color("87c749"), Color("45a03a")], 2)
		if w.walking and str(w.loop.get("tool", "")) == "broom" and fmod(w.t, 0.4) < delta: _puff("dust", front)

# ------------------------------------------------------------------ interiors: the sun's motes
func _step_motes(delta: float) -> void:
	if shafts.is_empty() or not extras_on: return
	var cap := MAX_MOTES if not UiKit.reduce_motion() else MAX_MOTES / 2
	while motes.size() < cap:
		var s: Dictionary = shafts[rng.randi() % shafts.size()]
		var beam: PackedVector2Array = s.beam
		var box := Rect2(beam[0], Vector2.ZERO)
		for q in beam: box = box.expand(q)
		var at := box.position + Vector2(rng.randf() * box.size.x, rng.randf() * box.size.y)
		if not Geometry2D.is_point_in_polygon(at, beam): continue
		motes.append({"at": at, "v": Vector2(rng.randf_range(-1.5, 2.5), rng.randf_range(-1.0, 1.5)), "t": rng.randf() * 4.0, "life": rng.randf_range(4.0, 8.0),
			"beam": beam})
	for i in range(motes.size() - 1, -1, -1):
		var m: Dictionary = motes[i]
		m.t = float(m.t) + delta
		m.at += (m.v as Vector2) * delta + Vector2(sin(float(m.t) * 0.8) * 0.8, 0) * delta
		if float(m.t) >= float(m.life) or not Geometry2D.is_point_in_polygon(m.at, m.beam): motes.remove_at(i)

# ------------------------------------------------------------------ events and cues
func _on_event(ev: String, p: Dictionary) -> void:
	match ev:
		"settings_changed":
			extras_on = TopdownAtmosphere.extras_on()
		"attack_started":
			# A slash over grass throws a few cut blades (not a technique; the player's own blows).
			if str(p.get("actor", "")) != Game.active_id or str(p.get("technique", "")) != "" or world.player == null: return
			var m: TopdownMotor = world.player.motor
			var aim: Vector2 = p.get("aim", m.dir)
			var at := m.pos + aim.normalized() * 22.0
			var c := TopdownRoom.cell_of(at)
			var grassy := room.inside(c.x, c.y) and room.paint_at(c.x, c.y) in ["g", "f", "m", "b"]
			for pv in plants:
				if is_instance_valid(pv) and (pv.rects[0] as Rect2).has_point(TopdownWorld.to_screen(at, m.z)): grassy = true
			if grassy and m.grounded:
				_bits(TopdownWorld.to_screen(at, m.z) + Vector2(0, -3), aim.normalized(), [Color("87c749"), Color("45a03a"), Color("cbe86c")], 6)

## A sound for a moment of life (a bird's wings, a frog's plop, a hammer on the anvil): the `cue_raised` signal, and
## the world sound "life_" + name where it happens (Audio.world_sound: positional, under the fight's sounds) while it
## is in view and the sound bank has it, each name at most every SOUND_GAP. The walking people's steps are
## the sound's own (TopdownSound steps a figure on its walk).
func raise_cue(cue_name: String, g: Vector2) -> void:
	cue_raised.emit(cue_name, g)
	var now := clock
	if now - float(_sounds.get(cue_name, -99.0)) < SOUND_GAP: return
	_sounds[cue_name] = now
	var id := "life_" + cue_name
	if SoundBank.has_sound(id) and _view().grow(8.0).has_point(TopdownWorld.to_screen(g, 0.0)): Audio.world_sound(id, g)

# ------------------------------------------------------------------ drawing
## A sprite of the sheet: frame `f` of `name`, its foot at `at`, mirrored when `flip`, tinted `col`.
static func blit(ci: CanvasItem, sprite: String, f: int, at: Vector2, flip := false, col := Color.WHITE) -> void:
	var sp: Dictionary = art().get("sprites", {}).get(sprite, {})
	if sp.is_empty() or sheet() == null: return
	var r: Array = sp.rect
	var size: Array = sp.size
	var foot: Array = sp.foot
	var n := int(sp.frames)
	var src := Rect2(float(r[0]) + float(size[0]) * float(posmod(f, n)), float(r[1]), float(size[0]), float(size[1]))
	var fx := float(foot[0])
	var dst := Rect2(at - Vector2(float(size[0]) - 1.0 - fx if flip else fx, float(foot[1])), src.size)
	dst.position = dst.position.round()
	if flip:
		ci.draw_set_transform(Vector2(dst.position.x * 2.0 + dst.size.x, 0), 0.0, Vector2(-1, 1))
		ci.draw_texture_rect_region(sheet(), dst, src, col)
		ci.draw_set_transform(Vector2.ZERO)
	else:
		ci.draw_texture_rect_region(sheet(), dst, src, col)

func draw_layer(ci: CanvasItem, which: String) -> void:
	var t0 := Time.get_ticks_usec()
	match which:
		"water": _draw_water(ci)
		"floor": _draw_floor(ci)
		"air": _draw_air(ci)
		"light": _draw_light(ci)
	spent_us += Time.get_ticks_usec() - t0
	spent_parts.draw += Time.get_ticks_usec() - t0

func _draw_water(ci: CanvasItem) -> void:
	for cr: Critter in critters:
		if cr.kind != "fish": continue
		var s: Vector2 = cr.s
		var f := int(cr.t * (10.0 if cr.state == "flee" else 4.0)) % 3
		blit(ci, "fish", f, s.round(), cr.face < 0, Color(1, 1, 1, cr.alpha))
	for p in puffs:
		if str(p.kind) != "ring": continue
		var k := float(p.t) / float(p.life)
		blit(ci, "ring", mini(3, int(k * 4.0)), p.at)

## On the floor: the small shadows of things in the air (a bird, a butterfly), and the sun's patches in an interior.
func _draw_floor(ci: CanvasItem) -> void:
	for cr: Critter in critters:
		var z := cr.z
		if z < 2.0 or cr.kind == "fish" or cr.state == "land" and z > 40.0: continue
		var s: Vector2 = cr.s
		var a := clampf(0.3 - z / 200.0, 0.08, 0.3) * cr.alpha
		var at := (s + Vector2(z * 0.45, z * 0.2)).round()
		ci.draw_rect(Rect2(at - Vector2(1, 0), Vector2(3, 1)), Color(TopdownLight.SHADOW, a))

func _draw_air(ci: CanvasItem) -> void:
	# Smoke and steam, lit from the north-west, thinning as they rise.
	for p in puffs:
		var kind := str(p.kind)
		if kind == "ring": continue
		var k := float(p.t) / float(p.life)
		var col: Color = SMOKE if kind == "smoke" else (STEAM if kind == "steam" else DUST)
		var size := mini(3, int(k * 3.4) + (1 if kind == "smoke" else 0))
		if kind == "dust": size = mini(1, int(k * 2.0))
		var a := col.a * clampf(k * 6.0, 0.0, 1.0) * clampf((1.0 - k) * 1.8, 0.0, 1.0)
		blit(ci, "puff_%d" % size, 0, (p.at as Vector2).round(), false, Color(col, a))
	# Incense: a thin thread rising from each burner in view, bent by the wind.
	var view := _view().grow(24.0)
	for e in emitters:
		if str(e.kind) != "incense" or not view.has_point(e.at): continue
		var at: Vector2 = e.at
		for j in 14:
			var x := sin(clock * 1.7 + j * 0.45) * (0.4 + j * 0.12) + j * (0.25 + gust * 0.35)
			var a := 0.55 * (1.0 - j / 14.0)
			ci.draw_rect(Rect2((at + Vector2(x, -j * 1.0)).round(), Vector2.ONE), Color(0.88, 0.9, 0.93, a))
	# Bits: cut blades, chips, drops and sparks.
	for b in bits:
		var col: Color = b.col
		var a := clampf((1.0 - float(b.t) / float(b.life)) * 2.0, 0.0, 1.0)
		ci.draw_rect(Rect2((b.at as Vector2).round(), Vector2.ONE), Color(col, col.a * a))
	# Critters in the air: sparrows flying, butterflies, dragonflies.
	for cr: Critter in critters:
		var kind := cr.kind
		var s: Vector2 = cr.s
		var at := (s - Vector2(0, cr.z)).round()
		var col := Color(1, 1, 1, cr.alpha)
		match kind:
			"sparrow":
				if cr.state == "ground": continue
				blit(ci, "sparrow_fly", int(cr.t * 14.0), at, cr.face < 0, col)
			"butterfly":
				blit(ci, "butterfly_" + cr.variant, int(cr.t * (16.0 if cr.state == "flee" else 10.0)), at, false, col)
			"dragonfly":
				blit(ci, "dragonfly", int(cr.t * 20.0), at, cr.face < 0, col)

## The sun through an interior's windows: a faint beam, its patch on the floor with the lattice's bars in it, and the
## dust turning in it (added over the room).
func _draw_light(ci: CanvasItem) -> void:
	for s in shafts:
		ci.draw_colored_polygon(s.beam, Color(TopdownLight.SUN, SHAFT_A))
		# The patch: the window's panes, its lattice's bars left dark between them.
		var patch: Rect2 = s.patch
		var x := patch.position.x
		while x < patch.end.x:
			var w := minf(3.0, patch.end.x - x)
			ci.draw_rect(Rect2(x, patch.position.y, w, 4), Color(TopdownLight.SUN, PATCH_A))
			ci.draw_rect(Rect2(x, patch.position.y + 5, w, patch.size.y - 5), Color(TopdownLight.SUN, PATCH_A))
			x += 4.0
	for m in motes:
		var tw := 0.5 + 0.5 * sin(float(m.t) * 2.3 + (m.at as Vector2).x)
		var k := clampf(float(m.t) / 0.8, 0.0, 1.0) * clampf((float(m.life) - float(m.t)) / 1.0, 0.0, 1.0)
		ci.draw_rect(Rect2((m.at as Vector2).round(), Vector2.ONE), Color(TopdownLight.SUN, 0.55 * tw * k))

# ------------------------------------------------------------------ the tools people hold
## A body's height over its feet in its frame (art px), from the figure's own bounds, so the tools sit where its hands
## and shoulders are at any size.
static func _height(figure: TopdownFigure, action: String, row: String, f: int) -> float:
	var b := figure.bounds(action, row, f)
	return maxf(20.0, -b.position.y) if b.size.y > 0.0 else 36.0

## Draw a held tool round a body (feet at the origin): `back` is the pass before the body. A broom sweeps across the
## ground before them; a shoulder pole runs along the way they walk, its baskets either side (seen end on, one peeks
## over the shoulder and one hangs before the knees); a laundry basket rides the hip; a rod reaches out over the water
## with its line and float.
static func draw_tool(ci: CanvasItem, tool: String, row: String, figure: TopdownFigure, action: String, f: int, t: float, working: String, back: bool) -> void:
	var hgt := _height(figure, action, row, f)
	# The hands' reach out from the body grows with the figure (36 px to the head's top at the 38 px size).
	var wk := hgt / 36.0
	var away := row in ["n", "ne", "nw"]
	var west := row in ["w", "sw", "nw"]
	var side := (-1.0 if west else 1.0) * wk
	var bob := 1.0 if f % 2 == 1 and action in ["walk", "run"] else 0.0
	match tool:
		"broom":
			if back != away: return
			var swish: int = [0, 1, 2, 1][int(t * 5.0) % 4] if working == "sweep" or action == "walk" else 1
			var hands := Vector2(side * (3.0 if row in ["s", "n"] else 5.0), -hgt * 0.42)
			blit(ci, "broom", swish, hands + Vector2(0, 0), not west and row not in ["s", "n"])
		"pole":
			if row in ["e", "w", "se", "sw", "ne", "nw"]:
				if not back: blit(ci, "pole_side", 0, Vector2(0, -hgt * 0.62 + bob), false)
			else:
				if back: blit(ci, "pole_back", 0, Vector2(signf(side), -hgt * 0.8 + bob), false)
				else: blit(ci, "pole_front", 0, Vector2(signf(side), -hgt * 0.4 + bob), false)
		"basket":
			if back != away: return
			blit(ci, "laundry_basket", 0, Vector2(side * 7.0, -hgt * 0.30 + bob), false)
		"rod":
			if back != away: return
			var hands := Vector2(side * 4.0, -hgt * 0.45)
			var reach: Vector2 = {"s": Vector2(4, 6), "se": Vector2(12, 0), "e": Vector2(16, -8), "ne": Vector2(10, -16), "n": Vector2(2, -18),
				"nw": Vector2(-10, -16), "w": Vector2(-16, -8), "sw": Vector2(-12, 0)}.get(row, Vector2(4, 6))
			var tip := hands + reach * wk
			var float_at: Vector2 = {"s": Vector2(6, 16), "se": Vector2(20, 12), "e": Vector2(26, 2), "ne": Vector2(16, -10), "n": Vector2(2, -14),
				"nw": Vector2(-16, -10), "w": Vector2(-26, 2), "sw": Vector2(-20, 12)}.get(row, Vector2(6, 16))
			float_at *= wk
			float_at.y += 1.0 if int(t * 1.6) % 3 == 0 and working == "fish" else 0.0
			_line(ci, hands, tip, Color("8b5b34"))
			_line(ci, tip, float_at, Color(0.9, 0.93, 0.9, 0.55))
			ci.draw_rect(Rect2(float_at.round() - Vector2(0, 1), Vector2(1, 2)), Color("d95b49"))

## A tool set down beside a body: the pole's two baskets either side, or the laundry basket at its feet.
static func draw_tool_down(ci: CanvasItem, tool: String, row: String) -> void:
	match tool:
		"pole":
			blit(ci, "pole_front", 0, Vector2(-10, 1), false)
			blit(ci, "pole_back", 0, Vector2(10, 1), false)
		"basket":
			blit(ci, "laundry_basket", 0, Vector2(9, 1), false)

## A pixel line (whole art px, no smoothing).
static func _line(ci: CanvasItem, a: Vector2, b: Vector2, col: Color) -> void:
	var n := int(maxf(absf(b.x - a.x), absf(b.y - a.y)))
	for i in n + 1:
		var p := a.lerp(b, float(i) / maxf(1.0, n)).round()
		ci.draw_rect(Rect2(p, Vector2.ONE), col)

# ------------------------------------------------------------------ the nodes
## A critter: a plain record (no node of its own, no physics), typed for speed.
class Critter extends RefCounted:
	var kind := ""
	var state := "idle"
	var g := Vector2.ZERO           ## on the ground plane (world units)
	var floor := 0.0                ## the floor it is on (world units; the water's for a fish)
	var z := 0.0                    ## its height over that floor (art px)
	var v := Vector2.ZERO
	var t := 0.0                    ## its own clock
	var st := 0.0                   ## seconds in this state
	var face := 1
	var alpha := 1.0
	var node = null                 ## the sorted node it borrows while on the ground
	var variant := ""
	var s := Vector2.ZERO           ## its feet on the screen (art px)
	var anchor := Vector2.ZERO      ## where it keeps to (flowers, water)
	var target := Vector2.ZERO      ## where it goes (a landing, a dart)
	var home := Vector2.ZERO        ## an animal's home (world units)
	var hs := Vector2.ZERO          ## and on the screen
	var home_id := -1               ## an animal's index in the room's list; -1 for a wild one
	var lead := false               ## a flock's first
	var hop_t := 0.0
	var water := Vector2.ZERO       ## the way to the water, for a frog
	var moving := false
	var skip := 0.0                 ## the time since its last step (a calm one steps one frame in CALM_EVERY)

static var _frames := {}
## How many frames a sprite of the sheet has (looked up once).
static func frames_of(sprite: String) -> int:
	if not _frames.has(sprite): _frames[sprite] = maxi(1, int(art().get("sprites", {}).get(sprite, {}).get("frames", 1)))
	return int(_frames[sprite])

class Layer extends Node2D:
	var life
	var which := ""
	func _init(l, w: String) -> void:
		life = l
		which = w
		name = "Life_" + w
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func _draw() -> void:
		life.draw_layer(self, which)

## A critter on the ground, sorted with the room like a body (a house or a tree hides it; it never hides the player).
class CritterNode extends TopdownWorld.Sorted:
	var critter = null
	var feet := Vector2.ZERO
	var sprite := ""
	var frame := 0
	var _drawn := 0
	var _g := Vector2.INF
	## Where it stands, its sort key, and its pose: redrawn only when one of them has changed.
	func sync(r: TopdownRoom) -> void:
		var cr: TopdownLife.Critter = critter
		feet = cr.s.round()
		var k := position.y
		if cr.g != _g:
			_g = cr.g
			# On the ground floor the key is its row (TopdownRoom.sort_key's own rule there), with no floor to ask.
			k = floorf(cr.g.y / TopdownRoom.ART * 16.0) / 16.0 if cr.floor == 0.0 else r.sort_key(cr.g, cr.floor)
		# Placed (its x, its key as y) only when that has changed: a node's move is a transform sent on.
		var at := Vector2(feet.x, k)
		if at != position: position = at
		_pose(cr)
		var sig := _sprite_id + frame * 7919 + int(feet.x) * 131 + int(feet.y) * 65537 + int(cr.z) * 3 + cr.face * 17 + int(cr.alpha * 8.0) * 1009
		if sig != _drawn:
			_drawn = sig
			queue_redraw()
	var _for: TopdownLife.Critter = null
	var _act := -1
	var _frames := 1
	var _sprite_id := 0
	## Its pose: a sprite of POSES by the critter's state, the name and its frame count looked up only when it changes.
	func _pose(cr: TopdownLife.Critter) -> void:
		var t := cr.t
		var act := 0
		var fps := 1.0
		match cr.kind:
			"sparrow":
				act = 1 if cr.hop_t > 0.0 else (2 if int(t * 1.3) % 3 == 0 else 0)
				fps = 4.0
			"frog":
				act = 1 if cr.state == "leap" else 0
			"hen":
				act = 3 if cr.state == "flee" else (2 if cr.state == "peck" else (1 if cr.moving else 0))
				fps = 8.0 if act == 3 else 3.0
				if cr.variant == "hen_brown": act += 4
			"cat":
				act = 1 if cr.state == "sleep" else (2 if cr.state == "walk" or cr.state == "home" else 0)
				fps = 6.0 if act == 2 else 1.2
			"dog":
				act = 2 if cr.state == "trot" or cr.state == "home" else (1 if cr.state == "sit" else 0)
				fps = 7.0 if act == 2 else (4.0 if act == 1 else 0.8)
		if cr != _for or act != _act:
			_for = cr
			_act = act
			sprite = TopdownLife.POSES[cr.kind][act]
			_frames = maxi(1, TopdownLife.frames_of(sprite))
			_sprite_id = sprite.hash()
		if cr.kind == "frog":
			frame = ((0 if cr.st < 0.25 else 1) if act == 1 else (1 if fmod(t, 3.0) > 2.4 else 0)) % _frames
		else:
			frame = posmod(int(t * fps), _frames)
	func _draw() -> void:
		if critter == null: return
		var t0 := Time.get_ticks_usec()
		var cr: TopdownLife.Critter = critter
		# A small contact shadow under the ones that sit on the ground, then the critter.
		var rx: float = TopdownLife.BLOB_RX.get(cr.kind, 3.0)
		TopdownWorld.draw_blob(self, 0.0, feet.y - position.y, rx, 0.35 * cr.alpha)
		TopdownLife.blit(self, sprite, frame, Vector2(0, feet.y - position.y - cr.z), cr.face < 0, Color(1, 1, 1, cr.alpha))
		TopdownLife.spent_us += Time.get_ticks_usec() - t0
		TopdownLife.spent_parts.draw += Time.get_ticks_usec() - t0

## What hangs on an interior's back wall: sorted just after the wall's row, so the people in front cover it.
class Hangings extends TopdownWorld.Sorted:
	var life
	func _init(w, l) -> void:
		super(w)
		life = l
		key(T + 1.0 / 64.0)
	func _draw() -> void:
		for h in life.hangings:
			TopdownLife.blit(self, str(h[0]), 0, (h[1] as Vector2) - position)
