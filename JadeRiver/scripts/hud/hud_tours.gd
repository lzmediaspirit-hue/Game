class_name HudTours
extends HudPart
## The tutorial coach's anchors on the HUD (decision 43): a control or a plate by its name, so a tour never leans on how
## the HUD is laid out.
## A part of the HUD (audit 45, S6): HudPart says how a part works.

## Decision 45: hit_targets as they stand this frame, for the tutorial coach (tour_rect). The coach asks for several
## anchors a frame, and each asking afresh counted the points badges again (the Realisations' walks the technique trees):
## half a millisecond a frame on a desktop while a HUD lesson showed. Asked again on a new frame, when the game moves on
## (Game.revision) or the fan opens or shuts.
func tour_targets() -> Array:
	return hud._tour_targets.value([hud.fan_open, hud.fight, hud.skill_page], func(): return hud.layout.hit_targets(hud.layout.frame_badges()))

## Decision 43 (docs/redesign/tutorials.md): a tutorial's anchor on the HUD, by name, so a tour never leans on how the HUD
## is laid out: a round control by its role in hit_targets ("attack", "jump", "skill" for all the technique buttons,
## "icon:menu", "points:meridian", …) or a plate ("minimap", "portrait", "tracker", "progress", "log", and the panel's
## "qi" and "soul" bars with their labels). Rect2() while it is not shown. Decision 44: a Treasure button ("treasure:0",
## "treasure:1") comes out only in a fight; at rest, once revealed, its anchor is where it comes out then (ring 2).
func tour_rect(name: String) -> Rect2:
	var c = Game.active()
	match name:
		"minimap": return hud.minimap_rect if hud.shown("minimap") else Rect2()
		"portrait": return hud.layout.panel_rect(c) if hud.shown("player_panel") else Rect2()
		"tracker": return hud.tracker_rect if hud.shown("quest_tracker") else Rect2()
		"progress": return Rect2(0, 704, 1280, 16) if hud.shown("progress_bar") else Rect2()
		"log": return hud.layout.log_rect()
		"qi", "soul":
			# The bars' rows as _draw_player_panel lays them: HP, then QI once there is a pool, then SL.
			if c == null or not hud.shown("player_panel"): return Rect2()
			var qi: bool = c.pools.max_qi > 0.0 and hud.shown("qi_bar")
			var at := hud.layout.panel_rect(c).position + Vector2(18, 78.0 if hud.shown("hp_bar") else 60.0)
			if name == "qi": return Rect2(at, Vector2(330, 14)) if qi else Rect2()
			return Rect2(at + Vector2(0, 18.0 if qi else 0.0), Vector2(330, 14)) if c.pools.max_soul > 0.0 and hud.shown("soul_bar") else Rect2()
	var out := Rect2()
	for tg in tour_targets():
		# Decision 45: "quick" is the quick slots that show ("quick:0" to "quick:2" each on its own).
		if str(tg.role) != name and not (name == "quick" and str(tg.role).begins_with("quick:")): continue
		var d := float(tg.drawn) + 2.0
		var r := Rect2(tg.center - Vector2(d, d), Vector2(d, d) * 2.0)
		out = r if out.size == Vector2.ZERO else out.merge(r)
	if out.size == Vector2.ZERO and name in ["treasure:0", "treasure:1"] and not hud.fight and hud.shown("treasure_%d" % (int(name.right(1)) + 1)):
		var at := hud.layout.on_ring(hud.attack_center, Hud.RING2_R, float(Hud.RING2_HOME["treasure:0"]) + 22.0 * int(name.right(1)))
		return Rect2(at - Vector2(28, 28), Vector2(56, 56))
	return out
