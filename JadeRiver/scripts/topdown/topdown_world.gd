class_name TopdownWorld
extends Node2D
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1, §4): the prototype room's view, mounted by main.gd in
## place of world.gd behind `--topdown-proto` or the title screen's hidden entry. The world renders at 640x360 in its
## own SubViewport (one art px = one viewport px, snapped to whole pixels) shown x2 under the 1280x720 HUD. Floors and
## water draw first; raised rows, stairs, props, the body and its shadow sort in one Y-sorted layer by explicit keys
## (TopdownRoom.sort_key: every node's y is its key and it draws back to its screen row); a silhouette shows the body
## through whatever covers it. The camera follows the ground underfoot, not the jump arc, and snaps to whole pixels.
##
## Phase 2: with a character, the room is entered through the World authority (`enter_grid_room`) and the simulation
## runs as in every room: Game.tick after the body's step, the room's foes (PLACEHOLDER sprites, sorted with the rest),
## a blow's hit-stop freezing both. Over the viewport, at the HUD's resolution and following the camera, the overlay
## holds what reads best crisp: the effects layer (FxLayer, the technique forms from art/fx/, numbers), the foes'
## labels and HP bars (EnemyView in label mode, placed by WorldLabels round the HUD), loot, and the aim (decision 30).

const Player := preload("res://scripts/topdown/topdown_player.gd")
const VIEW := Vector2i(640, 360)
const T := 16.0

var room_id := "td_proto_square"
var room: TopdownRoom
var player
var viewport: SubViewport
var container: SubViewportContainer
var camera: Camera2D
var sorted: Node2D
var shadow: Node2D
var fx: Node2D
var silhouette: Node2D
var occluded := false
var cam := Vector2.ZERO
var cam_z := 0.0
var sim_frozen := false
# Read and written by hud.gd as on world.gd.
var context: Dictionary = {}
var label_obstacles: Array = []
var hud_minimap := false        ## the HUD's minimap draws side-view rooms; it stays off in the prototype
# Phase 2: the fight.
var overlay: Node2D             ## screen resolution, world units (1 unit = 1 screen px), following the camera
var effects: FxLayer
var combat_fx: CombatFx
var shake := ShakeRig.new()
var foe_views: Dictionary = {}  ## uid -> FoeView (the figure, in the sorted layer)
var label_views: Dictionary = {} ## uid -> EnemyView in label mode (on the overlay)
var loot_layer: Node2D
var aim_view: Node2D
var _atlases: Dictionary = {}

func _ready() -> void:
	# Phase 2: a character enters the room through the World authority; its RoomRuntime carries the grid.
	if Game.active() != null and Game.submit({"type": "enter_grid_room", "room": room_id}).get("ok", false):
		room = Game.room_rt.topdown
	else:
		room = TopdownRoom.load_room(room_id)
	container = SubViewportContainer.new()
	container.stretch = true
	container.stretch_shrink = 2
	container.size = Vector2(VIEW * 2)
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	container.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(container)
	viewport = SubViewport.new()
	viewport.size = VIEW
	viewport.handle_input_locally = false
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	viewport.snap_2d_transforms_to_pixel = true
	viewport.snap_2d_vertices_to_pixel = true
	container.add_child(viewport)
	var bg := ColorRect.new()
	bg.color = Color("0A2027")
	bg.size = room.art_size() + Vector2(VIEW)
	bg.position = -Vector2(VIEW) * 0.5
	viewport.add_child(bg)
	viewport.add_child(WaterView.new(self))
	viewport.add_child(FloorView.new(self))
	sorted = Node2D.new()
	sorted.name = "Sorted"
	sorted.y_sort_enabled = true
	viewport.add_child(sorted)
	for y in room.h:
		var strip := StripView.new(self, y)
		if not strip.rects.is_empty(): sorted.add_child(strip)
	for st in room.stairs: sorted.add_child(StairsView.new(self, st))
	for p in room.props: sorted.add_child(PropView.new(self, p))
	shadow = ShadowView.new(self)
	sorted.add_child(shadow)
	player = Player.new()
	player.world = self
	player.motor = TopdownMotor.new(room)
	player.actor_id = Game.active_id if Game.active() != null else ""
	sorted.add_child(player)
	fx = FxView.new(self)
	sorted.add_child(fx)
	silhouette = Silhouette.new(self)
	viewport.add_child(silhouette)
	camera = Camera2D.new()
	viewport.add_child(camera)
	camera.make_current()
	overlay = Node2D.new()
	overlay.name = "Overlay"
	add_child(overlay)
	loot_layer = Node2D.new()
	overlay.add_child(loot_layer)
	aim_view = AimView.new(self)
	overlay.add_child(aim_view)
	effects = FxLayer.new()
	overlay.add_child(effects)
	effects.chest = float(ContentDB.movement("topdown.combat.chest", 40))
	combat_fx = CombatFx.new(effects, self)
	var caption := CanvasLayer.new()
	caption.layer = 4
	add_child(caption)
	caption.add_child(Caption.new(self))
	if player.bound():
		Game.bind_movement(player.actor_id, player.state)
		GameEvents.event.connect(_on_event)
		_loadout(Game.active())
		for uid in Game.room_rt.enemies: _add_foe(Game.room_rt.enemies[uid])
	cam_z = player.motor.z
	_sync(0.0)
	cam = _cam_target()
	camera.position = cam.round()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

func _physics_process(delta: float) -> void:
	if sim_frozen or Game.paused: return
	if player.bound() and Game.combat.hold_for_hitstop(delta): return   # a blow's hit-stop holds the fight still
	for e in player.physics_step(delta): _feedback(e)
	if player.bound(): Game.tick(delta)

func _process(delta: float) -> void:
	_sync(delta)
	var m: TopdownMotor = player.motor
	if m.grounded and m.sink_t < 0.0: cam_z = m.z
	elif m.z < cam_z and m.sink_t < 0.0: cam_z = m.z   # a fall below the last floor is followed down
	var k := 1.0 - exp(-delta * 3.0 / float(TopdownMotor.conf("camera_settle_s", 0.3)))
	cam = cam.lerp(_cam_target(), k)
	camera.position = cam.round()
	camera.offset = (shake.offset(delta) / TopdownRoom.ART).round()
	overlay.position = (Vector2(VIEW) * 0.5 - camera.position - camera.offset) * TopdownRoom.ART
	if player.bound(): layout_labels()

## The camera's goal in art px: the feet on the ground underfoot (not the jump arc) plus a look-ahead, inside the room.
func _cam_target() -> Vector2:
	var m: TopdownMotor = player.motor
	var t := (Vector2(m.pos.x, m.pos.y - cam_z) + m.vel * float(TopdownMotor.conf("camera_look_ahead", 0.2))) / TopdownRoom.ART + Vector2(0, -12)
	var size := room.art_size()
	var half := Vector2(VIEW) * 0.5
	t.x = size.x * 0.5 if size.x <= VIEW.x else clampf(t.x, half.x, size.x - half.x)
	t.y = size.y * 0.5 if size.y <= VIEW.y else clampf(t.y, half.y, size.y - half.y)
	return t

func _sync(delta: float) -> void:
	player.sync(delta)
	shadow.sync()
	fx.advance(delta)
	for uid in foe_views.keys():
		if is_instance_valid(foe_views[uid]): foe_views[uid].sync(delta)
		else: foe_views.erase(uid)
	occluded = is_occluded()
	silhouette.queue_redraw()
	aim_view.queue_redraw()

## Is the body covered by something sorted after it (a raised row's face, the flight of stairs, a prop)?
func is_occluded() -> bool:
	var feet: Vector2 = player.screen
	var body := Rect2(feet.x - 5, feet.y - 34, 10, 30)
	for n in sorted.get_children():
		if n == player or n == shadow or n == fx or n.position.y <= player.position.y: continue
		for r in n.get("rects"):
			if (r as Rect2).intersects(body): return true
	return false

func _feedback(e: Dictionary) -> void:
	var m: TopdownMotor = player.motor
	match str(e.type):
		"jumped": Audio.play("jump")
		"dashed", "plunged": Audio.play("dodge")
		"landed":
			fx.puff(m.pos, m.z, maxf(float(e.fall), 64.0) if e.get("plunge", false) else float(e.fall))
			if e.get("plunge", false):
				# The Plunge's impact (decision 35): a shock ring the size of its strike, dust and a jolt, as the side view's.
				var feet := player_feet()
				effects.add("ring", feet, {"color": Color(UiKit.PALE_GOLD, 0.8), "radius": float(ContentDB.movement("plunge.radius", 60.0)), "dur": 0.35})
				effects.add("dust", feet, {"color": Color(0.8, 0.74, 0.62, 0.7), "dur": 0.4})
				Audio.play("rumble")
				add_shake(0.2)
			elif float(e.fall) > 12.0: Audio.play("land")
		"splashed":
			fx.splash(m.pos)
			Audio.play("water_step")

# ------------------------------------------------------------------ Phase 2: the fight's views
## A point on the plane at height z in the overlay's units (the effects layer's: world units, y lifted by z).
static func lifted(p: Vector2, z: float) -> Vector2:
	return Vector2(p.x, p.y - z)

## The player's feet in the overlay's units.
func player_feet() -> Vector2:
	return lifted(player.motor.pos, player.motor.z)

## The room's `loadout`: one technique per aim form in the stand-in character's empty slots (a slot the player filled
## keeps its own), so the prototype's technique buttons have something to aim.
func _loadout(c) -> void:
	var list: Array = room.def.get("loadout", [])
	for i in mini(list.size(), c.cultivator.technique_slots.size()):
		if c.cultivator.technique_slots[i] != null: continue
		var tid := str(list[i])
		if not c.cultivator.techniques_known.has(tid): Game.apply_effects(c.id, [{"kind": "learn_technique", "technique": tid}], "topdown_prototype")
		Game.submit({"type": "equip_technique", "slot": i, "id": tid})

func add_shake(s: float, amp := -1.0) -> void:
	shake.add(s, amp)

func _add_foe(e: EnemyState) -> void:
	if foe_views.has(e.uid) and is_instance_valid(foe_views[e.uid]): return
	var v := FoeView.new(self, e)
	sorted.add_child(v)
	foe_views[e.uid] = v
	var lv := EnemyView.new()
	lv.label_only = true
	lv.setup(e)
	overlay.add_child(lv)
	label_views[e.uid] = lv

## The foes' names and HP bars keep clear of each other and of the HUD's controls (WorldLabels, as world.gd places
## them), nearest the player first.
func layout_labels() -> Dictionary:
	var views: Array = []
	var px: float = player.motor.pos.x
	for uid in label_views.keys():
		var v = label_views[uid]
		if not is_instance_valid(v):
			label_views.erase(uid)
			continue
		views.append({"id": "e%d" % int(uid), "view": v, "kind": v.label_kind, "near": absf(v.position.x - px)})
	return WorldLabels.place_views(views, overlay.get_global_transform_with_canvas(), label_obstacles)

func _on_event(name: String, p: Dictionary) -> void:
	match name:
		"enemy_spawned", "ally_spawned":
			var e: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", p.get("uid", 0)))) if Game.room_rt else null
			if e: _add_foe(e)
		"enemy_aggro":
			var foe: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
			if foe and not foe.hidden: effects.label(lifted(foe.plane, foe.altitude) - Vector2(0, foe.height() + 24), "!", UiKit.GOLD, 26)
		"loot_dropped":
			for l in p.get("items", []):
				var lv := LootView.new()
				lv.setup(l)
				loot_layer.add_child(lv)
		"hit_landed": combat_fx.hit(p)
		"hit_missed", "hit_immune", "hit_dodged": combat_fx.word(name, p, player_feet())
		"attack_started":
			if str(p.get("actor", "")) == Game.active_id:
				var aim: Vector2 = p.get("aim", Vector2(int(p.get("facing", 1)), 0))
				var tech := str(p.get("technique", ""))
				if tech != "":
					var at: Vector2 = p.get("at", player.motor.pos)
					var point := lifted(at, room.height_at(at) if room.height_at(at) < INF else player.motor.z)
					# A circle at a point plays where it lands (its form's feet anchor is the point, not the caster).
					var t := ContentDB.entry("techniques", tech)
					var on_point := TopdownAim.form_of(t) == "point"
					combat_fx.cast(tech, point if on_point else player_feet(), int(p.facing), SpriteCache.element_color(str(p.get("element", "none"))),
						float(p.get("windup", -1.0)), point, aim, float(TopdownAim.cfg("point_radius", 48)) if on_point else TopdownAim.reach_of(t))
					Audio.play("technique")
				else:
					# A swing's arc along the aim, so each of the eight directions reads (the placeholder body has one strike pose).
					var f := 1 if aim.x >= 0.0 else -1
					effects.add("slash", player_feet() + aim * 26.0 + Vector2(0, -effects.chest + 8.0), {"color": UiKit.PAPER, "facing": f,
						"turn": (aim * f).angle(), "radius": 22.0, "dur": 0.22, "delay": float(p.get("windup", 0.0)) * 0.6})
					Audio.play("swing")
			elif p.get("enemy", false):
				Audio.play("tell")
		"parried":
			effects.parry(player_feet(), player.facing)
			Audio.play("parry")
		"projectile_ended":
			effects.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": UiKit.PAPER, "dur": 0.15})

## World units on the ground plane at height z to the viewport's art px.
static func to_screen(p: Vector2, z: float) -> Vector2:
	return Vector2(p.x, p.y - z) / TopdownRoom.ART

func tile(name: String) -> Rect2:
	var r: Array = room.tileset.get("tiles", {}).get(name, [0, 0, 16, 16])
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))

## The top tile a paint mark draws, with a fixed per-cell variant.
## (The tile set's `paint` table says which tiles each mark draws, decision 31: new art replaces rows, not code.)
func top_tile(x: int, y: int) -> String:
	var tops: Array = room.tileset.get("paint", {}).get(room.paint_at(x, y), {}).get("top", ["grass_a"])
	return str(tops[1 if tops.size() > 1 and (x * 7 + y * 13) % 5 < 2 else 0])

func face_tile(x: int, y: int, first: bool, over_water: bool) -> String:
	var p: Dictionary = room.tileset.get("paint", {}).get(room.paint_at(x, y), {})
	var kind := str(p.get("face", "stone"))
	if over_water and not p.get("keep_face", false): kind = str(room.tileset.get("bank_face", "bank"))
	return kind + ("_face_top" if first else "_face")

## An atlas of the tile set (tiles, props, body, foes), loaded once from the file its manifest names.
func atlas(kind: String) -> Texture2D:
	if not _atlases.has(kind): _atlases[kind] = load(str(room.tileset.get("atlas", {}).get(kind, "")))
	return _atlases[kind]

## The level the cell south of an edge shows at that edge: a stair's height where it meets it, water -1.
func edge_level(x: int, y: int) -> int:
	if not room.inside(x, y): return 99
	if not room.stair_at(x, y).is_empty(): return floori(room.height_at(Vector2((x + 0.5) * TopdownRoom.TILE, y * TopdownRoom.TILE + 0.5)) / TopdownRoom.LEVEL + 0.01)
	return room.levels[y * room.w + x]

## A node in the sorted layer sits at its key and draws back to screen rows by `lift` = key.
class Sorted extends Node2D:
	var world
	var rects: Array = []    ## what it covers on screen, for the silhouette test
	func _init(w) -> void:
		world = w
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func key(k: float) -> void:
		position = Vector2(0, k)

class WaterView extends Node2D:
	var world
	var frame := -1
	func _init(w) -> void: world = w
	func _process(_d: float) -> void:
		var f := int(Time.get_ticks_msec() / 250) % 4
		if f != frame:
			frame = f
			queue_redraw()
	func _draw() -> void:
		var r: TopdownRoom = world.room
		var src: Rect2 = world.tile("water_%d" % maxi(0, frame))
		for y in r.h:
			for x in r.w:
				if r.levels[y * r.w + x] == TopdownRoom.WATER: draw_texture_rect_region(world.atlas("tiles"), Rect2(x * T, y * T - TopdownRoom.WATER_Z / TopdownRoom.ART, T, T), src)

## Ground-level tops and the bank faces over water: under everything that sorts.
class FloorView extends Node2D:
	var world
	func _init(w) -> void: world = w
	func _draw() -> void:
		var r: TopdownRoom = world.room
		for y in r.h:
			for x in r.w:
				if r.levels[y * r.w + x] != 0 or not r.stair_at(x, y).is_empty(): continue
				draw_texture_rect_region(world.atlas("tiles"), Rect2(x * T, y * T, T, T), world.tile(world.top_tile(x, y)))
				if world.edge_level(x, y + 1) == TopdownRoom.WATER:
					var src: Rect2 = world.tile(world.face_tile(x, y, true, true))
					draw_texture_rect_region(world.atlas("tiles"), Rect2(x * T, (y + 1) * T, T, T * 0.5), Rect2(src.position, Vector2(T, T * 0.5)))

## One row of raised cells: their tops at their height and their south faces down to the level in front, with a rim
## on the sides that drop away. Its key is the row's south edge.
class StripView extends Sorted:
	var row := 0
	func _init(w, y: int) -> void:
		super(w)
		row = y
		key((y + 1) * T)
		var r: TopdownRoom = w.room
		for x in r.w:
			var l := r.levels[y * r.w + x]
			if l <= 0 or not r.stair_at(x, y).is_empty(): continue
			var south := mini(l, w.edge_level(x, y + 1))
			rects.append(Rect2(x * T, (y - l) * T, T, T * (1 + l - maxi(south, -1)) - (T * 0.5 if south < 0 else 0.0)))
	func _draw() -> void:
		var r: TopdownRoom = world.room
		var lift := position.y
		for x in r.w:
			var l := r.levels[row * r.w + x]
			if l <= 0 or not r.stair_at(x, row).is_empty(): continue
			var top := Rect2(x * T, (row - l) * T - lift, T, T)
			draw_texture_rect_region(world.atlas("tiles"), top, world.tile(world.top_tile(x, row)))
			var south := mini(l, world.edge_level(x, row + 1))
			for k in range(l - south):
				var water: bool = south + k + 1 == 0
				var src: Rect2 = world.tile(world.face_tile(x, row, k == 0, water))
				var h := T * 0.5 if water else T
				draw_texture_rect_region(world.atlas("tiles"), Rect2(x * T, (row + 1 - l + k) * T - lift, T, h), Rect2(src.position, Vector2(T, h)))
			for side in [-1, 1]:   # the rim where the neighbour drops away (plan §1.5)
				if world.edge_level(x + side, row) < l: draw_rect(Rect2(top.position.x + (T - 1 if side > 0 else 0), top.position.y, 1, T), Color(1, 0.95, 0.8, 0.35))

## A flight of stairs, drawn step by step from its top edge to its foot; its key is the flight's south edge.
class StairsView extends Sorted:
	var rect: Rect2
	func _init(w, st: Dictionary) -> void:
		super(w)
		var r: Rect2i = st.rect
		var top := r.position.y * T - float(st.to) * T
		var foot := r.end.y * T - float(st.from) * T
		rect = Rect2(r.position.x * T, top, r.size.x * T, foot - top)
		rects.append(rect)
		key(r.end.y * T)
	func _draw() -> void:
		var src: Rect2 = world.tile("stairs")
		var lift := position.y
		var y := rect.position.y
		while y < rect.end.y:
			for x in int(rect.size.x / T):
				draw_texture_rect_region(world.atlas("tiles"), Rect2(rect.position.x + x * T, y - lift, T, minf(8.0, rect.end.y - y)), Rect2(src.position, Vector2(T, minf(8.0, rect.end.y - y))))
			y += 8.0
		for side in [0.0, rect.size.x - 1.0]:
			draw_rect(Rect2(rect.position.x + side, rect.position.y - lift, 1, rect.size.y), Color(0.03, 0.06, 0.07, 0.5))

## A prop sprite from the atlas; its footprint's south-west corner sits on the floor it stands on, its key is the
## footprint's south edge (a little past the row's own, so it draws over the floor it stands on).
class PropView extends Sorted:
	var src: Rect2
	var at: Vector2
	func _init(w, p: Dictionary) -> void:
		super(w)
		var art: Dictionary = p.art
		var rr: Array = art.get("rect", [0, 0, 16, 16])
		var origin: Array = art.get("origin", [0, 16])
		src = Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3]))
		var cell: Vector2i = p.cell
		var south: float = (cell.y + (p.size as Vector2i).y) * T
		var lvl := int(p.level)
		var ground := TopdownRoom.WATER_Z / TopdownRoom.ART * -1.0 if lvl < 0 else -lvl * T
		at = Vector2(cell.x * T - float(origin[0]), south + ground - float(origin[1]))
		rects.append(Rect2(at, src.size))
		key(south + 0.5)
	func _draw() -> void:
		draw_texture_rect_region(world.atlas("props"), Rect2(at - position, src.size), src)

## The blob shadow on the floor under the body; it shrinks and fades with the height above that floor (plan §1.5).
class ShadowView extends Sorted:
	var k := 1.0
	var feet := Vector2.ZERO
	func sync() -> void:
		var m: TopdownMotor = world.player.motor
		var ground: float = world.room.height_at(m.pos)
		visible = ground < INF and m.sink_t < 0.0
		if not visible: return
		k = clampf(1.0 - (m.z - ground) / 96.0, 0.6, 1.0)
		feet = TopdownWorld.to_screen(m.pos, ground).round()
		key(world.room.sort_key(m.pos, ground))
		position.x = feet.x
		queue_redraw()
	func _draw() -> void:
		var rx := roundf(8.0 * k)
		var col := Color(0.01, 0.035, 0.04, 0.55 * k)
		var dy := feet.y - position.y
		draw_rect(Rect2(-rx, dy - 1, rx * 2, 3), col)
		draw_rect(Rect2(-rx + 2, dy - 2, rx * 2 - 4, 5), col)

## Landing dust and splashes, a few pixels each.
class FxView extends Sorted:
	var items: Array = []
	func puff(p: Vector2, z: float, fall: float) -> void:
		items.append({"kind": "dust", "at": TopdownWorld.to_screen(p, z).round(), "t": 0.0, "size": clampf(fall / 32.0, 0.5, 2.0), "key": world.room.sort_key(p, z)})
	func splash(p: Vector2) -> void:
		items.append({"kind": "splash", "at": TopdownWorld.to_screen(p, TopdownRoom.WATER_Z).round(), "t": 0.0, "size": 1.0, "key": world.room.sort_key(p, 0.0)})
	func advance(delta: float) -> void:
		for it in items: it.t = float(it.t) + delta
		items = items.filter(func(it): return float(it.t) < 0.45)
		key(items.back().key if not items.is_empty() else 0.0)
		queue_redraw()
	func _draw() -> void:
		for it in items:
			var a: Vector2 = it.at - position
			var t := float(it.t) / 0.45
			var col := Color(0.91, 0.88, 0.81, 0.8 * (1.0 - t)) if it.kind == "dust" else Color(0.56, 0.8, 0.8, 0.9 * (1.0 - t))
			var spread := roundf((3.0 + 9.0 * t) * float(it.size))
			for s in [-1, 1]:
				draw_rect(Rect2(a.x + s * spread - 1, a.y - 1 - roundf(3.0 * t), 2, 2), col)
				draw_rect(Rect2(a.x + s * roundf(spread * 0.5) - 1, a.y - 2 - roundf(5.0 * t), 1, 1), col)
			if it.kind == "splash": draw_arc(a, spread, 0, TAU, 12, col, 1.0)

## The body drawn flat in jade over whatever covers it (the side-view game's occlusion outline, redone for the grid).
class Silhouette extends Node2D:
	var world
	func _init(w) -> void:
		world = w
		z_index = 100
		var mat := ShaderMaterial.new()
		mat.shader = Shader.new()
		mat.shader.code = "shader_type canvas_item;\nvoid fragment() { COLOR = vec4(0.4, 0.84, 0.74, texture(TEXTURE, UV).a * 0.55); }"
		material = mat
	func _draw() -> void:
		if world.occluded: world.player.draw_body(self, world.player.screen)

## A line under the HUD that says what this is.
class Caption extends Control:
	var world
	func _init(w) -> void:
		world = w
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	func _draw() -> void:
		UiKit.draw_outlined(self, Tx.t("topdown.caption"), Vector2(320, 28), 14, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 640)

## Phase 2: one foe on the grid, a PLACEHOLDER sprite (art/topdown/placeholder_foes.png, east drawn, west mirrored)
## sorted with the room like the body, its shadow on the floor under it, a flash when struck and a fade in death.
class FoeView extends Sorted:
	var uid := 0
	var frames: Dictionary = {}
	var cell := Vector2(32, 24)
	var foot := Vector2(16, 21)
	var feet := Vector2.ZERO
	var ground_y := 0.0
	var src := Rect2()
	var flip := false
	var tint := Color.WHITE
	var t := 0.0
	var last := ""
	func _init(w, e: EnemyState) -> void:
		super(w)
		uid = e.uid
		var sheet: Dictionary = w.room.tileset.get("foes", {})
		frames = sheet.get("species", {}).get(e.def_id, sheet.get("species", {}).get("mudshell_crab", {}))
		var c: Array = sheet.get("cell", [32, 24])
		var f: Array = sheet.get("foot", [16, 21])
		cell = Vector2(float(c[0]), float(c[1]))
		foot = Vector2(float(f[0]), float(f[1]))
	func sync(delta: float) -> void:
		var e: EnemyState = Game.room_rt.enemies.get(uid) if Game.room_rt else null
		if e == null:
			queue_free()
			return
		var room: TopdownRoom = world.room
		feet = TopdownWorld.to_screen(e.plane, e.altitude + e.hover).round()
		var g := room.height_at(e.plane)
		ground_y = TopdownWorld.to_screen(e.plane, g if g < INF else e.altitude).round().y
		key(room.sort_key(e.plane, e.altitude))
		position.x = feet.x
		visible = not e.hidden or e.ai.state == "windup"
		var act := str(e.action)
		if e.ai.state == "stagger" or (e.flash > 0.0 and act in ["idle", "walk"]) or act == "death": act = "hurt"
		if not frames.has(act): act = "idle"
		if act != last:
			last = act
			t = 0.0
		t += delta
		var list: Array = frames.get(act, [[0, 0]])
		var at: Array = list[int(t * (8.0 if act == "walk" else 2.0)) % list.size()]
		src = Rect2(float(at[0]), float(at[1]), cell.x, cell.y)
		flip = e.facing < 0
		tint = Color(1, 1, 1, clampf(1.0 - e.dead_time / 1.4, 0.0, 1.0)) if not e.alive else (Color(1.8, 1.8, 1.8) if e.flash > 0.0 else Color.WHITE)
		queue_redraw()
	func _draw() -> void:
		var sy := ground_y - position.y
		draw_rect(Rect2(-7, sy - 1, 14, 3), Color(0.01, 0.035, 0.04, 0.45 * tint.a))
		draw_rect(Rect2(-5, sy - 2, 10, 5), Color(0.01, 0.035, 0.04, 0.45 * tint.a))
		draw_set_transform(Vector2(0, feet.y - position.y), 0.0, Vector2(-1, 1) if flip else Vector2.ONE)
		draw_texture_rect_region(world.atlas("foes"), Rect2(-foot, cell), src, tint)
		draw_set_transform(Vector2.ZERO)

## Phase 2 (decision 30): the aim on the ground, on the overlay in world units. While a thumb aims (the player's
## `aim`), its form from the feet: an arrow for a blow, a line, a cone, a circle at its point (joined to the feet) or
## round the caster, and a ring on the foe it snaps to. Otherwise, in a fight, a faint ring marks the soft lock: the foe
## a tap would strike.
class AimView extends Node2D:
	var world
	func _init(w) -> void:
		world = w
		z_index = 3500
	func _draw() -> void:
		var p = world.player
		if not p.bound(): return
		var m: TopdownMotor = p.motor
		var fill := Color(UiKit.BRIGHT_JADE, 0.16)
		var line := Color(UiKit.BRIGHT_JADE, 0.75)
		var a: Dictionary = p.aim
		_guard(m)
		match str(a.get("move", "")):
			"plunge":
				# Decision 35: the Plunge's landing ring on the floor straight under the body, joined to it by a drop line.
				var o0: Vector2 = TopdownWorld.lifted(m.pos, m.z)
				var c0: Vector2 = TopdownWorld.lifted(a.at, float(a.ground))
				var y := o0.y + 6.0
				while y < c0.y - 6.0:
					draw_line(Vector2(o0.x, y), Vector2(o0.x, minf(y + 8.0, c0.y - 6.0)), Color(UiKit.GOLD, 0.8), 2.0)
					y += 14.0
				draw_circle(c0, float(a.reach), Color(UiKit.GOLD, 0.14))
				draw_arc(c0, float(a.reach), 0, TAU, 48, Color(UiKit.GOLD, 0.9), 3.0)
				return
			"guard": return
		if a.is_empty():
			var foe := TopdownAim.soft_target(Game.room_rt.living_enemies(), m.pos, m.z, m.dir, not m.grounded)
			if foe != null and WorldLabels.fight_near(Game.active(), m.pos): _ring(foe, Color(UiKit.PALE_GOLD, 0.45))
			return
		var o: Vector2 = TopdownWorld.lifted(m.pos, m.z)
		var d: Vector2 = a.dir
		var reach := float(a.reach)
		var side := Vector2(-d.y, d.x)
		match str(a.form) if a.kind == "skill" else "arrow":
			"arrow":
				var tip := o + d * (reach + 24.0)
				if str(a.get("move", "")) == "finisher":
					# Decision 35: the finisher armed, a heavier gold arrow with the step's sweep at its head.
					var gold := Color(UiKit.GOLD, 0.95)
					draw_line(o + d * 10.0, tip, gold, 5.0)
					draw_colored_polygon(PackedVector2Array([tip + d * 14.0, tip + side * 10.0, tip - side * 10.0]), gold)
					draw_arc(o, reach + 30.0, d.angle() - 0.5, d.angle() + 0.5, 16, gold, 3.0)
				else:
					draw_line(o + d * 10.0, tip, line, 3.0)
					draw_colored_polygon(PackedVector2Array([tip + d * 10.0, tip + side * 7.0, tip - side * 7.0]), line)
			"line":
				var hw := float(a.half)
				var poly := PackedVector2Array([o + side * hw, o + side * hw + d * reach, o - side * hw + d * reach, o - side * hw])
				draw_colored_polygon(poly, fill)
				poly.append(poly[0])
				draw_polyline(poly, line, 2.0)
			"cone":
				var half := deg_to_rad(float(TopdownAim.cfg("cone_half_deg", 45)))
				var pts := PackedVector2Array([o])
				for i in 13: pts.append(o + d.rotated(lerpf(-half, half, i / 12.0)) * reach)
				draw_colored_polygon(pts, fill)
				pts.append(o)
				draw_polyline(pts, line, 2.0)
			"point":
				var at: Vector2 = a.at
				var g: float = world.room.height_at(at)
				var c := TopdownWorld.lifted(at, g if g < INF else m.z)
				draw_line(o, c, Color(line, 0.4), 2.0)
				draw_circle(c, float(TopdownAim.cfg("point_radius", 48)), fill)
				draw_arc(c, float(TopdownAim.cfg("point_radius", 48)), 0, TAU, 40, line, 2.0)
			"self":
				draw_circle(o, reach, fill)
				draw_arc(o, reach, 0, TAU, 56, line, 2.0)
		if a.target != null and is_instance_valid(a.target) and (a.target as EnemyState).alive: _ring(a.target, UiKit.GOLD)
	## A guard (Attack held, decision 35, or the Dodge button held): the guarded front as a half ring at the feet, jade
	## for a guard, gold for a stance; brighter and heavier while the parry window is open. Nothing animates.
	func _guard(m: TopdownMotor) -> void:
		var tl: Dictionary = Game.combat.timeline(world.player.actor_id)
		if not tl.guard: return
		var stance := float(tl.stance) > 0.0
		var parry := float(tl.guard_t) <= float(StatRules.family(Game.active()).get("parry_s", 0.18))
		var col := Color(UiKit.GOLD if stance else UiKit.BRIGHT_JADE, 1.0 if parry else 0.7)
		var o: Vector2 = TopdownWorld.lifted(m.pos, m.z)
		draw_set_transform(o, 0.0, Vector2(1, 0.5))
		draw_arc(Vector2.ZERO, 30.0, m.dir.angle() - PI * 0.5, m.dir.angle() + PI * 0.5, 20, col, 5.0 if parry else 3.0)
		draw_set_transform(Vector2.ZERO)

	func _ring(e: EnemyState, col: Color) -> void:
		var at := TopdownWorld.lifted(e.plane, e.altitude)
		draw_set_transform(at, 0.0, Vector2(1, 0.5))
		draw_arc(Vector2.ZERO, e.half_width() + 6.0, 0, TAU, 32, col, 2.0)
		draw_set_transform(Vector2.ZERO)
