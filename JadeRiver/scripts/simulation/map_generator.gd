class_name MapGenerator
extends RefCounted
## Deterministic spatial grammar: reserve circulation, parcel the rear edge,
## populate parcels, then construct reachable elevation routes.
const VERSION=6
const WIDTH=5400.0
const REAR=620.0
const GROUND_REAR=480.0
const FRONT=960.0
const LANE=Rect2(0,790,WIDTH,130)
static func profiles() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://data/map_themes.json"))
static func surface(id: String,rect: Array,height: float,kind: String,stratum="platform") -> Dictionary:
	return {"id":id,"rect":rect,"height":height,"kind":kind,"stratum":stratum,"open_edges":stratum!="ground"}
static func generate(theme: String,seed_value: int,override_profile: Dictionary={}) -> Dictionary:
	var catalog=profiles()
	assert(catalog.has(theme),"Unknown map theme: "+theme)
	var profile: Dictionary=catalog[theme].duplicate(true)
	profile.merge(override_profile,true)
	var rng=RandomNumberGenerator.new()
	rng.seed=seed_value
	var result={"revision":7,"generator_version":VERSION,"theme":theme,"seed":seed_value,"gates":RoomTravel.specs(WIDTH),
		"ground_material":profile.ground,"background":profile.background,"bounds":[0,480,WIDTH,FRONT-480],"spawn":[300,850],
		"surfaces":[surface("river_walk",[0,GROUND_REAR,WIDTH,FRONT-GROUND_REAR],0,"ground","ground")],
		"objects":[],"parcels":[],"routes":[],"reserved":[{"id":"main_road","rect":[0,790,WIDTH,130]}]}
	# The east garden/cavern ascent is reserved before placing buildings or trees.
	var building_count=clampi(int(profile.building_count),0,8)
	var previous_roof=""
	for i in building_count:
		var width=minf(float(profile.building_width),340)
		var x=350+i*(width+100)+rng.randi_range(0,12)
		var height=88.0 if i%3==0 else (164.0 if i%3==1 else 240.0)
		var id="building_%02d"%i
		result.parcels.append({"id":id,"use":"building","rect":[x,REAR,width,140]})
		var roof=surface(id,[x,REAR,width,140],height,"roof")
		roof.visual_variant=i%2
		result.surfaces.append(roof)
		var previous="river_walk"
		for level in int(height/88):
			if height-(level+1)*80<24: break
			var step_id=id+"_balcony_"+str(level)
			result.surfaces.append(surface(step_id,[x-82,REAR+70,82,64],(level+1)*80,"balcony"))
			result.routes.append({"from":previous,"to":step_id,"mode":"jump"})
			previous=step_id
		result.routes.append({"from":previous,"to":id,"mode":"jump"})
		if previous_roof!="":
			result.routes.append({"from":previous_roof,"to":id,"mode":"double_jump"})
			result.routes.append({"from":id,"to":previous_roof,"mode":"double_jump"})
		previous_roof=id
	# Trees occupy unbuilt back-edge parcels. Never scatter trunks into the road.
	var requested=clampi(int(profile.tree_count),0,20)
	var placed=0
	var tree_sites=[]
	for i in 24: tree_sites.append(200+((i*7)%24)*164.0)
	for parcel in result.parcels:
		tree_sites.append(float(parcel.rect[0])+float(parcel.rect[2])+96)
	for x in tree_sites:
		if placed>=requested: break
		var footprint=Rect2(x-24,REAR+30,48,34)
		var clear=true
		for parcel in result.parcels:
			var r=parcel.rect
			if footprint.grow(70).intersects(Rect2(r[0],r[1],r[2],r[3])): clear=false
		if not clear: continue
		result.objects.append(tree("tree_%02d"%placed,x,REAR+64,240+rng.randi_range(0,50)))
		result.parcels.append({"id":"tree_%02d"%placed,"use":"tree","rect":[x-24,REAR+30,48,34]})
		placed+=1
	# Ordinary tree artwork also exposes real, reachable branch surfaces.
	for item in result.objects:
		if not str(item.id).begins_with("tree_"): continue
		var previous="river_walk"
		for level in 3:
			var id=str(item.id)+"_branch_"+str(level)
			var branch_x=float(item.position[0])-70+(24 if level%2 else -64)
			result.surfaces.append(surface(id,[branch_x,GROUND_REAR+20,140,48],88+level*72,"tree_branch"))
			result.routes.append({"from":previous,"to":id,"mode":"jump"})
			previous=id
	var rocks=0
	for x in tree_sites:
		if rocks>=int(profile.rock_count): break
		var footprint=Rect2(x-32,REAR+40,64,38)
		var clear=true
		for parcel in result.parcels:
			var r=parcel.rect
			if footprint.grow(50).intersects(Rect2(r[0],r[1],r[2],r[3])): clear=false
		if not clear: continue
		var id="rock_%02d"%rocks
		result.objects.append({"id":id,"art":"props","cell":7,"position":[x,REAR+78],"size":[150,130],
			"front_y":REAR+78,"footprint":[x-32,REAR+40,64,38],"height":130,
			"occlusion":[x-75,REAR-52,150,130]})
		result.parcels.append({"id":id,"use":"rock","rect":[x-32,REAR+40,64,38]})
		rocks+=1
	if profile.climb:
		var kind=str(profile.ascent_kind)
		if kind=="tree_branch": result.objects.append(tree("ascent_tree",4540,REAR+74,590))
		var previous="river_walk"
		for i in 6:
			var x=4330.0+(i%2)*100
			var id="ascent_%02d"%i
			result.surfaces.append(surface(id,[x,GROUND_REAR+20,190,54],88.0*(i+1),kind))
			result.routes.append({"from":previous,"to":id,"mode":"jump"})
			previous=id
		if profile.clouds:
			for i in 5:
				var id="cloud_%02d"%i
				result.surfaces.append(surface(id,[4490+i*130,GROUND_REAR+20,220,80],616+i*64,"cloud"))
				result.routes.append({"from":previous,"to":id,"mode":"jump"})
				previous=id
	# A raised rear terrace adds ground depth without interrupting the main road.
	var stairs=surface("garden_stairs",[4980,690,200,100],64,"stairs","ground")
	stairs.rise=-64
	stairs.rise_axis="y"
	result.surfaces.append(stairs)
	result.surfaces.append(surface("garden_terrace",[4920,620,320,70],64,"ground","ground"))
	result.routes.append({"from":"river_walk","to":"garden_stairs","mode":"walk"})
	result.routes.append({"from":"garden_stairs","to":"garden_terrace","mode":"walk"})
	result.objects.append({"id":"garden_terrace_wall","art":"none","footprint":[4920,620,320,70],"height":64,"radius":0})
	result["profile"]=profile
	var masks=JSON.parse_string(FileAccess.get_file_as_string("res://data/surface_masks.json"))
	for spec in result.surfaces:
		var key=str(spec.kind)
		if key=="roof": key="roof_even" if int(spec.get("visual_variant",0))%2==0 else "roof_odd"
		if masks.has(key): spec.support_mask=masks[key]
	return result
static func tree(id: String,x: float,y: float,height: float) -> Dictionary:
	return {"id":id,"art":"props","cell":2,"position":[x,y],"size":[height*1.15,height],
		"front_y":y,"footprint":[x-24,y-34,48,34],"height":height,
		"occlusion":[x-height*0.575,y-height,height*1.15,height]}
