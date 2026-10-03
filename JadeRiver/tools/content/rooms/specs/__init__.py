"""E1 room specs, grouped by zone (docs/architecture/room_engine.md): each zone's module lists its rooms in `ROOMS`.
`ALL` is every spec in the order topdown_rooms.py builds them. A new zone's module is added to ZONES."""
import importlib

ZONES = ["lotus_ferry", "willow_path", "stoneford", "jade_sect", "cloud_sect", "reed_marsh", "caravan_road", "mudwater_hideout", "deepwater_bend",
         "drowned_shrine", "whitewater_gorge"]   # R2


def all_specs():
    out = []
    for z in ZONES:
        out += importlib.import_module("content.rooms.specs." + z).ROOMS
    ids = [s["id"] for s in out]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError("room specs: %s written twice" % ", ".join(dup))
    return out
