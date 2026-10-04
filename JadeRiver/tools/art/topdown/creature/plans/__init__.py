"""Body plans (audit 45 §6.2, the monster engine): the pose functions the foes are drawn with, each extracted from the
species first drawn by hand with it, parameterised by part sizes and motion styles.

  quadruped  rodent, mustelid, suid    the reed rat, the reed otter, the boarlets (and the hollowed boarlet);
             canine, talpid            M1: the mud hound and the ember fox (the canine head kind the wolves and foxes
                                       after them take); the ironclaw mole
  amphibian  frog, toad                the reed frog, the mossback toad
  crab       mud                       the mud crab (M1: the tide crab, its great claw and pearls)
  serpent    eel, leech, viper         the hollowed eel, the marsh leech; M1: the green viper
  fish       minnow, greyfin           the hollow minnow; the greyfin (E2's first new species); M1: the jade carp
  shell      snapper, beetle, tortoise Old Snapper; the rock beetle (new); M1: the stone tortoise
  humanoid   puppet, imp, monkey,      the Trial Puppet; the pebble imp (new); M1: the bamboo monkey, the stone guardian
             guardian
  person     fighter, archer, brute    M1: the human foes, the shared character body dressed in their outfit and cast by
                                       the character's own pipeline (figure/), not sculpted
  bird       chick                     M1: the jade crane chick
  spirit     talisman                  M1: the paper talisman ghost
  insect     drone, moth               M4: the hollow drone, the orbit moth (flying insects, two pairs of wings)

A species names its plan and variant ("quadruped.rodent"), and may lay its own parts, materials and motion over the
variant's (`resolve`); its sheet is then drawn by the plan's `pose(body, action, frame, **facing)`, cast and coloured by
creature/sculpt.py like any hand-drawn species. docs/architecture/monster_engine.md has the plans' parts and styles.
"""
from __future__ import annotations

import importlib

from .kit import Body, merge

PLANS = ("quadruped", "amphibian", "crab", "serpent", "fish", "shell", "humanoid", "person", "bird", "spirit", "insect")


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
