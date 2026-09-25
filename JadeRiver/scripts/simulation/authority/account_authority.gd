class_name AccountAuthority
extends Authority
## S23/S35/S37 · Slots, character list, active character, highest realm, idle
## tasks, storage, collection book, visited rooms, Account Legacy, settings, daily
## and weekly resets and the app lifecycle. Idle characters never break through,
## never die and earn realm progress at the offline factor 0.1.

var reset_timer := 0.0

func intents() -> Array:
	return ["create_character", "switch_character", "set_idle_task", "collect_idle", "deposit", "withdraw", "delete_character",
		"app_paused", "app_resumed", "set_setting", "enter_character"]

func subscribe() -> void:
	GameEvents.subscribe("realm_changed", _on_realm_changed, 70)
	GameEvents.subscribe("actor_defeated", _on_actor_defeated, 70)
	GameEvents.subscribe("sect_level_changed", _on_sect_level, 70)

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
	var elapsed := Clock.elapsed_since(c.last_active_utc)
	if elapsed.valid and float(elapsed.elapsed) > 60.0 and not c.seclusion.is_empty():
		welcome = game.progression.claim_offline(c, float(elapsed.elapsed))
	elif not c.idle_task.is_empty():
		welcome = collect_idle(c.id)
		c.idle_task = {}
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
		if not (t in ["town", "sect", "home", "interior"] or game.room_rt.def.get("safe", false)):
			return fail("not_here", {"text": Tx.t("sim.account.switch_characters_at_a_shrine")})
		if current.idle_task.is_empty() and Unlocks.is_unlocked(current.id, "idle_tasks"):
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
	emit("system_used", {"actor": c.id, "system": "second_path"})
	c.idle_task = {"task": kind, "room": str(task.get("room", c.position.get("room", ""))), "started_utc": Clock.now_utc(),
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
	var stackable := not ContentDB.is_equipment(str(bag_item.id))
	if stackable:
		for s in items:
			if InventoryAuthority.stack_key(s) == InventoryAuthority.stack_key(bag_item):
				var removed = game.inventory.apply_remove_index(c.id, index, count, "deposit")
				s.count = int(s.count) + int(removed.get("count", 0))
				emit("storage_changed", {})
				return ok()
	if items.size() >= storage_size(): return fail("storage_full")
	var removed2 = game.inventory.apply_remove_index(c.id, index, count, "deposit")
	items.append(removed2)
	game.account.storage.items = items
	emit("storage_changed", {})
	return ok()

func withdraw(c, index: int) -> Dictionary:
	var items: Array = game.account.storage.get("items", [])
	if c == null or index < 0 or index >= items.size(): return fail("bad_index")
	var s: Dictionary = items[index]
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
