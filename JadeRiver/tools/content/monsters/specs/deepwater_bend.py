"""Deepwater Bend's foes (chapter 3, past the Caravan Road): the Bend Shore's jade carp and tide crabs, and the ember fox
met wild there (a starter spirit animal, not hostile)."""
from content.monsters import species

# A large jade-green river carp riding the water line, its fins and lobes tipped in gold, gold whiskers trailing from its
# mouth, a big gold-ringed eye. It curls its tail up (the tell) and darts in to slap; beaten, it rolls belly up.
species("jade_carp", plan="fish.minnow", share=True, size=1.85,
        parts=dict(Z=1.6, trunk=((0.0, 0.0, 0.0), (5.4, 2.2, 2.7)), head=((4.0, 0.0, 0.1), (2.8, 2.0, 2.3)),
                   tail={"pivot": -3.9, "seg": ((-1.8, 0.0, 0.0), (2.5, 1.1, 1.5)), "lobe": (-4.9, 1.1, (2.5, 0.4, 1.05), 40.0)},
                   dorsal={"plates": ((-2.2, 1.2), (-1.1, 2.0), (0.0, 2.3), (1.0, 1.8), (1.9, 1.0)), "base": 2.3, "r": (0.7, 0.32)},
                   pecs={"at": (2.0, 1.9, -0.9), "r": (1.5, 1.1, 0.3)},
                   eye={"socket": (4.0, 0.0, 0.1), "rim": (1.25, 1.55, 0.95), "at": (1.5, 1.5, 0.6), "colour": "CARP_EYE", "ring": True},
                   mouth=(6.7, 0.0, -0.3), jaw={"at": (4.7, 0.0, -1.3), "drop": 0.45, "r": (1.8, 1.2, 0.5), "turn": 32.0, "corner": (6.1, 0.0, -0.9)},
                   glints=((8.2, 0.0, 0.4), (8.8, 0.0, 1.0), (7.7, 0.0, 1.1)), barbels=(6.2, 0.8, -0.7), wake=None, mist=False),
        mats=dict(skin="carp_scale", back="carp_back", belly="carp_belly", fin="carp_fin", gold="carp_gold"),
        palette=["carp_scale", "carp_back", "carp_belly", "carp_fin", "carp_gold"], accents=("carp_gold",), shadow=(9, 3), cycle=12.0,
        data=dict(level=(19, 22), role="normal", element="water", page="bend", drops=[("jade_scale", 0.5), ("jade_carp_fish", 0.15)],
                  attacks=[("tail_slap", 0.5, 50, 1.0, dict(dash=90))], ai="leaper", speed=70, width=22, height=24),
        sound=dict(body="slime", tell="water"))

# A big blue-teal crab, its shell studded with pearls, one oversized shield claw held before its face (it guards from
# the front); the shield claw rears up high and gapes in the tell and snaps shut as it thrusts.
species("tide_crab", plan="crab.mud", share=True, size=1.3,
        parts=dict(shell={"pearls": ((1.4, 2.4, 0.6), (-1.6, -2.2, 0.55), (-0.6, 4.4, 0.5), (0.8, -4.6, 0.5), (-2.4, 0.6, 0.6))},
                   claws={"scale": (1.55, 0.85)}),
        mats=dict(shell="tide_shell", rim="tide_rim", pale="tide_under", leg="tide_leg", claw="tide_claw", tip="tide_tip", eye="eye",
                  pearl="pearl"),
        palette=["tide_shell", "tide_rim", "tide_under", "tide_leg", "tide_claw", "tide_tip", "eye", "pearl"], accents=("tide_tip", "pearl"),
        gold=("eye",), shadow=(12, 4), cycle=10.0, sideways=True,
        data=dict(level=(20, 23), role="normal", element="water", page="bend", drops=[("tide_shell", 0.5), ("pearl", 0.15)],
                  attacks=[("pinch", 0.45, 46, 1.1)], ai="guard_counter", speed=50, width=24, height=30, front_guard=0.6),
        sound=dict(body="shell", tell="water"))

# A starter spirit animal, met wild (not hostile) from Qi Unfurling 7, as its kin the reed otter and the jade crane chick:
# a small orange-red fox kit, a white bib and muzzle, dark socks, its bushy tail's tip burning.
species("ember_fox", plan="quadruped.canine", share=True, size=1.45, parts=dict(tail=dict(flame=True)),
        palette=["fox_fur", "fox_white", "fox_sock", "fox_ear_in", "hound_nose", "tongue"], elite=False, shadow=(11, 3),
        cycle=11.0, view=True,
        data=dict(level=(19, 24), role="normal", element="fire", page=None, drops=[], attacks=[("nip", 0.4, 36, 0.8)], ai="wild_pet",
                  tameable=True, width=18, height=28, passive=True))
