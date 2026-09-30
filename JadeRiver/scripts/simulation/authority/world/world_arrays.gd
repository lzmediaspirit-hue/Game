extends "res://scripts/simulation/authority/world/world_part.gd"
## World · the sect's transfer arrays (decision 42). A sect keeps transfer arrays at its key places (the gate's plaza by
## the steward, the mentor's peak) and one at the Marsh Edge's watch post that both sects keep. A disciple's token opens
## them once the Weapon Hall is done (the unlock `transfer_array`, taught at the gate as Strange Tracks begins). A node
## answers the token once it knows it: stood on or tapped (the lesson keys the gate's and the watch post's, the mentor
## his peak's). Tapped, it asks where to among the nodes the token knows; a route (the tracker, auto-path) takes one as
## a way (WorldRules.ways_out). Free: the sect's own; the teleport stones' shards are for the world beyond.

const ARRAY_ATTUNE_R := 96.0

static func array_flag(node_id: String) -> String:
	return "array_" + node_id

func array_attuned(c, node_id: String) -> bool:
	return c != null and c.quests.has_flag(array_flag(node_id))

## A node of the character's own sect's network, or one both sects keep.
static func array_mine(c, node: Dictionary) -> bool:
	var net := str(node.get("network", ""))
	return net == "" or (c != null and net == str(c.training_sect.get("id", "")))

## May the character take the array at `from_id` (in `from_room`) to `to_id` now: the arrays opened to it, both nodes
## its sect's and known to its token, and never past the prototype's gate.
func array_open(c, from_room: String, from_id: String, to_id: String) -> bool:
	if c == null or not Unlocks.is_unlocked(c.id, "transfer_array"): return false
	var nodes := WorldRules.array_nodes()
	var a: Dictionary = nodes.get(from_id, {})
	var b: Dictionary = nodes.get(to_id, {})
	if a.is_empty() or b.is_empty() or not array_mine(c, a) or not array_mine(c, b): return false
	if not array_attuned(c, from_id) or not array_attuned(c, to_id): return false
	return not world.portals.prototype_gate(c, from_room, str(b.room))

func attune_array(c, node_id: String) -> void:
	if c == null or array_attuned(c, node_id) or not Unlocks.is_unlocked(c.id, "transfer_array"): return
	if not array_mine(c, WorldRules.array_nodes().get(node_id, {})): return
	game.quest.apply_flag(c.id, array_flag(node_id))
	emit("array_attuned", {"actor": c.id, "object": node_id})

## Where the array at `node_id` can send the character now: [{id, room, network}] in data order.
func array_destinations(c, node_id: String) -> Array:
	var here := str(WorldRules.array_nodes().get(node_id, {}).get("room", ""))
	return WorldRules.array_links(node_id).filter(func(n): return array_open(c, here, node_id, str(n.id)))

## What the travel picker shows at the node `node_id` (decision 42: its own small page, not a talk): the array's name,
## the room it stands in, a line, and where the token can go from it ([{id, room, name}] in data order: the nodes of its
## network the token knows, never one past the prototype's gate, array_destinations).
func array_view(c, node_id: String) -> Dictionary:
	var node: Dictionary = WorldRules.array_nodes().get(node_id, {})
	var here := str(node.get("room", ""))
	var label := Tx.t("sim.world.array_speaker")
	for o in ContentDB.room(here).get("objects", []):
		if str(o.get("id", "")) == node_id: label = str(o.get("name", label))
	var dests: Array = []
	if c != null and not node.is_empty():
		for n in array_destinations(c, node_id):
			dests.append({"id": str(n.id), "room": str(n.room), "name": ContentDB.name_of("rooms", str(n.room))})
	return {"id": node_id, "name": label, "room": here, "room_name": ContentDB.name_of("rooms", here) if here != "" else "",
		"line": Tx.t("sim.world.array_where") if not dests.is_empty() else Tx.t("sim.world.array_alone"), "destinations": dests}

## Keep the nodes the character walks onto (the shrines' rule: close by is enough).
func attune_arrays(c, rt: RoomRuntime, st: ActorState) -> void:
	if st == null or not Unlocks.is_unlocked(c.id, "transfer_array"): return
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) != "transfer_array" or array_attuned(c, str(o.id)): continue
		var at: Array = o.get("at", [0, 0])
		if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) <= ARRAY_ATTUNE_R and absf(st.altitude - float(o.get("alt", 0.0))) <= WorldAuthority.REACH_ALT:
			attune_array(c, str(o.id))

## Step onto the array at `from_id` and come out on the one at `to_id`.
func array_travel(c, from_id: String, to_id: String) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var o: Dictionary = game.room_rt.object_def(from_id)
	if o.is_empty() or str(o.get("type", "")) != "transfer_array": return fail("unknown_object")
	var st: ActorState = game.actor_state(c.id)
	var at: Array = o.get("at", [0, 0])
	if st != null and st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > world.context.reach_of(o) + 20.0: return fail("too_far")
	if game.combat.is_wounded(c.id): return fail("wounded")
	attune_array(c, from_id)
	if not array_open(c, game.room_rt.room_id, from_id, to_id):
		var node: Dictionary = WorldRules.array_nodes().get(to_id, {})
		var gate: bool = not node.is_empty() and world.portals.prototype_gate(c, game.room_rt.room_id, str(node.room))
		return fail("sealed", {"text": Tx.t("sim.world.road_being_drawn") if gate else Tx.t("sim.world.array_unknown")})
	var to: Dictionary = WorldRules.array_nodes()[to_id]
	if c.cultivator.meditating: game.progression.stop_meditation(c, "portal")
	emit("array_travelled", {"actor": c.id, "from": from_id, "to": to_id, "room": game.room_rt.room_id, "to_room": str(to.room)})
	return world.load_room(c, str(to.room), "", _array_spot(c, to))

## Where an array lands: on the far node, on the grid where its layout sets it; in the side view on its ground.
func _array_spot(c, node: Dictionary) -> Vector2:
	var grid := world.grid_for(c, str(node.room))
	if grid != null and grid.def.get("place", {}).has(str(node.id)):
		return TopdownRoom.cell_point(grid.def.place[str(node.id)])
	return Vector2(float(node.at[0]), float(node.at[1]) + 20.0)
