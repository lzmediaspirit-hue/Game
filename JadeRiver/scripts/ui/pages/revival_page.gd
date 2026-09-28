extends Page
## Gravely wounded (S31, Part 9.11 · Revival): return to the last shrine, or revive
## here when allowed (talisman or the Prologue's free recovery).
## P5 (docs/page_identity.md row 39, the way family): the life lamp at the shrine, burning low. One bronze lamp in a dark
## stone niche; what the fall takes stands in the shadow at its left, what you keep in its light at its right; the
## choices under the lamp. The flame steadies from a gutter as the page opens (none under Reduce motion). The early grace
## (P12) is told here: in full on the first fall before Bone Forging 5, then in a line.

const NICHE := Rect2(568, 180, 144, 200)
const LAMP := Vector2(640, 344)   # the lamp's bowl
const LOST := Rect2(292, 188, 256, 196)
const KEPT := Rect2(732, 188, 256, 196)
const CHOICES_X := 424.0
const CHOICES_W := 432.0
const GUTTER_S := 0.6   # the flame gutters, then steadies (decoration: none under Reduce motion)
## The shrine's wall, and the lightest its stones come to (in the lamp's light at the right).
var wall := UiKit.SURFACE.niche.lerp(UiKit.SURFACE.stone, 0.35)
var wall_light := wall.lerp(UiKit.PAPER, 0.08)

func _init() -> void:
	title = Tx.t("ui.revival.gravely_wounded")
	modal = true
	frame_rect = WINDOW_MEDIUM
	identity = Identity.new("niche", false, "own", "lamp_in_dark_niche", 0.3)

func content_rect() -> Rect2:
	return Rect2(frame_rect.position.x + 24, frame_rect.position.y + 80, frame_rect.size.x - 48, frame_rect.size.y - 96)

## The wall of the shrine in the lamp's shadow, the niche cut into it, and the light the lamp throws on the stone.
func draw_surface(r: Rect2) -> void:
	WayKit.stone(self, r, wall, 40.0, 96.0)
	draw_rect(r, Color(UiKit.BLOOD, 0.06))
	ground(r, wall_light)
	# The light falls to the right of the lamp; the left stays in shadow.
	glow(Rect2(LAMP.x - 300, LAMP.y - 260, 600, 440), Color(UiKit.SURFACE.glow, 0.10 * _halo()))
	hshade(Rect2(r.position.x, r.position.y, 360, r.size.y), Color(UiKit.INK, 0.55), Color(UiKit.INK, 0.0))
	draw_rect(r, Color(UiKit.BRONZE, 0.5), false, 1.0)
	# The niche: a round-topped recess, its lip catching the light.
	var n := NICHE
	var arch := PackedVector2Array()
	for i in 17: arch.append(Vector2(n.get_center().x, n.position.y + n.size.x * 0.5) + Vector2.from_angle(PI + PI * float(i) / 16.0) * n.size.x * 0.5)
	arch.append(n.end)
	arch.append(Vector2(n.position.x, n.end.y))
	var lip := PackedVector2Array(Array(arch).map(func(p): return n.get_center() + (p - n.get_center()) * 1.08))
	draw_colored_polygon(lip, UiKit.SURFACE.stone.lerp(UiKit.SURFACE.glow, 0.12))
	draw_colored_polygon(arch, UiKit.INK)
	glow(Rect2(LAMP.x - 90, LAMP.y - 150, 180, 200), Color(UiKit.SURFACE.ember, 0.35 * _halo()))

func title_rect() -> Rect2:
	return Rect2(frame_rect.get_center().x - 200, frame_rect.position.y + 14, 400, 52)

## The title's lintel: a dark stone tablet over the niche.
func draw_title_mount(r: Rect2) -> void:
	WayKit.tablet(self, r, false)

## What the fall costs, as this character stands: nothing in the Prologue, the early grace before Bone Forging 5 (in full
## the first time), half as much once the soul can flee (from Sage), else a tenth of the stage.
func loss_text(ch) -> String:
	var prologue: bool = not Unlocks.is_unlocked(ch.id, "kill_progress")
	var out := Tx.t("ui.revival.no_penalty_in_the_prologue") if prologue else Tx.t("ui.revival.you_lose_10_of_this")
	# The early grace (P12): told in full on the first fall, then in a line.
	if not prologue and ProgressionRules.death_grace(ch.cultivator.realm_key):
		out = Tx.t("ui.revival.early_grace_short" if ch.quests.has_flag("death_grace_told") else "ui.revival.early_grace")
	# S48 nascent-soul escape: from Sage the soul flees to the shrine and half as much is lost.
	if not prologue and ProgressionRules.at_least(ch.cultivator.realm_key, str(ContentDB.stat_const("soul_escape", {}).get("from", "sage_1"))):
		out = Tx.t("ui.revival.soul_escape")
	return out

## Whether this fall costs nothing (the Prologue, or the early grace).
func free_fall(ch) -> bool:
	return not Unlocks.is_unlocked(ch.id, "kill_progress") or ProgressionRules.death_grace(ch.cultivator.realm_key)

func draw_page() -> void:
	var ch = c()
	if ch == null: return
	text(Vector2(frame_rect.position.x, frame_rect.position.y + 100), Tx.t("ui.revival.your_vision_greys").strip_edges(), 18, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, frame_rect.size.x)
	_lamp()
	var free := free_fall(ch)
	# In the shadow: what the fall takes.
	text(Vector2(LOST.position.x, LOST.position.y + 18), Tx.t("ui.revival.lost"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_RIGHT, LOST.size.x)
	para(Rect2(LOST.position.x, LOST.position.y + 30, LOST.size.x, LOST.size.y - 30), loss_text(ch), 20, UiKit.PALE_GOLD if free else UiKit.RED_TEXT, 7)
	# In the light: what stays with you.
	ground(KEPT, wall_light.lerp(UiKit.SURFACE.glow, 0.1))
	text(Vector2(KEPT.position.x, KEPT.position.y + 18), Tx.t("ui.revival.kept"), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_LEFT, KEPT.size.x)
	var y := KEPT.position.y + 30
	for key in (["ui.revival.kept_progress"] if free else []) + ["ui.revival.kept_realm", "ui.revival.kept_gear"]:
		y += para(Rect2(KEPT.position.x, y, KEPT.size.x, 60), Tx.t(key), 20, UiKit.BRIGHT_JADE, 2) + 8
	# The choices under the lamp.
	y = NICHE.end.y + 28
	var shrine := str(ch.last_shrine.get("room", ""))
	var where := ContentDB.name_of("rooms", shrine) if shrine != "" else ContentDB.name_of("rooms", str(ch.last_town if ch.last_town != "" else "lf_village"))
	btn(Rect2(CHOICES_X, y, CHOICES_W, 62), Tx.t("ui.revival.return_to") % where, "choose", "shrine", true)
	var here: Dictionary = Game.combat.revive_here_allowed(ch)
	btn(Rect2(CHOICES_X, y + 72, CHOICES_W, 58), str(here.get("label", Tx.t("ui.revival.revive_here"))), "choose", "here", false,
		bool(here.get("ok", false)), str(here.get("text", "")))
	var note_y := y + 140
	if not bool(here.get("ok", false)) and str(here.get("text", "")) != "":
		text(Vector2(CHOICES_X, note_y + 16), str(here.text), 16, UiKit.MIST, HORIZONTAL_ALIGNMENT_CENTER, CHOICES_W)
		note_y += 26
	# A natural treasure: an Evergreen Heart fruit lifts you here, whole.
	var fruits: int = ch.inventory.count("evergreen_heart_fruit")
	if fruits > 0:
		var fruit: Dictionary = Game.combat.fruit_revival_allowed(ch)
		btn(Rect2(CHOICES_X, note_y, CHOICES_W, 58), Tx.t("ui.revival.eat_an_evergreen_heart_fruit") % fruits, "choose", "fruit", false,
			bool(fruit.get("ok", false)), str(fruit.get("text", "")))

## The bronze lamp on its foot in the niche, its flame burning low: it gutters as the page opens, then steadies.
func _lamp() -> void:
	var p := LAMP
	# The foot and stem.
	draw_colored_polygon(PackedVector2Array([p + Vector2(-26, 34), p + Vector2(26, 34), p + Vector2(14, 26), p + Vector2(6, 8), p + Vector2(-6, 8), p + Vector2(-14, 26)]), UiKit.INK)
	draw_colored_polygon(PackedVector2Array([p + Vector2(-23, 32), p + Vector2(23, 32), p + Vector2(12, 25), p + Vector2(4, 9), p + Vector2(-4, 9), p + Vector2(-12, 25)]), UiKit.BRONZE.lerp(UiKit.INK, 0.25))
	# The bowl, lit on its rim.
	draw_set_transform(p, 0.0, Vector2(1.0, 0.45))
	draw_circle(Vector2.ZERO, 34.0, UiKit.INK, true, -1.0, true)
	draw_circle(Vector2.ZERO, 31.0, UiKit.BRONZE, true, -1.0, true)
	draw_circle(Vector2(0, -4), 26.0, UiKit.BRONZE.lerp(UiKit.INK, 0.45), true, -1.0, true)
	draw_arc(Vector2.ZERO, 31.0, PI * 1.1, PI * 1.9, 24, UiKit.GOLD, 2.0, true)
	draw_set_transform(Vector2.ZERO)
	# The flame: a gutter that settles over GUTTER_S, then a slow breath; steady under Reduce motion or battery saver.
	var still := UiKit.reduce_motion() or bool(Game.account.settings.get("battery_saver", false))
	var settle := 1.0 if still else clampf(opened / GUTTER_S, 0.0, 1.0)
	var sway := 0.0 if still else (1.0 - settle) * sin(t * 23.0) * 0.8 + 0.12 * sin(t * 2.3)
	var h := 30.0 + 8.0 * settle + (0.0 if still else 1.5 * sin(t * 3.1))
	glow(Rect2(p.x - 40, p.y - 12 - h - 30, 80, h + 70), Color(UiKit.SURFACE.flame, 0.45 * _halo()))
	WayKit.flame(self, p + Vector2(0, -8), h, sway)

func on_action(id: String, data) -> void:
	if id == "choose":
		var r := submit({"type": "choose_revival", "where": str(data)})
		if r.get("ok", false): closed.emit(self)

func close() -> void:
	# Revival must be chosen; the close button returns to the shrine.
	on_action("choose", "shrine")
