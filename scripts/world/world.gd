# The playable side-scrolling world: loads an area, simulates player/enemies/nodes on the shared
# x/depth/height surfaces at a fixed 60 Hz, and draws everything into the low-res pixel viewport.
extends Node2D

const C = preload("res://scripts/data/content.gd")
const S = preload("res://scripts/core/state.gd")
const R = preload("res://scripts/core/rules.gd")

signal toast(text: String, kind: String)
signal dialogue(npc: String, lines: Array, menu: Array)
signal station(type: String)
signal died
signal area_loaded(id: String)
signal threat
signal trial_end(success: bool)

const BASE_Y := 180.0
const VIEW_H := 270

var ctl := Ctl.new()
var view_w := 480
var paused := false
var mode := "combat"          # combat | cultivation (UI state; never disables damage)

var area_id := ""
var A: Dictionary = {}
var W := 1500.0
var surfs: Array = []
var bg: Dictionary = {}
var floor_t: Texture2D
var rail_t: Texture2D
var lanterns: Array = []
var theme: Dictionary = {}

var pl: Actor
var enemies: Array = []
var npcs: Array = []
var nodes: Array = []
var stations: Array = []
var portals: Array = []
var runes: Array = []
var projectiles: Array = []
var fx: Array = []
var boss: Actor = null
var arena_locked := false

var cam_x := 0.0
var cam_y := 0.0
var shake := 0.0
var frame := 0
var hitstop := 0
var prompt: Dictionary = {}
var st: Dictionary = {}       # cached derived stats
var art_cd := {}              # ability id → frames remaining
var step_cd := 0
var combo := 0
var combo_queued := false
var cast: Dictionary = {}     # active art
var parry := 0
var guard_spin := 0
var harvest: Dictionary = {}  # active gather channel
var med_t := 0
var qi_acc := 0.0
var buf := {}                  # buffered inputs: key → frames left
var trial: Dictionary = {}
var trial_return: Dictionary = {}
var seal_progress := 0
var font: Font
static var node_ready_at := {}   # node id → unix time it regrows (session)


func _ready() -> void:
	font = ThemeDB.fallback_font
	pl = Actor.new()
	pl.kind = "player"
	Game.changed.connect(func(_a, _r): _refresh_stats())


func _refresh_stats() -> void:
	if Game.p.is_empty():
		return
	st = S.stats(Game.p)
	pl.max_hp = st.max_hp
	_plook = {}


# ---------------------------------------------------------------- area loading
func load_area(id: String, spawn_x := -1.0, spawn_d := -1.0) -> void:
	area_id = id
	A = C.AREAS[id]
	W = A.width
	theme = Backgrounds.theme(A.theme)
	surfs = [{"id": "ground", "kind": "ground", "x0": 0.0, "x1": W, "d0": 0.0, "d1": Physics.DEPTH_MAX, "h0": 0.0, "h1": 0.0,
		"solid": false, "oneWay": false, "rails": {"back": true, "front": true, "left": true, "right": true}}]
	for s in A.surfaces:
		var c: Dictionary = s.duplicate(true)
		for k in ["x0", "x1", "d0", "d1", "h0", "h1"]:
			c[k] = float(c[k])
		surfs.append(c)
	bg = Backgrounds.build(A.theme, int(W), view_w, hash(id) % 1000)
	floor_t = Backgrounds.floor_tex(A.theme, int(W))
	var gaps := []
	for n in A.nodes:
		if C.NODE_TYPES[n.type].sprite == "fish":
			gaps.append(float(n.x))
	var r := Backgrounds.rail(A.theme, int(W), gaps)
	rail_t = r.tex
	lanterns = r.lanterns
	# nodes
	nodes = []
	for n in A.nodes:
		var nd: Dictionary = n.duplicate()
		nd.def = C.NODE_TYPES[n.type]
		nd.surf = n.get("surface", "ground")
		nd.h = Physics.surf_h(_surf(nd.surf), float(n.x))
		nodes.append(nd)
	stations = []
	for s in A.stations:
		stations.append(s.duplicate())
	portals = A.portals.duplicate(true)
	runes = []
	for rn in A.get("runes", []):
		var rr: Dictionary = rn.duplicate()
		rr.surf = rn.get("surface", "ground")
		rr.h = Physics.surf_h(_surf(rr.surf), float(rn.x))
		rr.lit = false
		runes.append(rr)
	seal_progress = 0
	# actors
	npcs = []
	for n in A.npcs:
		var a := Actor.new()
		a.kind = "npc"
		a.type = n.id
		a.x = n.x
		a.d = n.depth
		a.facing = 1
		npcs.append(a)
	# merchant beside the shop
	for s in stations:
		if s.type == "shop":
			var m := Actor.new()
			m.kind = "npc"
			m.type = "merchant"
			m.x = s.x + 26
			m.d = s.depth + 8
			m.facing = -1
			npcs.append(m)
	enemies = []
	projectiles = []
	fx = []
	boss = null
	arena_locked = false
	var mult := 1.0 + (int(A.region) - 1) * 0.55
	for e in A.enemies:
		enemies.append(_spawn_enemy(e.type, float(e.x), float(e.depth), e.get("surface", "ground"), mult))
	if A.has("boss") and not Game.p.bosses.get(A.boss.id, false):
		boss = _spawn_enemy(A.boss.type, float(A.boss.x), float(A.boss.depth), "ground", 1.0)
		boss.boss_id = A.boss.id
		boss.spawn.respawn = false
		boss.facing = -1
		enemies.append(boss)
	# player
	_refresh_stats()
	pl.x = spawn_x if spawn_x >= 0 else float(Game.p.get("x", 200.0))
	pl.x = clampf(pl.x, 20, W - 20)
	pl.d = spawn_d if spawn_d >= 0 else clampf(float(Game.p.get("depth", 40.0)), 20, 70)
	pl.h = 0.0
	pl.surf = "ground"
	pl.grounded = true
	pl.vz = 0
	pl.alive = true
	pl.set_state("idle")
	pl.inv = 60
	harvest = {}
	cast = {}
	Game.p.area = id
	cam_x = clampf(pl.x - view_w * 0.45, 0, maxf(0, W - view_w))
	cam_y = 0
	if A.type != "trial":
		Game.perform("discover_area", {"area": id})
	area_loaded.emit(id)
	queue_redraw()


func _surf(id: String) -> Dictionary:
	for s in surfs:
		if s.id == id:
			return s
	return surfs[0]


func _spawn_enemy(type: String, x: float, dd: float, surf_id: String, mult: float) -> Actor:
	var e := Actor.new()
	e.kind = "enemy"
	e.type = type
	e.def = C.ENEMIES[type]
	e.x = x
	e.d = dd
	e.surf = surf_id
	e.h = Physics.surf_h(_surf(surf_id), x)
	e.home_x = x
	e.home_d = dd
	e.home_surf = surf_id
	e.max_hp = float(e.def.hp) * mult
	e.hp = e.max_hp
	e.atk = float(e.def.atk) * mult
	e.scale = float(e.def.get("scale", 1.0))
	e.facing = -1
	e.spawn = {"respawn": not e.def.get("boss", false), "mult": mult}
	e.cd = randi() % 60
	return e


# ---------------------------------------------------------------- main loop
func _physics_process(_dt: float) -> void:
	if paused or area_id == "" or Game.p.is_empty():
		ctl.clear_edges()
		return
	frame += 1
	if hitstop > 0:
		hitstop -= 1
		queue_redraw()
		return
	_update_player()
	for e in enemies.duplicate():
		_update_enemy(e)
	_update_projectiles()
	_update_fx()
	if frame % 20 == 0:
		_update_nodes()
	_update_arena()
	if A.type == "trial":
		_update_trial()
	_update_camera()
	_update_prompt()
	if frame % 120 == 0:
		Game.p.x = pl.x
		Game.p.depth = pl.d
	ctl.clear_edges()
	queue_redraw()


# ---------------------------------------------------------------- player
func _update_player() -> void:
	var p: Dictionary = Game.p
	if st.is_empty():
		_refresh_stats()
	pl.anim += 0.12
	pl.t += 1
	if pl.inv > 0:
		pl.inv -= 1
	if pl.flash > 0:
		pl.flash -= 1
	if step_cd > 0:
		step_cd -= 1
	for k in art_cd.keys():
		art_cd[k] -= 1
		if art_cd[k] <= 0:
			art_cd.erase(k)
	if pl.ignore_t > 0:
		pl.ignore_t -= 1
		if pl.ignore_t == 0:
			pl.ignore = ""
	# combat Qi regenerates slowly
	qi_acc += 0.5 / 60.0
	if qi_acc >= 1.0:
		qi_acc -= 1.0
		p.qi = mini(int(p.qi) + 1, int(st.max_qi))
	if pl.state == "dead":
		return
	# buffer action presses briefly so a tap during another action is not lost
	for k in buf.keys():
		buf[k] -= 1
		if buf[k] <= 0:
			buf.erase(k)
	for i in 3:
		if ctl.arts[i]:
			buf["art%d" % i] = 14
	if ctl.dash or ctl.dash_dir != 0:
		buf["dash"] = 10
		if ctl.dash_dir != 0:
			buf["dash_dir"] = 10
			pl.extra.dash_dir = ctl.dash_dir
	if ctl.jump:
		buf["jump"] = 8
	var mv := ctl.move
	var any_input := mv.length() > 0.3 or ctl.jump or ctl.attack or ctl.dash
	# pills
	for i in 2:
		if ctl.pills[i]:
			var id: String = p.quickslots[i] if i < p.quickslots.size() else ""
			if id != "":
				var r := Game.perform("use", {"id": id})
				toast.emit(r.msg if r.ok else r.err, "ok" if r.ok else "err")
	match pl.state:
		"sit":
			pl.facing = 1
			if any_input or mode != "cultivation":
				_stand("Meditation interrupted.")
				return
			if not is_safe_spot():
				_stand("Unsafe — meditation stopped.")
				threat.emit()
				return
			med_t += 1
			if med_t >= 240:
				med_t = 0
				var r := Game.perform("meditate_cycle", {"safe": true})
				if r.ok:
					_float_text("+%d insight  +%d essence" % [r.insight, r.essence], pl.x, pl.d, pl.h + 52, Color("#9fdcff"))
					_ring(pl.x, pl.d, pl.h, Color("#5fe0c8"), 30)
					for l in r.get("lines", []):
						toast.emit(l, "quest")
			return
		"harvest":
			if any_input:
				harvest = {}
				pl.set_state("idle")
				toast.emit("Gathering cancelled.", "info")
				return
			harvest.prog += 1.0 / (float(harvest.node.def.time) * 60.0 * float(harvest.speed))
			if harvest.prog >= 1.0:
				_finish_harvest()
			return
		"hurt":
			pl.kb *= 0.8
			if pl.grounded:
				Physics.walk(pl, surfs, pl.kb, 0, W)
			else:
				_air(Vector2.ZERO)
			if pl.t > 14:
				pl.set_state("idle")
			return
		"dash":
			var sp := 4.2
			if pl.grounded:
				Physics.walk(pl, surfs, pl.facing * sp, mv.y * 1.0, W)
			else:
				_air(Vector2(pl.facing * sp, mv.y))
			if frame % 2 == 0:
				fx.append({"k": "ghost", "x": pl.x, "d": pl.d, "h": pl.h, "f": pl.facing, "t": 0, "life": 12})
			if pl.t > 11:
				pl.set_state("idle")
			return
		"attack":
			_attack_tick()
			if not pl.grounded:
				_air(mv * Vector2(1.2, 0.8))
			return
		"cast":
			_cast_tick()
			if not pl.grounded and not cast.get("move", false):
				_air(Vector2.ZERO)
			return
	# --- free movement states: idle / run / guard / jump
	if ctl.meditate:
		try_meditate()
		return
	if buf.has("dash"):
		if step_cd <= 0:
			buf.erase("dash")
			if buf.has("dash_dir"):
				pl.facing = int(pl.extra.get("dash_dir", pl.facing))
				buf.erase("dash_dir")
			elif absf(mv.x) > 0.2:
				pl.facing = signi(int(signf(mv.x)))
			step_cd = int(42 * st.step_cd)
			pl.inv = 12
			pl.set_state("dash")
			_leave_cultivation()
			return
	if ctl.attack:
		_leave_cultivation()
		combo = 0
		_start_attack()
		return
	for i in 3:
		if buf.has("art%d" % i):
			buf.erase("art%d" % i)
			_leave_cultivation()
			_use_art(i)
			if pl.state == "cast":
				return
	if ctl.interact and not prompt.is_empty():
		_interact(prompt)
		return
	var guarding := ctl.guard and pl.grounded
	var spd := 1.75 * float(st.speed) * (0.3 if guarding else 1.0)
	var v := Vector2(mv.x * spd, mv.y * spd * 0.66)
	if absf(mv.x) > 0.15 and not guarding:
		pl.facing = 1 if mv.x > 0 else -1
	if pl.grounded:
		if buf.has("jump"):
			buf.erase("jump")
			var cur := _surf(pl.surf)
			if mv.y > 0.5 and cur.get("oneWay", false):
				pl.ignore = pl.surf
				pl.ignore_t = 24
				pl.grounded = false
				pl.vz = 0
				pl.h -= 0.2
			else:
				pl.vz = Physics.JUMP_V
				pl.grounded = false
			pl.set_state("jump")
		elif v.length() > 0.05:
			Physics.walk(pl, surfs, v.x, v.y, W)
			pl.set_state("guard" if guarding else "run")
		else:
			pl.set_state("guard" if guarding else "idle")
	else:
		_air(v)
	if arena_locked and boss != null:
		pl.x = clampf(pl.x, float(A.boss.x0) + 8, float(A.boss.x1) - 8)


func _air(v: Vector2) -> void:
	Physics.air_move(pl, surfs, v.x, v.y, W)
	if Physics.fall(pl, surfs):
		if pl.state in ["jump", "fall"]:
			pl.set_state("idle")
		pl.ignore = ""
	elif pl.state in ["idle", "run", "jump", "guard"] and pl.vz < 0:
		pl.set_state("fall")


func _leave_cultivation() -> void:
	if mode == "cultivation":
		threat.emit()


func _stand(msg: String) -> void:
	pl.set_state("idle")
	med_t = 0
	if msg != "":
		toast.emit(msg, "info")


# ---------------------------------------------------------------- melee
func _start_attack() -> void:
	pl.set_state("attack")
	combo_queued = false
	pl.hit_ids = {}


func _attack_len() -> int:
	return int((15.0 if st.family == "sword" else 19.0) / float(st.atk_speed))


func _attack_tick() -> void:
	var L := _attack_len()
	if ctl.attack and pl.t > 4:
		combo_queued = true
	if absf(ctl.move.x) > 0.2 and pl.t < 3:
		pl.facing = 1 if ctl.move.x > 0 else -1
	if pl.t == int(L * 0.35):
		var mul: float = [1.0, 1.1, 1.5][combo]
		var reach: float = st.reach + (6.0 if combo == 2 else 0.0)
		_melee(reach, mul, 22.0, 14.0, true)
		if pl.grounded:
			Physics.walk(pl, surfs, pl.facing * (3.0 if combo == 2 else 1.5), 0, W)
		fx.append({"k": "slash", "x": pl.x + pl.facing * reach * 0.5, "d": pl.d, "h": pl.h + 22, "f": pl.facing, "t": 0, "life": 8, "r": reach * 0.55, "c": Color("#bff5e6"), "thrust": st.family == "spear"})
	if pl.t >= L:
		if combo_queued and combo < 2:
			combo += 1
			_start_attack()
		else:
			combo = 0
			pl.set_state("idle")


func _melee(reach: float, mul: float, htol: float, dtol: float, weapon: bool, dao := false) -> int:
	var hits := 0
	for e in enemies:
		if not e.alive or pl.hit_ids.has(e.get_instance_id()):
			continue
		var dx: float = (e.x - pl.x) * pl.facing
		if dx < -8 or dx > reach + 6 * e.scale:
			continue
		if absf(e.d - pl.d) > dtol + 4 * e.scale:
			continue
		if absf((e.h + 16 * e.scale) - (pl.h + 16)) > htol + 8 * e.scale:
			continue
		pl.hit_ids[e.get_instance_id()] = true
		_hit_enemy(e, _dmg(mul), pl.facing, weapon, dao)
		hits += 1
	return hits


func _dmg(mul: float) -> float:
	return maxf(1.0, float(st.atk) * mul * float(st.dmg_mul) * randf_range(0.9, 1.1))


func _hit_enemy(e: Actor, dmg: float, dir: int, weapon: bool, dao := false) -> void:
	e.hp -= dmg
	e.flash = 6
	e.aggro = true
	var poise: bool = e.def.get("poise", false)
	if not poise or combo == 2:
		e.stun = 14 if not poise else 6
		e.kb = dir * (3.0 if not poise else 1.2)
		if e.state != "windup" or not poise:
			e.set_state("hurt")
	hitstop = 3
	_sparks(e.x, e.d, e.h + 18 * e.scale, Color("#fff2b0"))
	_float_text(str(int(dmg)), e.x, e.d, e.h + 42 * e.scale, Color("#ffe080"))
	if weapon:
		Game.perform("mastery_hit", {"family": st.family})
	var dao_id = Game.p.dao.id if Game.p.dao is Dictionary else ""
	if dao and dao_id != "":
		Game.perform("dao_hit")
		if dao_id == "river":
			Game.p.qi = mini(int(Game.p.qi) + 3, int(st.max_qi))
		elif dao_id == "ember":
			e.burn = 3
			e.burn_dmg = dmg * 0.2
	if e.hp <= 0:
		_kill(e)


func _kill(e: Actor) -> void:
	e.alive = false
	e.hp = 0
	e.dead_t = 0
	e.set_state("dead")
	var r := Game.perform("record_kill", {"type": e.type, "boss_id": e.boss_id})
	if r.ok:
		var parts := []
		for id in r.drops:
			parts.append("%s ×%d" % [C.ITEMS[id].name, r.drops[id]])
		if r.coins:
			parts.append("%d coins" % r.coins)
		if not parts.is_empty():
			toast.emit(", ".join(parts), "loot")
		for l in r.get("lines", []):
			toast.emit(l, "quest")
	if e == boss:
		arena_locked = false
		shake = 10
		toast.emit("%s defeated!" % e.def.name, "quest")
		for i in 3:
			_ring(e.x, e.d, e.h, Color("#d9b25c"), 20 + i * 10)


# ---------------------------------------------------------------- arts
func _use_art(i: int) -> void:
	var p: Dictionary = Game.p
	var id = p.abilities.slots[i]
	if id == null:
		toast.emit("Empty art slot — learn and slot arts on the Skills page.", "info")
		return
	var a: Dictionary = C.ABILITIES[id]
	if a.source == "weapon" and a.family != st.family:
		toast.emit("%s needs a %s equipped." % [a.name, a.family], "err")
		return
	if a.source == "class" and p.cls != a.req.get("cls"):
		toast.emit("Requires the %s discipline." % C.CLASSES[a.req.cls].name, "err")
		return
	if art_cd.has(id):
		return
	var cost := int(ceil(float(a.qi) * float(st.art_cost)))
	if int(p.qi) < cost:
		toast.emit("Not enough Qi (%d/%d)." % [p.qi, cost], "err")
		return
	p.qi = int(p.qi) - cost
	art_cd[id] = int(float(a.cd) * 60)
	cast = {"id": id, "a": a, "hits": 0}
	pl.hit_ids = {}
	pl.set_state("cast")
	if a.shape == "heal":
		p.hp = mini(int(p.hp) + int(a.heal), int(st.max_hp))
		_float_text("+%d" % a.heal, pl.x, pl.d, pl.h + 46, Color("#8fffb0"))
		_ring(pl.x, pl.d, pl.h, Color("#e8c040"), 26)
	elif a.shape == "parry":
		parry = 24
	elif a.shape == "spin":
		guard_spin = 40
	elif a.shape == "lunge":
		cast.move = true


func _cast_tick() -> void:
	var a: Dictionary = cast.a
	var shape: String = a.shape
	var dmul: float = a.get("dmg", 1.0)
	match shape:
		"arc":
			if pl.t == 6:
				_melee(float(a.reach), dmul, 26, 22, true, true)
				fx.append({"k": "slash", "x": pl.x + pl.facing * 24, "d": pl.d, "h": pl.h + 20, "f": pl.facing, "t": 0, "life": 12, "r": 30.0, "c": Color("#6ff0d0")})
			if pl.t > 16:
				pl.set_state("idle")
		"thrust":
			if pl.t == 6:
				_melee(float(a.reach), dmul, 20, 12, true, true)
				fx.append({"k": "beam", "x": pl.x, "d": pl.d, "h": pl.h + 20, "f": pl.facing, "t": 0, "life": 10, "len": float(a.reach), "c": Color("#6ff0d0")})
			if pl.t > 16:
				pl.set_state("idle")
		"lunge":
			if pl.t < 12:
				var sp := float(a.reach) / 12.0
				if pl.grounded:
					Physics.walk(pl, surfs, pl.facing * sp, 0, W)
				else:
					Physics.air_move(pl, surfs, pl.facing * sp, 0, W)
				pl.inv = maxi(pl.inv, 2)
				_melee(20, dmul, 22, 14, true, true)
				if frame % 2 == 0:
					fx.append({"k": "ghost", "x": pl.x, "d": pl.d, "h": pl.h, "f": pl.facing, "t": 0, "life": 10})
			if pl.t > 18:
				pl.set_state("idle")
		"parry":
			if parry > 0:
				parry -= 1
			if pl.t > 24:
				parry = 0
				pl.set_state("idle")
		"combo":
			var hits := int(a.get("hits", 4))
			if pl.t % 8 == 4 and cast.hits < hits:
				cast.hits += 1
				pl.hit_ids = {}
				_melee(float(a.reach), dmul, 48, 16, true, true)
				fx.append({"k": "slash", "x": pl.x + pl.facing * 20, "d": pl.d, "h": pl.h + 18 + cast.hits * 5, "f": pl.facing, "t": 0, "life": 8, "r": 22.0, "c": Color("#8fb0ff")})
			if pl.t > hits * 8 + 6:
				pl.set_state("idle")
		"wave", "bolt":
			if pl.t == 6:
				var dao_river: bool = Game.p.dao is Dictionary and Game.p.dao.id == "river"
				projectiles.append({"x": pl.x + pl.facing * 14, "d": pl.d, "h": pl.h + (22 if shape == "wave" else 20), "vx": pl.facing * (4.0 if shape == "wave" else 5.5), "vd": 0.0,
					"range": float(a.reach), "dist": 0.0, "dmg": _dmg(dmul), "owner": "player", "kind": shape, "htol": 90.0 if shape == "wave" else 18.0, "dtol": 16.0,
					"pierce": shape == "wave" or dao_river, "hit": {}, "dao": true})
			if pl.t > 14:
				pl.set_state("idle")
		"nova":
			if pl.t == 5:
				for e in enemies:
					if e.alive and Vector2(e.x - pl.x, (e.d - pl.d) * 1.5).length() < float(a.reach) and absf(e.h - pl.h) < 80:
						_hit_enemy(e, _dmg(dmul), 1 if e.x > pl.x else -1, false, true)
				_ring(pl.x, pl.d, pl.h, Color("#4a9aff"), float(a.reach))
			if pl.t > 16:
				pl.set_state("idle")
		"spin":
			if pl.t == 4:
				for e in enemies:
					if e.alive and absf(e.x - pl.x) < float(a.reach) and absf(e.d - pl.d) < 20 and absf(e.h - pl.h) < 24:
						_hit_enemy(e, _dmg(dmul), 1 if e.x > pl.x else -1, true, true)
						e.kb = (1 if e.x > pl.x else -1) * 5.0
				_ring(pl.x, pl.d, pl.h, Color("#d9b25c"), float(a.reach))
			if guard_spin > 0:
				guard_spin -= 1
			if pl.t > 18:
				pl.set_state("idle")
		_:
			if pl.t > 12:
				pl.set_state("idle")


# ---------------------------------------------------------------- damage to player
func damage_player(amount: float, from_x: float, unblockable := false) -> void:
	if pl.state == "dead" or pl.inv > 0:
		return
	var p: Dictionary = Game.p
	var dir := 1 if from_x > pl.x else -1
	if parry > 0:
		parry = 0
		for e in enemies:
			if e.alive and absf(e.x - from_x) < 60:
				pl.hit_ids = {}
				pl.facing = dir
				_hit_enemy(e, _dmg(2.6), dir, true, true)
				break
		_float_text("PARRY", pl.x, pl.d, pl.h + 50, Color("#d9b25c"))
		pl.inv = 20
		return
	var dmg := maxf(1.0, amount - float(st.def) * 0.5)
	var blocked := false
	if (pl.state == "guard" or guard_spin > 0) and not unblockable and dir == pl.facing:
		dmg *= 1.0 - float(st.guard)
		blocked = true
	dmg = roundf(dmg)
	p.hp = int(p.hp) - int(dmg)
	pl.flash = 8
	_float_text(("-%d" % dmg) + (" guard" if blocked else ""), pl.x, pl.d, pl.h + 46, Color("#ff7060"))
	shake = maxf(shake, 3.0)
	if pl.state in ["sit", "harvest"]:
		harvest = {}
		med_t = 0
		toast.emit("Interrupted!", "err")
	threat.emit()
	if int(p.hp) <= 0:
		p.hp = 0
		_die()
		return
	pl.inv = 30
	if not blocked:
		pl.kb = -dir * 2.5
		pl.set_state("hurt")


func _die() -> void:
	pl.set_state("dead")
	harvest = {}
	cast = {}
	ctl.reset()
	arena_locked = false
	if A.type == "trial":
		toast.emit("The trial overwhelms you. Nothing is lost — recover and try again.", "err")
		_end_trial(false)
		return
	died.emit()


func revive(mode_: String) -> void:
	var r := Game.perform("revive", {"mode": mode_})
	if not r.ok:
		toast.emit(r.err, "err")
		return
	toast.emit(r.msg, "ok")
	if mode_ == "here":
		pl.set_state("idle")
		pl.inv = 150
		_ring(pl.x, pl.d, pl.h, Color("#e8c040"), 30)
	else:
		var town: String = C.SANCTUARY_OF.get(str(A.region), "jr_town")
		load_area(town, 150, 40)


# ---------------------------------------------------------------- enemies
func _update_enemy(e: Actor) -> void:
	e.anim += 0.1
	e.t += 1
	if e.flash > 0:
		e.flash -= 1
	if not e.alive:
		e.dead_t += 1
		if e.spawn.respawn and e.dead_t > 45 * 60 and absf(e.home_x - pl.x) > view_w * 0.7:
			var n := _spawn_enemy(e.type, e.home_x, e.home_d, e.home_surf, e.spawn.mult)
			enemies[enemies.find(e)] = n
		return
	if e.burn > 0 and frame % 30 == 0:
		e.burn -= 1
		e.hp -= e.burn_dmg
		_float_text(str(int(e.burn_dmg)), e.x, e.d, e.h + 40, Color("#ff9040"))
		if e.hp <= 0:
			_kill(e)
			return
	if e.cd > 0:
		e.cd -= 1
	var def: Dictionary = e.def
	var dx := pl.x - e.x
	var same_level := absf(pl.h - e.h) < 14.0 or (pl.grounded == false and absf(Physics.shadow_h(surfs, pl.x, pl.d, pl.h) - e.h) < 14.0)
	var player_ok := pl.state != "dead"
	if e == boss:
		e.aggro = player_ok and arena_locked
	elif player_ok and same_level and absf(dx) < 150 and absf(pl.d - e.d) < 70:
		e.aggro = true
	elif not player_ok or absf(dx) > 260 or not same_level:
		e.aggro = false
	if e.boss_id != "" and e.phase == 1 and e.hp < e.max_hp * 0.5:
		e.phase = 2
		toast.emit("%s grows desperate!" % def.name, "err")
		if e.type == "captain":
			for k in 2:
				var add := _spawn_enemy("raider", e.x + (k * 2 - 1) * 60, 30 + k * 30, "ground", 1.0)
				add.spawn.respawn = false
				add.aggro = true
				enemies.append(add)
	match e.state:
		"hurt":
			e.kb *= 0.8
			_enemy_walk(e, e.kb, 0)
			if e.t > e.stun:
				e.set_state("chase" if e.aggro else "idle")
			return
		"windup":
			if e.t >= int(def.windup):
				e.set_state("strike")
			return
		"strike":
			_enemy_strike(e)
			return
		"recover":
			if e.t > 22:
				e.set_state("chase" if e.aggro else "idle")
			return
	# idle / patrol / chase
	if not e.aggro:
		var tx := e.home_x + sin(frame / 90.0 + e.home_x) * 30
		if absf(tx - e.x) > 4:
			e.facing = 1 if tx > e.x else -1
			_enemy_walk(e, e.facing * float(def.speed) * 0.5, 0)
			e.set_state("patrol")
		else:
			e.set_state("idle")
		return
	e.facing = 1 if dx > 0 else -1
	var reach := float(def.reach) * (1.0 + (e.scale - 1.0) * 0.6)
	var ranged: bool = def.get("ranged", false)
	var want := reach * 0.8 if not ranged else 110.0
	var ddd := pl.d - e.d
	var mvx := 0.0
	if absf(dx) > want + 6:
		mvx = signf(dx) * float(def.speed)
	elif ranged and absf(dx) < want - 30:
		mvx = -signf(dx) * float(def.speed) * 0.7
	var mvd := clampf(ddd, -1, 1) * float(def.speed) * 0.7 if absf(ddd) > 4 else 0.0
	if mvx != 0 or mvd != 0:
		_enemy_walk(e, mvx, mvd)
		e.set_state("chase")
	var in_range := absf(dx) <= reach + 4 and absf(ddd) <= 12 if not ranged else absf(dx) < 200 and absf(ddd) < 30
	if e.boss_id != "" and e.cd <= 0:
		_boss_pattern(e, dx)
		return
	if in_range and e.cd <= 0 and same_level:
		e.set_state("windup")
		e.extra.kind = "shot" if ranged else "melee"


func _enemy_walk(e: Actor, vx: float, vd: float) -> void:
	var ox := e.x
	var od := e.d
	var oh := e.h
	var os: String = e.surf
	Physics.walk(e, surfs, vx, vd, W)
	if not e.grounded:   # enemies hold their level instead of stepping off open edges
		e.x = ox
		e.d = od
		e.h = oh
		e.surf = os
		e.grounded = true
	if e.boss_id != "":
		e.x = clampf(e.x, float(A.boss.x0) + 10, float(A.boss.x1) - 10)


func _enemy_strike(e: Actor) -> void:
	var def: Dictionary = e.def
	var kind: String = e.extra.get("kind", "melee")
	var reach := float(def.reach) * (1.0 + (e.scale - 1.0) * 0.6)
	if kind == "shot":
		if e.t == 1:
			var bolt: bool = def.get("bolt", false)
			var vx := float(e.facing) * (3.0 if bolt else 3.6)
			var vd := clampf((pl.d - e.d) / maxf(20.0, absf(pl.x - e.x)) * absf(vx), -1.2, 1.2)
			projectiles.append({"x": e.x + e.facing * 10, "d": e.d, "h": e.h + 20, "vx": vx, "vd": vd, "range": 240.0, "dist": 0.0, "dmg": e.atk, "owner": "enemy", "kind": "qi" if bolt else "arrow", "htol": 16.0, "dtol": 9.0, "hit": {}})
		if e.t > 10:
			e.cd = int(def.cd)
			e.set_state("recover")
		return
	if kind == "melee":
		if def.get("quad", false) and e.t < 8:
			_enemy_walk(e, e.facing * 3.0, 0)
		if e.t == 2 or (def.get("quad", false) and e.t == 6):
			if absf(pl.x - e.x) <= reach + 8 and signf(pl.x - e.x) == e.facing and absf(pl.d - e.d) <= 12 + 4 * e.scale and absf(pl.h - e.h) <= 18 + 6 * e.scale:
				damage_player(e.atk, e.x)
			fx.append({"k": "slash", "x": e.x + e.facing * reach * 0.5, "d": e.d, "h": e.h + 18 * e.scale, "f": e.facing, "t": 0, "life": 8, "r": reach * 0.5, "c": Color("#ff8a70")})
		if e.t > 10:
			e.cd = int(def.cd)
			e.set_state("recover")
		return
	_boss_strike(e, kind)


# Boss patterns — each telegraphed, each answered by jump, spacing, depth or guard.
func _boss_pattern(e: Actor, dx: float) -> void:
	var r := randf()
	var kind := "melee"
	match e.type:
		"captain":
			kind = "dash" if r < 0.35 else "melee"
		"sentinel":
			kind = "wave" if r < 0.45 else ("spikes" if e.phase == 2 and r < 0.75 else "melee")
		"qiu":
			kind = "fan" if r < 0.35 else ("ring" if e.phase == 2 and r < 0.6 else ("blink" if r < 0.8 else "melee"))
	if kind == "melee" and absf(dx) > float(e.def.reach) * e.scale + 10:
		if e.type == "captain" or e.type == "qiu":
			kind = "dash" if e.type == "captain" else "fan"
		else:
			return
	e.extra.kind = kind
	e.tele = Vector3(pl.x, pl.d, 0)
	e.set_state("windup")


func _boss_strike(e: Actor, kind: String) -> void:
	match kind:
		"dash":
			if e.t < 18:
				_enemy_walk(e, e.facing * 6.0, clampf(e.tele.y - e.d, -1, 1))
				if absf(pl.x - e.x) < 26 and absf(pl.d - e.d) < 14 and absf(pl.h - e.h) < 22:
					damage_player(e.atk * 1.3, e.x)
				if frame % 2 == 0:
					fx.append({"k": "ghost_e", "a": e, "x": e.x, "d": e.d, "h": e.h, "f": e.facing, "t": 0, "life": 10})
			elif e.t > 30:
				e.cd = 50
				e.set_state("recover")
		"wave":
			if e.t == 1:
				shake = 8
				for dir in ([-1, 1] if e.phase == 2 else [e.facing]):
					projectiles.append({"x": e.x, "d": e.d, "h": 0.0, "vx": dir * 3.0, "vd": 0.0, "range": 400.0, "dist": 0.0, "dmg": e.atk, "owner": "enemy", "kind": "shock", "htol": 7.0, "dtol": 20.0, "hit": {}, "ground": true})
			if e.t > 26:
				e.cd = 70
				e.set_state("recover")
		"spikes":
			if e.t == 1:
				for k in 3:
					fx.append({"k": "spike", "x": pl.x + (k - 1) * 40, "d": clampf(pl.d + (k - 1) * 12, 4, 74), "h": 0.0, "t": 0, "life": 70, "dmg": e.atk})
			if e.t > 20:
				e.cd = 60
				e.set_state("recover")
		"fan":
			if e.t == 1:
				for k in 3:
					projectiles.append({"x": e.x + e.facing * 10, "d": e.d, "h": e.h + 24, "vx": e.facing * 3.2, "vd": (k - 1) * 0.9, "range": 300.0, "dist": 0.0, "dmg": e.atk * 0.8, "owner": "enemy", "kind": "qi", "htol": 16.0, "dtol": 9.0, "hit": {}})
			if e.t > 16:
				e.cd = 50
				e.set_state("recover")
		"ring":
			if e.t == 1:
				fx.append({"k": "shockring", "x": e.x, "d": e.d, "h": 0.0, "t": 0, "life": 70, "dmg": e.atk, "hit": false})
			if e.t > 30:
				e.cd = 70
				e.set_state("recover")
		"blink":
			if e.t == 1:
				_ring(e.x, e.d, e.h, Color("#c070ff"), 20)
				e.x = clampf(pl.x - pl.facing * 34, float(A.boss.x0) + 12, float(A.boss.x1) - 12)
				e.d = pl.d
				e.facing = 1 if pl.x > e.x else -1
				_ring(e.x, e.d, e.h, Color("#c070ff"), 20)
			if e.t == 16:
				if absf(pl.x - e.x) < 40 and absf(pl.d - e.d) < 14 and absf(pl.h - e.h) < 22:
					damage_player(e.atk * 1.2, e.x)
				fx.append({"k": "slash", "x": e.x + e.facing * 20, "d": e.d, "h": e.h + 26, "f": e.facing, "t": 0, "life": 10, "r": 26.0, "c": Color("#d070ff")})
			if e.t > 30:
				e.cd = 40
				e.set_state("recover")
		_:
			if e.t == 2:
				var reach := float(e.def.reach) * e.scale
				if absf(pl.x - e.x) <= reach + 10 and signf(pl.x - e.x) == e.facing and absf(pl.d - e.d) <= 18 and absf(pl.h - e.h) <= 26:
					damage_player(e.atk, e.x)
				fx.append({"k": "slash", "x": e.x + e.facing * reach * 0.6, "d": e.d, "h": e.h + 22 * e.scale, "f": e.facing, "t": 0, "life": 10, "r": reach * 0.6, "c": Color("#ff8a70")})
			if e.t > 14:
				e.cd = int(e.def.cd)
				e.set_state("recover")


# ---------------------------------------------------------------- projectiles & fx
func _update_projectiles() -> void:
	for pr in projectiles.duplicate():
		pr.x += pr.vx
		pr.d = clampf(pr.d + pr.vd, 0, 78)
		pr.dist += absf(pr.vx)
		if pr.dist > pr.range or pr.x < 0 or pr.x > W:
			projectiles.erase(pr)
			continue
		if pr.owner == "player":
			for e in enemies:
				if not e.alive or pr.hit.has(e.get_instance_id()):
					continue
				if absf(e.x - pr.x) < 10 * e.scale and absf(e.d - pr.d) < pr.dtol + 4 * e.scale and absf((e.h + 16 * e.scale) - pr.h) < pr.htol + 10 * e.scale:
					pr.hit[e.get_instance_id()] = true
					pl.hit_ids = {}
					_hit_enemy(e, pr.dmg, signi(int(signf(pr.vx))), false, pr.get("dao", false))
					if not pr.pierce:
						projectiles.erase(pr)
						break
		else:
			var ph: float = pl.h + (0.0 if pr.get("ground", false) else 16.0)
			if pl.state != "dead" and absf(pl.x - pr.x) < 9 and absf(pl.d - pr.d) < pr.dtol and absf(ph - pr.h) < pr.htol:
				damage_player(pr.dmg, pr.x - pr.vx * 4)
				if not pr.get("ground", false):
					projectiles.erase(pr)


func _update_fx() -> void:
	for f in fx.duplicate():
		f.t += 1
		if f.k == "spike" and f.t == 50:
			if absf(pl.x - f.x) < 16 and absf(pl.d - f.d) < 12 and pl.h < 10:
				damage_player(f.dmg, f.x, true)
			shake = maxf(shake, 3)
		if f.k == "shockring" and not f.hit:
			var rad: float = f.t * 2.2
			var dist := Vector2(pl.x - f.x, (pl.d - f.d) * 1.6).length()
			if absf(dist - rad) < 8 and pl.h < 8:
				f.hit = true
				damage_player(f.dmg, f.x, true)
		if f.t >= f.life:
			fx.erase(f)


func _float_text(s: String, x: float, dd: float, h: float, c: Color) -> void:
	fx.append({"k": "text", "s": s, "x": x, "d": dd, "h": h, "t": 0, "life": 50, "c": c})


func _sparks(x: float, dd: float, h: float, c: Color) -> void:
	fx.append({"k": "spark", "x": x, "d": dd, "h": h, "t": 0, "life": 10, "c": c, "seed": randi()})


func _ring(x: float, dd: float, h: float, c: Color, r: float) -> void:
	fx.append({"k": "ring", "x": x, "d": dd, "h": h, "t": 0, "life": 18, "c": c, "r": r})


# ---------------------------------------------------------------- nodes, discovery, arena, trial
func node_ready(n: Dictionary) -> bool:
	return node_ready_at.get(n.id, 0.0) <= Time.get_unix_time_from_system()


func _update_nodes() -> void:
	if A.type == "trial":
		return
	for n in nodes:
		if absf(float(n.x) - (cam_x + view_w / 2.0)) < view_w / 2.0 and not Game.p.discovered.nodes.has(n.id):
			var r := Game.perform("discover_node", {"node_id": n.id})
			if r.ok and r.has("msg"):
				toast.emit("Discovered: %s (+1 soul)" % n.def.name, "info")


func _update_arena() -> void:
	if boss == null or not boss.alive:
		return
	if not arena_locked and pl.x > float(A.boss.x0) + 24 and pl.state != "dead":
		arena_locked = true
		boss.aggro = true
		toast.emit("%s blocks the way!" % boss.def.name, "err")
		threat.emit()


func _update_camera() -> void:
	var tx := pl.x - view_w * 0.45 + pl.facing * 16
	var lo := 0.0
	var hi := maxf(0.0, W - view_w)
	if arena_locked:
		lo = clampf(float(A.boss.x0) - 20, 0, hi)
		hi = clampf(float(A.boss.x1) + 20 - view_w, lo, hi)
	cam_x = lerpf(cam_x, clampf(tx, lo, hi), 0.12)
	var sh := Physics.shadow_h(surfs, pl.x, pl.d, pl.h, pl.ignore)
	cam_y = lerpf(cam_y, clampf(sh * 0.45, 0, 42), 0.06)
	shake = maxf(0.0, shake - 0.5)


func is_safe_spot() -> bool:
	for e in enemies:
		if e.alive and (e.aggro or absf(e.x - pl.x) < 170):
			return false
	if A.type == "town":
		return true
	for s in stations:
		if s.type in ["rest", "shrine"] and absf(float(s.x) - pl.x) < 80:
			return true
	return false


func near_safe_travel() -> bool:
	for s in stations:
		if s.type in ["rest", "shrine"] and absf(float(s.x) - pl.x) < 80:
			return is_safe_spot()
	return false


func try_meditate() -> void:
	if pl.state == "sit":
		_stand("")
		return
	if not pl.grounded or pl.state == "dead":
		return
	if not is_safe_spot():
		toast.emit("Unsafe — meditate in town or beside a field shrine with no enemies near.", "err")
		return
	pl.set_state("sit")
	med_t = 0
	toast.emit("Meditating… each cycle grants insight and Qi essence. Move to stop.", "info")


func start_trial() -> void:
	var r := Game.perform("check_trial", {"safe": is_safe_spot()})
	if not r.ok:
		toast.emit(r.err, "err")
		return
	trial_return = {"area": area_id, "x": pl.x, "d": pl.d}
	load_area("trial", 120, 40)
	trial = {"wave": 0, "t": 0, "done": false}
	toast.emit("Inner Sea Trial — defeat three waves of echoes.", "quest")


func _update_trial() -> void:
	if trial.is_empty() or trial.done:
		return
	trial.t += 1
	var alive := 0
	for e in enemies:
		if e.alive:
			alive += 1
	if alive == 0 and trial.t > 60:
		if trial.wave >= 3:
			trial.done = true
			var r := Game.perform("complete_trial")
			toast.emit(r.msg if r.ok else r.err, "quest" if r.ok else "err")
			for l in r.get("lines", []):
				toast.emit(l, "quest")
			for i in 4:
				_ring(pl.x, pl.d, pl.h, Color("#d9b25c"), 20 + i * 14)
			get_tree().create_timer(2.0).timeout.connect(func(): _end_trial(r.ok))
			return
		trial.wave += 1
		var n: int = 2 + trial.wave
		var realm_mult: float = 1.0 + Game.p.realm * 0.5
		for i in n:
			var e := _spawn_enemy("echo", 300 + (i % 2) * 220 + randf() * 40, 10 + randf() * 60, "ground", realm_mult)
			e.spawn.respawn = false
			e.aggro = true
			enemies.append(e)
		toast.emit("Wave %d / 3" % trial.wave, "info")


func _end_trial(success: bool) -> void:
	trial = {}
	var back: Dictionary = trial_return if not trial_return.is_empty() else {"area": "jr_town", "x": 150.0, "d": 40.0}
	if not success:
		Game.p.hp = S.stats(Game.p).max_hp
	load_area(back.area, back.x, back.d)
	trial_end.emit(success)


# ---------------------------------------------------------------- interaction
func _update_prompt() -> void:
	prompt = {}
	if pl.state in ["dead", "sit", "harvest", "attack", "cast", "dash"]:
		return
	_best = 9999.0
	var consider := _consider
	for po in portals:
		var locked: bool = po.has("lock") and not Game.p.flags.get(po.lock, false)
		consider.call("portal", po, float(po.x), 30.0, 0.0, ("Locked: " if locked else "Travel: ") + po.label, 34.0, 20.0)
	for n in npcs:
		consider.call("npc", n, n.x, n.d, n.h, "Talk" if n.type != "merchant" else "Shop", 30.0, 15.0)
	for s in stations:
		var lbl: String = {"shrine": "Shrine", "rest": "Rest Shrine", "forge": "Forge", "furnace": "Alchemy Furnace", "research": "Research Desk", "chest": "Shared Storage", "shop": "Shop", "board": "Commissions", "seal": "Seal Altar"}.get(s.type, s.type)
		consider.call("station", s, float(s.x), float(s.depth), 0.0, lbl, 30.0, 5.0)
	for n in nodes:
		var verb: String = C.PROFESSIONS[n.def.prof].verb
		consider.call("node", n, float(n.x), float(n.depth), float(n.h), (verb if node_ready(n) else "Depleted") + ": " + str(n.def.name), 20.0, 10.0)
	for rn in runes:
		consider.call("rune", rn, float(rn.x), float(rn.depth), float(rn.h), "Touch rune", 18.0, 12.0)


var _best := 9999.0


func _consider(kind: String, obj, x: float, dd: float, h: float, label: String, rx: float, prio: float) -> void:
	var dx := absf(x - pl.x)
	if dx > rx or absf(dd - pl.d) > 22 or absf(h - pl.h) > 8:
		return
	var score := dx + absf(dd - pl.d) * 0.5 - prio
	if score < _best:
		_best = score
		prompt = {"kind": kind, "obj": obj, "label": label}


func _interact(pr: Dictionary) -> void:
	match pr.kind:
		"portal":
			var po: Dictionary = pr.obj
			if po.has("lock") and not Game.p.flags.get(po.lock, false):
				var ch := "Chapter I" if po.lock == "ch1_done" else "Chapter II"
				toast.emit("The way is sealed. Complete %s and report to your mentor." % ch, "err")
				return
			if boss != null and boss.alive and arena_locked:
				return
			Game.p.x = po.spawn
			load_area(po.to, float(po.spawn), 40.0)
		"npc":
			var n: Actor = pr.obj
			n.facing = 1 if pl.x > n.x else -1
			if n.type == "merchant":
				station.emit("shop")
				return
			var r := Game.perform("talk", {"npc": n.type})
			if r.ok:
				dialogue.emit(n.type, r.lines, r.get("menu", []))
		"station":
			var s: Dictionary = pr.obj
			if s.type == "seal":
				_seal_altar()
			else:
				if s.type == "rest":
					Game.p.flags["rest_" + area_id] = true
				station.emit(s.type)
		"node":
			var n: Dictionary = pr.obj
			if not node_ready(n):
				toast.emit("%s regrows in %ds." % [n.def.name, int(node_ready_at[n.id] - Time.get_unix_time_from_system())], "info")
				return
			var p: Dictionary = Game.p
			if not R.has_tool(p, n.def.tool):
				toast.emit("Requires a %s — Elder Wen in Jade River Town provides one." % {"mining": "pick", "herbalism": "harvest kit", "fishing": "fishing rod"}[n.def.tool], "err")
				return
			var lv := S.prof_lv(p, n.def.prof)
			if lv < int(n.def.lv):
				toast.emit("%s Lv %d required (you are Lv %d). Gather lower-tier nodes to train." % [S.cap(n.def.prof), n.def.lv, lv], "err")
				return
			var speed := 0.6 if (n.def.tool == "mining" and p.items.has("steel_pick")) else 1.0
			harvest = {"node": n, "prog": 0.0, "speed": speed}
			pl.facing = 1 if float(n.x) >= pl.x else -1
			pl.set_state("harvest")
		"rune":
			_touch_rune(pr.obj)


func _finish_harvest() -> void:
	var n: Dictionary = harvest.node
	harvest = {}
	pl.set_state("idle")
	var r := Game.perform("harvest", {"node_id": n.id, "type": n.type})
	if r.ok:
		node_ready_at[n.id] = Time.get_unix_time_from_system() + float(n.def.respawn)
		_float_text(r.msg, float(n.x), float(n.depth), float(n.h) + 30, Color("#bfffd0"))
		toast.emit(r.msg, "loot")
		for l in r.get("lines", []):
			toast.emit(l, "quest")
	else:
		toast.emit(r.err, "err")


func _seal_altar() -> void:
	var p: Dictionary = Game.p
	if p.flags.get("seal_repaired", false):
		toast.emit("The grove seal hums, whole again.", "info")
		return
	if p.quests.ch2.state != "active" or int(p.quests.ch2.step) < 2:
		toast.emit("A cracked seal altar. Archivist Suyin may know its purpose.", "info")
		return
	if not p.flags.get("seal_primed", false):
		var r := Game.perform("seal_prime")
		toast.emit(r.msg if r.ok else r.err, "quest" if r.ok else "err")
		if not r.ok:
			return
	seal_progress = 0
	for rn in runes:
		rn.lit = false
	dialogue.emit("seal", ["The altar tablet reads: “Water rises, wood drinks, fire is fed, earth receives.”", "Touch the four runes in that order: Water → Wood → Fire → Earth. One rune rests on the raised step."], [])


func _touch_rune(rn: Dictionary) -> void:
	var p: Dictionary = Game.p
	if not p.flags.get("seal_primed", false) or p.flags.get("seal_repaired", false):
		toast.emit("The rune is cold.", "info")
		return
	var order: Array = A.runeOrder
	if rn.lit:
		return
	if order[seal_progress] == rn.id:
		rn.lit = true
		seal_progress += 1
		_ring(float(rn.x), float(rn.depth), float(rn.h), Color("#5fe0c8"), 18)
		if seal_progress >= order.size():
			var r := Game.perform("seal_complete")
			toast.emit(r.msg if r.ok else r.err, "quest")
			for l in r.get("lines", []):
				toast.emit(l, "quest")
	else:
		seal_progress = 0
		for x in runes:
			x.lit = false
		toast.emit("The runes flicker out. Hint: Water → Wood → Fire → Earth.", "err")


func travel_to(id: String) -> void:
	var a: Dictionary = C.AREAS[id]
	var x := 150.0
	for s in a.stations:
		if s.type in ["shrine", "rest"]:
			x = float(s.x) + 30
	load_area(id, x, 40.0)


# ---------------------------------------------------------------- minimap data
func minimap() -> Dictionary:
	var ens := []
	for e in enemies:
		if e.alive:
			ens.append([e.x / W, e.boss_id != ""])
	var nds := []
	var sense: bool = Game.p.soul >= int(C.SOUL_MILESTONES[0].at)
	for n in nodes:
		if Game.p.discovered.nodes.has(n.id) or sense:
			nds.append([float(n.x) / W, node_ready(n), n.def.prof])
	var others := []
	for n in npcs:
		others.append(n.x / W)
	for s in stations:
		if s.type in ["shrine", "rest"]:
			others.append(float(s.x) / W)
	var ports := []
	for po in portals:
		ports.append([float(po.x) / W, po.has("lock") and not Game.p.flags.get(po.lock, false)])
	return {"player": pl.x / W, "enemies": ens, "nodes": nds, "others": others, "portals": ports, "view": [cam_x / W, (cam_x + view_w) / W]}


# ================================================================ rendering
func sy(dd: float, h: float) -> float:
	return BASE_Y + dd - h + cam_y


var _plook: Dictionary = {}


func _draw() -> void:
	if area_id == "":
		return
	if frame % 30 == 0 or _plook.is_empty():
		_plook = Sprites.player_look(Game.p)
	var cx := floorf(cam_x + (randf() - 0.5) * shake)
	var cyo := floorf(cam_y + (randf() - 0.5) * shake * 0.5)
	for L in bg.layers:
		draw_texture(L.tex, Vector2(-floorf(cx * L.f), floorf(cyo * L.fy)))
		if L.has("falls"):
			for fr in L.falls:
				var fxp: float = fr.position.x - floorf(cx * L.f)
				if fxp < -8 or fxp > view_w + 8:
					continue
				for k in 3:
					var yy: float = fr.position.y + fmod(frame * 1.3 + k * fr.size.y / 3.0, fr.size.y)
					draw_rect(Rect2(fxp + 1, yy + floorf(cyo * L.fy), 2, 3), Color(1, 1, 1, 0.9))
	draw_texture(rail_t, Vector2(-cx, BASE_Y - 22 + cyo))
	for lx in lanterns:
		var px: float = lx - cx
		if px < -10 or px > view_w + 10:
			continue
		var fl := 0.8 + 0.2 * sin(frame * 0.2 + lx)
		draw_circle(Vector2(px, BASE_Y - 26 + cyo), 7 * fl, Color(Painter.col(theme.light), 0.18))
		draw_rect(Rect2(px - 3, BASE_Y - 31 + cyo, 6, 7), Color("#c0392b"))
		draw_rect(Rect2(px - 2, BASE_Y - 30 + cyo, 4, 5), Color(Painter.col(theme.light), fl))
	draw_texture(floor_t, Vector2(-cx, BASE_Y - 2 + cyo))
	# sortable objects
	var items := []
	for s in surfs:
		if s.id == "ground":
			continue
		items.append([float(s.d1), 0, s])
	for s in stations:
		items.append([float(s.depth), 1, s])
	for po in portals:
		items.append([1.0, 2, po])
	for n in nodes:
		items.append([_key_at(n.surf, float(n.depth)), 3, n])
	for rn in runes:
		items.append([_key_at(rn.surf, float(rn.depth)), 4, rn])
	for n in npcs:
		items.append([n.d, 5, n])
	for e in enemies:
		items.append([_actor_key(e), 5, e])
	items.append([_actor_key(pl), 6, pl])
	items.sort_custom(func(a, b): return a[0] < b[0])
	for it in items:
		match it[1]:
			0: _draw_deck(it[2], cx, cyo)
			1: _draw_station(it[2], cx, cyo)
			2: _draw_portal(it[2], cx, cyo)
			3: _draw_node(it[2], cx, cyo)
			4: _draw_rune(it[2], cx, cyo)
			5, 6: _draw_actor(it[2], cx, cyo)
	for pr in projectiles:
		_draw_projectile(pr, cx, cyo)
	for f in fx:
		_draw_fx(f, cx, cyo)
	if not harvest.is_empty():
		var c := Vector2(pl.x - cx, BASE_Y + pl.d - pl.h + cyo - 54)
		draw_arc(c, 7, 0, TAU, 20, Color(0, 0, 0, 0.6), 3)
		draw_arc(c, 7, -PI / 2, -PI / 2 + TAU * harvest.prog, 20, Color("#5fe0c8"), 2)
	if pl.state == "sit":
		var c2 := Vector2(pl.x - cx, BASE_Y + pl.d - pl.h + cyo - 50)
		draw_arc(c2, 7, 0, TAU, 20, Color(0, 0, 0, 0.6), 3)
		draw_arc(c2, 7, -PI / 2, -PI / 2 + TAU * med_t / 240.0, 20, Color("#9fdcff"), 2)


func _key_at(surf_id: String, dd: float) -> float:
	if surf_id == "ground":
		return dd
	return float(_surf(surf_id).d1) + 0.5 + dd * 0.001


func _actor_key(a: Actor) -> float:
	var s := Physics.support(surfs, a.x, a.d, a.h, a.ignore)
	if s.is_empty() or s.id == "ground":
		return a.d
	return float(s.d1) + 0.5 + a.d * 0.001


func _draw_deck(s: Dictionary, cx: float, cy: float) -> void:
	var sp := Props.deck(s, A.theme)
	var x0: float = s.x0 - cx
	if x0 > view_w or x0 + (s.x1 - s.x0) < 0:
		return
	draw_texture(sp.tex, Vector2(x0, BASE_Y + s.d0 - sp.maxh - sp.top + cy))


func _draw_station(s: Dictionary, cx: float, cy: float) -> void:
	var sp := Props.station(s.type)
	var x: float = float(s.x) - cx
	if x < -40 or x > view_w + 40:
		return
	var y: float = BASE_Y + float(s.depth) + cy
	draw_texture(sp.tex, Vector2(x - sp.ax, y - sp.ay))
	if s.type in ["shrine", "rest"]:
		var g := 0.5 + 0.5 * sin(frame * 0.05)
		draw_circle(Vector2(x, y - 22), 6 + g * 2, Color(0.37, 0.88, 0.78, 0.15))
	if s.type == "furnace" or s.type == "forge":
		for k in 3:
			var ph := fmod(frame * 0.4 + k * 12, 36.0)
			draw_rect(Rect2(x - 8 + k * 5 + sin(ph * 0.3) * 2, y - 30 - ph, 2, 2), Color(0.85, 0.85, 0.85, 0.6 * (1.0 - ph / 36.0)))


func _draw_portal(po: Dictionary, cx: float, cy: float) -> void:
	var locked: bool = po.has("lock") and not Game.p.flags.get(po.lock, false)
	var sp := Props.portal(locked)
	var x: float = float(po.x) - cx
	if x < -40 or x > view_w + 40:
		return
	var y := BASE_Y + 34 + cy
	draw_texture(sp.tex, Vector2(x - sp.ax, y - sp.ay))
	if not locked:
		draw_circle(Vector2(x, y - 30), 14 + sin(frame * 0.08) * 2, Color(0.37, 0.88, 0.78, 0.12))


func _draw_node(n: Dictionary, cx: float, cy: float) -> void:
	var ready := node_ready(n)
	var sp := Props.node(n.def.sprite, n.def.get("tint", null), ready)
	var x: float = float(n.x) - cx
	if x < -30 or x > view_w + 30:
		return
	var y: float = BASE_Y + float(n.depth) - float(n.h) + cy
	draw_texture(sp.tex, Vector2(x - sp.ax, y - sp.ay))
	if ready and n.def.sprite == "crystal":
		draw_circle(Vector2(x, y - 14), 9 + sin(frame * 0.1) * 1.5, Color(Painter.col(n.def.tint), 0.2))
	if ready and frame % 90 < 45 and not Game.p.discovered.nodes.has(n.id):
		draw_rect(Rect2(x - 1, y - 36, 2, 2), Color.WHITE)


func _draw_rune(rn: Dictionary, cx: float, cy: float) -> void:
	var sp := Props.rune(rn.glyph, rn.lit)
	var x: float = float(rn.x) - cx
	var y: float = BASE_Y + float(rn.depth) - float(rn.h) + cy
	draw_texture(sp.tex, Vector2(x - sp.ax, y - sp.ay))
	if rn.lit:
		draw_circle(Vector2(x, y - 16), 10, Color(0.37, 0.88, 0.78, 0.22))


func _pose_of(a: Actor) -> Array:
	match a.state:
		"run", "patrol", "chase":
			return ["run", int(a.anim * 1.6)]
		"attack":
			var L := _attack_len()
			return ["attack", 0 if a.t < L * 0.3 else (1 if a.t < L * 0.65 else 2)]
		"cast":
			return ["cast", 0]
		"jump":
			return ["jump", 0]
		"fall":
			return ["fall", 0]
		"dash":
			return ["dash", 0]
		"guard":
			return ["guard", 0]
		"hurt":
			return ["hurt", 0]
		"sit":
			return ["sit", 0]
		"dead":
			return ["dead", 0]
		"windup":
			return ["attack", 0]
		"strike":
			return ["attack", 1]
		"recover":
			return ["attack", 2]
		"harvest":
			return ["attack", int(a.anim * 0.7) % 2]
	return ["idle", int(a.anim * 0.5)]


func _draw_actor(a: Actor, cx: float, cy: float) -> void:
	var x := a.x - cx
	if x < -60 or x > view_w + 60:
		return
	var sh := Physics.shadow_h(surfs, a.x, a.d, a.h, a.ignore)
	var foot := BASE_Y + a.d - a.h + cy
	if a.state != "dead" or a.dead_t < 40:
		_ellipse(Vector2(x, BASE_Y + a.d - sh + cy), 8 * a.scale, 2.5 * a.scale, Color(0, 0, 0, 0.35))
	if a.kind == "enemy" and not a.alive and a.dead_t > 50:
		return
	var pz := _pose_of(a)
	var pose: String = pz[0]
	var fr: int = pz[1]
	var spr: Dictionary
	var look_scale := a.scale
	var is_beast: bool = a.kind == "enemy" and a.def.get("quad", false)
	if a.kind == "player":
		spr = Sprites.humanoid(_plook, pose, fr)
	elif is_beast:
		var bp := "dead" if a.state == "dead" else ("attack" if a.state in ["windup", "strike"] else "run")
		spr = Sprites.beast(a.type, int(a.anim * 1.5) if a.state in ["chase", "patrol", "strike"] else 0, bp)
	elif a.type == "sentinel":
		spr = Sprites.sentinel(int(a.anim), "dead" if a.state == "dead" else ("attack" if a.state in ["windup", "strike"] else "idle"))
	else:
		var look: Dictionary = Sprites.LOOKS.get(a.def.get("look", a.type) if a.kind == "enemy" else a.type, Sprites.LOOKS.raider)
		spr = Sprites.humanoid(look, pose, fr, look_scale)
	var mod := Color.WHITE
	if a.flash > 0 and a.flash % 2 == 0:
		mod = Color(1, 0.45, 0.45)
	if a.kind == "player" and a.inv > 0 and a.state != "dash" and frame % 6 < 3:
		mod.a = 0.55
	if a.type == "echo":
		mod = Color(0.7, 1, 0.95, 0.75)
	draw_set_transform(Vector2(floorf(x), floorf(foot)), 0, Vector2(a.facing, 1))
	draw_texture(spr.tex, Vector2(-spr.ax, -spr.ay), mod)
	# weapon
	if not is_beast and a.type != "sentinel" and a.state != "dead" and a.kind != "npc":
		var hand := Sprites.hand_at(pose, fr, look_scale)
		if not hand.is_empty():
			var wa: float = hand.a
			if pose in ["idle", "run", "talk", "fall", "jump"]:
				wa = -0.95
			elif pose == "guard":
				wa = -1.35
			elif pose == "sit":
				wa = -0.1
			_draw_weapon(a, Vector2(hand.x - spr.ax, hand.y - spr.ay), wa)
	draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	var top := foot - (46 if a.type != "sentinel" else 94) * (a.scale if a.type != "sentinel" else 1.0)
	if a.kind == "enemy" and a.alive:
		if a.state == "windup":
			var col := Color("#ff4030") if frame % 8 < 4 else Color("#ffd040")
			draw_string(font, Vector2(x - 3, top - 2), "!", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, col)
			if Game.p.soul >= int(C.SOUL_MILESTONES[1].at):
				_ellipse(Vector2(x + a.facing * 18 * a.scale, foot), 14 * a.scale, 4, Color(1, 0.25, 0.2, 0.25))
			if a.extra.get("kind", "") == "dash":
				draw_line(Vector2(x, foot), Vector2(x + a.facing * 100, foot), Color(1, 0.3, 0.2, 0.4), 2)
		if a.hp < a.max_hp and a.boss_id == "":
			draw_rect(Rect2(x - 10, top - 4, 20, 3), Color(0, 0, 0, 0.7))
			draw_rect(Rect2(x - 10, top - 4, 20 * a.hp / a.max_hp, 3), Color("#e04a3a"))
	if a.kind == "npc":
		var nm: String = C.NPCS[a.type].name if C.NPCS.has(a.type) else "Merchant"
		draw_string(font, Vector2(x - 40, top - 4), nm, HORIZONTAL_ALIGNMENT_CENTER, 80, 8, Color("#f0dca0"))
		var ch = R.active_chapter(Game.p)
		if ch != null and ch.mentor == a.type:
			var q: Dictionary = Game.p.quests[ch.id]
			var st_: Dictionary = ch.steps[q.step]
			if st_.type == "talk" or (ch.id == "ch3" and int(q.step) in [2, 3]):
				var bob := sin(frame * 0.1) * 2
				draw_rect(Rect2(x - 2, top - 20 + bob, 4, 8), Color("#ffd040"))
				draw_rect(Rect2(x - 2, top - 10 + bob, 4, 3), Color("#ffd040"))


func _draw_weapon(a: Actor, hand: Vector2, ang: float) -> void:
	var dir := Vector2(cos(ang), sin(ang))
	if a.kind == "player":
		var w: Dictionary = C.ITEMS[Game.p.equip.weapon]
		var tint: Color = Painter.col(w.get("tint", "#cfd8de"))
		if w.family == "spear":
			var back := hand - dir * 12
			var tip := hand + dir * 22
			draw_line(back, tip, Color("#6a3a1a"), 2)
			draw_line(back, tip - dir * 2, Color("#9a6a34"), 1)
			var n := Vector2(-dir.y, dir.x)
			draw_colored_polygon(PackedVector2Array([tip, tip + dir * 8 + n * 0.5, tip + n * 2.5, tip - n * 2.5]), tint)
			draw_line(tip - dir * 1, tip - dir * 4 + Vector2(0, 5), Color("#1f8a6e"), 2)
		else:
			var tip2 := hand + dir * 16
			draw_line(hand, tip2, tint, 2)
			draw_line(hand + dir * 2, tip2, Painter.shade(tint, 0.4), 1)
			var n2 := Vector2(-dir.y, dir.x)
			draw_line(hand - n2 * 3, hand + n2 * 3, Color("#d9b25c"), 2)
		return
	match a.type:
		"archer":
			draw_arc(hand + Vector2(2, 0), 8, -1.2, 1.2, 8, Color("#6a4a2a"), 2)
			draw_line(hand + Vector2(2, 0) + Vector2(cos(-1.2), sin(-1.2)) * 8, hand + Vector2(2, 0) + Vector2(cos(1.2), sin(1.2)) * 8, Color("#e8e0cc"), 1)
		"acolyte", "echo":
			if a.state == "windup":
				draw_circle(hand, 3 + sin(frame * 0.5), Color("#c070ff") if a.type == "acolyte" else Color("#5fe0c8"))
		"heavy":
			draw_line(hand - dir * 4, hand + dir * 16, Color("#4a3a2a"), 4)
			draw_rect(Rect2(hand + dir * 12 - Vector2(3, 3), Vector2(6, 6)), Color("#50585e"))
		"qiu":
			draw_line(hand - dir * 14, hand + dir * 20, Color("#2a1a3a"), 2)
			draw_circle(hand + dir * 20, 2.5, Color("#d070ff"))
		_:
			var tip3 := hand + dir * 14 * a.scale
			var n3 := Vector2(-dir.y, dir.x)
			draw_polyline(PackedVector2Array([hand, hand + dir * 7 * a.scale + n3 * 1.5, tip3 - n3 * 1.5]), Color("#d8dce0"), 2)


func _draw_projectile(pr: Dictionary, cx: float, cy: float) -> void:
	var p := Vector2(pr.x - cx, BASE_Y + pr.d - pr.h + cy)
	match pr.kind:
		"arrow":
			draw_line(p - Vector2(signf(pr.vx) * 8, 0), p, Color("#e8e0cc"), 1)
			draw_rect(Rect2(p - Vector2(1, 1), Vector2(2, 2)), Color("#cfd8de"))
		"qi":
			draw_circle(p, 4, Color("#8a4ad0"))
			draw_circle(p, 2, Color("#f0c8ff"))
		"shock":
			for k in 4:
				draw_rect(Rect2(p.x - 6 + k * 3, p.y - 3 - (k % 2) * 3 - sin(frame * 0.6 + k) * 2, 3, 4 + (k % 2) * 3), Color("#a8c860"))
			_ellipse(p, 10, 3, Color(0.66, 0.78, 0.38, 0.35))
		"wave":
			draw_arc(p, 14, -1.2 * signf(pr.vx) + (0.0 if pr.vx > 0 else PI), 1.2 * signf(pr.vx) + (0.0 if pr.vx > 0 else PI), 10, Color("#6ff0d0"), 3)
			var off := 0.0 if pr.vx > 0 else PI
			draw_arc(p, 10, off - 1.0, off + 1.0, 8, Color(1, 1, 1, 0.8), 1)
		"bolt":
			draw_circle(p, 4, Color("#4a9aff"))
			draw_circle(p, 2, Color("#dff0ff"))
			draw_line(p, p - Vector2(signf(pr.vx) * 10, 0), Color(0.4, 0.7, 1, 0.6), 2)


func _draw_fx(f: Dictionary, cx: float, cy: float) -> void:
	var p := Vector2(f.x - cx, BASE_Y + f.d - f.h + cy)
	var k: float = float(f.t) / float(f.life)
	match f.k:
		"text":
			draw_string(font, p + Vector2(-40, -k * 16), f.s, HORIZONTAL_ALIGNMENT_CENTER, 80, 9, Color(f.c, 1.0 - k * k))
		"slash":
			var dirf: float = f.f
			var r: float = f.r
			var a0 := -1.2 if dirf > 0 else PI - 1.2
			if f.get("thrust", false):
				draw_line(p - Vector2(dirf * r, 0), p + Vector2(dirf * r * 0.8, 0), Color(f.c, 0.9 - k), 2)
			else:
				draw_arc(p, r, a0, a0 + 2.4, 12, Color(f.c, 0.95 - k), 2.5)
		"beam":
			draw_line(p, p + Vector2(f.f * f.len, 0), Color(f.c, 1.0 - k), 3)
			draw_line(p, p + Vector2(f.f * f.len, 0), Color(1, 1, 1, 0.8 - k), 1)
		"ring":
			var rr: float = f.r * (0.3 + 0.7 * k)
			_ellipse_ring(p, rr, rr * 0.35, Color(f.c, 1.0 - k), 2)
		"spark":
			var rng := RandomNumberGenerator.new()
			rng.seed = f.seed
			for i in 6:
				var ang := rng.randf() * TAU
				draw_rect(Rect2(p + Vector2(cos(ang), sin(ang)) * (2 + k * 10), Vector2(2, 2)), Color(f.c, 1.0 - k))
		"ghost":
			var spr := Sprites.humanoid(_plook, "dash", 0)
			draw_set_transform(p, 0, Vector2(f.f, 1))
			draw_texture(spr.tex, Vector2(-spr.ax, -spr.ay), Color(0.5, 1, 0.9, 0.4 * (1.0 - k)))
			draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
		"ghost_e":
			_ellipse(p, 10, 3, Color(1, 0.3, 0.2, 0.3 * (1.0 - k)))
		"spike":
			if f.t < 50:
				_ellipse_ring(p, 12, 4, Color(1, 0.3, 0.2, 0.5 + 0.5 * sin(f.t * 0.4)), 1.5)
			else:
				for i in 5:
					draw_line(p + Vector2(-8 + i * 4, 0), p + Vector2(-8 + i * 4, -14 - (i % 2) * 6), Color("#8a9a4a"), 2)
		"shockring":
			var rad: float = f.t * 2.2
			_ellipse_ring(p, rad, rad / 1.6, Color(0.75, 0.44, 1.0, 1.0 - k), 3)


func _ellipse(c: Vector2, rx: float, ry: float, col: Color) -> void:
	var pts := PackedVector2Array()
	for i in 16:
		var a := TAU * i / 16.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	draw_colored_polygon(pts, col)


func _ellipse_ring(c: Vector2, rx: float, ry: float, col: Color, w: float) -> void:
	var pts := PackedVector2Array()
	for i in 25:
		var a := TAU * i / 24.0
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	draw_polyline(pts, col, w)
