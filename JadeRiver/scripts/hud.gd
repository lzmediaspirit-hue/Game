extends Control
var font=preload("res://art/fonts/CormorantGaramond.ttf")
var frame_style: StyleBoxFlat
var player: Node2D
var skill_page=0
var scroll_progress=1.0
var scroll_direction=-1
signal page_changed(page: int)
func scroll_skills(direction: int):
	if scroll_progress<1.0: return
	scroll_direction=direction
	scroll_progress=0.0
	skill_page=(skill_page+1)%2
	page_changed.emit(skill_page)
func advance_scroll(delta: float):
	scroll_progress=minf(1.0,scroll_progress+delta/0.36)
var touches: Dictionary={}
var joystick_id=-999
var joystick_origin=Vector2.ZERO
var slots=[Vector2(1036,634),Vector2(1030,536),Vector2(1088,455),Vector2(1185,425)]
var attack_center=Vector2(1165,605)
var jump_center=Vector2(933,640)
var meditate_center=Vector2(841,640)
var mouse_down=false
const GOLD=Color("d5bd85")
func _ready():
	frame_style=panel_style()
	mouse_filter=Control.MOUSE_FILTER_IGNORE
func _process(delta):
	advance_scroll(delta)
	queue_redraw()
func _notification(what):
	if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
		touches.clear()
		joystick_id=-999
		mouse_down=false
		if is_instance_valid(player):
			player.movement=Vector2.ZERO
			player.joystick_engaged=false
			player.reset_sprint()
func role_at(p: Vector2) -> String:
	if p.distance_to(attack_center)<74: return "attack"
	if p.distance_to(jump_center)<36: return "jump"
	if p.distance_to(meditate_center)<36: return "meditate"
	for center in slots:
		if p.distance_to(center)<43: return "skill"
	if p.x<640: return "joystick"
	return "none"
func press(id: int,p: Vector2):
	var role=role_at(p)
	touches[id]={"role":role,"start":p,"swiped":false}
	match role:
		"joystick":
			if joystick_id==-999:
				joystick_id=id
				joystick_origin=p
				player.joystick_engaged=true
		"attack": player.attack()
		"jump": player.jump()
		"meditate": player.meditate()
func drag(id: int,p: Vector2):
	if not touches.has(id): return
	if id==joystick_id:
		var delta=p-joystick_origin
		player.movement=delta.limit_length(76)/76 if delta.length()>9 else Vector2.ZERO
	elif touches[id].role=="skill" and not touches[id].swiped:
		var delta=p-touches[id].start
		if absf(delta.y)>40 and absf(delta.y)>absf(delta.x):
			scroll_skills(-1 if delta.y<0 else 1)
			touches[id].swiped=true
func release(id: int):
	touches.erase(id)
	if id==joystick_id:
		joystick_id=-999
		player.movement=Vector2.ZERO
		player.joystick_engaged=false
		player.reset_sprint()
func _input(event):
	if event is InputEventMouse and event.device == -1: return
	if event is InputEventScreenTouch:
		if event.pressed and not event.canceled: press(event.index,event.position)
		else: release(event.index)
	elif event is InputEventScreenDrag: drag(event.index,event.position)
	elif event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		mouse_down=event.pressed
		if event.pressed: press(-1,event.position)
		else: release(-1)
	elif event is InputEventMouseMotion and mouse_down: drag(-1,event.position)
	elif event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_SPACE: player.jump()
			KEY_J: player.attack()
			KEY_M: player.meditate()
			KEY_TAB: scroll_skills(-1)
func ring(center: Vector2,radius: float,active=false,opacity=1.0):
	var tint=Color(1,1,1,opacity)
	draw_circle(center+Vector2(0,3),radius+4,Color(0,0.025,0.04,0.7)*tint)
	draw_circle(center,radius,Color(0.035,0.10,0.13,0.88)*tint)
	draw_arc(center,radius,0,TAU,40,(GOLD if active else Color("84958c"))*tint,2,false)
	draw_arc(center,radius-5,0,TAU,40,Color("344d52")*tint,2,false)
func skill_position(index: float) -> Vector2:
	var low=clampi(int(floor(index)),0,2)
	return slots[low].lerp(slots[low+1],index-low)
func draw_skill_scroll():
	if scroll_progress>=1:
		for center in slots: ring(center,33)
		return
	var t=scroll_progress*scroll_progress*(3-2*scroll_progress)
	var shift=-scroll_direction*4.0*t
	for page in 2:
		for i in 4:
			var index=i+shift+(scroll_direction*4 if page==1 else 0)
			if index < -0.35 or index > 3.35: continue
			var fade=minf(clampf((index+0.35)/0.35,0,1),clampf((3.35-index)/0.35,0,1))
			ring(skill_position(index),33,false,fade)
func _draw():
	if not is_instance_valid(player): return

	draw_style_box(frame_style,Rect2(22,22,310,82))
	for row in 2:
		var y=40+row*32
		var amount=player.hp if row==0 else player.qi
		draw_string(font,Vector2(38,y+13),"HP" if row==0 else "QI",HORIZONTAL_ALIGNMENT_LEFT,-1,18,GOLD)
		draw_rect(Rect2(75,y,237,16),Color("17242c"))
		draw_rect(Rect2(77,y+2,233*amount/100,12),Color("ae5360") if row==0 else Color("4bafaa"))
		draw_line(Vector2(78,y+3),Vector2(78+232*amount/100,y+3),Color(1,0.9,0.7,0.35),1)
	draw_arc(attack_center,141,PI*0.95,PI*1.55,50,Color(0.7,0.65,0.49,0.3),2,true)
	draw_skill_scroll()
	for i in 2:
		draw_circle(Vector2(1113+i*16,501),3,GOLD if i==skill_page else Color("344d52"))
	ring(attack_center,66,player.attack_time>0)
	# A restrained sword glyph; skill sockets remain completely empty.
	draw_colored_polygon(PackedVector2Array([attack_center+Vector2(-20,13),attack_center+Vector2(17,-27),attack_center+Vector2(28,-33),attack_center+Vector2(25,-20),attack_center+Vector2(-13,20)]),GOLD)
	draw_line(attack_center+Vector2(-27,8),attack_center+Vector2(-8,26),GOLD,5,true)
	draw_line(attack_center+Vector2(-19,20),attack_center+Vector2(-29,32),GOLD,5,true)
	ring(jump_center,32)
	draw_line(jump_center+Vector2(0,15),jump_center+Vector2(0,-14),GOLD,3,true)
	draw_polyline(PackedVector2Array([jump_center+Vector2(-11,-3),jump_center+Vector2(0,-15),jump_center+Vector2(11,-3)]),GOLD,3,true)
	ring(meditate_center,32,player.meditating)
	for i in range(-1,2):
		var tip=meditate_center+Vector2(i*17,-12 if i!=0 else -19)
		draw_polyline(PackedVector2Array([meditate_center+Vector2(-14,11),tip,meditate_center+Vector2(14,11)]),GOLD,2,true)
	draw_arc(meditate_center+Vector2(0,2),18,0,PI,20,GOLD,2,true)
func panel_style() -> StyleBoxFlat:
	var style=StyleBoxFlat.new()
	style.bg_color=Color(0.025,0.075,0.10,0.88)
	style.border_color=Color("958665")
	style.set_border_width_all(1)
	style.set_corner_radius_all(6)
	return style
