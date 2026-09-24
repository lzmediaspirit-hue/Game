extends Node2D
## Pose-registered rendering: all garments share the APK's floor and direction rows.
var outfit: Dictionary = {}
var action = "idle"
var facing = 1
var hide_bow_arrow = false
var elapsed = 0.0
var playback_speed = 1.0
var externally_timed=false
var only_category = ""
var entries: Array = []
var last_key = ""
var thumbnail_size = Vector2.ZERO
var thumbnail_bounds = Rect2()
func _ready():
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if outfit.is_empty(): outfit = Wardrobe.defaults()
func equip(category: String, item: String):
	if category in Wardrobe.CATEGORIES and Wardrobe.parts[category].has(item):
		outfit[category] = item
		last_key = ""
func play(next: String):
	if action != next:
		action = next
		elapsed = 0
func _process(delta):
	if not externally_timed: elapsed += delta * playback_speed
	queue_redraw()
func refresh_entries():
	if outfit.is_empty(): return
	var key = str(outfit) + action + only_category
	if key != last_key:
		entries.clear()
		for category in ["body", "cape", "shoes", "pants", "shirt", "hair", "hat", "weapon"]:
			if only_category != "" and category != only_category: continue
			var item = Wardrobe.parts[category].get(outfit.get(category, "none"), {})
			for layer in item.get("layers", []):
				assert(layer.animations.has(action),"Missing equipment pose: "+category+" / "+action)
				var anim = layer.animations.get(action,{})
				if anim.is_empty() or anim.get("hidden",false): continue
				entries.append({"texture": Wardrobe.texture(anim.sheets[mini(int(outfit.get("hair_color",0)),anim.sheets.size()-1)] if category=="hair" else anim.sheets[0]), "cell":int(anim.get("cell",256)), "z":int(anim.get("z",layer.z)), "held_arrow":category=="weapon" and str(anim.get("source","")).contains("/arrow/")})
		entries.sort_custom(func(a,b): return a.z < b.z)
		last_key = key
		if thumbnail_size != Vector2.ZERO:
			thumbnail_bounds=Rect2()
			for entry in entries:
				var cell: int=entry.cell
				var region=entry.texture.get_image().get_region(Rect2i(0,cell,cell,cell)).get_used_rect()
				if region.size==Vector2i.ZERO: continue
				var offset=(cell-256)*0.5
				var occupied=Rect2(Vector2(region.position)+Vector2(-128-offset,-190-offset),Vector2(region.size))
				thumbnail_bounds=occupied if thumbnail_bounds.size==Vector2.ZERO else thumbnail_bounds.merge(occupied)
func pose_frame() -> int:
	var spec = Wardrobe.parts._actions.get(action, Wardrobe.parts._actions.idle)
	var index=int(elapsed*spec.fps)
	return mini(index,int(spec.frames)-1) if not spec.get("loop",action not in ["jump","swing","attack","punch","bow"]) else index%int(spec.frames)
func _draw():
	refresh_entries()
	var frame=pose_frame()
	if thumbnail_size != Vector2.ZERO and thumbnail_bounds.size != Vector2.ZERO:
		frame=0
		var fit=minf(thumbnail_size.x/thumbnail_bounds.size.x,thumbnail_size.y/thumbnail_bounds.size.y)
		draw_set_transform(-thumbnail_bounds.get_center()*fit,0,Vector2.ONE*fit)
	var bob = -8 + sin(elapsed * TAU / 2.8) * 3 if action == "meditate" else 0.0
	for entry in entries:
		if hide_bow_arrow and action=="bow" and entry.held_arrow: continue
		var cell: int = entry.cell
		var tex: Texture2D = entry.texture
		var frames = maxi(1, int(tex.get_width() / cell))
		var row = 0 if facing < 0 else 1
		var source = Rect2((frame % frames) * cell, row * cell, cell, cell)
		var offset = (cell - 256) * 0.5
		draw_texture_rect_region(tex, Rect2(-128 - offset, -190 - offset + bob, cell, cell), source)
