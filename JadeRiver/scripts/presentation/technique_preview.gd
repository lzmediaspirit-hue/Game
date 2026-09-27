class_name TechniquePreview
extends Control
## The Techniques page's live preview (under the chooser): the character casting the chosen art as a fight casts it,
## against pebble imps that take it. The pieces are the room's own: the layered avatar in the art's pose (`vfx.pose`,
## pose_of), the creature sprite a foe's EnemyView draws, and an FxLayer (not the room's: `world` off) that plays the
## form's sheet through FxLayer.cast, sized, anchored and timed as World._cast plays it, and marks each hit with
## FxLayer.hit (its number and spark). One clock drives them all (their own processes are off), one beat after
## another: the pose and the sheet at `lead_s`, the impact at the art's wind-up later, the foes' hurt, flash and
## knockback, then a pause, and again. How the foes meet the art (data/moments.json `technique_preview`): a single
## strike one imp, a multi-hit or area form a pack; a ward's dome turns an imp's blow aside, a counter parries an imp's
## attack and strikes back, a snare or a seal holds its imp struggling in place; an art that strikes nothing (a ward, a
## chorus) leaves no number. Reduce motion shows one still frame at the impact; Battery saver steps it at 30 fps with
## a longer pause (and FxLayer plays the middle band at most). It lives and draws only while its page is open.
## Presentation only: nothing here reads or changes a fight.

const Avatar = preload("res://scripts/avatar.gd")
const GROUND := 136.0         # the feet, in room px from the stage's top
const CASTER_X := 28.0        # the caster's feet, in room px from the stage's left
const PACK := {1: [[104.0, 0.0]], 2: [[98.0, 2.0], [128.0, -4.0]], 3: [[90.0, 2.0], [116.0, -6.0], [142.0, 4.0]]}   # foes' feet: x, depth

var cfg: Dictionary = {}
var art := ""                 # the art shown ("": the character stands alone)
var tech: Dictionary = {}     # its technique row
var form := ""                # its form (vfx.anim): the sheet it plays
var pose := "idle"            # the body pose it is cast in
var plays := "hit"            # how the foes meet it: hit, ward, counter or bind
var still := false            # Reduce motion: one frame at the impact, held
var clock := 0.0              # seconds into the loop
var lead := 0.0               # when the cast begins
var impact := 0.0             # when its blow lands
var length := 0.0             # the loop, its pause included
var amount := 0.0             # a hit's number
var stage: Node2D             # the room in miniature, `scale` screen px a room px: the pack, the caster, the effects
var pack: Node2D              # the foes, the farther drawn first
var caster: Node2D
var fx: FxLayer
var foes: Array = []          # [{sprite, home, push, vel, hurt, flash, bound}]
var _fired := {}
var _acc := 0.0
var _who = null

func _init() -> void:
	cfg = MomentRules.cfg().get("technique_preview", {})
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	stage = Node2D.new()
	stage.scale = Vector2.ONE * float(cfg.get("scale", 1.25))
	stage.process_mode = Node.PROCESS_MODE_DISABLED   # its pieces never step themselves: this preview's clock steps them
	add_child(stage)
	pack = Node2D.new()
	stage.add_child(pack)
	caster = Avatar.new()
	caster.externally_timed = true
	caster.position = Vector2(CASTER_X, GROUND)
	stage.add_child(caster)
	fx = FxLayer.new()
	fx.world = false
	fx.number_scale = 0.8 / stage.scale.x
	stage.add_child(fx)

## Layered by the order of its pieces alone, never by z (the page's own drawing and any page over it stay in order).
func _ready() -> void:
	fx.z_index = 0

## The character's outfit (the page dresses it again when the equipment changes).
func dress(outfit: Dictionary) -> void:
	caster.outfit = outfit
	caster.last_key = ""

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
	pose = pose_of(tech, _who, caster.outfit) if not tech.is_empty() else "idle"
	plays = str(cfg.get("plays", {}).get(form, "hit"))
	var n := int(cfg.get("foes", {}).get(form, 1)) if not tech.is_empty() else 0
	for f in foes: f.sprite.queue_free()
	foes.clear()
	for spot in PACK.get(n, []):   # the nearest first: a single-target art lands on it
		var s := CreatureSprite.new()
		s.creature_id = str(cfg.get("foe", "pebble_imp"))
		s.scale = Vector2.ONE * float(cfg.get("foe_scale", 0.75))
		s.facing = -1
		foes.append({"sprite": s, "home": Vector2(float(spot[0]), GROUND + float(spot[1]))})
	var deep := foes.duplicate()
	deep.sort_custom(func(a, b): return float(a.home.y) < float(b.home.y))
	for f in deep:
		pack.add_child(f.sprite)
	var a := FxLayer.form_spec(form)
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
		while clock < to - 0.0001: _advance(minf(1.0 / 30.0, to - clock))
		_advance(0.0)

## Debug (--preview-t, the page's shots): the loop from its start stepped `at` s in and held there.
func hold(at: float) -> void:
	restart()
	while clock < at - 0.0001: _advance(minf(1.0 / 60.0, at - clock))
	set_process(false)

func _loop() -> void:
	clock = 0.0
	_fired.clear()
	fx.fx.clear()
	fx.stacks.clear()
	caster.play("idle")
	caster.facing = 1
	caster.position.x = CASTER_X if not tech.is_empty() else roundf(size.x / stage.scale.x * 0.5)   # alone, it stands centred
	for f in foes:
		f.merge({"push": 0.0, "vel": 0.0, "hurt": 0.0, "flash": 0.0, "bound": false}, true)
		f.sprite.play("idle", true)
		f.sprite.position = f.home

## The caster's feet on the page.
func feet() -> Vector2:
	return position + stage.position + caster.position * stage.scale

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

func _battery() -> bool:
	return Game.account != null and bool(Game.account.settings.get("battery_saver", false))

func _process(delta: float) -> void:
	if not is_visible_in_tree(): return
	if _battery():
		_acc += delta
		if _acc < 1.0 / float(cfg.get("battery_fps", 30)): return
		delta = _acc
	_acc = 0.0
	_advance(minf(delta, 0.1))

## Once, when the clock passes `at`.
func _beat(name: String, at: float) -> bool:
	if clock < at or _fired.has(name): return false
	_fired[name] = true
	return true

## The loop moved on by `dt`: its beats, then each piece.
func _advance(dt: float) -> void:
	clock += dt
	if not tech.is_empty():
		if clock >= length:
			_loop()
		_beats()
	caster.elapsed += dt
	if str(caster.action) != "idle" and clock > impact + 0.55 and not still: caster.play("idle")
	caster.queue_redraw()
	for f in foes:
		var s: CreatureSprite = f.sprite
		s.t += dt
		f.hurt = maxf(0.0, float(f.hurt) - dt)
		f.flash = maxf(0.0, float(f.flash) - dt)
		f.push = float(f.push) + float(f.vel) * dt
		f.vel = float(f.vel) * maxf(0.0, 1.0 - dt * 7.0)
		if absf(float(f.vel)) < 12.0: f.push = move_toward(float(f.push), 0.0, 36.0 * dt)
		if size.x > 0.0: f.push = minf(float(f.push), size.x / stage.scale.x - 12.0 - float(f.home.x))   # knocked back, never out of the frame
		if s.action == "hurt" and float(f.hurt) <= 0.0: s.play("walk" if f.bound else "idle", true)
		elif s.action == "attack" and s.t > 0.4: s.play("idle", true)
		s.position = (f.home + Vector2(float(f.push), 0.0)).round()
		s.set_flash(float(f.flash) / 0.12)
		s.queue_redraw()
	fx.step(dt)

func _beats() -> void:
	var feet: Vector2 = caster.position
	var col := SpriteCache.element_color(str(tech.get("element", "none")))
	var first: Dictionary = foes[0] if not foes.is_empty() else {}
	match plays:
		"counter":   # the imp winds up first and strikes into the parry
			if _beat("windup", 0.05): first.sprite.play("windup", true)
			if _beat("lunge", impact - 0.12):
				first.sprite.play("attack", true)
				first.vel = -160.0
		"ward":   # the dome rises, then an imp's blow glances off it
			if _beat("windup", impact): first.sprite.play("windup", true)
			if _beat("lunge", impact + 0.3):
				first.sprite.play("attack", true)
				first.vel = -200.0
			if _beat("turned", impact + 0.45):
				fx.add("flash", feet + Vector2(34, -48), {"color": col.lerp(UiKit.PAPER, 0.5), "radius": 26, "dur": 0.25})
				first.vel = 230.0
				first.flash = 0.12
	if _beat("cast", lead):
		caster.play(pose)
		caster.elapsed = 0.0
		var far := CASTER_X
		for f in foes: far = maxf(far, f.home.x)
		var target: Vector2 = first.home if not first.is_empty() else feet + Vector2(60, 0)
		fx.cast(tech, feet, 1, col, target, float(tech.get("windup_s", 0.2)), minf(float(tech.get("hitbox", {}).get("x", [0, 80])[1]), far - CASTER_X + 20.0))
	if plays == "ward": return
	if plays == "counter" and _beat("parry", impact): fx.parry(feet, 1)
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
	if not f.bound: f.vel = 150.0 + 30.0 * i
	var at: Vector2 = f.home + Vector2(float(f.push), -40.0)
	var src := "tech:" + art
	if mine <= 0:
		fx.hit(at, 0.0, src, str(tech.get("element", "none")), str(tech.get("damage_type", "")), false, "", false)
	for h in mine:
		fx.hit(at, roundf(amount * (1.0 + 0.07 * h)), src, str(tech.get("element", "none")), str(tech.get("damage_type", "")), false, "foe%d" % i)
