class_name TechniqueTreeRules
extends RefCounted
## P13a · The element trees (docs/technique_plan.md §3-§4), pure: the cells of the trees, their nodes and routes, the
## Realisations that pay for them, the tree's passives, the heavy-art cap and the Lost Arts board. Reads
## techniques.json, technique_trees.json and lost_arts.json and a character; writes nothing (ProgressionAuthority
## owns the state and the intents).
##
## Nodes: a passage "p:<tree>:<family>:<ring>", a notable "n:<tree>:<family>:<act>", and an art by its own id (an
## orthodox or path art of a cell, or a keystone at the outer ring of an act). Routes run out from each sector's gate:
## passage to passage, a passage to the arts of its cell, the act's last passage to its notable and to its kin group's
## keystone, a notable to the next ring's passage and (the channels) to the neighbouring sectors' notables.

static var _built = null     # the techniques list the index was built from
static var _cells := {}      # "tree|family|ring" -> {"o": [ids], "p": [ids]}
static var _keys := {}       # "tree|kin|act" -> keystone id
static var _home := {}       # art id -> {tree, family, ring, slot}

static func config() -> Dictionary:
	return ContentDB.config("technique_trees")

# ------------------------------------------------------------------ the shape of the trees
static func trees() -> Array:
	return (config().get("trees", []) as Array).map(func(t): return str(t.id))

static func tree_def(tree: String) -> Dictionary:
	for t in config().get("trees", []):
		if str(t.id) == tree: return t
	return {}

## The tree an element's arts grow on (the `none` element's is Formless).
static func tree_of_element(el: String) -> String:
	for t in config().get("trees", []):
		if str(t.element) == el: return str(t.id)
	return ""

static func sectors() -> Array:
	return (config().get("sectors", []) as Array).filter(func(s): return s.get("built", false)).map(func(s): return str(s.id))

static func first_ring(tree: String) -> int:
	return int(tree_def(tree).get("first_ring", 1))

static func ring_row(ring: int) -> Dictionary:
	for r in config().get("rings", []):
		if int(r.ring) == ring: return r
	return {}

static func act_of(ring: int) -> int:
	return int(ring_row(ring).get("act", 99))

static func edge_ring(act: int) -> int:
	return int(config().get("act_edges", {}).get(str(act), 0))

static func is_edge(ring: int) -> bool:
	return edge_ring(act_of(ring)) == ring

## The ring whose band a Level stands in (§1.4).
static func ring_at_level(lv: int) -> int:
	var best := 1
	for r in config().get("rings", []):
		if lv >= int(r.level): best = maxi(best, int(r.ring))
	return best

## The kin group of a weapon family (gauntlets are the fists'); "" for none.
static func kin_of(family: String) -> String:
	if family == "gauntlets": family = "fists"
	for s in config().get("sectors", []):
		if str(s.id) == family: return str(s.kin)
	return ""

static func kin_sectors(kin: String) -> Array:
	return sectors().filter(func(f): return kin_of(f) == kin)

## A keystone is its kin group's: any weapon of the group holds it, and the Body and Voice group's are free-hand arts.
static func kin_holds(t: Dictionary, held_family: String) -> bool:
	var kin := str(t.get("kin", "voice"))
	return kin == "voice" or kin_of(held_family) == kin

# ------------------------------------------------------------------ the cells
static func _index() -> void:
	var list: Array = ContentDB.all("techniques")
	if is_same(_built, list): return
	_built = list
	_cells.clear(); _keys.clear(); _home.clear()
	for t in list:
		var kind := str(t.get("kind", ""))
		var tree := tree_of_element(str(t.get("element", "none")))
		if kind == "keystone":
			_keys["%s|%s|%d" % [tree, str(t.kin), act_of(int(t.ring))]] = str(t.id)
			_home[str(t.id)] = {"tree": tree, "family": "", "kin": str(t.kin), "ring": int(t.ring), "slot": "k"}
			continue
		if kind != "": continue
		var ring := int(t.get("ring", 0))
		var slot := "p" if str(t.get("path", "")) != "" and ring > first_ring(tree) else "o"
		var key := "%s|%s|%d" % [tree, str(t.family), ring]
		if not _cells.has(key): _cells[key] = {"o": [], "p": []}
		_cells[key][slot].append(str(t.id))
		_home[str(t.id)] = {"tree": tree, "family": str(t.family), "ring": ring, "slot": slot}

static func cell(tree: String, family: String, ring: int) -> Dictionary:
	_index()
	return _cells.get("%s|%s|%d" % [tree, family, ring], {"o": [], "p": []})

static func keystone_at(tree: String, kin: String, act: int) -> String:
	_index()
	return str(_keys.get("%s|%s|%d" % [tree, kin, act], ""))

## Where an art sits on the trees ({tree, family, ring, slot}); {} for one that is off them (a Dao or lost art).
static func home(tid: String) -> Dictionary:
	_index()
	return _home.get(tid, {})

# ------------------------------------------------------------------ nodes
static func passage(tree: String, family: String, ring: int) -> String:
	return "p:%s:%s:%d" % [tree, family, ring]

static func notable(tree: String, family: String, act: int) -> String:
	return "n:%s:%s:%d" % [tree, family, act]

## A node as a dictionary: {kind: passage | notable | art | keystone, tree, family, ring, act, kin, id}; {} if none.
static func node(nid: String) -> Dictionary:
	var p := nid.split(":")
	if p.size() == 4 and p[0] == "p":
		return {"kind": "passage", "tree": p[1], "family": p[2], "ring": int(p[3]), "act": act_of(int(p[3])), "id": nid}
	if p.size() == 4 and p[0] == "n":
		return {"kind": "notable", "tree": p[1], "family": p[2], "act": int(p[3]), "ring": edge_ring(int(p[3])), "id": nid}
	var h := home(nid)
	if h.is_empty(): return {}
	var out := h.duplicate()
	out.merge({"kind": "keystone" if h.slot == "k" else "art", "act": act_of(int(h.ring)), "id": nid})
	return out

static func cost(nid: String) -> int:
	var costs: Dictionary = config().get("costs", {})
	var n := node(nid)
	return int(costs.get({"passage": "passage", "notable": "notable", "art": "art", "keystone": "keystone"}.get(str(n.get("kind", "")), ""), 0))

## Every node of a tree, sector by sector and ring by ring, then the keystones (a v1.2.x tree: 324 and its trunk).
static func nodes_of(tree: String) -> Array:
	var out: Array = []
	var built := int(config().get("act_open", 3))
	for f in sectors():
		for ring in range(first_ring(tree), 14):
			out.append(passage(tree, f, ring))
			var c := cell(tree, f, ring)
			out.append_array(c.o)
			out.append_array(c.p)
			if is_edge(ring): out.append(notable(tree, f, act_of(ring)))
	for act in range(1, 7):
		for kin in ["voice", "edges", "reach", "distance"]:
			var k := keystone_at(tree, kin, act)
			if k != "": out.append(k)
	return out

## The nodes a node needs one of (its route inward), before any gate, Level or source.
static func inward(nid: String) -> Array:
	var n := node(nid)
	match str(n.get("kind", "")):
		"passage":
			var ring := int(n.ring)
			if ring <= first_ring(str(n.tree)): return []
			var out := [passage(str(n.tree), str(n.family), ring - 1)]
			if is_edge(ring - 1): out.append(notable(str(n.tree), str(n.family), act_of(ring - 1)))
			return out
		"notable":
			var out2 := [passage(str(n.tree), str(n.family), int(n.ring))]
			var fams := sectors()
			var i := fams.find(str(n.family))
			for j in [i - 1, i + 1]:
				out2.append(notable(str(n.tree), str(fams[posmod(j, fams.size())]), int(n.act)))
			return out2
		"art": return [passage(str(n.tree), str(n.family), int(n.ring))]
		"keystone":
			return kin_sectors(str(n.kin)).map(func(f): return passage(str(n.tree), f, int(n.ring)))
	return []

# ------------------------------------------------------------------ the character's side
static func tree_state(c) -> Dictionary:
	return c.cultivator.tree

static func realised(c) -> Dictionary:
	return c.cultivator.tree.get("realised", {})

## A sector's gate (§4.2): open once the family has been used (its weapon Dao has insight) or an art of it is known;
## the free hand's is always open.
static func gate_open(c, family: String) -> bool:
	if family == "any": return true
	var dao := str(ContentDB.entry("weapon_families", family).get("dao", ""))
	if dao != "" and c.cultivator.daos.has(dao): return true
	for tid in c.cultivator.techniques_known:
		if str(ContentDB.entry("techniques", str(tid)).get("family", "")) == family: return true
	return false

## The path a path art asks to be walked, to realise it (§4.4 rule 3).
static func walks(c, path: String) -> bool:
	match path:
		"body": return ProgressionRules.body_tier_index(c.cultivator) >= 1
		"blood": return ProgressionAuthority.walks(c, "blood")
		"confucian": return ProgressionAuthority.walks(c, "confucian")
		"buddhist": return not c.cultivator.vows.is_empty()
		"poison": return ProgressionRules.knows_poison_art(c)
	return true

## Realisations (§4.3), one pool for every tree: Level + 2 x the major breakthroughs passed + every Dao's tiers + each
## known art's mastery tiers past the second. {total, spent, free}.
static func realisations(c) -> Dictionary:
	var total := ProgressionRules.level(c) + 2 * ProgressionRules.realm_index(c.cultivator.realm_key)
	for d in c.cultivator.daos: total += int(c.cultivator.daos[d].get("tier", 0))
	for tid in c.cultivator.techniques_known:
		total += maxi(0, int(c.cultivator.mastery.get(str(tid), {}).get("tier", 1)) - 2)
	var spent := 0
	for nid in realised(c): spent += cost(str(nid))
	return {"total": total, "spent": spent, "free": maxi(0, total - spent)}

## Why a node cannot be realised now, or "" (§4.4): the act not open yet, already lit, the ring's Level, the gate,
## the route, the path, the keystone's source, the Realisations. `ctx` is the requirement context (keystones' sources).
static func realise_block(c, nid: String, ctx: Dictionary) -> String:
	var n := node(nid)
	if n.is_empty(): return "unknown_node"
	if realised(c).has(nid): return "realised"
	if str(n.kind) in ["art", "keystone"] and c.cultivator.techniques_known.has(nid): return "known"
	if int(n.act) > int(config().get("act_open", 3)): return "act_locked"
	if ProgressionRules.level(c) < int(ring_row(int(n.ring)).get("level", 999)): return "level"
	var inner := inward(nid)
	if inner.is_empty():
		if not gate_open(c, str(n.family)): return "gate"
	elif not inner.any(func(i): return realised(c).has(i)): return "route"
	if str(n.kind) == "art":
		var t := ContentDB.entry("techniques", nid)
		if str(n.slot) == "p" and not walks(c, str(t.get("path", ""))): return "path"
	if str(n.kind) == "keystone" and not RequirementRules.passes(ContentDB.entry("techniques", nid).get("teach", {}), ctx): return "source"
	if cost(nid) > int(realisations(c).free): return "realisations"
	return ""

## Every realised node of a tree that is still joined to an open gate through realised nodes, when `without` is
## taken away (the check that a respec takes leaves first, §4.5).
static func joined(c, tree: String, without: Dictionary) -> Dictionary:
	var have := {}
	for nid in realised(c):
		if not without.has(nid) and str(node(str(nid)).get("tree", "")) == tree: have[str(nid)] = true
	var reached := {}
	var grew := true
	while grew:
		grew = false
		for nid in have:
			if reached.has(nid): continue
			var inner := inward(nid)
			var ok := gate_open(c, str(node(nid).get("family", ""))) if inner.is_empty() else inner.any(func(i): return reached.has(i))
			if ok:
				reached[nid] = true
				grew = true
	return reached

## Why a realised node cannot be let go now, or "" (§4.5): not realised, its art in a slot, or something realised
## further out still needs it.
static func unrealise_block(c, nid: String) -> String:
	if not realised(c).has(nid): return "not_realised"
	var n := node(nid)
	if str(n.get("kind", "")) in ["art", "keystone"] and slotted(c, nid): return "slotted"
	var tree := str(n.get("tree", ""))
	var left := joined(c, tree, {nid: true})
	for other in realised(c):
		if other != nid and str(node(str(other)).get("tree", "")) == tree and not left.has(str(other)): return "leaf"
	return ""

## In a slot of either weapon's bar.
static func slotted(c, tid: String) -> bool:
	if c.cultivator.technique_slots.has(tid): return true
	for bar in c.cultivator.technique_bars.values():
		if (bar as Array).has(tid): return true
	return false

## The route from a sector's gate to a known art's cell: the passages a save from before the trees lights (§4.9).
static func route_to(tid: String) -> Array:
	var h := home(tid)
	if h.is_empty() or str(h.slot) == "k": return []
	var out: Array = []
	for ring in range(first_ring(str(h.tree)), int(h.ring) + 1): out.append(passage(str(h.tree), str(h.family), ring))
	return out

# ------------------------------------------------------------------ passives (§4.2, §6.2)
## The tree's share of an art's damage (the one additive bucket) and of its Qi cost: the passages, notables and
## keystones realised on its own element and sector. The damage share is capped by Level (+15% by 99, +25% by 165).
static func passives(c, t: Dictionary) -> Dictionary:
	var k: Dictionary = config().get("passives", {})
	var tree := tree_of_element(str(t.get("element", "none")))
	var fam := str(t.get("family", "any"))
	var dmg := 0.0
	var cut := 0.0
	var kin := kin_of(fam) if fam != "any" else "voice"
	for nid in realised(c):
		var n := node(str(nid))
		if str(n.get("tree", "")) != tree: continue
		match str(n.kind):
			"passage":
				if str(n.family) != fam: continue
				if int(n.ring) % 2 == 1: dmg += float(k.get("passage_power", 0.01))
				else: cut -= float(k.get("passage_cost", -0.02))
			"notable":
				if str(n.family) == fam: dmg += float(k.get("notable", 0.03))
			"keystone":
				if str(n.kin) == kin: dmg += float(k.get("keystone", 0.02))
	return {"damage": minf(dmg, tree_cap(ProgressionRules.level(c))), "cost": cut}

## The most the trees add to one bucket at a Level: +15% by Level 99 and +25% by 165, rising with the Level.
static func tree_cap(lv: int) -> float:
	var k: Dictionary = config().get("passives", {})
	var c99 := float(k.get("cap_99", 0.15))
	if lv <= 99: return c99 * float(lv) / 99.0
	return minf(float(k.get("cap_165", 0.25)), c99 + (float(k.get("cap_165", 0.25)) - c99) * float(lv - 99) / 66.0)

# ------------------------------------------------------------------ the loadout (§6.3)
## A heavy art (a keystone or a lost art) is one to a ring of four: may `tid` go into `slot` of `slots`?
static func heavy_fits(slots: Array, slot: int, tid: String) -> bool:
	if not bool(ContentDB.entry("techniques", tid).get("heavy", false)): return true
	var ring := slot / 4
	for i in range(ring * 4, mini(slots.size(), ring * 4 + 4)):
		if i == slot or slots[i] == null or str(slots[i]) == tid: continue
		if bool(ContentDB.entry("techniques", str(slots[i])).get("heavy", false)): return false
	return true

# ------------------------------------------------------------------ Lost Arts (§5, decision 19)
## Found: known. A lost art is a technique, an Inner Art or a Secret Art.
static func lost_found(c, row: Dictionary) -> bool:
	var id := str(row.id)
	match str(row.get("kind", "")):
		"inner": return c.cultivator.inner_arts_known.has(id)
		"secret": return c.cultivator.secret_arts.has(id)
	return c.cultivator.techniques_known.has(id)

## The lost arts a stele (an insight stone) holds, for WorldAuthority to read when it is touched. World data only: no
## page reads this.
static func lost_at(object_id: String) -> Array:
	return ContentDB.all("lost_arts").filter(func(row): return str(row.get("src", {}).get("kind", "")) == "stele" and str(row.src.get("object", "")) == object_id)

## The Lost Arts board as the page may show it (roadmap §6 decision 19): for each act the character has reached, how
## many of its lost arts are found and the full card of each found one; a lineage appears once a piece of it is found,
## with its found pieces. An art not yet found is only counted: nothing here names it, draws it or says where it is.
static func lost_view(c) -> Dictionary:
	var reached := mini(act_of(ring_at_level(ProgressionRules.level(c))), int(config().get("act_open", 3)))
	var acts: Array = []
	for a in range(1, reached + 1): acts.append({"act": a, "found": 0, "total": 0, "arts": []})
	var lineages := {}
	for row in ContentDB.all("lost_arts"):
		var a := int(row.get("act", 1))
		if a > reached: continue
		var slot: Dictionary = acts[a - 1]
		slot.total = int(slot.total) + 1
		if not lost_found(c, row): continue
		slot.found = int(slot.found) + 1
		var card := lost_card(row)
		slot.arts.append(card)
		var lin := str(row.get("lineage", ""))
		if lin != "":
			if not lineages.has(lin): lineages[lin] = {"id": lin, "name": ContentDB.text("lineage.%s.name" % lin), "rule": ContentDB.text("lineage.%s.rule" % lin), "found": 0, "arts": []}
			lineages[lin].found = int(lineages[lin].found) + 1
			lineages[lin].arts.append(card)
	return {"acts": acts, "lineages": lineages.values()}

## A found art's card: what it is and what it does, never where it came from.
static func lost_card(row: Dictionary) -> Dictionary:
	var id := str(row.id)
	var table: String = {"inner": "inner_arts", "secret": "secret_arts"}.get(str(row.get("kind", "")), "techniques")
	var d := ContentDB.entry(table, id)
	return {"id": id, "kind": str(row.get("kind", "technique")), "act": int(row.get("act", 1)), "name": str(d.get("name", id)),
		"desc": describe(d) if table == "techniques" else str(d.get("desc", "")), "element": str(d.get("element", "")), "family": str(d.get("family", ""))}

# ------------------------------------------------------------------ words
## What an art does, as the player reads it: its own line when it has one (today's arts, the keystones, the Dao and
## Lost Arts), else its form's, its element's verb and its path's rule (strings technique.*), filled with its numbers.
static func describe(t: Dictionary) -> String:
	if str(t.get("desc", "")) != "": return str(t.desc)
	var form := str(t.get("form", ""))
	var el := str(t.get("element", "none"))
	var args := {"reach": int((t.get("hitbox", {}).get("x", [0, 0]) as Array)[1]), "targets": int(t.get("max_targets", 1)), "hits": int(t.get("hits", 1)),
		"dash": int(t.get("dash", 0)), "stance": t.get("stance_s", 2), "radius": int(t.get("heal_radius", 0)),
		"heal": int(round(float(t.get("allies_heal_pct", 0.0)) * 100.0)), "heal_s": int(t.get("allies_heal_s", 0)),
		"hp": int(round(float(t.get("hp_cost_pct", 0.0)) * 100.0))}
	var parts: Array = [ContentDB.text("technique.form." + form, args)]
	if form == "ward": parts.append(ContentDB.text("technique.ward." + el))
	elif form == "snare": parts.append(ContentDB.text("technique.control." + el))
	elif not form in ["chorus", "counter", "seal"] and str(t.get("path", "")) != "poison": parts.append(ContentDB.text("technique.verb." + el))
	var path := str(t.get("path", ""))
	if path != "" and str(t.get("kind", "")) == "": parts.append(ContentDB.text("technique.path." + path, args))
	return " ".join(parts)
