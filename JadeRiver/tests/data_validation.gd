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
		if m: effect_kinds[m.get_string(1)] = true
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
	for e in ContentDB.all("enemies"):
		check(ContentDB.has_entry("loot_tables", str(e.get("loot", e.id))), "enemy %s has a loot table" % e.id)
		check(not e.get("attacks", []).is_empty() or e.get("passive", false), "enemy %s can attack" % e.id)
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
		check(shop_learns.has(str(ia.id)), "inner art %s is taught in a shop" % ia.id)
	var stance_fams := {}
	for sn in ContentDB.all("stances"):
		check(ContentDB.has_entry("weapon_families", str(sn.family)) and not stance_fams.has(str(sn.family)), "stance %s: one for family %s" % [sn.id, sn.family])
		stance_fams[str(sn.family)] = true
		for m6 in sn.get("modifiers", []): check(stat_ids.has(str(m6.stat)), "stance %s stat %s" % [sn.id, m6.stat])
	for cb in ContentDB.all("combos"):
		check(ContentDB.has_entry("techniques", str(cb.first)) and ContentDB.has_entry("techniques", str(cb.second)), "combo %s techniques" % cb.id)
		check(str(cb.get("effect", {}).get("kind", "")) in ["shockwave", "extra_target", "pull", "bleed", "stun", "root"], "combo %s effect" % cb.id)
	for tq in ContentDB.all("techniques"): check(str(tq.get("grade", "")) in ["common", "earth", "heaven"], "technique %s grade" % tq.id)
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
		if it.has("use_action"): check(str(it.use_action) in ["appraise", "incubate", "tame", "absorb_flame", "talisman", "bath"], "item %s use_action" % it.id)
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
const VOLUME_KINDS := ["water_shallow", "water_deep", "current", "updraft", "wind", "bounce", "crumble", "rising_water", "hazard", "no_flight"]

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
			check(ids.has(str(m.surface)) and str(m.get("mode", "pingpong")) in ["loop", "pingpong", "trigger"] and not m.get("path", []).is_empty(),
				"%s: mover %s moves a real surface along a path" % [rid, m.surface])
		for cb in room.get("climbables", []):
			check(str(cb.get("kind", "")) in ["ladder", "rope", "vine", "chain"] and (str(cb.get("top", "")) == "" or ids.has(str(cb.top))), "%s: climbable %s" % [rid, cb.id])
