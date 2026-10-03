"""The Bamboo Grove's foes (levels 10-15, between the Reed Marsh's Sunken Causeway and Crane Falls): the bamboo monkeys,
the green vipers and the thornback boar, the grove's elite (the Thicket Heart)."""
from content.monsters import species

# A small, agile green-gold monkey (the Whispering Bamboo), hunched on its haunches with its knuckles down, an olive
# mantle over its gold fur, a pale face with big amber eyes, a tuft of bamboo leaves on its crown, its tail curling. It
# draws a bamboo shoot back over its shoulder, chattering (the tell), and hurls it overhand.
species("bamboo_monkey", plan="humanoid.monkey", share=True, size=1.45,
        palette=["monkey_fur", "monkey_mantle", "monkey_skin", "bamboo_leaf", "bamboo_cane", "bamboo_node", "maw"],
        accents=("bamboo_leaf", "bamboo_cane"), shadow=(9, 3), cycle=9.0, view=True,
        data=dict(level=(10, 12), role="normal", element="wood", page="bamboo", drops=[("bamboo_shoot", 0.6)],
                  attacks=[("shoot_toss", 0.4, 280, 0.9, dict(projectile={"speed": 420, "art": "bamboo"}))], ai="ranged", speed=120,
                  agile=True, tameable=True, width=18, height=34, steals_coins=True, keep_distance=150))

# A slender bamboo pit viper (green, a pale belly and flank stripe, an orange tail tip), coiled with its neck raised in an
# S; it draws back into a tight S with its jaws parting (the tell) and strikes along the ground (its bite may poison).
species("green_viper", plan="serpent.viper", share=True, size=1.8,
        palette=["viper_scale", "viper_belly", "viper_tail", "viper_mouth"], accents=("viper_tail",), shadow=(13, 4), cycle=10.0,
        view=True,
        data=dict(level=(11, 14), role="normal", element="wood", page="bamboo", drops=[("viper_fang", 0.5), ("venom_sac", 0.3)],
                  attacks=[("strike", 0.35, 46, 1.0, dict(status={"id": "poison", "chance": 0.35, "power": 0.02, "duration_s": 5}))],
                  ai="melee", speed=85, width=24, height=18))

# The elite of the grove: a hulking wild boar overgrown with thorny wood-green vines, pale thorns along its spine
# (bristling up in anger), a long upcurved tusk, a small fierce red eye. The boarlet's body and its charge, grown huge.
species("thornback_boar", plan="quadruped.suid", share=True, size=1.95,
        parts=dict(coat=dict(kind="vines", twist=0.45, width=0.33),
                   crest=dict(kind="thorns", n=11, at=(4.8, 5.7), step=1.15, side=0.9, sag=1.4, length=2.4, r=0.55),
                   head=dict(tusk=1.6, eyes=dict(colour="TB_EYE", rim="TB_EYE_DARK"))),
        mats=dict(hide="tb_hide", head="tb_hide", stripe="tb_vine", hoof="tb_hoof", snout="tb_snout", bristle="tb_mane", tusk="tusk",
                  ear=("tb_mane", 1), vine="tb_vine", leaf="tb_leaf", thorn="tb_thorn"),
        palette=["tb_hide", "tb_mane", "tb_vine", "tb_leaf", "tb_thorn", "tb_snout", "tb_hoof", "tusk"], accents=("tusk", "tb_thorn"),
        shadow=(16, 5), cycle=13.0, view=True,
        data=dict(level=(13, 15), role="elite", element="wood", page="bamboo", drops=[("thorn_hide", 1.0), ("ember_pepper", 0.6, (1, 2))],
                  attacks=[("thorn_charge", 0.55, 50, 1.2, dict(dash=110, knockback=60))], ai="charger", speed=80, width=34, height=44,
                  thorns=0.1))
