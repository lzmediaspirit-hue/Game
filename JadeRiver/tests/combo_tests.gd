extends SceneTree
var checks=0
var failures: Array[String]=[]
var attacks: Array[String]=[]
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok:
		failures.append(label)
		push_error(label)
func run():
	var w=load("res://scripts/world.gd").new()
	w.map_theme="forest"
	w.outfit=root.get_node("Wardrobe").defaults()
	root.add_child(w)
	w.set_process(false)
	var p=w.player
	p.set_physics_process(false)
	p.attack_started.connect(func(action,_point,_height,_direction): attacks.append(action))
	for weapon in ["none","sword","spear","dagger","staff"]:
		p.avatar.outfit.weapon=weapon
		for taps in [1,2,3,8]:
			attacks.clear()
			for tap in taps: p.attack()
			p.step(3.0,Vector2.ZERO)
			check(attacks.size()==mini(taps,3),"One strike per tap; buffer capped at three: "+weapon+" taps="+str(taps))
	for rate in [30,60,120]:
		for weapon in ["none","sword","spear","dagger","staff"]:
			p.avatar.outfit.weapon=weapon
			attacks.clear()
			p.attack()
			p.attack()
			p.attack()
			for frame in rate*3:
				p.step(1.0/rate,Vector2.ZERO)
				p.avatar.refresh_entries()
				if p.attack_time>0:
					check(p.avatar.pose_frame()<int(root.get_node("Wardrobe").parts._actions[p.avatar.action].frames),"Combo stays within registered frames")
			var family="swing" if weapon=="sword" else ("punch" if weapon=="none" else "thrust")
			check(attacks==[family+"_1",family+"_2",family+"_3"],"Buffered three-hit combo "+weapon+" at "+str(rate))
			check(p.combo_index==-1 and p.combo_queue==0 and p.avatar.action=="idle","Combo ends cleanly")
	p.avatar.outfit.weapon="sword"
	attacks.clear()
	p.attack()
	p.step(0.8,Vector2.ZERO)
	p.attack()
	check(attacks==["swing_1","swing_2"],"Second tap during chain window performs the second swing")
	p.step(1.4,Vector2.ZERO)
	p.attack()
	check(attacks.back()=="swing_1","Expired chain starts at swing")
	p.attack()
	p.jump()
	check(p.combo_queue==0 and p.attack_time==0 and p.avatar.action=="jump","Jump cancels combo without a delayed strike")
	for frame in 180: p.step(1.0/120,Vector2.ZERO)
	p.avatar.outfit.weapon="bow"
	attacks.clear()
	p.attack()
	p.attack()
	p.attack()
	p.step(1.4,Vector2.ZERO)
	check(attacks==["bow"],"Bow retains its projectile attack without melee buffering")
	p.avatar.outfit.weapon="sword"
	p.attack()
	p.avatar.outfit.weapon="spear"
	p.step(0.1,Vector2.ZERO)
	check(p.attack_time==0 and p.combo_index==-1,"Equipment swap cancels old attack state")
	p.attack()
	check(attacks.back()=="thrust_1","Newly equipped spear starts its own first thrust")
	p.step(3.0,Vector2.ZERO)
	p.avatar.outfit.weapon="none"
	p.attack()
	p.step(0.65,Vector2.ZERO)
	p.avatar.outfit.weapon="sword"
	p.attack()
	check(attacks.back()=="swing_1","Swap during recovery starts the new family's first strike")
	print("COMBO_TESTS: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
