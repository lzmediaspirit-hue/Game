class_name FxLayer
extends Node2D
## Transient effects and floating numbers driven by events (S36): hit sparks
## tinted by element, damage numbers (crits larger and gold, soul violet, Qi teal),
## slash arcs, dust, rings, breakthrough spirals, meditation motes, projectiles.
## Presentation only: nothing here changes game state.

const ARRAY_COLOURS := {"guard": Color("8aebee"), "killing": Color("e45858"), "binding": Color("b18de2")}   # as their plates are engraved
## Every transient kind `add` takes, one per arm of _draw's match (contract_tests keeps the two in step; moments.json
## names only these).
const KINDS := ["number", "spark", "slash", "dust", "ring", "note", "wave", "spiral", "motes", "flash", "pagoda", "seal_slam",
	"talisman_wave", "pill_cloud", "heaven_cloud", "heaven_storm", "text", "pillar", "converge", "rain", "tint", "anim"]
## Defaults by kind: a spark's bit (6 px) and reach (28 px, tier 1), a wave's stroke (8 px); else size 20 (a talisman wave's height), radius 30.
const DEFAULTS := {"spark": {"size": 6, "radius": 28}, "wave": {"size": 8}}
## Technique animations (data/fx_art.json, drawn by tools/art/fx): the sprite scale of a band-sized form by its
## richness band, and the band of a vfx tier (1-2, 3-4, 5-7). Reduce motion plays every form at the calmest band
## and Battery saver at the middle one at most.
const BAND_SCALE := [1.0, 1.5, 2.0]

var fx: Array = []          # {kind, pos, t, dur, color, facing, text, size, vel, radius, count, height, style, core}; t < 0 waits
var stacks: Dictionary = {} # P6e multi-hit numbers: stack key -> {n, sum, last, top (its highest number's entry), at, size}
var clock := 0.0            # seconds of this layer's own time (stacks are timed on it)
var fixed_step := 0.0       # debug (--cast --capture): when > 0, every frame advances this many seconds, not the real delta
var number_scale := 1.0     # numbers and words at this share of their size (a staged layer drawn larger than the room)
var world := true           # the room's layer: also draws Combat's arrays and fires, a held Presence and the projectiles
var chest := 56.0           # a figure's chest over its feet, where a cast's chest-high forms sit (the top-down body is shorter)
                            # from state; false for a layer staged on a page (the Techniques page's preview)
var lazy_sheets := false    # a form's sheet not yet in memory loads on a loading thread and its frames wait for it (the
                            # Techniques page's preview, which asks for it as an art is chosen), never stalling a frame
## Decision 38: the top-down world draws the technique forms, their bolts and the blows' impact marks itself, from the
## ground-plane sheets (TopdownFx); its layer keeps the rest (numbers, words, rings, washes).
var forms := true           # draw a cast's form sheet and a technique's bolt here
var sparks := true          # draw a hit's spark here

func _ready() -> void:
	z_index = 4000
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func add(kind: String, pos: Vector2, extra := {}) -> void:
	var e := {"kind": kind, "pos": pos, "t": -float(extra.get("delay", 0.0)), "dur": float(extra.get("dur", 0.4)), "color": extra.get("color", UiKit.PAPER),
		"facing": int(extra.get("facing", 1)), "text": str(extra.get("text", "")), "size": int(extra.get("size", DEFAULTS.get(kind, {}).get("size", 20))),
		"vel": extra.get("vel", Vector2.ZERO), "radius": float(extra.get("radius", DEFAULTS.get(kind, {}).get("radius", 30))), "count": int(extra.get("count", 0)),
		"height": float(extra.get("height", 0.0)), "style": str(extra.get("style", "square")), "core": float(extra.get("core", 10)),
		"turn": float(extra.get("turn", 0.0))}   # a slash's or a form's turn off the facing (the top-down aim, redesign Phase 2)
	if kind == "tint" and not _tint_allowed(e): return
	if kind == "anim":
		for k in ["form", "row", "scale", "scale_y", "start", "travel", "tiles", "alpha"]: e[k] = extra.get(k)
	fx.append(e)
	if fx.size() > 160: fx.pop_front()

# ------------------------------------------------------------------ technique animations (decision 23)
## The sheet spec of a form (data/fx_art.json), {} when no sheet is built for it.
static func form_spec(form: String) -> Dictionary:
	return ContentDB.config("fx_art").get("forms", {}).get(form, {})

## The richness band (0-2) a vfx tier plays at, under Reduce motion (the calmest) and Battery saver (the middle at most).
static func band_of(tier: int) -> int:
	var s: Dictionary = Game.account.settings
	if s.get("reduce_motion", false): return 0
	var bands: Array = ContentDB.config("fx_art").get("bands", [])
	var band := 0
	for i in bands.size():
		if (bands[i] as Array).any(func(t): return int(t) == tier): band = i   # JSON reads its tiers as floats
	return mini(band, 1) if s.get("battery_saver", false) else band

## The sheet row of an element at a band: the manifest's element (a sub-element takes its parent's, `none` formless).
static func form_row(element: String, band: int) -> int:
	var a: Dictionary = ContentDB.config("fx_art")
	var els: Array = a.get("elements", [])
	var el := str(a.get("element_of", {}).get(element, element))
	if not el in els: el = str(a.get("element_of", {}).get(CombatRules.parent_element(element), "formless"))
	return band * els.size() + maxi(0, els.find(el))

## A sprite scale snapped to halves, so every art pixel stays a whole number of screen pixels; `down` never rounds past `px`.
static func snap_scale(s: float, down := false) -> float:
	var v := floorf(s * 2.0) / 2.0 if down else roundf(s * 2.0) / 2.0
	return clampf(v, 0.5, 4.0)

## Play a form's animation at `pos` (its anchor on the effect's anchor), facing `facing`, at its element's row and the
## tier's band. extra: scale (1; scale_y when a line is stretched along the reach only), delay (s before it starts),
## start (s into it to begin, when the hit frame must land before the sheet's impact), travel (px it moves over its
## life), tiles (copies side by side along the facing), alpha.
func play_form(form: String, element: String, tier: int, pos: Vector2, facing: int, extra := {}) -> Dictionary:
	var a := form_spec(form)
	if a.is_empty(): return {}
	var band := band_of(tier)
	var e := {"form": form, "row": form_row(element, band), "scale": float(extra.get("scale", 1.0)), "start": float(extra.get("start", 0.0)),
		"scale_y": float(extra.get("scale_y", extra.get("scale", 1.0))),
		"travel": extra.get("travel", Vector2.ZERO), "tiles": int(extra.get("tiles", 1)), "alpha": float(extra.get("alpha", 1.0)), "facing": facing,
		"turn": float(extra.get("turn", 0.0)),
		"delay": float(extra.get("delay", 0.0)), "dur": float(a.frames) / float(a.fps) - float(extra.get("start", 0.0))}
	if e.dur <= 0.0: return {}
	add("anim", pos, e)
	return e

## P6e a technique cast at its tier (docs/moments_design.md §5), by the caster at `at` facing `facing` toward `target`
## (the foe it lands on: the room's nearest in reach, or a page's staged one): a ring at the feet (from tier 2), a wash
## of its element over the screen (from tier 3, under the flash limiter; only on the room's layer), and its shape, drawn
## at the reach it really strikes (§5.4, `reach` the hitbox's by default): a slash, a wave along the reach, a ring at it
## with echo rings inside, a rain of streaks, a pillar on the foe, or a ring and motes round the caster. A bolt is drawn
## by its projectile.
## Decision 23: with the technique's form animation (`vfx.anim`, data/fx_art.json) the cast plays that sheet instead of
## the procedural shape, timed so its impact frame lands on the pose's hit frame (`windup`, the timeline's hit_at),
## facing the cast, sized to the hitbox and at its tier's band; an area's edge (a ring at the true reach, §5.4) and
## a heal's radius are still drawn at the reach. The procedural shapes remain for a technique without a sheet.
## On the top-down plane (redesign Phase 2) the cast follows its `aim`: the sheets and shapes turn to it, mirrored so none
## draws upside down.
func cast(t: Dictionary, at: Vector2, facing: int, col: Color, target: Vector2, windup := -1.0, reach := -1.0, aim := Vector2.ZERO) -> void:
	var n := MomentRules.tier_numbers("tech:" + str(t.get("id", "")))
	var tier := int(t.get("vfx", {}).get("tier", 1))
	if reach < 0.0: reach = float(t.hitbox.x[1])
	var turn := 0.0
	if aim != Vector2.ZERO:
		facing = 1 if aim.x >= 0.0 else -1
		turn = (aim * facing).angle()
	var up := Vector2(0, -(chest - 6.0))
	if float(n.cast_ring_r) > 0.0: add("ring", at, {"color": col, "radius": float(n.cast_ring_r), "dur": 0.3})
	if float(n.tint_alpha) > 0.0 and world: add("tint", at, {"color": Color(col, float(n.tint_alpha)), "dur": 0.4})
	var shape := str(t.get("vfx", {}).get("shape", "strike"))
	var form := str(t.get("vfx", {}).get("anim", ""))
	if not form_spec(form).is_empty():
		if forms: _cast_form(t, form, facing, tier, reach, at, target, windup, turn)
		if shape == "ring": add("wave", at, {"color": col, "radius": reach, "size": n.wave_width, "dur": 0.45})
		if shape == "domain" and t.has("heal_radius"): add("ring", at, {"color": Color(col, 0.7), "radius": float(t.heal_radius), "dur": 0.6})
		return
	match shape:
		"strike": add("slash", at + Vector2(facing * 40, 0).rotated(turn) + up, {"color": col, "facing": facing, "turn": turn, "radius": 46.0 + 6.0 * (tier - 1), "dur": 0.3})
		"wave": add("talisman_wave", at + up, {"color": col, "facing": facing, "radius": reach, "size": 20 + 2 * tier, "dur": 0.4})
		"ring":
			for i in int(n.echoes) + 1:
				add("wave", at, {"color": col, "radius": reach * [1.0, 0.7, 0.4, 0.55][i], "size": n.wave_width, "dur": 0.45, "delay": 0.08 * i})
		"rain": add("rain", at + Vector2(facing * reach * 0.5, 0).rotated(turn), {"color": col, "radius": reach * 0.5, "height": 240.0, "dur": 0.5,
			"count": MomentRules.particle_count(3 * int(t.get("hits", 1)) + 2 * tier)})
		"pillar": add("pillar", target, {"color": col, "radius": 12.0 + 4.0 * tier, "height": 300.0, "dur": 0.35})
		"domain":
			add("ring", at, {"color": col, "radius": float(t.get("heal_radius", reach)), "dur": 0.6})
			add("motes", at + Vector2(0, -10), {"color": col, "dur": 0.8})

## A form's sheet on a cast: anchored by its `at` (the caster's chest or feet, the foe's feet or chest), sized by its
## `size` rule (band: bigger by tier, never past a strike's reach; reach: snapped down so a ring or a line never
## passes the hitbox; tile: repeated across the reach; travel: the crest crosses the reach over its life), and
## started so its impact frame lands on the hit frame: later when the wind-up is long, part-way in when it is short.
func _cast_form(t: Dictionary, form: String, facing: int, tier: int, reach: float, at: Vector2, target: Vector2, windup: float, turn := 0.0) -> void:
	var a := form_spec(form)
	var band := band_of(tier)
	var span := float(a.span)
	var extra := {"turn": turn}
	var s := 1.0
	match str(a.size):
		"band":
			s = float(BAND_SCALE[band])
			if a.get("fit", false): s = minf(s, maxf(1.0, snap_scale(reach * 1.15 / span, true)))   # never past the reach, never under native
		"reach": s = maxf(1.0, snap_scale(reach / span, true))
		"stretch":   # a line along the reach: its exact length, the band's height
			s = reach / span
			extra.scale_y = float(BAND_SCALE[band])
		"tile":
			s = 1.0 if band < 2 else 1.5
			extra.tiles = maxi(1, ceili(reach / (float(a.cell[0]) * s)))
		"travel":
			s = float(BAND_SCALE[band])
			extra.travel = Vector2(facing * maxf(0.0, reach - span * s * 0.5), 0).rotated(turn)
	extra.scale = s
	var pos := at
	match str(a.at):
		"chest": pos = at + Vector2(0, -chest)
		"target": pos = target
		"target_chest": pos = target + Vector2(facing * 30, 0).rotated(turn) + Vector2(0, -(chest - 6.0))
	if windup >= 0.0:
		var lead := windup - float(a.impact) / float(a.fps)
		if lead >= 0.0: extra.delay = lead
		else: extra.start = -lead
	play_form(form, str(t.get("element", "none")), tier, pos, facing, extra)

## A hit's marks at `pos` (§5.2): its number (when `numbers`; a crit gold, Qi teal, Soul violet, a blow on the player
## red), sized by the technique's tier and stacked with the cast's other hits on that target (`stack`), and a spark in
## its element at the tier's count, size, reach and style. `source` is the blow's ("tech:<id>" for a technique).
func hit(pos: Vector2, amount: float, source: String, element: String, dtype: String, crit: bool, stack := "", numbers := true, on_player := false) -> void:
	var color = UiKit.PAPER
	if on_player: color = UiKit.RED
	elif crit: color = UiKit.GOLD
	elif dtype == "qi": color = UiKit.QI
	elif dtype == "soul": color = UiKit.SOUL
	var n := MomentRules.tier_numbers(source)
	var tech := ContentDB.entry("techniques", source.trim_prefix("tech:")) if source.begins_with("tech:") else {}
	if numbers:
		number(pos, UiKit.short(amount), color, int(n.number_size) if not tech.is_empty() else 22, crit, stack + source if not tech.is_empty() else "", amount)
	if not sparks: return
	add("spark", pos + Vector2(0, 20), {"color": SpriteCache.element_color(element), "dur": 0.25,
		"count": MomentRules.particle_count(int(n.spark_count)), "size": n.spark_size, "radius": n.spark_reach, "core": n.core_r,
		"style": tech.get("vfx", {}).get("particles", MomentRules.particle_style("", element, dtype))})

## The frame of a form's sheet at `t` seconds in (held on the last frame).
static func form_frame(a: Dictionary, t: float) -> int:
	return clampi(int(t * float(a.fps)), 0, int(a.frames) - 1)

## Draw one frame of a form sheet: `anchor` on `at`, mirrored for a left facing, `scale` whole halves (a stretched line
## keeps `scale_y` and takes its exact length along the reach).
## `turn`: the top-down aim's turn off the facing (redesign Phase 2).
func draw_form(a: Dictionary, at: Vector2, frame: int, row: int, facing: int, scale: float, alpha := 1.0, scale_y := -1.0, turn := 0.0) -> void:
	if lazy_sheets and SpriteCache.tex_async(str(a.file)) == null: return
	draw_form_on(self, a, at, frame, row, facing, scale, alpha, scale_y, turn)

## The same frame on any canvas (a page's card shows its art's impact frame).
static func draw_form_on(ci: CanvasItem, a: Dictionary, at: Vector2, frame: int, row: int, facing: int, scale: float, alpha := 1.0, scale_y := -1.0, turn := 0.0) -> void:
	var tex := SpriteCache.tex(str(a.file))
	if tex == null: return
	var cell := Vector2(float(a.cell[0]), float(a.cell[1]))
	var anchor := Vector2(float(a.anchor[0]), float(a.anchor[1]))
	ci.draw_set_transform(at.snapped(Vector2(2, 2)), turn, Vector2(float(facing) * scale, scale_y if scale_y > 0.0 else scale))
	ci.draw_texture_rect_region(tex, Rect2(-anchor, cell), Rect2(Vector2(frame * cell.x, row * cell.y), cell), Color(1, 1, 1, alpha))
	ci.draw_set_transform(Vector2.ZERO)

## A screen tint (a Heaven-grade technique, §5.2): none with Reduce motion or Battery saver, 0.3 of its alpha with Bright
## flashes off, and at most one flash or tint a second from every source (the flash limiter, §5.10).
func _tint_allowed(e: Dictionary) -> bool:
	var s: Dictionary = Game.account.settings
	if s.get("reduce_motion", false) or s.get("battery_saver", false): return false
	if not s.get("flashes", true): e.color = Color(e.color, e.color.a * 0.3)
	return MomentView.claim_flash(float(MomentRules.cfg().get("settings", {}).get("flash_gap_s", 1.0)))

## A damage number; none with Settings › Damage numbers off (P6 finding 2). With a `stack` key (a target and a technique)
## the hits of one cast rise one after another, each 18 px over the one before and swaying, and three or more add up to
## a total (§5.5).
func number(pos: Vector2, text: String, color: Color, size := 22, crit := false, stack := "", value := 0.0) -> void:
	if not Game.account.settings.get("damage_numbers", true): return
	size = roundi(size * number_scale)
	if stack == "":
		label(pos, text, color, size + (8 if crit else 0), crit)
		return
	var cfg: Dictionary = MomentRules.cfg().get("numbers", {})
	var now := clock
	var st: Dictionary = stacks.get(stack, {})
	if st.is_empty() or now - float(st.last) > float(cfg.get("stack_s", 0.3)): st = {"n": 0, "sum": 0.0, "at": pos, "size": size}
	var i := int(st.n)
	st.n = i + 1
	st.sum = float(st.sum) + value
	st.last = now
	stacks[stack] = st
	if i >= int(cfg.get("cap", 6)): return   # past the cap a hit only adds to the total
	var y: float = float(st.top.pos.y) - float(cfg.get("step_px", 18)) if st.has("top") else float(st.at.y)
	add("number", Vector2(float(st.at.x) + (1 if i % 2 == 0 else -1) * float(cfg.get("sway_px", 12)), y), {"text": text, "color": color,
		"size": size + (8 if crit else 0), "dur": 1.0, "delay": float(cfg.get("step_s", 0.06)) * i, "vel": Vector2(0, -70.0)})   # one speed, so a crit keeps its place
	st.top = fx.back()

## A parry (the caster's counter meeting a blow): a pale gold flash in front of the chest and the word over the head.
func parry(feet: Vector2, facing: int) -> void:
	add("flash", feet + Vector2(facing * 20, -50), {"color": UiKit.PALE_GOLD, "radius": 30, "dur": 0.25})
	label(feet + Vector2(0, -110), Tx.t("world_view.parry"), UiKit.GOLD, 22)

## A word that rises like a number (Miss, Evade, Parry, a foe's "!"), whatever the Damage numbers setting.
func label(pos: Vector2, text: String, color: Color, size := 22, fast := false) -> void:
	add("number", pos + Vector2(randf_range(-10, 10), 0), {"text": text, "color": color, "size": roundi(size * number_scale), "dur": 1.0,
		"vel": Vector2(randf_range(-12, 12), -90.0 if fast else -70.0)})

func _process(delta: float) -> void:
	step(fixed_step if fixed_step > 0.0 else delta)

## Advance every effect by `delta` seconds (a staged layer is stepped by its owner's clock instead of its own process).
func step(delta: float) -> void:
	clock += delta
	for e in fx.duplicate():
		e.t = float(e.t) + delta
		e.pos = e.pos + e.vel * delta   # a number waiting its turn rises unseen with its stack, so the column keeps its spacing
		if e.kind == "number": e.vel = e.vel * (1.0 - delta * 1.5)
		if float(e.t) >= float(e.dur): fx.erase(e)
	_totals()
	queue_redraw()

## A stack of three or more hits, 0.1 s after its last: the sum in pale gold, a size up, 24 px over the top number.
func _totals() -> void:
	var cfg: Dictionary = MomentRules.cfg().get("numbers", {})
	var now := clock
	for key in stacks.keys():
		var st: Dictionary = stacks[key]
		if now - float(st.last) < float(cfg.get("total_after_s", 0.1)) + float(cfg.get("step_s", 0.06)) * mini(int(st.n), int(cfg.get("cap", 6))): continue
		if int(st.n) >= int(cfg.get("total_from", 3)) and st.has("top"):
			add("number", Vector2(float(st.at.x), float(st.top.pos.y) - float(cfg.get("total_up_px", 24))), {"text": UiKit.short(float(st.sum)), "color": UiKit.PALE_GOLD,
				"size": int(st.size) + int(cfg.get("total_plus_px", 2)), "dur": 1.1, "vel": Vector2(0, -60.0)})
		stacks.erase(key)

func _draw() -> void:
	if world: _draw_state()
	_draw_fx()

## What the room's state holds, under the transient effects.
func _draw_state() -> void:
	# S48 Array Plates laid in a fight are drawn from Combat's state, on the ground under everything else.
	if Game.combat:
		for a in Game.combat.arrays: _draw_array(a)
		for f in Game.combat.ground_fires: _draw_ground_fire(f)   # v1.2 Phase D: cinders and pyre rings
	# S28 v1.2: a held Presence is a pale ring on the ground; where it meets a foe's, the boundary shimmers.
	if Game.field and Game.active() != null and Game.field.is_on(Game.active_id): _draw_presence(Game.active())
	if Game.field and Game.active() != null and Game.field.sphere_on(Game.active_id): _draw_sphere(Game.active())
	# Projectiles live in the RoomRuntime and are drawn from state.
	if Game.room_rt:
		for p in Game.room_rt.projectiles:
			if float(p.get("delay", 0.0)) > 0.0: continue
			_draw_projectile(p)

func _draw_fx() -> void:
	for e in fx:
		if float(e.t) < 0.0: continue
		var k: float = float(e.t) / maxf(0.001, float(e.dur))
		var c: Color = e.color
		match str(e.kind):
			"number":
				var a := 1.0 if k < 0.6 else 1.0 - (k - 0.6) / 0.4
				UiKit.draw_outlined(self, e.text, e.pos + Vector2(-100, 0), int(e.size), Color(c, a), HORIZONTAL_ALIGNMENT_CENTER, 200)
			"spark":
				_draw_spark(e, k, c)
			"slash":
				var f := float(e.facing)
				var pts := PackedVector2Array()
				for i in 9:
					var ang := lerpf(-1.1, 1.0, i / 8.0)
					pts.append(e.pos + Vector2(cos(ang) * f, sin(ang)).rotated(float(e.turn)) * float(e.radius))
				draw_polyline(pts, Color(c, 1.0 - k), 6.0 * (1.0 - k) + 2.0)
				draw_polyline(pts, Color(1, 1, 1, 0.7 * (1.0 - k)), 2.0)
			"dust":
				for i in 5:
					var off := Vector2((i - 2) * 9.0 * (1.0 + k), -6.0 * k * (1 + i % 2))
					draw_circle(e.pos + off, 6.0 * (1.0 - k) + 2.0, Color(0.75, 0.68, 0.55, 0.6 * (1.0 - k)))
			"ring":
				if int(e.count) > 1:
					# P6: `count` rings at the feet, the outer faint and the inner bright (a major breakthrough, mockup 05).
					var fade4 := 1.0 if k < 0.6 else 1.0 - (k - 0.6) / 0.4
					draw_set_transform(e.pos, 0.0, Vector2(1, 0.215))
					for i in int(e.count):
						var u := float(i) / float(int(e.count) - 1)
						draw_arc(Vector2.ZERO, float(e.radius) * (1.0 - 0.66 * u) * (0.94 + 0.06 * minf(1.0, k * 4.0)), 0, TAU, 48,
							Color(c.lerp(Color.WHITE, 0.6 * u), (0.35 + 0.55 * u) * fade4), 2.5)
				else:
					draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
					draw_arc(Vector2.ZERO, float(e.radius) * (0.3 + k), 0, TAU, 40, Color(c, 1.0 - k), 4.0)
				draw_set_transform(Vector2.ZERO)
			"note":
				# A musical note of the flute's melody (S47 v1.1): rises, sways and fades.
				var sway := sin(float(e.t) * 5.0 + float(e.radius)) * 6.0
				_draw_note(e.pos + Vector2(sway, 0), c, 1.0 if k < 0.5 else 1.0 - (k - 0.5) * 2.0, float(e.size) / 20.0)
			"wave":
				draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
				draw_arc(Vector2.ZERO, float(e.radius) * k, 0, TAU, 48, Color(c, 0.9 * (1.0 - k)), float(e.size) * (1.0 - k) + 2.0)
				draw_set_transform(Vector2.ZERO)
			"spiral":
				for i in 24:
					var ang := i * 0.55 + k * 8.0
					var r := 10.0 + i * 4.0 * k
					draw_rect(Rect2((e.pos + Vector2(cos(ang), sin(ang) * 0.5) * r - Vector2(0, i * 5.0 * k)).snapped(Vector2(2, 2)), Vector2(4, 4)), Color(c, 1.0 - k))
			"motes":
				for i in 6:
					var ph := fmod(k + i / 6.0, 1.0)
					var p2: Vector2 = e.pos + Vector2(sin(i * 2.1 + ph * 4.0) * 26.0, -ph * 70.0)
					draw_rect(Rect2(p2.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(c, 0.8 * (1.0 - ph)))
			"flash":
				var bright := 0.5 if Game.account.settings.get("flashes", true) else 0.15
				draw_circle(e.pos, float(e.radius) * (0.5 + k), Color(c, bright * (1.0 - k)))
			"pagoda":
				# A jade pagoda falls over the foe and holds it; it fades as the prison lifts.
				var drop := minf(1.0, k * 8.0)
				var pp: Vector2 = e.pos + Vector2(0, -150.0 * (1.0 - drop))
				var fade2 := 0.9 if k < 0.85 else (1.0 - k) / 0.15 * 0.9
				for i in 4:
					var w := 44.0 - i * 8.0
					var y := -i * 26.0
					draw_rect(Rect2(pp + Vector2(-w * 0.5 + 4, y - 22), Vector2(w - 8, 18)), Color(0.75, 0.2, 0.2, fade2 * 0.8))
					draw_colored_polygon(PackedVector2Array([pp + Vector2(-w * 0.5 - 6, y - 22), pp + Vector2(w * 0.5 + 6, y - 22), pp + Vector2(w * 0.5 - 4, y - 30),
						pp + Vector2(-w * 0.5 + 4, y - 30)]), Color(c, fade2))
				draw_rect(Rect2(pp + Vector2(-2, -128), Vector2(4, 12)), Color(UiKit.GOLD, fade2))
			"seal_slam":
				var land := minf(1.0, k * 4.0)
				var sp2: Vector2 = e.pos + Vector2(0, -200.0 * (1.0 - land) - 40.0)
				if k < 0.5:
					draw_rect(Rect2(sp2 - Vector2(34, 24), Vector2(68, 48)), Color(c, 0.9))
					draw_rect(Rect2(sp2 - Vector2(22, 12), Vector2(44, 24)), Color(0.8, 0.2, 0.2, 0.9))
				if land >= 1.0:
					var kk := (k - 0.25) / 0.75
					draw_set_transform(e.pos, 0.0, Vector2(1, 0.35))
					draw_arc(Vector2.ZERO, float(e.radius) * kk, 0, TAU, 48, Color(c, 0.9 * (1.0 - kk)), 10.0 * (1.0 - kk) + 2.0)
					draw_set_transform(Vector2.ZERO)
			"talisman_wave":
				# The talisman's stroke: a long blade of light across the room in front of you.
				var f2 := float(e.get("facing", 1))
				var len2 := float(e.radius) * minf(1.0, k * 3.0)
				var a3 := 1.0 - k
				var h2 := float(e.size)   # 20 px; a technique's is 20 + 2 × its tier
				draw_rect(Rect2(e.pos + Vector2(0 if f2 > 0 else -len2, -h2 * 0.5), Vector2(len2, h2)), Color(c, 0.35 * a3))
				draw_rect(Rect2(e.pos + Vector2(0 if f2 > 0 else -len2, -h2 * 0.2), Vector2(len2, h2 * 0.4)), Color(1, 1, 0.9, 0.9 * a3))
			"pill_cloud":
				# A Halo or Soul pill forms (G1): a coloured cloud boils up over the furnace, then thins away.
				var fade := 1.0 if k < 0.7 else 1.0 - (k - 0.7) / 0.3
				for i in 14:
					var ang := i * 2.39996 + k * 1.6
					var rr := 18.0 + (i % 5) * 11.0 + 20.0 * k
					var pc: Vector2 = e.pos + Vector2(cos(ang) * rr * 1.5, sin(ang) * rr * 0.45 - 40.0 * k)
					draw_circle(pc, 16.0 + (i % 3) * 6.0 + 10.0 * k, Color(c, 0.22 * fade))
				for i in 10:
					var ph := fmod(k * 2.0 + i / 10.0, 1.0)
					var sp: Vector2 = e.pos + Vector2(sin(i * 1.7 + ph * 5.0) * 60.0, -20.0 - ph * 90.0)
					draw_rect(Rect2(sp.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(1.0, 0.95, 0.75, 0.9 * fade * (1.0 - ph)))
			"heaven_cloud":
				# S49 heavenly phenomenon: auspicious clouds gather high over the room and pour light down on you.
				var grow := minf(1.0, k * 3.0)
				var fade2 := 1.0 if k < 0.75 else 1.0 - (k - 0.75) / 0.25
				var top: Vector2 = e.pos + Vector2(0, -320)
				draw_rect(Rect2(e.pos + Vector2(-34.0 * grow, -300), Vector2(68.0 * grow, 300)), Color(1.0, 0.93, 0.7, 0.12 * fade2))
				draw_rect(Rect2(e.pos + Vector2(-12.0 * grow, -300), Vector2(24.0 * grow, 300)), Color(1.0, 0.97, 0.85, 0.2 * fade2))
				_cloud_bank(top, 620.0 * (0.4 + 0.6 * grow), 70.0, c, Color(1.0, 0.98, 0.9), 0.9 * fade2, 3, float(e.t))
				for i in 14:
					var ph := fmod(float(e.t) * 0.35 + i / 14.0, 1.0)
					var mp: Vector2 = e.pos + Vector2((_hash(i, 5) - 0.5) * 90.0, -ph * 300.0)
					draw_rect(Rect2(mp.snapped(Vector2(2, 2)), Vector2(4, 4)), Color(1.0, 0.95, 0.75, 0.9 * fade2 * (1.0 - ph)))
			"heaven_storm":
				# A tribulation's sky: a dark bank low over the room, lit from inside, and bolts that fall near you.
				var grow2 := minf(1.0, k * 4.0)
				var fade3 := 1.0 if k < 0.8 else 1.0 - (k - 0.8) / 0.2
				var top2: Vector2 = e.pos + Vector2(0, -300)
				var beat := int(float(e.t) * 3.0)
				var lit := fmod(float(e.t) * 3.0, 1.0) < 0.3
				_cloud_bank(top2, 820.0 * (0.4 + 0.6 * grow2), 80.0, Color(0.2, 0.21, 0.29), Color(0.55, 0.62, 0.8) if lit else Color(0.34, 0.36, 0.46), fade3, 7, float(e.t))
				if lit:
					var bx := (_hash(beat, 11) - 0.5) * 420.0
					var pts2 := PackedVector2Array()
					var yy := -290.0
					var xx := bx
					while yy < 0.0:
						pts2.append(e.pos + Vector2(xx, yy))
						yy += 40.0 + _hash(beat * 7 + int(yy), 12) * 30.0
						xx += (_hash(beat * 13 + int(yy), 13) - 0.5) * 50.0
					pts2.append(e.pos + Vector2(xx, 0))
					draw_polyline(pts2, Color(c, 0.35 * fade3), 7.0)
					draw_polyline(pts2, Color(0.95, 0.97, 1.0, 0.95 * fade3), 2.0)
			"text":
				var a2 := 1.0 if k < 0.7 else 1.0 - (k - 0.7) / 0.3
				UiKit.draw_outlined(self, e.text, e.pos + Vector2(-200, 0), int(e.size), Color(c, a2), HORIZONTAL_ALIGNMENT_CENTER, 400)
			"pillar":
				# P6: a column of light on its target, `radius` half-wide and `height` tall; it widens over the first fifth
				# and fades over the last seventh (a major breakthrough, mockup 05).
				_pillar(e.pos, float(e.radius) * minf(1.0, k * 5.0), float(e.height), c, 1.0 if k < 0.86 else (1.0 - k) / 0.14)
			"converge":
				# P6: `count` motes along eight curved paths from r `radius` into the target, each with a short trail.
				var n2 := maxi(1, int(e.count))
				for i in n2:
					var ang := TAU * (i % 8) / 8.0 + 0.3
					var lap := floorf(i / 8.0)
					var from := Vector2(cos(ang), sin(ang) * 0.6) * float(e.radius) * (1.0 - 0.3 * lap)
					var ctrl := from.rotated(0.7) * 0.55
					for j in 3:
						var u := clampf(k * 1.1 - 0.05 * j - 0.04 * lap, 0.0, 1.0)
						var q := from.lerp(ctrl, u).lerp(ctrl.lerp(Vector2.ZERO, u), u)
						var a4 := minf(1.0, u * 6.0) * (1.0 if u < 0.85 else (1.0 - u) / 0.15) * (1.0 - 0.3 * j)
						draw_circle(e.pos + q, 6.0 - j * 1.5, Color(c, 0.55 * a4))
						if j == 0: draw_circle(e.pos + q, 2.0, Color(1, 1, 1, 0.9 * a4))
			"rain":
				# P6e: `count` streaks falling over the hitbox (`radius` either side of it), each from `height` up to the ground.
				for i in int(e.count):
					var u := clampf(k * 1.6 - _hash(i, 21) * 0.6, 0.0, 1.0)
					if u <= 0.0 or u >= 1.0: continue
					var x := (_hash(i, 22) * 2.0 - 1.0) * float(e.radius)
					var head: Vector2 = e.pos + Vector2(x - 30.0 * (1.0 - u), -float(e.height) * (1.0 - u))
					draw_line(head, head + Vector2(10, -34), Color(c, 0.85 * (1.0 - u * 0.5)), 3.0)
					draw_line(head, head + Vector2(5, -17), Color(1, 1, 1, 0.8 * (1.0 - u)), 1.5)
			"tint":
				# P6e: the screen washed in a Heaven-grade technique's colour for a moment (the view, wherever the camera is).
				var view := get_canvas_transform().affine_inverse() * get_viewport_rect()
				draw_rect(view, Color(c, c.a * (1.0 - k)))
			"anim":
				# Decision 23: a technique form's frames from its sheet, at its element's row and its tier's band, moving
				# along `travel` over its life (a wave's crest) or repeated `tiles` times along the facing (a rain).
				var a := form_spec(str(e.form))
				if not a.is_empty():
					var frame := form_frame(a, float(e.t) + float(e.start))
					var head: Vector2 = e.pos + (e.travel as Vector2) * k
					var s := float(e.scale)
					for i in maxi(1, int(e.tiles)):
						draw_form(a, head + Vector2(float(e.facing) * i * float(a.cell[0]) * s, 0).rotated(float(e.turn)), frame, int(e.row), int(e.facing), s,
							float(e.alpha), float(e.scale_y), float(e.turn))

## A hit spark (§5.2, §5.6): `count` bits flying out to `radius` (its tier's reach; 28 at tier 1), `size` px shrinking
## to 2, and a white core of `core`; the style draws them as squares, rising embers, falling shards, ink drops falling
## under 400 px/s², or three thin rings.
func _draw_spark(e: Dictionary, k: float, c: Color) -> void:
	var n := int(e.count) if int(e.count) > 0 else 8
	var reach := float(e.radius)
	var sz := float(e.size)
	match str(e.style):
		"ring":
			for i in 3:
				var kk := clampf(k * 1.3 - i * 0.15, 0.0, 1.0)
				draw_arc(e.pos, reach * kk, 0, TAU, 32, Color(c, 0.8 * (1.0 - kk)), 2.0)
		_:
			for i in n:
				var ang := i * TAU / n + 0.3
				var dir := Vector2(cos(ang), sin(ang) * 0.7)
				var p1: Vector2 = e.pos + dir * (6.0 + (reach - 6.0) * k)
				match str(e.style):
					"shard":
						p1 += Vector2(0, 46.0 * k * k)
						draw_line(p1, p1 + dir * (4.0 + sz) * (1.0 - k * 0.5), Color(c, 1.0 - k), 2.0)
					"ink":
						p1 += Vector2(0, 200.0 * pow(k * float(e.dur), 2.0))   # 400 px/s² over the spark's life
						draw_circle(p1, (sz * 0.6) * (1.0 - k) + 1.5, Color(c, 1.0 - k))
					"ember":   # a square with a hot pale-gold heart, rising and flickering
						p1 = (p1 + Vector2(0, -40.0 * k)).snapped(Vector2(2, 2))
						var s2 := (sz - 2.0) * (1.0 - k) + 2.0
						var a2 := (1.0 - k) * (0.75 + 0.25 * absf(sin(float(e.t) * 30.0 + i)))
						draw_rect(Rect2(p1, Vector2.ONE * s2), Color(c, a2))
						draw_rect(Rect2(p1 + Vector2.ONE * s2 * 0.25, Vector2.ONE * s2 * 0.5), Color(UiKit.PALE_GOLD, a2))
					_:
						draw_rect(Rect2(p1.snapped(Vector2(2, 2)), Vector2.ONE * ((sz - 2.0) * (1.0 - k) + 2.0)), Color(c, 1.0 - k))
	draw_circle(e.pos, float(e.core) * (1.0 - k), Color(1, 1, 1, 0.8 * (1.0 - k)))

## A column of light: faint at its edges and bright along its middle, masked to fade toward the top and at the feet,
## with a thin white core.
func _pillar(feet: Vector2, half: float, height: float, c: Color, a: float) -> void:
	if half <= 0.5 or a <= 0.0: return
	var xs := [-1.0, -0.35, 0.0, 0.35, 1.0]
	var ax := [0.0, 0.3, 0.8, 0.3, 0.0]
	var ys := [0.0, 0.4, 0.9, 1.0]           # from the column's top (0) to the feet (1)
	var ay := [0.1, 1.0, 1.0, 0.0]
	for yi in 3:
		for xi in 4:
			var pts := PackedVector2Array()
			var cols := PackedColorArray()
			for q in [[xi, yi], [xi + 1, yi], [xi + 1, yi + 1], [xi, yi + 1]]:
				pts.append(feet + Vector2(xs[q[0]] * half, -height * (1.0 - ys[q[1]])))
				cols.append(Color(c.lerp(Color.WHITE, 0.5 * ax[q[0]]), ax[q[0]] * ay[q[1]] * a))
			draw_polygon(pts, cols)
	var w := clampf(half * 0.05, 1.5, 4.0)
	draw_polygon(PackedVector2Array([feet + Vector2(-w, -height), feet + Vector2(w, -height), feet + Vector2(w, 0), feet + Vector2(-w, 0)]),
		PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0), Color(1, 1, 1, 0.85 * a), Color(1, 1, 1, 0.85 * a)]))

## A soft bank of cloud: many flattened, overlapping puffs (a shadowed underside, a lit top) that drift slowly.
func _cloud_bank(center: Vector2, width: float, height: float, base: Color, lit: Color, alpha: float, salt: int, t: float) -> void:
	for layer in 2:
		for i in 34:
			var u := _hash(i, salt) - 0.5
			var rx := 34.0 + _hash(i, salt + 1) * 46.0
			var arch := (1.0 - absf(u) * 2.0) * height * 0.6
			var at: Vector2 = center + Vector2(u * width + sin(t * 0.5 + i) * 6.0, (_hash(i, salt + 2) - 0.5) * height * 0.4 - arch * 0.5)
			if layer == 1:
				at += Vector2(0, -rx * 0.22)
				rx *= 0.7
			draw_set_transform(at, 0.0, Vector2(1.0, 0.46))
			draw_circle(Vector2.ZERO, rx, Color(base if layer == 0 else lit, (0.3 if layer == 0 else 0.16) * alpha))
	draw_set_transform(Vector2.ZERO)

## v1.2 the Sphere: a filled circle of its element's colour with a bright rim; the Sword Domain rings it with turning
## blade strokes.
func _draw_sphere(c) -> void:
	var st: ActorState = Game.actor_state(c.id)
	if st == null: return
	var sd: Dictionary = Game.field.sphere_of(c)
	if sd.is_empty(): return
	var t := float(Time.get_ticks_msec()) / 1000.0
	var r := float(sd.radius)
	var col := Color(str(ContentDB.config("elements").get("colors", {}).get(str(sd.element), "#e8d9a0"))) if str(sd.element) != "sword" else Color("dce8f0")
	draw_set_transform(st.plane, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, r, Color(col, 0.10))
	draw_arc(Vector2.ZERO, r, 0, TAU, 96, Color(col, 0.7), 3.0)
	draw_arc(Vector2.ZERO, r * 0.94, 0, TAU, 96, Color(col, 0.25), 1.5)
	if sd.get("domain", false) or str(sd.element) in ["metal", "star"]:
		for i in 12:
			var a := t * 0.8 + i * TAU / 12.0
			var p := Vector2(cos(a), sin(a)) * r * 0.97
			draw_line(p, p + Vector2(cos(a + 1.3), sin(a + 1.3)) * 22.0, Color(1, 1, 1, 0.75), 2.0)
	draw_set_transform(Vector2.ZERO)

## An array on the ground: two rings of the array's colour, eight trigram strokes between them and a slow turn.
func _draw_presence(c) -> void:
	var st: ActorState = Game.actor_state(c.id)
	if st == null: return
	var t := float(Time.get_ticks_msec()) / 1000.0
	var r: float = Game.field.radius_of(c)
	var col := UiKit.PALE_GOLD
	draw_set_transform(st.plane, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, r, Color(col, 0.05))
	draw_arc(Vector2.ZERO, r, 0, TAU, 72, Color(col, 0.35 + 0.1 * sin(t * 2.0)), 2.0)
	# Two faint ripples travel outward while it is held.
	for i in 2:
		var k := fmod(t * 0.5 + i * 0.5, 1.0)
		draw_arc(Vector2.ZERO, r * (0.3 + 0.7 * k), 0, TAU, 48, Color(col, 0.25 * (1.0 - k)), 2.0)
	draw_set_transform(Vector2.ZERO)
	var cl: Dictionary = Game.field.clash_of(c.id)
	if cl.is_empty(): return
	var at := Vector2(float(cl.x), float(cl.y))
	var dir: Vector2 = (at - st.plane).normalized() if at.distance_to(st.plane) > 1.0 else Vector2.RIGHT
	var side := Vector2(-dir.y, dir.x)
	var wcol := UiKit.GOLD if str(cl.winner) == "you" else (UiKit.RED if str(cl.winner) == "foe" else UiKit.MIST)
	# A standing wall of light: a wavering line across the ground and up into the air.
	var pts := PackedVector2Array()
	for i in 13:
		var u := (i - 6) / 6.0
		var wob := sin(t * 6.0 + i) * 4.0
		pts.append(at + side * u * 70.0 * 0.35 + dir * wob + Vector2(0, -u * 0.0))
	draw_polyline(pts, Color(wcol, 0.8), 3.0)
	for i in 7:
		var h := 30.0 + 20.0 * i
		var wob2 := sin(t * 5.0 + i * 0.8) * 5.0
		draw_line(at + Vector2(wob2 - 4, -h), at + Vector2(wob2 + 4, -h - 14), Color(wcol, 0.55 - i * 0.06), 2.0)

## v1.2 Phase D: a burning patch on the ground: an ember glow with flickering tongues, fading in its last second.
func _draw_ground_fire(f: Dictionary) -> void:
	var at := Vector2(float(f.x), float(f.y))
	var r := float(f.r)
	var fade := clampf(float(f.t), 0.0, 1.0)
	var t := float(Time.get_ticks_msec()) / 1000.0
	draw_set_transform(at, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, r, Color(0.9, 0.35, 0.1, 0.18 * fade))
	draw_circle(Vector2.ZERO, r * 0.6, Color(1.0, 0.55, 0.15, 0.22 * fade))
	draw_arc(Vector2.ZERO, r, 0, TAU, 48, Color(1.0, 0.45, 0.12, 0.6 * fade), 2.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	for i in 6:
		var x := at.x + (float(i) - 2.5) / 2.5 * r * 0.8
		var h := 14.0 + 10.0 * absf(sin(t * 7.0 + float(i) * 1.7))
		var base := Vector2(x, at.y - 2)
		draw_colored_polygon(PackedVector2Array([base + Vector2(-5, 0), base + Vector2(5, 0), base + Vector2(0, -h)]), Color(1.0, 0.62, 0.2, 0.75 * fade))

func _draw_array(a: Dictionary) -> void:
	var kind := str(a.kind)
	var col: Color = ARRAY_COLOURS.get(kind, ARRAY_COLOURS.guard)
	var at := Vector2(float(a.x), float(a.y))
	var r := float(a.radius)
	var fade := clampf(float(a.t), 0.0, 1.0)
	var spin := float(Time.get_ticks_msec()) / 1000.0 * (1.4 if kind == "killing" else 0.6)
	draw_set_transform(at, 0.0, Vector2(1, 0.35))
	draw_circle(Vector2.ZERO, r, Color(col, 0.08 * fade))
	draw_arc(Vector2.ZERO, r, 0, TAU, 64, Color(col, 0.75 * fade), 3.0)
	draw_arc(Vector2.ZERO, r * 0.72, 0, TAU, 48, Color(col, 0.5 * fade), 2.0)
	for i in 8:
		var ang := spin + TAU * i / 8.0
		var p0 := Vector2(cos(ang), sin(ang)) * r * 0.76
		var p1 := Vector2(cos(ang), sin(ang)) * r * 0.94
		var side := Vector2(-sin(ang), cos(ang)) * 6.0
		draw_line(p0 + side, p1 + side, Color(col, 0.85 * fade), 2.0)
		if i % 2 == 0: draw_line(p0 - side, p1 - side, Color(col, 0.85 * fade), 2.0)
	# The heart of each array: trigram bars (guarding), four blades pointing in (killing), a chain turning (binding).
	match kind:
		"killing":
			for i in 4:
				var ang := -spin * 0.5 + TAU * i / 4.0 + PI / 4.0
				var u := Vector2(cos(ang), sin(ang))
				var w := Vector2(-u.y, u.x) * r * 0.08
				draw_colored_polygon(PackedVector2Array([u * r * 0.6 + w, u * r * 0.6 - w, u * r * 0.12]), Color(col, 0.7 * fade))
		"binding":
			for i in 12:
				var ang := -spin + TAU * i / 12.0
				draw_arc(Vector2(cos(ang), sin(ang)) * r * 0.45, r * 0.06, 0, TAU, 12, Color(col, 0.8 * fade), 2.0)
		_:
			for i in 8:
				var ang := spin * 0.5 + TAU * i / 8.0
				var u := Vector2(cos(ang), sin(ang)) * r * 0.42
				var w := Vector2(-sin(ang), cos(ang)) * r * 0.09
				draw_line(u + w, u - w, Color(col, 0.8 * fade), 3.0)
			draw_circle(Vector2.ZERO, r * 0.06, Color(UiKit.PALE_GOLD, 0.9 * fade))
	draw_set_transform(Vector2.ZERO)

## A quaver: an ink-edged oval head, a stem and a flag, drawn on the 2-pixel grid.
func _draw_note(at: Vector2, col: Color, alpha: float, sc: float) -> void:
	var head := at.snapped(Vector2(2, 2))
	draw_set_transform(head, -0.35, Vector2(1.0, 0.72) * sc)
	draw_circle(Vector2.ZERO, 6.0, Color(UiKit.INK, alpha))
	draw_circle(Vector2.ZERO, 4.2, Color(col, alpha))
	draw_set_transform(Vector2.ZERO)
	var top := head + Vector2(5, -20) * sc
	draw_line(head + Vector2(5, -2) * sc, top, Color(UiKit.INK, alpha), 3.0 * sc)
	draw_line(head + Vector2(5, -2) * sc, top, Color(col, alpha), 1.4 * sc)
	draw_line(top, top + Vector2(7, 6) * sc, Color(UiKit.INK, alpha), 3.0 * sc)
	draw_line(top, top + Vector2(7, 6) * sc, Color(col, alpha), 1.4 * sc)

static func _hash(i: int, salt: int) -> float:
	return fposmod(sin(float(i) * 12.9898 + float(salt) * 78.233) * 43758.5453, 1.0)

## A shot on the top-down plane (redesign Phase 2) flies along its `aim`: its drawing turns to it, kept upright by
## mirroring the ones that fly left.
func _draw_projectile(p: Dictionary) -> void:
	var pos := Vector2(float(p.x), float(p.y) - float(p.alt)).snapped(Vector2(2, 2))
	if not p.has("aim"):
		_draw_shot(p, pos, float(p.dir), 0.0)
		return
	var aim: Vector2 = p.aim
	var dir := 1.0 if aim.x >= 0.0 else -1.0
	var turn := (aim * dir).angle()
	draw_set_transform(pos, turn)
	_draw_shot(p, Vector2.ZERO, dir, turn, pos)
	draw_set_transform(Vector2.ZERO)

## `pos` in the current transform; `turn` and `at` (the shot's place) for a form's bolt, which sets its own.
func _draw_shot(p: Dictionary, pos: Vector2, dir: float, turn: float, at := Vector2.INF) -> void:
	# Decision 23: a technique's Qi bolt is its form's projectile loop (arc, volley, seeker, return), in its element's
	# row; the weapon arts (an arrow, a fan, a note, a needle, the released jian) stay their own drawings.
	if str(p.get("art", "")).begins_with("qi_") and p.has("technique"):
		var t := ContentDB.entry("techniques", str(p.technique))
		var a := form_spec(str(t.get("vfx", {}).get("anim", "")))
		if a.has("bolt") and not forms: return   # the top-down world draws it (TopdownFx's bolts)
		if a.has("bolt"):
			var b: Dictionary = a.bolt
			var band := band_of(int(t.get("vfx", {}).get("tier", 1)))
			draw_form(b, pos if at == Vector2.INF else at, int(float(p.get("travelled", 0.0)) / 24.0) % int(b.frames), form_row(str(p.get("element", "none")), band), int(dir),
				1.0 if band < 2 else 1.5, 1.0, -1.0, turn)
			if at != Vector2.INF: draw_set_transform(at, turn)
			return
	match str(p.get("art", "arrow")):
		"arrow":
			draw_line(pos + Vector2(-dir * 18, 0), pos + Vector2(dir * 12, 0), Color("d6b779"), 2)
			draw_colored_polygon(PackedVector2Array([pos + Vector2(dir * 18, 0), pos + Vector2(dir * 8, -4), pos + Vector2(dir * 8, 4)]), Color("d9e3cb"))
			draw_line(pos + Vector2(-dir * 18, -4), pos + Vector2(-dir * 10, 0), Color("b8cbb7"), 2)
			draw_line(pos + Vector2(-dir * 18, 4), pos + Vector2(-dir * 10, 0), Color("b8cbb7"), 2)
		"pebble", "boulder":
			var r := 6.0 if p.art == "pebble" else 12.0
			draw_circle(pos, r + 2, UiKit.INK)
			draw_circle(pos, r, Color("9a8c78"))
			draw_rect(Rect2(pos + Vector2(-r * 0.4, -r * 0.5), Vector2(4, 4)), Color("c8bca6"))
		"ice_shard":
			var tip := pos + Vector2(dir * 12, 0)
			draw_colored_polygon(PackedVector2Array([tip, pos + Vector2(0, -5), pos + Vector2(-dir * 10, 0), pos + Vector2(0, 5)]), Color("9fd8ff"))
			draw_polyline(PackedVector2Array([tip, pos + Vector2(0, -5), pos + Vector2(-dir * 10, 0), pos + Vector2(0, 5), tip]), UiKit.INK, 2)
			draw_line(pos + Vector2(-dir * 4, -1), tip, Color("e8f7ff"), 2)
			for i in 3:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 6), (i - 1) * 3)).snapped(Vector2(2, 2)), Vector2(2, 2)), Color("dff3ff"))
		"sand_crescent":
			# The Tomb King's thrown crescent of sand: a curved blade of gold grit with a dusty trail.
			var arc := PackedVector2Array()
			for i in 9:
				var a := lerpf(-1.2, 1.2, i / 8.0)
				arc.append((pos + Vector2(dir * cos(a) * 16.0, sin(a) * 22.0)).snapped(Vector2(2, 2)))
			draw_polyline(arc, UiKit.INK, 8.0)
			draw_polyline(arc, Color("d9a54a"), 5.0)
			draw_polyline(arc, Color("ffe6a1"), 2.0)
			for i in 5:
				draw_rect(Rect2((pos + Vector2(-dir * (12 + i * 8), sin(float(p.travelled) * 0.08 + i * 1.7) * 10.0)).snapped(Vector2(2, 2)), Vector2(4, 4)),
					Color("c9a06a", 0.7 - i * 0.12))
		"moon_crescent":
			# S47 the Moon Spirit's skill: a thin crescent of pale moonlight skimming forward, with a silver wake.
			draw_circle(pos, 32, Color(0.75, 0.9, 1.0, 0.16))
			var moon := PackedVector2Array()
			for i in 13:
				var a := lerpf(-1.3, 1.3, i / 12.0)
				moon.append((pos + Vector2(dir * cos(a) * 24.0, sin(a) * 36.0)).snapped(Vector2(2, 2)))
			draw_polyline(moon, UiKit.INK, 9.0)
			draw_polyline(moon, Color("9fc8f0"), 6.0)
			draw_polyline(moon, Color("f2f8ff"), 2.0)
			for i in 4:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 9), sin(float(p.travelled) * 0.07 + i * 1.9) * 12.0)).snapped(Vector2(2, 2)), Vector2(2, 2)),
					Color(0.85, 0.95, 1.0, 0.8 - i * 0.18))
		"bamboo":
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), UiKit.INK, 6)
			draw_line(pos + Vector2(-10, -4), pos + Vector2(10, 4), Color("8cc05a"), 4)
		"talisman":
			draw_rect(Rect2(pos - Vector2(6, 10), Vector2(12, 20)), Color("e8d99a"))
			draw_rect(Rect2(pos - Vector2(3, 5), Vector2(6, 8)), UiKit.RED)
		"flying_sword":
			# S47: the released jian, point first, with a pale streak behind it.
			for k in 4:
				draw_line(pos + Vector2(-dir * (20 + k * 10), 0), pos + Vector2(-dir * (28 + k * 10), 0), Color(0.8, 0.95, 1.0, 0.5 - k * 0.12), 3)
			draw_line(pos + Vector2(-dir * 16, 0), pos + Vector2(dir * 14, 0), Color("2b2f33"), 5)
			draw_line(pos + Vector2(-dir * 14, 0), pos + Vector2(dir * 14, 0), Color("dfe8ee"), 3)
			draw_colored_polygon(PackedVector2Array([pos + Vector2(dir * 14, -2), pos + Vector2(dir * 14, 2), pos + Vector2(dir * 20, 0)]), Color("f4fbff"))
			draw_line(pos + Vector2(-dir * 16, -6), pos + Vector2(-dir * 16, 6), Color("b5892f"), 3)
			draw_line(pos + Vector2(-dir * 17, 0), pos + Vector2(-dir * 24, 0), Color("5a3a22"), 3)
		"note":
			# The flute's note: a jade-lit quaver with a short trail of motes (S47 v1.1).
			draw_circle(pos, 13, Color(0.55, 0.95, 0.85, 0.22))
			for i in 3:
				draw_rect(Rect2((pos + Vector2(-dir * (14 + i * 8), sin(float(p.travelled) * 0.09 + i * 1.3) * 5.0)).snapped(Vector2(2, 2)), Vector2(4, 4)),
					Color(0.7, 1.0, 0.9, 0.6 - i * 0.18))
			_draw_note(pos + Vector2(0, sin(float(p.travelled) * 0.06) * 3.0), Color("8fe8cf"), 1.0, 1.0)
		"fan":
			# The thrown fan (S47 v1.1): an open folding fan spinning edge-over-edge, with a wind streak.
			var spin := float(p.travelled) * 0.05 * dir
			for i in 3:
				draw_line(pos + Vector2(-dir * (18 + i * 9), -6 + i * 6), pos + Vector2(-dir * (30 + i * 9), -6 + i * 6), Color(0.9, 0.96, 1.0, 0.45 - i * 0.12), 2)
			var ribs := PackedVector2Array([pos])
			for i in 9:
				var a := spin + lerpf(-1.2, 1.2, i / 8.0)
				ribs.append(pos + Vector2(cos(a), sin(a)) * 16.0)
			draw_colored_polygon(ribs, Color("e9dcc0"))
			draw_polyline(ribs + PackedVector2Array([pos]), UiKit.INK, 2.0)
			for i in 5:
				var a2 := spin + lerpf(-1.2, 1.2, i / 4.0)
				draw_line(pos, pos + Vector2(cos(a2), sin(a2)) * 15.0, Color("8a5a34"), 1.0)
			draw_arc(pos, 11.0, spin - 1.2, spin + 1.2, 8, Color("b0373a"), 2.0)
			draw_circle(pos, 3, Color("5a3a22"))
		"needle":
			draw_line(pos + Vector2(-dir * 12, 0), pos + Vector2(dir * 8, 0), UiKit.INK, 3)
			draw_line(pos + Vector2(-dir * 12, 0), pos + Vector2(dir * 8, 0), Color("e8eef0"), 1)
			draw_rect(Rect2(pos + Vector2(-dir * 14 - 1, -1), Vector2(3, 3)), UiKit.RED)
		"knife":
			var tip2 := pos + Vector2(dir * 12, 0)
			draw_colored_polygon(PackedVector2Array([tip2, pos + Vector2(0, -4), pos + Vector2(-dir * 6, 0), pos + Vector2(0, 4)]), Color("c9d2d6"))
			draw_polyline(PackedVector2Array([tip2, pos + Vector2(0, -4), pos + Vector2(-dir * 6, 0), pos + Vector2(0, 4), tip2]), UiKit.INK, 2)
			draw_line(pos + Vector2(-dir * 6, 0), pos + Vector2(-dir * 12, 0), Color("6b4a2a"), 3)
			draw_arc(pos + Vector2(-dir * 14, 0), 3, 0, TAU, 8, UiKit.RED, 2)
		"pellet":
			draw_circle(pos, 7, UiKit.INK)
			draw_circle(pos, 5, Color("2a2a30"))
			draw_rect(Rect2(pos + Vector2(-5, -1), Vector2(10, 2)), UiKit.RED)
			draw_rect(Rect2(pos + Vector2(-dir * 2, -9), Vector2(3, 3)), Color("ffd76a"))
		_:
			var col := SpriteCache.element_color(str(p.get("element", "none")))
			if str(p.art).begins_with("soul"): col = UiKit.SOUL
			draw_circle(pos, 12, Color(col, 0.35))
			draw_circle(pos, 8, Color(col, 0.8))
			draw_circle(pos, 4, Color(1, 1, 1, 0.9))
			for i in 4:
				draw_rect(Rect2((pos + Vector2(-dir * (10 + i * 7), sin(float(p.travelled) * 0.1 + i) * 4)).snapped(Vector2(2, 2)), Vector2(4, 4)), Color(col, 0.6 - i * 0.12))
