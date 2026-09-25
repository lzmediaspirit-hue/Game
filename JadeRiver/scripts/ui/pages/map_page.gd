extends Page
## World map (S18, Part 9.6): one painted scroll per discovered zone. The valley shows
## the Jade River running through it; the Azure Expanse shows islands in a sea of cloud.
## Regions carry Level ranges, visited rooms, locks, the attunement they ask for, room
## hazards with the attribute that answers them, and field boss timers. Tap a region for its rooms; tabs switch between zones.

var sel := ""
var zone_id := "jade_river_valley"

func _init() -> void:
	title = Tx.t("ui.map.jade_river_valley")

func setup() -> void:
	var ch = c()
	if ch == null: return
	var room_id := str(ch.position.get("room", ""))
	var here_zone := str(ContentDB.zone_of_room(room_id).get("id", ""))
	if here_zone != "": zone_id = here_zone
	sel = str(ContentDB.room(room_id).get("region", ""))
	# A tab per zone the account has set foot in (the valley always).
	tabs = []
	for z in ContentDB.all("zones"):
		if str(z.id) == "jade_river_valley" or _zone_seen(str(z.id)):
			tabs.append({"id": str(z.id), "label": str(z.get("name", z.id))})
	if tabs.size() < 2: tabs = []
	for i in tabs.size():
		if str(tabs[i].id) == zone_id: tab = i
	title = str(ContentDB.zone(zone_id).get("name", title))

func _zone_seen(zid: String) -> bool:
	for id in ContentDB.zone(zid).get("rooms", []):
		if Game.account.visited_rooms.has(str(id)): return true
	return false

func regions() -> Array:
	return ContentDB.zone(zone_id).get("regions", []).filter(func(r): return not r.get("hidden", false))

func region_rooms(rid: String) -> Array:
	var out: Array = []
	for id in ContentDB.rooms:
		var r: Dictionary = ContentDB.rooms[id]
		if str(r.get("region", "")) == rid and str(r.get("zone", "")) == zone_id and not r.get("instanced", false): out.append(id)
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
	var sky := zone_id != "jade_river_valley"
	draw_rect(map_r, Color("c9d6dc") if sky else Color("d9ccaa"))
	draw_rect(map_r.grow(-6), Color("e2ebee") if sky else Color("e8dcbc"))
	draw_rect(map_r, UiKit.BRONZE, false, 3)
	var pts := {}
	for r in regions():
		var m: Array = r.get("map", [0.5, 0.5])
		pts[str(r.id)] = map_r.position + Vector2(float(m[0]) * map_r.size.x, float(m[1]) * map_r.size.y)
	if sky: _draw_cloud_sea(map_r, pts)
	else: _draw_valley(map_r)
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
		var planned: bool = r.get("planned", false)
		var col := UiKit.BRONZE if seen else Color(0.45, 0.42, 0.36)
		draw_circle(p, 17, UiKit.INK if not planned else Color(0.3, 0.34, 0.38, 0.6))
		draw_circle(p, 14, (col if rid != sel else UiKit.GOLD) if not planned else Color(0.62, 0.68, 0.72, 0.8))
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
	var att = ContentDB.zone(zone_id).get("attunement")
	if att is Dictionary and reg.has("attunement"):
		var have: float = Game.progression.attunement_value(ch, zone_id) if str(ContentDB.zone_of_room(str(ch.position.get("room", ""))).get("id", "")) == zone_id else float(ch.cultivator.attunement.get(zone_id, 0.0))
		var need := float(reg.attunement)
		text(Vector2(right.position.x + 20, y + 10), Tx.t("ui.map.attunement_need") % [str(att.get("name", "")), int(need), int(have)], 17,
			UiKit.BRIGHT_JADE if have >= need else UiKit.RED)
		y += 28
	if reg.get("planned", false):
		para(Rect2(right.position.x + 20, y + 4, right.size.x - 40, 80), Tx.t("ui.map.way_not_open"), 17, UiKit.HOLLOW)
		return
	for id in region_rooms(sel):
		var seen2: bool = Game.account.visited_rooms.has(id)
		var room := ContentDB.room(id)
		var here_room: bool = id == str(ch.position.get("room", ""))
		text(Vector2(right.position.x + 24, y + 22), ("▶ " if here_room else ("· " if seen2 else "? ")) + (str(room.get("name", id)) if seen2 else Tx.t("ui.map.unknown")), 18,
			UiKit.GOLD if here_room else (UiKit.PAPER if seen2 else UiKit.HOLLOW))
		# S18 room data: its hazards and the attribute that answers them.
		if seen2:
			for hz in HazardRules.summary(ch, room):
				text(Vector2(right.position.x + 44, y + 44), Tx.t("ui.map.hazard") % [str(hz.name), Tx.t("ui.cultivation." + str(hz.stat)), int(hz.need)], 15,
					UiKit.BRIGHT_JADE if hz.answered else UiKit.PALE_GOLD)
				y += 20
		for sp in room.get("spawns", []):
			if sp.get("field_boss", false) and Unlocks.is_unlocked(ch.id, "field_boss_timers"):
				var until := float(Game.account.rooms.get("field_boss_timers", {}).get(str(sp.enemy), 0.0))
				var left_s := int(until - Clock.now_utc())
				text(Vector2(right.position.x + 44, y + 44), Tx.t("ui.map.boss") % ("ready" if left_s <= 0 else "%dm" % (left_s / 60 + 1)), 15, UiKit.RED)
				y += 20
		y += 28
		if y > right.end.y - 40: break

## The valley: ink mountains along the top and the Jade River from east to west.
func _draw_valley(map_r: Rect2) -> void:
	for i in 9:
		var bx := map_r.position.x + 40 + i * 88
		var by := map_r.position.y + 70 + (i % 3) * 8
		draw_colored_polygon(PackedVector2Array([Vector2(bx - 44, by + 20), Vector2(bx, by - 30 - (i % 2) * 14), Vector2(bx + 44, by + 20)]), Color(0.35, 0.42, 0.40, 0.35))
	var river := PackedVector2Array()
	for i in 41:
		var f := i / 40.0
		river.append(map_r.position + Vector2(map_r.size.x * (1.0 - f), map_r.size.y * (0.62 + 0.10 * sin(f * 7.0))))
	draw_polyline(river, Color("2c9e8f"), 14.0)
	draw_polyline(river, Color("67d6bd"), 4.0)

## The Expanse: soft cloud bands, and each region an island adrift under its marker.
func _draw_cloud_sea(map_r: Rect2, pts: Dictionary) -> void:
	for k in 7:
		var y := map_r.position.y + 40 + k * (map_r.size.y - 60) / 6.0
		var band := PackedVector2Array()
		for i in 33:
			var f := i / 32.0
			band.append(Vector2(map_r.position.x + 10 + f * (map_r.size.x - 20), y + 6.0 * sin(f * 9.0 + k * 1.7)))
		draw_polyline(band, Color(1, 1, 1, 0.55), 5.0)
	for rid in pts:
		var p: Vector2 = pts[rid]
		var isle := PackedVector2Array([p + Vector2(-34, 8), p + Vector2(34, 8), p + Vector2(18, 20), p + Vector2(4, 38), p + Vector2(-10, 24), p + Vector2(-26, 18)])
		draw_colored_polygon(isle, Color(0.42, 0.48, 0.60, 0.55))
		draw_line(p + Vector2(-34, 8), p + Vector2(34, 8), Color(0.45, 0.62, 0.50, 0.8), 4)

func on_action(id: String, data) -> void:
	if id == "sel": sel = str(data)
	if id == "_tab":
		zone_id = str(data)
		title = str(ContentDB.zone(zone_id).get("name", title))
		sel = ""
