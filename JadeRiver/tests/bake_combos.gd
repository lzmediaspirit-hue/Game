extends SceneTree
## Rebuild the established v0.12 clips only. New movements must first redraw and
## review the unclothed body, then matching equipment, as required by AGENTS.md.
func _initialize():
	var catalog=JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	var made=0
	for action in ComboRig.RECIPES:
		var recipe: Dictionary=ComboRig.RECIPES[action]
		catalog._actions[action]={"frames":8,"fps":14 if action.ends_with("_1") else (13 if action.ends_with("_2") else 11),"label":recipe.label,"loop":false}
		for category in ["body","hair","shirt","pants","shoes","weapon"]:
			if "--weapons-only" in OS.get_cmdline_user_args() and category!="weapon": continue
			for item_id in catalog[category]:
				for layer in catalog[category][item_id].get("layers",[]):
					var original: Dictionary=layer.animations[recipe.source]
					if original.get("hidden",false):
						layer.animations[action]=original.duplicate(true)
						continue
					var paths=[]
					for dye in original.sheets.size():
						var source=Image.load_from_file(ProjectSettings.globalize_path(str(original.sheets[dye]).replace("art_v12/","res://art/")))
						var sheet=ComboRig.bake(source,int(original.cell),recipe,category=="weapon")
						var path="art_v12/%s_%s_%s_%s_%s.png"%[category,item_id,layer.section,action,dye]
						assert(sheet.save_png(path.replace("art_v12/","res://art/"))==OK)
						paths.append(path)
						made+=1
					layer.animations[action]={"cell":original.cell,"sheets":paths,"z":original.get("z",layer.z),"source":original.sheets,"combo_rig":action}
	var file=FileAccess.open("res://data/parts.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(catalog,"  "))
	file.close()
	print("COMBO_BAKE: ",made," registered sheets for nine attacks")
	quit()
