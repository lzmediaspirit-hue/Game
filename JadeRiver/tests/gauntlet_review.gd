extends SceneTree
## Review sheets for the gauntlets (AGENTS.md rule 1), rendered by the game's own Avatar and occlusion outline into
## docs/mockups/gauntlets/. Run from JadeRiver/ with a renderer (not --headless):
##   xvfb-run -a godot --rendering-driver opengl3 --path . -s res://tests/gauntlet_review.gd
## - pose_<action>.png: every frame of the action, both facings; per facing the bare hands (reference), then the
##   gauntlets over the long-sleeved robe, the sleeveless shirt and the wide-sleeved scholar robe, then the occlusion
##   outline of the gauntleted figure;
## - dyes.png: the gauntlets with every robe and trouser dye, in a frame of each base action, both facings;
## - items.png: every gauntlet item, the look it wears and its jab.
const OUT := "res://docs/mockups/gauntlets/"
const BG := Color("263c42")
const CW := 150
const CH := 215
var wardrobe
var avatar_script: Script


func _initialize(): call_deferred("run")


func outfit(shirt: String, weapon: String, dye := "none") -> Dictionary:
	var o: Dictionary = wardrobe.defaults()
	o.shirt = shirt
	o.weapon = weapon
	o.shirt_dye = dye
	o.pants_dye = dye
	return o


func figure(parent: Node, o: Dictionary, action: String, frame: int, facing: int, at: Vector2, outline := false) -> void:
	var avatar = avatar_script.new()
	avatar.outfit = o
	avatar.action = action
	avatar.facing = facing
	avatar.elapsed = (frame + 0.01) / float(wardrobe.parts._actions[action].fps)
	avatar.externally_timed = true
	avatar.position = at
	avatar.scale = Vector2.ONE * 2
	if not outline:
		parent.add_child(avatar)
		return
	# The outline the world draws when the figure is behind scenery, from the same composited layers.
	var holder := Node2D.new()
	var src := GDScript.new()
	src.source_code = "extends Node2D\nvar avatar\n"
	src.reload()
	holder.set_script(src)
	holder.avatar = avatar
	holder.position = at
	avatar.position = Vector2.ZERO
	avatar.visible = false
	holder.add_child(avatar)
	parent.add_child(holder)
	var ring := OcclusionOutline.new()
	ring.source = holder
	ring.scale = Vector2.ONE * 2
	parent.add_child(ring)
	ring.position = at
	ring.z_index = 0
	ring.sync()
	ring.position = at


func label(parent: Node, text: String, at: Vector2) -> void:
	var l := Label.new()
	l.text = text
	l.position = at
	l.add_theme_font_size_override("font_size", 14)
	parent.add_child(l)


func sheet(width: int, height: int) -> SubViewport:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(width, height)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	root.add_child(viewport)
	var background := ColorRect.new()
	background.size = Vector2(width, height)
	background.color = BG
	viewport.add_child(background)
	return viewport


func save(viewport: SubViewport, name: String) -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png(ProjectSettings.globalize_path(OUT + name))
	viewport.queue_free()
	await process_frame


func run():
	wardrobe = root.get_node("Wardrobe")
	avatar_script = load("res://scripts/avatar.gd")   # after the autoloads it names
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var rows := [["bare hands", "cardigan", "none"], ["gauntlets, long sleeves", "cardigan", "gauntlets"],
		["gauntlets, sleeveless", "sleeveless", "gauntlets"], ["gauntlets, wide sleeves", "scholar", "gauntlets"]]
	var made := 0
	for action in wardrobe.parts._actions:
		var frames := int(wardrobe.parts._actions[action].frames)
		var viewport := sheet(150 + frames * CW, (rows.size() + 1) * 2 * CH)
		var y := 0
		for facing in [1, -1]:
			for r in rows.size() + 1:
				var spec: Array = rows[mini(r, rows.size() - 1)]
				label(viewport, "%s\n%s\n%s" % [action, "facing right" if facing > 0 else "facing left", "occlusion outline" if r == rows.size() else spec[0]], Vector2(6, y + 80))
				for f in frames:
					figure(viewport, outfit(spec[1], spec[2]), action, f, facing, Vector2(150 + f * CW + CW / 2, y + 208), r == rows.size())
					if y == 0: label(viewport, str(f), Vector2(150 + f * CW + CW / 2 - 4, 2))
				y += CH
		await save(viewport, "pose_%s.png" % action)
		made += 1
	# Every dye of robe and trousers, with the gauntlets, in a frame of each base action and both facings.
	var shots := [["idle", 0], ["walk", 3], ["jump", 2], ["attack", 4], ["swing", 4], ["bow", 6], ["punch", 3], ["meditate", 0]]
	var dyes: Array = wardrobe.parts._dyes.order
	var viewport := sheet(150 + shots.size() * 2 * CW, dyes.size() * CH)
	for d in dyes.size():
		label(viewport, "dye: %s" % dyes[d], Vector2(6, d * CH + 60))
		for s in shots.size():
			for side in 2:
				figure(viewport, outfit("cardigan", "gauntlets", dyes[d]), shots[s][0], shots[s][1], 1 - side * 2, Vector2(150 + (s * 2 + side) * CW + CW / 2, d * CH + 208))
				if d == 0 and side == 0: label(viewport, "%s %d" % shots[s], Vector2(150 + s * 2 * CW + CW - 30, 2))
	await save(viewport, "dyes.png")
	# Every gauntlet item and the look it wears.
	var items: Array = root.get_node("ContentDB").all("artifacts").filter(func(a): return str(a.get("family", "")) == "gauntlets")
	viewport = sheet(items.size() * 190, 2 * CH + 70)
	for i in items.size():
		var look := str(items[i].appearance)
		label(viewport, "%s\n(%s)" % [items[i].name, look], Vector2(i * 190 + 6, 4))
		for side in 2:
			figure(viewport, outfit("cardigan", look), "punch", 3, 1 - side * 2, Vector2(i * 190 + 95, side * CH + 270))
	await save(viewport, "items.png")
	print("GAUNTLET_REVIEW: %d pose sheets, every dye, %d gauntlet items" % [made, items.size()])
	quit()
