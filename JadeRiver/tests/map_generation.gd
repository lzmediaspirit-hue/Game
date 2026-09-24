extends SceneTree
func _initialize(): call_deferred("run")
func run():
	var failures=0
	var cases=0
	for theme in MapGenerator.profiles():
		for seed_value in range(12):
			var data=MapGenerator.generate(theme,seed_value)
			var errors=MapValidator.validate(data)
			if JSON.stringify(data)!=JSON.stringify(MapGenerator.generate(theme,seed_value)): errors.append("Not deterministic")
			cases+=1
			if not errors.is_empty():
				failures+=1
				push_error(theme+" seed "+str(seed_value)+": "+str(errors))
	# A validator must reject broken layouts, not only accept the generator's output.
	var broken=MapGenerator.generate("forest",7)
	broken.surfaces[1].height=900
	cases+=1
	if MapValidator.validate(broken).is_empty(): failures+=1
	broken=MapGenerator.generate("road",7)
	broken.objects.append({"id":"blocked_road","art":"none","footprint":[100,790,100,130],"height":999})
	cases+=1
	if MapValidator.validate(broken).is_empty(): failures+=1
	broken=MapGenerator.generate("town",7)
	broken.surfaces.append(broken.surfaces[1].duplicate(true))
	cases+=1
	if MapValidator.validate(broken).is_empty(): failures+=1
	var custom=MapGenerator.generate("forest",19,{"tree_count":0,"rock_count":3,"background":"cave","ascent_kind":"rock_ledge","clouds":false,"ground":"slate"})
	cases+=1
	if not MapValidator.validate(custom).is_empty(): failures+=1
	print("GENERATED_MAPS: ",cases-failures,"/",cases)
	quit(1 if failures else 0)
