# Domain operations. Every mutation of persistent state goes through an action here,
# invoked via Game.perform(name, args), which snapshots and rolls back on failure.
# Actions validate their own preconditions so a later server can reuse them unchanged.
# ctx = {p, bank, now (unix s), rng: RandomNumberGenerator, events: Array}
class_name Rules
extends RefCounted

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")

const ASSIGN := {
	"meditation": {"name": "Secluded meditation", "desc": "1 insight per 4 min, 1 essence per 10 min."},
	"mining": {"name": "Quarry work", "desc": "1 ore per 6 min from your highest unlocked region."},
	"herbalism": {"name": "Herb gathering", "desc": "1 herb per 6 min from your highest unlocked region."},
	"fishing": {"name": "Riverbank fishing", "desc": "1 fish per 6 min from your highest unlocked region."},
}
const ASSIGN_CAP_S := 8 * 3600


static func fail(msg: String) -> Dictionary:
	return {"ok": false, "err": msg}


static func ok(extra := {}) -> Dictionary:
	var r := {"ok": true}
	r.merge(extra, true)
	return r


# ---------------------------------------------------------------- inventory helpers
static func count(p: Dictionary, id: String) -> int:
	return int(p.items.get(id, 0))


static func add(p: Dictionary, id: String, n := 1) -> void:
	p.items[id] = count(p, id) + n


static func remove(p: Dictionary, id: String, n := 1) -> void:
	p.items[id] = count(p, id) - n
	if p.items[id] <= 0:
		p.items.erase(id)


# returns "" when all present, else a message naming the first missing item
static func missing(p: Dictionary, need: Dictionary) -> String:
	for id in need:
		if count(p, id) < int(need[id]):
			return "Need %d %s (have %d)" % [need[id], C.ITEMS[id].name, count(p, id)]
	return ""


static func grant(ctx: Dictionary, g: Dictionary) -> Array:
	var p: Dictionary = ctx.p
	var got := []
	for id in g.get("items", {}):
		add(p, id, int(g.items[id]))
		got.append("%s ×%d" % [C.ITEMS[id].name, g.items[id]])
	if int(g.get("coins", 0)):
		p.coins += int(g.coins)
		got.append("%d coins" % g.coins)
	if int(g.get("insight", 0)):
		p.insight += int(g.insight)
		got.append("%d insight" % g.insight)
	if int(g.get("essence", 0)):
		p.essence += int(g.essence)
		got.append("%d Qi essence" % g.essence)
	if int(g.get("xp", 0)):
		gain_xp(ctx, int(g.xp))
		got.append("%d XP" % g.xp)
	return got


static func gain_xp(ctx: Dictionary, n: int) -> int:
	var p: Dictionary = ctx.p
	p.xp += n
	var ups := 0
	while p.xp >= S.xp_to_next(p.level):
		p.xp -= S.xp_to_next(p.level)
		p.level += 1
		ups += 1
	if ups:
		var s := S.stats(p)
		p.hp = s.max_hp
		p.qi = s.max_qi
		ctx.events.append(["levelup", {"level": p.level}])
	return ups


static func rand(ctx: Dictionary, a: int, b: int) -> int:
	return ctx.rng.randi_range(a, b)


static func today(now: int) -> String:
	return Time.get_date_string_from_unix_time(now)


# ---------------------------------------------------------------- quests
static func active_chapter(p: Dictionary):
	for ch in C.CHAPTERS:
		if p.quests[ch.id].state != "complete":
			return ch
	return null


static func step_progress(p: Dictionary, ch: Dictionary, idx: int) -> Dictionary:
	var q: Dictionary = p.quests[ch.id]
	if idx >= ch.steps.size():
		return {"done": true, "have": 1, "need": 1}
	var st: Dictionary = ch.steps[idx]
	match st.type:
		"talk":
			return {"done": false, "have": 0, "need": 1}
		"have":
			var parts := []
			var h := 0
			var nd := 0
			var all_ok := true
			for id in st.items:
				var need := int(st.items[id])
				var have := mini(need, count(p, id))
				parts.append({"id": id, "have": have, "need": need})
				h += have
				nd += need
				all_ok = all_ok and have >= need
			return {"done": all_ok, "parts": parts, "have": h, "need": nd}
		"kill":
			var hk := mini(int(st.count), int(p.stats.kills.get(st.enemy, 0)) - int(q.base))
			return {"done": hk >= int(st.count), "have": maxi(0, hk), "need": st.count}
		"craft":
			var hc := mini(int(st.count), int(p.stats.crafted.get(st.recipe, 0)) - int(q.base))
			return {"done": hc >= int(st.count), "have": maxi(0, hc), "need": st.count}
		"realm":
			return {"done": int(p.realm) >= int(st.idx), "have": mini(p.realm, st.idx), "need": st.idx}
		"boss":
			var b: bool = p.bosses.get(st.id, false)
			return {"done": b, "have": 1 if b else 0, "need": 1}
		"flag":
			var f: bool = p.flags.get(st.flag, false)
			return {"done": f, "have": 1 if f else 0, "need": 1}
	return {"done": false, "have": 0, "need": 1}


static func enter_step(p: Dictionary, ch: Dictionary, idx: int) -> void:
	var q: Dictionary = p.quests[ch.id]
	q.step = idx
	q.base = 0
	if idx < ch.steps.size():
		var st: Dictionary = ch.steps[idx]
		if st.type == "kill":
			q.base = int(p.stats.kills.get(st.enemy, 0))
		# craft steps count every craft of that recipe, so brewing ahead of time is never wasted


# Auto-advance any satisfied non-talk steps. Returns mentor lines for newly entered steps.
static func quest_tick(ctx: Dictionary) -> Array:
	var p: Dictionary = ctx.p
	var lines := []
	for ch in C.CHAPTERS:
		var q: Dictionary = p.quests[ch.id]
		if q.state != "active" or q.step == 0:
			continue
		for _guard in 10:
			if q.step >= ch.steps.size():
				break
			var st: Dictionary = ch.steps[q.step]
			if st.type == "talk" or not step_progress(p, ch, q.step).done:
				break
			enter_step(p, ch, q.step + 1)
			var key := str(q.step)
			if ch.stepLines.has(key):
				lines.append(ch.stepLines[key])
			ctx.events.append(["quest", {"chapter": ch.id, "step": q.step}])
	return lines


static func objective(p: Dictionary) -> Dictionary:
	var ch = active_chapter(p)
	if ch == null:
		return {"chapter": null, "text": "The seal is whole. Cultivate, craft and take commissions.", "short": "Free cultivation", "progress": null}
	var q: Dictionary = p.quests[ch.id]
	var st: Dictionary = ch.steps[q.step]
	var prog := step_progress(p, ch, q.step)
	var text: String = st.text
	var npc: Dictionary = C.NPCS[ch.mentor]
	if q.step == 0 and p.area != npc.area:
		text = "Travel to %s and speak with %s" % [C.AREAS[npc.area].name, npc.name]
	return {"chapter": ch, "step": st, "idx": q.step, "text": text, "short": st.short, "chip": st.get("chip", ""), "progress": prog}


# ---------------------------------------------------------------- breakthrough
static func breakthrough_reqs(p: Dictionary):
	var target: int = p.realm + 1
	if target >= C.REALMS.size():
		return null
	var r: Dictionary = C.REALMS[target]
	var req: Dictionary = r.req
	var min_mer := (target - 1) * 2
	var list := [
		{"id": "level", "label": "Level %d" % req.level, "have": p.level, "need": req.level, "ok": p.level >= req.level, "hint": "Earn XP from combat, quests and discovery."},
		{"id": "insight", "label": "Insight %d" % req.insight, "have": p.insight, "need": req.insight, "ok": p.insight >= req.insight, "hint": "Meditate at a shrine; brew Insight Pills."},
	]
	if int(req.pills):
		var fp := count(p, "foundation_pill")
		list.append({"id": "pills", "label": "Foundation Pills", "have": fp, "need": req.pills, "ok": fp >= int(req.pills), "hint": "Brew at an Alchemy Furnace: 2 Moon Lotus (Whispering Bamboo), 1 Moon Eel, 1 Spirit Shard."})
	if min_mer:
		list.append({"id": "meridians", "label": "Open %d meridians" % min_mer, "have": p.meridians.size(), "need": min_mer, "ok": p.meridians.size() >= min_mer, "hint": "Spend Qi essence on the Meridians tab."})
	return {"target": target, "realm": r, "list": list}


static func _missing_text(br: Dictionary) -> String:
	var parts := []
	for x in br.list:
		if not x.ok:
			parts.append("%s (%d/%d)" % [x.label, x.have, x.need])
	return "" if parts.is_empty() else "Missing: " + ", ".join(parts)


static func _apply_breakthrough(ctx: Dictionary) -> Dictionary:
	var p: Dictionary = ctx.p
	var br = breakthrough_reqs(p)
	if br == null:
		return fail("You stand at the peak of the known realms.")
	var m := _missing_text(br)
	if m != "":
		return fail(m)
	p.insight -= int(br.realm.req.insight)
	if int(br.realm.req.pills):
		remove(p, "foundation_pill", int(br.realm.req.pills))
	p.realm = br.target
	var s := S.stats(p)
	p.hp = s.max_hp
	p.qi = s.max_qi
	for id in C.ABILITIES:
		var a: Dictionary = C.ABILITIES[id]
		if a.source == "realm" and S.can_learn(p, id) and not p.abilities.known.has(id):
			p.abilities.known.append(id)
			_auto_slot(p, id)
	ctx.events.append(["breakthrough", {"realm": p.realm}])
	return ok({"name": br.realm.name})


static func _auto_slot(p: Dictionary, id: String) -> void:
	var i: int = p.abilities.slots.find(null)
	if i >= 0:
		p.abilities.slots[i] = id


# ---------------------------------------------------------------- dispatcher
static func run(action: String, ctx: Dictionary, a: Dictionary) -> Dictionary:
	match action:
		"talk": return talk(ctx, a.npc)
		"quest_tick": return ok({"lines": quest_tick(ctx)})
		"discover_node": return discover_node(ctx, a.node_id)
		"discover_area":
			ctx.p.discovered.areas[a.area] = true
			return ok({"quiet": true})
		"harvest": return harvest(ctx, a.node_id, a.type)
		"record_kill": return record_kill(ctx, a.type, a.get("boss_id", ""))
		"mastery_hit": return mastery_hit(ctx, a.family, int(a.get("n", 1)))
		"dao_hit":
			if ctx.p.dao is Dictionary:
				ctx.p.dao.xp += 1
			return ok({"quiet": true})
		"meditate_cycle": return meditate_cycle(ctx, a.safe)
		"breakthrough": return breakthrough(ctx, a.safe)
		"check_trial": return check_trial(ctx, a.safe)
		"complete_trial":
			var r := _apply_breakthrough(ctx)
			if r.ok:
				r.msg = "Trial passed — %s!" % r.name
				r.lines = quest_tick(ctx)
			return r
		"open_meridian": return open_meridian(ctx)
		"temper_body": return temper_body(ctx, a.branch)
		"choose_dao": return choose_dao(ctx, a.id)
		"learn": return learn(ctx, a.id)
		"slot": return slot(ctx, int(a.slot), a.id)
		"choose_class": return choose_class(ctx, a.cls)
		"equip": return equip(ctx, a.id)
		"use": return use(ctx, a.id)
		"sell": return sell(ctx, a.id, int(a.get("n", 1)))
		"buy": return buy(ctx, a.id, int(a.get("n", 1)), a.shop)
		"deposit": return deposit(ctx, a.id, int(a.get("n", 1)))
		"withdraw": return withdraw(ctx, a.id, int(a.get("n", 1)))
		"craft": return craft(ctx, a.id, a.station, int(a.get("times", 1)))
		"research": return research(ctx, a.id)
		"seal_prime": return seal_prime(ctx)
		"seal_complete": return seal_complete(ctx)
		"commission": return commission(ctx, a.town, a.id)
		"revive": return revive(ctx, a.mode)
		"assign": return assign(ctx, a.kind)
		"collect_assignment": return collect_assignment(ctx)
	return fail("Unknown action " + action)


# ---------------------------------------------------------------- world / quests
static func talk(ctx: Dictionary, npc: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var idx := -1
	for i in C.CHAPTERS.size():
		if C.CHAPTERS[i].mentor == npc:
			idx = i
	if idx < 0:
		return fail("Nobody answers.")
	var ch: Dictionary = C.CHAPTERS[idx]
	var q: Dictionary = p.quests[ch.id]
	var name: String = C.NPCS[npc].name
	if q.state == "unoffered":
		if idx > 0 and p.quests[C.CHAPTERS[idx - 1].id].state != "complete":
			return ok({"lines": ["%s: The river is restless. Come back when your path brings you here." % name], "menu": []})
		q.state = "active"
		enter_step(p, ch, 0)
	if q.state == "complete":
		return ok({"lines": ["%s: Cultivate well, disciple. The commission board always needs hands." % name], "menu": ["class"] if npc == "wen" else (["dao"] if npc == "tao" else [])})
	var st: Dictionary = ch.steps[q.step]
	var lines := []
	var menu := []
	if st.type == "talk" and st.npc == npc:
		if q.step == 0:
			lines = ch.intro.duplicate()
			lines.append("(Received: %s)" % ", ".join(grant(ctx, ch.grant)))
			enter_step(p, ch, 1)
			if ch.stepLines.has("1"):
				lines.append(ch.stepLines["1"])
		else:
			lines = ch.outro.duplicate()
			var rw: Dictionary = ch.reward
			lines.append("(Received: %s)" % ", ".join(grant(ctx, rw)))
			p.flags[rw.flag] = true
			q.state = "complete"
			q.step = ch.steps.size()
			if idx + 1 < C.CHAPTERS.size():
				var nx: Dictionary = C.CHAPTERS[idx + 1]
				p.quests[nx.id].state = "active"
				enter_step(p, nx, 0)
			for aid in C.AREAS:
				if C.AREAS[aid].get("unlock", "") == rw.flag:
					p.discovered.areas[aid] = true
			ctx.events.append(["chapter", {"id": ch.id}])
	elif ch.id == "ch3" and q.step == 2:
		if int(p.soul) >= int(C.SOUL_MILESTONES[0].at):
			p.flags["soul_awakened"] = true
			lines.append("Keeper Tao: Close your eyes… yes. Your soul already senses the veins beneath the valley. Soul Sense is awake.")
		else:
			lines.append("Keeper Tao: Your soul is still clouded (%d/10 soul points). Discover more resource sites across the valley." % p.soul)
	elif ch.id == "ch3" and q.step == 3:
		lines.append("Keeper Tao: River or Ember. Choose the principle that will shape your arts.")
		menu.append("dao")
	else:
		lines.append(ch.stepLines.get(str(q.step), "%s: %s." % [name, st.text]))
	lines.append_array(quest_tick(ctx))
	if npc == "wen" and (int(q.step) >= 3 or q.state == "complete"):
		menu.append("class")
	return ok({"lines": lines, "menu": menu})


static func discover_node(ctx: Dictionary, node_id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if p.discovered.nodes.has(node_id):
		return ok({"quiet": true})
	p.discovered.nodes[node_id] = true
	var before: int = p.soul
	p.soul += 1
	for m in C.SOUL_MILESTONES:
		if before < int(m.at) and p.soul >= int(m.at):
			ctx.events.append(["soul", {"milestone": m}])
	return ok({"msg": "Discovered a resource site (+1 soul)"})


static func has_tool(p: Dictionary, tool: String) -> bool:
	for id in p.items:
		var d: Dictionary = C.ITEMS[id]
		if d.kind == "tool" and d.tool == tool:
			return true
	return false


static func harvest(ctx: Dictionary, node_id: String, type: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.NODE_TYPES.has(type):
		return fail("Nothing to gather.")
	var n: Dictionary = C.NODE_TYPES[type]
	if not has_tool(p, n.tool):
		var tn := "a pick" if n.tool == "mining" else ("a harvest kit" if n.tool == "herbalism" else "a fishing rod")
		return fail("Requires %s — Elder Wen provides one." % tn)
	var lv := S.prof_lv(p, n.prof)
	if lv < int(n.lv):
		return fail("%s Lv %d required (you are Lv %d)." % [S.cap(n.prof), n.lv, lv])
	var amt := rand(ctx, int(n.yield[0]), int(n.yield[1]))
	add(p, n.item, amt)
	p.prof[n.prof] += int(n.xp)
	p.stats.gathered[n.item] = int(p.stats.gathered.get(n.item, 0)) + amt
	var after := S.prof_lv(p, n.prof)
	if after > lv:
		ctx.events.append(["proflevel", {"prof": n.prof, "level": after}])
	discover_node(ctx, node_id)
	return ok({"msg": "+%d %s" % [amt, C.ITEMS[n.item].name], "item": n.item, "amt": amt, "lines": quest_tick(ctx)})


static func record_kill(ctx: Dictionary, type: String, boss_id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var e: Dictionary = C.ENEMIES[type]
	p.stats.kills[type] = int(p.stats.kills.get(type, 0)) + 1
	var drops := {}
	for d in e.drops:
		if ctx.rng.randf() < float(d[1]):
			drops[d[0]] = int(drops.get(d[0], 0)) + 1
	var coins := rand(ctx, int(e.coins[0]), int(e.coins[1]))
	var got := grant(ctx, {"items": drops, "coins": coins, "xp": e.xp})
	if int(e.xp):
		p.insight += 10 if e.get("boss", false) else 1
	if boss_id != "":
		p.bosses[boss_id] = true  # the fragment itself is granted by the mentor
	return ok({"got": got, "drops": drops, "coins": coins, "lines": quest_tick(ctx), "quiet": true})


static func mastery_hit(ctx: Dictionary, family: String, n: int) -> Dictionary:
	var p: Dictionary = ctx.p
	var before := S.mastery_rank(p, family)
	p.mastery[family] = mini(C.MASTERY_CAP, int(p.mastery.get(family, 0)) + n)
	var after := S.mastery_rank(p, family)
	if after > before:
		ctx.events.append(["mastery", {"family": family, "rank": after}])
	return ok({"quiet": true})


# ---------------------------------------------------------------- cultivation
static func meditate_cycle(ctx: Dictionary, safe: bool) -> Dictionary:
	var p: Dictionary = ctx.p
	if not safe:
		return fail("Unsafe — enemies are near.")
	var clarity := 1.25 if int(p.soul) >= int(C.SOUL_MILESTONES[2].at) else 1.0
	var ins := int(round((2 + p.realm) * clarity))
	var ess := 1 + (1 if p.research.get("still_mind", false) else 0)
	p.insight += ins
	p.essence += ess
	var s := S.stats(p)
	p.qi = mini(s.max_qi, int(p.qi) + 6)
	return ok({"insight": ins, "essence": ess, "lines": quest_tick(ctx), "quiet": true})


static func breakthrough(ctx: Dictionary, safe: bool) -> Dictionary:
	var br = breakthrough_reqs(ctx.p)
	if br == null:
		return fail("No further realm is known.")
	if not safe:
		return fail("Break through only at a safe shrine.")
	if br.realm.trial:
		return fail("This breakthrough requires a trial.")
	var r := _apply_breakthrough(ctx)
	if r.ok:
		r.msg = "Breakthrough! " + r.name
		r.lines = quest_tick(ctx)
	return r


static func check_trial(ctx: Dictionary, safe: bool) -> Dictionary:
	var br = breakthrough_reqs(ctx.p)
	if br == null:
		return fail("No further realm is known.")
	if not safe:
		return fail("Begin a trial only at a safe shrine.")
	var m := _missing_text(br)
	if m != "":
		return fail(m)
	return ok({"quiet": true})


static func open_meridian(ctx: Dictionary) -> Dictionary:
	var p: Dictionary = ctx.p
	var i: int = p.meridians.size()
	if i >= C.MERIDIANS.size():
		return fail("All six meridians are open.")
	var nx: Dictionary = C.MERIDIANS[i]
	var capn := S.meridian_cap(p.realm)
	if i >= capn:
		return fail("Your realm can hold %d open meridians. Break through to open more." % capn)
	if p.essence < int(nx.cost):
		return fail("Need %d Qi essence (have %d). Absorb crystals or meditate." % [nx.cost, p.essence])
	p.essence -= int(nx.cost)
	p.meridians.append(nx.id)
	return ok({"msg": nx.name + " opened", "lines": quest_tick(ctx)})


static func temper_body(ctx: Dictionary, branch: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var b = null
	for x in C.BODY_BRANCHES:
		if x.id == branch:
			b = x
	if b == null:
		return fail("Unknown branch")
	var r: int = p.body[branch]
	if r >= int(b.max):
		return fail(b.name + " is fully tempered.")
	var hide := r + 1
	var ess := 12 * (r + 1)
	if p.essence < ess:
		return fail("Need %d Qi essence (have %d)." % [ess, p.essence])
	var m := missing(p, {"hide": hide})
	if m != "":
		return fail(m + " — wolves in Whispering Bamboo drop hide.")
	remove(p, "hide", hide)
	p.essence -= ess
	p.body[branch] = r + 1
	return ok({"msg": "%s rank %d" % [b.name, r + 1]})


static func choose_dao(ctx: Dictionary, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.DAOS.has(id):
		return fail("Unknown principle")
	var q: Dictionary = p.quests.ch3
	if not (q.state == "complete" or (q.state == "active" and int(q.step) >= 3)):
		return fail("Keeper Tao has not yet taught the principles.")
	if p.dao is Dictionary and p.dao.id == id:
		return fail("Already following this principle.")
	var keep := int(p.dao.xp) / 2 if p.dao is Dictionary else 0
	p.dao = {"id": id, "xp": keep}
	p.flags["dao_chosen"] = true
	return ok({"msg": "You follow the " + C.DAOS[id].name, "lines": quest_tick(ctx)})


# ---------------------------------------------------------------- skills
static func learn(ctx: Dictionary, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.ABILITIES.has(id):
		return fail("Unknown art")
	if p.abilities.known.has(id):
		return fail("Already learned.")
	if not S.can_learn(p, id):
		return fail("Prerequisites not met.")
	p.abilities.known.append(id)
	_auto_slot(p, id)
	return ok({"msg": "Learned " + C.ABILITIES[id].name})


static func slot(ctx: Dictionary, i: int, id) -> Dictionary:
	var p: Dictionary = ctx.p
	if i < 0 or i > 2:
		return fail("Bad slot")
	if id != null and not p.abilities.known.has(id):
		return fail("Not learned.")
	if id == "step":
		return fail("Step is always available.")
	var prev: int = p.abilities.slots.find(id) if id != null else -1
	if prev >= 0:
		p.abilities.slots[prev] = p.abilities.slots[i]
	p.abilities.slots[i] = id
	return ok({"quiet": true})


static func choose_class(ctx: Dictionary, cls: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.CLASSES.has(cls):
		return fail("Unknown discipline")
	if p.cls == cls:
		return fail("Already your discipline.")
	if p.cls != null:
		if p.coins < C.CLASS_RETRAIN_FEE:
			return fail("Retraining costs %d coins." % C.CLASS_RETRAIN_FEE)
		p.coins -= C.CLASS_RETRAIN_FEE
	var old = p.cls
	p.cls = cls
	if cls == "spirit_sage" and not p.abilities.known.has("spirit_bolt"):
		p.abilities.known.append("spirit_bolt")
		_auto_slot(p, "spirit_bolt")
	if old == "spirit_sage":
		p.abilities.known.erase("spirit_bolt")
		for k in 3:
			if p.abilities.slots[k] == "spirit_bolt":
				p.abilities.slots[k] = null
	var s := S.stats(p)
	p.hp = mini(p.hp, s.max_hp)
	p.qi = mini(p.qi, s.max_qi)
	return ok({"msg": "Discipline: " + C.CLASSES[cls].name})


# ---------------------------------------------------------------- inventory
static func equip(ctx: Dictionary, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.ITEMS.has(id) or count(p, id) <= 0:
		return fail("You do not own that.")
	var d: Dictionary = C.ITEMS[id]
	if d.kind == "weapon":
		var need := int(d.rank) * 20
		var have := int(p.mastery.get(d.family, 0))
		if have < need:
			return fail("Requires %s Mastery %d (%d/%d)." % [S.cap(d.family), need, have, need])
		if int(d.get("realm", 0)) > int(p.realm):
			return fail("Requires %s realm." % C.REALMS[d.realm].name)
		p.equip.weapon = id
	elif d.kind == "cosmetic":
		p.equip[d.slot] = null if p.equip[d.slot] == id else id
	else:
		return fail("Cannot equip that.")
	var s := S.stats(p)
	p.hp = mini(p.hp, s.max_hp)
	return ok({"msg": "Equipped " + d.name if d.kind == "weapon" else "", "quiet": d.kind != "weapon"})


static func use(ctx: Dictionary, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.ITEMS.has(id) or count(p, id) <= 0:
		return fail("No %s left." % (C.ITEMS[id].name if C.ITEMS.has(id) else "item"))
	var d: Dictionary = C.ITEMS[id]
	var s := S.stats(p)
	if d.kind == "pill":
		if id == "foundation_pill":
			return fail("Foundation Pills are consumed by a breakthrough.")
		var e: Dictionary = d.effect
		if e.has("hp"):
			if p.hp >= s.max_hp:
				return fail("Already at full health.")
			p.hp = mini(s.max_hp, p.hp + int(round(e.hp * (1.3 if p.research.get("gentle_fire", false) else 1.0))))
		if e.has("qi"):
			if p.qi >= s.max_qi:
				return fail("Qi is already full.")
			p.qi = mini(s.max_qi, p.qi + int(round(e.qi * (1.3 if p.research.get("clear_spring", false) else 1.0))))
		if e.has("insight"):
			p.insight += int(e.insight)
		remove(p, id, 1)
		return ok({"msg": "Used " + d.name, "lines": quest_tick(ctx)})
	if d.kind == "crystal":
		remove(p, id, 1)
		p.essence += int(d.essence)
		return ok({"msg": "Absorbed %s: +%d Qi essence" % [d.name, d.essence]})
	return fail("That cannot be used.")


static func sell(ctx: Dictionary, id: String, n: int) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.ITEMS.has(id):
		return fail("Unknown item")
	var d: Dictionary = C.ITEMS[id]
	if d.kind == "quest":
		return fail("Quest items cannot be sold.")
	if d.kind == "tool" and int(d.value) == 0:
		return fail("Starter tools cannot be sold.")
	if p.equip.values().has(id) and count(p, id) <= n:
		return fail("Unequip it first.")
	var m := missing(p, {id: n})
	if m != "":
		return fail(m)
	remove(p, id, n)
	var gain := maxi(1, int(d.value) / 2) * n
	p.coins += gain
	return ok({"msg": "Sold %s ×%d for %d coins" % [d.name, n, gain], "lines": quest_tick(ctx)})


static func buy(ctx: Dictionary, id: String, n: int, shop: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if not C.SHOPS.has(shop) or not C.SHOPS[shop].has(id):
		return fail("Not sold here.")
	var price := buy_price(id) * n
	if p.coins < price:
		return fail("Need %d coins (have %d)." % [price, p.coins])
	p.coins -= price
	add(p, id, n)
	return ok({"msg": "Bought %s ×%d" % [C.ITEMS[id].name, n], "lines": quest_tick(ctx)})


static func buy_price(id: String) -> int:
	return maxi(3, int(C.ITEMS[id].value) * C.BUY_MARKUP)


static func deposit(ctx: Dictionary, id: String, n: int) -> Dictionary:
	var p: Dictionary = ctx.p
	var d: Dictionary = C.ITEMS.get(id, {})
	if d.is_empty() or d.kind == "quest" or d.kind == "tool":
		return fail("That stays with you.")
	if p.equip.values().has(id) and count(p, id) <= n:
		return fail("Unequip it first.")
	var m := missing(p, {id: n})
	if m != "":
		return fail(m)
	remove(p, id, n)
	ctx.bank[id] = int(ctx.bank.get(id, 0)) + n
	return ok({"quiet": true})


static func withdraw(ctx: Dictionary, id: String, n: int) -> Dictionary:
	var p: Dictionary = ctx.p
	if int(ctx.bank.get(id, 0)) < n:
		return fail("Not in storage.")
	ctx.bank[id] = int(ctx.bank[id]) - n
	if ctx.bank[id] <= 0:
		ctx.bank.erase(id)
	add(p, id, n)
	return ok({"quiet": true, "lines": quest_tick(ctx)})


# ---------------------------------------------------------------- crafting
static func find_recipe(id: String) -> Dictionary:
	for r in C.RECIPES:
		if r.id == id:
			return r
	return {}


static func craft(ctx: Dictionary, id: String, station: String, times: int) -> Dictionary:
	var p: Dictionary = ctx.p
	var r := find_recipe(id)
	if r.is_empty():
		return fail("Unknown recipe")
	if station != r.station:
		return fail("Craft this at %s in a town." % ("a Forge" if r.station == "forge" else "an Alchemy Furnace"))
	var lv := S.prof_lv(p, r.skill)
	if lv < int(r.lv):
		return fail("%s Lv %d required (you are Lv %d)." % [S.cap(r.skill), r.lv, lv])
	var need := {}
	for iid in r["in"]:
		need[iid] = int(r["in"][iid]) * times
	var m := missing(p, need)
	if m != "":
		return fail(m)
	for iid in need:
		remove(p, iid, need[iid])
	for iid in r["out"]:
		add(p, iid, int(r["out"][iid]) * times)
	p.prof[r.skill] += int(r.xp) * times
	p.stats.crafted[id] = int(p.stats.crafted.get(id, 0)) + times
	var after := S.prof_lv(p, r.skill)
	if after > lv:
		ctx.events.append(["proflevel", {"prof": r.skill, "level": after}])
	var names := []
	for iid in r["out"]:
		names.append(C.ITEMS[iid].name)
	return ok({"msg": "Crafted %s ×%d" % [", ".join(names), times], "lines": quest_tick(ctx)})


static func research(ctx: Dictionary, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var r = null
	for x in C.RESEARCH:
		if x.id == id:
			r = x
	if r == null:
		return fail("Unknown doctrine")
	if p.research.get(id, false):
		return fail("Already researched.")
	if p.coins < int(r.coins):
		return fail("Need %d coins." % r.coins)
	var m := missing(p, r.cost)
	if m != "":
		return fail(m)
	for iid in r.cost:
		remove(p, iid, int(r.cost[iid]))
	p.coins -= int(r.coins)
	p.research[id] = true
	return ok({"msg": "Doctrine learned: " + r.name})


# ---------------------------------------------------------------- formation seal (Chapter II)
static func seal_prime(ctx: Dictionary) -> Dictionary:
	var p: Dictionary = ctx.p
	if p.flags.get("seal_primed", false):
		return ok({"quiet": true})
	var m := missing(p, {"spirit_shard": 2})
	if m != "":
		return fail(m + " — shrine crystal nodes yield them.")
	remove(p, "spirit_shard", 2)
	p.flags["seal_primed"] = true
	return ok({"msg": "The altar drinks two Spirit Shards. The runes awaken."})


static func seal_complete(ctx: Dictionary) -> Dictionary:
	var p: Dictionary = ctx.p
	if not p.flags.get("seal_primed", false):
		return fail("The altar is dormant.")
	if p.flags.get("seal_repaired", false):
		return ok({"quiet": true})
	p.flags["seal_repaired"] = true
	p.soul += 2
	gain_xp(ctx, 60)
	return ok({"msg": "The grove seal is repaired! (+2 soul, +60 XP)", "lines": quest_tick(ctx)})


# ---------------------------------------------------------------- commissions
static func commission(ctx: Dictionary, town: String, id: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var c = null
	for x in C.COMMISSIONS.get(town, []):
		if x.id == id:
			c = x
	if c == null:
		return fail("Unknown commission")
	var d := today(ctx.now)
	if p.commissions.day != d:
		p.commissions.day = d
		p.commissions.counts = {}
	var done := int(p.commissions.counts.get(id, 0))
	if done >= C.COMMISSION_DAILY_CAP:
		return fail("Completed %d× today — the board refreshes tomorrow." % C.COMMISSION_DAILY_CAP)
	if c.has("give"):
		var m := missing(p, c.give)
		if m != "":
			return fail(m)
		for iid in c.give:
			remove(p, iid, int(c.give[iid]))
	elif c.has("kill"):
		var type: String = c.kill.keys()[0]
		var n := int(c.kill[type])
		if not p.commissions.active.has(id):
			p.commissions.active[id] = int(p.stats.kills.get(type, 0))
			return ok({"msg": "Commission accepted."})
		var prog := int(p.stats.kills.get(type, 0)) - int(p.commissions.active[id])
		if prog < n:
			return fail("Progress %d/%d." % [prog, n])
		p.commissions.active.erase(id)
	p.commissions.counts[id] = done + 1
	return ok({"msg": "Commission complete: " + ", ".join(grant(ctx, c.reward)), "lines": quest_tick(ctx)})


# ---------------------------------------------------------------- defeat & revival
static func revive_cost(p: Dictionary) -> int:
	return 10 + int(p.level) * 5


static func revive(ctx: Dictionary, mode: String) -> Dictionary:
	var p: Dictionary = ctx.p
	var s := S.stats(p)
	if mode == "here":
		var cost := revive_cost(p)
		if p.coins < cost:
			return fail("Need %d coins." % cost)
		p.coins -= cost
		p.hp = int(ceil(s.max_hp * 0.6))
		p.qi = int(ceil(s.max_qi * 0.5))
		return ok({"msg": "Revived on site (−%d coins)" % cost})
	p.hp = s.max_hp
	p.qi = s.max_qi
	return ok({"msg": "You awaken at the sanctuary."})


# ---------------------------------------------------------------- assignments (offline-capable, capped)
static func assign(ctx: Dictionary, kind: String) -> Dictionary:
	var p: Dictionary = ctx.p
	if p.assignment != null:
		return fail("An assignment is already running. Collect it first.")
	if not ASSIGN.has(kind):
		return fail("Unknown assignment")
	p.assignment = {"kind": kind, "start": ctx.now}
	return ok({"msg": "%s assigned. It continues while you are away (up to 8h)." % ASSIGN[kind].name})


static func assignment_yield(p: Dictionary, now: int) -> Dictionary:
	var a = p.assignment
	if a == null:
		return {}
	var secs := clampi(now - int(a.start), 0, ASSIGN_CAP_S)
	var mins := secs / 60
	var region := 3 if p.flags.get("ch2_done", false) else (2 if p.flags.get("ch1_done", false) else 1)
	if a.kind == "meditation":
		return {"minutes": mins, "grant": {"insight": mins / 4, "essence": mins / 10}}
	var table := {"mining": ["copper", "iron", "jade_ore"], "herbalism": ["herb", "lotus", "ginseng"], "fishing": ["carp", "eel", "koi"]}
	var item: String = table[a.kind][region - 1]
	var n := mini(40, mins / 6)
	return {"minutes": mins, "grant": {"items": {item: n}} if n > 0 else {}, "prof": a.kind, "prof_xp": n * 2}


static func collect_assignment(ctx: Dictionary) -> Dictionary:
	var p: Dictionary = ctx.p
	if p.assignment == null:
		return fail("No assignment running.")
	var res := assignment_yield(p, ctx.now)
	p.assignment = null
	var got := grant(ctx, res.grant)
	if res.has("prof"):
		p.prof[res.prof] += int(res.prof_xp)
	return ok({"msg": ("Assignment collected: " + ", ".join(got)) if not got.is_empty() else "Collected — too little time passed to yield anything.", "lines": quest_tick(ctx)})
