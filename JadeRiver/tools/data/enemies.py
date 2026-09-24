"""S13 enemies.json and S32 loot_tables.json (Part 8 monsters and bosses)."""
from common import entries, titled


def atk(id, windup, reach, mult=1.0, depth=26, alt=(0, 70), **extra):
    d = {"id": id, "windup_s": windup, "active_s": extra.pop("active", 0.18), "recover_s": extra.pop("recover", 0.45),
         "hitbox": {"x": [-6, reach], "depth": depth, "alt": list(alt)}, "mult": mult}
    d.update(extra)
    return d


def mob(id, levels, role, element, page, drops, attacks, ai="melee", art=None, width=22, height=40, **extra):
    lv = levels if isinstance(levels, (list, tuple)) else (levels, levels)
    row = {"id": id, "name": extra.pop("name", titled(id)), "level": list(lv), "role": role, "element": element,
           "race": extra.pop("race", "beast"), "energy": extra.pop("energy", "none"),
           "ai": {"profile": ai, "aggro_range": extra.pop("aggro", 200), "flee_below": extra.pop("flee", 0.0),
                  "move_speed": extra.pop("speed", 90), "patrol": extra.pop("patrol", 140)},
           "attacks": attacks, "loot": extra.pop("loot", id), "drops": drops,
           "tameable": extra.pop("tameable", False),
           "collection": {"page": page, "kills_to_fill": 50} if page else None,
           "art": art or {"creature": id}, "half_width": width, "height": height}
    row.update(extra)
    return row


HUMAN = {
    "mudwater_bandit": {"hair": "short_knot", "hair_color": 5, "shirt": "sleeveless", "pants": "martial", "shoes": "boots", "weapon": "dagger", "hat": "tied"},
    "bandit_archer": {"hair": "ponytail", "hair_color": 0, "shirt": "sleeveless", "pants": "cuffed", "shoes": "boots", "weapon": "bow", "hat": "tied"},
    "gorge_bandit_adept": {"hair": "long_tied", "hair_color": 2, "shirt": "vneck", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "none"},
    "drowned_acolyte": {"hair": "short_knot", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "slippers", "weapon": "staff", "hat": "none", "tint": "#9fc6c9"},
    "big_toad_tan": {"hair": "topknot", "hair_color": 5, "shirt": "sleeveless", "pants": "loose", "shoes": "boots", "weapon": "staff", "hat": "none"},
    "drowned_abbot": {"hair": "flowing", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "slippers", "weapon": "staff", "hat": "none", "tint": "#8fb7c2"},
    "elder_gu": {"hair": "long_tied", "hair_color": 1, "shirt": "scholar", "pants": "scholar", "shoes": "folded", "weapon": "none", "hat": "none"},
    "shen_lian": {"hair": "high_pony", "hair_color": 2, "shirt": "vneck", "pants": "martial", "shoes": "boots", "weapon": "none", "hat": "none"},
    "wen_zhao": {"hair": "flowing", "hair_color": 0, "shirt": "cardigan", "pants": "martial", "shoes": "folded", "weapon": "sword", "hat": "none"},
    "trial_disciple": {"hair": "topknot", "hair_color": 0, "shirt": "disciple", "pants": "loose", "shoes": "slippers", "weapon": "none", "hat": "none"},
}


def human(id):
    o = dict(HUMAN[id])
    o["name"] = titled(id)
    o["body"] = "light"
    return {"avatar": o}


def d(item, chance=0.6, count=(1, 1), weight=1):
    return {"item": item, "chance": chance, "count": list(count), "weight": weight}


def build():
    M = [
        mob("mudshell_crab", 1, "normal", "water", "valley_shore", [d("crab_shell", 0.7), d("river_mud", 0.4)],
            [atk("pinch", 0.4, 40)], ai="slow_melee", speed=55, width=20, height=26, aggro=0),
        mob("reedtail_rat", 2, "normal", "none", "valley_shore", [d("rat_tail", 0.6)], [atk("bite", 0.35, 36)],
            ai="melee", speed=120, flee=0.25, width=18, height=22, aggro=150),
        mob("old_snapper", 3, "elite", "water", "valley_shore", [d("snapper_claw", 1.0)],
            [atk("claw_slam", 0.6, 74, 1.4, depth=34, knockback=40)], ai="snapper", speed=45, width=40, height=56,
            phases=[{"below": 0.5, "action": "dig_in", "duration": 3.0, "invulnerable": True}], appears_after={"item": "crab_shell", "count": 5},
            hp_mult=0.42, attack_mult=0.7),
        mob("hollow_minnow", 1, "event", "hollow", None, [], [atk("nibble", 0.45, 30, 0.8)], ai="flyer", speed=80,
            hp_override=5, width=14, height=18, flying=True, hollowing=1),
        mob("hollowed_eel", 10, "event", "hollow", None, [], [atk("lunge", 1.0, 120, 0.5, depth=60, knockback=80)],
            ai="event_eel", invulnerable=True, width=60, height=120, flying=True),
        mob("trial_puppet", 2, "trial", "none", None, [d("entry_token", 1.0)], [atk("counter_palm", 0.5, 44, 1.0)],
            ai="guard_counter", speed=60, width=22, height=60, knockback_immune=True, no_death_penalty=True),
        mob("wild_boarlet", (1, 2), "normal", "earth", "willow_path", [d("boar_hide", 0.5), d("tough_meat", 0.5)],
            [atk("charge", 0.45, 40, 1.0, dash=70)], ai="charger", speed=80, width=22, height=30),
        mob("mossback_toad", (2, 3), "normal", "wood", "willow_path", [d("toad_oil", 0.5), d("moss", 0.5)],
            [atk("tongue_lash", 0.4, 110, 0.9)], ai="ranged_melee", speed=50, tameable=True, width=20, height=26),
        mob("rock_beetle", (4, 5), "normal", "earth", "quarry", [d("beetle_shell", 0.6), d("copper_ore", 0.3)],
            [atk("roll", 0.5, 40, 1.1, dash=90)], ai="charger", speed=60, width=20, height=24),
        mob("pebble_imp", (4, 6), "normal", "earth", "quarry", [d("riverstone", 0.5), d("pebble_core", 0.08)],
            [atk("pebble_throw", 0.4, 300, 0.9, projectile={"speed": 380, "art": "pebble"})], ai="ranged", speed=70, width=16, height=32,
            keep_distance=180),
        mob("stone_tortoise", (5, 7), "normal", "earth", "quarry", [d("tortoise_plate", 0.5), d("jadeiron", 0.15)],
            [atk("slam", 0.6, 80, 1.2, depth=40, both_sides=True, knockback=60)], ai="slow_melee", speed=35, width=36, height=40,
            hp_mult=1.4),
        mob("ironclaw_mole", (5, 7), "normal", "earth", "quarry", [d("mole_claw", 0.5), d("ore_dust", 0.6)],
            [atk("burst_claw", 0.6, 44, 1.2)], ai="burrower", speed=70, tameable=True, width=20, height=26),
        mob("reed_frog", (4, 6), "normal", "wood", "marsh", [d("frog_leg", 0.6), d("willow_moss", 0.3)],
            [atk("jump_kick", 0.35, 40, 1.0, dash=80)], ai="charger", speed=90, width=16, height=22),
        mob("marsh_leech", (5, 7), "normal", "water", "marsh", [d("leech_oil", 0.6)],
            [atk("latch", 0.4, 38, 0.8, dash=50, drain=0.3)], ai="melee", speed=40, width=20, height=16),
        mob("greyfin", (7, 11), "normal", "hollow_water", "marsh", [d("tiny_hollow_shard", 0.4)],
            [atk("leap_bite", 0.5, 44, 1.0, dash=100)], ai="leaper", speed=70, width=18, height=22, hollowing=3),
        mob("hollowed_boarlet", (7, 12), "normal", "hollow_earth", "marsh", [d("hollow_shard", 0.12), d("grey_hide", 0.5)],
            [atk("double_charge", 0.45, 40, 1.0, dash=70, repeat=2)], ai="charger", speed=85, width=22, height=30, hollowing=4),
        mob("bamboo_monkey", (10, 12), "normal", "wood", "bamboo", [d("bamboo_shoot", 0.6)],
            [atk("shoot_toss", 0.4, 280, 0.9, projectile={"speed": 420, "art": "bamboo"})], ai="ranged", speed=120, agile=True,
            tameable=True, width=18, height=34, steals_coins=True, keep_distance=150),
        mob("green_viper", (11, 14), "normal", "wood", "bamboo", [d("viper_fang", 0.5), d("venom_sac", 0.3)],
            [atk("strike", 0.35, 46, 1.0, status={"id": "poison", "chance": 0.35, "power": 0.02, "duration_s": 5})],
            ai="melee", speed=85, width=24, height=18),
        mob("thornback_boar", (13, 15), "elite", "wood", "bamboo", [d("thorn_hide", 1.0), d("ember_pepper", 0.6, (1, 2))],
            [atk("thorn_charge", 0.55, 50, 1.2, dash=110, knockback=60)], ai="charger", speed=80, width=34, height=44, thorns=0.1),
        mob("mudwater_bandit", (14, 19), "normal", "none", "road", [d("cloth", 0.5), d("rat_tail", 0.0)],
            [atk("slash", 0.4, 60, 1.0), atk("qi_strike", 0.55, 90, 1.3, damage_type="qi")], ai="humanoid", art=human("mudwater_bandit"),
            race="human", energy="primal_qi", speed=100, width=18, height=90, coin_mult=2.0, equipment_chance=0.05),
        mob("stone_guardian", (17, 19), "normal", "earth", "road", [d("guardian_stone", 0.25)],
            [atk("fist_slam", 0.6, 70, 1.3, depth=36, knockback=60)], ai="slow_melee", speed=45, width=28, height=60, knockback_immune=True),
        mob("bandit_archer", (16, 20), "normal", "none", "road", [d("arrows", 0.6), d("bow_parts", 0.3)],
            [atk("arrow", 0.6, 420, 1.0, projectile={"speed": 600, "art": "arrow"})], ai="ranged", art=human("bandit_archer"),
            race="human", energy="primal_qi", speed=90, width=18, height=90, keep_distance=260, equipment_chance=0.05),
        mob("mud_hound", (16, 20), "normal", "earth", "road", [d("hound_fang", 0.5)], [atk("bite", 0.35, 44, 1.0)],
            ai="melee", speed=130, pack=True, width=22, height=28),
        mob("jade_carp", (19, 22), "normal", "water", "bend", [d("jade_scale", 0.5), d("jade_carp_fish", 0.15)],
            [atk("tail_slap", 0.5, 50, 1.0, dash=90)], ai="leaper", speed=70, width=22, height=24),
        mob("tide_crab", (20, 23), "normal", "water", "bend", [d("tide_shell", 0.5), d("pearl", 0.15)],
            [atk("pinch", 0.45, 46, 1.1)], ai="guard_counter", speed=50, width=24, height=30, front_guard=0.6),
        mob("drowned_acolyte", (21, 25), "normal", "water", "shrine", [d("prayer_beads", 0.4), d("manual_page", 0.04)],
            [atk("staff_strike", 0.45, 80, 1.0), atk("bell_chant", 0.8, 0, 0.0, buff_allies=0.15)], ai="caster",
            art=human("drowned_acolyte"), race="human", energy="primal_qi", width=18, height=90),
        mob("paper_talisman_ghost", (22, 26), "normal", "soul", "shrine", [d("talisman_paper", 0.5), d("ink", 0.3)],
            [atk("talisman_throw", 0.5, 300, 1.0, damage_type="soul", projectile={"speed": 400, "art": "talisman"})],
            ai="flyer_ranged", speed=70, flying=True, width=20, height=40, weak_to="fire", phases_walls=True),
        mob("rapids_lizard", (28, 31), "normal", "water", "gorge", [d("lizard_scale", 0.5), d("pearl", 0.1)],
            [atk("tail_whip", 0.4, 60, 1.0, both_sides=True)], ai="melee", speed=130, width=26, height=22),
        mob("gorge_bandit_adept", (29, 33), "normal", "none", "gorge", [d("cloth", 0.4), d("manual_page", 0.06), d("manual_ember_burst", 0.03)],
            [atk("sword_arc", 0.45, 80, 1.1), atk("crescent", 0.6, 300, 1.2, damage_type="qi", projectile={"speed": 520, "art": "qi_arc"})],
            ai="humanoid", art=human("gorge_bandit_adept"), race="human", energy="primal_qi", width=18, height=90, guards=True,
            coin_mult=2.0, equipment_chance=0.06),
        mob("boulder_serpent", (32, 35), "normal", "earth", "gorge", [d("serpent_scale", 0.5), d("jadeiron", 0.2)],
            [atk("boulder_roll", 0.6, 50, 1.2, dash=160)], ai="charger", speed=60, width=34, height=34),
        mob("mist_vulture", (34, 36), "normal", "wind", "gorge", [d("vulture_plume", 0.5)],
            [atk("dive", 0.6, 60, 1.2, dash=120)], ai="flyer", speed=100, flying=True, width=26, height=40),
        mob("cloudwing_crane", (37, 40), "normal", "wind", "cliffs", [d("cloud_feather", 0.5)],
            [atk("swoop", 0.5, 60, 1.0, dash=120)], ai="flyer", speed=110, flying=True, width=26, height=50),
        mob("stormwing_hawk", (38, 43), "normal", "thunder", "cliffs", [d("storm_feather", 0.5)],
            [atk("lightning_dive", 0.55, 60, 1.2, dash=140, status={"id": "shock", "chance": 0.3, "power": 0.2, "duration_s": 3})],
            ai="flyer", speed=140, flying=True, width=22, height=34),
        mob("cliff_ape", (41, 45), "normal", "earth", "cliffs", [d("ape_fur", 0.5), d("cloudtop_orchid", 0.05)],
            [atk("smash", 0.5, 60, 1.2), atk("boulder_throw", 0.7, 320, 1.3, projectile={"speed": 360, "art": "boulder"})],
            ai="humanoid", speed=90, width=28, height=56),
        mob("mist_wolf", (46, 50), "normal", "water", "mist_peak", [d("mist_pelt", 0.5)], [atk("lunge", 0.4, 50, 1.0, dash=60)],
            ai="melee", speed=150, pack=True, tameable=True, width=28, height=34, hidden_in_fog=True),
        mob("mirror_wisp", (47, 51), "normal", "soul", "mist_peak", [d("mirror_dust", 0.5)],
            [atk("soul_flash", 0.6, 240, 1.1, damage_type="soul", projectile={"speed": 500, "art": "soul_bolt"})],
            ai="flyer_ranged", speed=70, flying=True, width=18, height=30),
        mob("weeping_lantern", (50, 55), "normal", "soul", "mist_peak", [d("lantern_wick", 0.4), d("soul_wax", 0.4)],
            [atk("flare", 0.7, 90, 1.0, damage_type="soul", depth=50, both_sides=True,
                 status={"id": "confusion", "chance": 0.3, "power": 1, "duration_s": 2})], ai="flyer", speed=50, flying=True, width=18, height=44),
        mob("jade_sentinel", (52, 56), "normal", "earth", "mist_peak", [d("jade_core", 0.08), d("formation_stone", 0.5)],
            [atk("halberd_sweep", 0.6, 90, 1.2, depth=36)], ai="slow_melee", speed=50, width=26, height=64, linked=True),
        mob("hollow_stag", (55, 59), "normal", "hollow_wood", "summit", [d("hollow_antler", 0.4), d("hollow_shard", 0.2)],
            [atk("antler_charge", 0.5, 60, 1.2, dash=140)], ai="charger", speed=120, width=30, height=56, hollowing=5, cleansable=True),
        mob("cloudpeak_roc", (58, 63), "normal", "wind", "summit", [d("roc_feather", 0.5), d("mystic_ore", 0.1)],
            [atk("wing_gust", 0.7, 160, 1.0, depth=60, knockback=120)], ai="flyer", speed=110, flying=True, width=40, height=50),
        # Bosses
        mob("big_toad_tan", 18, "dungeon_boss", "none", None, [d("mudwater_manual", 1.0)],
            [atk("club_swing", 0.55, 90, 1.2, depth=34, knockback=60), atk("call_bandits", 1.0, 0, 0.0, summon="mudwater_bandit")],
            ai="boss_tan", art=human("big_toad_tan"), race="human", energy="primal_qi", width=24, height=96,
            phases=[{"below": 0.5, "action": "drink_wine", "heal": 0.1, "breakable": "wine_jar"}], unique_drop="mudwater_cleaver"),
        mob("riverbed_serpent", 25, "field_boss", "water", "bend", [d("serpent_core", 1.0), d("serpent_scale", 1.0, (2, 4))],
            [atk("bite", 0.6, 110, 1.3, depth=40), atk("tail_flood", 1.0, 260, 1.0, depth=80, both_sides=True)], ai="boss_serpent",
            width=70, height=150, respawn_min=45, flying=True),
        mob("drowned_abbot", 27, "dungeon_boss", "water", None, [d("riverbreath_scroll", 1.0), d("drowned_robe", 1.0)],
            [atk("bell_shockwave", 0.7, 180, 1.2, depth=70, both_sides=True, knockback=80),
             atk("summon_ghosts", 1.2, 0, 0.0, summon="paper_talisman_ghost")], ai="boss_abbot", art=human("drowned_abbot"),
            race="human", energy="primal_qi", width=22, height=96, weak_to="fire",
            phases=[{"below": 0.66, "action": "flood"}, {"below": 0.33, "action": "summon"}]),
        mob("the_reflection", 36, "story_boss", "none", None, [], [atk("mirror_strike", 0.45, 70, 1.0)], ai="reflection",
            art={"avatar": "player"}, race="human", energy="primal_qi", width=18, height=90),
        mob("elder_gu", 53, "story_boss", "water", None, [d("smuggler_ledger", 1.0)], [atk("tide_palm", 0.5, 90, 1.2, damage_type="qi")],
            ai="humanoid", art=human("elder_gu"), race="human", energy="true_qi", width=18, height=90, flees_after_s=60, invulnerable=True),
        mob("hollow_behemoth", 58, "story_boss", "hollow_earth", None, [d("siege_medal", 1.0), d("mistjade_robe", 1.0)],
            [atk("stampede", 0.7, 90, 1.4, dash=240, knockback=120), atk("drone_burst", 1.0, 200, 1.0, both_sides=True, depth=70)],
            ai="boss_behemoth", width=80, height=140, hollowing=8),
        mob("gate_guardian", 63, "story_boss", "earth", None, [], [atk("ring_sweep", 0.7, 180, 1.3, both_sides=True, depth=70, knockback=100),
                                                                   atk("soul_gaze", 0.9, 320, 1.1, damage_type="soul", projectile={"speed": 500, "art": "soul_bolt"})],
            ai="boss_guardian", width=60, height=180, phases=[{"below": 0.66, "action": "soul_phase"}, {"below": 0.33, "action": "flight_phase"}]),
        mob("shen_lian", 4, "trial", "none", None, [], [atk("fish_gutting_fist", 0.4, 46, 1.0)], ai="duelist", art=human("shen_lian"),
            race="human", width=18, height=90, spar=True),
        mob("wen_zhao", 44, "trial", "wind", None, [], [atk("cloud_cut", 0.4, 80, 1.1), atk("crescent", 0.6, 300, 1.2, damage_type="qi",
                                                                                                  projectile={"speed": 540, "art": "qi_arc"})],
            ai="duelist", art=human("wen_zhao"), race="human", width=18, height=90, spar=True),
        mob("sparring_disciple", 10, "trial", "none", None, [], [atk("palm", 0.45, 46, 1.0)], ai="duelist", art=human("trial_disciple"),
            race="human", width=18, height=90, spar=True),
    ]
    # Starter spirit animals exist as enemy templates (non-hostile wild versions from Qi Unfurling 7).
    for pid, el in [("reed_otter", "water"), ("ember_fox", "fire"), ("jade_crane_chick", "wind")]:
        M.append(mob(pid, (19, 24), "normal", el, None, [], [atk("nip", 0.4, 36, 0.8)], ai="wild_pet", tameable=True, width=18, height=28,
                     passive=True))
    entries("enemies.json", M)

    tables = []
    for m in M:
        role = m["role"]
        drops = m.get("drops", [])
        table = {"id": m["loot"], "groups": [], "coins": {}, "equipment": {}, "rare": []}
        if role == "normal":
            table["groups"] = [{"chance": 0.6, "pick": [dict(x, weight=x.get("weight", 1)) for x in drops if x["chance"] > 0.2]}]
            table["rare"] = [x for x in drops if x["chance"] <= 0.2 and x["chance"] > 0]
            table["coins"] = {"chance": 0.2 * m.get("coin_mult", 1.0), "mult": 1}
            table["equipment"] = {"chance": m.get("equipment_chance", 0.03), "min_quality": "flawed"}
        elif role == "elite":
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 6}
            table["equipment"] = {"chance": 0.25, "min_quality": "fine"}
            table["rare"] = [{"item": "manual_page", "chance": 0.05, "count": [1, 1]}]
        elif role in ("dungeon_boss", "field_boss", "story_boss"):
            table["guaranteed"] = [dict(x) for x in drops]
            table["coins"] = {"chance": 1.0, "mult": 40}
            table["equipment"] = {"chance": 1.0, "min_quality": "superior"} if role != "story_boss" else {}
        else:
            table["guaranteed"] = [dict(x) for x in drops if x["chance"] >= 1.0]
        tables.append(table)
    tables.append({"id": "jar_valley_low", "groups": [{"chance": 0.5, "pick": [{"item": "rice", "weight": 2, "count": [1, 1]},
                   {"item": "willow_moss", "weight": 2, "count": [1, 2]}, {"item": "herbal_tea", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.5, "mult": 1}, "rare": [], "equipment": {}})
    tables.append({"id": "jar_valley_mid", "groups": [{"chance": 0.6, "pick": [{"item": "rice_ball", "weight": 2, "count": [1, 1]},
                   {"item": "spirit_stone_shard", "weight": 1, "count": [1, 1]}, {"item": "healing_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 0.6, "mult": 2}, "rare": [], "equipment": {}})
    tables.append({"id": "chest_valley", "guaranteed": [{"item": "spirit_stone_shard", "count": [1, 3], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "healing_pill", "weight": 2, "count": [1, 2]}, {"item": "manual_page", "weight": 1, "count": [1, 1]},
                                                         {"item": "qi_gathering_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 5}, "rare": [], "equipment": {"chance": 0.3, "min_quality": "fine"}})
    tables.append({"id": "chest_dungeon", "guaranteed": [{"item": "spirit_stone_shard", "count": [2, 4], "chance": 1.0}],
                   "groups": [{"chance": 1.0, "pick": [{"item": "manual_page", "weight": 1, "count": [1, 2]}, {"item": "foundation_guard_pill", "weight": 1, "count": [1, 1]}]}],
                   "coins": {"chance": 1.0, "mult": 10}, "rare": [], "equipment": {"chance": 0.6, "min_quality": "fine"}})
    entries("loot_tables.json", tables)
    return M


if __name__ == "__main__":
    build()
