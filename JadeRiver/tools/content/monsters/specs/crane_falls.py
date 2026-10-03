"""Crane Falls' creatures (between the Bamboo Grove and Cleansing Peak): the jade crane chick met wild by its pool (a
starter spirit animal, not hostile)."""
from content.monsters import species

# A starter spirit animal, met wild (not hostile) from Qi Unfurling 7, as its kin the reed otter and the ember fox: a
# fluffy white-and-jade crane chick on long legs, a red crown. It struts with a bobbing head, spreads its wings and puffs
# up (the tell), and buffets with them in a hop; beaten, it folds down to sit with its head tucked.
species("jade_crane_chick", plan="bird.chick", share=True, size=1.85,
        palette=["chick_down", "chick_jade", "chick_leg", "chick_beak", "chick_crown"], accents=("chick_crown",), elite=False,
        shadow=(7, 3), cycle=10.0, view=True,
        data=dict(level=(19, 24), role="normal", element="wind", page=None, drops=[], attacks=[("nip", 0.4, 36, 0.8)], ai="wild_pet",
                  tameable=True, width=18, height=28, passive=True))
