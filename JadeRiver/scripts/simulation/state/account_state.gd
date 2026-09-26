class_name AccountState
extends RefCounted
## S23 · Account-wide state shared by every character (Idleon model).

const VERSION := 3
const MAX_SLOTS := 12

var account_id := ""
var slots_unlocked := 1
var active_slot := 1
var characters: Dictionary = {}       # slot(str) -> summary {name, realm_key, idle_task, room}
var highest_realm := "mortal"
var currencies: Dictionary = {"silver_tael": 0, "spirit_stone": 0}
var storage: Dictionary = {"size": 0, "items": []}
var codex: Dictionary = {}            # entry -> true
var collection: Dictionary = {}       # enemy -> kills
var collection_pages_done: Dictionary = {}
var visited_rooms: Dictionary = {}
var paths_above: Dictionary = {}      # "room:surface" -> true (S43 "Paths Above" ledges stood on)
var wardrobe_unlocked: Dictionary = {} # "category:look" -> true: every look ever worn (S47 appearance override)
var teleports: Dictionary = {}
var recipes_seen: Dictionary = {}
var experiments: Array = []        # S44: every herb mix any character has tried, {key, herbs, result, by}, so none is repeated
var legacy: Dictionary = {}           # major realm -> true
var sect: Dictionary = {}             # your own sect (S25)
var mail: Array = []
var mail_next_id := 1
var settings: Dictionary = {}
var clock: Dictionary = {"last_active_utc": 0.0}
var unlocks: Dictionary = {}
var achievements: Dictionary = {"counters": {}, "done": {}}
var economy: Dictionary = {"rotation_day": -1, "rotation": {}, "buyback": [], "stock_bought": {}}
var resets: Dictionary = {"last_daily_day": -1, "last_weekly": -1}
var rooms: Dictionary = {"field_boss_timers": {}}
var rng_seed := 0
var created_utc := 0.0                 # S49: the calendar's day zero (seasons, world events); 0 on saves from before it
var calendar: Dictionary = {}          # S49 Calendar: {active: {event: k}, told: {event: k}, season, weather: {region: tag}, rifts: {k: true}}
var activity: Dictionary = {}          # S49 daily activity (Account): {day, points, by: {source: points}, claimed: [tier ids]}
var rng_state: Dictionary = {}
var welcome_pending: Dictionary = {}
var storehouse: Dictionary = {}        # S50 Keeping Post (V10): the account's bulk store, item -> count (Post authority)

static func default_settings() -> Dictionary:
	return {"music": 0.7, "sfx": 0.8, "ambience": 0.6, "ui": 0.7, "text_size": 1, "left_handed": false,
		"minimap": true, "minimap_monsters": true, "minimap_large": false, "damage_numbers": true,
		"screen_shake": true, "flashes": true, "haptics": true, "battery_saver": false, "language": "en",
		"notifications": {"offline_cap": true, "batch": true, "expedition": true, "defence": true, "pet": true},
		"first_run_done": false}

func _init() -> void:
	settings = default_settings()

func snapshot() -> Dictionary:
	return {"version": VERSION, "account_id": account_id, "slots_unlocked": slots_unlocked, "active_slot": active_slot,
		"characters": characters.duplicate(true), "highest_realm": highest_realm, "currencies": currencies.duplicate(),
		"storage": storage.duplicate(true), "codex": codex.keys(), "collection": collection.duplicate(),
		"collection_pages_done": collection_pages_done.keys(), "visited_rooms": visited_rooms.keys(), "paths_above": paths_above.keys(), "wardrobe_unlocked": wardrobe_unlocked.keys(),
		"teleports": teleports.keys(), "recipes_seen": recipes_seen.keys(), "experiments": experiments.duplicate(true), "legacy": legacy.keys(),
		"sect": sect.duplicate(true), "mail": mail.duplicate(true), "mail_next_id": mail_next_id,
		"settings": settings.duplicate(true), "clock": clock.duplicate(), "unlocks": unlocks.keys(),
		"achievements": achievements.duplicate(true), "economy": economy.duplicate(true), "resets": resets.duplicate(),
		"rooms": rooms.duplicate(true), "rng": {"seed": str(rng_seed), "streams": rng_state.get("streams", {})},
		"welcome_pending": welcome_pending.duplicate(true), "created_utc": created_utc, "calendar": calendar.duplicate(true),
		"activity": activity.duplicate(true), "storehouse": storehouse.duplicate()}

func restore(d: Dictionary) -> void:
	account_id = str(d.get("account_id", account_id))
	slots_unlocked = clampi(int(d.get("slots_unlocked", 1)), 1, MAX_SLOTS)
	active_slot = clampi(int(d.get("active_slot", 1)), 1, MAX_SLOTS)
	characters = d.get("characters", {}).duplicate(true)
	highest_realm = str(d.get("highest_realm", "mortal"))
	if ContentDB.realm(highest_realm).is_empty(): highest_realm = "mortal"
	currencies = {"silver_tael": 0, "spirit_stone": 0}
	for k in d.get("currencies", {}): currencies[k] = maxi(0, int(d.currencies[k]))
	storage = d.get("storage", storage).duplicate(true)
	codex = _to_set(d.get("codex", []))
	collection = d.get("collection", {}).duplicate()
	collection_pages_done = _to_set(d.get("collection_pages_done", []))
	visited_rooms = _to_set(d.get("visited_rooms", []))
	paths_above = _to_set(d.get("paths_above", []))
	wardrobe_unlocked = _to_set(d.get("wardrobe_unlocked", []))
	teleports = _to_set(d.get("teleports", []))
	recipes_seen = _to_set(d.get("recipes_seen", []))
	experiments = d.get("experiments", []).duplicate(true) if d.get("experiments", []) is Array else []
	legacy = _to_set(d.get("legacy", []))
	sect = d.get("sect", {}).duplicate(true)
	mail = d.get("mail", []).duplicate(true)
	mail_next_id = int(d.get("mail_next_id", mail.size() + 1))
	settings = default_settings()
	var s: Dictionary = d.get("settings", {})
	for k in s: settings[k] = s[k]
	clock = d.get("clock", clock).duplicate()
	unlocks = _to_set(d.get("unlocks", []))
	achievements = d.get("achievements", achievements).duplicate(true)
	economy = d.get("economy", economy).duplicate(true)
	resets = d.get("resets", resets).duplicate()
	rooms = d.get("rooms", rooms).duplicate(true)
	var r: Dictionary = d.get("rng", {})
	created_utc = float(d.get("created_utc", 0.0))
	calendar = d.get("calendar", {}).duplicate(true) if d.get("calendar") is Dictionary else {}
	activity = d.get("activity", {}).duplicate(true) if d.get("activity") is Dictionary else {}
	storehouse = {}
	var sh = d.get("storehouse", {})
	if sh is Dictionary:
		for k in sh:
			if int(sh[k]) > 0: storehouse[str(k)] = int(sh[k])
	rng_seed = int(str(r.get("seed", "0")))
	rng_state = r.duplicate(true)
	welcome_pending = d.get("welcome_pending", {}).duplicate(true)

static func _to_set(values) -> Dictionary:
	var out := {}
	if values is Array:
		for v in values: out[str(v)] = true
	elif values is Dictionary:
		for v in values: out[str(v)] = true
	return out
