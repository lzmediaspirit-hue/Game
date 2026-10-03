class_name HudPart
extends RefCounted
## Base of the HUD's parts (audit 45, S6; docs/architecture/hud.md). A part holds one section of the HUD's work and no
## state of its own. The HUD (hud.gd) makes one of each part, keeps every field and forwards its public methods to
## them, so every caller still calls hud.<method>. In a part:
##   - the HUD's fields, its signals and the canvas it draws on are reached through `hud` (hud.touches, hud.open_page,
##     hud.draw_rect), and its constants through its class (Hud.RING2_R);
##   - a function another part keeps is called on that part (hud.layout.ring2(c)), and one the HUD keeps on the HUD
##     (hud.shown("bag"), hud.add_log(...));
##   - a part draws only while the HUD draws: the HUD's _draw calls the parts in its order, on its own canvas.
## The reference is a plain one. The HUD is a Node and not ref-counted, so the two cannot keep each other alive, and the
## parts go with the HUD.

var hud: Hud

func _init(h: Hud) -> void:
	hud = h
