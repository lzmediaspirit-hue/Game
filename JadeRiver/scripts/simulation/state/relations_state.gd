class_name RelationsState
extends RefCounted
## S49 · What the world remembers of one character: the karma ledger (merit, sin, named debts), the righteous-demonic
## alignment, personal Fame, NPC affinity, formal bonds, grudges, bounties, mortal missions and the Fortune meter.
## Only the Relations authority writes here.

var merit := 0
var sin := 0
var debts: Dictionary = {}           # id -> {due_utc, mail, attachments, paid, callback}
var merit_used: Dictionary = {}      # great realm -> true once merit has eased its breakthrough
var alignment := 0                   # -100 demonic ... +100 righteous; never gates core realm progress
var fame := 0                        # Unknown -> Noted -> Rising -> Renowned -> Legendary
var affinity: Dictionary = {}        # npc -> {hearts, gift_day}
var bonds: Dictionary = {"dao_companion": "", "master": "", "sworn": []}
var grudges: Dictionary = {}         # faction -> value
var bounties: Array = []             # taken bounty ids
var mortal: Dictionary = {}          # mortal missions
var fortune: Dictionary = {}         # {meter, last_utc}
var deeds: Dictionary = {}           # once-only deeds done: id (or id:key) -> true
var ledger: Array = []               # the latest karma entries, newest first: {reason, merit, sin, utc}

func snapshot() -> Dictionary:
	return {"merit": merit, "sin": sin, "debts": debts.duplicate(true), "merit_used": merit_used.duplicate(), "alignment": alignment,
		"fame": fame, "affinity": affinity.duplicate(true), "bonds": bonds.duplicate(true), "grudges": grudges.duplicate(),
		"bounties": bounties.duplicate(true), "mortal": mortal.duplicate(true), "fortune": fortune.duplicate(), "deeds": deeds.duplicate(),
		"ledger": ledger.duplicate(true)}

func restore(d: Dictionary) -> void:
	merit = maxi(0, int(d.get("merit", 0)))
	sin = maxi(0, int(d.get("sin", 0)))
	debts = d.get("debts", {}).duplicate(true) if d.get("debts") is Dictionary else {}
	merit_used = d.get("merit_used", {}).duplicate() if d.get("merit_used") is Dictionary else {}
	alignment = clampi(int(d.get("alignment", 0)), -100, 100)
	fame = maxi(0, int(d.get("fame", 0)))
	affinity = d.get("affinity", {}).duplicate(true) if d.get("affinity") is Dictionary else {}
	bonds = {"dao_companion": "", "master": "", "sworn": []}
	if d.get("bonds") is Dictionary: bonds.merge(d.bonds.duplicate(true), true)
	grudges = d.get("grudges", {}).duplicate() if d.get("grudges") is Dictionary else {}
	bounties = d.get("bounties", []).duplicate(true) if d.get("bounties") is Array else []
	mortal = d.get("mortal", {}).duplicate(true) if d.get("mortal") is Dictionary else {}
	fortune = d.get("fortune", {}).duplicate() if d.get("fortune") is Dictionary else {}
	deeds = d.get("deeds", {}).duplicate() if d.get("deeds") is Dictionary else {}
	ledger = d.get("ledger", []).duplicate(true) if d.get("ledger") is Array else []
