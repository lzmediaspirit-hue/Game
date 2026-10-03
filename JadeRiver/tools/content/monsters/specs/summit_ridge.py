"""The Summit Ridge's foes (M2; the Windswept Ridge and the Frozen Shrine, levels 55-63): the hollow stags and the
cloudpeak rocs."""
from content.monsters import species

# M2. A grey-white stag of the Windswept Ridge drained by the Hollow: the Hollow's dark cracks over its hide, broken
# branching antlers, empty white eyes, grey mist seeping off it. It drops its head with its antlers levelled and stamps a
# forehoof (the tell, held), and charges; beaten, its legs fold and it comes apart into grey motes.
species("hollow_stag", plan="quadruped.cervid", share=True, size=2.2,
        palette=["stag_hide", "stag_antler", "stag_hoof", "strand"], accents=("strand",), shadow=(14, 4), cycle=13.0, view=True,
        data=dict(level=(55, 59), role="normal", element="hollow_wood", page="summit", drops=[("hollow_antler", 0.4), ("hollow_shard", 0.2)],
                  attacks=[("antler_charge", 0.5, 60, 1.2, dict(dash=140))], ai="charger", speed=120, width=30, height=56, hollowing=5,
                  cleansable=True))

# M2. The great storm roc of the high peaks (the Windswept Ridge, the Frozen Shrine): huge, white and gold, its wings of a
# great span with gold-tipped fingered primaries, a long gold-banded tail fan, gold crest plumes swept back from its
# crown, a hooked gold beak, fierce amber eyes under a heavy brow, golden talons. It rears its wings back and up as the
# wind gathers round it (the tell, held) and beats them forward in a great gust that throws you back; beaten, it folds
# and falls.
species("cloudpeak_roc", plan="bird.roc", share=True, size=2.7,
        palette=["roc_plume", "roc_flight", "roc_gold", "roc_beak", "roc_talon"], accents=("roc_gold", "roc_beak"), shadow=(16, 5),
        cycle=16.0, view=True,
        data=dict(level=(58, 63), role="normal", element="wind", page="summit", drops=[("roc_feather", 0.5), ("mystic_ore", 0.1)],
                  attacks=[("wing_gust", 0.7, 160, 1.0, dict(depth=60, knockback=120))], ai="flyer", speed=110, flying=True, width=40, height=50))
