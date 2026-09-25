extends Node2D
## Painted atlas regions are projected onto the same bounds used by simulation.
var surface: WalkSurface
var ground_material="stone"
var generated=false
var art=""            # building prop id (data/prop_art.json) or painted atlas key
var tint=Color.WHITE
const PLATFORMS=preload("res://art/environment/platforms-v6.png")
const GROUND=preload("res://art/environment/ground-v6.png")
const GROUND_EXTRA=preload("res://art/environment/ground-extra.png")   # rock, snow and sand (tools/art/bake_ground.py)
const EXTRA_CELLS={"rock":0,"snow":1,"sand":2}
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
	if generated and EXTRA_CELLS.has(ground_material):
		texture=GROUND_EXTRA
		var cell_x=Vector2(GROUND_EXTRA.get_size().y,GROUND_EXTRA.get_size().y)
		texture_region=Rect2(Vector2(cell_x.x*EXTRA_CELLS[ground_material],0),cell_x)
	elif generated:
		texture=GROUND
		var quadrants={"earth":Vector2(0,0),"moss":Vector2(1,0),"slate":Vector2(0,1),"stone":Vector2(1,1)}
		var cell=GROUND.get_size()/2
		texture_region=Rect2(quadrants.get(ground_material,Vector2.ONE)*cell,cell)
	for row in int(ceil(rect.size.y/tile.y)):
		for col in int(ceil(rect.size.x/tile.x)):
			var p=rect.position+Vector2(col,row)*tile
			var size=(rect.end-p).min(tile)
			var src=Rect2(texture_region.position,texture_region.size*size/tile)
			# Painted cells mirror at their seams; the baked rock and snow cells tile directly.
			var mirror=not (generated and EXTRA_CELLS.has(ground_material))
			if mirror and col%2: src.position.x=texture_region.end.x-src.size.x
			if mirror and row%2: src.position.y=texture_region.end.y-src.size.y
			var dest=Rect2(p,size)
			if mirror and col%2: dest.size.x=-dest.size.x
			if mirror and row%2: dest.size.y=-dest.size.y
			draw_texture_rect_region(texture,dest,src,tint)
const ATLAS_BUILDINGS={"gate":Rect2(0,0,720,465),"hall":Rect2(739,70,797,390),"two_storey":Rect2(0,475,900,549),"tower":Rect2(1040,475,365,549)}
func building_source() -> Rect2:
	if ATLAS_BUILDINGS.has(art): return ATLAS_BUILDINGS[art]
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
	if surface.kind=="ladder":
		# Bamboo ladder leaning on the facade: foot at the ramp's front edge, top at the roof line.
		var foot_y=r.end.y
		var top=pt(r.position.x,r.position.y).y
		for rail in [r.position.x+6,r.end.x-10]:
			draw_rect(Rect2(rail,top,4,foot_y-top),Color("5d4a2a"))
			draw_rect(Rect2(rail,top,2,foot_y-top),Color("a88a4f"))
		for y in range(int(top)+6,int(foot_y),14):
			draw_rect(Rect2(r.position.x+8,y,r.size.x-16,4),Color("4a3a22"))
			draw_rect(Rect2(r.position.x+8,y,r.size.x-16,2),Color("c2a364"))
		return
	if surface.kind in ["branch","rock_ledge"] and art!="" and not SpriteCache.prop(art).is_empty():
		# Prop-art platforms (driftwood, ledges): posts down to the ground, then the prop
		# stretched across the walkable top face.
		var e2: Dictionary=SpriteCache.prop(art)
		var tex2: Texture2D=SpriteCache.tex(str(e2.get("file","")))
		if tex2:
			var top_left=pt(r.position.x,r.position.y)
			var ground_y=r.end.y
			for px in [r.position.x+14,r.end.x-22]:
				draw_rect(Rect2(px,top_left.y+r.size.y-6,8,ground_y-(top_left.y+r.size.y-6)),Color("3d2c1e"))
				draw_rect(Rect2(px,top_left.y+r.size.y-6,3,ground_y-(top_left.y+r.size.y-6)),Color("6b5034"))
			var fw2=float(e2.frame[0])
			var fh2=float(e2.frame[1])
			draw_texture_rect_region(tex2,Rect2(top_left-Vector2(0,fh2*0.35),Vector2(r.size.x,r.size.y+fh2*0.35)),Rect2(0,0,fw2,fh2),tint)
			return
	if surface.kind=="roof" and art!="" and not ATLAS_BUILDINGS.has(art):
		# Building props: roof art on the walkable top face, facade below it.
		var e: Dictionary=SpriteCache.prop(art)
		var texture: Texture2D=SpriteCache.tex(str(e.get("file","")))
		if texture:
			var size=Vector2(float(e.frame[0]),float(e.frame[1]))
			draw_texture_rect_region(texture,Rect2(Vector2(r.position.x+(r.size.x-size.x)*0.5,r.end.y-surface.base-r.size.y),size),Rect2(Vector2.ZERO,size),tint)
			return
	if surface.kind=="ground" and ground_material in ["wood","floor_stone","floor_earth","sand_wood"]:
		var tile={"wood":"floor_wood","floor_stone":"floor_stone","floor_earth":"floor_earth","sand_wood":"floor_wood"}[ground_material]
		SpriteCache.draw_tiled(self,tile,Rect2(a,r.size+Vector2(0,500 if surface.base==0 else 0)),0.0,tint)
		if surface.base>0:
			draw_rect(Rect2(d,Vector2(r.size.x,surface.base)),Color("3b2c22"))
			draw_line(d,d+Vector2(r.size.x,0),Color("c9a46a"),2)
		return
	if surface.kind in ["dock","deck"]:
		draw_rect(Rect2(a,r.size),Color("5a4130"))
		for y in range(0,int(r.size.y),12):
			draw_line(a+Vector2(0,y),a+Vector2(r.size.x,y),Color("8c6a48"),2)
			draw_line(a+Vector2(0,y+6),a+Vector2(r.size.x,y+6),Color("6e5038"),2)
		for x in range(0,int(r.size.x),64):
			draw_rect(Rect2(d+Vector2(x+4,0),Vector2(8,maxf(surface.base,14))),Color("3a2a1e"))
		draw_rect(Rect2(d,Vector2(r.size.x,6)),Color("3a2a1e"))
		return
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
			paving(Rect2(ground_origin,extent),tint*self.tint)
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
