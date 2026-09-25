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
	var v := int(data.get("version", 0))
	if v == VERSION: return data
	data["version"] = VERSION
	return data

func migrate_character(data: Dictionary) -> Dictionary:
	var v := int(data.get("version", 0))
	if v == VERSION: return data
	data["version"] = VERSION
	return data

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
