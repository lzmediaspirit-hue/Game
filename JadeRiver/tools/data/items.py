"""S14/S15/Part 8: items.json (non-equipment) and artifacts.json (equipment bases)."""
from common import entries, titled, req, c

MID_ILV = {"plain": 5, "common": 14, "earth": 27, "heaven": 45, "mystic": 59, "spirit": 68, "sage": 77}


def item(id, type, grade="plain", stack=99, desc="", name=None, icon=None, **extra):
    row = {"id": id, "name": name or titled(id), "type": type, "grade": grade, "ilv": extra.pop("ilv", MID_ILV.get(grade, 5)),
           "stack": stack, "icon": icon or id, "desc": desc}
    row.update(extra)
    return row


HERBS = [
    ("willow_moss", "plain", "Soft moss from willow roots. The base of many remedies."),
    ("riverreed_ginseng_10", "common", "A ten-year riverreed ginseng root.", "Riverreed Ginseng (10 yr)"),
    ("riverreed_ginseng_100", "earth", "A century-old root with golden hairs; strong and rare.", "Riverreed Ginseng (100 yr)"),
    ("ember_pepper", "common", "A fiery red pepper that warms the meridians."),
    ("mist_lotus", "earth", "A pale lotus that only opens in waterfall mist."),
    ("cloudtop_orchid", "heaven", "An orchid that grows on ledges only flyers can reach."),
    ("soulbell_flower", "heaven", "Its bell-shaped petals ring softly against the soul."),
    ("frost_lotus", "spirit", "A lotus that blooms in snow on Rimefrost Heights. Cold to the touch, clear to the mind."),
    ("ember_cactus", "sage", "A cactus flower that stores the Sunscar sun. It glows like a coal long after dusk."),
]
# S44 / Part 8 herb nature: a hot herb moves the Extraction band up 8% of its range, a cold one down. Roles are the
# recipe slots a herb can fill (Principal, Minister, Assistant, Envoy); an Alchemy Dao tier-5 substitute must match both.
HERB_NATURE = {"willow_moss": ("neutral", ["assistant", "envoy"]),
               "riverreed_ginseng_10": ("hot", ["principal", "minister", "assistant"]),
               "riverreed_ginseng_100": ("hot", ["principal", "minister", "assistant"]),
               "ember_pepper": ("hot", ["minister", "assistant", "envoy"]),
               "mist_lotus": ("cold", ["principal", "minister", "assistant"]),
               "cloudtop_orchid": ("cold", ["principal", "minister"]),
               "soulbell_flower": ("neutral", ["principal", "assistant", "envoy"]),
               "frost_lotus": ("cold", ["principal", "minister"]),
               "ember_cactus": ("hot", ["principal", "minister"])}
NATURE_TEXT = {"hot": " A hot herb: it drives the Extraction band up.", "cold": " A cold herb: it draws the Extraction band down.",
               "neutral": ""}
ORES = [
    ("copper_ore", "plain", "Soft copper ore from the quarry rim.", "Copper"),
    ("riverstone", "common", "Dense river-polished stone used in forging and building."),
    ("jadeiron", "earth", "Iron veined with jade; it holds Qi paths well."),
    ("spirit_stone_shard", "earth", "A splinter of crystallised Qi. Fuel and small change.", "Spirit Stone Shard"),
    ("cloudsteel_ore", "heaven", "Feather-light ore from the sky ledges."),
    ("mystic_ore", "mystic", "Ore that hums faintly in cold wind."),
    ("stormsteel_ore", "spirit", "Blue-black ore from where lightning strikes the same ground twice."),
    ("sunglass_ore", "sage", "Desert glass the Sunscar sun fused out of the dunes. It holds heat and light like a lamp.", "Sunglass"),
]
# S47 talisman craft: inks and papers (Part 8).
TALISMAN_MATS = [("cinnabar", "common", "Red mercury ore ground to powder: the ink every talisman begins with. Stoneford General Store sells it.", "Cinnabar"),
                 ("beast_blood_ink", "earth", "Ink cut with a beast's blood; it holds a stronger charge than cinnabar alone.", "Beast-Blood Ink"),
                 ("spirit_paper", "earth", "Talisman paper steeped with Mist Lotus until it drinks Qi.", "Spirit Paper")]
# The talismans themselves: (id, grade, kind, desc). Numbers live in talismans.json.
# Item text: one line on where it comes from and what it is for (the UI shows it under the name).
BEAST_DESC = {
    "ore_dust": "Glittering grit from an Ironclaw Mole's tunnels. Smiths pack it into Thunderclap Pellets.",
    "crab_shell": "A mud-brown shell from a Mudshell Crab. Traders buy it to burn for lime.",
    "rat_tail": "A Reedtail Rat's tail. Ink-makers boil it down for its binding fat.",
    "boar_hide": "Bristly hide from a Wild Boarlet. Smiths wrap iron hilts with it.",
    "tough_meat": "Stringy meat from a big beast. Slow-stewed, it builds a body up.",
    "toad_oil": "Slick oil wrung from a Mossback Toad's skin. Cooks fold it into dumplings.",
    "moss": "Damp moss scraped from a Mossback Toad's back. Qi Gathering Pills start with it.",
    "beetle_shell": "A Rock Beetle's plate, hard as slate. Needle-smiths and Iron Wall talismans both use it.",
    "tortoise_plate": "A slab of Stone Tortoise shell. Bone Strengthening Pills and Body Jades need it.",
    "mole_claw": "A digging claw from an Ironclaw Mole, still sharp enough to scratch iron.",
    "frog_leg": "A Reed Frog's leg. Jade-smiths set its spring into a Swift Jade.",
    "leech_oil": "Oil pressed from a Marsh Leech. Qi Restoration Pills and Essence Jades use it.",
    "bamboo_shoot": "A tender shoot a Bamboo Monkey was hoarding. Traders buy them by the basket.",
    "viper_fang": "A Green Viper's fang, still beaded with venom. It binds a sealing talisman's stroke.",
    "venom_sac": "A Green Viper's venom sac. Antidotes start here, and so do poisons.",
    "thorn_hide": "Hide from a Thornback Boar, studded with thorn-like bristles. Tiger Blood Pills need it.",
    "hound_fang": "A Mud Hound's fang. Boiled with rat tail, it makes beast-blood ink.",
    "jade_scale": "A green scale from a Jade Carp, cool to the touch. Jadeiron smiths and alchemists both want it.",
    "tide_shell": "A Tide Crab's shell, ridged like waves. It rings when tapped.",
    "pearl": "A small river pearl. Traders buy them; alchemists grind them for clear pills.",
    "lizard_scale": "A slick scale from a Rapids Lizard. Water runs off it without wetting it.",
    "serpent_scale": "A heavy scale from a river serpent. Traders pay well for an unchipped one.",
    "vulture_plume": "A grey Mist Vulture plume. A Wind Step talisman's stroke needs its lightness.",
    "cloud_feather": "A white Cloudwing Crane feather that drifts upward when dropped.",
    "storm_feather": "A Stormwing Hawk's feather that crackles in dry air. Thunder talismans need it.",
    "ape_fur": "Thick fur from a Cliff Ape, warm enough for the high passes.",
    "mist_pelt": "A Mist Wolf's pelt, grey and hard to look at directly.",
    "mirror_dust": "Silver dust shed by a Mirror Wisp. It remembers what it last reflected.",
    "soul_wax": "Wax from a Weeping Lantern that burns without heat. Soul Soothing Pills need it.",
    "hollow_antler": "A Hollow Stag's antler, grey and cold. Handle it with gloves.",
    "roc_feather": "A great flight feather from a Cloudpeak Roc, as long as a spear.",
}
FISH_DESC = {
    "river_minnow": "A silver minnow from the Jade River shallows. Bait, or a quick snack.",
    "reed_perch": "A striped perch that hides among the reeds.",
    "jade_carp_fish": "A green-gold carp from the deeper pools. Said to bring luck to a household.",
    "river_eel": "A slippery river eel. Smoked, it keeps for a month.",
    "mist_trout": "A pale trout from the cold falls pool, lean and full of Qi.",
    "rapids_salmon": "A strong salmon caught where the river runs white.",
    "moon_carp": "A carp that shines faintly in the dark. It bites only at night, in any water.",
}
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
    "drying_rack": "A folding bamboo rack. Dried herbs keep longer and refine cleaner.",
}

TALISMANS = [("flame_talisman", "common", "attack", "Thrown, it bursts into a sheet of fire: 180% fire damage at the talisman's own grade within 80."),
             ("thunder_talisman", "earth", "attack", "Thrown, it calls a bolt: 240% thunder damage at the talisman's own grade, and Shock."),
             ("iron_wall_talisman", "common", "defence", "Burned, it wraps you in iron Qi: a shield that absorbs 20% of your max HP for 6 s."),
             ("wind_step_talisman", "common", "movement", "Burned, it lends you one free dodge within 60 s, cooldown or not."),
             ("veil_talisman", "earth", "movement", "Burned, it hides you for 10 s: monsters that have not found you pass you by."),
             ("binding_talisman", "earth", "sealing", "Thrown, it roots the nearest foe for 2 s. Bosses shrug it off.")]
# S47 gear upkeep: what Salvage gives back, and what steadies an enhancement.
REFINING = [("refining_essence", "common", "The refined Qi of a salvaged piece. The forge feeds it into an enhancement to steady it.", "Refining Essence")]
BEAST = ["ore_dust", "crab_shell", "rat_tail", "boar_hide", "tough_meat", "toad_oil", "moss", "beetle_shell", "tortoise_plate",
         "mole_claw", "frog_leg", "leech_oil", "bamboo_shoot", "viper_fang", "venom_sac", "thorn_hide", "hound_fang", "jade_scale",
         "tide_shell", "pearl", "lizard_scale", "serpent_scale", "vulture_plume", "cloud_feather", "storm_feather", "ape_fur",
         "mist_pelt", "mirror_dust", "soul_wax", "hollow_antler", "roc_feather"]
BEAST_GRADE = {"ore_dust": "plain", "crab_shell": "plain", "rat_tail": "plain", "boar_hide": "plain", "tough_meat": "plain",
               "toad_oil": "plain", "moss": "plain", "beetle_shell": "plain", "tortoise_plate": "plain", "mole_claw": "plain",
               "frog_leg": "plain", "leech_oil": "plain", "bamboo_shoot": "common", "viper_fang": "common", "venom_sac": "common",
               "thorn_hide": "common", "hound_fang": "common", "jade_scale": "earth", "tide_shell": "earth", "pearl": "earth",
               "lizard_scale": "earth", "serpent_scale": "earth", "vulture_plume": "earth", "cloud_feather": "heaven",
               "storm_feather": "heaven", "ape_fur": "heaven", "mist_pelt": "heaven", "mirror_dust": "heaven", "soul_wax": "heaven",
               "hollow_antler": "mystic", "roc_feather": "mystic"}
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


# S44 · Pill families for lifetime resistance (Part 8). Pills not listed are exempt.
PILL_FAMILIES = {"qi_gathering_pill": "accumulation", "qi_flow_pill": "accumulation", "bone_strengthening_pill": "body",
                 "clear_mind_pill": "insight", "soul_soothing_pill": "soul", "foundation_guard_pill": "support", "cleansing_pill": "support"}
# The unique effect a Pill Soul of each recipe carries (S44 soul_effect; the effects live in grades.json pill.soul).
SOUL_BY_GROUP = {"healing": "mend_meridians", "restoration": "mend_meridians", "buff": "iron_skin", "utility": "steady_heart"}
SOUL_EFFECT = {"clear_mind_pill": "clear_mind", "soul_soothing_pill": "clear_mind", "mind_lake_opening_pill": "clear_mind",
               "method_conversion_pill": "clear_mind", "bone_strengthening_pill": "iron_skin", "tiger_blood_pill": "iron_skin"}


def pills():
    P = []

    def pill(id, grade, mark, desc, toxicity, effects, cause=None, group="restoration", **extra):
        fam = PILL_FAMILIES.get(id)
        if fam:
            extra["family"] = fam
        P.append(item(id, "pill", grade, 99, desc, pill={"mark": mark, "toxicity": toxicity, "cause": cause, "group": group},
                      use=effects, soul_effect=SOUL_EFFECT.get(id, SOUL_BY_GROUP.get(group, "steady_heart")), **extra))
    pill("healing_pill", "common", "heart", "Cures a minor body injury and restores 30% HP over 5 s.", 5,
         [effect("cure_injury", injury="body", max_severity=1), effect("heal", pct=0.3, over_s=5)], cause="structure", group="healing")
    pill("qi_restoration_pill", "common", "spiral", "Restores 40% QI and cures a minor meridian injury.", 5,
         [effect("restore_resource", pool="qi", pct=0.4), effect("cure_injury", injury="meridian", max_severity=1)], cause="energy")
    pill("qi_gathering_pill", "common", "spiral_up", "Adds 8% of the current stage's need.", 10,
         [effect("add_progress", pct_of_need=0.08)], cause="energy", group="utility")
    pill("bone_strengthening_pill", "common", "bone", "Adds 150 body XP.", 8, [effect("add_body_xp", amount=150)], cause="structure", group="utility")
    pill("purging_pill", "common", "leaf", "Purges 30 toxicity.", 0, [effect("add_toxicity", amount=-30)], group="utility")
    pill("viper_antidote", "common", "leaf", "Cures poison.", 0, [effect("cure_status", status="poison")], group="utility")
    pill("tiger_blood_pill", "common", "flame", "+20% attack for 60 s, then exhaustion (-20% for 60 s).", 12,
         [effect("add_modifier", stat="physical_attack", op="pct_add", value=0.2, duration=60, source="tiger_blood"),
          effect("apply_status", status="exhausted", delay=60, duration=60)], group="buff")
    pill("cleansing_pill", "common", "gate", "Support item: lowers the risk of Heaven's Cleansing by one step.", 10,
         [], cause="environment", group="utility", support={"risk": -1, "event": "heavens_cleansing"})
    pill("foundation_guard_pill", "earth", "gate", "Breakthrough support: lowers risk by one step.", 12, [],
         cause="structure", group="utility", support={"risk": -1})
    pill("clear_mind_pill", "earth", "lamp", "+50% insight rate for 30 minutes.", 8,
         [effect("add_modifier", stat="insight_rate", op="flat", value=0.5, duration=1800, source="clear_mind")], cause="understanding", group="buff")
    pill("meridian_reversal_pill", "earth", "arrows_loop", "Resets all meridian points.", 10, [effect("reset_meridians")], group="utility")
    pill("method_conversion_pill", "earth", "arrows", "Halves the cost of switching cultivation methods.", 10, [], group="utility", method_conversion=True)
    pill("qi_refining_pill", "earth", "spiral", "Required to break through from Heart Tempering 9 to Cloud Stride 1.", 15, [], cause="material", group="utility")
    pill("soul_soothing_pill", "heaven", "eye", "Cures a soul injury; +20% Soul for 10 minutes.", 8,
         [effect("cure_injury", injury="soul", max_severity=3), effect("add_modifier", stat="max_soul", op="pct_add", value=0.2, duration=600, source="soul_soothing"),
          effect("add_soul", amount=50)], cause="soul")
    pill("mind_lake_opening_pill", "heaven", "eye_gate", "Required to break through from Cloud Stride 9 to Spirit Awakening 1.", 15, [], cause="material", group="utility")
    pill("sage_condensing_pill", "mystic", "knot", "Required to break through from Heaven Glimpse 3 to Sage 1.", 20, [], cause="material", group="utility")
    pill("sovereign_settling_pill", "sage", "knot", "Settles a new Sage Sovereign stage at once: its consolidation ends.", 15,
         [effect("settle_consolidation")], cause="structure", group="utility")
    pill("will_tempering_pill", "sage", "eye", "+40 Will for 30 minutes: another's Presence weighs less on you.", 12,
         [effect("add_modifier", stat="will", op="flat", value=40, duration=1800, source="will_tempering")], cause="soul", group="buff")
    pill("storm_blood_pill", "mystic", "bolt", "+4 attunement in the zone you stand in for 30 minutes.", 10,
         [effect("add_modifier", stat="attunement_bonus", op="flat", value=4, duration=1800, source="storm_blood")], group="buff")
    # S44 / Part 8 new forms. The Qi Flow Pill's debt comes due when its hour is up (`then`, applied on buff_expired).
    pill("qi_flow_pill", "earth", "spiral_up", "+20% accumulation for 60 minutes. When it wears off, the toxicity it held back comes due: +15.", 5,
         [effect("add_modifier", stat="accumulation_rate", op="flat", value=0.2, duration=3600, source="qi_flow_pill")],
         cause="energy", group="buff", then=[effect("add_toxicity", amount=15)])
    # S44 hidden recipes, found only by experiment.
    pill("sunfire_pill", "common", "flame", "Found by experiment: ginseng and Ember Pepper. +12% attack for 10 minutes.", 8,
         [effect("add_modifier", stat="physical_attack", op="pct_add", value=0.12, duration=600, source="sunfire_pill")], group="buff")
    pill("stillwater_pill", "earth", "drop_leaf", "Found by experiment: Mist Lotus, Soulbell and willow moss. Composure +40, heart demon -5.", 6,
         [effect("add_composure", amount=40), effect("add_heart_demon", amount=-5)], cause="soul", group="utility")
    pill("cloudstep_pill", "heaven", "arrows", "Found by experiment: Cloudtop Orchid and willow moss. +10% move speed for 20 minutes.", 8,
         [effect("add_modifier", stat="move_speed", op="pct_add", value=0.10, duration=1200, source="cloudstep_pill")], group="buff")
    pill("murky_pill", "plain", "drop_leaf", "What a failed experiment leaves: grey, gritty, and good for nothing but a stomach ache. A trader gives a tael for it.", 8,
         [], group="utility", value_override=1)
    return P


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


# Eaten raw (gap report G1): 30% of the herb's pill at twice its toxicity. An emergency, and the reason
# alchemy exists. Herbs never rot.
RAW_HERB = {
    "willow_moss": ([effect("heal", pct=0.09, over_s=5)], 10),
    "riverreed_ginseng_10": ([effect("add_progress", pct_of_need=0.024)], 20),
    "riverreed_ginseng_100": ([effect("add_progress", pct_of_need=0.05)], 30),
    "ember_pepper": ([effect("add_modifier", stat="physical_attack", op="pct_add", value=0.06, duration=60, source="raw_ember_pepper")], 24),
    "mist_lotus": ([effect("add_modifier", stat="insight_rate", op="flat", value=0.15, duration=540, source="raw_mist_lotus")], 16),
    "cloudtop_orchid": ([effect("add_body_xp", amount=90)], 30),
    "soulbell_flower": ([effect("add_soul", amount=15)], 16),
    "frost_lotus": ([effect("cure_injury", injury="meridian", max_severity=1), effect("add_composure", amount=20)], 30),
    "ember_cactus": ([effect("heal", pct=0.1, over_s=5)], 30),
}


def raw_family(effects):
    """A raw herb counts toward the family of what it builds up (S44)."""
    kinds = {e["kind"] for e in effects}
    for kind, fam in (("add_progress", "accumulation"), ("add_body_xp", "body"), ("add_soul", "soul"), ("add_insight", "insight")):
        if kind in kinds:
            return fam
    return ""


def build_items():
    rows = []
    TREASURE_DEFS.clear()
    for h in HERBS:
        raw = RAW_HERB.get(h[0])
        extra = {"use": raw[0], "raw": {"toxicity": raw[1]}} if raw else {}
        if raw:
            fam = raw_family(raw[0])
            if fam:
                extra["family"] = fam
        nature, roles = HERB_NATURE[h[0]]
        extra["nature"] = nature
        extra["roles"] = roles
        rows.append(item(h[0], "herb", h[1], 99, h[2] + NATURE_TEXT[nature] + (" Can be eaten raw in need: weak, and hard on the meridians." if raw else ""),
                         name=h[3] if len(h) > 3 else None, **extra))
    for o in ORES:
        rows.append(item(o[0], "ore", o[1], 99, o[2], name=o[3] if len(o) > 3 else None))
    for o in REFINING + TALISMAN_MATS:
        rows.append(item(o[0], "material", o[1], 99, o[2], name=o[3]))
    for tid, grade, kind, desc in TALISMANS:
        rows.append(item(tid, "talisman", grade, 20, desc, use=[], use_action="talisman", talisman=kind))
    # A Shattered Relic (S47): the Drowned Abbot's old blade in pieces; a master smith restores it.
    rows.append(item("shattered_moon_blade", "relic_shard", "heaven", 1, "The pieces of a jian that once held a spirit, pale as moonlight. "
                     "A smith of Expert rank could restore it at the forge.", name="Shattered Moon Blade", sell=False, restores="moonlit_blade"))
    for b in BEAST:
        rows.append(item(b, "beast_part", BEAST_GRADE[b], 99, BEAST_DESC.get(b, "A material taken from a valley beast.")))
    # Azure Expanse beasts (Act II)
    rows.append(item("spark_pelt", "beast_part", "spirit", 99, "A golden pelt that snaps with static. Taken from Spark Weasels."))
    rows.append(item("thunder_horn", "beast_part", "spirit", 99, "A thunderhorn's horn. It still holds a charge."))
    rows.append(item("rime_fang", "beast_part", "spirit", 99, "A frost lynx's fang, rimed with ice that never melts."))
    rows.append(item("snow_ape_hide", "beast_part", "spirit", 99, "A thick white hide from a Snow Ape. Warm even in a blizzard."))
    rows.append(item("dragonet_scale", "beast_part", "spirit", 99, "An azure scale from a carp halfway to becoming a dragon."))
    rows.append(item("sentinel_core", "material", "spirit", 99, "The polished heart-stone of a River Sentinel. Water turns slowly inside it."))
    rows.append(item("mirror_eye", "material", "spirit", 99, "One of the Thousand-Eye Toad's mirror eyes. It still shows what it last saw."))
    rows.append(item("kite_silk", "beast_part", "spirit", 99, "Painted silk from a Wind Kite. It still pulls toward the wind."))
    rows.append(item("harpy_plume", "beast_part", "spirit", 99, "A russet plume from a Canyon Harpy's crest, barred like a hawk's."))
    rows.append(item("scorpion_stinger", "beast_part", "spirit", 99, "A Sandstorm Scorpion's stinger, a bead of amber venom still inside."))
    rows.append(item("worm_glass_tooth", "beast_part", "sage", 99, "A tooth of clear desert glass from a Dune Worm's ringed maw."))
    rows.append(item("terracotta_shard", "material", "spirit", 99, "A shard of a Terracotta Warden. The clay is warm, as if fired yesterday."))
    rows.append(item("sun_crown_fragment", "material", "sage", 99, "A gold ray broken from the Tomb King's sun crown. It never cools."))
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
    rows.append(item("comet_iron", "material", "sage", 99, "Iron hammered from a pirate hull that once flew through a comet's tail. It rings like a bell."))
    rows.append(item("alliance_badge", "beast_part", "spirit", 99, "A Nine Peaks disciple's jade badge, its peak scratched out by a deserter's knife.",
                     name="Scratched Alliance Badge"))
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
    rows.append(item("storm_shard", "material", "spirit", 999,
                     "A splinter of the Expanse's storms. Levels your Storm Ward jades (Character > Attunement)."))
    for (cid, grade, rank, desc) in [("serpent_core", "earth", 2, "The core of the Riverbed Serpent; a pill ingredient."),
                                     ("guardian_stone", "earth", 2, "Heart-stone of a Stone Guardian."),
                                     ("jade_core", "heaven", 3, "A jade core from a Forgotten Monastery sentinel."),
                                     ("pebble_core", "common", 1, "A tiny earth core from a Pebble Imp.")]:
        # A core can be absorbed for Qi (it counts toward a hollow foundation), or, from rank 2, burnt as Beast Fire (S44).
        qp = 0.05 if grade == "common" else 0.1
        use_text = " Absorb it for Qi, or burn it as Beast Fire." if rank >= 2 else " Absorb it for Qi. Too weak a core to burn as Beast Fire."
        rows.append(item(cid, "core", grade, 99, desc + use_text, core={"qp_pct": qp, "rank": rank},
                         use=[effect("add_progress", pct_of_need=qp)], raw={"toxicity": 12}, family="accumulation"))
    rows.append(item("tiny_hollow_shard", "hollow", "common", 99, "A grey sliver that drinks warmth. Handle with care."))
    rows.append(item("hollow_shard", "hollow", "earth", 99, "A shard of the Hollow Tide. Appraise before use."))
    rows.append(item("grey_hide", "hollow", "common", 99, "Hide from a Hollowed beast, grey and cold."))
    for f, g in FISH:
        rows.append(item(f, "fish", g, 99, FISH_DESC.get(f, "A fish from the Jade River."), name="Jade Carp" if f == "jade_carp_fish" else None))
    for (sid, grade, desc) in [("manual_page", "common", "A loose technique manual page. Raises mastery beyond tier 3."),
                               ("riverbreath_scroll", "heaven", "The Riverbreath inheritance scroll: the complete method."),
                               ("lu_journal_page", "plain", "A page of Lu's journal, water-stained."),
                               ("recipe_scroll", "common", "A recipe written in a steady hand.")]:
        extra = {"use": [effect("learn_method", method="riverbreath_complete")]} if sid == "riverbreath_scroll" else {}
        rows.append(item(sid, "scroll", grade, 99, desc, **extra))
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
    for mid, tech, grade in [("mudwater_manual", "rising_tide", "common"), ("manual_rain_of_reeds", "rain_of_reeds", "earth"),
                             ("manual_ember_burst", "ember_burst", "earth")]:
        rows.append(item(mid, "scroll", grade, 99, "A technique manual. Read it to learn %s." % titled(tech),
                         use=[effect("learn_technique", technique=tech)]))
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
    rows.append(item("myriad_year_calm_incense", "treasure", "heaven", 1, "Clears Heart Demons (-20) and steadies Composure for an hour. Never sold.", sell=False,
                     use=[effect("add_heart_demon", amount=-20), effect("add_modifier", stat="will", op="flat", value=20, duration=3600, source="calm_incense")]))
    # Natural treasures (Part 5): one job each, never sold.
    rows.append(item("mindwell_lotus", "treasure", "heaven", 9,
                     "Heals and shields the soul: +500 Soul, mends a soul injury, soul defence +30% for an hour. It answers once in each great realm. Never sold.",
                     sell=False, use_limit="realm",
                     use=[effect("add_soul", amount=500), effect("cure_injury", injury="soul", max_severity=3),
                          effect("add_modifier", stat="soul_defense", op="pct_add", value=0.3, duration=3600, source="mindwell_lotus")]))
    rows.append(item("evergreen_heart_seed", "treasure", "heaven", 1,
                     "A seed with a slow pulse. Plant it in rich earth where Qi gathers: a cave abode or your sect's Back Mountain. Never sold.", sell=False))
    rows.append(item("evergreen_heart_fruit", "treasure", "heaven", 3,
                     "Eat it when gravely wounded to rise where you fell, whole. The tree bears one each season. Never sold.", sell=False))
    rows.append(item("fuel_crystal_low", "material", "earth", 99, "Formation fuel pressed from Spirit Stone shards."))
    rows.append(item("fuel_crystal_mid", "material", "heaven", 99, "Ten low fuel crystals fused into one."))
    rows.append(item("blank_plate", "material", "earth", 99, "A blank jade plate for portable arrays."))
    rows.append(item("spirit_egg", "egg", "earth", 1, "A warm egg. Something stirs inside. Use it to start incubating.", use=[], use_action="incubate"))
    tools = [("old_pickaxe", "plain", "mining", 1.0), ("iron_pickaxe", "common", "mining", 1.3), ("herb_sickle", "common", "gathering", 1.3),
             ("bamboo_rod", "plain", "fishing", 1.0), ("clay_pot", "plain", "cooking", 1.0),
             ("forge_hammer", "common", "smithing", 1.0), ("formation_kit", "earth", "formations", 1.0), ("needle_case", "earth", "healing", 1.0),
             ("appraisers_loupe", "common", "appraisal", 1.0), ("drying_rack", "common", "alchemy", 1.0)]
    for tid, grade, craft, power in tools:
        rows.append(item(tid, "tool", grade, 1, TOOL_DESC[tid], tool={"craft": craft, "power": power},
                         icon="appraiser_loupe" if tid == "appraisers_loupe" else tid))
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
                                           ("marrow_washing_bath", "earth", 1500, 20, 8, "A bath that scours the marrow: ginseng, hound fang, ape fur and Mist Lotus.")]:
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
    rows.append(item("array_plate", "formation", "earth", 20, "A portable one-use protection formation: +15% defence for two minutes.",
                     use=[{"kind": "add_modifier", "stat": "physical_defense", "op": "pct_add", "value": 0.15, "duration": 120, "source": "array_plate"}]))
    rows.extend(pills())
    rows.extend(foods())
    rows.append(item("sphere_comprehension_stone", "treasure", "will", 1, "A stone that holds a folded world. (Later zones.)", sell=False, ilv=95))
    rows.append(item("law_condensing_pill", "pill", "law", 99, "Converts Sage Qi toward Law Qi. (Later zones.)", ilv=105, pill={"mark": "arrows", "toxicity": 20, "group": "utility"}, use=[]))
    rows.append(item("law_touching_pill", "pill", "law", 99, "Supports the attempt to touch a World Law. (Later zones.)", ilv=106, pill={"mark": "gate", "toxicity": 20, "group": "utility"}, use=[]))
    rows.append(item("monarch_condensing_pill", "pill", "monarch", 99, "Helps the Monarch conversion. (Later zones.)", ilv=115, pill={"mark": "knot", "toxicity": 25, "group": "utility"}, use=[]))
    rows.append(item("sigil_anchor_pill", "pill", "monarch", 99, "Anchors the Dao Sigil. (Later zones.)", ilv=120, pill={"mark": "knot", "toxicity": 25, "group": "utility"}, use=[]))
    entries("items.json", rows)
    entries("treasures.json", TREASURE_DEFS)   # S47: what each treasure does, keyed by its item id
    return rows


FAMILY_APPEARANCE = {"gauntlets": "none", "jian": "sword", "spear": "spear", "short_blade": "dagger", "staff": "staff", "bow": "bow"}
# Garment dyes (data/parts.json "_dyes"): plain hemp is undyed brown, better cloth takes richer colour.
GRADE_DYE = {"plain": {"robe": "earth", "trousers": "earth"}, "common": {"robe": "grey", "trousers": "ink"},
             "earth": {"robe": "indigo", "trousers": "ink"}, "heaven": {"robe": "cloud", "trousers": "grey"},
             "mystic": {"robe": "white", "trousers": "jade"}, "spirit": {"robe": "indigo", "trousers": "cloud"},
             "sage": {"robe": "ochre", "trousers": "crimson"}}
GRADE_WORD = {"plain": "training", "common": "iron", "earth": "jadeiron", "heaven": "cloudsteel", "mystic": "mistjade", "spirit": "stormsteel",
              "sage": "sunsteel"}
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
}


def artifact(id, slot, grade, name, appearance, family=None, ilv=None, icon=None, **extra):
    row = {"id": id, "name": name, "slot": slot, "grade": grade, "ilv": ilv or MID_ILV[grade], "appearance": appearance,
           "energy_type": {"plain": "none", "common": "primal_qi", "earth": "primal_qi", "heaven": "true_qi", "mystic": "true_qi", "spirit": "sage_qi",
                           "sage": "sage_qi"}[grade],
           "sockets": {"plain": 0, "common": 0, "earth": 1, "heaven": 1, "mystic": 2, "spirit": 2, "sage": 3}[grade], "icon": icon or id, "type": "equipment",
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
            name = "%s %s" % (word.capitalize(), {"short_blade": "Short Blade", "jian": "Jian"}.get(fam, titled(fam)))
            extra = {}
            if grade == "plain":
                extra["ilv"] = 5
                extra["requires"] = req(c("level_at_least", level=3), c("unlock", system="weapons"))
                extra["source"] = ["weapon_hall"]
            if fam == "bow":
                extra["attribute_req"] = {"agility": {"plain": 8, "common": 18, "earth": 30, "heaven": 50, "mystic": 65, "spirit": 80, "sage": 92}[grade]}
            if fam == "staff":
                extra["attribute_req"] = {"body": {"plain": 8, "common": 18, "earth": 30, "heaven": 50, "mystic": 65, "spirit": 80, "sage": 92}[grade]}
            rows.append(artifact(id, "weapon", grade, name, look, fam, **extra))
    for grade, slots in ARMOUR.items():
        for slot, (id, name, look) in slots.items():
            extra = {"dye": GRADE_DYE[grade][slot]} if slot in ("robe", "trousers") else {}
            rows.append(artifact(id, slot, grade, name, look, ilv=(1 if id == "plain_straw_hat" else None), **extra))
    gourds = [("starter_gourd", "plain", "Starter Spirit Gourd", 25, 5), ("bamboo_gourd", "common", "Bamboo Gourd", 30, 8),
              ("jadeiron_gourd", "earth", "Jadeiron Gourd", 35, 10), ("cloud_gourd", "heaven", "Cloud Gourd", 40, 12),
              ("mistjade_gourd", "mystic", "Mistjade Gourd", 45, 15), ("stormsteel_gourd", "spirit", "Stormsteel Gourd", 50, 16),
              ("sunsteel_gourd", "sage", "Sunsteel Gourd", 55, 18)]
    for id, grade, name, bag, quick in gourds:
        rows.append(artifact(id, "gourd", grade, name, "none", gourd={"bag": bag, "quick": quick}, ilv=(1 if grade == "plain" else None)))
    rows.append(artifact("mistjade_cape", "cape", "mystic", "Mistjade Cape", "solid", resist=["water", "wind"]))
    for fid, grade, name, icon, desc, stats in FURNACES:
        extra = {"sell": False} if stats.get("named") else {}
        rows.append(artifact(fid, "tool_furnace", grade, name, "none", icon=icon, desc=desc, furnace=stats, sockets=0,
                             energy_type="none", ilv=(1 if grade == "plain" else None), **extra))
    rows.append(artifact("cloud_talisman", "talisman", "heaven", "Cloud Talisman", "none"))
    # Set pieces reuse appearances and grade icons.
    for sect, look in [("jade_current", ("headband", "cardigan", "martial", "folded")), ("cloudpiercing", ("tied", "vneck", "cuffed", "boots"))]:
        for slot, app in zip(["hat", "robe", "trousers", "boots"], look):
            dye = {"jade_current": ("jade", "ink"), "cloudpiercing": ("cloud", "indigo")}[sect]
            extra = {"dye": dye[0] if slot == "robe" else dye[1]} if slot in ("robe", "trousers") else {}
            rows.append(artifact("%s_%s" % (sect, slot), slot, "earth", "%s %s" % (titled(sect), slot.capitalize()), app,
                                 icon="jadeiron_%s" % slot, set=sect, source=["sect_shop"], **extra))
    rows.append(artifact("mudwater_cleaver", "weapon", "common", "Mudwater Cleaver", "sword", "jian", icon="iron_jian", set="mudwater", ilv=18))
    rows.append(artifact("mudwater_robe", "robe", "common", "Mudwater Robe", "sleeveless", icon="cotton_robe", set="mudwater", ilv=18, dye="earth"))
    for slot, app in [("hat", "tied"), ("robe", "scholar"), ("boots", "slippers")]:
        rows.append(artifact("drowned_%s" % slot, slot, "earth", "Drowned Abbot %s" % slot.capitalize(), app, icon="jadeiron_%s" % slot, set="drowned_abbot", ilv=30,
                             **({"dye": "ink"} if slot == "robe" else {})))
    for slot, app in [("robe", "vneck"), ("trousers", "cuffed"), ("boots", "boots")]:
        rows.append(artifact("crane_%s" % slot, slot, "heaven", "Crane %s" % slot.capitalize(), app, icon="cloudsilk_%s" % slot, set="crane", ilv=45,
                             **({"dye": "white" if slot == "robe" else "cloud"} if slot in ("robe", "trousers") else {})))
    # S47 rogue cultivators drop what they carry in the open.
    rows.append(artifact("serpent_tongue_jian", "weapon", "earth", "Serpent-Tongue Jian", "sword", "jian", icon="jadeiron_jian", ilv=30,
                         desc="A rogue cultivator's jian, its blade forked at the tip. Whoever it belonged to, it is yours now."))
    rows.append(artifact("moonlit_blade", "weapon", "heaven", "The Moonlit Blade", "sword", "jian", icon="cloudsteel_jian", ilv=50,
                         relic=True, unique="Awake spirit: +8% Qi attack",
                         spirit={"name": "Moon Spirit", "strength": 26, "effect": {"stat": "qi_attack", "op": "pct_add", "value": 0.08}}))
    rows.append(artifact("sleeping_blade", "weapon", "heaven", "The Sleeping Blade", "sword", "jian", icon="cloudsteel_jian", ilv=52,
                         relic=True, unique="Awake spirit: +10% crit damage",
                         spirit={"name": "Blade Spirit", "strength": 30, "effect": {"stat": "crit_damage", "op": "flat", "value": 0.1}}))
    entries("artifacts.json", rows)
    return rows


if __name__ == "__main__":
    build_items()
    build_artifacts()
