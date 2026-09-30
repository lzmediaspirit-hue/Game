extends Node
## Audit 45 DUP-10 · the grid's walking rules in parity. The rooms' checks (tools/data/topdown_rooms.py) walk the layouts
## with their own Grid, so they run without Godot; `topdown_rooms.py --check` asks the game, through this scene, for what
## its own TopdownRoom and TopdownRoute make of every layout, and compares the two cell for cell:
##   floor   each cell's floor for a body (TopdownRoom.cell_floor: a prop's top, a stair's slope, the places' solid
##           cells; null where nothing stands: a prop's wall, the water, the room's edge)
##   reach   from each start the request names, the cells auto-path reaches (TopdownRoute.reach, the tracker's go
##           button: walking, stairs, drops and a hop a level up), one character per cell, row by row ("1" reached)
##
## Run from JadeRiver/: godot --headless --path . res://tools/data/grid_parity.tscn -- <request.json> <answer.json>
## The request is {"rooms": {room id: [[x, y], ...]}} (the starts, as cells); the answer {room id: {"size", "floor",
## "reach"}}. It exits 1 when it cannot read the request or write the answer.

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var req = JSON.parse_string(FileAccess.get_file_as_string(args[0])) if args.size() >= 2 else null
	if not (req is Dictionary and req.get("rooms") is Dictionary):
		push_error("grid_parity: no request (-- <request.json> <answer.json>)")
		get_tree().quit(1)
		return
	var out := {}
	for rid in req.rooms:
		var room := TopdownRoom.load_room(str(rid))
		var floor: Array = []
		for y in room.h:
			var row: Array = []
			for x in room.w:
				var f := room.cell_floor(Vector2i(x, y))
				row.append(null if f == INF else f)
			floor.append(row)
		var reach: Array = []
		for s in req.rooms[rid]:
			var bits := PackedByteArray()
			bits.resize(room.w * room.h)
			bits.fill(48)
			for c in TopdownRoute.reach(room, Vector2i(int(s[0]), int(s[1])), true): bits[c.y * room.w + c.x] = 49
			reach.append(bits.get_string_from_ascii())
		out[rid] = {"size": [room.w, room.h], "floor": floor, "reach": reach}
	var f := FileAccess.open(args[1], FileAccess.WRITE)
	if f == null:
		push_error("grid_parity: cannot write " + args[1])
		get_tree().quit(1)
		return
	f.store_string(JSON.stringify(out))
	f.close()
	get_tree().quit(0)
