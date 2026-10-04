"""The quest engine (decision 45, audit 45 §6.5; docs/architecture/quest_engine.md): side quests and the daily mission
board as specs, compiled into the rows the game reads.

    python3 tools/content/quests/engine.py --check       # the engine's gate (tools/run_tests.sh, Test.ps1)
    python3 tools/content/quests/engine.py --list        # every quest: its band, room, realm and pay
    python3 tools/content/quests/engine.py --show ID     # one quest: the row, and what was derived and pinned
    python3 tools/content/quests/engine.py --bands       # the band table: Levels, need, cultivation, pay
    python3 tools/content/quests/engine.py --diffs       # the quests that pay otherwise than their band, or sit far from their room

A spec (specs/<module>.py, spec.py) writes:
- the quest's quests.json row (story.py places each section with `rows(section)` among its hand quests and calls
  `settle(Q)` once quest_tiers has found every tier), deriving
    - `target_room` from where the target is: the room where a foe spawns most, where what it drops or a node yields
      is, where a person stands (the built rooms, data/rooms; the loot of the monster engine, data/loot_tables.json),
    - `requires`' realm from the target room's band of Levels,
    - its pay from the band table at its tier (bands.py), the cultivation following the same tier (quest_tiers);
- the daily mission board's templates (economy.py's missions() takes `missions()`).
Its strings follow the rows: economy.py's strings() reads the built quests (a quest that teaches an art names it).
Deterministic: no randomness; every derived value can be pinned in the spec.
"""
import copy
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
DATA = os.path.join(ROOT, "data")
for _p in (os.path.join(TOOLS, "data"), TOOLS):
    if _p not in sys.path:
        sys.path.append(_p)

if __name__ == "__main__" and not __package__:
    # Run as a script: the package's own module runs the command line, so the specs and the CLI share one compile.
    from content.quests import engine as _engine
    raise SystemExit(_engine.main())

from .spec import AUTO, DROP, ORDER, PAY, ROOM, SpecError  # noqa: E402
from . import bands as B  # noqa: E402

NODES = ("herb_patch", "ore_vein", "insect_swarm", "star_sight")   # the room objects a template's item comes from
BOARD_TOP = 70        # the daily board's last Level (a job posted "at any Level" runs to it)
SMALL = {"of", "the", "and", "in", "to", "a", "on", "for", "from", "over", "at", "by", "with"}   # a title's small words


def titled(snake):
    words = snake.split("_")
    return " ".join(w if (i and w in SMALL) else w.capitalize() for i, w in enumerate(words))


def plural(name, n=2):
    """A name as the quest log counts it: "Marsh Leeches", "Mist Wolves", "Bamboo Monkeys"; a name ending in s
    (Willow Moss, Mist Lotus) as it is."""
    if n == 1 or name.endswith("s"):
        return name
    if name.endswith(("ch", "sh", "x")):
        return name + "es"
    if name.endswith("y") and name[-2:-1] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith("f"):
        return name[:-1] + "ves"
    return name + "s"


# ------------------------------------------------------------------------------------------------ the world it reads
def _read(*parts):
    path = os.path.join(DATA, *parts)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class World:
    """What the derived values read: the built rooms (each one's band of Levels, its spawns, nodes, people and spar
    posts), the foes' loot, and the names of foes, items, people and rooms."""

    def __init__(self, rooms, loot=(), enemies=(), items=(), npcs=(), homes=None):
        self.rooms = {r["id"]: r for r in rooms}
        self.loot = {r["id"]: r for r in loot}
        self.enemies = {r["id"]: r for r in enemies}
        self.items = {r["id"]: r for r in items}
        self.npcs = {r["id"]: r for r in npcs}
        self.homes = dict(homes or {})   # npc -> its home room (the NPC engine's first place)

    @classmethod
    def from_data(cls):
        rooms = []
        for f in sorted(os.listdir(os.path.join(DATA, "rooms"))):
            if f.endswith(".json"):
                rooms.append(_read("rooms", f))
        items = _read("items.json")["entries"] + _read("artifacts.json")["entries"]
        from content.npcs import engine as NE
        homes = {s["id"]: s["at"][0]["room"] for s in NE.state().npcs if s["at"]}
        return cls(rooms, _read("loot_tables.json")["entries"], _read("enemies.json")["entries"], items,
                   _read("npcs.json")["entries"], homes)

    def band(self, rid):
        lr = (self.rooms.get(rid) or {}).get("level_range") or [0, 0]
        return (int(lr[0]), int(lr[-1])) if int(lr[0]) > 0 else None

    def _pick(self, weights):
        """The room with the most, then the lowest band, then the first by id."""
        if not weights:
            return None
        return min(weights, key=lambda r: (-weights[r], (self.band(r) or (0, 0))[0], r))

    def _spawns(self, enemy, weights):
        for rid, r in self.rooms.items():
            for s in r.get("spawns", []):
                if s.get("enemy") == enemy and not s.get("wild_pet") and "requires" not in s:
                    weights[rid] = weights.get(rid, 0) + int(s.get("max", 1))

    def droppers(self, item, qid=None):
        """The foes whose loot carries `item` (and those that drop it for quest `qid` only)."""
        out = []
        for eid, e in self.enemies.items():
            t = self.loot.get(e.get("loot", eid)) or {}
            picks = [p for g in t.get("groups", []) for p in g.get("pick", [])] + t.get("rare", [])
            picks += [p for p in t.get("quest_drops", []) if p.get("quest") == qid]
            if any(p.get("item") == item for p in picks):
                out.append(eid)
        return out

    def _nodes(self, item, weights):
        for rid, r in self.rooms.items():
            for ob in r.get("objects", []):
                if ob.get("type") in NODES and ob.get("item") == item:
                    weights[rid] = weights.get(rid, 0) + 1

    def node_kind(self, item):
        for r in self.rooms.values():
            for ob in r.get("objects", []):
                if ob.get("type") in NODES and ob.get("item") == item:
                    return ob["type"]
        return None

    def person_room(self, npc):
        if npc in self.homes:
            return self.homes[npc]
        for rid in sorted(self.rooms):
            if any(ob.get("type") == "npc" and ob.get("npc") == npc for ob in self.rooms[rid].get("objects", [])):
                return rid
        return None

    def lead(self, lead, qid=None, giver=None, hand_in=None):
        """The room a step leads to (None: nowhere in particular)."""
        if not lead:
            return None
        kind, what = lead
        w = {}
        if kind == "room":
            return what
        if kind == "spawn":
            self._spawns(what, w)
        elif kind == "source":
            for e in self.droppers(what, qid):
                self._spawns(e, w)
            self._nodes(what, w)
        elif kind == "node":
            self._nodes(what, w)
        elif kind in ("npc", "spar"):
            if what in (giver, hand_in):
                return None
            if kind == "spar":
                for rid in sorted(self.rooms):
                    if any(ob.get("type") == "spar_post" and ob.get("opponent") == what for ob in self.rooms[rid].get("objects", [])):
                        return rid
            return self.person_room(what)
        return self._pick(w)

    def name(self, kind, what):
        table = {"enemy": self.enemies, "item": self.items, "npc": self.npcs, "room": self.rooms}[kind]
        return (table.get(what) or {}).get("name") or titled(what)


# ------------------------------------------------------------------------------------------------ the specs
class State:
    def __init__(self, sections, dailies):
        self.sections = [(name, list(qs)) for name, qs in sections]
        self.dailies = list(dailies)
        self.quests = [q for _, qs in self.sections for q in qs]
        self.by_id = {}
        for q in self.quests:
            if q["id"] in self.by_id:
                raise SpecError("%s is written twice" % q["id"])
            self.by_id[q["id"]] = q
        self.section_of = {q["id"]: name for name, qs in self.sections for q in qs}


_STATE = None
_WORLD = None


def load(sections=None, dailies=None):
    """The specs of specs/__init__.py SECTIONS (each a section story.py places: its modules, or `module:LIST`) and
    DAILIES."""
    from . import specs as S
    out = []
    for name, mods in (sections or S.SECTIONS):
        qs = []
        for m in mods:
            mod, _, lst = m.partition(":")
            qs += getattr(importlib.import_module("content.quests.specs." + mod), lst or "QUESTS")
        out.append((name, qs))
    if dailies is None:
        mod, _, lst = S.DAILIES.partition(":")
        dailies = getattr(importlib.import_module("content.quests.specs." + mod), lst or "DAILIES")
    return State(out, dailies)


def state():
    global _STATE
    if _STATE is None:
        _STATE = load()
    return _STATE


def world():
    global _WORLD
    if _WORLD is None:
        _WORLD = World.from_data()
    return _WORLD


def reset():
    global _STATE, _WORLD
    _STATE = None
    _WORLD = None


# ------------------------------------------------------------------------------------------------ the row
def quest_row(qid, name, kind, giver, objectives, rewards=(), hand_in=None, offer=(), complete=(), progress=(), **kw):
    """A quests.json row, the one layout of every quest (story.py's `quest()` writes its hand quests with it): the head,
    the texts, then `kw` in the order given; a quest that is a deed of the karma ledger (relations.QUEST_DEEDS: its
    merit, alignment and Fame in karma.json) names it last among its rewards."""
    from relations import QUEST_DEEDS
    rewards = list(rewards)
    if qid in QUEST_DEEDS:
        rewards.append({"kind": "deed", "deed": qid})
    d = {"id": qid, "name": name, "kind": kind, "giver": giver, "hand_in": giver if hand_in is None else hand_in,
         "marker": kw.pop("marker", "gold" if kind in ("main", "prologue") else "blue"),
         "objectives": list(objectives), "rewards": rewards}
    if offer:
        d["offer_text"] = list(offer)
    if complete:
        d["complete_text"] = list(complete)
    if progress:
        d["progress_text"] = list(progress)
    d.update(kw)
    return d


class Pay(dict):
    """A quest's pay before its tier is known: `settle` fills it from the band (or the pinned amount)."""

    def __init__(self, qid, amount=None):
        super().__init__(kind="grant_currency", currency=None, amount=amount)
        self.qid = qid
        self.pinned = amount


def text_of(s, w):
    """A step's quest-log line: its own, or one from the names ("Defeat Reedtail Rats", "Bring Crab Shells")."""
    if s.get("text") is not None:
        return s["text"]
    k, n = s["kind"], int(s.get("count", 1))
    if k == "kill":
        return "Defeat %s" % plural(w.name("enemy", s["enemy"]), n)
    if k == "collect":
        return "Bring %s" % plural(w.name("item", s["item"]), n)
    if k == "deliver":
        return "Deliver %s" % plural(w.name("item", s["item"]), n)
    if k == "gather_node":
        nm = w.name("item", s["item"])
        return ("Mine %s" % nm) if w.node_kind(s["item"]) == "ore_vein" else ("Gather %s" % plural(nm, n))
    if k == "talk_to":
        return "%s %s" % (s.verb or "Talk to", w.name("npc", s["npc"]))
    if k == "win_spar":
        return ("Win a spar against %s" % w.name("enemy", s["opponent"])) if s.get("opponent") else "Win a spar"
    if k == "reach_room":
        return "%s %s" % ("Reach" if s.verb in (None, "Reach") else "See them safely to", w.name("room", s["room"]))
    raise SpecError("a %s step needs its text" % k)


def derive(q, w):
    """What the engine derives for quest spec `q`, pins winning: {target_room, derived_room (where its steps lead,
    pinned or not), realm, requires}."""
    from common import realm as realm_c, qdone, qactive
    import realms as R
    giver = q["giver"]
    hand_in = giver if q["hand_in"] is None else q["hand_in"]
    lead = None
    for s in q["steps"]:
        lead = w.lead(s.lead, q["id"], giver, hand_in)
        if lead:
            break
    target = lead if q["target_room"] is AUTO else q["target_room"]
    rk = q["realm"]
    if rk is AUTO or rk is ROOM:
        # The room's realm: AUTO for a quest that follows no other, ROOM also for one that does (E5b: it then opens at
        # the later of the two, for a room that lies past where the story leaves you).
        room_realm = rk is ROOM
        rk = None
        band = w.band(target) if target else None
        if band and (room_realm or not q["after"]):
            rk = R.key_at_level((band[0] + band[1]) // 2)
    if q["requires"] is not AUTO:
        req = q["requires"]
    else:
        conds = [qdone(a) for a in q["after"]] + [qactive(d) for d in q["during"]]
        conds += [realm_c(rk)] if rk else []
        conds += list(q["needs"])
        req = {"all": conds} if conds else None
    return {"target_room": target, "derived_room": lead, "realm": rk, "requires": req}


def compile_quest(q, w):
    """The quest's row as story.py places it (its pay a `Pay` until `settle`)."""
    d = derive(q, w)
    objectives = []
    for s in q["steps"]:
        ob = copy.deepcopy(dict(s))
        ob["text"] = text_of(s, w)
        objectives.append(ob)
    rewards = []
    gives = list(q["gives"])
    if q["pay"] is not None and PAY not in gives:
        gives.insert(0, PAY)
    for g in gives:
        if g is PAY:
            if q["pay"] is None:
                continue
            if isinstance(q["pay"], dict):
                rewards.append(copy.deepcopy(q["pay"]))
            else:
                rewards.append(Pay(q["id"], None if q["pay"] is AUTO else int(q["pay"])))
        else:
            rewards.append(copy.deepcopy(g))
    found = {"requires": d["requires"], "target_room": d["target_room"]}
    found.update({k: v for k, v in q["keys"].items() if k in ORDER})
    kw = {k: copy.deepcopy(found[k]) for k in ORDER if found.get(k) is not None}
    kw.update({k: copy.deepcopy(v) for k, v in q["keys"].items() if k not in ORDER})
    r = quest_row(q["id"], q["name"] or titled(q["id"]), q["kind"], q["giver"], objectives, rewards, q["hand_in"],
                  q["offer"], q["done"], q["progress"], **kw)
    for k, v in q["row"].items():
        if v is DROP:
            r.pop(k, None)
        else:
            r[k] = copy.deepcopy(v)
    return r


def rows(section, st=None, w=None):
    """The rows of one section, in the specs' order (story.py: `Q.extend(rows(section))`)."""
    st, w = st or state(), w or world()
    names = [n for n, _ in st.sections]
    if section not in names:
        raise SpecError("no section %r (specs/__init__.py SECTIONS: %s)" % (section, ", ".join(names)))
    return [compile_quest(q, w) for q in dict(st.sections)[section]]


def band_of_tier(tier):
    import realms as R
    lv = next((int(r["level"]) for r in R.ladder() if r["key"] == tier), 0)
    return B.band_at(lv)


def settle(quests):
    """Once story.py's quest_tiers has found each quest's tier: every engine quest's pay from its band (bands.py), or
    its pinned amount in the band's currency. Returns the rows settled."""
    done = 0
    for q in quests:
        for i, e in enumerate(q.get("rewards", [])):
            if isinstance(e, Pay):
                b = band_of_tier(q["tier"])
                q["rewards"][i] = {"kind": "grant_currency", "currency": b[2], "amount": b[3] if e.pinned is None else e.pinned}
                done += 1
    return done


# ------------------------------------------------------------------------------------------------ the daily board
def job_levels(s, w):
    """A job's Levels when the spec does not pin them: a foe's band (enemies.json `level`) from a Level under its first
    to four over its last; a node's from a Level under the first field band it grows in to twenty over; else any Level
    of the board."""
    if s["kind"] == "kill" and s["enemy"] in w.enemies:
        lv = w.enemies[s["enemy"]].get("level") or [0, 0]
        return max(0, int(lv[0]) - 1), min(BOARD_TOP, int(lv[-1]) + 4)
    if s["kind"] == "gather_node":
        firsts = sorted(b[0] for rid, b in ((rid, w.band(rid)) for rid in w.rooms) if b and any(
            ob.get("type") in NODES and ob.get("item") == s["item"] for ob in w.rooms[rid].get("objects", [])))
        if firsts:
            return max(0, firsts[0] - 1), min(BOARD_TOP, firsts[0] - 1 + 20)
    return 0, BOARD_TOP


def missions(st=None, w=None):
    """The mission board's templates (mission_templates.json), in the specs' order."""
    st, w = st or state(), w or world()
    out = []
    for d in st.dailies:
        r = {"id": d["id"], "name": d["name"]}
        if d["requires"]:
            r["requires"] = copy.deepcopy(d["requires"])
        opts = []
        for j in d["jobs"]:
            s = j["step"]
            ob = dict(s)
            ob["text"] = text_of(s, w)
            lo, hi = job_levels(s, w) if j["levels"] is AUTO else j["levels"]
            opts.append({"name": j["name"], "objective": {k: copy.deepcopy(ob[k]) for k in s.board if k in ob},
                         "min_level": lo, "max_level": hi})
        r["options"] = opts
        out.append(r)
    return out


# ------------------------------------------------------------------------------------------------ checks
def check_specs(errs, st=None, w=None):
    """Every spec resolves: its giver and hand-in are people (the NPC engine's, or story.py's one-off rows), what each
    step names exists, each item it gives exists, a derived room is found where a step leads, each pinned room
    exists."""
    st, w = st or state(), w or world()
    for q in st.quests:
        who = q["id"]
        for p in [q["giver"]] + ([q["hand_in"]] if q["hand_in"] else []) + q["keys"].get("giver_any", []) + q["keys"].get("hand_in_any", []):
            if p not in w.npcs:
                errs.append("%s: no person %s (data/npcs.json)" % (who, p))
        for s in q["steps"]:
            for key, table in (("enemy", w.enemies), ("opponent", w.enemies), ("item", w.items), ("npc", w.npcs), ("room", w.rooms)):
                if key in s and s[key] not in table:
                    errs.append("%s: no %s %s" % (who, key, s[key]))
            if s.lead and s.lead[0] in ("spawn", "source", "node") and q["target_room"] is AUTO and not w.lead(s.lead, who):
                errs.append("%s: nothing leads to %s %s in the built rooms (pin target_room)" % (who, s.lead[0], s.lead[1]))
        for g in q["gives"] + ([q["pay"]] if isinstance(q["pay"], dict) else []):
            if isinstance(g, dict) and g.get("kind") == "grant_item" and g["item"] not in w.items:
                errs.append("%s: gives no item %s" % (who, g["item"]))
        tr = q["target_room"]
        if tr not in (AUTO, None) and tr not in w.rooms:
            errs.append("%s: no room %s" % (who, tr))
        if q["pay"] is not AUTO and not q.get("why"):
            errs.append("%s: its pay is pinned (%r) with no reason: give why=\"...\" (the story's), or let it pay its band" % (who, q["pay"]))
    for d in st.dailies:
        for j in d["jobs"]:
            s = j["step"]
            for key, table in (("enemy", w.enemies), ("item", w.items)):
                if key in s and s[key] not in table:
                    errs.append("daily %s %r: no %s %s" % (d["id"], j["name"], key, s[key]))
            if j["levels"] is not AUTO and not j.get("why"):
                errs.append("daily %s %r: its Levels are pinned %r with no reason: give why=\"...\", or let them follow its band" % (
                    d["id"], j["name"], j["levels"]))
    return errs


def check_rooms(errs, st=None, w=None):
    """E5b: no quest is pitched far from its room (far_rooms), and no daily job is posted far from its foe's or its
    node's band (far_jobs)."""
    for qid, tier, lv, room, band in far_rooms(st, w):
        errs.append("%s: its room %s (Levels %s) is far from its tier %s (Level %d): move its target, or let it open later "
                    "(realm=ROOM)" % (qid, room, band, tier, lv))
    for did, name, lv, what, band in far_jobs(st, w):
        errs.append("daily %s %r: posted at Levels %d-%d, far from %s (Levels %s)" % (did, name, lv[0], lv[1], what, band))
    return errs


def _settled(r, built):
    """An engine row as the built data should hold it: its pay as the built tier's band (or its pin) pays."""
    r = copy.deepcopy(r)
    for i, e in enumerate(r["rewards"]):
        if isinstance(e, Pay):
            b = band_of_tier(built.get("tier", "mortal"))
            r["rewards"][i] = {"kind": "grant_currency", "currency": b[2], "amount": b[3] if e.pinned is None else e.pinned}
    return r


def check_built(errs, st=None, w=None):
    """The built data holds every quest as the engine writes it (its pay settled at its built tier), in the sections'
    order; story.py adds only `qp` (Act II and III), `tier` and `cultivation`; the cultivation is the band table's at
    that tier (phase 1's numbers); the mission board is the engine's."""
    import realms as R
    from stats import QUEST_CULTIVATION
    st, w = st or state(), w or world()
    built_rows = _read("quests.json")["entries"]
    built = {r["id"]: r for r in built_rows}
    mine = [q["id"] for q in st.quests]
    have = [r["id"] for r in built_rows if r["id"] in st.by_id]
    if have != mine:
        errs.append("data/quests.json does not list the engine's quests in the sections' order (run build_data.py)")
    for q in st.quests:
        b = built.get(q["id"])
        if b is None:
            errs.append("%s: not in data/quests.json (run build_data.py)" % q["id"])
            continue
        want = _settled(compile_quest(q, w), b)
        got = {k: v for k, v in b.items() if k in want}
        extra = [k for k in b if k not in want and k not in ("qp", "tier", "cultivation")]
        if got != want or list(got) != list(want) or extra:
            errs.append("%s: data/quests.json does not hold the engine's row (run build_data.py)" % q["id"])
        kind = str(b.get("qp", b["kind"]))
        lv = next((int(r["level"]) for r in R.ladder() if r["key"] == b.get("tier")), 0)
        share = float(QUEST_CULTIVATION.get(kind, 0.0))
        if int(b.get("cultivation", -1)) != (R.cultivation(share, lv) if share > 0 else 0):
            errs.append("%s: its cultivation %s is not phase 1's at its tier %s" % (q["id"], b.get("cultivation"), b.get("tier")))
    if _read("mission_templates.json")["entries"] != missions(st, w):
        errs.append("data/mission_templates.json is not the engine's daily board (run build_data.py)")
    return errs


def check_bands(errs):
    """Each band holds one need (so its cultivation is one number) and starts where the one before it ends."""
    import realms as R
    firsts = [b[1] for b in B.BANDS]
    if firsts != sorted(set(firsts)):
        errs.append("bands.py: the bands' first Levels are not rising")
    for b in B.BANDS:
        needs = {R.need_at_level(lv) for lv in B.levels(b)}
        if len(needs) != 1:
            errs.append("bands.py: band %s spans needs %s" % (b[0], sorted(needs)))
        if b[2] not in (B.TAELS, B.STONES, B.CRYSTALS) or int(b[3]) <= 0:
            errs.append("bands.py: band %s pays %r %r" % (b[0], b[2], b[3]))
    return errs


def deterministic(errs):
    """Two compiles write the same bytes."""
    def dump():
        st, w = state(), world()
        return json.dumps([[compile_quest(q, w) for q in st.quests], missions(st, w)], sort_keys=True)
    a = dump()
    reset()
    if a != dump():
        errs.append("two compiles differ: the engine is not deterministic")
    return errs


# ------------------------------------------------------------------------------------------------ what it paid
def differences(st=None, w=None):
    """[(quest, band, tier, what the band pays, what the quest pays, why)] for every quest whose pay is pinned otherwise,
    or whose cultivation is not its band's (a quest of Act II's sections at an Act I tier pays Act II's share); `why` is
    its spec's reason."""
    st, w = st or state(), w or world()
    built = {r["id"]: r for r in _read("quests.json")["entries"]}
    out = []
    for q in st.quests:
        b = built.get(q["id"])
        if b is None:
            continue
        band = band_of_tier(b["tier"])
        want = B.pay(band)
        got = [e for e in b["rewards"] if e.get("kind") == "grant_currency"]
        exp_band, exp = B.experience(band), int(b.get("cultivation", 0))
        pay_s = lambda e: "%d %s" % (e["amount"], {"silver_tael": "taels", "spirit_stone": "spirit stones", "sage_crystal": "sage crystals"}.get(e["currency"], e["currency"]))
        if [want] != got or exp != exp_band:
            out.append((q["id"], band[0], b["tier"], "%s, +%d" % (pay_s(want), exp_band),
                        "%s, +%d" % (", ".join(pay_s(e) for e in got) or "no money", exp), q.get("why") or ""))
    return out


def far_rooms(st=None, w=None, above=4, below=8, tiers=None):
    """[(quest, tier, Level, room, band)] for every quest whose room (its target, or where its first step leads when it
    names none) lies more than `above` Levels over its tier (the kill gap's full-credit band, stats.json) or `below`
    under it: a quest pitched at a tier its fights do not match. `tiers` (quest -> tier) stands for the built data's."""
    import realms as R
    st, w = st or state(), w or world()
    if tiers is not None:
        built = {k: {"tier": t} for k, t in tiers.items()}
    else:
        built = {r["id"]: r for r in _read("quests.json")["entries"]}
    out = []
    for q in st.quests:
        b = built.get(q["id"])
        if b is None:
            continue
        d = derive(q, w)
        room = d["target_room"] or d["derived_room"]
        band = w.band(room) if room else None
        lv = next((int(r["level"]) for r in R.ladder() if r["key"] == b["tier"]), 0)
        if band and (band[0] > lv + above or band[1] < lv - below):
            out.append((q["id"], b["tier"], lv, room, "%d-%d" % band))
    return out


def far_jobs(st=None, w=None, above=4, below=8, node_below=20):
    """[(template, job, (lo, hi), what, band)] for every daily job posted far from what it asks (E5b): a hunt whose foe's
    first Level is more than `above` over the job's lowest Level, or whose last is more than `below` under its highest
    (the quests' bounds); a gathering whose first field band starts more than `above` over its lowest Level, or whose
    last field band tops out more than `node_below` under its highest (job_levels' own reach of twenty)."""
    st, w = st or state(), w or world()
    out = []
    for d in st.dailies:
        for j in d["jobs"]:
            s = j["step"]
            lo, hi = job_levels(s, w) if j["levels"] is AUTO else j["levels"]
            if s["kind"] == "kill" and s["enemy"] in w.enemies:
                lv = w.enemies[s["enemy"]].get("level") or [0, 0]
                first, last, slack = int(lv[0]), int(lv[-1]), below
                what = w.name("enemy", s["enemy"])
            elif s["kind"] == "gather_node":
                bands = [w.band(rid) for rid in w.rooms if w.band(rid) and any(
                    ob.get("type") in NODES and ob.get("item") == s["item"] for ob in w.rooms[rid].get("objects", []))]
                if not bands:
                    continue
                first, last, slack = min(b[0] for b in bands), max(b[1] for b in bands), node_below
                what = w.name("item", s["item"])
            else:
                continue
            if first > lo + above or last < hi - slack:
                out.append((d["id"], j["name"], (lo, hi), what, "%d-%d" % (first, last)))
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="engine.py", description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="the gate: the specs, determinism, the built data, the bands, tests.py")
    ap.add_argument("--list", action="store_true", help="every quest: its section, band, room, realm and pay")
    ap.add_argument("--show", metavar="ID", help="one quest: the row, what was derived and what is pinned")
    ap.add_argument("--bands", action="store_true", help="the band table")
    ap.add_argument("--diffs", action="store_true", help="the quests that pay otherwise than their band, and those pitched far from their room")
    args = ap.parse_args(argv)
    st, w = state(), world()
    if args.list:
        built = {r["id"]: r for r in _read("quests.json")["entries"]}
        for q in st.quests:
            d = derive(q, w)
            b = built.get(q["id"], {})
            print("%-28s %-13s %-18s %-22s %-20s %s" % (q["id"], st.section_of[q["id"]], b.get("tier", "-"), d["target_room"] or "-",
                                                     d["realm"] or "-", [e.get("amount") for e in b.get("rewards", []) if e.get("kind") == "grant_currency"]))
        return 0
    if args.show:
        return show(args.show, st, w)
    if args.bands:
        import realms as R
        print("%-18s %-9s %-8s %-12s %s" % ("band", "Levels", "need", "cultivation", "pay"))
        for b in B.BANDS:
            lv = B.levels(b)
            print("%-18s %-9s %-8d +%-11d %d %s" % (b[0], "%d-%d" % (lv[0], lv[-1]), R.need_at_level(b[1]), B.experience(b), b[3], b[2]))
        return 0
    if args.diffs:
        print("pay: the quests that pay otherwise than the band at their tier, and why")
        for row in differences(st, w):
            print("  %-28s %-16s %-18s band: %-28s quest: %s\n  %28s why: %s" % (row[:5] + ("", row[5] or "(no reason given)")))
        print("rooms: the quests whose room's Levels are far from their tier")
        for row in far_rooms(st, w):
            print("  %-28s %-18s Level %-4d %-24s Levels %s" % row)
        print("board: the daily jobs posted far from their foe's or node's Levels")
        for did, name, lv, what, band in far_jobs(st, w):
            print("  %-8s %-26s Levels %d-%d  %s, Levels %s" % (did, name, lv[0], lv[1], what, band))
        print("board pins: the jobs whose Levels are pinned, and why")
        for d in st.dailies:
            for j in d["jobs"]:
                if j["levels"] is not AUTO:
                    print("  %-8s %-26s Levels %d-%d (derived %d-%d)  why: %s" % ((d["id"], j["name"]) + tuple(j["levels"]) +
                                                                            job_levels(j["step"], w) + (j.get("why") or "(no reason given)",)))
        return 0
    errs = []
    deterministic(errs)
    check_specs(errs)
    check_built(errs)
    check_bands(errs)
    check_rooms(errs)
    from . import tests
    ran, failed = tests.run()
    errs += failed
    if errs:
        print("quest engine:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    st = state()
    band = sum(1 for q in st.quests if q["pay"] is AUTO)
    none = sum(1 for q in st.quests if q["pay"] is None)
    print("quest engine: %d quests in %d sections (%d pay their band, %d a pinned sum, %d no money, each pin with its reason), "
          "%d daily templates with %d jobs; %d tests; the specs, determinism, the built data, the bands, the rooms and the "
          "board hold" % (len(st.quests), len(st.sections), band, len(st.quests) - band - none, none, len(st.dailies),
                          sum(len(d["jobs"]) for d in st.dailies), ran))
    return 0


def show(qid, st, w):
    q = st.by_id.get(qid)
    if q is None:
        print("no spec %s" % qid, file=sys.stderr)
        return 1
    d = derive(q, w)
    r = compile_quest(q, w)
    built = {x["id"]: x for x in _read("quests.json")["entries"]}.get(qid)
    if built:
        r = _settled(r, built)
    print(json.dumps(r, indent=1, ensure_ascii=False))
    print("section %s; target room %s%s; realm %s%s" % (st.section_of[qid], d["target_room"], " (pinned; derived %s)" % d["derived_room"]
                                                       if q["target_room"] is not AUTO else " (derived)", d["realm"],
                                                       " (derived)" if q["realm"] is AUTO else " (its room's)" if q["realm"] is ROOM else " (pinned)"))
    if built:
        band = band_of_tier(built["tier"])
        print("tier %s, band %s: +%d cultivation, %d %s; this quest pays %s" % (built["tier"], band[0], B.experience(band), band[3], band[2],
                                                                                "the band's" if q["pay"] is AUTO else "pinned: %r (%s)" % (q["pay"], q.get("why"))))
    return 0
