class_name SceneStage
extends Node2D
## Decision 39: what a staged scene draws over the world at the HUD's resolution, from the SceneDirector's state each
## frame: the weather it calls, the speech balloons and emotes over the people's heads (a balloon docks at the screen's
## edge, its speaker named, when the speaker is out of view), the hand-off's prompt over what to do (a bobbing chevron
## and a plate over a thing, a person, a foe or a way; a ring round a HUD control), the letterbox, the fade, a flash,
## the title card (the moments' band, mockup 05) and, in a cut, "Hold to skip" with the hold's ring. Reduce motion
## stills the rain, the bob and the pop, and the letterbox and the title fade in instead of sliding.

var director: SceneDirector
static var _box: StyleBoxFlat
const HEAD := {"npc": -88.0, "player": -88.0, "prop": -34.0}
const TEXT := 18
const MARGIN := 16.0

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	if _box == null:
		_box = StyleBoxFlat.new()
		_box.set_corner_radius_all(10)
		_box.set_border_width_all(2)
		_box.anti_aliasing = true

func _draw() -> void:
	var run = director.run
	if run == null or not (director.world is TopdownWorld): return
	var still := director.reduce_motion()
	var lb_h := float(SceneRules.cfg().get("letterbox_h", 64)) * float(run.lb)
	if run.weather != "": _weather(str(run.weather), still)
	for a in run.actors.values():
		if not a.visible: continue
		var head := _head(a)
		if a.get("say", "") != "": _balloon(head, a, still, lb_h)
		elif a.emote != "": _emote(head + Vector2(0, -22), str(a.emote), float(a.emote_t), still)
	if not run.prompt.is_empty(): _prompt(run.prompt, still)
	MomentView.letterbox(self, float(SceneRules.cfg().get("letterbox_h", 64)), float(run.lb), 1.0, still)
	if float(run.fade) > 0.0: draw_rect(Rect2(0, 0, 1280, 720), Color(UiKit.INK, clampf(float(run.fade), 0.0, 1.0)))
	if not run.flash.is_empty():
		var k := float(run.flash.t) / maxf(0.01, float(run.flash.s))
		var a := (1.0 if Game.account.settings.get("flashes", true) else 0.3) * 0.55 * (1.0 - k)
		if a > 0.0: draw_rect(Rect2(0, 0, 1280, 720), Color(run.flash.color as Color, a))
	if not run.title.is_empty() and is_instance_valid(director.moments):
		var tt := float(run.title.t)
		var out := clampf((float(run.title.s) - tt) / 0.4, 0.0, 1.0)
		director.moments.draw_title(self, str(run.title.title), str(run.title.sub), tt, out, still)
	if run.mode == "cut": _skip_hint(still)

## The top of a head on the screen (a prop's middle), where balloons and emotes hang.
func _head(a: Dictionary) -> Vector2:
	var w = director.world
	var kind := "player" if a.name == "player" else ("prop" if a.prop != "" else "npc")
	var p: Vector2 = a.pos if kind != "player" else director.player_pos()
	var z := float(w.stage_zoom) if w is TopdownWorld else 1.0
	return w.overlay.get_global_transform_with_canvas() * Vector2(p.x, p.y - float(a.alt)) + Vector2(0, HEAD[kind] * z)

## A speech balloon over the speaker: rice paper, ink words wrapped to the balloon's width, a tail to the head. Out of
## view it docks at the edge with the speaker's name on it.
func _balloon(head: Vector2, a: Dictionary, still: bool, lb_h: float) -> void:
	var lines := UiKit.wrap(str(a.say), TEXT, float(SceneRules.cfg().get("balloon_w", 380)))
	var tw := 0.0
	for ln in lines: tw = maxf(tw, UiKit.text_width(str(ln), TEXT))
	var lh := UiKit.line_height(TEXT)
	var name := _name_of(a)
	var r := Rect2(head.x - tw * 0.5 - 16.0, head.y - lh * lines.size() - 34.0, tw + 32.0, lh * lines.size() + 20.0)
	var inside := Rect2(MARGIN, lb_h + MARGIN, 1280.0 - MARGIN * 2.0, 720.0 - (lb_h + MARGIN) * 2.0)
	var off := not inside.has_point(head)
	r.position.x = clampf(r.position.x, inside.position.x, inside.end.x - r.size.x)
	r.position.y = clampf(r.position.y, inside.position.y + (22.0 if off else 0.0), inside.end.y - r.size.y)
	# Out of a cut the HUD is up: a balloon never lies over its panels (the prototype's QA: Washer Mei's thanks at the
	# top-left covered the HP bar as Old Snapper appeared). It moves aside of the panel it would cover, else below it.
	if not director.in_cut() and is_instance_valid(director.hud) and director.hud.modulate.a > 0.5:
		r = clear_of_hud(r, director.hud.obstacle_rects(), inside)
	var k := 1.0 if still else clampf(float(a.get("say_t", 1.0)) / 0.15, 0.0, 1.0)
	_box.bg_color = Color(UiKit.PAPER, 0.96 * k)
	_box.border_color = Color(UiKit.INK, k)
	if not off:
		var tip := Vector2(clampf(head.x, r.position.x + 18.0, r.end.x - 18.0), r.end.y - 1.0)
		draw_colored_polygon(PackedVector2Array([tip + Vector2(-9, 0), tip + Vector2(9, 0), head + Vector2(0, -4)]), Color(UiKit.INK, k))
		draw_colored_polygon(PackedVector2Array([tip + Vector2(-6, -1), tip + Vector2(6, -1), head + Vector2(0, -8)]), Color(UiKit.PAPER, 0.96 * k))
	draw_style_box(_box, r)
	if off or a.name == "player":
		UiKit.draw_outlined(self, name, Vector2(r.position.x + 12.0, r.position.y - 6.0), 16, Color(UiKit.PALE_GOLD, k), HORIZONTAL_ALIGNMENT_LEFT, 300)
	var y := r.position.y + 10.0 + TEXT * UiKit.text_scale()
	for ln in lines:
		UiKit.draw_text(self, str(ln), Vector2(r.position.x + 16.0, y), TEXT, Color(UiKit.PAPER_INK, k), HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)
		y += lh
	if director.in_cut():
		var bob := 0.0 if still else roundf(sin(Time.get_ticks_msec() / 160.0) * 2.0)
		UiKit.draw_text(self, "▼", Vector2(r.end.x - 20.0, r.end.y - 4.0 + bob), 12, Color(UiKit.BRONZE, k), HORIZONTAL_ALIGNMENT_LEFT, -1.0, false)

## A balloon's box moved clear of the HUD's panels and controls (`hud_rects`, screen rects), inside `inside`: aside of
## the one it covers (away from its middle), else below it; unchanged when nothing is clear.
static func clear_of_hud(r: Rect2, hud_rects: Array, inside: Rect2) -> Rect2:
	var hits := func(b: Rect2) -> bool: return hud_rects.any(func(o): return (o as Rect2).intersects(b))
	if not hits.call(r): return r
	for o in hud_rects:
		if not (o as Rect2).intersects(r): continue
		var right := (o as Rect2).get_center().x < 640.0
		var side := Rect2(Vector2((o as Rect2).end.x + 8.0 if right else (o as Rect2).position.x - 8.0 - r.size.x, r.position.y), r.size)
		if inside.encloses(side) and not hits.call(side): return side
	# Else the first clear row under a panel.
	var ys: Array = hud_rects.map(func(o): return (o as Rect2).end.y + 8.0).filter(func(y): return y > r.position.y)
	ys.sort()
	for y in ys:
		var below := Rect2(Vector2(r.position.x, y), r.size)
		if inside.encloses(below) and not hits.call(below): return below
	return r

func _name_of(a: Dictionary) -> String:
	if a.name == "player": return str(Game.active().name) if Game.active() else ""
	return ContentDB.name_of("npcs", str(a.npc)) if str(a.npc) != "" else ""

## An emote in a small round balloon over the head, popping in (still under Reduce motion).
func _emote(at: Vector2, kind: String, left: float, still: bool) -> void:
	var life := float(SceneRules.cfg().get("emote_s", 1.2))
	var k := clampf(left / 0.2, 0.0, 1.0)
	var s := 1.0 if still else lerpf(1.25, 1.0, clampf((life - left) / 0.15, 0.0, 1.0))
	draw_set_transform(at, 0.0, Vector2(s, s))
	draw_circle(Vector2.ZERO, 19.0, Color(UiKit.INK, k))
	draw_circle(Vector2.ZERO, 17.0, Color(UiKit.PAPER, k))
	draw_colored_polygon(PackedVector2Array([Vector2(-5, 15), Vector2(5, 15), Vector2(0, 24)]), Color(UiKit.PAPER, k))
	match kind:
		"!": UiKit.draw_text(self, "!", Vector2(-20, 9), 26, Color(UiKit.RED, k), HORIZONTAL_ALIGNMENT_CENTER, 40, false)
		"?": UiKit.draw_text(self, "?", Vector2(-20, 9), 24, Color(UiKit.PAPER_INK, k), HORIZONTAL_ALIGNMENT_CENTER, 40, false)
		"...":
			for i in 3: draw_circle(Vector2(-8 + i * 8, 2), 2.6, Color(UiKit.PAPER_INK, k))
		"note":
			draw_circle(Vector2(-3, 6), 4.5, Color(UiKit.JADE, k))
			draw_line(Vector2(1, 6), Vector2(1, -9), Color(UiKit.JADE, k), 2.5)
			draw_line(Vector2(1, -9), Vector2(8, -5), Color(UiKit.JADE, k), 2.5)
		"heart": UiKit._heart(self, Vector2(0, 1), 10.0, Color(UiKit.HEART, k))
		"anger":
			for q in [Vector2(-5, -5), Vector2(5, -5), Vector2(-5, 5), Vector2(5, 5)]:
				draw_arc(q * 1.1, 5.0, (q.angle() + PI) - 0.9, (q.angle() + PI) + 0.9, 8, Color(UiKit.RED, k), 2.5)
		"sweat":
			draw_circle(Vector2(0, 4), 6.0, Color(UiKit.SKY, k))
			draw_colored_polygon(PackedVector2Array([Vector2(-5.2, 1), Vector2(5.2, 1), Vector2(0, -10)]), Color(UiKit.SKY, k))
		"idea":
			draw_circle(Vector2(0, -2), 7.0, Color(UiKit.GOLD, k))
			draw_rect(Rect2(-3, 5, 6, 5), Color(UiKit.BRONZE, k))
	draw_set_transform(Vector2.ZERO)

## The hand-off's prompt: over a thing in the world, a jade chevron bobbing above it and the plate with what to do; at
## a HUD control, a ring round it pulsing and the plate above it. Off the screen, the plate docks at the edge.
## Where a hand-off's prompt plate stands across the screen: by its target, the whole plate on the screen. A long prompt
## by a control at the edge (the Bag's, top right) was cut off there (the prototype's QA, "Open your Bag: put Herbal
## Tea in Quick-…").
static func prompt_x(text: String, x: float) -> float:
	var half := UiKit.text_width(text, 18, true) * 0.5 + 16.0
	return clampf(x, half, 1280.0 - half) if half * 2.0 < 1280.0 else 640.0

func _prompt(pr: Dictionary, still: bool) -> void:
	var t := float(pr.t)
	var a := clampf(t / 0.25, 0.0, 1.0)
	var at = pr.at
	var target := Vector2.INF
	var hud_ring := false
	if not (at is Array) and str(at).begins_with("hud:"):
		var role := str(at).trim_prefix("hud:")
		if is_instance_valid(director.hud):
			for tg in director.hud.hit_targets():
				if str(tg.role) == role:
					target = tg.center
					var pulse := 1.0 if still else 1.0 + 0.12 * sin(t * 5.0)
					draw_arc(target, (float(tg.drawn) + 8.0) * pulse, 0, TAU, 40, Color(UiKit.GOLD, a), 3.0)
					hud_ring = true
					break
	else:
		var w := director.where(at)
		if w != Vector2.INF: target = director.world.overlay.get_global_transform_with_canvas() * w + Vector2(0, -64)
	var inside := Rect2(40, 90, 1200, 520)
	var plate_at := Vector2(640, 600) if target == Vector2.INF else Vector2(clampf(target.x, inside.position.x + 120, inside.end.x - 120), clampf(target.y - (56.0 if hud_ring else 26.0), inside.position.y, inside.end.y))
	if target != Vector2.INF and not hud_ring and inside.has_point(target):
		var bob := 0.0 if still else roundf(sin(t * 4.0) * 4.0)
		var c := target + Vector2(0, bob)
		draw_colored_polygon(PackedVector2Array([c + Vector2(-11, -10), c + Vector2(11, -10), c + Vector2(0, 2)]), Color(UiKit.INK, a))
		draw_colored_polygon(PackedVector2Array([c + Vector2(-8, -8), c + Vector2(8, -8), c + Vector2(0, -1)]), Color(UiKit.BRIGHT_JADE, a))
		plate_at.y = c.y - 20.0
	plate_at.x = prompt_x(str(pr.text), plate_at.x)
	draw_set_transform(plate_at)
	UiKit.draw_nameplate(self, str(pr.text), "", 0.0, Color(UiKit.PALE_GOLD, a), UiKit.MIST, 18)
	draw_set_transform(Vector2.ZERO)

## A storm's dark and its rain (still under Reduce motion: the dark alone); rain alone for "rain".
func _weather(kind: String, still: bool) -> void:
	if kind == "storm": draw_rect(Rect2(0, 0, 1280, 720), Color(UiKit.DIM, 0.3))
	if still: return
	var t := Time.get_ticks_msec() / 1000.0
	var col := Color(UiKit.MIST, 0.45)
	for i in 90:
		var x := fmod(float((i * 7919) % 1280) + t * 260.0, 1320.0) - 20.0
		var y := fmod(float((i * 104729) % 720) + t * 900.0 * (0.8 + float(i % 5) * 0.08), 760.0) - 20.0
		draw_line(Vector2(x, y), Vector2(x - 6, y + 22), col, 1.5)

## In a cut: "Hold to skip" in the corner, and while a press is held, its ring filling.
func _skip_hint(still: bool) -> void:
	var k := director.skip_k()
	var at := Vector2(1206, 690)
	UiKit.draw_outlined(self, Tx.t("scene.hold_to_skip"), at + Vector2(-230, 6), 16, Color(UiKit.MIST, 0.55 + 0.45 * k), HORIZONTAL_ALIGNMENT_RIGHT, 200)
	draw_arc(at, 14.0, 0, TAU, 28, Color(UiKit.MIST, 0.35), 2.0)
	if k > 0.0: draw_arc(at, 14.0, -PI * 0.5, -PI * 0.5 + TAU * k, 28, UiKit.PALE_GOLD, 3.0 if not still else 2.0)
