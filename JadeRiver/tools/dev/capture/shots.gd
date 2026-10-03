extends RefCounted
## The capture registry (tools/dev/README.md, "Captures"): every set of review pictures the game takes of itself, as
## rows. A set is what one run takes (`capture.tscn -- <set>`): where its pictures go (`out`, under docs/), the steps
## that make its game (`stage`) and its rows, run in order. A row is one picture (or a few) and what leads to it:
##   name   the picture's name ("{tag}", or any --key=value of the command line, is filled in); a row with no name
##          takes no picture (it only moves the game on)
##   if     run the row only when: "detail" (the flag --detail was given), "tag=after", "sect=jade", "phone" (a window
##          wider than 1280), "!phone"
##   hour   the clock pinned at this hour of the day (0.375 midday, 0.68 dusk, 0.87 night) and the light with it
##   room   the room entered (through the World authority, at the row's cell); cell: where the body stands (facing the
##          camera, the camera settled on it) and wait: the frames it stands there (the set's `wait`, else 120)
##   foes   [[def, offset in cells]] set round the cell; turned: set on the player; fight: frames of the fight played
##          with the body kept whole (or [frames, false]: not kept); without `fight`, 20 frames
##   do     steps before the picture (capture_steps.gd, capture_scripted.gd: [name, args...])
##   take   the steps that take it (the set's `take`, else [["shot"]]: the whole window, HUD and all); a take's first
##          argument is its picture's name, "*" the row's
##   then   steps after it
## Every set pins the clock's light at midday unless a row names its hour, and plays on saves of its own
## (user://capture_<set>/, never the player's nor the Max Tester's).

const BASE := Vector2(22.5, 19.0) * 32.0   ## the prototype square's open middle (world units)
const SPOT := Vector2(51, 17)              ## the Reed Shallows' flats, where the foes are lined up (cells)
## E1's views: [picture, room, cell, whole room after it].
const E1_VIEWS := [
	["01_caravan_road_turnoff", "cr_caravan_road", Vector2(56, 13), true], ["02_caravan_road_west", "cr_caravan_road", Vector2(16, 14), false],
	["03_bend_shore_bay", "dw_bend_shore", Vector2(21, 15), true], ["04_bend_shore_steps", "dw_bend_shore", Vector2(48, 17), false],
	["05_stockade_yard", "mh_stockade", Vector2(26, 13), true], ["06_tunnels_cavern", "mh_tunnels", Vector2(28, 13), true],
	["07_loot_cave_hoard", "mh_loot_cave", Vector2(40, 14), true], ["08_boss_den", "mh_boss_den", Vector2(10, 13), true],
	# R3: the sects' insides, Stoneford's hall, tower and grove, the quarry (pictures under r3/)
	["r3/09_alchemy_hall", "ja_alchemy_hall", Vector2(12.5, 11), true], ["r3/10_library", "ja_library", Vector2(14, 9), true],
	["r3/11_retreat", "ja_retreat", Vector2(13, 9), true], ["r3/12_cave_abode", "ja_cave_abode", Vector2(20, 12), true],
	["r3/13_cloud_library", "cm_cloud_library", Vector2(13, 9), true], ["r3/14_cloud_retreat", "cm_retreat", Vector2(14, 9), true],
	["r3/15_cloud_herb_terraces", "cm_herb_terraces", Vector2(20, 18), true], ["r3/16_cloud_terraces_upper", "cm_herb_terraces", Vector2(34, 11), false],
	["r3/17_cloud_cave_abode", "cm_cave_abode", Vector2(19, 12), true], ["r3/18_county_hall", "sf_county_hall", Vector2(11.5, 9), true],
	["r3/19_trial_tower", "sf_trial_tower", Vector2(20, 14), true], ["r3/20_beast_grove", "sf_beast_grove", Vector2(20, 16), true],
	["r3/21_quarry_rim", "sq_quarry_rim", Vector2(14, 18), true], ["r3/22_quarry_scaffold", "sq_quarry_rim", Vector2(34, 12), false],
	["r3/23_lower_pit", "sq_lower_pit", Vector2(26, 18), true], ["r3/24_pit_tunnel_mouth", "sq_lower_pit", Vector2(50, 14), false],
	["r3/25_collapsed_tunnel", "sq_collapsed_tunnel", Vector2(20, 12), true],
	# R1: the main story's path past chapter 3 (pictures under r1/).
	["r1/01_grey_pools_jetty", "rm_grey_pools", Vector2(22, 15), true], ["r1/02_grey_pools_hamlet_way", "rm_grey_pools", Vector2(34, 12), false],
	["r1/03_sunken_causeway", "rm_sunken_causeway", Vector2(30, 14), true], ["r1/04_hermit_stilt_house", "rm_hermit_stilt_house", Vector2(8, 12), true],
	["r1/05_hamlet_square", "gh_hamlet_square", Vector2(27, 14), true], ["r1/06_whispering_bamboo", "bg_whispering_bamboo", Vector2(26, 14), true],
	["r1/07_thicket_heart", "bg_thicket_heart", Vector2(30, 14), true], ["r1/08_falls_pool", "cf_falls_pool", Vector2(24, 12), true],
	["r1/09_behind_falls", "cf_behind_falls", Vector2(20, 16), true], ["r1/10_pilgrim_stairs_foot", "cp_pilgrim_stairs", Vector2(28, 26), true],
	["r1/11_pilgrim_stairs_landing", "cp_pilgrim_stairs", Vector2(36, 18), false], ["r1/12_cleansing_summit", "cp_cleansing_summit", Vector2(17, 15), true],
	# R2: the Serpent's Shallows, the Drowned Shrine and Whitewater Gorge (their pictures under r2/)
	["r2/01_flooded_gate_court", "ds_flooded_gate", Vector2(14, 10), true], ["r2/02_hall_of_lanterns", "ds_hall_of_lanterns", Vector2(28, 12), true],
	["r2/03_scripture_well", "ds_scripture_well", Vector2(28, 16), true], ["r2/04_abbots_sanctum", "ds_abbots_sanctum", Vector2(36, 13), true],
	["r2/05_drowned_grotto", "ds_drowned_grotto", Vector2(20, 11), true], ["r2/06_serpents_shallows", "dw_serpents_shallows", Vector2(31, 10), true],
	["r2/07_gorge_mouth_bridge", "wg_gorge_mouth", Vector2(24, 11), true], ["r2/08_rapids_terraces_falls", "wg_rapids_terraces", Vector2(36, 13), true],
	["r2/09_echo_cliffs", "wg_echo_cliffs", Vector2(30, 13), true], ["r2/10_waterfall_cave", "wg_waterfall_cave", Vector2(18, 10), true],
	# R4: the peaks (a view named "r4/..." keeps its world picture and its room's whole one under r4/ too).
	["r4/01_cliff_faces_crags", "cc_cliff_faces", Vector2(46, 12), true], ["r4/02_cliff_faces_brink", "cc_cliff_faces", Vector2(28, 24), false],
	["r4/03_sky_ledges_climb", "cc_sky_ledges", Vector2(36, 15), true], ["r4/04_sky_ledges_summit", "cc_sky_ledges", Vector2(50, 7), false],
	["r4/05_misty_slopes_mere", "mp_misty_slopes", Vector2(34, 20), true], ["r4/06_misty_slopes_knoll", "mp_misty_slopes", Vector2(22, 12), false],
	["r4/07_monastery_hall", "mp_forgotten_monastery", Vector2(36, 11), true], ["r4/08_monastery_garden", "mp_forgotten_monastery", Vector2(50, 21), false],
	["r4/09_ascension_gate", "mp_ascension_gate", Vector2(36, 14), true], ["r4/10_windswept_ridge", "sr_windswept_ridge", Vector2(28, 16), true],
	["r4/11_frozen_shrine_court", "sr_frozen_shrine", Vector2(26, 11), true], ["r4/12_vale_gate", "hv_vale_gate", Vector2(20, 13), true],
	["r4/13_sect_grounds", "hv_sect_grounds", Vector2(28, 19), true], ["r4/14_back_mountain_spring", "hv_back_mountain", Vector2(26, 20), true],
	["r4/15_hidden_grotto", "hg_hidden_grotto", Vector2(20, 12), true],
	# R5: the story's own rooms and the Tidebreak Front (their pictures under r5/)
	["r5/01_gus_warehouse", "si_gus_warehouse", Vector2(22, 12), true], ["r5/02_warehouse_strongroom", "si_gus_warehouse", Vector2(36, 8), false],
	["r5/03_trial_of_reflections", "si_trial_of_reflections", Vector2(18, 12), true], ["r5/04_presence_trial", "si_presence_trial", Vector2(20, 13), true],
	["r5/05_siege_gate", "si_siege", Vector2(20, 15), true], ["r5/06_siege_field", "si_siege", Vector2(40, 7), false],
	["r5/07_sect_war_gate", "si_sect_war", Vector2(14, 15), true], ["r5/08_sect_war_junk", "si_sect_war", Vector2(46, 14), false],
	["r5/09_tidebreak_bastion", "tf_tidebreak_bastion", Vector2(22, 12), true], ["r5/10_tide_battle", "si_tide_battle", Vector2(30, 12), true],
	["r5/11_greyfall_breach", "tf_greyfall_breach", Vector2(28, 14), true], ["r5/12_hollow_wake", "tf_hollow_wake", Vector2(26, 13), true],
	["r5/13_drone_hive", "tf_drone_hive", Vector2(32, 13), true],
	# R7: Act II's chapters 13 and 14, Nine Peaks to the Tomb of Sunscar (their pictures under r7/).
	["r7/01_alliance_gate_dock", "np_alliance_gate", Vector2(12, 22), true], ["r7/02_alliance_gate_lions", "np_alliance_gate", Vector2(30, 14), false],
	["r7/03_hall_of_nine", "np_hall_of_nine", Vector2(30, 12), true], ["r7/04_auction_pavilion", "np_auction_pavilion", Vector2(11.5, 8), true],
	["r7/05_presence_terrace", "np_presence_terrace", Vector2(26, 15), true], ["r7/06_trial_hall", "np_trial_hall", Vector2(13.5, 9), true],
	["r7/07_canyon_mouth_toll", "gc_canyon_mouth", Vector2(14, 13), true], ["r7/08_canyon_mouth_mesa", "gc_canyon_mouth", Vector2(34, 12), false],
	["r7/09_kite_winds", "gc_kite_winds", Vector2(30, 14), true], ["r7/10_harpy_roosts", "gc_harpy_roosts", Vector2(32, 12), true],
	["r7/11_windbridge", "gc_windbridge", Vector2(36, 13), true],
	["r7/12_hold_gate", "ir_hold_gate", Vector2(30, 15), true], ["r7/13_clan_hearth", "ir_clan_hearth", Vector2(28, 11), true],
	["r7/14_ancestor_hall", "ir_ancestor_hall", Vector2(11.5, 8), true],
	["r7/15_glass_dunes", "sd_glass_dunes", Vector2(30, 15), true], ["r7/16_scorpion_flats", "sd_scorpion_flats", Vector2(30, 12), true],
	["r7/17_oasis_of_bones", "sd_oasis_of_bones", Vector2(28, 15), true], ["r7/18_worm_sea_tomb_door", "sd_worm_sea", Vector2(58, 13), true],
	["r7/19_sealed_gate", "ts_sealed_gate", Vector2(40, 12), true], ["r7/20_hall_of_sand_kings", "ts_hall_of_sand_kings", Vector2(30, 13), true],
	["r7/21_mirror_crypt", "ts_mirror_crypt", Vector2(28, 13), true], ["r7/22_throne_of_the_tomb_king", "ts_throne", Vector2(28, 12), true],
	# R9: the star field's end, the Starsea's crossings to the Lantern Heart (their pictures under r9/).
	["r9/01_starsea_crossing", "ss_starsea_crossing", Vector2(30, 12), true], ["r9/02_lantern_crossing", "ss_lantern_crossing", Vector2(30, 12), true],
	["r9/03_citadel_gate_court", "wc_citadel_gate", Vector2(34, 13), true], ["r9/04_citadel_gate_piers", "wc_citadel_gate", Vector2(30, 20), false],
	["r9/05_wardens_hall", "wc_wardens_hall", Vector2(13.5, 11), true], ["r9/06_observatory", "wc_observatory", Vector2(13.5, 11), true],
	["r9/07_presence_court", "wc_presence_court", Vector2(27, 17), true],
]

static func sets() -> Dictionary:
	var hud_stage := [["new_game"], ["frames", 30], ["no_scenes"], ["weapon_hall"], ["load", "lf_village", Vector2.ZERO], ["frames", 20], ["no_scenes"]]
	var hud_rest := [["beside", "npc_lu_boatman"], ["hud", "fight_override", false], ["frames", 90], ["clear_notices"], ["frames", 4]]
	var two_boarlets := [["wild_boarlet", Vector2(150, -30)], ["wild_boarlet", Vector2(190, 60)]]
	var hud_fight := [["hud", "fight_override", true], ["arena", ["here", Vector2(0, 40)], two_boarlets], ["cooldown", "tech:flowing_palm", 2.4],
		["qi_short", "cloudpiercing_stroke", 4.0], ["frames", 30], ["clear_notices"], ["cooldown", "tech:flowing_palm", 2.4], ["frames", 2]]
	var hud_fight_end := [["clear_enemies"], ["cooldown_off", "tech:flowing_palm"], ["qi_full"], ["hud", "fight_override", null]]
	var loadout_bar := ["region", "{tag}_loadout_bar", Rect2(0, 648, 660, 72), 2, true]
	var night_stage := [["new_game"], ["frames", 240],
		["quests_done", ["morning_tide", "a_quiet_river", "the_runaway_kite", "mas_delivery", "grannys_remedy", "fists_first", "crab_trouble"]],
		["unlocks_evaluate"], ["gear", "weapon", "training_short_blade", 910], ["gear", "hat", "plain_straw_hat", 911], ["give", "herbal_tea", 3],
		["refresh"], ["rewards", "evening_on_the_river"], ["flush"], ["frames", 20], ["bind"]]
	var terrain_views := [
		{"name": "01_village_square", "room": "lf_village", "cell": Vector2(33, 21)}, {"name": "02_jade_gate_street", "room": "ja_gate_street", "cell": Vector2(24, 15)},
		{"name": "03_marsh_edge", "room": "rm_marsh_edge", "cell": Vector2(30, 14)}, {"name": "04_reed_shallows", "room": "lf_reed_shallows", "cell": Vector2(40, 15)},
		{"name": "05_fishers_hut_lane", "room": "lf_village", "cell": Vector2(12, 18)}, {"name": "08_cliff_stair", "room": "cm_cliff_stair", "cell": Vector2(40, 10)},
		{"name": "09_elder_sung_peak", "room": "cm_elder_sung_peak", "cell": Vector2(20, 10)}]
	var foliage_views := [
		{"name": "10_willow_path_east", "room": "wp_east", "cell": Vector2(40, 12)}, {"name": "11_herb_terraces", "room": "ja_herb_terraces", "cell": Vector2(20, 20)},
		{"name": "12_pavilion_rooftops", "room": "ja_pavilion_rooftops", "cell": Vector2(22, 20)}, {"name": "13_willow_path_west", "room": "wp_west", "cell": Vector2(26, 16)}]
	var foliage_fights := [
		{"name": "14_fight_willow_path_hud", "room": "wp_east", "cell": Vector2(20, 14), "foes": [["wild_boarlet", Vector2(3, 2)], ["wild_boarlet", Vector2(-4, 3)], ["reedtail_rat", Vector2(5, -1)]]},
		{"name": "15_fight_marsh_edge_hud", "room": "rm_marsh_edge", "cell": Vector2(34, 15), "foes": [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)], ["reed_frog", Vector2(2, -2)]]}]
	var alone := [{"name": "06_riverside_square", "take": [["view_alone", "*", "td_proto_square"]]}, {"name": "07_height_levels", "take": [["heights", "*", "view"]]}]
	var monster_stage := [["pausable"], ["new_game"], ["frames", 360], ["keep_whole", true]]
	var at_the_flats := {"room": "lf_reed_shallows", "cell": SPOT, "wait": 90}
	var s := {}

	# ------------------------------------------------------------------------------------------------ the redesign's phases
	s["phase1"] = {"doc": "Redesign phase 1 (docs/redesign_top_down_plan.md): the prototype square under the HUD, walking behind the house, the pier's gap and long jump, standing on the low wall",
		"out": "redesign/phase1/", "stage": [["proto"]], "rows": [
		{"name": "01_square"},
		{"name": "02_behind_house_strip", "do": [["start", ["prop", "house", Vector2(-1.5, -1), Vector2(0, 8)]]], "take": [["strip", "*", Vector2.RIGHT, 84, [], [], [0, 24, 42, 60, 84]]]},
		{"name": "02_behind_house", "do": [["start", ["prop", "house", Vector2(3.5, -1), Vector2(0, 8)]]]},
		{"name": "03_gap_strip", "do": [["start", Vector2(19.5, 23.4) * 32.0]], "take": [["strip", "*", Vector2.DOWN, 40, [6], [], [0, 10, 18, 26, 40]]]},
		{"name": "04_long_jump_strip", "do": [["start", Vector2(20.2, 27.0) * 32.0]], "take": [["strip", "*", Vector2.RIGHT, 48, [8], [1], [0, 9, 20, 32, 48]]]},
		{"name": "05_upper_level_strip", "do": [["start", Vector2(30.5, 19.6) * 32.0]], "take": [["strip", "*", Vector2.UP, 30, [2], [], [0, 8, 16, 24, 30]]]},
		{"name": "05_on_the_low_wall", "do": [["stop"], ["frames", 30]]}]}

	s["phase2"] = {"doc": "Redesign phase 2: a fight with three foes, a technique, the rooftop jump, the water's edge, an aimed attack and an aimed technique under the thumb",
		"out": "redesign/phase2/", "stage": [["proto"]], "rows": [
		{"name": "01_fight_three_foes", "do": [["arena", BASE, [["mudshell_crab", Vector2(-52, 10)], ["reedtail_rat", Vector2(46, -22)], ["wild_boarlet", Vector2(20, 44)]]], ["fight", 40, 14]]},
		{"name": "02_technique_strip", "do": [["arena", BASE, [["wild_boarlet", Vector2(90, 10)], ["mudshell_crab", Vector2(170, -6)]]], ["cooldowns_clear"], ["aim_technique", 1, Vector2.RIGHT]],
			"take": [["strip", "*", Vector2.ZERO, 36, [], [], [0, 8, 16, 24, 36]]]},
		{"name": "02_technique", "do": [["cooldowns_clear"], ["arena", BASE, [["wild_boarlet", Vector2(100, 0)], ["mudshell_crab", Vector2(120, 30)]]], ["aim_technique", 2, Vector2.RIGHT, 0.55], ["frames", 18]]},
		{"name": "03_rooftop_jump_strip", "do": [["arena", ["prop", "storehouse", Vector2(1.5, -1.0)], []]], "take": [["strip", "*", Vector2.DOWN, 96, [6, 60], [], [0, 14, 30, 50, 66, 96]]]},
		{"name": "04_water_edge_strip", "do": [["arena", Vector2(10.5, 20.0) * 32.0, []]], "take": [["strip", "*", Vector2.DOWN, 60, [], [], [0, 20, 40, 60]]]},
		{"name": "05_aimed_attack", "do": [["arena", BASE, [["wild_boarlet", Vector2(70, -20)], ["reedtail_rat", Vector2(-60, 40)]]], ["hud_state", true],
			["press", 90, "attack"], ["drag", 90, "attack", Vector2(80, -30)], ["frames", 16]]},
		{"name": "06_aimed_technique", "do": [["release", 90], ["frames", 30], ["press", 91, "slot2"], ["drag", 91, "slot2", Vector2(70, -70)], ["frames", 16]], "then": [["release", 91]]}]}

	s["phase3"] = {"doc": "Redesign phase 3 (art bible §12): the square as the game draws it (x2, under the HUD, whole), the mock beside it, the water's frames, a fight, the height-levels test",
		"out": "redesign/phase3/", "stage": [["proto"]], "rows": [
		{"name": "08_ingame_square_x2", "do": [["start", ["spawn"]], ["tick", 20]], "take": [["world"]]},
		{"name": "09_ingame_square_hud"},
		{"name": "10_ingame_whole_room", "take": [["whole_room"]]},
		{"name": "11_before_after", "take": [["panels", "*", [["The approved mock (Phase 3 art, the target)", "docs:redesign/phase3/01_square_mock_x2.png"],
			["Before: the loader with the new tiles, no auto-tiles, rims or shadows", "docs:redesign/phase3/07_ingame_square.png"],
			["After: in the game, the room redesigned, with bamboo, lotus pond and lanterns", "08_ingame_square_x2"]], 1]]},
		{"name": "15_water_frames_x2", "take": [["water_frames"]]},
		{"name": "13_fight_hud", "do": [["arena", BASE, [["mudshell_crab", Vector2(-120, 20)], ["reedtail_rat", Vector2(120, -50)], ["wild_boarlet", Vector2(70, 110)], ["mudshell_crab", Vector2(-40, -110)]]],
			["timeline", 16, {6: [["aim_attack", Vector2.LEFT]]}, {"whole": true}]], "take": [["shot"], ["view_x4", "14_fight_x4", Vector2.ZERO, Vector2i(160, 100)]]},
		{"name": "06_height_levels_test", "do": [["hud", "visible", true]], "take": [["heights", "*", "panels"]]}]}

	s["character"] = {"doc": "Redesign phase 3, decision 32: the real character in the square in the jian among the tutorial's villagers, a foe to fight; a strip of it cutting, walking and dashing",
		"out": "redesign/phase3/character/", "stage": [["proto"]], "rows": [
		{"name": "07_ingame_square", "do": [["equip", "training_jian"], ["villagers", Vector2(22.5, 18.6) * 32.0, [["aunt_ping", Vector2(-150, -50), "se"], ["lu_boatman", Vector2(-104, 30), "e"],
			["little_dou", Vector2(-40, -70), "s"], ["old_ma", Vector2(190, -40), "w"], ["washer_mei", Vector2(-190, 36), "s"], ["uncle_guo", Vector2(150, 60), "nw"]]],
			["frames", 300], ["arena", Vector2(22.5, 18.6) * 32.0, [["wild_boarlet", Vector2(84, 30)]]], ["hud_state", true], ["face", Vector2.RIGHT], ["frames", 10],
			["aim_attack", Vector2.RIGHT], ["frames", 8]], "take": [["shot"], ["closeup_last", "07_ingame_closeup", Vector2i(480, 270), Vector2i(240, 180)]]},
		{"name": "07_ingame_strip", "do": [["arena", Vector2(22.5, 18.6) * 32.0, [["wild_boarlet", Vector2(90, 0)]]], ["face", Vector2.RIGHT], ["frames", 4], ["aim_attack", Vector2.RIGHT]],
			"take": [["strip", "*", Vector2.ZERO, 34, [], [], [0, 5, 10, 16, 34]]]},
		{"name": "07_ingame_walk_strip", "take": [["strip", "*", Vector2(0.7, 0.7).normalized(), 40, [], [22], [0, 8, 16, 24, 40]]]}]}

	s["drag_moves"] = {"doc": "Decision 35: Attack's drag moves armed under the thumb, each with its mark on the button and the ground (the finisher, the Plunge and its impact, the guard)",
		"out": "redesign/drag_moves/", "stage": [["proto"]], "rows": [
		{"name": "01_finisher_armed", "do": [["arena", BASE, [["wild_boarlet", Vector2(-56, -44)], ["reedtail_rat", Vector2(64, 36)]]], ["hud_state", true],
			["press", 90, "attack"], ["drag", 90, "attack", Vector2(-100, -80)], ["frames", 12]]},
		{"name": "02_plunge_armed", "do": [["release", 90], ["frames", 40], ["secret_art", "plunge"], ["arena", BASE, [["wild_boarlet", Vector2(34, 12)], ["mudshell_crab", Vector2(-36, 18)]]],
			["hud_state", true], ["jump"], ["frames", 5], ["press", 91, "attack"], ["drag", 91, "attack", Vector2(0, 80)], ["frames", 2]]},
		{"name": "03_plunge_impact", "do": [["release", 91], ["frames", 4]]},
		{"name": "04_guard", "do": [["frames", 40], ["arena", BASE, [["wild_boarlet", Vector2(44, 0)]]], ["hud_state", true], ["face", Vector2.RIGHT], ["press", 92, "attack"], ["frames", 24]],
			"then": [["release", 92]]}]}

	var combo := {0: [["aim_attack", Vector2(1, 0.25)]], 18: [["aim_attack", Vector2(1, 0.25)]], 36: [["aim_attack", Vector2(1, 0.25)]]}
	var combo_rows := []
	for fam in ["jian", "fists", "spear", "heavy_sabre", "brush", "bell"]:
		combo_rows.append({"name": "ingame_combo_" + fam, "do": [["gear", "weapon", null if fam == "fists" else "training_" + fam, 900], ["refresh"],
			["arena", BASE, [["wild_boarlet", Vector2(46, 18)], ["mudshell_crab", Vector2(40, -24)]]], ["sturdy"], ["face", Vector2(1, 0.3)],
			["timeline", 64, combo, {"grab": [3, 1, 16, 192, 144], "into": "combo"}]], "take": [["sheet", "*", "combo", 8]]})
	var techs := [{"do": [["gear", "weapon", null], ["refresh"]]}]
	for aim in [Vector2(1, 0.4).normalized(), Vector2(0.2, 1).normalized(), Vector2.RIGHT.normalized(), Vector2(-1, -0.3).normalized()]:
		techs.append({"do": [["arena", BASE, [["wild_boarlet", Vector2(70, 20)], ["mudshell_crab", Vector2(-60, -30)], ["reedtail_rat", Vector2(10, 70)]]], ["sturdy"],
			["cooldowns_clear"], ["qi_full"], ["aim_technique", techs.size() - 1, aim, 0.6], ["tick", 14], ["keep_crop", "techniques", 480, 300]]})
	s["combat"] = {"doc": "Decision 38: the combat feel in the game: a combo of each weapon family frame by frame round the body, the dragged finisher and a dash attack, each technique's form, the guard, a parry and the Plunge",
		"out": "redesign/phase5/combat/", "stage": [["proto"], ["hud", "visible", false]], "rows": combo_rows + [
		{"name": "ingame_finisher_and_dash_attack", "do": [["gear", "weapon", "training_jian", 901], ["refresh"], ["arena", BASE, [["wild_boarlet", Vector2(0, 46)], ["wild_boarlet", Vector2(0, -52)]]],
			["sturdy"], ["timeline", 70, {0: [["finisher", Vector2.DOWN]], 36: [["dodge"]], 40: [["aim_attack", Vector2.UP]]},
			{"grab": [4, 1, 16, 192, 144], "into": "finisher", "move": [[34, 40, Vector2.UP * 0.9]]}]], "take": [["sheet", "*", "finisher", 8]]}] + techs + [
		{"name": "ingame_techniques", "take": [["sheet", "*", "techniques", 2]]},
		{"do": [["arena", BASE, [["wild_boarlet", Vector2(40, 0)]]], ["face", Vector2.RIGHT], ["submit", {"type": "guard_start"}], ["frames", 6], ["keep_crop", "marks", 192, 144],
			["parry"], ["frames", 2], ["keep_crop", "marks", 192, 144], ["submit", {"type": "guard_end"}], ["secret_art", "plunge"],
			["arena", BASE, [["wild_boarlet", Vector2(34, 12)], ["mudshell_crab", Vector2(-36, 18)]]], ["jump"], ["frames", 6], ["plunge"], ["tick", 5],
			["keep_crop", "marks", 192, 144], ["frames", 4], ["keep_crop", "marks", 192, 144]]},
		{"name": "ingame_guard_parry_plunge", "take": [["sheet", "*", "marks", 4]], "then": [["hud", "visible", true]]}]}

	s["phase4"] = {"doc": "Redesign phase 4: a new top-down character's game, each converted room under the HUD at a spot that shows it, and a quest talk on the dialogue page",
		"out": "redesign/phase4/", "stage": [["new_game"]], "rows": [
		{"name": "01_fishers_hut", "cell": Vector2(8, 7)},
		{"do": [["portal", "exit"], ["frames", 120]]},
		{"name": "02_village_home_lane", "cell": Vector2(12, 18), "wait": 60},
		{"name": "03_village_square", "cell": Vector2(33, 21), "wait": 60},
		{"name": "04_village_docks", "cell": Vector2(58, 26), "wait": 60},
		{"name": "16_quest_talk_lu", "cell": Vector2(55, 28), "wait": 40, "do": [["talk", "npc_lu_boatman"], ["frames", 90]], "then": [["close_pages"]]},
		{"name": "05_old_ma_store", "room": "lf_old_ma_store", "cell": Vector2(9, 7)}, {"name": "06_granny_liu_hut", "room": "lf_granny_liu_hut", "cell": Vector2(9, 7)},
		{"name": "07_reed_shallows", "room": "lf_reed_shallows", "cell": Vector2(40, 15)}, {"name": "08_village_night", "room": "lf_village_night", "cell": Vector2(22, 20)},
		{"name": "09_lu_boat", "room": "lf_lu_boat", "cell": Vector2(11, 7)}, {"name": "10_willow_path_east", "room": "wp_east", "cell": Vector2(31, 13)},
		{"name": "11_willow_path_west", "room": "wp_west", "cell": Vector2(40, 15)}, {"name": "12_stoneford_gate", "room": "sf_gate", "cell": Vector2(30, 14)},
		{"name": "13_market_street", "room": "sf_market", "cell": Vector2(24, 15)}, {"name": "14_artisan_row", "room": "sf_artisan_row", "cell": Vector2(30, 15)},
		{"name": "15_fairground", "room": "sf_fairground", "cell": Vector2(28, 16)}]}

	s["chapter2"] = {"doc": "Redesign phase 4, second part: chapter 2's rooms (the Entry Trials, both sects' grounds, the Marsh Edge) under the HUD, with the foes that live there",
		"out": "redesign/phase4/", "stage": [["new_game"], ["frames", 360]], "rows": [
		{"name": "17_trial_jade", "room": "sf_trial_jade", "cell": Vector2(20, 13), "foes": [["trial_puppet", Vector2(6, 3)]]},
		{"name": "18_trial_cloud", "room": "sf_trial_cloud", "cell": Vector2(18, 13), "foes": [["trial_puppet", Vector2(8, 3)]]},
		{"name": "19_jade_gate_street", "room": "ja_gate_street", "cell": Vector2(24, 15)}, {"name": "20_jade_gate_street_gate", "room": "ja_gate_street", "cell": Vector2(10, 22)},
		{"name": "21_jade_weapon_hall", "room": "ja_weapon_hall", "cell": Vector2(12, 9)}, {"name": "22_pavilion_rooftops", "room": "ja_pavilion_rooftops", "cell": Vector2(26, 14)},
		{"name": "23_east_terrace", "room": "ja_east_terrace", "cell": Vector2(30, 14)}, {"name": "24_herb_terraces", "room": "ja_herb_terraces", "cell": Vector2(26, 16)},
		{"name": "25_elder_hu_peak", "room": "ja_elder_hu_peak", "cell": Vector2(20, 13)}, {"name": "26_cloud_cliff_stair", "room": "cm_cliff_stair", "cell": Vector2(26, 18)},
		{"name": "27_sword_court", "room": "cm_sword_court", "cell": Vector2(34, 15)}, {"name": "28_cloud_weapon_hall", "room": "cm_weapon_hall", "cell": Vector2(12, 9)},
		{"name": "29_array_court", "room": "cm_array_court", "cell": Vector2(30, 15)}, {"name": "30_elder_sung_peak", "room": "cm_elder_sung_peak", "cell": Vector2(20, 14)},
		{"name": "31_marsh_edge", "room": "rm_marsh_edge", "cell": Vector2(30, 14), "foes": [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)]]},
		{"name": "32_marsh_edge_west", "room": "rm_marsh_edge", "cell": Vector2(12, 12), "foes": [["marsh_leech", Vector2(4, 4)], ["reed_frog", Vector2(-3, 3)]]}]}

	s["tutorial_foes"] = {"doc": "Redesign phase 4: the tutorial rooms' other foes in their own figures (the eel's night with its minnows, Old Snapper, the mossback toads), under the HUD while they fight, and x4 round the fight",
		"out": "redesign/phase4/", "stage": [["new_game"], ["frames", 360]], "rows": [
		{"name": "33_night_eel_minnows", "room": "lf_village_night", "cell": Vector2(33, 32), "wait": 60, "foes": [["hollow_minnow", Vector2(-3, -2)], ["hollow_minnow", Vector2(4, -3)]],
			"turned": true, "fight": 150, "take": [["shot"], ["view_x4", "34_night_eel_minnows_x4", Vector2(24, 24)]]},
		{"name": "35_reed_shallows_old_snapper", "room": "lf_reed_shallows", "cell": SPOT, "wait": 60, "foes": [["old_snapper", Vector2(3, 2)]],
			"turned": true, "fight": 150, "take": [["shot"], ["view_x4", "36_reed_shallows_old_snapper_x4", Vector2(24, 12)]]},
		{"name": "37_willow_path_west_toads", "room": "wp_west", "cell": Vector2(17, 7), "wait": 60, "foes": [["mossback_toad", Vector2(-3, 1)], ["mossback_toad", Vector2(3, 0)]],
			"turned": true, "fight": 150, "take": [["shot"], ["view_x4", "38_willow_path_west_toads_x4", Vector2(0, 0)]]}]}

	# ------------------------------------------------------------------------------------------------ the story
	s["story"] = {"doc": "Decision 39: the staged scenes as a new top-down character meets them, played by the game's own SceneDirector, the story moved on between them as the walk would",
		"out": "redesign/phase5/story/", "stage": [["new_game"]], "rows": [
		{"name": "01_opening_title", "do": [["scene_at", "opening_dawn", "title", 1.6]]},
		{"name": "02_opening_ping_wakes_you", "do": [["scene_at", "opening_dawn", "say", 1.2]]},
		{"name": "03_opening_walk_strip", "take": [["story_strip", "*", "opening_dawn", "move", 4, 14]]},
		{"name": "04_opening_bag_handoff", "do": [["scene_at", "opening_dawn", "handoff", 0.6]]},
		{"name": "05_opening_door_handoff", "do": [["scene_at", "opening_dawn", "handoff", 0.8, "door"]]},
		{"name": "06_dawn_boat_on_the_river", "do": [["portal", "exit"], ["frames", 30], ["scene_at", "river_dawn", "camera", 2.2]]},
		{"name": "07_dawn_villagers_talk", "do": [["scene_at", "river_dawn", "say", 1.5, "Hush"]]},
		{"name": "08_dawn_the_kite", "do": [["scene_at", "river_dawn", "say", 1.2, "kite"]]},
		{"name": "09_errands_guo_at_his_stump", "do": [["until_idle"], ["choose", "npc_lu_boatman", "hand_in", "a_quiet_river"], ["scene_at", "four_errands", "say", 0.8, "Hah"]],
			"then": [["until_idle"]]},
		{"name": "10_granny_the_jar_falls", "do": [["portal", "granny_door"], ["frames", 40], ["choose", "npc_granny_liu", "accept", "grannys_remedy"], ["scene_at", "granny_jar", "say", 1.0, "clumsy"]]},
		{"name": "11_granny_bag_handoff", "do": [["scene_at", "granny_jar", "handoff", 0.8]]},
		{"name": "12_granny_quick_use_handoff", "do": [["submit", {"type": "set_quick_use", "item": "herbal_tea"}], ["scene_at", "granny_jar", "handoff", 0.8, "Drink"]],
			"then": [["submit", {"type": "use_quick"}], ["until_idle"]]},
		{"name": "13_the_east_gate_opens", "do": [["quests_done", ["the_runaway_kite", "mas_delivery", "fists_first"]], ["portal", "exit"], ["frames", 30], ["quest_start", "crab_trouble"],
			["scene_at", "east_gate", "wait", 0.4]], "then": [["until_idle"]]},
		{"name": "14_crabs_mei_on_the_flats", "do": [["portal", "east_gate"], ["frames", 30], ["scene_at", "crabs_mei", "say", 1.2, "Shoo"]]},
		{"name": "15_crabs_drive_one_off", "do": [["scene_at", "crabs_mei", "handoff", 0.8]]},
		{"name": "16_the_hollow_night", "do": [["quests_done", ["crab_trouble", "evening_on_the_river"]], ["effects", [{"kind": "set_flag", "flag": "night_active"}]],
			["load", "lf_village_night"], ["frames", 20], ["scene_at", "hollow_rises", "title", 1.2]]},
		{"name": "17_hollow_night_the_river_boils", "do": [["scene_at", "hollow_rises", "say", 1.2, "river"]], "then": [["until_idle"]]},
		{"name": "18_river_token_lu", "do": [["effects", [{"kind": "set_flag", "flag": "night_survived"}]], ["quests_done", ["the_hollow_night"]], ["load", "lf_lu_boat"],
			["frames", 20], ["scene_at", "river_token", "say", 1.4, "gift"]]},
		{"name": "19_river_token_meditate_handoff", "do": [["scene_at", "river_token", "handoff", 0.8]]},
		{"name": "20_first_breakthrough", "do": [["submit", {"type": "start_meditation"}], ["until_idle"], ["submit", {"type": "stop_meditation"}],
			["effects", [{"kind": "add_progress", "pct_of_need": 1.0}]], ["submit", {"type": "report_page_opened", "page": "cultivation"}],
			["submit", {"type": "start_breakthrough", "support_items": []}], ["scene_at", "first_breakthrough", "say", 0.3, "Bone Forging", 0, 3600, true]], "then": [["until_idle"]]},
		{"name": "21_market_thief", "do": [["quests_done", ["the_river_token"]], ["load", "sf_market"], ["frames", 20], ["scene_at", "market_thief", "say", 0.8, "purse"]],
			"then": [["until_idle"]]},
		{"name": "22_fair_title", "do": [["load", "sf_fairground"], ["frames", 20], ["scene_at", "fair_arrival", "title", 1.4]]},
		{"name": "23_fair_recruiters", "do": [["scene_at", "fair_arrival", "say", 1.2, "Cloud Sect"]], "then": [["until_idle"]]},
		{"name": "24_sect_chosen_portrait_box", "do": [["queue_scene", "sect_chosen"], ["scene_at", "sect_chosen", "say", 0.0, "Welcome"], ["frames", 40]], "then": [["close_pages"]]},
		{"name": "25_sect_chosen", "do": [["scene_at", "sect_chosen", "title", 1.4]], "then": [["until_idle"]]}]}

	s["night"] = {"doc": "Decision 42: the Hollow Night as an action set piece, played by a character the story has brought there: the storm, Dou among the minnows, a school cut down, the grey up the lane, the eel's entrance, tell and window, Lu's palm, its fall",
		"out": "redesign/feedback/hollow_night/", "stage": night_stage + [["keep_whole", true]], "rows": [
		{"name": "01_that_night_the_storm", "do": [["scene_at", "hollow_rises", "title", 1.0]]},
		{"name": "02_the_river_boils", "do": [["scene_at", "hollow_rises", "camera", 0.15, "dou"]]},
		{"name": "03_dou_among_the_minnows", "do": [["scene_at", "hollow_rises", "say", 1.4, "Grey fish"]]},
		{"name": "04_aunt_ping_at_her_door", "do": [["scene_at", "hollow_rises", "say", 1.4, "lamp is lit"]]},
		{"name": "05_strike_the_minnows_handoff", "do": [["scene_at", "hollow_rises", "handoff", 0.8]]},
		{"do": [["strike_at", "npc_ma_night", "hollow_minnow", 2, "06_a_school_cut_down"], ["send_in", "npc_ma_night"]]},
		{"name": "07_old_ma_runs_for_the_hut", "do": [["scene_at", "night_ma_goes", "move", 1.4]]},
		{"do": [["until_idle"], ["strike_at", "npc_granny_night", "hollow_minnow", 2], ["send_in", "npc_granny_night"], ["until_idle"],
			["strike_at", "npc_dou_night", "hollow_minnow", 2], ["send_in", "npc_dou_night"], ["stand_cell", [19, 33]],
			["lane_and_card", "08_the_grey_spreads_up_the_lane", "09_the_eel_rises"], ["eel_found"], ["eel_bank"]]},
		{"name": "10_the_eel_rears_its_tell", "do": [["eel_tell"]]},
		{"name": "11_the_eel_ashore_its_window", "do": [["eel_landing"], ["eel_strike", 40]]},
		{"name": "12_the_climax_lu_comes", "do": [["eel_climax"], ["scene_at", "lu_arrives", "say", 1.0, "Lu!", 0, 1200]]},
		{"name": "13_lus_palm_pins_the_eel", "do": [["eel_pinned"], ["frames", 3]]},
		{"name": "14_the_eel_falls", "do": [["eel_down"], ["frames", 60]]},
		{"name": "15_the_grey_lifts_lu", "do": [["scene_at", "grey_lifts", "say", 1.6, "held the bank", 0, 1800]]},
		{"name": "16_the_palm_you_saw", "do": [["scene_at", "grey_lifts", "say", 1.6, "teach it", 0, 900]]},
		{"name": "17_on_lus_boat", "do": [["until_idle"], ["frames", 90]]}]}

	s["first_boss"] = {"doc": "Decision 45: the first boss reworked, played by a character the story has brought to the night: phase one ashore, the waking, phase two, overwhelmed, the elders' rescue, the fall, Lu's boat (the shots after_NN_*)",
		"out": "redesign/feedback/first_boss/", "stage": night_stage + [["boss_listen"], ["keep_whole", true]], "rows": [
		{"do": [["scene_at", "hollow_rises", "handoff", 0.2, "", 0, 3600], ["flag", "ma_safe"], ["flag", "granny_safe"], ["flag", "dou_safe"], ["flush"],
			["stand_cell", [19, 32]], ["boss_minnows"], ["eel_found", 0], ["boss_ashore"]]},
		{"name": "after_01_phase_one_the_eel_ashore", "do": [["eel_hp", 0.9], ["eel_strike", 24]]},
		{"name": "after_02_it_wakes_the_river_boils", "do": [["boss_wake"], ["scene_at", "eel_awakens", "wait", 0.3, "", 0, 2400]]},
		{"name": "after_03_it_wakes_aunt_pings_warning", "do": [["scene_at", "eel_awakens", "say", 1.2, "boiling", 0, 2400]]},
		{"name": "after_04_phase_two_stay_alive", "do": [["scene_at", "eel_awakens", "handoff", 0.4, "", 0, 2400]]},
		{"name": "after_05_phase_two_the_surge", "do": [["boss_wait", "surge"]]},
		{"name": "after_06_phase_two_its_hide_turns_the_blow", "do": [["boss_wait", "landing"], ["boss_glance"]]},
		{"name": "after_07_overwhelmed_the_eel_looms", "do": [["boss_overwhelmed"], ["scene_at", "elders_come", "say", 1.2, "Get away", 0, 2400]]},
		{"name": "after_08_granny_liu_comes", "do": [["scene_at", "elders_come", "say", 1.0, "Old legs", 0, 2400]]},
		{"name": "after_09_granny_lius_nine_seals", "do": [["scene_at", "elders_come", "say", 0.15, "Nine seals", 0, 2400]]},
		{"name": "after_10_old_ma_comes", "do": [["scene_at", "elders_come", "say", 1.2, "Thousand-Catty", 0, 2400]]},
		{"name": "after_11_old_mas_thousand_catty_palm", "do": [["scene_at", "elders_come", "wait", 0.24, "", 1, 2400]]},
		{"name": "after_12_lu_comes_up_the_river", "do": [["scene_at", "elders_come", "say", 1.2, "Back to the dark", 0, 2400]]},
		{"name": "after_13_lus_river_dragon_rises", "do": [["scene_at", "elders_come", "wait", 0.4, "", 2, 2400]]},
		{"name": "after_14_the_dragon_strikes", "do": [["scene_at", "elders_come", "wait", 0.08, "", 3, 2400]]},
		{"name": "after_15_the_eel_falls", "do": [["scene_at", "elders_come", "wait", 0.4, "", 3, 2400]]},
		{"name": "after_16_what_you_saw_was_cultivation", "do": [["scene_at", "grey_lifts", "say", 1.6, "cultivation, child", 0, 3600]]},
		{"name": "after_17_come_to_my_boat", "do": [["scene_at", "grey_lifts", "say", 1.6, "you begin", 0, 2400]]},
		{"name": "after_18_on_lus_boat_cultivate", "do": [["until_idle"], ["boss_to_the_boat"], ["scene_at", "river_token", "handoff", 0.8, "", 0, 2400]]}]}

	# ------------------------------------------------------------------------------------------------ the world's look
	s["light"] = {"doc": "Decision 40, runtime light: the key rooms by day, at dusk and at night under the HUD, and the height-levels room whole (--tag=before|after)",
		"out": "redesign/terrain_v2/light/", "vars": {"tag": "after"}, "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360]], "rows": [
		{"name": "{tag}_village_day", "hour": 0.375, "room": "lf_village", "cell": Vector2(33, 21), "then": [["log_light"]]},
		{"name": "{tag}_village_night", "hour": 0.375, "room": "lf_village_night", "cell": Vector2(22, 20), "then": [["log_light"]]},
		{"name": "{tag}_jade_gate_street", "hour": 0.375, "room": "ja_gate_street", "cell": Vector2(24, 15), "then": [["log_light"]]},
		{"name": "{tag}_marsh_edge", "hour": 0.375, "room": "rm_marsh_edge", "cell": Vector2(30, 14), "foes": [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)]], "then": [["log_light"]]},
		{"name": "{tag}_village_lane", "hour": 0.375, "room": "lf_village", "cell": Vector2(12, 18), "then": [["log_light"]]},
		{"name": "{tag}_village_dusk", "hour": 0.68, "room": "lf_village", "cell": Vector2(33, 21), "then": [["log_light"]]},
		{"name": "{tag}_village_clock_night", "hour": 0.87, "room": "lf_village", "cell": Vector2(33, 21), "then": [["log_light"]]},
		{"name": "{tag}_heights", "hour": 0.375, "take": [["heights", "*", "x2"]]}]}

	s["terrain"] = {"doc": "Decision 40, Terrain v2: the same views before and after the tile work, the world alone at x2, and the pairs (--tag=before|after)",
		"out": "redesign/terrain_v2/{tag}/", "vars": {"tag": "after"}, "stage": [["new_game"], ["frames", 360]], "take": [["world"]],
		"rows": terrain_views + alone + [{"do": [["pairs", "redesign/terrain_v2/", "redesign/terrain_v2/", ["01_village_square", "02_jade_gate_street", "03_marsh_edge",
			"04_reed_shallows", "05_fishers_hut_lane", "08_cliff_stair", "09_elder_sung_peak", "06_riverside_square", "07_height_levels"], "After: Terrain v2"]]}]}

	s["foliage"] = {"doc": "Decision 40's third part: Terrain v2's views and more with the foliage and decor, two fights under the HUD, every room whole, and the pairs (--tag=before|after)",
		"out": "redesign/terrain_v2/foliage/{tag}/", "vars": {"tag": "after"}, "stage": [["new_game"], ["frames", 360]], "take": [["world"]],
		"rows": terrain_views + foliage_views + [foliage_fights[0].merged({"take": [["shot"]]}), foliage_fights[1].merged({"take": [["shot"]]}),
			{"do": [["rooms_whole", "rooms/"]]}] + alone + [{"do": [["pairs", "redesign/terrain_v2/foliage/", "redesign/terrain_v2/foliage/", ["01_village_square",
			"02_jade_gate_street", "03_marsh_edge", "04_reed_shallows", "05_fishers_hut_lane", "08_cliff_stair", "09_elder_sung_peak", "06_riverside_square", "07_height_levels",
			"10_willow_path_east", "11_herb_terraces", "12_pavilion_rooftops", "13_willow_path_west", "14_fight_willow_path_hud", "15_fight_marsh_edge_hud"], "After: foliage and decor"]]}]}

	var ss_views := [
		["01_lotus_ferry_bank", "lf_village", Vector2(12, 31), [[14, 32, 0], [23, 32, 0]], true],
		["02_lotus_ferry_shore", "lf_village", Vector2(53, 31), [[56, 33, 0], [64, 32, 0]], false],
		["03_reed_shallows_beach", "lf_reed_shallows", Vector2(38, 19), [[44, 21, 0], [27, 21, 0]], true],
		["04_marsh_edge_spits", "rm_marsh_edge", Vector2(12, 21), [[12, 23, 0], [42, 22, 0]], true],
		["05_willow_path_east_stream", "wp_east", Vector2(18, 18), [[18, 20, 0]], true],
		["06_willow_path_west_pond", "wp_west", Vector2(22, 23), [[22, 24, 0]], true],
		["07_elder_hu_peak", "ja_elder_hu_peak", Vector2(22, 10), [[22, 5, 3], [1, 6, 3]], true],
		["08_cliff_stair_ledge", "cm_cliff_stair", Vector2(42, 10), [[48, 6, 4], [52, 8, 5]], true],
		["09_elder_sung_peak", "cm_elder_sung_peak", Vector2(30, 12), [[37, 8, 4], [31, 4, 3]], true]]
	var ss_rows := []
	var ss_pairs := []
	for v in ss_views:
		var take := [["world"]]
		ss_pairs.append(v[0])
		for k in (v[3] as Array).size():
			take.append(["closeup", "{tag}/closeups/%s_%d" % [v[0], k + 1], v[3][k]])
			ss_pairs.append("closeups/%s_%d" % [v[0], k + 1])
		if v[4]: take.append(["whole_room", "{tag}/rooms/" + str(v[1])])   # each room whole once, at its first view
		ss_rows.append({"name": "{tag}/" + str(v[0]), "room": v[1], "cell": v[2], "wait": 90, "take": take})
	s["sand_snow"] = {"doc": "Decision 44, sand and snow: each view at x2 with the body on the new ground, x4 close-ups of its transitions, every room they are in whole, the sampler (after) and the pairs (--tag=before|after)",
		"out": "redesign/feedback/sand_snow/", "vars": {"tag": "after"}, "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360]],
		"rows": ss_rows + [{"name": "{tag}/10_sampler", "if": "tag=after", "take": [["sampler", "*", SAMPLER_PAINT, "{tag}/closeups/10_sampler"]]},
			{"do": [["pairs", "redesign/feedback/sand_snow/", "redesign/feedback/sand_snow/pairs/", ss_pairs, "After: sand and snow"]]}]}

	var life_rows := []
	for r in [["01_village_square", "lf_village", Vector2(33, 21), 0.375], ["02_village_docks", "lf_village", Vector2(58, 28), 0.375],
			["03_village_lane", "lf_village", Vector2(12, 21), 0.375], ["04_sect_gate_street", "ja_gate_street", Vector2(30, 16), 0.375],
			["05_sect_sword_court", "cm_sword_court", Vector2(12, 14), 0.375], ["06_herb_terraces", "ja_herb_terraces", Vector2(20, 22), 0.375],
			["07_marsh_edge", "rm_marsh_edge", Vector2(10, 16), 0.375], ["08_peak_vista", "ja_elder_hu_peak", Vector2(24, 23), 0.375],
			["09_cliff_stair", "cm_cliff_stair", Vector2(28, 30), 0.375], ["10_market", "sf_market", Vector2(30, 16), 0.375],
			["11_interior_granny_liu", "lf_granny_liu_hut", Vector2(9, 9), 0.375], ["12_interior_fishers_hut", "lf_fishers_hut", Vector2(8, 9), 0.375],
			["13_interior_store", "lf_old_ma_store", Vector2(8, 9), 0.375], ["14_interior_weapon_hall", "ja_weapon_hall", Vector2(12, 10), 0.375],
			["15_village_night", "lf_village", Vector2(33, 21), 0.87], ["16_marsh_night", "rm_marsh_edge", Vector2(10, 16), 0.87],
			["17_village_story_night", "lf_village_night", Vector2(22, 20), 0.375]]:
		life_rows.append({"name": "{tag}/" + r[0], "hour": r[3], "room": r[1], "cell": r[2]})
	for r in [["01_sparrows_pecking", "lf_village", Vector2(35, 29), 0.375, "sparrows", Vector2(20, -30)],
			["02_sparrows_take_off", "lf_village", Vector2(35, 29), 0.375, "sparrows_flee", Vector2(20, -40)],
			["03_hens_and_dog", "lf_village", Vector2(47, 26), 0.375, "", Vector2(0, 0)],
			["04_fish_dragonfly", "lf_village", Vector2(24, 32), 0.375, "water", Vector2(0, 30)],
			["05_frogs", "rm_marsh_edge", Vector2(34, 21), 0.375, "frogs", Vector2(0, 10)],
			["06_butterflies", "ja_gate_street", Vector2(14, 23), 0.375, "butterflies", Vector2(0, 0)],
			["07_grass_parts", "lf_village", Vector2(5.5, 26.2), 0.375, "", Vector2(0, -10)],
			["08_work_carry_mend", "lf_village", Vector2(58, 25), 0.375, "", Vector2(10, 20)],
			["09_work_laundry_fish", "lf_village", Vector2(16, 30), 0.375, "", Vector2(0, 10)],
			["10_work_chop", "lf_village", Vector2(61, 20), 0.375, "", Vector2(20, -20)],
			["10b_chimney_smoke", "lf_village", Vector2(18, 8), 0.375, "", Vector2(0, 20)],
			["11_work_forms", "lf_village", Vector2(32, 24), 0.375, "", Vector2(-20, -10)],
			["12_work_sword_hammer", "ja_weapon_hall", Vector2(13, 9), 0.375, "", Vector2(10, -50)],
			["13_work_sweep", "ja_gate_street", Vector2(31, 18), 0.375, "", Vector2(-20, -20)],
			["14_interior_sun", "lf_fishers_hut", Vector2(9, 9), 0.375, "", Vector2(0, -60)],
			["15_interior_granny", "lf_granny_liu_hut", Vector2(9, 9), 0.375, "", Vector2(-40, -50)],
			["16_incense_banners", "ja_gate_street", Vector2(6, 16), 0.375, "", Vector2(0, -40)],
			["17_vista_peak", "ja_elder_hu_peak", Vector2(24, 25), 0.375, "", Vector2(0, 50)],
			["18_vista_north", "cm_sword_court", Vector2(30, 4), 0.375, "", Vector2(0, -60)],
			["19_vista_river", "lf_village", Vector2(30, 33), 0.375, "", Vector2(0, 60)],
			["20_lanterns_night", "lf_village", Vector2(64, 27), 0.87, "", Vector2(-40, -10)],
			["21_boat_on_the_river", "lf_lu_boat", Vector2(12, 8), 0.375, "", Vector2(0, 0)]]:
		life_rows.append({"name": "detail/" + r[0], "if": "detail", "hour": r[3], "room": r[1], "cell": r[2], "wait": 150,
			"do": [["critters", r[4]]] if r[4] != "" else [], "take": [["detail", "*", r[5]]]})
	s["life"] = {"doc": "Decision 43, the living world: the village, a sect, the terraces, the marsh, a peak, the market, four interiors and two nights under the HUD, the room played a few seconds first (--tag=before|after; --detail adds the close-ups x2 into detail/)",
		"out": "redesign/feedback/living_world/", "vars": {"tag": "after"}, "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360]], "rows": life_rows}

	var work_rows := []
	for r in [["ingame_01_village_sweep", "lf_village", "npc_aunt_ping_lane", "work_sweep"], ["ingame_02_village_carry", "lf_village", "npc_shen_lian_npc", "work_carry"],
			["ingame_03_village_laundry", "lf_village", "npc_washer_mei", "work_hang"], ["ingame_04_village_fisher", "lf_village", "x_bank_fisher", "work_rod"],
			["ingame_05_village_woodcutter", "lf_village", "x_woodcutter", "work_chop"], ["ingame_06_village_net", "lf_village", "npc_fisher_wen", "work_mend"],
			["ingame_07_hut_cook", "lf_fishers_hut", "npc_aunt_ping", "work_stir"], ["ingame_08_hut_grind", "lf_granny_liu_hut", "npc_granny_liu", "work_grind"],
			["ingame_09_sect_smith", "ja_weapon_hall", "npc_jade_smith", "work_hammer"], ["ingame_10_sect_sweeper", "ja_gate_street", "x_ja_sweeper", "work_sweep"],
			["ingame_11_sect_herbs", "ja_herb_terraces", "npc_jade_gardener", "work_pick"], ["ingame_12_market_cook", "sf_market", "npc_auntie_rong", "work_stir"],
			["ingame_13_artisan_smith", "sf_artisan_row", "npc_smith_bao", "work_hammer"], ["ingame_14_marsh_fisher_cast", "rm_marsh_edge", "x_marsh_fisher", "work_cast"]]:
		work_rows.append({"name": r[0], "take": [["worker", "*", r[1], r[2], r[3]]]})
	s["work_poses"] = {"doc": "Decision 44: the people at work in their drawn work poses (close-ups x2 round each worker), the village and a sect at work, and the player using a place mid-pose",
		"out": "redesign/feedback/work_poses/", "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360],
			["set", "training_sect", {"id": "jade_sect", "rank": "outer", "contribution": 0}]], "rows": work_rows + [
		{"name": "ingame_20_village_at_work", "room": "lf_village", "cell": Vector2(55, 22), "wait": 240},
		{"name": "ingame_21_sect_at_work", "room": "ja_gate_street", "cell": Vector2(38, 20), "wait": 240},
		{"name": "ingame_22_weapon_hall_at_work", "room": "ja_weapon_hall", "cell": Vector2(13, 10), "wait": 240},
		{"do": [["unlock", ["mail", "cultivation", "herb_garden", "storage"]], ["frames", 420]]},   # the places' systems opened, their notices gone
		{"name": "ingame_30_player_open_letter_box", "take": [["place_use", "*", "letter_box"]]},
		{"name": "ingame_31_player_tend_bed", "take": [["place_use", "*", "garden_bed"]]},
		{"name": "ingame_32_player_sit_mat", "take": [["place_use", "*", "meditation_mat"]]}]}

	# ------------------------------------------------------------------------------------------------ figures, before and after
	s["quality"] = {"doc": "Decision 42's rollout: the figure drawn better, the same instants before and after (the world alone x2, the tree held still), with boxes.json of where each body stands (--tag=before|after)",
		"out": "redesign/feedback/character_quality/rollout/{tag}/", "vars": {"tag": "after"}, "stage": [["pausable"], ["new_game"], ["frames", 360], ["hud", "visible", false]], "rows": [
		{"name": "01_village_square", "take": [["staged", "*", {"room": "lf_village", "spot": Vector2(33.5, 21.5), "player": ["idle", 0, "s"], "people": [
			["uncle_guo", Vector2(30.3, 22.1), "se", "idle"], ["washer_mei", Vector2(31.9, 24.3), "se", "idle"], ["little_dou", Vector2(36.7, 22.7), "sw", "idle"],
			["shen_lian_npc", Vector2(38.2, 20.3), "sw", "idle"]]}]]},
		{"name": "02_jade_gate_street", "take": [["staged", "*", {"room": "ja_gate_street", "spot": Vector2(24.5, 15.6), "player": ["idle", 0, "s"], "people": [
			["jade_deacon", Vector2(21.2, 14.6), "se", "idle"], ["jade_disciple_b", Vector2(20.6, 17.2), "se", "idle"], ["jade_steward", Vector2(26.4, 17.8), "sw", "idle"],
			["jade_disciple_a", Vector2(28.0, 15.2), "sw", "idle"]]}]]},
		# The story's gestures (decision 39): the player and Shen Lian salute, Guo kneels, Mei points the way, Dou starts back.
		{"name": "04_gestures", "take": [["staged", "*", {"room": "lf_village", "spot": Vector2(33.5, 21.5), "player": ["salute", 2, "se"], "people": [
			["uncle_guo", Vector2(31.2, 22.3), "se", "kneel"], ["washer_mei", Vector2(31.9, 24.3), "e", "point"], ["little_dou", Vector2(36.2, 22.9), "sw", "startle"],
			["shen_lian_npc", Vector2(35.6, 20.8), "sw", "salute"]]}]]},
		{"name": "03_fight", "take": [["staged_fight"]]},
		{"name": "boxes", "take": [["boxes_json"]], "then": [["hud", "visible", true]]}]}

	s["people_scale"] = {"doc": "Decision 43: the people drawn about 1.2x bigger, the same instants before and after: the opening's scenes, the villagers at the hut's door, a roof, an interior, a fight (--tag=before|after)",
		"out": "redesign/feedback/people_scale/{tag}/", "vars": {"tag": "after"}, "stage": [["pausable"], ["new_game"]], "rows": [
		{"name": "04_scene_hut", "do": [["scene_at", "opening_dawn", "say", 1.2]]},
		{"name": "06_scene_home_lane", "do": [["scene_at", "opening_dawn", "handoff", 0.8, "door"], ["portal", "exit"], ["frames", 30], ["scene_at", "river_dawn", "say", 1.5, "Hush"]],
			"then": [["until_idle"], ["hud", "visible", false]]},
		{"name": "01_door_hut_people", "take": [["staged", "*", {"room": "lf_village", "spot": Vector2(8.3, 15.3), "player": ["idle", 0, "sw"], "people": [
			["aunt_ping", Vector2(10.3, 16.1), "sw", "idle"], ["washer_mei", Vector2(11.5, 15.4), "sw", "idle"], ["little_dou", Vector2(10.9, 17.3), "sw", "idle"],
			["uncle_guo", Vector2(12.6, 16.8), "sw", "idle"], ["granny_liu", Vector2(15.2, 15.3), "sw", "idle"]]}]]},
		{"name": "03_roof", "take": [["staged", "*", {"room": "lf_village", "spot": Vector2(18.0, 12.4), "player": ["idle", 0, "s"], "people": [
			["little_dou", Vector2(16.4, 15.4), "se", "point"], ["washer_mei", Vector2(20.2, 15.8), "sw", "idle"]]}]]},
		{"name": "05_interior", "take": [["staged", "*", {"room": "lf_fishers_hut", "spot": Vector2(9.5, 10.8), "player": ["idle", 0, "se"], "people": [
			["aunt_ping", Vector2(6.0, 6.4), "se", "idle"]]}]]},
		{"name": "02_fight", "take": [["staged_fight"]], "then": [["hud", "visible", true]]}]}

	var poses := []
	for st in [["01_idle", "idle", 0, Vector2.DOWN], ["02_tells", "windup", -1, Vector2(1, 1)], ["03_strikes", "attack", 1, Vector2(1, 1)], ["04_struck", "hurt", 0, Vector2(1, 1)]]:
		poses.append({"name": st[0], "do": [["pose_lineup", st[1], st[2], st[3], true]]})
	s["monsters"] = {"doc": "Decision 43's monsters: every foe drawn for the grid lined up on the Reed Shallows and held still (idle, tell, strike, struck, falling, the elites), the eel on the night's river, live fights under the HUD (--tag=before|after)",
		"out": "redesign/feedback/monsters/{tag}/", "vars": {"tag": "after"}, "stage": monster_stage, "take": [["lineup_shot"]], "rows": [
		at_the_flats.merged({"do": [["hud", "visible", false], ["lineup", MONSTER_LINEUP]]})] + poses + [
		{"name": "05_falling", "do": [["fell_lineup"]]},
		{"do": [["lineup", MONSTER_ELITES]]},
		{"name": "06_elites", "do": [["pose_lineup", "idle", 0, Vector2(1, 1)]]},
		{"name": "06_elites_tells", "do": [["pose_lineup", "windup", -1, Vector2(1, 1)]]},
		{"do": [["paused", false]]},
		{"room": "lf_village_night", "cell": Vector2(33, 32), "do": [["eel_on_river"]]},
		{"name": "07_eel_idle", "take": [["eel_pose_shot", "*", "idle", 0]]},
		{"name": "07_eel_tell", "take": [["eel_pose_shot", "*", "windup", -1]]},
		{"name": "07_eel_strike", "take": [["eel_pose_shot", "*", "attack", 1]]},
		{"do": [["paused", false], ["hud", "visible", true]]},
		{"name": "08_fight_willow_path", "room": "wp_east", "cell": Vector2(20, 14), "wait": 60, "foes": [["wild_boarlet", Vector2(3, 2)], ["wild_boarlet", Vector2(-4, 3)],
			["reedtail_rat", Vector2(5, -1)]], "turned": true, "fight": [150, false], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "09_fight_marsh_edge", "room": "rm_marsh_edge", "cell": Vector2(34, 15), "wait": 60, "foes": [["hollowed_boarlet", Vector2(3, 3)], ["reed_otter", Vector2(-4, 4)],
			["reed_frog", Vector2(2, -2)], ["marsh_leech", Vector2(-3, -2)]], "turned": true, "fight": [150, false], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "10_fight_reed_shallows", "room": "lf_reed_shallows", "cell": SPOT, "wait": 60, "foes": [["old_snapper", Vector2(3, 2)], ["mudshell_crab", Vector2(-3, 1)],
			["mudshell_crab", Vector2(-2, -3)]], "turned": true, "fight": [150, false], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "11_fight_hollow_night", "room": "lf_village_night", "cell": Vector2(33, 32), "wait": 60, "foes": [["hollow_minnow", Vector2(-3, -2)], ["hollow_minnow", Vector2(4, -3)],
			["hollow_minnow", Vector2(2, 3)]], "turned": true, "fight": [150, false], "take": [["shot"], ["view_x4", "*_x4"]]}]}

	var polish := []
	for st in [["12_head_on", "idle", 0, Vector2.DOWN], ["13_head_on_walk", "walk", 2, Vector2.DOWN], ["14_head_on_tells", "windup", -1, Vector2.DOWN],
			["15_head_on_strikes", "attack", 1, Vector2.DOWN], ["16_tail_on", "idle", 0, Vector2.UP], ["17_tail_on_walk", "walk", 2, Vector2.UP],
			["18_tail_on_tells", "windup", -1, Vector2.UP], ["19_three_quarter", "idle", 0, Vector2(1, 1)], ["20_three_quarter_tells", "windup", -1, Vector2(1, 1)]]:
		polish.append({"name": st[0], "do": [["pose_lineup", st[1], st[2], st[3]]]})
	s["monsters_polish"] = {"doc": "Decision 44's foe polish: the four-legged foes and the leech head-on, tail-on and three-quarter (idle, mid-stride, tell, hit), and leeches on the bank and in the river (--tag=before|after)",
		"out": "redesign/feedback/monsters/polish/{tag}/", "vars": {"tag": "after"}, "stage": monster_stage, "take": [["lineup_shot"]], "rows": [
		at_the_flats.merged({"do": [["hud", "visible", false], ["lineup", POLISH_LINEUP]]})] + polish + [
		{"name": "21_leech_bank_and_river", "do": [["leeches"]], "then": [["paused", false]]}]}

	# Audit 45 (E2): the monster engine's first new species, each one spec (tools/content/monsters/specs/).
	var e2 := []
	for st in [["01_head_on", "idle", 0, Vector2.DOWN], ["02_walk", "walk", 2, Vector2(1, 1)], ["03_tells", "windup", -1, Vector2(1, 1)],
			["04_strikes", "attack", 1, Vector2(1, 1)], ["05_struck", "hurt", 0, Vector2(1, 1)], ["06_side", "idle", 0, Vector2.RIGHT],
			["07_tail_on", "walk", 2, Vector2.UP], ["08_tail_on_tells", "windup", -1, Vector2.UP]]:
		e2.append({"name": st[0], "do": [["pose_lineup", st[1], st[2], st[3]]]})
	s["monsters_e2"] = {"doc": "Audit 45 E2: the first species drawn from a monster-engine spec (the rock beetle, the pebble imp, the greyfin) beside the reed rat, the crab and a boarlet for scale on the Reed Shallows, held still (head-on, walking, tell, strike, struck, side, tail-on, falling), their elites, and a live fight under the HUD (--tag=after)",
		"out": "redesign/feedback/monsters/e2/{tag}/", "vars": {"tag": "after"}, "stage": monster_stage, "take": [["lineup_shot"]], "rows": [
		at_the_flats.merged({"do": [["hud", "visible", false], ["lineup", E2_LINEUP]]})] + e2 + [
		{"name": "09_falling", "do": [["fell_lineup"]]},
		{"do": [["lineup", E2_ELITES]]},
		{"name": "10_elites", "do": [["pose_lineup", "idle", 0, Vector2(1, 1)]]},
		{"name": "11_elites_tells", "do": [["pose_lineup", "windup", -1, Vector2(1, 1)]]},
		{"do": [["paused", false], ["hud", "visible", true]]},
		{"name": "12_fight", "room": "lf_reed_shallows", "cell": SPOT, "wait": 60, "foes": [["rock_beetle", Vector2(3, 2)], ["pebble_imp", Vector2(-4, 1)],
			["greyfin", Vector2(-2, -3)]], "turned": true, "fight": [150, false], "take": [["shot"], ["view_x4", "*_x4"]]}]}

	# M1: the monster engine's first batch past E2 (tools/content/monsters/specs/), lined up by kind on the Reed Shallows
	# beside drawn foes for scale: (a) the quarry's and the bamboo grove's, (b) chapter 3's and 4's beasts and the paper
	# ghost, (c) the people (cast in the shared character body); every pose of the E2 set, their elites, and live fights
	# in the top-down rooms they live in.
	var m1 := []
	for lu in [["a", M1_LINEUP_A], ["b", M1_LINEUP_B], ["c", M1_LINEUP_C]]:
		m1.append({"do": [["lineup", lu[1]]]})
		for st in [["01_head_on", "idle", 0, Vector2.DOWN], ["02_walk", "walk", 2, Vector2(1, 1)], ["03_tells", "windup", -1, Vector2(1, 1)],
				["04_strikes", "attack", 1, Vector2(1, 1)], ["05_struck", "hurt", 0, Vector2(1, 1)], ["06_side", "idle", 0, Vector2.RIGHT],
				["07_tail_on", "walk", 2, Vector2.UP], ["08_tail_on_tells", "windup", -1, Vector2.UP]]:
			m1.append({"name": lu[0] + "_" + st[0], "do": [["pose_lineup", st[1], st[2], st[3]]]})
		m1.append({"name": lu[0] + "_09_falling", "do": [["fell_lineup"]]})
	for el in [["d", M1_ELITES_A], ["e", M1_ELITES_B]]:
		m1.append({"do": [["lineup", el[1]]]})
		m1.append({"name": el[0] + "_10_elites", "do": [["pose_lineup", "idle", 0, Vector2(1, 1)]]})
		m1.append({"name": el[0] + "_11_elites_tells", "do": [["pose_lineup", "windup", -1, Vector2(1, 1)]]})
	s["monsters_m1"] = {"doc": "M1: the monster engine's first batch past E2 (the quarry's, the bamboo grove's, chapter 3-5's beasts and people) beside drawn foes for scale on the Reed Shallows, held still (head-on, walking, tell, strike, struck, side, tail-on, falling), their elites, and live fights in their own top-down rooms under the HUD (the Caravan Road, Bend Shore, the Boss Den, the Lower Pit, the Thicket Heart, the Whispering Bamboo, the Pilgrim Stairs, the Hall of Lanterns, the Abbot's Sanctum, the Gorge Mouth) (--tag=after)",
		"out": "redesign/feedback/monsters/m1/{tag}/", "vars": {"tag": "after"}, "stage": monster_stage, "take": [["lineup_shot"]], "rows": [
		at_the_flats.merged({"do": [["hud", "visible", false]]})] + m1 + [
		{"do": [["paused", false], ["hud", "visible", true]]},
		# A fight in the species' own room: the room's own foes cleared (they stand far above a new body's Level, and a
		# blow of theirs would open the fall's page over the shot), the batch's set on the player at Level 1.
		{"name": "12_fight_caravan_road", "room": "cr_caravan_road", "cell": Vector2(30, 16), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(30, 16), [["mudwater_bandit", Vector2(3, 1)], ["bandit_archer", Vector2(-5, 1)], ["mud_hound", Vector2(2, -2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "13_fight_bend_shore", "room": "dw_bend_shore", "cell": Vector2(23, 15), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(23, 15), [["jade_carp", Vector2(-2, 2)], ["tide_crab", Vector2(3, 1)], ["ember_fox", Vector2(-4, -2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "14_fight_boss_den", "room": "mh_boss_den", "cell": Vector2(28, 14), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(28, 14), [["big_toad_tan", Vector2(4, 0)], ["mudwater_lieutenant", Vector2(-3, 2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "15_fight_lower_pit", "room": "sq_lower_pit", "cell": Vector2(24, 17), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(24, 17), [["stone_tortoise", Vector2(4, 0)], ["ironclaw_mole", Vector2(-4, 1)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "16_fight_thicket_heart", "room": "bg_thicket_heart", "cell": Vector2(30, 14), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(30, 14), [["thornback_boar", Vector2(4, 1)], ["green_viper", Vector2(-4, 2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "17_fight_whispering_bamboo", "room": "bg_whispering_bamboo", "cell": Vector2(30, 14), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(30, 14), [["bamboo_monkey", Vector2(4, 2)], ["bamboo_monkey", Vector2(-4, 1)], ["ember_fox", Vector2(2, -2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "18_fight_pilgrim_stairs", "room": "cp_pilgrim_stairs", "cell": Vector2(24, 25), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(24, 25), [["stone_guardian", Vector2(4, 0)], ["stone_guardian", Vector2(-4, 2)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "19_fight_hall_of_lanterns", "room": "ds_hall_of_lanterns", "cell": Vector2(28, 8), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(28, 8), [["drowned_acolyte", Vector2(-4, 2)], ["paper_talisman_ghost", Vector2(4, -1)], ["paper_talisman_ghost", Vector2(3, 3)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "20_fight_abbots_sanctum", "room": "ds_abbots_sanctum", "cell": Vector2(30, 13), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(30, 13), [["drowned_abbot", Vector2(5, 0)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]},
		{"name": "21_fight_gorge_mouth", "room": "wg_gorge_mouth", "cell": Vector2(34, 11), "wait": 60, "do": [["clear_enemies"], ["close_pages"],
			["foes", Vector2(34, 11), [["gorge_bandit_adept", Vector2(4, 1)], ["gorge_bandit_adept", Vector2(-4, 1)]], true],
			["tick", 150], ["close_pages"]], "take": [["shot"], ["view_x4", "*_x4"]]}]}

	# ------------------------------------------------------------------------------------------------ the HUD and the pages
	s["hud"] = {"doc": "Decision 42, the prototype's feedback: the HUD at rest and in a fight, the Techniques page and its loadout bar, Old Ma's shop, Aunt Ping's offer and the screen once it is taken (--tag=before|after)",
		"out": "redesign/feedback/hud/", "vars": {"tag": "after"}, "stage": hud_stage, "rows": [
		{"name": "{tag}_hud_rest", "do": hud_rest},
		{"name": "{tag}_hud_fight", "do": hud_fight, "then": hud_fight_end},
		{"name": "{tag}_techniques", "do": [["open_page", "techniques"], ["frames", 240]], "take": [["shot"], loadout_bar], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_shop", "do": [["open_page", "shop", {"shop": "old_ma", "npc": "old_ma"}], ["frames", 90]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_quest_offer", "do": [["beside", "npc_aunt_ping_lane"], ["clear_notices"], ["talk", "npc_aunt_ping_lane"], ["frames", 20], ["dialogue_end"], ["frames", 30]]},
		{"name": "{tag}_quest_accepted", "do": [["dialogue_accept"], ["frames", 40], ["dialogue_end"], ["clear_notices"], ["frames", 20]], "then": [["close_pages"]]}]}

	s["hud_round"] = {"doc": "Decision 43: the technique buttons round and a little bigger: the HUD at rest and in a fight, the thumb's cluster x2, one button through its cooldown x3; at 1280x720 and at a 20:9 phone's 2400x1080 (the _phone shots) (--tag=before|after)",
		"out": "redesign/feedback/hud/", "vars": {"tag": "after"}, "stage": hud_stage, "rows": [
		{"name": "{tag}_round_rest{sfx}", "do": [["know_all"], ["beside", "npc_lu_boatman"], ["hud", "fight_override", false], ["frames", 90], ["guides_off"], ["frames", 10],
			["clear_notices"], ["frames", 4]]},
		{"name": "{tag}_round_fight{sfx}", "do": [["hud", "fight_override", true], ["arena", ["here", Vector2(0, 40)], two_boarlets], ["qi_short", "cloudpiercing_stroke", 4.0],
			["cooldown", "tech:flowing_palm", 2.4], ["frames", 30], ["clear_notices"], ["cooldown", "tech:flowing_palm", 2.4], ["frames", 2]],
			"take": [["shot"], ["region", "{tag}_round_cluster{sfx}", Rect2(900, 380, 380, 340), 2, true]]},
		{"name": "{tag}_round_cooldown{sfx}", "take": [["cooldown_strip"]], "then": [["clear_enemies"], ["qi_full"], ["hud", "fight_override", null]]}]}

	s["pictures"] = {"doc": "Decision 42: the technique pictures and the old sprite's leftovers, before and after: the HUD at rest (a companion's chip) and in a fight, the Techniques page's Water and Fire trees, the array's travel picker; --pages adds the pages that show the character (--tag=before|after; --dir=people_scale shoots into that folder)",
		"out": "redesign/feedback/{dir}/", "vars": {"tag": "after", "dir": "pictures"}, "stage": hud_stage.slice(0, 4) + [["companion", "lan_yue"]] + hud_stage.slice(4), "rows": [
		{"name": "{tag}_hud_rest", "do": hud_rest},
		{"name": "{tag}_hud_fight", "do": hud_fight, "then": hud_fight_end},
		{"name": "{tag}_tree_water", "do": [["open_page", "techniques", {"tab": "water"}], ["frames", 20], ["page_action", "node", "flowing_palm"], ["frames", 240]],
			"take": [["shot"], loadout_bar], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_tree_fire", "do": [["open_page", "techniques", {"tab": "fire"}], ["frames", 20], ["frames", 240]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_travel_picker", "do": [["set", "training_sect", {"id": "jade_sect", "rank": "outer_disciple", "contribution": 0, "reputation": {"jade_sect": 10}}],
			["unlock", ["transfer_array"]], ["flag", "array_array_ja_gate"], ["flag", "array_array_marsh"], ["flag", "array_array_ja_peak"],
			["load", "ja_gate_street", Vector2.ZERO], ["frames", 20], ["no_scenes"], ["spot", Vector2(8, 22), 60], ["clear_notices"], ["array_tap", "array_ja_gate"], ["frames", 120]],
			"then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_page_character", "if": "pages", "do": [["open_page", "character"], ["frames", 120]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_page_inventory", "if": "pages", "do": [["open_page", "inventory"], ["frames", 120]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_page_cultivation", "if": "pages", "do": [["open_page", "cultivation"], ["frames", 120]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_page_shop", "if": "pages", "do": [["open_page", "shop", {"shop": "old_ma", "npc": "old_ma"}], ["frames", 120]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "{tag}_page_dialogue", "if": "pages", "do": [["load", "lf_village", Vector2.ZERO], ["frames", 20], ["no_scenes"], ["beside", "npc_aunt_ping_lane"], ["clear_notices"],
			["talk", "npc_aunt_ping_lane"], ["frames", 20], ["dialogue_end"], ["frames", 60]], "then": [["close_pages"], ["frames", 10]]}]}

	s["progression"] = {"doc": "Decision 45, the progression numbers: the HUD's three quick slots at rest and in a fight and the thumb's cluster; the Bag at 50 spaces; the Cultivation page's speed; a basic hit beside a charged one (run at 1280x720 and at 2400x1080: the _phone HUD shots)",
		"out": "redesign/feedback/progression/", "stage": hud_stage.slice(0, 4) + [["give", "healing_pill", 2], ["give", "qi_gathering_incense", 3], ["give", "rice_ball", 4],
			["give", "riverreed_ginseng_10", 2], ["give", "qi_gathering_pill", 1], ["set", "inventory.quick", ["herbal_tea", "healing_pill", "qi_gathering_incense"]],
			["learn_method", "riverbreath_fragment"], ["unlock", ["qi_springs"]]] + hud_stage.slice(4), "rows": [
		{"name": "hud_quick_rest{sfx}", "do": [["beside", "npc_lu_boatman"], ["hud", "fight_override", false], ["frames", 90], ["coach_off"], ["clear_notices"], ["frames", 4]]},
		{"name": "hud_quick_fight{sfx}", "do": [["hud", "fight_override", true], ["arena", ["here", Vector2(0, 40)], two_boarlets], ["frames", 30], ["coach_off"], ["clear_notices"],
			["frames", 2]], "take": [["shot"], ["region", "hud_quick_cluster{sfx}", Rect2(880, 300, 400, 420), 2, true]],
			"then": [["log_quick_slots"], ["clear_enemies"], ["hud", "fight_override", null], ["frames", 10]]},
		{"name": "bag_50", "if": "!phone", "do": [["open_page", "inventory"], ["frames", 60], ["bag_select", "healing_pill"], ["frames", 40], ["coach_off"]],
			"then": [["log_bag"], ["close_pages"], ["frames", 10]]},
		{"name": "cultivation_overview", "if": "!phone", "do": [["use_item", "qi_gathering_incense"], ["open_page", "cultivation"], ["frames", 90], ["coach_off"]]},
		{"name": "cultivation_speed", "if": "!phone", "do": [["page_set", "speed_open", true], ["frames", 20], ["coach_off"]], "then": [["log_speed"], ["close_pages"], ["frames", 10]]},
		{"name": "combat_basic_vs_charged", "if": "!phone", "do": [["spot", Vector2(33, 21), 30], ["arena", ["here", Vector2.ZERO], [["wild_boarlet", Vector2(64, 0)]]],
			["charged", "combat_basic", "combat_charged"]], "take": [["pair_sheet", "*", "combat_basic", "combat_charged"]]}]}

	s["tutorials"] = {"doc": "Decision 43: the unlock tutorials' coach at the phone layout: the first foundation points step by step, then the Techniques and Quests pages' tours on their first opening",
		"out": "redesign/feedback/tutorials/", "stage": [["new_game"], ["frames", 30], ["tutorial_stage"]], "take": [["snap"]], "rows": [
		{"name": "foundation_1_hud", "do": [["levels_gained", "bone_forging_1"], ["frames", 20]]},
		{"name": "foundation_2_menu", "do": [["open_page", "menu"], ["frames", 30]]},
		{"name": "foundation_3_tab", "do": [["open_page", "cultivation"], ["frames", 30]]},
		{"name": "foundation_4_node", "do": [["page_tab", "foundation"], ["frames", 20]]},
		{"do": [["submit", {"type": "open_meridian", "channel": "body"}], ["flush"], ["frames", 20], ["tour", "foundation", "foundation_{n}_tour_{k}", 5, 4], ["close_pages"], ["frames", 10]]},
		{"do": [["open_page", "techniques"], ["frames", 200], ["tour", "techniques", "techniques_{k}"], ["close_pages"], ["frames", 10]]},
		{"do": [["open_page", "quests"], ["frames", 40], ["tour", "quests", "quests_{k}"], ["close_pages"], ["frames", 10]]}]}

	s["tutorials_late"] = {"doc": "Decision 44: the late HUD powers' lessons, the character brought to the realm that opens each: the treasures, the weapon swap, Spirit Sense, the Presence and the Sphere; each guide's steps and each tour step",
		"out": "redesign/feedback/tutorials/late_powers/", "stage": [["new_game"], ["frames", 30], ["tutorial_stage"], ["late_stage"]], "take": [["snap", "*", true]], "rows": [
		{"do": [["late_open", "treasure", "heart_tempering_1", ["treasures"]], ["give", "practice_bell", 1], ["tour", "treasure", "treasure_{n}_tour_{k}", 1, 6, true]]},
		{"name": "treasure_4_guide_bag"},
		{"name": "treasure_5_guide_item", "do": [["open_page", "inventory"], ["frames", 30]], "then": [["coach", "next"], ["close_pages"], ["frames", 10]]},
		{"name": "weapon_swap_1_guide_bag", "do": [["late_open", "weapon_swap", "heart_tempering_1", ["dual_loadout"]]]},
		{"name": "weapon_swap_2_guide_weapon", "do": [["open_page", "inventory"], ["frames", 30]]},
		{"name": "weapon_swap_3_guide_spare", "do": [["bag_tap", "iron_jian"], ["frames", 10]], "then": [["page_action", "spare"], ["close_pages"], ["frames", 20]]},
		{"name": "weapon_swap_4_guide_swap", "then": [["coach", "control"], ["frames", 4], ["tour", "weapon_swap", "weapon_swap_{n}_tour_{k}", 5, 6, true],
			["submit", {"type": "swap_loadout"}], ["flush"], ["frames", 10]]},
		{"name": "sense_1_guide_fan", "do": [["hud", "fan_rest_open", false], ["hud", "fan_open", false], ["late_open", "sense", "spirit_awakening_1", ["spirit_sense"]]],
			"then": [["hud_call", "toggle_fan"], ["frames", 6]]},
		{"name": "sense_2_guide_button", "then": [["coach", "control"], ["frames", 4], ["tour", "sense", "sense_{n}_tour_{k}", 3, 6, true], ["submit", {"type": "sense_pulse"}],
			["flush"], ["frames", 10]]},
		{"name": "presence_1_guide", "do": [["late_open", "presence", "will_manifest_1", ["presence"]]], "then": [["coach", "control"], ["frames", 4],
			["tour", "presence", "presence_{n}_tour_{k}", 2, 6, true], ["submit", {"type": "toggle_presence", "on": false}], ["flush"], ["frames", 10]]},
		{"name": "sphere_1_guide", "do": [["late_open", "sphere", "sphere_lord_1", ["dao_tree", "sphere"]]], "then": [["coach", "control"], ["frames", 4],
			["tour", "sphere", "sphere_{n}_tour_{k}", 2, 6, true]]},
		{"name": "sphere_5_guide_menu"},
		{"name": "sphere_6_guide_cultivation", "do": [["open_page", "menu"], ["frames", 30]]},
		{"name": "sphere_7_guide_dao", "do": [["open_page", "cultivation"], ["frames", 30]], "then": [["close_pages"], ["frames", 10]]}]}

	# ------------------------------------------------------------------------------------------------ places and the sect's stretch
	s["places"] = {"doc": "Decision 43, systems as places: each place in the world with its state under the HUD and the world alone round it x2, the same corner quiet, the minimap's marks, the world map's Places view, the Menu's place card and its walk",
		"out": "redesign/feedback/places/", "clean": true, "stage": [["weather", "clear"], ["places_stage"]], "rows": [
		{"name": "01_lotus_ferry_services", "do": [["place_at", "lf_village", Vector2(35, 19), 120]]},
		{"name": "02_lotus_ferry_services_detail", "take": [["cell_detail", "*", Vector2(38.5, 13.5), Vector2(520, 200)]]},
		{"name": "03_lotus_ferry_services_quiet", "do": [["mail_read"], ["read_board"], ["storage", false], ["frames", 40]],
			"take": [["cell_detail", "*", Vector2(38.5, 13.5), Vector2(520, 200)]], "then": [["storage", true], ["mail_send", "places_review"]]},
		{"name": "04_meditation_mat_by_the_spring", "do": [["place_at", "lf_village", Vector2(28, 26), 90]]},
		{"name": "05_meditation_mat_detail", "take": [["cell_detail", "*", Vector2(25, 26.5), Vector2(220, 130)]]},
		{"name": "06_minimap_marks", "do": [["place_at", "lf_village", Vector2(35, 19), 30]], "take": [["region", "*", Rect2(1024, 8, 248, 156), 3]]},
		{"name": "07_market_stall_board_storehouse", "do": [["seen_forgotten"], ["place_at", "sf_market", Vector2(19, 17), 90]]},
		{"name": "08_market_stall_detail", "take": [["cell_detail", "*", Vector2(15.5, 12), Vector2(360, 200)]]},
		{"name": "09_market_courier_post_teleport_stone", "do": [["place_at", "sf_market", Vector2(44, 17), 60]], "take": [["cell_detail", "*", Vector2(35, 18), Vector2(420, 190)]]},
		{"name": "10_walked_up_to_the_board", "do": [["place_at", "sf_market", Vector2(20, 14), 40]], "take": [["cell_detail", "*", Vector2(20, 12.5), Vector2(220, 170)]]},
		{"name": "11_artisan_row_furnace_working", "do": [["furnace", 900.0], ["place_at", "sf_artisan_row", Vector2(47, 15), 90]],
			"take": [["cell_detail", "*", Vector2(52, 9.5), Vector2(220, 200)]]},
		{"name": "12_artisan_row_furnace_ready", "do": [["furnace", -5.0], ["frames", 60]], "take": [["cell_detail", "*", Vector2(52, 9.5), Vector2(220, 200)]], "then": [["furnace", null]]},
		{"name": "13_herb_terraces_beds", "do": [["beds"], ["place_at", "ja_herb_terraces", Vector2(21, 16), 90]], "take": [["cell_detail", "*", Vector2(20, 15.5), Vector2(420, 220)]]},
		{"name": "14_world_map_places_boards", "do": [["place_at", "lf_village", Vector2(12, 20), 30], ["open_page", "world_map", {"view": "places", "kind": "notice_board"}], ["frames", 90]],
			"then": [["close_pages"], ["frames", 10]]},
		{"name": "15_world_map_places_storehouse", "do": [["open_page", "world_map", {"place": "lf_storehouse"}], ["frames", 90]], "then": [["close_pages"], ["frames", 10]]},
		{"name": "16_menu_storage_at_the_storehouse", "do": [["open_page", "menu"], ["frames", 90]]},
		{"name": "17_menu_place_card", "do": [["page_action", "open", "storage"], ["frames", 40]]},
		{"name": "18_travel_arrived_at_the_storehouse", "do": [["page_action", "card_travel", "lf_storehouse"], ["travel_wait"], ["frames", 30]]},
		{"name": "19_menu_place_card_from_another_area", "do": [["place_at", "sf_market", Vector2(30, 17), 30], ["open_page", "menu"], ["frames", 60], ["page_action", "open", "storage"],
			["frames", 40]], "then": [["close_pages"]]}]}

	s["sect"] = {"doc": "Decision 42, the sect's stretch: for each sect, the steward's lesson at the array, where it goes, the watch post, the token humming, the mentor at the marsh, the walk up the grounds with something on the way, the mentor's array (from topdown_tutorial's checkpoints: run it with -- --keep=\"The Weapon Hall,The Weapon Hall (Cloud)\")",
		"out": "redesign/feedback/sect/", "boot": false, "each": [
			{"sect": "jade", "pre": "a_jade_", "cp": "the_weapon_hall", "gate": "ja_gate_street", "array": "array_ja_gate", "array_cell": Vector2(8, 22), "lesson": "array_lesson_jade",
				"mentor": "npc_elder_hu_marsh", "descends": "mentor_descends_jade", "peak": "ja_elder_hu_peak", "elder": "npc_elder_hu", "peak_scene": "mentor_peak_jade",
				"peak_array": "array_ja_peak", "peak_cell": Vector2(9, 25)},
			{"sect": "cloud", "pre": "b_cloud_", "cp": "the_weapon_hall_(cloud)", "gate": "cm_cliff_stair", "array": "array_cm_gate", "array_cell": Vector2(9, 26),
				"lesson": "array_lesson_cloud", "mentor": "npc_elder_sung_marsh", "descends": "mentor_descends_cloud", "peak": "cm_elder_sung_peak", "elder": "npc_elder_sung",
				"peak_scene": "mentor_peak_cloud", "peak_array": "array_cm_peak", "peak_cell": Vector2(11, 27)}], "rows": [
		{"do": [["checkpoint", "{cp}", "user://capture_sect_{sect}/"], ["to_gate", "{gate}"]]},
		{"name": "{pre}01_the_steward_shows_the_array", "do": [["scene_at", "{lesson}", "say", 1.6, "transfer array"]]},
		{"name": "{pre}02_step_onto_the_array", "do": [["scene_at", "{lesson}", "handoff", 1.0]]},
		{"name": "{pre}03_the_array_asks_where_to", "do": [["spot", "{array_cell}", 30], ["array_tap", "{array}", "sect"], ["frames", 240]], "then": [["close_pages"], ["until_idle"]]},
		{"name": "{pre}04_out_at_the_watch_post", "do": [["array_travel", "{array}", "array_marsh"], ["frames", 9]], "then": [["frames", 60]]},
		{"name": "{pre}05_the_watch_post", "if": "sect=jade", "cell": Vector2(8, 16), "wait": 60},
		{"name": "{pre}06_the_token_hums", "do": [["grey_patches"], ["scene_at", "grey_rises", "say", 1.2, "Grey shapes"]], "then": [["until_idle"]]},
		{"name": "{pre}07_the_mentor_comes_down", "do": [["clear_spawns"], ["spot", Vector2(12, 14), 20], ["quest_count", "the_humming_token", 5], ["scene_at", "{descends}", "emote", 0.1]]},
		{"name": "{pre}08_the_mentor_at_the_marsh", "do": [["scene_at", "{descends}", "say", 1.4, "hum"]], "then": [["until_idle"], ["choose", "{mentor}", "hand_in", "the_humming_token"],
			["close_pages"], ["until_idle"], ["choose", "npc_mei_qing_marsh", "accept", "mei_qings_errand"], ["close_pages"]]},
		{"name": "{pre}09_mei_qing_at_the_watch_post", "if": "sect=jade", "cell": Vector2(6, 18), "wait": 40},
		{"do": [["give", "willow_moss", 5], ["give", "grey_hide", 3], ["flush"], ["choose", "npc_mei_qing_marsh", "hand_in", "mei_qings_errand"], ["close_pages"], ["until_idle"],
			["spot", Vector2(4, 18), 20], ["array_travel", "array_marsh", "{array}"], ["frames", 30]]},
		{"name": "{pre}10_on_the_way_a_spar_offered", "if": "sect=jade", "do": [["walk_to", "ja_pavilion_rooftops", "east"], ["scene_at", "yard_spar_jade", "say", 1.4, "One round"]],
			"then": [["until_quiet"]]},
		{"name": "{pre}11_on_the_way_elders_overheard", "if": "sect=jade", "do": [["walk_to", "ja_east_terrace", "east"], ["scene_at", "terrace_talk_jade", "say", 1.4, "shrine"]],
			"then": [["until_quiet"]]},
		{"name": "{pre}12_on_the_way_the_gardeners_favour", "if": "sect=jade", "do": [["walk_to", "ja_herb_terraces", "east"], ["scene_at", "gardener_favour_jade", "say", 1.4, "lotus"]],
			"then": [["until_quiet"], ["choose", "npc_jade_gardener", "accept", "tea_for_the_elder"], ["close_pages"]]},
		{"name": "{pre}10_on_the_way_a_spar_offered", "if": "sect=cloud", "do": [["walk_to", "cm_sword_court", "east"], ["scene_at", "court_spar_cloud", "say", 1.4, "poles"]],
			"then": [["until_quiet"]]},
		{"name": "{pre}11_on_the_way_the_gardeners_favour", "if": "sect=cloud", "do": [["walk_to", "cm_array_court", "east"], ["scene_at", "gardener_favour_cloud", "say", 1.4, "lotus"]],
			"then": [["until_quiet"], ["choose", "npc_cloud_gardener", "accept", "tea_for_the_elder"], ["close_pages"]]},
		{"name": "{pre}12_on_the_way_elders_overheard", "if": "sect=cloud", "do": [["scene_at", "array_court_talk_cloud", "say", 1.4, "shrine"]], "then": [["until_quiet"]]},
		{"name": "{pre}13_the_mentor_keys_his_array", "do": [["walk_to", "{peak}", "peak_path"], ["report_to", "{elder}"], ["scene_at", "{peak_scene}", "say", 1.2, "array"]],
			"then": [["until_idle"]]},
		{"name": "{pre}14_the_peaks_array", "do": [["spot", "{peak_cell}", 30], ["array_tap", "{peak_array}", "dialogue"], ["frames", 240]], "then": [["close_pages"], ["frames", 10]]}]}

	s["decision42_route"] = {"doc": "Decision 42: auto-path's steering in Lotus Ferry village, the whole room with the tour's new route (gold) and the old one (red), a close-up of its east side, and the body running the road to the east gate",
		"out": "redesign/feedback/combat/", "stage": [["new_game"], ["frames", 360], ["hud", "visible", false]], "rows": [
		{"name": "autopath_village_route", "room": "lf_village", "cell": Vector2(9, 18), "wait": 150, "take": [["route", "*", "autopath_village_frames", "east_gate"],
			["cut", "autopath_village_route_closeup", "autopath_village_route", Rect2i(660, 220, 500, 260), Vector2i(1000, 520)]], "then": [["hud", "visible", true]]}]}

	# E1, the room engine (docs/architecture/room_engine.md): every room it converted from the side view, at midday,
	# under the HUD at a spot that shows it, the world alone x2 there, and each room whole once.
	var e1_rows := []
	for v in E1_VIEWS:
		var dir := str(v[0]).get_base_dir()   # R2: a view under a folder (r2/) keeps its x2 copy and its room there too
		var pre := dir + "/" if dir != "" else ""
		var take := [["shot"], ["world", pre + "world/" + str(v[0]).get_file()]]
		if v[3]: take.append(["whole_room", pre + "rooms/" + str(v[1])])
		e1_rows.append({"name": str(v[0]), "room": v[1], "cell": v[2], "wait": 90, "take": take})
	s["room_engine"] = {"doc": "E1, the room engine: each room it converted from the side view under the HUD at a spot that shows it, the world alone x2 there, and every such room whole",
		"out": "architecture/room_engine/", "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360], ["keep_whole", true]], "rows": e1_rows}

	# E3, the NPC engine (docs/architecture/npc_engine.md): its first new people, Greyreed Hamlet's three villagers come
	# home once the well runs clean, each one spec placed and set to work by anchors.
	s["npc_engine"] = {"doc": "E3, the NPC engine: Greyreed Hamlet's square before the well runs clean and after, its three villagers home and at work (each worker up close), a word with one, and the square whole",
		"out": "architecture/npc_engine/", "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360], ["keep_whole", true]], "rows": [
		{"name": "01_hamlet_before", "room": "gh_hamlet_square", "cell": Vector2(15, 17), "wait": 120},
		{"do": [["quests_done", ["grey_roofs", "cleansing_the_well"]]]},
		{"name": "02_hamlet_home_again", "room": "gh_hamlet_square", "cell": Vector2(15, 17), "wait": 240},
		{"name": "03_washer_ying_wash", "take": [["worker", "*", "gh_hamlet_square", "npc_washer_ying", "tend"]]},
		{"name": "04_washer_ying_hang", "take": [["worker", "*", "gh_hamlet_square", "npc_washer_ying", "work_hang"]]},
		{"name": "05_fisher_gan_mend", "take": [["worker", "*", "gh_hamlet_square", "npc_fisher_gan", "work_mend"]]},
		{"name": "06_old_jiu_sweep", "take": [["worker", "*", "gh_hamlet_square", "npc_old_jiu", "work_sweep"]]},
		{"name": "07_talk_washer_ying", "room": "gh_hamlet_square", "cell": Vector2(11, 20), "wait": 60, "do": [["talk", "npc_washer_ying"], ["frames", 40], ["dialogue_end"], ["frames", 4]],
			"then": [["close_pages"], ["frames", 10]]},
		{"name": "08_hamlet_whole", "room": "gh_hamlet_square", "cell": Vector2(15, 17), "wait": 120, "take": [["whole_room", "rooms/gh_hamlet_square"]]}]}

	# T1 (docs/architecture/topdown_mechanics.md): the side view's traversal on the grid, played in the rooms that need
	# it: a raft carrying the body over the Grey Pools and the hermit's pond, the vine up to the Falls Pool's spray ledge,
	# a glide from it over the falls' spray, the spray lifting a glider, the rope up the falls ledge.
	var on_the_ledge := Vector2(-1, 1).normalized()
	s["traversal"] = {"doc": "T1: the side view's traversal on the grid: rafts, the vine and the rope, the glide and the falls' updraft, flight",
		"out": "architecture/topdown_mechanics/", "stage": [["hour", 0.375], ["weather", "clear"], ["new_game"], ["frames", 360],
			["keep_whole", true], ["set", "cultivator.realm_key", "qi_kindling_9"], ["unlocks_evaluate"], ["refresh"], ["qi_full"],
			["secret_art", "falling_leaf_glide"]], "rows": [
		{"name": "01_raft_grey_pools", "room": "rm_grey_pools", "cell": Vector2(19, 21), "wait": 60, "do": [["on_raft", "log_raft_a"], ["frames", 150]],
			"take": [["shot"], ["world", "world/01_raft_grey_pools"]]},
		{"name": "02_raft_hermit_pond", "room": "rm_hermit_stilt_house", "cell": Vector2(12, 7), "wait": 60, "do": [["on_raft", "pond_raft"], ["frames", 150]],
			"take": [["world", "world/02_raft_hermit_pond"]]},
		{"name": "03_vine_climb", "room": "cf_falls_pool", "cell": Vector2(34, 8), "wait": 60, "do": [["move", Vector2.UP], ["frames", 48], ["stop"], ["frames", 4]],
			"take": [["world", "world/03_vine_climb"]], "then": [["move", Vector2.UP], ["frames", 90], ["stop"]]},
		{"name": "04_glide_over_the_spray", "room": "cf_falls_pool", "cell": Vector2(30, 6), "wait": 60,
			"do": [["qi_full"], ["face", on_the_ledge], ["move", on_the_ledge], ["frames", 2], ["jump"], ["hold_jump", true], ["frames", 34]],
			"take": [["world", "world/04_glide_over_the_spray"]], "then": [["frames", 90], ["hold_jump", false], ["stop"], ["frames", 60]]},
		{"name": "05_updraft_lifts", "room": "cf_falls_pool", "cell": Vector2(25, 11), "wait": 60,
			"do": [["qi_full"], ["face", Vector2.RIGHT], ["move", Vector2(1, -0.4).normalized()], ["frames", 2], ["jump"], ["hold_jump", true], ["frames", 44]],
			"take": [["world", "world/05_updraft_lifts"]], "then": [["hold_jump", false], ["stop"], ["frames", 90]]},
		{"name": "06_rope_falls_ledge", "room": "cf_falls_pool", "cell": Vector2(14, 7), "wait": 60, "do": [["move", Vector2.LEFT], ["frames", 44], ["stop"], ["frames", 4]],
			"take": [["world", "world/06_rope_falls_ledge"]], "then": [["move", Vector2.LEFT], ["frames", 90], ["stop"]]},
		{"name": "07_falls_pool_whole", "room": "cf_falls_pool", "cell": Vector2(36, 8), "wait": 60, "take": [["whole_room", "rooms/cf_falls_pool"]]},
		{"name": "08_flight_over_the_shore", "room": "cf_falls_pool", "cell": Vector2(45, 22), "wait": 60,
			"do": [["set", "cultivator.realm_key", "cloud_stride_1"], ["unlock", ["flight"]], ["refresh"], ["qi_full"], ["face", Vector2.DOWN],
				["jump"], ["hold_jump", true], ["frames", 60], ["hold_jump", false], ["frames", 2], ["move", Vector2.RIGHT], ["frames", 20], ["stop"], ["frames", 2]],
			"take": [["world", "world/08_flight_over_the_shore"]], "then": [["submit", {"type": "stop_flight", "reason": "landed"}], ["frames", 90]]}]}

	var weave_foes := [["wild_boarlet", Vector2(46, 12)], ["mudshell_crab", Vector2(54, -22)]]
	s["decision42"] = {"doc": "Decision 42: the weave (basic attack, technique, basic attack, each cutting the last one's recovery) frame by frame for the bare hands and the jian; the sprint and the light touch's walk as strips",
		"out": "redesign/feedback/combat/", "stage": [["proto"], ["hud", "visible", false]], "rows": [
		{"name": "weave_fists", "do": [["gear", "weapon", null, 900], ["refresh"], ["arena", BASE, weave_foes], ["sturdy"], ["cooldowns_clear"], ["qi_full"], ["fresh_chain"],
			["face", Vector2(1, 0.2)]], "take": [["weave"]]},
		{"name": "weave_jian", "do": [["gear", "weapon", "training_jian", 900], ["refresh"], ["arena", BASE, weave_foes], ["sturdy"], ["cooldowns_clear"], ["qi_full"],
			["fresh_chain"], ["face", Vector2(1, 0.2)]], "take": [["weave"]]},
		{"name": "sprint_strip", "do": [["gear", "weapon", null], ["refresh"], ["arena", BASE + Vector2(-140, -40), []]], "take": [["strip", "*", Vector2.RIGHT, 48, [], [], [0, 12, 24, 36, 48]]]},
		{"name": "walk_light_touch_strip", "do": [["arena", BASE + Vector2(-140, -40), []]], "take": [["strip", "*", Vector2(0.5, 0), 48, [], [], [0, 12, 24, 36, 48]]],
			"then": [["hud", "visible", true]]}]}
	return s

## The lineups of the monsters' review: [def, offset from SPOT in cells, elite].
const MONSTER_LINEUP := [["old_snapper", Vector2(-8.5, -3.5), false], ["trial_puppet", Vector2(-4.0, -3.5), false],
	["mossback_toad", Vector2(-0.5, -3.5), false], ["reed_otter", Vector2(3.0, -3.5), false], ["hollowed_boarlet", Vector2(7.0, -3.5), false],
	["mudshell_crab", Vector2(-8.0, 0.5), false], ["reedtail_rat", Vector2(-5.0, 0.5), false], ["wild_boarlet", Vector2(3.0, 0.5), false],
	["reed_frog", Vector2(6.0, 0.5), false], ["marsh_leech", Vector2(8.5, 0.5), false], ["hollow_minnow", Vector2(-2.5, 0.5), false]]
const MONSTER_ELITES := [["wild_boarlet", Vector2(-7.0, -2.0), false], ["wild_boarlet", Vector2(-4.0, -2.0), true],
	["reed_frog", Vector2(-0.5, -2.0), false], ["reed_frog", Vector2(2.0, -2.0), true],
	["mudshell_crab", Vector2(5.0, -2.0), false], ["mudshell_crab", Vector2(8.0, -2.0), true],
	["mossback_toad", Vector2(-7.0, 1.5), false], ["mossback_toad", Vector2(-4.0, 1.5), true],
	["reedtail_rat", Vector2(3.0, 1.5), false], ["reedtail_rat", Vector2(5.5, 1.5), true], ["marsh_leech", Vector2(8.0, 1.5), true]]
## Audit 45 (E2): the new species beside drawn ones for scale, and their elites beside them.
const E2_LINEUP := [["rock_beetle", Vector2(-7.0, -2.5), false], ["pebble_imp", Vector2(-3.0, -2.5), false],
	["greyfin", Vector2(1.5, -2.5), false], ["reedtail_rat", Vector2(6.0, -2.5), false],
	["mudshell_crab", Vector2(-7.0, 1.5), false], ["wild_boarlet", Vector2(6.0, 1.5), false]]
const E2_ELITES := [["rock_beetle", Vector2(-7.0, -2.0), false], ["rock_beetle", Vector2(-3.5, -2.0), true],
	["greyfin", Vector2(1.0, -2.0), false], ["greyfin", Vector2(5.5, -2.0), true], ["pebble_imp", Vector2(-5.0, 2.0), false]]
const POLISH_LINEUP := [["wild_boarlet", Vector2(-4.5, -2.2), false], ["hollowed_boarlet", Vector2(-1.5, -2.2), false],
	["wild_boarlet", Vector2(1.5, -2.2), true], ["reedtail_rat", Vector2(4.5, -2.2), false],
	["reed_otter", Vector2(-4.5, 1.0), false], ["mossback_toad", Vector2(-1.5, 1.0), false], ["mudshell_crab", Vector2(1.5, 1.0), false],
	["marsh_leech", Vector2(3.4, 1.0), false], ["marsh_leech", Vector2(5.2, 1.0), true]]
# M1: the monster engine's first batch, by kind, beside drawn foes for scale (the reed rat, the rock beetle, the boarlet,
# the mud crab), and their elites beside them.
# The mole stands past its aggro range from the player (200 px, over six tiles): one that took the player for prey would
# burrow toward it before the lineup is held, and a burrowing foe is not drawn.
const M1_LINEUP_A := [["stone_tortoise", Vector2(-7.5, -2.6), false], ["bamboo_monkey", Vector2(-3.0, -2.6), false],
	["reedtail_rat", Vector2(2.5, -2.6), false], ["thornback_boar", Vector2(7.0, -2.6), false],
	["ironclaw_mole", Vector2(-7.5, 2.0), false], ["green_viper", Vector2(-3.5, 2.0), false], ["rock_beetle", Vector2(2.5, 2.0), false],
	["wild_boarlet", Vector2(7.0, 2.0), false]]
const M1_LINEUP_B := [["jade_carp", Vector2(-7.5, -2.6), false], ["tide_crab", Vector2(-3.0, -2.6), false],
	["ember_fox", Vector2(2.5, -2.6), false], ["mud_hound", Vector2(7.0, -2.6), false],
	["stone_guardian", Vector2(-7.5, 2.2), false], ["jade_crane_chick", Vector2(-3.0, 2.2), false],
	["paper_talisman_ghost", Vector2(2.5, 2.2), false], ["mudshell_crab", Vector2(7.0, 2.2), false]]
const M1_LINEUP_C := [["mudwater_bandit", Vector2(-7.5, -2.6), false], ["bandit_archer", Vector2(-4.0, -2.6), false],
	["mudwater_lieutenant", Vector2(3.0, -2.6), false], ["big_toad_tan", Vector2(7.0, -2.6), false],
	["drowned_acolyte", Vector2(-7.5, 2.2), false], ["rogue_cultivator", Vector2(-4.0, 2.2), false],
	["drowned_abbot", Vector2(3.0, 2.2), false], ["gorge_bandit_adept", Vector2(7.0, 2.2), false]]
const M1_ELITES_A := [["ironclaw_mole", Vector2(-7.5, -2.4), false], ["stone_tortoise", Vector2(-3.0, -2.4), false],
	["stone_tortoise", Vector2(2.5, -2.4), true], ["ironclaw_mole", Vector2(7.0, -2.4), true],
	["bamboo_monkey", Vector2(-7.5, 2.0), false], ["bamboo_monkey", Vector2(-4.0, 2.0), true],
	["green_viper", Vector2(2.5, 2.0), false], ["green_viper", Vector2(6.5, 2.0), true]]
const M1_ELITES_B := [["thornback_boar", Vector2(-7.5, -2.4), false], ["thornback_boar", Vector2(-2.5, -2.4), true],
	["jade_carp", Vector2(3.0, -2.4), false], ["jade_carp", Vector2(7.0, -2.4), true],
	["tide_crab", Vector2(-7.5, 2.2), true], ["mudwater_bandit", Vector2(-4.0, 2.2), false], ["mudwater_bandit", Vector2(3.0, 2.2), true],
	["rogue_cultivator", Vector2(7.0, 2.2), true]]

## The sand and snow sampler's paint (40 x 22 cells, the phone's view). West: meadow, a dirt path and a paved corner round
## a sand flat, its beach on the water and a jetty. East: a snow field on the meadow with a packed-snow path through it,
## granite and paving at its edges, and a rock shelf two levels up under snow on its east half, its face capped by the
## snow's lip.
const SAMPLER_PAINT := [
	"gggggggddggggggggggggrrrrrrrrrrrrrrrrrrr",
	"gggggggddgggggpppppggrrrrrrrnnnnnnnnnnnn",
	"gggggggddgggggpppppggrrrrrrnnnnnnnnnnnnn",
	"gggggggddggggapppppggrrrrrrrnnnnnnnnnnnn",
	"ggggggaddaagaaapppgggggggggggggggggggggg",
	"ggggaaaddaaaaaaappggggggggggggggggkkgggg",
	"gggaaaaaaaaaaaaaaggggggnnnnnnnnnnkkngggg",
	"ggaaaaaaaaaaaaaaaaggggnnnnnnnnnnnkknnggg",
	"ggaaaaaaaaaaaaaaaggggnnnnnnnnnnnnkknnggg",
	"gggaaaaaaaaaaaaaggggnnnnnnnnnnnnkknnnggg",
	"ggggaaaaaaaaaaaggggnnnnnnnnnnnnnkknnnggg",
	"gggggaaaaaaaaagggggnnnnnnnnnnnnkknnnnggg",
	"ggggaaaaaaaaaaagggggnnnnnnnnnnnkknnnssss",
	"gggaaaaaaaaaaaaagggppnnnnnnnnnkknnnnssss",
	"aaaaaaaaaaaaaaaaaaaapppnnnnnnkknnnnnssss",
	"aaaaaaaaaaaaaaaaaaaapppppnnnkknnnnggssss",
	"aaaaaaaaaaaawwaaaaaapppppggkkgggggggssss",
	"~~~~~~~~~~~~ww~~~~~~pppppgkkggggggggggss",
	"~~~~~~~~~~~~ww~~~~~~ppppgkkggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~pppgkkgggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~pppgkkgggggggggggggg",
	"~~~~~~~~~~~~~~~~~~~~ppggkkgggggggggggggg",
]
