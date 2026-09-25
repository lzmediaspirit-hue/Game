extends Page
## Quest log (S19): Main, Side, Daily, Done. Track up to three; abandon side quests.

var sel := ""

func _init() -> void:
	title = Tx.t("ui.quest.quests")
	tabs = [{"id": "main", "label": Tx.t("ui.quest.main")}, {"id": "side", "label": Tx.t("ui.quest.side")}, {"id": "daily", "label": Tx.t("ui.quest.daily")}, {"id": "done", "label": Tx.t("ui.quest.done")}]

func ids_for(ch, which: String) -> Array:
	var out: Array = []
	if which == "done":
		for q in ch.quests.done: out.append(q)
		out.reverse()
		return out
	for q in ch.quests.active:
		var k := str(Game.quest.quest_def(ch, q).get("kind", "side"))
		var group := "main" if k in ["main", "prologue", "guided"] else ("daily" if k == "daily" else "side")
		if group == which: out.append(q)
	if which in ["main", "side"]:
		for q in ch.quests.offered:
			var d := ContentDB.entry("quests", q)
			var k2 := str(d.get("kind", "side"))
			var g2 := "main" if k2 in ["main", "prologue", "guided"] else "side"
			if g2 == which and not ch.quests.is_active(q) and Game.quest.can_offer(ch, d): out.append(q)
	return out

## Between chapters the Main tab says what the story is waiting for.
func _next_chapter(ch, left: Rect2) -> void:
	var keyed: Array = []   # [chapter * 1000 + data order, quest]: story order, stable within a chapter
	var all_q: Array = ContentDB.all("quests")
	for i in all_q.size():
		var dq: Dictionary = all_q[i]
		if str(dq.get("kind", "")) != "main": continue
		var chap := str(dq.get("chapter", ""))
		keyed.append([(int(chap) if chap.is_valid_int() else 0) * 1000 + i, dq])
	keyed.sort_custom(func(a, b): return int(a[0]) < int(b[0]))
	for kd in keyed:
		var d: Dictionary = kd[1]
		var q := str(d.id)
		if ch.quests.done.has(q) or ch.quests.is_active(q) or d.get("hidden", false): continue
		var waits := true
		for r in d.get("requires", {}).get("all", []):
			if str(r.get("kind", "")) == "quest_done" and not ch.quests.done.has(str(r.get("quest", ""))): waits = false
		if not waits: continue
		var why := RequirementRules.first_failure_text(d.get("requires", {}), Game.ctx(ch))
		var body := Tx.t("ui.quest.next_in_the_story") % str(d.get("name", q))
		if why != "": body += "\n" + why
		else: body += Tx.t("ui.quest.the_river_will_call_when")
		para(Rect2(left.position + Vector2(24, 100), Vector2(left.size.x - 48, 120)), body, 18, UiKit.MIST)
		return

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	var ids := ids_for(ch, str(tabs[tab].id))
	var left := Rect2(content.position.x, content.position.y, 440, content.size.y)
	panel(left)
	if ids.is_empty():
		text(left.position + Vector2(0, 70), Tx.t("ui.quest.nothing_here_yet"), 20, UiKit.HOLLOW, HORIZONTAL_ALIGNMENT_CENTER, left.size.x)
		if str(tabs[tab].id) == "main": _next_chapter(ch, left)
	# S49 daily activity: the day's points and the four chests sit under the day's missions.
	var list_rect := left.grow(-10)
	if str(tabs[tab].id) == "daily":
		list_rect.size.y -= 176
		_activity(ch, Rect2(left.position.x + 18, left.end.y - 172, left.size.x - 36, 160))
	list("q", list_rect, ids.size(), 62, func(i: int, rr: Rect2):
		var q := str(ids[i])
		var d := Game.quest.quest_def(ch, q)
		var active: bool = ch.quests.is_active(q)
		var ready: bool = active and ch.quests.active[q].get("state") == "ready"
		panel(rr, "minor_panel", "selected" if sel == q else "normal")
		var mark := "?" if ready else ("!" if not active and str(tabs[tab].id) != "done" else "")
		text(rr.position + Vector2(14, 38), mark, 26, UiKit.GOLD)
		text(rr.position + Vector2(40, 38), str(d.get("name", q)), 20, UiKit.PAPER if active or str(tabs[tab].id) == "done" else UiKit.MIST)
		if ch.quests.tracked.has(q): text(rr.position + Vector2(0, 38), "◆", 16, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_RIGHT, rr.size.x - 14)
		region(rr, "sel", q)
	)
	var right := Rect2(left.end.x + 20, content.position.y, content.end.x - left.end.x - 20, content.size.y)
	panel(right)
	if sel == "" and not ids.is_empty(): sel = str(ids[0])
	if sel == "": return
	var d2 := Game.quest.quest_def(ch, sel)
	heading(right.position + Vector2(24, 44), str(d2.get("name", sel)), right.size.x - 48)
	var y := right.position.y + 70
	var giver := Game.quest.hand_in_npc(ch, d2) if d2.has("hand_in_any") else str(d2.get("giver", ""))
	if giver != "": text(Vector2(right.position.x + 24, y + 18), Tx.t("ui.quest.from") % ContentDB.name_of("npcs", giver), 17, UiKit.MIST)
	y += 30
	var offer: Array = d2.get("offer_text", [])
	if not offer.is_empty(): y += para(Rect2(right.position.x + 24, y, right.size.x - 48, 110), str(offer[0]), 18, UiKit.PAPER, 4) + 10
	var st: Dictionary = ch.quests.active.get(sel, {})
	for i in d2.get("objectives", []).size():
		var o: Dictionary = d2.objectives[i]
		var have := int(st.get("progress", [])[i]) if not st.is_empty() else (int(o.get("count", 1)) if ch.quests.is_done(sel) else 0)
		var need := int(o.get("count", 1))
		var done := have >= need
		text(Vector2(right.position.x + 24, y + 22), ("✓ " if done else "○ ") + str(o.get("text", o.kind)) + (" (%d/%d)" % [have, need] if need > 1 else ""), 18, UiKit.BRIGHT_JADE if done else UiKit.PAPER)
		y += 28
	y += 12
	var rewards: Array = d2.get("rewards", [])
	var lines := _reward_lines(d2)
	var has_row := rewards.any(func(r): return str(r.get("kind", "")) in ["grant_item", "grant_currency"])
	if has_row or not lines.is_empty():
		text(Vector2(right.position.x + 24, y + 20), Tx.t("ui.quest.rewards"), 19, UiKit.GOLD)
		var x := right.position.x + 24
		for r in rewards:
			if r.get("kind", "") == "grant_item":
				slot_box(Rect2(x, y + 30, 52, 52), str(r.item), int(r.get("count", 1)))
				x += 58
			elif r.get("kind", "") == "grant_currency":
				x += currency_pill(Vector2(x, y + 40), str(r.currency), int(r.amount)) + 8
		var ly := y + (92 if has_row else 30)
		for line in lines:
			if ly > right.end.y - 90: break
			text(Vector2(right.position.x + 24, ly + 18), fit("· " + str(line), 17, right.size.x - 48), 17, UiKit.PALE_GOLD)
			ly += 24
	if ch.quests.is_active(sel):
		btn(Rect2(right.position.x + 24, right.end.y - 70, 200, 52), Tx.t("ui.quest.untrack") if ch.quests.tracked.has(sel) else Tx.t("ui.quest.track"), "track", sel)
		if str(d2.get("kind", "")) in ["side", "daily"]:
			btn(Rect2(right.end.x - 224, right.end.y - 70, 200, 52), Tx.t("ui.quest.abandon"), "abandon", sel)

## Rewards that are not items: what is learned or earned, and the realm-progress share (S29).
func _reward_lines(d: Dictionary) -> Array:
	var out: Array = []
	for r in d.get("rewards", []):
		match str(r.get("kind", "")):
			"learn_technique": out.append(Tx.t("ui.quest.reward_technique") % ContentDB.name_of("techniques", str(r.technique)))
			"learn_recipe": out.append(Tx.t("ui.quest.reward_recipe") % ContentDB.name_of("recipes", str(r.recipe)))
			"learn_method": out.append(Tx.t("ui.quest.reward_method") % ContentDB.name_of("methods", str(r.method)))
			"learn_secret_art": out.append(Tx.t("ui.quest.reward_secret_art") % ContentDB.name_of("secret_arts", str(r.art)))
			"grant_title": out.append(Tx.t("ui.quest.reward_title") % ContentDB.name_of("titles", str(r.title)))
			"sect_rank": out.append(Tx.t("ui.quest.reward_rank") % str(r.rank).replace("_", " ").capitalize())
			"add_contribution": out.append(Tx.t("ui.quest.reward_contribution") % int(r.amount))
			"deed":
				var dd := ContentDB.entry("karma", str(r.deed))
				if int(dd.get("merit", 0)) > 0: out.append(Tx.t("ui.quest.reward_merit") % int(dd.merit))
				if int(dd.get("fame", 0)) > 0: out.append(Tx.t("ui.quest.reward_fame") % int(dd.fame))
	var pct := float(ContentDB.curve("quest_qp_pct.%s" % str(d.get("qp", d.get("kind", "side"))), 0.0))
	if pct > 0.0: out.append(Tx.t("ui.quest.reward_progress") % int(round(pct * 100.0)))
	return out

## The activity bar: today's points toward four chests (20, 40, 60, 100), shared by every character.
func _activity(ch, r: Rect2) -> void:
	var a: Dictionary = Game.accounts.activity()
	var pts := int(a.get("points", 0))
	var tiers: Array = ContentDB.all("activity")
	var top := int(tiers.back().points) if not tiers.is_empty() else 100
	text(r.position + Vector2(0, 18), Tx.t("ui.quest.activity"), 22, UiKit.GOLD)
	text(Vector2(r.end.x - 180, r.position.y + 18), Tx.t("ui.quest.activity_points") % [pts, top], 17, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 180)
	var br := Rect2(r.position.x, r.position.y + 90, r.size.x, 20)
	bar(br, float(pts) / float(top), UiKit.GOLD)
	for tr in tiers:
		var cx: float = br.position.x + br.size.x * float(tr.points) / float(top)
		var claimed: bool = (a.get("claimed", []) as Array).has(str(tr.id))
		var ready: bool = pts >= int(tr.points) and not claimed
		var box := Rect2(clampf(cx - 24, r.position.x, r.end.x - 48), r.position.y + 34, 48, 46)
		if ready:
			var glow := 0.45 + 0.35 * sin(t * 4.0)
			draw_rect(box.grow(3), Color(UiKit.GOLD, glow), false, 3.0)
		panel(box, "minor_panel", "selected" if ready else "normal")
		var ico := Rect2(box.get_center() - Vector2(16, 16), Vector2(32, 32))
		icon_at(ico, "open")
		if not ready: draw_rect(box.grow(-2), Color(0.02, 0.05, 0.06, 0.55))
		if claimed: text(Vector2(box.position.x, box.position.y + 32), "✓", 24, UiKit.BRIGHT_JADE, HORIZONTAL_ALIGNMENT_CENTER, box.size.x)
		region(box, "chest", str(tr.id), ready, Tx.t("ui.quest.chest_locked") % int(tr.points) if not claimed else Tx.t("ui.quest.chest_claimed"))
		text(Vector2(box.position.x, br.end.y + 20), str(int(tr.points)), 15, UiKit.PALE_GOLD if pts >= int(tr.points) else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, box.size.x)
	para(Rect2(r.position.x, br.end.y + 26, r.size.x, 40), Tx.t("ui.quest.activity_note"), 14, UiKit.MIST, 2)

func on_action(id: String, data) -> void:
	match id:
		"chest": submit({"type": "claim_activity_chest", "tier": str(data)})
		"sel": sel = str(data)
		"_tab": sel = ""
		"track": submit({"type": "track_quest", "quest": str(data)})
		"abandon": ask(Tx.t("ui.quest.abandon_this_quest_you_can"), "abandon_yes", data, true)
		"abandon_yes": submit({"type": "abandon_quest", "quest": str(data)})
