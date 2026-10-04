extends Node
## Saves (Part 2 · Persistence, Part 5 · Save format v3). Writes through a
## repository interface and runs one migration per version step. Version 2
## (`user://disciples.json`, three appearance slots) migrates to v3 characters that
## skipped the Prologue: Bone Forging 2 in Stoneford, appearance kept, a v2 weapon
## turned into an inventory item, and a one-time welcome gift mailed.

const VERSION := 3
const V2_PATH := "user://disciples.json"

var repo := RepositoryLocal.new()
var last_error: Error = OK
var migrated_from_v2 := false

func use_folder(folder: String) -> void:
	repo = RepositoryLocal.new(folder)

func load_account() -> Dictionary:
	var data := repo.load_account()
	return migrate_account(data) if not data.is_empty() else {}

func save_account(data: Dictionary) -> Error:
	last_error = repo.save_account(data)
	return last_error

func load_character(slot: int) -> Dictionary:
	var data := repo.load_character(slot)
	return migrate_character(data) if not data.is_empty() else {}

func save_character(slot: int, data: Dictionary) -> Error:
	last_error = repo.save_character(slot, data)
	return last_error

func recovered_files() -> Array:
	return repo.last_recovered

# ------------------------------------------------------------------ export and import (S40)
const EXPORT_PREFIX := "jade_river_save_"
const EXPORT_FORMAT := "jade_river_export"

## Where exports go: the device's Documents folder when the game may write there (so a
## player can carry the file to a new phone), otherwise the game's own folder.
func export_dirs() -> Array:
	var out: Array = []
	var docs := OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)
	if docs != "": out.append(docs.path_join("JadeRiver") + "/")
	out.append("user://exports/")
	return out

## The account and every character in one file. Returns the path written, or "".
func export_bundle(slots: Array) -> String:
	var bundle := {"format": EXPORT_FORMAT, "version": VERSION, "exported_utc": Clock.now_utc(),
		"account": repo.load_account(), "characters": {}}
	for slot in slots: bundle.characters[str(slot)] = repo.load_character(int(slot))
	var stamp := Clock.file_stamp()
	for dir in export_dirs():
		if DirAccess.make_dir_recursive_absolute(dir) != OK and not DirAccess.dir_exists_absolute(dir): continue
		var path: String = str(dir) + EXPORT_PREFIX + stamp + ".json"
		var f := FileAccess.open(path, FileAccess.WRITE)
		if f == null: continue
		f.store_string(JSON.stringify(bundle))
		f.close()
		return path
	return ""

## Export files found in the export folders, newest first: [{path, name, modified}].
func list_exports() -> Array:
	var out: Array = []
	for dir in export_dirs():
		if not DirAccess.dir_exists_absolute(dir): continue
		for f in DirAccess.get_files_at(dir):
			if f.begins_with(EXPORT_PREFIX) and f.ends_with(".json"):
				out.append({"path": str(dir) + f, "name": f.trim_prefix(EXPORT_PREFIX).trim_suffix(".json"), "modified": FileAccess.get_modified_time(str(dir) + f)})
	out.sort_custom(func(a, b): return int(a.modified) > int(b.modified))
	return out

## Replace the saves with an export (the current files keep their .bak). The caller reboots.
func import_bundle(path: String) -> Error:
	var parser := JSON.new()
	if not FileAccess.file_exists(path) or parser.parse(FileAccess.get_file_as_string(path)) != OK: return ERR_PARSE_ERROR
	var b = parser.data
	if not (b is Dictionary) or str(b.get("format", "")) != EXPORT_FORMAT or not (b.get("account") is Dictionary) or (b.account as Dictionary).is_empty():
		return ERR_INVALID_DATA
	for slot_key in b.get("characters", {}):
		var cd = b.characters[slot_key]
		if cd is Dictionary and not cd.is_empty(): repo.save_character(int(slot_key), migrate_character(cd))
	return repo.save_account(migrate_account(b.account))

## Copy the newest engine log next to the exports, for a bug report. Returns the path or "".
func export_log() -> String:
	var logs := "user://logs/"
	if not DirAccess.dir_exists_absolute(logs): return ""
	var newest := ""
	var newest_t := 0
	for f in DirAccess.get_files_at(logs):
		var t := FileAccess.get_modified_time(logs + f)
		if t >= newest_t:
			newest_t = t
			newest = f
	if newest == "": return ""
	for dir in export_dirs():
		if DirAccess.make_dir_recursive_absolute(dir) != OK and not DirAccess.dir_exists_absolute(dir): continue
		var dest: String = str(dir) + "jade_river_log_" + newest.get_basename() + ".txt"
		if DirAccess.copy_absolute(logs + newest, dest) == OK: return dest
	return ""

func migrate_account(data: Dictionary) -> Dictionary:
	data["version"] = VERSION
	# S12a (one world): Settings' "Classic side view (new games)" is gone with the side view.
	if data.get("settings") is Dictionary: (data.settings as Dictionary).erase("classic_side_view")
	return data

func migrate_character(data: Dictionary) -> Dictionary:
	data["version"] = VERSION
	var minor := int(data.get("minor", 0))
	# P12 Might (minor 1): the maxima are rebuilt on load and grow by the Might of the Level, so the saved health grows
	# with them and the character keeps the same share of it. Qi and Soul take no Might. Runs once.
	if minor < 1:
		var cu = data.get("cultivator", {})
		var pools = data.get("pools", {})
		if cu is Dictionary and pools is Dictionary and pools.has("hp"):
			var lv := ProgressionRules.level_for(str(cu.get("realm_key", "mortal")), float(cu.get("progress", 0.0)))
			pools["hp"] = float(pools.hp) * StatRules.might_at(lv)
	# S12a, one world (minor 2): a character of the retired side view comes onto the height grid; every save loses its
	# `view`. Runs once.
	if minor < 2:
		if str(data.get("view", "")) != "topdown": migrate_side_view(data)
		data.erase("view")
	data["minor"] = GameCharacter.MINOR
	drop_unknown_recipes(data)
	return data

## The creator's own look, for a choice the top-down figure has no layer for (it draws every one parts.json names).
const LOOK_DEFAULTS := {"body": "light", "hair": "topknot", "shirt": "cardigan", "pants": "loose", "shoes": "boots"}

## S12a (decision 45, one world): a character made in the retired side view (`view` "" or none), onto the height grid,
## losing nothing:
## - its look keeps every choice and hair colour the top-down figure draws (TopdownFigure's items: every name and dye of
##   parts.json), a name it has none for taking the creator's default;
## - its gear and bag stay as they are (a garment's dye is the garment's own);
## - its saved spot and its shrine are placed in their rooms on the grid by the room events' rule
##   (TopdownRoom.grid_points: as far across the room and as deep as the spot stood in the side view's bounds, on the
##   nearest open cell reached on foot from the room's spawn); a shrine it knew stands where its room's layout places it.
static func migrate_side_view(data: Dictionary) -> void:
	var look = data.get("appearance", {})
	if look is Dictionary:
		var items: Dictionary = TopdownFigure.manifest().get("items", {})
		for cat in LOOK_DEFAULTS:
			if not (items.get(cat, {}) as Dictionary).has(str(look.get(cat, ""))): look[cat] = LOOK_DEFAULTS[cat]
		var colours: Dictionary = items.get("hair", {}).get(str(look.hair), {}).get("sheets", {})
		look["hair_color"] = clampi(int(look.get("hair_color", 0)), 0, maxi(0, colours.size() - 1))
	var pos = data.get("position", {})
	if pos is Dictionary:
		pos.erase("surface")
		var at := Vector2(float(pos.get("x", 0.0)), float(pos.get("y", 0.0)))
		var spot := grid_spot(str(pos.get("room", "")), at) if at != Vector2.ZERO else Vector2.ZERO
		pos["x"] = spot.x
		pos["y"] = spot.y
	var shrine = data.get("last_shrine", {})
	if shrine is Dictionary and not (shrine as Dictionary).is_empty():
		var room := str(shrine.get("room", ""))
		var at := Vector2(float(shrine.get("x", 0.0)), float(shrine.get("y", 0.0)))
		var id := str(shrine.get("object", ""))
		if id == "":
			# Saved before shrines kept their id: the room's shrine nearest the spot.
			var best := INF
			for o in ContentDB.room(room).get("objects", []):
				if str(o.get("type", "")) != "shrine": continue
				var d := at.distance_to(Vector2(float(o.at[0]), float(o.at[1])))
				if d < best:
					best = d
					id = str(o.id)
		var place: Dictionary = TopdownRoom.load_room(room).def.get("place", {}) if TopdownRoom.has_layout(room) else {}
		var p := TopdownRoom.cell_point(place[id]) if place.has(id) else grid_spot(room, at)
		data["last_shrine"] = {"room": room, "x": p.x, "y": p.y, "object": id}

## A side-view spot in `room_id` on its layout (TopdownRoom.grid_points from the room's spawn, over the room's side-view
## `bounds`); the layout's spawn (ZERO: enter_world takes the spawn) for a room with none.
static func grid_spot(room_id: String, side: Vector2) -> Vector2:
	if not TopdownRoom.has_layout(room_id): return Vector2.ZERO
	var grid := TopdownRoom.load_room(room_id)
	if grid.w == 0: return Vector2.ZERO
	var pts: Array = grid.grid_points([[side.x, side.y]], grid.spawn, ContentDB.room(room_id).get("bounds", []))
	return Vector2(float(pts[0][0]), float(pts[0][1]))

## A recipe renamed or removed from the data since the save was written (BUG-01, audit 45): its id leaves the known
## recipes, the pages held and the auto-refine queue (a batch of it is lost), with a warning, so nothing looks it up
## later. Skipped when no recipe loaded, so a broken data build never empties a save. Runs on every load.
func drop_unknown_recipes(data: Dictionary) -> void:
	var cr = data.get("crafting")
	if not (cr is Dictionary) or ContentDB.all("recipes").is_empty(): return
	var known := func(id) -> bool: return ContentDB.has_entry("recipes", str(id))
	var dropped := {}
	if cr.get("recipes") is Array:
		for id in cr.recipes:
			if not known.call(id): dropped[str(id)] = true
		cr["recipes"] = (cr.recipes as Array).filter(known)
	if cr.get("auto_queue") is Array:
		var queue: Array = []
		for b in cr.auto_queue:
			if b is Dictionary and known.call(b.get("recipe", "")): queue.append(b)
			else: dropped[str(b.get("recipe", "")) if b is Dictionary else str(b)] = true
		cr["auto_queue"] = queue
	if cr.get("recipe_fragments") is Dictionary:
		for id in (cr.recipe_fragments as Dictionary).keys():
			if not known.call(id):
				cr.recipe_fragments.erase(id)
				dropped[str(id)] = true
	if not dropped.is_empty():
		push_warning("Save %s: recipes no longer in the data dropped: %s" % [str(data.get("name", data.get("slot", "?"))), ", ".join(dropped.keys())])

## Read a v2 `disciples.json` (or its .bak) if no v3 account exists yet.
func read_v2(path := V2_PATH) -> Array:
	for p in [path, path + ".bak"]:
		if not FileAccess.file_exists(p): continue
		var parser := JSON.new()
		if parser.parse(FileAccess.get_file_as_string(p)) != OK: continue
		var d = parser.data
		if d is Dictionary and int(d.get("version", 0)) in [1, 2] and d.get("slots") is Array: return d.slots
	return []

## Convert v2 disciple slots into v3 character dictionaries (Part 5 · Migration from version 2).
func migrate_v2_slots(slots: Array) -> Array:
	var out: Array = []
	var slot_no := 1
	for s in slots:
		if not (s is Dictionary):
			continue
		var appearance := {"body": "light", "hair": str(s.get("hair", "topknot")), "hair_color": clampi(int(s.get("hair_color", 0)), 0, 5),
			"shirt": str(s.get("shirt", "cardigan")), "pants": str(s.get("pants", "loose")), "shoes": str(s.get("shoes", "boots"))}
		for cat in ["hair", "shirt", "pants", "shoes"]:
			if not ContentDB.parts.get(cat, {}).has(appearance[cat]): appearance[cat] = {"hair": "topknot", "shirt": "cardigan", "pants": "loose", "shoes": "boots"}[cat]
		var weapon := str(s.get("weapon", "none"))
		out.append({"version": VERSION, "slot": slot_no, "name": str(s.get("name", "Disciple")).left(24), "appearance": appearance,
			"migrated_v2": true, "v2_weapon": weapon})
		slot_no += 1
	migrated_from_v2 = not out.is_empty()
	return out
