"""The Willow Path's foes: the wild boarlets and the mossback toad."""
from content.monsters import species

species("wild_boarlet", plan="quadruped.suid", size=1.4,
        palette=["hide", "hide_head", "stripe", "hoof", "snout", "bristle", "tusk", "pink"], accents=("tusk",), shadow=(13, 4),
        cycle=13.0, view=True,
        data=dict(level=(1, 2), role="normal", element="earth", page="willow_path", drops=[("boar_hide", 0.5), ("tough_meat", 0.5)],
                  attacks=[("charge", 0.45, 40, 1.0, dict(dash=70))], ai="charger", speed=80, width=22, height=30),
        loot=dict(starter=True, finds="early"))

species("mossback_toad", plan="amphibian.toad", size=1.56,
        palette=["toad", "toad_leg", "toad_belly", "toad_sac", "toad_moss", "toad_fern", "tongue", "toad_eye", "maw"],
        accents=("toad_eye", "tongue"), shadow=(12, 4), cycle=7.0, view=True,
        data=dict(level=(2, 3), role="normal", element="wood", page="willow_path", drops=[("toad_oil", 0.5), ("moss", 0.5)],
                  attacks=[("tongue_lash", 0.4, 110, 0.9)], ai="ranged_melee", speed=50, tameable=True, width=20, height=26),
        loot=dict(starter=True, finds="early"),
        sound=dict(body="slime", tell="water"))
