extends Page
## World map (S18, Part 9.6): the valley as a painted scroll with the Jade River
## running through it; regions with Level ranges, visited rooms, locks and field
## boss timers. Tap a region for its rooms.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.map.jade_river_valley")

func setup() -> void:
	var ch = c()
	if ch: sel = str(ContentDB.room(str(ch.position.get("room", ""))).get("region", ""))

func regions() -> Array:
	return ContentDB.zone("jade_river_valley").get("regions", []).filter(func(r): return not r.get("hidden", false))

func region_rooms(rid: String) -> Array:
	var out: Array = []
	for id in ContentDB.rooms:
		var r: Dictionary = ContentDB.rooms[id]
		if str(r.get("region", "")) == rid and not r.get("instanced", false): out.append(id)
	out.sort()
	return out

func visited(rid: String) -> bool:
	for id in region_rooms(rid):
		if Game.account.visited_rooms.has(id): return true
	return false

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var map_r := Rect2(content.position.x, content.position.y, 780, content.size.y)
	draw_rect(map_r, Color("d9ccaa"))
	draw_rect(map_r.grow(-6), Color("e8dcbc"))
	draw_rect(map_r, UiKit.BRONZE, false, 3)
	var pts := {}
	for r in regions():
		var m: Array = r.get("map", [0.5, 0.5])
		pts[str(r.id)] = map_r.position + Vector2(float(m[0]) * map_r.size.x, float(m[1]) * map_r.size.y)
	# Ink mountains along the top.
	for i in 9:
		var bx := map_r.position.x + 40 + i * 88
		var by := map_r.position.y + 70 + (i % 3) * 8
		draw_colored_polygon(PackedVector2Array([Vector2(bx - 44, by + 20), Vector2(bx, by - 30 - (i % 2) * 14), Vector2(bx + 44, by + 20)]), Color(0.35, 0.42, 0.40, 0.35))
	# The Jade River: east to west through the valley.
	var river := PackedVector2Array()
	for i in 41:
		var f := i / 40.0
		river.append(map_r.position + Vector2(map_r.size.x * (1.0 - f), map_r.size.y * (0.62 + 0.10 * sin(f * 7.0))))
	draw_polyline(river, Color("2c9e8f"), 14.0)
	draw_polyline(river, Color("67d6bd"), 4.0)
	# Routes between neighbouring regions via portals.
	for r in regions():
		for id in region_rooms(str(r.id)):
			for p in ContentDB.room(id).get("portals", []):
				var to_region := str(ContentDB.room(str(p.get("to", ""))).get("region", ""))
				if to_region != "" and to_region != str(r.id) and pts.has(to_region) and str(r.id) < to_region:
					draw_line(pts[str(r.id)], pts[to_region], Color(0.35, 0.25, 0.12, 0.55), 3)
	var here := str(ContentDB.room(str(ch.position.get("room", ""))).get("region", ""))
	for r in regions():
		var rid := str(r.id)
		var p: Vector2 = pts[rid]
		var seen := visited(rid)
		var col := UiKit.BRONZE if seen else Color(0.45, 0.42, 0.36)
		draw_circle(p, 17, UiKit.INK)
		draw_circle(p, 14, col if rid != sel else UiKit.GOLD)
		if rid == here:
			draw_colored_polygon(PackedVector2Array([p + Vector2(0, -34), p + Vector2(10, -20), p + Vector2(-10, -20)]), UiKit.RED)
		var name_ := str(r.name) if seen else "?"
		UiKit.draw_outlined(self, name_, p + Vector2(-90, 36), 15, UiKit.PAPER if seen else UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, 180)
		region(Rect2(p - Vector2(30, 30), Vector2(60, 60)), "sel", rid)
	# Details.
	var right := Rect2(map_r.end.x + 20, content.position.y, content.end.x - map_r.end.x - 20, content.size.y)
	panel(right)
	if sel == "": return
	var reg := {}
	for r in regions():
		if str(r.id) == sel: reg = r
	if reg.is_empty(): return
	heading(right.position + Vector2(20, 40), str(reg.name) if visited(sel) else Tx.t("ui.map.unexplored"), right.size.x - 40)
	var lv: Array = reg.get("levels", [0, 0])
	text(right.position + Vector2(20, 72), Tx.t("ui.map.safe") if int(lv[1]) == 0 else Tx.t("ui.map.monster_level") % [int(lv[0]), int(lv[1])], 18, UiKit.MIST)
	var y := right.position.y + 90
	for id in region_rooms(sel):
		var seen2: bool = Game.account.visited_rooms.has(id)
		var room := ContentDB.room(id)
		var here_room: bool = id == str(ch.position.get("room", ""))
		text(Vector2(right.position.x + 24, y + 22), ("▶ " if here_room else ("· " if seen2 else "? ")) + (str(room.get("name", id)) if seen2 else Tx.t("ui.map.unknown")), 18,
			UiKit.GOLD if here_room else (UiKit.PAPER if seen2 else UiKit.HOLLOW))
		for sp in room.get("spawns", []):
			if sp.get("field_boss", false) and Unlocks.is_unlocked(ch.id, "field_boss_timers"):
				var until := float(Game.account.rooms.get("field_boss_timers", {}).get(str(sp.enemy), 0.0))
				var left_s := int(until - Clock.now_utc())
				text(Vector2(right.position.x + 44, y + 44), Tx.t("ui.map.boss") % ("ready" if left_s <= 0 else "%dm" % (left_s / 60 + 1)), 15, UiKit.RED)
				y += 20
		y += 28
		if y > right.end.y - 40: break

func on_action(id: String, data) -> void:
	if id == "sel": sel = str(data)
