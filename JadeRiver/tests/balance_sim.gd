extends Node
## Balance simulator (S38, Part 7): a rate-based bot plays the data to the end of Act I
## and reports hours to each realm. Each Level it spends an active minute as
## data/balance.json says (fighting at the right Level, meditating at the best spot it
## has reached, the rest travelling and crafting), hands in the quests that open at that
## Level and one daily mission per hour. Realm progress uses the real rules: kill QP and
## gap factors, the meditation rate of a real character with that realm's method,
## body-stage training, quest percentages. It fails when a realm lands more than ±15%
## off the Part 4 pacing table.
## Run headless:  godot --headless --path . res://tests/balance_sim.tscn

var checks := 0
var failures := 0

func check(ok: bool, what: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		print("FAIL: ", what)

func _ready() -> void:
	call_deferred("_main")

func _main() -> void:
	var cfg := ContentDB.config("balance")
	check(not cfg.is_empty(), "balance.json is present")
	var c = _character()
	check(c != null, "a character to simulate")
	if c == null: return _finish()
	var quest_levels := _quest_levels()
	var hours := {}              # realm key -> hours when it is reached
	var t := float(cfg.get("prologue_hours", 0.5)) * 60.0   # active minutes
	var end_key := str(cfg.get("act_end", "heaven_glimpse_3"))
	var sim_end := str(cfg.get("sim_end", end_key))
	var key := "bone_forging_1"
	while key != "":
		hours[key] = t / 60.0
		var r := ContentDB.realm(key)
		var lv := int(r.get("level", 0))
		var need := float(r.get("accumulate_needed", 100))
		var income := _income(c, cfg, key, lv)
		# Quests that open inside this stage pay a share of its need on hand-in.
		# Optional side quests are detours: they also cost active time the mixed session does not cover.
		var lump := 0.0
		var detour := 0.0
		for n in int(r.get("levels", 1)):
			for kind in quest_levels.get(lv + n, {}):
				lump += float(ContentDB.curve("quest_qp_pct.%s" % kind, 0.0)) * int(quest_levels[lv + n][kind])
				detour += float(cfg.get("quest_minutes", {}).get(kind, 0.0)) * int(quest_levels[lv + n][kind])
		var base_min := need / income
		# Daily missions: a share of the need per hour of play.
		var daily := float(ContentDB.curve("quest_qp_pct.daily", 0.05)) * float(cfg.get("dailies_per_hour", 1.0)) * base_min / 60.0
		var minutes := base_min * maxf(0.2, 1.0 - lump - daily)
		t += minutes + detour
		if key == end_key: hours["act_end"] = t / 60.0
		if key == sim_end: break
		key = str(r.get("next", ""))
	var tol := float(cfg.get("tolerance", 0.15))
	print("realm                  sim h   target h   ratio")
	var targets: Array = cfg.get("pacing", []).duplicate()
	targets.append(["act_end", float(cfg.get("act_end_hours", 65))])
	for row in targets:
		var k := str(row[0])
		var want := float(row[1])
		var got := float(hours.get(k, -1.0))
		var ratio := got / want if want > 0.0 else 0.0
		print("%-22s %6.1f   %8.1f   %5.2f" % [k, got, want, ratio])
		if k == "bone_forging_1": continue   # set by the Prologue, not by rates
		check(got > 0.0 and absf(ratio - 1.0) <= tol, "%s reached at %.1f h (target %.1f h ±%d%%)" % [k, got, want, int(tol * 100.0)])
	_currency(cfg)
	_posts()
	_account_month()
	_finish()

## S39: a player can afford the next upgrade in their grade band after about 1–2 hours.
func _currency(cfg: Dictionary) -> void:
	for row in cfg.get("upgrades", []):
		var lv := int(row[0])
		var item := str(row[1])
		var rate := _taels_per_hour(cfg, lv)
		var price := LootRules.buy_price(item)
		var h := price / maxf(1.0, rate)
		print("Level %d: %d taels/h (spec about %d) · %s costs %d → %.1f h" % [lv, int(rate), int(row[2]), item, price, h])
		check(h >= float(cfg.get("afford_hours", [0.75, 2.5])[0]) and h <= float(cfg.get("afford_hours", [0.75, 2.5])[1]),
			"%s is affordable after %.1f h of play at Level %d" % [item, h, lv])

## Coins and loot sold at NPC prices from the monsters of this Level, plus daily mission pay.
func _taels_per_hour(cfg: Dictionary, lv: int) -> float:
	var rng := RandomNumberGenerator.new()
	rng.seed = 12345 + lv
	var foes: Array = ContentDB.all("enemies").filter(func(e):
		var r: Array = e.get("level", [0, 0])
		return str(e.get("role", "")) == "normal" and not e.get("passive", false) and lv >= int(r[0]) - 2 and lv <= int(r[r.size() - 1]) + 2)
	if foes.is_empty(): return 0.0
	var per_kill := 0.0
	var rolls := 200
	for e in foes:
		for i in rolls:
			var drop := LootRules.roll(str(e.get("loot", e.id)), rng, lv, 0.0, 0.0, {"no_equipment": true})
			per_kill += int(drop.coins)
			for it in drop.items: per_kill += LootRules.sell_price(str(it.item)) * int(it.count)
	per_kill /= float(rolls * foes.size())
	var kills_h := float(cfg.get("kills_per_min", 6)) * 60.0 * float(cfg.get("mix", {}).get("fight", 0.35))
	var dailies := float(cfg.get("dailies_per_hour", 1.0)) * (10 + lv * 3)
	return per_kill * kills_h + dailies

## S50 Keeping Post (docs/idle_gathering_design.md §8): the calibration targets from the real formulas and node data.
func _posts() -> void:
	var nodes: Dictionary = ContentDB.config("posts").get("nodes", {})
	var chance := func(fin: float, item: String) -> float: return float(PostRules.yield_of(fin, float(nodes[item].toughness)).chance)
	var f0 := PostRules.finesse(6.0, 10.0, 1)
	var r0 := PostRules.rates(f0, [{"item": "copper_ore", "toughness": nodes.copper_ore.toughness, "exp": nodes.copper_ore.exp, "weight": 1.0}], 3.0, PostRules.diligence("craft"))
	check(float(r0.items.copper_ore) >= 70.0 and float(r0.items.copper_ore) <= 100.0, "a new delver's copper post: %.0f an hour (70-100)" % float(r0.items.copper_ore))
	var fv := PostRules.finesse(13.0, 70.0, 25)
	check(absf(chance.call(fv, "jadeiron") - 0.5) <= 0.1 and absf(chance.call(fv, "spirit_stone_shard") - 0.4) <= 0.1,
		"valley end: jadeiron %.0f%%, spirit stone shard %.0f%% (about 50 and 40)" % [100.0 * chance.call(fv, "jadeiron"), 100.0 * chance.call(fv, "spirit_stone_shard")])
	var fe := PostRules.finesse(24.0, 115.0, 42, 0.0, [8.0])
	check(chance.call(fe, "stormsteel_ore") >= 0.3, "the Expanse: stormsteel %.0f%% (at least 30)" % (100.0 * chance.call(fe, "stormsteel_ore")))
	var fl := PostRules.finesse(35.0, 150.0, 55, 0.0, [16.0])
	check(chance.call(fl, "driftglass") >= 0.3, "Act III: driftglass %.0f%% before the account web (at least 30)" % (100.0 * chance.call(fl, "driftglass")))
	var rv := PostRules.rates(fv, [{"item": "jadeiron", "toughness": nodes.jadeiron.toughness, "exp": 30.0, "weight": 1.0}], 4.0, PostRules.diligence("craft"))
	var satchel := PostRules.capacity(PostRules.compartment_cap(4)) / float(rv.items.jadeiron)
	check(satchel >= 10.0 and satchel <= 16.0, "a Satchel pouch holds %.1f h of a valley-end post (10-16)" % satchel)
	check(PostRules.capacity(PostRules.compartment_cap(0)) / float(r0.items.copper_ore) <= 1.0, "an unsewn pouch fills within the hour")

## V10d3 (docs/idle_gathering_design.md §6, §9): thirty days of twelve characters at their posts, 20 hours a day,
## the account web bought greedily from the Storehouse and a day's silver of active play: Post Arts (Dreaming
## Artisan, then Steady Hand), craft seals, Guardian Steles, the Favour of the Guilds, the Cinnabar line and two
## plain flags over half the posts. Reports Diligence, what the web multiplies Finesse by, levels and salts.
func _account_month() -> void:
	var cfg: Dictionary = ContentDB.config("posts")
	var nodes: Dictionary = cfg.get("nodes", {})
	var crafts := ["delving", "foraging", "angling", "netting"]
	var tools := {"delving": [13.0, 4.0], "foraging": [14.0, 4.0], "angling": [19.0, 4.0], "netting": [20.0, 5.0]}   # tier 3
	var attr := 60.0
	var ladders := {}
	for cr in crafts: ladders[cr] = []
	for id in nodes:
		var n: Dictionary = nodes[id]
		if ladders.has(str(n.get("craft", ""))) and not n.get("side", false): ladders[str(n.craft)].append(str(id))
	for cr in crafts: ladders[cr].sort_custom(func(a, b): return int(nodes[a].gate) < int(nodes[b].gate))
	var arts_def := {}
	for a in cfg.get("post_arts", []): arts_def[str(a.id)] = a
	var seal_of := {}
	for sd in cfg.get("seals", []):
		if str(sd.get("craft", "")) in crafts: seal_of[str(sd.craft)] = sd
	var chars: Array = []
	# Three characters to a craft, each a rung below the last: the account's goods span the ladder seals and steles climb.
	for i in 12: chars.append({"craft": crafts[i % 4], "rung": i / 4, "xp": 0.0, "arts": {"dreaming_artisan": 0, "steady_hand": 0}, "flag": i < 6})
	var store := {}
	var seals := {}
	var steles := {}
	var web := {"guilds": false, "flag": -1}   # a Dictionary: lambdas capture locals by value
	var taels := 0.0
	var line := {"rank": 1, "fire": 0, "refined": 0}
	var st: Dictionary = cfg.get("steles", {})
	var flag_plain: Dictionary = cfg.get("flags", {}).get("kinds", {}).get("plain", {})
	var dil_of := func(ch: Dictionary) -> float:
		var a: Dictionary = arts_def.dreaming_artisan
		var src := PostRules.curve("decay", float(a.x1), float(a.x2), float(ch.arts.dreaming_artisan)) + (3.0 if web.guilds else 0.0)
		if ch.flag and int(web.flag) >= 0: src += float(flag_plain.base) + float(flag_plain.per_level) * int(web.flag)
		return PostRules.diligence("craft", src)
	var fin_of := func(ch: Dictionary, web: bool) -> float:
		var lv := PostRules.level_for(float(ch.xp))
		var t: Array = tools[ch.craft]
		if not web: return PostRules.finesse(float(t[0]), attr, lv)
		var sh: Dictionary = arts_def.steady_hand
		var groups: Array = [PostRules.curve("decay", float(sh.x1), float(sh.x2), float(ch.arts.steady_hand))]
		var flat := 3.0 * mini(int(seals.get(ch.craft, 0)), lv)
		return PostRules.finesse(float(t[0]), attr, lv, flat, groups, float(steles.get(ch.craft, 0)) * float(st.get("power_per_level", 0.3)))
	var rows := {}
	for day in range(1, 31):
		taels += 15000.0
		for ch in chars:
			var lv := PostRules.level_for(float(ch.xp))
			var fin: float = fin_of.call(ch, true)
			var best := 0
			var lad: Array = ladders[ch.craft]
			for k in lad.size():
				if int(nodes[lad[k]].gate) <= lv and float(PostRules.yield_of(fin, float(nodes[lad[k]].toughness)).chance) >= 0.3: best = k
			var pick := str(lad[maxi(0, best - int(ch.rung))])
			var n: Dictionary = nodes[pick]
			var r := PostRules.rates(fin, [{"item": pick, "toughness": float(n.toughness), "exp": float(n.exp), "weight": 1.0}], float(tools[ch.craft][1]), dil_of.call(ch))
			store[pick] = float(store.get(pick, 0.0)) + float(r.items[pick]) * 20.0
			ch.xp = float(ch.xp) + float(r.exp_h) * 20.0
			# Post Arts: a point every two levels (the character knows four crafts), Dreaming Artisan to 40 first.
			var pts := PostRules.art_points(PostRules.level_for(float(ch.xp)) + 3) - int(ch.arts.dreaming_artisan) - int(ch.arts.steady_hand)
			while pts > 0:
				if int(ch.arts.dreaming_artisan) < 40: ch.arts.dreaming_artisan += 1
				else: ch.arts.steady_hand += 1
				pts -= 1
		# The Cinnabar line from day 3: 96 cycles a day as far as copper and moss last; refined each evening.
		if day >= 3:
			var rk := int(line.rank)
			var cyc := 96
			cyc = mini(cyc, int(float(store.get("copper_ore", 0.0)) / PostRules.calcination_cost(rk, 3)))
			cyc = mini(cyc, int(float(store.get("willow_moss", 0.0)) / PostRules.calcination_cost(rk, 2)))
			store["copper_ore"] = float(store.get("copper_ore", 0.0)) - cyc * PostRules.calcination_cost(rk, 3)
			store["willow_moss"] = float(store.get("willow_moss", 0.0)) - cyc * PostRules.calcination_cost(rk, 2)
			var salts := cyc * PostRules.calcination_fire(rk)
			store["cinnabar_salt"] = float(store.get("cinnabar_salt", 0.0)) + salts
			line.refined = int(line.refined) + salts
			while int(line.refined) >= PostRules.calcination_rank_need(int(line.rank)):
				line.refined = int(line.refined) - PostRules.calcination_rank_need(int(line.rank))
				line.rank = int(line.rank) + 1
		# Seals: as deep as the Storehouse pays (salts past 10), keeping half of each good.
		for cr in crafts:
			var sd: Dictionary = seal_of[cr]
			while int(seals.get(cr, 0)) < int(sd.max):
				var cost := PostRules.seal_cost(int(seals.get(cr, 0)), sd.ladder)
				if float(store.get(str(cost.item), 0.0)) < 2.0 * int(cost.count): break
				if cost.has("salt") and float(store.get(str(cost.salt), 0.0)) < int(cost.salt_count): break
				store[str(cost.item)] = float(store[str(cost.item)]) - int(cost.count)
				if cost.has("salt"): store[str(cost.salt)] = float(store[str(cost.salt)]) - int(cost.salt_count)
				seals[cr] = int(seals.get(cr, 0)) + 1
		# Steles with a third of the day's silver, cheapest first.
		var budget := 5000.0
		for k in 40:
			var best := ""
			for cr in crafts:
				if best == "" or int(steles.get(cr, 0)) < int(steles.get(best, 0)): best = cr
			var sc := PostRules.stele_cost(int(steles.get(best, 0)))
			if float(sc.taels) > budget or float(store.get(str(sc.item), 0.0)) < int(sc.count) or int(steles.get(best, 0)) >= int(st.get("max", 40)): break
			budget -= float(sc.taels)
			taels -= float(sc.taels)
			store[str(sc.item)] = float(store[str(sc.item)]) - int(sc.count)
			steles[best] = int(steles.get(best, 0)) + 1
		if not web.guilds and taels >= 6000.0 and float(store.get("jadeiron", 0.0)) >= 300.0 and float(store.get("reed_cicada", 0.0)) >= 200.0:
			web.guilds = true
			taels -= 6000.0
			store["jadeiron"] = float(store.jadeiron) - 300.0
			store["reed_cicada"] = float(store.reed_cicada) - 200.0
		if day >= 10:
			if int(web.flag) < 0: web.flag = 0
			var fc := PostRules.flag_cost(int(web.flag))
			while int(web.flag) < 20 and float(store.get(str(fc.salt), 0.0)) >= 2.0 * int(fc.salt_count):
				store[str(fc.salt)] = float(store[str(fc.salt)]) - 2.0 * int(fc.salt_count)
				web.flag = int(web.flag) + 1
				fc = PostRules.flag_cost(int(web.flag))
		if day in [1, 10, 20, 30]:
			var dsum := 0.0
			var mult := 0.0
			var lvs := 0
			for ch in chars:
				dsum += float(dil_of.call(ch))
				mult += (float(fin_of.call(ch, true)) - 12.0) / (float(fin_of.call(ch, false)) - 12.0)
				lvs += PostRules.level_for(float(ch.xp))
			rows[day] = {"dil": dsum / 12.0, "mult": mult / 12.0, "level": lvs / 12.0}
			print("  day %d: Craft Diligence %.0f%%, web Finesse x%.2f, craft level %.1f, seals %s, steles %s, line rank %d, flag %d, guilds %s" % [day,
				100.0 * dsum / 12.0, mult / 12.0, lvs / 12.0, str(seals.values()), str(steles.values()), int(line.rank), int(web.flag), str(web.guilds)])
	check(absf(PostRules.diligence("craft") - 0.52) < 0.001, "a new account's posts work at 52%")
	check(float(rows[30].dil) >= 0.6 and float(rows[30].dil) <= 0.8, "day 30: Craft Diligence %.0f%% (60-80 from arts, the Guilds and flags alone)" % (100.0 * float(rows[30].dil)))
	check(float(rows[10].mult) > 1.3 and float(rows[30].mult) >= float(rows[10].mult), "the web's Finesse keeps growing (x%.2f at day 10, x%.2f at day 30)" % [float(rows[10].mult), float(rows[30].mult)])
	check(float(rows[30].mult) >= 1.5 and float(rows[30].mult) <= 2.5, "day 30: the account web multiplies Finesse by %.2f (1.5-2.5 in the first month; 2-4 later)" % float(rows[30].mult))
	check(int(line.rank) >= 3, "a month of the Cinnabar line reaches rank %d (opening the Verdigris line)" % int(line.rank))

func _finish() -> void:
	print("balance_sim: %d checks, %d failures" % [checks, failures])
	get_tree().quit(1 if failures > 0 else 0)

## QP per active minute at this stage, from the real rules.
func _income(c, cfg: Dictionary, key: String, lv: int) -> float:
	var mix: Dictionary = cfg.get("mix", {})
	var major := str(ContentDB.realm(key).get("realm", key))
	c.cultivator.realm_key = key
	c.cultivator.method_id = str(cfg.get("method", {}).get(major, "riverbreath_fragment"))
	c.cultivator.stability = str(cfg.get("stability", "stable"))
	c.cultivator.consolidation_penalty = false
	var fight := float(cfg.get("kills_per_min", 6)) * ProgressionRules.kill_qp(lv, lv, "normal")
	var density := float(cfg.get("density", {}).get(major, 1.0))
	var sit := ProgressionRules.meditation_rate(c, density, 0.0)
	if ProgressionRules.is_body_stage(key): sit = maxf(sit, float(ContentDB.curve("training_qp_per_min", 40)))
	return float(mix.get("fight", 0.4)) * fight + float(mix.get("meditate", 0.3)) * sit

## Level -> {quest kind: count}: where each quest becomes available (its realm requirement,
## its chapter code such as "qk5", or the median of its numbered chapter).
func _quest_levels() -> Dictionary:
	var codes := {"bf": "bone_forging", "qk": "qi_kindling", "qu": "qi_unfurling", "ht": "heart_tempering", "cs": "cloud_stride",
		"sa": "spirit_awakening", "hg": "heaven_glimpse"}
	var placed := {}   # quest -> level
	var chapters := {} # numbered chapter -> [levels]
	for q in ContentDB.all("quests"):
		var lv := -1
		for r in q.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "realm_at_least": lv = maxi(lv, int(ContentDB.realm(str(r.realm)).get("level", 0)))
		var ch := str(q.get("chapter", ""))
		if lv < 0 and ch.length() >= 3 and codes.has(ch.left(2)) and ch.substr(2).is_valid_int():
			lv = int(ContentDB.realm("%s_%s" % [codes[ch.left(2)], ch.substr(2)]).get("level", -1))
		if lv >= 0: placed[str(q.id)] = lv
		if ch.is_valid_int() and lv >= 0: chapters[ch] = chapters.get(ch, []) + [lv]
	var out := {}
	var loose: Array = []   # side stories with no realm anchor: spread evenly over the Act
	for q in ContentDB.all("quests"):
		var kind := str(q.get("qp", q.get("kind", "side")))
		if kind == "prologue": continue
		var lv2 := int(placed.get(str(q.id), -1))
		var ch2 := str(q.get("chapter", ""))
		if lv2 < 0 and chapters.has(ch2):
			var ls: Array = chapters[ch2].duplicate()
			ls.sort()
			lv2 = int(ls[ls.size() / 2])
		if lv2 < 0:
			loose.append(kind)
			continue
		_add(out, lv2, kind)
	var last := int(ContentDB.realm(str(ContentDB.config("balance").get("act_end", "heaven_glimpse_3"))).get("level", 57))
	for i in loose.size():
		_add(out, 1 + int(float(i + 1) * (last - 1) / float(loose.size() + 1)), str(loose[i]))
	return out

func _add(out: Dictionary, lv: int, kind: String) -> void:
	if not out.has(lv): out[lv] = {}
	out[lv][kind] = int(out[lv].get(kind, 0)) + 1

func _character():
	var folder := "user://balance_sim/"
	DirAccess.make_dir_recursive_absolute(folder)
	for f in DirAccess.get_files_at(folder): DirAccess.remove_absolute(folder + f)
	Saves.use_folder(folder)
	Clock.override_utc = 1767225600.0   # a fixed "now" and seed: the same character every run
	Game.boot()
	Game.autosave_enabled = false
	Game.account.rng_seed = 2026
	Rng.restore("account", {}, 2026)
	Game.submit({"type": "create_character", "slot": 1, "name": "Balance", "appearance": {"hair": "topknot"}})
	Game.submit({"type": "enter_character", "slot": 1})
	return Game.active()
