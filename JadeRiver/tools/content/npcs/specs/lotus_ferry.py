"""Lotus Ferry's people (docs/architecture/npc_engine.md): the seven villagers and two neighbours of the prologue's
village, at home and at work, and the two villagers at work with no part in the story."""
from content.npcs.spec import extra, look, npc, place, work


NPCS = [
    npc("aunt_ping", "Aunt Ping", "Your aunt", look("long_tied:1", "cardigan:rose", "straight:earth", "folded"),
        ["Eat something before you run off.", "Your mother had the same stubborn chin.",
         "The river gives, the river takes. Mostly it gives fish."], ["Mind the steps!", "Who left the net out again?"],
        tree="aunt_ping",
        at=[place("lf_fishers_hut", work=work("cook", [6, 6, "sw"], [5.2, 8.1, "w"])),
            place("lf_village", "npc_aunt_ping_lane", work=work("sweep", [11, 17, "w"], [9.2, 17.6, "w"], [12.6, 18.3, "sw"])),
            place("lf_village_night", "npc_ping_night")]),
    npc("lu_boatman", "Lu", "Ferryman", look("topknot:1", "scholar:grey", "scholar:ink", "folded", hat="straw"),
        ["The river has been restless.", "Breathe in when the water rises. Out when it falls.",
         "Every current started as a trickle."], ["Hm.", "Tide's turning."], tree="lu",
        at=[place("lf_village", work=work("watch", [56, 28, "s"], [57.8, 28.8, "s"])),
            place("lf_lu_boat", "npc_lu_boat", work=work("watch", [10, 8, "s"], [8.2, 8.6, "s"], [11.8, 8.4, "se"]))]),
    npc("little_dou", "Little Dou", "Neighbour's boy", look("short_knot", "sleeveless:ochre", "cuffed", "slippers"),
        ["When I grow up I'll punch a crab so hard it flies to Stoneford!", "Did you see my kite? It's the best kite."],
        ["Kite! Kiiite!", "Hi-yah!"], scale=0.8, tree="little_dou",
        at=[place("lf_village", work=work("play", [44, 24, "s"], [45.8, 25.4, "se"], [42.6, 25.6, "sw"], [44.8, 26.2, "s"])),
            place("lf_village_night", "npc_dou_night")]),
    npc("old_ma", "Old Ma", "Shopkeeper", look("short_knot:5", "vneck:earth", "loose", "slippers"),
        ["Silver or barter, I'm not fussy.", "Rice balls! Fresh this morning. Well. This week."],
        ["Fresh rice balls!", "Everything must go. Eventually."], services=["shop:old_ma"], tree="old_ma",
        at=[place("lf_old_ma_store", work=work("sell", [12, 3, "s"], [13.5, 2.2, "n"], [10.8, 2.6, "s"])),
            place("lf_village_night", "npc_ma_night")]),
    npc("granny_liu", "Granny Liu", "Herbalist", look("long_tied:1", "cardigan:jade", "scholar:grey", "folded"),
        ["Bitter tea, sweet health.", "A herb picked at dawn is worth two at noon."],
        ["Where did I put my pestle?", "Hmph. Young people."], services=["shop:granny_liu"], tree="granny_liu",
        at=[place("lf_granny_liu_hut", work=work("grind", [6, 6, "sw"], [4.3, 5.6, "w", "cook"], [4.2, 7.4, "w", "grind"])),
            place("lf_village_night", "npc_granny_night")]),
    npc("shen_lian_npc", "Shen Lian", "Fisher's son", look("high_pony", "sleeveless:indigo", "martial", "boots"),
        ["Race you to the tower. Loser guts the fish.", "One day I'll join a sect. A real one."],
        ["Faster!", "Bet you can't catch me."], tree="shen_lian",
        at=[place("lf_village", work=work("carry", [52, 27, "e"], [54.2, 26.2, "ne"], [50.2, 26.4, "w"]))]),
    npc("uncle_guo", "Uncle Guo", "Retired brawler", look("topknot:5", "sleeveless:crimson", "martial", "boots"),
        ["Fists first. Everything else is decoration.", "I kindled Qi once. For a day. Long story."],
        ["Hah! Hup!", "Keep your elbow in."], tree="uncle_guo",
        at=[place("lf_village", work=work("fists", [30, 22, "se"], [31.6, 23.3, "s"], [28.8, 23.4, "e"]))]),
    npc("fisher_wen", "Fisher Wen", "Fisherman", look("short_knot:5", "vneck:indigo", "cuffed", "folded", hat="straw"),
        ["The carp aren't biting. Something scared them.", "Grey water near the reeds last week. Never seen that."],
        ["Nothing. Again."], at=[place("lf_village", work=work("mend", [64.4, 27.2, "ne"], [66.2, 27.6, "n"]))]),
    npc("washer_mei", "Washer Mei", "Villager", look("ponytail:2", "cardigan:white", "straight", "slippers"),
        ["Aunt Ping says you're finally awake before noon.", "The river's cold as winter this morning."], ["Scrub, scrub."],
        at=[place("lf_village", work=work("laundry", [14.1, 33.2, "e", "wash"], [12.0, 30.4, "nw", "hang"]))]),
]

# People at work with no part in the story: a fisherman on the bank below the square, a woodcutter at the block by the
# watch-tower.
EXTRAS = [
    extra("x_bank_fisher", "lf_village", look("short_knot:5", "vneck:grey", "cuffed", "folded", hat="straw"), work("fish", [38.5, 33.25, "s"])),
    extra("x_woodcutter", "lf_village", look("short_knot", "sleeveless:ochre", "loose", "folded"), work("chop", [65.1, 18.3, "w"])),
]
