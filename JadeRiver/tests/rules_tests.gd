extends Node
## Rules, replay and offline suites (Part 7 · Quality gates).
##   Rules:   each formula at its sample values (monster pools, damage steps, gap
##            factors, mastery, risk, offline caps).
##   Replay:  same seed plus same intents gives the same state.
##   Offline: caps, a backward clock, bottlenecks hold, no breakthrough while away.
##   Pets:    stage gates need all three conditions, branches, traits, resonance, hunger.
##   Weekly:  Sect Service ends on either path and survives the daily reset.
##   Saves:   a damaged file is restored from its .bak; the migration stamps the version.
##   Hazards: the answer a room asks, the cycle, strikes, pushes, pools and shelter (S17).
## Run headless:  godot --headless --path . res://tests/rules_tests.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func near(a: float, b: float, eps := 0.01) -> bool:
	return absf(a - b) <= eps * maxf(1.0, absf(b))

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	rules_suite()
	replay_suite()
	offline_suite()
	pets_suite()
	weekly_suite()
	pills_suite()
	treasures_suite()
	hazards_suite()
	starsea_suite()
	movement_suite()
	g1_suite()
	g2_suite()
	traversal_suite()
	arts_volumes_suite()
	arts_combat_suite()
	nav_suite()
	emotes_suite()
	save_suite()
	print("rules_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ formulas
func rules_suite() -> void:
	# S13: HP_mob = (30 + 15L + 1.1L^2) x role; the spec's own check is 290 HP at Level 10.
	var normal := StatRules.mob_stats({"role": "normal"}, 10)
	check(near(normal.max_hp, 290.0), "normal monster at Level 10 has 290 HP (%.1f)" % normal.max_hp)
	check(near(normal.attack, 37.0), "normal monster attack at Level 10 is 37 (%.1f)" % normal.attack)
	var elite := StatRules.mob_stats({"role": "normal"}, 10, true)
	check(near(elite.max_hp, 290.0 * 6.0) and near(elite.attack, 37.0 * 1.5), "elites are 6x HP and 1.5x attack")
	var boss := StatRules.mob_stats({"role": "dungeon_boss"}, 18)
	check(near(boss.max_hp, (30.0 + 15.0 * 18 + 1.1 * 18 * 18) * 80.0), "dungeon bosses are 80x HP")
	check(near(StatRules.mob_stats({"role": "normal", "hp_mult": 0.5}, 10).max_hp, 145.0), "hp_mult scales one monster")
	# S13 kill progress gap factors: 5+ above x1.2, within 4 x1.0, 5-9 below x0.5, 10+ below x0.1.
	check(near(ProgressionRules.gap_factor(6), 1.2), "5+ levels above: x1.2")
	check(near(ProgressionRules.gap_factor(0), 1.0) and near(ProgressionRules.gap_factor(-4), 1.0), "within 4 levels: x1.0")
	check(near(ProgressionRules.gap_factor(-6), 0.5), "5-9 below: x0.5")
	check(near(ProgressionRules.gap_factor(-12), 0.1), "10+ below: x0.1")
	# S12 combat steps
	check(near(CombatRules.hit_chance(100.0, 0.0), 1.0), "hit chance caps at 100%")
	check(CombatRules.hit_chance(100.0, 1000.0) >= 0.55, "hit chance never below the floor")
	var dr := CombatRules.defence_reduction(1e9, 1, 0.0)
	check(dr <= 0.75 + 1e-6, "defence reduction caps at 75%% (%.3f)" % dr)
	check(CombatRules.defence_reduction(100.0, 10, 0.4) < CombatRules.defence_reduction(100.0, 10, 0.0), "penetration lowers defence")
	check(CombatRules.realm_gap_factor(3, 1) > 1.0 and CombatRules.realm_gap_factor(1, 3) < 1.0, "realm gap favours the higher realm")
	check(near(CombatRules.realm_gap_factor(2, 2), 1.0), "same realm: no gap factor")
	# S18 attunement at 0.5x, 1x and 1.15x the requirement; a zone that asks nothing changes nothing.
	var half := CombatRules.attunement_factors(5.0, 10.0)
	check(near(half.dealt, 0.65) and near(half.taken, 1.5), "attunement at half: 65%% dealt, 150%% taken")
	var full := CombatRules.attunement_factors(10.0, 10.0)
	check(near(full.dealt, 1.0) and near(full.taken, 1.0), "attunement met: no change")
	var over := CombatRules.attunement_factors(11.5, 10.0)
	check(near(over.dealt, 1.1) and near(over.taken, 1.0), "attunement 1.15x: dealt capped at 110%%")
	var none := CombatRules.attunement_factors(0.0, 0.0)
	check(near(none.dealt, 1.0) and near(none.taken, 1.0), "no requirement: no attunement factor")
	# S09 mastery doubles per tier; S05 risk words
	check(near(ProgressionRules.mastery_needed(1), 100.0) and near(ProgressionRules.mastery_needed(3), 400.0), "mastery 100 / 200 / 400")
	check(ProgressionRules.risk_index(0, false, 0, 0, false) == 0 and ProgressionRules.risk_index(5, true, 3, 0, false) == 3, "risk index clamps 0..3")
	check(ProgressionRules.risk_index(1, false, 0, 1, false) == 0, "a support cancels one unmet soft requirement")
	check(ProgressionRules.success_chance("low") > ProgressionRules.success_chance("severe"), "lower risk, better odds")
	# S07 offline window
	var span := ProgressionRules.offline_minutes(20.0 * 3600.0, 12.0)
	check(near(span.minutes, 720.0) and span.capped, "offline caps at 12 hours")
	check(near(ProgressionRules.offline_minutes(3600.0, 12.0).minutes, 60.0), "an hour away is an hour")
	# Body XP grows linearly per level (S29)
	check(ProgressionRules.body_xp_needed(5) > ProgressionRules.body_xp_needed(1), "body levels get dearer")

# ------------------------------------------------------------------ replay
## Two runs from the same seed with the same intents must end in the same state.
func _run_once(folder: String) -> String:
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # fixed "now"
	Clock.debug_offset_s = 0.0
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 12345
	Rng.restore("account", {}, 12345)
	Game.submit({"type": "create_character", "slot": 1, "name": "Replay", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	var c = Game.active()
	Rng.restore(c.id, {}, 777)
	Game.submit({"type": "enter_world"})
	var st := ActorState.new()
	Game.bind_movement(c.id, st)
	st.surface = Game.room_rt.geometry.surfaces[0]
	st.plane = Vector2(330, 780)
	# A fixed script of intents and ticks.
	for i in 400:
		if i % 20 == 0: Game.submit({"type": "basic_attack", "facing": 1})
		if i == 100: Game.submit({"type": "start_meditation"})
		if i == 300: Game.submit({"type": "stop_meditation"})
		Game.tick(0.05)
	var snap: Dictionary = c.snapshot()
	snap.erase("last_active_utc")
	return JSON.stringify(snap)

func replay_suite() -> void:
	var a := _run_once("user://replay_a/")
	var b := _run_once("user://replay_b/")
	check(a == b, "same seed and intents replay to the same character state")
	check(a.length() > 200, "replay produced a real snapshot")

# ------------------------------------------------------------------ offline
func offline_suite() -> void:
	var c = Game.active()
	if c == null:
		check(false, "offline suite needs a character")
		return
	var cu = c.cultivator
	# Seclusion is locked before Bone Forging 7: pretend we are there for the rule checks.
	cu.realm_key = "bone_forging_7"
	Game.progression.apply_learn_method(c.id, "riverbreath_fragment")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var before: float = cu.qp
	var r := Game.progression.claim_offline(c, -3600.0)
	check(r.get("ok", false) and near(cu.qp, before), "a backward clock gains nothing")
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	var r12: Dictionary = Game.progression.claim_offline(c, 12.0 * 3600.0)
	var gained_12: float = cu.qp - before
	cu.qp = before
	cu.state = "accumulating"
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 48.0 * 3600.0)
	var gained_48: float = cu.qp - before
	check(gained_12 > 0.0, "offline seclusion accumulates progress (%.1f)" % gained_12)
	check(near(gained_48, gained_12, 0.02) or cu.state == "bottleneck", "offline gains stop at the 12-hour cap")
	# Offline never breaks through: fill to the bottleneck and claim a long absence.
	cu.qp = cu.need() * 0.99
	cu.state = "accumulating"
	var realm_before: String = cu.realm_key
	c.seclusion = {"spot": "lf_village", "focus": "accumulate", "started_utc": Clock.now_utc(), "cap_h": 12, "density": 1.0}
	Game.progression.claim_offline(c, 12.0 * 3600.0)
	check(cu.realm_key == realm_before, "offline progress never breaks through")
	check(cu.state == "bottleneck" or cu.qp <= cu.need(), "a full bar waits at the bottleneck")
	# Offline factor: realm progress while away is 10% of the meditation rate.
	var rate := ProgressionRules.meditation_rate(c, 1.0, Game.progression.accumulation_bonus(c))
	check(near(float(r12.get("gains", {}).get("qp", 0.0)), rate * float(ContentDB.curve("offline_factor", 0.1)) * 720.0, 0.05), "offline factor 0.1 of the meditation rate")
	Clock.override_utc = -1.0

# ------------------------------------------------------------------ pets (S22)
func pets_suite() -> void:
	var c = Game.active()
	if c == null:
		check(false, "pet suite needs a character")
		return
	c.cultivator.realm_key = "qi_unfurling_5"
	Game.pets.apply_grant(c.id, "reed_otter")
	var p: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(p.uid)
	check((p.traits as Array).size() == 3 and int(p.revealed) == 0, "a new animal carries three hidden traits")
	# Juvenile: Level 15, 3 hearts, owner at Heart Tempering. Each gate alone is not enough.
	p.level = 15
	p.bond = 1.0
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "level alone does not evolve")
	p.bond = 3.0
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "level and hearts without the owner's realm do not evolve")
	c.cultivator.realm_key = "heart_tempering_1"
	p.level = 14
	check(not Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false), "hearts and realm without the level do not evolve")
	p.level = 15
	check(Game.submit({"type": "evolve_pet", "pet": p.uid}).get("ok", false) and str(p.stage) == "juvenile", "all three gates: Hatchling to Juvenile")
	check(int(p.revealed) == 1 and Game.pets.revealed_traits(p).size() == 1, "Juvenile reveals the first trait")
	# Adult needs a branch from the species.
	p.level = 35
	p.bond = 5.0
	c.cultivator.realm_key = "spirit_awakening_1"
	check(Game.submit({"type": "evolve_pet", "pet": p.uid}).get("reason", "") == "choose_branch", "Adult asks for a branch")
	check(Game.submit({"type": "evolve_pet", "pet": p.uid, "branch": "Tide Otter"}).get("ok", false) and str(p.branch) == "Tide Otter", "Adult takes one of the two branches")
	# Resonance: Cultivation role from Spirit Awakening 1, Adult +10%; hunger costs 30%.
	p.role = "cultivation"
	p.hunger_day = Clock.reset_day(Clock.now_utc())
	var fed: float = Game.pets.resonance(c) - Game.pets.trait_bonus(c, "resonance")
	check(near(fed, 0.10), "Adult resonance is +10%% (%.3f)" % fed)
	p.hunger_day = Clock.reset_day(Clock.now_utc()) - 2
	check(near(Game.pets.care_mult(p), 0.7), "a hungry animal works at 70%")
	check(Game.progression.accumulation_bonus(c) >= Game.pets.resonance(c) - 0.0001, "resonance feeds accumulation")
	p.role = "combat"
	check(near(Game.pets.resonance(c), 0.0), "no resonance outside the Cultivation role")
	# Rarity scales strength; breeding pairs two Adults of one family (Heaven Glimpse 1, Beast Pavilion 4).
	p.rarity = "rare"
	check(near(Game.pets.rarity_power(p), 1.25), "a Rare animal is 25% stronger")
	p.rarity = "common"
	Game.pets.apply_grant(c.id, "mossback_toad")
	var toad: Dictionary = c.pets[c.pets.size() - 1]
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	toad.stage = "adult"
	fox.stage = "adult"
	toad.rarity = "fine"
	c.eggs.clear()
	var sect_before: Dictionary = Game.account.sect.duplicate(true)
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("reason", "")) == "locked", "breeding waits for its unlock")
	Unlocks.force_unlock(c.id, "pet_breeding")
	Game.account.sect = {"name": "Test", "level": 4, "buildings": {"beast_pavilion": 3}}
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("text", "")).contains("Beast Pavilion"), "breeding needs Beast Pavilion 4")
	Game.account.sect.buildings.beast_pavilion = 4
	check(str(Game.pets.breed(c, str(p.uid), str(fox.uid)).get("reason", "")) == "not_a_pair", "an otter and a fox are not one family")
	check(Game.pets.breed_partners(c, p).has(toad) and not Game.pets.breed_partners(c, p).has(fox), "otter and toad are both river animals")
	Clock.override_utc = 1900000000.0
	var br: Dictionary = Game.pets.breed(c, str(p.uid), str(toad.uid))
	check(br.get("ok", false) and c.eggs.size() == 1 and c.eggs[0].get("bred", false), "two river Adults make an egg %s" % str(br))
	var egg: Dictionary = c.eggs[0] if not c.eggs.is_empty() else {}
	var order := ["common", "fine", "rare", "epic", "primordial"]
	check(order.find(str(egg.get("rarity", ""))) >= 1, "the child takes at least the higher parent rarity (%s)" % str(egg.get("rarity", "")))
	var parent_traits: Array = (p.traits as Array) + (toad.traits as Array)
	var inherited: int = (egg.get("traits", []) as Array).filter(func(t): return parent_traits.has(t)).size()
	check((egg.get("traits", []) as Array).size() == 3 and inherited >= 2, "its traits come from the parents, at most one new")
	check(float(egg.get("hatch_utc", 0.0)) - Clock.now_utc() >= 26.0 * 3600.0 - 1.0, "breeding takes a day before the egg can hatch")
	check(str(Game.pets.breed(c, str(p.uid), str(toad.uid)).get("reason", "")) == "locked", "one pair at a time")
	check(not Game.pets.hatch_egg(c, 0).get("ok", false), "the egg is not ready yet")
	Clock.override_utc += 49.0 * 3600.0
	var n_before: int = c.pets.size()
	check(Game.pets.hatch_egg(c, 0).get("ok", false) and c.pets.size() == n_before + 1, "the bred egg hatches")
	var child: Dictionary = c.pets[c.pets.size() - 1]
	check(str(child.rarity) == str(egg.get("rarity", "")) and child.traits == egg.get("traits", []), "the hatchling keeps the egg's rarity and traits")
	check(str(child.species) in ["reed_otter", "mossback_toad"], "and one parent's species")
	Clock.override_utc = -1.0
	Game.account.sect = sect_before

# ------------------------------------------------------------------ weekly mission (S20)
func weekly_suite() -> void:
	var c = Game.active()
	if c == null: return
	Game.quest.start_weekly(true)
	var id := "weekly_%d" % Clock.reset_week(Clock.now_utc())
	check(c.quests.is_active(id), "Sect Service is offered for the week")
	Game.quest.start_daily(true)
	check(c.quests.is_active(id), "the daily reset leaves the weekly mission alone")
	# Either path finishes it: here, one field boss.
	GameEvents.emit_event("actor_defeated", {"victim": "0", "victim_kind": "enemy", "def": "cloudpeak_roc", "role": "field_boss", "killer": c.id, "level": 40,
		"room": str(c.position.get("room", "")), "x": 400.0, "y": 800.0, "alt": 0.0, "elite": false, "summoned": false, "first_hit_by_player": true})
	GameEvents.flush()
	check(c.quests.done.has(id) and not c.quests.is_active(id), "a field boss completes Sect Service")
	Game.quest.start_weekly(true)
	check(not c.quests.is_active(id), "Sect Service is offered once a week")

# ------------------------------------------------------------------ pill qualities (S15)
func _pill_stacks(c, id: String) -> Array:
	var out: Array = []
	for i in c.inventory.bag.size():
		var s = c.inventory.bag[i]
		if s != null and str(s.id) == id: out.append(i)
	return out

func _use_fresh(c, index: int) -> Dictionary:
	c.pools.cooldowns.clear()
	c.cultivator.toxicity = 0.0
	c.cultivator.pill_memory.clear()
	return Game.inventory.use_item(c, index, true)

func pills_suite() -> void:
	var c = Game.active()
	if c == null: return
	c.cultivator.realm_key = "heart_tempering_1"
	var pill := "healing_pill"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.inventory.apply_add(c.id, pill, 2, "test")
	Game.inventory.apply_add(c.id, pill, 2, "test", {"quality": "pill_grain"})
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "pill_grain"})
	var idx := _pill_stacks(c, pill)
	check(idx.size() == 2 and int(c.inventory.bag[idx[1]].count) == 3, "a Pill Grain stacks apart from Common pills")
	check(c.inventory.count(pill) == 5, "the bag counts every quality of a pill")
	check(not c.inventory.bag[idx[0]].has("quality"), "a Common pill is a plain stack (older saves read unchanged)")
	Game.inventory.move_item(c, idx[1], idx[0])
	check(_pill_stacks(c, pill).size() == 2, "moving a Pill Grain onto Common pills swaps instead of merging")
	check(near(InventoryAuthority.pill_potency({"id": pill}), 1.0) and near(InventoryAuthority.pill_potency({"id": pill, "quality": "flawed"}), 0.5)
		and near(InventoryAuthority.pill_potency({"id": pill, "quality": "pill_soul"}), 2.2), "potency: Flawed 50%, Common 100%, Pill Soul 220%")
	var grain := -1
	for i in _pill_stacks(c, pill):
		if str(c.inventory.bag[i].get("quality", "")) == "pill_grain": grain = i
	var used := _use_fresh(c, grain)
	check(near(float(used.get("factor", 0.0)), 1.8), "a Pill Grain works at 180%% (%s)" % str(used))
	check(near(c.cultivator.toxicity, float(ContentDB.item(pill).pill.toxicity) * 0.5), "and leaves half the toxicity")
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "flawed"})
	var flawed := -1
	for i in _pill_stacks(c, pill):
		if str(c.inventory.bag[i].get("quality", "")) == "flawed": flawed = i
	_use_fresh(c, flawed)
	check(near(c.cultivator.toxicity, float(ContentDB.item(pill).pill.toxicity) * 1.5), "a Flawed pill poisons more")
	# Grain, Halo and Soul need every strike perfect, from Heart Tempering 1 (perfect timing).
	Unlocks.force_unlock(c.id, "perfect_timing")
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	check(Game.crafting._rare_pill_quality(c, [0.95, 0.6, 0.95], rng) == "perfect", "one imperfect strike: no rare quality")
	check(Game.crafting._rare_pill_quality(c, [1.0, 1.0], rng) == "perfect", "an unfinished run: no rare quality")
	var got := {}
	for i in 4000:
		var q := Game.crafting._rare_pill_quality(c, [1.0, 0.9, 0.95], rng)
		got[q] = int(got.get(q, 0)) + 1
	var boost: float = 1.0 + Game.crafting.furnace_bonus(c) + 0.1 * int(c.cultivator.daos.get("alchemy", {}).get("tier", 0))
	var rare: Dictionary = ContentDB.config("grades").pill.rare
	check(near(float(got.get("pill_grain", 0)) / 4000.0, float(rare.pill_grain) * boost, 0.03), "a perfect run rolls Pill Grain about %d%% of the time (%s)" % [int(float(rare.pill_grain) * boost * 100), str(got)])
	check(got.has("pill_halo") and got.has("pill_soul") and int(got.get("pill_soul", 0)) < int(got.get("pill_halo", 0)), "Halo is rarer than Grain, Soul rarer still")
	# Pill Halo grows 1% a day in a storage chest in a room of Qi density 2 or more, up to +20% (S44).
	var day := 86400.0
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 5 * day, "stored_density": 1.0}), 0.0),
		"a Pill Halo stored in thin Qi does not grow")
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 5.5 * day, "stored_density": 2.2}), 0.05),
		"five days in a dense-Qi chest: Halo +5%")
	check(near(InventoryAuthority.halo_now({"quality": "pill_halo", "stored_utc": Clock.now_utc() - 60 * day, "stored_density": 2.2}), 0.2),
		"Halo growth stops at +20% (240% potency)")
	Unlocks.force_unlock(c.id, "storage")
	var dens0 = Game.room_rt.def.get("qi_density", 1.0)
	Game.room_rt.def.qi_density = 2.2
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	Game.inventory.apply_add(c.id, pill, 1, "test", {"quality": "pill_halo"})
	var n_store: int = Game.account.storage.get("items", []).size()
	check(Game.accounts.deposit(c, _bag_index(c, pill), 1).get("ok", false), "a Halo pill goes into the storage chest")
	Game.room_rt.def.qi_density = dens0
	var stored: Dictionary = Game.account.storage.items[n_store]
	stored.stored_utc = float(stored.stored_utc) - 10 * day
	Game.accounts.withdraw(c, n_store)
	var halo_i := _bag_index(c, pill)
	check(halo_i >= 0 and near(float(c.inventory.bag[halo_i].get("halo", 0.0)), 0.1) and not c.inventory.bag[halo_i].has("stored_utc"),
		"taken out after ten days in the pavilion's chest: Halo +10%")
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# A Pill Soul always carries its recipe's own unique effect.
	Game.inventory.apply_add(c.id, pill, 8, "test", {"quality": "pill_soul"})
	var awakened := 0
	for n in 8:
		var soul := -1
		for i in _pill_stacks(c, pill):
			if str(c.inventory.bag[i].get("quality", "")) == "pill_soul": soul = i
		if soul < 0: break
		if str(_use_fresh(c, soul).get("soul_effect", "")) != "": awakened += 1
	check(awakened == 8 and str(ContentDB.item(pill).get("soul_effect", "")) == "mend_meridians", "a Healing Pill Soul mends the meridians, every time (%d of 8)" % awakened)
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null

# ------------------------------------------------------------------ natural treasures (Part 5)
func treasures_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu = c.cultivator
	cu.realm_key = "spirit_awakening_8"
	cu.state = "accumulating"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	c.pools.cooldowns.clear()
	# Mindwell Lotus: +500 Soul, once in each great realm.
	Game.inventory.apply_add(c.id, "mindwell_lotus", 2, "test")
	var soul0: float = cu.soul_cultivation
	check(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("ok", false) and near(cu.soul_cultivation, soul0 + 500.0),
		"the Mindwell Lotus adds 500 Soul")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("reason", "")) == "once_per_realm", "a second lotus in the same great realm is refused")
	cu.realm_key = "heaven_glimpse_1"
	c.pools.cooldowns.clear()
	check(Game.inventory.use_item(c, c.inventory.first_index("mindwell_lotus"), true).get("ok", false), "the next great realm, the lotus answers again")
	check(ContentDB.item("mindwell_lotus").get("sell", true) == false and ContentDB.item("evergreen_heart_fruit").get("sell", true) == false, "natural treasures are never sold")
	cu.realm_key = "spirit_awakening_8"
	# Evergreen Heart Tree: planted once, first fruit after a day, then one per season.
	Clock.override_utc = 1800000000.0
	c.crafting.erase("evergreen")
	var plot := {"id": "plot_test", "type": "treasure_plot"}
	check(str(Game.crafting.tend_treasure_plot(c, plot).get("text", "")) == Tx.t("sim.crafting.rich_earth_waits"), "rich earth waits for a seed")
	Game.inventory.apply_add(c.id, "evergreen_heart_seed", 1, "test")
	Game.crafting.tend_treasure_plot(c, plot)
	check(bool(Game.crafting.evergreen_state(c).planted) and c.inventory.count("evergreen_heart_seed") == 0, "the seed is planted")
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 0, "no fruit on the first day")
	Clock.override_utc += 25.0 * 3600.0
	Game.crafting.tend_treasure_plot(c, plot)
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 1, "one fruit after a day, and only one")
	Clock.override_utc += 7.0 * 86400.0
	Game.crafting.tend_treasure_plot(c, plot)
	check(c.inventory.count("evergreen_heart_fruit") == 2, "another fruit the next season")
	check(str(Game.crafting.tend_treasure_plot(c, {"id": "elsewhere", "type": "treasure_plot"}).get("text", "")).contains("grows in"), "one tree per character")
	# The fruit lifts you from a grave wound where you fell, at full health.
	Game.combat._gravely_wound(c, "hp")
	c.pools.hp = 0.0
	check(Game.combat.choose_revival(c, "fruit").get("ok", false) and near(c.pools.hp, c.pools.max_hp) and c.inventory.count("evergreen_heart_fruit") == 1,
		"an Evergreen Heart fruit revives in place at full health")
	check(not Game.combat.is_wounded(c.id), "and the wound is gone")
	Clock.override_utc = -1.0
	# Nine-Bough Jade Tree: only at an Understanding bottleneck, once per realm stage.
	cu.realm_key = "spirit_awakening_9"
	Unlocks.force_unlock(c.id, "dao_tree")
	cu.daos = {"sword": {"tier": 3, "insight": 900.0}}
	cu.state = "accumulating"
	check(str(Game.progression.consult_jade_tree(c).get("text", "")) == Tx.t("sim.progression.the_jade_leaves_are_still"), "no answer away from a bottleneck")
	cu.state = "bottleneck"
	var jt: Dictionary = Game.progression.consult_jade_tree(c)
	var gained := float(cu.daos.sword.insight) - 900.0
	check(gained >= 0.75 * 1100.0 - 1.0, "at the Dao-tier wall it gives three quarters of the gap to the next tier (%.0f, %s)" % [gained, str(jt)])
	var ins: float = float(cu.daos.sword.insight)
	Game.progression.consult_jade_tree(c)
	check(near(float(cu.daos.sword.insight), ins), "the tree answers once per realm stage")
	cu.state = "accumulating"
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# Library floor 3 formations (S16): Restraint slows monsters 30%, Concealment hides you.
	var here := str(c.position.get("room", ""))
	var saved: Array = c.crafting.get("formations", []).duplicate(true)
	c.crafting.formations = [{"type": "restraint", "room": here, "until_utc": Clock.now_utc() + 3600.0},
		{"type": "concealment", "room": here, "until_utc": Clock.now_utc() + 3600.0}]
	check(near(Game.workshop.formation_effect(c, "enemy_slow"), 0.3) and Game.workshop.formation_effect(c, "conceal") > 0.0, "Restraint and Concealment take effect where they stand")
	c.crafting.formations[0].until_utc = Clock.now_utc() - 1.0
	check(near(Game.workshop.formation_effect(c, "enemy_slow"), 0.0), "an unfuelled formation does nothing")
	c.crafting.formations = saved

# ------------------------------------------------------------------ hazards (S17)
## Run a hazard to the end of its phase and one tick on.
func _hazard_step(hs: Dictionary) -> void:
	hs.t = float(hs.dur) + 0.01
	Game.tick(0.05)

func _hazard_room(c, room: String, at: Vector2) -> Dictionary:
	Game.world.apply_teleport(c.id, room)
	var st: ActorState = Game.actor_state(c.id)
	for s in Game.room_rt.geometry.surfaces:
		if s.stratum == "ground" and s.contains(at): st.surface = s
	st.plane = at
	st.altitude = 0.0
	Game.combat.cure_status(c.id, "spawn_protection")
	for s in ["stun", "slow", "shock", "bleed", "poison"]: Game.combat.cure_status(c.id, s)
	c.pools.invulnerable = 0.0   # i-frames left over from the revival checks above
	c.pools.hp = c.pools.max_hp
	var hid: String = str(Game.room_rt.def.get("hazards", [""])[0])
	return Game.room_rt.hazards.get(hid, {})

## Pin an attribute for a check (override), or release it (value < 0).
func _answer(c, stat: String, value: float) -> void:
	c.stats.remove_source("test_hazard")
	if value >= 0.0: c.stats.add_modifier({"stat": stat, "op": "override", "value": value, "duration": 600.0, "source": "test_hazard"})
	Game.combat.refresh_stats(c.id)

## Run the cycle round to the start of the next active phase.
func _hazard_to_active(hs: Dictionary, on: Vector2 = Vector2.INF) -> void:
	for i in 5:
		_hazard_step(hs)
		if hs.phase == "tell" and on.is_finite(): hs.spots = [[on.x, on.y, 0.0]] + hs.spots.slice(1)
		if hs.phase == "active": return

func hazards_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	var gust := ContentDB.entry("hazards", "wind_gust")
	check(HazardRules.need(gust, ContentDB.room("gc_windbridge")) == 116, "the Windbridge's gusts ask Body 116 (1.4 x (5 + 78))")
	check(near(HazardRules.effect_scale(0.0, 100.0), 1.0) and near(HazardRules.effect_scale(50.0, 100.0), 0.75) and HazardRules.effect_scale(100.0, 100.0) == 0.0,
		"a hazard's push or status falls to half as the answer nears and stops once it is met")
	check(near(HazardRules.damage_scale(120.0, 100.0), 0.35) and near(HazardRules.damage_scale(0.0, 100.0), 1.0), "an answered strike still lands, at 35%")
	var events: Array = []
	var grab := func(n, p): if str(n).begins_with("hazard_"): events.append([str(n), p])
	GameEvents.event.connect(grab)
	# Falling rocks: a quiet tell, a warning, then the strike on the marked spot.
	var spot := Vector2(900, 820)
	var hs := _hazard_room(c, "sq_quarry_rim", spot)
	_answer(c, "body", 1.0)
	check(hs.get("phase", "") == "cooldown", "hazards start in their cooldown: nothing falls on arrival")
	_hazard_step(hs)
	check(hs.phase == "tell" and hs.spots.size() == 2, "the quiet tell picks two spots")
	hs.spots[0] = [spot.x, spot.y, 0.0]
	_hazard_step(hs)
	GameEvents.flush()
	check(hs.phase == "warn" and events.any(func(e): return e[0] == "hazard_warned"), "a warning comes before the strike")
	var hp0: float = c.pools.hp
	_hazard_step(hs)
	check(hs.phase == "active" and c.pools.hp < hp0 and c.pools.has_status("stun"), "the rock lands on the marked spot and stuns (%.0f)" % (hp0 - c.pools.hp))
	var full_hit: float = (hp0 - c.pools.hp) / c.pools.max_hp   # as a share of max HP: Body also raises max HP
	# Answered: Body over the need, the blow is lighter and nothing stuns.
	_answer(c, "body", 400.0)
	Game.combat.cure_status(c.id, "stun")
	c.pools.hp = c.pools.max_hp
	hp0 = c.pools.hp
	events.clear()
	_hazard_to_active(hs, spot)
	GameEvents.flush()
	var struck: Array = events.filter(func(e): return e[0] == "hazard_struck")
	check(c.pools.hp < hp0 and (hp0 - c.pools.hp) / c.pools.max_hp < full_hit * 0.6 and not c.pools.has_status("stun"), "answered, the rock hurts less and does not stun")
	check(not struck.is_empty() and struck[-1][1].get("answered", false), "the blow is reported as answered")
	_answer(c, "body", 1.0)
	# A dodge through the strike avoids it.
	c.pools.hp = c.pools.max_hp
	hs.phase = "warn"
	hs.spots = [[spot.x, spot.y, 0.0]]
	Game.combat.timeline(c.id).dodge_t = 0.3
	_hazard_step(hs)
	check(near(c.pools.hp, c.pools.max_hp), "a dodge through the strike avoids it")
	Game.combat.timeline(c.id).dodge_t = 0.0
	# Wind gusts push downwind while active, less for a stronger body, not at all once answered.
	hs = _hazard_room(c, "gc_windbridge", Vector2(1500, 820))
	_answer(c, "body", 58.0)
	_hazard_to_active(hs)
	var push := Game.world.hazard_drift(c.id)
	check(near(absf(push.x), 230.0 * 0.75) and signf(push.x) == float(hs.dir), "a gust pushes downwind, three quarters as hard for half the Body (%.0f px/s)" % push.x)
	_answer(c, "body", 400.0)
	Game.tick(0.05)
	check(Game.world.hazard_drift(c.id) == Vector2.ZERO, "an answering Body holds its footing")
	_answer(c, "body", 1.0)
	# The rapids pull downstream in the shallows, harder in a surge.
	hs = _hazard_room(c, "wg_rapids_terraces", Vector2(1500, 920))
	Game.tick(0.05)
	var calm_pull := Game.world.hazard_drift(c.id).x
	_hazard_to_active(hs)
	var surge_pull := Game.world.hazard_drift(c.id).x
	check(calm_pull < 0.0 and surge_pull < calm_pull * 2.0, "the shallows pull downstream, harder in a surge (%.0f, %.0f)" % [calm_pull, surge_pull])
	Game.actor_state(c.id).plane = Vector2(1500, 700)
	Game.tick(0.05)
	check(Game.world.hazard_drift(c.id) == Vector2.ZERO, "out of the water, no pull")
	# Hollow puddles taint and slow whoever stands in them while they rise.
	hs = _hazard_room(c, "rm_grey_pools", Vector2(600, 900))
	_answer(c, "spirit", 1.0)
	var hol: float = c.pools.hollowing
	_hazard_to_active(hs)
	check(c.pools.hollowing > hol and c.pools.has_status("slow"), "a Hollow puddle taints and slows")
	_answer(c, "body", 1.0)
	# Bitter cold slows in the open; a shrine shelters.
	hs = _hazard_room(c, "rf_rimefrost_summit", Vector2(1600, 820))
	_hazard_to_active(hs)
	check(c.pools.has_status("slow"), "the freezing blast stiffens the limbs in the open")
	hs = _hazard_room(c, "rf_rimefrost_summit", Vector2(360, 760))
	_hazard_to_active(hs)
	check(not c.pools.has_status("slow"), "a shrine gives shelter from the cold")
	# Safe rooms never carry hazards; the map lists what a room asks.
	var bad: Array = []
	for id in ContentDB.rooms:
		var r: Dictionary = ContentDB.rooms[id]
		if r.get("safe", false) and not r.get("hazards", []).is_empty(): bad.append(id)
	check(bad.is_empty(), "no hazards in safe rooms %s" % str(bad))
	var sm: Array = HazardRules.summary(c, ContentDB.room("sr_windswept_ridge"))
	check(sm.size() == 1 and str(sm[0].stat) == "body" and int(sm[0].need) == 91, "the map shows the ridge's gusts and the Body they ask (91)")
	GameEvents.event.disconnect(grab)
	_answer(c, "", -1.0)
	for s in ["stun", "slow", "shock", "bleed", "poison"]: Game.combat.cure_status(c.id, s)
	c.pools.hollowing = 0.0
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ the Starsea and Act II systems (v1.1)
func starsea_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	# S18: a dock asks for the Starsea's survival (Sage 3), a vessel and the route's chart, in that order.
	Game.world.apply_teleport(c.id, "ae_skydock")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "wrong_dock", "a route sails only from its own dock")
	Game.world.apply_teleport(c.id, "ae_shipyard")
	var had := Unlocks.is_unlocked(c.id, "starsea")
	if not had: check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "locked", "the Starsea is closed before Sage 3")
	Unlocks.force_unlock(c.id, "starsea")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "no_vessel", "no vessel, no voyage")
	Game.inventory.apply_add(c.id, "cloud_skiff", 1, "test")
	check(str(Game.world.set_sail(c, "wreck_run").get("reason", "")) == "no_chart", "no chart, no voyage")
	Game.inventory.apply_add(c.id, "star_chart_wreck", 1, "test")
	var r := Game.world.set_sail(c, "wreck_run")
	check(r.get("ok", false) and Game.room_rt.room_id == "ss_starsea_crossing" and near(float(Game.room_rt.event.remaining), 70.0, 0.5),
		"a skiff crosses the Wreck Run in 70 s")
	Game.room_rt.event.remaining = 0.01
	Game.tick(0.05)
	GameEvents.flush()
	check(Game.room_rt.room_id == "sw_broken_pier", "the crossing ends in port at the Broken Pier")
	Game.inventory.apply_add(c.id, "storm_sloop", 1, "test")
	r = Game.world.set_sail(c, "wreck_run_home")
	check(r.get("ok", false) and near(float(Game.room_rt.event.remaining), 70.0 / 1.5, 0.5), "a storm sloop crosses half again as fast")
	Game.world.apply_teleport(c.id, "ae_shipyard")
	check(not Game.world.voyages.has(c.id), "leaving the crossing abandons the voyage")
	Game.world.apply_teleport(c.id, "sw_starsea_launch")
	check(str(Game.world.set_sail(c, "lantern_run").get("reason", "")) == "planned", "the Lantern Run waits for the next act")
	for k in ["cloud_skiff", "storm_sloop", "star_chart_wreck"]: Game.inventory.apply_remove(c.id, k, 1, "test")
	# The star wind strips Qi; Spirit holds it in.
	if c.pools.max_qi > 0.0:
		var hs := _hazard_room(c, "sw_riven_peak", Vector2(1500, 820))
		hs = Game.room_rt.hazards.get("star_wind", {})
		_answer(c, "spirit", 1.0)
		c.pools.qi = c.pools.max_qi
		_hazard_to_active(hs)
		check(c.pools.qi < c.pools.max_qi * 0.97, "the star wind strips Qi (%.0f%%)" % (100.0 * c.pools.qi / c.pools.max_qi))
		_answer(c, "spirit", 9999.0)
		c.pools.qi = c.pools.max_qi
		_hazard_to_active(hs)
		_hazard_to_active(hs)
		check(near(c.pools.qi, c.pools.max_qi, 1.0), "enough Spirit keeps every drop of it")
		_answer(c, "", -1.0)
	# The Presence of the eight seats is answered by Will (S17 Weight zones).
	var pres := ContentDB.entry("hazards", "presence")
	check(str(pres.answer) == "will" and HazardRules.need(pres, ContentDB.room("si_presence_trial")) == 189, "the Presence Trial asks Will 189 (2.2 x (5 + 81))")
	# S18: an Expanse Outpost lends every member of the sect its Storm Ward.
	var saved: Dictionary = Game.account.sect.duplicate(true)
	var base := Game.progression.attunement_value(c, "azure_expanse")
	Game.account.sect = {"level": 8, "buildings": {"expanse_outpost": 3}, "damaged": {}}
	check(near(Game.progression.attunement_value(c, "azure_expanse") - base, 3.0), "an Expanse Outpost at level 3 adds 3 Storm Ward")
	check(Game.sect.outpost_attunement("jade_river_valley") == 0.0, "and nothing in the valley")
	Game.account.sect = saved
	# Paired cultivation only while meditating.
	check(Game.companions.paired_bonus(c) == 0.0, "no paired bonus while not meditating")
	# Rare Daos: closed until a teacher opens them; each tier adds its modifiers. Zone caps: the Expanse's Laws go deeper.
	Game.world.apply_teleport(c.id, "ae_landing")
	Unlocks.force_unlock(c.id, "dao_tree")
	var daos_saved: Dictionary = c.cultivator.daos.duplicate(true)
	c.cultivator.daos.erase("blood")
	Game.progression.apply_insight(c.id, "blood", 500.0, "test:blood:a")
	check(not c.cultivator.daos.has("blood"), "a rare Dao cannot be contemplated before a teacher opens it")
	StatRules.rebuild(c)
	var hp0: float = c.stats.value("max_hp")
	Game.progression.apply_open_dao(c.id, "blood")
	StatRules.rebuild(c)
	check(int(c.cultivator.daos.get("blood", {}).get("tier", 0)) == 1 and c.stats.value("max_hp") > hp0 * 1.04,
		"a teacher opens the Blood Dao at tier 1: +5%% max HP (%.0f -> %.0f)" % [hp0, c.stats.value("max_hp")])
	Game.world.apply_teleport(c.id, "lf_village")
	c.cultivator.daos["thunder"] = {"tier": 0, "insight": 0.0}
	Game.progression.apply_insight(c.id, "thunder", 3000.0, "test:thunder:valley")
	var valley_tier := int(c.cultivator.daos.thunder.tier)
	Game.world.apply_teleport(c.id, "ae_landing")
	Game.progression.apply_insight(c.id, "thunder", 10.0, "test:thunder:expanse")
	check(valley_tier == 2 and int(c.cultivator.daos.thunder.tier) == 4, "the Thunder Dao stops at tier 2 in the valley and deepens in the Expanse (%d, %d)" % [valley_tier, int(c.cultivator.daos.thunder.tier)])
	c.cultivator.daos = daos_saved
	StatRules.rebuild(c)
	# The Elder's token (Sage Sovereign 1): home to the training sect for no shards.
	if not c.training_sect.is_empty():
		var sid := str(c.training_sect.id)
		var stone := "jade_academy" if sid == "jade_sect" else "cloud_monastery"
		var fee := Game.world.teleport_fee(stone, c)
		Game.apply_effects(c.id, [{"kind": "upgrade_sect_token"}], "test")
		check(fee > 0 and Game.world.teleport_fee(stone, c) == 0, "an Elder's token calls its bearer home for free")
		Game.inventory.apply_remove(c.id, sid.replace("_sect", "") + "_elder_token", 1, "test")
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ world movement (S17, S30)
## Run the real solver: the body leaves the ground with `jumps` presses (the second at the top of the
## first) while drifting toward `toward`; returns the surface it comes to rest on.
func _jump_to(geo: ZoneGeometry, from: Vector2, toward: Vector2, jumps: int) -> ActorState:
	var st := ActorState.new()
	st.plane = from
	st.surface = geo.landing_target(from, 1.0, -1.0)
	st.altitude = 0.0
	MovementSolver.jump(st)
	var pressed := 1
	for i in 240:
		var v := (toward - st.plane).limit_length(1.0) * 205.0 if st.plane.distance_to(toward) > 4.0 else Vector2.ZERO
		MovementSolver.advance(st, geo, 1.0 / 60.0, v)
		if pressed < jumps and st.surface == null and st.vertical_speed <= 0.0:
			MovementSolver.jump(st)
			pressed += 1
		if st.surface != null and i > 5: break
	return st

func movement_suite() -> void:
	var c = Game.active()
	if c == null: return
	var back := str(c.position.get("room", "lf_village"))
	check(near(MovementSolver.JUMP_IMPULSE * MovementSolver.JUMP_IMPULSE / (2.0 * MovementSolver.GRAVITY), 122.1, 0.5),
		"a single jump peaks at 122 units; Cloud Ladder Step adds 80 (about 202)")
	# A field made climbable: a jump onto the low ledge, a double jump onto the high one (where the chest waits).
	Game.world.apply_teleport(c.id, "tp_thunderhorn_flats")
	var geo: ZoneGeometry = Game.room_rt.geometry
	var low: WalkSurface = geo.index.get("ledge_mv_0")
	var high: WalkSurface = geo.index.get("ledge_mv_1")
	check(low != null and high != null and geo.index.has("cloud_mv"), "the Thunderhorn Flats have ledges and a cloud ledge")
	if low and high:
		var under := Vector2(low.bounds.get_center().x, low.bounds.end.y + 30.0)
		var st1 := _jump_to(geo, under, low.bounds.get_center(), 1)
		check(st1.surface == low and near(st1.altitude, 100.0, 0.5), "one jump lands on the 100-unit ledge (%s)" % (st1.surface.id if st1.surface else "air"))
		var st1b := _jump_to(geo, Vector2(high.bounds.get_center().x, high.bounds.end.y + 30.0), high.bounds.get_center(), 1)
		check(st1b.surface == null or st1b.surface != high, "one jump does not reach the 176-unit ledge")
		var st2 := _jump_to(geo, Vector2(high.bounds.get_center().x, high.bounds.end.y + 30.0), high.bounds.get_center(), 2)
		check(st2.surface == high and near(st2.altitude, 176.0, 0.5), "a double jump reaches it (%s)" % (st2.surface.id if st2.surface else "air"))
		var chest: Dictionary = Game.room_rt.object_def("chest_ledge_mv_1")
		check(not chest.is_empty() and near(float(chest.get("alt", 0)), 176.0), "the chest waits on the high ledge")
		var cloud: WalkSurface = geo.index.get("cloud_mv")
		var st3 := _jump_to(geo, Vector2(cloud.bounds.get_center().x, cloud.bounds.end.y + 30.0), cloud.bounds.get_center(), 2)
		check(st3.surface != cloud, "the cloud ledge is above double-jump reach: it is for fliers")
	# A standable crate on the Skydock's yard.
	Game.world.apply_teleport(c.id, "ae_shipyard")
	geo = Game.room_rt.geometry
	var crate_top: WalkSurface = null
	for srf in geo.surfaces:
		if srf.kind == "support" and srf.id.begins_with("crate_"): crate_top = srf
	check(crate_top != null, "a crate in the yard has a top to stand on")
	if crate_top:
		var st4 := _jump_to(geo, crate_top.bounds.get_center() + Vector2(0, 40), crate_top.bounds.get_center(), 1)
		check(st4.surface == crate_top, "a jump lands on the crate (%s)" % (st4.surface.id if st4.surface else "air"))
	# Wall-Step: in the air, pushing into a building's facade, there is a wall to kick off (S43).
	Game.world.apply_teleport(c.id, "lf_village")
	geo = Game.room_rt.geometry
	var roof: WalkSurface = geo.index.get("old_ma_store")
	if roof:
		var st5 := ActorState.new()
		st5.plane = Vector2(roof.bounds.position.x - 8.0, roof.bounds.end.y - 20.0)
		st5.altitude = 60.0
		st5.air_stratum = "ground"
		st5.jumps_used = 2
		var side := MovementSolver.wall_step(st5, geo, 1)
		check(side == 1 and near(st5.vertical_speed, 450.0), "Wall-Step kicks off the store's facade (within 12 units, pushing in)")
		check(MovementSolver.wall_step(st5, geo) == 0, "not without pushing into the wall")
		var st6 := ActorState.new()
		st6.plane = Vector2(roof.bounds.position.x - 200.0, roof.bounds.end.y - 20.0)
		st6.altitude = 60.0
		check(MovementSolver.wall_step(st6, geo, 1) == 0, "no wall, no kick")
	# The rooms: count how many give the jump something to do.
	var flat: Array = []
	for rid in ContentDB.rooms:
		var def: Dictionary = ContentDB.room(rid)
		var up := false
		for srf in def.get("surfaces", []):
			if str(srf.get("stratum", "")) == "platform" or str(srf.get("kind", "")) in ["roof", "stairs", "ladder"]: up = true
		for sc in def.get("scenery", []):
			if sc.get("standable", false) or float(sc.get("height", 999)) <= 80.0: up = true
		if not up and not str(def.get("type", "")) in ["interior", "insight", "home", "story", "event", "sect"]: flat.append(rid)
	check(flat.size() <= 3, "fields, towns and dungeons all have something to climb %s" % str(flat))
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ what pills cost (gap report G1)
func _bag_index(c, id: String) -> int:
	for i in c.inventory.bag.size():
		if c.inventory.bag[i] != null and str(c.inventory.bag[i].id) == id: return i
	return -1

func g1_suite() -> void:
	var c = Game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	var back := str(c.position.get("room", "lf_village"))
	cu.realm_key = "heart_tempering_3"
	cu.state = "accumulating"
	cu.qp = 0.0
	for i in c.inventory.bag.size(): c.inventory.bag[i] = null
	# Lifetime resistance (S44): every 5 doses of a family add 1 to its count; a pill works at 1 / (1 + 0.25 x count).
	cu.pill_resistance.clear()
	check(ProgressionRules.pill_family(ContentDB.item("qi_gathering_pill")) == "accumulation" and ProgressionRules.pill_family(ContentDB.item("healing_pill")) == ""
		and ProgressionRules.pill_family(ContentDB.item("foundation_guard_pill")) == "support", "pill families come from data; healing pills are exempt")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 6, "test")
	var factors: Array = []
	for i in 6: factors.append(snappedf(float(_use_fresh(c, _bag_index(c, "qi_gathering_pill")).get("factor", 0)), 0.01))
	check(factors == [1.0, 1.0, 1.0, 1.0, 1.0, 0.8], "five Qi pills at full strength, the sixth at 80%% (%s)" % str(factors))
	check(ProgressionRules.resistance_count(cu, "accumulation") == 1 and int(cu.pill_resistance.accumulation.doses) == 1, "count 1 and one dose toward the next")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 1, "test", {"quality": "pill_grain"})
	var rg := _use_fresh(c, _bag_index(c, "qi_gathering_pill"))
	check(near(float(rg.get("factor", 0)), InventoryAuthority.pill_potency({"quality": "pill_grain"})) and int(cu.pill_resistance.accumulation.doses) == 1,
		"a Pill Grain ignores lifetime resistance and adds no dose")
	cu.pill_resistance.accumulation.count = 3
	Game.progression._advance(c, "heart_tempering_4", true)
	check(ProgressionRules.resistance_count(cu, "accumulation") == 1, "a major breakthrough: count 3 drops by 1, then halves (1)")
	var old := CultivatorState.new()
	old.restore({"pill_resistance": {"qi": 7}, "foundation": {"realm": "heart_tempering", "total": 10.0, "pill": 4.0}, "support_fails": {"x": {"a": 1, "b": 2}}})
	check(old.pill_resistance.get("accumulation", {}).get("count", -1) == 1 and int(old.pill_resistance.accumulation.doses) == 2
		and near(float(old.foundation.pill_qp), 4.0) and int(old.support_failures.get("x", 0)) == 2, "a version 4 save migrates to the v2 shapes")
	# Raw herbs: weak and poisonous, and they count toward resistance.
	cu.realm_key = "heart_tempering_3"
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 1, "test")
	var raw_i := _bag_index(c, "riverreed_ginseng_10")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, raw_i, false).get("reason", "")) == "confirm", "eating a herb raw asks first")
	_use_fresh(c, raw_i)
	check(near(cu.toxicity, 20.0) and int(cu.pill_resistance.accumulation.doses) == 2, "a raw ginseng root: toxicity 20, one more accumulation dose")
	# Residue: 5% of toxicity stays; each 10 costs 1% accumulation.
	cu.residue = 0.0
	Game.progression.apply_toxicity(c.id, 100.0)
	check(near(cu.residue, 5.0) and near(ProgressionRules.residue_penalty(cu), 0.0), "100 toxicity leaves 5 residue (no penalty yet)")
	Game.progression.apply_toxicity(c.id, 300.0)
	check(near(ProgressionRules.residue_penalty(cu), 0.02), "20 residue: accumulation -2%")
	Game.apply_effects(c.id, [{"kind": "add_toxicity", "amount": -1000}], "test")
	check(near(cu.residue, 20.0), "a Purging Pill does not touch residue")
	cu.toxicity = 0.0
	c.inventory.bag.fill(null)
	# Foundation: Qi from pills beyond 30% of the great realm leaves it hollow.
	cu.realm_key = "heart_tempering_9"
	cu.foundation = {}
	Game.progression.apply_progress(c.id, cu.need() * 0.2, "meditation")
	check(not ProgressionRules.foundation_hollow(cu), "meditated Qi keeps the foundation sound")
	Game.progression.apply_progress(c.id, cu.need() * 0.5, "item:qi_gathering_pill")
	check(ProgressionRules.foundation_hollow(cu) and near(ProgressionRules.foundation_share(cu), 0.5 / 0.7, 0.02), "pill Qi past 30%% of the realm's Qi leaves it hollow (%.2f)" % ProgressionRules.foundation_share(cu))
	var q := Game.progression.query_breakthrough(c)
	var hollow_row := false
	for row in q.results:
		if str(row.get("kind", "")) == "foundation" and not row.ok and not row.hard: hollow_row = true
	check(q.get("hollow", false) and hollow_row, "a major breakthrough counts a hollow foundation as an unmet soft requirement")
	c.seclusion = {"spot": "", "focus": "settle_foundation", "started_utc": 0.0, "cap_h": 12, "density": 1.0}
	var settled := Game.progression.claim_offline(c, 9 * 3600.0)
	check(not ProgressionRules.foundation_hollow(cu) and near(cu.residue, 0.0) and float(settled.gains.get("foundation", 0)) > 0.0,
		"nine hours settling (5 points and 5 residue an hour) make the foundation sound and burn off the residue (%.2f)" % ProgressionRules.foundation_share(cu))
	# Heart demons: a changed method feeds them; each 25 is a risk step; Calm Incense clears them.
	cu.heart_demon = 0.0
	cu.methods_known = ["riverbreath_fragment", "jade_current_scripture"]
	cu.method_id = "riverbreath_fragment"
	Game.progression.switch_method(c, "jade_current_scripture", false)
	check(near(cu.heart_demon, 10.0), "switching method feeds the heart demon (+10)")
	Game.progression.apply_heart_demon(c.id, 45.0, "test")
	var q2 := Game.progression.query_breakthrough(c)
	check(int(q2.get("heart_demon_steps", 0)) == 2, "55 heart demon is two risk steps at a major breakthrough")
	check(ProgressionRules.risk_index(0, false, 0, 0, false, 2) == 2 and ProgressionRules.risk_index(0, false, 0, 0, false, -1) == 0, "risk steps add and merit subtracts, within Low..Severe")
	Game.inventory.apply_add(c.id, "myriad_year_calm_incense", 1, "test")
	_use_fresh(c, _bag_index(c, "myriad_year_calm_incense"))
	check(near(cu.heart_demon, 35.0), "Myriad-Year Calm Incense clears 20")
	# Karma: merit eases one breakthrough per great realm; sin feeds the demon; the back room is a sin.
	cu.merit = 0
	cu.merit_used.clear()
	Game.apply_effects(c.id, [{"kind": "add_merit", "amount": 100, "reason": "test"}], "test")
	check(ProgressionRules.merit_step(cu) == 1 and int(Game.progression.query_breakthrough(c).get("merit", 0)) == 1, "100 merit eases a great breakthrough")
	cu.merit_used[ProgressionRules.great_realm(cu.realm_key)] = true
	check(ProgressionRules.merit_step(cu) == 0, "once in each great realm")
	var hd0 := cu.heart_demon
	Game.apply_effects(c.id, [{"kind": "add_sin", "amount": 30, "reason": "test"}], "test")
	check(cu.sin >= 30 and near(cu.heart_demon, hd0 + 3.0), "sin feeds the heart demon (+1 per 10 sin)")
	Game.quest.apply_flag(c.id, "path_independent")
	Unlocks.force_unlock(c.id, "shop")
	Game.economy.apply_currency("spirit_stone", 100, "test")
	var sin0 := cu.sin
	var bought := Game.economy.buy(c, "free_market", "manual_page", 1, -1)
	check(bought.get("ok", false) and cu.sin == sin0 + 2, "Broker Mu's back room stains the ledger (+2 sin) %s" % str(bought.get("reason", "")))
	# A named debt comes due as a letter.
	var mails0: int = Game.account.mail.size() if Game.account.get("mail") is Array else 0
	Game.apply_effects(c.id, [{"kind": "record_debt", "id": "test_debt", "due_h": 0.0, "mail": "gu_repays", "attachments": [{"currency": "spirit_stone", "amount": 1}]}], "test")
	Game.progression.tick(0.1)
	check(bool(cu.debts.get("test_debt", {}).get("paid", false)), "a debt that falls due is repaid by letter")
	cu.debts.erase("test_debt")
	# Furnace and fire: the bronze furnace holds three; charcoal stops at Perfect; a named furnace or a flame reaches Soul.
	c.inventory.key_items = c.inventory.key_items.filter(func(k): return not ContentDB.item(str(k.id)).has("furnace"))
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	var fu: Dictionary = Game.crafting.furnace_of(c)
	check(str(fu.id) == "bronze_furnace" and int(fu.batch) == 3, "the bronze furnace refines three to a batch")
	check(Game.crafting.rare_allowed(fu, "charcoal").is_empty() and Game.crafting.rare_allowed(fu, "earth_fire") == ["pill_grain"]
		and "pill_soul" in Game.crafting.rare_allowed(fu, "heavenly_flame"), "charcoal stops at Perfect, Earth Fire reaches Grain, a Heavenly Flame reaches Soul")
	check("pill_soul" in Game.crafting.rare_allowed(ContentDB.item("nine_dragon_cauldron").furnace, "charcoal"), "the Nine-Dragon Cauldron reaches Soul on any fire")
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var any_rare := false
	for i in 400:
		if Game.crafting._rare_pill_quality(c, [1.0, 1.0, 1.0], rng, []) != "perfect": any_rare = true
	check(not any_rare, "no rare quality ever comes out of charcoal")
	Game.inventory.apply_add(c.id, "earth_vein_furnace", 1, "test")
	check(str(Game.crafting.furnace_of(c).id) == "earth_vein_furnace" and near(Game.crafting.band_mult(c, "beast_fire"), 1.2),
		"the best furnace carried is used; Beast Fire in it widens the band by 20%")
	check(not "beast_fire" in Game.crafting.fires_available(c), "no core, no Beast Fire")
	Game.inventory.apply_add(c.id, "pebble_core", 1, "test")
	check("beast_fire" in Game.crafting.fires_available(c), "a beast core in the bag lights Beast Fire")
	Game.world.apply_teleport(c.id, "wg_rapids_terraces")
	var vent: Dictionary = Game.room_rt.object_def("earth_vent_wg")
	check(not vent.is_empty(), "Whitewater Gorge has an Earth Fire vent")
	if not vent.is_empty():
		Game.actor_state(c.id).plane = Vector2(float(vent.at[0]) + 60.0, float(vent.at[1]))
		check("earth_fire" in Game.crafting.fires_available(c) and Game.crafting.station_near(c, ["alchemy_furnace", "earth_vent"]),
			"at the vent: Earth Fire, and the vent serves as a furnace")
	# Pill marks: a Pill Soul carries all nine; each is +2%.
	check(Game.crafting._roll_marks("pill_soul", rng) == 9 and Game.crafting._roll_marks("flawed", rng) == 0, "marks: Soul nine, Flawed none")
	check(near(InventoryAuthority.pill_potency({"quality": "common", "marks": 5}), 1.1), "five marks: +10%")
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 2, "test", {"quality": "fine", "marks": 3})
	Game.inventory.apply_add(c.id, "qi_gathering_pill", 1, "test", {"quality": "fine"})
	var marked = c.inventory.bag[_bag_index(c, "qi_gathering_pill")]
	check(int(marked.get("marks", 0)) == 3 and int(marked.count) == 2, "a refined stack keeps its gold marks, apart from an unmarked one")
	# A Heavenly Flame is absorbed once; a second copy gutters into Spirit Stones.
	c.crafting["flames"] = []
	Game.inventory.apply_add(c.id, "cold_lamp_flame", 2, "test")
	var fr := Game.inventory.use_item(c, _bag_index(c, "cold_lamp_flame"), true)
	check(fr.get("ok", false) and (c.crafting.flames as Array).has("cold_lamp_flame") and Game.account.codex.has("cold_lamp_flame"),
		"the Cold Lamp Flame is absorbed and entered in the Codex")
	check("heavenly_flame" in Game.crafting.fires_available(c), "an absorbed flame burns under any furnace")
	var ss0: int = Game.economy.balance("spirit_stone")
	Game.inventory.use_item(c, _bag_index(c, "cold_lamp_flame"), true)
	check(Game.economy.balance("spirit_stone") == ss0 + 20, "a second copy gutters into 20 Spirit Stones")
	# The Reflection brings a heart demon for every 25.
	var ev: Dictionary = ContentDB.room("si_trial_of_reflections").get("event", {})
	check(str(ev.get("heart_demons", "")) == "heart_demon" and ContentDB.has_entry("enemies", "heart_demon"), "the Trial of Reflections summons heart demons")
	check((ev.get("on_complete", []) as Array).any(func(e): return str(e.get("kind", "")) == "add_heart_demon" and int(e.get("amount", 0)) == -30),
		"passing the Heart Trial clears 30 heart demon")
	var cleansing := ContentDB.entry("set_pieces", "heavens_cleansing")
	check(str(cleansing.get("room_event", {}).get("on_flawless", [{}])[0].get("kind", "")) == "clear_residue", "a flawless Heaven's Cleansing clears residue")
	c.inventory.bag.fill(null)
	cu.heart_demon = 0.0
	cu.residue = 0.0
	cu.foundation = {}
	cu.pill_resistance.clear()
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ treasures, throwables, talismans, vessels (gap report G2)
func _g2_foe(def_id: String, at: Vector2, boss := false) -> EnemyState:
	var e: EnemyState = Game.enemies.spawn_at(def_id, at, 12)
	if e != null and boss: e.role = "field_boss"
	return e

func _g2_ready(c) -> void:
	Game.room_rt.enemies.clear()
	Game.room_rt.projectiles.clear()
	Game.combat.treasure_fx.clear()
	c.pools.cooldowns.clear()
	c.pools.qi = c.pools.max_qi
	c.pools.hp = c.pools.max_hp * 0.5

func g2_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var back := str(c.position.get("room", "lf_village"))
	var events: Array = []
	var grab := func(n, p): events.append([str(n), p])
	GameEvents.event.connect(grab)
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	for st_id in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, st_id)
	var here: Vector2 = Game.actor_state(c.id).plane
	Game.combat.timeline(c.id).facing = 1
	var realm0: String = c.cultivator.realm_key
	c.cultivator.realm_key = "heart_tempering_5"
	Game.combat.refresh_stats(c.id)
	c.inventory.bag.fill(null)
	var treasures := ["bronze_bell", "little_pagoda", "bright_mirror", "mountain_seal", "taming_cauldron", "wisp_banner", "sealing_gourd"]
	for id in treasures: Game.inventory.apply_add(c.id, id, 1, "test")
	# Two Treasure buttons: the first at Heart Tempering 1 with "A Treasure in Hand", the second at Spirit Awakening 1.
	var tu := ContentDB.entry("unlocks", "treasures")
	check(str(tu.get("reveals", [""])[0]) == "hud:treasure_1" and str(tu.get("quest", "")) == "a_treasure_in_hand" and ContentDB.has_entry("unlocks", "treasure_slot_2"),
		"the Treasure buttons are unlocks that reveal HUD buttons; the first comes with A Treasure in Hand")
	var tq: Dictionary = ContentDB.entry("quests", "a_treasure_in_hand")
	check(str(tq.get("on_accept", [{}])[0].get("item", "")) == "practice_bell" and near(float(CombatAuthority.treasure_of("practice_bell").get("stun_s", 0)), 0.5)
		and int(CombatAuthority.treasure_of("practice_bell").get("qi", 0)) == 15, "the Practice Bell: stun 0.5 s for 15 QI, given on acceptance")
	Unlocks.force_unlock(c.id, "treasures")
	Unlocks.force_unlock(c.id, "treasure_slot_2")
	var r := Game.submit({"type": "set_treasure", "slot": 0, "item": "bronze_bell"})
	check(r.get("ok", false) and c.inventory.treasures[0] == "bronze_bell", "the Bronze Bell sits in Treasure 1")
	Game.submit({"type": "set_treasure", "slot": 1, "item": "bronze_bell"})
	check(c.inventory.treasures == ["", "bronze_bell"], "set in Treasure 2, it leaves Treasure 1")
	check(str(Game.submit({"type": "set_treasure", "slot": 0, "item": "iron_needles"}).get("reason", "")) == "not_a_treasure", "only a treasure art fits a Treasure button")
	# The Bronze Bell: stun 1 s and Qi Seal 3 s within 150; a boss keeps its feet.
	_g2_ready(c)
	var a := _g2_foe("bamboo_monkey", here + Vector2(80, 0))
	var b := _g2_foe("bamboo_monkey", here + Vector2(-120, 10))
	var far := _g2_foe("bamboo_monkey", here + Vector2(600, 0))
	var boss := _g2_foe("ember_fox", here + Vector2(60, -10), true)
	var qi0: float = c.pools.qi
	r = Game.submit({"type": "use_treasure", "slot": 1})
	check(r.get("ok", false) and int(r.get("targets", 0)) == 3, "the bell reaches everyone within 150 (%s)" % str(r.get("targets", r.get("reason", ""))))
	check(a.pools.has_status("stun") and b.pools.has_status("stun") and not far.pools.has_status("stun"), "foes close by are stunned; a far one is not")
	check(not boss.pools.has_status("stun") and boss.pools.has_status("qi_seal"), "a boss is not stunned, only Qi-sealed")
	check(near(qi0 - c.pools.qi, 30.0), "the bell costs 30 QI (%.1f)" % (qi0 - c.pools.qi))
	check(str(Game.submit({"type": "use_treasure", "slot": 1}).get("reason", "")) == "cooldown", "then it rests for 20 s")
	c.pools.cooldowns.clear()
	c.pools.qi = 20.0
	check(str(Game.submit({"type": "use_treasure", "slot": 1}).get("reason", "")) == "no_qi", "without the Qi it stays silent")
	# From Spirit Awakening 1 a treasure also draws on the Soul: a third of its QI cost.
	c.cultivator.realm_key = "spirit_awakening_1"
	Game.combat.refresh_stats(c.id)
	_g2_ready(c)
	if c.pools.max_soul <= 0.0: c.pools.set_max("soul", 300.0)   # the Soul pool opens with the SA1 unlock
	c.pools.soul = c.pools.max_soul
	var soul0: float = c.pools.soul
	Game.submit({"type": "use_treasure", "slot": 1})
	check(c.pools.max_soul > 0.0 and near(soul0 - c.pools.soul, 10.0), "at Spirit Awakening the bell also costs 10 Soul (%.1f)" % (soul0 - c.pools.soul))
	c.cultivator.realm_key = "heart_tempering_5"
	Game.combat.refresh_stats(c.id)
	# The Little Pagoda: a prison for one foe (an elite first), never a boss.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "little_pagoda"})
	_g2_foe("ember_fox", here + Vector2(60, 0), true)
	check(str(Game.submit({"type": "use_treasure", "slot": 0}).get("reason", "")) == "immune" and c.pools.cooldown("treasure:little_pagoda") == 0.0
		and near(c.pools.qi, c.pools.max_qi), "the pagoda cannot hold a boss, and a failed throw costs nothing")
	var small := _g2_foe("bamboo_monkey", here + Vector2(40, 0))
	r = Game.submit({"type": "use_treasure", "slot": 0})
	var held := false
	for st in small.pools.statuses: if st.id == "stun" and near(float(st.remaining), 4.0): held = true
	check(r.get("ok", false) and held, "the nearest foe is held for 4 s")
	# The Bright Mirror sends an arrow back at the archer.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "bright_mirror"})
	var archer := _g2_foe("bandit_archer", here + Vector2(200, 0))
	archer.facing = -1
	Game.submit({"type": "use_treasure", "slot": 0})
	var hp_c: float = c.pools.hp
	var hp_a: float = archer.pools.hp
	Game.combat.spawn_enemy_projectile(archer, archer.def.attacks[0])
	events.clear()
	for i in 12: Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_reflected") and near(c.pools.hp, hp_c) and archer.pools.hp < hp_a,
		"the arrow turns back and strikes its archer (%.0f)" % (hp_a - archer.pools.hp))
	# The Sealing Gourd drinks it instead.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "sealing_gourd"})
	archer = _g2_foe("bandit_archer", here + Vector2(200, 0))
	archer.facing = -1
	Game.submit({"type": "use_treasure", "slot": 0})
	hp_c = c.pools.hp
	Game.combat.spawn_enemy_projectile(archer, archer.def.attacks[0])
	events.clear()
	Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_absorbed") and Game.room_rt.projectiles.is_empty() and near(c.pools.hp, hp_c),
		"the gourd swallows the arrow before it lands")
	# The Mountain Seal: 250% Qi Attack to all within 120.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "mountain_seal"})
	var s1 := _g2_foe("bamboo_monkey", here + Vector2(60, 0))
	var s2 := _g2_foe("bamboo_monkey", here + Vector2(-90, 0))
	var s_hp := s1.pools.hp
	r = Game.submit({"type": "use_treasure", "slot": 0})
	check(r.get("ok", false) and int(r.targets) == 2 and s1.pools.hp < s_hp and s2.pools.hp < s_hp, "the seal comes down on both foes")
	# The Wisp Banner: three wisps strike the nearest foes each second.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "wisp_banner"})
	var w1 := _g2_foe("bamboo_monkey", here + Vector2(100, 0))
	var w_hp := w1.pools.hp
	Game.submit({"type": "use_treasure", "slot": 0})
	events.clear()
	Game.combat._tick_treasures(c, 1.0)
	GameEvents.flush()
	check(events.filter(func(e): return e[0] == "wisp_struck").size() == 1 and w1.pools.hp < w_hp, "a second in, the wisps find the only foe")
	for i in 10: Game.combat._tick_treasures(c, 1.0)
	check(not Game.combat.treasure_fx.get(c.id, {}).has("wisps"), "after 10 s the banner furls")
	# The Taming Cauldron: a worn-down beast is taken whole, as materials, with no loot roll.
	_g2_ready(c)
	Game.submit({"type": "set_treasure", "slot": 0, "item": "taming_cauldron"})
	var beast := _g2_foe("bamboo_monkey", here + Vector2(60, 0))
	var man := _g2_foe("bandit_archer", here + Vector2(30, 0))
	man.pools.hp = 1.0
	check(str(Game.submit({"type": "use_treasure", "slot": 0}).get("reason", "")) == "no_target", "a healthy beast (or any person) cannot be taken")
	beast.pools.hp = beast.pools.max_hp * 0.1
	events.clear()
	r = Game.submit({"type": "use_treasure", "slot": 0})
	GameEvents.flush()
	var taken: Array = events.filter(func(e): return e[0] == "beast_captured")
	var mats := LootRules.capture_materials("bamboo_monkey")
	check(r.get("ok", false) and not beast.alive and man.alive and taken.size() == 1 and mats.size() > 0 and int(taken[0][1].items) == mats.size()
		and Game.combat.captured.is_empty(), "the worn beast is taken whole, as its fixed materials (%s)" % str(mats))
	# Throwables: needles fly three at a time and share a 1.2 s cooldown.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "iron_needles", 5, "test")
	var t1 := _g2_foe("bamboo_monkey", here + Vector2(150, 0))
	var t_hp := t1.pools.hp
	r = Game.inventory.use_item(c, _bag_index(c, "iron_needles"), true)
	check(r.get("ok", false) and Game.room_rt.projectiles.size() == 3 and c.inventory.count("iron_needles") == 4, "one bundle throws three needles")
	check(str(Game.inventory.use_item(c, _bag_index(c, "iron_needles"), true).get("reason", "")) == "cooldown" and near(c.pools.cooldown("item:throw"), 1.2),
		"throwables share a 1.2 s cooldown")
	for i in 10: Game.combat._tick_projectiles(0.05)
	check(t1.pools.hp < t_hp and Game.room_rt.projectiles.is_empty(), "the needles land (%.0f)" % (t_hp - t1.pools.hp))
	# Shots fly at chest height but still strike a creature under the line (a rat is 22 tall).
	_g2_ready(c)
	var rat := _g2_foe("reedtail_rat", here + Vector2(120, 0))
	Game.combat._spawn_projectile({"team": "player", "owner": c.id, "x": here.x + 28, "y": here.y, "alt": Game.actor_state(c.id).altitude + 58.0, "dir": 1,
		"speed": 620, "range": 480, "pierce": 0, "art": "arrow", "attack": {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0]}})
	for i in 6: Game.combat._tick_projectiles(0.05)
	check(rat.pools.hp < rat.pools.max_hp, "an arrow at chest height strikes a rat beneath it")
	# A thunderclap pellet bursts: the foe behind the one it hits is caught too.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "thunderclap_pellet", 1, "test")
	var p1 := _g2_foe("bamboo_monkey", here + Vector2(150, 0))
	var p2 := _g2_foe("bamboo_monkey", here + Vector2(230, 0))
	var p_hp := p2.pools.hp
	events.clear()
	Game.inventory.use_item(c, _bag_index(c, "thunderclap_pellet"), true)
	for i in 10: Game.combat._tick_projectiles(0.05)
	GameEvents.flush()
	check(events.any(func(e): return e[0] == "projectile_burst") and p2.pools.hp < p_hp and p1.pools.hp < p1.pools.max_hp, "the pellet bursts and catches the foe behind")
	# Elder Hu's Talisman: three charges of 600% Qi Attack from a Treasure button, charges only.
	_g2_ready(c)
	Game.inventory.apply_add(c.id, "elder_hus_talisman", 1, "test")
	Game.submit({"type": "set_treasure", "slot": 0, "item": "elder_hus_talisman"})
	var big := _g2_foe("bamboo_monkey", here + Vector2(200, 0))
	var big_hp := big.pools.hp
	r = Game.submit({"type": "use_treasure", "slot": 0})
	check(r.get("ok", false) and big.pools.hp < big_hp and int(r.get("charges", 0)) == 2 and near(c.pools.qi, c.pools.max_qi),
		"one charge of the palm strikes the monkey; two charges left, no Qi spent")
	check(Game.submit({"type": "use_treasure", "slot": 0}).get("ok", false), "charges only: no cooldown between them")
	Game.submit({"type": "use_treasure", "slot": 0})
	check(c.inventory.count("elder_hus_talisman") == 0 and c.inventory.treasures[0] == "", "the third charge spends the paper and empties the button")
	# Flight vessels: kept once in the key pouch, chosen for flight.
	Game.inventory.apply_add(c.id, "flying_sword_vessel", 1, "test")
	Game.inventory.apply_add(c.id, "flying_sword_vessel", 1, "test")
	check(c.inventory.count("flying_sword_vessel") == 1 and c.inventory.key_items.any(func(k): return k.id == "flying_sword_vessel"), "a vessel is kept once, in the key pouch")
	check(Game.submit({"type": "choose_vessel", "item": "flying_sword_vessel"}).get("ok", false) and near(Game.combat.vessel_qi_mult(c), 0.8),
		"the Flying Sword: flight costs 20% less Qi")
	check(not Game.submit({"type": "choose_vessel", "item": "bronze_bell"}).get("ok", false), "a bell is not a vessel")
	var saved: Dictionary = c.inventory.snapshot()
	var inv2 := InventoryState.new()
	inv2.restore(saved)
	check(inv2.vessel == "flying_sword_vessel" and inv2.treasures == c.inventory.treasures, "treasures and the vessel survive a save")
	Game.submit({"type": "choose_vessel", "item": ""})
	check(c.inventory.vessel == "" and near(Game.combat.vessel_qi_mult(c), 1.0), "dismounted, you fly on Qi alone")
	# Tidy up.
	GameEvents.event.disconnect(grab)
	_g2_ready(c)
	c.inventory.treasures = ["", ""]
	c.inventory.bag.fill(null)
	c.inventory.key_items = c.inventory.key_items.filter(func(k): return k.id != "flying_sword_vessel")
	c.cultivator.realm_key = realm0
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	Game.world.apply_teleport(c.id, back)

# ------------------------------------------------------------------ traversal (Build Prompt v2 S43)
func _trav_zone() -> ZoneGeometry:
	var z := ZoneGeometry.new()
	z.configure({"bounds": [0, 480, 3000, 480], "surfaces": [
		{"id": "ground", "rect": [0, 560, 3000, 400], "height": 0, "kind": "ground", "stratum": "ground", "open_edges": false},
		{"id": "deck", "rect": [200, 600, 400, 100], "height": 100, "kind": "roof", "stratum": "platform"},
		{"id": "loft", "rect": [1150, 600, 200, 88], "height": 88, "kind": "roof", "stratum": "platform"}],
		"blocks": [{"id": "crate", "rect": [800, 700, 60, 60], "base": 0, "top": 60, "kind": "crate"},
			{"id": "wall", "rect": [1600, 560, 40, 400], "base": 0, "top": 300, "kind": "wall"}],
		"climbables": [{"id": "ladder", "kind": "ladder", "at": [1250, 725], "top_at": [1250, 680], "bottom_alt": 0, "top_alt": 88, "bottom": "ground", "top": "loft"}]})
	return z

func _trav_actor(z: ZoneGeometry, sid: String, at: Vector2, arts := {}) -> ActorState:
	var st := ActorState.new()
	st.surface = z.index[sid]
	st.plane = at
	st.altitude = st.surface.height_at(at)
	st.arts = {"double_jump": false, "wall_step": false, "drop_through": true, "mantle": true, "climb": true}
	st.arts.merge(arts, true)
	return st

func _trav_run(st: ActorState, z: ZoneGeometry, secs: float, v: Vector2, dt := 1.0 / 120.0) -> void:
	var t := 0.0
	while t < secs - 0.0001:
		MovementSolver.advance(st, z, dt, v)
		t += dt

func traversal_suite() -> void:
	var z := _trav_zone()
	# Rule 1: platform back edges are closed, the others open; a block top is open all round.
	var d: WalkSurface = z.index.deck
	check(d.edges == {"n": "closed", "s": "open", "e": "open", "w": "open"} and (z.index.ground as WalkSurface).edges.n == "closed"
		and (z.index.crate as WalkSurface).edges.n == "open", "platforms close their back edge by default; blocks are open all round")
	var st := _trav_actor(z, "deck", Vector2(400, 620))
	_trav_run(st, z, 1.0, Vector2(0, -205))
	check(st.surface == d and st.plane.y >= 600.0, "walking north off a roof is stopped by its closed back edge")
	_trav_run(st, z, 1.5, Vector2(0, 205))
	check(st.surface != null and st.surface.id == "ground", "walking south off it drops to the ground")
	# Blocks stop walking, can be stood on, and a 60 block can be jumped over at walk speed.
	st = _trav_actor(z, "ground", Vector2(760, 730))
	_trav_run(st, z, 0.8, Vector2(205, 0))
	check(st.plane.x < 800.0 and st.surface.id == "ground", "a crate stops a walker (x %.0f)" % st.plane.x)
	st = _trav_actor(z, "ground", Vector2(700, 730))
	MovementSolver.jump(st)
	_trav_run(st, z, 1.4, Vector2(205, 0))
	check(st.surface != null and st.surface.id == "ground" and st.plane.x > 866.0, "a 60 block is jumped over at walk speed (x %.0f)" % st.plane.x)
	st = _trav_actor(z, "ground", Vector2(775, 730))
	MovementSolver.jump(st)
	_trav_run(st, z, 0.3, Vector2(205, 0))
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(st.surface != null and st.surface.id == "crate" and near(st.altitude, 60.0), "a crate can be stood on")
	# Rule 2: coyote time, jump buffer and the fixed jump, at three frame rates.
	for dt in [1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0]:
		st = _trav_actor(z, "deck", Vector2(400, 690))
		_trav_run(st, z, 0.1, Vector2(0, 205), dt)
		var off := st.surface == null
		var coy := MovementSolver.jump(st)
		check(off and coy and near(st.vertical_speed, 530.0) and st.jumps_used == 1, "a jump just after walking off an edge is still a ground jump (dt %.3f)" % dt)
		st = _trav_actor(z, "ground", Vector2(1000, 800))
		MovementSolver.jump(st)
		while st.vertical_speed > -480.0: MovementSolver.advance(st, z, 1.0 / 240.0, Vector2.ZERO)
		var early := MovementSolver.jump(st)
		st.events.clear()
		_trav_run(st, z, 0.2, Vector2.ZERO, dt)
		var names: Array = st.events.map(func(e): return e.name)
		check(not early and names.find("landed") >= 0 and names.find("jumped", names.find("landed")) > 0,
			"a jump pressed just before landing fires on landing (dt %.3f) %s" % [dt, str(names)])
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	var peak := 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		peak = maxf(peak, st.altitude)
	check(near(peak, 122.1, 0.01), "the base jump peaks at 122 (%.1f)" % peak)
	# Cloud Ladder Step: a second jump of +80 from where it is used; none without the art.
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	while st.vertical_speed > 0.0: MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
	check(not MovementSolver.jump(st), "no double jump without Cloud Ladder Step")
	st = _trav_actor(z, "ground", Vector2(1000, 800), {"double_jump": true})
	MovementSolver.jump(st)
	while st.vertical_speed > 0.0: MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
	var from_h: float = st.altitude
	check(MovementSolver.jump(st) and near(st.vertical_speed, 430.0), "Cloud Ladder Step jumps again at impulse 430")
	peak = 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		peak = maxf(peak, st.altitude)
	check(near(peak - from_h, 80.4, 0.02) and near(peak, 202.0, 0.02), "+80 from where it is used; about 202 from the ground (%.0f)" % peak)
	# Wall-Step: push into a wall face within 12 and kick (vertical 450), three times per airtime.
	st = _trav_actor(z, "ground", Vector2(1590, 800), {"wall_step": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.2, Vector2.ZERO)
	check(MovementSolver.wall_step(st, z, 0) == 0, "no Wall-Step without pushing into the wall")
	var kicks := 0
	for i in 4:
		if MovementSolver.wall_step(st, z, 1) != 0: kicks += 1
	check(kicks == 3 and near(st.vertical_speed, 450.0), "three Wall-Step kicks per airtime at vertical speed 450 (%d)" % kicks)
	# Rule 3: drop through a platform, never the ground or a block.
	st = _trav_actor(z, "deck", Vector2(400, 650))
	check(MovementSolver.drop_through(st), "drop through the deck")
	_trav_run(st, z, 1.2, Vector2.ZERO)
	check(st.surface != null and st.surface.id == "ground", "and land on the ground below it")
	check(not MovementSolver.drop_through(st), "the ground cannot be dropped through")
	st = _trav_actor(z, "crate", Vector2(830, 730))
	check(not MovementSolver.drop_through(st), "nor a block")
	# Rule 4: a just-missed ledge within 24 up and 16 across is mantled.
	st = _trav_actor(z, "ground", Vector2(190, 650))
	st.surface = null
	st.altitude = 84.0
	st.air_peak = 110.0
	st.vertical_speed = -50.0
	st.jumps_used = 1
	MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(205, 0))
	check(st.surface == d and near(st.altitude, 100.0), "a ledge 16 above is mantled")
	# Rule 5: climb a ladder, stop, reach the top, come down, jump off, be knocked off.
	st = _trav_actor(z, "ground", Vector2(1250, 740))
	var ladder: Dictionary = z.climbable_near(st.plane, st.altitude)
	check(not ladder.is_empty() and MovementSolver.start_climb(st, ladder, false), "the ladder is in reach and can be climbed")
	_trav_run(st, z, 0.2, Vector2(0, -205))
	var mid: float = st.altitude
	_trav_run(st, z, 0.2, Vector2.ZERO)
	check(near(mid, 32.0, 0.05) and near(st.altitude, mid), "climbing at 160 a second, and stopping on the rungs (%.0f)" % mid)
	for i in 120:
		if st.climbing.is_empty(): break
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(0, -205))
	check(st.climbing.is_empty() and st.surface != null and st.surface.id == "loft", "the top step lands on the loft")
	var down_from: Dictionary = z.climbable_near(st.plane, st.altitude)
	check(not down_from.is_empty() and MovementSolver.start_climb(st, down_from, true), "climb back down from the top")
	for i in 120:
		if st.climbing.is_empty(): break
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(0, 205))
	check(st.climbing.is_empty() and st.surface.id == "ground", "the foot steps onto the ground")
	MovementSolver.start_climb(st, z.climbable_near(st.plane, st.altitude), false)
	_trav_run(st, z, 0.2, Vector2(0, -205))
	check(MovementSolver.release_climb(st, 1, true) and st.surface == null and st.vertical_speed > 0.0, "a jump lets go of the ladder")
	st = _trav_actor(z, "ground", Vector2(1250, 740))
	MovementSolver.start_climb(st, z.climbable_near(st.plane, st.altitude), false)
	check(MovementSolver.release_climb(st, -1, false) and st.surface == null and near(st.vertical_speed, 0.0), "a hit knocks the climber off")
	# Rule 6: the void lies 250 below the lowest surface.
	check(near(z.void_altitude, -250.0), "void altitude defaults to 250 below the lowest surface")
	# Traversal events are recorded for the authority to announce.
	st = _trav_actor(z, "ground", Vector2(1000, 800))
	MovementSolver.jump(st)
	check(st.events.any(func(e): return e.name == "jumped"), "a jump records a jumped event")
	# Room data reaches the room's geometry: blocks, climbables and the void (the World authority compiles it).
	var echo := ZoneGeometry.new()
	echo.configure(WorldAuthority.compile_geometry(ContentDB.room("wg_echo_cliffs")))
	check(echo.index.has("shaft_west") and echo.wall_face_at(Vector2(1356, 690), 120.0, "ground"), "the Echo Cliffs shaft walls are in the room's geometry")
	var ferry := ZoneGeometry.new()
	ferry.configure(WorldAuthority.compile_geometry(ContentDB.room("lf_village")))
	check(ferry.climbables.size() >= 1, "the Lotus Ferry hall ladder is in the room's geometry")

# ------------------------------------------------------------------ S43 movement arts, volumes and movers (V2b)
func _vol_zone() -> ZoneGeometry:
	var z := ZoneGeometry.new()
	z.configure({"bounds": [0, 480, 4000, 480], "surfaces": [
		{"id": "ground", "rect": [0, 560, 4000, 400], "height": 0, "kind": "ground", "stratum": "ground", "open_edges": false},
		{"id": "raft", "rect": [2000, 700, 90, 40], "height": 10, "kind": "raft", "stratum": "platform"},
		{"id": "boards", "rect": [2600, 650, 200, 70], "height": 100, "kind": "bridge", "stratum": "platform"},
		{"id": "cracked", "rect": [3200, 650, 200, 70], "height": 100, "kind": "rock_ledge", "stratum": "platform", "cracked": true}],
		"blocks": [{"id": "drum", "rect": [1900, 740, 60, 60], "base": 0, "top": 40, "kind": "drum"}],
		"volumes": [
			{"id": "shallow", "kind": "water_shallow", "rect": [100, 800, 300, 100], "alt": [-50, 10]},
			{"id": "deep", "kind": "water_deep", "rect": [500, 800, 300, 100], "alt": [-100, 10]},
			{"id": "drain", "kind": "current", "rect": [900, 800, 200, 100], "alt": [-50, 10], "push": [-80, 0]},
			{"id": "draft", "kind": "updraft", "rect": [1200, 560, 150, 400], "alt": [0, 300]},
			{"id": "gale", "kind": "wind", "rect": [1500, 560, 300, 400], "alt": [-50, 600], "push": [-100, 0]},
			{"id": "pad", "kind": "bounce", "rect": [1900, 740, 60, 60], "alt": [30, 50]},
			{"id": "rot", "kind": "crumble", "rect": [2600, 650, 200, 70], "surface": "boards"},
			{"id": "flood", "kind": "rising_water", "rect": [3600, 560, 300, 400], "alt": [-100, -20],
				"rise": [{"event": "boss_phase", "match": {"action": "flood"}, "to": 30, "over_s": 4.0, "hold_s": 2.0, "back_to": -20}]}],
		"movers": [{"surface": "raft", "path": [[300, 0, 0]], "speed": 100, "wait_s": 1.0, "mode": "pingpong"}]})
	return z

func _fall_until_landed(st: ActorState, z: ZoneGeometry, v := Vector2.ZERO, limit := 4.0) -> float:
	var t := 0.0
	while st.surface == null and t < limit:
		MovementSolver.advance(st, z, 1.0 / 120.0, v)
		t += 1.0 / 120.0
	return t

func arts_volumes_suite() -> void:
	var z := _vol_zone()
	# Falling Leaf Glide: descent capped at 120/s, 10% faster across; from an apex jump about 1.5 s and 300 flat.
	var st := _trav_actor(z, "ground", Vector2(2900, 900))
	MovementSolver.jump(st)
	check(not MovementSolver.glide(st, true), "no glide without Falling Leaf Glide")
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"glide": true})
	var x0: float = st.plane.x
	MovementSolver.jump(st)
	var air := 0.0
	while st.vertical_speed > 0.0:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2(205, 0))
		air += 1.0 / 120.0
	check(MovementSolver.glide(st, true) and st.gliding, "Jump held while falling glides")
	_trav_run(st, z, 0.3, Vector2(205, 0))
	check(st.vertical_speed >= -120.01, "a glide falls no faster than 120 a second (%.1f)" % st.vertical_speed)
	air += 0.3 + _fall_until_landed(st, z, Vector2(205, 0))
	var flat: float = st.plane.x - x0
	check(air > 1.4 and air < 1.7 and flat > 280.0 and flat < 360.0 and not st.gliding, "an apex glide lasts about 1.5 s and 300 units (%.2f s, %.0f)" % [air, flat])
	# Swallow Dart: in the air the body holds its height for 0.25 s while it darts 140; once per airtime.
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"air_dash": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.3, Vector2.ZERO)
	var alt0: float = st.altitude
	x0 = st.plane.x
	check(MovementSolver.air_dash(st), "Evade in the air darts")
	_trav_run(st, z, 0.25, Vector2(560, 0))
	check(near(st.altitude, alt0, 0.5) and near(st.plane.x - x0, 140.0, 1.0), "the dart holds the height and covers 140 (%.1f, %.0f)" % [st.altitude - alt0, st.plane.x - x0])
	check(not MovementSolver.air_dash(st), "one dart per airtime")
	_fall_until_landed(st, z)
	check(not st.air_dash_used, "landing gives the dart back")
	# Plunge: straight down at 900; the landing is left for Combat; a cracked floor breaks under it.
	st = _trav_actor(z, "ground", Vector2(2900, 900), {"plunge": true})
	MovementSolver.jump(st)
	_trav_run(st, z, 0.4, Vector2.ZERO)
	x0 = st.plane.x
	check(MovementSolver.plunge(st) and near(st.vertical_speed, -900.0), "Down + Attack in the air plunges at 900")
	var drop := _fall_until_landed(st, z, Vector2(205, 0))
	check(near(st.plane.x, x0, 0.5) and drop < 0.16 and not st.plunge_impact.is_empty() and not st.plunging, "a plunge drops straight and leaves an impact (%.2f s)" % drop)
	st = _trav_actor(z, "ground", Vector2(3300, 690), {"plunge": true})
	st.surface = null
	st.altitude = 220.0
	st.air_peak = 220.0
	st.jumps_used = 1
	MovementSolver.plunge(st)
	_fall_until_landed(st, z)
	check((z.index.cracked as WalkSurface).disabled and st.surface != null and st.surface.id == "ground", "a plunge breaks a cracked floor and falls through it")
	# Shallow water: x0.7.
	st = _trav_actor(z, "ground", Vector2(120, 850))
	_trav_run(st, z, 1.0, Vector2(205, 0))
	check(near(st.plane.x - 120.0, 143.5, 1.5), "shallow water slows walking to x0.7 (%.1f)" % (st.plane.x - 120.0))
	# Deep water: sinks in 1 s without an art; Breath Control swims at x0.6; Water Skimming runs across while sprinting.
	st = _trav_actor(z, "ground", Vector2(520, 850))
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(st.events.any(func(e): return e.name == "volume_entered" and str(e.volume) == "deep") and near(st.sink_depth, 20.0, 1.0) and not st.drowned,
		"deep water pulls a body down (%.1f) and says so" % st.sink_depth)
	check(not MovementSolver.jump(st), "a sinking body cannot jump out")
	_trav_run(st, z, 0.6, Vector2.ZERO)
	check(st.drowned and near(st.sink_depth, 40.0), "after 1 s it has sunk 40 and must be recovered")
	st = _trav_actor(z, "ground", Vector2(520, 850), {"breath_control": true})
	_trav_run(st, z, 1.0, Vector2(205, 0))
	check(not st.drowned and st.mode() == "swim" and near(st.plane.x - 520.0, 123.0, 1.5), "Breath Control swims at x0.6 (%.1f)" % (st.plane.x - 520.0))
	st = _trav_actor(z, "ground", Vector2(470, 850), {"water_skimming": true})
	st.sprinting = true
	_trav_run(st, z, 0.6, Vector2(348, 0))
	check(not st.drowned and st.water.get("skimming", false) and st.sink_depth == 0.0 and st.events.any(func(e): return e.name == "art_used" and e.art == "water_skimming"),
		"Water Skimming runs on deep water while sprinting")
	_trav_run(st, z, 0.55, Vector2.ZERO)
	check(not st.water.get("skimming", true), "stopping for half a second ends the skim")
	_trav_run(st, z, 1.1, Vector2.ZERO)
	check(st.drowned, "and then the water takes you")
	# Current: pushes a body standing in it.
	st = _trav_actor(z, "ground", Vector2(1050, 850))
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(near(st.plane.x - 1050.0, -80.0, 1.0), "a current pushes 80 a second (%.1f)" % (st.plane.x - 1050.0))
	# Updraft: a fall turns into a rise toward +220.
	st = _trav_actor(z, "ground", Vector2(1275, 800))
	st.surface = null
	st.altitude = 150.0
	st.air_peak = 150.0
	st.vertical_speed = -200.0
	st.jumps_used = 1
	_trav_run(st, z, 1.0, Vector2.ZERO)
	check(st.surface == null and st.altitude > 150.0 and st.vertical_speed > 100.0, "an updraft lifts a falling body (alt %.0f, vz %.0f)" % [st.altitude, st.vertical_speed])
	# Wind: strong for 1.5 s of every 4, a breeze (x0.3) the rest.
	st = _trav_actor(z, "ground", Vector2(1650, 800))
	z.time = 0.0
	_trav_run(st, z, 0.5, Vector2.ZERO)
	var gust: float = st.plane.x - 1650.0
	z.time = 2.0
	var x1: float = st.plane.x
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(near(gust, -50.0, 1.0) and near(st.plane.x - x1, -15.0, 1.0), "wind gusts at full push, then a breeze (%.1f, %.1f)" % [gust, st.plane.x - x1])
	# Bounce: landing on the drum launches at 700 (apex about 213 above it).
	st = _trav_actor(z, "ground", Vector2(1930, 770))
	st.surface = null
	st.altitude = 120.0
	st.air_peak = 120.0
	st.jumps_used = 1
	_fall_until_landed(st, z)
	var bounced := st.surface == null and near(st.vertical_speed, 700.0, 30.0)
	var top := 0.0
	for i in 240:
		MovementSolver.advance(st, z, 1.0 / 120.0, Vector2.ZERO)
		top = maxf(top, st.altitude)
	check(bounced and near(top, 40.0 + 213.0, 4.0), "a bounce pad throws you back up about 213 (%.0f)" % (top - 40.0))
	# Crumble: the boards give way 0.8 s after a foot lands and come back 5 s later.
	st = _trav_actor(z, "boards", Vector2(2700, 690))
	for i in 60:
		MovementSolver.advance(st, z, 1.0 / 60.0, Vector2.ZERO)
		z.advance(1.0 / 60.0)
	_fall_until_landed(st, z)
	check((z.index.boards as WalkSurface).disabled and st.surface != null and st.surface.id == "ground", "crumbling boards drop whoever stands on them")
	z.advance(5.1)
	check(not (z.index.boards as WalkSurface).disabled, "and return after 5 s")
	# Movers: the offset is a pure function of the room clock, and riders ride along.
	var m: Dictionary = z.movers[0]
	check(z.mover_offset(m, 0.5) == Vector3.ZERO and near(z.mover_offset(m, 2.0).x, 100.0) and near(z.mover_offset(m, 4.5).x, 300.0)
		and near(z.mover_offset(m, 6.0).x, 200.0) and z.mover_offset(m, 8.0 + 0.5) == Vector3.ZERO, "a pingpong mover waits, travels, waits and returns")
	var replay := func() -> Vector2:
		var zz := _vol_zone()
		var rider := _trav_actor(zz, "raft", Vector2(2040, 720))
		for i in 150:
			zz.advance(1.0 / 60.0)
			MovementSolver.advance(rider, zz, 1.0 / 60.0, Vector2(20, 0) if i % 50 < 10 else Vector2.ZERO)
		return rider.plane
	var p1: Vector2 = replay.call()
	var p2: Vector2 = replay.call()
	check(p1 == p2 and p1.x > 2100.0, "a rider is carried by its mover, the same on every replay (%s)" % str(p1))
	# Rising water follows its event, holds, then drains.
	z.on_event("boss_phase", {"action": "flood"})
	z.advance(4.0)
	var flood: Dictionary = z.volumes[7]
	var risen := near(float(flood.hi), 30.0)
	z.advance(2.0 + 4.0 + 0.1)
	check(risen and near(float(flood.hi), -20.0), "a boss phase floods the arena, and it drains after its hold")
	st = _trav_actor(z, "ground", Vector2(3700, 800))
	z.on_event("boss_phase", {"action": "flood"})
	z.advance(4.0)
	_trav_run(st, z, 0.5, Vector2.ZERO)
	check(st.sink_depth > 0.0, "rising water is deep water while it stands")

## Movement arts through the Game: Plunge strikes, glide costs QI, Swallow Dart shares the dodge cooldown,
## sect grounds refuse flight and a climber cannot use techniques.
func arts_combat_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "bg_whispering_bamboo")
	for sid in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	check(str(Game.submit({"type": "plunge"}).get("reason", "")) == "locked", "Plunge must be learned")
	for art in ["plunge", "falling_leaf_glide", "swallow_dart"]: Game.progression.apply_learn_secret_art(c.id, art)
	check(Game.combat.knows_art(c, "plunge") and Game.combat.knows_art(c, "glide") and Game.combat.knows_art(c, "air_dash"), "learned arts are known by their movement name")
	var geo: ZoneGeometry = Game.room_rt.geometry
	var foe: EnemyState = Game.enemies.spawn_at("green_viper", st.plane + Vector2(30, 0), 12)
	check(foe != null, "a foe to plunge on")
	var here: Vector2 = st.plane
	st.surface = null
	st.altitude = 150.0
	st.air_peak = 150.0
	st.vertical_speed = 0.0
	st.jumps_used = 1
	var r := Game.submit({"type": "plunge"})
	check(r.get("ok", false) and st.plunging, "Plunge in the air %s" % str(r))
	check(str(Game.submit({"type": "plunge"}).get("reason", "")) in ["cooldown", "not_airborne"], "one Plunge at a time; then it rests 4 s")
	var hp0 := 0.0
	if foe:
		foe.plane = here + Vector2(30, 0)
		foe.altitude = 0.0
		hp0 = foe.pools.hp
	_fall_until_landed(st, geo)
	Game.tick(0.05)
	check(st.plunge_impact.is_empty() and (foe == null or foe.pools.hp < hp0), "the Plunge lands a blow within 60")
	check(foe == null or not foe.alive or foe.pools.has_status("stun"), "and stuns for half a second")
	# Glide costs 2 QI a second, and stops when you land.
	c.pools.qi = c.pools.max_qi
	st.surface = null
	st.altitude = 200.0
	st.vertical_speed = -10.0
	r = Game.submit({"type": "glide", "on": true})
	var qi0: float = c.pools.qi
	for i in 20: Game.tick(0.05)
	check(r.get("ok", false) and Game.combat.is_gliding(c.id) and near(qi0 - c.pools.qi, 2.0, 0.3), "gliding drains 2 QI a second (%.2f)" % (qi0 - c.pools.qi))
	_fall_until_landed(st, geo)
	Game.tick(0.05)
	check(not Game.combat.is_gliding(c.id), "landing ends the glide")
	# Swallow Dart: an Evade tap in the air, once per airtime, on the dodge's cooldown.
	var had_dodge: bool = c.cultivator.unlocked.has("dodge_dash")
	c.cultivator.unlocked["dodge_dash"] = true
	c.pools.cooldowns.erase("dodge")
	st.surface = null
	st.altitude = 100.0
	st.vertical_speed = 0.0
	st.air_dash_used = false
	r = Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1})
	check(r.get("air_dash", false) and st.air_dash_used and c.pools.cooldown("dodge") > 0.0, "Evade in the air is Swallow Dart %s" % str(r))
	if not had_dodge: c.cultivator.unlocked.erase("dodge_dash")
	_fall_until_landed(st, geo)
	# Sect grounds refuse flight; techniques wait while climbing.
	var room0: Dictionary = Game.room_rt.def
	Game.room_rt.def = room0.duplicate()
	Game.room_rt.def.type = "sect"
	check(not Game.combat.flight_allowed(c.id), "no flight on sect grounds")
	Game.room_rt.def = room0
	st.climbing = {"id": "test_ladder", "kind": "ladder"}
	var slot0 = c.cultivator.technique_slots[0] if c.cultivator.technique_slots.size() > 0 else null
	if slot0 != null and str(slot0) != "":
		check(str(Game.submit({"type": "use_technique", "slot": 0, "facing": 1}).get("reason", "")) == "climbing", "techniques wait while you climb")
	check(str(Game.submit({"type": "basic_attack", "facing": 1}).get("reason", "")) == "climbing", "and so do attacks")
	st.climbing = {}

# ------------------------------------------------------------------ S43 rules 10-12: bands, shots, navigation, allies (V2c)
func nav_suite() -> void:
	# Rule 10: the melee band is -30..+60 of the attacker's height, Qi arcs -10..+80.
	var ground := {"x": 0.0, "y": 800.0, "alt": 0.0}
	var melee := {"x": [0, 60], "depth": 30, "alt": ContentDB.movement("combat_bands.melee", [])}
	var qi_arc := {"x": [0, 60], "depth": 30, "alt": ContentDB.movement("combat_bands.qi_arc", [])}
	var on_roof := {"x": 30.0, "y": 800.0, "alt": 88.0, "half_width": 14.0, "height": 88.0}
	var mid_jump := {"x": 30.0, "y": 800.0, "alt": 40.0, "half_width": 14.0, "height": 88.0}
	check(not CombatAuthority.hit_test(ground, 1, melee, on_roof) and CombatAuthority.hit_test(ground, 1, melee, mid_jump),
		"a ground fighter cannot strike a target on an 88 roof, but can strike it mid-jump")
	check(CombatAuthority.hit_test(ground, 1, qi_arc, {"x": 30.0, "y": 800.0, "alt": 75.0, "half_width": 14.0, "height": 40.0})
		and not CombatAuthority.hit_test(ground, 1, melee, {"x": 30.0, "y": 800.0, "alt": 75.0, "half_width": 14.0, "height": 40.0}), "a Qi arc reaches 80 up; a blow reaches 60")
	var jb: Array = ContentDB.entry("weapon_families", "jian").altitude
	var vb: Array = ContentDB.entry("enemies", "green_viper").attacks[0].hitbox.alt
	check(near(float(jb[0]), -30.0) and near(float(jb[1]), 60.0) and near(float(vb[0]), -30.0) and near(float(vb[1]), 60.0), "weapons and monsters strike in the melee band")
	# Shots stop at blocks and walls, never at platform decks.
	var z := _trav_zone()
	check(z.stops_shot(Vector2(830, 730), 40.0) and not z.stops_shot(Vector2(830, 730), 70.0) and not z.stops_shot(Vector2(400, 650), 58.0),
		"a shot stops at a crate below its top, flies over it, and passes a roof deck")
	# Rule 11: the navigation graph, by species movement.
	var jumper := {"jump": 530, "climb": false, "drop": true}
	var g: Dictionary = z.nav_graph(jumper)
	var kinds := func(from: String, to: String) -> Array:
		return g.get(from, []).filter(func(e): return e.to == to).map(func(e): return e.kind)
	check(kinds.call("ground", "deck") == ["jump"] and kinds.call("deck", "ground") == ["drop"] and kinds.call("ground", "crate") == ["jump"],
		"a jumper can hop onto a 100 deck and a crate and drop back down")
	check(kinds.call("ground", "wall").is_empty(), "a 300 wall is out of a 530 jump")
	check(z.nav_graph({"jump": 0, "climb": false, "drop": true}).get("ground", []).filter(func(e): return e.to == "deck").is_empty(), "a species that cannot jump stays below")
	var climber: Dictionary = z.nav_graph({"jump": 0, "climb": true, "drop": true})
	check(climber.get("ground", []).any(func(e): return e.to == "loft" and e.kind == "climb"), "a climber takes the ladder to the loft")
	var z2 := _trav_zone()
	check(str(z2.nav_graph(jumper)) == str(g), "the graph is identical on two builds of the same room")
	check(z.nav_path("ground", "deck", jumper).size() == 1 and z.nav_path("deck", "loft", {"jump": 0, "climb": true, "drop": true}).size() == 2,
		"paths chain drop and climb edges")
	# In a real room: a jumping monster follows the player onto a ledge; one that cannot jump gives up.
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wg_echo_cliffs")
	for sid in ["stun", "slow", "shock", "spawn_protection"]: Game.combat.cure_status(c.id, sid)
	var geo: ZoneGeometry = Game.room_rt.geometry
	for e0 in Game.room_rt.living_enemies(): e0.alive = false
	var ledge: WalkSurface = geo.index.get("ledge_0")
	st.surface = ledge
	st.plane = ledge.bounds.get_center()
	st.altitude = ledge.height_at(st.plane)
	st.vertical_speed = 0.0
	c.pools.hp = c.pools.max_hp
	var hunter: EnemyState = Game.enemies.spawn_at("mudwater_bandit", Vector2(ledge.bounds.get_center().x + 60, 860), 16)
	var plodder: EnemyState = Game.enemies.spawn_at("stone_tortoise", Vector2(ledge.bounds.get_center().x - 60, 860), 5)
	for e1 in [hunter, plodder]:
		e1.ai.state = "aggro"
		e1.ai.timer = 99.0
		e1.threat[c.id] = 1.0
	var on_ledge := false
	var unreach := 0.0
	for i in 240:
		Game.tick(0.05)
		c.pools.hp = c.pools.max_hp
		if hunter.surface_id == "ledge_0": on_ledge = true
		unreach = maxf(unreach, float(plodder.ai.get("unreach", 0.0)))
		st.surface = ledge
		st.altitude = ledge.height_at(st.plane)
	check(on_ledge, "a bandit jumps up the ledge after you")
	check(unreach >= 2.0, "a tortoise that cannot jump finds you out of reach (%.1f s)" % unreach)
	check(str(plodder.ai.state) == "return" or bool(plodder.ai.get("leashed", false)) or plodder.surface_id == plodder.home_surface, "after 6 s it goes home to heal")
	# Rule 12: an ally that cannot reach its owner blinks to them after 2 s.
	var high: WalkSurface = geo.index.get("ledge_2")
	st.surface = high
	st.plane = high.bounds.get_center()
	st.altitude = high.height_at(st.plane)
	var pal := EnemyState.new()
	pal.team = "ally"
	pal.def = {"name": "Test", "movement": {"jump": 0, "climb": false, "fly": false, "drop": true}}
	pal.plane = Vector2(st.plane.x - 100, 860)
	pal.surface_id = "ground"
	pal.ai = {"state": "follow", "timer": 0.0, "offset": 56, "depth_offset": 14, "speed": 200}
	for e2 in Game.room_rt.living_enemies(): e2.alive = false
	for i in 50: AllyBrain.think(Game, pal, 0.05, 1.0, 36.0)
	check(pal.surface_id == "ledge_2" and near(pal.altitude, 300.0), "an ally that cannot follow blinks to its owner after 2 s")
	pal.plane = Vector2(st.plane.x + 900, 860)
	pal.surface_id = "ground"
	AllyBrain.think(Game, pal, 0.05, 1.0, 36.0)
	check(pal.plane.distance_to(st.plane) < 120.0, "and at once when more than 480 away")

# ------------------------------------------------------------------ emotes (S34)
func emotes_suite() -> void:
	var starting := ContentDB.all("emotes").filter(func(e): return str(e.get("achievement", "")) == "")
	check(starting.size() >= 6, "six emotes from the start (%d)" % starting.size())
	check(Game.submit({"type": "emote", "emote": "bow"}).get("ok", false), "a starting emote plays")
	var done: Dictionary = Game.account.achievements.done
	var had := done.has("valley_champion")
	done.erase("valley_champion")
	check(str(Game.submit({"type": "emote", "emote": "champion"}).get("reason", "")) == "locked", "an achievement emote waits for its achievement")
	done["valley_champion"] = true
	check(Game.submit({"type": "emote", "emote": "champion"}).get("ok", false), "and plays once it is earned")
	if not had: done.erase("valley_champion")

# ------------------------------------------------------------------ saves (Part 7 · Save migration)
func save_suite() -> void:
	var folder := "user://save_suite/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	var repo := RepositoryLocal.new(folder)
	check(repo.save_character(1, {"version": 3, "name": "First"}) == OK, "a character saves")
	check(repo.save_character(1, {"version": 3, "name": "Second"}) == OK, "saving again keeps the previous file as .bak")
	var f := FileAccess.open(repo.character_path(1), FileAccess.WRITE)
	f.store_string("{ this is not json")
	f.close()
	var back: Dictionary = repo.load_character(1)
	check(str(back.get("name", "")) == "First" and repo.last_recovered.has("char_1.json"), "a damaged save is restored from its .bak")
	# S40: a manual export carries the account and characters; importing it restores them.
	repo.save_account({"version": 3, "account_id": "export-test", "characters": {"1": {}}})
	var saved_repo = Saves.repo
	Saves.repo = repo
	var path := Saves.export_bundle([1])
	check(path != "" and FileAccess.file_exists(path), "a save exports to one file (%s)" % path)
	repo.save_account({"version": 3, "account_id": "changed", "characters": {}})
	check(Saves.import_bundle(path) == OK and str(repo.load_account().get("account_id", "")) == "export-test", "importing the export restores the account")
	check(str(repo.load_character(1).get("name", "")) != "", "and its characters")
	check(Saves.import_bundle("user://no_such_file.json") != OK, "a missing or foreign file is refused")
	check(Saves.list_exports().any(func(e): return str(e.path) == path), "exports are listed for restoring")
	DirAccess.remove_absolute(path)
	Saves.repo = saved_repo
	var old: Dictionary = Saves.migrate_character({"name": "Old", "version": 2})
	check(int(old.get("version", 0)) == Saves.VERSION, "an older character file is brought to the current version")
