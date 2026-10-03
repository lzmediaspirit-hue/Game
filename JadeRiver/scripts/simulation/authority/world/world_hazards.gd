class_name WorldHazards
extends WorldPart
## WorldAuthority's part: hazards (S17) and hazard volumes (S43): a room's hazards cycle through cooldown, tell, warn
## and active, and strike, push or pulse as their kind says, scaled by how well the answering attribute meets the room's
## need.

## Every hazard starts part-way into its cooldown, so nothing strikes on arrival.
func init_hazards(c, rt: RoomRuntime) -> void:
	rt.hazards.clear()
	rt.hazard_drift = Vector2.ZERO
	if rt.def.get("safe", false): return
	var rng := Rng.stream(c.id, "world")
	for hid in rt.def.get("hazards", []):
		var h := ContentDB.entry("hazards", str(hid))
		if h.is_empty(): continue
		rt.hazards[str(hid)] = {"phase": "cooldown", "t": 0.0, "dur": rng.randf_range(2.0, 2.0 + HazardRules.duration(h, "cooldown")),
			"spots": [], "dir": 1, "pulse": 0.0, "inside": false}

## S43 hazard volumes (lava, spores, poison vents): status and damage each pulse while inside their rect and altitude.
func tick_hazard_volumes(c, rt: RoomRuntime, st: ActorState, delta: float) -> void:
	if rt.geometry.volumes.is_empty() or game.combat.is_wounded(c.id) or c.pools.has_status("spawn_protection"): return
	for v in rt.geometry.volumes_at(st.plane, st.altitude):
		if str(v.kind) != "hazard": continue
		var key := "hazard_vol:" + str(v.id)
		var left := float(rt.hazard_pulse.get(key, 0.0)) - delta
		if left > 0.0:
			rt.hazard_pulse[key] = left
			continue
		rt.hazard_pulse[key] = float(v.get("pulse_s", 1.0))
		var amount := 0.0
		if float(v.get("damage_pct", 0.0)) > 0.0:
			amount = game.combat.apply_hazard_damage(c, c.pools.max_hp * float(v.damage_pct), str(v.get("damage_type", "physical")),
				str(v.get("element", "none")), "hazard:" + str(v.id))
		var sd: Dictionary = v.get("status", {})
		if not sd.is_empty(): game.combat.apply_status(c.id, str(sd.id), float(sd.get("s", 2.0)), float(sd.get("power", 1.0)))
		emit("hazard_struck", {"actor": c.id, "room": rt.room_id, "hazard": str(v.get("hazard", v.id)), "amount": int(round(maxf(0.0, amount))),
			"share": 1.0, "answered": false, "stat": "", "need": 0, "have": 0})

## The push the room puts on a character this tick (gusts, currents); the presentation adds it to walking.
func hazard_drift(actor_id: String) -> Vector2:
	if game.room_rt == null or actor_id != game.active_id: return Vector2.ZERO
	return game.room_rt.hazard_drift

func tick_hazards(c, rt: RoomRuntime, st: ActorState, delta: float) -> void:
	rt.hazard_drift = Vector2.ZERO
	if rt.hazards.is_empty() or st == null: return
	# The cycle keeps running; its effects wait while the character is down or just arrived.
	var calm: bool = game.combat.is_wounded(c.id) or c.pools.has_status("spawn_protection")
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		hs.t = float(hs.t) + delta
		if float(hs.t) >= float(hs.dur): _hazard_advance(c, rt, st, h, hs, calm)
		_hazard_hold(c, rt, st, h, hs, delta, calm)

## Next phase, skipping phases of zero length (a thicket is always active).
func _hazard_advance(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, calm: bool) -> void:
	var rng := Rng.stream(c.id, "world")
	for i in HazardRules.PHASES.size():
		hs.phase = HazardRules.next_phase(str(hs.phase))
		hs.t = 0.0
		hs.dur = HazardRules.duration(h, str(hs.phase))
		if hs.phase == "cooldown": hs.dur = float(hs.dur) * rng.randf_range(0.8, 1.2)
		if float(hs.dur) <= 0.0: continue
		hazard_enter(c, rt, st, h, hs, rng, calm)
		return
	# Every phase but "active" is empty: a constant hazard.
	hs.phase = "active"
	hs.dur = HazardRules.duration(h, "active")
	hazard_enter(c, rt, st, h, hs, rng, calm)

func hazard_enter(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, rng: RandomNumberGenerator, calm: bool) -> void:
	match str(hs.phase):
		"tell":
			hs.dir = int(h.get("dir", -1 if rng.randf() < 0.5 else 1))
			hs.spots = hazard_spots(rt, st, h, rng)
		"warn":
			if str(h.get("aim", "")) == "player": hs.spots = [[st.plane.x, st.plane.y, st.altitude]]
			emit("hazard_warned", {"actor": c.id, "room": rt.room_id, "hazard": str(h.id), "spots": hs.spots, "dir": int(hs.dir)})
		"active":
			hs.pulse = 0.0
			match str(h.kind):
				"strike":
					var r := float(h.get("radius", 60))
					# A blow lands on its own floor: the side view's reach up and down, one level on the height grid.
					var band := 90.0 if WorldAuthority.side_view(rt) else TopdownRoom.LEVEL
					for sp in hs.spots:
						var at := Vector2(float(sp[0]), float(sp[1]))
						if st.plane.distance_to(at) <= r and absf(st.altitude - float(sp[2])) < band:
							_hazard_hit(c, rt, h, calm)
							break
				"aura":
					if not _sheltered(rt, st, h): _hazard_hit(c, rt, h, calm)
				"gust":
					_hazard_hit(c, rt, h, calm)

## Debug tools (S38): hold every hazard of the room part-way into a phase, for previews. Nothing strikes.
func debug_hazard_phase(phase: String, k: float) -> void:
	var rt: RoomRuntime = game.room_rt
	var c = game.active()
	if rt == null or c == null or not phase in HazardRules.PHASES: return
	var st: ActorState = game.actor_state(c.id)
	var rng := Rng.stream(c.id, "world")
	for hid in rt.hazards:
		var h := ContentDB.entry("hazards", str(hid))
		var hs: Dictionary = rt.hazards[hid]
		hs.phase = "tell"
		hazard_enter(c, rt, st, h, hs, rng, true)
		if phase != "tell":
			hs.phase = "warn"
			hazard_enter(c, rt, st, h, hs, rng, true)
		hs.phase = phase
		hs.dur = maxf(HazardRules.duration(h, phase), 2.0)
		hs.t = clampf(k, 0.0, 0.95) * float(hs.dur)

## Strikes land around (or on) the character; the first spot is always close.
func hazard_spots(rt: RoomRuntime, st: ActorState, h: Dictionary, rng: RandomNumberGenerator) -> Array:
	if str(h.kind) != "strike": return []
	var out: Array = []
	var spread := float(h.get("spread", 0))
	for i in int(h.get("count", 1)):
		var reach := spread * (0.35 if i == 0 else 1.0)
		if not WorldAuthority.side_view(rt):
			# On the height grid the strikes fall all round on the plane, on floors inside the room, at the floor's height.
			var q: Vector2 = st.plane + Vector2.from_angle(rng.randf() * TAU) * reach * sqrt(rng.randf())
			var g := rt.topdown.nearest_standable(q.clamp(Vector2.ONE * TopdownRoom.TILE, Vector2(rt.topdown.w - 1, rt.topdown.h - 1) * TopdownRoom.TILE))
			out.append([g.x, g.y, rt.topdown.floor_at(g)])
			continue
		var p := Vector2(clampf(st.plane.x + rng.randf_range(-reach, reach), 80.0, rt.width() - 80.0),
			clampf(st.plane.y + rng.randf_range(-50.0, 50.0), 660.0, 940.0))
		var s := world.ground_at(rt, p)
		out.append([p.x, p.y, s.height_at(p) if s else 0.0])
	return out

## Is the character on the floor, within `tol` of it (not jumping over a pool or a current): the ground in the side
## view, the floor under it on the height grid, so a pool on the square acts on a body on the terrace only on its own.
func _on_hazard_floor(rt: RoomRuntime, st: ActorState, tol: float) -> bool:
	if WorldAuthority.side_view(rt): return st.altitude < tol
	return absf(st.altitude - rt.topdown.floor_at(st.plane)) < tol

## Hazards that act for as long as they are active: gusts and currents push, pools pulse.
func _hazard_hold(c, rt: RoomRuntime, st: ActorState, h: Dictionary, hs: Dictionary, delta: float, calm: bool) -> void:
	var active: bool = hs.phase == "active"
	match str(h.kind):
		"gust":
			if active and not calm:
				var push := float(h.get("push", 200)) * _hazard_share(c, rt, h)
				if st.flying: push *= float(ContentDB.stat_const("hazard.flyer_push", 1.5))
				rt.hazard_drift += Vector2(float(hs.dir) * push, 0.0)
		"flow":
			var inside := false
			for a in HazardRules.areas(h, rt.def):
				if HazardRules.rect(a).has_point(st.plane) and _on_hazard_floor(rt, st, 2.0):
					inside = true
					if not calm:
						var flow := float(a.get("current", -60)) * (float(h.get("surge", 2.0)) if active else 1.0)
						rt.hazard_drift += Vector2(flow * _hazard_share(c, rt, h), 0.0)
			# A surge that catches you is reported once, when you enter it or it rises around you.
			if active and inside and not hs.inside: _hazard_hit(c, rt, h, calm)
			hs.inside = inside and active
		"pool":
			if not active: return
			hs.pulse = float(hs.pulse) - delta
			if float(hs.pulse) > 0.0: return
			hs.pulse = float(h.get("pulse", 1.0))
			for a in HazardRules.areas(h, rt.def):
				if HazardRules.rect(a).has_point(st.plane) and _on_hazard_floor(rt, st, 10.0):
					_hazard_hit(c, rt, h, calm)
					return

## How much of a push or status gets through this character's answer.
func _hazard_share(c, rt: RoomRuntime, h: Dictionary) -> float:
	return HazardRules.effect_scale(c.stats.value(str(h.answer)), float(HazardRules.need(h, rt.def)))

func _sheltered(rt: RoomRuntime, st: ActorState, h: Dictionary) -> bool:
	var kinds: Array = h.get("shelter", [])
	if kinds.is_empty(): return false
	var r := float(ContentDB.stat_const("hazard.shelter_radius", 220))
	for o in rt.def.get("objects", []):
		if str(o.get("type", "")) in kinds:
			var at: Array = o.get("at", [0, 0])
			if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) <= r: return true
	return false

## One blow of a hazard on the character: damage, status, buff and Hollowing, each scaled by
## how well the answering attribute meets the room's need.
func _hazard_hit(c, rt: RoomRuntime, h: Dictionary, calm: bool) -> void:
	if calm: return
	var need_v := float(HazardRules.need(h, rt.def))
	var have: float = c.stats.value(str(h.answer))
	var share := HazardRules.effect_scale(have, need_v)
	var amount := 0.0
	if float(h.get("damage_pct", 0.0)) > 0.0:
		# A blow to the soul is measured against the Soul pool it lands on, not against HP.
		var pool_max: float = c.pools.max_soul if str(h.get("damage_type", "")) == "soul" and c.pools.max_soul > 0.0 else c.pools.max_hp
		amount = game.combat.apply_hazard_damage(c, pool_max * float(h.damage_pct) * HazardRules.damage_scale(have, need_v),
			str(h.get("damage_type", "physical")), str(h.get("element", "none")), "hazard:" + str(h.id))
		if amount < 0.0: return   # dodged
	var sd: Dictionary = h.get("status", {})
	if not sd.is_empty() and share > 0.0:
		var by_time := str(sd.get("scale", "power")) == "duration"
		game.combat.apply_status(c.id, str(sd.id), float(sd.s) * (share if by_time else 1.0), float(sd.power) * (1.0 if by_time else share))
	var bd: Dictionary = h.get("buff", {})
	if not bd.is_empty() and share > 0.0:
		game.combat.apply_buff(c.id, {"stat": str(bd.stat), "op": str(bd.get("op", "pct_add")), "value": float(bd.value) * share,
			"duration": HazardRules.duration(h, "active") + 1.0, "source": "hazard:" + str(h.id)}, "hazard")
	if float(h.get("hollowing", 0.0)) > 0.0 and share > 0.0:
		game.combat.apply_resource_change(c.id, "hollowing", float(h.hollowing) * share, "hazard")
	# The Starsea's star wind strips Qi before it touches the body (Starsea survival, Sage 3).
	if float(h.get("qi_drain_pct", 0.0)) > 0.0 and share > 0.0 and c.pools.max_qi > 0.0:
		game.combat.apply_resource_change(c.id, "qi", -c.pools.max_qi * float(h.qi_drain_pct) * share, "hazard")
	emit("hazard_struck", {"actor": c.id, "room": rt.room_id, "hazard": str(h.id), "amount": int(round(amount)), "share": share,
		"answered": share <= 0.0, "stat": str(h.answer), "need": int(need_v), "have": int(have)})
