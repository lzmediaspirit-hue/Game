"""Story data (S02, S19, S27, Part 4 unlock timeline, Part 8 quests):
npcs.json, unlocks.json, quests.json, dialogue/*.json, mail_templates.json, codex.json.

Names and places are original to Jade River; the source novel only informs the shape of
the world (a river valley, sects, a slow climb through realms).
"""
import json
import os

from common import DATA, write, entries

# ---------------------------------------------------------------------------------------------
# Requirement helpers
def realm(r):
    return {"kind": "realm_at_least", "realm": r}


def qdone(q):
    return {"kind": "quest_done", "quest": q}


def qactive(q):
    return {"kind": "quest_active", "quest": q}


def flag(f):
    return {"kind": "flag_set", "flag": f}


def noflag(f):
    return {"kind": "flag_not_set", "flag": f}


def unlocked(s):
    return {"kind": "unlock", "system": s}


def sect(s):
    return {"kind": "training_sect", "sect": s}


def all_of(*c):
    return {"all": list(c)}


def any_of(*c):
    return {"any": list(c)}


# ---------------------------------------------------------------------------------------------
# NPCs. Outfits use the player's layered avatar engine (parts.json) plus garment dyes.
def outfit(hair="short_knot", color=0, shirt="disciple", pants="loose", shoes="slippers", hat="none", cape="none",
           weapon="none", body="light", **dyes):
    o = {"body": body, "hair": hair, "hair_color": color, "shirt": shirt, "pants": pants, "shoes": shoes, "hat": hat,
         "cape": cape, "weapon": weapon}
    o.update(dyes)
    return o


MENTORS = ["elder_hu", "elder_sung"]
STEWARDS = ["jade_steward", "cloud_steward"]
WEAPON_MASTERS = ["jade_weapon_master", "cloud_weapon_master"]
HALL_MASTERS = ["jade_hall_master", "cloud_hall_master"]
DEACONS = ["jade_deacon", "cloud_deacon"]
LIBRARIANS = ["jade_librarian", "cloud_librarian"]
SMITHS = ["jade_smith", "cloud_smith"]
FORMATION_ELDERS = ["jade_formation_elder", "cloud_formation_elder"]
PHYSICIANS = ["jade_physician", "cloud_physician"]


def npcs():
    N = []

    def npc(nid, name, title, o, lines, barks=(), services=(), **kw):
        d = {"id": nid, "name": name, "title": title, "outfit": o, "lines": list(lines), "barks": list(barks), "services": list(services)}
        d.update(kw)
        N.append(d)

    # Lotus Ferry — the seven villagers and two neighbours
    npc("aunt_ping", "Aunt Ping", "Your aunt", outfit("long_tied", 1, "cardigan", "straight", "folded", shirt_dye="rose", pants_dye="earth"),
        ["Eat something before you run off.", "Your mother had the same stubborn chin.", "The river gives, the river takes. Mostly it gives fish."],
        ["Mind the steps!", "Who left the net out again?"], tree="aunt_ping")
    npc("lu_boatman", "Lu", "Ferryman", outfit("topknot", 1, "scholar", "scholar", "folded", hat="straw", shirt_dye="grey", pants_dye="ink"),
        ["The river has been restless.", "Breathe in when the water rises. Out when it falls.", "Every current started as a trickle."],
        ["Hm.", "Tide's turning."], tree="lu")
    npc("little_dou", "Little Dou", "Neighbour's boy", outfit("short_knot", 0, "sleeveless", "cuffed", "slippers", shirt_dye="ochre"),
        ["When I grow up I'll punch a crab so hard it flies to Stoneford!", "Did you see my kite? It's the best kite."],
        ["Kite! Kiiite!", "Hi-yah!"], scale=0.8, tree="little_dou")
    npc("old_ma", "Old Ma", "Shopkeeper", outfit("short_knot", 5, "vneck", "loose", "slippers", shirt_dye="earth"),
        ["Silver or barter, I'm not fussy.", "Rice balls! Fresh this morning. Well. This week."],
        ["Fresh rice balls!", "Everything must go. Eventually."], services=["shop:old_ma"], tree="old_ma")
    npc("granny_liu", "Granny Liu", "Herbalist", outfit("long_tied", 1, "cardigan", "scholar", "folded", shirt_dye="jade", pants_dye="grey"),
        ["Bitter tea, sweet health.", "A herb picked at dawn is worth two at noon."],
        ["Where did I put my pestle?", "Hmph. Young people."], services=["shop:granny_liu"], tree="granny_liu")
    npc("shen_lian_npc", "Shen Lian", "Fisher's son", outfit("high_pony", 0, "sleeveless", "martial", "boots", shirt_dye="indigo"),
        ["Race you to the tower. Loser guts the fish.", "One day I'll join a sect. A real one."],
        ["Faster!", "Bet you can't catch me."], tree="shen_lian")
    npc("uncle_guo", "Uncle Guo", "Retired brawler", outfit("topknot", 5, "sleeveless", "martial", "boots", shirt_dye="crimson"),
        ["Fists first. Everything else is decoration.", "I kindled Qi once. For a day. Long story."],
        ["Hah! Hup!", "Keep your elbow in."], tree="uncle_guo")
    npc("fisher_wen", "Fisher Wen", "Fisherman", outfit("short_knot", 5, "vneck", "cuffed", "folded", hat="straw", shirt_dye="indigo"),
        ["The carp aren't biting. Something scared them.", "Grey water near the reeds last week. Never seen that."], ["Nothing. Again."])
    npc("washer_mei", "Washer Mei", "Villager", outfit("ponytail", 2, "cardigan", "straight", "slippers", shirt_dye="white"),
        ["Aunt Ping says you're finally awake before noon.", "The river's cold as winter this morning."], ["Scrub, scrub."])

    # Stoneford (about 20 people)
    npc("guard_hou", "Captain Hou", "Gate guard", outfit("topknot", 0, "disciple", "martial", "boots", weapon="spear", shirt_dye="earth"),
        ["Stoneford gate. Keep your blades sheathed.", "Recruitment Fair's on the Fairground. West, past Artisan Row."], ["Next!", "Move along."])
    npc("foreman_dong", "Foreman Dong", "Quarry foreman", outfit("short_knot", 5, "sleeveless", "loose", "boots", shirt_dye="earth"),
        ["Stonewall Quarry needs strong backs.", "Rock beetles again. Curl up, roll, bite. Watch the curl."], ["Put your back into it!"])
    npc("adventurer_kai", "Kai", "Wandering swordsman", outfit("flowing", 0, "vneck", "straight", "boots", weapon="sword", cape="tattered", shirt_dye="ink"),
        ["The Caravan Road's gone bad. Bandits call themselves the Mudwater.", "I came for the tournament. I stayed for the tea."], ["Anyone up for a spar?"])
    npc("storekeeper_fang", "Proprietor Fang", "General store", outfit("short_knot", 0, "scholar", "scholar", "folded", shirt_dye="ochre"),
        ["Teas, rice, charms. If Stoneford needs it, Fang sells it.", "Return charms! Never walk home again!"], ["Bargains!"], services=["shop:stoneford_general"])
    npc("auntie_rong", "Auntie Rong", "Tea house", outfit("long_tied", 3, "cardigan", "straight", "slippers", shirt_dye="rose"),
        ["Lotus root tea calms the belly and the Qi.", "Sit. Everyone who sits in my tea house leaves stronger."], ["Tea! Hot tea!"], services=["shop:stoneford_tea"])
    npc("keeper_shi", "Keeper Shi", "Stone keeper", outfit("topknot", 1, "scholar", "scholar", "folded", shirt_dye="jade"),
        ["Teleport stones remember those who touch them.", "A shard of Spirit Stone pays the ferryman of the stones."], ["The stones hum today."])
    npc("courier_lin", "Courier Lin", "Courier", outfit("ponytail", 0, "vneck", "cuffed", "boots", shirt_dye="indigo"),
        ["Letters to every sect, parcels to every village.", "The mail finds you. Somehow. Always."], ["Coming through!"])
    npc("adventurer_su", "Su Qing", "Herb hunter", outfit("high_pony", 4, "cardigan", "cuffed", "boots", shirt_dye="jade"),
        ["The bamboo grove east of the marsh has ember peppers. And vipers.", "Never eat a mushroom that smiles at you."], ["Hm, willow moss..."])
    npc("old_pan", "Old Pan", "Wandering merchant", outfit("topknot", 1, "vneck", "loose", "folded", hat="straw", cape="tattered", shirt_dye="ochre"),
        ["Rare wares for rare coin. Spirit Stones only.", "I'm here today. Tomorrow? Who knows."], ["Rare wares!"], services=["shop:old_pan"])
    npc("smith_bao", "Smith Bao", "Blacksmith", outfit("short_knot", 0, "sleeveless", "martial", "boots", shirt_dye="ink"),
        ["Iron remembers every hammer blow.", "Bring me Jadeiron and I'll make you something that sings."], ["*clang*"], services=["shop:stoneford_smith"])
    npc("tinkerer_yu", "Tinkerer Yu", "Tinkerer", outfit("ponytail", 3, "scholar", "cuffed", "folded", shirt_dye="grey"),
        ["Tools are just patience you can hold.", "A better pickaxe means more ore and fewer blisters."], ["Where's my small spanner?"], services=["shop:tinkerer", "page:workshop"],
        service_labels={"page:workshop": "Puppet bench"}, service_unlocks={"page:workshop": "puppetry"})
    npc("elder_gu", "Elder Gu", "Trade house master", outfit("long_tied", 1, "scholar", "scholar", "folded", cape="solid", shirt_dye="crimson"),
        ["Everything has a price. Most things have two.", "Bring me curiosities and I'll tell you what they're worth."], ["Hmm, interesting."], services=["shop:gu_trade_house", "page:workshop"],
        service_labels={"page:workshop": "Appraise"}, service_unlocks={"page:workshop": "appraisal"})
    npc("madam_hua", "Madam Hua", "Trade house master", outfit("flowing", 2, "cardigan", "straight", "slippers", cape="solid", shirt_dye="jade"),
        ["The trade house deals fairly now. I promise you that.", "Gu's ledgers made interesting reading."], ["Fair prices!"], services=["shop:gu_trade_house"])
    npc("mei_qing", "Mei Qing", "Alchemist", outfit("flowing", 3, "cardigan", "scholar", "slippers", shirt_dye="indigo"),
        ["A pill is a promise. Keep it simple and it keeps you alive.", "Willow moss, riverreed ginseng, and patience."], ["Too hot... too hot!"], services=["shop:mei_qing", "shop:mei_qing_recipes"])
    npc("mei_qing_sect", "Mei Qing", "Visiting alchemist", outfit("flowing", 3, "cardigan", "scholar", "slippers", shirt_dye="indigo"),
        ["I teach at both sects. The furnace doesn't care about robes."], ["Mind the fumes."])
    npc("apprentice_tao", "Apprentice Tao", "Smith's apprentice", outfit("short_knot", 0, "sleeveless", "cuffed", "slippers", shirt_dye="earth"),
        ["Master Bao says I'll hold a hammer next year.", "Did you know iron can taste angry?"], ["Hot, hot!"], scale=0.9)
    npc("recruiter_qing_lan", "Qing Lan", "Jade Sect recruiter", outfit("high_pony", 0, "disciple", "martial", "boots", weapon="sword", shirt_dye="jade", pants_dye="jade"),
        ["The Jade Sect teaches the water's patience and the sword's clarity.", "Our academy sits by the river. You'll feel at home."], ["Join the Jade Sect!"], tree="recruiter_jade",
        on_talk=[{"kind": "set_flag", "flag": "met_recruiter_jade"}])
    npc("recruiter_mo_yun", "Mo Yun", "Cloud Sect recruiter", outfit("topknot", 0, "disciple", "martial", "boots", weapon="staff", shirt_dye="cloud", pants_dye="cloud"),
        ["The Cloud Sect climbs. Our monastery touches the clouds.", "Wind cannot be held. Neither can a Cloud disciple."], ["The Cloud Sect awaits!"], tree="recruiter_cloud",
        on_talk=[{"kind": "set_flag", "flag": "met_recruiter_cloud"}])
    npc("shen_lian", "Shen Lian", "Cloud Sect disciple", outfit("high_pony", 0, "disciple", "martial", "boots", shirt_dye="cloud", pants_dye="cloud"),
        ["We picked different sects. Doesn't mean I'll go easy on you.", "Spar me at the practice yard. I'm faster now."], ["Still slow?"], services=["spar:shen_lian"],
        service_labels={"spar:shen_lian": "Spar"})
    npc("wen_zhao", "Wen Zhao", "Rival", outfit("flowing", 0, "disciple", "martial", "boots", weapon="sword", cape="solid", shirt_dye="ink", pants_dye="ink"),
        ["The tournament finals. You and me. Don't disappoint.", "Talent is a door. You still have to walk through it."], ["Hmph."],
        services=["spar:wen_zhao"], service_labels={"spar:wen_zhao": "Spar"})
    npc("fair_vendor_he", "Vendor He", "Fair vendor", outfit("short_knot", 5, "vneck", "loose", "slippers", shirt_dye="rose"),
        ["Candied hawthorn! Sect badges! Lucky charms!", "Buy a lucky charm. Can't hurt."], ["Hawthorn! Sweet hawthorn!"])
    npc("adventurer_rui", "Rui", "Retired disciple", outfit("topknot", 5, "scholar", "straight", "folded", shirt_dye="grey"),
        ["I washed out at Heart Tempering. The Heart Trial shows you things.", "Pick the sect whose method suits your breath, not your pride."], ["Ah, youth."])
    npc("hamlet_elder_gao", "Elder Gao", "Greyreed Hamlet", outfit("long_tied", 1, "vneck", "loose", "folded", shirt_dye="grey"),
        ["The grey came up from the pools. It took the colour, then the people.", "If the well runs clean again, we might come home."], ["..."])
    npc("hamlet_trader_min", "Trader Min", "Greyreed trade post", outfit("ponytail", 0, "vneck", "cuffed", "boots", shirt_dye="jade"),
        ["Greyreed trades again! Thanks to you."], ["Market day!"], services=["shop:greyreed"])
    npc("hermit_yao", "Hermit Yao", "Marsh hermit", outfit("flowing", 1, "scholar", "loose", "folded", hat="straw", cape="tattered", shirt_dye="earth"),
        ["The otters trust me. Maybe one day they'll trust you.", "Spirit beasts are not tools. They are friends who bite."], ["Shh. Listen to the reeds."], services=["shop:hermit"], tree="hermit_yao")

    # Sects: mirrored roles (Jade / Cloud)
    first_sect_npc = len(N)
    for s, sname, dye, weapon in [("jade", "Jade", "jade", "sword"), ("cloud", "Cloud", "cloud", "staff")]:
        npc(s + "_steward", {"jade": "Steward Wei", "cloud": "Steward Ruo"}[s], sname + " Sect steward",
            outfit("topknot", 5, "scholar", "scholar", "folded", shirt_dye=dye, pants_dye="grey"),
            ["Service disciples sweep, carry and learn. In that order.", "Your bunk is in the dorm. Keep it tidy."], ["Brooms don't sweep themselves."])
        npc(s + "_weapon_master", {"jade": "Master Kong", "cloud": "Master Fei"}[s], "Weapon master",
            outfit("short_knot", 0, "sleeveless", "martial", "boots", weapon=weapon, shirt_dye=dye),
            ["Try each weapon. Your hands will choose before your head does.", "A weapon is only your arm, longer."], ["Again!"])
        npc(s + "_deacon", {"jade": "Deacon Rui", "cloud": "Deacon Heng"}[s], "Mission deacon",
            outfit("topknot", 0, "disciple", "scholar", "folded", shirt_dye=dye, pants_dye=dye),
            ["Missions earn contribution. Contribution earns everything else.", "Five missions a day. The board refreshes at dawn."], ["Missions posted!"],
            services=["missions", "shop:" + s + "_sect"])
        npc(s + "_hall_master", {"jade": "Master Lin", "cloud": "Master Qiao"}[s], "Training hall master",
            outfit("high_pony", 0, "disciple", "martial", "boots", shirt_dye=dye, pants_dye="ink"),
            ["A technique is a question your meridians learn to answer.", "Practice twenty times. Then twenty more."], ["Form! Form!"])
        npc(s + "_librarian", {"jade": "Librarian Zhu", "cloud": "Librarian Pei"}[s], "Librarian",
            outfit("long_tied", 1, "scholar", "scholar", "folded", shirt_dye="grey", pants_dye=dye),
            ["Methods by rank. Manuals by contribution. Silence by law.", "Torn pages can be restored. Torn students less so."], ["Shh."],
            services=["page:library", "page:workshop"], service_labels={"page:library": "Browse", "page:workshop": "Restore manuals"},
            service_unlocks={"page:workshop": "research"})
        npc(s + "_smith", {"jade": "Smith Ouyang", "cloud": "Smith Tan"}[s], "Sect smith",
            outfit("short_knot", 5, "sleeveless", "martial", "boots", shirt_dye="ink"),
            ["The sect forge answers to disciples with Qi in their hands.", "Common first. Earth when you've earned it."], ["*clang*"])
        npc(s + "_formation_elder", {"jade": "Elder Bian", "cloud": "Elder Lou"}[s], "Formation elder",
            outfit("flowing", 1, "scholar", "scholar", "folded", cape="solid", shirt_dye=dye),
            ["Lines on the floor, fuel in the nodes, intent in the centre.", "A good formation outlives its maker."], ["Mind the lines."],
            services=["page:workshop", "page:arrays"], service_labels={"page:workshop": "Formations", "page:arrays": "Etch plates"},
            service_unlocks={"page:workshop": "formations", "page:arrays": "array_plates"})
        npc(s + "_physician", {"jade": "Physician Nan", "cloud": "Physician Qu"}[s], "Sect physician",
            outfit("ponytail", 3, "cardigan", "scholar", "slippers", shirt_dye="white"),
            ["Injured disciples, bitter medicine.", "A needle in the right place is worth a hundred pills."], ["Next patient."],
            services=["page:workshop"], service_labels={"page:workshop": "Infirmary"}, service_unlocks={"page:workshop": "healing"})
        npc(s + "_gardener" if s == "jade" else "cloud_gardener", "Gardener Ji" if s == "jade" else "Gardener Ren", "Sect gardener",
            outfit("short_knot", 5, "vneck", "cuffed", "slippers", hat="straw", shirt_dye="earth"),
            ["Plant, water, wait. Harvest.", "Willow moss likes shade and gossip."], ["Grow, little ones."])
        npc(s + "_disciple_a", {"jade": "Disciple Hao", "cloud": "Disciple Ling"}[s], "Outer disciple",
            outfit("ponytail", 0, "disciple", "martial", "boots", shirt_dye=dye, pants_dye=dye),
            ["The Heart Trial? Don't talk about the Heart Trial.", "I heard the elders fought a Hollow thing last winter."], ["Morning, junior."])
    for d in N[first_sect_npc:]:
        d["sect"] = "jade_sect" if d["id"].startswith("jade_") else "cloud_sect"
    npc("jade_disciple_b", "Disciple Yue", "Inner disciple", outfit("flowing", 4, "disciple", "martial", "boots", weapon="sword", shirt_dye="jade", pants_dye="jade"),
        ["Inner disciples get the good retreat rooms.", "Qi Unfurling feels like breathing with your whole skin."], ["Focus."])
    npc("elder_hu", "Elder Hu", "Jade Sect elder", outfit("long_tied", 1, "scholar", "scholar", "folded", cape="solid", shirt_dye="jade", pants_dye="ink"),
        ["The river does not hurry, yet it carves the valley.", "Come to me when you hit a wall. Walls are my speciality."], ["Hmm."], tree="mentor", sect="jade_sect")
    npc("elder_sung", "Elder Sung", "Cloud Sect elder", outfit("topknot", 1, "scholar", "scholar", "folded", cape="solid", shirt_dye="cloud", pants_dye="ink"),
        ["The wind does not fight the mountain. It goes over.", "Bring me your walls. I'll show you the sky above them."], ["Hm-hm."], tree="mentor", sect="cloud_sect")
    npc("arena_master", "Arena Master Quan", "Arena", outfit("short_knot", 0, "sleeveless", "martial", "boots", cape="solid", shirt_dye="crimson"),
        ["Three wins for the qualifier. No excuses.", "The Valley Tournament crowns one champion a year."], ["Next bout!"], services=["spar:sparring_disciple"],
        service_labels={"spar:sparring_disciple": "Arena match"})

    # Companions (S26)
    npc("lan_yue", "Lan Yue", "Healer", outfit("flowing", 4, "cardigan", "scholar", "slippers", weapon="staff", shirt_dye="indigo"),
        ["Stay close. I can't heal what I can't reach."], ["Careful!"], companion="lan_yue")
    npc("tie_niu", "Tie Niu", "Brawler", outfit("short_knot", 0, "sleeveless", "martial", "boots", shirt_dye="earth"),
        ["Hit me. No, harder. See? Iron Ox."], ["HAH!"], companion="tie_niu")
    npc("qiu_feng", "Qiu Feng", "Archer", outfit("high_pony", 0, "vneck", "cuffed", "boots", weapon="bow", shirt_dye="jade"),
        ["I mark them. You hit them. Simple."], ["Mark!"], companion="qiu_feng")
    npc("bai_ling", "Bai Ling", "Formation student", outfit("ponytail", 2, "disciple", "straight", "slippers", weapon="sword", shirt_dye="cloud"),
        ["Three nodes and a centre. Watch."], ["Lines drawn!"], companion="bai_ling")
    entries("npcs", N)
    return {n["id"] for n in N}


# ---------------------------------------------------------------------------------------------
# Unlocks (Part 4 timeline). Gate = trigger + quest.
def unlocks():
    U = []

    def u(uid, label, trigger=None, quest="", reveals=(), effects=(), scope="character", prologue=False, **kw):
        d = {"id": uid, "label": label, "trigger": trigger or {}, "reveals": list(reveals), "effects": list(effects), "scope": scope}
        if quest:
            d["quest"] = quest
        if prologue:
            d["prologue"] = True
            d["same_stage_ok"] = True
        d.update(kw)
        U.append(d)

    # Prologue (S27 HUD reveal order)
    u("move", "Move", reveals=["hud:joystick", "hud:context"], prologue=True, toast=False)
    u("talk", "Talk", prologue=True, toast=False)
    u("bag", "Bag", {}, "morning_tide", ["hud:bag"], prologue=True)
    u("navigation", "Map and Tracker", all_of(qdone("morning_tide")), "a_quiet_river", ["hud:room_banner", "hud:minimap", "hud:quest_tracker"], prologue=True)
    u("jump", "Jump", all_of(qdone("a_quiet_river")), "the_runaway_kite", ["hud:jump"], prologue=True)
    u("shop", "Coins and Shops", all_of(qdone("a_quiet_river")), "mas_delivery", ["hud:currency"], prologue=True)
    u("quick_use", "Quick-use and Health", all_of(qdone("a_quiet_river")), "grannys_remedy", ["hud:quick_use", "hud:hp_bar", "hud:player_panel"], prologue=True)
    u("shrines", "Shrines", all_of(qdone("a_quiet_river")), "grannys_remedy", [], prologue=True, toast=False)
    u("sprint", "Sprint", all_of(qdone("a_quiet_river")), "race_to_the_tower", [], prologue=True)
    u("attack", "Attack", all_of(qdone("a_quiet_river")), "fists_first", ["hud:attack", "hud:damage_numbers"], prologue=True)
    u("loot", "Loot and Log", all_of(qdone("a_quiet_river_return")), "crab_trouble", ["hud:system_log", "hud:enemy_hp_bars", "hud:elite_marker"], prologue=True)
    u("equipment", "Equipment", all_of(qdone("crab_trouble")), "", ["page:equipment"], prologue=True)
    u("menu", "Menu", all_of(qdone("crab_trouble")), "evening_on_the_river", ["hud:menu"], prologue=True)
    u("cultivate", "Cultivate", all_of(flag("night_survived")), "the_river_token", ["hud:cultivate", "hud:progress_bar", "hud:realm_badge"], prologue=True)
    u("cultivation", "Cultivation page", all_of(flag("night_survived")), "the_river_token", ["page:cultivation"], prologue=True, toast=False)
    u("breakthrough", "Breakthrough", all_of(flag("night_survived")), "the_river_token", [], prologue=True, toast=False)
    u("codex", "Codex", all_of(flag("night_survived")), "the_river_token", ["page:codex"], prologue=True, toast=False)

    # Bone Forging
    bf1 = all_of(realm("bone_forging_1"))
    u("body_training", "Body training", bf1, "the_willow_path", [])
    u("kill_progress", "Progress from fights", bf1, "the_willow_path", [], same_stage_ok=True, toast=False)
    u("shrine_respawn", "Shrines remember you", bf1, "the_willow_path", [], same_stage_ok=True, toast=False)
    u("world_menu", "World map", bf1, "the_willow_path", ["hud:map", "page:world_map"], same_stage_ok=True)
    u("foundation", "Foundation", bf1, "the_willow_path", ["page:foundation"], same_stage_ok=True, toast=False)
    u("mail", "Mail", bf1, "the_willow_path", ["hud:mail"], same_stage_ok=True)
    bf2 = all_of(qdone("the_willow_path"))
    u("sect_choice", "Sects", bf2, "the_recruitment_fair", ["page:training_sect"])
    u("town_hub", "Town services", bf2, "the_recruitment_fair", ["page:shop"], same_stage_ok=True, toast=False)
    u("notice_board", "Notice board", all_of(realm("bone_forging_2"), qdone("the_recruitment_fair")), "entry_trial", [], same_stage_ok=True)
    u("return_charm", "Return charm", all_of(realm("bone_forging_2"), qdone("the_recruitment_fair")), "entry_trial", [], same_stage_ok=True, toast=False)
    u("character_menu", "Character", all_of(realm("bone_forging_2"), qdone("the_recruitment_fair")), "entry_trial", ["page:character"], same_stage_ok=True)
    u("sect_hub", "Sect hub and dorm", all_of(qdone("entry_trial")), "a_disciples_chores", [], same_stage_ok=True)
    u("guard", "Guard", all_of(realm("bone_forging_3"), qdone("entry_trial")), "the_weapon_hall", ["hud:guard", "page:equipment"])
    u("weapons", "Weapons", all_of(realm("bone_forging_3"), qdone("entry_trial")), "the_weapon_hall", [], same_stage_ok=True)
    u("weapon_dao", "Weapon Dao", all_of(realm("bone_forging_3"), qdone("entry_trial")), "the_weapon_hall", [], same_stage_ok=True, toast=False)
    u("herb_gathering", "Herb gathering", all_of(realm("bone_forging_4"), qdone("entry_trial")), "eyes_for_qi", ["page:crafts"],
      effects=[{"kind": "grant_item", "item": "herb_sickle", "count": 1}])
    u("ambient_qi", "Ambient Qi", all_of(realm("bone_forging_4"), qdone("entry_trial")), "eyes_for_qi", [], same_stage_ok=True, toast=False)
    u("outer_rank", "Outer disciple", all_of(realm("bone_forging_4"), qdone("entry_trial")), "outer_trial", [], same_stage_ok=True)
    u("mining", "Mining", all_of(realm("bone_forging_5")), "stone_and_sweat", [], effects=[{"kind": "grant_item", "item": "old_pickaxe", "count": 1}])
    u("dodge_dash", "Dodge dash", all_of(realm("bone_forging_5")), "stone_and_sweat", [], same_stage_ok=True)
    u("collection_book", "Collection book", all_of(realm("bone_forging_5")), "stone_and_sweat", ["page:collection"], same_stage_ok=True, toast=False)
    u("idle_tasks", "Idle tasks", all_of({"kind": "account_realm", "realm": "bone_forging_5"}), "a_second_path", ["page:characters"], scope="account")
    u("daily_missions", "Sect missions", all_of(realm("bone_forging_6"), qdone("entry_trial")), "earning_your_keep", [])
    u("contribution_shop", "Contribution shop", all_of(realm("bone_forging_6"), qdone("entry_trial")), "earning_your_keep", [], same_stage_ok=True, toast=False)
    u("field_boss_timers", "Field-boss timers", all_of(realm("bone_forging_6")), "earning_your_keep", [], same_stage_ok=True, toast=False)
    bf7 = all_of(realm("bone_forging_7"))
    u("qi_pool", "Qi", bf7, "the_first_current", ["hud:qi_bar"])
    u("seclusion", "Offline seclusion", bf7, "the_first_current", ["page:seclusion"], same_stage_ok=True)
    u("qi_springs", "Qi springs", bf7, "the_first_current", [], same_stage_ok=True, toast=False)
    u("element_affinity", "Element affinity", bf7, "the_first_current", [], same_stage_ok=True, toast=False)
    u("cooking", "Cooking", all_of(realm("bone_forging_8")), "aunt_pings_broth", [],
      effects=[{"kind": "grant_item", "item": "clay_pot", "count": 1}, {"kind": "grant_item", "item": "bamboo_rod", "count": 1}])
    u("fishing", "Fishing", all_of(realm("bone_forging_8")), "aunt_pings_broth", [], same_stage_ok=True)
    u("bottleneck_panel", "Bottlenecks", all_of(realm("bone_forging_9")), "the_wall", ["page:breakthrough"])
    u("stored_qi", "Stored Qi", all_of(realm("bone_forging_9")), "the_wall", [], same_stage_ok=True, toast=False)

    # Qi Kindling
    u("technique_slots_2", "Techniques", all_of(realm("qi_kindling_1")), "first_technique", ["hud:skills", "page:techniques"])
    u("dao_tree", "Dao tree", all_of(realm("qi_kindling_1")), "first_technique", ["page:dao"], same_stage_ok=True, toast=False)
    u("storage", "Storage", all_of({"kind": "account_realm", "realm": "qi_kindling_1"}), "", ["page:storage"], scope="account")
    u("alchemy", "Alchemy", all_of(realm("qi_kindling_2")), "mei_qings_furnace", [], effects=[{"kind": "grant_item", "item": "bronze_furnace", "count": 1}])
    u("teleport_stones", "Teleport stones", all_of(realm("qi_kindling_3")), "stones_that_move_you", ["page:teleport"],
      effects=[{"kind": "grant_item", "item": "spirit_stone_shard", "count": 2}])
    u("insight_sites", "Insight sites", all_of(realm("qi_kindling_4")), "listening_to_the_waterfall", [])
    u("contemplate", "Contemplate", all_of(realm("qi_kindling_4")), "listening_to_the_waterfall", [], same_stage_ok=True, toast=False)
    u("technique_slots_4", "More technique slots", all_of(realm("qi_kindling_5")), "two_hands_full", [])
    u("companions", "Companions", all_of(realm("qi_kindling_5")), "two_hands_full", ["page:companions"], same_stage_ok=True)
    u("appraisal", "Appraisal", all_of(realm("qi_kindling_6")), "is_it_real", [], effects=[{"kind": "grant_item", "item": "appraisers_loupe", "count": 1}])
    u("dungeon_keys", "Dungeons", all_of(realm("qi_kindling_7")), "the_caravan_road", [])
    u("auto_refine", "Auto-refine", all_of(realm("qi_kindling_8")), "batch_work", [])
    u("cleansing_prep", "Heaven's Cleansing", all_of(realm("qi_kindling_9")), "toward_cleansing_peak", [])

    # Qi Unfurling
    u("technique_page_2", "Ranged Qi and skill page 2", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [])
    u("composure", "Composure", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [], same_stage_ok=True)
    u("retreat_room", "Retreat room", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [], same_stage_ok=True, toast=False)
    u("your_sect", "Your own sect", all_of({"kind": "account_realm", "realm": "qi_unfurling_1"}), "a_hall_of_our_own", ["page:your_sect"], scope="account")
    u("smithing", "Smithing", all_of(realm("qi_unfurling_2")), "the_sect_forge", [], effects=[{"kind": "grant_item", "item": "forge_hammer", "count": 1}])
    u("inheritances", "Inheritances", all_of(realm("qi_unfurling_3")), "the_shrine_surfaces", [])
    u("herb_garden", "Herb garden", all_of(realm("qi_unfurling_4")), "seeds_of_the_valley", [])
    u("spirit_animals", "Spirit animals", all_of(realm("qi_unfurling_5")), "a_friend_in_the_reeds", ["hud:pet", "page:spirit_animals"])
    u("technique_slots_8", "Eight technique slots", all_of(realm("qi_unfurling_6")), "full_hands", [])
    u("field_bosses", "Field bosses", all_of(realm("qi_unfurling_7")), "the_riverbed_serpent", [])
    u("taming", "Taming", all_of(realm("qi_unfurling_7")), "calming_the_wild", [], same_stage_ok=True)
    u("tournament", "Tournament", all_of(realm("qi_unfurling_8")), "the_valley_tournament", [])
    u("heart_trial_prep", "Heart Trial preparation", all_of(realm("qi_unfurling_9")), "the_quiet_heart", [])

    # Heart Tempering to Heaven Glimpse
    u("formations", "Formations", all_of(realm("heart_tempering_1")), "lines_in_the_sand", ["page:formations"],
      effects=[{"kind": "grant_item", "item": "formation_kit", "count": 1}])
    u("perfect_timing", "Perfect timing", all_of(realm("heart_tempering_1")), "lines_in_the_sand", [], same_stage_ok=True, toast=False)
    u("healing", "Healing", all_of(realm("heart_tempering_3")), "the_infirmary", [], effects=[{"kind": "grant_item", "item": "needle_case", "count": 1}])
    u("array_plates", "Array plates", all_of(realm("heart_tempering_5")), "carry_a_wall", [])
    u("spirit_eggs", "Spirit eggs", all_of(realm("heart_tempering_5")), "the_warm_egg", [], same_stage_ok=True)
    u("second_companion", "Second companion", all_of(realm("heart_tempering_6")), "brothers_in_arms", [])
    u("guard_formation", "Guard formation", all_of(realm("heart_tempering_7")), "keep_watch", [])
    u("heart_trial", "The Heart Trial", all_of(realm("heart_tempering_9")), "the_heart_trial", [])
    u("flight", "Flight", all_of(realm("cloud_stride_1")), "wings_of_cloud", [])
    u("mounts", "Mounts", all_of(realm("cloud_stride_1")), "riding_the_wind", [], same_stage_ok=True)
    u("core_rank", "Core disciple", all_of(realm("cloud_stride_1"), qdone("the_valley_tournament")), "the_bracket", [], same_stage_ok=True)
    u("refine_qi", "Refine Qi", all_of(realm("cloud_stride_2")), "clearer_water", [])
    u("sky_rooms", "Sky rooms", all_of(realm("cloud_stride_3")), "above_the_mist", [])
    u("library_floor_3", "Library floor 3", all_of(realm("cloud_stride_4")), "the_upper_stacks", [])
    u("puppetry", "Puppetry", all_of(realm("cloud_stride_5")), "hands_of_wood", [])
    u("tournament_finals", "Tournament finals", all_of(realm("cloud_stride_7"), flag("tournament_top8")), "the_valley_finals", [])
    u("mind_lake_pill", "Mind Lake Opening", all_of(realm("cloud_stride_9")), "opening_the_lake", [])
    u("spirit_sense", "Spirit Sense", all_of(realm("spirit_awakening_1")), "a_lake_inside", ["hud:soul_bar", "hud:sense"])
    u("hidden_portals", "Hidden portals", all_of(realm("spirit_awakening_2")), "what_the_eyes_miss", [])
    u("binding", "Binding", all_of(realm("spirit_awakening_3")), "the_sleeping_blade", [])
    u("nourish_soul", "Nourish soul", all_of(realm("spirit_awakening_4")), "quiet_waters", [])
    u("personal_disciple", "Personal disciple", all_of(realm("spirit_awakening_5")), "the_mentors_gift", [])
    u("advanced_formations", "Restraint and Concealment formations", all_of(realm("spirit_awakening_1"), unlocked("library_floor_3")), "", [],
      same_stage_ok=True)
    u("pet_breeding", "Spirit animal breeding", all_of(realm("heaven_glimpse_1")), "", [], same_stage_ok=True)
    u("natural_treasures", "Natural treasures", all_of(realm("spirit_awakening_8")), "treasures_of_heaven_and_earth", [])
    u("research", "Research", all_of(realm("spirit_awakening_6")), "torn_pages", [])
    u("teaching", "Teaching", all_of(realm("spirit_awakening_7")), "passing_it_on", [])
    u("cape_slot", "Cape slot", all_of(realm("heaven_glimpse_1")), "a_wider_sky", [])
    u("currency_exchange", "Currency exchange", all_of(realm("heaven_glimpse_3")), "beyond_the_valley", ["page:exchange"])
    entries("unlocks", U)
    return U


# ---------------------------------------------------------------------------------------------
# Quests
Q = []


def o(kind, text, count=1, **kw):
    d = {"kind": kind, "text": text, "count": count}
    d.update(kw)
    return d


def quest(qid, name, kind, giver, objectives, rewards=(), hand_in=None, offer=(), complete=(), progress=(), **kw):
    d = {"id": qid, "name": name, "kind": kind, "giver": giver, "hand_in": giver if hand_in is None else hand_in,
         "marker": kw.pop("marker", "gold" if kind in ("main", "prologue") else "blue"),
         "objectives": list(objectives), "rewards": list(rewards)}
    if offer:
        d["offer_text"] = list(offer)
    if complete:
        d["complete_text"] = list(complete)
    if progress:
        d["progress_text"] = list(progress)
    d.update(kw)
    Q.append(d)
    return d


def item(i, n=1):
    return {"kind": "grant_item", "item": i, "count": n}


def taels(n):
    return {"kind": "grant_currency", "currency": "silver_tael", "amount": n}


def fx(kind, **kw):
    d = {"kind": kind}
    d.update(kw)
    return d


def prologue_quests():
    quest("morning_tide", "Morning Tide", "prologue", "aunt_ping", [
        o("collect", "Pick up Herbal Tea", 3, item="herbal_tea", consume=False),
        o("open_page", "Open your Bag", page="inventory"),
        o("use_portal", "Step outside"),
    ], [], hand_in="", sequential=True, target_room="lf_fishers_hut", chapter="prologue",
        offer=["You're awake! Good. The river's been muttering all night.", "Fetch the three teas I left about the hut, then look in your bag so you know where things are.",
               "Then out you go. Lu wants you at the docks."],
        progress=["Three teas. One on the table, one on the shelf, one by the stove."],
        complete=["There. Now go on, Lu's waiting."],
        next="a_quiet_river")
    quest("a_quiet_river", "A Quiet River", "prologue", "aunt_ping", [
        o("talk_to", "Find Lu at the Ferry Docks", npc="lu_boatman"),
    ], [], hand_in="lu_boatman", auto_accept=True, requires=all_of(qdone("morning_tide")), target_room="lf_village", chapter="prologue",
        complete=["You're up. The river is too quiet. Fish gone deep, birds gone high.",
                  "Help the village while I watch the water. Little Dou lost his kite, Old Ma needs a hand, Granny Liu has something for you, and Guo wants to see your fists.",
                  "Come back when you've done all four. Gold marks mean the story. Blue mean lessons."])
    after_lu = all_of(qdone("a_quiet_river"))
    quest("the_runaway_kite", "The Runaway Kite", "prologue", "little_dou", [
        o("deliver", "Fetch the kite from the Ferry Inn roof", item="kite"),
    ], [item("rice_ball", 1)], requires=after_lu, target_room="lf_village", chapter="prologue", marker="blue",
        offer=["My kite! It flew onto the inn roof! The big one!", "Climb the ladder on the Village Hall, then jump up. Jump twice if you have to!"],
        progress=["Ladder, hall roof, then jump onto the inn. You can do it!"],
        complete=["My kite! You're the best! Here, I saved this rice ball. It's only a bit squashed."])
    quest("mas_delivery", "Ma's Delivery", "prologue", "old_ma", [
        o("sell_item", "Sell the Old Net to Old Ma", item="old_net"),
        o("buy_item", "Buy Rice Balls", 2, item="rice_ball"),
    ], [taels(30)], requires=after_lu, target_room="lf_old_ma_store", chapter="prologue", marker="blue",
        on_accept=[item("old_net", 1), taels(10)],
        offer=["Aunt Ping's old net has been in my way for a month. Sell it back to me, fair and square.",
               "Then buy two rice balls. That's how trade works: you give, you get."],
        complete=["See? Coins go round like the river. Here's a little for your trouble."])
    quest("grannys_remedy", "Granny's Remedy", "prologue", "granny_liu", [
        o("use_system", "Put Herbal Tea in the Quick-use slot", system="set_quick_use"),
        o("use_item", "Drink a Herbal Tea", item="herbal_tea"),
        o("interact_object", "Pray at the village shrine", type="shrine"),
    ], [item("herbal_tea", 3)], requires=after_lu, target_room="lf_village", chapter="prologue", marker="blue",
        offer=["Hold still, child. Herbal Tea. Put it where your hand finds it without looking.", "Drink one. Then bow at the shrine in the square. It remembers those who visit."],
        complete=["Good. The shrine will patch you up when you're hurt. Tea when you can't reach it."])
    quest("race_to_the_tower", "Race to the Tower", "side", "shen_lian_npc", [
        o("interact_object", "Ring the watch-tower bell", object="tower_bell"),
    ], [fx("grant_title", title="fleet_footed")], requires=after_lu, target_room="lf_village", chapter="prologue", time_limit_s=25,
        offer=["Race you to the watch tower bell. Loser guts tomorrow's fish.", "Hold the joystick all the way over to sprint. Go!"],
        complete=["What?! ...Fine. Fleet-Footed. Don't let it go to your head."], fail_text="Too slow! Talk to Shen Lian to try again.")
    quest("fists_first", "Fists First", "prologue", "uncle_guo", [
        o("hit_object", "Punch the training stump", 12, type="training_stump"),
        o("hit_object", "Hit the dummy after its wind-up", 5, type="training_dummy"),
    ], [item("herbal_tea", 1)], requires=after_lu, target_room="lf_village", chapter="prologue",
        offer=["Fists first! Jab, cross, jab. Hold the button and they flow.", "Twelve on the stump. Then the dummy: watch it lean back before it swings. Hit it then."],
        progress=["Elbow in! Twelve on the stump, five on the dummy."],
        complete=["Not bad! The East Gate's open for you. Reed Shallows. Crabs. You'll see."])
    quest("a_quiet_river_return", "A Quiet River (Return)", "prologue", "lu_boatman", [
        o("talk_to", "Report to Lu", npc="lu_boatman"),
    ], [], hand_in="lu_boatman", auto_accept=True, target_room="lf_village", chapter="prologue",
        requires=all_of(qdone("the_runaway_kite"), qdone("mas_delivery"), qdone("grannys_remedy"), qdone("fists_first")),
        complete=["Kite, net, tea and fists. The village thanks you.", "Guo's fretting about the crabs in the Reed Shallows. Too many, too angry. Go and see him."])
    quest("crab_trouble", "Crab Trouble", "prologue", "uncle_guo", [
        o("collect", "Collect Crab Shells", 5, item="crab_shell"),
        o("kill", "Defeat Old Snapper", enemy="old_snapper", after=0),
    ], [taels(50), item("plain_straw_hat", 1)], requires=all_of(qdone("a_quiet_river_return")), target_room="lf_reed_shallows", chapter="prologue",
        offer=["The crabs came up the shallows in the night. Dozens. Something's pushing them out of the river.",
               "Bring me five shells. And if the big one shows, Old Snapper, watch its claw: step up or down when it rears back."],
        complete=["Old Snapper! Ha! Here, fifty taels and my old straw hat. Wear it, it keeps the sun out of a fighter's eyes."])
    quest("evening_on_the_river", "Evening on the River", "prologue", "lu_boatman", [
        o("talk_to", "Have dinner with Aunt Ping", npc="aunt_ping"),
        o("talk_to", "Meet Lu at the docks at sunset", npc="lu_boatman"),
    ], [fx("set_flag", flag="night_active"), fx("teleport", target="lf_village_night", portal="")], hand_in="", sequential=True,
        requires=all_of(qdone("crab_trouble")), target_room="lf_village", chapter="prologue",
        offer=["Eat with your aunt tonight. Then come to the docks at sunset. There's something I want to show you on the water."])
    quest("the_hollow_night", "The Hollow Night", "main", "lu_boatman", [
        o("set_flag", "Get Little Dou to the hut", flag="dou_safe"),
        o("set_flag", "Get Granny Liu to the hut", flag="granny_safe"),
        o("set_flag", "Get Old Ma to the hut", flag="ma_safe"),
        o("survive_timer", "Survive until Lu comes", event="hollow_night"),
    ], [], hand_in="", auto_accept=True, requires=all_of(flag("night_active"), noflag("night_survived")), target_room="lf_village_night", chapter="prologue")
    quest("the_river_token", "The River Token", "main", "lu_boatman", [
        o("meditate_seconds", "Meditate on the boat", 15),
        o("open_page", "Look inward (open the Cultivation page)", page="cultivation"),
        o("breakthrough", "Break through to Bone Forging 1"),
    ], [item("river_token", 1), fx("codex", entry="the_hollowing"), fx("codex", entry="realms")], auto_accept=True,
        requires=all_of(flag("night_survived")), target_room="lf_lu_boat", chapter="prologue",
        on_accept=[fx("learn_method", method="riverbreath_fragment"), fx("add_progress", pct_of_need=0.92), fx("codex", entry="lotus_ferry")],
        offer=["That thing in the water was a Hollowed eel. The grey is spreading.", "You have a gift. I felt it last night. Sit. Breathe as I showed you."],
        complete=["Bone Forging. Your first step. The body is the cup; Qi will be the water.",
                  "Take this River Token. Go west along the Willow Path. There's a note waiting for you."],
        next="the_willow_path")


def guided_quests():
    M = MENTORS
    quest("the_willow_path", "The Willow Path", "guided", "lu_boatman", [
        o("reach_room", "Reach Willow Path West", room="wp_west"),
        o("hit_object", "Hit a training stump", 30, type="training_stump"),
        o("kill", "Defeat Wild Boarlets", 5, enemy="wild_boarlet"),
    ], [item("rice_ball", 3), fx("codex", entry="body_training")], hand_in="", offered_by_unlock=True, auto_accept=True,
        target_room="wp_west", chapter="bf1",
        complete=["(A note in Lu's hand) Good. Now Stoneford. The sects are recruiting at the Fairground."])
    quest("the_recruitment_fair", "The Recruitment Fair", "guided", "recruiter_qing_lan", [
        o("talk_to", "Speak to the Jade Sect recruiter", npc="recruiter_qing_lan"),
        o("talk_to", "Speak to the Cloud Sect recruiter", npc="recruiter_mo_yun"),
        o("join_sect", "Choose a sect"),
    ], [fx("codex", entry="sects")], hand_in="", offered_by_unlock=True, target_room="sf_fairground", chapter="bf2",
        giver_any=["recruiter_qing_lan", "recruiter_mo_yun"],
        offer=["The Recruitment Fair! Both sects take new service disciples this week.", "Speak to both of us before you choose. The choice is for life."],
        complete=["Welcome, disciple. Now pass the Entry Trial."])
    quest("entry_trial", "Entry Trial", "guided", "recruiter_qing_lan", [
        o("reach_realm", "Reach Bone Forging 2", realm="bone_forging_2"),
        o("set_flag", "Climb to the trial bell", flag="trial_climbed"),
        o("kill", "Beat the Trial Puppet", enemy="trial_puppet"),
    ], [fx("sect_rank", rank="service_disciple"), item("entry_token", 1), fx("codex", entry="training_sects"),
        fx("set_flag", flag="prologue_done")], hand_in="",
        offered_by_unlock=True, auto_accept=True, target_room="sf_fairground", chapter="bf2",
        complete=["Service Disciple! Report to the steward at your sect's gate."])
    quest("a_disciples_chores", "A Disciple's Chores", "main", "jade_steward", [
        o("set_flag", "Sweep the first spot", flag="swept_ja_0", alt_flag="swept_cm_0"),
        o("set_flag", "Sweep the second spot", flag="swept_ja_1", alt_flag="swept_cm_1"),
        o("set_flag", "Sweep the third spot", flag="swept_ja_2", alt_flag="swept_cm_2"),
    ], [fx("set_flag", flag="dorm_bed"), taels(40), fx("add_contribution", amount=20)], offered_by_unlock=True, chapter="1",
        giver_any=STEWARDS, hand_in_any=STEWARDS, target_room="ja_gate_street",
        offer=["Service disciples sweep. Three spots on the street. The grey dust gets everywhere these days."],
        complete=["Clean enough. Your bunk is in the dorm: rest there any time."])
    quest("fish_gutting_fists", "Fish-Gutting Fists", "main", "shen_lian", [
        o("win_spar", "Beat Shen Lian in a spar", opponent="shen_lian"),
    ], [taels(40), fx("add_progress", pct_of_need=0.15)], requires=all_of(qdone("a_disciples_chores")), chapter="1",
        target_room="sf_fairground",
        offer=["Cloud Sect taught me more in a week than the river did in ten years. Spar me."],
        complete=["...Fine. You won. This time. Don't get lazy."])
    quest("the_weapon_hall", "The Weapon Hall", "guided", "jade_weapon_master", [
        o("equip_slot", "Take a training weapon from the rack", slot="weapon"),
        o("hit_object", "Try it on the dummies", 15, type="training_dummy"),
        o("use_system", "Raise your guard", system="guard"),
    ], [fx("codex", entry="weapons")], offered_by_unlock=True, chapter="1", giver_any=WEAPON_MASTERS, hand_in_any=WEAPON_MASTERS,
        on_accept=[item("training_jian", 1), item("training_spear", 1), item("training_gauntlets", 1)],
        target_room="ja_weapon_hall",
        offer=["Three training weapons: jian, spear, gauntlets. Try them on the dummies. Keep the one that feels like your own arm.",
               "Guard is the other half of a weapon. Hold it up when they swing."],
        complete=["Good hands. The weapon Dao grows with every strike. The smiths sell better ones in Stoneford."])
    quest("eyes_for_qi", "Eyes for Qi", "guided", "elder_hu", [
        o("meditate_seconds", "Meditate by a Qi spring or glowing spot", 60),
        o("gather_node", "Gather Willow Moss", 3, item="willow_moss", craft="herb_gathering"),
    ], [item("herb_sickle", 1), item("qi_gathering_pill", 1)], offered_by_unlock=True, chapter="1", giver_any=M, hand_in_any=M,
        target_room="lf_reed_shallows",
        offer=["You're starting to feel Qi in the air. Sit and let it show itself.", "Willow Moss grows in the Reed Shallows. Pick three: Mei Qing will want them."],
        complete=["You see it now. The valley glows, faintly, everywhere."])
    quest("outer_trial", "Outer Trial", "guided", "elder_hu", [
        o("win_spar", "Win spars at the practice posts", 3),
    ], [fx("sect_rank", rank="outer_disciple"), fx("add_contribution", amount=50)], offered_by_unlock=True, chapter="1", giver_any=M, hand_in_any=M,
        target_room="ja_pavilion_rooftops",
        offer=["Outer disciples are chosen by their fists. Win three spars at the practice posts."],
        complete=["Outer Disciple. You'll get a proper robe soon."])
    quest("stone_and_sweat", "Stone and Sweat", "guided", "foreman_dong", [
        o("gather_node", "Mine Copper", 5, item="copper_ore", craft="mining"),
        o("kill", "Defeat Rock Beetles", 5, enemy="rock_beetle"),
        o("dodge_attacks", "Dodge pebble throws", 3),
    ], [item("iron_pickaxe", 1)], offered_by_unlock=True, target_room="sq_quarry_rim", chapter="bf5",
        offer=["Take my old pickaxe. Five copper, five beetles. And dodge the imps' pebbles, they sting."],
        complete=["You'll make a miner yet. Here, an iron pick. Mind your toes."])
    quest("a_second_path", "A Second Path", "guided", "courier_lin", [
        o("use_system", "Create a second character or set an idle task", system="second_path"),
    ], [taels(200)], offered_by_unlock=True, hand_in="", chapter="bf5", target_room="",
        offer=["(A letter from your mentor) One cultivator can't walk every road. Train a second disciple, or leave this one to train while you rest."])
    quest("earning_your_keep", "Earning Your Keep", "guided", "jade_deacon", [
        o("use_system", "Finish daily missions", 2, system="daily_mission_done"),
    ], [fx("add_contribution", amount=40)], offered_by_unlock=True, chapter="bf6", giver_any=DEACONS, hand_in_any=DEACONS,
        on_accept=[fx("start_daily", count=5)], target_room="ja_gate_street",
        offer=["Missions. Five a day. Hunt, gather, deliver. Contribution buys what money can't."],
        complete=["The contribution shop is open to you now."])
    quest("the_first_current", "The First Current", "main", "lu_boatman", [
        o("meditate_seconds", "Meditate in the Lotus Ferry Qi spring", 30, near="qi_spring"),
        o("enter_seclusion", "Enter seclusion once"),
    ], [item("qi_gathering_pill", 2), fx("codex", entry="qi")], offered_by_unlock=True, chapter="3", target_room="lf_village",
        offer=["You feel it, don't you? A current inside. That's Qi. Your cup can hold water now.",
               "The old spring by Granny Liu's hut has woken. Sit in it. Then learn to cultivate while you sleep."],
        complete=["Your first current. Don't let it flood you."])
    quest("aunt_pings_broth", "Aunt Ping's Broth", "guided", "aunt_ping", [
        o("catch_fish", "Catch fish", 2),
        o("collect", "Gather Tough Meat", 2, item="tough_meat", consume=False),
        o("craft", "Cook Boar Bone Broth", recipe="boar_bone_broth", craft="cooking"),
    ], [fx("learn_recipe", recipe="riverfish_soup"), fx("learn_recipe", recipe="roast_fish"), fx("learn_recipe", recipe="lotus_root_tea")],
        offered_by_unlock=True, chapter="bf8", target_room="lf_village",
        on_accept=[fx("learn_recipe", recipe="boar_bone_broth")],
        offer=["You look thin! Here, my old pot and your uncle's rod. Two fish from the docks, two cuts of boar, and we'll make broth."],
        complete=["Now that's a broth. You'll feed yourself properly now, won't you?"])
    quest("the_wall", "The Wall", "guided", "elder_hu", [
        o("open_page", "Open the Bottleneck panel", page="breakthrough"),
        o("meditate_seconds", "Meditate until your Qi is full", 30),
    ], [item("qi_gathering_pill", 1)], offered_by_unlock=True, chapter="bf9", giver_any=M, hand_in_any=M,
        offer=["Bone Forging 9. Every realm ends in a wall. Look at it. Read what it asks."],
        complete=["Walls are only lists. Work down the list."])
    quest("first_technique", "First Technique", "guided", "jade_hall_master", [
        o("learn_technique", "Learn a starter technique"),
        o("use_technique", "Use it", 20),
    ], [item("rice_ball", 5)], offered_by_unlock=True, chapter="qk1", giver_any=HALL_MASTERS, hand_in_any=HALL_MASTERS,
        on_accept=[fx("learn_technique", technique="flowing_palm")],
        target_room="ja_pavilion_rooftops",
        offer=["Qi Kindling. Now your Qi can leave your body. Flowing Palm: push Qi through the palm. Twenty times."],
        complete=["The technique remembers you now. Train it and it grows."])
    quest("mei_qings_furnace", "Mei Qing's Furnace", "guided", "mei_qing", [
        o("collect", "Gather Willow Moss", 4, item="willow_moss", consume=False),
        o("craft", "Refine Healing Pills", 3, recipe="healing_pill", craft="alchemy"),
    ], [fx("learn_recipe", recipe="qi_restoration_pill"), fx("learn_recipe", recipe="purging_pill")], offered_by_unlock=True, chapter="qk2",
        on_accept=[fx("learn_recipe", recipe="healing_pill")], target_room="sf_artisan_row",
        offer=["You have Qi enough to feed a furnace. Take this little bronze one. Healing Pills: willow moss and patience."],
        complete=["Three pills. None of them exploded. You're a natural."])
    quest("stones_that_move_you", "Stones That Move You", "guided", "keeper_shi", [
        o("interact_object", "Touch teleport stones", 2, type="teleport_stone"),
        o("teleport", "Teleport once"),
    ], [item("spirit_stone_shard", 3)], offered_by_unlock=True, chapter="qk3", target_room="sf_market",
        offer=["Touch the stones and they'll remember you. A shard pays the way."],
        complete=["Travel lighter now. The valley's smaller than you thought."])
    quest("listening_to_the_waterfall", "Listening to the Waterfall", "guided", "elder_hu", [
        o("reach_room", "Reach the Falls Pool", room="cf_falls_pool"),
        o("meditate_seconds", "Meditate at the insight stone", 90),
    ], [item("clear_mind_pill", 1)], offered_by_unlock=True, chapter="qk4", giver_any=M, hand_in_any=M, target_room="cf_falls_pool",
        offer=["Some places teach. The Falls Pool teaches Water. Sit by the insight stone and listen."],
        complete=["You heard it. Insight grows the Dao; the Dao shapes the technique."])
    quest("two_hands_full", "Two Hands Full", "guided", "elder_hu", [
        o("choose_companion", "Choose a companion"),
        o("kill", "Defeat the Thicket Heart elite together", enemy="thornback_boar"),
    ], [fx("codex", entry="companions")], offered_by_unlock=True, chapter="qk5", giver_any=M, hand_in_any=M, target_room="bg_thicket_heart",
        offer=["Four disciples of your year are looking for a partner. Pick one. Then prove it in the Thicket Heart."],
        complete=["Two can walk where one would fall. Your technique slots have grown too."])
    quest("is_it_real", "Is It Real?", "guided", "elder_gu", [
        o("use_system", "Appraise items", 3, system="appraise"),
    ], [item("spirit_stone_shard", 3)], offered_by_unlock=True, chapter="qk6", target_room="sf_artisan_row",
        on_accept=[item("dusty_curio", 3)],
        offer=["Here's a loupe. Look at three things and tell me what they really are. Half the valley's jade is glass."],
        complete=["Good eye. Keep it. The wandering merchant Old Pan will trade with you now."])
    quest("the_caravan_road", "The Caravan Road", "guided", "elder_gu", [
        o("kill", "Defeat Mudwater Bandits", 6, enemy="mudwater_bandit"),
        o("collect", "Find the Hideout key", item="mudwater_key", consume=False),
    ], [fx("codex", entry="dungeons")], offered_by_unlock=True, chapter="qk7", target_room="cr_caravan_road",
        offer=["My carts go missing on the Caravan Road. Mudwater bandits. Thin them out and find their key."],
        complete=["The Hideout. Take the key; clear the place and my carts roll again."])
    quest("batch_work", "Batch Work", "guided", "mei_qing", [
        o("use_system", "Queue an auto-refine batch", system="auto_refine_queued"),
        o("use_system", "Collect the batch", system="auto_refine_collected"),
    ], [item("drying_rack", 1)], offered_by_unlock=True, chapter="qk8", target_room="sf_artisan_row",
        offer=["You can't stand at the furnace all day. Queue a batch and come back."],
        complete=["Here's a drying rack for herbs. Batches go faster with dry ingredients."])
    quest("toward_cleansing_peak", "Toward Cleansing Peak", "main", "elder_hu", [
        o("reach_room", "Climb the Pilgrim Stairs", room="cp_pilgrim_stairs"),
        o("kill", "Defeat Stone Guardians", 3, enemy="stone_guardian"),
    ], [fx("learn_recipe", recipe="cleansing_pill"), fx("codex", entry="heavens_cleansing")], offered_by_unlock=True, chapter="4",
        giver_any=M, hand_in_any=M, target_room="cp_pilgrim_stairs",
        offer=["Qi Kindling 9. The next wall is Heaven's Cleansing: heaven washes the impurities out of you. Or tries.",
               "Climb the Pilgrim Stairs. The guardians test who may approach the summit."],
        complete=["The summit is open to you. Prepare Cleansing Pills before the rite."])
    quest("after_the_cleansing", "After the Cleansing", "guided", "elder_hu", [
        o("use_technique", "Use a ranged technique", 10, ranged=True),
    ], [fx("sect_rank", rank="inner_disciple"), fx("add_contribution", amount=100)], offered_by_unlock=True, chapter="4", giver_any=M, hand_in_any=M,
        on_accept=[fx("learn_technique_for_weapon", options={"none": "palm_wave", "gauntlets": "palm_wave", "jian": "crescent_arc",
                                                             "spear": "spear_lance", "short_blade": "flying_blades", "staff": "earthshaker_wave",
                                                             "bow": "pinning_arrow"})],
        offer=["Qi Unfurling. Your Qi can fly now. Send it at a target ten times."],
        complete=["Inner Disciple. A retreat room is yours; the door is past the mission hall."])
    quest("the_sect_forge", "The Sect Forge", "guided", "jade_smith", [
        o("craft", "Forge a Common weapon", craft="smithing"),
        o("use_system", "Enhance it to +1", system="enhance"),
    ], [fx("learn_recipe", recipe="jadeiron_jian")], offered_by_unlock=True, chapter="qu2", giver_any=SMITHS, hand_in_any=SMITHS,
        on_accept=[fx("learn_recipe", recipe="iron_jian"), fx("learn_recipe", recipe="iron_spear"), fx("learn_recipe", recipe="iron_gauntlets")],
        offer=["A disciple with Qi in their hands can work the sect forge. Take this hammer. Forge something, then make it better."],
        complete=["An Earth blueprint. Don't waste the Jadeiron."])
    quest("seeds_of_the_valley", "Seeds of the Valley", "guided", "jade_gardener", [
        o("interact_object", "Tend a garden bed", 3, type="garden_bed"),
    ], [item("willow_moss", 5)], offered_by_unlock=True, chapter="qu4", giver_any=["jade_gardener", "cloud_gardener"], hand_in_any=["jade_gardener", "cloud_gardener"],
        offer=["Plant, water, harvest. Three beds."], complete=["You've got green hands."])
    quest("a_friend_in_the_reeds", "A Friend in the Reeds", "guided", "hermit_yao", [
        o("bond_pet", "Choose a starter spirit animal"),
    ], [item("bonding_offering_common", 5)], offered_by_unlock=True, chapter="qu5", target_room="rm_hermit_stilt_house",
        offer=["Three young ones came to me after the grey took their mothers. An otter, a fox and a crane chick. One will choose you."],
        complete=["Feed it, fight beside it, and it'll grow."])
    quest("full_hands", "Full Hands", "guided", "jade_hall_master", [
        o("reach_mastery", "Raise a technique to mastery tier 4", tier=4),
    ], [item("manual_page", 1)], offered_by_unlock=True, chapter="qu6", giver_any=HALL_MASTERS, hand_in_any=HALL_MASTERS,
        offer=["Eight slots now. But a technique used a thousand times beats eight used once. Tier 4."],
        complete=["Here, a manual page. Pages push mastery past what practice alone can."])
    quest("the_riverbed_serpent", "The Riverbed Serpent", "guided", "jade_deacon", [
        o("kill", "Defeat the Riverbed Serpent", enemy="riverbed_serpent"),
    ], [item("serpent_core", 1), taels(300)], offered_by_unlock=True, chapter="qu7", giver_any=DEACONS, hand_in_any=DEACONS,
        target_room="dw_serpents_shallows",
        offer=["The notice board's been screaming about it: the Riverbed Serpent surfaces in Serpent's Shallows every 45 minutes. Stand on the high rocks."],
        complete=["The serpent's core. Alchemists will pay well; better still, keep it."])
    quest("calming_the_wild", "Calming the Wild", "guided", "hermit_yao", [
        o("bond_pet", "Tame a wild spirit animal"),
    ], [item("bonding_offering_earth", 1)], offered_by_unlock=True, chapter="qu7", target_room="rm_marsh_edge",
        offer=["Wild ones wander the valley now: otters in the marsh, foxes in the bamboo, crane chicks at the falls. Calm one."],
        complete=["It trusts you. Don't make me regret it."])
    quest("the_bracket", "The Bracket", "guided", "arena_master", [
        o("win_spar", "Win your bracket bouts", 2, opponent="sparring_disciple"),
    ], [fx("set_flag", flag="tournament_top8"), fx("sect_rank", rank="core_disciple"), fx("add_contribution", amount=150)],
        offered_by_unlock=True, chapter="cs1", same_stage_ok=True,
        offer=["Cloud Stride, and a qualifier behind you. The bracket's open: two more wins puts you in the top eight.",
               "Top eight means core disciple. The elders are watching."],
        complete=["Top eight. Core disciple. The third floor of the library is yours."])
    quest("the_valley_finals", "The Valley Finals", "guided", "arena_master", [
        o("win_spar", "Win the finals", 3, opponent="sparring_disciple"),
    ], [fx("grant_title", title="valley_champion"), fx("add_prestige", amount=50), taels(500)], offered_by_unlock=True, chapter="cs7",
        offer=["Finals. Three bouts, no rest between. Win and the valley knows your name."],
        complete=["Valley Champion. Wear it lightly."])
    quest("the_valley_tournament", "The Valley Tournament (Qualifier)", "guided", "arena_master", [
        o("win_spar", "Win arena matches", 3, opponent="sparring_disciple"),
    ], [fx("set_flag", flag="tournament_entry"), fx("add_contribution", amount=100)], offered_by_unlock=True, chapter="7",
        offer=["Three wins and you're in the Valley Tournament."], complete=["You're in. The bracket opens at Cloud Stride."])
    quest("the_quiet_heart", "The Quiet Heart", "guided", "elder_hu", [
        o("use_item", "Burn Calm Incense", item="calm_incense"),
        o("meditate_seconds", "Meditate without backlash", 300),
    ], [item("myriad_year_calm_incense", 1)], offered_by_unlock=True, chapter="qu9", giver_any=M, hand_in_any=M,
        on_accept=[item("calm_incense", 1)],
        offer=["The Heart Trial will show you yourself. Practise stillness first. Five minutes, no backlash."],
        complete=["Still water. Take this incense for the real trial."])
    quest("lines_in_the_sand", "Lines in the Sand", "guided", "jade_formation_elder", [
        o("use_system", "Place and fuel a gathering formation", system="formation_placed"),
    ], [item("fuel_crystal_low", 10)], offered_by_unlock=True, chapter="ht1", giver_any=FORMATION_ELDERS, hand_in_any=FORMATION_ELDERS,
        on_accept=[item("fuel_crystal_low", 3)],
        offer=["Three nodes, one centre, fuel in each. A gathering formation thickens Qi around you."],
        complete=["Lines hold. Formations are patience made visible."])
    quest("the_infirmary", "The Infirmary", "guided", "jade_physician", [
        o("use_system", "Treat injured disciples", 3, system="treat_patient"),
    ], [fx("add_contribution", amount=100)], offered_by_unlock=True, chapter="ht3", giver_any=PHYSICIANS, hand_in_any=PHYSICIANS,
        offer=["Needles, pills and a gentle hand. Three patients."], complete=["Healing is cultivation turned outward."])
    quest("carry_a_wall", "Carry a Wall", "guided", "jade_formation_elder", [
        o("craft", "Craft an Array Plate", recipe="array_plate"),
    ], [item("blank_plate", 3)], offered_by_unlock=True, chapter="ht5", same_stage_ok=True, giver_any=FORMATION_ELDERS, hand_in_any=FORMATION_ELDERS,
        on_accept=[fx("learn_recipe", recipe="array_plate"), item("blank_plate", 1), item("formation_stone", 1)],
        offer=["A formation you can carry. Etch one plate."], complete=["Take these blanks."])
    quest("the_warm_egg", "The Warm Egg", "guided", "hermit_yao", [
        o("use_system", "Incubate a spirit egg", system="egg_incubated"),
    ], [item("spirit_egg", 1)], offered_by_unlock=True, chapter="ht5", same_stage_ok=True, on_accept=[item("spirit_egg", 1)],
        offer=["An egg, warm and humming. Keep it close."], complete=["Another life in your care."])
    quest("brothers_in_arms", "Brothers in Arms", "guided", "elder_hu", [
        o("choose_companion", "Choose a second companion"),
        o("reach_room", "Clear Echo Cliffs together", room="wg_echo_cliffs"),
    ], [], offered_by_unlock=True, chapter="ht6", giver_any=M, hand_in_any=M,
        offer=["The gorge is too much for two. Take a second companion."], complete=["Three together. Good."])
    quest("keep_watch", "Keep Watch", "guided", "jade_formation_elder", [
        o("breakthrough", "Break through a stage inside a guard formation", formation="guard"),
    ], [item("fuel_crystal_low", 2)], offered_by_unlock=True, chapter="ht7", giver_any=FORMATION_ELDERS, hand_in_any=FORMATION_ELDERS,
        offer=["A guard formation around you while you break through: nothing interrupts, nothing surprises."], complete=["Safe and stronger."])
    quest("the_heart_trial", "The Heart Trial", "main", "elder_hu", [
        o("pass_event", "Win the Trial of Reflections", event="heart_trial"),
    ], [fx("codex", entry="heart_trial")], offered_by_unlock=True, chapter="6", giver_any=M, hand_in_any=M,
        offer=["Step into the circle on my peak. What comes out of the mirror is you. Beat it."],
        complete=["You looked yourself in the eye and didn't blink. Cloud Stride awaits."])
    quest("wings_of_cloud", "Wings of Cloud", "main", "elder_hu", [
        o("use_system", "Take to the air: jump again at the top of a double jump", system="flight"),
        o("reach_room", "Reach the Cliff Faces", room="cc_cliff_faces"),
        o("kill", "Defeat Cloudwing Cranes", 3, enemy="cloudwing_crane"),
    ], [fx("codex", entry="flight")], offered_by_unlock=True, chapter="7", giver_any=M, hand_in_any=M,
        offer=["Cloud Stride. Your Qi can carry you. The cranes of the cliffs will teach you the rest."],
        complete=["The sky is a road now."])
    quest("riding_the_wind", "Riding the Wind", "guided", "hermit_yao", [
        o("bond_pet", "Bond with your spirit animal again"),
        o("use_system", "Ride it: Spirit Animals, choose Mount", system="mount"),
    ], [], offered_by_unlock=True, chapter="cs1", same_stage_ok=True, offer=["A big enough friend can carry you."], complete=["Hold on tight."])
    quest("clearer_water", "Clearer Water", "guided", "elder_hu", [
        o("enter_seclusion", "Seclusion with Refine Qi", focus="refine_qi"),
    ], [fx("add_purity", amount=100.0)], offered_by_unlock=True, chapter="cs2", giver_any=M, hand_in_any=M,
        offer=["Impure Qi clouds everything. Refine it in seclusion."], complete=["Clearer. Purer. Stronger."])
    quest("above_the_mist", "Above the Mist", "guided", "elder_hu", [
        o("reach_room", "Reach the Sky Ledges", room="cc_sky_ledges"),
        o("kill", "Defeat Stormwing Hawks", 5, enemy="stormwing_hawk"),
    ], [fx("learn_technique", technique="cloud_descent")], offered_by_unlock=True, chapter="cs3", giver_any=M, hand_in_any=M,
        offer=["Up. Higher. The hawks nest on the Sky Ledges."], complete=["Cloud Descent: fall on them like weather."])
    quest("the_upper_stacks", "The Upper Stacks", "guided", "jade_librarian", [
        o("reach_rank", "Reach core disciple", rank="core_disciple"),
    ], [item("manual_page", 2)], offered_by_unlock=True, chapter="cs4", giver_any=LIBRARIANS, hand_in_any=LIBRARIANS,
        offer=["Floor 3 is for core disciples."], complete=["Mind the dust. Some manuals bite."])
    quest("hands_of_wood", "Hands of Wood", "guided", "tinkerer_yu", [
        o("use_system", "Build a worker puppet", system="puppet_built"),
    ], [], offered_by_unlock=True, chapter="cs5", on_accept=[item("spirit_wood", 4), item("puppet_core", 1)],
        offer=["A puppet that gathers while you cultivate. Here's wood and a core; build one at my bench."], complete=["Look at it go!"])
    quest("opening_the_lake", "Opening the Lake", "guided", "mei_qing", [
        o("collect", "Gather Cloud Feathers", 3, item="cloud_feather", consume=False),
        o("collect", "Gather Cloudtop Orchids", 2, item="cloudtop_orchid", consume=False),
        o("craft", "Refine the Mind Lake Opening Pill", recipe="mind_lake_opening_pill", craft="alchemy"),
    ], [], offered_by_unlock=True, chapter="cs9", on_accept=[fx("learn_recipe", recipe="mind_lake_opening_pill")],
        offer=["Spirit Awakening needs a mind lake. This pill opens it."], complete=["Take it when you're ready to wake."])
    quest("a_lake_inside", "A Lake Inside", "guided", "elder_hu", [
        o("use_system", "Pulse Spirit Sense", 5, system="spirit_sense"),
    ], [item("cloud_talisman", 1)], offered_by_unlock=True, chapter="sa1", giver_any=M, hand_in_any=M,
        offer=["Your soul has a lake now. Pulse it outward: Spirit Sense."], complete=["The world has more in it than eyes see."])
    quest("what_the_eyes_miss", "What the Eyes Miss", "main", "elder_hu", [
        o("use_portal", "Find and use hidden portals", 3, hidden=True),
    ], [fx("learn_secret_art", art="concealment")], offered_by_unlock=True, chapter="8", giver_any=M, hand_in_any=M,
        offer=["Hidden doors all over the valley. Sense them. Use them."], complete=["Concealment: be what the eyes miss."])
    quest("the_sleeping_blade", "The Sleeping Blade", "guided", "elder_hu", [
        o("reach_room", "Reach the Drowned Shrine vault", room="ds_abbots_sanctum"),
        o("collect", "Take the Sleeping Blade from its altar", item="sleeping_blade", consume=False),
        o("use_system", "Bind it (Bag: tap the blade, Bind; stand clear of blows)", system="bind"),
    ], [], offered_by_unlock=True, chapter="sa3", giver_any=M, hand_in_any=M,
        offer=["The Abbot's vault holds a blade that sleeps. Your soul can wake it."], complete=["It chose you. Treat it well."])
    quest("quiet_waters", "Quiet Waters", "guided", "elder_hu", [
        o("enter_seclusion", "Seclusion with Nourish soul", focus="nourish_soul"),
    ], [fx("learn_recipe", recipe="soul_soothing_pill")], offered_by_unlock=True, chapter="sa4", giver_any=M, hand_in_any=M,
        offer=["Souls tire. Rest yours."], complete=["Soul Soothing Pills, for the worst days."])
    quest("the_mentors_gift", "The Mentor's Gift", "guided", "elder_hu", [
        o("win_spar", "Pass the personal-disciple trial", opponent="sparring_disciple"),
    ], [fx("learn_secret_art", art="lotus_heart_breathing")], offered_by_unlock=True, chapter="sa5", giver_any=M, hand_in_any=M,
        offer=["Beat my best disciple and I'll teach you personally."], complete=["My personal disciple. My secret art is yours, and the cave behind the pagoda is your abode."])
    quest("treasures_of_heaven_and_earth", "Treasures of Heaven and Earth", "guided", "elder_hu", [
        o("collect", "Pick the Mindwell Lotus behind Crane Falls", item="mindwell_lotus", consume=False),
        o("use_system", "Plant the Evergreen Heart seed in rich earth (the elder's peak, your cave abode or the Back Mountain)",
          system="plant_evergreen"),
    ], [], offered_by_unlock=True, chapter="sa8", giver_any=M, hand_in_any=M, on_accept=[item("evergreen_heart_seed", 1)],
        offer=["Heaven and earth grow a few things that are worth more than pills. Never sell them.",
               "A lotus that shields the soul. A tree whose fruit lifts you from death's edge. Take this seed."],
        complete=["Good. One more: at the Forgotten Monastery stands the Nine-Bough Jade Tree.",
                  "When your understanding stalls at a wall, sit beneath it. Only then will it answer."])
    quest("torn_pages", "Torn Pages", "guided", "jade_librarian", [
        o("use_system", "Restore a damaged manual", system="restore_manual"),
    ], [item("restoration_ink", 3)], offered_by_unlock=True, chapter="sa6", giver_any=LIBRARIANS, hand_in_any=LIBRARIANS,
        on_accept=[item("torn_manual", 1), item("restoration_ink", 1)],
        offer=["Restore a manual. Ink, patience, insight."], complete=["You gave a dead technique back its voice."])
    quest("passing_it_on", "Passing It On", "guided", "elder_hu", [
        o("use_system", "Teach an NPC disciple", system="teach"),
    ], [], offered_by_unlock=True, chapter="sa7", giver_any=M, hand_in_any=M, offer=["Teach, and learn twice."], complete=["You'll make a fine elder."])
    quest("a_wider_sky", "A Wider Sky", "main", "elder_hu", [
        o("reach_room", "Reach the Forgotten Monastery", room="mp_forgotten_monastery"),
        o("meditate_seconds", "Meditate by the heaven insight stone", 120),
    ], [item("mistjade_cape", 1), fx("learn_technique", technique="glimpse_of_heaven")], offered_by_unlock=True, chapter="9", giver_any=M, hand_in_any=M,
        offer=["Heaven Glimpse. There's a stone at the Forgotten Monastery where the sky leans close."], complete=["You glimpsed it. Now the valley feels small."])
    quest("beyond_the_valley", "Beyond the Valley", "main", "lu_boatman", [
        o("reach_room", "Follow Lu's map to the Frozen Shrine on Summit Ridge", room="sr_frozen_shrine"),
    ], [fx("codex", entry="azure_expanse")], offered_by_unlock=True, chapter="10", target_room="sr_frozen_shrine",
        offer=["Heaven Glimpse 3. The valley can't hold you any more. Here: my old map.",
               "The way out runs past the Frozen Shrine. Walk it once, then come back and tell me what you saw."],
        complete=["The Gate is past the shrine, then. Before you go, the village will want to see you."],
        next="farewells")
    quest("farewells", "Farewells", "main", "lu_boatman", [
        o("talk_to", "Visit Aunt Ping", npc="aunt_ping"),
        o("talk_to", "Visit Old Ma", npc="old_ma"),
        o("talk_to", "Visit Granny Liu", npc="granny_liu"),
        o("talk_to", "Visit Little Dou", npc="little_dou"),
        o("talk_to", "Visit Uncle Guo", npc="uncle_guo"),
    ], [], requires=all_of(qdone("beyond_the_valley")), chapter="10", target_room="lf_village",
        offer=["Say your farewells. Aunt Ping first, or she'll never forgive either of us."],
        complete=["Good. Now go. The river will still be here."],
        next="the_ascension_gate")
    quest("the_ascension_gate", "The Ascension Gate", "main", "lu_boatman", [
        o("kill", "Defeat the Gate Guardian", enemy="gate_guardian"),
    ], [fx("codex", entry="act_one_end")], hand_in="", auto_accept=True, requires=all_of(qdone("farewells")), chapter="10",
        target_room="mp_ascension_gate")


def main_quests():
    """Act I main story chapters 2, 3, 5, 6, 8, 9 (others are guided quests above)."""
    M = MENTORS
    quest("strange_tracks", "Strange Tracks", "main", "elder_hu", [
        o("interact_object", "Investigate grey patches in the Reed Marsh", 3, type="inspect", room="rm_marsh_edge"),
    ], [taels(60)], requires=all_of(realm("bone_forging_4"), qdone("entry_trial")), chapter="2", giver_any=M, hand_in_any=M, target_room="rm_marsh_edge",
        offer=["Disciples report grey patches in the Reed Marsh. Colour drained from the reeds. Look, but touch nothing."],
        complete=["Hollowing. It's closer than we hoped."])
    quest("the_humming_token", "The Humming Token", "main", "elder_hu", [
        o("reach_room", "Follow the token to the Grey Pools", room="rm_grey_pools"),
        o("kill", "Defeat Hollowed Boarlets", 5, enemy="hollowed_boarlet"),
    ], [taels(80), fx("codex", entry="hollowed")], requires=all_of(qdone("strange_tracks")), chapter="2", giver_any=M, hand_in_any=M,
        target_room="rm_grey_pools",
        offer=["Your River Token hums when you face east. Follow it."], complete=["Lu's token. It knows the grey. Keep it close."])
    quest("mei_qings_errand", "Mei Qing's Errand", "main", "mei_qing", [
        o("collect", "Bring Willow Moss", 5, item="willow_moss"),
        o("collect", "Bring Copper Ore", 3, item="copper_ore"),
    ], [item("healing_pill", 3), taels(60)], requires=all_of(qdone("the_humming_token")), chapter="2", target_room="sf_artisan_row",
        offer=["The Hollowed wounds need a new salve. Willow moss and copper dust."], complete=["This will save lives. Thank you."])
    quest("grey_at_the_edges", "Grey at the Edges", "main", "elder_hu", [
        o("talk_to", "Report to your mentor", npc="elder_hu", npc_any=MENTORS),
    ], [fx("add_progress", pct_of_need=0.2)], requires=all_of(qdone("mei_qings_errand")), chapter="2", giver_any=M, hand_in_any=M, hand_in="",
        offer=["Tell me everything you saw."], auto_accept=True)
    quest("bandits_on_the_road", "Bandits on the Road", "main", "guard_hou", [
        o("kill", "Defeat Mudwater Bandits", 10, enemy="mudwater_bandit"),
    ], [taels(150)], requires=all_of(realm("qi_kindling_6")), chapter="3", target_room="cr_caravan_road",
        offer=["The Caravan Road's a bandit den. Ten of them, and Stoneford breathes easier."], complete=["Good work. The Mudwater won't forget you."])
    quest("gus_cargo", "Gu's Cargo", "main", "elder_gu", [
        o("reach_room", "Escort the cart to Bend Shore", room="dw_bend_shore"),
    ], [taels(200)], requires=all_of(qdone("bandits_on_the_road"), realm("qi_kindling_7")), chapter="3", target_room="cr_caravan_road",
        offer=["One cart, one road, one bodyguard. You."], complete=["Every crate intact. You'll go far."])
    quest("mudwater_hideout", "Mudwater Hideout", "main", "guard_hou", [
        o("kill", "Defeat \"Big Toad\" Tan", enemy="big_toad_tan"),
    ], [taels(300), item("mudwater_manual", 1)], requires=all_of(qdone("the_caravan_road")), chapter="3", target_room="mh_boss_den",
        offer=["Tan runs the Mudwater from the hideout. End him."], complete=["The road's safe. Stoneford owes you."])
    quest("the_rite", "The Rite", "main", "elder_hu", [
        o("pass_event", "Complete Heaven's Cleansing", event="heavens_cleansing"),
    ], [fx("codex", entry="yan_heng")], requires=all_of(qdone("toward_cleansing_peak")), chapter="4", giver_any=M, hand_in_any=M,
        target_room="cp_cleansing_summit",
        offer=["Stand in the circle at the summit. Let heaven wash you."], complete=["You saw someone in the light. A man with a river in his eyes. Yan Heng..."])
    quest("the_shrine_surfaces", "The Shrine Surfaces", "main", "elder_hu", [
        o("reach_room", "Enter the Drowned Shrine", room="ds_flooded_gate"),
    ], [], offered_by_unlock=True, chapter="5", giver_any=M, hand_in_any=M,
        offer=["The Drowned Shrine has risen at Deepwater Bend. Lu's handwriting is on the old maps."], complete=["Go deeper."])
    quest("lus_handwriting", "Lu's Handwriting", "main", "elder_hu", [
        o("interact_object", "Find Lu's inscriptions", 4, type="inspect", room="ds_hall_of_lanterns"),
    ], [fx("codex", entry="lu_past")], requires=all_of(qdone("the_shrine_surfaces")), chapter="5", giver_any=M, hand_in_any=M,
        target_room="ds_hall_of_lanterns", offer=["Find what Lu wrote."], complete=["Lu was here. Long before you were born."])
    quest("the_riverbreath_trial", "The Riverbreath Trial", "main", "elder_hu", [
        o("pass_event", "Pass Lu's inheritance trial at the Scripture Well", event="riverbreath_trial"),
    ], [fx("codex", entry="riverbreath_inheritance")], requires=all_of(qdone("lus_handwriting")), chapter="5", giver_any=M, hand_in_any=M,
        target_room="ds_scripture_well",
        offer=["Lu left more than words down there. An inheritance tests the one who claims it.",
               "Stand in the stone ring by the well and hold while the drowned rise. Breathe with the river."],
        complete=["The well accepted you. Now only the Abbot stands between you and Lu's method."])
    quest("the_drowned_abbot", "The Drowned Abbot", "main", "elder_hu", [
        o("kill", "Defeat the Drowned Abbot", enemy="drowned_abbot"),
    ], [item("riverbreath_scroll", 1)], requires=all_of(qdone("the_riverbreath_trial")), chapter="5", giver_any=M, hand_in_any=M,
        target_room="ds_abbots_sanctum", offer=["The Abbot guards the Riverbreath inheritance. Ring his four bells to silence him."],
        complete=["The full Riverbreath. Lu's own method."])
    quest("quiet_before_the_storm", "Quiet Before the Storm", "main", "elder_hu", [
        o("reach_room", "Train in Whitewater Gorge", room="wg_rapids_terraces"),
        o("kill", "Defeat Rapids Lizards", 8, enemy="rapids_lizard"),
    ], [], requires=all_of(realm("heart_tempering_1")), chapter="6", giver_any=M, hand_in_any=M, target_room="wg_rapids_terraces",
        offer=["Heart Tempering tests Composure. Train where the water never rests."], complete=["Steadier. Good."])
    quest("shen_lians_failure", "Shen Lian's Failure", "main", "shen_lian", [
        o("win_spar", "Duel Shen Lian", opponent="shen_lian"),
    ], [], requires=all_of(realm("heart_tempering_5")), chapter="6", target_room="sf_fairground",
        offer=["I failed the Heart Trial. I saw... never mind. Fight me. I need to hit something that hits back."],
        complete=["Thanks. Don't fail yours."])
    quest("hidden_cargo", "Hidden Cargo", "main", "madam_hua", [
        o("use_system", "Use Spirit Sense in the warehouse district", system="spirit_sense"),
    ], [], requires=all_of(qdone("what_the_eyes_miss")), chapter="8", giver_any=["elder_gu", "madam_hua"], hand_in="elder_hu", hand_in_any=M,
        offer=["(A sealed note) Gu is smuggling Hollow shards. Sense the warehouses."], complete=["Hollow shards. Crates of them."])
    quest("gus_warehouse", "Gu's Warehouse", "main", "elder_hu", [
        o("reach_room", "Raid Gu's warehouse", room="si_gus_warehouse"),
        o("collect", "Take the smuggler's ledger", item="smuggler_ledger", consume=False),
    ], [fx("set_flag", flag="gu_fled")], requires=all_of(qdone("hidden_cargo"), realm("spirit_awakening_8")), chapter="8", giver_any=M, hand_in_any=M,
        offer=["Raid the warehouse. Take his ledger."], complete=["He fled through a Tide rift. The ledger will do."])
    quest("the_rift", "The Rift", "main", "elder_hu", [
        o("talk_to", "Report to Madam Hua", npc="madam_hua"),
    ], [taels(500)], requires=all_of(qdone("gus_warehouse")), chapter="8", giver_any=M, hand_in="madam_hua",
        offer=["Madam Hua takes over the trade house. Tell her what you found."], complete=["Thank you. The trade house will be honest now."])
    quest("allies_at_the_wall", "Allies at the Wall", "main", "elder_hu", [
        o("use_system", "Build formations with both sects", 2, system="formation_placed"),
    ], [], requires=all_of(realm("heaven_glimpse_2")), chapter="9", giver_any=M, hand_in_any=M,
        offer=["Both sects will stand together. Build the wall formations."], complete=["The wall holds. For now."])
    quest("the_siege", "The Siege", "main", "elder_hu", [
        o("pass_event", "Survive the Siege of Two Sects", event="siege_of_two_sects"),
    ], [item("siege_medal", 1)], requires=all_of(qdone("allies_at_the_wall")), chapter="9", giver_any=M, hand_in_any=M,
        offer=["They're coming. Hollow waves, and something huge."], complete=["We held."])
    quest("what_remains", "What Remains", "main", "elder_hu", [
        o("talk_to", "Speak with your mentor", npc="elder_hu", npc_any=MENTORS),
    ], [], requires=all_of(qdone("the_siege")), chapter="9", giver_any=M, hand_in_any=M, auto_accept=True,
        complete=["I'm still here. Because you cleared every defence. Thank you."])


def side_quests():
    # Small valley threads for the people who had none (optional; Part 8 "about 35 side quests").
    quest("nets_and_shells", "Nets and Shells", "side", "fisher_wen", [o("collect", "Bring Mudshell Crab shells", 5, item="crab_shell")],
          [taels(40), item("roast_fish", 2)], requires=all_of(realm("bone_forging_2")), target_room="lf_reed_shallows",
          offer=["The crabs cut my nets to ribbons. Bring me their shells and I'll patch the nets with them. Fair's fair."],
          complete=["Ha! Crab-shell floats. They'll never live it down. Here, supper."])
    quest("the_muddy_wash", "The Muddy Wash", "side", "washer_mei", [o("kill", "Chase the Reedtail Rats off the washing lines", 6, enemy="reedtail_rat")],
          [taels(40)], requires=all_of(realm("bone_forging_3")), target_room="lf_reed_shallows",
          offer=["Rats in the reeds again. They chew the lines and drag the washing through the mud. Six of them, at least."],
          complete=["Clean sheets for once. Bless you."])
    quest("beetle_shell_lacquer", "Beetle Shell Lacquer", "side", "storekeeper_fang", [o("collect", "Bring Rock Beetle shells", 6, item="beetle_shell")],
          [taels(90)], requires=all_of(realm("bone_forging_5")), target_room="sq_quarry_rim",
          offer=["Ground beetle shell makes the finest lacquer in the valley. The quarry beetles are too tough for my porters."],
          complete=["Look at that shine. The Jade Sect will pay double for boxes like these."])
    quest("copper_for_the_bellows", "Copper for the Bellows", "side", "smith_bao", [o("collect", "Bring Copper ore", 8, item="copper_ore")],
          [taels(100), item("forge_hammer", 1)], requires=all_of(realm("bone_forging_5")),
          offer=["My bellows need new copper fittings and the quarry price doubled. Mine me some, would you?"],
          complete=["Good ore. Take my old hammer. It still rings true."])
    quest("auntie_rongs_soup", "Auntie Rong's Soup", "side", "auntie_rong", [o("deliver", "Bring Riverfish Soup", 2, item="riverfish_soup")],
          [taels(80), item("lotus_root_tea", 2)], requires=all_of(realm("bone_forging_8"), unlocked("cooking")),
          offer=["My hands shake too much to gut fish these days. Two bowls of riverfish soup for my grandsons?"],
          complete=["Just like my mother made. Take some tea, dear."])
    quest("kais_wager", "Kai's Wager", "side", "adventurer_kai", [o("kill", "Defeat Mud Hounds at the Mudwater stockade", 6, enemy="mud_hound")],
          [taels(150)], requires=all_of(realm("qi_kindling_7")), target_room="mh_stockade",
          offer=["I bet Rui you could clear the stockade kennels before I could. Don't make me lose."],
          complete=["Ha! Rui owes me a month of dumplings. Here's your cut."])
    quest("su_qings_map", "Su Qing's Map", "side", "adventurer_su", [
        o("reach_room", "Reach the Echo Cliffs", room="wg_echo_cliffs"),
        o("kill", "Drive off Boulder Serpents", 3, enemy="boulder_serpent"),
    ], [taels(250), item("spirit_stone_low", 2)], requires=all_of(realm("heart_tempering_3")), target_room="wg_echo_cliffs",
          offer=["I'm charting the gorge for the cartographers' guild. The serpents on the Echo Cliffs keep eating my surveyors' lunch."],
          complete=["The ledge is clear. My map will have your name in the corner."])
    quest("mins_first_caravan", "Min's First Caravan", "side", "hamlet_trader_min", [o("kill", "Clear the gorge bandits from the caravan road", 5, enemy="gorge_bandit_adept")],
          [item("spirit_stone_low", 3)], requires=all_of(qdone("market_day")), target_room="wg_gorge_mouth",
          offer=["Greyreed's first caravan leaves for Stoneford tomorrow. The gorge bandits know it too."],
          complete=["The caravan made it! Greyreed is a real trade post now."])
    quest("wen_zhaos_challenge", "Wen Zhao's Challenge", "side", "wen_zhao", [o("win_spar", "Beat Wen Zhao in a rematch", opponent="wen_zhao")],
          [fx("grant_title", title="rivals_respect")], requires=all_of(qdone("the_valley_finals")),
          offer=["The finals were luck. Face me again, here, with no crowd to cheer for you."],
          complete=["...Not luck, then. Next time I'll be ready."])
    quest("guos_old_wound", "Guo's Old Wound", "side", "uncle_guo", [o("collect", "Bring Willow Salve", item="willow_salve")],
          [taels(80)], requires=all_of(realm("qi_kindling_3")), target_room="lf_village",
          offer=["My old meridian wound aches. Granny's salve helps."], complete=["Ahh. Better."])
    quest("the_broken_kindling", "The Broken Kindling", "side", "uncle_guo", [o("collect", "Bring Qi Gathering Pills", 2, item="qi_gathering_pill")],
          [taels(120)], requires=all_of(qdone("guos_old_wound")), offer=["I want to try again. Kindling. Help me?"], complete=["We'll see."])
    quest("a_second_try", "A Second Try", "side", "uncle_guo", [o("talk_to", "Watch Uncle Guo meditate", npc="uncle_guo")],
          [fx("grant_title", title="guos_student")], requires=all_of(qdone("the_broken_kindling"), realm("qi_unfurling_1")),
          offer=["Stay with me while I try."], complete=["Qi Kindling 1. At my age! Ha!"], hand_in="")
    quest("dous_kite_returns", "Dou's Kite Returns", "side", "little_dou", [o("deliver", "Bring a Cloud Feather for the new kite", item="cloud_feather")],
          [taels(50)], requires=all_of(realm("bone_forging_3"), qdone("the_runaway_kite")), offer=["I'm making a kite that flies to the clouds! I need a cloud feather."],
          complete=["It flies! Sort of!"])
    quest("dou_wants_to_train", "Dou Wants to Train", "side", "little_dou", [o("hit_object", "Show Dou how to punch the stump", 20, type="training_stump")],
          [fx("grant_title", title="big_sibling")], requires=all_of(qdone("dous_kite_returns")), offer=["Teach me to punch! Please please please."],
          complete=["Hi-YAH! Did you see?!"])
    quest("grey_roofs", "Grey Roofs", "side", "hamlet_elder_gao", [o("kill", "Clear the Hollowed from the Grey Pools", 10, enemy="hollowed_boarlet")],
          [taels(120)], requires=all_of(realm("heart_tempering_1")), target_room="rm_grey_pools",
          offer=["Clear the pools and we can walk home."], complete=["The road home is open."])
    quest("cleansing_the_well", "Cleansing the Well", "side", "hamlet_elder_gao", [o("set_flag", "Cleanse the hamlet well", flag="well_cleansed")],
          [taels(150)], requires=all_of(qdone("grey_roofs")), target_room="gh_hamlet_square",
          on_accept=[item("cleansing_pill", 1)], offer=["The well. If it runs clear, we stay."], complete=["Clear water. Thank you."])
    quest("market_day", "Market Day", "side", "hamlet_elder_gao", [o("deliver", "Deliver Rice", 10, item="rice")],
          [taels(200)], requires=all_of(qdone("cleansing_the_well")), offer=["A market needs goods. Rice to start."],
          complete=["Greyreed trades again!"])
    quest("old_pans_errand_1", "Old Pan's First Errand", "side", "old_pan", [o("deliver", "Bring Ember Peppers", 5, item="ember_pepper")],
          [item("spirit_stone_low", 2)], requires=all_of(unlock_req("appraisal")), offer=["Peppers. Five."], complete=["Spicy. Good."])
    quest("old_pans_errand_2", "Old Pan's Second Errand", "side", "old_pan", [o("deliver", "Bring a Pearl", item="pearl")],
          [item("spirit_stone_low", 4)], requires=all_of(qdone("old_pans_errand_1")), offer=["A pearl. From the tide crabs."], complete=["Lovely."])
    quest("old_pans_errand_3", "Old Pan's Third Errand", "side", "old_pan", [o("deliver", "Bring Mist Lotus", 2, item="mist_lotus")],
          [fx("set_flag", flag="pan_rotation_plus")], requires=all_of(qdone("old_pans_errand_2")), offer=["Mist lotus. Two."],
          complete=["I'll keep something special for you from now on."])
    for cid, name, lines in [
        ("lan_yue", "Lan Yue", [("the_herb_thief", "The Herb Thief", "kill", "bamboo_monkey", 8), ("a_cure_for_stoneford", "A Cure for Stoneford", "collect", "riverreed_ginseng_10", 5),
                                ("lan_yues_oath", "Lan Yue's Oath", "kill", "drowned_acolyte", 6)]),
        ("tie_niu", "Tie Niu", [("iron_oxs_debt", "Iron Ox's Debt", "collect", "copper_ore", 10), ("the_quarry_fight", "The Quarry Fight", "kill", "stone_tortoise", 5),
                                ("stronger_than_stone", "Stronger Than Stone", "kill", "boulder_serpent", 5)]),
        ("qiu_feng", "Qiu Feng", [("the_missing_hunter", "The Missing Hunter", "kill", "green_viper", 6), ("crane_falls_at_dawn", "Crane Falls at Dawn", "reach", "cf_falls_pool", 1),
                                  ("one_arrow", "One Arrow", "kill", "mist_vulture", 5)]),
        ("bai_ling", "Bai Ling", [("lines_on_the_floor", "Lines on the Floor", "collect", "formation_stone", 3), ("the_broken_array", "The Broken Array", "kill", "jade_sentinel", 4),
                                  ("bai_lings_formation", "Bai Ling's Formation", "collect", "formation_stone", 6)]),
    ]:
        prev = None
        for qid, qname, kind, target, n in lines:
            if kind == "kill":
                ob = o("kill", "Defeat %s" % target.replace("_", " ").title(), n, enemy=target)
            elif kind == "collect":
                ob = o("collect", "Gather %s" % target.replace("_", " ").title(), n, item=target)
            else:
                ob = o("reach_room", "Visit the Falls Pool at dawn", room=target)
            rq = all_of({"kind": "companion_owned", "companion": cid}) if prev is None else all_of(qdone(prev))
            quest(qid, qname, "side", cid, [ob], [fx("add_bond", amount=10), taels(80)], requires=rq, chapter="companion",
                  offer=["%s has a favour to ask." % name], complete=["%s smiles. \"Thank you.\"" % name])
            prev = qid
    quest("a_hall_of_our_own", "A Hall of Our Own", "side", "courier_lin", [o("use_system", "Found your sect", system="found_sect")],
          [taels(300)], offered_by_unlock=True, hand_in="", offer=["(A letter) The Hidden Vale beyond Crane Falls could hold a sect. Yours."])
    quest("first_recruits", "First Recruits", "side", "courier_lin", [o("use_system", "Recruit NPC disciples", 2, system="recruit")],
          [taels(200)], requires=all_of(qdone("a_hall_of_our_own")), hand_in="", offer=["A sect needs people."])
    quest("walls_of_the_vale", "Walls of the Vale", "side", "courier_lin", [o("use_system", "Win a defence event", system="defence_won")],
          [taels(400)], requires=all_of(qdone("first_recruits")), hand_in="", offer=["Defend the Vale."])


def unlock_req(s):
    return {"kind": "unlock", "system": s}


# ---------------------------------------------------------------------------------------------
def dialogue():
    trees = {}

    def tree(tid, entries_, nodes):
        trees[tid] = {"id": tid, "entries": entries_, "nodes": nodes}

    # Night: send villagers to the hut.
    tree("little_dou", [{"requires": all_of({"kind": "in_room", "room": "lf_village_night"}, noflag("dou_safe")), "node": "night"}],
         {"night": {"lines": ["The water's grey! There's something in it!"],
                    "choices": [{"text": "Run to the hut! Now!", "effects": [{"kind": "set_flag", "flag": "dou_safe"}], "close": True}]}})
    tree("granny_liu", [{"requires": all_of({"kind": "in_room", "room": "lf_village_night"}, noflag("granny_safe")), "node": "night"}],
         {"night": {"lines": ["My old legs... help me, child."],
                    "choices": [{"text": "Lean on me. To Aunt Ping's hut.", "effects": [{"kind": "set_flag", "flag": "granny_safe"}], "close": True}]}})
    tree("old_ma", [{"requires": all_of({"kind": "in_room", "room": "lf_village_night"}, noflag("ma_safe")), "node": "night"}],
         {"night": {"lines": ["My shop! My stock!"],
                    "choices": [{"text": "Leave it! Get to the hut!", "effects": [{"kind": "set_flag", "flag": "ma_safe"}], "close": True}]}})
    # Sect choice at the Recruitment Fair.
    for rid, s, sname, pitch in [("recruiter_jade", "jade_sect", "Jade Sect", "Water's patience, the sword's clarity. Jade Current Scripture: steady, deep, forgiving."),
                                 ("recruiter_cloud", "cloud_sect", "Cloud Sect", "Wind and height. Cloudpiercing Canon: fast, sharp, a little wild.")]:
        tree(rid, [{"requires": all_of(qactive("the_recruitment_fair"), {"kind": "has_training_sect", "value": False},
                                       flag("met_recruiter_jade"), flag("met_recruiter_cloud")), "node": "choose"}],
             {"choose": {"lines": [pitch, "Will you join the %s?" % sname],
                         "choices": [{"text": "Join the %s" % sname, "effects": [{"kind": "join_sect", "sect": s}, {"kind": "set_flag", "flag": "joined_" + s}], "close": True},
                                     {"text": "Let me think", "close": True}]}})
    tree("aunt_ping", [{"requires": all_of(qactive("evening_on_the_river")), "node": "dinner"}],
         {"dinner": {"lines": ["Sit, sit. Fish congee. Your favourite.", "...Lu took you out on the water tonight? Be careful. The river's been strange."],
                     "choices": [{"text": "I'll be careful.", "close": True}]}})
    tree("lu", [], {})
    tree("shen_lian", [], {})
    tree("uncle_guo", [], {})
    comps = [("lan_yue", "Lan Yue, the healer", "Lan Yue mends what others break. Quiet, stubborn, never leaves a wounded friend."),
             ("tie_niu", "Tie Niu, the brawler", "Tie Niu hits first and apologises never. A wall with fists."),
             ("qiu_feng", "Qiu Feng, the archer", "Qiu Feng can split a reed at a hundred paces. Keeps to the back."),
             ("bai_ling", "Bai Ling, the formation student", "Bai Ling draws lines that bite. Clever, impatient, loyal.")]

    def comp_choices(flag_id, about_node):
        return [{"text": label, "requires": all_of({"kind": "companion_owned", "companion": cid, "value": False}),
                 "effects": [{"kind": "add_companion", "companion": cid}, {"kind": "set_flag", "flag": flag_id}], "close": True}
                for cid, label, _ in comps] + [{"text": "Tell me about them", "next": about_node}, {"text": "Later", "close": True}]

    def about(back):
        return {"lines": [blurb for _, _, blurb in comps], "choices": [{"text": "I'm ready to choose", "next": back}]}
    tree("mentor", [{"requires": all_of({"kind": "realm_below", "realm": "bone_forging_4"}), "node": "young"},
                    {"requires": all_of(qactive("two_hands_full"), noflag("companion_1")), "node": "companion"},
                    {"requires": all_of(qactive("brothers_in_arms"), noflag("companion_2")), "node": "companion_2"}],
         {"young": {"lines": ["Come back when your body is ready. Bone Forging 4, at least.", "Sweep, train, eat. In that order."],
                    "choices": [{"text": "Yes, Elder.", "close": True}]},
          "companion": {"lines": ["Four disciples of your year still walk alone. One of them should walk with you.", "Who will it be?"],
                        "choices": comp_choices("companion_1", "about_1")},
          "companion_2": {"lines": ["The gorge is too much for two. Who else will you trust?"], "choices": comp_choices("companion_2", "about_2")},
          "about_1": about("companion"), "about_2": about("companion_2")})
    # Hermit Yao: the starter spirit animal (S22) and the mount bond at Cloud Stride.
    tree("hermit_yao", [{"requires": all_of(qactive("a_friend_in_the_reeds"), noflag("starter_chosen")), "node": "starter"},
                        {"requires": all_of(qactive("riding_the_wind"), noflag("mount_bonded")), "node": "mount"}],
         {"starter": {"lines": ["Three young ones came to me after the grey took their mothers.",
                                "The otter gathers, the fox fights, the crane chick cultivates and will carry you one day. Which one looks back at you?"],
                      "choices": [{"text": "The Reed Otter", "effects": [{"kind": "choose_starter", "species": "reed_otter"}], "close": True},
                                  {"text": "The Ember Fox kit", "effects": [{"kind": "choose_starter", "species": "ember_fox"}], "close": True},
                                  {"text": "The Jade Crane chick", "effects": [{"kind": "choose_starter", "species": "jade_crane"}], "close": True},
                                  {"text": "Let me watch them a while", "close": True}]},
          "mount": {"lines": ["Cloud Stride, eh? Then a big enough friend can carry you.", "This crane has watched you for weeks. Hold out your hand."],
                    "choices": [{"text": "Hold out a hand", "effects": [{"kind": "grant_pet", "species": "jade_crane"}, {"kind": "set_flag", "flag": "mount_bonded"}], "close": True},
                                {"text": "Not yet", "close": True}]}})
    for tid, t in trees.items():
        write(tid + ".json", {"trees": {tid: t}}, folder=os.path.join(DATA, "dialogue"))


def mail_templates():
    rows = [
        {"id": "aunt_ping_realm", "from": "Aunt Ping", "subject": "You reached {realm}!", "body": "Lu told me. I cried a little. Eat properly. I sent rice balls."},
        {"id": "mentor_hint", "from": "Your mentor", "subject": "About that wall", "body": "You've been stuck at {realm} for a while. Open the Breakthrough panel and read each requirement. Every one has a fix."},
        {"id": "welcome_gift", "from": "The Valley", "subject": "Welcome to Jade River", "body": "A small gift for the road."},
        {"id": "dou_drawing", "from": "Little Dou", "subject": "I drew you!", "body": "This is you punching a crab. The crab is losing."},
        {"id": "overflow", "from": "Lost and Found", "subject": "Items you couldn't carry", "body": "These were found where you left them."},
        {"id": "idle_report", "from": "Your disciple", "subject": "While you were away", "body": "{summary}"},
        {"id": "mentor_letter", "from": "Your mentor", "subject": "A second path", "body": "One cultivator cannot walk every road."},
    ]
    entries("mail_templates", rows)


def codex():
    rows = [
        {"id": "lotus_ferry", "title": "Lotus Ferry", "body": "A fishing village at the river's bend. Aunt Ping, Lu and a few dozen others. Home."},
        {"id": "the_hollowing", "title": "The Hollowing", "body": "A grey that drains colour, then life. Hollowed beasts have empty white eyes."},
        {"id": "realms", "title": "Realms", "body": "Mortal, Bone Forging, Qi Kindling, Qi Unfurling, Heart Tempering, Cloud Stride, Spirit Awakening, Heaven Glimpse... and beyond the valley, more."},
        {"id": "body_training", "title": "Body training", "body": "Stumps and stones temper the body. Body Level supports every breakthrough."},
        {"id": "sects", "title": "Training sects", "body": "The Jade Sect Academy by the river and the Cloud Sect Monastery on the cliffs."},
        {"id": "training_sects", "title": "Ranks", "body": "Service, outer, inner, core and personal disciples."},
        {"id": "weapons", "title": "Weapons", "body": "Gauntlets, jian, spear, short blade, staff and bow. Each has its Dao."},
        {"id": "qi", "title": "Qi", "body": "The river's breath, gathered inside you. Meditate to gather it; techniques spend it."},
        {"id": "companions", "title": "Companions", "body": "Fellow disciples who fight beside you."},
        {"id": "dungeons", "title": "Dungeons", "body": "Chains of rooms with a boss at the end and a chest for the brave."},
        {"id": "heavens_cleansing", "title": "Heaven's Cleansing", "body": "At Qi Kindling 9, heaven washes the body of impurity."},
        {"id": "hollowed", "title": "Hollowed beasts", "body": "Grey versions of valley animals. They spread the Hollowing with every hit."},
        {"id": "yan_heng", "title": "Yan Heng", "body": "A figure in the light of the Cleansing. A man with a river in his eyes."},
        {"id": "lu_past", "title": "Lu's past", "body": "Lu's handwriting on a shrine drowned a hundred years ago."},
        {"id": "riverbreath_inheritance", "title": "The Riverbreath inheritance", "body": "Lu hid his method's full form at the bottom of the Scripture Well, for whoever could breathe with the river."},
        {"id": "heart_trial", "title": "The Heart Trial", "body": "A mirror. What comes out is you."},
        {"id": "flight", "title": "Flight", "body": "At Cloud Stride, Qi carries the body."},
        {"id": "azure_expanse", "title": "The Azure Expanse", "body": "Beyond the Ascension Gate: a larger world."},
        {"id": "act_one_end", "title": "Beyond the Gate", "body": "You passed the Gate Guardian. The river keeps flowing."},
        {"id": "river_of_time", "title": "River of Time and Space", "body": "Locked.", "locked": True},
        {"id": "jade_river", "title": "The Jade River", "body": "It runs through every land you will ever see."},
    ]
    entries("codex", rows)


def validate(npc_ids, U):
    """Cross-reference quests, npcs, unlocks, items, enemies and rooms (the Godot validator repeats this)."""
    def ids(name):
        return {e["id"] for e in json.load(open(os.path.join(DATA, name + ".json")))["entries"]}
    items = ids("items") | ids("artifacts")
    enemies = ids("enemies")
    rooms = {f[:-5] for f in os.listdir(os.path.join(DATA, "rooms"))}
    quests = {q["id"] for q in Q}
    errs = []
    for u in U:
        if u.get("quest") and u["quest"] not in quests:
            errs.append("unlock %s quest %s" % (u["id"], u["quest"]))
    for q in Q:
        for who in [q["giver"], q["hand_in"]] + q.get("giver_any", []) + q.get("hand_in_any", []):
            if who and who not in npc_ids:
                errs.append("quest %s npc %s" % (q["id"], who))
        for ob in q["objectives"]:
            if "item" in ob and ob["item"] not in items:
                errs.append("quest %s item %s" % (q["id"], ob["item"]))
            if "enemy" in ob and ob["enemy"] not in enemies:
                errs.append("quest %s enemy %s" % (q["id"], ob["enemy"]))
            if "room" in ob and ob["room"] not in rooms:
                errs.append("quest %s room %s" % (q["id"], ob["room"]))
            if ob["kind"] == "talk_to" and ob["npc"] not in npc_ids:
                errs.append("quest %s talk %s" % (q["id"], ob["npc"]))
        for r in q["rewards"] + q.get("on_accept", []):
            if r["kind"] == "grant_item" and r["item"] not in items:
                errs.append("quest %s reward %s" % (q["id"], r["item"]))
        if q.get("next") and q["next"] not in quests:
            errs.append("quest %s next %s" % (q["id"], q["next"]))
        if q.get("target_room") and q["target_room"] not in rooms:
            errs.append("quest %s target %s" % (q["id"], q["target_room"]))
    for u in U:
        for e in u["effects"]:
            if e["kind"] == "grant_item" and e["item"] not in items:
                errs.append("unlock %s item %s" % (u["id"], e["item"]))
    # Every NPC placed in a room exists; every quest giver is placed somewhere.
    placed = set()
    for f in os.listdir(os.path.join(DATA, "rooms")):
        room = json.load(open(os.path.join(DATA, "rooms", f)))
        for ob in room["objects"]:
            if ob["type"] == "npc":
                placed.add(ob["npc"])
                if ob["npc"] not in npc_ids:
                    errs.append("room %s npc %s" % (room["id"], ob["npc"]))
    companions_only = {"lan_yue", "tie_niu", "qiu_feng", "bai_ling"}
    for q in Q:
        givers = q.get("giver_any") or [q["giver"]]
        if not any(g in placed or g in companions_only or g == "courier_lin" for g in givers):
            errs.append("quest %s giver not placed: %s" % (q["id"], givers))
    assert not errs, "\n".join(errs)


def build():
    Q.clear()
    npc_ids = npcs()
    U = unlocks()
    prologue_quests()
    guided_quests()
    main_quests()
    side_quests()
    entries("quests", Q)
    d = os.path.join(DATA, "dialogue")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    dialogue()
    mail_templates()
    codex()
    validate(npc_ids, U)
    print("quests:", len(Q), "npcs:", len(npc_ids), "unlocks:", len(U))


if __name__ == "__main__":
    build()
