class_name TechniquePreview
extends Control
## The Techniques page's live preview (under the chooser): the character casting the chosen art as a fight casts it,
## against foes that take it. The pieces are the room's own: the character in the art's pose, the foes' sprites, and an
## FxLayer (not the room's: `world` off) that plays the form's sheet through FxLayer.cast, sized, anchored and timed as a
## fight plays it, and marks each hit with FxLayer.hit (its number and spark). One clock drives them all (their own
## processes are off), one beat after another: the pose and the sheet at `lead_s`, the impact at the art's wind-up
## later, the foes' hurt, flash and knockback, then a pause, and again. How the foes meet the art (data/moments.json
## `technique_preview`): a single strike one foe, a multi-hit or area form a pack; a ward's dome turns a foe's blow
## aside, a counter parries a foe's attack and strikes back, a snare or a seal holds its foe struggling in place; an art
## that strikes nothing (a ward, a chorus) leaves no number. Reduce motion shows one still frame at the impact; Battery
## saver steps it at 30 fps with a longer pause (and FxLayer plays the middle band at most). It lives and draws only
## while its page is open. Presentation only: nothing here reads or changes a fight.
##
## Decision 42: a top-down character casts as the top-down game draws it: the character is a TopdownDoll playing the
## art's top-down pose toward its foes (the pose a fight plays, TechniquePreview.top_pose), the foes are the top-down
## world's own (art/topdown/foes/, `top_foe`), all at a whole `top_scale` screen px an art px, and the form plays at
## the top-down world's proportion to the body (2 world units an art px). A classic side-view character keeps the side
## view's avatar against pebble imps. Only the pieces that moved are drawn again: the caster when its frame changes, a
## foe while it moves or its frame changes, the effects while any are alive.

const GROUND := 136.0         # the feet, in room px from the stage's top
const CASTER_X := 28.0        # the caster's feet, in room px from the stage's left
const PACK := {1: [[104.0, 0.0]], 2: [[98.0, 2.0], [128.0, -4.0]], 3: [[90.0, 2.0], [116.0, -6.0], [142.0, 4.0]]}   # foes' feet: x, depth
## The top-down stage, in art px: the feet's line, the caster's feet and the foes' (x, depth), and the rows they face.
const TOP_GROUND := 52.0
const TOP_CASTER_X := 13.0
const TOP_PACK := {1: [[46.0, 0.0]], 2: [[42.0, 3.0], [58.0, -4.0]], 3: [[38.0, 3.0], [52.0, -5.0], [63.0, 4.0]]}
const CASTER_ROW := "e"
const FOE_ROW := "w"

var cfg: Dictionary = {}
var art := ""                 # the art shown ("": the character stands alone)
var tech: Dictionary = {}     # its technique row
var form := ""                # its form (vfx.anim): the sheet it plays
var pose := "idle"            # the body pose it is cast in
var plays := "hit"            # how the foes meet it: hit, ward, counter or bind
var still := false            # Reduce motion: one frame at the impact, held
var top := false              # the top-down character (decision 42), else the side view's
var clock := 0.0              # seconds into the loop
var lead := 0.0               # when the cast begins
var impact := 0.0             # when its blow lands
var length := 0.0             # the loop, its pause included
var amount := 0.0             # a hit's number
var stage: Node2D             # the room in miniature, `scale` screen px a stage px: the pack, the caster, the effects
var pack: Node2D              # the foes, the farther drawn first
var caster: Node2D            # the side view's Avatar, or a TopdownDoll
var fx: FxLayer
var foes: Array = []          # [{sprite, home, push, vel, hurt, flash, bound}]
var units := 1.0              # the effects' units a stage px (the top-down world's 2 world units an art px)
var _fired := {}
var _acc := 0.0
var _who = null

func _init() -> void:
	cfg = MomentRules.cfg().get("technique_preview", {})
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage = Node2D.new()
	stage.process_mode = Node.PROCESS_MODE_DISABLED   # its pieces never step themselves: this preview's clock steps them
	add_child(stage)
	pack = Node2D.new()
	stage.add_child(pack)
	fx = FxLayer.new()
	fx.world = false
	fx.lazy_sheets = true
	stage.add_child(fx)
	_build(false)

## Layered by the order of its pieces alone, never by z (the page's own drawing and any page over it stay in order).
func _ready() -> void:
	fx.z_index = 0

## Closed with its page (or freed unshown): the foes' index is taken back from its worker (TopFoe.settle).
func _notification(what: int) -> void:
	if what == NOTIFICATION_EXIT_TREE or what == NOTIFICATION_PREDELETE: TopFoe.settle()

## The caster and the stage's scale for the side view or the top-down character (a new caster when the view changes).
func _build(top_down: bool) -> void:
	top = top_down
	if is_instance_valid(caster): caster.free()
	units = 2.0 if top else 1.0
	stage.scale = Vector2.ONE * (float(cfg.get("top_scale", 3)) if top else float(cfg.get("scale", 1.25)))
	fx.scale = Vector2.ONE / units
	fx.number_scale = 0.8 / (stage.scale.x / units)
	if top:
		TopFoe.texture(str(cfg.get("top_foe", "mudshell_crab")))   # the foe's sheet and index start loading now, ahead of the first art chosen
		caster = TopdownDoll.new()
		caster.externally_timed = true
		caster.position = Vector2(TOP_CASTER_X, TOP_GROUND)
		caster.shadow = true
	else:
		caster = Figures.side_avatar()
		caster.externally_timed = true
		caster.position = Vector2(CASTER_X, GROUND)
	stage.add_child(caster)
	stage.move_child(caster, 1)   # over the pack, under the effects

## The character's outfit (the page dresses it again when the equipment changes), and which view draws it.
func dress(outfit: Dictionary, top_down := false) -> void:
	if top_down != top or caster == null: _build(top_down)
	caster.outfit = outfit
	if not top: caster.last_key = ""

## Show `id` cast by `who` (a technique the page may show; "" for none): from its beginning when it is another art.
func show_art(id: String, who) -> void:
	if id == art and who == _who: return
	art = id
	_who = who
	restart()

## The loop from its first beat: the art's row, its sheet, pose and pack, its timing; under Reduce motion, the impact
## frame at once and held.
func restart() -> void:
	tech = ContentDB.entry("techniques", art) if art != "" else {}
	form = str(tech.get("vfx", {}).get("anim", ""))
	if tech.is_empty(): pose = "idle"
	else: pose = top_pose(tech, _who) if top else pose_of(tech, _who, caster.outfit)
	plays = str(cfg.get("plays", {}).get(form, "hit"))
	var n := int(cfg.get("foes", {}).get(form, 1)) if not tech.is_empty() else 0
	for f in foes: f.sprite.queue_free()
	foes.clear()
	for spot in (TOP_PACK if top else PACK).get(n, []):   # the nearest first: a single-target art lands on it
		var s: Node2D
		if top:
			s = TopFoe.new(str(cfg.get("top_foe", "mudshell_crab")), FOE_ROW)
		else:
			s = CreatureSprite.new()
			s.creature_id = str(cfg.get("foe", "pebble_imp"))
			s.scale = Vector2.ONE * float(cfg.get("foe_scale", 0.75))
			s.facing = -1
		foes.append({"sprite": s, "home": Vector2(float(spot[0]), (TOP_GROUND if top else GROUND) + float(spot[1]))})
	var deep := foes.duplicate()
	deep.sort_custom(func(a, b): return float(a.home.y) < float(b.home.y))
	for f in deep:
		pack.add_child(f.sprite)
	var a := FxLayer.form_spec(form)
	if not a.is_empty(): SpriteCache.tex_async(str(a.file))   # the sheet loads on a thread through the lead-in
	lead = float(cfg.get("lead_s", 0.4)) + (0.3 if plays == "counter" else 0.0)
	impact = lead + float(tech.get("windup_s", 0.2))
	var rest := (float(a.frames) - float(a.impact)) / float(a.fps) if not a.is_empty() else 0.0
	still = UiKit.reduce_motion()
	length = impact + maxf(float(cfg.get("after_s", 0.9)), rest) + float(cfg.get("battery_pause_s" if _battery() else "pause_s", 0.8))
	var dtype := str(tech.get("damage_type", "physical"))
	var at_stat := "qi_attack" if dtype == "qi" else ("soul_attack" if dtype == "soul" else "physical_attack")
	var mult: Array = tech.get("mult", [1.0, 1.0])
	amount = maxf(1.0, (_who.stats.value(at_stat) if _who != null else 100.0) * (float(mult[0]) + float(mult[-1])) * 0.5) if not mult.is_empty() else 1.0
	_loop()
	set_process(not still)
	if still:
		# One frame at the impact: every piece stepped there, the blow's first number risen into view, then held.
		var to := impact + 0.02 if not tech.is_empty() else 0.0
		while clock < to - 0.0001: advance(minf(1.0 / 30.0, to - clock))
		advance(0.0)

## Debug (--preview-t, the page's shots): the loop from its start stepped `at` s in and held there.
func hold(at: float) -> void:
	restart()
	while clock < at - 0.0001: advance(minf(1.0 / 60.0, at - clock))
	set_process(false)

func _loop() -> void:
	clock = 0.0
	_fired.clear()
	fx.fx.clear()
	fx.stacks.clear()
	fx.queue_redraw()
	caster.play("idle")
	if top:
		caster.row = CASTER_ROW if not tech.is_empty() else TopdownDoll.PORTRAIT_ROW
		caster.position.x = TOP_CASTER_X if not tech.is_empty() else roundf(size.x / stage.scale.x * 0.5)
	else:
		caster.facing = 1
		caster.position.x = CASTER_X if not tech.is_empty() else roundf(size.x / stage.scale.x * 0.5)   # alone, it stands centred
	caster.queue_redraw()
	for f in foes:
		f.merge({"push": 0.0, "vel": 0.0, "hurt": 0.0, "flash": 0.0, "bound": false}, true)
		f.sprite.play("idle", true)
		f.sprite.position = f.home
		f.sprite.queue_redraw()

## The caster's feet on the page.
func feet() -> Vector2:
	return position + stage.position + caster.position * stage.scale

## A stage point (room px, or the top-down art px) in the effects' units.
func _u(p: Vector2) -> Vector2:
	return p * units

## The body pose an art is shown in: its `vfx.pose`, a combo step `combo_<n>` taken from the family's combo (the free
## hand's, of the weapon in hand), when every layer the character wears has it; else the idle stance.
static func pose_of(t: Dictionary, who, outfit: Dictionary) -> String:
	var p := str(t.get("vfx", {}).get("pose", t.get("action", "idle")))
	if p.begins_with("combo_"):
		var fam := str(t.get("family", "any"))
		if fam == "any": fam = str(StatRules.family(who).get("id", "fists")) if who != null else "fists"
		var combo: Array = ContentDB.entry("weapon_families", fam).get("combo", [])
		p = str(combo[mini(int(p.right(1)) - 1, combo.size() - 1)].action) if not combo.is_empty() else "idle"
	for cat in outfit:
		var item: Dictionary = Wardrobe.parts.get(cat, {}).get(str(outfit[cat]), {}) if cat in Wardrobe.CATEGORIES else {}
		for layer in item.get("layers", []):
			if not layer.animations.has(p): return "idle"
	return p

## The top-down pose an art is cast in, as a fight plays it (TopdownPlayer._strike_pose on Combat's action for it):
## the art's own action as the weapon in hand plays it (the heavy sabre's two-handed cuts, the bell's toll, the bow's
## draw), the form's top-down pose for a meditation or a leap, and the hand seal's cast for an art with no action.
## `family`: the weapon family in hand when the caller has it (StatRules.family of `who`).
static func top_pose(t: Dictionary, who, family := {}) -> String:
	var fam: Dictionary = family if not family.is_empty() else (StatRules.family(who) if who != null else ContentDB.entry("weapon_families", "fists"))
	var fid := str(fam.get("id", "fists"))
	var raw = t.get("action")
	if raw == null or str(raw) in ["", "null", "meditate_burst"]: return TopdownFigure.resolve("cast", fid)
	if str(raw) in ["meditate", "jump"]: return TopdownFigure.resolve(CombatFeel.form_pose(t, fam), fid)
	return TopdownFigure.resolve(str(raw), fid)

func _battery() -> bool:
	return Game.account != null and bool(Game.account.settings.get("battery_saver", false))

func _process(delta: float) -> void:
	if not is_visible_in_tree(): return
	if _battery():
		_acc += delta
		if _acc < 1.0 / float(cfg.get("battery_fps", 30)): return
		delta = _acc
	_acc = 0.0
	advance(minf(delta, 0.1))

## Once, when the clock passes `at`.
func _beat(name: String, at: float) -> bool:
	if clock < at or _fired.has(name): return false
	_fired[name] = true
	return true

## The loop moved on by `dt`: its beats, then each piece (each drawn again only when what it shows changed).
func advance(dt: float) -> void:
	clock += dt
	if not tech.is_empty():
		if clock >= length:
			_loop()
		_beats()
	if top:
		caster.step(dt)
		if str(caster.action) != "idle" and clock > impact + 0.55 and not still:
			caster.play("idle")
			caster.row = CASTER_ROW if not tech.is_empty() else TopdownDoll.PORTRAIT_ROW
	else:
		caster.elapsed += dt
		if str(caster.action) != "idle" and clock > impact + 0.55 and not still: caster.play("idle")
		caster.queue_redraw()
	for f in foes:
		var s: Node2D = f.sprite
		s.t += dt
		f.hurt = maxf(0.0, float(f.hurt) - dt)
		var was_flash := float(f.flash)
		f.flash = maxf(0.0, float(f.flash) - dt)
		f.push = float(f.push) + float(f.vel) * dt
		f.vel = float(f.vel) * maxf(0.0, 1.0 - dt * 7.0)
		if absf(float(f.vel)) < 12.0 / units: f.push = move_toward(float(f.push), 0.0, 36.0 / units * dt)
		if size.x > 0.0: f.push = minf(float(f.push), size.x / stage.scale.x - 12.0 / units - float(f.home.x))   # knocked back, never out of the frame
		if s.action == "hurt" and float(f.hurt) <= 0.0: s.play("walk" if f.bound else "idle", true)
		elif s.action == "attack" and s.t > 0.4: s.play("idle", true)
		var at: Vector2 = (f.home + Vector2(float(f.push), 0.0)).round()
		if top:
			var moved: bool = at != s.position or was_flash != float(f.flash)
			s.position = at
			s.set_flash(float(f.flash) / 0.12)
			if moved or s.changed(): s.queue_redraw()
		else:
			s.position = at
			s.set_flash(float(f.flash) / 0.12)
			s.queue_redraw()
	fx.step(dt)

func _beats() -> void:
	var feet: Vector2 = caster.position
	var col := SpriteCache.element_color(str(tech.get("element", "none")))
	var first: Dictionary = foes[0] if not foes.is_empty() else {}
	var back := 1.0 / units   # a stage px of the side view's velocities
	match plays:
		"counter":   # the foe winds up first and strikes into the parry
			if _beat("windup", 0.05): first.sprite.play("windup", true)
			if _beat("lunge", impact - 0.12):
				first.sprite.play("attack", true)
				first.vel = -160.0 * back
		"ward":   # the dome rises, then a foe's blow glances off it
			if _beat("windup", impact): first.sprite.play("windup", true)
			if _beat("lunge", impact + 0.3):
				first.sprite.play("attack", true)
				first.vel = -200.0 * back
			if _beat("turned", impact + 0.45):
				fx.add("flash", _u(feet) + Vector2(34, -48), {"color": col.lerp(UiKit.PAPER, 0.5), "radius": 26, "dur": 0.25})
				first.vel = 230.0 * back
				first.flash = 0.12
	if _beat("cast", lead):
		caster.play(pose)
		if top: caster.t = 0.0
		else: caster.elapsed = 0.0
		var far := TOP_CASTER_X if top else CASTER_X
		for f in foes: far = maxf(far, f.home.x)
		var target: Vector2 = first.home if not first.is_empty() else feet + Vector2(60, 0) / units
		var reach := minf(float(tech.get("hitbox", {}).get("x", [0, 80])[1]), (far - feet.x) * units + 20.0)
		fx.cast(tech, _u(feet), 1, col, _u(target), float(tech.get("windup_s", 0.2)), reach, Vector2.RIGHT if top else Vector2.ZERO)
	if plays == "ward": return
	if plays == "counter" and _beat("parry", impact): fx.parry(_u(feet), 1)
	for i in foes.size():
		if _beat("hit%d" % i, impact + 0.06 * i): _strike(i)

## Foe `i` takes the art: its share of the hits (each foe in reach takes them all, else they are shared out, three at
## most a foe so the numbers stay readable), the hurt frames and a flash, and a knockback (a bound foe struggles in
## place instead).
func _strike(i: int) -> void:
	var f: Dictionary = foes[i]
	var total := int(tech.get("hits", 1))
	var n := foes.size()
	var mine := total if int(tech.get("max_targets", 1)) >= n else total / n + (1 if i < total % n else 0)
	mine = mini(mine, 3)
	f.sprite.play("hurt", true)
	f.hurt = 0.3
	f.flash = 0.12
	f.bound = plays == "bind"
	if not f.bound: f.vel = (150.0 + 30.0 * i) / units
	var at: Vector2 = _u(f.home + Vector2(float(f.push), 0.0)) + Vector2(0, -(f.sprite.top() * units + 8.0 if top else 40.0))
	var src := "tech:" + art
	if mine <= 0:
		fx.hit(at, 0.0, src, str(tech.get("element", "none")), str(tech.get("damage_type", "")), false, "", false)
	for h in mine:
		fx.hit(at, roundf(amount * (1.0 + 0.07 * h)), src, str(tech.get("element", "none")), str(tech.get("damage_type", "")), false, "foe%d" % i)

## Decision 42: a foe of the top-down world (decision 43: its species' sheet in art/topdown/foes/, indexed by
## data/topdown/foes.json, built by tools/art/topdown/build_foes.py) with the few calls the preview makes of a CreatureSprite: play, its clock `t`, a flash
## (white as it is struck, then the fight's tint, TopdownWorld.FoeView's), and its height for the numbers. The sheet's
## index is read on a worker thread and its texture on a loading thread, both asked for as the top-down preview is
## built, so choosing an art never waits on them (a foe appears the frame they are in).
class TopFoe extends Node2D:
	static var _sheet: Dictionary = {}
	static var _task := -1
	static var _parsed = null
	static var _texs: Dictionary = {}
	var species := ""
	var row := "w"
	var action := "idle"
	var t := 0.0
	var flash := 0.0
	var _src := Rect2()
	var _drawn_tex: Texture2D

	func _init(sp: String, facing_row: String) -> void:
		species = sp
		row = facing_row
		texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

	## The foes' sheet index, read on a worker thread the first time it is asked for ({} until it is in).
	static func sheet() -> Dictionary:
		if _sheet.is_empty():
			if _task == -1:
				_task = WorkerThreadPool.add_task(func(): TopFoe._parsed = JSON.parse_string(FileAccess.get_file_as_string(TopdownRoom.DIR + "foes.json")))
			elif _task >= 0 and WorkerThreadPool.is_task_completed(_task):
				settle()
		return _sheet

	## The index's reading taken back from the worker (waited for if it is still reading): a preview does this as it
	## goes, so no task of the pool is left unclaimed. One never claimed kept its function past this script's end,
	## and the engine crashed as it quit (the tutorials suite, "53 checks, 0 failures" and a non-zero exit, when its
	## Techniques page closed before the reading was taken back).
	static func settle() -> void:
		if _task < 0: return
		WorkerThreadPool.wait_for_task_completion(_task)
		_task = -2
		var ts = _parsed
		_parsed = null
		if ts is Dictionary: _sheet = ts

	## A species' sheet, from its loading thread (null until it is in).
	static func texture(sp: String) -> Texture2D:
		var path := str(sheet().get("species", {}).get(sp, {}).get("atlas", ""))
		if path == "": return null
		if _texs.get(path) == null: _texs[path] = SpriteCache.tex_async(path)
		return _texs[path]

	func play(next: String, restart := false) -> void:
		if next != action or restart:
			action = next
			t = 0.0

	func set_flash(v: float) -> void:
		flash = v

	## The art px its idle frame rises over its feet.
	func top() -> float:
		return float(sheet().get("species", {}).get(species, {}).get("top", 20))

	## True when what it shows is not what it drew last: its frame moved on, or its sheet came in.
	func changed() -> bool:
		return _frame() != _src or texture(species) != _drawn_tex

	func _frame() -> Rect2:
		var sh := sheet()
		var acts: Dictionary = sh.get("species", {}).get(species, {}).get("actions", {})
		var a: Dictionary = acts.get(action, acts.get("idle", {}))
		var mirror: Dictionary = sh.get("mirror", {})
		var list: Array = a.get("frames", {}).get(str(mirror.get(row, row)), [[0, 0]])
		var i := int(t * float(a.get("fps", 6)))
		var at: Array = list[i % list.size() if a.get("loop", true) else mini(i, list.size() - 1)]
		var c: Array = sh.get("species", {}).get(species, {}).get("cell", [64, 72])
		return Rect2(float(at[0]), float(at[1]), float(c[0]), float(c[1]))

	func _draw() -> void:
		_drawn_tex = texture(species)
		_src = _frame()
		if _drawn_tex == null: return
		var foot: Array = _sheet.get("species", {}).get(species, {}).get("foot", [32, 40])
		var tint := Color.WHITE if flash <= 0.0 else Color(str(CombatFeel.cfg().get("flash", {}).get("tint", "#ffb4a0")))
		material = TopdownFx.white_material() if flash > 0.6 else null
		# A blob shadow under its feet, as the world's FoeShadow.
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.35))
		draw_circle(Vector2.ZERO, float(_sheet.get("species", {}).get(species, {}).get("shadow", [8, 3])[0]), Color(0, 0, 0, 0.25))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(-1, 1) if (_sheet.get("mirror", {}) as Dictionary).has(row) else Vector2.ONE)
		draw_texture_rect_region(_drawn_tex, Rect2(-Vector2(float(foot[0]), float(foot[1])), _src.size), _src, tint)
		draw_set_transform(Vector2.ZERO)
