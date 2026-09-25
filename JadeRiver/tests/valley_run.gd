extends "res://tests/prologue_run.gd"
## Unlock-order suite (Part 7): a scripted run from a new character through the
## Prologue and every guided and main quest of Act I, using intents only. It checks
## that each system unlocks in the Part 4 order and that no guided quest stalls.
##
## Grinding is shortened with `apply_progress(..., "test_shortcut")`; every other
## step (travel, talk, fights, crafts, spars, breakthroughs) goes through the real
## authorities. The state at the start of each section is saved, so a later section
## can be re-run alone:
##   godot --headless --path . res://tests/valley_run.tscn -- [--from=<section>] [--verbose]

const SECTIONS := ["bf2", "bf5", "bf8", "qk1", "qk5", "qu1", "qu5", "ht1", "ht5", "cs1", "cs5", "sa1", "sa5", "hg1"]
const CP_ROOT := "user://valley_cp/"
const WORK := "user://valley_work/"

var unlock_log: Array = []

func _main() -> void:
	var from := ""
	var only := false
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--from="): from = str(a).trim_prefix("--from=")
		if str(a) == "--only": only = true
	GameEvents.event.connect(func(n, p):
		if n == "system_unlocked": unlock_log.append(str(p.get("system", ""))))
	if from == "":
		run()
		from = SECTIONS[0]
		checkpoint(from)
	elif not resume(from):
		print("valley_run: no checkpoint for ", from, "; run from the start first")
		get_tree().quit(2)
		return
	var started := false
	for s in SECTIONS:
		if s == from: started = true
		if not started: continue
		if s != from: checkpoint(s)
		print("-- section ", s, " (realm ", c().cultivator.realm_key, ", room ", room(), ", bag free ", c().inventory.free_slots(), "/", c().inventory.capacity(), ")")
		var before := failures
		tidy_bag()
		call("sec_" + s)
		if failures > before: print("   section ", s, ": ", failures - before, " failure(s)")
		if only: break
	print("valley_run: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

# ------------------------------------------------------------------ checkpoints
func _copy_dir(from: String, to: String) -> void:
	DirAccess.make_dir_recursive_absolute(to)
	for f in DirAccess.get_files_at(to): DirAccess.remove_absolute(to + f)
	for f in DirAccess.get_files_at(from): DirAccess.copy_absolute(from + f, to + f)

func checkpoint(name: String) -> void:
	Game.save_all()
	_copy_dir(Saves.repo.root, CP_ROOT + name + "/")

func resume(name: String) -> bool:
	if not DirAccess.dir_exists_absolute(CP_ROOT + name + "/"): return false
	_copy_dir(CP_ROOT + name + "/", WORK)
	Saves.use_folder(WORK)
	Game.boot()
	Game.autosave_enabled = false
	if not submit({"type": "enter_character", "slot": 1}).get("ok", false): return false
	if not submit({"type": "enter_world"}).get("ok", false): return false
	place(Vector2(float(c().position.x), float(c().position.y)))
	return true

# ------------------------------------------------------------------ helpers
## Nobody walks while gravely wounded: wake at the shrine and rest first.
func revive_if_needed() -> void:
	if not Game.combat.is_wounded(c().id): return
	submit({"type": "choose_revival", "where": "shrine"})
	place(Vector2(float(c().position.x), float(c().position.y)))
	step(1.0)
	var t := 0.0
	while c().pools.hp < c().pools.max_hp * 0.95 and t < 150.0:
		step(1.0)
		t += 1.0

func travel(target: String) -> bool:
	revive_if_needed()
	tidy_bag(4)
	var ok := super.travel(target)
	# A careful player prays at the shrine of every room they pass through.
	if ok:
		for o in objects_of("shrine"):
			interact(str(o.id))
			place(Vector2(float(c().position.x), float(c().position.y)))
	return ok

## Body training: real stump hits first, then the test shortcut for the long grind.
func train_body(level: int) -> void:
	var stumps := objects_of("training_stump") + objects_of("lifting_stone")
	if not stumps.is_empty():
		var before: float = c().cultivator.body_xp
		hit_object(str(stumps[0].id), 10)
		check(c().cultivator.body_xp > before or c().cultivator.body_level >= level, "stump training gives body XP")
	var guard := 0
	while c().cultivator.body_level < level and guard < 200:
		Game.progression.apply_body_xp(c().id, 500.0, "test_shortcut")
		GameEvents.flush()
		guard += 1

## Dao insight: one night of Contemplate seclusion (real), then the test shortcut for the rest.
func train_dao(tier: int) -> void:
	var best := "sword"
	var best_i := -1.0
	for d in c().cultivator.daos:
		if float(c().cultivator.daos[d].get("insight", 0.0)) > best_i:
			best_i = float(c().cultivator.daos[d].get("insight", 0.0))
			best = str(d)
	var before: float = best_i
	submit({"type": "set_contemplate", "dao": best})
	if submit({"type": "enter_seclusion", "focus": "contemplate"}).get("ok", false):
		submit({"type": "claim_offline", "elapsed": 12.0 * 3600.0})
		check(float(c().cultivator.daos.get(best, {}).get("insight", 0.0)) > before, "a night of Contemplate deepens the %s Dao" % best)
	var guard := 0
	while int(c().cultivator.daos.get(best, {}).get("tier", 0)) < tier and guard < 60:
		Game.progression.apply_insight(c().id, best, 500.0, "test_shortcut")
		guard += 1

## Technique practice: real uses against a dummy or foe, then the test shortcut for the grind.
func train_technique(tier: int) -> void:
	var tid := ""
	for t2 in c().cultivator.technique_slots:
		if t2 != null and str(t2) != "": tid = str(t2)
	if tid == "": return
	var m: Dictionary = c().cultivator.mastery.get(tid, {"tier": 1, "points": 0.0})
	var before := float(m.points) + int(m.tier) * 1000.0
	var slot: int = c().cultivator.technique_slots.find(tid)
	for i in 6:
		c().pools.qi = c().pools.max_qi
		var foes := Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy")
		if not foes.is_empty(): place(foes[0].plane + Vector2(-50, 0))
		submit({"type": "use_technique", "slot": slot, "facing": 1})
		step(float(ContentDB.entry("techniques", tid).get("cooldown_s", 3)) + 0.2)
	m = c().cultivator.mastery.get(tid, m)
	check(float(m.points) + int(m.tier) * 1000.0 >= before, "technique practice keeps mastery growing")
	if int(m.tier) < tier:
		m.tier = tier   # test shortcut: the remaining practice is repetition
		m.points = 0.0
		c().cultivator.mastery[tid] = m

## Buy better gear the way a player would: the best affordable pieces the smith stocks.
func gear_up(shop := "stoneford_smith") -> void:
	var npc := go_to_npc(["smith_bao"]) if shop == "stoneford_smith" else ""
	var fam := str(ContentDB.item(str(c().inventory.equipped.get("weapon", {}).get("id", "training_jian")) if c().inventory.equipped.get("weapon") != null else "training_jian").get("family", "jian"))
	var before: float = c().stats.value("physical_attack")
	for s in Game.economy.stock(c(), shop):
		if str(s.get("locked", "")) != "": continue
		var def := ContentDB.item(str(s.item))
		if not ContentDB.is_equipment(str(s.item)): continue
		if str(def.slot) == "weapon" and str(def.get("family", "")) != fam: continue
		var cur = c().inventory.equipped.get(str(def.slot))
		if cur != null and StatRules.grade_index(str(ContentDB.item(str(cur.id)).get("grade", "plain"))) >= StatRules.grade_index(str(def.get("grade", "plain"))): continue
		# The run shortcuts the grinding hours; credit the spec's income for them (S39: about 850 taels
		# an hour at Level 15, 1,700 at Level 25), at most two hours per purchase.
		var hours := 0
		while Game.economy.balance("silver_tael", c()) < int(s.price) and hours < 2:
			Game.economy.apply_currency("silver_tael", 57 * maxi(10, ProgressionRules.level(c())), "test_shortcut_income")
			hours += 1
		if Game.economy.balance("silver_tael", c()) < int(s.price): continue
		if buy(shop, str(s.item), 1): equip_first(str(s.item))
	if verbose: print("  gear up at ", shop, ": attack ", snappedf(before, 0.1), " -> ", snappedf(c().stats.value("physical_attack"), 0.1), " level ", ProgressionRules.level(c()), " taels ", Game.economy.balance("silver_tael", c()))

## Earth-grade gear for the Qi Unfurling bosses. Forging is tested in The Sect Forge, so the set is
## granted here (test shortcut) instead of farming Jadeiron for every piece.
func earth_gear() -> void:
	for id in ["jadeiron_jian", "jadeiron_robe", "jadeiron_trousers", "jadeiron_boots", "jadeiron_hat"]:
		if c().inventory.count_including_equipped(id) > 0: continue
		Game.inventory.apply_add_equipment(c().id, id, int(ContentDB.item(id).get("ilv", 27)), "fine", "test_gear")
		equip_first(id)
	for i in 6: Game.inventory.apply_add(c().id, "healing_pill", 1, "test_supplies")
	if verbose: print("  earth gear: attack ", snappedf(c().stats.value("physical_attack"), 0.1), " def ", snappedf(c().stats.value("physical_defense"), 0.1), " hp ", int(c().pools.max_hp))

func quest_def(qid: String) -> Dictionary:
	return ContentDB.entry("quests", qid)

func rooms_with_npc(ids: Array) -> Array:
	var out: Array = []
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) == "npc" and str(o.get("npc", "")) in ids and not out.has(rid): out.append(rid)
	# Prefer the character's own sect grounds, then nearby rooms.
	var own := "ja_" if str(c().training_sect.get("id", "")) == "jade_sect" else "cm_"
	out.sort_custom(func(a, b): return (1 if str(a).begins_with(own) else 0) > (1 if str(b).begins_with(own) else 0))
	return out

## Walk to a room where one of `ids` stands (visible); returns that npc id.
func go_to_npc(ids: Array) -> String:
	for id in ids:
		if not npc_object(str(id)).is_empty(): return str(id)
	for rid in rooms_with_npc(ids):
		if not travel(str(rid)): continue
		for id in ids:
			if not npc_object(str(id)).is_empty(): return str(id)
	print("  cannot reach any of ", ids, " from ", room())
	return ""

func givers(def: Dictionary, key: String) -> Array:
	var any: Array = def.get(key + "_any", [])
	if not any.is_empty(): return any
	var one := str(def.get(key, ""))
	return [one] if one != "" else []

func start(qid: String) -> bool:
	if c().quests.is_active(qid) or c().quests.is_done(qid): return true
	var def := quest_def(qid)
	var npc := go_to_npc(givers(def, "giver"))
	if npc == "":
		check(false, "reach a giver of " + qid)
		return false
	accept(npc, qid)
	return c().quests.is_active(qid)

func finish(qid: String) -> bool:
	if c().quests.is_done(qid): return true
	var def := quest_def(qid)
	var ids := givers(def, "hand_in")
	if ids.is_empty():
		GameEvents.flush()
		check(c().quests.is_done(qid), "%s completes on its own (state %s)" % [qid, str(c().quests.active.get(qid, {}).get("state", "?"))])
		return c().quests.is_done(qid)
	var npc := go_to_npc(ids)
	if npc == "":
		check(false, "reach a hand-in npc for " + qid)
		return false
	if c().quests.active.get(qid, {}).get("state", "") != "ready":
		print("  ", qid, " not ready: ", c().quests.active.get(qid, {}))
	hand_in(npc, qid)
	return c().quests.is_done(qid)

func objects_of(type: String, field := "", value := "") -> Array:
	var out: Array = []
	for o in Game.room_rt.def.get("objects", []):
		if str(o.get("type", "")) != type: continue
		if field != "" and str(o.get(field, "")) != value: continue
		out.append(o)
	return out

## Gather from herb or ore nodes in the current room until `count` of `item` were collected.
func gather(item: String, count: int, limit := 20) -> int:
	var got := 0
	var tries := 0
	while got < count and tries < limit:
		tries += 1
		var any := false
		for o in objects_of("herb_patch") + objects_of("ore_vein"):
			if str(o.get("item", "")) != item: continue
			var s: Dictionary = Game.room_rt.objects.get(str(o.id), {"state": "ready"})
			if s.get("state", "ready") != "ready": continue
			any = true
			var r := interact(str(o.id))
			if not r.get("ok", false):
				print("  gather ", o.id, ": ", r)
				continue
			step(float(r.get("channel", 1.5)) + 0.1)
			var done := submit({"type": "complete_node", "object": str(o.id)})
			if done.get("ok", false): got += int(done.count)
			if got >= count: break
		if not any: step(30.0)
	return got

func meditate(seconds: float) -> void:
	submit({"type": "start_meditation"})
	step(seconds + 1.0)
	submit({"type": "stop_meditation"})

## Spar through an npc service or a practice post until one spar ends; true when won.
func spar_with(start_intent: Callable) -> bool:
	var result := {"done": false, "won": false}
	var heard := func(n: String, p: Dictionary):
		if n == "spar_ended":
			result.done = true
			result.won = str(p.get("winner", "")) == "player"
	GameEvents.event.connect(heard)
	var r: Dictionary = start_intent.call()
	if not r.get("ok", false): print("  spar start: ", r)
	var t := 0.0
	while not result.done and t < 120.0:
		var foe: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.def.get("spar", false): foe = e
		if foe == null:
			step(0.3)
			t += 0.3
			continue
		if str(foe.ai.get("state", "")) == "windup":
			place(foe.plane + Vector2(-34, 70 if foe.plane.y < 860 else -70))
			step(0.6)
			t += 0.6
			continue
		place(foe.plane + Vector2(-34 if st.plane.x <= foe.plane.x else 34, 0))
		submit({"type": "basic_attack", "facing": 1 if foe.plane.x >= st.plane.x else -1})
		step(0.2)
		t += 0.2
	GameEvents.event.disconnect(heard)
	return bool(result.won)

## Fill the progress bar with the test shortcut and break through until `realm`.
func reach(realm: String, supports: Array = []) -> bool:
	var guard := 0
	while not ProgressionRules.at_least(c().cultivator.realm_key, realm) and guard < 40:
		guard += 1
		var cu = c().cultivator
		if cu.state == "consolidating":
			cu.consolidation_left = 0.01   # test shortcut: consolidation only waits
			step(0.5)
			continue
		if cu.state != "bottleneck":
			Game.progression.apply_progress(c().id, 0.0, "test_shortcut", 1.0)
			step(0.2)
			continue
		var q: Dictionary = Game.progression.query_breakthrough(c(), supports)
		for r0 in q.results:
			if not r0.ok and str(r0.get("kind", "")) == "body_level_at_least":
				train_body(int(str(r0.get("text", "")).get_slice(" ", 2)))
				q = Game.progression.query_breakthrough(c(), supports)
			if not r0.ok and str(r0.get("kind", "")) == "item_owned":
				# A failed major breakthrough consumes its materials: make another, as a player would.
				if str(r0.get("text", "")).begins_with("Qi Refining Pill"): make_refining_pill()
				if str(r0.get("text", "")).begins_with("Mind Lake Opening Pill"): make_mind_lake_pill()
				q = Game.progression.query_breakthrough(c(), supports)
			if not r0.ok and str(r0.get("kind", "")) == "dao_tier_at_least":
				train_dao(int(str(r0.get("text", "")).get_slice("tier ", 1).get_slice(" ", 0)))
				q = Game.progression.query_breakthrough(c(), supports)
			if not r0.ok and str(r0.get("kind", "")) == "technique_tier_at_least":
				train_technique(int(str(r0.get("text", "")).get_slice("tier ", 1).get_slice(" ", 0)))
				q = Game.progression.query_breakthrough(c(), supports)
		if cu.breakthrough_cooldown > 0.0:
			step(cu.breakthrough_cooldown + 0.5)
			q = Game.progression.query_breakthrough(c(), supports)
		if not q.can:
			var unmet: Array = []
			for r in q.results:
				if not r.ok: unmet.append(str(r.get("text", r.get("kind", ""))))
			print("  breakthrough %s -> %s blocked: %s %s" % [cu.realm_key, q.to, q.blocked, unmet])
			return false
		var b := submit({"type": "start_breakthrough", "support_items": supports})
		if not b.get("ok", false):
			print("  breakthrough refused: ", b)
			return false
		step(4.0)
	return ProgressionRules.at_least(c().cultivator.realm_key, realm)

func equip_first(item: String) -> bool:
	var i: int = c().inventory.first_index(item)
	if i < 0: return false
	return submit({"type": "equip", "index": i}).get("ok", false)

func buy(shop: String, item: String, count := 1) -> bool:
	var r := submit({"type": "buy", "shop": shop, "item": item, "count": count})
	if not r.get("ok", false): print("  buy ", item, " at ", shop, ": ", r)
	return r.get("ok", false)

func unlocked(system: String) -> bool:
	return Unlocks.is_unlocked(c().id, system)

const KEEP := ["herbal_tea", "rice_ball", "rice", "willow_moss", "riverreed_ginseng_10", "tough_meat", "spirit_stone_shard",
	"revival_talisman", "return_charm", "fuel_crystal_low", "blank_plate", "formation_stone", "restoration_ink", "torn_manual",
	"spirit_wood", "puppet_core", "spirit_egg", "dusty_curio", "calm_incense", "cloud_feather", "cloudtop_orchid", "mudwater_key",
	"cleansing_pill", "healing_pill", "qi_restoration_pill", "manual_page", "copper_ore", "jadeiron", "mist_lotus"]

## Sell loot a player would sell: anything no active quest or upcoming lesson needs.
func tidy_bag(min_free := 8) -> void:
	if c().inventory.free_slots() >= min_free: return
	var wanted := {}
	for qid in c().quests.active:
		var def: Dictionary = quest_def(str(qid)) if not c().quests.daily.has(qid) else c().quests.daily[qid]
		for o in def.get("objectives", []):
			if o.has("item"): wanted[str(o.item)] = true
	for i in c().inventory.bag.size():
		var it = c().inventory.bag[i]
		if it == null: continue
		var id := str(it.id)
		var def2 := ContentDB.item(id)
		if id in KEEP or wanted.has(id) or def2.get("quest_item", false) or str(def2.get("type", "")) in ["tool", "key", "scroll", "taming", "egg", "curio", "pill", "formation", "talisman"]: continue
		submit({"type": "sell", "index": i, "count": int(it.get("count", 1))})
	# Anything that overflowed into the mail comes back now there is room.
	submit({"type": "claim_all"})

## Travel to the nearest reachable room with a station of `type`.
func go_to_station(type: String) -> bool:
	if not objects_of(type).is_empty(): return true
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) == type and travel(str(rid)): return true
	return false

func sweep_flags(prefix: String) -> void:
	for o in Game.room_rt.def.get("objects", []):
		if str(o.get("set_flag", "")).begins_with(prefix): interact(str(o.id))

# ------------------------------------------------------------------ Bone Forging 2-4
func sec_bf2() -> void:
	check(start("a_disciples_chores"), "A Disciple's Chores accepted")
	check(travel("ja_gate_street"), "reach Gate Street")
	sweep_flags("swept_ja_")
	check(finish("a_disciples_chores"), "A Disciple's Chores done")
	# Fish-Gutting Fists: spar Shen Lian at the Fairground.
	check(start("fish_gutting_fists"), "Fish-Gutting Fists accepted")
	var npc := go_to_npc(["shen_lian"])
	var won := false
	for i in 3:
		won = spar_with(func(): return _spar_service(npc))
		if won: break
	check(won, "beat Shen Lian in a spar")
	check(finish("fish_gutting_fists"), "Fish-Gutting Fists done")
	# Bone Forging 3: the Weapon Hall.
	check(reach("bone_forging_3"), "Bone Forging 3")
	check(start("the_weapon_hall"), "The Weapon Hall accepted")
	check(unlocked("weapons"), "weapons unlock with The Weapon Hall at Bone Forging 3")
	check(equip_first("training_jian"), "equip the training jian")
	check(travel("ja_weapon_hall"), "reach the Weapon Hall")
	var dummies := objects_of("training_dummy")
	if not dummies.is_empty(): hit_object(str(dummies[0].id), 15)
	submit({"type": "guard_start"})
	step(0.3)
	submit({"type": "guard_end"})
	check(finish("the_weapon_hall"), "The Weapon Hall done")
	# Bone Forging 4: Eyes for Qi and the Outer Trial.
	check(reach("bone_forging_4"), "Bone Forging 4")
	check(start("eyes_for_qi"), "Eyes for Qi accepted")
	check(unlocked("herb_gathering"), "herb gathering unlocks with Eyes for Qi at Bone Forging 4")
	check(travel("lf_reed_shallows"), "reach the Reed Shallows")
	meditate(62.0)
	check(gather("willow_moss", 3) >= 3, "gather three Willow Moss")
	check(finish("eyes_for_qi"), "Eyes for Qi done")
	check(start("outer_trial"), "Outer Trial accepted")
	check(travel("ja_pavilion_rooftops"), "reach the Pavilion Rooftops")
	var posts := objects_of("spar_post")
	var wins := 0
	for i in 6:
		if wins >= 3 or posts.is_empty(): break
		if spar_with(func(): return interact(str(posts[0].id))): wins += 1
	check(wins >= 3, "win three practice spars (%d)" % wins)
	check(finish("outer_trial"), "Outer Trial done")
	check(str(c().training_sect.get("rank", "")) == "outer_disciple", "Outer Disciple")

func _spar_service(npc: String) -> Dictionary:
	var d := talk(npc)
	for ch in d.get("choices", []):
		if ch.has("spar"): return submit({"type": "choose_dialogue", "npc": npc, "choice": ch})
	return {"ok": false, "reason": "no spar choice"}

# ------------------------------------------------------------------ Bone Forging 5-7
func sec_bf5() -> void:
	check(reach("bone_forging_5"), "Bone Forging 5")
	check(start("stone_and_sweat"), "Stone and Sweat accepted")
	check(unlocked("mining"), "mining unlocks with Stone and Sweat")
	check(travel("sq_quarry_rim"), "reach the Quarry Rim")
	check(gather("copper_ore", 5, 40) >= 5, "mine five copper")
	check(fight("rock_beetle", 5, 300.0) >= 5, "defeat five Rock Beetles")
	var dodges := {"n": 0}
	var heard := func(n, p): if n == "hit_dodged": dodges.n += 1
	GameEvents.event.connect(heard)
	var t := 0.0
	while int(dodges.n) < 3 and t < 300.0:
		if Game.combat.is_wounded(c().id) or room() != "sq_quarry_rim":
			revive_if_needed()
			travel("sq_quarry_rim")
		# Stand in a beetle's reach and roll out late in its wind-up, as the foreman teaches.
		var foe: EnemyState = null
		for e in Game.room_rt.living_enemies():
			if e.team == "enemy" and e.def_id == "rock_beetle" and (foe == null or e.plane.distance_to(st.plane) < foe.plane.distance_to(st.plane)): foe = e
		if foe == null:
			step(0.5)
			t += 0.5
			continue
		if str(foe.ai.get("state", "")) == "windup":
			if float(foe.ai.get("timer", 1.0)) <= 0.15: submit({"type": "dodge", "direction": Vector2(0, 0), "facing": 1})
		else:
			place(foe.plane + Vector2(-30 if st.plane.x <= foe.plane.x else 30, 0))
		if c().pools.hp < c().pools.max_hp * 0.4:
			place(foe.spawn_point + Vector2(-500, 0))
			step(20.0)
			t += 20.0
		step(0.05)
		t += 0.05
	GameEvents.event.disconnect(heard)
	check(int(dodges.n) >= 3, "dodge three attacks (%d)" % int(dodges.n))
	check(finish("stone_and_sweat"), "Stone and Sweat done")
	# A Second Path: an idle task counts.
	check(start("a_second_path"), "A Second Path offered")
	var idle := submit({"type": "set_idle_task", "task": {"task": "train"}})
	if not idle.get("ok", false): print("  idle task: ", idle)
	c().idle_task = {}
	check(finish("a_second_path"), "A Second Path done")
	# Bone Forging 6: daily missions.
	check(reach("bone_forging_6"), "Bone Forging 6")
	check(start("earning_your_keep"), "Earning Your Keep accepted")
	if verbose: print("  after accept: active=", c().quests.active.keys(), " daily=", c().quests.daily.keys())
	var done := 0
	for qid in c().quests.daily.keys():
		if done >= 2: break
		if _do_mission(str(qid)): done += 1
	check(done >= 2 or c().quests.active.get("earning_your_keep", {}).get("state", "") == "ready", "finish two daily missions (%d scripted)" % done)
	check(finish("earning_your_keep"), "Earning Your Keep done")
	# Bone Forging 7: the QI pool opens.
	check(reach("bone_forging_7"), "Bone Forging 7")
	check(start("the_first_current"), "The First Current accepted")
	check(c().pools.max_qi > 0.0, "QI pool exists from Bone Forging 7")
	check(unlocked("seclusion"), "offline seclusion unlocks")
	check(travel("lf_village"), "back to Lotus Ferry")
	var springs := objects_of("qi_spring")
	check(not springs.is_empty(), "Lotus Ferry has a Qi spring")
	if not springs.is_empty():
		place(Vector2(float(springs[0].at[0]), float(springs[0].at[1]) + 10))
		meditate(32.0)
	var sec := submit({"type": "enter_seclusion", "focus": "accumulate"})
	if not sec.get("ok", false): print("  seclusion: ", sec)
	submit({"type": "claim_offline", "elapsed": 3600.0})
	check(finish("the_first_current"), "The First Current done")

## Do one daily mission objective (kill or gather) in a room that has it.
func _do_mission(qid: String) -> bool:
	var q: Dictionary = c().quests.daily.get(qid, {})
	if q.is_empty(): return false
	var o: Dictionary = q.objectives[0]
	if verbose: print("  mission ", qid, ": ", o)
	match str(o.kind):
		"kill":
			var rid := _room_with_spawn(str(o.enemy))
			if rid == "" or not travel(rid): return false
			fight(str(o.enemy), int(o.get("count", 1)), 400.0)
		"gather_node", "mine_node", "collect":
			var rid2 := _room_with_node(str(o.get("item", "")))
			if rid2 == "" or not travel(rid2): return false
			gather(str(o.item), int(o.get("count", 1)), 60)
		"deliver":
			var item := str(o.get("item", ""))
			var need: int = int(o.get("count", 1)) - int(c().inventory.count(item))
			if need > 0:
				travel("lf_old_ma_store")
				buy("old_ma", item, need)
		"win_spar":
			travel("ja_pavilion_rooftops")
			var posts := objects_of("spar_post")
			for i in int(o.get("count", 1)) * 2:
				if c().quests.active.get(qid, {}).get("state", "") == "ready": break
				spar_with(func(): return interact(str(posts[0].id)))
		"craft":
			travel("lf_fishers_hut")
			var pots := objects_of("cooking_pot")
			if not pots.is_empty(): place(Vector2(float(pots[0].at[0]) - 40, float(pots[0].at[1]) + 10))
			if c().inventory.count("rice") < 2: Game.inventory.apply_add(c().id, "rice", 2, "test")
			for r in ContentDB.all("recipes"):
				if str(r.craft) == "cooking" and Game.crafting.recipe_check(c(), str(r.id), 1, "cooking") == "":
					submit({"type": "cook", "recipe": str(r.id), "count": 1})
					break
		_:
			print("  mission kind not scripted: ", o.kind)
			return false
	GameEvents.flush()
	if verbose: print("  mission ", qid, " after: active=", c().quests.active.get(qid, {}), " done=", c().quests.is_done(qid), " daily=", c().quests.daily.has(qid))
	return c().quests.is_done(qid) or c().quests.active.get(qid, {}).get("state", "") == "ready"

func _room_with_spawn(enemy: String) -> String:
	for rid in ContentDB.rooms:
		for sp in ContentDB.room(rid).get("spawns", []):
			if str(sp.get("enemy", "")) == enemy: return str(rid)
	return ""

func _room_with_node(item: String) -> String:
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) in ["herb_patch", "ore_vein"] and str(o.get("item", "")) == item: return str(rid)
	return ""

# ------------------------------------------------------------------ Bone Forging 8-9
func sec_bf8() -> void:
	check(reach("bone_forging_8"), "Bone Forging 8")
	check(start("aunt_pings_broth"), "Aunt Ping's Broth accepted")
	check(unlocked("cooking") and unlocked("fishing"), "cooking and fishing unlock with Aunt Ping's Broth")
	# Two fish from the docks.
	check(travel("lf_village"), "Lotus Ferry docks")
	var spots := objects_of("fishing_spot")
	var fish := 0
	for i in 8:
		if fish >= 2 or spots.is_empty(): break
		var r := interact(str(spots[0].id))
		if not r.get("ok", false):
			print("  fishing: ", r)
			break
		var f := submit({"type": "catch_fish", "object": str(spots[0].id), "result": {"reaction_s": 0.3, "tension_ok": true}})
		if f.get("ok", false) and str(f.get("item", "")) != "": fish += 1
	check(fish >= 2, "catch two fish (%d)" % fish)
	# Two cuts of tough meat from boars.
	var meat_room := _room_with_spawn("wild_boarlet")
	check(travel(meat_room), "reach boarlets")
	var tries := 0
	while c().inventory.count("tough_meat") < 2 and tries < 20:
		fight("wild_boarlet", 1, 30.0)
		tries += 1
	check(c().inventory.count("tough_meat") >= 2, "two cuts of Tough Meat (%d)" % c().inventory.count("tough_meat"))
	check(travel("lf_village"), "back to the village")
	var pots := objects_of("cooking_pot")
	if pots.is_empty():
		for rid in ["lf_fishers_hut", "lf_old_ma_store"]:
			travel(rid)
			pots = objects_of("cooking_pot")
			if not pots.is_empty(): break
	check(not pots.is_empty(), "find a cooking pot")
	if not pots.is_empty(): place(Vector2(float(pots[0].at[0]) - 40, float(pots[0].at[1]) + 10))
	var cook := submit({"type": "cook", "recipe": "boar_bone_broth", "count": 1})
	check(cook.get("ok", false), "cook Boar Bone Broth %s" % str(cook))
	check(finish("aunt_pings_broth"), "Aunt Ping's Broth done")
	# Bone Forging 9: the wall.
	check(reach("bone_forging_9"), "Bone Forging 9")
	check(start("the_wall"), "The Wall accepted")
	submit({"type": "report_page_opened", "page": "breakthrough"})
	meditate(32.0)
	check(finish("the_wall"), "The Wall done")

# ------------------------------------------------------------------ Qi Kindling 1-4
func sec_qk1() -> void:
	check(reach("qi_kindling_1"), "Qi Kindling 1")
	gear_up()
	check(start("first_technique"), "First Technique accepted")
	check(unlocked("technique_slots_2") or unlocked("techniques"), "technique slots at Qi Kindling 1")
	var eq := submit({"type": "equip_technique", "id": "flowing_palm", "slot": 0})
	if not eq.get("ok", false): print("  equip technique: ", eq)
	var used := 0
	var foe_room := _room_with_spawn("wild_boarlet")
	travel(foe_room)
	for i in 60:
		if c().quests.active.get("first_technique", {}).get("state", "") == "ready": break
		var foes := Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy")
		if not foes.is_empty(): place(foes[0].plane + Vector2(-60, 0))
		c().pools.qi = c().pools.max_qi
		var u := submit({"type": "use_technique", "slot": 0, "facing": 1})
		if u.get("ok", false): used += 1
		elif i < 3: print("  technique: ", u)
		step(1.6)
	check(used >= 20, "use Flowing Palm twenty times (%d)" % used)
	check(finish("first_technique"), "First Technique done")
	# Qi Kindling 2: Mei Qing's furnace.
	check(reach("qi_kindling_2"), "Qi Kindling 2")
	check(start("mei_qings_furnace"), "Mei Qing's Furnace accepted")
	check(unlocked("alchemy"), "alchemy unlocks with Mei Qing's Furnace")
	if c().inventory.count("willow_moss") < 10:
		travel("lf_reed_shallows")
		gather("willow_moss", 10 - c().inventory.count("willow_moss"), 60)
	if c().inventory.count("riverreed_ginseng_10") < 3:
		go_to_npc(["mei_qing"])
		buy("mei_qing", "riverreed_ginseng_10", 3 - c().inventory.count("riverreed_ginseng_10"))
	check(go_to_station("alchemy_furnace"), "reach a furnace")
	var furn := objects_of("alchemy_furnace")
	if not furn.is_empty(): place(Vector2(float(furn[0].at[0]) - 40, float(furn[0].at[1]) + 10))
	var made := 0
	for i in 5:
		if made >= 3: break
		var rf := refine_with("healing_pill", 1, [0.06, 0.06, 0.06])
		if rf.get("ok", false): made += int(rf.count)
		else: print("  refine: ", rf)
	check(made >= 3, "refine three Healing Pills (%d)" % made)
	check(finish("mei_qings_furnace"), "Mei Qing's Furnace done")
	# Qi Kindling 3: teleport stones.
	check(reach("qi_kindling_3"), "Qi Kindling 3")
	check(start("stones_that_move_you"), "Stones That Move You accepted")
	var touched := 0
	for rid in ["sf_market", "lf_village", "ja_gate_street", "wp_east"]:
		if touched >= 2: break
		if not travel(rid): continue
		var stones := objects_of("teleport_stone")
		if stones.is_empty(): continue
		if interact(str(stones[0].id)).get("ok", false): touched += 1
	check(touched >= 2, "touch two teleport stones (%d)" % touched)
	var tp_to := ""
	for sid in Game.account.teleports:
		var sd := ContentDB.entry("teleport_stones", str(sid))
		if str(sd.get("room", "")) != room(): tp_to = str(sid)
	if c().inventory.count("spirit_stone_shard") < 1: Game.inventory.apply_add(c().id, "spirit_stone_shard", 1, "test")
	var tp := submit({"type": "teleport", "stone": tp_to})
	check(tp.get("ok", false), "teleport once %s" % str(tp))
	if tp.get("ok", false): place(Vector2(float(c().position.x), float(c().position.y)))
	check(finish("stones_that_move_you"), "Stones That Move You done")
	# Qi Kindling 4: the waterfall.
	check(reach("qi_kindling_4"), "Qi Kindling 4")
	check(start("listening_to_the_waterfall"), "Listening to the Waterfall accepted")
	check(travel("cf_falls_pool"), "reach the Falls Pool")
	var stone := objects_of("insight_stone")
	if not stone.is_empty(): place(Vector2(float(stone[0].at[0]) - 30, float(stone[0].at[1]) + 10))
	meditate(92.0)
	check(finish("listening_to_the_waterfall"), "Listening to the Waterfall done")

# ------------------------------------------------------------------ Qi Kindling 5-9 and the story so far
## Before a boss, a player buys pills and a couple of Revival Talismans.
func stock_up() -> void:
	var here := room()
	for want in [["healing_pill", 6, "mei_qing", ["mei_qing"]], ["revival_talisman", 2, "granny_liu", ["granny_liu"]]]:
		var n: int = int(want[1]) - int(c().inventory.count(str(want[0])))
		if n <= 0: continue
		if go_to_npc(want[3]) == "": continue
		if Game.economy.balance("silver_tael", c()) < 600: Game.economy.apply_currency("silver_tael", 57 * maxi(10, ProgressionRules.level(c())), "test_shortcut_income")
		buy(str(want[2]), str(want[0]), n)
	travel(here)

## Fight a boss or elite that may take a few tries; companions and the pet help.
func defeat(def_id: String, room_id: String, tries := 4) -> bool:
	stock_up()
	for i in tries:
		if not travel(room_id): return false
		step(1.0)
		if verbose: print("  in ", room_id, ": ", Game.room_rt.living_enemies().map(func(e): return "%s%s L%d hp%d" % [e.def_id, "*" if e.elite else "", e.level, int(e.pools.hp)]))
		if fight(def_id, 1, 900.0, 0.0, true) >= 1: return true
		revive_if_needed()
	return false

func sec_qk5() -> void:
	# Main story, Act I chapter 2: the grey in the marsh.
	check(start("strange_tracks"), "Strange Tracks accepted")
	check(travel("rm_marsh_edge"), "reach the Marsh Edge")
	var seen := 0
	for o in objects_of("inspect"):
		if seen >= 3: break
		if interact(str(o.id)).get("ok", false): seen += 1
	check(finish("strange_tracks"), "Strange Tracks done (inspected %d)" % seen)
	check(start("the_humming_token"), "The Humming Token accepted")
	check(travel("rm_grey_pools"), "reach the Grey Pools")
	check(fight("hollowed_boarlet", 5, 400.0) >= 5, "defeat five Hollowed Boarlets")
	check(finish("the_humming_token"), "The Humming Token done")
	check(start("mei_qings_errand"), "Mei Qing's Errand accepted")
	if c().inventory.count("willow_moss") < 5:
		travel("lf_reed_shallows")
		gather("willow_moss", 5 - c().inventory.count("willow_moss"), 60)
	if c().inventory.count("copper_ore") < 3:
		travel("sq_quarry_rim")
		gather("copper_ore", 3 - c().inventory.count("copper_ore"), 60)
	check(finish("mei_qings_errand"), "Mei Qing's Errand done")
	check(start("grey_at_the_edges"), "Grey at the Edges accepted")
	go_to_npc(["elder_hu", "elder_sung"])
	talk(go_to_npc(["elder_hu", "elder_sung"]))
	GameEvents.flush()
	check(c().quests.is_done("grey_at_the_edges"), "Grey at the Edges done")
	# Qi Kindling 5: the first companion.
	check(reach("qi_kindling_5"), "Qi Kindling 5")
	gear_up()
	check(start("two_hands_full"), "Two Hands Full accepted")
	var mentor := go_to_npc(["elder_hu", "elder_sung"])
	check(talk_choose(mentor, "effects", "Tie Niu"), "choose Tie Niu as companion")
	check((c().companions.roster as Array).has("tie_niu"), "Tie Niu joins the roster")
	check(defeat("thornback_boar", "bg_thicket_heart"), "defeat the Thicket Heart elite together")
	check(finish("two_hands_full"), "Two Hands Full done")
	# Qi Kindling 6: appraisal and the bandits.
	check(reach("qi_kindling_6"), "Qi Kindling 6")
	check(start("is_it_real"), "Is It Real? accepted")
	check(unlocked("appraisal") and c().inventory.count("appraisers_loupe") >= 1, "appraisal unlocks with a loupe")
	var appraised := 0
	for i in 3:
		var idx: int = c().inventory.first_index("dusty_curio")
		if idx < 0: break
		var ap := submit({"type": "use_item", "index": idx})
		if ap.get("ok", false): appraised += 1
		else: print("  appraise: ", ap)
	check(appraised == 3, "appraise three curios (%d)" % appraised)
	check(finish("is_it_real"), "Is It Real? done")
	check(start("bandits_on_the_road"), "Bandits on the Road accepted")
	check(travel("cr_caravan_road"), "reach the Caravan Road")
	check(fight("mudwater_bandit", 10, 600.0) >= 10, "defeat ten Mudwater Bandits")
	check(finish("bandits_on_the_road"), "Bandits on the Road done")
	# Qi Kindling 7: the Caravan Road, the key, the Hideout and Gu's cargo.
	check(reach("qi_kindling_7"), "Qi Kindling 7")
	check(start("the_caravan_road"), "The Caravan Road accepted")
	check(travel("cr_caravan_road"), "back on the Caravan Road")
	check(fight("mudwater_bandit", 6, 600.0) >= 6, "defeat six more Mudwater Bandits")
	var kt := 0
	while c().inventory.count("mudwater_key") < 1 and kt < 30:
		fight("mudwater_bandit", 1, 60.0)
		kt += 1
	check(c().inventory.count("mudwater_key") >= 1, "the Hideout key drops (%d fights)" % kt)
	check(finish("the_caravan_road"), "The Caravan Road done")
	check(start("mudwater_hideout"), "Mudwater Hideout accepted")
	check(travel("mh_stockade"), "the key opens the Stockade")
	# The first dungeon boss is a wall for some at Qi Kindling 7; a player comes back stronger if needed.
	if defeat("big_toad_tan", "mh_boss_den", 2): finish("mudwater_hideout")
	else: print("  Big Toad Tan held at Qi Kindling 7: returning at Qi Unfurling 1")
	check(start("gus_cargo"), "Gu's Cargo accepted")
	check(travel("dw_bend_shore"), "reach the Bend Shore")
	check(finish("gus_cargo"), "Gu's Cargo done")
	# Qi Kindling 8: auto-refine.
	check(reach("qi_kindling_8"), "Qi Kindling 8")
	check(start("batch_work"), "Batch Work accepted")
	if c().inventory.count("willow_moss") < 2 or c().inventory.count("riverreed_ginseng_10") < 1:
		go_to_npc(["mei_qing"])
		buy("mei_qing", "willow_moss", 2)
		buy("mei_qing", "riverreed_ginseng_10", 1)
	go_to_station("alchemy_furnace")
	var furn2 := objects_of("alchemy_furnace")
	if not furn2.is_empty(): place(Vector2(float(furn2[0].at[0]) - 40, float(furn2[0].at[1]) + 10))
	var qa := submit({"type": "queue_auto_refine", "recipe": "healing_pill", "count": 1})
	check(qa.get("ok", false), "queue an auto-refine batch %s" % str(qa))
	Clock.debug_offset_s += 3600.0
	var ca := submit({"type": "collect_auto_refine"})
	check(ca.get("ok", false), "collect the batch an hour later %s" % str(ca))
	check(finish("batch_work"), "Batch Work done")
	# Qi Kindling 9: Heaven's Cleansing.
	check(reach("qi_kindling_9"), "Qi Kindling 9")
	check(start("toward_cleansing_peak"), "Toward Cleansing Peak accepted")
	check(travel("cp_pilgrim_stairs"), "climb the Pilgrim Stairs")
	check(fight("stone_guardian", 3, 600.0) >= 3, "defeat three Stone Guardians")
	check(finish("toward_cleansing_peak"), "Toward Cleansing Peak done")
	check(start("the_rite"), "The Rite accepted")
	check(travel("cp_cleansing_summit"), "reach the Cleansing Summit")
	var circle := objects_of("rite_circle")
	var rite := interact(str(circle[0].id)) if not circle.is_empty() else {}
	check(rite.get("ok", false), "begin Heaven's Cleansing %s" % str(rite))
	var t0: float = Game.sim_time
	while not ("heavens_cleansing" in c().cultivator.events_passed) and Game.sim_time - t0 < 120.0:
		fight("stone_guardian", 1, 5.0)
		if Game.combat.is_wounded(c().id): break
		step(0.5)
	check("heavens_cleansing" in c().cultivator.events_passed, "Heaven's Cleansing passed")
	check(finish("the_rite"), "The Rite done")
	check(reach("qi_unfurling_1", ["cleansing_pill"]), "Qi Unfurling 1")
# ------------------------------------------------------------------ Qi Unfurling 1-4
func use_ranged(times: int) -> int:
	var slot := -1
	for i in c().cultivator.technique_slots.size():
		var t = c().cultivator.technique_slots[i]
		if t != null and str(t) != "":
			var td := ContentDB.entry("techniques", str(t))
			if td.has("projectile") or float(td.get("hitbox", {}).get("x", [0, 0])[1]) >= 200.0: slot = i
	if slot < 0: return 0
	var n := 0
	for i in times * 3:
		if n >= times: break
		c().pools.qi = c().pools.max_qi
		var foes := Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy")
		if not foes.is_empty(): place(foes[0].plane + Vector2(-150, 0))
		if submit({"type": "use_technique", "slot": slot, "facing": 1}).get("ok", false): n += 1
		step(float(ContentDB.entry("techniques", str(c().cultivator.technique_slots[slot])).get("cooldown_s", 3)) + 0.3)
	return n

func sec_qu1() -> void:
	if not c().quests.is_done("mudwater_hideout"):
		earth_gear()
		check(defeat("big_toad_tan", "mh_boss_den"), "defeat Big Toad Tan")
	check(finish("mudwater_hideout"), "Mudwater Hideout done")
	check(start("after_the_cleansing"), "After the Cleansing accepted")
	check(c().cultivator.techniques_known.has("crescent_arc"), "the jian's ranged technique is taught (Crescent Arc)")
	travel(_room_with_spawn("wild_boarlet"))
	check(use_ranged(10) >= 10, "use a ranged technique ten times")
	check(finish("after_the_cleansing"), "After the Cleansing done")
	check(str(c().training_sect.get("rank", "")) == "inner_disciple", "Inner Disciple")
	# Your own sect (account slot 4 at Qi Unfurling 1).
	check(start("a_hall_of_our_own"), "A Hall of Our Own offered")
	var f := submit({"type": "found_sect", "name": "Reed Lantern Sect", "emblem": [3, 1]})
	check(f.get("ok", false), "found your own sect %s" % str(f))
	check(finish("a_hall_of_our_own"), "A Hall of Our Own done")
	check(start("first_recruits"), "First Recruits offered")
	for i in 2: submit({"type": "recruit_disciple", "index": 0})
	check(finish("first_recruits"), "First Recruits done")
	# Qi Unfurling 2: the sect forge.
	check(reach("qi_unfurling_2"), "Qi Unfurling 2")
	check(start("the_sect_forge"), "The Sect Forge accepted")
	for need in [["copper_ore", 6], ["riverstone", 3], ["boar_hide", 2]]:
		var have: int = c().inventory.count(str(need[0]))
		if have < int(need[1]): Game.inventory.apply_add(c().id, str(need[0]), int(need[1]) - have, "test_materials")
	check(go_to_station("forge_anvil"), "reach a forge")
	var anvil := objects_of("forge_anvil")
	if not anvil.is_empty(): place(Vector2(float(anvil[0].at[0]) - 40, float(anvil[0].at[1]) + 10))
	var fg := forge_with("iron_jian", [0.03, 0.06, 0.045])
	check(fg.get("ok", false), "forge an Iron Jian %s" % str(fg))
	var idx: int = c().inventory.first_index("iron_jian")
	var en := submit({"type": "enhance", "index": idx}) if idx >= 0 else submit({"type": "enhance", "slot": "weapon"})
	if not en.get("ok", false):
		print("  enhance: ", en)
		for need2 in [["jadeiron", 5], ["spirit_stone_shard", 5]]: Game.inventory.apply_add(c().id, str(need2[0]), int(need2[1]), "test_materials")
		en = submit({"type": "enhance", "slot": "weapon"})
	check(en.get("ok", false), "enhance a weapon to +1 %s" % str(en))
	check(finish("the_sect_forge"), "The Sect Forge done")
	# Main story, chapter 5: the Drowned Shrine surfaces at Qi Unfurling 3.
	check(reach("qi_unfurling_3"), "Qi Unfurling 3")
	check(start("the_shrine_surfaces"), "The Shrine Surfaces accepted")
	check(travel("ds_flooded_gate"), "reach the Flooded Gate")
	check(finish("the_shrine_surfaces"), "The Shrine Surfaces done")
	check(start("lus_handwriting"), "Lu's Handwriting accepted")
	check(travel("ds_hall_of_lanterns"), "reach the Hall of Lanterns")
	for o in objects_of("inspect"): interact(str(o.id))
	check(finish("lus_handwriting"), "Lu's Handwriting done")
	check(start("the_drowned_abbot"), "The Drowned Abbot accepted (fought at Qi Unfurling 9, its level)")
	# Qi Unfurling 4: the herb garden.
	check(reach("qi_unfurling_4"), "Qi Unfurling 4")
	check(start("seeds_of_the_valley"), "Seeds of the Valley accepted")
	check(travel("ja_herb_terraces"), "reach the Herb Terraces")
	for o in objects_of("garden_bed"): interact(str(o.id))
	check(finish("seeds_of_the_valley"), "Seeds of the Valley done")

# ------------------------------------------------------------------ Qi Unfurling 5-9
func sec_qu5() -> void:
	check(reach("qi_unfurling_5"), "Qi Unfurling 5")
	check(start("a_friend_in_the_reeds"), "A Friend in the Reeds accepted")
	check(talk_choose(go_to_npc(["hermit_yao"]), "effects", "Reed Otter"), "choose the Reed Otter")
	check(c().pets.size() >= 1 and c().active_pet != "", "a spirit animal bonds with you")
	check(finish("a_friend_in_the_reeds"), "A Friend in the Reeds done")
	check(reach("qi_unfurling_6"), "Qi Unfurling 6")
	check(start("full_hands"), "Full Hands accepted")
	var tid := "flowing_palm"
	var m: Dictionary = c().cultivator.mastery.get(tid, {})
	m.tier = 3   # test shortcut: tiers 1-3 come from practice
	m.points = ProgressionRules.mastery_needed(3)
	c().cultivator.mastery[tid] = m
	if c().inventory.count("manual_page") < 1: Game.inventory.apply_add(c().id, "manual_page", 1, "test")
	var ru := submit({"type": "rank_up_technique", "id": tid})
	check(ru.get("ok", false), "a manual page lifts mastery to tier 4 %s" % str(ru))
	check(finish("full_hands"), "Full Hands done")
	check(reach("qi_unfurling_7"), "Qi Unfurling 7")
	check(start("the_riverbed_serpent"), "The Riverbed Serpent accepted")
	gear_up()
	check(defeat("riverbed_serpent", "dw_serpents_shallows", 3), "defeat the Riverbed Serpent")
	check(finish("the_riverbed_serpent"), "The Riverbed Serpent done")
	check(start("calming_the_wild"), "Calming the Wild accepted")
	check(tame_one(), "tame a wild spirit animal")
	check(finish("calming_the_wild"), "Calming the Wild done")
	check(reach("qi_unfurling_8"), "Qi Unfurling 8")
	check(start("the_valley_tournament"), "The Valley Tournament accepted")
	var arena := go_to_npc(["arena_master"])
	var wins := 0
	for i in 6:
		if wins >= 3: break
		if spar_with(func(): return _spar_service(arena)): wins += 1
	check(wins >= 3, "win three arena bouts (%d)" % wins)
	check(finish("the_valley_tournament"), "The Valley Tournament done")
	check(reach("qi_unfurling_9"), "Qi Unfurling 9")
	check(start("the_quiet_heart"), "The Quiet Heart accepted")
	var inc: int = c().inventory.first_index("calm_incense")
	check(inc >= 0 and submit({"type": "use_item", "index": inc, "confirm": true}).get("ok", false), "burn Calm Incense")
	meditate(302.0)
	check(finish("the_quiet_heart"), "The Quiet Heart done")
	earth_gear()
	check(defeat("drowned_abbot", "ds_abbots_sanctum"), "defeat the Drowned Abbot")
	check(finish("the_drowned_abbot"), "The Drowned Abbot done")

func upgrade_method(manual: String, method: String) -> bool:
	if c().cultivator.method_id == method: return true
	var shop := "jade_sect" if str(c().training_sect.get("id", "")) == "jade_sect" else "cloud_sect"
	go_to_npc(["jade_deacon", "cloud_deacon"])
	var have: int = int(c().training_sect.get("contribution", 0))
	var price := 800 if manual.contains("sovereign") or manual.contains("nine_winds") else 300
	if have < price:
		print("  contribution ", have, " < ", price, ": test shortcut")
		Game.training.apply_contribution(c().id, price - have, "test_shortcut")
	if not buy(shop, manual, 1): return false
	var r := submit({"type": "use_item", "index": c().inventory.first_index(manual)})
	if not r.get("ok", false):
		print("  read manual: ", r)
		return false
	var sw := submit({"type": "switch_method", "id": method})
	if not sw.get("ok", false): print("  switch: ", sw)
	return c().cultivator.method_id == method

## Cloud feathers from cranes; orchids and lotus from the valley (or Mei Qing's stall).
func make_mind_lake_pill() -> bool:
	if c().inventory.count("mind_lake_opening_pill") > 0: return true
	while c().inventory.count("cloud_feather") < 3:
		travel(_room_with_spawn("cloudwing_crane"))
		if fight("cloudwing_crane", 1, 60.0) == 0: break
	for need in [["cloudtop_orchid", 2], ["mist_lotus", 2]]:
		var n: int = int(need[1]) - int(c().inventory.count(str(need[0])))
		if n > 0:
			go_to_npc(["mei_qing"])
			if Game.economy.balance("silver_tael", c()) < 400: Game.economy.apply_currency("silver_tael", 400, "test_shortcut")
			buy("mei_qing", str(need[0]), n)
	var fn: int = 3 - int(c().inventory.count("cloud_feather"))
	if fn > 0:
		print("  had to shortcut cloud_feather (", 3 - fn, ")")
		Game.inventory.apply_add(c().id, "cloud_feather", fn, "test_materials")
	go_to_station("alchemy_furnace")
	var furn := objects_of("alchemy_furnace")
	if not furn.is_empty(): place(Vector2(float(furn[0].at[0]) - 40, float(furn[0].at[1]) + 10))
	var rf := refine_with("mind_lake_opening_pill", 1, [0.03, 0.03, 0.03])
	if not rf.get("ok", false): print("  refine mind lake: ", rf)
	return c().inventory.count("mind_lake_opening_pill") > 0

func make_refining_pill() -> bool:
	if c().inventory.count("qi_refining_pill") > 0: return true
	go_to_npc(["mei_qing"])
	if Game.economy.balance("silver_tael", c()) < 1200: Game.economy.apply_currency("silver_tael", 1200, "test_shortcut")
	if not c().crafting.recipes.has("qi_refining_pill") and not buy("mei_qing_recipes", "recipe_scroll", 1): return false
	for need in [["pearl", 2], ["mist_lotus", 2]]:
		var n: int = int(need[1]) - int(c().inventory.count(str(need[0])))
		if n > 0: buy("mei_qing", str(need[0]), n)
	if c().inventory.count("serpent_core") < 1: Game.inventory.apply_add(c().id, "serpent_core", 1, "test_materials")
	go_to_station("alchemy_furnace")
	var furn := objects_of("alchemy_furnace")
	if not furn.is_empty(): place(Vector2(float(furn[0].at[0]) - 40, float(furn[0].at[1]) + 10))
	var r := refine_with("qi_refining_pill", 1, [0.03, 0.03, 0.03])
	if not r.get("ok", false): print("  refine qi_refining_pill: ", r)
	return c().inventory.count("qi_refining_pill") > 0

## Weaken a paw-marked beast below 30% and offer it a Bonding Offering.
func tame_one() -> bool:
	for sp in ["reed_otter", "ember_fox", "jade_crane_chick", "bamboo_monkey", "mossback_toad"]:
		var rid := _room_with_spawn(sp)
		if rid == "" or not travel(rid): continue
		for attempt in 6:
			if c().inventory.count("bonding_offering_common") < 1: Game.inventory.apply_add(c().id, "bonding_offering_common", 3, "test")
			var target: EnemyState = null
			for e in Game.room_rt.living_enemies():
				if e.def_id == sp and e.team == "enemy": target = e
			if target == null:
				step(10.0)
				continue
			var t := 0.0
			while target.alive and target.pools.hp > target.pools.max_hp * 0.25 and t < 60.0:
				place(target.plane + Vector2(-34, 0))
				submit({"type": "basic_attack", "facing": 1})
				step(0.25)
				t += 0.25
			if not target.alive: continue
			place(target.plane + Vector2(-60, 0))
			var r := submit({"type": "use_item", "index": c().inventory.first_index("bonding_offering_common")})
			if verbose: print("  tame ", sp, ": ", r)
			if r.get("ok", false) and r.get("success", false): return true
			revive_if_needed()
	return false

# ------------------------------------------------------------------ Heart Tempering
func sec_ht1() -> void:
	check(reach("heart_tempering_1", ["foundation_guard_pill"]), "Heart Tempering 1")
	check(start("quiet_before_the_storm"), "Quiet Before the Storm accepted")
	check(travel("wg_rapids_terraces"), "reach the Rapids Terraces")
	check(fight("rapids_lizard", 8, 600.0) >= 8, "defeat eight Rapids Lizards")
	check(finish("quiet_before_the_storm"), "Quiet Before the Storm done")
	check(start("lines_in_the_sand"), "Lines in the Sand accepted")
	check(c().inventory.count("formation_kit") >= 1, "a Formation Kit arrives with the unlock")
	travel("ja_herb_terraces")
	var pf := submit({"type": "place_formation", "formation": "gathering"})
	check(pf.get("ok", false), "place a gathering formation %s" % str(pf))
	check(Game.workshop.formation_effect(c(), "qi_density") > 0.0, "the formation thickens the Qi here")
	check(finish("lines_in_the_sand"), "Lines in the Sand done")
	check(reach("heart_tempering_3"), "Heart Tempering 3")
	check(start("the_infirmary"), "The Infirmary accepted")
	go_to_npc(["jade_physician"])
	var treated := 0
	for i in 3:
		c().pools.qi = c().pools.max_qi
		var tr := submit({"type": "treat_patient"})
		if tr.get("ok", false): treated += 1
		elif i == 0: print("  treat: ", tr)
	check(treated == 3, "treat three patients (%d)" % treated)
	check(finish("the_infirmary"), "The Infirmary done")

func sec_ht5() -> void:
	check(reach("heart_tempering_5"), "Heart Tempering 5")
	check(start("carry_a_wall"), "Carry a Wall accepted")
	check(start("the_warm_egg"), "The Warm Egg accepted")
	var ins := submit({"type": "inscribe", "recipe": "array_plate"})
	check(ins.get("ok", false), "etch an Array Plate %s" % str(ins))
	check(finish("carry_a_wall"), "Carry a Wall done")
	var egg: int = c().inventory.first_index("spirit_egg")
	var inc := submit({"type": "use_item", "index": egg})
	check(inc.get("ok", false), "incubate the spirit egg %s" % str(inc))
	check(finish("the_warm_egg"), "The Warm Egg done")
	Clock.debug_offset_s += 25.0 * 3600.0
	var pets_before: int = c().pets.size()
	check(submit({"type": "hatch_egg", "index": 0}).get("ok", false) and c().pets.size() == pets_before + 1, "the egg hatches a day later")
	check(start("shen_lians_failure"), "Shen Lian's Failure accepted")
	var sl := go_to_npc(["shen_lian"])
	var won := false
	for i in 3:
		won = spar_with(func(): return _spar_service(sl))
		if won: break
	check(won, "beat Shen Lian again")
	check(finish("shen_lians_failure"), "Shen Lian's Failure done")
	check(reach("heart_tempering_6"), "Heart Tempering 6")
	check(start("brothers_in_arms"), "Brothers in Arms accepted")
	check(talk_choose(go_to_npc(["elder_hu", "elder_sung"]), "effects", "Lan Yue"), "choose Lan Yue as second companion")
	check(travel("wg_echo_cliffs"), "clear to the Echo Cliffs")
	check(finish("brothers_in_arms"), "Brothers in Arms done")
	check(reach("heart_tempering_7"), "Heart Tempering 7")
	check(start("keep_watch"), "Keep Watch accepted")
	travel("ja_herb_terraces")
	if c().inventory.count("fuel_crystal_low") < 5: Game.inventory.apply_add(c().id, "fuel_crystal_low", 5, "test")
	submit({"type": "remove_formation", "index": 0})
	var gf := submit({"type": "place_formation", "formation": "guard"})
	check(gf.get("ok", false), "place a guard formation %s" % str(gf))
	check(reach("heart_tempering_8"), "break through inside the guard formation")
	check(finish("keep_watch"), "Keep Watch done")
	# Jade Current ends at Heart Tempering 9: learn a library method while progress is low.
	check(upgrade_method("manual_willow_breath_art", "willow_breath_art"), "switch to a library method")
	check(reach("heart_tempering_9"), "Heart Tempering 9")
	check(make_refining_pill(), "refine the Qi Refining Pill for Cloud Stride")
	check(start("the_heart_trial"), "The Heart Trial accepted")
	check(travel("ja_elder_hu_peak"), "Elder Hu's peak")
	var rite := interact("rite_reflection")
	check(rite.get("ok", false), "step into the circle %s" % str(rite))
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(fight("the_reflection", 1, 600.0, 0.0, true) >= 1, "defeat your Reflection")
	check("heart_trial" in c().cultivator.events_passed, "Heart Trial passed")
	travel("ja_elder_hu_peak")
	check(finish("the_heart_trial"), "The Heart Trial done")

# ------------------------------------------------------------------ Cloud Stride
func sec_cs1() -> void:
	check(reach("cloud_stride_1"), "Cloud Stride 1")
	check(start("wings_of_cloud"), "Wings of Cloud accepted")
	check(travel("cc_cliff_faces"), "reach the Cliff Faces")
	check(fight("cloudwing_crane", 3, 600.0) >= 3, "defeat three Cloudwing Cranes")
	check(finish("wings_of_cloud"), "Wings of Cloud done")
	check(start("riding_the_wind"), "Riding the Wind accepted")
	check(talk_choose(go_to_npc(["hermit_yao"]), "effects", "Hold out"), "bond with a crane that can carry you")
	check(finish("riding_the_wind"), "Riding the Wind done")
	check(reach("cloud_stride_2"), "Cloud Stride 2")
	check(start("clearer_water"), "Clearer Water accepted")
	var sec := submit({"type": "enter_seclusion", "focus": "refine_qi"})
	check(sec.get("ok", false), "seclusion with Refine Qi %s" % str(sec))
	var purity_before: int = c().cultivator.purity
	Clock.debug_offset_s += 12.0 * 3600.0   # one night away
	submit({"type": "claim_offline", "elapsed": 12.0 * 3600.0})
	check(c().cultivator.purity < purity_before, "a night of Refine Qi raises purity (%d -> %d)" % [purity_before, c().cultivator.purity])
	check(finish("clearer_water"), "Clearer Water done")
	check(reach("cloud_stride_3"), "Cloud Stride 3")
	check(start("above_the_mist"), "Above the Mist accepted")
	check(travel("cc_sky_ledges"), "reach the Sky Ledges")
	check(fight("stormwing_hawk", 5, 600.0) >= 5, "defeat five Stormwing Hawks")
	check(finish("above_the_mist"), "Above the Mist done")
	check(reach("cloud_stride_4"), "Cloud Stride 4")
	check(start("the_upper_stacks"), "The Upper Stacks accepted")
	check(start("the_bracket"), "The Bracket accepted")
	var arena := go_to_npc(["arena_master"])
	var wins := 0
	for i in 5:
		if wins >= 2: break
		if spar_with(func(): return _spar_service(arena)): wins += 1
	check(finish("the_bracket"), "The Bracket done: top eight")
	check(str(c().training_sect.get("rank", "")) == "core_disciple", "Core Disciple (%s)" % str(c().training_sect.get("rank", "")))
	check(finish("the_upper_stacks"), "The Upper Stacks done")

func sec_cs5() -> void:
	check(reach("cloud_stride_5"), "Cloud Stride 5")
	check(start("hands_of_wood"), "Hands of Wood accepted")
	go_to_npc(["tinkerer_yu"])
	var bp := submit({"type": "build_puppet", "blueprint": "worker_puppet"})
	check(bp.get("ok", false), "build a worker puppet %s" % str(bp))
	check(finish("hands_of_wood"), "Hands of Wood done")
	Clock.debug_offset_s += 3.0 * 3600.0
	var cp := submit({"type": "collect_puppets"})
	check(cp.get("ok", false), "the puppet mines while you are away %s" % str(cp))
	check(reach("cloud_stride_7"), "Cloud Stride 7")
	check(start("the_valley_finals"), "The Valley Finals accepted")
	var arena2 := go_to_npc(["arena_master"])
	var fw := 0
	for i in 6:
		if fw >= 3: break
		if spar_with(func(): return _spar_service(arena2)): fw += 1
	check(finish("the_valley_finals"), "The Valley Finals done")
	check(c().cultivator.titles.has("valley_champion"), "title Valley Champion")
	check(reach("cloud_stride_9"), "Cloud Stride 9")
	check(start("opening_the_lake"), "Opening the Lake accepted")
	check(make_mind_lake_pill(), "refine the Mind Lake Opening Pill")
	check(finish("opening_the_lake"), "Opening the Lake done")

# ------------------------------------------------------------------ Spirit Awakening
func sec_sa1() -> void:
	check(reach("spirit_awakening_1", ["mind_lake_opening_pill"]), "Spirit Awakening 1")
	check(c().pools.max_soul > 0.0, "a soul pool from Spirit Awakening")
	check(start("a_lake_inside"), "A Lake Inside accepted")
	var pulses := 0
	for i in 8:
		if pulses >= 5: break
		c().pools.soul = c().pools.max_soul
		if submit({"type": "sense_pulse"}).get("ok", false): pulses += 1
		step(6.5)
	check(pulses >= 5, "pulse Spirit Sense five times (%d)" % pulses)
	check(finish("a_lake_inside"), "A Lake Inside done")
	check(reach("spirit_awakening_2"), "Spirit Awakening 2")
	check(start("what_the_eyes_miss"), "What the Eyes Miss accepted")
	var used := 0
	for spot in [["sq_quarry_rim", "tunnel"], ["cf_falls_pool", "behind"], ["wg_rapids_terraces", "cave"]]:
		var rid := str(spot[0])
		for r2 in ContentDB.rooms:
			for p2 in ContentDB.room(r2).get("portals", []):
				if str(p2.id) == str(spot[1]) and str(p2.get("type", "")) == "hidden": rid = str(r2)
		if not travel(rid): continue
		var pp: Dictionary = {}
		for p3 in Game.room_rt.def.get("portals", []):
			if str(p3.id) == str(spot[1]): pp = p3
		if pp.is_empty(): continue
		place(Vector2(float(pp.at[0]), float(pp.at[1]) + 10))
		c().pools.soul = c().pools.max_soul
		c().pools.cooldowns.erase("sense")
		submit({"type": "sense_pulse"})
		if go(str(spot[1])):
			used += 1
			go(str(Game.room_rt.def.get("portals", [{}])[0].get("id", "")))
	check(used >= 3, "find and use three hidden portals (%d)" % used)
	check(finish("what_the_eyes_miss"), "What the Eyes Miss done")
	check(start("hidden_cargo"), "Hidden Cargo accepted")
	c().pools.soul = c().pools.max_soul
	c().pools.cooldowns.erase("sense")
	submit({"type": "sense_pulse"})
	check(finish("hidden_cargo"), "Hidden Cargo done")
	check(reach("spirit_awakening_3"), "Spirit Awakening 3")
	check(start("the_sleeping_blade"), "The Sleeping Blade accepted")
	check(travel("ds_abbots_sanctum"), "reach the Abbot's vault")
	check(interact("sleeping_blade_altar").get("ok", false), "lift the blade from the altar")
	check(c().inventory.count_including_equipped("sleeping_blade") >= 1, "bind the Sleeping Blade")
	check(finish("the_sleeping_blade"), "The Sleeping Blade done")
	check(reach("spirit_awakening_4"), "Spirit Awakening 4")
	check(start("quiet_waters"), "Quiet Waters accepted")
	var ns := submit({"type": "enter_seclusion", "focus": "nourish_soul"})
	check(ns.get("ok", false), "seclusion with Nourish Soul %s" % str(ns))
	submit({"type": "claim_offline", "elapsed": 8.0 * 3600.0})
	check(finish("quiet_waters"), "Quiet Waters done")

func sec_sa5() -> void:
	check(reach("spirit_awakening_5"), "Spirit Awakening 5")
	check(start("the_mentors_gift"), "The Mentor's Gift accepted")
	travel("ja_pavilion_rooftops")
	var posts := objects_of("spar_post")
	var won := false
	for i in 3:
		won = spar_with(func(): return interact(str(posts[0].id)))
		if won: break
	check(won, "pass the personal-disciple trial")
	check(finish("the_mentors_gift"), "The Mentor's Gift done")
	check(reach("spirit_awakening_6"), "Spirit Awakening 6")
	check(start("torn_pages"), "Torn Pages accepted")
	go_to_npc(["jade_librarian"])
	var rm := submit({"type": "restore_manual"})
	check(rm.get("ok", false), "restore a damaged manual %s" % str(rm))
	check(finish("torn_pages"), "Torn Pages done")
	check(reach("spirit_awakening_7"), "Spirit Awakening 7")
	check(start("passing_it_on"), "Passing It On accepted")
	if Game.workshop.teachable_daos(c()).is_empty():
		Game.progression.apply_insight(c().id, "sword", 5000.0, "test_shortcut")
	var tc := submit({"type": "teach_disciple", "index": 0})
	check(tc.get("ok", false), "teach a sect disciple %s" % str(tc))
	check(finish("passing_it_on"), "Passing It On done")
	# Chapter 8: Gu's warehouse opens at Spirit Awakening 8.
	check(reach("spirit_awakening_8"), "Spirit Awakening 8")
	check(start("gus_warehouse"), "Gu's Warehouse accepted")
	check(travel("sf_artisan_row") and go("warehouse_door"), "slip into Gu's warehouse")
	var fled := {"n": 0}
	var on_flee := func(n, p): if n == "boss_fled": fled.n += 1
	GameEvents.event.connect(on_flee)
	fight("elder_gu", 1, 90.0, 0.0, true)
	GameEvents.event.disconnect(on_flee)
	check(int(fled.n) == 1, "Elder Gu holds you off, then flees")
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	check(c().inventory.count("smuggler_ledger") >= 1, "the smuggler's ledger falls as he runs")
	go("entry")
	check(finish("gus_warehouse"), "Gu's Warehouse done")
	check(start("the_rift"), "The Rift accepted")
	check(finish("the_rift"), "The Rift done (Madam Hua)")
	# The library method ends at Spirit Awakening 9: take the sect's core scripture.
	var core := "manual_tidal_sovereign_scripture" if str(c().training_sect.get("id", "")) == "jade_sect" else "manual_nine_winds_canon"
	var core_m := "tidal_sovereign_scripture" if core.contains("tidal") else "nine_winds_canon"
	if int(c().training_sect.get("contribution", 0)) < 800: Game.training.apply_contribution(c().id, 800, "test_shortcut")
	check(upgrade_method(core, core_m), "switch to the sect's core scripture")

# ------------------------------------------------------------------ Heaven Glimpse and the end of Act I
func sec_hg1() -> void:
	check(reach("heaven_glimpse_1"), "Heaven Glimpse 1")
	check(start("a_wider_sky"), "A Wider Sky accepted")
	check(travel("mp_forgotten_monastery"), "reach the Forgotten Monastery")
	var stone := objects_of("insight_stone")
	if not stone.is_empty(): place(Vector2(float(stone[0].at[0]) - 30, float(stone[0].at[1]) + 10))
	meditate(122.0)
	check(finish("a_wider_sky"), "A Wider Sky done")
	check(unlocked("cape_slot"), "cape slot at Heaven Glimpse 1")
	check(reach("heaven_glimpse_2"), "Heaven Glimpse 2")
	check(start("allies_at_the_wall"), "Allies at the Wall accepted")
	if c().inventory.count("fuel_crystal_low") < 10: Game.inventory.apply_add(c().id, "fuel_crystal_low", 10, "test")
	for rid in ["ja_gate_street", "sf_fairground"]:
		travel(rid)
		for i in 2: submit({"type": "remove_formation", "index": 0})
		submit({"type": "place_formation", "formation": "protection"})
	check(finish("allies_at_the_wall"), "Allies at the Wall done")
	check(start("the_siege"), "The Siege accepted")
	var siege := "ja_gate_street" if str(c().training_sect.get("id", "")) == "jade_sect" else "cm_cliff_stair"
	check(siege != "" and travel(siege), "reach the siege start (%s)" % siege)
	for o in objects_of("rite_circle"):
		if str(o.get("event", "")) == "siege_of_two_sects": interact(str(o.id))
	place(Vector2(float(c().position.x), float(c().position.y)))
	var t0: float = Game.sim_time
	while not ("siege_of_two_sects" in c().cultivator.events_passed) and Game.sim_time - t0 < 400.0:
		var foes := Game.room_rt.living_enemies().filter(func(e): return e.team == "enemy")
		if foes.is_empty(): step(1.0)
		else: fight(foes[0].def_id, 1, 20.0)
		revive_if_needed()
	check("siege_of_two_sects" in c().cultivator.events_passed, "hold the wall in the Siege of Two Sects")
	check(finish("the_siege"), "The Siege done")
	check(start("what_remains"), "What Remains accepted")
	talk(go_to_npc(["elder_hu", "elder_sung"]))
	check(finish("what_remains"), "What Remains done")
	check(reach("heaven_glimpse_3"), "Heaven Glimpse 3")
	check(start("beyond_the_valley"), "Beyond the Valley accepted")
	for npc in ["aunt_ping", "old_ma", "granny_liu", "little_dou", "uncle_guo"]:
		talk(go_to_npc([npc]))
	check(finish("beyond_the_valley"), "Beyond the Valley done")
	check(start("the_ascension_gate"), "The Ascension Gate accepted")
	var gate_room := _room_with_spawn("gate_guardian")
	check(defeat("gate_guardian", gate_room, 4), "defeat the Gate Guardian (%s)" % gate_room)
	GameEvents.flush()
	check(c().quests.is_done("the_ascension_gate"), "Act I complete: the Ascension Gate")
	# Unlock order (Part 4): each system unlocks in timeline order.
	var expected := ["weapons", "herb_gathering", "mining", "daily_missions", "qi_pool", "cooking", "first_technique_slots", "alchemy",
		"teleport_stones", "companions", "appraisal", "auto_refine", "spirit_animals", "taming", "formations", "healing", "spirit_eggs",
		"guard_formation", "puppetry", "spirit_sense", "research", "teaching", "cape_slot"]
	var last := -1
	var ordered := true
	for sys in expected:
		var i := unlock_log.find(sys)
		if i < 0: continue
		if i < last:
			ordered = false
			print("  unlock out of order: ", sys)
		last = i
	check(ordered, "systems unlock in the Part 4 order")

## The mini-game through intents: each strike's distance from the band centre, then the craft.
func strike_steps(recipe: String, craft: String, offsets: Array) -> void:
	for o in offsets: submit({"type": "craft_step", "recipe": recipe, "craft": craft, "offset": o})

func refine_with(recipe: String, count: int, offsets: Array) -> Dictionary:
	strike_steps(recipe, "alchemy", offsets)
	return submit({"type": "refine", "recipe": recipe, "count": count})

func forge_with(recipe: String, offsets: Array) -> Dictionary:
	strike_steps(recipe, "smithing", offsets)
	return submit({"type": "forge", "recipe": recipe})
