"""Dev tool (P7a · M13, M36, M37): write the Item Wiki and the Monster & Drops Wiki from data/.

    python3 tools/dev/wiki.py            # writes docs/wiki/items.md and docs/wiki/monsters.md
    python3 tools/dev/wiki.py --gaps     # also prints the items nothing hands out

It reads only the JSON in data/ (never the scripts), and its output is byte-identical on every
run: ids and keys are sorted and nothing carries a date. build_data.py runs it after a full build.

An item's sources are found by scanning every place data/ hands items out (SOURCE CHANNELS below).
Where a rule lives in a script but its numbers or ids live in data/, the tool mirrors the rule and
names it: the banded equipment roll (LootRules.make_equipment), beast cores
(WorldAuthority.beast_core_for), the Beast Tide's cores (WorldAuthority.apply_tide_result) and the
Elder's token (GameAuthority, effect upgrade_sect_token). tests/data_validation.gd
(item_source_suite) scans the same channels: keep the two in step.

An item that no channel hands out carries an explicit mark in its data instead, `"source": "<mark>"`
(a string, or a list holding one, as the artifacts' authored source lists do). The marks:
    story    a scripted story beat or start gives it, and the data does not name it there
    system   a game system names the item in its own rule (a failed experiment, a tree's fruit)
    later    it belongs to a zone not built yet, and nothing hands it out in this build
Any other `source` value (the artifacts' "weapon_hall", "sect_shop" hints) is not a mark. An item
with neither is a real gap: the page says so, and data_validation lists it in KNOWN_SOURCE_GAPS
until it has a source.

SOURCE CHANNELS
    drops        enemy loot tables (guaranteed, groups, rare, quest drops, lost manuals), first-defeat treasures,
                 pet skill books, beast cores, Spirit Soil, the banded equipment roll
    containers   jars, crates, chests and wine jars in rooms, tower floors, calendar rifts
    gathering    herb patches, ore veins, star sights, insect swarms, beast trails, pickups, fishing
                 spots, Beast King nests, treasure births, posts (nodes, side drops, swarms, trails)
    garden       beds grown from seeds, seeds returned by a harvest
    crafting     recipe outputs, post calcination salts, the Apprentice Bench, professions
                 (appraisal, research, puppets), curio appraisal, relic and legend restoration, salvage
    shops        shop stock and rotations, the two auctions
    rewards      every grant_item / grant_equipment effect anywhere in data/, rooms and dialogue
                 (quests, unlocks, achievements, activity chests, guild ranks, NPC hearts, room events,
                 the skip-start kit...), reward lists (expeditions, the beast arena and grove, the Beast
                 Tide, the gathering trial, route medals, rooftop chases), sect tokens
    mail         attachments of mails sent by effects and karma debts
"""
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs", "wiki")
MARKS = {"story": "given by a scripted story beat or start; the data does not name it there",
         "system": "made by a game system whose own rule names the item (see the description)",
         "later": "belongs to a zone not built yet; nothing hands it out in this build"}
GRANT_KINDS = ("grant_item", "grant_equipment")
PART_LABELS = {"rewards": ", reward", "on_accept": ", on accept", "on_complete": ", on completion", "on_flawless": ", flawless",
               "heart_rewards": " heart reward", "effects": ""}
CHANNELS = ["Drop", "Container", "Gathering", "Garden", "Crafting", "Shop", "Reward", "Mail"]
# WorldAuthority.apply_tide_result: `cores` beast cores of these elements at the holder's tier.
TIDE_CORE_ELEMENTS = ("fire", "water", "wood", "earth", "wind", "thunder")
TIDE_CORE_TIERS = (("low", "below Lv 28"), ("mid", "Lv 28–45"), ("high", "Lv 46 and up"))


# ------------------------------------------------------------------ loading
def read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Data:
    def __init__(self):
        self.t = {}
        for path in sorted(glob.glob(os.path.join(DATA, "*.json"))):
            self.t[os.path.basename(path)[:-5]] = read(path)
        # The tables the game does not read (the legendary chains' record) sit in tests/data (audit 45).
        for path in sorted(glob.glob(os.path.join(ROOT, "tests", "data", "*.json"))):
            self.t[os.path.basename(path)[:-5]] = read(path)
        self.rooms = {}
        for path in sorted(glob.glob(os.path.join(DATA, "rooms", "*.json"))):
            r = read(path)
            self.rooms[r["id"]] = r
        self.dialogue = {}
        for path in sorted(glob.glob(os.path.join(DATA, "dialogue", "*.json"))):
            for tid, tree in read(path).get("trees", {}).items():
                self.dialogue[tid] = tree
        self.items = collections.OrderedDict()
        for table in ("items", "artifacts"):
            for e in self.entries(table):
                self.items[e["id"]] = e
        self.enemies = {e["id"]: e for e in self.entries("enemies")}
        self.loot = {e["id"]: e for e in self.entries("loot_tables")}
        self.npcs = {e["id"]: e for e in self.entries("npcs")}
        self.quests = {e["id"]: e for e in self.entries("quests")}
        self.realms = {e["key"]: e for e in self.entries("realms")}
        self.unlocks = {e["id"]: e for e in self.entries("unlocks")}
        self.shops = {e["id"]: e for e in self.entries("shops")}
        self.zones = {e["id"]: e for e in self.entries("zones")}
        self.regions = {}
        for z in self.entries("zones"):
            for reg in z.get("regions", []):
                self.regions[(z["id"], reg["id"])] = reg["name"]
        self.grade_order = self.t["grades"]["order"]
        self.icons = self.t["icon_manifest"]
        self.npc_rooms = collections.defaultdict(set)
        for rid, r in self.rooms.items():
            for o in r.get("objects", []):
                if o.get("type") == "npc" and o.get("npc"):
                    self.npc_rooms[o["npc"]].add(rid)

    def entries(self, table):
        return self.t.get(table, {}).get("entries", [])

    def cfg(self, table):
        return self.t.get(table, {})

    # names
    def item_name(self, iid):
        return self.items.get(iid, {}).get("name", iid)

    def room_name(self, rid):
        r = self.rooms.get(rid)
        if not r:
            return rid
        region = self.regions.get((r.get("zone"), r.get("region")))
        return "%s (%s)" % (r.get("name", rid), region) if region and region != r.get("name") else r.get("name", rid)

    def zone_name(self, zid):
        return self.zones.get(zid, {}).get("name", zid)

    def npc_name(self, nid):
        return self.npcs.get(nid, {}).get("name", nid)

    def enemy_name(self, eid):
        return self.enemies.get(eid, {}).get("name", eid)

    def quest_name(self, qid):
        return self.quests.get(qid, {}).get("name", qid)

    def unlock_name(self, uid):
        return self.unlocks.get(uid, {}).get("label", uid)

    def currency_name(self, cid):
        for cur in self.cfg("currencies").get("currencies", []):
            if cur.get("id") == cid:
                return cur.get("name", cid)
        return titled(cid)

    def realm_name(self, key):
        return self.realms.get(key, {}).get("name", key)

    def grade_index(self, grade):
        return self.grade_order.index(grade) if grade in self.grade_order else len(self.grade_order)

    def drop(self):
        """The equipment roll's rules (grades.json `drop`, read by LootRules)."""
        return self.cfg("grades").get("drop", {})

    def drop_level_cap(self):
        """LootRules.drop_level_cap: the top Level of the highest grade with banded bases."""
        grades = {a["grade"] for a in self.entries("artifacts") if banded_eligible(self, a)}
        return max([int(b[2]) for b in self.cfg("stats").get("grade_bands", []) if b[0] in grades] or [1])

    def grade_for_ilv(self, ilv):
        for band in self.cfg("stats").get("grade_bands", []):
            if band[1] <= ilv <= band[2]:
                return band[0]
        return "plain"


# ------------------------------------------------------------------ formatting
def pct(p):
    return ("%.2f" % (float(p) * 100.0)).rstrip("0").rstrip(".") + "%"


def num(v):
    if isinstance(v, float):
        return ("%.2f" % v).rstrip("0").rstrip(".")
    return str(v)


def count_text(c):
    if isinstance(c, list):
        return str(c[0]) if c[0] == c[1] else "%d–%d" % (c[0], c[1])
    return str(c)


def times(c):
    t = count_text(c)
    return "" if t == "1" else " ×" + t


def titled(snake):
    return str(snake).replace("_", " ").capitalize()


def band_text(lo, hi):
    return "Lv %d" % lo if lo == hi else "Lv %d–%d" % (lo, hi)


def item_link(d, iid):
    return "[%s](#item-%s)" % (d.item_name(iid), iid)


def enemy_link(d, eid, page="monsters.md"):
    return "[%s](%s#enemy-%s)" % (d.enemy_name(eid), page, eid)


def join_rooms(d, rids, limit=None):
    names = sorted({d.room_name(r) for r in rids})
    if limit and len(names) > limit:
        return ", ".join(names[:limit]) + " and %d more" % (len(names) - limit)
    return ", ".join(names)


def req_text(d, req):
    if not isinstance(req, dict) or not req:
        return ""
    parts = []
    for key, sep in (("all", " and "), ("any", " or ")):
        conds = []
        for c in req.get(key, []):
            if "all" in c or "any" in c:
                conds.append("(" + req_text(d, c) + ")")
                continue
            k = c.get("kind", "")
            if k == "realm_at_least":
                conds.append(d.realm_name(c.get("realm", "")))
            elif k == "level_at_least":
                conds.append("Level %s" % c.get("level", c.get("value", "")))
            elif k == "unlock":
                conds.append("unlock " + d.unlock_name(c.get("system", "")))
            elif k in ("quest_done", "quest_active"):
                conds.append("%s %s" % ("after" if k == "quest_done" else "during", d.quest_name(c.get("quest", ""))))
            elif k == "sect_rank_at_least":
                conds.append("sect rank %s" % titled(c.get("rank", "")))
            elif k == "reputation_at_least":
                conds.append("%s reputation %s" % (titled(c.get("faction", "")), c.get("value", c.get("amount", ""))))
            else:
                args = ", ".join("%s %s" % (a, c[a]) for a in sorted(c) if a not in ("kind", "hard", "cause", "fix"))
                conds.append(titled(k) + (" (" + args + ")" if args else ""))
        if conds:
            parts.append(sep.join(conds))
    return " and ".join(parts)


def effect_text(d, e):
    k = e.get("kind", "")
    args = []
    for a in sorted(e):
        if a == "kind":
            continue
        v = e[a]
        if a == "item" and v in d.items:
            v = d.item_name(v)
        args.append("%s %s" % (a.replace("_", " "), json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else num(v)))
    return titled(k) + (" (" + ", ".join(args) + ")" if args else "")


# ------------------------------------------------------------------ sources
class Sources:
    def __init__(self, d):
        self.d = d
        self.cap = d.drop_level_cap()
        self.by_item = collections.defaultdict(set)
        self.loot_users = collections.defaultdict(list)   # table -> [(kind, text, Level bands, enemy id)]
        self.enemy_extra = collections.defaultdict(list)   # enemy -> [(item, rate text, note)] outside the table
        self.banded = collections.defaultdict(set)         # grade -> set of "who rolls it" texts

    def add(self, iid, channel, text):
        if iid in self.d.items:
            self.by_item[iid].add((CHANNELS.index(channel), channel, text))

    def run(self):
        self.enemies()
        self.containers()
        self.loot_tables()
        self.banded_equipment()
        self.gathering()
        self.garden()
        self.crafting()
        self.shops()
        self.rewards()
        self.effects()
        return self

    # --- enemies and their tables
    def enemy_levels(self, eid):
        e = self.d.enemies[eid]
        lv = e.get("level", [1, 1])
        lo, hi = int(lv[0]), int(lv[-1])
        for r in self.d.rooms.values():
            for s in r.get("spawns", []):
                if s.get("enemy") == eid:
                    slo, shi = spawn_levels(s)
                    lo, hi = min(lo, slo), max(hi, shi)
        return lo, hi

    def enemies(self):
        d = self.d
        cores = d.cfg("pet_growth").get("cores", {})
        soil = d.cfg("garden").get("spirit_soil", {})
        soil_foes = []
        for eid in sorted(d.enemies):
            e = d.enemies[eid]
            lo, hi = self.enemy_levels(eid)
            link = enemy_link(d, eid) + " (%s)" % band_text(lo, hi)
            table = e.get("loot", eid)
            self.loot_users[table].append(("enemy", link, [(lo, hi)], eid))
            for it in e.get("first_defeat", []):
                self.add(it, "Drop", "%s · first defeat, once" % link)
                self.enemy_extra[eid].append((it, "100%", "first defeat, once per character"))
            for it in e.get("elite_first_defeat", []):
                self.add(it, "Drop", "%s · first defeat as an elite, once" % link)
                self.enemy_extra[eid].append((it, "100%", "first defeat of an elite, once per character"))
            book = e.get("pet_book")
            if book:
                note = "elites only" if book.get("elite_only") else "pet skill book"
                self.add(book["item"], "Drop", "%s · %s (%s)" % (link, pct(book.get("chance", 0)), note))
                self.enemy_extra[eid].append((book["item"], pct(book.get("chance", 0)), note))
            # Beast cores (WorldAuthority.beast_core_for): rank = (Level - 1) / 9 + 1, 2% a rank.
            if e.get("race", "beast") == "beast":
                by_core = collections.defaultdict(list)
                for lv in range(lo, hi + 1):
                    core, chance = self.beast_core(e, lv, cores)
                    if core:
                        by_core[core].append((lv, chance))
                for core in sorted(by_core):
                    levels = by_core[core]
                    rates = sorted({c for _, c in levels})
                    rate = pct(rates[0]) if len(rates) == 1 else "%s–%s" % (pct(rates[0]), pct(rates[-1]))
                    self.add(core, "Drop", "%s · %s (beast core)" % (link, rate))
                    self.enemy_extra[eid].append((core, rate, "beast core, %s" % band_text(levels[0][0], levels[-1][0])))
                if soil and hi >= int(soil.get("min_level", 19)):
                    soil_foes.append(eid)
                    self.enemy_extra[eid].append(("spirit_soil", pct(soil.get("chance", 0.01)), "Spirit Soil, a beast of Lv %d+" % soil.get("min_level", 19)))
        if soil_foes:
            self.add("spirit_soil", "Drop", "any beast of Lv %d+ · %s: %s" % (
                soil.get("min_level", 19), pct(soil.get("chance", 0.01)), ", ".join(enemy_link(d, e) for e in soil_foes)))

    def beast_core(self, e, lv, cfg):
        rank = max(1, min(9, (max(1, lv) - 1) // 9 + 1))
        if rank < int(cfg.get("min_rank", 2)):
            return "", 0
        tier = ""
        for t, band in cfg.get("tiers", {}).items():
            if band[0] <= rank <= band[1]:
                tier = t
        el = str(e.get("element", "earth"))
        if el.startswith("hollow_"):
            el = el[len("hollow_"):]
        if el in ("hollow", "none", ""):
            el = "soul" if el == "hollow" else "earth"
        core = "%s_core_%s" % (el, tier)
        if core not in self.d.items:
            core = "%s_core_%s" % (self.d.cfg("elements").get("parent", {}).get(el, el), tier)
        return (core, float(cfg.get("chance_per_rank", 0.02)) * rank) if core in self.d.items else ("", 0)

    def containers(self):
        d = self.d
        grouped = collections.defaultdict(lambda: {"rooms": set(), "levels": set()})
        for rid, r in sorted(d.rooms.items()):
            for o in r.get("objects", []):
                if "loot" in o and o.get("type") in ("jar", "crate", "chest", "wine_jar"):
                    g = grouped[(o["loot"], o["type"])]
                    g["rooms"].add(rid)
                    g["levels"].add(int(o.get("level", 1)))
        for (table, kind), g in sorted(grouped.items()):
            lv = sorted(g["levels"])
            text = "%s in %s (%s)" % (titled(kind), join_rooms(d, g["rooms"], 12), band_text(lv[0], lv[-1]))
            self.loot_users[table].append(("container", text, [(v, v) for v in lv], None))
        tower = d.cfg("tower")
        floors = collections.defaultdict(list)
        for f in d.entries("tower"):
            floors[f["loot"]].append(f)
        for table, fl in sorted(floors.items()):
            nums = sorted(int(f["floor"]) for f in fl)
            lvs = sorted(int(f["level"]) for f in fl)
            text = "Trial Tower floors %d–%d, clear or daily sweep, in %s (%s)" % (nums[0], nums[-1], d.room_name(tower.get("room", "")), band_text(lvs[0], lvs[-1]))
            self.loot_users[table].append(("tower", text, [(v, v) for v in lvs], None))
        for ev in d.entries("calendar"):
            if "loot" in ev:
                text = "%s (calendar event) in %d field rooms" % (ev.get("name", ev["id"]), len(ev.get("rooms", [])))
                self.loot_users[ev["loot"]].append(("event", text, [], None))

    def loot_tables(self):
        d = self.d
        for table, users in sorted(self.loot_users.items()):
            t = d.loot.get(table)
            if not t:
                continue
            for iid, rate, note in table_rows(d, t):
                for kind, text, levels, eid in users:
                    self.add(iid, "Drop" if kind == "enemy" else "Container", "%s · %s%s" % (text, rate, " (" + note + ")" if note else ""))
            eq = t.get("equipment", {})
            if eq and float(eq.get("chance", 0)) > 0:
                for kind, text, levels, eid in users:
                    if not levels:
                        continue
                    for g in self.grades_for(levels):
                        self.banded[g].add("%s · %s" % (text, pct(eq["chance"])))

    def grades_for(self, bands):
        """Grades an equipment roll can make for foes or chests of these Level bands (iLv = Level ±2, capped)."""
        grades = set()
        for lo, hi in bands:
            clamp = lambda v: max(1, min(self.cap, v))
            grades |= {self.d.grade_for_ilv(i) for i in range(clamp(lo - 2), clamp(hi + 2) + 1)}
        return sorted(grades, key=self.d.grade_index)

    def banded_equipment(self):
        for a in self.d.entries("artifacts"):
            if banded_eligible(self.d, a) and self.banded.get(a["grade"]):
                self.add(a["id"], "Drop", "banded equipment roll, grade %s: see [Banded equipment drops](#banded-%s)" % (titled(a["grade"]), a["grade"]))

    # --- gathering
    def gathering(self):
        d = self.d
        nodes = collections.defaultdict(lambda: collections.defaultdict(set))
        for rid, r in sorted(d.rooms.items()):
            for o in r.get("objects", []):
                t = o.get("type")
                if t in ("herb_patch", "ore_vein", "star_sight") and o.get("item"):
                    extra = " (rare)" if o.get("rare") else ""
                    nodes[o["item"]]["%s, %s rank%s" % (titled(t), o.get("rank", "any"), extra)].add(rid)
                elif t == "insect_swarm":
                    outs = o.get("outputs", [])
                    total = sum(float(x.get("weight", 1)) for x in outs) or 1.0
                    for x in outs:
                        nodes[x["item"]]["Insect swarm, %s rank, %s of catches" % (o.get("rank", "any"), pct(float(x.get("weight", 1)) / total))].add(rid)
                elif t == "beast_trail" and o.get("critter"):
                    nodes[o["critter"]]["Beast trail (snaring)"].add(rid)
                elif t == "pickup" and o.get("item"):
                    nodes[o["item"]]["Pickup%s%s" % (" \"" + o["label"] + "\"" if o.get("label") else "", times(o.get("count", 1)))].add(rid)
                elif t == "npc" and o.get("chase"):
                    for rw in o["chase"].get("rewards", []):
                        if "item" in rw:
                            self.add(rw["item"], "Reward", "catching the %s in %s%s" % (d.npc_name(o.get("npc", "")), d.room_name(rid), times(rw.get("count", 1))))
                elif t == "route_stone":
                    route = o.get("route", {})
                    for medal, rws in sorted(route.get("medal_rewards", {}).items()):
                        for rw in rws:
                            if "item" in rw:
                                self.add(rw["item"], "Reward", "%s route, %s medal, in %s%s" % (route.get("name", o["id"]), medal, d.room_name(rid), times(rw.get("count", 1))))
        for iid in sorted(nodes):
            for label in sorted(nodes[iid]):
                self.add(iid, "Gathering", "%s in %s" % (label, join_rooms(d, nodes[iid][label])))
        # Fishing: fish.json spots name the fishing_spot objects' spot.
        spots = collections.defaultdict(set)
        for rid, r in d.rooms.items():
            for o in r.get("objects", []):
                if o.get("type") == "fishing_spot":
                    spots[o.get("spot", "")].add(rid)
        fish = d.entries("fish")
        named = set(spots) | {sp for f in fish for sp in f.get("spots", []) if sp != "any"}
        for spot in sorted(named):
            here = [f for f in fish if spot in f.get("spots", []) or "any" in f.get("spots", [])]
            total = sum(float(x.get("weight", 1)) for x in here) or 1.0
            where = join_rooms(d, spots[spot]) if spots.get(spot) else "no room has this spot"
            for f in here:
                when = " (%s only)" % " and ".join(f["time"]) if f.get("time") else ""
                self.add(f["item"], "Gathering", "Fishing at %s (%s) · %s of catches%s" % (titled(spot), where, pct(float(f.get("weight", 1)) / total), when))
        for k in d.entries("beast_kings"):
            nest = k.get("nest", {})
            if nest.get("item"):
                self.add(nest["item"], "Gathering", "Beast King nest of %s in %s, one every %s min while the king lives" % (
                    enemy_link(d, k["id"], "monsters.md"), d.room_name(k.get("room", "")), nest.get("minutes", "?")))
        for ev in d.entries("calendar"):
            if ev.get("item"):
                self.add(ev["item"], "Gathering", "%s (calendar event, every %s days) in %d field rooms" % (ev.get("name", ev["id"]), ev.get("every_days", "?"), len(ev.get("rooms", []))))
        posts = d.cfg("posts")
        crafts = {p["id"]: p for p in posts.get("entries", [])}
        for iid, n in sorted(posts.get("nodes", {}).items()):
            craft = crafts.get(n.get("craft"), {}).get("name", titled(n.get("craft", "")))
            if n.get("side"):
                continue
            self.add(iid, "Gathering", "Post: %s, gate Lv %s" % (craft, n.get("gate", 1)))
        for craft, side in sorted(posts.get("rules", {}).get("side_drops", {}).items()):
            name = crafts.get(craft, {}).get("name", titled(craft))
            self.add(side["item"], "Gathering", "Post: %s side drop, one every %s gathers" % (name, side.get("every", "?")))
        for iid, n in sorted(posts.get("nodes", {}).items()):
            if n.get("side") and iid not in [s["item"] for s in posts.get("rules", {}).get("side_drops", {}).values()]:
                craft = crafts.get(n.get("craft"), {}).get("name", titled(n.get("craft", "")))
                where = ""
                if n.get("craft") == "rites":
                    where = " at the altars in " + join_rooms(d, posts.get("altars", {}).keys())
                self.add(iid, "Gathering", "Post: %s, side catch%s" % (craft, where))
        for rid, outs in sorted(posts.get("swarms", {}).items()):
            total = sum(float(x.get("weight", 1)) for x in outs) or 1.0
            for x in outs:
                self.add(x["item"], "Gathering", "Post: Insect Netting in %s · %s of catches" % (d.room_name(rid), pct(float(x.get("weight", 1)) / total)))
        for rid, tr in sorted(posts.get("trails", {}).items()):
            self.add(tr["critter"], "Gathering", "Post: Beast Snaring in %s" % d.room_name(rid))
        for cp in posts.get("bench", {}).get("components", []):
            self.add(cp["item"], "Crafting", "Apprentice Bench (posts): %s work a piece, from craft Lv %s" % (cp.get("progress", "?"), cp.get("gate", 1)))

    def garden(self):
        d = self.d
        g = d.cfg("garden")
        seeds = g.get("seeds", {})
        for fam, ages in sorted(g.get("families", {}).items()):
            seed = seeds.get(fam)
            for age, iid in sorted(ages.items(), key=lambda kv: int(kv[0])):
                how = "grown from %s" % item_link(d, seed) if seed else "no seed: a transplanted plant"
                self.add(iid, "Garden", "Garden bed, %s, harvested at %s years" % (how, age))
        for fam in sorted(g.get("harvest_seeds", [])):
            if seeds.get(fam):
                self.add(seeds[fam], "Garden", "a harvest of %s in a garden bed returns seeds · %s" % (titled(fam), pct(g.get("seed_chance", 0.1))))

    # --- crafting
    def crafting(self):
        d = self.d
        for r in d.entries("recipes"):
            ins = ", ".join("%s ×%d" % (d.item_name(i["item"]), i.get("count", 1)) for i in r.get("inputs", []))
            how = "known by default" if r.get("default") else ("a hidden recipe" if r.get("hidden") else "")
            for o in r.get("outputs", []):
                self.add(o["item"], "Crafting", "Recipe `%s` (%s, %s): %s%s%s" % (
                    r["id"], titled(r.get("craft", "")), titled(r.get("grade", "")), ins, times(o.get("count", 1)), "; " + how if how else ""))
        posts = d.cfg("posts")
        for s in posts.get("salts", []):
            ins = ", ".join("%s ×%d" % (d.item_name(i["item"]), i.get("qty", 1)) for i in s.get("inputs", []))
            self.add(s["id"], "Crafting", "Post calcination: %s" % ins)
        for p in d.entries("professions"):
            res = p.get("results", [])
            total = sum(float(x.get("weight", 1)) for x in res) or 1.0
            for x in res:
                self.add(x["item"], "Crafting", "%s (profession) · %s of results%s" % (p.get("name", p["id"]), pct(float(x.get("weight", 1)) / total), times(x.get("count", 1))))
            for b in p.get("blueprints", []):
                for y in b.get("yield", []):
                    self.add(y["item"], "Crafting", "%s: a %s works %s an hour" % (p.get("name", p["id"]), b.get("name", b["id"]), y.get("per_hour", "?")))
        for it in d.items.values():
            app = it.get("appraise", [])
            total = sum(float(x.get("weight", 1)) for x in app) or 1.0
            for x in app:
                self.add(x["item"], "Crafting", "appraising a %s · %s%s" % (item_link(d, it["id"]), pct(float(x.get("weight", 1)) / total), times(x.get("count", 1))))
            if it.get("restores"):
                self.add(it["restores"], "Crafting", "restoring a %s at the forge" % item_link(d, it["id"]))
        for ch in d.entries("legendary_chains"):
            rest = ch.get("restore", {})
            pieces = ", ".join(item_link(d, p["item"]) for p in ch.get("pieces", []))
            rank = titled(rest.get("rank", ""))
            self.add(ch.get("weapon", ""), "Crafting", "legendary chain %s: its pieces (%s) made whole by %s %s smith" % (
                ch.get("name", ch["id"]), pieces, "an" if rank[:1] in "AEIOU" else "a", rank))
        for s in d.entries("salvage"):
            for x in s.get("returns", []):
                self.add(x["item"], "Crafting", "salvaging %s-grade equipment%s" % (titled(s["id"]), times(x.get("count", 1))))

    # --- shops
    def shops(self):
        d = self.d
        sellers = collections.defaultdict(set)
        for nid, n in d.npcs.items():
            for s in n.get("services", []):
                if s.startswith("shop:"):
                    sellers[s[5:]].add(nid)
        for sid in sorted(d.shops):
            sh = d.shops[sid]
            who = []
            for nid in sorted(sellers.get(sid, [])):
                rooms = sorted(d.npc_rooms.get(nid, []))
                who.append("%s%s" % (d.npc_name(nid), " in " + join_rooms(d, rooms) if rooms else ""))
            where = "%s (%s)" % (sh.get("name", sid), "; ".join(who) if who else "no NPC offers this shop")
            for s in sh.get("stock", []):
                cur = d.currency_name(s.get("currency", sh.get("currency", "silver_tael")))
                price = "%s %s" % (s["price"], cur) if "price" in s else "at list price in %s" % cur
                extra = []
                if s.get("daily"):
                    extra.append("%d a day" % s["daily"])
                if s.get("learn"):
                    extra.append("teaches recipe `%s`" % s["learn"])
                if s.get("requires"):
                    extra.append("needs " + req_text(d, s["requires"]))
                self.add(s["item"], "Shop", "%s · %s%s" % (where, price, "; " + "; ".join(extra) if extra else ""))
            rot = sh.get("rotation", {})
            for s in rot.get("pool", []):
                self.add(s["item"], "Shop", "%s · daily rotation (%s of %d)" % (where, rot.get("count", 1), len(rot.get("pool", []))))
        auc = d.cfg("auction")
        for label, pool in (("Auction Pavilion (Azure Expanse)", auc.get("pool", [])), ("Auction Day on Market Street (valley)", auc.get("valley", {}).get("pool", []))):
            total = sum(float(x.get("weight", 1)) for x in pool) or 1.0
            for x in pool:
                if "item" in x:
                    note = "; teaches recipe `%s`" % x["learn"] if x.get("learn") else ""
                    self.add(x["item"], "Shop", "%s lot%s, opening bid %s · %s of lots%s" % (label, times(x.get("count", 1)), x.get("start", "?"), pct(float(x.get("weight", 1)) / total), note))

    # --- reward lists that are not effects
    def rewards(self):
        d = self.d
        for ex in d.entries("expeditions"):
            for x in ex.get("rewards", []):
                if "item" in x:
                    note = []
                    if x.get("chance"):
                        note.append(pct(x["chance"]))
                    if x.get("min_hours"):
                        note.append("%s h or longer" % x["min_hours"])
                    self.add(x["item"], "Reward", "Expedition %s (%s h)%s%s" % (ex.get("name", ex["id"]), "/".join(str(h) for h in ex.get("hours", [])), times(x.get("count", 1)), " · " + ", ".join(note) if note else ""))
        tide = d.cfg("expeditions").get("beast_tide", {})
        rw = tide.get("rewards", {})
        where = "Beast Tide at %s" % d.room_name(tide.get("room", ""))
        if rw.get("egg"):
            self.add(rw["egg"], "Reward", where)
        if rw.get("stag_egg"):
            self.add(rw["stag_egg"], "Reward", "%s, from %s" % (where, d.realm_name(rw.get("stag_realm", ""))))
        if rw.get("soil"):
            self.add("spirit_soil", "Reward", where + times(rw["soil"]))
        for el in TIDE_CORE_ELEMENTS:
            for tier, levels in TIDE_CORE_TIERS:
                self.add("%s_core_%s" % (el, tier), "Reward", "%s, one of %s beast cores of a random element at the holder's tier (%s)" % (
                    where, rw.get("cores", 3), levels))
        arena = d.cfg("beast_arena")
        for x in arena.get("rewards", []):
            if x.get("item"):
                self.add(x["item"], "Reward", "Beast Arena weekly rank %s" % "–".join(str(v) for v in sorted(set(x.get("ranks", [])))))
        grove = arena.get("grove", {})
        where = "Beast Grove trial in %s" % d.room_name(grove.get("room", ""))
        if grove.get("first"):
            self.add(grove["first"], "Reward", where + ", first clear")
        pool = grove.get("pool", [])
        total = sum(float(x.get("weight", 1)) for x in pool) or 1.0
        for x in pool:
            self.add(x["item"], "Reward", "%s · %s of rewards" % (where, pct(float(x.get("weight", 1)) / total)))
        for ev in d.entries("calendar"):
            for place, x in sorted(ev.get("rewards", {}).items()) if isinstance(ev.get("rewards"), dict) else []:
                if isinstance(x, dict) and x.get("item"):
                    self.add(x["item"], "Reward", "%s (calendar event), place %s%s" % (ev.get("name", ev["id"]), place, times(x.get("count", 1))))
        for s in d.entries("sects"):
            if s.get("token"):
                self.add(s["token"], "Reward", "joining the %s" % s.get("name", s["id"]))

    # --- effects anywhere in data
    def effects(self):
        """Every grant effect, mail attachment and sect-token upgrade anywhere in data/, walked whole."""
        d = self.d
        labels = {
            "quests": lambda q: "Quest %s (%s%s)" % (q.get("name", q["id"]), q.get("kind", ""), ", from " + d.npc_name(q["giver"]) if q.get("giver") else ""),
            "unlocks": lambda u: "Unlock: %s" % d.unlock_name(u["id"]),
            "activity": lambda a: "Daily activity chest at %s points" % a.get("points", "?"),
            "npcs": lambda n: n.get("name", n["id"]),
        }
        for table in sorted(d.t):
            data = d.t[table]
            if not isinstance(data, dict):
                continue
            for key in sorted(data):
                if key == "entries":
                    for e in data["entries"]:
                        if table == "guilds":
                            for r in e.get("ranks", []):
                                self.walk(r, "%s, rank %s" % (e.get("name", e["id"]), titled(r.get("id", ""))))
                            continue
                        label = labels[table](e) if table in labels else "%s: %s" % (titled(table), e.get("name", e.get("id", "")))
                        for part in sorted(e):
                            if part in PART_LABELS and isinstance(e[part], dict) and table == "npcs":
                                for level, fx in sorted(e[part].items()):
                                    self.walk(fx, "%s at heart %s" % (e.get("name", e["id"]), level))
                            else:
                                self.walk(e[part], label + PART_LABELS.get(part, ""))
                elif table == "account_rules" and key == "skip_start":
                    self.walk(data[key], "Skip-the-Prologue start")
                elif table == "karma" and key == "debts":
                    for debt, v in sorted(data[key].items()):
                        self.walk(v, "Karma debt %s" % debt)
                else:
                    self.walk(data[key], "%s (%s)" % (titled(table), key.replace("_", " ")))
        for tid in sorted(d.dialogue):
            self.walk(d.dialogue[tid], "Dialogue with %s" % d.npc_name(tid))
        for rid in sorted(d.rooms):
            r = d.rooms[rid]
            for key in sorted(r):
                if key == "objects":
                    for o in r["objects"]:
                        self.walk(o, "%s in %s" % (o.get("label", titled(o.get("type", ""))), d.room_name(rid)))
                elif key == "event":
                    self.walk(r[key], "Room event in %s" % d.room_name(rid))
                else:
                    self.walk(r[key], d.room_name(rid))

    def walk(self, node, label):
        d = self.d
        if isinstance(node, dict):
            if node.get("kind") in GRANT_KINDS and node.get("item"):
                note = times(node.get("count", 1))
                if node["kind"] == "grant_equipment":
                    note += " (iLv %s, %s)" % (node.get("ilv", "?"), node.get("quality", "common"))
                self.add(node["item"], "Reward", label + note)
            if node.get("kind") == "upgrade_sect_token":
                # GameAuthority: the training sect's token becomes its Elder's token (`<sect>_token` -> `<sect>_elder_token`).
                for sect in d.entries("sects"):
                    if sect.get("token"):
                        self.add(sect["token"].replace("_token", "_elder_token"), "Reward", "%s: the %s's token becomes an Elder's" % (label, sect.get("name", sect["id"])))
            if isinstance(node.get("attachments"), list):
                mail = node.get("mail", node.get("template", ""))
                sender = next((m.get("from", "") for m in d.entries("mail_templates") if m["id"] == mail), "")
                for a in node["attachments"]:
                    if isinstance(a, dict) and a.get("item"):
                        self.add(a["item"], "Mail", "%s: a letter%s%s" % (label, " from " + sender if sender else "", times(a.get("count", 1))))
            for k in sorted(node):
                if k != "attachments":
                    self.walk(node[k], label)
        elif isinstance(node, list):
            for v in node:
                self.walk(v, label)


def spawn_levels(sp):
    """A room spawn's Level band: `level` is [lo, hi] (or a single Level)."""
    lv = sp.get("level", 1)
    return (int(lv[0]), int(lv[-1])) if isinstance(lv, list) else (int(lv), int(lv))


def banded_eligible(d, a):
    """LootRules.is_banded: the bases the equipment roll picks from."""
    return not (a.get("set") or a.get("relic") or a.get("legend") or a.get("imitation") or a.get("named") or a.get("pet_gear")
                or a.get("slot") in d.drop().get("pool_skip_slots", []))


def table_rows(d, t):
    """(item, rate text, note) for every item row of a loot table, as LootRules.roll draws them."""
    rows = []
    for g in t.get("guaranteed", []):
        rows.append((g["item"], pct(g.get("chance", 1.0)) + times(g.get("count", [1, 1])), "guaranteed"))
    for grp in t.get("groups", []):
        picks = grp.get("pick", [])
        total = sum(float(p.get("weight", 1)) for p in picks) or 1.0
        for p in picks:
            share = float(p.get("weight", 1)) / total
            note = "group %s, weight %s of %s" % (pct(grp.get("chance", 1.0)), num(p.get("weight", 1)), num(total)) if len(picks) > 1 else "group"
            rows.append((p["item"], pct(float(grp.get("chance", 1.0)) * share) + times(p.get("count", [1, 1])), note))
    for r in t.get("rare", []):
        rows.append((r["item"], pct(r.get("chance", 0)) + times(r.get("count", [1, 1])), "rare"))
    for q in t.get("quest_drops", []):
        rows.append((q["item"], pct(q.get("chance", 1.0)) + times(q.get("count", [1, 1])), "only during " + d.quest_name(q.get("quest", ""))))
    for key, note in (("named", "named"), ("elite_named", "named, elites only")):
        for r in t.get(key, []):
            rows.append((r["item"], pct(r.get("chance", 0)), note))
    for r in t.get("lost", []):   # P13a: a lost art's manual, never in the random roll (technique_plan §5.3)
        rows.append((r["item"], pct(r.get("chance", 0)), "lost art, until found" + (", sure by kill %d" % r["pity"] if r.get("pity") else "")))
    return rows


def item_marks(it):
    src = it.get("source")
    vals = src if isinstance(src, list) else [src] if src else []
    return sorted(v for v in vals if v in MARKS)


# ------------------------------------------------------------------ items page
def item_group(it):
    if it.get("type") == "equipment":
        return "equipment: " + it.get("slot", "")
    return it.get("type", "other")


def group_title(g):
    if g.startswith("equipment: "):
        return "Equipment · " + titled(g[len("equipment: "):])
    return titled(g)


def item_stats(d, it):
    out = []
    eq = d.cfg("stats").get("equipment", {})
    poly = lambda s, x: float(s.get("a", 0)) + float(s.get("b", 0)) * x + float(s.get("c", 0)) * x * x
    ilv = float(it.get("ilv", 1))
    if it.get("type") == "equipment":
        slot = it.get("slot")
        if slot == "weapon":
            out.append("Weapon Attack %s at iLv %d, Common quality (`stats.json` equipment.weapon_attack)" % (num(round(poly(eq.get("weapon_attack", {}), ilv), 1)), ilv))
        elif slot in eq.get("slot_share", {}):
            arm = poly(eq.get("armour_defence", {}), ilv) * float(eq["slot_share"][slot])
            out.append("Physical Defense %s at iLv %d, Common quality (armour_defence × %s slot share)" % (num(round(arm, 1)), ilv, slot))
        for key in ("family", "energy_type", "sockets", "appearance", "dye"):
            if it.get(key) not in (None, "", "none", 0):
                out.append("%s %s" % (titled(key), it[key]))
        if it.get("set"):
            out.append("set [%s](#set-%s)" % (titled(it["set"]), it["set"]))
        if it.get("named"):
            out.append(named_text(it["named"]))
        for key in ("legend", "imitation", "spirit", "gourd", "furnace", "pet_gear"):
            if it.get(key):
                v = {k: x for k, x in it[key].items() if k != "barks"} if isinstance(it[key], dict) else it[key]   # a spirit's lines are not stats
                out.append("%s: %s" % (titled(key), json.dumps(v, sort_keys=True)))
        if it.get("resist"):
            out.append("resists %s" % ", ".join(it["resist"]))
        if it.get("unique"):
            out.append("unique")
        return out
    for e in it.get("use", []):
        out.append(effect_text(d, e))
    if it.get("use_action"):
        out.append("used as: %s" % titled(it["use_action"]))
    for key in ("core", "pill", "food", "herb", "seed", "raw", "talisman", "treasure", "jade", "bath", "flight", "draught", "post",
                "egg_species", "egg_rarity", "burst", "support", "chart", "vessel", "region", "nature", "roles", "pet_book",
                "beast_bag", "hour_incense", "soul_effect", "method_conversion", "then", "family", "tool"):
        if key in it and it[key] not in ("", None, [], {}):
            v = it[key]
            out.append("%s: %s" % (titled(key), json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else num(v)))
    return out


def named_text(nm):
    """A named piece's tags (item_plan §2.1): archetype, zone, element, path and fixed affixes."""
    parts = ["named: %s, %s" % (titled(nm.get("archetype", "")), titled(nm.get("zone", "")))]
    if nm.get("element"):
        parts.append("element %s (+2%% %s power)" % (titled(nm["element"]), nm["element"]))
    if nm.get("path"):
        parts.append("path %s" % titled(nm["path"]))
    for fx in nm.get("fixed", []):
        parts.append("fixed %s %s" % (titled(fx["stat"]), bonus_value(fx)))
    return ", ".join(parts)


def bonus_value(b):
    """A stat modifier's value as the game shows it: a share as a percentage, a count as a number."""
    v = float(b.get("value", 0))
    return ("+%s%%" % num(round(v * 100, 2))) if b.get("op") != "flat" or abs(v) < 1 else "+%s" % num(v)


def sets_section(d):
    """Every set: its archetype, tier, element and path, its pieces, and its bonuses (a mechanic by its values)."""
    lines = ['<a id="sets"></a>', "", "## Sets", "",
             "A set's bonuses count the pieces worn (a set's weapons share the weapon slot); while the wearer holds the set's "
             "path its 2-piece bonus counts double (`StatRules.set_modifiers`). A bonus with a mechanic is read by the rule that "
             "owns it (`StatRules.set_flag`).", ""]
    for st in d.entries("sets"):
        lines += ['<a id="set-%s"></a>' % st["id"], "", "### %s" % titled(st["id"]), "",
                  "- **Archetype**: %s · tier %s%s%s" % (titled(st.get("archetype", "")), st.get("tier", "?"),
                                                         " · element %s" % titled(st["element"]) if st.get("element") else "",
                                                         " · path %s" % titled(st["path"]) if st.get("path") else ""),
                  "- **Pieces**: " + ", ".join(item_link(d, p) for p in st.get("pieces", []))]
        for need in sorted(st.get("bonuses", {}), key=int):
            rows = []
            for b in st["bonuses"][need]:
                if "flag" in b:
                    rows.append("%s (%s)" % (titled(b["flag"]), json.dumps({k: v for k, v in b.items() if k != "flag"}, sort_keys=True)))
                else:
                    cond = " (%s)" % titled(b["condition"]["element"]) if b.get("condition", {}).get("element") else ""
                    rows.append("%s %s%s" % (bonus_value(b), titled(b["stat"]), cond))
            lines.append("- **%s pieces**: %s" % (need, "; ".join(rows)))
        lines.append("")
    return lines


def item_requirement(d, it):
    parts = []
    if it.get("requires"):
        parts.append(req_text(d, it["requires"]))
    if it.get("attribute_req"):
        parts.append(", ".join("%s %s" % (titled(k), v) for k, v in sorted(it["attribute_req"].items())))
    if isinstance(it.get("post"), dict) and it["post"].get("level_req"):
        parts.append("%s level %s" % (titled(it["post"].get("craft", "")), it["post"]["level_req"]))
    if it.get("hatch_realm"):
        parts.append("hatches at %s" % d.realm_name(it["hatch_realm"]))
    if it.get("use_limit"):
        parts.append("use limit %s" % json.dumps(it["use_limit"], sort_keys=True))
    return "; ".join(p for p in parts if p)


def icon_link(d, it):
    path = d.icons.get(it.get("icon", ""), "")
    if not path.startswith("res://"):
        return ""
    return "![%s](../../%s)" % (it.get("name", it["id"]), path[len("res://"):])


def items_page(d, s):
    groups = collections.defaultdict(list)
    for it in d.items.values():
        groups[item_group(it)].append(it)
    order = sorted(groups, key=lambda g: (0 if g.startswith("equipment") else 1, g))
    sourced = sum(1 for i in d.items if s.by_item.get(i))
    marked = sum(1 for i in d.items if not s.by_item.get(i) and item_marks(d.items[i]))
    lines = ["# Item Wiki", "",
             "Generated by `tools/dev/wiki.py` from `data/` (never edit by hand: `python3 tools/data/build_data.py` rewrites it).",
             "",
             "%d items: %d in `data/items.json` and %d pieces of equipment in `data/artifacts.json`. "
             "%d have a source in the data, %d carry an explicit source mark, %d have neither." % (
                 len(d.items), len(d.entries("items")), len(d.entries("artifacts")), sourced, marked, len(d.items) - sourced - marked),
             "",
             "Rates are per kill, per open or per catch at the base Drop Rate (Drop Rate raises group, rare and equipment rolls). "
             "A group rolls once and then picks one row by weight, so a row's rate is the group chance times its weight share. "
             "Quest-only items drop only while their quest still needs them. An elite of a normal kind rolls its table twice, "
             "and every species' first kill rolls it once more. Marks: " +
             "; ".join("`%s`: %s" % (k, v) for k, v in sorted(MARKS.items())) + ".",
             "", "## Contents", ""]
    for g in order:
        lines.append("- [%s](#group-%s) (%d)" % (group_title(g), re.sub(r"[^a-z0-9]+", "-", g).strip("-"), len(groups[g])))
    lines.append("- [Sets](#sets)")
    lines.append("- [Banded equipment drops](#banded-equipment-drops)")
    lines.append("")
    for g in order:
        lines += ['<a id="group-%s"></a>' % re.sub(r"[^a-z0-9]+", "-", g).strip("-"), "", "## %s (%d)" % (group_title(g), len(groups[g])), ""]
        for it in sorted(groups[g], key=lambda i: (d.grade_index(i.get("grade", "")), int(i.get("ilv", 0)), i.get("name", ""), i["id"])):
            lines += item_entry(d, s, it)
    lines += sets_section(d)
    lines += ['<a id="banded-equipment-drops"></a>', "", "## Banded equipment drops", ""] + drop_rules_text(d) + [""]
    for g in sorted(s.banded, key=d.grade_index):
        pieces = sorted((a for a in d.entries("artifacts") if a.get("grade") == g and banded_eligible(d, a)), key=lambda a: a["id"])
        lines += ['<a id="banded-%s"></a>' % g, "", "### %s (%d pieces)" % (titled(g), len(pieces)), "",
                  "Pieces: " + (", ".join(item_link(d, a["id"]) for a in pieces) or "none"), "", "Rolled by:", ""]
        for who in sorted(s.banded[g]):
            lines.append("- " + who)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def drop_rules_text(d):
    """The equipment roll (LootRules, grades.json `drop`) in words."""
    dr = d.drop()
    order = d.cfg("grades").get("quality_order", [])
    floors = []
    for floor, shares in sorted(dr.get("quality", {}).items(), key=lambda kv: order.index(kv[0])):
        floors.append("from %s: %s" % (titled(floor), ", ".join("%s %s" % (pct(v), titled(order[i])) for i, v in enumerate(shares) if v)))
    ex = dr.get("elite_extra", {})
    return ["A loot table's equipment roll makes a piece at the foe's or chest's Level ±%d, capped at %d (the top Level of the highest "
            "grade with banded bases). Once the Weapons system is open %s of rolls make a weapon (%s of those in the family in hand), "
            "the rest one of the four armour slots, among the banded pieces of that iLv's grade: none named, in a set, a relic, a "
            "legend, an imitation or pet gear, and no %s (`LootRules.make_equipment`)." % (
                int(dr.get("level_spread", 2)), d.drop_level_cap(), pct(dr.get("weapon_share", 0)), pct(dr.get("family_bias", 0)),
                ", ".join(titled(x) for x in dr.get("pool_skip_slots", []))), "",
            "Quality starts at the table's floor (Fortune moves the roll toward the best): %s. A normal kind spawned as an elite has "
            "one more roll at %s from %s. A named row drops its piece at the source's floor, at least %s." % (
                "; ".join(floors), pct(ex.get("chance", 0)), titled(ex.get("min_quality", "")), titled(dr.get("named_floor", "")))]


def item_entry(d, s, it):
    iid = it["id"]
    kind = "%s, %s" % (titled(it.get("type", "")), it.get("slot")) if it.get("type") == "equipment" else titled(it.get("type", ""))
    out = ['<a id="item-%s"></a>' % iid, "", "### %s %s" % (icon_link(d, it), it.get("name", iid)), "",
           "`%s` · %s · %s · iLv %s · stack %s" % (iid, kind, titled(it.get("grade", "")), it.get("ilv", "?"), it.get("stack", 1)), ""]
    if it.get("desc"):
        out.append("> " + it["desc"])
        out.append("")
    stats = item_stats(d, it)
    if stats:
        out.append("- **%s**: %s" % ("Stats" if it.get("type") == "equipment" else "Effect", "; ".join(stats)))
    req = item_requirement(d, it)
    if req:
        out.append("- **Requires**: " + req)
    flags = []
    if it.get("sell") is False:
        flags.append("cannot be sold")
    if it.get("quest_item"):
        flags.append("quest item")
    if it.get("value_override") is not None:
        flags.append("value %s" % it["value_override"])
    if flags:
        out.append("- **Notes**: " + ", ".join(flags))
    srcs = sorted(s.by_item.get(iid, []))
    marks = item_marks(it)
    if srcs:
        out.append("- **Sources**:")
        for _, ch, text in srcs:
            out.append("  - %s: %s" % (ch, text))
    if marks:
        out.append("- **Source mark**: " + "; ".join("`%s` (%s)" % (m, MARKS[m]) for m in marks))
    if not srcs and not marks:
        out.append("- **Sources**: none found in the data")
    out.append("")
    return out


# ------------------------------------------------------------------ monsters page
ENEMY_KEYS = ("enemy", "foes", "guardian", "boss", "summon", "opponent", "target", "hunter", "win_on_kill", "heart_demons",
              "disciple", "warden", "rivals", "duel", "king", "king_alive")


def enemy_appearances(d):
    """enemy -> {(where, how)} beyond ordinary room spawns (events, trials, tower, tides, summons...)."""
    seen = collections.defaultdict(set)

    def walk(node, label, key=""):
        if isinstance(node, dict):
            for k in sorted(node):
                if k not in ("objective", "objectives", "match"):   # a kill order or a karma trigger, not a place it appears
                    walk(node[k], label, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, label, key)
        elif isinstance(node, str) and key in ENEMY_KEYS and node in d.enemies:
            seen[node].add("%s (%s)" % (label, key.replace("_", " ")))

    for rid in sorted(d.rooms):
        r = d.rooms[rid]
        for k in ("event", "ambush"):
            if k in r:
                walk(r[k], "%s in %s" % ("room event" if k == "event" else "ambush", d.room_name(rid)))
        for o in r.get("objects", []):
            what = "%s in %s" % (o.get("label", titled(o.get("type", ""))).lower(), d.room_name(rid))
            if isinstance(o.get("guardian"), dict) and o["guardian"].get("enemy") in d.enemies:
                seen[o["guardian"]["enemy"]].add("guards the " + what)
            if o.get("type") != "npc":
                walk({k: v for k, v in o.items() if k not in ("king", "guardian")}, what[0].upper() + what[1:])
    for e in d.entries("enemies"):
        for a in e.get("attacks", []) + e.get("phases", []):
            if a.get("summon") in d.enemies:
                seen[a["summon"]].add("summoned by %s" % enemy_link(d, e["id"], ""))
    floors = collections.defaultdict(set)
    for f in d.entries("tower"):
        for foe in f.get("foes", []):
            floors[(foe, "foe")].add(int(f["floor"]))
        if f.get("guardian"):
            floors[(f["guardian"], "guardian")].add(int(f["floor"]))
    for (foe, role), nums in sorted(floors.items()):
        seen[foe].add("Trial Tower %s, floor%s %s" % (role, "s" if len(nums) > 1 else "", ", ".join(str(n) for n in sorted(nums))))
    tide = d.cfg("expeditions").get("beast_tide", {})
    walk(tide.get("waves", []), "Beast Tide at %s (wave)" % d.room_name(tide.get("room", "")))
    grove = d.cfg("beast_arena").get("grove", {})
    walk(grove.get("waves", []), "Beast Grove trial in %s (wave)" % d.room_name(grove.get("room", "")))
    skip = {"enemies", "loot_tables", "npcs", "quests", "pets", "eggs", "codex", "rankings", "achievements", "mission_templates",
            "beast_kings", "tower", "expeditions", "beast_arena"}
    for table in sorted(d.t):
        if table in skip or not isinstance(d.t[table], dict):
            continue
        for key in sorted(d.t[table]):
            if key == "entries":
                for e in d.t[table]["entries"]:
                    walk(e, "%s: %s" % (titled(table), e.get("name", e.get("id", ""))))
            else:
                walk(d.t[table][key], "%s (%s)" % (titled(table), key.replace("_", " ")))
    for q in d.entries("quests"):
        for o in q.get("objectives", []):
            if o.get("opponent") in d.enemies:
                seen[o["opponent"]].add("spar in quest %s" % q.get("name", q["id"]))
    for r in d.entries("rankings"):
        if r.get("enemy") in d.enemies:
            seen[r["enemy"]].add("the rankings: %s" % r.get("name", r["id"]))
    for comp in d.entries("companions"):   # RelationsAuthority: a friendly duel spars `duel_<companion>`
        if "duel_" + comp["id"] in d.enemies:
            seen["duel_" + comp["id"]].add("a friendly duel with the companion %s, from %s hearts" % (comp.get("name", comp["id"]), d.cfg("bonds").get("duel_hearts", 3)))
    for k in d.entries("beast_kings"):
        if k["id"] in d.enemies:
            seen[k["id"]].add("Beast King of %s, in %s" % (d.zone_name(k.get("zone", "")), d.room_name(k.get("room", ""))))
    return seen


def enemy_spawns(d, eid):
    rows = []
    for rid in sorted(d.rooms):
        r = d.rooms[rid]
        for sp in r.get("spawns", []):
            if sp.get("enemy") != eid:
                continue
            tags = [t.replace("_", " ") for t in ("elite", "boss", "field_boss", "mini_boss", "wild_pet") if sp.get(t)]
            if sp.get("requires"):
                tags.append("needs " + req_text(d, sp["requires"]))
            if sp.get("calendar"):
                tags.append("calendar %s" % sp["calendar"])
            if sp.get("king_alive"):
                tags.append("while %s lives" % d.enemy_name(sp["king_alive"]))
            rows.append((d.zone_name(r.get("zone", "")), d.regions.get((r.get("zone"), r.get("region")), titled(r.get("region", ""))),
                         r.get("name", rid), spawn_levels(sp), sp.get("max", 1), sp.get("respawn_s"), tags))
    return sorted(rows, key=lambda x: (str(x[0]), str(x[1]), str(x[2]), x[3]))


def home_zone(d, eid):
    best = None
    for rid, r in d.rooms.items():
        for sp in r.get("spawns", []):
            if sp.get("enemy") == eid:
                key = (spawn_levels(sp)[0], r.get("zone", ""))
                best = key if best is None or key < best else best
    return best[1] if best else ""


def monsters_page(d, s):
    seen = enemy_appearances(d)
    zone_order = [z["id"] for z in d.entries("zones")]
    groups = collections.defaultdict(list)
    for eid in d.enemies:
        groups[home_zone(d, eid)].append(eid)
    order = [z for z in zone_order if z in groups] + ([""] if "" in groups else [])
    mob = d.cfg("stats").get("mob", {})
    lines = ["# Monster & Drops Wiki", "",
             "Generated by `tools/dev/wiki.py` from `data/` (never edit by hand: `python3 tools/data/build_data.py` rewrites it).", "",
             "%d enemies in `data/enemies.json`, %d loot tables in `data/loot_tables.json`. Each foe is listed under the zone of its "
             "lowest-level room spawn; foes that no room spawns (trials, spars, events, summons) come last." % (len(d.enemies), len(d.loot)), "",
             "Stats are the `stats.json` mob templates at the band's lowest and highest Level for the foe's role, times its own "
             "multipliers (an elite spawn of a normal foe uses the elite role). Rates are per kill at the base Drop Rate; an elite of "
             "a normal kind rolls its table twice and has one more equipment roll at %s from %s, and each species' first kill rolls "
             "the table once more. Beast cores (2%% a beast rank, rank 2 and up), Spirit Soil and pet books roll outside the table." % (
                 pct(d.drop().get("elite_extra", {}).get("chance", 0)), titled(d.drop().get("elite_extra", {}).get("min_quality", ""))), "",
             "## Contents", ""]
    for z in order:
        lines.append("- [%s](#zone-%s) (%d)" % (d.zone_name(z) if z else "Not spawned in rooms", z or "none", len(groups[z])))
    lines.append("")
    for z in order:
        lines += ['<a id="zone-%s"></a>' % (z or "none"), "", "## %s (%d)" % (d.zone_name(z) if z else "Not spawned in rooms", len(groups[z])), ""]
        for eid in sorted(groups[z], key=lambda e: (s.enemy_levels(e)[0], d.enemies[e].get("name", ""), e)):
            lines += enemy_entry(d, s, eid, seen.get(eid, set()), mob)
    return "\n".join(lines).rstrip("\n") + "\n"


def mob_stats(d, e, lv, mob, role=None):
    """StatRules.mob_stats: the par tables by Level (P12), a boss's par time, armour times the Level's Might."""
    poly = lambda sp, x: float(sp.get("a", 0)) + float(sp.get("b", 0)) * x + float(sp.get("c", 0)) * x * x
    at = lambda table, fallback: float(table[max(0, min(lv, len(table) - 1))]) if table else fallback
    stats = d.cfg("stats")
    r = mob.get("roles", {}).get(role or e.get("role", "normal"), {"hp": 1, "attack": 1, "defence": 0.8})
    hp = at(mob.get("hp_table", []), poly(mob.get("hp", {}), lv)) * float(r["hp"]) * float(e.get("hp_mult", 1.0))
    if "par_s" in e:
        par = stats.get("par", {}).get("table", [])
        hp = float(par[max(0, min(lv, len(par) - 1))]["dps"]) * float(e["par_s"]) * float(e.get("hp_mult", 1.0))
    if "hp_override" in e:
        hp = float(e["hp_override"])
    atk = at(mob.get("attack_table", []), poly(mob.get("attack", {}), lv)) * float(r["attack"]) * float(e.get("attack_mult", 1.0))
    might = at(stats.get("might", {}).get("table", []), 1.0)
    arm = poly(stats.get("equipment", {}).get("armour_defence", {}), lv) * float(r["defence"]) * float(e.get("defence_mult", 1.0)) * might
    acc = poly(mob.get("accuracy", {}), lv)
    return "HP %d, Attack %d, Physical Defense %d, Accuracy %d" % (round(hp), round(atk), round(arm), round(acc))


def sheet_text(d, e):
    art = e.get("art", {})
    if art.get("creature"):
        c = d.cfg("creature_art").get(art["creature"], {})
        f = c.get("file", "")
        path = f[len("res://"):] if f.startswith("res://") else f
        return "creature sheet `%s` ([%s](../../%s), %s px cells%s)" % (art["creature"], path, path, c.get("cell", "?"), ", flying" if c.get("flying") else "") if path else "creature sheet `%s` (not in creature_art.json)" % art["creature"]
    if art.get("avatar"):
        av = art["avatar"]
        if not isinstance(av, dict):
            return "avatar `%s` (drawn with the %s's own parts)%s" % (av, av, "; tint %s" % art["tint"] if art.get("tint") else "")
        parts = ", ".join("%s %s" % (k.replace("_", " "), av[k]) for k in sorted(av) if k != "name")
        return "avatar parts (%s)%s" % (parts, "; tint %s" % art["tint"] if art.get("tint") else "")
    return "none"


def enemy_entry(d, s, eid, seen, mob):
    e = d.enemies[eid]
    lo, hi = s.enemy_levels(eid)
    lv = e.get("level", [lo, hi])
    head = "`%s` · %s · %s · %s · %s · energy %s" % (eid, titled(e.get("role", "")), band_text(lo, hi), titled(e.get("element", "")), e.get("race", ""), e.get("energy", "none"))
    if e.get("beast_rank"):
        head += " · beast rank %s" % e["beast_rank"]
    out = ['<a id="enemy-%s"></a>' % eid, "", "### %s" % e.get("name", eid), "", head, ""]
    out.append("- **Sheet**: " + sheet_text(d, e))
    spawns = enemy_spawns(d, eid)
    if spawns:
        out.append("- **Spawns** (%d room spawns):" % len(spawns))
        for zone, region, room, slv, mx, resp, tags in spawns:
            out.append("  - %s › %s › %s: %s, up to %s%s%s" % (zone, region, room, band_text(*slv), mx, ", respawn %ss" % resp if resp else "", "; " + "; ".join(tags) if tags else ""))
    else:
        out.append("- **Spawns**: no room spawns it")
    if seen:
        out.append("- **Also appears**: " + "; ".join(sorted(seen)))
    out.append("- **Level band**: %s in `enemies.json`%s" % (band_text(int(lv[0]), int(lv[-1])), "; %s with its room spawns" % band_text(lo, hi) if (lo, hi) != (int(lv[0]), int(lv[-1])) else ""))
    st = "Lv %d: %s" % (lo, mob_stats(d, e, lo, mob))
    if hi != lo:
        st += "; Lv %d: %s" % (hi, mob_stats(d, e, hi, mob))
    if e.get("role") == "normal" and any(sp[6] and "elite" in sp[6] for sp in spawns):
        st += "; as an elite at Lv %d: %s" % (hi, mob_stats(d, e, hi, mob, "elite"))
    out.append("- **Stats**: " + st)
    out.append("- **Behaviour**: " + behaviour_text(d, e))
    out += drops_text(d, s, eid)
    out.append("")
    return out


def behaviour_text(d, e):
    ai = e.get("ai", {})
    parts = ["AI %s" % ai.get("profile", "?")]
    for k in ("aggro_range", "move_speed", "patrol", "flee_below"):
        if ai.get(k):
            parts.append("%s %s" % (k.replace("_", " "), num(ai[k])))
    mv = e.get("movement", {})
    moves = [k for k in ("climb", "fly", "drop") if mv.get(k)] + (["jump %s" % mv["jump"]] if mv.get("jump") else [])
    if moves:
        parts.append("moves: " + ", ".join(moves))
    for k in ("flying", "pack", "keep_distance", "knockback_immune", "invulnerable", "agile", "passive", "hunter", "presence", "hollowing",
              "weak_to", "thorns", "front_guard", "phases_walls", "hidden_in_fog", "steals_coins", "surrenders", "spar", "bounty", "sphere",
              "guards", "linked", "cleansable", "flees_after_s", "respawn_min", "appears_after", "tameable", "tame_species", "faction"):
        if e.get(k) not in (None, False, "", [], {}):
            v = e[k]
            parts.append(k.replace("_", " ") if v is True else "%s %s" % (k.replace("_", " "), json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else num(v)))
    atk = []
    for a in e.get("attacks", []):
        bits = ["%s×%s" % (a.get("id", "attack"), num(a.get("mult", 1.0)))]
        bits.append("windup %ss" % num(a.get("windup_s", 0)))
        for k in ("damage_type", "element", "art", "shape", "reach", "count", "status", "knockback", "summon", "cooldown_s", "range"):
            if a.get(k) not in (None, "", 0):
                bits.append("%s %s" % (k.replace("_", " "), json.dumps(a[k], sort_keys=True) if isinstance(a[k], (dict, list)) else num(a[k])))
        atk.append(" ".join([bits[0], "(" + ", ".join(bits[1:]) + ")"]))
    text = "; ".join(parts)
    if atk:
        text += ". Attacks: " + "; ".join(atk)
    ph = []
    for p in e.get("phases", []):
        ph.append("below %s HP: %s" % (pct(p.get("below", 0)), ", ".join("%s %s" % (k.replace("_", " "), json.dumps(p[k], sort_keys=True) if isinstance(p[k], (dict, list)) else num(p[k])) for k in sorted(p) if k != "below")))
    if ph:
        text += ". Phases: " + "; ".join(ph)
    return text


def drops_text(d, s, eid):
    e = d.enemies[eid]
    table = e.get("loot", eid)
    t = d.loot.get(table)
    out = []
    if not t:
        out.append("- **Drops**: loot table `%s` is missing" % table)
        return out
    rows = table_rows(d, t)
    out.append("- **Drops** (loot table `%s`):" % table)
    for iid, rate, note in rows:
        out.append("  - [%s](items.md#item-%s): %s (%s)" % (d.item_name(iid), iid, rate, note))
    for iid, rate, note in s.enemy_extra.get(eid, []):
        out.append("  - [%s](items.md#item-%s): %s (%s)" % (d.item_name(iid), iid, rate, note))
    coins = t.get("coins", {})
    if coins and float(coins.get("chance", 0)) > 0:
        out.append("  - coins: %s, ×%s the Level's purse, in the zone's everyday currency" % (pct(coins["chance"]), num(coins.get("mult", 1))))
    eq = t.get("equipment", {})
    if eq and float(eq.get("chance", 0)) > 0 and t.get("starter"):
        st = d.drop()["starter"]
        out.append("  - equipment: %s, starter gear: a Plain %s or armour piece at the par item Level, no better than par quality; "
                   "a character's first kill in the first rooms drops a %s %s, and its first %d pieces come by the %dth kill "
                   "without one at the latest" % (pct(eq["chance"]), ", ".join(titled(f) for f in st["families"]), titled(st["first_quality"]),
                                                  titled(st["first_family"]), st["pity_pieces"], st["pity"]))
    elif eq and float(eq.get("chance", 0)) > 0:
        grades = s.grades_for([s.enemy_levels(eid)])
        out.append("  - equipment: %s, a banded piece of %s (min quality %s; see [Banded equipment drops](items.md#banded-equipment-drops))" % (
            pct(eq["chance"]), " or ".join(titled(g) for g in grades), eq.get("min_quality", "flawed")))
    elif t.get("no_equipment"):
        out.append("  - equipment: none (%s)" % t["no_equipment"])
    if not rows and not s.enemy_extra.get(eid) and not coins and not eq and not t.get("no_equipment"):
        out.append("  - nothing")
    if e.get("unique_drop") and e["unique_drop"] not in [r[0] for r in rows]:
        out.append("  - note: `unique_drop` names %s, which the loot table does not hold" % d.item_name(e["unique_drop"]))
    return out


# ------------------------------------------------------------------ main
def write(name, text):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def build(gaps=False):
    d = Data()
    s = Sources(d).run()
    write("items.md", items_page(d, s))
    write("monsters.md", monsters_page(d, s))
    missing = [i for i in d.items if not s.by_item.get(i) and not item_marks(d.items[i])]
    if gaps:
        for i in missing:
            print("no source:", i, "(%s, %s)" % (d.items[i].get("type"), d.items[i].get("grade")))
    return missing


if __name__ == "__main__":
    miss = build("--gaps" in sys.argv)
    print("wiki: docs/wiki/items.md, docs/wiki/monsters.md (%d items without a source or mark)" % len(miss))
