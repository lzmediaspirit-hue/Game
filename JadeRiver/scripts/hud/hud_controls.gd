class_name HudControls
extends HudPart
## Drawing the thumb's cluster: Attack and its drag moves, Jump and Dodge, the techniques' round buttons and their page,
## the fan and its toggles, ring 2 (the pins, the quick slots, the Draught, the treasures, the context, Keeping Post,
## the swap), the harvest ring, the pet wheel and the stick.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

func draw_pet_wheel(c) -> void:
	if not hud.pet_wheel: return
	hud.draw_circle(hud.pet_center, 152.0, Color(UiKit.PLATE, 0.86))
	hud.draw_arc(hud.pet_center, 152.0, 0, TAU, 64, Color(UiKit.GOLD, 0.6), 2.0)
	var cur := str(Game.pets.commands.get(c.id, "follow"))
	for i in Hud.PET_WHEEL.size():
		var id := str(Hud.PET_WHEEL[i])
		var pos := hud.input.wheel_pos(i)
		var on := i == hud.pet_pick
		var active := id == cur
		hud.ring(pos, 34, on)
		if active: hud.draw_arc(pos, 38, 0, TAU, 32, UiKit.GOLD, 2.0)
		var label := Tx.t("hud.pet_cmd_" + id)
		if id == "ride": label = Tx.t("hud.pet_cmd_dismount") if c.mount_pet != "" and c.riding else Tx.t("hud.pet_cmd_ride")
		UiKit.draw_outlined(hud, label, pos + Vector2(-44, 6), 16, UiKit.GOLD if on else (UiKit.PALE_GOLD if active else UiKit.PAPER), HORIZONTAL_ALIGNMENT_CENTER, 88)
	UiKit.draw_outlined(hud, Tx.t("hud.pet_cmd_title"), hud.pet_center + Vector2(-150, -162), 18, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 300)

func skill_position(index: float) -> Vector2:
	var low := clampi(int(floor(index)), 0, 2)
	return hud.slots[low].lerp(hud.slots[low + 1], index - low)

## Decision 42: a technique as the Techniques tree's node picture (TechniquePicture), the card's miniature: the whole
## character at x1 in the art's pose in its element's ink, the form's mark beside it and its rank badge. Decision 43: a
## round button TILE px across (TechniquePicture.draw_round: an ink rim, the bright jade ring, the picture cut to the
## circle, the badge inside it). Closed (the weapon in hand cannot use it), a slate ring, the picture dim and a lock;
## cooling, the radial sweep (an ink pie from the top round, the ring dim over the part to wait) and its seconds, then a
## flash of the ring as it is ready again (READY_S); short of Qi, the picture dimmed and a Qi arc along its foot. An
## empty or locked slot is not drawn (G3).
func draw_skill_slot(center: Vector2, slot: int, opacity: float) -> void:
	var rad := Hud.TILE * 0.5
	if not hud.bound():
		hud.draw_circle(center, rad, Color(UiKit.INK, opacity))
		hud.draw_arc(center, rad - 3.0, 0.0, TAU, 48, Color(UiKit.BRIGHT_JADE, opacity), TechniquePicture.RING - 1.0, true)
		hud.draw_circle(center, rad - TechniquePicture.RING, Color(UiKit.JADE_SHADOW, opacity))
		return
	if not hud.layout.slot_filled(slot): return
	var c = Game.active()
	var tid := str(c.cultivator.technique_slots[slot])
	var tdef := ContentDB.entry("techniques", tid)
	var fam := str(StatRules.family(c).get("id", "fists"))
	var closed: bool = str(tdef.get("family", "any")) != "any" and not (str(tdef.family) == fam or (str(tdef.family) == "fists" and fam == "gauntlets"))
	var cd: float = c.pools.cooldown("tech:" + tid)
	var cost: float = Game.combat.technique_cost(c, tdef)
	var short: bool = not closed and cd <= 0.0 and c.pools.max_qi > 0 and c.pools.qi < cost
	var frame := UiKit.HOLLOW if closed else UiKit.BRIGHT_JADE
	TechniquePicture.draw_round(hud, center, rad, tid, c, _look(c), frame, 0.45 if closed else (0.72 if short else 1.0), opacity, "hud")
	if closed: TechniquePicture.draw_lock_round(hud, center, rad, opacity)
	if cd > 0.0:
		hud._cooling[tid] = true
		TechniquePicture.draw_cooldown_round(hud, center, rad, cd / maxf(0.1, float(tdef.get("cooldown_s", 5))), cd, opacity)
	else:
		if hud._cooling.has(tid):
			hud._cooling.erase(tid)
			hud._ready_at[tid] = hud.t
		if short: TechniquePicture.draw_qi_short_round(hud, center, rad, c.pools.qi / maxf(1.0, cost), opacity)
		var since := hud.t - float(hud._ready_at.get(tid, -99.0))
		if since < Hud.READY_S and not closed: TechniquePicture.draw_ready_round(hud, center, rad, since / Hud.READY_S, opacity, UiKit.reduce_motion())

## The character's look for the techniques' pictures, found once a frame.
func _look(c) -> Dictionary:
	return hud._look_now.value(null, func(): return InventoryAuthority.outfit_for(c))

## A cooldown's dark sweep over a ring's face, `frac` of the way round from the top.
func _sweep(center: Vector2, r: float, frac: float, opacity := 1.0) -> void:
	if frac <= 0.02: return
	var pts := PackedVector2Array([center])
	for i in 25: pts.append(center + Vector2.from_angle(-PI / 2 + TAU * frac * (i / 24.0)) * r)
	hud.draw_colored_polygon(pts, Color(UiKit.INK, 0.6 * opacity))

## The techniques of the page on ring 1, at rest as in a fight (decision 42). A page turn slides both pages along the
## arc.
func draw_skill_scroll() -> void:
	if hud.scroll_progress >= 1:
		for i in hud.slots.size():
			var slot := i + hud.skill_page * 4
			if hud.bound() and not hud.layout.slot_filled(slot): continue
			draw_skill_slot(hud.slots[i], slot, 1.0)
		return
	var tt := hud.scroll_progress * hud.scroll_progress * (3 - 2 * hud.scroll_progress)
	var shift := -hud.scroll_direction * 4.0 * tt
	var old_page := (hud.skill_page + 1) % 2
	for page in 2:
		for i in 4:
			var index := i + shift + (hud.scroll_direction * 4 if page == 1 else 0)
			if index < -0.35 or index > 3.35: continue
			var fade := minf(clampf((index + 0.35) / 0.35, 0, 1), clampf((3.35 - index) / 0.35, 0, 1))
			draw_skill_slot(skill_position(index), i + (old_page if page == 0 else hud.skill_page) * 4, fade)

## A number in the corner of a ring (a count, the Presence's level): a dark pill at its lower right (the kit's .k-corner).
func _corner(at: Vector2, s: String, col := UiKit.PAPER) -> void:
	var w := maxf(22.0, UiKit.text_width(s, 14) + 10.0)
	var cen := at + Vector2(21, 21)
	UiKit.pill(hud, Rect2(cen - Vector2(w * 0.5, 11), Vector2(w, 22)), UiKit.INK)
	UiKit.draw_text(hud, s, Vector2(cen.x - w * 0.5, cen.y + 5), 14, col, HORIZONTAL_ALIGNMENT_CENTER, w)

## The harvest ring (S45): it shrinks from wide to the context's button, where the harvest began (decision 42); the gold
## band is the perfect window for your rank.
func draw_tap_ring() -> void:
	var at := hud.context_center
	var inner := Hud.CTX_R - 6.0
	var outer := inner + 70.0
	var f := clampf(float(hud.tapping.t) / maxf(0.01, float(hud.tapping.ring)), 0.0, 1.0)
	var at_f := func(x: float) -> float: return lerpf(outer, inner, clampf(x, 0.0, 1.0))
	var lo: float = at_f.call(float(hud.tapping.target) + float(hud.tapping.window) * 0.5)
	var hi: float = at_f.call(float(hud.tapping.target) - float(hud.tapping.window) * 0.5)
	hud.draw_circle(at, outer + 6.0, Color(UiKit.PLATE, 0.55))
	hud.draw_arc(at, outer + 6.0, 0, TAU, 64, Color(UiKit.GOLD, 0.35), 1.5)
	hud.draw_arc(at, (lo + hi) * 0.5, 0, TAU, 64, Color(UiKit.GOLD, 0.55), maxf(2.0, hi - lo))
	hud.draw_arc(at, lo, 0, TAU, 64, UiKit.GOLD, 1.5)
	hud.draw_arc(at, hi, 0, TAU, 64, UiKit.GOLD, 1.5)
	var in_band := f >= float(hud.tapping.target) - float(hud.tapping.window) * 0.5 and f <= float(hud.tapping.target) + float(hud.tapping.window) * 0.5
	hud.draw_arc(at, at_f.call(f), 0, TAU, 64, UiKit.PALE_GOLD if in_band else UiKit.BRIGHT_JADE, 4)
	UiKit.draw_outlined(hud, Tx.t("hud.tap_now"), at + Vector2(-90, -outer - 18), 20, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 180)

## A harvest tap's word over the context's button for a moment after it lands (S45: perfect, or a miss).
func draw_tap_words() -> void:
	for k in ["tap:perfect", "tap:miss"]:
		if hud.pulses.has(k): UiKit.draw_outlined(hud, Tx.t("hud." + k.replace(":", "_")), hud.context_center + Vector2(-90, -Hud.CTX_R - 58), 22,
			UiKit.GOLD if k == "tap:perfect" else UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, 180)

## The stick under the left thumb while it is down, and in the prologue's first seconds the line that says to drag there.
func draw_stick() -> void:
	if hud.joystick_id != -999:
		hud.draw_arc(hud.joystick_origin, 76, 0, TAU, 40, Color(1, 1, 1, 0.12), 2)
		hud.draw_circle(hud.joystick_origin + (hud.joystick_pos - hud.joystick_origin).limit_length(76), 18, Color(1, 1, 1, 0.14))
	if not Game.is_revealed("hud:joystick_hint_done") and Game.active().quests.has_flag("prologue_active") and hud.t < 12.0:
		UiKit.draw_outlined(hud, Tx.t("hud.drag_on_the_left_half"), Vector2(40, 470), 20, Color(UiKit.PAPER, 0.6 + 0.4 * sin(hud.t * 3.0)), HORIZONTAL_ALIGNMENT_CENTER, 560)

## The glyph of what the context offers (talk, gather, enter...), on its own button on ring 2.
func context_glyph() -> String:
	if hud.context.is_empty() and hud.tapping.object != "": return "gather"
	return {"npc": "talk", "herb_patch": "gather", "ore_vein": "mine", "fishing_spot": "fish", "chest": "open", "storage_chest": "open",
		"portal": "enter", "climbable": "enter", "cooking_pot": "cook", "alchemy_furnace": "alchemy", "earth_vent": "alchemy", "forge_anvil": "forge", "star_sight": "gather",
		"chart_table": "forge", "shipyard_slip": "forge", "starsea_dock": "enter", "mercy": "talk", "insect_swarm": "gather",
		"beast_trail": "gather", "ancestral_altar": "open"}.get(str(hud.context.get("type", "")), "open")

## The verb and its target under the context's button (mockup 02: "Talk · Peddler Ning").
func _context_line(c) -> String:
	var verb := str(hud.context.get("label", ""))
	var who := ""
	if str(hud.context.get("npc", "")) != "": who = ContentDB.name_of("npcs", str(hud.context.npc))
	elif hud.context.has("portal") and str(hud.context.get("target", "")) != "": who = ContentDB.name_of("rooms", str(hud.context.target))
	return (Tx.t("hud.context_target") % [verb, who] if who != "" and verb != "" else verb) + hud.actions.node_plate(c)

func draw(c) -> void:
	_draw_fan(c)
	_draw_ring2(c)
	# Ring 1: jump, the techniques (out at rest as in a fight, decision 42), dodge.
	if hud.shown("jump"):
		hud.ring(hud.jump_center, Hud.JUMP_R, false, 1.0, hud.pulses.has("hud:jump"))
		hud.glyph("jump", hud.jump_center)
	if hud.shown("guard"):
		hud.ring(hud.guard_center, 26, Game.combat.timeline(c.id).guard, 1.0, hud.pulses.has("hud:guard"), hud.guard_pressed)
		hud.glyph("dodge" if Unlocks.is_unlocked(c.id, "dodge_dash") else "guard", hud.guard_center, 32)
		var dcd = c.pools.cooldown("dodge")
		if dcd > 0: hud.draw_arc(hud.guard_center, 22, -PI / 2, -PI / 2 + TAU * (1.0 - dcd / 2.5), 20, UiKit.MIST, 3)
	if hud.shown("skills"): draw_skill_scroll()
	if hud.layout.page_tab_shown(c): _draw_page_tab()
	# The attack button: the weapon in hand's glyph, always (decision 42: what the world offers has its own button).
	if hud.shown("attack"):
		hud.ring(hud.attack_center, 66, Game.combat.is_busy(c.id) or Game.combat.is_playing(c.id), 1.0, hud.pulses.has("hud:attack"), hud.attack_pressed)
		hud.glyph(attack_glyph(c), hud.attack_center, 64)
	if hud.input.aims(): _draw_attack_moves()

## The Attack button's face: the weapon family's glyph, never a context's (decision 42).
func attack_glyph(c) -> String:
	return str(StatRules.family(c).get("hud_glyph", "fist"))

## S49 auto-hunt: a small toggle under the icon row, only in rooms where idle Hunt is allowed.
func draw_auto_hunt(c) -> void:
	if not hud.layout.auto_hunt_shown(c): return
	var on: bool = Game.world.auto_hunting(c.id)
	hud.ring(hud.auto_center, 26, on)
	if on: hud.draw_arc(hud.auto_center, 29, fmod(hud.t * 3.0, TAU), fmod(hud.t * 3.0, TAU) + PI * 1.2, 24, UiKit.GOLD, 3.0)
	hud.glyph("jian", hud.auto_center + Vector2(0, -4), 32)
	UiKit.draw_outlined(hud, Tx.t("hud.auto_hunt"), hud.auto_center + Vector2(-40, 23), 14, UiKit.GOLD if on else UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 80)

## How strongly an armed move's mark is lit this frame: a slow pulse, steady under Reduce motion.
func armed_glow() -> float:
	return 1.0 if UiKit.reduce_motion() else 0.8 + 0.2 * sin(hud.t * 8.0)

## Decision 35: while a thumb is on Attack in the top-down room the button shows its drag moves. On the ground, once the
## thumb leaves the dead circle, the finisher's line round the button (pulled in near the screen's edges), lit gold
## when the drag crosses it. In the air, when the body can plunge, the Plunge's sector under the button, lit gold when
## the drag is in it. Held still, a ring fills toward the guard; guarding, the button is ringed in jade (gold for a
## stance). The armed move's name stands over the button, above ring 1's gap. Nothing pulses under Reduce motion.
func _draw_attack_moves() -> void:
	var g := hud.input.attack_gesture()
	if g == null or not hud.input.moves_live(): return
	var mv := hud.input.armed(g)
	var glow := armed_glow()
	var gold := UiKit.GOLD
	var jade := UiKit.BRIGHT_JADE
	var air: bool = not hud.player.motor.grounded
	if not air and g.strayed and not g.guarding:
		var pts := PackedVector2Array()
		for i in 73:
			var d := Vector2.from_angle(TAU * i / 72.0)
			pts.append(g.origin + d * g.long_px(d))
		var lit := mv == "finisher"
		hud.draw_polyline(pts, Color(gold, 0.95 * glow) if lit else Color(UiKit.PAPER, 0.4), 4.0 if lit else 1.5, true)
	if air and hud.player.plunge_ready():
		var half := deg_to_rad(float(TopdownAim.cfg("plunge_deg", 35)))
		var r0 := float(TopdownAim.cfg("plunge_px", 48))
		var r1 := g.edge_room(Vector2.DOWN)
		var sector := PackedVector2Array()
		for i in 13: sector.append(g.origin + Vector2.DOWN.rotated(lerpf(-half, half, i / 12.0)) * r0)
		for i in 13: sector.append(g.origin + Vector2.DOWN.rotated(lerpf(half, -half, i / 12.0)) * r1)
		var lit := mv == "plunge"
		hud.draw_colored_polygon(sector, Color(gold, 0.3 * glow) if lit else Color(UiKit.PAPER, 0.1))
		sector.append(sector[0])
		hud.draw_polyline(sector, Color(gold, 0.95) if lit else Color(UiKit.PAPER, 0.4), 3.0 if lit else 1.5, true)
		var tip := g.origin + Vector2(0, r0 + 18.0)
		hud.draw_colored_polygon(PackedVector2Array([tip + Vector2(-9, -6), tip + Vector2(9, -6), tip + Vector2(0, 5)]), Color(gold, 0.95) if lit else Color(UiKit.PAPER, 0.5))
	var hold_s := float(TopdownAim.cfg("hold_s", 0.18))
	var guard_s := float(TopdownAim.cfg("guard_s", 0.3))
	if g.guarding:
		hud.draw_arc(g.origin, 72.0, 0, TAU, 64, gold if g.guard_kind == "stance" else jade, 5.0)
	elif not g.strayed and not g.refused and g.t > hold_s:
		var k := clampf((g.t - hold_s) / maxf(0.01, guard_s - hold_s), 0.0, 1.0)
		hud.draw_arc(g.origin, 72.0, -PI / 2, -PI / 2 + TAU * k, 48, Color(jade, 0.85), 3.0)
	var word := str({"finisher": "hud.move_finisher", "plunge": "hud.move_plunge"}.get(mv, ""))
	if mv == "guard": word = "hud.move_stance" if g.guard_kind == "stance" else "hud.move_guard"
	if word != "":
		var col := jade if mv == "guard" and g.guard_kind != "stance" else gold
		UiKit.draw_outlined(hud, Tx.t(word), g.origin + Vector2(-80, -76), 18, col, HORIZONTAL_ALIGNMENT_CENTER, 160)

## The technique page tab (mockup 01): "1/2" in a small ring; a tap turns the page (so does a swipe on the ring).
func _draw_page_tab() -> void:
	hud.ring(hud.page_center, 24, false, 1.0, hud.pulses.has("hud:technique_page"))
	var one := str(hud.skill_page + 1)
	var w1 := UiKit.text_width(one, 16)
	var x0 := hud.page_center.x - (w1 + UiKit.text_width("/2", 14)) * 0.5
	UiKit.draw_text(hud, one, Vector2(x0, hud.page_center.y + 6), 16, UiKit.PALE_GOLD)
	UiKit.draw_text(hud, "/2", Vector2(x0 + w1, hud.page_center.y + 6), 14, UiKit.MIST)

## The fan (decision 20; mockups 01 and 02). Closed: one button with a chevron, lit gold when Cultivate is (the
## bottleneck) or a toggle inside is new; the toggles that are on stand pinned beside it on ring 2. Open: a paper fan
## behind the toggles with their names; in a fight a toggle taken from it folds it again.
func _draw_fan(c) -> void:
	var items := hud.layout.fan_items()
	if items.is_empty(): return
	var gold: bool = c.cultivator.state == "bottleneck"
	if hud.fan_open:
		_draw_paper_fan(items)
		for f in items:
			var at: Vector2 = f.center
			_draw_toggle(c, str(f.id), at)
			var cap := Tx.t("hud.fan_" + str(f.id))
			var lit: bool = str(f.id) == "cultivate" and gold
			var beside: bool = float(f.deg) < 230.0
			if beside and not hud.left_handed: UiKit.draw_outlined(hud, cap, Vector2(at.x - 34 - 160, at.y + 5), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_RIGHT, 160)
			elif beside: UiKit.draw_outlined(hud, cap, Vector2(at.x + 34, at.y + 5), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_LEFT, 160)
			else: UiKit.draw_outlined(hud, cap, Vector2(at.x - 80, at.y - 34), 14, UiKit.PALE_GOLD if lit else UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 160)
		hud.ring(hud.fan_center, 26, false, 1.0, false, true)
	else:
		var fresh := Hud.FAN_TOGGLES.any(func(id): return hud.pulses.has("hud:" + str(id)))
		hud.ring(hud.fan_center, 26, false, 1.0, gold or fresh)
		var tip := hud.fan_center + Vector2(0, -30)
		var chev := PackedVector2Array([tip + Vector2(-6, 6), tip + Vector2(6, 6), tip + Vector2(0, -1)])
		hud.draw_colored_polygon(PackedVector2Array([tip + Vector2(-8, 7), tip + Vector2(8, 7), tip + Vector2(0, -3)]), UiKit.INK)
		hud.draw_colored_polygon(chev, UiKit.GOLD if gold else UiKit.PALE_GOLD)
	hud.glyph("fan", hud.fan_center, 32, UiKit.GOLD if gold and not hud.fan_open else Color.WHITE)

## The open fan's paper (mockup 02): a sector behind the toggles with its ribs and a pale rim.
func _draw_paper_fan(items: Array) -> void:
	var d0: float = float(items[0].deg) - 5.0
	var d1: float = maxf(float(items[items.size() - 1].deg) + 7.0, d0 + 40.0)   # a fan of one or two still opens like a fan
	var arc := PackedVector2Array()
	for i in 25: arc.append(hud.layout.on_ring(hud.fan_center, Hud.PAPER_R, lerpf(d0, d1, i / 24.0), true))
	var sector := PackedVector2Array([hud.fan_center]) + arc
	hud.draw_colored_polygon(sector, Color(UiKit.PAPER, 0.13))
	for i in items.size() + 1: hud.draw_line(hud.fan_center, hud.layout.on_ring(hud.fan_center, Hud.PAPER_R, lerpf(d0, d1, float(i) / items.size()), true), Color(UiKit.BRONZE, 0.55), 1.5)
	hud.draw_polyline(sector + PackedVector2Array([hud.fan_center]), Color(UiKit.GOLD, 0.55), 2.0)
	hud.draw_polyline(arc, Color(UiKit.PALE_GOLD, 0.5), 3.0)

## One of the fan's toggles, in the open fan or pinned on ring 2: lit while it is on.
func _draw_toggle(c, id: String, at: Vector2) -> void:
	match id:
		"cultivate":
			var gold: bool = c.cultivator.state == "bottleneck"
			hud.ring(at, 26, c.cultivator.meditating, 1.0, gold or hud.pulses.has("hud:cultivate"), hud.cultivate_pressed)
			if gold: hud.draw_arc(at, 32 + sin(hud.t * 4.0) * 2, 0, TAU, 40, Color(UiKit.GOLD, 0.6), 3)
			hud.glyph("cultivate", at, 32, UiKit.GOLD if gold else Color.WHITE)
			if hud.cultivate_pressed and hud.cultivate_hold > 0.1:
				hud.draw_arc(at, 30, -PI / 2, -PI / 2 + TAU * hud.cultivate_hold / 0.6, 30, UiKit.PALE_GOLD, 3)
		"presence":
			# Held, its Soul upkeep runs round it as an arc (mockup 01); its level in the corner.
			var held: bool = Game.field.is_on(c.id)
			hud.ring(at, 26, held, 1.0, hud.pulses.has("hud:presence"))
			if held and c.pools.max_soul > 0.0: hud.draw_arc(at, 31, -PI / 2, -PI / 2 + TAU * clampf(c.pools.soul / c.pools.max_soul, 0.0, 1.0), 32, UiKit.SOUL, 3)
			hud.glyph("presence", at, 32, UiKit.PALE_GOLD if held else Color.WHITE)
			_corner(at, str(Game.field.presence_level(c)))
		"sphere":
			var raised: bool = Game.field.sphere_on(c.id)
			hud.ring(at, 26, raised, 1.0, hud.pulses.has("hud:sphere"))
			hud.glyph("sphere", at, 32, UiKit.PALE_GOLD if raised else Color.WHITE)
		"sense":
			hud.ring(at, 26, false, 1.0, hud.pulses.has("hud:sense"))
			hud.glyph("sense", at, 32)
		"pet":
			hud.ring(at, 26, false, 1.0, hud.pulses.has("hud:pet"), hud.pet_pressed)
			hud.glyph("pet", at, 32)

## Ring 2 beside the fan: the pinned toggles, the healing slot, the Draught, the treasures, the context or the post chip
## and the weapon swap, each where `_ring2` puts it.
func _draw_ring2(c) -> void:
	for it in hud.layout.ring2(c):
		var at: Vector2 = it.center
		match str(it.role):
			"quick:0", "quick:1", "quick:2": _draw_quick(c, at, int(str(it.role).right(1)))
			"draught": _draw_draught(c, at)
			"treasure:0", "treasure:1": _draw_treasure(c, int(str(it.role).get_slice(":", 1)), at)
			"context":
				# Decision 42: its own button, at rest as in a fight, lit gold; a harvest's hold runs round it.
				hud.context_center = at
				hud.ring(at, Hud.CTX_R, false, 1.0, true)
				hud.glyph(context_glyph(), at, 32)
				if hud.channel.object != "":
					hud.draw_arc(at, Hud.CTX_R - 3.0, -PI / 2, -PI / 2 + TAU * clampf(hud.channel.t / maxf(0.01, hud.channel.dur), 0, 1), 32, UiKit.BRIGHT_JADE, 4)
				var lr := hud.layout.context_label_rect()
				UiKit.draw_outlined(hud, UiKit.fit(_context_line(c), 14, lr.size.x, true), Vector2(lr.position.x, lr.position.y + 14), 14, UiKit.PALE_GOLD,
					HORIZONTAL_ALIGNMENT_CENTER, lr.size.x)
			"post":
				hud.context_center = at
				var mine: bool = Game.posts.at_post(c) and str(Game.posts.post_of(c).get("object", "")) == str(hud.context.get("object", ""))
				hud.ring(at, 26, mine, 1.0, hud.pulses.has("hud:post"))
				hud.glyph("post", at, 32, UiKit.BRIGHT_JADE if mine else Color.WHITE)
				UiKit.draw_outlined(hud, Tx.t("hud.keep_post"), at + Vector2(-60, 44), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 120)
			"swap": _draw_swap(c, at)
			_: _draw_toggle(c, str(it.get("toggle", "")), at)

## A quick slot (mockup 01's healing slot; decision 45: three of them): the item at its native 32, how many are left in
## the corner, its own cooldown group's shade. While a quest step asks for the first, it glows and names itself as the
## step does ("Quick-use"); empty, a tap opens the Bag.
func _draw_quick(c, at: Vector2, slot := 0) -> void:
	var qid := str(c.inventory.quick[slot])
	var asked := slot == 0 and hud.layout.quick_asked(c)
	hud.ring(at, 26, false, 1.0, hud.pulses.has("hud:quick_use") or asked)
	if asked: UiKit.draw_outlined(hud, Tx.t("hud.quick_use"), at + Vector2(-50, 44), 14, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_CENTER, 100)
	if qid == "": return
	var n: int = c.inventory.count(qid)
	hud.glyph(qid, at, 32, Color(1, 1, 1, 1.0 if n > 0 else 0.4))
	var def := ContentDB.item(qid)
	var cd: float = c.pools.cooldown("item:" + str(def.get("pill", def.get("food", {})).get("group", "utility")))
	if cd > 0: hud.draw_circle(at, 22, Color(UiKit.INK, 0.5))
	_corner(at, str(n), UiKit.PAPER if n > 0 else UiKit.RED_TEXT)

## S44: the Draught slot, with the minutes left before the liquid goes flat.
func _draw_draught(c, at: Vector2) -> void:
	var dr: Dictionary = c.inventory.draught
	hud.ring(at, 26)
	hud.glyph(str(dr.id), at, 32)
	var left: float = Game.inventory.draught_left(c)
	hud.draw_arc(at, 29, -PI / 2, -PI / 2 + TAU * left / float(ContentDB.item(str(dr.id)).get("draught", {}).get("expires_s", 600)), 32, UiKit.BRIGHT_JADE, 3)
	_corner(at, str(int(dr.count)))

func _draw_treasure(c, ti: int, at: Vector2) -> void:
	var tid := hud.layout.treasure_id(c, ti)
	hud.ring(at, 26, false, 1.0, hud.pulses.has("hud:treasure_%d" % (ti + 1)))
	if tid == "": return
	var tdef: Dictionary = CombatAuthority.treasure_of(tid)
	var short: bool = c.pools.qi < float(tdef.get("qi", 0)) or c.pools.soul < CombatAuthority.treasure_soul_cost(c, tdef)
	hud.glyph(tid, at, 32, Color(1, 1, 1, 0.4 if short else 1.0))
	var tcd: float = c.pools.cooldown("treasure:" + tid)
	if tcd > 0.05:
		_sweep(at, 24.0, clampf(tcd / maxf(1.0, float(tdef.get("cooldown_s", 20))), 0.0, 1.0))
		UiKit.draw_outlined(hud, str(int(ceil(tcd))), at + Vector2(-20, 7), 16, UiKit.PAPER, HORIZONTAL_ALIGNMENT_CENTER, 40)
	if tdef.has("charges"):
		# A talisman treasure shows the charges it has left.
		var ti_bag: int = c.inventory.first_index(tid)
		_corner(at, "×%d" % (int(c.inventory.bag[ti_bag].get("charges", int(tdef.charges))) if ti_bag >= 0 else 0), UiKit.PALE_GOLD)

## S47: the spare weapon's icon under two turning arrows, and which loadout is in hand.
func _draw_swap(c, at: Vector2) -> void:
	var spare = c.inventory.loadout.get("spare")
	hud.ring(at, 26, false, 1.0, hud.pulses.has("hud:weapon_swap"))
	if spare != null: hud.glyph(str(spare.id), at, 32, Color(1, 1, 1, 0.9))
	for side in [-1.0, 1.0]:
		hud.draw_arc(at, 21, PI * (0.15 if side > 0 else 1.15), PI * (0.75 if side > 0 else 1.75), 10, Color(UiKit.PALE_GOLD, 0.9 if spare != null else 0.35), 2.0)
	UiKit.draw_outlined(hud, str(c.inventory.loadout.get("active", "a")).to_upper(), at + Vector2(10, 27), 16, UiKit.PALE_GOLD, HORIZONTAL_ALIGNMENT_LEFT, 20)
