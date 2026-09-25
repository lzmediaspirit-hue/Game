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
## S43 blocks: a solid box with a flat, lit top you can stand on. `art` holds the block kind.
const BLOCK_COLORS={"crate":["8a6236","a57a45","5c3f22"],"barrel":["6b4a2c","86603a","3f2a18"],"cart":["7d5a33","9b7443","4d3620"],
	"wall":["7c7d78","9a9b95","4f504c"],"rock":["6f7568","8d9384","474c43"],"fence":["80603a","a07c4c","52391f"],
	"stall":["9a3b2e","b8574a","5e231b"],"pillar":["9f2f2a","c24a3f","5f1a17"],"statue":["8b8f86","a9ada2","5a5d56"],
	"well":["71776f","8f958b","4a4f48"],"lantern":["a8342a","cf5a45","641d17"],"drum":["9c2c24","efe2c0","5a1814"],
	"stone_pillar":["868a84","a9ada4","55584f"],"slab":["7d776c","a49d8f","4a453d"],"rubble":["76705f","958d78","4b4637"],
	"log":["6e5134","8e6c46","433020"],"lily":["4f7d45","79a86a","2f4f2a"],"bamboo":["6f8a3a","a9c46a","4f6a28"],
	"stalagmite":["7a7f86","9ca2a8","4e5258"],"shelf":["6d4c2e","8c6840","43301c"]}
## The fair's great drum (S43 bounce): a red barrel with brass studs under a taut cream skin.
func _draw_drum():
	var r=surface.bounds
	var top=surface.base
	var cx=r.get_center().x
	var rx=r.size.x*0.5
	var ry=r.size.y*0.32
	var cy_top=r.get_center().y-top
	var cy_bottom=r.get_center().y
	var body=PackedVector2Array()
	for i in 17:
		var a=PI*float(i)/16.0
		body.append(Vector2(cx+cos(a)*rx,cy_bottom+sin(a)*ry))
	body.append(Vector2(cx-rx,cy_top))
	body.append(Vector2(cx+rx,cy_top))
	draw_colored_polygon(body,Color("9c2c24"))
	draw_rect(Rect2(cx-rx,cy_top,rx*0.35,top),Color("7a1f19"))
	draw_rect(Rect2(cx+rx*0.55,cy_top,rx*0.45,top),Color("b8473a"))
	for k in 2:
		var yy=cy_top+4.0 if k==0 else cy_bottom-2.0
		for i in 7:
			var a=PI*(0.1+0.8*float(i)/6.0)
			draw_circle(Vector2(cx-cos(a)*rx*0.96,yy+sin(a)*ry*0.9),2.0,Color("e0b84a"))
	var skin=PackedVector2Array()
	for i in 32:
		var a=TAU*float(i)/32.0
		skin.append(Vector2(cx+cos(a)*rx,cy_top+sin(a)*ry))
	draw_colored_polygon(skin,Color("efe2c0"))
	draw_polyline(skin+PackedVector2Array([skin[0]]),Color("7a1f19"),2.0)
	draw_arc(Vector2(cx,cy_top),rx*0.4,0,TAU,24,Color(0.8,0.2,0.16,0.6),2.0)
## Block kinds drawn with their prop's painted art, standing on the block's front edge (S43 kit).
const BLOCK_PROPS={"crate":"crate","barrel":"barrel","cart":"cart_broken","rock":"boulder_moss","boulder":"rock_large",
	"fence":"fence_wood","bamboo":"bamboo_fence","wall":"stone_wall_low","palisade":"stockade_wall","lantern":"stone_lantern",
	"well":"well","statue":"statue_guardian_lion","stall":"market_stall","pillar":"pressure_pillar","stump":"training_stump",
	"sack":"sack_pile","hay":"hay_bale","table":"table","log":"driftwood","lily":"lotus_pads","rubble":"rock_small",
	"stalagmite":"icicle_rock","shelf":"shelf","lifting":"lifting_stone"}
func _draw_block():
	if art=="drum":
		_draw_drum()
		return
	if surface.cracked:
		_draw_cracked()
		return
	var prop=str(BLOCK_PROPS.get(art,""))
	var e: Dictionary=SpriteCache.prop(prop) if prop!="" else {}
	if not e.is_empty() and surface.base<=120.0:
		var tex: Texture2D=SpriteCache.tex(str(e.get("file","")))
		if tex:
			var rb=surface.bounds
			var h=surface.base+rb.size.y*0.5
			var w=rb.size.x*1.08
			draw_texture_rect_region(tex,Rect2(rb.get_center().x-w*0.5,rb.end.y-h,w,h),Rect2(0,0,float(e.frame[0]),float(e.frame[1])),tint)
			# The walkable top gets a flat highlight (S43 visual language).
			draw_line(Vector2(rb.position.x+4,rb.end.y-surface.base),Vector2(rb.end.x-4,rb.end.y-surface.base),Color(1.0,0.95,0.75,0.55),2.0)
			return
	var r=surface.bounds
	var top=surface.base
	var cols: Array=BLOCK_COLORS.get(art if art!="" else "crate",BLOCK_COLORS.crate)
	var body=Color(cols[0])
	var lit=Color(cols[1])
	var dark=Color(cols[2])
	# Front face from the ground line up to the top's front edge.
	var front=Rect2(r.position.x,r.end.y-top,r.size.x,top)
	draw_rect(front,body)
	draw_rect(Rect2(front.position.x,front.end.y-4,front.size.x,4),dark)
	if art in ["crate","cart","fence","stall"]:
		for x in range(int(r.position.x)+12,int(r.end.x)-4,18):
			draw_line(Vector2(x,front.position.y+3),Vector2(x,front.end.y-3),dark,1.5)
	elif art in ["wall","rock","well","statue","pillar","slab","stone_pillar","rubble","stalagmite"]:
		for y in range(int(front.position.y)+10,int(front.end.y),14):
			draw_line(Vector2(r.position.x+2,y),Vector2(r.end.x-2,y),dark,1.0)
	# The walkable top: a flat highlight with a lit lip on its front edge (S43 visual language).
	var top_rect=Rect2(r.position.x,r.position.y-top,r.size.x,r.size.y)
	draw_rect(top_rect,lit)
	draw_rect(Rect2(top_rect.position.x,top_rect.end.y-3,top_rect.size.x,3),Color(1.0,0.93,0.72,0.9))
	draw_rect(Rect2(r.position.x,r.position.y-top,r.size.x,r.size.y+top),dark,false,2.0)
## A cracked floor slab (S43): a Plunge breaks it. Grey flagstones split by dark zig-zag cracks.
func _draw_cracked():
	var r=surface.bounds
	var top=surface.base
	var face=Rect2(r.position.x,r.end.y-top,r.size.x,top)
	draw_rect(face,Color("7d776c"))
	var top_rect=Rect2(r.position.x,r.position.y-top,r.size.x,r.size.y)
	draw_rect(top_rect,Color("a49d8f"))
	for y in range(int(top_rect.position.y)+16,int(top_rect.end.y),16):
		draw_line(Vector2(r.position.x,y),Vector2(r.end.x,y),Color("8a8376"),1)
	var c=top_rect.get_center()
	for k in 5:
		var ang=k*TAU/5.0+0.3
		var p0=c
		for step in 4:
			var p1=p0+Vector2(cos(ang),sin(ang)*0.55)*(10.0+step*3.0)+Vector2(((step+k)%3-1)*4.0,0)
			draw_line(p0,p1,Color("2e2a24"),2.0 if step<2 else 1.0)
			p0=p1
	draw_rect(Rect2(top_rect.position.x,top_rect.end.y-3,top_rect.size.x,3),Color(1.0,0.93,0.72,0.9))
	draw_rect(Rect2(r.position.x,r.position.y-top,r.size.x,r.size.y+top),Color("4a453d"),false,2.0)
func _draw():
	if surface.disabled: return   # crumbled or broken (S43); it returns when the floor does
	if surface.kind=="block":
		_draw_block()
		return
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
	if surface.kind=="raft":
		# S43 mover: a bamboo raft, poles lashed across two cross-bars, riding low on the water.
		draw_rect(Rect2(a,r.size),Color("6f5d2e"))
		for y in range(0,int(r.size.y),7):
			draw_line(a+Vector2(2,y+3),a+Vector2(r.size.x-2,y+3),Color("c2ab6a"),3)
		for x in [10.0,r.size.x-14]:
			draw_line(a+Vector2(x,0),a+Vector2(x,r.size.y),Color("4a3a1c"),3)
		draw_rect(Rect2(d,Vector2(r.size.x,maxf(4.0,surface.base))),Color("4a3a1c"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.9),2)
		return
	if surface.kind=="pole":
		# Bamboo (S43 kit): a single stalk under a narrow plum-blossom pole top, or a platform of lashed bamboo
		# slats on two stalks. Stalks are green with pale node rings; slats run across, yellowing at the ends.
		var foot=r.end.y
		var head=d.y
		var stalks=[r.get_center().x] if r.size.x<70 else [r.position.x+16,r.end.x-20]
		for cx in stalks:
			draw_rect(Rect2(cx-5,head,10,foot-head),Color("6f8a3a"))
			draw_rect(Rect2(cx-5,head,3,foot-head),Color("a9c46a"))
			draw_rect(Rect2(cx+3,head,2,foot-head),Color("4f6a28"))
			for y in range(int(head)+24,int(foot),28): draw_line(Vector2(cx-6,y),Vector2(cx+6,y),Color("d8e6a4"),2)
		var row=0
		for y in range(0,int(r.size.y),7):
			draw_rect(Rect2(a+Vector2(0,y),Vector2(r.size.x,6)),Color("b9a35a") if row%2==0 else Color("a48c46"))
			draw_line(a+Vector2(0,y+6),a+Vector2(r.size.x,y+6),Color("5e4a22"),1)
			for x in range(int(18+(row%3)*9),int(r.size.x)-6,34): draw_line(a+Vector2(x,y),a+Vector2(x,y+6),Color("7d6a33"),1)
			row+=1
		for cx in stalks:
			var lx=cx-r.position.x
			draw_line(a+Vector2(lx-7,0),a+Vector2(lx+7,r.size.y),Color("3e3018"),2)
			draw_line(a+Vector2(lx+7,0),a+Vector2(lx-7,r.size.y),Color("3e3018"),2)
		draw_rect(Rect2(d,Vector2(r.size.x,5)),Color("7b6a2e"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.85),2)
		return
	if surface.kind in ["chimney","stone_pillar"]:
		# A brick chimney stack or a broken stone pillar from the ground to its top; the top is a small sooty
		# (or mossy) cap. Both are later ledges: their faces are what Wall-Step and the double jump test.
		var brick=surface.kind=="chimney"
		var face=Color("8a4f3a") if brick else Color("8d9290")
		var mortar=Color("5a3326") if brick else Color("5f6563")
		draw_rect(Rect2(d,Vector2(r.size.x,surface.base)),face)
		var row=0
		for y in range(0,int(surface.base),10 if brick else 22):
			draw_line(d+Vector2(0,y),d+Vector2(r.size.x,y),mortar,1)
			var off=(10.0 if brick else 20.0)*float(row%2)
			for x in range(int(off),int(r.size.x),20 if brick else 40):
				draw_line(d+Vector2(x,y),d+Vector2(x,y+(10 if brick else 22)),mortar,1)
			row+=1
		draw_rect(Rect2(d,Vector2(4,surface.base)),Color(1,1,1,0.12))
		draw_rect(Rect2(a,r.size),Color("3b2a24") if brick else Color("6f7a64"))
		draw_rect(Rect2(a,Vector2(r.size.x,4)),Color("a36a4c") if brick else Color("9fb08a"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.8),2)
		return
	if surface.kind=="walltop":
		# A town wall's walkway: dressed stone face down to the street, flagstones on top, crenels along the back.
		draw_rect(Rect2(d,Vector2(r.size.x,surface.base)),Color("9a958a"))
		var course=0
		for y in range(0,int(surface.base),18):
			draw_line(d+Vector2(0,y),d+Vector2(r.size.x,y),Color("6c675e"),1)
			for x in range(18*(course%2),int(r.size.x),36):
				draw_line(d+Vector2(x,y),d+Vector2(x,y+18),Color("6c675e"),1)
			course+=1
		draw_rect(Rect2(a,r.size),Color("b7b1a4"))
		for y in range(0,int(r.size.y),14):
			draw_line(a+Vector2(0,y),a+Vector2(r.size.x,y),Color("8f897c"),1)
		for x in range(0,int(r.size.x)-10,36):
			draw_rect(Rect2(a+Vector2(x,-22),Vector2(20,22)),Color("a39d90"))
			draw_rect(Rect2(a+Vector2(x,-22),Vector2(20,3)),Color("cfc9bb"))
		draw_rect(Rect2(d,Vector2(r.size.x,6)),Color("5f5a52"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.85),2)
		return
	if surface.kind in ["bridge","rope_bridge"]:
		# A rope bridge: planks on two ropes, railing ropes sagging above, posts at each end.
		var sag=6.0
		for x in range(0,int(r.size.x),14):
			var k=float(x)/maxf(1.0,r.size.x)
			var dy=sin(k*PI)*sag
			draw_rect(Rect2(a+Vector2(x+1,dy),Vector2(11,r.size.y)),Color("7a5a36"))
			draw_line(a+Vector2(x+1,dy+1),a+Vector2(x+12,dy+1),Color("b08a5a"),1.5)
		for side in [0.0,r.size.y]:
			var pts=PackedVector2Array()
			for i in 17:
				var k=float(i)/16.0
				pts.append(a+Vector2(r.size.x*k,side-26+sin(k*PI)*(sag+8)))
			draw_polyline(pts,Color("5a4630"),2.0)
		for x in [0.0,r.size.x-6]:
			draw_rect(Rect2(a+Vector2(x,-30),Vector2(6,r.size.y+30+surface.base)),Color("3d2c1e"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.8),2)
		return
	if surface.kind in ["stilt","scaffold"]:
		# Stilt decks and scaffolds: weathered planks laid across bamboo-lashed posts; scaffolds brace their
		# posts with crossed timbers. A fascia board and a lit lip mark the walkable front.
		var posts=[6.0,r.size.x*0.5-4,r.size.x-12]
		for x in posts:
			draw_rect(Rect2(d+Vector2(x,0),Vector2(7,surface.base)),Color("4a3526"))
			draw_line(d+Vector2(x+1,0),d+Vector2(x+1,surface.base),Color("8c6a48"),1.5)
			for k in range(1,int(surface.base/40.0)+1):
				draw_line(d+Vector2(x-1,k*40-6),d+Vector2(x+8,k*40-2),Color("c2a364"),2)   # rope lashing
		if surface.kind=="scaffold":
			for i in 2:
				var xa=posts[i]+3
				var xb=posts[i+1]+3
				draw_line(d+Vector2(xa,0),d+Vector2(xb,surface.base),Color("6e5038"),2)
				draw_line(d+Vector2(xb,0),d+Vector2(xa,surface.base),Color("6e5038"),2)
		# The top face: boards running across, alternating tone, dark seams between them.
		var row=0
		for y in range(0,int(r.size.y),9):
			var tone=Color("8a6a44") if row%2==0 else Color("7a5c3a")
			draw_rect(Rect2(a+Vector2(0,y),Vector2(r.size.x,8)),tone)
			draw_line(a+Vector2(0,y+8),a+Vector2(r.size.x,y+8),Color("3e2c1c"),1)
			var knot=float((row*37)%int(maxf(1.0,r.size.x-20)))
			draw_line(a+Vector2(knot+6,y+3),a+Vector2(knot+14,y+3),Color("5e4428"),1)
			row+=1
		draw_rect(Rect2(d,Vector2(r.size.x,8)),Color("5a4130"))    # fascia board
		draw_line(d+Vector2(0,8),d+Vector2(r.size.x,8),Color("2e2016"),1)
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.85),2)
		return
	if surface.kind=="awning":
		# A stall awning (S43 kit): striped cloth on two thin poles, a scalloped front edge.
		for x in [4.0,r.size.x-8]:
			draw_rect(Rect2(d+Vector2(x,0),Vector2(4,surface.base)),Color("5a3a22"))
		var stripe=int(maxf(12.0,r.size.x/8.0))
		for i in range(0,int(r.size.x),stripe):
			var col=Color("b8473a") if (i/stripe)%2==0 else Color("efe2c0")
			draw_rect(Rect2(a+Vector2(i,0),Vector2(minf(stripe,r.size.x-i),r.size.y)),col)
		draw_line(a,a+Vector2(r.size.x,0),Color("7a1f19"),2)
		for i in range(0,int(r.size.x),stripe):
			draw_arc(d+Vector2(i+stripe*0.5,0),stripe*0.5,0.0,PI,8,Color("7a1f19"),2.0)
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.8),2)
		return
	if surface.kind=="boards":
		# Rotten boards on two posts: a walkable lip, gaps between the planks (S43 crumble).
		for x in [6.0,r.size.x*0.5-3,r.size.x-12]:
			draw_rect(Rect2(d+Vector2(x,0),Vector2(6,surface.base)),Color("3d2c1e"))
			draw_line(d+Vector2(x+1,0),d+Vector2(x+1,surface.base),Color("6b5034"),1)
		draw_rect(Rect2(a,r.size),Color("2e2218"))
		var row=0
		for y in range(0,int(r.size.y)-4,9):
			row+=1
			# Old planks laid across the way, a few split or missing: it will not hold for long.
			var sag=sin(float(row)*1.7)*1.5
			for seg in [[0.0,0.46],[0.52,1.0]] if row%3==1 else [[0.0,1.0]]:
				var x0=r.size.x*float(seg[0])+2
				var x1=r.size.x*float(seg[1])-2
				draw_rect(Rect2(a+Vector2(x0,y+sag),Vector2(x1-x0,7)),Color("6b5034"))
				draw_line(a+Vector2(x0,y+sag),a+Vector2(x1,y+sag),Color("9c7a52"),1.5)
		draw_rect(Rect2(d,Vector2(r.size.x,5)),Color("3a2a1e"))
		draw_line(d,d+Vector2(r.size.x,0),Color(1.0,0.93,0.72,0.8),2)
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
		"cloud", "tree_branch", "rock_ledge", "canopy", "ledge", "causeway":
			var row_y=70 if surface.kind in ["tree_branch","canopy"] else (400 if surface.kind=="cloud" else 700)
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
