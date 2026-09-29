extends Node
## The top-down character's compatibility gallery (AGENTS.md rule 3): every layer x action x facing x dye, drawn by the
## game's own compositor (TopdownFigure) over the starting outfit, one sheet per item and dye or hair colour: rows are
## the actions, column groups the eight facings (NW, W and SW mirrored), a red bar under each strike's hit frame.
## Numerical checks cannot certify alignment: look at the sheets. Needs a renderer:
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tests/topdown_figure_gallery.tscn -- [--out=DIR] [--only=cat|set]
## Sheets go to DIR (default user://topdown_gallery/), named <cat>_<item>__<variant>.png.

const CELL := Vector2i(68, 76)   # decision 43: the 46 px figure (review_character.py's cell)
const FEET := Vector2(34, 62)
const ROWS := ["s", "se", "e", "ne", "n", "nw", "w", "sw"]
const LABEL_W := 96

var out_dir := "user://topdown_gallery/"
var only := ""

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="): out_dir = a.substr(6).trim_suffix("/") + "/"
		if a.begins_with("--only="): only = a.substr(7)
	call_deferred("_main")

func starting() -> Dictionary:
	return {"body": "light", "hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose", "shoes": "slippers",
		"weapon": "none", "hat": "none", "cape": "none"}

func _main() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir) if out_dir.begins_with("user://") or out_dir.begins_with("res://") else out_dir)
	var man := TopdownFigure.manifest()
	var made := 0
	for cat in man.items:
		for name in man.items[cat]:
			if only != "" and cat != only and str(man.items[cat][name].get("set", "")) != only: continue
			for variant in man.items[cat][name].sheets:
				var o := starting()
				if cat == "body": o = {"body": "light"}
				else: o[cat] = name
				if cat == "hair": o.hair_color = int(variant)
				elif cat in ["shirt", "pants"]: o[cat + "_dye"] = variant
				await _sheet(TopdownFigure.wearing(o), man, "%s_%s__%s" % [cat, name, variant])
				made += 1
	print("topdown_figure_gallery: %d sheets in %s" % [made, ProjectSettings.globalize_path(out_dir) if out_dir.begins_with("user://") else out_dir])
	get_tree().quit()

func _sheet(fig: TopdownFigure, man: Dictionary, file: String) -> void:
	var order: Array = man.action_order
	var per := 0
	for a in order: per = maxi(per, int(man.actions[a].frames))
	var size := Vector2i(LABEL_W + ROWS.size() * (per * CELL.x + 8), 18 + order.size() * CELL.y)
	var vp := SubViewport.new()
	vp.size = size
	vp.transparent_bg = false
	vp.render_target_update_mode = SubViewport.UPDATE_ONCE
	vp.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(vp)
	var board := Board.new()
	board.fig = fig
	board.man = man
	board.per = per
	board.size = size
	vp.add_child(board)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := vp.get_texture().get_image()
	img.save_png(out_dir.path_join(file + ".png"))
	vp.queue_free()

class Board extends Node2D:
	var fig: TopdownFigure
	var man: Dictionary
	var per := 0
	var size := Vector2i.ZERO
	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), Color("161e22"))
		var font := ThemeDB.fallback_font
		for c in ROWS.size():
			draw_string(font, Vector2(LABEL_W + c * (per * CELL.x + 8), 13), ROWS[c].to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("afc9d1"))
		var y := 18
		for a in man.action_order:
			var spec: Dictionary = man.actions[a]
			draw_string(font, Vector2(4, y + 20), str(a), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color("e8e1cf"))
			for c in ROWS.size():
				var x0: int = LABEL_W + c * (per * CELL.x + 8)
				for i in int(spec.frames):
					var at := Vector2(x0 + i * CELL.x, y)
					draw_rect(Rect2(at, CELL), Color("485c54"))
					fig.draw(self, at + FEET, a, ROWS[c], i)
					if int(spec.hit) == i: draw_rect(Rect2(at + Vector2(0, CELL.y - 2), Vector2(CELL.x, 2)), Color("e55858"))
			y += CELL.y
