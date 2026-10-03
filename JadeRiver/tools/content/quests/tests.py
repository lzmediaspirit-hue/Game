"""The quest engine's own tests (engine.py --check runs them): the templates, the derived rooms, realms and pay, the
row's layout and pins, the band table and the daily board, on a small world of their own, and today's specs."""
import copy
import traceback

from . import engine as E
from . import bands as B
from .spec import (AUTO, DROP, PAY, SpecError, side, daily, job, clear, fetch, deliver, gather, talk, spar, escort, reach,
                   step, item, fx, taels, stones)


def _world():
    """Two fields, a town, a quarry and a shrine: foes that spawn in more than one, a gated spawn, a quest drop, nodes, a
    person at home and one with a spar post."""
    rooms = [
        {"id": "a_field", "name": "A Field", "level_range": [4, 8], "objects": [
            {"type": "herb_patch", "item": "moss"}, {"type": "npc", "npc": "farmer"}],
         "spawns": [{"enemy": "rat", "max": 3}, {"enemy": "boar", "max": 2}]},
        {"id": "b_field", "name": "B Field", "level_range": [10, 14], "objects": [
            {"type": "herb_patch", "item": "moss"}, {"type": "herb_patch", "item": "moss"}, {"type": "ore_vein", "item": "iron"}],
         "spawns": [{"enemy": "rat", "max": 3}, {"enemy": "wolf", "max": 4},
                    {"enemy": "boar", "max": 9, "requires": {"all": [{"kind": "quest_active", "quest": "x"}]}}]},
        {"id": "c_quarry", "name": "C Quarry", "level_range": [2, 2], "objects": [{"type": "spar_post", "opponent": "chief"}],
         "spawns": [{"enemy": "boar", "max": 1}, {"enemy": "pet_boar", "max": 5, "wild_pet": True}]},
        {"id": "town", "name": "Town", "level_range": [0, 0], "objects": [
            {"type": "npc", "npc": "elder"}, {"type": "npc", "npc": "farmer"}], "spawns": []},
    ]
    loot = [{"id": "rat", "groups": [{"chance": 0.5, "pick": [{"item": "tail"}]}]},
            {"id": "wolf", "groups": [], "rare": [{"item": "fang"}], "quest_drops": [{"item": "tail", "quest": "wolf_tails"}]},
            {"id": "boar", "groups": [{"pick": [{"item": "hide"}]}]}]
    enemies = [{"id": "rat", "name": "Reed Rat", "level": [4, 5]}, {"id": "wolf", "name": "Mist Wolf", "level": [10, 13]},
               {"id": "boar", "name": "Boar", "level": [5, 6]}, {"id": "chief", "name": "Chief Yan"}, {"id": "pet_boar", "name": "Piglet"}]
    items = [{"id": x, "name": n} for x, n in (("tail", "Rat Tail"), ("fang", "Wolf Fang"), ("hide", "Boar Hide"), ("moss", "Willow Moss"),
                                               ("iron", "Iron"), ("soup", "Fish Soup"), ("leech", "Marsh Leech"), ("cherry", "Cherry"))]
    npcs = [{"id": x, "name": n} for x, n in (("elder", "Elder Gao"), ("farmer", "Farmer Li"), ("chief", "Chief Yan"))]
    return E.World(rooms, loot, enemies, items, npcs, homes={"farmer": "town"})


def _row(q, w=None):
    return E.compile_quest(q, w or _world())


def t_row_layout():
    r = E.quest_row("q", "Q", "side", "elder", [{"kind": "x"}], [taels(5)], None, ["hi"], ["bye"], [], requires={"all": []},
                    marker="gold", chapter="1")
    assert list(r) == ["id", "name", "kind", "giver", "hand_in", "marker", "objectives", "rewards", "offer_text", "complete_text",
                       "requires", "chapter"], list(r)
    assert r["hand_in"] == "elder" and r["marker"] == "gold"
    d = E.quest_row("guos_old_wound", "G", "side", "elder", [], [taels(1)], "")
    assert d["hand_in"] == "" and d["marker"] == "blue" and d["rewards"][-1] == {"kind": "deed", "deed": "guos_old_wound"}, d


def t_templates():
    w = _world()
    assert list(clear("rat", 3)) == ["kind", "text", "count", "enemy"]
    assert list(fetch("tail", 2)) == ["kind", "text", "count", "item", "consume"]
    assert list(deliver("soup", 2)) == ["kind", "text", "count", "consume", "item"]
    assert list(gather("moss", 2, craft="herbs")) == ["kind", "text", "count", "item", "craft"]
    assert [s["kind"] for s in escort("farmer", "b_field")] == ["talk_to", "reach_room"]
    texts = [E.text_of(s, w) for s in (clear("rat", 3), clear("wolf", 2), clear("rat", 1), fetch("tail", 2), deliver("soup", 2),
                                       gather("moss", 3), gather("iron", 4), talk("elder"), spar("chief"), spar(), reach("a_field"))]
    assert texts == ["Defeat Reed Rats", "Defeat Mist Wolves", "Defeat Reed Rat", "Bring Rat Tails", "Deliver Fish Soups",
                     "Gather Willow Moss", "Mine Iron", "Talk to Elder Gao", "Win a spar against Chief Yan", "Win a spar",
                     "Reach A Field"], texts
    assert [E.plural(x) for x in ("Marsh Leech", "Cherry", "Bamboo Monkey", "Mist Lotus", "Box")] == \
        ["Marsh Leeches", "Cherries", "Bamboo Monkeys", "Mist Lotus", "Boxes"]
    assert clear("rat", 2, "Chase the rats")["text"] == "Chase the rats"
    try:
        side("bad", {"kind": "kill"}, giver="elder")
        raise AssertionError("a step that is no template's was taken")
    except SpecError:
        pass


def t_rooms():
    w = _world()
    lead = lambda s, q="q", g="elder", h=None: w.lead(s.lead, q, g, h)
    assert lead(clear("rat")) == "a_field", "a tie: the lower band"
    assert lead(clear("wolf")) == "b_field"
    assert lead(clear("boar")) == "a_field", "the gated spawn and the wild pets do not count"
    assert lead(fetch("hide")) == "a_field"
    assert lead(fetch("moss")) == "b_field", "the most nodes"
    assert lead(fetch("tail")) == "a_field" and lead(fetch("tail"), q="wolf_tails") == "b_field", "a quest drop counts for its quest"
    assert lead(gather("iron")) == "b_field" and lead(deliver("soup")) is None
    assert lead(talk("farmer")) == "town" and lead(talk("elder")) is None and lead(talk("farmer"), g="x", h="farmer") is None
    assert lead(spar("chief")) == "c_quarry" and lead(spar("chief"), g="chief") is None
    assert lead(reach("a_field")) == "a_field" and lead(escort("farmer", "b_field")[1]) == "b_field"
    r = _row(side("q", talk("farmer"), clear("wolf", 2), giver="farmer"))
    assert r["target_room"] == "b_field", "the first step that leads somewhere"
    assert "target_room" not in _row(side("q", clear("wolf"), giver="elder", target_room=None))
    assert _row(side("q", clear("wolf"), giver="elder", target_room="town"))["target_room"] == "town"


def t_realm_and_requires():
    w = _world()
    req = lambda **k: _row(side("q", clear("wolf"), giver="elder", **k), w).get("requires")
    assert req() == {"all": [{"kind": "realm_at_least", "realm": "qi_kindling_3"}]}, "the middle of 10-14 is Level 12"
    assert req(after="p") == {"all": [{"kind": "quest_done", "quest": "p"}]}, "a quest that follows another opens with it"
    assert req(after="p", during="d", realm="bone_forging_2", needs=[{"kind": "unlock", "system": "s"}]) == {"all": [
        {"kind": "quest_done", "quest": "p"}, {"kind": "quest_active", "quest": "d"}, {"kind": "realm_at_least", "realm": "bone_forging_2"},
        {"kind": "unlock", "system": "s"}]}
    assert req(realm=None) is None and req(requires={"any": []}) == {"any": []}
    assert _row(side("q", reach("town"), giver="farmer"), w).get("requires") is None, "a town has no band"


def t_pay_and_keys():
    w = _world()
    r = _row(side("q", clear("rat"), giver="elder", gives=[item("hide", 2)]), w)
    assert isinstance(r["rewards"][0], E.Pay) and r["rewards"][1] == item("hide", 2), "the pay first when PAY is not named"
    r = _row(side("q", clear("rat"), giver="elder", gives=[fx("add_bond", amount=1), PAY], pay=7), w)
    assert r["rewards"][0]["kind"] == "add_bond" and r["rewards"][1].pinned == 7
    assert _row(side("q", clear("rat"), giver="elder", pay=stones(9)), w)["rewards"] == [stones(9)]
    assert _row(side("q", clear("rat"), giver="elder", pay=None, gives=[item("hide")]), w)["rewards"] == [item("hide")]
    rows = [dict(_row(side("q", clear("rat"), giver="elder"), w), tier="qi_kindling_4"),
            dict(_row(side("p", clear("rat"), giver="elder", pay=7), w), tier="sage_2")]
    assert E.settle(rows) == 2
    assert rows[0]["rewards"] == [B.pay(B.band_at(13))] and rows[1]["rewards"] == [{"kind": "grant_currency", "currency": "spirit_stone", "amount": 7}]
    r = _row(side("q", clear("rat"), giver="elder", on_accept=[item("hide")], chapter="9", offered_by_unlock=True, marker="gold",
                  row={"offer_text": DROP, "extra": 1}, offer="x"), w)
    assert list(r)[8:] == ["requires", "offered_by_unlock", "chapter", "target_room", "on_accept", "extra"], list(r)


def t_bands():
    import realms as R
    errs = E.check_bands([])
    assert not errs, errs
    assert B.band_at(0)[0] == "mortal" and B.band_at(7)[0] == "bone_forging" and B.band_at(64)[0] == "sage" and B.band_at(165)[0] == "inner_heaven"
    assert B.experience(B.band_at(2)) == 90 and B.experience(B.band_at(12)) == 530, "phase 1's numbers (cultivation_loop.md §16.3)"
    for b in B.BANDS:
        for lv in B.levels(b):
            kind = B.qp(b)
            from stats import QUEST_CULTIVATION
            assert B.experience(b) == R.cultivation(QUEST_CULTIVATION[kind], lv), (b, lv)
    assert B.qp(B.band_at(63)) == "side" and B.qp(B.band_at(64)) == "act2_side"


def t_board():
    w = _world()
    st = E.State([], [daily("hunt", "Hunt", job("Rats", clear("rat", 8)), job("Wolves", clear("wolf", 6), levels=(1, 2))),
                      daily("gather", "Gather", job("Moss", gather("moss", 5)), requires={"all": []}),
                      daily("odd", "Odd", job("Cook", step("craft", "Cook three dishes", 3, craft="cooking")), job("Spar", spar()))])
    m = E.missions(st, w)
    assert [list(r) for r in m] == [["id", "name", "options"], ["id", "name", "requires", "options"], ["id", "name", "options"]]
    o0 = m[0]["options"][0]
    assert list(o0) == ["name", "objective", "min_level", "max_level"] and list(o0["objective"]) == ["kind", "enemy", "count", "text"]
    assert (o0["min_level"], o0["max_level"], o0["objective"]["text"]) == (3, 9, "Defeat Reed Rats"), o0
    assert (m[0]["options"][1]["min_level"], m[0]["options"][1]["max_level"]) == (1, 2)
    assert (m[1]["options"][0]["min_level"], m[1]["options"][0]["max_level"]) == (3, 23), "from the first field it grows in"
    assert m[2]["options"][0]["objective"] == {"kind": "craft", "craft": "cooking", "count": 3, "text": "Cook three dishes"}
    assert m[2]["options"][1]["objective"] == {"kind": "win_spar", "count": 1, "text": "Win a spar"}
    assert (m[2]["options"][1]["min_level"], m[2]["options"][1]["max_level"]) == (0, E.BOARD_TOP)


def t_errors():
    w = _world()
    st = E.State([("s", [side("q", clear("ghost"), fetch("nothing"), giver="nobody", gives=[item("air")])])], [])
    errs = E.check_specs([], st, w)
    assert any("no person nobody" in e for e in errs) and any("no enemy ghost" in e for e in errs) \
        and any("gives no item air" in e for e in errs) and any("nothing leads" in e for e in errs), errs
    try:
        E.State([("s", [side("q", clear("rat"), giver="elder")]), ("t", [side("q", clear("rat"), giver="elder")])], [])
        raise AssertionError("a quest written twice was taken")
    except SpecError:
        pass
    try:
        E.rows("nowhere", E.State([], []), w)
        raise AssertionError("a section nobody wrote was placed")
    except SpecError:
        pass


def t_todays_specs():
    """E5's own quests derive their room, realm and pay (no pins); every engine quest pays the band at its tier or says
    otherwise in its spec; the companions' favours are their template's."""
    st = E.state()
    new = dict(st.sections)["act1"][-4:]
    for q in new:
        assert q["target_room"] is AUTO and q["realm"] is AUTO and q["pay"] is AUTO and q["requires"] is AUTO, q["id"]
    favours = [q for q in st.quests if q["keys"].get("chapter") == "companion"]
    assert len(favours) == 12 and all(q["pay"] == 80 and q["target_room"] is None for q in favours)
    w = E.world()
    for q in st.quests:
        r = E.compile_quest(q, w)
        assert r["id"] == q["id"] and r["kind"] == "side", q["id"]
    a = json_dump(st, w)
    assert a == json_dump(st, w), "two compiles differ"


def json_dump(st, w):
    import json
    return json.dumps([[E.compile_quest(q, w) for q in st.quests], E.missions(st, w)], sort_keys=True)


TESTS = [t_row_layout, t_templates, t_rooms, t_realm_and_requires, t_pay_and_keys, t_bands, t_board, t_errors, t_todays_specs]


def run():
    failed = []
    for t in TESTS:
        try:
            t()
        except Exception as e:  # noqa: BLE001 (a test's failure, whatever it is, is reported)
            failed.append("tests.py %s: %s" % (t.__name__, (str(e) or type(e).__name__) + ("" if isinstance(e, AssertionError) else
                                                                                          " " + traceback.format_exc(limit=2).splitlines()[-1])))
    return len(TESTS), failed
