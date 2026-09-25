class_name CultivatorState
extends RefCounted
## S04 · The six tracks of one character (Realm, Energy, Body, Soul, Dao, World)
## plus shared cultivation state. Scene-free: primitives, arrays, dictionaries and
## stable IDs only. HP/QI/Soul current values live in the ResourcePool.

const VERSION := 4

# Realm track
var realm_key := "mortal"
var state := "accumulating"          # accumulating | bottleneck | consolidating
var qp := 0.0                        # Qi points gathered in the current sub-level
var stored_qi := 0.0
var consolidation_left := 0.0
var breakthrough_cooldown := 0.0
# Energy track
var energy_type := "none"
var purity := 9                      # grade 9 -> 1 from Cloud Stride
var purity_points := 0.0
# Body track
var body_level := 1
var body_xp := 0.0
# Soul track
var soul_cultivation := 0.0
# Dao track: id -> {tier, insight}
var daos: Dictionary = {}
var insight_memory: Dictionary = {}  # context -> last tick (diminishing returns)
# World track
var attunement: Dictionary = {}
var attunement_jades: Dictionary = {}   # zone -> [jade levels] (S18); attunement[zone] is their total
var inner_world = null
var events_passed: Array = []        # heavens_cleansing, heart_trial ...
# Shared
var stability := "stable"
var stability_progress := 0.0        # seconds of meditation toward the next step
var injuries: Dictionary = {}        # kind -> {severity, time_left}
var toxicity := 0.0
var pill_memory: Dictionary = {}     # pill group -> last use sim time (repeat window)
# What yesterday's shortcuts cost (gap report G1): lasting pill resistance, the share of this
# great realm's QP that came from pills and cores, the residue that never drains on its own,
# the heart-demon meter and the karma ledger.
var pill_resistance: Dictionary = {} # pill family (qi, body, soul, insight) -> doses taken
var foundation: Dictionary = {}      # {realm (great realm), total, pill} QP this great realm
var residue := 0.0
var heart_demon := 0.0               # 0-100: each 25 is a risk step at a major breakthrough
var merit := 0
var sin := 0
var debts: Dictionary = {}           # named karma debts: id -> {text, due_utc, kind, paid}
var merit_used: Dictionary = {}      # great realm -> true once merit has eased its breakthrough
var support_fails: Dictionary = {}   # realm key -> {support item: failed attempts it was used in}
var treasure_uses: Dictionary = {}   # natural treasure -> realm (or stage) it was last used in
var method_id := ""
var methods_known: Array = []
var aptitude: Dictionary = {}        # key -> {value, revealed}
var origin := ""
var meridians: Dictionary = {"body": 0, "agility": 0, "essence": 0, "spirit": 0, "insight": 0}
var unspent_meridian_points := 0
var meridian_levels_granted := 0     # highest Level whose meridian points were granted
# Unlocks (owned by the unlock service, stored here per S02)
var unlocked: Dictionary = {}
var offered: Dictionary = {}
var revealed: Dictionary = {}
# Techniques (Progression owns knowledge; Combat owns use)
var techniques_known: Array = []
var technique_slots: Array = [null, null, null, null, null, null, null, null]
var mastery: Dictionary = {}         # technique -> {tier, points}
var technique_use: Dictionary = {}   # technique -> uses (Heart Trial reflection)
var secret_arts: Array = []
# Meditation
var meditating := false
var meditation_settle := 0.0
var meditation_spot := ""
var bottleneck_seconds := 0.0
var consolidation_penalty := false
var titles: Array = []
var active_title := ""
var lifetime_stats: Dictionary = {}

func need() -> float:
	return float(ContentDB.realm(realm_key).get("accumulate_needed", 100))

func progress_fraction() -> float:
	var n := need()
	return clampf(qp / n, 0.0, 1.0) if n > 0 else 1.0

func snapshot() -> Dictionary:
	return {"realm_key": realm_key, "state": state, "progress": progress_fraction(), "qp": qp, "stored_qi": stored_qi,
		"consolidation_left": consolidation_left, "breakthrough_cooldown": breakthrough_cooldown,
		"energy_type": energy_type, "purity": purity, "purity_points": purity_points,
		"body_level": body_level, "body_xp": body_xp, "soul_cultivation": soul_cultivation,
		"daos": daos.duplicate(true), "attunement": attunement.duplicate(true), "attunement_jades": attunement_jades.duplicate(true), "inner_world": inner_world,
		"events_passed": events_passed.duplicate(), "stability": stability, "stability_progress": stability_progress,
		"injuries": injuries.duplicate(true), "toxicity": toxicity, "treasure_uses": treasure_uses.duplicate(), "method_id": method_id,
		"pill_resistance": pill_resistance.duplicate(), "foundation": foundation.duplicate(), "residue": residue,
		"heart_demon": heart_demon, "merit": merit, "sin": sin, "debts": debts.duplicate(true), "merit_used": merit_used.duplicate(),
		"support_fails": support_fails.duplicate(true),
		"methods_known": methods_known.duplicate(), "aptitude": aptitude.duplicate(true), "origin": origin,
		"meridians": meridians.duplicate(), "unspent_meridian_points": unspent_meridian_points,
		"meridian_levels_granted": meridian_levels_granted,
		"unlocked": unlocked.keys(), "offered": offered.duplicate(), "revealed": revealed.keys(),
		"techniques": {"known": techniques_known.duplicate(), "slots": technique_slots.duplicate(),
			"mastery": mastery.duplicate(true), "use": technique_use.duplicate()},
		"secret_arts": secret_arts.duplicate(), "titles": titles.duplicate(), "active_title": active_title,
		"lifetime_stats": lifetime_stats.duplicate(), "bottleneck_seconds": bottleneck_seconds,
		"consolidation_penalty": consolidation_penalty}

func restore(d: Dictionary) -> void:
	realm_key = str(d.get("realm_key", "mortal"))
	if ContentDB.realm(realm_key).is_empty(): realm_key = "mortal"
	state = str(d.get("state", "accumulating"))
	if state not in ["accumulating", "bottleneck", "consolidating"]: state = "accumulating"
	qp = _num(d, "qp", _num(d, "progress", 0.0) * need())
	stored_qi = _num(d, "stored_qi", 0.0)
	consolidation_left = _num(d, "consolidation_left", 0.0)
	breakthrough_cooldown = _num(d, "breakthrough_cooldown", 0.0)
	energy_type = str(d.get("energy_type", ContentDB.realm(realm_key).get("energy", "none")))
	purity = clampi(int(_num(d, "purity", 9)), 1, 9)
	purity_points = _num(d, "purity_points", 0.0)
	body_level = maxi(1, int(_num(d, "body_level", 1)))
	body_xp = _num(d, "body_xp", 0.0)
	soul_cultivation = _num(d, "soul_cultivation", 0.0)
	daos = _dict(d, "daos")
	attunement = _dict(d, "attunement")
	attunement_jades = _dict(d, "attunement_jades")
	inner_world = d.get("inner_world", null)
	events_passed = _arr(d, "events_passed")
	stability = str(d.get("stability", "stable"))
	stability_progress = _num(d, "stability_progress", 0.0)
	injuries = _dict(d, "injuries")
	toxicity = _num(d, "toxicity", 0.0)
	treasure_uses = _dict(d, "treasure_uses")
	pill_resistance = _dict(d, "pill_resistance")
	foundation = _dict(d, "foundation")
	residue = maxf(0.0, _num(d, "residue", 0.0))
	heart_demon = clampf(_num(d, "heart_demon", 0.0), 0.0, 100.0)
	merit = maxi(0, int(_num(d, "merit", 0)))
	sin = maxi(0, int(_num(d, "sin", 0)))
	debts = _dict(d, "debts")
	merit_used = _dict(d, "merit_used")
	support_fails = _dict(d, "support_fails")
	method_id = str(d.get("method_id", ""))
	methods_known = _arr(d, "methods_known")
	aptitude = _dict(d, "aptitude")
	origin = str(d.get("origin", ""))
	var m := _dict(d, "meridians")
	for k in meridians: meridians[k] = int(m.get(k, 0))
	unspent_meridian_points = int(_num(d, "unspent_meridian_points", 0))
	meridian_levels_granted = int(_num(d, "meridian_levels_granted", 0))
	unlocked.clear()
	for k in _arr(d, "unlocked"): unlocked[str(k)] = true
	offered = _dict(d, "offered")
	revealed.clear()
	for k in _arr(d, "revealed"): revealed[str(k)] = true
	var t := _dict(d, "techniques")
	techniques_known = t.get("known", []).duplicate()
	technique_slots = [null, null, null, null, null, null, null, null]
	var slots: Array = t.get("slots", [])
	for i in mini(8, slots.size()): technique_slots[i] = slots[i]
	mastery = t.get("mastery", {}).duplicate(true)
	technique_use = t.get("use", {}).duplicate()
	secret_arts = _arr(d, "secret_arts")
	titles = _arr(d, "titles")
	active_title = str(d.get("active_title", ""))
	lifetime_stats = _dict(d, "lifetime_stats")
	bottleneck_seconds = _num(d, "bottleneck_seconds", 0.0)
	consolidation_penalty = bool(d.get("consolidation_penalty", false))

static func _num(d: Dictionary, key: String, fallback: float) -> float:
	var v = d.get(key, fallback)
	if (v is float or v is int) and is_finite(float(v)): return float(v)
	return fallback

static func _dict(d: Dictionary, key: String) -> Dictionary:
	var v = d.get(key, {})
	return v.duplicate(true) if v is Dictionary else {}

static func _arr(d: Dictionary, key: String) -> Array:
	var v = d.get(key, [])
	return v.duplicate(true) if v is Array else []
