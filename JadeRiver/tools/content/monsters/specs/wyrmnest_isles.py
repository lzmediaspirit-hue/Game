"""The Wyrmnest Isles' foes (M4; the Nest Cliffs, the Eggshell Terraces, the Hatching Cave and the Guardian's Crown,
levels 85-96; the wyrmlings fight on at the Tidebreak Front): the hollowed wyrmlings and the nest guardians."""
from content.monsters import species

# M4. A young wyrm of the star-sea nests corrupted by the Hollow: a serpentine little dragonet, grey-violet ashen scales
# split by ash-white cracks leaking a sickly violet glow, pale ash spines, swept-back ash horns, empty glowing violet eyes,
# small torn wings, stubby legs, its tail coiled into a spiral behind it. It rears up on its hind legs as its wings flare
# and its throat swells with fire (the tell, held: its snap's too) and lunges to spit a short cone of grey-violet fire;
# beaten, it crumbles into a heap of ash that drifts away.
species("hollowed_wyrmling", plan="quadruped.wyrm", share=True, size=1.6,
        palette=["hw_scale", "hw_belly", "hw_wing", "hw_horn", "hw_mouth", "hw_fire_gv", "hw_fire_v"], glow=("hw_fire_gv", "hw_fire_v"),
        shadow=(12, 4), cycle=11.0, view=True,
        data=dict(level=(88, 96), role="normal", element="hollow_fire", page="lantern",
                  drops=[("wyrm_ash", 0.5), ("star_shard", 0.5, (1, 2)), ("hollow_shard", 0.3)],
                  attacks=[("grey_flame", 0.6, 110, 1.3, dict(depth=50, damage_type="qi", status={"id": "burn", "chance": 0.3, "power": 0.012, "duration_s": 3})),
                           ("wyrm_snap", 0.4, 60, 1.1, dict(dash=90))],
                  ai="melee", speed=120, width=32, height=36, hollowing=6))

# M4. The guardian beast of the wyrm nests: a stocky six-legged lizard-tortoise, a low slate-indigo hide speckled with star
# scales, a banded carapace of five dark bronze plates with a riveted rim and star crystals glowing along its ridge, a
# blunt head under a horned bronze helm with a glowing gold eye, a thick tail ending in a bronze club. It rears its front
# up on its hind legs, its club raised high behind it and its jaws open as its crystals flare (the tell, held: its club
# tail's too), and slams its forelegs down in a stomp, a burst of star light and crystal shards; beaten, its legs buckle
# and it sinks onto its belly as its crystals go dark.
species("nest_guardian", plan="shell.guardian", share=True, size=1.9,
        palette=["ng_hide", "ng_bronze", "ng_rim", "ng_belly", "ng_horn", "ng_crystal", "ng_crystal_dim", "maw", "snap_eye"],
        accents=("ng_crystal",), shadow=(24, 6), cycle=9.0, view=True, canvas=(176, 140),
        data=dict(level=(85, 93), role="normal", element="earth", page="lantern", drops=[("guardian_scale", 0.45), ("star_shard", 0.6, (1, 3))],
                  attacks=[("club_tail", 0.9, 150, 1.45, dict(depth=60, knockback=130, both_sides=True)),
                           ("crystal_stomp", 0.8, 110, 1.3, dict(depth=70, status={"id": "stun", "chance": 0.2, "power": 1.0, "duration_s": 0.8}))],
                  ai="slow_melee", speed=70, width=60, height=64, presence=2))
