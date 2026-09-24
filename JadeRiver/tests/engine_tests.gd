extends Node
const World=preload("res://scripts/world.gd")
const Hud=preload("res://scripts/hud.gd")
var failures: Array[String]=[]
var count=0
func check(value: bool,message: String):
	count+=1
	if not value:
		failures.append(message)
		push_error(message)
func _ready(): call_deferred("run")
func place(p,world,id: String,point: Vector2):
	p.surface=world.by_id(id)
	p.plane=point
	p.altitude=p.surface.height_at(point)
	p.vertical_speed=0
	p.attack_time=0
	p.bow_release_time=-1
	p.meditating=false
	p.joystick_engaged=false
	p.movement=Vector2.ZERO
	p.reset_sprint()
	p.sync_visual()
func run():
	var world=World.new()
	world.outfit=Wardrobe.defaults()
	add_child(world)
	world.set_process(false)
	var p=world.player
	p.set_physics_process(false)
	check(Wardrobe.attack_for({"weapon":"sword"})=="swing","Sword dispatch")
	check(Wardrobe.attack_for({"weapon":"bow"})=="bow","Bow dispatch")
	check(Wardrobe.attack_for({"weapon":"none"})=="punch","Unarmed dispatch")
	check(Wardrobe.validate({"hair":"invalid","name":""}).hair=="topknot","Invalid appearance recovers")
	for category in ["body","hair","shirt","pants","shoes","weapon"]:
		for item in Wardrobe.parts[category].values():
			for layer in item.get("layers",[]):
				for anim in layer.animations.values():
					for path in anim.get("sheets",[]):
						check(FileAccess.file_exists(path.replace("art_v12/","res://art/")),"Asset exists: "+path)
	check(p.avatar.scale==Vector2.ONE,"Gameplay character uses smaller native 2x artwork")
	# Full foreground route passes under every roof without climbing automatically.
	place(p,world,"river_walk",Vector2(20,845))
	for i in 3150: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x>5300 and p.altitude==0 and p.surface.id=="river_walk","Ground route remains free beneath all platforms")
	place(p,world,"river_walk",Vector2(4630,730))
	for i in 112: p.step(1.0/120,Vector2.UP)
	check(p.surface.id=="upper_terrace" and is_equal_approx(p.altitude,80),"Depth stairs connect raised ground terrace")
	for i in 112: p.step(1.0/120,Vector2.DOWN)
	check(p.surface.id=="river_walk" and is_zero_approx(p.altitude),"Depth stairs descend continuously to ground")
	place(p,world,"jade_roof",Vector2(1300,650))
	var prior=p.plane
	for i in 20: p.step(1.0/120,Vector2.DOWN)
	check(p.plane.y>prior.y and p.altitude==88,"Roof has walkable depth")
	var jump_plane=p.plane
	p.jump()
	check(p.jump_height==0,"Roof takeoff is relative to support height")
	for i in 20: p.step(1.0/120,Vector2.ZERO)
	check(p.jump_height>0 and absf(p.jump_height-(p.altitude-88))<0.1 and p.plane==jump_plane,"Jump height independent of depth")
	for i in 150: p.step(1.0/120,Vector2.ZERO)
	check(p.surface.id=="jade_roof" and p.altitude==88,"Roof jump lands on roof")
	place(p,world,"jade_roof",Vector2(1300,705))
	for i in 100: p.step(1.0/120,Vector2.DOWN)
	check(p.surface!=null and p.surface.id=="river_walk" and not world.geometry.blocks(p.plane,p.state),"Open roof edge drops to unblocked ground")
	check(not FileAccess.get_file_as_string("res://data/world.json").contains("\"portal\""),"No automatic rooftop transport links")
	# Actual reachable one-way landings, including long-frame integration.
	for dt in [1.0/30,1.0/60,1.0/120,0.2]:
		place(p,world,"river_walk",Vector2(1150,650))
		p.jump()
		for i in int(ceil(1.2/dt)): p.step(dt,Vector2.ZERO)
		check(p.surface!=null and p.surface.id=="jade_roof","Ground jump reaches low roof at dt="+str(dt))
	place(p,world,"river_walk",Vector2(2300,650))
	p.jump()
	for i in 150: p.step(0.01,Vector2.ZERO)
	check(p.surface.id=="river_walk","Jump cannot reach a roof above maximum height")
	for route in [["jade_roof",1520,"bridge_roof"],["bridge_roof",2010,"cloud_roof"],["east_entry",3450,"east_step"],["east_step",3740,"heaven_roof"]]:
		place(p,world,route[0],Vector2(route[1],650))
		p.jump()
		for i in 85: p.step(0.01,Vector2.RIGHT)
		check(p.surface!=null and p.surface.id==route[2],"Reachable roof jump: "+route[0]+" to "+route[2])
	place(p,world,"jade_roof",Vector2(1150,650))
	p.jump()
	for i in 46: p.step(0.01,Vector2.ZERO)
	check(p.z_index>int(560-88),"Jump apex remains visible above its roof deck")
	place(p,world,"upper_terrace",Vector2(4560.5,550))
	p.step(0.1,Vector2(-1,1).normalized())
	check(p.plane.y>550 and p.altitude==80,"Closed side wall allows depth sliding")
	place(p,world,"river_walk",Vector2(600,850))
	var start=p.plane
	p.step(0.1,Vector2(99,99))
	check(p.plane.distance_to(start)<=20.501,"Oversized input cannot increase movement speed")
	var snapshot=p.authority.snapshot()
	check(snapshot.entity_id=="local-disciple" and snapshot.zone_id=="jade_river" and snapshot.schema==2,"Versioned identity-bearing simulation snapshot")
	start=p.plane
	check(not p.authority.move(p.command_sequence,Vector2.RIGHT,0.1,205) and p.plane==start,"Duplicate commands rejected without moving actor")
	check(not p.authority.move(p.command_sequence+1,Vector2(INF,0),0.1,205),"Nonfinite movement rejected")
	place(p,world,"river_walk",Vector2(600,850))
	world.record_safe_position()
	p.hp=65
	p.qi=37
	p.facing=-1
	world.skill_page=1
	p.surface=null
	p.altitude=-260
	world.recover_to_safe()
	check(p.hp==65 and p.qi==37 and p.facing==-1 and world.skill_page==1,"Fall recovery preserves resources and skill page")
	check(world.props.size()==5 and world.geometry.obstacles.size()==11,"Structured map loads five props and six building volumes")
	place(p,world,"river_walk",Vector2(850,700))
	for i in 80: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x<890,"House footprint blocks grounded movement")
	place(p,world,"river_walk",Vector2(2050,700))
	p.jump()
	for i in 150: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x<2090 and p.surface!=null and p.surface.id=="river_walk","Unreachable building volume cannot be crossed by jumping")
	place(p,world,"jade_roof",Vector2(920,690))
	var roof_start=p.plane.x
	for i in 30: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x>roof_start+40,"Ground obstacle footprint never blocks the platform above it")
	place(p,world,"river_walk",Vector2(278,725))
	for i in 80: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x<315,"Scholar rock footprint blocks from either frame direction")
	place(p,world,"river_walk",Vector2(2300,930))
	for i in 80: p.step(1.0/120,Vector2.RIGHT)
	check(p.plane.x<2330,"Garden stones block walking")
	place(p,world,"river_walk",Vector2(1000,650))
	world.update_occlusion()
	check(p.visible and world.player_outline.visible,"House occlusion preserves sprite pixels outside scenery")
	place(p,world,"river_walk",Vector2(1000,760))
	world.update_occlusion()
	check(p.visible and not world.player_outline.visible,"Player in front of a house renders normally")
	place(p,world,"river_walk",Vector2(3010,650))
	world.update_occlusion()
	check(p.visible and world.player_outline.visible,"Tree uses partial occlusion with animated outline")
	var occupied={"schema":2,"tick":p.authority.tick+1,"entity_id":"local-disciple","zone_id":"jade_river","x":360.0,"y":725.0,"altitude":0.0,"vz":0.0,"vx":0.0,"vy":0.0,"surface":"river_walk","air_base":0.0,"air_stratum":"ground"}
	check(not p.authority.restore_authoritative_snapshot(occupied),"Authoritative snapshot inside a solid footprint is rejected")
	var old_progress={"map_revision":3,"surface":"river_walk","x":360.0,"y":725.0,"hp":75.0,"qi":45.0,"facing":1,"skill_page":0}
	world.restore_progress(old_progress)
	check(not world.geometry.blocks(p.plane,p.state) and p.surface.contains(p.plane),"Migrated save inside new scenery moves to the nearest valid ground point")
	for dt in [1.0/30,1.0/60,0.2]:
		place(p,world,"river_walk",Vector2(850,700))
		for i in int(ceil(0.6/dt)): p.step(dt,Vector2.RIGHT)
		check(p.plane.x<890,"Solid building collision remains stable at dt="+str(dt))
	place(p,world,"river_walk",Vector2(500,800))
	for obstacle in world.geometry.obstacles:
		if not obstacle.get("blocks",true): continue
		var footprint: Rect2=obstacle.footprint
		check(world.geometry.blocks_at(footprint.get_center(),0,"ground"),"Solid footprint is active: "+obstacle.id)
		for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
			var start_point=footprint.get_center()+direction*(maxf(footprint.size.x,footprint.size.y)+24)
			var resolved=world.geometry.resolve_motion(start_point,footprint.get_center(),p.state)
			check(not footprint.grow(float(obstacle.get("radius",11))).has_point(resolved),"Cardinal sweep cannot enter "+obstacle.id)
	# Projected sorting: deck, feet, and front lip; foreground is always clear.
	var deck: Node2D
	check(world.terrain_visuals.size()==world.surfaces.size(),"Exactly one terrain drawable per surface")
	for visual in world.terrain_visuals:
		if visual.surface.id=="jade_roof":
			deck=visual
	world.update_sorting()
	place(p,world,"river_walk",Vector2(1250,740))
	check(p.z_index>deck.z_index,"Ground player sorts in front of background roof")
	place(p,world,"jade_roof",Vector2(1250,650))
	check(deck.z_index<p.z_index,"Platform feet sort above the roof artwork")
	p.qi=50
	p.meditate()
	p.step(0.4,Vector2.ZERO)
	check(p.meditating and p.qi>50,"Meditation restores QI")
	p.step(0.01,Vector2.RIGHT)
	check(not p.meditating,"Movement interrupts meditation")
	var hud=Hud.new()
	hud.player=p
	add_child(hud)
	hud.set_process(false)
	place(p,world,"river_walk",Vector2(400,820))
	hud.press(1,Vector2(200,500))
	hud.drag(1,Vector2(276,500))
	for i in 120: p.step(1.0/60,Vector2.RIGHT)
	check(not p.sprinting,"Sprint waits until drag exceeds two seconds")
	p.step(0.02,Vector2.RIGHT)
	check(p.sprinting and p.velocity.x>p.speed*1.6 and p.avatar.playback_speed>1,"Held joystick enables faster movement and animation")
	hud.press(2,hud.jump_center)
	check(p.movement.x==1 and p.surface==null,"Multi-touch jump preserves movement")
	hud.release(2)
	check(p.movement.x==1,"Action release preserves joystick")
	hud.release(1)
	check(not p.sprinting and p.drag_seconds==0 and p.movement==Vector2.ZERO,"Release resets sprint")
	hud.press(1,Vector2(200,500))
	hud.drag(1,Vector2(276,500))
	p.step(2.1,Vector2.RIGHT)
	hud.drag(1,Vector2(200,500))
	p.step(0.01,Vector2.ZERO)
	check(not p.sprinting,"Joystick dead zone resets sprint")
	hud.press(3,hud.slots[0])
	hud.drag(3,hud.slots[0]-Vector2(0,70))
	check(hud.skill_page==1 and hud.scroll_progress==0,"Swipe starts visible page transition")
	hud.advance_scroll(0.15)
	check(hud.scroll_progress>0 and hud.scroll_progress<1,"Skill scroll has intermediate frames")
	hud.advance_scroll(0.3)
	check(hud.scroll_progress==1,"Skill scroll finishes")
	hud.release(3)
	hud.press(3,hud.slots[2])
	hud.drag(3,hud.slots[2]+Vector2(0,70))
	check(hud.skill_page==0 and hud.scroll_direction==1,"Downward swipe reverses animation")
	hud._notification(NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(p.movement==Vector2.ZERO and not p.sprinting and hud.touches.is_empty(),"Focus loss clears held controls")
	place(p,world,"river_walk",Vector2(900,810))
	p.avatar.equip("weapon","bow")
	p.attack()
	p.step(0.5,Vector2.ZERO)
	check(get_tree().get_nodes_in_group("arrows").is_empty(),"Bow waits for release frame")
	p.step(0.06,Vector2.ZERO)
	var arrows=get_tree().get_nodes_in_group("arrows")
	check(arrows.size()==1,"Bow releases exactly one projectile")
	var arrow=arrows[0]
	arrow.set_physics_process(false)
	var initial=arrow.position.x
	arrow.advance(0.3)
	check(arrow.position.x>initial and arrow.travelled>0,"Arrow flies forward")
	p.step(0.7,Vector2.ZERO)
	check(get_tree().get_nodes_in_group("arrows").size()==1,"Release does not duplicate arrows")
	arrow.advance(2)
	check(arrow.travelled==480 and arrow.is_queued_for_deletion(),"Arrow disappears at finite range")
	world.spawn_arrow(Vector2(1400,800),0,-1)
	var left_arrow=get_tree().get_nodes_in_group("arrows").back()
	left_arrow.set_physics_process(false)
	var left_start=left_arrow.position.x
	left_arrow.advance(0.2)
	check(left_arrow.position.x<left_start,"Left-facing bow shoots left")
	left_arrow.queue_free()
	p.avatar.equip("weapon","sword")
	p.attack_time=0
	p.attack()
	check(p.bow_release_time<0,"Melee does not schedule a projectile")
	# Sweep every walkable surface in eight directions, including open edges and corners.
	var sweep_ok=true
	for support in world.surfaces:
		for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN,Vector2(1,1).normalized(),Vector2(-1,1).normalized(),Vector2(1,-1).normalized(),Vector2(-1,-1).normalized()]:
			place(p,world,support.id,support.bounds.get_center())
			world.record_safe_position()
			for i in 240:
				p.step(1.0/60,direction)
				sweep_ok=sweep_ok and p.plane.is_finite() and is_finite(p.altitude)
				if p.surface: sweep_ok=sweep_ok and p.surface.contains(p.plane) and absf(p.altitude-p.surface.height_at(p.plane))<0.01
	check(sweep_ok,"All surface direction sweeps keep finite valid supported positions")
	var first=ActorState.new()
	var second=ActorState.new()
	first.surface=world.by_id("river_walk")
	second.surface=first.surface
	var first_authority=LocalAuthority.new(first,world.geometry)
	var second_authority=LocalAuthority.new(second,world.geometry)
	for i in 120:
		var input=Vector2(cos(i*0.05),sin(i*0.05))
		first_authority.move(i,input,1.0/60,205)
		second_authority.move(i,input,1.0/60,205)
	check(first_authority.snapshot()==second_authority.snapshot(),"Identical command replay produces identical local state")
	var trusted=first_authority.snapshot()
	trusted.x+=10
	check(second_authority.restore_authoritative_snapshot(trusted) and second.plane.x==trusted.x,"Trusted authoritative correction updates simulation independently of rendering")
	trusted.zone_id="other_zone"
	check(not second_authority.restore_authoritative_snapshot(trusted),"Snapshot for another zone is rejected")
	# Save tests use their own path and preserve all real player data.
	var old_slots=Wardrobe.slots.duplicate(true)
	var old_path=Wardrobe.save_path
	Wardrobe.save_path="user://engine-v2-test.json"
	Wardrobe.slots=[null,null,null]
	var appearance=Wardrobe.defaults()
	appearance.hair_color=4
	appearance.name="Azure Disciple"
	check(Wardrobe.save_slot(1,appearance)==OK,"Character creation save succeeds")
	world.save_slot_index=1
	p.avatar.outfit=appearance.duplicate(true)
	place(p,world,"jade_roof",Vector2(1290,650))
	p.hp=78
	p.qi=42
	p.facing=-1
	world.skill_page=1
	check(world.save_game()==OK,"World progress saves")
	p.qi=39
	world._process(5.1)
	check(Wardrobe.slots[1].progress.qi==39 and world.save_timer==0,"Timed autosave writes changed progress")
	p.qi=42
	world.save_game()
	Wardrobe.slots=[null,null,null]
	Wardrobe.load_slots()
	var saved=Wardrobe.slots[1]
	check(saved.hair_color==4 and saved.progress.surface=="jade_roof" and saved.progress.hp==78,"Dye, equipment and progress persist")
	check(Wardrobe.slots[0]==null and Wardrobe.slots[2]==null,"Other slots remain independent")
	place(p,world,"river_walk",Vector2(400,800))
	world.restore_progress(saved.progress)
	check(p.plane==Vector2(1290,650) and p.altitude==88 and p.qi==42 and p.facing==-1 and world.skill_page==1,"World state restores on exact elevation")
	world.record_safe_position()
	p.jump()
	p.step(0.1,Vector2.RIGHT)
	world.save_game()
	check(Wardrobe.slots[1].progress.x==1290,"Midair save uses last safe surface position")
	var f=FileAccess.open(Wardrobe.save_path,FileAccess.WRITE)
	f.store_string("not a save")
	f.close()
	Wardrobe.load_slots()
	check(Wardrobe.slots[1].hair_color==4,"Damaged primary save recovers from backup")
	f=FileAccess.open(Wardrobe.save_path,FileAccess.WRITE)
	var legacy=Wardrobe.defaults()
	legacy.erase("hair_color")
	f.store_string(JSON.stringify({"version":1,"slots":[legacy,null,null]}))
	f.close()
	Wardrobe.load_slots()
	check(Wardrobe.slots[0].hair_color==0 and not Wardrobe.slots[0].has("progress"),"Version 1 appearance saves migrate safely")
	check(Wardrobe.save_slot(8,appearance)==ERR_INVALID_PARAMETER,"Invalid slot rejected")
	var test_path=Wardrobe.save_path
	Wardrobe.save_path=test_path+"/not_a_directory.json"
	var before_failed_save=Wardrobe.slots.duplicate(true)
	check(Wardrobe.save_slot(1,appearance)!=OK and Wardrobe.slots==before_failed_save,"Failed write cannot replace in-memory character data")
	Wardrobe.save_path=test_path
	for suffix in ["",".bak",".tmp"]: DirAccess.remove_absolute(Wardrobe.save_path+suffix)
	Wardrobe.save_path=old_path
	Wardrobe.slots=old_slots
	world.save_slot_index=-1
	var main=load("res://scenes/main.tscn").instantiate()
	add_child(main)
	main.preview_mode=true
	main.show_creation(0)
	check(main.dye_buttons.size()==6,"Creation offers six hair dyes")
	main.set_hair_dye(2)
	check(main.draft.hair_color==2 and main.preview.outfit.hair_color==2,"Dye updates live idle preview")
	check(main.preview.action=="idle","Creation remains idle only")
	var before=main.draft.hair
	main.cycle("hair",1)
	check(main.draft.hair!=before and main.draft.hair_color==2,"Hair style changes preserve dye")
	main.cycle("sect",1)
	check(main.draft.sect=="Cloud","Sect choice works")
	main.show_selection()
	check(main.screen=="selection","Cancel returns safely")
	print("ENGINE_TESTS: ",count-failures.size(),"/",count," passed")
	get_tree().quit(0 if failures.is_empty() else 1)




