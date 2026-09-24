extends SceneTree
func _initialize():
	var catalog=JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	var made=0
	for category in ["body","hair","shirt","pants","shoes","weapon"]:
		for item_id in catalog[category]:
			for layer in catalog[category][item_id].get("layers",[]):
				for action in catalog._actions:
					if layer.animations.has(action) and not layer.animations[action].has("rig"): continue
					if category!="weapon" or not layer.animations.has("idle") or not layer.animations.idle.has("sheets"):
						layer.animations[action]={"hidden":true,"reason":"Conditional layer is absent in this pose"}
						continue
					var idle=layer.animations.idle
					var source=Image.load_from_file(str(idle.sheets[0]).replace("art_v12/","res://art/"))
					var cell=int(idle.cell)
					if source.get_region(Rect2i(0,cell,cell,cell)).is_invisible():
						layer.animations[action]={"hidden":true,"reason":"Empty split weapon layer; companion layer provides the pose"}
						continue
					var poses=EquipmentRig.track(action,int(catalog._actions[action].frames))
					var image=EquipmentRig.render_sheet(source,cell,EquipmentRig.GRIPS[item_id],poses)
					var path="art_v12/weapon_%s_%s_%s_combo.png"%[item_id,layer.section,action]
					var error=image.save_png(path.replace("art_v12/","res://art/"))
					assert(error==OK)
					layer.animations[action]={"sheets":[path],"cell":384,"z":8 if action in ["punch","bow"] else 150,
						"source":idle.sheets[0],"rig":{"grip":EquipmentRig.GRIPS[item_id],"track":poses},"fallback":null}
					made+=1
	var file=FileAccess.open("res://data/parts.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(catalog,"  "))
	file.close()
	print("EQUIPMENT_POSES: ",made," matching sheets; all conditional omissions explicit")
	quit()
