class_name WorldIdle
extends WorldPart
## WorldAuthority's part: S49 mobile conventions: idle rooms, auto-hunt and auto-path, and the quest direction mark
## (P1). The toggles and walks under way are the authority's `auto_hunt` and `auto_paths`.

## Rooms where auto-hunt is always off (S49): bosses, trials, dungeons, story instances, secret places.
const AUTO_HUNT_OFF := ["boss_arena", "trial", "dungeon", "story", "secret", "prologue"]

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
	return world.auto_hunt.has(actor_id)

func set_auto_hunt(c, on: bool) -> Dictionary:
	if not on:
		end_auto_hunt(c.id, "off")
		return ok({"on": false})
	var why := auto_hunt_block(c)
	if why != "": return fail(why, {"text": Tx.t("sim.world.auto_hunt_" + why)})
	world.auto_paths.erase(c.id)
	world.auto_hunt[c.id] = true
	emit("auto_hunt_changed", {"actor": c.id, "on": true, "reason": ""})
	return ok({"on": true})

func end_auto_hunt(actor_id: String, reason: String) -> void:
	if not world.auto_hunt.has(actor_id): return
	world.auto_hunt.erase(actor_id)
	emit("auto_hunt_changed", {"actor": actor_id, "on": false, "reason": reason})

func tick_auto_hunt(c, delta: float) -> void:
	if not world.auto_hunt.has(c.id): return
	world.auto_check -= delta
	if world.auto_check > 0.0: return
	world.auto_check = 0.5
	var why := auto_hunt_block(c)
	if why != "": end_auto_hunt(c.id, why)

## Decision 43: with `place` (a place's id, data/places.json) the walk goes on inside the place's room to the cell its
## user stands on (the Menu's and the map's travel to a place), from another room or from this one.
func start_auto_path(c, target: String, place := "") -> Dictionary:
	var goal := PlaceRules.get_place(place) if place != "" else {}
	if not goal.is_empty(): target = str(goal.room)
	if target == "":
		end_auto_path(c.id, "cancelled")
		return ok()
	if game.room_rt == null: return fail("no_room")
	var r: Array = []
	if target == game.room_rt.room_id:
		if goal.is_empty(): return fail("here", {"text": Tx.t("sim.world.auto_path_here")})
	else:
		r = world.route(c, game.room_rt.room_id, target)
		if r.is_empty(): return fail("no_route", {"text": Tx.t("sim.world.auto_path_none")})
	end_auto_hunt(c.id, "path")
	world.auto_paths[c.id] = {"target": target, "route": r}
	if not goal.is_empty(): world.auto_paths[c.id].place = place
	emit("auto_path_started", {"actor": c.id, "target": target, "rooms": r.size(), "place": place, "name": str(goal.get("name", ""))})
	return ok({"route": r, "place": place})

## Where auto-path is heading in this room: the portal to take ({portal, x, y, press_up}), in the place's own room the
## cell its user stands on ({place, x, y}), or {}.
func auto_path_step(c) -> Dictionary:
	var ap: Dictionary = world.auto_paths.get(c.id, {}) if c != null else {}
	if ap.is_empty() or game.room_rt == null: return {}
	for s in ap.route:
		if str(s.room) != game.room_rt.room_id: continue
		var at := _step_point(s)
		if at.is_empty(): return {}
		if s.get("dock", false): return {"dock": str(s.portal), "x": float(at.x), "y": float(at.y), "press_up": false, "surface": ""}
		return {"portal": str(s.portal), "x": float(at.x), "y": float(at.y), "press_up": bool(at.p.get("press_up", false)), "surface": str(at.p.get("surface", ""))}
	if ap.has("place") and game.room_rt.room_id == str(ap.target):
		var pl := PlaceRules.get_place(str(ap.place))
		var sp := PlaceRules.stand_point(pl) if not WorldAuthority.side_view(game.room_rt) else _side_place_point(pl)
		return {"place": str(ap.place), "object": str(pl.get("object", "")), "x": sp.x, "y": sp.y}
	return {}

## A side-view room: the place's object where the side view has it (the place's own point without one).
func _side_place_point(pl: Dictionary) -> Vector2:
	var o: Dictionary = game.room_rt.object_def(str(pl.get("object", "")))
	return Vector2(float(o.at[0]), float(o.at[1])) if not o.is_empty() else PlaceRules.point(pl)

## Decision 43: the walk to a place ends at its user's cell.
func auto_path_arrive(c) -> void:
	if c == null or not world.auto_paths.has(c.id): return
	var pl := PlaceRules.get_place(str(world.auto_paths[c.id].get("place", "")))
	end_auto_path(c.id, "arrived")
	if not pl.is_empty(): emit("place_reached", {"actor": c.id, "place": str(pl.id), "object": str(pl.object), "room": str(pl.room)})

## Where a route step starts in this room: its dock object or its portal ({x, y, p: the portal}), {} when it is not here.
func _step_point(s: Dictionary) -> Dictionary:
	if s.get("dock", false):
		for o in game.room_rt.def.get("objects", []):
			if str(o.id) == str(s.portal): return {"x": float(o.at[0]), "y": float(o.at[1]), "p": {}}
		return {}
	var p = game.room_rt.portal_def(str(s.portal))
	return {} if p.is_empty() else {"x": float(p.at[0]), "y": float(p.at[1]), "p": p}

## P1 quest direction: where the tracked quest leads from this room, the main story's first:
## {target, next, portal, x, y} (the exit to take here) or {} when nothing tracked leads elsewhere.
func guide_step(c) -> Dictionary:
	if c == null or game.room_rt == null: return {}
	var here := str(game.room_rt.room_id)
	var goal := guide_target(c)
	if goal == "": return {}
	var key := here + ">" + goal
	if str(world.guide_cache.get("key", "")) == key and Clock.now_utc() - float(world.guide_cache.get("at", 0.0)) < 5.0: return world.guide_cache.step
	var step := {}
	var r := world.route(c, here, goal)
	# Behind a hidden way not yet seen, the mark leads as far as the room that hides it (Spirit Sense shows it there).
	if r.is_empty():
		for hid in WorldRules.rooms_with("hidden_to=" + goal):
			r = world.route(c, here, str(hid))
			if not r.is_empty(): break
	if not r.is_empty() and str(r[0].room) == here:
		var at := _step_point(r[0])
		if not at.is_empty(): step = {"target": goal, "next": str(r[0].to), "portal": str(r[0].portal), "x": float(at.x), "y": float(at.y)}
	world.guide_cache = {"key": key, "at": Clock.now_utc(), "step": step}
	return step

## The room the tracker leads to (the main story's first: its quest under way, or its next one between quests), other
## than where the character stands.
func guide_target(c) -> String:
	if c == null: return ""
	var here := str(c.position.get("room", ""))
	# Decision 43: a tutorial leading to a place (the coach's guide) takes the direction mark first, while it leads.
	var taught: String = game.tutorials.goal_of(c) if game.tutorials != null else ""
	if taught != "" and taught != here: return taught
	var goal := ""
	for q in game.quest.tracker(c):
		var t := str(q.get("target_room", ""))
		if t == "" or t == here: continue
		if goal == "" or QuestAuthority.leads(str(q.kind)): goal = t
		if QuestAuthority.leads(str(q.kind)): break
	return goal

## "Room · Region" for a room id, as the tracker and the map name a destination.
static func place_name(room_id: String) -> String:
	var rd := ContentDB.room(room_id)
	var nm := str(rd.get("name", room_id))
	var zone := ContentDB.entry("zones", str(rd.get("zone", "")))
	for rg in zone.get("regions", []):
		if str(rg.get("id", "")) == str(rd.get("region", "")) and str(rg.get("name", "")) != nm: return "%s · %s" % [nm, str(rg.name)]
	return nm

func auto_path_target(c) -> String:
	return str(world.auto_paths.get(c.id, {}).get("target", "")) if c != null else ""

func end_auto_path(actor_id: String, reason: String) -> void:
	if not world.auto_paths.has(actor_id): return
	var target := str(world.auto_paths[actor_id].target)
	world.auto_paths.erase(actor_id)
	emit("auto_path_ended", {"actor": actor_id, "target": target, "reason": reason})

## Each room reached: arrived, still on the way, or off the route (it finds a new one from here).
func auto_path_room(_p: Dictionary) -> void:
	var c = game.active()
	if c == null or not world.auto_paths.has(c.id) or game.room_rt == null: return
	var ap: Dictionary = world.auto_paths[c.id]
	if game.room_rt.room_id == str(ap.target):
		if not ap.has("place"): end_auto_path(c.id, "arrived")   # a place's walk goes on to it (auto_path_step)
		return
	if (ap.route as Array).any(func(s): return str(s.room) == game.room_rt.room_id): return
	if game.room_rt.def.get("crossing", false): return   # under sail: the route goes on at the far pier
	var r := world.route(c, game.room_rt.room_id, str(ap.target))
	if r.is_empty(): end_auto_path(c.id, "lost")
	else: ap.route = r

## At a Starsea dock the route boards a vessel; without one (or a chart) it stops there and says why.
func auto_path_board(c, dock_id: String) -> Dictionary:
	# Decision 42: a transfer array on the route is taken to the node the route names.
	for s in world.auto_paths.get(c.id, {}).get("route", []):
		if game.room_rt != null and str(s.room) == game.room_rt.room_id and str(s.portal) == dock_id and str(s.get("array", "")) != "":
			var ra := world.array_travel(c, dock_id, str(s.array))
			if not ra.get("ok", false): end_auto_path(c.id, "dock")
			return ra
	var r := world.interact(c, dock_id)
	if not r.get("ok", false): end_auto_path(c.id, "dock")
	return r

## It stops at danger: the moment something strikes you, the controls are yours again.
func auto_path_danger(p: Dictionary) -> void:
	if str(p.get("target_kind", "")) == "player" and world.auto_paths.has(str(p.get("target", ""))): end_auto_path(str(p.target), "danger")
