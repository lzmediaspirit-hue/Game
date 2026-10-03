"""The Reed Marsh's foes (chapter 2): the reed frog, the marsh leech, the hollowed boarlet and the reed otter (a wild
spirit animal, not hostile)."""
from content.monsters import species

species("reed_frog", plan="amphibian.frog", size=1.42,
        palette=["frog", "frog_belly", "frog_stripe", "frog_sac", "frog_eye"], accents=("frog_eye",), shadow=(11, 4), cycle=6.0,
        data=dict(level=(4, 6), role="normal", element="wood", page="marsh", drops=[("frog_leg", 0.6), ("willow_moss", 0.3)],
                  attacks=[("jump_kick", 0.35, 40, 1.0, dict(dash=80))], ai="charger", speed=90, width=16, height=22),
        sound=dict(body="slime", tell="water"))

species("marsh_leech", plan="serpent.leech", size=1.44,
        palette=["leech", "leech_dark", "leech_belly", "leech_lip", "leech_maw"], accents=("leech_lip",), shadow=(13, 4), cycle=8.0,
        view=True, extra=("swim",),
        data=dict(level=(5, 7), role="normal", element="water", page="marsh", drops=[("leech_oil", 0.6)],
                  attacks=[("latch", 0.4, 38, 0.8, dict(dash=50, drain=0.3))], ai="melee", speed=40, width=20, height=16),
        sound=dict(body="slime", tell="water"))

# The boarlet with its colour drunk out of it (the Hollow): ash grey with pale stripes, cold eyes, the Hollow's strands,
# coming apart into motes when it falls.
species("hollowed_boarlet", plan="quadruped.suid", size=1.4,
        mats=dict(hide="h_hide", head="h_head", stripe="h_stripe", hoof="h_bristle", snout="h_snout", bristle="h_bristle", tusk="tusk",
                  ear=("h_snout", 1)),
        opts=dict(hollowed=True),
        palette=["h_hide", "h_head", "h_stripe", "h_snout", "h_bristle", "tusk", "strand", "pink"], accents=("tusk", "strand"),
        shadow=(13, 4), cycle=13.0, view=True,
        data=dict(level=(7, 12), role="normal", element="hollow_earth", page="marsh", drops=[("hollow_shard", 0.12), ("grey_hide", 0.5)],
                  attacks=[("double_charge", 0.45, 40, 1.0, dict(dash=70, repeat=2))], ai="charger", speed=85, width=22, height=30,
                  hollowing=4),
        # Research §3.3: Mei Qing's three grey hides drop every kill while still wanted.
        loot=dict(quest=[{"item": "grey_hide", "chance": 1.0, "count": [1, 1], "quest": "mei_qings_errand"}]))

# A starter spirit animal, met wild (not hostile) from Qi Unfurling 7, as its kin the ember fox and the jade crane chick.
species("reed_otter", plan="quadruped.mustelid", size=1.44,
        palette=["otter", "otter_pale", "otter_dark"], shadow=(13, 4), cycle=12.0, view=True,
        data=dict(level=(19, 24), role="normal", element="water", page=None, drops=[], attacks=[("nip", 0.4, 36, 0.8)], ai="wild_pet",
                  tameable=True, width=18, height=28, passive=True),
        sound=dict(tell="water"))
