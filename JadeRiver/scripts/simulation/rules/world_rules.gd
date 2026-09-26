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

static var _npc_rooms: Dictionary = {}

## The room a named NPC stands in (the first one that places them), "" when none does.
static func npc_room(npc_id: String) -> String:
	if _npc_rooms.is_empty():
		for rid in ContentDB.rooms:
			for o in ContentDB.room(str(rid)).get("objects", []):
				if str(o.get("type", "")) == "npc" and not _npc_rooms.has(str(o.get("npc", ""))): _npc_rooms[str(o.get("npc", ""))] = str(rid)
	return str(_npc_rooms.get(npc_id, ""))
