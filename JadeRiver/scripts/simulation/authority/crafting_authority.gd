class_name CraftingAuthority
extends Authority
## S15/S16/S33 · Recipes known, profession ranks, gathering and mining nodes,
## fishing, cooking, alchemy (five-screen mini-game scores), the forge and the
## auto-refine queue. One crafting framework: validate inputs, consume, roll quality
## with the `crafting` stream, grant output and profession XP, emit craft_completed.
##
## The authority keeps the state and takes the intents; the work is done by its parts in authority/crafting/, one for
## each section (audit 45, S10: CraftingPart says how a part works). Its public methods forward to them.

var pending: Dictionary = {}   # actor -> {object, kind, started, channel}
var steps: Dictionary = {}     # actor -> {recipe, craft, scores}: the mini-game in progress
var refines: Dictionary = {}   # actor -> the five-screen refine in progress (V9e2): see start_refine
var tribulations: Dictionary = {}   # actor -> the pill tribulation in progress {recipe, count, quality, fire, furnace, bolts[], blocked, answered, stage}

const NODE_CRAFT := {"herb_patch": "herb_gathering", "ore_vein": "mining", "fishing_spot": "fishing", "star_sight": "star_charting",
	"insect_swarm": "insect_netting"}
const RANK_CAPS := {
	"herb_gathering": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"], ["sage_sovereign_1", "grandmaster"]],
	"mining": [["qi_unfurling_1", "adept"], ["spirit_awakening_1", "expert"], ["sage_sovereign_1", "master"]],
	"cooking": [["qi_kindling_1", "adept"], ["heart_tempering_1", "expert"], ["heaven_glimpse_1", "master"]],
	"fishing": [["qi_kindling_1", "adept"], ["cloud_stride_1", "expert"], ["sage_1", "master"]],
	"alchemy": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
	"smithing": [["qi_unfurling_1", "adept"], ["cloud_stride_1", "expert"], ["heaven_glimpse_1", "master"]],
	# S16: the Starsea crafts open at Sage 3 and rise with the Sovereign stages.
	"star_charting": [["sage_3", "adept"], ["sage_sovereign_1", "expert"], ["sage_sovereign_3", "master"]],
	"shipwright": [["sage_3", "adept"], ["sage_sovereign_1", "expert"], ["sage_sovereign_3", "master"]],
	# S47: Old Scribe Bai's brush, from Qi Kindling 6.
	"talisman": [["qi_kindling_6", "adept"], ["heart_tempering_1", "expert"], ["cloud_stride_1", "master"]],
}
## Stations and the verb each craft uses; the Starsea crafts take no mini-game.
const STATIONS := {"cooking": ["cooking_pot"], "alchemy": ["alchemy_furnace", "earth_vent"], "smithing": ["forge_anvil"],
	"star_charting": ["chart_table"], "shipwright": ["shipyard_slip"]}
const GRADE_CAP := [["qi_kindling_1", "common"], ["qi_unfurling_1", "earth"], ["cloud_stride_1", "heaven"], ["heaven_glimpse_1", "mystic"], ["sage_1", "spirit"],
	["sage_sovereign_1", "sage"], ["will_manifest_1", "sovereign"], ["sphere_lord_1", "will"]]

var professions: CraftingProfessions
var gathering: CraftingGathering
var garden: CraftingGarden
var recipes: CraftingRecipes
var refine: CraftingRefine
var furnaces: CraftingFurnaces
var forge: CraftingForge
var research: CraftingResearch
var guilds: CraftingGuilds

func _init(g) -> void:
	super(g)
	professions = CraftingProfessions.new(self)
	gathering = CraftingGathering.new(self)
	garden = CraftingGarden.new(self)
	recipes = CraftingRecipes.new(self)
	refine = CraftingRefine.new(self)
	furnaces = CraftingFurnaces.new(self)
	forge = CraftingForge.new(self)
	research = CraftingResearch.new(self)
	guilds = CraftingGuilds.new(self)

func intents() -> Array:
	return ["complete_node", "catch_fish", "cook", "craft_step", "refine", "start_refine", "refine_input", "cancel_refine", "queue_auto_refine",
		"collect_auto_refine", "forge", "enhance", "salvage_item",
		"salvage", "inherit_enhancement", "reroll_affixes", "choose_affixes", "lock_affix", "chart_route", "build_vessel", "absorb_flame",
		"trace_talisman", "restore_relic", "awaken_weapon", "mend_furnace", "deduce_recipe", "start_experiment", "take_guild_exam", "accept_commission",
		"deliver_commission", "tribulation_shield", "catch_pill_soul", "plant_seed", "water_bed", "harvest_bed", "apply_spirit_soil", "use_dew",
		"transplant", "start_rack", "collect_racks"]

func subscribe() -> void:
	# S44 guild exams count what comes out of the furnace while the candle burns.
	GameEvents.subscribe("craft_completed", guilds.on_craft_completed, 40)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"complete_node": return complete_node(c, str(intent.get("object", "")), float(intent.get("timing", -1.0)))
		"catch_fish": return catch_fish(c, str(intent.get("object", "")), intent.get("result", {}))
		"cook": return craft(c, str(intent.get("recipe", "")), maxi(1, int(intent.get("count", 1))), [], "cooking")
		"craft_step": return craft_step(c, str(intent.get("recipe", "")), str(intent.get("craft", "alchemy")), float(intent.get("offset", 1.0)),
			str(intent.get("fire", "charcoal")))
		"refine": return craft(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), recipes.take_steps(c, str(intent.get("recipe", ""))), "alchemy",
			str(intent.get("fire", "charcoal")), intent.get("substitute", {}) if intent.get("substitute", {}) is Dictionary else {}, bool(intent.get("live", false)))
		"start_refine": return start_refine(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10), str(intent.get("fire", "charcoal")),
			str(intent.get("array", "")), intent.get("substitute", {}) if intent.get("substitute", {}) is Dictionary else {})
		"refine_input": return refine_input(c, str(intent.get("step", "")), intent.get("value", {}) if intent.get("value", {}) is Dictionary else {})
		"cancel_refine": return cancel_refine(c)
		"tribulation_shield": return tribulation_shield(c, int(intent.get("bolt", -1)), float(intent.get("timing", 99.0)))
		"catch_pill_soul": return catch_pill_soul(c, float(intent.get("timing", 99.0)))
		"forge": return craft(c, str(intent.get("recipe", "")), 1, recipes.take_steps(c, str(intent.get("recipe", ""))), "smithing")
		"queue_auto_refine": return queue_auto(c, str(intent.get("recipe", "")), clampi(int(intent.get("count", 1)), 1, 10))
		"absorb_flame": return absorb_flame(c, int(intent.get("index", -1)))
		"collect_auto_refine": return collect_auto(c)
		"enhance": return enhance(c, intent)
		"salvage_item": return salvage(c, [forge.uid_at(c, int(intent.get("index", -1)))])
		"salvage": return salvage(c, intent.get("items", []))
		"inherit_enhancement": return inherit(c, int(intent.get("from", -1)), int(intent.get("to", -1)))
		"reroll_affixes": return reroll(c, int(intent.get("uid", -1)))
		"choose_affixes": return choose_affixes(c, int(intent.get("uid", -1)), str(intent.get("keep", "new")) == "new")
		"lock_affix": return lock_affix(c, int(intent.get("uid", -1)), int(intent.get("affix", -1)))
		"trace_talisman": return trace_talisman(c, str(intent.get("recipe", "")), float(intent.get("score", 0.0)), bool(intent.get("broken", false)))
		"restore_relic": return restore_relic(c, int(intent.get("index", -1)))
		"awaken_weapon": return awaken_weapon(c, intent)
		"mend_furnace": return mend_furnace(c, int(intent.get("uid", -1)))
		"deduce_recipe": return deduce(c, str(intent.get("recipe", "")))
		"start_experiment": return experiment(c, intent.get("herbs", []) if intent.get("herbs", []) is Array else [])
		"take_guild_exam": return take_exam(c, str(intent.get("craft", "alchemy")), str(intent.get("rank", "")))
		"accept_commission": return accept_commission(c, str(intent.get("id", "")))
		"deliver_commission": return deliver_commission(c, str(intent.get("id", "")), str(intent.get("pay", "taels")))
		"plant_seed": return plant_seed(c, str(intent.get("bed", "")), str(intent.get("seed", "")))
		"water_bed": return water_bed(c, str(intent.get("bed", "")))
		"harvest_bed": return harvest_bed(c, str(intent.get("bed", "")))
		"apply_spirit_soil": return apply_spirit_soil(c, str(intent.get("bed", "")))
		"use_dew": return use_dew(c, str(intent.get("bed", "")))
		"transplant": return transplant(c, str(intent.get("object", "")))
		"start_rack": return start_rack(c, str(intent.get("kind", "")), str(intent.get("herb", "")), int(intent.get("count", 1)))
		"collect_racks": return collect_racks(c)
		"chart_route": return craft(c, str(intent.get("recipe", "")), 1, [], "star_charting")
		"build_vessel": return craft(c, str(intent.get("recipe", "")), 1, [], "shipwright")
	return fail("unknown_intent")

func tick(_delta: float) -> void:
	guilds.tick_exam()

# ------------------------------------------------------------------ the facade
## Every public method, forwarded to the part that does the work, among them the helpers tests and tools call by name
## (public since audit 45's S11).

# Professions (crafting_professions.gd)
func rank_of(c, craft: String) -> String: return professions.rank_of(c, craft)
func rank_index(rank: String) -> int: return professions.rank_index(rank)
func rank_cap(c, craft: String) -> int: return professions.rank_cap(c, craft)
func add_xp(c, craft: String, xp: float) -> void: professions.add_xp(c, craft, xp)
func grade_cap(c) -> String: return professions.grade_cap(c)
func tool_power(c, craft: String) -> float: return professions.tool_power(c, craft)
func station_near(c, types: Array) -> bool: return professions.station_near(c, types)

# Gathering (crafting_gathering.gd)
func gather(c, o: Dictionary) -> Dictionary: return gathering.gather(c, o)
func complete_node(c, object_id: String, timing := -1.0) -> Dictionary: return gathering.complete_node(c, object_id, timing)
func catch_fish(c, object_id: String, result: Dictionary) -> Dictionary: return gathering.catch_fish(c, object_id, result)

# The garden (crafting_garden.gd)
func beds(c) -> Dictionary: return garden.beds(c)
func bed_def(key: String) -> Dictionary: return garden.bed_def(key)
func bed_record(c, key: String) -> Dictionary: return garden.bed_record(c, key)
func bed_grade(c, key: String) -> String: return garden.bed_grade(c, key)
func bed_holds(c, key: String, herb: String) -> bool: return garden.bed_holds(c, key, herb)
func bed_speed(key: String) -> float: return garden.bed_speed(key)
func settle_bed(c, key: String) -> Dictionary: return garden.settle_bed(c, key)
func bed_view(c, key: String) -> Dictionary: return garden.bed_view(c, key)
func room_beds(c, room_id: String) -> Array: return garden.room_beds(c, room_id)
func bed_check(c, key: String) -> String: return garden.bed_check(c, key)
func plant_seed(c, key: String, seed: String) -> Dictionary: return garden.plant_seed(c, key, seed)
func water_bed(c, key: String) -> Dictionary: return garden.water_bed(c, key)
func harvest_bed(c, key: String) -> Dictionary: return garden.harvest_bed(c, key)
func apply_spirit_soil(c, key: String) -> Dictionary: return garden.apply_spirit_soil(c, key)
func dew_state(c) -> Dictionary: return garden.dew_state(c)
func dew_age_cap(key: String) -> int: return garden.dew_age_cap(key)
func use_dew(c, key: String) -> Dictionary: return garden.use_dew(c, key)
func bottle_spring_water(c) -> Dictionary: return garden.bottle_spring_water(c)
func racks(c) -> Array: return garden.racks(c)
func start_rack(c, kind: String, herb: String, count: int) -> Dictionary: return garden.start_rack(c, kind, herb, count)
func collect_racks(c) -> Dictionary: return garden.collect_racks(c)
func check_raids(c) -> Array: return garden.check_raids(c)
func can_transplant(c) -> bool: return garden.can_transplant(c)
func transplant_death(c) -> float: return garden.transplant_death(c)
func transplant(c, object_id: String) -> Dictionary: return garden.transplant(c, object_id)
func evergreen_state(c) -> Dictionary: return garden.evergreen_state(c)
func tend_treasure_plot(c, o: Dictionary) -> Dictionary: return garden.tend_treasure_plot(c, o)

# Recipes and the craft (crafting_recipes.gd)
func apply_learn_recipe(actor_id: String, recipe: String) -> void: recipes.apply_learn_recipe(actor_id, recipe)
func knows(c, recipe: String) -> bool: return recipes.knows(c, recipe)
func recipe_check(c, recipe_id: String, count: int, craft: String, inputs: Array = [], anywhere := false) -> String: return recipes.recipe_check(c, recipe_id, count, craft, inputs, anywhere)
func with_aged(c, inputs: Array, count: int) -> Dictionary: return recipes.with_aged(c, inputs, count)
func craft_step(c, recipe_id: String, craft_kind: String, offset: float, fire := "charcoal") -> Dictionary: return recipes.craft_step(c, recipe_id, craft_kind, offset, fire)
func steps_for(recipe_id: String) -> int: return recipes.steps_for(recipe_id)
func craft(c, recipe_id: String, count: int, scores: Array, craft_kind: String, fire := "charcoal", substitute: Dictionary = {}, live := false) -> Dictionary: return recipes.craft(c, recipe_id, count, scores, craft_kind, fire, substitute, live)
func consume(c, recipe_id: String, rows: Array, principal: String) -> Dictionary: return recipes.consume(c, recipe_id, rows, principal)
func quality_score(c, craft_kind: String, furnace: Dictionary, r: Dictionary, scores: Array) -> float: return recipes.quality_score(c, craft_kind, furnace, r, scores)
func queue_auto(c, recipe_id: String, count: int) -> Dictionary: return recipes.queue_auto(c, recipe_id, count)
func collect_auto(c) -> Dictionary: return recipes.collect_auto(c)
func trace_talisman(c, recipe_id: String, score: float, broken: bool) -> Dictionary: return recipes.trace_talisman(c, recipe_id, score, broken)

# The five-screen refine (crafting_refine.gd)
func furnace_game() -> Dictionary: return refine.furnace_game()
func refine_session(c) -> Dictionary: return refine.refine_session(c)
func suited_array(recipe_id: String, substitute: Dictionary = {}) -> String: return refine.suited_array(recipe_id, substitute)
func array_mult(recipe_id: String, array: String, substitute: Dictionary = {}) -> float: return refine.array_mult(recipe_id, array, substitute)
func heat_band(c, fire: String, recipe_id: String, array: String, substitute: Dictionary = {}) -> float: return refine.heat_band(c, fire, recipe_id, array, substitute)
func impurities_seen(c, n: int) -> int: return refine.impurities_seen(c, n)
func sense_herbs(c, recipe_id: String, count: int, substitute: Dictionary = {}) -> Array: return refine.sense_herbs(c, recipe_id, count, substitute)
func refine_block(c, recipe_id: String, count: int, fire: String, substitute: Dictionary = {}) -> String: return refine.refine_block(c, recipe_id, count, fire, substitute)
func start_refine(c, recipe_id: String, count: int, fire: String, array: String, substitute: Dictionary = {}) -> Dictionary: return refine.start_refine(c, recipe_id, count, fire, array, substitute)
func refine_input(c, step: String, value: Dictionary) -> Dictionary: return refine.refine_input(c, step, value)
func cancel_refine(c) -> Dictionary: return refine.cancel_refine(c)
func nature_shift(recipe_id: String, substitute: Dictionary = {}) -> float: return refine.nature_shift(recipe_id, substitute)
func inputs_with(recipe_id: String, substitute: Dictionary) -> Array: return refine.inputs_with(recipe_id, substitute)
func role_of(recipe_id: String, item_id: String) -> String: return refine.role_of(recipe_id, item_id)
func substitute_check(c, recipe_id: String, from: String, to: String) -> String: return refine.substitute_check(c, recipe_id, from, to)
func substitutes_for(c, recipe_id: String, from: String) -> Array: return refine.substitutes_for(c, recipe_id, from)
func conflict_in(inputs: Array) -> Dictionary: return refine.conflict_in(inputs)
func blast(c, recipe_id: String, inputs: Array, count: int, clash: Dictionary) -> Dictionary: return refine.blast(c, recipe_id, inputs, count, clash)

# Furnaces, fire and the pill tribulation (crafting_furnaces.gd)
func furnace_of(c) -> Dictionary: return furnaces.furnace_of(c)
func fires_available(c) -> Array: return furnaces.fires_available(c)
func band_mult(c, fire: String) -> float: return furnaces.band_mult(c, fire)
func rare_allowed(furnace: Dictionary, fire: String) -> Array: return furnaces.rare_allowed(furnace, fire)
func core_to_burn(c) -> String: return furnaces.core_to_burn(c)
func roll_marks(quality: String, rng: RandomNumberGenerator) -> int: return furnaces.roll_marks(quality, rng)
func absorb_flame(c, index: int) -> Dictionary: return furnaces.absorb_flame(c, index)
func apply_absorb_flame(actor_id: String, id: String) -> void: furnaces.apply_absorb_flame(actor_id, id)
func rare_pill_quality(c, scores: Array, rng: RandomNumberGenerator, allowed: Array = ["pill_grain", "pill_halo", "pill_soul"]) -> String: return furnaces.rare_pill_quality(c, scores, rng, allowed)
func apply_grain_blessing(actor_id: String, value: float) -> void: furnaces.apply_grain_blessing(actor_id, value)
func furnace_bonus(c) -> float: return furnaces.furnace_bonus(c)
func begin_tribulation(c, recipe_id: String, count: int, quality: String, fire: String, furnace: Dictionary, prep := "") -> Dictionary: return furnaces.begin_tribulation(c, recipe_id, count, quality, fire, furnace, prep)
func tribulation_shield(c, bolt: int, timing: float) -> Dictionary: return furnaces.tribulation_shield(c, bolt, timing)
func catch_pill_soul(c, timing: float) -> Dictionary: return furnaces.catch_pill_soul(c, timing)

# Gear upkeep at the forge (crafting_forge.gd)
func upkeep(key: String, fallback): return forge.upkeep(key, fallback)
func grade_row(item_id: String) -> Dictionary: return forge.grade_row(item_id)
func enhance_chance(inst: Dictionary, essence := 0) -> float: return forge.enhance_chance(inst, essence)
func enhance_cost(inst: Dictionary) -> Dictionary: return forge.enhance_cost(inst)
func enhance_check(c, inst: Dictionary, essence := 0) -> String: return forge.enhance_check(c, inst, essence)
func reroll_check(c, inst: Dictionary) -> String: return forge.reroll_check(c, inst)
func enhance(c, intent: Dictionary) -> Dictionary: return forge.enhance(c, intent)
func inherit(c, from_uid: int, to_uid: int) -> Dictionary: return forge.inherit(c, from_uid, to_uid)
func salvage_preview(c, uids: Array) -> Dictionary: return forge.salvage_preview(c, uids)
func salvage(c, uids: Array) -> Dictionary: return forge.salvage(c, uids)
func reroll_cost(inst: Dictionary, c = null) -> Dictionary: return forge.reroll_cost(inst, c)
func free_reroll_ready(c) -> bool: return forge.free_reroll_ready(c)
func reroll(c, uid: int) -> Dictionary: return forge.reroll(c, uid)
func choose_affixes(c, uid: int, keep_new: bool) -> Dictionary: return forge.choose_affixes(c, uid, keep_new)
func lock_affix(c, uid: int, affix: int) -> Dictionary: return forge.lock_affix(c, uid, affix)
func restore_relic(c, index: int) -> Dictionary: return forge.restore_relic(c, index)
static func awaken_grade_ok(item_id: String) -> bool: return CraftingForge.awaken_grade_ok(item_id)
static func awakened_skill(item_id: String) -> Dictionary: return CraftingForge.awakened_skill(item_id)
func awaken_check(c, inst: Dictionary) -> String: return forge.awaken_check(c, inst)
func awaken_weapon(c, intent: Dictionary) -> Dictionary: return forge.awaken_weapon(c, intent)
func mend_cost(inst: Dictionary) -> Dictionary: return forge.mend_cost(inst)
func mend_furnace(c, uid: int) -> Dictionary: return forge.mend_furnace(c, uid)

# Ancient recipes and experiments (crafting_research.gd)
func apply_recipe_page(actor_id: String, recipe: String, page: int) -> void: research.apply_recipe_page(actor_id, recipe, page)
func pages_held(c, recipe: String) -> int: return research.pages_held(c, recipe)
func deduce_chance(c, recipe: String) -> float: return research.deduce_chance(c, recipe)
func ancient_in_progress(c) -> Array: return research.ancient_in_progress(c)
func deduce(c, recipe: String) -> Dictionary: return research.deduce(c, recipe)
static func experiment_key(herbs: Array) -> String: return CraftingResearch.experiment_key(herbs)
func experiment_logged(key: String) -> Dictionary: return research.experiment_logged(key)
func experiment(c, herbs: Array) -> Dictionary: return research.experiment(c, herbs)
func experiment_result_text(e: Dictionary) -> String: return research.experiment_result_text(e)

# Guilds, exams and commissions (crafting_guilds.gd)
func guild_def(craft: String) -> Dictionary: return guilds.guild_def(craft)
func guilds_open(c) -> Array: return guilds.guilds_open(c)
func guild_rank(c, craft: String) -> String: return guilds.guild_rank(c, craft)
func guild_rank_def(craft: String, rank: String) -> Dictionary: return guilds.guild_rank_def(craft, rank)
func next_guild_rank(c, craft: String) -> Dictionary: return guilds.next_guild_rank(c, craft)
static func quality_rank(q: String) -> int: return CraftingGuilds.quality_rank(q)
func exam_block(c, rk: Dictionary) -> String: return guilds.exam_block(c, rk)
static func exam_counts(rk: Dictionary, recipe_id: String) -> bool: return CraftingGuilds.exam_counts(rk, recipe_id)
func take_exam(c, craft: String, rank: String) -> Dictionary: return guilds.take_exam(c, craft, rank)
func exam_left(c) -> float: return guilds.exam_left(c)
static func commission_day() -> int: return CraftingGuilds.commission_day()
func commission_cap(c, craft := "alchemy") -> int: return guilds.commission_cap(c, craft)
func commission_paid_today(c, craft := "alchemy") -> int: return guilds.commission_paid_today(c, craft)
func commissions(c, craft := "alchemy") -> Array: return guilds.commissions(c, craft)
func accept_commission(c, id: String) -> Dictionary: return guilds.accept_commission(c, id)
func deliver_commission(c, id: String, pay: String) -> Dictionary: return guilds.deliver_commission(c, id, pay)
