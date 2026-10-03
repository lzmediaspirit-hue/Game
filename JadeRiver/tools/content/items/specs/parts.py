"""Creature parts: what a beast or a monster leaves behind (beast parts, and the monster materials crafted the same way),
one family a zone. A part names the creatures it comes from, `part(id, grade, desc, [creature, ...])`: the monster
engine (E2, tools/data/enemies.py) writes the drop rows, and the item engine's --check finds the part in each named
creature's loot table, so a part no creature drops is reported, not shipped. `drop=True` is a part many creatures carry.
A boss's or a monster's material is `type="material"`; everything else here is a `beast_part`.
"""
from content.items.dsl import family, member


def part(id, grade, desc, creatures, name=None, type=None, section=None, **sources):
    m = member(grade, grade, id=id, desc=desc, name=name, sources=dict(sources, drop=creatures))
    if type:
        m["type"] = type
    if section:
        m["section"] = section
    return m


FAMILIES = [
    # The Jade River valley (Act I): every beast of the valley's fields and dungeons.
    family("part.valley", kind="part", members=[
        part("ore_dust", "plain", "Glittering grit from an Ironclaw Mole's tunnels. Smiths pack it into Thunderclap Pellets.", ["ironclaw_mole"],
             shop={"formation_guild": dict(price=8, flag="guild_formations_adept")}),
        part("crab_shell", "plain", "A mud-brown shell from a Mudshell Crab. Traders buy it to burn for lime.", ["mudshell_crab"]),
        part("rat_tail", "plain", "A Reedtail Rat's tail. Ink-makers boil it down for its binding fat.", ["reedtail_rat"]),
        part("boar_hide", "plain", "Bristly hide from a Wild Boarlet. Smiths wrap iron hilts with it.", ["wild_boarlet"],
             shop={"old_ma": dict(rotation=True)}, reward=True),
        part("tough_meat", "plain", "Stringy meat from a big beast. Slow-stewed, it builds a body up.", True,
             shop={"oasis_keeper": {}, "herders_camp": {}}),
        part("toad_oil", "plain", "Slick oil wrung from a Mossback Toad's skin. Cooks fold it into dumplings.", ["mossback_toad"]),
        part("moss", "plain", "Damp moss scraped from a Mossback Toad's back. Qi Gathering Pills start with it.", ["mossback_toad"]),
        part("beetle_shell", "plain", "A Rock Beetle's plate, hard as slate. Needle-smiths and Iron Wall talismans both use it.", ["rock_beetle"]),
        part("tortoise_plate", "plain", "A slab of Stone Tortoise shell. Bone Strengthening Pills and Body Jades need it.", ["stone_tortoise"]),
        part("mole_claw", "plain", "A digging claw from an Ironclaw Mole, still sharp enough to scratch iron.", ["ironclaw_mole"]),
        part("frog_leg", "plain", "A Reed Frog's leg. Jade-smiths set its spring into a Swift Jade.", ["reed_frog"]),
        part("leech_oil", "plain", "Oil pressed from a Marsh Leech. Qi Restoration Pills and Essence Jades use it.", ["marsh_leech"], reward=True),
        part("bamboo_shoot", "common", "A tender shoot a Bamboo Monkey was hoarding. Traders buy them by the basket.", ["bamboo_monkey"], reward=True),
        part("viper_fang", "common", "A Green Viper's fang, still beaded with venom. It binds a sealing talisman's stroke.", ["green_viper"]),
        part("venom_sac", "common", "A Green Viper's venom sac. Antidotes start here, and so do poisons.", ["green_viper"]),
        part("thorn_hide", "common", "Hide from a Thornback Boar, studded with thorn-like bristles. Tiger Blood Pills need it.", ["thornback_boar"]),
        part("hound_fang", "common", "A Mud Hound's fang. Boiled with rat tail, it makes beast-blood ink.", ["mud_hound"]),
        part("jade_scale", "earth", "A green scale from a Jade Carp, cool to the touch. Jadeiron smiths and alchemists both want it.", ["jade_carp"],
             shop={"alchemist_guild": dict(price=30, flag="guild_alchemy_adept")}, reward=True),
        part("tide_shell", "earth", "A Tide Crab's shell, ridged like waves. It rings when tapped.", ["tide_crab"]),
        # The valley's first beasts carry a pearl as an early surprise (enemies.py EARLY_FINDS).
        part("pearl", "earth", "A small river pearl. Traders buy them; alchemists grind them for clear pills.", True,
             shop={"mei_qing": dict(price=40, realm="heart_tempering_5")}, reward=True),
        part("lizard_scale", "earth", "A slick scale from a Rapids Lizard. Water runs off it without wetting it.", ["rapids_lizard"]),
        part("serpent_scale", "earth", "A heavy scale from a river serpent. Traders pay well for an unchipped one.", ["boulder_serpent", "riverbed_serpent"]),
        part("vulture_plume", "earth", "A grey Mist Vulture plume. A Wind Step talisman's stroke needs its lightness.", ["mist_vulture"]),
        part("cloud_feather", "heaven", "A white Cloudwing Crane feather that drifts upward when dropped.", ["cloudwing_crane"], reward=True),
        part("storm_feather", "heaven", "A Stormwing Hawk's feather that crackles in dry air. Thunder talismans need it.", ["stormwing_hawk"]),
        part("ape_fur", "heaven", "Thick fur from a Cliff Ape, warm enough for the high passes.", ["cliff_ape"]),
        part("mist_pelt", "heaven", "A Mist Wolf's pelt, grey and hard to look at directly.", ["mist_wolf"]),
        part("mirror_dust", "heaven", "Silver dust shed by a Mirror Wisp. It remembers what it last reflected.", ["mirror_wisp"]),
        part("soul_wax", "heaven", "Wax from a Weeping Lantern that burns without heat. Soul Soothing Pills need it.", ["weeping_lantern"], reward=True),
        part("hollow_antler", "mystic", "A Hollow Stag's antler, grey and cold. Handle it with gloves.", ["hollow_stag"]),
        part("roc_feather", "mystic", "A great flight feather from a Cloudpeak Roc, as long as a spear.", ["cloudpeak_roc"],
             shop={"port_apothecary": dict(price=12, rotation=True)}),
    ]),
    # The Azure Expanse (Act II): the Thunderhorn Plains, Rimefrost Heights, Mirrorwater Lake, the Gale Canyons and Sunscar.
    family("part.expanse", kind="part", members=[
        part("spark_pelt", "spirit", "A golden pelt that snaps with static. Taken from Spark Weasels.", ["spark_weasel"], section="parts.expanse"),
        part("thunder_horn", "spirit", "A thunderhorn's horn. It still holds a charge.", ["thunderhorn_rhino"], section="parts.expanse", reward=True),
        part("rime_fang", "spirit", "A frost lynx's fang, rimed with ice that never melts.", ["frost_lynx"], section="parts.expanse"),
        part("snow_ape_hide", "spirit", "A thick white hide from a Snow Ape. Warm even in a blizzard.", ["snow_ape"], section="parts.expanse"),
        part("dragonet_scale", "spirit", "An azure scale from a carp halfway to becoming a dragon.", ["azure_carp_dragonet"], section="parts.expanse",
             reward=True),
        part("sentinel_core", "spirit", "The polished heart-stone of a River Sentinel. Water turns slowly inside it.", ["river_sentinel"], type="material",
             section="parts.expanse", shop={"free_market": dict(price=30, rotation=True)}, mail=True, auction=True),
        part("mirror_eye", "spirit", "One of the Thousand-Eye Toad's mirror eyes. It still shows what it last saw.", ["thousand_eye_toad"], type="material",
             section="parts.expanse", shop={"free_market": dict(price=70, rotation=True)}, auction=True),
        part("kite_silk", "spirit", "Painted silk from a Wind Kite. It still pulls toward the wind.", ["wind_kite"], section="parts.expanse", reward=True),
        part("harpy_plume", "spirit", "A russet plume from a Canyon Harpy's crest, barred like a hawk's.", ["canyon_harpy"], section="parts.expanse"),
        part("scorpion_stinger", "spirit", "A Sandstorm Scorpion's stinger, a bead of amber venom still inside.", ["sandstorm_scorpion"],
             section="parts.expanse"),
        part("worm_glass_tooth", "sage", "A tooth of clear desert glass from a Dune Worm's ringed maw.", ["dune_worm"], section="parts.expanse"),
        part("terracotta_shard", "spirit", "A shard of a Terracotta Warden. The clay is warm, as if fired yesterday.", ["terracotta_warden"],
             type="material", section="parts.expanse"),
        part("sun_crown_fragment", "sage", "A gold ray broken from the Tomb King's sun crown. It never cools.", ["tomb_king"], type="material",
             section="parts.expanse"),
    ]),
    # Phase E · the Starsea: the pirates' hull iron and the deserters' badges.
    family("part.starsea", kind="part", members=[
        part("comet_iron", "sage", "Iron hammered from a pirate hull that once flew through a comet's tail. It rings like a bell.",
             ["pirate_captain", "pirate_gunner", "starsea_pirate"], type="material", section="parts.starsea", chest=True, reward=True),
        part("alliance_badge", "spirit", "A Nine Peaks disciple's jade badge, its peak scratched out by a deserter's knife.", ["nine_peaks_disciple"],
             name="Scratched Alliance Badge", section="parts.starsea"),
    ]),
    # v1.2 · the Lantern Star Field (Act III): the Drifting Shoals, the Wyrmnest Isles, Blackmast Haven, the Nebula Deep,
    # the Ashen Reach and the Tidebreak Front; then the Orbit Ruins.
    family("part.lantern", kind="part", members=[
        part("jelly_silk", "sovereign", "A Star Jellyfish's trailing silk. It glows for a day after the jelly dies, and stings for two.", ["star_jellyfish"],
             section="parts.lantern", shop={"lanternfall_goods": dict(price=2, rotation=True)}),
        part("comet_plume", "sovereign", "A tail feather of a Comet Sparrow, still warm, trailing sparks when it is waved.", ["comet_sparrow"],
             section="parts.lantern"),
        part("star_powder", "sovereign", "Pirate gunpowder cut with star-dust. It burns blue and bangs gold.", ["admiral_voss", "pirate_gunner"],
             type="material", section="parts.lantern"),
        part("guardian_scale", "sovereign", "A bronze plate from a Nest Guardian's shell, set with a crystal that still glows.", ["nest_guardian"],
             section="parts.lantern"),
        part("eel_essence", "will", "The bright thread of a Nebula Eel's life, coiled in a drop. It bends the space around it a hair's width.",
             ["nebula_eel", "nebula_leviathan"], section="parts.lantern"),
        part("void_carapace", "will", "A plate of Void Crab shell. Look into it and it is deeper than it is thick.", ["void_crab"], section="parts.lantern"),
        part("leviathan_scale", "will", "A scale from the Nebula Leviathan, as broad as a shield. Stars move in it, slowly.", ["nebula_leviathan"],
             section="parts.lantern", reward=True),
        part("cinder_ash", "will", "Ash from an Ashborn's cinder Qi. It stays warm for days. Smiths temper blades in it.",
             ["ashborn_pyre_keeper", "ashborn_raider", "general_kharn"], type="material", section="parts.lantern"),
        part("pyre_ember", "will", "An ember from an Ashborn pyre that will not go out. Alchemists use it to keep a furnace steady.",
             ["ashborn_pyre_keeper", "general_kharn"], type="material", section="parts.lantern", craft=True),
        part("drone_shell", "will", "The grey carapace of a Hollow Drone: metal that forgot it was metal. Copperjaw beetles love it.", ["hollow_drone"],
             type="material", section="parts.lantern", reward=True),
        part("gravity_core", "will", "The heavy heart of a Gravity Golem. Set it down and small things roll toward it.", ["gravity_golem"],
             section="parts.orbit"),
        part("orbit_stone_chip", "sovereign", "A chip of an orbit stone. It turns slowly in the palm, by itself.", ["gravity_golem"], type="material",
             section="parts.orbit"),
        part("moth_dust", "sovereign", "Silver dust from an Orbit Moth's wings. It hangs in the air a long while.", ["orbit_moth"], section="parts.orbit"),
        part("wyrm_ash", "will", "Grey ash from a Hollowed Wyrmling. It is cold, and it is not quite dead. Cleansing pills are made from it.",
             ["hollowed_wyrmling"], section="parts.orbit"),
    ]),
]
