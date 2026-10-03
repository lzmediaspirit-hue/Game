"""Stonewall Quarry's foes (levels 4-7, off Stoneford's quarry road): the rock beetle and the pebble imp, the first foes
past the top-down rooms there (the quest `stone_and_sweat`: five beetles, three pebble throws dodged)."""
from content.monsters import species

# A squat beetle whose carapace is a set of rocky plates; it curls into a stone ball and rolls at you.
species("rock_beetle", plan="shell.beetle", size=1.6,
        palette=["beetle_rock", "beetle_pronotum", "beetle_lichen", "beetle_chitin", "beetle_horn"], accents=("beetle_horn",),
        shadow=(11, 4), cycle=9.0, view=True,
        data=dict(level=(4, 5), role="normal", element="earth", page="quarry", drops=[("beetle_shell", 0.6), ("copper_ore", 0.3)],
                  attacks=[("roll", 0.5, 40, 1.1, dict(dash=90))], ai="charger", speed=60, width=20, height=24),
        sound=dict(body="shell"))

# A small, grinning earth spirit of stone studded with pebbles, a glowing crack in its belly; it pelts you with stones
# and crumbles into a heap of them.
species("pebble_imp", plan="humanoid.imp", size=1.5,
        palette=["imp_stone", "imp_limb", "maw", "peb_ochre", "peb_slate", "peb_rust"], accents=("peb_slate",), elite=False, shadow=(9, 3),
        view=True, cycle=8.0,
        data=dict(level=(4, 6), role="normal", element="earth", page="quarry", drops=[("riverstone", 0.5), ("pebble_core", 0.08)],
                  attacks=[("pebble_throw", 0.4, 300, 0.9, dict(projectile={"speed": 380, "art": "pebble"}))], ai="ranged", speed=70,
                  width=16, height=32, keep_distance=180),
        sound=dict(body="shell"))

# M1. Deeper in the quarry (the Lower Pit): a huge, slow tortoise whose shell is a small stone mountain, pale granite
# crags in strata, moss on the ledges, a little wind-bent pine on the saddle; an old beaked head. It rears onto its hind
# legs (the tell) and stamps down in a ring of dust that strikes on both sides of it; beaten, it draws in and the
# mountain cracks.
species("stone_tortoise", plan="shell.tortoise", share=True, size=1.4,
        palette=["mtn_rock", "mtn_rim", "mtn_moss", "mtn_pine", "mtn_bark", "tort_skin", "tort_belly", "tort_beak", "snap_eye", "maw"],
        accents=("snap_eye",), shadow=(18, 5), cycle=9.0,
        data=dict(level=(5, 7), role="normal", element="earth", page="quarry", drops=[("tortoise_plate", 0.5), ("jadeiron", 0.15)],
                  attacks=[("slam", 0.6, 80, 1.2, dict(depth=40, both_sides=True, knockback=60))], ai="slow_melee", speed=35, width=36,
                  height=40, hp_mult=1.4),
        sound=dict(body="shell"))

# M1. A plump velvet-furred mole with a pink star nose and huge iron-grey digging claws (the Lower Pit, the Collapsed
# Tunnel). It moves unseen under the ground (the room view hides it as it burrows); it bursts up out of its hole rearing,
# claws raised, clods flying (the tell), and rakes them down.
species("ironclaw_mole", plan="quadruped.talpid", share=True, size=1.7,
        palette=["mole_fur", "mole_sheen", "mole_palm", "mole_pink", "mole_iron", "mole_dirt"], accents=("mole_iron", "mole_pink"),
        shadow=(10, 3), cycle=9.0, view=True,
        data=dict(level=(5, 7), role="normal", element="earth", page="quarry", drops=[("mole_claw", 0.5), ("ore_dust", 0.6)],
                  attacks=[("burst_claw", 0.6, 44, 1.2)], ai="burrower", speed=70, tameable=True, width=20, height=26),
        sound=dict(body="shell"))
