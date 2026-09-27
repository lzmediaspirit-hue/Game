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
	moments_data_suite()
	item_source_suite()
	room_suite()
	overlap_suite()
	movement_suite()
	auto_path_suite()
	quest_guidance_suite()
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

## P6 moments (docs/moments_design.md §3.8): every row of data/moments.json against the event contract (its trigger,
## merges and every payload key it reads), FxLayer's kinds, data/audio.json, the strings, UiKit's colours, the closed
## lists of MomentRules and the timing rules (a lock of at most max_lock_s, every screen layer inside the row).
func moments_data_suite() -> void:
	var contract: Dictionary = ContentDB.config("event_contract").get("events", {})
	var cfg: Dictionary = ContentDB.config("moments")
	var rows: Array = ContentDB.all("moments")
	check(rows.size() >= 11 and cfg.has("settings"), "moments.json has its rows and settings (%d rows)" % rows.size())
	var declared := func(ev: String) -> Array: return (contract.get(ev, {}).get("payload", []) as Array).map(func(k): return str(k).trim_suffix("?"))
	for r in rows:
		var where := "moment " + str(r.id)
		var keys: Array = declared.call(str(r.event))
		check(contract.has(str(r.event)) and not keys.is_empty(), "%s: its event %s is in the contract with a declared payload" % [where, r.event])
		var slots := {}
		for m in r.get("merge", []):
			check(contract.has(str(m.event)), "%s: merged event %s is in the contract" % [where, m.event])
			slots[str(m.get("into", ""))] = declared.call(str(m.event))
			for k in m.get("when", {}): check(k in MomentRules.MATCHERS or k in declared.call(str(m.event)), "%s: merge %s reads a declared key (%s)" % [where, m.event, k])
		for k in r.get("when", {}): check(k in MomentRules.MATCHERS or k in keys, "%s: matcher %s is known or a declared key" % [where, k])
		for h in r.get("hold_until", []): check(contract.has(str(h)), "%s: held until %s, an event in the contract" % [where, h])
		var refs := []
		_moment_walk(r, refs)
		for ref in refs:
			var s := str(ref)
			var part := s.split(".")
			if s.begins_with("payload."): check(s.trim_prefix("payload.") in keys, "%s reads %s, declared by %s" % [where, s, r.event])
			elif s.begins_with("slot.last."): check(part.size() == 4 and part[3] in declared.call(part[2]), "%s reads %s, declared by %s" % [where, s, part[2]])
			elif s.begins_with("slot.now.") or s.begins_with("slot.before."): check(part[2] in cfg.get("stats", []) or part[2] == "hp_pct", "%s reads %s, a snapshot number" % [where, s])
			elif s.begins_with("slot.rare."): check("items" in keys, "%s reads %s: its event carries items" % [where, s])
			elif s.begins_with("slot."): check(part.size() == 3 and part[2] in slots.get(part[1], []), "%s reads %s, from a merged event that declares it" % [where, s])
			elif s.begins_with("item."): check("item" in keys, "%s reads %s: its event names an item" % [where, s])
			elif s.begins_with("enemy."): check("enemy" in keys and s.trim_prefix("enemy.") in ["level", "elite", "def_id"], "%s reads %s: its event names an enemy" % [where, s])
		check(float(r.lock_s) <= float(cfg.settings.max_lock_s) and (float(r.lock_s) == 0.0 or float(r.lock_s) < float(r.duration_s)), "%s: its lock is within %s s and the row" % [where, cfg.settings.max_lock_s])
		check(float(r.get("skip_to_s", 0.0)) < float(r.duration_s) and str(r.skip) in ["", "tap"] and str(r.in_fight) in ["play", "toast"] and str(r.scope) in ["actor", "room"], "%s: skip, in_fight and scope are known, the skip point inside the row" % where)
		check(r.get("hold_until", []).is_empty() == (float(r.get("max_s", 0.0)) == 0.0), "%s: a held row has hold_until and max_s" % where)
		for v in r.get("variants", []):
			for k in v.get("when", {}): check(k in keys, "%s: a variant tests a declared key (%s)" % [where, k])
		for v in [r] + r.get("variants", []):
			var dur := float(v.get("duration_s", r.duration_s))
			for L in v.layers:
				var kind := str(L.kind)
				check(MomentRules.LAYER_KINDS.has(kind), "%s: layer kind %s is known" % [where, kind])
				if MomentRules.LAYER_KINDS.get(kind, "") in ["under", "over"]: check(float(L.t) < dur, "%s: its %s layer starts inside the row" % [where, kind])
				if kind == "fx": check(str(L.fx) in FxLayer.KINDS, "%s: fx %s is an FxLayer kind" % [where, L.fx])
				if kind == "sound": check(ContentDB.config("audio").get("sfx", {}).has(str(L.sfx)), "%s: sound %s is in data/audio.json" % [where, L.sfx])
				if kind == "bark":
					for i in 3: check(ContentDB.strings.has("%s_%d" % [L.key, i]), "%s: bark line %s_%d" % [where, L.key, i])
				if L.get("at") is String: check(str(L.at) in MomentRules.ANCHORS + ["band", "strip"], "%s: anchor %s is known" % [where, L.at])
				if L.has("to"): check(str(L.to) in MomentRules.ANCHORS, "%s: camera anchor %s is known" % [where, L.to])
				for art in ["band", "strip"]:
					if kind == art: check("ink_band" in r.get("art", []) and ContentDB.config("ui_assets_hd").has("ink_band"), "%s: its %s's ink band is listed and built" % [where, kind])
		for k in keys:
			check(r.sample.has(k), "%s: its sample carries %s" % [where, k])
	# The names moments write: a stage's great realm, a craft, a failure's cause, a stat's label.
	for rr in ContentDB.all("realms"): check(ContentDB.strings.has("realm_great." + str(rr.realm)), "realm_great.%s is a string" % rr.realm)
	var crafts := {}
	for rc in ContentDB.all("recipes"): crafts[str(rc.get("craft", ""))] = true
	for g in ContentDB.all("guilds"): crafts[str(g.craft)] = true
	for n in CraftingAuthority.NODE_CRAFT.values(): crafts[str(n)] = true
	crafts.erase("")
	for cr in crafts: check(ContentDB.strings.has("craft." + str(cr)), "craft.%s is a string" % cr)
	for f in ContentDB.all("failures"): check(ContentDB.strings.has("failure." + str(f.id)), "failure.%s is a string (finding 8)" % f.id)
	for st in cfg.get("stats", []): check(ContentDB.strings.has("moment.stat." + str(st)), "moment.stat.%s is a string" % st)
	for en in ContentDB.all("enemies"):
		for i in (en.get("phases", []) as Array).size(): check(ContentDB.strings.has("moment.numeral.%d" % (i + 1)), "%s's phase %d has a numeral" % [en.id, i + 1])
	# §3.8 rule 9: the rare finds exist; one main quest closes each chapter, 23 in all.
	for it in cfg.get("rare", {}).get("items", {}): check(item_ok(str(it)), "rare find %s is an item" % it)
	var ends: Dictionary = cfg.get("chapter_ends", {})
	var chapters := {}
	for q in ends:
		var qd := ContentDB.entry("quests", str(q))
		check(str(qd.get("kind", "")) == "main" and str(qd.get("chapter", "")) == str(ends[q]), "chapter end %s is a main quest of chapter %s" % [q, ends[q]])
		chapters[str(ends[q])] = true
	check(ends.size() == 23 and chapters.size() == 23, "one main quest closes each of the 23 chapters (%d)" % ends.size())
	for k in ["moment.story.chapter", "moment.story.prologue", "moment.rare.more"]: check(ContentDB.strings.has(k), "%s is a string" % k)
	for src in cfg.get("fountain", {}):
		var fo: Dictionary = cfg.fountain[src]
		check((fo.apex as Array).size() == 3 and (fo.flight as Array).size() == 3 and float(fo.gap) > 0.0 and (not fo.has("flash") or MomentRules.tokens().has(str(fo.flash))),
			"the %s fountain has its apex, flight, gap and a token flash" % src)
	for fam in cfg.get("dao_colours", {}): check(MomentRules.tokens().has(str(cfg.dao_colours[fam])), "the %s Daos' colour is a UiKit token" % fam)
	var elems: Dictionary = ContentDB.config("elements").get("colors", {})
	var grades: Dictionary = ContentDB.config("grades")
	var tokens := MomentRules.tokens()
	var colours := []
	_moment_walk(rows, [], colours)
	for c in colours:
		var s := str(c)
		var id := s.get_slice(":", 1)
		var ok := tokens.has(s)
		if s.contains(":"): ok = id.contains(".") or {"element": elems, "grade": grades.get("grade_colors", {}), "quality": grades.get("quality_colors", {})}.get(s.get_slice(":", 0), {}).has(id)
		check(ok, "moments colour %s is a UiKit token or a data id" % s)
	var texts := []
	_moment_walk(rows, [], [], texts)
	for t in texts:
		if not t.src.has("key"):
			var tb := str(t.src.get("name_of", t.src.get("field_of", "")))
			check(ContentDB.tables.has(tb), "moments text source reads %s, a table" % tb)
			continue
		var k := str(t.src.key) + (MomentRules.id_of(t.sample.get(str(t.src.suffix).trim_prefix("payload."), "")) if t.src.has("suffix") else "")
		check(ContentDB.strings.has(k), "moments text %s is a string (not the fallback)" % k)
	var tiers: Array = cfg.get("vfx_tiers", [])
	check(tiers.size() == 7, "the escalation curve has 7 tiers")
	for i in range(1, tiers.size()):
		for col in tiers[i]:
			check(float(tiers[i][col]) >= float(tiers[i - 1][col]), "vfx tier %d: %s does not fall" % [i + 1, col])
		check(int(tiers[i].spark_count) > int(tiers[i - 1].spark_count), "vfx tier %d: more sparks than tier %d" % [i + 1, i])
	for t in tiers:
		check(int(t.number_size) + 8 <= 40 and float(t.shake_s) <= 0.15 and float(t.tint_alpha) <= 0.2, "vfx tier %d stays within the limits" % int(t.tier))
	# §3.8 rule 10 and rule 3's second half: a tier per realm, rising 1 to 7; every technique's block at its unlock realm's
	# band (Common 1, Earth 2, Heaven 3 and up), a known shape drawn by FxLayer kinds, and a known spark style.
	var bands: Array = cfg.get("vfx_bands", [])
	check(bands.size() == ContentDB.all("realms").map(func(r): return int(r.realm_index)).max() + 1 and int(bands[0]) == 1 and int(bands[-1]) == 7,
		"vfx_bands names a tier for every realm, 1 to 7")
	for i in range(1, bands.size()): check(int(bands[i]) >= int(bands[i - 1]), "vfx band of realm %d does not fall" % i)
	var shapes: Dictionary = cfg.get("vfx_shapes", {})
	check(shapes.keys().all(func(s): return s in MomentRules.SHAPES) and MomentRules.SHAPES.all(func(s): return shapes.has(s)), "vfx_shapes lists every shape")
	for s in shapes:
		for kind in shapes[s]: check(str(kind) in FxLayer.KINDS, "shape %s draws %s, an FxLayer kind" % [s, kind])
	for st in cfg.get("particles", {}).get("families", {}).values() + cfg.get("particles", {}).get("elements", {}).values():
		check(str(st) in MomentRules.STYLES, "spark style %s is known" % st)
	for t in ContentDB.all("techniques"):
		var v: Dictionary = t.get("vfx", {})
		var tier := int(v.get("tier", 0))
		var want := int(bands[clampi(int(ContentDB.realm(str(t.unlock)).get("realm_index", 0)), 0, bands.size() - 1)]) if not bands.is_empty() else -1
		check(tier == want and {"common": tier == 1, "earth": tier == 2, "heaven": tier >= 3}.get(str(t.get("grade", "")), false),
			"technique %s: vfx tier %d is its unlock realm's band (%d, %s)" % [t.id, tier, want, t.get("grade", "")])
		check(str(v.get("shape", "")) in MomentRules.SHAPES and str(v.get("particles", "")) in MomentRules.STYLES, "technique %s: a known vfx shape and style" % t.id)

## Every reference ("payload.x", "slot.x.y", "item.x"), colour and string-key text source inside a moments node.
func _moment_walk(node, refs: Array, colours := [], texts := [], sample := {}) -> void:
	if node is Dictionary:
		if node.has("sample") and node.has("layers"): sample = node.sample
		if (node.has("key") or node.has("name_of") or node.has("field_of")) and not node.has("kind"): texts.append({"src": node, "sample": sample})
		for k in node:
			if k == "sample": continue
			var v = node[k]
			if k in ["color", "glow"]: colours.append(v)
			if v is String:
				var r: String = v.get_slice(":", 1) if v.contains(":") else v
				if r.begins_with("payload.") or r.begins_with("slot.") or r.begins_with("item.") or r.begins_with("enemy."): refs.append(r)
				if k == "if": refs.append("payload." + v)   # a line shown only when the payload says so
			_moment_walk(v, refs, colours, texts, sample)
	elif node is Array:
		for v in node: _moment_walk(v, refs, colours, texts, sample)

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
		if k == "record_debt": check(ContentDB.strings.has("ui.cultivation.debt_" + str(e.id)), "%s: debt %s has a label (B24)" % [where, e.id])
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
			for p in g.get("pick", []):
				check(item_ok(str(p.item)), "loot %s: %s" % [t.id, p.item])
				# A group rolls once and picks by weight: a chance on a picked row would be read by nothing (P7a).
				check(not p.has("chance"), "loot %s: the group row %s carries a weight, not a chance" % [t.id, p.item])
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
	# B24: Named Debts lists each debt by its label; the ones karma.json defines and the ones foes leave had none.
	var debt_ids: Array = (ContentDB.config("karma").get("debts", {}) as Dictionary).keys()
	for en in ContentDB.all("enemies"):
		for dk in ["spare_debt", "kill_debt"]:
			if str(en.get(dk, "")) != "": debt_ids.append(str(en[dk]))
	for did in debt_ids: check(ContentDB.strings.has("ui.cultivation.debt_" + str(did)), "debt %s has a label (B24)" % did)
	# B10: an origin has its name and a line for the creator (it showed its id, "Fishers Child", and no description).
	for og in ContentDB.all("origins"): check(str(og.get("name", "")) != "" and str(og.get("desc", "")) != "", "origin %s has a name and a description (B10)" % og.id)
	# B8: a shop's prices name their currency from the strings (the page spelled "taels" and "stones" in code).
	for sh in ContentDB.all("shops"): check(ContentDB.strings.has("ui.shop.price_" + str(sh.get("currency", "silver_tael"))), "shop %s currency has a price word (B8)" % sh.id)
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
		if it.has("use_action"): check(str(it.use_action) in ["appraise", "incubate", "tame", "absorb_flame", "talisman", "bath", "pet_item", "guqin", "swarm"], "item %s use_action" % it.id)
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

## P7a (M37): every item and piece of equipment has a source in the data, or carries an explicit mark,
## `"source": "<mark>"` (a string, or a list holding one): story, system or later (see tools/dev/wiki.py).
## The channels are the ones tools/dev/wiki.py lists as an item's sources; keep the two in step.
const SOURCE_MARKS := ["story", "system", "later"]
const TIDE_CORE_ELEMENTS := ["fire", "water", "wood", "earth", "wind", "thunder"]   # WorldAuthority.apply_tide_result
const TIDE_CORE_TIERS := ["low", "mid", "high"]
## Real gaps found by P7a: items nothing hands out, reported for P7b to source (a mark would say the gap is
## meant; these are bugs). An entry must go as soon as its item has a source, so the list only shrinks.
const KNOWN_SOURCE_GAPS := [
	# Beast cores of an element and rank band no beast has (and the Beast Tide does not give).
	"metal_core_low", "metal_core_mid", "metal_core_high", "star_core_low", "star_core_mid", "star_core_high",
	"space_core_low", "space_core_mid", "space_core_high", "soul_core_high", "wood_core_peak", "soul_core_peak",
	"spirit_stone_high", "beast_bag_mist", "beast_bag_star",
	"hour_incense_2", "hour_incense_4", "hour_incense_12", "hour_incense_24", "hour_incense_72", "wandering_incense",
	"iron_snare_kit", "silk_snare_kit", "star_snare_kit", "jade_rite_tablet", "cloud_rite_tablet", "star_rite_tablet",
	"cloud_gourd", "mistjade_gourd", "sunsteel_gourd",
	# Set pieces: the sect Mission Halls stock only the robes; the other sets have no source but a robe.
	"jade_current_hat", "jade_current_trousers", "jade_current_boots", "cloudpiercing_hat", "cloudpiercing_trousers", "cloudpiercing_boots",
	"mudwater_cleaver", "mudwater_robe", "drowned_hat", "drowned_boots", "crane_robe", "crane_trousers", "crane_boots",
]

func item_source_suite() -> void:
	var got := item_sources()
	var missing: Array = []
	for table in ["items", "artifacts"]:
		for it in ContentDB.all(table):
			var src = it.get("source", [])
			var marks: Array = src if src is Array else [src]
			var marked := false
			for m in marks: marked = marked or str(m) in SOURCE_MARKS
			if it.has("source") and src is String: check(str(src) in SOURCE_MARKS, "%s %s: unknown source mark '%s'" % [table, it.id, src])
			if got.has(str(it.id)) or marked: check(not str(it.id) in KNOWN_SOURCE_GAPS, "%s has a source now: drop it from KNOWN_SOURCE_GAPS" % it.id)
			elif not str(it.id) in KNOWN_SOURCE_GAPS: missing.append(str(it.id))
	for gap in KNOWN_SOURCE_GAPS: check(item_ok(str(gap)), "KNOWN_SOURCE_GAPS names an item that does not exist: %s" % gap)
	check(missing.is_empty(), "every item has a source or a source mark (none for %s)" % ", ".join(missing))
	print("data_validation: %d items still wait for a source (KNOWN_SOURCE_GAPS, see docs/wiki/items.md)" % KNOWN_SOURCE_GAPS.size())

func item_sources() -> Dictionary:
	var got := {}
	var rolled_by := {}   # loot table -> [[lo, hi] Level bands of whoever rolls it]
	var soil: Dictionary = ContentDB.config("garden").get("spirit_soil", {})
	# Drops: loot tables, first-defeat treasures, pet books, beast cores, Spirit Soil.
	for e in ContentDB.all("enemies"):
		var band := [int(e.get("level", [1])[0]), int(e.get("level", [1]).back())]
		for rid in ContentDB.rooms:
			for sp in ContentDB.room(rid).get("spawns", []):
				if str(sp.get("enemy", "")) == str(e.id):
					var lv0 = sp.get("level", 1)
					var slv: Array = lv0 if lv0 is Array else [lv0, lv0]
					band = [mini(band[0], int(slv[0])), maxi(band[1], int(slv.back()))]
		_rolled(rolled_by, str(e.get("loot", e.id)), band)
		for it in e.get("first_defeat", []) + e.get("elite_first_defeat", []): got[str(it)] = true
		if e.has("pet_book"): got[str(e.pet_book.item)] = true
		if str(e.get("race", "beast")) == "beast":
			for lv in range(band[0], band[1] + 1):
				var core := WorldAuthority.beast_core_for(e, lv)
				if core != "": got[core] = true
			if not soil.is_empty() and band[1] >= int(soil.get("min_level", 19)): got["spirit_soil"] = true
	# Containers: jars, crates, chests and wine jars; tower floors; calendar events.
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			if o.has("loot") and str(o.get("type", "")) in ["jar", "crate", "chest", "wine_jar"]:
				_rolled(rolled_by, str(o.loot), [int(o.get("level", 1)), int(o.get("level", 1))])
	for f in ContentDB.all("tower"): _rolled(rolled_by, str(f.loot), [int(f.level), int(f.level)])
	for ev in ContentDB.all("calendar"):
		if ev.has("loot"): _rolled(rolled_by, str(ev.loot), [])
	var grades := {}
	for tid in rolled_by:
		var t := ContentDB.entry("loot_tables", tid)
		for g in t.get("guaranteed", []) + t.get("rare", []) + t.get("quest_drops", []): got[str(g.item)] = true
		for grp in t.get("groups", []):
			for p in grp.get("pick", []): got[str(p.item)] = true
		if float(t.get("equipment", {}).get("chance", 0.0)) > 0.0:
			for band2 in rolled_by[tid]:
				if band2.is_empty(): continue
				for ilv in range(clampi(band2[0] - 2, 1, 81), clampi(band2[1] + 2, 1, 81) + 1): grades[LootRules.grade_for_ilv(ilv)] = true
	# The banded equipment roll (LootRules.make_equipment picks among these).
	for a in ContentDB.all("artifacts"):
		if a.has("set") or a.get("relic", false) or str(a.slot) in ["gourd", "cape", "talisman", "tool_furnace"] or a.has("pet_gear"): continue
		if grades.has(str(a.grade)): got[str(a.id)] = true
	# Gathering: room nodes, fishing, Beast King nests, treasure births, posts.
	for rid in ContentDB.rooms:
		for o in ContentDB.room(rid).get("objects", []):
			var ty := str(o.get("type", ""))
			if ty in ["herb_patch", "ore_vein", "star_sight", "pickup"] and o.has("item"): got[str(o.item)] = true
			if ty == "beast_trail" and o.has("critter"): got[str(o.critter)] = true
			if ty == "insect_swarm": _items_of(o.get("outputs", []), got)
			if o.get("chase") is Dictionary: _items_of(o.chase.get("rewards", []), got)
			if ty == "route_stone":
				for medal in o.get("route", {}).get("medal_rewards", {}).values(): _items_of(medal, got)
	for f2 in ContentDB.all("fish"): got[str(f2.item)] = true
	for k in ContentDB.all("beast_kings"):
		if k.get("nest", {}).has("item"): got[str(k.nest.item)] = true
	for ev2 in ContentDB.all("calendar"):
		if ev2.has("item"): got[str(ev2.item)] = true
		var rw = ev2.get("rewards", {})
		if rw is Dictionary:
			for place in rw:
				if rw[place] is Dictionary and rw[place].has("item"): got[str(rw[place].item)] = true
	var posts := ContentDB.config("posts")
	for n in posts.get("nodes", {}): got[str(n)] = true
	for sd in posts.get("rules", {}).get("side_drops", {}).values(): got[str(sd.item)] = true
	for outs in posts.get("swarms", {}).values():
		for x3 in outs: got[str(x3.item)] = true
	for tr in posts.get("trails", {}).values(): got[str(tr.critter)] = true
	for cp in posts.get("bench", {}).get("components", []): got[str(cp.item)] = true
	# Garden: beds grow each family's ages; a harvest returns seeds.
	var garden := ContentDB.config("garden")
	for fam in garden.get("families", {}):
		for age in garden.families[fam]: got[str(garden.families[fam][age])] = true
	for fam2 in garden.get("harvest_seeds", []):
		if garden.get("seeds", {}).has(fam2): got[str(garden.seeds[fam2])] = true
	# Crafting: recipes, salts, professions, curio appraisal, restoration, legendary chains, salvage.
	for r in ContentDB.all("recipes"):
		for o2 in r.get("outputs", []): got[str(o2.item)] = true
	for s in posts.get("salts", []): got[str(s.id)] = true
	for pr in ContentDB.all("professions"):
		for x4 in pr.get("results", []): got[str(x4.item)] = true
		for b in pr.get("blueprints", []):
			for y in b.get("yield", []): got[str(y.item)] = true
	for it2 in ContentDB.all("items"):
		for x5 in it2.get("appraise", []): got[str(x5.item)] = true
		if it2.has("restores"): got[str(it2.restores)] = true
	for ch in ContentDB.all("legendary_chains"): got[str(ch.weapon)] = true
	for sv in ContentDB.all("salvage"):
		for x6 in sv.get("returns", []): got[str(x6.item)] = true
	# Shops and auctions.
	for sh in ContentDB.all("shops"):
		for st in sh.get("stock", []) + sh.get("rotation", {}).get("pool", []): got[str(st.item)] = true
	var auction := ContentDB.config("auction")
	for lot in auction.get("pool", []) + auction.get("valley", {}).get("pool", []):
		if lot.has("item"): got[str(lot.item)] = true
	# Reward lists: expeditions, the Beast Tide, the beast arena and grove, sect tokens.
	for ex in ContentDB.all("expeditions"):
		_items_of(ex.get("rewards", []), got)
	var tide: Dictionary = ContentDB.config("expeditions").get("beast_tide", {}).get("rewards", {})
	for key in ["egg", "stag_egg"]:
		if tide.has(key): got[str(tide[key])] = true
	if int(tide.get("soil", 0)) > 0: got["spirit_soil"] = true
	if int(tide.get("cores", 0)) > 0:
		for el in TIDE_CORE_ELEMENTS:
			for tier in TIDE_CORE_TIERS: got["%s_core_%s" % [el, tier]] = true
	var arena := ContentDB.config("beast_arena")
	_items_of(arena.get("rewards", []) + arena.get("grove", {}).get("pool", []), got)
	if arena.get("grove", {}).has("first"): got[str(arena.grove.first)] = true
	for sect in ContentDB.all("sects"):
		if sect.has("token"): got[str(sect.token)] = true
	# Effects and mail attachments anywhere: every table, room and dialogue tree.
	for table in ContentDB.configs: _granted(ContentDB.configs[table], got)
	for rid2 in ContentDB.rooms: _granted(ContentDB.room(rid2), got)
	for tid2 in ContentDB.dialogue: _granted(ContentDB.dialogue[tid2], got)
	return got

func _items_of(list: Array, got: Dictionary) -> void:
	for x in list:
		if x is Dictionary and x.has("item"): got[str(x.item)] = true

func _rolled(rolled_by: Dictionary, table: String, band: Array) -> void:
	if not rolled_by.has(table): rolled_by[table] = []
	rolled_by[table].append(band)

func _granted(node, got: Dictionary) -> void:
	if node is Dictionary:
		var k := str(node.get("kind", ""))
		if k in ["grant_item", "grant_equipment"] and node.has("item"): got[str(node.item)] = true
		if k == "upgrade_sect_token":
			for sect in ContentDB.all("sects"):
				if sect.has("token"): got[str(sect.token).replace("_token", "_elder_token")] = true
		if node.get("attachments") is Array:
			for a in node.attachments:
				if a is Dictionary and a.has("item"): got[str(a.item)] = true
		for v in node.values(): _granted(v, got)
	elif node is Array:
		for v2 in node: _granted(v2, got)

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

## M18: no interactable hides another. Standing on an object (or at a door) and pressing the context button must reach it,
## so no other object on the same tier may claim the button there by WorldAuthority's own ranking (context_rank): an
## NPC on an NPC or on a shrine, a chest on a herb, any object whose reach covers a door. Two objects that are never
## shown together (one's visible_if is the other's hidden_if: Elder Gu and Madam Hua) do not meet.
func overlap_suite() -> void:
	var pairs := 0
	for rid in ContentDB.rooms:
		var room: Dictionary = ContentDB.room(rid)
		var heights := {}
		for s in room.get("surfaces", []): heights[str(s.id)] = float(s.get("height", 0))
		var objs: Array = room.get("objects", []).filter(func(o): return WorldAuthority.offers_context(o))
		for a in objs:
			var at_a := Vector2(float(a.at[0]), float(a.at[1]))
			var reach := float(a.get("radius", 110))
			for b in objs:
				if a == b or absf(float(a.get("alt", 0)) - float(b.get("alt", 0))) > WorldAuthority.REACH_ALT: continue
				if a.has("visible_if") and a.visible_if == b.get("hidden_if") or b.has("visible_if") and b.visible_if == a.get("hidden_if"): continue
				pairs += 1
				var d := at_a.distance_to(Vector2(float(b.at[0]), float(b.at[1])))
				check(d > reach or WorldAuthority.context_rank(a, true) * 1000.0 + d > WorldAuthority.context_rank(b) * 1000.0,
					"%s: %s hides %s (%d apart, reach %d)" % [rid, a.id, b.id, int(d), int(reach)])
			for p in room.get("portals", []):
				if not WorldAuthority.context_portal(p) or absf(float(a.get("alt", 0)) - float(heights.get(str(p.get("surface", "")), 0.0))) > WorldAuthority.REACH_ALT: continue
				pairs += 1
				var dp := at_a.distance_to(Vector2(float(p.at[0]), float(p.at[1])))
				check(dp > reach, "%s: %s hides the %s %s (%d apart, reach %d)" % [rid, a.id, str(p.get("type", "edge")), p.id, int(dp), int(reach)])
	check(pairs > 2000, "overlap_suite looked at %d pairs" % pairs)
# ------------------------------------------------------------------ S43 movement data
const VOLUME_KINDS := ["water_shallow", "water_deep", "current", "updraft", "wind", "bounce", "crumble", "rising_water", "hazard", "no_flight", "ice", "low_gravity"]

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
			if v.has("switch"):
				var sw := str(v.switch)
				check(room.get("objects", []).any(func(o): return str(o.id) == sw and str(o.type) == "gravity_switch"),
					"%s: volume %s names a gravity switch in the room" % [rid, v.id])
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

## M20 (P2): every guided and main quest leads the player on. A probe character is set at the point in the story where
## the quest is offered: at the realm it is offered at, with every quest it waits on done (its requirements, its
## unlock's trigger, the quest whose `next` it is, all the way back) and every prologue, main and guided quest the story
## offers and finishes at a lower realm, and with the flags, events, arts, sect, unlocks and items they gave. The game's
## own rules then answer, walking from home through the ways open at that point:
##   - the giver stands visible where the player can reach, a marker calls the player over and the giver offers it (an
##     auto-accepted quest needs no giver);
##   - under way, each objective that needs a place leads the direction mark to a real room that holds what it asks for
##     and that the player can reach (a story instance entered by an event is left out); once done, so does the hand-in.
func quest_guidance_suite() -> void:
	var story: Array = ContentDB.all("quests").filter(func(q): return str(q.kind) in ["prologue", "main", "guided"])
	var held := {}    # quest -> the conditions that hold when it is offered (its requirements, its unlock's trigger)
	var waits := {}   # quest -> the quests it waits on
	for q in story:
		held[str(q.id)] = _conds(q.get("requires", {}))
		for u in ContentDB.all("unlocks"):
			if str(u.get("quest", "")) == str(q.id): held[str(q.id)] += _conds(u.get("trigger", {}))
		waits[str(q.id)] = held[str(q.id)].filter(func(k): return str(k.kind) in ["quest_done", "quest_accepted"]).map(func(k): return str(k.quest))
	for q in story:
		if waits.has(str(q.get("next", ""))): waits[str(q.next)].append(str(q.id))
	var before := {}
	for q in story: before[str(q.id)] = _all_back(waits, str(q.id))
	var offered_at := {}    # quest -> the realm (its position) it is offered at; finished_at: and is finished at
	var finished_at := {}
	for q in story:
		var r := -1
		for d in [str(q.id)] + before[str(q.id)].keys():
			for k in held.get(d, []):
				if str(k.kind) in ["realm_at_least", "account_realm"]: r = maxi(r, ContentDB.realm_position(str(k.realm)))
		offered_at[str(q.id)] = r
		finished_at[str(q.id)] = r
		for o in q.objectives:
			if str(o.kind) == "reach_realm": finished_at[str(q.id)] = maxi(r, ContentDB.realm_position(str(o.realm)))
	var c := GameCharacter.new()
	c.id = "m20_probe"
	Game.characters[c.id] = c
	var quests := 0
	for q in story:
		var qid := str(q.id)
		if str(q.kind) == "prologue": continue
		quests += 1
		var done: Dictionary = before[qid].duplicate()
		for p in story:
			var pid := str(p.id)
			if pid != qid and not before[pid].has(qid) and offered_at[pid] < offered_at[qid] and finished_at[pid] <= offered_at[qid]:
				done[pid] = 1
				done.merge(before[pid])
		_story_point(c, q, done, held)
		if not q.get("auto_accept", false):
			var giver := QuestAuthority.own_npc(c, q.get("giver_any", q.giver))
			var at: Array = Game.quest.npc_rooms(c, giver)
			check(not at.is_empty() and _walks_to(c, str(at[0])), "%s: its giver %s stands where the player can reach when it is offered (%s)" % [qid, giver, at])
			check(QuestAuthority.marker_calls(Game.quest.npc_marker(c, giver)), "%s: a marker calls the player to %s (%s)" % [qid, giver, Game.quest.npc_marker(c, giver)])
			var offer: Array = Game.quest.talk(c, giver).get("dialogue", {}).get("choices", [])
			check(offer.any(func(ch): return str(ch.get("accept", "")) == qid), "%s: %s offers it" % [qid, giver])
		c.quests.offered = {}
		c.quests.active[qid] = {"state": "active", "progress": q.objectives.map(func(_o): return 0), "accepted_tick": 0}
		_gains(c, q.get("on_accept", []))
		for u in ContentDB.all("unlocks"):
			if str(u.get("quest", "")) == qid: c.cultivator.unlocked[str(u.id)] = true
		c.quests.tracked = [qid]
		for i in q.objectives.size():
			var o: Dictionary = q.objectives[i]
			var places: Array = Game.quest.objective_places(c, o)
			if not places.is_empty():
				# The objectives before this one done: the tracker's mark is this one's.
				c.quests.active[qid].progress = range(q.objectives.size()).map(func(j): return int(q.objectives[j].get("count", 1)) if j < i else 0)
				var room := str(Game.quest.tracker(c)[0].target_room)
				# A place a door or hidden way leads to is marked itself; the quest's own room stands in only for story instances.
				var doors: Array = places.filter(func(r): return not WorldRules.rooms_with("to=" + str(r)).is_empty() or not WorldRules.rooms_with("hidden_to=" + str(r)).is_empty())
				check(room != "" and (room in places or doors.is_empty() and room == str(q.get("target_room", ""))), "%s: '%s' has a direction mark (%s)" % [qid, o.text, room])
				check(room == "" or _walks_to(c, room), "%s: '%s' leads to %s, which the player can reach then" % [qid, o.text, room])
			_gains(c, [o])
		var hand_in := Game.quest.hand_in_npc(c, q)
		if hand_in != "":
			c.quests.active[qid].state = "ready"
			var back := str(Game.quest.tracker(c)[0].target_room)
			check(_stands_in(c, hand_in, back) and _walks_to(c, back), "%s: the mark leads to its hand-in %s where the player can reach (%s)" % [qid, hand_in, back])
	Game.characters.erase(c.id)
	check(quests >= 100, "quest_guidance_suite followed %d guided and main quests" % quests)

## Every quest `id` waits on, all the way back.
func _all_back(waits: Dictionary, id: String) -> Dictionary:
	var out := {}
	var todo: Array = waits.get(id, []).duplicate()
	while not todo.is_empty():
		var d: String = todo.pop_back()
		if out.has(d): continue
		out[d] = 1
		todo += waits.get(d, [])
	return out

## Every condition in a requirement, flattened.
func _conds(req) -> Array:
	var out: Array = []
	if req is Dictionary:
		for k in req.get("all", []) + req.get("any", []): out += _conds(k) if k.has("all") or k.has("any") else [k]
	return out

## The probe at the point where quest `q` is offered: what the quests `done` gave, and the conditions that held then.
func _story_point(c, q: Dictionary, done: Dictionary, held: Dictionary) -> void:
	c.quests.done = done.duplicate()
	c.quests.active = {}
	c.quests.flags = {}
	c.quests.offered = {str(q.id): true}
	c.cultivator.realm_key = "mortal"
	c.cultivator.events_passed = []
	c.cultivator.secret_arts = []
	c.cultivator.unlocked = {}
	c.training_sect = {}
	c.inventory.key_items = []
	c.cultivator.field_powers = {}
	c.position = {"room": "lf_village"}
	for d in done:
		var dq := ContentDB.entry("quests", d)
		_gains(c, held.get(d, []) + dq.get("on_accept", []) + dq.get("objectives", []) + dq.get("rewards", []))
	_gains(c, held.get(str(q.id), []))
	for u in ContentDB.all("unlocks"):
		if done.has(str(u.get("quest", ""))) or str(u.get("quest", "")) == "" and RequirementRules.passes(u.get("trigger", {}), Game.ctx(c)):
			c.cultivator.unlocked[str(u.id)] = true

## What conditions held, and effects and objectives met, leave on the probe: realm, flags, events (and what finishing
## them sets), arts, sect, items.
func _gains(c, list: Array) -> void:
	for e in list:
		match str(e.get("kind", "")):
			"realm_at_least", "account_realm", "reach_realm":
				if not ProgressionRules.at_least(c.cultivator.realm_key, str(e.realm)): c.cultivator.realm_key = str(e.realm)
			"unlock": c.cultivator.unlocked[str(e.system)] = true
			"presence_level_at_least":
				c.cultivator.field_powers["presence"] = {"xp": float(ContentDB.stat_const("presence.xp_levels", [0])[int(e.value) - 1])}
			"set_flag", "flag_set": c.quests.flags[str(e.flag)] = true
			"event_passed", "pass_event", "survive_timer":
				if str(e.event) in c.cultivator.events_passed: continue
				c.cultivator.events_passed.append(str(e.event))
				for run in WorldRules.event_runs(str(e.event)): _gains(c, run.event.get("on_complete", []))
			"learn_secret_art", "grant_art": c.cultivator.secret_arts.append(str(e.art))
			"join_sect", "has_training_sect": c.training_sect = {"id": "jade_sect"}
			"grant_item", "collect", "item_owned": c.inventory.key_items.append({"id": str(e.item), "count": int(e.get("count", 1))})

func _stands_in(c, npc: String, room: String) -> bool:
	return ContentDB.room(room).get("objects", []).any(func(o): return str(o.get("npc", "")) == npc and Game.world.object_visible(c, o))

## The probe can walk (and sail) from home to a room through the ways open to it, or to the room that hides a hidden
## way there once Spirit Sense can show it; a story instance with no way in is entered by its event instead.
func _walks_to(c, room: String) -> bool:
	var home := "lf_village"
	var open := func(r: String) -> bool: return r == home or not Game.world.route(c, home, r).is_empty()
	var hidden: Array = WorldRules.rooms_with("hidden_to=" + room)
	if open.call(room) or WorldRules.rooms_with("to=" + room).is_empty() and hidden.is_empty(): return true
	return Unlocks.is_unlocked(c.id, "hidden_portals") and hidden.any(func(h): return open.call(str(h)))
