class_name CraftingGuilds
extends CraftingPart
## CraftingAuthority's part: the profession guilds (S44, S49): their ranks and timed exams, and the daily commissions
## on each guild's board.

# ------------------------------------------------------------------ S44/S49 the guilds
## The three profession associations (guilds.json): the Alchemist Guild (S44), the Forge Guild and the Formation Guild
## (S49). Each keys its exams, commissions and shop by the craft it certifies.
func guild_def(craft: String) -> Dictionary:
	for g in ContentDB.all("guilds"):
		if str(g.get("craft", "")) == craft: return g
	return {}

## The guilds whose gate this character has opened, in data order.
func guilds_open(c) -> Array:
	var out: Array = []
	for g in ContentDB.all("guilds"):
		if Unlocks.is_unlocked(c.id, str(g.get("unlock", ""))): out.append(g)
	return out

## Your rank in a craft's guild: "" (none), then the ranks in order.
func guild_rank(c, craft: String) -> String:
	return str(c.crafting.get("guild", {}).get(craft, ""))

func guild_rank_def(craft: String, rank: String) -> Dictionary:
	for rk in guild_def(craft).get("ranks", []):
		if str(rk.id) == rank: return rk
	return {}

## The next rank to sit for, or {} when there is none left.
func next_guild_rank(c, craft: String) -> Dictionary:
	var ranks: Array = guild_def(craft).get("ranks", [])
	var have := guild_rank(c, craft)
	for i in ranks.size():
		if have == "" and i == 0: return ranks[0]
		if str(ranks[i].id) == have and i + 1 < ranks.size(): return ranks[i + 1]
	return {}

static func quality_rank(q: String) -> int:
	var order := ["flawed", "common", "fine", "superior", "perfect", "pill_grain", "pill_halo", "pill_soul"]
	return order.find(q)

## Why a rank's exam cannot be sat here and now ("" when it can): its realm, then its hall. The Master exams are sat
## at Cloudgate Port.
func exam_block(c, rk: Dictionary) -> String:
	if rk.has("requires") and not RequirementRules.passes(rk.requires, game.ctx(c)): return RequirementRules.first_failure_text(rk.requires, game.ctx(c))
	var hall := str(rk.get("hall", ""))
	if hall != "" and (game.room_rt == null or game.room_rt.room_id != hall): return Tx.t("sim.crafting.exam_hall") % ContentDB.name_of("rooms", hall)
	return ""

## Whether a finished craft counts toward a rank's exam: its own recipe, or (the Forge Guild) any recipe of at least
## the rank's grade whose piece fits the rank's slot.
static func exam_counts(rk: Dictionary, recipe_id: String) -> bool:
	if rk.has("recipe"): return recipe_id == str(rk.recipe)
	var r := ContentDB.entry("recipes", recipe_id)
	if r.is_empty() or StatRules.grade_index(str(r.get("grade", "plain"))) < StatRules.grade_index(str(rk.get("grade", "plain"))): return false
	var slot := str(rk.get("slot", ""))
	return slot == "" or str(ContentDB.item(str(r.outputs[0].item)).get("slot", "")) == slot

func take_exam(c, craft: String, rank: String) -> Dictionary:
	var g := guild_def(craft)
	var gate := str(g.get("unlock", "alchemist_guild"))
	if g.is_empty() or not Unlocks.is_unlocked(c.id, gate): return fail("locked", {"text": Unlocks.locked_text(gate)})
	var nxt := next_guild_rank(c, craft)
	if nxt.is_empty() or (rank != "" and str(nxt.id) != rank): return fail("rank", {"text": Tx.t("sim.crafting.exam_not_yours")})
	var why := exam_block(c, nxt)
	if why != "": return fail("not_here", {"text": why})
	if not c.crafting.get("guild_exam", {}).is_empty(): return fail("busy", {"text": Tx.t("sim.crafting.exam_running")})
	c.crafting["guild_exam"] = {"craft": craft, "rank": str(nxt.id), "started": game.sim_time, "made": 0}
	emit("guild_exam_started", {"actor": c.id, "craft": craft, "rank": str(nxt.id), "time_s": float(nxt.time_s)})
	return ok({"rank": str(nxt.id), "time_s": float(nxt.time_s)})

## Seconds left on the exam's candle (0 when none is burning).
func exam_left(c) -> float:
	var ex: Dictionary = c.crafting.get("guild_exam", {})
	if ex.is_empty(): return 0.0
	var rk := guild_rank_def(str(ex.craft), str(ex.rank))
	return maxf(0.0, float(rk.get("time_s", 0)) - (game.sim_time - float(ex.started)))

## A furnace, anvil or etching that finishes while the candle burns counts (the auto-refine queue never does).
func on_craft_completed(p: Dictionary) -> void:
	var c = game.character(str(p.get("actor", "")))
	if c == null or p.get("auto", false): return
	var ex: Dictionary = c.crafting.get("guild_exam", {})
	if ex.is_empty() or str(p.get("craft", "")) != str(ex.craft): return
	var rk := guild_rank_def(str(ex.craft), str(ex.rank))
	if not exam_counts(rk, str(p.get("recipe", ""))) or exam_left(c) <= 0.0: return
	if quality_rank(str(p.get("quality", ""))) < quality_rank(str(rk.get("quality", "common"))): return
	ex.made = int(ex.made) + int(p.get("count", 1))
	if int(ex.made) >= int(rk.get("count", 1)): _pass_exam(c, str(ex.craft), rk)

func _pass_exam(c, craft: String, rk: Dictionary) -> void:
	var guild: Dictionary = c.crafting.get("guild", {})
	guild[craft] = str(rk.id)
	c.crafting["guild"] = guild
	c.crafting["guild_exam"] = {}
	game.quest.apply_flag(c.id, str(rk.get("flag", "")))
	var fx: Array = [{"kind": "grant_title", "title": str(rk.get("title", ""))}]
	fx.append_array(rk.get("rewards", []))
	game.apply_effects(c.id, fx, "guild:" + craft)
	emit("guild_rank_changed", {"actor": c.id, "craft": craft, "rank": str(rk.id), "title": str(rk.get("title", ""))})

func tick_exam() -> void:
	# S44: a guild exam whose candle burns out fails.
	var ac = game.active()
	if ac != null and not ac.crafting.get("guild_exam", {}).is_empty() and exam_left(ac) <= 0.0:
		var ex: Dictionary = ac.crafting.guild_exam
		ac.crafting["guild_exam"] = {}
		emit("guild_exam_failed", {"actor": ac.id, "craft": str(ex.craft), "rank": str(ex.rank), "made": int(ex.made)})

# ------------------------------------------------------------------ S44/S49 commissions
## The day's number (commissions refresh each morning, with the daily reset).
static func commission_day() -> int:
	return Clock.reset_day(Clock.now_utc())

## Where a guild's board keeps its day (the Alchemist Guild's keeps its first key, so old saves carry on).
static func _board_key(craft: String) -> String:
	return "commission_state" if craft == "alchemy" else "commission_state_" + craft

## A fifth of the zone's daily income target, per guild: Level x 60 taels an hour for three hours of play (S39).
func commission_cap(c, craft := "alchemy") -> int:
	var k: Dictionary = guild_def(craft).get("commissions", {})
	return int(float(k.get("cap_share", 0.2)) * float(k.get("income_per_level_hour", 60)) * float(k.get("play_hours", 3)) * ProgressionRules.level(c))

func commission_paid_today(c, craft := "alchemy") -> int:
	var cm: Dictionary = c.crafting.get(_board_key(craft), {})
	return int(cm.get("paid", 0)) if int(cm.get("day", -1)) == commission_day() else 0

## What a guild takes orders for: pills for the Alchemist Guild, worn pieces for the Forge Guild, plates for the Formation Guild.
func _orderable(craft: String, item: String) -> bool:
	match craft:
		"alchemy": return ContentDB.item(item).has("pill")
		"smithing": return ContentDB.is_equipment(item)
	return true

## Today's three orders on a guild's board, drawn from what this character knows how to make.
func commissions(c, craft := "alchemy") -> Array:
	var rank := guild_rank(c, craft)
	if rank == "": return []
	var day := commission_day()
	var key := _board_key(craft)
	var cm: Dictionary = c.crafting.get(key, {})
	if int(cm.get("day", -1)) == day: return cm.get("orders", [])
	var k: Dictionary = guild_def(craft).get("commissions", {})
	var known: Array = []
	for r in ContentDB.all("recipes"):
		if str(r.craft) == craft and crafting.knows(c, str(r.id)) and _orderable(craft, str(r.outputs[0].item)): known.append(str(r.id))
	known.sort()
	var rng := Rng.stream(c.id, "commission" if craft == "alchemy" else "commission_" + craft)   # drawn once each morning
	var orders: Array = []
	var mult := float(guild_rank_def(craft, rank).get("pay_mult", 1.2))
	var prefix := "c" if craft == "alchemy" else craft + "_"
	for i in int(k.get("per_day", 3)):
		if known.is_empty(): break
		var rid: String = known[rng.randi_range(0, known.size() - 1)]
		var item := str(ContentDB.entry("recipes", rid).outputs[0].item)
		var cnt: Array = k.get("count", [1, 3])
		var n := rng.randi_range(int(cnt[0]), int(cnt[1]))
		orders.append({"id": "%s%d_%d" % [prefix, day, i], "item": item, "count": n, "quality": "common",
			"pay": int(round(LootRules.buy_price(item) * mult * n)), "accepted": false, "done": false})
	c.crafting[key] = {"day": day, "orders": orders, "paid": 0}
	return orders

## An order on any open board: {order, craft}, or {} when there is none.
func _order(c, id: String) -> Dictionary:
	for g in ContentDB.all("guilds"):
		for o in commissions(c, str(g.craft)):
			if str(o.id) == id: return {"order": o, "craft": str(g.craft)}
	return {}

func accept_commission(c, id: String) -> Dictionary:
	var found := _order(c, id)
	if found.is_empty() or found.order.get("done", false): return fail("no_order")
	found.order.accepted = true
	return ok()

func deliver_commission(c, id: String, pay: String) -> Dictionary:
	var found := _order(c, id)
	if found.is_empty() or found.order.get("done", false): return fail("no_order")
	var o: Dictionary = found.order
	var craft: String = found.craft
	if not o.get("accepted", false): return fail("not_accepted", {"text": Tx.t("sim.crafting.commission_accept_first")})
	# Pieces or pills of the order's quality or better, from any stacks; a locked piece is never handed over.
	var fits := func(s) -> bool:
		return s != null and str(s.id) == str(o.item) and quality_rank(str(s.get("quality", "common"))) >= quality_rank(str(o.quality)) \
			and not c.inventory.locked.has(int(s.get("uid", -1)))
	var have := 0
	for s in c.inventory.bag:
		if fits.call(s): have += int(s.get("count", 1))
	if have < int(o.count): return fail("materials", {"text": Tx.t("sim.crafting.missing") % ContentDB.item_name(str(o.item))})
	var left := int(o.count)
	for i in c.inventory.bag.size():
		if left <= 0: break
		var s = c.inventory.bag[i]
		if not fits.call(s): continue
		var take := mini(left, int(s.get("count", 1)))
		game.inventory.apply_remove_index(c.id, i, take, "commission")
		left -= take
	o.done = true
	var room := maxi(0, commission_cap(c, craft) - commission_paid_today(c, craft))
	var paid := mini(int(o.pay), room)
	var cm: Dictionary = c.crafting.get(_board_key(craft), {})
	cm.paid = commission_paid_today(c, craft) + paid
	var k: Dictionary = guild_def(craft).get("commissions", {})
	if pay == "contribution":
		var contrib := int(round(paid * float(k.get("contribution_per_tael", 0.1))))
		if contrib > 0: game.apply_effects(c.id, [{"kind": "add_contribution", "amount": contrib}], "commission")
	elif paid > 0:
		game.economy.apply_currency("silver_tael", paid, "commission")
	emit("commission_completed", {"actor": c.id, "id": id, "craft": craft, "item": str(o.item), "count": int(o.count), "paid": paid, "pay": pay,
		"capped": paid < int(o.pay)})
	return ok({"paid": paid, "capped": paid < int(o.pay)})
