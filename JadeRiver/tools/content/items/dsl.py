"""The item engine's spec language (docs/architecture/item_engine.md). A spec module under specs/ imports from here and
lists its families in `FAMILIES`; nothing here reads data/ or writes a file.

    family(fid, kind=..., tiers=(...) | members=[member(...)], id=, name=, desc=, <the kind's fields>,
           recipe=dict(...), icon=dict(...), sources=dict(...), row=dict(...), section=..., sinks=(...))

- `fid` is "<kind>.<stem>". A one-member family's id is its stem unless `id=` says otherwise; a ladder's `id`, `name`
  and `desc` are templates over the member's context ({tier}, {Tier}, {Grade}, {word}, {Word}, {pct}, {minutes},
  {cult}, and the member's own fields).
- `tiers=` makes one member of each grade (a ladder; `words={grade: word}` names them); `members=[member(...)]` lists
  them by hand, each with its own id, grade and fields (a field of the member's wins over the family's).
- Any value may be `curve(name[, key])` (the member's grade on a curve of curves.py) or `per({tier: value}, default=)`.
- `qi(share)` is decision 45's fixed cultivation for the member's grade; `effect(kind, ...)` any other use effect.
- `row=` pins values in the finished row (hand tweaks live here, never in the JSON); a pin of `DROP` removes a key.
- `gear(family, kind=weapon|armour|gourd|pet_gear|furnace, ...)` is family() for gear, the fid made from the kind.
"""

DROP = object()   # a `row` pin (or a pill's `cause` / `soul`) that removes the key
_MISSING = object()


class Curve:
    def __init__(self, name, key=None):
        self.name, self.key = name, key

    def __repr__(self):
        return "curve(%r%s)" % (self.name, "" if self.key is None else ", %r" % (self.key,))


class Per:
    """A value that differs by member: keyed by the member's id, tier (a grade, or a herb's age) or grade, else
    `default`."""
    def __init__(self, table, default=_MISSING):
        self.table = dict(table)
        self.default = default

    def __repr__(self):
        return "per(%r)" % (self.table,)


def curve(name, key=None):
    return Curve(name, key)


def per(table=None, default=_MISSING, **kw):
    return Per(dict(table or {}, **kw), default)


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


# Where a member comes from (engine.CHANNEL): `shop` and `recipe` the engine writes, the rest it finds in the data.
SOURCE_KEYS = {"shop", "auction", "recipe", "drop", "chest", "gather", "garden", "craft", "reward", "mail", "mark"}


class Family:
    """A family as its spec wrote it; engine.compile_families() turns it into members and rows."""

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
    """A gear family over the grades: family("<kind>.<fid>", kind, ...)."""
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
        if value.default is not _MISSING:
            return resolve(value.default, ctx)
        raise KeyError("per(): no value for %s (tier %s)" % (ctx["id"], ctx["tier"]))
    if isinstance(value, dict):
        return {k: resolve(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, ctx) for v in value]
    if isinstance(value, tuple):
        return tuple(resolve(v, ctx) for v in value)
    return value
