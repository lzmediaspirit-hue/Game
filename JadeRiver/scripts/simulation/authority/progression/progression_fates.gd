class_name ProgressionFates
extends ProgressionPart
## ProgressionAuthority's part: the fate cards offered after a major breakthrough, and the fates' lasting gifts and
## costs (S48).

# ------------------------------------------------------------------ breakthrough fates (S48)
## After a major breakthrough: three distinct cards from the deck, drawn on the breakthrough stream.
func offer_fates(c) -> void:
	var pool := ProgressionRules.fate_pool(game.ctx(c))
	var cards := ProgressionRules.draw_fates(pool, int(ContentDB.config("fates").get("offer", 3)), Rng.stream(c.id, "breakthrough"))
	if cards.size() < 2: return
	c.cultivator.fate_offer = cards
	if not game.account.codex.has("fates"): game.quest.apply_codex("fates")
	emit("fate_offered", {"actor": c.id, "cards": cards})

## Choose one of the cards offered: its gift and its cost both apply now; some of either last the realm.
func choose_fate(c, card: String) -> Dictionary:
	var cu: CultivatorState = c.cultivator
	if cu.fate_offer.is_empty(): return fail("no_offer")
	if not card in cu.fate_offer: return fail("not_offered")
	var f := ContentDB.entry("fates", card)
	var rec := {"id": card, "realm": ProgressionRules.great_realm(cu.realm_key)}
	if f.has("next"): rec.next = (f.next as Dictionary).duplicate()
	if "dao_echo" in f.get("flags", []): rec.dao = ProgressionRules.strongest_dao(c)
	cu.fates.append(rec)
	cu.fate_offer = []
	game.apply_effects(c.id, f.get("effects", []), "fate:" + card)
	emit("fate_chosen", {"actor": c.id, "card": card})
	return ok({"card": card})

## A fate given outright (a quest, a relic, a fortune): as if chosen from an offer, without one.
func apply_grant_fate(actor_id: String, card: String) -> void:
	var c = game.character(actor_id)
	if c == null or not ContentDB.has_entry("fates", card): return
	var saved: Array = c.cultivator.fate_offer.duplicate()
	c.cultivator.fate_offer = [card]
	choose_fate(c, card)
	c.cultivator.fate_offer = saved

## The fates still waiting on a `next` (a tribulation's extra bolts, a breakthrough's bonus): spent once, then gone.
## Another authority spends one too (Fox Spirit's Favour: the next egg's purity).
func spend_fate_next(c, key: String) -> float:
	var total := 0.0
	for rec in c.cultivator.fates:
		var nx: Dictionary = rec.get("next", {})
		if nx.has(key):
			total += float(nx[key])
			nx.erase(key)
	return total

## Hungry Dantian: every pill family's lifetime resistance rises by a count.
func apply_pill_resistance_all(actor_id: String, amount: int) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var fams := {}
	for it in ContentDB.all("items"):
		var fam := ProgressionRules.pill_family(it)
		if fam != "": fams[fam] = true
	for fam in fams:
		var pr: Dictionary = c.cultivator.pill_resistance.get(fam, {"count": 0, "doses": 0})
		pr.count = int(pr.get("count", 0)) + amount
		c.cultivator.pill_resistance[fam] = pr
		emit("pill_resistance_changed", {"actor": c.id, "family": fam, "count": int(pr.count), "doses": int(pr.get("doses", 0))})

## Debt of Heaven: purity one grade better (grade 1 is the purest).
func apply_purity_grade(actor_id: String, grades: int) -> void:
	var c = game.character(actor_id)
	if c == null: return
	var before: int = c.cultivator.purity
	c.cultivator.purity = clampi(c.cultivator.purity - grades, 1, 9)
	if c.cultivator.purity != before: emit("purity_changed", {"actor": c.id, "grade": c.cultivator.purity})

## A fate flag held (reveal_hidden, streak_heart_demon, dao_echo).
func fate_flag(c, flag: String) -> bool:
	for rec in c.cultivator.fates:
		if flag in ContentDB.entry("fates", str(rec.get("id", ""))).get("flags", []): return true
	return false
