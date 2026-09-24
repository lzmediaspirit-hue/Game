extends SceneTree
func _initialize(): call_deferred("run")
func run():
	var viewport=SubViewport.new()
	viewport.size=Vector2i(1728,960)
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var background=ColorRect.new()
	background.size=Vector2(1728,960)
	background.color=Color("263c42")
	viewport.add_child(background)
	var catalog=root.get_node("Wardrobe")
	var weapons=["sword","spear","dagger","staff","none","bow"]
	for row in weapons.size():
		var label=Label.new()
		label.text=weapons[row]+"   |   SWING                                      THRUST                                      PUNCH"
		label.position=Vector2(8,row*160)
		viewport.add_child(label)
		var column=0
		for action in ["swing","attack","punch"]:
			for facing in [1,-1]:
				for frame in [0,int(catalog.parts._actions[action].frames)/2,int(catalog.parts._actions[action].frames)-1]:
					var avatar=load("res://scripts/avatar.gd").new()
					avatar.outfit=catalog.defaults()
					avatar.outfit.weapon=weapons[row]
					avatar.action=action
					avatar.facing=facing
					avatar.elapsed=(frame+0.01)/float(catalog.parts._actions[action].fps)
					avatar.externally_timed=true
					avatar.position=Vector2(column*96+48,row*160+140)
					viewport.add_child(avatar)
					column+=1
	await process_frame
	await RenderingServer.frame_post_draw
	viewport.get_texture().get_image().save_png("res://../previews/v10-combo-equipment.png")
	viewport.queue_free()
	await verify_outlines(catalog)
	# Actual touch input: keep joystick UP throughout the entire jump and landing.
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	var main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(catalog.defaults())
	main.change_region("forest",7,1)
	var w=main.world
	w.set_process(false)
	var p=w.player
	p.set_physics_process(false)
	var target=w.by_id("tree_00_branch_0")
	p.surface=w.by_id("river_walk")
	p.plane=target.bounds.get_center()+Vector2(0,50)
	p.altitude=0
	main.hud.press(1,Vector2(200,530))
	main.hud.drag(1,Vector2(200,454))
	main.hud.press(2,main.hud.jump_center)
	main.hud.release(2)
	for frame in 180: p.step(1.0/60,p.movement)
	assert(p.surface==target and p.movement.y< -0.9,"Holding joystick up must land and remain on the branch")
	p.sync_visual()
	w.camera.position=w.camera_target()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v10-upward-touch-landing.png")
	print("COMBO_VISUAL: equipment gallery and held-UP touch landing captured")
	quit()
func verify_outlines(catalog):
	var viewport=SubViewport.new()
	viewport.size=Vector2i(512,512)
	viewport.transparent_bg=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var avatar=load("res://scripts/avatar.gd").new()
	avatar.outfit=catalog.defaults()
	avatar.position=Vector2(256,300)
	avatar.externally_timed=true
	viewport.add_child(avatar)
	var source=load("res://scripts/player.gd").new()
	source.avatar=avatar
	var outline=load("res://scripts/occlusion_outline.gd").new()
	outline.source=source
	var count=0
	for weapon in ["sword","spear","dagger","staff","bow","none"]:
		avatar.outfit.weapon=weapon
		for action in ComboRig.RECIPES:
			avatar.action=action
			avatar.elapsed=(int(catalog.parts._actions[action].frames)/2+0.01)/float(catalog.parts._actions[action].fps)
			for facing in [-1,1]:
				avatar.facing=facing
				outline.sync()
				await process_frame
				await RenderingServer.frame_post_draw
				var rendered=viewport.get_texture().get_image()
				var mask=outline.pose.get_image()
				var bounds=rendered.get_used_rect().merge(mask.get_used_rect())
				var matches=true
				for y in range(bounds.position.y,bounds.end.y,2):
					for x in range(bounds.position.x,bounds.end.x,2):
						if absf(rendered.get_pixel(x,y).a-mask.get_pixel(x,y).a)>0.02: matches=false
				assert(matches,"Outline must match the rendered equipment/body pose: "+weapon+" "+action)
				count+=1
	print("COMBO_OUTLINES: ",count," composited masks match rendered sprites")
	source.free()
	outline.free()
	viewport.queue_free()
