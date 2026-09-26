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

const SECTIONS := ["bf2", "bf5", "bf8", "qk1", "qk5", "qu1", "qu5", "ht1", "ht5", "cs1", "cs5", "sa1", "sa5", "hg1", "ae1", "ae2", "ae3", "ae4",
	"ae5", "ae6", "ls1", "ls2", "ls3"]
const CP_ROOT := "user://valley_cp/"
const WORK := "user://valley_work/"

var unlock_log: Array = []
var fates_offered := 0          # S48: fate cards offered after great breakthroughs
var tribulations_weathered := 0 # S48: heavenly tribulations stood through

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
	# The run's clock skips go with the saves, so timed state (auction lots, cooldowns) resumes in step.
	var f := FileAccess.open(CP_ROOT + name + ".clock", FileAccess.WRITE)
	if f != null: f.store_string(str(Clock.debug_offset_s))

func resume(name: String) -> bool:
	if not DirAccess.dir_exists_absolute(CP_ROOT + name + "/"): return false
	_copy_dir(CP_ROOT + name + "/", WORK)
	if FileAccess.file_exists(CP_ROOT + name + ".clock"):
		Clock.debug_offset_s = float(FileAccess.get_file_as_string(CP_ROOT + name + ".clock"))
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
		if buy(shop, str(s.item), 1): equip_newest(str(s.item))
	if verbose: print("  gear up at ", shop, ": attack ", snappedf(before, 0.1), " -> ", snappedf(c().stats.value("physical_attack"), 0.1), " level ", ProgressionRules.level(c()), " taels ", Game.economy.balance("silver_tael", c()))

## Gear from a Spirit Stone shop of the Expanse, the same rule as gear_up: better grade only, the
## weapon family kept; the stones stand in for the hours of Expanse income the run skips.
func gear_up_stones(shop: String) -> void:
	var w = c().inventory.equipped.get("weapon")
	var fam := str(ContentDB.item(str(w.id)).get("family", "jian")) if w != null else "jian"
	for s in Game.economy.stock(c(), shop):
		if str(s.get("locked", "")) != "": continue
		var def := ContentDB.item(str(s.item))
		if not ContentDB.is_equipment(str(s.item)): continue
		if str(def.slot) == "weapon" and str(def.get("family", "")) != fam: continue
		var cur = c().inventory.equipped.get(str(def.slot))
		if cur != null and StatRules.grade_index(str(ContentDB.item(str(cur.id)).get("grade", "plain"))) >= StatRules.grade_index(str(def.get("grade", "plain"))): continue
		var short := int(s.price) - Game.economy.balance("spirit_stone")
		if short > 0: Game.economy.apply_currency("spirit_stone", short, "test_shortcut_income")
		if buy(shop, str(s.item), 1): equip_newest(str(s.item))

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
		for o in objects_of("herb_patch") + objects_of("ore_vein") + objects_of("star_sight") + objects_of("insect_swarm"):
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
				# The condensing pills come from recipes the player has learned: refine another (test shortcut).
				for cp in ["sage_condensing_pill", "law_condensing_pill", "monarch_condensing_pill"]:
					if str(r0.get("text", "")).begins_with(ContentDB.item_name(cp)) and c().inventory.count(cp) < 1:
						Game.inventory.apply_add(c().id, cp, 1, "test_shortcut")
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
		weather_tribulation()
		choose_fate()
	return ProgressionRules.at_least(c().cultivator.realm_key, realm)

## S48: from Cloud Stride on the heavens test a great breakthrough. Step out of each ring as it closes, as a player
## would (a test shortcut moves the body straight to the side).
func weather_tribulation() -> void:
	var guard := 0
	while Game.progression.is_under_tribulation(c().id) and guard < 900:
		var tv: Dictionary = Game.progression.tribulation_view(c().id)
		var w: Dictionary = tv.get("warn", {})
		var st: ActorState = Game.actor_state(c().id)
		if not w.is_empty() and st != null and absf(st.plane.x - float(w.x)) < 200.0:
			var width: float = Game.room_rt.width() if Game.room_rt else 2560.0
			st.plane.x = float(w.x) + (260.0 if float(w.x) < width * 0.5 else -260.0)
		step(0.1)
		guard += 1
	if guard > 0: tribulations_weathered += 1

## S48: a fate after each great breakthrough. The run keeps the gentlest card on offer so later checks stay put.
func choose_fate() -> void:
	var offer: Array = c().cultivator.fate_offer
	if offer.is_empty(): return
	fates_offered += 1
	var pick := str(offer[0])
	for f in ["lucky_star", "bone_of_the_river", "wandering_eye", "blood_memory", "iron_will", "dao_echo", "thunder_tempered", "quiet_heart",
			"hungry_dantian", "debt_of_heaven", "scar_of_failure"]:
		if f in offer:
			pick = f
			break
	submit({"type": "choose_fate", "card": pick})

## Equip the copy just bought or made (the highest uid), not an older one of a worse quality in the bag.
func equip_newest(item: String) -> bool:
	var best := -1
	for i in c().inventory.bag.size():
		var it = c().inventory.bag[i]
		if it != null and str(it.id) == item and (best < 0 or int(it.get("uid", 0)) > int(c().inventory.bag[best].get("uid", 0))): best = i
	if best < 0: return false
	return submit({"type": "equip", "index": best}).get("ok", false)

func equip_first(item: String) -> bool:
	var i: int = c().inventory.first_index(item)
	if i < 0: return false
	return submit({"type": "equip", "index": i}).get("ok", false)

func buy(shop: String, item: String, count := 1, learn := "") -> bool:
	var r := submit({"type": "buy", "shop": shop, "item": item, "count": count, "learn": learn})
	if not r.get("ok", false): print("  buy ", item, " at ", shop, ": ", r)
	return r.get("ok", false)

func unlocked(system: String) -> bool:
	return Unlocks.is_unlocked(c().id, system)

const KEEP := ["herbal_tea", "rice_ball", "rice", "willow_moss", "riverreed_ginseng_10", "tough_meat", "spirit_stone_shard", "sunscar_seal",
	"revival_talisman", "return_charm", "fuel_crystal_low", "blank_plate", "formation_stone", "restoration_ink", "torn_manual",
	"spirit_wood", "puppet_core", "spirit_egg", "dusty_curio", "calm_incense", "cloud_feather", "cloudtop_orchid", "mudwater_key",
	"cleansing_pill", "healing_pill", "qi_restoration_pill", "manual_page", "copper_ore", "jadeiron", "mist_lotus", "evergreen_heart_seed",
	"storm_shard", "thunder_horn", "stormsteel_ore"]

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
		# Natural treasures are never sold: a careful player puts them in storage.
		if str(def2.get("type", "")) == "treasure":
			submit({"type": "deposit", "index": i, "count": int(it.get("count", 1))})
			continue
		submit({"type": "sell", "index": i, "count": int(it.get("count", 1))})
	# Still short: a careful player banks the manuals already learned.
	if c().inventory.free_slots() < min_free:
		for i in c().inventory.bag.size():
			var it = c().inventory.bag[i]
			if it == null or wanted.has(str(it.id)) or str(it.id) in KEEP: continue
			if str(ContentDB.item(str(it.id)).get("type", "")) == "scroll": submit({"type": "deposit", "index": i, "count": int(it.get("count", 1))})
	# And the keepsakes no lesson ahead calls for: relic shards, treasure arts, spare talismans.
	if c().inventory.free_slots() < min_free:
		for i in c().inventory.bag.size():
			var it = c().inventory.bag[i]
			if it == null or wanted.has(str(it.id)) or str(it.id) in KEEP: continue
			if str(ContentDB.item(str(it.id)).get("type", "")) in ["relic_shard", "treasure_art", "talisman"]:
				submit({"type": "deposit", "index": i, "count": int(it.get("count", 1))})
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
	# S43: the Outer Trial teaches Plunge; come down hard from a jump once.
	check("plunge" in c().cultivator.secret_arts, "the mentor teaches Plunge")
	check(plunges(1) == 1, "plunge from the air")
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
	_keeping_post()
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

## S50 Keeping Post (V10): Fisher Wen's lesson. The first disciple keeps post at a willow moss patch in the Reed
## Shallows while a second disciple is played; coming back settles the post. Then Little Dou's glowflies and a net.
func _keeping_post() -> void:
	check(start("keeping_post"), "Keeping Post accepted")
	check(unlocked("keeping_post"), "Keeping Post unlocks once a second disciple can take over")
	check(travel("lf_reed_shallows"), "to the Reed Shallows")
	var moss := objects_of("herb_patch", "item", "willow_moss")
	check(not moss.is_empty(), "willow moss grows in the Reed Shallows")
	if moss.is_empty(): return
	place(Vector2(float(moss[0].at[0]), float(moss[0].at[1]) + 10))
	check(submit({"type": "take_post", "object": str(moss[0].id)}).get("ok", false), "keep post at the willow moss")
	if not Game.characters.has("c2"):
		submit({"type": "create_character", "slot": 2, "name": "Second Disciple", "skip_prologue": true})
	check(submit({"type": "switch_character", "slot": 2}).get("ok", false), "switch to a second disciple, straight from the post")
	Clock.debug_offset_s += 3.0 * 3600.0
	var home := submit({"type": "switch_character", "slot": 1})
	var ledger: Dictionary = home.get("welcome", {}).get("post", {})
	check(home.get("ok", false) and int(ledger.get("items", {}).get("willow_moss", 0)) > 0 and float(ledger.get("exp", 0.0)) > 0.0,
		"three hours later the first disciple comes back with %d willow moss and Foraging EXP" % int(ledger.get("items", {}).get("willow_moss", 0)))
	submit({"type": "enter_world"})
	place(Vector2(float(c().position.x), float(c().position.y)))
	check(finish("keeping_post"), "Keeping Post done")
	submit({"type": "send_to_storehouse", "character": c().id})
	check(int(Game.account.storehouse.get("willow_moss", 0)) > 0, "the haul goes to the Storehouse")
	submit({"type": "leave_post"})
	# Little Dou's glowflies: Insect Netting.
	check(start("glowflies"), "Little Dou's Glowflies accepted")
	check(unlocked("insect_netting") and c().inventory.count("reed_net") > 0, "Insect Netting unlocks with a reed net")
	check(travel("lf_reed_shallows"), "back to the Reed Shallows")
	var got := gather("glowfly", 5, 40)
	check(got >= 5, "net five glowflies (%d)" % got)
	check(Game.posts.xp(c(), "netting") > 0.0, "netting by hand trains Insect Netting")
	check(finish("glowflies"), "Little Dou's Glowflies done")

## S50 V10c: an apprentice at the bench (Tinkerer Yu), a snare on the Reed Shallows trail (Adventurer Kai), and the
## County Hall's rites (Magistrate Qian).
func _stations() -> void:
	check(start("an_apprentices_hands"), "An Apprentice's Hands accepted")
	check(unlocked("apprentice_bench"), "the Apprentice Bench unlocks")
	check(submit({"type": "bench_assign", "slot": 0, "item": "hemp_cord"}).get("ok", false), "an apprentice twists hemp cord")
	check(finish("an_apprentices_hands"), "An Apprentice's Hands done")
	check(start("snares_before_swords"), "Snares Before Swords accepted")
	check(unlocked("beast_snaring") and c().inventory.count("hemp_snare_kit") > 0, "Beast Snaring unlocks with a hemp snare kit")
	check(travel("lf_reed_shallows"), "to the Reed Shallows trail")
	var trails := objects_of("beast_trail")
	check(not trails.is_empty(), "a beast trail in the Reed Shallows")
	if trails.is_empty(): return
	place(Vector2(float(trails[0].at[0]), float(trails[0].at[1]) + 10))
	check(submit({"type": "set_snare", "object": str(trails[0].id), "snare": "snare_20m"}).get("ok", false), "set a twenty-minute snare")
	Clock.debug_offset_s += 1300.0
	var got := submit({"type": "collect_snare", "object": str(trails[0].id)})
	check(got.get("ok", false) and int(got.get("items", {}).get("jade_frog", 0)) >= 1, "take it up with a jade frog")
	check(finish("snares_before_swords"), "Snares Before Swords done")
	check(start("the_ancestors_regard"), "The Ancestors' Regard accepted")
	check(unlocked("ancestral_rites") and c().inventory.count("wood_rite_tablet") > 0, "the Rites unlock with a wooden tablet")
	check(travel("sf_county_hall"), "to the County Hall")
	var altars := objects_of("ancestral_altar")
	check(not altars.is_empty(), "the County Hall keeps an ancestral altar")
	if altars.is_empty(): return
	place(Vector2(float(altars[0].at[0]), float(altars[0].at[1]) + 10))
	var rite := submit({"type": "hold_rite", "object": str(altars[0].id)})
	check(rite.get("ok", false) and int(rite.get("wisps", 0)) > 0, "hold the rites: wave %d, %d Spirit Wisps" % [int(rite.get("wave", 0)), int(rite.get("wisps", 0))])
	check(finish("the_ancestors_regard"), "The Ancestors' Regard done")

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
	check(c().inventory.furnace != null and str(c().inventory.furnace.id) == "bronze_furnace", "Mei Qing's bronze furnace sits in the furnace slot")
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
	# S43: Falling Leaf Glide at the Falls Pool.
	check(start("leaf_on_the_wind"), "Leaf on the Wind accepted")
	check(travel("cf_falls_pool"), "reach the Falls Pool for the glide")
	check(glides(2) == 2, "glide twice")
	check(finish("leaf_on_the_wind"), "Leaf on the Wind done")
	_stations()
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
	# S47: Old Scribe Bai's talisman craft; one clean stroke writes the first Flame Talisman.
	tidy_bag()
	check(start("ink_and_paper"), "Ink and Paper accepted")
	var tr := submit({"type": "trace_talisman", "recipe": "flame_talisman", "score": 0.85})
	if not tr.get("ok", false): print("  trace: ", tr)
	check(tr.get("ok", false) and c().inventory.count("flame_talisman") >= 1, "trace a Flame Talisman")
	check(finish("ink_and_paper"), "Ink and Paper done")
	check(start("bandits_on_the_road"), "Bandits on the Road accepted")
	check(travel("cr_caravan_road"), "reach the Caravan Road")
	check(fight("mudwater_bandit", 10, 600.0) >= 10, "defeat ten Mudwater Bandits")
	check(finish("bandits_on_the_road"), "Bandits on the Road done")
	# Qi Kindling 7: the Caravan Road, the key, the Hideout and Gu's cargo.
	check(reach("qi_kindling_7"), "Qi Kindling 7")
	# S43: Swallow Dart from the library's first floor.
	check(start("swallow_dart"), "Swallow Dart accepted")
	check(air_dashes(3) == 3, "dart through the air three times")
	check(finish("swallow_dart"), "Swallow Dart done")
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
	# The rank opens the sect retreat rooms (S07): seclusion there runs to a 16 h cap.
	var own_retreat := ("ja_" if str(c().training_sect.get("id", "")) == "jade_sect" else "cm_") + "retreat"
	check(travel(own_retreat), "walk into the sect retreat rooms")
	check(submit({"type": "enter_seclusion", "focus": "heal"}).get("ok", false), "enter seclusion in a retreat room")
	var away := submit({"type": "claim_offline", "elapsed": 20.0 * 3600.0})
	check(away.get("capped", false) and is_equal_approx(float(away.get("hours", 0.0)), 16.0), "a retreat room holds seclusion for 16 h %s" % str(away))
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
	# The Iron Jian takes 6 copper; as Common gear its first enhancement takes 2 Riverstone (S47 salvage.json metals).
	for need in [["copper_ore", 8], ["riverstone", 5], ["boar_hide", 2]]:
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
	check(start("the_riverbreath_trial"), "The Riverbreath Trial accepted")
	check(travel("ds_scripture_well"), "reach the Scripture Well")
	var well := objects_of("rite_circle", "event", "riverbreath_trial")
	var wr := interact(str(well[0].id)) if not well.is_empty() else {}
	check(wr.get("ok", false), "begin Lu's inheritance trial %s" % str(wr))
	var tw: float = Game.sim_time
	while not ("riverbreath_trial" in c().cultivator.events_passed) and Game.sim_time - tw < 120.0:
		fight("drowned_acolyte", 1, 5.0)
		revive_if_needed()
		step(0.5)
	check("riverbreath_trial" in c().cultivator.events_passed, "hold the Scripture Well: the inheritance accepts you")
	check(finish("the_riverbreath_trial"), "The Riverbreath Trial done")
	check(start("the_drowned_abbot"), "The Drowned Abbot accepted (fought at Qi Unfurling 9, its level)")
	# Qi Unfurling 4: the herb garden.
	check(reach("qi_unfurling_4"), "Qi Unfurling 4")
	check(start("seeds_of_the_valley"), "Seeds of the Valley accepted")
	check(travel("ja_herb_terraces"), "reach the Herb Terraces")
	var planted := 0
	for o in objects_of("garden_bed"):
		interact(str(o.id))
		if submit({"type": "plant_seed", "bed": Game.room_rt.room_id + ":" + str(o.id), "seed": "willow_moss_seed"}).get("ok", false): planted += 1
	check(planted == 3, "plant the three willow moss seeds Gardener Ji gives (%d)" % planted)
	check(finish("seeds_of_the_valley"), "Seeds of the Valley done")
	# Two hours on, the moss is grown: harvest one bed.
	Clock.debug_offset_s += 2.0 * 3600.0 + 60.0
	var moss := submit({"type": "harvest_bed", "bed": "ja_herb_terraces:bed_0"})
	check(moss.get("ok", false) and str(moss.get("item", "")) == "willow_moss", "two hours later the first bed is ready to harvest %s" % str(moss))

# ------------------------------------------------------------------ Qi Unfurling 5-9
func sec_qu5() -> void:
	check(reach("qi_unfurling_5"), "Qi Unfurling 5")
	check(start("a_friend_in_the_reeds"), "A Friend in the Reeds accepted")
	check(talk_choose(go_to_npc(["hermit_yao"]), "effects", "Reed Otter"), "choose the Reed Otter")
	check(c().pets.size() >= 1 and c().active_pet != "", "a spirit animal bonds with you")
	check(finish("a_friend_in_the_reeds"), "A Friend in the Reeds done")
	check(reach("qi_unfurling_6"), "Qi Unfurling 6")
	# S43: Cloud Ladder Step, the double jump, is taught by the librarians at Qi Unfurling 6.
	check(start("cloud_ladder"), "Cloud Ladder accepted")
	check("cloud_ladder_step" in c().cultivator.secret_arts, "the librarian teaches Cloud Ladder Step")
	check(double_jumps(3) == 3, "double jump three times")
	check(finish("cloud_ladder"), "Cloud Ladder done")
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
	# S43: the hermit's Skipping Stones teaches Water Skimming over the pond under the stilts.
	check(start("skipping_stones"), "Skipping Stones accepted")
	check(travel("rm_hermit_stilt_house"), "reach the hermit's pond")
	check(skim_the_pond(), "sprint across the deep pond")
	check(interact("pond_lotus").get("ok", false) and c().inventory.count("mist_lotus") >= 1, "pick the Mist Lotus on the rock")
	check(finish("skipping_stones"), "Skipping Stones done")
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
	if not c().crafting.recipes.has("qi_refining_pill") and not buy("mei_qing_recipes", "recipe_scroll", 1, "qi_refining_pill"): return false
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
		if verbose: print("  tame: ", sp, " in ", rid)
		if rid == "" or not travel(rid): continue
		for attempt in 10:
			if c().inventory.count("bonding_offering_common") < 1: Game.inventory.apply_add(c().id, "bonding_offering_common", 3, "test")
			# A failed offering makes the beast bolt: wait for the next one to wander in.
			var target: EnemyState = null
			var waited := 0.0
			while target == null and waited < 150.0:
				for e in Game.room_rt.living_enemies():
					if e.def_id == sp and e.team == "enemy": target = e
				if target == null:
					step(5.0)
					waited += 5.0
			if target == null:
				if verbose: print("  tame: no ", sp, " came back")
				break
			# One blow to show the fight is real, then the careful chipping a player does is a test shortcut: a
			# character this strong kills a low beast outright with a second blow.
			place(target.plane + Vector2(-34, 0))
			submit({"type": "basic_attack", "facing": 1})
			step(0.25)
			if target.alive and target.pools.hp > target.pools.max_hp * 0.25: target.pools.hp = target.pools.max_hp * 0.2
			if not target.alive:
				if verbose: print("  tame: the ", sp, " fell before it could be offered to")
				continue
			place(target.plane + Vector2(-60, 0))
			var r := submit({"type": "use_item", "index": c().inventory.first_index("bonding_offering_common")})
			if verbose: print("  tame ", sp, ": ", r)
			if r.get("ok", false) and r.get("success", false): return true
			revive_if_needed()
	return false

# ------------------------------------------------------------------ Heart Tempering
func sec_ht1() -> void:
	check(reach("heart_tempering_1", ["foundation_guard_pill"]), "Heart Tempering 1")
	# S47: the first Treasure button opens with the Practice Bell.
	check(start("a_treasure_in_hand"), "A Treasure in Hand accepted")
	check(ring_the_bell(3) == 3, "ring the Practice Bell three times")
	check(finish("a_treasure_in_hand"), "A Treasure in Hand done")
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
	# S43: Wall-Step is learned in the Echo Cliffs shaft at Heart Tempering 4.
	check(reach("heart_tempering_4"), "Heart Tempering 4")
	check(start("between_two_walls"), "Between Two Walls accepted")
	check(travel("wg_echo_cliffs"), "reach the Echo Cliffs")
	check(wall_step_shaft() == 3, "kick up the shaft three times")
	check(fight("mist_vulture", 3, 600.0) >= 3, "defeat three Mist Vultures")
	check(finish("between_two_walls"), "Between Two Walls done")

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
	# S48: the core formed with a grade, and a fate was kept at each great breakthrough.
	check(c().cultivator.core_grade >= 4 and c().cultivator.core_grade <= 9 and c().cultivator.purity == c().cultivator.core_grade,
		"the core formed at purity grade %d" % c().cultivator.core_grade)
	check(c().cultivator.fates.size() >= 4, "a fate kept at each great breakthrough so far (%d)" % c().cultivator.fates.size())
	check(start("wings_of_cloud"), "Wings of Cloud accepted")
	check(travel("cc_cliff_faces"), "reach the Cliff Faces")
	take_to_the_air()
	check(fight("cloudwing_crane", 3, 600.0) >= 3, "defeat three Cloudwing Cranes")
	check(finish("wings_of_cloud"), "Wings of Cloud done")
	check(start("riding_the_wind"), "Riding the Wind accepted")
	check(talk_choose(go_to_npc(["hermit_yao"]), "effects", "Hold out"), "bond with a crane that can carry you")
	ride_the_crane()
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
	rare_harvest()
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

## S45: Bend Shore's hundred-year root at its dawn ripening. Its Tide Crab wakes as you climb to it and must fall
## first; a perfect tap keeps the full hundred years.
func rare_harvest() -> void:
	Game.crafting.add_xp(c(), "herb_gathering", 5000.0)   # test shortcut: at least Adept
	tidy_bag(6)
	check(travel("dw_bend_shore"), "back to Bend Shore for its hundred-year root")
	var rg: Dictionary = Game.room_rt.object_def("rare_ginseng_bs")
	var hs := HerbRules.ripen_state(rg, Clock.now_utc())
	if not hs.ripe: Clock.debug_offset_s += float(hs.seconds) + 60.0
	var first := interact("rare_ginseng_bs")
	var uid := int(Game.room_rt.guardians.get("rare_ginseng_bs", -1))
	check(str(first.get("reason", "")) == "guarded" and uid >= 0, "a Tide Crab wakes to guard the ripe root %s" % str(first))
	for i in 8:
		var keeper = Game.room_rt.enemies.get(uid)
		if keeper == null or not keeper.alive: break
		fight("tide_crab", 1, 180.0, 0.3, true)
		revive_if_needed()
	var got := interact("rare_ginseng_bs")
	step(float(got.get("channel", 1.5)) + 0.1)
	var picked := submit({"type": "complete_node", "object": "rare_ginseng_bs", "timing": 0.7})
	check(picked.get("ok", false) and str(picked.get("item", "")) == "riverreed_ginseng_100" and picked.get("perfect", false),
		"with its guardian gone, a perfect hundred-year root %s" % str(picked))

# ------------------------------------------------------------------ Spirit Awakening
func sec_sa1() -> void:
	var weathered := tribulations_weathered
	check(reach("spirit_awakening_1", ["mind_lake_opening_pill"]), "Spirit Awakening 1")
	check(tribulations_weathered > weathered, "a heavenly tribulation stood through into Spirit Awakening")
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
	check(c().inventory.count_including_equipped("sleeping_blade") >= 1, "the Sleeping Blade is in the bag")
	bind_the_blade()
	check(finish("the_sleeping_blade"), "The Sleeping Blade done")
	wake_the_blade()
	# S44: the Abbot's sealed vault answers a Spirit Awakening 3 soul; the Nine-Dragon Cauldron is inside.
	check(travel("ds_abbots_sanctum"), "back at the Abbot's vault")
	check(interact("vault").get("ok", false), "open the sealed vault")
	for l in Game.room_rt.loot.duplicate(): submit({"type": "pick_up", "uid": int(l.uid)})
	check(c().inventory.count_including_equipped("nine_dragon_cauldron") >= 1, "the Nine-Dragon Cauldron is in the vault")
	var ndi: int = c().inventory.first_index("nine_dragon_cauldron")
	if ndi >= 0: check(submit({"type": "equip", "index": ndi}).get("ok", false), "set the Nine-Dragon Cauldron in the furnace slot")
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
	# A personal disciple's cave abode: dense Qi, and it counts as a retreat room.
	var abode := ("ja_" if str(c().training_sect.get("id", "")) == "jade_sect" else "cm_") + "cave_abode"
	check(travel(abode), "the mentor's cave abode opens to a personal disciple")
	check(float(Game.room_rt.def.get("qi_density", 1.0)) >= 2.0, "the cave abode's Qi is dense")
	var bq: Dictionary = Game.progression.query_breakthrough(c(), [])
	check(bq.get("reasons", []).has(Tx.t("sim.progression.retreat_room")), "a breakthrough in the cave abode counts the retreat")
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
	treasures_of_heaven_and_earth()
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

## Natural treasures (Spirit Awakening 8): the Mindwell Lotus behind Crane Falls, the Evergreen
## Heart seed planted on the elder's peak and its first fruit.
func treasures_of_heaven_and_earth() -> void:
	check(start("treasures_of_heaven_and_earth"), "Treasures of Heaven and Earth accepted")
	check(c().inventory.count("evergreen_heart_seed") == 1, "the elder gives an Evergreen Heart seed")
	check(travel("cf_behind_falls"), "go behind Crane Falls")
	check(gather("mindwell_lotus", 1) >= 1, "pick the Mindwell Lotus")
	var peak := "ja_elder_hu_peak" if str(c().training_sect.get("id", "")) == "jade_sect" else "cm_elder_sung_peak"
	check(travel(peak), "climb to the elder's peak")
	var plot := objects_of("treasure_plot")
	check(not plot.is_empty(), "rich earth on the peak")
	if plot.is_empty(): return
	place(Vector2(float(plot[0].at[0]) - 40, float(plot[0].at[1]) + 10))
	interact(str(plot[0].id))
	check(c().inventory.count("evergreen_heart_seed") == 0 and bool(Game.crafting.evergreen_state(c()).get("planted", false)), "plant the Evergreen Heart seed")
	check(finish("treasures_of_heaven_and_earth"), "Treasures of Heaven and Earth done")
	interact(str(plot[0].id))
	check(c().inventory.count("evergreen_heart_fruit") == 0, "no fruit on the day it is planted")
	c().crafting.evergreen.planted_utc = float(c().crafting.evergreen.planted_utc) - 25.0 * 3600.0   # test shortcut: a day passes
	interact(str(plot[0].id))
	check(c().inventory.count("evergreen_heart_fruit") == 1, "the tree bears its first fruit a day later")
	interact(str(plot[0].id))
	check(c().inventory.count("evergreen_heart_fruit") == 1, "one fruit per season")
	var soul_before: float = c().cultivator.soul_cultivation
	var li: int = c().inventory.first_index("mindwell_lotus")
	check(submit({"type": "use_item", "index": li, "confirm": true}).get("ok", false) and c().cultivator.soul_cultivation >= soul_before + 499.0,
		"the Mindwell Lotus feeds the soul")
	Game.inventory.apply_add(c().id, "mindwell_lotus", 1, "test")
	var again := submit({"type": "use_item", "index": c().inventory.first_index("mindwell_lotus"), "confirm": true})
	check(str(again.get("reason", "")) == "once_per_realm", "a second lotus waits for the next great realm %s" % str(again))

# ------------------------------------------------------------------ Heaven Glimpse and the end of Act I
func sec_hg1() -> void:
	# The Nine-Bough Jade Tree answers only an Understanding bottleneck.
	check(reach("spirit_awakening_9"), "Spirit Awakening 9")
	var fill := 0
	while c().cultivator.state != "bottleneck" and fill < 10:
		Game.progression.apply_progress(c().id, 0.0, "test_shortcut", 1.0)
		step(0.2)
		fill += 1
	check(travel("mp_forgotten_monastery"), "reach the Nine-Bough Jade Tree")
	var tree := objects_of("treasure_tree")
	check(not tree.is_empty(), "the Nine-Bough Jade Tree stands at the monastery")
	if not tree.is_empty():
		var stuck := false
		for r0 in Game.progression.query_requirements(c()):
			if not r0.ok and str(r0.cause) == "understanding": stuck = true
		var before := 0.0
		for d in c().cultivator.daos: before += float(c().cultivator.daos[d].get("insight", 0.0))
		place(Vector2(float(tree[0].at[0]) - 60, float(tree[0].at[1]) + 20))
		var jt := interact(str(tree[0].id))
		var after := 0.0
		for d in c().cultivator.daos: after += float(c().cultivator.daos[d].get("insight", 0.0))
		if stuck: check(after > before + 400.0, "the tree deepens the strongest Dao at an Understanding bottleneck (%s)" % str(jt))
		else: check(is_equal_approx(after, before), "the tree stays still when understanding is not the wall")
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
	check(travel("sr_frozen_shrine"), "follow Lu's map to the Frozen Shrine")
	check(finish("beyond_the_valley"), "Beyond the Valley done")
	# S49 master inheritance: the personal-disciple trial made the mentor your master; the last lesson passes a legacy.
	check(str(c().relations.bonds.get("master", "")) in ["elder_hu", "elder_sung"], "your mentor is your master")
	check(start("the_elders_last_lesson"), "The Elder's Last Lesson accepted")
	meditate(62.0)
	check(finish("the_elders_last_lesson"), "The Elder's Last Lesson done")
	check(c().cultivator.inner_arts_known.has("lotus_mind_legacy") or c().cultivator.inner_arts_known.has("drifting_cloud_legacy"), "the master's legacy art is yours")
	check(start("farewells"), "Farewells accepted")
	for npc in ["aunt_ping", "old_ma", "granny_liu", "little_dou", "uncle_guo"]:
		talk(go_to_npc([npc]))
	check(finish("farewells"), "Farewells done")
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

## Act II · chapter 11 (v1.1): the valley save crosses the Ascension Gate and plays the Expanse
## up to Sage 1: the toll warden, the broker, Storm Ward jades, the plains and the Condensing Hall.
func sec_ae1() -> void:
	GameEvents.flush()
	check(c().quests.is_active("through_the_gate") or c().quests.is_done("through_the_gate"), "Through the Gate begins when Act I ends")
	check(travel("ae_landing"), "cross the Ascension Gate into Cloudgate Port")
	check(str(ContentDB.zone_of_room(room()).get("id", "")) == "azure_expanse", "Cloudgate Port lies in the Azure Expanse")
	# A new land: the valley goods go into the port storehouse.
	var stored := 0
	for i in c().inventory.bag.size():
		var it = c().inventory.bag[i]
		if it == null or ContentDB.is_equipment(str(it.id)) or str(it.id) in ["healing_pill", "qi_restoration_pill", "revival_talisman", "rice_ball", "return_charm"]: continue
		if submit({"type": "deposit", "index": i, "count": int(it.get("count", 1))}).get("ok", false): stored += 1
	submit({"type": "claim_all"})
	check(stored > 0 and c().inventory.free_slots() >= 8, "store the valley goods at the port (%d stacks, %d free)" % [stored, c().inventory.free_slots()])
	talk(go_to_npc(["warden_cao"]))
	GameEvents.flush()
	check(c().quests.is_done("through_the_gate"), "Through the Gate done")
	var stones0: int = Game.economy.balance("spirit_stone", c())
	check(start("a_sky_full_of_toll_roads"), "A Sky Full of Toll Roads accepted")
	talk(go_to_npc(["factor_ruan"]))
	talk(go_to_npc(["broker_mu"]))
	check(finish("a_sky_full_of_toll_roads"), "A Sky Full of Toll Roads done")
	check(Game.economy.balance("spirit_stone", c()) > stones0, "chapter 11 pays in Spirit Stones")
	# The plains road stays shut until the broker has explained the storms.
	check(start("storm_in_the_blood"), "Storm in the Blood accepted")
	check(unlocked("storm_ward"), "Storm Ward attunement unlocks with the broker's quest")
	var zone := "azure_expanse"
	for i in 4:
		var r := submit({"type": "attune_jade", "zone": zone, "index": i})
		check(r.get("ok", false), "raise Storm Ward jade %d %s" % [i, str(r.get("reason", ""))])
	check(is_equal_approx(float(c().cultivator.attunement.get(zone, 0.0)), 4.0), "four jades at level 1 give Storm Ward 4")
	var poor := submit({"type": "attune_jade", "zone": zone, "index": 9})
	check(not poor.get("ok", false), "a jade that does not exist cannot be raised")
	check(travel("tp_stormgrass_verge"), "walk out onto the Stormgrass Verge")
	var f: Dictionary = Game.progression.attunement_factors(c())
	check(float(f.dealt) < 1.0 and float(f.taken) > 1.0, "under-attuned on the Verge: deal less, take more (%.2f / %.2f)" % [float(f.dealt), float(f.taken)])
	var got := fight("spark_weasel", 6, 600.0, 0.3)
	check(got >= 6 or c().quests.is_done("storm_in_the_blood"), "hunt six Spark Weasels (%d)" % got)
	if c().inventory.count("storm_shard") < 30:
		Game.inventory.apply_add(c().id, "storm_shard", 30 - c().inventory.count("storm_shard"), "test_shortcut")
	# Feed the jades until the Verge's need is met: then the land stops draining you.
	var guard := 0
	while Game.progression.attunement_value(c(), zone) < Game.progression.attunement_required(room()) and guard < 20:
		var lv: Array = Game.progression.jade_levels(c(), zone)
		var lowest := lv.find(lv.min())
		if not submit({"type": "attune_jade", "zone": zone, "index": lowest}).get("ok", false): break
		guard += 1
	f = Game.progression.attunement_factors(c())
	check(is_equal_approx(float(f.dealt), 1.0) and is_equal_approx(float(f.taken), 1.0), "attuned to the Verge: no penalty (%.2f / %.2f)" % [float(f.dealt), float(f.taken)])
	check(finish("storm_in_the_blood"), "Storm in the Blood done")
	check(start("horns_for_the_furnace"), "Horns for the Furnace accepted")
	var horns := 0
	while c().inventory.count("thunder_horn") < 3 and horns < 12:
		if not defeat("thunderhorn_rhino", "tp_thunderhorn_flats", 2): break
		horns += 1
	if c().inventory.count("thunder_horn") < 3:
		Game.inventory.apply_add(c().id, "thunder_horn", 3 - c().inventory.count("thunder_horn"), "test_shortcut")
	tidy_bag()
	check(finish("horns_for_the_furnace"), "Horns for the Furnace done")
	submit({"type": "claim_all"})
	check(c().inventory.count("sage_condensing_pill") >= 1, "Alchemist Fen condenses a Sage pill")
	check(start("sage"), "Sage accepted")
	check(travel("ae_condensing_hall"), "sit in the Condensing Hall")
	# Sage asks for True Qi of the third grade: nights of Refine Qi seclusion in the hall.
	var nights := 0
	while c().cultivator.purity > 3 and nights < 8:
		if not submit({"type": "enter_seclusion", "focus": "refine_qi"}).get("ok", false): break
		Clock.debug_offset_s += 12.0 * 3600.0
		submit({"type": "claim_offline", "elapsed": 12.0 * 3600.0})
		nights += 1
	check(c().cultivator.purity <= 3, "refine True Qi to the third grade (%d nights, grade %d)" % [nights, c().cultivator.purity])
	check(reach("sage_1"), "Sage 1")
	check(c().cultivator.energy_type == "sage_qi", "Sage Qi flows")
	check(finish("sage"), "Sage done: chapter 11 complete")
	# Loot in the Expanse pays Spirit Stones, not taels.
	check(LootRules.zone_coins("tp_thunderhorn_flats", 100).currency == "spirit_stone", "the Expanse pays loot coins in Spirit Stones")
	# A cross-zone stone costs five times the fee; the end state is kept for previews (--load=…/valley_cp/ae_end).
	Game.account.teleports["cloudgate"] = true
	check(Game.world.teleport_fee("stoneford") == 5 * int(ContentDB.entry("teleport_stones", "stoneford").get("fee_shards", 1)), "teleporting back to the valley costs five times the fee")
	travel("tp_herders_camp")

## Feed the zone's jades (lowest first) until the attunement reaches `need`; shards from the
## test shortcut stand in for the hunting a player does between story beats.
func attune_to(zone: String, need: float) -> void:
	var guard := 0
	while float(c().cultivator.attunement.get(zone, 0.0)) < need and guard < 80:
		var lv: Array = Game.progression.jade_levels(c(), zone)
		var lowest := lv.find(lv.min())
		var cost: int = Game.progression.jade_cost(zone, int(lv[lowest]))
		var shard := str(ContentDB.zone(zone).get("attunement", {}).get("shard", "storm_shard"))
		if c().inventory.count(shard) < cost:
			Game.inventory.apply_add(c().id, shard, cost, "test_shortcut")
		if not submit({"type": "attune_jade", "zone": zone, "index": lowest}).get("ok", false): break
		guard += 1

## Act II · chapter 12 (v1.1 Phase B): the Grey Pilgrim's trail across the plains, the hermit's
## cave on Rimefrost Summit, the Lake Shrine's mirror and the Thousand-Eye Toad.
func sec_ae2() -> void:
	check(start("shards_for_sale"), "Shards for Sale accepted")
	talk(go_to_npc(["herder_suo"]))
	check(travel("tp_lightning_scar"), "reach the Lightning Scar")
	var tracks := 0
	for o in objects_of("inspect"):
		if str(o.id).begins_with("grey_tracks") and interact(str(o.id)).get("ok", false): tracks += 1
	check(tracks == 3, "follow the grey buyer's tracks (%d)" % tracks)
	attune_to("azure_expanse", 16.0)
	talk(go_to_npc(["grey_pilgrim"]))
	check(room() == "rf_frostpine_climb", "the stranger waits on Frostpine Climb")
	check(finish("shards_for_sale"), "Shards for Sale done")
	check(start("frost_and_silence"), "Frost and Silence accepted")
	attune_to("azure_expanse", 22.0)
	check(travel("rf_rimefrost_summit"), "climb to Rimefrost Summit")
	var cave := {}
	for p in Game.room_rt.def.get("portals", []):
		if str(p.id) == "ice_cave": cave = p
	check(not cave.is_empty() and str(cave.type) == "hidden", "the hermit's cave is hidden")
	place(Vector2(float(cave.at[0]), float(cave.at[1]) + 10))
	c().pools.soul = c().pools.max_soul
	c().pools.cooldowns.erase("sense")
	submit({"type": "sense_pulse"})
	check(go("ice_cave") and room() == "rf_hermits_ice_cave", "Spirit Sense finds the Hermit's Ice Cave")
	talk(go_to_npc(["hermit_shuang"]))
	meditate(92.0)
	check(finish("frost_and_silence"), "Frost and Silence done")
	check(reach("sage_2"), "Sage 2")
	check(start("the_mirror_remembers"), "The Mirror Remembers accepted")
	attune_to("azure_expanse", 28.0)
	# Mirrorwater's field boss is Level 68: a player sails there in the port's Spirit-grade stormsteel, not the
	# valley's jadeiron (the same rule as the desert road; a lucky run used to win without it).
	tidy_bag(12)
	gear_up_stones("alliance_factor")
	check(travel("ml_reedless_shore"), "sail the sky-ship to Mirrorwater Lake")
	check(travel("ml_lake_shrine"), "cross the Sentinel Causeway to the Lake Shrine")
	check(interact("mirror_altar").get("ok", false), "look into the bronze mirror")
	var journal := interact("journal_lake")
	check(c().quests.has_flag("journal_lake"), "pick up Lu's journal page at the shrine %s" % str(journal.get("reason", "")))
	c().pools.hp = c().pools.max_hp
	check(defeat("thousand_eye_toad", "ml_toads_hollow", 6), "silence the Thousand-Eye Toad")
	GameEvents.flush()
	check(c().quests.is_done("the_mirror_remembers"), "The Mirror Remembers done: chapter 12 complete")
	travel("ae_port_market")

## Act II · chapter 13 (v1.1 Phase C): a seat at the Hall of Nine, the auction house, the canyon
## toll and adoption into the Ironroot clan; the path can be changed once, for a price.
func sec_ae3() -> void:
	check(start("nine_seats"), "Nine Seats accepted")
	check(travel("np_hall_of_nine"), "sail to Nine Peaks and enter the Hall of Nine")
	check(talk_choose(go_to_npc(["envoy_lanshi"]), "effects", "Alliance"), "take the Alliance seat")
	check(c().quests.has_flag("path_alliance") and c().inventory.count("alliance_token") == 1, "the Alliance token is yours")
	check(finish("nine_seats"), "Nine Seats done")
	# The Alliance Factor gives its members a better price.
	var plain := int(ContentDB.entry("items", "stormsteel_jian").get("price", LootRules.buy_price("stormsteel_jian")))
	var listed := 0
	for row in Game.economy.stock(c(), "alliance_factor"):
		if str(row.item) == "stormsteel_jian": listed = int(row.price)
	check(listed > 0 and listed < int(round(plain * 0.01)) + 1, "the Factor discounts Alliance members (%d stones)" % listed)
	# The auction house: a bid is answered at once inside the bidder's limit; above it, you hold the lot.
	check(start("going_once"), "Going Once accepted")
	check(travel("np_auction_pavilion"), "reach the Auction Pavilion")
	Game.economy.auction_roll()
	var lots: Array = Game.economy.auction_lots().filter(func(l): return not l.get("closed", false))
	check(lots.size() >= 4, "the Pavilion shows today's lots (%d)" % lots.size())
	if not lots.is_empty():
		var lot: Dictionary = lots[0]
		Game.economy.apply_currency("spirit_stone", 2000, "test_shortcut")
		var low := submit({"type": "auction_bid", "lot": str(lot.id), "amount": Game.economy.auction_min_bid(lot)})
		check(low.get("ok", false), "place a bid %s" % str(low.get("reason", "")))
		var before: int = Game.economy.balance("spirit_stone")
		var high_amount := int(lot.cap) + 5
		var high := submit({"type": "auction_bid", "lot": str(lot.id), "amount": maxi(high_amount, Game.economy.auction_min_bid(lot))})
		check(high.get("top", false) and Game.economy.balance("spirit_stone") < before, "a bid past the limit holds the lot and its stones")
		Clock.debug_offset_s += 12.0 * 3600.0
		step(2.5)
		submit({"type": "claim_all"})
		var fresh: Array = Game.economy.auction_lots().filter(func(x): return not x.get("closed", false))
		check(fresh.size() >= 4, "new lots open as old ones close (%d)" % fresh.size())
		check(lot.get("closed", false) and str(lot.bidder) == c().id, "the hammer falls: the lot is yours (%s)" % str(lot.item))
		var mailed := false
		for m in Game.account.mail:
			for a in m.get("attachments", []):
				if str(a.get("item", "")) == str(lot.item): mailed = true
		check(mailed or c().inventory.count_including_equipped(str(lot.item)) >= int(lot.count) or ContentDB.item(str(lot.item)).get("type", "") == "currency_item",
			"the won lot arrives by mail")
	check(finish("going_once"), "Going Once done")
	check(start("the_canyon_toll"), "The Canyon Toll accepted")
	attune_to("azure_expanse", 42.0)
	talk(go_to_npc(["tollkeeper_bai"]))
	var brigands := 0
	for rid in ["gc_canyon_mouth", "gc_windbridge", "gc_canyon_mouth", "gc_windbridge"]:
		if c().quests.is_done("the_canyon_toll") or int(c().quests.active.get("the_canyon_toll", {}).get("progress", [0, 0, 0])[1]) >= 6: break
		if travel(rid): brigands += fight("canyon_brigand", 3, 300.0, 0.3)
		revive_if_needed()
	check(int(c().quests.active.get("the_canyon_toll", {}).get("progress", [0, 0, 0])[1]) >= 6, "break the veiled brigands (%d)" % brigands)
	check(travel("ir_hold_gate"), "cross the Windbridge to Ironroot Hold")
	check(finish("the_canyon_toll"), "The Canyon Toll done")
	check(unlocked("clans") or c().quests.is_active("ironroot_blood") or c().cultivator.offered.has("clans"), "clans open at Sage 2")
	check(start("ironroot_blood"), "Ironroot Blood accepted")
	c().pools.hp = c().pools.max_hp
	var won := false
	for i in 3:
		if won: break
		won = spar_with(func(): return _spar_service(go_to_npc(["ironroot_warden"])))
		c().pools.hp = c().pools.max_hp
	check(won, "pass the warden's test of root")
	talk(go_to_npc(["matriarch_tie"]))
	check(travel("ir_ancestor_hall"), "enter the Ancestor Hall")
	check(interact("ancestral_tablets").get("ok", false), "honour the ancestral tablets")
	check(finish("ironroot_blood"), "Ironroot Blood done: chapter 13 complete")
	check(c().quests.has_flag("clan_ironroot") and "ironroot_kin" in c().cultivator.titles, "adopted into the Ironroot clan")
	# Canyon side stories: silk from the kites for the toll flags, plumes from the roosts for the clan forge.
	check(start("silk_on_the_wind") and start("plumes_for_the_bellows"), "the canyon side stories accepted")
	for i in 12:
		if c().inventory.count("kite_silk") >= 5: break
		if travel("gc_kite_winds"): fight("wind_kite", 2, 240.0, 0.3)
		revive_if_needed()
	for i in 12:
		if c().inventory.count("harpy_plume") >= 4: break
		if travel("gc_harpy_roosts"): fight("canyon_harpy", 2, 240.0, 0.3)
		revive_if_needed()
	check(c().inventory.count("kite_silk") >= 5 and c().inventory.count("harpy_plume") >= 4,
		"silk and plumes from the canyons (%d, %d)" % [c().inventory.count("kite_silk"), c().inventory.count("harpy_plume")])
	check(finish("silk_on_the_wind"), "Silk on the Wind done")
	check(finish("plumes_for_the_bellows"), "Plumes for the Bellows done")
	# One change of path, for a price.
	travel("np_hall_of_nine")
	var stones: int = Game.economy.balance("spirit_stone")
	if stones < 300: Game.economy.apply_currency("spirit_stone", 300 - stones, "test_shortcut")
	check(talk_choose(go_to_npc(["envoy_lanshi"]), "effects", "Change"), "ask the envoy to change paths")
	check(c().quests.has_flag("path_independent") and not c().quests.has_flag("path_alliance") and c().inventory.count("alliance_token") == 0,
		"the free road now, token returned")
	travel("ae_port_market")

## Act II · chapter 14 (v1.1 Phase D): across the Sunscar to the Oasis of Bones, the Dune Worms'
## key, the Sealed Gate's inscription (Insight 80), the Tomb King and the seal, then Sage Sovereign.
func _objective(qid: String, i: int) -> int:
	return int(c().quests.active.get(qid, {}).get("progress", [0, 0, 0, 0, 0])[i])

func sec_ae4() -> void:
	check(reach("sage_3"), "Sage 3")
	check(start("glass_and_bone"), "Glass and Bone accepted")
	attune_to("azure_expanse", 50.0)
	# A player bound for the desert wears the port's Spirit-grade stormsteel and stormsilk.
	tidy_bag(12)
	gear_up_stones("alliance_factor")
	check(travel("sd_oasis_of_bones"), "take the desert road across the Glass Dunes and the Scorpion Flats to the Oasis of Bones")
	for rid in ["sd_scorpion_flats", "sd_glass_dunes", "sd_scorpion_flats", "sd_glass_dunes"]:
		if _objective("glass_and_bone", 1) >= 6: break
		if travel(rid): fight("sandstorm_scorpion", 3, 300.0, 0.3)
		revive_if_needed()
	check(_objective("glass_and_bone", 1) >= 6, "clear the Sandstorm Scorpions from the caravan road")
	check(finish("glass_and_bone"), "Glass and Bone done")
	# The Sealed Gate: the key's pieces are in the Dune Worms; the inscription asks a scholar's eye.
	check(start("the_sealed_gate"), "The Sealed Gate accepted")
	for i in 10:
		if c().inventory.count("sun_seal_shard") >= 3: break
		if travel("sd_worm_sea"): fight("dune_worm", 2, 300.0, 0.3)
		revive_if_needed()
	check(c().inventory.count("sun_seal_shard") >= 3, "cut the three pieces of the key from the Dune Worms")
	check(travel("ts_sealed_gate"), "find the Sealed Gate beyond the Worm Sea")
	if c().stats.value("insight") < 80.0: train_dao(5)
	check(interact("tomb_gate").get("ok", false) and c().quests.has_flag("tomb_gate_opened"), "read the inscription: the bronze doors open")
	var shards_before: int = c().inventory.count("sun_seal_shard")
	check(finish("the_sealed_gate"), "The Sealed Gate done")
	check(c().inventory.count("sun_seal_shard") == shards_before - 3, "the key's three pieces stay with the bone-reader")
	# Sovereign: a full Sage Qi reserve and one Dao at Adaptation; the Settling Pill ends the consolidation.
	check(start("sovereign"), "Sovereign accepted")
	c().pools.qi = c().pools.max_qi
	check(reach("sage_sovereign_1"), "Sage Sovereign 1")
	if c().cultivator.state == "consolidating" or c().cultivator.consolidation_left > 0.0:
		var pi: int = c().inventory.first_index("sovereign_settling_pill")
		check(pi >= 0 and submit({"type": "use_item", "index": pi, "confirm": true}).get("ok", false), "take a Sovereign Settling Pill")
		step(0.5)
		check(c().cultivator.consolidation_left <= 0.0, "the new stage settles at once")
	check(finish("sovereign"), "Sovereign done")
	# Now the tomb.
	check(start("the_tomb_king"), "The Tomb King accepted")
	attune_to("azure_expanse", 55.0)
	# Sage-grade gear from the Ironroot forge, open to kin who have become Sovereigns.
	var atk0: float = c().stats.value("physical_attack")
	var pow0: float = atk0 + c().stats.value("physical_defense")
	travel("ir_clan_hearth")
	tidy_bag(12)
	gear_up_stones("ironroot_clan")
	var pow1: float = c().stats.value("physical_attack") + c().stats.value("physical_defense")
	check(str(ContentDB.item(str(c().inventory.equipped.get("robe", {}).get("id", ""))).get("grade", "")) == "sage" and pow1 > pow0,
		"Sage-grade sunsilk and sunsteel from the clan forge (attack + defence %.0f -> %.0f)" % [pow0, pow1])
	check(travel("ts_mirror_crypt"), "through the Hall of Sand Kings to the Mirror Crypt")
	check(interact("journal_tomb").get("ok", false), "find Lu's page among the mirrors")
	c().pools.hp = c().pools.max_hp
	check(defeat("tomb_king", "ts_throne"), "the Tomb King of Sunscar falls")
	check(c().inventory.count("sunscar_seal") == 1, "the sun seal is yours to take")
	check(talk_choose(go_to_npc(["grey_pilgrim"]), "effects", "keep the seal"), "refuse the Grey Pilgrim: keep the seal")
	check(c().quests.has_flag("seal_kept") and "seal_keeper" in c().cultivator.titles, "Keeper of the Sun Seal")
	check(finish("the_tomb_king"), "The Tomb King done: chapter 14 complete")
	check(c().inventory.count("sunscar_seal") == 1, "the seal stays with you")
	# Side stories of the oasis and the Hold. Gathering Master is a long road (S15): test shortcut.
	Game.crafting.add_xp(c(), "herb_gathering", 20000.0)
	tidy_bag(12)
	check(start("cactus_water") and start("glass_teeth") and start("stingers_for_the_hold"), "the Sunscar side stories accepted")
	for rid in ["sd_glass_dunes", "sd_scorpion_flats", "sd_worm_sea", "sd_glass_dunes"]:
		if c().inventory.count("ember_cactus") >= 4: break
		if travel(rid): gather("ember_cactus", 4 - c().inventory.count("ember_cactus"), 3)
	check(c().inventory.count("ember_cactus") >= 4, "pick Ember Cactus flowers across the dunes (%d)" % c().inventory.count("ember_cactus"))
	for i in 20:   # a tooth drops about one kill in three, but a run can go a long time without
		if c().inventory.count("worm_glass_tooth") >= 3: break
		if travel("sd_worm_sea"): fight("dune_worm", 2, 300.0, 0.3)
		revive_if_needed()
	# The worm hunt fills the bag with glass and shards: make room so every stinger can be picked up.
	tidy_bag(10)
	for i in 16:
		if c().inventory.count("scorpion_stinger") >= 5: break
		if c().inventory.free_slots() < 3: tidy_bag(10)
		if travel("sd_scorpion_flats"): fight("sandstorm_scorpion", 3, 300.0, 0.3)
		revive_if_needed()
	if verbose: print("  stingers: ", c().inventory.count("scorpion_stinger"))
	check(finish("cactus_water"), "Cactus Water done")
	check(finish("glass_teeth"), "Glass Teeth done")
	check(finish("stingers_for_the_hold"), "Stingers for the Hold done")
	check(c().inventory.count("cactus_water") >= 1, "cactus water in the gourd")
	travel("sd_oasis_of_bones")

## S18 Starsea travel through the real intents: walk to the route's dock, set sail, fight off
## whatever boards the vessel while the crossing runs, and make port at the far end.
func sail(route: String) -> bool:
	var v := ContentDB.entry("voyages", route)
	if room() != str(v.get("from", "")) and not travel(str(v.get("from", ""))): return false
	var docks := objects_of("starsea_dock", "route", route)
	if docks.is_empty(): return false
	place(obj_at(str(docks[0].id)) + Vector2(40, 60))
	var r := interact(str(docks[0].id))
	if not r.get("ok", false):
		print("  set sail on ", route, ": ", r)
		return false
	var t0: float = Game.sim_time
	while room() == str(v.crossing) and Game.sim_time - t0 < 240.0:
		var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.team != "ally")
		if foes.is_empty():
			step(1.0)
		else:
			fight(str(foes[0].def_id), 1, 20.0, 0.25)
		if Game.combat.is_wounded(c().id): break
	revive_if_needed()
	return room() == str(v.get("to", ""))

## Hold a set piece's room event: fight what it sends (its win-on-kill foe first) until it ends.
func hold_event(limit_s := 400.0) -> bool:
	var t0: float = Game.sim_time
	var inside := room()
	while room() == inside and Game.room_rt.event.get("active", false) and Game.sim_time - t0 < limit_s:
		var boss := str(Game.room_rt.event.get("win_on_kill", ""))
		var foes: Array = Game.room_rt.living_enemies().filter(func(e): return e.team != "ally")
		var pick := ""
		for e in foes:
			if e.def_id == boss: pick = boss
		if pick == "" and not foes.is_empty(): pick = str(foes[0].def_id)
		# Between blows, a pill when the waves have worn you below half (as a player on the gate would).
		if c().pools.hp < c().pools.max_hp * 0.5:
			var hi: int = c().inventory.first_index("healing_pill")
			if hi >= 0: submit({"type": "use_item", "index": hi})
		if pick == "":
			step(1.0)
		else:
			fight(pick, 1, 30.0, 0.2)
		if Game.combat.is_wounded(c().id): return false
	return not Game.combat.is_wounded(c().id)

func craft_at(station: String, intent: String, recipe: String) -> bool:
	if not go_to_station(station): return false
	place(obj_at(str(objects_of(station)[0].id)) + Vector2(60, 70))
	var r := submit({"type": intent, "recipe": recipe})
	if not r.get("ok", false): print("  ", intent, " ", recipe, ": ", r)
	return r.get("ok", false)

func sec_ae5() -> void:
	# Act II · chapter 15, Pirates of the Starsea (Sage Sovereign 1-2), and the Shipwrights' Yard.
	tidy_bag(12)
	check(unlocked("starsea") and c().cultivator.offered.has("star_charting") and c().cultivator.offered.has("shipwright"),
		"Sage 3: Starsea survival, and the Yard offers star charts and vessels")
	check(unlocked("elder_token") and c().inventory.count(str(ContentDB.entry("sects", str(c().training_sect.id)).token).replace("_token", "_elder_token")) == 1
		and str(c().training_sect.rank) == "elder", "Sage Sovereign 1: the sect token becomes an Elder's token")
	var home_stone := "jade_academy" if str(c().training_sect.id) == "jade_sect" else "cloud_monastery"
	check(Game.world.teleport_fee(home_stone, c()) == 0 and Game.world.teleport_fee("sunscar", c()) > 0, "the Elder's token calls its bearer home for free")
	# A Chart of One's Own: star readings from three sighting stones, sky ink, the chart table.
	check(start("a_chart_of_ones_own"), "A Chart of One's Own accepted")
	for rid in ["ae_shipyard", "rf_rimefrost_summit", "np_presence_terrace", "ae_shipyard"]:
		if c().inventory.count("star_reading") >= 4: break
		if travel(rid): gather("star_reading", 4 - c().inventory.count("star_reading"), 22)
	check(c().inventory.count("star_reading") >= 4, "take four star readings (%d)" % c().inventory.count("star_reading"))
	travel("ae_shipyard")
	check(buy("navigator", "sky_ink", 2), "buy sky ink from Navigator Sun")
	check(craft_at("chart_table", "chart_route", "star_chart_wreck") and c().inventory.count("star_chart_wreck") == 1, "chart the Wreck Run")
	check(finish("a_chart_of_ones_own"), "A Chart of One's Own done")
	# Keel and Ward: a smith's hand (test shortcut for the rank), the Yard's timber and plates, the canyon's plumes.
	check(start("keel_and_ward"), "Keel and Ward accepted")
	if Game.crafting.rank_index(Game.crafting.rank_of(c(), "smithing")) < Game.crafting.rank_index("adept"):
		Game.crafting.add_xp(c(), "smithing", 1000.0)
	for i in 16:   # plumes drop about one kill in five
		if c().inventory.count("harpy_plume") >= 3: break
		if travel("gc_harpy_roosts"): fight("canyon_harpy", 3, 300.0, 0.3)
		revive_if_needed()
	check(c().inventory.count("harpy_plume") >= 3, "harpy plumes for the sail")
	travel("ae_shipyard")
	for need in [["spirit_wood", 6], ["stormsteel_ore", 4], ["formation_stone", 2]]:
		var short: int = int(need[1]) - c().inventory.count(str(need[0]))
		if short > 0: buy("shipwright", str(need[0]), short)
	check(craft_at("shipyard_slip", "build_vessel", "cloud_skiff") and c().inventory.count("cloud_skiff") == 1, "build a Cloud Skiff")
	check(finish("keel_and_ward"), "Keel and Ward done")
	# Two Breaths, One River: meditate beside a companion.
	check(start("two_breaths"), "Two Breaths, One River accepted")
	travel("ae_condensing_hall")
	step(2.0)
	var rate0: float = Game.progression.accumulation_bonus(c())
	var med := submit({"type": "start_meditation"})
	step(3.0)
	if verbose: print("  paired: ", med, " allies ", Game.companions.allies, " meditating ", c().cultivator.meditating, " unlocked ", unlocked("paired_cultivation"),
		" room type ", Game.room_rt.def.get("type", ""))
	check(Game.progression.accumulation_bonus(c()) > rate0 + 0.1, "paired cultivation: a companion beside you speeds the Qi (+%.0f%%)" % ((Game.progression.accumulation_bonus(c()) - rate0) * 100.0))
	step(32.0)
	submit({"type": "stop_meditation"})
	check(finish("two_breaths"), "Two Breaths, One River done")
	# Gu's Ledger.
	check(start("gus_ledger"), "Gu's Ledger accepted")
	for npc in ["broker_mu", "navigator_sun"]:
		var n := go_to_npc([npc])
		if n != "": talk(n)
	check(finish("gus_ledger"), "Gu's Ledger done")
	# The Skyport Wreck: sail the chart, take back the pages, find the seller.
	check(start("the_skyport_wreck"), "The Skyport Wreck accepted")
	attune_to("azure_expanse", 60.0)
	check(sail("wreck_run"), "sail the Wreck Run across the Starsea to the Broken Pier")
	check(c().quests.is_done("the_skyport_wreck") or _objective("the_skyport_wreck", 2) >= 1, "arrive at the Skyport Wreck")
	for rid in ["sw_broken_pier", "sw_pirate_deck", "sw_pirate_deck", "sw_riven_peak", "sw_pirate_deck"]:
		if c().inventory.count("ledger_page") >= 3: break
		if travel(rid): fight("starsea_pirate", 3, 300.0, 0.3)
		revive_if_needed()
	check(c().inventory.count("ledger_page") >= 3, "take three ledger pages from the pirates")
	check(travel("sw_pirate_deck") and talk_choose(go_to_npc(["gu_in_chains"]), "effects", "Break his chains"), "free Elder Gu on the Pirate Deck")
	check(c().quests.has_flag("gu_freed") and c().inventory.count("black_ledger") == 1, "the Black Ledger")
	var box := interact("pirate_strongbox")
	check(box.get("ok", false), "Gu opens the pirates' strongbox")
	check(sail("wreck_run_home"), "sail home to the Shipwrights' Yard")
	var pages_before: int = c().inventory.count("ledger_page")
	check(finish("the_skyport_wreck"), "The Skyport Wreck done")
	check(c().inventory.count("ledger_page") == pages_before - 3, "three ledger pages go into the Black Ledger (%d left over)" % c().inventory.count("ledger_page"))
	# Sect War: Sage Sovereign 2, then hold the Alliance Gate.
	check(start("the_gate_holds"), "Sect War accepted")
	check(reach("sage_sovereign_2"), "Sage Sovereign 2")
	c().pools.hp = c().pools.max_hp
	var held := false
	for i in 3:
		if "sect_war" in c().cultivator.events_passed: break
		stock_up()
		if not travel("np_alliance_gate"): break
		c().pools.hp = c().pools.max_hp
		var g := interact("war_gong_np")
		if not g.get("ok", false) and str(g.get("reason", "")) == "cooldown":
			# Beaten back: a careful player returns when the comet sails have regrouped (about 20 h).
			Clock.debug_offset_s += 21.0 * 3600.0
			c().pools.hp = c().pools.max_hp
			g = interact("war_gong_np")
		if not g.get("ok", false):
			print("  war gong: ", g)
			break
		held = hold_event()
		revive_if_needed()
	check("sect_war" in c().cultivator.events_passed, "the Alliance Gate holds: Comet Captain Rao falls")
	check("gate_defender" in c().cultivator.titles, "Defender of the Alliance Gate")
	if room() == "si_sect_war": go("exit")
	check(talk_choose(go_to_npc(["elder_zhong"]), "effects", "Burn it"), "burn the Black Ledger")
	check(c().quests.has_flag("ledger_burned") and c().inventory.count("black_ledger") == 0, "the valley's debts end in ashes")
	check(finish("the_gate_holds"), "Sect War done: chapter 15 complete")
	# The sect war repeats (S25): the gong answers again once the comet sails have regrouped.
	travel("np_alliance_gate")
	var again := interact("war_gong_np")
	check(not again.get("ok", false) and str(again.get("reason", "")) == "cooldown", "the war gong waits for the comet sails to regroup")
	# Side stories of the Wreck.
	check(start("the_deserters") and start("iron_from_a_comet"), "the Wreck's side stories accepted")
	check(sail("wreck_run"), "back across the Starsea")
	for i in 10:
		if _objective("the_deserters", 0) >= 6 and c().inventory.count("alliance_badge") >= 4: break
		if travel("sw_broken_pier"): fight("nine_peaks_disciple", 3, 300.0, 0.3)
		revive_if_needed()
	for i in 10:
		if c().inventory.count("comet_iron") >= 6: break
		if travel("sw_pirate_deck"): fight("starsea_pirate", 3, 300.0, 0.3)
		revive_if_needed()
	check(sail("wreck_run_home"), "home again")
	check(finish("the_deserters"), "The Deserters done")
	check(finish("iron_from_a_comet") and Game.crafting.knows(c(), "storm_sloop"), "Iron from a Comet done: the storm sloop's lines")

func sec_ae6() -> void:
	# Act II · chapter 16, The Presence Trial (Sage Sovereign 3), and the rare Daos of the Expanse's teachers.
	tidy_bag(12)
	# Blood Remembers: kneel before the Ironroot tablets.
	check(start("blood_remembers"), "Blood Remembers accepted")
	check(travel("ir_ancestor_hall") and interact("ancestral_tablets").get("ok", false), "kneel before the tablets")
	check(finish("blood_remembers"), "Blood Remembers done")
	check(int(c().cultivator.daos.get("blood", {}).get("tier", 0)) >= 1, "the Blood Dao opens (tier %d)" % int(c().cultivator.daos.get("blood", {}).get("tier", 0)))
	var hp0: float = c().stats.value("max_hp")
	Game.progression.apply_insight(c().id, "blood", 300.0, "test_shortcut")
	check(c().stats.value("max_hp") >= hp0, "Blood Dao tiers add their modifiers")
	# What the Bones Say: shards of the Terracotta Wardens.
	check(start("what_the_bones_say"), "What the Bones Say accepted")
	for i in 20:   # about one kill in three leaves a shard: keep at it, as a player would
		if c().inventory.count("terracotta_shard") >= 3: break
		if travel("ts_hall_of_sand_kings"): fight("terracotta_warden", 2, 300.0, 0.3)
		revive_if_needed()
	check(finish("what_the_bones_say") and c().cultivator.daos.has("life_death"), "What the Bones Say done: the Life and Death Dao")
	# Lu's Last Page.
	check(start("lus_last_page"), "Lu's Last Page accepted")
	check(sail("wreck_run"), "sail to the Wreck")
	check(travel("sw_riven_peak") and interact("journal_riven").get("ok", false), "Lu's last page on the Riven Peak")
	# The Lantern Run's readings while the stars are clear.
	for i in 3:
		if c().inventory.count("star_reading") >= 8: break
		gather("star_reading", 8 - c().inventory.count("star_reading"), 25)
	check(travel("sw_starsea_launch"), "on to the Starsea Launch")
	check(teleport_home(), "the Launch's teleport stone carries you back to Cloudgate")
	check(finish("lus_last_page"), "Lu's Last Page done")
	# The Presence Trial: Sage Sovereign 3, then sit beneath the ninth seat.
	check(start("the_presence_trial"), "The Presence Trial accepted")
	check(reach("sage_sovereign_3"), "Sage Sovereign 3")
	var will0: float = c().stats.value("will")
	var pi: int = c().inventory.first_index("will_tempering_pill")
	if pi >= 0: submit({"type": "use_item", "index": pi, "confirm": true})
	check(c().stats.value("will") > will0 or pi < 0, "a Will Tempering Pill steadies the will (%.0f -> %.0f)" % [will0, c().stats.value("will")])
	for i in 3:
		if "presence_trial" in c().cultivator.events_passed: break
		stock_up()
		if not travel("np_trial_hall"): break
		c().pools.hp = c().pools.max_hp
		var r := interact("presence_gate")
		if not r.get("ok", false):
			print("  presence gate: ", r)
			break
		hold_event(120.0)
		revive_if_needed()
		if room().begins_with("sw_"): teleport_home()   # revived at the Wreck's last shrine
	check("presence_trial" in c().cultivator.events_passed, "the Presence Trial is passed")
	if room() == "si_presence_trial": go("exit")
	check(finish("the_presence_trial"), "The Presence Trial done")
	var q: Dictionary = Game.progression.query_breakthrough(c(), [])
	check(str(q.get("to", "")) == "will_manifest_1" and not q.can, "the Expanse cannot hold a Will Manifest: the zone ceiling locks it")
	# Stars Beyond: chart the Lantern Run, stand at the Launch.
	check(start("stars_beyond"), "Stars Beyond accepted")
	travel("ae_shipyard")
	check(buy("navigator", "recipe_scroll", 1) or Game.crafting.knows(c(), "star_chart_lantern"), "the navigator's lesson for the Lantern Run")
	var sc: int = c().inventory.first_index("recipe_scroll")
	if sc >= 0 and not Game.crafting.knows(c(), "star_chart_lantern"): submit({"type": "use_item", "index": sc, "confirm": true})
	var ink: int = 4 - c().inventory.count("sky_ink")
	if ink > 0: buy("navigator", "sky_ink", ink)
	for rid in ["ae_shipyard", "np_presence_terrace", "rf_rimefrost_summit", "ae_shipyard"]:
		if c().inventory.count("star_reading") >= 8: break
		if travel(rid): gather("star_reading", 8 - c().inventory.count("star_reading"), 22)
	check(craft_at("chart_table", "chart_route", "star_chart_lantern"), "chart the Lantern Run")
	check(sail("wreck_run"), "sail to the Wreck")
	check(travel("sw_starsea_launch"), "reach the Starsea Launch")
	check(finish("stars_beyond"), "Stars Beyond done: chapter 16 and Act II complete")
	check("starsea_voyager" in c().cultivator.titles and c().quests.has_flag("stars_beyond_done"), "Voyager of the Starsea")
	checkpoint("ae_end")

## Act III · chapter 17 (v1.2 Phase A): the Lantern Run, Lanternfall Harbor, Sage Crystals, Starsea Endurance,
## Will Manifest and the first Presence.
func sec_ls1() -> void:
	tidy_bag(12)
	check(c().quests.is_active("the_lantern_run") or c().quests.is_done("the_lantern_run"), "The Lantern Run begins when Act II ends")
	check(sail("lantern_run"), "sail the Lantern Run across the Starsea")
	check(str(ContentDB.zone_of_room(room()).get("id", "")) == "lantern_star_field", "Lanternfall Harbor lies in the Lantern Star Field")
	talk(go_to_npc(["harbormaster_lin"]))
	GameEvents.flush()
	check(c().quests.is_done("the_lantern_run"), "The Lantern Run done")
	check(start("crystal_and_jade"), "Crystal and Jade accepted")
	talk(go_to_npc(["clerk_yu"]))
	if Game.economy.balance("spirit_stone", c()) < 500: Game.economy.apply_currency("spirit_stone", 500, "test_shortcut")
	var crystals0: int = Game.economy.balance("sage_crystal", c())
	var ex := submit({"type": "exchange_currency", "from": "spirit_stone", "to": "sage_crystal", "amount": 500})
	check(ex.get("ok", false) and Game.economy.balance("sage_crystal", c()) == crystals0 + 40, "500 Spirit Stones buy 40 Sage Crystals (10 to one, less the fifth)")
	talk(go_to_npc(["warden_xiao"]))
	check(finish("crystal_and_jade"), "Crystal and Jade done")
	check(start("salt_of_the_stars"), "Salt of the Stars accepted")
	check(unlocked("starsea_endurance"), "Starsea Endurance attunement unlocks with the Warden's quest")
	var zone := "lantern_star_field"
	for i in 4:
		check(submit({"type": "attune_jade", "zone": zone, "index": i}).get("ok", false), "raise Starsea Endurance jade %d" % i)
	check(is_equal_approx(float(c().cultivator.attunement.get(zone, 0.0)), 6.0), "four jades at level 1 give Endurance 6 (each level is worth 1.5)")
	attune_to(zone, 24.0)
	check(travel("dr_jellyfish_shallows"), "wade into the Jellyfish Shallows")
	var f: Dictionary = Game.progression.attunement_factors(c())
	check(float(f.dealt) >= 1.0 and float(f.taken) <= 1.0, "attuned to the Shallows: no penalty (%.2f / %.2f)" % [float(f.dealt), float(f.taken)])
	var got := fight("star_jellyfish", 6, 600.0, 0.3)
	check(got >= 6 or c().quests.is_done("salt_of_the_stars"), "thin six Star Jellyfish (%d)" % got)
	if c().inventory.count("star_shard") < 12: Game.inventory.apply_add(c().id, "star_shard", 12 - c().inventory.count("star_shard"), "test_shortcut")
	check(finish("salt_of_the_stars"), "Salt of the Stars done")
	check(start("will_manifest"), "Will Manifest accepted")
	check(travel("dr_moored_hulks"), "sit on the Moored Hulks")
	if c().pools.max_soul < 1500.0:
		# Soul cultivation to the 1,500 the step asks (the Soul pool grows with it): a test shortcut for weeks of nourishing.
		c().cultivator.soul_cultivation += 1500.0
		Game.combat.refresh_stats(c().id)
	check(c().pools.max_soul >= 1500.0, "Max Soul %d reaches 1,500" % int(c().pools.max_soul))
	check(reach("will_manifest_1"), "Will Manifest 1")
	check(finish("will_manifest"), "Will Manifest done")
	check(start("a_presence_of_ones_own"), "A Presence of One's Own accepted")
	check(unlocked("presence") and Game.is_revealed("hud:presence"), "Presence unlocks, and its button shows")
	c().pools.soul = c().pools.max_soul
	check(submit({"type": "toggle_presence"}).get("ok", false), "hold the Presence")
	check(travel("dr_sparrow_reefs"), "on to the Sparrow Reefs")
	if not Game.field.is_on(c().id): submit({"type": "toggle_presence", "on": true})
	var hunted := fight("comet_sparrow", 5, 600.0, 0.3)
	check(hunted >= 5 or c().quests.is_done("a_presence_of_ones_own"), "hunt five Comet Sparrows under the Presence (%d)" % hunted)
	check(Game.field.presence_xp(c()) > 0.0, "pressing them trains the Presence (%.0f)" % Game.field.presence_xp(c()))
	if Game.field.presence_level(c()) < 2: Game.field.apply_presence_xp(c().id, 60.0, "test_shortcut")
	check(finish("a_presence_of_ones_own"), "A Presence of One's Own done: chapter 17 complete")
	submit({"type": "toggle_presence", "on": false})
	LootRules.zone_coins("dr_sparrow_reefs", 100)
	check(LootRules.zone_coins("dr_sparrow_reefs", 400).currency == "sage_crystal", "the Field pays loot coins in Sage Crystals")
	var q: Dictionary = Game.progression.query_breakthrough(c(), [])
	check(str(q.get("to", "")) == "will_manifest_2", "the Field holds the next order of Will Manifest")
	checkpoint("ls1_end")

## Act III · chapter 18 (v1.2 Phase B): Blackmast Haven, the Gunners' Battery, Gu the purser, Admiral Voss and the first
## Presence clash.
func sec_ls2() -> void:
	tidy_bag(12)
	var zone := "lantern_star_field"
	check(start("the_pursers_ledger"), "The Purser's Ledger accepted")
	talk(go_to_npc(["harbormaster_lin"]))
	attune_to(zone, 34.0)
	check(travel("bm_blackmast_docks"), "follow the lanes to Blackmast Haven")
	var shards0: int = c().inventory.count("star_shard")
	var storm0: int = c().inventory.count("storm_shard")
	var got := fight("starsea_pirate", 6, 600.0, 0.3)
	check(got >= 6 or c().quests.is_done("the_pursers_ledger"), "cut down six of the Admiral's pirates (%d)" % got)
	check(c().inventory.count("storm_shard") == storm0 and c().inventory.count("star_shard") >= shards0,
		"the Starsea pirates leave star shards in the Field, not storm shards")
	check(finish("the_pursers_ledger"), "The Purser's Ledger done")
	check(start("gunners_battery"), "Gunners' Battery accepted")
	attune_to(zone, 36.0)
	check(travel("bm_gunners_battery"), "climb to the Gunners' Battery")
	var spiked := 0
	for i in 3:
		place(obj_at("cannon_%d" % i) + Vector2(40, 60))
		if interact("cannon_%d" % i).get("ok", false): spiked += 1
	check(spiked == 3, "spike the three cannons (%d)" % spiked)
	var gunners := fight("pirate_gunner", 4, 600.0, 0.3)
	check(gunners >= 4 or _objective("gunners_battery", 1) >= 4, "silence four gunners (%d)" % gunners)
	# The cove under the battery: a hidden door that Spirit Sense shows.
	var cove: Dictionary = {}
	for pp in Game.room_rt.def.get("portals", []):
		if str(pp.id) == "cove": cove = pp
	place(Vector2(float(cove.at[0]), float(cove.at[1]) + 10))
	c().pools.soul = c().pools.max_soul
	c().pools.cooldowns.erase("sense")
	submit({"type": "sense_pulse"})
	check(go("cove") and room() == "bm_smugglers_cove", "Spirit Sense shows the smugglers' door")
	talk(go_to_npc(["gu_the_purser"]))
	check(_objective("gunners_battery", 2) >= 1, "find Elder Gu counting the Admiral's money")
	go("entry")
	check(reach("will_manifest_2"), "Will Manifest 2")
	check(finish("gunners_battery"), "Gunners' Battery done")
	check(start("the_admiral"), "The Admiral accepted")
	c().pools.soul = c().pools.max_soul
	var clashed := [false]
	var seen := func(n, _p): if str(n) == "presence_clash": clashed[0] = true
	GameEvents.event.connect(seen)
	var won := false
	for i in 4:
		stock_up()
		if not travel("bm_flagship_deck"): break
		c().pools.soul = c().pools.max_soul
		if not Game.field.is_on(c().id): submit({"type": "toggle_presence", "on": true})
		if fight("admiral_voss", 1, 900.0, 0.0, true) >= 1:
			won = true
			break
		revive_if_needed()
	GameEvents.event.disconnect(seen)
	check(won, "Admiral Voss falls on his own deck")
	check(clashed[0], "his Presence met yours: the first clash")
	submit({"type": "toggle_presence", "on": false})
	for i in 3:
		if c().inventory.count("admirals_seal") > 0: break
		step(1.0)
		for l in Game.room_rt.loot.duplicate():
			if str(l.get("item", "")) == "admirals_seal": place(Vector2(float(l.x), float(l.y)))
	if c().inventory.count("admirals_seal") < 1: Game.inventory.apply_add(c().id, "admirals_seal", 1, "test_shortcut")
	check(finish("the_admiral"), "The Admiral done: chapter 18 complete")
	check("admiral_breaker" in c().cultivator.titles and c().quests.has_flag("gu_fled"), "Breaker of the Blackmast; Gu fled into the Hollow Wake")
	checkpoint("ls2_end")

## Act III · chapter 19 (v1.2 Phase B): star-tier beasts, the Hollowed brood and the Hollowing past half, the last
## star-wyrm egg, and the Sect Master's seat in the valley.
func sec_ls3() -> void:
	tidy_bag(12)
	var zone := "lantern_star_field"
	attune_to(zone, 48.0)
	check(travel("wn_nest_cliffs"), "take Old Bo's skiff to the Wyrmnest Isles")
	check(start("star_tier_beasts"), "Star-Tier Beasts accepted")
	check(unlocked("star_beasts"), "star-tier beasts answer a Will Manifest 2")
	var pets0: int = c().pets.size()
	var tamed := false
	for attempt in 12:
		if c().inventory.count("bonding_offering_heaven") < 1: Game.inventory.apply_add(c().id, "bonding_offering_heaven", 3, "test")
		var target: EnemyState = null
		var waited := 0.0
		while target == null and waited < 120.0:
			for e in Game.room_rt.living_enemies():
				if e.def_id == "comet_sparrow" and e.team == "enemy": target = e
			if target == null:
				step(5.0)
				waited += 5.0
		if target == null: break
		place(target.plane + Vector2(-60, 0))
		target.pools.hp = target.pools.max_hp * 0.2   # the careful chipping a player does (test shortcut)
		var r := submit({"type": "use_item", "index": c().inventory.first_index("bonding_offering_heaven")})
		if r.get("ok", false) and r.get("success", false):
			tamed = true
			break
		revive_if_needed()
	check(tamed and c().pets.size() > pets0, "a Comet Sparrow chooses you")
	check(finish("star_tier_beasts"), "Star-Tier Beasts done")
	check(start("a_hollowed_brood"), "A Hollowed Brood accepted")
	check(travel("wn_eggshell_terraces"), "on to the Eggshell Terraces")
	var brood := fight("hollowed_wyrmling", 6, 600.0, 0.3)
	check(brood >= 6 or _objective("a_hollowed_brood", 0) >= 6, "put six Hollowed Wyrmlings to rest (%d)" % brood)
	check(c().pools.hollowing > 0.0, "their grey fire leaves Hollowing (%.0f%%)" % c().pools.hollowing)
	var h0: float = c().pools.hollowing
	check(submit({"type": "use_item", "index": c().inventory.first_index("lantern_incense"), "confirm": true}).get("ok", false), "burn Lantern Incense")
	check(c().pools.hollowing < h0 or h0 <= 0.0, "the incense draws the grey out (%.0f -> %.0f)" % [h0, c().pools.hollowing])
	check(finish("a_hollowed_brood"), "A Hollowed Brood done")
	check(start("the_last_egg"), "The Last Egg accepted")
	check(travel("wn_hatching_cave"), "climb to the Hatching Cave")
	var guard := fight("nest_guardian", 1, 600.0, 0.0, true)
	check(guard >= 1 or _objective("the_last_egg", 1) >= 1, "get past the Brood Guardian")
	place(obj_at("last_egg") + Vector2(0, 20))
	interact("last_egg")
	check(c().inventory.count("wyrm_egg") >= 1, "the last star-wyrm egg")
	var egg_i: int = c().inventory.first_index("wyrm_egg")
	var inc := submit({"type": "use_item", "index": egg_i, "confirm": true})
	check(inc.get("ok", false) and c().eggs.size() >= 1, "warm the egg %s" % str(inc.get("reason", "")))
	var egg: Dictionary = c().eggs[c().eggs.size() - 1] if not c().eggs.is_empty() else {}
	check(str(egg.get("species", "")) == "hatchling_wyrm" and str(egg.get("hatch_realm", "")) == "sphere_lord_2", "a Hatchling Wyrm, waiting for Sphere Lord 2")
	Clock.debug_offset_s += 30.0 * 3600.0
	var early := Game.pets.hatch_egg(c(), c().eggs.size() - 1)
	check(not early.get("ok", true) and str(early.get("reason", "")) == "realm", "however long it is warmed, it will not hatch below Sphere Lord 2")
	check(finish("the_last_egg"), "The Last Egg done")
	check(reach("will_manifest_3"), "Will Manifest 3")
	var jade := str(c().training_sect.get("id", "")) == "jade_sect"
	var mentor := "elder_hu" if jade else "elder_sung"
	check(teleport_from("lh_harbor_market", "stone_lanternfall", "jade_academy" if jade else "cloud_monastery"), "the Lanternfall stone carries you home to the valley")
	check(start("the_masters_seat"), "The Master's Seat accepted")
	talk(go_to_npc([mentor]))
	check(finish("the_masters_seat"), "The Master's Seat done: chapter 19 complete")
	check(str(c().training_sect.get("rank", "")) == "sect_master" and "sect_master" in c().cultivator.titles, "Sect Master of your sect")
	var q: Dictionary = Game.progression.query_breakthrough(c(), [])
	check(str(q.get("to", "")) == "sphere_lord_1", "the next step is Sphere Lord")
	checkpoint("ls3_end")

## Walk to a teleport stone and take it to another (a cross-zone jump costs five times the fee).
func teleport_from(stone_room: String, stone_obj: String, to_stone: String) -> bool:
	if not travel(stone_room): return false
	place(obj_at(stone_obj) + Vector2(40, 40))
	interact(stone_obj)
	Game.account.teleports[to_stone] = true
	if c().inventory.count("spirit_stone_shard") < 20: Game.inventory.apply_add(c().id, "spirit_stone_shard", 20, "test_shortcut")
	var r := submit({"type": "teleport", "stone": to_stone})
	if not r.get("ok", false): print("  teleport to ", to_stone, ": ", r)
	return r.get("ok", false)

## From the Skyport Wreck back to the Expanse: the Launch's teleport stone (cross-region fee).
func teleport_home() -> bool:
	if not travel("sw_starsea_launch"): return false
	interact("stone_skyport")
	var r := submit({"type": "teleport", "stone": "cloudgate"})
	if not r.get("ok", false): print("  teleport home: ", r)
	return r.get("ok", false)

## The mini-game through intents: each strike's distance from the band centre, then the craft.
func strike_steps(recipe: String, craft: String, offsets: Array) -> void:
	for o in offsets: submit({"type": "craft_step", "recipe": recipe, "craft": craft, "offset": o})

## The five-screen furnace through intents (S15): each herb held in its band a little off the mark, every impurity
## tapped, the essences merged in order with the array turned `offset` from each mark, and the pill condensed as late.
func refine_with(recipe: String, count: int, offsets: Array) -> Dictionary:
	var off := float(offsets[0]) if not offsets.is_empty() else 0.05
	var lit := submit({"type": "start_refine", "recipe": recipe, "count": count, "array": Game.crafting.suited_array(recipe)})
	if not lit.get("ok", false): return lit
	for i in (lit.plan.herbs as Array).size():
		var ex := submit({"type": "refine_input", "step": "extraction", "value": {"herb": i, "held": 1.0 - off, "taps": (lit.plan.herbs[i].specks as Array).size()}})
		if not ex.get("ok", false): return ex
	var marks: Array = []
	for m in lit.plan.marks: marks.append(off)
	var fu := submit({"type": "refine_input", "step": "fusion", "value": {"order": lit.plan.order, "marks": marks}})
	if not fu.get("ok", false) or fu.has("quality") or fu.has("pending"): return fu
	return submit({"type": "refine_input", "step": "condensation", "value": {"offset": off}})

func forge_with(recipe: String, offsets: Array) -> Dictionary:
	strike_steps(recipe, "smithing", offsets)
	return submit({"type": "forge", "recipe": recipe})

## Cloud Stride flight through the real solver: Combat grants it and pays QI; the body climbs,
## holds its altitude, then descends and lands on the ground.
## S43 movement arts go through the body's own authority, so their art_used events reach the quests.
func body_authority() -> LocalAuthority:
	if st == null: place(Vector2(float(c().position.x), float(c().position.y)))
	var la := LocalAuthority.new(st, Game.room_rt.geometry)
	la.actor_id = c().id
	# The body knows the movement arts its character has learned (the player node does this each frame).
	for sa in c().cultivator.secret_arts:
		var art := str(ContentDB.entry("secret_arts", str(sa)).get("movement_art", ""))
		if art != "": st.arts[art] = true
	return la

var body_seq := 0
func body_step(la: LocalAuthority, seconds: float, axis := Vector2.ZERO, speed := 205.0) -> void:
	var t := 0.0
	while t < seconds - 0.0001:
		body_seq += 1
		la.move(body_seq, axis, 1.0 / 60.0, speed)
		t += 1.0 / 60.0
	GameEvents.flush()

## Jump from the room's spawn point and press again near the top: Cloud Ladder Step.
func double_jumps(times: int) -> int:
	var sp: Array = Game.room_rt.def.get("spawn_point", [700, 850])
	var used := 0
	for i in times:
		place(Vector2(float(sp[0]), float(sp[1])))
		var la := body_authority()
		la.jump()
		body_step(la, 0.4)
		if la.jump() and st.jumps_used == 2: used += 1
		for k in 120:
			if st.surface != null: break
			body_step(la, 1.0 / 60.0)
	return used

## The Echo Cliffs shaft: two rock walls 100 apart. Kick off one, drift across, kick off the other.
func wall_step_shaft() -> int:
	place(Vector2(1368, 690))
	var la := body_authority()
	var kicks := 0
	var side := -1
	la.jump()
	body_step(la, 0.25)
	for i in 3:
		if la.wall_step(side) != 0: kicks += 1
		elif verbose: print("  no wall at x %.0f alt %.0f side %d" % [st.plane.x, st.altitude, side])
		body_step(la, 0.2, Vector2(-side, 0), MovementSolver.WALL_KICK_SPEED)
		body_step(la, 0.05)
		side = -side
	for k in 300:
		if st.surface != null: break
		body_step(la, 1.0 / 60.0)
	return kicks

## Jump and Plunge: Down + Attack in the air; the landing strikes (Combat resolves it on the next tick).
func plunges(times: int) -> int:
	var sp: Array = Game.room_rt.def.get("spawn_point", [700, 850])
	var done := 0
	for i in times:
		c().pools.cooldowns.erase("plunge")
		place(Vector2(float(sp[0]), float(sp[1])))
		var la := body_authority()
		la.jump()
		body_step(la, 0.35)
		if submit({"type": "plunge"}).get("ok", false): done += 1
		for k in 120:
			if st.surface != null: break
			body_step(la, 1.0 / 60.0)
		Game.tick(0.05)
	return done

## Jump, and once falling hold Jump: Falling Leaf Glide (2 QI a second).
func glides(times: int) -> int:
	var sp: Array = Game.room_rt.def.get("spawn_point", [700, 850])
	var done := 0
	for i in times:
		c().pools.qi = c().pools.max_qi
		place(Vector2(float(sp[0]), float(sp[1])))
		var la := body_authority()
		la.jump()
		body_step(la, 0.5)
		if submit({"type": "glide", "on": true}).get("ok", false): done += 1
		for k in 240:
			if st.surface != null: break
			body_step(la, 1.0 / 60.0, Vector2(1, 0))
			Game.tick(1.0 / 60.0)
	return done

## Jump and tap Evade in the air: Swallow Dart, waiting out the dodge's cooldown between darts.
func air_dashes(times: int) -> int:
	var sp: Array = Game.room_rt.def.get("spawn_point", [700, 850])
	var done := 0
	for i in times:
		c().pools.cooldowns.erase("dodge")
		place(Vector2(float(sp[0]), float(sp[1])))
		var la := body_authority()
		la.jump()
		body_step(la, 0.3)
		if submit({"type": "dodge", "direction": Vector2(1, 0), "facing": 1}).get("air_dash", false): done += 1
		for k in 120:
			if st.surface != null: break
			body_step(la, 1.0 / 60.0)
			Game.tick(1.0 / 60.0)
	return done

## Sprint at the pond and keep running: Water Skimming over deep water to its far side.
func skim_the_pond() -> bool:
	place(Vector2(560, 740))
	var la := body_authority()
	st.sprinting = true
	var skimmed := false
	for k in 150:
		body_step(la, 1.0 / 60.0, Vector2(1, 0), 348.0)
		if st.water.get("skimming", false): skimmed = true
		if st.plane.x > 1090.0: break
	st.sprinting = false
	return skimmed and not st.drowned and st.plane.x > 1070.0

## Set the Practice Bell in Treasure button 1 and ring it, waiting out its cooldown between rings.
func ring_the_bell(times: int) -> int:
	submit({"type": "set_treasure", "slot": 0, "item": "practice_bell"})
	var rung := 0
	for i in times:
		c().pools.qi = c().pools.max_qi
		var r := submit({"type": "use_treasure", "slot": 0})
		if r.get("ok", false): rung += 1
		elif verbose: print("  bell: ", r)
		for k in 104: Game.tick(0.25)
	GameEvents.flush()
	return rung

func take_to_the_air() -> void:
	place(Vector2(700, 850))
	c().pools.qi = c().pools.max_qi
	var r := submit({"type": "start_flight"})
	check(r.get("ok", false), "take to the air %s" % str(r.get("reason", "")))
	if not r.get("ok", false): return
	MovementSolver.start_flight(st, float(r.climb), float(r.ceiling))
	var geo: ZoneGeometry = Game.room_rt.geometry
	var qi0: float = c().pools.qi
	st.climb = 1.0
	for i in 40:
		MovementSolver.advance(st, geo, 0.05, Vector2(80, 0))
		Game.tick(0.05)
	var high: float = st.altitude
	st.climb = 0.0
	for i in 20:
		MovementSolver.advance(st, geo, 0.05, Vector2.ZERO)
		Game.tick(0.05)
	var held := absf(st.altitude - high) < 0.5
	st.climb = -1.0
	for i in 100:
		MovementSolver.advance(st, geo, 0.05, Vector2.ZERO)
		Game.tick(0.05)
		if not st.flying: break
	submit({"type": "stop_flight", "reason": "landed"})
	check(high > 150.0 and high <= float(r.ceiling) + 0.01, "flight climbs to at most the ceiling (%.0f px)" % high)
	check(held, "flight holds its altitude")
	check(not st.flying and st.surface != null, "descending onto the ground lands")
	check(c().pools.qi < qi0 and not Game.combat.is_flying(c().id), "flight costs QI and ends on landing")

## S14 binding: a found relic's power is sealed until bound; then its spirit can be challenged.
func bind_the_blade() -> void:
	var idx: int = c().inventory.first_index("sleeping_blade")
	check(idx >= 0 and c().inventory.bag[idx].get("sealed", false), "a found relic starts sealed")
	travel("ja_elder_hu_peak")   # bind where no blow can break the channel
	var old_weapon = c().inventory.equipped.get("weapon")
	var old_uid := int(old_weapon.get("uid", -1)) if old_weapon is Dictionary else -1
	check(submit({"type": "equip", "index": c().inventory.first_index("sleeping_blade")}).get("ok", false), "hold the sealed blade")
	var sealed_atk: float = c().stats.value("physical_attack")
	var r := submit({"type": "bind_item", "slot": "weapon"})
	check(r.get("ok", false), "begin binding %s" % str(r.get("reason", "")))
	step(float(r.get("seconds", 20)) + 0.5)
	if Game.inventory.binding.has(c().id) and verbose: print("  binding still running: ", Game.inventory.binding)
	var blade = c().inventory.equipped.get("weapon")
	check(blade is Dictionary and not blade.get("sealed", false) and blade.get("bound", false), "the Sleeping Blade is bound")
	check(c().stats.value("physical_attack") > sealed_atk * 1.2, "a bound relic wakes its power (%.0f → %.0f attack)" % [sealed_atk, c().stats.value("physical_attack")])
	# S47 Artifact Spirit depth: the spirit answers only a hand it knows, and only where it slept.
	var s := submit({"type": "subdue_spirit", "slot": "weapon"})
	check(str(s.get("reason", "")) == "affinity", "a spirit that does not know you will not answer (%s)" % str(s.get("reason", "")))
	# Back to the weapon the run was built around.
	if old_uid >= 0:
		for i in c().inventory.bag.size():
			var it = c().inventory.bag[i]
			if it is Dictionary and int(it.get("uid", -2)) == old_uid:
				submit({"type": "equip", "index": i})
				break

## S47 Artifact Spirit depth: the blade's awakening quest. Two gifts of its favourite win its trust; it wakes only in the
## Abbot's sanctum, where it slept.
func wake_the_blade() -> void:
	check(start("the_blade_spirit"), "The Blade That Sleeps No More accepted")
	var old_weapon = c().inventory.equipped.get("weapon")
	var old_uid := int(old_weapon.get("uid", -1)) if old_weapon is Dictionary else -1
	var bi: int = c().inventory.first_index("sleeping_blade")
	if bi >= 0: submit({"type": "equip", "index": bi})
	Game.inventory.apply_add(c().id, "refining_essence", 2, "test")
	for i in 2: submit({"type": "gift_spirit", "item": "refining_essence"})
	var blade = c().inventory.equipped.get("weapon")
	check(blade is Dictionary and float(blade.get("spirit_affinity", 0.0)) >= 30.0 and c().quests.has_flag("spirit_close:sleeping_blade"),
		"two gifts of its favourite and the spirit knows your hand")
	check(travel("ds_abbots_sanctum"), "carry the blade back to the Abbot's sanctum")
	var s := {}
	for i in 4:
		Game.inventory.spirit_cd.erase(c().id)
		s = submit({"type": "subdue_spirit", "slot": "weapon"})
		if s.get("awake", false): break
	check(s.get("ok", false) and s.get("awake", false), "the blade's spirit wakes where it slept (%.0f%%)" % (float(s.get("chance", 0.0)) * 100.0))
	if old_uid >= 0:
		for i in c().inventory.bag.size():
			var it = c().inventory.bag[i]
			if it is Dictionary and int(it.get("uid", -2)) == old_uid:
				submit({"type": "equip", "index": i})
				break
	check(finish("the_blade_spirit"), "The Blade That Sleeps No More done")

## S22 Mount role: the crane carries you (walk x1.5, no follower); the previous companion comes back after.
func ride_the_crane() -> void:
	var was_active: String = c().active_pet
	var crane := ""
	for p in c().pets:
		if str(p.species) == "jade_crane": crane = str(p.uid)
	check(crane != "", "the crane is yours")
	if crane == "": return
	var was_role: String = str(Game.pets._pet(c(), crane).get("role", "mount"))
	submit({"type": "set_active_pet", "pet": crane})
	check(submit({"type": "set_pet_role", "pet": crane, "role": "mount"}).get("ok", false), "ride the crane")
	check(absf(Game.pets.mount_speed(c()) - 1.5) < 0.001 and Game.pets.ally_uid == 0, "a mount carries you at 1.5x and does not follow on foot")
	check(absf(Game.pets.flight_qi_mult(c()) - 1.0) < 0.001, "a flying mount only eases flight from Cloud Stride 5")
	submit({"type": "set_pet_role", "pet": crane, "role": was_role if was_role != "mount" else "cultivation"})
	submit({"type": "set_active_pet", "pet": was_active})
