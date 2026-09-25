class_name CultivatorState
extends RefCounted
## S04 · The six tracks of one character (Realm, Energy, Body, Soul, Dao, World)
## plus shared cultivation state. Scene-free: primitives, arrays, dictionaries and
## stable IDs only. HP/QI/Soul current values live in the ResourcePool.

const VERSION := 6

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
# and the heart-demon meter (the karma ledger moved to RelationsState, S49).
var pill_resistance: Dictionary = {} # pill family -> {count, doses}: every 5 doses add 1 to count (S44)
var foundation: Dictionary = {}      # {realm (great realm), total_qp, pill_qp} QP since the last major breakthrough (S44)
var residue := 0.0
var heart_demon := 0.0               # 0-100: each 25 is a risk step at a major breakthrough
var support_failures: Dictionary = {} # realm key -> failed attempts made there with support pills (S44)
var treasure_uses: Dictionary = {}   # natural treasure -> realm (or stage) it was last used in
# Heart and fate (S48). Version 6 writes every field; the rules that read vows, Inner Arts, stances, the false
# realm and fates arrive with their systems.
var body_tier := "mortal"            # mortal | copper | iron | jade | gold (body_tiers.json)
var body_trials: Array = []          # body tiers whose Temper trial is passed
var body_baths: Array = []           # body tiers whose bath was soaked in full
var core_grade := 0                  # the purity grade the core formed at (Heart Tempering 9 -> Cloud Stride 1); 0 before
var fates: Array = []                # fate cards chosen at major breakthroughs: {id, realm, next?, dao?}
var fate_offer: Array = []           # the cards drawn and waiting for a choice
var physiques: Array = []            # physiques awakened by deeds (physiques.json)
var vows: Array = []
var inner_arts: Array = []           # the Inner Art slots: art id or "" (2 at QU1, 3 at HT1, 4 at SA1)
var inner_arts_known: Array = []     # Inner Arts learned from manuals
var stances: Dictionary = {}         # weapon family -> stance id
var false_realm := ""
var longevity := 0                   # S49: years added to the realm's lifespan by longevity treasures (display only)
var epiphany_cooldown := 0.0
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
var technique_bars: Dictionary = {}   # S47 dual loadout: "a"/"b" -> the bar kept for the weapon not in hand
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
		"heart_demon": heart_demon,
		"support_failures": support_failures.duplicate(),
		"body_tier": body_tier, "body_trials": body_trials.duplicate(), "body_baths": body_baths.duplicate(), "core_grade": core_grade,
		"fates": fates.duplicate(true), "fate_offer": fate_offer.duplicate(), "physiques": physiques.duplicate(), "vows": vows.duplicate(), "inner_arts": inner_arts.duplicate(), "inner_arts_known": inner_arts_known.duplicate(),
		"stances": stances.duplicate(), "false_realm": false_realm, "longevity": longevity, "epiphany_cooldown": epiphany_cooldown,
		"methods_known": methods_known.duplicate(), "aptitude": aptitude.duplicate(true), "origin": origin,
		"meridians": meridians.duplicate(), "unspent_meridian_points": unspent_meridian_points,
		"meridian_levels_granted": meridian_levels_granted,
		"unlocked": unlocked.keys(), "offered": offered.duplicate(), "revealed": revealed.keys(),
		"techniques": {"known": techniques_known.duplicate(), "slots": technique_slots.duplicate(),
			"mastery": mastery.duplicate(true), "use": technique_use.duplicate(), "bars": technique_bars.duplicate(true)},
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
	# Version 5 (S44): resistance counts every 5 doses; foundation keys are pill_qp and total_qp.
	pill_resistance = {}
	for fam in _dict(d, "pill_resistance"):
		var v = d.pill_resistance[fam]
		var key := "accumulation" if str(fam) == "qi" else str(fam)
		pill_resistance[key] = {"count": int(v.get("count", 0)), "doses": int(v.get("doses", 0))} if v is Dictionary else {"count": int(v) / 5, "doses": int(v) % 5}
	foundation = _dict(d, "foundation")
	if foundation.has("total") or foundation.has("pill"):
		foundation = {"realm": str(foundation.get("realm", "")), "total_qp": float(foundation.get("total", 0.0)), "pill_qp": float(foundation.get("pill", 0.0))}
	residue = maxf(0.0, _num(d, "residue", 0.0))
	heart_demon = clampf(_num(d, "heart_demon", 0.0), 0.0, 100.0)
	support_failures = {}
	for rk in _dict(d, "support_failures"): support_failures[rk] = int(d.support_failures[rk])
	for rk in _dict(d, "support_fails"):   # version 4: per item; the worst item's count carries over
		var worst := 0
		for it in d.support_fails[rk]: worst = maxi(worst, int(d.support_fails[rk][it]))
		support_failures[rk] = maxi(int(support_failures.get(rk, 0)), worst)
	body_tier = str(d.get("body_tier", "mortal"))
	if body_tier != "mortal" and not ContentDB.has_entry("body_tiers", body_tier): body_tier = "mortal"
	body_trials = _arr(d, "body_trials")
	body_baths = _arr(d, "body_baths")
	core_grade = clampi(int(_num(d, "core_grade", 0)), 0, 9)
	fates = []
	for f in _arr(d, "fates"):
		if f is Dictionary and ContentDB.has_entry("fates", str(f.get("id", ""))): fates.append(f)
	fate_offer = []
	for f in _arr(d, "fate_offer"):
		if ContentDB.has_entry("fates", str(f)): fate_offer.append(str(f))
	physiques = _arr(d, "physiques")
	vows = _arr(d, "vows")
	inner_arts = []
	for a in _arr(d, "inner_arts"): inner_arts.append(str(a) if ContentDB.has_entry("inner_arts", str(a)) else "")
	inner_arts_known = []
	for a in _arr(d, "inner_arts_known"):
		if ContentDB.has_entry("inner_arts", str(a)): inner_arts_known.append(str(a))
	stances = _dict(d, "stances")
	false_realm = str(d.get("false_realm", "")) if d.get("false_realm") != null else ""
	longevity = int(d.get("longevity", 0))
	epiphany_cooldown = maxf(0.0, _num(d, "epiphany_cooldown", 0.0))
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
	technique_bars = {}
	var bars = t.get("bars", {})
	if bars is Dictionary:
		for k in ["a", "b"]:
			if bars.get(k) is Array: technique_bars[k] = (bars[k] as Array).duplicate()
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
