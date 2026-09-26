class_name RelationsAuthority
extends Authority
## S49 · Karma, bonds and the living world, per character: the karma ledger (merit, sin, named debts), the
## righteous-demonic alignment, personal Fame, NPC affinity and gifts, formal bonds, grudges and bounties, and the
## Fortune meter with its encounters (fortune_deck.json).
## Deeds come from karma.json: an effect, a call or a matching event gives merit, sin, alignment or Fame.

const LEDGER_KEEP := 12

var debt_clock := 0.0
var challenges: Dictionary = {}   # actor -> {enemy, level, room}: a young master waiting for an answer (not saved)

func intents() -> Array:
	return ["answer_challenge", "give_gift", "offer_bond", "companion_duel", "pay_grudge", "take_bounty", "judge_foe", "donate_relief", "county_jobs"]

func subscribe() -> void:
	# Every event a deed listens for (karma.json); the ledger answers before the default subscribers.
	var events := {}
	for dd in ContentDB.all("karma"): events[str(dd.get("event", ""))] = true
	for ev in events:
		if str(ev) != "": GameEvents.subscribe(str(ev), _on_deed_event.bind(str(ev)), 85)
	GameEvents.subscribe("room_entered", _on_room_entered, 86)
	GameEvents.subscribe("quest_completed", _on_quest_completed, 86)
	GameEvents.subscribe("spar_ended", _on_spar_ended, 86)
	GameEvents.subscribe("actor_defeated", _on_defeated, 86)
	GameEvents.subscribe("quest_accepted", _on_quest_accepted, 86)
	# S49 fortune encounters and heavenly phenomena (after the room, gathering and fall have settled).
	GameEvents.subscribe("room_entered", _on_fortune_room, 95)
	GameEvents.subscribe("node_gathered", _on_fortune_gathered, 95)
	GameEvents.subscribe("fell_out", _on_fortune_fell, 95)
	GameEvents.subscribe("heavenly_phenomenon", _on_phenomenon, 86)
	GameEvents.subscribe("technique_used", _on_mortal_technique, 86)

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
		"pay_grudge": return pay_grudge(c, str(intent.get("faction", "")), str(intent.get("method", "")))
		"take_bounty": return take_bounty(c, str(intent.get("id", "")))
		"judge_foe": return judge_foe(c, int(intent.get("enemy", 0)), bool(intent.get("spare", true)))
		"donate_relief": return donate_relief(c, str(intent.get("tier", "")))
		"county_jobs": return ok({"jobs": county_jobs(c)})
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
	var merit_before := r.merit
	r.merit = maxi(0, r.merit + merit)
	r.sin = maxi(0, r.sin + sin)
	r.ledger.push_front({"reason": reason, "merit": merit, "sin": sin, "utc": Clock.now_utc()})
	if r.ledger.size() > LEDGER_KEEP: r.ledger.resize(LEDGER_KEEP)
	if not game.account.codex.has("karma"): game.quest.apply_codex("karma")
	if sin > 0: game.progression.apply_heart_demon(c.id, sin * float(ContentDB.stat_const("heart_demon", {}).get("per_sin", 0.1)), "sin")
	if merit != 0: emit("merit_changed", {"actor": c.id, "value": r.merit, "delta": merit, "reason": reason})
	# S48 the Buddhist path: each hundred merit crossed calms the heart of one who holds a vow.
	var bud: Dictionary = ContentDB.stat_const("paths", {}).get("buddhist", {})
	var step := int(bud.get("merit_milestone", 100))
	if merit > 0 and step > 0 and not c.cultivator.vows.is_empty():
		var crossed := int(r.merit / step) - int(merit_before / step)
		if crossed > 0: game.progression.apply_heart_demon(c.id, float(bud.get("milestone_heart_demon", -10)) * crossed, "merit_milestone")
	if sin != 0: emit("sin_changed", {"actor": c.id, "value": r.sin, "delta": sin, "reason": reason})

## A named debt: a deed the world remembers. It falls due after some hours or when a quest is done; then its
## letter arrives, a flag is set, or a hunter waits for you (Part 8: the saved repay you; a victim's kin hunts you).
## A debt named in karma.json's "debts" takes its terms from there.
func apply_karma_debt(actor_id: String, debt_id: String, due_h: float, mail: String, attachments: Array) -> void:
	var c = game.character(actor_id)
	if c == null or c.relations.debts.has(debt_id): return
	var named: Dictionary = cfg().get("debts", {}).get(debt_id, {})
	var d := {"due_utc": Clock.now_utc() + float(named.get("due_h", due_h)) * 3600.0, "mail": str(named.get("mail", mail)),
		"attachments": (named.get("attachments", attachments) as Array).duplicate(true), "paid": false}
	if named.has("due_quest"):
		d.due_quest = str(named.due_quest)
		d.due_utc = 0.0
	if named.has("hunter"): d.hunter = named.hunter.duplicate()
	if named.has("flag"): d.flag = str(named.flag)
	c.relations.debts[debt_id] = d
	emit("debt_recorded", {"actor": c.id, "debt": debt_id})

func _debt_due(c, d: Dictionary) -> bool:
	if d.has("due_quest"): return c.quests.is_done(str(d.due_quest)) or c.quests.is_active(str(d.due_quest)) and bool(d.get("on_accept", false))
	return Clock.now_utc() >= float(d.get("due_utc", 0.0))

func settle_debts(c) -> void:
	for id in c.relations.debts:
		var d: Dictionary = c.relations.debts[id]
		if d.get("paid", false) or not _debt_due(c, d): continue
		d.paid = true
		if str(d.get("mail", "")) != "": game.mail.apply_send(c.id, str(d.mail), d.get("attachments", []), {})
		if str(d.get("flag", "")) != "": game.quest.apply_flag(c.id, str(d.flag))
		if d.has("hunter"): c.relations.hunters.append({"enemy": str(d.hunter.enemy), "room": str(d.hunter.room), "debt": str(id)})
		emit("debt_called", {"actor": c.id, "debt": id})

## The breakthrough that merit eased this great realm (once per great realm).
func apply_merit_used(actor_id: String, great_realm: String) -> void:
	var c = game.character(actor_id)
	if c != null: c.relations.merit_used[great_realm] = true

func tick(delta: float) -> void:
	var c = game.active()
	if c == null: return
	_fill_fortune(c, delta)   # the Fortune meter fills only while you play
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

## A deed that counts only a few times a day (healing an ally: S48 the Buddhist path).
func apply_daily_deed(actor_id: String, deed_id: String, cap: int) -> bool:
	var day := Clock.reset_day(Clock.now_utc())
	var c = game.character(actor_id)
	if c == null: return false
	for n in cap:
		var key := "%s:%d:%d" % [deed_id, day, n]
		if c.relations.deeds.has(key): continue
		c.relations.deeds[key] = true
		# Yesterday's keys are dropped so the ledger does not grow.
		for k in c.relations.deeds.keys():
			if str(k).begins_with(deed_id + ":") and not str(k).begins_with("%s:%d:" % [deed_id, day]): c.relations.deeds.erase(k)
		return apply_deed(actor_id, deed_id)
	return false

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
	_spawn_hunters(c)
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
	_on_faction_quest(c, str(p.get("quest", "")))
	if not c.relations.debts.is_empty(): settle_debts(c)
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
	if str(p.get("winner", "")) == "player":
		var cc = game.character(str(p.get("actor", game.active_id)))
		for f in ContentDB.all("factions"):
			if cc != null and str(f.get("duel", "")) == opp: clear_grudge(cc, str(f.id), "duel")
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
	return maxf(best, county_discount(c, shop_id))   # S49: the county's Benefactor pays less in Stoneford

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

# ------------------------------------------------------------------ grudges, hunters and bounties (S49 v1.0)
func fcfg() -> Dictionary:
	return ContentDB.config("factions")

func grudge(c, faction: String) -> int:
	return int(c.relations.grudges.get(faction, 0))

## A faction's grudge (0-100). Past its threshold its hunters come for you in the field.
func apply_grudge(actor_id: String, faction: String, delta: int, reason: String) -> void:
	var c = game.character(actor_id)
	var f := ContentDB.entry("factions", faction)
	if c == null or f.is_empty() or delta == 0: return
	if c.relations.deeds.has("grudge_cleared:" + faction) and delta > 0: return   # a story grudge settled for good
	var before := grudge(c, faction)
	c.relations.grudges[faction] = clampi(before + delta, 0, 100)
	if c.relations.grudges[faction] == before: return
	if not game.account.codex.has("grudges"): game.quest.apply_codex("grudges")
	emit("grudge_changed", {"actor": c.id, "faction": faction, "value": grudge(c, faction), "delta": grudge(c, faction) - before, "reason": reason,
		"hunted": grudge(c, faction) >= int(f.get("threshold", 30))})

func clear_grudge(c, faction: String, reason: String, forever := false) -> void:
	if forever: c.relations.deeds["grudge_cleared:" + faction] = true
	if grudge(c, faction) > 0: apply_grudge(c.id, faction, -grudge(c, faction), reason)

## Settle a grudge: blood money now, or a duel with the faction's champion (won), or its quest (done).
func pay_grudge(c, faction: String, method: String) -> Dictionary:
	var f := ContentDB.entry("factions", faction)
	if f.is_empty() or grudge(c, faction) <= 0: return fail("no_grudge", {"text": Tx.t("sim.relations.no_grudge")})
	match method:
		"blood_money":
			var bm: Dictionary = f.get("blood_money", {})
			if bm.is_empty(): return fail("no_method", {"text": Tx.t("sim.relations.no_blood_money")})
			if game.economy.balance(str(bm.currency), c) < int(bm.amount): return fail("poor", {"text": Tx.t("sim.relations.cannot_pay") % int(bm.amount)})
			game.economy.apply_currency(str(bm.currency), -int(bm.amount), "blood_money")
			clear_grudge(c, faction, "blood_money")
			return ok({"paid": int(bm.amount)})
		"duel":
			if str(f.get("duel", "")) == "": return fail("no_method")
			return game.quest.start_spar(c, str(f.duel), ProgressionRules.level(c))
	return fail("no_method")

## Named kills raise their faction's grudge; a hunter or bounty target that falls is struck off.
func _on_defeated(p: Dictionary) -> void:
	if str(p.get("victim_kind", "")) != "enemy": return
	var c = game.character(str(p.get("killer", "")))
	if c == null: c = game.active()
	if c == null: return
	var def := ContentDB.entry("enemies", str(p.get("def", "")))
	var faction := str(def.get("faction", ""))
	if faction != "" and def.get("named", false):
		apply_grudge(c.id, faction, int(ContentDB.entry("factions", faction).get("per_named", 15)), "named:" + str(p.def))
	for h in c.relations.hunters.duplicate():
		if str(h.enemy) == str(p.def): c.relations.hunters.erase(h)
	for b in c.relations.bounties.duplicate():
		var bd := _bounty(str(b.get("id", "")))
		if str(bd.get("target", "")) != str(p.def): continue
		c.relations.bounties.erase(b)
		var rw: Dictionary = bd.get("reward", {})
		if not rw.is_empty(): game.economy.apply_currency(str(rw.currency), int(rw.amount), "bounty")
		apply_deed(c.id, "bounty_claimed")
		emit("bounty_claimed", {"actor": c.id, "bounty": str(bd.id), "reward": int(rw.get("amount", 0)), "currency": str(rw.get("currency", ""))})

## Story grudges (Elder Gu's ring) rise with the cargo you uncover and end when the warehouse falls; a faction's
## own quest (Old Scores) settles it too.
func _on_faction_quest(c, qid: String) -> void:
	for f in ContentDB.all("factions"):
		var st: Dictionary = f.get("story", {})
		if st.get("raise", {}).has(qid): apply_grudge(c.id, str(f.id), int(st.raise[qid]), "story:" + qid)
		if str(st.get("clear", "")) == qid: clear_grudge(c, str(f.id), "story:" + qid, true)
		if str(f.get("quest", "")) == qid: clear_grudge(c, str(f.id), "quest:" + qid)

func _on_quest_accepted(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c != null and not c.relations.debts.is_empty(): settle_debts(c)

## Hunters: in a faction's hunting grounds, past its threshold, one may be waiting (at your level). Debt hunters
## (Kuai Shan) always wait in their room. Bounty targets appear in theirs while the bounty is yours.
func _spawn_hunters(c) -> void:
	var rt = game.room_rt
	if rt == null: return
	var here: String = rt.room_id
	var st: ActorState = game.actor_state(c.id)
	var at: Vector2 = (st.plane if st else Vector2(c.position.x, c.position.y))
	var spot := Vector2(clampf(at.x + 420.0, 120.0, rt.width() - 120.0), at.y)
	for h in c.relations.hunters:
		if str(h.room) == here and not _present(str(h.enemy)):
			var e: EnemyState = game.enemies.spawn_at(str(h.enemy), spot, ProgressionRules.level(c), {"elite": true})
			if e: emit("hunter_dispatched", {"actor": c.id, "faction": str(e.def.get("faction", "")), "room": here, "enemy": str(h.enemy), "debt": str(h.get("debt", ""))})
	for b in c.relations.bounties:
		var bd := _bounty(str(b.get("id", "")))
		if str(bd.get("room", "")) == here and not _present(str(bd.target)):
			game.enemies.spawn_at(str(bd.target), spot + Vector2(160, 0), int(ContentDB.entry("enemies", str(bd.target)).get("level", [20])[0]), {"elite": true})
	var hunt: Dictionary = fcfg().get("hunt", {})
	for f in ContentDB.all("factions"):
		if grudge(c, str(f.id)) < int(f.get("threshold", 30)) or not (f.get("hunt_rooms", []) as Array).has(here): continue
		if float(c.cooldowns.get("hunt_" + str(f.id), 0.0)) > Clock.now_utc(): continue
		if Rng.stream(c.id, "relations").randf() >= float(hunt.get("chance", 0.35)): continue
		c.cooldowns["hunt_" + str(f.id)] = Clock.now_utc() + float(hunt.get("cooldown_s", 1800))
		var he: EnemyState = game.enemies.spawn_at(str(f.hunter), spot, ProgressionRules.level(c), {"elite": true})
		if he: emit("hunter_dispatched", {"actor": c.id, "faction": str(f.id), "room": here, "enemy": str(f.hunter), "debt": ""})

func _present(def_id: String) -> bool:
	for e in game.room_rt.living_enemies():
		if e.def_id == def_id: return true
	return false

func _bounty(id: String) -> Dictionary:
	for b in fcfg().get("bounties", []):
		if str(b.id) == id: return b
	return {}

## The town board's bounties: take up to two at a time; each once a day.
func take_bounty(c, id: String) -> Dictionary:
	var b := _bounty(id)
	if b.is_empty(): return fail("unknown_bounty")
	if not ProgressionRules.at_least(c.cultivator.realm_key, str(b.get("realm", "mortal_1"))):
		return fail("realm", {"text": Tx.t("req.reach") % ContentDB.name_of("realms", str(b.realm))})
	for have in c.relations.bounties:
		if str(have.get("id", "")) == id: return fail("taken", {"text": Tx.t("sim.relations.bounty_taken")})
	if c.relations.bounties.size() >= int(fcfg().get("max_bounties", 2)): return fail("full", {"text": Tx.t("sim.relations.bounties_full")})
	var day := Clock.reset_day(Clock.now_utc())
	if int(c.cooldowns.get("bounty_" + id, -1)) == day: return fail("today", {"text": Tx.t("sim.relations.bounty_today")})
	c.cooldowns["bounty_" + id] = day
	c.relations.bounties.append({"id": id, "taken_utc": Clock.now_utc()})
	emit("bounty_taken", {"actor": c.id, "bounty": id, "room": str(b.room)})
	return ok({"bounty": id})

# ------------------------------------------------------------------ mercy (Part 8 spare / kill)
## A named foe yields: they kneel, and the victor decides.
func apply_surrender(c, e: EnemyState) -> void:
	e.ai["surrendered"] = true
	e.ai["judge"] = c.id
	e.velocity = Vector2.ZERO
	emit("foe_surrendered", {"actor": c.id, "enemy": e.uid, "def": e.def_id})

## Spare them (merit; some remember it) or finish them (sin; some have kin).
func judge_foe(c, uid: int, spare: bool) -> Dictionary:
	if game.room_rt == null: return fail("no_room")
	var e: EnemyState = game.room_rt.enemies.get(uid)
	if e == null or not e.alive or not e.ai.get("surrendered", false): return fail("no_foe", {"text": Tx.t("sim.relations.no_foe")})
	e.ai.erase("surrendered")
	if spare:
		apply_deed(c.id, "spared_foe")
		if str(e.def.get("spare_debt", "")) != "": apply_karma_debt(c.id, str(e.def.spare_debt), 0.0, "", [])
		game.enemies.release(e)
		emit("foe_judged", {"actor": c.id, "def": e.def_id, "spared": true})
		return ok({"spared": true})
	apply_deed(c.id, "killed_yielded")
	if str(e.def.get("kill_debt", "")) != "": apply_karma_debt(c.id, str(e.def.kill_debt), 0.0, "", [])
	game.combat.apply_execute(e, c.id)
	emit("foe_judged", {"actor": c.id, "def": e.def_id, "spared": false})
	return ok({"spared": false})

# ------------------------------------------------------------------ fortune encounters (S49 v1.0)
## A deck of rare vignettes (fortune_deck.json). Entering a room, gathering or a fall recovered from may turn one up,
## but only while the Fortune meter is full; it fills over three hours of play and holds one, so they cannot be farmed.
## Fortune raises the chance and the weights; merit favours kind cards. The draw uses the character's fortune stream.
func fortune_cfg() -> Dictionary:
	return ContentDB.config("fortune_deck")

func fortune_meter(c) -> float:
	return float(c.relations.fortune.get("meter", 0.0))

func _fill_fortune(c, delta: float) -> void:
	var m := fortune_meter(c)
	if m < 1.0: c.relations.fortune["meter"] = minf(1.0, m + delta / (float(fortune_cfg().get("meter_h", 3.0)) * 3600.0))

## Seconds of play until the meter is full again.
func fortune_ready_in(c) -> float:
	return (1.0 - fortune_meter(c)) * float(fortune_cfg().get("meter_h", 3.0)) * 3600.0

## The cards this moment could turn up, with their weights.
func fortune_cards(c, trigger: String) -> Array:
	var fc := fortune_cfg()
	var fortune: float = c.stats.value("fortune")
	var seen: Dictionary = c.relations.fortune.get("seen", {})
	var out: Array = []
	for card in ContentDB.all("fortune_deck"):
		if not trigger in card.get("triggers", []): continue
		if card.get("once", false) and seen.has(str(card.id)): continue
		if card.has("requires") and not RequirementRules.passes(card.requires, game.ctx(c)): continue
		var w: float = float(card.get("weight", 1)) * (1.0 + float(fc.get("fortune_weight", 0.03)) * fortune)
		w += float(card.get("merit_weight", 0)) * floorf(float(c.relations.merit) / float(fc.get("merit_per", 100)))
		if w > 0.0: out.append({"card": card, "w": w})
	return out

## A moment that may become a fortune encounter. `forced` names a card (debug tools and tests); it skips the meter
## and the chance, never the rules of where a card can come.
func fortune_check(c, trigger: String, forced := "") -> Dictionary:
	if c == null or game.room_rt == null: return {}
	var fc := fortune_cfg()
	var rt = game.room_rt
	if str(rt.def.get("type", "")) in fc.get("never_in", []) or rt.event.get("active", false): return {}
	if forced == "" and fortune_meter(c) < 1.0: return {}
	var rng := Rng.stream(c.id, "fortune")
	var cards := fortune_cards(c, trigger)
	if forced != "":
		cards = cards.filter(func(o): return str(o.card.id) == forced)
	elif rng.randf() >= float(fc.get("chance", {}).get(trigger, 0.0)) * (1.0 + float(fc.get("fortune_chance", 0.02)) * c.stats.value("fortune")):
		return {}
	if cards.is_empty(): return {}
	var total := 0.0
	for o in cards: total += float(o.w)
	var roll := rng.randf() * total
	var card: Dictionary = cards.back().card
	for o in cards:
		roll -= float(o.w)
		if roll < 0.0:
			card = o.card
			break
	c.relations.fortune["meter"] = maxf(0.0, fortune_meter(c) - 1.0)
	var seen: Dictionary = c.relations.fortune.get("seen", {})
	seen[str(card.id)] = int(seen.get(str(card.id), 0)) + 1
	c.relations.fortune["seen"] = seen
	emit("fortune_encounter", {"actor": c.id, "card": str(card.id), "trigger": trigger, "room": rt.room_id})
	game.apply_effects(c.id, card.get("effects", []), "fortune:" + str(card.id))
	return card

func _on_fortune_room(_p: Dictionary) -> void:
	fortune_check(game.active(), "room_entered")

func _on_fortune_gathered(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c != null and c.id == game.active_id: fortune_check(c, "node_gathered")

func _on_fortune_fell(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or c.id != game.active_id: return
	fortune_check(c, "fell_out")

## The Hidden Cave card: the fall ends in a cave no map shows. The way up leaves you where you fell.
func apply_fortune_grotto(actor_id: String) -> void:
	var c = game.character(actor_id)
	var st: ActorState = game.actor_state(actor_id)
	if c == null or game.room_rt == null or st == null: return
	c.cooldowns["grotto_return"] = {"room": game.room_rt.room_id, "x": st.plane.x, "y": st.plane.y}
	c.relations.fortune["grotto_n"] = int(c.relations.fortune.get("grotto_n", 0)) + 1
	game.world.load_room(c, "hg_hidden_grotto", "")

## The hermit's chess problem: insight into the Dao you know best (Progression works it out).
func apply_insight_best(actor_id: String, amount: float) -> void:
	game.progression.apply_insight_best(actor_id, amount, "fortune")

# ------------------------------------------------------------------ heavenly phenomena (S49 v1.0)
## The sky answered your breakthrough where people could see it: sometimes a jealous senior cannot let it pass.
func _on_phenomenon(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or c.id != game.active_id or str(p.get("kind", "")) != "cloud" or game.room_rt == null: return
	if int(p.get("people", 0)) <= 0 or challenges.has(c.id) or game.room_rt.event.get("active", false): return
	if str(game.room_rt.def.get("type", "")) in fortune_cfg().get("never_in", []): return
	var jc: Dictionary = cfg().get("jealous", {})
	if Rng.stream(c.id, "fortune").randf() >= float(jc.get("chance", 0.35)): return
	offer_challenge(c, str(jc.get("enemy", "jealous_senior")))

# ------------------------------------------------------------------ the mortal kingdom (S49 v1.1)
## The county magistrate at Stoneford posts three jobs a day for ordinary people; a relief fund takes silver for the
## county's poor. Both earn county favour (named tiers, the county's titles, and at the top a discount in Stoneford's
## shops). Showing a cultivator's power in a mortal town (a technique in Lotus Ferry's village or Greyreed Hamlet)
## costs sin. State: relations.mortal {favour, day, jobs, donated: {tier: day}, warned_s}.
func mcfg() -> Dictionary:
	return cfg().get("mortal", {})

func favour(c) -> int:
	return int(c.relations.mortal.get("favour", 0))

func favour_tier(c) -> Dictionary:
	var best := {}
	for t in mcfg().get("favour_tiers", []):
		if favour(c) >= int(t.get("min", 0)): best = t
	return best

func next_favour_tier(c) -> Dictionary:
	for t in mcfg().get("favour_tiers", []):
		if favour(c) < int(t.get("min", 0)): return t
	return {}

func apply_favour(actor_id: String, delta: int, reason: String) -> void:
	var c = game.character(actor_id)
	if c == null or delta == 0: return
	var before := str(favour_tier(c).get("id", ""))
	c.relations.mortal["favour"] = maxi(0, favour(c) + delta)
	var after := favour_tier(c)
	var up: bool = delta > 0 and str(after.get("id", "")) != before
	if up and str(after.get("title", "")) != "": game.apply_effects(c.id, [{"kind": "grant_title", "title": str(after.title)}], "county")
	emit("favour_changed", {"actor": c.id, "value": favour(c), "delta": delta, "tier": str(after.get("id", "")), "tier_up": up, "reason": reason})

## The county's discount in Stoneford's shops, from the top favour tier.
func county_discount(c, shop_id: String) -> float:
	if not (mcfg().get("discount_shops", []) as Array).has(shop_id): return 0.0
	return float(favour_tier(c).get("discount", 0.0))

## Today's county jobs: three, drawn for this character and day from the ones that suit its Level, accepted as soon as
## the magistrate's board is read. Yesterday's unfinished ones are taken down.
func county_jobs(c) -> Array:
	var m: Dictionary = c.relations.mortal
	var day := Clock.reset_day(Clock.now_utc())
	if int(m.get("day", -1)) == day: return m.get("jobs", [])
	for qid in m.get("jobs", []):
		c.quests.active.erase(qid)
		c.quests.tracked.erase(qid)
		c.quests.daily.erase(qid)
	m["day"] = day
	var made: Array = []
	var rng := Rng.keyed(int(c.rng_seed), "county:%d" % day)
	var lv := ProgressionRules.level(c)
	var jobs: Array = (mcfg().get("jobs", []) as Array).duplicate()
	for i in range(jobs.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = jobs[i]
		jobs[i] = jobs[j]
		jobs[j] = tmp
	var rw: Dictionary = mcfg().get("reward", {})
	for job in jobs:
		if made.size() >= int(mcfg().get("per_day", 3)): break
		var fit: Array = (job.get("options", []) as Array).filter(func(op): return lv >= int(op.get("min_level", 0)) and lv <= int(op.get("max_level", 999)))
		if fit.is_empty(): continue
		var op: Dictionary = fit[rng.randi_range(0, fit.size() - 1)]
		var id := "mortal_%d_%d" % [day, made.size()]
		c.quests.daily[id] = {"id": id, "name": str(op.name), "kind": "mortal", "objectives": [(op.objective as Dictionary).duplicate(true)],
			"hand_in": "", "auto_complete": true, "qp": "daily",
			"rewards": [{"kind": "grant_currency", "currency": "silver_tael", "amount": int(rw.get("silver_base", 20)) + lv * int(rw.get("silver_per_level", 4))},
				{"kind": "deed", "deed": str(rw.get("deed", "county_service"))}, {"kind": "county_favour", "amount": int(rw.get("favour", 10))}]}
		made.append(id)
	m["jobs"] = made
	for qid in made: game.quest.accept(c, qid)
	return made

## The relief fund: silver for the county's poor, once a day at each size; merit and favour in return.
func donate_relief(c, tier: String) -> Dictionary:
	var d: Dictionary = {}
	for row in mcfg().get("donations", []):
		if str(row.id) == tier: d = row
	if d.is_empty(): return fail("no_tier")
	var day := Clock.reset_day(Clock.now_utc())
	var given: Dictionary = c.relations.mortal.get("donated", {})
	if int(given.get(tier, -1)) == day: return fail("today", {"text": Tx.t("sim.relations.relief_today")})
	if game.economy.balance("silver_tael") < int(d.silver): return fail("silver", {"text": Tx.t("sim.relations.relief_silver") % int(d.silver)})
	game.economy.apply_currency("silver_tael", -int(d.silver), "relief")
	given[tier] = day
	c.relations.mortal["donated"] = given
	apply_deed(c.id, str(d.get("deed", "relief_small")))
	apply_favour(c.id, int(d.get("favour", 0)), "relief")
	emit("relief_donated", {"actor": c.id, "tier": tier, "silver": int(d.silver)})
	return ok({"tier": tier})

## Non-interference: a technique used in a mortal town by a cultivator from Qi Kindling up is sin (once a minute at most).
func _on_mortal_technique(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or game.room_rt == null: return
	var rule: Dictionary = mcfg().get("interference", {})
	var def: Dictionary = game.room_rt.def
	if not (rule.get("regions", []) as Array).has(str(def.get("region", ""))) or not (rule.get("room_types", []) as Array).has(str(def.get("type", ""))): return
	if not ProgressionRules.at_least(c.cultivator.realm_key, str(rule.get("realm", "qi_kindling_1"))): return
	if game.sim_time < float(c.relations.mortal.get("warned_s", -INF)) + float(rule.get("cooldown_s", 60)): return
	c.relations.mortal["warned_s"] = game.sim_time
	apply_deed(c.id, str(rule.get("deed", "mortal_interference")))
