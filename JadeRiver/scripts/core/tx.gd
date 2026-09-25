class_name Tx
extends RefCounted
## Player-facing text (Part 7 · Strings): every line the player reads comes from
## data/strings/en.json by key. The UI strings are authored in tools/data/ui_strings.json.

static func t(key: String) -> String:
	return ContentDB.text(key)
