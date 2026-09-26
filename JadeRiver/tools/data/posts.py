"""V10 Keeping Post (docs/idle_gathering_design.md): idle gathering after IdleOn's AFK model, in Jade River's names.

posts.json holds every constant PostRules reads, the crafts, the node outputs (Toughness, EXP, level gate, pouch
category), the pouch tiers with their sewing costs, and the incense. items.py adds the tools, insects and incense
from here, world.py places the insect swarms, economy.py adds the tool recipes.
"""
from common import write

# --------------------------------------------------------------------------- rules (§3)
RULES = {
    "diligence": {"craft_base": 0.52, "martial_base": 0.40, "floor": 0.01},
    "finesse": {"flat": 12.0, "base_flat": 4.0, "tool_exp": 1.3, "stat_flat_exp": 0.6, "stat_mult_exp": 0.35, "per_level": 0.005},
    "yield": {"full_at": 10.0, "chance_exp": 0.4, "chance_min_r": 0.025, "abundance_exp": 0.25, "flow_cap": 0.10, "windfall_chain": 4},
    "swing": {"scale": 6.0, "base": 1.0, "per_speed": 0.2, "top_speed": 10},
    "xp": {"a": 15.0, "base": 1.225, "cut": 0.164, "k": 0.135, "k_off": 50.0, "minus": 30.0, "max_level": 200},
    "pouch": {"compartments": 4, "base_cap": 10, "hard_cap": 2050000000},
    "settle": {"max_days": 90, "night_share": 0.3333},
    "side_drops": {"foraging": {"item": "spirit_wood", "every": 20}},
    "fervour": {"bonus": 0.5, "hours": 24},
    # V10b the Vigil: IdleOn's kills-an-hour with Jade River's combat numbers. `pace` scales the fighter's cap to
    # Jade River's slower fights; a Vigil kill gives a quarter of a hunted kill's realm progress (S23 keeps realm
    # progress away slower than play); a fall costs 600 s.
    "vigil": {"pace": 0.35, "sweep_rate": 0.5, "down_s": 600, "foe_attack_s": 2.2, "qp_share": 0.25, "samples": 48,
              "loot_samples": 40, "k_per_technique": 0.12, "k_max": 2.2, "walk_speed": 205},
    # V10b Bestiary Leaves: one leaf in a thousand kills of a species (Vigil or hand); tiers at 1, 5, 25 and 100
    # leaves; each species gives one kind of bonus, by tier.
    # V10c: snares, rites. A snare catches only beasts its Finesse meets; above that, (Finesse / Toughness)^0.25 more.
    "snaring": {"radiant": 0.02, "recall_share": 0.5},
    "rites": {"charge_base": 6.0, "charge_floor": 0.57, "charge_top": 5.7, "speed_k": 0.2, "level_div": 40.0, "cap_base": 50.0,
              "cap_per_tier": 25.0, "min_charge": 10.0, "wisps_base": 5.0, "wave_log": 5.0, "wave_per_charge": 25.0, "wave_max": 60,
              "exp_per_wave": 12.0},
    "leaves": {"chance": 0.001, "tiers": [1, 5, 25, 100], "values": [1.0, 2.0, 3.0, 5.0],
               "kinds": ["martial_diligence", "craft_diligence", "finesse", "capacity", "drop_rate"]},
}

CATEGORIES = ["ore", "herb", "fish", "insect", "material", "critter", "wisp"]

# --------------------------------------------------------------------------- crafts
CRAFTS = [
    {"id": "delving", "name": "Vein Delving", "short": "Delving", "attribute": "body", "unlock": "mining", "node": "ore_vein",
     "category": "ore", "tool_word": "pick", "icon": "craft_delving",
     "desc": "Working spirit-ore veins. Body drives it; a better pick breaks harder stone."},
    {"id": "foraging", "name": "Spirit Foraging", "short": "Foraging", "attribute": "insight", "unlock": "herb_gathering", "node": "herb_patch",
     "category": "herb", "tool_word": "sickle", "icon": "craft_foraging",
     "desc": "Cutting herbs at their stems, with spirit wood on the side. Insight drives it."},
    {"id": "angling", "name": "River Angling", "short": "Angling", "attribute": "body", "unlock": "fishing", "node": "fishing_spot",
     "category": "fish", "tool_word": "rod", "icon": "craft_angling",
     "desc": "Fishing a spot through the day. Body drives it; a finer line holds bigger fish."},
    {"id": "netting", "name": "Insect Netting", "short": "Netting", "attribute": "agility", "unlock": "insect_netting", "node": "insect_swarm",
     "category": "insect", "tool_word": "net", "icon": "craft_netting",
     "desc": "Netting spirit insects from their swarms. Agility drives it."},
    # V10c: timed crafts, not posts. Snares run on the clock; rite charge builds for everyone and is spent at an altar.
    {"id": "snaring", "name": "Beast Snaring", "short": "Snaring", "attribute": "agility", "unlock": "beast_snaring", "node": "beast_trail",
     "category": "critter", "tool_word": "snare kit", "icon": "craft_snaring", "timed": True,
     "desc": "Snares set on beast trails for a chosen time. Short snares pay more an hour, long ones more a visit."},
    {"id": "rites", "name": "Ancestral Rites", "short": "Rites", "attribute": "spirit", "unlock": "ancestral_rites", "node": "ancestral_altar",
     "category": "wisp", "tool_word": "tablet", "icon": "craft_rites", "timed": True,
     "desc": "Rite charge builds by itself; spent defending an ancestral altar, it calls down Spirit Wisps."},
]

# --------------------------------------------------------------------------- nodes (§4): output -> (craft, toughness, exp, gate)
NODES = {
    # Vein Delving
    "copper_ore": ("delving", 25, 12, 1), "riverstone": ("delving", 60, 20, 5), "jadeiron": ("delving", 140, 30, 10),
    "spirit_stone_shard": ("delving", 300, 48, 18), "cloudsteel_ore": ("delving", 550, 70, 25), "mystic_ore": ("delving", 900, 100, 32),
    "stormsteel_ore": ("delving", 1400, 150, 40), "sunglass_ore": ("delving", 2000, 210, 45), "driftglass": ("delving", 2800, 290, 50),
    # Spirit Foraging (the base herb; aged herbs are for the hand)
    "willow_moss": ("foraging", 10, 10, 1), "ember_pepper": ("foraging", 40, 18, 4), "riverreed_ginseng_10": ("foraging", 120, 28, 9),
    "mist_lotus": ("foraging", 300, 44, 15), "cloudtop_orchid": ("foraging", 550, 70, 25), "soulbell_flower": ("foraging", 900, 100, 32),
    "frost_lotus": ("foraging", 1400, 150, 40), "ember_cactus": ("foraging", 2000, 210, 45), "star_lotus": ("foraging", 2800, 290, 50),
    # River Angling (by the spot's weights)
    "river_minnow": ("angling", 15, 12, 1), "reed_perch": ("angling", 40, 18, 3), "river_eel": ("angling", 120, 30, 10),
    "jade_carp_fish": ("angling", 300, 44, 15), "mist_trout": ("angling", 550, 60, 20), "rapids_salmon": ("angling", 900, 85, 28),
    "moon_carp": ("angling", 1400, 130, 35),
    # Insect Netting (new)
    "glowfly": ("netting", 10, 10, 1), "reed_cicada": ("netting", 45, 20, 5), "jade_scarab": ("netting", 140, 32, 12),
    "silk_moth": ("netting", 550, 55, 20), "thunder_mantis": ("netting", 900, 90, 30), "frost_cricket": ("netting", 1400, 150, 40),
    "ember_locust": ("netting", 2000, 210, 45), "starwing_mote": ("netting", 2800, 290, 50),
}
# Beast Snaring (V10c): critters by trail, Toughness and EXP weight (the snare table's EXP times this).
NODES.update({
    "jade_frog": ("snaring", 35, 1.0, 1), "mist_hare": ("snaring", 120, 1.3, 5), "reed_ferret": ("snaring", 300, 1.6, 12),
    "cloud_marmot": ("snaring", 550, 2.0, 20), "thunder_hedgehog": ("snaring", 900, 2.5, 30), "frost_stoat": ("snaring", 1400, 3.0, 38),
    "sand_fox": ("snaring", 2000, 3.6, 45), "star_gecko": ("snaring", 2800, 4.2, 50),
})
CRAFT_CATEGORY = {c["id"]: c["category"] for c in CRAFTS}

# --------------------------------------------------------------------------- tools (§7.1)
# tier: (grade, pick, sickle, rod, net) with (power, speed, level gate, finesse %) per craft.
TIERS = [
    ("plain",     ("old_pickaxe", 2, 3, 1, 0),        ("herb_sickle", 3, 3, 1, 0),         ("bamboo_rod", 3, 3, 1, 0),      ("reed_net", 4, 4, 1, 0)),
    ("common",    ("copper_pick", 6, 3, 3, 0),        ("copper_sickle", 7, 3, 4, 0),       ("reedline_rod", 8, 3, 4, 0),    ("hemp_net", 9, 4, 4, 0)),
    ("common",    ("iron_pickaxe", 10, 4, 8, 0),      ("iron_sickle", 10, 3, 8, 0),        ("ironwood_rod", 13, 4, 9, 0),   ("cord_net", 14, 4, 10, 0)),
    ("earth",     ("jadeiron_pick", 13, 4, 15, 0),    ("jadeiron_sickle", 14, 4, 15, 0),   ("jadeline_rod", 19, 4, 15, 0),  ("silk_net", 20, 5, 15, 0)),
    ("heaven",    ("cloudsteel_pick", 16, 4, 25, 0),  ("cloudsteel_sickle", 18, 4, 20, 0), ("cloud_rod", 25, 5, 25, 0),     ("cloudsilk_net", 26, 5, 20, 0)),
    ("mystic",    ("mystic_pick", 19, 5, 32, 2),      ("mystic_sickle", 23, 5, 25, 0),     ("mystic_rod", 30, 5, 32, 0),    ("mystic_net", 31, 5, 25, 0)),
    ("spirit",    ("stormsteel_pick", 24, 5, 40, 8),  ("stormsteel_sickle", 26, 5, 30, 4), ("storm_rod", 36, 5, 40, 4),     ("storm_net", 37, 5, 30, 4)),
    ("sage",      ("sunglass_pick", 30, 6, 45, 12),   ("sunglass_sickle", 29, 6, 40, 8),   ("sunglass_rod", 43, 6, 45, 8),  ("sunglass_net", 45, 6, 40, 8)),
    ("sovereign", ("driftglass_pick", 35, 6, 50, 16), ("driftglass_sickle", 35, 6, 50, 12), ("starline_rod", 50, 6, 50, 12), ("starsilk_net", 55, 6, 50, 12)),
]
EXISTING_TOOLS = {"old_pickaxe", "iron_pickaxe", "herb_sickle", "bamboo_rod"}
# The active-harvest craft each post craft's tools also serve (crafting_authority.tool_power).
ACTIVE_CRAFT = {"delving": "mining", "foraging": "gathering", "angling": "fishing", "netting": "insect_netting"}
# Forge inputs per tier: (metal, count, second, count, binder, count)
TIER_INPUTS = [
    None,
    ("copper_ore", 6, "spirit_wood", 2, "cloth", 1),
    ("riverstone", 6, "copper_ore", 3, "spirit_wood", 2),
    ("jadeiron", 6, "riverstone", 3, "jade_scale", 1),
    ("cloudsteel_ore", 6, "jadeiron", 3, "cloud_feather", 1),
    ("mystic_ore", 6, "cloudsteel_ore", 3, "roc_feather", 1),
    ("stormsteel_ore", 6, "mystic_ore", 3, "spark_pelt", 1),
    ("sunglass_ore", 6, "stormsteel_ore", 3, "scorpion_stinger", 1),
    ("driftglass", 6, "sunglass_ore", 3, "star_shard", 2),
]
NET_BINDER = [None, ("cloth", 3), ("cloth", 4), ("kite_silk", 1), ("cloud_feather", 2), ("roc_feather", 2), ("kite_silk", 3),
              ("kite_silk", 4), ("jelly_silk", 3)]

TOOL_WORDS = {"delving": ("pick", "Breaks spirit ore at a post"), "foraging": ("sickle", "Cuts herbs at a post"),
              "angling": ("rod", "Fishes a spot through the day"), "netting": ("net", "Nets spirit insects from a swarm")}


def tool_rows():
    """(item id, craft, tier, grade, post dict) for all 36 tools."""
    out = []
    for tier, (grade, *per) in enumerate(TIERS):
        for craft, (tid, power, speed, gate, fin) in zip(["delving", "foraging", "angling", "netting"], per):
            out.append((tid, craft, tier, grade, {"craft": craft, "tier": tier, "power": power, "speed": speed, "level_req": gate,
                                                   "finesse_pct": fin}))
    return out


def tool_items(item):
    """Item rows for the tools that do not exist yet (items.py adds `post` to the four that do)."""
    rows = []
    for tid, craft, tier, grade, post in tool_rows():
        if tid in EXISTING_TOOLS:
            continue
        word, what = TOOL_WORDS[craft]
        desc = "%s. Post power %d, speed %d; Level %d in the craft to use it at a post." % (what, post["power"], post["speed"], post["level_req"])
        if post["finesse_pct"]:
            desc += " +%d%% Finesse." % post["finesse_pct"]
        rows.append(item(tid, "tool", grade, 1, desc, tool={"craft": ACTIVE_CRAFT[craft], "power": round(1.0 + 0.15 * tier, 2)}, post=post))
    return rows


def existing_tool_posts():
    return {tid: post for tid, craft, tier, grade, post in tool_rows() if tid in EXISTING_TOOLS}


def tool_recipes():
    """(id, craft, inputs, outputs, grade) for the forge: every tool from tier 1 up."""
    out = []
    for tid, craft, tier, grade, post in tool_rows():
        if tier == 0:
            continue
        metal, n1, second, n2, binder, n3 = TIER_INPUTS[tier]
        if craft == "netting":
            b, nb = NET_BINDER[tier]
            inputs = [(metal, 2), (b, nb), ("spirit_wood", 1)]
        elif craft == "angling":
            inputs = [(metal, 2), ("spirit_wood", 3), (binder, n3)]
        elif craft == "foraging":
            inputs = [(metal, 4), (second, n2), (binder, n3)]
        else:
            inputs = [(metal, n1), (second, n2), (binder, n3)]
        # V10c: from tier 4 the smith wants the Apprentice Bench's components too.
        if tier >= 4:
            inputs.append({4: ("bronze_rivet", 3), 5: ("bronze_rivet", 4), 6: ("whetstone", 2), 7: ("whetstone", 3), 8: ("spirit_glue", 2)}[tier])
        out.append((tid, "smithing", inputs, [(tid, 1)], grade))
    return out


# --------------------------------------------------------------------------- insects and swarms (§4.4)
INSECTS = [
    ("glowfly", "plain", "A firefly whose tail holds a bead of Qi-light. Lamp-makers and night alchemists buy them by the jar."),
    ("reed_cicada", "common", "A reed cicada. Its dried shell calms fevers; its song carries Qi a long way."),
    ("jade_scarab", "earth", "A green scarab whose shell is half jade. Ground, it binds a pill's ingredients."),
    ("silk_moth", "mystic", "A pale moth of the Mist Peak mulberries. Its cocoons spin spirit silk."),
    ("thunder_mantis", "spirit", "A storm-grass mantis that stores a spark in its claws. Handle it by the wings."),
    ("frost_cricket", "spirit", "An ice-blue cricket from the Rimefrost. It chirps colder than the wind."),
    ("ember_locust", "sage", "A Sunscar locust with ember-bright wings. A swarm can strip a dune garden bare."),
    ("starwing_mote", "sovereign", "A fly no bigger than a grain of rice, its wings dusted with starlight from the lanterns."),
]

SWARM_PROP = {"glowfly": "glowfly_swarm", "reed_cicada": "reed_cicada_swarm", "jade_scarab": "jade_scarab_swarm",
              "silk_moth": "silk_moth_swarm", "thunder_mantis": "thunder_mantis_swarm", "frost_cricket": "frost_cricket_swarm",
              "ember_locust": "ember_locust_swarm", "starwing_mote": "starwing_mote_swarm"}

# room -> (x as a share of the room's width, [(insect, weight), ...]); the first insect names the prop.
SWARMS = {
    "lf_reed_shallows": (0.62, [("glowfly", 100)]),
    "wp_west": (0.55, [("glowfly", 100)]),
    "rm_marsh_edge": (0.45, [("glowfly", 70), ("reed_cicada", 30)]),
    "rm_grey_pools": (0.58, [("reed_cicada", 70), ("glowfly", 30)]),
    "bg_whispering_bamboo": (0.42, [("reed_cicada", 60), ("jade_scarab", 40)]),
    "bg_thicket_heart": (0.52, [("jade_scarab", 100)]),
    "dw_bend_shore": (0.66, [("jade_scarab", 70), ("reed_cicada", 30)]),
    "cc_sky_ledges": (0.48, [("silk_moth", 50), ("jade_scarab", 50)]),
    "mp_misty_slopes": (0.44, [("silk_moth", 100)]),
    "mp_forgotten_monastery": (0.6, [("silk_moth", 70), ("jade_scarab", 30)]),
    "tp_stormgrass_verge": (0.5, [("thunder_mantis", 100)]),
    "tp_thunderhorn_flats": (0.38, [("thunder_mantis", 100)]),
    "tp_lightning_scar": (0.56, [("thunder_mantis", 80), ("silk_moth", 20)]),
    "rf_frostpine_climb": (0.46, [("frost_cricket", 100)]),
    "rf_snow_ape_ledges": (0.6, [("frost_cricket", 100)]),
    "rf_rimefrost_summit": (0.34, [("frost_cricket", 80), ("thunder_mantis", 20)]),
    "sd_glass_dunes": (0.52, [("ember_locust", 100)]),
    "sd_scorpion_flats": (0.4, [("ember_locust", 100)]),
    "sd_worm_sea": (0.62, [("ember_locust", 80), ("frost_cricket", 20)]),
    "dr_jellyfish_shallows": (0.36, [("starwing_mote", 100)]),
    "dr_sparrow_reefs": (0.55, [("starwing_mote", 100)]),
    "dr_driftglass_bank": (0.7, [("starwing_mote", 80), ("ember_locust", 20)]),
}


def insect_items(item):
    rows = []
    for iid, grade, desc in INSECTS:
        rows.append(item(iid, "insect", grade, 99, desc))
    return rows


# --------------------------------------------------------------------------- V10c · Beast Snaring (§7.3)
CRITTERS = [
    ("jade_frog", "plain", "A thumb-sized jade frog from the reed pools. Spirit beasts gulp them whole."),
    ("mist_hare", "common", "A grey hare that fades into morning mist. Its fur lines winter robes."),
    ("reed_ferret", "earth", "A quick ferret of the bamboo and reeds, sleek and curious."),
    ("cloud_marmot", "mystic", "A plump marmot of the high ledges with a tail like a puff of cloud."),
    ("thunder_hedgehog", "spirit", "A hedgehog whose quills crackle before a storm."),
    ("frost_stoat", "spirit", "A white winter stoat of the Rimefrost, colder than the snow it hides in."),
    ("sand_fox", "sage", "A small fox of the Sunscar with ears like sails."),
    ("star_gecko", "sovereign", "A gecko of the drifting islands with gold spots that glow like distant stars."),
]
RADIANT = ("radiant_pelt", "heaven", "The pelt of a radiant beast, a snare's rare prize: pearly, warm, and worth a great deal.")
# room -> (share of width, critter): one beast trail per room.
TRAILS = {
    "lf_reed_shallows": (0.28, "jade_frog"), "rm_marsh_edge": (0.25, "jade_frog"), "wp_west": (0.3, "mist_hare"),
    "sq_quarry_rim": (0.6, "mist_hare"), "bg_whispering_bamboo": (0.7, "reed_ferret"), "dw_bend_shore": (0.3, "reed_ferret"),
    "mp_misty_slopes": (0.7, "cloud_marmot"), "cc_sky_ledges": (0.75, "cloud_marmot"), "tp_stormgrass_verge": (0.25, "thunder_hedgehog"),
    "tp_thunderhorn_flats": (0.68, "thunder_hedgehog"), "rf_frostpine_climb": (0.22, "frost_stoat"), "rf_snow_ape_ledges": (0.3, "frost_stoat"),
    "sd_glass_dunes": (0.25, "sand_fox"), "sd_scorpion_flats": (0.7, "sand_fox"), "dr_sparrow_reefs": (0.25, "star_gecko"),
    "dr_driftglass_bank": (0.35, "star_gecko"),
}
# Snare kits: (item, grade, tier, power, level gate, snares at once)
KITS = [("hemp_snare_kit", "common", 0, 4, 1, 1), ("iron_snare_kit", "earth", 1, 14, 15, 2),
        ("silk_snare_kit", "mystic", 2, 26, 30, 3), ("star_snare_kit", "sovereign", 3, 45, 45, 4)]
# Snare lengths: (id, least kit tier, seconds, critters, EXP, kind). Short snares pay more an hour, long ones a visit.
SNARES = [
    ("snare_20m", 0, 1200, 1, 1, ""), ("snare_1h", 0, 3600, 2, 2, ""), ("snare_8h", 0, 28800, 10, 8, ""), ("snare_20h", 0, 72000, 20, 15, ""),
    ("snare_40h", 1, 144000, 35, 50, ""), ("snare_3h", 2, 10800, 5, 5, ""), ("snare_60h", 2, 216000, 50, 40, ""),
    ("snare_120h", 2, 432000, 100, 80, ""), ("snare_120h_beasts", 2, 432000, 200, 0, "beasts"), ("snare_120h_insight", 2, 432000, 0, 200, "insight"),
    ("snare_28d", 3, 2419200, 550, 1150, ""),
]

# --------------------------------------------------------------------------- V10c · Ancestral Rites (§7.3)
TABLETS = [("wood_rite_tablet", "common", 0, 4, 4, 1), ("jade_rite_tablet", "earth", 1, 12, 5, 15),
           ("cloud_rite_tablet", "mystic", 2, 24, 6, 30), ("star_rite_tablet", "sovereign", 3, 40, 7, 45)]   # (item, grade, tier, power, speed, gate)
# room -> (share of width, Toughness): the ancestral altars.
ALTARS = {"sf_county_hall": (0.3, 25), "ja_library": (0.7, 60), "cm_cloud_library": (0.7, 60), "np_hall_of_nine": (0.25, 400),
          "lh_star_chandlery": (0.3, 1400)}
# Post Vows (V10c): a boon and a curse, learned for the account with Spirit Wisps; two held per character.
POST_VOWS = [
    {"id": "vow_short_lamp", "name": "Vow of the Short Lamp", "cost": 40, "boon": {"craft_exp_pct": 25}, "curse": {"post_hours": 10},
     "text": "+25% craft EXP. Posts stop working after 10 hours away."},
    {"id": "vow_quiet_hand", "name": "Vow of the Quiet Hand", "cost": 60, "boon": {"finesse_pct": 15}, "curse": {"craft_exp_pct": -30},
     "text": "+15% Finesse. -30% craft EXP."},
    {"id": "vow_burdened", "name": "Vow of the Burdened Back", "cost": 90, "boon": {"craft_diligence": 8}, "curse": {"capacity_pct": -60},
     "text": "+8% Craft Diligence. Pouches hold 60% less."},
    {"id": "vow_iron_fast", "name": "Vow of the Iron Fast", "cost": 120, "boon": {"martial_diligence": 10}, "curse": {"food_mult": 2.0},
     "text": "+10% Martial Diligence. A Vigil eats its provisions twice as fast."},
    {"id": "vow_open_palm", "name": "Vow of the Open Palm", "cost": 160, "boon": {"drop_rate": 50}, "curse": {"kills_pct": -20},
     "text": "+50% Vigil drop rate. -20% Vigil kills."},
]

# --------------------------------------------------------------------------- V10c · Apprentice Bench (§7.3)
COMPONENTS = [("hemp_cord", "common", 100, 1, "A coil of hemp cord, twisted by an apprentice's patient hands."),
              ("bronze_rivet", "common", 200, 5, "A handful of bronze rivets for binding a tool's head to its haft."),
              ("kiln_brick", "earth", 350, 12, "A fired brick with the bench's stamp. Furnaces and forges are built of them."),
              ("lacquer_pot", "earth", 700, 17, "A pot of red lacquer with its brush, to seal wood against the damp."),
              ("whetstone", "heaven", 1200, 25, "A fine grey whetstone. A blade or a sickle kept on it cuts true."),
              ("spirit_glue", "mystic", 2000, 30, "Amber glue boiled from spirit resin. It holds what nails cannot.")]   # (item, grade, progress, level gate, desc)


def v10c_items(item):
    rows = []
    for iid, grade, desc in CRITTERS:
        rows.append(item(iid, "critter", grade, 99, desc, food={"group": "pet", "pet_food": True}))
    rows.append(item(RADIANT[0], "beast_part", RADIANT[1], 99, RADIANT[2]))
    for iid, grade, tier, power, gate, snares in KITS:
        rows.append(item(iid, "tool", grade, 1, "A snare kit: %d snare%s at once, power %d; Level %d in Beast Snaring to use it." % (snares, "" if snares == 1 else "s", power, gate),
                         post={"craft": "snaring", "tier": tier, "power": power, "speed": 3, "level_req": gate, "finesse_pct": 0, "snares": snares}))
    for iid, grade, tier, power, speed, gate in TABLETS:
        rows.append(item(iid, "tool", grade, 1, "An ancestral tablet for the Rites: power %d, charge speed %d; Level %d in Ancestral Rites to use it." % (power, speed, gate),
                         post={"craft": "rites", "tier": tier, "power": power, "speed": speed, "level_req": gate, "finesse_pct": 0}))
    rows.append(item("spirit_wisp", "wisp", "earth", 999, "A wisp of an ancestor's regard, called down at an altar. Post Vows are pledged with them."))
    for iid, grade, _prog, _gate, desc in COMPONENTS:
        rows.append(item(iid, "material", grade, 99, desc))
    return rows


# --------------------------------------------------------------------------- pouches (§3.7)
POUCH_TIERS = [25, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000, 25000, 30000, 35000]
TIER_NAMES = ["Thimble", "Palm", "Sleeve", "Satchel", "Gourd", "Chest-Gourd", "Cavern-Gourd", "Hall-Gourd", "Valley-Gourd",
              "Mountain-Gourd", "River-Gourd", "Sky-Gourd", "Heaven-and-Earth"]
SEW_MATERIALS = [("cloth", 2), ("cloth", 4), ("thorn_hide", 4), ("serpent_scale", 4), ("cloud_feather", 4), ("mist_pelt", 4),
                 ("kite_silk", 4), ("snow_ape_hide", 4), ("comet_iron", 4), ("jelly_silk", 6), ("jelly_silk", 10),
                 ("guardian_scale", 6), ("wyrm_ash", 4)]


def sewing():
    rows = []
    for i, cap in enumerate(POUCH_TIERS):
        mat, n = SEW_MATERIALS[i]
        items = [{"item": mat, "count": n}]
        if i + 1 >= 4:   # V10c: deeper folds are stitched with the Apprentice Bench's hemp cord
            items.append({"item": "hemp_cord", "count": 4 * (i + 1)})
        rows.append({"tier": i + 1, "name": TIER_NAMES[i], "cap": cap, "taels": int(round(30 * 2.1 ** (i + 1), -1)), "items": items})
    return rows


# --------------------------------------------------------------------------- incense (§3.9)
INCENSE = [("hour_incense_1", 1, "common"), ("hour_incense_2", 2, "common"), ("hour_incense_4", 4, "earth"),
           ("hour_incense_12", 12, "heaven"), ("hour_incense_24", 24, "mystic"), ("hour_incense_72", 72, "spirit")]


def incense_items(item):
    rows = []
    for iid, hours, grade in INCENSE:
        rows.append(item(iid, "other", grade, 99,
                         "Burned at a character's post from the Roll-Call: %d hour%s of that post's work at once." % (hours, "" if hours == 1 else "s"),
                         name="Hour Incense (%d h)" % hours, hour_incense={"hours": hours}))
    rows.append(item("wandering_incense", "other", "heaven", 99,
                     "Its smoke wanders. Burned at a post it grants anywhere from 5 to 500 hours of that post's work, most often about a day.",
                     name="Wandering Incense", hour_incense={"min": 5, "max": 500}))
    return rows


def build():
    nodes = {}
    for item_id, (craft, tough, exp, gate) in NODES.items():
        nodes[item_id] = {"craft": craft, "toughness": tough, "exp": exp, "gate": gate, "category": CRAFT_CATEGORY[craft]}
    nodes["spirit_wood"] = {"craft": "foraging", "toughness": 10, "exp": 0, "gate": 1, "category": "herb", "side": True}
    nodes["spirit_wisp"] = {"craft": "rites", "toughness": 0, "exp": 0, "gate": 1, "category": "wisp", "side": True}
    nodes[RADIANT[0]] = {"craft": "snaring", "toughness": 0, "exp": 0, "gate": 1, "category": "critter", "side": True}
    swarms = {rid: [{"item": i, "weight": w} for i, w in outs] for rid, (_x, outs) in SWARMS.items()}
    write("posts.json", {
        "entries": CRAFTS,
        "rules": RULES,
        "categories": CATEGORIES,
        "nodes": nodes,
        "pouch_tiers": POUCH_TIERS,
        "sewing": sewing(),
        "incense": {iid: h for iid, h, _g in INCENSE},
        "swarms": swarms,
        "snares": [{"id": sid, "kit": kt, "seconds": sec, "critters": cr, "exp": ex, "kind": kind} for sid, kt, sec, cr, ex, kind in SNARES],
        "trails": {rid: {"critter": cr} for rid, (_x, cr) in TRAILS.items()},
        "altars": {rid: {"toughness": t} for rid, (_x, t) in ALTARS.items()},
        "post_vows": POST_VOWS,
        "bench": {"components": [{"item": iid, "progress": prog, "gate": gate} for iid, _g, prog, gate, _d in COMPONENTS],
                  "apprentices": [0, 60, 150], "points_per_levels": 5, "speed_per_point": 0.02, "exp_per_point": 0.03, "cap_per_point": 0.1},
    })
