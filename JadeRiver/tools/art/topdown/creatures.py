"""The top-down foes (art bible §8 "Foes", decision 43): the prototype room's early monsters, those of chapter 2's
stretch (the Trial Puppet, the Reed Marsh's frog, leech and otter, the hollowed boarlet) and the tutorial rooms' others
(Old Snapper, the mossback toad, and the night's hollow minnow and hollowed eel), in eight facings (five drawn, SW, W
and NW mirrored in the room view).

Each species is a posed sculpture in its own module (tools/art/topdown/creature/), cast and coloured by the
character's renderer (creature/sculpt.py), in the action catalogue of creature/motion.py: idle 6, walk 8, windup 4,
attack 6 (its blow on HIT_FRAME), hurt 3 and death 8 frames. The foes grow with the people (decision 43: about 1.2x,
the body 46 px): SIZE is each species' size against its sculpture's art px; an elite is drawn ELITE times larger again,
darker, gold-eyed, in a ring of Qi (`creature.sculpt`), and the bosses (Old Snapper, the hollowed eel, the Trial Puppet)
are drawn larger by their own SIZE.

Decision 45: a boss that wakes in its second phase (the Hollowed eel, the first boss) has an `awakened` look too, its
own sheet (<species>_awakened.png): larger, its colours darker and bruised toward violet, its eyes burning red, more of
the Hollow's strands off it and the Hollow's own ring round it; its tell's rate is its awake attacks' (enemies.json
`awake`).

Each species has its own sheet (art/topdown/foes/<species>.png, its elite's apart in <species>_elite.png): a row per
drawn facing, the frames of every action along it, in a cell of its own size (the union of its frames); `build`
returns the sheets and the manifest block the room view reads (data/topdown/foes.json). The rates: idle and hurt
fixed, the walk by the species' speed, the wind-up by its shortest wind-up (enemies.json) so the tell's last frame is
up before the blow, the attack fast enough that its follow-through shows before the recovery. No randomness: a rebuild is byte-identical.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from creature import mats as M
from creature import sculpt
from creature.motion import FRAMES, HIT_FRAME

ROOT = Path(__file__).resolve().parents[3]
DIRS = ["s", "se", "e", "ne", "n"]
MIRROR = {"sw": "se", "w": "e", "nw": "ne"}
# The drawn facings' turn on the ground (east 0, south 90). As the figure's (figure/geom.py FACINGS), the side and
# back-diagonal rows are turned a little toward the camera so a face reads; the front and back rows a little off the
# axis too, so a beast facing the camera or walking away shows a flank and never reads as a capsule.
ANGLE = {"s": 80.0, "se": 48.0, "e": 14.0, "ne": -36.0, "n": -100.0}
SPECIES = ["mudshell_crab", "reedtail_rat", "wild_boarlet", "trial_puppet", "reed_frog", "marsh_leech", "reed_otter",
           "hollowed_boarlet", "old_snapper", "mossback_toad", "hollow_minnow", "hollowed_eel"]
ORDER = ["idle", "walk", "windup", "attack", "hurt", "death"]   # the sheet's column order
# Actions a species may draw past the catalogue, after it on its rows (decision 44: the leech's swim, which the room
# view plays for its walk and idle where it is in water), and their frames.
EXTRA = {"swim": 8}
LOOP = {"idle": True, "walk": True, "swim": True}
FPS = {"idle": 7, "attack": 20, "hurt": 12, "death": 10}
ELITE = 1.2          # an elite's size against its species'
MAX_SIDE = 4096      # a sheet's largest side (phones' texture limit)


class Spec:
    """A species: its pose function (action, frame) -> Pose, its size, palette, the materials its elite keeps (accents)
    or turns gold (`gold`: its eyes), whether it has an elite, whether it wears the elite's ring of Qi in its own colours
    (`aura`, a boss's presence), its blob shadow (rx, ry art px), how far one walk cycle carries it (art px at size 1,
    for the walk's rate), whether it keeps its broad side to the camera (`sideways`, the crab), whether it is posed
    at its size (`sized`, the eel against its water), whether its pose is told the facing's turn on the ground (`view`,
    creatures.ANGLE: a beast seen head-on or from behind is posed to read so, decision 44) and the actions it draws
    past the catalogue (`extra`, EXTRA's)."""

    def __init__(self, module: str, fn: str, size: float, palette: list, accents=(), elite=True, shadow=(10, 3),
                 cycle=10.0, sideways=False, glow=(), aura=False, sized=False, gold=(), view=False, extra=(), awakened=None,
                 plan=None, body=None):
        self.module, self.fn, self.size, self.palette = module, fn, size, palette
        self.plan, self.body, self._body = plan, dict(body or {}), None
        self.accents, self.elite, self.shadow, self.cycle, self.sideways, self.glow = accents, elite, shadow, cycle, sideways, glow
        self.aura, self.sized, self.gold, self.view, self.extra = aura, sized, gold, view, tuple(extra)
        # decision 45: {size (against its own), ramps {material: the awakened ramp's name}}, or None
        self.awakened = awakened

    def looks(self) -> list:
        """The looks it is drawn in: its own, its elite's, its awakened one's."""
        return ["base"] + (["elite"] if self.elite else []) + (["awakened"] if self.awakened else [])

    def actions(self) -> list:
        """Its actions in the sheet's order: the catalogue, then its extras."""
        return ORDER + list(self.extra)

    def pose(self, action: str, f: int, **kw):
        if self.plan:
            from creature import plans
            if self._body is None:
                self._body = plans.resolve(self.plan, **self.body)
            return plans.pose(self._body, action, f, **kw)
        import importlib
        mod = importlib.import_module("creature." + self.module)
        return getattr(mod, self.fn)(action, f, **kw)

    def look(self, variant: str = "base") -> sculpt.Look:
        pal = M.palette(*self.palette)
        if variant == "awakened":
            for mat, ramp in self.awakened.get("ramps", {}).items():
                pal[mat] = M.RAMPS[ramp]
        return sculpt.Look(pal, M.props(*self.palette), accents=self.accents, glow=self.glow, gold=self.gold)


# Sizes (decision 43, art bible §8 "Foes"): the people grow 1.2x (about 46 px from sole to crown) and every foe grows
# with them, about 1.2x its earlier size, so it keeps its share of a person: the crab about 32 px across its legs, the
# rat about 38 px long with its tail, the boarlets about 37 px long, the frog 20, the toad 28, the leech 32, the otter 41
# with its tail, the minnow 31 with its wake. The trial and the bosses grow more: the Trial Puppet about 51 px tall, a
# head over a disciple; Old Snapper 1.5x, about 77 px from its tail to its crusher; the hollowed eel about 1.4x, rising
# about 60 px out of the river. An elite is ELITE times its species' size.
REGISTRY = {
    "mudshell_crab": Spec("crab", "crab", 1.2, plan="crab.mud", palette=["shell", "shell_rim", "shell_pale", "crab_leg", "claw", "claw_tip", "eye"],
                          accents=("claw_tip",), gold=("eye",), shadow=(12, 4), cycle=10.0, sideways=True),
    "reedtail_rat": Spec("rat", "rat", 1.26, plan="quadruped.rodent", palette=["fur", "fur_light", "pink", "tail_a", "tail_b"], accents=("pink",),
                         shadow=(10, 3), cycle=11.0, view=True),
    "wild_boarlet": Spec("boar", "boarlet", 1.4, plan="quadruped.suid", palette=["hide", "hide_head", "stripe", "hoof", "snout", "bristle", "tusk", "pink"],
                         accents=("tusk",), shadow=(13, 4), cycle=13.0, view=True),
    "trial_puppet": Spec("puppet", "puppet", 1.58, plan="humanoid.puppet", palette=["timber", "timber_dark", "brass", "puppet_jade", "rope"],
                         accents=("puppet_jade", "brass"), elite=False, shadow=(11, 4), cycle=12.0),
    "reed_frog": Spec("frog", "frog", 1.42, plan="amphibian.frog", palette=["frog", "frog_belly", "frog_stripe", "frog_sac", "frog_eye"], accents=("frog_eye",),
                      shadow=(11, 4), cycle=6.0),
    "marsh_leech": Spec("leech", "leech", 1.44, plan="serpent.leech", palette=["leech", "leech_dark", "leech_belly", "leech_lip", "leech_maw"],
                        accents=("leech_lip",), shadow=(13, 4), cycle=8.0, view=True, extra=("swim",)),
    "reed_otter": Spec("otter", "otter", 1.44, plan="quadruped.mustelid", palette=["otter", "otter_pale", "otter_dark"], shadow=(13, 4), cycle=12.0, view=True),
    "hollowed_boarlet": Spec("boar", "hollowed", 1.4, plan="quadruped.suid", body={"mats": {"hide": "h_hide", "head": "h_head", "stripe": "h_stripe", "hoof": "h_bristle", "snout": "h_snout", "bristle": "h_bristle", "tusk": "tusk", "ear": ("h_snout", 1)}, "opts": {"hollowed": True}}, palette=["h_hide", "h_head", "h_stripe", "h_snout", "h_bristle", "tusk", "strand", "pink"],
                             accents=("tusk", "strand"), shadow=(13, 4), cycle=13.0, view=True),
    "old_snapper": Spec("snapper", "snapper", 1.8, plan="shell.snapper", palette=["snap_shell", "snap_moss", "snap_moss_lit", "snap_skin", "snap_belly", "snap_beak",
                                                   "crusher", "crusher_tip", "weed", "snap_eye", "maw"],
                        accents=("crusher", "snap_eye"), elite=False, aura=True, shadow=(26, 6), cycle=9.0),
    "mossback_toad": Spec("toad", "toad", 1.56, plan="amphibian.toad", palette=["toad", "toad_leg", "toad_belly", "toad_sac", "toad_moss", "toad_fern", "tongue",
                                                 "toad_eye", "maw"], accents=("toad_eye", "tongue"), shadow=(12, 4), cycle=7.0, view=True),
    "hollow_minnow": Spec("minnow", "minnow", 1.5, plan="fish.minnow", palette=["minnow", "minnow_back", "minnow_belly", "minnow_fin", "strand"],
                          accents=("strand",), elite=False, shadow=(5, 2), cycle=10.0),
    "hollowed_eel": Spec("eel", "eel", 1.44, plan="serpent.eel", palette=["eel", "eel_belly", "eel_fin", "eel_mouth", "strand"], accents=("strand",),
                         elite=False, shadow=(13, 4), cycle=12.0, sized=True,
                         awakened={"size": 1.22, "ramps": {"eel": "eel_wake", "eel_belly": "eel_wake_belly", "eel_fin": "eel_wake_fin",
                                                           "eel_mouth": "eel_wake_mouth", "strand": "strand_wake"}}),
}


def draw(species: str, action: str, f: int, facing: str, elite="base") -> np.ndarray:
    """One frame on the working canvas (RGBA), the feet on sculpt.FOOT; `elite` the look (base, elite, awakened; a bool
    for the elite)."""
    variant = ("elite" if elite else "base") if isinstance(elite, bool) else str(elite)
    elite = variant == "elite"
    sp = REGISTRY[species]
    yaw = ANGLE[facing]
    kw = {}
    if sp.sideways:
        # The crab keeps its broad side to the camera, front or back, and scuttles sideways: `aim` is where it faces
        # in its own frame.
        yaw = 90.0 if facing in ("s", "se", "e") else -90.0
        g, y = math.radians(ANGLE[facing]), math.radians(yaw)
        kw["aim"] = (math.cos(g - y), -math.sin(g - y))
    k = sp.size * (ELITE if elite else 1.0) * (float(sp.awakened.get("size", 1.0)) if variant == "awakened" else 1.0)
    if variant == "awakened":
        kw["awake"] = True
    if sp.sized:
        kw["k"] = k            # a creature laid out against a fixed world height (the eel's water) is posed at its size
    if sp.view:
        kw["view"] = ANGLE[facing]
    P = sp.pose(action, f, **kw)
    P.k = k
    return sculpt.picture(P, yaw, sp.look(variant), elite, f, "hollow" if variant == "awakened" else sp.aura)


def _enemies() -> dict:
    d = json.loads((ROOT / "data/enemies.json").read_text())
    return {e["id"]: e for e in d["entries"]}


def rates(species: str, enemies: dict, variant: str = "base") -> dict:
    """Each action's frame rate: the walk's by the species' speed (a cycle over `cycle` px at its size), the wind-up's so
    its last frame (the tell) is up within 70% of its shortest wind-up (enemies.json; the awakened look's by its `awake`
    attacks, the others' by the rest)."""
    sp = REGISTRY[species]
    e = enemies.get(species, {})
    fps = dict(FPS)
    speed = float(e.get("ai", {}).get("move_speed", 60)) * 0.5            # world units to art px (TopdownRoom.ART)
    fps["walk"] = int(max(8, min(16, round(FRAMES["walk"] * speed / (sp.cycle * sp.size)))))
    mine = [a for a in e.get("attacks", []) if bool(a.get("awake", False)) == (variant == "awakened")]
    wind = min([float(a.get("windup_s", 0.5)) for a in mine] or [0.5])
    fps["windup"] = int(math.ceil((FRAMES["windup"] - 1) / (0.7 * wind)))
    fps["swim"] = fps["walk"]
    return fps


def frames_of(action: str) -> int:
    return FRAMES[action] if action in FRAMES else EXTRA[action]


def _job(args):
    species, elite, facing = args
    return [draw(species, a, f, facing, elite) for a in REGISTRY[species].actions() for f in range(frames_of(a))]


def build(jobs: int = 1, only=None) -> tuple[dict, dict]:
    """The foe sheets ({path: PIL image}) and their manifest block."""
    from PIL import Image
    enemies = _enemies()
    tasks = [(sp, el, d) for sp in SPECIES if sp in REGISTRY and (only is None or sp in only)
             for el in REGISTRY[sp].looks() for d in DIRS]
    if jobs > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(jobs) as pool:
            done = pool.map(_job, tasks, chunksize=1)
    else:
        done = [_job(t) for t in tasks]
    frames = dict(zip(tasks, done))
    sheets, species = {}, {}
    for sp in SPECIES:
        if sp not in REGISTRY or (only is not None and sp not in only):
            continue
        order = REGISTRY[sp].actions()
        n = sum(frames_of(a) for a in order)
        block: dict = {}
        for el in REGISTRY[sp].looks():
            fps = rates(sp, enemies, el)
            # Its own sheet and cell (the union of its frames): an elite's rows load only where an elite stands.
            al = np.zeros(frames[(sp, el, DIRS[0])][0].shape[:2], dtype=bool)
            for d in DIRS:
                for im in frames[(sp, el, d)]:
                    al |= im[..., 3] > 0
            ys, xs = np.nonzero(al)
            x0, x1 = xs.min() - 1, xs.max() + 2
            y0, y1 = ys.min() - 1, ys.max() + 2
            cw, ch = int(x1 - x0), int(y1 - y0)
            per = max(1, min(n, MAX_SIDE // cw))
            rows_per = -(-n // per)
            sheet = Image.new("RGBA", (per * cw, len(DIRS) * rows_per * ch), (0, 0, 0, 0))
            acts: dict = {}
            for di, d in enumerate(DIRS):
                i = 0
                for a in order:
                    entry = acts.setdefault(a, {"fps": fps[a], "loop": LOOP.get(a, False), "frames": {}})
                    lst = []
                    for _ in range(frames_of(a)):
                        col, r = i % per, di * rows_per + i // per
                        sheet.paste(Image.fromarray(np.ascontiguousarray(frames[(sp, el, d)][i][y0:y1, x0:x1]), "RGBA"), (col * cw, r * ch))
                        lst.append([col * cw, r * ch])
                        i += 1
                    entry["frames"][d] = lst
            acts["attack"]["hit_frame"] = HIT_FRAME
            # How far the figure rises over its feet (art px) in its idle frame facing the camera: the view stands the
            # foe's label (its HP bar and plate) on its head there.
            idle = frames[(sp, el, "s")][0][..., 3] > 0
            iy = np.nonzero(idle.any(axis=1))[0]
            top = int(sculpt.FOOT[1] - iy.min()) if len(iy) else int(sculpt.FOOT[1] - y0)
            k = ELITE if el == "elite" else (float(REGISTRY[sp].awakened.get("size", 1.0)) if el == "awakened" else 1.0)
            shadow = [int(round(REGISTRY[sp].shadow[0] * k)), int(round(REGISTRY[sp].shadow[1] * k))]
            path = "art/topdown/foes/%s%s.png" % (sp, "" if el == "base" else "_" + el)
            v = {"actions": acts, "shadow": shadow, "top": top, "atlas": "res://" + path, "cell": [cw, ch],
                 "foot": [int(sculpt.FOOT[0] - x0), int(sculpt.FOOT[1] - y0)]}
            sheets[path] = sheet
            if el != "base":
                block[el] = v
            else:
                block.update(v)
        species[sp] = block
    return sheets, {"dirs": DIRS, "mirror": MIRROR, "species": species,
                    "note": "the top-down foes in eight facings (five drawn, three mirrored), a sheet a species (its elite's "
                            "apart), built by tools/art/topdown/build_foes.py"}
