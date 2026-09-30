extends "res://scripts/simulation/authority/world/world_part.gd"
## World · rooftop chases and timed routes (S43 rule 15): a thief to catch over the roofs before he is over the far
## wall, and a route (the Cloud Steps) to run against the clock and the week's rivals. The runs under way are the
## authority's `chases` and `runs`.

## Where a rooftop thief is `t` seconds into his run: {x, y, alt, moving, done, facing}. His route is waypoints
## [x, y, alt, wait_s]: he waits at each, then runs to the next at `speed` along the plane (a climb counts half its
## height). He stands at the last one until its wait is over, and then he is gone.
static func chase_point(route: Array, speed: float, t: float) -> Dictionary:
	var left := maxf(0.0, t)
	var facing := 1
	for i in route.size():
		var w: Array = route[i]
		var wait := float(w[3]) if w.size() > 3 else 0.0
		if left <= wait or i == route.size() - 1:
			return {"x": float(w[0]), "y": float(w[1]), "alt": float(w[2]), "moving": false, "done": i == route.size() - 1 and left > wait, "facing": facing}
		left -= wait
		var n: Array = route[i + 1]
		var d := Vector2(float(n[0]) - float(w[0]), float(n[1]) - float(w[1])).length() + absf(float(n[2]) - float(w[2])) * 0.5
		var leg := maxf(0.15, d / maxf(1.0, speed))
		facing = 1 if float(n[0]) >= float(w[0]) else -1
		if left <= leg:
			var k := left / leg
			return {"x": lerpf(float(w[0]), float(n[0]), k), "y": lerpf(float(w[1]), float(n[1]), k), "alt": lerpf(float(w[2]), float(n[2]), k),
				"moving": true, "done": false, "facing": facing}
		left -= leg
	return {"x": 0.0, "y": 0.0, "alt": 0.0, "moving": false, "done": true, "facing": facing}

## How long a thief's whole run lasts, in seconds.
static func chase_length(route: Array, speed: float) -> float:
	var total := 0.0
	for i in route.size():
		var w: Array = route[i]
		total += float(w[3]) if w.size() > 3 else 0.0
		if i + 1 < route.size():
			var n: Array = route[i + 1]
			var d := Vector2(float(n[0]) - float(w[0]), float(n[1]) - float(w[1])).length() + absf(float(n[2]) - float(w[2])) * 0.5
			total += maxf(0.15, d / maxf(1.0, speed))
	return total

func chase_done_today(c, object_id: String) -> bool:
	return int(c.cooldowns.get("chase_" + object_id, -1)) == Clock.reset_day(Clock.now_utc())

## The thief in the active character's chase, for the street to draw: {object, x, y, alt, moving, facing} or {}.
func chase_view(c) -> Dictionary:
	var ch: Dictionary = world.chases.get(c.id, {}) if c != null else {}
	if ch.is_empty() or game.room_rt == null or game.room_rt.room_id != str(ch.room): return {}
	var o: Dictionary = game.room_rt.object_def(str(ch.object))
	var p := chase_point(o.chase.route, float(o.chase.get("speed", 260)), game.sim_time - float(ch.start))
	p.object = str(ch.object)
	return p

## Speaking to the thief sends him running over the roofs. Catch him (reach him at his height) before he is over
## the far wall. One chase a street a day, caught or not.
func start_chase(c, o: Dictionary) -> Dictionary:
	var oid := str(o.id)
	if chase_done_today(c, oid): return fail("done", {"text": Tx.t("sim.world.thief_gone")})
	if world.chases.has(c.id): return fail("busy")
	world.chases[c.id] = {"object": oid, "room": game.room_rt.room_id, "start": game.sim_time}
	emit("chase_started", {"actor": c.id, "object": oid, "room": game.room_rt.room_id,
		"seconds": chase_length(o.chase.route, float(o.chase.get("speed", 260)))})
	return ok({"text": Tx.t("sim.world.thief_runs")})

func tick_chase(c, rt: RoomRuntime, st: ActorState) -> void:
	var ch: Dictionary = world.chases.get(c.id, {})
	if ch.is_empty(): return
	var o: Dictionary = rt.object_def(str(ch.object)) if rt.room_id == str(ch.room) else {}
	if o.is_empty():
		_end_chase(c, ch, false)   # you left the street: he is away over the roofs
		return
	var k: Dictionary = o.chase
	var el: float = game.sim_time - float(ch.start)
	var p := chase_point(k.route, float(k.get("speed", 260)), el)
	if st != null and el >= float(k.get("grace_s", 0.8)) and st.plane.distance_to(Vector2(float(p.x), float(p.y))) <= float(k.get("catch_px", 80)) \
			and absf(st.altitude - float(p.alt)) <= float(k.get("catch_alt", 40)):
		_end_chase(c, ch, true, o)
	elif p.done:
		_end_chase(c, ch, false, o)

func _end_chase(c, ch: Dictionary, caught: bool, o: Dictionary = {}) -> void:
	world.chases.erase(c.id)
	c.cooldowns["chase_" + str(ch.object)] = Clock.reset_day(Clock.now_utc())
	var secs: float = snappedf(game.sim_time - float(ch.start), 0.1)
	if caught:
		game.apply_effects(c.id, o.chase.get("rewards", []), "thief_chase")
		emit("thief_caught", {"actor": c.id, "object": str(ch.object), "room": str(ch.room), "seconds": secs})
	else:
		emit("thief_escaped", {"actor": c.id, "object": str(ch.object), "room": str(ch.room)})

## A timed route (the Cloud Sect's Cloud Steps): touch the stone to start, reach the finish before the limit.
func start_run(c, o: Dictionary) -> Dictionary:
	if world.runs.has(c.id) and str(world.runs[c.id].object) == str(o.id): return fail("busy", {"text": Tx.t("sim.world.run_on")})
	world.runs[c.id] = {"object": str(o.id), "room": game.room_rt.room_id, "start": game.sim_time}
	emit("route_started", {"actor": c.id, "route": str(o.route.id), "room": game.room_rt.room_id, "limit": float(o.route.get("limit_s", 90))})
	return ok({"text": Tx.t("sim.world.run_go")})

## The week's board for a route: its rivals' times, the same on every device (the account seed and the week).
func route_board(route: Dictionary, week: int) -> Array:
	var r := CalendarRules.draw(game.calendar.cal_seed(), "route:" + str(route.id), week)
	var span: Array = route.get("rival_s", [30, 60])
	var out: Array = []
	for name in route.get("rivals", []): out.append({"name": str(name), "seconds": snappedf(r.randf_range(float(span[0]), float(span[1])), 0.1)})
	return out

## A character's record on a route: {week, best, paid} for this week, plus medals won for good.
func route_record(c, route_id: String) -> Dictionary:
	var rec: Dictionary = c.cooldowns.get("route_" + route_id, {})
	var week: int = game.calendar.rank_week()
	if int(rec.get("week", -1)) != week: rec = {"week": week, "best": 0.0, "paid": false, "medals": rec.get("medals", [])}
	c.cooldowns["route_" + route_id] = rec
	return rec

## Your place on this week's board with this time: 1 + the rivals who were faster.
func route_rank(route: Dictionary, week: int, seconds: float) -> int:
	var rank := 1
	for rv in route_board(route, week):
		if float(rv.seconds) < seconds: rank += 1
	return rank

func tick_run(c, rt: RoomRuntime, st: ActorState) -> void:
	var run: Dictionary = world.runs.get(c.id, {})
	if run.is_empty(): return
	var o: Dictionary = rt.object_def(str(run.object)) if rt.room_id == str(run.room) else {}
	if o.is_empty() or st == null:
		world.runs.erase(c.id)
		return
	var route: Dictionary = o.route
	var el: float = game.sim_time - float(run.start)
	if el > float(route.get("limit_s", 90)):
		world.runs.erase(c.id)
		emit("route_finished", {"actor": c.id, "route": str(route.id), "finished": false})
		return
	var fin: Dictionary = route.get("finish", {})
	var at: Array = fin.get("at", [0, 0])
	if st.plane.distance_to(Vector2(float(at[0]), float(at[1]))) > float(fin.get("radius", 70)) or st.altitude < float(fin.get("alt", 0)) - 12.0: return
	world.runs.erase(c.id)
	finish_route(c, route, snappedf(el, 0.1))

## A finished run: the week's best, its place on the board (a place in the top three pays once a week), and each
## medal's reward the first time its par is beaten.
func finish_route(c, route: Dictionary, seconds: float) -> Dictionary:
	var rec := route_record(c, str(route.id))
	if float(rec.best) <= 0.0 or seconds < float(rec.best): rec.best = seconds
	var rank := route_rank(route, int(rec.week), float(rec.best))
	var medal := ""
	var pars: Dictionary = route.get("pars", {})
	for m in ["gold", "silver", "bronze"]:
		if pars.has(m) and seconds <= float(pars[m]):
			medal = m
			break
	var medals: Array = rec.get("medals", [])
	for m in ["bronze", "silver", "gold"]:
		if medal != "" and ["bronze", "silver", "gold"].find(m) <= ["bronze", "silver", "gold"].find(medal) and not medals.has(m):
			medals.append(m)
			game.apply_effects(c.id, route.get("medal_rewards", {}).get(m, []), "route:" + str(route.id))
	rec.medals = medals
	if rank <= 3 and not rec.get("paid", false):
		rec.paid = true
		game.apply_effects(c.id, route.get("week_rewards", []), "route:" + str(route.id))
	var out := {"actor": c.id, "route": str(route.id), "finished": true, "seconds": seconds, "best": float(rec.best), "rank": rank,
		"of": (route.get("rivals", []) as Array).size() + 1, "medal": medal}
	emit("route_finished", out)
	return ok(out)
