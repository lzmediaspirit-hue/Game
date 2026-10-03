"""The people along the valley's roads out of Stoneford (docs/architecture/npc_engine.md): Greyreed Hamlet's elder,
trader and villagers, the Caravan Road's night peddler, the Reed Marsh's hermit, and a fisherman at the Marsh Edge."""
from common import all_of, qdone
from content.npcs.spec import extra, look, npc, place, work

# The engine's first new people (decision 45, E3): Greyreed's villagers come home once the well runs clean (Cleansing
# the Well), as Elder Gao hoped. Each is one spec: their place in the hamlet is an anchor of the room, their work spots
# anchors of its layout (the water's edge, the laundry line, the net rack, the square).
HOME_AGAIN = dict(visible_if=all_of(qdone("cleansing_the_well")))

NPCS = [
    npc("hamlet_elder_gao", "Elder Gao", "Greyreed Hamlet", look("long_tied:1", "vneck:grey", "loose", "folded"),
        ["The grey came up from the pools. It took the colour, then the people.",
         "If the well runs clean again, we might come home."], ["..."], at=["gh_hamlet_square"]),
    npc("hamlet_trader_min", "Trader Min", "Greyreed trade post", look("ponytail", "vneck:jade", "cuffed", "boots"),
        ["Greyreed trades again! Thanks to you."], ["Market day!"], services=["shop:greyreed"], at=["gh_hamlet_square"]),
    npc("washer_ying", "Washer Ying", "Greyreed villager", look("ponytail", "cardigan:rose", "straight:grey", "slippers"),
        ["The pools took the grey downstream. The washing comes out white again.",
         "Elder Gao wept when the well ran clear. Don't tell him I told you."], ["Scrub, scrub.", "White as a heron."],
        at=[place("gh_hamlet_square", anchor="commons@9", facing=1, **HOME_AGAIN,
                  work=work("laundry", "water_edge:wash", "by:laundry_line:hang"))]),
    npc("fisher_gan", "Fisher Gan", "Greyreed villager", look("short_knot:5", "vneck:grey", "cuffed:earth", "folded", hat="straw"),
        ["The pools gave the fish back before they gave back the colour.",
         "Three seasons on my cousin's floor in Stoneford. Never again."], ["Knot, pull, knot.", "Mind the hooks."],
        at=[place("gh_hamlet_square", anchor="commons@12", facing=-1, **HOME_AGAIN, work=work("mend", "by:net_rack", "water_edge"))]),
    npc("old_jiu", "Old Jiu", "Greyreed villager", look("topknot:1", "vneck:earth", "loose", "slippers"),
        ["Grey dust everywhere. It sweeps like ash, but it is only dust now.",
         "We came home the day the well ran clear. The hamlet remembers who cleaned it."], ["Sweep, sweep.", "Mind your feet."],
        at=[place("gh_hamlet_square", anchor="square@22", facing=1, **HOME_AGAIN, work=work("sweep", "home", "open", "open"))]),
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
