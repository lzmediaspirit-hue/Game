"""The item engine's spec language (docs/architecture/item_engine.md). A spec module under specs/ imports from here and
lists its families in `FAMILIES`; nothing here reads data/ or writes a file.

    family(fid, kind=..., tiers=(...) | members=[...], name=..., desc=..., <kind fields>,
           recipe=dict(...), icon=dict(...), sources=dict(...), row=dict(...), section=..., sinks=(...))

- `fid` is "<kind>.<stem>". A one-member family's id is its stem unless `id=` says otherwise; a ladder's `id`, `name`
  and `desc` are templates over the member's context ({tier}, {Tier}, {word}, {Word}, {pct}, {minutes}, {cult}...).
- `tiers=` makes one member a grade (a ladder); `members=[member(...)]` lists them (each its own id, grade and fields).
- Any value may be `curve(name[, key])` (the member's grade on a curve of curves.py) or `per({tier: value})`.
- `row=` pins values in the finished row (hand tweaks live here, never in the JSON); `DROP` removes a key.
"""
import copy

DROP = object()   # a `row` pin that removes the key


class Curve:
    def __init__(self, name, key=None):
        self.name, self.key = name, key

    def __repr__(self):
        return "curve(%r%s)" % (self.name, "" if self.key is None else ", %r" % (self.key,))


class Per:
    """A value that differs by member: keyed by tier (grade, or a herb's age) or by the member's id."""
    def __init__(self, table):
        self.table = dict(table)

    def __repr__(self):
        return "per(%r)" % (self.table,)


def curve(name, key=None):
    return Curve(name, key)


def per(table=None, **kw):
    return Per(dict(table or {}, **kw))


def effect(kind, **f):
    d = {"kind": kind}
    d.update(f)
    return d


def qi(share):
    """Decision 45's fixed cultivation: an add_progress worth `share` of the stage at the middle of the member's grade."""
    return effect("add_progress", amount=curve("cultivation", share))


def member(tier=None, grade=None, **fields):
    """One member of a family listed by hand: its tier (a grade, or a herb's age), grade and its own fields."""
    d = {"tier": tier if tier is not None else grade, "grade": grade if grade is not None else tier}
    d.update(fields)
    return d


SOURCE_KEYS = {"shop", "recipe", "drop", "chest", "gather", "garden", "craft", "reward", "mail", "mark"}
FAMILY_KEYS = {"kind", "tiers", "members", "id", "name", "desc", "section", "words", "sources", "recipe", "icon", "row",
               "sinks", "stack", "seed", "grade", "ilv"}


class Family:
    """A family as its spec wrote it; engine.compile() turns it into members and rows."""

    def __init__(self, fid, kind, tiers=None, members=None, sources=None, **fields):
        if "." not in fid:
            raise ValueError("family %s: a family id is <kind>.<stem>" % fid)
        self.fid, self.kind = fid, kind
        self.stem = fid.split(".", 1)[1]
        if (tiers is None) == (members is None):
            raise ValueError("family %s: give tiers= or members=, not both or neither" % fid)
        if tiers is not None:
            words = fields.get("words") or {}
            self.members = [{"tier": t, "grade": t, "word": words.get(t)} for t in tiers]
        else:
            self.members = [dict(m) for m in members]
        self.sources = dict(sources or {})
        unknown = set(self.sources) - SOURCE_KEYS
        if unknown:
            raise ValueError("family %s: unknown source %s (sources: %s)" % (fid, ", ".join(sorted(unknown)), ", ".join(sorted(SOURCE_KEYS))))
        self.fields = fields

    def __repr__(self):
        return "family(%r)" % self.fid


def family(fid, kind, **kw):
    """A family × tier spec (audit 45 §6.4). See the module's docstring and item_engine.md."""
    return Family(fid, kind, **kw)


def gear(fid, kind="weapon", **kw):
    """A gear family over the grades (gear.py ARCHETYPES names its archetype): family(fid, kind=weapon|armour|gourd)."""
    return Family(fid if "." in fid else "%s.%s" % (kind, fid), kind, **kw)


def resolve(value, ctx):
    """`value` with every curve() and per() replaced by the member's own (deep: lists, tuples and dicts)."""
    from . import curves
    if isinstance(value, Curve):
        return curves.value(value.name, ctx["grade"], value.key)
    if isinstance(value, Per):
        for k in (ctx["id"], ctx["tier"], ctx["grade"]):
            if k in value.table:
                return resolve(value.table[k], ctx)
        raise KeyError("per(): no value for %s (tier %s)" % (ctx["id"], ctx["tier"]))
    if isinstance(value, dict):
        return {k: resolve(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, ctx) for v in value]
    if isinstance(value, tuple):
        return tuple(resolve(v, ctx) for v in value)
    return copy.deepcopy(value) if isinstance(value, (set,)) else value
