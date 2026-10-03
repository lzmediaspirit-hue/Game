"""The item engine (decision 45, audit 45 §6.4; docs/architecture/item_engine.md): families of items as specs, compiled
into what the game reads.

    python3 tools/content/items/engine.py --check     # the engine's gate (tools/run_tests.sh, Test.ps1)
    python3 tools/content/items/engine.py --list      # every family, its members and where each one comes from

A family (specs/*.py, `FAMILIES`) writes, for each of its members:
- its row in items.json or artifacts.json (items.py places each section: `items(section)`);
- its recipe (economy.py places each block: `recipes(block)`), with the recipe's element and fragments;
- its shop lines and the lines that sell its recipe (economy.py: `shelves(rows)`; a line the shop list does not place
  with an `F(item)` or `L(recipe)` marker goes at the end of that shop's stock or rotation);
- its icon: a pill's vessel and grade kit (tools/icons/families/pills.py reads `pill_icons()`), any other kind's id;
- each value a tier carries, from curves.py unless the spec pins it.
A family must name its sources: the engine refuses a member nothing hands out, and `--check` finds each source it
names but does not write (drops, chests, gathering, the garden, rewards...) in the built data, as wiki.py does.
"""
import copy
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(TOOLS, "data"), TOOLS):
    if _p not in sys.path:
        sys.path.append(_p)

if __name__ == "__main__" and not __package__:
    # Run as a script: the package's own module runs the command line, so the specs and the CLI share one compile.
    from content.items import engine as _engine
    raise SystemExit(_engine.main())

from common import all_of, flag as flag_req, realm as realm_req, titled  # noqa: E402

from . import curves, kinds  # noqa: E402
from .dsl import DROP, Family, resolve  # noqa: E402

# The spec modules, in the order their families are compiled (and their lines appended to a shop).
SPECS = ["pills", "herbs", "ores", "parts", "gear", "streams"]
# A declared source's channel in wiki.py's terms (tools/dev/wiki.py CHANNELS).
CHANNEL = {"shop": "Shop", "auction": "Shop", "recipe": "Crafting", "craft": "Crafting", "drop": "Drop", "chest": "Container", "gather": "Gathering",
           "garden": "Garden", "reward": "Reward", "mail": "Mail"}
MARKS = ("story", "system", "later")
# Keys of a family's fields that are the engine's, not a kind's.
META = {"id", "name", "desc", "section", "words", "recipe", "icon", "row", "sinks", "seed", "tier", "grade", "sources"}
RECIPE_META = {"id", "craft", "inputs", "outputs", "grade", "element", "fragments", "block", "learn", "after"}


class SpecError(Exception):
    pass


# ------------------------------------------------------------------------------------------------------- the compile
class Member(dict):
    """A compiled member: its row, recipe, lines and icon (a dict, so it prints as data)."""


class State:
    def __init__(self):
        self.families = []          # Family, in SPECS order
        self.members = []           # Member, in family order
        self.by_id = {}
        self.order = {}             # section or recipe block -> pinned order (ids)
        self.modules = {}
        self.errors = []
        self.used = {}              # table -> sections placed since begin()


_STATE = None


def state():
    global _STATE
    if _STATE is None:
        _STATE = _compile()
        if _STATE.errors:
            raise SystemExit("item engine:\n  " + "\n  ".join(_STATE.errors))
    return _STATE


def spec(name):
    """A spec module (its constants: specs/gear.py GRADE_WORD...)."""
    return state().modules[name]


def reset():
    """Forget the compile (the tests compile twice to prove the build deterministic)."""
    global _STATE
    _STATE = None
    for name in SPECS:
        sys.modules.pop("content.items.specs." + name, None)


def _compile():
    st = State()
    for name in SPECS:
        mod = importlib.import_module("content.items.specs." + name)
        st.modules[name] = mod
        for fam in getattr(mod, "FAMILIES", []):
            if not isinstance(fam, Family):
                st.errors.append("specs/%s.py: FAMILIES holds %r, not a family()" % (name, fam))
                continue
            fam.spec = name
            st.families.append(fam)
        for k, ids in getattr(mod, "ORDER", {}).items():
            if k in st.order:
                st.errors.append("specs/%s.py: ORDER pins %s twice" % (name, k))
            st.order[k] = ids if isinstance(ids, str) else list(ids)
    fids = set()
    for fam in st.families:
        if fam.fid in fids:
            st.errors.append("family %s is declared twice" % fam.fid)
        fids.add(fam.fid)
        try:
            ms = [_member(fam, raw, i) for i, raw in enumerate(fam.members)]
            if fam.fields.get("seed"):
                ms.append(_seed(fam, ms[0], len(ms)))
            for m in ms:
                if m["id"] in st.by_id:
                    st.errors.append("%s: id %s is already %s's" % (fam.fid, m["id"], st.by_id[m["id"]]["fid"]))
                    continue
                st.by_id[m["id"]] = m
                st.members.append(m)
        except (KeyError, ValueError, TypeError, SpecError) as e:
            st.errors.append("%s: %s" % (fam.fid, e))
    st.errors += _static_checks(st)
    return st


def _ctx(fam, raw):
    """The member's fields: the family's, then its own; then the context a template formats with."""
    m = {k: v for k, v in fam.fields.items() if k not in ("words",)}
    m.update(raw)
    tier, grade = m.get("tier"), m.get("grade")
    word = m.get("word")
    ctx = dict(m, tier=tier, grade=grade, Tier=str(tier).capitalize(), Grade=curves.GRADE_NAME.get(grade, str(grade)), stem=fam.stem,
               Stem=titled(fam.stem), word=word or "", Word=(word or "").capitalize())
    if grade in curves.SPEED:
        b, s = curves.speed(grade)
        ctx.update(pct=int(round(b * 100)), minutes=s // 60)
    return m, ctx


def _fmt(value, ctx):
    return value.format(**ctx) if isinstance(value, str) else value


def _member(fam, raw, index):
    m, ctx = _ctx(fam, raw)
    kind = fam.kind
    if kind not in kinds.KINDS:
        raise SpecError("no kind %s (kinds: %s)" % (kind, ", ".join(kinds.KINDS)))
    # The id: the member's own, the family's template, the herb rule, or (one member) the family's stem.
    if raw.get("id"):
        mid = raw["id"]
    elif kind == "herb":
        mid = kinds.herb_id(fam.stem, m["tier"], m.get("young_age"))
    elif fam.fields.get("id"):
        mid = _fmt(fam.fields["id"], ctx)
    elif len(fam.members) == 1:
        mid = fam.stem
    else:
        raise SpecError("a ladder needs an id template (id=\"{word}_...\")")
    ctx["id"] = mid
    m = resolve(m, ctx)
    m["id"], m["_stem"], m["fid"], m["kind"], m["index"] = mid, fam.stem, fam.fid, kind, index
    if kind == "herb" and not raw.get("name") and not fam.fields.get("name"):
        m["name"] = kinds.herb_name(fam.stem, m["tier"], m.get("young_age"))
    # Decision 45: a text that says the cultivation an item pays reads it from the item's own effects.
    gains = [e.get("amount", 0) for e in m.get("use", []) if isinstance(e, dict) and e.get("kind") == "add_progress"]
    ctx["cult"] = kinds.cult_text(int(sum(gains))) if gains else ""
    for key in ("name", "desc"):
        if isinstance(m.get(key), str):
            m[key] = _fmt(m[key], dict(ctx, **{k: v for k, v in m.items() if isinstance(v, (str, int, float)) and k not in ctx}))
    icon = m.get("icon")
    m["_icon"] = icon if isinstance(icon, str) else (icon or {}).get("id")
    sources = dict(fam.sources)
    sources.update(raw.get("sources") or {})
    sources = {k: resolve(v, dict(ctx, id=mid)) for k, v in sources.items() if v is not False and v is not None}
    for k, v in list(sources.items()):
        # An outside source given as a list names the tiers (or ids) it hands out; a part's `drop` list names creatures.
        if k not in ("shop", "drop", "mark") and isinstance(v, (list, tuple)):
            if m.get("tier") in v or m.get("grade") in v or mid in v:
                sources[k] = True
            else:
                del sources[k]
    m["_sources"] = sources
    if sources.get("mark"):
        if sources["mark"] not in MARKS:
            raise SpecError("%s: mark %s is not one of %s" % (mid, sources["mark"], ", ".join(MARKS)))
        m["_mark"] = sources["mark"]
    member = Member(fid=fam.fid, kind=kind, id=mid, tier=m.get("tier"), grade=m.get("grade"), spec=fam.spec,
                    section=m.get("section") or kinds.SECTION[kind], table=kinds.TABLE[kind], index=index)
    row = kinds.KINDS[kind](m)
    for pins in (fam.fields.get("row"), raw.get("row")):
        for k, v in (pins or {}).items():
            if v is DROP:
                row.pop(k, None)
            else:
                row[k] = resolve(v, dict(ctx, id=mid))
    member["row"] = row
    member["recipe"] = _recipe(fam, m, ctx)
    member["lines"] = _lines(m, sources.get("shop") or {}, mid)
    if member["recipe"]:
        r = member["recipe"]
        member["lines"] += _lines(m, r["learn"], "recipe_scroll", learn=r["row"]["id"])
    member["icon"] = _icon(m, icon) if kind == "pill" else None
    member["sources"] = sources
    member["herb"] = (fam.stem, m["tier"]) if kind == "herb" else None
    member["sinks"] = fam.fields.get("sinks")
    if member["sinks"] is not None and "sell" not in member["sinks"]:
        row["sell"] = False
    return member


def _seed(fam, first, index):
    """A herb family's seed (S45): a member of its own (section "seeds"), from the family's seed=dict(grade, desc,
    sources=...)."""
    spec_s = fam.fields["seed"]
    sid = spec_s.get("id") or fam.stem + "_seed"
    m = {"id": sid, "tier": spec_s["grade"], "grade": spec_s["grade"], "_stem": fam.stem}
    sources = {k: v for k, v in (spec_s.get("sources") or {}).items() if v is not False and v is not None}
    member = Member(fid=fam.fid, kind="seed", id=sid, tier=spec_s["grade"], grade=spec_s["grade"], spec=fam.spec, section="seeds",
                    table="items", index=index)
    member["row"] = kinds.seed(m, spec_s)
    member["recipe"] = None
    member["lines"] = _lines(m, sources.get("shop") or {}, sid)
    member["icon"] = None
    member["sources"] = sources
    member["herb"] = None
    member["sinks"] = None
    member["seed_of"] = (fam.stem, spec_s["desc"])
    return member


def _recipe(fam, m, ctx):
    spec_r = m.get("recipe")
    if callable(spec_r):
        spec_r = spec_r(m)
    if not spec_r:
        return None
    spec_r = resolve(spec_r, ctx)
    mid = m["id"]
    rid = _fmt(spec_r.get("id") or mid, dict(ctx, id=mid))
    craft = spec_r.get("craft", "alchemy")
    outputs = spec_r.get("outputs") or [(mid, 1)]
    row = {"id": rid, "craft": craft, "grade": spec_r.get("grade", m["grade"]),
           "inputs": [{"item": i, "count": n} for i, n in spec_r["inputs"]],
           "outputs": [{"item": i, "count": n} for i, n in outputs]}
    for k, v in spec_r.items():
        if k not in RECIPE_META:
            row[k] = v
    block = spec_r.get("block") or {"alchemy": "alchemy"}.get(craft, craft)
    return {"row": row, "block": block, "element": spec_r.get("element"), "fragments": spec_r.get("fragments"),
            "learn": spec_r.get("learn") or {}, "after": spec_r.get("after")}


def _applies(value, m):
    """A source's value for this member, or None when it does not apply: a list of tiers (or ids) the source covers, a
    dict keyed by tier (or id) of each one's details, or one details dict for every member."""
    if isinstance(value, (list, tuple)):
        return {} if (m["tier"] in value or m["id"] in value or m["grade"] in value) else None
    if isinstance(value, dict) and any(k not in LINE_KEYS for k in value):
        for k in (m["id"], m["tier"], m["grade"]):
            if k in value:
                return value[k]
        return None
    return dict(value or {})


LINE_KEYS = {"price", "requires", "realm", "flag", "rotation", "currency", "daily", "sealed", "learn"}


def _lines(m, shops, item_id, learn=None):
    """The member's shop lines: [(shop, part, line)] from shop={shop: details}."""
    out = []
    for shop, value in shops.items():
        d = _applies(value, m)
        if d is None:
            continue
        unknown = set(d) - LINE_KEYS
        if unknown:
            raise SpecError("%s: shop %s: unknown line key %s" % (m["id"], shop, ", ".join(sorted(unknown))))
        line = {"item": item_id}
        if learn:
            line["learn"] = learn
        part = "stock"
        for k, v in d.items():
            if k == "rotation":
                part = "rotation" if v else "stock"
            elif k == "realm":
                line["requires"] = all_of(realm_req(v))
            elif k == "flag":
                line["requires"] = all_of(flag_req(v))
            else:
                line[k] = v
        out.append((shop, part, line))
    return out


def _icon(m, icon):
    """A pill's icon: (id, vessel kind, grade, mark, pill material, ink[, extra]), tools/icons/families/pills.py PILLS_HD."""
    if not icon or isinstance(icon, str):
        return None
    vessel = icon.get("vessel") or {"healing": "healing", "restoration": "restoration", "buff": "buff"}.get(m["group"], "utility")
    row = (m["_icon"] or m["id"], vessel, icon.get("grade", m["grade"]), icon.get("mark", m["mark"]), icon["pill"], tuple(icon["ink"]))
    return row + ((icon["extra"],) if icon.get("extra") else ())


# ------------------------------------------------------------------------------------------------------ the channels
def _ordered(st, key, members):
    """`members` in the order ORDER pins for `key` (then the unpinned ones in spec order)."""
    pin = st.order.get(key)
    if not pin:
        return members
    by = {m["id"]: m for m in members}
    return [by[i] for i in pin if i in by] + [m for m in members if m["id"] not in pin]


def begin(table):
    """A host starts placing a table's sections (items.py: items, artifacts; economy.py: recipes)."""
    state().used[table] = []


def end(table):
    """Every section of `table` with members was placed (else its rows would be lost)."""
    st = state()
    used = st.used.pop(table, [])
    if table == "recipes":
        blocks = {m["recipe"]["block"] for m in st.members if m["recipe"]}
        missing = sorted(blocks - set(used))
    else:
        missing = sorted({m["section"] for m in st.members if m["table"] == table} - set(used))
    if missing:
        raise SystemExit("item engine: %s: no host places %s (items.py / economy.py)" % (table, ", ".join(missing)))


def _use(table, key):
    used = state().used.setdefault(table, [])
    if key in used:
        raise SystemExit("item engine: %s %s is placed twice" % (table, key))
    used.append(key)


def items(section):
    """The rows of a section, in its order (a herb family's seeds are the section "seeds")."""
    st = state()
    members = [m for m in st.members if m["section"] == section]
    if not members:
        raise SystemExit("item engine: no family writes the section %s" % section)
    _use(members[0]["table"], section)
    if st.order.get(section) == "grade":
        members = sorted(members, key=lambda m: (curves.grade_index(m["grade"]), _fam_index(st, m["fid"])))
    else:
        members = _ordered(st, section, members)
    return [copy.deepcopy(m["row"]) for m in members]


def _fam_index(st, fid):
    return next(i for i, f in enumerate(st.families) if f.fid == fid)


def recipes(block):
    """The recipe rows of a block (economy.py places each), in spec order, a recipe's `after` pin moving it."""
    st = state()
    _use("recipes", block)
    ms = [m for m in st.members if m["recipe"] and m["recipe"]["block"] == block]
    if st.order.get(block) == "grade":
        ms = sorted(ms, key=lambda m: (curves.grade_index(m["recipe"]["row"]["grade"]), _fam_index(st, m["fid"])))
    rows = [m["recipe"] for m in ms]
    for r in [r for r in rows if r["after"]]:
        rows.remove(r)
        at = next((i for i, x in enumerate(rows) if x["row"]["id"] == r["after"]), None)
        if at is None:
            raise SystemExit("item engine: recipe %s: after %s, which block %s does not hold" % (r["row"]["id"], r["after"], block))
        rows.insert(at + 1, r)
    return [copy.deepcopy(r["row"]) for r in rows]


def recipe_meta(rid):
    """(element, fragments) of a family recipe, or None for a recipe no family writes."""
    for m in state().members:
        if m["recipe"] and m["recipe"]["row"]["id"] == rid:
            return m["recipe"]["element"], m["recipe"]["fragments"]
    return None


def F(item_id):
    """A shop list's marker: the line a family declares for `item_id` at this shop goes here."""
    return {"__line__": item_id}


def L(recipe_id):
    """A shop list's marker: the line that sells the recipe `recipe_id` (a recipe scroll) goes here."""
    return {"__learn__": recipe_id}


def shelves(shops):
    """The shop rows with every family line in place: each marker replaced by its line, then the lines no marker
    placed at the end of their shop's stock or rotation, in spec order."""
    st = state()
    declared = []      # (shop, part, key, line)
    for m in st.members:
        for shop, part, line in m["lines"]:
            key = ("learn", line["learn"]) if line["item"] == "recipe_scroll" else ("item", line["item"])
            declared.append((shop, part, key, line))
    out = copy.deepcopy(shops)
    ids = {s["id"] for s in out}
    errs = ["shop %s (a family line for %s) does not exist" % (sh, k[1]) for sh, _, k, _ in declared if sh not in ids]
    placed = set()
    for s in out:
        for part in ("stock", "rotation"):
            lst = s.get("stock", []) if part == "stock" else s.get("rotation", {}).get("pool", [])
            for i, line in enumerate(lst):
                if "__line__" in line or "__learn__" in line:
                    key = ("item", line["__line__"]) if "__line__" in line else ("learn", line["__learn__"])
                    hit = [d for d in declared if d[0] == s["id"] and d[1] == part and d[2] == key]
                    if not hit:
                        errs.append("shop %s %s: a marker for %s, which no family declares there" % (s["id"], part, key[1]))
                        continue
                    if (s["id"], part, key) in placed:
                        errs.append("shop %s %s: %s is placed twice" % (s["id"], part, key[1]))
                    placed.add((s["id"], part, key))
                    lst[i] = copy.deepcopy(hit[0][3])
        for shop, part, key, line in declared:
            if shop != s["id"] or (shop, part, key) in placed:
                continue
            placed.add((shop, part, key))
            if part == "stock":
                s.setdefault("stock", []).append(copy.deepcopy(line))
            else:
                if "rotation" not in s:
                    errs.append("shop %s has no rotation for %s" % (shop, key[1]))
                    continue
                s["rotation"]["pool"].append(copy.deepcopy(line))
    if errs:
        raise SystemExit("item engine: shops:\n  " + "\n  ".join(errs))
    return out


def pill_icons():
    """Every pill family member's icon row (tools/icons/families/pills.py PILLS_HD)."""
    return [m["icon"] for m in state().members if m["icon"]]


def herb_ages():
    """{herb id: (family, age)} family by family, ages rising (garden.json `families`; herbs.py)."""
    st = state()
    out = {}
    for fam in st.families:
        if fam.kind == "herb":
            for m in sorted([m for m in st.members if m["fid"] == fam.fid and m["kind"] == "herb"], key=lambda m: m["tier"]):
                out[m["id"]] = m["herb"]
    return out


def seeds():
    """[(seed id, herb family, grade, desc)] in the seeds' order (garden.json `seeds`; herbs.py)."""
    st = state()
    return [(m["id"], m["seed_of"][0], m["grade"], m["seed_of"][1]) for m in _ordered(st, "seeds", [m for m in st.members if m["kind"] == "seed"])]


def members(kind=None):
    return [m for m in state().members if kind is None or m["kind"] == kind]


# ---------------------------------------------------------------------------------------------------------- checks
def _static_checks(st):
    """What a spec must hold before it builds: a source for every member, pins that name real members."""
    errs = []
    for m in st.members:
        src = m.get("sources") or {}
        has = bool(m.get("lines")) or bool(m.get("recipe")) or "mark" in src or any(k in CHANNEL and k not in ("shop", "recipe") for k in src)
        if not has:
            errs.append("%s (%s): nothing hands it out; name a source (shop, recipe, drop, chest, gather, garden, craft, "
                        "reward, mail) or a mark" % (m["id"], m["fid"]))
    known = set(st.by_id)
    seeds_ = set()
    rids = {m["recipe"]["row"]["id"] for m in st.members if m.get("recipe")}
    for key, pin in st.order.items():
        if pin == "grade":
            continue
        for i in pin:
            if i not in known and i not in seeds_ and i not in rids:
                errs.append("ORDER %s pins %s, which no family writes" % (key, i))
        if len(set(pin)) != len(pin):
            errs.append("ORDER %s names an id twice" % key)
    return errs


def _drops():
    """{creature: the items its loot table and first defeat hand out} from the built data (enemies.json, loot_tables.json)."""
    data = os.path.join(TOOLS, "..", "data")
    tables = {t["id"]: t for t in json.load(open(os.path.join(data, "loot_tables.json"), encoding="utf-8"))["entries"]}
    out = {}
    for e in json.load(open(os.path.join(data, "enemies.json"), encoding="utf-8"))["entries"]:
        t = tables.get(e.get("loot", e["id"]), {})
        got = {x["item"] for k in ("guaranteed", "rare", "quest_drops", "named", "elite_named", "lost") for x in t.get(k, [])}
        got |= {x["item"] for g in t.get("groups", []) for x in g.get("pick", [])}
        out[e["id"]] = got | set(e.get("first_defeat", [])) | set(e.get("elite_first_defeat", []))
    return out


def check_sources(errs):
    """Each source a family names but does not write is found in the built data (wiki.py's channels); a part's named
    creatures each drop it (their rows are the monster engine's, tools/data/enemies.py)."""
    sys.path.append(os.path.join(TOOLS, "dev"))
    import wiki
    found = wiki.Sources(wiki.Data()).run().by_item
    drops = _drops()
    for m in state().members:
        creatures = (m.get("sources") or {}).get("drop")
        for c in creatures if isinstance(creatures, list) else []:
            if c not in drops:
                errs.append("%s names the creature %s, which enemies.json does not hold" % (m["id"], c))
            elif m["id"] not in drops[c]:
                errs.append("%s names %s, which does not drop it (its loot table is the monster engine's, enemies.py)" % (m["id"], c))
        ids = [m["id"]]
        have = {c for _, c, _ in found.get(m["id"], set())}
        named = {k for k in (m.get("sources") or {}) if k not in ("mark", "shop", "recipe")}
        if any(line[2]["item"] != "recipe_scroll" for line in m["lines"]):
            named.add("shop")
        if m["recipe"]:
            named.add("recipe")
        for key in sorted(named):
            ch = CHANNEL[key]
            if ch not in have:
                errs.append("%s names %s (%s), but the built data hands it out by %s" % (m["id"], key, ch, ", ".join(sorted(have)) or "nothing"))
        for i in ids:
            mark = m["row"].get("source")
            if not found.get(i) and not (mark in MARKS or (isinstance(mark, list) and mark and mark[0] in MARKS)):
                errs.append("%s: no source in the built data (wiki.py --gaps)" % i)
    return errs


def check_built(errs):
    """The built tables hold every member as the engine writes it (build_data.py --check proves the files current)."""
    data = os.path.join(TOOLS, "..", "data")
    tables = {t: {r["id"]: r for r in json.load(open(os.path.join(data, t + ".json"), encoding="utf-8"))["entries"]}
              for t in ("items", "artifacts", "recipes")}
    manifest = json.load(open(os.path.join(data, "icon_manifest.json"), encoding="utf-8"))
    for m in state().members:
        if tables[m["table"]].get(m["id"]) != m["row"]:
            errs.append("%s: data/%s.json does not hold the engine's row (run build_data.py)" % (m["id"], m["table"]))
        if m["recipe"] and tables["recipes"].get(m["recipe"]["row"]["id"], {}).get("outputs") != m["recipe"]["row"]["outputs"]:
            errs.append("%s: data/recipes.json does not hold its recipe" % m["id"])
        icon = m["row"].get("icon", m["id"])
        if icon not in manifest:
            errs.append("%s: its icon %s is not built (tools/icons/build_icons.py)" % (m["id"], icon))
    return errs


def deterministic(errs):
    """Two compiles write the same bytes."""
    def dump():
        st = state()
        return json.dumps([[m["row"], m["recipe"] and m["recipe"]["row"], m["lines"], m["icon"]] for m in st.members], sort_keys=False)
    a = dump()
    reset()
    b = dump()
    if a != b:
        errs.append("two compiles differ: the engine is not deterministic")
    return errs


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="engine.py", description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="the gate: specs, determinism, the built data, sources, icons")
    ap.add_argument("--list", action="store_true", help="every family and its members")
    args = ap.parse_args(argv)
    st = state()
    if args.list:
        for fam in st.families:
            ms = [m for m in st.members if m["fid"] == fam.fid]
            print("%-28s %-6s %s" % (fam.fid, fam.kind, ", ".join("%s (%s)" % (m["id"], m["grade"]) for m in ms)))
        return 0
    errs = []
    deterministic(errs)
    check_built(errs)
    check_sources(errs)
    from . import tests
    errs += tests.run()
    if errs:
        print("item engine:\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    fams = len(st.families)
    print("item engine: %d families, %d members (%d recipes, %d shop lines, %d pill icons); specs, determinism, the built "
          "data, sources and icons hold" % (fams, len(st.members), sum(1 for m in st.members if m["recipe"]),
                                              sum(len(m["lines"]) for m in st.members), len(pill_icons())))
    return 0
