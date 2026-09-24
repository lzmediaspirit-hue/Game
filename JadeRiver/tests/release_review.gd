extends SceneTree
func _initialize(): call_deferred("run")
func capture(name: String):
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v13-"+name+".png")
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
	var lane=target.nearest_supported(target.bounds.get_center())
	p.surface=w.by_id("river_walk")
	p.altitude=0
	p.plane=Vector2(lane.x,maxf(484,lane.y-target.base+45))
	main.hud.press(1,Vector2(200,530))
	main.hud.drag(1,Vector2(200,454))
	main.hud.press(2,main.hud.jump_center)
	main.hud.release(2)
	for frame in 120: p.step(1.0/60,p.movement)
	assert(p.surface==target,"Visual branch approach must land while holding UP")
	w.update_occlusion()
	w.camera.position=w.camera_target()
	await capture("branch-landing")
	main.hud.release(1)
	p.surface=w.by_id("river_walk")
	p.altitude=0
	p.vertical_speed=0
	p.plane=Vector2(5250,866)
	p.step(1.0/60,Vector2.ZERO)
	w.update_occlusion()
	w.camera.position=Vector2(5140,650)
	await capture("east-gate")
	print("RELEASE_VISUAL: held-UP visible-branch landing and gate depth captured")
	quit()
