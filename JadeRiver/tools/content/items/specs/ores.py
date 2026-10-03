"""Ores: what the veins give, a rung a grade (the forge's band metals, gear.py BANDS), and the Spirit Stone Shard, the
Qi crystal mined beside jadeiron. One family; each member its id, grade, text and the shops that sell it.
Mining (world.py's veins), salvage and the puppets, drops, chests and rewards are named in `sources`.
"""
from common import all_of, flag, realm
from content.items.dsl import family, member

MINED = dict(gather=True, craft=True)   # every ore lies in a vein and comes back from salvage or a puppet


def ore(id, grade, desc, name=None, **sources):
    return member(grade, grade, id=id, desc=desc, name=name, sources=dict(MINED, **sources))


FAMILIES = [
    family("ore.vein", kind="ore", members=[
        ore("copper_ore", "plain", "Soft copper ore from the quarry rim.", "Copper", shop={"stoneford_smith": {}}, drop=True, reward=True),
        ore("riverstone", "common", "Dense river-polished stone used in forging and building.",
            shop={"forge_guild": dict(price=12, flag="guild_smithing_adept"), "stoneford_smith": {}}, drop=True, reward=True),
        ore("jadeiron", "earth", "Iron veined with jade; it holds Qi paths well.",
            shop={"forge_guild": dict(price=40, flag="guild_smithing_adept")}, drop=True, reward=True),
        ore("spirit_stone_shard", "earth", "A splinter of crystallised Qi. Fuel and small change.", "Spirit Stone Shard",
            shop={"gu_trade_house": {}}, chest=True, drop=True, reward=True),
        ore("cloudsteel_ore", "heaven", "Feather-light ore from the sky ledges.", shop={"forge_guild": dict(price=120, flag="guild_smithing_expert")},
            reward=True),
        ore("mystic_ore", "mystic", "Ore that hums faintly in cold wind.",
            shop={"forge_guild": dict(price=260, requires=all_of(flag("guild_smithing_expert"), realm("heaven_glimpse_1"))), "stormsteel_smith": {}},
            drop=True),
        ore("stormsteel_ore", "spirit", "Blue-black ore from where lightning strikes the same ground twice.",
            shop={"forge_guild": dict(price=480, flag="guild_smithing_master"), "stormsteel_smith": {}, "shipwright": {}, "ironroot_clan": {}},
            chest=True, reward=True, auction=True),
        ore("sunglass_ore", "sage", "Desert glass the Sunscar sun fused out of the dunes. It holds heat and light like a lamp.", "Sunglass",
            chest=True, drop=True, reward=True),
        ore("driftglass", "sovereign", "Glass the star tides have worn smooth on the Driftglass Bank. Lantern-makers grind it into lenses.",
            "Driftglass", shop={"bastion_armoury": dict(price=6)}, chest=True, reward=True),
    ]),
]
