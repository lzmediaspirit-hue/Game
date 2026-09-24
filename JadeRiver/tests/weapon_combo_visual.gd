extends SceneTree
func _initialize(): call_deferred("run")
func run():
	var catalog=root.get_node("Wardrobe")
	var weapons=["sword","spear","dagger","staff","none","bow"]
	var avatar_script=load("res://scripts/avatar.gd")
	for look in 6:
		var viewport=SubViewport.new()
		viewport.size=Vector2i(1536,1440)
		viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var background=ColorRect.new()
		background.size=Vector2(1536,1440)
		background.color=Color("263c42")
		viewport.add_child(background)
		var row=0
		for action in ComboRig.RECIPES:
			var label=Label.new()
			label.text=weapons[look]+" / "+action+" / "+ComboRig.RECIPES[action].label+"    windup → contact → follow-through → recovery     |     both facings"
			label.position=Vector2(8,row*160)
			viewport.add_child(label)
			var column=0
			for facing in [1,-1]:
				for frame in [1,3,5,7]:
					var avatar=avatar_script.new()
					avatar.outfit=catalog.defaults()
					for category in ["hair","shirt","pants","shoes"]:
						var items=catalog.parts[category].keys()
						avatar.outfit[category]=items[look%items.size()]
					avatar.outfit.hair_color=look
					avatar.outfit.weapon=weapons[look]
					avatar.action=action
					avatar.facing=facing
					avatar.elapsed=(frame+0.01)/float(catalog.parts._actions[action].fps)
					avatar.externally_timed=true
					avatar.position=Vector2(column*192+96,row*160+150)
					avatar.scale=Vector2.ONE
					viewport.add_child(avatar)
					column+=1
			row+=1
		await process_frame
		await RenderingServer.frame_post_draw
		viewport.get_texture().get_image().save_png("res://../previews/v12-combos-%s.png"%weapons[look])
		viewport.queue_free()
		await process_frame
		catalog.textures.clear()
	print("WEAPON_COMBO_VISUAL: six equipment/dye galleries, all nine actions and both facings")
	quit()
