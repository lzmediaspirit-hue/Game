class_name TopdownWorld
extends Node2D
## Top-down redesign, Phase 1 (docs/redesign_top_down_plan.md §1, §4): the prototype room's view, mounted by main.gd in
## place of world.gd behind `--topdown-proto`. The world renders at 640x360 in its own SubViewport (one art px = one
## viewport px, snapped to whole pixels) shown x2 under the 1280x720 HUD. Floors and water draw first; raised rows,
## stairs, props, the body and its shadow sort in one Y-sorted layer by explicit keys (TopdownRoom.sort_key: every
## node's y is its key and it draws back to its screen row); a silhouette shows the body through whatever covers it.
## The camera follows the ground underfoot, not the jump arc, and snaps to whole pixels.
##
## Phase 2: with a character, the room is entered through the World authority (`enter_grid_room`) and the simulation
## runs as in every room: Game.tick after the body's step, the room's foes (PLACEHOLDER sprites, sorted with the rest),
## a blow's hit-stop freezing both. Over the viewport, at the HUD's resolution and following the camera, the overlay
## holds what reads best crisp: the effects layer (FxLayer, the technique forms from art/fx/, numbers), the foes'
## labels and HP bars (EnemyView in label mode, placed by WorldLabels round the HUD), loot, and the aim (decision 30).
##
## Phase 3 (docs/redesign/art_bible.md, decisions 32–34): the terrain draws by the art bible's rules (TopdownTerrain):
## paths and shores auto-tiled, rims, contact shade and cast shade on every raised edge, face ends and stair cheeks,
## and each prop's floor shadow cut to the floor it stands on. Plants sway and lotus bob in their own frames, and the
## foes are the eight-facing sheet (art/topdown/foes.png).
##
## Phase 4 (`live`): the world view of a character's own game in every room of the world that has a layout on the grid
## (WorldAuthority.grid_for; main.gd mounts world.gd for the others). The room is Game.room_rt's and the view rebuilds
## as each room is entered: its people, things and ways (TopdownPlaces), the ways walked into or taken with the
## context button, the context's offer, the names over the world and the events' effects as the side view plays them
## (WorldShared), a night room's tint and the room's hazards and weather (HazardView), and moments (MomentView reads
## the same anchors of either view).
##
## Decision 40 (runtime light, docs/redesign/art_bible.md "Terrain v2 · Runtime light"): each room's cast shadows are
## baked once as it is built (TopdownShadows) and laid on the water, the ground floor and each raised row's tops; the
## grade, the night and its lights, cloud shadows and particles are the Atmosphere's (TopdownAtmosphere), all tuned in
## TopdownLight.

const Player := preload("res://scripts/topdown/topdown_player.gd")
const VIEW := Vector2i(TopdownRoom.VIEW)   ## the world view in art px (TopdownRoom.VIEW)
const T := 16.0
const CHUNK := Vector2i(16, 12)   ## Terrain v2: the floor and the water are drawn in chunks of this many cells

var room_id := "td_proto_square"
var live := false               ## Phase 4: the character's own room (Game.room_rt), not the prototype square
var room: TopdownRoom
var terrain: TopdownTerrain
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
var hud_minimap := false        ## the HUD's minimap (the grid's map); off in the prototype square, on in the world
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
# Phase 4: the room's people, things and ways (their label views, as world.gd keeps its views; TopdownPlaces).
var npc_views: Dictionary = {}
var object_views: Dictionary = {}
var portal_views: Array = []
var enemy_views: Dictionary:    ## MomentView and WorldShared ask for the foes' views by this name
	get: return label_views
var floor_layer: Node2D         ## marks on the floor, under everything sorted (the ways out)
var tint: CanvasModulate        ## a night room's blue (decision 40: the Atmosphere's night layer does it; kept white)
var shadows: TopdownShadows     ## decision 40: the room's cast shadows, baked as it is built
var atmosphere: TopdownAtmosphere   ## decision 40: grade, night and lights, clouds and particles
var hazards: HazardView
var transfer_cooldown := 0.0
var camera_hold := {}           ## a moment's camera move: {target (art px), t, in, hold, out}
var figures: Dictionary = {}    ## object id -> its Figure in the sorted layer (a staged scene moves the people)
## Decision 39: a staged scene's camera (SceneDirector): the point it looks at in world units (null: the body's
## follow), its zoom, and `stage_snap` to cut there at once (Reduce motion).
var stage_cam = null
var stage_zoom := 1.0
var stage_snap := false
var _room_nodes: Array = []     ## what the room built, cleared when the next one is entered
## Decision 38: the combat's effects on the ground plane (smears, forms, impacts, marks, dust) in the sorted layer, and
## whether a hit-stop holds the fight (and them) this frame.
var tfx: TopdownFx
var held := false

signal context_changed(ctx: Dictionary)

func _ready() -> void:
	if live and Game.room_rt != null and Game.room_rt.topdown != null:
		room = Game.room_rt.topdown
	# Phase 2: a character enters the prototype room through the World authority; its RoomRuntime carries the grid.
	elif Game.active() != null and Game.submit({"type": "enter_grid_room", "room": room_id}).get("ok", false):
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
	tint = CanvasModulate.new()
	viewport.add_child(tint)
	floor_layer = Node2D.new()
	floor_layer.name = "Floor"
	viewport.add_child(floor_layer)
	sorted = Node2D.new()
	sorted.name = "Sorted"
	sorted.y_sort_enabled = true
	viewport.add_child(sorted)
	shadow = ShadowView.new(self)
	sorted.add_child(shadow)
	player = Player.new()
	player.world = self
	player.motor = TopdownMotor.new(room)
	player.actor_id = Game.active_id if Game.active() != null else ""
	sorted.add_child(player)
	fx = FxView.new(self)
	sorted.add_child(fx)
	# The silhouette's layers draw as one image in a group, so its translucent jade is even where they overlap.
	var group := CanvasGroup.new()
	group.z_index = 100
	group.self_modulate = Color(1, 1, 1, 0.55)
	viewport.add_child(group)
	silhouette = Silhouette.new(self)
	group.add_child(silhouette)
	camera = Camera2D.new()
	viewport.add_child(camera)
	camera.make_current()
	atmosphere = TopdownAtmosphere.new(self)
	viewport.add_child(atmosphere)
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
	effects.forms = false    # decision 38: the forms, bolts and impact marks are TopdownFx's ground-plane sheets
	effects.sparks = false
	combat_fx = CombatFx.new(effects, self)
	tfx = TopdownFx.new(self)
	if not live:
		var caption := CanvasLayer.new()
		caption.layer = 4
		add_child(caption)
		caption.add_child(Caption.new(self))
	_build_room()
	if player.bound():
		Game.bind_movement(player.actor_id, player.state)
		GameEvents.event.connect(_on_event)
		if not live: _loadout(Game.active())
		if live: _place_player()
	_settle_camera()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

## The room's own nodes: the floor, water and raised rows, stairs and props, its people, things and ways, the foes
## and the loot lying there. The body, its shadow and the effects stay from room to room.
func _build_room() -> void:
	for n in _room_nodes:
		if is_instance_valid(n): n.queue_free()
	_room_nodes.clear()
	for uid in foe_views.keys():
		if is_instance_valid(foe_views[uid]): foe_views[uid].queue_free()
	for uid in label_views.keys():
		if is_instance_valid(label_views[uid]): label_views[uid].queue_free()
	foe_views.clear()
	label_views.clear()
	for l in loot_layer.get_children(): l.queue_free()
	if tfx != null: tfx.clear()
	terrain = TopdownTerrain.new(room)   # Phase 3's tile rules, per room
	var bg := ColorRect.new()
	bg.color = Color("0A2027")
	bg.size = room.art_size() + Vector2(VIEW) * 2.0
	bg.position = -Vector2(VIEW)
	# Terrain v2: the floor and the water in chunks, so the renderer skips the ones off screen and the water redraws
	# only the chunks in view.
	var under: Array = [bg]
	for cy in range(0, room.h, CHUNK.y):
		for cx in range(0, room.w, CHUNK.x):
			var r := Rect2i(Vector2i(cx, cy), CHUNK).intersection(Rect2i(0, 0, room.w, room.h))
			var water := WaterView.new(self, r)
			if not water.cells.is_empty(): under.insert(1, water)
			else: water.free()
	# Decision 40: the cast shadows, baked once for the room, laid over the water (after its chunks) and over the ground
	# floor (after its chunks).
	shadows = TopdownShadows.new(room)
	var water_shade := shadows.view("water")
	if water_shade != null: under.append(water_shade)
	for cy in range(0, room.h, CHUNK.y):
		for cx in range(0, room.w, CHUNK.x):
			under.append(FloorView.new(self, Rect2i(Vector2i(cx, cy), CHUNK).intersection(Rect2i(0, 0, room.w, room.h))))
	var ground_shade := shadows.view("ground")
	if ground_shade != null: under.append(ground_shade)
	for i in range(under.size() - 1, -1, -1):
		viewport.add_child(under[i])
		viewport.move_child(under[i], 0)   # under the floor marks and everything sorted
	_room_nodes.append_array(under)
	for y in room.h:
		var strip := StripView.new(self, y)
		if not strip.rects.is_empty():
			sorted.add_child(strip)
			_room_nodes.append(strip)
			var shade := shadows.view(y, strip.position)   # the shadows on the row's raised tops, drawn with it
			if shade != null: strip.add_child(shade)
	for st in room.stairs:
		var sv := StairsView.new(self, st)
		sorted.add_child(sv)
		_room_nodes.append(sv)
	for p in room.props:
		var pv := PropView.new(self, p)
		sorted.add_child(pv)
		_room_nodes.append(pv)
	npc_views = {}
	object_views = {}
	portal_views = []
	figures = {}
	labels_a = 1.0   # the room's new labels are drawn whole; a scene's cut fades them from there
	if live and Game.room_rt != null:
		var built := TopdownPlaces.build(room, Game.room_rt.def, sorted, floor_layer, overlay, player)
		npc_views = built.npc_views
		object_views = built.object_views
		portal_views = built.portal_views
		figures = built.figures
		_room_nodes.append_array(built.nodes)
		# The hazards' washes, weather and marks draw on the overlay under the names; their parts at a spot (a ring, a
		# falling rock, a bolt) sort with the room in the viewport.
		hazards = HazardView.new()
		hazards.world = self
		hazards.room = room
		hazards.sorted_layer = sorted
		overlay.add_child(hazards)
		_room_nodes.append(hazards)
		for l in Game.room_rt.loot:
			var lv := LootView.new()
			lv.setup(l)
			loot_layer.add_child(lv)
		hud_minimap = true
	atmosphere.enter_room()   # decision 40: the room's grade, night and lights, clouds and particles
	# The body, its shadow and its dust after the room's own nodes, so a tie in the sort goes to the body.
	for n in [shadow, player, fx]: sorted.move_child(n, -1)
	if player != null and player.bound():
		for uid in Game.room_rt.enemies: _add_foe(Game.room_rt.enemies[uid])

## Phase 4: the body where the World authority put the character (a portal's arrival, a shrine, a saved spot).
func _place_player() -> void:
	var c = Game.active()
	player.motor.room = room
	player.motor.place(Vector2(float(c.position.get("x", room.spawn.x)), float(c.position.get("y", room.spawn.y))))
	var inward := Vector2(float(c.position.get("facing", 1)), 0.0)
	var p := Game.room_rt.portal_def(str(c.position.get("portal", "")))
	if p.has("dir"): inward = -Vector2(float(p.dir[0]), float(p.dir[1]))
	player.motor.face(inward)
	player.physics_step(0.0001)
	transfer_cooldown = 0.4

func _settle_camera() -> void:
	cam_z = player.motor.z
	_sync(0.0)
	cam = _cam_target()
	camera.position = cam.round()

func _physics_process(delta: float) -> void:
	held = false
	if sim_frozen or Game.paused: return
	# A blow's hit-stop holds the fight still (decision 38: by its weight; none under Reduce motion).
	if player.bound():
		if not CombatFeel.hitstop_on(): Game.combat.hitstop = 0.0
		elif Game.combat.hold_for_hitstop(delta):
			held = true
			return
	for e in player.physics_step(delta): _feedback(e)
	if player.bound(): Game.tick(delta)
	if live: _check_portals(delta)

func _process(delta: float) -> void:
	_sync(delta)
	var m: TopdownMotor = player.motor
	if m.grounded and m.sink_t < 0.0: cam_z = m.z
	elif m.z < cam_z and m.sink_t < 0.0: cam_z = m.z   # a fall below the last floor is followed down
	var k := 1.0 - exp(-delta * 3.0 / float(TopdownMotor.conf("camera_settle_s", 0.3)))
	var goal := _cam_target()
	if stage_cam != null: goal = _clamp_cam((stage_cam as Vector2) / TopdownRoom.ART)   # a staged scene looks elsewhere
	if not camera_hold.is_empty():
		var h := camera_hold
		h.t = float(h.t) + delta
		var ends := float(h.in) + float(h.hold) + float(h.out)
		goal = goal.lerp(h.target, smoothstep(0.0, float(h.in), h.t) * (1.0 - smoothstep(ends - float(h.out), ends, h.t)))
		if float(h.t) >= ends: camera_hold = {}
	cam = goal if stage_snap else cam.lerp(goal, k)
	stage_snap = false
	camera.position = cam.round()
	camera.offset = (shake.offset(delta) / TopdownRoom.ART).round()
	camera.zoom = Vector2(stage_zoom, stage_zoom)
	overlay.scale = camera.zoom
	overlay.position = (Vector2(VIEW) * 0.5 - (camera.position + camera.offset) * stage_zoom) * TopdownRoom.ART
	if player.bound():
		if live: _update_context()
		layout_labels()

## The camera's goal in art px: the feet on the ground underfoot (not the jump arc) plus a look-ahead, inside the room
## as it is drawn (a ridge on its north edge included) and never leaving the body out of view (TopdownRoom.camera_for,
## which the Enemies authority also asks what the player sees).
func _cam_target() -> Vector2:
	var m: TopdownMotor = player.motor
	return room.camera_for(m.pos, cam_z, m.vel)

## A staged scene's camera point in art px kept inside the room as it is drawn (a ridge on its north edge included), at
## the view's zoom, or on its middle where the room is smaller.
func _clamp_cam(t: Vector2) -> Vector2:
	var b := room.drawn_rect()
	var half := Vector2(VIEW) * 0.5 / stage_zoom
	t.x = b.get_center().x if b.size.x <= half.x * 2.0 else clampf(t.x, b.position.x + half.x, b.end.x - half.x)
	t.y = b.get_center().y if b.size.y <= half.y * 2.0 else clampf(t.y, b.position.y + half.y, b.end.y - half.y)
	return t

func _sync(delta: float) -> void:
	player.sync(delta)
	shadow.sync()
	fx.advance(delta)
	if not held: tfx.advance(delta)
	_hold_marks()
	for uid in foe_views.keys():
		if is_instance_valid(foe_views[uid]): foe_views[uid].sync(delta)
		else: foe_views.erase(uid)
	occluded = is_occluded()
	silhouette.queue_redraw()
	aim_view.queue_redraw()

## Is the body covered by something sorted after it (a raised row's face, the flight of stairs, a prop)?
func is_occluded() -> bool:
	var feet_px: Vector2 = player.screen
	var body := Rect2(feet_px.x - 5, feet_px.y - 34, 10, 30)
	for n in sorted.get_children():
		if n == player or n == shadow or n == fx or n.position.y <= player.position.y: continue
		for r in n.get("rects") if n.get("rects") != null else []:
			if (r as Rect2).intersects(body): return true
	return false

func _feedback(e: Dictionary) -> void:
	var m: TopdownMotor = player.motor
	match str(e.type):
		"jumped": Audio.play("jump")
		"dashed", "plunged":
			Audio.play("dodge")
			if str(e.type) == "dashed": tfx.dust("dash", m.pos, m.z, m.dash_dir)   # decision 38: the dash's kick-off dust
		"landed":
			if float(e.fall) > 6.0 or e.get("plunge", false): tfx.dust("land", m.pos, m.z)
			if e.get("plunge", false):
				# The Plunge's impact (decision 35, drawn for decision 38): a crater, cracks and stone on the floor, a shock
				# ring the size of its strike, and a heavy jolt.
				tfx.mark("plunge", m.pos, m.z)
				effects.add("ring", player_feet(), {"color": Color(UiKit.PALE_GOLD, 0.8), "radius": float(ContentDB.movement("plunge.radius", 60.0)), "dur": 0.35})
				Audio.play("rumble")
				feel("heavy", Vector2.DOWN)
			elif float(e.fall) > 12.0: Audio.play("land")
		"splashed":
			fx.splash(m.pos)
			Audio.play("water_step")

# ------------------------------------------------------------------ Phase 4: ways, context and the shared host
## A way out walked into: at the way (the World authority's reach round it) with the stick pushing out through it (an
## edge's side, into a building's door, out of an interior's), the World authority takes it; a shut one says why. On
## the grid a door needs no hold: "up" is a real direction (plan §1.7).
func _check_portals(delta: float) -> void:
	transfer_cooldown = maxf(0.0, transfer_cooldown - delta)
	var c = Game.active()
	if transfer_cooldown > 0.0 or c == null or Game.room_rt == null or not player.motor.grounded: return
	var axis: Vector2 = player.last_axis
	if axis.length() < 0.5: return
	for p in Game.room_rt.def.get("portals", []):
		if not p.has("dir") or not Game.world.portal_near(c, p): continue
		if axis.normalized().dot(Vector2(float(p.dir[0]), float(p.dir[1]))) < 0.7: continue
		if Game.world.portal_state(c, p).get("hidden", false): continue
		request_portal(str(p.id), true)
		return

func request_portal(portal_id: String, crossing := false) -> void:
	WorldShared.request_portal(self, portal_id, crossing)

func _update_context() -> void:
	var ctx := WorldShared.context(Game.active(), player.motor.pos)
	WorldShared.mark_focus(ctx, object_views, npc_views, player_feet().x)
	if ctx.hash() != context.hash():
		context = ctx
		context_changed.emit(ctx)

## WorldShared's and MomentView's host: the effects layer, the player's feet in its units, the facing, the loot's
## layer, the middle of the view in world units and the feet on the screen.
func fx_layer() -> FxLayer: return effects
func feet() -> Vector2: return player_feet()
func facing() -> int: return player.facing
func loot_parent() -> Node2D: return loot_layer
func view_center() -> Vector2: return (camera.position + camera.offset) * TopdownRoom.ART
func screen_center() -> Vector2: return view_center()
func feet_on_screen() -> Vector2: return overlay.get_global_transform_with_canvas() * player_feet()

## Decision 39: the names, markers and plates over the world (the people's, the things', the ways', the foes') fade
## toward `to` (a staged scene's cut takes them away, and gives them back).
var labels_a := 1.0
func fade_labels(to: float, delta: float) -> void:
	labels_a = move_toward(labels_a, to, delta * 4.0)
	for v in npc_views.values() + object_views.values() + portal_views + label_views.values():
		if is_instance_valid(v): v.modulate.a = labels_a

## A moment's camera move (P6 `camera` layer) to a point in world units: ease there, hold, and ease back.
func hold_camera(target: Vector2, in_s: float, hold_s: float, out_s: float) -> void:
	camera_hold = {"target": target / TopdownRoom.ART, "t": 0.0, "in": in_s, "hold": hold_s, "out": out_s}

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

# ------------------------------------------------------------------ decision 38: the combat feel
## The camera's part of a blow of `weight` going along `dir`: a kick the way it went, and a shake for the heaviest
## (CombatFeel; none under Reduce motion or with Screen shake off).
func feel(weight: String, dir: Vector2) -> void:
	var w := CombatFeel.weight(weight)
	if float(w.get("kick_px", 0)) > 0.0: shake.kick(dir, float(w.kick_px), float(CombatFeel.cfg().get("kick_s", 0.12)))
	if float(w.get("shake_s", 0.0)) > 0.0: shake.add(float(w.shake_s), float(w.get("shake_px", 0)))

## CombatFx's hook for a blow that landed (a hit_landed payload): its impact mark where it struck, in the blow's
## direction, the element's colours and the blow's weight, and the camera's kick and shake; a blow on the player flashes
## the body.
func feel_hit(p: Dictionary) -> void:
	if str(p.get("type", "")) == "dot": return
	var at := Vector2(float(p.get("x", 0)), float(p.get("y", 0)))
	var from: Vector2 = at - player.motor.dir * 20.0
	var attacker = Game.room_rt.enemies.get(int(str(p.get("attacker", "")))) if Game.room_rt and str(p.get("attacker", "")).is_valid_int() else null
	if str(p.get("target_kind", "")) == "player":
		player.hurt_t = 0.0
		if attacker != null: from = attacker.plane
	elif str(p.get("attacker", "")) == Game.active_id: from = player.motor.pos
	var dir: Vector2 = (at - from).normalized() if at.distance_to(from) > 1.0 else player.motor.dir
	var weight := str(p.get("weight", "medium"))
	var floor_z := float(p.get("floor", 0.0))
	# The mark sits on the struck body at its chest (the hit's height over its floor), keyed with that body.
	var lift := clampf(float(p.get("alt", 0.0)) - floor_z, 0.0, 60.0) * 0.5
	tfx.impact(at, floor_z + lift, dir, weight, str(p.get("element", "none")))
	feel(weight, dir)

## The marks held while a state lasts: the guard's wall of qi while guarding, the charge gathering while a finisher is
## armed on Attack.
func _hold_marks() -> void:
	if not player.bound(): return
	var m: TopdownMotor = player.motor
	tfx.hold("guard", bool(Game.combat.timeline(player.actor_id).guard), m.pos, m.z, m.dir)
	tfx.hold("charge", str(player.aim.get("move", "")) == "finisher", m.pos, m.z, m.dir)

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

## A villager standing at `at` (world units, on the floor there) facing `row`, in the NPC's own outfit, sorted with the
## room: the rooms of the world place theirs (TopdownPlaces); this stands one anywhere, for the prototype and reviews.
func add_villager(npc_id: String, at: Vector2, row := "s") -> Node2D:
	var g: float = room.height_at(at)
	var o := {"type": "npc", "npc": npc_id, "at": [at.x, at.y], "alt": g if g < INF else 0.0, "row": row}
	var v := TopdownPlaces.Figure.new(room, o, TopdownPlaces.Person.new(o), null)
	sorted.add_child(v)
	return v

## The names over the world keep clear of each other and of the HUD's controls (WorldLabels, as world.gd places
## them), nearest the player first: the foes', and in the world the people's, the ways' and the things'.
func layout_labels() -> Dictionary:
	for uid in label_views.keys():
		if not is_instance_valid(label_views[uid]): label_views.erase(uid)
	return WorldLabels.place_views(WorldShared.label_views(self, player_feet(), Vector2.ONE), overlay.get_global_transform_with_canvas(), label_obstacles)

func _on_event(name: String, p: Dictionary) -> void:
	match name:
		"room_entered":
			# Phase 4: the next room on the grid (a room without a layout is world.gd's; main.gd swaps the views).
			if live and str(p.get("actor", "")) == Game.active_id and Game.room_rt != null and Game.room_rt.topdown != null:
				room = Game.room_rt.topdown
				_build_room()
				_place_player()
				_settle_camera()
		"enemy_spawned", "ally_spawned":
			var e: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", p.get("uid", 0)))) if Game.room_rt else null
			if e: _add_foe(e)
		"equipment_changed":
			if str(p.get("actor", "")) == player.actor_id: player.refresh_outfit()
		"attack_started":
			if str(p.get("actor", "")) == Game.active_id:
				var aim: Vector2 = p.get("aim", Vector2(int(p.get("facing", 1)), 0))
				var tech := str(p.get("technique", ""))
				var m: TopdownMotor = player.motor
				if tech != "":
					var at: Vector2 = p.get("at", m.pos)
					var at_z: float = room.height_at(at) if room.height_at(at) < INF else m.z
					var point := lifted(at, at_z)
					# A circle at a point plays where it lands (its form's feet anchor is the point, not the caster).
					var t := ContentDB.entry("techniques", tech)
					var on_point := TopdownAim.form_of(t) == "point"
					var reach := float(TopdownAim.cfg("point_radius", 48)) if on_point else TopdownAim.reach_of(t)
					combat_fx.cast(tech, point if on_point else player_feet(), int(p.facing), SpriteCache.element_color(str(p.get("element", "none"))),
						float(p.get("windup", -1.0)), point, aim, reach)
					# Decision 38: the form drawn on the ground plane in its direction, at the caster or where it lands (a form
					# on a foe lands on the point the aim locked: the foe's, or two thirds of the reach).
					tfx.form(t, m.pos, m.z, aim, at, at_z, float(p.get("windup", -1.0)), reach)
					Audio.play("technique")
				else:
					# Decision 38: the family's smear for this step, in its direction, its contact on the hit.
					var tl: Dictionary = Game.combat.timeline(player.actor_id)
					var move := "air" if tl.get("air_attack", false) else ("charged" if p.get("finisher", false) else \
						("dash" if player.dash_attack else "step_%d" % (int(p.get("combo", 0)) + 1)))
					tfx.smear(player.actor_id, str(tl.get("family", "fists")), move, aim, m.pos, m.z, float(p.get("windup", 0.0)), 1.0 + float(Game.active().stats.value("attack_speed")))
					Audio.play("swing")
			elif p.get("enemy", false):
				# A foe's wind-up: its tell over it (decision 38; its swipe comes with its blow, FoeView).
				var e: EnemyState = Game.room_rt.enemies.get(int(str(p.get("actor", "0")))) if Game.room_rt else null
				if e != null: tfx.mark("tell", e.plane, e.altitude + e.hover)
				Audio.play("tell")
		"attack_cancelled":
			if str(p.get("actor", "")) == Game.active_id: tfx.cancel(Game.active_id)
		"parried":
			# Decision 38: the parry's crossed strokes before the body, toward the foe it caught, and a heavy jolt.
			var pe: EnemyState = Game.room_rt.enemies.get(int(str(p.get("attacker", "0")))) if Game.room_rt else null
			var pd: Vector2 = (pe.plane - player.motor.pos).normalized() if pe != null and pe.plane.distance_to(player.motor.pos) > 1.0 else player.motor.dir
			tfx.mark("parry", player.motor.pos, player.motor.z, pd)
			feel("heavy", pd)
			WorldShared.play(self, name, p)
		"artifact_spirit_spoke":
			if str(p.get("actor", "")) == Game.active_id: effects.add("text", player_feet() + Vector2(0, -110), {"text": str(p.get("line", "")), "color": UiKit.PAPER, "size": 17, "dur": 3.0})
		_:
			WorldShared.play(self, name, p)

## World units on the ground plane at height z to the viewport's art px.
static func to_screen(p: Vector2, z: float) -> Vector2:
	return Vector2(p.x, p.y - z) / TopdownRoom.ART

func tile(name: String) -> Rect2:
	var r: Array = room.tileset.get("tiles", {}).get(name, [0, 0, 16, 16])
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))

## An atlas of the tile set (tiles, props, foes), loaded once from the file its manifest names.
func atlas(kind: String) -> Texture2D:
	if not _atlases.has(kind): _atlases[kind] = load(str(room.tileset.get("atlas", {}).get(kind, "")))
	return _atlases[kind]

## Draw the named tile at `at` on `ci`, its top `h` rows only (a face over water shows half).
func blit(ci: CanvasItem, name: String, at: Vector2, h := T) -> void:
	var src := tile(name)
	ci.draw_texture_rect_region(atlas("tiles"), Rect2(at, Vector2(T, h)), Rect2(src.position, Vector2(src.size.x, h)))

## Terrain v2: draw a layer ([tile, colour], TopdownTerrain) at `at`, its top `h` rows only.
func blit_layer(ci: CanvasItem, layer: Array, at: Vector2, h := T) -> void:
	var src := tile(str(layer[0]))
	ci.draw_texture_rect_region(atlas("tiles"), Rect2(at, Vector2(T, h)), Rect2(src.position, Vector2(src.size.x, h)), layer[1])

## A cell's top at `at`: its layers (Terrain v2: the macro tile or a path under grass, a decal, the sun and shade
## patches) and the light overlays for its level (art bible §5).
func blit_top(ci: CanvasItem, x: int, y: int, l: int, at: Vector2) -> void:
	for layer in terrain.top_layers(x, y, l): blit_layer(ci, layer, at)

## The prop shadows on row `row`'s floor at `level`, lifted by `dy` art px; with `cols`, only the pieces on those
## columns of cells (a floor chunk's).
func blit_shadows(ci: CanvasItem, row: int, level: int, dy: float, cols := Vector2i(-9999, 9999)) -> void:
	for piece in terrain.shadow_pieces(row, level):
		var dest: Rect2 = piece[0]
		var cx := floori(dest.position.x / T)
		if cx < cols.x or cx >= cols.y: continue
		ci.draw_texture_rect_region(atlas("props"), Rect2(dest.position + Vector2(0, dy), dest.size), piece[1])

## A node in the sorted layer sits at its key and draws back to screen rows by `lift` = key.
class Sorted extends Node2D:
	var world
	var rects: Array = []    ## what it covers on screen, for the silhouette test
	func _init(w) -> void:
		world = w
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	func key(k: float) -> void:
		position = Vector2(0, k)

## The water, half a level under the ground, one chunk of cells: each cell's layers (Terrain v2: the water pattern,
## the depth, its shore case, corner foam, ripples at the pilings) in the frame of the 250 ms clock (art bible §6–§7).
## A chunk off screen skips its redraws until it comes into view.
class WaterView extends Node2D:
	var world
	var frame := -1
	var area: Rect2
	var cells: Array = []   ## [screen position, [its layers in frames 0-3]]
	func _init(w, chunk: Rect2i) -> void:
		world = w
		var r: TopdownRoom = w.room
		for y in range(chunk.position.y, chunk.end.y):
			for x in range(chunk.position.x, chunk.end.x):
				if r.levels[y * r.w + x] == TopdownRoom.WATER: cells.append([Vector2(x * T, y * T - TopdownRoom.WATER_Z / TopdownRoom.ART), w.terrain.water_layers(x, y)])
		area = Rect2(Vector2(chunk.position) * T, Vector2(chunk.size) * T + Vector2(0, T))
	func _process(_d: float) -> void:
		var f := int(Time.get_ticks_msec() / 250) % 4
		if f != frame and _in_view():
			frame = f
			queue_redraw()
	func _in_view() -> bool:
		var vs := Vector2(world.viewport.size)
		return area.intersects(Rect2(world.camera.position - vs * 0.5, vs).grow(T))
	func _draw() -> void:
		for c in cells:
			for layer in c[1][maxi(0, frame)]: world.blit_layer(self, layer, c[0])

## Ground-level tops with their light, the bank faces over water, and the ground props' floor shadows, one chunk of
## cells: under everything that sorts.
class FloorView extends Node2D:
	var world
	var chunk: Rect2i
	func _init(w, c: Rect2i) -> void:
		world = w
		chunk = c
	func _draw() -> void:
		var r: TopdownRoom = world.room
		var tr: TopdownTerrain = world.terrain
		for y in range(chunk.position.y, chunk.end.y):
			for x in range(chunk.position.x, chunk.end.x):
				if r.levels[y * r.w + x] != 0 or not r.stair_at(x, y).is_empty(): continue
				world.blit_top(self, x, y, 0, Vector2(x * T, y * T))
				if tr.edge_level(x, y + 1) == TopdownRoom.WATER:
					for layer in tr.face_layers(x, y, 0, 0, TopdownRoom.WATER): world.blit_layer(self, layer, Vector2(x * T, (y + 1) * T), T * 0.5)
		for y in range(chunk.position.y, chunk.end.y): world.blit_shadows(self, y, 0, 0.0, Vector2i(chunk.position.x, chunk.end.x))

## One row of raised cells: their tops at their height with their light, their south faces down to the level in front
## (the face's ends lit or shaded where it turns a corner), and the floor shadows of the props on them. Its key is the
## row's south edge.
class StripView extends Sorted:
	var row := 0
	var levels := {}
	func _init(w, y: int) -> void:
		super(w)
		row = y
		key((y + 1) * T)
		var r: TopdownRoom = w.room
		for x in r.w:
			var l := r.levels[y * r.w + x]
			if l <= 0 or not r.stair_at(x, y).is_empty(): continue
			levels[l] = true
			var south := mini(l, w.terrain.edge_level(x, y + 1))
			rects.append(Rect2(x * T, (y - l) * T, T, T * (1 + l - maxi(south, -1)) - (T * 0.5 if south < 0 else 0.0)))
	func _draw() -> void:
		var r: TopdownRoom = world.room
		var tr: TopdownTerrain = world.terrain
		var lift := position.y
		for x in r.w:
			var l := r.levels[row * r.w + x]
			if l <= 0 or not r.stair_at(x, row).is_empty(): continue
			world.blit_top(self, x, row, l, Vector2(x * T, (row - l) * T - lift))
			var south := mini(l, tr.edge_level(x, row + 1))
			for k in range(l - south):
				var water: bool = south + k + 1 == 0
				var at := Vector2(x * T, (row + 1 - l + k) * T - lift)
				var h := T * 0.5 if water else T
				for layer in tr.face_layers(x, row, l, k, south): world.blit_layer(self, layer, at, h)
		for l in levels: world.blit_shadows(self, row, l, -l * T - lift)

## A flight of stairs, drawn step by step from its top edge to its foot, between a lit west cheek and a shaded east
## one; its key is the flight's south edge.
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
		var lift := position.y
		var y := rect.position.y
		while y < rect.end.y:
			for x in int(rect.size.x / T): world.blit(self, "stairs", Vector2(rect.position.x + x * T, y - lift), minf(8.0, rect.end.y - y))
			y += 8.0
		y = rect.position.y
		while y < rect.end.y:
			world.blit(self, "cheek_w", Vector2(rect.position.x, y - lift), minf(T, rect.end.y - y))
			world.blit(self, "cheek_e", Vector2(rect.end.x - T, y - lift), minf(T, rect.end.y - y))
			y += T

## A prop sprite from the atlas; its footprint's south-west corner sits on the floor it stands on, its key is the
## footprint's south edge (a little past the row's own, so it draws over the floor it stands on). An animated prop
## (the manifest's `frames`, side by side from its rect) plays on its own clock, each prop at its own phase.
class PropView extends Sorted:
	var src: Rect2
	var at: Vector2
	var frames := 1
	var frame_ms := 0
	var phase := 0
	var frame := 0
	func _init(w, p: Dictionary) -> void:
		super(w)
		var art: Dictionary = p.art
		var rr: Array = art.get("rect", [0, 0, 16, 16])
		var origin: Array = art.get("origin", [0, 16])
		src = Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3]))
		var cell: Vector2i = p.cell
		rects.append(Rect2())
		place_at(Vector2(cell.x * T, (cell.y + (p.size as Vector2i).y) * T), int(p.level), Vector2(float(origin[0]), float(origin[1])))
		frames = int(art.get("frames", 1))
		frame_ms = int(art.get("frame_ms", 0))
		phase = (cell.x * 3 + cell.y * 5) % maxi(1, frames)
	## Stand the footprint's south-west corner at `sw` (art px) on a floor at `level` (a staged scene moves a prop so: a
	## boat passing on the river).
	func place_at(sw: Vector2, level: int, origin: Vector2) -> void:
		var ground := TopdownRoom.WATER_Z / TopdownRoom.ART * -1.0 if level < 0 else -level * T
		sw = sw.round()
		at = Vector2(sw.x - origin.x, sw.y + ground - origin.y)
		rects[0] = Rect2(at, src.size)
		key(sw.y + 0.5)
		queue_redraw()
	func _ready() -> void:
		set_process(frames > 1 and frame_ms > 0)
	func _process(_d: float) -> void:
		var f := (int(Time.get_ticks_msec() / frame_ms) + phase) % frames
		if f != frame:
			frame = f
			queue_redraw()
	func _draw() -> void:
		draw_texture_rect_region(world.atlas("props"), Rect2(at - position, src.size), Rect2(src.position + Vector2(src.size.x * frame, 0), src.size))

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
		TopdownWorld.draw_blob(self, 0.0, feet.y - position.y, roundf(8.0 * k), 0.55 * k)

## A body's blob shadow on the floor at (x, y): `rx` wide each way, two stepped layers in the cast shadows' colour
## (decision 40, TopdownLight.BLOB): its rim and, over it, its core, at fractions of `a`.
static func draw_blob(ci: CanvasItem, x: float, y: float, rx: float, a: float) -> void:
	ci.draw_rect(Rect2(x - rx, y - 1, rx * 2, 3), Color(TopdownLight.BLOB, a * TopdownLight.BLOB_RIM))
	ci.draw_rect(Rect2(x - rx + 2, y - 2, rx * 2 - 4, 5), Color(TopdownLight.BLOB, a * TopdownLight.BLOB_CORE))

## Splashes, a few pixels each (the dust of landings, dashes and skids is TopdownFx's, decision 38).
class FxView extends Sorted:
	var items: Array = []
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
			var col := Color(0.56, 0.8, 0.8, 0.9 * (1.0 - t))
			var spread := roundf((3.0 + 9.0 * t) * float(it.size))
			for s in [-1, 1]:
				draw_rect(Rect2(a.x + s * spread - 1, a.y - 1 - roundf(3.0 * t), 2, 2), col)
				draw_rect(Rect2(a.x + s * roundf(spread * 0.5) - 1, a.y - 2 - roundf(5.0 * t), 1, 1), col)
			draw_arc(a, spread, 0, TAU, 12, col, 1.0)

## The body drawn flat in jade over whatever covers it (the side-view game's occlusion outline, redone for the grid).
class Silhouette extends Node2D:
	var world
	func _init(w) -> void:
		world = w
		var mat := ShaderMaterial.new()
		mat.shader = Shader.new()
		mat.shader.code = "shader_type canvas_item;\nvoid fragment() { COLOR = vec4(0.4, 0.84, 0.74, texture(TEXTURE, UV).a); }"
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

## One foe on the grid (Phase 3: art/topdown/foes.png), sorted with the room like the body, its shadow on the floor
## under it, a flash when struck and a fade in death. It turns to eight facings (five drawn, SW, W and NW mirrored):
## where it walks, else where it aims in a fight, keeping its facing until another is 12 degrees nearer. Each action
## plays at its own rate from the manifest; a strike, a flinch and a death play once and hold their last frame.
## Phase 4: a companion, a spirit animal, or a foe the sheet has no rows for is drawn by its stand-in
## (TopdownPlaces.stand_in: a companion in the top-down style in its own outfit, an animal or a foe as the side view's own
## figure at half size), placed, sorted and shadowed here the same way.
class FoeView extends Sorted:
	const FACINGS := {"e": 0.0, "se": 45.0, "s": 90.0, "sw": 135.0, "w": 180.0, "nw": -135.0, "n": -90.0, "ne": -45.0}
	var uid := 0
	var acts: Dictionary = {}
	var mirror: Dictionary = {}
	var cell := Vector2(48, 40)
	var foot := Vector2(24, 27)
	var shadow_rx := 8.0
	var feet := Vector2.ZERO
	var ground_y := 0.0
	var src := Rect2()
	var facing := "s"
	var flip := false
	var tint := Color.WHITE
	var t := 0.0
	var last := ""
	var art: Node2D = null   ## the stand-in's drawing (no rows in the foe sheet), its feet at its origin
	# Decision 38: the struck body flashes white, then tinted; a knockback hops it over the floor and leaves a skid.
	var white := 0.0
	var kb0 := 0.0
	var hop := 0.0
	var state := ""
	func _init(w, e: EnemyState) -> void:
		super(w)
		uid = e.uid
		add_child(FoeShadow.new(self))   # under the sprite, outside its flash
		var sheet: Dictionary = w.room.tileset.get("foes", {})
		if e.team == "ally" or not (sheet.get("species", {}) as Dictionary).has(e.def_id):
			art = TopdownPlaces.stand_in(e)
			add_child(art)
			shadow_rx = clampf(roundf(e.half_width() * 0.5), 5.0, 16.0)
			return
		var sp: Dictionary = sheet.get("species", {})[e.def_id]
		acts = sp.get("actions", {})
		mirror = sheet.get("mirror", {})
		var c: Array = sheet.get("cell", [48, 40])
		var f: Array = sheet.get("foot", [24, 27])
		cell = Vector2(float(c[0]), float(c[1]))
		foot = Vector2(float(f[0]), float(f[1]))
		shadow_rx = float(sp.get("shadow", [8, 3])[0])
		facing = TopdownMotor.nearest_row(Vector2(e.facing, 1.0), "s", FACINGS)
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
		visible = not e.hidden or (e.ai.state == "windup" and e.team != "ally")
		if art != null:
			art.position = Vector2(0, feet.y - position.y)
			TopdownPlaces.pose(art, e)
			tint = Color(1, 1, 1, clampf(1.0 - e.dead_time / 1.4, 0.0, 1.0)) if not e.alive else Color.WHITE
			queue_redraw()
			get_child(0).queue_redraw()
			return
		var fight := str(e.ai.state) in ["aggro", "windup", "attack", "recover"]
		var want := e.velocity if e.velocity.length() > 1.0 else (e.aim if fight else Vector2.ZERO)
		if e.alive and want != Vector2.ZERO: facing = TopdownMotor.nearest_row(want, facing, FACINGS, 12.0)
		var act := str(e.action)
		if not e.alive: act = "death"
		elif e.ai.state == "stagger" or (e.flash > 0.0 and act in ["idle", "walk"]): act = "hurt"
		if not acts.has(act): act = "idle"
		if act != last:
			last = act
			t = 0.0
		t += delta
		var a: Dictionary = acts.get(act, {})
		flip = mirror.has(facing)
		var list: Array = a.get("frames", {}).get(str(mirror.get(facing, facing)), [[0, 0]])
		var i := int(t * float(a.get("fps", 6)))
		var at: Array = list[i % list.size() if a.get("loop", true) else mini(i, list.size() - 1)]
		src = Rect2(float(at[0]), float(at[1]), cell.x, cell.y)
		var fl: Dictionary = CombatFeel.cfg().get("flash", {})
		white = 1.0 if e.alive and e.flash > 0.0 and 0.12 - e.flash < float(fl.get("white_s", 0.05)) else 0.0
		tint = Color(1, 1, 1, clampf(1.0 - e.dead_time / 1.4, 0.0, 1.0)) if not e.alive else (Color(str(fl.get("tint", "#ffb4a0"))) if e.flash > 0.0 else Color.WHITE)
		# The knockback's hop: up and down over the push, by its strength; a strong one skids dust.
		var kb := absf(e.knockback)
		if kb > kb0 + 0.5:
			kb0 = kb
			var kn: Dictionary = CombatFeel.cfg().get("knock", {})
			if kb >= float(kn.get("skid_from", 40)): world.tfx.dust("skid", e.plane, e.altitude, e.knock_dir)
		if kb <= 0.5: kb0 = 0.0
		hop = 0.0
		if kb0 > 0.0:
			var hmax := minf(float(CombatFeel.cfg().get("knock", {}).get("hop_max_px", 10)), kb0 * float(CombatFeel.weight("heavy").get("hop", 0.08)))
			hop = roundf(hmax * sin(PI * clampf(1.0 - kb / kb0, 0.0, 1.0)))
		# A foe's blow: its swipe the moment its wind-up turns into the strike.
		var st := str(e.ai.get("state", ""))
		if st == "attack" and state == "windup" and e.team == "enemy": world.tfx.mark("swipe", e.plane, e.altitude + e.hover, e.aim_dir())
		state = st
		material = TopdownFx.white_material() if white > 0.0 else null
		queue_redraw()
		get_child(0).queue_redraw()
	func _draw() -> void:
		if art != null: return   # the stand-in draws itself; its shadow is the FoeShadow child
		draw_set_transform(Vector2(0, feet.y - position.y - hop), 0.0, Vector2(-1, 1) if flip else Vector2.ONE)
		draw_texture_rect_region(world.atlas("foes"), Rect2(-foot, cell), src, tint)
		draw_set_transform(Vector2.ZERO)

## A foe's blob shadow on the floor, drawn behind its figure and outside the figure's hurt flash.
class FoeShadow extends Node2D:
	var foe
	func _init(f) -> void:
		foe = f
		show_behind_parent = true
	func _draw() -> void:
		TopdownWorld.draw_blob(self, 0.0, foe.ground_y - foe.position.y, foe.shadow_rx, 0.45 * foe.tint.a)

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
