class_name HudLayout
extends HudPart
## Where the HUD's controls stand and which show now: the thumb's cluster (its rings and the places on them), ring 2 as
## the moment fills it, the hit circles and the rects the world's names keep off, the points badges, and the rest and
## fight states that fold and open the fan.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## Every fixed place of the right-hand cluster from its ring and angle (mockups 01 and 02), mirrored when left-handed.
func place_cluster() -> void:
	hud.attack_center = mirror_x(Vector2(1165, 605))
	hud.jump_center = on_ring(hud.attack_center, Hud.RING1_R, Hud.JUMP_DEG)
	hud.guard_center = on_ring(hud.attack_center, Hud.RING1_R, Hud.DODGE_DEG)
	hud.slots = range(Hud.SKILL_DEG.size()).map(func(i): return on_ring(hud.attack_center, float(Hud.SKILL_R[i]), float(Hud.SKILL_DEG[i])))
	hud.fan_center = on_ring(hud.attack_center, Hud.RING2_R, Hud.FAN_DEG)
	hud.page_center = mirror_x(Vector2(1240, 672))

func mirror_x(p: Vector2) -> Vector2:
	return Vector2(1280.0 - p.x, p.y) if hud.left_handed else p

## The point `r` from `center` at `deg` (screen degrees, mirrored when left-handed), on whole pixels unless `exact`.
func on_ring(center: Vector2, r: float, deg: float, exact := false) -> Vector2:
	var v := Vector2.from_angle(deg_to_rad(deg)) * r
	if hud.left_handed: v.x = -v.x
	return center + v if exact else (center + v).round()

## Rest and fight (P5a): a foe near folds the fan and brings out the healing slot and the treasures; with none near
## for FIGHT_HOLD_S the fan opens again if the player left it open. The techniques and Attack stay out either way
## (decision 42).
func tick_fight(delta: float) -> void:
	var near := fight_now()
	hud.fight_left = Hud.FIGHT_HOLD_S if near else maxf(0.0, hud.fight_left - delta)
	var now := near or hud.fight_left > 0.0
	if not hud._settled:
		hud._settled = true
		hud.fight = now
		hud.fan_open = hud.fan_rest_open and not now
	elif now != hud.fight:
		hud.fight = now
		hud.fan_open = false if hud.fight else hud.fan_rest_open

func fight_now() -> bool:
	if hud.fight_override != null: return bool(hud.fight_override)
	if not hud.bound(): return true
	return WorldLabels.fight_near(Game.active(), hud.player.plane) or enemy_close() or foe_engaged()

## Tests and previews: hold the HUD at rest or in a fight, the fan open or closed.
## Test hook: rules_tests, tutorial_order, the top-down suite and the captures.
func set_state(in_fight: bool, open := false) -> void:
	hud.fight_override = in_fight
	hud.fight = in_fight
	hud.fight_left = 0.0
	hud.fan_open = open
	hud._settled = true

## A technique slot that holds a technique (an empty or locked slot is not drawn, review G3).
func slot_filled(slot: int) -> bool:
	if not hud.bound(): return true
	var c = Game.active()
	if slot >= ProgressionRules.technique_slot_count(c) or slot >= c.cultivator.technique_slots.size(): return false
	var tid = c.cultivator.technique_slots[slot]
	return tid != null and str(tid) != ""

## The techniques are out: once the HUD shows them, at rest as in a fight (decision 42).
func skills_live() -> bool:
	return hud.shown("skills")

## The page tab shows with the techniques once the second page is open.
func page_tab_shown(c) -> bool:
	return skills_live() and (not hud.bound() or Unlocks.is_unlocked(c.id, "technique_page_2"))

## The fan's toggles the player has, each with its role and its place while the fan is open.
func fan_items() -> Array:
	var out: Array = []
	for id in Hud.FAN_TOGGLES:
		if not hud.shown(id): continue
		var deg: float = Hud.FAN_DEG_OPEN[out.size()]
		var at := on_ring(hud.fan_center, Hud.FAN_R, deg)
		out.append({"id": id, "role": Hud.FAN_ROLE[id], "center": at, "deg": deg})
		hud.set(str(Hud.FAN_ROLE[id]) + "_center", at)
	return out

## A toggle that is on: Cultivate while meditating, the Presence held, the Sphere raised.
func toggle_on(c, id: String) -> bool:
	if c == null: return false
	match id:
		"cultivate": return c.cultivator.meditating
		"presence": return Game.field.is_on(c.id)
		"sphere": return Game.field.sphere_on(c.id)
	return false

## The toggles pinned beside the closed fan: the ones that are on (decision 20: the fan shows them while closed).
func pins(c) -> Array:
	if not hud.bound(): return ["presence"] if hud.shown("presence") else []
	return Hud.FAN_TOGGLES.filter(func(id): return hud.shown(id) and toggle_on(c, id))

func treasure_id(c, slot: int) -> String:
	var tid := str(c.inventory.treasures[slot])
	return "" if tid == "" or c.inventory.count(tid) <= 0 else tid   # sold or stored: the slot is empty again

## Ring 2 beside the fan as it stands now: [{role, center, deg, toggle}]. While the fan is closed, a toggle that is on;
## in a fight, the healing slot, the Draught and the treasures that hold something; at rest, the healing slot while it
## holds something to drink or a quest step asks for it (Granny's Remedy: the player must see where the tea goes), clear
## of the open fan; the context whenever the world offers something in reach (decision 42: its own button, at rest as in
## a fight) and, at rest beside a node, the post chip; the weapon swap when there is a spare. An empty slot is not drawn
## (mockup 01).
func ring2(c) -> Array:
	var items: Array = []
	var loose := not hud.bound()
	if not loose and c == null: return items
	if not hud.fan_open:
		for id in pins(c): items.append({"role": Hud.FAN_ROLE[id], "home": "pin" if items.is_empty() else "", "toggle": id})
	if hud.fight and not hud.fan_open:
		# Decision 45: the three quick slots, each while it holds something (every one unbound).
		for qi in Hud.QUICK_SLOTS:
			if hud.shown("quick_use") and (loose or str(c.inventory.quick[qi]) != ""): items.append({"role": "quick:%d" % qi, "home": "quick:%d" % qi})
		if has_draught(): items.append({"role": "draught", "home": ""})
		for ti in 2:
			if hud.shown("treasure_%d" % (ti + 1)) and (loose or treasure_id(c, ti) != ""): items.append({"role": "treasure:%d" % ti, "home": "treasure:%d" % ti})
	elif not hud.fight and not loose and hud.shown("quick_use"):
		for qi in Hud.QUICK_SLOTS:
			if c.inventory.count(str(c.inventory.quick[qi])) > 0 or (qi == 0 and quick_asked(c)): items.append({"role": "quick:%d" % qi, "home": "quick:%d" % qi})
	if context_shown(): items.append({"role": "context", "home": "context"})
	if post_chip(): items.append({"role": "post", "home": "post"})
	if hud.shown("weapon_swap") and (loose or c.inventory.loadout.get("spare") != null): items.append({"role": "swap", "home": "swap"})
	var fan_at: Array = fan_items().map(func(f): return f.center) if hud.fan_open else []
	return ring2_places(items, Hud.RING2_DEG.filter(func(d): return fan_at.any(func(p): return (p as Vector2).distance_to(on_ring(hud.attack_center, Hud.RING2_R, float(d))) < 60.0)))

## Places on ring 2 for `items` ([{role, home}]): each takes its home if it is free, the rest the next free place in
## order (never one of `taken`, the places the open fan covers). Decision 45: past ring 2's free places the rest stand
## on the outer row (RING3_DEG), in order; past both (a load no state makes), the last spread over the outer row.
func ring2_places(items: Array, taken: Array = []) -> Array:
	var out: Array = []
	var deg := {}
	var outer := {}
	var free: Array = Hud.RING2_DEG.filter(func(d): return not taken.has(d))
	for i in items.size():
		var home := str(items[i].get("home", ""))
		if Hud.RING2_HOME.has(home) and free.has(Hud.RING2_HOME[home]):
			deg[i] = Hud.RING2_HOME[home]
			free.erase(Hud.RING2_HOME[home])
	var row3: Array = Hud.RING3_DEG.duplicate()
	for i in items.size():
		if deg.has(i): continue
		if not free.is_empty(): deg[i] = free.pop_front()
		else:
			outer[i] = true
			deg[i] = row3.pop_front() if not row3.is_empty() else lerpf(Hud.RING3_DEG[0], Hud.RING3_DEG[-1], float(i % 4) / 3.0)
	for i in items.size():
		var o: Dictionary = items[i].duplicate()
		o.deg = float(deg[i])
		o.center = on_ring(hud.attack_center, Hud.RING3_R if outer.has(i) else Hud.RING2_R, float(deg[i]))
		out.append(o)
	return out

## Every round control the HUD shows now, as a hit circle {role, center, drawn, r}. The hud_suite in rules_tests holds
## the table to HIT_MIN and the drawn radius + 4.
## `badges`: the points badges showing (the HUD's frame passes its own, _frame_badges), else asked now.
func hit_targets(badges = null) -> Array:
	var out: Array = []
	var add := func(role: String, center: Vector2, drawn: float, hit := 0.0) -> void:
		out.append({"role": role, "center": center, "drawn": drawn, "r": maxf(maxf(Hud.HIT_MIN, drawn + 4.0), hit)})
	var c = Game.active()
	if hud.shown("attack"): add.call("attack", hud.attack_center, 66.0, 74.0)
	if hud.shown("jump"): add.call("jump", hud.jump_center, Hud.JUMP_R)
	if hud.shown("guard"): add.call("guard", hud.guard_center, 26.0)
	if skills_live():
		# A technique's round button (decision 43): `drawn` its radius, its hit circle a little past it.
		for i in hud.slots.size():
			if slot_filled(i + hud.skill_page * 4): add.call("skill", hud.slots[i], Hud.TILE * 0.5, Hud.TILE * 0.5 + 6.0)
	if page_tab_shown(c): add.call("page", hud.page_center, 24.0)
	var fan := fan_items()
	if not fan.is_empty():
		add.call("fan", hud.fan_center, 26.0)
		if hud.fan_open:
			for f in fan: add.call(str(f.role), f.center, 26.0)
	for it in ring2(c): add.call(str(it.role), it.center, Hud.CTX_R if str(it.role) == "context" else 26.0)
	for ic in hud.icon_row:
		if hud.shown(ic[0]): add.call("icon:" + str(ic[0]), ic[1], 26.0)
	for pc in party_chips(c): add.call("pets:" + str(pc.kind) + ":" + str(pc.uid), pc.center, float(pc.r))
	if auto_hunt_shown(c): add.call("auto_hunt", hud.auto_center, 26.0)
	for pb in (point_badges(c) if badges == null else badges): add.call("points:" + str(pb.id), pb.center, 16.0, Hud.POINTS_PITCH * 0.5)
	return out

## The points badges showing now, in POINT_SYSTEMS order: {id, count, center, page, tab}. Bound only (the counts are
## the character's); a system not yet unlocked or with nothing to spend has none.
func point_badges(c) -> Array:
	var out: Array = []
	if c == null or not hud.bound() or not hud.shown("player_panel"): return out
	var panel := panel_rect(c)
	for row in Hud.POINT_SYSTEMS:
		if not Unlocks.is_unlocked(c.id, str(row.unlock)): continue
		var n := int(hud.points_override[row.id]) if hud.points_override.has(row.id) else int(Game.get(str(row.count[0])).call(str(row.count[1]), c))
		if n <= 0: continue
		out.append({"id": str(row.id), "count": n, "page": str(row.page), "tab": str(row.tab),
			"center": Vector2(panel.end.x - 22.0 - out.size() * Hud.POINTS_PITCH, panel.position.y + 2.0)})
	return out

## The points badges for the HUD's own frame (its tick, the rects the world's names keep off, its drawing), worked out
## once a frame: each asks every system for its count, and the Realisations' walks the technique trees (a tenth of the
## HUD's frame, three times over). Asked again when the game moves on (Game.revision), the frame is another or a test's
## override changes; point_badges itself always asks afresh.
func frame_badges() -> Array:
	var c = Game.active() if hud.bound() else null
	return hud._badges_memo.value([c.get_instance_id() if c is Object else 0, hud.points_override], _work_badges.bind(c))

func _work_badges(c) -> Array:
	hud._badges = point_badges(c)
	return hud._badges

## Each frame: a badge newly shown starts its pop, and (after the first look) writes its line to the log. `badges`: the
## frame's (_frame_badges), else asked now.
func tick_points(badges = null) -> void:
	var now := {}
	for pb in (point_badges(Game.active() if hud.bound() else null) if badges == null else badges):
		now[pb.id] = true
		if not hud._points_seen.has(pb.id):
			hud._points_seen[pb.id] = hud.t
			if hud._points_primed: hud.add_log(Tx.t("hud.points_" + str(pb.id)), UiKit.PALE_GOLD)
	for id in hud._points_seen.keys():
		if not now.has(id): hud._points_seen.erase(id)
	hud._points_primed = hud.bound()

## A badge's pop: how far in (0 .. 1) since it appeared, 1 at once with Reduce motion.
func points_pop(id: String) -> float:
	if UiKit.reduce_motion(): return 1.0
	return clampf((hud.t - float(hud._points_seen.get(id, -99.0))) / Hud.POINTS_POP_S, 0.0, 1.0)

## The screen rects the HUD covers now (its round controls as drawn, its panels and plates), which the world's names
## keep clear of (G4). `badges`: the points badges as hit_targets takes them.
func obstacle_rects(badges = null) -> Array:
	var out: Array = []
	# Asked with the frame's badges (the HUD's own frame): the frame's targets, shared with the tutorial coach's anchors.
	for tg in (hud.tours.tour_targets() if badges != null and is_same(badges, hud._badges) else hit_targets(badges)):
		var d := float(tg.drawn) + 2.0
		out.append(Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0))
	var c = Game.active()
	if hud.shown("player_panel"): out.append(panel_rect(c))
	if hud.shown("minimap"): out.append(hud.minimap_rect)
	if hud.tracker_rect.size.x > 0.0: out.append(hud.tracker_rect)
	if hud.purse_rect.size.x > 0.0: out.append(hud.purse_rect)
	if hud.status_rect.size.x > 0.0 and hud.shown("player_panel"): out.append(hud.status_rect)
	if not hud.equip_prompt.current.is_empty(): out.append(EquipPrompt.RECT)
	if hud.top_stack.room_boss() != null: out.append(Rect2(400, 92, 480, 84))
	if context_shown(): out.append(context_label_rect())
	var log_r := log_rect()
	if log_r.size.x > 0.0: out.append(log_r)
	return out

## The log's rows as they stand (none when it is empty): the world's labels keep off them while they show (the
## polish pass saw a boarlet's plate across "Codex: Body training").
func log_rect() -> Rect2:
	var lines := hud.log_lines if hud.shown("system_log") else hud.log_lines.filter(func(l): return l.get("always", false))
	var rows := hud.panels.log_rows(lines)
	var n := rows.size()
	if n == 0: return Rect2()
	var w := 0.0
	for r in rows: w = maxf(w, float(r.indent) + UiKit.text_width(str(r.text), 16, true))
	var x := 20.0 if not hud.left_handed else 1280.0 - 20.0 - Hud.LOG_W   # where _draw_log draws it
	return Rect2(x, Hud.LOG_FOOT - (n - 1) * 21.0 - 16.0, minf(w, Hud.LOG_W), (n - 1) * 21.0 + 22.0)

## The player panel, one row taller once the Soul bar shows: it draws there, and the whole of it opens Character.
func panel_rect(c) -> Rect2:
	var soul_row: bool = c != null and c.pools.max_soul > 0.0 and hud.shown("soul_bar")
	return Rect2(16, 16, 360, 120 if soul_row else 104)

## A tracker line's go button hit area: 48 x 48 round the drawn button (P4 §7).
static func go_hit(drawn: Rect2) -> Rect2:
	return Rect2(drawn.get_center() - Vector2(24, 24), Vector2(48, 48))

## S43 rule 5: an enemy aggroed on the player within 400 makes a fight (the Attack button attacks either way since
## decision 42; Climb and Enter are on the context's own button).
func enemy_close() -> bool:
	if Game.room_rt == null or not is_instance_valid(hud.player): return false
	for e in Game.room_rt.living_enemies():
		if e.team != "enemy" or e.def.get("passive", false): continue
		if str(e.ai.get("state", "")) in ["aggro", "windup", "attack", "recover"] and e.plane.distance_to(hud.player.plane) < 400.0: return true
	return false

## A fight now: the P5a rest/fight state (a foe within the fight range, one engaged with you anywhere in the room, which
## is also one attacking you or struck a moment ago, and FIGHT_HOLD_S after).
func in_fight_now() -> bool:
	return hud.fight or fight_now()

## A foe engaged with the player anywhere in the room: turned on them, striking, recovering, fleeing (EnemyState.in_fight).
func foe_engaged() -> bool:
	if Game.room_rt == null: return false
	return Game.room_rt.living_enemies().any(func(e): return e.team == "enemy" and not e.def.get("passive", false) and e.in_fight())

## The context's own button on ring 2 (decision 42): whatever the world offers in reach, at rest as in a fight, and a
## harvest it began while it waits for its tap.
func context_shown() -> bool:
	return not hud.context.is_empty() or hud.tapping.object != ""

## S50 Keeping Post: beside a node, out of a fight, the Keep Post button shows. One character is enough: the post works
## while the game is put away, or for an incense stick burnt at it.
func post_chip() -> bool:
	return hud.bound() and str(hud.context.get("type", "")) in ["herb_patch", "ore_vein", "fishing_spot", "insect_swarm"] and not in_fight_now() \
		and Unlocks.is_unlocked(Game.active_id, "keeping_post")

func has_draught() -> bool:
	var c = Game.active()
	return c != null and c.inventory.draught != null

## The party chips beside the player panel (mockup 01): the animals beside you (the active one first) and the fellow
## disciples, each a 48 px ring with its face, an HP arc and its name under it; then the animals in the Spirit Beast Bag
## (tap to swap one in, never in a fight) and the mount (tap to ride or walk). An animal opens Spirit Animals, a disciple
## Companions.
func party_chips(c) -> Array:
	var specs: Array = []
	if c == null or not hud.shown("player_panel"): return specs
	var seen := {}
	if hud.shown("pet"):
		var act: Dictionary = Game.pets.active_pet(c)
		if not act.is_empty():
			specs.append({"kind": "active", "uid": str(act.uid), "name": str(act.get("name", ""))})
			seen[str(act.uid)] = true
		for p in Game.pets.party(c):
			if seen.has(str(p.uid)): continue
			specs.append({"kind": "party", "uid": str(p.uid), "name": str(p.get("name", ""))})
			seen[str(p.uid)] = true
	for cid in c.companions.get("active", []):
		specs.append({"kind": "companion", "uid": str(cid), "name": ContentDB.name_of("companions", str(cid))})
	if hud.shown("pet"):
		for uid in c.pet_bag:
			var bp: Dictionary = Game.pets._pet(c, str(uid))
			if bp.is_empty() or seen.has(str(uid)) or str(uid) == c.active_pet: continue
			specs.append({"kind": "bag", "uid": str(uid), "name": str(bp.get("name", ""))})
			seen[str(uid)] = true
		if not Game.pets.mount_pet_of(c).is_empty(): specs.append({"kind": "mount", "uid": str(c.mount_pet), "name": ""})
	for i in specs.size():
		specs[i].center = Vector2(408.0 + i * 60.0, 44.0)
		specs[i].r = 24.0
	return specs

func auto_hunt_shown(c) -> bool:
	return c != null and hud.bound() and Unlocks.is_unlocked(c.id, "idle_tasks") and (Game.world.auto_hunting(c.id) or Game.world.auto_hunt_block(c) == "")

## The context button's words under it, as wide as the ring leaves them (CTX_LABEL_W).
func context_label_rect() -> Rect2:
	return Rect2(hud.context_center.x - Hud.CTX_LABEL_W * 0.5, hud.context_center.y + Hud.CTX_R + 2.0, Hud.CTX_LABEL_W, 18.0)

## A quest step asks for the healing slot: to put something in it, or to use what it holds (Granny's Remedy).
func quick_asked(c) -> bool:
	return Game.quest.asks_for(c, "use_system", "set_quick_use") or Game.quest.asks_for(c, "use_item", str(c.inventory.quick_use))
