"""S14/S15/Part 8: items.json (non-equipment) and artifacts.json (equipment bases).

Decision 45 (audit 45 §6.4): the item engine writes the rows of its families (tools/content/items/specs: pills, herbs,
ores, creature parts, gear); this module places each family section among the rows written here, which are the
one-offs (quest items, keys, unique treasures and the like) and the groups not yet in a family.
"""
import os
import sys

from common import entries, titled, run_cli
from legends import CHAINS as LEGENDS, piece_rows
from gear import ARCHETYPES, tag
import posts

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # tools/: the content engines
from content.items import engine as E  # noqa: E402
from content.items.curves import MID_ILV  # noqa: E402
from content.items.kinds import item  # noqa: E402  (every module's row constructor)

# P5 (the Bag, decision 24): the kinds its filters show, by item type. Gear is every equipment piece (artifacts.json);
# a type not listed here is "other".
BAG_KINDS = {"pills": ["pill"], "materials": ["material", "beast_part", "core", "ore", "hollow", "herb", "fish", "insect", "critter", "jade",
                                              "wisp", "oil", "legend_piece"]}

# Decision 45: the spaces of the bag with no gourd worn, and of the Starter Spirit Gourd (stats.json bag.base).
BAG_BASE = 50


PET_BOOKS = [
    ("iron_hide", "Iron Hide", "common", "An animal that learns it takes 10% less damage."),
    ("frenzy", "Frenzy", "earth", "After a kill the animal strikes 15% faster for 6 seconds."),
    ("deep_pockets", "Deep Pockets", "earth", "While it is your active animal, your gourd holds one more row (6 slots)."),
    ("herb_whisper", "Herb Whisper", "earth", "While it walks beside you, herbs within 400 show how long until they ripen."),
    ("thunder_roar", "Thunder Roar", "heaven", "Every 15 seconds of a fight it roars: foes near it are stunned for 1 second."),
    ("guardian_spirit", "Guardian Spirit", "heaven", "Once every 30 seconds it takes a blow meant for you."),
]

CORE_ELEMENTS = ["fire", "water", "wood", "earth", "wind", "thunder", "soul", "metal", "star", "space"]   # v1.2: metal, star, space
# S45 herb ages and seeds, as garden.json reads them (herbs.py): the herb families' (specs/herbs.py).
HERB_AGE = E.herb_ages()
SEEDS = E.seeds()
# S47 talisman craft: inks and papers (Part 8).
TALISMAN_MATS = [("cinnabar", "common", "Red mercury ore ground to powder: the ink every talisman begins with. Stoneford General Store sells it.", "Cinnabar"),
                 ("beast_blood_ink", "earth", "Ink cut with a beast's blood; it holds a stronger charge than cinnabar alone.", "Beast-Blood Ink"),
                 ("spirit_paper", "earth", "Talisman paper steeped with Mist Lotus until it drinks Qi.", "Spirit Paper")]
# The talismans themselves: (id, grade, kind, desc). Numbers live in talismans.json.
# Item text: one line on where it comes from and what it is for (the UI shows it under the name).
FISH_DESC = {
    "river_minnow": "A silver minnow from the Jade River shallows. Bait, or a quick snack.",
    "reed_perch": "A striped perch that hides among the reeds.",
    "jade_carp_fish": "A green-gold carp from the deeper pools. Said to bring luck to a household.",
    "river_eel": "A slippery river eel. Smoked, it keeps for a month.",
    "mist_trout": "A pale trout from the cold falls pool, lean and full of Qi.",
    "rapids_salmon": "A strong salmon caught where the river runs white.",
    "moon_carp": "A carp that shines faintly in the dark. It bites only at night, in any water.",
}
# P13a the scrolls lost arts are found in (a foe's drop, a lot at auction): (item, art, name, grade).
LOST_SCROLLS = [("scroll_tide_palm", "tide_palm", "Tide-Palm Scroll", "heaven"), ("scroll_serpent_coil_thrust", "serpent_coil_thrust", "Serpent-Coil Scroll", "heaven"),
                ("scroll_sand_throne_sweep", "sand_throne_sweep", "Sand-Throne Scroll", "spirit"),
                ("scroll_many_eyed_pool_air", "many_eyed_pool_air", "Many-Eyed Scroll", "spirit"),
                ("scroll_ninth_peak_scroll", "ninth_peak_scroll", "Nine Peaks Lot Scroll", "spirit"),
                ("scroll_broadside_fan", "broadside_fan", "Broadside Scroll", "sovereign"),
                ("scroll_pyre_generals_lance", "pyre_generals_lance", "Pyre-General's Scroll", "sovereign"),
                ("scroll_comet_tail_arrow", "comet_tail_arrow", "Comet-Tail Scroll", "sovereign"), ("scroll_maw_song", "maw_song", "Maw-Song Scroll", "will")]

TOOL_DESC = {
    "old_pickaxe": "A worn pickaxe with a loose head. It still breaks ore, slowly.",
    "iron_pickaxe": "A sound iron pickaxe: veins give up their ore faster.",
    "herb_sickle": "A curved sickle for cutting herbs cleanly at the stem, so they keep their potency.",
    "bamboo_rod": "A bamboo fishing rod with a horsehair line. Every fisher starts with one.",
    "clay_pot": "A blackened clay pot. Cooking starts here.",
    "forge_hammer": "A smith's hammer, balanced for long days at the anvil.",
    "formation_kit": "Chalk, a compass and a pouch of flags: all a formation needs to be laid out.",
    "needle_case": "A case of fine silver needles for acupuncture and stitching wounds.",
    "appraisers_loupe": "A jade loupe that shows what a curio really is, and what it is worth.",
    "drying_rack": "A folding bamboo rack. Steam herbs on it (their pills carry 30% less toxicity) or soak them in rice wine (10% more potency). Set it up at any garden bed.",
    "spirit_spade": "A jade-edged spade that cuts earth without cutting roots. With Expert gathering, dig a rare herb up whole and move it to a garden bed.",
    "verdant_dew_vial": "A green glass vial that fills with one drop of dew a day, even while you are away (it holds three). A drop ages the herb in a bed one tier.",
}

TALISMANS = [("flame_talisman", "common", "attack", "Thrown, it bursts into a sheet of fire: 180% fire damage at the talisman's own grade within 80."),
             ("thunder_talisman", "earth", "attack", "Thrown, it calls a bolt: 240% thunder damage at the talisman's own grade, and Shock."),
             ("iron_wall_talisman", "common", "defence", "Burned, it wraps you in iron Qi: a shield that absorbs 20% of your max HP for 6 s."),
             ("wind_step_talisman", "common", "movement", "Burned, it lends you one free dodge within 60 s, cooldown or not."),
             ("veil_talisman", "earth", "movement", "Burned, it hides you for 10 s: monsters that have not found you pass you by."),
             ("binding_talisman", "earth", "sealing", "Thrown, it roots the nearest foe for 2 s. Bosses shrug it off.")]
# S47 gear upkeep: what Salvage gives back, and what steadies an enhancement.
REFINING = [("refining_essence", "common", "The refined Qi of a salvaged piece. The forge feeds it into an enhancement to steady it.", "Refining Essence")]
FISH = [("river_minnow", "plain"), ("reed_perch", "plain"), ("jade_carp_fish", "earth"), ("river_eel", "common"),
        ("mist_trout", "earth"), ("rapids_salmon", "earth"), ("moon_carp", "heaven")]


# S44 / Part 8 furnaces: equipment worn in the furnace slot (tool_furnace), enhanced at the forge (+1% heat
# stability a level). band = heat stability (the strike band widens), batch = pills a batch, filter = the share of
# each missed strike's impurities it takes out on its own, yield = chance of one more pill, element = +5% quality
# for that element's recipes. Only the named Nine-Dragon Cauldron changes what a fire allows.
FURNACES = [
    ("bronze_furnace", "plain", "Bronze Furnace", "bronze_furnace",
     "Mei Qing's old bronze furnace. Three pills to a batch; it holds heat well enough.",
     {"band": 0.0, "batch": 3, "filter": 0.0, "yield": 0.0}),
    ("jadeiron_furnace", "earth", "Jadeiron Furnace", "earth_vein_furnace",
     "Jadeiron walls a hand thick. Five pills to a batch, a steadier heat, and it strains a tenth of the impurities out.",
     {"band": 0.05, "batch": 5, "filter": 0.10, "yield": 0.05}),
    ("cloudsteel_furnace", "heaven", "Cloudsteel Furnace", "cloud_pattern_furnace",
     "Cloudsteel etched with drifting clouds. Eight pills to a batch; a fifth of the impurities slide off its walls.",
     {"band": 0.08, "batch": 8, "filter": 0.20, "yield": 0.10}),
    ("mistjade_furnace", "mystic", "Mistjade Furnace", "mystic_tripod",
     "A three-legged furnace of mistjade that hums over the fire. Ten pills to a batch, and it keeps almost a third of the impurities out.",
     {"band": 0.10, "batch": 10, "filter": 0.30, "yield": 0.15}),
    ("nine_dragon_cauldron", "heaven", "Nine-Dragon Cauldron", "nine_dragon_cauldron",
     "Nine bronze dragons coil round it and drink the heat. A named furnace: on any fire a perfect run can reach Grain, Halo "
     "and Soul. Eight pills to a batch; water pills come easier in it.",
     {"band": 0.12, "batch": 8, "filter": 0.20, "yield": 0.10, "named": True, "element": "water"}),
]
FLAMES = [
    # The valley's Heavenly Flame (Part 8): the Weeping Lantern elite of the Forgotten Monastery carries it.
    ("mist_lantern_flame", "mystic", "A pale flame that drifted in a Weeping Lantern's paper for a hundred years, lighting nothing."),
    ("cold_lamp_flame", "spirit", "A cold blue flame the Thousand-Eye Toad swallowed from a sunken lamp. It kept burning in its belly under Mirrorwater Lake."),
    ("sunscar_throne_ember", "sage", "An ember from under the Tomb King's throne. It remembers three thousand years of sun."),
    ("comet_tail_flame", "sage", "A white flame torn from a comet's tail, kept in Comet Captain Rao's lamp."),
    # v1.2 Phase E: the flame at the Lantern Heart, the fallen star every lantern of the Field was lit from.
    ("lantern_heart_flame", "will", "The flame at the heart of the Lantern Star Field, burning in a cage older than the Wardens. Lu once carried a spark of it home."),
]


# Treasures (Build Prompt v2 S47, Part 8): each is one action set in a HUD Treasure button, with a cooldown and a flat
# QI cost (and a Soul cost of a third of it from Spirit Awakening 1). The mechanics are also written to treasures.json.
TREASURES = [
    ("practice_bell", "plain", "A sect training bell. Rung, it stuns foes close by for half a second.",
     {"action": "bell", "cooldown_s": 25, "qi": 15, "radius": 100, "stun_s": 0.5, "seal_s": 0, "source": "A Treasure in Hand (Heart Tempering 1)"}),
    ("bronze_bell", "earth", "A drowned temple bell. Rung, it stuns foes around you for 1 s and seals their Qi for 3 s. Bosses only lose their Qi.",
     {"action": "bell", "cooldown_s": 20, "qi": 30, "radius": 150, "stun_s": 1, "seal_s": 3, "source": "Drowned Abbot (first clear)"}),
    ("little_pagoda", "heaven", "A jade pagoda the size of a palm. Thrown, it falls over one foe as a prison for 4 s. Bosses are too great for it.",
     {"action": "pagoda", "cooldown_s": 30, "qi": 40, "range": 320, "imprison_s": 4, "source": "Gu's Warehouse vault"}),
    ("bright_mirror", "earth", "A polished bronze mirror. For 2 s every missile that reaches you flies back at the one who threw it.",
     {"action": "mirror", "cooldown_s": 18, "qi": 25, "reflect_s": 2, "source": "Forge (Heart Tempering blueprint)"}),
    ("mountain_seal", "heaven", "A jade seal the weight of a hill. Brought down, it strikes everything within reach for 250% Qi Attack.",
     {"action": "seal", "cooldown_s": 25, "qi": 45, "radius": 120, "mult": 2.5, "knockback": 120, "damage_type": "qi", "source": "Stone Guardian (rare)"}),
    ("taming_cauldron", "earth", "An iron cauldron that takes in a beast worn below 20% HP whole, as materials. Not bosses.",
     {"action": "cauldron", "cooldown_s": 40, "qi": 30, "range": 260, "below": 0.2, "source": "Beast Hall shop"}),
    ("wisp_banner", "mystic", "A formation banner that calls three wisps of light. For 10 s they fight beside you, striking the nearest foes.",
     {"action": "banner", "cooldown_s": 45, "qi": 50, "wisps": 3, "duration": 10, "mult": 0.6, "range": 280, "source": "Bai Ling's quest line"}),
    ("sealing_gourd", "heaven", "A violet gourd with a paper seal. Unstoppered, it drinks every missile that comes near for 3 s.",
     {"action": "gourd", "cooldown_s": 20, "qi": 30, "absorb_s": 3, "radius": 240, "source": "Old Ma (after Spirit Awakening 1)"}),
    # S47 the sword swarm (v1.1): nine swords in a lacquered case; set in a Treasure slot they orbit and strike.
    ("nine_sword_array", "spirit", "Nine slim swords in a lacquered case. Released, they orbit you for 12 s and strike on their own; set in a Treasure slot it also lets a Sword Dao swarm number nine. One sword for each 10 Spirit.",
     {"action": "swarm", "cooldown_s": 45, "qi": 60, "duration": 12, "source": "Forge (Ironroot Clan blueprint)"}),
    # A talisman treasure: three charges of an art far above the realm, spent from a Treasure button (no cooldown).
    ("elder_hus_talisman", "mystic", "Elder Hu's Heaven-Splitting Palm folded into paper: three charges of 600% Qi Attack in a line before you. Never sold.",
     {"action": "palm", "cooldown_s": 0, "qi": 0, "charges": 3, "mult": 6.0, "reach": 540, "depth": 70, "source": "Elder Hu, before the Heart Trial"}),
]
TREASURE_DEFS = []
# Flight vessels (S47): a flight item sets the flight sprite and what the air costs.
VESSELS = [
    ("flying_sword_vessel", "heaven", "Ride your sword into the sky, the way the stories say. The air costs a fifth less.", {"sprite": "sword", "qi_mult": 0.8}),
    ("cloud_puff_vessel", "earth", "A small obedient cloud, soft and very cheap on Qi.", {"sprite": "cloud", "qi_mult": 0.65}),
    ("jade_gourd_vessel", "earth", "A great jade gourd you sit astride. Steady on the wind.", {"sprite": "gourd", "qi_mult": 0.85}),
    ("maple_leaf_vessel", "common", "A red maple leaf the size of a raft. It wanders, but it is kind to your Qi.", {"sprite": "leaf", "qi_mult": 0.75}),
]


def effect(kind, **f):
    d = {"kind": kind}
    d.update(f)
    return d


# Decision 45: an item's cultivation is a fixed number set by its grade: `share` of the need of the stage at the middle
# of its grade band (MID_ILV), the Level the item is pitched at. No item pays a share of the eater's own stage any more,
# so an early pill stays small later and a late core never skips a realm early.
def cultivation(share, grade):
    import realms
    return realms.cultivation(share, MID_ILV.get(grade, 5))


def progress(share, grade):
    """The add_progress effect of an item of `grade` worth `share` of its band's stage."""
    return effect("add_progress", amount=cultivation(share, grade))


def cult_text(n):
    """How an item's text says its cultivation: "+420 cultivation"."""
    return "+{:,} cultivation".format(n)


def foods():
    F = []

    def food(id, desc, effects, grade="plain", group="buff", pet_food=False, **extra):
        F.append(item(id, "food", grade, 99, desc, use=effects, food={"group": group, "pet_food": pet_food}, **extra))
    food("herbal_tea", "A calming brew of willow moss. +25% max HP over 5 s.", [effect("heal", pct=0.25, over_s=5)], group="healing")
    food("rice_ball", "Plain and filling. +0.5% HP regeneration per second for 10 minutes.",
         [effect("add_modifier", stat="hp_regen", op="flat", value=0.005, duration=600, source="rice_ball")])
    food("riverfish_soup", "+5% max HP for 20 minutes.", [effect("add_modifier", stat="max_hp", op="pct_add", value=0.05, duration=1200, source="riverfish_soup")])
    food("boar_bone_broth", "+120 body XP.", [effect("add_body_xp", amount=120)], group="utility")
    food("ember_pepper_stew", "+10% attack and +5 Fire resistance for 20 minutes.",
         [effect("add_modifier", stat="physical_attack", op="pct_add", value=0.1, duration=1200, source="ember_stew")], grade="common")
    food("lotus_root_tea", "+10% QI regeneration for 20 minutes.", [effect("add_modifier", stat="qi_regen", op="pct_add", value=0.1, duration=1200, source="lotus_tea")], grade="earth")
    food("toad_oil_dumplings", "+5% move speed for 15 minutes.", [effect("add_modifier", stat="move_speed", op="pct_add", value=0.05, duration=900, source="toad_dumplings")])
    food("cloudtop_orchid_broth", "+300 body XP.", [effect("add_body_xp", amount=300)], grade="heaven", group="utility")
    # S49 leisure arts: each region's tea house pours its own tea (Stoneford, Greyreed Hamlet, Cloudgate Port).
    food("jasmine_dew_tea", "Stoneford's jasmine, picked with the dew on it. +10% insight for 30 minutes.",
         [effect("add_modifier", stat="insight_rate", op="flat", value=0.1, duration=1800, source="jasmine_tea")], grade="common", region="stoneford")
    food("marsh_mist_tea", "Greyreed's grey-green tea, brewed thin as marsh fog. +8% evasion for 30 minutes.",
         [effect("add_modifier", stat="evasion", op="pct_add", value=0.08, duration=1800, source="marsh_tea")], grade="common", region="greyreed_hamlet")
    food("thunderhead_tea", "A Cloudgate brew that crackles on the tongue. +2 Storm Ward for 30 minutes.",
         [effect("add_modifier", stat="attunement_bonus", op="flat", value=2, duration=1800, source="thunderhead_tea")], grade="earth", region="cloudgate_port")
    food("jade_carp_congee", "+5% accumulation for 30 minutes.", [effect("add_modifier", stat="accumulation_rate", op="flat", value=0.05, duration=1800, source="carp_congee")], grade="earth")
    food("thunderhorn_stew", "+8% max HP and +5% physical defence for 30 minutes.",
         [effect("add_modifier", stat="max_hp", op="pct_add", value=0.08, duration=1800, source="thunderhorn_stew"),
          effect("add_modifier", stat="physical_defense", op="pct_add", value=0.05, duration=1800, source="thunderhorn_stew")], grade="spirit")
    food("cactus_water", "+20 Essence for 20 minutes: the Sunscar heat slides off.",
         [effect("add_modifier", stat="essence", op="flat", value=20, duration=1200, source="cactus_water")], grade="sage")
    food("roast_fish", "A spirit animal favourite.", [effect("heal", pct=0.1, over_s=3)], pet_food=True)
    food("ember_pepper_broth", "A spicy broth spirit animals love.", [effect("heal", pct=0.1, over_s=3)], grade="common", pet_food=True)
    F.append(item("willow_salve", "talisman", "plain", 99, "Cures a minor body injury.", use=[effect("cure_injury", injury="body", max_severity=1)],
                  food={"group": "healing"}))
    return F


def build_items():
    E.begin("items")
    rows = []
    TREASURE_DEFS.clear()
    rows.extend(E.items("herbs"))   # specs/herbs.py: the herbs by age, then their seeds
    rows.extend(E.items("seeds"))
    # S45 garden materials and tools.
    rows.append(item("spring_water", "material", "common", 20, "Qi-spring water in a stoppered gourd. Poured on a garden bed, it hurries the herb along by a quarter. A spring gives three bottles a day.",
                     name="Bottled Spring Water"))
    rows.append(item("dyed_root", "material", "plain", 99, "A carrot root dyed and combed to pass for hundred-year ginseng. Worth nothing, except as a lesson.",
                     name="Dyed Root", source="system"))
    rows.append(item("rice_wine", "material", "common", 20, "A clay jar of cloudy rice wine. Herbs soaked in it on a drying rack make stronger pills."))
    rows.append(item("spirit_soil", "material", "heaven", 20, "Black earth that still remembers a spirit vein. Worked into a garden bed, it raises the bed's field grade one step, for good. Strong beasts sometimes carry it in their hides."))
    rows.extend(E.items("ores"))   # specs/ores.py
    for o in REFINING + TALISMAN_MATS:
        rows.append(item(o[0], "material", o[1], 99, o[2], name=o[3]))
    for tid, grade, kind, desc in TALISMANS:
        rows.append(item(tid, "talisman", grade, 20, desc, use=[], use_action="talisman", talisman=kind))
    # A Shattered Relic (S47): the Drowned Abbot's old blade in pieces; a master smith restores it.
    # S47 legendary chains: three pieces of each legend (quest drops while its chain wants them), and the crystal that
    # awakens a +10 weapon of Heaven grade or better.
    for pid, pname, ch, i in piece_rows():
        where = "an old foe of the valley" if i == 0 else "the Azure Expanse"
        rows.append(item(pid, "legend_piece", "mystic", 1, "A piece of %s, found with %s. Three pieces, and an Expert smith, make it whole." % (ch["name"], where),
                         name=pname, sell=False, quest_item=True))
    rows.append(item("weapon_soul_crystal", "material", "heaven", 9, "A crystal with a small flame inside. At a forge it wakes a weapon forged to +10, "
                     "of Heaven grade or better, for one whose Dao of that weapon has reached Explanation.", name="Weapon Soul Crystal", sell=False))
    rows.append(item("shattered_moon_blade", "relic_shard", "heaven", 1, "The pieces of a jian that once held a spirit, pale as moonlight. "
                     "A smith of Expert rank could restore it at the forge.", name="Shattered Moon Blade", sell=False, restores="moonlit_blade"))
    # Creature parts (specs/parts.py): the valley's beasts, then the Azure Expanse's (Act II) and its monsters' materials.
    rows.extend(E.items("parts.valley"))
    rows.extend(E.items("parts.expanse"))
    rows.append(item("sun_seal_shard", "material", "sage", 9, "A curved piece of a gold and jade disc, swallowed long ago by a Dune Worm.",
                     sell=False, quest_item=True))
    rows.append(item("sunscar_seal", "key", "sage", 1, "The Tomb King's sun seal: a disc of gold and jade, warm as a living hand.", sell=False,
                     quest_item=True))
    rows.append(item("alliance_token", "key", "spirit", 1, "A jade token of the Nine Peaks Alliance. Sky roads open for its bearer."))
    rows.append(item("ironroot_token", "key", "spirit", 1, "An iron-hard sliver of root, carved with the Ironroot clan's mark."))
    # Phase E · the Starsea: star readings and charts (S16 star charting), vessels (shipwright), pirates' goods.
    rows.append(item("star_reading", "material", "sage", 99,
                     "A star's place, taken through a sighting ring and written in sky ink. Charts are made of them."))
    rows.append(item("sky_ink", "material", "spirit", 99, "Ink ground with star-dust. The Starsea wind cannot fade it."))
    rows.extend(E.items("parts.starsea"))   # the pirates' hull iron, the deserters' badges
    rows.append(item("ledger_page", "material", "sage", 9, "A page of the Black Ledger: valley family names, and what each paid to keep them secret.",
                     name="Black Ledger Page", sell=False, quest_item=True))
    rows.append(item("black_ledger", "key", "sage", 1, "Elder Gu's Black Ledger, stitched back together. Every valley family that ever paid him is in it.",
                     sell=False, quest_item=True))
    rows.append(item("star_chart_wreck", "key", "sage", 1, "A chart of the Wreck Run: from the Cloudgate Skydock across the Starsea to the Skyport Wreck, and home.",
                     name="Star Chart: the Wreck Run", sell=False, chart="wreck_run"))
    rows.append(item("star_chart_lantern", "key", "sage", 1, "A chart that ends at a field of lanterns hanging in the dark. No one alive has sailed it.",
                     name="Star Chart: the Lantern Run", sell=False, chart="lantern_run"))
    rows.append(item("cloud_skiff", "key", "sage", 1, "A one-sail skiff with a ward-lantern at the bow. Slow, stubborn, and yours. Crosses the Starsea.",
                     sell=False, vessel={"speed": 1.0}))
    rows.append(item("storm_sloop", "key", "sage", 1, "A two-sail sloop with a comet-iron keel and a formation ward. It crosses the Starsea half again as fast.",
                     sell=False, vessel={"speed": 1.5}))
    rows.append(item("jade_elder_token", "key", "sage", 1, "An Elder's token of the Jade Sect. At any teleport stone it calls you home to the Academy, free.",
                     name="Jade Elder's Token", sell=False))
    rows.append(item("cloud_elder_token", "key", "sage", 1, "An Elder's token of the Cloud Sect. At any teleport stone it calls you home to the Monastery, free.",
                     name="Cloud Elder's Token", sell=False))
    # v1.2 · the Lantern Star Field (Act III, docs/act3_design.md): shards for the Starsea Endurance jades and the Shoals' beasts.
    rows.append(item("star_shard", "material", "sovereign", 999,
                     "A chip of fallen starlight. Levels your Starsea Endurance jades (Character > Attunement)."))
    # The Lantern Star Field's creature parts (specs/parts.py): the Drifting Shoals, Blackmast Haven and the Wyrmnest
    # Isles (v1.2 Phase B), the Nebula Deep, the Ashen Reach and the Tidebreak Front (Phases D and E).
    rows.extend(E.items("parts.lantern"))
    rows.append(item("kharns_glaive_shard", "valuable", "will", 1, "A shard of General Kharn's cinder glaive. Whether he lived or not, the Ashborn will know this piece.",
                     sell=False))
    rows.extend(E.items("parts.orbit"))   # v1.2 Phase C: the Orbit Ruins, and the Hollowed brood's ash
    rows.append(item("admirals_seal", "key", "will", 1, "Admiral Voss's seal of command: a bronze star on a chain. Every pirate lane in the Field answered to it.",
                     sell=False, quest_item=True))
    rows.append(item("wyrm_egg", "egg", "will", 1, "The last star-wyrm egg of the Wyrmnest Isles: pearl-white, warm, humming. It will not hatch for anyone below "
                     "Sphere Lord 2, however long it is warmed.", use=[], use_action="incubate", egg_species="hatchling_wyrm", egg_rarity="primordial",
                     hatch_realm="sphere_lord_2", sell=False))
    rows.append(item("lantern_incense", "other", "sovereign", 20, "Lantern-wick incense from the Star Chandlery. Burned, it draws 15 points of Hollowing out of you.",
                     use=[effect("cleanse_hollowing", amount=15)]))
    rows.append(item("storm_shard", "material", "spirit", 999,
                     "A splinter of the Expanse's storms. Levels your Storm Ward jades (Character > Attunement)."))
    for (cid, grade, rank, desc) in [("serpent_core", "earth", 2, "The core of the Riverbed Serpent; a pill ingredient."),
                                     ("guardian_stone", "earth", 2, "Heart-stone of a Stone Guardian."),
                                     ("jade_core", "heaven", 3, "A jade core from a Forgotten Monastery sentinel."),
                                     ("pebble_core", "common", 1, "A tiny earth core from a Pebble Imp.")]:
        # A core can be absorbed for Qi (it counts toward a hollow foundation), or, from rank 2, burnt as Beast Fire (S44).
        qp = cultivation(0.05 if grade == "common" else 0.1, grade)
        use_text = (" Absorb it for Qi (%s), or burn it as Beast Fire." if rank >= 2 else " Absorb it for Qi (%s). Too weak a core to burn as Beast Fire.") % cult_text(qp)
        rows.append(item(cid, "core", grade, 99, desc + use_text, core={"qp": qp, "rank": rank},
                         use=[effect("add_progress", amount=qp)], raw={"toxicity": 12}, family="accumulation"))
    # S46 beast cores: every beast of rank 2 or more drops one at 2% per rank, by its element and rank tier. A pet of
    # the same element devours it for XP; the Core Exchange buys them; they burn as Beast Fire like any core.
    for tier, rank, grade, share in (("low", 2, "earth", 0.1), ("mid", 4, "heaven", 0.15), ("high", 6, "mystic", 0.2), ("peak", 8, "spirit", 0.25)):
        qp = cultivation(share, grade)
        for el in CORE_ELEMENTS:
            rows.append(item("%s_core_%s" % (el, tier), "core", grade, 99,
                             "The core of a rank %d-%d %s beast. Absorb it for Qi (%s); a %s spirit animal devours it for growth; the Core Exchange buys it; "
                             "it burns as Beast Fire." % (rank, rank + 1, el, cult_text(qp), el), name="%s %s Core" % (tier.capitalize(), el.capitalize()),
                             core={"qp": qp, "rank": rank, "element": el, "tier": tier},
                             use=[effect("add_progress", amount=qp)], raw={"toxicity": 12}, family="accumulation"))
    # S46 pet medicine.
    rows.append(item("purifying_offering", "taming", "earth", 20, "Incense and salt bound in a lotus leaf. Offered to a weakened demonic beast, it lets the beast be tamed; offered to a Hollowed one, it cleanses the grey from it first. Use it from quick-use beside one.",
                     use=[], use_action="tame"))
    rows.append(item("beast_revival_pill", "pill", "earth", 20, "A pill for a spirit animal, not for you. It mends a Grievous Wound at once.",
                     use=[effect("heal_pet_wound")], pill={"toxicity": 0, "group": "utility"}, use_action="pet_item"))
    # S46 bloodline: a drop of a great beast's essence blood lifts a spirit animal's purity, seals a Blood
    # Contract or rerolls an unhatched egg's hidden trait; the marrow pill rerolls one weak aptitude.
    rows.append(item("beast_essence_blood", "taming", "earth", 20, "A drop of a great beast's essence blood in a jade vial. Your active spirit animal drinks it for +10 bloodline purity; it also seals a Blood Contract or rerolls one hidden trait of an egg you are warming.",
                     use=[effect("add_pet_purity", amount=10)], use_action="pet_item"))
    rows.append(item("beast_marrow_washing_pill", "pill", "earth", 20, "A pill for a spirit animal, not for you. It washes the marrow of your active animal's weakest gift and rolls it again. It leaves no toxicity. The animal must be a Juvenile before its gifts show.",
                     use=[effect("wash_pet_marrow")], pill={"toxicity": 0, "group": "utility"}, use_action="pet_item"))
    # S46 pet skill books (pet_skill_books.json): taught to an animal with a free learned slot, or over a random one.
    for bid, bname, grade, desc in PET_BOOKS:
        rows.append(item("pet_book_" + bid, "pet_book", grade, 5, desc + " Teach it on the Spirit Animals page, or use it to teach your active animal.",
                         name="Skill Book: " + bname, use=[effect("learn_pet_skill", skill=bid)], use_action="pet_item", pet_book=bid))
    rows.append(item("tiny_hollow_shard", "hollow", "common", 99, "A grey sliver that drinks warmth. Handle with care."))
    rows.append(item("hollow_shard", "hollow", "earth", 99, "A shard of the Hollow Tide. Appraise before use."))
    rows.append(item("grey_hide", "hollow", "common", 99, "Hide from a Hollowed beast, grey and cold."))
    # The Hollow Night's trophy: the eel's first defeat (enemies.py first_defeat), a rare find when it drops.
    rows.append(item("hollow_eel_fang", "hollow", "common", 99, "The Hollowed eel's fang, from the night of the storm: hooked, grey to "
                     "the root, still cold. A trader would give 80 taels for it.", name="Hollowed Eel Fang", value_override=80))
    for f, g in FISH:
        rows.append(item(f, "fish", g, 99, FISH_DESC.get(f, "A fish from the Jade River."), name="Jade Carp" if f == "jade_carp_fish" else None))
    for (sid, grade, desc) in [("manual_page", "common", "A loose technique manual page. Raises mastery beyond tier 3."),
                               ("riverbreath_scroll", "heaven", "The Riverbreath inheritance scroll: the complete method."),
                               ("lu_journal_page", "plain", "A page of Lu's journal, water-stained."),
                               ("recipe_scroll", "common", "A recipe written in a steady hand."),
                               # S48 Inner Arts: the Mission Halls teach them from these (the shop entry names the art).
                               ("inner_art_manual", "earth", "A thin book of breathing and bearing: one Inner Art, learned once.")]:
        extra = {"use": [effect("learn_method", method="riverbreath_complete")]} if sid == "riverbreath_scroll" else {}
        rows.append(item(sid, "scroll", grade, 99, desc, **extra))
    # The sect libraries lend their technique manuals through the Mission Halls (the shop entry names the technique).
    rows.append(item("technique_manual", "scroll", "earth", 99, "A library copy of one technique, learned once and returned.", icon="manual_page"))
    # Method manuals (S08): read one to learn the method; the libraries sell them by rank.
    for mid, grade, name, desc in [("stonebody_canon", "earth", "Stonebody Canon", "An earth method: slow, heavy, the body grows with it. Ceiling Spirit Awakening 9."),
                                   ("willow_breath_art", "earth", "Willow Breath Art", "A wood method that bends and returns. Ceiling Spirit Awakening 9."),
                                   ("emberheart_sutra", "earth", "Emberheart Sutra", "A fire method: fast accumulation, hot temper. Ceiling Spirit Awakening 9."),
                                   ("tidal_sovereign_scripture", "heaven", "Tidal Sovereign Scripture", "The Jade Sect's core water method. Ceiling Sage Sovereign 3."),
                                   ("nine_winds_canon", "heaven", "Nine Winds Canon", "The Cloud Sect's core wind method. Ceiling Sage Sovereign 3.")]:
        rows.append(item("manual_" + mid, "scroll", grade, 1, desc, name="%s (manual)" % name,
                         use=[effect("learn_method", method=mid)]))
    for (sid, grade, low) in [("spirit_stone_low", "earth", 100), ("spirit_stone_mid", "heaven", 1000), ("spirit_stone_high", "mystic", 10000)]:
        rows.append(item(sid, "currency_item", grade, 99, "Crystallised Qi used as money and fuel.", value_override=low))
    keys = [("river_token", "Lu's River Token. It hums when the river is troubled."), ("jade_token", "Identity token of the Jade Sect. Returns you home."),
            ("cloud_token", "Identity token of the Cloud Sect. Returns you home."), ("mudwater_key", "Opens the Mudwater Hideout gate."),
            ("entry_token", "Proof of passing a sect entry trial."), ("siege_medal", "Awarded to defenders of the Two Sects."),
            ("smuggler_ledger", "Elder Gu's secret ledger."), ("kite", "Little Dou's paper kite."),
            ("aunt_pings_ladle", "Aunt Ping's soup ladle. The gulls keep stealing it.")]
    for kid, desc in keys:
        rows.append(item(kid, "key", "plain", 1, desc, sell=False, quest_item=kid in ("kite", "smuggler_ledger", "aunt_pings_ladle"),
                         name="Aunt Ping's Ladle" if kid == "aunt_pings_ladle" else None))
    # Lost manuals (P13a, technique_plan §5): reading one finds its lost art; a second copy is a Manual Page.
    for mid, tech, grade in [("mudwater_manual", "rising_tide", "common"), ("manual_rain_of_reeds", "rain_of_reeds", "earth"),
                             ("manual_ember_burst", "ember_burst", "earth")]:
        rows.append(item(mid, "scroll", grade, 99, "A technique manual. Read it to learn %s." % titled(tech),
                         use=[effect("learn_lost_art", art=tech)]))
    for mid, tech, name, grade in LOST_SCROLLS:
        rows.append(item(mid, "scroll", grade, 99, "A scroll in an old hand. Read it to learn what it holds.", name=name, icon="riverbreath_scroll",
                         use=[effect("learn_lost_art", art=tech)]))
    rows.append(item("rubbing_kit", "key", "common", 1, "Paper, a pad and pine-soot ink for taking a rubbing from carved stone.", sell=False,
                     icon="talisman_paper"))
    # P13a (technique_plan §4.5): a whole element tree let go, after the great realm's one free reset.
    rows.append(item("clear_heart_incense", "other", "earth", 99, "Burnt while you sit, it lets a cultivator unlearn a whole tree of "
                     "realised arts, to walk it again another way.", icon="calm_heart_incense", value_override=60))
    rows.append(item("old_net", "other", "plain", 99, "A torn fishing net. Old Ma buys these.", value_override=40))
    rows.append(item("snapper_claw", "other", "common", 99, "Old Snapper's claw. Worth 40 taels to a trader.", value_override=40))
    for oid, grade, desc in [
            ("river_mud", "plain", "Thick grey mud from the riverbank. Potters and wall-menders pay a little for it."),
            ("cloth", "common", "A bolt of plain hemp cloth, for bandages, patches and tailoring."),
            ("arrows", "common", "A bundle of fletched arrows. Hunters and bandits never have enough."),
            ("bow_parts", "common", "A cracked bow limb and a spool of string. A bowyer can make something of them."),
            ("prayer_beads", "earth", "Worn sandalwood beads, smooth from years of counted breaths."),
            ("talisman_paper", "common", "Coarse yellow paper cut to a talisman's size. It takes cinnabar well."),
            ("ink", "earth", "Pine-soot ink ground with spirit water. Scribes and formation masters use it."),
            ("formation_stone", "earth", "A palm-sized stone that holds a trace of Qi: the anchor of every array."),
            ("lantern_wick", "heaven", "A wick braided with spirit silk. It burns for a month without trimming."),
            ("rice", "plain", "A sack of valley rice. Every kitchen starts here."),
            ("restoration_ink", "heaven", "Ink steeped with mending herbs: it can close a torn scripture and still hold a stroke."),
            ("fish_bait", "plain", "Worms and dough in a clay pot. The fish of the valley are not picky.")]:
        rows.append(item(oid, "material", grade, 99, desc))
    rows.append(item("calm_incense", "other", "plain", 99, "Calming incense. Burn it and meditate to steady the heart.", use=[effect("add_composure", amount=30)]))
    # Decision 45: cultivation speed a new disciple can buy. Granny Liu burns Qi-Gathering Incense in the village from
    # Bone Forging 1; Stoneford's store sells the stronger Deep Current stick from Qi Kindling 1. One stick burns at a time
    # (the same source: a new one replaces the one alight); both show on the Cultivation page's speed list.
    rows.append(item("qi_gathering_incense", "other", "plain", 99, "Burn it and sit: the smoke draws the Qi to you. Cultivation +30% for 10 minutes.",
                     use=[effect("add_modifier", stat="accumulation_rate", op="flat", value=0.3, duration=600, source="qi_incense")]))
    rows.append(item("deep_current_incense", "other", "common", 99, "A thick stick rolled with ginseng dust. Cultivation +50% for 15 minutes.",
                     use=[effect("add_modifier", stat="accumulation_rate", op="flat", value=0.5, duration=900, source="qi_incense")]))
    rows.append(item("myriad_year_calm_incense", "treasure", "heaven", 1, "Clears Heart Demons (-20) and steadies Composure for an hour. Never sold.", sell=False,
                     use=[effect("add_heart_demon", amount=-20), effect("add_modifier", stat="will", op="flat", value=20, duration=3600, source="calm_incense")]))
    # Natural treasures (Part 5): one job each, never sold.
    rows.append(item("mindwell_lotus", "treasure", "heaven", 9,
                     "Heals and shields the soul: +500 Soul, mends a soul injury, soul defence +30% for an hour. It answers once in each great realm. Never sold.",
                     sell=False, use_limit="realm",
                     use=[effect("add_soul", amount=500), effect("cure_injury", injury="soul", max_severity=3),
                          effect("add_modifier", stat="soul_defense", op="pct_add", value=0.3, duration=3600, source="mindwell_lotus")]))
    # S49 treasure births (Part 8): a Spirit Fruit ripens in a field room every fourth day; rivals and a guardian stand
    # in the way. It carries a slice of the next realm and steadies the heart.
    rows.append(item("spirit_fruit", "treasure", "heaven", 3,
                     "A fruit that ripened on Qi alone: %s at once, and heart demons -5. Never sold." % cult_text(cultivation(0.08, "heaven")), sell=False,
                     use=[progress(0.08, "heaven"), effect("add_heart_demon", amount=-5)]))
    # S49 leisure arts: a seven-string guqin. Play it (from the bag) and a steady hand calms the Qi: meditation runs
    # faster for half an hour, more the better you play.
    rows.append(item("guqin", "tool", "earth", 1, "A seven-string guqin in a cloth wrap. Play it to calm the Qi: meditation runs up to 15% faster for 30 minutes.",
                     use=[], use_action="guqin"))
    # S49 fortune deck: the wine that makes the next batch in the furnace likelier to come out Grain.
    rows.append(item("hundred_year_wine", "treasure", "earth", 5,
                     "A jar dug out from under old roots. Pour it over the furnace: your next batch of pills is likelier to come out Grain or better. Never sold.",
                     sell=False, use=[effect("grain_blessing")]))
    # S49 lifespan (display only, never a clock): longevity treasures add years to the span your realm grants.
    rows.append(item("longevity_peach", "treasure", "earth", 5,
                     "A peach of long life. Eat it and ten years are added to your lifespan. Sold only at auction.", sell=False,
                     use=[effect("add_longevity", years=10)]))
    rows.append(item("thousand_year_lingzhi", "treasure", "heaven", 1,
                     "A lingzhi that grew for a thousand years. Eat it and thirty years are added to your lifespan. Never sold.", sell=False,
                     use=[effect("add_longevity", years=30)]))
    rows.append(item("evergreen_heart_seed", "treasure", "heaven", 1,
                     "A seed with a slow pulse. Plant it in rich earth where Qi gathers: a cave abode or your sect's Back Mountain. Never sold.", sell=False))
    rows.append(item("evergreen_heart_fruit", "treasure", "heaven", 3,
                     "Eat it when gravely wounded to rise where you fell, whole. The tree bears one each season. Never sold.", sell=False, source="system"))
    rows.append(item("fuel_crystal_low", "material", "earth", 99, "Formation fuel pressed from Spirit Stone shards."))
    rows.append(item("fuel_crystal_mid", "material", "heaven", 99, "Ten low fuel crystals fused into one."))
    rows.append(item("blank_plate", "material", "earth", 99, "A blank jade plate for portable arrays."))
    rows.append(item("spirit_egg", "egg", "earth", 1, "A warm egg. Something stirs inside. Use it to start incubating.", use=[], use_action="incubate"))
    # S46: the Beast King's nest egg is Rare or better; the Beast Tide's Cloud Stag egg always hatches a Cloud Stag.
    rows.append(item("rare_spirit_egg", "egg", "heaven", 1, "An egg from a Beast King's nest, warm as a hearth. What hatches is Rare or finer.",
                     use=[], use_action="incubate", egg_rarity="rare"))
    rows.append(item("cloud_stag_egg", "egg", "heaven", 1, "A pale egg that weighs almost nothing, left by the Beast Tide. A Cloud Stag, a mount that leaps like wind, hatches from it.",
                     use=[], use_action="incubate", egg_species="cloud_stag"))
    # S46 Spirit Beast Bags: key items that carry 2 to 6 spirit animals, so they can be swapped in the field (never in a fight).
    for bid, grade, slots, bname in (("beast_bag_reed", "common", 2, "Reed Beast Bag"), ("beast_bag_hide", "earth", 3, "Hide Beast Bag"),
                                     ("beast_bag_cloud", "heaven", 4, "Cloud Beast Bag"), ("beast_bag_mist", "mystic", 5, "Mistjade Beast Bag"),
                                     ("beast_bag_star", "spirit", 6, "Starweave Beast Bag")):
        rows.append(item(bid, "tool", grade, 1, "A Spirit Beast Bag with %d quiet rooms inside. Carry that many spirit animals and swap them in the field, though never in a fight." % slots,
                         name=bname, beast_bag={"slots": slots}))
    tools = [("old_pickaxe", "plain", "mining", 1.0), ("iron_pickaxe", "common", "mining", 1.3), ("herb_sickle", "common", "gathering", 1.3),
             ("bamboo_rod", "plain", "fishing", 1.0), ("clay_pot", "plain", "cooking", 1.0),
             ("forge_hammer", "common", "smithing", 1.0), ("formation_kit", "earth", "formations", 1.0), ("needle_case", "earth", "healing", 1.0),
             ("appraisers_loupe", "common", "appraisal", 1.0), ("drying_rack", "common", "alchemy", 1.0),
             ("spirit_spade", "heaven", "transplant", 1.0), ("verdant_dew_vial", "spirit", "garden_dew", 1.0)]
    post_tools = posts.existing_tool_posts()
    for tid, grade, craft, power in tools:
        extra = {"post": post_tools[tid]} if tid in post_tools else {}
        rows.append(item(tid, "tool", grade, 1, TOOL_DESC[tid], tool={"craft": craft, "power": power},
                         icon="appraiser_loupe" if tid == "appraisers_loupe" else tid, **extra))
    # V10 Keeping Post: the post tools (four ladders to tier 8), the insects of Insect Netting, Hour Incense.
    rows += posts.tool_items(item)
    rows += posts.insect_items(item)
    rows += posts.incense_items(item)
    rows += posts.v10c_items(item)
    rows += posts.salt_items(item)
    # Treasures (gap report G2): set in the HUD's Treasure buttons (one from Heart Tempering 1, a second from
    # Spirit Awakening 1). Each is one action with a cooldown and a QI cost; none is a stat stick.
    for tid, grade, desc, t in TREASURES:
        # Soul from Spirit Awakening 1: a third of the QI cost (a starting value, S47).
        t = dict(t, soul=t["qi"] // 3)
        extra = {"sell": False} if tid == "elder_hus_talisman" else {}
        rows.append(item(tid, "treasure_art", grade, 1, desc, treasure=tid, **extra))
        TREASURE_DEFS.append(dict(t, id=tid))
    # Throwables (S47, Part 8): forged, quick-use, and any weapon family can throw them.
    rows.append(item("iron_needles", "throwable", "common", 99, "Three needles flicked at once. Light, fast, and they find the gaps in armour.",
                     use=[effect("throw", art="needle", count=3, mult=0.45, speed=760, range=380, pierce=0)], food={"group": "throw"}))
    rows.append(item("flying_knives", "throwable", "earth", 99, "A balanced throwing knife. One hard hit at range that passes through a foe.",
                     use=[effect("throw", art="knife", count=1, mult=1.2, speed=640, range=420, pierce=1)], food={"group": "throw"}))
    rows.append(item("thunderclap_pellet", "throwable", "common", 99, "A lacquered pellet packed with ore dust and pepper. It bursts where it lands: damage and knockback all around.",
                     use=[effect("throw", art="pellet", count=1, mult=1.6, speed=520, range=360, burst=120, knockback=130)], food={"group": "throw"}))
    # S44 / Part 8 new forms: a poison pill thrown from quick-use, weapon oils, a liquid for the Draught slot, baths.
    rows.append(item("viper_smoke_pill", "throwable", "common", 99, "A poison pill. Thrown, it bursts into a green cloud: 4% of max HP a second for 5 s to everything within 90.",
                     use=[effect("throw", art="smoke", count=1, mult=0.2, speed=520, range=340, burst=90,
                                 cloud={"status": "poison", "power": 0.04, "duration_s": 5})], food={"group": "throw"}))
    for oid, status, word in [("viper_oil", "poison", "Poison"), ("ember_oil", "burn", "Burn")]:
        other = "ember_oil" if oid == "viper_oil" else "viper_oil"
        rows.append(item(oid, "oil", "common", 99, "Rubbed on the blade: for 5 minutes each hit has a 20%% chance to %s. One oil at a time." % ("poison" if status == "poison" else "set the foe burning"),
                         use=[effect("cure_status", status=other), effect("apply_status", status=oid, duration=300)], food={"group": "utility"}))
    rows.append(item("riverreed_draught", "draught", "common", 9, "A liquid medicine: +30% HP and a minor body injury mended. It goes to the Draught slot and goes flat 10 minutes after it is made.",
                     use=[effect("heal", pct=0.3, over_s=3), effect("cure_injury", injury="body", max_severity=1)], draught={"toxicity": 2, "expires_s": 600}))
    for bid, grade, xp, res, tox, desc in [("copper_body_bath", "common", 600, 10, 5, "A body-trial bath of tortoise plate, mole claw and willow moss."),
                                           ("marrow_washing_bath", "earth", 1500, 20, 8, "A bath that scours the marrow: ginseng, hound fang, ape fur and Mist Lotus."),
                                           # S48 body ladder: the Jade and Gold Body baths, taught by the tier before them.
                                           ("jade_marrow_bath", "heaven", 4000, 30, 10, "A green bath of cloudtop orchid and jade scale that sets the bones like jade."),
                                           ("golden_body_bath", "mystic", 9000, 40, 12, "A bath of frost lotus and thunder horn, hot and cold at once, that gilds the body.")]:
        rows.append(item(bid, "bath", grade, 9, desc + " Soak in it at a Bath station (seclusion): +%d body XP, %d residue cleared, the pill share of your foundation 10 points lower. Too strong a bath for your body injures it." % (xp, res),
                         use=[], use_action="bath", bath={"body_xp": xp, "residue": res, "share": 0.10, "toxicity": tox, "hours": 1.0}))
    rows.append(item("calm_heart_incense", "other", "earth", 99, "Incense of prayer beads and Mist Lotus. Burn it and sit: heart demon -10.",
                     use=[effect("add_heart_demon", amount=-10)], food={"group": "utility"}))
    # The tribulation treasure (S48): held, it takes one heavenly-tribulation bolt and burns away.
    rows.append(item("lightning_rod_talisman", "talisman", "heaven", 9, "Carried through a heavenly tribulation, it draws one bolt into itself and burns away."))
    # Flight vessels (S47): what you ride when you fly. It sets the look of your flight and what the air costs.
    for vid, grade, desc, fl in VESSELS:
        rows.append(item(vid, "vessel", grade, 1, desc, flight=fl))
    # Heavenly Flames (gap report G1): one to a zone tier, taken from a boss; absorbed for good and kept in the Codex.
    for fid, grade, desc in FLAMES:
        rows.append(item(fid, "treasure", grade, 1, desc + " Absorb it: a Heavenly Flame burns under any furnace you use, for good. Never sold.",
                         sell=False, use=[], use_action="absorb_flame"))
    rows.append(item("revival_talisman", "talisman", "common", 99, "Revive where you fall: 30% HP, 5 s invulnerable. Once per 5 minutes.", value_override=15))
    rows.append(item("return_charm", "talisman", "plain", 99, "Teleports you to the last town.", use=[effect("teleport", target="last_town")]))
    rows.append(item("escape_talisman", "talisman", "common", 99, "Leaves a dungeon at once.", use=[effect("teleport", target="dungeon_exit")]))
    for g in ["common", "earth", "heaven"]:
        rows.append(item("bonding_offering_" + g, "taming", g, 99,
                         "Calms a wounded spirit beast (below 30% HP, paw-marked) so it may bond with you. Use it from quick-use beside one.",
                         name="Bonding Offering (%s)" % g.capitalize(), use=[], use_action="tame"))
    for j, attr in [("body_jade", "body"), ("swift_jade", "agility"), ("essence_jade", "essence"), ("spirit_jade", "spirit"), ("insight_jade", "insight")]:
        rows.append(item(j, "jade", "common", 99, "A Qi jade for an inlay socket. +3/+6/+10 %s at Common/Earth/Heaven." % attr, jade={"attribute": attr, "values": [3, 6, 10]}))
    # Workshop goods (S16 appraisal, research, puppetry; formations and array plates).
    # S47: what a rogue cultivator carried, sealed with their Qi. Appraisal opens it.
    rows.append(item("sealed_storage_pouch", "curio", "earth", 20, "A rogue cultivator's storage pouch, sealed with Qi that is not yours. "
                     "An appraiser can open it; there is no telling what is inside.", value_override=30, use=[], use_action="appraise",
                     appraise=[{"item": "spirit_stone_shard", "count": 4, "weight": 4}, {"item": "jade_trinket", "count": 1, "weight": 3},
                               {"item": "refining_essence", "count": 3, "weight": 3}, {"item": "manual_page", "count": 2, "weight": 2},
                               {"item": "torn_manual", "count": 1, "weight": 2}, {"item": "qi_gathering_pill", "count": 2, "weight": 1},
                               {"item": "fake_jade", "count": 2, "weight": 1}]))
    rows.append(item("dusty_curio", "curio", "common", 99, "An old trinket of uncertain worth. Appraise it to learn what it really is.", value_override=15, use=[], use_action="appraise"))
    rows.append(item("jade_trinket", "valuable", "common", 99, "A small carving of real river jade.", value_override=60))
    rows.append(item("tinkerers_gear", "valuable", "common", 99, "A brass gear from a clockwork bird, lost on the chimney top of Artisan Row. "
                     "Worth a few taels to anyone, and a great deal to the tinkerer.", value_override=40, name="Tinkerer's Gear"))
    rows.append(item("string_of_old_coins", "valuable", "plain", 99, "Coins from a dynasty nobody remembers. Still silver.", value_override=25))
    rows.append(item("fake_jade", "valuable", "plain", 99, "Green glass. Half the valley's jade is glass.", value_override=1))
    rows.append(item("torn_manual", "scroll", "earth", 99, "A water-stained manual, half its characters gone. A librarian's bench can restore it.", value_override=30))
    rows.append(item("spirit_wood", "material", "common", 99, "Pale wood that holds a trace of Qi. Puppet frames are cut from it."))
    rows.append(item("puppet_core", "material", "earth", 99, "A carved jade heart that lets a puppet follow simple orders."))
    # S48 Array Plates, quick-deployed in a fight: each lays a small array at your feet for a few seconds. The
    # Formation Dao lengthens them (+10% at tier 1) and sharpens the killing array (+20% a tier).
    rows.append(item("array_plate", "formation", "earth", 20, "A guarding array for 12 s: while you stand inside its ring, +15% Physical Defense.",
                     use=[{"kind": "deploy_array", "array": "guard", "radius": 150, "duration": 12, "defense": 0.15}]))
    rows.append(item("killing_array_plate", "formation", "earth", 20, "A killing array for 10 s: every foe inside its ring takes 50% of your Qi Attack each second.",
                     use=[{"kind": "deploy_array", "array": "killing", "radius": 160, "duration": 10, "mult": 0.5}]))
    rows.append(item("binding_array_plate", "formation", "earth", 20, "A binding array for 10 s: every foe inside its ring is slowed by 40%.",
                     use=[{"kind": "deploy_array", "array": "binding", "radius": 160, "duration": 10, "slow": 0.4}]))
    rows.extend(E.items("pills"))   # specs/pills.py
    rows.extend(foods())
    # v1.2 Phase D · the Copperjaw Beetle swarm: a box of beetles that grows on ore, online or off.
    rows.append(item("copperjaw_box", "other", "will", 1, "A lacquered box of Copperjaw beetles. Feed it ore and the swarm grows, an hour at a time, "
                     "even while you are away. Open it and for 8 s the swarm chews every foe near you, the bigger it is the harder "
                     "(Wood foes shrug off half). It comes home after, and rests 30 s.", use=[], use_action="swarm", sell=False, ilv=92))
    rows.append(item("sphere_comprehension_stone", "treasure", "will", 1, "A stone that holds a folded world. The Observatory's keeper gives it to those who have seen their own Sphere in the stars; a Will Manifest 3 needs it to become a Sphere Lord.", sell=False, ilv=95))
    rows.extend(E.items("pills.later"))   # the Law and Monarch pills
    E.end("items")
    entries("items.json", rows, bag_kinds=BAG_KINDS)
    entries("treasures.json", TREASURE_DEFS)   # S47: what each treasure does, keyed by its item id
    return rows


FAMILY_APPEARANCE = {"gauntlets": "gauntlets", "jian": "sword", "spear": "spear", "short_blade": "dagger", "staff": "staff", "bow": "bow",
                     # S47 v1.1 families
                     "heavy_sabre": "sabre", "fan": "fan", "flute": "flute",
                     # P7b (item_plan §2.9): the brush and the bell at every grade, so the formation master and the bell musician
                     # hold a weapon of their own from Level 1 (G4)
                     "brush": "brush", "bell": "bell"}
# The attribute a family asks for at each grade (the bow Agility, the staff and heavy sabre Body, the flute and brush
# Insight, the bell Essence).
FAMILY_ATTRIBUTE = {"bow": "agility", "staff": "body", "heavy_sabre": "body", "flute": "insight", "brush": "insight", "bell": "essence"}
ATTRIBUTE_REQ = {"plain": 8, "common": 18, "earth": 30, "heaven": 50, "mystic": 65, "spirit": 80, "sage": 92, "sovereign": 100, "will": 110}
# Garment dyes (data/parts.json "_dyes"): plain hemp is undyed brown, better cloth takes richer colour.
GRADE_DYE = {"plain": {"robe": "earth", "trousers": "earth"}, "common": {"robe": "grey", "trousers": "ink"},
             "earth": {"robe": "indigo", "trousers": "ink"}, "heaven": {"robe": "cloud", "trousers": "grey"},
             "mystic": {"robe": "white", "trousers": "jade"}, "spirit": {"robe": "indigo", "trousers": "cloud"},
             "sage": {"robe": "ochre", "trousers": "crimson"}, "sovereign": {"robe": "rose", "trousers": "indigo"},
             "will": {"robe": "white", "trousers": "ink"}}
# P7b (item_plan §2.9, G1): Sovereign and Will, the Lantern Star Field's grades: driftsteel weapons and starsilk armour,
# lanternsteel and lanternsilk.
GRADE_WORD = {"plain": "training", "common": "iron", "earth": "jadeiron", "heaven": "cloudsteel", "mystic": "mistjade", "spirit": "stormsteel",
              "sage": "sunsteel", "sovereign": "driftsteel", "will": "lanternsteel"}
ARMOUR = {
    "plain": {"hat": ("plain_straw_hat", "Plain Straw Hat", "straw"), "robe": ("hemp_robe", "Hemp Robe", "sleeveless"),
              "trousers": ("hemp_trousers", "Hemp Trousers", "loose"), "boots": ("straw_sandals", "Straw Sandals", "slippers")},
    "common": {"hat": ("bamboo_hat", "Bamboo Hat", "straw"), "robe": ("cotton_robe", "Cotton Robe", "disciple"),
               "trousers": ("cotton_trousers", "Cotton Trousers", "straight"), "boots": ("cloth_boots", "Cloth Boots", "boots")},
    "earth": {"hat": ("jadeiron_hat", "Jadeiron Circlet", "headband"), "robe": ("jadeiron_robe", "Jadeiron-Trimmed Robe", "cardigan"),
              "trousers": ("jadeiron_trousers", "Jadeiron-Trimmed Trousers", "martial"), "boots": ("jadeiron_boots", "Jadeiron Greaves", "folded")},
    "heaven": {"hat": ("cloudsilk_hat", "Cloudsilk Band", "tied"), "robe": ("cloudsilk_robe", "Cloudsilk Robe", "vneck"),
               "trousers": ("cloudsilk_trousers", "Cloudsilk Trousers", "cuffed"), "boots": ("cloudsilk_boots", "Cloudsilk Boots", "boots")},
    "mystic": {"hat": ("mistjade_hat", "Mistjade Circlet", "headband"), "robe": ("mistjade_robe", "Mistjade Robe", "scholar"),
               "trousers": ("mistjade_trousers", "Mistjade Trousers", "scholar"), "boots": ("mistjade_boots", "Mistjade Boots", "folded")},
    # Spirit grade (Azure Expanse, Sage realm)
    "spirit": {"hat": ("stormsilk_hat", "Stormsilk Crown", "guan"), "robe": ("stormsilk_robe", "Stormsilk Robe", "vneck"),
               "trousers": ("stormsilk_trousers", "Stormsilk Trousers", "martial"), "boots": ("stormsilk_boots", "Stormsilk Boots", "boots")},
    # Sage grade (Sunscar, Sage Sovereign realm): sunsilk worked with desert glass; the veiled hat keeps the sun off.
    "sage": {"hat": ("sunsilk_hat", "Sunsilk Veil", "weimao"), "robe": ("sunsilk_robe", "Sunsilk Robe", "scholar"),
             "trousers": ("sunsilk_trousers", "Sunsilk Trousers", "cuffed"), "boots": ("sunsilk_boots", "Sunsilk Boots", "folded")},
    # Sovereign grade (the Drifting Shoals to the Orbit Ruins): starsilk, woven from star jellies' silk.
    "sovereign": {"hat": ("starsilk_hat", "Starsilk Band", "tied"), "robe": ("starsilk_robe", "Starsilk Robe", "disciple"),
                  "trousers": ("starsilk_trousers", "Starsilk Trousers", "straight"), "boots": ("starsilk_boots", "Starsilk Slippers", "slippers")},
    # Will grade (the Ashen Reach to the Lantern Heart): lanternsilk, cut for the Wardens' watch.
    "will": {"hat": ("lanternsilk_hat", "Lanternsilk Crown", "guan"), "robe": ("lanternsilk_robe", "Lanternsilk Robe", "cardigan"),
             "trousers": ("lanternsilk_trousers", "Lanternsilk Trousers", "martial"), "boots": ("lanternsilk_boots", "Lanternsilk Boots", "boots")},
}
# P7b (item_plan §2.9, G5, G6): banded ladders of pet gear and furnaces, forged at the forge. A pet piece gains 1% of its
# stat a grade (defence half that) from the first piece of its kind; a furnace's heat, batch, filter and yield by grade.
PET_LADDER = {"pet_collar": ("Collar", "common", {"hp": 0.10}, "earth", "+{hp}% HP for the animal that wears it."),
              "pet_talisman": ("Beast Talisman", "earth", {"attack": 0.10, "defence": 0.05}, "common",
                               "+{attack}% attack and +{defence}% defence for the animal that wears it."),
              "pet_saddle": ("Saddle", "common", {"mount_speed": 0.10}, "earth", "A mount wearing it carries you {mount_speed}% faster.")}
PET_STEP = {"hp": 0.01, "attack": 0.01, "defence": 0.005, "mount_speed": 0.01}
BANDED_FURNACES = [
    ("stormsteel_furnace", "spirit", "Stormsteel Furnace", "Blue-black stormsteel that drinks the lightning's heat. Ten pills to a batch.",
     {"band": 0.11, "batch": 10, "filter": 0.33, "yield": 0.16}),
    ("sunsteel_furnace", "sage", "Sunsteel Furnace", "Sunsteel set with desert glass that holds the fire's glow. Eleven pills to a batch.",
     {"band": 0.12, "batch": 11, "filter": 0.36, "yield": 0.17}),
    ("driftsteel_furnace", "sovereign", "Driftsteel Furnace", "Driftsteel walls lined with ground driftglass. Eleven pills to a batch, and little ash gets through.",
     {"band": 0.13, "batch": 11, "filter": 0.39, "yield": 0.18}),
    ("lanternsteel_furnace", "will", "Lanternsteel Furnace", "Cast from a lantern cage's metal; the fire in it never quite goes out. Twelve pills to a batch.",
     {"band": 0.14, "batch": 12, "filter": 0.42, "yield": 0.20}),
]


def artifact(id, slot, grade, name, appearance, family=None, ilv=None, icon=None, **extra):
    row = {"id": id, "name": name, "slot": slot, "grade": grade, "ilv": ilv or MID_ILV[grade], "appearance": appearance,
           "energy_type": {"plain": "none", "common": "primal_qi", "earth": "primal_qi", "heaven": "true_qi", "mystic": "true_qi", "spirit": "sage_qi",
                           "sage": "sage_qi", "sovereign": "sage_qi", "will": "sage_qi"}[grade],
           "sockets": {"plain": 0, "common": 0, "earth": 1, "heaven": 1, "mystic": 2, "spirit": 2, "sage": 3, "sovereign": 3, "will": 3}[grade], "icon": icon or id, "type": "equipment",
           "stack": 1}
    if family:
        row["family"] = family
    row.update(extra)
    return row


def build_artifacts():
    rows = []
    for grade, word in GRADE_WORD.items():
        for fam, look in FAMILY_APPEARANCE.items():
            id = "%s_%s" % (word, fam)
            name = "%s %s" % (word.capitalize(), {"short_blade": "Short Blade", "jian": "Jian", "heavy_sabre": "Heavy Sabre"}.get(fam, titled(fam)))
            extra = {}
            if grade == "plain":
                # The weapon slot is open from the start, and a training weapon asks nothing of its wearer: a first-hour
                # foe may drop one (grades.json drop.starter), and the Weapon Hall hands out three.
                extra["ilv"] = 5
                extra["source"] = ["weapon_hall"]
            if fam in FAMILY_ATTRIBUTE:
                extra["attribute_req"] = {FAMILY_ATTRIBUTE[fam]: ATTRIBUTE_REQ[grade]}
            rows.append(artifact(id, "weapon", grade, name, look, fam, **extra))
    for grade, slots in ARMOUR.items():
        for slot, (id, name, look) in slots.items():
            extra = {"dye": GRADE_DYE[grade][slot]} if slot in ("robe", "trousers") else {}
            rows.append(artifact(id, slot, grade, name, look, ilv=(1 if id == "plain_straw_hat" else None), **extra))
    # Decision 45: the bag starts at 50 (stats.json bag.base); each gourd up the ladder adds its 5 on top of that, as it
    # added them on top of 25 before (the Starter Spirit Gourd 50, from 25; the Lantern Gourd 90, from 65).
    gourds = [("starter_gourd", "plain", "Starter Spirit Gourd", 0, 5), ("bamboo_gourd", "common", "Bamboo Gourd", 5, 8),
              ("jadeiron_gourd", "earth", "Jadeiron Gourd", 10, 10), ("cloud_gourd", "heaven", "Cloud Gourd", 15, 12),
              ("mistjade_gourd", "mystic", "Mistjade Gourd", 20, 15), ("stormsteel_gourd", "spirit", "Stormsteel Gourd", 25, 16),
              ("sunsteel_gourd", "sage", "Sunsteel Gourd", 30, 18), ("driftglass_gourd", "sovereign", "Driftglass Gourd", 35, 19),
              ("lantern_gourd", "will", "Lantern Gourd", 40, 20)]
    for id, grade, name, extra_slots, quick in gourds:
        rows.append(artifact(id, "gourd", grade, name, "none", gourd={"bag": BAG_BASE + extra_slots, "quick": quick}, ilv=(1 if grade == "plain" else None),
                             **({"source": ["story"]} if id == "starter_gourd" else {})))   # the starting kit (AccountAuthority)
    rows.append(artifact("mistjade_cape", "cape", "mystic", "Mistjade Cape", "solid", resist=["water", "wind"], named=tag("general", "valley")))
    for fid, grade, name, icon, desc, stats in FURNACES:
        extra = {"sell": False} if stats.get("named") else {}
        rows.append(artifact(fid, "tool_furnace", grade, name, "none", icon=icon, desc=desc, furnace=stats, sockets=0,
                             energy_type="none", ilv=(1 if grade == "plain" else None), named=tag("alchemist", "valley"), **extra))
    for fid, grade, name, desc, stats in BANDED_FURNACES:
        rows.append(artifact(fid, "tool_furnace", grade, name, "none", desc=desc, furnace=stats, sockets=0, energy_type="none"))
    rows.append(artifact("cloud_talisman", "talisman", "heaven", "Cloud Talisman", "none", named=tag("general", "valley")))
    # S46 pet gear: a Collar, a Talisman and (for mounts) a Saddle, forged from beast materials and enhanced at the
    # forge (+10% of the base a level). Worn by a spirit animal, never by you.
    for gid, gslot, grade, gname, stats, desc in [
            ("bone_collar", "pet_collar", "common", "Bone Collar", {"hp": 0.10}, "Boar hide and mole claws. +10% HP for the animal that wears it."),
            ("scale_talisman", "pet_talisman", "earth", "Scale Talisman", {"attack": 0.10, "defence": 0.05}, "Serpent and jade scales on a cord. +10% attack and +5% defence for the animal that wears it."),
            ("reed_saddle", "pet_saddle", "common", "Reed Saddle", {"mount_speed": 0.10}, "Woven reed on boar hide. A mount wearing it carries you 10% faster.")]:
        rows.append(artifact(gid, gslot, grade, gname, "none", desc=desc, pet_gear=stats, sockets=0, energy_type="none", ilv=MID_ILV[grade],
                             named=tag("beast", "valley")))
    grades = list(MID_ILV)
    for gslot, (word, base_grade, base, first, text) in PET_LADDER.items():
        for grade in grades[grades.index(first):grades.index("will") + 1]:
            if grade == base_grade:
                continue
            stats = {k: round(v + PET_STEP[k] * (grades.index(grade) - grades.index(base_grade)), 3) for k, v in base.items()}
            rows.append(artifact("%s_%s" % (GRADE_WORD[grade], word.lower().replace(" ", "_")), gslot, grade, "%s %s" % (GRADE_WORD[grade].capitalize(), word),
                                 "none", sockets=0, energy_type="none", pet_gear=stats, desc=text.format(**{k: "%g" % (v * 100) for k, v in stats.items()})))
    # Set pieces reuse appearances and grade icons.
    for sect, look in [("jade_current", ("headband", "cardigan", "martial", "folded")), ("cloudpiercing", ("tied", "vneck", "cuffed", "boots"))]:
        for slot, app in zip(["hat", "robe", "trousers", "boots"], look):
            dye = {"jade_current": ("jade", "ink"), "cloudpiercing": ("cloud", "indigo")}[sect]
            extra = {"dye": dye[0] if slot == "robe" else dye[1]} if slot in ("robe", "trousers") else {}
            rows.append(artifact("%s_%s" % (sect, slot), slot, "earth", "%s %s" % (titled(sect), slot.capitalize()), app,
                                 icon="jadeiron_%s" % slot, set=sect, source=["sect_shop"], **extra))
    rows.append(artifact("mudwater_cleaver", "weapon", "common", "Mudwater Cleaver", "sword", "jian", icon="iron_jian", set="mudwater", ilv=18,
                         named=tag("sword", "valley")))
    rows.append(artifact("mudwater_robe", "robe", "common", "Mudwater Robe", "sleeveless", icon="cotton_robe", set="mudwater", ilv=18, dye="earth"))
    for slot, app in [("hat", "tied"), ("robe", "scholar"), ("boots", "slippers")]:
        rows.append(artifact("drowned_%s" % slot, slot, "earth", "Drowned Abbot %s" % slot.capitalize(), app, icon="jadeiron_%s" % slot, set="drowned_abbot", ilv=30,
                             **({"dye": "ink"} if slot == "robe" else {})))
    for slot, app in [("robe", "vneck"), ("trousers", "cuffed"), ("boots", "boots")]:
        rows.append(artifact("crane_%s" % slot, slot, "heaven", "Crane %s" % slot.capitalize(), app, icon="cloudsilk_%s" % slot, set="crane", ilv=45,
                             **({"dye": "white" if slot == "robe" else "cloud"} if slot in ("robe", "trousers") else {})))
    # v1.2 Phase D · the brush and the bell, from the Tidebreak Bastion's armoury (the Lantern Star Field's first weapons
    # of their families): a Sage-grade pair and a Will-grade pair.
    for wid, fam, grade, name, look, attr, desc, named in [
            ("ink_warden_brush", "brush", "sage", "Ink-Warden's Brush", "brush", "insight",
             "A Warden scribe's brush, its hairs set in black lacquer. Every technique written with it leaves a talisman on the foe.",
             tag("formation", "lantern", "space", ["qi_attack_pct"], MID_ILV["sage"])),
            ("starwrit_brush", "brush", "will", "Starwrit Brush", "brush", "insight",
             "Its tip was dipped in lantern ash. The characters it writes glow for a breath after.",
             tag("formation", "lantern", "space", ["qi_attack_pct"], MID_ILV["will"])),
            ("wardens_handbell", "bell", "sage", "Warden's Hand-bell", "bell", "essence",
             "A bronze bell rung on the Tidebreak walls at every change of watch. Its strikes ring out on both sides.",
             tag("musician", "lantern", "metal", ["melody_power"], MID_ILV["sage"])),
            ("tidebreak_bell", "bell", "will", "Tidebreak Bell", "bell", "essence",
             "Cast from a lantern cage that fell in the Breach. The Hollow does not like its note.",
             tag("musician", "lantern", "metal", ["melody_power"], MID_ILV["will"]))]:
        rows.append(artifact(wid, "weapon", grade, name, look, fam, desc=desc, source=["bastion_armoury"], named=named,
                             attribute_req={attr: {"sage": 92, "will": 110}[grade]}))
    # S47 rogue cultivators drop what they carry in the open.
    rows.append(artifact("serpent_tongue_jian", "weapon", "earth", "Serpent-Tongue Jian", "sword", "jian", icon="jadeiron_jian", ilv=30,
                         named=tag("sword", "valley", "metal", ["penetration"], 30),
                         desc="A rogue cultivator's jian, its blade forked at the tip. Whoever it belonged to, it is yours now."))
    # S47 Artifact Spirit depth: each relic's spirit has a control demand (the Spirit its full power needs), a skill
    # (a strike every so many hits once awake), a favourite gift, the place it wakes and its one-line barks.
    moon = {"name": "Moon Spirit", "strength": 26, "control": 60, "favourite": "mist_lotus", "wake_room": "ml_lake_shrine",
            "effect": {"stat": "qi_attack", "op": "pct_add", "value": 0.08},
            "skill": {"name": "Moonlit Crescent", "every_hits": 8, "mult": 1.6, "damage_type": "qi", "element": "water", "reach": 300, "art": "moon_crescent"},
            "barks": {"awake": ["The lake remembers the moon. So do I.", "At last, a hand that listens."],
                      "kill": ["Clean as moonlight.", "One less shadow on the water.", "Again. Like the tide."],
                      "gift": ["Mist lotus... I dreamed of it for a hundred years.", "Mm. That is kind."],
                      "devour": ["A small blade. It remembers little.", "I take its edge into mine."],
                      "low_hp": ["Breathe. The water does not hurry.", "Step back, and let me shine."],
                      "refuse": ["Your spirit is a puddle. I will not pour into it."]}}
    blade = {"name": "Blade Spirit", "strength": 30, "control": 80, "favourite": "refining_essence", "wake_room": "ds_abbots_sanctum",
             "effect": {"stat": "crit_damage", "op": "flat", "value": 0.1},
             "skill": {"name": "Waking Edge", "every_hits": 10, "mult": 2.2, "damage_type": "physical", "element": "metal", "reach": 220, "art": "flying_sword"},
             "barks": {"awake": ["I slept in the dark long enough. Show me the light.", "Hold me steady."],
                       "kill": ["Ha. Too slow.", "The Abbot swung harder than that.", "Next."],
                       "gift": ["Refined. Good. I can taste the fire in it.", "You feed me well."],
                       "devour": ["Crude steel. Still, it had a heart.", "More."],
                       "low_hp": ["Do not fall before I have had my fill.", "Get up. We are not finished."],
                       "refuse": ["Soft hands. Soft soul. Put me down."]}}
    rows.append(artifact("moonlit_blade", "weapon", "heaven", "The Moonlit Blade", "sword", "jian", icon="cloudsteel_jian", ilv=50,
                         relic=True, named=tag("sword", "valley"), unique="Awake spirit: +8% Qi attack; Moonlit Crescent every 8 hits", spirit=moon))
    rows.append(artifact("sleeping_blade", "weapon", "heaven", "The Sleeping Blade", "sword", "jian", icon="cloudsteel_jian", ilv=52,
                         relic=True, named=tag("sword", "valley"), unique="Awake spirit: +10% crit damage; Waking Edge every 10 hits", spirit=blade))
    # S47 legendary chains: each legend, restored from its three pieces, is Mystic grade with a gift of its own; awakened
    # at +10 it gains its own skill in place of its family's.
    for ch in LEGENDS:
        rows.append(artifact(ch["weapon"], "weapon", "mystic", ch["name"], FAMILY_APPEARANCE[ch["family"]], ch["family"], icon="mistjade_" + ch["family"], ilv=64,
                             legend={"chain": ch["id"], "effect": ch["effect"], "skill": ch["skill"]}, desc=ch["lore"], sell=False,
                             named=tag(next(a for a, x in ARCHETYPES.items() if ch["family"] in x["families"]), "expanse")))
    # S47 imitation relics (v1.1): a forge copy of a boss relic keeps 60% of its unique effect, always on, with no spirit,
    # no binding and no control demand.
    for iid, name, of, sp in [("moonshadow_jian", "Moonshadow Jian", "moonlit_blade", moon), ("drowsing_edge", "Drowsing Edge", "sleeping_blade", blade)]:
        fx = dict(sp["effect"])
        fx["value"] = round(fx["value"] * 0.6, 4)
        rows.append(artifact(iid, "weapon", "heaven", name, "sword", "jian", icon="cloudsteel_jian", ilv=48,
                             imitation={"of": of, "share": 0.6, "effect": fx}, named=tag("sword", "valley"),
                             desc="A forge copy of %s. It keeps six parts in ten of the original's gift, and no spirit." % ("the Moonlit Blade" if of == "moonlit_blade" else "the Sleeping Blade")))
    entries("artifacts.json", rows)
    return rows


def build():
    build_items()
    build_artifacts()


if __name__ == "__main__":
    raise SystemExit(run_cli(build))
