"""The companions' favours (S26): three a companion, the first once they travel with you, each after the one before.
Placed by story.py's side_quests() (section act1), after the valley's threads.

`favours(id, name, chain)` is their template: a chain of (quest id, title, step, gift), each paying a bond of ten and
the companion's eighty taels (a pin: the band table would pay by the tier), the gift after it. A favour leads nowhere
in particular: the companion is with you (target_room pinned None)."""
from content.quests.spec import side, clear, fetch, reach, item, fx, PAY


def favours(cid, name, chain):
    out = []
    prev = None
    for qid, title, s, gift in chain:
        out.append(side(qid, s, giver=cid, name=title, after=prev or (),
                         needs=[] if prev else [{"kind": "companion_owned", "companion": cid}], target_room=None,
                         chapter="companion", offer="%s has a favour to ask." % name, done="%s smiles. \"Thank you.\"" % name,
                         pay=80, gives=[fx("add_bond", amount=10), PAY] + ([item(gift, 1)] if gift else [])))
        prev = qid
    return out


def _kill(enemy, n):
    return clear(enemy, n, "Defeat %s" % enemy.replace("_", " ").title())


def _bring(it, n):
    return fetch(it, n, "Bring %s" % it.replace("_", " ").title())


QUESTS = (
    favours("lan_yue", "Lan Yue", [
        ("the_herb_thief", "The Herb Thief", _kill("bamboo_monkey", 8), None),
        ("a_cure_for_stoneford", "A Cure for Stoneford", _bring("riverreed_ginseng_10", 5), None),
        ("lan_yues_oath", "Lan Yue's Oath", _kill("drowned_acolyte", 6), None)])
    + favours("tie_niu", "Tie Niu", [
        ("iron_oxs_debt", "Iron Ox's Debt", _bring("copper_ore", 10), None),
        ("the_quarry_fight", "The Quarry Fight", _kill("stone_tortoise", 5), None),
        ("stronger_than_stone", "Stronger Than Stone", _kill("boulder_serpent", 5), None)])
    # Qiu Feng's dawn at the falls gives the Crane Robe (P7b, item_plan §3.4).
    + favours("qiu_feng", "Qiu Feng", [
        ("the_missing_hunter", "The Missing Hunter", _kill("green_viper", 6), None),
        ("crane_falls_at_dawn", "Crane Falls at Dawn", reach("cf_falls_pool", "Visit the Falls Pool at dawn"), "crane_robe"),
        ("one_arrow", "One Arrow", _kill("mist_vulture", 5), None)])
    # Bai Ling's last favour gives the Wisp Banner.
    + favours("bai_ling", "Bai Ling", [
        ("lines_on_the_floor", "Lines on the Floor", _bring("formation_stone", 3), None),
        ("the_broken_array", "The Broken Array", _kill("jade_sentinel", 4), None),
        ("bai_lings_formation", "Bai Ling's Formation", _bring("formation_stone", 6), "wisp_banner")])
)
