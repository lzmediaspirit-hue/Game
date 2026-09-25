class_name RelationsAuthority
extends Authority
## S49 · Karma, bonds and the living world, per character: the karma ledger (merit, sin, named debts), the
## righteous-demonic alignment, personal Fame, NPC affinity and gifts, formal bonds, grudges and bounties.
## Deeds come from karma.json: an effect, a call or a matching event gives merit, sin, alignment or Fame.

const LEDGER_KEEP := 12

var debt_clock := 0.0
var challenges: Dictionary = {}   # actor -> {enemy, level, room}: a young master waiting for an answer (not saved)

func intents() -> Array:
	return ["answer_challenge"]

func subscribe() -> void:
	# Every event a deed listens for (karma.json); the ledger answers before the default subscribers.
	var events := {}
	for dd in ContentDB.all("karma"): events[str(dd.get("event", ""))] = true
	for ev in events:
		if str(ev) != "": GameEvents.subscribe(str(ev), _on_deed_event.bind(str(ev)), 85)
	GameEvents.subscribe("room_entered", _on_room_entered, 86)

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"answer_challenge":
			var ch: Dictionary = challenges.get(c.id, {})
			if ch.is_empty() or game.room_rt == null or str(ch.room) != game.room_rt.room_id: return fail("no_challenge", {"text": Tx.t("sim.relations.no_challenge")})
			challenges.erase(c.id)
			if not bool(intent.get("accept", false)):
				apply_deed(c.id, str(cfg().get("young_master", {}).get("decline_deed", "challenge_declined")))
				return ok({"declined": true})
			var sp: Dictionary = game.quest.start_spar(c, str(ch.enemy), int(ch.level))
			return sp if not sp.get("ok", false) else ok({"spar": str(ch.enemy)})
	return fail("unknown_intent")

func cfg() -> Dictionary:
	return ContentDB.config("karma")

# ------------------------------------------------------------------ karma ledger
## Merit and sin (G1, S49). Sin also feeds the heart demon (S48).
func apply_karma(actor_id: String, merit: int, sin: int, reason: String) -> void:
	var c = game.character(actor_id)
	if c == null or (merit == 0 and sin == 0): return
	var r: RelationsState = c.relations
	r.merit = maxi(0, r.merit + merit)
	r.sin = maxi(0, r.sin + sin)
	r.ledger.push_front({"reason": reason, "merit": merit, "sin": sin, "utc": Clock.now_utc()})
	if r.ledger.size() > LEDGER_KEEP: r.ledger.resize(LEDGER_KEEP)
	if not game.account.codex.has("karma"): game.quest.apply_codex("karma")
	if sin > 0: game.progression.apply_heart_demon(c.id, sin * float(ContentDB.stat_const("heart_demon", {}).get("per_sin", 0.1)), "sin")
	if merit != 0: emit("merit_changed", {"actor": c.id, "value": r.merit, "delta": merit, "reason": reason})
	if sin != 0: emit("sin_changed", {"actor": c.id, "value": r.sin, "delta": sin, "reason": reason})

## A named debt: a deed the world remembers. When it falls due its mail arrives (the saved repay you).
func apply_karma_debt(actor_id: String, debt_id: String, due_h: float, mail: String, attachments: Array) -> void:
	var c = game.character(actor_id)
	if c == null or c.relations.debts.has(debt_id): return
	c.relations.debts[debt_id] = {"due_utc": Clock.now_utc() + due_h * 3600.0, "mail": mail, "attachments": attachments.duplicate(true), "paid": false}
	emit("debt_recorded", {"actor": c.id, "debt": debt_id})

func settle_debts(c) -> void:
	for id in c.relations.debts:
		var d: Dictionary = c.relations.debts[id]
		if d.get("paid", false) or Clock.now_utc() < float(d.get("due_utc", 0.0)): continue
		d.paid = true
		if str(d.get("mail", "")) != "": game.mail.apply_send(c.id, str(d.mail), d.get("attachments", []), {})
		emit("debt_called", {"actor": c.id, "debt": id})

## The breakthrough that merit eased this great realm (once per great realm).
func apply_merit_used(actor_id: String, great_realm: String) -> void:
	var c = game.character(actor_id)
	if c != null: c.relations.merit_used[great_realm] = true

func tick(delta: float) -> void:
	var c = game.active()
	if c == null: return
	debt_clock -= delta
	if debt_clock > 0.0: return
	debt_clock = 1.0
	if not c.relations.debts.is_empty(): settle_debts(c)

# ------------------------------------------------------------------ alignment and Fame
## The righteous-demonic axis (-100 ... +100). It gates some masters, shops and methods, never core realm progress.
func apply_alignment(actor_id: String, delta: int, reason: String) -> void:
	var c = game.character(actor_id)
	if c == null or delta == 0: return
	var before: int = c.relations.alignment
	var word_before := alignment_word(c)
	c.relations.alignment = clampi(before + delta, -100, 100)
	if c.relations.alignment == before: return
	if not game.account.codex.has("alignment"): game.quest.apply_codex("alignment")
	emit("alignment_changed", {"actor": c.id, "value": c.relations.alignment, "delta": c.relations.alignment - before, "reason": reason,
		"word": alignment_word(c), "word_changed": alignment_word(c) != word_before})

## Personal Fame, apart from any faction's reputation: public defeats cost it.
func apply_fame(actor_id: String, delta: int, reason: String) -> void:
	var c = game.character(actor_id)
	if c == null or delta == 0: return
	var tier_before := str(fame_tier(c).get("id", ""))
	var before: int = c.relations.fame
	c.relations.fame = maxi(0, before + delta)
	if c.relations.fame == before: return
	if not game.account.codex.has("fame"): game.quest.apply_codex("fame")
	var tier := str(fame_tier(c).get("id", ""))
	emit("fame_changed", {"actor": c.id, "value": c.relations.fame, "delta": c.relations.fame - before, "reason": reason, "tier": tier,
		"tier_up": tier != tier_before and delta > 0})

## The named Fame tier this character stands at (Unknown, Noted, Rising, Renowned, Legendary).
func fame_tier(c) -> Dictionary:
	var best := {}
	for t in cfg().get("fame_tiers", []):
		if c.relations.fame >= int(t.get("min", 0)): best = t
	return best

## The next tier up, or {} at Legendary.
func next_fame_tier(c) -> Dictionary:
	for t in cfg().get("fame_tiers", []):
		if c.relations.fame < int(t.get("min", 0)): return t
	return {}

## Demonic, shadowed, balanced, upright or righteous.
func alignment_word(c) -> String:
	var v: int = c.relations.alignment
	for w in cfg().get("alignment_words", []):
		if v <= int(w.get("max", 100)): return str(w.id)
	return "balanced"

# ------------------------------------------------------------------ deeds (karma.json)
## One named deed: its merit, sin, alignment and Fame together. Once-only deeds are remembered.
func apply_deed(actor_id: String, deed_id: String, times := 1, once_key := "") -> bool:
	var c = game.character(actor_id)
	var dd := ContentDB.entry("karma", deed_id)
	if c == null or dd.is_empty() or times <= 0: return false
	if dd.get("once", false) or dd.has("once_key"):
		var key := deed_id + (":" + once_key if once_key != "" else "")
		if c.relations.deeds.has(key): return false
		c.relations.deeds[key] = true
	apply_karma(c.id, int(dd.get("merit", 0)) * times, int(dd.get("sin", 0)) * times, deed_id)
	apply_alignment(c.id, int(dd.get("alignment", 0)) * times, deed_id)
	apply_fame(c.id, int(dd.get("fame", 0)) * times, deed_id)
	return true

## A deed fires when its event's payload matches every {key: value} in "match".
func _on_deed_event(p: Dictionary, event_name: String) -> void:
	var c = game.character(str(p.get("actor", p.get("killer", game.active_id))))
	if c == null: c = game.active()
	if c == null: return
	for dd in ContentDB.all("karma"):
		if str(dd.get("event", "")) != event_name: continue
		var matched := true
		for k in dd.get("match", {}):
			if str(p.get(k, "")) != str(dd.match[k]):
				matched = false
				break
		if not matched: continue
		if dd.get("in_town", false) and not _in_town(): continue
		apply_deed(c.id, str(dd.id), int(p.get("count", 1)) if dd.get("per_count", false) else 1,
			str(p.get(str(dd.get("once_key", "")), "")) if dd.has("once_key") else "")

func _in_town() -> bool:
	return game.room_rt != null and str(game.room_rt.def.get("type", "")) == "town"

# ------------------------------------------------------------------ Young Master provocations (Fame)
## From Rising Fame, walking into a town may bring out a young master who wants to prove himself against you
## (once a day). The challenge waits in that room for an answer; leaving the room lets it lapse.
func _on_room_entered(_p: Dictionary) -> void:
	var c = game.active()
	if c == null: return
	challenges.erase(c.id)
	if not _in_town(): return
	var yc: Dictionary = cfg().get("young_master", {})
	if c.relations.fame < int(yc.get("fame", 150)): return
	var day := Clock.reset_day(Clock.now_utc())
	if int(c.cooldowns.get("young_master_day", -1)) == day: return
	if Rng.stream(c.id, "relations").randf() >= float(yc.get("chance", 0.25)): return
	c.cooldowns["young_master_day"] = day
	offer_challenge(c, str(yc.get("enemy", "young_master")))

## A challenger steps up at the character's own level.
func offer_challenge(c, enemy: String) -> void:
	if game.room_rt == null: return
	challenges[c.id] = {"enemy": enemy, "level": ProgressionRules.level(c), "room": game.room_rt.room_id}
	emit("young_master_challenge", {"actor": c.id, "room": game.room_rt.room_id, "enemy": enemy})

func challenge_of(c) -> Dictionary:
	var ch: Dictionary = challenges.get(c.id, {})
	if ch.is_empty() or game.room_rt == null or str(ch.room) != game.room_rt.room_id: return {}
	return ch
