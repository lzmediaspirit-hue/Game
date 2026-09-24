extends SceneTree
var checks=0
var failures=0
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures+=1
		push_error(label)
func place(p,w,point: Vector2):
	p.surface=w.by_id("river_walk")
	p.plane=point
	p.altitude=0
	p.vertical_speed=0
	p.state.jumps_used=0
	p.attack_time=0
	p.reset_sprint()
func run():
	var w=load("res://scripts/world.gd").new()
	w.map_theme="forest"
	w.map_seed=7
	w.outfit=root.get_node("Wardrobe").defaults()
	root.add_child(w)
	w.set_process(false)
	var p=w.player
	p.set_physics_process(false)
	for rate in [30,60,120]:
		place(p,w,Vector2(2500,850))
		for i in rate*2: p.step(1.0/rate,Vector2.RIGHT)
		p.step(0.02,Vector2.RIGHT)
		check(p.sprinting,"Keyboard movement sprints after two seconds")
		p.step(1.0/rate,Vector2.LEFT)
		check(not p.sprinting and p.drag_seconds<0.1,"Reverse direction resets sprint")
		for i in rate*3: p.step(1.0/rate,Vector2.RIGHT if i%2 else Vector2.LEFT)
		check(not p.sprinting,"Alternating direction cannot trigger sprint")
		# Keep this boundary test in a clear column: held UP now intentionally
		# lands on the ordinary tree branch in the former x=2500 column.
		place(p,w,Vector2(4200,624))
		p.jump()
		for i in rate/3: p.step(1.0/rate,Vector2.UP)
		var first_height=p.altitude
		p.avatar.elapsed=0.4
		p.jump()
		check(p.state.jumps_used==2 and p.vertical_speed>0 and p.avatar.action=="jump" and p.avatar.elapsed==0,"Second jump restarts ascent and animation")
		p.step(0.1,Vector2.UP)
		check(p.altitude>first_height,"Double jump gains height")
		p.avatar.elapsed=2
		check(p.avatar.pose_frame()==5,"Jump holds its final airborne pose without looping")
		var speed=p.vertical_speed
		p.jump()
		check(p.vertical_speed==speed and p.state.jumps_used==2,"Third jump rejected")
		for i in rate*3: p.step(1.0/rate,Vector2.UP)
		check(p.surface!=null and p.surface.id=="river_walk" and p.altitude==0 and p.plane.y>=MapGenerator.GROUND_REAR,"Rear edge contains airborne actor")
		check(p.state.jumps_used==0 and p.avatar.action=="idle","Landing resets jumps and returns to idle")
		place(p,w,Vector2(2500,945))
		p.jump()
		for i in rate*2: p.step(1.0/rate,Vector2.DOWN)
		check(p.surface!=null and p.altitude==0 and p.plane.y<960,"Front ground edge contains jumps")
	for s in w.surfaces:
		if not s.id.begins_with("tree_") or not s.id.ends_with("_branch_0"): continue
		place(p,w,s.bounds.get_center()+Vector2(0,42))
		p.jump()
		for i in 180:
			p.step(1.0/120,(s.bounds.get_center()-p.plane).limit_length(205.0/120)/(205.0/120))
			if p.surface: break
		check(p.surface==s,"Ordinary tree branch landing: "+s.id)
	print("MOVEMENT_V07: ",checks-failures,"/",checks)
	quit(1 if failures else 0)
