class_name PlaceRules
extends RefCounted
## Decision 43, systems as places (docs/redesign/systems_as_places.md, "As built"): the places in the world where the
## game's systems live (data/places.json, built by tools/data/places.py). A place is an object of a room on the height
## grid: the context button's verb at it opens its page (WorldAuthority.interact), the world draws it and its state
## (TopdownPlaceArt), the world map and the minimap mark it, and the Menu says where a system lives until it may be
## opened from anywhere.
##
## Rules (a row's `rule`): "both" (the place and the Menu), "earned" (the first uses at the place; `remote.after`, and a
## first use at a place of the system with `remote.first_use`, open it from anywhere), "place" (only there).
## A first use sets the character's flag "place_used:<system>" (note_use).

const USED := "place_used:"
const SEEN := "paper_seen:"

static var _by_room := {}
static var _by_system := {}
static var _loaded_rows := -1

static func _index() -> void:
	var rows: Array = ContentDB.all("places")
	if rows.size() == _loaded_rows and not _by_room.is_empty(): return
	_by_room = {}
	_by_system = {}
	for r in rows:
		var room := str(r.get("room", ""))
		var sys := str(r.get("system", ""))
		if not _by_room.has(room): _by_room[room] = []
		_by_room[room].append(r)
		if not _by_system.has(sys): _by_system[sys] = []
		_by_system[sys].append(r)
	_loaded_rows = rows.size()

static func all() -> Array:
	return ContentDB.all("places")

static func get_place(id: String) -> Dictionary:
	return ContentDB.entry("places", id)

## The places of a room, in the table's order.
static func of_room(room_id: String) -> Array:
	_index()
	return _by_room.get(room_id, [])

## The places of a system (an unlock id: "storage", "mail", "herb_garden"...).
static func of_system(system: String) -> Array:
	_index()
	return _by_system.get(system, [])

## The place an object of a room is, or {}.
static func at_object(room_id: String, object_id: String) -> Dictionary:
	for r in of_room(room_id):
		if str(r.object) == object_id: return r
	return {}

## What kind of place each kind is: {name, icon, verb}; and the order the map's card lists them in.
static func kinds() -> Dictionary:
	return ContentDB.config("places").get("kinds", {})

static func kind_order() -> Array:
	return ContentDB.config("places").get("kind_order", [])

static func kind_name(kind: String) -> String:
	return str(kinds().get(kind, {}).get("name", kind))

## The objects this table adds to a room (a letter box, a meditation mat), each as its room definition has it: its id,
## type and label, where it stands (`at`, the cell's centre in world units) and what it needs.
static func added_objects(room_id: String) -> Array:
	var out: Array = []
	for r in of_room(room_id):
		if not r.get("added", false): continue
		var o: Dictionary = (r.get("object_def", {}) as Dictionary).duplicate(true)
		var cell: Array = r.get("cell", [0, 0])
		o.at = [(float(cell[0]) + 0.5) * TopdownRoom.TILE, (float(cell[1]) + 0.5) * TopdownRoom.TILE]
		out.append(o)
	return out

## The cells the places of a room block (a stall's counter, the Storehouse's shed): [Rect2i].
static func solids(room_id: String) -> Array:
	var out: Array = []
	for r in of_room(room_id):
		for s in r.get("solid", []): out.append(Rect2i(int(s[0]), int(s[1]), int(s[2]), int(s[3])))
	return out

# ------------------------------------------------------------------ the rules
static func used(c, system: String) -> bool:
	return c != null and c.quests.has_flag(USED + system)

## A use at a place of the system: the first one is what earned remote access waits for (with `remote.after`).
static func note_use(game, c, system: String) -> void:
	if c == null or system == "" or used(c, system) or of_system(system).is_empty(): return
	game.quest.apply_flag(c.id, USED + system)

static func rule(system: String) -> String:
	var rows := of_system(system)
	return str(rows[0].get("rule", "both")) if not rows.is_empty() else "both"

## May the system be opened away from its places? "both" always; "place" never; "earned" once its remote rule holds.
static func remote_open(c, system: String) -> bool:
	var rows := of_system(system)
	if rows.is_empty() or c == null: return true
	match str(rows[0].get("rule", "both")):
		"both": return true
		"place": return false
	var remote: Dictionary = rows[0].get("remote", {})
	if bool(remote.get("first_use", false)) and not used(c, system): return false
	return RequirementRules.passes(remote.get("after", {}), {"char": c, "account": Game.account, "room": {}})

## True while the system is open to the character but lives at its place: the Menu says where and offers the walk.
static func bound(c, system: String) -> bool:
	return c != null and str(rule(system)) == "earned" and Unlocks.is_unlocked(c.id, system) and not remote_open(c, system)

## The system a Menu tablet stands for, when one of its places names the tablet ("" for none).
static func menu_system(menu_id: String) -> String:
	for r in all():
		if str(r.get("menu", "")) == menu_id: return str(r.system)
	return ""

## The place a walk to the system leads to: of its places, the character's own sect's (or a place of no sect), then
## the home one, then the nearest by the ways open to it (the room it stands in first).
static func home(c, system: String) -> Dictionary:
	var rows := of_system(system)
	if rows.is_empty(): return {}
	var mine := str(c.training_sect.get("id", "")) if c != null else ""
	var best := {}
	var best_score := INF
	var here := str(c.position.get("room", "")) if c != null else ""
	for r in rows:
		var sect := str(r.get("sect", ""))
		if sect != "" and sect != mine and mine != "": continue
		var score := 0.0
		if sect != "" and mine == "": score += 1000.0      # a sect's place, before a sect is chosen
		if not r.get("home", false): score += 100.0
		if str(r.room) != here and c != null and Game.world != null:
			var way: Array = Game.world.route(c, here, str(r.room)) if here != "" else []
			score += way.size() if not way.is_empty() else 500.0
		if score < best_score:
			best_score = score
			best = r
	return best

## "At the Storehouse" for the system's place a walk leads to ("" when it has none).
static func where(c, system: String) -> String:
	return str(home(c, system).get("where", ""))

## Where a place's user stands (its `stand` cell's centre, world units).
static func stand_point(r: Dictionary) -> Vector2:
	var s: Array = r.get("stand", r.get("cell", [0, 0]))
	return Vector2((float(s[0]) + 0.5) * TopdownRoom.TILE, (float(s[1]) + 0.5) * TopdownRoom.TILE)

static func point(r: Dictionary) -> Vector2:
	var s: Array = r.get("at", [0, 0])
	return Vector2(float(s[0]), float(s[1]))

# ------------------------------------------------------------------ what a place shows
## The notice board's papers: the bounties posted and not taken, the requests of people nearby and today's missions,
## each [id]; none before the board opens to the character.
static func papers(c) -> Array:
	var out: Array = []
	if c == null or not Unlocks.is_unlocked(c.id, "notice_board"): return out
	var mine: Array = c.relations.bounties.map(func(v): return str(v.get("id", "")) if v is Dictionary else str(v))
	for b in Game.relations.fcfg().get("bounties", []):
		if not str(b.get("id", "")) in mine and ProgressionRules.at_least(c.cultivator.realm_key, str(b.get("realm", ""))): out.append("b:" + str(b.id))
	for qid in c.quests.offered:
		var d := ContentDB.entry("quests", str(qid))
		if not d.is_empty() and str(d.get("kind", "")) == "side" and Game.quest.can_offer(c, d): out.append("q:" + str(qid))
	for qid in c.quests.daily: out.append("d:" + str(qid))
	return out

## A paper the character has not read at a board yet.
static func new_papers(c) -> int:
	var n := 0
	for p in papers(c):
		if not c.quests.has_flag(SEEN + str(p)): n += 1
	return n

## Reading the board marks every paper on it read (the gold "!" goes).
static func read_board(game, c) -> void:
	for p in papers(c):
		if not c.quests.has_flag(SEEN + str(p)): game.quest.apply_flag(c.id, SEEN + str(p))

## What a place shows now, for the world's sight and the map's card: {state, n, of, new, on, text}.
static func state(c, r: Dictionary) -> Dictionary:
	var st := str(r.get("state", ""))
	var out := {"state": st, "n": 0, "of": 0, "new": 0, "on": false, "text": ""}
	if c == null: return out
	match st:
		"papers":
			var ps := papers(c)
			out.n = ps.size()
			out.new = new_papers(c)
			out.on = out.n > 0
			out.text = Tx.t("ui.place.state_papers_none") if out.n == 0 else Tx.plural("ui.place.state_papers", int(out.n)) % int(out.n)
		"ribbon":
			out.n = Game.mail.unread(c) if Unlocks.is_unlocked(c.id, "mail") else 0
			out.on = out.n > 0
			out.text = Tx.t("ui.place.state_ribbon_none") if out.n == 0 else Tx.plural("ui.place.state_ribbon", int(out.n)) % int(out.n)
		"stock":
			out.n = (Game.account.storage.get("items", []) as Array).size()
			out.of = Game.accounts.storage_size()
			out.on = out.n > 0
			out.text = Tx.t("ui.place.state_stock_none") if out.n == 0 else Tx.plural("ui.place.state_stock", int(out.n)) % int(out.n)
		"growth":
			var planted := 0
			for b in r.get("beds", [r.object]):
				var v: Dictionary = Game.crafting.bed_view(c, str(r.room) + ":" + str(b))
				if str(v.herb) != "": planted += 1
				if v.ready: out.n = int(out.n) + 1
			out.of = planted
			out.on = int(out.n) > 0
			out.text = Tx.t("ui.place.state_growth_none") if planted == 0 else Tx.t("ui.place.state_growth") % [int(out.n), planted]
		"smoke":
			var queue: Array = c.crafting.get("auto_queue", [])
			var ready := queue.any(func(q): return Clock.now_utc() >= float(q.get("done_utc", 0.0)))
			out.n = queue.size()
			out.on = not queue.is_empty() or not Game.crafting.refine_session(c).is_empty()
			out.new = 1 if ready else 0
			out.text = Tx.t("ui.place.state_ready") if ready else (Tx.t("ui.place.state_smoke") if out.on else Tx.t("ui.place.state_cold"))
		"attuned":
			var o := _object(r)
			out.on = Game.account.teleports.has(str(o.get("stone", r.object)))
			out.text = Tx.t("ui.place.state_attuned") if out.on else Tx.t("ui.place.state_unattuned")
		"mist":
			var qi := float(ContentDB.room(str(r.room)).get("qi", 1.0))
			out.n = qi
			out.on = Unlocks.is_unlocked(c.id, "cultivation")
			out.text = Tx.t("ui.place.state_mist") % ("%.1f" % qi)
		"lit":
			out.on = str(c.last_shrine.get("object", "")) == str(r.object) and str(c.last_shrine.get("room", "")) == str(r.room)
			out.text = Tx.t("ui.place.state_lit") if out.on else Tx.t("ui.place.state_idle")
		"wares":
			out.on = true
			out.text = Tx.t("ui.place.state_wares")
		"steam":
			out.on = true
			out.text = Tx.t("ui.place.state_steam")
		"sparks":
			out.on = true
			out.text = Tx.t("ui.place.state_sparks")
	return out

## The room's own definition of a place's object (the side view's, or the one this table adds).
static func _object(r: Dictionary) -> Dictionary:
	if r.get("added", false): return r.get("object_def", {})
	for o in ContentDB.room(str(r.room)).get("objects", []):
		if str(o.get("id", "")) == str(r.object): return o
	return {}
