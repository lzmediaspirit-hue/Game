extends Control
var world: Node2D
var image: Texture2D
var time = 0.0
var biome_images: Dictionary={}
func _ready():
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	image=load("res://art/environment/sanctuary-v3.png")
	var atlas=load("res://art/environment/biomes-v6.png")
	for biome in ["forest","cave"]:
		var texture=AtlasTexture.new()
		texture.atlas=atlas
		texture.region=Rect2(0,0 if biome=="forest" else atlas.get_height()/2,atlas.get_width(),atlas.get_height()/2)
		biome_images[biome]=texture
func _process(delta):
	time+=delta
	queue_redraw()
func _draw():
	var view=get_viewport_rect().size
	var cam=world.camera.position if is_instance_valid(world) and world.camera else Vector2(640,360)
	var scenery=image
	if is_instance_valid(world):
		var biome=str(world.map_data.get("background","settlement"))
		if biome_images.has(biome): scenery=biome_images[biome]
	var shift=(cam-Vector2(640,360))*Vector2(0.055,0.10)
	var factor=maxf((view.x+400)/scenery.get_width(),(view.y+180)/scenery.get_height())
	var drawn=scenery.get_size()*factor
	var margin=(drawn-view)*0.5
	shift.x=clampf(shift.x,-margin.x,margin.x)
	shift.y=clampf(shift.y,-margin.y,margin.y)
	draw_texture_rect(scenery,Rect2((view-drawn)/2-shift,drawn),false)
	if is_instance_valid(world):
		# Separate translucent mist planes create near/far parallax without map seams.
		for i in 3:
			var y=420+i*110-cam.y*(0.12+i*0.06)
			var points=PackedVector2Array()
			for x in range(-100,1500,60):
				points.append(Vector2(x,y+sin(x*0.007+time*0.08+i-cam.x*0.0002)*22))
			points.append(Vector2(1500,900))
			points.append(Vector2(-100,900))
			draw_colored_polygon(points,Color(0.5,0.77,0.78,0.035))
	else:
		draw_rect(Rect2(Vector2.ZERO,view),Color(0.015,0.04,0.065,0.25))
