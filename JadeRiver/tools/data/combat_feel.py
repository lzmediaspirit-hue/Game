"""Decision 38 · the combat feel of the top-down world, one table: data/combat_feel.json.

    python3 tools/data/combat_feel.py            # write it (build_data.py runs it too)
    python3 tools/data/combat_feel.py --check    # fail unless the file is current

The look rule (decision 38) heads the table: only the feel and technique come from the reference game (timing,
hit-stop, smears, impact readability, camera kick, knockback); the look of every attack and skill stays wuxia and
xianxia (the FX sheets of tools/art/fx/build_fx_topdown.py, in the element language of elements.py and the art
bible's palette). Research: docs/research/alabaster_dawn_2_5d.md §3.9.

What lives here (CombatFeel reads it; TopdownFx and the top-down views play it):

- weights: what a blow of each weight does. Hit-stop in 60 fps frames (about a third of a fighting game's: an action
  RPG lands many blows a second on a crowd), the camera's kick along the blow and its shake, the impact mark, the hop
  a knockback gives the struck body.
- families: per weapon family, each combo step's weight, its lunge toward the target, the rate its smear plays at (the
  smear's first frame leads the hit by one frame, and its three bright frames are the step's active window), and its
  cancel rule: a dodge cancels the anticipation (the blow is dropped) or the recovery once `recovery_after` of it has
  run, never the active window; the finisher only after `finisher_after`. The steps' own durations and hit frames stay
  in weapon_families.json: the phases are derived from them (CombatFeel.phases), never kept twice.
- forms: per technique form, its weight and the top-down pose it plays (the character pipeline's action names).
- poses: per family, the top-down pose it plays where that is not the side view's own action (the heavy sabre's
  two-handed cuts, the bell's toll, the fan's throw, the brush writing, the flute at the lips, the bow's draw), for a
  step's or a technique's action or for a move (a dash attack, a blow in the air, a throw); `moves` the pose of each move
  for every family that does not name its own (the dash slash, the air strike, the charge's held wind-up, the parry's
  deflection, the melody), and `melody_loop` the frames the held melody loops (CombatFeel.top_pose,
  TopdownFigure.resolve).
- foes: the weight of a foe's blow by its role, and the marks it shows (its tell on the wind-up, its swipe).
- missing_poses: the poses the character pipeline (decision 37) does not draw yet, each with the stand-in it plays.
  Empty: the full set draws every one (the bow batch).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, write  # noqa: E402

LOOK_RULE = ("Decision 38: only the feel and technique come from the reference game (timing, hit-stop, smears, impact "
             "readability, camera kick, knockback). The look of every attack and skill stays wuxia/xianxia: sword-light arcs and "
             "qi trails, ink-brush strokes, flowing silk and robe motion, jade and gold qi, elemental Dao imagery (water ripples, "
             "wind petals and leaves, thunder talismans, fire lotus, earth stone, metal sword-qi), palm prints, sword formations "
             "and calligraphic impact marks; never sci-fi, tech or generic fantasy.")

WEIGHTS = {
    # hitstop_f: frames at 60 fps; kick_px: the camera's jolt along the blow (screen px); shake_s / shake_px: a shake on top;
    # impact: the mark's weight in the impact sheets; hop: the struck body's knockback hop, art px per knockback unit.
    "light": {"hitstop_f": 3, "kick_px": 0, "shake_s": 0.0, "shake_px": 0, "impact": "light", "hop": 0.06},
    "medium": {"hitstop_f": 4, "kick_px": 2, "shake_s": 0.0, "shake_px": 0, "impact": "light", "hop": 0.07},
    "heavy": {"hitstop_f": 6, "kick_px": 4, "shake_s": 0.1, "shake_px": 2, "impact": "heavy", "hop": 0.08},
    "finisher": {"hitstop_f": 8, "kick_px": 6, "shake_s": 0.18, "shake_px": 4, "impact": "finisher", "hop": 0.1},
}
ORDER = ["light", "medium", "heavy", "finisher"]


def fam(steps, smear_fps, lunge, recovery_after=0.3, finisher_after=0.6, charged="finisher", poses=None):
    return {"steps": steps, "charged": charged, "smear_fps": smear_fps, "lunge": lunge, "recovery_after": recovery_after,
            "finisher_after": finisher_after, "poses": poses or {}}


# A family's own poses (the character catalogue's actions, tools/art/topdown/figure/actions.py): by the side view's
# action its step or technique names, or by a move. The thrust families' dash attack is their lunging thrust; the ranged
# families shoot from the dash and in the air as they do on the ground. The heavy sabre cuts two-handed; the bell's first
# two steps toll it out on both sides (its third is the heavy descending peal, swing_3); the brush writes its third step
# and every technique that has no blow of its own (its talisman); the fan's thrown step throws it.
THRUST = {"dash": "thrust_3"}


# Light weapons cancel early and lunge short; heavy ones commit (the reference's heavy-attack rule).
FAMILIES = {
    "fists": fam(["light", "light", "medium"], 24, [10, 10, 16], 0.0, 0.4),
    "gauntlets": fam(["light", "light", "heavy"], 24, [10, 10, 16], 0.0, 0.4),
    "jian": fam(["light", "light", "heavy"], 20, [12, 12, 20], 0.2, 0.5),
    "spear": fam(["light", "medium", "heavy"], 18, [8, 8, 24], 0.3, 0.6, poses=THRUST),
    "short_blade": fam(["light", "light", "medium"], 24, [12, 12, 16], 0.0, 0.3, poses=THRUST),
    "staff": fam(["medium", "medium", "heavy"], 18, [8, 8, 16], 0.3, 0.6, poses=THRUST),
    "heavy_sabre": fam(["medium", "heavy", "finisher"], 14, [8, 12, 20], 0.5, 0.8,
                       poses={"swing_1": "two_hand_swing_1", "swing_2": "two_hand_swing_2", "swing_3": "two_hand_swing_3"}),
    "fan": fam(["light", "light", "medium"], 20, [6, 6, 10], 0.2, 0.5, poses={"throw": "fan_throw"}),
    "flute": fam(["light"], 20, [0], 0.0, 0.5, charged="medium",
                 poses={"attack": "flute_play", "dash": "flute_play", "air": "flute_play"}),
    "brush": fam(["light", "light", "medium"], 20, [6, 6, 10], 0.2, 0.5, poses={"swing_3": "brush_write", "cast": "brush_write"}),
    "bell": fam(["light", "light", "medium"], 18, [0, 0, 0], 0.3, 0.6, poses={"swing_1": "bell_toll", "swing_2": "bell_toll"}),
    "bow": fam(["medium"], 20, [0], 0.3, 0.6, charged="heavy", poses={"bow": "bow_draw", "dash": "bow_draw", "air": "bow_draw"}),
}

# The pose of each move for a family that does not name its own: an attack in or just after a dash (the dash attack), a
# blow struck in the air, the dragged finisher held armed (its wind-up, before the release), the instant a guard
# parries, the flute's held melody (its frames `melody_loop`, the note on the second).
MOVES = {"dash": "dash_slash", "air": "air_strike", "charge": "charge_hold", "parry": "parry_deflect", "melody": "flute_play"}
MELODY_LOOP = [1, 4]

# Technique forms: the weight of their blow and the pose they play in the top-down catalogue (meditation is drawn facing
# the camera only, so a cast of a meditate form plays `cast`; the Plunge form plays the plunge; `combo` its family's step).
FORMS = {
    "strike": ("heavy", "combo_3"), "flurry": ("medium", "combo_1"), "thrust": ("heavy", "thrust_1"), "lunge": ("heavy", "dash"),
    "sweep": ("heavy", "combo_3"), "arc": ("medium", "combo_2"), "volley": ("medium", "cast"), "rain": ("medium", "cast"),
    "pillar": ("heavy", "cast"), "wave": ("heavy", "combo_3"), "burst": ("heavy", "cast"), "seeker": ("medium", "cast"),
    "return": ("medium", "combo_3"), "snare": ("medium", "cast"), "counter": ("heavy", "guard"), "ward": ("light", "cast"),
    "chorus": ("light", "cast"), "blink": ("heavy", "dash"), "plunge": ("finisher", "plunge"), "release": ("medium", "cast"),
    "swarm": ("medium", "cast"), "seal": ("medium", "cast"), "domain": ("medium", "cast"), "echo": ("heavy", "combo_2"),
}

# Poses the top-down catalogue does not draw yet, each with the stand-in it plays until the character pipeline draws it.
# None: the bow batch drew the last of them (the bow's draw, the flute at the lips, the charge's wind-up, the dash slash,
# the air strike, the parry's deflection, the heavy sabre's two-handed cuts, the bell's toll, the fan's throw, the brush
# writing; `poses` and `moves` above say who plays them).
MISSING_POSES: list = []

FOES = {"roles": {"normal": "light", "elite": "medium", "boss": "heavy"}, "big_hit_share": 0.15, "big_hit": "heavy",
        "tell": "tell", "swipe": "swipe"}


def payload() -> dict:
    return {
        "look_rule": LOOK_RULE,
        "_note": "Built by tools/data/combat_feel.py; never edit by hand. Decision 38: the combat feel of the top-down world.",
        "frame_s": round(1.0 / 60.0, 6),
        "crit_hitstop_f": 2,
        "kick_s": 0.12,
        "weights": WEIGHTS,
        "order": ORDER,
        "flash": {"white_s": 0.05, "tint": "#ffb4a0", "player_hop_px": 4},
        "knock": {"hop_max_px": 10, "skid_from": 40},
        "dash_attack_s": 0.15,
        "dodge_buffer_s": 0.2,
        "families": FAMILIES,
        "forms": {k: {"weight": v[0], "pose": v[1]} for k, v in FORMS.items()},
        "moves": MOVES,
        "melody_loop": MELODY_LOOP,
        "technique_recovery_after": 0.3,
        "foes": FOES,
        "missing_poses": MISSING_POSES,
    }


def build(check_only: bool = False) -> bool:
    path = os.path.join(DATA, "combat_feel.json")
    if check_only:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            write("combat_feel.json", payload(), folder=tmp)
            fresh = open(os.path.join(tmp, "combat_feel.json"), encoding="utf-8").read()
        current = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if fresh != current:
            print("data/combat_feel.json is not current: run python3 tools/data/combat_feel.py")
            return False
        print("combat_feel.json is current")
        return True
    write("combat_feel.json", payload())
    return True


if __name__ == "__main__":
    sys.exit(0 if build("--check" in sys.argv) else 1)
