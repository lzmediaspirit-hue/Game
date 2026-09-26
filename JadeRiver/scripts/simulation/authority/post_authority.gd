class_name PostAuthority
extends Authority
## S50 · Keeping Post (V10a, docs/idle_gathering_design.md). Every character who is not being played keeps working
## at its post: an ore vein, a herb patch, a fishing spot or an insect swarm. Posts earn craft EXP and fill the
## character's Qiankun pouch at PostRules' rates; a settle turns the hours away into items and EXP, and the
## Storehouse keeps the account's bulk. Owns GameCharacter.posts and AccountState.storehouse.

const NODE_CRAFT := {"ore_vein": "delving", "herb_patch": "foraging", "fishing_spot": "angling", "insect_swarm": "netting"}

func intents() -> Array:
	return ["take_post", "leave_post", "settle_post", "settle_all", "send_to_storehouse", "withdraw_storehouse", "sew_pouch", "burn_incense"]

func handle(intent: Dictionary) -> Dictionary:
	match str(intent.type):
		"take_post": return take_post(char_of(intent), str(intent.get("object", "")))
		"leave_post": return leave_post(char_of(intent), "choice")
		"settle_post": return settle_post(game.character(str(intent.get("character", game.active_id))))
		"settle_all": return settle_all()
		"send_to_storehouse": return send_to_storehouse(game.character(str(intent.get("character", game.active_id))))
		"withdraw_storehouse": return withdraw_storehouse(char_of(intent), str(intent.get("item", "")), int(intent.get("count", 1)))
		"sew_pouch": return sew_pouch(char_of(intent), str(intent.get("category", "")))
		"burn_incense": return burn_incense(game.character(str(intent.get("character", ""))), str(intent.get("item", "")))
	return fail("unknown_intent")

# ------------------------------------------------------------------ state
func state(c) -> Dictionary:
	if not (c.posts is Dictionary): c.posts = {}
	if not c.posts.has("crafts"): c.posts["crafts"] = {}
	if not c.posts.has("pouch"): c.posts["pouch"] = {}
	if not c.posts.has("post"): c.posts["post"] = {}
	return c.posts

func post_of(c) -> Dictionary:
	return state(c).post if c != null else {}

func has_post(c) -> bool:
	return c != null and not post_of(c).is_empty()

## True while the character stands at its post in the room it is in (a place it may be switched out from).
func at_post(c) -> bool:
	return has_post(c) and str(post_of(c).get("room", "")) == str(c.position.get("room", ""))

func craft_def(craft: String) -> Dictionary:
	return ContentDB.entry("posts", craft)

func crafts() -> Array:
	return ContentDB.all("posts")

func node_def(item_id: String) -> Dictionary:
	return ContentDB.config("posts").get("nodes", {}).get(item_id, {})

func craft_known(c, craft: String) -> bool:
	var d := craft_def(craft)
	return not d.is_empty() and Unlocks.is_unlocked(c.id, str(d.get("unlock", craft)))

func xp(c, craft: String) -> float:
	return float(state(c).crafts.get(craft, {}).get("xp", 0.0))

func level(c, craft: String) -> int:
	return PostRules.level_for(xp(c, craft))

## The public command for craft EXP (posts, hand harvesting, tests); announces each new level.
func apply_craft_xp(actor_id: String, craft: String, amount: float, source: String) -> void:
	var c = game.character(actor_id)
	if c == null or amount <= 0.0 or craft_def(craft).is_empty(): return
	var before := level(c, craft)
	var rec: Dictionary = state(c).crafts.get(craft, {"xp": 0.0})
	rec.xp = float(rec.get("xp", 0.0)) + amount
	c.posts.crafts[craft] = rec
	var after := level(c, craft)
	if after > before: emit("craft_leveled", {"actor": actor_id, "craft": craft, "level": after, "source": source})

## A hand harvest of `item` trains its craft by the node's EXP (the same EXP a post earns per success).
func apply_hand_harvest(actor_id: String, item_id: String, count := 1) -> void:
	var n := node_def(_base_item(item_id))
	if n.is_empty() or n.get("side", false): return
	var c = game.character(actor_id)
	if c == null or not craft_known(c, str(n.craft)): return
	apply_craft_xp(actor_id, str(n.craft), float(n.get("exp", 0.0)) * maxf(1.0, float(count) * 0.5), "hand")

# ------------------------------------------------------------------ tools, Finesse, Diligence
## The best post tool of a craft the character owns and may use at its craft level: the item's `post` block.
func tool_of(c, craft: String) -> Dictionary:
	var lv := level(c, craft)
	var best := {}
	var ids: Array = []
	for s in c.inventory.bag:
		if s != null: ids.append(str(s.id))
	for k in c.inventory.key_items: ids.append(str(k.id))
	for id in ids:
		var p: Dictionary = ContentDB.item(id).get("post", {})
		if str(p.get("craft", "")) != craft or int(p.get("level_req", 1)) > lv: continue
		if best.is_empty() or float(p.get("power", 0.0)) > float(best.get("power", 0.0)):
			best = p.duplicate()
			best["item"] = id
	return best

func finesse_of(c, craft: String) -> float:
	var tool := tool_of(c, craft)
	var attr := str(craft_def(craft).get("attribute", "body"))
	var groups: Array = []
	if float(tool.get("finesse_pct", 0.0)) > 0.0: groups.append(float(tool.finesse_pct))
	return PostRules.finesse(float(tool.get("power", 0.0)), float(c.stats.value(attr)), level(c, craft), 0.0, groups)

func diligence_of(_c, kind := "craft") -> float:
	var sources := 100.0 * float(game.sect.idle_rate_bonus("posts"))
	return PostRules.diligence(kind, sources)

# ------------------------------------------------------------------ nodes and outputs
func craft_of_object(o: Dictionary) -> String:
	return str(NODE_CRAFT.get(str(o.get("type", "")), ""))

## [{item, toughness, exp, gate, weight, category}] a node object yields at a post. Aged herbs give their base herb;
## a fishing spot gives its fish by weight (night fish a third of the time).
func outputs_of(o: Dictionary) -> Array:
	var raw: Array = []
	match str(o.get("type", "")):
		"ore_vein", "herb_patch": raw = [{"item": _base_item(str(o.get("item", ""))), "weight": 1.0}]
		"insect_swarm": raw = o.get("outputs", [{"item": str(o.get("item", "")), "weight": 1.0}])
		"fishing_spot":
			var night := float(PostRules.rule("settle.night_share", 0.3333))
			for f in ContentDB.all("fish"):
				var spots: Array = f.get("spots", [])
				if not (str(o.get("spot", "")) in spots or "any" in spots): continue
				var w := float(f.get("weight", 1.0)) * (night if "night" in f.get("time", []) else 1.0)
				raw.append({"item": str(f.get("item", "")), "weight": w})
	var out: Array = []
	for r in raw:
		var n := node_def(str(r.item))
		if n.is_empty(): continue
		out.append({"item": str(r.item), "toughness": float(n.toughness), "exp": float(n.exp), "gate": int(n.gate),
			"weight": float(r.get("weight", 1.0)), "category": str(n.category)})
	return out

func _base_item(item_id: String) -> String:
	if not node_def(item_id).is_empty(): return item_id
	var cut := item_id.rfind("_")
	if cut > 0 and item_id.substr(cut + 1).is_valid_int():
		var stem := item_id.left(cut)
		if not node_def(stem).is_empty(): return stem
		if not node_def(stem + "_10").is_empty(): return stem + "_10"
	return item_id

func _object(room_id: String, object_id: String) -> Dictionary:
	if game.room_rt != null and str(game.room_rt.room_id) == room_id: return game.room_rt.object_def(object_id)
	for o in ContentDB.room(room_id).get("objects", []):
		if str(o.get("id", "")) == object_id: return o
	return {}

## The hourly rates of a character's post at its current Finesse, tool and Diligence (empty without a post).
func post_rates(c) -> Dictionary:
	var p := post_of(c)
	if p.is_empty(): return {}
	var o := _object(str(p.get("room", "")), str(p.get("object", "")))
	return rates_at(c, o)

## Rates a character would have at node object `o`: outputs past the craft's level gate only.
func rates_at(c, o: Dictionary) -> Dictionary:
	var craft := craft_of_object(o)
	if craft == "": return {}
	var lv := level(c, craft)
	var outs: Array = []
	for out in outputs_of(o):
		if int(out.gate) <= lv: outs.append(out)
	var tool := tool_of(c, craft)
	var fin := finesse_of(c, craft)
	var r := PostRules.rates(fin, outs, float(tool.get("speed", 3.0)), diligence_of(c))
	r.merge({"craft": craft, "finesse": fin, "tool": str(tool.get("item", "")), "diligence": diligence_of(c), "level": lv}, true)
	var side: Dictionary = PostRules.rule("side_drops", {}).get(craft, {})
	if not side.is_empty():
		var succ := 0.0
		for id in r.items: succ += float(r.items[id])
		r.items[str(side.item)] = succ / maxf(1.0, float(side.get("every", 20)))
	return r

# ------------------------------------------------------------------ pouches
func pouch(c, cat: String) -> Dictionary:
	var pc: Dictionary = state(c).pouch
	if not pc.has(cat): pc[cat] = {"tier": 0, "items": {}}
	return pc[cat]

func category_of(item_id: String) -> String:
	var n := node_def(_base_item(item_id))
	return str(n.get("category", "material"))

func capacity(c, cat: String) -> float:
	return PostRules.capacity(PostRules.compartment_cap(int(pouch(c, cat).get("tier", 0))))

func held(c, cat: String) -> float:
	var n := 0.0
	for id in pouch(c, cat).items: n += float(pouch(c, cat).items[id])
	return n

func _add_to_pouch(c, items: Dictionary) -> void:
	for id in items:
		var n := int(items[id])
		if n <= 0: continue
		var p := pouch(c, category_of(str(id)))
		p.items[id] = int(p.items.get(id, 0)) + n

# ------------------------------------------------------------------ intents
func take_post(c, object_id: String) -> Dictionary:
	if c == null: return fail("no_character")
	if not Unlocks.is_unlocked(c.id, "keeping_post"): return fail("locked", {"text": Unlocks.locked_text("keeping_post")})
	if game.room_rt == null: return fail("no_room")
	var o: Dictionary = game.room_rt.object_def(object_id)
	var craft := craft_of_object(o)
	if craft == "": return fail("not_a_node", {"text": t("sim.posts.not_a_node")})
	if not craft_known(c, craft): return fail("craft", {"text": Unlocks.locked_text(str(craft_def(craft).get("unlock", craft)))})
	var st: ActorState = game.actor_state(c.id)
	var at: Array = o.get("at", [0, 0])
	if st != null and st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > float(o.get("radius", 110)) + 40.0:
		return fail("too_far", {"text": t("sim.posts.too_far")})
	var r := rates_at(c, o)
	if r.get("outputs", []).is_empty():
		var gate := 999
		for out in outputs_of(o): gate = mini(gate, int(out.gate))
		return fail("level", {"text": t("sim.posts.needs_level") % [str(craft_def(craft).get("short", craft)), gate]})
	if has_post(c): settle_post(c)
	state(c).post = {"kind": "craft", "craft": craft, "room": game.room_rt.room_id, "object": object_id, "since": Clock.now_utc(), "paused": true}
	emit("post_taken", {"actor": c.id, "craft": craft, "room": game.room_rt.room_id, "object": object_id})
	emit("system_used", {"actor": c.id, "system": "post"})
	return ok({"craft": craft, "rates": r})

func leave_post(c, reason: String) -> Dictionary:
	if not has_post(c): return fail("no_post")
	var led := settle_post(c)
	state(c).post = {}
	emit("post_left", {"actor": c.id, "reason": reason})
	return ok({"ledger": led.get("ledger", {})})

## S50 migration: an old idle Gather task becomes a craft post at a matching node of its room, from when it began.
func migrate_idle(c) -> void:
	if c == null or not (c.idle_task is Dictionary) or str(c.idle_task.get("task", "")) != "gather" or has_post(c): return
	var room := str(c.idle_task.get("room", ""))
	var want := _base_item(str(c.idle_task.get("item", "")))
	var pick := {}
	for o in ContentDB.room(room).get("objects", []):
		if craft_of_object(o) == "": continue
		if pick.is_empty() or _base_item(str(o.get("item", ""))) == want: pick = o
		if _base_item(str(o.get("item", ""))) == want: break
	if pick.is_empty(): return
	state(c).post = {"kind": "craft", "craft": craft_of_object(pick), "room": room, "object": str(pick.id),
		"since": float(c.idle_task.get("started_utc", Clock.now_utc())), "paused": false}
	c.idle_task = {}

## The character goes to play (entered): its post is settled and pauses while it is played.
func on_entered(c) -> Dictionary:
	if not has_post(c): return {}
	var r := settle_post(c)
	post_of(c)["paused"] = true
	return r.get("ledger", {})

## The character is switched out: at its post it resumes work from now; anywhere else it has walked away.
func on_left(c) -> void:
	if not has_post(c): return
	if at_post(c):
		post_of(c)["paused"] = false
		post_of(c)["since"] = Clock.now_utc()
	else:
		state(c).post = {}
		emit("post_left", {"actor": c.id, "reason": "walked"})

## The game is put away while this character is played: at its post it goes on working meanwhile.
func on_app_paused(c) -> void:
	if at_post(c) and post_of(c).get("paused", false):
		post_of(c)["paused"] = false
		post_of(c)["since"] = Clock.now_utc()

## Settle a post's hours since the last settle into its pouch and craft EXP. Returns ok({ledger}).
func settle_post(c) -> Dictionary:
	if not has_post(c): return ok({"ledger": {}})
	var p := post_of(c)
	if p.get("paused", false): return ok({"ledger": {}})
	var el := Clock.elapsed_since(float(p.get("since", 0.0)))
	p["since"] = Clock.now_utc()
	if not el.valid: return ok({"ledger": {}, "clock_moved_back": true})
	var hours := minf(float(el.elapsed) / 3600.0, 24.0 * float(PostRules.rule("settle.max_days", 90)))
	return ok({"ledger": _work(c, hours, "post")})

## `hours` of a post's work at current rates: items into the pouch (each category stops when full), EXP always.
func _work(c, hours: float, source: String) -> Dictionary:
	var r := post_rates(c)
	if r.is_empty() or hours <= 0.0: return {}
	var craft := str(r.craft)
	var cat_of := {}
	var held_by := {}
	var caps := {}
	for id in r.items:
		var cat := category_of(str(id))
		cat_of[id] = cat
		held_by[cat] = held(c, cat)
		caps[cat] = capacity(c, cat)
	var amt := PostRules.settle_amounts(hours, r.items, cat_of, held_by, caps)
	var rng := Rng.stream(c.id, "posts")
	var got := {}
	for id in amt.items:
		var n := PostRules.draw(float(amt.items[id]), rng)
		if n > 0: got[id] = n
	_add_to_pouch(c, got)
	var lv_before := level(c, craft)
	var exp := float(r.exp_h) * hours
	apply_craft_xp(c.id, craft, exp, source)
	var ledger := {"character": c.id, "name": c.name, "hours": hours, "craft": craft, "diligence": float(r.diligence),
		"exp": exp, "level_before": lv_before, "level": level(c, craft), "items": got, "full": amt.full, "source": source,
		"room": str(post_of(c).get("room", ""))}
	emit("post_settled", {"actor": c.id, "character": c.id, "craft": craft, "hours": hours, "items": got, "exp": exp, "full": amt.full, "source": source})
	return ledger

## Every posted character that is not being played, settled and sent to the Storehouse (the Roll-Call).
func settle_all() -> Dictionary:
	var ledgers: Array = []
	for id in game.characters:
		var c = game.character(str(id))
		if c != null: migrate_idle(c)
		if c == null or str(id) == game.active_id or not has_post(c): continue
		var r := settle_post(c)
		var led: Dictionary = r.get("ledger", {})
		send_to_storehouse(c)
		if not led.is_empty(): ledgers.append(led)
	return ok({"ledgers": ledgers})

func pouch_total(c) -> int:
	var n := 0
	for cat in state(c).pouch: n += int(held(c, str(cat)))
	return n

## Empty a character's pouch into the account's Storehouse.
func send_to_storehouse(c) -> Dictionary:
	if c == null: return fail("no_character")
	var moved := {}
	var cap := int(PostRules.rule("pouch.hard_cap", 2050000000))
	for cat in state(c).pouch:
		var p: Dictionary = state(c).pouch[cat]
		for id in p.items:
			var n := int(p.items[id])
			if n <= 0: continue
			game.account.storehouse[id] = mini(cap, int(game.account.storehouse.get(id, 0)) + n)
			moved[id] = n
		p.items = {}
	if not moved.is_empty(): emit("storehouse_changed", {"actor": c.id, "items": moved, "source": "pouch"})
	return ok({"items": moved})

## Take up to `count` of an item from the Storehouse into the bag, in a town or other safe room.
func withdraw_storehouse(c, item_id: String, count: int) -> Dictionary:
	if c == null: return fail("no_character")
	var have := int(game.account.storehouse.get(item_id, 0))
	if have <= 0 or count <= 0: return fail("empty")
	if game.room_rt != null:
		var ty := str(game.room_rt.def.get("type", ""))
		if not (ty in ["town", "sect", "home", "interior"] or game.room_rt.def.get("safe", false)):
			return fail("not_here", {"text": t("sim.posts.withdraw_in_town")})
	var n := mini(count, have)
	var added := int(game.inventory.apply_add(c.id, item_id, n, "storehouse", {}, false))
	if added <= 0: return fail("bag_full", {"text": Tx.t("sim.economy.your_gourd_is_full")})
	game.account.storehouse[item_id] = have - added
	if int(game.account.storehouse[item_id]) <= 0: game.account.storehouse.erase(item_id)
	emit("storehouse_changed", {"actor": c.id, "items": {item_id: -added}, "source": "withdraw"})
	return ok({"count": added})

## Sew a character's pouch for a category up one tier (Tailor Xun): taels and the tier's materials.
func sew_pouch(c, cat: String) -> Dictionary:
	if c == null: return fail("no_character")
	if not cat in ContentDB.config("posts").get("categories", []): return fail("unknown_category")
	if not Unlocks.is_unlocked(c.id, "pouch_sewing"): return fail("locked", {"text": Unlocks.locked_text("pouch_sewing")})
	var p := pouch(c, cat)
	var rows: Array = ContentDB.config("posts").get("sewing", [])
	var tier := int(p.get("tier", 0))
	if tier >= rows.size(): return fail("max", {"text": t("sim.posts.pouch_max")})
	var row: Dictionary = rows[tier]
	if game.economy.balance("silver_tael", c) < int(row.taels): return fail("funds", {"text": Tx.t("sim.economy.not_enough") % ContentDB.text("currency.silver_tael")})
	for need in row.get("items", []):
		if game.inventory.count(c, str(need.item)) < int(need.count):
			return fail("materials", {"text": t("sim.posts.needs_items") % [int(need.count), ContentDB.item_name(str(need.item))]})
	game.economy.apply_currency("silver_tael", -int(row.taels), "sew_pouch")
	for need in row.get("items", []): game.inventory.apply_remove(c.id, str(need.item), int(need.count), "sew_pouch")
	p.tier = tier + 1
	emit("system_used", {"actor": c.id, "system": "sew_pouch"})
	emit("pouch_sewn", {"actor": c.id, "category": cat, "tier": p.tier, "cap": capacity(c, cat)})
	return ok({"tier": p.tier, "cap": capacity(c, cat)})

## Burn Hour Incense from the active character's bag at another character's post: hours of its work at once.
func burn_incense(target, item_id: String) -> Dictionary:
	var me = game.active()
	if me == null or target == null: return fail("no_character")
	var hi: Dictionary = ContentDB.item(item_id).get("hour_incense", {})
	if hi.is_empty(): return fail("not_incense")
	if game.inventory.count(me, item_id) <= 0: return fail("none")
	if target.id == me.id or not has_post(target) or post_of(target).get("paused", false):
		return fail("no_post", {"text": t("sim.posts.incense_needs_post")})
	settle_post(target)
	var hours := float(hi.get("hours", 0.0))
	if hours <= 0.0:
		var u := Rng.stream(me.id, "posts").randf()
		hours = clampf(float(hi.get("min", 5.0)) * pow(100.0, pow(u, 1.5)), float(hi.get("min", 5.0)), float(hi.get("max", 500.0)))
	game.inventory.apply_remove(me.id, item_id, 1, "incense")
	var led := _work(target, hours, "incense")
	emit("incense_burned", {"actor": me.id, "character": target.id, "item": item_id, "hours": hours})
	return ok({"hours": hours, "ledger": led})

# ------------------------------------------------------------------ roll-call rows
## One row per character for the Roll-Call: post, craft level, rates, pouch fill and hours to full.
func roll_call() -> Array:
	var out: Array = []
	for slot in range(1, 13):
		var c = game.character("c%d" % slot)
		if c == null: continue
		migrate_idle(c)
		var p := post_of(c)
		var r := post_rates(c) if not p.is_empty() else {}
		var since_h: float = Clock.elapsed_since(float(p.get("since", 0.0))).elapsed / 3600.0 if not p.is_empty() and not p.get("paused", false) else 0.0
		# Projected from the unsettled hours: what the pouch holds now and how long until the first category fills.
		var fill := INF
		var cats := {}
		for id in r.get("items", {}):
			var cat := category_of(str(id))
			cats[cat] = float(cats.get(cat, 0.0)) + float(r.items[id])
		var inside := float(pouch_total(c))
		for cat in cats:
			var fh := PostRules.fill_hours(capacity(c, cat), held(c, cat), float(cats[cat]))
			fill = minf(fill, maxf(0.0, fh - since_h))
			inside += float(cats[cat]) * minf(since_h, fh)
		out.append({"id": c.id, "slot": slot, "name": c.name, "active": c.id == game.active_id, "post": p.duplicate(),
			"rates": r, "fill_h": fill, "pouch": int(inside), "since_h": since_h})
	return out
