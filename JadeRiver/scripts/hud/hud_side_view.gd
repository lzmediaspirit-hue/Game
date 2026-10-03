class_name HudSideView
extends HudPart
## The side view's own answers on the HUD (decision 41's fallback, frozen: audit 45 §2.4). Each is called from one
## branch marked "side view" in another part, so retiring the side view deletes this file and those branches
## (docs/architecture/hud.md lists them all):
##   - HudInput.dodge: a side-view body has no dash of its own; the combat authority's dodge, along its facing;
##   - HudActions.use_context: a ladder or a rope in reach (a "climbable" context, which only world.gd offers);
##   - HudPanels._draw_face: a classic side-view character's companions, cut from their avatar's idle frame;
##   - HudMinimap.draw: a room with no height grid, projected from its surfaces (x along the room, y the plane's y less
##     the altitude), and its surfaces, blocks, movers and ladders.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## A tap of Dodge for a body with no dash of its own (the side view's player): the combat authority's dodge.
func dodge() -> void:
	Game.submit({"type": "dodge", "direction": hud.player.last_axis, "facing": hud.player.facing})

## The context's button on a ladder or a rope in reach: the climb, unless the way up is shut (it says why).
func climb() -> void:
	hud.player.climb_hold = 0.0
	var near_c: Dictionary = hud.player.world.geometry.climbable_near(hud.player.plane, hud.player.altitude, 48.0)
	var open: Dictionary = Game.world.climbable_open(Game.active(), near_c) if not near_c.is_empty() else {"ok": true}
	if not open.get("ok", false):
		hud.add_log(str(open.get("text", "")), UiKit.MIST)
		return
	hud.player.authority.climb(near_c)

## A companion's face for a side-view character: the head and shoulders of their avatar's idle frame (FACE_AT, FACE_BOX),
## its layers kept once made.
func draw_face(center: Vector2, cid: String, dim := false) -> void:
	var box := Vector2(Hud.FACE_BOX, Hud.FACE_BOX)
	if not hud._faces.has(cid):
		var av = Figures.side_avatar(hud.panels.face_outfit(cid))
		av.refresh_entries()
		hud._faces[cid] = av.entries.duplicate()
		av.free()
	for en in hud._faces[cid]:
		var cell := int(en.cell)
		var off := (cell - 256) * 0.5
		var src := Rect2(Vector2(128.0 + off, cell + 190.0 + off) + Hud.FACE_AT - box * 0.5, box)
		hud.draw_texture_rect_region(en.texture, Rect2(center - box * 0.5, box), src, Color(1, 1, 1, 0.45 if dim else 1.0))

## The minimap's projection of a room with no height grid: x along the room, y = plane y - altitude, fitted to the
## room's real extent (highest roof line down to the front of the ground strip).
func minimap_projection(inner: Rect2, room: Dictionary) -> Callable:
	var b: Array = room.get("bounds", [0, 480, 1280, 480])
	var bw := float(b[2])
	var sx := inner.size.x / bw
	var top := 600.0
	var bottom := 700.0
	if Game.room_rt:
		for s0 in Game.room_rt.geometry.surfaces:
			top = minf(top, s0.bounds.position.y - s0.base - 20.0)
			bottom = maxf(bottom, s0.bounds.end.y)
	var sy := inner.size.y / maxf(1.0, bottom - top)
	return func(pos: Vector2, alt: float) -> Vector2:
		return inner.position + Vector2(pos.x * sx, (pos.y - alt - top) * sy)

## The room's surfaces on the minimap (S43): blocks as small squares, movers as dashed lines, the rest as lines.
func draw_minimap_surfaces(to_map: Callable) -> void:
	for s in Game.room_rt.geometry.surfaces if Game.room_rt else []:
		if s.disabled: continue
		var y0: Vector2 = to_map.call(Vector2(s.bounds.position.x, s.bounds.position.y), s.base)
		var y1: Vector2 = to_map.call(Vector2(s.bounds.end.x, s.bounds.position.y), s.base)
		if s.is_block:
			var mid := (y0 + y1) * 0.5
			hud.draw_rect(Rect2(mid - Vector2(2.5, 2.5), Vector2(5, 5)), Color(UiKit.SURFACE.map_line, 0.8))
		elif s.moving:
			hud.draw_dashed_line(y0, y1, Color(UiKit.PALE_GOLD, 0.9), 2.0, 3.0)
		else:
			hud.draw_line(y0, y1, Color(UiKit.SURFACE.map_line, 0.55 if s.stratum == "ground" else 0.8), 2)

## The room's ladders and ropes on the minimap (S43): a vertical line from foot to head. A room on the height grid has
## none (TopdownRoom.SIDE_ONLY).
func draw_minimap_ladders(to_map: Callable) -> void:
	for cb in Game.room_rt.geometry.climbables if Game.room_rt else []:
		var ca: Array = cb.at
		var foot: Vector2 = to_map.call(Vector2(float(ca[0]), float(ca[1])), float(cb.bottom_alt))
		var head: Vector2 = to_map.call(Vector2(float(ca[0]), float(ca[1])), float(cb.top_alt))
		hud.draw_line(foot, head, Color(UiKit.GOLD, 0.9), 1.5)
