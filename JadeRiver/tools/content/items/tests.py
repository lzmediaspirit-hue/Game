"""The item engine's own tests (engine.py --check runs them; docs/architecture/item_engine.md, "The checks").

Each test builds families of its own with engine.compile_families, so it proves the engine, not today's specs; the
last ones hold today's specs to decision 45's numbers and to gear.py's archetypes.
"""
from . import curves, engine
from .dsl import DROP, curve, effect, family, gear, member, per, qi

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def compiled(*families, order=None):
    st = engine.compile_families(families, order)
    assert not st.errors, st.errors
    return st


def errors_of(*families, order=None):
    return engine.compile_families(families, order).errors


def ladder(**kw):
    base = dict(kind="pill", tiers=("heaven", "mystic"), words={"heaven": "three", "mystic": "five"}, id="{word}_test_pill",
                name="{Word} Test Pill", desc="+{pct}% for {minutes} minutes.", mark="spiral_up", toxicity=curve("toxicity"), group="buff",
                use=[effect("add_modifier", stat="accumulation_rate", op="flat", value=curve("speed"), duration=curve("speed", "seconds"),
                            source="test_pill")],
                sources=dict(shop={"shop_a": {"heaven": dict(price=5)}}, chest=True))
    base.update(kw)
    return family("pill.test", **base)


@test
def a_ladder_takes_its_ids_names_and_values_from_templates_and_curves():
    st = compiled(ladder())
    rows = engine.items("pills", st)
    assert [r["id"] for r in rows] == ["three_test_pill", "five_test_pill"], rows
    b, s = curves.speed("mystic")
    five = rows[1]
    assert five["name"] == "Five Test Pill" and five["ilv"] == curves.MID_ILV["mystic"]
    assert five["use"][0]["value"] == b and five["use"][0]["duration"] == s
    assert five["desc"] == "+%d%% for %d minutes." % (round(b * 100), s // 60)
    assert five["pill"]["toxicity"] == curves.PILL_TOXICITY["mystic"]
    assert list(five)[:8] == ["id", "name", "type", "grade", "ilv", "stack", "icon", "desc"], list(five)


@test
def per_gives_each_member_its_own_value_and_a_default():
    st = compiled(ladder(toxicity=per(heaven=3, default=9)))
    assert [r["pill"]["toxicity"] for r in engine.items("pills", st)] == [3, 9]


@test
def row_pins_tweak_the_finished_row_in_place_add_at_the_end_and_drop():
    st = compiled(ladder(row=dict(stack=20, burst=True, soul_effect=DROP)))
    row = engine.items("pills", st)[0]
    keys = list(row)
    assert row["stack"] == 20 and keys.index("stack") == 5, keys
    assert keys[-1] == "burst" and "soul_effect" not in row, keys


@test
def a_member_nothing_hands_out_is_refused():
    errs = errors_of(ladder(sources=dict(shop={"shop_a": {"heaven": {}}})))
    assert any("five_test_pill" in e and "nothing hands it out" in e for e in errs), errs
    assert not any("three_test_pill" in e for e in errs), errs


@test
def an_outside_source_as_a_list_covers_only_its_tiers():
    errs = errors_of(ladder(sources=dict(reward=["heaven"])))
    assert any("five_test_pill" in e for e in errs) and not any("three_test_pill" in e for e in errs), errs


@test
def a_mark_is_the_source_of_a_row_nothing_hands_out():
    st = compiled(family("pill.lone_pill", kind="pill", tiers=("plain",), mark="knot", toxicity=1, group="utility", desc="x", use=[],
                         sources=dict(mark="system")))
    assert engine.items("pills", st)[0]["source"] == "system"
    assert errors_of(family("pill.odd_pill", kind="pill", tiers=("plain",), mark="knot", toxicity=1, group="utility", desc="x", use=[],
                            sources=dict(mark="someday")))


@test
def shop_lines_go_to_their_markers_and_the_rest_to_the_end_of_the_shop():
    st = compiled(ladder(sources=dict(shop={"shop_a": {"heaven": dict(price=5), "mystic": dict(rotation=True)}, "shop_b": ["mystic"]})))
    shops = [{"id": "shop_a", "stock": [{"item": "rice"}], "rotation": {"count": 1, "pool": [engine.F("five_test_pill"), {"item": "tea"}]}},
             {"id": "shop_b", "stock": [{"item": "salt"}]}]
    a, b = engine.shelves(shops, st)
    assert a["stock"] == [{"item": "rice"}, {"item": "three_test_pill", "price": 5}], a
    assert a["rotation"]["pool"] == [{"item": "five_test_pill"}, {"item": "tea"}], a
    assert b["stock"] == [{"item": "salt"}, {"item": "five_test_pill"}], b


@test
def a_marker_no_family_declares_and_a_shop_that_is_not_there_are_errors():
    st = compiled(ladder())
    for shops in ([{"id": "shop_a", "stock": [engine.F("rice")]}], [{"id": "elsewhere", "stock": []}]):
        try:
            engine.shelves(shops, st)
        except SystemExit:
            continue
        raise AssertionError("shelves() took %r" % shops)


@test
def a_recipe_writes_its_row_its_learn_line_and_moves_after_a_pin():
    fam = ladder(recipe=dict(inputs=[("rice", 2)], time_s=curve("recipe_time"), element="water", hidden=True,
                             learn={"shop_a": {"mystic": dict(price=9, realm="sage_1")}}))
    other = family("pill.other_pill", kind="pill", tiers=("earth",), mark="knot", toxicity=1, group="utility", desc="x", use=[],
                   recipe=dict(inputs=[("tea", 1)], after="three_test_pill"))
    st = compiled(other, fam)
    rows = engine.recipes("alchemy", st)
    assert [r["id"] for r in rows] == ["three_test_pill", "other_pill", "five_test_pill"], rows
    assert list(rows[0]) == ["id", "craft", "grade", "inputs", "outputs", "time_s", "hidden"] and rows[0]["time_s"] == curves.RECIPE_TIME["heaven"]
    assert engine.recipe_meta("five_test_pill", st) == ("water", None)
    learn = [x for m in st.members for x in m["lines"] if x[2]["item"] == "recipe_scroll"]
    assert learn == [("shop_a", "stock", {"item": "recipe_scroll", "learn": "five_test_pill", "price": 9,
                                         "requires": {"all": [{"kind": "realm_at_least", "realm": "sage_1"}]}})], learn


@test
def order_pins_and_the_grade_order_lay_out_a_section():
    a = family("pill.a_pill", kind="pill", tiers=("earth",), mark="k", toxicity=1, group="utility", desc="x", use=[], sources=dict(chest=True))
    b = family("pill.b_pill", kind="pill", tiers=("common",), mark="k", toxicity=1, group="utility", desc="x", use=[], sources=dict(chest=True))
    assert [r["id"] for r in engine.items("pills", compiled(a, b))] == ["a_pill", "b_pill"]
    assert [r["id"] for r in engine.items("pills", compiled(a, b, order={"pills": ["b_pill"]}))] == ["b_pill", "a_pill"]
    assert [r["id"] for r in engine.items("pills", compiled(a, b, order={"pills": "grade"}))] == ["b_pill", "a_pill"]
    assert errors_of(a, b, order={"pills": ["c_pill"]})


@test
def a_section_no_host_places_is_an_error():
    st = compiled(ladder())
    engine.begin("items", st)
    try:
        engine.end("items", st)
    except SystemExit:
        return
    raise AssertionError("end() let the section pills go unplaced")


@test
def a_herb_family_names_its_ages_and_writes_its_seed():
    st = compiled(family("herb.test_root", kind="herb", nature="hot", young_age=False,
                         members=[member(10, "common", desc="A root.", roles=["principal"], raw=dict(use=[qi(0.024)], toxicity=20)),
                                  member(100, "earth", desc="An old root.", roles=["principal"])],
                         seed=dict(grade="common", desc="Seeds.", sources=dict(garden=True)), sources=dict(gather=True)))
    young, old = engine.items("herbs", st)
    assert (young["id"], young["name"], old["id"], old["name"]) == ("test_root", "Test Root", "test_root_100", "Test Root (100 yr)")
    assert young["use"][0]["amount"] == curves.cultivation(0.024, "common") and young["family"] == "accumulation"
    assert "+%s cultivation" % format(young["use"][0]["amount"], ",") in young["desc"] and "raw" not in old
    assert engine.items("seeds", st)[0]["seed"] == {"family": "test_root"}
    assert engine.herb_ages(st) == {"test_root": ("test_root", 10), "test_root_100": ("test_root", 100)}


@test
def gear_runs_over_the_grades_with_its_word_and_a_forged_recipe():
    st = compiled(gear("test_blade", kind="weapon", tiers=("plain", "common"), words={"plain": "training", "common": "iron"},
                       id="{word}_test_blade", name="{Word} Test Blade", appearance="sword", attribute="agility",
                       attribute_req=per(plain=8, common=18), ilv=per(plain=5, default=None),
                       recipe=lambda m: None if m["grade"] == "plain" else dict(craft="smithing", inputs=[("copper_ore", 6)]),
                       sources=dict(drop=True)))
    plain, iron = engine.items("weapons", st)
    assert (plain["id"], plain["name"], plain["ilv"], plain["family"]) == ("training_test_blade", "Training Test Blade", 5, "test_blade")
    assert iron["ilv"] == curves.MID_ILV["common"] and iron["attribute_req"] == {"agility": 18}
    assert [r["id"] for r in engine.recipes("smithing", st)] == ["iron_test_blade"]


@test
def a_pill_icon_is_its_vessel_and_its_grades_kit():
    st = compiled(ladder(icon=dict(pill="cyan", ink=("qi", -1))))
    assert engine.pill_icons(st) == [("three_test_pill", "buff", "heaven", "spiral_up", "cyan", ("qi", -1)),
                                     ("five_test_pill", "buff", "mystic", "spiral_up", "cyan", ("qi", -1))]


# ----------------------------------------------------------------------------------------------- today's specs
@test
def decision_45s_fixed_numbers_hold():
    rows = {m["id"]: m["row"] for m in engine.members()}
    assert rows["qi_gathering_pill"]["use"] == [{"kind": "add_progress", "amount": 420}] and rows["qi_gathering_pill"]["desc"] == "+420 cultivation."
    assert [rows["riverreed_ginseng_%d" % a]["use"][0]["amount"] for a in (10, 100, 1000)] == [130, 240, 800]
    flow = rows["qi_flow_pill"]["use"][0]
    assert (flow["value"], flow["duration"]) == (0.2, 3600) == curves.speed("earth")


@test
def every_weapon_family_is_its_archetypes_and_every_archetype_family_has_one():
    from gear import ARCHETYPES
    fams = {m["fid"].split(".", 1)[1]: m for m in engine.members("weapon")}
    listed = {f for a in ARCHETYPES.values() for f in a["families"]}
    assert set(fams) == listed, (sorted(fams), sorted(listed))
    for fam in engine.state().families:
        if fam.kind == "weapon":
            assert fam.stem in ARCHETYPES[fam.fields["archetype"]]["families"], fam.fid


@test
def every_family_member_has_a_source_and_every_shop_line_a_shop():
    st = engine.state()
    assert not engine._static_checks(st)
    shops = {s["id"] for s in engine._table("shops")["entries"]}
    for m in st.members:
        for shop, _, _ in m["lines"]:
            assert shop in shops, (m["id"], shop)


def run():
    """(tests run, failures as lines)."""
    failed = []
    for fn in TESTS:
        try:
            fn()
        except Exception as e:   # noqa: BLE001  (a test reports whatever broke it)
            failed.append("test %s: %s: %s" % (fn.__name__, type(e).__name__, e))
    return len(TESTS), failed
