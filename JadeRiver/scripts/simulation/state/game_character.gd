class_name GameCharacter
extends RefCounted
## Everything that belongs to one character slot (S23 · per character). Each
## field has exactly one owning authority (Part 2 owner table); this class only
## groups the state objects and converts them to and from the v3 save shape.

const VERSION := 3

var id := ""
var slot := 1
var name := "Disciple"
var appearance: Dictionary = {}      # body, hair, hair_color (creator look; equipment overrides garments)
var cultivator := CultivatorState.new()
var relations := RelationsState.new()  # S49: karma ledger, alignment, Fame, affinity, bonds, grudges (Relations authority)
var pools := ResourcePool.new()
var stats := StatBlock.new()
var inventory := InventoryState.new()
var quests := QuestState.new()
var professions: Dictionary = {}     # craft -> {rank, xp}
var crafting: Dictionary = {"recipes": [], "auto_queue": [], "garden": [], "formations": []}
var training_sect: Dictionary = {}   # {id, rank, contribution, reputation, missions}
var position: Dictionary = {"room": "", "portal": "", "x": 0.0, "y": 0.0, "surface": "", "facing": 1}
var last_shrine: Dictionary = {}     # {room, x, y}
var last_town := ""
var seclusion: Dictionary = {}
var idle_task: Dictionary = {}
var companions: Dictionary = {"roster": [], "active": [], "bond": {}, "downed": {}}
var pets: Array = []
var eggs: Array = []                 # [{species, hatch_utc}] incubating spirit eggs (S22)
var active_pet := ""
var party_pets: Array = []           # S46: more animals beside the active one, up to the command capacity
var pet_bag: Array = []              # S46: animals carried in a Spirit Beast Bag (swappable in the field)
var mount_pet := ""                  # S46 Mount slot: the animal that carries you (beside a combat animal)
var riding := false                  # S46: on the mount (the Mount button)
var beast_arena: Dictionary = {}     # S46 Beast Arena: {rank, week, day, fights, last}
var tower: Dictionary = {}           # S49 Trial Tower (World): {cleared: highest floor, swept: {floor: day}}
var cooldowns: Dictionary = {}       # key -> utc until
var rooms: Dictionary = {}           # room id -> {nodes: {obj: utc}, opened: {obj: true}}
var skill_page := 0
var skip_prologue := false
var created_utc := 0.0
var last_active_utc := 0.0
var rng_seed := 0
var rng_state: Dictionary = {}
var loadouts: Array = []
var collection_first_kills: Dictionary = {}
var dungeon_lockouts: Dictionary = {} # boss -> reset day

func level() -> int:
	return ProgressionRules.level(self)

func realm_key() -> String:
	return cultivator.realm_key

func has_qi_pool() -> bool:
	return pools.max_qi > 0.0

func snapshot() -> Dictionary:
	return {"version": VERSION, "slot": slot, "id": id, "name": name, "appearance": appearance.duplicate(true),
		"origin": cultivator.origin, "cultivator": cultivator.snapshot(), "relations": relations.snapshot(), "pools": pools.snapshot(),
		"buffs": stats.snapshot(), "inventory": inventory.snapshot(), "professions": professions.duplicate(true),
		"crafting": crafting.duplicate(true), "training_sect": training_sect.duplicate(true),
		"quests": quests.snapshot(), "position": position.duplicate(true), "last_shrine": last_shrine.duplicate(true),
		"last_town": last_town, "seclusion": seclusion.duplicate(true), "idle_task": idle_task.duplicate(true),
		"companions": companions.duplicate(true), "pets": pets.duplicate(true), "eggs": eggs.duplicate(true), "active_pet": active_pet,
		"party_pets": party_pets.duplicate(), "pet_bag": pet_bag.duplicate(), "mount_pet": mount_pet, "riding": riding, "beast_arena": beast_arena.duplicate(true), "tower": tower.duplicate(true),
		"cooldowns": cooldowns.duplicate(true), "rooms": rooms.duplicate(true), "skill_page": skill_page,
		"skip_prologue": skip_prologue, "created_utc": created_utc, "last_active_utc": last_active_utc,
		"statuses": pools.statuses.duplicate(true), "loadouts": loadouts.duplicate(true),
		"collection_first_kills": collection_first_kills.duplicate(), "dungeon_lockouts": dungeon_lockouts.duplicate(),
		"rng": {"seed": str(rng_seed), "streams": rng_state.get("streams", {})}}

func restore(d: Dictionary) -> void:
	slot = int(d.get("slot", slot))
	id = str(d.get("id", "c%d" % slot))
	name = str(d.get("name", "Disciple")).strip_edges().left(24)
	if name == "": name = "Disciple"
	appearance = d.get("appearance", {}).duplicate(true)
	cultivator.restore(d.get("cultivator", {}))
	if cultivator.origin == "": cultivator.origin = str(d.get("origin", ""))
	if d.get("relations") is Dictionary: relations.restore(d.relations)
	else:
		# Before S49 the karma ledger lived on the cultivator (G1); it moves across unchanged.
		var cd: Dictionary = d.get("cultivator", {}) if d.get("cultivator") is Dictionary else {}
		relations.restore({"merit": cd.get("merit", 0), "sin": cd.get("sin", 0), "debts": cd.get("debts", {}), "merit_used": cd.get("merit_used", {})})
	inventory.restore(d.get("inventory", {}))
	professions = d.get("professions", {}).duplicate(true)
	crafting = d.get("crafting", crafting).duplicate(true)
	training_sect = d.get("training_sect", {}).duplicate(true)
	quests.restore(d.get("quests", {}))
	position = d.get("position", position).duplicate(true)
	last_shrine = d.get("last_shrine", {}).duplicate(true)
	last_town = str(d.get("last_town", ""))
	seclusion = d.get("seclusion", {}) if d.get("seclusion") is Dictionary else {}
	idle_task = d.get("idle_task", {}) if d.get("idle_task") is Dictionary else {}
	companions = d.get("companions", companions).duplicate(true)
	pets = d.get("pets", []).duplicate(true)
	eggs = d.get("eggs", []).duplicate(true)
	active_pet = str(d.get("active_pet", ""))
	party_pets = (d.get("party_pets", []) as Array).map(func(u): return str(u))
	pet_bag = (d.get("pet_bag", []) as Array).map(func(u): return str(u))
	mount_pet = str(d.get("mount_pet", ""))
	riding = bool(d.get("riding", false))
	beast_arena = d.get("beast_arena", {}).duplicate(true) if d.get("beast_arena") is Dictionary else {}
	tower = d.get("tower", {}).duplicate(true) if d.get("tower") is Dictionary else {}
	cooldowns = d.get("cooldowns", {}).duplicate(true)
	rooms = d.get("rooms", {}).duplicate(true)
	skill_page = clampi(int(d.get("skill_page", 0)), 0, 1)
	skip_prologue = bool(d.get("skip_prologue", false))
	created_utc = float(d.get("created_utc", 0.0))
	last_active_utc = float(d.get("last_active_utc", 0.0))
	loadouts = d.get("loadouts", []).duplicate(true)
	collection_first_kills = d.get("collection_first_kills", {}).duplicate()
	dungeon_lockouts = d.get("dungeon_lockouts", {}).duplicate()
	var r: Dictionary = d.get("rng", {})
	rng_seed = int(str(r.get("seed", "0")))
	rng_state = r.duplicate(true)
	pools.restore(d.get("pools", {}))
	stats.restore_timed(d.get("buffs", {}))
	for s in d.get("statuses", []):
		if s is Dictionary and s.has("id"): pools.statuses.append(s.duplicate())
