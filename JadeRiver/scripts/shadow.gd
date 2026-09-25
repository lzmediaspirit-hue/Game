extends Node2D
var player: Node2D
var world: Node2D
func _process(_delta):
	var support=world.landing_target(player.plane,player.altitude+0.1,-1)
	visible=support!=null
	if support:
		position=Vector2(player.plane.x,player.plane.y-support.height_at(player.plane))
		z_index=int(1499+player.plane.y) if support.stratum=="ground" and support.base==0 and support.rise==0 else 1501+int(support.bounds.end.y)
		scale=Vector2(1,0.26)*clampf(1-player.jump_height/500,0.55,1)
	queue_redraw()
func _draw():
	draw_circle(Vector2.ZERO,15,Color(0.01,0.035,0.04,0.4))
	# S43 landing ring: airborne within 200 of the surface below, a ring marks where you will land.
	var st=player.state
	if st.surface==null and not st.flying and st.climbing.is_empty() and player.jump_height<=200.0 and player.jump_height>4.0:
		var k=1.0-player.jump_height/200.0
		draw_arc(Vector2.ZERO,24.0,0,TAU,32,Color(0.55,0.95,0.8,0.35+0.45*k),2.5/scale.y*0.26)
		draw_arc(Vector2.ZERO,24.0+6.0*(1.0-k),0,TAU,32,Color(0.55,0.95,0.8,0.25*k),1.5/scale.y*0.26)
