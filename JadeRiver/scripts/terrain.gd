extends Node2D
## Painted atlas regions are projected onto the same bounds used by simulation.
var surface: WalkSurface
var ground_material="stone"
var generated=false
const PLATFORMS=preload("res://art/environment/platforms-v6.png")
const GROUND=preload("res://art/environment/ground-v6.png")
const STONE=preload("res://art/environment/courtyard-v3.png")
const BUILDING=preload("res://art/environment/pavilion-v3.png")
const BUILDINGS=preload("res://art/environment/wuxia-buildings-v4.png")
const STAIRS=preload("res://art/environment/temple-stairs-v4.png")
func pt(x: float,y: float) -> Vector2:
	return Vector2(x,y-surface.height_at(Vector2(x,y)))
func region(destination: Rect2,source: Rect2,tint=Color.WHITE):
	draw_texture_rect_region(BUILDING,destination,source,tint)
func paving(rect: Rect2,tint=Color.WHITE):
	# Mirrored repeats meet at identical edge pixels, avoiding seams in generated texture.
	var tile=Vector2(256,128)
	var texture: Texture2D=STONE
	var texture_region=Rect2(Vector2.ZERO,STONE.get_size())
	if generated:
		texture=GROUND
		var quadrants={"earth":Vector2(0,0),"moss":Vector2(1,0),"slate":Vector2(0,1),"stone":Vector2(1,1)}
		var cell=GROUND.get_size()/2
		texture_region=Rect2(quadrants.get(ground_material,Vector2.ONE)*cell,cell)
	for row in int(ceil(rect.size.y/tile.y)):
		for col in int(ceil(rect.size.x/tile.x)):
			var p=rect.position+Vector2(col,row)*tile
			var size=(rect.end-p).min(tile)
			var src=Rect2(texture_region.position,texture_region.size*size/tile)
			if col%2: src.position.x=texture_region.end.x-src.size.x
			if row%2: src.position.y=texture_region.end.y-src.size.y
			var dest=Rect2(p,size)
			if col%2: dest.size.x=-dest.size.x
			if row%2: dest.size.y=-dest.size.y
			draw_texture_rect_region(texture,dest,src,tint)
func building_source() -> Rect2:
	if generated:
		return Rect2(739,70,797,390) if surface.visual_variant%2==0 else Rect2(0,475,900,549)
	match surface.id:
		"jade_roof": return Rect2(739,70,797,390)
		"bridge_roof": return Rect2(0,0,720,465)
		"cloud_roof", "heaven_roof": return Rect2(0,475,900,549)
		_: return Rect2(1040,475,365,549)
func painted_building(a: Vector2,width: float):
	var source=building_source()
	# Roof depth and facade height project from the physical building volume.
	var roof_pixels=source.size.y*0.43
	var roof_source=Rect2(source.position,Vector2(source.size.x,roof_pixels))
	var facade_source=Rect2(source.position+Vector2(0,roof_pixels),Vector2(source.size.x,source.size.y-roof_pixels))
	draw_texture_rect_region(BUILDINGS,Rect2(a,Vector2(width,surface.bounds.size.y)),roof_source)
	var front=Vector2(a.x,surface.bounds.end.y-surface.base)
	draw_texture_rect_region(BUILDINGS,Rect2(front,Vector2(width,surface.base)),facade_source)
func _draw():
	var r=surface.bounds
	var a=pt(r.position.x,r.position.y)
	var d=pt(r.position.x,r.end.y)
	match surface.kind:
		"cloud", "tree_branch", "rock_ledge":
			var row_y=70 if surface.kind=="tree_branch" else (400 if surface.kind=="cloud" else 700)
			var source=Rect2(0,row_y,PLATFORMS.get_width(),290)
			draw_texture_rect_region(PLATFORMS,Rect2(a,r.size),source)
		"balcony":
			for x in [4,r.size.x-8]:
				draw_rect(Rect2(d+Vector2(x,0),Vector2(6,surface.base)),Color("493326"))
				draw_line(d+Vector2(x,0),d+Vector2(x,surface.base),Color("bd9562"),2)
			draw_rect(Rect2(a,r.size),Color("49382c"))
			for y in range(0,int(r.size.y),8):
				draw_line(a+Vector2(0,y),a+Vector2(r.size.x,y),Color("b39062"),2)
				draw_line(a+Vector2(0,y+4),a+Vector2(r.size.x,y+4),Color("725436"),2)
			draw_rect(Rect2(d,Vector2(r.size.x,10)),Color("382b24"))
			for x in [4,r.size.x-8]:
				draw_rect(Rect2(a+Vector2(x,0),Vector2(4,r.size.y+10)),Color("ccac70"))
		"ground":
			var extent=r.size+Vector2(0,500 if surface.base==0 else 0)
			var ground_origin=a
			if generated and surface.base==0:
				ground_origin.x-=640
				extent.x+=1280
			var tint=Color("929f9f")
			if ground_material=="earth": tint=Color("b29c73")
			elif ground_material=="moss": tint=Color("7b9b70")
			elif ground_material=="slate": tint=Color("728090")
			if generated: tint=Color.WHITE
			paving(Rect2(ground_origin,extent),tint)
			if generated and ground_material in ["moss","earth"] and surface.base==0:
				var original=ground_material
				ground_material="earth"
				paving(Rect2(-640,790,r.size.x+1280,130),Color("e0d4b5"))
				ground_material=original
			if not generated or ground_material=="stone": region(Rect2(a-Vector2(0,12),Vector2(r.size.x,12)),Rect2(76,721,1380,28))
			if surface.base>0:
				var wall_height=surface.base if generated else maxf(28,632-d.y)
				draw_texture_rect_region(BUILDINGS,Rect2(d,Vector2(r.size.x,wall_height)),Rect2(768,382,768,92),Color("c8d0c5"))
				draw_line(d,d+Vector2(r.size.x,0),Color("e1d4ac"),4)
		"roof":
			painted_building(a,r.size.x)
		"stairs", "ramp":
			var stair_rect=Rect2(a-Vector2(24,12),Vector2(r.size.x+48,d.y-a.y+24))
			draw_texture_rect(STAIRS,stair_rect,false)
		"branch":
			# A shallow timber garden deck shares its drawn and walkable bounds.
			draw_rect(Rect2(a,r.size),Color("483d32"))
			for y in range(0,int(r.size.y),8):
				draw_line(a+Vector2(0,y),a+Vector2(r.size.x,y),Color("927453"),2)
			draw_rect(Rect2(d,Vector2(r.size.x,8)),Color("302e2b"))
