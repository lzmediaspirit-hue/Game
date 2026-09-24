extends "res://tests/movement_visual_v07.gd"
func shot(label: String):
	main.world.player.sync_visual()
	main.world.camera.position=main.world.camera_target()
	main.world.update_occlusion()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../previews/v09-"+label+".png")
func run():
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(root.get_node("Wardrobe").defaults())
	var w=main.world
	w.set_process(false)
	var p=w.player
	p.set_physics_process(false)
	var roof=w.by_id("building_01")
	p.surface=w.by_id("river_walk")
	p.plane=Vector2(roof.bounds.get_center().x,590)
	p.altitude=0
	await shot("behind-building")
	p.avatar.play("swing")
	p.avatar.elapsed=0.2
	await shot("attack-outline")
	p.avatar.play("meditate")
	p.avatar.elapsed=0.5
	await shot("meditation-outline")
	p.avatar.play("idle")
	p.surface=roof
	p.plane=roof.nearest_supported(roof.bounds.get_center())
	p.altitude=roof.base
	await shot("rooftop")
	p.surface=w.by_id("river_walk")
	p.plane=Vector2(900,946)
	p.altitude=0
	await shot("front-ground")
	p.surface=w.by_id("garden_terrace")
	p.plane=Vector2(5080,650)
	p.altitude=64
	await shot("terrace")
	main.change_region("forest",7,1)
	w=main.world
	w.set_process(false)
	p=w.player
	p.set_physics_process(false)
	var target=w.by_id("tree_00_branch_0")
	p.plane=target.bounds.get_center()+Vector2(0,42)
	p.altitude=0
	p.surface=w.by_id("river_walk")
	main.hud.press(1,main.hud.jump_center)
	main.hud.release(1)
	for frame in 180:
		p.step(1.0/120,(target.nearest_supported(target.bounds.get_center())-p.plane).limit_length(205.0/120)/(205.0/120))
		p.avatar._process(1.0/120)
		if p.surface: break
	assert(p.surface==target)
	await shot("branch-landing")
	print("VISUAL_V09: building depth, roof, ground edge and touch branch landing captured")
	quit()
