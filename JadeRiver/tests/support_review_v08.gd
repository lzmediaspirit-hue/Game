extends SceneTree
var failures=0
var checks=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures+=1
		push_error(label)
func run():
	var data=MapGenerator.generate("forest",7)
	var zone=ZoneGeometry.new()
	zone.configure(ZoneLayout.compile(data))
	var masks=JSON.parse_string(FileAccess.get_file_as_string("res://data/surface_masks.json"))
	for key in masks:
		var viewport=SubViewport.new()
		viewport.size=Vector2i(640,480)
		viewport.transparent_bg=true
		viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var kind="roof" if str(key).begins_with("roof") else str(key)
		var spec={"id":"review","rect":[100,200,320,120],"height":88,"kind":kind,"support_mask":masks[key],"visual_variant":1 if key=="roof_odd" else 0}
		var surface=WalkSurface.new(spec)
		var terrain=load("res://scripts/terrain.gd").new()
		terrain.surface=surface
		terrain.generated=true
		viewport.add_child(terrain)
		await process_frame
		await RenderingServer.frame_post_draw
		var rendered=viewport.get_texture().get_image()
		var solid=0
		var empty=0
		for y in 24:
			for x in 32:
				var point=surface.bounds.position+Vector2((x+0.5)/32,(y+0.5)/24)*surface.bounds.size
				if surface.contains(point):
					solid+=1
					var screen=point-Vector2(0,88)
					check(rendered.get_pixel(int(screen.x),int(screen.y)).a>0.85,"Supported point must have rendered artwork: "+str(key)+" "+str(point))
				else: empty+=1
		check(solid>0 and empty>0,"Surface uses shaped support: "+str(key))
		viewport.queue_free()
	var w=load("res://scripts/world.gd").new()
	w.map_theme="forest"
	w.outfit=root.get_node("Wardrobe").defaults()
	root.add_child(w)
	w.set_process(false)
	w.player.set_physics_process(false)
	var p=w.player
	for surface in w.surfaces:
		if surface.kind!="tree_branch": continue
		p.surface=surface
		p.plane=surface.nearest_supported(surface.bounds.get_center())
		p.altitude=surface.base
		p.vertical_speed=0
		for i in 240: p.step(1.0/120,Vector2.ZERO)
		check(p.surface==surface and p.altitude==surface.base,"Stable standing on "+surface.id)
		for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
			p.surface=surface
			p.plane=surface.nearest_supported(surface.bounds.get_center())
			p.altitude=surface.base
			for i in 80:
				p.step(1.0/120,direction)
				check(p.surface==null or p.surface.contains(p.plane),"No unsupported walking: "+surface.id)
	p.surface=w.by_id("river_walk")
	p.plane=Vector2(2500,850)
	p.altitude=0
	p.reset_sprint()
	# Vertical input must never accrue horizontal sprint time, even before reaching an edge.
	for i in 150:
		p.plane.y=850
		p.step(1.0/60,Vector2.UP)
	check(not p.sprinting and p.drag_seconds==0,"Vertical movement never sprints")
	for i in 130:
		p.plane.y=850
		p.step(1.0/60,Vector2(1,0.4 if i%2 else -0.4))
	check(p.sprinting,"Same horizontal direction tolerates depth movement")
	p.step(1.0/60,Vector2.LEFT)
	check(not p.sprinting,"Horizontal reversal resets sprint")
	var arrow=load("res://scripts/arrow.gd").new()
	arrow.zone=zone
	arrow.plane=Vector2(140,670)
	arrow.altitude=20
	root.add_child(arrow)
	arrow.set_physics_process(false)
	arrow.advance(0.5)
	check(arrow.is_queued_for_deletion() and arrow.plane.x<200,"Arrow stops at tree trunk instead of crossing it")
	var town=ZoneGeometry.new()
	town.configure(ZoneLayout.compile(MapGenerator.generate("town",7)))
	for roof in town.surfaces:
		if roof.kind!="roof": continue
		for rate in [30,60,120]:
			for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
				var actor=ActorState.new()
				actor.surface=roof
				actor.plane=roof.nearest_supported(roof.bounds.get_center())
				actor.altitude=roof.base
				for frame in rate*2:
					MovementSolver.advance(actor,town,1.0/rate,direction*205)
					check(actor.surface==null or (actor.surface.contains(actor.plane) and not town.blocks(actor.plane,actor)),"Roof edge cannot leave unsupported grounded state: "+roof.id)
	var restored=load("res://scripts/world.gd").new()
	restored.map_theme="town"
	restored.map_seed=7
	restored.outfit=root.get_node("Wardrobe").defaults()
	var roof=town.index.building_00
	restored.outfit.progress={"map_revision":6,"map_theme":"town","map_seed":7,"generator_version":3,
		"surface":"building_00","x":roof.bounds.position.x+1,"y":roof.bounds.position.y+1,"hp":61,"qi":23}
	root.add_child(restored)
	restored.player.set_physics_process(false)
	restored.set_process(false)
	check(restored.player.surface.id=="building_00" and restored.player.surface.contains(restored.player.plane),"Old roof save moves onto visible support")
	check(restored.player.hp==61 and restored.player.qi==23,"Support migration preserves resources")
	print("SUPPORT_REVIEW_V08: ",checks-failures,"/",checks)
	quit(1 if failures else 0)
