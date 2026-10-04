class_name HudMinimap
extends HudPart
## The minimap: the room in its frame (the height grid's level map), its ways, people, foes and places, the way to the
## tracked quest, and what a tap on it opens.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

func draw(c) -> void:
	var r := hud.minimap_rect
	hud.draw_style_box(UiKit.style("minimap_frame"), r)
	var room := Game.room_rt.def if Game.room_rt else {}
	UiKit.draw_text(hud, str(room.get("name", "")), r.position + Vector2(12, 19), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, r.size.x - 24, true, true)
	var inner := Rect2(r.position + Vector2(8, 26), r.size - Vector2(16, 34))
	var grid: TopdownRoom = Game.room_rt.topdown if Game.room_rt else null
	if grid == null: return
	# Redesign Phase 4: the room is drawn as its level map, the whole room fitted in the frame (the plane seen from
	# above); the ways, marks, people and foes below take the same projection.
	var k := minf(inner.size.x / (grid.w * TopdownRoom.TILE), inner.size.y / (grid.h * TopdownRoom.TILE))
	var at0 := inner.position + (inner.size - Vector2(grid.w, grid.h) * TopdownRoom.TILE * k) * 0.5
	var to_map := func(pos: Vector2, _alt: float) -> Vector2: return at0 + pos * k
	hud.draw_texture_rect(_grid_map(grid), Rect2(at0, Vector2(grid.w, grid.h) * TopdownRoom.TILE * k), false)
	for p in room.get("portals", []):
		var at: Array = p.at
		var st: Dictionary = WorldShared.portal_state(c, p)
		if st.get("hidden", false): continue
		hud.draw_circle(to_map.call(Vector2(float(at[0]), float(at[1])), 0.0), 4, UiKit.BRIGHT_JADE if st.open else UiKit.HOLLOW)
	# P1 quest direction: the exit toward the tracked quest pulses gold, and a chevron on the frame's edge points
	# the way from where you stand.
	var gs: Dictionary = WorldShared.guide_step(c)
	if not gs.is_empty():
		var gp: Vector2 = to_map.call(Vector2(float(gs.x), float(gs.y)), 0.0)
		hud.draw_arc(gp, 7.0 + sin(hud.t * 5.0) * 1.5, 0, TAU, 14, UiKit.GOLD, 2.0)
		var me: ActorState = Game.actor_state(c.id)
		# The way may lie any way round: the chevron sits on the frame's edge the way points.
		var way := way_toward(to_map.call(me.plane, 0.0), gp) if me != null else Vector2.RIGHT
		var tip := edge_point(inner.grow(-8.0), inner.get_center(), way)
		tip += way * sin(hud.t * 4.0) * 2.0
		var side := Vector2(-way.y, way.x)
		var chev := PackedVector2Array([tip, tip - way * 9.0 - side * 7.0, tip - way * 9.0 + side * 7.0])
		hud.draw_colored_polygon(chev, UiKit.GOLD)
		hud.draw_polyline(chev + PackedVector2Array([chev[0]]), UiKit.INK, 1.5)
	for o in room.get("objects", []):
		if not WorldShared.object_visible(c, o): continue
		var at2: Array = o.at
		var mp: Vector2 = to_map.call(Vector2(float(at2[0]), float(at2[1])), float(o.get("alt", 0)))
		if o.type == "npc":
			var mk: String = WorldShared.npc_marker(c, str(o.npc))
			hud.draw_circle(mp, 3, UiKit.GOLD if mk in ["main", "ready"] else (UiKit.BRIGHT_JADE if mk == "again" else UiKit.PALE_GOLD))
			if QuestAuthority.marker_calls(mk): hud.draw_arc(mp, 6 + sin(hud.t * 4.0) * 1.5, 0, TAU, 12, UiKit.BRIGHT_JADE if mk == "again" else UiKit.GOLD, 1)
		elif o.type in ["shrine", "qi_spring", "teleport_stone"] and PlaceRules.at_object(Game.room_rt.room_id, str(o.id)).is_empty():   # a place draws its own glyph
			hud.draw_rect(Rect2(mp - Vector2(3, 3), Vector2(6, 6)), UiKit.BRIGHT_JADE)
		elif o.type == "treasure_birth":
			# S45: a Spirit Fruit ripening here stands up as a pillar of light on the minimap.
			var pa := 0.55 + 0.25 * sin(hud.t * 3.0)
			hud.draw_rect(Rect2(Vector2(mp.x - 3.0, inner.position.y + 2.0), Vector2(6.0, mp.y - inner.position.y - 2.0)), Color(UiKit.GOLD, pa * 0.35))
			hud.draw_line(Vector2(mp.x, inner.position.y + 2.0), mp, Color(UiKit.PALE_GOLD, pa), 1.5)
			hud.draw_circle(mp, 3.5, UiKit.GOLD)
		elif o.type == "spirit_mine":
			# S49 territory: a mine shows in its holder's colour; yours glints jade.
			var mid := str(o.get("mine", ""))
			var mc := UiKit.BRIGHT_JADE if Game.sect.holds(mid) else Color(str(Game.sect.rival(str(ContentDB.entry("territory", mid).get("sect", ""))).get("color", UiKit.MIST.to_html(false)))).lightened(0.3)
			hud.draw_colored_polygon(PackedVector2Array([mp + Vector2(0, -4), mp + Vector2(4, 0), mp + Vector2(0, 4), mp + Vector2(-4, 0)]), mc)
		elif o.type == "herb_patch" and o.has("ripen"):
			# S45: a rare herb shows as a leaf, gold while ripe, with the time left (or until it ripens).
			var hs: Dictionary = Game.world.herb_state(o)
			var spent: bool = Game.room_rt.objects.get(str(o.id), {}).get("state", "ready") == "depleted"
			var ripe: bool = hs.ripe and not hs.dormant and not spent
			var lc := UiKit.GOLD if ripe else Color(UiKit.HOLLOW, 0.9)
			hud.draw_colored_polygon(PackedVector2Array([mp + Vector2(0, -5), mp + Vector2(3.5, 0), mp + Vector2(0, 4), mp + Vector2(-3.5, 0)]), lc)
			if ripe: hud.draw_arc(mp, 6.5 + sin(hud.t * 5.0), 0, TAU, 12, UiKit.GOLD, 1)
			if not hs.dormant and not spent:
				UiKit.draw_text(hud, UiKit.span(float(hs.seconds)), mp + Vector2(-30, 14), 14, lc, HORIZONTAL_ALIGNMENT_CENTER, 60)
	# Decision 43: the room's places, each a small glyph of its kind (TopdownPlaceArt's things, read at a glance); one
	# that has something waiting (a new notice, a letter, a ripe bed, a finished batch) wears a gold spark. A tap near
	# one opens the world map's Places on it, whose card offers the walk there.
	# The marks are worked out twice a second, or as the room changes (the room's map stays put in between).
	hud._place_look -= hud.get_process_delta_time()
	var mark_room := str(Game.room_rt.room_id)
	if hud._place_look <= 0.0 or mark_room != hud._place_room:
		hud.minimap_places = place_marks(c, mark_room, to_map, inner.position.y + 6.0)
		hud._place_room = mark_room
		hud._place_look = 0.5
	for mk in hud.minimap_places: TopdownPlaceArt.glyph(hud, (mk.at as Vector2).round(), str(mk.kind), bool(mk.wait), hud.t)
	if Game.room_rt and Game.account.settings.get("minimap_monsters", true):
		for e in Game.room_rt.enemies.values():
			if not e.alive or e.hidden: continue
			var ep: Vector2 = to_map.call(e.plane, e.altitude)
			var col = UiKit.SKY if e.team == "ally" else (UiKit.GOLD if e.elite or e.is_boss() else UiKit.RED)
			hud.draw_circle(ep, 2.5, col)
	var pp: Vector2 = to_map.call(hud.player.plane, hud.player.altitude)
	# The arrow points the way the body faces, any of eight ways.
	var fv := (hud.player.motor.dir as Vector2).normalized() if hud.player.get("motor") != null else Vector2(hud.player.facing, 0)
	var fs := Vector2(-fv.y, fv.x)
	hud.draw_colored_polygon(PackedVector2Array([pp + fv * 5.0, pp - fv * 3.0 - fs * 4.0, pp - fv * 3.0 + fs * 4.0]), Color.WHITE)

## The room's places on the minimap (decision 43): [{id, kind, at (the map's px, by `to_map`), wait}], each place the
## character sees (PlaceRules.visible); two a few cells apart would overlap on the small map, so the later one steps
## above (not over `top`) or below. `wait`: something waits there (a new notice, a letter, a ripe bed, a ready batch).
func place_marks(c, room_id: String, to_map: Callable, top := -INF) -> Array:
	var out: Array = []
	for pl in PlaceRules.of_room(room_id):
		if not PlaceRules.visible(c, pl): continue
		var at: Vector2 = to_map.call(PlaceRules.point(pl), 0.0)
		for k in 2:
			for other in out:
				if at.distance_to(other.at) < 15.0: at.y += -14.0 if at.y >= float(other.at.y) and at.y - 14.0 > top else 14.0
		if hud._place_look <= 0.0 or not hud._place_states.has(str(pl.id)): hud._place_states[str(pl.id)] = PlaceRules.state(c, pl)
		var ps: Dictionary = hud._place_states[str(pl.id)]
		var wait := int(ps.get("new", 0)) > 0 or (str(ps.state) in ["ribbon", "growth"] and bool(ps.get("on", false)))
		out.append({"id": str(pl.id), "kind": str(pl.kind), "at": at, "wait": wait})
	return out

## What a tap on the minimap opens the world map on: the Places view on the place nearest the tap (within 16 px of its
## glyph), else the map as it opens.
func place_at(p: Vector2) -> Dictionary:
	var best := {}
	var best_d := 16.0
	for mp in hud.minimap_places:
		var d := p.distance_to(mp.at)
		if d < best_d:
			best_d = d
			best = {"view": "places", "place": str(mp.id)}
	return best

## Redesign Phase 4: the direction mark's way on a grid room's map, from the player's dot to the goal (east when on it).
static func way_toward(from: Vector2, to: Vector2) -> Vector2:
	return (to - from).normalized() if from.distance_to(to) > 0.5 else Vector2.RIGHT

## Where a ray from `center` along `way` leaves `r` (the direction mark's place on the map's frame).
static func edge_point(r: Rect2, center: Vector2, way: Vector2) -> Vector2:
	var k := INF
	if absf(way.x) > 0.001: k = minf(k, ((r.end.x if way.x > 0.0 else r.position.x) - center.x) / way.x)
	if absf(way.y) > 0.001: k = minf(k, ((r.end.y if way.y > 0.0 else r.position.y) - center.y) / way.y)
	return center + way * (k if k < INF else 0.0)

## A room on the height grid as a map, one pixel a cell, made once a room (drawn scaled, nearest): water, the floor by
## its level (higher is paler), and walls and the props' footprints dark.
func _grid_map(grid: TopdownRoom) -> Texture2D:
	if hud._grid_maps.has(grid.id): return hud._grid_maps[grid.id]
	var img := Image.create(grid.w, grid.h, false, Image.FORMAT_RGBA8)
	for y in grid.h:
		for x in grid.w:
			var l := grid.level(x, y)
			var col := Color(UiKit.SURFACE.map_line, 0.10)
			if l == TopdownRoom.WATER: col = Color(UiKit.SKY, 0.45)
			elif l == TopdownRoom.SOLID: col = Color(UiKit.INK, 0.55)
			elif not grid.stair_at(x, y).is_empty(): col = Color(UiKit.SURFACE.map_line, 0.45)
			else: col = Color(UiKit.SURFACE.map_line, clampf(0.16 + 0.12 * l, 0.16, 0.7))
			img.set_pixel(x, y, col)
	hud._grid_maps = {grid.id: ImageTexture.create_from_image(img)}
	return hud._grid_maps[grid.id]
