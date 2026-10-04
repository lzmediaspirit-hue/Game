extends RefCounted
## Decision 41's gate (the prototype's end) for its checks once every side-view room has a top-down layout: R8 and R9
## laid out the last of them, so no way from a room on the grid leads off it. The gate's checks (rules_tests' prototype
## suite, topdown_tutorial's end of the prototype) need such a way, so while they run they stand the last batch's rooms
## off the grid, as the world was before R9 laid them out (a test shortcut over TopdownRoom.has_layout's cache: the
## game still gates exactly the rooms with no layout). While a way off the grid is left, nothing is stood off.

## R9's rooms, the story's last: the Starsea's crossings and the Lantern Star Field's last zones (chapters 20 to 22).
const LAST_BATCH := ["ss_starsea_crossing", "ss_lantern_crossing",
	"wc_citadel_gate", "wc_wardens_hall", "wc_observatory", "wc_presence_court",
	"or_tumbling_stair", "or_orbit_garden", "or_golem_foundry", "or_inverted_hall",
	"ar_cinder_fields", "ar_ashborn_palisade", "ar_war_camp", "ar_kharns_pyre",
	"nd_nebula_verge", "nd_eel_currents", "nd_crab_grottoes", "nd_leviathans_maw",
	"lt_wick_gate", "lt_hall_of_burning_stars", "lt_flame_heart"]

## Whether some way from a room on the grid leads into a room of the world with no layout.
static func way_off_grid() -> bool:
	for rid in ContentDB.rooms:
		if not TopdownRoom.has_layout(str(rid)): continue
		for p in ContentDB.room(str(rid)).get("portals", []):
			var to := str(p.get("to", ""))
			if to != "" and not ContentDB.room(to).is_empty() and not TopdownRoom.has_layout(to): return true
	return false

## With no way off the grid left, the last batch's rooms stand off it; returns the rooms stood off, for `restore`.
static func stand_off() -> Array:
	if way_off_grid(): return []
	for r in LAST_BATCH: TopdownRoom._layouts[r] = false
	Game.quest._story_cache = {}
	return LAST_BATCH.duplicate()

## The rooms stood off are on the grid again (their layouts' files read again).
static func restore(rooms: Array) -> void:
	for r in rooms: TopdownRoom._layouts.erase(r)
	if not rooms.is_empty(): Game.quest._story_cache = {}
