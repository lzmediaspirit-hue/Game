class_name WorldRules
extends RefCounted
## S49 quest auto-path (mobile conventions): the room graph as data. Rooms are nodes and portals are edges; a
## caller decides which portals are open (the character's realm, quests and arts, or a validation's rule).

## The fewest rooms from one room to another, breadth first in portal data order (the same answer on every
## device): [{room, portal, to}] for each portal taken, [] when there is no way or it is already there.
static func route(from_room: String, to_room: String, can_pass: Callable) -> Array:
	if from_room == to_room or ContentDB.room(to_room).is_empty(): return []
	var prev: Dictionary = {from_room: {}}
	var queue: Array = [from_room]
	var head := 0
	while head < queue.size():
		var room_id: String = queue[head]
		head += 1
		for p in ways_out(room_id):
			var to := str(p.get("to", ""))
			if to == "" or prev.has(to) or not can_pass.call(room_id, p): continue
			prev[to] = {"room": room_id, "portal": str(p.id), "to": to, "dock": p.get("dock", false)}
			if to == to_room:
				var out: Array = []
				var at := to
				while at != from_room:
					var step: Dictionary = prev[at]
					out.push_front(step)
					at = str(step.room)
				return out
			queue.append(to)
	return []

## A room's ways out: its portals, and its Starsea docks as the voyages they sail ({id, to, requires, dock: true}).
static func ways_out(room_id: String) -> Array:
	var out: Array = (ContentDB.room(room_id).get("portals", []) as Array).duplicate()
	for o in ContentDB.room(room_id).get("objects", []):
		if str(o.get("type", "")) != "starsea_dock": continue
		var v := ContentDB.entry("voyages", str(o.get("route", "")))
		if v.is_empty() or v.get("planned", false) or str(v.get("to", "")) == "": continue
		var way := {"id": str(o.id), "to": str(v.to), "dock": true, "at": o.get("at", [0, 0])}
		if o.has("requires"): way.requires = o.requires
		out.append(way)
	return out

## A town, sect, home, interior or safe room: where a character may be switched out, or take from the Storehouse.
static func safe_room(def: Dictionary) -> bool:
	return str(def.get("type", "")) in ["town", "sect", "home", "interior"] or bool(def.get("safe", false))

static var _where: Dictionary = {}

## The rooms, in data order, that hold a thing named "<key>=<value>": an object's npc, item (a node or a pickup), type,
## set_flag, opponent or event (the set piece it starts); "enemy=<id>" for a spawn of that foe and "drop=<item>" for a
## spawn whose loot holds it as a quest drop; "to=<room>" for a way there and "hidden_to=<room>" for a hidden one.
static func rooms_with(key: String) -> Array:
	if _where.is_empty():
		for rid in ContentDB.rooms:
			var room := ContentDB.room(str(rid))
			var keys: Array = []
			for o in room.get("objects", []):
				for k in ["npc", "item", "type", "set_flag", "opponent", "event"]:
					if o.has(k): keys.append("%s=%s" % [k, o[k]])
			for sp in room.get("spawns", []):
				keys.append("enemy=" + str(sp.get("enemy", "")))
				var e := ContentDB.entry("enemies", str(sp.get("enemy", "")))
				for qd in ContentDB.entry("loot_tables", str(e.get("loot", e.get("id", "")))).get("quest_drops", []): keys.append("drop=" + str(qd.item))
			for p in room.get("portals", []): keys.append(("hidden_to=" if str(p.get("type", "")) == "hidden" else "to=") + str(p.get("to", "")))
			for k2 in keys:
				if not (_where.get(k2, []) as Array).has(str(rid)): _where[k2] = (_where.get(k2, []) as Array) + [str(rid)]
	return _where.get(key, [])

## The room a named NPC stands in (the first one that places them), "" when none does.
static func npc_room(npc_id: String) -> String:
	var at := rooms_with("npc=" + npc_id)
	return str(at[0]) if not at.is_empty() else ""

## Every room reachable from one, by the fewest ways, through the ways a caller lets it pass: room -> ways taken.
static func hops(from_room: String, can_pass: Callable) -> Dictionary:
	var out := {from_room: 0}
	var queue: Array = [from_room]
	var head := 0
	while head < queue.size():
		var room_id: String = queue[head]
		head += 1
		for p in ways_out(room_id):
			var to := str(p.get("to", ""))
			if to == "" or out.has(to) or not can_pass.call(room_id, p): continue
			out[to] = int(out[room_id]) + 1
			queue.append(to)
	return out

## The runs that pass a story event (M20): a room's own event ({event, room}) and each set piece that plays it
## ({event, set_piece}: its room event, or the story instance it opens).
static func event_runs(event: String) -> Array:
	var passes := func(ev: Dictionary) -> bool:
		return str(ev.get("id", "")) == event or (ev.get("on_complete", []) as Array).any(
			func(e): return str(e.get("kind", "")) == "event_passed" and str(e.get("event", "")) == event)
	var out: Array = []
	for rid in ContentDB.rooms:
		if passes.call(ContentDB.room(str(rid)).get("event", {})): out.append({"event": ContentDB.room(str(rid)).event, "room": str(rid)})
	var inside: Array = out.map(func(run): return run.room)
	for sp in ContentDB.all("set_pieces"):
		if str(sp.id) == event or passes.call(sp.get("room_event", {})) or str(sp.get("room", "")) in inside:
			out.append({"event": sp.get("room_event", {}), "set_piece": str(sp.id)})
	return out

## The rooms where a story event is passed: a room whose own event passes it, and the rooms whose rite circle or gong
## starts a set piece that plays it.
static func event_rooms(event: String) -> Array:
	var out: Array = []
	for run in event_runs(event): out += [run.room] if run.has("room") else rooms_with("event=" + str(run.set_piece))
	return out
