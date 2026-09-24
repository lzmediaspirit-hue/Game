extends SceneTree
func _initialize(): call_deferred("run")
func run():
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	var main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(root.get_node("Wardrobe").defaults())
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
	assert(p.surface==target)
	main.hud.release(1)
	main.hud.press(3,Vector2(200,530))
	for pass_index in 3:
		var direction=1 if pass_index!=1 else -1
		main.hud.drag(3,Vector2(200+76*direction,560))
		for frame in (12 if pass_index!=1 else 24):
			p.step(1.0/60,p.movement)
			assert(p.surface==target and target.contains(p.plane),"Joystick drift must not drop the player while walking on the branch")
	main.hud.release(3)
	p.step(1.0/60,Vector2.ZERO)
	p.sync_visual()
	w.camera.position=w.camera_target()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v11-platform-walk.png")
	print("PLATFORM_TOUCH: held-UP landing, sideways traversal, reversal and stop passed")
	quit()
