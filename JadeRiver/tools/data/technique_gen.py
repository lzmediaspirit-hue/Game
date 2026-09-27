"""P13a · The technique generator (docs/technique_plan.md §3, §4): walks the cells of the eleven element trees and writes
one row per art, deterministically, honouring the hand rows first (today's 56, the keystones, the Dao arts, the Lost
Arts). Called by techniques.build(); writes techniques.json (compact: a row keeps only what differs from its form's and
its ring's defaults, which ContentDB fills in at load), technique_trees.json and lost_arts.json.

Checks as it builds (and fails the build): names unique, at most 28 characters, words from the lists, not an item's,
place's, NPC's, title's or realm's name, not on the denylist (exact or within an edit distance of 2); rules 1, 2, 3 and
6 of §3.6. data_validation checks the written data again.
"""
import hashlib
import json
import os
import re

from common import DATA
import technique_grammar as G
import technique_hand as H

TREE_ORDER = list(G.TREES)
BUILT = [f for f in G.SECTORS if f not in G.LATER_FAMILIES]   # the twelve sectors of v1.2.x
RING_UNLOCK = {1: "qi_kindling_1", 2: "qi_unfurling_1", 3: "cloud_stride_1", 4: "heaven_glimpse_1", 5: "sage_1", 6: "sage_sovereign_1",
               7: "will_manifest_1", 8: "sphere_lord_1", 9: "law_touching_1", 10: "monarch_1", 11: "inner_heaven_1", 12: "inner_heaven_5",
               13: "world_genesis"}
# Player-facing names of the keystones' sources and the tree's own (strings technique_source.<id>); a quest reads as its name.
SOURCE_NAMES = {"tree": "Realised on its element's tree", "library_top": "The sect library's top floor", "library_elder": "The sect library's elders' floor",
                "tower_20": "The Trial Tower, floor 20", "tower_30": "The Trial Tower, floor 30", "lost": "Found in the world",
                "fist_dao_3": "Fist Dao, third tier", "fist_dao_5": "Fist Dao, fifth tier", "spear_dao_3": "Spear Dao, third tier",
                "spear_dao_5": "Spear Dao, fifth tier", "blade_dao_3": "Blade Dao, third tier", "blade_dao_5": "Blade Dao, fifth tier",
                "staff_dao_3": "Staff Dao, third tier", "staff_dao_5": "Staff Dao, fifth tier", "bow_dao_3": "Bow Dao, third tier",
                "bow_dao_5": "Bow Dao, fifth tier", "fan_dao_3": "Fan Dao, third tier", "fan_dao_5": "Fan Dao, fifth tier",
                "music_dao_3": "Music Dao, third tier", "music_dao_5": "Music Dao, fifth tier", "brush_dao_3": "Brush Dao, third tier",
                "brush_dao_5": "Brush Dao, fifth tier", "water_dao_3": "Water Dao, third tier", "water_dao_5": "Water Dao, fifth tier",
                "wood_dao_3": "Wood Dao, third tier", "wood_dao_5": "Wood Dao, fifth tier", "earth_dao_3": "Earth Dao, third tier",
                "earth_dao_5": "Earth Dao, fifth tier", "wind_dao_3": "Wind Dao, third tier", "wind_dao_5": "Wind Dao, fifth tier",
                "fire_dao_3": "Fire Dao, third tier", "fire_dao_5": "Fire Dao, fifth tier", "metal_dao_3": "Metal Dao, third tier",
                "metal_dao_5": "Metal Dao, fifth tier", "thunder_dao_3": "Thunder Dao, third tier", "thunder_dao_5": "Thunder Dao, fifth tier",
                "soul_dao_5": "Soul Dao, fifth tier", "space_dao_3": "Space Dao, third tier", "space_dao_5": "Space Dao, fifth tier",
                "heart_trial": "The Heart Trial", "siege_of_two_sects": "The Siege of Two Sects", "copper_body_trial": "The Copper Body Trial",
                "riverbreath_trial": "The Riverbreath Trial at the Falls Pool", "trial_of_reflections": "The Trial of Reflections",
                "sect_war": "The Sect War at the Alliance Gate", "iron_body_trial": "The Iron Body Trial", "presence_trial": "The Presence Trial",
                "hollow_tide_battle": "The Tide Breaks at the Tidebreak Bastion", "jade_body_trial": "The Jade Body Trial"}


def h(*parts):
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:12], 16)


def snake(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def ring_of_level(lv):
    return max(r for r in G.RINGS if G.RINGS[r][1] <= lv)


def realm_levels():
    return {r["key"]: r["level"] for r in json.load(open(os.path.join(DATA, "realms.json")))["entries"]}


def tree_of(element):
    return G.TREE_OF[element]


def rings_of(tree):
    return list(range(G.TREES[tree][1], 14))


# ----------------------------------------------------------------------------------------------------------------------
# Forms per cell (§3.6 rules 1-3): every sector's rings take different forms, neighbouring rings differ in role, and no
# family puts one form on one ring in more than two trees.
def assign_forms(fixed):
    """fixed: (tree, family, ring) -> form of an existing orthodox art. Returns the same key -> form for every cell."""
    out = {}
    for fam in G.SECTORS:
        can = [f for f in G.FORMS if fam in G.FORMS[f]["fams"]]
        count = {}   # (ring, form) -> trees: today's arts count first, wherever their tree comes in the order (rule 2)
        for (_t, f2, r), form in fixed.items():
            if f2 == fam:
                count[(r, form)] = count.get((r, form), 0) + 1
        for tree in TREE_ORDER:
            rings = rings_of(tree)
            pinned = {r: fixed[(tree, fam, r)] for r in rings if (tree, fam, r) in fixed}
            got = dict(pinned)
            used = set(pinned.values())
            tries = [0]

            def ok_role(r, f):
                prev, nxt = got.get(r - 1), got.get(r + 1)
                return all(n is None or G.FORMS[n]["role"] != G.FORMS[f]["role"] for n in (prev, nxt))

            def dfs(i):
                if i == len(rings):
                    return True
                r = rings[i]
                if r in pinned:
                    return dfs(i + 1)
                tries[0] += 1
                opts = [f for f in can if f not in used and G.FORMS[f]["opens"] <= r and ok_role(r, f) and count.get((r, f), 0) < 2]
                opts.sort(key=lambda f: h(tree, fam, r, f))
                for f in opts:
                    got[r] = f
                    used.add(f)
                    if tries[0] < 20000 and dfs(i + 1):
                        return True
                    del got[r]
                    used.discard(f)
                return False
            assert dfs(0), ("no form assignment", tree, fam)
            for r in rings:
                if r not in pinned:
                    count[(r, got[r])] = count.get((r, got[r]), 0) + 1
                out[(tree, fam, r)] = got[r]
    return out


def path_of(tree, fam, ring):
    """§4.6: the path of a cell's path art rotates through the five, the family's two affinities taking three rings of
    twelve and the rest two, never one path on neighbouring rings, from an offset set by the element and the family."""
    a1, a2 = G.AFFINITY[fam]
    o1, o2, o3 = [p for p in G.PATH_ORDER if p not in (a1, a2)]
    seq = [a1, o1, a2, o2, a1, o3, a2, o1, a1, o2, a2, o3]
    off = (TREE_ORDER.index(tree) * 5 + G.SECTORS.index(fam) * 7) % 12
    return seq[(ring - 2 + off) % 12]


def path_form(fam, ring, path, orth, tree):
    can = [f for f in G.FORMS if fam in G.FORMS[f]["fams"] and G.FORMS[f]["opens"] <= ring and f != orth]
    fav = [f for f in G.PATHS[path]["forms"] if f in can]
    if not fav:
        roles = {G.FORMS[f]["role"] for f in G.PATHS[path]["forms"]}
        fav = [f for f in can if G.FORMS[f]["role"] in roles] or can
    return fav[(ring + TREE_ORDER.index(tree)) % len(fav)]


# ----------------------------------------------------------------------------------------------------------------------
# Rows
def damage_type(form, fam, element):
    t = G.FORMS[form]["dtype"]
    if t == "qi*":
        t = "physical" if fam == "bow" else "qi"
    if t in ("physical", "qi"):
        if fam in ("flute", "brush") and t == "physical":
            t = "qi"
        if fam == "bell" or element == "soul":
            t = "soul" if t == "qi" or fam == "bell" else t
    return t


def pose(form, fam):
    if fam == "bow":
        return "bow"
    if fam == "flute":
        return "attack"
    combo = FAMILY_COMBO.get(fam, [])
    for p in G.FORMS[form]["pose"]:
        if p in ("jump", "meditate_burst"):
            return p
        if p == "punch*":
            if fam in ("any", "fists"):
                return "punch"
            continue
        if p.startswith("c") and p[1:].isdigit():
            return combo[int(p[1:]) - 1] if combo else "punch"
        if p in combo or (fam == "any" and p.startswith("punch")):
            return p
    return combo[-1] if combo else "punch"


def reach_of(form, fam, ring, element):
    F = G.FORMS[form]
    ex = F["extra"]
    if "projectile" in ex:
        base = ex["projectile"]["range"]
    elif "reach" in ex:
        base = ex["reach"]
    else:
        base = G.FAMILY_REACH[fam] * ex.get("reach_mult", 1.0)
    wind = 1.15 if element == "wind" and F["role"] != "control" else 1.0
    return int(round(base * (1 + G.RINGS[ring][5]) * wind))


def verb_fields(form, element):
    """The element's verb on a form (§3.3): its status on the control forms, its second verb on the rest."""
    E = G.ELEMENTS[element]
    role = G.FORMS[form]["role"]
    if form in ("ward", "chorus", "counter"):
        return {}
    if role == "control" and form != "seal":
        c = E["control"]
        if c == "armour_break":
            return {"armour_break": {"chance": 1.0, "duration_s": 4}}
        if c == "knockup":
            return {"knockup_s": 0.7}
        return dict(c) if "pull" in c else {"status": dict(c)}
    out = {}
    for k, v in E["other"].items():
        if form == "seal" and k == "status":
            continue
        if k == "reach":
            continue   # baked into the reach
        out[k] = dict(v) if isinstance(v, dict) else v
    return out


def cost_of_blood(form):
    cd = G.FORMS[form]["cd"]
    return 0.05 if cd <= 5 else (0.10 if cd <= 9 else 0.15)


def make_row(tree, fam, ring, form, path=None):
    """One generated art of a cell: the form's line at the ring's budget, the element's verb, the path's rule."""
    element = G.TREES[tree][0]
    F, E = G.FORMS[form], G.ELEMENTS[element]
    dtype = damage_type(form, fam, element)
    row = {"form": form, "family": fam, "element": element, "ring": ring}
    if path:
        row["path"] = path
    if dtype != F["dtype"]:
        row["damage_type"] = dtype
        row.setdefault("hitbox", {})["alt"] = [-10, 80] if dtype in ("qi", "soul") else [-30, 60]
    lo, hi = F["mult"]
    if lo > 0 and dtype != "stance":
        k = G.RING_BUDGET[ring] * E.get("mult", 1.0) * (G.PATHS[path]["budget"] if path else 1.0)
        row["mult"] = [round(lo * k, 3), round(hi * k, 3)]
    extra_t = G.RINGS[ring][4]
    if F["targets"] >= 2 and extra_t:
        row["max_targets"] = F["targets"] + extra_t
    reach = reach_of(form, fam, ring, element)
    row.setdefault("hitbox", {})["x"] = [-10, reach]
    for k, v in F["extra"].items():
        if k in ("reach", "reach_mult", "depth"):
            continue
        row[k] = json.loads(json.dumps(v))
    if "projectile" in row:
        row["projectile"]["range"] = reach
        if fam in G.PROJECTILE_ART:
            row["projectile"]["art"] = G.PROJECTILE_ART[fam]
    row["action"] = pose(form, fam)
    row["dao"] = G.FAMILY_DAO.get(fam) or (G.TREES[tree][2] or "none")
    if form == "ward":
        row["buffs"] = [dict(b) for b in E["ward"]]
    row.update(verb_fields(form, element))
    if E.get("cost", {}).get("soul") and dtype in ("soul", "qi") and form not in ("ward", "chorus", "counter"):
        row["soul_cost"] = E["cost"]["soul"]
    if path:
        row.update(G.PATHS[path]["fields"])
        if path == "blood":
            row["hp_cost_pct"] = cost_of_blood(form)
        elif path == "buddhist":
            row["composure_cost"], row["qi_cost"] = F["qi"], 0
            row["shield_hp_pct"], row["shield_s"] = G.BUDDHIST_SHIELD, 6
        elif path == "poison" and dtype not in ("buff", "stance"):
            row["status"] = dict(G.POISON_STATUS)
    row["vfx"] = {"particles": particle_style(fam, element, dtype)}
    return row


def particle_style(fam, element, dtype):
    from techniques import particle_style as ps   # P6e's one rule for the hit spark
    return ps(fam, element, dtype)


# ----------------------------------------------------------------------------------------------------------------------
# Keystones (§3.7): a template with the element's verb, at the outer ring of the act.
def keystone_row(tree, kin, act, name, template, desc):
    element = G.TREES[tree][0]
    E = G.ELEMENTS[element]
    ring = G.ACT_EDGE[act]
    b = G.RING_BUDGET[ring]
    dtype = "soul" if element == "soul" else "qi"
    row = {"id": snake(name), "name": name, "family": "any", "kin": kin, "element": element, "ring": ring, "kind": "keystone",
           "template": template, "heavy": True, "action": "meditate_burst", "dao": G.TREES[tree][2] or "none", "desc": desc,
           "windup_s": 0.3, "active_s": 0.3, "soul_cost": 0, "composure_cost": 0, "mastery": MASTERY}
    ctrl = verb_fields("snare", element)
    if template == "constructs":
        row.update(damage_type=dtype, mult=[round(0.36 * b, 3), round(0.44 * b, 3)], hits=9, max_targets=1, cooldown_s=24, qi_cost=28,
                   projectile={"speed": 520, "range": 460, "count": 9, "seek": True}, hitbox={"x": [-10, 460], "depth": 40, "alt": [-10, 80]})
        row.update({k: v for k, v in verb_fields("seeker", element).items()})
    elif template == "field":
        row.update(damage_type=dtype, mult=[round(0.45 * b, 3), round(0.55 * b, 3)], hits=4, max_targets=8, cooldown_s=18, qi_cost=26,
                   both_sides=True, hitbox={"x": [-10, 300], "depth": 90, "alt": [-10, 80]})
        row.update(ctrl)
    elif template == "finisher":
        row.update(damage_type=dtype, mult=[round(3.0 * b, 3), round(3.6 * b, 3)], hits=1, max_targets=1, cooldown_s=14, qi_cost=24,
                   ignore_resistance=0.15, hitbox={"x": [-10, 260], "depth": 40, "alt": [-10, 80]})
    elif template == "avatar":
        buffs = [dict(x, value=round(x["value"] * 1.6, 3), duration=10) for x in E["ward"]]
        buffs += [{"stat": s, "op": "pct_add", "value": 0.15, "duration": 10} for s in ("physical_attack", "qi_attack")]
        row.update(damage_type="buff", mult=[0, 0], hits=0, max_targets=0, cooldown_s=40, qi_cost=30, buffs=buffs,
                   hitbox={"x": [-10, 110], "depth": 30, "alt": [-30, 60]})
    elif template == "mirror":
        row.update(damage_type="illusion", mult=[0, 0], hits=0, max_targets=0, cooldown_s=24, qi_cost=24, illusion_s=6,
                   illusion_hits=4, illusion_radius=500, hitbox={"x": [-10, 110], "depth": 30, "alt": [-30, 60]})
    elif template == "procession":
        row.update(damage_type="buff", mult=[0, 0], hits=0, max_targets=0, cooldown_s=36, qi_cost=24,
                   buffs=[{"stat": "elemental_power", "op": "flat", "value": 0.20, "duration": 12}],
                   hitbox={"x": [-10, 110], "depth": 30, "alt": [-30, 60]})
        if tree == "water" and act == 1:
            row.update(allies_heal_pct=0.12, allies_heal_s=12, heal_radius=300)
    row["vfx"] = {"particles": particle_style("any", element, row["damage_type"]), "shape": TEMPLATE_SHAPE[template]}
    return row


MASTERY = {"dmg_per_tier": 0.08, "cost_per_tier": -0.05}
TEMPLATE_SHAPE = {"constructs": "bolt", "field": "domain", "avatar": "domain", "finisher": "pillar", "mirror": "domain", "procession": "domain"}
FAMILY_COMBO = {}


def form_defaults():
    from technique_anim import pose_of
    out = {}
    for f, F in G.FORMS.items():
        dtype = F["dtype"] if F["dtype"] != "qi*" else "qi"
        # The pose most of the form's families take (a row of another family keeps its own), and the FX's pose with it.
        takes = {}
        for fam in G.SECTORS:
            if fam in F["fams"] and fam not in G.LATER_FAMILIES:
                takes[pose(f, fam)] = takes.get(pose(f, fam), 0) + 1
        action = sorted(takes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        out[f] = {"damage_type": dtype, "hits": F["hits"], "max_targets": F["targets"], "cooldown_s": F["cd"], "qi_cost": F["qi"],
                  "windup_s": 0.2, "active_s": 0.2, "soul_cost": 0, "composure_cost": 0, "mastery": MASTERY,
                  "mult": [0, 0] if F["mult"][0] == 0 else list(F["mult"]),
                  "hitbox": {"depth": F["extra"].get("depth", 30), "alt": [-10, 80] if dtype in ("qi", "soul") else [-30, 60]},
                  "action": action, "vfx": {"shape": F["shape"], "anim": f, "pose": pose_of({"action": action})}}   # the form's FX
    # (technique_anim); no icon: the emblem is composed from its id
    return out


def ring_defaults():
    return {str(r): {"grade": v[0], "unlock": RING_UNLOCK[r], "source": "tree", "vfx": {"tier": v[3]}} for r, v in G.RINGS.items()}


# ----------------------------------------------------------------------------------------------------------------------
# Names (§3.8)
def lev(a, b, cap=3):
    if abs(len(a) - len(b)) >= cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        if min(cur) >= cap:
            return cap
        prev = cur
    return prev[-1]


def norm(name):
    return re.sub(r"[^a-z ]", "", name.lower().replace("-", " ")).strip()


DENY = [norm(d) for d in G.DENYLIST]


def denied(name):
    n = norm(name)
    return any(n == d or lev(n, d) <= 2 for d in DENY)


def fits(noun, fam):
    return noun if isinstance(noun, str) else (noun[0] if fam in noun[1].split() else None)


def gen_name(tree, fam, ring, form, path, hits, used, forbidden):
    element = G.TREES[tree][0]
    imgs = G.IMAGES[element]
    band = 0 if ring <= 4 else (1 if ring <= 8 else 2)
    nouns = [n for n in (fits(x, fam) for x in G.NOUNS[form]) if n]
    images, creatures, places = imgs[band], imgs[3], imgs[4]
    # An image that is a phrase ("Lamp Before Birth") stands only after "of the"; a plain one (one or two words) anywhere.
    plain = [i for i in images if len(i.split()) <= 2 and i == i.title()] or images
    for salt in range(400):
        s = h(tree, fam, ring, form, path or "", salt)
        img = plain[s % len(plain)]
        noun = nouns[(s // 7) % len(nouns)]
        if path:
            epi = G.PATHS[path]["words"][(s // 11) % len(G.PATHS[path]["words"])]
            short = [i for i in plain if " " not in i] or plain
            pats = ["%s %s %s" % (epi, short[s % len(short)], noun)]
            if band == 2:
                pats.append("%s %s of the %s" % (epi, noun, places[(s // 13) % len(places)]))
            if form in G.BODY and creatures:
                pats.append("%s %s %s" % (epi, creatures[(s // 19) % len(creatures)], noun))
        elif band == 2:
            phrase = images[(s // 29) % len(images)]
            pats = ["%s of the %s" % (noun, places[(s // 13) % len(places)]), "%s %s" % (img, noun),
                    "%s of %s" % (noun, phrase) if phrase.startswith(("The ", "Yesterday")) else "%s of the %s" % (noun, phrase)]
            pats[-1] = pats[-1].replace("of The ", "of the ")
        else:
            pats = ["%s %s" % (img, noun)]
            if hits >= 2 and hits in G.NUMBERS:
                pats.append("%s %s %s" % (G.NUMBERS[hits], img, noun))
            if form in G.HEAVY and " " not in img and "-" not in img and element != "none":
                pats.append("%s-%s %s" % (img, G.VERBING[(s // 17) % len(G.VERBING)], noun))
            if form in G.BODY and creatures:
                pats.append("%s %s" % (creatures[(s // 19) % len(creatures)], noun))
        pats = [p for p in pats if p]
        name = pats[(s // 23) % len(pats)]
        if len(name) <= G.MAX_NAME and name.lower() not in used and name.lower() not in forbidden and not denied(name) \
                and snake(name) not in used:
            return name
    raise AssertionError("no name for %s %s %d %s" % (tree, fam, ring, form))


def forbidden_names():
    """Items, places, NPCs, titles and realms: no art takes one of their names (§3.8)."""
    out = set()
    for table in ("items", "artifacts", "npcs", "titles", "realms", "zones", "quests"):
        path = os.path.join(DATA, table + ".json")
        if os.path.exists(path):
            out |= {str(e.get("name", "")).lower() for e in json.load(open(path))["entries"] if e.get("name")}
    rooms = os.path.join(DATA, "rooms")
    for f in sorted(os.listdir(rooms)):
        out.add(str(json.load(open(os.path.join(rooms, f))).get("name", "")).lower())
    return out


# ----------------------------------------------------------------------------------------------------------------------
def build(existing):
    """existing: today's 56 rows (techniques.py). Returns (rows, trees config, lost table)."""
    global FAMILY_COMBO
    wf = {e["id"]: e for e in json.load(open(os.path.join(DATA, "weapon_families.json")))["entries"]}
    FAMILY_COMBO = {f: [s["action"] for s in wf[f]["combo"]] for f in wf}
    levels = realm_levels()
    by_id = {t["id"]: t for t in existing}
    # Today's 56 re-homed: form, ring, the tree's cell or the Dao trunk or the Lost Arts.
    fixed, cells = {}, {}
    for t in existing:
        tid = t["id"]
        form = H.FORM_OF[tid]
        if form in G.FORMS:
            t["form"] = form
        else:
            t["template"] = form
        t["ring"] = ring_of_level(levels[t["unlock"]])
        t["grade"] = G.RINGS[t["ring"]][0]
        path = next((p for flag, p in (("body", "body"), ("blood_path", "blood"), ("needs_vow", "buddhist"), ("poison_path", "poison"),
                                       ("confucian_path", "confucian")) if t.get(flag)), None)
        if path:
            t["path"] = path
        if tid in H.DAO_EXISTING:
            t["kind"], t["dao_art"] = "dao", list(H.DAO_EXISTING[tid])
            continue
        if tid in H.LOST_EXISTING:
            t.update(kind="lost", heavy=True, lost=True)
            continue
        tree = tree_of(t["element"])
        slot = "p" if path and t["ring"] > G.TREES[tree][1] else "o"
        key = (tree, t["family"], t["ring"])
        cells.setdefault(key, {"o": [], "p": []})[slot].append(tid)
        if slot == "o" and key not in fixed:
            fixed[key] = form
    forms = assign_forms(fixed)
    used = {t["name"].lower() for t in existing} | {t["id"] for t in existing}
    forbidden = forbidden_names()
    rows = list(existing)

    def add(row):
        assert row["name"].lower() not in used and row["id"] not in used, ("duplicate name", row["name"])
        assert len(row["name"]) <= G.MAX_NAME and not denied(row["name"]) and row["name"].lower() not in forbidden, ("bad name", row["name"])
        used.add(row["name"].lower())
        used.add(row["id"])
        rows.append(row)

    for tree in TREE_ORDER:
        first = G.TREES[tree][1]
        for fam in G.SECTORS:
            if fam in G.LATER_FAMILIES:
                continue   # v1.3 brings these four sectors (§8 step 10); their rows wait for their weapons
            for ring in rings_of(tree):
                have = cells.get((tree, fam, ring), {"o": [], "p": []})
                orth = forms[(tree, fam, ring)]
                if not have["o"]:
                    r = make_row(tree, fam, ring, orth)
                    r["name"] = gen_name(tree, fam, ring, orth, None, r.get("hits", G.FORMS[orth]["hits"]), used, forbidden)
                    r["id"] = snake(r["name"])
                    add(r)
                if ring > first and not have["p"]:
                    path = path_of(tree, fam, ring)
                    pf = path_form(fam, ring, path, orth, tree)
                    r = make_row(tree, fam, ring, pf, path)
                    r["name"] = gen_name(tree, fam, ring, pf, path, r.get("hits", G.FORMS[pf]["hits"]), used, forbidden)
                    r["id"] = snake(r["name"])
                    add(r)
    # Keystones, Acts I-III: the pool of sources by act, Water's Act I fixed.
    for (tree, act), four in H.KEYSTONES.items():
        templates = [x[1] for x in four]
        assert len(set(templates)) == 4, ("rule 6", tree, act)
        pool = H.KEYSTONE_FIXED.get((tree, act)) or [H.KEYSTONE_POOL[act][(TREE_ORDER.index(tree) * 3 + i) % len(H.KEYSTONE_POOL[act])] for i in range(4)]
        for kin, (name, template, desc), (src, cond) in zip(G.KIN, four, pool):
            r = keystone_row(tree, kin, act, name, template, desc)
            r["source"], r["teach"] = src, {"all": [cond]}
            add(r)
    # Dao arts: taught by their Dao's third and fifth tiers (off the cells: on the gate or the trunk).
    for (tid, dao, tier, fam, element, form, desc, extra) in H.DAO_ARTS:
        ring = 3 if tier == 3 else 7
        r = make_row(tree_of(element), fam, ring, form)
        r.update(id=tid, name=titled_name(tid), kind="dao", dao_art=[dao, tier], source="%s_dao_%d" % (dao, tier), desc=desc)
        merge(r, extra)
        add(r)
    # Lost Arts: techniques as rows, Inner Arts and Secret Arts in their own tables (techniques.py, paths.py).
    lost_table, lineages = lost_arts(add)
    return rows, lost_table, lineages


def titled_name(tid):
    from common import titled
    return titled(tid)


def merge(row, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(row.get(k), dict):
            row[k] = dict(row[k], **v)
        else:
            row[k] = v
    if "projectile" in extra and "count" in extra["projectile"]:
        row["hits"] = extra["projectile"]["count"] if row.get("hits", 1) < extra["projectile"]["count"] else row["hits"]


LOST_RING = {1: 3, 2: 5, 3: 7, 4: 9, 5: 11}
LOST_NAMES = {"tide_palm": "Tide-Palm", "falls_climbing_step": "Falls-Climbing Step", "kite_string_cut": "Kite-String Cut",
              "mist_lamp_meditation": "Mist-Lamp Meditation", "well_bottom_sutra": "Well-Bottom Sutra",
              "quarry_breaker_fist": "Quarry-Breaker Fist", "frost_shrine_sword": "Frost-Shrine Sword",
              "echo_cliff_refrain": "Echo-Cliff Refrain", "serpent_coil_thrust": "Serpent-Coil Thrust",
              "scar_lightning_lance": "Scar-Lightning Lance", "mirror_lake_knell": "Mirror-Lake Knell",
              "crypt_seal_cleave": "Crypt-Seal Cleave", "sand_throne_sweep": "Sand-Throne Sweep",
              "many_eyed_pool_air": "Many-Eyed Pool Air", "roost_scatter_fan": "Roost-Scatter Fan",
              "deck_cutter_flick": "Deck-Cutter Flick", "ninth_peak_scroll": "Ninth Peak Scroll",
              "star_sighting_shot": "Star-Sighting Shot", "upside_down_staff": "Upside-Down Staff", "wyrm_egg_knuckle": "Wyrm-Egg Knuckle",
              "hulk_breaker": "Hulk-Breaker", "pyre_generals_lance": "Pyre-General's Lance", "comet_tail_arrow": "Comet-Tail Arrow",
              "maw_song": "Maw-Song", "burning_star_peal": "Burning-Star Peal", "sand_glyph_snare": "Sand-Glyph Snare",
              "throne_dust_veil": "Throne-Dust Veil", "lamp_on_a_tether": "Lamp on a Tether", "inverted_stair_kick": "Inverted Stair Kick",
              "orbit_stone_sling": "Orbit-Stone Sling"}


def lost_arts(add):
    """Every lost art of Acts I-III: its technique row (a heavy art) and its entry in lost_arts.json with its source."""
    table, lineages = [], []

    def tech(spec, extra_src=None):
        tid = spec["id"]
        name = LOST_NAMES.get(tid) or titled_name(tid)
        ring = LOST_RING[spec["act"]]
        tree = tree_of(spec["element"])
        if spec.get("template"):
            r = keystone_row(tree, G.KIN_OF[spec["family"]] if spec["family"] != "any" else "voice", 2, name, spec["template"], spec["desc"])
            r.update(ring=ring, id=tid)
        else:
            r = make_row(tree, spec["family"], ring, spec["form"], spec.get("path"))
            k = spec.get("fields", {}).get("mult_x", 1.1)
            if "mult" in r:
                r["mult"] = [round(v * k, 3) for v in r["mult"]]
            r.update(id=tid, name=name)
        merge(r, {k: v for k, v in spec.get("fields", {}).items() if k != "mult_x"})
        r.update(kind="lost", lost=True, heavy=True, act=spec["act"], source="lost", desc=spec["desc"])
        add(r)

    for spec in H.LOST:
        if spec["kind"] == "technique" and spec["id"] not in H.LOST_EXISTING:
            tech(spec)
        table.append({"id": spec["id"], "kind": spec["kind"], "act": spec["act"], "src": spec["src"]})
    for lin in H.LINEAGES:
        ids = []
        for i, p in enumerate(lin["pieces"]):
            if p["kind"] == "technique":
                tech(p)
            src = {"kind": "pages", "count": p["count"], "item": "lu_journal_page"} if "count" in p else {"kind": "ruin", "room": p["room"], "object": "lost_" + p["id"]}
            table.append({"id": p["id"], "kind": p["kind"], "act": p["act"], "lineage": lin["id"], "piece": i + 1, "src": src})
            ids.append(p["id"])
        lineages.append({"id": lin["id"], "name": lin["name"], "rule": lin["rule"], "pieces": ids})
    return table, lineages


def lost_minor(kind):
    """The Lost Arts of a kind other than techniques ('inner' or 'secret'), as rows for their own tables."""
    out = []
    specs = [s for s in H.LOST if s["kind"] == kind and "desc" in s] + [p for lin in H.LINEAGES for p in lin["pieces"] if p["kind"] == kind]
    for s in specs:
        name = LOST_NAMES.get(s["id"]) or titled_name(s["id"])
        out.append({"id": s["id"], "name": name, "desc": s["desc"], "modifiers": s.get("mods", []), "lost": True, "act": s["act"]})
    return out


# What a generated art does, read by TechniqueTreeRules.describe from its form, its element's verb and its path (strings
# technique.form.<form>, technique.verb.<element>, technique.control.<element>, technique.ward.<element>,
# technique.path.<path>), so the rows carry no text and a translation translates these lines.
FORM_TEXT = {
    "strike": "One heavy blow on a foe within {reach}.", "flurry": "{hits} quick blows on one foe within {reach}.",
    "thrust": "A thrust through up to {targets} foes in a line within {reach}.", "lunge": "Rush {dash} and strike every foe you pass, up to {targets}.",
    "sweep": "A sweep that strikes up to {targets} foes on both sides within {reach}.", "arc": "An arc that flies {reach} and cuts up to {targets} foes.",
    "volley": "{hits} shots at a foe within {reach}.", "rain": "{hits} strikes rain on up to {targets} foes within {reach}.",
    "pillar": "A pillar on one foe within {reach}.", "wave": "A wave {reach} long that strikes up to {targets} foes.",
    "burst": "A burst around you that strikes up to {targets} foes within {reach}.", "seeker": "{hits} seekers that find their foes within {reach}.",
    "return": "A throw that flies {reach} and back, cutting up to {targets} foes both ways.", "snare": "Holds up to {targets} foes within {reach}.",
    "counter": "A guard of {stance} s: the next blow is answered twice over.", "ward": "A ward on yourself for 8 s:",
    "chorus": "You and every ally within {radius} heal {heal}% of your health over {heal_s} s.", "blink": "Blink behind a foe within {reach} and strike.",
    "plunge": "Drop from the air on up to {targets} foes below.", "release": "The weapon flies at the foes {hits} times on its own.",
    "swarm": "{hits} constructs seek the nearest foes within {reach}.", "domain": "A field around you: {hits} strikes on up to {targets} foes within {reach}.",
    "seal": "Seals the arts of up to {targets} foes within {reach} for 3 s.", "echo": "A blow that strikes again: {hits} hits on one foe.",
}
VERB_TEXT = {"water": "Draws them 40 toward you.", "wood": "A bloom takes 1% of their health a second for 4 s.", "fire": "It may burn them.",
             "earth": "It knocks them back.", "metal": "+10% crit.", "wind": "It reaches 15% farther.", "thunder": "It may shock them.",
             "soul": "It passes armour and costs Soul.", "none": "+10% penetration.", "space": "It passes 10% of their resistance.",
             "time": "It may slow them."}
CONTROL_TEXT = {"water": "They are slowed 20% for 2 s.", "wood": "They are rooted for 1.8 s.", "fire": "They burn for 3 s.", "earth": "They are stunned for 0.7 s.",
                "metal": "Their armour breaks for 4 s.", "wind": "They are thrown into the air.", "thunder": "They are shocked.",
                "soul": "They may be confused for 2 s.", "none": "They are rooted for 1.5 s.", "space": "They are pulled to you.", "time": "They are slowed 30% for 2 s."}
WARD_TEXT = {"water": "+25% Qi resistance.", "wood": "+25% physical defence.", "fire": "+15% Qi attack.", "earth": "+30% physical defence.",
             "metal": "+20% physical defence and +5% crit.", "wind": "+25% evasion and 10% faster on foot.", "thunder": "+12% attack speed.",
             "soul": "+30% soul defence.", "none": "+15% physical defence and Qi resistance.", "space": "+30% evasion.", "time": "+10% attack speed."}
PATH_TEXT = {"body": "A body art: from Copper Body it can spend health when Qi runs short.",
             "blood": "Blood path only: it costs {hp}% of your health.",
             "buddhist": "Held with a vow: it costs Composure and shields you for 6% of your health.",
             "poison": "Its marks are poisoned (2% of their health a second for 5 s).",
             "confucian": "Confucian path only: its strength follows your Insight."}


def strings():
    out = {}
    for group, table in (("form", FORM_TEXT), ("verb", VERB_TEXT), ("control", CONTROL_TEXT), ("ward", WARD_TEXT), ("path", PATH_TEXT)):
        for k, v in table.items():
            out["technique.%s.%s" % (group, k)] = v
    for r, v in G.RINGS.items():
        if v[0] not in ("common", "earth", "heaven"):
            out["ui.techniques.grade_" + v[0]] = v[0].replace("_", " ").title()
    for t in G.TREES:
        out["technique.tree." + t] = t.title()
    out.update({"technique.kin.voice": "Body and Voice", "technique.kin.edges": "Edges", "technique.kin.reach": "Reach",
                "technique.kin.distance": "Distance and Ink"})
    for lin in H.LINEAGES:
        out["lineage.%s.name" % lin["id"]] = lin["name"]
        out["lineage.%s.rule" % lin["id"]] = lin["rule"]
    return out


def trees_config():
    return {"trees": [{"id": t, "element": v[0], "first_ring": v[1], "dao": v[2]} for t, v in G.TREES.items()],
            "sectors": [{"id": f, "kin": G.KIN_OF[f], "built": f not in G.LATER_FAMILIES} for f in G.SECTORS],
            "rings": [{"ring": r, "grade": v[0], "level": v[1], "act": v[2], "tier": v[3], "extra_targets": v[4], "reach": v[5],
                       "unlock": RING_UNLOCK[r]} for r, v in G.RINGS.items()],
            "act_edges": {str(a): r for a, r in G.ACT_EDGE.items()}, "act_open": G.BUILT_ACT, "costs": G.COSTS, "passives": G.PASSIVES,
            "grade_bonus": {v[0]: G.grade_bonus(r) for r, v in G.RINGS.items()}, "reset_item": "clear_heart_incense", "found_twice": "manual_page",
            "templates": list(G.TEMPLATES), "forms": {f: {"role": F["role"], "fams": sorted(F["fams"]), "opens": F["opens"]} for f, F in G.FORMS.items()},
            "budget": {str(r): b for r, b in G.RING_BUDGET.items()}, "verb_value": G.VERB_VALUE,
            "path_budget": {p: v["budget"] for p, v in G.PATHS.items()}, "element_mult": {e: v.get("mult", 1.0) for e, v in G.ELEMENTS.items()},
            "max_name": G.MAX_NAME, "denylist": G.DENYLIST}


def write_compact(name, head, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"schema_version": 1')
        for k, v in head.items():
            f.write(',\n"%s": %s' % (k, json.dumps(v, ensure_ascii=False, separators=(",", ":"))))
        f.write(',\n"entries": [\n' + ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows) + "\n]}\n")
    return path


def compact(row):
    """Drop what the row's form, ring, element and family give it anyway (ContentDB fills them back in at load): the
    row as built, read over its layers, keeps only its own keys, and of a dictionary only the keys that differ."""
    full = {}
    for key, layers in DEFAULTS.items():
        _merge(full, layers.get(str(row.get(key, "")), {}))
    _merge(full, row)
    base = expand({k: full[k] for k in DEFAULTS if k in full}, DEFAULTS)
    out = {}
    for k, v in full.items():
        if k in DEFAULTS or k not in base:
            out[k] = v
        elif isinstance(v, dict) and isinstance(base[k], dict):
            sub = {kk: vv for kk, vv in v.items() if kk not in base[k] or base[k][kk] != vv}
            if sub:
                out[k] = sub
        elif base[k] != v:
            out[k] = v
    assert expand(out, DEFAULTS) == full, ("compaction loses", row.get("id"))
    return out


FORM_DEFAULTS = form_defaults()
RING_DEFAULTS = ring_defaults()
# The element's layer: its Dao (a free-hand art's) and its spark; the family's: its weapon Dao and its own spark.
ELEMENT_DEFAULTS = {e: {"dao": (G.TREES[G.TREE_OF[e]][2] or "none"), "vfx": {"particles": particle_style("any", e, "soul" if e == "soul" else "qi")}}
                    for e in G.ELEMENTS}
FAMILY_DEFAULTS = {f: dict({"dao": G.FAMILY_DAO[f]}, **({"vfx": {"particles": G.FAMILY_PARTICLES[f]}} if f in G.FAMILY_PARTICLES else {}))
                   for f in G.FAMILY_DAO}
DEFAULTS = {"form": FORM_DEFAULTS, "ring": RING_DEFAULTS, "element": ELEMENT_DEFAULTS, "family": FAMILY_DEFAULTS}


def expand(row, defaults):
    """What ContentDB does at load: the layers in order, dictionaries merging, then the row's own keys over them (a
    dictionary of the row merging one level into the layers')."""
    out = {}
    for key, layers in defaults.items():
        _merge(out, layers.get(str(row.get(key, "")), {}))
    for k, v in json.loads(json.dumps(row)).items():
        out[k] = dict(out[k], **v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _merge(into, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(into.get(k), dict):
            d = dict(into[k])
            _merge(d, v)
            into[k] = d
        else:
            into[k] = json.loads(json.dumps(v)) if isinstance(v, (dict, list)) else v


def load_rows():
    """techniques.json with its defaults filled in, for the builders that read it (economy, the icons, the wiki)."""
    d = json.load(open(os.path.join(DATA, "techniques.json")))
    return [expand(e, d.get("defaults", {})) for e in d["entries"]]
