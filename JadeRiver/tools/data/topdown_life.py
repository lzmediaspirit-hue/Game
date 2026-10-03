"""Decision 43, the living world (docs/redesign/art_bible.md §14.13; docs/roadmap_master_ui.md decision 43): what lives
in each room on the grid, for TopdownLife (scripts/topdown/topdown_life.gd) and TopdownWork (topdown_work.gd). Writes
data/topdown/life.json:

  loops     the work loops: at each work spot the steps (a character action, seconds, a cue for the view: dust off a
            broom, sparks off an anvil, chips off a block), the tool held, the weapon worn, the walk between spots;
  work      room -> NPC object id -> {loop, spots [[x, y, facing, steps?], ...]}: a villager's or a disciple's loop
            between work spots within LEASH tiles of their own spot (spots in cells, like the layouts' places);
  extras    room -> [{id, outfit, loop, spots}]: a few people with no part in the story at work where the room has
            a job and no one to do it (a fisherman on the bank, a sweeper in a court); they speak to no one;
  animals   room -> [[kind, x, y], ...]: the hens, cats and dogs that live there (the view keeps them near home);
  critters  area (the room's backdrop) -> kind -> how many at most in view (the wild ones: sparrows, butterflies,
            dragonflies, fish, frogs), and room -> overrides;
  hangings  room -> [[sprite, x, y], ...]: what hangs on an interior's back wall (art px); a window lets the sun in;
  vistas    room -> [{edge, kind, pad}]: the land past a room's edge the camera may show (also written into the
            layout by topdown_rooms.py, so TopdownRoom's camera knows it).

Two hooks keep this module's content out of the rooms' own lines (tools/data/topdown_rooms.py calls them as it builds):
`dress(lay)` adds FURNISH (an interior's furnishings, a station's props: art in tools/art/topdown/furnish.py) to a
layout before it is checked, and `extend(rid, d)` adds a room's `vista` to its layout file.

Checked as it is built (`build`, also run by topdown_rooms.py --check): every work spot stands on a floor a body can
stand on, at its NPC's height, within LEASH tiles of the NPC's own spot (so standing next to a worker the talk is always
in reach: the World authority's 110 units round the spot, 132 on the grid with the people drawn 1.2 times bigger), and
every leg between spots is walked on that floor with nothing in the way; every extra's and animal's spot is standable;
every loop's action is one the figures play.
Deterministic: `python3 tools/data/topdown_life.py` writes the file, `--check` proves it current (tools/data/README.md).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import DATA, ROOT, emit, fail, read, run_cli  # noqa: E402
sys.path.append(os.path.abspath(os.path.join(HERE, "..")))
from lib.pix import h01  # noqa: E402  the pixel library's coordinate hash (tools/lib/pix.py)

OUT = os.path.join(ROOT, "data", "topdown", "life.json")
LAYOUTS = os.path.join(ROOT, "data", "topdown")

# A work spot's reach round its NPC's own spot, in tiles: the talk reaches 110 units (3.4 tiles; 132 on the grid)
# round the spot, so a player standing beside the worker (a tile off) is always in reach.
LEASH = 2.5

# ==================================================================================================================
# The work loops. `at`: the steps at a work spot, [action, seconds, cue?, frame held?]; a spot may name its own steps
# (`steps`, by key). `walk`: the pose between spots and its speed (world units a second); `weapon`: worn for the loop (a
# disciple's training sword).
# Decision 44: the work is drawn. Each step plays one of the figure's work actions (figure/work.py: the broom's sweep,
# the axe's chop, the hammer at the anvil...) for a whole number of its cycles, so a blow lands on its contact frame on
# every cycle (the view's `work_chop_hit` and `work_hammer_hit`); a rest step holds its action's first frame, the tool
# still in hand (the 4th element). `tools`: the tools the figure holds (the `tool` layer set, each drawn only in the
# actions that hold it: the broom, the rod, the axe and the herb basket are carried in the idle and walk poses too);
# `load`: carried on the shoulder between the spots (in `work_carry`) and set down beside them at a spot (the pole's
# baskets, the washing's basket); `pause`: "hold" keeps the work pose's rest frame when the player stops them (the tool
# in hand), else they stand idle.
# ==================================================================================================================
LOOPS = {
    "sweep": {"at": [["work_sweep", 3.0, "sweep"], ["idle", 0.8]], "walk": "walk", "speed": 26, "tools": ["broom"]},
    "carry": {"at": [["tend", 1.5, "set_down"], ["idle", 1.0]], "walk": "work_carry", "speed": 40, "tools": ["pole"],
              "load": "pole"},
    "laundry": {"steps": {"wash": [["tend", 4.0, "scrub"], ["idle", 0.6]],
                          "hang": [["work_hang", 1.0, "hang"], ["idle", 0.5], ["work_hang", 1.0, "hang"]]},
                "at": [["idle", 1.0]], "walk": "work_carry", "speed": 38, "tools": ["washing"], "load": "basket"},
    "fists": {"at": [["punch_1", 0.45], ["punch_2", 0.45], ["punch_3", 0.6], ["guard", 0.9], ["punch_1", 0.45], ["punch_3", 0.6],
                     ["salute", 1.3], ["idle", 0.8]], "walk": "walk", "speed": 48},
    "sword": {"at": [["swing_1", 0.5], ["swing_2", 0.5], ["thrust_1", 0.55], ["swing_3", 0.75], ["guard", 0.8], ["salute", 1.3],
                     ["idle", 0.6]], "walk": "walk", "speed": 48, "weapon": "sword"},
    "staff": {"at": [["thrust_1", 0.55], ["thrust_2", 0.55], ["thrust_3", 0.7], ["guard", 0.9], ["salute", 1.2], ["idle", 0.6]],
              "walk": "walk", "speed": 48, "weapon": "staff"},
    "spear": {"at": [["thrust_1", 0.55], ["thrust_3", 0.7], ["thrust_2", 0.55], ["guard", 1.0], ["idle", 1.0]], "walk": "walk",
              "speed": 44, "weapon": "spear"},
    "herbs": {"at": [["work_pick", 3.6, "pick"], ["idle", 0.8]], "walk": "walk", "speed": 34, "tools": ["herbs"]},
    "cook": {"at": [["work_stir", 1.6, "stir"], ["work_stir", 1.6, "stir"], ["work_stir", 1.2, "", 0]], "walk": "walk", "speed": 36,
             "tools": ["ladle"], "pause": "hold"},
    "grind": {"steps": {"cook": [["work_stir", 1.6, "stir"], ["work_stir", 1.6, "stir"], ["work_stir", 0.8, "", 0]],
                        "grind": [["work_grind", 3.2, "grind"], ["work_grind", 0.6, "", 0]]},
              "at": [["idle", 2.0]], "walk": "walk", "speed": 30, "tools": ["ladle", "pestle"], "pause": "hold"},
    "chop": {"at": [["work_chop", 1.0, "chop"], ["work_chop", 1.0, "chop"], ["idle", 1.4]], "walk": "walk", "speed": 40,
             "tools": ["axe"]},
    "hammer": {"steps": {"anvil": [["work_hammer", 1.0, "hammer"], ["work_hammer", 1.0, "hammer"], ["work_hammer", 1.0, "hammer"],
                                   ["work_hammer", 1.0, "", 0]],
                         "forge": [["tend", 2.5, "stoke"], ["idle", 0.8]]},
               "at": [["idle", 1.5]], "walk": "walk", "speed": 40, "tools": ["hammer"], "pause": "hold"},
    "fish": {"at": [["work_rod", 6.0, "fish"], ["work_cast", 1.0, "recast"]], "walk": "walk", "speed": 36, "tools": ["rod"]},
    "mend": {"at": [["work_mend", 4.0, "mend"], ["work_mend", 1.2, "", 0]], "walk": "walk", "speed": 34, "tools": ["net"],
             "pause": "hold"},
    "watch": {"at": [["idle", 3.2, "look"], ["idle", 1.0]], "walk": "walk", "speed": 32},
    "play": {"at": [["startle", 0.5], ["idle", 0.9]], "walk": "run", "speed": 92},
    "read": {"at": [["idle", 2.6], ["point", 1.2], ["idle", 1.6]], "walk": "walk", "speed": 32},
    "sell": {"at": [["point", 1.0], ["idle", 2.2], ["salute", 1.2], ["idle", 2.0]], "walk": "walk", "speed": 34},
    "pray": {"at": [["salute", 1.6], ["idle", 2.4]], "walk": "walk", "speed": 30},
    "write": {"at": [["brush_write", 1.4, "write"], ["idle", 1.2]], "walk": "walk", "speed": 30, "weapon": "brush"},
    "meditate": {"at": [["meditate", 14.0, "breathe"]], "walk": "walk", "speed": 30},
}
# The loads a carrier sets down at a spot (TopdownLife.draw_tool_down).
LOADS = ["pole", "basket"]
# The cues a step can give the view (dust, splashes, sparks, chips, steam, a float's bob) and the sounds they raise.
CUES = ["sweep", "set_down", "scrub", "hang", "pick", "stir", "grind", "chop", "hammer", "stoke", "fish", "recast", "mend",
        "look", "write", "breathe"]

# ==================================================================================================================
# The rooms. A spot is [x, y, facing, steps key?] in cells (fractions allowed); "auto": n picks n spots round the NPC
# on its own floor by a hash of the room and the NPC (see auto_spots). Facing: n, ne, e, se, s, sw, w, nw.
# A smith's "anvil" spot stands the room's anvil (the Forge place) a tile east of the feet and 0.4 of a tile south, in
# front: the hammer's pose (figure/work.py BAR_AT) meets its hot ingot there (check_work holds every smith to it).
# ==================================================================================================================
WORK = {
    "lf_village": {
        "npc_aunt_ping_lane": {"loop": "sweep", "spots": [[11, 17, "w"], [9.2, 17.6, "w"], [12.6, 18.3, "sw"]]},
        "npc_washer_mei": {"loop": "laundry", "spots": [[14.1, 33.2, "e", "wash"], [12.0, 30.4, "nw", "hang"]]},
        "npc_uncle_guo": {"loop": "fists", "spots": [[30, 22, "se"], [31.6, 23.3, "s"], [28.8, 23.4, "e"]]},
        "npc_little_dou": {"loop": "play", "spots": [[44, 24, "s"], [45.8, 25.4, "se"], [42.6, 25.6, "sw"], [44.8, 26.2, "s"]]},
        "npc_shen_lian_npc": {"loop": "carry", "spots": [[52, 27, "e"], [54.2, 26.2, "ne"], [50.2, 26.4, "w"]]},
        "npc_fisher_wen": {"loop": "mend", "spots": [[64.4, 27.2, "ne"], [66.2, 27.6, "n"]]},
        "npc_lu_boatman": {"loop": "watch", "spots": [[56, 28, "s"], [57.8, 28.8, "s"]]},
    },
    "lf_fishers_hut": {"npc_aunt_ping": {"loop": "cook", "spots": [[6, 6, "sw"], [5.2, 8.1, "w"]]}},
    "lf_granny_liu_hut": {"npc_granny_liu": {"loop": "grind", "spots": [[6, 6, "sw"], [4.3, 5.6, "w", "cook"], [4.2, 7.4, "w", "grind"]]}},
    "lf_old_ma_store": {"npc_old_ma": {"loop": "sell", "spots": [[12, 3, "s"], [13.5, 2.2, "n"], [10.8, 2.6, "s"]]}},
    "lf_lu_boat": {"npc_lu_boat": {"loop": "watch", "spots": [[10, 8, "s"], [8.2, 8.6, "s"], [11.8, 8.4, "se"]]}},
    "ja_weapon_hall": {
        "npc_jade_weapon_master": {"loop": "sword", "spots": [[10, 5, "s"], [11.8, 6.2, "s"], [8.4, 6.0, "se"]]},
        "npc_jade_smith": {"loop": "hammer", "spots": [[18.0, 6.6, "e", "anvil"], [18.9, 4.6, "ne", "forge"], [17, 5, "s"]]},
    },
    "cm_weapon_hall": {
        "npc_cloud_weapon_master": {"loop": "staff", "spots": [[10, 5, "s"], [11.8, 6.2, "s"], [8.4, 6.0, "se"]]},
        "npc_cloud_smith": {"loop": "hammer", "spots": [[18.0, 6.6, "e", "anvil"], [18.9, 4.6, "ne", "forge"], [17, 5, "s"]]},
    },
    "ja_gate_street": {
        "npc_jade_disciple_a": {"loop": "sweep", "spots": [[29, 15, "sw"], [27.4, 16.2, "w"], [30.8, 16.4, "s"]]},
        "npc_jade_disciple_b": {"loop": "sword", "spots": [[40, 17, "s"], [41.8, 17.6, "se"], [38.4, 18.2, "s"]]},
        "npc_jade_steward": {"loop": "pray", "spots": [[7, 16, "s"], [5.4, 14.8, "n"]]},
        "npc_jade_deacon": {"loop": "read", "spots": [[57, 15, "s"], [58.8, 14.2, "ne"]]},
    },
    "cm_cliff_stair": {
        "npc_cloud_disciple_a": {"loop": "sweep", "spots": [[22, 22, "sw"], [20.4, 23.0, "w"], [23.8, 23.2, "s"]]},
        "npc_cloud_steward": {"loop": "pray", "spots": [[7, 21, "s"], [8.4, 19.6, "n"]]},
        "npc_cloud_deacon": {"loop": "read", "spots": [[48, 22, "s"], [46.8, 21.0, "n"]]},
    },
    "cm_sword_court": {
        "npc_cloud_hall_master": {"loop": "staff", "auto": 2},
        "npc_arena_cm": {"loop": "watch", "auto": 2},
    },
    "ja_pavilion_rooftops": {
        "npc_jade_hall_master": {"loop": "fists", "auto": 2},
        "npc_jade_wm_yard": {"loop": "sword", "auto": 2},
    },
    "ja_east_terrace": {
        "npc_jade_formation_elder": {"loop": "read", "auto": 1},
        "npc_jade_physician": {"loop": "herbs", "auto": 2},
        "npc_arena_master": {"loop": "watch", "auto": 2},
    },
    "cm_array_court": {
        "npc_cloud_formation_elder": {"loop": "read", "auto": 1},
        "npc_cloud_physician": {"loop": "cook", "auto": 1},
        "npc_cloud_gardener": {"loop": "herbs", "auto": 2},
    },
    "ja_herb_terraces": {"npc_jade_gardener": {"loop": "herbs", "auto": 2}},
    "ja_elder_hu_peak": {"npc_elder_hu": {"loop": "meditate", "spots": [[24, 13, "s"]]}},
    "cm_elder_sung_peak": {"npc_elder_sung": {"loop": "meditate", "spots": [[31, 5, "s"]]}},
    "sf_gate": {
        "npc_guard_hou": {"loop": "spear", "auto": 2},
        "npc_foreman_dong": {"loop": "carry", "auto": 2},
        "npc_adventurer_kai": {"loop": "sword", "auto": 1},
    },
    "sf_market": {
        "npc_storekeeper_fang": {"loop": "sell", "auto": 1},
        "npc_auntie_rong": {"loop": "cook", "auto": 1},
        "npc_keeper_shi": {"loop": "sell", "auto": 1},
        "npc_courier_lin": {"loop": "carry", "auto": 2},
        "npc_tailor_xun": {"loop": "sell", "auto": 1},
        "npc_adventurer_su": {"loop": "watch", "auto": 2},
    },
    "sf_artisan_row": {
        "npc_smith_bao": {"loop": "hammer", "spots": [[15.0, 12.6, "e", "anvil"], [13, 13, "s"]]},
        "npc_apprentice_tao": {"loop": "carry", "auto": 2},
        "npc_old_scribe_bai": {"loop": "write", "auto": 1},
        "npc_tinkerer_yu": {"loop": "mend", "auto": 1},
    },
    "sf_fairground": {
        "npc_fair_vendor_he": {"loop": "sell", "auto": 1},
        "npc_adventurer_rui": {"loop": "watch", "auto": 2},
    },
    "rm_marsh_edge": {
        "npc_watcher_bo": {"loop": "watch", "auto": 2},
        "npc_watcher_su": {"loop": "watch", "auto": 2},
    },
    # R3: Mei Qing at her drawers, the librarians and the magistrate at their desks, the foreman over his crews.
    "ja_alchemy_hall": {"npc_mei_qing_sect": {"loop": "cook", "auto": 1}},
    "ja_library": {"npc_jade_librarian": {"loop": "write", "auto": 1}},
    "cm_cloud_library": {"npc_cloud_librarian": {"loop": "write", "auto": 1}},
    "sf_county_hall": {"npc_magistrate_qian": {"loop": "read", "auto": 1}},
    "sq_quarry_rim": {"npc_dong_rim": {"loop": "watch", "auto": 2}},
}

# People at work with no part in the story. Outfits are parts of the figures' catalogue (parts.json names).
VILLAGER = {"body": "light", "hair": "short_knot", "hair_color": 0, "shirt": "vneck", "pants": "cuffed", "shoes": "folded",
            "hat": "straw", "cape": "none", "weapon": "none", "shirt_dye": "earth"}
EXTRAS = {
    "lf_village": [
        {"id": "x_bank_fisher", "outfit": dict(VILLAGER, hair_color=5, shirt_dye="grey"), "loop": "fish", "spots": [[38.5, 33.25, "s"]]},
        {"id": "x_woodcutter", "outfit": dict(VILLAGER, hat="none", shirt="sleeveless", shirt_dye="ochre", pants="loose"),
         "loop": "chop", "spots": [[65.1, 18.3, "w"]]},
    ],
    "ja_gate_street": [
        {"id": "x_ja_sweeper", "outfit": {"body": "light", "hair": "ponytail", "hair_color": 3, "shirt": "disciple", "pants": "martial",
                                          "shoes": "boots", "hat": "none", "cape": "none", "weapon": "none", "shirt_dye": "jade",
                                          "pants_dye": "jade"},
         "loop": "sweep", "spots": [[47, 19.5, "w"], [45.4, 20.2, "w"], [48.6, 20.6, "sw"]]},
    ],
    "cm_sword_court": [
        {"id": "x_cm_pupil", "outfit": {"body": "light", "hair": "high_pony", "hair_color": 0, "shirt": "disciple", "pants": "martial",
                                        "shoes": "boots", "hat": "none", "cape": "none", "weapon": "sword", "shirt_dye": "cloud",
                                        "pants_dye": "cloud"},
         "loop": "sword", "spots": [[24, 15, "s"], [26, 15.6, "s"]]},
    ],
    "rm_marsh_edge": [
        {"id": "x_marsh_fisher", "outfit": dict(VILLAGER, shirt_dye="indigo"), "loop": "fish", "spots": [[33.4, 22.3, "s"]]},
    ],
}

# The animals that live in a room: [kind, x, y] in cells; the view keeps each near home.
ANIMALS = {
    "lf_village": [["hen", 44.6, 26.9], ["hen_brown", 46.9, 25.3], ["hen", 43.3, 27.5], ["cat", 5.0, 16.4], ["dog", 61.6, 27.2]],
    "lf_village_night": [["cat", 5.0, 16.4]],
    "lf_granny_liu_hut": [["cat", 12.4, 6.6]],
    "sf_market": [["dog", 36.5, 15.4], ["hen", 4.5, 16.5], ["hen_brown", 3.2, 17.3]],
    "sf_gate": [["dog", 33.5, 12.6]],
    "sf_artisan_row": [["cat", 23.5, 14.4]],
    "sf_fairground": [["dog", 26.5, 16.6]],
    "wp_east": [["hen", 26.5, 10.2], ["hen_brown", 28.2, 9.4]],
    "cm_cliff_stair": [["cat", 35.4, 18.6]],
}

# The wild critters: area (the room's backdrop) -> kind -> how many at most in view. Sparrows come in flocks (the
# number is flocks); butterflies keep to flowers, dragonflies and fish to water, frogs to the marsh's wet edge.
CRITTERS = {
    "valley_day": {"sparrow": 2, "butterfly": 4, "dragonfly": 3, "fish": 4, "frog": 1},
    "marsh": {"sparrow": 1, "butterfly": 2, "dragonfly": 4, "fish": 3, "frog": 5},
    "sect_jade": {"sparrow": 2, "butterfly": 4, "dragonfly": 2, "fish": 3},
    "sect_cloud": {"sparrow": 1, "butterfly": 3, "fish": 2},
    "mist_peak": {"sparrow": 1, "butterfly": 3, "fish": 2},
    "valley_dusk": {"fish": 4, "dragonfly": 1},
    "valley_night": {"fish": 2, "frog": 3},
    "interior": {},
    "cave": {"fish": 1},
    "": {"sparrow": 1, "butterfly": 2, "fish": 2},
}
# By day only (the clock's morning, day and evening): these sleep at night.
DAY_ONLY = ["sparrow", "butterfly", "dragonfly"]

# ==================================================================================================================
# Interiors and stations: props added to a layout (tools/art/topdown/furnish.py), (kind, x, y) each; a prop may stand
# on any floor, never on a kept-clear cell, a stair, the water or another prop.
# ==================================================================================================================
FURNISH = {
    "lf_village": [("laundry_line", 10, 29), ("wash_tub", 15, 33), ("net_rack", 65, 26), ("fish_basket", 54, 25),
                   ("woodpile", 62, 17), ("chop_block", 64, 18)],
    "lf_fishers_hut": [("stove", 3, 8), ("bed", 15, 10), ("water_jar", 7, 1), ("fish_basket", 12, 8), ("sacks", 17, 7)],
    "lf_granny_liu_hut": [("cabinet", 8, 1), ("drying_rack", 10, 1), ("stove", 2, 5), ("bed", 13, 9),
                          ("herb_baskets", 11, 7)],
    "lf_old_ma_store": [("cabinet", 8, 1), ("cabinet", 13, 1), ("sacks", 15, 7), ("sacks", 14, 9), ("cloth_bolts", 15, 5),
                        ("water_jar", 1, 5)],
    "ja_weapon_hall": [("forge", 19, 3), ("water_jar", 21, 4), ("mat", 13, 9)],
    "cm_weapon_hall": [("forge", 19, 3), ("water_jar", 21, 4), ("mat", 13, 9)],
    "ja_herb_terraces": [("herb_baskets", 23, 22), ("drying_rack", 13, 22)],
    "sf_market": [("sacks", 10, 15), ("fish_basket", 23, 16)],
    "sf_artisan_row": [("woodpile", 5, 15), ("chop_block", 8, 16)],
}

# What hangs on an interior's back wall: [sprite, x, y] in art px (y on the wall's face, which runs from -32 to 16 over
# the first floor row). A window lets the sun in: a shaft of light falls from it across the floor.
HANGINGS = {
    "lf_fishers_hut": [["window", 56, -22], ["nets", 84, -20], ["window", 136, -22], ["drying_fish", 176, -24]],
    "lf_granny_liu_hut": [["window", 190, -22], ["herbs", 120, -26], ["scroll", 230, -24], ["herbs", 248, -26]],
    "lf_old_ma_store": [["window", 104, -22], ["plaque", 180, -28], ["window", 236, -22]],
    "ja_weapon_hall": [["plaque", 176, -28], ["window", 300, -22], ["scroll", 214, -22], ["ribbon_banner", 150, -26],
                       ["window", 40, -22]],
    "cm_weapon_hall": [["plaque", 176, -28], ["window", 300, -22], ["scroll", 214, -22], ["window", 40, -22]],
    # R3: the sects' halls, Stoneford's County Hall and Trial Tower (their walls four or five levels high: the face
    # runs from -48, or -64, to 16).
    "ja_alchemy_hall": [["plaque", 196, -42], ["window", 180, -26], ["window", 216, -26], ["herbs", 278, -36],
                        ["herbs", 310, -36], ["scroll", 372, -30]],
    "ja_library": [["scroll", 276, -40], ["window", 304, -34], ["plaque", 348, -56], ["window", 392, -34]],
    "ja_retreat": [["window", 56, -26], ["plaque", 212, -40], ["scroll", 196, -30], ["scroll", 236, -30],
                   ["window", 304, -26], ["herbs", 78, -34]],
    "cm_cloud_library": [["window", 36, -34], ["plaque", 78, -56], ["window", 120, -34], ["scroll", 264, -40]],
    "cm_retreat": [["window", 116, -26], ["plaque", 212, -40], ["scroll", 196, -30], ["scroll", 236, -30],
                   ["window", 360, -26], ["herbs", 382, -34]],
    "sf_county_hall": [["window", 20, -26], ["plaque", 44, -40], ["window", 100, -26], ["plaque", 180, -42],
                       ["scroll", 166, -30], ["scroll", 210, -30]],
    "sf_trial_tower": [["window", 136, -26], ["window", 192, -26], ["plaque", 324, -42], ["ribbon_banner", 306, -30],
                       ["ribbon_banner", 348, -30], ["window", 456, -26], ["window", 512, -26]],
}

# The land past a room's edge (TopdownVista): edge n/s/e/w, the kind drawn there, and how far past the edge (art px)
# the camera may show it. `drop` kinds fall away under a cliff face; the others rise behind the room's north edge.
VISTAS = {
    "lf_village": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 40}],
    "lf_village_night": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 40}],
    "lf_reed_shallows": [{"edge": "n", "kind": "hills", "pad": 40}],
    "wp_east": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "wp_west": [{"edge": "n", "kind": "hills", "pad": 40}],
    "sf_gate": [{"edge": "s", "kind": "river", "pad": 32}],
    "sf_market": [{"edge": "s", "kind": "river", "pad": 32}],
    "sf_artisan_row": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "sf_fairground": [{"edge": "s", "kind": "river", "pad": 32}],
    "rm_marsh_edge": [{"edge": "n", "kind": "marsh", "pad": 40}],
    "ja_gate_street": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "ja_pavilion_rooftops": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "ja_east_terrace": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "ja_herb_terraces": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "ja_elder_hu_peak": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 88}],
    "cm_cliff_stair": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "cm_sword_court": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "cm_array_court": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "cm_elder_sung_peak": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 88}],
    "sf_trial_jade": [{"edge": "s", "kind": "cloud_sea", "pad": 64}],
    "sf_trial_cloud": [{"edge": "s", "kind": "cloud_sea", "pad": 64}],
    "lf_lu_boat": [{"edge": "all", "kind": "water", "pad": 0}],
    # E1's rooms (tools/content/rooms/specs/): the Caravan Road's hills and creek, the Bend's river, the stockade's hill.
    "cr_caravan_road": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "dw_bend_shore": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "mh_stockade": [{"edge": "n", "kind": "hills", "pad": 40}],
    # R3: the Cloud Sect's terraces over the cloud sea, the grove's hillside, the quarry's hills.
    "cm_herb_terraces": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 80}],
    "sf_beast_grove": [{"edge": "n", "kind": "hills", "pad": 40}],
    "sq_quarry_rim": [{"edge": "n", "kind": "hills", "pad": 40}],
    "sq_lower_pit": [{"edge": "n", "kind": "hills", "pad": 40}],
    # R1: the main story's path past chapter 3: the marsh's reeds and water, the grove's hills, the falls' and the
    # peak's mountains over the cloud sea.
    "rm_grey_pools": [{"edge": "n", "kind": "marsh", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "rm_sunken_causeway": [{"edge": "n", "kind": "marsh", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "rm_hermit_stilt_house": [{"edge": "n", "kind": "marsh", "pad": 40}],
    "gh_hamlet_square": [{"edge": "n", "kind": "marsh", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "bg_whispering_bamboo": [{"edge": "n", "kind": "hills", "pad": 40}],
    "bg_thicket_heart": [{"edge": "n", "kind": "hills", "pad": 40}],
    "cf_falls_pool": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "river", "pad": 32}],
    "cp_pilgrim_stairs": [{"edge": "n", "kind": "peaks", "pad": 56}],
    "cp_cleansing_summit": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 88}],
    # R2: the Serpent's Shallows' bank and river; Whitewater Gorge's peaks over its north wall and the river below it.
    "dw_serpents_shallows": [{"edge": "n", "kind": "hills", "pad": 40}, {"edge": "s", "kind": "river", "pad": 32}],
    "wg_gorge_mouth": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "river", "pad": 32}],
    "wg_rapids_terraces": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "river", "pad": 32}],
    "wg_echo_cliffs": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "river", "pad": 32}],
    # R6: Act II's first zones. Cloudgate Port's island falls away past its south rim into the sea of cloud, the airships
    # hanging over it at their berths; the Expanse's ranges behind its crags.
    "ae_landing": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 88}],
    "ae_port_market": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 104}],
    "ae_skydock": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 104}],
    "ae_shipyard": [{"edge": "n", "kind": "peaks", "pad": 56}, {"edge": "s", "kind": "cloud_sea", "pad": 104}],
}
DROPS = ["cloud_sea"]
EDGE_KINDS = ["hills", "river", "marsh", "peaks", "cloud_sea", "water"]


# ==================================================================================================================
# The hooks topdown_rooms.py calls.
# ==================================================================================================================
def dress(lay) -> None:
    """Add the room's furnishings and stations (FURNISH) to a layout before it is checked and written."""
    for kind, x, y in FURNISH.get(lay.id, []):
        lay.prop(kind, x, y)


def extend(rid: str, d: dict) -> None:
    """Add the room's vistas to its layout file (TopdownRoom reads `vista` for the camera's reach past the edge)."""
    if rid in VISTAS:
        d["vista"] = [dict(v) for v in VISTAS[rid]]


def check_furnish(rid: str, d: dict, g, clear: set) -> list:
    """The furnishings' rules: each inside the room on a floor (not the water or a stair), off every kept-clear cell (the
    spawn, a spot, a way's lane, a stair's head or foot) and off every other prop."""
    import topdown_rooms as TR
    errs = []
    kinds = {k for k, _, _ in FURNISH.get(rid, [])}
    taken = {}
    for p in d["props"]:
        fw, fh = TR.TILESET["props"][p["kind"]]["footprint"]
        for y in range(p["y"], p["y"] + fh):
            for x in range(p["x"], p["x"] + fw):
                taken.setdefault((x, y), []).append(p["kind"])
    for kind, x0, y0 in FURNISH.get(rid, []):
        fw, fh = TR.TILESET["props"][kind]["footprint"]
        for y in range(y0, y0 + fh):
            for x in range(x0, x0 + fw):
                where = "%s at %s" % (kind, str((x, y)))
                if not (0 <= x < g.w and 0 <= y < g.h):
                    errs.append(where + ": outside the room")
                    continue
                if g.lv[y][x] == TR.WATER or g.stair[y][x]:
                    errs.append(where + ": on the water or the stairs")
                if (x, y) in clear:
                    errs.append(where + ": on a kept-clear cell")
                if len(taken.get((x, y), [])) > 1:
                    errs.append(where + ": overlaps " + ", ".join(k for k in taken[(x, y)] if k != kind or kinds))
    return errs


# ==================================================================================================================
# Building life.json
# ==================================================================================================================
FACINGS = {"n": (0, -1), "ne": (1, -1), "e": (1, 0), "se": (1, 1), "s": (0, 1), "sw": (-1, 1), "w": (-1, 0), "nw": (-1, -1)}


def _seed(text: str) -> int:
    s = 0
    for ch in text:
        s = (s * 31 + ord(ch)) & 0xFFFF
    return s


def _floor(g, p):
    """The floor under a layout point (cells), in units, or None where nothing can stand."""
    import topdown_rooms as TR
    return g.floor(*TR.cell(p))


def walkable(g, a, b, floor) -> bool:
    """Every point along the leg a -> b (cells) stands on `floor` (within half a level's step) with nothing in the way,
    and a body's width either side of it too."""
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 6) + 1
    for k in range(n + 1):
        t = k / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for dx, dy in ((0, 0), (-0.22, 0), (0.22, 0), (0, -0.15), (0, 0.15)):
            f = _floor(g, (x + dx, y + dy))
            if f is None or abs(f - floor) > 8.0:
                return False
    return True


def blocked_cells(d: dict) -> set:
    """Cells a work spot keeps off: every other thing's spot (its ring), each way's lane."""
    import topdown_rooms as TR
    out = set()
    for p in d["portals"].values():
        for c in TR.portal_lane(p):
            out.add(c)
    return out


def auto_spots(rid: str, oid: str, d: dict, g, n: int) -> list:
    """`n` work spots round an NPC's spot on its own floor: cell centres within LEASH - 0.4 tiles, at least 1.4 tiles
    off, walked to in a straight line, off every way's lane and a tile clear of every other thing's spot; spread round
    the NPC by a hash of the room and the NPC (the first in the hashed direction, the next across from it). Each faces
    away from the NPC's spot, toward the room's middle row."""
    import topdown_rooms as TR
    home = d["place"][oid]
    floor = _floor(g, home)
    lanes = blocked_cells(d)
    others = [TR.cell(at) for k, at in d["place"].items() if k != oid]
    seed = _seed(rid + oid)
    cands = []
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            p = (round(home[0]) + dx, round(home[1]) + dy)
            dist = math.hypot(p[0] - home[0], p[1] - home[1])
            if dist < 1.4 or dist > LEASH - 0.4:
                continue
            c = TR.cell(p)
            if c in lanes or any(abs(c[0] - o[0]) <= 1 and abs(c[1] - o[1]) <= 1 for o in others):
                continue
            f = _floor(g, p)
            if f is None or abs(f - floor) > 8.0 or not walkable(g, home, p, floor):
                continue
            cands.append(p)
    if not cands:
        return []
    ang0 = h01(seed, 1, 7) * math.tau
    out = []
    for k in range(n):
        want = ang0 + k * math.tau / max(2, n)
        best = min(cands, key=lambda q: (abs(((math.atan2(q[1] - home[1], q[0] - home[0]) - want + math.pi) % math.tau) - math.pi),
                                         -math.hypot(q[0] - home[0], q[1] - home[1])))
        cands = [q for q in cands if q != best]
        out.append(best)
        if not cands:
            break
    spots = [[home[0], home[1], "s"]]
    mid_y = g.h / 2.0
    for q in out:
        fx, fy = q[0] - home[0], (mid_y - q[1]) * 0.2 + (q[1] - home[1])
        spots.append([q[0], q[1], _facing(fx, fy)])
    return spots


def _facing(dx: float, dy: float) -> str:
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return "s"
    ang = math.degrees(math.atan2(dy, dx))
    names = ["e", "se", "s", "sw", "w", "nw", "n", "ne"]
    return names[int(((ang + 22.5) % 360) // 45)]


def actions() -> set:
    man = read("character", LAYOUTS)
    return set(man["actions"]) | set(man.get("aliases", {}))


def check_work(errs: list) -> None:
    """Decision 44: every work step is drawn and held as the figure draws it. A work action's tool is among the loop's
    tools (the tool set's `actions`); a working step runs a whole number of its looping action's cycles, so its blow
    lands on the contact frame on every cycle; a rest step holds a frame the action has; a load is one the view sets
    down; `pause` is idle or hold."""
    man = read("character", LAYOUTS)
    path = os.path.join(LAYOUTS, "character", "tool.json")
    tools = read(path)["items"].get("tool", {}) if os.path.exists(path) else {}
    for name, lp in LOOPS.items():
        worn = lp.get("tools", [])
        for t in worn:
            if t not in tools:
                errs.append("loop %s: no tool %s drawn" % (name, t))
        if lp.get("load", "") not in [""] + LOADS:
            errs.append("loop %s: no load %s" % (name, lp.get("load")))
        if lp.get("pause", "idle") not in ("idle", "hold"):
            errs.append("loop %s: pause %s" % (name, lp.get("pause")))
        steps = list(lp.get("at", [])) + [st for v in lp.get("steps", {}).values() for st in v]
        steps.append([lp.get("walk", "walk"), 0.0])
        for st in steps:
            a = man["actions"].get(st[0])
            if a is None:
                continue
            if a.get("work") and not any(st[0] in tools.get(t, {}).get("actions", []) for t in worn):
                errs.append("loop %s: %s holds a tool the loop does not wear (%s)" % (name, st[0], worn))
            if len(st) > 3:
                if not 0 <= int(st[3]) < int(a["frames"]):
                    errs.append("loop %s: %s holds frame %s of %d" % (name, st[0], st[3], a["frames"]))
            elif a.get("work") and a["loop"] and float(st[1]) > 0.0:
                cycles = float(st[1]) * float(a["fps"]) / float(a["frames"])
                if abs(cycles - round(cycles)) > 1e-6 or round(cycles) < 1:
                    errs.append("loop %s: %s runs %.2f cycles (a whole number keeps its blows on the contact frame)"
                                % (name, st[0], cycles))


ANVIL_OFF = (1.0, 0.4)   # the room's anvil from a smith's "anvil" spot, in cells (figure/work.py BAR_AT)


def check_anvil(where: str, d: dict, side: dict, spots: list) -> list:
    """A smith's "anvil" spot faces e with the room's anvil (its forge_anvil) ANVIL_OFF from the feet, where the
    hammer's pose puts the hot bar on its face."""
    errs = []
    for s in spots:
        if len(s) < 4 or s[3] != "anvil":
            continue
        anvils = [oid for oid, o in side.items() if o.get("type") == "forge_anvil" and oid in d["place"]]
        if len(anvils) != 1:
            errs.append(where + ": %d anvils in the room" % len(anvils))
            continue
        ax, ay = d["place"][anvils[0]][:2]
        off = (float(ax) - float(s[0]), float(ay) - float(s[1]))
        if s[2] != "e" or abs(off[0] - ANVIL_OFF[0]) > 0.01 or abs(off[1] - ANVIL_OFF[1]) > 0.01:
            errs.append(where + ": the anvil at %s from the spot facing %s (the hammer wants %s facing e)"
                        % (str(off), s[2], str(ANVIL_OFF)))
    return errs


def room_side(rid: str) -> dict:
    return read(rid, os.path.join(DATA, "rooms"))


def build_rooms() -> tuple:
    """Every room's life: its work (spots expanded and checked), extras, animals, hangings and vistas; and the errors."""
    import topdown_rooms as TR
    errs = []
    acts = actions()
    for name, lp in LOOPS.items():
        steps = list(lp.get("at", []))
        for v in lp.get("steps", {}).values():
            steps += v
        for st in steps:
            if st[0] not in acts:
                errs.append("loop %s: no action %s" % (name, st[0]))
            if len(st) > 2 and st[2] != "" and st[2] not in CUES:
                errs.append("loop %s: no cue %s" % (name, st[2]))
        if lp.get("walk", "walk") not in acts:
            errs.append("loop %s: no walk %s" % (name, lp.get("walk")))
    check_work(errs)
    rooms = {}
    names = sorted(set(WORK) | set(EXTRAS) | set(ANIMALS) | set(HANGINGS) | set(VISTAS))
    for rid in names:
        path = os.path.join(LAYOUTS, rid + ".json")
        if not os.path.exists(path):
            errs.append("%s: no layout" % rid)
            continue
        d = read(path)
        g = TR.Grid(d)
        side = {o["id"]: o for o in room_side(rid).get("objects", [])}
        out = {}
        work = {}
        for oid, w in WORK.get(rid, {}).items():
            where = "%s %s" % (rid, oid)
            if oid not in d["place"] or side.get(oid, {}).get("type") != "npc":
                errs.append(where + ": not an NPC of the room")
                continue
            if w["loop"] not in LOOPS:
                errs.append(where + ": no loop " + w["loop"])
                continue
            spots = [list(s) for s in w["spots"]] if "spots" in w else auto_spots(rid, oid, d, g, int(w.get("auto", 2)))
            if not spots:
                errs.append(where + ": no work spot found")
                continue
            errs += check_spots(where, g, d["place"][oid], spots, LOOPS[w["loop"]])
            errs += check_anvil(where, d, side, spots)
            work[oid] = {"loop": w["loop"], "spots": spots}
        if work:
            out["work"] = work
        extras = []
        for e in EXTRAS.get(rid, []):
            where = "%s %s" % (rid, e["id"])
            if e["loop"] not in LOOPS:
                errs.append(where + ": no loop " + e["loop"])
            home = e["spots"][0]
            errs += check_spots(where, g, home, e["spots"], LOOPS.get(e["loop"], {}))
            extras.append(dict(e))
        if extras:
            out["extras"] = extras
        animals = []
        for kind, x, y in ANIMALS.get(rid, []):
            if _floor(g, (x, y)) is None:
                errs.append("%s: the %s at %s stands on nothing" % (rid, kind, str((x, y))))
            animals.append([kind, x, y])
        if animals:
            out["animals"] = animals
        if rid in HANGINGS:
            out["hangings"] = HANGINGS[rid]
        if rid in VISTAS:
            for v in VISTAS[rid]:
                if v["kind"] not in EDGE_KINDS:
                    errs.append("%s: no vista kind %s" % (rid, v["kind"]))
            out["vista"] = VISTAS[rid]
        rooms[rid] = out
    return rooms, errs


def check_spots(where: str, g, home, spots: list, loop: dict) -> list:
    """Each spot stands on its NPC's floor within LEASH tiles of its own spot, faces one of the eight rows, names steps
    its loop has; each leg (home to the first, then spot to spot and back round) is walked with nothing in the way."""
    errs = []
    floor = _floor(g, home)
    if floor is None:
        return [where + ": its own spot stands on nothing"]
    for s in spots:
        f = _floor(g, s)
        if f is None or abs(f - floor) > 8.0:
            errs.append("%s: spot %s is not on its floor" % (where, str(s[:2])))
        if math.hypot(s[0] - home[0], s[1] - home[1]) > LEASH + 1e-6:
            errs.append("%s: spot %s is %.2f tiles from its own, past the leash (%.1f)" % (where, str(s[:2]), math.hypot(s[0] - home[0], s[1] - home[1]), LEASH))
        if len(s) > 2 and s[2] not in FACINGS:
            errs.append("%s: spot %s faces %s" % (where, str(s[:2]), s[2]))
        if len(s) > 3 and s[3] not in loop.get("steps", {}):
            errs.append("%s: spot %s names steps %s its loop has not" % (where, str(s[:2]), s[3]))
    legs = [(home, spots[0])] + [(spots[i], spots[(i + 1) % len(spots)]) for i in range(len(spots))] if len(spots) > 1 else [(home, spots[0])]
    for a, b in legs:
        if not walkable(g, a, b, floor):
            errs.append("%s: the walk %s -> %s is blocked" % (where, str(a[:2]), str(b[:2])))
    return errs


def build() -> str:
    rooms, errs = build_rooms()
    fail("topdown_life", errs)
    body = {"schema_version": 1, "leash": LEASH, "loops": LOOPS, "cues": CUES, "critters": CRITTERS, "day_only": DAY_ONLY,
            "drops": DROPS, "rooms": rooms}
    emit(OUT, json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    return "life.json: %d rooms" % len(rooms)


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
