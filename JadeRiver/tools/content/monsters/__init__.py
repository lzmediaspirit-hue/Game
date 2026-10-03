"""The monster engine (audit 45 §6.2, decision 45): a species is one `species(...)` spec, and the engine writes
everything a species is made of from it, through the generators that already exist:

  the enemies.json row and its loot table   tools/data/enemies.py (mob(), atk(), d()): `data`, `loot`
  the top-down sheets and foes.json block    tools/art/topdown/creatures.py and build_foes.py: the body plan
                                             (`plan`, `parts`, `mats`, `motion`) and the art fields (`size`, `palette`...)
  its voice in sound.json                     tools/data/sound.py: `sound`
  its codex page and the wiki                 the row's collection `page`; tools/dev/wiki.py writes the wiki from data/

Specs live in tools/content/monsters/specs/*.py (one file a region), as Python literals. A spec names intent (a body
plan and its variant, part sizes, motion styles, the data's numbers) and the engine leaves frames, coordinates and
rows to the generators. Deterministic: no randomness; where a plan varies a species' look (a pebble's place, a fleck),
it hashes the species' id (`Body.seed`), so the seed is the id. `python3 tools/content/monsters/build.py --check`
checks every spec, its round trip through the data and its sheets.

Escape hatch: `pose="creature.rat:rat"` draws a species with a hand-written pose module (tools/art/topdown/creature/)
in place of a plan, so a species a plan cannot draw well keeps its own.

docs/architecture/monster_engine.md: the plans, the spec format, how to add a species and the review steps.
"""
from __future__ import annotations

import copy
import importlib
import pkgutil
import zlib

# What a spec may say about its picture (creatures.Spec): the size against its sculpture, its palette (mats.RAMPS
# names), the materials its elite keeps (`accents`) or turns gold (`gold`), whether it has an elite, its boss ring
# (`aura`), its blob shadow, the walk cycle's length, the crab's `sideways`, the eel's `sized`, the beasts' `view`, the
# actions past the catalogue (`extra`), a boss's awakened look, its glow materials.
ART_KEYS = ("size", "palette", "accents", "gold", "glow", "elite", "aura", "shadow", "cycle", "sideways", "sized", "view",
            "extra", "awakened")
# The voice families sound.py names (the creatures whose shell, slime or wood their race does not say).
BODIES = ("shell", "slime", "wood")
TELLS = ("water",)


class Species:
    """One spec: `id`, the body plan (`plan` "plan.variant" with `parts`, `mats`, `motion`, `opts`) or a hand module
    (`pose` "creature.module:function"), the art fields, `data` (the enemies row: level, role, element, page, drops,
    attacks, then any mob() field in order), `loot` (starter, finds, quest) and `sound` ("race", or the named body and
    tell)."""

    def __init__(self, id: str, plan=None, pose=None, parts=None, mats=None, motion=None, opts=None, data=None, loot=None,
                 sound="race", source="", **art):
        bad = [k for k in art if k not in ART_KEYS]
        if bad:
            raise TypeError("species %s: unknown fields %s" % (id, ", ".join(bad)))
        if bool(plan) == bool(pose):
            raise TypeError("species %s: name a body plan (plan=) or a hand module (pose=), one of them" % id)
        self.id, self.plan, self.pose = id, plan, pose
        self.parts, self.mats, self.motion, self.opts = dict(parts or {}), dict(mats or {}), dict(motion or {}), dict(opts or {})
        self.data, self.loot, self.sound, self.art, self.source = dict(data or {}), dict(loot or {}), sound, art, source

    @property
    def seed(self) -> int:
        """The species' seed: its id, hashed (crc32)."""
        return zlib.crc32(self.id.encode("utf-8"))


_REG: dict = {}
_LOADED = False


def species(id: str, **kw) -> Species:
    """Declare a species (called by the spec files)."""
    if id in _REG:
        raise ValueError("species %s is declared twice (%s and %s)" % (id, _REG[id].source, kw.get("source", "")))
    sp = Species(id, **kw)
    _REG[id] = sp
    return sp


def load() -> dict:
    """Every spec, in the order of the spec files (sorted by name) and of the calls in each."""
    global _LOADED
    if not _LOADED:
        _LOADED = True
        from . import specs
        for info in sorted(pkgutil.iter_modules(specs.__path__), key=lambda i: i.name):
            mod = importlib.import_module(specs.__name__ + "." + info.name)
            for sp in _REG.values():
                sp.source = sp.source or mod.__name__.rsplit(".", 1)[-1]
    return _REG


def ids() -> list:
    return list(load())


def get(id: str) -> Species:
    return load()[id]


# ------------------------------------------------------------------------------------------------ data
def row(id: str, mob, atk, drop) -> dict:
    """The species' enemies.json row, through enemies.py's own mob(), atk() and d() (passed in, so the row is made
    exactly as a hand-written one is)."""
    sp = get(id)
    d = copy.deepcopy(sp.data)
    levels, role, element = d.pop("level"), d.pop("role"), d.pop("element")
    page = d.pop("page", None)
    drops = [drop(*x) if isinstance(x, (tuple, list)) else drop(**x) for x in d.pop("drops", [])]
    attacks = [_attack(atk, a) for a in d.pop("attacks")]
    return mob(id, levels, role, element, page, drops, attacks, **d)


def _attack(atk, a):
    """An attack: (id, windup, reach[, mult][, {extras}]) or a dict of atk()'s fields."""
    if isinstance(a, dict):
        return atk(**a)
    args = list(a)
    extra = args.pop() if args and isinstance(args[-1], dict) else {}
    return atk(*args, **extra)


def rows(placed, mob, atk, drop) -> list:
    """The rows of the specs enemies.py has not placed by hand (a new species' row needs no other file): after the
    others, in the specs' order."""
    return [row(i, mob, atk, drop) for i in ids() if i not in placed]


def loot(id: str) -> dict:
    """The species' loot extras for enemies.py's loot table: `starter` (the first rooms' foes: starter gear),
    `finds` (rare rows: "early" for the early surprises, or a list of rows) and `quest` (rows that drop while a quest
    wants them)."""
    return dict(get(id).loot) if id in load() else {}


def voices() -> dict:
    """id -> {"body": "shell" | "slime" | "wood", "tell": "tell_water"} for every spec (an empty dict: its race's voice)."""
    out = {}
    for i, sp in load().items():
        v = {} if sp.sound in (None, "race") else dict(sp.sound)
        if v.get("body") and v["body"] not in BODIES:
            raise ValueError("species %s: sound body %r is not one of %s" % (i, v["body"], ", ".join(BODIES)))
        if v.get("tell"):
            t = v["tell"][len("tell_"):] if v["tell"].startswith("tell_") else v["tell"]
            if t not in TELLS:
                raise ValueError("species %s: sound tell %r is not one of %s" % (i, v["tell"], ", ".join(TELLS)))
            v["tell"] = "tell_" + t
        out[i] = v
    return out


# ------------------------------------------------------------------------------------------------ art
def art(id: str) -> dict:
    """The keyword arguments of the species' creatures.Spec: its pose (a plan and its body, or a hand module) and its
    art fields."""
    sp = get(id)
    kw = dict(sp.art)
    if sp.pose:
        kw["pose"] = sp.pose
    else:
        kw["plan"] = sp.plan
        kw["body"] = {"parts": sp.parts, "mats": sp.mats, "motion": sp.motion, "opts": dict(sp.opts, seed=sp.seed, id=sp.id)}
    return kw
