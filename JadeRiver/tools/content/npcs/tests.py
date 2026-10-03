"""The NPC engine's own tests (engine.py --check runs them; docs/architecture/npc_engine.md, "The checks").

Each test builds specs, rows and layouts of its own, so it proves the engine, not today's specs (the gate's other parts
hold today's specs to the built data): the look, a row's keys and pins, the one-off rows' places, the role templates,
the engine's own placements, and every kind of work spot anchor on a sample layout, a moved prop moving its worker.
"""
import copy
import math

from . import engine, spots as SPOTS
from .spec import DROP, ROLE, extra, look, npc, place, role, staff, work

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def raises(fn, kind=Exception):
    try:
        fn()
    except kind as e:
        return str(e)
    raise AssertionError("no error raised")


def state(*specs):
    return engine.State([s for s in specs if s["kind"] == "npc"], [s for s in specs if s["kind"] == "extra"])


# ------------------------------------------------------------------------------------------------ rows
@test
def a_look_is_the_outfit_story_py_always_wrote():
    import story
    pairs = [(look("ponytail:2", "cardigan:white", "straight", "slippers"), story.outfit("ponytail", 2, "cardigan", "straight", "slippers", shirt_dye="white")),
             (look("topknot", "disciple:jade", "martial:jade", "boots", weapon="sword", hat="guan", cape="solid"),
              story.outfit("topknot", 0, "disciple", "martial", "boots", hat="guan", cape="solid", weapon="sword", shirt_dye="jade", pants_dye="jade")),
             (look("flowing:5", "scholar", "scholar:grey", "folded"), story.outfit("flowing", 5, "scholar", "scholar", "folded", pants_dye="grey"))]
    for a, b in pairs:
        assert a == b and list(a) == list(b), (a, b)


@test
def a_row_takes_its_keys_in_the_order_of_KEYS_and_its_pins_last():
    s = npc("t_a", "A", "Tester", look("ponytail", "vneck:jade", "cuffed", "boots"), ["Hello."], ["Hm."], services=["shop:x"],
            sect="jade_sect", tree="t_tree", scale=0.9, service_labels={"shop:x": "Wares"}, concealed=["Small, are you?"],
            row={"tint": "#ffffff", "barks": DROP, "extra_key": 3})
    r = engine.row(s)
    assert list(r) == ["id", "name", "title", "outfit", "lines", "services", "scale", "tree", "service_labels", "sect",
                       "concealed_lines", "tint", "extra_key"], list(r)
    assert r["concealed_lines"] == ["Small, are you?"] and r["tint"] == "#ffffff" and "barks" not in r
    assert raises(lambda: npc("t_b", "B", "T", look(), [], colour="red"), ValueError).startswith("npc t_b: unknown keys colour")


@test
def a_rows_copy_is_its_own():
    s = npc("t_a", "A", "Tester", look(), ["Hello."])
    r = engine.row(s)
    r["lines"].append("changed")
    r["outfit"]["hair"] = "changed"
    assert engine.row(s)["lines"] == ["Hello."] and engine.row(s)["outfit"]["hair"] == "short_knot"


@test
def one_off_rows_stand_after_the_row_they_name():
    st = state(npc("t_a", "A", "T", look(), []), npc("t_b", "B", "T", look(), []), npc("t_c", "C", "T", look(), []))
    hand = [({"id": "h_1"}, "t_a"), ({"id": "h_2"}, "h_1"), ({"id": "h_3"}, None), ({"id": "h_4"}, "t_c")]
    assert [r["id"] for r in engine.rows(hand, st)] == ["t_a", "h_1", "h_2", "t_b", "t_c", "h_4", "h_3"]
    assert "no row is" in raises(lambda: engine.rows([({"id": "h_9"}, "nobody")], st), ValueError)
    assert "a spec and a hand row" in raises(lambda: engine.rows([({"id": "t_b"}, None)], st), ValueError)
    assert "written twice" in raises(lambda: state(npc("t_a", "A", "T", look(), []), npc("t_a", "A", "T", look(), [])), ValueError)


@test
def a_role_template_fills_each_sect_and_the_spec_wins():
    sects = {"red": dict(key="red", Sect="Red", sect="red_sect", dye="crimson", weapon="spear")}
    roles = {"guard": role("{Sect} Sect guard", dict(hair="topknot", shirt="disciple:{dye}", pants="martial", shoes="boots", weapon="{weapon}"),
                           ["We guard the {Sect} gate."], ["Halt."], services=["shop:{key}_armoury"], loop="{weapon}",
                           service_labels={"shop:{key}_armoury": "Armoury"})}
    s = staff("guard", roles, sects["red"], "Guard Ma", at=[place("r_gate", work=work(ROLE, auto=2)), place("r_yard", work=work("watch", auto=1))])
    r = engine.row(s)
    assert r["id"] == "red_guard" and r["title"] == "Red Sect guard" and r["lines"] == ["We guard the Red gate."]
    assert r["outfit"]["shirt_dye"] == "crimson" and r["outfit"]["weapon"] == "spear" and r["services"] == ["shop:red_armoury"]
    assert list(r)[-2:] == ["service_labels", "sect"] and r["sect"] == "red_sect", list(r)
    assert [p["work"]["loop"] for p in s["at"]] == ["spear", "watch"] and s["at"][0]["oid"] == "npc_red_guard"
    t = staff("guard", roles, sects["red"], "Guard Lu", title="Gate captain", lines=["Mine."])
    assert engine.row(t)["title"] == "Gate captain" and engine.row(t)["lines"] == ["Mine."]
    assert roles["guard"]["title"] == "{Sect} Sect guard"     # the template itself is left as it was


@test
def work_and_extras_are_written_per_room():
    st = state(npc("t_a", "A", "T", look(), [], at=[place("r_one", work=work("sweep", [1, 2, "s"])), place("r_two", "npc_a_two"),
                                                    place("r_two", "npc_a_yard", work=work("watch", auto=2))]),
               extra("x_t", "r_one", look("short_knot", "vneck:grey", "cuffed", "folded"), work("fish", "water_edge@4,5")))
    w = engine.work(st)
    assert w == {"r_one": {"npc_t_a": {"loop": "sweep", "spots": [[1, 2, "s"]]}}, "r_two": {"npc_a_yard": {"loop": "watch", "auto": 2}}}, w
    x = engine.extras(st)
    assert x == {"r_one": [{"id": "x_t", "outfit": look("short_knot", "vneck:grey", "cuffed", "folded"), "loop": "fish",
                            "spots": ["water_edge@4,5"]}]}, x
    assert "spots or auto" in raises(lambda: work("sweep", [1, 2, "s"], auto=2), ValueError)
    assert "names its spots" in raises(lambda: extra("x_u", "r_one", look(), work("fish", auto=1)), ValueError)


@test
def a_placement_the_engine_makes_writes_the_rooms_object_and_anchor():
    s = npc("t_new", "New", "T", look(), ["Hi."], at=[place("gh_hamlet_square", anchor="commons@20", facing=-1, visible_if={"all": []}),
                                                      place("gh_hamlet_square", "npc_t_new_two", anchor=(30, 18), side=[640, 800])])
    st = state(s)
    assert engine.anchors("gh_hamlet_square", st) == {"npc_t_new": "commons@20", "npc_t_new_two": (30, 18)}
    objs = engine.objects("gh_hamlet_square", [0, 480, 2560, 480], st=st)
    assert [list(o) for o in objs] == [["id", "type", "at", "npc", "facing", "visible_if"], ["id", "type", "at", "npc"]], objs
    # the anchor's column across the room (56 cells): cell 20's middle, 1.5 cells in from each edge
    assert objs[0]["at"] == [int(round((20 + 0.5 - 1.5) / 53.0 * 2560)), 864] and objs[1]["at"] == [640, 800], objs
    assert "belong to a placement the engine makes" in raises(lambda: place("r", facing=1), ValueError)
    # a side-view point keeps the talk's reach clear of the room's other things: the nearest step along the ground
    x0 = objs[0]["at"][0]
    moved = engine.objects("gh_hamlet_square", [0, 480, 2560, 480], taken=[[x0 + 20, 860]], st=state(s))
    assert moved[0]["at"] == [x0 - 3 * engine.SIDE_STEP, 864], moved      # 140 from it; two steps east is 60
    assert moved[1]["at"] == [640, 800] and abs(moved[0]["at"][0] - (x0 + 20)) > engine.SIDE_CLEAR


# ------------------------------------------------------------------------------------------------ work spots
def sample(shift=0):
    """A 20 x 12 meadow, the river along its south (rows 9 to 11), a wash tub, a laundry line, a shrine, a way west; the
    tub and the line `shift` cells east."""
    levels = ["0" * 20] * 9 + ["~" * 20] * 3
    return {"id": "t_room", "size": [20, 12], "levels": levels, "stairs": [], "spawn": [2, 4],
            "props": [{"kind": "wash_tub", "x": 6 + shift, "y": 7}, {"kind": "laundry_line", "x": 9 + shift, "y": 4}],
            "place": {"npc_washer": [7 + shift, 6], "shrine": [16, 6], "npc_sweeper": [15, 3]},
            "portals": {"west": {"at": [0, 4], "dir": "w", "arrive": [1.5, 4], "span": 3}}}


def resolved(d, who, spot_list, home="place"):
    import topdown_rooms as TR
    h = d["place"][who] if home == "place" else home
    return SPOTS.resolve(SPOTS.Room(d["id"], d, TR.Grid(d)), who, spot_list, h)


@test
def each_spot_anchor_resolves_as_its_rule_says():
    import topdown_life as LIFE
    import topdown_rooms as TR
    d = sample()
    g = TR.Grid(d)
    got = resolved(d, "npc_washer", ["by:wash_tub:wash", "by:laundry_line>s:hang", "water_edge", "home", "open"])
    home = d["place"]["npc_washer"]
    tub = [(6, 7)]
    line = [(9, 4), (10, 4), (11, 4)]
    a, b, c, h, o = got
    assert min(max(abs(a[0] - x), abs(a[1] - y)) for x, y in tub) == 1 and a[3] == "wash", a
    assert a[2] == SPOTS.facing_to(6 - a[0], 7 - a[1]), a
    assert min(max(abs(b[0] - x), abs(b[1] - y)) for x, y in line) == 1 and b[2] == "s" and b[3] == "hang", b
    assert d["levels"][c[1] + 1][c[0]] == "~" and c[2] == "s", c         # beside the river, facing it
    assert h == [home[0], home[1], "s"], h
    for s in got:
        assert math.hypot(s[0] - home[0], s[1] - home[1]) <= LIFE.LEASH - SPOTS.MARGIN + 1e-9, s
    assert not LIFE.check_spots("t", g, home, got, {"steps": {"wash": [], "hang": []}}), LIFE.check_spots("t", g, home, got, {"steps": {"wash": [], "hang": []}})
    near = resolved(d, "npc_sweeper", ["near:shrine", "open"])
    assert max(abs(near[0][0] - 16), abs(near[0][1] - 6)) in (1, 2) and near[0][2] == SPOTS.facing_to(16 - near[0][0], 6 - near[0][1]), near


@test
def a_moved_prop_moves_its_worker_and_the_choice_is_deterministic():
    one = resolved(sample(), "npc_washer", ["by:wash_tub:wash", "by:laundry_line:hang"])
    again = resolved(sample(), "npc_washer", ["by:wash_tub:wash", "by:laundry_line:hang"])
    moved = resolved(sample(shift=2), "npc_washer", ["by:wash_tub:wash", "by:laundry_line:hang"])
    assert one == again
    assert [[s[0] + 2] + s[1:] for s in one] == moved, (one, moved)


@test
def an_extras_first_spot_looks_round_its_point_and_is_its_home():
    d = sample()
    got = resolved(d, "x_fisher", ["water_edge@3", "open"], home=None)
    assert got[0][1] == 8 and abs(got[0][0] - 3) <= 1 and got[0][2] == "s", got     # the bank row, by column 3
    assert 1.0 <= math.hypot(got[1][0] - got[0][0], got[1][1] - got[0][1]) <= 2.1, got
    assert "needs" not in "".join(map(str, got))
    err = raises(lambda: resolved(d, "x_fisher", ["water_edge"], home=None), SPOTS.SpotError)
    assert "names the point it looks round" in err, err


@test
def a_spot_that_fits_nowhere_or_reads_wrong_says_so():
    d = sample()
    assert "no spot fits" in raises(lambda: resolved(d, "npc_sweeper", ["water_edge"]), SPOTS.SpotError)
    assert "the room has no woodpile" in raises(lambda: resolved(d, "npc_washer", ["by:woodpile"]), SPOTS.SpotError)
    assert "places no well" in raises(lambda: resolved(d, "npc_washer", ["near:well"]), SPOTS.SpotError)
    assert "an anchor is home" in raises(lambda: SPOTS.parse("beside the tub"), SPOTS.SpotError)
    assert SPOTS.parse("auto:water_edge@3.5,8>sw:wash") == ("water_edge", "", (3.5, 8.0), "sw", "wash")
    assert SPOTS.parse("by:laundry_line:hang") == ("by", "laundry_line", None, None, "hang")


@test
def pinned_spots_stay_as_written():
    d = sample()
    pins = [[7.4, 6.2, "e", "wash"], [8.0, 5.5, "nw"]]
    assert resolved(d, "npc_washer", copy.deepcopy(pins)) == pins


def run():
    """Every test: (how many ran, the failures)."""
    failed = []
    for fn in TESTS:
        try:
            fn()
        except Exception as e:  # noqa: BLE001  a test's failure, whatever it raised
            failed.append("test %s: %s: %s" % (fn.__name__, type(e).__name__, e))
    return len(TESTS), failed
