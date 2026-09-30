extends "res://scripts/simulation/authority/world/world_part.gd"
## World · Starsea voyages (S18): board at a dock, cross in the crossing's own room and make port at the far end. The
## crossings under way are the authority's `voyages`.

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
	world.voyages[c.id] = {"route": route_id, "vessel": vessel, "seconds": float(v.get("base_s", 60)) / maxf(0.25, speed)}
	emit("voyage_started", {"actor": c.id, "route": route_id, "vessel": vessel, "seconds": world.voyages[c.id].seconds})
	return world.load_room(c, str(v.crossing), "")

## The crossing's event ended: make port at the far end of the route.
func apply_voyage_arrive(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null or not world.voyages.has(actor_id): return
	var v := ContentDB.entry("voyages", str(world.voyages[actor_id].route))
	world.voyages.erase(actor_id)
	emit("voyage_arrived", {"actor": actor_id, "route": str(v.get("id", "")), "room": str(v.get("to", ""))})
	world.load_room(c, str(v.get("to", "")), str(v.get("to_portal", "")))
