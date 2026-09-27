"""Technique animations (docs/technique_plan.md §3.2, §3.10; docs/roadmap_master_ui.md decision 23).

Every technique plays the effect animation of its form (one of the 24, drawn by tools/art/fx into art/fx and
data/fx_art.json) on an existing body pose (AGENTS.md: a technique adds FX, never a pose). `add_animation`
writes two fields into a row's `vfx` block:

  anim   the form's animation id: the row's `form` when P13's grammar has tagged it, else FORM_OF (the plan's
         table for today's arts, the same one the Style A emblems use)
  pose   the catalogue action the effect is timed to: the row's `action` when it names one, `combo_1` for
         `meditate_burst` (the wielded family's first combo step, as CombatAuthority resolves it) and `combo_3`
         for a row with no action (its third)

`data_validation` fails a row whose anim is not a built form or whose pose is neither a `parts.json` action nor
an alias that resolves to one for every weapon family.
"""
import json
import os

from common import DATA

# The plan's form of every art that exists today (the icons' FORM_OF, with a form for the hand-marked ones).
FORM_OF = {
    "flowing_palm": "flurry", "jade_thrust": "thrust", "cloudpiercing_stroke": "strike", "reedcutter_slash": "strike",
    "riverstone_sweep": "sweep", "twin_reed_shot": "volley", "tiger_rush": "lunge", "willow_leaf_parry": "counter",
    "dragon_tail_sweep": "sweep", "shadow_flick": "volley", "bell_toll_strike": "strike", "pinning_arrow": "snare",
    "mountain_cleaver": "strike", "gale_fan": "wave", "reed_song": "seeker", "thunder_dao_arc": "arc",
    "returning_crane_fan": "return", "clear_heart_melody": "chorus", "rising_tide": "burst", "palm_wave": "arc",
    "crescent_arc": "arc", "spear_lance": "wave", "sword_release": "release", "sword_swarm": "swarm",
    "flying_blades": "seeker", "earthshaker_wave": "wave", "vine_snare": "snare", "rain_of_reeds": "rain",
    "stone_skin": "ward", "gale_step": "lunge", "mountain_shaker": "burst", "ember_burst": "burst",
    "still_water_focus": "ward", "shadowstep_cut": "blink", "cloud_descent": "plunge", "mirror_mind_spike": "pillar",
    "soul_lantern_ward": "ward", "sense_lock": "seal", "phantom_double": "ward", "soul_search": "pillar",
    "crimson_palm": "strike", "blood_river_slash": "arc", "sanguine_lotus": "burst", "golden_body": "ward",
    "venom_needles": "seeker", "miasma_palm": "burst", "splashed_ink": "volley", "cursive_storm": "rain",
    "stilling_peal": "seal", "qi_seal_toll": "seal", "wardens_call": "chorus", "upright_glyph": "wave",
    "benevolent_script": "chorus", "rite_seal_script": "seal", "blood_burning": "ward",
    "glimpse_of_heaven": "pillar",
}
# P13a: an art drawn from a keystone template (the keystones, and a few Dao and lost arts) plays the form its template is
# drawn with (tools/icons/emblem_atlas.py TEMPLATE_MARK), an Avatar or a Mirror the Ward's dome as today's Golden Body
# and Phantom Double do.
TEMPLATE_FORM = {"constructs": "swarm", "field": "domain", "finisher": "pillar", "procession": "chorus", "avatar": "ward", "mirror": "ward"}
# The pose aliases the combat authority resolves at cast: the wielded family's combo step (0-based).
POSE_ALIASES = {"combo_1": 0, "combo_2": 1, "combo_3": 2}


def forms():
    """The forms the FX library has built (data/fx_art.json), or the plan's 24 before a build."""
    path = os.path.join(DATA, "fx_art.json")
    if os.path.exists(path):
        return sorted(json.load(open(path, encoding="utf-8"))["forms"])
    return sorted(set(FORM_OF.values()))


def pose_of(t):
    action = t.get("action")
    if action in (None, "", "null"):
        return "combo_3"
    if action == "meditate_burst":
        return "combo_1"
    return str(action)


def add_animation(T):
    built = set(forms())
    for t in T:
        form = t.get("form") or FORM_OF.get(t["id"]) or TEMPLATE_FORM.get(t.get("template", ""))
        if form is None:
            raise ValueError("technique_anim: no form for technique %s (tag it with `form` or add it to FORM_OF)" % t["id"])
        if form not in built:
            raise ValueError("technique_anim: technique %s has form %s, which tools/art/fx has not built" % (t["id"], form))
        t.setdefault("vfx", {})
        t["vfx"]["anim"] = form
        t["vfx"]["pose"] = pose_of(t)
