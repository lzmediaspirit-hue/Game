extends Node2D
## World presentation (S17/S36). Loads one room at a time from the World
## authority's RoomRuntime, draws terrain, scenery, objects, portals, NPCs,
## monsters, allies and loot, follows the player with the camera and plays the
## effects that events call for. It sends intents and never changes game state.
##
## Legacy mode (no room id): loads the v0.13 authored street (data/world.json) for
## the movement/geometry regression checks in tests/engine_tests.gd.

const Player = preload("res://scripts/player.gd")
const Terrain = preload("res://scripts/terrain.gd")
const Arrow = preload("res://scripts/arrow.gd")
const OcclusionOutline = preload("res://scripts/occlusion_outline.gd")
const AvatarScript = preload("res://scripts/avatar.gd")
const MAP_REVISION = 7

var room_mode := false
var geometry := ZoneGeometry.new()
var surfaces: Array[WalkSurface] = []
var terrain_visuals: Array = []
var dynamic_terrain: Array = []     # S43: mover, crumble and cracked surfaces, redrawn every frame
var props: Array[Node2D] = []
var map_bounds: Rect2
var map_data: Dictionary = {}
var room_def: Dictionary = {}
var player: Node2D
var illusion_view: Node2D = null     # S48 Phantom Double: the player's illusion, a pale copy of the avatar
var player_shadow: Node2D
var player_outline: Node2D
var camera: Camera2D
var room_layer: Node2D
var fx: FxLayer
var outfit: Dictionary
var save_slot_index := -1
var skill_page := 0
var save_timer := 0.0
var last_safe: Dictionary = {}
var map_theme := ""
var map_seed := 1
var enemy_views: Dictionary = {}
var object_views: Dictionary = {}
var npc_views: Dictionary = {}
var portal_views: Array = []
var context: Dictionary = {}
var up_hold := 0.0
var shake := 0.0                    # seconds of camera shake left; add_shake is its one writer (P6 camera rig)
var shake_k := 0.0                  # px of shake amplitude per second left
var camera_hold := {}               # a moment's camera move: {target, t, in, hold, out}
var transfer_cooldown := 0.0
var travel := RoomTravel.new()
## P5a (G4): the screen rects of the HUD's controls and panels, which hud.gd writes each frame; no world label sits
## under one (WorldLabels).
var label_obstacles: Array = []

signal room_changed(room_id: String)
signal context_changed(ctx: Dictionary)

func _ready() -> void:
	room_layer = Node2D.new()
	room_layer.name = "Room"
	add_child(room_layer)
	camera = Camera2D.new()
	add_child(camera)
	fx = FxLayer.new()
	add_child(fx)
	if room_mode:
		GameEvents.event.connect(_on_event)
		player = Player.new()
		player.world = self
		player.actor_id = Game.active_id
		player.outfit = InventoryAuthority.outfit_for(Game.active())
		_build_room()
		add_child(player)
		_attach_player_helpers()
		_place_player()
	else:
		_legacy_ready()

func _exit_tree() -> void:
	if GameEvents.event.is_connected(_on_event): GameEvents.event.disconnect(_on_event)

# ------------------------------------------------------------------ room building
func _build_room() -> void:
	for child in room_layer.get_children():
		child.queue_free()
	terrain_visuals.clear()
	props.clear()
	enemy_views.clear()
	object_views.clear()
	npc_views.clear()
	portal_views.clear()
	var rt: RoomRuntime = Game.room_rt
	room_def = rt.def
	map_data = {"background": str(room_def.get("backdrop", "valley_day"))}
	geometry = rt.geometry
	map_bounds = geometry.bounds
	surfaces = geometry.surfaces
	var material := str(room_def.get("ground", {}).get("material", "earth"))
	var ground_tint := Color(str(room_def.get("ground", {}).get("tint", "#ffffff")))
	# Interior back wall and water areas.
	if room_def.has("wall"):
		var w: Dictionary = room_def.wall
		var wall = DecorView.make_area("wall", Rect2(-40, float(w.get("top", 150)), map_bounds.size.x + 80, float(w.get("bottom", 640)) - float(w.get("top", 150))), str(w.get("tile", "wall_wood")), -2100)
		room_layer.add_child(wall)
	for area in room_def.get("areas", []):
		var r: Array = area.rect
		var kind := str(area.get("kind", "water"))
		var tile := "shallow_water" if kind == "shallows" else "water"
		var rect := Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
		if kind in ["river", "water", "shallows"]:
			room_layer.add_child(DecorView.make_area("water", rect, tile, -1990 if kind != "river" else -2000))
	for s in surfaces:
		var terrain := Terrain.new()
		terrain.surface = s
		terrain.generated = true
		terrain.ground_material = material
		terrain.tint = ground_tint
		for spec in room_def.get("surfaces", []):
			if spec.id == s.id:
				terrain.art = str(spec.get("art", ""))
				if spec.has("material"): terrain.ground_material = str(spec.material)
		if s.is_block:
			for b in room_def.get("blocks", []):
				if str(b.id) == s.id: terrain.art = str(b.get("kind", "crate"))
		if s.stratum == "ground" and s.base > 0 and terrain.ground_material in ["earth", "moss"]: terrain.ground_material = "stone"
		room_layer.add_child(terrain)
		terrain_visuals.append(terrain)
	# S43 climbables: ladders, ropes, vines and chains, drawn from the foot to the top step.
	for cdef in room_def.get("climbables", []):
		room_layer.add_child(ClimbableView.make(cdef))
	# S43 volumes that have a look of their own, and the surfaces that move, crumble or break.
	for v in geometry.volumes:
		if str(v.kind) in ["updraft", "wind", "current", "rising_water", "bounce", "ice", "low_gravity"]: room_layer.add_child(VolumeView.make(geometry, v))
	dynamic_terrain.clear()
	for tv in terrain_visuals:
		var ts: WalkSurface = tv.surface
		if ts.moving or ts.cracked or not geometry.crumble_volume(ts.id).is_empty(): dynamic_terrain.append(tv)
	for spec in room_def.get("scenery", []):
		if spec.get("art", "props") == "none": continue
		var prop := SceneryProp.new()
		prop.spec = spec
		room_layer.add_child(prop)
		props.append(prop)
	for d in room_def.get("decor", []):
		room_layer.add_child(DecorView.make_prop(d))
	for o in room_def.get("objects", []):
		if o.type == "npc":
			var nv = NpcView.new()
			nv.setup(o)
			room_layer.add_child(nv)
			npc_views[str(o.id)] = nv
		elif o.type != "decor":
			var ov = ObjectView.new()
			ov.setup(o)
			room_layer.add_child(ov)
			object_views[str(o.id)] = ov
	for p in room_def.get("portals", []):
		var pv = PortalView.new()
		pv.setup(p, room_def)
		room_layer.add_child(pv)
		portal_views.append(pv)
	# Hazards, and the heavenly tribulation's rings and bolts (S48), which can fall in any room.
	var hv := HazardView.new()
	hv.world = self
	room_layer.add_child(hv)
	for uid in rt.enemies:
		_add_enemy_view(rt.enemies[uid])
	for l in rt.loot:
		var lv = LootView.new()
		lv.setup(l)
		room_layer.add_child(lv)
	update_sorting()
	room_changed.emit(rt.room_id)

func _attach_player_helpers() -> void:
	if player_shadow == null:
		player_shadow = preload("res://scripts/shadow.gd").new()
		player_shadow.player = player
		player_shadow.world = self
		add_child(player_shadow)
	if player_outline == null:
		player_outline = OcclusionOutline.new()
		player_outline.source = player
		add_child(player_outline)

func _place_player() -> void:
	var c = Game.active()
	var p := Vector2(float(c.position.get("x", 200)), float(c.position.get("y", 800)))
	var s: WalkSurface = geometry.index.get(str(c.position.get("surface", "")))
	if s == null or not s.contains(p):
		s = null
		for cand in surfaces:
			if cand.stratum == "ground" and cand.contains(p):
				s = cand
				break
		if s == null: s = surfaces[0]
	player.state.zone_id = Game.room_rt.room_id
	player.surface = s
	player.plane = p
	player.altitude = s.height_at(p)
	player.vertical_speed = 0.0
	player.velocity = Vector2.ZERO
	player.state.jumps_used = 0
	player.facing = int(c.position.get("facing", 1))
	player.authority = LocalAuthority.new(player.state, geometry)
	player.authority.actor_id = player.actor_id
	Game.bind_movement(Game.active_id, player.state)
	player.sync_visual()
	cam_follow_y = player.position.y
	camera.position = camera_target()
	record_safe_position()
	transfer_cooldown = 0.4

func _add_enemy_view(e: EnemyState) -> void:
	if enemy_views.has(e.uid) and is_instance_valid(enemy_views[e.uid]): return
	var v = EnemyView.new()
	v.setup(e)
	room_layer.add_child(v)
	enemy_views[e.uid] = v

# ------------------------------------------------------------------ simulation drive
func _physics_process(delta: float) -> void:
	if not room_mode or Game.paused: return
	player.physics_step(delta)
	Game.tick(delta)
	_check_portals(delta)

func _check_portals(delta: float) -> void:
	transfer_cooldown = maxf(0.0, transfer_cooldown - delta)
	if transfer_cooldown > 0.0 or player.surface == null: return
	var axis: Vector2 = player.last_axis
	var w := map_bounds.end.x
	for p in room_def.get("portals", []):
		var at: Array = p.get("at", [0, 0])
		var pos := Vector2(float(at[0]), float(at[1]))
		var near := absf(player.plane.x - pos.x) <= 60.0 and absf(player.plane.y - pos.y) <= 50.0
		if not near: continue
		var type := str(p.get("type", "edge"))
		var outward := 1.0 if pos.x > w * 0.5 else -1.0
		var at_edge := pos.x < 100.0 or pos.x > w - 100.0
		var walking_out = at_edge and type in ["edge", "gate", "sealed"] and not p.get("press_up", false) and axis.x * outward > 0.5
		# S43 controls: a plain press up walks into depth, so a portal needs a 0.3 s hold with little sideways input.
		var pressing_up := axis.y < -0.6 and absf(axis.x) < 0.3
		if pressing_up: up_hold += delta
		if walking_out or (pressing_up and up_hold >= 0.3):
			up_hold = 0.0
			request_portal(str(p.id), walking_out)
			return
	if axis.y >= -0.6 or absf(axis.x) >= 0.3: up_hold = 0.0

func request_portal(portal_id: String, crossing := false) -> void:
	if transfer_cooldown > 0.0: return
	transfer_cooldown = 0.6
	var r := Game.submit({"type": "use_portal", "portal": portal_id, "crossing": crossing})
	if not r.ok and r.has("text"):
		fx.add("text", player.position + Vector2(0, -130), {"text": str(r.text), "color": UiKit.MIST, "size": 18, "dur": 1.6})

func camera_target() -> Vector2:
	if not room_mode:
		var target := player.position + Vector2(player.velocity.x * 0.25, -150)
		target.x = clampf(target.x, 640, map_bounds.end.x - 640)
		target.y = clampf(target.y, 180, 730)
		return target
	# S43 rule 13: the room's camera {bounds [x0, y0, x1, y1], look_ahead}. It leads by a quarter of the
	# velocity and follows the surface underfoot rather than the jump arc (no bobbing); falls of more than a
	# tier are followed; standing still near a high open edge looks down 60.
	var cam: Dictionary = room_def.get("camera", {})
	var look := float(cam.get("look_ahead", ContentDB.movement("camera.look_ahead", 0.25)))
	var target2 := Vector2(player.position.x + player.velocity.x * look, cam_follow_y - 110.0 + cam_look_down)
	var w := map_bounds.size.x
	var bounds: Array = cam.get("bounds", [])
	if bounds.size() == 4: target2.x = clampf(target2.x, float(bounds[0]), float(bounds[2]))
	elif w <= 1280.0: target2.x = w * 0.5
	else: target2.x = clampf(target2.x, 640, w - 640)
	var y_min := float(bounds[1]) if bounds.size() == 4 else float(cam.get("y_min", ContentDB.movement("camera.y_min", 180)))
	var y_max := float(bounds[3]) if bounds.size() == 4 else float(cam.get("y_max", ContentDB.movement("camera.y_max", 600)))
	target2.y = clampf(target2.y, y_min, y_max)
	return target2

var cam_follow_y := 0.0      # the height the camera follows: the support underfoot, not the jump arc
var cam_look_down := 0.0
var cam_still := 0.0
func _update_camera_follow(delta: float) -> void:
	var st: ActorState = player.state
	if st.surface != null or st.flying or not st.climbing.is_empty():
		cam_follow_y = player.position.y
	elif player.position.y > cam_follow_y + 100.0:
		cam_follow_y = player.position.y - 100.0   # a fall of more than one tier: follow it down
	# Look down over a drop of more than 150 after standing still 0.5 s near an open edge.
	var s: WalkSurface = st.surface
	if s != null and player.velocity.length() < 5.0: cam_still += delta
	else: cam_still = 0.0
	var peer := cam_still >= 0.5 and s != null and s.base > 150.0 and geometry.open_edge_distance(s, player.plane) < 40.0
	cam_look_down = move_toward(cam_look_down, 60.0 if peer else 0.0, delta * 150.0)

func _process(delta: float) -> void:
	if not room_mode:
		_legacy_process(delta)
		return
	if player == null: return
	for tv in dynamic_terrain: tv.queue_redraw()
	_update_camera_follow(delta)
	var ct := camera_target()
	if not camera_hold.is_empty():
		var h := camera_hold
		h.t = float(h.t) + delta
		var ends := float(h.in) + float(h.hold) + float(h.out)
		ct = ct.lerp(h.target, smoothstep(0.0, float(h.in), h.t) * (1.0 - smoothstep(ends - float(h.out), ends, h.t)))
		if float(h.t) >= ends: camera_hold = {}
	# Across at the old pace; up and down it settles in about 0.4 s after a landing.
	camera.position = Vector2(lerpf(camera.position.x, ct.x, 1.0 - exp(-delta * 6.0)), lerpf(camera.position.y, ct.y, 1.0 - exp(-delta * 7.5)))
	shake = maxf(0.0, shake - delta)
	camera.offset = Vector2(randf_range(-1, 1), randf_range(-0.75, 0.75)) * shake_k * shake if shake > 0.0 else Vector2.ZERO
	camera.position = camera.position.snapped(Vector2(2, 2))
	_track_safe(delta)
	update_occlusion()
	_update_context()
	layout_labels()

## P5a (review G4): every name over the world is placed so none stacks on another or sits under a HUD control. The
## views keep their label boxes at their own offsets by kind; WorldLabels places them on screen in whole rows.
func layout_labels() -> Dictionary:
	if not is_inside_tree(): return {}
	var views: Array = []
	var px: float = player.position.x if player else 0.0
	for uid in enemy_views:
		var v = enemy_views[uid]
		if is_instance_valid(v): views.append({"id": "e%d" % int(uid), "view": v, "kind": v.label_kind, "near": absf(v.position.x - px)})
	for id in npc_views:
		var nv = npc_views[id]
		views.append({"id": "n" + str(id), "view": nv, "kind": "focus" if nv.focus else "npc", "near": absf(nv.position.x - px)})
	for i in portal_views.size(): views.append({"id": "p%d" % i, "view": portal_views[i], "kind": "place", "near": absf(portal_views[i].position.x - px)})
	for id in object_views: views.append({"id": "o" + str(id), "view": object_views[id], "kind": "place", "near": absf(object_views[id].position.x - px)})
	return WorldLabels.place_views(views, get_viewport().get_canvas_transform(), label_obstacles)

func _update_context() -> void:
	var c = Game.active()
	var ctx: Dictionary = Game.world.query_context(c) if c else {}
	# S43: a ladder, rope or vine in reach offers "Climb".
	if ctx.is_empty() and player and player.surface != null and player.state.climbing.is_empty():
		var near_c: Dictionary = geometry.climbable_near(player.plane, player.altitude, 48.0)
		if not near_c.is_empty(): ctx = {"type": "climbable", "climbable": str(near_c.id), "label": Tx.t("hud.climb")}
	# S49: a foe who has yielded to you waits for your judgement.
	if ctx.is_empty() and player and Game.room_rt:
		for e in Game.room_rt.living_enemies():
			if e.ai.get("surrendered", false) and str(e.ai.get("judge", "")) == Game.active_id and e.plane.distance_to(player.plane) < 160.0:
				ctx = {"type": "mercy", "enemy": e.uid, "def": e.def_id, "label": Tx.t("hud.judge")}
				break
	for id in object_views: object_views[id].focus = ctx.get("object", "") == id
	for id in npc_views:
		npc_views[id].focus = ctx.get("object", "") == id
		if ctx.get("object", "") == id: npc_views[id].face(player.position.x)
	if ctx.hash() != context.hash():
		context = ctx
		context_changed.emit(ctx)

## S49 Fame: from Noted, the nearest townsfolk know your name when you walk in.
func _fame_greeting() -> void:
	var c = Game.active()
	if c == null or Game.room_rt == null or str(Game.room_rt.def.get("type", "")) != "town": return
	var tier := str(Game.relations.fame_tier(c).get("id", "unknown"))
	if tier in ["", "unknown"]: return
	var best = null
	var best_d := 900.0
	for id in npc_views:
		var nv = npc_views[id]
		var dd: float = nv.position.distance_to(player.position)
		if nv.visible and dd < best_d:
			best = nv
			best_d = dd
	if best == null: return
	best.bark = Tx.t("world_view.fame_greet_" + tier) % c.name
	best.bark_time = 4.0

## The camera rig's one writer of the shake (P6): the longer shake and the stronger amplitude win. `amp` is the starting
## amplitude in px (default s × shake_amp_per_s: 4 px at 0.25 s); none with Screen shake off or Reduce motion on.
func add_shake(s: float, amp := -1.0) -> void:
	var a := MomentRules.shake_amp(s, amp)
	if a <= 0.0 or s <= 0.0: return
	shake_k = maxf(shake_k if shake > 0.0 else 0.0, a / s)
	shake = maxf(shake, s)

## P6e a technique cast at its tier (docs/moments_design.md §5): a ring at the feet (from tier 2), a wash of its
## element over the screen (from tier 3, under the flash limiter), and its shape, drawn at the reach it really strikes
## (§5.4): a slash, a wave along the reach, a ring at it with echo rings inside, a rain of streaks, a pillar on the foe,
## or a ring and motes round the caster. A bolt is drawn by its projectile.
var cast_shake: Dictionary = {}   # "tech:<id>" -> true until the cast's first hit shakes (tiers 3 and up)
func _cast(tech: String, facing: int, col: Color) -> void:
	var t := ContentDB.entry("techniques", tech)
	var n := MomentRules.tier_numbers("tech:" + tech)
	var tier := int(t.get("vfx", {}).get("tier", 1))
	var reach := float(t.hitbox.x[1])
	var at := player.position
	if float(n.shake_s) > 0.0: cast_shake["tech:" + tech] = true
	if float(n.cast_ring_r) > 0.0: fx.add("ring", at, {"color": col, "radius": float(n.cast_ring_r), "dur": 0.3})
	if float(n.tint_alpha) > 0.0: fx.add("tint", at, {"color": Color(col, float(n.tint_alpha)), "dur": 0.4})
	match str(t.get("vfx", {}).get("shape", "strike")):
		"strike": fx.add("slash", at + Vector2(facing * 40, -50), {"color": col, "facing": facing, "radius": 46.0 + 6.0 * (tier - 1), "dur": 0.3})
		"wave": fx.add("talisman_wave", at + Vector2(0, -50), {"color": col, "facing": facing, "radius": reach, "size": 20 + 2 * tier, "dur": 0.4})
		"ring":
			for i in int(n.echoes) + 1:
				fx.add("wave", at, {"color": col, "radius": reach * [1.0, 0.7, 0.4, 0.55][i], "size": n.wave_width, "dur": 0.45, "delay": 0.08 * i})
		"rain": fx.add("rain", at + Vector2(facing * reach * 0.5, 0), {"color": col, "radius": reach * 0.5, "height": 240.0, "dur": 0.5,
			"count": MomentRules.particle_count(3 * int(t.get("hits", 1)) + 2 * tier)})
		"pillar": fx.add("pillar", _foe_in_reach(at, facing, reach), {"color": col, "radius": 12.0 + 4.0 * tier, "height": 300.0, "dur": 0.35})
		"domain":
			fx.add("ring", at, {"color": col, "radius": float(t.get("heal_radius", reach)), "dur": 0.6})
			fx.add("motes", at + Vector2(0, -10), {"color": col, "dur": 0.8})

## Where a single-target cast lands: the nearest foe in front within reach, else halfway along it.
func _foe_in_reach(at: Vector2, facing: int, reach: float) -> Vector2:
	var best := at + Vector2(facing * reach * 0.5, 0)
	var best_d := reach
	for e in Game.room_rt.living_enemies():
		var dx: float = (e.plane.x - at.x) * facing
		if e.team == "enemy" and dx >= 0.0 and dx <= best_d and absf(e.plane.y - at.y) < 60.0:
			best_d = dx
			best = Vector2(e.plane.x, e.plane.y - e.altitude)
	return best

## Debug (--cast, P6e previews): a technique's cast toward the foes and its hits on each one in reach, drawn as a real
## cast's are, through this view only; nothing is submitted.
func preview_cast(tech: String) -> void:
	var t := ContentDB.entry("techniques", tech)
	var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy")
	var facing := 1 if foes.is_empty() or foes[0].plane.x >= player.position.x else -1
	_cast(tech, facing, SpriteCache.element_color(str(t.element)))
	for e in foes:
		if (e.plane.x - player.position.x) * facing > float(t.hitbox.x[1]) + 40.0: continue
		for h in int(t.hits):   # a buff or a heal strikes nothing
			_on_event("hit_landed", {"attacker": player.actor_id, "target": str(e.uid), "target_kind": "enemy", "amount": 3100 * (h + 3), "type": str(t.damage_type),
				"crit": h == 1, "element": str(t.element), "x": e.plane.x, "y": e.plane.y, "alt": e.altitude + e.height() * 0.8, "source": "tech:" + tech})

## A moment's camera move (P6 `camera` layer): ease to `target` over in_s, hold, and ease back over out_s.
func hold_camera(target: Vector2, in_s: float, hold_s: float, out_s: float) -> void:
	camera_hold = {"target": target, "t": 0.0, "in": in_s, "hold": hold_s, "out": out_s}

# ------------------------------------------------------------------ events → effects
func _on_event(name: String, p: Dictionary) -> void:
	match name:
		"room_entered":
			if str(p.get("actor", "")) == Game.active_id:
				_build_room()
				_place_player()
				_fame_greeting()
		"enemy_aggro":
			var foe: EnemyState = Game.room_rt.enemies.get(int(p.get("enemy", 0))) if Game.room_rt else null
			if foe and not foe.hidden: fx.label(Vector2(foe.plane.x, foe.plane.y - foe.altitude - foe.height() - 24), "!", UiKit.GOLD, 26)
		"enemy_spawned", "ally_spawned":
			var uid := int(p.get("enemy", p.get("uid", 0)))
			var e: EnemyState = Game.room_rt.enemies.get(uid)
			if e: _add_enemy_view(e)
		"loot_dropped":
			for l in p.get("items", []):
				var lv = LootView.new()
				lv.setup(l)
				room_layer.add_child(lv)
		# S43 traversal feedback.
		"landed":
			if str(p.get("actor", "")) == player.actor_id and p.get("plunge", false):
				# Plunge: a shock ring the size of its strike (60) and a jolt.
				fx.add("ring", player.position, {"color": Color(UiKit.PALE_GOLD, 0.8), "radius": 60.0, "dur": 0.35})
				fx.add("dust", player.position, {"color": Color(0.8, 0.74, 0.62, 0.7), "dur": 0.4})
				Audio.play("rumble")
				add_shake(0.2)
			elif str(p.get("actor", "")) == player.actor_id and float(p.get("fall_height", 0)) > 120.0:
				fx.add("ring", player.position, {"color": Color(0.85, 0.8, 0.7, 0.6), "radius": 34.0, "dur": 0.3})
				Audio.play("land")
		"art_used":
			if str(p.get("actor", "")) == player.actor_id:
				match str(p.get("art", "")):
					"air_dash": Audio.play("dodge")
					"glide": fx.add("dust", player.position + Vector2(0, -40), {"color": Color(UiKit.BRIGHT_JADE, 0.5), "dur": 0.3})
					"water_skimming": Audio.play("water_step")
					"bounce": Audio.play("land")
		"volume_entered":
			if str(p.get("actor", "")) == player.actor_id and str(p.get("kind", "")) in ["water_deep", "rising_water"]: Audio.play("water_step")
		"wall_kicked":
			if str(p.get("actor", "")) == player.actor_id:
				fx.add("spark", player.position + Vector2(-int(p.get("side", 1)) * -14, -50), {"color": UiKit.PAPER, "dur": 0.25})
		"fell_out":
			if str(p.get("actor", "")) == player.actor_id:
				fx.add("text", player.position + Vector2(0, -130), {"text": Tx.t("hud.fell"), "color": UiKit.MIST, "size": 18, "dur": 1.4})
		"hit_landed":
			if str(p.get("target_kind", "")) == "player" and str(p.get("target", "")) == player.actor_id: player.knock_off_climb()
			var pos := Vector2(float(p.get("x", 0)), float(p.get("y", 0)) - float(p.get("alt", 60)))
			var kind := str(p.get("target_kind", "enemy"))
			var amount := int(p.get("amount", 0))
			var color = UiKit.PAPER
			if kind == "player": color = UiKit.RED
			elif p.get("crit", false): color = UiKit.GOLD
			elif str(p.get("type", "")) == "qi": color = UiKit.QI
			elif str(p.get("type", "")) == "soul": color = UiKit.SOUL
			# P6e: a technique's hit draws at its tier (§5.2): the number's size, the spark's count, size, reach and style; the
			# hits of one cast on one foe stack (§5.5); the first hit of a Heaven-grade cast shakes once.
			var src := str(p.get("source", ""))
			var n := MomentRules.tier_numbers(src)
			var tech := ContentDB.entry("techniques", src.trim_prefix("tech:")) if src.begins_with("tech:") else {}
			if Game.is_revealed("hud:damage_numbers") or kind == "player":
				fx.number(pos, UiKit.short(amount), color, int(n.number_size) if not tech.is_empty() else 22, bool(p.get("crit", false)),
					str(p.get("target", "")) + src if not tech.is_empty() else "", float(amount))
			fx.add("spark", pos + Vector2(0, 20), {"color": SpriteCache.element_color(str(p.get("element", "none"))), "dur": 0.25,
				"count": MomentRules.particle_count(int(n.spark_count)), "size": n.spark_size, "radius": n.spark_reach, "core": n.core_r,
				"style": tech.get("vfx", {}).get("particles", MomentRules.particle_style("", str(p.get("element", "none")), str(p.get("type", ""))))})
			if cast_shake.has(src):
				cast_shake.erase(src)
				add_shake(float(n.shake_s), float(n.shake_amp))
			if kind == "player" and amount > Game.active().pools.max_hp * 0.15: add_shake(0.25)
			if p.get("crit", false): add_shake(0.12)
			Audio.play("hit_crit" if p.get("crit", false) else ("hurt" if kind == "player" else "hit"))
		"hazard_warned":
			var sfx := {"falling_rocks": "rumble", "lightning": "charge", "poison_mist": "hiss"}
			Audio.play(str(sfx.get(str(p.hazard), "tell")))
		"hazard_struck":
			if str(p.get("actor", "")) == Game.active_id:
				var hname := ContentDB.name_of("hazards", str(p.hazard))
				var over := player.position + Vector2(0, -130)
				if p.get("answered", false): fx.label(over, Tx.t("world_view.hazard_answered") % hname, UiKit.BRIGHT_JADE, 17)
				elif int(p.get("amount", 0)) == 0: fx.label(over, hname, UiKit.PALE_GOLD, 17)
		"hit_missed":
			fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60))), Tx.t("world_view.miss"), UiKit.MIST, 18)
		"hit_immune":
			fx.label(Vector2(float(p.x), float(p.y) - float(p.get("alt", 60)) - 40), Tx.t("world_view.immune"), UiKit.MIST, 18)
		"hit_dodged":
			fx.label(player.position + Vector2(0, -100), Tx.t("world_view.evade"), UiKit.BRIGHT_JADE, 18)
		"parried":
			fx.add("flash", player.position + Vector2(player.facing * 20, -50), {"color": UiKit.PALE_GOLD, "radius": 30, "dur": 0.25})
			fx.label(player.position + Vector2(0, -110), Tx.t("world_view.parry"), UiKit.GOLD, 22)
			Audio.play("parry")
		"attack_started":
			if str(p.get("actor", "")) == Game.active_id:
				var tech := str(p.get("technique", ""))
				if tech != "":
					_cast(tech, int(p.facing), SpriteCache.element_color(str(p.get("element", "none"))))
					Audio.play("technique")
				else:
					Audio.play("swing")
			elif p.get("enemy", false):
				Audio.play("tell")
		"actor_defeated":
			fx.add("dust", Vector2(float(p.x), float(p.y)), {"dur": 0.5})
		"object_hit":
			if object_views.has(str(p.object)): object_views[str(p.object)].hit_flash = 0.15
			fx.add("spark", Vector2(float(p.x), float(p.y) - 30), {"color": UiKit.PALE_GOLD, "dur": 0.2})
			Audio.play("hit")
		"object_broken":
			var ov = object_views.get(str(p.object))
			if ov: fx.add("dust", ov.position, {"dur": 0.5})
			Audio.play("break")
		# S47: a spare artifact detonated, and the flying sword leaving and returning.
		"artifact_detonated":
			fx.add("wave", player.position, {"color": Color("ff9a5a"), "radius": float(ContentDB.stat_const("detonation.radius", 180)), "dur": 0.5})
			fx.add("flash", player.position + Vector2(0, -50), {"color": Color("ffe0a0"), "radius": 90.0, "dur": 0.35})
			add_shake(0.35)
			Audio.play("rumble")
		"talisman_used":
			# S47: the paper flares and burns away; attack talismans burst where they land.
			var tat := Vector2(float(p.get("x", player.position.x)), float(p.get("y", player.position.y)) - float(p.get("alt", 0.0)) - 40.0)
			match str(p.get("kind", "")):
				"attack":
					fx.add("wave", tat, {"color": Color("ff8a4a") if str(p.get("item", "")) == "flame_talisman" else Color("9fd8ff"), "radius": 90.0, "dur": 0.45})
					fx.add("flash", tat, {"color": Color("fff0c0"), "radius": 50.0, "dur": 0.3})
				"defence": fx.add("wave", player.position + Vector2(0, -50), {"color": Color("c8ccd0"), "radius": 46.0, "dur": 0.6})
				_: fx.add("spark", player.position + Vector2(0, -70), {"color": Color("e8d99a"), "dur": 0.4})
			Audio.play("technique")
		"item_blooded":
			# S47 blood-drop bind: a bead of blood falls onto a piece worn for the first time.
			fx.add("spark", player.position + Vector2(0, -70), {"color": Color("c0303a"), "dur": 0.5})
			fx.add("text", player.position + Vector2(0, -120), {"text": "·", "color": Color("d23a44"), "size": 34, "dur": 0.9})
		"natal_broken":
			fx.add("flash", player.position + Vector2(0, -50), {"color": Color("ff6a5a"), "radius": 70.0, "dur": 0.4})
			add_shake(0.3)
			Audio.play("break")
		"array_deployed":
			var ac: Color = FxLayer.ARRAY_COLOURS.get(str(p.get("kind", "")), FxLayer.ARRAY_COLOURS.guard)
			fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": ac, "radius": float(p.radius), "dur": 0.5})
			Audio.play("forge")
		"artifact_spirit_spoke":
			if str(p.get("actor", "")) == Game.active_id and player: player.say(str(p.get("line", "")))
		"artifact_skill_used":
			if str(p.get("actor", "")) == Game.active_id:
				var ring := float(p.get("ring", 0.0))
				fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": Color("ffd27a") if p.get("awakened", false) else Color("b18de2"),
					"radius": ring if ring > 0.0 else 60.0, "dur": 0.4 if ring > 0.0 else 0.3})
				Audio.play("surge")
		"array_faded":
			if str(p.get("actor", "")) == Game.active_id: Audio.play("ui_close")
		"illusion_cast":
			if str(p.get("actor", "")) == Game.active_id and player:
				if is_instance_valid(illusion_view): illusion_view.queue_free()
				var gh := AvatarScript.new()
				gh.outfit = player.avatar.outfit.duplicate(true)
				gh.facing = int(p.get("facing", 1))
				gh.modulate = Color(0.78, 0.68, 1.0, 0.55)
				gh.position = Vector2(float(p.x), float(p.y) - float(p.alt)).snapped(Vector2(2, 2))
				gh.z_index = 1500 + int(float(p.y))
				room_layer.add_child(gh)
				illusion_view = gh
				fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": UiKit.SOUL, "radius": 70.0, "dur": 0.5})
				Audio.play("technique")
		"illusion_broken":
			if str(p.get("actor", "")) == Game.active_id and is_instance_valid(illusion_view):
				fx.add("spark", illusion_view.position + Vector2(0, -60), {"color": UiKit.SOUL, "dur": 0.45})
				fx.add("wave", illusion_view.position, {"color": UiKit.SOUL, "radius": 50.0, "dur": 0.4})
				illusion_view.queue_free()
				illusion_view = null
		"melody_pulse":
			# S47 v1.1 flute: the melody spreads as a jade ring, notes drifting up from the player.
			var mat := Vector2(float(p.x), float(p.y))
			fx.add("ring", mat, {"color": Color(0.56, 0.91, 0.81, 0.8), "radius": float(p.radius), "dur": 0.55})
			for i in 2:
				fx.add("note", player.position + Vector2(randf_range(-26, 26), -96 - i * 14), {"color": Color("8fe8cf") if i == 0 else UiKit.PALE_GOLD,
					"vel": Vector2(randf_range(-10, 10), -46.0), "dur": 1.2, "size": 18 + i * 4, "radius": randf() * 6.0})
		"melody_changed":
			if str(p.get("actor", "")) == Game.active_id and p.get("on", false):
				fx.add("wave", player.position, {"color": Color("8fe8cf"), "radius": 70.0, "dur": 0.5})
				Audio.play("meditate")
		"sword_released", "sword_returned":
			fx.add("spark", player.position + Vector2(0, -100), {"color": Color("dff3ff"), "dur": 0.3})
			Audio.play("forge")
		"treasure_used":
			var at := Vector2(float(p.x), float(p.y))
			var tr_radius := float(CombatAuthority.treasure_of(str(p.treasure)).get("radius", 150))
			match str(p.action):
				"bell":
					fx.add("wave", player.position, {"color": UiKit.PALE_GOLD, "radius": tr_radius, "dur": 0.6})
					fx.add("wave", player.position, {"color": UiKit.GOLD, "radius": tr_radius * 0.7, "dur": 0.45})
					Audio.play("bell")
				"pagoda":
					fx.add("pagoda", at, {"color": UiKit.BRIGHT_JADE, "dur": 4.0})
					Audio.play("forge")
				"mirror":
					fx.add("flash", player.position + Vector2(0, -50), {"color": Color("bfe8ff"), "radius": 60.0, "dur": 0.4})
				"seal":
					fx.add("seal_slam", player.position, {"color": UiKit.BRIGHT_JADE, "radius": tr_radius, "dur": 0.7})
					add_shake(0.25)
					Audio.play("break")
				"cauldron":
					fx.add("spiral", at + Vector2(0, -30), {"color": UiKit.QI, "dur": 1.0})
					Audio.play("technique")
				"banner", "gourd":
					fx.add("ring", player.position, {"color": UiKit.QI if str(p.action) == "banner" else UiKit.SOUL, "radius": 110.0, "dur": 0.8})
					Audio.play("technique")
				"palm":
					fx.add("talisman_wave", player.position + Vector2(0, -50), {"color": UiKit.PALE_GOLD, "radius": float(p.get("reach", 540)), "facing": int(p.get("facing", 1)), "dur": 0.6})
					add_shake(0.3)
					Audio.play("breakthrough")
		"wisp_struck":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": UiKit.QI, "dur": 0.25})
		"projectile_reflected", "projectile_absorbed":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": Color("bfe8ff") if name == "projectile_reflected" else UiKit.SOUL, "dur": 0.3})
		"projectile_burst":
			fx.add("wave", Vector2(float(p.x), float(p.y)), {"color": Color("ffd76a"), "radius": float(p.radius), "dur": 0.4})
			fx.add("flash", Vector2(float(p.x), float(p.y) - 30.0), {"color": Color("fff0b0"), "radius": 50.0, "dur": 0.25})
			add_shake(0.15)
			Audio.play("break")
		"meditation_tick":
			if Game.active() and Game.active().pools.max_qi > 0:
				fx.add("motes", player.position + Vector2(0, -10), {"color": UiKit.QI if not p.get("spring", false) else UiKit.BRIGHT_JADE, "dur": 1.0})
			elif Game.active():
				fx.add("motes", player.position + Vector2(0, -10), {"color": Color("f4ecd5"), "dur": 1.0})
		"player_revived":
			fx.add("flash", player.position + Vector2(0, -40), {"color": UiKit.BRIGHT_JADE, "radius": 60, "dur": 0.6})
		"projectile_ended":
			fx.add("spark", Vector2(float(p.x), float(p.y) - float(p.alt)), {"color": UiKit.PAPER, "dur": 0.15})
		"dodged":
			fx.add("dust", player.position, {"dur": 0.35})
			Audio.play("dodge")
		"node_gathered":
			var ov2 = object_views.get(str(p.object))
			if ov2: fx.add("motes", ov2.position, {"color": UiKit.BRIGHT_JADE, "dur": 0.8})
			Audio.play("pickup")
		"loot_picked":
			Audio.play("coin" if int(p.get("coins", 0)) > 0 else "pickup")
		"equipment_changed":
			if str(p.get("actor", "")) == Game.active_id and player:
				player.avatar.outfit = InventoryAuthority.outfit_for(Game.active())
				player.avatar.last_key = ""
		"emote_played":
			var em: Dictionary = ContentDB.entry("emotes", str(p.emote))
			player.play_emote(em)
			fx.add("text", player.position + Vector2(0, -150), {"text": str(em.get("text", "...")), "color": UiKit.PAPER, "size": 20, "dur": float(em.get("seconds", 1.8))})
# ------------------------------------------------------------------ shared helpers (legacy API kept)
func by_id(id: String) -> WalkSurface: return geometry.index.get(id)
func walk_target(point: Vector2, current_height: float, previous: WalkSurface) -> WalkSurface:
	return geometry.walk_target(point, current_height, previous)
func landing_target(point: Vector2, previous_height: float, next_height: float) -> WalkSurface:
	return geometry.landing_target(point, previous_height, next_height)

func update_occlusion() -> void:
	var hidden := not geometry.occluder_at(player.state).is_empty()
	player.visible = true
	player_shadow.visible = true
	player_outline.visible = hidden
	player_outline.sync()

func update_sorting() -> void:
	for visual in terrain_visuals:
		var s: WalkSurface = visual.surface
		if s.stratum == "ground" and ((map_theme == "" and not room_mode) or (s.base == 0 and s.rise == 0)):
			visual.z_index = -1800 if s.kind == "stairs" else -2000 + int(s.base)
		else:
			visual.z_index = 1500 + int(s.bounds.end.y)
			if s.kind == "roof":
				for obstacle in geometry.obstacles:
					if obstacle.get("surface", "") == s.id:
						visual.z_index = 1500 + int(obstacle.get("front_y", s.bounds.end.y))

func spawn_arrow(origin: Vector2, elevation: float, direction: int) -> void:
	var projectile := Arrow.new()
	projectile.zone = geometry
	projectile.plane = origin + Vector2(direction * 28, 0)
	projectile.altitude = elevation + 58
	projectile.direction = direction
	projectile.z_index = geometry.render_depth(player.state) + 1
	add_child(projectile)

## S43 rule 6: the safe spot is recorded after 0.3 s standing on a surface at least 24 units from any open
## edge. record_safe_position() still forces a record (room entry, tests).
var safe_stand := 0.0
func _track_safe(delta: float) -> void:
	var s: WalkSurface = player.surface if player else null
	# Never a safe spot in deep water, on a mover or on a floor that crumbles (S43).
	if s == null or not player.state.climbing.is_empty() or not _clear_of_open_edges(s, player.plane) or not player.state.water.is_empty() \
			or s.moving or s.disabled or not geometry.crumble_volume(s.id).is_empty():
		safe_stand = 0.0
		return
	safe_stand += delta
	if safe_stand >= 0.3: record_safe_position()

func _clear_of_open_edges(s: WalkSurface, p: Vector2) -> bool:
	var margin := 24.0
	if s.edges.get("n", "open") == "open" and p.y - s.bounds.position.y < margin: return false
	if s.edges.get("s", "open") == "open" and s.bounds.end.y - p.y < margin: return false
	if s.edges.get("w", "open") == "open" and p.x - s.bounds.position.x < margin: return false
	if s.edges.get("e", "open") == "open" and s.bounds.end.x - p.x < margin: return false
	return true

func record_safe_position() -> void:
	if player and player.surface:
		last_safe = {"map_revision": MAP_REVISION, "surface": player.surface.id, "x": player.plane.x, "y": player.plane.y, "map_theme": map_theme,
			"map_seed": map_seed, "generator_version": MapGenerator.VERSION}
		player.state.last_safe = {"room": str(room_def.get("id", "")) if room_mode else "", "surface": player.surface.id, "x": player.plane.x, "y": player.plane.y}

func restore_progress(state: Dictionary) -> void:
	if int(state.get("map_revision", 0)) not in [2, 3, 4, 5, 6, MAP_REVISION]: return
	if str(state.get("map_theme", "")) != map_theme: return
	player.hp = clampf(float(state.get("hp", 100)), 0, 100)
	player.qi = clampf(float(state.get("qi", 100)), 0, 100)
	player.facing = -1 if state.get("facing", 1) == -1 else 1
	skill_page = clampi(int(state.get("skill_page", 0)), 0, 1)
	var s := by_id(str(state.get("surface", "")))
	var p := Vector2(float(state.get("x", 0)), float(state.get("y", 0)))
	if s == null or not p.is_finite(): return
	if int(state.get("map_revision", 0)) in [2, 3]: p = p.clamp(s.bounds.position + Vector2.ONE, s.bounds.end - Vector2.ONE)
	if not s.contains(p): p = s.nearest_supported(p)
	player.surface = s
	player.altitude = s.height_at(p)
	player.plane = geometry.nearest_free(p, player.altitude, s.stratum)
	if not s.contains(player.plane):
		player.surface = surfaces[0]
		player.plane = Vector2(620, 820)
	player.altitude = player.surface.height_at(player.plane)

## Fall recovery returns to the last safe spot (or the room spawn point); never death.
func recover_to_safe() -> void:
	if room_mode:
		var sp: Array = room_def.get("spawn_point", [200, 800])
		var target := Vector2(float(last_safe.get("x", sp[0])), float(last_safe.get("y", sp[1]))) if not last_safe.is_empty() else Vector2(float(sp[0]), float(sp[1]))
		var s: WalkSurface = by_id(str(last_safe.get("surface", "")))
		if s == null or s.disabled or not s.contains(target):
			s = surfaces[0]
			target = Vector2(float(sp[0]), float(sp[1]))
		player.surface = s
		player.plane = target
		player.altitude = s.height_at(target)
	elif last_safe.is_empty():
		player.plane = Vector2(340, 800)
		player.surface = surfaces[0]
		player.altitude = 0
	else:
		var hp: float = player.hp
		var qi: float = player.qi
		var facing: int = player.facing
		var page := skill_page
		restore_progress(last_safe)
		player.hp = hp
		player.qi = qi
		player.facing = facing
		skill_page = page
	player.velocity = Vector2.ZERO
	player.reset_sprint()
	player.sync_visual()
	player.vertical_speed = 0
	player.state.jumps_used = 0
	player.state.landing_assist = ""
	player.state.departed_surface = ""
	player.state.air_peak = player.altitude
	player.state.air_base = player.altitude
	player.state.air_stratum = player.surface.stratum
	player.state.climbing = {}
	player.state.gliding = false
	player.state.plunging = false
	player.state.water = {}
	player.state.sink_depth = 0.0
	player.state.drowned = false
	if player.bound() and Game.combat.is_gliding(player.actor_id): Game.submit({"type": "glide", "on": false})
	travel.reset(player.plane, player.altitude)
	# Combat takes the fall's cost when it hears fell_out (S43 rule 6).
	if room_mode and player.bound():
		player.authority.fell_out({"x": player.plane.x, "y": player.plane.y, "surface": player.surface.id})

func save_game() -> Error:
	if room_mode:
		return Game.save_all()
	return OK

# ------------------------------------------------------------------ legacy (engine regression map)
func _legacy_ready() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://data/world.json"))
	map_data = data
	data = ZoneLayout.compile(data)
	geometry.configure(data)
	map_bounds = geometry.bounds
	surfaces = geometry.surfaces
	for s in surfaces:
		var terrain := Terrain.new()
		terrain.surface = s
		terrain.ground_material = str(map_data.get("ground_material", "stone"))
		room_layer.add_child(terrain)
		terrain_visuals.append(terrain)
	for spec in data.get("objects", []):
		if spec.get("art", "none") == "none": continue
		var prop := SceneryProp.new()
		prop.spec = spec
		room_layer.add_child(prop)
		props.append(prop)
	player = Player.new()
	player.world = self
	player.outfit = outfit.duplicate(true)
	player.plane = Vector2(data.spawn[0], data.spawn[1])
	player.surface = surfaces[0]
	add_child(player)
	player.arrow_released.connect(spawn_arrow)
	_attach_player_helpers()
	travel.reset(player.plane, player.altitude)
	player.sync_visual()
	camera.position = camera_target()
	record_safe_position()
	update_sorting()

func _legacy_process(delta: float) -> void:
	camera.position = camera.position.lerp(camera_target(), 1 - exp(-delta * 5))
	camera.position = camera.position.snapped(Vector2(2, 2))
	record_safe_position()
	update_occlusion()
	save_timer += delta
	if save_timer >= 5:
		save_timer = 0
		save_game()
