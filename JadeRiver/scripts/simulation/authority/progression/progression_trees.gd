class_name ProgressionTrees
extends ProgressionPart
## ProgressionAuthority's part: the element trees' Realisations and nodes (technique_plan §4), and the Lost Arts found
## at steles, on foes and in Lu's journal (§5, decision 19).

# ------------------------------------------------------------------ P13a the element trees (technique_plan §4)
## The Realisations pool, spent and free (TechniqueTreeRules.realisations).
func realisations(c) -> Dictionary:
	return TechniqueTreeRules.realisations(c)

## The Realisations there are to place now: the free ones, once a tree has opened (the HUD's points badge reads it).
func realisations_free(c) -> int:
	if c == null: return 0
	var lv := ProgressionRules.level(c)
	if not TechniqueTreeRules.trees().any(func(tree): return lv >= int(TechniqueTreeRules.ring_row(TechniqueTreeRules.first_ring(str(tree))).get("level", 1))): return 0
	return int(TechniqueTreeRules.realisations(c).free)

## The meridian points not yet spent on the Foundation tab (the HUD's points badge reads it).
func meridian_points_free(c) -> int:
	return int(c.cultivator.unspent_meridian_points) if c != null else 0

## Realise a node out of combat: it costs its Realisations, and an art's node teaches its art (§4.3, §4.4).
func realise_node(c, nid: String) -> Dictionary:
	if game.combat.in_combat(c): return fail("in_combat", {"text": Tx.t("sim.tree.in_combat")})
	var why := TechniqueTreeRules.realise_block(c, nid, game.ctx(c))
	if why != "": return fail(why, {"text": Tx.t("sim.tree." + why)})
	var n := TechniqueTreeRules.node(nid)
	c.cultivator.tree.realised[nid] = true
	if str(n.kind) in ["art", "keystone"]: progression.apply_learn_technique(c.id, nid)
	emit("tree_node_realised", {"actor": c.id, "node": nid, "tree": str(n.tree), "kind": str(n.kind)})
	return ok(TechniqueTreeRules.realisations(c))

## Let a node go out of combat, leaves first: its Realisations come back at once; a realised art is unlearned but keeps
## its mastery, and cannot go while it sits in a slot (§4.5).
func unrealise_node(c, nid: String) -> Dictionary:
	if game.combat.in_combat(c): return fail("in_combat", {"text": Tx.t("sim.tree.in_combat")})
	var why := TechniqueTreeRules.unrealise_block(c, nid)
	if why != "": return fail(why, {"text": Tx.t("sim.tree." + why)})
	var n := TechniqueTreeRules.node(nid)
	c.cultivator.tree.realised.erase(nid)
	if str(n.kind) in ["art", "keystone"]: c.cultivator.techniques_known.erase(nid)
	emit("tree_node_unrealised", {"actor": c.id, "node": nid, "tree": str(n.tree), "kind": str(n.kind)})
	return ok(TechniqueTreeRules.realisations(c))

## Let a whole tree go (§4.5): free once in each great realm, then for a Clear Heart Incense. Realised arts leave
## their slots; taught arts stay known.
func reset_tree(c, tree: String) -> Dictionary:
	if game.combat.in_combat(c): return fail("in_combat", {"text": Tx.t("sim.tree.in_combat")})
	if not tree in TechniqueTreeRules.trees(): return fail("unknown_tree")
	var nodes: Array = TechniqueTreeRules.realised(c).keys().filter(func(nid): return str(TechniqueTreeRules.node(str(nid)).get("tree", "")) == tree)
	if nodes.is_empty(): return fail("nothing", {"text": Tx.t("sim.tree.nothing")})
	var realm_now := ProgressionRules.great_realm(c.cultivator.realm_key)
	var free: bool = not c.cultivator.tree.resets.has(realm_now)
	var incense := str(TechniqueTreeRules.config().get("reset_item", "clear_heart_incense"))
	if not free:
		if c.inventory.count(incense) <= 0: return fail("needs_incense", {"text": Tx.t("sim.tree.needs_incense")})
		game.inventory.apply_remove(c.id, incense, 1, "tree_reset")
	else: c.cultivator.tree.resets[realm_now] = true
	var refund := 0
	for nid in nodes:
		refund += TechniqueTreeRules.cost(str(nid))
		c.cultivator.tree.realised.erase(nid)
		if not str(TechniqueTreeRules.node(str(nid)).get("kind", "")) in ["art", "keystone"]: continue
		c.cultivator.techniques_known.erase(nid)
		for i in c.cultivator.technique_slots.size():
			if c.cultivator.technique_slots[i] == nid:
				c.cultivator.technique_slots[i] = null
				emit("technique_equipped", {"actor": c.id, "technique": "", "slot": i})
		for bar in c.cultivator.technique_bars.values():
			for i in (bar as Array).size():
				if bar[i] == nid: bar[i] = null
	emit("tree_reset", {"actor": c.id, "tree": tree, "free": free, "refund": refund})
	return ok({"free": free, "refund": refund})

## A save from before the trees (§4.9): every known art on a tree lights the route from its sector's gate, paid from
## Realisations (the tree's opening gift to an established character), and the Dao arts of the tiers already reached
## are taught. Runs once, when the character is entered; mastery, slots and bars are untouched.
func migrate_tree(c) -> void:
	if c == null or int(c.cultivator.tree.get("v", 0)) >= 1: return
	for tid in c.cultivator.techniques_known.duplicate():
		for p in TechniqueTreeRules.route_to(str(tid)): c.cultivator.tree.realised[p] = true
	for d in c.cultivator.daos:
		var effects: Array = ContentDB.entry("daos", str(d)).get("effects", [])
		for i in mini(int(c.cultivator.daos[d].get("tier", 0)), effects.size()):
			if effects[i] is Dictionary and effects[i].has("learn_technique"): progression.apply_learn_technique(c.id, str(effects[i].learn_technique))
	lost_pages(c)   # the journal pages already gathered count toward the Ferryman's Oar
	c.cultivator.tree["v"] = 1

## The page's view of one node of a tree (the page asks for the nodes it shows, as it shows them): its state (realised,
## taught, open, or locked and why), its cost, and what learning it takes in one go (`learn`: the nodes to realise in
## order, `total` their cost; P13b). The Dao arts at a tree's gates are tree_dao_arts.
func tree_node(c, nid: String, ctx: Dictionary = {}) -> Dictionary:
	if ctx.is_empty(): ctx = game.ctx(c)
	var n := TechniqueTreeRules.node(nid)
	var state := "realised" if TechniqueTreeRules.realised(c).has(nid) else ("taught" if c.cultivator.techniques_known.has(nid) else "")
	var plan := {"nodes": [], "cost": TechniqueTreeRules.cost(nid), "why": "" if state != "" else "act_locked"}
	if state == "" and int(n.act) <= int(TechniqueTreeRules.config().get("act_open", 3)): plan = TechniqueTreeRules.learn_plan(c, nid, ctx)
	if state == "": state = "open" if str(plan.why) == "" else "locked"
	return {"id": nid, "kind": str(n.kind), "family": str(n.get("family", "")), "kin": str(n.get("kin", "")), "ring": int(n.ring),
		"state": state, "why": str(plan.why), "cost": TechniqueTreeRules.cost(nid), "learn": plan.nodes, "total": int(plan.cost)}

## The Dao arts at a tree's gates, each taught or waiting on its Dao's tier.
func tree_dao_arts(c, tree: String) -> Array:
	var daos: Array = TechniqueTreeRules.dao_arts(tree)
	for d in daos: d["state"] = "taught" if c.cultivator.techniques_known.has(str(d.id)) else "locked"
	return daos

## One node's prerequisites for the page's reading (TechniqueTreeRules.needs).
func node_needs(c, nid: String) -> Array:
	return TechniqueTreeRules.needs(c, nid, game.ctx(c))

## The lost manuals carried and not read, as found cards the board shows with Read (TechniqueTreeRules.lost_unread).
func lost_unread(c) -> Array:
	return TechniqueTreeRules.lost_unread(c)

## The trees' tabs (technique_plan §4.10), in the page's order: each tree's name and element, whether its first ring's
## Level is reached (Space and Time open late), its realised nodes and the arts of it the character knows.
func tree_tabs(c) -> Array:
	var lv := ProgressionRules.level(c)
	var realised_in := {}
	for nid in TechniqueTreeRules.realised(c):
		var t := str(TechniqueTreeRules.node(str(nid)).get("tree", ""))
		realised_in[t] = int(realised_in.get(t, 0)) + 1
	var known_in := {}
	for tid in c.cultivator.techniques_known:
		var t2 := TechniqueTreeRules.tree_of_element(str(ContentDB.entry("techniques", str(tid)).get("element", "none")))
		known_in[t2] = int(known_in.get(t2, 0)) + 1
	var out: Array = []
	for tree in TechniqueTreeRules.trees():
		var ring := TechniqueTreeRules.first_ring(tree)
		out.append({"tree": tree, "name": ContentDB.text("technique.tree." + tree), "element": str(TechniqueTreeRules.tree_def(tree).get("element", "")),
			"open": lv >= int(TechniqueTreeRules.ring_row(ring).get("level", 1)), "realised": int(realised_in.get(tree, 0)), "known": int(known_in.get(tree, 0))})
	return out

## The Lost Arts board (roadmap decision 19): counts per act and the found arts' cards, nothing of an unfound one.
func lost_arts_view(c) -> Dictionary:
	return TechniqueTreeRules.lost_view(c)

# ------------------------------------------------------------------ P13a Lost Arts (technique_plan §5; decision 19)
## A lost art found: a stele rubbed, a ruin's writing read, a master's lesson, a foe's manual, a quest's end, an auction
## lot, a lineage's piece. It is learned as what it is (a technique, an Inner Art or a Secret Art) and flagged
## found_<art>; found a second time it is a Manual Page instead (§5.3). Nothing spoke of it before.
func apply_learn_lost_art(actor_id: String, art: String) -> void:
	var c = game.character(actor_id)
	var row := ContentDB.entry("lost_arts", art)
	if c == null or row.is_empty(): return
	if TechniqueTreeRules.lost_found(c, row):
		game.inventory.apply_add(c.id, str(TechniqueTreeRules.config().get("found_twice", "manual_page")), 1, "lost_art_again")
		return
	match str(row.get("kind", "technique")):
		"inner": progression.apply_learn_inner_art(c.id, art)
		"secret": progression.apply_learn_secret_art(c.id, art)
		_: progression.apply_learn_technique(c.id, art)
	game.quest.apply_flag(c.id, "found_" + art)
	emit("lost_art_found", {"actor": c.id, "art": art, "kind": str(row.get("kind", "technique")), "act": int(row.get("act", 1)),
		"lineage": str(row.get("lineage", ""))})

## A stele read at its insight stone (§5.2): the first art it holds that is not yet found and whose condition holds
## (a Rubbing Kit, a Dao tier, an hour, a season) is taken as a rubbing. False when the stone is only a stone today.
func read_stele(c, object_id: String) -> bool:
	for row in TechniqueTreeRules.lost_at(object_id):
		if TechniqueTreeRules.lost_found(c, row): continue
		if not RequirementRules.passes({"all": row.src.get("requires", [])}, game.ctx(c)): continue
		apply_learn_lost_art(c.id, str(row.id))
		return true
	return false

## The lost manuals a defeated foe drops (§5.3), from its loot roll's `lost` rows (LootRules rolls them like named rows,
## never raised by drop rate): a manual is kept only while its art is not found and not already carried, and is sure by
## its pity-th kill.
func lost_drops(c, rolled: Array) -> Array:
	var out: Array = []
	for r in rolled:
		var art := str(r.art)
		if TechniqueTreeRules.lost_found(c, ContentDB.entry("lost_arts", art)) or c.inventory.count(str(r.item)) > 0: continue
		var kills := int(c.cultivator.tree.pity.get(art, 0)) + 1
		var pity := int(r.get("pity", 0))
		if bool(r.get("hit", false)) or (pity > 0 and kills >= pity):
			c.cultivator.tree.pity.erase(art)
			out.append({"item": str(r.item), "count": 1})
		else: c.cultivator.tree.pity[art] = kills
	return out

## Lu's journal (§5.5): each lineage piece of the Ferryman's Oar comes with its count of pages found.
func lost_pages(c) -> void:
	if c == null: return
	var flags: Array = ContentDB.config("lost_arts").get("journal_flags", [])
	var pages := flags.filter(func(f): return c.quests.has_flag(str(f))).size()
	for row in ContentDB.all("lost_arts"):
		var src: Dictionary = row.get("src", {})
		if str(src.get("kind", "")) == "pages" and pages >= int(src.get("count", 0)) and not TechniqueTreeRules.lost_found(c, row):
			apply_learn_lost_art(c.id, str(row.id))

func on_flag_set(p: Dictionary) -> void:
	if str(p.get("flag", "")) in ContentDB.config("lost_arts").get("journal_flags", []): lost_pages(game.character(str(p.get("actor", ""))))
