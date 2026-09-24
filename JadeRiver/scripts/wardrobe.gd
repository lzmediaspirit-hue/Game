extends Node
## Version 2 stores appearance and per-slot world progress; version 1 migrates on read.
var parts: Dictionary={}
var slots: Array=[null,null,null]
var textures: Dictionary={}
var save_path="user://disciples.json"
const CATEGORIES=["hair","shirt","pants","shoes","weapon"]
func _ready():
	parts=JSON.parse_string(FileAccess.get_file_as_string("res://data/parts.json"))
	load_slots()
func defaults() -> Dictionary:
	return {"name":"New Disciple","body":"light","hair":"topknot","hair_color":0,"shirt":"cardigan","pants":"loose","shoes":"boots","weapon":"sword","sect":"Jade"}
func validate(value: Dictionary) -> Dictionary:
	var result=defaults()
	for key in result:
		match key:
			"name": result[key]=str(value.get(key,result[key])).strip_edges().left(24)
			"hair_color": result[key]=clampi(int(value.get(key,0)),0,5) if value.get(key,0) is float or value.get(key,0) is int else 0
			"sect": result[key]=value.get(key,"Jade") if value.get(key) in ["Jade","Cloud"] else "Jade"
			_:
				if parts.get(key,{}).has(value.get(key,"")): result[key]=value[key]
	if result.name.is_empty(): result.name="New Disciple"
	if value.get("progress") is Dictionary:
		var state=value.progress
		var clean: Dictionary={}
		for key in ["x","y","hp","qi","facing","skill_page","map_revision","map_seed","generator_version"]:
			var n=state.get(key)
			if (n is float or n is int) and is_finite(float(n)): clean[key]=n
		clean.surface=str(state.get("surface",""))
		clean.map_theme=str(state.get("map_theme",""))
		result.progress=clean
	return result
func read_save(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var parser=JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path))!=OK: return {}
	var data=parser.data
	if data is Dictionary and (data.get("version")==1 or data.get("version")==2) and data.get("slots") is Array: return data
	return {}
func load_slots():
	var data=read_save(save_path)
	if data.is_empty(): data=read_save(save_path+".bak")
	if data.is_empty(): return
	slots=[null,null,null]
	for i in mini(3,data.slots.size()):
		if data.slots[i] is Dictionary: slots[i]=validate(data.slots[i])
func save_slot(index: int,value: Dictionary) -> Error:
	if index<0 or index>=3: return ERR_INVALID_PARAMETER
	var next=slots.duplicate(true)
	next[index]=validate(value)
	var file=FileAccess.open(save_path+".tmp",FileAccess.WRITE)
	if file==null: return FileAccess.get_open_error()
	file.store_string(JSON.stringify({"version":2,"slots":next},"\t"))
	file.flush()
	var result=file.get_error()
	file.close()
	if result!=OK: return result
	if not read_save(save_path).is_empty():
		result=DirAccess.copy_absolute(save_path,save_path+".bak")
		if result!=OK: return result
	result=DirAccess.rename_absolute(save_path+".tmp",save_path)
	if result==OK: slots=next
	return result
func texture(path: String) -> Texture2D:
	path=path.replace("art_v12/","res://art/")
	if not textures.has(path): textures[path]=load(path)
	return textures[path]
func attack_for(outfit: Dictionary) -> String:
	return parts._attack_by_weapon.get(outfit.get("weapon","none"),"punch")
