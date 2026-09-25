extends Node
## `Game` autoload: the GameAuthority facade (Part 2). Presentation sends intents
## through `submit`; authorities validate them, change their own state and emit
## events on GameEvents. `tick` advances the simulation in the fixed owner order:
## Movement (player LocalAuthority) → Combat → Progression → Enemies → World →
## deliver events → unlocks re-evaluate → save checkpoint → presentation draws.

const SAVE_INTERVAL := 5.0

var account := AccountState.new()
var characters: Dictionary = {}       # id -> GameCharacter
var active_id := ""
var movement: Dictionary = {}         # actor id -> ActorState (scene-free movement state)
var room_rt: RoomRuntime = null       # the loaded room (one room at a time)
var sim_time := 0.0
var tick_count := 0
var paused := false
var in_world := false
var autosave_enabled := true
var save_timer := 0.0
var booted := false
var last_seq: Dictionary = {}
var handlers: Dictionary = {}
var authorities: Array = []

var combat: CombatAuthority
var progression: ProgressionAuthority
var enemies: EnemyAuthority
var world: WorldAuthority
var inventory: InventoryAuthority
var quest: QuestAuthority
var economy: EconomyAuthority
var accounts: AccountAuthority
var crafting: CraftingAuthority
var training: TrainingSectAuthority
var mail: MailAuthority
var achievements: AchievementAuthority
var pets: PetAuthority
var companions: CompanionAuthority
var sect: SectAuthority
var workshop: WorkshopAuthority
var relations: RelationsAuthority
var calendar: CalendarAuthority

func _ready() -> void:
	build_authorities()

func build_authorities() -> void:
	GameEvents.clear_subscribers()
	handlers.clear()
	combat = CombatAuthority.new(self)
	progression = ProgressionAuthority.new(self)
	enemies = EnemyAuthority.new(self)
	world = WorldAuthority.new(self)
	inventory = InventoryAuthority.new(self)
	quest = QuestAuthority.new(self)
	economy = EconomyAuthority.new(self)
	accounts = AccountAuthority.new(self)
	crafting = CraftingAuthority.new(self)
	training = TrainingSectAuthority.new(self)
	mail = MailAuthority.new(self)
	achievements = AchievementAuthority.new(self)
	pets = PetAuthority.new(self)
	companions = CompanionAuthority.new(self)
	sect = SectAuthority.new(self)
	workshop = WorkshopAuthority.new(self)
	relations = RelationsAuthority.new(self)
	calendar = CalendarAuthority.new(self)
	authorities = [combat, progression, enemies, world, inventory, quest, economy, accounts, crafting, training, mail,
		achievements, pets, companions, sect, workshop, relations, calendar]
	for a in authorities:
		for type in a.intents():
			assert(not handlers.has(type), "Intent registered twice: " + type)
			handlers[type] = a
		a.subscribe()

## Fresh state (tests and account reset).
func reset_state() -> void:
	account = AccountState.new()
	characters.clear()
	movement.clear()
	active_id = ""
	room_rt = null
	sim_time = 0.0
	tick_count = 0
	paused = false
	in_world = false
	last_seq.clear()
	build_authorities()

# ------------------------------------------------------------------ queries
func active():
	return characters.get(active_id)

func character(id: String):
	return characters.get(id)

func actor_state(id: String) -> ActorState:
	return movement.get(id)

func bind_movement(actor_id: String, state: ActorState) -> void:
	movement[actor_id] = state

func ctx(c = null) -> Dictionary:
	if c == null: c = active()
	return {"char": c, "account": account, "room": room_rt.def if room_rt else {}}

func level_of(actor_id: String) -> int:
	var c = character(actor_id)
	return ProgressionRules.level(c) if c else 0

func is_revealed(element: String) -> bool:
	return Unlocks.is_revealed(active_id, element)

# ------------------------------------------------------------------ intents
## Presentation's only way to change the game. Returns {ok, reason?, ...}.
func submit(intent: Dictionary) -> Dictionary:
	var type := str(intent.get("type", ""))
	if not handlers.has(type): return Authority.fail("unknown_intent")
	var actor := str(intent.get("actor", active_id))
	intent["actor"] = actor
	if intent.has("seq"):
		var seq := int(intent.seq)
		if seq <= int(last_seq.get(actor, -1)): return Authority.fail("stale_sequence")
		last_seq[actor] = seq
	for k in intent:
		var v = intent[k]
		if (v is float and not is_finite(v)) or (v is Vector2 and not v.is_finite()): return Authority.fail("non_finite")
	var result: Dictionary = handlers[type].handle(intent)
	_after_pass()
	return result

## Effects (Part 2 · Effect): dispatched to the owning authority's apply_* command.
func apply_effects(actor_id: String, effects: Array, source: String) -> void:
	for e in effects:
		if not (e is Dictionary): continue
		match str(e.get("kind", "")):
			"grant_item": inventory.apply_add(actor_id, str(e.item), int(e.get("count", 1)), source, e.get("instance", {}))
			"remove_item": inventory.apply_remove(actor_id, str(e.item), int(e.get("count", 1)), source)
			"grant_currency": economy.apply_currency(str(e.get("currency", "silver_tael")), int(e.amount), source)
			"add_progress": progression.apply_progress(actor_id, float(e.get("amount", 0)), source, float(e.get("pct_of_need", 0)))
			# Gap report G1: the heart-demon meter, the karma ledger and its named debts, residue.
			"add_heart_demon": progression.apply_heart_demon(actor_id, float(e.get("amount", 0)), source)
			"add_merit": relations.apply_karma(actor_id, int(e.get("amount", 0)), 0, str(e.get("reason", source)))
			"add_sin": relations.apply_karma(actor_id, 0, int(e.get("amount", 0)), str(e.get("reason", source)))
			"record_debt": relations.apply_karma_debt(actor_id, str(e.id), float(e.get("due_h", 24)), str(e.get("mail", "")), e.get("attachments", []))
			# S49: a named deed from karma.json (merit, sin, alignment and Fame together), and the two axes alone.
			"deed": relations.apply_deed(actor_id, str(e.deed))
			"add_alignment": relations.apply_alignment(actor_id, int(e.get("amount", 0)), str(e.get("reason", source)))
			"add_fame": relations.apply_fame(actor_id, int(e.get("amount", 0)), str(e.get("reason", source)))
			"add_affinity": relations.apply_affinity(actor_id, str(e.npc), int(e.get("amount", 0)), str(e.get("reason", source)))
			"master_legacy": relations.apply_master_legacy(actor_id)
			"rift_reward": world.apply_rift_reward(actor_id, str(e.get("loot", "chest_dungeon")), int(e.get("level", 1)))
			"treasure_claim": calendar.apply_treasure_claim(actor_id, int(e.get("k", -1)))
			# S49 fortune encounters and lifespan.
			"fortune_grotto": relations.apply_fortune_grotto(actor_id)
			"insight_best": relations.apply_insight_best(actor_id, float(e.get("amount", 20)))
			"grain_blessing": crafting.apply_grain_blessing(actor_id, float(e.get("value", -1.0)))
			"add_longevity": progression.apply_longevity(actor_id, int(e.get("years", 0)))
			"add_bond_species": pets.apply_bond_species(actor_id, str(e.get("species", "")), float(e.get("amount", 1)))
			"learn_inner_art": progression.apply_learn_inner_art(actor_id, str(e.art))
			"add_residue": progression.apply_residue(actor_id, float(e.get("amount", 0)))
			"clear_residue": progression.apply_residue(actor_id, -float(e.get("amount", 1000000.0)))
			# S48 body ladder and physiques.
			"pass_body_trial": progression.pass_body_trial(actor_id, str(e.get("tier", "")))
			"awaken_physique": progression.awaken_physique(actor_id, str(e.get("physique", "")))
			# S48 fates' gifts and costs.
			"add_pill_resistance": progression.apply_pill_resistance_all(actor_id, int(e.get("amount", 1)))
			"set_stability": progression.apply_stability(actor_id, str(e.get("word", "unstable")))
			"add_purity_grade": progression.apply_purity_grade(actor_id, int(e.get("amount", 1)))
			"throw": combat.apply_throw(actor_id, e)
			"add_body_xp": progression.apply_body_xp(actor_id, float(e.amount), source)
			"add_soul": progression.apply_soul(actor_id, float(e.amount))
			"add_insight": progression.apply_insight(actor_id, str(e.dao), float(e.amount), source)
			"heal": combat.apply_heal(actor_id, float(e.get("pct", 0)), float(e.get("amount", 0)), float(e.get("over_s", 0)), source)
			"restore_resource": combat.apply_resource_change(actor_id, str(e.pool), float(e.get("amount", 0)), source, float(e.get("pct", 0)))
			"add_composure": combat.apply_resource_change(actor_id, "composure", float(e.amount), source)
			"add_modifier": combat.apply_buff(actor_id, e, source)
			"apply_status": combat.apply_status(actor_id, str(e.status), float(e.get("duration", 1)), float(e.get("power", 0)), float(e.get("delay", 0)))
			"cure_status": combat.cure_status(actor_id, str(e.status))
			"cure_injury": progression.apply_cure_injury(actor_id, str(e.injury), int(e.get("max_severity", 3)))
			"add_toxicity": progression.apply_toxicity(actor_id, float(e.amount))
			"reset_meridians": progression.apply_reset_meridians(actor_id)
			"set_flag": quest.apply_flag(actor_id, str(e.flag))
			"clear_flag": quest.apply_clear_flag(actor_id, str(e.flag))
			"start_quest": quest.apply_start(actor_id, str(e.quest))
			"offer_quest": quest.apply_offer(actor_id, str(e.quest))
			"unlock_system": Unlocks.force_unlock(actor_id, str(e.system)) if OS.is_debug_build() else null
			"add_contribution": training.apply_contribution(actor_id, int(e.amount), source)
			"add_reputation": training.apply_reputation(actor_id, str(e.get("faction", "")), int(e.amount))
			"add_prestige": sect.apply_prestige(int(e.amount), source)
			"add_bond": pets.apply_bond(actor_id, float(e.amount))
			"send_mail": mail.apply_send(str(e.get("to", actor_id)), str(e.template), e.get("attachments", []), e.get("args", {}))
			"teleport": world.apply_teleport(actor_id, str(e.get("target", "")), str(e.get("portal", "")))
			"learn_technique": progression.apply_learn_technique(actor_id, str(e.technique))
			"learn_technique_for_weapon":
				var ch = character(actor_id)
				var w = ch.inventory.equipped.get("weapon") if ch else null
				var fam := str(ContentDB.item(str(w.id)).get("family", "none")) if w != null else "none"
				var opts: Dictionary = e.get("options", {})
				progression.apply_learn_technique(actor_id, str(opts.get(fam, opts.get("none", ""))))
			"learn_method": progression.apply_learn_method(actor_id, str(e.method))
			"learn_recipe": crafting.apply_learn_recipe(actor_id, str(e.recipe))
			"recipe_page": crafting.apply_recipe_page(actor_id, str(e.recipe), int(e.get("page", 1)))
			"learn_secret_art": progression.apply_learn_secret_art(actor_id, str(e.art))
			"event_passed": progression.apply_event_passed(actor_id, str(e.event))
			"grant_title": achievements.apply_title(actor_id, str(e.title))
			"swap_path":
				# S20: the Hall allows one change of path. Each side has its flag, token and title.
				var pc = character(actor_id)
				if pc == null: continue
				var to_free: bool = pc.quests.has_flag("path_alliance")
				quest.apply_clear_flag(actor_id, "path_alliance" if to_free else "path_independent")
				quest.apply_flag(actor_id, "path_independent" if to_free else "path_alliance")
				if to_free: inventory.apply_remove(actor_id, "alliance_token", 1, source)
				else: inventory.apply_add(actor_id, "alliance_token", 1, source)
				achievements.apply_title(actor_id, "free_cultivator" if to_free else "alliance_envoy")
			"join_sect": training.apply_join(actor_id, str(e.sect))
			"sect_rank": training.apply_rank(actor_id, str(e.rank))
			"grant_equipment": inventory.apply_add_equipment(actor_id, str(e.item), int(e.get("ilv", 0)), str(e.get("quality", "common")), source)
			"add_companion": companions.apply_add(actor_id, str(e.companion))
			"grant_pet": pets.apply_grant(actor_id, str(e.species))
			"choose_starter": pets.choose_starter(character(actor_id), str(e.species))
			"add_stability": progression.apply_stability(actor_id, str(e.value))
			"settle_consolidation": progression.apply_settle(actor_id)
			"add_purity": progression.apply_purity(actor_id, float(e.amount))
			"unlock_slot": accounts.apply_slot(int(e.get("slot", 0)))
			"codex": quest.apply_codex(str(e.entry))
			"start_daily":
				quest.start_daily(true)
				quest.start_weekly(true)
			"system_used": GameEvents.emit_event("system_used", {"actor": actor_id, "system": str(e.system)})
			"sect_defence_result": sect.apply_defence_result(actor_id, bool(e.get("won", true)))
			"voyage_arrive": world.apply_voyage_arrive(actor_id)
			"upgrade_sect_token":
				# Part 4 · Sage Sovereign 1: the training sect's token becomes an Elder's token.
				var tc = character(actor_id)
				if tc == null or tc.training_sect.is_empty(): continue
				var token := str(ContentDB.entry("sects", str(tc.training_sect.get("id", ""))).get("token", ""))
				if token == "" or tc.inventory.count(token.replace("_token", "_elder_token")) > 0: continue
				inventory.apply_add(actor_id, token.replace("_token", "_elder_token"), 1, source)
				training.apply_rank(actor_id, "elder")
			"open_dao": progression.apply_open_dao(actor_id, str(e.dao))
			"heal_pet_wound": pets.heal_wound(actor_id)
			"add_pet_purity": pets.apply_purity(actor_id, float(e.get("amount", 10)), source)
			"wash_pet_marrow": pets.wash_marrow(actor_id)
			"learn_pet_skill": pets.apply_learn(actor_id, str(e.get("skill", "")))
			"beast_tide_result": world.apply_tide_result(actor_id, bool(e.get("won", true)))
			"beast_trial_result": world.apply_trial_result(actor_id, bool(e.get("won", true)))
			_: push_warning("Unknown effect kind: " + str(e.get("kind", "")))

# ------------------------------------------------------------------ simulation
## One fixed simulation tick (called by the world scene every physics frame).
func tick(delta: float) -> void:
	if paused or not in_world or not is_finite(delta) or delta <= 0.0: return
	delta = minf(delta, 0.25)
	sim_time += delta
	tick_count += 1
	combat.tick(delta)
	progression.tick(delta)
	enemies.tick(delta)
	world.tick(delta)
	for a in [crafting, companions, pets, quest, economy, accounts, sect, training, achievements, mail, inventory]:
		a.tick(delta)
	_after_pass()
	if autosave_enabled:
		save_timer += delta
		if save_timer >= SAVE_INTERVAL:
			save_timer = 0.0
			save_all()

func _after_pass() -> void:
	GameEvents.flush()
	if GameEvents.unlock_pending:
		GameEvents.unlock_pending = false
		if active_id != "": Unlocks.evaluate(active_id)
		GameEvents.flush()
		GameEvents.unlock_pending = false
	if GameEvents.save_pending:
		GameEvents.save_pending = false
		if autosave_enabled and booted: save_all()

# ------------------------------------------------------------------ lifecycle
## Boot sequence (S35): load account and characters (recover from .bak), migrate,
## check the clock, then claim offline and idle time.
func boot() -> Dictionary:
	reset_state()
	var report := {"recovered": [], "migrated_v2": false, "new_account": false}
	var data := Saves.load_account()
	if data.is_empty():
		account = AccountState.new()
		account.account_id = "local-%d" % int(Clock.now_utc())
		account.rng_seed = int(Clock.now_utc()) & 0x7fffffff
		var v2 := Saves.read_v2()
		if not v2.is_empty():
			accounts.migrate_from_v2(Saves.migrate_v2_slots(v2))
			report.migrated_v2 = true
		else:
			report.new_account = true
	else:
		account.restore(data)
		for slot_key in account.characters:
			var cd := Saves.load_character(int(slot_key))
			if cd.is_empty(): continue
			var c := GameCharacter.new()
			c.restore(cd)
			c.id = "c%d" % c.slot
			characters[c.id] = c
			Rng.restore(c.id, c.rng_state, c.rng_seed if c.rng_seed != 0 else hash(c.id))
			StatRules.rebuild(c)
	Rng.restore("account", account.rng_state, account.rng_seed if account.rng_seed != 0 else 1)
	report.recovered = Saves.recovered_files().duplicate()
	booted = true
	GameEvents.flush()
	return report

func save_all() -> Error:
	if not booted: return OK
	var err := OK
	for id in characters:
		var c: GameCharacter = characters[id]
		c.rng_state = Rng.snapshot(c.id)
		c.last_active_utc = Clock.now_utc() if id == active_id else c.last_active_utc
		var e := Saves.save_character(c.slot, c.snapshot())
		if e != OK: err = e
		account.characters[str(c.slot)] = accounts.summary(c)
	account.clock.last_active_utc = Clock.now_utc()
	account.rng_state = Rng.snapshot("account")
	var ea := Saves.save_account(account.snapshot())
	if ea != OK: err = ea
	return err

## S40 · Manual export: save first so the file holds the latest state.
func export_save() -> String:
	save_all()
	var slots: Array = []
	for id in characters: slots.append(int(characters[id].slot))
	return Saves.export_bundle(slots)

func pause(value: bool) -> void:
	paused = value
