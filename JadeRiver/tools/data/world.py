"""Zones and rooms (S17, S18, Part 8 room catalogue) -> data/zones.json, data/rooms/*.json,
data/teleport_stones.json, data/set_pieces.json.

Rooms are authored with a small builder so every room follows the same contract:
bounds [0, 480, W, 480], a ground strip [0, 620, W, 340], building roofs sized from
their prop art, two-way portals, density rules per room type and spawn points kept
away from portals. The Prologue rooms (Lotus Ferry) are laid out by hand; the rest of
the valley uses the same builder with region presets.
"""
import json
import os
import random

from common import DATA, write, entries, req, c

ROOMS_DIR = os.path.join(DATA, "rooms")
GROUND_Y = 620
GROUND_D = 340
SCREEN = 1280
PROPS = json.load(open(os.path.join(DATA, "prop_art.json")))

ROOMS = {}
LINKS = []


def unlock(system):
    return {"kind": "unlock", "system": system}


def realm(r):
    return {"kind": "realm_at_least", "realm": r}


def flag(f):
    return {"kind": "flag_set", "flag": f}


def noflag(f):
    return {"kind": "flag_not_set", "flag": f}


def qdone(q):
    return {"kind": "quest_done", "quest": q}


def qactive(q):
    return {"kind": "quest_active", "quest": q}


def sect(s):
    return {"kind": "training_sect", "sect": s}


def all_of(*conds):
    return {"all": list(conds)}


def any_of(*conds):
    return {"any": list(conds)}


# Gathering presets: node type, item, prop, unlock system.
HERBS = {
    "willow_moss": ("willow_moss_patch", [1, 2]),
    "riverreed_ginseng_10": ("riverreed_ginseng_patch", [1, 1]),
    "ember_pepper": ("ember_pepper_bush", [1, 2]),
    "mist_lotus": ("mist_lotus_patch", [1, 1]),
    "cloudtop_orchid": ("cloudtop_orchid_patch", [1, 1]),
    "soulbell_flower": ("soulbell_flower_patch", [1, 1]),
}
ORES = {
    "copper_ore": ("copper_vein", [1, 3]),
    "riverstone": ("riverstone_vein", [1, 2]),
    "jadeiron": ("jadeiron_vein", [1, 2]),
    "spirit_stone_shard": ("spirit_shard_vein", [1, 1]),
    "cloudsteel_ore": ("cloudsteel_vein", [1, 2]),
    "mystic_ore": ("mystic_vein", [1, 1]),
    "stormsteel_ore": ("stormsteel_vein", [1, 2]),
}
HERBS["frost_lotus"] = ("frost_lotus_patch", [1, 1])
HERBS["ember_cactus"] = ("ember_cactus_patch", [1, 1])
ORES["sunglass_ore"] = ("sunglass_vein", [1, 2])
HERB_RANK = {"willow_moss": "apprentice", "riverreed_ginseng_10": "apprentice", "ember_pepper": "apprentice",
             "mist_lotus": "adept", "cloudtop_orchid": "expert", "soulbell_flower": "expert", "frost_lotus": "master",
             "ember_cactus": "master"}
ORE_RANK = {"copper_ore": "apprentice", "riverstone": "apprentice", "jadeiron": "adept", "spirit_stone_shard": "adept",
            "cloudsteel_ore": "expert", "mystic_ore": "expert", "stormsteel_ore": "master", "sunglass_ore": "master"}


# S17 hazards. Each runs a cycle in seconds (quiet tell, warning, active, cooldown) and is answered by
# one attribute (S10 world effects): the answer a room asks is k x (5 + its top Level), what that
# attribute is at that Level before any training. Kinds: strike (marked spots), gust (a push across
# the room), flow (a push inside the room's water areas), aura (the whole room), pool (inside areas).
# Statuses scale their power, or their duration where "scale" says so.
HAZARDS = [
    {"id": "falling_rocks", "name": "Falling rocks", "kind": "strike", "answer": "body", "k": 1.6, "cycle": [2.0, 1.1, 0.4, 5.0],
     "count": 2, "radius": 64, "aim": "near", "spread": 260, "damage_pct": 0.08,
     "status": {"id": "stun", "s": 0.8, "power": 1.0, "scale": "duration"},
     "note": "Dust trickles from the quarry wall, then a shadow marks where the rock will land. Body braces against the blow."},
    {"id": "lightning", "name": "Lightning", "kind": "strike", "answer": "essence", "k": 1.2, "cycle": [2.5, 1.2, 0.3, 6.0],
     "count": 1, "radius": 56, "aim": "player", "spread": 0, "damage_pct": 0.07, "damage_type": "qi", "element": "wood",
     "status": {"id": "shock", "s": 4.0, "power": 0.2},
     "note": "The storm deck darkens overhead, then a ring of light marks the strike. Essence grounds it."},
    {"id": "wind_gust", "name": "Wind gusts", "kind": "gust", "answer": "body", "k": 1.4, "cycle": [2.5, 1.2, 1.8, 6.0], "push": 230,
     "note": "Leaves and grit lift first, then the gust shoves everything downwind, off ledges too. Body holds its footing."},
    {"id": "current", "name": "Rapids current", "kind": "flow", "answer": "body", "k": 1.3, "cycle": [3.0, 1.0, 2.5, 3.0], "surge": 2.4,
     "areas": ["shallows", "current"],
     "note": "The shallows always pull downstream, and whitecaps warn of a surge. Body wades against it."},
    {"id": "fog", "name": "Fog", "kind": "aura", "answer": "spirit", "k": 1.2, "cycle": [4.0, 2.0, 12.0, 10.0],
     "buff": {"stat": "accuracy", "op": "pct_add", "value": -0.3},
     "note": "Mist pools at the ankles, then rolls over the slope. Blows go astray in it. Spirit sees through."},
    {"id": "cold", "name": "Bitter cold", "kind": "aura", "answer": "body", "k": 1.4, "cycle": [3.0, 1.5, 3.0, 7.0],
     "status": {"id": "slow", "s": 5.0, "power": 0.25}, "shelter": ["shrine", "campfire", "qi_spring"],
     "note": "Snow thickens before each freezing blast, which stiffens the limbs. Body endures it; a shrine gives shelter."},
    {"id": "hollow_puddle", "name": "Hollow puddles", "kind": "pool", "answer": "spirit", "k": 1.3, "cycle": [3.0, 1.2, 2.2, 2.5],
     "areas": ["hollow_puddle"], "pulse": 1.0, "hollowing": 3.0, "status": {"id": "slow", "s": 1.5, "power": 0.3},
     "note": "Grey water that drinks colour. It bubbles before grey threads rise from it. Spirit keeps the Hollow out."},
    {"id": "thorns", "name": "Thorn thickets", "kind": "pool", "answer": "body", "k": 1.4, "cycle": [0.0, 0.0, 1.0, 0.0],
     "areas": ["thorns"], "pulse": 1.0, "damage_pct": 0.02, "status": {"id": "bleed", "s": 3.0, "power": 0.01},
     "note": "Old thorn canes hide in the bamboo. Walking through them tears skin. Body shrugs them off."},
    {"id": "scorching_heat", "name": "Scorching heat", "kind": "aura", "answer": "essence", "k": 1.3, "cycle": [3.0, 2.0, 4.0, 9.0],
     "status": {"id": "exhausted", "s": 8.0, "power": 1.0, "scale": "duration"}, "shelter": ["shrine", "qi_spring"],
     "note": "The air shimmers, then the full weight of the sun lands and blows go soft. Essence keeps the body cool; shrines give shade."},
    {"id": "sandstorm", "name": "Sandstorm", "kind": "gust", "answer": "body", "k": 1.3, "cycle": [3.0, 1.5, 3.0, 8.0], "push": 150,
     "buff": {"stat": "accuracy", "op": "pct_add", "value": -0.25},
     "note": "A brown wall rises on the horizon, then it shoves and blinds. Body stands in it."},
    {"id": "quicksand", "name": "Quicksand", "kind": "pool", "answer": "agility", "k": 1.3, "cycle": [2.0, 1.0, 3.0, 2.0],
     "areas": ["quicksand"], "pulse": 0.8, "status": {"id": "slow", "s": 1.2, "power": 0.5},
     "note": "The sand swirls before it swallows. Agility keeps the feet moving."},
    {"id": "spike_traps", "name": "Spike traps", "kind": "strike", "answer": "agility", "k": 1.3, "cycle": [1.5, 1.0, 0.35, 5.0],
     "count": 2, "radius": 52, "aim": "near", "spread": 220, "damage_pct": 0.07, "status": {"id": "bleed", "s": 3.0, "power": 0.01},
     "note": "Grit shivers over a pressure plate before bronze spikes spring from the floor. Agility gets the feet clear."},
    # Phase E: the Starsea's star wind (Starsea survival, Sage 3) and the Trial Hall's pressing Presences.
    {"id": "star_wind", "name": "Star wind", "kind": "aura", "answer": "spirit", "k": 1.3, "cycle": [3.0, 1.5, 3.0, 7.0],
     "qi_drain_pct": 0.08, "damage_pct": 0.03, "damage_type": "qi", "shelter": ["shrine"],
     "note": "Starlight streams sideways before each gust of the star wind, which strips Qi from anyone it passes. Spirit holds the Qi in."},
    {"id": "presence", "name": "Pressing Presence", "kind": "aura", "answer": "will", "k": 2.2, "cycle": [2.0, 1.5, 3.0, 4.0],
     "damage_pct": 0.06, "damage_type": "soul", "buff": {"stat": "physical_attack", "op": "pct_add", "value": -0.3},
     "note": "The seats of the Nine lean on you: the air thickens, then their Presence lands and the arms grow heavy. Will stands under it."},
    # Breath Control's water (S09): the breath lasts the tell and the warning; then the water takes you, unless an air pocket is near.
    {"id": "deep_water", "name": "Deep water", "kind": "aura", "answer": "body", "k": 2.0, "cycle": [22.0, 6.0, 3.0, 1.0],
     "damage_pct": 0.06, "status": {"id": "slow", "s": 3.0, "power": 0.2}, "shelter": ["air_pocket"],
     "note": "Under the well the grotto is flooded to the roof. Breath lasts about half a minute; the air pockets give it back."},
    {"id": "poison_mist", "name": "Poison mist", "kind": "pool", "answer": "body", "k": 1.3, "cycle": [3.0, 1.5, 4.0, 5.0],
     "areas": ["poison_mist"], "pulse": 1.0, "status": {"id": "poison", "s": 6.0, "power": 0.012},
     "note": "The bandits vent marsh gas through the tunnels: the vents hiss before they breathe. Body tolerates the poison."},
]


def hazards_json():
    for h in HAZARDS:
        assert h["kind"] in ("strike", "gust", "flow", "aura", "pool"), h["id"]
        assert h["answer"] in ("body", "agility", "essence", "spirit", "insight", "fortune", "will"), h["id"]   # Will: S17 Weight zones
        assert len(h["cycle"]) == 4 and h["cycle"][2] > 0, h["id"]
    entries("hazards", HAZARDS)


class Room:
    def __init__(self, rid, name, rtype, region, screens=1, **kw):
        self.id = rid
        self.w = int(SCREEN * screens)
        self.d = {
            "id": rid, "zone": kw.pop("zone", "jade_river_valley"), "region": region, "name": name, "type": rtype,
            "level_range": kw.pop("levels", [0, 0]), "recommended_cp": kw.pop("cp", 0),
            "element": kw.pop("element", "none"), "qi_density": kw.pop("qi", 1.0),
            "hazards": kw.pop("hazards", []), "gather_tier": kw.pop("gather_tier", ""),
            "idle": kw.pop("idle", []), "safe": kw.pop("safe", rtype in ("town", "interior", "home", "sect", "rest", "insight")),
            "no_flight": kw.pop("no_flight", False),
            "bounds": [0, 480, self.w, 480], "backdrop": kw.pop("backdrop", "valley_day"),
            "ground": {"material": kw.pop("material", "moss")},
            "spawn_point": kw.pop("spawn_point", [200, 820]),
            "surfaces": [], "portals": [], "objects": [], "spawns": [], "scenery": [], "decor": [], "areas": [],
        }
        if "tint" in kw:
            self.d["ground"]["tint"] = kw.pop("tint")
        for k, v in kw.items():
            self.d[k] = v
        self._n = 0
        self.rng = random.Random(rid)
        if not self.d.get("custom_ground"):
            self.surface("ground", [0, GROUND_Y, self.w, GROUND_D], 0, kind="ground", stratum="ground")
        ROOMS[rid] = self

    # -- geometry
    def surface(self, sid, rect, height, kind="branch", stratum="platform", **kw):
        s = {"id": sid, "rect": list(rect), "height": height, "kind": kind, "stratum": stratum,
             "open_edges": kw.pop("open_edges", stratum != "ground")}
        s.update(kw)
        self.d["surfaces"].append(s)
        return s

    def building(self, sid, prop, x, front=690, door_dx=0, door=None, **kw):
        """A building prop: roof surface sized from its art (roof_split), facade below."""
        e = PROPS[prop]
        fw, fh = e["frame"]
        roof = int(round(fh * e["roof_split"]))
        facade = fh - roof
        self.surface(sid, [x - fw // 2, front - roof, fw, roof], facade, kind="roof", stratum="platform", art=prop, **kw)
        if door:
            to, to_portal = door[0], door[1]
            self.portal(door[2] if len(door) > 2 else "door_" + sid, "door", [x + door_dx, front + 14], to, to_portal,
                        press_up=True, **(door[3] if len(door) > 3 else {}))
        return (x + door_dx, front + 14)

    def painted(self, sid, art, x, width, depth, height, front=690, **kw):
        """Painted atlas building (gate, hall, two_storey, tower) scaled to a roof height."""
        self.surface(sid, [x - width // 2, front - depth, width, depth], height, kind="roof", stratum="platform", art=art, **kw)

    def ladder(self, sid, x, front, height, width=48, depth=70):
        """A ladder: a narrow ramp in front of a facade, `height` at its back edge (the roof
        line) and 0 at its front edge. Walkers may step between a ladder and any surface
        at the same height (the only cross-layer move the engine allows)."""
        return self.surface(sid, [x - width // 2, front, width, depth], height, kind="ladder", stratum="platform",
                            rise=-height, rise_axis="y", open_edges=False)

    def stairs(self, sid, rect, height, rise_axis="y"):
        return self.surface(sid, rect, 0, kind="stairs", stratum="ground", rise=-height if rise_axis == "y" else height,
                            rise_axis=rise_axis, open_edges=False)

    def area(self, kind, rect, **kw):
        a = {"kind": kind, "rect": list(rect)}
        a.update(kw)
        self.d["areas"].append(a)

    # -- portals
    def portal(self, pid, ptype, at, to, to_portal, **kw):
        p = {"id": pid, "type": ptype, "at": list(at), "to": to, "to_portal": to_portal}
        p.update(kw)
        self.d["portals"].append(p)
        return p

    def edge(self, pid, side, to, to_portal, y=850, **kw):
        x = 40 if side == "west" else self.w - 40
        return self.portal(pid, kw.pop("ptype", "edge"), [x, y], to, to_portal, **kw)

    # -- objects
    def obj(self, oid, otype, at, **kw):
        o = {"id": oid, "type": otype, "at": list(at)}
        o.update(kw)
        self.d["objects"].append(o)
        return o

    def npc(self, npc, at, oid=None, **kw):
        return self.obj(oid or "npc_" + npc, "npc", at, npc=npc, **kw)

    def herb(self, item, at, oid=None, **kw):
        prop, y = HERBS[item]
        self._n += 1
        return self.obj(oid or "herb_%d" % self._n, "herb_patch", at, item=item, prop=prop, **{"yield": y},
                        rank=HERB_RANK[item], regrow_s=kw.pop("regrow_s", 240),
                        requires=all_of(unlock("herb_gathering")), locked_text="You don't know which leaves are worth picking yet.", **kw)

    def ore(self, item, at, oid=None, **kw):
        prop, y = ORES[item]
        self._n += 1
        return self.obj(oid or "ore_%d" % self._n, "ore_vein", at, item=item, prop=prop, **{"yield": y},
                        rank=ORE_RANK[item], regrow_s=kw.pop("regrow_s", 300),
                        requires=all_of(unlock("mining")), locked_text="The stone is too hard to work by hand.", **kw)

    def fishing(self, spot, at, oid=None):
        self._n += 1
        return self.obj(oid or "fish_%d" % self._n, "fishing_spot", at, spot=spot,
                        requires=all_of(unlock("fishing")), locked_text="You have no rod.")

    def breakable(self, at, loot="jar_valley_low", kind="jar", level=1):
        self._n += 1
        return self.obj("%s_%d" % (kind, self._n), kind, at, loot=loot, level=level, hp=1, respawn_s=300)

    def chest(self, at, loot="chest_valley", level=1, oid=None, **kw):
        self._n += 1
        return self.obj(oid or "chest_%d" % self._n, "chest", at, loot=loot, level=level, **kw)

    def spawn(self, enemy, points, mx, respawn=12, level=None, surface="ground", **kw):
        s = {"enemy": enemy, "surface": surface, "points": [list(p) for p in points], "max": mx, "respawn_s": respawn}
        if level:
            s["level"] = level
        s.update(kw)
        self.d["spawns"].append(s)
        return s

    def decor(self, prop, at, layer="play", **kw):
        d = {"prop": prop, "at": list(at), "layer": layer}
        d.update(kw)
        self.d["decor"].append(d)
        return d

    def block(self, prop, x, y, fw=40, fd=16, height=120, **kw):
        """Blocking scenery (trees, rocks, lanterns inside the walk strip)."""
        self._n += 1
        s = {"id": "%s_%d" % (prop, self._n), "prop": prop, "position": [x, y], "front_y": y,
             "footprint": [x - fw // 2, y - fd, fw, fd], "height": height}
        s.update(kw)
        self.d["scenery"].append(s)
        return s

    def points(self, n, x0=None, x1=None, y0=700, y1=930):
        """Spawn points spread across the room, kept 220 units away from edge portals."""
        x0 = 260 if x0 is None else x0
        x1 = self.w - 260 if x1 is None else x1
        out = []
        for i in range(n):
            x = x0 + (x1 - x0) * (i + 0.5) / n + self.rng.randint(-60, 60)
            y = self.rng.randint(y0, y1)
            out.append([int(x), int(y)])
        return out

    def build(self):
        # Shrines are revival points: keep monster spawns (and elites) well away from them,
        # and never spawn inside a portal's area (Part 7 room walk).
        shrines = [o["at"][0] for o in self.d["objects"] if o["type"] == "shrine"]
        portals = [p["at"] for p in self.d["portals"] if "at" in p]
        w = self.d["bounds"][2] if "bounds" in self.d else 2560

        def clear(pt):
            return all(abs(pt[0] - x) >= 380 for x in shrines) and \
                all(((pt[0] - a[0]) ** 2 + (pt[1] - a[1]) ** 2) ** 0.5 > 130 for a in portals)

        for sp in self.d["spawns"]:
            if sp.get("boss") or sp.get("field_boss"):
                continue
            fixed = []
            for pt in sp["points"]:
                if clear(pt):
                    fixed.append(pt)
                    continue
                for dx in (420, -420, 600, -600, 800, -800, 250, -250):
                    cand = [pt[0] + dx, pt[1]]
                    if 80 <= cand[0] <= w - 80 and clear(cand):
                        fixed.append(cand)
                        break
            sp["points"] = fixed or sp["points"]
        return self.d


def link(a, pa, b, pb):
    LINKS.append((a, pa, b, pb))


# ---------------------------------------------------------------------------------------------
# Scenery helpers
def back_trees(r, props=("willow_tree", "pine_tree"), step=520, y=636, start=180, skip=()):
    x = start
    i = 0
    while x < r.w - 100:
        if not any(a <= x <= b for a, b in skip):
            r.decor(props[i % len(props)], [x + r.rng.randint(-60, 60), y + r.rng.randint(-8, 4)], flip=bool(i % 2))
        x += step + r.rng.randint(-80, 80)
        i += 1


def front_grass(r, props=("tall_grass", "reeds"), step=300, y=988):
    x = 120
    i = 0
    while x < r.w:
        r.decor(props[i % len(props)], [x + r.rng.randint(-40, 40), y], layer="front", flip=bool(i % 2))
        x += step + r.rng.randint(-60, 90)
        i += 1


def lantern_row(r, xs, y=660):
    for x in xs:
        r.decor("lantern_post", [x, y])


def interior(rid, name, region, wall="wall_wood", floor="wood", **kw):
    r = Room(rid, name, kw.pop("rtype", "interior"), region, 1, backdrop="interior", material=floor, custom_ground=True,
             wall={"top": 150, "bottom": 650, "tile": wall}, camera={"y_min": 520, "y_max": 560}, **kw)
    r.surface("ground", [0, 650, SCREEN, 310], 0, kind="ground", stratum="ground")
    r.decor("hanging_lantern", [360, 180], layer="back")
    r.decor("hanging_lantern", [920, 180], layer="back")
    return r


# ---------------------------------------------------------------------------------------------
# Lotus Ferry (Prologue P1-P5)
def lotus_ferry():
    # P1 Fisher's Hut
    r = interior("lf_fishers_hut", "Fisher's Hut", "lotus_ferry", music="home", spawn_point=[330, 780])
    r.decor("window", [640, 330], layer="back")
    r.decor("fishing_net_rack", [860, 660])
    r.decor("bed", [300, 690])
    r.decor("stove", [1060, 680])
    r.decor("table", [640, 770])
    r.decor("shelf", [140, 660])
    r.decor("rug", [640, 820])
    r.obj("tea_table", "pickup", [640, 752], item="herbal_tea", count=1, prop="jar", alt=0,
          visible_if=all_of(qactive("morning_tide")), label="Herbal Tea")
    r.obj("tea_shelf", "pickup", [150, 700], item="herbal_tea", count=1, prop="jar",
          visible_if=all_of(qactive("morning_tide")), label="Herbal Tea")
    r.obj("tea_stove", "pickup", [1010, 720], item="herbal_tea", count=1, prop="jar",
          visible_if=all_of(qactive("morning_tide")), label="Herbal Tea")
    r.npc("aunt_ping", [520, 720], facing=-1, hidden_if=all_of(flag("night_active")))
    r.obj("net", "inspect", [860, 700], text="Lu's old net. Half the knots are yours, from when you were small.", prop="none")
    r.portal("exit", "door", [640, 660], "lf_village", "hut_door", press_up=True, label="Home Lane")

    # P2 Lotus Ferry Village: Home Lane (0-1280), Village Square (1280-2560), Ferry Docks (2560-3840)
    r = Room("lf_village", "Lotus Ferry Village", "town", "lotus_ferry", 3, material="earth", backdrop="valley_day",
             music="village_day", ambience="river_ambience", spawn_point=[400, 800], town=True, idle=["gather"],
             camera={"y_min": 470, "y_max": 600}, custom_ground=True,
             districts=[{"id": "home_lane", "name": "Home Lane", "x": [0, 1280]}, {"id": "village_square", "name": "Village Square", "x": [1280, 2560]},
                        {"id": "ferry_docks", "name": "Ferry Docks", "x": [2560, 3840]}])
    r.surface("ground", [0, GROUND_Y, 2560, GROUND_D], 0, kind="ground", stratum="ground")
    r.surface("docks_shore", [2560, GROUND_Y, 1280, 230], 0, kind="ground", stratum="ground", material="earth")
    r.surface("pier_a", [2980, 850, 140, 110], 0, kind="dock", stratum="ground")
    r.surface("pier_b", [3330, 850, 180, 110], 0, kind="dock", stratum="ground")
    r.area("river", [2560, 850, 1280, 160])
    # Home Lane
    r.building("fishers_hut", "thatched_hut", 420, front=690, door_dx=10, door=("lf_fishers_hut", "exit", "hut_door", {"label": "Fisher's Hut"}))
    r.building("granny_hut", "herb_hut", 1000, front=690, door_dx=0, door=("lf_granny_liu_hut", "exit", "granny_door", {"label": "Granny Liu's Herb Hut"}))
    r.decor("well", [700, 700])
    r.decor("fence_wood", [140, 668])
    r.decor("willow_tree", [720, 640])
    r.decor("drying_rack_fish", [250, 760])
    r.decor("flowers_wild", [1180, 740])
    r.block("barrel", 560, 720, 30, 14, 50)
    r.edge("west_gate", "west", "wp_east", "east", y=850, ptype="gate",
           requires=all_of(flag("night_survived")), locked_text="The West Gate is barred until morning.")
    r.obj("sign_home", "signpost", [150, 860], text="West: Willow Path (Lv 1-3) · Stoneford Market beyond.")
    # Village Square
    r.building("old_ma_store", "village_store", 1720, front=690, door_dx=40, door=("lf_old_ma_store", "exit", "store_door", {"label": "Old Ma's Store"}))
    r.painted("village_hall", "hall", 2150, 420, 110, 88, front=690)
    r.ladder("hall_ladder", 1920, 690, 88)
    r.painted("ferry_inn", "two_storey", 2470, 240, 120, 176, front=680)
    r.obj("kite", "pickup", [2470, 610], alt=176, item="kite", count=1, prop="stuck_kite",
          hidden_if=all_of(qdone("the_runaway_kite")), requires=all_of(qactive("the_runaway_kite")),
          locked_text="A kite is tangled on the inn roof.", label="Little Dou's Kite", radius=70)
    r.obj("shrine_village", "shrine", [1450, 700])
    r.obj("board_village", "notice_board", [2000, 700], hidden_if=all_of(noflag("prologue_done")))
    r.obj("stump_guo", "training_stump", [1560, 900])
    r.obj("dummy_guo", "training_dummy", [1660, 920])
    r.decor("lantern_string", [1900, 560], layer="back")
    lantern_row(r, [1330, 2280], y=700)
    r.decor("market_stall", [2240, 770])
    r.block("stone_lantern", 1280, 760, 30, 14, 90)
    r.obj("storage_village", "storage_chest", [1870, 700], requires=all_of(unlock("storage")), locked_text="The village chest is for family goods.")
    r.obj("cook_village", "cooking_pot", [2300, 880], requires=all_of(unlock("cooking")), locked_text="Aunt Ping's pot. Not yet.")
    r.obj("spring_village", "qi_spring", [1180, 900], spring=True, requires=all_of(unlock("qi_springs")),
          text="Qi wells up from the old spring stones.", locked_text="Just a damp patch of stones.")
    # Ferry Docks
    r.decor("dock_planks", [3060, 862])
    r.decor("mooring_post", [2980, 860])
    r.decor("mooring_post", [3510, 860])
    r.decor("lu_boat", [3420, 960])
    r.decor("fishing_net_rack", [2720, 660])
    r.decor("sack_pile", [2860, 700])
    r.decor("lotus_pads", [3700, 930])
    r.building("watch_tower", "watch_tower", 3660, front=690)
    r.obj("tower_bell", "bell", [3590, 710], visible_if=all_of(qactive("race_to_the_tower")))
    r.fishing("village_docks", [3060, 910], oid="fish_docks")
    r.portal("boat", "door", [3420, 872], "lf_lu_boat", "deck", press_up=True, label="Lu's Boat",
             requires=all_of(flag("night_survived")), locked_text="Lu's boat. He'll take you out when he's ready.")
    r.edge("east_gate", "east", "lf_reed_shallows", "west", y=760, ptype="gate",
           requires=all_of(qdone("fists_first")), locked_text="Uncle Guo won't let you past without learning to punch.")
    # Villagers (the seven): placed by district; some move after the Prologue.
    r.npc("lu_boatman", [3280, 800], facing=-1)
    r.npc("little_dou", [2250, 900], facing=1)
    r.npc("uncle_guo", [1610, 820], facing=-1)
    r.npc("shen_lian_npc", [3100, 760], facing=-1, hidden_if=all_of(flag("prologue_done")))
    r.npc("fisher_wen", [2800, 780], facing=1)
    r.npc("washer_mei", [880, 880], facing=1)
    r.npc("aunt_ping", [560, 800], oid="npc_aunt_ping_lane", facing=1, visible_if=all_of(qdone("morning_tide")))
    back_trees(r, ("willow_tree", "plum_tree", "willow_tree"), step=600, skip=[(300, 560), (880, 1150), (1560, 2600), (3560, 3760)])
    front_grass(r, ("tall_grass", "flowers_wild"), step=420)

    r = interior("lf_old_ma_store", "Old Ma's Store", "lotus_ferry", music="village_day")
    r.decor("counter", [640, 740])
    r.decor("shelf", [300, 660])
    r.decor("shelf", [980, 660])
    r.decor("sack_pile", [180, 760])
    r.decor("barrel", [1100, 760])
    r.npc("old_ma", [640, 700], facing=1)
    r.portal("exit", "door", [640, 660], "lf_village", "store_door", press_up=True)

    r = interior("lf_granny_liu_hut", "Granny Liu's Herb Hut", "lotus_ferry", music="village_day")
    r.decor("herb_drawers", [300, 660])
    r.decor("herb_drawers", [980, 660])
    r.decor("incense_burner", [820, 720])
    r.decor("table", [560, 760])
    r.npc("granny_liu", [640, 720], facing=-1)
    r.obj("shrine_granny", "shrine", [1080, 740], prop="altar")
    r.portal("exit", "door", [640, 660], "lf_village", "granny_door", press_up=True)

    # P3 Reed Shallows (first fight)
    r = Room("lf_reed_shallows", "Reed Shallows", "field", "lotus_ferry", 2, levels=[1, 3], cp=40, element="water",
             gather_tier="valley_low", idle=["hunt", "gather"], backdrop="valley_day", music="reeds_day", ambience="river_ambience",
             material="moss", spawn_point=[140, 820])
    r.area("shallows", [620, 850, 1500, 110])
    r.area("river", [0, 960, 2560, 60])
    r.surface("driftwood_a", [760, 720, 210, 46], 60, kind="branch", art="driftwood")
    r.surface("driftwood_b", [1260, 780, 230, 46], 90, kind="branch", art="driftwood")
    r.surface("driftwood_c", [1880, 700, 200, 46], 70, kind="branch", art="driftwood")
    r.spawn("mudshell_crab", [[520, 760], [900, 880], [1140, 820], [1480, 900], [1700, 760], [2000, 880]], 6, respawn=8, level=[1, 1])
    r.spawn("reedtail_rat", [[1300, 700], [1650, 700], [2100, 760], [2300, 820]], 4, respawn=8, level=[2, 2])
    r.spawn("old_snapper", [[2200, 860]], 1, respawn=180, level=[3, 3], elite=True, mini_boss=True,
            requires=all_of(qactive("crab_trouble"), {"kind": "item_owned", "item": "crab_shell", "count": 5}))
    for p in [[400, 720], [980, 930], [1560, 700], [2240, 720], [2420, 900]]:
        r.breakable(p)
    r.herb("willow_moss", [700, 690])
    r.herb("willow_moss", [1760, 690])
    r.herb("willow_moss", [2380, 700])
    r.fishing("reed_shallows", [1100, 920])
    r.decor("reeds", [640, 650])
    r.decor("reeds", [1180, 640])
    r.decor("reeds", [2150, 646])
    r.decor("lotus_pads", [1500, 948])
    r.decor("willow_tree", [300, 636])
    r.decor("willow_tree", [1940, 632], flip=True)
    r.decor("boulder_moss", [2480, 660])
    front_grass(r, ("reeds", "tall_grass"), step=260)
    r.edge("west", "west", "lf_village", "east_gate", y=820)
    r.edge("east", "east", "rm_marsh_edge", "west", y=820, ptype="sealed", requires=all_of(realm("bone_forging_4")),
           locked_text="The marsh path is too dangerous before Bone Forging 4.")

    # P4 Night in the village (instanced set piece; survival 60 s)
    r = Room("lf_village_night", "Lotus Ferry at Night", "story", "lotus_ferry", 2, material="earth", backdrop="valley_night",
             music="night_hollow", ambience="night_ambience", spawn_point=[1500, 820], instanced=True, safe=False,
             tint="#8fa0b8", night=True, custom_ground=True, levels=[1, 1],
             event={"id": "hollow_night", "duration": 60, "wave": {"enemy": "hollow_minnow", "every_s": 2.5, "max": 7,
                                                                   "points": [[300, 880], [900, 930], [1400, 900], [2000, 930], [2400, 880]]},
                    "fixed_spawns": [{"enemy": "hollowed_eel", "at": [1900, 940], "level": 10}],
                    "on_complete": [{"kind": "set_flag", "flag": "night_survived"}, {"kind": "clear_flag", "flag": "night_active"},
                                    {"kind": "teleport", "target": "lf_lu_boat", "portal": "deck"}],
                    "requires": all_of(noflag("night_survived"))})
    r.surface("ground", [0, GROUND_Y, 2560, 280], 0, kind="ground", stratum="ground")
    r.area("river", [0, 900, 2560, 120])
    r.building("fishers_hut_n", "thatched_hut", 420, front=690, tint="#7d8ca8")
    r.building("granny_hut_n", "herb_hut", 1000, front=690, tint="#7d8ca8")
    r.building("old_ma_store_n", "village_store", 1720, front=690, tint="#7d8ca8")
    r.painted("village_hall_n", "hall", 2150, 420, 110, 88, front=690, tint="#7d8ca8")
    r.obj("hut_refuge", "inspect", [430, 704], text="Aunt Ping has the door open. Get everyone inside!", prop="none")
    r.npc("little_dou", [2250, 820], oid="npc_dou_night", pose="idle", hidden_if=all_of(flag("dou_safe")), facing=-1)
    r.npc("granny_liu", [1000, 740], oid="npc_granny_night", hidden_if=all_of(flag("granny_safe")), facing=1)
    r.npc("old_ma", [1720, 760], oid="npc_ma_night", hidden_if=all_of(flag("ma_safe")), facing=-1)
    lantern_row(r, [700, 1330, 2280], y=700)
    r.decor("grey_patch", [1300, 900])
    r.decor("grey_patch", [2100, 880])
    r.decor("mist_bank", [900, 990], layer="front")
    r.decor("mist_bank", [2000, 990], layer="front")

    # P5 Lu's Boat (meditation, first breakthrough)
    r = Room("lf_lu_boat", "Lu's Boat", "home", "lotus_ferry", 1, material="wood", backdrop="valley_dusk", music="meditation",
             ambience="river_ambience", spawn_point=[520, 800], custom_ground=True, qi=1.4, element="water", camera={"y_min": 520, "y_max": 560})
    r.surface("deck", [240, 700, 800, 170], 0, kind="deck", stratum="ground")
    r.area("river", [0, 860, 1280, 160])
    r.area("river", [0, 640, 1280, 60])
    r.decor("lu_boat", [640, 900], scale=2.6)
    r.decor("meditation_mat", [560, 790])
    r.decor("lamp_oil", [900, 720])
    r.decor("lotus_pads", [180, 960])
    r.decor("lotus_pads", [1120, 940])
    r.npc("lu_boatman", [840, 760], oid="npc_lu_boat", facing=-1, pose="meditate")
    r.obj("boat_spring", "qi_spring", [560, 800], spring=False, prop="none", text="The river's breath is strong here.")
    r.portal("deck", "door", [300, 780], "lf_village", "boat", press_up=True, label="Ferry Docks",
             requires=all_of(qdone("the_river_token")), locked_text="Lu: \"Sit. Breathe. The shore can wait.\"")


# ---------------------------------------------------------------------------------------------
def field(rid, name, region, screens, levels, backdrop, material, spawns, herbs=(), ores=(), jars=5, chest=None,
          element="none", gather_tier="", qi=1.0, music="field", ambience="", rtype="field", trees=("willow_tree", "pine_tree"),
          platforms=(), fishing=None, loot="jar_valley_low", elite=True, hazards=(), ledge=None, front=None, **kw):
    r = Room(rid, name, rtype, region, screens, levels=levels, cp=int(20 + levels[0] * 18), element=element,
             gather_tier=gather_tier, idle=kw.pop("idle", ["hunt", "gather"]), backdrop=backdrop, material=material,
             music=music, ambience=ambience, qi=qi, hazards=list(hazards), **kw)
    lv_mid = max(1, (levels[0] + levels[1]) // 2)
    for i, (sx, sy, w, h) in enumerate(platforms):
        r.surface("ledge_%d" % i, [sx, sy, w, 50], h, kind=ledge or ("rock_ledge" if material in ("stone", "slate", "rock", "snow") else "branch"))
    for i, sp in enumerate(spawns):
        enemy, count, lv = sp[0], sp[1], sp[2]
        pts = r.points(count + 1, x0=240 + i * 60, x1=r.w - 240 - i * 40)
        r.spawn(enemy, pts, count, respawn=sp[3] if len(sp) > 3 else 12, level=lv)
    if elite and spawns:
        enemy, count, lv = spawns[0][0], spawns[0][1], spawns[0][2]
        r.spawn(enemy, [[r.w // 2 + 200, 820]], 1, respawn=180, level=[lv[1], lv[1]], elite=True)
    xs = [int(r.w * (i + 0.5) / max(1, len(herbs) + len(ores))) for i in range(len(herbs) + len(ores))]
    for i, h in enumerate(herbs):
        r.herb(h, [xs[i] + r.rng.randint(-60, 60), r.rng.choice([690, 700, 930])])
    for j, o in enumerate(ores):
        r.ore(o, [xs[len(herbs) + j] + r.rng.randint(-60, 60), 690])
    for i in range(jars):
        x = int(r.w * (i + 0.5) / jars) + r.rng.randint(-80, 80)
        r.breakable([x, r.rng.choice([700, 720, 900, 930])], loot=loot, level=lv_mid,
                    kind="crate" if material in ("stone", "slate", "earth", "rock") and i % 2 else "jar")
    if chest:
        r.chest([r.w - 360, 700], loot=chest, level=levels[1])
    if fishing:
        r.fishing(fishing, [r.w // 2 - 200, 930])
    back_trees(r, trees)
    front_grass(r, props=front or {"snow": ("rock_small", "rock_small"), "rock": ("tall_grass", "rock_small"),
                                   "sand": ("rock_small", "rock_small")}.get(material, ("tall_grass", "reeds")),
                step=420 if material == "snow" else 300)
    return r


def town(rid, name, region, screens=2, backdrop="valley_day", material="stone", **kw):
    r = Room(rid, name, kw.pop("rtype", "town"), region, screens, backdrop=backdrop, material=material,
             music=kw.pop("music", "village_day"), ambience=kw.pop("ambience", "town_ambience"), town=True, **kw)
    return r


def stoneford():
    r = town("sf_gate", "Stoneford Gate", "stoneford", 2, spawn_point=[2300, 820])
    r.painted("gatehouse", "gate", 1280, 520, 120, 150, front=680)
    r.building("guard_tower", "watch_tower", 420, front=690)
    r.decor("flag_pole_jade", [980, 660])
    r.decor("flag_pole_cloud", [1580, 660])
    r.decor("cart_broken", [2000, 720])
    r.obj("shrine_sf_gate", "shrine", [1800, 700])
    r.obj("sign_sf_gate", "signpost", [2380, 860], text="East: Willow Path · West: Market Street · North: Stonewall Quarry (Lv 4-7).")
    r.npc("guard_hou", [1180, 760], facing=1)
    r.npc("foreman_dong", [660, 760], facing=1)
    r.npc("adventurer_kai", [1500, 900], facing=-1)
    r.edge("east", "east", "wp_west", "west", y=850)
    r.edge("west", "west", "sf_market", "east", y=850)
    r.portal("quarry_road", "door", [660, 700], "sq_quarry_rim", "south", press_up=True, label="Quarry Road",
             requires=all_of(realm("bone_forging_4")), locked_text="Foreman Dong: \"Quarry's no place for a Bone Forging 3 kid.\"")
    back_trees(r, ("pine_tree", "willow_tree"), skip=[(1000, 1560), (300, 540)])

    r = town("sf_market", "Market Street", "stoneford", 2, spawn_point=[2300, 820], idle=["gather"])
    r.building("general_store", "village_store", 520, front=690)
    r.building("tea_house", "village_house", 1280, front=690)
    r.building("warehouse_sf", "warehouse", 2020, front=690)
    r.decor("market_stall", [900, 780])
    r.decor("market_stall", [1660, 780], flip=True)
    r.decor("lantern_string", [1000, 560], layer="back")
    r.decor("lantern_string", [1800, 560], layer="back")
    r.obj("stone_sf", "teleport_stone", [1480, 880], stone="stoneford")
    r.obj("board_sf", "notice_board", [760, 700])
    r.obj("storage_sf", "storage_chest", [1100, 710], requires=all_of(unlock("storage")), locked_text="The storehouse opens for Qi Kindling cultivators.")
    r.obj("exchange_sf", "inspect", [2240, 720], prop="counter", text="The exchange counter.", open_page="exchange",
          requires=all_of(unlock("currency_exchange")), locked_text="Currency exchange opens at Heaven Glimpse 3.")
    r.npc("storekeeper_fang", [520, 730], facing=1)
    r.npc("auntie_rong", [1280, 730], facing=1)
    r.npc("keeper_shi", [1560, 860], facing=-1)
    r.npc("courier_lin", [1900, 900], facing=1)
    r.npc("adventurer_su", [300, 900], facing=1)
    r.npc("old_pan", [2200, 900], facing=-1, visible_if=all_of(unlock("appraisal")))
    r.edge("east", "east", "sf_gate", "west", y=850)
    r.edge("west", "west", "sf_artisan_row", "east", y=850)

    r = town("sf_artisan_row", "Artisan Row", "stoneford", 2, spawn_point=[2300, 820])
    r.building("smithy", "village_house", 420, front=690)
    r.building("trade_house", "village_store", 1200, front=690, door_dx=40,
               door=("si_gus_warehouse", "entry", "warehouse_door", {"label": "Gu's Warehouse",
                     "requires": all_of(qactive("gus_warehouse")), "locked_text": "Elder Gu's private warehouse. Locked tight."}))
    r.building("alchemy_stall", "herb_hut", 1960, front=690)
    r.obj("anvil_sf", "forge_anvil", [640, 760], requires=all_of(unlock("smithing")), locked_text="Smith Bao's anvil. Not for novices.")
    r.obj("furnace_sf", "alchemy_furnace", [2160, 760], requires=all_of(unlock("alchemy")), locked_text="Mei Qing's furnace.")
    r.npc("smith_bao", [520, 760], facing=1)
    r.npc("tinkerer_yu", [860, 900], facing=1)
    r.npc("elder_gu", [1120, 760], facing=1, hidden_if=all_of(flag("gu_fled")))
    r.npc("madam_hua", [1120, 760], oid="npc_madam_hua", visible_if=all_of(flag("gu_fled")), facing=1)
    r.npc("mei_qing", [1960, 760], facing=-1)
    r.npc("apprentice_tao", [1500, 900], facing=-1)
    r.edge("east", "east", "sf_market", "west", y=850)
    r.edge("west", "west", "sf_fairground", "east", y=850)

    r = town("sf_fairground", "Fairground", "stoneford", 3, material="earth", spawn_point=[3500, 820], music="fair")
    r.decor("recruiter_tent_jade", [900, 680])
    r.decor("recruiter_tent_cloud", [1700, 680])
    r.decor("banner_jade", [700, 670])
    r.decor("banner_cloud", [1900, 670])
    r.decor("lantern_string", [1300, 560], layer="back")
    r.decor("weapon_rack_full", [2700, 690])
    r.npc("recruiter_qing_lan", [900, 760], facing=1)
    r.npc("recruiter_mo_yun", [1700, 760], facing=-1)
    r.npc("shen_lian", [2600, 820], facing=1, visible_if=all_of(flag("prologue_done")))
    r.npc("wen_zhao", [3000, 780], facing=-1, visible_if=all_of(realm("qi_kindling_1")))
    r.npc("fair_vendor_he", [2200, 900], facing=1)
    r.npc("adventurer_rui", [3300, 900], facing=-1)
    r.obj("spar_sf", "spar_post", [2800, 860], opponent="sparring_disciple", requires=all_of(unlock("attack")))
    r.portal("trial_jade", "door", [900, 700], "sf_trial_jade", "entry", press_up=True, label="Entry Trial (Jade)",
             requires=all_of(qactive("entry_trial"), sect("jade_sect")), locked_text="Choose the Jade Sect first.")
    r.portal("trial_cloud", "door", [1700, 700], "sf_trial_cloud", "entry", press_up=True, label="Entry Trial (Cloud)",
             requires=all_of(qactive("entry_trial"), sect("cloud_sect")), locked_text="Choose the Cloud Sect first.")
    r.portal("jade_road", "door", [400, 700], "ja_gate_street", "stoneford", press_up=True, label="Jade Sect Academy",
             requires=all_of(sect("jade_sect"), qdone("entry_trial")), locked_text="Only Jade Sect disciples may take this road.")
    r.portal("cloud_road", "door", [2300, 700], "cm_cliff_stair", "stoneford", press_up=True, label="Cloud Sect Monastery",
             requires=all_of(sect("cloud_sect"), qdone("entry_trial")), locked_text="Only Cloud Sect disciples may climb these stairs.")
    r.edge("east", "east", "sf_artisan_row", "west", y=850)
    r.edge("west", "west", "cr_caravan_road", "east", y=850, ptype="sealed", requires=all_of(realm("qi_kindling_6")),
           locked_text="Caravan Road: bandits. Qi Kindling 6 at least.")
    back_trees(r, ("plum_tree", "willow_tree"), skip=[(600, 2000)])

    for s, name, tint in [("jade", "Entry Trial (Jade)", "#d8efe6"), ("cloud", "Entry Trial (Cloud)", "#e6eef6")]:
        r = Room("sf_trial_" + s, name, "trial", "stoneford", 1, backdrop="sect_" + s, material="stone", instanced=True,
                 music="trial", levels=[2, 2], safe=False, spawn_point=[160, 820], dungeon_exit="sf_fairground")
        r.surface("step_1", [360, 700, 180, 50], 60, kind="rock_ledge")
        r.surface("step_2", [600, 660, 180, 50], 120, kind="rock_ledge")
        r.surface("step_3", [840, 700, 180, 50], 180, kind="rock_ledge")
        r.obj("trial_bell", "bell", [930, 724], alt=180, set_flag="trial_climbed")
        r.spawn("trial_puppet", [[1000, 840]], 1, respawn=9999, level=[2, 2], requires=all_of(flag("trial_climbed")))
        r.decor("banner_" + s, [200, 660])
        r.decor("banner_" + s, [1100, 660])
        r.decor("stone_lantern", [640, 660])
        r.portal("entry", "door", [120, 700], "sf_fairground", "trial_" + s, press_up=True, label="Fairground")


def willow_path():
    r = field("wp_east", "Willow Path East", "willow_path", 2, [1, 2], "valley_day", "earth",
              [("wild_boarlet", 4, [1, 2], 10)], herbs=("willow_moss",), jars=3, rtype="path", gather_tier="valley_low",
              music="field", ambience="birds_ambience", elite=False, trees=("willow_tree", "plum_tree"))
    r.obj("sign_wp", "signpost", [2380, 860], text="Willow Path. East: Lotus Ferry · West: Stoneford Market.")
    r.obj("pan_spot", "inspect", [1300, 700], prop="cart_broken", text="Wheel ruts. A merchant stops here sometimes.")
    r.npc("old_pan", [1400, 780], oid="npc_old_pan_wp", visible_if=all_of(unlock("appraisal")), facing=-1)
    r.obj("note_lu", "inspect", [2300, 720], prop="signpost", text="A note in Lu's hand: \"West, to the training stumps. Punch until the wood remembers you.\"",
          set_flag="read_lu_note")
    r.edge("east", "east", "lf_village", "west_gate", y=850)
    r.edge("west", "west", "wp_west", "east", y=850)

    r = field("wp_west", "Willow Path West", "willow_path", 2, [1, 3], "valley_day", "moss",
              [("wild_boarlet", 5, [1, 2], 10), ("mossback_toad", 3, [2, 3], 12)], herbs=("willow_moss", "willow_moss"), jars=5,
              gather_tier="valley_low", music="field", ambience="birds_ambience")
    for i, x in enumerate([700, 820, 940]):
        r.obj("stump_%d" % i, "training_stump", [x, 700 + i * 20])
    r.obj("lift_1", "lifting_stone", [1200, 720])
    r.obj("lift_2", "lifting_stone", [1320, 900])
    r.obj("shrine_wp", "shrine", [2330, 700])
    r.obj("sign_wpw", "signpost", [160, 860], text="West: Stoneford Gate · East: Willow Path East.")
    r.edge("east", "east", "wp_east", "west", y=850)
    r.edge("west", "west", "sf_gate", "east", y=850)


def sects():
    # Jade Sect Academy: the v0.13 street becomes Gate Street and Pavilion Rooftops.
    street = json.load(open(os.path.join(DATA, "world.json")))
    r = Room("ja_gate_street", "Gate Street", "sect", "jade_sect", 2.1, backdrop="sect_jade", material="stone", music="sect",
             spawn_point=[300, 820], custom_ground=True, sect="jade_sect", town=True)
    r.w = 2740
    r.d["bounds"] = [0, 480, 2740, 480]
    for s in street["surfaces"]:
        x = s["rect"][0]
        if x < 2740 and s["id"] not in ("rear_stairs", "upper_terrace"):
            s2 = dict(s)
            if s2["id"] == "river_walk":
                s2["rect"] = [0, 620, 2740, 340]
                s2["id"] = "ground"
            r.d["surfaces"].append(s2)
    for o in street["objects"]:
        if o["position"][0] < 2740:
            r.d["scenery"].append(o)
    r.obj("shrine_ja", "shrine", [700, 700])
    r.obj("stone_ja", "teleport_stone", [520, 880], stone="jade_academy")
    r.obj("board_ja", "notice_board", [2600, 700])
    r.obj("siege_gong_ja", "rite_circle", [2500, 900], event="siege_of_two_sects", prop="small_bell",
          visible_if=all_of(qactive("the_siege")), text="The war gong. Strike it and the sects march together.")
    r.npc("jade_steward", [360, 760], facing=1)
    r.npc("jade_deacon", [2560, 780], facing=-1)
    r.npc("jade_disciple_a", [1500, 900], facing=1)
    r.npc("jade_disciple_b", [2100, 880], facing=-1)
    r.obj("dorm_bed_ja", "inspect", [1200, 720], prop="bed", text="Your bunk in the service dorm.", rest=True,
          visible_if=all_of(qdone("a_disciples_chores")))
    for i, x in enumerate([1000, 1400, 1900]):
        r.obj("sweep_ja_%d" % i, "inspect", [x, 900], prop="grey_patch", text="Swept clean.", set_flag="swept_ja_%d" % i,
              visible_if=all_of(qactive("a_disciples_chores"), noflag("swept_ja_%d" % i)))
    r.portal("stoneford", "gate", [40, 850], "sf_fairground", "jade_road", label="Stoneford")
    r.edge("east", "east", "ja_pavilion_rooftops", "west", y=850)
    r.portal("weapon_hall", "door", [1210, 704], "ja_weapon_hall", "exit", press_up=True, label="Weapon Hall and Forge",
             requires=all_of(realm("bone_forging_3")), locked_text="The Weapon Hall admits disciples from Bone Forging 3.")
    r.portal("alchemy_hall", "door", [1810, 704], "ja_alchemy_hall", "exit", press_up=True, label="Alchemy Hall")
    r.portal("library", "door", [2410, 704], "ja_library", "exit", press_up=True, label="Library")

    r = Room("ja_pavilion_rooftops", "Pavilion Rooftops", "sect", "jade_sect", 2.1, backdrop="sect_jade", material="stone",
             music="sect", spawn_point=[200, 820], custom_ground=True, sect="jade_sect", town=True)
    r.w = 2660
    r.d["bounds"] = [0, 480, 2660, 480]
    for s in street["surfaces"]:
        if s["rect"][0] >= 2740 or s["id"] == "river_walk":
            s2 = json.loads(json.dumps(s))
            if s2["id"] == "river_walk":
                s2["rect"] = [0, 620, 2660, 340]
                s2["id"] = "ground"
            else:
                s2["rect"][0] -= 2740
            r.d["surfaces"].append(s2)
    for o in street["objects"]:
        if o["position"][0] >= 2740:
            o2 = json.loads(json.dumps(o))
            o2["position"][0] -= 2740
            o2["footprint"][0] -= 2740
            if "occlusion" in o2:
                o2["occlusion"][0] -= 2740
            r.d["scenery"].append(o2)
    r.obj("roof_chest", "chest", [3890 - 2740, 620], alt=300, loot="chest_valley", level=4)
    r.npc("jade_hall_master", [900, 880], facing=1)
    r.npc("jade_weapon_master", [1200, 900], oid="npc_jade_wm_yard", facing=-1, visible_if=all_of(qdone("the_weapon_hall")))
    for i, x in enumerate([500, 620]):
        r.obj("dummy_jp_%d" % i, "training_dummy", [x, 900])
    r.obj("spar_jp", "spar_post", [1500, 900], opponent="sparring_disciple")
    r.edge("west", "west", "ja_gate_street", "east", y=850)
    r.edge("east", "east", "ja_east_terrace", "west", y=850)

    r = Room("ja_east_terrace", "East Terrace", "sect", "jade_sect", 2, backdrop="sect_jade", material="stone", music="sect",
             sect="jade_sect", town=True, spawn_point=[200, 820])
    r.painted("mission_hall", "hall", 700, 600, 130, 120, front=690)
    r.painted("retreat_rooms", "tower", 1900, 280, 140, 200, front=690)
    r.npc("jade_formation_elder", [1300, 800], facing=-1)
    r.npc("jade_physician", [1600, 900], facing=1)
    r.npc("arena_master", [2200, 820], facing=-1)
    r.obj("formation_table_ja", "formation_table", [1100, 880], requires=all_of(unlock("formations")), locked_text="Formation lines. You can't read them yet.")
    r.portal("retreat", "door", [1900, 704], "ja_retreat", "exit", press_up=True, label="Retreat Rooms",
             requires=all_of(unlock("retreat_room")), locked_text="The retreat rooms are kept for inner disciples.")
    r.obj("arena_ja", "spar_post", [2400, 900], opponent="sparring_disciple", requires=all_of(unlock("tournament")))
    r.edge("west", "west", "ja_pavilion_rooftops", "east", y=850)
    r.edge("east", "east", "ja_herb_terraces", "west", y=850)

    r = Room("ja_herb_terraces", "Herb Terraces", "sect", "jade_sect", 2, backdrop="sect_jade", material="moss", music="sect",
             sect="jade_sect", town=True, spawn_point=[200, 820], gather_tier="valley_low")
    r.surface("terrace_1", [600, 660, 500, 90], 60, kind="rock_ledge")
    r.surface("terrace_2", [1300, 640, 500, 90], 120, kind="rock_ledge")
    for i, x in enumerate([700, 850, 1000]):
        r.obj("bed_%d" % i, "garden_bed", [x, 700], alt=60, requires=all_of(unlock("herb_garden")), locked_text="Garden beds belong to inner disciples.")
    r.herb("willow_moss", [400, 900])
    r.herb("riverreed_ginseng_10", [1500, 700], alt=120)
    r.npc("jade_gardener", [1200, 860], facing=-1)
    r.edge("west", "west", "ja_east_terrace", "east", y=850)
    r.portal("peak_path", "door", [2400, 700], "ja_elder_hu_peak", "path", press_up=True, label="Elder Hu's Peak")
    back_trees(r, ("bamboo_cluster", "pine_tree"))

    r = Room("ja_elder_hu_peak", "Elder Hu's Peak", "sect", "jade_sect", 1, backdrop="mist_peak", material="stone", music="meditation",
             sect="jade_sect", qi=1.6, spawn_point=[200, 820], town=True)
    r.npc("elder_hu", [760, 780], facing=-1)
    r.obj("spring_hu", "qi_spring", [480, 880], spring=True, requires=all_of(unlock("qi_springs")), locked_text="The spring is still to you.")
    r.obj("insight_hu", "insight_stone", [1000, 720], element="wood", requires=all_of(unlock("insight_sites")), locked_text="An old carved stone.")
    r.obj("rite_reflection", "rite_circle", [640, 900], event="trial_of_reflections", requires=all_of(realm("heart_tempering_9")),
          locked_text="The Heart Trial circle. Not before Heart Tempering 9.")
    r.decor("pagoda", [1150, 660])
    r.decor("pine_tree", [200, 640])
    r.portal("path", "door", [120, 700], "ja_herb_terraces", "peak_path", press_up=True, label="Herb Terraces")
    r.obj("plot_hu", "treasure_plot", [320, 900], requires=all_of(unlock("natural_treasures")), locked_text="Rich dark earth, ringed with river stones.")
    r.portal("abode", "door", [1180, 700], "ja_cave_abode", "exit", press_up=True, label="Cave Abode",
             requires=all_of(qdone("the_mentors_gift")), locked_text="Elder Hu's cave. Only a personal disciple may enter.")

    for rid, name, tile, npcs, objs in [
        ("ja_weapon_hall", "Weapon Hall and Forge", "wall_stone", [("jade_weapon_master", 640), ("jade_smith", 1000)],
         [("anvil_ja", "forge_anvil", [1000, 800], all_of(unlock("smithing")))]),
        ("ja_alchemy_hall", "Alchemy Hall", "wall_plaster", [("mei_qing_sect", 800)],
         [("furnace_ja", "alchemy_furnace", [640, 800], all_of(unlock("alchemy")))]),
        ("ja_library", "Library", "wall_wood", [("jade_librarian", 640)], [])]:
        r = interior(rid, name, "jade_sect", wall=tile, floor="floor_stone", rtype="sect", sect="jade_sect", music="sect")
        for npc, x in npcs:
            r.npc(npc, [x, 760], facing=-1)
        for oid, ot, at, rq in objs:
            o = r.obj(oid, ot, at, requires=rq, locked_text="Not yet.")
            if ot == "alchemy_furnace":
                o["furnace_bonus"] = 0.5   # the Alchemy Hall's furnace: better odds of a rare pill quality
        if rid == "ja_weapon_hall":
            r.decor("weapon_rack_full", [300, 670])
            r.decor("weapon_rack_full", [460, 670])
            for i, x in enumerate([280, 420]):
                r.obj("dummy_wh_%d" % i, "training_dummy", [x, 880])
        if rid == "ja_library":
            r.decor("bookcase", [220, 660])
            r.decor("bookcase", [1060, 660])
            r.decor("scroll_rack", [860, 670])
        if rid == "ja_alchemy_hall":
            r.decor("herb_drawers", [260, 660])
            r.decor("herb_drawers", [1020, 660])
        back = {"ja_weapon_hall": "weapon_hall", "ja_alchemy_hall": "alchemy_hall", "ja_library": "library"}[rid]
        r.portal("exit", "door", [640, 660], "ja_gate_street", back, press_up=True)

    # Cloud Sect Monastery
    r = Room("cm_cliff_stair", "Cliff Stair", "sect", "cloud_sect", 2, backdrop="sect_cloud", material="stone", music="sect",
             sect="cloud_sect", town=True, spawn_point=[200, 860])
    r.stairs("stair_a", [700, 640, 240, 150], 100)
    r.surface("landing", [700, 560, 560, 80], 100, kind="rock_ledge", stratum="ground", open_edges=False)
    r.surface("ledge_hi", [1500, 640, 300, 60], 200, kind="rock_ledge")
    r.obj("shrine_cm", "shrine", [1300, 880])
    r.obj("stone_cm", "teleport_stone", [460, 880], stone="cloud_monastery")
    r.obj("board_cm", "notice_board", [1800, 880])
    r.obj("siege_gong_cm", "rite_circle", [2200, 900], event="siege_of_two_sects", prop="small_bell",
          visible_if=all_of(qactive("the_siege")), text="The war gong. Strike it and the sects march together.")
    r.npc("cloud_steward", [360, 780], facing=1)
    r.npc("cloud_deacon", [2000, 800], facing=-1)
    r.npc("cloud_disciple_a", [1100, 900], facing=1)
    r.obj("dorm_bed_cm", "inspect", [1600, 900], prop="bed", text="Your bunk in the service dorm.", rest=True,
          visible_if=all_of(qdone("a_disciples_chores")))
    for i, x in enumerate([900, 1400, 2100]):
        r.obj("sweep_cm_%d" % i, "inspect", [x, 920], prop="grey_patch", text="Swept clean.", set_flag="swept_cm_%d" % i,
              visible_if=all_of(qactive("a_disciples_chores"), noflag("swept_cm_%d" % i)))
    r.decor("paifang_gate", [300, 650])
    r.decor("pine_tree", [2400, 640])
    r.portal("stoneford", "gate", [40, 850], "sf_fairground", "cloud_road", label="Stoneford")
    r.edge("east", "east", "cm_sword_court", "west", y=850)

    r = Room("cm_sword_court", "Sword Court", "sect", "cloud_sect", 2, backdrop="sect_cloud", material="floor_stone", music="sect",
             sect="cloud_sect", town=True, spawn_point=[200, 860])
    r.painted("sword_hall", "hall", 1280, 640, 130, 110, front=690)
    r.npc("cloud_hall_master", [700, 820], facing=1)
    r.npc("arena_master", [1900, 820], oid="npc_arena_cm", facing=-1)
    for i, x in enumerate([400, 520]):
        r.obj("dummy_cs_%d" % i, "training_dummy", [x, 900])
    r.obj("spar_cm", "spar_post", [1600, 900], opponent="sparring_disciple")
    r.portal("weapon_hall", "door", [1100, 704], "cm_weapon_hall", "exit", press_up=True, label="Weapon Hall and Forge",
             requires=all_of(realm("bone_forging_3")), locked_text="The Weapon Hall admits disciples from Bone Forging 3.")
    r.portal("library", "door", [1460, 704], "cm_cloud_library", "exit", press_up=True, label="Cloud Library")
    r.edge("west", "west", "cm_cliff_stair", "east", y=850)
    r.edge("east", "east", "cm_array_court", "west", y=850)

    r = Room("cm_array_court", "Array Court", "sect", "cloud_sect", 2, backdrop="sect_cloud", material="floor_stone", music="sect",
             sect="cloud_sect", town=True, spawn_point=[200, 860])
    r.npc("cloud_formation_elder", [900, 800], facing=-1)
    r.npc("cloud_physician", [1400, 900], facing=1)
    for i, x in enumerate([700, 1000, 1300]):
        r.decor("formation_node", [x, 760])
    r.obj("formation_table_cm", "formation_table", [1100, 880], requires=all_of(unlock("formations")), locked_text="Formation lines. You can't read them yet.")
    r.painted("retreat_rooms_cm", "tower", 1900, 280, 140, 200, front=690)
    r.portal("retreat", "door", [1900, 704], "cm_retreat", "exit", press_up=True, label="Retreat Rooms",
             requires=all_of(unlock("retreat_room")), locked_text="The retreat rooms are kept for inner disciples.")
    r.obj("furnace_cm", "alchemy_furnace", [2200, 760], requires=all_of(unlock("alchemy")), locked_text="The monastery furnace.", furnace_bonus=0.5)
    r.surface("rope_ledge", [1500, 640, 260, 50], 150, kind="rock_ledge")
    r.edge("west", "west", "cm_sword_court", "east", y=850)
    r.portal("peak_path", "door", [2400, 700], "cm_elder_sung_peak", "path", press_up=True, label="Elder Sung's Peak")

    r = Room("cm_elder_sung_peak", "Elder Sung's Peak", "sect", "cloud_sect", 1, backdrop="mist_peak", material="stone", music="meditation",
             sect="cloud_sect", qi=1.6, spawn_point=[200, 820], town=True)
    r.npc("elder_sung", [760, 780], facing=-1)
    r.obj("spring_sung", "qi_spring", [480, 880], spring=True, requires=all_of(unlock("qi_springs")), locked_text="The spring is still to you.")
    r.obj("insight_sung", "insight_stone", [1000, 720], element="wind", requires=all_of(unlock("insight_sites")), locked_text="An old carved stone.")
    r.obj("rite_reflection_cm", "rite_circle", [640, 900], event="trial_of_reflections", requires=all_of(realm("heart_tempering_9")),
          locked_text="The Heart Trial circle. Not before Heart Tempering 9.")
    r.decor("pagoda", [1150, 660])
    r.portal("path", "door", [120, 700], "cm_array_court", "peak_path", press_up=True, label="Array Court")
    r.obj("plot_sung", "treasure_plot", [320, 900], requires=all_of(unlock("natural_treasures")), locked_text="Rich dark earth, ringed with river stones.")
    r.portal("abode", "door", [1180, 700], "cm_cave_abode", "exit", press_up=True, label="Cave Abode",
             requires=all_of(qdone("the_mentors_gift")), locked_text="Elder Sung's cave. Only a personal disciple may enter.")

    for rid, name, tile, npcs, back in [
        ("cm_weapon_hall", "Weapon Hall and Forge", "wall_stone", [("cloud_weapon_master", 640), ("cloud_smith", 1000)], "weapon_hall"),
        ("cm_cloud_library", "Cloud Library", "wall_plaster", [("cloud_librarian", 640)], "library")]:
        r = interior(rid, name, "cloud_sect", wall=tile, floor="floor_stone", rtype="sect", sect="cloud_sect", music="sect")
        for npc, x in npcs:
            r.npc(npc, [x, 760], facing=-1)
        if rid == "cm_weapon_hall":
            r.decor("weapon_rack_full", [300, 670])
            r.decor("weapon_rack_full", [460, 670])
            for i, x in enumerate([280, 420]):
                r.obj("dummy_cwh_%d" % i, "training_dummy", [x, 880])
            r.obj("anvil_cm", "forge_anvil", [1000, 820], requires=all_of(unlock("smithing")), locked_text="Not yet.")
        else:
            r.decor("bookcase", [220, 660])
            r.decor("bookcase", [1060, 660])
        r.portal("exit", "door", [640, 660], "cm_sword_court", back, press_up=True)

    retreat_rooms("ja_retreat", "jade_sect", "ja_east_terrace")
    retreat_rooms("cm_retreat", "cloud_sect", "cm_array_court")
    cave_abode("ja_cave_abode", "jade_sect", "ja_elder_hu_peak", "wood")
    cave_abode("cm_cave_abode", "cloud_sect", "cm_elder_sung_peak", "wind")


def retreat_rooms(rid, sect_id, back):
    """A sect retreat room (S07): a quiet hall of screened cells. Seclusion here runs to the
    16 h cap and a breakthrough attempt is one risk step safer."""
    r = interior(rid, "Retreat Rooms", sect_id, wall="wall_plaster", floor="floor_stone", rtype="sect", sect=sect_id,
                 music="meditation", retreat=True, qi=1.3, spawn_point=[640, 820])
    banner = "banner_jade" if sect_id == "jade_sect" else "banner_cloud"
    r.decor("window", [640, 330], layer="back")
    for x in (200, 1100):
        r.decor(banner, [x, 640], layer="back")
    for x in (330, 950):
        r.decor("screen_folding", [x, 680])
    for x in (200, 470, 810, 1080):
        r.decor("meditation_mat", [x, 740])
    r.decor("altar", [640, 670])
    r.decor("incense_burner", [640, 700])
    r.decor("rug", [640, 800])
    r.obj("mat_" + rid, "inspect", [640, 780], prop="meditation_mat", text="A bare cell, a mat, the smell of cold incense.",
          open_page="seclusion", requires=all_of(unlock("seclusion")), locked_text="Seclusion comes at Bone Forging 7.", label="Retreat")
    r.portal("exit", "door", [120, 660], back, "retreat", press_up=True, label=ROOMS[back].d["name"])
    return r


def cave_abode(rid, sect_id, peak, element):
    """A personal disciple's cave abode (SA5): dense Qi, a private spring and a mat for long
    seclusion. It counts as a retreat room."""
    r = Room(rid, "Cave Abode", "sect", sect_id, 1, backdrop="cave", material="slate", music="meditation", sect=sect_id,
             qi=2.2, retreat=True, element=element, spawn_point=[220, 820])
    r.obj("spring_" + rid, "qi_spring", [520, 900], spring=True, requires=all_of(unlock("qi_springs")), locked_text="Still water.")
    r.obj("mat_" + rid, "inspect", [860, 780], prop="meditation_mat", text="Your mat. The rock hums with Qi.", open_page="seclusion",
          requires=all_of(unlock("seclusion")), label="Seclusion")
    r.obj("bed_" + rid, "inspect", [1000, 700], prop="bed", text="A stone bed under a thin quilt.", rest=True)
    r.decor("rug", [860, 800])
    r.decor("incense_burner", [760, 720])
    r.decor("scroll_rack", [1180, 690])
    r.decor("stone_lantern", [360, 700])
    r.decor("scholar_rock", [640, 690])
    r.decor("wine_jar", [1240, 760])
    r.obj("plot_" + rid, "treasure_plot", [380, 880], requires=all_of(unlock("natural_treasures")), locked_text="Rich dark earth, ringed with river stones.")
    r.portal("exit", "door", [120, 700], peak, "abode", press_up=True, label=ROOMS[peak].d["name"])
    return r


def valley():
    # Stonewall Quarry (BF4-7)
    r = field("sq_quarry_rim", "Quarry Rim", "stonewall_quarry", 2, [4, 6], "quarry", "rock",
              [("rock_beetle", 5, [4, 5]), ("pebble_imp", 3, [4, 6])], ores=("copper_ore", "copper_ore", "riverstone"), jars=5,
              element="earth", gather_tier="valley_low", music="field_earth", trees=("rock_large", "pine_tree"),
              platforms=[(700, 660, 260, 90), (1500, 680, 240, 120)], hazards=["falling_rocks"])
    r.npc("foreman_dong", [400, 780], oid="npc_dong_rim", facing=1)
    r.portal("south", "door", [160, 700], "sf_gate", "quarry_road", press_up=True, label="Stoneford Gate")
    r.edge("east", "east", "sq_lower_pit", "west", y=850)
    r = field("sq_lower_pit", "Lower Pit", "stonewall_quarry", 2, [5, 7], "quarry", "rock",
              [("stone_tortoise", 3, [5, 7]), ("ironclaw_mole", 4, [5, 7])], ores=("copper_ore", "jadeiron", "riverstone", "spirit_stone_shard"),
              jars=6, element="earth", gather_tier="valley_low", chest="chest_valley", music="field_earth", trees=("rock_large", "boulder_moss"),
              platforms=[(500, 660, 280, 90), (900, 640, 260, 180), (1400, 660, 300, 264), (1900, 680, 260, 120)])
    r.edge("west", "west", "sq_quarry_rim", "east", y=850)
    r.portal("tunnel", "hidden", [2380, 720], "sq_collapsed_tunnel", "entry", press_up=True, label="Collapsed Tunnel")
    r = field("sq_collapsed_tunnel", "Collapsed Tunnel", "stonewall_quarry", 1, [6, 7], "cave", "slate",
              [("ironclaw_mole", 2, [6, 7])], ores=("jadeiron", "spirit_stone_shard"), jars=4, rtype="secret", chest="chest_dungeon",
              music="dungeon", elite=True, trees=("rock_small",))
    r.obj("journal_tunnel", "pickup", [1100, 720], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_tunnel",
          hidden_if=all_of(flag("journal_tunnel")))
    r.portal("entry", "door", [140, 700], "sq_lower_pit", "tunnel", press_up=True)

    # Reed Marsh (BF4-QK1)
    r = field("rm_marsh_edge", "Marsh Edge", "reed_marsh", 2, [4, 6], "marsh", "moss",
              [("reed_frog", 5, [4, 6]), ("marsh_leech", 3, [5, 6])], herbs=("willow_moss", "willow_moss", "riverreed_ginseng_10"),
              jars=5, element="water", gather_tier="valley_low", music="marsh", ambience="marsh_ambience", trees=("reeds", "dead_tree_grey"),
              platforms=[(800, 700, 180, 70), (1500, 720, 180, 90)], fishing="marsh_edge")
    r.area("shallows", [400, 860, 1700, 100])
    r.spawn("reed_otter", [[1900, 900]], 1, respawn=600, level=[19, 19], wild_pet=True, requires=all_of(unlock("taming")))
    for i, x in enumerate([700, 1300, 2000]):
        r.obj("grey_patch_%d" % i, "inspect", [x, 910], prop="grey_patch", text="The reeds here are grey and brittle, as if the colour was drunk out of them.",
              set_flag="grey_patch_%d" % i, visible_if=all_of(qactive("strange_tracks")))
    r.edge("west", "west", "lf_reed_shallows", "east", y=820)
    r.edge("east", "east", "rm_grey_pools", "west", y=850)
    r = field("rm_grey_pools", "Grey Pools", "reed_marsh", 2, [7, 12], "marsh", "moss",
              [("greyfin", 4, [7, 11]), ("hollowed_boarlet", 4, [7, 12])], herbs=("willow_moss",), jars=5, element="hollow",
              gather_tier="valley_low", music="marsh_grey", ambience="marsh_ambience", trees=("dead_tree_grey", "reeds"), tint="#c9cfc9",
              hazards=["hollow_puddle"])
    for x, y in [(600, 900), (1200, 900), (1800, 900), (900, 770), (2150, 790)]:
        r.decor("hollow_puddle", [x, y])
        r.area("hollow_puddle", [x - 50, y - 18, 100, 30])
    r.edge("west", "west", "rm_marsh_edge", "east", y=850)
    r.edge("east", "east", "rm_sunken_causeway", "west", y=850)
    r.portal("hamlet", "door", [1280, 700], "gh_hamlet_square", "marsh", press_up=True, label="Greyreed Hamlet",
             requires=all_of(qdone("grey_roofs")), locked_text="Greyreed Hamlet. Grey, silent. Not yet.")
    r = field("rm_sunken_causeway", "Sunken Causeway", "reed_marsh", 2, [5, 12], "marsh", "wood",
              [("marsh_leech", 4, [5, 7]), ("greyfin", 2, [8, 11])], herbs=("riverreed_ginseng_10",), jars=3, rtype="path",
              element="water", music="marsh", ambience="marsh_ambience", trees=("reeds",), elite=False)
    r.area("river", [0, 900, 2560, 120])
    r.obj("sign_rm", "signpost", [2380, 860], text="East: Whispering Bamboo (Lv 10-15) · North: the hermit's stilt house.")
    r.edge("west", "west", "rm_grey_pools", "east", y=850)
    r.edge("east", "east", "bg_whispering_bamboo", "west", y=850, ptype="sealed", requires=all_of(realm("bone_forging_9")),
           locked_text="The bamboo is thick with vipers. Bone Forging 9 first.")
    r.portal("stilts", "door", [1280, 700], "rm_hermit_stilt_house", "stairs", press_up=True, label="Hermit's Stilt House")
    r = Room("rm_hermit_stilt_house", "Hermit's Stilt House", "rest", "reed_marsh", 1, backdrop="marsh", material="wood",
             music="meditation", ambience="marsh_ambience", qi=1.3, spawn_point=[300, 820], element="water")
    r.building("stilt_house", "stilt_house", 760, front=690)
    r.npc("hermit_yao", [500, 800], facing=1)
    r.obj("shrine_hermit", "shrine", [1100, 720])
    r.obj("spring_hermit", "qi_spring", [300, 900], spring=True, requires=all_of(unlock("qi_springs")), locked_text="Still water.")
    r.herb("riverreed_ginseng_10", [1000, 900])
    r.portal("stairs", "door", [140, 700], "rm_sunken_causeway", "stilts", press_up=True, label="Sunken Causeway")
    r.decor("reeds", [1200, 650])

    r = town("gh_hamlet_square", "Greyreed Hamlet", "greyreed_hamlet", 2, backdrop="marsh", material="earth", music="village_day")
    r.building("hamlet_house_a", "thatched_hut", 500, front=690)
    r.building("hamlet_house_b", "village_house", 1400, front=690)
    r.decor("well", [900, 700])
    r.obj("well_cleanse", "inspect", [900, 740], prop="none", text="The well water runs clear again.", set_flag="well_cleansed",
          visible_if=all_of(qactive("cleansing_the_well")))
    r.npc("hamlet_elder_gao", [1100, 800], facing=-1)
    r.npc("hamlet_trader_min", [2000, 800], facing=-1, visible_if=all_of(qdone("market_day")))
    r.portal("marsh", "gate", [40, 850], "rm_grey_pools", "hamlet", label="Grey Pools")
    r.obj("shrine_gh", "shrine", [1700, 700])

    # Bamboo Grove (QK1-QK5)
    r = field("bg_whispering_bamboo", "Whispering Bamboo", "bamboo_grove", 2, [10, 14], "bamboo", "moss",
              [("bamboo_monkey", 5, [10, 12]), ("green_viper", 3, [11, 14])], herbs=("ember_pepper", "ember_pepper", "willow_moss"),
              jars=6, element="wood", gather_tier="valley_mid", music="bamboo", ambience="bamboo_ambience", trees=("bamboo_cluster",),
              platforms=[(600, 700, 200, 110), (1100, 660, 200, 180), (1700, 700, 220, 110)], chest="chest_valley")
    r.spawn("ember_fox", [[2000, 880]], 1, respawn=600, level=[19, 19], wild_pet=True, requires=all_of(unlock("taming")))
    r.edge("west", "west", "rm_sunken_causeway", "east", y=850)
    r.edge("east", "east", "bg_thicket_heart", "west", y=850)
    r = field("bg_thicket_heart", "Thicket Heart", "bamboo_grove", 2, [12, 15], "bamboo", "moss",
              [("green_viper", 4, [12, 14]), ("thornback_boar", 1, [13, 15], 180)], herbs=("ember_pepper", "riverreed_ginseng_10"),
              jars=5, element="wood", gather_tier="valley_mid", music="bamboo", ambience="bamboo_ambience", trees=("bamboo_cluster", "boulder_moss"),
              chest="chest_valley", hazards=["thorns"])
    r.decor("beast_nest", [1500, 700])
    for x, y in [(760, 780), (1250, 900), (1900, 760), (2300, 880)]:
        r.decor("thorn_thicket", [x, y])
        r.area("thorns", [x - 62, y - 26, 124, 34])
    r.edge("west", "west", "bg_whispering_bamboo", "east", y=850)
    r.edge("east", "east", "cf_falls_pool", "west", y=850)

    # Crane Falls (insight site, secret, path to the Hidden Vale)
    r = Room("cf_falls_pool", "Falls Pool", "insight", "crane_falls", 2, backdrop="gorge", material="rock", music="meditation",
             ambience="waterfall_ambience", qi=1.8, element="water", spawn_point=[200, 820], gather_tier="valley_mid")
    r.area("water", [900, 860, 700, 100])
    r.decor("waterfall", [1250, 700], layer="back")
    r.obj("insight_falls", "insight_stone", [1000, 720], element="water", requires=all_of(unlock("insight_sites")),
          locked_text="The stone hums. You can't hear it yet.")
    r.obj("spring_falls", "qi_spring", [600, 900], spring=True, requires=all_of(unlock("qi_springs")), locked_text="Cold spray.")
    r.herb("mist_lotus", [1300, 900])
    r.obj("shrine_falls", "shrine", [1900, 700])
    r.spawn("jade_crane_chick", [[1700, 880]], 1, respawn=600, level=[19, 19], wild_pet=True, requires=all_of(unlock("taming")))
    r.edge("west", "west", "bg_thicket_heart", "east", y=850)
    r.edge("east", "east", "cp_pilgrim_stairs", "west", y=850, ptype="sealed", requires=all_of(realm("qi_kindling_9")),
           locked_text="The Pilgrim Stairs open to those preparing for Heaven's Cleansing (Qi Kindling 9).")
    r.portal("behind", "hidden", [1250, 870], "cf_behind_falls", "entry", press_up=True, label="Behind the Falls")
    r.portal("vale", "sealed", [2400, 700], "hv_vale_gate", "path", press_up=True, label="Hidden Vale",
             requires=all_of(unlock("your_sect")), locked_text="A path swallowed by mist. Someday.")
    r = Room("cf_behind_falls", "Behind the Falls", "secret", "crane_falls", 1, backdrop="cave", material="slate", music="dungeon",
             qi=2.2, element="water", spawn_point=[200, 820])
    r.obj("journal_falls", "pickup", [900, 740], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_falls",
          hidden_if=all_of(flag("journal_falls")))
    r.chest([1100, 720], loot="chest_dungeon", level=14)
    r.obj("spring_behind", "qi_spring", [640, 900], spring=True, requires=all_of(unlock("qi_springs")), locked_text="Cold spray.")
    r.obj("mindwell_lotus_cf", "herb_patch", [420, 900], item="mindwell_lotus", prop="mindwell_lotus_patch", **{"yield": [1, 1]},
          rank="apprentice", regrow_s=7 * 86400, requires=all_of(unlock("natural_treasures")),
          locked_text="A pale lotus. It closes when your hand comes near.")
    r.portal("entry", "door", [140, 700], "cf_falls_pool", "behind", press_up=True)

    # Caravan Road and Mudwater Hideout (QK6-QK8)
    r = field("cr_caravan_road", "Caravan Road", "caravan_road", 3, [14, 19], "valley_day", "earth",
              [("mudwater_bandit", 6, [14, 19])], herbs=("ember_pepper",), ores=("riverstone",), jars=4, rtype="path",
              music="field", trees=("pine_tree", "rock_large"), loot="jar_valley_mid")
    r.decor("cart_broken", [900, 720])
    r.decor("cart_broken", [2400, 740], flip=True)
    r.obj("sign_cr", "signpost", [3600, 860], text="Mudwater Hideout — turn back, traveller.")
    r.edge("east", "east", "sf_fairground", "west", y=850)
    r.edge("west", "west", "dw_bend_shore", "east", y=850, ptype="sealed", requires=all_of(realm("qi_kindling_7")),
           locked_text="Deepwater Bend lies beyond. Qi Kindling 7 first.")
    r.portal("hideout", "dungeon", [3000, 700], "mh_stockade", "west", press_up=True, label="Mudwater Hideout",
             requires=all_of({"kind": "item_owned", "item": "mudwater_key", "count": 1}), locked_text="A barred stockade gate. You need a key.")
    for rid, name, spawns, nxt, prev, extra in [
        ("mh_stockade", "Stockade", [("mudwater_bandit", 5, [15, 18]), ("mud_hound", 3, [16, 18])], "mh_tunnels", ("cr_caravan_road", "hideout"), {}),
        ("mh_tunnels", "Tunnels", [("bandit_archer", 4, [16, 19]), ("mud_hound", 3, [16, 20])], "mh_loot_cave", ("mh_stockade", "east"), {}),
        ("mh_loot_cave", "Loot Cave", [("mudwater_bandit", 4, [17, 19]), ("bandit_archer", 2, [17, 20])], "mh_boss_den", ("mh_tunnels", "east"), {}),
    ]:
        r = field(rid, name, "mudwater_hideout", 2, [14, 20], "cave" if rid != "mh_stockade" else "valley_dusk", "earth" if rid == "mh_stockade" else "slate",
                  spawns, ores=("riverstone",) if rid == "mh_tunnels" else (), jars=5, rtype="dungeon", chest="chest_dungeon",
                  music="dungeon", trees=("rock_small",), elite=False, loot="jar_valley_mid", dungeon_exit="cr_caravan_road", idle=[])
        r.edge("west", "west", prev[0], prev[1], y=850, ptype="gate" if rid == "mh_stockade" else "edge")
        r.edge("east", "east", nxt, "west", y=850)
        if rid == "mh_stockade":
            r.decor("stockade_wall", [640, 660])
            r.decor("stockade_wall", [1900, 660])
        if rid == "mh_tunnels":
            r.d["hazards"] = ["poison_mist"]
            for x, y in [(700, 800), (1350, 900), (1950, 770)]:
                r.decor("gas_vent", [x, y])
                r.area("poison_mist", [x - 90, y - 40, 180, 64])
    r = Room("mh_boss_den", "Boss Den", "boss_arena", "mudwater_hideout", 2, backdrop="cave", material="earth", music="boss",
             levels=[18, 18], safe=False, spawn_point=[200, 820], dungeon_exit="cr_caravan_road")
    r.spawn("big_toad_tan", [[1700, 840]], 1, respawn=86400, level=[18, 18], boss=True)
    for i, x in enumerate([1400, 2000, 2300]):
        r.obj("toad_wine_%d" % i, "wine_jar", [x, 720 if i % 2 else 900], loot="jar_valley_mid", hp=1, level=18, respawn_s=86400)
    r.chest([2400, 700], loot="chest_dungeon", level=20, requires=all_of({"kind": "quest_done", "quest": "mudwater_hideout"}),
            locked_text="Tan's strongbox. Defeat him first.")
    r.edge("west", "west", "mh_loot_cave", "east", y=850)
    r.portal("exit", "door", [2460, 860], "cr_caravan_road", "hideout", press_up=True, label="Caravan Road")

    # Cleansing Peak (QK9-QU1)
    r = field("cp_pilgrim_stairs", "Pilgrim Stairs", "cleansing_peak", 2, [17, 19], "mist_peak", "stone",
              [("stone_guardian", 4, [17, 19])], jars=3, rtype="path", music="field_mountain", trees=("pine_tree", "stone_lantern"),
              platforms=[(700, 680, 300, 80), (1300, 660, 300, 160), (1900, 680, 300, 240)], elite=False)
    r.obj("shrine_cp", "shrine", [300, 700])
    r.edge("west", "west", "cf_falls_pool", "east", y=850)
    r.edge("east", "east", "cp_cleansing_summit", "west", y=850)
    r = Room("cp_cleansing_summit", "Cleansing Summit", "event", "cleansing_peak", 1, backdrop="mist_peak", material="stone",
             music="meditation", qi=2.0, spawn_point=[200, 820])
    r.obj("rite_cleansing", "rite_circle", [640, 860], event="heavens_cleansing", requires=all_of(realm("qi_kindling_9"), qactive("the_rite")),
          locked_text="The rite circle waits for the Cleansing.")
    r.decor("pagoda", [1100, 660])
    r.decor("stone_lantern", [400, 660])
    r.decor("stone_lantern", [880, 660])
    r.edge("west", "west", "cp_pilgrim_stairs", "east", y=850)

    # Deepwater Bend and the Drowned Shrine (QU1-QU9)
    r = field("dw_bend_shore", "Bend Shore", "deepwater_bend", 2, [19, 23], "valley_day", "moss",
              [("jade_carp", 4, [19, 22]), ("tide_crab", 4, [20, 23])], herbs=("riverreed_ginseng_10", "mist_lotus"), jars=5,
              element="water", gather_tier="valley_mid", music="river", ambience="river_ambience", fishing="bend_shore", loot="jar_valley_mid")
    r.area("shallows", [600, 870, 1400, 90])
    r.edge("east", "east", "cr_caravan_road", "west", y=850)
    r.edge("west", "west", "wg_gorge_mouth", "east", y=850, ptype="sealed", requires=all_of(realm("heart_tempering_1")),
           locked_text="Whitewater Gorge. The rapids would break you before Heart Tempering.")
    r.portal("shallows", "door", [1280, 700], "dw_serpents_shallows", "shore", press_up=True, label="Serpent's Shallows")
    r.portal("shrine", "dungeon", [2200, 700], "ds_flooded_gate", "west", press_up=True, label="Drowned Shrine",
             requires=all_of(realm("qi_unfurling_3")), locked_text="The shrine roof lies under the water. It will surface at Qi Unfurling 3.")
    r = Room("dw_serpents_shallows", "Serpent's Shallows", "boss_arena", "deepwater_bend", 3, backdrop="valley_day", material="moss",
             music="boss", levels=[25, 25], safe=False, spawn_point=[200, 820], element="water")
    r.area("shallows", [400, 820, 3000, 140])
    for i, x in enumerate([900, 1700, 2500]):
        r.surface("high_rock_%d" % i, [x, 700, 180, 60], 100, kind="rock_ledge")
    r.spawn("riverbed_serpent", [[1900, 900]], 1, respawn=2700, level=[25, 25], field_boss=True, boss=True)
    r.portal("shore", "door", [140, 700], "dw_bend_shore", "shallows", press_up=True, label="Bend Shore")
    r.edge("east", "east", "dw_bend_shore", "shallows", y=850)
    for rid, name, spawns, nxt, prev in [
        ("ds_flooded_gate", "Flooded Gate", [("drowned_acolyte", 4, [21, 23])], "ds_hall_of_lanterns", ("dw_bend_shore", "shrine")),
        ("ds_hall_of_lanterns", "Hall of Lanterns", [("drowned_acolyte", 3, [22, 24]), ("paper_talisman_ghost", 3, [22, 25])], "ds_scripture_well", ("ds_flooded_gate", "east")),
        ("ds_scripture_well", "Scripture Well", [("paper_talisman_ghost", 4, [23, 26])], "ds_abbots_sanctum", ("ds_hall_of_lanterns", "east")),
    ]:
        r = field(rid, name, "drowned_shrine", 2, [21, 27], "cave", "floor_stone", spawns, jars=5, rtype="secret", chest="chest_dungeon",
                  music="dungeon", trees=("stone_lantern",), loot="jar_valley_mid", dungeon_exit="dw_bend_shore", elite=False, idle=[])
        r.area("shallows", [0, 900, r.w, 60])
        r.edge("west", "west", prev[0], prev[1], y=850, ptype="gate" if rid == "ds_flooded_gate" else "edge")
        r.edge("east", "east", nxt, "west", y=850)
        if rid == "ds_scripture_well":
            # Lu's inheritance trial (chapter 5): hold the well while the drowned rise.
            r.obj("rite_riverbreath", "rite_circle", [1300, 880], event="riverbreath_trial",
                  visible_if=all_of(qactive("the_riverbreath_trial")),
                  text="A ring of worn river stones around the well. Lu's words: \"Breathe with the river.\"")
        for i in range(4 if rid == "ds_hall_of_lanterns" else 1):
            r.obj("inscription_%s_%d" % (rid, i), "inspect", [500 + i * 450, 700], prop="scholar_rock",
                  text="Lu's handwriting, faded under the silt: \"Breathe with the river, not against it.\"",
                  set_flag="inscription_%s_%d" % (rid, i), visible_if=all_of(qactive("lus_handwriting")))
    r = Room("ds_abbots_sanctum", "Abbot's Sanctum", "boss_arena", "drowned_shrine", 2, backdrop="cave", material="floor_stone",
             music="boss", levels=[27, 27], safe=False, spawn_point=[200, 820], dungeon_exit="dw_bend_shore")
    r.spawn("drowned_abbot", [[1700, 840]], 1, respawn=86400, level=[27, 27], boss=True)
    for i, x in enumerate([500, 1100, 1700, 2300]):
        r.obj("small_bell_%d" % i, "bell", [x, 700])
    r.obj("vault", "chest", [2400, 700], loot="chest_dungeon", level=27, requires=all_of(realm("spirit_awakening_3")),
          locked_text="A sealed vault. Its seal answers only a Spirit Awakening soul.", vault=True)
    r.obj("journal_vault", "pickup", [2300, 900], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_vault",
          visible_if=all_of(realm("spirit_awakening_3")), hidden_if=all_of(flag("journal_vault")))
    # The Sleeping Blade rests on the Abbot's altar until a soul strong enough to bind it arrives (SA3).
    r.obj("sleeping_blade_altar", "pickup", [1900, 720], item="sleeping_blade", count=1, prop="altar", set_flag="blade_bound",
          visible_if=all_of({"kind": "unlock", "system": "binding"}, qactive("the_sleeping_blade")), hidden_if=all_of(flag("blade_bound")))
    r.edge("west", "west", "ds_scripture_well", "east", y=850)
    r.portal("exit", "door", [2460, 860], "dw_bend_shore", "shrine", press_up=True, label="Bend Shore")

    # Whitewater Gorge (HT1-HT9)
    r = field("wg_gorge_mouth", "Gorge Mouth", "whitewater_gorge", 2, [28, 31], "gorge", "rock",
              [("gorge_bandit_adept", 4, [29, 31])], herbs=("mist_lotus",), ores=("jadeiron",), jars=3, rtype="path",
              music="field_mountain", ambience="waterfall_ambience", trees=("pine_tree", "rock_large"), elite=False, loot="jar_valley_mid")
    r.obj("shrine_wg", "shrine", [400, 700])
    r.edge("east", "east", "dw_bend_shore", "west", y=850)
    r.edge("west", "west", "wg_rapids_terraces", "east", y=850)
    r = field("wg_rapids_terraces", "Rapids Terraces", "whitewater_gorge", 3, [28, 33], "gorge", "rock",
              [("rapids_lizard", 5, [28, 31]), ("gorge_bandit_adept", 3, [29, 33])], herbs=("mist_lotus", "mist_lotus"),
              ores=("jadeiron", "spirit_stone_shard"), jars=6, element="water", music="field_mountain", ambience="waterfall_ambience",
              trees=("pine_tree",), fishing="rapids", platforms=[(800, 680, 300, 80), (1800, 680, 300, 150), (2800, 680, 300, 80)],
              hazards=["current"], loot="jar_valley_mid")
    r.area("shallows", [600, 880, 2600, 80], current=-60)
    r.edge("east", "east", "wg_gorge_mouth", "west", y=850)
    r.edge("west", "west", "wg_echo_cliffs", "east", y=850)
    r.portal("cave", "hidden", [1900, 700], "wg_waterfall_cave", "entry", press_up=True, label="Waterfall Cave")
    r = field("wg_echo_cliffs", "Echo Cliffs", "whitewater_gorge", 2, [32, 36], "gorge", "rock",
              [("boulder_serpent", 4, [32, 35]), ("mist_vulture", 3, [34, 36])], ores=("jadeiron", "jadeiron"), jars=4,
              music="field_mountain", trees=("pine_tree", "cliff_face"),
              platforms=[(400, 680, 360, 100), (900, 650, 360, 200), (1500, 640, 360, 300), (2000, 660, 320, 200)], loot="jar_valley_mid")
    r.edge("east", "east", "wg_rapids_terraces", "west", y=850)
    r.edge("west", "west", "cc_cliff_faces", "east", y=850, ptype="sealed", requires=all_of(realm("cloud_stride_1")),
           locked_text="Crane Cliffs need wings. Cloud Stride first.")
    r = Room("wg_waterfall_cave", "Waterfall Cave", "secret", "whitewater_gorge", 1, backdrop="cave", material="slate", music="dungeon",
             qi=2.2, spawn_point=[200, 820])
    r.obj("journal_cave", "pickup", [900, 740], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_cave",
          hidden_if=all_of(flag("journal_cave")))
    r.chest([1100, 720], loot="chest_dungeon", level=33)
    r.portal("entry", "door", [140, 700], "wg_rapids_terraces", "cave", press_up=True)

    # Crane Cliffs (CS1-CS9)
    r = field("cc_cliff_faces", "Cliff Faces", "crane_cliffs", 3, [37, 43], "mist_peak", "rock",
              [("cloudwing_crane", 5, [37, 40]), ("stormwing_hawk", 3, [38, 43])], herbs=("cloudtop_orchid",), ores=("cloudsteel_ore",),
              jars=4, element="wind", music="field_mountain", ambience="wind_ambience", trees=("pine_tree", "cliff_face"),
              platforms=[(600, 660, 280, 180), (1300, 640, 280, 300), (2100, 650, 280, 240), (2900, 660, 280, 160)], loot="jar_valley_mid")
    r.edge("east", "east", "wg_echo_cliffs", "west", y=850)
    r.edge("west", "west", "cc_sky_ledges", "east", y=850)
    r = field("cc_sky_ledges", "Sky Ledges", "crane_cliffs", 2, [40, 45], "mist_peak", "rock",
              [("stormwing_hawk", 3, [40, 43]), ("cliff_ape", 4, [41, 45])], herbs=("cloudtop_orchid", "cloudtop_orchid"), ores=("cloudsteel_ore",),
              jars=4, element="wind", music="field_mountain", ambience="wind_ambience", trees=("pine_tree",),
              platforms=[(500, 650, 300, 260), (1200, 640, 300, 360), (1900, 650, 300, 260)], loot="jar_valley_mid")
    r.edge("east", "east", "cc_cliff_faces", "west", y=850)
    r.edge("west", "west", "mp_misty_slopes", "east", y=850, ptype="sealed", requires=all_of(realm("spirit_awakening_1")),
           locked_text="Mist Peak is thick with soul-mist. Spirit Awakening first.")

    # Mist Peak and Summit Ridge (SA1-HG3)
    r = field("mp_misty_slopes", "Misty Slopes", "mist_peak", 3, [46, 51], "mist_peak", "rock",
              [("mist_wolf", 5, [46, 50]), ("mirror_wisp", 3, [47, 51])], herbs=("soulbell_flower",), ores=("mystic_ore",), jars=5,
              element="soul", music="mist", ambience="wind_ambience", trees=("pine_tree", "dead_tree_grey"), hazards=["fog"], loot="jar_valley_mid")
    r.decor("mist_bank", [800, 990], layer="front")
    r.decor("mist_bank", [2200, 990], layer="front")
    r.obj("insight_mist", "insight_stone", [1900, 720], element="soul", requires=all_of(unlock("insight_sites")), locked_text="A carved stone.")
    r.edge("east", "east", "cc_sky_ledges", "west", y=850)
    r.edge("west", "west", "mp_forgotten_monastery", "east", y=850)
    r = field("mp_forgotten_monastery", "Forgotten Monastery", "mist_peak", 3, [50, 56], "mist_peak", "floor_stone",
              [("weeping_lantern", 4, [50, 55]), ("jade_sentinel", 3, [52, 56])], herbs=("soulbell_flower",), ores=("mystic_ore",),
              jars=6, element="soul", music="mist", trees=("stone_lantern", "pine_tree"), chest="chest_dungeon", loot="jar_valley_mid")
    r.painted("monastery_hall", "hall", 1900, 700, 140, 120, front=690)
    for i, x in enumerate([700, 2800]):
        r.decor("formation_node", [x, 760])
    r.obj("heaven_insight", "insight_stone", [1200, 720], element="heaven", requires=all_of(realm("heaven_glimpse_1")),
          locked_text="The sky above this stone looks too close.")
    r.obj("nine_bough_tree", "treasure_tree", [2580, 690], treasure="nine_bough_jade_tree", radius=150,
          requires=all_of(unlock("natural_treasures")), locked_text="An ancient tree with jade leaves. It does not notice you yet.")
    r.edge("east", "east", "mp_misty_slopes", "west", y=850)
    r.edge("west", "west", "sr_windswept_ridge", "east", y=850, ptype="sealed", requires=all_of(realm("heaven_glimpse_1")),
           locked_text="The ridge winds would tear a soul loose. Heaven Glimpse first.")
    r = field("sr_windswept_ridge", "Windswept Ridge", "summit_ridge", 3, [55, 60], "mist_peak", "snow",
              [("hollow_stag", 5, [55, 59]), ("cloudpeak_roc", 3, [58, 63])], ores=("mystic_ore", "mystic_ore"), jars=4,
              element="wind", music="summit", ambience="wind_ambience", trees=("dead_tree_grey", "rock_large"), hazards=["wind_gust"],
              platforms=[(900, 660, 300, 160), (2000, 650, 300, 220)], loot="jar_valley_mid")
    r.edge("east", "east", "mp_forgotten_monastery", "west", y=850)
    r.edge("west", "west", "sr_frozen_shrine", "east", y=850)
    r = field("sr_frozen_shrine", "Frozen Shrine", "summit_ridge", 2, [58, 63], "mist_peak", "snow",
              [("cloudpeak_roc", 4, [58, 63])], ores=("mystic_ore",), jars=4, element="wind", music="summit", ambience="wind_ambience",
              trees=("pine_tree",), loot="jar_valley_mid")
    r.obj("shrine_frozen", "shrine", [2300, 700])
    r.obj("exchange_summit", "inspect", [1400, 720], prop="altar", text="An old moneychanger's altar.", open_page="exchange",
          requires=all_of(unlock("currency_exchange")), locked_text="The altar is cold.")
    r.obj("journal_frozen", "pickup", [1800, 900], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_frozen",
          hidden_if=all_of(flag("journal_frozen")))
    r.edge("east", "east", "sr_windswept_ridge", "west", y=850)
    r.edge("west", "west", "mp_ascension_gate", "east", y=850)
    r = Room("mp_ascension_gate", "Ascension Gate", "boss_arena", "mist_peak", 3, backdrop="mist_peak", material="floor_stone",
             music="boss", levels=[63, 63], safe=False, spawn_point=[3600, 820])
    r.painted("ascension_arch", "gate", 1900, 700, 140, 220, front=690)
    r.spawn("gate_guardian", [[1900, 840]], 1, respawn=86400, level=[63, 63], boss=True, requires=all_of(qactive("the_ascension_gate")))
    r.edge("east", "east", "sr_frozen_shrine", "west", y=850)
    r.portal("ascend", "gate", [1900, 710], "ae_landing", "gate", press_up=True, label="Azure Expanse",
             requires=all_of(qdone("the_ascension_gate")), locked_text="The Gate Guardian bars the way.")

    # Story instances
    r = Room("si_trial_of_reflections", "Trial of Reflections", "story", "story", 1, backdrop="mist_peak", material="floor_stone",
             music="boss", instanced=True, safe=False, spawn_point=[240, 820], dungeon_exit="",
             event={"id": "trial_of_reflections", "duration": 600, "fixed_spawns": [{"enemy": "the_reflection", "at": [1000, 840]}],
                    "heart_demons": "heart_demon",
                    "win_on_kill": "the_reflection", "on_complete": [{"kind": "event_passed", "event": "heart_trial"}, {"kind": "add_heart_demon", "amount": -30}],
                    "on_timeout": [{"kind": "teleport", "target": "ja_elder_hu_peak", "portal": ""}]})
    r.portal("exit", "door", [140, 700], "ja_elder_hu_peak", "path", press_up=True, label="Leave",
             requires=all_of({"kind": "event_passed", "event": "heart_trial"}), locked_text="The mirror holds you until one of you breaks.")
    r = Room("si_gus_warehouse", "Gu's Warehouse", "story", "story", 2, backdrop="interior", material="wood", music="boss",
             instanced=True, safe=False, spawn_point=[200, 820], wall={"top": 150, "bottom": 650, "tile": "wall_wood"})
    r.spawn("mudwater_bandit", [[900, 820], [1200, 900], [1500, 760]], 3, respawn=99999, level=[50, 52])
    r.spawn("elder_gu", [[2100, 840]], 1, respawn=99999, level=[53, 53], boss=True)
    for x in [500, 800, 1700]:
        r.decor("sack_pile", [x, 700])
    r.decor("barrel", [1100, 700])
    r.portal("entry", "door", [140, 700], "sf_artisan_row", "warehouse_door", press_up=True, label="Artisan Row")
    r = Room("si_siege", "Siege of Two Sects", "story", "story", 3, backdrop="valley_dusk", material="stone", music="boss",
             instanced=True, safe=False, spawn_point=[400, 820],
             event={"id": "siege_of_two_sects", "duration": 240, "wave": {"enemy": "hollowed_boarlet", "every_s": 3, "max": 8,
                    "points": [[2600, 800], [3000, 900], [3400, 760]]}, "fixed_spawns": [{"enemy": "hollow_behemoth", "at": [3200, 840]}],
                    "on_complete": [{"kind": "event_passed", "event": "siege_of_two_sects"}]})
    r.decor("banner_jade", [300, 660])
    r.decor("banner_cloud", [600, 660])
    r.decor("stockade_wall", [900, 660])
    r.portal("exit", "door", [140, 700], "ja_gate_street", "stoneford", press_up=True, label="Leave",
             requires=all_of({"kind": "event_passed", "event": "siege_of_two_sects"}), locked_text="Hold the wall!")

    # Hidden Vale (your sect)
    r = town("hv_vale_gate", "Vale Gate", "hidden_vale", 1, backdrop="sect_jade", material="stone", music="sect")
    r.decor("paifang_gate", [640, 650])
    r.obj("stone_hv", "teleport_stone", [300, 880], stone="hidden_vale")
    r.obj("defence_hv", "inspect", [1000, 880], prop="rite_circle", text="The defence circle.", open_page="your_sect")
    r.portal("path", "gate", [40, 850], "cf_falls_pool", "vale", label="Falls Pool")
    r.edge("east", "east", "hv_sect_grounds", "west", y=850)
    r = town("hv_sect_grounds", "Sect Grounds", "hidden_vale", 2, backdrop="sect_jade", material="stone", music="sect")
    r.obj("sect_hall", "inspect", [1280, 720], prop="altar", text="Your sect's hall.", open_page="your_sect")
    # Buildings appear as they are built (S25). Each is a back-row prop that opens the sect page.
    built = lambda b: all_of({"kind": "sect_building_at_least", "building": b, "value": 1})
    for oid, bid, prop, x in [("hall_pagoda", "sect_hall", "pagoda", 1280), ("hall_gate", "sect_hall", "paifang_gate", 300),
                              ("treasury_hv", "treasury", "warehouse", 640), ("pavilion_hv", "meditation_pavilion", "stilt_house", 1720),
                              ("guest_house_hv", "guest_house", "village_house", 2140), ("mission_hall_hv", "mission_hall", "village_store", 960),
                              ("alchemy_hall_hv", "alchemy_hall", "herb_hut", 2420), ("library_hv", "library", "bookcase", 1540),
                              ("forge_hv", "forge", "weapon_rack_full", 1060), ("beast_pavilion_hv", "beast_pavilion", "thatched_hut", 180)]:
        r.obj(oid, "inspect", [x, 640], prop=prop, visible_if=built(bid), open_page="your_sect", z_back=False,
              text="Your sect's %s." % bid.replace("_", " "))
    for i, x in enumerate([1180, 1380]):
        r.obj("array_node_%d" % i, "inspect", [x, 900], prop="formation_node", visible_if=built("formation_array"),
              text="A node of the sect's Formation Array.")
    r.decor("banner_jade", [820, 660])
    r.decor("stone_lantern", [1120, 700])
    r.decor("stone_lantern", [1440, 700])
    r.obj("storage_hv", "storage_chest", [700, 720])
    r.obj("shrine_hv", "shrine", [1900, 700])
    r.obj("defence_bell", "defence_drum", [2400, 720], text="The alarm bell. Ring it when raiders come.")
    r.edge("west", "west", "hv_vale_gate", "east", y=850)
    r.edge("east", "east", "hv_back_mountain", "west", y=850, ptype="sealed", requires=all_of({"kind": "sect_level", "level": 4}),
           locked_text="The Back Mountain opens at sect level 4.")
    r = Room("hv_back_mountain", "Back Mountain", "sect", "hidden_vale", 2, backdrop="mist_peak", material="moss", music="meditation",
             qi=2.0, spawn_point=[200, 820], gather_tier="valley_mid")
    r.herb("mist_lotus", [800, 900])
    r.herb("cloudtop_orchid", [1500, 700])
    r.ore("spirit_stone_shard", [2100, 690])
    r.obj("spring_hv", "qi_spring", [1200, 900], spring=True)
    r.obj("plot_hv", "treasure_plot", [1750, 900], requires=all_of(unlock("natural_treasures")), locked_text="Rich dark earth, ringed with river stones.")
    # A quiet retreat above the grounds: old pines, a pagoda, a waterfall and mats by the spring.
    back_trees(r, props=("pine_tree", "plum_tree", "pine_tree"), step=460, skip=((1000, 1500),))
    r.decor("pagoda", [1900, 640], layer="back")
    r.decor("waterfall", [2400, 640], layer="back")
    r.decor("shrine", [620, 660])
    r.decor("scholar_rock", [980, 700])
    r.decor("incense_burner", [1320, 760])
    for x in (1060, 1340):
        r.decor("meditation_mat", [x, 880])
    lantern_row(r, [420, 1500, 2150], y=670)
    r.decor("boulder_moss", [300, 960], layer="front")
    front_grass(r, props=("tall_grass", "flowers_wild"), step=380)
    r.edge("west", "west", "hv_sect_grounds", "east", y=850)



# ---------------------------------------------------------------------------------------------
# Act II · The Azure Expanse (v1.1, docs/act2_design.md). Phase A: Cloudgate Port and the
# Thunderhorn Plains. Every room here is in zone azure_expanse; plains rooms ask for Storm Ward.
AE = {"zone": "azure_expanse"}


def plains_scenery(r, stones=3, yurts=0):
    """Open grass, wind-bent pines and lightning-split menhirs; herders' yurts near the camp."""
    back_trees(r, ("pine_tree", "storm_menhir", "pine_tree"), step=620)
    for i in range(stones):
        x = int(r.w * (i + 0.6) / max(1, stones)) + r.rng.randint(-120, 120)
        r.decor("storm_menhir", [x, 652], layer="back", flip=bool(i % 2))
    for i in range(yurts):
        r.decor("herder_yurt", [420 + i * 700, 668], layer="back", flip=bool(i % 2))
    front_grass(r, props=("tall_grass", "tall_grass", "rock_small"), step=260)


def azure_expanse():
    # --- Cloudgate Port: a sky harbour on a floating island, the Alliance's door into the Expanse
    r = town("ae_landing", "Arrival Terrace", "cloudgate_port", 2, backdrop="sky_port", material="stone", tint="#dfe6ee",
             music="sky_port", ambience="wind_ambience", spawn_point=[560, 820], qi=1.3, **AE)
    r.decor("paifang_gate", [300, 650])
    r.portal("gate", "gate", [300, 710], "mp_ascension_gate", "ascend", press_up=True, label="Ascension Gate")
    r.decor("portal_swirl", [300, 700])
    r.decor("banner_alliance", [620, 662])
    r.decor("banner_alliance", [1960, 662], flip=True)
    r.decor("statue_guardian_lion", [820, 690])
    r.decor("statue_guardian_lion", [1760, 690], flip=True)
    lantern_row(r, [1040, 1540, 2240], y=670)
    r.obj("shrine_ae_landing", "shrine", [1300, 700])
    r.obj("sign_ae_landing", "signpost", [2380, 860], text="Cloudgate Port. East: Port Market · West: the Skydock · The gate behind you leads home to the valley.")
    r.npc("warden_cao", [960, 780], facing=-1)
    r.npc("alliance_guard", [1700, 900], facing=-1)
    r.npc("wanderer_jiang", [2100, 760], facing=-1)
    r.edge("east", "east", "ae_port_market", "west", y=850)
    r.edge("west", "west", "ae_skydock", "east", y=850)

    r = town("ae_port_market", "Port Market", "cloudgate_port", 3, backdrop="sky_port", material="stone", tint="#dfe6ee",
             music="sky_port", spawn_point=[300, 820], qi=1.3, idle=["gather"], **AE)
    r.building("factors_hall", "village_store", 560, front=690)
    r.building("wayfarers_inn", "village_house", 1480, front=690, door_dx=40,
               door=("ae_wayfarers_inn", "entry", "inn_door", {"label": "Wayfarers' Inn"}))
    r.building("port_warehouse", "warehouse", 3280, front=690)
    for x, flip in ((980, False), (2240, True), (2700, False)):
        r.decor("market_stall", [x, 780], flip=flip)
    r.decor("lantern_string", [1000, 560], layer="back")
    r.decor("lantern_string", [2400, 560], layer="back")
    r.decor("banner_alliance", [300, 662])
    r.decor("sack_pile", [3000, 720])
    r.decor("barrel", [3080, 740])
    r.obj("stone_cloudgate", "teleport_stone", [1900, 880], stone="cloudgate")
    r.obj("board_ae", "notice_board", [760, 700])
    r.obj("storage_ae", "storage_chest", [1200, 710], requires=all_of(unlock("storage")), locked_text="The storehouse is locked.")
    r.obj("exchange_ae", "inspect", [2000, 720], prop="counter", text="The Alliance exchange: taels for Spirit Stones, at the Alliance's rate.",
          open_page="exchange", requires=all_of(unlock("currency_exchange")), locked_text="The exchange clerk ignores you.")
    r.npc("factor_ruan", [560, 730], facing=1)
    r.npc("peddler_gou", [980, 830], facing=1)
    r.npc("smith_hong", [2240, 830], facing=-1)
    r.npc("apothecary_wu", [2700, 830], facing=1)
    r.npc("sky_sailor_pei", [3500, 900], facing=-1)
    r.obj("sign_ae_market", "signpost", [3700, 860], text="East: the Thunderhorn Plains (Lv 64-69, Storm Ward 6-12) · West: Arrival Terrace.")
    r.edge("west", "west", "ae_landing", "east", y=850)
    r.edge("east", "east", "tp_stormgrass_verge", "west", y=850, ptype="sealed",
           requires=any_of(qactive("storm_in_the_blood"), qdone("storm_in_the_blood")),
           locked_text="A gate guard: \"Valley-soft blood won't last out there. Ask at the inn about the storms first.\"")

    r = interior("ae_wayfarers_inn", "Wayfarers' Inn", "cloudgate_port", wall="wall_wood", music="sky_port", qi=1.3,
                 rtype="rest", **AE)
    for x in (300, 700, 1000):
        r.decor("table", [x, 760])
        r.decor("cushion", [x - 50, 790])
    r.decor("wine_jar", [140, 700])
    r.decor("wine_jar", [1180, 700])
    r.decor("counter", [520, 700])
    r.decor("screen_folding", [860, 690])
    r.npc("innkeeper_tang", [520, 730], facing=1)
    r.npc("broker_mu", [960, 800], facing=-1)
    r.portal("entry", "door", [120, 700], "ae_port_market", "inn_door", press_up=True, label="Port Market")

    r = town("ae_skydock", "Skydock", "cloudgate_port", 2, backdrop="sky_port", material="wood", music="sky_port",
             ambience="wind_ambience", spawn_point=[2300, 820], qi=1.3, **AE)
    r.decor("sky_ship", [700, 660], layer="back")
    r.decor("sky_ship", [1700, 640], layer="back", flip=True)
    for x in (420, 1000, 1500, 2000):
        r.decor("mooring_post", [x, 700])
    r.decor("crate", [1180, 720])
    r.decor("sack_pile", [1260, 730])
    r.painted("condensing_hall", "hall", 2080, 520, 120, 120, front=690)
    r.portal("hall_door", "door", [2080, 704], "ae_condensing_hall", "entry", press_up=True, label="Condensing Hall")
    r.portal("lake_ferry", "door", [700, 704], "ml_reedless_shore", "ferry", press_up=True, label="Sky-ship to Mirrorwater Lake",
             requires=any_of(qactive("the_mirror_remembers"), qdone("the_mirror_remembers")),
             locked_text="Dockmaster Fu: \"The lake ferry sails for those with business there. Alliance rules.\"")
    r.portal("peaks_ferry", "door", [1700, 704], "np_alliance_gate", "ferry", press_up=True, label="Sky-ship to Nine Peaks",
             requires=all_of(qdone("the_mirror_remembers")),
             locked_text="Dockmaster Fu: \"Nine Peaks ships carry Alliance guests only. You'll be invited soon enough.\"")
    r.npc("dockmaster_fu", [1100, 780], facing=1)
    r.npc("sky_sailor_ning", [600, 900], facing=1)
    r.edge("east", "east", "ae_landing", "west", y=850)
    r.edge("west", "west", "ae_shipyard", "east", y=850)

    r = interior("ae_condensing_hall", "Condensing Hall", "cloudgate_port", wall="wall_stone", floor="floor_stone",
                 music="meditation", qi=2.0, rtype="insight", **AE)
    r.decor("incense_burner", [640, 760])
    for x in (420, 860):
        r.decor("meditation_mat", [x, 860])
    r.decor("herb_drawers", [1100, 690])
    r.decor("scroll_rack", [200, 690])
    r.obj("furnace_ae", "alchemy_furnace", [980, 760], requires=all_of(unlock("alchemy")), locked_text="Alchemist Fen's furnace.")
    r.npc("alchemist_fen", [760, 760], facing=-1)
    r.portal("entry", "door", [120, 700], "ae_skydock", "hall_door", press_up=True, label="Skydock")

    # --- Thunderhorn Plains: open storm grass, herds of rhinos and weasels that spit lightning
    plains = dict(backdrop="storm_plains", material="moss", tint="#c8d6d0", music="storm_plains", ambience="wind_ambience", element="thunder",
                  gather_tier="expanse_low", qi=1.4, loot="jar_expanse", trees=("pine_tree", "storm_menhir"), **AE)
    r = field("tp_stormgrass_verge", "Stormgrass Verge", "thunderhorn_plains", 3, [64, 66],
              spawns=[("spark_weasel", 5, [64, 66])], ores=("stormsteel_ore",), jars=4, attunement_required=6,
              hazards=["lightning"], **plains)
    plains_scenery(r, stones=2)
    r.obj("sign_tp_verge", "signpost", [200, 860], text="Thunderhorn Plains. West: Cloudgate Port · East: the Herders' Camp.")
    r.edge("west", "west", "ae_port_market", "east", y=850)
    r.edge("east", "east", "tp_herders_camp", "west", y=850)

    r = Room("tp_herders_camp", "Herders' Camp", "rest", "thunderhorn_plains", 2, backdrop="storm_plains", material="moss", tint="#c8d6d0",
             music="storm_plains", ambience="wind_ambience", element="thunder", qi=1.5, spawn_point=[400, 820],
             idle=["gather"], **AE)
    plains_scenery(r, stones=1, yurts=3)
    r.decor("fence_wood", [1200, 700])
    r.decor("hay_bale", [1400, 720])
    r.decor("cooking_pot", [1680, 800])
    r.decor("drying_rack_fish", [1900, 700])
    r.obj("shrine_tp_camp", "shrine", [900, 700])
    r.npc("herder_suo", [1600, 780], facing=-1)
    r.npc("herder_a_lan", [2000, 900], facing=-1)
    r.edge("west", "west", "tp_stormgrass_verge", "east", y=850)
    r.edge("east", "east", "tp_thunderhorn_flats", "west", y=850)

    r = field("tp_thunderhorn_flats", "Thunderhorn Flats", "thunderhorn_plains", 3, [65, 68],
              spawns=[("thunderhorn_rhino", 3, [65, 68], 16), ("spark_weasel", 3, [64, 66])], ores=("stormsteel_ore",), jars=4,
              attunement_required=10, hazards=["lightning"], **plains)
    plains_scenery(r, stones=3)
    r.edge("west", "west", "tp_herders_camp", "east", y=850)
    r.edge("east", "east", "tp_lightning_scar", "west", y=850)

    r = field("tp_lightning_scar", "Lightning Scar", "thunderhorn_plains", 3, [67, 69],
              spawns=[("thunderhorn_rhino", 4, [67, 69], 16), ("spark_weasel", 2, [66, 67])], ores=("stormsteel_ore", "stormsteel_ore"),
              jars=5, chest="chest_expanse", attunement_required=12, hazards=["lightning"], **plains)
    plains_scenery(r, stones=5)
    for i, x in enumerate((700, 1500, 2600)):
        r.obj("grey_tracks_%d" % i, "inspect", [x, 880], prop="grey_patch", text="Footprints in the scorched grass. Where each one falls, the colour has drained away.",
              visible_if=all_of(qactive("shards_for_sale")))
    r.obj("insight_thunder", "insight_stone", [1900, 720], element="thunder", requires=all_of(unlock("insight_sites")),
          locked_text="A glassy stone, fused by lightning.")
    r.edge("west", "west", "tp_thunderhorn_flats", "east", y=850)
    r.edge("east", "east", "rf_frostpine_climb", "west", y=850, ptype="sealed", requires=all_of(realm("sage_1")),
           locked_text="Rimefrost's cold stops any heart that has not reached Sage.")


def rimefrost_and_mirrorwater():
    """Phase B: Rimefrost Heights (Storm Ward 20) and Mirrorwater Lake (25), chapter 12."""
    heights = dict(backdrop="rimefrost", material="snow", music="summit", ambience="wind_ambience", element="water",
                   gather_tier="expanse_mid", qi=1.6, loot="jar_expanse", trees=("pine_tree", "icicle_rock"), hazards=["cold"], **AE)
    r = field("rf_frostpine_climb", "Frostpine Climb", "rimefrost_heights", 3, [67, 70],
              spawns=[("frost_lynx", 5, [67, 70])], herbs=("frost_lotus",), ores=("stormsteel_ore",), jars=4, attunement_required=16,
              platforms=[(700, 660, 300, 160), (1700, 650, 300, 240)], **heights)
    r.obj("sign_rf", "signpost", [200, 860], text="Rimefrost Heights. West: the Lightning Scar · East: the Snow Ape Ledges.")
    r.npc("grey_pilgrim", [2600, 760], facing=-1, visible_if=all_of(qactive("shards_for_sale")))
    r.edge("west", "west", "tp_lightning_scar", "east", y=850)
    r.edge("east", "east", "rf_snow_ape_ledges", "west", y=850)

    r = field("rf_snow_ape_ledges", "Snow Ape Ledges", "rimefrost_heights", 3, [68, 72],
              spawns=[("snow_ape", 4, [68, 72], 16), ("frost_lynx", 2, [68, 70])], herbs=("frost_lotus",), ores=("stormsteel_ore",),
              jars=4, attunement_required=20, platforms=[(900, 650, 300, 220), (2100, 660, 300, 180)], **heights)
    for x in (600, 1500, 3000):
        r.decor("icicle_rock", [x, 660], layer="back")
    r.edge("west", "west", "rf_frostpine_climb", "east", y=850)
    r.edge("east", "east", "rf_rimefrost_summit", "west", y=850)

    r = field("rf_rimefrost_summit", "Rimefrost Summit", "rimefrost_heights", 2, [70, 72],
              spawns=[("snow_ape", 3, [70, 72], 18)], herbs=("frost_lotus", "frost_lotus"), jars=3, chest="chest_expanse",
              attunement_required=22, elite=True, **heights)
    r.obj("shrine_rf_summit", "shrine", [300, 700])
    r.obj("insight_frost", "insight_stone", [1500, 720], element="water", requires=all_of(unlock("insight_sites")),
          locked_text="A stone glazed with clear ice.")
    r.portal("ice_cave", "hidden", [2200, 700], "rf_hermits_ice_cave", "entry", press_up=True, label="Hermit's Ice Cave")
    r.edge("west", "west", "rf_snow_ape_ledges", "east", y=850)

    r = interior("rf_hermits_ice_cave", "Hermit's Ice Cave", "rimefrost_heights", wall="wall_stone", floor="floor_stone",
                 music="meditation", qi=2.2, rtype="insight", tint="#dbe8f4", **AE)
    r.decor("icicle_rock", [220, 680], layer="back")
    r.decor("icicle_rock", [1080, 680], layer="back", flip=True)
    r.decor("meditation_mat", [640, 860])
    r.decor("incense_burner", [760, 760])
    r.obj("spring_ice", "qi_spring", [420, 900], spring=True)
    r.npc("hermit_shuang", [640, 780], facing=-1)
    r.portal("entry", "door", [120, 700], "rf_rimefrost_summit", "ice_cave", press_up=True, label="Rimefrost Summit")

    lake = dict(backdrop="mirror_lake", material="moss", music="river", ambience="river_ambience", element="water",
                gather_tier="expanse_mid", qi=1.7, loot="jar_expanse", trees=("willow_tree", "reeds"), tint="#b9c6d8", **AE)
    r = field("ml_reedless_shore", "Reedless Shore", "mirrorwater_lake", 3, [68, 70],
              spawns=[("azure_carp_dragonet", 4, [68, 70])], jars=4, attunement_required=22, fishing="mirror_lake", **lake)
    r.decor("sky_ship", [420, 660], layer="back")
    r.portal("ferry", "door", [420, 704], "ae_skydock", "lake_ferry", press_up=True, label="Sky-ship to Cloudgate Port")
    r.obj("sign_ml", "signpost", [700, 860], text="Mirrorwater Lake. East: the Mirror Shallows. The sky-ship returns to Cloudgate Port.")
    r.edge("east", "east", "ml_mirror_shallows", "west", y=850)

    r = field("ml_mirror_shallows", "Mirror Shallows", "mirrorwater_lake", 3, [69, 73],
              spawns=[("azure_carp_dragonet", 5, [69, 73])], jars=4, attunement_required=25, **lake)
    for x in (500, 1100, 1900, 2600, 3300):
        r.decor("lotus_lantern", [x, 700], layer="back")
    for i, x in enumerate((760, 1500, 2300, 3000)):
        r.decor("lotus_pads", [x, 770 + (i % 2) * 130])
    r.portal("hollow", "door", [1900, 700], "ml_toads_hollow", "entry", press_up=True, label="Toad's Hollow")
    r.edge("west", "west", "ml_reedless_shore", "east", y=850)
    r.edge("east", "east", "ml_sentinel_causeway", "west", y=850)

    r = field("ml_sentinel_causeway", "Sentinel Causeway", "mirrorwater_lake", 3, [72, 75],
              spawns=[("river_sentinel", 4, [72, 75], 20), ("azure_carp_dragonet", 2, [71, 73])], jars=4, chest="chest_expanse",
              attunement_required=28, **lake)
    for x in (400, 1300, 2200, 3100):
        r.decor("stone_lantern", [x, 690])
    r.edge("west", "west", "ml_mirror_shallows", "east", y=850)
    r.edge("east", "east", "ml_lake_shrine", "west", y=850)

    r = Room("ml_lake_shrine", "Lake Shrine", "insight", "mirrorwater_lake", 2, backdrop="mirror_lake", material="stone",
             music="meditation", ambience="river_ambience", element="soul", qi=2.0, spawn_point=[300, 820], tint="#e4e2f0", **AE)
    r.decor("paifang_gate", [640, 650])
    r.decor("pagoda", [1800, 640], layer="back")
    for x in (900, 1500, 2200):
        r.decor("lotus_lantern", [x, 700], layer="back")
    r.obj("shrine_ml", "shrine", [400, 700])
    r.obj("mirror_altar", "inspect", [1280, 720], prop="altar", text="A bronze mirror, green with age. The water in its basin does not ripple.",
          set_flag="mirror_vision_seen")
    r.obj("insight_mirror", "insight_stone", [2000, 720], element="soul", requires=all_of(unlock("insight_sites")),
          locked_text="Your reflection in the stone blinks after you do.")
    r.obj("journal_lake", "pickup", [1500, 900], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_lake",
          hidden_if=all_of(flag("journal_lake")))
    r.edge("west", "west", "ml_sentinel_causeway", "east", y=850)

    r = Room("ml_toads_hollow", "Toad's Hollow", "field", "mirrorwater_lake", 2, backdrop="mirror_lake", material="moss",
             music="boss", ambience="river_ambience", element="water", levels=[68, 68], safe=False, spawn_point=[260, 820],
             attunement_required=25, tint="#d0d4e6", **AE)
    r.spawn("thousand_eye_toad", [[1600, 860]], 1, respawn=2700, level=[68, 68], field_boss=True, boss=True)
    back_trees(r, ("willow_tree", "reeds", "willow_tree"), step=460)
    for x in (700, 1100, 2100):
        r.decor("lotus_lantern", [x, 700], layer="back")
    for i, x in enumerate((520, 980, 1420, 1880, 2260)):
        r.decor("lotus_pads", [x, 760 + (i % 2) * 140])
    r.decor("rock_large", [300, 700])
    r.decor("rock_small", [2400, 900])
    front_grass(r, props=("reeds", "tall_grass"), step=320)
    r.portal("entry", "door", [140, 700], "ml_mirror_shallows", "hollow", press_up=True, label="Mirror Shallows")


def nine_peaks_and_canyons():
    """Phase C: the Alliance seat at Nine Peaks, the Gale Canyons (Storm Ward 35-42) and Ironroot Hold; chapter 13."""
    peaks = dict(backdrop="nine_peaks", material="stone", music="sect", ambience="wind_ambience", qi=1.6, tint="#e8e2d6", **AE)
    r = town("np_alliance_gate", "Alliance Gate", "nine_peaks", 2, spawn_point=[420, 820], **peaks)
    r.decor("sky_ship", [420, 660], layer="back")
    r.portal("ferry", "door", [420, 704], "ae_skydock", "peaks_ferry", press_up=True, label="Sky-ship to Cloudgate Port")
    r.decor("paifang_gate", [1400, 650])
    for x in (900, 1900):
        r.decor("banner_alliance", [x, 662])
    r.decor("statue_guardian_lion", [1150, 690])
    r.decor("statue_guardian_lion", [1650, 690], flip=True)
    r.obj("stone_nine_peaks", "teleport_stone", [2100, 880], stone="nine_peaks")
    r.obj("shrine_np_gate", "shrine", [700, 700])
    r.npc("alliance_guard", [1400, 900], oid="npc_alliance_guard_np", facing=-1)
    r.obj("sign_np", "signpost", [2380, 860], text="Nine Peaks, seat of the Alliance. East: the Hall of Nine.")
    r.edge("east", "east", "np_hall_of_nine", "west", y=850)

    r = town("np_hall_of_nine", "Hall of Nine", "nine_peaks", 2, spawn_point=[300, 820], **peaks)
    r.painted("hall_of_nine", "hall", 1280, 700, 140, 130, front=690)
    for x in (400, 2160):
        r.decor("banner_alliance", [x, 662])
    lantern_row(r, [800, 1760], y=670)
    r.building("auction_house", "village_store", 2100, front=690, door_dx=40,
               door=("np_auction_pavilion", "entry", "pavilion_door", {"label": "Auction Pavilion"}))
    r.npc("envoy_lanshi", [1080, 780], facing=1)
    r.npc("elder_zhong", [1480, 760], facing=-1)
    r.npc("broker_mu", [300, 900], oid="npc_broker_mu_np", facing=1, visible_if=all_of(qactive("nine_seats")))
    r.edge("west", "west", "np_alliance_gate", "east", y=850)
    r.edge("east", "east", "np_presence_terrace", "west", y=850)

    r = interior("np_auction_pavilion", "Auction Pavilion", "nine_peaks", wall="wall_wood", music="sect", qi=1.6, **AE)
    r.decor("screen_folding", [300, 690])
    r.decor("scroll_rack", [1000, 690])
    for x in (500, 800):
        r.decor("cushion", [x, 820])
    r.obj("auction_block", "inspect", [640, 720], prop="counter", text="The auction block. Today's lots are chalked on the board behind it.",
          open_page="auction", requires=all_of(unlock("auction_house")), locked_text="Auctioneer Tong: \"Bidders only, friend. Alliance rules.\"")
    r.npc("auctioneer_tong", [760, 740], facing=-1)
    r.portal("entry", "door", [120, 700], "np_hall_of_nine", "pavilion_door", press_up=True, label="Hall of Nine")

    r = town("np_presence_terrace", "Presence Terrace", "nine_peaks", 2, spawn_point=[300, 820], **peaks)
    r.decor("rite_circle", [1280, 880])
    r.obj("spar_np", "spar_post", [1500, 860], opponent="alliance_champion", requires=all_of(unlock("attack")))
    r.npc("champion_qiao", [1700, 780], facing=-1)
    r.obj("sign_np_terrace", "signpost", [2380, 860], text="East: the Gale Canyons (Lv 73-78, Storm Ward 35-42). Tolls collected at the Canyon Mouth.")
    r.edge("west", "west", "np_hall_of_nine", "east", y=850)
    r.edge("east", "east", "gc_canyon_mouth", "west", y=850, ptype="sealed", requires=all_of(qdone("nine_seats")),
           locked_text="Champion Qiao: \"The canyons are the Alliance's business. Take a seat in the Hall first.\"")

    canyon = dict(backdrop="gale_canyon", material="earth", music="field_mountain", ambience="wind_ambience", element="wind",
                  gather_tier="expanse_high", qi=1.7, loot="jar_expanse", trees=("dead_tree_grey", "rock_large"), hazards=["wind_gust"],
                  tint="#ecd0ac", ledge="rock_ledge", **AE)
    r = field("gc_canyon_mouth", "Canyon Mouth", "gale_canyons", 3, [73, 75],
              spawns=[("wind_kite", 4, [73, 75]), ("canyon_brigand", 2, [73, 75])], ores=("stormsteel_ore",), jars=4, attunement_required=35,
              **canyon)
    r.npc("tollkeeper_bai", [500, 780], facing=1)
    r.edge("west", "west", "np_presence_terrace", "east", y=850)
    r.edge("east", "east", "gc_kite_winds", "west", y=850)
    r = field("gc_kite_winds", "Kite Winds", "gale_canyons", 3, [74, 76],
              spawns=[("wind_kite", 5, [74, 76]), ("canyon_harpy", 1, [74, 76])], jars=4, attunement_required=38,
              platforms=[(800, 650, 300, 220), (1900, 640, 300, 300)], **canyon)
    r.edge("west", "west", "gc_canyon_mouth", "east", y=850)
    r.edge("east", "east", "gc_harpy_roosts", "west", y=850)
    r = field("gc_harpy_roosts", "Harpy Roosts", "gale_canyons", 3, [75, 78],
              spawns=[("canyon_harpy", 4, [75, 78], 16)], ores=("stormsteel_ore",), jars=4, chest="chest_expanse", attunement_required=40,
              platforms=[(700, 640, 280, 320), (1600, 650, 280, 260), (2500, 640, 280, 340)], **canyon)
    r.obj("shrine_gc", "shrine", [300, 700])
    r.edge("west", "west", "gc_kite_winds", "east", y=850)
    r.edge("east", "east", "gc_windbridge", "west", y=850)
    r = field("gc_windbridge", "Windbridge", "gale_canyons", 3, [76, 78],
              spawns=[("canyon_harpy", 2, [76, 78]), ("wind_kite", 2, [76, 78]), ("canyon_brigand", 2, [76, 78])], jars=3,
              attunement_required=42, no_flight=True, **canyon)
    r.edge("west", "west", "gc_harpy_roosts", "east", y=850)
    r.edge("east", "east", "ir_hold_gate", "west", y=850)

    hold = dict(backdrop="quarry", material="earth", music="field_earth", ambience="wind_ambience", qi=1.6, tint="#d8ccb8", **AE)
    r = town("ir_hold_gate", "Hold Gate", "ironroot_hold", 2, spawn_point=[300, 820], **hold)
    r.decor("stockade_wall", [900, 660])
    r.decor("paifang_gate", [1280, 650])
    r.decor("stockade_wall", [1660, 660])
    r.decor("watch_tower", [2100, 640], layer="back")
    r.obj("shrine_ir", "shrine", [600, 700])
    r.npc("ironroot_warden", [1400, 780], oid="npc_ironroot_warden", facing=-1)
    r.edge("west", "west", "gc_windbridge", "east", y=850)
    r.edge("east", "east", "ir_clan_hearth", "west", y=850)
    r = town("ir_clan_hearth", "Clan Hearth", "ironroot_hold", 2, spawn_point=[300, 820], **hold)
    r.building("longhouse", "warehouse", 700, front=690)
    r.building("clan_forge", "village_house", 1800, front=690, door_dx=0,
               door=("ir_ancestor_hall", "entry", "hall_door", {"label": "Ancestor Hall"}))
    r.decor("cooking_pot", [1200, 800])
    r.decor("weapon_rack_full", [1450, 690])
    r.obj("anvil_ir", "forge_anvil", [1300, 760], requires=all_of(unlock("smithing")), locked_text="The clan's anvil.")
    r.npc("matriarch_tie", [1000, 760], facing=1)
    r.npc("clan_smith_gang", [1300, 820], facing=-1)
    r.edge("west", "west", "ir_hold_gate", "east", y=850)
    r.edge("desert_road", "east", "sd_glass_dunes", "west", y=850, ptype="sealed",
           requires=all_of(any_of(qactive("glass_and_bone"), qdone("glass_and_bone"))),
           locked_text="The desert road south. The Matriarch's scouts turn back everyone who has no reason to cross the Sunscar.")
    r = interior("ir_ancestor_hall", "Ancestor Hall", "ironroot_hold", wall="wall_wood", music="meditation", qi=2.0, rtype="insight", **AE)
    r.decor("altar", [640, 690])
    for x in (360, 920):
        r.decor("incense_burner", [x, 760])
    r.obj("ancestral_tablets", "inspect", [640, 720], prop="altar",
          text="Rows of iron-root tablets, one for every Ironroot who ever lived. The newest is blank.", set_flag="tablets_honoured")
    r.portal("entry", "door", [120, 700], "ir_clan_hearth", "hall_door", press_up=True, label="Clan Hearth")

def sunscar():
    """Phase D: the Sunscar Desert (Storm Ward 45-50) beyond Ironroot Hold, the Oasis of Bones and the Tomb of
    Sunscar (Storm Ward 55); chapter 14."""
    desert = dict(backdrop="sunscar", material="sand", music="desert", ambience="wind_ambience", element="earth",
                  gather_tier="expanse_high", qi=1.8, loot="jar_expanse", trees=("dune_cactus", "rock_large"), ledge="rock_ledge", **AE)
    r = field("sd_glass_dunes", "Glass Dunes", "sunscar_desert", 3, [73, 76],
              spawns=[("sandstorm_scorpion", 5, [73, 75])], herbs=("ember_cactus", "ember_cactus"), ores=("sunglass_ore",), jars=4,
              attunement_required=45, hazards=["scorching_heat"], **desert)
    r.decor("bleached_ribcage", [1500, 650], layer="back")
    r.obj("sign_sd", "signpost", [300, 860], text="The Sunscar road. South: the Oasis of Bones. Carry water. Carry more water.")
    r.edge("west", "west", "ir_clan_hearth", "desert_road", y=850)
    r.edge("east", "east", "sd_scorpion_flats", "west", y=850)
    r = field("sd_scorpion_flats", "Scorpion Flats", "sunscar_desert", 3, [75, 78],
              spawns=[("sandstorm_scorpion", 6, [75, 78], 14)], herbs=("ember_cactus",), ores=("sunglass_ore", "sunglass_ore"), jars=4,
              chest="chest_expanse", attunement_required=48, hazards=["sandstorm"], platforms=[(1400, 650, 280, 200)], **desert)
    r.obj("shrine_sd_flats", "shrine", [2000, 700])
    r.edge("west", "west", "sd_glass_dunes", "east", y=850)
    r.edge("east", "east", "sd_oasis_of_bones", "west", y=850)

    r = Room("sd_oasis_of_bones", "Oasis of Bones", "rest", "sunscar_desert", 2, backdrop="sunscar", material="sand", tint="#f4e6c8",
             music="desert", ambience="water_ambience", element="water", qi=1.8, spawn_point=[400, 820], idle=["gather"], **AE)
    r.area("water", [900, 860, 760, 100])
    r.decor("bleached_ribcage", [700, 660], layer="back")
    r.decor("bleached_ribcage", [1900, 660], layer="back", flip=True)
    for x, flip in ((820, False), (1160, True), (1740, False)):
        r.decor("palm_tree", [x, 700], flip=flip)
    r.decor("palm_tree", [2240, 960], layer="front")
    r.decor("yurt", [300, 690], layer="back")
    r.decor("cooking_pot", [560, 800])
    r.obj("stone_sunscar", "teleport_stone", [2150, 880], stone="sunscar")
    r.obj("shrine_oasis", "shrine", [1300, 700])
    r.obj("spring_oasis", "qi_spring", [1280, 900], spring=True, requires=all_of(unlock("qi_springs")), locked_text="Cool water under the palms.")
    r.npc("oasis_keeper_meng", [480, 780], facing=1)
    r.npc("bone_reader_xiu", [2000, 780], facing=-1)
    r.edge("west", "west", "sd_scorpion_flats", "east", y=850)
    r.edge("east", "east", "sd_worm_sea", "west", y=850)

    r = field("sd_worm_sea", "Worm Sea", "sunscar_desert", 3, [77, 81],
              spawns=[("dune_worm", 4, [77, 81], 16), ("sandstorm_scorpion", 2, [77, 78])], herbs=("ember_cactus",), ores=("sunglass_ore",),
              jars=4, attunement_required=50, hazards=["quicksand", "scorching_heat"], **desert)
    for x, y in [(900, 800), (1700, 900), (2600, 780)]:
        r.area("quicksand", [x - 90, y - 26, 180, 52])
    r.decor("bleached_ribcage", [2200, 650], layer="back", flip=True)
    r.portal("tomb", "dungeon", [3500, 700], "ts_sealed_gate", "west", press_up=True, label="Tomb of Sunscar",
             requires=all_of(any_of(qactive("the_sealed_gate"), qdone("the_sealed_gate"))),
             locked_text="A stepped portal half-drowned in sand. The bone-reader will know what it is.")
    r.edge("west", "west", "sd_oasis_of_bones", "east", y=850)

    tomb = dict(backdrop="sunscar_tomb", material="stone", tint="#e8cc98", music="tomb", element="earth", qi=2.0, loot="jar_expanse",
                trees=("stone_lantern",), rtype="dungeon", elite=False, idle=[], dungeon_exit="sd_worm_sea", attunement_required=55,
                front=("rock_small",), **AE)
    r = field("ts_sealed_gate", "Sealed Gate", "tomb_of_sunscar", 2, [77, 77],
              spawns=[("terracotta_warden", 3, [77, 77]), ("sandstorm_scorpion", 2, [77, 77])], jars=4, hazards=["spike_traps"], **tomb)
    r.obj("tomb_gate", "inspect", [2300, 700], prop="tomb_gate", state_flag={"flag": "tomb_gate_opened", "on": "open", "off": "sealed"},
          text="The pieces fit. The inscription is a scholar's riddle in an old script; you read it through twice, and the seal turns.",
          set_flag="tomb_gate_opened",
          requires=all_of({"kind": "item_owned", "item": "sun_seal_shard", "count": 3}, {"kind": "attribute_at_least", "attribute": "insight", "value": 80}),
          locked_text="A lock shaped like a sun, three pieces missing, and an inscription that slides away from the eye (Insight 80).")
    r.edge("west", "west", "sd_worm_sea", "tomb", y=850, ptype="gate")
    r.edge("east", "east", "ts_hall_of_sand_kings", "west", y=850, ptype="sealed", requires=all_of(flag("tomb_gate_opened")),
           locked_text="The bronze doors do not move.")
    r = field("ts_hall_of_sand_kings", "Hall of Sand Kings", "tomb_of_sunscar", 3, [77, 77],
              spawns=[("terracotta_warden", 5, [77, 77])], jars=4, chest="chest_tomb", hazards=["spike_traps"], **tomb)
    for i, x in enumerate((500, 1100, 1900, 2500, 3100)):
        r.decor("sand_king_statue", [x, 660], layer="back", flip=i % 2 == 1)
    r.decor("sarcophagus", [1500, 700])
    r.edge("west", "west", "ts_sealed_gate", "east", y=850)
    r.edge("east", "east", "ts_mirror_crypt", "west", y=850)
    r = field("ts_mirror_crypt", "Mirror Crypt", "tomb_of_sunscar", 2, [77, 77],
              spawns=[("terracotta_warden", 2, [77, 77])], jars=3, **tomb)
    for i, x in enumerate((500, 900, 1660, 2060)):
        r.decor("bronze_mirror", [x, 680], flip=i >= 2)
    r.decor("sarcophagus", [1280, 720])
    r.obj("journal_tomb", "pickup", [1280, 900], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_tomb",
          hidden_if=all_of(flag("journal_tomb")))
    r.edge("west", "west", "ts_hall_of_sand_kings", "east", y=850)
    r.edge("east", "east", "ts_throne", "west", y=850)
    r = Room("ts_throne", "Throne of the Tomb King", "boss_arena", "tomb_of_sunscar", 2, backdrop="sunscar_tomb", material="stone",
             tint="#e8cc98", music="boss", levels=[77, 77], safe=False, spawn_point=[200, 820], dungeon_exit="sd_worm_sea",
             attunement_required=55, **AE)
    r.decor("sun_throne", [1900, 690], layer="back")
    r.spawn("tomb_king", [[1700, 840]], 1, respawn=86400, level=[77, 77], boss=True)
    r.npc("grey_pilgrim", [600, 780], oid="npc_grey_pilgrim_tomb", facing=1, visible_if=all_of(qactive("the_tomb_king")))
    r.chest([2300, 900], loot="chest_tomb", level=77, requires=all_of(qdone("the_tomb_king")), locked_text="The King's grave goods. Not while he stands.")
    r.edge("west", "west", "ts_mirror_crypt", "east", y=850)
    r.portal("exit", "door", [2460, 860], "sd_worm_sea", "tomb", press_up=True, label="Worm Sea")


def star_sight(r, oid, at, **kw):
    """A sighting stone: one star reading every ten minutes for a navigator (S16 star charts, Sage 3)."""
    return r.obj(oid, "star_sight", at, item="star_reading", prop="star_sight_stone", **{"yield": [1, 1]}, regrow_s=600,
                 requires=all_of(unlock("star_charting")), locked_text="A ring of bronze on an old stone. Only a navigator knows what to sight through it.",
                 **kw)


def skyport_wreck():
    """Phase E: the Shipwrights' Yard at Cloudgate, the Starsea crossing, the Skyport Wreck (Storm Ward 56-60), the Trial
    Hall of the Nine Peaks, and the story instances of chapters 15-16 (the defence of the Alliance Gate, the Presence Trial)."""
    r = town("ae_shipyard", "Shipwrights' Yard", "cloudgate_port", 2, backdrop="sky_port", material="wood", music="sky_port",
             ambience="wind_ambience", spawn_point=[520, 820], qi=1.4, **AE)
    r.obj("dock_cloudgate", "starsea_dock", [260, 700], route="wreck_run", prop="cloud_skiff",
          requires=all_of(unlock("starsea")), locked_text="Skiffs for the Starsea. A Sage's Qi freezes out there before Sage 3.")
    r.decor("mooring_post", [120, 700])
    r.decor("mooring_post", [420, 700])
    r.obj("slip_cloudgate", "shipyard_slip", [1000, 700], requires=all_of(unlock("shipwright")),
          locked_text="Shipwright Lao's slipway. He builds for those who can crew what they build.")
    r.decor("crate", [1250, 720])
    r.decor("rope", [1320, 690])
    r.obj("chart_table_cloudgate", "chart_table", [1720, 760], requires=all_of(unlock("star_charting")),
          locked_text="Navigator Sun's chart table. Star maps, weighted at the corners.")
    r.decor("armillary_sphere", [1960, 700])
    star_sight(r, "sight_cloudgate", [2240, 700])
    r.npc("shipwright_lao", [1180, 800], facing=-1)
    r.npc("navigator_sun", [1560, 780], facing=1)
    r.edge("east", "east", "ae_skydock", "west", y=850)

    # Star-sighting stones on the Expanse's high places: the Wreck Run is charted before anyone sails it.
    star_sight(ROOMS["rf_rimefrost_summit"], "sight_rimefrost", [1500, 700])
    star_sight(ROOMS["np_presence_terrace"], "sight_presence_terrace", [2100, 700])

    # The crossing (instanced): the vessel's deck under the Starsea; the event runs as long as the vessel takes to cross.
    r = Room("ss_starsea_crossing", "Starsea Crossing", "story", "starsea", 3, backdrop="starsea", material="wood", tint="#b8a58a",
             music="starsea", ambience="wind_ambience", instanced=True, safe=False, crossing=True, levels=[79, 81],
             spawn_point=[900, 820], hazards=["star_wind"], no_flight=True, dungeon_exit="", attunement_required=60,
             event={"id": "starsea_crossing", "duration": 70,
                    "waves": [{"enemy": "starsea_pirate", "every_s": 10, "max": 2, "first_s": 8, "points": [[3400, 820], [3500, 900]]},
                              {"enemy": "wind_kite", "every_s": 14, "max": 2, "first_s": 16, "points": [[2800, 780], [3300, 760]]}],
                    "on_complete": [{"kind": "voyage_arrive"}]}, **AE)
    r.decor("sky_ship", [3300, 600], layer="back", flip=True)
    r.decor("broken_mast", [1500, 690])
    for x in (600, 2400):
        r.decor("crate", [x, 720])
    r.decor("rope", [1200, 690])
    r.decor("barrel", [2000, 720])

    wreck = dict(backdrop="skyport_wreck", material="stone", music="starsea", ambience="wind_ambience", element="metal",
                 gather_tier="expanse_high", qi=1.9, loot="jar_expanse", trees=("dead_tree_grey", "rock_large"), ledge="rock_ledge",
                 front=("rock_small",), tint="#c9c2d6", **AE)
    r = field("sw_broken_pier", "Broken Pier", "skyport_wreck", 3, [76, 78],
              spawns=[("nine_peaks_disciple", 4, [76, 78]), ("starsea_pirate", 2, [78, 79])], ores=("stormsteel_ore",), jars=4,
              attunement_required=56, hazards=["wind_gust"], spawn_point=[420, 820], **wreck)
    r.obj("dock_wreck", "starsea_dock", [220, 700], route="wreck_run_home", prop="cloud_skiff")
    r.obj("shrine_sw_pier", "shrine", [700, 700])
    r.decor("wreck_hull", [1700, 640], layer="back")
    r.decor("starsea_anchor", [1100, 720])
    r.decor("pirate_banner", [2300, 662])
    r.decor("broken_mast", [2900, 690])
    r.obj("sign_sw", "signpost", [560, 860], text="The Skyport Wreck. East: the Pirate Deck. Beyond it the peak, and the Starsea Launch.")
    r.edge("east", "east", "sw_pirate_deck", "west", y=850)

    r = field("sw_pirate_deck", "Pirate Deck", "skyport_wreck", 3, [78, 81],
              spawns=[("starsea_pirate", 5, [79, 81], 14), ("nine_peaks_disciple", 1, [78, 78])], jars=5, chest=None,
              attunement_required=58, hazards=["wind_gust"],
              **dict(wreck, material="wood", tint="#b8a58a", trees=("barrel", "crate", "sack_pile"), front=("barrel",)))
    for x in (700, 2500):
        r.decor("star_ballista", [x, 700])
    for x in (400, 1500, 3400):
        r.decor("pirate_banner", [x, 662])
    r.decor("broken_mast", [1900, 690])
    r.decor("barrel", [1100, 720])
    r.decor("crate", [1180, 730])
    r.npc("gu_in_chains", [2900, 780], facing=-1, visible_if=all_of(qactive("the_skyport_wreck")))
    r.chest([3200, 900], loot="chest_wreck", level=80, oid="pirate_strongbox", requires=all_of(flag("gu_freed")),
            locked_text="The pirates' strongbox. The lock is a formation; Gu knows its word.")
    r.edge("west", "west", "sw_broken_pier", "east", y=850)
    r.edge("east", "east", "sw_riven_peak", "west", y=850)

    r = field("sw_riven_peak", "Riven Peak", "skyport_wreck", 3, [79, 81],
              spawns=[("starsea_pirate", 3, [79, 81]), ("wind_kite", 2, [78, 78])], jars=3, chest="chest_expanse",
              attunement_required=60, hazards=["star_wind", "lightning"], platforms=[(900, 650, 300, 240), (2100, 640, 300, 320)],
              **dict(wreck, element="none", qi=2.0))
    star_sight(r, "sight_riven_a", [1050, 650], alt=240, surface="ledge_0")
    star_sight(r, "sight_riven_b", [2250, 640], alt=320, surface="ledge_1")
    star_sight(r, "sight_riven_c", [3300, 700])
    r.decor("broken_mast", [1600, 690])
    r.obj("journal_riven", "pickup", [2700, 900], item="lu_journal_page", count=1, prop="scroll_rack", set_flag="journal_riven",
          visible_if=all_of(qactive("lus_last_page")), hidden_if=all_of(flag("journal_riven")))
    r.edge("west", "west", "sw_pirate_deck", "east", y=850)
    r.edge("east", "east", "sw_starsea_launch", "west", y=850)

    r = Room("sw_starsea_launch", "Starsea Launch", "rest", "skyport_wreck", 2, backdrop="skyport_wreck", material="stone", tint="#c9c2d6",
             music="starsea", ambience="wind_ambience", qi=2.0, spawn_point=[400, 820], idle=["gather"], **AE)
    r.obj("launch_ring", "inspect", [1500, 700], prop="launch_ring", state_flag={"flag": "stars_beyond_done", "on": "active", "off": "idle"},
          text="The ring of the Starsea Launch. Its lamps follow a line of stars out past the edge of the Expanse, toward a field of lanterns.")
    r.obj("dock_launch", "starsea_dock", [2250, 700], route="lantern_run", prop="cloud_skiff")
    r.decor("armillary_sphere", [900, 700])
    r.decor("starsea_anchor", [620, 720])
    r.obj("shrine_sw_launch", "shrine", [1100, 700])
    r.obj("stone_skyport", "teleport_stone", [1900, 880], stone="skyport_wreck")
    r.npc("launch_warden_he", [1300, 780], facing=-1)
    r.edge("west", "west", "sw_riven_peak", "east", y=850)

    # Nine Peaks · the Trial Hall (chapter 16) off the Presence Terrace.
    ROOMS["np_presence_terrace"].painted("trial_hall", "hall", 640, 460, 120, 120, front=690)
    ROOMS["np_presence_terrace"].portal("trial_door", "door", [640, 704], "np_trial_hall", "entry", press_up=True, label="Trial Hall")
    r = interior("np_trial_hall", "Trial Hall", "nine_peaks", wall="wall_stone", floor="floor_stone", music="meditation", qi=2.0,
                 rtype="insight", **AE)
    for i, x in enumerate((160, 290, 420, 550, 730, 860, 990, 1120)):
        r.decor("trial_seat", [x, 690], layer="back", flip=i >= 4)
    r.decor("pressure_pillar", [640, 690], layer="back")
    r.obj("presence_gate", "rite_circle", [640, 860], event="presence_trial", prop="rite_circle",
          visible_if=all_of(any_of(qactive("the_presence_trial"), qdone("the_presence_trial"))),
          text="The ninth seat is empty. Sit in the circle below it and let the other eight look at you.")
    r.npc("trial_master_wen", [880, 800], facing=-1)
    r.portal("entry", "door", [120, 700], "np_presence_terrace", "trial_door", press_up=True, label="Presence Terrace")
    ROOMS["np_alliance_gate"].obj("war_gong_np", "rite_circle", [1650, 880], event="sect_war", prop="small_bell",
                                  visible_if=all_of(any_of(qactive("the_gate_holds"), qdone("the_gate_holds"))),
                                  text="The Alliance war gong. Strike it and the Gate's defenders take their places.")

    # Story instances: the defence of the Alliance Gate (the sect war, SS2) and the Presence Trial (SS3).
    r = Room("si_sect_war", "Sect War: the Alliance Gate", "story", "story", 3, backdrop="nine_peaks", material="stone", tint="#d6d0c4",
             music="boss", instanced=True, safe=False, spawn_point=[500, 820], levels=[78, 81], dungeon_exit="",
             event={"id": "sect_war", "duration": 300,
                    "waves": [{"enemy": "starsea_pirate", "every_s": 5, "max": 4, "points": [[3300, 800], [3500, 900], [3600, 760]]},
                              {"enemy": "nine_peaks_disciple", "every_s": 9, "max": 2, "first_s": 12, "points": [[3200, 880], [3500, 820]]}],
                    "timed_spawns": [{"enemy": "pirate_captain", "at": [3300, 840], "after_s": 40,
                                      "text": "Comet Captain Rao drops from the pirate junk onto the Gate!"}],
                    "win_on_kill": "pirate_captain",
                    "on_complete": [{"kind": "event_passed", "event": "sect_war"}, {"kind": "grant_currency", "currency": "spirit_stone", "amount": 150},
                                    {"kind": "grant_item", "item": "comet_iron", "count": 2}, {"kind": "grant_item", "item": "storm_shard", "count": 10}],
                    "on_timeout": [{"kind": "teleport", "target": "np_alliance_gate", "portal": ""}]}, **AE)
    r.decor("paifang_gate", [700, 650])
    for x in (300, 1100):
        r.decor("banner_alliance", [x, 662])
    r.decor("sky_ship", [3200, 600], layer="back", flip=True)
    r.decor("star_ballista", [2600, 700])
    r.decor("pirate_banner", [3000, 662])
    r.decor("stockade_wall", [1700, 660])
    r.portal("exit", "door", [140, 700], "np_alliance_gate", "east", press_up=True, label="Leave",
             requires=all_of({"kind": "event_passed", "event": "sect_war"}), locked_text="Hold the Gate!")
    r = Room("si_presence_trial", "The Presence Trial", "story", "story", 2, backdrop="nine_peaks", material="floor_stone", tint="#c8c0dc",
             music="boss", instanced=True, safe=False, spawn_point=[1280, 820], levels=[81, 81], dungeon_exit="", hazards=["presence"],
             event={"id": "presence_trial", "duration": 90,
                    "waves": [{"enemy": "presence_phantom", "every_s": 7, "max": 3, "points": [[400, 820], [2200, 820], [1280, 920]]}],
                    "timed_spawns": [{"enemy": "ninth_presence", "at": [2100, 840], "after_s": 45,
                                      "text": "The ninth seat fills. Its Presence is your own, grown old."}],
                    "on_complete": [{"kind": "event_passed", "event": "presence_trial"}, {"kind": "set_flag", "flag": "presence_trial_passed"}]},
             **AE)
    r.decor("rite_circle", [1280, 880])
    for i, x in enumerate((300, 600, 900, 1660, 1960, 2260)):
        r.decor("trial_seat", [x, 690], layer="back", flip=i >= 3)
    for x in (1100, 1460):
        r.decor("pressure_pillar", [x, 690], layer="back")
    r.portal("exit", "door", [140, 700], "np_trial_hall", "entry", press_up=True, label="Leave",
             requires=all_of({"kind": "event_passed", "event": "presence_trial"}), locked_text="The seats have not finished looking at you.")


VOYAGES = [
    {"id": "wreck_run", "name": "The Wreck Run", "from": "ae_shipyard", "to": "sw_broken_pier", "to_portal": "",
     "chart": "star_chart_wreck", "crossing": "ss_starsea_crossing", "base_s": 70},
    {"id": "wreck_run_home", "name": "The Wreck Run (home)", "from": "sw_broken_pier", "to": "ae_shipyard", "to_portal": "",
     "chart": "star_chart_wreck", "crossing": "ss_starsea_crossing", "base_s": 70},
    {"id": "lantern_run", "name": "The Lantern Run", "from": "sw_starsea_launch", "chart": "star_chart_lantern", "planned": True,
     "planned_text": "The ring points past the edge of the Expanse, toward the Lantern Star Field. That voyage belongs to the next age of your road."},
]


def voyages():
    """S18 Starsea routes: each needs its star chart and a vessel; the crossing room plays the voyage."""
    entries("voyages", VOYAGES)
    ids = {v["id"]: v for v in VOYAGES}
    for r in ROOMS.values():
        for o in r.d["objects"]:
            if o["type"] == "starsea_dock":
                v = ids.get(o.get("route"))
                assert v and v["from"] == r.id, (r.id, o)


def check_hazards():
    """Every hazard a room names exists, is never in a safe room, and has the areas its kind needs."""
    by_id = {h["id"]: h for h in HAZARDS}
    for rid, r in ROOMS.items():
        for hid in r.d["hazards"]:
            assert hid in by_id, (rid, hid)
            assert not r.d["safe"], (rid, "hazard in a safe room")
            kinds = by_id[hid].get("areas")
            if kinds:
                assert any(a["kind"] in kinds for a in r.d["areas"]), (rid, hid, "no areas")


def zone_json():
    rooms = sorted(k for k, r in ROOMS.items() if r.d["zone"] == "jade_river_valley")
    expanse = sorted(k for k, r in ROOMS.items() if r.d["zone"] == "azure_expanse")
    zones = [{
        "id": "jade_river_valley", "tier": 1, "name": "Jade River Valley", "level_range": [0, 63], "ceiling": "heaven_glimpse_3",
        "laws": ["water", "wood", "earth"], "currency": {"everyday": "silver_tael", "high": "spirit_stone"}, "attunement": None,
        "panorama": "valley_day", "start_room": "lf_fishers_hut", "qi_density": [0.8, 1.5], "rooms": rooms,
        "regions": [
            {"id": "lotus_ferry", "name": "Lotus Ferry", "levels": [0, 3], "map": [0.78, 0.58]},
            {"id": "willow_path", "name": "Willow Path", "levels": [1, 3], "map": [0.66, 0.58]},
            {"id": "stoneford", "name": "Stoneford", "levels": [0, 0], "map": [0.52, 0.56]},
            {"id": "jade_sect", "name": "Jade Sect Academy", "levels": [0, 0], "map": [0.46, 0.38]},
            {"id": "cloud_sect", "name": "Cloud Sect Monastery", "levels": [0, 0], "map": [0.60, 0.30]},
            {"id": "stonewall_quarry", "name": "Stonewall Quarry", "levels": [4, 7], "map": [0.55, 0.74]},
            {"id": "reed_marsh", "name": "Reed Marsh", "levels": [4, 12], "map": [0.86, 0.72]},
            {"id": "greyreed_hamlet", "name": "Greyreed Hamlet", "levels": [0, 0], "map": [0.93, 0.80]},
            {"id": "bamboo_grove", "name": "Bamboo Grove", "levels": [10, 15], "map": [0.90, 0.46]},
            {"id": "crane_falls", "name": "Crane Falls", "levels": [0, 0], "map": [0.84, 0.30]},
            {"id": "caravan_road", "name": "Caravan Road", "levels": [14, 19], "map": [0.38, 0.62]},
            {"id": "mudwater_hideout", "name": "Mudwater Hideout", "levels": [14, 20], "map": [0.32, 0.72]},
            {"id": "cleansing_peak", "name": "Cleansing Peak", "levels": [17, 19], "map": [0.76, 0.16]},
            {"id": "deepwater_bend", "name": "Deepwater Bend", "levels": [19, 25], "map": [0.24, 0.56]},
            {"id": "drowned_shrine", "name": "Drowned Shrine", "levels": [21, 27], "map": [0.20, 0.68]},
            {"id": "whitewater_gorge", "name": "Whitewater Gorge", "levels": [28, 36], "map": [0.14, 0.42]},
            {"id": "crane_cliffs", "name": "Crane Cliffs", "levels": [37, 45], "map": [0.18, 0.24]},
            {"id": "mist_peak", "name": "Mist Peak", "levels": [46, 63], "map": [0.32, 0.12]},
            {"id": "summit_ridge", "name": "Summit Ridge", "levels": [55, 63], "map": [0.44, 0.06]},
            {"id": "hidden_vale", "name": "Hidden Vale", "levels": [0, 0], "map": [0.96, 0.22]},
            {"id": "story", "name": "Story", "levels": [0, 0], "map": [0.5, 0.5], "hidden": True},
        ],
        "exit": {"room": "mp_ascension_gate", "to_zone": "azure_expanse"},
    }, {
        "id": "azure_expanse", "tier": 2, "name": "Azure Expanse", "level_range": [55, 81], "ceiling": "sage_sovereign_3",
        "laws": ["water", "wood", "earth", "fire", "metal", "wind", "thunder"], "currency": {"everyday": "spirit_stone", "high": "sage_crystal"},
        # Loot coins are counted in taels; the Expanse pays them out in Spirit Stones at this rate (S21).
        "coin_scale": 0.05, "qi_density": [1.2, 2.0],
        "attunement": {"stat": "storm_ward", "name": "Storm Ward", "shard": "storm_shard", "required": [10, 60], "unlock": "storm_ward",
                       "jade_max": 15, "jade_value": 1.0, "cost": {"base": 1, "per_level": 1},
                       "jades": [{"id": "thunder", "name": "Thunder Jade"}, {"id": "gale", "name": "Gale Jade"},
                                 {"id": "rain", "name": "Rain Jade"}, {"id": "lightning", "name": "Lightning Jade"}]},
        "panorama": "sky_port", "start_room": "ae_landing", "rooms": expanse,
        "regions": [
            {"id": "cloudgate_port", "name": "Cloudgate Port", "levels": [0, 0], "map": [0.82, 0.62]},
            {"id": "thunderhorn_plains", "name": "Thunderhorn Plains", "levels": [64, 69], "attunement": 10, "map": [0.62, 0.70]},
            {"id": "rimefrost_heights", "name": "Rimefrost Heights", "levels": [67, 72], "attunement": 20, "map": [0.50, 0.22]},
            {"id": "mirrorwater_lake", "name": "Mirrorwater Lake", "levels": [68, 75], "attunement": 25, "map": [0.70, 0.42]},
            {"id": "nine_peaks", "name": "Nine Peaks", "levels": [0, 0], "map": [0.40, 0.46]},
            {"id": "gale_canyons", "name": "Gale Canyons", "levels": [73, 78], "attunement": 40, "map": [0.26, 0.30]},
            {"id": "ironroot_hold", "name": "Ironroot Clan Hold", "levels": [0, 0], "map": [0.30, 0.60]},
            {"id": "sunscar_desert", "name": "Sunscar Desert", "levels": [73, 81], "attunement": 50, "map": [0.16, 0.74]},
            {"id": "tomb_of_sunscar", "name": "Tomb of Sunscar", "levels": [77, 77], "attunement": 55, "map": [0.08, 0.84]},
            {"id": "skyport_wreck", "name": "Skyport Wreck", "levels": [76, 81], "attunement": 60, "map": [0.10, 0.18]},
            {"id": "starsea", "name": "Starsea", "levels": [79, 81], "map": [0.05, 0.10], "hidden": True},
        ],
        "exit": {"room": "ae_landing", "to_zone": "jade_river_valley"},
    }]
    entries("zones", zones)


def teleport_stones():
    rows = [
        {"id": "stoneford", "name": "Stoneford Market", "room": "sf_market", "at": [1480, 880], "fee_shards": 1},
        {"id": "jade_academy", "name": "Jade Sect Academy", "room": "ja_gate_street", "at": [520, 880], "fee_shards": 1, "sect": "jade_sect"},
        {"id": "cloud_monastery", "name": "Cloud Sect Monastery", "room": "cm_cliff_stair", "at": [460, 880], "fee_shards": 1, "sect": "cloud_sect"},
        {"id": "hidden_vale", "name": "Hidden Vale", "room": "hv_vale_gate", "at": [300, 880], "fee_shards": 1},
        {"id": "cloudgate", "name": "Cloudgate Port", "room": "ae_port_market", "at": [1900, 880], "fee_shards": 1, "zone": "azure_expanse"},
        {"id": "nine_peaks", "name": "Nine Peaks", "room": "np_alliance_gate", "at": [2100, 880], "fee_shards": 1, "zone": "azure_expanse"},
        {"id": "sunscar", "name": "Oasis of Bones", "room": "sd_oasis_of_bones", "at": [2150, 880], "fee_shards": 1, "zone": "azure_expanse"},
        {"id": "skyport_wreck", "name": "Starsea Launch", "room": "sw_starsea_launch", "at": [1900, 880], "fee_shards": 1, "zone": "azure_expanse"},
    ]
    entries("teleport_stones", rows)
    # Every teleport stone object must name one of these.
    for r in ROOMS.values():
        for o in r.d["objects"]:
            if o["type"] == "teleport_stone":
                assert any(s["id"] == o.get("stone") for s in rows), (r.id, o)


def set_pieces():
    rows = [
        {"id": "heavens_cleansing", "name": "Heaven's Cleansing", "room_event": {"id": "heavens_cleansing", "duration": 45,
         "wave": {"enemy": "stone_guardian", "every_s": 6, "max": 3, "points": [[300, 860], [1000, 860]]},
         "on_complete": [{"kind": "event_passed", "event": "heavens_cleansing"}, {"kind": "set_flag", "flag": "cleansing_done"}],
         # Untouched by the heavens' judgment, the body is washed clean of every residue (gap report G1).
         "on_flawless": [{"kind": "clear_residue"}, {"kind": "set_flag", "flag": "cleansing_flawless"}]},
         "requires": all_of(realm("qi_kindling_9"))},
        {"id": "riverbreath_trial", "name": "The Riverbreath Trial", "room_event": {"id": "riverbreath_trial", "duration": 40,
         "wave": {"enemy": "drowned_acolyte", "every_s": 7, "max": 3, "points": [[900, 860], [1700, 860]]},
         "on_complete": [{"kind": "event_passed", "event": "riverbreath_trial"}, {"kind": "set_flag", "flag": "riverbreath_trial_done"}]},
         "requires": all_of(realm("qi_unfurling_3"))},
        {"id": "trial_of_reflections", "name": "Trial of Reflections", "room": "si_trial_of_reflections", "portal": "exit",
         "requires": all_of(realm("heart_tempering_9"))},
        {"id": "siege_of_two_sects", "name": "Siege of Two Sects", "room": "si_siege", "portal": "exit",
         "requires": all_of(realm("heaven_glimpse_2"))},
        # Act II · chapters 15-16: the defence of the Alliance Gate (S25 sect war) and the Presence Trial (S05, into Will Manifest).
        {"id": "sect_war", "name": "Sect War: the Alliance Gate", "room": "si_sect_war", "portal": "exit",
         "requires": all_of(realm("sage_sovereign_2")), "repeatable": {"cooldown_h": 20}},
        {"id": "presence_trial", "name": "The Presence Trial", "room": "si_presence_trial", "portal": "exit",
         "requires": all_of(realm("sage_sovereign_3"))},
    ]
    entries("set_pieces", rows)


# ---------------------------------------------------------------------------------------------
# Movement pass (S17 room rules, S30 movement): every room gives the jump, the double jump, the
# rooftops, Wall-Step and flight something to do. Low props become standable blocks, flat fields and
# dungeons get ledges with a reward on the higher one, towns get raised decks, and from the Crane
# Cliffs on a cloud ledge above double-jump height waits for fliers.
JUMP_ONE, JUMP_TWO, FLIGHT_LEDGE = 110, 220, 320   # single jump peaks at 122, double at 244
STANDABLE = {   # prop: (share of the art's width that is solid, height of its top)
    "crate": (0.8, 36), "barrel": (0.7, 48), "sack_pile": (0.8, 38), "hay_bale": (0.8, 42), "rock_small": (0.8, 32),
    "table": (0.85, 42), "stone_wall_low": (0.9, 48), "bed": (0.85, 40), "counter": (0.9, 58), "rock_large": (0.75, 78),
    "boulder_moss": (0.7, 86), "cart_broken": (0.75, 70), "sarcophagus": (0.85, 72), "icicle_rock": (0.7, 78),
    "storage_chest": (0.8, 38), "driftwood": (0.85, 22),
}


def _prop_width(prop):
    e = PROPS.get(prop, {})
    return float(e.get("frame", [80, 80])[0])


def _clear(r, x, y, radius):
    """No portal, object, spawn or arrival point within `radius` of (x, y)."""
    pts = [p["at"] for p in r.d["portals"] if "at" in p] + [o["at"] for o in r.d["objects"]] + [r.d["spawn_point"]]
    for sp in r.d["spawns"]:
        pts += sp["points"]
    return all(((x - a[0]) ** 2 + (y - a[1]) ** 2) ** 0.5 >= radius for a in pts)


def _free_span(r, x0, x1, pad=60):
    """True when nothing tall stands in the back row between x0 and x1 (portals, NPCs, objects, buildings, ledges)."""
    for p in r.d["portals"]:
        if "at" in p and x0 - pad - 120 <= p["at"][0] <= x1 + pad + 120:
            return False
    for o in r.d["objects"]:
        if x0 - pad <= o["at"][0] <= x1 + pad and o["at"][1] < 800:
            return False
    for srf in r.d["surfaces"]:
        if srf["stratum"] == "platform" or srf["kind"] in ("roof", "stairs", "ladder"):
            a, b = srf["rect"][0], srf["rect"][0] + srf["rect"][2]
            if not (x1 + pad < a or x0 - pad > b):
                return False
    for sc in r.d["scenery"]:
        a = sc["footprint"][0]
        if x0 - pad <= a <= x1 + pad and sc["footprint"][1] < 720:
            return False
    return True


def _spans(r, width, count, lo=260):
    """Up to `count` free back-row spans of `width`, spread across the room."""
    out = []
    w = r.w
    step = max(200, (w - 2 * lo) // max(1, count * 3))
    x = lo
    while x + width < w - lo and len(out) < count:
        if _free_span(r, x, x + width) and all(abs(x - o) > width + 200 for o in out):
            out.append(x)
            x += width + 300
        else:
            x += step
    return out


def _zone_chest(r):
    return "chest_expanse" if r.d["zone"] == "azure_expanse" else ("chest_dungeon" if r.d["type"] in ("dungeon", "secret", "boss_arena") else "chest_valley")


def _ledge_reward(r, sid, x, width, h, loot=None):
    o = r.chest([x + width // 2, 665], loot=loot or _zone_chest(r), level=max(1, r.d["level_range"][1]), alt=h, surface=sid, oid="chest_" + sid)
    return o


def earth_vents():
    """Earth Fire (gap report G1): one vent to a zone, where an alchemist sets a furnace over the ground's own fire."""
    for rid, oid, y in [("wg_rapids_terraces", "earth_vent_wg", 900), ("sd_scorpion_flats", "earth_vent_sd", 900)]:
        r = ROOMS[rid]
        x = next(x for x in range(600, r.w - 400, 80) if _clear(r, x, y, 180))
        r.obj(oid, "earth_vent", [x, y], requires=all_of(unlock("alchemy")),
              locked_text="Heat rises from a crack in the stone. An alchemist could use it.")


def movement_extras():
    """Hand-placed climbing where the automatic pass finds no clear back row."""
    def deck(rid, sid, rect, h, kind="balcony"):
        ROOMS[rid].surface(sid, rect, h, kind=kind)
    deck("ae_landing", "deck_terrace_0", [2140, 634, 200, 56], JUMP_ONE)
    deck("ae_landing", "deck_terrace_1", [1900, 630, 200, 52], JUMP_TWO)
    deck("ae_shipyard", "scaffold_slip", [860, 636, 280, 50], 120)          # the slipway's scaffold over the new hull
    deck("ae_shipyard", "deck_yard", [1860, 630, 200, 52], JUMP_TWO)
    ROOMS["ae_shipyard"].block("crate", 1360, 740, 36, 26, 36, standable=True)
    deck("sf_fairground", "deck_fair_0", [3150, 634, 220, 56], JUMP_ONE)
    deck("sf_fairground", "deck_fair_1", [3390, 630, 200, 52], JUMP_TWO)
    deck("sd_oasis_of_bones", "rocks_oasis_0", [700, 640, 240, 50], JUMP_ONE, "rock_ledge")
    deck("sd_oasis_of_bones", "rocks_oasis_1", [960, 636, 220, 46], JUMP_TWO, "rock_ledge")
    deck("cf_behind_falls", "ledge_falls", [520, 654, 220, 46], JUMP_ONE, "rock_ledge")
    deck("sq_collapsed_tunnel", "ledge_tunnel", [600, 650, 200, 46], JUMP_ONE, "rock_ledge")
    deck("wg_waterfall_cave", "ledge_cave", [400, 654, 240, 46], JUMP_ONE, "rock_ledge")
    # Set pieces: the Gate's wall-walks and the siege's broken ramparts give room to dodge a boss.
    deck("si_sect_war", "wallwalk_0", [900, 634, 300, 56], JUMP_ONE)
    deck("si_sect_war", "wallwalk_1", [2000, 634, 300, 56], JUMP_ONE)
    deck("si_siege", "rampart_0", [1300, 640, 300, 50], JUMP_ONE, "rock_ledge")
    deck("si_siege", "rampart_1", [2200, 640, 300, 50], JUMP_ONE, "rock_ledge")
    deck("cp_cleansing_summit", "summit_rock_0", [240, 652, 160, 46], JUMP_ONE, "rock_ledge")
    deck("cp_cleansing_summit", "summit_rock_1", [860, 652, 160, 46], JUMP_ONE, "rock_ledge")
    # The home sect's yard: plum-blossom poles, the classic footwork drill, in front of the halls.
    for x, y in ((1500, 900), (1570, 870), (1640, 905), (1710, 875), (1780, 900)):
        ROOMS["hv_sect_grounds"].block("training_stump", x, y, 26, 18, 64, standable=True)
    deck("hv_vale_gate", "ledge_vale", [820, 646, 220, 46], JUMP_ONE, "rock_ledge")
    # Elders' peaks and cave abodes: a rock shelf above the spring and a higher one beside it.
    for rid in ("ja_elder_hu_peak", "cm_elder_sung_peak"):
        deck(rid, "ledge_peak_0", [340, 648, 200, 46], JUMP_ONE, "rock_ledge")
        deck(rid, "ledge_peak_1", [560, 640, 170, 46], JUMP_TWO, "rock_ledge")
    for rid in ("ja_cave_abode", "cm_cave_abode"):
        deck(rid, "ledge_abode", [400, 650, 170, 46], JUMP_ONE, "rock_ledge")
    # Breath Control (secret art, Qi Unfurling 3): the Scripture Well drops into a flooded grotto.
    w = ROOMS["ds_scripture_well"]
    w.portal("grotto", "door", [1800, 700], "ds_drowned_grotto", "entry", press_up=True, label="The flooded shaft",
             requires=all_of({"kind": "secret_art", "art": "breath_control"}),
             locked_text="The well drops into black water. Without Breath Control you would not come back up.")
    r = Room("ds_drowned_grotto", "Drowned Grotto", "secret", "drowned_shrine", 2, backdrop="cave", material="floor_stone", tint="#7fa8c0",
             music="dungeon", ambience="water_ambience", levels=[24, 27], safe=False, spawn_point=[260, 820], hazards=["deep_water"],
             qi=1.6, idle=[], underwater=True)
    r.portal("entry", "door", [140, 700], "ds_scripture_well", "grotto", press_up=True, label="Up the shaft")
    for i, x in enumerate((900, 1700)):
        r.obj("air_pocket_%d" % i, "air_pocket", [x, 860])
    r.spawn("drowned_acolyte", [[1200, 800], [2000, 860]], 2, respawn=30, level=[24, 26])
    r.herb("mist_lotus", [600, 930])
    r.herb("mist_lotus", [2150, 930])
    r.surface("ledge_grotto", [1240, 650, 260, 46], JUMP_ONE, kind="rock_ledge")
    r.chest([1370, 665], loot="chest_dungeon", level=27, alt=JUMP_ONE, surface="ledge_grotto", oid="chest_grotto")
    r.decor("stone_lantern", [700, 640], layer="back")
    r.decor("scholar_rock", [2300, 700], layer="back")
    # The Starsea crossing: a raised stern deck (the quarterdeck) at the vessel's back.
    deck("ss_starsea_crossing", "quarterdeck", [240, 634, 360, 56], JUMP_ONE)
    ROOMS["ss_starsea_crossing"].block("barrel", 1900, 760, 30, 26, 48, standable=True)


def movement_pass():
    stats = {"blocks": 0, "ledges": 0, "cloud": 0, "decks": 0, "lofts": 0}
    for rid, r in ROOMS.items():
        d = r.d
        rtype = d["type"]
        # 1. Low props in the walk strip become standable blocks (you can hop onto crates and tables).
        keep = []
        for dec in d["decor"]:
            prop, at = dec["prop"], dec["at"]
            if dec.get("layer", "play") == "play" and prop in STANDABLE and 640 <= at[1] <= 940 and _clear(r, at[0], at[1], 120):
                share, top = STANDABLE[prop]
                fw = int(_prop_width(prop) * share)
                r.block(prop, at[0], at[1], fw, 26, top, standable=True, flip=dec.get("flip", False))
                stats["blocks"] += 1
                continue
            keep.append(dec)
        d["decor"] = keep
        if d.get("instanced") or rtype in ("story", "trial", "event", "home"):
            continue
        has_vertical = any(s["stratum"] == "platform" or s["kind"] in ("roof", "stairs", "ladder") for s in d["surfaces"])
        outdoor = not d.get("custom_ground")
        lv0 = d["level_range"][0]
        # 2. Flat fields, paths and dungeons: a jump ledge and a double-jump ledge with a chest on it.
        if rtype in ("field", "path", "dungeon", "secret", "boss_arena") and not has_vertical and r.w >= 2560:
            spans = _spans(r, 280, 2)
            for i, x in enumerate(spans):
                h = JUMP_ONE if i == 0 else JUMP_TWO
                sid = "ledge_mv_%d" % i
                r.surface(sid, [x, 640, 280, 50], h, kind="rock_ledge")
                stats["ledges"] += 1
                if i == 1 and rtype != "boss_arena":
                    _ledge_reward(r, sid, x, 280, h)
        # 3. Fliers' reward: a cloud ledge above double-jump height (Cloud Stride 1, S18 flight).
        if outdoor and rtype in ("field", "path") and lv0 >= 37 and not d.get("no_flight") and r.w >= 2560:
            spans = _spans(r, 240, 1, lo=r.w // 3)
            for x in spans:
                sid = "cloud_mv"
                r.surface(sid, [x, 636, 240, 44], FLIGHT_LEDGE, kind="cloud")
                _ledge_reward(r, sid, x, 240, FLIGHT_LEDGE, loot="chest_expanse" if d["zone"] == "azure_expanse" else "chest_dungeon")
                stats["cloud"] += 1
        # 4. Towns, sect grounds and rest stops with nothing to climb: a timber deck and a higher one beside it.
        if rtype in ("town", "sect", "rest") and outdoor and not has_vertical and r.w >= 2560:
            spans = _spans(r, 460, 1)
            for x in spans:
                r.surface("deck_mv_0", [x, 634, 220, 56], JUMP_ONE, kind="balcony")
                r.surface("deck_mv_1", [x + 240, 630, 220, 52], JUMP_TWO, kind="balcony")
                r.decor("lantern_string", [x + 230, 380], layer="back")
                stats["decks"] += 2
        # 5. Interiors and halls: a loft on the back wall where the wall is clear.
        if d.get("custom_ground") and rtype in ("interior", "insight", "sect", "rest") and r.w == 1280 and not has_vertical:
            for x in (820, 140, 480):
                if _free_span(r, x, x + 300, pad=20):
                    r.surface("loft_mv", [x, 654, 300, 46], JUMP_ONE, kind="balcony")
                    stats["lofts"] += 1
                    break
    print("movement pass:", stats)


def check_links():
    """Every portal target exists (or is planned) and every edge/door has a matching return portal."""
    planned = set()
    for r in ROOMS.values():
        for p in r.d["portals"]:
            to = p["to"]
            if to in planned:
                continue
            assert to in ROOMS, ("missing room", r.id, p["id"], to)
            back = [q for q in ROOMS[to].d["portals"] if q["id"] == p["to_portal"]]
            assert back, ("missing return portal", r.id, p["id"], to, p["to_portal"])


def reachability():
    """Every non-instanced room is reachable from Lotus Ferry (ignoring requirements)."""
    seen = set()
    todo = ["lf_fishers_hut"]
    while todo:
        rid = todo.pop()
        if rid in seen or rid not in ROOMS:
            continue
        seen.add(rid)
        for p in ROOMS[rid].d["portals"]:
            todo.append(p["to"])
        # A Starsea dock is a way on too: the Skyport Wreck is only reached by sailing.
        for o in ROOMS[rid].d["objects"]:
            if o["type"] == "starsea_dock":
                todo += [v["to"] for v in VOYAGES if v["id"] == o.get("route") and "to" in v]
    unreached = [rid for rid, r in ROOMS.items() if rid not in seen and not r.d.get("instanced")]
    assert not unreached, ("unreachable", unreached)


def build():
    ROOMS.clear()
    lotus_ferry()
    willow_path()
    stoneford()
    sects()
    valley()
    azure_expanse()
    rimefrost_and_mirrorwater()
    nine_peaks_and_canyons()
    sunscar()
    skyport_wreck()
    earth_vents()
    movement_extras()
    movement_pass()
    check_links()
    reachability()
    os.makedirs(ROOMS_DIR, exist_ok=True)
    for f in os.listdir(ROOMS_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(ROOMS_DIR, f))
    for rid, r in ROOMS.items():
        write(rid + ".json", r.build(), folder=ROOMS_DIR)
    zone_json()
    teleport_stones()
    set_pieces()
    voyages()
    hazards_json()
    check_hazards()
    print("rooms:", len(ROOMS))


if __name__ == "__main__":
    build()
