class_name WorldLoot
extends WorldPart
## WorldAuthority's part: beast ranks and cores (S46) and loot (S32): the roll on a kill, starter gear, the drops on the
## ground and picking them up.

const PICKUP_RADIUS := 48.0
const ATTUNEMENT_SHARDS := ["storm_shard", "star_shard"]

## A beast's rank from its Level (1-9 is rank 1 ... 73+ is rank 9); 0 for anything that is not a beast.
static func beast_rank(def: Dictionary, level: int) -> int:
	if str(def.get("race", "beast")) != "beast": return 0
	return clampi((maxi(1, level) - 1) / 9 + 1, 1, 9)

## The core a beast of this Level carries (by its element and rank tier), or "" below rank 2.
static func beast_core_for(def: Dictionary, level: int) -> String:
	var rank := beast_rank(def, level)
	var cfg: Dictionary = ContentDB.config("pet_growth").get("cores", {})
	if rank < int(cfg.get("min_rank", 2)): return ""
	var tier := ""
	for t in cfg.get("tiers", {}):
		var band: Array = cfg.tiers[t]
		if rank >= int(band[0]) and rank <= int(band[1]): tier = str(t)
	var el := str(def.get("element", "earth")).trim_prefix("hollow_")
	if el in ["hollow", "none", ""]: el = "soul" if el == "hollow" else "earth"
	var id := "%s_core_%s" % [el, tier]
	if ContentDB.item(id).is_empty(): id = "%s_core_%s" % [CombatRules.parent_element(el), tier]   # a sub-element's parent
	return id if ContentDB.item(id).size() > 0 else ""

static func core_chance(def: Dictionary, level: int) -> float:
	return float(ContentDB.config("pet_growth").get("cores", {}).get("chance_per_rank", 0.02)) * beast_rank(def, level)

## The next soul memory the account has not read ("" once all are read).
func _next_soul_memory() -> String:
	for i in range(1, 100):
		var id := "soul_memory_%d" % i
		if not ContentDB.has_entry("codex", id): return ""
		if not game.account.codex.has(id): return id
	return ""

func on_actor_defeated(p: Dictionary) -> void:
	if p.get("victim_kind", "") != "enemy" or game.room_rt == null: return
	var c = game.character(str(p.get("killer", game.active_id)))
	if c == null: c = game.active()
	if c == null: return
	var def := ContentDB.entry("enemies", str(p.def))
	if def.is_empty(): return
	var rng := Rng.stream(c.id, "loot")
	var elite_spawn: bool = bool(p.get("elite", false)) and def.get("role", "normal") == "normal"
	var table := ContentDB.entry("loot_tables", str(def.get("loot", p.def)))
	var drop := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate") + game.pets.trait_bonus(c, "drop_chance"), c.stats.value("coin_find"),
		{"needs": game.quest.item_needs(c), "elite": elite_spawn or def.get("role", "") == "elite", "find_rng": Rng.stream(c.id, "finds")})
	if elite_spawn:
		# A normal kind spawned as an elite rolls its items again, pays an elite's coins and has one more equipment roll
		# (P7b: grades.json drop.elite_extra).
		var extra := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate"), c.stats.value("coin_find"), {"no_equipment": true})
		drop.items.append_array(extra.items)
		drop.coins = LootRules.coins_for(int(p.level), 6.0, c.stats.value("coin_find"))
		var ex: Dictionary = LootRules.drop_cfg().get("elite_extra", {})
		if rng.randf() < float(ex.get("chance", 0.0)):
			drop.equipment.append({"level": int(p.level), "min_quality": str(ex.get("min_quality", "common")), "starter": bool(table.get("starter", false))})
	if bool(p.get("summoned", false)): drop.equipment.clear()
	elif not game.combat.captured.has(str(p.get("victim", ""))): starter_drop(c, table, int(p.level), drop)
	# Quest-only items drop only while a quest needs them.
	drop.items = drop.items.filter(func(it): return not ContentDB.item(it.item).get("quest_item", false) or game.quest.needs_item(c, str(it.item)))
	# First kill of each species per character gives a bonus roll.
	if not c.collection_first_kills.has(str(p.def)):
		c.collection_first_kills[str(p.def)] = true
		var bonus := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), 1.0, 0.0, {"no_equipment": true})
		drop.items.append_array(bonus.items)
	# S48 Soul Search: a searched elite gives up what it hid (one more roll) and a memory for the Codex.
	var sm: Dictionary = game.combat.searched.get(str(p.get("victim", "")), {})
	if not sm.is_empty():
		game.combat.searched.erase(str(p.victim))
		var hid := LootRules.roll(str(def.get("loot", p.def)), rng, int(p.level), c.stats.value("drop_rate"), 0.0, {"no_equipment": true})
		drop.items.append_array(hid.items)
		var memory := _next_soul_memory()
		if memory != "": game.apply_effects(c.id, [{"kind": "codex", "entry": memory}], "soul_search")
		emit("soul_searched", {"actor": c.id, "def": str(p.def), "memory": memory, "items": hid.items.size()})
	# P13a Lost Arts (technique_plan §5.3): the kill's own roll of its lost manuals (not the extra rolls above) is kept
	# only while the art is not found, and is sure by its pity-th kill.
	if not bool(p.get("summoned", false)) and not game.combat.captured.has(str(p.get("victim", ""))):
		drop.items.append_array(game.progression.lost_drops(c, drop.get("lost", [])))
	# Taken whole by the Taming Cauldron (S47): its materials at full count, no loot roll, no coins, nothing it wore.
	if game.combat.captured.has(str(p.get("victim", ""))):
		game.combat.captured.erase(str(p.victim))
		drop = {"items": LootRules.capture_materials(str(def.get("loot", p.def))), "coins": 0, "equipment": []}
		emit("beast_captured", {"actor": c.id, "def": str(p.def), "items": drop.items.size()})
	# S46 beast cores: rank 2 and up, 2% a rank, by the beast's element and rank tier (their own stream).
	var core := beast_core_for(def, int(p.level))
	if core != "" and not bool(p.get("summoned", false)) and Rng.stream(c.id, "cores").randf() < core_chance(def, int(p.level)):
		drop.items.append({"item": core, "count": 1})
	# S46 pet skill books from bosses and elites, on their own stream.
	var book: Dictionary = def.get("pet_book", {})
	if not book.is_empty() and not bool(p.get("summoned", false)) and (bool(p.get("elite", false)) or not book.get("elite_only", false)) \
			and Rng.stream(c.id, "books").randf() < float(book.get("chance", 0.0)):
		drop.items.append({"item": str(book.item), "count": 1})
	# S45 Spirit Soil: 1% from a beast of rank 3 or above (Level 19+), on its own stream so the loot roll is untouched.
	var soil: Dictionary = ContentDB.config("garden").get("spirit_soil", {})
	if str(def.get("race", "")) == "beast" and int(p.level) >= int(soil.get("min_level", 19)) and not bool(p.get("summoned", false)) \
			and Rng.stream(c.id, "garden").randf() < float(soil.get("chance", 0.01)):
		drop.items.append({"item": "spirit_soil", "count": 1})
	# A boss's one-time treasure (a Heavenly Flame, G1): guaranteed on its first defeat, outside the loot roll.
	# An elite can carry one too (the Weeping Lantern's Mist Lantern Flame, S44): only the elite of its kind drops it.
	var once: Array = def.get("first_defeat", []).duplicate()
	if p.get("elite", false): once.append_array(def.get("elite_first_defeat", []))
	for it in once:
		var flag := "first_defeat:%s:%s" % [str(p.def), str(it)]
		if c.quests.has_flag(flag): continue
		game.quest.apply_flag(c.id, flag)
		drop.items.append({"item": str(it), "count": 1})
	var role := str(p.get("role", ""))
	drop_loot(c, drop, Vector2(float(p.x), float(p.y)), float(p.get("alt", 0.0)),
		"field_boss" if role == "field_boss" else ("boss" if role in ["dungeon_boss", "story_boss"] else ("elite" if p.get("elite", false) else "enemy")))

## Starter gear (grades.json drop.starter; docs/tutorial_order.md): a kill of a first-room foe (a `starter` table).
## The character's first such kill drops its first weapon, a Fine training piece of `first_family`, marked for its
## moment. After it, until the character has `pity_pieces` starter pieces, a kill that drops none counts on the
## character (`starter_drops.kills`) and the `pity`-th gives one.
func starter_drop(c, table: Dictionary, level: int, drop: Dictionary) -> void:
	if not table.get("starter", false): return
	var cfg: Dictionary = LootRules.drop_cfg().get("starter", {})
	var sd: Dictionary = c.starter_drops
	if not sd.get("first", false):
		sd.first = true
		drop.equipment.append({"level": level, "min_quality": str(cfg.get("first_quality", "fine")), "starter": true,
			"family": str(cfg.get("first_family", "")), "first": true})
		return
	if sd.get("closed", false) or int(sd.get("pieces", 0)) >= int(cfg.get("pity_pieces", 0)): return
	sd.kills = int(sd.get("kills", 0)) + 1
	if drop.equipment.is_empty() and int(sd.kills) >= int(cfg.get("pity", 15)):
		drop.equipment.append({"level": level, "min_quality": str(table.get("equipment", {}).get("min_quality", "flawed")), "starter": true})
	if not drop.equipment.is_empty():
		sd.pieces = int(sd.get("pieces", 0)) + 1
		sd.kills = 0

## The shard a zone's attunement jades eat ("" in a zone with no attunement).
static func zone_shard(room_id: String) -> String:
	var att = ContentDB.zone_of_room(room_id).get("attunement")
	return str(att.get("shard", "")) if att is Dictionary else ""

## `source` says what left the loot (P6: the loot fountain tells a boss's drop from a jar's): enemy, elite, boss,
## field_boss, fled, jar, chest, rift or tower. It only goes into the event.
func drop_loot(c, drop: Dictionary, at: Vector2, alt: float, source: String) -> void:
	var rt: RoomRuntime = game.room_rt
	var rng := Rng.stream(c.id, "loot")
	var drops: Array = []
	var here_shard := zone_shard(rt.room_id)
	for it in drop.get("items", []):
		if ContentDB.item(str(it.item)).is_empty() or int(it.count) <= 0: continue
		var iid := str(it.item)
		# S18 v1.2: a foe that roams two zones (the Starsea pirates) leaves the attunement shards of the zone it dies in.
		if here_shard != "" and iid != here_shard and iid in ATTUNEMENT_SHARDS: iid = here_shard
		drops.append({"item": iid, "count": int(it.count), "find": bool(it.get("find", false))})
	var family := StatRules.family_of_weapon(c.inventory.equipped.get("weapon"))
	for eq in drop.get("equipment", []):
		var inst := LootRules.make_drop(Rng.stream(c.id, "affix"), eq, c.stats.value("fortune"), true, c.inventory.next_uid, family)
		if inst.is_empty(): continue
		c.inventory.take_uid()   # the uid it was made with
		drops.append({"item": inst.id, "count": 1, "instance": inst, "first": bool(eq.get("first", false))})
	if int(drop.get("coins", 0)) > 0: drops.append({"coins": int(LootRules.zone_coins(rt.room_id, int(drop.coins)).amount)})
	var i := 0
	var items_out: Array = []
	for d in drops:
		var spread := (i - (drops.size() - 1) * 0.5) * 22.0
		var spot := loot_spot(rt, at, alt, spread, rng.randf_range(-6, 6))
		var entry := {"uid": rt.uid(), "item": str(d.get("item", "")), "count": int(d.get("count", 0)), "coins": int(d.get("coins", 0)),
			"instance": d.get("instance", {}), "x": spot.x, "y": spot.y, "alt": spot.z,
			"ttl": 120.0 if d.has("coins") else 60.0, "age": 0.0}
		entry.quality = str(d.get("instance", {}).get("quality", "common"))
		if d.get("find", false): entry.find = true   # a rare row marked as a find (an early surprise): the rare-find moment
		if d.get("first", false): entry.first = true   # a character's first weapon: a find of its own (MomentRules.is_rare)
		rt.loot.append(entry)
		items_out.append(entry.duplicate())
		i += 1
	if not items_out.is_empty():
		emit("loot_dropped", {"room": rt.room_id, "items": items_out, "x": at.x, "y": at.y, "source": source,
			"first_weapon": items_out.any(func(it): return it.get("first", false))})

## Where one drop of a spill lies: (x, y, height), in a row across the spot, `spread` from it and `jitter` in depth. The
## side view keeps it inside its walk strip at the spot's height. On the height grid each lies on the floor it falls
## on, and one that would land in a wall, the water or off the spot's own floor (over a ledge) lies on the spot itself.
static func loot_spot(rt: RoomRuntime, at: Vector2, alt: float, spread: float, jitter: float) -> Vector3:
	if WorldAuthority.side_view(rt): return Vector3(at.x + spread, clampf(at.y + jitter, 626, 956), alt)
	var g := rt.topdown
	var p := at + Vector2(spread, jitter)
	if not g.standable(TopdownRoom.cell_of(p)) or absf(g.floor_at(p) - g.floor_at(at)) > 8.0: p = at
	return Vector3(p.x, p.y, g.floor_at(p))

func pick_up(c, uid: int) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	for l in game.room_rt.loot:
		if int(l.uid) == uid: return collect(c, l)
	return fail("gone")

func collect(c, l: Dictionary) -> Dictionary:
	var rt: RoomRuntime = game.room_rt
	if int(l.coins) > 0:
		game.economy.apply_currency(str(LootRules.zone_coins(rt.room_id, 1).currency), int(l.coins), "loot")
		rt.loot.erase(l)
		emit("loot_picked", {"actor": c.id, "uid": l.uid, "coins": l.coins})
		return ok()
	var added := 0
	if not (l.instance as Dictionary).is_empty():
		added = game.inventory.apply_add_instance(c.id, l.instance, "loot")
	else:
		added = game.inventory.apply_add(c.id, str(l.item), int(l.count), "loot", {}, false)
	if added <= 0: return fail("bag_full")
	l.count = int(l.count) - added
	if int(l.count) <= 0 or not (l.instance as Dictionary).is_empty():
		rt.loot.erase(l)
		emit("loot_picked", {"actor": c.id, "uid": l.uid, "item": l.item})
	return ok()

## Each tick: a drop the character stands at is picked up, and one left past its time is gone (a quest item or a
## piece of Fine quality and up goes to the overflow instead).
func tick_loot(c, rt: RoomRuntime, st: ActorState, delta: float) -> void:
	# The pickup's reach in height: the side view's 60 up and down; on the height grid half a level, so a drop on the
	# terrace is not drawn in from the square below its face.
	var loot_band := 60.0 if WorldAuthority.side_view(rt) else TopdownRoom.LEVEL * 0.5
	for l in rt.loot.duplicate():
		l.age = float(l.age) + delta
		if st != null and not game.combat.is_wounded(c.id) and float(l.age) > 0.45:
			if Vector2(float(l.x), float(l.y)).distance_to(st.plane) <= PICKUP_RADIUS * (1.6 if game.pets.gatherer_active(c.id) else 1.0) and absf(float(l.alt) - st.altitude) < loot_band:
				# A stack the bag refused is tried again once the bag changes, not every tick (each try says the bag is full).
				var bag_now := "%d|%d" % [c.inventory.free_slots(), c.inventory.count(str(l.item))]
				if str(l.get("refused", "")) != bag_now:
					if collect(c, l).ok: continue
					l.refused = bag_now
		if float(l.age) >= float(l.ttl):
			rt.loot.erase(l)
			if int(l.coins) == 0 and (ContentDB.item(str(l.item)).get("quest_item", false) or l.get("quality", "common") in ["fine", "superior", "perfect", "relic"]):
				game.inventory.apply_overflow(c.id, [{"item": l.item, "count": l.count, "instance": l.instance}])
			emit("loot_expired", {"uid": l.uid})
