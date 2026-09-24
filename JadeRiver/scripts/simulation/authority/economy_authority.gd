class_name EconomyAuthority
extends Authority
## S21/S39 · Currency balances (account-wide), shop stock and daily rotation,
## buying, selling, buyback and the currency exchange. Shops never offer a weapon
## before the character has finished "The Weapon Hall".

func intents() -> Array:
	return ["buy", "sell", "exchange_currency", "buyback"]

func handle(intent: Dictionary) -> Dictionary:
	var c = char_of(intent)
	if c == null: return fail("no_character")
	match str(intent.type):
		"buy": return buy(c, str(intent.get("shop", "")), str(intent.get("item", "")), maxi(1, int(intent.get("count", 1))), int(intent.get("price", -1)))
		"sell": return sell(c, int(intent.get("index", -1)), maxi(1, int(intent.get("count", 1))))
		"exchange_currency": return exchange(str(intent.get("from", "")), str(intent.get("to", "")), int(intent.get("amount", 0)))
		"buyback": return buyback(c, int(intent.get("index", -1)))
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
		if def.get("slot", "") == "weapon" and not c.quests.is_done("the_weapon_hall"): continue
		if s.has("requires") and not RequirementRules.passes(s.requires, game.ctx(c)):
			if s.get("hide_locked", false): continue
			locked = RequirementRules.first_failure_text(s.requires, game.ctx(c))
		var price := int(s.get("price", LootRules.buy_price(item_id)))
		if currency == "contribution": price = int(s.get("price", maxi(5, int(LootRules.value_of(item_id) / 2))))
		out.append({"item": item_id, "price": price, "currency": str(s.get("currency", currency)), "locked": locked,
			"rotating": s.get("rotating", false), "learn": str(s.get("learn", ""))})
	return out

func buy(c, shop_id: String, item_id: String, count: int, seen_price: int) -> Dictionary:
	var shop := ContentDB.entry("shops", shop_id)
	if shop.is_empty(): return fail("unknown_shop")
	if not Unlocks.is_unlocked(c.id, "shop"): return fail("locked")
	var entry := {}
	for s in stock(c, shop_id):
		if s.item == item_id:
			entry = s
			break
	if entry.is_empty(): return fail("not_sold")
	if entry.locked != "": return fail("locked", {"text": entry.locked})
	# A confirmation snapshots the price; a changed price is rejected, never charged (10.7).
	if seen_price >= 0 and seen_price != int(entry.price): return fail("stale_price", {"price": entry.price})
	var total := int(entry.price) * count
	if balance(str(entry.currency), c) < total: return fail("insufficient_funds", {"text": "Not enough %s" % ContentDB.text("currency." + str(entry.currency))})
	if entry.learn != "":
		if c.cultivator.techniques_known.has(entry.learn) or c.cultivator.methods_known.has(entry.learn): return fail("already_known")
	elif c.inventory.room_for(item_id, count) < count and ContentDB.item(item_id).get("type") != "key": return fail("bag_full", {"text": "Your gourd is full"})
	apply_currency(str(entry.currency), -total, "buy")
	if entry.learn != "":
		if ContentDB.has_entry("techniques", entry.learn): game.progression.apply_learn_technique(c.id, entry.learn)
		elif ContentDB.has_entry("methods", entry.learn): game.progression.apply_learn_method(c.id, entry.learn)
	else:
		game.inventory.apply_add(c.id, item_id, count, "shop:" + shop_id)
	emit("item_bought", {"actor": c.id, "shop": shop_id, "item": item_id, "count": count, "price": total})
	return ok({"spent": total})

func sell(c, index: int, count: int) -> Dictionary:
	if index < 0 or index >= c.inventory.bag.size() or c.inventory.bag[index] == null: return fail("empty")
	var s: Dictionary = c.inventory.bag[index]
	var def := ContentDB.item(str(s.id))
	if c.inventory.locked.has(int(s.get("uid", -1))): return fail("locked", {"text": "Unlock the item first"})
	if s.get("bound", false): return fail("bound", {"text": "Bound items cannot be sold"})
	var price := LootRules.sell_price(str(s.id), s if ContentDB.is_equipment(str(s.id)) else null)
	if price <= 0: return fail("cannot_sell", {"text": "This cannot be sold"})
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
