"""Decision 43 (docs/redesign/tutorials.md): every newly unlocked system teaches itself. data/tutorials.json holds one
entry a system or page; the Tutorial authority (scripts/simulation/authority/tutorial_authority.gd) keeps each
character's progress through them and the coach (scripts/ui/tutorial_coach.gd) shows them.

An entry:
  id                  the system or page it teaches (its tour's id)
  page, tab           the page (a main.gd PAGES id, "hud" for the HUD) and tab its tour is about ("" the whole page)
  trigger             when its guide is queued: {kind: unlock, unlock} a system opened; {kind: points, points, unlock}
                      the first of a resource (the HUD's points badges); {kind: item, bag_kind} the first thing of a kind in
                      the bag; {kind: bottleneck, unlock} the first bottleneck; {kind: technique, unlock} the first art in a
                      slot; {kind: page} none: only the page's first opening plays its tour
  chain               the guidance, from what the player sees to the page: {at: hud, anchor} a HUD button (with no page
                      open); {at: place, place, match} a thing in the world (the direction mark and the World map's lantern
                      lead there; data/places.json when it has the place, else the nearest thing `match` names); {at: page,
                      page, tab?, anchor, name?} a page on top (on that tab); the last may be the element to use on the
                      entry's own page, with a `try`
  hint                the first card's line (the HUD or place step)
  tour                3 to 6 steps on a page (a HUD tour 1 to 3): {anchor, text, try?, hud?}; `anchor` names a place the page
                      draws (Page.tour_rect: a tap region by its action, "tab:<id>", "tabs", "close", a page's own mark) or
                      the HUD shows (HUD.tour_rect); `a|b` takes the first found; `try` moves the step on when done: {event}
                      a game event, {tab} the tab chosen, {tap} a tap through the spotlight
  priority            higher first in the queue; prologue: true for the Prologue's systems (a character that skips it
                      knows them)
Every line is a key of tools/data/ui_strings.json (ui.tutorial.<id>.<n>, .hint, .do): at most two lines on a phone.
Pages with no tour: the talks and events (dialogue, gift, mercy, fates, revival, welcome), which the coach waits out.
"""
import json
import os
import re

from common import ROOT, entries

UI = os.path.join(os.path.dirname(__file__), "ui_strings.json")
MAX_CHARS = 92   # a card's line: two lines of the card at 20 px on a phone (the tutorials suite measures it)

# The HUD's points badges (scripts/hud.gd POINT_SYSTEMS): id -> [authority, getter].
POINTS = {"meridian": ["progression", "meridian_points_free"], "realisation": ["progression", "realisations_free"],
          "bench": ["posts", "bench_points_free"], "post_art": ["posts", "art_points_free"]}

# The anchors every page names (Page.tour_rect) besides its tap regions and its own marks.
SHARED = {"close", "help", "title", "content", "window", "tabs"}

E = []


def page_scripts():
    """main.gd PAGES: page id -> the script it opens (page ids sharing a script are one page)."""
    src = open(os.path.join(ROOT, "scripts", "main.gd"), encoding="utf-8").read()
    block = re.search(r"const PAGES := \{(.*?)\n\}", src, re.S).group(1)
    return dict(re.findall(r'"([a-z_]+)":\s*"res://scripts/ui/pages/([a-z_]+)\.gd"', block))


# ------------------------------------------------------------------ builders
def unlock(u):
    return {"kind": "unlock", "unlock": u}


def points(p, u):
    return {"kind": "points", "points": p, "unlock": u}


def first_open():
    return {"kind": "page"}


def hud(anchor):
    return {"at": "hud", "anchor": anchor}


def place(pid, **match):
    return {"at": "place", "place": pid, "match": match}


def on(page, anchor, tab="", name="", try_=None, element=False):
    st = {"at": "page", "page": page, "anchor": anchor}
    if tab:
        st["tab"] = tab
    if name:
        st["name"] = name
    if try_:
        st["try"] = try_
    if element:
        st["element"] = True
    return st


# The Menu's tablets: page id -> its name's string (menu_page.gd ENTRIES).
MENU = {"character": "ui.menu.character", "cultivation": "ui.menu.cultivation", "techniques": "ui.menu.techniques",
        "inventory": "ui.menu.bag", "quests": "ui.menu.quests", "world_map": "ui.menu.map", "calendar": "ui.menu.calendar",
        "training_sect": "ui.menu.sect", "your_sect": "ui.menu.your_sect", "spirit_animals": "ui.menu.spirit_animals",
        "companions": "ui.menu.companions", "crafts": "ui.menu.crafts", "workshop": "ui.menu.workshop",
        "characters": "ui.menu.characters", "posts": "ui.menu.roll_call", "works": "ui.menu.works", "codex": "ui.menu.codex",
        "mail": "ui.menu.mail", "emotes": "ui.menu.emotes", "settings": "ui.menu.settings"}


def via_menu(page, tab="", tab_name="", element=None):
    """The HUD's Menu button, the page's tablet, its tab and the element to use there."""
    chain = [hud("icon:menu"), on("menu", "open:" + page, name=MENU[page])]
    if tab:
        chain.append(on(page, "tab:" + tab, name=tab_name))
    if element:
        chain.append(dict(element, at="page", page=page, element=True, **({"tab": tab} if tab else {})))
    return chain


def element(anchor, try_=None):
    return {"anchor": anchor, "try": try_} if try_ else {"anchor": anchor}


def entry(eid, page, trigger, tour, tab="", chain=None, priority=0, prologue=False):
    d = {"id": eid, "page": page, "tab": tab, "trigger": trigger, "chain": chain or [],
         "tour": [dict(s) for s in tour], "priority": priority}
    if chain:
        d["hint"] = "ui.tutorial.%s.hint" % eid
    for i, st in enumerate(d["tour"]):
        st.setdefault("text", "ui.tutorial.%s.%d" % (eid, i + 1))
    for st in d["chain"]:
        if st.get("element"):
            st.setdefault("text", "ui.tutorial.%s.do" % eid)
    if prologue:
        d["prologue"] = True
    E.append(d)


def t(anchor, try_=None, hud_side=None):
    st = {"anchor": anchor}
    if try_:
        st["try"] = try_
    if hud_side is not None:
        st["hud"] = hud_side
    return st


# ------------------------------------------------------------------ the prototype's pages first
def prototype():
    # The Prologue's systems (a character that skips it knows them).
    entry("menu", "menu", unlock("menu"), [t("content"), t("bay:0"), t("bay:1"), t("locked"), t("close")],
          chain=[hud("icon:menu")], priority=9, prologue=True)
    entry("bag", "inventory", first_open(), [t("bag"), t("slot"), t("kind"), t("sort"), t("tab:key")], prologue=True)
    entry("gear", "inventory", {"kind": "item", "bag_kind": "gear"}, [],
          chain=[hud("icon:bag"), on("inventory", "gear", element=True, try_={"event": "equipment_changed"})],
          priority=8, prologue=True)
    entry("quests", "quests", unlock("navigation"), [t("story|sel"), t("read"), t("go"), t("track"), t("tab:done")],
          chain=[hud("tracker")], priority=7, prologue=True)
    entry("cultivate", "hud", unlock("cultivate"), [t("meditate"), t("progress"), t("portrait")], priority=6, prologue=True)
    entry("cultivation", "cultivation", unlock("cultivation"),
          [t("mountain"), t("stair"), t("next"), t("meditate"), t("tabs")], chain=via_menu("cultivation"), priority=5,
          prologue=True)
    entry("codex", "codex", unlock("codex"), [t("tabs"), t("sel|book"), t("corner|book"), t("tab:collection"), t("tab:achievements")],
          chain=via_menu("codex"), priority=2, prologue=True)
    # After the Prologue.
    entry("foundation", "cultivation", points("meridian", "foundation"),
          [t("points"), t("meridian"), t("bars"), t("reset_meridians")], tab="foundation",
          chain=via_menu("cultivation", "foundation", "ui.cultivation.foundation",
                         element("meridian", {"event": "attributes_changed"})), priority=8)
    entry("techniques", "techniques", unlock("technique_slots_2"),
          [t("tabs"), t("chart"), t("family"), t("reading"), t("dock"), t("next_learned")], chain=via_menu("techniques"),
          priority=7)
    entry("realisation", "techniques", points("realisation", "technique_slots_2"), [],
          chain=via_menu("techniques", element=element("open_node|node", {"event": "tree_node_realised"})), priority=6)
    entry("skills", "hud", {"kind": "technique", "unlock": "technique_slots_2"}, [t("skill"), t("attack")], priority=5)
    entry("map", "world_map", unlock("world_menu"), [t("map"), t("sel"), t("walk"), t("view"), t("tabs")],
          chain=[hud("icon:map")], priority=6)
    entry("calendar", "calendar", first_open(), [t("seasons"), t("week"), t("event"), t("go"), t("weather")])
    entry("mail", "mail", unlock("mail"), [t("stack"), t("letter"), t("parcel"), t("claim_all")], chain=[hud("icon:mail")],
          priority=4)
    entry("character", "character", unlock("character_menu"), [t("figure"), t("worn"), t("register"), t("titles"), t("tabs")],
          chain=[hud("portrait")], priority=5)
    entry("sect", "training_sect", unlock("sect_choice"), [t("hall"), t("seat"), t("next_rank"), t("tab:role")],
          chain=via_menu("training_sect"), priority=6)
    entry("shop", "shop", unlock("town_hub"), [t("wares"), t("counter"), t("bag_side"), t("purse")],
          chain=[place("shop", npc_service="shop")], priority=4)
    entry("notice_board", "notice_board", unlock("notice_board"), [t("board"), t("tab:bounties"), t("poster|bounty|to_tab")],
          chain=[place("notice_board", object_type="notice_board")], priority=4)
    entry("transfer_array", "transfer_array", unlock("transfer_array"), [t("title"), t("go|content"), t("close")],
          chain=[place("transfer_array", object_type="transfer_array")], priority=3)
    entry("crafts", "crafts", unlock("herb_gathering"), [t("tabs"), t("sel|strip"), t("hearth"), t("side")],
          chain=via_menu("crafts"), priority=4)
    entry("breakthrough", "breakthrough", {"kind": "bottleneck", "unlock": "breakthrough"},
          [t("doorway"), t("tablets"), t("pillars"), t("dishes"), t("go")],
          chain=via_menu("cultivation", "overview", "ui.cultivation.overview") + [on("cultivation", "breakthrough", tab="overview")],
          priority=9)
    entry("settings", "settings", first_open(), [t("tabs"), t("tab:access"), t("tab:controls", {"tab": "controls"}),
                                                 t("replay_tutorials")])
    entry("emotes", "emotes", first_open(), [t("known|emote"), t("unknown|emote"), t("close")])
    # HUD controls that open after the Prologue.
    entry("guard", "hud", unlock("guard"), [t("guard"), t("attack")], priority=5)
    entry("qi_pool", "hud", unlock("qi_pool"), [t("portrait"), t("skill|attack")], priority=5)
    entry("collection", "collection", unlock("collection_book"), [t("contents"), t("leaf|corner"), t("seals"), t("tab:achievements")],
          tab="collection", chain=via_menu("codex", "collection", "ui.codex.collection"), priority=3)


# ------------------------------------------------------------------ the rest of PAGES
def later():
    entry("achievements", "achievements", first_open(), [t("leaf|book"), t("corner"), t("tab:paths_above"), t("tab:seasons")],
          tab="achievements")
    entry("seasons", "seasons", first_open(), [t("book"), t("tab:codex"), t("close")], tab="seasons")
    entry("storage", "storage", unlock("storage"), [t("gourd"), t("chest"), t("deposit|chest"), t("close")],
          chain=[place("storage", object_type="storage_chest")], priority=3)
    entry("characters", "characters", unlock("idle_tasks"), [t("scroll"), t("choose"), t("task"), t("switch|choose")],
          chain=via_menu("characters"), priority=3)
    entry("posts", "posts", unlock("keeping_post"), [t("tablets"), t("turn"), t("settle_all"), t("tabs")],
          chain=via_menu("posts"), priority=3)
    entry("bench", "posts", points("bench", "apprentice_bench"), [t("bench_point"), t("bench_next"), t("bench_collect")],
          tab="bench", chain=via_menu("posts", "bench", "ui.posts.tab_bench", element("bench_point", {"event": "bench_assigned"})),
          priority=4)
    entry("pouches", "pouches", unlock("pouch_sewing"), [t("pouches"), t("sew"), t("close")],
          chain=[place("pouches", npc_service="page:pouches")], priority=3)
    entry("works", "works", unlock("post_arts"), [t("cabinet"), t("tabs"), t("tray"), t("slip")], chain=via_menu("works"),
          priority=3)
    entry("post_art", "works", points("post_art", "post_arts"), [t("art"), t("slip"), t("art_reset")], tab="arts",
          chain=via_menu("works", "arts", "ui.works.tab_arts", element("art", {"event": "post_art_learned"})), priority=4)
    entry("teleport", "teleport", unlock("teleport_stones"), [t("title"), t("go"), t("cost|close")],
          chain=[place("teleport", object_type="teleport_stone")], priority=3)
    entry("your_sect", "your_sect", unlock("your_sect"), [t("tabs"), t("found|pick"), t("pano|content"), t("tab:expeditions")],
          chain=via_menu("your_sect"), priority=3)
    entry("spirit_animals", "spirit_animals", unlock("spirit_animals"), [t("stalls"), t("leaf"), t("tabs"), t("close")],
          chain=via_menu("spirit_animals"), priority=4)
    entry("pet", "hud", unlock("spirit_animals"), [t("pet|fan")], priority=3)
    entry("companions", "companions", unlock("companions"), [t("gates"), t("pick|gates"), t("thread"), t("close")],
          chain=via_menu("companions"), priority=3)
    entry("beast_arena", "beast_arena", first_open(), [t("pit"), t("ladder"), t("fight"), t("close")])
    entry("core_exchange", "core_exchange", first_open(), [t("shelves"), t("urn"), t("tally"), t("rest")])
    entry("relations", "relations", first_open(), [t("tabs"), t("beam"), t("tab:bonds"), t("tab:fame")])
    entry("tower", "tower", first_open(), [t("sel"), t("floor"), t("climb"), t("sweep|close")])
    entry("county", "county", first_open(), [t("banner"), t("stick|tube"), t("warrant"), t("tab:relief")])
    entry("guqin", "guqin", first_open(), [t("strings"), t("play"), t("close")])
    entry("chess", "chess", first_open(), [t("board"), t("pick"), t("close")])
    entry("exchange", "exchange", unlock("currency_exchange"), [t("rates"), t("ex"), t("purses")],
          chain=[place("exchange", opens="exchange")], priority=3)
    entry("auction", "auction", first_open(), [t("lot"), t("board"), t("paddles|bid"), t("front")])
    entry("garden", "garden", unlock("herb_garden"), [t("terraces"), t("basket"), t("tend"), t("tab:racks")],
          chain=[place("garden", object_type="garden_bed")], priority=3)
    entry("fishing", "fishing", unlock("fishing"), [t("content"), t("content"), t("again|close")],
          chain=[place("fishing", object_type="fishing_spot")], priority=2)
    # The Cultivation page's tabs.
    entry("seclusion", "seclusion", unlock("seclusion"), [t("focus"), t("away"), t("tabs")], tab="seclusion",
          chain=via_menu("cultivation", "seclusion", "ui.cultivation.seclusion"), priority=3)
    entry("body", "body", unlock("body_training"), [t("body_level"), t("rungs"), t("hint")], tab="body",
          chain=via_menu("cultivation", "body", "ui.cultivation.body_tab"), priority=3)
    entry("heart", "heart", first_open(), [t("heart_panel|content"), t("relations|content"), t("tabs")], tab="heart")
    entry("dao", "cultivation", unlock("dao_tree"), [t("daos|content"), t("contemplate|content"), t("tabs")], tab="dao",
          chain=via_menu("cultivation", "dao", "ui.cultivation.dao"), priority=3)
    entry("vows", "cultivation", unlock("vows"), [t("paths"), t("vow_on|vow_off"), t("tabs")], tab="vows",
          chain=via_menu("cultivation", "vows", "ui.cultivation.paths"), priority=2)
    entry("methods", "cultivation", first_open(), [t("methods|content"), t("switch|content"), t("tabs")], tab="methods")
    # The Crafts page's crafts, and the Workshop.
    entry("cooking", "cooking", unlock("cooking"), [t("sel|strip"), t("hearth"), t("side")], tab="cooking",
          chain=via_menu("crafts", "cooking", "craft.cooking"), priority=3)
    entry("alchemy", "alchemy", unlock("alchemy"), [t("sel|strip"), t("hearth"), t("side"), t("close")], tab="alchemy",
          chain=via_menu("crafts", "alchemy", "craft.alchemy"), priority=3)
    entry("smithing", "forge", unlock("smithing"), [t("forge_mode"), t("sel|strip"), t("hearth"), t("side")], tab="smithing",
          chain=via_menu("crafts", "smithing", "craft.smithing"), priority=3)
    entry("talisman", "talisman", unlock("talisman"), [t("strip"), t("hearth"), t("side")], tab="talisman",
          chain=via_menu("crafts", "talisman", "craft.talisman"), priority=3)
    entry("guild", "guild", unlock("alchemist_guild"), [t("guild_pick|strip"), t("exam|hearth"), t("side")], tab="guild",
          chain=via_menu("crafts", "guild", "ui.crafts.guild"), priority=3)
    entry("workshop", "workshop", unlock("appraisal"), [t("wall"), t("bench"), t("tabs")], chain=via_menu("workshop"),
          priority=3)
    entry("formations", "formations", unlock("formations"), [t("place|bench"), t("bench"), t("wall")], tab="formations",
          chain=via_menu("workshop", "formations", "craft.formations"), priority=3)


def check(rows, scripts):
    ui = json.load(open(UI, encoding="utf-8"))
    ids = [r["id"] for r in rows]
    pages = set(scripts) | {"hud"}
    for r in rows:
        where = "tutorial " + r["id"]
        assert r["page"] in pages, (where, "unknown page", r["page"])
        n = len(r["tour"])
        if r["page"] == "hud":
            assert 1 <= n <= 3, (where, "a HUD tour has 1 to 3 steps", n)
        elif n:
            assert 3 <= n <= 6, (where, "a page tour has 3 to 6 steps", n)
        keys = [s["text"] for s in r["tour"]] + [s["text"] for s in r["chain"] if "text" in s]
        if r.get("hint"):
            keys.append(r["hint"])
        for s in r["chain"]:
            if s.get("name"):
                keys.append(s["name"])
            assert s["at"] in ("hud", "place", "page"), (where, s)
            if s["at"] == "page":
                assert s["page"] in pages, (where, "unknown chain page", s["page"])
        for k in keys:
            # A tab's or a tablet's name may be a generated string (craft.*); the tutorials suite finds every key.
            if k.startswith("ui.tutorial."):
                assert k in ui, (where, "no string", k)
                assert len(ui[k]) <= MAX_CHARS, (where, k, "longer than two lines", len(ui[k]))
        kind = r["trigger"]["kind"]
        assert kind in ("unlock", "points", "item", "bottleneck", "technique", "page"), (where, kind)
        if kind == "points":
            assert r["trigger"]["points"] in POINTS, (where, r["trigger"])
        if kind != "page" and r["page"] != "hud":
            assert r["chain"], (where, "a triggered guide has a chain")
    assert len(ids) == len(set(ids))


def build():
    del E[:]
    prototype()
    later()
    scripts = page_scripts()
    check(E, scripts)
    unlocks = {u["id"] for u in json.load(open(os.path.join(ROOT, "data", "unlocks.json")))["entries"]}
    for r in E:
        u = r["trigger"].get("unlock", "")
        assert not u or u in unlocks, ("tutorial", r["id"], "unknown unlock", u)
    entries("tutorials", E, page_scripts=scripts, points=POINTS)


if __name__ == "__main__":
    build()
