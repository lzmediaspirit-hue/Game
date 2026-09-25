class_name InventoryState
extends RefCounted
## S14 · Bag, equipped slots, quick-use and item instances for one character.
## Only the Inventory authority writes here. Stackables are {id, count};
## equipment instances carry {uid, id, ilv, quality, affixes, enhance, bound,
## durability, sockets, appearance}.

const SLOTS := ["weapon", "hat", "robe", "gourd", "trousers", "boots", "cape", "talisman"]

var bag: Array = []                # capacity-sized; null or instance
var equipped: Dictionary = {}      # slot -> instance or null
var quick_use := ""                # item id
var key_items: Array = []          # temporary quest items (not in the gourd)
var locked: Dictionary = {}        # uid -> true
var next_uid := 1
var new_items: Dictionary = {}     # item id -> true (green "new" dot until viewed)
var treasures: Array = ["", ""]    # gap report G2: treasures set in the HUD's Treasure buttons (item ids)
var vessel := ""                   # the flight vessel ridden when flying (a key item id), "" = none
var loadout: Dictionary = {"spare": null, "active": "a"}   # S47 dual loadout: the weapon not in hand, and which of A/B is held
var appearance_override: Dictionary = {}   # S47 wardrobe: slot -> look id shown instead of the item's own

func _init() -> void:
	for s in SLOTS: equipped[s] = null
	resize(25)

func capacity() -> int:
	var g = equipped.get("gourd")
	if g == null: return 25
	return int(ContentDB.item(g.id).get("gourd", {}).get("bag", 25))

func quick_capacity() -> int:
	var g = equipped.get("gourd")
	if g == null: return 5
	return int(ContentDB.item(g.id).get("gourd", {}).get("quick", 5))

func resize(n: int) -> void:
	while bag.size() < n: bag.append(null)
	# Never drop items when a smaller gourd is equipped; extra slots stay until emptied.
	while bag.size() > n and bag.back() == null: bag.pop_back()

func count(id: String) -> int:
	var total := 0
	for s in bag:
		if s != null and s.id == id: total += int(s.get("count", 1))
	for k in key_items:
		if k.id == id: total += int(k.get("count", 1))
	return total

func count_including_equipped(id: String) -> int:
	var total := count(id)
	for slot in equipped:
		if equipped[slot] != null and equipped[slot].id == id: total += 1
	return total

func free_slots() -> int:
	var n := 0
	for s in bag:
		if s == null: n += 1
	return n

func find_uid(uid: int) -> int:
	for i in bag.size():
		if bag[i] != null and int(bag[i].get("uid", -1)) == uid: return i
	return -1

func first_index(id: String) -> int:
	for i in bag.size():
		if bag[i] != null and bag[i].id == id: return i
	return -1

## How many of `id` could be added without overflow.
func room_for(id: String, n: int) -> int:
	var def := ContentDB.item(id)
	var stack := int(def.get("stack", 99))
	var space := 0
	for s in bag:
		if s == null: space += stack
		elif s.id == id and stack > 1: space += stack - int(s.count)
	return mini(n, space)

func snapshot() -> Dictionary:
	var eq := {}
	for s in SLOTS: eq[s] = equipped[s].duplicate(true) if equipped[s] != null else null
	return {"bag": bag.duplicate(true), "equipped": eq, "quick_use": quick_use, "key_items": key_items.duplicate(true),
		"locked": locked.keys(), "next_uid": next_uid, "treasures": treasures.duplicate(), "vessel": vessel,
		"loadout": {"spare": loadout.spare.duplicate(true) if loadout.get("spare") != null else null, "active": str(loadout.get("active", "a"))},
		"appearance_override": appearance_override.duplicate()}

func restore(d: Dictionary) -> void:
	bag = []
	for s in d.get("bag", []):
		bag.append(s.duplicate(true) if s is Dictionary and ContentDB.item(str(s.get("id", ""))).size() > 0 else null)
	for s in SLOTS:
		var v = d.get("equipped", {}).get(s)
		equipped[s] = v.duplicate(true) if v is Dictionary and ContentDB.is_equipment(str(v.get("id", ""))) else null
	quick_use = str(d.get("quick_use", ""))
	treasures = ["", ""]
	var ts = d.get("treasures", [])
	if ts is Array:
		for i in mini(2, ts.size()): treasures[i] = str(ts[i]) if ContentDB.item(str(ts[i])).has("treasure") else ""
	vessel = str(d.get("vessel", ""))
	var lo: Dictionary = d.get("loadout", {}) if d.get("loadout", {}) is Dictionary else {}
	var sp = lo.get("spare")
	loadout = {"spare": sp.duplicate(true) if sp is Dictionary and ContentDB.is_equipment(str(sp.get("id", ""))) else null,
		"active": "b" if str(lo.get("active", "a")) == "b" else "a"}
	appearance_override = d.get("appearance_override", {}).duplicate() if d.get("appearance_override", {}) is Dictionary else {}
	key_items = []
	for k in d.get("key_items", []):
		if k is Dictionary: key_items.append(k.duplicate(true))
	# Tools live in the key-item pouch (they never take bag space); older saves move them there.
	for i in bag.size():
		var s2 = bag[i]
		if s2 != null and str(ContentDB.item(str(s2.id)).get("type", "")) == "tool":
			var merged := false
			for k2 in key_items:
				if str(k2.id) == str(s2.id):
					merged = true
			if not merged: key_items.append({"id": str(s2.id), "count": 1})
			bag[i] = null
	locked.clear()
	for uid in d.get("locked", []): locked[int(uid)] = true
	next_uid = int(d.get("next_uid", 1))
	for s in bag:
		if s != null and s.has("uid"): next_uid = maxi(next_uid, int(s.uid) + 1)
	for s in SLOTS:
		if equipped[s] != null and equipped[s].has("uid"): next_uid = maxi(next_uid, int(equipped[s].uid) + 1)
	resize(capacity())
