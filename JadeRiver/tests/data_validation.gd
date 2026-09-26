extends Node
## Data validation and room-walk suites (Part 7 · Quality gates).
##   Data: every ID reference resolves, no duplicates, effect and requirement kinds
##         are known to their rules, appearances and dyes exist in parts.json.
##   Rooms: every portal links both ways, every room is reachable from Lotus Ferry,
##          spawns stand on their surfaces, no portal inside a spawn area.
## Run headless:  godot --headless --path . res://tests/data_validation.tscn

var checks := 0
var failures := 0
var effect_kinds := {}
var req_kinds := {}

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	_learn_kinds()
	data_suite()
	room_suite()
	movement_suite()
	auto_path_suite()
	print("data_validation: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## The rules themselves say which kinds they understand (kept in sync by reading the source).
func _learn_kinds() -> void:
	var re := RegEx.create_from_string('^\\t+"([a-z_]+)"(?:, "([a-z_]+)")*:')
	var src := FileAccess.get_file_as_string("res://scripts/simulation/authority/game_authority.gd")
	var in_effects := false
	for line in src.split("\n"):
		if line.begins_with("func apply_effects"): in_effects = true
		elif line.begins_with("func ") and in_effects: in_effects = false
		if not in_effects: continue
		var m := re.search(line)
		if m:
			for part in m.get_string(0).strip_edges().trim_suffix(":").split(","):
				effect_kinds[part.strip_edges().trim_prefix("\"").trim_suffix("\"")] = true
	for line in FileAccess.get_file_as_string("res://scripts/core/requirement_rules.gd").split("\n"):
		var m2 := re.search(line)
		if m2:
			for part in line.strip_edges().trim_suffix(":").split(","):
				req_kinds[part.strip_edges().trim_prefix("\"").trim_suffix("\"")] = true
	check(effect_kinds.size() > 30 and req_kinds.size() > 30, "rule kinds discovered (%d effects, %d requirements)" % [effect_kinds.size(), req_kinds.size()])

func item_ok(id: String) -> bool:
	return ContentDB.has_entry("items", id) or ContentDB.has_entry("artifacts", id)

func check_req(req, where: String) -> void:
	if not (req is Dictionary) or req.is_empty(): return
	for key in ["all", "any"]:
		for cond in req.get(key, []):
			if cond is Dictionary and (cond.has("all") or cond.has("any")):
				check_req(cond, where)
				continue
			var k := str(cond.get("kind", ""))
			check(req_kinds.has(k), "%s: unknown requirement kind '%s'" % [where, k])
			match k:
				"quest_done", "quest_active", "quest_accepted", "quest_not_done": check(ContentDB.has_entry("quests", str(cond.quest)), "%s: quest %s" % [where, cond.quest])
				"realm_at_least", "realm_below", "account_realm": check(ContentDB.realm_index.has(str(cond.realm)), "%s: realm %s" % [where, cond.realm])
				"item_owned": check(item_ok(str(cond.item)), "%s: item %s" % [where, cond.item])
				"unlock": check(ContentDB.has_entry("unlocks", str(cond.system)), "%s: unlock %s" % [where, cond.system])
				"companion_owned": check(ContentDB.has_entry("companions", str(cond.companion)), "%s: companion %s" % [where, cond.companion])
				"in_room": check(ContentDB.rooms.has(str(cond.room)), "%s: room %s" % [where, cond.room])
				"body_level_at_least", "soul_at_least", "purity_at_least", "level_at_least", "slots_unlocked_at_least":
					check(cond.has("value"), "%s: %s needs a value" % [where, k])

func check_effects(list, where: String) -> void:
	if not (list is Array): return
	for e in list:
		if not (e is Dictionary): continue
		var k := str(e.get("kind", ""))
		check(effect_kinds.has(k), "%s: unknown effect kind '%s'" % [where, k])
		if e.has("item"): check(item_ok(str(e.item)), "%s: effect item %s" % [where, e.item])
		if k == "learn_technique": check(ContentDB.has_entry("techniques", str(e.technique)), "%s: technique %s" % [where, e.technique])
		if k == "learn_method": check(ContentDB.has_entry("methods", str(e.method)), "%s: method %s" % [where, e.method])
		if k == "learn_recipe": check(ContentDB.has_entry("recipes", str(e.recipe)), "%s: recipe %s" % [where, e.recipe])
		if k in ["start_quest", "offer_quest"]: check(ContentDB.has_entry("quests", str(e.quest)), "%s: quest %s" % [where, e.quest])
		if k == "add_companion": check(ContentDB.has_entry("companions", str(e.companion)), "%s: companion %s" % [where, e.companion])
		if k in ["grant_pet", "choose_starter"]: check(ContentDB.has_entry("pets", str(e.species)), "%s: pet %s" % [where, e.species])
		if k == "teleport" and not str(e.get("target", "")) in ["last_town", "dungeon_exit", ""]: check(ContentDB.rooms.has(str(e.target)), "%s: teleport room %s" % [where, e.target])
		if k == "deed": check(ContentDB.has_entry("karma", str(e.deed)), "%s: deed %s" % [where, e.deed])
		if k == "learn_technique_for_weapon":
			for fam in e.get("options", {}): check(ContentDB.has_entry("techniques", str(e.options[fam])), "%s: technique %s" % [where, e.options[fam]])

# ------------------------------------------------------------------ data
func data_suite() -> void:
	check(ContentDB.load_errors.is_empty(), "content loads without errors %s" % str(ContentDB.load_errors))
	var npcs := {}
	for n in ContentDB.all("npcs"): npcs[str(n.id)] = n
	# Quests
	for q in ContentDB.all("quests"):
		var where := "quest " + str(q.id)
		for key in ["giver", "hand_in"]:
			var who := str(q.get(key, ""))
			if who != "": check(npcs.has(who), "%s: %s npc %s" % [where, key, who])
		for key2 in ["giver_any", "hand_in_any"]:
			for who2 in q.get(key2, []): check(npcs.has(str(who2)), "%s: %s npc %s" % [where, key2, who2])
		check_req(q.get("requires", {}), where)
		check_effects(q.get("rewards", []), where + " rewards")
		check_effects(q.get("on_accept", []), where + " on_accept")
		check(not q.get("objectives", []).is_empty(), where + " has objectives")
		for o in q.get("objectives", []):
			if o.has("item"): check(item_ok(str(o.item)), "%s: objective item %s" % [where, o.item])
			if o.has("enemy") and str(o.enemy) != "any": check(ContentDB.has_entry("enemies", str(o.enemy)), "%s: enemy %s" % [where, o.enemy])
			if o.has("room"): check(ContentDB.rooms.has(str(o.room)), "%s: room %s" % [where, o.room])
			if o.has("npc"): check(npcs.has(str(o.npc)), "%s: npc %s" % [where, o.npc])
			if o.has("recipe") and str(o.recipe) != "any": check(ContentDB.has_entry("recipes", str(o.recipe)), "%s: recipe %s" % [where, o.recipe])
			if o.has("technique") and str(o.technique) != "any": check(ContentDB.has_entry("techniques", str(o.technique)), "%s: technique %s" % [where, o.technique])
			if str(o.kind) == "use_system": check(_system_reported(str(o.system)), "%s: nothing reports system '%s'" % [where, o.system])
	# Unlocks: one per-character guided quest per realm stage (same_stage_ok marks the intended pairs).
	var per_stage := {}
	for u in ContentDB.all("unlocks"):
		var where2 := "unlock " + str(u.id)
		check_req(u.get("trigger", {}), where2)
		check_effects(u.get("effects", []), where2)
		if str(u.get("quest", "")) != "": check(ContentDB.has_entry("quests", str(u.quest)), "%s: quest %s" % [where2, u.quest])
		if str(u.get("scope", "character")) == "character" and not u.get("same_stage_ok", false):
			for cond in u.get("trigger", {}).get("all", []):
				if str(cond.get("kind", "")) == "realm_at_least":
					var key3 := str(cond.realm) + "|" + str(u.get("quest", ""))
					per_stage[str(cond.realm)] = per_stage.get(str(cond.realm), {})
					per_stage[str(cond.realm)][str(u.get("quest", ""))] = true
	for stage in per_stage:
		check((per_stage[stage] as Dictionary).size() <= 1, "one guided lesson per stage at %s: %s" % [stage, str(per_stage[stage].keys())])
	# Loot, shops, recipes
	for t in ContentDB.all("loot_tables"):
		for g in t.get("groups", []):
			for p in g.get("pick", []): check(item_ok(str(p.item)), "loot %s: %s" % [t.id, p.item])
		for key4 in ["guaranteed", "rare", "quest_drops"]:
			for r in t.get(key4, []): check(item_ok(str(r.item)), "loot %s: %s" % [t.id, r.item])
		for qd in t.get("quest_drops", []): check(ContentDB.has_entry("quests", str(qd.quest)), "loot %s: quest %s" % [t.id, qd.quest])
		# P1: every loot table rolls equipment, or says why it does not (a spar opponent, a fixed story reward).
		check(float(t.get("equipment", {}).get("chance", 0.0)) > 0.0 or str(t.get("no_equipment", "")) in ["spar", "set_reward"],
			"loot %s rolls equipment or gives a reason" % t.id)
	for e in ContentDB.all("enemies"):
		check(ContentDB.has_entry("loot_tables", str(e.get("loot", e.id))), "enemy %s has a loot table" % e.id)
		check(not e.get("attacks", []).is_empty() or e.get("passive", false), "enemy %s can attack" % e.id)
		if str(e.get("role", "")) in ["story_boss", "dungeon_boss", "field_boss"]:
			check(not (e.get("phases", []) as Array).is_empty(), "boss %s has phases" % e.id)
	for sh in ContentDB.all("shops"):
		var seen := {}
		for st in sh.get("stock", []) + sh.get("rotation", {}).get("pool", []):
			check(item_ok(str(st.item)), "shop %s: %s" % [sh.id, st.item])
			var key5 := str(st.item) + "|" + str(st.get("learn", ""))
			check(not seen.has(key5), "shop %s lists %s once" % [sh.id, st.item])
			seen[key5] = true
			check_req(st.get("requires", {}), "shop %s:%s" % [sh.id, st.item])
			var learn := str(st.get("learn", ""))
			if learn != "": check(ContentDB.has_entry("techniques", learn) or ContentDB.has_entry("methods", learn) or ContentDB.has_entry("recipes", learn)
				or ContentDB.has_entry("inner_arts", learn), "shop %s teaches %s" % [sh.id, learn])
	for r2 in ContentDB.all("recipes"):
		for io in r2.get("inputs", []) + r2.get("outputs", []): check(item_ok(str(io.item)), "recipe %s: %s" % [r2.id, io.item])
		# S44: no authored recipe blows the furnace; an alchemy recipe has an element and one role per slot.
		if str(r2.get("craft", "")) == "alchemy":
			check(Game.crafting.conflict_in(r2.get("inputs", [])).is_empty(), "recipe %s has no conflicting herbs" % r2.id)
			check(str(r2.get("element", "")) != "" and (r2.get("roles", []) as Array).size() == (r2.get("inputs", []) as Array).size(), "recipe %s element and roles" % r2.id)
	for hc in ContentDB.all("herb_conflicts"):
		for h in hc.get("herbs", []): check(item_ok(str(h)), "herb conflict %s: %s" % [hc.id, h])
	# S45 herbs: every herb has a family and an age the garden table maps back; seeds name a family; four seasons.
	var garden := ContentDB.config("garden")
	for it in ContentDB.all("items"):
		if str(it.get("type", "")) == "herb":
			var hb: Dictionary = it.get("herb", {})
			check(str(garden.get("families", {}).get(str(hb.get("family", "")), {}).get(str(int(hb.get("age", 0))), "")) == str(it.id),
				"herb %s: family and age map back to it" % it.id)
		if str(it.get("type", "")) == "seed":
			check(garden.get("families", {}).has(str(it.get("seed", {}).get("family", ""))), "seed %s names a herb family" % it.id)
	for fam in garden.get("seeds", {}): check(item_ok(str(garden.seeds[fam])), "garden seed for %s" % fam)
	check(ContentDB.all("seasons").size() == 4, "four seasons")
	var rare_nodes := 0
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) != "herb_patch" or not o.has("ripen"): continue
			rare_nodes += 1
			var rp: Dictionary = o.ripen
			check(garden.get("phases", {}).has(str(rp.get("phase", ""))) and int(rp.get("every_days", 0)) >= 1, "rare herb %s.%s ripens at a known phase" % [rid, o.id])
			check(float(o.get("alt", 0)) > 0.0, "rare herb %s.%s sits on a raised tier" % [rid, o.id])
			check(HerbRules.item_age(str(o.item)) == int(o.get("age", 0)) and int(o.age) >= 100, "rare herb %s.%s is 100 years or older" % [rid, o.id])
			if o.has("guardian"): check(ContentDB.has_entry("enemies", str(o.guardian.get("enemy", ""))), "rare herb %s.%s guardian" % [rid, o.id])
			if o.has("season"): check(ContentDB.has_entry("seasons", str(o.season)), "rare herb %s.%s season" % [rid, o.id])
	check(rare_nodes >= 9, "the Part 8 rare herb nodes are placed (%d)" % rare_nodes)
	var bed_count := 0
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) != "garden_bed": continue
			bed_count += 1
			check(str(o.get("field_grade", "")) in garden.get("field_grades", []), "garden bed %s.%s has a field grade" % [rid, o.id])
	check(bed_count >= 10, "garden beds in both sects and the cave abodes (%d)" % bed_count)
	for fam in garden.get("families", {}): check(garden.get("grow_hours", {}).has(fam) and garden.get("props", {}).has(fam), "garden grows %s" % fam)
	# S46: every tameable beast tames into a species with art; every beast of rank 2+ has a core to drop.
	var creatures := ContentDB.config("creature_art")
	for pe in ContentDB.all("pets"): check(creatures.has(str(pe.get("art", pe.id))), "pet %s has creature art" % pe.id)
	for en in ContentDB.all("enemies"):
		if en.get("tameable", false):
			var sp := str(en.get("tame_species", en.id)).trim_suffix("_chick") if not ContentDB.has_entry("pets", str(en.get("tame_species", en.id))) else str(en.get("tame_species", en.id))
			check(ContentDB.has_entry("pets", sp), "tameable %s becomes a pet species (%s)" % [en.id, sp])
		if int(en.get("beast_rank", 0)) >= 2:
			check(WorldAuthority.beast_core_for(en, int(en.level[0])) != "", "beast %s (rank %d) has a core" % [en.id, int(en.beast_rank)])
	for rar in ContentDB.config("pet_growth").get("rarities", []): check(ContentDB.config("pet_growth").get("purity", {}).has(str(rar.id)), "purity band for %s" % rar.id)
	# S47 Artifact Spirit depth: every relic spirit has a control demand, a skill, a favourite, a real resting place,
	# every kind of bark and an awakening quest; every imitation copies 60% of a relic's gift.
	var awaken_q := {}
	for q in ContentDB.all("quests"):
		for f in JSON.stringify(q.get("requires", {})).split("bound:").slice(1): awaken_q[f.get_slice("\"", 0)] = str(q.id)
	for it in ContentDB.all("items"):
		if it.get("relic", false) and it.has("spirit"):
			var sp: Dictionary = it.spirit
			check(float(sp.get("control", 0)) > 0.0 and int(sp.get("skill", {}).get("every_hits", 0)) > 0 and ContentDB.has_entry("items", str(sp.get("favourite", ""))),
				"relic %s: control demand, skill and favourite" % it.id)
			check(not ContentDB.room(str(sp.get("wake_room", ""))).is_empty(), "relic %s wakes in a real room" % it.id)
			for kind in ["awake", "kill", "gift", "devour", "low_hp", "refuse"]:
				check(not (sp.get("barks", {}).get(kind, []) as Array).is_empty(), "relic %s speaks on %s" % [it.id, kind])
			check(awaken_q.has(str(it.id)), "relic %s has an awakening quest" % it.id)
		if it.has("imitation"):
			var of := ContentDB.item(str(it.imitation.of))
			check(of.get("relic", false) and absf(float(it.imitation.effect.value) - float(of.get("spirit", {}).get("effect", {}).get("value", 0)) * 0.6) < 0.0001
				and str(it.imitation.effect.stat) == str(of.spirit.effect.stat) and ContentDB.has_entry("recipes", str(it.id)), "imitation %s copies 60%% of %s" % [it.id, it.imitation.of])
	# S47 legendary chains and weapon awakening: every chain's weapon, pieces, sources, recipe and quest are real; every
	# awakenable family has a skill.
	var drops_of := {}
	for t in ContentDB.all("loot_tables"):
		for qd in t.get("quest_drops", []): drops_of[str(qd.item)] = str(t.id)
	for ch in ContentDB.all("legendary_chains"):
		var wd := ContentDB.item(str(ch.weapon))
		check(wd.has("legend") and str(wd.get("family", "")) == str(ch.family) and StatRules.grade_index(str(wd.get("grade", ""))) >= StatRules.grade_index("heaven"),
			"legend %s is a %s of Heaven grade or better" % [ch.weapon, ch.family])
		check(ContentDB.has_entry("recipes", str(ch.weapon)) and ContentDB.has_entry("quests", str(ch.quest)), "legend %s has a recipe and a quest" % ch.id)
		check((ch.pieces as Array).size() == 3 and str(ch.pieces[0].zone) == "jade_river_valley", "legend %s: three pieces, the first in the valley" % ch.id)
		for pc in ch.pieces:
			check(ContentDB.item(str(pc.item)).get("quest_item", false) and drops_of.get(str(pc.item), "") == str(pc.source), "piece %s drops from %s" % [pc.item, pc.source])
		check(not (ch.get("later", []) as Array).is_empty(), "legend %s lists its later steps" % ch.id)
	for fam in ContentDB.all("weapon_families"):
		if str(fam.id) != "fists": check(fam.has("awakened") and int(fam.awakened.get("every_hits", 0)) > 0, "family %s can awaken" % fam.id)
	# S46 bloodline: every species has an ancestral skill and a form; contracts, capacity and incubation read real items.
	var pg := ContentDB.config("pet_growth")
	for pe in ContentDB.all("pets"):
		if pe.get("construct", false):
			check(not pe.has("bloodline_skill") and not pe.has("form_change") and (pe.favourite_foods as Array).is_empty(), "construct %s has no blood, form or food" % pe.id)
			continue
		check(str(pe.get("bloodline_skill", {}).get("name", "")) != "" and float(pe.get("bloodline_skill", {}).get("mult", 0)) > 1.0, "pet %s has a bloodline skill" % pe.id)
		check(str(pe.get("form_change", {}).get("name", "")) != "" and Color.html_is_valid(str(pe.get("form_change", {}).get("tint", ""))), "pet %s has a form change" % pe.id)
	check(int(pg.get("awakening", {}).get("skill_at", 0)) == 50 and int(pg.get("awakening", {}).get("form_at", 0)) == 90, "awakenings at purity 50 and 90")
	var caps: Array = pg.get("command", []).map(func(x): return int(x.count))
	check(caps == [1, 2, 3], "command capacity 1, 2, 3 (%s)" % str(caps))
	for step in pg.get("command", []):
		check(str(step.realm) == "" or not ContentDB.realm(str(step.realm)).is_empty(), "command step realm %s" % step.realm)
	for key in [str(pg.get("contracts", {}).get("blood", {}).get("item", "")), str(pg.get("incubation", {}).get("reroll_item", ""))]:
		check(str(ContentDB.item(key).get("use_action", "")) == "pet_item", "S46 item %s exists and goes to a pet" % key)
	check(ContentDB.has_entry("recipes", "beast_marrow_washing_pill") and float(ContentDB.item("beast_marrow_washing_pill").get("pill", {}).get("toxicity", 1)) == 0.0,
		"the Beast Marrow Washing Pill is refined, and leaves no toxicity")
	# S46 skill books: every book has its item, and all but the Trial Grove's have a place to be found.
	var book_sources := {}
	for sh in ContentDB.all("shops"):
		for st in (sh.get("stock", []) as Array) + (sh.get("rotation", {}).get("pool", []) as Array): book_sources[str(st.get("item", ""))] = true
	for en in ContentDB.all("enemies"):
		if en.has("pet_book"): book_sources[str(en.pet_book.item)] = true
	for lt in ContentDB.all("loot_tables"):
		for gi in lt.get("guaranteed", []): book_sources[str(gi.item)] = true
	for bk in ContentDB.all("pet_skill_books"):
		var bitem := "pet_book_" + str(bk.id)
		check(str(ContentDB.item(bitem).get("pet_book", "")) == str(bk.id), "skill book %s has its item" % bk.id)
		if str(bk.id) != "guardian_spirit": check(book_sources.has(bitem), "skill book %s can be found (%s)" % [bk.id, bk.get("source", "")])
	var ledge := false
	for o in ContentDB.room("cf_falls_pool").get("objects", []):
		if str(o.get("loot", "")) == "falls_pool_chest": ledge = true
	check(ledge, "the Falls Pool ledge chest keeps Herb Whisper")
	for gid in ["bone_collar", "scale_talisman", "reed_saddle"]:
		check(ContentDB.item(gid).has("pet_gear") and ContentDB.has_entry("recipes", gid) and str(ContentDB.item(gid).slot).begins_with("pet_"), "pet gear %s is forged and worn by an animal" % gid)
	var cgs: Array = pg.get("core_grades", [])
	for i in range(1, cgs.size()): check(float(cgs[i].min) > float(cgs[i - 1].min) and float(cgs[i].bonus) > float(cgs[i - 1].bonus), "core grade %s ranks above %s" % [cgs[i].id, cgs[i - 1].id])
	check(ContentDB.entry("pets", "ember_fox").has("bloodline_skill") and pg.get("fusion", {}).has("trait_chance"), "fusion odds in data")
	# S46 Beast Kings, nests, the Beast Tide, bags and mount-only species.
	for kg in ContentDB.all("beast_kings"):
		var ke := ContentDB.entry("enemies", str(kg.id))
		check(str(ke.get("role", "")) == "field_boss" and int(ke.get("beast_rank", 0)) > 0, "Beast King %s is a field-boss beast" % kg.id)
		var has_nest := false
		for o in ContentDB.room(str(kg.room)).get("objects", []):
			if str(o.get("type", "")) == "egg_nest" and str(o.get("king", "")) == str(kg.id): has_nest = true
		check(has_nest and ContentDB.item(str(kg.nest.item)).get("use_action", "") == "incubate", "Beast King %s has a nest in %s" % [kg.id, kg.room])
	var tide: Dictionary = ContentDB.config("expeditions").get("beast_tide", {})
	check((tide.get("waves", []) as Array).size() == 3 and not ContentDB.room(str(tide.get("room", ""))).is_empty(), "the Beast Tide: three waves at a real room")
	for w in tide.get("waves", []): check(int(ContentDB.entry("enemies", str(w.enemy)).get("beast_rank", 0)) > 0 and int(w.level_min) >= 10 and int(w.level_max) <= 45, "tide wave %s: rank 2-5 beasts" % w.enemy)
	var gong := false
	for o in ContentDB.room(str(tide.get("room", ""))).get("objects", []):
		if str(o.get("type", "")) == "beast_tide_drum": gong = true
	check(gong and ContentDB.has_entry("items", str(tide.rewards.stag_egg)), "the tide's gong and its Cloud Stag egg")
	var slots_seen: Array = []
	for it in ContentDB.all("items"):
		if it.has("beast_bag"): slots_seen.append(int(it.beast_bag.slots))
		if it.has("egg_species"): check(ContentDB.has_entry("pets", str(it.egg_species)), "egg %s hatches a real species" % it.id)
	slots_seen.sort()
	check(slots_seen == [2, 3, 4, 5, 6], "Spirit Beast Bags carry 2 to 6 (%s)" % str(slots_seen))
	for pe in ContentDB.all("pets"):
		if pe.get("mount_only", false): check(pe.has("mount") and float(pe.mount.get("speed", 0)) >= 1.5, "mount-only %s carries you" % pe.id)
	check(float(ContentDB.entry("pets", "cloud_stag").mount.speed) == 1.6 and int(ContentDB.entry("pets", "cloud_stag").movement.jump) == 600
		and int(ContentDB.entry("pets", "riverstone_ox").movement.jump) == 530 and not ContentDB.entry("pets", "riverstone_ox").movement.climb, "the ox and the stag move as Part 8 says")
	var ox_spawn := false
	for sp in ContentDB.room("sq_quarry_rim").get("spawns", []):
		if str(sp.enemy) == "riverstone_ox": ox_spawn = true
	check(ox_spawn and ContentDB.entry("enemies", "riverstone_ox").get("tameable", false), "the Riverstone Ox grazes Quarry Rim, paw-marked")
	check(ContentDB.entry("fates", "fox_spirits_favour").get("available", true) and float(ContentDB.entry("fates", "fox_spirits_favour").get("next", {}).get("egg_purity", 0)) == 10.0,
		"Fox Spirit's Favour is in the deck: the next egg +10 purity")
	# S48 body ladder: each rung names a bath item, a Temper trial set piece with a drum, and stats that exist.
	var stat_ids := {}
	for sd in ContentDB.stat_const("stats", []): stat_ids[str(sd.id)] = true
	var drums := {}
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) == "rite_circle": drums[str(o.get("event", ""))] = true
	var last_need := 0
	for bt in ContentDB.all("body_tiers"):
		check(str(ContentDB.item(str(bt.bath)).get("use_action", "")) == "bath", "body tier %s bath %s is a bath" % [bt.id, bt.bath])
		check(ContentDB.has_entry("set_pieces", str(bt.trial)) and drums.has(str(bt.trial)), "body tier %s trial %s has a set piece and a drum" % [bt.id, bt.trial])
		check(int(bt.need) > last_need, "body tier %s needs more body than the rung below" % bt.id)
		last_need = int(bt.need)
		for m in bt.get("modifiers", []): check(stat_ids.has(str(m.stat)), "body tier %s stat %s" % [bt.id, m.stat])
		for rid2 in bt.get("teaches", []): check(ContentDB.has_entry("recipes", str(rid2)), "body tier %s teaches %s" % [bt.id, rid2])
	for ph in ContentDB.all("physiques"):
		check(str(ph.get("earned", "")) != "" and str(ph.get("gift_text", "")) != "" and str(ph.get("drawback_text", "")) != "", "physique %s says how it is earned, its gift and its drawback" % ph.id)
		for m in ph.get("modifiers", []): check(stat_ids.has(str(m.stat)), "physique %s stat %s" % [ph.id, m.stat])
	for m2 in ContentDB.all("methods"): check(str(m2.get("yin_yang", "")) in ["yin", "yang"], "method %s leans yin or yang" % m2.id)
	# S48 fates and tribulations.
	var offerable := 0
	for fc in ContentDB.all("fates"):
		check(str(fc.get("gift_text", "")) != "" and str(fc.get("cost_text", "")) != "" and float(fc.get("weight", 0)) > 0.0, "fate %s has gift, cost and weight" % fc.id)
		for m4 in fc.get("modifiers", []) + fc.get("realm_modifiers", []): check(stat_ids.has(str(m4.stat)), "fate %s stat %s" % [fc.id, m4.stat])
		check_effects(fc.get("effects", []), "fate " + str(fc.id))
		check_req(fc.get("requires", {}), "fate " + str(fc.id))
		if fc.get("available", true): offerable += 1
	check(offerable >= int(ContentDB.config("fates").get("offer", 3)), "enough fates to offer three distinct cards")
	# S48 Inner Arts, stances and combos.
	var shop_learns := {}
	for sh2 in ContentDB.all("shops"):
		for st2 in sh2.get("stock", []): shop_learns[str(st2.get("learn", ""))] = true
	for ia in ContentDB.all("inner_arts"):
		for m5 in ia.get("modifiers", []): check(stat_ids.has(str(m5.stat)), "inner art %s stat %s" % [ia.id, m5.stat])
		if ia.has("family"): check(ContentDB.has_entry("weapon_families", str(ia.family)), "inner art %s family %s" % [ia.id, ia.family])
		# A master's legacy (S49) is passed on, never sold; every other art is taught in a shop.
		if ia.has("legacy"): check(not shop_learns.has(str(ia.id)), "legacy art %s is not sold" % ia.id)
		else: check(shop_learns.has(str(ia.id)), "inner art %s is taught in a shop" % ia.id)
	var stance_fams := {}
	for sn in ContentDB.all("stances"):
		check(ContentDB.has_entry("weapon_families", str(sn.family)) and not stance_fams.has(str(sn.family)), "stance %s: one for family %s" % [sn.id, sn.family])
		stance_fams[str(sn.family)] = true
		for m6 in sn.get("modifiers", []): check(stat_ids.has(str(m6.stat)), "stance %s stat %s" % [sn.id, m6.stat])
	for cb in ContentDB.all("combos"):
		check(ContentDB.has_entry("techniques", str(cb.first)) and ContentDB.has_entry("techniques", str(cb.second)), "combo %s techniques" % cb.id)
		check(str(cb.get("effect", {}).get("kind", "")) in ["shockwave", "extra_target", "pull", "bleed", "stun", "root"], "combo %s effect" % cb.id)
	for tq in ContentDB.all("techniques"): check(str(tq.get("grade", "")) in ["common", "earth", "heaven"], "technique %s grade" % tq.id)
	# S49: alignment, karma and Fame may gate optional content, never a realm (Part 7 forbidden patterns).
	var rel_kinds := ["alignment_at_least", "alignment_at_most", "merit_at_least", "fame_at_least", "reputation_at_least"]
	for rr in ContentDB.all("realms"):
		for cond in rr.get("major_breakthrough", {}).get("requirements", {}).get("all", []):
			check(not str(cond.get("kind", "")) in rel_kinds, "realm %s: no %s on a breakthrough" % [rr.id, cond.get("kind", "")])
	for dd in ContentDB.all("karma"):
		check(str(dd.get("name", "")) != "", "deed %s has a name" % dd.id)
		if str(dd.get("event", "")) != "": check(not (dd.get("match", {}) as Dictionary).is_empty(), "event deed %s matches on something" % dd.id)
	for key in ["fame_tiers", "alignment_words"]:
		for w in ContentDB.config("karma").get(key, []):
			check(ContentDB.strings.has("ui.relations." + ("fame_" if key == "fame_tiers" else "align_") + str(w.id)), "%s %s has a label" % [key, w.id])
	check(ContentDB.has_entry("enemies", str(ContentDB.config("karma").get("young_master", {}).get("enemy", ""))), "the young master is an enemy")
	# S49 affinity: gifts are real items; heart rewards are valid effects; every companion can duel; legacies exist.
	for n in ContentDB.all("npcs"):
		for key in ["loved", "liked"]:
			for it in n.get("gifts", {}).get(key, []): check(item_ok(str(it)), "npc %s %s gift %s" % [n.id, key, it])
		for h in n.get("heart_rewards", {}):
			check(int(h) >= 1 and int(h) <= 5, "npc %s heart reward at %s" % [n.id, h])
			check_effects(n.heart_rewards[h], "npc %s heart %s" % [n.id, h])
		if n.has("affinity"): check(ContentDB.has_entry("npcs", str(n.affinity)), "npc %s affinity id %s" % [n.id, n.affinity])
	for cp in ContentDB.all("companions"):
		check(ContentDB.has_entry("enemies", "duel_" + str(cp.id)), "companion %s has a duel form" % cp.id)
		check(not ContentDB.entry("npcs", str(cp.id)).get("gifts", {}).is_empty(), "companion %s has favourite gifts" % cp.id)
	for kind in ["dao_companion", "sworn", "master"]: check(ContentDB.has_entry("bonds", kind), "bond %s" % kind)
	for m in ContentDB.entry("bonds", "master").get("legacy", {}):
		check(ContentDB.has_entry("inner_arts", str(ContentDB.entry("bonds", "master").legacy[m])), "legacy art of %s" % m)
	check(ContentDB.has_entry("titles", str(ContentDB.entry("bonds", "sworn").get("title", ""))), "the sworn title")
	# S44/S49 guilds: every rank names a real recipe (or a grade), a title and a flag; halls, masters, shops and gates exist.
	for g in ContentDB.all("guilds"):
		var gid := "guild " + str(g.id)
		check(ContentDB.room(str(g.get("hall", ""))).size() > 0 and ContentDB.has_entry("npcs", str(g.get("master", ""))), gid + " has a hall and a master")
		check(ContentDB.has_entry("shops", str(g.get("shop", ""))) and ContentDB.has_entry("unlocks", str(g.get("unlock", ""))), gid + " has a shop and a gate")
		for rk in g.get("ranks", []):
			var rid := gid + " rank " + str(rk.id)
			if rk.has("recipe"):
				check(str(ContentDB.entry("recipes", str(rk.recipe)).get("craft", "")) == str(g.craft), rid + ": its recipe is of the guild's craft")
			else:
				check(StatRules.grade_index(str(rk.get("grade", ""))) >= 0 and str(rk.get("grade", "")) != "", rid + ": a recipe or a grade")
			check(ContentDB.has_entry("titles", str(rk.get("title", ""))) and str(rk.get("flag", "")) != "", rid + ": a title and a flag")
			if rk.has("hall"): check(ContentDB.room(str(rk.hall)).size() > 0, rid + ": its hall exists")
			if rk.has("requires"): check_req(rk.requires, rid)
			check_effects(rk.get("rewards", []), rid)
	# S49 calendar: every event names real rooms and realms; every rift room has its tear.
	for ev in ContentDB.all("calendar"):
		check(str(ev.get("name", "")) != "" and str(ev.get("desc", "")) != "", "calendar %s has a name and a line" % ev.id)
		if str(ev.get("room", "")) != "": check(ContentDB.rooms.has(str(ev.room)), "calendar %s room %s" % [ev.id, ev.room])
		if str(ev.get("cap_below", "")) != "": check(ContentDB.realm_index.has(str(ev.cap_below)), "calendar %s cap %s" % [ev.id, ev.cap_below])
		for rr in ev.get("rooms", []):
			var has_tear := false
			for o in ContentDB.room(str(rr)).get("objects", []):
				if str(o.type) == "rift_tear": has_tear = true
			check(has_tear, "rift room %s has a tear" % rr)
	var last_bolts := 0
	for tb in ContentDB.all("tribulations"):
		check(ContentDB.realm_index.has(str(tb.from)) and bool(ContentDB.realm(str(ContentDB.realm(str(tb.from)).get("next", ""))).get("major", false)),
			"tribulation %s guards a major breakthrough" % tb.id)
		var all_bolts := int(tb.bolts) * int(tb.get("waves", 1))
		check(all_bolts > last_bolts, "tribulation %s brings more bolts than the one before" % tb.id)
		last_bolts = all_bolts
	for r4 in ContentDB.all("recipes"):
		if r4.has("fire"): check(str(r4.fire) in (ContentDB.config("grades").get("pill", {}).get("fires", {}) as Dictionary), "recipe %s fire %s" % [r4.id, r4.fire])
	for tl in ContentDB.all("titles"):
		for m3 in tl.get("modifiers", []): check(stat_ids.has(str(m3.stat)), "title %s stat %s" % [tl.id, m3.stat])
	# Items that start systems name a known action; manuals teach something real.
	for it in ContentDB.all("items"):
		check_effects(it.get("use", []), "item " + str(it.id))
		# Rate stats are bonuses read as (1 + value) from a zero base: a percentage of them adds nothing, so they are flat.
		for e in it.get("use", []):
			if str(e.get("kind", "")) == "add_modifier" and str(e.get("stat", "")) in ["accumulation_rate", "insight_rate"]:
				check(str(e.get("op", "flat")) == "flat", "item %s: %s is raised flat" % [it.id, e.stat])
		# S44: every herb has a nature and the roles it can fill.
		if str(it.get("type", "")) == "herb":
			check(str(it.get("nature", "")) in ["hot", "cold", "neutral"] and not (it.get("roles", []) as Array).is_empty(), "herb %s nature and roles" % it.id)
		if it.has("use_action"): check(str(it.use_action) in ["appraise", "incubate", "tame", "absorb_flame", "talisman", "bath", "pet_item", "guqin"], "item %s use_action" % it.id)
		# S47: a treasure item points at its entry in treasures.json, with a cooldown or charges and a QI cost.
		if it.has("treasure"):
			var t := ContentDB.entry("treasures", str(it.treasure))
			check(not t.is_empty() and (float(t.get("cooldown_s", 0)) > 0.0 or t.has("charges")) and t.has("qi"), "treasure %s is defined" % it.id)
	# Appearances and dyes (parts.json)
	var slot_cat := {"weapon": "weapon", "robe": "shirt", "trousers": "pants", "boots": "shoes", "hat": "hat", "cape": "cape"}
	var dyes: Array = ContentDB.parts.get("_dyes", {}).get("order", [])
	for a in ContentDB.all("artifacts"):
		var cat := str(slot_cat.get(str(a.slot), ""))
		if cat != "" and str(a.get("appearance", "none")) != "none":
			check(ContentDB.parts.get(cat, {}).has(str(a.appearance)), "artifact %s appearance %s/%s" % [a.id, cat, a.appearance])
		if a.has("dye"): check(str(a.dye) in dyes, "artifact %s dye %s" % [a.id, a.dye])
	for n2 in npcs.values():
		var o2: Dictionary = n2.get("outfit", {})
		for cat2 in ["hair", "shirt", "pants", "shoes", "hat", "cape", "weapon"]:
			var look := str(o2.get(cat2, "none"))
			if look != "none" and o2.has(cat2): check(ContentDB.parts.get(cat2, {}).has(look), "npc %s %s %s" % [n2.id, cat2, look])
		for dk in ["shirt_dye", "pants_dye"]:
			if o2.has(dk): check(str(o2[dk]) in dyes, "npc %s %s %s" % [n2.id, dk, o2[dk]])
	# Methods, techniques and professions
	for m in ContentDB.all("methods"):
		check(ContentDB.realm_index.has(str(m.get("ceiling", ""))), "method %s ceiling" % m.id)
		var taught := str(m.get("source", "")) in ["lu_boatman", "jade_sect", "cloud_sect"] or ContentDB.has_entry("items", "manual_" + str(m.id))
		for it2 in ContentDB.all("items"):
			for u2 in it2.get("use", []):
				if str(u2.get("kind", "")) == "learn_method" and str(u2.get("method", "")) == str(m.id): taught = true
		check(taught, "method %s can be learned somewhere" % m.id)
	for f in ContentDB.all("formations"):
		check(ContentDB.has_entry("unlocks", str(f.unlock)) and item_ok(str(f.fuel)), "formation %s unlock and fuel" % f.id)
	for pr in ContentDB.all("professions"):
		for r3 in pr.get("results", []): check(item_ok(str(r3.item)), "profession %s result %s" % [pr.id, r3.item])
		for b in pr.get("blueprints", []):
			for inp in b.get("inputs", []) + b.get("yield", []): check(item_ok(str(inp.item)), "puppet %s: %s" % [b.id, inp.item])
	# Every item and piece of equipment has a drawing (its own or the one its `icon` names).
	for table in ["items", "artifacts"]:
		for it in ContentDB.all(table):
			var path := SpriteCache.icon_path(str(it.id))
			check(path != "" and ResourceLoader.exists(path), "%s %s has an icon" % [table, it.id])
	for tech in ContentDB.all("techniques"):
		var tpath := SpriteCache.icon_path(str(tech.get("icon", tech.id)))
		check(tpath != "" and ResourceLoader.exists(tpath), "technique %s has an icon" % tech.id)
	# Dialogue trees
	for tid in ContentDB.dialogue:
		var tree: Dictionary = ContentDB.dialogue[tid]
		for en in tree.get("entries", []):
			check_req(en.get("requires", {}), "tree " + tid)
			check(tree.get("nodes", {}).has(str(en.node)), "tree %s entry node %s" % [tid, en.node])
		for nid in tree.get("nodes", {}):
			for ch in tree.nodes[nid].get("choices", []):
				check_effects(ch.get("effects", []), "tree %s:%s" % [tid, nid])
				if ch.has("next"): check(tree.nodes.has(str(ch.next)), "tree %s:%s next %s" % [tid, nid, ch.next])

## A `use_system` objective must be reported by an authority (never from UI code):
## some authority both emits system_used and names the system.
func _system_reported(system: String) -> bool:
	var dir := "res://scripts/simulation/authority/"
	for f in DirAccess.get_files_at(dir):
		if not f.ends_with(".gd"): continue
		var src := FileAccess.get_file_as_string(dir + f)
		if src.contains("system_used") and src.contains('"%s"' % system): return true
	for rid in ContentDB.rooms:
		if JSON.stringify(ContentDB.room(rid)).contains('"system":"%s"' % system): return true
	# S43 movement arts report as art_used from the solver.
	if FileAccess.get_file_as_string("res://scripts/simulation/movement_solver.gd").contains('"art":"%s"' % system): return true
	return false

# ------------------------------------------------------------------ rooms
func room_suite() -> void:
	var start := "lf_fishers_hut"
	var seen := {start: true}
	var queue := [start]
	while not queue.is_empty():
		var rid: String = queue.pop_front()
		var ways: Array = []
		for p in ContentDB.room(rid).get("portals", []): ways.append(str(p.get("to", "")))
		# A Starsea dock sails to the far end of its route (S18): the Skyport Wreck has no other way in.
		for o in ContentDB.room(rid).get("objects", []):
			if str(o.get("type", "")) == "starsea_dock": ways.append(str(ContentDB.entry("voyages", str(o.get("route", ""))).get("to", "")))
		for to in ways:
			if to != "" and ContentDB.rooms.has(to) and not seen.has(to):
				seen[to] = true
				queue.append(to)
	# Rooms entered by set pieces or events count as reachable through them.
	for sp in ContentDB.all("set_pieces"):
		if sp.has("room"): seen[str(sp.room)] = true
	for rid2 in ContentDB.rooms:
		var room: Dictionary = ContentDB.room(rid2)
		check(seen.has(rid2) or room.get("instanced", false), "room %s reachable from Lotus Ferry" % rid2)
		var surfaces: Array = room.get("surfaces", [])
		for p2 in room.get("portals", []):
			var to2 := str(p2.get("to", ""))
			if to2 == "": continue
			var planned := ["ae_landing"]   # the Azure Expanse arrives with the next zone (v1.1)
			check(ContentDB.rooms.has(to2) or to2 in planned, "%s:%s leads to a real room (%s)" % [rid2, p2.id, to2])
			if not ContentDB.rooms.has(to2): continue
			var back := str(p2.get("to_portal", ""))
			var found := back == ""
			for q in ContentDB.room(to2).get("portals", []):
				if str(q.id) == back: found = true
			check(found, "%s:%s arrives at %s:%s" % [rid2, p2.id, to2, back])
			var returns := false
			for q2 in ContentDB.room(to2).get("portals", []):
				if str(q2.get("to", "")) == rid2: returns = true
			# Boss-room and story exits are one-way doors back to the world.
			var one_way: bool = str(p2.id) == "exit" or room.get("instanced", false) or str(p2.get("type", "")) in ["teleport", "one_way"]
			check(returns or one_way or ContentDB.room(to2).get("instanced", false), "%s has a way back to %s" % [to2, rid2])
			for sp2 in room.get("spawns", []):
				for pt in sp2.get("points", []):
					var at: Array = p2.get("at", [0, 0])
					check(Vector2(float(pt[0]), float(pt[1])).distance_to(Vector2(float(at[0]), float(at[1]))) > 120.0,
						"%s: spawn %s at %s is clear of portal %s" % [rid2, sp2.enemy, str(pt), p2.id])
		for sp3 in room.get("spawns", []):
			check(ContentDB.has_entry("enemies", str(sp3.enemy)), "%s spawns a real enemy %s" % [rid2, sp3.enemy])
			for pt2 in sp3.get("points", []):
				var on := false
				for s in surfaces:
					var rr: Array = s.get("rect", [0, 0, 0, 0])
					if Rect2(float(rr[0]), float(rr[1]), float(rr[2]), float(rr[3])).grow(2).has_point(Vector2(float(pt2[0]), float(pt2[1]))): on = true
				check(on, "%s: spawn %s at %s stands on a surface" % [rid2, sp3.enemy, str(pt2)])
		for o in room.get("objects", []):
			if str(o.get("type", "")) == "npc": check(ContentDB.has_entry("npcs", str(o.npc)), "%s places a real npc %s" % [rid2, o.npc])
			if o.has("item"): check(item_ok(str(o.item)), "%s object %s item %s" % [rid2, o.id, o.item])
			if o.has("loot"): check(ContentDB.has_entry("loot_tables", str(o.loot)), "%s object %s loot %s" % [rid2, o.id, o.loot])
			check_req(o.get("requires", {}), "%s:%s" % [rid2, o.id])
		if room.has("event"): check_effects(room.event.get("on_complete", []) + room.event.get("on_timeout", []), "%s event" % rid2)

	# Every Starsea route starts at a dock in its own room and ends in a real room with a crossing to sail through.
	for v in ContentDB.all("voyages"):
		var docked := false
		for o in ContentDB.room(str(v.get("from", ""))).get("objects", []):
			if str(o.get("type", "")) == "starsea_dock" and str(o.get("route", "")) == str(v.id): docked = true
		check(docked, "voyage %s leaves from a dock in %s" % [v.id, v.get("from", "")])
		if v.get("planned", false): continue
		check(ContentDB.rooms.has(str(v.get("to", ""))) and ContentDB.room(str(v.get("crossing", ""))).get("crossing", false)
			and ContentDB.has_entry("items", str(v.get("chart", ""))), "voyage %s: destination, crossing and chart exist" % v.id)
# ------------------------------------------------------------------ S43 movement data
const VOLUME_KINDS := ["water_shallow", "water_deep", "current", "updraft", "wind", "bounce", "crumble", "rising_water", "hazard", "no_flight", "ice"]

func movement_suite() -> void:
	# movement.json is the one table of traversal numbers: the solver's constants must match it.
	var pairs := {"jump.impulse": MovementSolver.JUMP_IMPULSE, "jump.gravity": MovementSolver.GRAVITY, "jump.coyote_s": MovementSolver.COYOTE_S,
		"jump.buffer_s": MovementSolver.BUFFER_S, "double_jump.impulse": MovementSolver.DOUBLE_JUMP_IMPULSE,
		"wall_step.kick_speed": MovementSolver.WALL_KICK_SPEED, "wall_step.kicks": MovementSolver.WALL_KICKS, "wall_step.reach": MovementSolver.WALL_REACH,
		"mantle.rise": MovementSolver.MANTLE_RISE, "mantle.reach": MovementSolver.MANTLE_REACH, "climb.speed": MovementSolver.CLIMB_SPEED,
		"glide.fall": MovementSolver.GLIDE_FALL, "glide.drift": MovementSolver.GLIDE_DRIFT, "air_dash.hold_s": MovementSolver.AIR_DASH_HOLD,
		"plunge.speed": MovementSolver.PLUNGE_SPEED, "water.shallow_factor": MovementSolver.SHALLOW_FACTOR, "water.swim_factor": MovementSolver.SWIM_FACTOR,
		"water.sink_factor": MovementSolver.SINK_FACTOR, "water.sink_s": MovementSolver.SINK_S, "water.sink_depth": MovementSolver.SINK_DEPTH,
		"water.swim_s": MovementSolver.SWIM_S, "water.skim_min_speed": MovementSolver.SKIM_MIN_SPEED, "water.skim_still_s": MovementSolver.SKIM_STILL_S,
		"updraft.speed": MovementSolver.UPDRAFT_SPEED, "updraft.ease": MovementSolver.UPDRAFT_EASE, "bounce.speed": MovementSolver.BOUNCE_SPEED,
		"wind.edge": MovementSolver.WIND_EDGE}
	for path in pairs:
		check(absf(float(ContentDB.movement(path, -999.0)) - float(pairs[path])) < 0.0001, "movement.json %s matches the solver (%s)" % [path, str(pairs[path])])
	# Every movement art: a secret art with a how-to line, taught by a quest that learns it on acceptance.
	for a in ContentDB.movement("arts", []):
		if not a.has("secret_art"): continue
		var sa := ContentDB.entry("secret_arts", str(a.secret_art))
		check(not sa.is_empty() and str(sa.get("movement_art", "")) == str(a.art) and str(sa.get("how_to", "")) != "", "movement art %s is a secret art with a how-to" % a.art)
		if str(a.art) == "dodge": continue
		var q := ContentDB.entry("quests", str(sa.get("quest", "")))
		var learns := false
		for e in q.get("on_accept", []):
			if str(e.get("kind", "")) == "learn_secret_art" and str(e.get("art", "")) == str(a.secret_art): learns = true
		check(learns, "%s is taught when its quest (%s) is accepted" % [a.secret_art, str(sa.get("quest", ""))])
	# Rooms: volumes, movers and climbables point at real things, and nothing waits inside deep water.
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.rooms[rid]
		var ids := {}
		for sf in room.get("surfaces", []): ids[str(sf.id)] = true
		for b in room.get("blocks", []): ids[str(b.id)] = true
		for v in room.get("volumes", []):
			check(str(v.kind) in VOLUME_KINDS, "%s: volume kind %s" % [rid, v.kind])
			if str(v.kind) == "crumble": check(ids.has(str(v.get("surface", ""))), "%s: crumble %s names a surface" % [rid, v.id])
			if str(v.kind) != "water_deep": continue
			var r: Array = v.rect
			var area := Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))
			var top := float(v.get("alt", [-100, 10])[1])
			for o in room.get("objects", []):
				var at: Array = o.get("at", [0, 0])
				check(not area.has_point(Vector2(float(at[0]), float(at[1]))) or float(o.get("alt", 0.0)) >= top, "%s: %s is not under deep water" % [rid, o.id])
			for p in room.get("portals", []):
				var pa: Array = p.get("at", [0, 0])
				check(not area.has_point(Vector2(float(pa[0]), float(pa[1]))), "%s: portal %s is not in deep water" % [rid, p.id])
			for sp in room.get("spawns", []):
				for pt in sp.get("points", []):
					check(not area.has_point(Vector2(float(pt[0]), float(pt[1]))), "%s: %s spawns clear of deep water" % [rid, sp.enemy])
			var spawn: Array = room.get("spawn_point", [0, 0])
			check(not area.has_point(Vector2(float(spawn[0]), float(spawn[1]))), "%s: the spawn point is dry" % rid)
		for m in room.get("movers", []):
			var swings := str(m.get("mode", "")) in ["swing", "circle"]
			check(ids.has(str(m.surface)) and str(m.get("mode", "pingpong")) in ["loop", "pingpong", "trigger", "swing", "circle"]
				and (swings and float(m.get("period_s", 0)) > 0.0 or not m.get("path", []).is_empty()),
				"%s: mover %s moves a real surface along a path (or swings round)" % [rid, m.surface])
		for cb in room.get("climbables", []):
			check(str(cb.get("kind", "")) in ["ladder", "rope", "vine", "chain"] and (str(cb.get("top", "")) == "" or ids.has(str(cb.top))), "%s: climbable %s" % [rid, cb.id])

## S49 test: auto-path reaches every quest target using only known arts. From the quest giver's room (or the zone's
## first room), a route of portals and Starsea voyages reaches the target without any movement art the character
## has not been taught by then (the one art-gated way, Breath Control's grotto, is closed to it). Story instances
## entered by an event, not a door, are left out.
func auto_path_suite() -> void:
	var no_arts := func(_room_id: String, p: Dictionary) -> bool:
		var r: Dictionary = p.get("requires", {})
		for cond in r.get("all", []) + r.get("any", []):
			if cond is Dictionary and str(cond.get("kind", "")) == "secret_art": return false
		return true
	var checked := 0
	for q in ContentDB.all("quests"):
		var target := str(q.get("target_room", ""))
		if target == "" or ContentDB.room(target).get("instanced", false): continue
		var from := WorldRules.npc_room(str(q.get("giver", "")))
		if from == "": from = str(ContentDB.zone(str(ContentDB.room(target).get("zone", ""))).get("start_room", ""))
		if from == target: continue
		checked += 1
		check(not WorldRules.route(from, target, no_arts).is_empty(), "auto-path: %s reaches %s from %s without new arts" % [q.id, target, from])
	check(checked >= 60, "auto-path covered %d quest targets" % checked)
