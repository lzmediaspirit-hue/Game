class_name WorldAuthority
extends Authority
## S17/S18/S32 · Owns the loaded room (RoomRuntime), portals and world objects,
## ground loot (rolled on actor_defeated), discovered teleport stones and the
## zone context. One room is loaded at a time.

const PICKUP_RADIUS := 48.0
const PORTAL_RADIUS := Vector2(64, 44)
const BREAKABLES := ["jar", "crate", "wine_jar"]
const TRAINING := ["training_stump", "training_dummy"]

var pending_transfer: Dictionary = {}   # presentation performs the fade, then calls complete_transfer
## Debug tools (S38, the Max Test APK): every portal, hidden way and climb is open, whatever its quest, flag or rank.
## A way to a room not built yet stays "Coming soon".
var debug_open_ways := false

func intents() -> Array:
	return ["use_portal", "interact", "teleport", "pick_up", "enter_world", "sense_pulse", "set_sail", "climb_tower", "sweep_floor",
		"set_auto_hunt", "auto_path"]

func subscribe() -> void:
	# S49 mobile conventions: auto-path follows the character room to room and stops at danger.
	GameEvents.subscribe("room_entered", _auto_path_room, 60)
	GameEvents.subscribe("hit_landed", _auto_path_danger, 60)
	# S43 rising water: a boss phase or a boss's fall moves the water in the room.
	for ev in ["boss_phase", "field_boss_defeated"]:
		GameEvents.subscribe(ev, _on_room_script.bind(ev), 50)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 50)
	GameEvents.subscribe("actor_defeated", _event_kill, 55)
	GameEvents.subscribe("bottleneck_reached", _on_bottleneck, 50)
	GameEvents.subscribe("hit_landed", _on_hit_during_event, 50)
	GameEvents.subscribe("room_entered", _on_room_entered_fates, 51)
	GameEvents.subscribe("room_entered", _on_room_entered_ambush, 52)
	GameEvents.subscribe("world_event_started", _on_world_event_started, 50)

## S45 treasure births (on the S49 calendar): World announces the fruit ripening in its room.
func _on_world_event_started(p: Dictionary) -> void:
	if str(p.get("event", "")) != "treasure_birth": return
	emit("treasure_birth_announced", {"room": str(p.get("room", "")), "item": str(CalendarRules.event("treasure_birth").get("item", "spirit_fruit")),
		"ends": float(p.get("ends", 0.0))})

## S48 Wandering Eye (a fate): one hidden way in each room entered shows itself.
func _on_room_entered_fates(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or game.room_rt == null or not game.progression.fate_flag(c, "reveal_hidden"): return
	for pt in game.room_rt.def.get("portals", []):
		if str(pt.get("type", "")) != "hidden": continue
		var f: String = "seen_" + game.room_rt.room_id + "_" + str(pt.id)
		if c.quests.has_flag(f): continue
		game.quest.apply_flag(c.id, f)
		emit("hidden_portal_revealed", {"actor": c.id, "portal": str(pt.id), "room": game.room_rt.room_id, "source": "wandering_eye"})
		return

# ------------------------------------------------------------------ bandit ambushes (S48 hidden cultivation)
var ambush_cd: Dictionary = {}   # actor -> seconds before the roads may spring another ambush (not saved)

## The chance that a road's ambush springs on this entry. Bandits judge the realm you show, not the one you hold:
## past their reach they leave you be, and a false realm (Concealment) looks like easy prey and doubles the odds.
func ambush_chance(c, amb: Dictionary) -> float:
	var k: Dictionary = ContentDB.stat_const("ambush", {})
	var cu: CultivatorState = c.cultivator
	var shown := ProgressionRules.level_for(game.progression.shown_realm(c), cu.progress_fraction())
	var lv: Array = amb.get("level", [1, 1])
	if shown > int(lv[1]) + int(k.get("reach", 8)): return 0.0
	var chance := float(k.get("chance", 0.06))
	if cu.false_realm != "": chance *= float(k.get("concealed_mult", 2.0))
	return chance

## A road room with an `ambush` rolls once as you come in: never on a first visit, never during a room event and not
## again until the cooldown has run.
func _on_room_entered_ambush(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	var rt: RoomRuntime = game.room_rt
	if c == null or rt == null or p.get("first_visit", false) or rt.event.get("active", false): return
	var amb: Dictionary = rt.def.get("ambush", {})
	if amb.is_empty() or float(ambush_cd.get(c.id, 0.0)) > 0.0: return
	if amb.has("requires") and not RequirementRules.passes(amb.requires, game.ctx(c)): return
	if Rng.stream(c.id, "ambush").randf() >= ambush_chance(c, amb): return
	spring_ambush(c, amb)

## The gang drops in on both sides of you. They are summoned foes: they fight like the road's own and scatter if
## you leave.
func spring_ambush(c, amb: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null: return
	var k: Dictionary = ContentDB.stat_const("ambush", {})
	ambush_cd[c.id] = float(k.get("cooldown_s", 900))
	var rng := Rng.stream(c.id, "ambush")
	var lv: Array = amb.get("level", [1, 1])
	var at := Vector2(float(c.position.get("x", 400)), float(c.position.get("y", 850)))
	var n := int(amb.get("count", 2))
	var off := float(k.get("offset", 360))
	for i in n:
		var side := 1.0 if i % 2 == 0 else -1.0
		var x := clampf(at.x + side * (off + 90.0 * floorf(i / 2.0)), 120.0, rt.width() - 120.0)
		game.enemies.spawn_at(str(amb.enemy), Vector2(x, at.y), rng.randi_range(int(lv[0]), int(lv[1])))
	emit("ambush_sprung", {"actor": c.id, "room": rt.room_id, "enemy": str(amb.enemy), "count": n, "concealed": c.cultivator.false_realm != ""})

# ------------------------------------------------------------------ rare herbs (S45)
var herb_clock := 0.0             # the rare-herb check runs once a second
var sensed_herbs: Dictionary = {} # object -> {until, ripe, seconds, dormant}: a Spirit Sense readout over the node

## A rare node's state now: {ripe, seconds, window, dormant}.
func herb_state(o: Dictionary) -> Dictionary:
	var now := Clock.now_utc()
	var st := HerbRules.ripen_state(o, now)
	st.dormant = not HerbRules.in_season(o, now)
	return st

## Once a second: a rare node that has just ripened says so, and its guardian wakes when you climb toward it.
func _tick_rare_herbs(c, rt: RoomRuntime, delta: float) -> void:
	herb_clock -= delta
	if herb_clock > 0.0: return
	herb_clock = 1.0
	var st: ActorState = game.actor_state(c.id)
	var whisper: float = game.pets.whisper_range(c)   # S46 Herb Whisper: an animal beside you reads the herbs near you
	for o in rt.def.get("objects", []):
		if o.type != "herb_patch" or not o.has("ripen"): continue
		var os: Dictionary = rt.objects.get(str(o.id), {})
		var hs := herb_state(o)
		var hat: Array = o.get("at", [0, 0])
		if whisper > 0.0 and st != null and st.plane.distance_to(Vector2(float(hat[0]), float(hat[1]))) <= whisper:
			sensed_herbs[str(o.id)] = {"until": game.sim_time + 1.5, "utc": Clock.now_utc(), "ripe": hs.ripe, "seconds": float(hs.seconds), "dormant": hs.dormant,
				"season": str(o.get("season", "")), "spent": os.get("state", "ready") == "depleted"}
		var ripe: bool = hs.ripe and not hs.dormant and os.get("state", "ready") == "ready"
		if ripe and not os.get("ripe", false):
			emit("herb_ripening", {"actor": c.id, "room": rt.room_id, "object": str(o.id), "item": str(o.item), "seconds": float(hs.seconds)})
			if not game.account.codex.has("rare_herbs"): game.quest.apply_codex("rare_herbs")
		os.ripe = ripe
		rt.objects[str(o.id)] = os
		if ripe and st != null and _guardian_wakes(o, st): wake_guardian(c, o, int(hs.window))

func _guardian_wakes(o: Dictionary, st: ActorState) -> bool:
	var g: Dictionary = ContentDB.config("garden").get("guardian", {})
	var at: Array = o.get("at", [0, 0])
	return absf(st.plane.x - float(at[0])) <= float(g.get("wake_px", 480)) \
		and st.altitude >= float(o.get("alt", 0)) - float(g.get("wake_below", 60))

## The guardian rises once per ripening (S45): an elite of the room's roster, on the ground under the node.
func wake_guardian(c, o: Dictionary, window: int) -> EnemyState:
	var gd: Dictionary = o.get("guardian", {})
	var rt: RoomRuntime = game.room_rt
	if gd.is_empty() or gd.get("boss", false) or rt == null: return null
	var mem := _room_mem(c, rt.room_id)
	if not mem.has("guardians"): mem.guardians = {}
	if int(mem.guardians.get(str(o.id), -999)) == window: return null
	mem.guardians[str(o.id)] = window
	var at: Array = o.get("at", [0, 0])
	var e: EnemyState = game.enemies.spawn_at(str(gd.enemy), Vector2(float(at[0]), 840.0), int(gd.get("level", -1)), {"elite": gd.get("elite", true)})
	if e == null: return null
	rt.guardians[str(o.id)] = e.uid
	emit("guardian_spawned", {"actor": c.id, "room": rt.room_id, "object": str(o.id), "enemy": str(gd.enemy), "uid": e.uid})
	return e

## Why a ripe node can't be picked yet ("" if it can). Kill the guardian, lure it past its leash, or pick the herb
## unseen: with Concealment, a guardian that hasn't noticed you doesn't stop you.
func herb_guard_text(c, o: Dictionary) -> String:
	var gd: Dictionary = o.get("guardian", {})
	var rt: RoomRuntime = game.room_rt
	if gd.is_empty() or rt == null: return ""
	var hs := herb_state(o)
	if not hs.ripe: return ""   # an early pick finds no guardian: they rise with the ripening
	var at: Array = o.get("at", [0, 0])
	var node := Vector2(float(at[0]), float(at[1]))
	var leash := float(ContentDB.config("garden").get("guardian", {}).get("leash_px", 600))
	var unseen: bool = "concealment" in c.cultivator.secret_arts
	var keeper: EnemyState = null
	if gd.get("boss", false):
		for e in rt.living_enemies():
			if e.def_id == str(gd.enemy) and e.plane.distance_to(node) <= leash: keeper = e
	else:
		if int(_room_mem(c, rt.room_id).get("guardians", {}).get(str(o.id), -999)) != int(hs.window):
			keeper = wake_guardian(c, o, int(hs.window))
		else:
			var uid := int(rt.guardians.get(str(o.id), -1))
			var e2 = rt.enemies.get(uid)
			if e2 != null and e2.alive and e2.plane.distance_to(node) <= leash: keeper = e2
	if keeper == null: return ""
	if unseen and not str(keeper.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"]: return ""
	return Tx.t("sim.world.herb_guarded") % ContentDB.name_of("enemies", keeper.def_id)

## Room events remember every blow the player takes: a flawless Heaven's Cleansing burns off residue (G1).
func _on_hit_during_event(p: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null or not rt.event.get("active", false) or str(p.get("target_kind", "")) != "player": return
	if int(p.get("amount", 0)) > 0: rt.event.hits_taken = int(rt.event.get("hits_taken", 0)) + 1

## S18: at the zone's ceiling the land itself is the limit.
func _on_bottleneck(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or not game.progression.at_zone_ceiling(c): return
	var zone := ContentDB.zone_of_room(str(c.position.get("room", "")))
	emit("zone_ceiling_reached", {"actor": c.id, "zone": str(zone.get("id", "")), "ceiling": str(p.get("realm_key", ""))})

## Crafting gathered a node: World owns room objects, their regrowth and the character's memory of them.
func apply_node_depleted(c, object_id: String, regrow_s: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var st: Dictionary = rt.objects.get(object_id, {"state": "ready"})
	st.state = "depleted"
	st.timer = regrow_s
	rt.objects[object_id] = st
	_room_mem(c, rt.room_id).nodes[object_id] = Clock.now_utc() + regrow_s
	emit("node_depleted", {"room": rt.room_id, "object": object_id})

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
		"auto_path": return start_auto_path(c, str(intent.get("target", "")))
		"set_sail": return set_sail(c, str(intent.get("route", "")))
	return fail("unknown_intent")

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
	var rt := RoomRuntime.new()
	rt.room_id = room_id
	rt.def = def
	rt.geometry.configure(compile_geometry(def))
	rt.next_uid = 1000
	game.room_rt = rt
	# Arrival: on the linked portal facing into the room, never mid-air.
	var arrival := point
	var facing := int(c.position.get("facing", 1))
	if not arrival.is_finite():
		var p := rt.portal_def(portal_id)
		if not p.is_empty():
			var at: Array = p.get("at", [0, 0])
			var inward := 1 if float(at[0]) < rt.width() * 0.5 else -1
			arrival = Vector2(float(at[0]) + inward * float(p.get("arrive_offset", 70)), float(at[1]) + float(p.get("arrive_dy", 0)))
			facing = inward
		else:
			var sp: Array = def.get("spawn_point", [200, 800])
			arrival = Vector2(float(sp[0]), float(sp[1]))
	var surf := _ground_at(rt, arrival)
	if surf == null:
		var sp2: Array = def.get("spawn_point", [200, 800])
		arrival = Vector2(float(sp2[0]), float(sp2[1]))
		surf = _ground_at(rt, arrival)
	arrival = rt.geometry.nearest_free(arrival, surf.height_at(arrival) if surf else 0.0, surf.stratum if surf else "ground")
	c.position = {"room": room_id, "portal": portal_id, "x": arrival.x, "y": arrival.y, "surface": surf.id if surf else "", "facing": facing}
	var first = not game.account.visited_rooms.has(room_id)
	game.account.visited_rooms[room_id] = true
	rt.first_visit = first
	var zone_old = ContentDB.room_zone.get(old, "")
	var zone_new = ContentDB.room_zone.get(room_id, "")
	if def.get("type", "") in ["town", "sect", "home"] or def.get("town", false): c.last_town = room_id
	_restore_object_states(c, rt)
	_init_hazards(c, rt)
	rt.arrival_protection = float(ContentDB.stat_const("combat.spawn_protection_s", 1.5))
	game.combat.apply_status(c.id, "spawn_protection", rt.arrival_protection, 1.0)
	emit("room_entered", {"actor": c.id, "room": room_id, "portal": portal_id, "first_visit": first, "x": arrival.x, "y": arrival.y,
		"facing": facing, "surface": c.position.surface, "zone": zone_new})
	if zone_new != zone_old: emit("zone_entered", {"actor": c.id, "zone": zone_new})
	if def.has("event"): _start_event(c, rt, def.event)
	game.crafting.check_raids(c)   # S45: what came for the garden while you were away
	return ok({"room": room_id, "x": arrival.x, "y": arrival.y, "facing": facing})

func _ground_at(rt: RoomRuntime, p: Vector2) -> WalkSurface:
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

func portal_near(c, portal: Dictionary) -> bool:
	var st: ActorState = game.actor_state(c.id)
	if st == null: return true
	var at: Array = portal.get("at", [0, 0])
	var r: Vector2 = PORTAL_RADIUS * float(portal.get("radius_scale", 1.0))
	return absf(st.plane.x - float(at[0])) <= r.x and absf(st.plane.y - float(at[1])) <= r.y

func portal_state(c, portal: Dictionary) -> Dictionary:
	var target := str(portal.get("to", ""))
	if ContentDB.room(target).is_empty():
		return {"open": false, "text": Tx.t("sim.world.coming_soon")}
	if debug_open_ways: return {"open": true, "text": ContentDB.name_of("rooms", target)}
	if portal.has("requires") and not RequirementRules.passes(portal.requires, game.ctx(c)):
		return {"open": false, "text": str(portal.get("locked_text", RequirementRules.first_failure_text(portal.requires, game.ctx(c))))}
	if portal.get("type", "") == "hidden" and not c.quests.has_flag("seen_" + game.room_rt.room_id + "_" + str(portal.id)):
		return {"open": false, "text": "", "hidden": true}
	return {"open": true, "text": ContentDB.name_of("rooms", target)}

func use_portal(c, portal_id: String, crossing: bool) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var p = game.room_rt.portal_def(portal_id)
	if p.is_empty(): return fail("unknown_portal")
	if not crossing and not portal_near(c, p): return fail("too_far")
	if game.combat.is_wounded(c.id): return fail("wounded")
	var state := portal_state(c, p)
	if not state.open:
		emit("portal_blocked", {"actor": c.id, "portal": portal_id, "text": state.text})
		return fail("sealed", {"text": state.text})
	if c.cultivator.meditating: game.progression.stop_meditation(c, "portal")
	# S49 fortune: the Hidden Grotto's way up leaves you where you fell.
	var back: Dictionary = c.cooldowns.get("grotto_return", {}) if p.get("fortune_return", false) else {}
	if not back.is_empty() and not ContentDB.room(str(back.room)).is_empty():
		emit("portal_used", {"actor": c.id, "portal": portal_id, "room": game.room_rt.room_id, "to": str(back.room), "hidden": false})
		c.cooldowns.erase("grotto_return")
		return load_room(c, str(back.room), "", Vector2(float(back.x), float(back.y)))
	emit("portal_used", {"actor": c.id, "portal": portal_id, "room": game.room_rt.room_id, "to": str(p.to), "hidden": str(p.get("type", "")) == "hidden"})
	var r := load_room(c, str(p.to), str(p.get("to_portal", "")))
	return r

func apply_teleport(actor_id: String, target: String, portal := "") -> void:
	var c = game.character(actor_id)
	if c == null: return
	match target:
		"last_town":
			var town = c.last_town if c.last_town != "" else "lf_village"
			load_room(c, town, "town_arrival")
		"dungeon_exit":
			var exit_room = str(game.room_rt.def.get("dungeon_exit", c.last_town)) if game.room_rt else c.last_town
			load_room(c, exit_room if exit_room != "" else "lf_village", "")
		_:
			if not ContentDB.room(target).is_empty(): load_room(c, target, portal)

func apply_return_to_shrine(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	if c.last_shrine.is_empty():
		var start := str(ContentDB.zone("jade_river_valley").get("start_room", "lf_fishers_hut"))
		var sr = c.last_town if c.last_town != "" else start
		load_room(c, sr, "")
		return
	load_room(c, str(c.last_shrine.room), "", Vector2(float(c.last_shrine.x) + 50, float(c.last_shrine.y) + 20))

## S18: a stone in another zone answers across the sky, at five times its fee.
func teleport_fee(stone_id: String, c = null) -> int:
	var stone := ContentDB.entry("teleport_stones", stone_id)
	var fee := int(stone.get("fee_shards", 1))
	# An Elder's token (Sage Sovereign 1) calls its bearer home to the training sect for nothing.
	if c != null and str(stone.get("sect", "")) != "" and str(stone.get("sect", "")) == str(c.training_sect.get("id", "")):
		var elder := str(ContentDB.entry("sects", str(stone.sect)).get("token", "")).replace("_token", "_elder_token")
		if c.inventory.count(elder) > 0: return 0
	if game.room_rt != null and ContentDB.room_zone.get(str(stone.get("room", "")), "") != ContentDB.room_zone.get(game.room_rt.room_id, ""):
		fee *= int(ContentDB.stat_const("teleport_cross_zone_mult", 5))
	return fee

func teleport(c, stone_id: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "teleport_stones"): return fail("locked")
	if not game.account.teleports.has(stone_id): return fail("undiscovered")
	var stone := ContentDB.entry("teleport_stones", stone_id)
	if stone.is_empty(): return fail("unknown_stone")
	var fee := teleport_fee(stone_id, c)
	if c.inventory.count("spirit_stone_shard") < fee: return fail("no_fee", {"text": Tx.t("sim.world.needs_spirit_stone_shard") % fee})
	game.inventory.apply_remove(c.id, "spirit_stone_shard", fee, "teleport")
	emit("teleported", {"actor": c.id, "stone": stone_id})
	return load_room(c, str(stone.room), "", Vector2(float(stone.at[0]) + 60, float(stone.at[1]) + 10))

## Spirit Sense (S17, SA1/SA2): a soul pulse that reveals hidden portals and
## fog-hidden monsters within the sense radius.
func sense_pulse(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_sense"): return fail("locked", {"text": Unlocks.locked_text("spirit_sense")})
	if c.pools.cooldown("sense") > 0.0: return fail("cooldown")
	var cost := 10.0
	if StatRules.gate_flag(c, "sense_cost_25"): cost *= float(ContentDB.stat_const("gates", {}).get("sense_cost_mult", 0.75))   # S10 Spirit 25
	if c.pools.get_value("soul") < cost: return fail("no_soul", {"text": Tx.t("sim.world.not_enough_soul")})
	c.pools.set_value("soul", c.pools.get_value("soul") - cost)
	c.pools.cooldowns["sense"] = 6.0
	var st: ActorState = game.actor_state(c.id)
	var here: Vector2 = st.plane if st else Vector2(float(c.position.x), float(c.position.y))
	var radius := maxf(420.0, c.stats.value("sense_radius"))
	var found := 0
	if game.room_rt:
		for p in game.room_rt.def.get("portals", []):
			if p.get("type", "") != "hidden" or not Unlocks.is_unlocked(c.id, "hidden_portals"): continue
			var at: Array = p.get("at", [0, 0])
			var f = "seen_" + game.room_rt.room_id + "_" + str(p.id)
			if here.distance_to(Vector2(float(at[0]), float(at[1]))) <= radius and not c.quests.has_flag(f):
				game.quest.apply_flag(c.id, f)
				emit("hidden_portal_revealed", {"actor": c.id, "portal": str(p.id), "room": game.room_rt.room_id})
				found += 1
		for e in game.room_rt.living_enemies():
			if e.hidden and here.distance_to(e.plane) <= radius:
				e.hidden = false
				e.ai["sensed"] = 8.0
	# S45: rare herbs in reach show when they ripen (or how long they stay ripe, or their season).
	var herbs := 0
	if game.room_rt:
		for o in game.room_rt.def.get("objects", []):
			if o.type != "herb_patch" or not o.has("ripen"): continue
			var at2: Array = o.get("at", [0, 0])
			if here.distance_to(Vector2(float(at2[0]), float(at2[1]))) > radius: continue
			var hs := herb_state(o)
			sensed_herbs[str(o.id)] = {"until": game.sim_time + 8.0, "utc": Clock.now_utc(), "ripe": hs.ripe, "seconds": float(hs.seconds), "dormant": hs.dormant,
				"season": str(o.get("season", "")), "spent": game.room_rt.objects.get(str(o.id), {}).get("state", "ready") == "depleted"}
			herbs += 1
	emit("spirit_sense_pulsed", {"actor": c.id, "x": here.x, "y": here.y, "radius": radius, "found": found, "herbs": herbs})
	emit("system_used", {"actor": c.id, "system": "spirit_sense"})
	return ok({"found": found})

# ------------------------------------------------------------------ objects
func _room_mem(c, room_id: String) -> Dictionary:
	if not c.rooms.has(room_id): c.rooms[room_id] = {"nodes": {}, "opened": {}, "broken": {}}
	return c.rooms[room_id]

func _restore_object_states(c, rt: RoomRuntime) -> void:
	var mem := _room_mem(c, rt.room_id)
	var now := Clock.now_utc()
	for o in rt.def.get("objects", []):
		var id := str(o.get("id", ""))
		var st := {"state": "ready", "timer": 0.0, "hits": 0}
		if o.type in ["herb_patch", "ore_vein", "star_sight"] and float(mem.nodes.get(id, 0.0)) > now:
			st.state = "depleted"
			st.timer = float(mem.nodes[id]) - now
		if o.type in ["chest"] and mem.opened.has(open_key(o)): st.state = "open"
		if o.type in BREAKABLES and float(mem.broken.get(id, 0.0)) > now:
			st.state = "broken"
			st.timer = float(mem.broken[id]) - now
		rt.objects[id] = st

func object_visible(c, o: Dictionary) -> bool:
	if o.has("visible_if") and not RequirementRules.passes(o.visible_if, game.ctx(c)): return false
	if o.has("hidden_if") and RequirementRules.passes(o.hidden_if, game.ctx(c)): return false
	if str(o.get("type", "")) == "egg_nest" and nest_closes(str(o.get("king", ""))) <= Clock.now_utc(): return false   # S46: only while open
	# S43 rule 15: a rooftop thief is on his street until you have chased him today (caught or not).
	if o.has("chase") and c != null and chase_done_today(c, str(o.id)) and str(chases.get(c.id, {}).get("object", "")) != str(o.id): return false
	return true

## A sealed climbable (S43: library floors, lofts) opens when its requirement is met.
func climbable_open(c, climbable: Dictionary) -> Dictionary:
	if climbable.has("requires") and not debug_open_ways and not RequirementRules.passes(climbable.requires, game.ctx(c)):
		return {"ok": false, "text": str(climbable.get("locked_text", RequirementRules.first_failure_text(climbable.requires, game.ctx(c))))}
	return {"ok": true}

## A chest that `reopens` with a calendar event is opened once per occurrence (S49); any other chest once.
func open_key(o: Dictionary) -> String:
	if str(o.get("reopens", "")) == "": return str(o.id)
	# S49 fortune: the Hidden Grotto's chest fills again for each fall that ends there.
	if str(o.reopens) == "fortune":
		var fc = game.active()
		return "%s@%d" % [str(o.id), int(fc.relations.fortune.get("grotto_n", 0)) if fc != null else 0]
	var occ: Dictionary = game.calendar.active_of(str(o.reopens))
	return "%s@%d" % [str(o.id), int(occ.get("k", -1))]

func object_available(c, o: Dictionary) -> Dictionary:
	if not object_visible(c, o): return {"ok": false, "text": "", "hidden": true}
	if o.has("requires") and not RequirementRules.passes(o.requires, game.ctx(c)):
		return {"ok": false, "text": str(o.get("locked_text", RequirementRules.first_failure_text(o.requires, game.ctx(c))))}
	var st: Dictionary = game.room_rt.objects.get(str(o.id), {})
	if st.get("state", "ready") in ["depleted", "broken", "open"]: return {"ok": false, "text": "", "spent": true}
	# S45: a rare herb out of its season lies dormant (seasons never gate progression).
	if o.type == "herb_patch" and not HerbRules.in_season(o, Clock.now_utc()):
		return {"ok": false, "text": Tx.t("sim.world.herb_dormant") % ContentDB.name_of("seasons", str(o.season)), "dormant": true}
	if o.type == "egg_nest" and c.quests.has_flag(_nest_flag(str(o.get("king", "")))): return {"ok": false, "text": Tx.t("sim.world.nest_taken")}
	if o.type == "beast_trial_stone" and int(c.cooldowns.get("grove_day", -1)) == Clock.reset_day(Clock.now_utc()):
		return {"ok": false, "text": Tx.t("sim.world.grove_done")}
	if o.type == "beast_tide_drum" and not tide_due(c):
		return {"ok": false, "text": Tx.t("sim.world.tide_not_due") % maxi(1, tide_days_left(c))}
	return {"ok": true, "text": ""}

func hittable_objects(pv: Dictionary, facing: int, hitbox: Dictionary) -> Array:
	var out: Array = []
	var c = game.active()
	if game.room_rt == null or c == null: return out
	for o in game.room_rt.def.get("objects", []):
		if not (o.type in BREAKABLES or o.type in TRAINING): continue
		if not object_visible(c, o): continue
		var st: Dictionary = game.room_rt.objects.get(str(o.id), {})
		if st.get("state", "ready") == "broken": continue
		var at: Array = o.get("at", [0, 0])
		var view := {"x": float(at[0]), "y": float(at[1]), "alt": float(o.get("alt", 0)), "half_width": 14.0, "height": 40.0}
		if CombatAuthority.hit_test(pv, facing, hitbox, view): out.append(o)
	return out

func apply_object_hit(actor_id: String, o: Dictionary) -> void:
	var c = game.character(actor_id)
	var id := str(o.id)
	var st: Dictionary = game.room_rt.objects.get(id, {"state": "ready", "hits": 0})
	st.hits = int(st.get("hits", 0)) + 1
	game.room_rt.objects[id] = st
	var at: Array = o.get("at", [0, 0])
	emit("object_hit", {"actor": actor_id, "object": id, "type": o.type, "x": float(at[0]), "y": float(at[1]), "hits": st.hits})
	if o.type in BREAKABLES and int(st.hits) >= int(o.get("hp", 1)):
		st.state = "broken"
		st.timer = float(o.get("respawn_s", 300))
		_room_mem(c, game.room_rt.room_id).broken[id] = Clock.now_utc() + st.timer
		var drop := LootRules.roll(str(o.get("loot", "jar_valley_low")), Rng.stream(actor_id, "loot"), int(o.get("level", 1)),
			c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": true})
		_drop_loot(c, drop, Vector2(float(at[0]), float(at[1])), 0.0)
		emit("object_broken", {"actor": actor_id, "object": id, "type": o.type})

## `pick` (S45): go straight to the harvest at a rare herb, past the Pick / Dig it up choice.
func interact(c, object_id: String, pick := false) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var o = game.room_rt.object_def(object_id)
	if o.is_empty(): return fail("unknown_object")
	var st: ActorState = game.actor_state(c.id)
	var at: Array = o.get("at", [0, 0])
	if st != null and st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > float(o.get("radius", 110)) + 20.0:
		return fail("too_far")
	if st != null and absf(st.altitude - float(o.get("alt", 0.0))) > 48.0:
		return fail("out_of_reach", {"text": Tx.t("sim.world.out_of_reach_from_here")})
	var avail := object_available(c, o)
	if avail.get("dormant", false) and not game.account.codex.has("seasons"): game.quest.apply_codex("seasons")
	if not avail.ok and o.type != "npc":
		return fail("unavailable", {"text": avail.text})
	if o.type == "herb_patch" and o.has("ripen") and not game.account.codex.has("rare_herbs"): game.quest.apply_codex("rare_herbs")
	var result := ok({"type": o.type})
	match str(o.type):
		"npc":
			if o.has("chase"): return start_chase(c, o)   # S43 rule 15: the rooftop thief bolts
			return game.quest.talk(c, str(o.npc))
		"route_stone":
			return start_run(c, o)
		"shrine":
			c.last_shrine = {"room": game.room_rt.room_id, "x": float(at[0]), "y": float(at[1]), "object": object_id}
			game.combat.apply_resource_change(c.id, "hp", c.pools.max_hp, "shrine")
			if c.pools.max_qi > 0: game.combat.apply_resource_change(c.id, "qi", c.pools.max_qi, "shrine")
			GameEvents.save_pending = true
			result.text = Tx.t("sim.world.the_shrine_remembers_you_wounds")
		"herb_patch", "ore_vein", "fishing_spot", "star_sight":
			# S45: with a Spirit Spade and Expert gathering, a rare herb can be dug up whole instead of picked.
			if o.type == "herb_patch" and o.has("ripen") and not pick and game.crafting.can_transplant(c):
				return ok({"dialogue": {"npc": "", "speaker": ContentDB.item_name(str(o.item)), "portrait": {}, "lines": [Tx.t("sim.world.rare_herb_choice")],
					"choices": [{"text": Tx.t("sim.world.pick_it"), "page": "_harvest", "args": {"object": object_id}},
						{"text": Tx.t("sim.world.dig_it_up") % int(round(game.crafting.transplant_death(c) * 100.0)), "intent": {"type": "transplant", "object": object_id}},
						{"text": Tx.t("sim.world.leave_it"), "close": true}]}})
			return game.crafting.gather(c, o)
		"starsea_dock":
			return set_sail(c, str(o.get("route", "")))
		"chest":
			var s: Dictionary = game.room_rt.objects.get(object_id, {})
			s.state = "open"
			_room_mem(c, game.room_rt.room_id).opened[open_key(o)] = true
			var chest_lv := int(o.get("level", 0))
			if chest_lv <= 0: chest_lv = ProgressionRules.level(c)   # a chest of no fixed level fits its finder (the grotto)
			var drop := LootRules.roll(str(o.get("loot", "chest_valley")), Rng.stream(c.id, "loot"), chest_lv,
				c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": not Unlocks.is_unlocked(c.id, "weapons")})
			_drop_loot(c, drop, Vector2(float(at[0]), float(at[1])), 0.0)
		"teleport_stone":
			var sid := str(o.get("stone", object_id))
			if not game.account.teleports.has(sid):
				game.account.teleports[sid] = true
				emit("teleport_discovered", {"actor": c.id, "id": sid})
			result.open_page = "teleport"
		"lifting_stone":
			emit("object_hit", {"actor": c.id, "object": object_id, "type": o.type, "x": float(at[0]), "y": float(at[1]), "hits": 1})
			result.channel = 3.0
		"pickup":
			var item := str(o.get("item", ""))
			var mem := _room_mem(c, game.room_rt.room_id)
			mem.opened[object_id] = true
			game.room_rt.objects[object_id] = {"state": "open"}
			game.inventory.apply_add(c.id, item, int(o.get("count", 1)), "pickup")
		"inspect":
			result.text = str(o.get("text", ""))
			if o.has("open_page"): result.open_page = str(o.open_page)
			if o.has("page_args"): result.page_args = o.page_args
			# Some things teach you something the first time you look (a Codex entry): once per character.
			if o.has("effects") and not c.quests.has_flag("inspected_" + object_id):
				c.quests.flags["inspected_" + object_id] = true
				game.apply_effects(c.id, o.effects, "inspect:" + object_id)
		"rite_circle":
			return game.quest.start_set_piece(c, str(o.get("event", "")))
		"storage_chest":
			result.open_page = "storage"
		"bath_station":
			# S44: the bath is a seclusion focus, chosen on the Seclusion page.
			result.open_page = "seclusion"
		"cooking_pot", "alchemy_furnace", "earth_vent", "forge_anvil", "formation_table", "garden_bed", "chart_table", "shipyard_slip":
			result.open_page = str(o.get("page", {"cooking_pot": "cooking", "alchemy_furnace": "alchemy", "earth_vent": "alchemy", "forge_anvil": "forge",
				"formation_table": "formations", "garden_bed": "garden", "chart_table": "charts", "shipyard_slip": "vessels"}[o.type]))
		"notice_board":
			result.open_page = "notice_board"
		"signpost":
			result.text = str(o.get("text", ""))
		"insight_stone":
			result.text = str(o.get("text", Tx.t("sim.world.meditate_here")))
			# S49 leisure arts: a chess problem is carved beside every insight stone; one answer a day.
			if game.progression.chess_open(c, object_id):
				return ok({"dialogue": {"npc": "", "speaker": Tx.t("sim.world.chess_speaker"), "portrait": {}, "lines": [Tx.t("sim.world.chess_line")],
					"choices": [{"text": Tx.t("sim.world.chess_study"), "page": "chess", "args": {"site": object_id}},
						{"text": Tx.t("sim.world.chess_meditate"), "close": true}]}})
		"qi_spring":
			# S45: a gardener bottles the spring's water, three bottles a day; otherwise it is a place to meditate.
			var sw: Dictionary = game.crafting.bottle_spring_water(c) if Unlocks.is_unlocked(c.id, "herb_garden") else {}
			result.text = str(sw.get("text", o.get("text", Tx.t("sim.world.meditate_here"))))
		"spar_post":
			return game.quest.start_spar_from_object(c, o)
		"defence_drum":
			return game.sect.start_defence(c)
		"egg_nest":
			# S46: the fallen King's nest gives each character one Rare egg per opening.
			var king := ContentDB.entry("beast_kings", str(o.get("king", "")))
			game.quest.apply_flag(c.id, _nest_flag(str(o.get("king", ""))))
			game.inventory.apply_add(c.id, str(king.get("nest", {}).get("item", "rare_spirit_egg")), 1, "king_nest")
			result.text = Tx.t("sim.world.nest_egg")
		"beast_tide_drum":
			return start_beast_tide(c)
		"spirit_mine":
			return game.sect.mine_dialogue(c, str(o.get("mine", "")))
		"rift_tear":
			return game.calendar.open_rift(c)
		"treasure_birth":
			return game.calendar.open_treasure(c)
		"beast_trial_stone":
			return start_beast_trial(c)
		"treasure_plot":
			var tp: Dictionary = game.crafting.tend_treasure_plot(c, o)
			result.text = str(tp.get("text", ""))
		"treasure_tree":
			var tt: Dictionary = game.progression.consult_jade_tree(c)
			result.text = str(tt.get("text", ""))
		"bell":
			var bs: Dictionary = game.room_rt.objects.get(object_id, {})
			bs.state = "open"
			game.room_rt.objects[object_id] = bs
			emit("bell_rung", {"actor": c.id, "object": object_id})
		_:
			pass
	if o.has("set_flag"): game.quest.apply_flag(c.id, str(o.set_flag))
	emit("object_interacted", {"actor": c.id, "object": object_id, "type": o.type, "room": game.room_rt.room_id})
	return result

## Context action for the Attack button (Part 9.9): quest target → NPC → loot → gather → travel.
func query_context(c) -> Dictionary:
	if game.room_rt == null or c == null: return {}
	var st: ActorState = game.actor_state(c.id)
	if st == null: return {}
	var best := {}
	var best_score := INF
	for o in game.room_rt.def.get("objects", []):
		if o.type in BREAKABLES or o.type in TRAINING or o.type in ["decor", "air_pocket", "route_finish"]: continue
		if not object_visible(c, o): continue
		if o.has("chase") and str(chases.get(c.id, {}).get("object", "")) == str(o.id): continue   # he is off over the roofs
		var at: Array = o.get("at", [0, 0])
		var d: float = st.plane.distance_to(Vector2(float(at[0]), float(at[1])))
		if d > float(o.get("radius", 110)): continue
		var avail := object_available(c, o)
		if avail.get("spent", false): continue
		var priority := 3.0
		if o.type == "npc":
			priority = 1.0 if game.quest.npc_marker(c, str(o.npc)) != "" else 2.0
		elif o.type in ["herb_patch", "ore_vein", "fishing_spot", "star_sight"]: priority = 4.0
		elif o.type == "pickup": priority = 0.5
		var score: float = priority * 1000.0 + d
		if score < best_score:
			best_score = score
			best = {"object": str(o.id), "type": o.type, "label": _verb(o), "ok": avail.ok, "text": avail.text, "npc": str(o.get("npc", ""))}
	if best.is_empty():
		for p in game.room_rt.def.get("portals", []):
			if p.get("type", "edge") == "edge" and not p.get("press_up", false): continue
			if portal_near(c, p):
				var ps := portal_state(c, p)
				if ps.get("hidden", false): continue
				best = {"portal": str(p.id), "type": "portal", "label": Tx.t("sim.world.enter"), "ok": ps.open, "text": ps.text, "target": str(p.get("to", ""))}
				break
	return best

func _verb(o: Dictionary) -> String:
	if o.has("chase"): return Tx.t("sim.world.chase")
	match str(o.type):
		"npc": return Tx.t("sim.world.talk")
		"route_stone": return Tx.t("sim.world.begin")
		"herb_patch": return Tx.t("sim.world.gather")
		"ore_vein": return Tx.t("sim.world.mine")
		"fishing_spot": return Tx.t("sim.world.fish")
		"chest", "storage_chest": return Tx.t("sim.world.open")
		"shrine": return Tx.t("sim.world.pray")
		"pickup": return Tx.t("sim.world.take")
		"lifting_stone": return Tx.t("sim.world.lift")
		"cooking_pot": return Tx.t("sim.world.cook")
		"alchemy_furnace", "earth_vent": return Tx.t("sim.world.refine")
		"forge_anvil": return Tx.t("sim.world.forge")
		"bath_station": return Tx.t("sim.world.bathe")
		"teleport_stone": return Tx.t("sim.world.travel")
		"notice_board", "signpost", "inspect": return Tx.t("sim.world.read")
		"rite_circle": return Tx.t("sim.world.begin")
		"spar_post": return Tx.t("sim.world.spar")
		"bell", "beast_tide_drum": return Tx.t("sim.world.ring")
		"rift_tear": return Tx.t("sim.world.touch")
		"treasure_birth": return Tx.t("sim.world.reach")
		"beast_trial_stone": return Tx.t("sim.world.begin")
		"egg_nest": return Tx.t("sim.world.take")
		"treasure_plot", "garden_bed": return Tx.t("sim.world.tend")
		"treasure_tree": return Tx.t("sim.world.sit_beneath")
		"star_sight": return Tx.t("sim.world.observe")
		"chart_table": return Tx.t("sim.world.chart")
		"shipyard_slip": return Tx.t("sim.world.build")
		"starsea_dock": return Tx.t("sim.world.set_sail")
		"spirit_mine": return Tx.t("sim.world.survey")
	return Tx.t("sim.world.use")

# ------------------------------------------------------------------ beast ranks and cores (S46)
## A beast's rank from its Level (1-9 is rank 1 ... 73+ is rank 9); 0 for anything that is not a beast.
static func beast_rank(def: Dictionary, level: int) -> int:
	if str(def.get("race", "beast")) != "beast": return 0
	return clampi((maxi(1, level) - 1) / 9 + 1, 1, 9)

## The core a beast of this Level carries (by its element and rank tier), or "" below rank 2.
static func beast_core_for(def: Dictionary, level: int) -> String:
	var rank := beast_rank(def, level)
	var cfg: Dictionary = ContentDB.config("pet_growth").get("cores", {})
	if rank < int(cfg.get("min_rank", 2)): return ""
	var tier := ""
	for t in cfg.get("tiers", {}):
		var band: Array = cfg.tiers[t]
		if rank >= int(band[0]) and rank <= int(band[1]): tier = str(t)
	var el := str(def.get("element", "earth")).trim_prefix("hollow_")
	if el in ["hollow", "none", ""]: el = "soul" if el == "hollow" else "earth"
	var id := "%s_core_%s" % [el, tier]
	if ContentDB.item(id).is_empty(): id = "%s_core_%s" % [CombatRules.parent_element(el), tier]   # a sub-element's parent
	return id if ContentDB.item(id).size() > 0 else ""

static func core_chance(def: Dictionary, level: int) -> float:
	return float(ContentDB.config("pet_growth").get("cores", {}).get("chance_per_rank", 0.02)) * beast_rank(def, level)

# ------------------------------------------------------------------ loot (S32)
## The next soul memory the account has not read ("" once all are read).
func _next_soul_memory() -> String:
	for i in range(1, 100):
		var id := "soul_memory_%d" % i
		if not ContentDB.has_entry("codex", id): return ""
		if not game.account.codex.has(id): return id
	return ""

func _on_actor_defeated(p: Dictionary) -> void:
	if p.get("victim_kind", "") != "enemy" or game.room_rt == null: return
	var c = game.character(str(p.get("killer", game.active_id)))
	if c == null: c = game.active()
	if c == null: return
	var def := ContentDB.entry("enemies", str(p.def))
	if def.is_empty(): return
	var rng := Rng.stream(c.id, "loot")
	var drop := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate") + game.pets.trait_bonus(c, "drop_chance"), c.stats.value("coin_find"),
		{"no_equipment": not Unlocks.is_unlocked(c.id, "weapons"), "needs": game.quest.item_needs(c)})
	if bool(p.get("elite", false)) and def.get("role", "normal") == "normal":
		var extra := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate"), c.stats.value("coin_find"))
		drop.items.append_array(extra.items)
		drop.coins = LootRules.coins_for(int(p.level), 6.0, c.stats.value("coin_find"))
		if rng.randf() < 0.25: drop.equipment.append({"level": int(p.level), "min_quality": "fine"})
	if bool(p.get("summoned", false)): drop.equipment.clear()
	# Quest-only items drop only while a quest needs them.
	drop.items = drop.items.filter(func(it): return not ContentDB.item(it.item).get("quest_item", false) or game.quest.needs_item(c, str(it.item)))
	# First kill of each species per character gives a bonus roll.
	if not c.collection_first_kills.has(str(p.def)):
		c.collection_first_kills[str(p.def)] = true
		var bonus := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), 1.0, 0.0, {"no_equipment": true})
		drop.items.append_array(bonus.items)
	# S48 Soul Search: a searched elite gives up what it hid (one more roll) and a memory for the Codex.
	var sm: Dictionary = game.combat.searched.get(str(p.get("victim", "")), {})
	if not sm.is_empty():
		game.combat.searched.erase(str(p.victim))
		var hid := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate"), 0.0, {"no_equipment": true})
		drop.items.append_array(hid.items)
		var memory := _next_soul_memory()
		if memory != "": game.apply_effects(c.id, [{"kind": "codex", "entry": memory}], "soul_search")
		emit("soul_searched", {"actor": c.id, "def": str(p.def), "memory": memory, "items": hid.items.size()})
	# Taken whole by the Taming Cauldron (S47): its materials at full count, no loot roll, no coins, nothing it wore.
	if game.combat.captured.has(str(p.get("victim", ""))):
		game.combat.captured.erase(str(p.victim))
		drop = {"items": LootRules.capture_materials(str(def.get("loot", p.def))), "coins": 0, "equipment": []}
		emit("beast_captured", {"actor": c.id, "def": str(p.def), "items": drop.items.size()})
	# S46 beast cores: rank 2 and up, 2% a rank, by the beast's element and rank tier (their own stream).
	var core := beast_core_for(def, int(p.level))
	if core != "" and not bool(p.get("summoned", false)) and Rng.stream(c.id, "cores").randf() < core_chance(def, int(p.level)):
		drop.items.append({"item": core, "count": 1})
	# S46 pet skill books from bosses and elites, on their own stream.
	var book: Dictionary = def.get("pet_book", {})
	if not book.is_empty() and not bool(p.get("summoned", false)) and (bool(p.get("elite", false)) or not book.get("elite_only", false)) \
			and Rng.stream(c.id, "books").randf() < float(book.get("chance", 0.0)):
		drop.items.append({"item": str(book.item), "count": 1})
	# S45 Spirit Soil: 1% from a beast of rank 3 or above (Level 19+), on its own stream so the loot roll is untouched.
	var soil: Dictionary = ContentDB.config("garden").get("spirit_soil", {})
	if str(def.get("race", "")) == "beast" and int(p.level) >= int(soil.get("min_level", 19)) and not bool(p.get("summoned", false)) \
			and Rng.stream(c.id, "garden").randf() < float(soil.get("chance", 0.01)):
		drop.items.append({"item": "spirit_soil", "count": 1})
	# A boss's one-time treasure (a Heavenly Flame, G1): guaranteed on its first defeat, outside the loot roll.
	# An elite can carry one too (the Weeping Lantern's Mist Lantern Flame, S44): only the elite of its kind drops it.
	var once: Array = def.get("first_defeat", []).duplicate()
	if p.get("elite", false): once.append_array(def.get("elite_first_defeat", []))
	for it in once:
		var flag := "first_defeat:%s:%s" % [str(p.def), str(it)]
		if c.quests.has_flag(flag): continue
		game.quest.apply_flag(c.id, flag)
		drop.items.append({"item": str(it), "count": 1})
	_drop_loot(c, drop, Vector2(float(p.x), float(p.y)), float(p.get("alt", 0.0)))

func _drop_loot(c, drop: Dictionary, at: Vector2, alt: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var rng := Rng.stream(c.id, "loot")
	var drops: Array = []
	for it in drop.get("items", []):
		if ContentDB.item(str(it.item)).is_empty() or int(it.count) <= 0: continue
		drops.append({"item": str(it.item), "count": int(it.count)})
	var allow_weapons: bool = Unlocks.is_unlocked(c.id, "weapons")
	for eq in drop.get("equipment", []):
		var inst := LootRules.make_equipment(Rng.stream(c.id, "affix"), int(eq.level), str(eq.min_quality), c.stats.value("fortune"), allow_weapons, c.inventory.next_uid)
		if inst.is_empty(): continue
		c.inventory.next_uid += 1
		drops.append({"item": inst.id, "count": 1, "instance": inst})
	if int(drop.get("coins", 0)) > 0: drops.append({"coins": int(LootRules.zone_coins(rt.room_id, int(drop.coins)).amount)})
	var i := 0
	var items_out: Array = []
	for d in drops:
		var spread := (i - (drops.size() - 1) * 0.5) * 22.0
		var entry := {"uid": rt.uid(), "item": str(d.get("item", "")), "count": int(d.get("count", 0)), "coins": int(d.get("coins", 0)),
			"instance": d.get("instance", {}), "x": at.x + spread, "y": clampf(at.y + rng.randf_range(-6, 6), 626, 956), "alt": alt,
			"ttl": 120.0 if d.has("coins") else 60.0, "age": 0.0}
		entry.quality = str(d.get("instance", {}).get("quality", "common"))
		rt.loot.append(entry)
		items_out.append(entry.duplicate())
		i += 1
	if not items_out.is_empty():
		emit("loot_dropped", {"room": rt.room_id, "items": items_out, "x": at.x, "y": at.y})

func pick_up(c, uid: int) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	for l in game.room_rt.loot:
		if int(l.uid) == uid: return _collect(c, l)
	return fail("gone")

func _collect(c, l: Dictionary) -> Dictionary:
	var rt: RoomRuntime = game.room_rt
	if int(l.coins) > 0:
		game.economy.apply_currency(str(LootRules.zone_coins(rt.room_id, 1).currency), int(l.coins), "loot")
		rt.loot.erase(l)
		emit("loot_picked", {"actor": c.id, "uid": l.uid, "coins": l.coins})
		return ok()
	var added := 0
	if not (l.instance as Dictionary).is_empty():
		added = game.inventory.apply_add_instance(c.id, l.instance, "loot")
	else:
		added = game.inventory.apply_add(c.id, str(l.item), int(l.count), "loot", {}, false)
	if added <= 0: return fail("bag_full")
	l.count = int(l.count) - added
	if int(l.count) <= 0 or not (l.instance as Dictionary).is_empty():
		rt.loot.erase(l)
		emit("loot_picked", {"actor": c.id, "uid": l.uid, "item": l.item})
	return ok()

# ------------------------------------------------------------------ tick
func tick(delta: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var c = game.active()
	if rt == null or c == null: return
	rt.elapsed += delta
	_tick_auto_hunt(c, delta)
	if float(ambush_cd.get(c.id, 0.0)) > 0.0: ambush_cd[c.id] = float(ambush_cd[c.id]) - delta
	_tick_rare_herbs(c, rt, delta)
	# S43: the room clock moves movers, drops crumbled floors and raises water.
	rt.geometry.advance(delta)
	var st: ActorState = game.actor_state(c.id)
	if st != null: _tick_hazard_volumes(c, rt, st, delta)
	if st != null and st.surface != null:
		c.position.x = st.plane.x
		c.position.y = st.plane.y
		c.position.surface = st.surface.id
		c.position.room = rt.room_id
	for id in rt.objects:
		var os: Dictionary = rt.objects[id]
		if os.get("state", "ready") in ["depleted", "broken"] and float(os.get("timer", 0.0)) > 0.0:
			os.timer = float(os.timer) - delta
			if float(os.timer) <= 0.0:
				os.state = "ready"
				os.hits = 0
				emit("node_regrown", {"room": rt.room_id, "object": id})
	for l in rt.loot.duplicate():
		l.age = float(l.age) + delta
		if st != null and not game.combat.is_wounded(c.id) and float(l.age) > 0.45:
			if Vector2(float(l.x), float(l.y)).distance_to(st.plane) <= PICKUP_RADIUS * (1.6 if game.pets.gatherer_active(c.id) else 1.0) and absf(float(l.alt) - st.altitude) < 60:
				if _collect(c, l).ok: continue
		if float(l.age) >= float(l.ttl):
			rt.loot.erase(l)
			if int(l.coins) == 0 and (ContentDB.item(str(l.item)).get("quest_item", false) or l.get("quality", "common") in ["fine", "superior", "perfect", "relic"]):
				game.inventory.apply_overflow(c.id, [{"item": l.item, "count": l.count, "instance": l.instance}])
			emit("loot_expired", {"uid": l.uid})
	if rt.event.get("active", false): _tick_event(c, rt, delta)
	_tick_chase(c, rt, st)
	_tick_run(c, rt, st)
	_attune_shrines(c, rt, st)
	_tick_hazards(c, rt, st, delta)

# ------------------------------------------------------------------ rooftop chases and timed routes (S43 rule 15)
var chases: Dictionary = {}   # actor -> {object, room, start}: a thief running over the roofs (not saved)
var runs: Dictionary = {}     # actor -> {object, room, start}: a timed route under way (not saved)

## Where a rooftop thief is `t` seconds into his run: {x, y, alt, moving, done, facing}. His route is waypoints
## [x, y, alt, wait_s]: he waits at each, then runs to the next at `speed` along the plane (a climb counts half its
## height). He stands at the last one until its wait is over, and then he is gone.
static func chase_point(route: Array, speed: float, t: float) -> Dictionary:
	var left := maxf(0.0, t)
	var facing := 1
	for i in route.size():
		var w: Array = route[i]
		var wait := float(w[3]) if w.size() > 3 else 0.0
		if left <= wait or i == route.size() - 1:
			return {"x": float(w[0]), "y": float(w[1]), "alt": float(w[2]), "moving": false, "done": i == route.size() - 1 and left > wait, "facing": facing}
		left -= wait
		var n: Array = route[i + 1]
		var d := Vector2(float(n[0]) - float(w[0]), float(n[1]) - float(w[1])).length() + absf(float(n[2]) - float(w[2])) * 0.5
		var leg := maxf(0.15, d / maxf(1.0, speed))
		facing = 1 if float(n[0]) >= float(w[0]) else -1
		if left <= leg:
			var k := left / leg
			return {"x": lerpf(float(w[0]), float(n[0]), k), "y": lerpf(float(w[1]), float(n[1]), k), "alt": lerpf(float(w[2]), float(n[2]), k),
				"moving": true, "done": false, "facing": facing}
		left -= leg
	return {"x": 0.0, "y": 0.0, "alt": 0.0, "moving": false, "done": true, "facing": facing}

## How long a thief's whole run lasts, in seconds.
static func chase_length(route: Array, speed: float) -> float:
	var total := 0.0
	for i in route.size():
		var w: Array = route[i]
		total += float(w[3]) if w.size() > 3 else 0.0
		if i + 1 < route.size():
			var n: Array = route[i + 1]
			var d := Vector2(float(n[0]) - float(w[0]), float(n[1]) - float(w[1])).length() + absf(float(n[2]) - float(w[2])) * 0.5
			total += maxf(0.15, d / maxf(1.0, speed))
	return total

func chase_done_today(c, object_id: String) -> bool:
	return int(c.cooldowns.get("chase_" + object_id, -1)) == Clock.reset_day(Clock.now_utc())

## The thief in the active character's chase, for the street to draw: {object, x, y, alt, moving, facing} or {}.
func chase_view(c) -> Dictionary:
	var ch: Dictionary = chases.get(c.id, {}) if c != null else {}
	if ch.is_empty() or game.room_rt == null or game.room_rt.room_id != str(ch.room): return {}
	var o: Dictionary = game.room_rt.object_def(str(ch.object))
	var p := chase_point(o.chase.route, float(o.chase.get("speed", 260)), game.sim_time - float(ch.start))
	p.object = str(ch.object)
	return p

## Speaking to the thief sends him running over the roofs. Catch him (reach him at his height) before he is over
## the far wall. One chase a street a day, caught or not.
func start_chase(c, o: Dictionary) -> Dictionary:
	var oid := str(o.id)
	if chase_done_today(c, oid): return fail("done", {"text": Tx.t("sim.world.thief_gone")})
	if chases.has(c.id): return fail("busy")
	chases[c.id] = {"object": oid, "room": game.room_rt.room_id, "start": game.sim_time}
	emit("chase_started", {"actor": c.id, "object": oid, "room": game.room_rt.room_id,
		"seconds": chase_length(o.chase.route, float(o.chase.get("speed", 260)))})
	return ok({"text": Tx.t("sim.world.thief_runs")})

func _tick_chase(c, rt: RoomRuntime, st: ActorState) -> void:
	var ch: Dictionary = chases.get(c.id, {})
	if ch.is_empty(): return
	var o: Dictionary = rt.object_def(str(ch.object)) if rt.room_id == str(ch.room) else {}
	if o.is_empty():
		_end_chase(c, ch, false)   # you left the street: he is away over the roofs
		return
	var k: Dictionary = o.chase
	var el: float = game.sim_time - float(ch.start)
	var p := chase_point(k.route, float(k.get("speed", 260)), el)
	if st != null and el >= float(k.get("grace_s", 0.8)) and st.plane.distance_to(Vector2(float(p.x), float(p.y))) <= float(k.get("catch_px", 80)) \
			and absf(st.altitude - float(p.alt)) <= float(k.get("catch_alt", 40)):
		_end_chase(c, ch, true, o)
	elif p.done:
		_end_chase(c, ch, false, o)

func _end_chase(c, ch: Dictionary, caught: bool, o: Dictionary = {}) -> void:
	chases.erase(c.id)
	c.cooldowns["chase_" + str(ch.object)] = Clock.reset_day(Clock.now_utc())
	var secs: float = snappedf(game.sim_time - float(ch.start), 0.1)
	if caught:
		game.apply_effects(c.id, o.chase.get("rewards", []), "thief_chase")
		emit("thief_caught", {"actor": c.id, "object": str(ch.object), "room": str(ch.room), "seconds": secs})
	else:
		emit("thief_escaped", {"actor": c.id, "object": str(ch.object), "room": str(ch.room)})

## A timed route (the Cloud Sect's Cloud Steps): touch the stone to start, reach the finish before the limit.
func start_run(c, o: Dictionary) -> Dictionary:
	if runs.has(c.id) and str(runs[c.id].object) == str(o.id): return fail("busy", {"text": Tx.t("sim.world.run_on")})
	runs[c.id] = {"object": str(o.id), "room": game.room_rt.room_id, "start": game.sim_time}
	emit("route_started", {"actor": c.id, "route": str(o.route.id), "room": game.room_rt.room_id, "limit": float(o.route.get("limit_s", 90))})
	return ok({"text": Tx.t("sim.world.run_go")})

## The week's board for a route: its rivals' times, the same on every device (the account seed and the week).
func route_board(route: Dictionary, week: int) -> Array:
	var r := CalendarRules.draw(game.calendar.cal_seed(), "route:" + str(route.id), week)
	var span: Array = route.get("rival_s", [30, 60])
	var out: Array = []
	for name in route.get("rivals", []): out.append({"name": str(name), "seconds": snappedf(r.randf_range(float(span[0]), float(span[1])), 0.1)})
	return out

## A character's record on a route: {week, best, paid} for this week, plus medals won for good.
func route_record(c, route_id: String) -> Dictionary:
	var rec: Dictionary = c.cooldowns.get("route_" + route_id, {})
	var week: int = game.calendar.rank_week()
	if int(rec.get("week", -1)) != week: rec = {"week": week, "best": 0.0, "paid": false, "medals": rec.get("medals", [])}
	c.cooldowns["route_" + route_id] = rec
	return rec

## Your place on this week's board with this time: 1 + the rivals who were faster.
func route_rank(route: Dictionary, week: int, seconds: float) -> int:
	var rank := 1
	for rv in route_board(route, week):
		if float(rv.seconds) < seconds: rank += 1
	return rank

func _tick_run(c, rt: RoomRuntime, st: ActorState) -> void:
	var run: Dictionary = runs.get(c.id, {})
	if run.is_empty(): return
	var o: Dictionary = rt.object_def(str(run.object)) if rt.room_id == str(run.room) else {}
	if o.is_empty() or st == null:
		runs.erase(c.id)
		return
	var route: Dictionary = o.route
	var el: float = game.sim_time - float(run.start)
	if el > float(route.get("limit_s", 90)):
		runs.erase(c.id)
		emit("route_finished", {"actor": c.id, "route": str(route.id), "finished": false})
		return
	var fin: Dictionary = route.get("finish", {})
	var at: Array = fin.get("at", [0, 0])
	if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > float(fin.get("radius", 70)) or st.altitude < float(fin.get("alt", 0)) - 12.0: return
	runs.erase(c.id)
	finish_route(c, route, snappedf(el, 0.1))

## A finished run: the week's best, its place on the board (a place in the top three pays once a week), and each
## medal's reward the first time its par is beaten.
func finish_route(c, route: Dictionary, seconds: float) -> Dictionary:
	var rec := route_record(c, str(route.id))
	if float(rec.best) <= 0.0 or seconds < float(rec.best): rec.best = seconds
	var rank := route_rank(route, int(rec.week), float(rec.best))
	var medal := ""
	var pars: Dictionary = route.get("pars", {})
	for m in ["gold", "silver", "bronze"]:
		if pars.has(m) and seconds <= float(pars[m]):
			medal = m
			break
	var medals: Array = rec.get("medals", [])
	for m in ["bronze", "silver", "gold"]:
		if medal != "" and ["bronze", "silver", "gold"].find(m) <= ["bronze", "silver", "gold"].find(medal) and not medals.has(m):
			medals.append(m)
			game.apply_effects(c.id, route.get("medal_rewards", {}).get(m, []), "route:" + str(route.id))
	rec.medals = medals
	if rank <= 3 and not rec.get("paid", false):
		rec.paid = true
		game.apply_effects(c.id, route.get("week_rewards", []), "route:" + str(route.id))
	var out := {"actor": c.id, "route": str(route.id), "finished": true, "seconds": seconds, "best": float(rec.best), "rank": rank,
		"of": (route.get("rivals", []) as Array).size() + 1, "medal": medal}
	emit("route_finished", out)
	return ok(out)

## Walking past a shrine is enough for it to remember you as a revival point
## (praying still heals). Nobody loses their respawn by forgetting to press Pray.
func _attune_shrines(c, rt: RoomRuntime, st: ActorState) -> void:
	if st == null or c.last_shrine.get("room", "") == rt.room_id: return
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) != "shrine": continue
		var at: Array = o.get("at", [0, 0])
		if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) <= 160.0:
			c.last_shrine = {"room": rt.room_id, "x": float(at[0]), "y": float(at[1]), "object": str(o.id)}
			emit("shrine_attuned", {"actor": c.id, "room": rt.room_id, "object": str(o.id)})
			GameEvents.save_pending = true
			return

# ------------------------------------------------------------------ hazards (S17)
## Every hazard starts part-way into its cooldown, so nothing strikes on arrival.
func _init_hazards(c, rt: RoomRuntime) -> void:
	rt.hazards.clear()
	rt.hazard_drift = Vector2.ZERO
	if rt.def.get("safe", false): return
	var rng := Rng.stream(c.id, "world")
	for hid in rt.def.get("hazards", []):
		var h := ContentDB.entry("hazards", str(hid))
		if h.is_empty(): continue
		rt.hazards[str(hid)] = {"phase": "cooldown", "t": 0.0, "dur": rng.randf_range(2.0, 2.0 + HazardRules.duration(h, "cooldown")),
			"spots": [], "dir": 1, "pulse": 0.0, "inside": false}

## The push the room puts on a character this tick (gusts, currents); the presentation adds it to walking.
func _on_room_script(p: Dictionary, ev: String) -> void:
	if game.room_rt != null: game.room_rt.geometry.on_event(ev, p)

## S43 hazard volumes (lava, spores, poison vents): status and damage each pulse while inside their rect and altitude.
func _tick_hazard_volumes(c, rt: RoomRuntime, st: ActorState, delta: float) -> void:
	if rt.geometry.volumes.is_empty() or game.combat.is_wounded(c.id) or c.pools.has_status("spawn_protection"): return
	for v in rt.geometry.volumes_at(st.plane, st.altitude):
		if str(v.kind) != "hazard": continue
		var key := "hazard_vol:" + str(v.id)
		var left := float(rt.hazard_pulse.get(key, 0.0)) - delta
		if left > 0.0:
			rt.hazard_pulse[key] = left
			continue
		rt.hazard_pulse[key] = float(v.get("pulse_s", 1.0))
		var amount := 0.0
		if float(v.get("damage_pct", 0.0)) > 0.0:
			amount = game.combat.apply_hazard_damage(c, c.pools.max_hp * float(v.damage_pct), str(v.get("damage_type", "physical")),
				str(v.get("element", "none")), "hazard:" + str(v.id))
		var sd: Dictionary = v.get("status", {})
		if not sd.is_empty(): game.combat.apply_status(c.id, str(sd.id), float(sd.get("s", 2.0)), float(sd.get("power", 1.0)))
		emit("hazard_struck", {"actor": c.id, "room": rt.room_id, "hazard": str(v.get("hazard", v.id)), "amount": int(round(maxf(0.0, amount))),
			"share": 1.0, "answered": false, "stat": "", "need": 0, "have": 0})

func hazard_drift(actor_id: String) -> Vector2:
	if game.room_rt == null or actor_id != game.active_id: return Vector2.ZERO
	return game.room_rt.hazard_drift

func _tick_hazards(c, rt: RoomRuntime, st: ActorState, delta: float) -> void:
	rt.hazard_drift = Vector2.ZERO
	if rt.hazards.is_empty() or st == null: return
	# The cycle keeps running; its effects wait while the character is down or just arrived.
	var calm: bool = game.combat.is_wounded(c.id) or c.pools.has_status("spawn_protection")
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		hs.t = float(hs.t) + delta
		if float(hs.t) >= float(hs.dur): _hazard_advance(c, rt, st, h, hs, calm)
		_hazard_hold(c, rt, st, h, hs, delta, calm)

## Next phase, skipping phases of zero length (a thicket is always active).
func _hazard_advance(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, calm: bool) -> void:
	var rng := Rng.stream(c.id, "world")
	for i in HazardRules.PHASES.size():
		hs.phase = HazardRules.next_phase(str(hs.phase))
		hs.t = 0.0
		hs.dur = HazardRules.duration(h, str(hs.phase))
		if hs.phase == "cooldown": hs.dur = float(hs.dur) * rng.randf_range(0.8, 1.2)
		if float(hs.dur) <= 0.0: continue
		_hazard_enter(c, rt, st, h, hs, rng, calm)
		return
	# Every phase but "active" is empty: a constant hazard.
	hs.phase = "active"
	hs.dur = HazardRules.duration(h, "active")
	_hazard_enter(c, rt, st, h, hs, rng, calm)

func _hazard_enter(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, rng: RandomNumberGenerator, calm: bool) -> void:
	match str(hs.phase):
		"tell":
			hs.dir = int(h.get("dir", -1 if rng.randf() < 0.5 else 1))
			hs.spots = _hazard_spots(rt, st, h, rng)
		"warn":
			if str(h.get("aim", "")) == "player": hs.spots = [[st.plane.x, st.plane.y, st.altitude]]
			emit("hazard_warned", {"actor": c.id, "room": rt.room_id, "hazard": str(h.id), "spots": hs.spots, "dir": int(hs.dir)})
		"active":
			hs.pulse = 0.0
			match str(h.kind):
				"strike":
					var r := float(h.get("radius", 60))
					for sp in hs.spots:
						var at := Vector2(float(sp[0]), float(sp[1]))
						if st.plane.distance_to(at) <= r and absf(st.altitude - float(sp[2])) < 90.0:
							_hazard_hit(c, rt, h, calm)
							break
				"aura":
					if not _sheltered(rt, st, h): _hazard_hit(c, rt, h, calm)
				"gust":
					_hazard_hit(c, rt, h, calm)

## Debug tools (S38): hold every hazard of the room part-way into a phase, for previews. Nothing strikes.
func debug_hazard_phase(phase: String, k: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var c = game.active()
	if rt == null or c == null or not phase in HazardRules.PHASES: return
	var st: ActorState = game.actor_state(c.id)
	var rng := Rng.stream(c.id, "world")
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		hs.phase = "tell"
		_hazard_enter(c, rt, st, h, hs, rng, true)
		if phase != "tell":
			hs.phase = "warn"
			_hazard_enter(c, rt, st, h, hs, rng, true)
		hs.phase = phase
		hs.dur = maxf(HazardRules.duration(h, phase), 2.0)
		hs.t = clampf(k, 0.0, 0.95) * float(hs.dur)

## Strikes land around (or on) the character; the first spot is always close.
func _hazard_spots(rt: RoomRuntime, st: ActorState, h: Dictionary, rng: RandomNumberGenerator) -> Array:
	if str(h.kind) != "strike": return []
	var out: Array = []
	var spread := float(h.get("spread", 0))
	for i in int(h.get("count", 1)):
		var reach := spread * (0.35 if i == 0 else 1.0)
		var p := Vector2(clampf(st.plane.x + rng.randf_range(-reach, reach), 80.0, rt.width() - 80.0),
			clampf(st.plane.y + rng.randf_range(-50.0, 50.0), 660.0, 940.0))
		var s := _ground_at(rt, p)
		out.append([p.x, p.y, s.height_at(p) if s else 0.0])
	return out

## Hazards that act for as long as they are active: gusts and currents push, pools pulse.
func _hazard_hold(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, delta: float, calm: bool) -> void:
	var active: bool = hs.phase == "active"
	match str(h.kind):
		"gust":
			if active and not calm:
				var push := float(h.get("push", 200)) * _hazard_share(c, rt, h)
				if st.flying: push *= float(ContentDB.stat_const("hazard.flyer_push", 1.5))
				rt.hazard_drift += Vector2(float(hs.dir) * push, 0.0)
		"flow":
			var inside := false
			for a in HazardRules.areas(h, rt.def):
				if HazardRules.rect(a).has_point(st.plane) and st.altitude < 2.0:
					inside = true
					if not calm:
						var flow := float(a.get("current", -60)) * (float(h.get("surge", 2.0)) if active else 1.0)
						rt.hazard_drift += Vector2(flow * _hazard_share(c, rt, h), 0.0)
			# A surge that catches you is reported once, when you enter it or it rises around you.
			if active and inside and not hs.inside: _hazard_hit(c, rt, h, calm)
			hs.inside = inside and active
		"pool":
			if not active: return
			hs.pulse = float(hs.pulse) - delta
			if float(hs.pulse) > 0.0: return
			hs.pulse = float(h.get("pulse", 1.0))
			for a in HazardRules.areas(h, rt.def):
				if HazardRules.rect(a).has_point(st.plane) and st.altitude < 10.0:
					_hazard_hit(c, rt, h, calm)
					return

## How much of a push or status gets through this character's answer.
func _hazard_share(c, rt: RoomRuntime, h: Dictionary) -> float:
	return HazardRules.effect_scale(c.stats.value(str(h.answer)), float(HazardRules.need(h, rt.def)))

func _sheltered(rt: RoomRuntime, st: ActorState, h: Dictionary) -> bool:
	var kinds: Array = h.get("shelter", [])
	if kinds.is_empty(): return false
	var r := float(ContentDB.stat_const("hazard.shelter_radius", 220))
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) in kinds:
			var at: Array = o.get("at", [0, 0])
			if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) <= r: return true
	return false

## One blow of a hazard on the character: damage, status, buff and Hollowing, each scaled by
## how well the answering attribute meets the room's need.
func _hazard_hit(c, rt: RoomRuntime, h: Dictionary, calm: bool) -> void:
	if calm: return
	var need_v := float(HazardRules.need(h, rt.def))
	var have: float = c.stats.value(str(h.answer))
	var share := HazardRules.effect_scale(have, need_v)
	var amount := 0.0
	if float(h.get("damage_pct", 0.0)) > 0.0:
		# A blow to the soul is measured against the Soul pool it lands on, not against HP.
		var pool_max: float = c.pools.max_soul if str(h.get("damage_type", "")) == "soul" and c.pools.max_soul > 0.0 else c.pools.max_hp
		amount = game.combat.apply_hazard_damage(c, pool_max * float(h.damage_pct) * HazardRules.damage_scale(have, need_v),
			str(h.get("damage_type", "physical")), str(h.get("element", "none")), "hazard:" + str(h.id))
		if amount < 0.0: return   # dodged
	var sd: Dictionary = h.get("status", {})
	if not sd.is_empty() and share > 0.0:
		var by_time := str(sd.get("scale", "power")) == "duration"
		game.combat.apply_status(c.id, str(sd.id), float(sd.s) * (share if by_time else 1.0), float(sd.power) * (1.0 if by_time else share))
	var bd: Dictionary = h.get("buff", {})
	if not bd.is_empty() and share > 0.0:
		game.combat.apply_buff(c.id, {"stat": str(bd.stat), "op": str(bd.get("op", "pct_add")), "value": float(bd.value) * share,
			"duration": HazardRules.duration(h, "active") + 1.0, "source": "hazard:" + str(h.id)}, "hazard")
	if float(h.get("hollowing", 0.0)) > 0.0 and share > 0.0:
		game.combat.apply_resource_change(c.id, "hollowing", float(h.hollowing) * share, "hazard")
	# The Starsea's star wind strips Qi before it touches the body (Starsea survival, Sage 3).
	if float(h.get("qi_drain_pct", 0.0)) > 0.0 and share > 0.0 and c.pools.max_qi > 0.0:
		game.combat.apply_resource_change(c.id, "qi", -c.pools.max_qi * float(h.qi_drain_pct) * share, "hazard")
	emit("hazard_struck", {"actor": c.id, "room": rt.room_id, "hazard": str(h.id), "amount": int(round(amount)), "share": share,
		"answered": share <= 0.0, "stat": str(h.answer), "need": int(need_v), "have": int(have)})

# ------------------------------------------------------------------ Starsea voyages (S18)
var voyages: Dictionary = {}   # actor -> {route, vessel, seconds}: a crossing under way

## The best vessel the character owns: the one that crosses fastest.
func best_vessel(c) -> String:
	var best := ""
	var speed := 0.0
	for k in c.inventory.key_items:
		var v: Dictionary = ContentDB.item(str(k.id)).get("vessel", {})
		if not v.is_empty() and float(v.get("speed", 1.0)) > speed:
			speed = float(v.get("speed", 1.0))
			best = str(k.id)
	return best

## Board at a Starsea dock: a vessel, the route's star chart and a Qi that survives the star wind
## (Sage 3). The crossing is its own room: the event runs while the vessel sails, and ends in port.
func set_sail(c, route_id: String) -> Dictionary:
	var v := ContentDB.entry("voyages", route_id)
	if v.is_empty(): return fail("unknown_route")
	if game.room_rt == null or game.room_rt.room_id != str(v.get("from", "")): return fail("wrong_dock")
	if v.get("planned", false): return fail("planned", {"text": str(v.get("planned_text", Tx.t("sim.world.this_route_is_not_charted_yet")))})
	if not Unlocks.is_unlocked(c.id, "starsea"): return fail("locked", {"text": Unlocks.locked_text("starsea")})
	var vessel := best_vessel(c)
	if vessel == "": return fail("no_vessel", {"text": Tx.t("sim.world.you_need_a_vessel_to_sail")})
	if c.inventory.count(str(v.chart)) <= 0:
		return fail("no_chart", {"text": Tx.t("sim.world.you_need_the_chart") % ContentDB.item_name(str(v.chart))})
	var speed := float(ContentDB.item(vessel).get("vessel", {}).get("speed", 1.0))
	voyages[c.id] = {"route": route_id, "vessel": vessel, "seconds": float(v.get("base_s", 60)) / maxf(0.25, speed)}
	emit("voyage_started", {"actor": c.id, "route": route_id, "vessel": vessel, "seconds": voyages[c.id].seconds})
	return load_room(c, str(v.crossing), "")

## The crossing's event ended: make port at the far end of the route.
func apply_voyage_arrive(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or not voyages.has(actor_id): return
	var v := ContentDB.entry("voyages", str(voyages[actor_id].route))
	voyages.erase(actor_id)
	emit("voyage_arrived", {"actor": actor_id, "route": str(v.get("id", "")), "room": str(v.get("to", ""))})
	load_room(c, str(v.get("to", "")), str(v.get("to_portal", "")))

# ------------------------------------------------------------------ room events (survival, S27 night)
## Start a timed event in the loaded room (set pieces, sect defence).
func start_room_event(c, ev: Dictionary) -> void:
	if game.room_rt: _start_event(c, game.room_rt, ev)

## What a survived rift leaves behind: a chest's roll at the rift's level, dropped at your feet (S49).
func apply_rift_reward(actor_id: String, loot: String, level: int) -> void:
	var c = game.character(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	if c == null or st == null: return
	var drop := LootRules.roll(loot, Rng.stream(c.id, "loot"), level, c.stats.value("drop_rate"), c.stats.value("coin_find"),
		{"no_equipment": not Unlocks.is_unlocked(c.id, "weapons")})
	_drop_loot(c, drop, st.plane, 0.0)

func _start_event(c, rt: RoomRuntime, ev: Dictionary) -> void:
	if ev.has("requires") and not RequirementRules.passes(ev.requires, game.ctx(c)): return
	rt.event = ev.duplicate(true)
	rt.event.active = true
	rt.event.remaining = float(ev.get("duration", 60))
	# A voyage lasts as long as its vessel takes to cross (S18).
	if voyages.has(c.id) and str(ev.get("id", "")) == "starsea_crossing":
		rt.event.remaining = float(voyages[c.id].get("seconds", rt.event.remaining))
	rt.event.duration = rt.event.remaining
	rt.event.spawn_timer = 2.0
	# Several waves can run at once, each on its own timer; timed spawns arrive once, part-way through.
	var waves: Array = ev.get("waves", [ev.wave] if ev.has("wave") else [])
	rt.event.waves = waves.duplicate(true)
	rt.event.wave_timers = []
	for w in waves: rt.event.wave_timers.append(float(w.get("first_s", 2.0)))
	rt.event.timed_done = []
	rt.event.hits_taken = 0
	rt.event.kills = 0         # kill_count events (S48 Iron Body trial)
	rt.event.ground_s = 0.0    # the pole trial: seconds on the ground in a row
	emit("room_event_started", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "duration": rt.event.remaining})
	# A Temper trial clears the ground: the room's own foes withdraw and wait for it to end (S48).
	if ev.get("clear_room", false):
		for e in rt.living_enemies():
			if not e.summoned and e.team == "enemy": game.enemies.release(e)
	for sp in ev.get("fixed_spawns", []):
		game.enemies.spawn_at(str(sp.enemy), Vector2(float(sp.at[0]), float(sp.at[1])), int(sp.get("level", -1)))
	# The Reflection brings your heart demons with it: one for every 25 on the meter (G1).
	var demons := ProgressionRules.heart_demon_steps(c.cultivator) if str(ev.get("heart_demons", "")) != "" else 0
	for i in demons:
		game.enemies.spawn_at(str(ev.heart_demons), Vector2(700.0 + 260.0 * i, 860.0), int(ev.get("level", -1)))
	if demons > 0: emit("room_event_wave", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "enemy": str(ev.heart_demons),
		"text": Tx.t("sim.world.heart_demons_rise") % demons})

func _tick_event(c, rt: RoomRuntime, delta: float) -> void:
	var ev: Dictionary = rt.event
	ev.remaining = float(ev.remaining) - delta
	var rng := Rng.stream(c.id, "world")
	for i in (ev.waves as Array).size():
		var w: Dictionary = ev.waves[i]
		ev.wave_timers[i] = float(ev.wave_timers[i]) - delta
		if float(ev.wave_timers[i]) > 0.0: continue
		if w.has("until_s") and float(ev.duration) - float(ev.remaining) > float(w.until_s): continue   # its part of the event is over
		ev.wave_timers[i] = float(w.get("every_s", 4.0))
		var alive := 0
		for e in rt.living_enemies():
			if e.def_id == str(w.enemy) and (e.summoned or not ev.get("clear_room", false)): alive += 1
		if alive < int(w.get("max", 6)):
			var pts: Array = w.get("points", [[400, 800]])
			var p: Array = pts[rng.randi_range(0, pts.size() - 1)]
			game.enemies.spawn_at(str(w.enemy), Vector2(float(p[0]), float(p[1])), event_level(c, w))
	var elapsed := float(ev.duration) - float(ev.remaining)
	var timed: Array = ev.get("timed_spawns", [])
	for i in timed.size():
		if i in ev.timed_done or elapsed < float(timed[i].get("after_s", 0.0)): continue
		ev.timed_done.append(i)
		game.enemies.spawn_at(str(timed[i].enemy), Vector2(float(timed[i].at[0]), float(timed[i].at[1])), int(timed[i].get("level", -1)))
		emit("room_event_wave", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "enemy": str(timed[i].enemy),
			"text": str(timed[i].get("text", ""))})
	# S48 Temper trials: fall below the HP floor, or stand on the ground too long in the pole trial, and it is over.
	if float(ev.get("hp_floor", 0.0)) > 0.0 and c.pools.hp < c.pools.max_hp * float(ev.hp_floor):
		_end_event(c, rt, false, "hp_floor")
		return
	if ev.has("ground_grace_s"):
		var st: ActorState = game.actor_state(c.id)
		var grounded := st != null and st.mode() == "ground" and st.surface != null and not st.surface.is_block and st.surface.stratum == "ground"
		ev.ground_s = float(ev.ground_s) + delta if grounded and elapsed > float(ev.get("ground_free_s", 5.0)) else 0.0
		if float(ev.ground_s) > float(ev.ground_grace_s):
			_end_event(c, rt, false, "ground")
			return
	if float(ev.remaining) <= 0.0:
		# A kill-to-win event (a trial) that runs out of time is failed, not passed.
		if ev.has("win_on_kill") or ev.has("kill_count"):
			_end_event(c, rt, false, "time")
		else:
			_end_event(c, rt, true)

## The level a wave's foes come at: a number, or "player" for the character's own Level (the Temper trials).
func event_level(c, w: Dictionary) -> int:
	if str(w.get("level", "")) == "player":
		return clampi(ProgressionRules.level(c) + int(w.get("level_offset", 0)), int(w.get("level_min", 1)), int(w.get("level_max", 999)))
	return int(w.get("level", -1))

# ------------------------------------------------------------------ Beast Kings' nests and the Beast Tide (S46)
## When a fallen King's nest closes again (0 when it is closed).
func nest_closes(king: String) -> float:
	return float(game.account.rooms.get("king_nests", {}).get(king, 0.0))

func _nest_flag(king: String) -> String:
	return "king_nest:%s:%d" % [king, int(nest_closes(king))]

func tide_cfg() -> Dictionary:
	return ContentDB.config("expeditions").get("beast_tide", {})

## The Beast Tide comes once a real week: due when this character has not stood against this week's tide.
func tide_due(c) -> bool:
	return int(c.cooldowns.get("beast_tide_week", -1)) != Clock.reset_week(Clock.now_utc())

func tide_days_left(c) -> int:
	var now := Clock.now_utc()
	var d := 0
	while d < 8 and Clock.reset_week(now + d * 86400.0) == Clock.reset_week(now): d += 1
	return d

## Ring the gate's gong: three waves of beasts, their Level following yours (S25 room-event waves).
func start_beast_tide(c) -> Dictionary:
	var cfg := tide_cfg()
	if game.room_rt == null or game.room_rt.room_id != str(cfg.get("room", "sf_gate")): return fail("not_here")
	if not tide_due(c): return fail("not_due", {"text": Tx.t("sim.world.tide_not_due") % maxi(1, tide_days_left(c))})
	if game.room_rt.event.get("active", false): return fail("busy")
	var ev := {"id": "beast_tide", "duration": float(cfg.get("duration", 90)), "waves": cfg.get("waves", []),
		"on_complete": [{"kind": "beast_tide_result", "won": true}]}
	_start_event(c, game.room_rt, ev)
	emit("beast_tide_started", {"actor": c.id, "room": game.room_rt.room_id, "week": Clock.reset_week(Clock.now_utc()),
		"duration": float(cfg.get("duration", 90))})
	return ok({"event": "beast_tide"})

## S46 Beast Trial Grove: once a day the animals fight ten beasts (their Level following yours) while you rally them.
func start_beast_trial(c) -> Dictionary:
	var cfg: Dictionary = ContentDB.config("beast_arena").get("grove", {})
	if game.room_rt == null or game.room_rt.room_id != str(cfg.get("room", "sf_beast_grove")): return fail("not_here")
	var today := Clock.reset_day(Clock.now_utc())
	if int(c.cooldowns.get("grove_day", -1)) == today: return fail("done", {"text": Tx.t("sim.world.grove_done")})
	if game.pets.party(c).is_empty(): return fail("no_pet", {"text": Tx.t("sim.pet.no_active")})
	if game.room_rt.event.get("active", false): return fail("busy")
	c.cooldowns["grove_day"] = today
	var waves: Array = []
	for w in cfg.get("waves", []):
		var w2: Dictionary = (w as Dictionary).duplicate()
		w2.level = "player"
		w2.level_offset = int(cfg.get("level_offset", -2))
		w2.level_min = int(cfg.get("level_min", 10))
		w2.level_max = int(cfg.get("level_max", 60))
		waves.append(w2)
	var ev := {"id": "beast_trial", "pet_trial": true, "duration": float(cfg.get("duration", 150)), "waves": waves,
		"kill_count": {"enemy": "*", "count": int(cfg.get("count", 10))},
		"on_complete": [{"kind": "beast_trial_result", "won": true}], "on_timeout": [{"kind": "beast_trial_result", "won": false}]}
	_start_event(c, game.room_rt, ev)
	return ok({"event": "beast_trial"})

## The Grove's reward: the Guardian Spirit book the first time, then one draw from the pool.
func apply_trial_result(actor_id: String, won: bool) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var cfg: Dictionary = ContentDB.config("beast_arena").get("grove", {})
	var item := ""
	if won:
		if not c.quests.has_flag("grove_first_clear"):
			game.quest.apply_flag(c.id, "grove_first_clear")
			item = str(cfg.get("first", ""))
		else:
			var pool: Array = cfg.get("pool", [])
			var pick := LootRules.RngService_weighted(Rng.stream(c.id, "world"), pool)
			item = str(pick.get("item", ""))
		if item != "": game.inventory.apply_add(c.id, item, 1, "beast_trial")
	emit("beast_trial_result", {"actor": c.id, "won": won, "item": item})

## Held the gate: this week's tide is spent; cores of your rank, an egg (the Cloud Stag's once, from Cloud Stride 1)
## and Spirit Soil.
func apply_tide_result(actor_id: String, won: bool) -> void:
	var c = game.character(actor_id)
	if c == null: return
	c.cooldowns["beast_tide_week"] = Clock.reset_week(Clock.now_utc())
	var rw: Dictionary = tide_cfg().get("rewards", {})
	var got: Array = []
	if won:
		var rng := Rng.stream(c.id, "world")
		var els: Array = ["fire", "water", "wood", "earth", "wind", "thunder"]
		var tier := "low" if ProgressionRules.level(c) < 28 else ("mid" if ProgressionRules.level(c) < 46 else "high")
		for i in int(rw.get("cores", 3)):
			var core := "%s_core_%s" % [els[rng.randi_range(0, els.size() - 1)], tier]
			game.inventory.apply_add(c.id, core, 1, "beast_tide")
			got.append(core)
		var egg := str(rw.get("egg", "spirit_egg"))
		if ProgressionRules.at_least(c.cultivator.realm_key, str(rw.get("stag_realm", "cloud_stride_1"))) and not c.quests.has_flag("tide_stag_egg"):
			egg = str(rw.get("stag_egg", "cloud_stag_egg"))
			game.quest.apply_flag(c.id, "tide_stag_egg")
		game.inventory.apply_add(c.id, egg, 1, "beast_tide")
		got.append(egg)
		game.inventory.apply_add(c.id, "spirit_soil", int(rw.get("soil", 1)), "beast_tide")
		got.append("spirit_soil")
	emit("beast_tide_result", {"actor": c.id, "won": won, "items": got})

func _end_event(c, rt: RoomRuntime, won: bool, reason := "") -> void:
	var ev: Dictionary = rt.event
	ev.active = false
	emit("room_event_completed" if won else "room_event_failed", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "reason": reason})
	for e in rt.living_enemies():
		if e.summoned: game.enemies.release(e)   # the rest scatter: no loot, no kill credit
	game.apply_effects(c.id, ev.get("on_complete" if won else "on_timeout", []), "event:" + str(ev.get("id", "")))
	if won and int(ev.get("hits_taken", 0)) == 0 and not ev.get("on_flawless", []).is_empty():
		emit("room_event_flawless", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", ""))})
		game.apply_effects(c.id, ev.on_flawless, "event:" + str(ev.get("id", "")) + ":flawless")

## A kill-to-win event ends the moment its foe falls.
func _event_kill(p: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null or not rt.event.get("active", false): return
	if str(rt.event.get("win_on_kill", "")) != "" and str(p.get("def", "")) == str(rt.event.win_on_kill):
		var c = game.active()
		if c != null: _end_event(c, rt, true)
		return
	# S48 Iron Body trial: so many of one foe in a single run.
	var kc: Dictionary = rt.event.get("kill_count", {})
	if not kc.is_empty() and (str(kc.get("enemy", "")) == "*" or str(p.get("def", "")) == str(kc.get("enemy", ""))) and str(p.get("victim_kind", "enemy")) == "enemy":
		rt.event.kills = int(rt.event.get("kills", 0)) + 1
		var c2 = game.active()
		if c2 != null: emit("room_event_wave", {"actor": c2.id, "room": rt.room_id, "event": str(rt.event.get("id", "")), "enemy": str(kc.enemy),
			"text": Tx.t("sim.world.trial_kills") % [int(rt.event.kills), int(kc.get("count", 1))]})
		if c2 != null and int(rt.event.kills) >= int(kc.get("count", 1)): _end_event(c2, rt, true)

# ------------------------------------------------------------------ the Trial Tower (S49 v1.0)
## Thirty floors at the Fairground (tower.json), all in one room: each floor is a room event with its own rule.
## The floors you have cleared are World state on the character; each can be swept once a day for its loot.
func tower_floor(f: int) -> Dictionary:
	return ContentDB.entry("tower", "floor_%d" % f)

func tower_cleared(c) -> int:
	return int(c.tower.get("cleared", 0))

func tower_swept_today(c, f: int) -> bool:
	return int(c.tower.get("swept", {}).get(str(f), -1)) == Clock.reset_day(Clock.now_utc())

## Climb a floor: the next one, or any you have cleared before. The trial starts in the tower room.
func climb_tower(c, f: int) -> Dictionary:
	var row := tower_floor(f)
	if row.is_empty(): return fail("no_floor")
	if f > tower_cleared(c) + 1: return fail("locked", {"text": Tx.t("sim.world.tower_locked") % (tower_cleared(c) + 1)})
	if game.room_rt != null and game.room_rt.event.get("active", false): return fail("busy", {"text": Tx.t("sim.world.tower_busy")})
	var room := str(ContentDB.config("tower").get("room", "sf_trial_tower"))
	if game.room_rt == null or game.room_rt.room_id != room:
		var moved := load_room(c, room, "entry")
		if not moved.get("ok", false): return moved
	var lv := int(row.level)
	var foes: Array = row.get("foes", [])
	var points := [[900, 860], [1300, 820], [1700, 860], [2100, 840]]
	var ev := {"id": "tower_floor", "floor": f, "clear_room": true, "duration": float(row.get("time_s", 60)),
		"on_complete": [{"kind": "tower_clear", "floor": f}]}
	match str(row.kind):
		"clear", "swift":
			var n := int(row.get("count", 4))
			var spawns: Array = []
			for i in n: spawns.append({"enemy": str(foes[i % foes.size()]), "at": points[i % points.size()], "level": lv})
			ev.fixed_spawns = spawns
			ev.kill_count = {"enemy": "*", "count": n}
		"survive":
			var waves: Array = []
			for i in foes.size():
				waves.append({"enemy": str(foes[i]), "first_s": 2.0 + i * 3.0, "every_s": 5.0, "max": 2, "level": lv, "points": points})
			ev.waves = waves
		_:
			ev.fixed_spawns = [{"enemy": str(row.guardian), "at": [1600, 850], "level": int(row.get("guardian_level", lv + 4))},
				{"enemy": str(foes[0]), "at": points[0], "level": lv}, {"enemy": str(foes[foes.size() - 1]), "at": points[3], "level": lv}]
			ev.win_on_kill = str(row.guardian)
	start_room_event(c, ev)
	return ok({"floor": f})

## A floor cleared: its loot at your feet; the first time, Spirit Stones as well and the next floor opens.
func apply_tower_clear(actor_id: String, f: int) -> void:
	var c = game.character(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	var row := tower_floor(f)
	if c == null or row.is_empty(): return
	var first := f > tower_cleared(c)
	if first: c.tower["cleared"] = f
	if st != null and game.room_rt != null:
		_drop_loot(c, LootRules.roll(str(row.loot), Rng.stream(c.id, "loot"), int(row.level), c.stats.value("drop_rate"), c.stats.value("coin_find"),
			{"no_equipment": not Unlocks.is_unlocked(c.id, "weapons")}), st.plane, 0.0)
	if first: game.apply_effects(c.id, [{"kind": "grant_currency", "currency": "spirit_stone", "amount": int(row.get("stones", 2))}], "tower")
	emit("tower_floor_cleared", {"actor": c.id, "floor": f, "first": first})

## Sweep: each floor you have cleared gives its loot once a day, straight to the bag, without the fight.
## floor -1 sweeps every cleared floor not yet swept today.
func sweep_tower(c, f := -1) -> Dictionary:
	var day := Clock.reset_day(Clock.now_utc())
	var swept: Dictionary = c.tower.get("swept", {})
	var done := 0
	for i in range(1, tower_cleared(c) + 1):
		if (f > 0 and i != f) or int(swept.get(str(i), -1)) == day: continue
		var row := tower_floor(i)
		var drop := LootRules.roll(str(row.loot), Rng.stream(c.id, "loot"), int(row.level), c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": true})
		var fx: Array = []
		for it in drop.get("items", []):
			if not ContentDB.item(str(it.item)).is_empty() and int(it.count) > 0: fx.append({"kind": "grant_item", "item": str(it.item), "count": int(it.count)})
		var silver := int(drop.get("coins", 0)) + int(ContentDB.config("tower").get("sweep_silver_per_floor", 15))
		fx.append({"kind": "grant_currency", "currency": "silver_tael", "amount": silver})
		game.apply_effects(c.id, fx, "tower_sweep")
		swept[str(i)] = day
		done += 1
	c.tower["swept"] = swept
	if done == 0: return fail("nothing", {"text": Tx.t("sim.world.tower_nothing")})
	emit("tower_swept", {"actor": c.id, "floors": done})
	return ok({"floors": done})

# ------------------------------------------------------------------ S49 mobile conventions: idle rooms, auto-hunt, auto-path
## Rooms where auto-hunt is always off (S49): bosses, trials, dungeons, story instances, secret places.
const AUTO_HUNT_OFF := ["boss_arena", "trial", "dungeon", "story", "secret", "prologue"]
var auto_hunt: Dictionary = {}    # actor -> true while the toggle is on (the session only)
var auto_paths: Dictionary = {}   # actor -> {target, route: [{room, portal, to}]}
var _auto_check := 0.0

## The idle Hunt and Gather tasks (S23) run only in rooms that list them (room.idle); rest, seclusion and
## training go anywhere.
func idle_allowed(room_id: String, kind: String) -> bool:
	if not kind in ["hunt", "gather"]: return true
	return (ContentDB.room(room_id).get("idle", []) as Array).has(kind)

## Why this character may not auto-hunt here now ("" when it may): the room must allow idle Hunt, and it is off in
## bosses, trials, dungeons, room events and tribulations. It never uses treasures, pills or breakthroughs.
func auto_hunt_block(c) -> String:
	var rt: RoomRuntime = game.room_rt
	if c == null or rt == null: return "room"
	if str(rt.def.get("type", "")) in AUTO_HUNT_OFF or not idle_allowed(rt.room_id, "hunt"): return "room"
	if rt.event.get("active", false): return "event"
	if not game.progression.tribulation_view(c.id).is_empty(): return "tribulation"
	if c.pools.hp < c.pools.max_hp * 0.2: return "low_hp"
	for e in rt.living_enemies():
		if e.is_boss(): return "boss"
	return ""

func auto_hunting(actor_id: String) -> bool:
	return auto_hunt.has(actor_id)

func set_auto_hunt(c, on: bool) -> Dictionary:
	if not on:
		_end_auto_hunt(c.id, "off")
		return ok({"on": false})
	var why := auto_hunt_block(c)
	if why != "": return fail(why, {"text": Tx.t("sim.world.auto_hunt_" + why)})
	auto_paths.erase(c.id)
	auto_hunt[c.id] = true
	emit("auto_hunt_changed", {"actor": c.id, "on": true, "reason": ""})
	return ok({"on": true})

func _end_auto_hunt(actor_id: String, reason: String) -> void:
	if not auto_hunt.has(actor_id): return
	auto_hunt.erase(actor_id)
	emit("auto_hunt_changed", {"actor": actor_id, "on": false, "reason": reason})

func _tick_auto_hunt(c, delta: float) -> void:
	if not auto_hunt.has(c.id): return
	_auto_check -= delta
	if _auto_check > 0.0: return
	_auto_check = 0.5
	var why := auto_hunt_block(c)
	if why != "": _end_auto_hunt(c.id, why)

## Is this portal open to this character, seen from its own room (requirements, hidden ways found)?
func portal_open(c, room_id: String, p: Dictionary) -> bool:
	if ContentDB.room(str(p.get("to", ""))).is_empty(): return false
	if p.has("requires") and not RequirementRules.passes(p.requires, game.ctx(c)): return false
	if str(p.get("type", "")) == "hidden" and not c.quests.has_flag("seen_" + room_id + "_" + str(p.id)): return false
	return true

## The shortest way between two rooms through the portals open to this character (its realm, quests and arts):
## [{room, portal, to}], [] when there is none or it is already there.
func route(c, from_room: String, to_room: String) -> Array:
	return WorldRules.route(from_room, to_room, func(room_id: String, p: Dictionary) -> bool: return portal_open(c, room_id, p))

func start_auto_path(c, target: String) -> Dictionary:
	if target == "":
		_end_auto_path(c.id, "cancelled")
		return ok()
	if game.room_rt == null: return fail("no_room")
	if target == game.room_rt.room_id: return fail("here", {"text": Tx.t("sim.world.auto_path_here")})
	var r := route(c, game.room_rt.room_id, target)
	if r.is_empty(): return fail("no_route", {"text": Tx.t("sim.world.auto_path_none")})
	_end_auto_hunt(c.id, "path")
	auto_paths[c.id] = {"target": target, "route": r}
	emit("auto_path_started", {"actor": c.id, "target": target, "rooms": r.size()})
	return ok({"route": r})

## Where auto-path is heading in this room: the portal to take ({portal, x, y, press_up}), or {}.
func auto_path_step(c) -> Dictionary:
	var ap: Dictionary = auto_paths.get(c.id, {}) if c != null else {}
	if ap.is_empty() or game.room_rt == null: return {}
	for s in ap.route:
		if str(s.room) != game.room_rt.room_id: continue
		if s.get("dock", false):
			for o in game.room_rt.def.get("objects", []):
				if str(o.id) == str(s.portal): return {"dock": str(o.id), "x": float(o.at[0]), "y": float(o.at[1]), "press_up": false, "surface": ""}
			return {}
		var p = game.room_rt.portal_def(str(s.portal))
		if p.is_empty(): return {}
		return {"portal": str(s.portal), "x": float(p.at[0]), "y": float(p.at[1]), "press_up": bool(p.get("press_up", false)),
			"surface": str(p.get("surface", ""))}
	return {}

func auto_path_target(c) -> String:
	return str(auto_paths.get(c.id, {}).get("target", "")) if c != null else ""

func _end_auto_path(actor_id: String, reason: String) -> void:
	if not auto_paths.has(actor_id): return
	var target := str(auto_paths[actor_id].target)
	auto_paths.erase(actor_id)
	emit("auto_path_ended", {"actor": actor_id, "target": target, "reason": reason})

## Each room reached: arrived, still on the way, or off the route (it finds a new one from here).
func _auto_path_room(_p: Dictionary) -> void:
	var c = game.active()
	if c == null or not auto_paths.has(c.id) or game.room_rt == null: return
	var ap: Dictionary = auto_paths[c.id]
	if game.room_rt.room_id == str(ap.target):
		_end_auto_path(c.id, "arrived")
		return
	if (ap.route as Array).any(func(s): return str(s.room) == game.room_rt.room_id): return
	if game.room_rt.def.get("crossing", false): return   # under sail: the route goes on at the far pier
	var r := route(c, game.room_rt.room_id, str(ap.target))
	if r.is_empty(): _end_auto_path(c.id, "lost")
	else: ap.route = r

## At a Starsea dock the route boards a vessel; without one (or a chart) it stops there and says why.
func auto_path_board(c, dock_id: String) -> Dictionary:
	var r := interact(c, dock_id)
	if not r.get("ok", false): _end_auto_path(c.id, "dock")
	return r

## It stops at danger: the moment something strikes you, the controls are yours again.
func _auto_path_danger(p: Dictionary) -> void:
	if str(p.get("target_kind", "")) == "player" and auto_paths.has(str(p.get("target", ""))): _end_auto_path(str(p.target), "danger")
