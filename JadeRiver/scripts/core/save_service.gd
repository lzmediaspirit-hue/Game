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
