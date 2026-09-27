class_name TopdownWorld
extends Node2D
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1, §4): the prototype room's view, mounted by main.gd in
## place of world.gd behind `--topdown-proto` or the title screen's hidden entry. The world renders at 640x360 in its
## own SubViewport (one art px = one viewport px, snapped to whole pixels) shown x2 under the 1280x720 HUD. Floors and
## water draw first; raised rows, stairs, props, the body and its shadow sort in one Y-sorted layer by explicit keys
## (TopdownRoom.sort_key: every node's y is its key and it draws back to its screen row); a silhouette shows the body
## through whatever covers it. The camera follows the ground underfoot, not the jump arc, and snaps to whole pixels.

const Player := preload("res://scripts/topdown/topdown_player.gd")
const TILES := preload("res://art/topdown/proto_tiles.png")
const PROPS := preload("res://art/topdown/proto_props.png")
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

func _ready() -> void:
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
	var caption := CanvasLayer.new()
	caption.layer = 4
	add_child(caption)
	caption.add_child(Caption.new(self))
	cam_z = player.motor.z
	_sync(0.0)
	cam = _cam_target()
	camera.position = cam.round()

func _physics_process(delta: float) -> void:
	if sim_frozen or (Game.paused if Game else false): return
	for e in player.physics_step(delta): _feedback(e)

func _process(delta: float) -> void:
	_sync(delta)
	var m: TopdownMotor = player.motor
	if m.grounded and m.sink_t < 0.0: cam_z = m.z
	elif m.z < cam_z: cam_z = maxf(m.z, room.height_at(m.pos) if room.height_at(m.pos) < INF else m.z)
	var k := 1.0 - exp(-delta * 3.0 / float(TopdownMotor.conf("camera_settle_s", 0.3)))
	cam = cam.lerp(_cam_target(), k)
	camera.position = cam.round()

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
	occluded = is_occluded()
	silhouette.queue_redraw()

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
		"dashed": Audio.play("dodge")
		"landed":
			fx.puff(m.pos, m.z, float(e.fall))
			if float(e.fall) > 12.0: Audio.play("land")
		"splashed":
			fx.splash(m.pos)
			Audio.play("water_step")

## World units on the ground plane at height z to the viewport's art px.
static func to_screen(p: Vector2, z: float) -> Vector2:
	return Vector2(p.x, p.y - z) / TopdownRoom.ART

func tile(name: String) -> Rect2:
	var r: Array = room.tileset.get("tiles", {}).get(name, [0, 0, 16, 16])
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))

## The top tile a paint mark draws, with a fixed per-cell variant.
func top_tile(x: int, y: int) -> String:
	var v := (x * 7 + y * 13) % 5 < 2
	match room.paint_at(x, y):
		"g": return "grass_b" if v else "grass_a"
		"f": return "grass_flowers"
		"d": return "dirt"
		"p": return "paving_b" if v else "paving_a"
		"s": return "stone_top"
		"w": return "wood"
		"r": return "rock"
	return "grass_a"

func face_tile(x: int, y: int, first: bool, over_water: bool) -> String:
	var kind: String = {"g": "earth", "f": "earth", "d": "earth", "p": "stone", "s": "stone", "w": "wood", "r": "rock"}.get(room.paint_at(x, y), "stone")
	if over_water and kind != "wood": kind = "bank"
	return kind + ("_face_top" if first else "_face")

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
				if r.levels[y * r.w + x] == TopdownRoom.WATER: draw_texture_rect_region(TILES, Rect2(x * T, y * T - TopdownRoom.WATER_Z / TopdownRoom.ART, T, T), src)

## Ground-level tops and the bank faces over water: under everything that sorts.
class FloorView extends Node2D:
	var world
	func _init(w) -> void: world = w
	func _draw() -> void:
		var r: TopdownRoom = world.room
		for y in r.h:
			for x in r.w:
				if r.levels[y * r.w + x] != 0 or not r.stair_at(x, y).is_empty(): continue
				draw_texture_rect_region(TILES, Rect2(x * T, y * T, T, T), world.tile(world.top_tile(x, y)))
				if world.edge_level(x, y + 1) == TopdownRoom.WATER:
					var src: Rect2 = world.tile(world.face_tile(x, y, true, true))
					draw_texture_rect_region(TILES, Rect2(x * T, (y + 1) * T, T, T * 0.5), Rect2(src.position, Vector2(T, T * 0.5)))

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
			draw_texture_rect_region(TILES, top, world.tile(world.top_tile(x, row)))
			var south := mini(l, world.edge_level(x, row + 1))
			for k in range(l - south):
				var water: bool = south + k + 1 == 0
				var src: Rect2 = world.tile(world.face_tile(x, row, k == 0, water))
				var h := T * 0.5 if water else T
				draw_texture_rect_region(TILES, Rect2(x * T, (row + 1 - l + k) * T - lift, T, h), Rect2(src.position, Vector2(T, h)))
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
				draw_texture_rect_region(TILES, Rect2(rect.position.x + x * T, y - lift, T, minf(8.0, rect.end.y - y)), Rect2(src.position, Vector2(T, minf(8.0, rect.end.y - y))))
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
		draw_texture_rect_region(PROPS, Rect2(at - position, src.size), src)

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
