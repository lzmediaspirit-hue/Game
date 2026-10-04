"""The Sunscar Desert's foes (M3; Act II, the Azure Expanse: the Glass Dunes, the Scorpion Flats and the Worm Sea, levels
73-81): the sandstorm scorpions and the dune worms."""
from content.monsters import species

# M3. A dog-sized desert scorpion whose carapace has fused with wind-blown sand into plates of rough amber desert glass:
# low over its eight legs, a sand-gold body, an amber glass plate glinting on each segment, a bone-pale belly, two
# umber-tipped pincers held before it, its tail curled up and forward over its back to a venom-amber telson and a dark
# barb; sand streaming off its back. Its tail climbs into a high arc forward over its back as the telson glows and its
# pincers gape (the tell, held: its sting's and its snap's), and it pitches nose-down and stabs forward over its claws in
# a burst of sand; struck, glass chips fly; beaten, it flips onto its back, curls its legs, and its cracked carapace pours
# out its sand in heaps as it fades.
species("sandstorm_scorpion", plan="crab.scorpion", share=True, size=3.0,
        palette=["ssc_sand", "ssc_leg", "ssc_glass", "ssc_umber", "ssc_belly", "ssc_venom", "ssc_grain"], accents=("ssc_venom",),
        shadow=(13, 4), cycle=10.0, view=True,
        data=dict(level=(73, 78), role="normal", element="earth", page="azure",
                  drops=[("scorpion_stinger", 0.45), ("storm_shard", 0.5, (1, 2)), ("sunglass_ore", 0.08)],
                  attacks=[("tail_sting", 0.55, 76, 1.25, dict(status={"id": "poison", "chance": 0.4, "power": 0.012, "duration_s": 5})),
                           ("pincer_snap", 0.4, 46, 1.0)],
                  ai="melee", speed=115, pack=True, width=34, height=30),
        sound=dict(body="shell"))
