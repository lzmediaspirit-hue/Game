class_name WorldAuthority
extends Authority
## S17/S18/S32 · Owns the loaded room (RoomRuntime), portals and world objects,
## ground loot (rolled on actor_defeated), discovered teleport stones and the
## zone context. One room is loaded at a time.
##
## The authority keeps the state, the intents, the subscriptions, the room's lifecycle (loading and entering a room, the
## character's memory of it) and the tick; the rest of the work is done by its parts in authority/world/, one for each
## section (audit 45, S9: WorldPart says how a part works). Its public methods forward to them.

const BREAKABLES := ["jar", "crate", "wine_jar"]
const TRAINING := ["training_stump", "training_dummy"]
const REACH_ALT := 48.0   # an object answers only a body within this height of it (the context button and interact)

## Debug tools (S38, the Max Test APK): every portal, hidden way and climb is open, whatever its quest, flag or rank.
## A way to a room not built yet stays "Coming soon".
var debug_open_ways := false
var ambush_cd: Dictionary = {}    # actor -> seconds before the roads may spring another ambush (not saved)
var herb_clock := 0.0             # the rare-herb check runs once a second
var sensed_herbs: Dictionary = {} # object -> {until, ripe, seconds, dormant}: a Spirit Sense readout over the node
var chases: Dictionary = {}       # actor -> {object, room, start}: a thief running over the roofs (not saved)
var runs: Dictionary = {}         # actor -> {object, room, start}: a timed route under way (not saved)
var voyages: Dictionary = {}      # actor -> {route, vessel, seconds}: a crossing under way
var auto_hunt: Dictionary = {}    # actor -> true while the toggle is on (the session only)
var auto_paths: Dictionary = {}   # actor -> {target, route: [{room, portal, to}]}
var auto_check := 0.0             # auto-hunt asks whether it may go on twice a second
var guide_cache := {}             # the direction mark's last step: {key, at, step}

# The parts, untyped on purpose (docs/architecture/authority_parts.md, S9): typed, they put the parts in a cycle with
# this class, and Godot's analyzer then leaves ActorState's untyped members unresolved for every script compiled after
# boot (rules_tests failed to parse). Each holds the class named in its comment.
var ambush        # WorldAmbush: bandit ambushes
var herbs         # WorldHerbs: rare herbs and their guardians
var portals       # WorldPortals: portals, hidden ways, routes, teleports and Spirit Sense
var arrays        # WorldArrays: the sect's transfer arrays
var objects       # WorldObjects: room objects: shown, open, their states, blows on them
var context       # WorldContext: interact and the context button
var loot          # WorldLoot: beast cores and loot
var races         # WorldRaces: rooftop chases and timed routes
var hazards       # WorldHazards: room hazards and hazard volumes
var starsea       # WorldStarsea: Starsea voyages
var room_events   # WorldRoomEvents: room events
var nests         # WorldNests: the Beast Kings' nests, the Beast Tide, the Beast Trial Grove
var tower         # WorldTower: the Trial Tower
var idle          # WorldIdle: idle rooms, auto-hunt, auto-path and the direction mark

func _init(g) -> void:
	super(g)
	ambush = WorldAmbush.new(self)
	herbs = WorldHerbs.new(self)
	portals = WorldPortals.new(self)
	arrays = WorldArrays.new(self)
	objects = WorldObjects.new(self)
	context = WorldContext.new(self)
	loot = WorldLoot.new(self)
	races = WorldRaces.new(self)
	hazards = WorldHazards.new(self)
	starsea = WorldStarsea.new(self)
	room_events = WorldRoomEvents.new(self)
	nests = WorldNests.new(self)
	tower = WorldTower.new(self)
	idle = WorldIdle.new(self)

func intents() -> Array:
	return ["use_portal", "interact", "teleport", "pick_up", "enter_world", "sense_pulse", "climb_tower", "sweep_floor",
		"set_auto_hunt", "auto_path", "enter_grid_room", "array_travel"]

func subscribe() -> void:
	# S49 mobile conventions: auto-path follows the character room to room and stops at danger.
	GameEvents.subscribe("room_entered", idle.auto_path_room, 60)
	GameEvents.subscribe("hit_landed", idle.auto_path_danger, 60)
	# S43 rising water: a boss phase or a boss's fall moves the water in the room.
	for ev in ["boss_phase", "field_boss_defeated"]:
		GameEvents.subscribe(ev, _on_room_script.bind(ev), 50)
	GameEvents.subscribe("actor_defeated", loot.on_actor_defeated, 50)
	GameEvents.subscribe("actor_defeated", room_events.event_kill, 55)
	GameEvents.subscribe("bottleneck_reached", _on_bottleneck, 50)
	GameEvents.subscribe("hit_landed", room_events.on_hit_during_event, 50)
	GameEvents.subscribe("room_entered", portals.on_room_entered_fates, 51)
	GameEvents.subscribe("room_entered", ambush.on_room_entered_ambush, 52)
	GameEvents.subscribe("world_event_started", objects.on_world_event_started, 50)
	for ev in ["room_entered", "quest_completed"]: GameEvents.subscribe(ev, objects.announce_first_fruit, 96)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"use_portal": return use_portal(c, str(intent.get("portal", "")), bool(intent.get("crossing", false)))
		"interact": return interact(c, str(intent.get("object", "")), bool(intent.get("pick", false)))
		"teleport": return teleport(c, str(intent.get("stone", "")))
		"pick_up": return pick_up(c, int(intent.get("uid", -1)))
		"enter_world": return enter_world(c)
		"sense_pulse": return sense_pulse(c)
		"climb_tower": return climb_tower(c, int(intent.get("floor", 0)))
		"sweep_floor": return sweep_tower(c, int(intent.get("floor", -1)))
		"set_auto_hunt": return set_auto_hunt(c, bool(intent.get("on", false)))
		"auto_path": return start_auto_path(c, str(intent.get("target", "")), str(intent.get("place", "")))
		"enter_grid_room": return enter_grid_room(c, TopdownRoom.load_room(str(intent.get("room", ""))))
		"array_travel": return array_travel(c, str(intent.get("from", "")), str(intent.get("to", "")))
	return fail("unknown_intent")

## The side view (decision 41 keeps it as a new-game fallback): a room played side-on, with no height grid. Every
## side-view branch of the world asks this, or finds grid_for null, so they can go together when the side view does.
static func side_view(rt: RoomRuntime) -> bool:
	return rt == null or rt.topdown == null

## S18: at the zone's ceiling the land itself is the limit.
func _on_bottleneck(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or not game.progression.at_zone_ceiling(c): return
	var zone := ContentDB.zone_of_room(str(c.position.get("room", "")))
	emit("zone_ceiling_reached", {"actor": c.id, "zone": str(zone.get("id", "")), "ceiling": str(p.get("realm_key", ""))})

## S43 rising water: the room's geometry answers a boss phase or a boss's fall.
func _on_room_script(p: Dictionary, ev: String) -> void:
	if game.room_rt != null: game.room_rt.geometry.on_event(ev, p)
	# T1: on the grid the same script raises the layout's floods (TopdownTraverse).
	if game.room_rt != null and game.room_rt.topdown != null and game.room_rt.topdown.traverse != null: game.room_rt.topdown.traverse.on_event(ev, p)

# ------------------------------------------------------------------ rooms
static func compile_geometry(def: Dictionary) -> Dictionary:
	var data := {"bounds": def.get("bounds", [0, 480, 1280, 480]), "surfaces": def.get("surfaces", []).duplicate(true),
		"objects": def.get("scenery", []).duplicate(true), "gates": []}
	# S43 traversal sections pass straight through to the geometry.
	for k in ["blocks", "climbables", "void_altitude", "volumes", "movers"]:
		if def.has(k): data[k] = def[k].duplicate(true) if def[k] is Array else def[k]
	for o in def.get("objects", []):
		if o.has("footprint") and o.get("blocks", false):
			data.objects.append({"id": "obj_" + str(o.id), "art": "none", "footprint": o.footprint, "height": float(o.get("height", 60)), "radius": 4})
	return ZoneLayout.compile(data)

func load_room(c, room_id: String, portal_id: String, point := Vector2.INF) -> Dictionary:
	var def := ContentDB.room(room_id)
	if def.is_empty(): return fail("unknown_room")
	if voyages.has(c.id) and not def.get("crossing", false): voyages.erase(c.id)   # a crossing abandoned (fallen overboard)
	var old = game.room_rt.room_id if game.room_rt else ""
	if old != "":
		emit("room_left", {"actor": c.id, "room": old, "portal": portal_id})
	var grid := grid_for(c, room_id)
	var rt := _runtime(room_id, def, grid)
	game.room_rt = rt
	# Arrival: on the linked portal facing into the room, never mid-air.
	var arrival := point
	var facing := int(c.position.get("facing", 1))
	if not arrival.is_finite():
		var p := rt.portal_def(portal_id)
		if not p.is_empty() and grid != null:
			# On the grid: the portal's own arrival cell inside it, facing away from the way out.
			var ar: Array = p.get("arrive", p.get("at", [0, 0]))
			arrival = Vector2(float(ar[0]), float(ar[1]))
			facing = -1 if float((p.get("dir", [-1, 0]) as Array)[0]) > 0.0 else 1
		elif not p.is_empty():
			var at: Array = p.get("at", [0, 0])
			var inward := 1 if float(at[0]) < rt.width() * 0.5 else -1
			arrival = Vector2(float(at[0]) + inward * float(p.get("arrive_offset", 70)), float(at[1]) + float(p.get("arrive_dy", 0)))
			facing = inward
		else:
			var sp: Array = rt.def.get("spawn_point", [200, 800])
			arrival = Vector2(float(sp[0]), float(sp[1]))
	var surf := ground_at(rt, arrival)
	if surf == null:
		var sp2: Array = rt.def.get("spawn_point", [200, 800])
		arrival = Vector2(float(sp2[0]), float(sp2[1]))
		surf = ground_at(rt, arrival)
	if grid != null:
		# On the grid: a spot inside the room where a body can stand (a shrine's step or a saved spot is never in a wall).
		if not rt.geometry.bounds.has_point(arrival): arrival = grid.spawn
		arrival = grid.nearest_standable(arrival)
	else:
		arrival = rt.geometry.nearest_free(arrival, surf.height_at(arrival) if surf else 0.0, surf.stratum if surf else "ground")
	c.position = {"room": room_id, "portal": portal_id, "x": arrival.x, "y": arrival.y, "surface": surf.id if surf and grid == null else "", "facing": facing}
	var first = not game.account.visited_rooms.has(room_id)
	game.account.visited_rooms[room_id] = true
	rt.first_visit = first
	var zone_old = ContentDB.room_zone.get(old, "")
	var zone_new = ContentDB.room_zone.get(room_id, "")
	if def.get("type", "") in ["town", "sect", "home"] or def.get("town", false): c.last_town = room_id
	objects.restore_object_states(c, rt)
	_arrive(c, rt, portal_id, arrival, facing, first, str(zone_new))
	if zone_new != zone_old: emit("zone_entered", {"actor": c.id, "zone": zone_new})
	if rt.def.has("event"): room_events.start_event(c, rt, rt.def.event)
	game.crafting.check_raids(c)   # S45: what came for the garden while you were away
	return ok({"room": room_id, "x": arrival.x, "y": arrival.y, "facing": facing})

## Every room's arrival: its hazards set, a moment of spawn protection, and room_entered (Enemies fills the spawns).
func _arrive(c, rt: RoomRuntime, portal_id: String, arrival: Vector2, facing: int, first: bool, zone: String) -> void:
	hazards.init_hazards(c, rt)
	rt.arrival_protection = float(ContentDB.stat_const("combat.spawn_protection_s", 1.5))
	game.combat.apply_status(c.id, "spawn_protection", rt.arrival_protection, 1.0)
	emit("room_entered", {"actor": c.id, "room": rt.room_id, "portal": portal_id, "first_visit": first, "x": arrival.x, "y": arrival.y,
		"facing": facing, "surface": str(c.position.get("surface", "")) if side_view(rt) else "", "zone": zone})

## Redesign Phase 2: enter a room on the top-down height grid (the prototype room). It runs on the same authorities as
## every room (its foes, loot, fights), but it is not a place in the world: the character's saved position and
## visited rooms stay as they were. The rooms of the world on the grid are entered by load_room (Phase 4).
func enter_grid_room(c, grid: TopdownRoom) -> Dictionary:
	if grid.w == 0: return fail("unknown_room")
	var old = game.room_rt.room_id if game.room_rt else ""
	if old != "": emit("room_left", {"actor": c.id, "room": old, "portal": ""})
	var rt := _runtime(grid.id, grid.runtime_def(), grid)
	rt.def.prototype = true
	game.room_rt = rt
	game.in_world = true
	_arrive(c, rt, "", grid.spawn, 1, false, "")
	return ok({"room": grid.id, "x": grid.spawn.x, "y": grid.spawn.y})

## A room's live state: its definition and its geometry. A room on the grid takes its places from its layout
## (TopdownRoom.merge_def) and a stand-in ground under the grid's own heights (TopdownRoom.geometry_def).
func _runtime(room_id: String, def: Dictionary, grid: TopdownRoom) -> RoomRuntime:
	var rt := RoomRuntime.new()
	rt.room_id = room_id
	rt.topdown = grid
	rt.def = def if grid == null or str(def.get("view", "")) == "topdown" else grid.merge_def(def)
	rt.geometry.configure(compile_geometry(rt.def) if grid == null else grid.geometry_def())
	rt.next_uid = 1000
	return rt

## The layout a character plays a room on (redesign Phase 4): a character made for the top-down world (`view`) enters
## every room that has one on the height grid; every other room, and every side-view character, stays side-view.
func grid_for(c, room_id: String) -> TopdownRoom:
	if c == null or str(c.view) != "topdown" or not TopdownRoom.has_layout(room_id): return null
	var grid := TopdownRoom.load_room(room_id)
	return grid if grid.w > 0 else null

## The surface under a point, the ground before a ledge; with none under it, the room's first ground.
func ground_at(rt: RoomRuntime, p: Vector2) -> WalkSurface:
	var best: WalkSurface = null
	for s in rt.geometry.surfaces:
		if s.contains(p) and (best == null or s.stratum == "ground"): best = s
	if best == null:
		for s in rt.geometry.surfaces:
			if s.stratum == "ground": return s
	return best

func enter_world(c) -> Dictionary:
	var room_id := str(c.position.get("room", ""))
	if ContentDB.room(room_id).is_empty(): room_id = str(ContentDB.zone("jade_river_valley").get("start_room", "lf_fishers_hut"))
	var point := Vector2(float(c.position.get("x", 0)), float(c.position.get("y", 0)))
	if point == Vector2.ZERO: point = Vector2.INF
	game.in_world = true
	return load_room(c, room_id, str(c.position.get("portal", "")), point)

# ------------------------------------------------------------------ the character's memory of a room
## What the character remembers of a room: nodes gathered, chests opened, jars broken and foes slain.
func room_mem(c, room_id: String) -> Dictionary:
	if not c.rooms.has(room_id): c.rooms[room_id] = {"nodes": {}, "opened": {}, "broken": {}}
	if not c.rooms[room_id].has("slain"): c.rooms[room_id]["slain"] = {}   # older saves
	return c.rooms[room_id]

## The foes this character has slain in a room and not yet seen return: spawn point key -> the Clock time of the kill
## (EnemyAuthority reads it on entry to hold those points empty until they are due, however long the player was away).
func slain_foes(c, room_id: String) -> Dictionary:
	if c == null or not c.rooms.has(room_id): return {}
	return c.rooms[room_id].get("slain", {})

## Enemies: a spawn point's foe was slain (or tamed); the character remembers it with the room.
func apply_foe_slain(c, room_id: String, key: String) -> void:
	if c == null: return
	room_mem(c, room_id).slain[key] = Clock.now_utc()

## Enemies: the spawn point's foe is back; the memory of its kill is let go.
func apply_foe_returned(c, room_id: String, key: String) -> void:
	if c != null and c.rooms.has(room_id): c.rooms[room_id].get("slain", {}).erase(key)

# ------------------------------------------------------------------ tick
func tick(delta: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var c = game.active()
	if rt == null or c == null: return
	rt.elapsed += delta
	idle.tick_auto_hunt(c, delta)
	if float(ambush_cd.get(c.id, 0.0)) > 0.0: ambush_cd[c.id] = float(ambush_cd[c.id]) - delta
	herbs.tick_rare_herbs(c, rt, delta)
	# S43: the room clock moves movers, drops crumbled floors and raises water.
	rt.geometry.advance(delta)
	# T1: on the grid the rafts ride the same clock (TopdownTraverse.time; docs/architecture/topdown_mechanics.md).
	if rt.topdown != null and rt.topdown.traverse != null: rt.topdown.traverse.time = rt.geometry.time
	var st: ActorState = game.actor_state(c.id)
	if st != null: hazards.tick_hazard_volumes(c, rt, st, delta)
	# The spot a save resumes at: on the grid too (Phase 4), never in the prototype room, which is not a place.
	if st != null and st.surface != null and not rt.def.get("prototype", false):
		c.position.x = st.plane.x
		c.position.y = st.plane.y
		c.position.surface = st.surface.id if side_view(rt) else ""
		c.position.room = rt.room_id
	objects.tick_regrowth(rt, delta)
	loot.tick_loot(c, rt, st, delta)
	if rt.event.get("active", false): room_events.tick_event(c, rt, delta)
	elif rt.event.has("leaving"): room_events.tick_leave(c, rt, delta)
	races.tick_chase(c, rt, st)
	races.tick_run(c, rt, st)
	objects.attune_shrines(c, rt, st)
	arrays.attune_arrays(c, rt, st)
	hazards.tick_hazards(c, rt, st, delta)

# ------------------------------------------------------------------ the facade
## Every public method, forwarded to the part that does the work, among them the helpers tests and ObjectView call by
## name (public since audit 45's S11).

# Bandit ambushes (world_ambush.gd)
func ambush_chance(c, amb: Dictionary) -> float: return ambush.ambush_chance(c, amb)
func spring_ambush(c, amb: Dictionary) -> void: ambush.spring_ambush(c, amb)

# Rare herbs (world_herbs.gd)
func herb_state(o: Dictionary) -> Dictionary: return herbs.herb_state(o)
func wake_guardian(c, o: Dictionary, window: int) -> EnemyState: return herbs.wake_guardian(c, o, window)
func herb_guard_text(c, o: Dictionary) -> String: return herbs.herb_guard_text(c, o)
func guardian_wakes(o: Dictionary, st: ActorState) -> bool: return herbs.guardian_wakes(o, st)

# Portals, routes, teleports and Spirit Sense (world_portals.gd)
func portal_near(c, portal: Dictionary) -> bool: return portals.portal_near(c, portal)
static func seen_flag(room_id: String, portal_id: String) -> String: return WorldPortals.seen_flag(room_id, portal_id)
func prototype_gate(c, from_room: String, to_room: String) -> bool: return portals.prototype_gate(c, from_room, to_room)
func portal_state(c, portal: Dictionary) -> Dictionary: return portals.portal_state(c, portal)
func portal_open(c, room_id: String, p: Dictionary) -> bool: return portals.portal_open(c, room_id, p)
func route(c, from_room: String, to_room: String) -> Array: return portals.route(c, from_room, to_room)
func use_portal(c, portal_id: String, crossing: bool) -> Dictionary: return portals.use_portal(c, portal_id, crossing)
func apply_teleport(actor_id: String, target: String, portal := "") -> void: portals.apply_teleport(actor_id, target, portal)
func apply_return_to_shrine(actor_id: String) -> void: portals.apply_return_to_shrine(actor_id)
func teleport_fee(stone_id: String, c = null) -> int: return portals.teleport_fee(stone_id, c)
func teleport(c, stone_id: String) -> Dictionary: return portals.teleport(c, stone_id)
func sense_pulse(c) -> Dictionary: return portals.sense_pulse(c)

# Transfer arrays (world_arrays.gd)
static func array_flag(node_id: String) -> String: return WorldArrays.array_flag(node_id)
func array_attuned(c, node_id: String) -> bool: return arrays.array_attuned(c, node_id)
static func array_mine(c, node: Dictionary) -> bool: return WorldArrays.array_mine(c, node)
func array_open(c, from_room: String, from_id: String, to_id: String) -> bool: return arrays.array_open(c, from_room, from_id, to_id)
func attune_array(c, node_id: String) -> void: arrays.attune_array(c, node_id)
func array_destinations(c, node_id: String) -> Array: return arrays.array_destinations(c, node_id)
func array_view(c, node_id: String) -> Dictionary: return arrays.array_view(c, node_id)
func array_travel(c, from_id: String, to_id: String) -> Dictionary: return arrays.array_travel(c, from_id, to_id)

# Room objects (world_objects.gd)
func apply_node_depleted(c, object_id: String, regrow_s: float) -> void: objects.apply_node_depleted(c, object_id, regrow_s)
func object_visible(c, o: Dictionary) -> bool: return objects.object_visible(c, o)
func in_spar(npc: String) -> bool: return objects.in_spar(npc)
func climbable_open(c, climbable: Dictionary) -> Dictionary: return objects.climbable_open(c, climbable)
func open_key(o: Dictionary) -> String: return objects.open_key(o)
func object_available(c, o: Dictionary) -> Dictionary: return objects.object_available(c, o)
func hittable_objects(pv: Dictionary, facing: int, hitbox: Dictionary) -> Array: return objects.hittable_objects(pv, facing, hitbox)
func apply_object_hit(actor_id: String, o: Dictionary) -> void: objects.apply_object_hit(actor_id, o)
func toggle_gravity(c, object_id: String) -> Dictionary: return objects.toggle_gravity(c, object_id)

# Interact and the context button (world_context.gd)
func interact(c, object_id: String, pick := false) -> Dictionary: return context.interact(c, object_id, pick)
func reach_of(o: Dictionary) -> float: return context.reach_of(o)
func query_context(c) -> Dictionary: return context.query_context(c)
static func resource_node(o: Dictionary) -> bool: return WorldContext.resource_node(o)
static func offers_context(o: Dictionary) -> bool: return WorldContext.offers_context(o)
static func context_rank(o: Dictionary, calls := false) -> float: return WorldContext.context_rank(o, calls)
static func context_portal(p: Dictionary) -> bool: return WorldContext.context_portal(p)
func verb(o: Dictionary) -> String: return context.verb(o)

# Beast cores and loot (world_loot.gd)
static func beast_rank(def: Dictionary, level: int) -> int: return WorldLoot.beast_rank(def, level)
static func beast_core_for(def: Dictionary, level: int) -> String: return WorldLoot.beast_core_for(def, level)
static func core_chance(def: Dictionary, level: int) -> float: return WorldLoot.core_chance(def, level)
static func zone_shard(room_id: String) -> String: return WorldLoot.zone_shard(room_id)
func pick_up(c, uid: int) -> Dictionary: return loot.pick_up(c, uid)
## A drop another authority leaves in the room (Enemies: a boss that fled). `source` names it for the loot fountain.
func apply_loot_drop(c, drop: Dictionary, at: Vector2, alt: float, source: String) -> void: loot.drop_loot(c, drop, at, alt, source)
func on_actor_defeated(p: Dictionary) -> void: loot.on_actor_defeated(p)
func starter_drop(c, table: Dictionary, level: int, drop: Dictionary) -> void: loot.starter_drop(c, table, level, drop)
static func loot_spot(rt: RoomRuntime, at: Vector2, alt: float, spread: float, jitter: float) -> Vector3: return WorldLoot.loot_spot(rt, at, alt, spread, jitter)

# Rooftop chases and timed routes (world_races.gd)
static func chase_point(route: Array, speed: float, t: float) -> Dictionary: return WorldRaces.chase_point(route, speed, t)
static func chase_length(route: Array, speed: float) -> float: return WorldRaces.chase_length(route, speed)
func chase_done_today(c, object_id: String) -> bool: return races.chase_done_today(c, object_id)
func chase_view(c) -> Dictionary: return races.chase_view(c)
func start_chase(c, o: Dictionary) -> Dictionary: return races.start_chase(c, o)
func start_run(c, o: Dictionary) -> Dictionary: return races.start_run(c, o)
func route_board(route: Dictionary, week: int) -> Array: return races.route_board(route, week)
func route_record(c, route_id: String) -> Dictionary: return races.route_record(c, route_id)
func route_rank(route: Dictionary, week: int, seconds: float) -> int: return races.route_rank(route, week, seconds)
func finish_route(c, route: Dictionary, seconds: float) -> Dictionary: return races.finish_route(c, route, seconds)
func tick_chase(c, rt: RoomRuntime, st: ActorState) -> void: races.tick_chase(c, rt, st)
func tick_run(c, rt: RoomRuntime, st: ActorState) -> void: races.tick_run(c, rt, st)

# Hazards (world_hazards.gd)
func hazard_drift(actor_id: String) -> Vector2: return hazards.hazard_drift(actor_id)
func debug_hazard_phase(phase: String, k: float) -> void: hazards.debug_hazard_phase(phase, k)
func hazard_enter(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, rng: RandomNumberGenerator, calm: bool) -> void: hazards.hazard_enter(c, rt, st, h, hs, rng, calm)
func hazard_spots(rt: RoomRuntime, st: ActorState, h: Dictionary, rng: RandomNumberGenerator) -> Array: return hazards.hazard_spots(rt, st, h, rng)

# Starsea voyages (world_starsea.gd)
func best_vessel(c) -> String: return starsea.best_vessel(c)
func set_sail(c, route_id: String) -> Dictionary: return starsea.set_sail(c, route_id)
func apply_voyage_arrive(actor_id: String) -> void: starsea.apply_voyage_arrive(actor_id)

# Room events (world_room_events.gd)
func start_room_event(c, ev: Dictionary) -> void: room_events.start_room_event(c, ev)
func apply_rift_reward(actor_id: String, loot_table: String, level: int) -> void: room_events.apply_rift_reward(actor_id, loot_table, level)
func event_level(c, w: Dictionary) -> int: return room_events.event_level(c, w)
func start_event(c, rt: RoomRuntime, ev: Dictionary) -> void: room_events.start_event(c, rt, ev)
func tick_event(c, rt: RoomRuntime, delta: float) -> void: room_events.tick_event(c, rt, delta)
func end_event(c, rt: RoomRuntime, won: bool, reason := "") -> void: room_events.end_event(c, rt, won, reason)
func event_kill(p: Dictionary) -> void: room_events.event_kill(p)

# Nests, the Beast Tide and the Grove (world_nests.gd)
func nest_closes(king: String) -> float: return nests.nest_closes(king)
func tide_cfg() -> Dictionary: return nests.tide_cfg()
func tide_due(c) -> bool: return nests.tide_due(c)
func tide_days_left(c) -> int: return nests.tide_days_left(c)
func start_beast_tide(c) -> Dictionary: return nests.start_beast_tide(c)
func start_beast_trial(c) -> Dictionary: return nests.start_beast_trial(c)
func apply_trial_result(actor_id: String, won: bool) -> void: nests.apply_trial_result(actor_id, won)
func apply_tide_result(actor_id: String, won: bool) -> void: nests.apply_tide_result(actor_id, won)

# The Trial Tower (world_tower.gd)
func tower_floor(f: int) -> Dictionary: return tower.tower_floor(f)
func tower_cleared(c) -> int: return tower.tower_cleared(c)
func tower_swept_today(c, f: int) -> bool: return tower.tower_swept_today(c, f)
func climb_tower(c, f: int) -> Dictionary: return tower.climb_tower(c, f)
func apply_tower_clear(actor_id: String, f: int) -> void: tower.apply_tower_clear(actor_id, f)
func sweep_tower(c, f := -1) -> Dictionary: return tower.sweep_tower(c, f)

# Idle rooms, auto-hunt, auto-path and the direction mark (world_idle.gd)
func idle_allowed(room_id: String, kind: String) -> bool: return idle.idle_allowed(room_id, kind)
func auto_hunt_block(c) -> String: return idle.auto_hunt_block(c)
func auto_hunting(actor_id: String) -> bool: return idle.auto_hunting(actor_id)
func set_auto_hunt(c, on: bool) -> Dictionary: return idle.set_auto_hunt(c, on)
func start_auto_path(c, target: String, place := "") -> Dictionary: return idle.start_auto_path(c, target, place)
func auto_path_step(c) -> Dictionary: return idle.auto_path_step(c)
func auto_path_arrive(c) -> void: idle.auto_path_arrive(c)
func guide_step(c) -> Dictionary: return idle.guide_step(c)
func guide_target(c) -> String: return idle.guide_target(c)
static func place_name(room_id: String) -> String: return WorldIdle.place_name(room_id)
func auto_path_target(c) -> String: return idle.auto_path_target(c)
func auto_path_board(c, dock_id: String) -> Dictionary: return idle.auto_path_board(c, dock_id)
func tick_auto_hunt(c, delta: float) -> void: idle.tick_auto_hunt(c, delta)
