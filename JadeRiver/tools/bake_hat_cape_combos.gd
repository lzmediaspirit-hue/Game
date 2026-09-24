extends SceneTree
## Bake the nine combo clips for hat and cape layers with the same ComboRig
## recipes used for body, hair and garments, so NPCs and equipment in the Hat and
## Cape slots render in every registered action (AGENTS.md rule 1).
## Run: godot --headless --path . --script res://tools/bake_hat_cape_combos.gd
func _initialize():
	var catalog = JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	var made := 0
	for action in ComboRig.RECIPES:
		var recipe: Dictionary = ComboRig.RECIPES[action]
		for category in ["hat", "cape"]:
			for item_id in catalog[category]:
				for layer in catalog[category][item_id].get("layers", []):
					if layer.animations.has(action) and layer.animations[action].has("combo_rig"): continue
					var original: Dictionary = layer.animations[recipe.source]
					if original.get("hidden", false):
						layer.animations[action] = original.duplicate(true)
						continue
					var paths := []
					for dye in original.sheets.size():
						var source := Image.load_from_file(ProjectSettings.globalize_path(str(original.sheets[dye]).replace("art_v12/", "res://art/")))
						var sheet := ComboRig.bake(source, int(original.cell), recipe, false)
						var path := "art_v12/%s_%s_%s_%s_%s.png" % [category, item_id, layer.section, action, dye]
						assert(sheet.save_png(ProjectSettings.globalize_path(path.replace("art_v12/", "res://art/"))) == OK)
						paths.append(path)
						made += 1
					layer.animations[action] = {"cell": original.cell, "sheets": paths, "z": original.get("z", layer.z), "source": original.sheets, "combo_rig": action}
	var file := FileAccess.open("res://data/parts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(catalog, "  "))
	file.close()
	print("HAT_CAPE_COMBOS: ", made, " sheets")
	quit()
