extends "res://tools/dev/hud_capture.gd"
## Decision 42 ("I want the skills icon to look like the attached image"; "there are places we still use the old sprite
## character"): the technique pictures and the leftovers, before and after, into docs/redesign/feedback/pictures/
## <tag>_*.png. hud_capture's stage (a top-down character past the Weapon Hall, a jian in hand, four arts slotted: one
## cooling in the fight, one short of Qi, one ready and a spear art the jian cannot use), with a companion beside it for
## the party chip: the HUD at rest and in a fight, the Techniques page on the Water tree and on the Fire tree (the
## loadout bar cropped at x2 from the first), and the Jade Transfer Array asking where to at the sect's gate.
##   xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/picture_capture.tscn \
##     -- --tag=<before|after>
## `--dir=<folder under docs/redesign/feedback/>` shoots into that folder instead, on saves of its own (decision 43's
## people drawn bigger: `--dir=people_scale`); `--pages` adds the pages that show the character (the Character page, the
## Bag, the Cultivation page, Old Ma's shop and a talk's portrait strip).

const PICTURES := "res://docs/redesign/feedback/pictures/"
const PIC_SAVES := "user://picture_capture_saves/"
var pics := PICTURES
var pic_saves := PIC_SAVES

func _main() -> void:
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--tag="): tag = str(a).trim_prefix("--tag=")
		if str(a).begins_with("--dir="):
			pics = "res://docs/redesign/feedback/%s/" % str(a).trim_prefix("--dir=")
			pic_saves = "user://picture_capture_%s_saves/" % str(a).trim_prefix("--dir=")
	DirAccess.make_dir_recursive_absolute(pic_saves)
	for f in DirAccess.get_files_at(pic_saves): DirAccess.remove_absolute(pic_saves + f)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(pics))
	TopdownLight.debug_hour = 0.375
	main = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	await get_tree().process_frame
	Saves.use_folder(pic_saves)
	Game.boot()
	Game.autosave_enabled = false
	await _topdown_game(pics)
	await frames(30)
	await _no_scenes()
	_weapon_hall_stage()
	Game.companions.apply_add(Game.active_id, "lan_yue")
	Game.world.load_room(Game.active(), "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	await frames(20)
	await _no_scenes()
	await _pic_rest()
	await _pic_fight()
	await _pic_tree("water", true)
	await _pic_tree("fire", false)
	await _pic_travel()
	if "--pages" in OS.get_cmdline_user_args(): await _pic_pages()
	print("picture_capture: %s done" % tag)
	get_tree().quit()

## At rest beside Lu at the docks: the techniques on ring 1 and the companion's chip.
func _pic_rest() -> void:
	await _beside("npc_lu_boatman")
	main.hud.fight_override = false
	await frames(90)
	_clear_notices()
	await frames(4)
	await shot("%s_hud_rest" % tag, pics)

## In a fight on the square: Flowing Palm cooling, Cloudpiercing Stroke short of Qi, Jade Thrust closed (a spear art).
func _pic_fight() -> void:
	var c = Game.active()
	main.hud.fight_override = true
	await arena(w.player.motor.pos + Vector2(0, 40), [["wild_boarlet", Vector2(150, -30)], ["wild_boarlet", Vector2(190, 60)]])
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	c.pools.qi = maxf(0.0, Game.combat.technique_cost(c, ContentDB.entry("techniques", "cloudpiercing_stroke")) - 4.0)
	await frames(30)
	_clear_notices()
	c.pools.cooldowns["tech:flowing_palm"] = 2.4
	await frames(2)
	await shot("%s_hud_fight" % tag, pics)
	Game.room_rt.enemies.clear()
	c.pools.cooldowns.erase("tech:flowing_palm")
	c.pools.qi = c.pools.max_qi
	main.hud.fight_override = null

## The Techniques page on `tree`'s tab, Flowing Palm chosen on the Water tree (its reading's picture); with `bar`, its
## loadout bar cropped at x2 too.
func _pic_tree(tree: String, bar: bool) -> void:
	main.open_page("techniques", {"tab": tree})
	await frames(20)
	var pg = main.top_page()
	if tree == "water" and pg != null: pg.on_action("node", "flowing_palm")
	await frames(240)
	await RenderingServer.frame_post_draw
	var img := get_tree().root.get_texture().get_image()
	img.save_png(pics + "%s_tree_%s.png" % [tag, tree])
	if bar:
		var strip_img := img.get_region(Rect2i(0, 648, 660, 72))
		strip_img.resize(1320, 144, Image.INTERPOLATE_NEAREST)
		strip_img.save_png(pics + "%s_loadout_bar.png" % tag)
	main.close_all_pages()
	await frames(10)

## The Jade sect's gate: the array keyed with the watch post's and the mentor's peak's, tapped, and where it asks to go.
func _pic_travel() -> void:
	var c = Game.active()
	c.training_sect = {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}
	Unlocks.force_unlock(c.id, "transfer_array")
	for n in ["array_ja_gate", "array_marsh", "array_ja_peak"]: Game.quest.apply_flag(c.id, "array_" + n)
	Game.world.load_room(c, "ja_gate_street", "", Vector2.ZERO)
	GameEvents.flush()
	await frames(20)
	await _no_scenes()
	await at_spot(Vector2(8, 22), 60)
	_clear_notices()
	var r := Game.submit({"type": "interact", "object": "array_ja_gate"})
	if r.has("open_page"):
		var pa := {"object": "array_ja_gate"}
		pa.merge(r.get("page_args", {}), true)
		main.open_page(str(r.open_page), pa)
	elif r.has("dialogue"):
		main.open_page("dialogue", {"convo": r.dialogue})
	else:
		print("picture_capture: the array did not ask (%s)" % str(r))
	await frames(120)
	await shot("%s_travel_picker" % tag, pics)
	main.close_all_pages()
	await frames(10)

## Decision 43: the pages that show the character, each once it has drawn (their dolls' sheets load on threads).
func _pic_pages() -> void:
	for pg in [["character", {}], ["inventory", {}], ["cultivation", {}], ["shop", {"shop": "old_ma", "npc": "old_ma"}]]:
		main.open_page(str(pg[0]), pg[1])
		await frames(120)
		await shot("%s_page_%s" % [tag, pg[0]], pics)
		main.close_all_pages()
		await frames(10)
	Game.world.load_room(Game.active(), "lf_village", "", Vector2.ZERO)
	GameEvents.flush()
	await frames(20)
	await _no_scenes()
	await _beside("npc_aunt_ping_lane")
	_clear_notices()
	var r := Game.submit({"type": "interact", "object": "npc_aunt_ping_lane"})
	if r.has("dialogue"):
		main.open_page("dialogue", {"convo": r.dialogue})
		await frames(20)
		var dp = main.top_page()
		dp.line = maxi(0, dp.lines().size() - 1)
		dp.shown_chars = 9999.0
		await frames(60)
		await shot("%s_page_dialogue" % tag, pics)
		main.close_all_pages()
		await frames(10)
