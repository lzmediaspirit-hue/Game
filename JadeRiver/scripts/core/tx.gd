class_name Tx
extends RefCounted
## Player-facing text (Part 7 · Strings): every line the player reads comes from
## data/strings/en.json by key. The UI strings are authored in tools/data/ui_strings.json.

static func t(key: String) -> String:
	return ContentDB.text(key)

## A counted line: the "_one" form of `key` when `count` is 1 and the strings have one, else `key` itself; the caller
## formats it (I12: "Raise · 1 shards", "5 shard").
static func plural(key: String, count: int) -> String:
	return t(key + "_one") if count == 1 and ContentDB.strings.has(key + "_one") else t(key)
