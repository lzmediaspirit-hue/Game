"""The treasure births' guardian (M3; Part 8's calendar, `living_world.py`: every fourth day a Spirit Fruit ripens in a
field room, rival cultivators come for it and its guardian wakes, at the room's level +2): the Fruit-Guardian Boar."""
from content.monsters import species

# M3. The boar that guards a Spirit Fruit: the thornback boar's build grown old and huge (its row's 46 to the thornback's
# 34), an olive-grey hide under moss, mossy bristles, the fruit tree's bark-brown vines winding over it with blossoms
# among them, pale bark thorns down its spine, jade eyes; on its back the tree itself, a gnarled sapling rooted in it,
# jade leaves and golden spirit fruits glowing under them. It paws the ground as its fruits blaze (the tell, held: its
# charge's and its root stamp's) and charges to toss; beaten, it buckles and rolls, the sapling still on its back.
species("fruit_guardian", plan="quadruped.suid", share=True, size=2.6, elite=False,
        parts=dict(coat=dict(kind="vines", twist=0.4, width=0.3),
                   crest=dict(kind="thorns", n=11, at=(4.8, 5.7), step=1.15, side=0.9, sag=1.4, length=2.6, r=0.6),
                   head=dict(tusk=1.8, eyes=dict(colour="FG_EYE", rim="FG_EYE_DARK")),
                   sapling=dict(at=(-0.8, 0.0), height=5.6, r=(0.75, 0.42), branches=((60.0, 2.8), (180.0, 2.5), (-70.0, 2.7)),
                                leaves=1.7, fruit=0.95,
                                blossoms=((2.2, 0.8), (1.0, -1.0), (-1.5, 1.1), (-2.8, -0.7), (0.3, 1.3), (-0.6, -1.4)))),
        mats=dict(hide="fg_hide", head="fg_hide", stripe="fg_vine", hoof="fg_hoof", snout="fg_snout", bristle="fg_mane", tusk="tusk",
                  ear=("fg_mane", 1), vine="fg_vine", leaf="fg_leaf", thorn="fg_thorn", bark="fg_vine", fruit="fg_fruit"),
        palette=["fg_hide", "fg_mane", "fg_vine", "fg_leaf", "fg_thorn", "fg_snout", "fg_hoof", "fg_fruit", "tusk"], accents=("fg_fruit",),
        shadow=(20, 6), cycle=13.0, view=True,
        data=dict(level=20, role="elite", element="wood", page=None, drops=[("thorn_hide", 1.0, (2, 3))],
                  attacks=[("thorn_charge", 0.55, 60, 1.3, dict(dash=220, knockback=110)),
                           ("root_stamp", 0.8, 120, 1.2, dict(both_sides=True, depth=60))],
                  ai="charger", width=46, height=60, hp_mult=3.0, name="Fruit-Guardian Boar"))
