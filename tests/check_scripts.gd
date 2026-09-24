# Loads every script so parse errors surface: godot --headless --path . --script tests/check_scripts.gd
extends SceneTree

func _init() -> void:
	var bad := 0
	for dir in ["res://scripts/core", "res://scripts/art", "res://scripts/world", "res://scripts/ui", "res://scripts"]:
		var da := DirAccess.open(dir)
		if da == null:
			continue
		for f in da.get_files():
			if f.ends_with(".gd"):
				var s = load(dir + "/" + f)
				if s == null or not s.can_instantiate():
					bad += 1
					print("BAD ", dir, "/", f)
	print("checked, bad=", bad)
	quit(1 if bad else 0)
