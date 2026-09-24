extends SceneTree
var errors: Array[String]=[]
var checks=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		errors.append(label)
		push_error(label)
func run():
	var wardrobe=root.get_node("Wardrobe")
	var original_path=wardrobe.save_path
	var original_slots=wardrobe.slots.duplicate(true)
	wardrobe.save_path="user://generated-review-"+str(Time.get_ticks_usec())+".json"
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	var main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.enter_world(wardrobe.defaults())
	check(main.world.map_theme=="village","New character starts in generated village")
	main.world.player.hp=71
	main.world.player.qi=42
	main.world.skill_page=1
	for theme in ["road","forest","cave","mountain","town","village"]:
		main.change_region(theme,7,1)
		var world=main.world
		world.set_process(false)
		var p=world.player
		p.set_physics_process(false)
		check(world.map_theme==theme,"Transition loads "+theme)
		check(p.state.zone_id==WorldCatalog.zone_id(theme,7),"Authoritative zone identity "+theme)
		check(p.hp==71 and p.qi==42 and world.skill_page==1,"Transition preserves state "+theme)
		check(p.plane.distance_to(RoomTravel.arrival(MapGenerator.WIDTH,1))<1,"Safe region entry "+theme)
		var route_start=world.by_id("ascent_00").bounds.get_center()+Vector2(0,45)
		for waypoint in [Vector2(route_start.x,850),route_start]:
			for frame in 2400:
				var offset=waypoint-p.plane
				if offset.length()<0.5: break
				p.step(1.0/30,offset.limit_length(205.0/30)/(205.0/30))
		check(p.plane.distance_to(route_start)<1,"Walk from entry to ascent "+theme)
		var last=""
		for route in world.map_data.routes:
			if not str(route.to).begins_with("ascent_") and not str(route.to).begins_with("cloud_"): continue
			var target=world.by_id(route.to)
			p.jump()
			for frame in 180:
				var offset=target.bounds.get_center()-p.plane
				p.step(1.0/120,offset.limit_length(205.0/120)/(205.0/120))
				if p.surface: break
			check(p.surface!=null and p.surface.id==target.id,"Continuous climb "+theme+" / "+target.id)
			last=target.id
		world.record_safe_position()
		var saved=wardrobe.validate({"progress":world.last_safe}).progress
		world.save_slot_index=2
		check(world.save_game()==OK,"Generated map disk save "+theme)
		wardrobe.slots=[null,null,null]
		wardrobe.load_slots()
		check(wardrobe.slots[2].progress.map_theme==theme and int(wardrobe.slots[2].progress.map_seed)==7,"Generated map disk identity "+theme)
		saved=wardrobe.slots[2].progress
		world.save_slot_index=-1
		var copy=load("res://scripts/world.gd").new()
		copy.map_theme=theme
		copy.map_seed=7
		copy.outfit=wardrobe.defaults()
		copy.outfit.progress=JSON.parse_string(JSON.stringify(saved))
		root.add_child(copy)
		copy.player.set_physics_process(false)
		copy.set_process(false)
		check(copy.player.surface.id==last and copy.player.plane.distance_to(p.plane)<0.1,"Restore generated platform "+theme)
		copy.queue_free()
		# Walk off the last platform and fall back to a supporting surface.
		for frame in 480: p.step(1.0/120,Vector2.DOWN)
		check(p.surface!=null and p.surface.id=="river_walk","Safe descent "+theme)
		await process_frame
	# Exercise the actual edge signal and deferred scene swap.
	var world=main.world
	var hud_id=main.hud.get_instance_id()
	main.hud.press(9,Vector2(100,500))
	main.hud.drag(9,Vector2(176,500))
	world.player.plane=Vector2(MapGenerator.WIDTH-300,866)
	world.travel.reset(world.player.plane)
	world.player.surface=world.by_id("river_walk")
	world.player.altitude=0
	world.player.last_axis=Vector2.RIGHT
	world.player.drag_seconds=3
	world.player.sprint_direction=Vector2.RIGHT
	world.player.sprinting=true
	world.player.plane=Vector2(MapGenerator.WIDTH-20,866)
	world._process(0.016)
	await process_frame
	await process_frame
	check(main.world.map_theme=="road","Full gate traversal enters next region")
	check(main.world.player.sprinting and main.world.player.drag_seconds>=3,"Sustained horizontal sprint survives region transition")
	check(main.hud.get_instance_id()==hud_id and main.world.player.joystick_engaged and main.world.player.movement.x>0.9,"Held joystick survives region transition")
	main.hud.release(9)
	check(main.world.player.movement==Vector2.ZERO,"Joystick release reaches new player")
	check(main.get_node("MobileHUD").get_child_count()==1,"Exactly one HUD after transitions")
	world=main.world
	world.set_process(false)
	world.player.set_physics_process(false)
	world.player.plane=Vector2(300,866)
	world.travel.reset(world.player.plane)
	world.player.plane=Vector2(20,866)
	world._process(0.016)
	await process_frame
	await process_frame
	check(main.world.map_theme=="village","West gate returns to previous room")
	check(main.world.player.plane.distance_to(RoomTravel.arrival(MapGenerator.WIDTH,-1))<1,"West travel arrives safely inside east entrance")
	main.return_to_selection()
	var legacy=wardrobe.defaults()
	legacy.progress={"map_revision":5,"map_theme":"","surface":"jade_roof","x":1000,"y":650,"hp":55,"qi":22}
	main.enter_world(legacy)
	check(main.world.map_theme=="village" and main.world.player.plane.distance_to(Vector2(300,850))<1,"Legacy disciple migrates to generated village")
	check(main.world.player.hp==55 and main.world.player.qi==22,"Legacy migration preserves resources")
	main.world.restore_progress({"map_revision":6,"map_theme":"village","map_seed":1,"generator_version":4,
		"surface":"removed_platform","x":900,"y":650,"hp":43,"qi":17,"facing":-1,"skill_page":1})
	check(main.world.player.hp==43 and main.world.player.qi==17 and main.world.skill_page==1,"Missing old surface preserves character resources")
	check(main.world.player.surface.contains(main.world.player.plane),"Missing old surface keeps safe spawn")
	for suffix in ["",".bak",".tmp"]:
		if FileAccess.file_exists(wardrobe.save_path+suffix): DirAccess.remove_absolute(wardrobe.save_path+suffix)
	wardrobe.save_path=original_path
	wardrobe.slots=original_slots
	print("GENERATED_RUNTIME: ",checks-errors.size(),"/",checks)
	quit(1 if not errors.is_empty() else 0)
