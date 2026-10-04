"""The monster engine's command line (audit 45 §6.2; docs/architecture/monster_engine.md). Run from JadeRiver/:

    python3 tools/content/monsters/build.py               # write what the specs make: the data (build_data.py, which
                                                         # writes the wiki after) and the sheets (build_foes.py)
    python3 tools/content/monsters/build.py --check      # the engine's checks (the runners' `monsters` gate)
    python3 tools/content/monsters/build.py --list       # the specs: id, plan (or hand module), size, where declared
    python3 tools/content/monsters/build.py --review ID  # a species' review images (build_foes.py --only ID --review):
                                                         # docs/redesign/feedback/monsters/sheets/<ID>_x3.png and the GIF
    python3 tools/content/monsters/build.py --update ID[,ID]  # M1: the data, then only those species' sheets and their
                                                         # foes.json blocks (build_foes.py --update), the rest as they are

--check, without writing anything:
  specs     every spec resolves: its plan and variant, every motion style it names, its palette's ramps, its accents
            and gold among its palette, its voice a family sound.py knows; a hand module (the escape hatch) loads
  poses     every species poses every action of the catalogue (and its extras) for its frames in the five drawn facings,
            in each look; the catalogue's frame counts and the blow's frame (HIT_FRAME) are the sheets'
  data      every spec's enemies.json row is the row its spec makes (mob(), atk(), d()); its loot table carries its
            starter mark, its finds and its quest drops; sound.json names its voice
  sheets    data/topdown/foes.json has every spec's block (its elite and awakened looks where it has them, the blow on
            frame 1), every sheet is on disk; sampled frames drawn twice are the same, and the same as the sheet's cell
  elite     an elite's look wears the ring of Qi (pale gold round its outline), its species' own does not
  hatch     a spec naming a hand module (`pose=`) draws through it
Exit 0 when all pass, 1 otherwise; the last line reads "monsters: N checks, M failures".
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOLS = ROOT / "tools"
for p in (TOOLS, TOOLS / "data", TOOLS / "art", TOOLS / "art" / "topdown"):
    if str(p) not in sys.path:
        sys.path.append(str(p))

from content import monsters as MON  # noqa: E402

# The frames drawn twice and compared with the sheet on disk: (action, frame, facing).
SAMPLES = (("idle", 0, "s"), ("windup", -1, "se"), ("attack", 1, "e"), ("death", -1, "ne"))


class Checks:
    def __init__(self):
        self.n = 0
        self.fails = []

    def check(self, ok: bool, what: str) -> bool:
        self.n += 1
        if not ok:
            self.fails.append(what)
            print("FAIL:", what)
        return ok


def _hatch_pose(action: str, f: int, **kw):
    """A stand-in hand module for the escape hatch's check: the reed rat's plan, called as a hand module is."""
    from creature import plans
    return plans.pose(plans.resolve("quadruped.rodent"), action, f, **kw)


def check_specs(C: Checks) -> None:
    import creatures
    from creature import mats as M
    from creature import plans
    sound = __import__("sound")
    for sid, sp in MON.load().items():
        spec = creatures.REGISTRY[sid]
        if sp.plan:
            try:
                body = spec.resolved()
                ok = body.plan in plans.PLANS
            except (KeyError, TypeError) as e:
                print("   ", sid, e)
                ok = False
            C.check(ok, "%s: its plan %s resolves (variant, parts, motion styles)" % (sid, sp.plan))
        else:
            mod, _, fn = sp.pose.partition(":")
            try:
                import importlib
                ok = callable(getattr(importlib.import_module(mod), fn))
            except (ImportError, AttributeError):
                ok = False
            C.check(ok, "%s: its hand module %s loads" % (sid, sp.pose))
        pal = list(spec.palette)
        # A person (plans/person.py) is coloured by its outfit's own palettes, so it names no ramps of its own.
        person = str(sp.plan or "").startswith("person.")
        C.check((bool(pal) or person) and all(n in M.RAMPS for n in pal), "%s: every palette material is a ramp (%s)" % (
            sid, [n for n in pal if n not in M.RAMPS]))
        if person:
            av = sp.data.get("art", {}).get("avatar", {})
            # M3: the Reflection's row wears the player's own avatar ("player", the side view's); its sheet names the
            # outfit it is cast in (`parts.outfit`).
            mirror = av == "player" and isinstance(sp.parts.get("outfit"), dict) and sp.parts["outfit"].get("body") == "light"
            C.check(mirror or isinstance(av, dict) and av.get("body") == "light" and bool(av.get("name")),
                    "%s: a person's row has its outfit (art.avatar, content.monsters.person)" % sid)
        C.check(set(spec.accents) <= set(pal) and set(spec.gold) <= set(pal), "%s: its accents and gold are in its palette" % sid)
        if spec.awakened:
            C.check(all(r in M.RAMPS for r in spec.awakened.get("ramps", {}).values()), "%s: its awakened ramps exist" % sid)
        v = MON.voices()[sid]
        C.check(v.get("body") in (None,) + MON.BODIES and v.get("tell") in (None, "tell_water"), "%s: its voice is one sound.py knows" % sid)
    C.check(callable(sound.payload), "sound.py loads with the specs' voices")


def check_poses(C: Checks) -> None:
    import creatures
    from creature.motion import FRAMES, HIT_FRAME
    C.check(FRAMES == {"idle": 6, "walk": 8, "windup": 4, "attack": 6, "hurt": 3, "death": 8} and HIT_FRAME == 1,
            "the catalogue: idle 6, walk 8, windup 4, attack 6 (the blow on frame 1), hurt 3, death 8")
    for sid in MON.ids():
        spec = creatures.REGISTRY[sid]
        bad = []
        for look in spec.looks():
            for d in creatures.DIRS:
                kw = _kw(creatures, spec, d, look)
                for a in spec.actions():
                    for f in range(creatures.frames_of(a)):
                        try:
                            P = spec.pose(a, f, **kw)
                            if not P.parts:
                                bad.append("%s %s %s %d: no parts" % (look, d, a, f))
                        except Exception as e:  # noqa: BLE001 - a pose that fails is the finding
                            bad.append("%s %s %s %d: %s" % (look, d, a, f, e))
        C.check(not bad, "%s: poses every action and frame in the five facings and its looks (%s)" % (sid, bad[:3]))


def _kw(creatures, spec, facing: str, look: str) -> dict:
    """The keywords creatures.draw passes a pose (without drawing)."""
    kw = {}
    if spec.sideways:
        yaw = 90.0 if facing in ("s", "se", "e") else -90.0
        g, y = math.radians(creatures.ANGLE[facing]), math.radians(yaw)
        kw["aim"] = (math.cos(g - y), -math.sin(g - y))
    k = spec.size * (creatures.ELITE if look == "elite" else 1.0) * (float(spec.awakened.get("size", 1.0)) if look == "awakened" else 1.0)
    if look == "awakened":
        kw["awake"] = True
    if spec.sized:
        kw["k"] = k
    if spec.view:
        kw["view"] = creatures.ANGLE[facing]
    return kw


def check_data(C: Checks) -> None:
    import enemies as E
    rows = {r["id"]: r for r in json.loads((ROOT / "data/enemies.json").read_text())["entries"]}
    loot = {r["id"]: r for r in json.loads((ROOT / "data/loot_tables.json").read_text())["entries"]}
    snd = json.loads((ROOT / "data/sound.json").read_text())["foes"]
    for sid in MON.ids():
        want = MON.row(sid, E.mob, E.atk, E.d)
        # The passes enemies.py makes over every row after: races, beast ranks and natures, a boss's par time.
        E.beast_ranks([want])
        if sid in E.BOSS_PAR_S:
            want["par_s"] = E.BOSS_PAR_S[sid]
            want.pop("hp_mult", None)
        C.check(rows.get(sid) == json.loads(json.dumps(want)), "%s: its enemies.json row is the one its spec makes" % sid)
        L = MON.loot(sid)
        t = loot.get(sid, {})
        C.check(bool(t), "%s: it has a loot table" % sid)
        C.check(bool(t.get("starter", False)) == bool(L.get("starter", False)), "%s: its loot table's starter mark is its spec's" % sid)
        finds = E._EARLY if L.get("finds") == "early" else (L.get("finds") or [])
        C.check(all(x in t.get("rare", []) for x in finds), "%s: its finds are in its loot table's rare rows" % sid)
        C.check(all(x in t.get("quest_drops", []) for x in L.get("quest", [])), "%s: its quest drops are in its loot table" % sid)
        v = MON.voices()[sid]
        C.check(snd["body"].get(sid) == v.get("body") and snd["tell"].get(sid) == v.get("tell"),
                "%s: sound.json gives it its spec's voice (%s)" % (sid, v or "its race's"))


def check_sheets(C: Checks) -> None:
    import numpy as np
    from PIL import Image
    import creatures
    from creature import sculpt
    man = json.loads((ROOT / "data/topdown/foes.json").read_text())
    C.check(man.get("dirs") == creatures.DIRS and man.get("mirror") == creatures.MIRROR, "foes.json: five drawn facings, three mirrored")
    for sid in MON.ids():
        spec = creatures.REGISTRY[sid]
        block = man["species"].get(sid)
        if not C.check(block is not None, "%s: foes.json has its block" % sid):
            continue
        looks = {"base": block}
        looks.update({v: block[v] for v in ("elite", "awakened") if v in block})
        C.check(sorted(looks) == sorted(spec.looks()), "%s: its looks in foes.json are its spec's (%s)" % (sid, sorted(looks)))
        for look, lk in looks.items():
            path = ROOT / lk["atlas"][len("res://"):]
            if not C.check(path.exists(), "%s %s: its sheet is on disk" % (sid, look)):
                continue
            acts = lk["actions"]
            C.check(all(len(acts[a]["frames"][d]) == creatures.frames_of(a) for a in spec.actions() for d in creatures.DIRS)
                    and acts["attack"].get("hit_frame") == 1, "%s %s: every action's frames in every facing, the blow on frame 1" % (sid, look))
            sheet = np.asarray(Image.open(path).convert("RGBA"))
            cw, ch = lk["cell"]
            fx, fy = lk["foot"]
            for a, f, d in SAMPLES:
                f = f % creatures.frames_of(a)
                one = creatures.draw(sid, a, f, d, look)
                two = creatures.draw(sid, a, f, d, look)
                C.check(np.array_equal(one, two), "%s %s %s %d %s: drawn twice, the same" % (sid, look, a, f, d))
                x, y = acts[a]["frames"][d][f]
                cell = sheet[y:y + ch, x:x + cw]
                x0, y0 = creatures.foot_of(sid)[0] - fx, creatures.foot_of(sid)[1] - fy
                # The frame in its cell (a cell may run past the working canvas by its margin: that part is empty).
                drawn = np.zeros((ch, cw, 4), np.uint8)
                part = one[y0:y0 + ch, x0:x0 + cw]
                drawn[:part.shape[0], :part.shape[1]] = part
                outside = one.copy()
                outside[y0:y0 + ch, x0:x0 + cw] = 0
                C.check(np.array_equal(drawn, cell) and not (outside[..., 3] > 0).any(),
                        "%s %s %s %d %s: the sheet on disk is what the spec draws (build_foes.py)" % (sid, look, a, f, d))


def check_elite(C: Checks) -> None:
    import numpy as np
    import creatures
    from creature import sculpt
    gold = np.array(sculpt.AURA["gold"]["main"])
    for sid in MON.ids():
        spec = creatures.REGISTRY[sid]
        if not spec.elite:
            continue
        base = creatures.draw(sid, "idle", 0, "se", "base")
        el = creatures.draw(sid, "idle", 0, "se", "elite")
        ring = (np.all(el[..., :3] == gold, axis=-1) & (el[..., 3] > 0)).sum()
        none = (np.all(base[..., :3] == gold, axis=-1) & (base[..., 3] > 0)).sum()
        C.check(ring > 20 and none == 0 and (el[..., 3] > 0).sum() > (base[..., 3] > 0).sum(),
                "%s: its elite is larger and wears the ring of Qi (%d ring px), its own look none" % (sid, ring))


def check_hatch(C: Checks) -> None:
    import numpy as np
    import creatures
    hatch = creatures.Spec(pose="content.monsters.build:_hatch_pose", size=1.26, palette=["fur", "fur_light", "pink", "tail_a", "tail_b"],
                           accents=("pink",), view=True)
    plan = creatures.Spec(plan="quadruped.rodent", size=1.26, palette=["fur", "fur_light", "pink", "tail_a", "tail_b"], accents=("pink",), view=True)
    from creature import sculpt
    a = sculpt.picture(hatch.pose("attack", 1, view=48.0), 48.0, hatch.look(), False, 1)
    b = sculpt.picture(plan.pose("attack", 1, view=48.0), 48.0, plan.look(), False, 1)
    C.check(np.array_equal(a, b) and (a[..., 3] > 0).any(), "the escape hatch: a spec's hand module (pose=) draws the species")
    C.check(MON.get(MON.ids()[0]).seed != MON.get(MON.ids()[1]).seed, "each species' seed is its own (its id hashed)")


def run_check() -> int:
    C = Checks()
    for part in (check_specs, check_poses, check_data, check_sheets, check_elite, check_hatch):
        part(C)
    print("monsters: %d checks, %d failures (%d species: %s)" % (C.n, len(C.fails), len(MON.ids()), ", ".join(MON.ids())))
    return 1 if C.fails else 0


def main(argv: list) -> int:
    os.chdir(ROOT)
    if "--check" in argv:
        return run_check()
    if "--list" in argv:
        import creatures
        for sid, sp in MON.load().items():
            spec = creatures.REGISTRY[sid]
            print("%-20s %-20s size %-5s %-8s %s" % (sid, sp.plan or "pose=" + sp.pose, spec.size, "+".join(spec.looks()), sp.source))
        return 0
    if "--review" in argv:
        sid = argv[argv.index("--review") + 1]
        return subprocess.call([sys.executable, str(TOOLS / "art/topdown/build_foes.py"), "--only", sid])
    jobs = argv[argv.index("--jobs") + 1] if "--jobs" in argv else "2"
    code = subprocess.call([sys.executable, str(TOOLS / "data/build_data.py")])
    if "--update" in argv:
        return code or subprocess.call([sys.executable, str(TOOLS / "art/topdown/build_foes.py"), "--jobs", jobs, "--update",
                                        argv[argv.index("--update") + 1]])
    return code or subprocess.call([sys.executable, str(TOOLS / "art/topdown/build_foes.py"), "--jobs", jobs])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
