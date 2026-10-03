"""E1 room specs, grouped by zone (docs/architecture/room_engine.md): each zone's module lists its rooms in `ROOMS`.
`ALL` is every spec in the order topdown_rooms.py builds them. A new zone's module is added to ZONES."""
import importlib

ZONES = ["lotus_ferry", "willow_path", "stoneford", "jade_sect", "cloud_sect", "reed_marsh", "caravan_road", "mudwater_hideout", "deepwater_bend"]
ZONES += ["stonewall_quarry"]   # R3
# R1: the main story's path past chapter 3 (reed_marsh's rooms past the Marsh Edge are in its module).
ZONES += ["greyreed_hamlet", "bamboo_grove", "crane_falls", "cleansing_peak"]
# R2: the Drowned Shrine and Whitewater Gorge (the Serpent's Shallows is in deepwater_bend's module).
ZONES += ["drowned_shrine", "whitewater_gorge"]
# R4: the peaks.
ZONES += ["crane_cliffs", "mist_peak", "summit_ridge", "hidden_vale", "unmapped"]
# R5: the story's own rooms and the Tidebreak Front.
ZONES += ["story", "tidebreak_front"]
# R7: Act II's chapters 13 and 14, Nine Peaks to the Tomb of Sunscar.
ZONES += ["nine_peaks", "gale_canyons", "ironroot_hold", "sunscar_desert", "tomb_of_sunscar"]
# R9: the star field's end, in the story's order: the Starsea's crossings, the Star Warden Citadel, the Orbit Ruins, the
# Ashen Reach, the Nebula Deep and the Lantern Heart.
ZONES += ["starsea", "lantern_crossing", "warden_citadel", "orbit_ruins", "ashen_reach", "nebula_deep", "lantern_heart"]


def all_specs():
    out = []
    for z in ZONES:
        out += importlib.import_module("content.rooms.specs." + z).ROOMS
    ids = [s["id"] for s in out]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError("room specs: %s written twice" % ", ".join(dup))
    return out
