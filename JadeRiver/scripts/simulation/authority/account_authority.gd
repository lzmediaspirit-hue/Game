class_name AccountAuthority
extends Authority
## S23/S35/S37 · Slots, character list, active character, highest realm, idle
## tasks, storage, collection book, visited rooms, Account Legacy, settings, daily
## and weekly resets and the app lifecycle. Idle characters never break through,
## never die and earn realm progress at the offline factor 0.1.

var reset_timer := 0.0

func intents() -> Array:
	return ["create_character", "switch_character", "set_idle_task", "collect_idle", "deposit", "withdraw", "delete_character",
		"app_paused", "app_resumed", "set_setting", "enter_character", "claim_activity_chest"]

func subscribe() -> void:
	GameEvents.subscribe("realm_changed", _on_realm_changed, 70)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 70)
	GameEvents.subscribe("sect_level_changed", _on_sect_level, 70)
	# S49 daily activity: what counts toward today's chests.
	GameEvents.subscribe("quest_completed", func(p): if str(p.get("kind", "")) == "daily": apply_activity("mission"), 88)
	GameEvents.subscribe("actor_defeated", func(p): if str(p.get("role", "")) == "dungeon_boss" and str(p.get("killer", "")).begins_with("c"): apply_activity("dungeon"), 88)
	GameEvents.subscribe("craft_completed", func(_p): apply_activity("craft"), 88)
	GameEvents.subscribe("node_gathered", func(_p): apply_activity("harvest"), 88)
	GameEvents.subscribe("spar_ended", func(_p): apply_activity("spar"), 88)
	GameEvents.subscribe("tower_floor_cleared", func(_p): apply_activity("tower"), 88)
	GameEvents.subscribe("arena_battle", func(_p): apply_activity("arena"), 88)
	GameEvents.subscribe("beast_trial_result", func(_p): apply_activity("beast_trial"), 88)

func handle(intent: Dictionary) -> Dictionary:
	match str(intent.type):
		"create_character": return create_character(intent)
		"enter_character": return enter_character(int(intent.get("slot", 1)))
		"switch_character": return switch_character(int(intent.get("slot", 1)))
		"set_idle_task": return set_idle_task(game.character(str(intent.actor)), intent.get("task", {}))
		"collect_idle": return collect_idle(str(intent.get("character", "")))
		"deposit": return deposit(game.character(str(intent.actor)), int(intent.get("index", -1)), int(intent.get("count", 999)))
		"withdraw": return withdraw(game.character(str(intent.actor)), int(intent.get("index", -1)))
		"delete_character": return delete_character(int(intent.get("slot", 0)))
		"app_paused": return app_paused()
		"app_resumed": return app_resumed()
		"set_setting":
			game.account.settings[str(intent.get("key", ""))] = intent.get("value")
			emit("settings_changed", {"key": str(intent.get("key", "")), "value": intent.get("value")})
			return ok()
		"claim_activity_chest": return claim_activity_chest(game.character(str(intent.get("actor", ""))), str(intent.get("tier", "")))
	return fail("unknown_intent")

# ------------------------------------------------------------------ characters
func summary(c) -> Dictionary:
	return {"name": c.name, "realm_key": c.cultivator.realm_key, "level": ProgressionRules.level(c), "room": str(c.position.get("room", "")),
		"idle_task": c.idle_task.duplicate(true), "appearance": c.appearance.duplicate(), "outfit": InventoryAuthority.outfit_for(c),
		"sect": str(c.training_sect.get("id", "")), "bottleneck": c.cultivator.state == "bottleneck", "injured": not c.cultivator.injuries.is_empty()}

func slot_conditions() -> Array:
	return ContentDB.config("account_rules").get("slots", [])

func create_character(intent: Dictionary) -> Dictionary:
	var slot := int(intent.get("slot", 1))
	if slot < 1 or slot > game.account.slots_unlocked: return fail("slot_locked")
	if game.characters.has("c%d" % slot): return fail("slot_taken")
	var name := str(intent.get("name", Tx.t("sim.account.disciple"))).strip_edges().left(24)
	if name == "": return fail("bad_name", {"text": Tx.t("sim.account.please_enter_a_name")})
	var a: Dictionary = intent.get("appearance", {})
	var appearance := {"body": "light", "hair": "topknot", "hair_color": 0, "shirt": "cardigan", "pants": "loose", "shoes": "boots"}
	for k in ["hair", "shirt", "pants", "shoes"]:
		if ContentDB.parts.get(k, {}).has(str(a.get(k, ""))): appearance[k] = str(a[k])
	appearance.hair_color = clampi(int(a.get("hair_color", 0)), 0, 5)
	var origin := str(intent.get("origin", "fishers_child"))
	if not ContentDB.has_entry("origins", origin): origin = "fishers_child"
	var c := GameCharacter.new()
	c.slot = slot
	c.id = "c%d" % slot
	c.name = name
	c.appearance = appearance
	c.cultivator.origin = origin
	c.created_utc = Clock.now_utc()
	if game.account.created_utc <= 0.0: game.account.created_utc = c.created_utc   # the calendar's day zero (S49)
	c.rng_seed = (int(game.account.rng_seed) + slot * 7919) & 0x7fffffff
	Rng.forget(c.id)
	Rng.ensure(c.id, c.rng_seed)
	game.characters[c.id] = c
	game.progression.roll_aptitude(c)
	# Weaponless start (S27): creator look becomes the starting hemp garments.
	for s in [["starter_gourd", {}], ["hemp_robe", {"appearance": appearance.shirt}], ["hemp_trousers", {"appearance": appearance.pants}], ["straw_sandals", {"appearance": appearance.shoes}]]:
		var def := ContentDB.item(s[0])
		var inst := LootRules.make_instance(s[0], int(def.get("ilv", 1)), "common", null, c.inventory.next_uid)
		c.inventory.next_uid += 1
		for k in s[1]: inst[k] = s[1][k]
		c.inventory.equipped[str(def.slot)] = inst
	c.inventory.resize(c.inventory.capacity())
	var skip = bool(intent.get("skip_prologue", false)) and ContentDB.config("account_rules").get("skip_prologue_allowed", true) and game.characters.size() > 1
	c.skip_prologue = skip
	var start: Dictionary = ContentDB.config("account_rules").get("skip_start" if skip else "new_start", {})
	c.position = {"room": str(start.get("room", "lf_fishers_hut")), "portal": "", "x": float(start.get("x", 0)), "y": float(start.get("y", 0)), "surface": "", "facing": 1}
	StatRules.rebuild(c)
	c.pools.hp = c.pools.max_hp
	game.account.characters[str(slot)] = summary(c)
	emit("character_created", {"slot": slot, "actor": c.id, "skip_prologue": skip})
	if game.characters.size() > 1 and game.active_id != "":
		emit("system_used", {"actor": game.active_id, "system": "second_path"})
	if skip: _apply_skip_prologue(c, start)
	game.save_all()
	return ok({"actor": c.id})

func _apply_skip_prologue(c, start: Dictionary) -> void:
	# Later characters may skip the Prologue: Bone Forging 2 in Stoneford (S23).
	Unlocks.grant_prologue(c.id)
	for q in start.get("quests_done", []): c.quests.done[q] = 1
	for f in start.get("flags", []): c.quests.flags[f] = true
	game.progression.apply_learn_method(c.id, "riverbreath_fragment")
	c.cultivator.realm_key = str(start.get("realm", "bone_forging_2"))
	c.cultivator.energy_type = "none"
	c.cultivator.meridian_levels_granted = ProgressionRules.level(c)
	c.cultivator.unspent_meridian_points = 2 * ProgressionRules.level(c)
	for e in start.get("effects", []): game.apply_effects(c.id, [e], "skip_prologue")
	StatRules.rebuild(c)
	c.pools.hp = c.pools.max_hp

# ------------------------------------------------------------------ Max Test character (debug tools, S38)
## A character for checking everything, built only where debug tools run (debug builds and the Max Test APK).
## It stands at the highest realm this build's zones allow. It has:
## - every system unlocked;
## - every method, technique (top mastery), Inner Art, movement art, recipe and Dao tier;
## - the Prologue behind it;
## - the best gear at Perfect +10, and one best weapon of each family;
## - every animal, the companions, a training sect at Elder and a founded sect at its top level;
## - every teleport stone and room known, and money and shards to spend.
func create_max_character(slot: int, name: String) -> Dictionary:
	if not Unlocks.debug_tools(): return fail("locked")
	var made := create_character({"slot": slot, "name": name, "appearance": {"hair": "topknot", "shirt": "disciple", "pants": "loose", "shoes": "boots"}})
	if not made.get("ok", false): return made
	var c = game.character("c%d" % slot)
	c.skip_prologue = true
	var start: Dictionary = ContentDB.config("account_rules").get("skip_start", {})
	_apply_skip_prologue(c, start)
	c.position = {"room": str(start.get("room", "sf_fairground")), "portal": "", "x": float(start.get("x", 0)), "y": float(start.get("y", 0)), "surface": "", "facing": 1}
	for entry in ContentDB.all("unlocks"): Unlocks.force_unlock(c.id, str(entry.id))
	# The realm: the highest zone ceiling (Sage Sovereign 3 in v1.1); realms above it have no zone to stand in yet.
	var cu: CultivatorState = c.cultivator
	var top := "mortal"
	for z in ContentDB.all("zones"):
		if ContentDB.realm_position(str(z.get("ceiling", ""))) > ContentDB.realm_position(top): top = str(z.ceiling)
	cu.realm_key = top
	cu.energy_type = str(ContentDB.entry("realms", top).get("energy", cu.energy_type))
	cu.state = "accumulating"
	cu.qp = 0.0
	cu.purity = 1
	cu.core_grade = 1
	for k in cu.aptitude: cu.aptitude[k].revealed = true
	var level := ProgressionRules.level(c)
	cu.meridian_levels_granted = level
	cu.unspent_meridian_points = 0
	for lv in range(1, level + 1): cu.unspent_meridian_points += ProgressionRules.meridian_points_for_level(lv)
	var tiers: Array = ContentDB.all("body_tiers")
	for t in tiers:
		cu.body_trials.append(str(t.id))
		cu.body_baths.append(str(t.id))
	if not tiers.is_empty():
		cu.body_tier = str(tiers.back().id)
		cu.body_level = maxi(int(tiers.back().get("need", 1)), level)
	# Methods (the one reaching highest in use), techniques, Inner Arts (worn), movement arts, Daos, recipes and crafts.
	var method := ""
	for m in ContentDB.all("methods"):
		game.progression.apply_learn_method(c.id, str(m.id))
		if not m.get("fragment", false) and (method == "" or ContentDB.realm_position(str(m.get("ceiling", ""))) > ContentDB.realm_position(str(ContentDB.entry("methods", method).get("ceiling", "")))):
			method = str(m.id)
	if method != "": cu.method_id = method
	for t in ContentDB.all("techniques"):
		game.progression.apply_learn_technique(c.id, str(t.id))
		cu.mastery[str(t.id)] = {"tier": 6, "points": 0.0}
	for ia in ContentDB.all("inner_arts"): game.progression.apply_learn_inner_art(c.id, str(ia.id))
	for i in mini(ProgressionRules.inner_art_slot_count(cu.realm_key), cu.inner_arts_known.size()):
		game.progression.equip_inner_art(c, i, str(cu.inner_arts_known[i]))
	for art in ContentDB.all("secret_arts"): game.progression.apply_learn_secret_art(c.id, str(art.id))
	for d in ContentDB.all("daos"): cu.daos[str(d.id)] = {"tier": maxi(1, (d.get("tiers", []) as Array).size()), "insight": 0.0}
	var learn: Array = []
	var crafts := {}
	for r in ContentDB.all("recipes"):
		learn.append({"kind": "learn_recipe", "recipe": str(r.id)})
		crafts[str(r.get("craft", ""))] = true
	game.apply_effects(c.id, learn, "debug")
	var ranks: Array = ContentDB.curve("profession_ranks", [])
	for craft in crafts:
		if craft == "" or ranks.is_empty(): continue
		var cap: int = game.crafting.rank_cap(c, craft)
		c.professions[craft] = {"rank": str(ranks[cap][0]), "xp": float(ranks[cap][1])}
	var guild_ranks := {}
	for g in ContentDB.all("guilds"):
		for rk in g.get("ranks", []):
			if str(rk.get("flag", "")) != "": c.quests.flags[str(rk.flag)] = true
			if str(rk.get("title", "")) != "" and not c.cultivator.titles.has(str(rk.title)): c.cultivator.titles.append(str(rk.title))
			guild_ranks[str(g.craft)] = str(rk.id)   # every guild at its top rank
	c.crafting["guild"] = guild_ranks
	_max_gear(c)
	# Animals (each at the highest stage this realm reaches), a mount, the companions and both sects.
	var stage := {"id": "hatchling", "level": 1}
	for st in ContentDB.config("pet_growth").get("stages", []):
		if ProgressionRules.at_least(cu.realm_key, str(st.get("realm", "mortal"))): stage = st
	for sp in ContentDB.all("pets"):
		game.pets.apply_grant(c.id, str(sp.id))
	for pet in c.pets:
		if pet.get("construct", false): continue
		pet.stage = str(stage.id)
		pet.level = maxi(int(pet.level), int(stage.get("level", 1)))
		pet.bond = 10.0
		pet.revealed = (pet.get("traits", []) as Array).size()
	for pet in c.pets:
		if ContentDB.entry("pets", str(pet.species)).get("mount_only", false):
			game.pets.set_mount(c, str(pet.uid), null)
			break
	for comp in ContentDB.all("companions"): game.companions.apply_add(c.id, str(comp.id))
	var sects: Array = ContentDB.all("sects")
	if not sects.is_empty():
		game.training.apply_join(c.id, str(sects[0].id))
		for rk in ContentDB.config("sect_ranks").get("order", []): game.training.apply_rank(c.id, str(rk))
		game.training.apply_contribution(c.id, 100000, "debug")
	if game.account.sect.is_empty():
		var levels: Array = ContentDB.config("sect_levels").get("levels", [])
		var b := {}
		for row in ContentDB.all("sect_buildings"): b[str(row.id)] = int(row.get("max_level", 1))
		game.account.sect = {"name": name, "emblem": [0, 0], "level": int(levels.back().level) if not levels.is_empty() else 1,
			"prestige": int(levels.back().prestige) if not levels.is_empty() else 0, "buildings": b, "queue": [], "disciples": [],
			"candidates": [], "expeditions": [], "candidate_day": -1}
	# The map: every teleport stone found, every room walked; silver, stones and shards for fees and shops.
	for stone in ContentDB.all("teleport_stones"): game.account.teleports[str(stone.id)] = true
	for rid in ContentDB.rooms: game.account.visited_rooms[rid] = true
	game.economy.apply_currency("silver_tael", 10000000, "debug")
	game.economy.apply_currency("spirit_stone", 1000000, "debug")
	StatRules.rebuild(c)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.soul = c.pools.max_soul
	game.account.characters[str(slot)] = summary(c)
	game.save_all()
	return ok({"actor": c.id})

## The Max Test character's gear: the best piece for every slot at Perfect +10, the best furnace, one best weapon of
## each family in the bag (a jian in hand), every flight vessel (the last ridden), a Beast Bag, and ten of every pill,
## talisman and throwable in the account storage chest (the bag stays free for what you find).
func _max_gear(c) -> void:
	var rng := Rng.stream(c.id, "affix")
	var best := {}
	var by_family := {}
	for a in ContentDB.all("artifacts"):
		if a.get("relic", false) or a.get("legend", false) or a.get("imitation", false): continue
		var slot := str(a.get("slot", ""))
		var key := slot
		if slot == "weapon":
			var fam := str(a.get("family", ""))
			if not by_family.has(fam) or int(a.get("ilv", 0)) > int(by_family[fam].get("ilv", 0)): by_family[fam] = a
			continue
		if not best.has(key) or int(a.get("ilv", 0)) > int(best[key].get("ilv", 0)): best[key] = a
	if by_family.has("jian"): best["weapon"] = by_family.jian
	for slot in best:
		var def: Dictionary = best[slot]
		var inst := LootRules.make_instance(str(def.id), int(def.get("ilv", 1)), "perfect", rng, c.inventory.next_uid)
		c.inventory.next_uid += 1
		inst.enhance = 10
		if slot == "tool_furnace": c.inventory.furnace = inst
		elif c.inventory.equipped.has(slot): c.inventory.equipped[slot] = inst
	c.inventory.resize(c.inventory.capacity())
	for fam in by_family:
		if fam != "jian": game.inventory.apply_add_equipment(c.id, str(by_family[fam].id), int(by_family[fam].get("ilv", 1)), "perfect", "debug")
	var gifts := {"spirit_stone_shard": 99, "beast_bag_star": 1, "weapon_soul_crystal": 3}
	var stored: Array = game.account.storage.get("items", [])
	for it in ContentDB.all("items"):
		match str(it.get("type", "")):
			"vessel":
				gifts[str(it.id)] = 1
				c.inventory.vessel = str(it.id)
			"pill", "talisman", "throwable":
				var e := InventoryAuthority.pill_entry(str(it.id), {})
				e.count = 10
				stored.append(e)
	game.account.storage["items"] = stored
	for id in gifts:
		if not ContentDB.item(str(id)).is_empty(): game.inventory.apply_add(c.id, str(id), int(gifts[id]), "debug")

## Enter the world as this slot's character: claim offline/idle time first (S35 boot).
func enter_character(slot: int) -> Dictionary:
	var c = game.character("c%d" % slot)
	if c == null: return fail("empty_slot")
	var previous: String = game.active_id
	game.active_id = c.id
	game.account.active_slot = slot
	Rng.restore(c.id, c.rng_state, c.rng_seed if c.rng_seed != 0 else hash(c.id))
	StatRules.rebuild(c)
	var welcome := {}
	game.posts.migrate_idle(c)   # S50: an old idle Gather task becomes a post before anything is collected
	var elapsed := Clock.elapsed_since(c.last_active_utc)
	if elapsed.valid and float(elapsed.elapsed) > 60.0 and not c.seclusion.is_empty():
		welcome = game.progression.claim_offline(c, float(elapsed.elapsed))
	elif not c.idle_task.is_empty():
		welcome = collect_idle(c.id)
		c.idle_task = {}
	# S50 Keeping Post: a character coming in from its post settles it (the Return Ledger) and pauses it while played.
	var ledger: Dictionary = game.posts.on_entered(c)
	if not ledger.is_empty():
		if not welcome.has("gains"): welcome["gains"] = {}
		welcome["post"] = ledger
		welcome.gains["post"] = true
		if not welcome.has("hours"): welcome["hours"] = float(ledger.get("hours", 0.0))
	c.cultivator.meditating = false
	if previous != "" and previous != c.id: emit("character_switched", {"from": previous, "to": c.id})
	emit("character_entered", {"actor": c.id, "slot": slot})
	check_resets()
	game.quest._refresh_offers()
	GameEvents.unlock_pending = true
	return ok({"welcome": welcome})

## Switching only at a shrine, town or your sect; the character left starts its idle task.
func switch_character(slot: int) -> Dictionary:
	var current = game.active()
	var target = game.character("c%d" % slot)
	if target == null: return fail("empty_slot")
	if current != null and game.room_rt != null:
		var t := str(game.room_rt.def.get("type", ""))
		# S50: a character standing at its post may be switched out there; it goes on working.
		var posted: bool = game.posts.at_post(current)
		if not (t in ["town", "sect", "home", "interior"] or game.room_rt.def.get("safe", false) or posted):
			return fail("not_here", {"text": Tx.t("sim.account.switch_characters_at_a_shrine")})
		game.posts.on_left(current)
		if posted: current.idle_task = {}
		elif current.idle_task.is_empty() and Unlocks.is_unlocked(current.id, "idle_tasks"):
			current.idle_task = {"task": "seclusion" if Unlocks.is_unlocked(current.id, "seclusion") else "rest", "room": game.room_rt.room_id,
				"started_utc": Clock.now_utc(), "focus": "accumulate"}
		elif not current.idle_task.is_empty():
			current.idle_task.started_utc = Clock.now_utc()
		current.last_active_utc = Clock.now_utc()
	game.save_all()
	game.in_world = false
	game.room_rt = null
	return enter_character(slot)

func set_idle_task(c, task: Dictionary) -> Dictionary:
	if c == null: return fail("no_character")
	if not Unlocks.is_unlocked(c.id, "idle_tasks"): return fail("locked")
	var kind := str(task.get("task", "seclusion"))
	var def := ContentDB.entry("idle_tasks", kind)
	if def.is_empty(): return fail("unknown_task")
	if def.has("requires") and not RequirementRules.passes(def.requires, game.ctx(c)): return fail("locked", {"text": RequirementRules.first_failure_text(def.requires, game.ctx(c))})
	# S50: with Keeping Post, gathering while away is a post at a node, not an idle task.
	if kind == "gather" and Unlocks.is_unlocked(c.id, "keeping_post"): return fail("use_post", {"text": Tx.t("sim.posts.use_post")})
	# S49: idle Hunt and Gather only in rooms that allow them (room.idle).
	var idle_room := str(task.get("room", c.position.get("room", "")))
	if not game.world.idle_allowed(idle_room, kind): return fail("room", {"text": Tx.t("sim.account.idle_room_" + kind)})
	emit("system_used", {"actor": c.id, "system": "second_path"})
	c.idle_task = {"task": kind, "room": idle_room, "started_utc": Clock.now_utc(),
		"focus": str(task.get("focus", "accumulate")), "item": str(task.get("item", ""))}
	emit("idle_task_set", {"actor": c.id, "task": kind})
	return ok()

## Idle gains (S23): realm progress at the offline factor 0.1; materials and body XP at 25%; capped.
func collect_idle(char_id: String) -> Dictionary:
	var c = game.character(char_id)
	if c == null or c.idle_task.is_empty(): return ok({"gains": {}})
	var elapsed := Clock.elapsed_since(float(c.idle_task.get("started_utc", 0.0)))
	if not elapsed.valid:
		c.idle_task.started_utc = Clock.now_utc()
		return ok({"gains": {}, "clock_moved_back": true})
	var cap_h := float(ContentDB.curve("idle_cap_h", 12)) + float(game.sect.idle_cap_bonus())
	var span := ProgressionRules.offline_minutes(float(elapsed.elapsed), cap_h)
	var minutes := float(span.minutes)
	var factor := float(ContentDB.curve("offline_factor", 0.1))
	var mat := float(ContentDB.curve("idle_material_factor", 0.25))
	var gains := {}
	var task := str(c.idle_task.get("task", "seclusion"))
	var room := ContentDB.room(str(c.idle_task.get("room", "")))
	match task:
		"seclusion", "rest":
			var rate := ProgressionRules.meditation_rate(c, float(room.get("qi_density", 1.0)), game.progression.accumulation_bonus(c) + game.sect.idle_rate_bonus("seclusion"))
			gains.qp = rate * factor * minutes
			game.progression.apply_progress(c.id, gains.qp, "idle")
		"train":
			gains.body_xp = float(ContentDB.curve("training_body_xp_per_min", 20)) * mat * minutes
			game.progression.apply_body_xp(c.id, gains.body_xp, "idle")
		"hunt":
			if not game.world.idle_allowed(str(c.idle_task.get("room", "")), "hunt"): minutes = 0.0   # S49: nothing to hunt here
			var cp := StatRules.combat_power(c)
			var rec := maxf(1.0, float(room.get("recommended_cp", 50)))
			var kills_per_min := 6.0 * clampf(cp / rec, 0.2, 1.5) * mat
			var kills := int(kills_per_min * minutes)
			var lv := int(room.get("level_range", [1, 1])[0])
			gains.kills = kills
			gains.qp = ProgressionRules.kill_qp(ProgressionRules.level(c), lv, "normal") * kills * factor / mat
			game.progression.apply_progress(c.id, gains.qp, "idle")
			var pay := LootRules.zone_coins(str(c.idle_task.get("room", "")), int(LootRules.coins_for(lv, 1.0, 0.0) * kills * 0.2))
			if int(pay.amount) > 0: game.economy.apply_currency(str(pay.currency), int(pay.amount), "idle")
			gains.coins = int(pay.amount)
			gains.coin_currency = str(pay.currency)
		"gather":
			if not game.world.idle_allowed(str(c.idle_task.get("room", "")), "gather"): minutes = 0.0   # S49: nothing grows here
			var item := str(c.idle_task.get("item", ""))
			if item != "":
				var n := int(minutes / 6.0 * mat * 2.0)
				if n > 0: game.inventory.apply_add(c.id, item, n, "idle")
				gains.items = {item: n}
	c.idle_task.started_utc = Clock.now_utc()
	emit("idle_collected", {"character": c.id, "gains": gains, "capped": span.capped, "hours": minutes / 60.0})
	return ok({"gains": gains, "capped": span.capped, "hours": minutes / 60.0, "task": task})

func delete_character(slot: int) -> Dictionary:
	var id := "c%d" % slot
	if not game.characters.has(id) or id == game.active_id: return fail("cannot_delete")
	game.characters.erase(id)
	game.account.characters.erase(str(slot))
	Saves.repo.delete_character(slot)
	emit("character_deleted", {"slot": slot})
	return ok()

# ------------------------------------------------------------------ storage
func storage_size() -> int:
	if not Unlocks.is_unlocked(game.active_id, "storage"): return 0
	return 40 + int(game.sect.treasury_bonus())

func deposit(c, index: int, count: int) -> Dictionary:
	if c == null or storage_size() <= 0: return fail("locked")
	var items: Array = game.account.storage.get("items", [])
	var bag_item = c.inventory.bag[index] if index >= 0 and index < c.inventory.bag.size() else null
	if bag_item == null: return fail("empty")
	if ContentDB.item(str(bag_item.id)).get("type") == "key": return fail("key_item")
	var stackable := not ContentDB.is_equipment(str(bag_item.id)) and str(bag_item.get("quality", "")) != "pill_halo"   # a Halo stack keeps its own deposit time
	if stackable:
		for s in items:
			if InventoryAuthority.stack_key(s) == InventoryAuthority.stack_key(bag_item):
				var removed = game.inventory.apply_remove_index(c.id, index, count, "deposit")
				s.count = int(s.count) + int(removed.get("count", 0))
				emit("storage_changed", {})
				return ok()
	if items.size() >= storage_size(): return fail("storage_full")
	var removed2 = game.inventory.apply_remove_index(c.id, index, count, "deposit")
	if str(removed2.get("quality", "")) == "pill_halo":
		# A Halo pill drinks the Qi of the room its chest stands in (S44).
		removed2.stored_utc = Clock.now_utc()
		removed2.stored_density = float(game.room_rt.def.get("qi_density", 1.0)) if game.room_rt else 1.0
	items.append(removed2)
	game.account.storage.items = items
	emit("storage_changed", {})
	return ok()

## Another authority takes items out of storage (S46 Feeding Trough). Returns how many were taken.
func apply_take_storage(item_id: String, count: int, source: String) -> int:
	var items: Array = game.account.storage.get("items", [])
	var taken := 0
	for i in range(items.size() - 1, -1, -1):
		if taken >= count: break
		var s: Dictionary = items[i]
		if str(s.get("id", "")) != item_id: continue
		var n := mini(count - taken, int(s.get("count", 1)))
		s.count = int(s.get("count", 1)) - n
		taken += n
		if int(s.count) <= 0: items.remove_at(i)
	if taken > 0:
		game.account.storage.items = items
		emit("storage_changed", {"source": source})
	return taken

func withdraw(c, index: int) -> Dictionary:
	var items: Array = game.account.storage.get("items", [])
	if c == null or index < 0 or index >= items.size(): return fail("bad_index")
	var s: Dictionary = items[index]
	if s.has("stored_utc"):
		s.halo = InventoryAuthority.halo_now(s)
		s.erase("stored_utc")
		s.erase("stored_density")
	var added := 0
	if ContentDB.is_equipment(str(s.id)): added = game.inventory.apply_add_instance(c.id, s, "withdraw", false)
	else: added = game.inventory.apply_add(c.id, str(s.id), int(s.get("count", 1)), "withdraw", s, false)
	if added <= 0: return fail("bag_full")
	if ContentDB.is_equipment(str(s.id)) or added >= int(s.get("count", 1)): items.remove_at(index)
	else: s.count = int(s.count) - added
	emit("storage_changed", {})
	return ok()

# ------------------------------------------------------------------ reactions
func _on_realm_changed(p: Dictionary) -> void:
	var to := str(p.get("to", ""))
	var acc: AccountState = game.account
	if ContentDB.realm_position(to) > ContentDB.realm_position(acc.highest_realm):
		acc.highest_realm = to
		emit("account_highest_realm_changed", {"realm": to})
		_check_slots()
		var realm := str(ContentDB.realm(to).get("realm", ""))
		if bool(p.get("major", false)) and not acc.legacy.has(realm) and Unlocks.is_unlocked(str(p.actor), "account_legacy"):
			acc.legacy[realm] = true
			emit("legacy_recorded", {"realm": realm, "actor": str(p.actor)})
	if bool(p.get("major", false)):
		game.mail.apply_send(str(p.actor), "aunt_ping_realm", [{"item": "rice_ball", "count": 3}], {"realm": ContentDB.name_of("realms", to)})
	var c = game.character(str(p.actor))
	if c: acc.characters[str(c.slot)] = summary(c)

func _on_sect_level(_p: Dictionary) -> void:
	_check_slots()

func _check_slots() -> void:
	var acc: AccountState = game.account
	for rule in slot_conditions():
		var slot := int(rule.slot)
		if slot <= acc.slots_unlocked: continue
		if RequirementRules.passes(rule.get("requires", {}), {"char": game.active(), "account": acc, "room": {}}):
			acc.slots_unlocked = slot
			emit("slot_unlocked", {"slot": slot})
		else:
			break

func apply_slot(slot: int) -> void:
	if slot > game.account.slots_unlocked:
		game.account.slots_unlocked = mini(slot, AccountState.MAX_SLOTS)
		emit("slot_unlocked", {"slot": slot})

func _on_actor_defeated(p: Dictionary) -> void:
	if p.get("victim_kind", "") != "enemy" or not str(p.get("killer", "")).begins_with("c"): return
	if not Unlocks.is_unlocked(str(p.killer), "collection_book"): return
	var def := ContentDB.entry("enemies", str(p.def))
	var col = def.get("collection")
	if col == null: return
	var acc: AccountState = game.account
	var kills := int(acc.collection.get(str(p.def), 0)) + 1
	acc.collection[str(p.def)] = kills
	if kills == int(col.get("kills_to_fill", 50)):
		emit("collection_card_filled", {"enemy": str(p.def)})
		var page := str(col.page)
		var full := true
		for e in ContentDB.all("enemies"):
			var ec = e.get("collection")
			if ec != null and str(ec.get("page", "")) == page and int(acc.collection.get(e.id, 0)) < int(ec.get("kills_to_fill", 50)): full = false
		if full and not acc.collection_pages_done.has(page):
			acc.collection_pages_done[page] = true
			emit("collection_page_completed", {"page": page, "actor": str(p.killer)})

# ------------------------------------------------------------------ daily activity chests (S49 v1.0)
## Points from the day's missions, dungeon clears, crafts, harvests, spars, tower floors and beast fights fill four
## chests for the whole account (activity.json). Some sources are capped; everything starts again at the daily reset.
func activity() -> Dictionary:
	var day := Clock.reset_day(Clock.now_utc())
	if int(game.account.activity.get("day", -1)) != day:
		game.account.activity = {"day": day, "points": 0, "by": {}, "claimed": []}
	return game.account.activity

func apply_activity(source: String, times := 1) -> void:
	var src: Dictionary = ContentDB.config("activity").get("sources", {}).get(source, {})
	if src.is_empty() or times <= 0: return
	var a := activity()
	var had := int(a.by.get(source, 0))
	var add := int(src.get("points", 0)) * times
	if int(src.get("cap", 0)) > 0: add = mini(add, int(src.cap) - had)
	if add <= 0: return
	var before := int(a.points)
	a.by[source] = had + add
	a.points = before + add
	for t in ContentDB.all("activity"):
		if before < int(t.points) and int(a.points) >= int(t.points): emit("activity_chest_ready", {"tier": str(t.id), "points": int(t.points)})

func claim_activity_chest(c, tier: String) -> Dictionary:
	if c == null: return fail("no_character")
	var t := ContentDB.entry("activity", tier)
	if t.is_empty(): return fail("no_tier")
	var a := activity()
	if (a.claimed as Array).has(tier): return fail("claimed", {"text": Tx.t("sim.account.chest_claimed")})
	if int(a.points) < int(t.points): return fail("short", {"text": Tx.t("sim.account.chest_short") % (int(t.points) - int(a.points))})
	a.claimed.append(tier)
	game.apply_effects(c.id, t.get("rewards", []), "activity:" + tier)
	emit("activity_chest_claimed", {"actor": c.id, "tier": tier, "points": int(t.points)})
	return ok({"tier": tier})

# ------------------------------------------------------------------ resets (S37) and lifecycle (S35)
func tick(delta: float) -> void:
	reset_timer += delta
	if reset_timer >= 5.0:
		reset_timer = 0.0
		check_resets()

func check_resets() -> void:
	var acc: AccountState = game.account
	var now := Clock.now_utc()
	var day := Clock.reset_day(now)
	if int(acc.resets.get("last_daily_day", -1)) != day:
		acc.resets.last_daily_day = day
		emit("daily_reset", {"date": day})
	var week := Clock.reset_week(now)
	if int(acc.resets.get("last_weekly", -1)) != week:
		acc.resets.last_weekly = week
		emit("weekly_reset", {"date": week})

## Android pause/focus loss: save everything; start seclusion if meditating.
func app_paused() -> Dictionary:
	var c = game.active()
	if c != null:
		if c.cultivator.meditating and Unlocks.is_unlocked(c.id, "seclusion") and c.seclusion.is_empty():
			game.progression.enter_seclusion(c, "accumulate")
		game.posts.on_app_paused(c)
		c.last_active_utc = Clock.now_utc()
	emit("app_paused", {"elapsed": 0})
	game.save_all()
	return ok()

## Resume: clock check, claim offline exactly once, Welcome back after 5 minutes.
func app_resumed() -> Dictionary:
	var c = game.active()
	if c == null: return ok()
	var el := Clock.elapsed_since(c.last_active_utc)
	var result := {}
	if not el.valid:
		c.last_active_utc = Clock.now_utc()
		return ok({"clock_moved_back": true})
	if not c.seclusion.is_empty() and float(el.elapsed) > 0.0:
		result = game.progression.claim_offline(c, float(el.elapsed))
	# S50: a character left at its post when the game was put away worked there meanwhile.
	var ledger: Dictionary = game.posts.on_entered(c)
	if not ledger.is_empty():
		if not result.has("gains"): result["gains"] = {}
		result["post"] = ledger
		result.gains["post"] = true
		if not result.has("hours"): result["hours"] = float(ledger.get("hours", 0.0))
	c.last_active_utc = Clock.now_utc()
	check_resets()
	emit("app_resumed", {"elapsed": el.elapsed, "welcome": float(el.elapsed) > 300.0})
	return ok({"elapsed": el.elapsed, "welcome": result})

func migrate_from_v2(chars: Array) -> void:
	var acc: AccountState = game.account
	acc.slots_unlocked = maxi(1, chars.size())
	for d in chars:
		var slot := int(d.slot)
		var r := create_character({"slot": slot, "name": d.name, "appearance": d.appearance, "origin": "fishers_child"})
		var c = game.character("c%d" % slot)
		if c == null: continue
		c.skip_prologue = true
		_apply_skip_prologue(c, ContentDB.config("account_rules").get("skip_start", {}))
		var weapon := str(d.get("v2_weapon", "none"))
		var map := {"sword": "training_jian", "spear": "training_spear", "dagger": "training_short_blade", "staff": "training_staff", "bow": "training_bow"}
		if map.has(weapon): game.inventory.apply_add(c.id, map[weapon], 1, "v2_migration", {}, true)
		game.mail.apply_send(c.id, "welcome_gift", [{"item": "healing_pill", "count": 3}, {"item": "rice_ball", "count": 5}], {})
		acc.characters[str(slot)] = summary(c)
