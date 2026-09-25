class_name RelationsAuthority
extends Authority
## S49 · Karma, bonds and the living world, per character: the karma ledger (merit, sin, named debts), the
## righteous-demonic alignment, personal Fame, NPC affinity and gifts, formal bonds, grudges and bounties.
## Deeds come from karma.json: an effect, a call or a matching event gives merit, sin, alignment or Fame.

const LEDGER_KEEP := 12

var debt_clock := 0.0
var challenges: Dictionary = {}   # actor -> {enemy, level, room}: a young master waiting for an answer (not saved)

func intents() -> Array:
	return ["answer_challenge", "give_gift", "offer_bond", "companion_duel"]

func subscribe() -> void:
	# Every event a deed listens for (karma.json); the ledger answers before the default subscribers.
	var events := {}
	for dd in ContentDB.all("karma"): events[str(dd.get("event", ""))] = true
	for ev in events:
		if str(ev) != "": GameEvents.subscribe(str(ev), _on_deed_event.bind(str(ev)), 85)
	GameEvents.subscribe("room_entered", _on_room_entered, 86)
	GameEvents.subscribe("quest_completed", _on_quest_completed, 86)
	GameEvents.subscribe("spar_ended", _on_spar_ended, 86)

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
		"give_gift": return give_gift(c, str(intent.get("npc", "")), int(intent.get("index", -1)))
		"offer_bond": return offer_bond(c, str(intent.get("kind", "")), str(intent.get("npc", "")))
		"companion_duel":
			var cid := str(intent.get("companion", ""))
			if not (c.companions.get("roster", []) as Array).has(cid): return fail("not_companion")
			if hearts(c, cid) < int(acfg().get("duel_hearts", 3)): return fail("hearts", {"text": Tx.t("sim.relations.duel_hearts") % int(acfg().get("duel_hearts", 3))})
			return game.quest.start_spar(c, "duel_" + cid, ProgressionRules.level(c))
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

# ------------------------------------------------------------------ affinity and gifts (S49 v1.0)
func acfg() -> Dictionary:
	return ContentDB.config("bonds").get("affinity", {})

## The id hearts are kept under (one person may have two NPC rows).
func aff_id(npc: String) -> String:
	var n := ContentDB.entry("npcs", npc)
	if not n.is_empty(): return str(n.get("affinity", npc))
	return npc

func has_affinity(npc: String) -> bool:
	return not ContentDB.entry("npcs", npc).get("gifts", {}).is_empty() or ContentDB.has_entry("companions", npc)

func points(c, npc: String) -> int:
	return int(c.relations.affinity.get(aff_id(npc), {}).get("points", 0))

func hearts(c, npc: String) -> int:
	return c.relations.hearts_of(npc)

## Gifts a person loves and likes (companions carry theirs on their NPC row).
func gifts_of(npc: String) -> Dictionary:
	var n := ContentDB.entry("npcs", npc)
	if n.is_empty() or n.get("gifts", {}).is_empty():
		for row in ContentDB.all("npcs"):
			if str(row.get("affinity", row.id)) == aff_id(npc) and not row.get("gifts", {}).is_empty(): return row.gifts
	return n.get("gifts", {})

func _npc_row(npc: String) -> Dictionary:
	var id := aff_id(npc)
	var n := ContentDB.entry("npcs", id)
	return n if not n.is_empty() else ContentDB.entry("npcs", npc)

## Affinity changes: hearts crossed pay their one-time reward (a recipe, a keepsake).
func apply_affinity(actor_id: String, npc: String, delta: int, reason: String) -> void:
	var c = game.character(actor_id)
	if c == null or delta == 0 or not has_affinity(npc): return
	var id := aff_id(npc)
	var a: Dictionary = c.relations.affinity.get(id, {})
	var before := hearts(c, id)
	if not game.account.codex.has("affinity"): game.quest.apply_codex("affinity")
	var cap := int(acfg().get("max_hearts", 5)) * int(acfg().get("per_heart", 100))
	a["points"] = clampi(int(a.get("points", 0)) + delta, 0, cap)
	c.relations.affinity[id] = a
	var after := hearts(c, id)
	for h in range(before + 1, after + 1):
		var fx: Array = _npc_row(id).get("heart_rewards", {}).get(str(h), [])
		if not fx.is_empty() and not (a.get("paid", []) as Array).has(h):
			var paid: Array = a.get("paid", [])
			paid.append(h)
			a["paid"] = paid
			game.apply_effects(c.id, fx, "hearts:" + id)
	emit("affinity_changed", {"actor": c.id, "npc": id, "value": int(a.points), "hearts": after, "delta": delta, "reason": reason,
		"heart_up": after > before})

## One gift per person a day. Loved is a heart; liked less; anything else a courtesy.
func give_gift(c, npc: String, index: int) -> Dictionary:
	if gifts_of(npc).is_empty(): return fail("no_gifts", {"text": Tx.t("sim.relations.no_gifts")})
	var id := aff_id(npc)
	var day := Clock.reset_day(Clock.now_utc())
	var a: Dictionary = c.relations.affinity.get(id, {})
	if int(a.get("gift_day", -1)) == day: return fail("gifted_today", {"text": Tx.t("sim.relations.gifted_today")})
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("no_item")
	var item_id := str(c.inventory.bag[index].id)
	if not giftable(c.inventory.bag[index]): return fail("not_giftable", {"text": Tx.t("sim.relations.not_giftable")})
	var g := gifts_of(npc)
	var reaction := "loved" if (g.get("loved", []) as Array).has(item_id) else ("liked" if (g.get("liked", []) as Array).has(item_id) else "other")
	game.inventory.apply_remove_index(c.id, index, 1, "gift:" + id)
	a = c.relations.affinity.get(id, {})
	a["gift_day"] = day
	var known: Dictionary = a.get("known", {})
	if reaction != "other": known[item_id] = reaction
	a["known"] = known
	c.relations.affinity[id] = a
	apply_affinity(c.id, id, int(acfg().get(reaction, 15)), "gift:" + reaction)
	return ok({"reaction": reaction, "item": item_id, "hearts": hearts(c, id)})

## Key items, tools, bound relics and gear stay with you; anything else can be given.
static func giftable(slot: Dictionary) -> bool:
	var id := str(slot.get("id", ""))
	return not (str(ContentDB.item(id).get("type", "")) in ["key", "tool", "currency_item", "vessel"]) and not slot.get("bound", false) \
		and not ContentDB.is_equipment(id)

## Quests make friends: the giver likes you a little more for each one done.
func _on_quest_completed(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null: return
	var def := ContentDB.entry("quests", str(p.get("quest", "")))
	var giver := str(def.get("giver", ""))
	if giver != "" and not gifts_of(giver).is_empty(): apply_affinity(c.id, giver, int(acfg().get("quest", 30)), "quest")
	# S49 master: passing the personal-disciple trial makes the elder your master.
	var m := ContentDB.entry("bonds", "master")
	if str(p.get("quest", "")) == str(m.get("formed_by", "")) and str(c.relations.bonds.get("master", "")) == "":
		var sect := str(c.training_sect.get("id", "jade_sect"))
		var who := str(m.get("mentors", {}).get(sect, "elder_hu"))
		c.relations.bonds["master"] = who
		emit("bond_formed", {"actor": c.id, "kind": "master", "npc": who})

## A friendly duel won against a companion (once a day counts).
func _on_spar_ended(p: Dictionary) -> void:
	var opp := str(p.get("opponent", ""))
	if not opp.begins_with("duel_") or str(p.get("winner", "")) != "player": return
	var c = game.character(str(p.get("actor", game.active_id)))
	if c == null: return
	var cid := opp.trim_prefix("duel_")
	var day := Clock.reset_day(Clock.now_utc())
	var a: Dictionary = c.relations.affinity.get(cid, {})
	if int(a.get("duel_day", -1)) == day: return
	a["duel_day"] = day
	c.relations.affinity[cid] = a
	apply_affinity(c.id, cid, int(acfg().get("duel", 20)), "duel")

## The shop discount a keeper's hearts give (3 hearts 5%, 5 hearts 10%).
func shop_discount(c, shop_id: String) -> float:
	var best := 0.0
	for n in ContentDB.all("npcs"):
		if not (n.get("services", []) as Array).has("shop:" + shop_id) or n.get("gifts", {}).is_empty(): continue
		var h := hearts(c, str(n.id))
		for step in acfg().get("discount", []):
			if h >= int(step[0]): best = maxf(best, float(step[1]))
	return best

# ------------------------------------------------------------------ bonds
## Dao Companion (5 hearts, one) or sworn sibling (4 hearts, up to three), from the companions who travel with you.
func offer_bond(c, kind: String, npc: String) -> Dictionary:
	var b := ContentDB.entry("bonds", kind)
	if b.is_empty() or str(b.get("from", "")) != "companions": return fail("unknown_bond")
	if not (c.companions.get("roster", []) as Array).has(npc): return fail("not_companion", {"text": Tx.t("sim.relations.not_companion")})
	var need := int(b.get("hearts", 5))
	if hearts(c, npc) < need: return fail("hearts", {"text": Tx.t("sim.relations.bond_hearts") % need})
	var r: RelationsState = c.relations
	if kind == "dao_companion":
		if str(r.bonds.get("dao_companion", "")) != "": return fail("taken", {"text": Tx.t("sim.relations.dao_taken")})
		if (r.bonds.get("sworn", []) as Array).has(npc): return fail("sworn", {"text": Tx.t("sim.relations.already_sworn")})
		r.bonds["dao_companion"] = npc
	else:
		var sworn: Array = r.bonds.get("sworn", [])
		if sworn.has(npc) or str(r.bonds.get("dao_companion", "")) == npc: return fail("already", {"text": Tx.t("sim.relations.already_sworn")})
		if sworn.size() >= int(b.get("max", 3)): return fail("full", {"text": Tx.t("sim.relations.sworn_full") % int(b.get("max", 3))})
		sworn.append(npc)
		r.bonds["sworn"] = sworn
		if str(b.get("title", "")) != "": game.achievements.apply_title(c.id, str(b.title))
	game.combat.refresh_stats(c.id)
	emit("bond_formed", {"actor": c.id, "kind": kind, "npc": npc})
	return ok({"kind": kind, "npc": npc})

## Is the Dao Companion fighting beside you (in the party, not downed)?
func dao_in_party(c) -> bool:
	var dc := str(c.relations.bonds.get("dao_companion", ""))
	return dc != "" and (c.companions.get("active", []) as Array).has(dc)

## The Dao Companion's support slot: risk steps off a major breakthrough while they are with you.
func bond_support(c) -> int:
	return int(ContentDB.entry("bonds", "dao_companion").get("support_steps", 1)) if dao_in_party(c) else 0

## Shared insight while the Dao Companion is with you.
func insight_share(c) -> float:
	return float(ContentDB.entry("bonds", "dao_companion").get("insight", 0.1)) if dao_in_party(c) else 0.0

## The master's legacy art (The Elder's Last Lesson): an Inner Art only that elder taught.
func apply_master_legacy(actor_id: String) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var who := str(c.relations.bonds.get("master", ""))
	var art := str(ContentDB.entry("bonds", "master").get("legacy", {}).get(who, ""))
	if art != "": game.progression.apply_learn_inner_art(c.id, art)
