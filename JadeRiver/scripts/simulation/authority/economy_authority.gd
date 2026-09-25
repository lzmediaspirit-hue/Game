class_name EconomyAuthority
extends Authority
## S21/S39 · Currency balances (account-wide), shop stock and daily rotation,
## buying, selling, buyback and the currency exchange. Shops never offer a weapon
## before the character has finished "The Weapon Hall".

## Contribution lives with the training sect; Economy announces it like every other currency.
func subscribe() -> void:
	GameEvents.subscribe("contribution_changed", _on_contribution, 20)

func _on_contribution(p: Dictionary) -> void:
	emit("currency_changed", {"currency": "contribution", "value": int(p.get("value", 0)), "delta": int(p.get("delta", 0)), "source": str(p.get("source", ""))})

func intents() -> Array:
	return ["buy", "sell", "exchange_currency", "buyback", "auction_bid"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"buy": return buy(c, str(intent.get("shop", "")), str(intent.get("item", "")), maxi(1, int(intent.get("count", 1))), int(intent.get("price", -1)),
			str(intent.get("learn", "")))
		"sell": return sell(c, int(intent.get("index", -1)), maxi(1, int(intent.get("count", 1))))
		"exchange_currency": return exchange(str(intent.get("from", "")), str(intent.get("to", "")), int(intent.get("amount", 0)))
		"buyback": return buyback(c, int(intent.get("index", -1)))
		"auction_bid": return auction_bid(c, str(intent.get("lot", "")), int(intent.get("amount", 0)))
	return fail("unknown_intent")

func balance(currency: String, c = null) -> int:
	if currency == "contribution":
		if c == null: c = game.active()
		return int(c.training_sect.get("contribution", 0)) if c else 0
	return int(game.account.currencies.get(currency, 0))

func apply_currency(currency: String, amount: int, source: String) -> bool:
	if currency == "contribution":
		game.training.apply_contribution(game.active_id, amount, source)
		return true
	var v := int(game.account.currencies.get(currency, 0)) + amount
	if v < 0: return false
	game.account.currencies[currency] = v
	emit("currency_changed", {"currency": currency, "value": v, "delta": amount, "source": source})
	return true

## Daily rotation (S39): one or more slots re-rolled once per reset day, seeded by the day.
func rotation(shop_id: String) -> Array:
	var shop := ContentDB.entry("shops", shop_id)
	var rot: Dictionary = shop.get("rotation", {})
	if rot.is_empty(): return []
	var day := Clock.reset_day(Clock.now_utc())
	var key := "%s:%d" % [shop_id, day]
	var eco: Dictionary = game.account.economy
	if not eco.get("rotation", {}).has(key):
		var rng := RandomNumberGenerator.new()
		rng.seed = hash(key) ^ int(game.account.rng_seed)
		var pool: Array = rot.get("pool", [])
		var picks: Array = []
		for i in mini(int(rot.get("count", 1)), pool.size()):
			var p: Dictionary = pool[rng.randi_range(0, pool.size() - 1)]
			if not picks.has(p): picks.append(p)
		var rotation_map: Dictionary = eco.get("rotation", {})
		for k in rotation_map.keys():
			if not str(k).ends_with(":%d" % day): rotation_map.erase(k)
		rotation_map[key] = picks
		eco["rotation"] = rotation_map
		emit("shop_restocked", {"shop": shop_id})
	return eco.rotation[key]

## Everything the shop shows to this character: [{item, price, currency, locked_text, limit}].
func stock(c, shop_id: String) -> Array:
	var shop := ContentDB.entry("shops", shop_id)
	var out: Array = []
	var currency := str(shop.get("currency", "silver_tael"))
	var entries_list: Array = shop.get("stock", []).duplicate()
	for r in rotation(shop_id): entries_list.append(r.merged({"rotating": true}))
	for s in entries_list:
		var item_id := str(s.item)
		var def := ContentDB.item(item_id)
		if def.is_empty(): continue
		var locked := ""
		if def.get("slot", "") == "weapon" and not Unlocks.is_unlocked(c.id, "weapons"): continue
		if s.has("requires") and not RequirementRules.passes(s.requires, game.ctx(c)):
			if s.get("hide_locked", false): continue
			locked = RequirementRules.first_failure_text(s.requires, game.ctx(c))
		var price := int(s.get("price", LootRules.buy_price(item_id)))
		if currency == "contribution": price = int(s.get("price", maxi(5, int(LootRules.value_of(item_id) / 2))))
		elif currency != "silver_tael" and not s.has("price"):
			# Tael prices convert at the exchange rate (S21): a Spirit Stone shop charges what the taels would buy.
			var rate := float(ContentDB.config("currencies").get("exchange", {}).get("silver_tael>" + currency, 1.0))
			price = maxi(1, int(round(price * rate)))
		# S20: a shop may favour one path (the Alliance Factor gives Alliance members a better price).
		var disc: Dictionary = shop.get("discount", {})
		if not disc.is_empty() and c.quests.has_flag(str(disc.get("flag", ""))):
			price = maxi(1, int(round(price * (1.0 - float(disc.get("pct", 0.0))))))
		out.append({"item": item_id, "price": price, "currency": str(s.get("currency", currency)), "locked": locked,
			"rotating": s.get("rotating", false), "learn": str(s.get("learn", ""))})
	return out

func buy(c, shop_id: String, item_id: String, count: int, seen_price: int, learn := "") -> Dictionary:
	var shop := ContentDB.entry("shops", shop_id)
	if shop.is_empty(): return fail("unknown_shop")
	if not Unlocks.is_unlocked(c.id, "shop"): return fail("locked")
	var entry := {}
	# A shop can sell several recipe scrolls: `learn` names which one (the same item id teaches different things).
	for s in stock(c, shop_id):
		if s.item == item_id and (learn == "" or str(s.get("learn", "")) == learn):
			entry = s
			break
	if entry.is_empty(): return fail("not_sold")
	if entry.locked != "": return fail("locked", {"text": entry.locked})
	# A confirmation snapshots the price; a changed price is rejected, never charged (10.7).
	if seen_price >= 0 and seen_price != int(entry.price): return fail("stale_price", {"price": entry.price})
	var total := int(entry.price) * count
	if balance(str(entry.currency), c) < total: return fail("insufficient_funds", {"text": Tx.t("sim.economy.not_enough") % ContentDB.text("currency." + str(entry.currency))})
	if entry.learn != "":
		if c.cultivator.techniques_known.has(entry.learn) or c.cultivator.methods_known.has(entry.learn) or c.crafting.recipes.has(entry.learn): return fail("already_known")
	elif c.inventory.room_for(item_id, count) < count and not ContentDB.item(item_id).get("type") in ["key", "tool"]: return fail("bag_full", {"text": Tx.t("sim.economy.your_gourd_is_full")})
	apply_currency(str(entry.currency), -total, "buy")
	if entry.learn != "":
		if ContentDB.has_entry("techniques", entry.learn): game.progression.apply_learn_technique(c.id, entry.learn)
		elif ContentDB.has_entry("methods", entry.learn): game.progression.apply_learn_method(c.id, entry.learn)
		elif ContentDB.has_entry("recipes", entry.learn): game.crafting.apply_learn_recipe(c.id, entry.learn)
	else:
		game.inventory.apply_add(c.id, item_id, count, "shop:" + shop_id)
	emit("item_bought", {"actor": c.id, "shop": shop_id, "item": item_id, "count": count, "price": total})
	# A back-room market's goods come with a small stain on the ledger (G1 karma).
	if shop.get("black_market", false):
		game.progression.apply_karma(c.id, 0, int(ContentDB.stat_const("karma", {}).get("black_market_sin", 2)) * count, "black_market")
	return ok({"spent": total})

func sell(c, index: int, count: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(s.id))
	if c.inventory.locked.has(int(s.get("uid", -1))): return fail("locked", {"text": Tx.t("sim.economy.unlock_the_item_first")})
	if s.get("bound", false): return fail("bound", {"text": Tx.t("sim.economy.bound_items_cannot_be_sold")})
	var price := LootRules.sell_price(str(s.id), s if ContentDB.is_equipment(str(s.id)) else null)
	if price <= 0: return fail("cannot_sell", {"text": Tx.t("sim.economy.this_cannot_be_sold")})
	count = mini(count, int(s.get("count", 1)))
	var removed = game.inventory.apply_remove_index(c.id, index, count, "sell")
	apply_currency("silver_tael", price * count, "sell")
	var bb: Array = game.account.economy.get("buyback", [])
	bb.push_front({"entry": removed, "price": price * count, "day": Clock.reset_day(Clock.now_utc())})
	while bb.size() > 20: bb.pop_back()
	game.account.economy["buyback"] = bb
	emit("item_sold", {"actor": c.id, "item": str(s.id), "count": count, "price": price * count})
	emit("buyback_changed", {})
	return ok({"earned": price * count})

func buyback(c, index: int) -> Dictionary:
	var bb: Array = game.account.economy.get("buyback", [])
	if index < 0 or index >= bb.size(): return fail("bad_index")
	var e: Dictionary = bb[index]
	if balance("silver_tael") < int(e.price): return fail("insufficient_funds")
	var entry: Dictionary = e.entry
	var added := 0
	if ContentDB.is_equipment(str(entry.id)): added = game.inventory.apply_add_instance(c.id, entry, "buyback", false)
	else: added = game.inventory.apply_add(c.id, str(entry.id), int(entry.get("count", 1)), "buyback", {}, false)
	if added <= 0: return fail("bag_full")
	apply_currency("silver_tael", -int(e.price), "buyback")
	bb.remove_at(index)
	emit("buyback_changed", {})
	return ok()

## NPC exchange at a poor rate (S39: 100 taels = 1 Spirit Stone; 20% spread).
func exchange(from: String, to: String, amount: int) -> Dictionary:
	if not Unlocks.is_unlocked(game.active_id, "currency_exchange"): return fail("locked")
	var rates: Dictionary = ContentDB.config("currencies").get("exchange", {})
	var key := from + ">" + to
	if not rates.has(key) or amount <= 0: return fail("no_rate")
	if balance(from) < amount: return fail("insufficient_funds")
	var got := int(floor(amount * float(rates[key]) * (1.0 - float(ContentDB.config("currencies").get("spread", 0.2)))))
	if got <= 0: return fail("too_small")
	apply_currency(from, -amount, "exchange")
	apply_currency(to, got, "exchange")
	return ok({"received": got})

# ------------------------------------------------------------------ S21 · NPC auction house
## The Auction Pavilion at Nine Peaks (Sage 1). A few rare lots open each day and close on the
## clock. NPC bidders answer at once up to a limit they keep to themselves; a bid above it holds
## the lot, the stones stay with the house, and the item arrives by mail when the lot closes.
## An outbid character is refunded at once. The Alliance pays a larger premium than the free path.
var _auction_t := 0.0

func tick(delta: float) -> void:
	_auction_t += delta
	if _auction_t < 2.0: return
	_auction_t = 0.0
	_auction_close()
	auction_roll()

func auction_lots() -> Array:
	return game.account.economy.get("auction", {}).get("lots", [])

## The Pavilion keeps a few lots open at all times: when one closes, the next is drawn from the
## pool (seeded by the lot's running number and the account, so the sequence is fixed per account).
func auction_roll() -> void:
	var cfg := ContentDB.config("auction")
	if cfg.is_empty() or (cfg.get("pool", []) as Array).is_empty(): return
	_auction_rebase()
	var au: Dictionary = game.account.economy.get("auction", {})
	var lots: Array = au.get("lots", [])
	var open := lots.filter(func(l): return not l.get("closed", false))
	var want := int(cfg.get("lots_open", 4))
	if open.size() >= want: return
	var pool: Array = cfg.pool
	var total := 0.0
	for p in pool: total += float(p.get("weight", 1.0))
	var now := Clock.now_utc()
	var dur: Array = cfg.get("duration_h", [2, 6])
	var cap: Array = cfg.get("npc_limit", [1.4, 2.6])
	var bidders: Array = cfg.get("bidders", [])
	var n := int(au.get("next", 0))
	var rng := RandomNumberGenerator.new()
	while open.size() < want:
		rng.seed = hash("auction:%d" % n) ^ int(game.account.rng_seed)
		var pick: Dictionary = pool[0]
		for attempt in 6:   # never two open lots of the same goods
			var r := rng.randf() * total
			for p in pool:
				r -= float(p.get("weight", 1.0))
				if r <= 0.0:
					pick = p
					break
			if not open.any(func(o): return str(o.item) == str(pick.item)): break
		var start := int(pick.get("start", 10))
		# Staggered closing times, so lots come and go through the day.
		var hours := rng.randf_range(float(dur[0]), float(dur[1])) + open.size() * 0.5
		var lot := {"id": "lot_%d" % n, "item": str(pick.item), "count": int(pick.get("count", 1)), "start": start, "bid": start,
			"bidder": "npc", "npc": rng.randi_range(0, maxi(0, bidders.size() - 1)), "cap": int(round(start * rng.randf_range(float(cap[0]), float(cap[1])))),
			"opened": now, "ends": now + hours * 3600.0, "paid": 0, "closed": false}
		lots.append(lot)
		open.append(lot)
		n += 1
	# Keep a short history of closed lots only.
	while lots.size() > want + 12:
		var oldest := -1
		for i in lots.size():
			if lots[i].get("closed", false):
				oldest = i
				break
		if oldest < 0: break
		lots.remove_at(oldest)
	au["next"] = n
	au["lots"] = lots
	game.account.economy["auction"] = au
	emit("shop_restocked", {"shop": "auction"})

## What a lot stands at now: an NPC-held lot creeps up over its life (never past its limit).
func auction_price(l: Dictionary) -> int:
	if str(l.get("bidder", "npc")) != "npc": return int(l.bid)
	var span := maxf(1.0, float(l.ends) - float(l.opened))
	var f := clampf((Clock.now_utc() - float(l.opened)) / span, 0.0, 1.0)
	var drift := int(round(float(l.start) + (float(l.cap) * float(ContentDB.config("auction").get("npc_drift", 0.6)) - float(l.start)) * f))
	return maxi(int(l.bid), mini(drift, int(l.cap)))

func auction_min_bid(l: Dictionary) -> int:
	var inc := float(ContentDB.config("auction").get("min_increment", 0.1))
	var p := auction_price(l)
	return maxi(p + 1, int(ceil(p * (1.0 + inc))))

## The house premium on top of a bid: smaller on the free path (S20).
func auction_fee(c) -> float:
	var fees: Dictionary = ContentDB.config("auction").get("premium", {})
	var path := "alliance" if c.quests.has_flag("path_alliance") else ("independent" if c.quests.has_flag("path_independent") else "none")
	return float(fees.get(path, 0.1))

func auction_bid(c, lot_id: String, amount: int) -> Dictionary:
	if not Unlocks.is_unlocked(c.id, "auction_house"): return fail("locked", {"text": Unlocks.locked_text("auction_house")})
	var l := {}
	for x in auction_lots():
		if str(x.id) == lot_id: l = x
	if l.is_empty() or l.get("closed", false) or Clock.now_utc() >= float(l.ends): return fail("closed", {"text": Tx.t("sim.economy.lot_closed")})
	if str(l.bidder) == c.id: return fail("leading", {"text": Tx.t("sim.economy.you_hold_the_lot")})
	var need := auction_min_bid(l)
	if amount < need: return fail("too_low", {"text": Tx.t("sim.economy.bid_at_least") % need})
	var cost := int(ceil(amount * (1.0 + auction_fee(c))))
	if balance("spirit_stone") < cost: return fail("insufficient_funds", {"text": Tx.t("sim.economy.not_enough_stones")})
	emit("system_used", {"actor": c.id, "system": "auction_bid"})
	# An NPC answers at once while the bid is inside its limit.
	if amount < int(l.cap):
		l.bid = mini(int(l.cap), maxi(amount + 1, int(ceil(amount * (1.0 + float(ContentDB.config("auction").get("min_increment", 0.1)))))))
		if str(l.bidder) != "npc": _auction_refund(l)
		l.bidder = "npc"
		emit("auction_outbid", {"actor": c.id, "lot": lot_id, "item": str(l.item), "bid": int(l.bid)})
		return ok({"outbid": true, "bid": int(l.bid)})
	if str(l.bidder) != "npc": _auction_refund(l)
	apply_currency("spirit_stone", -cost, "auction")
	l.bid = amount
	l.bidder = c.id
	l.paid = cost
	emit("auction_bid_placed", {"actor": c.id, "lot": lot_id, "item": str(l.item), "bid": amount, "cost": cost})
	return ok({"top": true, "bid": amount, "cost": cost})

func _auction_refund(l: Dictionary) -> void:
	if int(l.get("paid", 0)) > 0:
		apply_currency("spirit_stone", int(l.paid), "auction_refund")
		emit("auction_outbid", {"actor": str(l.bidder), "lot": str(l.id), "item": str(l.item), "bid": int(l.bid)})
	l.paid = 0

## A clock that moved backward resets the reference (Part 2 · Time): an open lot keeps the time it had left.
func _auction_rebase() -> void:
	var now := Clock.now_utc()
	for l in auction_lots():
		if l.get("closed", false) or float(l.opened) <= now + 1.0: continue
		var back := float(l.opened) - now
		l.opened = now
		l.ends = float(l.ends) - back

func _auction_close() -> void:
	_auction_rebase()
	var now := Clock.now_utc()
	for l in auction_lots():
		if l.get("closed", false) or now < float(l.ends): continue
		l.closed = true
		if str(l.bidder) != "npc" and game.character(str(l.bidder)) != null:
			game.mail.apply_send(str(l.bidder), "auction_won", [{"item": str(l.item), "count": int(l.count)}],
				{"item": ContentDB.item_name(str(l.item))})
			emit("auction_won", {"actor": str(l.bidder), "lot": str(l.id), "item": str(l.item), "count": int(l.count), "bid": int(l.bid)})

