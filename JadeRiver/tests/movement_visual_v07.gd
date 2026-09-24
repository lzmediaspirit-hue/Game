extends SceneTree
var main
func _initialize(): call_deferred("run")
func shot(label: String):
	main.world.player.sync_visual()
	main.world.camera.position=main.world.camera_target()
	main.world.update_occlusion()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v07-"+label+".png")
func run():
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(root.get_node("Wardrobe").defaults())
	main.change_region("forest",7,1)
	var w=main.world
	w.set_process(false)
	var p=w.player
	p.set_physics_process(false)
	p.avatar.set_process(false)
	var target=w.by_id("tree_00_branch_0")
	p.plane=target.bounds.get_center()+Vector2(0,42)
	p.altitude=0
	p.surface=w.by_id("river_walk")
	main.hud.press(1,main.hud.jump_center)
	main.hud.release(1)
	for i in 24:
		p.step(1.0/120,(target.bounds.get_center()-p.plane).limit_length(205.0/120)/(205.0/120))
		p.avatar._process(1.0/120)
	await shot("first-jump")
	main.hud.press(1,main.hud.jump_center)
	main.hud.release(1)
	assert(p.state.jumps_used==2)
	await shot("second-takeoff")
	for i in 160:
		p.step(1.0/120,Vector2.ZERO)
		p.avatar._process(1.0/120)
	await shot("tree-landing")
	assert(p.surface and p.surface.id.begins_with("tree_00_branch_"))
	assert(p.avatar.action=="idle")
	print("MOVEMENT_VISUAL_V07: touch double jump and tree landing passed")
	quit()
