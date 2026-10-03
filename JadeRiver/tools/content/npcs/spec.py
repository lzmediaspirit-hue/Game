"""E3, the NPC engine: the spec a person is written in (docs/architecture/npc_engine.md).

A spec is a Python literal, kept in tools/content/npcs/specs/<zone>.py in the module's `NPCS` list (and `EXTRAS`). It
names who the person is and where they live and work; the engine (engine.py) writes every row the game reads about them.

  npc(id, name, title, look, lines, barks=(), services=(), at=(), concealed=(), row=None, **keys)
    look       look(...) below: the character pipeline's parts and dyes
    lines      what they say when spoken to; `barks` what they call out as you pass; `concealed` their lines to a
               cultivator who hides their realm (S48)
    services   ["shop:<shop>", "page:<page>", "spar:<id>", "missions"]; with the keys `service_labels` and
               `service_unlocks` ({service: label}, {service: unlock id})
    keys       tree (their dialogue tree's id, data/dialogue/<tree>.json), scale, tint, on_talk, companion, sect;
               the row takes them in the order KEYS lists, whatever order the spec gives them in
    at         [place(...)]: where they stand in rooms, their home first
    row        pins on the finished npcs.json row: {key: value} (a key the row has keeps its place, a new one goes
               at the end; DROP takes one out)

  look(hair, shirt, pants, shoes, hat="none", cape="none", weapon="none", body="light")
    parts of data/parts.json; "style:colour" for the hair (a colour's index in the character's `hair_colors`, 0 when
    left out), "garment:dye" for the shirt and the trousers (a dye of the character's `dyes`; none when left out)

  place(room, oid=None, work=None, anchor=None, side=None, **obj)
    room       the room's id; `oid` the person's object there ("npc_<id>" by default). A room's own placement (its
               object in world.py, its anchor in the room's spec) is named by its room and object
    work       work(...) below: what they do there all day (life.json `work`)
    anchor     a placement the engine makes itself (a person new to the room): a room engine anchor ("road.n@30",
               "near:well", "auto" or a cell) for the top-down room; `side` the point in the side-view room ([x, y];
               by default from the anchor's column, on the ground line), and `obj` the side-view object's other
               fields (facing, visible_if, hidden_if)

  work(loop, *spots, auto=None)
    loop       one of topdown_life.LOOPS (ROLE: the role's own, for a sect's staff)
    spots      each a cell [x, y, facing(, steps)], pinned, or an anchor the engine resolves on the room's layout
               (spots.py), so that a building moved moves its workers:
                 "home"            the person's own spot
                 "water_edge"      the bank beside open water, facing it
                 "by:<prop kind>"  beside a prop of that kind (the wash tub, the anvil's forge, a stall), facing it
                 "near:<oid>"      beside another thing of the room (the shrine, the notice board), facing it
                 "open"            a free spot round the person, facing out
               then, each optional and in this order, "@x" or "@x,y" (the point to look round: the person's own
               spot by default; an extra's first spot needs one), ">dir" (the facing kept) and ":steps" (the loop's
               steps there): "by:wash_tub>e:wash". "auto:water_edge" reads as "water_edge".
    auto       n spots round the person by a hash of the room and the person (topdown_life.auto_spots)

  role(title, look, lines, barks, services=(), loop=None, **keys) and staff(role, sect, name, at=(), **over)
    a role template for a sect's staff (specs/sects.py ROLES) and one person from it: the id "<sect>_<role>", the
    role's title, look, lines, barks, services and keys with "{Sect}", "{sect}", "{dye}" and "{weapon}" filled from
    the sect (SECTS), the sect's id as `sect`; `over` wins over the role

  extra(id, room, look, work)
    a figure at work with no part in the story (life.json `extras`): no row, no talk; its first spot is its home
"""
import copy

# The keys of an npcs.json row past its fixed head, in the order the row has them (story.py's hand rows had them so).
KEYS = ("scale", "tint", "tree", "on_talk", "service_labels", "service_unlocks", "companion", "sect")
HEAD = ("id", "name", "title", "outfit", "lines", "barks", "services")
LOOK_KEYS = ("hair", "shirt", "pants", "shoes", "hat", "cape", "weapon", "body")
PLACE_KEYS = ("room", "oid", "work", "anchor", "side", "obj")


class Drop:
    """A pin that takes a key out of the row."""

    def __repr__(self):
        return "DROP"


DROP = Drop()
ROLE = None       # work(ROLE, ...): a sect's staff at the role's own loop


class SpecError(ValueError):
    pass


def _split(value, what):
    name, _, tail = str(value).partition(":")
    if not name:
        raise SpecError("look: no %s in %r" % (what, value))
    return name, tail


def look(hair="short_knot", shirt="disciple", pants="loose", shoes="slippers", hat="none", cape="none", weapon="none",
         body="light"):
    """An outfit as npcs.json and life.json hold it (story.py's outfit() made the same dict)."""
    style, colour = _split(hair, "hair")
    shirt, shirt_dye = _split(shirt, "shirt")
    pants, pants_dye = _split(pants, "trousers")
    o = {"body": body, "hair": style, "hair_color": int(colour or 0), "shirt": shirt, "pants": pants, "shoes": shoes,
         "hat": hat, "cape": cape, "weapon": weapon}
    if shirt_dye:
        o["shirt_dye"] = shirt_dye
    if pants_dye:
        o["pants_dye"] = pants_dye
    return o


def work(loop, *spots, auto=None):
    """A work loop and its spots (or `auto` spots round the person)."""
    if auto is not None and spots:
        raise SpecError("work %s: spots or auto, not both" % loop)
    if auto is not None:
        return {"loop": loop, "auto": int(auto)}
    if not spots:
        raise SpecError("work %s: no spot (give spots, or auto=n)" % loop)
    return {"loop": loop, "spots": [list(s) if isinstance(s, (list, tuple)) else str(s) for s in spots]}


def place(room, oid=None, work=None, anchor=None, side=None, **obj):
    """Where a person stands in a room, and what they do there."""
    if anchor is None and (side is not None or obj):
        raise SpecError("place %s: side and object fields belong to a placement the engine makes (give its anchor)" % room)
    return {"room": room, "oid": oid, "work": work, "anchor": anchor, "side": list(side) if side else None, "obj": obj}


def npc(id, name, title, look, lines, barks=(), services=(), at=(), concealed=(), row=None, **keys):
    """A person of the story."""
    bad = [k for k in keys if k not in KEYS]
    if bad:
        raise SpecError("npc %s: unknown keys %s (KEYS: %s; pin anything else with row=)" % (id, ", ".join(bad), ", ".join(KEYS)))
    places = []
    for p in at:
        p = place(p) if isinstance(p, str) else dict(p)
        p["oid"] = p["oid"] or "npc_" + id
        places.append(p)
    return {"kind": "npc", "id": id, "name": name, "title": title, "look": dict(look), "lines": list(lines),
            "barks": list(barks), "services": list(services), "keys": dict(keys), "at": places,
            "concealed": list(concealed), "row": dict(row or {})}


def extra(id, room, look, work):
    """A figure at work with no part in the story."""
    if not work or not work.get("spots"):
        raise SpecError("extra %s: its work names its spots (the first is its home)" % id)
    return {"kind": "extra", "id": id, "room": room, "look": dict(look), "work": dict(work)}


# ------------------------------------------------------------------------------------------------ role templates
def role(title, look, lines, barks, services=(), loop=None, **keys):
    """A role template: what every person of the role shares (`look` holds look()'s keywords)."""
    bad = [k for k in look if k not in LOOK_KEYS]
    if bad:
        raise SpecError("role %s: look keys %s" % (title, ", ".join(bad)))
    return {"title": title, "look": dict(look), "lines": list(lines), "barks": list(barks), "services": list(services),
            "loop": loop, "keys": dict(keys)}


def _fill(v, ctx):
    if isinstance(v, str):
        return v.format(**ctx)
    if isinstance(v, list):
        return [_fill(x, ctx) for x in v]
    if isinstance(v, tuple):
        return tuple(_fill(x, ctx) for x in v)
    if isinstance(v, dict):
        return {_fill(k, ctx): _fill(x, ctx) for k, x in v.items()}
    return v


def staff(role_id, roles, sect, name, at=(), **over):
    """One of a sect's staff from the role `roles[role_id]` and the sect (a SECTS row: key, Sect, sect, dye, weapon)."""
    t = roles[role_id]
    ctx = dict(sect)
    filled = _fill(copy.deepcopy(t), ctx)
    places = []
    for p in at:
        p = dict(p)
        if p.get("work") and p["work"].get("loop") is None:
            if not filled["loop"]:
                raise SpecError("staff %s_%s: no loop given and the role has none" % (sect["key"], role_id))
            p["work"] = dict(p["work"], loop=filled["loop"])
        places.append(p)
    keys = dict(filled["keys"])
    for k in KEYS:
        if k in over:
            keys[k] = over.pop(k)
    keys["sect"] = sect["sect"]
    fields = dict(look=look(**filled["look"]), lines=filled["lines"], barks=filled["barks"], services=filled["services"],
                  at=places)
    fields.update(over)
    return npc("%s_%s" % (sect["key"], role_id), name, fields.pop("title", filled["title"]), **fields, **keys)
