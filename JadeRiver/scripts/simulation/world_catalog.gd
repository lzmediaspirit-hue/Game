class_name WorldCatalog
extends RefCounted
## Region identity is stable across saves and independent of view nodes.
const REGIONS=["village","road","forest","cave","mountain","town"]
static func zone_id(theme: String,seed_value: int) -> String:
	return "%s:%d:v%d"%[theme,seed_value,MapGenerator.VERSION]
static func neighbour(theme: String,direction: int) -> String:
	var index=REGIONS.find(theme)
	if index<0: return "village"
	return REGIONS[posmod(index+direction,REGIONS.size())]
static func valid_theme(theme: String) -> bool:
	return MapGenerator.profiles().has(theme)
