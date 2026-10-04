extends RefCounted
## Which ways of a room lead into a building, from the room's own data (data/rooms, tools/data/world.py): a way marked
## `facade`, or a door or a gate standing in a building roof's front (within 40 below the roof's front edge, across its
## width; an archway a way passes under, art "gate", is no building) in a room that is not an interior. The suites hold
## each such way to its doorway on the grid (TopdownRoom.entrance "building"): tutorial_order, data_validation and
## visibility_suite. (The side view's PortalView.building_front read the same data to draw the doorway; it went with
## the side view in S12a.)

static func into_building(p: Dictionary, room: Dictionary) -> bool:
	if p.get("facade", false): return true
	if not str(p.get("type", "")) in ["door", "gate"] or p.has("surface") or not room.get("wall", {}).is_empty(): return false
	var at: Array = p.get("at", [0, 0])
	var x := float(at[0])
	var y := float(at[1])
	for s in room.get("surfaces", []):
		if str(s.get("kind", "")) != "roof" or str(s.get("art", "")) == "gate": continue
		var r: Array = s.get("rect", [0, 0, 0, 0])
		var front := float(r[1]) + float(r[3])
		if x >= float(r[0]) and x <= float(r[0]) + float(r[2]) and y >= front and y <= front + 40.0: return true
	return false
