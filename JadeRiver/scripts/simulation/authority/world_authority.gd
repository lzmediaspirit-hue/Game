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

func intents() -> Array:
	return ["use_portal", "interact", "teleport", "pick_up", "enter_world", "sense_pulse"]

func subscribe() -> void:
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 50)
	GameEvents.subscribe("actor_defeated", _event_kill, 55)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"use_portal": return use_portal(c, str(intent.get("portal", "")), bool(intent.get("crossing", false)))
		"interact": return interact(c, str(intent.get("object", "")))
		"teleport": return teleport(c, str(intent.get("stone", "")))
		"pick_up": return pick_up(c, int(intent.get("uid", -1)))
		"enter_world": return enter_world(c)
		"sense_pulse": return sense_pulse(c)
	return fail("unknown_intent")

# ------------------------------------------------------------------ rooms
static func compile_geometry(def: Dictionary) -> Dictionary:
	var data := {"bounds": def.get("bounds", [0, 480, 1280, 480]), "surfaces": def.get("surfaces", []).duplicate(true),
		"objects": def.get("scenery", []).duplicate(true), "gates": []}
	for o in def.get("objects", []):
		if o.has("footprint") and o.get("blocks", false):
			data.objects.append({"id": "obj_" + str(o.id), "art": "none", "footprint": o.footprint, "height": float(o.get("height", 60)), "radius": 4})
	return ZoneLayout.compile(data)

func load_room(c, room_id: String, portal_id: String, point := Vector2.INF) -> Dictionary:
	var def := ContentDB.room(room_id)
	if def.is_empty(): return fail("unknown_room")
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
	rt.arrival_protection = float(ContentDB.stat_const("combat.spawn_protection_s", 1.5))
	game.combat.apply_status(c.id, "spawn_protection", rt.arrival_protection, 1.0)
	emit("room_entered", {"actor": c.id, "room": room_id, "portal": portal_id, "first_visit": first, "x": arrival.x, "y": arrival.y,
		"facing": facing, "surface": c.position.surface, "zone": zone_new})
	if zone_new != zone_old: emit("zone_entered", {"actor": c.id, "zone": zone_new})
	if def.has("event"): _start_event(c, rt, def.event)
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
		return {"open": false, "text": "Coming soon"}
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

func teleport(c, stone_id: String) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "teleport_stones"): return fail("locked")
	if not game.account.teleports.has(stone_id): return fail("undiscovered")
	var stone := ContentDB.entry("teleport_stones", stone_id)
	if stone.is_empty(): return fail("unknown_stone")
	var fee := int(stone.get("fee_shards", 1))
	if c.inventory.count("spirit_stone_shard") < fee: return fail("no_fee", {"text": "Needs %d Spirit Stone shard" % fee})
	game.inventory.apply_remove(c.id, "spirit_stone_shard", fee, "teleport")
	emit("teleported", {"actor": c.id, "stone": stone_id})
	return load_room(c, str(stone.room), "", Vector2(float(stone.at[0]) + 60, float(stone.at[1]) + 10))

## Spirit Sense (S17, SA1/SA2): a soul pulse that reveals hidden portals and
## fog-hidden monsters within the sense radius.
func sense_pulse(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_sense"): return fail("locked", {"text": Unlocks.locked_text("spirit_sense")})
	if c.pools.cooldown("sense") > 0.0: return fail("cooldown")
	var cost := 10.0
	if c.pools.get_value("soul") < cost: return fail("no_soul", {"text": "Not enough Soul"})
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
	emit("spirit_sense_pulsed", {"actor": c.id, "x": here.x, "y": here.y, "radius": radius, "found": found})
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
		if o.type in ["herb_patch", "ore_vein"] and float(mem.nodes.get(id, 0.0)) > now:
			st.state = "depleted"
			st.timer = float(mem.nodes[id]) - now
		if o.type in ["chest"] and mem.opened.has(id): st.state = "open"
		if o.type in BREAKABLES and float(mem.broken.get(id, 0.0)) > now:
			st.state = "broken"
			st.timer = float(mem.broken[id]) - now
		rt.objects[id] = st

func object_visible(c, o: Dictionary) -> bool:
	if o.has("visible_if") and not RequirementRules.passes(o.visible_if, game.ctx(c)): return false
	if o.has("hidden_if") and RequirementRules.passes(o.hidden_if, game.ctx(c)): return false
	return true

func object_available(c, o: Dictionary) -> Dictionary:
	if not object_visible(c, o): return {"ok": false, "text": "", "hidden": true}
	if o.has("requires") and not RequirementRules.passes(o.requires, game.ctx(c)):
		return {"ok": false, "text": str(o.get("locked_text", RequirementRules.first_failure_text(o.requires, game.ctx(c))))}
	var st: Dictionary = game.room_rt.objects.get(str(o.id), {})
	if st.get("state", "ready") in ["depleted", "broken", "open"]: return {"ok": false, "text": "", "spent": true}
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

func interact(c, object_id: String) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var o = game.room_rt.object_def(object_id)
	if o.is_empty(): return fail("unknown_object")
	var st: ActorState = game.actor_state(c.id)
	var at: Array = o.get("at", [0, 0])
	if st != null and st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > float(o.get("radius", 110)) + 20.0:
		return fail("too_far")
	if st != null and absf(st.altitude - float(o.get("alt", 0.0))) > 48.0:
		return fail("out_of_reach", {"text": "Out of reach from here."})
	var avail := object_available(c, o)
	if not avail.ok and o.type != "npc":
		return fail("unavailable", {"text": avail.text})
	var result := ok({"type": o.type})
	match str(o.type):
		"npc":
			return game.quest.talk(c, str(o.npc))
		"shrine":
			c.last_shrine = {"room": game.room_rt.room_id, "x": float(at[0]), "y": float(at[1]), "object": object_id}
			game.combat.apply_resource_change(c.id, "hp", c.pools.max_hp, "shrine")
			if c.pools.max_qi > 0: game.combat.apply_resource_change(c.id, "qi", c.pools.max_qi, "shrine")
			GameEvents.save_pending = true
			result.text = "The shrine remembers you. Wounds close."
		"herb_patch", "ore_vein", "fishing_spot":
			return game.crafting.gather(c, o)
		"chest":
			var s: Dictionary = game.room_rt.objects.get(object_id, {})
			s.state = "open"
			_room_mem(c, game.room_rt.room_id).opened[object_id] = true
			var drop := LootRules.roll(str(o.get("loot", "chest_valley")), Rng.stream(c.id, "loot"), int(o.get("level", ProgressionRules.level(c))),
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
		"rite_circle":
			return game.quest.start_set_piece(c, str(o.get("event", "")))
		"storage_chest":
			result.open_page = "storage"
		"cooking_pot", "alchemy_furnace", "forge_anvil", "formation_table", "garden_bed":
			result.open_page = str(o.get("page", {"cooking_pot": "cooking", "alchemy_furnace": "alchemy", "forge_anvil": "forge",
				"formation_table": "formations", "garden_bed": "garden"}[o.type]))
		"notice_board":
			result.open_page = "notice_board"
		"signpost":
			result.text = str(o.get("text", ""))
		"insight_stone", "qi_spring":
			result.text = str(o.get("text", "Meditate here."))
		"spar_post":
			return game.quest.start_spar_from_object(c, o)
		"defence_drum":
			return game.sect.start_defence(c)
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
		if o.type in BREAKABLES or o.type in TRAINING or o.type == "decor": continue
		if not object_visible(c, o): continue
		var at: Array = o.get("at", [0, 0])
		var d := st.plane.distance_to(Vector2(float(at[0]), float(at[1])))
		if d > float(o.get("radius", 110)): continue
		var avail := object_available(c, o)
		if avail.get("spent", false): continue
		var priority := 3.0
		if o.type == "npc":
			priority = 1.0 if game.quest.npc_marker(c, str(o.npc)) != "" else 2.0
		elif o.type in ["herb_patch", "ore_vein", "fishing_spot"]: priority = 4.0
		elif o.type == "pickup": priority = 0.5
		var score := priority * 1000.0 + d
		if score < best_score:
			best_score = score
			best = {"object": str(o.id), "type": o.type, "label": _verb(o), "ok": avail.ok, "text": avail.text, "npc": str(o.get("npc", ""))}
	if best.is_empty():
		for p in game.room_rt.def.get("portals", []):
			if p.get("type", "edge") == "edge" and not p.get("press_up", false): continue
			if portal_near(c, p):
				var ps := portal_state(c, p)
				if ps.get("hidden", false): continue
				best = {"portal": str(p.id), "type": "portal", "label": "Enter", "ok": ps.open, "text": ps.text, "target": str(p.get("to", ""))}
				break
	return best

func _verb(o: Dictionary) -> String:
	match str(o.type):
		"npc": return "Talk"
		"herb_patch": return "Gather"
		"ore_vein": return "Mine"
		"fishing_spot": return "Fish"
		"chest", "storage_chest": return "Open"
		"shrine": return "Pray"
		"pickup": return "Take"
		"lifting_stone": return "Lift"
		"cooking_pot": return "Cook"
		"alchemy_furnace": return "Refine"
		"forge_anvil": return "Forge"
		"teleport_stone": return "Travel"
		"notice_board", "signpost", "inspect": return "Read"
		"rite_circle": return "Begin"
		"spar_post": return "Spar"
		"bell": return "Ring"
	return "Use"

# ------------------------------------------------------------------ loot (S32)
func _on_actor_defeated(p: Dictionary) -> void:
	if p.get("victim_kind", "") != "enemy" or game.room_rt == null: return
	var c = game.character(str(p.get("killer", game.active_id)))
	if c == null: c = game.active()
	if c == null: return
	var def := ContentDB.entry("enemies", str(p.def))
	if def.is_empty(): return
	var rng := Rng.stream(c.id, "loot")
	var drop := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate"), c.stats.value("coin_find"),
		{"no_equipment": false, "needs": game.quest.item_needs(c)})
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
	if int(drop.get("coins", 0)) > 0: drops.append({"coins": int(drop.coins)})
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
		game.economy.apply_currency(str(ContentDB.zone_of_room(rt.room_id).get("currency", {}).get("everyday", "silver_tael")), int(l.coins), "loot")
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
	var st: ActorState = game.actor_state(c.id)
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
				game.mail.apply_overflow(c.id, [{"item": l.item, "count": l.count, "instance": l.instance}])
			emit("loot_expired", {"uid": l.uid})
	if rt.event.get("active", false): _tick_event(c, rt, delta)
	_attune_shrines(c, rt, st)

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

# ------------------------------------------------------------------ room events (survival, S27 night)
## Start a timed event in the loaded room (set pieces, sect defence).
func start_room_event(c, ev: Dictionary) -> void:
	if game.room_rt: _start_event(c, game.room_rt, ev)

func _start_event(c, rt: RoomRuntime, ev: Dictionary) -> void:
	if ev.has("requires") and not RequirementRules.passes(ev.requires, game.ctx(c)): return
	rt.event = ev.duplicate(true)
	rt.event.active = true
	rt.event.remaining = float(ev.get("duration", 60))
	rt.event.spawn_timer = 2.0
	emit("room_event_started", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", "")), "duration": rt.event.remaining})
	for sp in ev.get("fixed_spawns", []):
		game.enemies.spawn_at(str(sp.enemy), Vector2(float(sp.at[0]), float(sp.at[1])), int(sp.get("level", -1)))

func _tick_event(c, rt: RoomRuntime, delta: float) -> void:
	var ev: Dictionary = rt.event
	ev.remaining = float(ev.remaining) - delta
	ev.spawn_timer = float(ev.spawn_timer) - delta
	if float(ev.spawn_timer) <= 0.0 and ev.has("wave"):
		ev.spawn_timer = float(ev.wave.get("every_s", 4.0))
		var alive := 0
		for e in rt.living_enemies():
			if e.def_id == str(ev.wave.enemy): alive += 1
		if alive < int(ev.wave.get("max", 6)):
			var pts: Array = ev.wave.get("points", [[400, 800]])
			var rng := Rng.stream(c.id, "world")
			var p: Array = pts[rng.randi_range(0, pts.size() - 1)]
			game.enemies.spawn_at(str(ev.wave.enemy), Vector2(float(p[0]), float(p[1])))
	if float(ev.remaining) <= 0.0:
		# A kill-to-win event (a trial) that runs out of time is failed, not passed.
		if ev.has("win_on_kill"):
			_end_event(c, rt, false)
		else:
			_end_event(c, rt, true)

func _end_event(c, rt: RoomRuntime, won: bool) -> void:
	var ev: Dictionary = rt.event
	ev.active = false
	emit("room_event_completed" if won else "room_event_failed", {"actor": c.id, "room": rt.room_id, "event": str(ev.get("id", ""))})
	for e in rt.living_enemies():
		if e.summoned: game.enemies.defeat(e, "event")
	game.apply_effects(c.id, ev.get("on_complete" if won else "on_timeout", []), "event:" + str(ev.get("id", "")))

## A kill-to-win event ends the moment its foe falls.
func _event_kill(p: Dictionary) -> void:
	var rt: RoomRuntime = game.room_rt
	if rt == null or not rt.event.get("active", false): return
	if str(rt.event.get("win_on_kill", "")) != "" and str(p.get("def", "")) == str(rt.event.win_on_kill):
		var c = game.active()
		if c != null: _end_event(c, rt, true)
