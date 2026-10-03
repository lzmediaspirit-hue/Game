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
        palette=["imp_stone", "imp_limb", "maw", "peb_ochre", "peb_slate", "peb_rust"], accents=("peb_slate",), shadow=(9, 3), view=True,
        cycle=8.0,
        data=dict(level=(4, 6), role="normal", element="earth", page="quarry", drops=[("riverstone", 0.5), ("pebble_core", 0.08)],
                  attacks=[("pebble_throw", 0.4, 300, 0.9, dict(projectile={"speed": 380, "art": "pebble"}))], ai="ranged", speed=70,
                  width=16, height=32, keep_distance=180),
        sound=dict(body="shell"))
