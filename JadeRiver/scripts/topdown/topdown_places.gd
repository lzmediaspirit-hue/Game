class_name TopdownPlaces
extends RefCounted
## Redesign Phase 4: the people, things and ways of a room of the world on the height grid, for TopdownWorld. Each is
## drawn twice, as the side view's own views split in two:
##   - in the pixel viewport, sorted with the room (Figure): the villager's layered avatar, or the thing's prop (an
##     ObjectView in "art" mode), the side view's art at half size (2 world units per art px, one art px per viewport
##     px), its feet on the floor it stands on;
##   - on the overlay at the HUD's resolution (world units, following the camera): the side view's NpcView, ObjectView
##     and PortalView in their label modes, so markers, barks, verb plates, a pickup's badge and a way's plate read
##     crisp, placed by WorldLabels as in the side view.
## The label views are the ones the shared room presentation works on (WorldShared: focus, flashes, names), and each
## figure follows its label twin. A way out draws as a mark on the floor (WayMark) where the layout sets it.

## One villager or thing in the sorted layer: a node at its sort key (TopdownRoom.sort_key) holding the side view's
## drawing at half size, drawn back to its screen row.
class Figure extends Node2D:
	var rects: Array = []   ## what it covers for the silhouette test: people and small things never hide the body
	var art: Node2D         ## an Avatar, or an ObjectView in "art" mode
	var twin: Node2D        ## its label view on the overlay (NpcView or ObjectView)
	var room: TopdownRoom
	var def: Dictionary
	var feet := Vector2.ZERO

	func _init(r: TopdownRoom, o: Dictionary, drawing: Node2D, label: Node2D) -> void:
		room = r
		def = o
		art = drawing
		twin = label
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		art.scale = Vector2(0.5, 0.5)
		add_child(art)
		var at: Array = o.get("at", [0, 0])
		place(Vector2(float(at[0]), float(at[1])), float(o.get("alt", 0.0)))

	## Stand at a ground point and height: x on whole art px, y at the sort key, the drawing on its screen row. A flat
	## thing on the ground (a ripple, a circle of runes, a grey patch) lies under the figures standing on it.
	func place(p: Vector2, z: float) -> void:
		feet = TopdownWorld.to_screen(p, z).round()
		var key := room.sort_key(p, z)
		if def.get("type", "") != "npc" and bool(SpriteCache.prop(ObjectView.prop_of(def)).get("decal", false)): key -= 12.0
		position = Vector2(feet.x, key)
		art.position = Vector2(0, feet.y - key)

	func _process(_d: float) -> void:
		if not is_instance_valid(twin): return
		visible = twin.visible
		if twin is NpcView:
			art.facing = twin.avatar.facing
			if art.action != twin.avatar.action: art.play(twin.avatar.action)
			# A rooftop thief on the run is where his route puts him (the label view follows the World authority's clock).
			if def.has("chase"):
				var ch: Dictionary = Game.world.chase_view(Game.active()) if Game.active() else {}
				if str(ch.get("object", "")) == str(def.id): place(Vector2(float(ch.x), float(ch.y)), float(ch.alt))
		elif twin is ObjectView:
			art.hit_flash = maxf(art.hit_flash, twin.hit_flash)
			art.focus = twin.focus

## A way out on the floor where the layout sets it: jade marks walking out through an edge, a lit threshold before a
## door (a building's doorway or the gap in an interior's wall), grey and still when it is shut. The side view's
## PortalView, label only, names it on the overlay.
class WayMark extends Node2D:
	var def: Dictionary
	var at := Vector2.ZERO    ## the mark's centre in art px
	var dir := Vector2.DOWN
	var t := 0.0
	var open := true

	func _init(p: Dictionary) -> void:
		def = p
		var a: Array = p.get("at", [0, 0])
		var d: Array = p.get("dir", [0, 1])
		dir = Vector2(float(d[0]), float(d[1]))
		at = TopdownWorld.to_screen(Vector2(float(a[0]), float(a[1])), float(p.get("alt", 0.0))).round()
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

	func _process(delta: float) -> void:
		t += delta
		var c = Game.active()
		var st: Dictionary = Game.world.portal_state(c, def) if c else {"open": true}
		visible = not st.get("hidden", false)
		open = bool(st.get("open", true))
		queue_redraw()

	func _draw() -> void:
		var side := Vector2(-dir.y, dir.x)
		var col := Color(0.55, 0.93, 0.8, 0.85) if open else Color(0.55, 0.6, 0.62, 0.7)
		if str(def.get("type", "edge")) == "door":
			# The threshold: a warm lit strip two tiles wide across the doorway, brighter as it pulses.
			var glow := Color(1.0, 0.85, 0.5, 0.20 + 0.10 * sin(t * 3.0)) if open else Color(0.4, 0.45, 0.5, 0.25)
			for k in 3:
				var w := 12.0 - k * 3.0
				draw_rect(Rect2(at + side * -w + dir * (-6.0 + k * 2.0), Vector2(absf(side.x) * w * 2.0 + absf(dir.x) * 4.0, absf(side.y) * w * 2.0 + absf(dir.y) * 4.0)), glow)
			return
		# An edge: three chevrons stepping out through it (whole art px), dimmed and still while it is shut.
		var bob := roundf(2.0 * sin(t * 4.0)) if open else 0.0
		for k in 3:
			var c := at + dir * (k * 5.0 - 4.0 + bob)
			for s in range(-3, 4):
				var q := (c + side * s - dir * absf(s)).round()
				draw_rect(Rect2(q, Vector2(1, 1)), col)
				draw_rect(Rect2(q + dir, Vector2(1, 1)), Color(col, col.a * 0.5))

## Build the room's people, things and ways: figures into `sorted`, marks into `floor_layer`, label views onto
## `overlay`. Returns {npc_views, object_views, portal_views} (the label views by id, as the side view keeps them)
## and `nodes`: everything made, for the next room to clear.
static func build(room: TopdownRoom, def: Dictionary, sorted: Node2D, floor_layer: Node2D, overlay: Node2D) -> Dictionary:
	var out := {"npc_views": {}, "object_views": {}, "portal_views": [], "nodes": []}
	for o in def.get("objects", []):
		var kind := str(o.get("type", ""))
		if kind == "decor" or not o.has("at"): continue
		if kind == "npc":
			var nv := NpcView.new()
			nv.label_only = true
			nv.setup(o)
			overlay.add_child(nv)
			var fig := Figure.new(room, o, NpcView.figure(o), nv)
			sorted.add_child(fig)
			out.npc_views[str(o.id)] = nv
			out.nodes.append_array([nv, fig])
		else:
			var lv := ObjectView.new()
			lv.mode = "label"
			lv.setup(o)
			overlay.add_child(lv)
			var art := ObjectView.new()
			art.mode = "art"
			art.setup(o)
			var fig := Figure.new(room, o, art, lv)
			sorted.add_child(fig)
			out.object_views[str(o.id)] = lv
			out.nodes.append_array([lv, fig])
	for p in def.get("portals", []):
		var pv := PortalView.new()
		pv.label_only = true
		pv.setup(p, def)
		pv.position.y -= float(p.get("alt", 0.0))
		# A door's plate stands over the building's front (three tiles of wall and the eaves), an edge's over the way.
		if str(p.get("type", "")) == "door": pv.door_top = -150.0 if float((p.get("dir", [0, -1]) as Array)[1]) < 0.0 else -70.0
		overlay.add_child(pv)
		out.portal_views.append(pv)
		var mark := WayMark.new(p)
		floor_layer.add_child(mark)
		out.nodes.append_array([pv, mark])
	return out
