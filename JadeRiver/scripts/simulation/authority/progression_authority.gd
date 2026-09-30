class_name ProgressionAuthority
extends Authority
## S05–S10 · Owns the Realm track, stability, injuries, toxicity, body, soul,
## purity, Daos, methods, meridians, techniques (knowledge and mastery) and
## seclusion. Breakthroughs start only from the `start_breakthrough` intent —
## never from an offline, idle or automatic path.
##
## The authority keeps the state, takes the intents and runs the cultivator's clock (tick); the work is done by its
## parts in authority/progression/, one for each section (audit 45, S10: ProgressionPart says how a part works). Its
## public methods forward to them.

const CHANNEL_S := 3.0
var channels: Dictionary = {}       # actor -> breakthrough in progress
var sec_accum: Dictionary = {}      # actor -> fractional second for per-second meditation ticks
var contemplate: Dictionary = {}    # actor -> dao id
var tribulations: Dictionary = {}   # actor -> heavenly tribulation under way (S48; not saved: leaving ends it)
var streaks: Dictionary = {}        # actor -> {n, t}: kills in a row (Blood Memory; Killing Intent grows from it)
var last_attune: Dictionary = {}    # actor -> "dealt|taken" last emitted, so rooms only re-emit on a change

var meditation: ProgressionMeditation
var realms: ProgressionRealms
var tribulation: ProgressionTribulation
var fates: ProgressionFates
var insight: ProgressionInsight
var attunement: ProgressionAttunement
var body: ProgressionBody
var condition: ProgressionCondition
var vows: ProgressionVows
var techniques: ProgressionTechniques
var trees: ProgressionTrees

func _init(g) -> void:
	super(g)
	meditation = ProgressionMeditation.new(self)
	realms = ProgressionRealms.new(self)
	tribulation = ProgressionTribulation.new(self)
	fates = ProgressionFates.new(self)
	insight = ProgressionInsight.new(self)
	attunement = ProgressionAttunement.new(self)
	body = ProgressionBody.new(self)
	condition = ProgressionCondition.new(self)
	vows = ProgressionVows.new(self)
	techniques = ProgressionTechniques.new(self)
	trees = ProgressionTrees.new(self)

func intents() -> Array:
	return ["start_meditation", "stop_meditation", "toggle_meditation", "start_breakthrough", "learn_method", "switch_method",
		"open_meridian", "reset_meridians", "equip_technique", "unequip_technique", "rank_up_technique", "set_contemplate",
		"enter_seclusion", "claim_offline", "use_treatment", "train_object", "attune_jade", "start_bath", "choose_fate", "equip_inner_art", "set_stance", "set_vow", "set_path", "set_false_realm",
		"play_guqin", "solve_chess", "realise_node", "unrealise_node", "reset_tree"]

func subscribe() -> void:
	GameEvents.subscribe("loadout_swapped", techniques.on_loadout_swapped, 30)
	# S44: a pill whose effect is on loan (the Qi Flow Pill) pays it back when the buff wears off.
	GameEvents.subscribe("buff_expired", func(p): condition.on_buff_expired(p), 30)
	# S44: a furnace blast leaves a minor body injury.
	GameEvents.subscribe("furnace_blast", func(p): apply_injury(str(p.get("actor", "")), "body", 1), 30)
	GameEvents.subscribe("hit_landed", meditation.on_hit_landed, 30)
	# S48 Ember Heart: every Fire pill refined counts.
	GameEvents.subscribe("craft_completed", body.on_fire_pill, 30)
	GameEvents.subscribe("actor_defeated", realms.on_actor_defeated, 30)
	GameEvents.subscribe("player_gravely_wounded", realms.on_gravely_wounded, 30)
	GameEvents.subscribe("technique_used", techniques.on_technique_used, 30)
	GameEvents.subscribe("object_hit", body.on_object_hit, 30)
	GameEvents.subscribe("zone_entered", attunement.on_zone_entered, 30)
	GameEvents.subscribe("room_entered", func(p): attunement.refresh_attunement(game.character(str(p.get("actor", "")))), 30)
	GameEvents.subscribe("stats_changed", func(p): if "attunement_bonus" in p.get("changed_ids", []): attunement.refresh_attunement(game.character(str(p.get("actor", "")))), 30)
	# P13a: a page of Lu's journal picked up may complete a piece of the Ferryman's Oar.
	GameEvents.subscribe("flag_set", trees.on_flag_set, 30)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"start_meditation": return start_meditation(c)
		"stop_meditation": return stop_meditation(c, str(intent.get("reason", "moved")))
		"toggle_meditation": return stop_meditation(c, "tapped") if c.cultivator.meditating else start_meditation(c)
		"play_guqin": return play_guqin(c, float(intent.get("score", 0.0)))
		"solve_chess": return solve_chess(c, str(intent.get("site", "")), str(intent.get("choice", "")))
		"start_breakthrough": return start_breakthrough(c, intent.get("support_items", []))
		"learn_method": return fail("taught_by_npc")
		"switch_method": return switch_method(c, str(intent.get("id", "")), bool(intent.get("use_conversion_pill", false)))
		"open_meridian": return open_meridian(c, str(intent.get("channel", "")))
		"reset_meridians": return reset_meridians(c)
		"equip_technique": return equip_technique(c, int(intent.get("slot", -1)), str(intent.get("id", "")))
		"unequip_technique": return equip_technique(c, int(intent.get("slot", -1)), "")
		"rank_up_technique": return rank_up_technique(c, str(intent.get("id", "")))
		"set_contemplate":
			if not Unlocks.is_unlocked(c.id, "insight_sites"): return fail("locked")
			contemplate[c.id] = str(intent.get("dao", ""))
			return ok()
		"enter_seclusion": return enter_seclusion(c, str(intent.get("focus", "accumulate")))
		"start_bath": return start_bath(c, str(intent.get("item", intent.get("recipe", ""))))
		"claim_offline": return claim_offline(c, float(intent.get("elapsed", 0.0)))
		"train_object": return fail("use_attack")
		"attune_jade": return attune_jade(c, str(intent.get("zone", "")), int(intent.get("index", -1)))
		"choose_fate": return choose_fate(c, str(intent.get("card", "")))
		"equip_inner_art": return equip_inner_art(c, int(intent.get("slot", -1)), str(intent.get("art", "")))
		"set_stance": return set_stance(c, str(intent.get("family", "")), str(intent.get("stance", "")))
		"set_vow": return set_vow(c, str(intent.get("vow", "")), bool(intent.get("on", true)))
		"set_path": return set_path(c, str(intent.get("path", "")), bool(intent.get("on", true)))
		"set_false_realm": return set_false_realm(c, str(intent.get("realm", "")))
		"realise_node": return realise_node(c, str(intent.get("node", "")))
		"unrealise_node": return unrealise_node(c, str(intent.get("node", "")))
		"reset_tree": return reset_tree(c, str(intent.get("tree", "")))
	return fail("unknown_intent")

func tick(delta: float) -> void:
	var c = game.active()
	if c == null: return
	var cu: CultivatorState = c.cultivator
	realms.tick_channel(c, delta)
	tribulation.tick_tribulation(c, delta)
	if cu.meditating:
		if cu.meditation_settle > 0.0:
			cu.meditation_settle -= delta
		else:
			sec_accum[c.id] = float(sec_accum.get(c.id, 0.0)) + delta
			while sec_accum[c.id] >= 1.0:
				sec_accum[c.id] -= 1.0
				meditation.meditation_second(c)
	if cu.consolidation_left > 0.0:
		cu.consolidation_left = maxf(0.0, cu.consolidation_left - delta)
		if cu.consolidation_left <= 0.0:
			cu.consolidation_penalty = false
			if cu.state == "consolidating": cu.state = "accumulating"
			emit("consolidation_finished", {"actor": c.id})
	if cu.breakthrough_cooldown > 0.0: cu.breakthrough_cooldown = maxf(0.0, cu.breakthrough_cooldown - delta)
	if cu.epiphany_cooldown > 0.0: cu.epiphany_cooldown = maxf(0.0, cu.epiphany_cooldown - delta)   # two hours of play (S48)
	condition.tick_injuries(c, delta, 3.0 if cu.meditating else 1.0)
	if cu.toxicity > 0.0:
		var drain := float(ContentDB.stat_const("toxicity.drain_per_min", 1)) / 60.0 * delta
		if cu.meditating: drain *= float(ContentDB.stat_const("toxicity.meditate_drain_mult", 2))
		cu.toxicity = maxf(0.0, cu.toxicity - drain)
	if cu.state == "bottleneck":
		cu.bottleneck_seconds += delta
		var hint_s := float(ContentDB.curve("bottleneck_hint_minutes", 20)) * 60.0
		if cu.bottleneck_seconds >= hint_s and not c.quests.has_flag("hint_" + cu.realm_key):
			game.quest.apply_flag(c.id, "hint_" + cu.realm_key)
			game.mail.apply_send(c.id, "mentor_hint", [], {"realm": ContentDB.name_of("realms", cu.realm_key)})

# ------------------------------------------------------------------ the facade
## Every public method, forwarded to the part that does the work. A forwarder named with a leading underscore keeps a
## private name that tests or tools call by (audit 45 S11 gives those public names).

# Meditation, seclusion and the offline claim (progression_meditation.gd)
func start_meditation(c) -> Dictionary: return meditation.start_meditation(c)
func stop_meditation(c, reason := "moved") -> Dictionary: return meditation.stop_meditation(c, reason)
func meditation_context(c) -> Dictionary: return meditation.meditation_context(c)
func accumulation_bonus(c) -> float: return meditation.accumulation_bonus(c)
func speed_breakdown(c) -> Dictionary: return meditation.speed_breakdown(c)
static func bonus_source_label(source: String) -> String: return ProgressionMeditation.bonus_source_label(source)
func enter_seclusion(c, focus: String) -> Dictionary: return meditation.enter_seclusion(c, focus)
func start_bath(c, item_id: String) -> Dictionary: return meditation.start_bath(c, item_id)
func seclusion_cap(room: Dictionary) -> float: return meditation.seclusion_cap(room)
func claim_offline(c, elapsed_s: float) -> Dictionary: return meditation.claim_offline(c, elapsed_s)
func play_guqin(c, score: float) -> Dictionary: return meditation.play_guqin(c, score)

# Realms and breakthroughs (progression_realms.gd)
func at_zone_ceiling(c) -> bool: return realms.at_zone_ceiling(c)
func apply_progress(actor_id: String, amount: float, source: String, pct_of_need := 0.0) -> void: realms.apply_progress(actor_id, amount, source, pct_of_need)
func cu_owner(cu: CultivatorState) -> String: return realms.cu_owner(cu)
func _levels_gained(c, from_level: int, to_level: int) -> void: realms.levels_gained(c, from_level, to_level)
func query_requirements(c) -> Array: return realms.query_requirements(c)
func query_breakthrough(c, support_items: Array = []) -> Dictionary: return realms.query_breakthrough(c, support_items)
func start_breakthrough(c, support_items: Array) -> Dictionary: return realms.start_breakthrough(c, support_items)
func _maybe_deviate(c, risk: String) -> void: realms.maybe_deviate(c, risk)
func is_channeling(actor_id: String) -> bool: return realms.is_channeling(actor_id)
func _advance(c, to: String, major: bool) -> void: realms.advance(c, to, major)
func _forge_core(c) -> void: realms.forge_core(c)
func core_forging_points(c) -> Array: return realms.core_forging_points(c)
func roll_aptitude(c) -> void: realms.roll_aptitude(c)
func apply_event_passed(actor_id: String, event: String) -> void: realms.apply_event_passed(actor_id, event)
func _on_gravely_wounded(p: Dictionary) -> void: realms.on_gravely_wounded(p)

# The heavenly tribulation (progression_tribulation.gd)
func _start_tribulation(c, ch: Dictionary) -> void: tribulation.start_tribulation(c, ch)
func _tick_tribulation(c, delta: float) -> void: tribulation.tick_tribulation(c, delta)
func is_under_tribulation(actor_id: String) -> bool: return tribulation.is_under_tribulation(actor_id)
func tribulation_view(actor_id: String) -> Dictionary: return tribulation.tribulation_view(actor_id)

# Breakthrough fates (progression_fates.gd)
func choose_fate(c, card: String) -> Dictionary: return fates.choose_fate(c, card)
func apply_grant_fate(actor_id: String, card: String) -> void: fates.apply_grant_fate(actor_id, card)
func spend_fate_next(c, key: String) -> float: return fates.spend_fate_next(c, key)
func _spend_fate_next(c, key: String) -> float: return fates.spend_fate_next(c, key)
func apply_pill_resistance_all(actor_id: String, amount: int) -> void: fates.apply_pill_resistance_all(actor_id, amount)
func apply_purity_grade(actor_id: String, grades: int) -> void: fates.apply_purity_grade(actor_id, grades)
func fate_flag(c, flag: String) -> bool: return fates.fate_flag(c, flag)

# Insight and the Daos (progression_insight.gd)
func apply_insight(actor_id: String, dao: String, amount: float, context: String) -> void: insight.apply_insight(actor_id, dao, amount, context)
func apply_open_dao(actor_id: String, dao: String) -> void: insight.apply_open_dao(actor_id, dao)
func _roll_epiphany(c, context: String) -> void: insight.roll_epiphany(c, context)
func trigger_epiphany(c, rng: RandomNumberGenerator) -> void: insight.trigger_epiphany(c, rng)
func consult_jade_tree(c) -> Dictionary: return insight.consult_jade_tree(c)
func chess_of(site: String) -> Dictionary: return insight.chess_of(site)
func chess_open(c, site: String) -> bool: return insight.chess_open(c, site)
func solve_chess(c, site: String, choice: String) -> Dictionary: return insight.solve_chess(c, site, choice)
func apply_insight_best(actor_id: String, amount: float, context := "fortune") -> void: insight.apply_insight_best(actor_id, amount, context)

# Attunement (progression_attunement.gd)
func attunement_required(room_id: String) -> float: return attunement.attunement_required(room_id)
func attunement_value(c, zone_id: String) -> float: return attunement.attunement_value(c, zone_id)
func attunement_factors(c) -> Dictionary: return attunement.attunement_factors(c)
func jade_levels(c, zone_id: String) -> Array: return attunement.jade_levels(c, zone_id)
func jade_cost(zone_id: String, level: int) -> int: return attunement.jade_cost(zone_id, level)
func attune_jade(c, zone_id: String, index: int) -> Dictionary: return attunement.attune_jade(c, zone_id, index)

# The body (progression_body.gd)
func apply_body_xp(actor_id: String, xp: float, _source: String) -> void: body.apply_body_xp(actor_id, xp, _source)
func pass_body_trial(actor_id: String, tier: String) -> void: body.pass_body_trial(actor_id, tier)
func _check_body_tier(c) -> void: body.check_body_tier(c)
func awaken_physique(actor_id: String, physique: String) -> void: body.awaken_physique(actor_id, physique)
func add_lifetime(c, key: String, amount: float) -> void: body.add_lifetime(c, key, amount)
func _count_streak(c) -> void: body.count_streak(c)
func _on_fire_pill(p: Dictionary) -> void: body.on_fire_pill(p)
func add_air_distance(actor_id: String, px: float) -> void: body.add_air_distance(actor_id, px)

# Condition (progression_condition.gd)
func apply_injury(actor_id: String, kind: String, severity: int) -> void: condition.apply_injury(actor_id, kind, severity)
func apply_cure_injury(actor_id: String, kind: String, max_severity: int) -> void: condition.apply_cure_injury(actor_id, kind, max_severity)
func apply_toxicity(actor_id: String, amount: float) -> void: condition.apply_toxicity(actor_id, amount)
func apply_residue(actor_id: String, amount: float) -> void: condition.apply_residue(actor_id, amount)
func apply_pill_dose(actor_id: String, family: String) -> void: condition.apply_pill_dose(actor_id, family)
func apply_heart_demon(actor_id: String, amount: float, source: String) -> void: condition.apply_heart_demon(actor_id, amount, source)
func apply_settle(actor_id: String) -> void: condition.apply_settle(actor_id)
func apply_stability(actor_id: String, word: String) -> void: condition.apply_stability(actor_id, word)
func apply_soul(actor_id: String, amount: float) -> void: condition.apply_soul(actor_id, amount)
func apply_purity(actor_id: String, points: float) -> void: condition.apply_purity(actor_id, points)
func apply_longevity(actor_id: String, years: int) -> void: condition.apply_longevity(actor_id, years)

# Vows, paths and the false realm (progression_vows.gd)
func set_vow(c, vow: String, on: bool) -> Dictionary: return vows.set_vow(c, vow, on)
func set_path(c, path: String, on: bool) -> Dictionary: return vows.set_path(c, path, on)
static func walks(c, path: String) -> bool: return ProgressionVows.walks(c, path)
func vow_forbids(c, what: String) -> String: return vows.vow_forbids(c, what)
func set_false_realm(c, realm: String) -> Dictionary: return vows.set_false_realm(c, realm)
func false_realm_choices(c) -> Array: return vows.false_realm_choices(c)
func shown_realm(c) -> String: return vows.shown_realm(c)

# Methods, meridians and techniques (progression_techniques.gd)
func apply_learn_method(actor_id: String, method_id: String) -> void: techniques.apply_learn_method(actor_id, method_id)
func switch_method(c, method_id: String, use_pill: bool) -> Dictionary: return techniques.switch_method(c, method_id, use_pill)
func method_switch_preview(c, use_pill: bool) -> float: return techniques.method_switch_preview(c, use_pill)
func open_meridian(c, channel: String) -> Dictionary: return techniques.open_meridian(c, channel)
func reset_meridians(c) -> Dictionary: return techniques.reset_meridians(c)
func apply_reset_meridians(actor_id: String) -> void: techniques.apply_reset_meridians(actor_id)
func apply_learn_technique(actor_id: String, tid: String) -> void: techniques.apply_learn_technique(actor_id, tid)
func apply_learn_secret_art(actor_id: String, art: String) -> void: techniques.apply_learn_secret_art(actor_id, art)
func equip_technique(c, slot: int, tid: String) -> Dictionary: return techniques.equip_technique(c, slot, tid)
func rank_up_technique(c, tid: String) -> Dictionary: return techniques.rank_up_technique(c, tid)
func apply_learn_inner_art(actor_id: String, art: String) -> void: techniques.apply_learn_inner_art(actor_id, art)
func equip_inner_art(c, slot: int, art: String) -> Dictionary: return techniques.equip_inner_art(c, slot, art)
func set_stance(c, family: String, stance: String) -> Dictionary: return techniques.set_stance(c, family, stance)

# The element trees and the Lost Arts (progression_trees.gd)
func realisations(c) -> Dictionary: return trees.realisations(c)
func realisations_free(c) -> int: return trees.realisations_free(c)
func meridian_points_free(c) -> int: return trees.meridian_points_free(c)
func realise_node(c, nid: String) -> Dictionary: return trees.realise_node(c, nid)
func unrealise_node(c, nid: String) -> Dictionary: return trees.unrealise_node(c, nid)
func reset_tree(c, tree: String) -> Dictionary: return trees.reset_tree(c, tree)
func migrate_tree(c) -> void: trees.migrate_tree(c)
func tree_node(c, nid: String, ctx: Dictionary = {}) -> Dictionary: return trees.tree_node(c, nid, ctx)
func tree_dao_arts(c, tree: String) -> Array: return trees.tree_dao_arts(c, tree)
func node_needs(c, nid: String) -> Array: return trees.node_needs(c, nid)
func lost_unread(c) -> Array: return trees.lost_unread(c)
func tree_tabs(c) -> Array: return trees.tree_tabs(c)
func lost_arts_view(c) -> Dictionary: return trees.lost_arts_view(c)
func apply_learn_lost_art(actor_id: String, art: String) -> void: trees.apply_learn_lost_art(actor_id, art)
func read_stele(c, object_id: String) -> bool: return trees.read_stele(c, object_id)
func lost_drops(c, rolled: Array) -> Array: return trees.lost_drops(c, rolled)
func lost_pages(c) -> void: trees.lost_pages(c)
