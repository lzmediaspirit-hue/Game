class_name TopdownPlaces
extends RefCounted
## Redesign Phase 4: the people, things and ways of a room of the world on the height grid, for TopdownWorld. Each is
## drawn twice, as the side view's own views split in two:
##   - in the pixel viewport, sorted with the room (Figure), its feet on the floor it stands on: a villager drawn in the
##     top-down style (Person: TopdownFigure, decision 32, in their own outfit), or the thing's prop (an ObjectView in
##     "art" mode), the side view's art at half size (2 world units per art px, one art px per viewport px);
##   - on the overlay at the HUD's resolution (world units, following the camera): the side view's NpcView, ObjectView
##     and PortalView in their label modes, so markers, barks, verb plates, a pickup's badge and a way's plate read
##     crisp, placed by WorldLabels as in the side view.
## The label views are the ones the shared room presentation works on (WorldShared: focus, flashes, names), and each
## figure follows its label twin. A way out draws as a mark on the floor (WayMark) where the layout sets it.

## Decision 43: a person on the grid is drawn 46 art px tall, 8 more than the 38 the label views' marks were set over, so
## the marker, the bark and a plate lifted over the head stand this much higher (world units: two an art px).
const HEAD_LIFT := -16.0

## One villager or thing in the sorted layer: a node at its sort key (TopdownRoom.sort_key) holding its drawing (a
## Person, or the side view's ObjectView at half size), drawn back to its screen row.
class Figure extends Node2D:
	var rects: Array = []   ## what it covers for the silhouette test: people and small things never hide the body
	var art: Node2D         ## a Person, or an ObjectView in "art" mode
	var twin: Node2D        ## its label view on the overlay (NpcView or ObjectView), or null for a stand-in
	var player: Node2D      ## the TopdownPlayer a villager turns to while the player is at them
	var room: TopdownRoom
	var def: Dictionary
	var feet := Vector2.ZERO
	var plane := Vector2.ZERO   ## where it stands on the ground plane (world units)
	var staged := false         ## a staged scene has the person (decision 39): it sets where they face and what they do
	## Decision 43: the person's work loop (TopdownWork, TopdownLife gives it), or null; an extra at work has no twin.
	var work: TopdownWork = null
	var _was_staged := false

	func _init(r: TopdownRoom, o: Dictionary, drawing: Node2D, label: Node2D, body: Node2D = null) -> void:
		room = r
		def = o
		art = drawing
		twin = label
		player = body
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		if not art is TopdownPlaces.Person: art.scale = Vector2(0.5, 0.5)
		add_child(art)
		var at: Array = o.get("at", [0, 0])
		place(Vector2(float(at[0]), float(at[1])), float(o.get("alt", 0.0)))

	## Stand at a ground point and height: x on whole art px, y at the sort key, the drawing on its screen row. A flat
	## thing on the ground (a ripple, a circle of runes, a grey patch) lies under the figures standing on it, over the
	## floor it lies on (TopdownRoom.decal_key: on a terrace too, not under the terrace's own row).
	func place(p: Vector2, z: float) -> void:
		plane = p
		feet = TopdownWorld.to_screen(p, z).round()
		var key := room.sort_key(p, z)
		var pa: Dictionary = SpriteCache.prop(ObjectView.prop_of(def)) if def.get("type", "") != "npc" else {}
		if bool(pa.get("decal", false)): key = room.decal_key(p, z)
		position = Vector2(feet.x, key)
		art.position = Vector2(0, feet.y - key)
		# A thing as tall as a body (a training dummy, a stump, a shrine) can hide one standing behind it: it counts for
		# the silhouette test, so the body shows through (the prototype's QA lost the player behind Guo's dummy).
		var fr: Array = pa.get("frame", [0, 0])
		var an: Array = pa.get("anchor", fr)
		rects = [Rect2(feet - Vector2(float(an[0]), float(an[1])) * 0.5, Vector2(float(fr[0]), float(fr[1])) * 0.5)] if float(fr[1]) * 0.5 > 24.0 and not bool(pa.get("decal", false)) else []

	func _process(_d: float) -> void:
		if work != null and twin == null:
			_work(_d, false, false)   # decision 43: an extra at work, with no label and no talk
			return
		if not is_instance_valid(twin): return
		visible = twin.visible
		if staged:
			_was_staged = work != null
			return
		if twin is NpcView:
			# Decision 43: at work between the spots of their loop, stopping for the player; the label follows them.
			if work != null and not def.has("chase"):
				if _was_staged:
					_was_staged = false
					work.pos = plane
					work.paused = 0.0
					work._resume()
				_work(_d, twin.focus, QuestAuthority.marker_calls(str(twin.marker)))
				return
			var moving := false
			# A rooftop thief on the run is where his route puts him (the label view follows the World authority's clock),
			# walking the way he goes.
			if def.has("chase"):
				var ch: Dictionary = Game.world.chase_view(Game.active()) if Game.active() else {}
				if str(ch.get("object", "")) == str(def.id):
					var was := plane
					place(Vector2(float(ch.x), float(ch.y)), float(ch.alt))
					moving = bool(ch.get("moving", false))
					if moving: art.look(plane - was)
			# At the player's side (the context's focus: a talk, a gift, a shop), they turn to the player; else they
			# stand as the room has them.
			if twin.focus and is_instance_valid(player): art.look(player.plane - plane)
			elif not moving: art.row = art.rest
			art.play("walk" if moving else art.stand)
		elif twin is ObjectView:
			art.hit_flash = maxf(art.hit_flash, twin.hit_flash)
			art.focus = twin.focus

	## Decision 43: a step of the work loop: where they stand, face and what they do, what they hold; the label with them.
	func _work(delta: float, focus: bool, calls: bool) -> void:
		var t0 := Time.get_ticks_usec()
		var at: Vector2 = player.plane if is_instance_valid(player) and player.get("motor") != null else Vector2.INF
		work.advance(delta, at, focus, calls)
		if work.pos != plane: place(work.pos, work.alt)
		if is_instance_valid(twin): twin.position = Vector2(plane.x, plane.y - work.alt)
		if art is Person:
			art.row = work.facing()
			art.play(work.action)
			art.frame_override = work.frame()
			art.tool = work.tool
			art.tool_down = work.tool_down
			art.working = work.step_cue
		TopdownLife.spent_us += Time.get_ticks_usec() - t0
		TopdownLife.spent_parts.work += Time.get_ticks_usec() - t0

## A villager in the top-down style (decision 32): TopdownFigure in their own outfit (npcs.json), in one of the eight
## rows. At rest they stand in the pose the room gives them (idle, or meditate), three-quarters toward the camera on the
## side the side view faces them (or the row a layout names); they walk where a route moves them, and Figure turns them
## to the player at their side. A companion is one too (`outfit` in place of `npc`, redesign Phase 4), placed on its
## floor and shadowed there by the room's FoeView (`shadow` off).
class Person extends Node2D:
	const BLOB_RX := 8.0    ## its blob's half width (art px): 7 for the 38 px figure, 1.2 times that (decision 43)
	var figure: TopdownFigure
	var shadow := true      ## its own blob at its feet (a villager's); a companion's falls on the floor under it
	var rest := "sw"        ## the row they face at rest
	var row := "sw"
	var stand := "idle"     ## their pose at rest
	var action := "idle"
	var tint := Color.WHITE
	var t := 0.0
	## Decision 43: at work (TopdownWork): the frame the loop's clock gives (-1: the action's own), the tool in hand and
	## the one set down (TopdownLife draws them), and the step's cue (a broom swishes while sweeping).
	var frame_override := -1
	var tool := ""
	var tool_down := ""
	var working := ""

	func _init(o: Dictionary) -> void:
		var n := ContentDB.entry("npcs", str(o.get("npc", "")))
		figure = TopdownFigure.for_npc(str(o.get("npc", "")), true) if o.has("npc") else TopdownFigure.wearing(o.get("outfit", {}), true)
		rest = str(o.get("row", "se" if int(o.get("facing", n.get("facing", -1))) > 0 else "sw"))
		row = rest
		stand = TopdownFigure.resolve(str(o.get("pose", n.get("pose", "idle"))))
		action = stand
		if n.has("tint"): tint = Color(str(n.tint))
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		# Every sheet of the outfit is asked for as the room is populated (not one a frame from the first draw): they
		# stream in on loading threads within a few frames (main.gd warms the pages one at a time, PageWarmer).
		for l in figure.layers: Wardrobe.texture_async(str(l.path))

	## Turn toward a direction on the ground plane, one of the eight rows, as the player's motor turns.
	func look(dir: Vector2) -> void:
		if dir.length() > 0.5: row = TopdownMotor.nearest_row(dir, row, TopdownMotor.ROW_ANGLES, 10.0)

	func play(a: String) -> void:
		if a == action: return
		action = a
		t = 0.0

	func _process(delta: float) -> void:
		t += delta
		queue_redraw()

	func _draw() -> void:
		if shadow: TopdownWorld.draw_blob(self, 0.0, 0.0, BLOB_RX, 0.5)
		var f := frame_override if frame_override >= 0 else TopdownFigure.frame_at(action, t)
		# Decision 43: a tool set down lies beside them; one in hand is drawn behind the body facing away, else before it.
		if tool_down != "": TopdownLife.draw_tool_down(self, tool_down, row)
		if tool != "": TopdownLife.draw_tool(self, tool, row, figure, action, f, t, working, true)
		figure.draw(self, Vector2.ZERO, action, row, f, tint)
		if tool != "": TopdownLife.draw_tool(self, tool, row, figure, action, f, t, working, false)

## Redesign Phase 4: a companion's, a spirit animal's or a foe's drawing when the grid's foe sheet has no rows for it. A
## companion is a Person in its own outfit (the player's for a reflection); an animal or a foe is the side view's own
## figure at half size (EnemyView in its art mode: the creature sheet, its action, facing and flash). FoeView places it
## on its floor and draws its shadow there.
static func stand_in(e: EnemyState) -> Node2D:
	var art: Dictionary = e.def.get("art", {})
	# A person sparring with the player (QuestAuthority.start_spar) is that person, in their own clothes, while their
	# villager figure is hidden.
	if str(e.ai.get("partner", "")) != "":
		var own := Person.new({"npc": str(e.ai.partner), "facing": e.facing})
		own.shadow = false
		return own
	if art.has("avatar"):
		var outfit = art.avatar
		if outfit is String and outfit == "player": outfit = InventoryAuthority.outfit_for(Game.active()) if Game.active() else Wardrobe.defaults()
		var person := Person.new({"outfit": outfit, "facing": e.facing})
		person.shadow = false
		return person
	var v := EnemyView.new()
	v.art_only = true
	v.setup(e)
	v.scale = Vector2(0.5, 0.5)
	return v

## A stand-in's pose from its state, each frame (an EnemyView poses itself): a Person turns to where it walks or aims,
## one of the eight rows, and plays its action (a wind-up and its blow as its weapon family's first step, as that family
## plays it on the grid: the bow draws, the heavy sabre cuts two-handed).
static func pose(art: Node2D, e: EnemyState) -> void:
	if not art is Person: return
	art.look(e.velocity if e.velocity.length() > 1.0 else e.aim_dir())
	var fam := CombatFeel.family_of_look(str(art.figure.outfit.get("weapon", "none")))
	var combo: Array = ContentDB.entry("weapon_families", fam).get("combo", [])
	var strike := TopdownFigure.resolve(str(combo[0].action) if not combo.is_empty() else "punch_1", fam)
	art.play(TopdownFigure.resolve(str({"walk": "walk", "windup": strike, "attack": strike, "hurt": "hurt", "death": "knockdown"}.get(str(e.action), "idle"))))

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
		var st: Dictionary = WorldShared.portal_state(c, def) if c else {"open": true}
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
static func build(room: TopdownRoom, def: Dictionary, sorted: Node2D, floor_layer: Node2D, overlay: Node2D, player: Node2D = null) -> Dictionary:
	var out := {"npc_views": {}, "object_views": {}, "portal_views": [], "figures": {}, "nodes": []}
	for o in def.get("objects", []):
		var kind := str(o.get("type", ""))
		if kind == "decor" or not o.has("at"): continue
		if kind == "npc":
			var made := person(room, o, sorted, overlay, player)
			out.npc_views[str(o.id)] = made[0]
			out.figures[str(o.id)] = made[1]
			out.nodes.append_array(made)
		else:
			var lv := ObjectView.new()
			lv.mode = "label"
			lv.setup(o)
			overlay.add_child(lv)
			var art: Node2D
			if o.has("place"):
				art = TopdownPlaceArt.object(o)   # decision 43: a thing the places table adds (a letter box, a mat), drawn by it
			else:
				art = ObjectView.new()
				art.mode = "art"
				art.setup(o)
				# The Figure sorts it with the room: the side view's depth (ObjectView.depth, 1500 and more) as its z drew
				# every thing over every body, a notice board over the head of one standing in front of it (decision 43's
				# review).
				art.z_index = 0
			var fig := Figure.new(room, o, art, lv)
			if o.has("place"):
				art.scale = Vector2.ONE
				if str(o.get("type", "")) == "meditation_mat":
					# A mat lies flat on the floor: under the bodies sitting on it or behind it.
					var k := room.decal_key(fig.plane, float(o.get("alt", 0.0)))
					fig.position.y = k
					art.position.y = fig.feet.y - k
			sorted.add_child(fig)
			out.object_views[str(o.id)] = lv
			out.figures[str(o.id)] = fig
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
		# Decision 41: a way past the prototype's gate is closed by a barrier standing in it (TopdownGate).
		if Game.active() != null and Game.world.prototype_gate(Game.active(), str(def.get("id", Game.room_rt.room_id if Game.room_rt else "")), str(p.get("to", ""))):
			for g in TopdownGate.make(room, p):
				sorted.add_child(g)
				out.nodes.append(g)
	# Decision 43: the room's places (data/places.json): the sights round them and what each shows.
	out.nodes.append_array(TopdownPlaceArt.build(room, str(def.get("id", "")), sorted, out.figures))
	return out

## One person: their label view on the overlay and their figure sorted with the room, following it: [NpcView, Figure]
## (a room's villager, or one a staged scene brings on).
static func person(room: TopdownRoom, o: Dictionary, sorted: Node2D, overlay: Node2D, player: Node2D = null) -> Array:
	var nv := NpcView.new()
	nv.label_only = true
	nv.head_lift = HEAD_LIFT
	nv.setup(o)
	overlay.add_child(nv)
	var fig := Figure.new(room, o, Person.new(o), nv, player)
	sorted.add_child(fig)
	return [nv, fig]
