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
	paths_above_suite()
	forge_upkeep_suite()
	sword_loadout_suite()
	natal_wardrobe_suite()
	talisman_suite()
	herb_nature_suite()
	new_forms_suite()
	guild_suite()
	tribulation_suite()
	body_path_suite()
	heaven_suite()
	arts_suite()
	vows_suite()
	herbs_suite()
	garden_suite()
	herb_prep_suite()
	beasts_suite()
	bloodline_suite()
	pet_growth_suite()
	beast_world_suite()
	beast_arena_suite()
	relations_suite()
	bonds_suite()
	grudges_suite()
	calendar_suite()
	world_events_suite()
	fortune_suite()
	tower_activity_ranking_suite()
	mobile_conventions_suite()
	mortal_leisure_suite()
	territory_suite()
	depth_hooks_suite()
	v2_hooks_suite()
	weapon_families_suite()
	soul_poison_suite()
	blood_buddhist_suite()
	sect_roles_suite()
	swarm_array_puppet_suite()
	emotes_suite()
	save_suite()
	print("rules_tests: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ S43 Paths Above and the room catalogue
func paths_above_suite() -> void:
	# Every row names a real optional ledge (a surface or a block) marked for that later art.
	for e in ContentDB.all("paths_above"):
		var room := ContentDB.room(str(e.room))
		var named := false
		for s in room.get("surfaces", []) + room.get("blocks", []):
			if str(s.id) == str(e.surface) and str(s.get("later", "")) == str(e.art): named = true
		check(named, "Paths Above row %s names a later ledge" % e.id)
	check(ContentDB.has_entry("paths_above", "wp_west:pine_top") and ContentDB.has_entry("paths_above", "cf_behind_falls:shaft_top"),
		"the catalogue's later ledges (Willow Path West's pine top, the falls' Wall-Step shaft) are rows")
	# A cracked block (the Lower Pit slab over the shard) stops walking until a Plunge breaks it.
	var pit := ZoneGeometry.new()
	pit.configure(WorldAuthority.compile_geometry(ContentDB.room("sq_lower_pit")))
	var slab: WalkSurface = pit.index.get("cracked_slab")
	check(slab != null and slab.cracked and pit.wall_face_at(Vector2(1900, 810), 10.0, "ground"), "the Lower Pit slab is a cracked block that stops you")
	pit.break_surface("cracked_slab")
	check(slab != null and slab.disabled and not pit.wall_face_at(Vector2(1900, 810), 10.0, "ground"), "a broken slab no longer blocks")
	# The Jade trial's planks rise with the room clock; the libraries' upper floors are sealed by rank.
	var trial := ZoneGeometry.new()
	trial.configure(WorldAuthority.compile_geometry(ContentDB.room("sf_trial_jade")))
	check(trial.movers.size() == 2 and (trial.index.plank_1 as WalkSurface).moving, "the Jade trial has two moving planks")
	var sealed := 0
	for cl in ContentDB.room("ja_library").get("climbables", []):
		if cl.has("requires"): sealed += 1
	check(sealed == 2, "both library floors are sealed by rank (%d)" % sealed)
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Game.world.apply_teleport(c.id, "wp_west")
	Game.account.paths_above.erase("wp_west:pine_top")
	var heard := []
	var listen := func(n: String, p: Dictionary):
		if n == "path_above_found": heard.append(p)
	GameEvents.event.connect(listen)
	for sid in ["pine_top", "pine_top", "willow_branch_a"]:
		GameEvents.emit_event("landed", {"actor": c.id, "surface": sid, "fall_height": 0.0, "plunge": false})
		GameEvents.flush()
	GameEvents.event.disconnect(listen)
	check(Game.account.paths_above.has("wp_west:pine_top") and heard.size() == 1, "standing on a later ledge finds it, once (%d)" % heard.size())
	check(Game.account.snapshot().paths_above.has("wp_west:pine_top"), "found ledges are saved with the account")

# ------------------------------------------------------------------ S47 gear upkeep
func forge_upkeep_suite() -> void:
	var c = Game.active()
	if c == null: return
	Unlocks.force_unlock(c.id, "smithing")
	var add := func(id: String, quality := "common") -> Dictionary:
		Game.inventory.apply_add_equipment(c.id, id, int(ContentDB.item(id).get("ilv", 10)), quality, "test")
		var best: Dictionary = {}
		for it in c.inventory.bag:
			if it != null and str(it.id) == id and (best.is_empty() or int(it.uid) > int(best.uid)): best = it
		return best
	# Pity: from +5 a try can fail; each failure adds 5% to the next try on that piece, a success clears it.
	var jian: Dictionary = add.call("jadeiron_jian")
	jian.enhance = 5
	var row: Dictionary = Game.crafting.grade_row("jadeiron_jian")
	check(str(row.metal) == "jadeiron", "an Earth piece is enhanced with Jadeiron (salvage.json)")
	check(near(Game.crafting.enhance_chance(jian), 0.88), "the try from +5 is 88%% (%.2f)" % Game.crafting.enhance_chance(jian))
	Game.inventory.apply_add(c.id, "jadeiron", 200, "test")
	Game.inventory.apply_add(c.id, "spirit_stone_shard", 60, "test")
	Game.economy.apply_currency("silver_tael", 50000, "test")
	var fails := 0
	var saw_reset := false
	for i in 40:
		var before := float(jian.get("pity", 0.0))
		var r := Game.submit({"type": "enhance", "uid": int(jian.uid)})
		if not r.get("ok", false): break
		if r.success:
			saw_reset = saw_reset or before > 0.0
			check(near(float(jian.get("pity", 0.0)), 0.0, 0.0) or float(jian.get("pity", 0.0)) == 0.0, "a success clears the pity")
			if int(jian.enhance) >= 9: break
		else:
			fails += 1
			check(near(float(jian.pity), before + 0.05, 0.001), "a failure adds 5%% pity (%.2f -> %.2f)" % [before, float(jian.pity)])
		if int(jian.enhance) >= 9: break
	check(fails > 0 and saw_reset, "pity builds on failures and resets on a success (%d failures)" % fails)
	check(near(Game.crafting.enhance_chance({"id": "jadeiron_jian", "enhance": 7, "pity": 0.1}, 2), 1.0 - 0.36 + 0.1 + 0.05, 0.001),
		"pity and two Refining Essence add to the chance")
	# Inherit moves N - 2 for 2 Spirit Stones a level; the old piece goes back to +0.
	var old_jian: Dictionary = add.call("jadeiron_jian")
	old_jian.enhance = 7
	var new_jian: Dictionary = add.call("cloudsteel_jian") if ContentDB.has_entry("items", "cloudsteel_jian") else add.call("jadeiron_jian")
	Game.economy.apply_currency("spirit_stone", 50, "test")
	var stones0: int = Game.economy.balance("spirit_stone")
	var ih := Game.submit({"type": "inherit_enhancement", "from": int(old_jian.uid), "to": int(new_jian.uid)})
	check(ih.get("ok", false) and int(new_jian.enhance) == 5 and int(old_jian.enhance) == 0 and stones0 - Game.economy.balance("spirit_stone") == 10,
		"Inherit moves +7 as +5 for 10 Spirit Stones (%s)" % str(ih))
	var robe: Dictionary = add.call("jadeiron_robe")
	check(not Game.submit({"type": "inherit_enhancement", "from": int(new_jian.uid), "to": int(robe.uid)}).get("ok", true), "Inherit keeps to one slot")
	# Salvage: metal and essence by grade; locked pieces are never touched.
	var a: Dictionary = add.call("jadeiron_robe")
	var b: Dictionary = add.call("jadeiron_robe")
	c.inventory.locked[int(b.uid)] = true
	var ess0: int = c.inventory.count("refining_essence")
	var sv := Game.submit({"type": "salvage", "items": [int(a.uid), int(b.uid)]})
	check(sv.get("ok", false) and (sv.items as Array).size() == 1 and c.inventory.find_uid(int(b.uid)) >= 0 and c.inventory.find_uid(int(a.uid)) < 0,
		"Salvage takes the free piece and never the locked one")
	check(c.inventory.count("refining_essence") - ess0 == 3, "an Earth piece gives 2 Jadeiron and 3 Refining Essence")
	c.inventory.locked.erase(int(b.uid))
	# Reroll: the locked affix stays, the reroll costs double, and the old roll can be kept.
	var fine: Dictionary = add.call("jadeiron_robe", "superior")
	check((fine.affixes as Array).size() >= 2, "a Superior piece has affixes to reroll")
	Game.inventory.apply_add(c.id, "refining_essence", 40, "test")
	var plain_cost: Dictionary = Game.crafting.reroll_cost(fine)
	check(Game.submit({"type": "lock_affix", "uid": int(fine.uid), "affix": 0}).get("ok", false), "lock the first affix")
	var locked_cost: Dictionary = Game.crafting.reroll_cost(fine)
	check(int(locked_cost.essence) == 2 * int(plain_cost.essence) and int(locked_cost.taels) == 2 * int(plain_cost.taels), "a locked affix doubles the reroll")
	var kept: Dictionary = (fine.affixes[0] as Dictionary).duplicate()
	var old_affixes: Array = (fine.affixes as Array).duplicate(true)
	var rr := Game.submit({"type": "reroll_affixes", "uid": int(fine.uid)})
	check(rr.get("ok", false) and str(rr.new[0].id) == str(kept.id) and near(float(rr.new[0].value), float(kept.value)), "the locked affix survives the reroll")
	check(Game.submit({"type": "choose_affixes", "uid": int(fine.uid), "keep": "old"}).get("ok", false) and str(fine.affixes) == str(old_affixes) and not fine.has("pending_affixes"),
		"keeping the old roll leaves the piece as it was")
	Game.submit({"type": "reroll_affixes", "uid": int(fine.uid)})
	var fresh: Array = (fine.pending_affixes as Array).duplicate(true)
	Game.submit({"type": "choose_affixes", "uid": int(fine.uid), "keep": "new"})
	check(str(fine.affixes) == str(fresh), "taking the new roll keeps it")
	# Tidy up the test pieces.
	for it in [jian, old_jian, new_jian, robe, b, fine]:
		var i: int = c.inventory.find_uid(int(it.uid))
		if i >= 0: Game.inventory.apply_remove_index(c.id, i, 1, "test")

# ------------------------------------------------------------------ S47 flying sword, Sword Intent, loadouts, self-detonation
func sword_loadout_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "dao_tree")
	# The Sword Dao's third tier teaches Sword Release.
	c.cultivator.techniques_known.erase("sword_release")
	c.cultivator.daos["sword"] = {"tier": 2, "insight": 0.0}
	var need := 0.0
	for t in 60:
		if ProgressionRules.dao_tier_for(need) >= 3: break
		need += 50.0
	Game.progression.apply_insight(c.id, "sword", need + 1.0, "test:sword:%d" % randi())
	check(int(c.cultivator.daos.sword.tier) >= 3 and c.cultivator.techniques_known.has("sword_release"), "Sword Dao tier 3 teaches Sword Release")
	# Sword Release needs a jian in hand; it flies for 8 s, strikes the nearest foe, and the hands fight with palms.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_jian", 27, "common", "test")
	var ji: int = c.inventory.first_index("jadeiron_jian")
	var held_before = c.inventory.equipped.get("weapon")
	# The test character's realm may be below the jian's; it is put in hand directly (wearing rules are tested elsewhere).
	c.inventory.equipped["weapon"] = c.inventory.bag[ji]
	c.inventory.bag[ji] = held_before
	Unlocks.force_unlock(c.id, "attack")
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:sword_release")
	var heard := {}
	var listen := func(n: String, p: Dictionary):
		if n in ["sword_released", "sword_returned", "sword_intent_changed", "loadout_swapped", "artifact_detonated", "projectile_spawned"]:
			heard[n] = int(heard.get(n, 0)) + 1
			if n == "projectile_spawned" and str(p.get("art", "")) == "flying_sword": heard["sword_strike"] = int(heard.get("sword_strike", 0)) + 1
	GameEvents.event.connect(listen)
	var rel := Game.submit({"type": "toggle_sword_release"})
	check(rel.get("ok", false) and Game.combat.sword_released.has(c.id), "the jian is released (%s)" % str(rel))
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(200, 0), 2)
	for i in 30:
		Game.tick(0.05)
		GameEvents.flush()
	check(int(heard.get("sword_strike", 0)) >= 1, "the flying sword strikes the nearest foe (%d)" % int(heard.get("sword_strike", 0)))
	Game.combat.basic_attack(c, 1)
	var tl: Dictionary = Game.combat.timeline(c.id)
	check(str(tl.family) == "fists" and near(float((tl.get("step", {}) as Dictionary).get("mult", 1.0)), float(ContentDB.entry("weapon_families", "fists").combo[0].get("mult", 1.0)) * 0.8, 0.01),
		"while it flies, the hands fight with Qi palms at x0.8")
	for i in 200:
		Game.tick(0.05)
		GameEvents.flush()
		if not Game.combat.sword_released.has(c.id): break
	check(not Game.combat.sword_released.has(c.id) and int(heard.get("sword_returned", 0)) >= 1, "the sword returns after 8 s")
	# Sword Intent: consecutive jian hits stack to 10 (+1% penetration each) and fade 3 s after the last.
	if foe == null or not foe.alive: foe = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(40, 0), 2)
	for i in 12: Game.combat._feed_intent(c, foe, {"source": "basic"})
	check(int(Game.combat.sword_intent[c.id].stacks) == 10 and near(Game.combat.intent_penetration(c), 0.10, 0.001), "ten jian hits give ten stacks of Intent (+10% penetration)")
	for i in 70:
		Game.tick(0.05)
	GameEvents.flush()
	check(int(Game.combat.sword_intent[c.id].stacks) == 0, "Intent fades 3 s after the last jian hit")
	# Dual loadout: a spare weapon, a swap, and each weapon keeps its own technique bar.
	Unlocks.force_unlock(c.id, "dual_loadout")
	var spear_id := "iron_spear"
	Game.inventory.apply_add_equipment(c.id, spear_id, 10, "common", "test")
	var si: int = c.inventory.first_index(spear_id)
	var ss := Game.submit({"type": "set_spare_weapon", "index": si})
	check(ss.get("ok", false) or str(ss.get("reason", "")) == "cannot_wear", "a spare weapon follows the wearing rules (%s)" % str(ss))
	if not ss.get("ok", false):   # the test character has not passed the Entry Trial: the spear is placed directly
		c.inventory.loadout["spare"] = c.inventory.bag[si]
		c.inventory.bag[si] = null
	var bar_a: Array = c.cultivator.technique_slots.duplicate()
	var sw := Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(sw.get("ok", false) and str(c.inventory.equipped.weapon.id) == spear_id and str(c.inventory.loadout.spare.id) == "jadeiron_jian", "Swap puts the spear in hand and the jian in the spare slot")
	c.cultivator.technique_slots[0] = null
	var bar_b: Array = c.cultivator.technique_slots.duplicate()
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(str(c.cultivator.technique_slots) == str(bar_a), "swapping back brings the jian's own bar")
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	check(str(c.cultivator.technique_slots) == str(bar_b) and int(c.cultivator.daos.sword.tier) >= 3, "the spear's bar is kept too, and no Dao tier is touched")
	Game.submit({"type": "swap_loadout"})
	GameEvents.flush()
	# Self-detonation needs a confirmation, then the spare artifact is gone.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_robe", 27, "common", "test")
	var ri: int = c.inventory.first_index("jadeiron_robe")
	var d1 := Game.submit({"type": "self_detonate", "index": ri})
	check(str(d1.get("reason", "")) == "confirm" and c.inventory.first_index("jadeiron_robe") == ri, "self-detonation asks first and destroys nothing")
	var d2 := Game.submit({"type": "self_detonate", "index": ri, "confirm": true})
	GameEvents.flush()
	check(d2.get("ok", false) and c.inventory.bag[ri] == null and int(heard.get("artifact_detonated", 0)) == 1, "confirmed, the spare artifact bursts and is gone")
	GameEvents.event.disconnect(listen)
	# Put things back.
	Game.submit({"type": "set_spare_weapon", "index": -1})
	var worn = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = held_before
	if held_before != null:
		var hb: int = c.inventory.find_uid(int(held_before.get("uid", -1)))
		if hb >= 0: c.inventory.bag[hb] = worn
	for id in ["jadeiron_jian", spear_id]:
		var k: int = c.inventory.first_index(id)
		if k >= 0: Game.inventory.apply_remove_index(c.id, k, 1, "test")
	if foe != null and foe.alive: foe.alive = false

# ------------------------------------------------------------------ S47 v1.1 weapon families: heavy sabre, fan, flute
## Put a fresh weapon of this id straight into the hand (wearing rules are tested elsewhere); returns what was held.
func _wield(c, item_id: String):
	Game.inventory.apply_add_equipment(c.id, item_id, 14, "common", "test")
	var i: int = c.inventory.first_index(item_id)
	var held = c.inventory.equipped.get("weapon")
	c.inventory.equipped["weapon"] = c.inventory.bag[i]
	c.inventory.bag[i] = null
	Game.combat.refresh_stats(c.id)
	return held

func _idle_hands(c) -> void:
	for i in 40:
		if not Game.combat.is_busy(c.id): break
		Game.tick(0.05)
	GameEvents.flush()

func weapon_families_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "attack")
	Unlocks.force_unlock(c.id, "composure")
	for fam_id in ["heavy_sabre", "fan", "flute"]:
		var fam := ContentDB.entry("weapon_families", fam_id)
		var look := str(fam.get("appearance", [""])[0])
		check(not fam.is_empty() and Wardrobe.parts.weapon.has(look) and Wardrobe.parts._attack_by_weapon.has(look), "the %s family exists with its avatar weapon (%s)" % [fam_id, look])
		for grade in ["training", "iron", "jadeiron", "cloudsteel"]:
			check(ContentDB.entry("artifacts", "%s_%s" % [grade, fam_id]).get("family", "") == fam_id, "%s %s is a %s" % [grade, fam_id, fam_id])
	var heard := {"hits": {}, "arts": {}, "pulse": 0, "melody_off": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "hit_landed" and str(p.get("target_kind", "")) == "enemy":
			heard.hits[str(p.target)] = int(heard.hits.get(str(p.target), 0)) + 1
		if n == "projectile_spawned": heard.arts[str(p.art)] = int(heard.arts.get(str(p.art), 0)) + 1
		if n == "melody_pulse": heard.pulse = int(heard.pulse) + 1
		if n == "melody_changed" and not p.get("on", false): heard.melody_off = str(p.get("reason", ""))
	GameEvents.event.connect(listen)
	var lv := ProgressionRules.level(c) + 12
	# The heavy sabre: slow, a cleave that reaches three foes in a line, and armour break.
	var held_before = _wield(c, "iron_heavy_sabre")
	check(str(StatRules.family(c).id) == "heavy_sabre", "an iron heavy sabre puts the heavy sabre family in hand")
	var foes: Array = []
	for i in 3: foes.append(Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(36 + i * 20, 0), lv))
	_idle_hands(c)
	heard.hits = {}
	Game.combat.basic_attack(c, 1)
	for i in 20:
		Game.tick(0.05)
	GameEvents.flush()
	var struck := 0
	for f in foes:
		if heard.hits.has(str(f.uid)): struck += 1
	check(struck >= 2, "one sabre cleave strikes several foes in a line (%d of 3)" % struck)
	var foe: EnemyState = foes[0]
	Game.combat._weapon_after_hit(c, foe, {"armour_break": {"chance": 1.0, "duration_s": 4}})
	check(foe.pools.has_status("sundered"), "an armour break leaves the foe Sundered")
	var pv := Game.combat.player_view(c)
	pv["accuracy"] = 99999.0
	var ev := Game.combat.enemy_view(foe)
	ev["physical_defense"] = 400.0
	var atk := {"damage_type": "physical", "element": "none", "mult": [1.0, 1.0], "range": [1.0, 1.0], "source": "test"}
	var r1 := CombatRules.resolve(pv, ev, atk, Rng.keyed(7, "sunder"))
	ev["sundered"] = false
	var r2 := CombatRules.resolve(pv, ev, atk, Rng.keyed(7, "sunder"))
	check(int(r1.amount) > int(r2.amount), "a Sundered foe takes more from every blow (%d > %d)" % [int(r1.amount), int(r2.amount)])
	# The fan: wind that lifts a foe (helpless until it lands) and a third stroke thrown out and back.
	_wield(c, "iron_fan")
	var foe2: EnemyState = foes[1]
	Game.combat._weapon_after_hit(c, foe2, {"knockup_s": 0.8})
	check(foe2.pools.has_status("launched") and foe2.pools.blocked("move") and foe2.pools.blocked("attack"), "the fan's wind launches a foe: it can neither move nor strike")
	for i in 8: Game.tick(0.05)
	check(foe2.hover > 20.0, "a launched foe rises into the air (%.0f)" % foe2.hover)
	for i in 14: Game.tick(0.05)
	check(not foe2.pools.has_status("launched") and foe2.hover == 0.0, "and lands when it ends")
	for f in foes:
		f.alive = false
	var target: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(130, 0), lv)
	_idle_hands(c)
	heard.hits = {}
	heard.arts = {}
	var fam_fan := ContentDB.entry("weapon_families", "fan")
	Game.combat._start_step(c, fam_fan, 2, 1)
	for i in 50:
		Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.arts.get("fan", 0)) == 1, "the fan's third stroke throws the fan")
	check(int(heard.hits.get(str(target.uid), 0)) >= 2, "the thrown fan cuts on its way out and again on its way back (%d)" % int(heard.hits.get(str(target.uid), 0)))
	target.alive = false
	# The flute: a note of Qi at the tap; held, a melody aura that slows, heals and drains Composure.
	_wield(c, "iron_flute")
	_idle_hands(c)
	heard.arts = {}
	Game.combat.basic_attack(c, 1)
	for i in 14: Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.arts.get("note", 0)) == 1, "a flute's tap sends a note")
	_idle_hands(c)
	var near_foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(120, 0), lv)
	var ally: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-80, 0), 5)
	ally.team = "ally"
	ally.pools.hp = ally.pools.max_hp * 0.5
	c.pools.composure = 100.0
	c.pools.hp = c.pools.max_hp * 0.6
	var hp0: float = c.pools.hp
	var on := Game.submit({"type": "channel_melody", "on": true})
	check(on.get("ok", false) and Game.combat.is_playing(c.id), "holding Attack with a flute plays the melody (%s)" % str(on))
	check(Game.combat.move_factor(c.id) <= 0.5 + 0.001, "the player walks at half pace while playing")
	for i in 22: Game.tick(0.05)
	GameEvents.flush()
	check(int(heard.pulse) >= 2, "the melody pulses every half second (%d)" % int(heard.pulse))
	check(near_foe.pools.has_status("slow"), "foes within the aura are slowed")
	check(ally.pools.hp > ally.pools.max_hp * 0.5 and c.pools.hp > hp0, "allies and the player recover health as it plays")
	check(c.pools.composure < 100.0 - 6.0, "the melody drains Composure (%.1f)" % c.pools.composure)
	Game.submit({"type": "channel_melody", "on": false})
	GameEvents.flush()
	check(not Game.combat.is_playing(c.id) and heard.melody_off == "released", "letting go ends it")
	c.pools.composure = 1.0
	Game.submit({"type": "channel_melody", "on": true})
	check(not Game.combat.is_playing(c.id), "it will not start with almost no Composure")
	c.pools.composure = 6.0
	Game.submit({"type": "channel_melody", "on": true})
	for i in 30: Game.tick(0.05)
	GameEvents.flush()
	check(not Game.combat.is_playing(c.id) and heard.melody_off == "composure", "it ends when Composure runs out")
	# Confusion and Fear now move a monster: a feared foe backs away instead of closing in.
	near_foe.ai.state = "aggro"
	near_foe.ai.timer = 0.0
	var d0: float = absf(near_foe.plane.x - st.plane.x)
	Game.combat.apply_enemy_status(near_foe, {"id": "fear", "power": 1.0, "remaining": 1.5, "source": c.id})
	for i in 10: Game.tick(0.05)
	check(absf(near_foe.plane.x - st.plane.x) > d0 + 10.0 and str(near_foe.ai.state) == "aggro", "a feared monster runs from its foe")
	# Clear Heart Melody: 4% a second for 6 s on the caster and every ally within 220.
	ally.pools.hp = ally.pools.max_hp * 0.5
	var healed := Game.combat.heal_circle(c, 0.04, 6.0, 220.0, "test")
	for i in 20: Game.tick(0.05)
	check(healed >= 1 and ally.pools.hp > ally.pools.max_hp * 0.52, "Clear Heart Melody heals the allies beside the player over time (%d, %.2f)" % [healed, ally.pools.hp / ally.pools.max_hp])
	var ch := ContentDB.entry("techniques", "clear_heart_melody")
	check(float(ch.get("allies_heal_pct", 0)) == 0.04 and not ch.has("buff"), "Clear Heart Melody is a healing song, not a resting buff")
	# Their techniques carry the families' traits, and the library ones are taught by the Mission Hall.
	check(ContentDB.entry("techniques", "thunder_dao_arc").has("armour_break"), "the heavy sabre's arc breaks armour")
	check(bool(ContentDB.entry("techniques", "returning_crane_fan").projectile.get("returning", false)), "Returning Crane Fan flies out and back")
	check(str(ContentDB.entry("techniques", "reed_song").projectile.get("art", "")) == "note", "Reed Song sends notes")
	var hall := ContentDB.entry("shops", "jade_sect")
	var taught := {}
	for sitem in hall.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual": taught[str(sitem.learn)] = true
	var missing := []
	for t in ContentDB.all("techniques"):
		if str(t.get("source", "")) in ["library_1", "library_2", "library_3"] and not taught.has(str(t.id)): missing.append(str(t.id))
	check(missing.is_empty() and taught.has("clear_heart_melody") and taught.has("gale_fan"), "the Jade Sect Mission Hall teaches every library technique (missing %s)" % str(missing))
	GameEvents.event.disconnect(listen)
	near_foe.alive = false
	ally.alive = false
	Game.combat.ally_hots.clear()
	c.inventory.equipped["weapon"] = held_before
	Game.combat.refresh_stats(c.id)
	c.pools.composure = 100.0

# ------------------------------------------------------------------ S48 the Soul line, the Poison path and the S10 meridian gates
func soul_poison_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear", "poison"]: Game.combat.cure_status(c.id, sid)
	var meridians_before: Dictionary = c.cultivator.meridians.duplicate()
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var tox_before: float = c.cultivator.toxicity
	var lv := ProgressionRules.level(c) + 12
	# The mentor's techniques now have a teacher, and the Soul Dao's first three tiers teach the Soul line.
	var grants := {}
	for q in ContentDB.all("quests"):
		for fx in q.get("rewards", []) + q.get("on_accept", []):
			if fx is Dictionary and str(fx.get("kind", "")) == "learn_technique": grants[str(fx.get("technique", ""))] = str(q.id)
	for tid in ["mirror_mind_spike", "soul_lantern_ward", "still_water_focus"]:
		check(grants.has(tid), "%s is taught by a quest (%s)" % [tid, str(grants.get(tid, "none"))])
	for tid in ["sense_lock", "phantom_double", "soul_search"]: c.cultivator.techniques_known.erase(tid)
	c.cultivator.daos["soul"] = {"tier": 0, "insight": 0.0}
	var need := 0.0
	for t in 200:
		if ProgressionRules.dao_tier_for(need) >= 3: break
		need += 50.0
	Game.progression.apply_insight(c.id, "soul", need + 1.0, "teacher:test")
	check(c.cultivator.techniques_known.has("sense_lock") and c.cultivator.techniques_known.has("phantom_double") and c.cultivator.techniques_known.has("soul_search"),
		"Soul Dao tiers 1-3 teach Sense Lock, Phantom Double and Soul Search (tier %d)" % int(c.cultivator.daos.soul.tier))
	# Spirit is a main stat for soul attacks, whatever the weapon.
	c.cultivator.meridians["spirit"] = 0
	Game.combat.refresh_stats(c.id)
	var soul0: float = c.stats.value("soul_attack")
	c.cultivator.meridians["spirit"] = 60
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("soul_attack") > soul0 * 1.3, "60 Spirit lifts soul attack by more than a third (%.0f -> %.0f)" % [soul0, c.stats.value("soul_attack")])
	# S10 meridian gates open exactly at their thresholds.
	c.cultivator.meridians["spirit"] = 24
	check(not StatRules.gate_flag(c, "sense_cost_25"), "Spirit 24 opens no gate")
	c.cultivator.meridians["spirit"] = 25
	check(StatRules.gate_flag(c, "sense_cost_25") and not StatRules.gate_flag(c, "fear_immune_weaker"), "Spirit 25 opens the Sense gate and no more")
	c.cultivator.meridians["spirit"] = 100
	check(StatRules.gate_flag(c, "fear_immune_weaker") and StatRules.gate_flag(c, "soul_ignore_20"), "Spirit 100 opens all three Spirit gates")
	c.cultivator.meridians["essence"] = 0
	var air0 := Game.combat.air_qi_mult(c)
	c.cultivator.meridians["essence"] = 50
	check(near(Game.combat.air_qi_mult(c), air0 * 0.8, 0.001), "Essence 50: flight costs 20% less QI")
	c.cultivator.daos["soul"] = {"tier": 4, "insight": 0.0}
	c.cultivator.meridians["insight"] = 99
	var t4 := ProgressionRules.effective_dao_tier(c, "soul")
	c.cultivator.meridians["insight"] = 100
	check(t4 == 4 and ProgressionRules.effective_dao_tier(c, "soul") == 5, "Insight 100: a Dao at Explanation gives one tier more")
	c.cultivator.meridians["insight"] = 25
	c.cooldowns.erase("free_reroll_wk")
	var fake := {"id": "iron_jian", "affixes": [{"id": "x"}]}
	check(bool(Game.crafting.reroll_cost(fake, c).get("free", false)), "Insight 25: one affix reroll a week is free")
	c.cooldowns["free_reroll_wk"] = Clock.reset_week(Clock.now_utc())
	check(not Game.crafting.reroll_cost(fake, c).get("free", false), "and only one")
	# Agility 50: a second dodge charge.
	Unlocks.force_unlock(c.id, "dodge_dash")
	c.pools.cooldowns.erase("dodge")
	c.pools.cooldowns.erase("dodge_2")
	c.cultivator.meridians["agility"] = 0
	Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	var d2 := Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	check(not d2.get("ok", false), "without the gate a second dodge waits for the cooldown")
	c.pools.cooldowns.erase("dodge")
	c.cultivator.meridians["agility"] = 50
	Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	var d3 := Game.submit({"type": "dodge", "direction": Vector2.RIGHT, "facing": 1})
	check(d3.get("ok", false), "Agility 50: a second dodge charge (%s)" % str(d3))
	for i in 20: Game.tick(0.05)
	# Essence 25: the first technique of each fight costs no QI.
	_idle_hands(c)
	c.cultivator.meridians["essence"] = 25
	var slot_before = c.cultivator.technique_slots[0]
	c.cultivator.technique_slots[0] = "flowing_palm"
	if not c.cultivator.techniques_known.has("flowing_palm"): c.cultivator.techniques_known.append("flowing_palm")
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:flowing_palm")
	Game.combat.timeline(c.id)["fight_t"] = -999.0
	var q0: float = c.pools.qi
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and near(c.pools.qi, q0, 0.01), "Essence 25: the first technique of a fight is free (%s)" % str(u1))
	_idle_hands(c)
	c.pools.cooldowns.erase("tech:flowing_palm")
	var q1: float = c.pools.qi
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(c.pools.qi < q1, "the next one in the same fight is paid for")
	_idle_hands(c)
	c.cultivator.technique_slots[0] = slot_before
	# Sense Lock: a foe that evades everything cannot evade a locked soul.
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	foe.stats["evasion"] = 999999.0
	var heard := {"miss": 0, "hit": 0, "search": "", "broken": ""}
	var listen := func(n: String, p: Dictionary):
		if n == "hit_missed" and str(p.get("target", "")) == str(foe.uid): heard.miss = int(heard.miss) + 1
		if n == "hit_landed" and str(p.get("target", "")) == str(foe.uid): heard.hit = int(heard.hit) + 1
		if n == "soul_searched": heard.search = str(p.get("memory", "?"))
		if n == "illusion_broken": heard.broken = str(p.get("reason", ""))
	GameEvents.event.connect(listen)
	var atk := {"damage_type": "physical", "element": "none", "mult": [0.01, 0.01], "range": [1.0, 1.0], "source": "test"}
	for i in 30: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(int(heard.miss) >= 5, "an evasive foe dodges ordinary blows (%d of 30 missed)" % int(heard.miss))
	Game.combat._weapon_after_hit(c, foe, {"sense_lock_s": 8.0})
	heard.miss = 0
	for i in 30: Game.combat._player_hits_enemy(c, Game.combat.player_view(c), foe, atk, 1)
	GameEvents.flush()
	check(foe.pools.has_status("sense_locked") and int(heard.miss) == 0, "Sense Locked, it cannot evade (%d missed)" % int(heard.miss))
	foe.alive = false
	# Phantom Double: foes near it turn on the illusion; three strikes break it; time also ends it.
	var foe2: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(150, 0), lv)
	Game.combat._cast_illusion(c, ContentDB.entry("techniques", "phantom_double"))
	var aim := EnemyBrain.target_position(Game.enemies, foe2)
	check(str(aim.get("id", "")) == "decoy", "a foe near the illusion hunts it instead of the player")
	var d: Dictionary = Game.combat.decoys[c.id]
	foe2.plane = Vector2(float(d.x) + 30.0, float(d.y))
	foe2.facing = -1
	var ev := Game.combat.enemy_view(foe2)
	for i in 3: Game.combat._strike_decoy(foe2, ev, {"x": [0, 60], "depth": 30, "alt": [-30, 60]}, {})
	GameEvents.flush()
	check(not Game.combat.decoys.has(c.id) and heard.broken == "struck", "three strikes break the illusion")
	heard.broken = ""
	Game.combat._cast_illusion(c, ContentDB.entry("techniques", "phantom_double"))
	for i in 240:
		Game.tick(0.05)
		if not Game.combat.decoys.has(c.id): break
	GameEvents.flush()
	check(not Game.combat.decoys.has(c.id) and heard.broken == "time", "the illusion fades when its time is up")
	foe2.alive = false
	# Soul Search: an elite searched and slain gives up a memory and an extra drop; a common foe is not marked.
	var common: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(80, 20), lv)
	Game.combat._weapon_after_hit(c, common, {"soul_search_s": 12.0})
	check(not Game.combat.searched.has(str(common.uid)), "Soul Search marks only elites and bosses")
	common.alive = false
	var elite: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(80, -20), lv, {"elite": true})
	Game.combat._weapon_after_hit(c, elite, {"soul_search_s": 12.0})
	check(Game.combat.searched.has(str(elite.uid)) and elite.pools.has_status("soul_searched"), "an elite is marked for Soul Search")
	Game.combat._damage_enemy(elite, elite.pools.hp + 10.0, c.id, "soul", "soul", false, {})
	for i in 4: Game.tick(0.05)
	GameEvents.flush()
	check(heard.search != "" and (heard.search == "?" or Game.account.codex.has(heard.search)), "a searched elite's death gives up a soul memory (%s)" % heard.search)
	# Soul Lantern Ward: a shield of 20% max Soul for 6 s.
	c.pools.shield = 0.0
	if c.pools.max_soul <= 0.0: c.pools.max_soul = 100.0
	Game.combat._resolve_technique(c, ContentDB.entry("techniques", "soul_lantern_ward"))
	check(near(c.pools.shield, c.pools.max_soul * 0.2, 0.5), "Soul Lantern Ward shields 20%% of max Soul (%.1f)" % c.pools.shield)
	for i in 130: Game.tick(0.05)
	check(c.pools.shield == 0.0, "and fades after 6 s")
	# The Poison Body: a poison art known and toxicity past half its tolerance turns hits into poison.
	var tol: float = c.stats.value("toxicity_tolerance")
	c.cultivator.techniques_known.erase("venom_needles")
	c.cultivator.toxicity = tol * 0.8
	check(not Game.combat.poison_body_active(c), "no Poison Body without a poison art")
	c.cultivator.techniques_known.append("venom_needles")
	check(Game.combat.poison_body_active(c), "a poison art and toxicity past half open the Poison Body")
	var pf: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	var tx0: float = c.cultivator.toxicity
	Game.combat._poison_body(c, pf)
	check(pf.pools.has_status("poison") and near(c.cultivator.toxicity, tx0 - 1.0, 0.01), "each hit turns a point of toxicity into poison on the foe")
	Game.combat._poison_body(c, pf)
	check(near(c.cultivator.toxicity, tx0 - 1.0, 0.01), "at most once per foe each half second")
	c.cultivator.toxicity = tol * 0.3
	check(not Game.combat.poison_body_active(c), "below half the tolerance it closes")
	pf.alive = false
	var peddler := ContentDB.entry("shops", "night_peddler")
	var sells := []
	for sitem in peddler.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual": sells.append(str(sitem.learn))
	check("venom_needles" in sells and "miasma_palm" in sells, "the night peddler sells both poison arts")
	GameEvents.event.disconnect(listen)
	c.cultivator.meridians = meridians_before
	c.cultivator.techniques_known = known_before
	c.cultivator.toxicity = tox_before
	c.cooldowns.erase("free_reroll_wk")
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 the Blood path and the Buddhist path (v1.1)
func blood_buddhist_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	Unlocks.force_unlock(c.id, "vows")
	var realm_before: String = c.cultivator.realm_key
	var align_before: int = c.relations.alignment
	var merit_before: int = c.relations.merit
	var hd_before: float = c.cultivator.heart_demon
	var vows_before: Array = c.cultivator.vows.duplicate()
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var slot_before = c.cultivator.technique_slots[0]
	var ts_before: Dictionary = c.training_sect.duplicate(true)
	var daos_had_blood: bool = c.cultivator.daos.has("blood")
	if ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index("heart_tempering_1"): c.cultivator.realm_key = "heart_tempering_1"
	if str(c.training_sect.get("id", "")) == "": c.training_sect = {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	var sect := str(c.training_sect.id)
	var heard := {"path": 0}
	var listen := func(n: String, _p: Dictionary):
		if n == "path_changed": heard.path = int(heard.path) + 1
	GameEvents.event.connect(listen)
	# The Blood path: an opt-in for a demonic heart.
	c.cultivator.paths.erase("blood")
	c.relations.alignment = 0
	var r0 := Game.submit({"type": "set_path", "path": "blood", "on": true})
	check(not r0.get("ok", false) and str(r0.get("reason", "")) == "alignment", "a righteous or neutral heart cannot take the Blood path")
	c.relations.alignment = -30
	var rep0 := int(c.training_sect.get("reputation", {}).get(sect, 0))
	var r1 := Game.submit({"type": "set_path", "path": "blood", "on": true})
	GameEvents.flush()
	check(r1.get("ok", false) and ProgressionAuthority.walks(c, "blood") and int(heard.path) == 1, "at alignment -30 the Blood path is taken (%s)" % str(r1))
	check(c.relations.alignment == -40 and int(c.training_sect.reputation.get(sect, 0)) == rep0 - 20 and c.cultivator.daos.has("blood"),
		"taking it costs 10 alignment and 20 sect regard, and opens the Blood Dao")
	var snap: Dictionary = JSON.parse_string(JSON.stringify(c.cultivator.snapshot()))
	var copy := CultivatorState.new()
	copy.restore(snap)
	check(bool(copy.paths.get("blood", false)), "the path survives a save")
	c.cultivator.heart_demon = 10.0
	Game.progression.apply_heart_demon(c.id, 5.0, "test")
	check(near(c.cultivator.heart_demon, 20.0, 0.01), "on the Blood path the heart demon grows twice as fast")
	# Blood arts: health for power; blood essence pays first; the sect's regard falls with each.
	if not c.cultivator.techniques_known.has("crimson_palm"): c.cultivator.techniques_known.append("crimson_palm")
	c.cultivator.technique_slots[0] = "crimson_palm"
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:crimson_palm")
	Game.combat.blood_essence.erase(c.id)
	var rep1 := int(c.training_sect.reputation.get(sect, 0))
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and near(c.pools.hp, c.pools.max_hp * 0.95, 1.0), "Crimson Palm costs 5%% of health (%s)" % str(u1))
	check(int(c.training_sect.reputation.get(sect, 0)) == rep1 - 1, "and a point of the sect's regard")
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.erase("tech:crimson_palm")
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "normal"})
	check(near(Game.combat.essence_of(c.id), 10.0, 0.01), "a kill gives 10 blood essence")
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(near(c.pools.hp, c.pools.max_hp, 1.0) and near(Game.combat.essence_of(c.id), 5.0, 0.01), "blood essence pays the art's cost first")
	_idle_hands(c)
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": true, "role": "elite"})
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "boss"})
	Game.combat._feed_blood_essence({"victim_kind": "enemy", "killer": c.id, "def": "wild_boarlet", "elite": false, "role": "boss"})
	check(near(Game.combat.essence_of(c.id), 100.0, 0.01), "elites give 25, bosses 50, up to 100")
	Game.combat.blood_essence[c.id].t = Game.sim_time - 30.0
	for i in 20: Game.tick(0.05)
	check(Game.combat.essence_of(c.id) < 99.0, "unfed for 20 s, it drains")
	# Lifesteal: 3% (+1% a Blood Dao tier), twice that for a Blood art.
	c.cultivator.daos["blood"] = {"tier": 0, "insight": 0.0}
	check(near(Game.combat.blood_lifesteal(c), 0.03, 0.0001), "lifesteal is 3% at Blood Dao tier 0")
	c.pools.hp = c.pools.max_hp * 0.5
	var h0: float = c.pools.hp
	Game.combat._lifesteal(c, 1000.0, {"source": "basic"})
	check(near(c.pools.hp - h0, 30.0, 0.5), "a 1000 blow drinks back 30 health")
	h0 = c.pools.hp
	Game.combat._lifesteal(c, 1000.0, {"technique": "crimson_palm"})
	check(near(c.pools.hp - h0, 60.0, 0.5), "a Blood art drinks back twice that")
	# The sect's regard below zero closes the Mission Hall's manuals.
	c.training_sect.reputation[sect] = -5
	var hall := ContentDB.entry("shops", sect)
	var gated := {}
	for sitem in hall.get("stock", []):
		if str(sitem.get("item", "")) == "technique_manual" and str(sitem.get("learn", "")) == "tiger_rush": gated = sitem.get("requires", {})
	check(not gated.is_empty() and not RequirementRules.passes(gated, Game.ctx(c)), "with the sect's regard below zero the Mission Hall lends no manuals")
	c.training_sect.reputation[sect] = 10
	check(RequirementRules.passes(gated, Game.ctx(c)) or ProgressionRules.realm_index(c.cultivator.realm_key) < ProgressionRules.realm_index("qi_kindling_5"), "and at 10 it does again")
	# Leaving the path marks the heart.
	c.cultivator.heart_demon = 0.0
	var off := Game.submit({"type": "set_path", "path": "blood", "on": false})
	GameEvents.flush()
	check(off.get("ok", false) and not ProgressionAuthority.walks(c, "blood") and near(c.cultivator.heart_demon, 10.0, 0.01), "leaving the Blood path adds 10 heart demon")
	_idle_hands(c)
	c.pools.cooldowns.erase("tech:crimson_palm")
	var u3 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(str(u3.get("reason", "")) == "needs_blood_path", "off the path, Blood arts cannot be used")
	# The Buddhist path: merit milestones calm a vow-keeper's heart; healing allies is merit; the Golden Body needs a vow.
	c.cultivator.vows.clear()
	c.cultivator.heart_demon = 30.0
	c.relations.merit = 95
	Game.relations.apply_karma(c.id, 10, 0, "test")
	check(near(c.cultivator.heart_demon, 30.0, 0.01), "without a vow, merit milestones do not calm the heart")
	Game.submit({"type": "set_vow", "vow": "mercy", "on": true})
	c.relations.merit = 195
	Game.relations.apply_karma(c.id, 10, 0, "test")
	check(near(c.cultivator.heart_demon, 20.0, 0.01), "a vow-keeper crossing 200 merit loses 10 heart demon")
	var ally: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(-60, 0), 5)
	ally.team = "ally"
	for k in c.relations.deeds.keys():
		if str(k).begins_with("heal_ally:"): c.relations.deeds.erase(k)
	var m0: int = c.relations.merit
	for i in 7: Game.combat.heal_circle(c, 0.01, 1.0, 220.0, "test")
	check(c.relations.merit == m0 + 5, "healing an ally is merit, five times a day (%d)" % (c.relations.merit - m0))
	ally.alive = false
	Game.combat.ally_hots.clear()
	if not c.cultivator.techniques_known.has("golden_body"): c.cultivator.techniques_known.append("golden_body")
	c.cultivator.technique_slots[0] = "golden_body"
	c.cultivator.vows.clear()
	_idle_hands(c)
	c.pools.composure = 100.0
	c.pools.cooldowns.erase("tech:golden_body")
	var g0 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(str(g0.get("reason", "")) == "needs_vow", "the Golden Body answers only a vow-keeper")
	c.cultivator.vows.append("plain_fare")
	var def0: float = c.stats.value("physical_defense")
	Game.combat._resolve_technique(c, ContentDB.entry("techniques", "golden_body"))
	check(c.stats.value("physical_defense") > def0 * 1.2, "the Golden Body hardens the body (+25%% defence: %.0f -> %.0f)" % [def0, c.stats.value("physical_defense")])
	# Where the arts are found.
	var peddler := ContentDB.entry("shops", "night_peddler")
	var blood_ok := 0
	for sitem in peddler.get("stock", []):
		if str(sitem.get("learn", "")) in ["crimson_palm", "blood_river_slash", "sanguine_lotus"]:
			for cond in sitem.get("requires", {}).get("all", []):
				if str(cond.get("kind", "")) == "alignment_at_most": blood_ok += 1
	check(blood_ok == 3, "the night peddler sells the three Blood arts to the demonic side only")
	var gb := false
	for sitem in ContentDB.entry("shops", "cloud_sect").get("stock", []):
		if str(sitem.get("learn", "")) == "golden_body": gb = true
	check(gb, "the Cloud Mission Hall lends the Golden Body")
	GameEvents.event.disconnect(listen)
	for m in c.stats.modifiers.duplicate():
		if str(m.get("source", "")).begins_with("tech:golden_body"): c.stats.remove_source(str(m.source))
	c.cultivator.paths.erase("blood")
	c.cultivator.realm_key = realm_before
	c.relations.alignment = align_before
	c.relations.merit = merit_before
	c.cultivator.heart_demon = hd_before
	c.cultivator.vows = vows_before
	c.cultivator.techniques_known = known_before
	c.cultivator.technique_slots[0] = slot_before
	c.training_sect = ts_before
	if not daos_had_blood: c.cultivator.daos.erase("blood")
	Game.combat.blood_essence.erase(c.id)
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 sect role variants and the sect tree (v0.9)
func sect_roles_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	var ts_before: Dictionary = c.training_sect.duplicate(true)
	var prof_before: Dictionary = c.professions.duplicate(true)
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var slot_before = c.cultivator.technique_slots[0]
	c.training_sect = {"id": "jade_sect", "rank": "service_disciple", "contribution": 2000, "reputation": {"jade_sect": 10}}
	var heard := {"role": 0, "node": 0}
	var listen := func(n: String, _p: Dictionary):
		if n == "sect_role_chosen": heard.role = int(heard.role) + 1
		if n == "sect_node_bought": heard.node = int(heard.node) + 1
	GameEvents.event.connect(listen)
	var r0 := Game.submit({"type": "set_sect_role", "role": "damage"})
	check(str(r0.get("reason", "")) == "rank", "a service disciple has no sect role yet")
	c.training_sect.rank = "outer_disciple"
	var r1 := Game.submit({"type": "set_sect_role", "role": "damage"})
	GameEvents.flush()
	check(r1.get("ok", false) and str(c.training_sect.role) == "damage" and int(c.training_sect.contribution) == 2000 and int(heard.role) == 1, "the first role is free")
	var v := ProgressionRules.signature_variant(c, "flowing_palm")
	check(near(float(v.get("mult", 0.0)), 0.25, 0.001) and ProgressionRules.signature_variant(c, "tiger_rush").is_empty(), "the damage variant touches only the signature line")
	var r2 := Game.submit({"type": "set_sect_role", "role": "support"})
	check(r2.get("ok", false) and int(c.training_sect.contribution) == 1950, "changing it costs 50 contribution")
	# The support variant heals on use, and grows with the crafts ranked up.
	c.professions = {}
	var m0: float = Game.combat.sect_support_mult(c)
	c.professions = {"healing": {"rank": "adept", "xp": 0.0}}
	check(near(m0, 1.0, 0.001) and Game.combat.sect_support_mult(c) > m0, "support healing grows with the crafts (%.2f)" % Game.combat.sect_support_mult(c))
	c.professions = {}
	if not c.cultivator.techniques_known.has("flowing_palm"): c.cultivator.techniques_known.append("flowing_palm")
	c.cultivator.technique_slots[0] = "flowing_palm"
	_idle_hands(c)
	c.pools.hp = c.pools.max_hp * 0.5
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:flowing_palm")
	var h0: float = c.pools.hp
	var u1 := Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(u1.get("ok", false) and c.pools.hp >= h0 + c.pools.max_hp * 0.039, "Mending Current heals the user by 4%% (%s)" % str(u1))
	_idle_hands(c)
	# The tree: bought in order with contribution; later nodes need a higher rank.
	var atk0: float = c.stats.value("physical_attack")
	var b1 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	GameEvents.flush()
	check(b1.get("ok", false) and int(c.training_sect.contribution) == 1890 and c.stats.value("physical_attack") > atk0 * 1.025 and int(heard.node) == 1,
		"the first Edge node costs 60 and adds 3%% attack (%.0f -> %.0f)" % [atk0, c.stats.value("physical_attack")])
	Game.submit({"type": "buy_sect_node", "branch": "edge"})
	var b3 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	check(str(b3.get("reason", "")) == "rank", "the third node waits for Inner Disciple")
	c.training_sect.rank = "core_disciple"
	for i in 3: Game.submit({"type": "buy_sect_node", "branch": "edge"})
	var b6 := Game.submit({"type": "buy_sect_node", "branch": "edge"})
	check(int(c.training_sect.tree.edge) == 5 and str(b6.get("reason", "")) == "complete", "a branch has five nodes")
	check(near(ProgressionRules.sect_tree_flag(c, "signature_cooldown"), -1.0, 0.001) and near(ProgressionRules.sect_tree_flag(c, "signature_mult"), 0.15, 0.001),
		"the Edge branch's flags add up")
	c.pools.cooldowns.erase("tech:flowing_palm")
	c.pools.qi = c.pools.max_qi
	Game.submit({"type": "use_technique", "slot": 0, "facing": 1})
	check(near(c.pools.cooldown("tech:flowing_palm"), float(ContentDB.entry("techniques", "flowing_palm").cooldown_s) - 1.0, 0.05), "signature arts are ready a second sooner")
	_idle_hands(c)
	c.training_sect.contribution = 0
	var b7 := Game.submit({"type": "buy_sect_node", "branch": "root"})
	check(str(b7.get("reason", "")) == "contribution", "no contribution, no node")
	# The Cloud support variant is a shield.
	c.training_sect = {"id": "cloud_sect", "rank": "outer_disciple", "contribution": 100, "reputation": {"cloud_sect": 10}, "role": "support"}
	c.pools.shield = 0.0
	Game.combat._sect_support(c, ProgressionRules.signature_variant(c, "jade_thrust"))
	check(near(c.pools.shield, c.pools.max_hp * 0.08, 1.0), "Guarding Cloud shields 8% of health")
	GameEvents.event.disconnect(listen)
	c.pools.shield = 0.0
	c.training_sect = ts_before
	c.professions = prof_before
	c.cultivator.techniques_known = known_before
	c.cultivator.technique_slots[0] = slot_before
	Game.combat.refresh_stats(c.id)


# ------------------------------------------------------------------ S47/S48 v1.1: the sword swarm, Array Plates in a fight, the combat puppet
func swarm_array_puppet_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var st: ActorState = Game.actor_state(c.id)
	Game.world.apply_teleport(c.id, "wp_west")
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal", "confusion", "fear"]: Game.combat.cure_status(c.id, sid)
	var daos_before: Dictionary = c.cultivator.daos.duplicate(true)
	var known_before: Array = c.cultivator.techniques_known.duplicate()
	var meridians_before: Dictionary = c.cultivator.meridians.duplicate()
	var treasures_before: Array = c.inventory.treasures.duplicate()
	var lv := ProgressionRules.level(c) + 12
	var heard := {"released": 0, "returned": "", "deployed": 0, "faded": 0}
	var listen := func(n: String, p: Dictionary):
		if n == "sword_released" and int(p.get("swarm", 0)) > 0: heard.released = int(p.swarm)
		if n == "sword_returned" and p.get("swarm", false): heard.returned = str(p.get("reason", ""))
		if n == "array_deployed": heard.deployed = int(heard.deployed) + 1
		if n == "array_faded": heard.faded = int(heard.faded) + 1
	GameEvents.event.connect(listen)
	# The swarm: 3 swords at Sword Dao 5, 9 with the Nine Swords Array, 36 with it at tier 6; one sword per 10 Spirit.
	c.cultivator.meridians["spirit"] = 100
	Game.combat.refresh_stats(c.id)
	var cap := int(floor(c.stats.value("spirit") / 10.0))
	c.cultivator.daos["sword"] = {"tier": 4, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == 0, "no swarm below Sword Dao 5")
	c.cultivator.daos["sword"] = {"tier": 5, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == mini(3, cap), "Sword Dao 5: three swords (%d)" % Game.combat.swarm_count(c, false))
	check(Game.combat.swarm_count(c, true) == mini(9, cap), "released from the Nine Swords Array: nine (%d)" % Game.combat.swarm_count(c, true))
	c.inventory.treasures[0] = "nine_sword_array"
	check(Game.combat.swarm_count(c, false) == mini(9, cap), "the Array set in a Treasure slot lifts the Dao swarm to nine")
	c.cultivator.daos["sword"] = {"tier": 6, "insight": 0.0}
	check(Game.combat.swarm_count(c, false) == mini(36, cap) and cap < 36, "Original Application: 36, held to what Spirit can steer (%d of %d)" % [Game.combat.swarm_count(c, false), cap])
	c.inventory.treasures = treasures_before.duplicate()
	c.cultivator.meridians["spirit"] = 0
	Game.combat.refresh_stats(c.id)
	var low := maxi(1, int(floor(c.stats.value("spirit") / 10.0)))
	check(low < cap and Game.combat.swarm_count(c, true) == mini(36, low), "less Spirit steers fewer swords (%d)" % Game.combat.swarm_count(c, true))
	c.cultivator.meridians["spirit"] = 100
	Game.combat.refresh_stats(c.id)
	# Sword Dao tier 5 teaches the Sword Swarm.
	c.cultivator.techniques_known.erase("sword_swarm")
	c.cultivator.daos["sword"] = {"tier": 0, "insight": 0.0}
	var need := 0.0
	for t in 400:
		if ProgressionRules.dao_tier_for(need) >= 5: break
		need += 50.0
	Game.progression.apply_insight(c.id, "sword", need + 1.0, "teacher:test")
	check(c.cultivator.techniques_known.has("sword_swarm"), "Sword Dao tier 5 teaches the Sword Swarm (tier %d)" % int(c.cultivator.daos.sword.tier))
	# The technique toggles the swarm, pays QI, and the swords strike a foe nearby on their own.
	c.cultivator.daos["sword"] = {"tier": 5, "insight": 0.0}
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(160, 0), lv)
	foe.pools.max_hp = 999999.0
	foe.pools.hp = 999999.0
	foe.stats["evasion"] = 0.0
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.erase("tech:sword_swarm")
	var qi0: float = c.pools.qi
	var sw := Game.combat.toggle_sword_swarm(c, ContentDB.entry("techniques", "sword_swarm"))
	GameEvents.flush()
	check(sw.get("ok", false) and Game.combat.swarm_of(c.id) == mini(3, cap) and heard.released == Game.combat.swarm_of(c.id) and c.pools.qi < qi0,
		"the Sword Swarm rises for QI (%s)" % str(sw))
	for i in 50:
		Game.tick(0.05)
		foe.plane = st.plane + Vector2(160, 0)
	check(foe.pools.hp < 999999.0, "the swarm strikes a foe nearby without a button (%.0f lost)" % (999999.0 - foe.pools.hp))
	var off := Game.combat.toggle_sword_swarm(c, ContentDB.entry("techniques", "sword_swarm"))
	GameEvents.flush()
	check(off.get("ok", false) and Game.combat.swarm_of(c.id) == 0 and heard.returned == "recalled", "pressed again, the swords come home")
	Game.combat.start_swarm(c, true, 0.5)
	for i in 14: Game.tick(0.05)
	GameEvents.flush()
	check(Game.combat.swarm_of(c.id) == 0 and heard.returned == "time", "the swarm returns when its time is up")
	Game.inventory.apply_add(c.id, "nine_sword_array", 1, "test")
	Unlocks.force_unlock(c.id, "treasures")
	c.inventory.treasures[0] = "nine_sword_array"
	c.pools.qi = c.pools.max_qi
	c.pools.cooldowns.clear()
	var tr := Game.submit({"type": "use_treasure", "slot": 0})
	check(tr.get("ok", false) and Game.combat.swarm_of(c.id) == mini(9, cap), "the Nine Swords Array, released, orbits nine swords (%s)" % str(tr))
	Game.combat._end_swarm(c, "recalled")
	c.inventory.treasures = treasures_before.duplicate()
	Game.inventory.apply_remove(c.id, "nine_sword_array", 1, "test")
	c.cultivator.daos["sword"] = daos_before.get("sword", {"tier": 0, "insight": 0.0})
	# Array Plates: each lays an array at your feet; the Formation Dao lengthens them and sharpens the killing array.
	c.cultivator.daos["formation"] = {"tier": 0, "insight": 0.0}
	Game.combat.arrays.clear()
	var def0: float = c.stats.value("physical_defense")
	Game.inventory.apply_add(c.id, "array_plate", 1, "test")
	var ins0 := float(c.cultivator.daos.formation.get("insight", 0.0))
	var u := Game.submit({"type": "use_item", "index": c.inventory.first_index("array_plate")})
	GameEvents.flush()
	check(u.get("ok", false) and Game.combat.arrays.size() == 1 and str(Game.combat.arrays[0].kind) == "guard" and near(float(Game.combat.arrays[0].t), 12.0, 0.01)
		and int(heard.deployed) == 1, "an Array Plate lays a guarding array for 12 s (%s)" % str(u))
	check(float(c.cultivator.daos.formation.get("insight", 0.0)) > ins0, "each plate teaches the Formation Dao a little")
	for i in 3: Game.tick(0.05)
	check(c.stats.value("physical_defense") > def0 * 1.1, "inside its ring, Physical Defense rises (%.0f -> %.0f)" % [def0, c.stats.value("physical_defense")])
	Game.combat.arrays[0].t = 0.05
	for i in 3: Game.tick(0.05)
	GameEvents.flush()
	check(Game.combat.arrays.is_empty() and int(heard.faded) == 1, "the array fades when its time is up")
	var k: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), lv)
	k.pools.max_hp = 999999.0
	k.pools.hp = 999999.0
	k.stats["evasion"] = 0.0
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	var m0 := float(Game.combat.arrays[-1].mult)
	for i in 25:
		Game.tick(0.05)
		k.plane = st.plane + Vector2(60, 0)
	check(k.pools.hp < 999999.0, "a killing array wounds every foe inside it (%.0f lost)" % (999999.0 - k.pools.hp))
	Game.combat.deploy_array(c.id, {"array": "binding", "radius": 160, "duration": 10, "slow": 0.4})
	for i in 12:
		Game.tick(0.05)
		k.plane = st.plane + Vector2(60, 0)
	check(k.pools.has_status("slow"), "a binding array slows every foe inside it")
	k.alive = false
	Game.combat.arrays.clear()
	c.cultivator.daos["formation"] = {"tier": 2, "insight": 0.0}
	Game.combat.deploy_array(c.id, {"array": "killing", "radius": 160, "duration": 10, "mult": 0.5})
	check(near(float(Game.combat.arrays[-1].mult), m0 * 1.4, 0.001) and near(float(Game.combat.arrays[-1].t), 11.0, 0.01),
		"Formation Dao 2: the killing array hits 40% harder and holds a tenth longer")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	GameEvents.flush()
	check(Game.combat.arrays.is_empty(), "arrays stay in the room they were laid in")
	c.cultivator.daos["formation"] = daos_before.get("formation", {"tier": 0, "insight": 0.0})
	# The combat puppet: built at the tinkerer's bench, takes a pet slot, one only; a construct that is repaired, not healed.
	var pets_before: Array = c.pets.duplicate(true)
	var active_before: String = c.active_pet
	var party_before: Array = c.party_pets.duplicate()
	c.pets = c.pets.filter(func(p): return str(p.species) != "combat_puppet")
	Unlocks.force_unlock(c.id, "puppetry")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	for it in [["spirit_wood", 8], ["puppet_core", 2], ["jadeiron", 4]]: Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "test")
	var wood0: int = c.inventory.count("spirit_wood")
	var b := Game.submit({"type": "build_puppet", "blueprint": "combat_puppet"})
	var pup := {}
	for p in c.pets:
		if str(p.species) == "combat_puppet": pup = p
	check(b.get("ok", false) and not pup.is_empty() and PetAuthority.is_construct(pup) and str(pup.stage) == "adult" and (pup.traits as Array).is_empty()
		and c.inventory.count("spirit_wood") == wood0 - 8, "the tinkerer builds a combat puppet into a pet slot (%s)" % str(b))
	for it in [["spirit_wood", 8], ["puppet_core", 2], ["jadeiron", 4]]: Game.inventory.apply_add(c.id, str(it[0]), int(it[1]), "test")
	check(str(Game.submit({"type": "build_puppet", "blueprint": "combat_puppet"}).get("reason", "")) == "one_puppet", "only one combat puppet")
	Game.inventory.apply_add(c.id, "roast_fish", 1, "test")
	check(str(Game.submit({"type": "feed_pet", "pet": str(pup.uid), "item": "roast_fish"}).get("reason", "")) == "construct", "a puppet does not eat")
	check(str(Game.submit({"type": "set_pet_role", "pet": str(pup.uid), "role": "gatherer"}).get("reason", "")) == "construct", "a puppet only fights")
	check(Game.pets.breed_partners(c, pup).is_empty() and not Game.pets.can_evolve(c, pup), "a puppet neither breeds nor grows")
	pup.wounded = true
	Game.pets.heal_wound(c.id)
	check(pup.wounded, "a Beast Revival Pill or rest does not mend a puppet")
	for it in [["spirit_wood", c.inventory.count("spirit_wood")]]: Game.inventory.apply_remove(c.id, str(it[0]), int(it[1]), "test")
	check(str(Game.submit({"type": "repair_puppet"}).get("reason", "")) == "materials", "a repair needs spirit wood")
	Game.inventory.apply_add(c.id, "spirit_wood", 2, "test")
	var rp := Game.submit({"type": "repair_puppet"})
	check(rp.get("ok", false) and not pup.wounded and c.inventory.count("spirit_wood") == 0, "the tinkerer repairs it for two spirit wood (%s)" % str(rp))
	check(str(Game.submit({"type": "repair_puppet"}).get("reason", "")) == "whole", "a whole puppet needs no repair")
	for it in ["puppet_core", "jadeiron", "roast_fish"]: Game.inventory.apply_remove(c.id, it, c.inventory.count(it), "test")
	c.pets = pets_before
	c.active_pet = active_before
	c.party_pets = party_before
	Game.world.apply_teleport(c.id, "wp_west")
	GameEvents.event.disconnect(listen)
	c.cultivator.daos = daos_before
	c.cultivator.techniques_known = known_before
	c.cultivator.meridians = meridians_before
	c.inventory.treasures = treasures_before
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S47 natal treasure, wardrobe, blood-drop, rogue cultivators
func natal_wardrobe_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "natal")
	Unlocks.force_unlock(c.id, "wardrobe")
	Game.inventory.apply_add_equipment(c.id, "jadeiron_jian", 27, "common", "test")
	var ji: int = c.inventory.first_index("jadeiron_jian")
	var held_before = c.inventory.equipped.get("weapon")
	var jian: Dictionary = c.inventory.bag[ji]
	c.inventory.equipped["weapon"] = jian
	c.inventory.bag[ji] = held_before
	# Natal: flag it, feed it ore (20 XP a grade step each): 5 Jadeiron -> 300 XP -> natal level 2, +4% stats.
	var mult0: float = StatRules.instance_mult(jian, c.cultivator.energy_type)
	check(Game.submit({"type": "flag_natal", "uid": int(jian.uid)}).get("ok", false) and jian.get("natal", false), "a jian becomes the Natal treasure")
	Game.inventory.apply_add(c.id, "jadeiron", 5, "test")
	var fd := Game.submit({"type": "feed_natal", "uid": int(jian.uid), "item": "jadeiron", "count": 5})
	check(fd.get("ok", false) and int(jian.natal_level) == 2 and near(float(jian.natal_xp), 300.0), "five Jadeiron feed it to natal level 2 (%s)" % str(fd))
	check(near(StatRules.instance_mult(jian, c.cultivator.energy_type), mult0 * 1.04, 0.001), "natal level 2 gives +4%")
	var cap: int = Game.inventory.natal_cap(jian)
	check(cap > int(jian.ilv) and int(jian.get("ilv_eff", jian.ilv)) == clampi(ProgressionRules.level(c), int(jian.ilv), cap),
		"its item level follows yours, up to the grade band above its own (cap %d)" % cap)
	# It breaks only to the listed causes: an ordinary blow leaves it whole, a boss's shatter breaks it.
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", Game.actor_state(c.id).plane + Vector2(40, 0), 2)
	c.pools.invulnerable = 0.0
	c.pools.statuses = c.pools.statuses.filter(func(x): return str(x.id) != "spawn_protection")
	Game.combat.timeline(c.id).dodge_t = 0.0
	Game.combat._enemy_hits_player(foe, c, Game.combat.enemy_view(foe), Game.combat.player_view(c), {"mult": 0.01})
	check(not jian.get("broken", false), "an ordinary blow never breaks a natal weapon")
	c.pools.invulnerable = 0.0
	Game.combat._enemy_hits_player(foe, c, Game.combat.enemy_view(foe), Game.combat.player_view(c), {"mult": 0.01, "shatter": true})
	GameEvents.flush()
	check(jian.get("broken", false) and StatRules.instance_mult(jian, c.cultivator.energy_type) == 0.0 and not c.cultivator.injuries.is_empty(),
		"a shatter blow breaks it: its stats go dark and an injury follows")
	Game.inventory.apply_add(c.id, "jadeiron", 20, "test")
	Game.economy.apply_currency("silver_tael", 5000, "test")
	check(Game.submit({"type": "reforge_natal", "uid": int(jian.uid)}).get("ok", false) and not jian.get("broken", false) and int(jian.natal_level) == 2,
		"a re-forge mends it and keeps its growth")
	check(Game.combat.natal_demand(jian) == 20.0, "control demand is 10 + 5 a natal level")
	# Wardrobe and blood-drop: the first wear adds the look and bleeds a Plain-to-Heaven piece once.
	Game.inventory.apply_add_equipment(c.id, "jadeiron_robe", 27, "common", "test")
	var robe: Dictionary = c.inventory.bag[c.inventory.first_index("jadeiron_robe")]
	var bled := []
	var listen := func(n: String, p: Dictionary):
		if n == "item_blooded": bled.append(p)
	GameEvents.event.connect(listen)
	Game.inventory._first_wear(c, robe, "robe")
	Game.inventory._first_wear(c, robe, "robe")
	GameEvents.flush()
	GameEvents.event.disconnect(listen)
	var look := str(robe.get("appearance", ContentDB.item("jadeiron_robe").get("appearance", "")))
	check(bled.size() == 1 and robe.get("blooded", false), "a first wear takes one drop of blood")
	check(Game.account.wardrobe_unlocked.has("shirt:" + look), "the look joins the wardrobe (%s)" % look)
	check(not Game.submit({"type": "set_appearance", "slot": "robe", "look": "never_worn_look"}).get("ok", true), "a look never worn cannot be chosen")
	check(Game.submit({"type": "set_appearance", "slot": "robe", "look": look}).get("ok", false) and str(c.inventory.appearance_override.robe) == look,
		"a worn look can stand in for the robe's own")
	Game.submit({"type": "set_appearance", "slot": "robe", "look": ""})
	# Rogue cultivators drop what they carry, and a sealed pouch that Appraisal opens.
	var drop: Dictionary = LootRules.roll("rogue_cultivator", Rng.stream(c.id, "loot"), 25, 0.0, 0.0)
	var got := (drop.get("items", []) as Array).map(func(x): return str(x.item))
	check(got.has("serpent_tongue_jian") and got.has("sealed_storage_pouch"), "a rogue cultivator always drops its jian and a sealed pouch (%s)" % str(got))
	Unlocks.force_unlock(c.id, "appraisal")
	Game.progression.apply_learn_secret_art(c.id, "appraisal_eye")
	Game.inventory.apply_add(c.id, "sealed_storage_pouch", 1, "test")
	var ap := Game.workshop.appraise(c, c.inventory.first_index("sealed_storage_pouch"))
	var table: Array = ContentDB.item("sealed_storage_pouch").get("appraise", [])
	check(ap.get("ok", false) and table.any(func(x): return str(x.item) == str(ap.item)), "Appraisal opens the pouch into something from its own table (%s)" % str(ap))
	# Put things back.
	for k in ["natal", "natal_xp", "natal_level", "ilv_eff"]: jian.erase(k)
	c.inventory.equipped["weapon"] = held_before
	if foe != null: foe.alive = false
	for id in ["jadeiron_jian", "jadeiron_robe"]:
		var k2: int = c.inventory.first_index(id)
		if k2 >= 0: Game.inventory.apply_remove_index(c.id, k2, 1, "test")
	c.cultivator.injuries.clear()

# ------------------------------------------------------------------ S47 talisman craft and Shattered Relics
func talisman_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "talisman")
	var learn: Array = []
	for r in ["flame_talisman", "iron_wall_talisman", "wind_step_talisman", "binding_talisman", "beast_blood_ink"]:
		learn.append({"kind": "learn_recipe", "recipe": r})
	Game.apply_effects(c.id, learn, "test")
	for need in [["talisman_paper", 12], ["cinnabar", 12], ["ember_pepper", 8], ["beetle_shell", 4], ["vulture_plume", 2], ["hound_fang", 2], ["rat_tail", 2]]:
		Game.inventory.apply_add(c.id, str(need[0]), int(need[1]), "test")
	# A broken stroke spoils the paper and nothing else.
	var paper0: int = c.inventory.count("talisman_paper")
	var cin0: int = c.inventory.count("cinnabar")
	var br := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 0.9, "broken": true})
	check(str(br.get("reason", "")) == "spoiled" and c.inventory.count("talisman_paper") == paper0 - 1 and c.inventory.count("cinnabar") == cin0
		and c.inventory.count("flame_talisman") == 0, "a broken stroke spoils one sheet of paper and makes nothing")
	# Tracing score to quality: a clean, unhurried stroke writes a better talisman than a shaky one.
	var order: Array = ContentDB.config("grades").get("quality_order", ["flawed", "common", "fine", "superior", "perfect"])
	var good := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 1.0})
	var poor := Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 0.1})
	check(good.get("ok", false) and poor.get("ok", false) and order.find(str(good.quality)) > order.find(str(poor.quality)),
		"a clean stroke writes a better talisman (%s) than a shaky one (%s)" % [str(good.get("quality", "")), str(poor.get("quality", ""))])
	check(Game.submit({"type": "trace_talisman", "recipe": "beast_blood_ink"}).get("ok", false) and c.inventory.count("beast_blood_ink") >= 1, "inks are made without tracing")
	# An attack talisman strikes at its own grade and quality, never the user's stats.
	var st: ActorState = Game.actor_state(c.id)
	for sid in ["stun", "slow", "shock", "spawn_protection", "qi_seal"]: Game.combat.cure_status(c.id, sid)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 2)
	foe.pools.max_hp = 99999.0
	foe.pools.hp = 99999.0
	var used_q := [""]
	var dealt := func() -> float:
		var hp0: float = foe.pools.hp
		for k in 8:
			var old: int = c.inventory.first_index("flame_talisman")
			if old < 0: break
			Game.inventory.apply_remove_index(c.id, old, int(c.inventory.bag[old].get("count", 1)), "test")
		Game.submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 1.0})
		var idx: int = c.inventory.first_index("flame_talisman")
		if idx >= 0: used_q[0] = str(c.inventory.bag[idx].get("quality", "common"))
		Game.submit({"type": "use_item", "index": idx})
		return hp0 - foe.pools.hp
	var d1: float = dealt.call()
	var q1: String = str(used_q[0])
	Game.combat.apply_buff(c.id, {"stat": "qi_attack", "op": "pct_add", "value": 2.0, "duration": 30.0, "source": "test"}, "test")
	var d2: float = dealt.call()
	var qm := float(ContentDB.config("talismans").get("quality_mult", {}).get(q1, 1.0))
	var qm2 := float(ContentDB.config("talismans").get("quality_mult", {}).get(str(used_q[0]), 1.0))
	check(d1 > 0.0 and near(d1 / qm, d2 / qm2, 0.001) and near(d1, 90.0 * 1.8 * qm, 0.01), "a Flame Talisman deals 180%% at its own grade, whatever your Qi attack (%.0f, %.0f)" % [d1, d2])
	# Iron Wall shields 20% of max HP; Wind Step holds one free dodge; Binding roots a foe but not a boss.
	Game.submit({"type": "trace_talisman", "recipe": "iron_wall_talisman", "score": 0.6})
	c.pools.shield = 0.0
	Game.submit({"type": "use_item", "index": c.inventory.first_index("iron_wall_talisman")})
	check(c.pools.shield > c.pools.max_hp * 0.15, "Iron Wall shields about a fifth of your max HP (%.0f)" % c.pools.shield)
	Game.submit({"type": "trace_talisman", "recipe": "wind_step_talisman", "score": 0.6})
	Game.submit({"type": "use_item", "index": c.inventory.first_index("wind_step_talisman")})
	Unlocks.force_unlock(c.id, "dodge_dash")
	c.pools.cooldowns["dodge"] = 5.0
	var dg := Game.submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1})
	check(dg.get("ok", false) and not Game.combat.treasure_fx.get(c.id, {}).has("free_dodge"), "Wind Step spends its charge on a dodge the cooldown would refuse")
	Game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": "binding_talisman"}], "test")
	Game.inventory.apply_add(c.id, "binding_talisman", 1, "test")
	var bi := Game.submit({"type": "use_item", "index": c.inventory.first_index("binding_talisman")})
	check(bi.get("ok", false) and foe.pools.has_status("root"), "a Binding Talisman roots the nearest foe")
	# A Shattered Relic needs an Expert smith at a forge.
	Game.inventory.apply_add(c.id, "shattered_moon_blade", 1, "test")
	var rr := Game.submit({"type": "restore_relic", "index": c.inventory.first_index("shattered_moon_blade")})
	check(not rr.get("ok", true) and str(rr.get("reason", "")) in ["no_station", "rank"], "a Shattered Relic waits for an Expert smith at a forge (%s)" % str(rr.get("reason", "")))
	check(ContentDB.item("moonlit_blade").get("relic", false) and str(ContentDB.item("shattered_moon_blade").get("restores", "")) == "moonlit_blade",
		"the Moon Blade's shards restore into a relic")
	# Tidy up.
	if foe != null: foe.alive = false
	c.pools.shield = 0.0
	for id in ["flame_talisman", "iron_wall_talisman", "wind_step_talisman", "binding_talisman", "shattered_moon_blade", "beast_blood_ink"]:
		for k in 8:
			var at: int = c.inventory.first_index(id)
			if at < 0: break
			Game.inventory.apply_remove_index(c.id, at, int(c.inventory.bag[at].get("count", 1)), "test")

# ------------------------------------------------------------------ S44 herb natures, roles, conflicts and the furnace blast
func herb_nature_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	check(str(ContentDB.item("riverreed_ginseng_10").get("nature", "")) == "hot" and str(ContentDB.item("mist_lotus").get("nature", "")) == "cold"
		and str(ContentDB.item("willow_moss").get("nature", "")) == "neutral" and str(ContentDB.item("cloudtop_orchid").get("nature", "")) == "cold",
		"herbs carry Part 8's natures")
	check(near(Game.crafting.nature_shift("healing_pill"), 0.08) and near(Game.crafting.nature_shift("clear_mind_pill"), -0.08),
		"a hot Principal moves the Extraction band up 8%%; a cold one down")
	check(Game.crafting.role_of("healing_pill", "riverreed_ginseng_10") == "principal" and Game.crafting.role_of("healing_pill", "willow_moss") == "minister",
		"recipe order gives the roles: Principal, then Minister")
	# The substitute: Alchemy Dao tier 5, the same nature, and a role the herb can fill.
	var daos: Dictionary = c.cultivator.daos
	var had: Dictionary = daos.get("alchemy", {}).duplicate()
	daos["alchemy"] = {"tier": 4, "insight": 0.0}
	check(Game.crafting.substitute_check(c, "cleansing_pill", "riverreed_ginseng_100", "ember_pepper") != "", "below tier 5 no herb stands in for another")
	daos["alchemy"] = {"tier": 5, "insight": 0.0}
	check(Game.crafting.substitute_check(c, "cleansing_pill", "riverreed_ginseng_100", "ember_pepper") == "", "tier 5: hot Ember Pepper may stand in for hot ginseng as Assistant")
	check(Game.crafting.substitute_check(c, "cleansing_pill", "mist_lotus", "ember_pepper") != "", "a hot herb never stands in for a cold one")
	check(Game.crafting.substitute_check(c, "healing_pill", "riverreed_ginseng_10", "ember_pepper") != "", "Ember Pepper cannot be a Principal")
	# Every listed conflict blows the furnace: minor body injury, -10 durability, and the batch is lost.
	Unlocks.force_unlock(c.id, "alchemy")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	Game.actor_state(c.id).plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	c.inventory.bag.fill(null)
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "jadeiron_furnace", 1, "test")
	c.cultivator.injuries.clear()
	Game.apply_effects(c.id, [{"kind": "learn_recipe", "recipe": "cleansing_pill"}], "test")
	for inp in ContentDB.entry("recipes", "cleansing_pill").inputs: Game.inventory.apply_add(c.id, str(inp.item), int(inp.count), "test")
	Game.inventory.apply_add(c.id, "ember_pepper", 1, "test")
	var bl := Game.crafting.craft(c, "cleansing_pill", 1, [1.0, 1.0, 1.0], "alchemy", "charcoal", {"from": "riverreed_ginseng_100", "to": "ember_pepper"})
	GameEvents.flush()
	check(str(bl.get("reason", "")) == "blast" and int(c.inventory.furnace.durability) == 90 and c.inventory.count("cleansing_pill") == 0
		and c.inventory.count("mist_lotus") == 0 and c.inventory.count("ember_pepper") == 0,
		"Ember Pepper meets Mist Lotus: the furnace blows, loses 10 durability, and the batch is gone")
	check(int(c.cultivator.injuries.get("body", {}).get("severity", 0)) >= 1, "the blast leaves a minor body injury")
	check((c.crafting.get("known_conflicts", []) as Array).has("ember_pepper+mist_lotus"), "the pair is remembered, so the page can warn next time")
	for row in ContentDB.all("herb_conflicts"):
		var pair: Array = row.herbs
		check(not Game.crafting.conflict_in([{"item": pair[0]}, {"item": pair[1]}]).is_empty(), "conflict %s blows the furnace" % row.id)
	# Tidy up.
	c.cultivator.injuries.clear()
	if had.is_empty(): daos.erase("alchemy")
	else: daos["alchemy"] = had
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S44 new forms: Qi Flow, oils, the poison pill, the draught, baths
func new_forms_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	c.inventory.bag.fill(null)
	# The Qi Flow Pill: +20% accumulation for an hour; the toxicity comes due when it wears off.
	Game.inventory.apply_add(c.id, "qi_flow_pill", 1, "test")
	for k in ["item:buff", "item:utility", "item:healing"]: c.pools.cooldowns.erase(k)
	var acc0: float = c.stats.value("accumulation_rate")
	Game.apply_effects(c.id, ContentDB.item("qi_flow_pill").use, "item:qi_flow_pill")   # the effect itself (the test body is too young for an Earth pill)
	GameEvents.flush()
	check(c.stats.value("accumulation_rate") > acc0 + 0.15, "the Qi Flow Pill lifts accumulation (%.2f -> %.2f)" % [acc0, c.stats.value("accumulation_rate")])
	var tox0: float = cu.toxicity
	for m in c.stats.modifiers:
		if str(m.get("source", "")) == "qi_flow_pill": m.remaining = 0.01
	Game.combat.tick(0.05)
	GameEvents.flush()
	check(cu.toxicity >= tox0 + 14.0, "when the hour is up, +15 toxicity comes due (%.1f -> %.1f)" % [tox0, cu.toxicity])
	# Weapon oils: one at a time; each hit may carry the oil's status.
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var st: ActorState = Game.actor_state(c.id)
	var foe: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 2)
	foe.pools.max_hp = 99999.0
	foe.pools.hp = 99999.0
	Game.inventory.apply_add(c.id, "viper_oil", 1, "test")
	Game.inventory.apply_add(c.id, "ember_oil", 1, "test")
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "viper_oil"), true)
	check(c.pools.has_status("viper_oil"), "Viper Oil is on the blade")
	var poisoned := 0
	for i in 60:
		foe.pools.statuses.clear()
		Game.combat._oil_strike(c, foe, Game.combat.enemy_view(foe))
		if foe.pools.has_status("poison"): poisoned += 1
	check(poisoned > 3 and poisoned < 25, "Viper Oil poisons about one hit in five (%d of 60)" % poisoned)
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "ember_oil"), true)
	check(c.pools.has_status("ember_oil") and not c.pools.has_status("viper_oil"), "a second oil wipes off the first")
	Game.combat.cure_status(c.id, "ember_oil")
	# The Viper Smoke Pill leaves a poison cloud: 4% of max HP a second for 5 s.
	foe.pools.statuses.clear()
	Game.combat._burst(c, {"x": foe.plane.x, "y": foe.plane.y, "alt": 0.0, "burst": 90.0, "attack": {"damage_type": "physical", "mult": [0.2, 0.2], "range": [1.0, 1.0]},
		"cloud": ContentDB.item("viper_smoke_pill").use[0].cloud}, null)
	var cloud_ok := false
	for s2 in foe.pools.statuses:
		if str(s2.id) == "poison" and near(float(s2.power), 0.04) and near(float(s2.remaining), 5.0): cloud_ok = true
	check(cloud_ok, "the smoke cloud poisons for 4%% of max HP a second, 5 s")
	foe.alive = false
	# The Riverreed Draught: two strikes, straight to the Draught slot, flat after ten minutes.
	check(Game.crafting.steps_for("riverreed_draught") == 2 and Game.crafting.steps_for("healing_pill") == 3, "a liquid takes two strikes (no Condensation)")
	Unlocks.force_unlock(c.id, "alchemy")
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	st.plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 2, "test")
	Game.inventory.apply_add(c.id, "river_minnow", 2, "test")
	c.inventory.draught = null
	var dr := Game.crafting.craft(c, "riverreed_draught", 1, [1.0, 1.0], "alchemy")
	check(dr.get("ok", false) and c.inventory.draught != null and int(c.inventory.draught.count) >= 1 and c.inventory.count("riverreed_draught") == 0,
		"the draught goes to the Draught slot, not the bag")
	c.pools.hp = c.pools.max_hp * 0.4
	c.pools.cooldowns.erase("item:healing")
	var dk := Game.submit({"type": "drink_draught"})
	for k in 40: Game.tick(0.1)
	check(dk.get("ok", false) and c.pools.hp > c.pools.max_hp * 0.6, "drinking it restores 30% HP")
	Game.inventory.apply_draught(c.id, "riverreed_draught", 1, "test")
	c.inventory.draught.made_utc = Clock.now_utc() - 601.0
	Game.inventory.tick(0.1)
	check(c.inventory.draught == null, "ten minutes after it is made, the draught goes flat")
	# Baths: the seclusion slot at a Bath station; a bath beyond the body injures it.
	Unlocks.force_unlock(c.id, "medicinal_bath")
	Unlocks.force_unlock(c.id, "seclusion")
	Game.world.apply_teleport(c.id, "ja_retreat")
	var bo: Dictionary = Game.room_rt.object_def("bath_ja_retreat")
	check(not bo.is_empty(), "the retreat rooms have a Bath station")
	if not bo.is_empty():
		st.plane = Vector2(float(bo.at[0]) - 40.0, float(bo.at[1]))
		c.cultivator.injuries.clear()
		cu.body_level = 5
		Game.inventory.apply_add(c.id, "copper_body_bath", 1, "test")
		cu.residue = 30.0
		var xp0: float = cu.body_xp
		var lv0: int = cu.body_level
		var sb := Game.submit({"type": "start_bath", "item": "copper_body_bath"})
		check(sb.get("ok", false) and str(c.seclusion.get("focus", "")) == "bath" and c.inventory.count("copper_body_bath") == 0, "the Copper Body Bath takes the seclusion slot")
		var cl := Game.progression.claim_offline(c, 3600.0)
		var g: Dictionary = cl.get("gains", {})
		check(near(float(g.get("body_xp", 0.0)), 600.0) and near(float(g.get("residue", 0.0)), 10.0) and not g.get("injured", false),
			"an hour in it: +600 body XP and 10 residue cleared, no harm at any body")
		Game.inventory.apply_add(c.id, "marrow_washing_bath", 1, "test")
		Game.submit({"type": "start_bath", "item": "marrow_washing_bath"})
		var cl2 := Game.progression.claim_offline(c, 3600.0)
		check(cl2.get("gains", {}).get("injured", false) and int(c.cultivator.injuries.get("body", {}).get("severity", 0)) >= 1,
			"a Marrow-Washing Bath before Copper Body injures the body")
		c.cultivator.injuries.clear()
		check(ProgressionRules.body_tier_index(cu) == 0 and cu.body_baths.has("copper") and not cu.body_baths.has("iron"),
			"a full Copper Body soak is recorded; a bath that injures is not")
	# Calm Heart Incense: heart demon -10. The Murky Pill sells for a tael.
	cu.heart_demon = 30.0
	Game.inventory.apply_add(c.id, "calm_heart_incense", 1, "test")
	c.pools.cooldowns.erase("item:utility")
	Game.inventory.use_item(c, _bag_index(c, "calm_heart_incense"), true)
	check(near(cu.heart_demon, 20.0), "Calm Heart Incense clears 10 heart demon (%.1f)" % cu.heart_demon)
	cu.heart_demon = 0.0
	check(LootRules.sell_price("murky_pill", null) <= 1, "a Murky Pill sells for a tael")
	c.inventory.bag.fill(null)
	cu.toxicity = 0.0

# ------------------------------------------------------------------ S44 ancient recipes, experiments, the Alchemist Guild
func guild_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	c.inventory.bag.fill(null)
	Unlocks.force_unlock(c.id, "alchemy")
	Game.world.apply_teleport(c.id, "sf_artisan_row")
	var st: ActorState = Game.actor_state(c.id)
	var fo: Dictionary = Game.room_rt.object_def("furnace_sf")
	st.plane = Vector2(float(fo.at[0]) - 40.0, float(fo.at[1]))
	# Deduce: 20% a page + 10% a Dao tier above the third, capped at 95%; a full set teaches it outright.
	var daos: Dictionary = c.cultivator.daos
	var had: Dictionary = daos.get("alchemy", {}).duplicate()
	daos["alchemy"] = {"tier": 3, "insight": 0.0}
	c.crafting["recipe_fragments"] = {}
	c.crafting.recipes.erase("method_conversion_pill")
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 1}], "test")
	check(near(Game.crafting.deduce_chance(c, "method_conversion_pill"), 0.2), "one page of three: a 20% chance")
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 2}], "test")
	daos["alchemy"] = {"tier": 5, "insight": 0.0}
	check(near(Game.crafting.deduce_chance(c, "method_conversion_pill"), 0.6), "two pages and Dao tier 5: 60%")
	c.crafting["recipe_fragments"] = {"sovereign_settling_pill": [1, 2, 3]}
	daos["alchemy"] = {"tier": 9, "insight": 0.0}
	check(near(Game.crafting.deduce_chance(c, "sovereign_settling_pill"), 0.95), "the chance never passes 95%")
	for inp in ContentDB.entry("recipes", "method_conversion_pill").inputs: Game.inventory.apply_add(c.id, str(inp.item), int(inp.count), "test")
	c.crafting["recipe_fragments"] = {"method_conversion_pill": [1, 2]}
	var dd := Game.submit({"type": "deduce_recipe", "recipe": "method_conversion_pill"})
	check(dd.get("ok", false) and c.inventory.count("manual_page") == 0, "a Deduce attempt spends one set of ingredients")
	c.crafting.recipes.erase("method_conversion_pill")
	c.crafting["recipe_fragments"] = {"method_conversion_pill": [1, 2]}
	Game.apply_effects(c.id, [{"kind": "recipe_page", "recipe": "method_conversion_pill", "page": 3}], "test")
	check(Game.crafting.knows(c, "method_conversion_pill"), "the last page of a set teaches the recipe")
	if had.is_empty(): daos.erase("alchemy")
	else: daos["alchemy"] = had
	check(ContentDB.room("mh_loot_cave").get("objects", []).any(func(o): return str(o.id) == "page_method_conversion_pill_1"), "the first page lies in the Mudwater Hideout")
	# Experiments: hidden recipes by their herbs; anything else a Murky Pill; the account log refuses a repeat.
	Unlocks.force_unlock(c.id, "experiments")
	c.inventory.furnace = null
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	Game.account.experiments.clear()
	c.crafting.recipes.erase("sunfire_pill")
	for h in ["riverreed_ginseng_10", "ember_pepper", "willow_moss"]: Game.inventory.apply_add(c.id, h, 3, "test")
	var ex1 := Game.submit({"type": "start_experiment", "herbs": ["ember_pepper", "riverreed_ginseng_10"]})
	check(ex1.get("ok", false) and str(ex1.get("recipe", "")) == "sunfire_pill" and Game.crafting.knows(c, "sunfire_pill"), "ginseng and Ember Pepper reveal the Sunfire Pill")
	var ex2 := Game.submit({"type": "start_experiment", "herbs": ["willow_moss", "ember_pepper"]})
	check(ex2.get("ok", false) and str(ex2.get("result", "")) == "murky" and c.inventory.count("murky_pill") == 1, "an idle mix makes a Murky Pill")
	var ex3 := Game.submit({"type": "start_experiment", "herbs": ["ember_pepper", "willow_moss"]})
	check(str(ex3.get("reason", "")) == "tried" and c.inventory.count("murky_pill") == 1, "the log refuses a mix already tried, in any order")
	check(Game.account.experiments.size() == 2, "the log is the account's")
	# The Alchemist Guild: the Adept exam counts Fine Healing Pills while the candle burns.
	Unlocks.force_unlock(c.id, "alchemist_guild")
	c.crafting["guild"] = {}
	c.crafting["guild_exam"] = {}
	var te := Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	check(not te.get("ok", false), "the Expert exam waits for the Adept badge")
	te = Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "adept"})
	check(te.get("ok", false) and near(float(te.time_s), 180.0), "the Adept exam: three minutes")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "common", "count": 3})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "fine", "count": 3})
	GameEvents.flush()
	check(int(c.crafting.guild_exam.get("made", 0)) == 3 and Game.crafting.guild_rank(c, "alchemy") == "", "Common pills do not count; three Fine ones do")
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "healing_pill", "craft": "alchemy", "quality": "superior", "count": 2})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "alchemy") == "adept" and c.quests.has_flag("guild_alchemy_adept"), "five Fine Healing Pills in time: Guild Adept")
	# Commissions: three a day, capped at a fifth of the day's income target.
	var orders: Array = Game.crafting.commissions(c)
	check(orders.size() == 3 and Game.crafting.commissions(c) == orders, "three orders a day, the same all day")
	var o: Dictionary = orders[0]
	Game.inventory.apply_add(c.id, str(o.item), int(o.count), "test", {"quality": "fine"})
	check(not Game.submit({"type": "deliver_commission", "id": str(o.id)}).get("ok", false), "an order is taken before it is delivered")
	Game.submit({"type": "accept_commission", "id": str(o.id)})
	var t0: int = Game.economy.balance("silver_tael")
	var dl := Game.submit({"type": "deliver_commission", "id": str(o.id), "pay": "taels"})
	var cap: int = Game.crafting.commission_cap(c)
	check(dl.get("ok", false) and Game.economy.balance("silver_tael") - t0 == mini(int(o.pay), cap) and Game.economy.balance("silver_tael") - t0 <= cap,
		"a delivered order pays 1.2x the pill's price, within the daily cap (%d of %d)" % [Game.economy.balance("silver_tael") - t0, cap])
	# The Expert exam teaches the Qi Flow Pill.
	c.crafting["guild_exam"] = {}
	Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	c.crafting.guild_exam.started = Game.sim_time - 400.0
	Game.crafting.tick(0.1)
	GameEvents.flush()
	check(c.crafting.get("guild_exam", {}).is_empty() and Game.crafting.guild_rank(c, "alchemy") == "adept", "a burnt-out candle fails the exam")
	Game.submit({"type": "take_guild_exam", "craft": "alchemy", "rank": "expert"})
	GameEvents.emit_event("craft_completed", {"actor": c.id, "recipe": "foundation_guard_pill", "craft": "alchemy", "quality": "superior", "count": 3})
	GameEvents.flush()
	check(Game.crafting.guild_rank(c, "alchemy") == "expert" and Game.crafting.knows(c, "qi_flow_pill"), "Guild Expert, and the Qi Flow Pill recipe")
	c.crafting["guild"] = {}
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S44 pill tribulation and the Pill Soul's flight
# ------------------------------------------------------------------ S48 the body ladder, physiques, roots, Core Forging
func body_path_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var realm_was := cu.realm_key
	var body_was := cu.body_level
	c.inventory.bag.fill(null)
	# Titles: the worn title's modifiers reach the stats (they were never applied before V5a).
	var had_titles: Array = cu.titles.duplicate()
	var title_was := cu.active_title
	cu.titles.append("fleet_footed")
	cu.active_title = ""
	Game.combat.refresh_stats(c.id)
	var ms0: float = c.stats.value("move_speed")
	cu.active_title = "fleet_footed"
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("move_speed") > ms0 + 0.5, "a worn title's modifier applies (Fleet-Footed: %.1f -> %.1f move speed)" % [ms0, c.stats.value("move_speed")])
	cu.titles = had_titles
	cu.active_title = title_was
	# Body tier needs level, trial and bath, one rung at a time.
	cu.body_tier = "mortal"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.body_level = 20
	cu.physiques.clear()
	cu.realm_key = "qi_unfurling_5"
	Game.progression.pass_body_trial(c.id, "copper")
	check(cu.body_tier == "mortal", "the Copper trial alone does not open Copper Body")
	cu.body_trials.clear()
	cu.body_baths.append("copper")
	Game.progression._check_body_tier(c)
	check(cu.body_tier == "mortal", "the Copper bath alone does not open it either")
	Game.progression.pass_body_trial(c.id, "copper")
	check(cu.body_tier == "copper" and ProgressionRules.body_tier_index(cu) == 1, "trial and bath together: Copper Body")
	check(not cu.physiques.has("stone_marrow"), "Copper Body after Qi Unfurling 3 does not awaken Stone Marrow")
	Game.combat.refresh_stats(c.id)
	var mods := 0
	for m in c.stats.modifiers:
		if str(m.get("source", "")).begins_with("body_tier:copper"): mods += 1
	check(mods == 1, "Copper Body's gift is one Physical Defense modifier (%d)" % mods)
	Game.progression.pass_body_trial(c.id, "iron")
	cu.body_baths.append("iron")
	Game.progression._check_body_tier(c)
	check(cu.body_tier == "copper", "Iron Body waits for body level 36")
	cu.body_level = 35
	Game.progression.apply_body_xp(c.id, ProgressionRules.body_xp_needed(35) + 1.0, "test")
	check(cu.body_level == 36 and cu.body_tier == "iron" and c.crafting.recipes.has("jade_marrow_bath"),
		"reaching body level 36 with the trial and bath done opens Iron Body, which teaches the Jade Marrow Bath")
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("knockback_resistance") >= 0.10, "Iron Body: +10%% knockback resistance (%.2f)" % c.stats.value("knockback_resistance"))
	# The trials themselves are room events: the HP floor fails one, a kill count wins another.
	Game.world.apply_teleport(c.id, "wp_west")
	var sp := ContentDB.entry("set_pieces", "copper_body_trial")
	Game.world._start_event(c, Game.room_rt, sp.room_event)
	c.pools.hp = c.pools.max_hp * 0.4
	Game.world._tick_event(c, Game.room_rt, 0.1)
	check(not Game.room_rt.event.get("active", true), "falling below half HP ends the Copper trial")
	c.pools.hp = c.pools.max_hp
	Game.world.apply_teleport(c.id, "cp_pilgrim_stairs")
	var iron := ContentDB.entry("set_pieces", "iron_body_trial")
	Game.world._start_event(c, Game.room_rt, iron.room_event)
	for i in 5: Game.world._event_kill({"def": "stone_guardian", "victim_kind": "enemy"})
	check(not Game.room_rt.event.get("active", true), "five Stone Guardians in one run pass the Iron trial")
	# Gold Body is immune to Qi Seal; the flag lives on the tier.
	cu.body_tier = "gold"
	Game.combat.apply_status(c.id, "qi_seal", 5.0, 1.0)
	check(not c.pools.has_status("qi_seal"), "Gold Body shrugs off Qi Seal")
	cu.body_tier = "copper"
	# Copper Body: a body technique spends HP when QI runs short, never below a fifth.
	var tiger := ContentDB.entry("techniques", "tiger_rush")
	c.pools.qi = 0.0
	c.pools.hp = c.pools.max_hp
	check(Game.combat.body_hp_cost(c, tiger, 12.0) > 0.0, "Tiger Rush with no QI spends HP at Copper Body")
	c.pools.hp = c.pools.max_hp * 0.2 + 1.0
	check(Game.combat.body_hp_cost(c, tiger, 12.0) == 0.0, "never below a fifth of HP")
	check(Game.combat.body_hp_cost(c, ContentDB.entry("techniques", "flowing_palm"), 8.0) == 0.0, "a technique that is not a body technique never spends HP")
	c.pools.hp = c.pools.max_hp
	# Physiques: gift and drawback, counters, the heart-demon multiplier.
	Game.combat.refresh_stats(c.id)
	var hp0: float = c.stats.value("max_hp")
	var qr0: float = c.stats.value("qi_resistance")
	Game.progression.awaken_physique(c.id, "jade_bone")
	Game.combat.refresh_stats(c.id)
	check(cu.physiques.has("jade_bone") and c.stats.value("max_hp") > hp0 and c.stats.value("qi_resistance") <= qr0,
		"Jade Bone: more HP, a little less Qi Resistance")
	cu.lifetime_stats["fire_pills"] = 49.0
	Game.progression._on_fire_pill({"actor": c.id, "craft": "alchemy", "recipe": "tiger_blood_pill", "count": 1})
	check(cu.physiques.has("ember_heart"), "the fiftieth Fire pill awakens Ember Heart")
	Game.progression._on_fire_pill({"actor": c.id, "craft": "alchemy", "recipe": "healing_pill", "count": 5})
	check(float(cu.lifetime_stats.get("fire_pills", 0)) == 50.0, "pills of other elements do not count")
	cu.heart_demon = 0.0
	cu.physiques.append("hollow_touched")
	Game.progression.apply_heart_demon(c.id, 10.0, "test")
	check(near(cu.heart_demon, 15.0), "Hollow-Touched: heart-demon gains x1.5 (%.1f)" % cu.heart_demon)
	Game.progression.apply_heart_demon(c.id, -10.0, "test")
	check(near(cu.heart_demon, 5.0), "drains are not multiplied")
	cu.heart_demon = 0.0
	cu.physiques.clear()
	cu.body_tier = "mortal"
	cu.realm_key = "bone_forging_9"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.body_level = 17
	Game.progression.pass_body_trial(c.id, "copper")
	cu.body_baths.append("copper")
	cu.body_level = 18
	Game.progression._check_body_tier(c)
	check(cu.physiques.has("stone_marrow"), "Copper Body before Qi Unfurling 3 awakens Stone Marrow")
	cu.physiques.clear()
	# Named roots at the edges: +5% counts, above +10% is Heavenly, the strongest wind is Mutated.
	var apt_was: Dictionary = cu.aptitude.duplicate(true)
	var set_roots := func(vals: Dictionary) -> void:
		for el in ["water", "wood", "fire", "earth", "metal", "wind"]:
			cu.aptitude["element_" + el] = {"value": float(vals.get(el, 0.0)), "revealed": true}
	set_roots.call({"water": 0.11})
	check(ProgressionRules.root_name(cu) == "heavenly", "one element above +10%: Heavenly")
	set_roots.call({"water": 0.10})
	check(ProgressionRules.root_name(cu) == "faint", "exactly +10% is not Heavenly; one element counting alone is Faint")
	set_roots.call({"water": 0.05, "fire": 0.05})
	check(ProgressionRules.root_name(cu) == "true", "two elements at +5%: True")
	set_roots.call({"water": 0.05, "fire": 0.049})
	check(ProgressionRules.root_name(cu) == "faint", "+4.9% does not count")
	set_roots.call({"water": 0.06, "fire": 0.06, "earth": 0.06, "metal": 0.06})
	check(ProgressionRules.root_name(cu) == "mixed", "four elements at +5% or more: Mixed")
	set_roots.call({"wind": 0.07, "water": 0.06})
	check(ProgressionRules.root_name(cu) == "mutated", "wind the strongest: Mutated")
	cu.aptitude["element_fire"].revealed = false
	check(ProgressionRules.root_name(cu) == "", "no root name while the elements are hidden")
	cu.aptitude = apt_was
	# Core Forging: 9 minus the points that count (80% each), floor 5; a flawless Cleansing one more, floor 4.
	check(ProgressionRules.core_grade(0, false) == 9 and ProgressionRules.core_grade(0, true) == 8 and ProgressionRules.core_grade(5, false) == 5
		and ProgressionRules.core_grade(5, true) == 4 and ProgressionRules.core_grade(2, false) == 7, "core grade from points: 9, flawless 8, floor 5, flawless floor 4")
	cu.method_id = "jade_current_scripture"
	cu.residue = 0.0
	c.pools.composure = 100.0
	Game.world.apply_teleport(c.id, "cf_falls_pool")
	c.cultivator.pill_memory["heavenly_flame_pill"] = Game.sim_time - 60.0
	var pts: Array = Game.progression.core_forging_points(c)
	var met := 0
	for pt in pts:
		if pt.met: met += 1
	check(pts.size() == 5 and pts[0].met and pts[2].met and pts[3].met and pts[4].met, "a water method at the Falls Pool, Composure full, no residue, the pill an hour since: four points (%d)" % met)
	var grades := []
	for run in 2:
		Rng.restore(c.id, {}, 4242)
		cu.realm_key = "heart_tempering_9"
		cu.purity = 9
		Game.progression._forge_core(c)
		grades.append(cu.core_grade)
	check(grades[0] == grades[1] and cu.purity == cu.core_grade and cu.core_grade >= 5 and cu.core_grade <= 9 - 0,
		"the same seed forms the same core (%s)" % str(grades))
	c.cultivator.pill_memory.erase("heavenly_flame_pill")
	cu.core_grade = 0
	cu.purity = 9
	cu.realm_key = realm_was
	cu.body_level = body_was
	cu.body_tier = "mortal"
	cu.body_trials.clear()
	cu.body_baths.clear()
	cu.lifetime_stats.erase("fire_pills")
	cu.events_passed.erase("iron_body_trial")
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 heavenly tribulation, fates, Qi Deviation
func heaven_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var st: ActorState = Game.actor_state(c.id)
	var realm_was := cu.realm_key
	var hd_was := cu.heart_demon
	var sin_was: int = c.relations.sin
	c.inventory.bag.fill(null)
	# Bolt counts by realm, heart demon and sin.
	check(ProgressionRules.tribulation_bolts("heart_tempering_9", 0, 0) == 0, "no tribulation into Cloud Stride (the Heart Trial is the set piece)")
	check(ProgressionRules.tribulation_bolts("cloud_stride_9", 0, 0) == 3 and ProgressionRules.tribulation_bolts("spirit_awakening_9", 0, 0) == 6
		and ProgressionRules.tribulation_bolts("heaven_glimpse_3", 0, 0) == 9, "3 bolts into Spirit Awakening, 6 into Heaven Glimpse, 9 into Sage")
	check(ProgressionRules.tribulation_bolts("sage_3", 0, 0) == 18 and ProgressionRules.tribulation_bolts("sage_sovereign_3", 0, 0) == 27,
		"then waves of 9: 2 into Sage Sovereign, 3 into Will Manifest")
	check(ProgressionRules.tribulation_bolts("cloud_stride_9", 24.0, 99) == 3 and ProgressionRules.tribulation_bolts("cloud_stride_9", 25.0, 100) == 5
		and ProgressionRules.tribulation_bolts("cloud_stride_9", 50.0, 0, 2) == 7, "+1 per 25 heart demon, +1 per 100 sin, and a fate's extra bolts")
	check(near(ProgressionRules.tribulation_damage(1000.0, 0, 0.0, false), 200.0) and near(ProgressionRules.tribulation_damage(1000.0, 500, 0.0, false), 400.0)
		and near(ProgressionRules.tribulation_damage(1000.0, 0, 200.0, true), 200.0), "bolt damage: 20% max HP x (1 + sin/500) x (1 + heart demon/200), guard halves")
	# A tribulation run: every bolt lands on a character who stands still; one talisman takes one bolt.
	Game.world.apply_teleport(c.id, "cp_cleansing_summit")
	cu.realm_key = "cloud_stride_9"
	cu.heart_demon = 0.0
	c.relations.sin = 0
	cu.fates.clear()
	cu.fate_offer = []
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	Game.inventory.apply_add(c.id, "lightning_rod_talisman", 1, "test")
	var starts := []
	var hook := func(n: String, p: Dictionary): if n == "tribulation_result": starts.append(p)
	GameEvents.event.connect(hook)
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": 1.0})
	check(Game.progression.is_under_tribulation(c.id) and int(Game.progression.tribulation_view(c.id).total) == 3, "the cloud gathers: 3 bolts")
	var guard := 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	var res: Dictionary = starts.back() if not starts.is_empty() else {}
	check(res.get("survived", false) and int(res.get("absorbed", 0)) == 1 and c.inventory.count("lightning_rod_talisman") == 0,
		"three bolts weathered; the Lightning Rod took one (%s)" % str(res))
	check(cu.realm_key == "spirit_awakening_1", "a weathered tribulation settles the breakthrough")
	var offer: Array = cu.fate_offer.duplicate()
	var distinct := {}
	for f in offer: distinct[f] = true
	check(offer.size() == 3 and distinct.size() == 3 and not offer.has("fox_spirits_favour"), "three distinct fate cards are offered (%s)" % str(offer))
	# Stepping out of the ring: the bolt misses.
	cu.realm_key = "cloud_stride_9"
	c.pools.hp = c.pools.max_hp
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": -1.0})
	var home: Vector2 = st.plane
	guard = 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		var tv: Dictionary = Game.progression.tribulation_view(c.id)
		if not (tv.get("warn", {}) as Dictionary).is_empty(): st.plane = Vector2(float(tv.warn.x) + 400.0, float(tv.warn.y))
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	st.plane = home
	check(int(starts.back().get("struck", -1)) == 0 and bool(starts.back().get("survived", false)), "stepping out of every ring: no bolt lands (%s)" % str(starts.back()))
	check(cu.realm_key == "cloud_stride_9", "a weathered tribulation still rolls the breakthrough (forced to fail here)")
	# Brought to nothing under the heavens: a Bodily failure, not a grave wound.
	c.pools.hp = c.pools.max_hp * 0.1
	Game.progression._start_tribulation(c, {"to": "spirit_awakening_1", "risk": "low", "from": "cloud_stride_9", "used": [], "causes": [], "bonus": 1.0})
	guard = 0
	while Game.progression.is_under_tribulation(c.id) and guard < 400:
		Game.progression._tick_tribulation(c, 0.1)
		GameEvents.flush()
		guard += 1
	check(not starts.back().get("survived", true) and str(starts.back().get("failure", "")) == "bodily_failure" and c.pools.hp > 0.0 and cu.realm_key == "cloud_stride_9",
		"a bolt that would kill fails the breakthrough with the body and leaves the character standing")
	GameEvents.event.disconnect(hook)
	c.cultivator.injuries.clear()
	c.pools.hp = c.pools.max_hp
	# Fates: gifts and costs, realm-long costs that lapse, and what waits for the next tribulation or breakthrough.
	cu.realm_key = "cloud_stride_5"
	cu.fate_offer = []
	check(not Game.submit({"type": "choose_fate", "card": "iron_will"}).get("ok", false), "no fate can be chosen without an offer")
	cu.fate_offer = ["iron_will", "quiet_heart", "hungry_dantian"]
	check(not Game.submit({"type": "choose_fate", "card": "lucky_star"}).get("ok", false), "only an offered card can be chosen")
	Game.combat.refresh_stats(c.id)
	var will0: float = c.stats.value("will")
	var ms0: float = c.stats.value("move_speed")
	check(Game.submit({"type": "choose_fate", "card": "iron_will"}).get("ok", false) and cu.fate_offer.is_empty(), "choosing a card spends the offer")
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("will") >= will0 + 9.9 and c.stats.value("move_speed") < ms0, "Iron Will: +10 Will, slower this realm")
	cu.realm_key = "spirit_awakening_1"
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("will") >= will0 + 9.9 and near(c.stats.value("move_speed"), ms0), "in the next great realm the Will stays and the slowness lapses")
	cu.heart_demon = 30.0
	cu.fate_offer = ["quiet_heart", "hungry_dantian", "debt_of_heaven"]
	Game.submit({"type": "choose_fate", "card": "quiet_heart"})
	check(near(cu.heart_demon, 15.0), "Quiet Heart: heart demon -15")
	cu.pill_resistance = {}
	cu.fate_offer = ["hungry_dantian", "debt_of_heaven", "lucky_star"]
	Game.submit({"type": "choose_fate", "card": "hungry_dantian"})
	check(ProgressionRules.resistance_count(cu, "body") == 1 and ProgressionRules.resistance_count(cu, "accumulation") == 1 and ProgressionRules.resistance_count(cu, "soul") == 1, "Hungry Dantian: pill resistance +1 in every family")
	cu.pill_resistance = {}
	cu.purity = 6
	cu.fate_offer = ["debt_of_heaven", "lucky_star", "iron_will"]
	Game.submit({"type": "choose_fate", "card": "debt_of_heaven"})
	check(cu.purity == 5 and ProgressionRules.tribulation_bolts("cloud_stride_9", 0.0, 0, int(Game.progression._spend_fate_next(c, "tribulation_bolts"))) == 5
		and Game.progression._spend_fate_next(c, "tribulation_bolts") == 0.0, "Debt of Heaven: purity a grade better; the next tribulation alone gets 2 more bolts")
	cu.fate_offer = ["scar_of_failure", "lucky_star", "iron_will"]
	Game.submit({"type": "choose_fate", "card": "scar_of_failure"})
	check(cu.stability == "unstable" and near(Game.progression._spend_fate_next(c, "breakthrough_bonus"), 0.10), "Scar of Failure: unstable now, +10% on the next breakthrough")
	cu.stability = "stable"
	# The draw: distinct, by weight, never an unavailable card, the same for the same seed.
	var pool := ProgressionRules.fate_pool(Game.ctx(c))
	var draws := []
	for run in 2:
		Rng.restore(c.id, {}, 99)
		draws.append(ProgressionRules.draw_fates(pool, 3, Rng.stream(c.id, "breakthrough")))
	check(draws[0] == draws[1], "the same seed draws the same three cards")
	var never := true
	for i in 60:
		for f in ProgressionRules.draw_fates(pool, 3, Rng.stream(c.id, "breakthrough")):
			if str(f) == "fox_spirits_favour": never = false
	check(never, "a card not yet available (Fox Spirit's Favour, S46) is never drawn")
	# Blood Memory: a streak of 10 kills feeds the heart demon only with the fate.
	cu.heart_demon = 0.0
	for i in 10: Game.progression._count_streak(c)
	check(near(cu.heart_demon, 0.0), "a streak of 10 without Blood Memory costs nothing")
	cu.fates.append({"id": "blood_memory", "realm": ProgressionRules.great_realm(cu.realm_key)})
	for i in 10: Game.progression._count_streak(c)
	check(near(cu.heart_demon, 1.0), "Blood Memory: +1 heart demon at a streak of 10 (%.1f)" % cu.heart_demon)
	# Qi Deviation: only at Severe risk or on a Poor method.
	check(ProgressionRules.qi_deviates("severe", "good") and ProgressionRules.qi_deviates("low", "poor") and not ProgressionRules.qi_deviates("high", "excellent"),
		"Qi Deviation only at Severe risk or with a Poor method")
	c.pools.statuses.clear()
	var method_was := cu.method_id
	cu.method_id = "stonebody_canon"
	var earth_was: Dictionary = cu.aptitude.get("element_earth", {}).duplicate()
	cu.aptitude["element_earth"] = {"value": 0.08, "revealed": true}
	Game.progression._maybe_deviate(c, "high")
	check(not c.pools.has_status("qi_deviation"), "a failure at High risk on a good method does not deviate")
	Game.progression._maybe_deviate(c, "severe")
	var els := {}
	for i in 30: els[Game.combat.technique_element(c, ContentDB.entry("techniques", "flowing_palm"))] = true
	check(c.pools.has_status("qi_deviation") and els.size() >= 3, "at Severe risk the Qi deviates: techniques take random elements (%d seen)" % els.size())
	c.pools.statuses.clear()
	check(Game.combat.technique_element(c, ContentDB.entry("techniques", "flowing_palm")) == "water", "once it passes, techniques keep their own element")
	cu.aptitude["element_earth"] = earth_was
	cu.method_id = method_was
	cu.fates.clear()
	cu.fate_offer = []
	cu.realm_key = realm_was
	cu.heart_demon = hd_was
	c.relations.sin = sin_was
	cu.purity = 9
	c.cultivator.injuries.clear()
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 Inner Arts, stances, technique grades, combos
func arts_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var realm_was := cu.realm_key
	var weapon_was = c.inventory.equipped.get("weapon")
	check(ProgressionRules.inner_art_slot_count("bone_forging_9") == 0 and ProgressionRules.inner_art_slot_count("qi_unfurling_1") == 2
		and ProgressionRules.inner_art_slot_count("heart_tempering_1") == 3 and ProgressionRules.inner_art_slot_count("spirit_awakening_1") == 4,
		"Inner Art slots: 2 at Qi Unfurling 1, 3 at Heart Tempering 1, 4 at Spirit Awakening 1")
	cu.realm_key = "qi_unfurling_5"
	cu.inner_arts = []
	cu.inner_arts_known = []
	check(not Game.submit({"type": "equip_inner_art", "slot": 0, "art": "iron_shirt"}).get("ok", false), "an Inner Art not yet learned cannot be worn")
	Game.progression.apply_learn_inner_art(c.id, "iron_shirt")
	Game.progression.apply_learn_inner_art(c.id, "ember_channel")
	Game.progression.apply_learn_inner_art(c.id, "sword_heart")
	Game.progression.apply_learn_inner_art(c.id, "swallows_breath")
	Game.combat.refresh_stats(c.id)
	var pd0: float = c.stats.value("physical_defense")
	check(Game.submit({"type": "equip_inner_art", "slot": 0, "art": "iron_shirt"}).get("ok", false), "Iron Shirt worn in the first slot")
	check(c.stats.value("physical_defense") > pd0 * 1.07, "Iron Shirt: +8%% Physical Defense (%.1f -> %.1f)" % [pd0, c.stats.value("physical_defense")])
	check(not Game.submit({"type": "equip_inner_art", "slot": 2, "art": "ember_channel"}).get("ok", false), "the third slot is closed at Qi Unfurling")
	Game.submit({"type": "equip_inner_art", "slot": 1, "art": "iron_shirt"})
	check(str(cu.inner_arts[0]) == "" and str(cu.inner_arts[1]) == "iron_shirt", "an art moves to the slot it is put in")
	var fire_t := ContentDB.entry("techniques", "ember_burst")
	var cost0 := Game.combat.technique_cost(c, fire_t)
	var water_cost0 := Game.combat.technique_cost(c, ContentDB.entry("techniques", "rising_tide"))
	Game.submit({"type": "equip_inner_art", "slot": 0, "art": "ember_channel"})
	check(Game.combat.technique_cost(c, fire_t) < cost0 * 0.95 and near(Game.combat.technique_cost(c, ContentDB.entry("techniques", "rising_tide")), water_cost0),
		"Ember Channel: Fire techniques cost less, others do not")
	Game.submit({"type": "equip_inner_art", "slot": 0, "art": "swallows_breath"})
	check(near(c.stats.value("dodge_cooldown"), -0.15), "Swallow's Breath: the dodge cooldown 15%% shorter (%.2f)" % c.stats.value("dodge_cooldown"))
	# Weapon-linked: Sword Heart sleeps without a jian.
	cu.realm_key = "heart_tempering_1"
	Game.submit({"type": "equip_inner_art", "slot": 2, "art": "sword_heart"})
	c.inventory.equipped["weapon"] = null
	Game.combat.refresh_stats(c.id)
	check(int(ProgressionRules.path_flag(c, "sword_intent_max", 10)) == 10, "Sword Heart sleeps with bare hands")
	c.inventory.equipped["weapon"] = {"id": "iron_jian", "uid": 900001, "quality": "common"}
	Game.combat.refresh_stats(c.id)
	check(int(ProgressionRules.path_flag(c, "sword_intent_max", 10)) == 12, "with a jian in hand Sword Intent builds to 12")
	# Stances: one per family, and only with that weapon in hand.
	check(not Game.submit({"type": "set_stance", "family": "jian", "stance": "iron_horse"}).get("ok", false), "a stance belongs to its own family")
	var as0: float = c.stats.value("attack_speed")
	check(Game.submit({"type": "set_stance", "family": "jian", "stance": "willow_leaf_parry"}).get("ok", false), "the jian takes Willow Leaf Parry")
	check(float(ProgressionRules.path_flag(c, "parry_counter", 0.0)) == 2.0 and c.stats.value("attack_speed") < as0, "held: a parry counters for 200%, attacks a little slower")
	Game.submit({"type": "set_stance", "family": "gauntlets", "stance": "iron_horse"})
	check(not ProgressionRules.path_flag(c, "knockback_immune", false), "Iron Horse sleeps while a jian is in hand")
	c.inventory.equipped["weapon"] = {"id": "iron_gauntlets", "uid": 900002, "quality": "common"}
	Game.combat.refresh_stats(c.id)
	check(ProgressionRules.path_flag(c, "knockback_immune", false) and ProgressionRules.path_flag(c, "parry_counter", null) == null,
		"with gauntlets, Iron Horse holds and the jian's stance does not")
	Game.submit({"type": "set_stance", "family": "gauntlets", "stance": ""})
	Game.submit({"type": "set_stance", "family": "jian", "stance": ""})
	check(cu.stances.is_empty(), "letting a stance go clears it")
	# Grades and combos.
	check(near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "flowing_palm")), 0.0)
		and near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "crescent_arc")), 0.10)
		and near(ProgressionRules.technique_grade_bonus(ContentDB.entry("techniques", "glimpse_of_heaven")), 0.20), "technique grades: Common +0, Earth +10%, Heaven +20%")
	check(str(ProgressionRules.combo_for("flowing_palm", "tiger_rush", 0.8).get("id", "")) == "palm_into_rush", "Flowing Palm then Tiger Rush within a second: a combo")
	check(ProgressionRules.combo_for("flowing_palm", "tiger_rush", 1.2).is_empty() and ProgressionRules.combo_for("tiger_rush", "flowing_palm", 0.2).is_empty(),
		"too slow, or the wrong order: no combo")
	c.inventory.equipped["weapon"] = weapon_was
	cu.inner_arts = []
	cu.inner_arts_known = []
	cu.stances = {}
	cu.realm_key = realm_was
	Game.combat.refresh_stats(c.id)

# ------------------------------------------------------------------ S48 vows, Killing Intent, epiphany, Blood Burning, the false realm
func vows_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	var st: ActorState = Game.actor_state(c.id)
	var realm_was := cu.realm_key
	c.inventory.bag.fill(null)
	Game.world.apply_teleport(c.id, "wp_west")
	Unlocks.force_unlock(c.id, "vows")
	cu.vows.clear()
	cu.heart_demon = 0.0
	# Vows block what they forbid; letting one go breaks it (+15 heart demon).
	check(Game.submit({"type": "set_vow", "vow": "plain_fare", "on": true}).get("ok", false) and Game.submit({"type": "set_vow", "vow": "fasting", "on": true}).get("ok", false),
		"vows taken: Plain Fare and Fasting")
	Game.inventory.apply_add(c.id, "tiger_blood_pill", 1, "test")
	Game.inventory.apply_add(c.id, "rice_ball", 1, "test")
	Game.inventory.apply_add(c.id, "healing_pill", 1, "test")
	c.pools.cooldowns.clear()
	check(str(Game.inventory.use_item(c, _bag_index(c, "tiger_blood_pill"), true).get("reason", "")) == "vow", "Plain Fare refuses a burst pill")
	check(str(Game.inventory.use_item(c, _bag_index(c, "rice_ball"), true).get("reason", "")) == "vow", "Fasting refuses food that lends a buff")
	check(Game.inventory.use_item(c, _bag_index(c, "healing_pill"), true).get("ok", false), "a healing pill is no burst pill")
	check(near(cu.heart_demon, 0.0), "taking a vow costs nothing")
	Game.submit({"type": "set_vow", "vow": "plain_fare", "on": false})
	check(near(cu.heart_demon, 15.0) and not cu.vows.has("plain_fare"), "breaking a vow: +15 heart demon (%.1f)" % cu.heart_demon)
	Game.combat.refresh_stats(c.id)
	check(c.stats.value("accumulation_rate") >= 0.05 - 0.0001, "Fasting's gift: +5% accumulation")
	Game.submit({"type": "set_vow", "vow": "fasting", "on": false})
	cu.heart_demon = 0.0
	# Mercy: a fleeing foe survives the blow that would have killed it.
	Game.submit({"type": "set_vow", "vow": "mercy", "on": true})
	var e: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(40, 0), 2)
	e.ai["fled"] = true
	var pv: Dictionary = Game.combat.player_view(c)
	var blow := {"damage_type": "physical", "element": "none", "mult": [8.0, 8.0], "range": [1.0, 1.0], "source": "test"}
	for i in 6:
		if not e.alive or e.pools.hp <= 1.01: break
		Game.combat._player_hits_enemy(c, pv, e, blow, 1)
	check(e.alive and e.pools.hp >= 1.0, "Mercy: the fleeing boarlet gets away with its life")
	Game.submit({"type": "set_vow", "vow": "mercy", "on": false})
	for i in 6:
		if not e.alive: break
		Game.combat._player_hits_enemy(c, pv, e, blow, 1)
	check(not e.alive, "without the vow the blow lands")
	GameEvents.flush()
	cu.heart_demon = 0.0
	# Killing Intent: kills in quick succession, +1% crit a stack, up to 10; Silence sheathes it.
	Game.combat.killing_intent.erase(c.id)
	var crit0 := float(Game.combat.player_view(c).crit_chance)
	for i in 12: Game.combat._gain_killing_intent(c, e)
	check(Game.combat.killing_intent_stacks(c.id) == 10 and near(float(Game.combat.player_view(c).crit_chance), crit0 + 0.10),
		"Killing Intent: 10 stacks at most, +10%% crit (%d)" % Game.combat.killing_intent_stacks(c.id))
	for i in 110: Game.combat._tick_sword(c, 0.1)
	check(Game.combat.killing_intent_stacks(c.id) == 0, "ten seconds without a kill and it fades")
	Game.submit({"type": "set_vow", "vow": "silence", "on": true})
	Game.combat._gain_killing_intent(c, e)
	check(Game.combat.killing_intent_stacks(c.id) == 0, "Silence keeps the killing intent sheathed")
	Game.submit({"type": "set_vow", "vow": "silence", "on": false})
	cu.heart_demon = 0.0
	# Epiphany: five times the insight for a minute, then two hours before another.
	cu.epiphany_cooldown = 0.0
	Game.progression.trigger_epiphany(c, Rng.stream(c.id, "fortune"))
	Game.combat.refresh_stats(c.id)
	check(near(cu.epiphany_cooldown, 7200.0) and c.stats.value("insight_rate") >= 3.9, "an epiphany: insight x5 and a two-hour cooldown")
	var seen := 0
	for i in 2000:
		var before := cu.epiphany_cooldown
		Game.progression._roll_epiphany(c, "tech:flowing_palm:x")
		if cu.epiphany_cooldown != before: seen += 1
	check(seen == 0, "no second epiphany while the mind rests")
	cu.epiphany_cooldown = 0.0
	# Blood Burning: 30% of max HP and a body injury for +50% attack.
	cu.realm_key = "sage_sovereign_1"
	Game.combat.refresh_stats(c.id)
	if not cu.techniques_known.has("blood_burning"): cu.techniques_known.append("blood_burning")
	var slots_was: Array = cu.technique_slots.duplicate()
	Unlocks.force_unlock(c.id, "technique_slots_2")
	cu.technique_slots[0] = "blood_burning"
	cu.injuries.clear()
	c.pools.hp = c.pools.max_hp
	c.pools.cooldowns.clear()
	var atk0: float = c.stats.value("physical_attack")
	var max0: float = c.pools.max_hp
	var bb := Game.combat.use_technique(c, 0, 1)
	var hp_after: float = c.pools.hp
	for i in 10: Game.combat.tick(0.1)
	Game.combat.refresh_stats(c.id)
	check(bb.get("ok", false) and absf(hp_after - max0 * 0.7) <= max0 * 0.02 and cu.injuries.has("body"),
		"Blood Burning costs 30%% of max HP and wounds the body (%.0f of %.0f)" % [hp_after, max0])
	check(c.stats.value("physical_attack") > atk0 * 1.4, "and burns +50%% attack (%.0f -> %.0f)" % [atk0, c.stats.value("physical_attack")])
	cu.technique_slots = slots_was
	cu.injuries.clear()
	# The false realm: Concealment shows up to two great realms lower.
	cu.realm_key = "heart_tempering_5"
	var had_conceal := cu.secret_arts.has("concealment")
	cu.secret_arts.erase("concealment")
	check(not Game.submit({"type": "set_false_realm", "realm": "qi_kindling_1"}).get("ok", false), "no false realm without Concealment")
	cu.secret_arts.append("concealment")
	var choices: Array = Game.progression.false_realm_choices(c)
	check(choices == ["qi_kindling_1", "qi_unfurling_1"], "two great realms lower at most (%s)" % str(choices))
	check(not Game.submit({"type": "set_false_realm", "realm": "bone_forging_1"}).get("ok", false), "three great realms lower is too far")
	check(Game.submit({"type": "set_false_realm", "realm": "qi_unfurling_1"}).get("ok", false) and Game.progression.shown_realm(c) == "qi_unfurling_1",
		"others now see Qi Unfurling 1")
	# ...and they talk to the weaker cultivator you show; bandits on the road see easy prey.
	var talk: Dictionary = Game.quest.talk(c, "alliance_guard").get("dialogue", {})
	check(str((talk.get("lines", [""]) as Array)[0]) == str(ContentDB.entry("npcs", "alliance_guard").concealed_lines[0]), "a veiled realm changes what people say")
	var amb: Dictionary = ContentDB.room("cr_caravan_road").get("ambush", {})
	check(near(Game.world.ambush_chance(c, amb), 0.12), "the Mudwater stragglers jump a veiled Heart Tempering at twice the odds (%.2f)" % Game.world.ambush_chance(c, amb))
	Game.submit({"type": "set_false_realm", "realm": ""})
	check(near(Game.world.ambush_chance(c, amb), 0.0), "unveiled at Heart Tempering 5 you are past their reach")
	cu.realm_key = "qi_kindling_8"
	check(near(Game.world.ambush_chance(c, amb), 0.06), "at Qi Kindling 8 the plain odds hold")
	Game.world.load_room(c, "cr_caravan_road", "")
	Game.world.ambush_cd.erase(c.id)
	var sprung := [0]
	var on_amb := func(n: String, _p: Dictionary) -> void:
		if n == "ambush_sprung": sprung[0] += 1
	GameEvents.event.connect(on_amb)
	Game.world.spring_ambush(c, amb)
	GameEvents.flush()
	GameEvents.event.disconnect(on_amb)
	var gang := 0
	for foe in Game.room_rt.living_enemies():
		if foe.summoned and foe.def_id == "mudwater_bandit": gang += 1
	check(gang == 2 and sprung[0] == 1 and float(Game.world.ambush_cd.get(c.id, 0.0)) > 0.0, "an ambush drops two bandits around you and rests (%d)" % gang)
	Game.world.ambush_cd.erase(c.id)
	cu.realm_key = "heart_tempering_5"
	if not had_conceal: cu.secret_arts.erase("concealment")
	# A teacher's lesson opens a rare Dao at exactly tier 1, even under a Dao Echo fate for another Dao.
	Unlocks.force_unlock(c.id, "dao_tree")
	var fates_was: Array = cu.fates.duplicate(true)
	cu.fates.append({"card": "dao_echo", "dao": "sword"})
	cu.daos.erase("blood")
	var room_was := str(c.position.get("room", ""))
	c.position.room = "ir_ancestor_hall"   # a rare Dao deepens only where the Expanse's Laws allow it
	Game.progression.apply_open_dao(c.id, "blood")
	c.position.room = room_was
	check(int(cu.daos.get("blood", {}).get("tier", 0)) == 1, "a teacher opens the Blood Dao at tier 1 under Dao Echo")
	cu.fates = fates_was
	cu.daos.erase("blood")
	# Nascent-soul escape: from Sage a grave wound costs 5% of the stage, not 10%.
	cu.realm_key = "sage_1"
	cu.state = "accumulating"
	cu.qp = cu.need() * 0.5
	Game.progression._on_gravely_wounded({"actor": c.id})
	check(near(cu.qp, cu.need() * 0.45), "from Sage the soul flees: 5%% lost (%.3f of the need left)" % (cu.qp / cu.need()))
	cu.realm_key = "cloud_stride_5"
	cu.qp = cu.need() * 0.5
	Game.progression._on_gravely_wounded({"actor": c.id})
	check(near(cu.qp, cu.need() * 0.4), "below Sage: 10% lost")
	cu.injuries.clear()
	cu.heart_demon = 0.0
	# A boss's nascent-soul self-detonation: telegraphed, then a blast that ends the fight.
	cu.realm_key = realm_was
	Game.combat.refresh_stats(c.id)
	c.pools.hp = c.pools.max_hp
	var boss: EnemyState = Game.enemies.spawn_at("pirate_captain", st.plane + Vector2(120, 0), 80)
	boss.pools.hp = boss.pools.max_hp * 0.35
	Game.enemies._check_phases(boss)
	boss.pools.hp = boss.pools.max_hp * 0.1
	Game.enemies._check_phases(boss)
	check(str(boss.ai.get("state", "")) == "detonating" and boss.invulnerable, "cornered, the Captain burns his nascent soul (a telegraph)")
	var hp_before: float = c.pools.hp
	for i in 40:
		if not boss.alive: break
		Game.enemies.tick(0.1)
	GameEvents.flush()
	check(not boss.alive and c.pools.hp < hp_before - c.pools.max_hp * 0.5, "the blast lands on whoever stays in the ring, and the Captain is gone")
	c.pools.hp = c.pools.max_hp
	cu.vows.clear()
	cu.heart_demon = 0.0
	c.inventory.bag.fill(null)

# ------------------------------------------------------------------ S45 rare herbs, the harvest tap, seeds, seasons
func herbs_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var cu: CultivatorState = c.cultivator
	Unlocks.force_unlock(c.id, "herb_gathering")
	var prof_was: Dictionary = c.professions.get("herb_gathering", {"rank": "apprentice", "xp": 0.0}).duplicate()
	c.professions["herb_gathering"] = {"rank": "adept", "xp": 1000.0}
	var had_conceal := cu.secret_arts.has("concealment")
	cu.secret_arts.erase("concealment")
	# The tap window by rank: 12% Apprentice ... 28% Grandmaster, around the ring's target.
	check(near(HerbRules.tap_window("apprentice"), 0.12) and near(HerbRules.tap_window("expert"), 0.20) and near(HerbRules.tap_window("grandmaster"), 0.28),
		"the tap window widens with rank: 12% / 20% / 28%")
	check(HerbRules.tap_perfect(0.759, "apprentice") and not HerbRules.tap_perfect(0.761, "apprentice") and HerbRules.tap_perfect(0.839, "grandmaster")
		and not HerbRules.tap_perfect(-1.0, "grandmaster"), "a tap is perfect only inside its band; no tap is a miss")
	check(Game.crafting.RANK_CAPS.herb_gathering.back()[1] == "grandmaster", "herb gathering can reach Grandmaster")
	# Ripening: dawn, every 2nd in-game day, 20 minutes.
	Game.world.load_room(c, "dw_bend_shore", "")
	var o: Dictionary = Game.room_rt.object_def("rare_ginseng_bs")
	var L := HerbRules.day_s()
	var centre := float(40000 + int(o.ripen.offset)) * L
	check(HerbRules.ripen_state(o, centre).ripe and HerbRules.ripen_state(o, centre + 590.0).ripe and HerbRules.ripen_state(o, centre - 590.0).ripe,
		"a hundred-year ginseng is ripe for 20 minutes around dawn")
	var after := HerbRules.ripen_state(o, centre + 610.0)
	check(not after.ripe and near(float(after.seconds), 2.0 * L - 1210.0, 1.0) and not HerbRules.ripen_state(o, centre + L).ripe,
		"then it grows for two in-game days (%.0f s to the next window)" % float(after.seconds))
	var st: ActorState = Game.actor_state(c.id)
	var pick := func(obj: Dictionary, timing: float) -> Dictionary:
		Game.room_rt.objects[str(obj.id)] = {"state": "ready", "timer": 0.0, "hits": 0}
		st.plane = Vector2(float(obj.at[0]) - 30.0, float(obj.at[1]))
		st.altitude = float(obj.get("alt", 0))
		var g := Game.submit({"type": "interact", "object": str(obj.id)})
		if not g.get("ok", false): return g
		Game.crafting.pending[c.id].started = Game.sim_time - 5.0
		return Game.submit({"type": "complete_node", "object": str(obj.id), "timing": timing})
	# Picked early, it is a tier younger even with a perfect tap.
	Clock.override_utc = centre + 700.0
	var early: Dictionary = pick.call(o, 0.7)
	check(early.get("ok", false) and str(early.get("item", "")) == "riverreed_ginseng_10" and early.get("early", false), "picked early: a ten-year root (%s)" % str(early.get("item", early)))
	# Ripe, the Tide Crab wakes as you reach for it, once per ripening.
	Clock.override_utc = centre
	var woke := [0]
	var on_wake := func(n: String, p: Dictionary) -> void:
		if n == "guardian_spawned": woke[0] += 1
	GameEvents.event.connect(on_wake)
	var guarded: Dictionary = pick.call(o, 0.7)
	var again: Dictionary = pick.call(o, 0.7)
	GameEvents.flush()
	var keeper: EnemyState = Game.room_rt.enemies.get(int(Game.room_rt.guardians.get("rare_ginseng_bs", -1)))
	check(str(guarded.get("reason", "")) == "guarded" and str(again.get("reason", "")) == "guarded" and woke[0] == 1 and keeper != null and keeper.elite
		and keeper.def_id == "tide_crab", "the Tide Crab guards the ripe root, and wakes once a ripening (%d)" % woke[0])
	# Lured past its leash, it no longer stops you: a perfect tap keeps the full hundred years.
	keeper.plane = Vector2(float(o.at[0]) + 700.0, keeper.plane.y)
	var ripe: Dictionary = pick.call(o, 0.7)
	check(ripe.get("ok", false) and str(ripe.get("item", "")) == "riverreed_ginseng_100" and ripe.get("perfect", false), "lured away: a perfect hundred-year root")
	# The next ripening wakes a new guardian; under Concealment an unaware one lets you pick, but a miss drops a tier.
	Clock.override_utc = centre + 2.0 * L
	pick.call(o, 0.7)
	GameEvents.flush()
	check(woke[0] == 2, "a new ripening, a new guardian (%d)" % woke[0])
	var keeper2: EnemyState = Game.room_rt.enemies.get(int(Game.room_rt.guardians.get("rare_ginseng_bs", -1)))
	cu.secret_arts.append("concealment")
	keeper2.ai["state"] = "idle"
	var unseen: Dictionary = pick.call(o, 0.0)
	check(unseen.get("ok", false) and str(unseen.get("item", "")) == "riverreed_ginseng_10" and not unseen.get("perfect", true), "picked unseen, but a missed tap: ten years")
	keeper2.ai["state"] = "aggro"
	check(str(pick.call(o, 0.7).get("reason", "")) == "guarded", "a guardian that has seen you still stops you")
	GameEvents.event.disconnect(on_wake)
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	# Seeds: a perfect harvest finds one about one time in ten, the same under the same seed.
	Game.world.load_room(c, "cf_falls_pool", "")
	var lotus: Dictionary = Game.room_rt.object_def("rare_lotus_fp")
	var lc := float(30000 * 3 + int(lotus.ripen.offset)) * L + 0.75 * L
	Clock.override_utc = lc
	var rng := Rng.stream(c.id, "crafting")
	var rng_was := rng.state
	var runs: Array = []
	for run in 2:
		rng.seed = 4242
		var seeds := 0
		for i in 80:
			if str(pick.call(lotus, 0.7).get("seed", "")) == "mist_lotus_seed": seeds += 1
		runs.append(seeds)
	rng.state = rng_was
	check(runs[0] == runs[1] and runs[0] >= 2 and runs[0] <= 18, "perfect harvests find Mist Lotus seeds at about 10%%, the same under a fixed seed (%d, %d of 80)" % [runs[0], runs[1]])
	check(ContentDB.config("garden").seeds.get("cloudtop_orchid", "") != "" and HerbRules.harvest_seed("cloudtop_orchid_100") == "",
		"Cloudtop Orchid seeds never come from a harvest")
	# Seasons: the Thicket Heart's hundred-year pepper flowers only in Summer.
	var summer := 1900000000.0
	while HerbRules.season(summer) != "summer": summer += 604800.0
	var pepper: Dictionary = ContentDB.room("bg_thicket_heart").objects.filter(func(x): return str(x.id) == "rare_pepper_th")[0]
	check(HerbRules.in_season(pepper, summer) and not HerbRules.in_season(pepper, summer + 604800.0) and HerbRules.season(summer + 604800.0) == "autumn",
		"seasons turn weekly, and the pepper flowers only in Summer")
	Game.world.load_room(c, "bg_thicket_heart", "")
	Clock.override_utc = summer + 604800.0
	var dormant: Dictionary = pick.call(pepper, 0.7)
	check(not dormant.get("ok", false) and Game.account.codex.has("seasons"), "out of season it lies dormant, and the Codex learns the seasons")
	# An older herb stands in for a younger one when the recipe's own runs short, and refines better.
	for id in ["riverreed_ginseng_10", "riverreed_ginseng_100", "riverreed_ginseng_1000"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test")
	var a1: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 1}], 1)
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 1, "test")
	var a2: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 1}], 1)
	var a3: Dictionary = Game.crafting.with_aged(c, [{"item": "riverreed_ginseng_10", "count": 3}], 1)
	check(a1.inputs == [{"item": "riverreed_ginseng_100", "count": 1}] and int(a1.tiers) == 1, "a hundred-year root stands in for a ten-year one")
	check(a2.inputs == [{"item": "riverreed_ginseng_10", "count": 1}] and int(a2.tiers) == 0, "never while a ten-year root is to hand")
	check(a3.inputs == [{"item": "riverreed_ginseng_10", "count": 3}], "still short: the check asks for the recipe's own herb (%s)" % str(a3.inputs))
	Clock.override_utc = -1.0
	c.professions["herb_gathering"] = prof_was
	if had_conceal and not cu.secret_arts.has("concealment"): cu.secret_arts.append("concealment")
	if not had_conceal: cu.secret_arts.erase("concealment")

# ------------------------------------------------------------------ S45 garden beds, soil, water, dew, transplanting
func garden_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	Unlocks.force_unlock(c.id, "herb_garden")
	Unlocks.force_unlock(c.id, "herb_gathering")
	var now := 1950000000.0
	Clock.override_utc = now
	Game.world.load_room(c, "ja_herb_terraces", "")
	var bed := "ja_herb_terraces:bed_0"
	var garden_was: Dictionary = Game.crafting.beds(c).duplicate(true)
	Game.crafting.beds(c).clear()
	for id in ["willow_moss_seed", "cloudtop_orchid_seed", "spring_water", "spirit_soil"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "willow_moss_seed", 2, "test")
	Game.inventory.apply_add(c.id, "cloudtop_orchid_seed", 1, "test")
	# Soil caps the grade: a Low bed grows up to Earth; an orchid (Heaven) needs Spirit Soil first.
	var poor := Game.submit({"type": "plant_seed", "bed": bed, "seed": "cloudtop_orchid_seed"})
	check(not poor.get("ok", false) and str(poor.get("reason", "")) == "soil" and Game.crafting.bed_grade(c, bed) == "low", "a Low bed cannot grow a Heaven-grade orchid")
	Game.inventory.apply_add(c.id, "spirit_soil", 1, "test")
	check(Game.submit({"type": "apply_spirit_soil", "bed": bed}).get("ok", false) and Game.crafting.bed_grade(c, bed) == "mid", "Spirit Soil raises the bed to Mid, for good")
	check(Game.submit({"type": "plant_seed", "bed": bed, "seed": "cloudtop_orchid_seed"}).get("ok", false) and c.inventory.count("cloudtop_orchid_seed") == 0,
		"now the orchid takes")
	# Spring water: three bottles a day at a Qi spring, each +25% growth.
	var spring: Dictionary = {}
	for o in ContentDB.room("ja_elder_hu_peak").get("objects", []):
		if str(o.type) == "qi_spring": spring = o
	Unlocks.force_unlock(c.id, "qi_springs")
	var bottled := 0
	for i in 4:
		if Game.crafting.bottle_spring_water(c).get("ok", false): bottled += 1
	check(bottled == 3 and c.inventory.count("spring_water") == 3, "a spring gives three bottles a day (%d)" % bottled)
	Clock.override_utc = now + 86400.0
	check(Game.crafting.bottle_spring_water(c).get("ok", false), "and three more the next day")
	Clock.override_utc = now
	Game.crafting.settle_bed(c, bed)
	check(Game.submit({"type": "water_bed", "bed": bed}).get("ok", false) and near(float(Game.crafting.bed_view(c, bed).progress), 0.25, 0.001), "watering: +25% growth")
	# It grows on the clock, offline too: 8 hours for an orchid, the watered quarter already done.
	Clock.override_utc = now + 6.0 * 3600.0 - 60.0
	check(not Game.crafting.bed_view(c, bed).ready, "not yet at six hours less a minute")
	Clock.override_utc = now + 6.0 * 3600.0 + 1.0
	check(Game.crafting.bed_view(c, bed).ready, "ready after six hours (a quarter watered off eight)")
	var hv := Game.submit({"type": "harvest_bed", "bed": bed})
	check(hv.get("ok", false) and str(hv.get("item", "")) == "cloudtop_orchid" and int(hv.get("count", 0)) >= 2 and str(Game.crafting.bed_view(c, bed).herb) == "",
		"harvest: the orchids, and the bed is free (%s)" % str(hv))
	# The Verdant Dew Vial: a drop a day, offline too, three at most; a drop ages the herb one tier, to 1,000 years.
	Game.inventory.apply_add(c.id, "verdant_dew_vial", 1, "test")
	c.crafting["dew"] = {"count": 0, "last": 0.0}
	check(int(Game.crafting.dew_state(c).dew) == 0, "a new vial starts dry")
	Clock.override_utc = now + 6.0 * 3600.0 + 2.0 * 86400.0 + 10.0
	check(int(Game.crafting.dew_state(c).dew) == 2, "two days away: two drops")
	Clock.override_utc = now + 30.0 * 86400.0
	check(int(Game.crafting.dew_state(c).dew) == 3, "a month away: still three, the vial is full")
	Game.inventory.apply_add(c.id, "riverreed_ginseng_seed", 1, "test")
	Game.submit({"type": "plant_seed", "bed": bed, "seed": "riverreed_ginseng_seed"})
	var d1 := Game.submit({"type": "use_dew", "bed": bed})
	var d2 := Game.submit({"type": "use_dew", "bed": bed})
	var d3 := Game.submit({"type": "use_dew", "bed": bed})
	check(str(d1.get("herb", "")) == "riverreed_ginseng_100" and str(d2.get("herb", "")) == "riverreed_ginseng_1000" and not d3.get("ok", true)
		and int(Game.crafting.dew_state(c).dew) == 1, "dew ages the root to a hundred, then a thousand years, and no further in the valley")
	Game.crafting.beds(c).clear()
	Game.crafting.bed_record(c, bed).soil = 1
	# Transplanting: a Spirit Spade and Expert gathering; 25% it dies at Expert, 20% at Master.
	c.professions["herb_gathering"] = {"rank": "expert", "xp": 5000.0}
	check(not Game.crafting.can_transplant(c), "no spade, no transplant")
	Game.inventory.apply_add(c.id, "spirit_spade", 1, "test")
	check(Game.crafting.can_transplant(c) and near(Game.crafting.transplant_death(c), 0.25), "with a spade at Expert: 25% it dies")
	c.professions["herb_gathering"] = {"rank": "master", "xp": 20000.0}
	check(near(Game.crafting.transplant_death(c), 0.20), "at Master: 20%")
	c.professions["herb_gathering"] = {"rank": "expert", "xp": 5000.0}
	Game.world.load_room(c, "cf_falls_pool", "")
	var lotus: Dictionary = Game.room_rt.object_def("rare_lotus_fp")
	var L := HerbRules.day_s()
	Clock.override_utc = float(30000 * 3 + int(lotus.ripen.offset)) * L + 0.75 * L
	var st: ActorState = Game.actor_state(c.id)
	st.plane = Vector2(float(lotus.at[0]) - 30.0, float(lotus.at[1]))
	st.altitude = float(lotus.alt)
	var prompt := Game.submit({"type": "interact", "object": "rare_lotus_fp"})
	check(prompt.has("dialogue") and (prompt.dialogue.choices as Array).size() == 3, "with a spade, a rare herb asks: pick it or dig it up")
	var rng := Rng.stream(c.id, "garden")
	var rng_was := rng.state
	rng.seed = 777
	var lived := 0
	for i in 100:
		Game.room_rt.objects["rare_lotus_fp"] = {"state": "ready", "timer": 0.0, "hits": 0}
		Game.crafting.bed_record(c, bed).herb = ""
		var tr := Game.submit({"type": "transplant", "object": "rare_lotus_fp"})
		if tr.get("survived", false): lived += 1
	rng.state = rng_was
	check(lived >= 62 and lived <= 88, "three in four transplants live at Expert (%d of 100)" % lived)
	check(str(Game.crafting.bed_view(c, bed).herb) == "mist_lotus_100" or lived < 100, "a transplanted lotus keeps its hundred years in the bed")
	# Spirit Soil drops from strong beasts, on its own stream.
	var soil: Dictionary = ContentDB.config("garden").spirit_soil
	check(near(float(soil.chance), 0.01) and int(soil.min_level) == 19 and ContentDB.entry("loot_tables", "abbots_vault").guaranteed.any(func(g): return str(g.item) == "spirit_soil"),
		"Spirit Soil: 1% from rank 3+ beasts, and one in the Abbot's vault")
	Clock.override_utc = -1.0
	c.crafting["garden"] = garden_was
	for id in ["spirit_spade", "verdant_dew_vial"]: Game.inventory.apply_remove(c.id, id, 1, "test")

# ------------------------------------------------------------------ S45 racks, fakes and garden raids
func herb_prep_suite() -> void:
	var c = Game.active()
	if c == null: return
	Unlocks.force_unlock(c.id, "herb_garden")
	Unlocks.force_unlock(c.id, "appraisal")
	var now := 1960000000.0
	Clock.override_utc = now
	for id in ["mist_lotus", "riverreed_ginseng_10", "riverreed_ginseng_100", "willow_moss", "rice_wine", "dyed_root"]:
		Game.inventory.apply_remove(c.id, id, c.inventory.count(id), "test")
	Game.inventory.apply_add(c.id, "drying_rack", 1, "test")
	c.crafting["racks"] = []
	# Racks: steaming takes an hour; the herbs come back marked.
	Game.inventory.apply_add(c.id, "mist_lotus", 5, "test")
	var sr := Game.submit({"type": "start_rack", "kind": "steamed", "herb": "mist_lotus", "count": 5})
	check(sr.get("ok", false) and c.inventory.count("mist_lotus") == 0 and Game.crafting.racks(c).size() == 1, "five lotus go on the steaming rack")
	check(not Game.submit({"type": "collect_racks"}).get("ok", false), "nothing to take off before the hour")
	Clock.override_utc = now + 3601.0
	check(Game.submit({"type": "collect_racks"}).get("ok", false) and Game.inventory.count_prep(c, "mist_lotus", "steamed") == 5, "an hour later: five steamed lotus")
	# Wine-soaking wants a jar of rice wine for every five herbs, and four hours.
	Game.inventory.apply_add(c.id, "riverreed_ginseng_10", 3, "test")
	check(str(Game.submit({"type": "start_rack", "kind": "wine", "herb": "riverreed_ginseng_10", "count": 3}).get("reason", "")) == "needs", "no rice wine, no soaking")
	Game.inventory.apply_add(c.id, "rice_wine", 1, "test")
	check(Game.submit({"type": "start_rack", "kind": "wine", "herb": "riverreed_ginseng_10", "count": 3}).get("ok", false) and c.inventory.count("rice_wine") == 0,
		"a jar of rice wine soaks three roots")
	Clock.override_utc = now + 3601.0 + 4.0 * 3600.0
	Game.submit({"type": "collect_racks"})
	check(Game.inventory.count_prep(c, "riverreed_ginseng_10", "wine") == 3, "four hours later: three wine-soaked roots")
	# A pill takes the prep of its principal herb when all of it was prepared.
	Game.inventory.apply_add(c.id, "willow_moss", 2, "test")
	var used: Dictionary = Game.crafting._consume(c, "healing_pill", [{"item": "riverreed_ginseng_10", "count": 1}, {"item": "willow_moss", "count": 2}], "riverreed_ginseng_10")
	check(str(used.prep) == "wine" and Game.inventory.count_prep(c, "riverreed_ginseng_10", "wine") == 2 and not used.fake, "a healing pill from a wine-soaked root is wine-soaked")
	check(near(InventoryAuthority.pill_potency({"id": "healing_pill", "prep": "wine"}), 1.1) and near(InventoryAuthority.pill_toxicity_mult({"id": "healing_pill", "prep": "steamed"}), 0.7),
		"wine-soaked: +10% potency; steamed: -30% toxicity")
	# Sealed herbs: some are fakes, each in its own slot until appraised; a fake in a recipe risks a Flawed pill.
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": true, "seal": c.inventory.next_uid})
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": false, "seal": c.inventory.next_uid})
	var sealed: Array = []
	for i in c.inventory.bag.size():
		var st = c.inventory.bag[i]
		if st != null and str(st.id) == "riverreed_ginseng_100": sealed.append(i)
	check(sealed.size() == 2 and Game.inventory.count_prep(c, "riverreed_ginseng_100", "") == 0, "two sealed roots, one slot each, not counted as appraised")
	var fake_i := -1
	for i in sealed:
		if c.inventory.bag[i].get("fake", false): fake_i = int(i)
	var had_loupe: bool = Game.crafting.tool_power(c, "appraisal") > 0.0
	var had_eye: bool = c.cultivator.secret_arts.has("appraisal_eye")
	Game.inventory.apply_remove(c.id, "appraisers_loupe", 1, "test")
	c.cultivator.secret_arts.erase("appraisal_eye")
	check(not Game.submit({"type": "appraise_item", "index": fake_i}).get("ok", false), "no loupe, no appraisal")
	Game.inventory.apply_add(c.id, "appraisers_loupe", 1, "test")
	if had_eye: c.cultivator.secret_arts.append("appraisal_eye")
	var ap := Game.submit({"type": "appraise_item", "index": fake_i})
	check(ap.get("ok", false) and ap.get("fake", false) and c.inventory.count("dyed_root") == 1 and c.inventory.count("riverreed_ginseng_100") == 1,
		"appraisal shows the fake: a dyed root")
	var used2: Dictionary = Game.crafting._consume(c, "cleansing_pill", [{"item": "riverreed_ginseng_100", "count": 1}], "mist_lotus")
	check(not used2.fake, "the genuine sealed root is no fake")
	if not had_loupe: Game.inventory.apply_remove(c.id, "appraisers_loupe", 1, "test")
	c.inventory.next_uid += 1
	Game.inventory.apply_add(c.id, "riverreed_ginseng_100", 1, "test", {"unappraised": true, "fake": true, "seal": c.inventory.next_uid})
	check(Game.crafting._consume(c, "cleansing_pill", [{"item": "riverreed_ginseng_100", "count": 1}], "mist_lotus").fake, "an unappraised fake goes into the furnace unseen")
	# Garden raids: an unguarded bed can be hit while you are away; a Protection formation keeps it safe.
	var bed := "ja_herb_terraces:bed_1"
	var garden_was: Dictionary = Game.crafting.beds(c).duplicate(true)
	var forms_was = c.crafting.get("formations", []).duplicate(true)
	c.crafting["formations"] = []
	var raids: Dictionary = ContentDB.config("garden").raids
	var chance_was := float(raids.chance)
	raids.chance = 1.0
	var rec: Dictionary = Game.crafting.bed_record(c, bed)
	rec.herb = "willow_moss"
	rec.progress = 0.5
	rec.updated = Clock.now_utc()
	rec.raid_day = Clock.reset_day(Clock.now_utc()) - 3
	var mails_before: int = c.mail.size() if c.get("mail") is Array else 0
	var hit: Array = Game.crafting.check_raids(c)
	check(hit.size() >= 1 and (str(rec.herb) == "" or float(rec.progress) < 0.5), "an unguarded bed is raided while you are away (%s)" % str(hit))
	rec.herb = "willow_moss"
	rec.progress = 0.5
	rec.raid_day = Clock.reset_day(Clock.now_utc()) - 3
	c.crafting.formations = [{"type": "protection", "room": "ja_herb_terraces", "until_utc": Clock.now_utc() + 86400.0}]
	check(Game.crafting.check_raids(c).is_empty() and str(rec.herb) == "willow_moss" and near(float(rec.progress), 0.5), "a Protection formation keeps the raiders off")
	raids.chance = chance_was
	c.crafting["formations"] = forms_was
	c.crafting["garden"] = garden_was
	Clock.override_utc = -1.0

# ------------------------------------------------------------------ S46 beasts: bloodline, ranks, cores, wounds, taming
func beasts_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "taming")
	# A new animal's bloodline: purity by rarity, hidden growth and aptitude.
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	var g: Dictionary = ContentDB.config("pet_growth")
	check(int(fox.purity) >= 5 and int(fox.purity) <= 15 and float(fox.growth) >= 0.8 and float(fox.growth) <= 1.3
		and float(fox.aptitude.attack) >= 0.8 and float(fox.aptitude.attack) <= 1.2 and str(fox.contract) == "master", "a Common fox: purity 5-15, growth and aptitude rolled, a master's contract")
	check(not Game.pets.aptitude_known(fox), "growth and aptitude stay hidden in a Hatchling")
	fox.stage = "juvenile"
	check(Game.pets.aptitude_known(fox), "a Juvenile shows them")
	var legacy := {"uid": "old_1", "species": "reed_otter", "rarity": "rare"}
	Game.pets.ensure_fields(legacy)
	check(int(legacy.purity) == 38 and near(float(legacy.growth), 1.0) and legacy.learned_skills == [] and not legacy.locked, "an animal from an older save gets neutral fields")
	# Beast rank and nature (Part 8): rank from the Level band, ghosts and constructs have none.
	var crab := ContentDB.entry("enemies", "tide_crab")
	check(int(crab.beast_rank) == 3 and str(crab.nature) == "spirit" and WorldAuthority.beast_rank(crab, 22) == 3 and WorldAuthority.beast_rank(crab, 73) == 9,
		"a Tide Crab is a rank 3 spirit beast")
	check(str(ContentDB.entry("enemies", "mud_hound").nature) == "demonic" and str(ContentDB.entry("enemies", "hollow_stag").nature) == "hollowed"
		and str(ContentDB.entry("enemies", "mirror_wisp").race) == "ghost" and not ContentDB.entry("enemies", "jade_sentinel").has("beast_rank"),
		"natures: demonic and Hollowed; ghosts and constructs are no beasts")
	# Cores: rank 2 and up at 2% a rank, by element and tier.
	check(WorldAuthority.beast_core_for(crab, 22) == "water_core_low" and near(WorldAuthority.core_chance(crab, 22), 0.06)
		and WorldAuthority.beast_core_for(ContentDB.entry("enemies", "reedtail_rat"), 2) == "" and WorldAuthority.beast_core_for(ContentDB.entry("enemies", "mirror_wisp"), 49) == "",
		"a rank 3 crab carries a Low Water Core 6% of the time; rank 1 beasts and ghosts carry none")
	# Devouring: only its own element.
	Game.inventory.apply_add(c.id, "fire_core_low", 2, "test")
	Game.inventory.apply_add(c.id, "water_core_low", 1, "test")
	var xp0 := float(fox.xp) + 20.0 * pow(int(fox.level), 1.5) * 0.0
	var lv0 := int(fox.level)
	check(Game.submit({"type": "devour_core", "pet": fox.uid, "item": "fire_core_low"}).get("ok", false) and (int(fox.level) > lv0 or float(fox.xp) > xp0),
		"the fox devours a fire core and grows")
	check(str(Game.submit({"type": "devour_core", "pet": fox.uid, "item": "water_core_low"}).get("reason", "")) == "wrong_element", "but will not touch a water core")
	# The Core Exchange at the Beast Hall: fixed stones by tier, 60 a day.
	check(str(Game.submit({"type": "sell_cores", "item": "fire_core_low", "count": 1}).get("reason", "")) == "not_here", "the Exchange is at the Beast Hall")
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	c.crafting.erase("core_exchange")
	Game.inventory.apply_add(c.id, "earth_core_peak", 5, "test")
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var sold := Game.submit({"type": "sell_cores", "item": "earth_core_peak", "count": 5})
	check(sold.get("ok", false) and int(sold.count) == 3 and int(Game.account.currencies.get("spirit_stone", 0)) - stones0 == 60 and Game.pets.exchange_left(c) == 0,
		"peak cores at 20 stones: three a day fill the cap of 60 (%s)" % str(sold))
	# Grievous Wound: three knockouts in five minutes; the Beast Revival Pill mends it.
	c.active_pet = str(fox.uid)
	var hp0: float = Game.pets.stat_mult(fox, "hp")
	for i in 3: Game.pets._knocked_out(c, fox)
	GameEvents.flush()
	check(fox.wounded and near(Game.pets.stat_mult(fox, "hp"), hp0 * 0.8, 0.001), "three knockouts in five minutes: a Grievous Wound, -20%")
	Game.inventory.apply_add(c.id, "beast_revival_pill", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "beast_revival_pill"), "confirm": true})
	check(not fox.wounded, "a Beast Revival Pill mends it")
	fox.knockouts = []
	Game.pets._knocked_out(c, fox)
	Game.pets._knocked_out(c, fox)
	Game.sim_time += 400.0
	Game.pets._knocked_out(c, fox)
	check(not fox.wounded, "three knockouts spread over more than five minutes do not")
	# Taming by nature: a demonic hound takes only a Purifying Offering; a Hollowed boarlet must be cleansed first.
	var st: ActorState = Game.actor_state(c.id)
	var hound: EnemyState = Game.enemies.spawn_at("mud_hound", st.plane + Vector2(60, 0), 18)
	hound.pools.hp = hound.pools.max_hp * 0.1
	Game.inventory.apply_add(c.id, "bonding_offering_common", 3, "test")
	Game.inventory.apply_add(c.id, "purifying_offering", 3, "test")
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "demonic", "a Bonding Offering does nothing for a demonic hound")
	var tp := Game.submit({"type": "attempt_tame", "offering": "purifying_offering"})
	check(tp.get("ok", false) and str(tp.get("species", "")) == "mud_hound", "a Purifying Offering can tame it")
	var boar: EnemyState = Game.enemies.spawn_at("hollowed_boarlet", st.plane + Vector2(60, 0), 10)
	boar.pools.hp = boar.pools.max_hp * 0.1
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "hollowed", "a Hollowed boarlet cannot be tamed as it is")
	check(Game.submit({"type": "attempt_tame", "offering": "purifying_offering"}).get("cleansed", false) and boar.ai.get("cleansed", false), "the Purifying Offering cleanses it")
	var tb := Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"})
	check(tb.get("ok", false) and not tb.has("cleansed") and str(tb.get("species", "")) == "cleansed_boarlet", "then any offering can tame it")
	# The taming fix: struck down with an offering on quick-use, a tameable beast stays subdued at 1 HP.
	var otter: EnemyState = Game.enemies.spawn_at("reed_otter", st.plane + Vector2(60, 0), 20)
	c.inventory.quick_use = "bonding_offering_common"
	Game.combat._damage_enemy(otter, otter.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	check(otter.alive and near(otter.pools.hp, 1.0) and otter.ai.get("subdued_once", false), "a one-hit otter is subdued at 1 HP, not killed")
	Game.combat._damage_enemy(otter, 10.0, c.id, "physical", "none", false, {})
	check(not otter.alive, "only once: the next blow lands")
	c.inventory.quick_use = ""
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	c.pets = pets_was
	c.active_pet = active_was

## S46 · bloodline awakenings, suppression, contracts, command capacity, incubation input and beast medicine.
func bloodline_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var party_was: Array = c.party_pets.duplicate()
	var eggs_was: Array = c.eggs.duplicate(true)
	var realm_was: String = c.cultivator.realm_key
	var fates_was: Array = c.cultivator.fates.duplicate(true)
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	c.quests.flags.erase("equal_contract")
	c.cooldowns.erase("essence_blood")
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "spirit_eggs")
	Game.world.load_room(c, "lf_reed_shallows", "")
	var heard := {}
	GameEvents.event.connect(func(n, p): heard[n] = p)
	# Purity thresholds: 49 and 50, 89 and 90.
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(fox.uid)
	fox.purity = 48
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.purity) == 49 and int(fox.get("awakened", 0)) == 0 and Game.pets.bloodline_skill(fox).is_empty(), "purity 49: no awakening yet")
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.awakened) == 1 and str(Game.pets.bloodline_skill(fox).get("name", "")) == "Nine-Tail Flame" and int(heard.get("bloodline_awakened", {}).get("step", 0)) == 1,
		"purity 50: the Nine-Tail Flame awakens")
	var m89 := Game.pets.stat_mult(fox, "attack")
	fox.purity = 88
	Game.pets.add_purity(c, fox, 1)
	check(int(fox.awakened) == 1 and Game.pets.form_of(fox).is_empty(), "purity 89: still its first form")
	Game.pets.add_purity(c, fox, 1)
	GameEvents.flush()
	check(int(fox.awakened) == 2 and str(Game.pets.form_of(fox).get("name", "")) == "Nine-Tail Fox" and near(Game.pets.stat_mult(fox, "attack"), m89 * 1.1, 0.001),
		"purity 90: the Nine-Tail Fox, +10% to every stat")
	check(int(heard.get("bloodline_awakened", {}).get("step", 0)) == 2, "each awakening is announced once")
	Game.pets.add_purity(c, fox, 50)
	check(int(fox.purity) == 100, "purity stops at 100")
	# Trait strength: +0.2% a point of purity.
	fox.traits = ["stormborn", "quick_paws", "loyal"]
	fox.revealed = 1
	fox.purity = 0
	var t0 := Game.pets._trait_sum(fox, "pet_damage")
	fox.purity = 100
	check(near(t0, 0.15) and near(Game.pets._trait_sum(fox, "pet_damage"), 0.15 * 1.2), "a pure bloodline strengthens its traits by 20%")
	# Suppression (the Pressure contest): an Epic, awakened fox cows a rank 1 rat, not a rank 9 boss.
	check(near(CombatRules.pressure_loss(2.0, 1.0), 0.25) and near(CombatRules.pressure_loss(1.0, 2.0), 0.0) and near(CombatRules.pressure_loss(9.0, 1.0), 0.5),
		"Pressure over Will: min(50%, 25% x (P/W - 1))")
	fox.rarity = "epic"
	var st: ActorState = Game.actor_state(c.id)
	var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", st.plane + Vector2(80, 0), 2)
	check(Game.pets.bloodline_tier(fox) == 6 and Game.pets.beast_tier(rat) == 1 and Game.pets.suppresses(fox, rat), "an Epic fox with both awakenings (tier 6) outranks a rank 1 rat (tier 1)")
	fox.rarity = "common"
	fox.awakened = 0
	check(not Game.pets.suppresses(fox, rat), "a Common fox (tier 1) does not")
	Unlocks.force_unlock(c.id, "taming")
	rat.pools.hp = rat.pools.max_hp * 0.1
	var plain := Game.pets.tame_chance(c, rat, "bonding_offering_common", 0.5)
	fox.rarity = "epic"
	fox.awakened = 2
	check(near(Game.pets.tame_chance(c, rat, "bonding_offering_common", 0.5), minf(plain + 0.1, float(ContentDB.config("taming").get("max", 0.95)))),
		"suppression adds +10% to the taming chance")
	Game.pets._spawn(c)
	var ally: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(ally != null and float(ally.def.art.get("scale", 1.0)) > 1.0, "the true form stands larger")
	if ally != null:
		ally.plane = rat.plane + Vector2(-40, 0)
		ally.ai.sup_t = 0.0
		Game.pets._suppress(c, fox, ally, 0.1)
		GameEvents.flush()
		check(rat.ai.get("suppressed", false) and rat.pools.has_status("fear") and heard.has("beast_suppressed"), "and its blood grips the rat with Fear")
	Game.enemies.release(rat)
	# Skill casts: the awakened skill hits x2.5 every 12 s.
	if ally != null:
		ally.ai.state = "windup"
		ally.ai.timer = 0.01
		ally.ai.skill_cd = 0.0
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 2.5) and float(ally.ai.skill_cd) > 11.0, "the bloodline skill lands at x2.5, then rests 12 s")
		ally.ai.timer = 0.01
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 1.0), "not again while it rests")
	# Contracts: Equal at 10 hearts, once per character; Blood with essence blood.
	fox.bond = 9.0
	check(str(Game.submit({"type": "offer_contract", "pet": fox.uid, "kind": "equal"}).get("reason", "")) == "hearts", "no Equal Contract at 9 hearts")
	heard.erase("contract_offered")
	Game.pets.apply_bond(c.id, 1.0, str(fox.uid))
	GameEvents.flush()
	check(heard.has("contract_offered"), "at 10 hearts the fox offers one")
	check(Game.submit({"type": "offer_contract", "pet": fox.uid, "kind": "equal"}).get("ok", false) and str(fox.contract) == "equal", "an Equal Contract is formed")
	if ally != null:
		ally = Game.room_rt.enemies.get(Game.pets.ally_uid)
		ally.ai.state = "windup"
		ally.ai.timer = 0.01
		ally.ai.skill_cd = 5.0
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 2.5) and not ally.ai.free_cast, "Equal: one free skill cast in a fight")
		ally.ai.timer = 0.01
		check(near(Game.pets._skill_mult(c, fox, ally, 0.02), 1.0), "only one")
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets[c.pets.size() - 1]
	otter.bond = 10.0
	check(str(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "equal"}).get("reason", "")) == "once", "one Equal Contract per character, ever")
	check(str(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "blood"}).get("reason", "")) == "no_blood", "a Blood Contract needs essence blood")
	Game.inventory.apply_add(c.id, "beast_essence_blood", 3, "test")
	var om := Game.pets.stat_mult(otter, "hp")
	check(Game.submit({"type": "offer_contract", "pet": otter.uid, "kind": "blood"}).get("ok", false) and near(Game.pets.stat_mult(otter, "hp"), om * 1.15, 0.001)
		and c.inventory.count("beast_essence_blood") == 2, "a Blood Contract: +15% stats for a drop of essence blood")
	# Command capacity by realm, and the party beside you (called somewhere safe: the field needs the Beast Bag).
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	c.cultivator.realm_key = "heart_tempering_9"
	check(Game.pets.command_capacity(c) == 1, "one animal at a time before Spirit Awakening")
	check(str(Game.submit({"type": "set_party", "pet": otter.uid, "on": true}).get("reason", "")) == "capacity", "a second must wait")
	c.cultivator.realm_key = "spirit_awakening_1"
	check(Game.pets.command_capacity(c) == 2, "two from Spirit Awakening")
	check(Game.submit({"type": "set_party", "pet": otter.uid, "on": true}).get("ok", false) and Game.pets.allies.size() == 2 and Game.pets.party(c).size() == 2,
		"the otter walks beside the fox")
	c.cultivator.realm_key = "sage_1"
	check(Game.pets.command_capacity(c) == 3, "three from Sage")
	# A Blood-bound animal knocked out bruises its owner's soul.
	var inj0 := int(c.cultivator.injuries.get("soul", {}).get("severity", 0))
	var oa: EnemyState = Game.room_rt.enemies.get(int(Game.pets.allies.get(str(otter.uid), 0)))
	if oa != null: Game.pets.apply_retreat(oa)
	check(oa != null and int(c.cultivator.injuries.get("soul", {}).get("severity", 0)) == inj0 + 1, "the otter's knockout gives a soul injury")
	c.cultivator.injuries.erase("soul")
	Game.submit({"type": "set_party", "pet": otter.uid, "on": false})
	check(c.party_pets.is_empty() and Game.pets.allies.size() == 1, "sent home again")
	# Resonance flows both ways under an Equal Contract.
	fox.role = "combat"
	fox.stage = "adult"
	check(Game.pets.resonance(c) > 0.0, "an Equal animal resonates whatever its role")
	var xp0 := float(fox.xp)
	var lv0 := int(fox.level)
	GameEvents.emit_event("meditation_tick", {"actor": c.id})
	GameEvents.flush()
	check(float(fox.xp) > xp0 or int(fox.level) > lv0, "and your meditation feeds it")
	# Incubation input.
	c.eggs = [{"species": "reed_otter", "hatch_utc": Clock.now_utc() - 1.0}]
	var hp_before: float = c.pools.max_hp
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "blood"}).get("ok", false) and near(c.pools.max_hp, hp_before * 0.9, hp_before * 0.02)
		and float(c.cooldowns.get("essence_blood", 0.0)) > Clock.now_utc() + 23.0 * 3600.0, "your essence blood: -10% max HP for 24 h")
	check(str(Game.submit({"type": "incubate_input", "egg": 0, "kind": "blood"}).get("reason", "")) == "already", "once per egg")
	Game.inventory.apply_add(c.id, "earth_core_low", 1, "test")
	check(str(Game.submit({"type": "incubate_input", "egg": 0, "kind": "element", "item": "earth_core_low"}).get("reason", "")) == "no_element", "no egg of earth answers an earth core")
	Game.inventory.apply_add(c.id, "fire_core_low", 1, "test")
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "element", "item": "fire_core_low"}).get("ok", false) and str(c.eggs[0].species) == "ember_fox",
		"a fire core steers the egg to fire")
	check(Game.submit({"type": "incubate_input", "egg": 0, "kind": "reroll"}).get("ok", false) and (c.eggs[0].traits as Array).size() == 3, "essence blood rerolls a hidden trait")
	c.cultivator.fates.append({"id": "fox_spirits_favour", "realm": "sage", "next": {"egg_purity": 10}})
	var n0: int = c.pets.size()
	Game.submit({"type": "hatch_egg", "index": 0})
	var chick: Dictionary = c.pets[c.pets.size() - 1] if c.pets.size() > n0 else {}
	check(not chick.is_empty() and near(float(chick.bond), 3.0) and int(chick.purity) >= 25 and str(chick.species) == "ember_fox",
		"a self-warmed hatchling starts at 3 hearts with +10 purity and Fox Spirit's Favour's +10 (%s)" % str(chick.get("purity", "")))
	check(ProgressionRules.fate_pool(Game.ctx(c)).any(func(f): return str(f.id) == "fox_spirits_favour"), "Fox Spirit's Favour is in the deck once eggs are open")
	c.cooldowns["essence_blood"] = Clock.now_utc() - 1.0
	Game.pets.essence_check = 0.0
	Game.pets.tick(0.1)
	check(not c.cooldowns.has("essence_blood") and near(c.pools.max_hp, hp_before, hp_before * 0.02), "a day later your blood has recovered")
	# Beast medicine: essence blood lifts purity; the marrow pill needs a Juvenile and leaves no toxicity.
	c.active_pet = str(chick.uid)
	var pu0 := int(chick.purity)
	Game.submit({"type": "use_item", "index": _bag_index(c, "beast_essence_blood"), "confirm": true})
	check(int(chick.purity) == mini(100, pu0 + 10), "Beast Essence Blood: +10 purity")
	Game.inventory.apply_add(c.id, "beast_marrow_washing_pill", 2, "test")
	check(str(Game.submit({"type": "use_item", "index": _bag_index(c, "beast_marrow_washing_pill"), "confirm": true}).get("reason", "")) == "too_young"
		and c.inventory.count("beast_marrow_washing_pill") == 2, "the marrow pill waits for a Juvenile, and is not spent")
	chick.stage = "juvenile"
	chick.aptitude = {"hp": 1.1, "attack": 0.8, "defence": 1.0, "speed": 1.2}
	var tox0: float = c.cultivator.toxicity
	check(Game.submit({"type": "use_item", "index": _bag_index(c, "beast_marrow_washing_pill"), "confirm": true}).get("ok", false)
		and near(float(chick.aptitude.hp), 1.1) and near(float(chick.aptitude.speed), 1.2) and near(c.cultivator.toxicity, tox0), "it rolls only the weakest gift again, with no toxicity")
	c.pets = pets_was
	c.active_pet = active_was
	c.party_pets = party_was
	c.eggs = eggs_was
	c.cultivator.realm_key = realm_was
	c.cultivator.fates = fates_was
	c.quests.flags.erase("equal_contract")
	c.cooldowns.erase("essence_blood")
	Game.combat.refresh_stats(c.id)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · skill books, pet gear, fusion, pet breakthroughs and Pet Core Formation.
func pet_growth_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var party_was: Array = c.party_pets.duplicate()
	var realm_was: String = c.cultivator.realm_key
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cap0: int = c.inventory.capacity()
	Unlocks.force_unlock(c.id, "spirit_animals")
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "lf_reed_shallows", "")
	c.cultivator.realm_key = "sage_1"
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets[c.pets.size() - 1]
	c.active_pet = str(otter.uid)
	c.party_pets = []
	# Skill books: no slots as a Hatchling; a Juvenile has 2; when full a new book takes a random slot.
	Game.inventory.apply_add(c.id, "pet_book_iron_hide", 1, "test")
	check(str(Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_iron_hide"}).get("reason", "")) == "cannot_learn"
		and c.inventory.count("pet_book_iron_hide") == 1, "a Hatchling cannot learn, and the book is kept")
	otter.stage = "juvenile"
	check(Game.pets.skill_slots(otter) == 2 and Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_iron_hide"}).get("ok", false)
		and Game.pets.has_skill(otter, "iron_hide"), "a Juvenile learns Iron Hide into its first slot")
	Game.inventory.apply_add(c.id, "pet_book_deep_pockets", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "pet_book_deep_pockets"), "confirm": true})
	check(Game.pets.has_skill(otter, "deep_pockets") and (otter.learned_skills as Array).size() == 2, "a book used from the gourd teaches the active animal")
	check(c.inventory.capacity() == cap0 + 6, "Deep Pockets: one more row in the gourd while it is active (%d)" % c.inventory.capacity())
	Game.inventory.apply_add(c.id, "pet_book_frenzy", 2, "test")
	var rng: RandomNumberGenerator = Rng.stream(c.id, "pet")
	var st0 := rng.state
	var learned0: Array = (otter.learned_skills as Array).duplicate()
	var r1 := Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_frenzy"})
	var after1: Array = (otter.learned_skills as Array).duplicate()
	check(r1.get("ok", false) and after1.size() == 2 and after1.has("frenzy") and learned0.has(str(r1.get("replaced", ""))), "slots full: Frenzy overwrites a random slot (%s)" % str(r1.get("replaced", "")))
	otter.learned_skills = learned0.duplicate()
	rng.state = st0
	Game.submit({"type": "learn_skill_book", "pet": otter.uid, "book": "pet_book_frenzy"})
	check(otter.learned_skills == after1, "under the same seed the same slot is overwritten")
	otter.learned_skills = ["iron_hide", "deep_pockets"]
	Game.pets._apply_pockets(c)
	# Iron Hide in combat; Herb Whisper beside you; Thunder Roar; Guardian Spirit; Frenzy after a kill.
	Game.pets._spawn(c)
	var ally: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(ally != null and near(Game.pets.damage_taken_mult(ally), 1.0 + Game.pets._trait_sum(otter, "pet_damage_taken") - 0.1), "Iron Hide: 10% less damage")
	check(Game.pets.whisper_range(c) == 0.0, "no Herb Whisper yet")
	otter.learned_skills = ["herb_whisper", "thunder_roar"]
	Game.pets._apply_pockets(c)
	check(c.inventory.capacity() == cap0 and near(Game.pets.whisper_range(c), 400.0), "Deep Pockets forgotten: the row goes; Herb Whisper reads herbs within 400")
	var st: ActorState = Game.actor_state(c.id)
	if ally != null:
		var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", ally.plane + Vector2(40, 0), 2)
		ally.ai.roar_cd = 0.0
		Game.pets._roar(c, otter, ally, 0.1)
		check(rat.pools.has_status("stun") and float(ally.ai.roar_cd) > 14.0, "Thunder Roar stuns a foe beside it, then rests 15 s")
		Game.enemies.release(rat)
		otter.learned_skills = ["guardian_spirit", "frenzy"]
		Game.pets.guardian_cd.erase(c.id)
		check(Game.pets.guardian_absorbs(c) and not Game.pets.guardian_absorbs(c), "Guardian Spirit takes one blow, then waits 30 s")
		Game.pets._on_actor_defeated({"victim_kind": "enemy", "level": 1})
		check(float(ally.ai.get("frenzy", 0.0)) > 5.0, "Frenzy: a kill quickens it for 6 s")
	# Pet gear: worn through the equip intent, +10% of base a level of enhancement; a saddle only on a mount.
	otter.learned_skills = []
	var hp0: float = Game.pets.stat_mult(otter, "hp")
	Game.inventory.apply_add_equipment(c.id, "bone_collar", 14, "common", "test")
	check(Game.submit({"type": "equip", "index": _bag_index(c, "bone_collar")}).get("ok", false) and otter.equipment.has("pet_collar")
		and near(Game.pets.stat_mult(otter, "hp"), hp0 * 1.1, 0.001), "a Bone Collar on the otter: +10% HP")
	otter.equipment.pet_collar.enhance = 2
	check(near(Game.pets.gear_bonus(otter, "hp"), 0.12), "enhanced +2: +12%")
	Game.inventory.apply_add_equipment(c.id, "reed_saddle", 14, "common", "test")
	check(str(Game.submit({"type": "equip_pet", "pet": otter.uid, "index": _bag_index(c, "reed_saddle")}).get("reason", "")) == "not_mountable", "a saddle only fits a mount")
	check(Game.submit({"type": "unequip_pet", "pet": otter.uid, "slot": "pet_collar"}).get("ok", false) and c.inventory.count("bone_collar") == 1, "taken off, back to the gourd")
	check(ContentDB.item("scale_talisman").has("pet_gear") and ContentDB.has_entry("recipes", "bone_collar"), "pet gear is forged")
	# Fusion: at the Beast Hall, never a locked animal, only when confirmed; half the purity gap carries over.
	Game.pets.apply_grant(c.id, "reed_otter")
	var spare: Dictionary = c.pets[c.pets.size() - 1]
	otter.purity = 20
	spare.purity = 60
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true}).get("reason", "")) == "cannot_fuse", "fusion only at the Beast Hall")
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	spare.locked = true
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true}).get("reason", "")) == "cannot_fuse", "a locked animal is never fused")
	spare.locked = false
	check(str(Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid}).get("reason", "")) == "confirm", "fusion asks for confirmation")
	var n0: int = c.pets.size()
	var fz := Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": spare.uid, "confirm": true})
	check(fz.get("ok", false) and c.pets.size() == n0 - 1 and int(otter.purity) == 40, "fused: the spare is gone and half its purity above the otter's carries over (%d)" % int(otter.purity))
	# Fusion odds: about 30% for each trait and learned skill.
	var tries := 0
	var hits := 0
	for i in 60:
		Game.pets.apply_grant(c.id, "mossback_toad")
		var b: Dictionary = c.pets[c.pets.size() - 1]
		b.traits = ["stormborn", "keen_nose", "lucky_find"]
		b.learned_skills = []
		otter.traits = ["deep_diver", "iron_hide", "loyal"]
		otter.revealed = 0
		var f2 := Game.submit({"type": "fuse_pets", "keep": otter.uid, "sacrifice": b.uid, "confirm": true})
		tries += 3
		hits += (f2.get("traits", []) as Array).size()
	var rate := float(hits) / float(tries)
	check(rate > 0.2 and rate < 0.4, "each trait carries over about 30%% of the time (%.2f over %d)" % [rate, tries])
	# Breakthroughs from Awakened on: evolve refuses, the breakthrough rolls; Core Formation grades the core.
	otter.stage = "adult"
	otter.level = 55
	otter.bond = 7.0
	otter.wounded = false
	check(str(Game.submit({"type": "evolve_pet", "pet": otter.uid}).get("reason", "")) == "breakthrough", "Adult to Awakened is a breakthrough, not a plain evolve")
	Game.inventory.apply_add(c.id, "water_core_mid", 1, "test")
	Game.inventory.apply_add(c.id, "beast_essence_blood", 1, "test")
	var base := Game.pets.breakthrough_chance(c, otter, [])
	check(near(Game.pets.breakthrough_chance(c, otter, ["water_core_mid", "beast_essence_blood"]), minf(0.95, base + 0.25)) and near(Game.pets.support_value(otter, "fire_core_mid"), 0.0),
		"a core of its own element and essence blood raise the chance; another element's core does not")
	var bcfg: Dictionary = ContentDB.config("pet_growth").breakthrough
	var base_was: float = float(bcfg.base)
	bcfg.base = 5.0
	var ok1 := Game.submit({"type": "pet_breakthrough", "pet": otter.uid, "support": ["water_core_mid"]})
	check(ok1.get("success", false) and str(otter.stage) == "awakened" and str(otter.get("core_grade", "")) != "" and c.inventory.count("water_core_mid") == 0,
		"a breakthrough: Awakened, a %s, the support spent" % str(otter.get("core_grade", "")))
	var cg: Dictionary = Game.pets.core_grade_def(str(otter.core_grade))
	check(near(Game.pets.core_bonus(otter), float(cg.get("bonus", 0.0))), "the core grade adds to every stat")
	bcfg.base = -5.0
	otter.level = 75
	otter.bond = 9.0
	c.cultivator.realm_key = "sphere_lord_1"
	var fb := Game.submit({"type": "pet_breakthrough", "pet": otter.uid, "support": []})
	check(not fb.get("success", true) and str(otter.stage) == "awakened" and (float(otter.bond) < 9.0 or otter.wounded), "a failure costs a heart or leaves a wound (%s)" % str(fb.get("lost", "")))
	bcfg.base = base_was
	c.pets = pets_was
	c.active_pet = active_was
	c.party_pets = party_was
	c.cultivator.realm_key = realm_was
	Game.pets._apply_pockets(c)
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · the Spirit Beast Bag and field swaps, the Mount slot and mount-only species, rarity rolls, Beast Kings and
## their nests, the Beast Tide, and pets that never die.
func beast_world_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var bag_was: Array = c.pet_bag.duplicate()
	var realm_was: String = c.cultivator.realm_key
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var timers_was: Dictionary = Game.account.rooms.get("field_boss_timers", {}).duplicate()
	var keys_was: Array = c.inventory.key_items.duplicate(true)
	Unlocks.force_unlock(c.id, "spirit_animals")
	Unlocks.force_unlock(c.id, "mounts")
	c.inventory.bag.fill(null)
	c.cultivator.realm_key = "cloud_stride_1"
	c.pets = []
	c.active_pet = ""
	c.pet_bag = []
	c.mount_pet = ""
	c.riding = false
	# Rarity rolls: a wild tame is mostly Common, an elite never is, a King's egg is Rare or finer.
	var counts := {}
	for i in 300:
		var r: String = Game.pets.roll_rarity(c, "tame")
		counts[r] = int(counts.get(r, 0)) + 1
	check(int(counts.get("common", 0)) > 150 and int(counts.get("common", 0)) < 270, "a wild tame is Common about 70%% of the time (%s)" % str(counts))
	var ok_elite := true
	var ok_rare := true
	for i in 60:
		if Game.pets.roll_rarity(c, "tame_elite") == "common": ok_elite = false
		if not Game.pets.roll_rarity(c, "rare") in ["rare", "epic", "primordial"]: ok_rare = false
	check(ok_elite and ok_rare, "an elite is never Common; a nest egg is Rare or better")
	Unlocks.force_unlock(c.id, "spirit_eggs")
	Game.inventory.apply_add(c.id, "cloud_stag_egg", 1, "test")
	Game.submit({"type": "use_item", "index": _bag_index(c, "cloud_stag_egg"), "confirm": true})
	check(not c.eggs.is_empty() and str(c.eggs.back().species) == "cloud_stag" and c.eggs.back().has("rarity"), "the Beast Tide's egg holds a Cloud Stag")
	c.eggs = []
	# The Spirit Beast Bag: carried animals, swapped in the field but never in a fight.
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	Game.pets.apply_grant(c.id, "ember_fox")
	var fox: Dictionary = c.pets.back()
	Game.pets.apply_grant(c.id, "reed_otter")
	var otter: Dictionary = c.pets.back()
	Game.pets.apply_grant(c.id, "mossback_toad")
	var toad: Dictionary = c.pets.back()
	c.active_pet = str(fox.uid)
	check(str(Game.submit({"type": "set_pet_bag", "pet": otter.uid, "on": true}).get("reason", "")) == "no_bag", "carrying needs a Spirit Beast Bag")
	Game.inventory.apply_add(c.id, "beast_bag_reed", 1, "test")
	Game.inventory.apply_add(c.id, "beast_bag_hide", 1, "test")
	check(Game.pets.bag_capacity(c) == 3, "the best bag counts: a Hide Beast Bag carries 3")
	check(Game.submit({"type": "set_pet_bag", "pet": otter.uid, "on": true}).get("ok", false) and c.pet_bag.has(str(otter.uid)), "pack the otter at the Beast Hall")
	Game.world.load_room(c, "lf_reed_shallows", "")
	check(str(Game.submit({"type": "set_active_pet", "pet": toad.uid}).get("reason", "")) == "cannot_call", "in the field an animal left at home cannot be called")
	check(str(Game.submit({"type": "set_pet_bag", "pet": toad.uid, "on": true}).get("reason", "")) == "not_safe", "nor packed")
	var sw := Game.submit({"type": "swap_pet_from_bag", "pet": otter.uid})
	check(sw.get("ok", false) and c.active_pet == str(otter.uid) and c.pet_bag.has(str(fox.uid)) and not c.pet_bag.has(str(otter.uid)),
		"swap from the bag: the otter comes out, the fox goes in")
	var st: ActorState = Game.actor_state(c.id)
	var rat: EnemyState = Game.enemies.spawn_at("reedtail_rat", st.plane + Vector2(120, 0), 2)
	rat.ai.state = "aggro"
	check(str(Game.submit({"type": "swap_pet_from_bag", "pet": fox.uid}).get("reason", "")) == "in_combat", "never in a fight")
	Game.enemies.release(rat)
	# The Mount slot: a combat animal and a mount together; mount-only species; the Mount button.
	Game.world.load_room(c, "rm_hermit_stilt_house", "")
	Game.pets.apply_grant(c.id, "riverstone_ox")
	var ox: Dictionary = c.pets.back()
	check(str(Game.submit({"type": "set_active_pet", "pet": ox.uid}).get("reason", "")) == "cannot_call"
		and str(Game.submit({"type": "set_pet_role", "pet": ox.uid, "role": "combat"}).get("reason", "")) == "mount_only", "a Riverstone Ox only carries you")
	check(Game.submit({"type": "set_mount", "pet": ox.uid}).get("ok", false) and c.mount_pet == str(ox.uid) and c.riding and c.active_pet == str(otter.uid),
		"the ox takes the Mount slot; the otter stays active")
	Game.world.load_room(c, "lf_reed_shallows", "")
	check(near(Game.pets.mount_speed(c), 1.5) and Game.pets.ally_uid != 0, "riding the ox at x1.5 while the otter walks beside you")
	Game.submit({"type": "set_mount", "on": false})
	check(not c.riding and near(Game.pets.mount_speed(c), 1.0), "the Mount button: off and walking")
	Game.pets.apply_grant(c.id, "cloud_stag")
	var stag: Dictionary = c.pets.back()
	Game.submit({"type": "set_mount", "pet": stag.uid})
	check(near(Game.pets.mount_speed(c), 1.6) and int(ContentDB.entry("pets", "cloud_stag").movement.jump) == 600 and str(ox.role) == "mount", "the Cloud Stag: x1.6, jump 600")
	# An older save rode the active animal in the Mount role: it moves to the Mount slot.
	c.mount_pet = ""
	c.riding = false
	var crane_like := stag
	c.active_pet = str(crane_like.uid)
	check(not Game.pets.mount_of(c).is_empty() and c.mount_pet == str(crane_like.uid) and c.active_pet == "", "an old mount moves into the Mount slot")
	c.active_pet = str(otter.uid)
	# Beast Kings: +10% to their zone's beasts while they live; lifted at once when they fall; the nest opens.
	var timers: Dictionary = Game.account.rooms.get("field_boss_timers", {})
	timers["riverbed_serpent"] = Clock.now_utc() + 3600.0
	Game.account.rooms["field_boss_timers"] = timers
	var plain: EnemyState = Game.enemies.spawn_at("tide_crab", st.plane + Vector2(300, 0), 22)
	var base_hp: float = plain.pools.max_hp
	var base_atk: float = float(plain.stats.attack)
	Game.enemies.release(plain)
	timers["riverbed_serpent"] = 0.0
	var buffed: EnemyState = Game.enemies.spawn_at("tide_crab", st.plane + Vector2(300, 0), 22)
	check(near(buffed.pools.max_hp, base_hp * 1.1, 0.5) and near(float(buffed.stats.attack), base_atk * 1.1, 0.05), "while the Riverbed Serpent lives, a valley crab is 10% stronger")
	GameEvents.emit_event("actor_defeated", {"victim_kind": "enemy", "def": "riverbed_serpent", "role": "field_boss", "room": "dw_serpents_shallows",
		"level": 25, "x": 0.0, "y": 0.0})
	GameEvents.flush()
	check(near(buffed.pools.max_hp, base_hp, 0.5) and not buffed.ai.get("king_buff", true), "the King falls: the buff lifts at once")
	Game.enemies.release(buffed)
	check(Game.world.nest_closes("riverbed_serpent") > Clock.now_utc() + 1700.0, "its nest opens for 30 minutes")
	var shore := {"enemy": "reed_otter", "king_alive": "riverbed_serpent"}
	timers["riverbed_serpent"] = Clock.now_utc() + 3600.0
	check(not Game.enemies._spawn_allowed(shore), "with the King dead, no extra paw-marked beasts")
	timers["riverbed_serpent"] = 0.0
	check(Game.enemies._spawn_allowed(shore), "while it lives they gather")
	Game.world.load_room(c, "dw_serpents_shallows", "")
	var nest: Dictionary = Game.room_rt.object_def("serpent_nest")
	check(Game.world.object_visible(c, nest), "the nest shows while it is open")
	Game.actor_state(c.id).plane = Vector2(float(nest.at[0]), float(nest.at[1]))
	Game.actor_state(c.id).altitude = float(nest.get("alt", 0))   # up on the high rock beside it
	var n0: int = c.inventory.count("rare_spirit_egg")
	var ni := Game.world.interact(c, "serpent_nest")
	check(c.inventory.count("rare_spirit_egg") == n0 + 1 and not Game.world.object_available(c, nest).ok, "one Rare Spirit Egg per opening %s" % str(ni.get("reason", "")))
	# The Beast Tide: once a week at Stoneford Gate; three waves whose Level follows yours; cores, an egg, Spirit Soil.
	Game.world.load_room(c, "sf_gate", "")
	c.cooldowns.erase("beast_tide_week")
	check(Game.world.tide_due(c), "the Beast Tide is due this week")
	var tw := Game.world.start_beast_tide(c)
	check(tw.get("ok", false) and Game.room_rt.event.get("active", false) and (Game.room_rt.event.waves as Array).size() == 3, "ring the gong: three waves")
	var w0: Dictionary = Game.room_rt.event.waves[0]
	check(Game.world.event_level(c, w0) == clampi(ProgressionRules.level(c) - 4, 10, 45), "the waves' Level follows yours, between 10 and 45")
	Game.room_rt.event.remaining = float(Game.room_rt.event.duration) - 40.0
	Game.room_rt.event.wave_timers[0] = 0.0
	var crabs := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "tide_crab").size()
	Game.world._tick_event(c, Game.room_rt, 0.01)
	check(Game.room_rt.living_enemies().filter(func(e): return e.def_id == "tide_crab").size() == crabs, "the first wave stops after its 30 seconds")
	var stag_eggs: int = c.inventory.count("cloud_stag_egg")
	c.quests.flags.erase("tide_stag_egg")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(not Game.world.tide_due(c) and c.inventory.count("cloud_stag_egg") == stag_eggs + 1 and c.inventory.count("spirit_soil") >= 1,
		"held: the week's tide is spent; a Cloud Stag egg (Cloud Stride 1) and Spirit Soil")
	# Pets never die: at 0 HP an animal retreats into its token and comes back.
	Game.world.load_room(c, "lf_reed_shallows", "")
	Game.pets._spawn(c)
	var a: EnemyState = Game.room_rt.enemies.get(Game.pets.ally_uid)
	check(a != null, "the otter is out")
	if a != null:
		a.pools.hp = 0.0
		Game.pets.apply_retreat(a)
		check(str(a.ai.state) == "downed" and a.alive and c.pets.has(otter), "at 0 HP it retreats into its token, alive")
		c.cultivator.meditating = true
		AllyBrain.think(Game, a, 0.1, 1.0, 36.0)
		c.cultivator.meditating = false
		check(str(a.ai.state) == "follow" and near(a.pools.hp, a.pools.max_hp), "meditation calls it back whole")
	Game.account.rooms["field_boss_timers"] = timers_was
	c.pets = pets_was
	c.active_pet = active_was
	c.pet_bag = bag_was
	c.mount_pet = ""
	c.riding = false
	c.inventory.key_items = keys_was
	c.cultivator.realm_key = realm_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S46 · the Beast Arena's auto-battle and ladder, the Beast Trial Grove, Beast Taming Dao tiers, the Feeding Trough.
func beast_arena_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var pets_was: Array = c.pets.duplicate(true)
	var active_was: String = c.active_pet
	var arena_was: Dictionary = c.beast_arena.duplicate(true)
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	var sect_was: Dictionary = Game.account.sect.duplicate(true)
	var storage_was: Array = (Game.account.storage.get("items", []) as Array).duplicate(true)
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	Unlocks.force_unlock(c.id, "spirit_animals")
	c.inventory.bag.fill(null)
	c.pets = []
	c.party_pets = []
	c.pet_bag = []
	c.mount_pet = ""
	var bcfg: Dictionary = Game.pets.arena_cfg().battle
	# The auto-battle: pure and deterministic; the stronger side wins.
	var strong := PetRules.combatant({"species": "mist_wolf", "level": 40, "rarity": "rare", "stage": "adult"}, bcfg)
	var weak := PetRules.combatant({"species": "reed_otter", "level": 12, "rarity": "common", "stage": "hatchling"}, bcfg)
	var r1 := PetRules.battle([strong], [weak], bcfg, _seeded(7))
	var r2 := PetRules.battle([strong], [weak], bcfg, _seeded(7))
	check(str(r1.winner) == "a" and r1.log == r2.log, "the same seed fights the same fight, and the stronger animal wins")
	var sk := PetRules.combatant({"species": "ember_fox", "level": 20, "skill_mult": 2.5, "free_cast": true}, bcfg)
	var r3 := PetRules.battle([sk], [PetRules.combatant({"species": "ember_fox", "level": 20}, bcfg)], bcfg, _seeded(3))
	check(not (r3.log as Array).is_empty() and bool(r3.log[0].skill) and str(r3.log[0].side) == "a", "an Equal Contract's free cast opens the fight")
	# The ladder: challenge the tamer above you; a win takes their rank; five fights a day; 3v3 needs three.
	Game.pets.apply_grant(c.id, "mist_wolf")
	var wolf: Dictionary = c.pets.back()
	wolf.level = 60
	wolf.rarity = "epic"
	wolf.stage = "awakened"
	c.active_pet = str(wolf.uid)
	c.beast_arena = {}
	var st0: Dictionary = Game.pets.arena_state(c)
	check(int(st0.rank) == 11 and str(Game.pets.arena_opponent(c).id) == "farmhand_qiao", "unranked, the first opponent is Farmhand Qiao (rank 10)")
	check(str(Game.submit({"type": "arena_challenge", "mode": "trio"}).get("reason", "")) == "team", "a 3v3 needs three animals")
	var f1 := Game.submit({"type": "arena_challenge", "mode": "solo"})
	check(f1.get("won", false) and int(c.beast_arena.rank) == 10 and not (c.beast_arena.last.log as Array).is_empty(), "a Level 60 wolf beats him and takes rank 10")
	for i in 4: Game.submit({"type": "arena_challenge", "mode": "solo"})
	check(str(Game.submit({"type": "arena_challenge", "mode": "solo"}).get("reason", "")) == "no_fights", "five fights a day")
	# The week turns: rank 3 pays 15 Spirit Stones and a Beast Marrow Washing Pill; the ladder starts again.
	c.beast_arena.rank = 3
	c.beast_arena.week = Clock.reset_week(Clock.now_utc()) - 1
	var pills0: int = c.inventory.count("beast_marrow_washing_pill")
	Game.pets.arena_state(c)
	check(int(Game.account.currencies.get("spirit_stone", 0)) == stones0 + 15 and c.inventory.count("beast_marrow_washing_pill") == pills0 + 1
		and int(c.beast_arena.rank) == 11, "the week turns: rank 3 pays out, the ladder starts again")
	# The Trial Grove: once a day; the keeper's blows rally instead of striking; ten kills; the Guardian Spirit first.
	Game.world.load_room(c, "sf_beast_grove", "")
	Game.pets._spawn(c)
	c.cooldowns.erase("grove_day")
	check(Game.world.start_beast_trial(c).get("ok", false) and Game.room_rt.event.get("pet_trial", false), "the Grove's trial begins")
	check(str(Game.world.start_beast_trial(c).get("reason", "")) == "done", "once a day")
	var st: ActorState = Game.actor_state(c.id)
	var boar: EnemyState = Game.enemies.spawn_at("wild_boarlet", st.plane + Vector2(60, 0), 20)
	var hp0: float = boar.pools.hp
	Game.pets.rally_ready.erase(c.id)
	Game.combat._damage_enemy(boar, 50.0, c.id, "physical", "none", false, {})
	check(near(boar.pools.hp, hp0) and float(Game.pets.rally_until.get(c.id, 0.0)) > Game.sim_time, "your blow rallies the animals instead of striking")
	var pw := Game.pets.pet_power(c, wolf)
	Game.pets.rally_until.erase(c.id)
	check(near(pw, Game.pets.pet_power(c, wolf) * 1.25, 0.01), "rallied: +25%")
	Game.combat._damage_enemy(boar, 1e9, c.id, "physical", "none", false, {"source": "ally:1"})
	GameEvents.flush()
	check(int(Game.room_rt.event.get("kills", 0)) == 1, "the animals' kills count toward the ten")
	c.quests.flags.erase("grove_first_clear")
	var books0: int = c.inventory.count("pet_book_guardian_spirit")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(c.inventory.count("pet_book_guardian_spirit") == books0 + 1, "the first clear gives the Guardian Spirit book")
	# Beast Taming Dao: elites from tier 3; eggs 10% sooner from tier 2; teachable from tier 4.
	Unlocks.force_unlock(c.id, "taming")
	Game.world.load_room(c, "lf_reed_shallows", "")
	st = Game.actor_state(c.id)
	var eo: EnemyState = Game.enemies.spawn_at("reed_otter", st.plane + Vector2(60, 0), 20, {"elite": true})
	eo.pools.hp = eo.pools.max_hp * 0.1
	Game.inventory.apply_add(c.id, "bonding_offering_common", 2, "test")
	c.cultivator.daos["beast_taming"] = {"tier": 2, "insight": 0.0}
	check(str(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("reason", "")) == "elite_tier", "an elite needs the Dao at tier 3")
	c.cultivator.daos["beast_taming"] = {"tier": 3, "insight": 0.0}
	check(Game.submit({"type": "attempt_tame", "offering": "bonding_offering_common"}).get("ok", false), "at tier 3 the elite can be tried")
	check(not Game.workshop.teachable_daos(c).has("beast_taming"), "not yet teachable at tier 3")
	c.cultivator.daos["beast_taming"] = {"tier": 4, "insight": 0.0}
	check(Game.workshop.teachable_daos(c).has("beast_taming"), "teachable at tier 4")
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	# The Feeding Trough: with a Beast Pavilion, hungry animals eat from storage once a day.
	Game.account.sect = {"name": "Test", "level": 1, "buildings": {"beast_pavilion": 1}}
	Game.account.storage["items"] = [{"id": "roast_fish", "count": 2}]
	wolf.hunger_day = Clock.reset_day(Clock.now_utc()) - 2
	c.cooldowns.erase("trough_day")
	Game.pets._trough(c)
	check(int(wolf.hunger_day) == Clock.reset_day(Clock.now_utc()) and int(Game.account.storage.items[0].count) == 1, "the trough feeds the hungry wolf from storage")
	wolf.hunger_day = 0
	Game.pets._trough(c)
	check(int(wolf.hunger_day) == 0, "once a day")
	Game.account.sect = sect_was
	Game.account.storage["items"] = storage_was
	Game.account.currencies["spirit_stone"] = stones0
	c.cultivator.daos = daos_was
	c.beast_arena = arena_was
	c.pets = pets_was
	c.active_pet = active_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49: the Relations authority owns the karma ledger, alignment and Fame; deeds come from karma.json.
func relations_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var rel: RelationsState = c.relations
	rel.restore({})
	# A save from before S49 carries its ledger on the cultivator; it moves across.
	var old_save: Dictionary = c.snapshot()
	old_save.erase("relations")
	old_save.cultivator["merit"] = 77
	old_save.cultivator["sin"] = 5
	old_save.cultivator["debts"] = {"gu_repays": {"due_utc": 1.0, "mail": "gu_repays", "attachments": [], "paid": true}}
	old_save.cultivator["merit_used"] = {"cloud_stride": true}
	var moved := GameCharacter.new()
	moved.restore(old_save)
	check(moved.relations.merit == 77 and moved.relations.sin == 5 and moved.relations.debts.has("gu_repays") and moved.relations.merit_used.has("cloud_stride"),
		"an old save's merit, sin, debts and eased realms move to Relations")
	check(not moved.cultivator.snapshot().has("merit") and moved.snapshot().relations.merit == 77, "and are saved there from now on")
	# A named deed from an effect: merit, alignment and Fame together, once.
	Game.apply_effects(c.id, [{"kind": "deed", "deed": "cleansing_the_well"}], "test")
	GameEvents.flush()
	check(rel.merit == 30 and rel.alignment == 5 and rel.fame == 15, "cleansing the well: +30 merit, +5 alignment, +15 Fame (Part 8)")
	Game.apply_effects(c.id, [{"kind": "deed", "deed": "cleansing_the_well"}], "test")
	check(rel.merit == 30, "a once-only deed counts once")
	check(str(rel.ledger[0].reason) == "cleansing_the_well", "the ledger remembers the deed")
	Game.relations.apply_deed(c.id, "heal_patient")
	Game.relations.apply_deed(c.id, "heal_patient")
	check(rel.merit == 34, "each patient healed is +2 merit, again and again")
	# Event deeds: a spar won in a town square is public; the same spar in the wilds is not.
	Game.world.load_room(c, "sf_market", "")
	var f0 := rel.fame
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "player", "room": "sf_market"}, "spar_ended")
	check(rel.fame == f0 + 3, "a public win: +3 Fame")
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "opponent", "room": "sf_market"}, "spar_ended")
	check(rel.fame == f0 - 2, "a public defeat costs 5")
	Game.world.load_room(c, "lf_reed_shallows", "")
	Game.relations._on_deed_event({"actor": c.id, "opponent": "sparring_disciple", "winner": "opponent", "room": "lf_reed_shallows"}, "spar_ended")
	check(rel.fame == f0 - 2, "no one sees a spar in the reeds")
	var f1 := rel.fame
	var boss := {"victim": "9", "victim_kind": "enemy", "def": "riverbed_serpent", "role": "field_boss", "killer": c.id}
	Game.relations._on_deed_event(boss, "actor_defeated")
	Game.relations._on_deed_event(boss, "actor_defeated")
	boss.def = "thousand_eye_toad"
	Game.relations._on_deed_event(boss, "actor_defeated")
	check(rel.fame == f1 + 20, "each field lord felled is +10 Fame, the first time")
	# Fame tiers and the tier-up.
	rel.fame = 140
	var ups: Array = []
	var on_fame := func(p: Dictionary): if p.get("tier_up", false): ups.append(str(p.tier))
	GameEvents.subscribe("fame_changed", on_fame, 200)
	Game.relations.apply_fame(c.id, 20, "test")
	GameEvents.flush()
	check(str(Game.relations.fame_tier(c).id) == "rising" and ups == ["rising"], "150 Fame is Rising, and the step up is announced")
	Game.relations.apply_fame(c.id, -1000, "test")
	check(rel.fame == 0, "Fame never goes below 0")
	# Alignment: clamped, named, and a gate on optional things only.
	rel.alignment = 0
	var upright := {"all": [{"kind": "alignment_at_least", "value": 20}]}
	var shadowed := {"all": [{"kind": "alignment_at_most", "value": -20}]}
	check(not RequirementRules.passes(upright, {"char": c}) and not RequirementRules.passes(shadowed, {"char": c}), "a balanced cultivator is neither upright nor shadowed")
	Game.relations.apply_alignment(c.id, 500, "test")
	check(rel.alignment == 100 and Game.relations.alignment_word(c) == "righteous" and RequirementRules.passes(upright, {"char": c}), "alignment stops at +100 (Righteous)")
	Game.relations.apply_alignment(c.id, -130, "test")
	check(rel.alignment == -30 and Game.relations.alignment_word(c) == "shadowed" and RequirementRules.passes(shadowed, {"char": c}), "and leans the other way")
	var cloud := ContentDB.entry("shops", "cloud_sect")
	var incense := {}
	for row in cloud.get("stock", []):
		if str(row.item) == "calm_heart_incense": incense = row
	check(not RequirementRules.passes(incense.get("requires", {}), {"char": c}), "the Cloud Sect's incense is for the upright")
	check(RequirementRules.passes({"all": [{"kind": "realm_at_least", "realm": c.cultivator.realm_key}]}, {"char": c}), "alignment never touches a realm requirement")
	# A black-market purchase is a deed from the event, per item.
	rel.alignment = 0
	var sin0 := rel.sin
	Game.relations._on_deed_event({"actor": c.id, "shop": "free_market", "item": "manual_page", "count": 3}, "item_bought")
	check(rel.sin == sin0 + 6 and rel.alignment == -3, "three items from the back room: +6 sin, -3 alignment")
	# Young masters: from Rising Fame, a town may bring one out; answer him or lose face.
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	rel.fame = 100
	c.cooldowns.erase("young_master_day")
	for i in 40: Game.relations._on_room_entered({})
	check(Game.relations.challenge_of(c).is_empty(), "below Rising no one comes")
	rel.fame = 200
	var came := false
	for i in 60:
		c.cooldowns.erase("young_master_day")
		Game.relations._on_room_entered({})
		if not Game.relations.challenge_of(c).is_empty():
			came = true
			break
	check(came, "a Rising name draws a young master in town")
	Game.relations._on_room_entered({})
	check(Game.relations.challenge_of(c).is_empty(), "once a day at most")
	Game.relations.offer_challenge(c, "young_master")
	check(Game.submit({"type": "answer_challenge", "accept": false}).get("ok", false) and rel.fame == 195, "declining costs 5 Fame")
	check(not Game.submit({"type": "answer_challenge", "accept": true}).get("ok", false), "and the challenge is gone")
	Game.relations.offer_challenge(c, "young_master")
	check(Game.submit({"type": "answer_challenge", "accept": true}).get("ok", false), "accepting starts the spar")
	var ym: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "young_master": ym = e
	check(ym != null and ym.level == ProgressionRules.level(c), "he fights at your own level")
	if ym != null:
		Game.enemies.end_spar(ym, c.id)
		GameEvents.flush()
		check(rel.fame == 195 + 15 + 3, "humbling him in the square: +18 Fame")
	Game.relations.offer_challenge(c, "young_master")
	Game.world.load_room(c, "lf_reed_shallows", "")
	GameEvents.flush()
	check(Game.relations.challenge_of(c).is_empty(), "walking away lets the challenge lapse")
	GameEvents.unsubscribe_object(self)
	c.relations.restore(rel_was)
	c.cooldowns = cd_was
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0: NPC affinity (hearts, gifts once a day, heart rewards, discounts), companion duels, sworn siblings, the
## Dao Companion and the master's legacy.
func bonds_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var comp_was: Dictionary = c.companions.duplicate(true)
	var recipes_was: Array = c.crafting.recipes.duplicate()
	var arts_was: Array = c.cultivator.inner_arts_known.duplicate()
	var title_was: String = c.cultivator.active_title
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var rel: RelationsState = c.relations
	rel.restore({})
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "lf_reed_shallows", "")
	# A gift a day: loved is a heart; the second gift that day is refused.
	Game.inventory.apply_add(c.id, "riverfish_soup", 2, "test")
	var r1: Dictionary = Game.submit({"type": "give_gift", "npc": "aunt_ping", "index": _bag_index(c, "riverfish_soup")})
	check(r1.get("ok", false) and str(r1.reaction) == "loved" and rel.hearts_of("aunt_ping") == 1, "Riverfish Soup is Aunt Ping's favourite: a whole heart")
	check(str(Game.submit({"type": "give_gift", "npc": "aunt_ping", "index": _bag_index(c, "riverfish_soup")}).get("reason", "")) == "gifted_today", "one gift a day")
	check(str(rel.affinity.aunt_ping.known.get("riverfish_soup", "")) == "loved", "and you remember what she loves")
	Game.inventory.apply_add(c.id, "rice_ball", 1, "test")
	Game.submit({"type": "give_gift", "npc": "granny_liu", "index": _bag_index(c, "rice_ball")})
	check(int(rel.affinity.granny_liu.points) == 15, "anything else is a courtesy (+15)")
	Game.inventory.apply_add(c.id, "training_jian", 1, "test")
	check(str(Game.submit({"type": "give_gift", "npc": "old_ma", "index": _bag_index(c, "training_jian")}).get("reason", "")) == "not_giftable"
		and not RelationsAuthority.giftable({"id": "kite", "count": 1}), "gear and key items stay with you")
	# One person, two rows: Mei Qing at her stall and in the sect keep one heart count.
	Game.inventory.apply_add(c.id, "cloudtop_orchid", 1, "test")
	Game.submit({"type": "give_gift", "npc": "mei_qing_sect", "index": _bag_index(c, "cloudtop_orchid")})
	check(rel.hearts_of("mei_qing") == 1 and rel.hearts_of("mei_qing_sect") == 1, "Mei Qing is one person wherever you meet her")
	# Hearts pay once: Aunt Ping teaches Riverfish Soup at three.
	c.crafting.recipes.erase("riverfish_soup")
	Game.relations.apply_affinity(c.id, "aunt_ping", 200, "test")
	check(rel.hearts_of("aunt_ping") == 3 and c.crafting.recipes.has("riverfish_soup"), "three hearts: Aunt Ping teaches her soup")
	c.crafting.recipes.erase("riverfish_soup")
	Game.relations.apply_affinity(c.id, "aunt_ping", -100, "test")
	Game.relations.apply_affinity(c.id, "aunt_ping", 100, "test")
	check(not c.crafting.recipes.has("riverfish_soup"), "and only once")
	check(RequirementRules.passes({"all": [{"kind": "hearts_at_least", "npc": "aunt_ping", "value": 3}]}, {"char": c}), "hearts_at_least reads the hearts")
	# Quests make friends.
	var gp: int = int(rel.affinity.get("granny_liu", {}).get("points", 0))
	Game.relations._on_quest_completed({"actor": c.id, "quest": "grannys_remedy"})
	check(int(rel.affinity.granny_liu.points) == gp + 30, "a quest done for Granny Liu: +30")
	# A keeper who likes you gives a little off.
	var dear := ""
	var price0 := 0
	for row in Game.economy.stock(c, "old_ma"):
		if int(row.price) > price0:
			price0 = int(row.price)
			dear = str(row.item)
	Game.relations.apply_affinity(c.id, "old_ma", 300, "test")
	var price1 := 0
	for row in Game.economy.stock(c, "old_ma"):
		if str(row.item) == dear: price1 = int(row.price)
	check(Game.relations.shop_discount(c, "old_ma") == 0.05 and price1 < price0, "three hearts with Old Ma: 5%% off (%d -> %d)" % [price0, price1])
	# Companions: a duel at three hearts, sworn at four, a Dao Companion at five.
	c.companions = {"roster": ["lan_yue", "tie_niu"], "active": ["lan_yue", "tie_niu"], "bond": {}, "downed": {}}
	Game.submit({"type": "set_active_companions", "ids": ["lan_yue", "tie_niu"]})
	check(str(Game.submit({"type": "companion_duel", "companion": "lan_yue"}).get("reason", "")) == "hearts", "no duel before three hearts")
	Game.relations.apply_affinity(c.id, "lan_yue", 300, "test")
	check(c.crafting.recipes.has("lotus_root_tea"), "three hearts with Lan Yue: her tea")
	check(Game.submit({"type": "companion_duel", "companion": "lan_yue"}).get("ok", false), "a friendly duel at three")
	var dz: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "duel_lan_yue": dz = e
	check(dz != null and dz.level == ProgressionRules.level(c), "Lan Yue duels at your level")
	var lp: int = int(rel.affinity.lan_yue.points)
	if dz != null:
		Game.enemies.end_spar(dz, c.id)
		GameEvents.flush()
	check(int(rel.affinity.lan_yue.points) == lp + 20, "winning the duel: +20")
	Game.relations._on_spar_ended({"actor": c.id, "opponent": "duel_lan_yue", "winner": "player"})
	check(int(rel.affinity.lan_yue.points) == lp + 20, "once a day")
	check(str(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("reason", "")) == "hearts", "sworn siblings need four hearts")
	Game.relations.apply_affinity(c.id, "lan_yue", 100, "test")
	var atk0: float = c.stats.value("physical_attack")
	check(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("ok", false) and (rel.bonds.sworn as Array).has("lan_yue"), "four hearts: sworn")
	check(c.stats.value("physical_attack") > atk0 and c.cultivator.titles.has("sworn_sibling"), "a sworn sibling in the party lifts your attack, and you share a title")
	check(str(Game.submit({"type": "offer_bond", "kind": "sworn", "npc": "lan_yue"}).get("reason", "")) == "already", "once")
	Game.relations.apply_affinity(c.id, "tie_niu", 500, "test")
	check(str(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "lan_yue"}).get("reason", "")) in ["hearts", "sworn"], "a sworn sibling is not a Dao Companion")
	check(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "tie_niu"}).get("ok", false), "five hearts: Tie Niu is your Dao Companion")
	Game.relations.apply_affinity(c.id, "lan_yue", 100, "test")
	check(str(Game.submit({"type": "offer_bond", "kind": "dao_companion", "npc": "lan_yue"}).get("reason", "")) in ["taken", "sworn"], "one Dao Companion only")
	check(Game.relations.bond_support(c) == 1 and near(Game.relations.insight_share(c), 0.1), "beside you: the support slot and +10% insight")
	c.cultivator.meditating = true
	check(near(Game.companions.paired_bonus(c), 0.25), "resonance meditation with the Dao Companion: +25%")
	c.cultivator.meditating = false
	Game.submit({"type": "set_active_companions", "ids": ["lan_yue"]})
	check(Game.relations.bond_support(c) == 0, "not when they stay behind")
	# The master: the personal-disciple trial binds you; the last lesson passes the legacy art.
	Game.relations._on_quest_completed({"actor": c.id, "quest": "the_mentors_gift"})
	var mentor := "elder_sung" if str(c.training_sect.get("id", "")) == "cloud_sect" else "elder_hu"
	check(str(rel.bonds.master) == mentor, "the mentor's trial makes %s your master" % mentor)
	c.cultivator.inner_arts_known.erase("lotus_mind_legacy")
	c.cultivator.inner_arts_known.erase("drifting_cloud_legacy")
	Game.apply_effects(c.id, [{"kind": "master_legacy"}], "test")
	check(c.cultivator.inner_arts_known.has("lotus_mind_legacy" if mentor == "elder_hu" else "drifting_cloud_legacy"), "the last lesson passes the master's legacy art")
	var sold := false
	for row in ContentDB.entry("shops", "jade_sect").get("stock", []):
		if str(row.get("learn", "")) in ["lotus_mind_legacy", "drifting_cloud_legacy"]: sold = true
	check(not sold, "legacy arts are never sold")
	c.relations.restore(rel_was)
	c.companions = comp_was
	c.crafting.recipes = recipes_was
	c.cultivator.inner_arts_known = arts_was
	c.cultivator.titles.erase("sworn_sibling")
	c.cultivator.active_title = title_was
	c.inventory.bag.fill(null)
	Game.combat.refresh_stats(c.id)
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0: grudges and hunters, settling them, bounties, a named foe's surrender and Part 8's named debts.
func grudges_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var rel_was: Dictionary = c.relations.snapshot()
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var done_was: Dictionary = c.quests.done.duplicate()
	var flags_was: Dictionary = c.quests.flags.duplicate()
	var taels0 := int(Game.account.currencies.get("silver_tael", 0))
	var mail0: int = Game.account.mail.size()
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var rel: RelationsState = c.relations
	rel.restore({})
	# Named kills raise a faction's grudge; the rank and file do not.
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "mudwater_bandit", "killer": c.id})
	check(Game.relations.grudge(c, "mudwater") == 0, "an ordinary bandit is no one's name")
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "big_toad_tan", "killer": c.id})
	check(Game.relations.grudge(c, "mudwater") == 15, "killing Big Toad Tan: the Mudwater grudge +15")
	# Past the threshold, hunters wait on the roads they know, at your level; not every time, not too often.
	Game.relations.apply_grudge(c.id, "mudwater", 15, "test")
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var found := false
	for i in 40:
		c.cooldowns.erase("hunt_mudwater")
		for e in Game.room_rt.living_enemies():
			if e.def_id == "mudwater_cutthroat": Game.enemies.release(e)
		Game.relations._spawn_hunters(c)
		for e in Game.room_rt.living_enemies():
			if e.def_id == "mudwater_cutthroat" and e.level == ProgressionRules.level(c): found = true
		if found: break
	check(found, "at 30 the Mudwater send a cutthroat onto the Caravan Road, at your level")
	var n0 := Game.room_rt.living_enemies().filter(func(e): return e.def_id == "mudwater_cutthroat").size()
	for i in 20: Game.relations._spawn_hunters(c)
	check(Game.room_rt.living_enemies().filter(func(e): return e.def_id == "mudwater_cutthroat").size() == n0, "then not again for a while")
	for e in Game.room_rt.living_enemies():
		if e.def_id == "mudwater_cutthroat": Game.enemies.release(e)
	# Settling: blood money, a duel with Tan's brother, a quest, or the story.
	Game.account.currencies["silver_tael"] = 500
	check(Game.submit({"type": "pay_grudge", "faction": "mudwater", "method": "blood_money"}).get("ok", false)
		and Game.relations.grudge(c, "mudwater") == 0 and int(Game.account.currencies.silver_tael) == 300, "200 taels of blood money settles the Mudwater")
	Game.relations.apply_grudge(c.id, "mudwater", 20, "test")
	check(Game.submit({"type": "pay_grudge", "faction": "mudwater", "method": "duel"}).get("ok", false), "or a duel with Tan the Younger")
	var tan: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "tan_the_younger": tan = e
	if tan != null:
		Game.enemies.end_spar(tan, c.id)
		GameEvents.flush()
	check(tan != null and Game.relations.grudge(c, "mudwater") == 0, "winning it settles the grudge")
	Game.relations.apply_grudge(c.id, "gorge", 25, "test")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "old_scores"})
	check(Game.relations.grudge(c, "gorge") == 0, "Old Scores settles the Gorge Bandits")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "gus_cargo"})
	Game.relations._on_quest_completed({"actor": c.id, "quest": "hidden_cargo"})
	check(Game.relations.grudge(c, "smugglers") == 40, "Gu's ring: +20 for the cargo, +20 for the hidden cargo")
	Game.relations._on_quest_completed({"actor": c.id, "quest": "gus_warehouse"})
	Game.relations.apply_grudge(c.id, "smugglers", 30, "test")
	check(Game.relations.grudge(c, "smugglers") == 0, "the warehouse ends it for good")
	# Bounties: the board's named targets wait in their rooms while the bounty is yours.
	c.cooldowns.erase("bounty_one_eye_pang")
	var bt: Dictionary = Game.submit({"type": "take_bounty", "id": "one_eye_pang"})
	check(bt.get("ok", false), "take the bounty on One-Eye Pang %s" % str(bt.get("reason", "")))
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var pang: EnemyState = null
	for e in Game.room_rt.living_enemies():
		if e.def_id == "one_eye_pang": pang = e
	check(pang != null and pang.elite, "One-Eye Pang is on the Caravan Road")
	var t1 := int(Game.account.currencies.get("silver_tael", 0))
	var f1 := rel.fame
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "one_eye_pang", "killer": c.id})
	check(int(Game.account.currencies.silver_tael) == t1 + 150 and rel.fame == f1 + 10 and rel.bounties.is_empty(), "the bounty pays 150 taels and +10 Fame")
	check(Game.relations.grudge(c, "mudwater") == 15, "and Pang was a name the Mudwater remember")
	check(str(Game.submit({"type": "take_bounty", "id": "one_eye_pang"}).get("reason", "")) == "today", "each bounty once a day")
	# A named foe yields: spare him (merit; he remembers) or finish him (sin; his brother hunts you).
	var st: ActorState = Game.actor_state(c.id)
	var lt: EnemyState = Game.enemies.spawn_at("mudwater_lieutenant", st.plane + Vector2(80, 0), 19)
	Game.combat._damage_enemy(lt, lt.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	GameEvents.flush()
	check(lt.alive and lt.ai.get("surrendered", false), "Lieutenant Kuai yields instead of dying")
	var hp_y := lt.pools.hp
	Game.combat._damage_enemy(lt, 500.0, c.id, "physical", "none", false, {})
	check(near(lt.pools.hp, hp_y), "a foe who has yielded is not struck")
	var m0 := rel.merit
	check(Game.submit({"type": "judge_foe", "enemy": lt.uid, "spare": true}).get("ok", false) and not lt.alive and rel.merit == m0 + 10, "sparing him: +10 merit")
	check(rel.debts.has("lieutenant_spared"), "and he remembers")
	c.quests.done["hidden_cargo"] = 1
	Game.relations.settle_debts(c)
	GameEvents.flush()
	check(bool(rel.debts.lieutenant_spared.paid) and c.quests.has_flag("warned_of_ambush") and Game.account.mail.size() > mail0, "before Gu's warehouse, his warning arrives")
	var lt2: EnemyState = Game.enemies.spawn_at("mudwater_lieutenant", st.plane + Vector2(80, 0), 19)
	Game.combat._damage_enemy(lt2, lt2.pools.max_hp * 5.0, c.id, "physical", "none", false, {})
	var s0 := rel.sin
	check(Game.submit({"type": "judge_foe", "enemy": lt2.uid, "spare": false}).get("ok", false) and not lt2.alive and rel.sin == s0 + 15, "killing a foe who yielded: +15 sin")
	rel.debts.lieutenant_killed.due_utc = 0.0
	Game.relations.settle_debts(c)
	GameEvents.flush()
	check(rel.hunters.size() == 1 and str(rel.hunters[0].enemy) == "kuai_shan", "his brother Kuai Shan comes hunting")
	Game.world.load_room(c, "cr_caravan_road", "")
	GameEvents.flush()
	var ks := false
	for e in Game.room_rt.living_enemies():
		if e.def_id == "kuai_shan": ks = true
	check(ks, "Kuai Shan waits on the Caravan Road")
	Game.relations._on_defeated({"victim_kind": "enemy", "def": "kuai_shan", "killer": c.id})
	check(rel.hunters.is_empty(), "until he falls")
	# Little Dou's rescue is repaid in chapter 6 with a heaven herb.
	Game.apply_effects(c.id, [{"kind": "record_debt", "id": "dou_rescue"}], "test")
	check(str(rel.debts.dou_rescue.get("due_quest", "")) == "the_heart_trial", "Little Dou's debt falls due with the Heart Trial")
	c.quests.done["the_heart_trial"] = 1
	var mails: int = Game.account.mail.size()
	Game.relations.settle_debts(c)
	check(Game.account.mail.size() == mails + 1 and str(Game.account.mail[0].attachments[0].item) == "cloudtop_orchid", "Dou's letter brings a Cloudtop Orchid")
	# The night peddler: +5 sin a purchase.
	var s1 := rel.sin
	Game.relations._on_deed_event({"actor": c.id, "shop": "night_peddler", "item": "manual_page", "count": 2}, "item_bought")
	check(rel.sin == s1 + 10, "two things from the night peddler: +10 sin")
	check(not RequirementRules.passes(ContentDB.entry("shops", "night_peddler").requires, {"char": c}) or Clock.time_of_day() == "night", "his mat is out only at night")
	for e in Game.room_rt.living_enemies():
		if e.summoned: Game.enemies.release(e)
	c.relations.restore(rel_was)
	c.cooldowns = cd_was
	c.quests.done = done_was
	c.quests.flags = flags_was
	Game.account.currencies["silver_tael"] = taels0
	while Game.account.mail.size() > mail0: Game.account.mail.pop_front()
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0 world calendar: seeded and identical for the same save, events on their rhythm, repeat runs behind the
## cycle and a realm cap (first visits never), the spatial rift, seasons from the account's first week.
func calendar_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var realm_was: String = c.cultivator.realm_key
	var kills_was: Dictionary = c.collection_first_kills.duplicate()
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	var over_was: float = Clock.override_utc
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 424242
	var rift := CalendarRules.event("spatial_rift")
	var shrine := CalendarRules.event("shrine_reopening")
	var fall := CalendarRules.event("waterfall_reopening")
	# The same seed and first day give the same calendar on any device; another seed moves the rifts.
	var a := CalendarRules.schedule(origin + 40 * 86400.0, 424242, origin)
	var b := CalendarRules.schedule(origin + 40 * 86400.0, 424242, origin)
	check(a == b and not a.is_empty(), "the same save sees the same calendar")
	var differ := false
	for k in 12:
		if str(CalendarRules.occurrence(rift, k, 424242, origin).room) != str(CalendarRules.occurrence(rift, k, 7, origin).room): differ = true
	check(differ, "another seed opens the rifts elsewhere")
	# Rhythms: a rift every three days for an hour in a valley field room; the shrine every five days for a day;
	# the Waterfall Cave on the same rhythm, two days later.
	var r0 := CalendarRules.occurrence(rift, 0, 424242, origin)
	var r1 := CalendarRules.occurrence(rift, 1, 424242, origin)
	check(absf(float(r1.start) - float(r0.start) - 3 * 86400.0) <= 12 * 3600.0 and near(float(r0.end) - float(r0.start), 3600.0)
		and (rift.rooms as Array).has(str(r0.room)), "a rift every three days, for an hour, in a field room")
	var s0 := CalendarRules.occurrence(shrine, 0, 424242, origin)
	var f0 := CalendarRules.occurrence(fall, 0, 424242, origin)
	check(near(float(CalendarRules.occurrence(shrine, 1, 424242, origin).start) - float(s0.start), 5 * 86400.0)
		and near(float(f0.start) - float(s0.start), 2 * 86400.0) and near(float(s0.end) - float(s0.start), 86400.0), "reopenings every five days for a day, the cave two days after the shrine")
	check(CalendarRules.active(shrine, float(s0.start) + 3600.0, 424242, origin).get("k", -1) == 0
		and CalendarRules.active(shrine, float(s0.end) + 3600.0, 424242, origin).is_empty(), "open for its day, closed after")
	# Repeat runs only while open and at or below the cap; the first defeat never waits.
	c.cultivator.realm_key = "qi_unfurling_5"
	check(CalendarRules.repeat_open(shrine, float(s0.start) + 60.0, 424242, origin, c.cultivator.realm_key), "the Abbot again: open at Qi Unfurling 5")
	check(not CalendarRules.repeat_open(shrine, float(s0.start) + 60.0, 424242, origin, "heart_tempering_2"), "not at Heart Tempering (past the cap)")
	Clock.override_utc = float(s0.end) + 3600.0
	var spec := {"enemy": "drowned_abbot", "calendar": "shrine_reopening"}
	c.collection_first_kills.erase("drowned_abbot")
	check(Game.enemies._spawn_allowed(spec), "the first defeat is never behind the cycle")
	c.collection_first_kills["drowned_abbot"] = true
	check(not Game.enemies._spawn_allowed(spec), "a repeat waits for the shrine to surface")
	Clock.override_utc = float(s0.start) + 3600.0
	check(Game.enemies._spawn_allowed(spec), "and wakes while it has")
	# The Waterfall Cave's inner cache: once per opening.
	Clock.override_utc = float(f0.start) + 3600.0
	var cache := {}
	for o in ContentDB.room("wg_waterfall_cave").get("objects", []):
		if str(o.id) == "cave_inner_cache": cache = o
	check(not cache.is_empty() and Game.world.open_key(cache) == "cave_inner_cache@0", "the cache is keyed to this opening")
	# The spatial rift: its tear shows in its room while open; touching it pours out that room's beasts, stronger.
	Clock.override_utc = float(r0.start) + 600.0
	Game.world.load_room(c, str(r0.room), "")
	GameEvents.flush()
	var tear := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.type) == "rift_tear": tear = o
	check(not tear.is_empty() and Game.world.object_visible(c, tear), "the tear shows in %s while the rift is open" % r0.room)
	c.cooldowns.erase("rift_k")
	var opened: Dictionary = Game.calendar.open_rift(c)
	check(opened.get("ok", false) and str(Game.room_rt.event.get("id", "")) == "spatial_rift", "touching it starts the rift")
	check(str(Game.calendar.open_rift(c).get("reason", "")) in ["done", "busy"], "once per rift")
	var top := 0
	for w in Game.room_rt.event.get("waves", []): top = maxi(top, int(w.level))
	var room_top := 0
	for sp in Game.room_rt.def.get("spawns", []):
		if not sp.get("boss", false) and not sp.has("requires"): room_top = maxi(room_top, int((sp.get("level", [0]) as Array).back()))
	check(top == room_top + 3, "its beasts come three levels stronger (%d over %d)" % [top, room_top])
	Game.world._end_event(c, Game.room_rt, false)
	Clock.override_utc = float(r0.end) + 600.0
	check(not Game.world.object_visible(c, tear), "the tear closes with the hour")
	# Seasons from the account's first week: spring first.
	HerbRules.origin_week = Clock.reset_week(origin)
	check(HerbRules.season(origin + 3600.0) == "spring" and HerbRules.season(origin + 7 * 86400.0 + 3600.0) != "spring", "spring comes first, from the account's first week")
	HerbRules.origin_week = 0
	if Game.room_rt.event.get("active", false): Game.world._end_event(c, Game.room_rt, false)
	Clock.override_utc = over_was
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	c.cultivator.realm_key = realm_was
	c.collection_first_kills = kills_was
	c.cooldowns = cd_was
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 v1.0/v1.1: Auction Day on Market Street, a Spirit Fruit birth, the Herb Terraces trial, the weather.
func world_events_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var recipes_was: Array = c.crafting.recipes.duplicate()
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	var over_was: float = Clock.override_utc
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var econ_was: Dictionary = Game.account.economy.duplicate(true)
	var mail0: int = Game.account.mail.size()
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 777
	c.inventory.bag.fill(null)
	# Auction Day: the valley's house opens only on Saturdays, its lots close with the day, a recipe is taught.
	var ad := CalendarRules.occurrence(CalendarRules.event("auction_day"), 1, 777, origin)
	check(int(Time.get_datetime_dict_from_unix_time(int(ad.start)).weekday) == 6, "Auction Day falls on a Saturday")
	Clock.override_utc = float(ad.start) - 3600.0
	Game.account.economy.erase("valley_auction")
	Game.economy.auction_roll("valley")
	check(Game.economy.auction_lots("valley").is_empty(), "no valley lots before the day")
	Clock.override_utc = float(ad.start) + 3600.0
	Game.economy.auction_roll("valley")
	var vlots: Array = Game.economy.auction_lots("valley")
	check(vlots.size() == 5 and vlots.all(func(l): return float(l.ends) <= float(ad.end) and str(l.get("house", "")) == "valley"), "five lots on the day, all closing with it")
	var pool_ok := vlots.all(func(l): return str(l.item) in ["recipe_scroll", "spirit_egg", "rare_spirit_egg", "manual_page"] or str(l.item).ends_with("_seed"))
	check(pool_ok, "seeds, recipe scrolls and eggs")
	var lot: Dictionary = {}
	for l in vlots:
		if str(l.get("learn", "")) != "": lot = l
	if lot.is_empty():
		lot = vlots[0]
		lot.learn = "cloudtop_orchid_broth"
		lot.item = "recipe_scroll"
	c.crafting.recipes.erase(str(lot.learn))
	Game.account.currencies["spirit_stone"] = 5000
	var won: Dictionary = Game.submit({"type": "auction_bid", "house": "valley", "lot": str(lot.id), "amount": int(lot.cap) + 5})
	check(won.get("top", false), "a bid above the house's limit holds the lot")
	Clock.override_utc = float(ad.end) + 60.0
	Game.economy._auction_close("valley")
	check(c.crafting.recipes.has(str(lot.learn)) and Game.account.mail.size() > mail0, "when the hammer falls the recipe is yours")
	check(str(Game.submit({"type": "auction_bid", "house": "valley", "lot": str(vlots[0].id), "amount": 999}).get("reason", "")) == "closed", "after the day the stall is gone")
	# A Spirit Fruit birth: two rivals and a guardian; beat all three and the fruit is yours, once.
	var tb := CalendarRules.occurrence(CalendarRules.event("treasure_birth"), 2, 777, origin)
	Clock.override_utc = float(tb.start) + 600.0
	Game.world.load_room(c, str(tb.room), "")
	GameEvents.flush()
	var tree := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.type) == "treasure_birth": tree = o
	check(not tree.is_empty() and Game.world.object_visible(c, tree), "the fruit tree stands in %s while the fruit is ripe" % tb.room)
	c.cooldowns.erase("birth_k")
	check(Game.calendar.open_treasure(c).get("ok", false), "reaching for it wakes its guardians")
	var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.summoned)
	var defs: Array = foes.map(func(e): return e.def_id)
	check(defs.count("rogue_cultivator") == 2 and defs.has("fruit_guardian"), "two rival cultivators and the Fruit-Guardian Boar %s" % str(defs))
	for e in foes:
		Game.combat.apply_execute(e, c.id)
		GameEvents.flush()
	check(c.inventory.count("spirit_fruit") == 1 and not Game.room_rt.event.get("active", false), "all three down: the Spirit Fruit is yours")
	check(str(Game.calendar.open_treasure(c).get("reason", "")) == "taken", "one fruit per birth")
	# The Herb Terraces trial: herbs gathered there count; the ranking pays when the day ends.
	var gtr := CalendarRules.occurrence(CalendarRules.event("gathering_trial"), 1, 777, origin)
	Clock.override_utc = float(gtr.start) + 3600.0
	Game.world.load_room(c, "ja_herb_terraces", "")
	GameEvents.flush()
	c.cooldowns.erase("gtrial")
	Game.calendar._on_gathered({"actor": c.id, "item": "mist_lotus", "count": 30})
	check(int(c.cooldowns.gtrial.pts) == 30 and Game.calendar.trial_rank(c) == 1, "thirty herbs lead the valley's gatherers")
	check(Game.calendar.trial_rivals(int(gtr.k)) == Game.calendar.trial_rivals(int(gtr.k)), "the rivals' scores are fixed for the trial")
	c.crafting.recipes.erase("foundation_guard_pill")
	Game.calendar._pay_trial(c)
	check(not c.crafting.recipes.has("foundation_guard_pill"), "nothing is paid while the trial runs")
	Clock.override_utc = float(gtr.end) + 60.0
	Game.calendar._pay_trial(c)
	GameEvents.flush()
	check(c.crafting.recipes.has("foundation_guard_pill") and c.inventory.count("foundation_guard_pill") == 3, "first place: the Foundation Guard Pill recipe and three pills")
	var n3: int = c.inventory.count("foundation_guard_pill")
	Game.calendar._pay_trial(c)
	check(c.inventory.count("foundation_guard_pill") == n3, "paid once")
	# Weather: a storm feeds Thunder; rain widens the fishing window; clear skies take it all away.
	Game.combat.apply_weather(c.id, "storm")
	check(near(c.stats.conditional("elemental_power", "element", "thunder"), 0.10), "a storm: Thunder +10%")
	Game.combat.apply_weather(c.id, "clear")
	check(near(c.stats.conditional("elemental_power", "element", "thunder"), 0.0), "and it passes")
	check(near(float(ContentDB.config("calendar").weather_effects.rain.fishing_window), 0.2), "rain: fish bite eagerly (+20% window)")
	check(CalendarRules.weather("marsh", origin + 5000.0, 777) == CalendarRules.weather("marsh", origin + 5000.0, 777), "the weather is the same on every device")
	c.cooldowns = cd_was
	c.crafting.recipes = recipes_was
	c.inventory.bag.fill(null)
	Clock.override_utc = over_was
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	Game.account.currencies["spirit_stone"] = stones0
	Game.account.economy = econ_was
	while Game.account.mail.size() > mail0: Game.account.mail.pop_front()
	if room_was != "": Game.world.load_room(c, room_was, "")

## S49 fortune encounters, heavenly phenomena and lifespan.
func fortune_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var fortune_was: Dictionary = c.relations.fortune.duplicate(true)
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var rel_was := [c.relations.merit, c.relations.alignment, c.relations.fame]
	var qp_was: float = c.cultivator.qp
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	var codex_had: bool = Game.account.codex.has("river_dream")
	var created_was: float = c.created_utc
	c.inventory.bag.fill(null)
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	# The meter: empty for a new hand, full after three hours of play, and it holds only one.
	c.relations.fortune = {}
	check(near(Game.relations.fortune_meter(c), 0.0), "a new character's Fortune meter starts empty")
	check(Game.relations.fortune_check(c, "room_entered").is_empty(), "no encounter while it is empty")
	Game.relations._fill_fortune(c, 3.0 * 3600.0 - 60.0)
	check(Game.relations.fortune_meter(c) < 1.0, "a minute short of three hours of play, not yet")
	Game.relations._fill_fortune(c, 120.0)
	check(near(Game.relations.fortune_meter(c), 1.0), "full after three hours of play, and no fuller")
	var fired := 0
	for i in 500:
		if not Game.relations.fortune_check(c, "room_entered").is_empty(): fired += 1
	GameEvents.flush()
	check(fired == 1, "a full meter turns up one encounter, then holds the rest back (%d in 500 rooms)" % fired)
	# The deck: where each card can come, what it asks, and once-only cards.
	var ids := func(trigger: String) -> Array: return Game.relations.fortune_cards(c, trigger).map(func(o): return str(o.card.id))
	check(not (ids.call("room_entered") as Array).has("hidden_cave") and (ids.call("fell_out") as Array).has("hidden_cave"), "the Hidden Cave comes only from a fall")
	var crane: bool = c.pets.any(func(pp): return str(pp.species) == "jade_crane")
	check((ids.call("room_entered") as Array).has("wounded_crane") == crane, "the wounded crane comes only to someone who keeps a Jade Crane")
	c.relations.fortune["seen"] = {"river_dream": 1}
	check(not (ids.call("room_entered") as Array).has("river_dream"), "the River dream comes once")
	var w0: float = Game.relations.fortune_cards(c, "room_entered").filter(func(o): return str(o.card.id) == "lost_child")[0].w
	c.relations.merit += 200
	var w1: float = Game.relations.fortune_cards(c, "room_entered").filter(func(o): return str(o.card.id) == "lost_child")[0].w
	check(w1 > w0, "merit makes a kind vignette likelier")
	c.relations.merit -= 200
	# A lost child walked home: merit.
	var m0: int = c.relations.merit
	check(str(Game.relations.fortune_check(c, "room_entered", "lost_child").get("id", "")) == "lost_child" and c.relations.merit == m0 + 10, "a lost child walked home: +10 merit")
	# The Hidden Cave: the fall ends in the grotto; its chest fills for each such fall; the way up leaves you where you fell.
	var at: Vector2 = Game.actor_state(c.id).plane
	Game.relations.fortune_check(c, "fell_out", "hidden_cave")
	GameEvents.flush()
	check(Game.room_rt.room_id == "hg_hidden_grotto", "a fall that draws the Hidden Cave ends in the Hidden Grotto")
	var chest := {}
	for o in Game.room_rt.def.get("objects", []):
		if str(o.id) == "grotto_chest": chest = o
	var k1 := Game.world.open_key(chest)
	check(Game.world.object_available(c, chest).get("ok", false), "an old chest waits on the ledge")
	check(Game.world.use_portal(c, "way_up", true).get("ok", false) and Game.room_rt.room_id == "rm_marsh_edge"
		and Game.actor_state(c.id).plane.distance_to(at) < 60.0, "the way up leaves you where you fell")
	GameEvents.flush()
	Game.relations.fortune_check(c, "fell_out", "hidden_cave")
	GameEvents.flush()
	check(Game.world.open_key(chest) != k1, "the chest fills again for the next such fall")
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	# The Hundred-Year Wine: the next Perfect batch is likelier to come out Grain.
	Game.apply_effects(c.id, [{"kind": "grain_blessing"}], "test")
	check(near(float(c.cooldowns.get("grain_blessing", 0.0)), 0.25), "the wine blesses the next batch (+25% Grain)")
	if Unlocks.is_unlocked(c.id, "perfect_timing"):
		Game.crafting.apply_grain_blessing(c.id, 1.0)
		check(Game.crafting._rare_pill_quality(c, [1.0, 1.0, 1.0], _seeded(3)) in ["pill_grain", "pill_halo", "pill_soul"], "blessed, a Perfect run comes out Grain or better")
	# Heavenly phenomena: a major breakthrough gathers clouds, a tribulation lightning; minor steps pass quietly.
	var seen: Array = []
	var on_ph := func(p: Dictionary): seen.append(str(p.kind))
	GameEvents.subscribe("heavenly_phenomenon", on_ph, 200)
	Game.calendar._on_breakthrough({"actor": c.id, "to": "qi_kindling_2", "major": false})
	Game.calendar._on_breakthrough({"actor": c.id, "to": "qi_unfurling_1", "major": true})
	Game.calendar._on_tribulation({"actor": c.id, "to": "cloud_stride_1"})
	GameEvents.flush()
	check(seen == ["cloud", "lightning"], "clouds for a major breakthrough, lightning for a tribulation, nothing for a minor step %s" % str(seen))
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	Game.relations.challenges.erase(c.id)
	var offered := false
	for i in 30:
		Game.relations._on_phenomenon({"actor": c.id, "kind": "cloud", "people": 3})
		if str(Game.relations.challenge_of(c).get("enemy", "")) == "jealous_senior": offered = true
		Game.relations.challenges.erase(c.id)
	check(offered, "where people saw it, a jealous senior may step out")
	Game.relations._on_phenomenon({"actor": c.id, "kind": "cloud", "people": 0})
	check(Game.relations.challenge_of(c).is_empty(), "with nobody there to see, nobody is jealous")
	GameEvents.unsubscribe_object(self)
	# Lifespan: display only. Each great realm's span, a year every four weeks, longevity treasures, ageing people.
	check(int(ContentDB.realm("mortal").max_years) == 80 and int(ContentDB.realm("bone_forging_1").max_years) == 100
		and int(ContentDB.realm("world_genesis").max_years) == 0, "a mortal lives 80 years, Bone Forging 100, World Genesis without end")
	c.created_utc = 1_700_000_000.0
	check(ProgressionRules.age_of(c, c.created_utc + 27.0 * 86400.0) == 16 and ProgressionRules.age_of(c, c.created_utc + 29.0 * 86400.0) == 17, "sixteen at the start, a year older every four weeks")
	check(ProgressionRules.npc_age("granny_liu", c, c.created_utc + 57.0 * 86400.0) == 85, "Granny Liu grows older alongside you")
	var span0 := ProgressionRules.lifespan_of(c)
	Game.inventory.apply_add(c.id, "longevity_peach", 1, "test")
	var pi: int = c.inventory.first_index("longevity_peach")
	Game.submit({"type": "use_item", "index": pi, "confirm": true})
	GameEvents.flush()
	check(ProgressionRules.lifespan_of(c) == span0 + 10 and c.inventory.count("longevity_peach") == 0, "eating a Longevity Peach adds ten years")
	# Restore.
	c.created_utc = created_was
	c.cultivator.longevity = 0
	c.relations.fortune = fortune_was
	c.cooldowns = cd_was
	c.relations.merit = int(rel_was[0])
	c.relations.alignment = int(rel_was[1])
	c.relations.fame = int(rel_was[2])
	c.cultivator.qp = qp_was
	c.cultivator.daos = daos_was
	if not codex_had: Game.account.codex.erase("river_dream")
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 the Trial Tower with its sweep, daily activity chests and the Heaven Ranking.
func tower_activity_ranking_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var tower_was: Dictionary = c.tower.duplicate(true)
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var act_was: Dictionary = Game.account.activity.duplicate(true)
	var stones0 := int(Game.account.currencies.get("spirit_stone", 0))
	var fame_was: int = c.relations.fame
	var created_was: float = Game.account.created_utc
	var seed_was: int = Game.account.rng_seed
	c.inventory.bag.fill(null)
	# The tower: thirty floors, two Levels apart, a guardian every fifth.
	var floors: Array = ContentDB.all("tower")
	check(floors.size() == 30 and int(floors[0].level) == 4 and int(floors[29].level) == 62, "thirty floors, Level 4 to 62")
	check(floors.filter(func(f): return str(f.kind) == "guardian").size() == 6 and floors.all(func(f): return str(f.kind) != "guardian" or not (f.foes as Array).has(str(f.guardian))),
		"a guardian every fifth floor, never escorted by its own kind")
	c.tower = {}
	check(str(Game.world.climb_tower(c, 2).get("reason", "")) == "locked", "floor 2 waits for floor 1")
	check(Game.world.climb_tower(c, 1).get("ok", false) and Game.room_rt.room_id == "sf_trial_tower" and Game.room_rt.event.get("active", false),
		"climbing floor 1 starts its trial in the tower")
	GameEvents.flush()
	for e in Game.room_rt.living_enemies().filter(func(e2): return e2.summoned or e2.team == "enemy"):
		Game.combat.apply_execute(e, c.id)
		GameEvents.flush()
	check(Game.world.tower_cleared(c) == 1 and not Game.room_rt.event.get("active", false), "every foe down: floor 1 is cleared")
	check(int(Game.account.currencies.get("spirit_stone", 0)) == stones0 + int(floors[0].stones), "the first clear pays Spirit Stones")
	# A survive floor passes when the time runs out.
	c.tower["cleared"] = 1
	Game.world.climb_tower(c, 2)
	GameEvents.flush()
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(Game.world.tower_cleared(c) == 2, "floor 2 (survive): holding out clears it")
	# The sweep: every cleared floor once a day, straight to the bag.
	var silver0: int = Game.economy.balance("silver_tael")
	var sw := Game.world.sweep_tower(c)
	check(sw.get("ok", false) and int(sw.floors) == 2 and Game.economy.balance("silver_tael") > silver0, "sweeping gives both cleared floors' loot")
	check(str(Game.world.sweep_tower(c).get("reason", "")) == "nothing", "once a day")
	# Daily activity: sources, caps, the four chests.
	Game.account.activity = {}
	var a0: Dictionary = Game.accounts.activity()
	check(int(a0.points) == 0 and (a0.claimed as Array).is_empty(), "the day starts with no activity")
	for i in 20: Game.accounts.apply_activity("harvest")
	check(int(Game.accounts.activity().by.harvest) == 20, "harvests are capped at 20 points a day")
	check(str(Game.submit({"type": "claim_activity_chest", "tier": "chest_40"}).get("reason", "")) == "short", "the 40-point chest waits")
	check(Game.submit({"type": "claim_activity_chest", "tier": "chest_20"}).get("ok", false), "the 20-point chest opens")
	check(str(Game.submit({"type": "claim_activity_chest", "tier": "chest_20"}).get("reason", "")) == "claimed", "once a day")
	GameEvents.emit_event("quest_completed", {"actor": c.id, "quest": "daily_x", "name": "x", "kind": "daily"})
	GameEvents.emit_event("tower_floor_cleared", {"actor": c.id, "floor": 3, "first": false})
	GameEvents.flush()
	check(int(Game.accounts.activity().points) == 20 + 10 + 10, "a mission and a tower floor add 10 each (%d)" % int(Game.accounts.activity().points))
	# The Heaven Ranking: seeded, the same on every device, climbing week by week.
	var origin := 1_700_000_000.0
	Game.account.created_utc = origin
	Game.account.rng_seed = 4242
	var t1: Array = CalendarRules.rank_table(origin + 86400.0, 4242, origin)
	check(t1.size() == 7 and t1 == CalendarRules.rank_table(origin + 86400.0, 4242, origin), "seven seeded cultivators, the same table on every device")
	var sl := ContentDB.entry("rankings", "shen_lian")
	check(CalendarRules.rank_level(sl, 5) == 20 and CalendarRules.rank_level(sl, 100) == int(sl.cap), "Shen Lian climbs two Levels a week, to her ceiling")
	var sorted_ok := true
	for i in range(1, t1.size()): sorted_ok = sorted_ok and int(t1[i - 1].cp) >= int(t1[i].cp)
	check(sorted_ok, "strongest first")
	# Entering: by CP (top eight) or the tournament finals.
	var entered := Game.calendar.rank_entered(c)
	check(entered == (StatRules.combat_power(c) >= int(CalendarRules.rank_table(Clock.now_utc(), 4242, origin).back().cp)), "you enter at the top eight by CP")
	c.quests.done["the_valley_finals"] = 1
	check(Game.calendar.rank_entered(c) and Game.calendar.ranking(c).any(func(o): return o.get("player", false)), "or by reaching the tournament finals")
	var above := Game.calendar.rank_above(c)
	if not above.is_empty():
		var other: Array = Game.calendar.ranking(c).filter(func(o): return not o.get("player", false) and str(o.id) != str(above.id))
		if not other.is_empty(): check(str(Game.calendar.challenge_rank(c, str(other[0].id)).get("reason", "")) == "not_above", "only the one directly above can be challenged")
		c.cooldowns["rank_duel"] = str(above.id)
		var f0: int = c.relations.fame
		Game.calendar._on_rank_spar({"opponent": str(ContentDB.entry("rankings", str(above.id)).enemy), "winner": "player"})
		GameEvents.flush()
		var t2: Array = Game.calendar.ranking(c)
		var mine := -1
		var theirs := -1
		for i in t2.size():
			if t2[i].get("player", false): mine = i
			elif str(t2[i].id) == str(above.id): theirs = i
		check(mine >= 0 and mine < theirs and c.relations.fame > f0, "beat them in a spar and you hold their place for the week (+Fame)")
	c.quests.done.erase("the_valley_finals")
	# Restore.
	c.tower = tower_was
	c.cooldowns = cd_was
	c.relations.fame = fame_was
	Game.account.activity = act_was
	Game.account.currencies["spirit_stone"] = stones0
	Game.account.created_utc = created_was
	Game.account.rng_seed = seed_was
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 mobile conventions: idle rooms, auto-hunt only where allowed, and quest auto-path over the room graph.
func mobile_conventions_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var idle_was: Dictionary = c.idle_task.duplicate(true)
	var hp_was: float = c.pools.hp
	# Idle Hunt and Gather only where the room allows them.
	check(Game.world.idle_allowed("rm_marsh_edge", "hunt") and not Game.world.idle_allowed("sf_market", "hunt") and Game.world.idle_allowed("sf_market", "rest"),
		"idle Hunt runs in the marsh, not on Market Street (rest goes anywhere)")
	if Unlocks.is_unlocked(c.id, "idle_tasks"):
		check(str(Game.accounts.set_idle_task(c, {"task": "hunt", "room": "sf_market"}).get("reason", "")) == "room", "idle hunting in a town is refused")
		check(Game.accounts.set_idle_task(c, {"task": "hunt", "room": "rm_marsh_edge"}).get("ok", false), "idle hunting in the marsh is accepted")
	# Auto-hunt: refused outside eligible rooms, on in a hunting room, off when a room event starts or health runs low.
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "set_auto_hunt", "on": true}).get("reason", "")) == "room" and not Game.world.auto_hunting(c.id), "auto-hunt is refused in a town")
	Game.world.load_room(c, "sf_trial_tower", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "set_auto_hunt", "on": true}).get("reason", "")) == "room", "and in a trial")
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	for e in Game.room_rt.living_enemies():
		if e.is_boss(): Game.enemies.release(e)
	c.pools.hp = c.pools.max_hp
	check(Game.submit({"type": "set_auto_hunt", "on": true}).get("ok", false) and Game.world.auto_hunting(c.id), "auto-hunt turns on in the marsh")
	Game.world.start_room_event(c, {"id": "test_event", "duration": 30.0})
	Game.world._tick_auto_hunt(c, 1.0)
	GameEvents.flush()
	check(not Game.world.auto_hunting(c.id), "a room event turns it off")
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(Game.submit({"type": "set_auto_hunt", "on": true}).get("ok", false), "and it can go on again after")
	c.pools.hp = c.pools.max_hp * 0.1
	Game.world._tick_auto_hunt(c, 1.0)
	check(not Game.world.auto_hunting(c.id), "low health turns it off")
	c.pools.hp = c.pools.max_hp
	# Auto-path: the fewest rooms through open portals, the portal to take here, arriving, and stopping at danger.
	var r1: Array = Game.world.route(c, "wp_west", "sf_market")
	check(not r1.is_empty() and str(r1[0].room) == "wp_west" and str(r1.back().to) == "sf_market", "a route from the Willow Path to Market Street (%d rooms)" % r1.size())
	var linked := true
	for i in range(1, r1.size()): linked = linked and str(r1[i].room) == str(r1[i - 1].to)
	check(linked, "each step leaves from where the last one arrived")
	check(r1 == Game.world.route(c, "wp_west", "sf_market"), "the same route every time")
	var shut: Dictionary = {"to": "wp_east", "requires": {"all": [{"kind": "flag_set", "flag": "never_set_flag"}]}}
	check(not Game.world.portal_open(c, "lf_village", shut), "a portal whose requirement is unmet is not on any route")
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	check(Game.submit({"type": "auto_path", "target": "sf_market"}).get("ok", false) and str(Game.world.auto_path_step(c).get("portal", "")) == str(r1[0].portal),
		"auto-path shows the portal to take in this room")
	check(not Game.world.auto_hunting(c.id), "auto-path and auto-hunt never run together")
	GameEvents.emit_event("hit_landed", {"attacker": "x", "target": c.id, "target_kind": "player", "amount": 1})
	GameEvents.flush()
	check(Game.world.auto_path_target(c) == "", "a blow stops auto-path")
	Game.submit({"type": "auto_path", "target": "sf_market"})
	Game.world.load_room(c, "sf_market", "")
	GameEvents.flush()
	check(Game.world.auto_path_target(c) == "", "arriving ends it")
	check(str(Game.submit({"type": "auto_path", "target": "sf_market"}).get("reason", "")) == "here", "nothing to do where you already are")
	# Across the Starsea: the route sails from the shipyard's dock.
	var sea: Array = WorldRules.route("ae_shipyard", "sw_broken_pier", func(_r, _p): return true)
	check(sea.size() == 1 and sea[0].get("dock", false), "the Skyport Wreck is a voyage from the shipyard's dock")
	# Restore.
	Game.world.auto_hunt.clear()
	Game.world.auto_paths.clear()
	c.idle_task = idle_was
	c.pools.hp = hp_was
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## V9a: v2's remaining requirement and effect kinds, the treasure-birth announcement and the pet command wheel.
func v2_hooks_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var req := func(cond: Dictionary) -> bool: return RequirementRules.passes({"all": [cond]}, Game.ctx(c))
	# heart_demon_at_most and foundation_share_at_most (S48, S44).
	var hd_was: float = c.cultivator.heart_demon
	c.cultivator.heart_demon = 40.0
	check(req.call({"kind": "heart_demon_at_most", "value": 50}) and not req.call({"kind": "heart_demon_at_most", "value": 30}), "heart_demon_at_most")
	c.cultivator.heart_demon = hd_was
	var f_was: Dictionary = c.cultivator.foundation.duplicate()
	c.cultivator.foundation = {"realm": ProgressionRules.great_realm(c.cultivator.realm_key), "pill_qp": 40.0, "total_qp": 100.0}
	check(req.call({"kind": "foundation_share_at_most", "value": 0.5}) and not req.call({"kind": "foundation_share_at_most", "value": 0.3}), "foundation_share_at_most")
	c.cultivator.foundation = f_was
	# art_known and grant_art: v2's names for the secret (movement) arts.
	var arts_was: Array = c.cultivator.secret_arts.duplicate()
	c.cultivator.secret_arts.erase("breath_control")
	check(not req.call({"kind": "art_known", "art": "breath_control"}), "art_known: not yet")
	Game.apply_effects(c.id, [{"kind": "grant_art", "art": "breath_control"}], "test")
	GameEvents.flush()
	check(req.call({"kind": "art_known", "art": "breath_control"}), "grant_art teaches it")
	c.cultivator.secret_arts = arts_was
	# grant_fate: a fate given outright, as if chosen.
	var fates_was: Array = c.cultivator.fates.duplicate(true)
	var offer_was: Array = c.cultivator.fate_offer.duplicate()
	Game.apply_effects(c.id, [{"kind": "grant_fate", "fate": "lucky_star"}], "test")
	GameEvents.flush()
	check(c.cultivator.fates.any(func(f): return str(f.id) == "lucky_star") and c.cultivator.fate_offer == offer_was, "grant_fate adds the fate and leaves any offer alone")
	c.cultivator.fates = fates_was
	# absorb_flame as an effect: a flame given outright burns under every furnace.
	var flames_was: Array = (c.crafting.get("flames", []) as Array).duplicate()
	var fl: Array = flames_was.duplicate()
	fl.erase("comet_tail_flame")
	c.crafting["flames"] = fl
	Game.apply_effects(c.id, [{"kind": "absorb_flame", "flame": "comet_tail_flame"}], "test")
	GameEvents.flush()
	check((c.crafting.get("flames", []) as Array).has("comet_tail_flame"), "absorb_flame as an effect")
	c.crafting["flames"] = flames_was
	# treasure_birth_announced: World names the fruit and the room when the calendar starts a birth.
	var heard: Array = []
	GameEvents.subscribe("treasure_birth_announced", func(p): heard.append(p), 200)
	GameEvents.emit_event("world_event_started", {"event": "treasure_birth", "k": 1, "room": "wp_east", "ends": 0.0})
	GameEvents.flush()
	check(heard.size() == 1 and str(heard[0].room) == "wp_east" and str(heard[0].item) != "", "a treasure birth is announced with its room and fruit")
	GameEvents.unsubscribe_object(self)
	# The pet command wheel: a known order is kept for every animal out; an unknown one is refused.
	check(Game.submit({"type": "pet_command", "command": "stay"}).get("ok", false) and str(Game.pets.commands.get(c.id, "")) == "stay", "stay")
	check(not Game.submit({"type": "pet_command", "command": "dance"}).get("ok", true), "an unknown order is refused")
	Game.submit({"type": "pet_command", "command": "follow"})
	GameEvents.flush()

## v2 "Depth hooks": every S44-S49 field is written with a neutral value from the start, and round-trips through a
## save (as JSON) and a restore. The build's names for v2's fields are listed in docs/v2_audit.md (Deviations).
func depth_hooks_suite() -> void:
	var c = Game.active()
	if c == null: return
	var norm := func(v): return JSON.parse_string(JSON.stringify(v))
	# A new character carries every depth field, neutral.
	var fresh := GameCharacter.new()
	var fs: Dictionary = fresh.snapshot()
	var cu_keys := ["pill_resistance", "foundation", "residue", "heart_demon", "support_failures", "body_tier", "core_grade", "fates", "physiques",
		"vows", "inner_arts", "stances", "false_realm", "longevity", "epiphany_cooldown"]
	var rel_keys := ["merit", "sin", "debts", "alignment", "fame", "affinity", "bonds", "grudges", "bounties", "mortal", "fortune"]
	var inv_keys := ["treasures", "loadout", "furnace", "draught", "vessel"]
	var missing: Array = []
	for k in cu_keys:
		if not (fs.cultivator as Dictionary).has(k): missing.append("cultivator." + k)
	for k in rel_keys:
		if not (fs.relations as Dictionary).has(k): missing.append("relations." + k)
	for k in inv_keys:
		if not (fs.inventory as Dictionary).has(k): missing.append("inventory." + k)
	for k in ["pets", "pet_bag", "mount_pet", "party_pets", "tower", "beast_arena", "crafting"]:
		if not fs.has(k): missing.append(k)
	check(missing.is_empty(), "a new character carries every S44-S49 field (%s)" % ", ".join(missing))
	check(float(fs.cultivator.heart_demon) == 0.0 and float(fs.cultivator.residue) == 0.0 and (fs.cultivator.fates as Array).is_empty()
		and (fs.cultivator.vows as Array).is_empty() and int(fs.relations.merit) == 0 and int(fs.relations.sin) == 0 and int(fs.relations.alignment) == 0
		and int(fs.relations.fame) == 0, "and every one starts neutral")
	var acc_snap: Dictionary = AccountState.new().snapshot()
	check(acc_snap.has("calendar") and acc_snap.has("activity") and acc_snap.has("sect"), "the account carries the calendar, activity and sect blocks")
	# Non-neutral values survive a save and a restore.
	var ch := GameCharacter.new()
	ch.restore(c.snapshot())
	var cu: CultivatorState = ch.cultivator
	cu.heart_demon = 37.0
	cu.residue = 12
	cu.foundation = {"realm": ProgressionRules.great_realm(cu.realm_key), "pill_qp": 50.0, "total_qp": 200.0}
	cu.pill_resistance = {"accumulation": {"count": 1, "doses": 3}}
	cu.support_failures = {"bone_forging": 1}
	cu.fates = [{"id": "hungry_dantian", "realm": ProgressionRules.great_realm(cu.realm_key)}]
	cu.vows = ["no_burst_pills"]
	cu.stances = {"sword": "sword_flowing"}
	cu.epiphany_cooldown = 1234.0
	var rel: RelationsState = ch.relations
	rel.merit = 42
	rel.sin = 7
	rel.alignment = -25
	rel.fame = 88
	rel.grudges = {"mudwater": 30}
	rel.mortal = {"favour": 60, "day": 3}
	rel.affinity = {"mei_qing": {"points": 40, "gift_day": 5}}
	ch.tower = {"cleared": 3, "swept": {"1": 2}}
	ch.beast_arena = {"rank": 4}
	ch.inventory.treasures = ["bright_mirror", ""]
	var s1: Dictionary = ch.snapshot()
	var ch2 := GameCharacter.new()
	ch2.restore(norm.call(s1))
	var s2: Dictionary = ch2.snapshot()
	var lost: Array = []
	for k in cu_keys:
		if norm.call(s1.cultivator[k]) != norm.call(s2.cultivator[k]): lost.append("cultivator." + k)
	for k in rel_keys:
		if norm.call(s1.relations[k]) != norm.call(s2.relations[k]): lost.append("relations." + k)
	for k in inv_keys:
		if norm.call(s1.inventory[k]) != norm.call(s2.inventory[k]): lost.append("inventory." + k)
	for k in ["pets", "tower", "beast_arena", "crafting", "mount_pet", "pet_bag"]:
		if norm.call(s1[k]) != norm.call(s2[k]): lost.append(k)
	check(lost.is_empty(), "every depth field round-trips through save and restore (%s)" % ", ".join(lost))
	# The account's depth blocks too: the calendar, the activity chests, the sect's mines.
	var acc := AccountState.new()
	acc.restore(Game.account.snapshot())
	acc.calendar = {"active": {"spatial_rift": 3}, "told": {}, "weather": {"marsh": "rain"}, "season": "autumn"}
	acc.activity = {"day": 9, "points": 40, "claimed": [20]}
	acc.sect = {"name": "Test", "level": 3, "mines": {"lower_pit_seam": {"collected": 100.0, "contest": 200.0, "contested": false, "until": 0.0, "guards": [0], "n": 1}}}
	var a1: Dictionary = acc.snapshot()
	var acc2 := AccountState.new()
	acc2.restore(norm.call(a1))
	var a2: Dictionary = acc2.snapshot()
	check(norm.call(a1.calendar) == norm.call(a2.calendar) and norm.call(a1.activity) == norm.call(a2.activity) and norm.call(a1.sect) == norm.call(a2.sect),
		"the account's calendar, activity and sect (with its mines) round-trip")

## S49 territory: spirit mines taken from rival sects, their carts, the old holders' timers, the guards.
func territory_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var sect_was: Dictionary = Game.account.sect.duplicate(true)
	var stones0: int = Game.economy.balance("spirit_stone")
	var cfg: Dictionary = ContentDB.config("territory")
	var base_was: float = float(cfg.contest.base)
	var t0 := Clock.now_utc()
	var seen := {"claimed": 0, "contested": 0, "defended": [], "lost": [], "collected": 0}
	GameEvents.subscribe("mine_claimed", func(_p): seen.claimed += 1, 200)
	GameEvents.subscribe("mine_contested", func(_p): seen.contested += 1, 200)
	GameEvents.subscribe("mine_defended", func(p): seen.defended.append(str(p.by)), 200)
	GameEvents.subscribe("mine_lost", func(p): seen.lost.append(int(p.stones)), 200)
	GameEvents.subscribe("mine_collected", func(p): seen.collected += int(p.stones), 200)
	# Five mines in field rooms, each held by one of three rival sects with guards and a warden.
	var ms: Array = ContentDB.all("territory")
	var placed := 0
	for m in ms:
		if Game.sect.rival(str(m.sect)).is_empty(): continue
		for o in ContentDB.room(str(m.room)).get("objects", []):
			if str(o.type) == "spirit_mine" and str(o.get("mine", "")) == str(m.id): placed += 1
	check(ms.size() == 5 and placed == 5, "five mines, each a vein in its room and held by a rival sect")
	var armed := 0
	for r in cfg.sects:
		if not ContentDB.entry("enemies", str(r.disciple)).is_empty() and not ContentDB.entry("enemies", str(r.warden)).is_empty() \
			and not SpriteCache.prop(str(r.banner)).is_empty(): armed += 1
	check(armed == (cfg.sects as Array).size() and armed == 3, "every rival has guards, a warden and a banner")
	# No sect, no mine.
	Game.account.sect = {}
	check(Game.sect.assault_block(c, "lower_pit_seam") == Tx.t("sim.sect.mine_no_sect"), "only a sect can hold a mine")
	Game.account.sect = {"name": "Test", "emblem": [0, 0], "level": 1, "prestige": 0, "buildings": {"sect_hall": 1}, "queue": [], "candidates": [],
		"candidate_day": Clock.reset_day(t0), "expeditions": [], "disciples": [{"name": "Wei", "level": 5, "trait": "green_thumb"}, {"name": "Lan", "level": 3, "trait": "green_thumb"}]}
	check(Game.sect.mine_cap() == 1 and Game.sect.assault_block(c, "grey_pools_seep") == Tx.t("sim.sect.needs_sect_level") % 2, "a new sect holds one mine; the Grey Pools needs sect level 2")
	# Taking the Lower Pit: at the mine, its guards and the warden; the warden falls and the mine is yours.
	Game.world.load_room(c, "wp_west", "")
	GameEvents.flush()
	check(str(Game.submit({"type": "assault_mine", "mine": "lower_pit_seam"}).get("reason", "")) == "wrong_room", "you fight for a mine at the mine")
	Game.world.load_room(c, "sq_lower_pit", "")
	GameEvents.flush()
	Game.actor_state(c.id).plane = Vector2(1100, 870)
	Game.actor_state(c.id).altitude = 0.0
	var dlg: Dictionary = Game.world.interact(c, "mine_lower_pit_seam")
	var offers := false
	for choice in dlg.get("dialogue", {}).get("choices", []):
		if str(choice.get("intent", {}).get("type", "")) == "assault_mine": offers = true
	check(offers, "the vein offers to take the mine (%s)" % str(dlg).left(300))
	check(Game.submit({"type": "assault_mine", "mine": "lower_pit_seam"}).get("ok", false) and str(Game.room_rt.event.get("id", "")) == "mine_assault",
		"the fight for the mine starts")
	GameEvents.flush()
	var wardens: Array = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "ironpine_warden")
	var guards: Array = Game.room_rt.living_enemies().filter(func(e): return e.def_id == "ironpine_disciple")
	check(wardens.size() == 1 and int(wardens[0].level) == 12 and guards.size() == 3 and guards.all(func(e): return int(e.level) == 9),
		"three Ironpine guards at Level 9 and their warden at 12")
	var p0: int = int(Game.sect.sect().prestige)
	Game.combat.apply_execute(wardens[0], c.id)
	GameEvents.flush()
	check(Game.sect.holds("lower_pit_seam") and not Game.room_rt.event.get("active", false) and seen.claimed == 1 and int(Game.sect.sect().prestige) == p0 + 30,
		"the warden falls: the mine is yours (+30 Prestige)")
	Game.sect.sect().level = 2
	check(Game.sect.assault_block(c, "grey_pools_seep") == Tx.t("sim.sect.mine_cap") % 1, "one more mine only at sect level 3")
	# The carts: a stone an hour, a day's worth at most; only whole stones leave.
	Clock.override_utc = t0 + 5.5 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 5, "five and a half hours: five stones")
	check(Game.submit({"type": "collect_mine", "mine": "lower_pit_seam"}).get("ok", false) and Game.economy.balance("spirit_stone") == stones0 + 5, "collected")
	Clock.override_utc = t0 + 6.1 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 1, "the half hour left behind still counts")
	Clock.override_utc = t0 + 60.0 * 3600.0
	check(Game.sect.mine_stored("lower_pit_seam") == 24, "the carts hold a day's worth")
	# Guards: posted and recalled; a guard cannot go on an expedition; more guards hold better.
	var ch0: float = Game.sect.guard_chance("lower_pit_seam")
	check(Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 0}).get("ok", false) and Game.sect.guard_chance("lower_pit_seam") > ch0,
		"a guard posted: the mine is likelier to hold")
	var exr := Game.submit({"type": "send_expedition", "region": "willow_path", "hours": 1, "disciples": [0]})
	check(str(exr.get("reason", "")) == "busy", "a guard stays at the mine (%s)" % str(exr))
	# (S25 expeditions: the one who is home goes, and comes back with the region's goods for every hour away.)
	var silver_ex: int = Game.economy.balance("silver_tael")
	var moss0: int = c.inventory.count("willow_moss")
	check(Game.submit({"type": "send_expedition", "region": "willow_path", "hours": 1, "disciples": [1]}).get("ok", false), "a disciple at home can go")
	check(str(Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1}).get("reason", "")) == "busy", "and cannot stand guard while away")
	Clock.override_utc = t0 + 61.0 * 3600.0
	var back: Dictionary = Game.submit({"type": "collect_expedition", "index": 0})
	check(back.get("ok", false) and (not back.success or (Game.economy.balance("silver_tael") >= silver_ex + 60 and c.inventory.count("willow_moss") == moss0 + 3)),
		"the expedition comes home (%s)" % str(back))
	Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1})
	Game.submit({"type": "guard_mine", "mine": "lower_pit_seam", "index": 1})
	check((Game.sect.mines().lower_pit_seam.guards as Array) == [0], "a guard recalled")
	c.inventory.bag.fill(null)
	# The old holder comes back on its timer: hold it in person.
	var st: Dictionary = Game.sect.mines().lower_pit_seam
	var due: float = float(st.contest)
	var days := (due - t0) / 86400.0
	check(days >= 2.0 and days <= 4.0, "the Ironpine Gate come back within two to four days (%.1f)" % days)
	Clock.override_utc = due + 60.0
	Game.sect._tick_mines(Clock.now_utc())
	GameEvents.flush()
	check(bool(st.contested) and seen.contested == 1 and is_equal_approx(float(st.until), due + 12.0 * 3600.0), "a contest opens with twelve hours to answer it")
	check(Game.submit({"type": "defend_mine", "mine": "lower_pit_seam"}).get("ok", false) and str(Game.room_rt.event.get("id", "")) == "mine_defence", "holding the mine starts its fight")
	GameEvents.flush()
	Game.world._end_event(c, Game.room_rt, true)
	GameEvents.flush()
	check(not bool(st.contested) and seen.defended == ["you"] and float(st.contest) > Clock.now_utc() + 2.0 * 86400.0 - 1.0, "held: the next visit is days away")
	# Away while they come: the guards decide it when the window closes; a lost mine takes its carts with it.
	cfg.contest.base = -5.0
	Clock.override_utc = float(st.contest) + 13.0 * 3600.0
	Game.sect._tick_mines(Clock.now_utc())
	GameEvents.flush()
	check(not Game.sect.holds("lower_pit_seam") and seen.lost.size() == 1 and int(seen.lost[0]) == 24, "the guards fall: the mine and its 24 stones are lost")
	check(Game.sect.guarding().is_empty(), "the guards come home")
	# Restore.
	cfg.contest.base = base_was
	Clock.override_utc = -1.0
	GameEvents.unsubscribe_object(self)
	Game.account.sect = sect_was
	Game.economy.apply_currency("spirit_stone", stones0 - Game.economy.balance("spirit_stone"), "test")
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

## S49 the mortal kingdom (county jobs, favour, the relief fund, non-interference) and the leisure arts (guqin, chess).
func mortal_leisure_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	var room_was: String = Game.room_rt.room_id if Game.room_rt else ""
	var mortal_was: Dictionary = c.relations.mortal.duplicate(true)
	var rel_was := [c.relations.merit, c.relations.sin, c.relations.alignment, c.relations.fame]
	var titles_was: Array = c.cultivator.titles.duplicate()
	var active_title_was: String = c.cultivator.active_title
	var cd_was: Dictionary = c.cooldowns.duplicate(true)
	var silver0: int = Game.economy.balance("silver_tael")
	var realm_was: String = c.cultivator.realm_key
	var qp_was: float = c.cultivator.qp
	var daos_was: Dictionary = c.cultivator.daos.duplicate(true)
	c.inventory.bag.fill(null)
	# County jobs: three a day, fit for your Level, taken as soon as the board is read; the same three all day.
	c.relations.mortal = {}
	var jobs: Array = Game.relations.county_jobs(c)
	check(jobs.size() == 3 and jobs.all(func(q): return c.quests.is_active(str(q)) and str(Game.quest.quest_def(c, str(q)).kind) == "mortal"), "three county jobs are posted and taken")
	check(Game.relations.county_jobs(c) == jobs, "the same jobs all day")
	# Favour: a job pays 10; the tiers name you and grant the county's titles; the top one earns a discount.
	var f0 := Game.relations.favour(c)
	Game.apply_effects(c.id, Game.quest.quest_def(c, str(jobs[0])).get("rewards", []), "test")
	GameEvents.flush()
	check(Game.relations.favour(c) == f0 + 10, "a finished county job earns favour")
	Game.relations.apply_favour(c.id, 150 - Game.relations.favour(c), "test")
	check(str(Game.relations.favour_tier(c).id) == "friend" and c.cultivator.titles.has("friend_of_the_county"), "150 favour: Friend of the County, and its title")
	check(Game.relations.shop_discount(c, "stoneford_tea") < 0.05 or not Game.relations.county_discount(c, "stoneford_tea") > 0.0, "no county discount yet")
	Game.relations.apply_favour(c.id, 400 - Game.relations.favour(c), "test")
	check(near(Game.relations.county_discount(c, "stoneford_tea"), 0.05) and Game.relations.shop_discount(c, "stoneford_tea") >= 0.05, "a Benefactor pays 5% less at Stoneford's tea house")
	check(near(Game.relations.county_discount(c, "alliance_factor"), 0.0), "and nothing off elsewhere")
	# The relief fund: silver for merit and favour, once a day at each size.
	Game.economy.apply_currency("silver_tael", 2000 - Game.economy.balance("silver_tael"), "test")
	var m0: int = c.relations.merit
	var fv: int = Game.relations.favour(c)
	check(Game.submit({"type": "donate_relief", "tier": "small"}).get("ok", false) and Game.economy.balance("silver_tael") == 1900
		and c.relations.merit == m0 + 1 and Game.relations.favour(c) == fv + 3, "100 silver to the relief fund: +1 merit, +3 favour")
	check(str(Game.submit({"type": "donate_relief", "tier": "small"}).get("reason", "")) == "today", "once a day at each size")
	check(str(Game.submit({"type": "donate_relief", "tier": "grand"}).get("reason", "")) == "silver", "a grand gift needs 10,000 silver")
	# Non-interference: a technique in a mortal town from Qi Kindling up is sin, once a minute at most.
	Game.world.load_room(c, "lf_village", "")
	GameEvents.flush()
	c.cultivator.realm_key = "qi_kindling_3"
	var s0: int = c.relations.sin
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.flush()
	check(c.relations.sin == s0 + 5, "a technique among the villagers of Lotus Ferry: +5 sin, once a minute (%d)" % (c.relations.sin - s0))
	Game.world.load_room(c, "rm_marsh_edge", "")
	GameEvents.flush()
	var s1: int = c.relations.sin
	c.relations.mortal["warned_s"] = -INF
	GameEvents.emit_event("technique_used", {"actor": c.id, "technique": "x", "hits": 1, "targets": 0})
	GameEvents.flush()
	check(c.relations.sin == s1, "in the wild it is only a technique")
	c.cultivator.realm_key = realm_was
	# The guqin: needs the instrument; the better the playing, the faster meditation runs; then the hands rest.
	c.cooldowns.erase("guqin_until")
	check(str(Game.submit({"type": "play_guqin", "score": 1.0}).get("reason", "")) == "no_guqin", "no guqin, no music")
	Game.inventory.apply_add(c.id, "guqin", 1, "test")
	var acc0: float = c.stats.value("accumulation_rate")
	var gq := Game.submit({"type": "play_guqin", "score": 1.0})
	check(gq.get("ok", false) and near(float(gq.bonus), 0.15) and near(c.stats.value("accumulation_rate"), acc0 + 0.15), "a perfect piece: meditation +15% for half an hour")
	check(str(Game.submit({"type": "play_guqin", "score": 1.0}).get("reason", "")) == "resting", "then the fingers rest")
	check(near(float(Game.progression.play_guqin(c, 0.0).get("bonus", -1.0)), -1.0), "(still resting)")
	# Chess at an insight site: today's problem is the same on every device; the right point, once a day.
	var pz: Dictionary = Game.progression.chess_of("insight_hu")
	check(not pz.is_empty() and pz == Game.progression.chess_of("insight_hu"), "an insight site's problem for today is fixed")
	c.cooldowns.erase("chess:insight_hu")
	var wrong := "A" if str(pz.answer) != "A" else "B"
	check(not Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": wrong}).get("right", true), "a wrong point is wrong")
	check(str(Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": str(pz.answer)}).get("reason", "")) == "done", "one answer a day at each stone")
	c.cooldowns.erase("chess:insight_hu")
	var q0: float = c.cultivator.qp
	var ins0: float = 0.0
	for d in c.cultivator.daos: ins0 += float(c.cultivator.daos[d].get("insight", 0.0))
	check(Game.submit({"type": "solve_chess", "site": "insight_hu", "choice": str(pz.answer)}).get("right", false), "the right point is right")
	var ins1: float = 0.0
	for d in c.cultivator.daos: ins1 += float(c.cultivator.daos[d].get("insight", 0.0))
	check(ins1 > ins0 or c.cultivator.qp > q0 or c.cultivator.state != "accumulating", "and brings insight (or, before any Dao, a little progress)")
	# Restore.
	c.relations.mortal = mortal_was
	c.relations.merit = int(rel_was[0])
	c.relations.sin = int(rel_was[1])
	c.relations.alignment = int(rel_was[2])
	c.relations.fame = int(rel_was[3])
	c.cultivator.titles = titles_was
	c.cultivator.active_title = active_title_was
	c.cooldowns = cd_was
	c.cultivator.qp = qp_was
	c.cultivator.daos = daos_was
	for q in jobs:
		c.quests.active.erase(str(q))
		c.quests.tracked.erase(str(q))
		c.quests.daily.erase(str(q))
	Game.economy.apply_currency("silver_tael", silver0 - Game.economy.balance("silver_tael"), "test")
	c.inventory.bag.fill(null)
	if room_was != "": Game.world.load_room(c, room_was, "")
	GameEvents.flush()

func _seeded(seed: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = seed
	return r

func tribulation_suite() -> void:
	var c = Game.active()
	if c == null or Game.actor_state(c.id) == null: return
	c.inventory.bag.fill(null)
	var t1 := Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	check(str(t1.get("pending", "")) == "tribulation" and (t1.bolts as Array).size() == 3, "a Heaven pill faces 3 bolts")
	var last := {}
	for i in 3: last = Game.crafting.tribulation_shield(c, i, 0.05)
	var got := str(last.get("quality", ""))
	if str(last.get("pending", "")) == "soul": got = str(Game.crafting.catch_pill_soul(c, 0.0).get("quality", ""))
	check(got in ["pill_halo", "pill_soul"] and c.inventory.count("soul_soothing_pill") >= 1, "every bolt held: the Halo holds (or rises), and the pills are yours (%s)" % got)
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	Game.crafting.tribulation_shield(c, 0, 0.0)
	Game.crafting.tribulation_shield(c, 1, 0.9)
	var miss := Game.crafting.tribulation_shield(c, 2, 0.0)
	check(str(miss.get("quality", "")) == "perfect", "one bolt missed: the pills drop to Perfect")
	check((Game.crafting.begin_tribulation(c, "sage_condensing_pill", 1, "pill_halo", "charcoal", {}).bolts as Array).size() == 5, "a Mystic pill faces 5 bolts")
	Game.crafting.tribulations.erase(c.id)
	check((Game.crafting.begin_tribulation(c, "sovereign_settling_pill", 1, "pill_halo", "charcoal", {}).bolts as Array).size() == 9, "a Sage pill: 9 bolts, the most there are")
	Game.crafting.tribulations.erase(c.id)
	# The Pill Soul flees; a missed catch settles the batch as Pill Halo, never loses it.
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 2, "pill_soul", "charcoal", {})
	var fl := {}
	for i in 3: fl = Game.crafting.tribulation_shield(c, i, 0.0)
	check(str(fl.get("pending", "")) == "soul", "a Soul pill that comes through flees the furnace")
	var n0: int = c.inventory.count("soul_soothing_pill")
	var cp := Game.crafting.catch_pill_soul(c, 0.8)
	check(not cp.get("caught", true) and str(cp.get("quality", "")) == "pill_halo" and c.inventory.count("soul_soothing_pill") >= n0 + 2,
		"a missed catch: the batch settles as Pill Halo, not lost")
	# A tribulation left unfinished settles when the next craft begins: every unanswered bolt struck.
	Game.crafting.begin_tribulation(c, "soul_soothing_pill", 1, "pill_halo", "charcoal", {})
	var before: int = c.inventory.count("soul_soothing_pill")
	Game.crafting.craft_step(c, "healing_pill", "alchemy", 0.0)
	check(not Game.crafting.tribulations.has(c.id) and c.inventory.count("soul_soothing_pill") == before + 1, "an abandoned tribulation settles, and its pills still come")
	# A shop that sells several recipe scrolls sells the one asked for.
	Game.economy.apply_currency("silver_tael", 5000, "test")
	c.crafting.recipes.erase("qi_refining_pill")
	var realm_was: String = c.cultivator.realm_key
	if ProgressionRules.realm_index(realm_was) < ProgressionRules.realm_index("heart_tempering_5"): c.cultivator.realm_key = "heart_tempering_5"
	var bs := Game.submit({"type": "buy", "shop": "mei_qing_recipes", "item": "recipe_scroll", "count": 1, "learn": "qi_refining_pill"})
	check(bs.get("ok", false) and c.crafting.recipes.has("qi_refining_pill"), "the Recipe Box sells the Qi Refining scroll asked for, not the first on the shelf")
	c.cultivator.realm_key = realm_was
	c.inventory.bag.fill(null)

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
		check(not chest.is_empty() and float(chest.get("alt", 0)) >= high.base - 1.0, "the chest waits up high (on the room's highest tier, S43)")
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
	var rel: RelationsState = c.relations
	rel.merit = 0
	rel.merit_used.clear()
	Game.apply_effects(c.id, [{"kind": "add_merit", "amount": 100, "reason": "test"}], "test")
	check(ProgressionRules.merit_step(c) == 1 and int(Game.progression.query_breakthrough(c).get("merit", 0)) == 1, "100 merit eases a great breakthrough")
	rel.merit_used[ProgressionRules.great_realm(cu.realm_key)] = true
	check(ProgressionRules.merit_step(c) == 0, "once in each great realm")
	var hd0 := cu.heart_demon
	Game.apply_effects(c.id, [{"kind": "add_sin", "amount": 30, "reason": "test"}], "test")
	check(rel.sin >= 30 and near(cu.heart_demon, hd0 + 3.0), "sin feeds the heart demon (+1 per 10 sin)")
	Game.quest.apply_flag(c.id, "path_independent")
	Unlocks.force_unlock(c.id, "shop")
	Game.economy.apply_currency("spirit_stone", 100, "test")
	var sin0: int = rel.sin
	var bought := Game.economy.buy(c, "free_market", "manual_page", 1, -1)
	GameEvents.flush()
	check(bought.get("ok", false) and rel.sin == sin0 + 2, "Broker Mu's back room stains the ledger (+2 sin) %s" % str(bought.get("reason", "")))
	# A named debt comes due as a letter.
	var mails0: int = Game.account.mail.size() if Game.account.get("mail") is Array else 0
	Game.apply_effects(c.id, [{"kind": "record_debt", "id": "test_debt", "due_h": 0.0, "mail": "gu_repays", "attachments": [{"currency": "spirit_stone", "amount": 1}]}], "test")
	Game.relations.debt_clock = 0.0
	Game.relations.tick(0.1)
	check(bool(rel.debts.get("test_debt", {}).get("paid", false)), "a debt that falls due is repaid by letter")
	rel.debts.erase("test_debt")
	# Furnace and fire (S44): the furnace slot holds one furnace instance; the bronze one holds three; charcoal stops
	# at Perfect; a named furnace or a flame reaches Soul.
	Unlocks.force_unlock(c.id, "alchemy")
	c.inventory.furnace = null
	c.inventory.bag.fill(null)
	Game.inventory.apply_add(c.id, "bronze_furnace", 1, "test")
	var fu: Dictionary = Game.crafting.furnace_of(c)
	check(str(fu.id) == "bronze_furnace" and int(fu.batch) == 3 and c.inventory.furnace != null and c.inventory.furnace.has("uid"),
		"the first furnace goes into the empty furnace slot, three to a batch")
	check(near(float(fu.get("yield", 1.0)), 0.0) and near(float(fu.get("filter", 1.0)), 0.0), "the bronze furnace has no filter and no extra pill")
	check(Game.crafting.rare_allowed(fu, "charcoal").is_empty() and Game.crafting.rare_allowed(fu, "earth_fire") == ["pill_grain"]
		and "pill_soul" in Game.crafting.rare_allowed(fu, "heavenly_flame"), "charcoal stops at Perfect, Earth Fire reaches Grain, a Heavenly Flame reaches Soul")
	check("pill_soul" in Game.crafting.rare_allowed(ContentDB.item("nine_dragon_cauldron").furnace, "charcoal"), "the Nine-Dragon Cauldron reaches Soul on any fire")
	var nd: Dictionary = ContentDB.item("nine_dragon_cauldron").furnace
	check(int(nd.batch) == 8 and near(float(nd.band), 0.12) and str(nd.get("element", "")) == "water", "the Nine-Dragon Cauldron: eight a batch, +12% heat, Water")
	check(str(ContentDB.room("ds_abbots_sanctum").get("objects", []).filter(func(o): return str(o.get("id", "")) == "vault")[0].get("loot", "")) == "abbots_vault"
		and ContentDB.entry("loot_tables", "abbots_vault").get("guaranteed", []).any(func(g): return str(g.item) == "nine_dragon_cauldron"),
		"the Nine-Dragon Cauldron waits in the Drowned Abbot's sealed vault")
	var batch_try := Game.crafting.craft(c, "healing_pill", 4, [], "alchemy")
	check(str(batch_try.get("reason", "")) == "batch", "a bronze furnace refuses a batch of four")
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var any_rare := false
	for i in 400:
		if Game.crafting._rare_pill_quality(c, [1.0, 1.0, 1.0], rng, []) != "perfect": any_rare = true
	check(not any_rare, "no rare quality ever comes out of charcoal")
	# A better furnace sits in the bag until you set it; enhancement steadies its heat 1% a level.
	Game.inventory.apply_add(c.id, "jadeiron_furnace", 1, "test")
	check(str(Game.crafting.furnace_of(c).id) == "bronze_furnace", "a second furnace waits in the bag")
	var jf: int = _bag_index(c, "jadeiron_furnace")
	check(Game.submit({"type": "equip", "index": jf}).get("ok", false) and str(Game.crafting.furnace_of(c).id) == "jadeiron_furnace"
		and c.inventory.count("bronze_furnace") == 1, "setting a furnace swaps the old one back into the bag")
	check(near(Game.crafting.band_mult(c, "beast_fire"), 1.2), "Beast Fire in a Jadeiron Furnace widens the band by 20%")
	c.inventory.furnace.enhance = 3
	check(near(float(Game.crafting.furnace_of(c).band), 0.08), "a +3 Jadeiron Furnace holds its heat 3%% steadier (%.2f)" % float(Game.crafting.furnace_of(c).band))
	c.inventory.furnace.enhance = 0
	# The filter takes out its share of each miss; a furnace of the pill's element adds 5%.
	check(str(ContentDB.entry("recipes", "qi_refining_pill").get("element", "")) == "water", "Qi Refining is a Water pill")
	var qr := ContentDB.entry("recipes", "qi_refining_pill")
	var base_q: float = Game.crafting.quality_score(c, "alchemy", {}, qr, [0.5, 0.5, 0.5])
	check(near(Game.crafting.quality_score(c, "alchemy", Game.crafting.furnace_of(c), qr, [0.5, 0.5, 0.5]) - base_q, 0.05),
		"a Jadeiron Furnace strains out a tenth of each miss (+0.05 on half-missed strikes)")
	check(near(Game.crafting.quality_score(c, "alchemy", ContentDB.item("nine_dragon_cauldron").furnace, qr, [0.5, 0.5, 0.5]) - base_q, 0.15),
		"the Nine-Dragon Cauldron: a fifth of each miss, and +5% for a Water pill")
	# Durability: a cracked furnace refines nothing until it is mended at a forge.
	c.inventory.furnace.durability = 0
	check(Game.crafting.furnace_of(c).get("cracked", false) and str(Game.crafting.craft(c, "healing_pill", 1, [], "alchemy").get("reason", "")) == "cracked",
		"a cracked furnace refuses to refine")
	var mend := Game.crafting.mend_cost(c.inventory.furnace)
	check(str(mend.metal) == "jadeiron" and int(mend.count) == 20, "mending a Jadeiron Furnace from nothing takes 20 jadeiron")
	c.inventory.furnace.durability = 100
	# Beast Fire burns a core of rank 2 or more; a Pebble Imp's core is too weak.
	for k in 4:
		var old_core: int = _bag_index(c, "pebble_core")
		if old_core < 0: break
		c.inventory.bag[old_core] = null
	check(not "beast_fire" in Game.crafting.fires_available(c), "no core, no Beast Fire")
	Game.inventory.apply_add(c.id, "pebble_core", 1, "test")
	check(not "beast_fire" in Game.crafting.fires_available(c), "a rank-1 Pebble Core is too weak for Beast Fire")
	Game.inventory.apply_add(c.id, "serpent_core", 1, "test")
	check("beast_fire" in Game.crafting.fires_available(c) and Game.crafting._core_to_burn(c) == "serpent_core", "a rank-2 core lights Beast Fire")
	# Old saves: furnaces in the key-item pouch become furnace instances, the best in the slot.
	var inv2 := InventoryState.new()
	inv2.restore({"bag": [], "key_items": [{"id": "bronze_furnace", "count": 1}, {"id": "earth_vein_furnace", "count": 1}, {"id": "old_pickaxe", "count": 1}]})
	check(inv2.furnace != null and str(inv2.furnace.id) == "jadeiron_furnace" and inv2.count("bronze_furnace") == 1 and inv2.count("old_pickaxe") == 1,
		"an old save's furnaces become instances: the Jadeiron in the slot, the bronze in the bag")
	# The valley's Heavenly Flame rides the Forgotten Monastery's elite Weeping Lantern.
	check((ContentDB.entry("enemies", "weeping_lantern").get("elite_first_defeat", []) as Array).has("mist_lantern_flame")
		and not (ContentDB.entry("enemies", "drowned_abbot").get("first_defeat", []) as Array).has("cold_lamp_flame"),
		"the Mist Lantern Flame comes from the Weeping Lantern elite")
	c.inventory.bag.fill(null)
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
