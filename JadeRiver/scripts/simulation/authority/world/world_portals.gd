extends "res://scripts/simulation/authority/world/world_part.gd"
## World · the ways out of a room: portals and hidden ways (Spirit Sense, the Wandering Eye), which of them are open and
## the shortest route through them, the prototype's gate (decision 41), teleport stones and the shrine a fall wakes
## you at. Every way ends in the authority's load_room.

const PORTAL_RADIUS := Vector2(64, 44)

## S48 Wandering Eye (a fate): one hidden way in each room entered shows itself.
func on_room_entered_fates(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or game.room_rt == null or not game.progression.fate_flag(c, "reveal_hidden"): return
	for pt in game.room_rt.def.get("portals", []):
		if str(pt.get("type", "")) != "hidden": continue
		var f := seen_flag(game.room_rt.room_id, str(pt.id))
		if c.quests.has_flag(f): continue
		game.quest.apply_flag(c.id, f)
		emit("hidden_portal_revealed", {"actor": c.id, "portal": str(pt.id), "room": game.room_rt.room_id, "source": "wandering_eye"})
		return

func portal_near(c, portal: Dictionary) -> bool:
	var st: ActorState = game.actor_state(c.id)
	if st == null: return true
	var at: Array = portal.get("at", [0, 0])
	var r: Vector2 = PORTAL_RADIUS
	if portal.has("reach"):
		# Redesign Phase 4: a way on the height grid reaches along its edge or doorway and a tile across it (turned with
		# its direction, TopdownRoom.merge_def), and only on its own floor: never from the ground under a terrace's door.
		r = Vector2(float(portal.reach[0]), float(portal.reach[1]))
		if absf(st.altitude - float(portal.get("alt", 0.0))) > TopdownRoom.LEVEL * 0.5: return false
	return absf(st.plane.x - float(at[0])) <= r.x and absf(st.plane.y - float(at[1])) <= r.y

## The flag a character carries once a hidden way in a room has shown itself to them.
static func seen_flag(room_id: String, portal_id: String) -> String:
	return "seen_" + room_id + "_" + portal_id

## Decision 41, the end of the prototype: in a top-down character's game, a way from a room on the height grid into a
## room with no top-down layout yet is closed by a gate ("The road beyond is still being drawn."), so the side view is
## never entered mid-game. A way out of a side-view room (a save from before the gate) stays open, back onto the grid.
func prototype_gate(c, from_room: String, to_room: String) -> bool:
	return c != null and str(c.view) == "topdown" and to_room != "" and TopdownRoom.has_layout(from_room) and not TopdownRoom.has_layout(to_room)

func portal_state(c, portal: Dictionary) -> Dictionary:
	var target := str(portal.get("to", ""))
	if ContentDB.room(target).is_empty():
		return {"open": false, "text": Tx.t("sim.world.coming_soon")}
	# The prototype's gate comes before every other lock (the debug tools' too): a way never shown yet stays hidden.
	if game.room_rt != null and prototype_gate(c, game.room_rt.room_id, target):
		if portal.get("type", "") == "hidden" and not c.quests.has_flag(seen_flag(game.room_rt.room_id, str(portal.id))):
			return {"open": false, "text": "", "hidden": true}
		return {"open": false, "text": Tx.t("sim.world.road_being_drawn"), "gate": true}
	if world.debug_open_ways: return {"open": true, "text": ContentDB.name_of("rooms", target)}
	if portal.has("requires") and not RequirementRules.passes(portal.requires, game.ctx(c)):
		return {"open": false, "text": str(portal.get("locked_text", RequirementRules.first_failure_text(portal.requires, game.ctx(c))))}
	# A quest whose step is to leave this room keeps its ways shut until the steps before it are done, and says which.
	var hold: String = game.quest.room_hold(c, game.room_rt.room_id) if game.room_rt != null else ""
	if hold != "": return {"open": false, "text": Tx.t("sim.world.step_first") % hold}
	if portal.get("type", "") == "hidden" and not c.quests.has_flag(seen_flag(game.room_rt.room_id, str(portal.id))):
		return {"open": false, "text": "", "hidden": true}
	return {"open": true, "text": ContentDB.name_of("rooms", target)}

## Is this portal open to this character, seen from its own room (requirements, hidden ways found)?
func portal_open(c, room_id: String, p: Dictionary) -> bool:
	if ContentDB.room(str(p.get("to", ""))).is_empty(): return false
	if p.has("array"): return world.arrays.array_open(c, room_id, str(p.id), str(p.array))   # decision 42: a transfer array's link
	if prototype_gate(c, room_id, str(p.get("to", ""))): return false   # decision 41: no route, mark or hop past the gate
	if p.has("requires") and not RequirementRules.passes(p.requires, game.ctx(c)): return false
	if str(p.get("type", "")) == "hidden" and not c.quests.has_flag(seen_flag(room_id, str(p.id))): return false
	return true

## The shortest way between two rooms through the portals open to this character (its realm, quests and arts):
## [{room, portal, to}], [] when there is none or it is already there.
func route(c, from_room: String, to_room: String) -> Array:
	return WorldRules.route(from_room, to_room, func(room_id: String, p: Dictionary) -> bool: return portal_open(c, room_id, p))

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
		return world.load_room(c, str(back.room), "", Vector2(float(back.x), float(back.y)))
	emit("portal_used", {"actor": c.id, "portal": portal_id, "room": game.room_rt.room_id, "to": str(p.to), "hidden": str(p.get("type", "")) == "hidden"})
	var r := world.load_room(c, str(p.to), str(p.get("to_portal", "")))
	return r

func apply_teleport(actor_id: String, target: String, portal := "") -> void:
	var c = game.character(actor_id)
	if c == null: return
	match target:
		"last_town":
			var town = c.last_town if c.last_town != "" else "lf_village"
			world.load_room(c, town, "town_arrival")
		"dungeon_exit":
			var exit_room = str(game.room_rt.def.get("dungeon_exit", c.last_town)) if game.room_rt else c.last_town
			world.load_room(c, exit_room if exit_room != "" else "lf_village", "")
		_:
			if not ContentDB.room(target).is_empty(): world.load_room(c, target, portal)

func apply_return_to_shrine(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	# A story set piece there is no walking back into (the Hollow Night, instanced) wakes you inside it at its `refuge`
	# (Aunt Ping's door), and its event begins again: a fall there never leaves you in the day with the night unfinished.
	var here: RoomRuntime = game.room_rt
	if here != null and str(here.def.get("refuge", "")) != "":
		var ro: Dictionary = here.object_def(str(here.def.refuge))
		var ra: Array = ro.get("at", here.def.get("spawn_point", [200, 800]))
		world.load_room(c, here.room_id, "", Vector2(float(ra[0]), float(ra[1])))
		return
	if c.last_shrine.is_empty():
		var start := str(ContentDB.zone("jade_river_valley").get("start_room", "lf_fishers_hut"))
		var sr = c.last_town if c.last_town != "" else start
		world.load_room(c, sr, "")
		return
	world.load_room(c, str(c.last_shrine.room), "", Vector2(float(c.last_shrine.x) + 50, float(c.last_shrine.y) + 20))

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
	# Decision 41: a stone another character found off the top-down map is past the prototype's gate.
	if game.room_rt != null and prototype_gate(c, game.room_rt.room_id, str(stone.get("room", ""))):
		return fail("gate", {"text": Tx.t("sim.world.road_being_drawn")})
	var fee := teleport_fee(stone_id, c)
	if c.inventory.count("spirit_stone_shard") < fee: return fail("no_fee", {"text": Tx.plural("sim.world.needs_spirit_stone_shard", fee) % fee})
	game.inventory.apply_remove(c.id, "spirit_stone_shard", fee, "teleport")
	emit("teleported", {"actor": c.id, "stone": stone_id})
	return world.load_room(c, str(stone.room), "", _stone_spot(c, stone, stone_id))

## Where a teleport lands: beside its stone, the side view's spot, or on the grid in front of the stone where the
## room's layout sets it.
func _stone_spot(c, stone: Dictionary, stone_id: String) -> Vector2:
	var grid := world.grid_for(c, str(stone.room))
	if grid != null:
		for o in ContentDB.room(str(stone.room)).get("objects", []):
			if str(o.get("type", "")) == "teleport_stone" and str(o.get("stone", o.id)) == stone_id and grid.def.get("place", {}).has(str(o.id)):
				return TopdownRoom.cell_point(grid.def.place[str(o.id)]) + Vector2(0, TopdownRoom.TILE)
	return Vector2(float(stone.at[0]) + 60, float(stone.at[1]) + 10)

## Spirit Sense (S17, SA1/SA2): a soul pulse that reveals hidden portals and
## fog-hidden monsters within the sense radius.
func sense_pulse(c) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "spirit_sense"): return fail("locked", {"text": Unlocks.locked_text("spirit_sense")})
	if c.pools.cooldown("sense") > 0.0: return fail("cooldown")
	var cost := 10.0
	if StatRules.gate_flag(c, "sense_cost_25"): cost *= float(ContentDB.stat_const("gates", {}).get("sense_cost_mult", 0.75))   # S10 Spirit 25
	if c.pools.get_value("soul") < cost: return fail("no_soul", {"text": Tx.t("sim.world.not_enough_soul")})
	game.combat.apply_resource_change(c.id, "soul", -cost, "spirit_sense")
	c.pools.cooldowns["sense"] = 6.0
	var st: ActorState = game.actor_state(c.id)
	var here: Vector2 = st.plane if st else Vector2(float(c.position.x), float(c.position.y))
	var radius := maxf(420.0, c.stats.value("sense_radius"))
	var found := 0
	if game.room_rt:
		for p in game.room_rt.def.get("portals", []):
			if p.get("type", "") != "hidden" or not Unlocks.is_unlocked(c.id, "hidden_portals"): continue
			var at: Array = p.get("at", [0, 0])
			var f := seen_flag(game.room_rt.room_id, str(p.id))
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
			var hs := world.herbs.herb_state(o)
			world.sensed_herbs[str(o.id)] = {"until": game.sim_time + 8.0, "utc": Clock.now_utc(), "ripe": hs.ripe, "seconds": float(hs.seconds), "dormant": hs.dormant,
				"season": str(o.get("season", "")), "spent": game.room_rt.objects.get(str(o.id), {}).get("state", "ready") == "depleted"}
			herbs += 1
	emit("spirit_sense_pulsed", {"actor": c.id, "x": here.x, "y": here.y, "radius": radius, "found": found, "herbs": herbs})
	emit("system_used", {"actor": c.id, "system": "spirit_sense"})
	return ok({"found": found})
