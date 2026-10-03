"""The people along the valley's roads out of Stoneford (docs/architecture/npc_engine.md): Greyreed Hamlet's elder and
trader, the Caravan Road's night peddler, the Reed Marsh's hermit, and a fisherman at the Marsh Edge."""
from content.npcs.spec import extra, look, npc, work


NPCS = [
    npc("hamlet_elder_gao", "Elder Gao", "Greyreed Hamlet", look("long_tied:1", "vneck:grey", "loose", "folded"),
        ["The grey came up from the pools. It took the colour, then the people.",
         "If the well runs clean again, we might come home."], ["..."], at=["gh_hamlet_square"]),
    npc("hamlet_trader_min", "Trader Min", "Greyreed trade post", look("ponytail", "vneck:jade", "cuffed", "boots"),
        ["Greyreed trades again! Thanks to you."], ["Market day!"], services=["shop:greyreed"], at=["gh_hamlet_square"]),
    # Part 8 (S49 karma): the night peddler of the Caravan Road. Everything on his mat is a small sin.
    npc("peddler_shao", "Peddler Shao", "Sells after dark",
        look("long_tied:4", "cardigan:ink", "loose:ink", "folded", hat="weimao"),
        ["Don't ask where it came from. Ask what it costs.",
         "The road's quiet at night. Good for business. Bad for questions."], ["Psst."], services=["shop:night_peddler"],
        at=["cr_caravan_road"]),
    npc("hermit_yao", "Hermit Yao", "Marsh hermit",
        look("flowing:1", "scholar:earth", "loose", "folded", hat="straw", cape="tattered"),
        ["The otters trust me. Maybe one day they'll trust you.",
         "Spirit beasts are not tools. They are friends who bite."], ["Shh. Listen to the reeds."],
        services=["shop:hermit", "page:core_exchange"], tree="hermit_yao",
        service_labels={"page:core_exchange": "Core Exchange"}, service_unlocks={"page:core_exchange": "spirit_animals"},
        at=["rm_hermit_stilt_house"]),
]

EXTRAS = [
    extra("x_marsh_fisher", "rm_marsh_edge", look("short_knot", "vneck:indigo", "cuffed", "folded", hat="straw"),
          work("fish", [33.4, 22.3, "s"])),
]
