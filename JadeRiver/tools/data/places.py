"""Decision 43, systems as places (docs/redesign/systems_as_places.md, "As built"): the places in the world where the
game's systems live, one row per place, into data/places.json. The world draws each place and its state
(TopdownPlaceArt), the context button's verb opens the place's page (WorldAuthority.interact), the Menu shows where a
system that lives at a place is (PlaceRules.where) with a travel button, and the world map and the minimap mark them.

A place is an object of a room on the height grid (data/topdown/<room>.json places it): one the side-view room already
has (the notice board, the storage chest, the furnace, a bed, the teleport stone, a shrine, a keeper), or one this table
adds to the room (`add`: the letter box, the meditation mat), with a sight round it where it needs one (`art`: the
Storehouse's shed, a stall's counter and awning; its `solid` cells block like a prop's footprint). Every place is
checked here as it is built: its cell stands on a floor, a body reaches it on foot from every way into the room, auto-
path walks to its `stand` cell, and what it blocks leaves every thing and way of the room reached (topdown_rooms.py's
rules). A system first used in the prologue or the tutorial has its home place on their path (`tutorial`).

The rule of each place (`rule`):
  both    the place opens the page and the Menu (or the HUD) keeps it too: the place adds a reason to walk there, a
          sight and its state (the letter box's ribbon, the mat's Qi mist).
  earned  the first uses happen at the place; `remote.after` (requirements, as an unlock's trigger) and, with
          `remote.first_use`, a first use at a place of the system open it from anywhere (PlaceRules.remote_open).
          Until then the Menu's entry says where it lives ("At the Storehouse") and offers to walk there.
  place   being there is the point: shops and their keepers, the notice boards, teleport stones, shrines.

The table is stable for its readers (the unlock tutorials' "go to the place" step reads `system`, `home`, `room`,
`object`, `stand`, `name` and `where`; the walk there is `{"type": "auto_path", "target": room, "place": id}`).

Run from JadeRiver/: `python3 tools/data/build_data.py places` (or `python3 tools/data/places.py [--check]`).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import topdown_rooms as TR   # noqa: E402  the grid's walking rules, shared with the layouts' own check
from common import DATA, all_of, entries, flag, realm, unlocked   # noqa: E402

TILE = 32.0
SCHEMA = 1
# The rooms of the prologue and the tutorial (Lotus Ferry to the recruitment fair): a system first used there has its home
# place in one of them, so no place ever stands between a new player and a lesson.
TUTORIAL_ROOMS = {"lf_fishers_hut", "lf_village", "lf_old_ma_store", "lf_granny_liu_hut", "lf_lu_boat", "lf_reed_shallows",
                  "wp_east", "wp_west", "sf_gate", "sf_market", "sf_artisan_row", "sf_fairground"}
# What each kind of place is called on the map and in the Menu, its icon on the world map (data/icon_manifest.json) and
# the verb the context button shows (a string key; a keeper's is Talk).
KINDS = {
    "notice_board": ("Notice Board", "quest", "sim.world.read"),
    "stall": ("Shop", "shop", "sim.world.talk"),
    "storehouse": ("Storehouse", "storage", "sim.world.open"),
    "garden_bed": ("Garden", "craft_foraging", "sim.world.tend"),
    "furnace": ("Furnace", "alchemy", "sim.world.refine"),
    "anvil": ("Forge", "forge_marker", "sim.world.forge"),
    "cooking_pot": ("Cooking Pot", "cook", "sim.world.cook"),
    "teleport_stone": ("Teleport Stone", "teleport_marker", "sim.world.travel"),
    "meditation_mat": ("Meditation Mat", "meditating", "sim.world.sit"),
    "letter_box": ("Letter Box", "mail", "sim.world.read"),
    "shrine": ("Shrine", "shrine_marker", "sim.world.pray"),
}
# The Menu's order for the places card and the map's Places view.
KIND_ORDER = ["notice_board", "stall", "storehouse", "letter_box", "garden_bed", "furnace", "anvil", "cooking_pot",
              "meditation_mat", "teleport_stone", "shrine"]

# Earned remote access (systems_as_places.md §0 item 3, §5): the place first, then from anywhere.
REMOTE = {
    # Storage: a spatial pouch from Tailor Xun (the Pouches, plan §3) reaches the storehouse from anywhere.
    "storage": {"after": all_of(unlocked("pouch_sewing")), "first_use": True,
                "text": "Opens from anywhere once Tailor Xun has sewn you a pouch (A Pouch for the Road)."},
    # The Garden's tending: from anywhere after the first harvest at a bed (plan §3).
    "herb_garden": {"after": all_of(flag("place_used:herb_garden")), "first_use": True,
                    "text": "Tend your beds from anywhere after your first harvest."},
    # The Crafts queue (auto-refine): queued at a furnace until Qi Unfurling; then from anywhere.
    "alchemy": {"after": all_of(realm("qi_unfurling_1")), "first_use": True, "scope": "queue",
                "text": "Queue batches from anywhere from Qi Unfurling 1; refine by hand at a furnace."},
}

# The unlock a place's system waits for before its object answers (an added object's `requires`).
NEEDS = {"mail": "mail", "cultivation": "cultivation"}


def P(pid, system, page, room, obj, kind, rule, name, state, **kw):
    """One place. `obj` is the object's id in the room; `add` gives the object's definition when the table adds it."""
    row = {"id": pid, "system": system, "page": page, "page_args": kw.pop("page_args", {}), "room": room, "object": obj,
           "kind": kind, "rule": rule, "name": name, "state": state}
    row.update(kw)
    return row


def places():
    return [
        # ---- Lotus Ferry, the first home: its services round the square (rule 4: within one screen of each other).
        P("lf_notice_board", "notice_board", "notice_board", "lf_village", "board_village", "notice_board", "place",
          "the Village Notice Board", "papers", home=True, tutorial=True),
        P("lf_storehouse", "storage", "storage", "lf_village", "storage_village", "storehouse", "earned",
          "the Storehouse", "stock", home=True, menu="storage",
          art={"kind": "shed", "cells": [42, 14, 3, 2]}, solid=[[42, 14, 3, 2]]),
        P("lf_letter_box", "mail", "mail", "lf_village", "letter_box_village", "letter_box", "both",
          "the Letter Box", "ribbon", home=True, tutorial=True, menu="mail",
          add={"type": "letter_box", "cell": [31, 16], "label": "Letter Box"}),
        P("lf_meditation_mat", "cultivation", "cultivation", "lf_village", "mat_village", "meditation_mat", "both",
          "the Meditation Mat", "mist", home=True, tutorial=True, menu="cultivation",
          add={"type": "meditation_mat", "cell": [25, 28], "label": "Meditation Mat", "spring": "spring_village"}),
        P("lf_cooking_pot", "cooking", "cooking", "lf_village", "cook_village", "cooking_pot", "both",
          "the Village Cooking Pot", "steam", home=True),
        P("lf_shrine", "shrines", "", "lf_village", "shrine_village", "shrine", "place", "the Village Shrine", "lit",
          home=True, tutorial=True),
        P("lf_granny_shrine", "shrines", "", "lf_granny_liu_hut", "shrine_granny", "shrine", "place",
          "Granny Liu's Altar", "lit", tutorial=True),
        P("lf_old_ma_counter", "shop", "shop", "lf_old_ma_store", "npc_old_ma", "stall", "place", "Old Ma's Store",
          "wares", home=True, tutorial=True, keeper="old_ma", stand=[12, 6]),
        P("wp_shrine", "shrines", "", "wp_west", "shrine_wp", "shrine", "place", "the Wayside Shrine", "lit"),
        # ---- Stoneford: the Market's services round its teleport stone, the Artisan Row's stations.
        P("sf_shrine", "shrines", "", "sf_gate", "shrine_sf_gate", "shrine", "place", "the Gate Shrine", "lit"),
        P("sf_notice_board", "notice_board", "notice_board", "sf_market", "board_sf", "notice_board", "place",
          "the Market Notice Board", "papers", tutorial=True),
        P("sf_general_stall", "shop", "shop", "sf_market", "npc_storekeeper_fang", "stall", "place",
          "Proprietor Fang's Stall", "wares", keeper="storekeeper_fang",
          art={"kind": "stall", "cells": [12, 14, 3, 1]}, solid=[[12, 14, 3, 1]], stand=[13, 15]),
        P("sf_storehouse", "storage", "storage", "sf_market", "storage_sf", "storehouse", "earned",
          "the Market Storehouse", "stock"),
        P("sf_courier_post", "mail", "mail", "sf_market", "courier_post_sf", "letter_box", "both",
          "the Courier Post", "ribbon",
          add={"type": "letter_box", "cell": [33, 19], "label": "Courier Post", "post": "courier"}),
        P("sf_teleport_stone", "teleport_stones", "teleport", "sf_market", "stone_sf", "teleport_stone", "place",
          "the Market Teleport Stone", "attuned", home=True),
        P("sf_furnace", "alchemy", "alchemy", "sf_artisan_row", "furnace_sf", "furnace", "earned",
          "the Artisan Row Furnace", "smoke", home=True),
        P("sf_anvil", "smithing", "forge", "sf_artisan_row", "anvil_sf", "anvil", "both", "Smith Bao's Anvil", "sparks", stand=[17, 14],
          home=True),
        # ---- The Jade Sect.
        P("ja_notice_board", "notice_board", "notice_board", "ja_gate_street", "board_ja", "notice_board", "place",
          "the Jade Sect Notice Board", "papers", sect="jade_sect"),
        P("ja_teleport_stone", "teleport_stones", "teleport", "ja_gate_street", "stone_ja", "teleport_stone", "place",
          "the Jade Gate Teleport Stone", "attuned", sect="jade_sect"),
        P("ja_shrine", "shrines", "", "ja_gate_street", "shrine_ja", "shrine", "place", "the Jade Gate Shrine", "lit",
          sect="jade_sect"),
        P("ja_garden", "herb_garden", "garden", "ja_herb_terraces", "bed_0", "garden_bed", "earned",
          "the Herb Terraces", "growth", home=True, menu="garden", sect="jade_sect", beds=["bed_0", "bed_1", "bed_2"],
          where="At the Terraces"),
        # ---- The Cloud Sect.
        P("cm_notice_board", "notice_board", "notice_board", "cm_cliff_stair", "board_cm", "notice_board", "place",
          "the Cloud Sect Notice Board", "papers", sect="cloud_sect"),
        P("cm_teleport_stone", "teleport_stones", "teleport", "cm_cliff_stair", "stone_cm", "teleport_stone", "place",
          "the Cliff Stair Teleport Stone", "attuned", sect="cloud_sect"),
        P("cm_shrine", "shrines", "", "cm_cliff_stair", "shrine_cm", "shrine", "place", "the Cliff Stair Shrine", "lit",
          sect="cloud_sect"),
        P("cm_garden", "herb_garden", "garden", "cm_array_court", "bed_cm_0", "garden_bed", "earned",
          "the Array Court Beds", "growth", home=True, menu="garden", sect="cloud_sect",
          beds=["bed_cm_0", "bed_cm_1", "bed_cm_2"], where="At the Array Court"),
        P("cm_furnace", "alchemy", "alchemy", "cm_array_court", "furnace_cm", "furnace", "earned",
          "the Array Court Furnace", "smoke", sect="cloud_sect"),
    ]


# -------------------------------------------------------------------- building and checking
def _layout(room):
    return json.load(open(os.path.join(TR.OUT, room + ".json")))


def _side(room):
    return json.load(open(os.path.join(DATA, "rooms", room + ".json")))


def _grid(d, solids):
    g = TR.Grid(d)
    for x, y, w, h in solids:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                g.solid[yy][xx] = True
    return g


def _starts(d):
    out = [TR.cell(d["spawn"])]
    for p in d["portals"].values():
        a = p.get("arrive")
        if a is None:
            v = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}[p["dir"]]
            a = [p["at"][0] - v[0] * 1.5, p["at"][1] - v[1] * 1.5]
        out.append(TR.cell(a))
    return out


def _stand(g, c, walked, rivals, on=False):
    """The cell a body stands on to use the thing at `c`: the nearest round it (south first; `on`: the thing itself, a
    mat sat on) within the context button's reach (three cells), on a floor auto-path reaches from every way in, and
    clear of the reach of every person and pickup of the room (`rivals`), which would take the button from a thing
    (WorldAuthority.context_rank)."""
    cands = sorted((dx * dx + dy * dy + (0.25 if dy < 0 else (0.1 if dy == 0 else 0.0)) + abs(dx) * 0.01, dx, dy) for dy in range(-3, 4) for dx in range(-3, 4)
                   if dx * dx + dy * dy <= 9 and (on or dx or dy))
    fallback = None
    for _, dx, dy in cands:
        q = (c[0] + dx, c[1] + dy)
        if g.floor(*q) is None or not all(q in r for r in walked):
            continue
        if fallback is None:
            fallback = q
        if all((q[0] - rx) ** 2 + (q[1] - ry) ** 2 > 3.6 ** 2 for rx, ry in rivals):
            return [q[0], q[1]]
    return [fallback[0], fallback[1]] if fallback else None


def check_room(room, rows):
    """Every place of the room stands where a body reaches it, and what the places block leaves the room whole."""
    d = _layout(room)
    solids = [s for r in rows for s in r.get("solid", [])]
    g = _grid(d, solids)
    errs = []
    taken = {}
    for s in solids:
        for yy in range(s[1], s[1] + s[3]):
            for xx in range(s[0], s[0] + s[2]):
                if TR.Grid(d).level(xx, yy) in (TR.SOLID, TR.WATER):
                    errs.append("%s: its solid cell %s is already a prop, a wall or water" % (room, str((xx, yy))))
                taken[(xx, yy)] = True
    for oid, at in d["place"].items():
        if TR.cell(at) in taken:
            errs.append("%s: a place's solid cell covers %s" % (room, oid))
    starts = [s for s in _starts(d) if g.floor(*s) is not None]
    reached = [g.reach(s) for s in starts]
    walked = [g.reach(s, False) for s in starts]
    # Every thing and way of the room is still reached with the places' cells blocked (topdown_rooms.check's rule).
    for oid, at in d["place"].items():
        c = TR.cell(at)
        alt = g.floor(*c) if g.floor(*c) is not None else 0.0
        near = [(x, y) for y in range(c[1] - 3, c[1] + 4) for x in range(c[0] - 3, c[0] + 4)
                if g.floor(x, y) is not None and (x - c[0]) ** 2 + (y - c[1]) ** 2 <= 9 and abs(g.floor(x, y) - alt) <= 48]
        for i, r in enumerate(reached):
            if near and not any(q in r for q in near):
                errs.append("%s: %s is cut off by a place's cells (from start %s)" % (room, oid, str(starts[i])))
    for pid, p in d["portals"].items():
        c = TR.cell(p["at"])
        for i, r in enumerate(walked):
            if c not in r:
                errs.append("%s: way %s is cut off by a place's cells for auto-path (from %s)" % (room, pid, str(starts[i])))
    return g, walked, errs


def build_rows():
    rows = places()
    ids = {}
    errs = []
    by_room = {}
    for r in rows:
        assert r["id"] not in ids, ("duplicate place", r["id"])
        ids[r["id"]] = True
        assert r["kind"] in KINDS, (r["id"], r["kind"])
        assert r["rule"] in ("both", "earned", "place"), (r["id"], r["rule"])
        by_room.setdefault(r["room"], []).append(r)
    unlocks = {u["id"] for u in json.load(open(os.path.join(DATA, "unlocks.json")))["entries"]}
    out = []
    for room, rs in by_room.items():
        d = _layout(room)
        side = {o["id"]: o for o in _side(room).get("objects", [])}
        g, walked, e = check_room(room, rs)
        errs += e
        for r in rs:
            kind = KINDS[r["kind"]]
            if "add" in r:
                a = dict(r.pop("add"))
                cell = a.pop("cell")
                assert r["object"] not in side and r["object"] not in d["place"], ("added object id taken", r["object"])
                obj = {"id": r["object"], "type": a.pop("type"), "label": a.pop("label"), "place": r["id"]}
                obj.update(a)
                if r["system"] in NEEDS:
                    obj["requires"] = all_of(unlocked(NEEDS[r["system"]]))
                r["added"] = True
                r["object_def"] = obj
            else:
                if r["object"] not in d["place"]:
                    errs.append("%s: %s is not placed in %s's layout" % (r["id"], r["object"], room))
                    continue
                cell = d["place"][r["object"]]
                r["added"] = False
            r["cell"] = cell
            c = TR.cell(cell)
            if g.floor(*c) is None and not r.get("art"):
                errs.append("%s: its cell %s has no floor" % (r["id"], str(c)))
            rivals = [TR.cell(at) for oid, at in d["place"].items() if oid != r["object"]
                      and side.get(oid, {}).get("type") in ("npc", "pickup")]
            stand = r.get("stand") or _stand(g, c, walked, rivals, r["kind"] == "meditation_mat")
            if stand is None or g.floor(*stand) is None or not all(tuple(stand) in w for w in walked):
                errs.append("%s: no cell by it that auto-path reaches from every way in (%s)" % (r["id"], str(stand)))
                stand = stand or [c[0], c[1]]
            r["stand"] = [stand[0], stand[1]]
            r["at"] = [(float(cell[0]) + 0.5) * TILE, (float(cell[1]) + 0.5) * TILE]
            r["verb"] = kind[2]
            r["icon"] = kind[1]
            r["kind_name"] = kind[0]
            r.setdefault("where", "At " + r["name"])
            r.setdefault("home", False)
            r.setdefault("tutorial", False)
            r.setdefault("menu", "")
            r.setdefault("sect", "")
            r["remote"] = dict(REMOTE[r["system"]]) if r["rule"] == "earned" else {}
            if r["system"] not in unlocks:
                errs.append("%s: its system %s is no unlock" % (r["id"], r["system"]))
            if r["tutorial"] and room not in TUTORIAL_ROOMS:
                errs.append("%s: a tutorial system's place off the tutorial's path (%s)" % (r["id"], room))
            out.append(r)
    # One home place per system (per sect where the sects differ); a system first used in the tutorial has its home on
    # the tutorial's path.
    systems = {}
    for r in out:
        systems.setdefault(r["system"], []).append(r)
    for s, rs in systems.items():
        homes = [r for r in rs if r["home"]]
        if not homes:
            errs.append("system %s has no home place" % s)
        if any(r["tutorial"] for r in rs) and not any(r["tutorial"] and r["home"] for r in rs):
            errs.append("system %s is first used in the tutorial but its home place is not on the tutorial's path" % s)
        if len({r["rule"] for r in rs}) > 1:
            errs.append("system %s has places of different rules" % s)
    out.sort(key=lambda r: [x["id"] for x in places()].index(r["id"]))
    if errs:
        raise SystemExit("places:\n  " + "\n  ".join(errs))
    return out


def payload():
    rows = build_rows()
    return {"kinds": {k: {"name": v[0], "icon": v[1], "verb": v[2]} for k, v in KINDS.items()}, "kind_order": KIND_ORDER,
            "rules": {"both": "the place opens the page; the Menu or the HUD keeps it too",
                      "earned": "the first uses at the place; remote.after (and a first use, remote.first_use) opens it from anywhere",
                      "place": "only at the place"},
            "tutorial_rooms": sorted(TUTORIAL_ROOMS)}, rows


def build():
    extra, rows = payload()
    entries("places", rows, **extra)


if __name__ == "__main__":
    if "--check" in sys.argv:
        extra, rows = payload()
        body = {"schema_version": SCHEMA, "entries": rows}
        body.update(extra)
        want = json.dumps(body, indent=1, ensure_ascii=False) + "\n"
        have = open(os.path.join(DATA, "places.json"), encoding="utf-8").read() if os.path.exists(os.path.join(DATA, "places.json")) else ""
        if want != have:
            raise SystemExit("places: data/places.json is not current (python3 tools/data/build_data.py places)")
        print("places: %d places current and reached" % len(rows))
    else:
        build()
        print("built places")
