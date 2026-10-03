"""Body plans (audit 45 §6.2, the monster engine): the pose functions the foes are drawn with, each extracted from the
species first drawn by hand with it, parameterised by part sizes and motion styles.

  quadruped  rodent, mustelid, suid    the reed rat, the reed otter, the boarlets (and the hollowed boarlet)
  amphibian  frog, toad                the reed frog, the mossback toad
  crab       mud                       the mud crab
  serpent    eel, leech                the hollowed eel, the marsh leech
  fish       minnow, greyfin           the hollow minnow; the greyfin (E2's first new species)
  shell      snapper, beetle           Old Snapper; the rock beetle (new)
  humanoid   puppet, imp               the Trial Puppet; the pebble imp (new)
  person     fighter, archer, brute    M1: the human foes, the shared character body dressed in their outfit and cast by
                                       the character's own pipeline (figure/), not sculpted

A species names its plan and variant ("quadruped.rodent"), and may lay its own parts, materials and motion over the
variant's (`resolve`); its sheet is then drawn by the plan's `pose(body, action, frame, **facing)`, cast and coloured by
creature/sculpt.py like any hand-drawn species. docs/architecture/monster_engine.md has the plans' parts and styles.
"""
from __future__ import annotations

import importlib

from .kit import Body, merge

PLANS = ("quadruped", "amphibian", "crab", "serpent", "fish", "shell", "humanoid", "person")


def module(plan: str):
    if plan not in PLANS:
        raise KeyError("no body plan %r (plans: %s)" % (plan, ", ".join(PLANS)))
    return importlib.import_module(__name__ + "." + plan)


def variants(plan: str) -> list:
    return list(module(plan).VARIANTS)


def styles(plan: str) -> dict:
    return module(plan).STYLES


def resolve(name: str, parts=None, mats=None, motion=None, opts=None) -> Body:
    """A species' body: its plan's variant (`name` "plan.variant") with the spec's parts, materials, motion and options
    laid over it."""
    plan, _, variant = name.partition(".")
    mod = module(plan)
    if variant not in mod.VARIANTS:
        raise KeyError("%s: no variant %r (variants: %s)" % (plan, variant, ", ".join(mod.VARIANTS)))
    v = mod.VARIANTS[variant]
    return Body(plan, variant, merge(v["parts"], parts), merge(v["mats"], mats), merge(v["motion"], motion), mod.STYLES,
                merge(v.get("opts", {}), opts))


def pose(body: Body, action: str, f: int, **kw):
    """The species posed for frame `f` of `action` (a creature/sculpt.py Pose)."""
    return module(body.plan).pose(body, action, f, **kw)
