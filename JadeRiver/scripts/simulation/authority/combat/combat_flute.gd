class_name CombatFlute
extends CombatPart
## CombatAuthority's part for the flute's melody (S47 v1.1, the Music path). Hold Attack with a flute to channel a
## melody aura: every half second it slows the foes around you and may confuse them, and you and your allies
## (companions, pets) recover a little health, while Composure drains. It ends on release, when Composure runs out, or
## when you are stunned, wounded, attack, use a technique or change weapon. State: `combat.melody` (not saved).

func channel_melody(c, on: bool) -> Dictionary:
	if not on:
		end_melody(c, "released")
		return ok({"on": false})
	var ch: Dictionary = StatRules.family(c).get("channel", {})
	if ch.is_empty(): return fail("wrong_weapon", {"text": Tx.t("sim.combat.melody_needs_flute")})
	if not Unlocks.is_unlocked(c.id, "composure"): return fail("locked", {"text": Unlocks.locked_text("composure")})
	if combat.melody.has(c.id): return ok({"on": true})
	var reason := combat.can_act(c)
	if reason != "": return fail(reason)
	if combat.climbing(c.id) or combat.flying.has(c.id): return fail("busy")
	var tl := combat.timeline(c.id)
	if combat.is_busy(c.id):
		# The note of the tap flies first; then the hands settle into the melody.
		if tl.technique != "" or not tl.hit_done: return fail("busy")
		tl.action = ""
		tl.queued = 0
	if c.pools.composure < float(ch.get("min_composure", 5)): return fail("no_composure", {"text": Tx.t("sim.combat.melody_no_composure")})
	combat.melody[c.id] = {"next": float(ch.get("tick_s", 0.5)) * 0.5}
	emit("melody_changed", {"actor": c.id, "on": true, "reason": "played"})
	return ok({"on": true})

func is_playing(actor_id: String) -> bool:
	return combat.melody.has(actor_id)

func end_melody(c, why: String) -> void:
	if c == null or not combat.melody.has(c.id): return
	combat.melody.erase(c.id)
	emit("melody_changed", {"actor": c.id, "on": false, "reason": why})

func tick_melody(c, delta: float) -> void:
	if not combat.melody.has(c.id): return
	var ch: Dictionary = StatRules.family(c).get("channel", {})
	if ch.is_empty():
		end_melody(c, "weapon")
		return
	if combat.wounded.has(c.id) or c.pools.blocked("attack") or combat.is_busy(c.id) or combat.flying.has(c.id):
		end_melody(c, "broken")
		return
	var m: Dictionary = combat.melody[c.id]
	var note := StatRules.set_flag(c, "sustained_note")
	m.played = float(m.get("played", 0.0)) + delta
	if m.played > float(note.get("free_s", 0.0)):
		var cost := float(ch.get("composure_per_s", 8)) * float(ProgressionRules.path_flag(c, "channel_cost_mult", 1.0)) * delta
		combat.apply_resource_change(c.id, "composure", -cost, "melody", 0.0, true)
	c.pools.since_composure_use = 0.0
	if c.pools.composure <= 0.0:
		end_melody(c, "composure")
		return
	m.next = float(m.next) - delta
	if float(m.next) > 0.0: return
	var tick := float(ch.get("tick_s", 0.5))
	m.next = tick
	var pv := combat.player_view(c)
	var at := Vector2(float(pv.x), float(pv.y))
	# Each tier of the Music Dao carries the melody 5% further.
	var radius := float(ch.get("radius", 220)) * (1.0 + 0.05 * combat._dao_tier(c, "music"))
	var rng := Rng.stream(c.id, "melody")
	var power: float = 1.0 + c.stats.value("melody_power")
	var ally_heal: float = (float(ch.get("ally_heal_pct", 0.02)) + float(note.get("ally_heal", 0.0))) * power
	var foes := 0
	var allies := 0
	if game.room_rt != null:
		for e in game.room_rt.living_enemies():
			if e.plane.distance_to(at) > radius: continue
			if e.team == "ally":
				if e.pools.hp < e.pools.max_hp:
					e.pools.hp = minf(e.pools.max_hp, e.pools.hp + e.pools.max_hp * ally_heal * tick)
				allies += 1
				continue
			if e.hidden or e.ai.get("surrendered", false): continue
			foes += 1
			var sl: Dictionary = ch.get("slow", {})
			if not sl.is_empty() and not e.pools.steadfast.has("slow"):
				combat._apply_status_to_enemy(e, {"id": "slow", "power": minf(0.9, float(sl.get("power", 0.3)) * power), "remaining": float(sl.get("duration_s", 1.2)), "source": c.id})
			if not e.is_boss() and not e.pools.steadfast.has("confusion") and not e.pools.has_status("confusion") \
					and rng.randf() < float(ch.get("confusion_chance", 0.08)):
				combat._apply_status_to_enemy(e, {"id": "confusion", "power": 1.0, "remaining": float(ch.get("confusion_s", 1.5)), "source": c.id})
	var self_heal: float = c.pools.max_hp * float(ch.get("self_heal_pct", 0.01)) * tick * power * (1.0 + c.stats.value("healing_received"))
	if self_heal > 0.0 and c.pools.hp < c.pools.max_hp: combat.apply_resource_change(c.id, "hp", self_heal, "melody", 0.0, true)
	emit("melody_pulse", {"actor": c.id, "x": at.x, "y": at.y, "radius": radius, "foes": foes, "allies": allies})
