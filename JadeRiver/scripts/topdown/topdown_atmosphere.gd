class_name TopdownAtmosphere
extends Node2D
## Decision 40, runtime light: the air of a room on the grid, over its tiles and its baked cast shadows
## (TopdownShadows). Every colour and count is TopdownLight's. Inside the world's 640x360 viewport, one art px to a
## pixel, so all of it stays on the pixel grid; the HUD and the overlay's labels are outside it and never graded.
##   - the colour grade: the area's (its backdrop) and the hour's, one full-view pass over the viewport (a CanvasLayer
##     over the world, reading the screen);
##   - the night: the world multiplied by the hour's ambient light, lifted to warm by the room's lights (lanterns, fires,
##     embers, open doorways) in stepped pools, baked once per room the first time the lights burn; the flames glow over
##     it. A night room is always night; outdoors the game's clock turns morning, day, evening and night;
##   - cloud shadows: a few big, faint, dithered shapes gliding over everything by day;
##   - particles, few and capped (TopdownLight.MAX_PARTICLES): motes in sunlight, fireflies at night, leaves and petals
##     falling from trees, mist wisps over water and marsh, glints on sunlit water; tied to the area, hour and weather.
## Settings' "world_extras" off (weak phones) keeps the cast shadows and a night room's night, and drops the grade, the
## clock's hours, clouds and particles; Reduce motion halves the particles.

const VIEW := Vector2(640, 360)
const T := 16.0

var world                            ## the TopdownWorld
var room: TopdownRoom
var def: Dictionary = {}             ## the room's definition (its backdrop, night, weather)
var now: Dictionary = {}             ## TopdownLight.look for this room at this hour
var extras := true
var weather := "clear"
var rng := RandomNumberGenerator.new()
var particles: Array = []            ## {kind, p, v, t, life, ...}
var lights: Array = []               ## [kind, screen point (art px)]: the room's lights
var water_cells := PackedVector2Array()   ## each water cell's surface on screen (its top-left)
var grass_cells := PackedVector2Array()   ## each grass floor's top on screen
var mist_cells := PackedVector2Array()    ## where mist lies: the water and the marsh's wet meadow (paint `m`)
var trees: Array = []                ## [fall colour, crown Rect2 on screen, ground y]
var pools_baked := 0                 ## times this view baked a room's light pools (once per room, when first lit)
var _pools: ImageTexture
var _pools_room := ""
var _look_t := 0.0
var _spawn_t: Dictionary = {}
var _fresh := false                  ## a room just entered: its air fills in at the first frame, once the camera is on it
var _busy := false                   ## particles were drawn last frame
var _cam := Vector2.INF
var t := 0.0
# The layers.
var grade_layer: CanvasLayer
var grade: ColorRect
var night: Night
var glow: Layer
var air: Layer
var low: Layer
var clouds: Clouds

static var _grade_shader: Shader
static var _night_shader: Shader
static var _pool_stamps: Dictionary = {}
static var _cloud_shader: Shader
static var _blank: ImageTexture
static var _white: ImageTexture

func _init(w) -> void:
	world = w
	name = "Atmosphere"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

## Built into the world's viewport: the mist and glints under everything sorted, the clouds, motes and leaves over it,
## the night over those and the glows over the night, the grade last of all.
func _ready() -> void:
	var vp: SubViewport = world.viewport
	low = Layer.new(self, "low")
	vp.add_child(low)
	vp.move_child(low, world.sorted.get_index())
	clouds = Clouds.new()
	clouds.z_index = 60
	clouds.material = ShaderMaterial.new()
	clouds.material.shader = cloud_shader()
	add_child(clouds)
	air = Layer.new(self, "air")
	air.z_index = 70
	add_child(air)
	night = Night.new()
	night.z_index = 80
	night.material = ShaderMaterial.new()
	night.material.shader = night_shader()
	add_child(night)
	glow = Layer.new(self, "glow")
	glow.z_index = 95
	var add := CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	glow.material = add
	add_child(glow)
	grade_layer = CanvasLayer.new()
	grade_layer.layer = 1
	vp.add_child(grade_layer)
	grade = ColorRect.new()
	grade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	grade.material = ShaderMaterial.new()
	grade.material.shader = grade_shader()
	grade_layer.add_child(grade)
	if not GameEvents.event.is_connected(_on_event): GameEvents.event.connect(_on_event)

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

func _on_event(ev: String, p: Dictionary) -> void:
	if ev == "settings_changed" and str(p.get("key", "")) in ["world_extras", "reduce_motion"] and room != null: refresh()

## Settings' switch for the extras (on unless the player turned it off).
static func extras_on() -> bool:
	return Game == null or Game.account == null or bool(Game.account.settings.get("world_extras", true))

# ------------------------------------------------------------------ a room
## A room entered (or rebuilt): its definition, what in it gives light and where the air can show, the look of its
## hour, and the particles already drifting as it appears.
func enter_room() -> void:
	room = world.room
	def = Game.room_rt.def if world.live and Game.room_rt != null and Game.room_rt.topdown == room else room.def
	rng.seed = hash(room.id)
	particles.clear()
	_spawn_t.clear()
	_collect()
	clouds.setup(room, rng)
	world.tint.color = Color.WHITE   # the night is this node's night layer, not the old tint
	refresh()
	_fresh = true

## Re-read the hour, the weather and the Settings; the layers follow.
func refresh() -> void:
	extras = extras_on()
	weather = "clear"
	if str(def.get("weather", "")) != "" and Game.get("calendar") != null and Game.room_rt != null and Game.room_rt.def == def:
		weather = str(Game.calendar.weather_here())
	# The extras off: the clock's hours stay at midday outdoors (a night room keeps its night, an interior its lamps).
	now = TopdownLight.look(def, -1.0 if extras else 0.375, weather if extras else "clear")
	# The night layer: the hour's ambient and the lights' pools (baked the first time they burn in this room).
	var amb: Color = now.ambient
	var lit := float(now.lights)
	var dark := not amb.is_equal_approx(Color.WHITE) or lit > 0.0
	night.visible = dark
	if dark:
		if lit > 0.0 and _pools_room != room.id: _bake_pools()
		night.set_map(_pools if _pools_room == room.id else null, room)
		night.material.set_shader_parameter("ambient", Vector3(amb.r, amb.g, amb.b))
		night.material.set_shader_parameter("strength", lit if _pools_room == room.id else 0.0)
		var cc := TopdownLight.CARRY
		night.material.set_shader_parameter("carry", Vector4(cc.r, cc.g, cc.b, float(now.carry)))
		night.material.set_shader_parameter("carry_r", TopdownLight.CARRY_RADIUS)
	# The sun's cast shadows are as strong as the hour makes them (faint under the moon).
	TopdownShadows.set_strength(float(now.shadows))
	# The grade.
	var g: Dictionary = now.grade
	grade_layer.visible = extras and not TopdownLight.plain_grade(g)
	if grade_layer.visible:
		var m: ShaderMaterial = grade.material
		var hi: Color = g.hi
		var lo := TopdownLight.SHADOW
		m.set_shader_parameter("hi", Vector3(hi.r, hi.g, hi.b))
		m.set_shader_parameter("lo", Vector3(lo.r, lo.g, lo.b))
		m.set_shader_parameter("sun", float(g.sun))
		m.set_shader_parameter("shade", float(g.shade))
		m.set_shader_parameter("sat", float(g.sat))
	clouds.visible = extras and float(now.clouds) > 0.0
	var tone := TopdownLight.TONE_SHADE
	clouds.material.set_shader_parameter("tone", Vector3(tone.r, tone.g, tone.b))
	clouds.material.set_shader_parameter("alpha", TopdownLight.CLOUD_ALPHA * float(now.clouds))
	if not extras: particles.clear()

## Where the room's lights, water, grass and trees are, in art px on the viewport.
func _collect() -> void:
	lights.clear()
	trees.clear()
	water_cells = PackedVector2Array()
	grass_cells = PackedVector2Array()
	mist_cells = PackedVector2Array()
	var paint: Dictionary = room.tileset.get("paint", {})
	var grass := {}   # the paint marks that are grass, by their code
	for mark in paint:
		if bool(paint[mark].get("grass", false)): grass[str(mark).unicode_at(0)] = true
	var marsh := "m".unicode_at(0)
	for y in room.h:
		for x in room.w:
			var i := y * room.w + x
			var l := room.levels[i]
			if l == TopdownRoom.WATER:
				if room.solid[i] == 0:
					water_cells.append(Vector2(x * T, y * T + 8.0))
					mist_cells.append(Vector2(x * T, y * T + 8.0))
			elif room.solid[i] == 0 and room.stair_of[i] == 0 and grass.has(room.paint[i]):
				grass_cells.append(Vector2(x * T, (y - l) * T))
				if room.paint[i] == marsh: mist_cells.append(Vector2(x * T, (y - l) * T))
	for p in room.props:
		var art: Dictionary = p.art
		var rr: Array = art.get("rect", [0, 0, 16, 16])
		var origin: Array = art.get("origin", [0, 16])
		var c: Vector2i = p.cell
		var south := float(c.y + (p.size as Vector2i).y) * T
		var ground := 8.0 if int(p.level) < 0 else -float(p.level) * T
		var at := Vector2(c.x * T - float(origin[0]), south + ground - float(origin[1]))
		var kind := str(p.kind)
		if TopdownLight.PROP_LIGHTS.has(kind):
			var pl: Array = TopdownLight.PROP_LIGHTS[kind]
			lights.append([str(pl[0]), at + Vector2(float(pl[1]), float(pl[2]))])
		if (p.door as Array).size() == 2:
			var door: Array = p.door
			lights.append([TopdownLight.DOOR_LIGHT, Vector2((c.x + (float(door[0]) + float(door[1]) + 1.0) * 0.5) * T, south + ground + 2.0)])
		if TopdownLight.FALLS.has(kind):
			trees.append([TopdownLight.FALLS[kind], Rect2(at + Vector2(2, 2), Vector2(float(rr[2]) - 4.0, float(rr[3]) * 0.5)), south + ground])
	for o in def.get("objects", []) if world.live else []:
		var key := str(o.get("type", ""))
		if not TopdownLight.OBJECT_LIGHTS.has(key): key = str(o.get("prop", ""))
		if not TopdownLight.OBJECT_LIGHTS.has(key) or not o.has("at"): continue
		var ol: Array = TopdownLight.OBJECT_LIGHTS[key]
		var at2 := TopdownWorld.to_screen(Vector2(float(o.at[0]), float(o.at[1])), float(o.get("alt", 0.0))).round()
		lights.append([str(ol[0]), at2 - Vector2(0, float(ol[1]))])

# ------------------------------------------------------------------ light pools
## The room's pools of light, once: each light's stepped disc laid over the others (its colour, its strength in alpha).
func _bake_pools() -> void:
	_pools_room = room.id
	pools_baked += 1
	var img := Image.create(maxi(1, room.w * int(T)), maxi(1, room.h * int(T)), false, Image.FORMAT_RGBA8)
	for l in lights:
		var st := pool_stamp(str(l[0]))
		var at: Vector2 = l[1]
		img.blend_rect(st, Rect2i(Vector2i.ZERO, st.get_size()), Vector2i(at.round()) - st.get_size() / 2)
	_pools = ImageTexture.create_from_image(img)

## A light's pool: stepped bands of its strength (alpha) in its colour, a 1 px checker where one band meets the next.
static func pool_stamp(kind: String) -> Image:
	if _pool_stamps.has(kind): return _pool_stamps[kind]
	var lk: Dictionary = TopdownLight.LIGHT_KINDS.get(kind, TopdownLight.LIGHT_KINDS.lantern)
	var r := int(lk.radius)
	var bands: Array = lk.bands
	var col: Color = lk.color
	var img := Image.create(r * 2 + 1, r * 2 + 1, false, Image.FORMAT_RGBA8)
	# Row by row, the outermost band first and each inner one over it: the pixels just past a band's edge (within 1 px)
	# on the checker, then the band's own span.
	for y in r * 2 + 1:
		var dy2 := float((y - r) * (y - r))
		for i in range(bands.size() - 1, -1, -1):
			var edge := float(bands[i][0]) * r
			var c := Color(col.r, col.g, col.b, float(bands[i][1]))
			var ring := edge + 1.0
			if ring * ring >= dy2:
				var inner := floori(sqrt(edge * edge - dy2)) if edge * edge >= dy2 else -1
				for dx in range(inner + 1, floori(sqrt(ring * ring - dy2)) + 1):
					for x in [r - dx, r + dx]:
						if (x + y) % 2 == 0: img.set_pixel(x, y, c)
			if edge * edge >= dy2:
				var half := floori(sqrt(edge * edge - dy2))
				img.fill_rect(Rect2i(r - half, y, half * 2 + 1, 1), c)
	_pool_stamps[kind] = img
	return img

# ------------------------------------------------------------------ particles
func particle_count() -> int:
	return particles.size()

## How many of each kind this room wants at this hour: its cap x the hour's and area's share; Reduce motion halves it.
func wanted(kind: String) -> int:
	if not extras: return 0
	var cap := float(TopdownLight.PARTICLES[kind].cap)
	if UiKit.reduce_motion(): cap *= 0.5
	var share := 0.0
	match kind:
		"mote": share = float(now.motes)
		"firefly": share = float(now.fireflies) * (1.0 if not grass_cells.is_empty() else 0.0)
		"leaf": share = 1.0 if not trees.is_empty() else 0.0
		"mist": share = float(now.mist) / 1.6 if not mist_cells.is_empty() else 0.0
		"glint": share = float(now.glints) if not water_cells.is_empty() else 0.0
	return int(round(cap * clampf(share, 0.0, 1.0)))

func _view() -> Rect2:
	var c: Vector2 = world.camera.position if world.camera != null else VIEW * 0.5
	return Rect2(c - VIEW * 0.5, VIEW)

## The room appears with its air already moving: each kind's share spawned at a random age.
func _prewarm() -> void:
	var view := _view()
	# One cloud's shadow starts over the view, gliding in (the rest wander the room).
	if not clouds.at.is_empty(): clouds.at[0] = view.position + Vector2(rng.randf_range(-0.3, 0.5), rng.randf_range(-0.2, 0.5)) * view.size
	for kind in TopdownLight.PARTICLES:
		for i in wanted(kind):
			var p := _spawn(kind, view)
			if p.is_empty(): break
			p.t = rng.randf() * float(p.life) * 0.8
			if kind == "leaf": p.p += p.v * float(p.t) * 0.5

func _process(delta: float) -> void:
	if room == null: return
	t += delta
	_look_t -= delta
	if _look_t <= 0.0:
		_look_t = 1.0
		refresh()
	var view := _view()
	# The air fills in where the camera is: on a new room, and when the camera jumps (a way taken, a spot placed).
	if _fresh or _cam.distance_to(view.get_center()) > 160.0:
		_fresh = false
		particles.clear()
		_prewarm()
	_cam = view.get_center()
	if night.visible and float(now.get("carry", 0.0)) > 0.0 and world.player != null:
		night.material.set_shader_parameter("carry_at", (world.player.screen as Vector2) + Vector2(0, -10))
	if extras:
		var counts := {}
		for p in particles: counts[p.kind] = int(counts.get(p.kind, 0)) + 1
		for kind in TopdownLight.PARTICLES:
			_spawn_t[kind] = float(_spawn_t.get(kind, 0.0)) - delta
			if float(_spawn_t[kind]) > 0.0: continue
			var n := wanted(kind)
			if n <= 0 or int(counts.get(kind, 0)) >= n: continue
			_spawn(kind, view)
			var life: Array = TopdownLight.PARTICLES[kind].life
			_spawn_t[kind] = (float(life[0]) + float(life[1])) * 0.5 / float(n)
		_step(delta, view)
		clouds.drift(delta)
	# The layers redraw only while they have something on them (and once more to clear it).
	var busy := not particles.is_empty()
	if busy or _busy:
		low.queue_redraw()
		air.queue_redraw()
	if busy or _busy or (night.visible and float(now.get("lights", 0.0)) > 0.0):
		glow.queue_redraw()
	_busy = busy

func _count(kind: String) -> int:
	var n := 0
	for p in particles: if p.kind == kind: n += 1
	return n

## One new particle of `kind` inside the view (or none when the cap is reached or no place for it shows).
func _spawn(kind: String, view: Rect2) -> Dictionary:
	if particles.size() >= TopdownLight.MAX_PARTICLES: return {}
	var spec: Dictionary = TopdownLight.PARTICLES[kind]
	var life: Array = spec.life
	var p := {"kind": kind, "t": 0.0, "life": rng.randf_range(float(life[0]), float(life[1])), "v": Vector2.ZERO, "phase": rng.randf() * TAU,
		"color": spec.get("color", Color.WHITE)}
	match kind:
		"mote":
			p.p = view.position + Vector2(rng.randf() * view.size.x, rng.randf() * view.size.y)
			p.v = Vector2(rng.randf_range(2.0, 6.0), rng.randf_range(-1.5, 1.0))
		"firefly":
			var c := _pick(grass_cells, view)
			if c.x == INF: return {}
			p.p = c + Vector2(rng.randf() * T, rng.randf() * T - rng.randf_range(4.0, 14.0))
			p.v = Vector2.from_angle(rng.randf() * TAU) * 5.0
		"leaf":
			var near := trees.filter(func(q): return (q[1] as Rect2).intersects(view.grow(24.0)))
			if near.is_empty(): return {}
			var tr: Array = near[rng.randi() % near.size()]
			var crown: Rect2 = tr[1]
			p.p = crown.position + Vector2(rng.randf() * crown.size.x, rng.randf() * crown.size.y)
			p.ground = float(tr[2]) + rng.randf_range(-6.0, 6.0)
			p.color = tr[0]
			p.v = Vector2(rng.randf_range(2.0, 5.0), rng.randf_range(9.0, 14.0))
		"mist":
			var c := _pick(mist_cells, view)
			if c.x == INF: return {}
			p.p = c + Vector2(rng.randf() * T - 8.0, rng.randf() * 12.0)
			p.len = rng.randi_range(10, 22)
			p.twin = rng.randf() < 0.5
			p.v = Vector2(rng.randf_range(2.0, 5.0), 0.0)
		"glint":
			var c := _pick(water_cells, view)
			if c.x == INF: return {}
			p.p = c + Vector2(rng.randi_range(2, 13), rng.randi_range(2, 11))
	particles.append(p)
	return p

## A random cell of `list` inside the view (a few tries); INF when none shows.
func _pick(list: PackedVector2Array, view: Rect2) -> Vector2:
	if list.is_empty(): return Vector2.INF
	for i in 12:
		var c := list[rng.randi() % list.size()]
		if view.grow(-4.0).has_point(c + Vector2(8, 8)): return c
	return Vector2.INF

func _step(delta: float, view: Rect2) -> void:
	for i in range(particles.size() - 1, -1, -1):
		var p: Dictionary = particles[i]
		p.t = float(p.t) + delta
		match str(p.kind):
			"mote": p.p += (p.v as Vector2) * delta + Vector2(0.0, sin(t * 1.3 + float(p.phase)) * 3.0 * delta)
			"firefly":
				p.v = (p.v as Vector2).rotated(sin(t * 0.9 + float(p.phase)) * 1.6 * delta)
				p.p += (p.v as Vector2) * delta
			"leaf":
				if (p.p as Vector2).y < float(p.ground):
					p.p += Vector2((p.v as Vector2).x + sin(t * 2.4 + float(p.phase)) * 10.0, (p.v as Vector2).y) * delta
				elif not p.has("landed"):
					p.landed = true
					p.t = maxf(float(p.t), float(p.life) - 1.2)   # lies on the ground a moment, then fades
			"mist": p.p += (p.v as Vector2) * delta
		if float(p.t) >= float(p.life) or not view.grow(48.0).has_point(p.p): particles.remove_at(i)

## A particle's strength through its life: in over its first fifth, out over its last third.
static func envelope(p: Dictionary) -> float:
	var k := float(p.t) / maxf(0.001, float(p.life))
	return clampf(k * 5.0, 0.0, 1.0) * clampf((1.0 - k) * 3.0, 0.0, 1.0)

## The layers draw their share: `low` the mist and glints (on the water, under everything standing), `air` the motes and
## leaves, `glow` the fireflies and the flames of the lights (added over the night).
func draw_layer(ci: CanvasItem, which: String) -> void:
	for p in particles:
		var k := envelope(p)
		if k <= 0.0: continue
		var spec: Dictionary = TopdownLight.PARTICLES[p.kind]
		var col: Color = p.color
		var a := float(spec.alpha) * k
		var at := (p.p as Vector2).floor()
		match [which, str(p.kind)]:
			["low", "mist"]:
				var n := int(p.len)
				ci.draw_rect(Rect2(at, Vector2(2, 1)), Color(col, a * 0.5))
				ci.draw_rect(Rect2(at + Vector2(2, 0), Vector2(n - 4, 1)), Color(col, a))
				ci.draw_rect(Rect2(at + Vector2(n - 2, 0), Vector2(2, 1)), Color(col, a * 0.5))
				if p.twin: ci.draw_rect(Rect2(at + Vector2(4, -2), Vector2(maxi(2, n / 2), 1)), Color(col, a * 0.55))
			["low", "glint"]:
				ci.draw_rect(Rect2(at, Vector2.ONE), Color(col, a))
				if k > 0.6:
					for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]: ci.draw_rect(Rect2(at + d, Vector2.ONE), Color(col, a * 0.45))
			["air", "mote"]:
				var tw := 0.6 + 0.4 * sin(t * 3.0 + float(p.phase))
				ci.draw_rect(Rect2(at, Vector2.ONE), Color(col, a * tw))
				if tw > 0.85:
					for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]: ci.draw_rect(Rect2(at + d, Vector2.ONE), Color(col, a * 0.25))
			["air", "leaf"]:
				var flat: bool = int(float(p.t) * 3.0 + float(p.phase)) % 2 == 0 or p.has("landed")
				ci.draw_rect(Rect2(at, Vector2(2, 1) if flat else Vector2(1, 2)), Color(col, a))
			["glow", "firefly"]:
				var blink := clampf(sin(t * 2.2 + float(p.phase)) * 1.6 + 0.4, 0.0, 1.0)
				if blink <= 0.0: continue
				ci.draw_rect(Rect2(at, Vector2.ONE), Color(col, a * blink))
				for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]: ci.draw_rect(Rect2(at + d, Vector2.ONE), Color(col, a * blink * 0.3))
	if which == "glow" and night.visible and float(now.get("lights", 0.0)) > 0.0:
		var lit := float(now.lights)
		for l in lights:
			var lk: Dictionary = TopdownLight.LIGHT_KINDS.get(str(l[0]), {})
			if not lk.has("flame"): continue
			var at: Vector2 = (l[1] as Vector2).round()
			var flick := 0.8 + 0.2 * sin(t * 7.0 + at.x * 0.37) * sin(t * 3.1 + at.y * 0.21)
			var fc: Color = lk.flame
			ci.draw_rect(Rect2(at - Vector2(1, 1), Vector2(2, 2)), Color(fc, 0.55 * lit * flick))
			ci.draw_rect(Rect2(at - Vector2(2, 0), Vector2(4, 1)), Color(fc, 0.22 * lit * flick))
			ci.draw_rect(Rect2(at - Vector2(0, 2), Vector2(1, 4)), Color(fc, 0.22 * lit * flick))

# ------------------------------------------------------------------ shaders
## The grade (§14.2: the tiles are graded already): saturation round the pixel's grey (at most +5%), the light values
## at most `sun` (4%) toward `hi` (SUN, or MIST in the mist's areas), the dark ones at most `shade` (4%) toward SHADOW.
## Nearest sampling at the viewport's own size, so it only maps colours.
static func grade_shader() -> Shader:
	if _grade_shader == null:
		_grade_shader = Shader.new()
		_grade_shader.code = """shader_type canvas_item;
uniform sampler2D screen : hint_screen_texture, filter_nearest;
uniform vec3 hi = vec3(1.0, 0.914, 0.651);
uniform vec3 lo = vec3(0.141, 0.122, 0.31);
uniform float sun = 0.0;
uniform float shade = 0.0;
uniform float sat = 1.0;
void fragment() {
	vec3 c = textureLod(screen, SCREEN_UV, 0.0).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, sat);
	c = mix(c, hi, sun * smoothstep(0.35, 0.9, l));
	c = mix(c, lo, shade * (1.0 - smoothstep(0.1, 0.55, l)));
	COLOR = vec4(clamp(c, 0.0, 1.0), 1.0);
}
"""
	return _grade_shader

## The night: the world multiplied by the ambient, lifted toward each light's colour by its pool's strength.
static func night_shader() -> Shader:
	if _night_shader == null:
		_night_shader = Shader.new()
		_night_shader.code = """shader_type canvas_item;
render_mode blend_mul;
uniform vec3 ambient = vec3(1.0);
uniform float strength = 1.0;
uniform vec2 carry_at = vec2(-99999.0);
uniform vec4 carry = vec4(1.0, 0.94, 0.82, 0.0);
uniform float carry_r = 44.0;
varying vec2 world;
void vertex() {
	world = VERTEX;
}
void fragment() {
	vec4 l = texture(TEXTURE, UV);
	vec3 c = mix(ambient, l.rgb, clamp(l.a * strength, 0.0, 1.0));
	// The light the player carries: two stepped bands, a 1 px checker past each edge.
	float d = length(world - carry_at);
	float chk = mod(floor(FRAGCOORD.x) + floor(FRAGCOORD.y), 2.0);
	float b = d < carry_r * 0.55 ? 1.0 : (d < carry_r ? 0.4 : 0.0);
	if (d >= carry_r * 0.55 && d < carry_r * 0.55 + 1.0 && chk > 0.5) b = 1.0;
	if (d >= carry_r && d < carry_r + 1.0 && chk > 0.5) b = 0.4;
	c = mix(c, max(c, carry.rgb), b * carry.a);
	COLOR = vec4(c, 1.0);
}
"""
	return _night_shader

static func blank() -> ImageTexture:
	if _blank == null: _blank = ImageTexture.create_from_image(Image.create(1, 1, false, Image.FORMAT_RGBA8))
	return _blank

static func white() -> ImageTexture:
	if _white == null:
		var img := Image.create(1, 1, false, Image.FORMAT_RGBA8)
		img.fill(Color.WHITE)
		_white = ImageTexture.create_from_image(img)
	return _white

## A cloud's shade (Clouds.SIZE px): a few overlapping ellipses, solid inside, their rim dithered thinner and thinner
## on a 4x4 ordered pattern tied to the cloud's own pixels, so the edge is soft on the pixel grid and never shimmers as
## it glides. Drawn by the GPU: nothing to build on the CPU.
static func cloud_shader() -> Shader:
	if _cloud_shader == null:
		_cloud_shader = Shader.new()
		_cloud_shader.code = """shader_type canvas_item;
uniform vec2 size = vec2(208.0, 112.0);
uniform vec3 tone = vec3(0.055, 0.29, 0.345);
uniform float alpha = 0.08;
const vec4 BLOBS[5] = vec4[5](vec4(76.0, 58.0, 62.0, 34.0), vec4(128.0, 48.0, 56.0, 32.0), vec4(104.0, 72.0, 78.0, 28.0),
	vec4(164.0, 66.0, 38.0, 24.0), vec4(42.0, 70.0, 34.0, 22.0));
const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
void fragment() {
	vec2 p = floor(UV * size);
	float v = -1.0;
	for (int i = 0; i < 5; i++) {
		vec2 d = (p - BLOBS[i].xy) / BLOBS[i].zw;
		v = max(v, 1.0 - dot(d, d));
	}
	float fill = clamp(v / 0.45, 0.0, 1.0);
	int bi = int(mod(p.y, 4.0)) * 4 + int(mod(p.x, 4.0));
	float on = (v > 0.0 && (fill >= 1.0 || fill * 16.0 > BAYER[bi])) ? 1.0 : 0.0;
	COLOR = vec4(tone, on * alpha);
}
"""
	return _cloud_shader

# ------------------------------------------------------------------ the layers
class Layer extends Node2D:
	var atmo
	var which := ""
	func _init(a, w: String) -> void:
		atmo = a
		which = w
		name = "Air_" + w
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func _draw() -> void:
		atmo.draw_layer(self, which)

## The night's multiply over the room: the pools' texture over the room, the bare ambient round it.
class Night extends Node2D:
	var map: Texture2D
	var rect := Rect2()
	func _init() -> void:
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func set_map(tex: Texture2D, r: TopdownRoom) -> void:
		map = tex
		rect = Rect2(Vector2.ZERO, r.art_size())
		queue_redraw()
	func _draw() -> void:
		var pad := Vector2(640, 360)
		var outer := Rect2(rect.position - pad, rect.size + pad * 2.0)
		var bare: Texture2D = TopdownAtmosphere.blank()
		draw_texture_rect(map if map != null else bare, rect, false)
		for r in [Rect2(outer.position, Vector2(outer.size.x, pad.y)), Rect2(Vector2(outer.position.x, rect.end.y), Vector2(outer.size.x, pad.y)),
				Rect2(Vector2(outer.position.x, rect.position.y), Vector2(pad.x, rect.size.y)), Rect2(Vector2(rect.end.x, rect.position.y), Vector2(pad.x, rect.size.y))]:
			draw_texture_rect(bare, r, false)

## The cloud shade: a few clouds gliding with the wind, wrapping round the room.
class Clouds extends Node2D:
	const SIZE := Vector2(208, 112)
	var at: Array = []
	var bounds := Rect2()
	func _init() -> void:
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func setup(r: TopdownRoom, rng: RandomNumberGenerator) -> void:
		bounds = Rect2(-SIZE, r.art_size() + SIZE)
		at.clear()
		for i in maxi(1, roundi(r.art_size().x * r.art_size().y / (640.0 * 360.0) * TopdownLight.CLOUDS_PER_SCREEN)):
			at.append(bounds.position + Vector2(rng.randf() * bounds.size.x, rng.randf() * bounds.size.y))
		queue_redraw()
	func drift(delta: float) -> void:
		if not visible: return
		for i in at.size():
			var p: Vector2 = at[i] + TopdownLight.CLOUD_DRIFT * delta
			if p.x > bounds.end.x: p.x = bounds.position.x
			if p.y > bounds.end.y: p.y = bounds.position.y
			at[i] = p
		queue_redraw()
	func _draw() -> void:
		for p in at: draw_texture_rect(TopdownAtmosphere.white(), Rect2((p as Vector2).floor(), SIZE), false)
