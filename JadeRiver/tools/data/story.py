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


NPC_AGES = {"aunt_ping": 46, "lu_boatman": 61, "little_dou": 9, "old_ma": 72, "granny_liu": 83, "uncle_guo": 54,
            "shen_lian_npc": 16, "shen_lian": 16, "wen_zhao": 17, "mei_qing": 19, "mei_qing_sect": 19, "madam_hua": 41,
            "old_scribe_bai": 77, "magistrate_qian": 58, "guard_hou": 38, "peddler_shao": 50, "elder_hu": 212, "elder_sung": 187,
            "lan_yue": 18, "tie_niu": 20, "qiu_feng": 22, "bai_ling": 17, "hermit_yao": 340, "elder_gu": 96}


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
    # S49 the mortal kingdom: the county magistrate keeps the hall behind the gatehouse.
    npc("magistrate_qian", "Magistrate Qian", "County magistrate", outfit("long_tied", 1, "scholar", "scholar", "folded", hat="guan", shirt_dye="indigo"),
        ["The county has more trouble than hands. You have hands.", "Cultivators pass through Stoneford like weather. The ones who stop to help are remembered.",
         "Keep your techniques sheathed in the villages. Ordinary people have long memories and short tempers."],
        ["Next petition!", "The county thanks you."], services=["page:county"], service_labels={"page:county": "County business"})
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
    npc("guildmaster_tang", "Guildmaster Tang", "Alchemist Guild", outfit("topknot", 4, "scholar", "scholar", "slippers", hat="guan", shirt_dye="jade", pants_dye="ink"),
        ["The guild does not care who taught you. It cares what comes out of your furnace.",
         "An exam is a batch of pills against a candle. Nothing more mysterious than that.",
         "Commissions come in every morning. Pay is fair; the guild takes nothing but your good name."],
        ["Mind the candle.", "Another order for Healing Pills. Always Healing Pills."], services=["page:guild", "shop:alchemist_guild"])
    npc("old_scribe_bai", "Old Scribe Bai", "Talisman master", outfit("topknot", 5, "scholar", "scholar", "slippers", hat="guan", shirt_dye="ink"),
        ["A talisman is a sentence the world has to finish.", "Steady wrist, one breath, no lifting the brush."], ["Mind the ink."],
        services=["page:talisman"], service_labels={"page:talisman": "Write talismans"}, service_unlocks={"page:talisman": "talisman"})
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
    # Part 8 (S49 karma): the night peddler of the Caravan Road. Everything on his mat is a small sin.
    npc("peddler_shao", "Peddler Shao", "Sells after dark", outfit("long_tied", 4, "cardigan", "loose", "folded", hat="weimao", shirt_dye="ink", pants_dye="ink"),
        ["Don't ask where it came from. Ask what it costs.", "The road's quiet at night. Good for business. Bad for questions."], ["Psst."],
        services=["shop:night_peddler"])
    npc("hermit_yao", "Hermit Yao", "Marsh hermit", outfit("flowing", 1, "scholar", "loose", "folded", hat="straw", cape="tattered", shirt_dye="earth"),
        ["The otters trust me. Maybe one day they'll trust you.", "Spirit beasts are not tools. They are friends who bite."], ["Shh. Listen to the reeds."], services=["shop:hermit", "page:core_exchange"], tree="hermit_yao",
        service_labels={"page:core_exchange": "Core Exchange"}, service_unlocks={"page:core_exchange": "spirit_animals"})

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

    # Act II · Cloudgate Port and the Thunderhorn Plains (Azure Expanse, v1.1)
    npc("warden_cao", "Warden Cao", "Nine Peaks toll warden", outfit("topknot", 0, "disciple", "martial", "boots", hat="guan", weapon="spear",
        shirt_dye="indigo", pants_dye="ink"),
        ["Every sky road in the Expanse belongs to the Nine Peaks Alliance.", "Toll first, questions after. The Factor's hall is in the market."],
        ["Toll tokens, please.", "Next!"], tree="warden_cao")
    npc("alliance_guard", "Alliance Guard", "Nine Peaks patrol", outfit("short_knot", 0, "disciple", "martial", "boots", weapon="spear",
        shirt_dye="indigo", pants_dye="indigo"),
        ["Keep your Qi to yourself inside the port.", "Nine peaks, one law. The Alliance's."], ["Move along."])
    npc("wanderer_jiang", "Jiang", "Independent cultivator", outfit("flowing", 0, "vneck", "straight", "boots", weapon="sword", cape="tattered",
        shirt_dye="grey", pants_dye="ink"),
        ["The Alliance calls us 'unaffiliated'. We call ourselves free.", "Valley folk come through that gate every few years. Most go home."],
        ["Hm. Fresh from the valley."])
    npc("factor_ruan", "Factor Ruan", "Alliance factor", outfit("long_tied", 1, "scholar", "scholar", "folded", hat="guan", cape="solid",
        shirt_dye="indigo", pants_dye="ink"),
        ["Stormsteel, stormsilk, fair Alliance prices.", "Spirit Stones only. Taels are for the valley."],
        ["Alliance-grade goods!"], services=["shop:alliance_factor"])
    npc("peddler_gou", "Peddler Gou", "Sky road peddler", outfit("short_knot", 5, "vneck", "loose", "folded", hat="straw", shirt_dye="ochre"),
        ["Pills, charms, rice balls. Everything a traveller forgets.", "I've walked every sky road twice. Once to go, once to come back for my hat."],
        ["Traveller's goods!"], services=["shop:port_peddler"])
    npc("smith_hong", "Smith Hong", "Stormsteel smith", outfit("short_knot", 0, "sleeveless", "martial", "boots", shirt_dye="crimson"),
        ["Stormsteel wants a Sage's hands. Before that, it bites.", "Lightning Scar ore, spark pelt for the grip. That's the recipe."],
        ["*crackle* *clang*"], services=["shop:stormsteel_smith"])
    npc("apothecary_wu", "Apothecary Wu", "Port apothecary", outfit("ponytail", 3, "cardigan", "scholar", "slippers", shirt_dye="jade"),
        ["Storm blood is real. Newcomers bleed Qi into the wind until they attune.", "A Storm Blood Pill buys you half an hour of patience."],
        ["Remedies!"], services=["shop:port_apothecary"])
    npc("sky_sailor_pei", "Sailor Pei", "Sky-ship hand", outfit("short_knot", 0, "vneck", "cuffed", "boots", hat="headband", shirt_dye="cloud"),
        ["Never look down from a sky-ship. Look at the sails.", "The Alliance ships run to Nine Peaks. When they feel like it."], ["Heave!"])
    npc("sky_sailor_ning", "Sailor Ning", "Sky-ship hand", outfit("ponytail", 0, "vneck", "cuffed", "boots", hat="headband", shirt_dye="indigo"),
        ["The Qi cushion under the keel? Twelve stones a day to keep it fed.", "Storms on the plains sink ships. We go round."], ["Mind the ropes!"])
    npc("dockmaster_fu", "Dockmaster Fu", "Skydock master", outfit("topknot", 5, "scholar", "scholar", "folded", hat="tied", shirt_dye="ochre", pants_dye="grey"),
        ["No berths for private ships without Alliance papers.", "The Condensing Hall? Behind me. Mind the alchemist; she bites harder than the smith."],
        ["Berths full!"])
    npc("innkeeper_tang", "Innkeeper Tang", "Wayfarers' Inn", outfit("long_tied", 3, "cardigan", "straight", "slippers", shirt_dye="rose"),
        ["Rooms by the night, soup by the bowl, gossip for free.", "The broker in the corner? Pays her bill. That's all I ask."],
        ["Soup's on!"], services=["shop:wayfarers_inn"])
    npc("broker_mu", "Broker Mu", "Free broker", outfit("flowing", 1, "cardigan", "straight", "boots", hat="weimao", cape="solid", shirt_dye="ink", pants_dye="ink"),
        ["I sell what the Alliance doesn't want sold. Mostly, the truth.", "Your blood is still valley-soft. The storms here will drink it."],
        ["Information, fairly priced."], tree="broker_mu", services=["shop:free_market"])
    npc("alchemist_fen", "Alchemist Fen", "Condensing Hall", outfit("long_tied", 1, "scholar", "scholar", "folded", hat="guan", shirt_dye="white", pants_dye="grey"),
        ["Sage Qi is True Qi pressed until it remembers it was once light.", "Bring me thunder and I'll condense it into something you can swallow."],
        ["Don't touch the furnace."], services=["shop:condensing_hall"])
    npc("herder_suo", "Old Suo", "Thunderhorn herder", outfit("short_knot", 5, "vneck", "loose", "boots", hat="tied", cape="tattered", shirt_dye="earth"),
        ["The thunderhorns aren't cruel. They're just very sure of where they're going.", "Stew's hot. Stones, not taels, I'm afraid."],
        ["Easy, easy..."], services=["shop:herders_camp"])
    npc("herder_a_lan", "A-Lan", "Herder's daughter", outfit("ponytail", 0, "cardigan", "cuffed", "boots", shirt_dye="crimson"),
        ["Spark weasels steal the lightning out of the grass. Then they spit it at you!", "Grandpa Suo says the storms remember everyone who crosses."],
        ["Hup! Hup!"], scale=0.9)

    npc("hermit_shuang", "Hermit Shuang", "Rimefrost hermit", outfit("flowing", 5, "scholar", "scholar", "folded", cape="tattered",
        shirt_dye="white", pants_dye="grey"),
        ["...", "Snow keeps every footprint until the wind decides otherwise.", "Silence is not empty. Listen."],
        ["...", "Hm."])
    npc("grey_pilgrim", "The Grey Pilgrim", "A stranger", outfit("long_tied", 5, "scholar", "scholar", "folded", hat="weimao", cape="solid",
        shirt_dye="grey", pants_dye="grey"),
        ["You carry the valley's river on you. How quaint.", "Every shard finds its way home in the end. I only help them along."],
        ["..."], tint="#dfe2ea", tree="grey_pilgrim")

    # Act II · Nine Peaks, the Gale Canyons and Ironroot Hold (Phase C)
    npc("envoy_lanshi", "Envoy Lanshi", "Alliance envoy", outfit("long_tied", 0, "scholar", "scholar", "folded", hat="guan", cape="solid",
        shirt_dye="indigo", pants_dye="indigo"),
        ["Nine peaks, nine seats, one voice. Mine, today.", "The Alliance keeps the sky roads open. Someone has to."],
        ["The Hall is in session."], tree="envoy_lanshi")
    npc("elder_zhong", "Elder Zhong", "First Peak elder", outfit("flowing", 5, "scholar", "scholar", "folded", hat="guan", cape="solid",
        shirt_dye="white", pants_dye="grey"),
        ["The First Peak remembers when there was no Alliance. There were more graves then.",
         "A Hollow shard in the wrong hands is a war waiting for a reason."], ["Hm."], tree="elder_zhong")
    npc("auctioneer_tong", "Auctioneer Tong", "Auction Pavilion", outfit("topknot", 1, "scholar", "scholar", "folded", hat="guan",
        shirt_dye="crimson", pants_dye="ink"),
        ["Lots at dawn, hammers at dusk. Bid with your head, pay with your stones.",
         "The limit is in the other bidder's heart. Find it."], ["Going once!"], services=["page:auction"],
        service_labels={"page:auction": "Today's lots"}, service_unlocks={"page:auction": "auction_house"})
    npc("champion_qiao", "Champion Qiao", "Presence Terrace", outfit("topknot", 0, "disciple", "martial", "boots", hat="guan", weapon="spear",
        shirt_dye="indigo", pants_dye="ink"),
        ["Presence is the weight a cultivator puts on the air. Show me yours.", "Nine peaks, nine styles. I've learned eight."],
        ["Again."], services=["spar:alliance_champion"], service_labels={"spar:alliance_champion": "Spar"})
    npc("tollkeeper_bai", "Tollkeeper Bai", "Canyon Mouth toll", outfit("short_knot", 5, "vneck", "loose", "boots", hat="straw", weapon="spear",
        shirt_dye="indigo", pants_dye="earth"),
        ["Ten stones a crossing. Alliance tokens pass free.", "Brigands in the canyon wear veils. Honest folk don't."],
        ["Toll!"])
    npc("ironroot_warden", "Warden Tie Shan", "Ironroot gatekeeper", outfit("short_knot", 4, "sleeveless", "martial", "boots", hat="headband",
        weapon="staff", shirt_dye="earth", pants_dye="earth"),
        ["The Ironroot don't bend. We grow around things.", "Outsiders come to the Hold for iron. Few come for kin."],
        ["Halt."], services=["spar:ironroot_warden"], service_labels={"spar:ironroot_warden": "Test your root"})
    npc("matriarch_tie", "Matriarch Tie Yun", "Ironroot matriarch", outfit("long_tied", 5, "cardigan", "straight", "boots", hat="headband",
        cape="solid", shirt_dye="earth", pants_dye="ink"),
        ["Blood is who you were born to. Roots are who you choose to hold.", "Our ancestors sit in the Hall. They're picky about company."],
        ["The Hold is well."], tree="matriarch_tie")
    npc("clan_smith_gang", "Smith Gang", "Ironroot forge", outfit("short_knot", 0, "sleeveless", "martial", "boots", shirt_dye="earth"),
        ["Iron from the roots, fire from the canyon wind. Best forge in the Expanse.", "Kin get the good steel. Guests get the rest."],
        ["*CLANG*"], services=["shop:ironroot_clan"])
    # Act II · Phase D: the Oasis of Bones.
    npc("oasis_keeper_meng", "Keeper Meng", "Oasis of Bones", outfit("long_tied", 3, "vneck", "loose", "boots", hat="weimao",
        shirt_dye="ochre", pants_dye="earth"),
        ["Water is free. Shade is free. Everything else costs stones, because the caravans stopped coming.",
         "Drink before the heat asks you to. By then it's late."], ["Water here."], services=["shop:oasis_keeper"])
    npc("bone_reader_xiu", "Bone-Reader Xiu", "Diviner of the oasis", outfit("flowing", 5, "scholar", "scholar", "folded", cape="solid",
        shirt_dye="ink", pants_dye="ochre"),
        ["The bones remember the sand kings. I only read them aloud.", "Every crack in a shoulder blade is a road. Most end in the tomb."],
        ["The bones are warm today."], tree="bone_reader_xiu")

    # Act II · Phase E: the Shipwrights' Yard, the Skyport Wreck, the Trial Hall.
    npc("navigator_sun", "Navigator Sun", "Star navigator", outfit("flowing", 1, "scholar", "scholar", "folded", hat="straw", cape="solid",
        shirt_dye="indigo", pants_dye="ink"),
        ["The Starsea has no roads. Only stars, and the lines we draw between them.",
         "A chart is four readings and the patience to trust them. Most sailors have the readings."],
        ["Mind the table."], services=["shop:navigator"])
    npc("shipwright_lao", "Shipwright Lao", "Skydock shipwright", outfit("short_knot", 4, "sleeveless", "martial", "boots", hat="headband",
        shirt_dye="ochre", pants_dye="earth"),
        ["A hull is a formation you can stand on. Get one line wrong and the Starsea finds it.",
         "Spirit wood for the ribs, stormsteel for the keel, harpy plumes for the sail. The plumes are the hard part."],
        ["*tok tok tok*"], services=["shop:shipwright"])
    npc("gu_in_chains", "Elder Gu", "A prisoner of the comet sails", outfit("long_tied", 1, "scholar", "scholar", "folded",
        shirt_dye="grey", pants_dye="grey"),
        ["...", "Water. Or the key. Either."], ["..."], tree="gu_in_chains")
    npc("launch_warden_he", "Warden He", "Starsea Launch", outfit("topknot", 5, "vneck", "straight", "boots", hat="straw",
        shirt_dye="white", pants_dye="indigo"),
        ["The ring was built to throw ships at the stars. It has not thrown one in two hundred years.",
         "On clear nights you can see lanterns out there. Nobody hangs them. They are just there."],
        ["The ring is quiet."])
    npc("trial_master_wen", "Trial Master Wen", "Trial Hall", outfit("flowing", 0, "scholar", "scholar", "folded", hat="guan", cape="solid",
        shirt_dye="white", pants_dye="indigo"),
        ["Eight seats, eight Presences. The ninth seat waits for whoever can sit under the other eight and stay themselves.",
         "Will is not stubbornness. Stubbornness breaks. Will bends and comes back."],
        ["Sit up straight."])

    # Companions (S26)
    npc("lan_yue", "Lan Yue", "Healer", outfit("flowing", 4, "cardigan", "scholar", "slippers", weapon="staff", shirt_dye="indigo"),
        ["Stay close. I can't heal what I can't reach."], ["Careful!"], companion="lan_yue")
    npc("tie_niu", "Tie Niu", "Brawler", outfit("short_knot", 0, "sleeveless", "martial", "boots", shirt_dye="earth"),
        ["Hit me. No, harder. See? Iron Ox."], ["HAH!"], companion="tie_niu")
    npc("qiu_feng", "Qiu Feng", "Archer", outfit("high_pony", 0, "vneck", "cuffed", "boots", weapon="bow", shirt_dye="jade"),
        ["I mark them. You hit them. Simple."], ["Mark!"], companion="qiu_feng")
    npc("bai_ling", "Bai Ling", "Formation student", outfit("ponytail", 2, "disciple", "straight", "slippers", weapon="sword", shirt_dye="cloud"),
        ["Three nodes and a centre. Watch."], ["Lines drawn!"], companion="bai_ling")
    # S48 hidden cultivation: with a false realm showing (Concealment), common folk take you for the weaker cultivator
    # you pretend to be. The old and the strong see through it.
    concealed = {
        "guard_hou": ["Kindling, are you? Keep to the road. The Mudwater never went away, not really."],
        "adventurer_kai": ["You look green. The Caravan Road eats green travellers. Go in daylight, and not alone."],
        "storekeeper_fang": ["First time in town? The starter charms are on the low shelf. The good ones would cost you a year."],
        "old_pan": ["Spirit Stones only, little one. Come back when your Qi is worth a second look."],
        "smith_bao": ["Soft hands for a blade like that. I'll sharpen it anyway. Maybe it will teach you."],
        "elder_gu": ["A small cultivator with a heavy purse. Mind who sees you open it."],
        "innkeeper_tang": ["The cheap room's in the attic. Draughty, but honest, like the price."],
        "warden_cao": ["A low realm on the sky roads? Pay your toll and stay out of the Alliance's way."],
        "alliance_guard": ["Weak Qi and loud boots. Walk softly in the port, junior."],
        "peddler_gou": ["Newcomer? Everyone below Sage buys the storm charm. Everyone. Trust me."],
        "factor_ruan": ["Stormsteel is for Sages. Are you buying for your master?"],
        "tollkeeper_bai": ["Ten stones. For someone at your realm the canyon costs more than stones. Think on it."],
        "oasis_keeper_meng": ["Water is free, even for the weak. The sand is not so generous."],
        "navigator_sun": ["The Starsea eats small realms whole. Are you sure you want a chart?"],
        "elder_hu": ["You can hide your realm from bandits, child. Not from the one who taught you to breathe."],
        "elder_sung": ["A cloud can look like a small thing from below. I am not below you. Put the mask away when we talk."],
        "grey_pilgrim": ["A mask over a mask. How quaint. I see the river under both."],
        "elder_zhong": ["Hiding your realm on the First Peak? The Alliance notices those who make themselves small."],
        "champion_qiao": ["Hiding your weight? The Terrace will find it. Presence does not lie, even when you do."],
        "wanderer_jiang": ["Smart. Look weak, and the Alliance ignores you. The bandits won't, mind."],
    }
    for n in N:
        if n["id"] in concealed:
            n["concealed_lines"] = concealed[n["id"]]
    missing = set(concealed) - {n["id"] for n in N}
    assert not missing, missing
    # S49 affinity: favourite gifts, the id hearts are kept under, and what each heart pays once.
    from relations import AFFINITY, AFFINITY_ALIAS
    for n in N:
        aid = AFFINITY_ALIAS.get(n["id"], n["id"])
        if aid in AFFINITY:
            a = AFFINITY[aid]
            n["affinity"] = aid
            n["gifts"] = {"loved": list(a["loved"]), "liked": list(a["liked"])}
            n["heart_rewards"] = dict(a.get("rewards", {}))
    missing = (set(AFFINITY) | set(AFFINITY_ALIAS)) - {n["id"] for n in N}
    assert not missing, missing
    # S49 lifespan as flavour: the named people's ages when your story starts. They grow older with you (a year for
    # every four weeks you play, one season a week), shown wherever their hearts are.
    for n in N:
        if n["id"] in NPC_AGES:
            n["age"] = NPC_AGES[n["id"]]
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
    u("alchemy", "Alchemy", all_of(realm("qi_kindling_2")), "mei_qings_furnace", [], effects=[{"kind": "grant_item", "item": "bronze_furnace", "count": 1},
      {"kind": "codex", "entry": "pills_and_the_body"}, {"kind": "codex", "entry": "furnaces_and_fire"}])
    u("teleport_stones", "Teleport stones", all_of(realm("qi_kindling_3")), "stones_that_move_you", ["page:teleport"],
      effects=[{"kind": "grant_item", "item": "spirit_stone_shard", "count": 2}])
    u("insight_sites", "Insight sites", all_of(realm("qi_kindling_4")), "listening_to_the_waterfall", [])
    u("contemplate", "Contemplate", all_of(realm("qi_kindling_4")), "listening_to_the_waterfall", [], same_stage_ok=True, toast=False)
    u("technique_slots_4", "More technique slots", all_of(realm("qi_kindling_5")), "two_hands_full", [])
    u("companions", "Companions", all_of(realm("qi_kindling_5")), "two_hands_full", ["page:companions"], same_stage_ok=True)
    u("appraisal", "Appraisal", all_of(realm("qi_kindling_6")), "is_it_real", [], effects=[{"kind": "grant_item", "item": "appraisers_loupe", "count": 1}])
    u("dungeon_keys", "Dungeons", all_of(realm("qi_kindling_7")), "the_caravan_road", [])
    u("auto_refine", "Auto-refine", all_of(realm("qi_kindling_8")), "batch_work", [])
    # S44 / Part 7: the Alchemist Guild's Adept exam and commission board open with Batch Work (Qi Kindling 8).
    u("alchemist_guild", "Alchemist Guild", all_of(realm("qi_kindling_8")), "batch_work", ["page:guild"], same_stage_ok=True,
      effects=[{"kind": "codex", "entry": "alchemist_guild"}])
    # S44: ancient recipes come in pages; a page is enough to begin deducing, a full set teaches it outright.
    u("experiments", "Experiments", all_of(realm("qi_unfurling_1"), unlocked("alchemy")), "", [], same_stage_ok=True, toast=False,
      effects=[{"kind": "codex", "entry": "experiments"}])
    u("cleansing_prep", "Heaven's Cleansing", all_of(realm("qi_kindling_9")), "toward_cleansing_peak", [])

    # Qi Unfurling
    u("technique_page_2", "Ranged Qi and skill page 2", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [])
    u("composure", "Composure", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [], same_stage_ok=True)
    u("retreat_room", "Retreat room", all_of(realm("qi_unfurling_1")), "after_the_cleansing", [], same_stage_ok=True, toast=False)
    u("your_sect", "Your own sect", all_of({"kind": "account_realm", "realm": "qi_unfurling_1"}), "a_hall_of_our_own", ["page:your_sect"], scope="account")
    u("smithing", "Smithing", all_of(realm("qi_unfurling_2")), "the_sect_forge", [], effects=[{"kind": "grant_item", "item": "forge_hammer", "count": 1}])
    u("inheritances", "Inheritances", all_of(realm("qi_unfurling_3")), "the_shrine_surfaces", [])
    u("herb_garden", "Herb garden", all_of(realm("qi_unfurling_4")), "seeds_of_the_valley", [], effects=[{"kind": "codex", "entry": "herb_garden"}])
    u("spirit_animals", "Spirit animals", all_of(realm("qi_unfurling_5")), "a_friend_in_the_reeds", ["hud:pet", "page:spirit_animals"])
    u("technique_slots_8", "Eight technique slots", all_of(realm("qi_unfurling_6")), "full_hands", [])
    u("field_bosses", "Field bosses", all_of(realm("qi_unfurling_7")), "the_riverbed_serpent", [])
    u("taming", "Taming", all_of(realm("qi_unfurling_7")), "calming_the_wild", [], same_stage_ok=True)
    u("tournament", "Tournament", all_of(realm("qi_unfurling_8")), "the_valley_tournament", [])
    u("heart_trial_prep", "Heart Trial preparation", all_of(realm("qi_unfurling_9")), "the_quiet_heart", [])

    # Heart Tempering to Heaven Glimpse
    u("formations", "Formations", all_of(realm("heart_tempering_1")), "lines_in_the_sand", ["page:formations"],
      effects=[{"kind": "grant_item", "item": "formation_kit", "count": 1}])
    # Gap report G2: the Treasure button. Plates and treasures both hold Qi, so the arrays quest teaches it.
    # S47: the first Treasure button comes with "A Treasure in Hand"; the Bright Mirror blueprint with it.
    u("treasures", "Treasures", all_of(realm("heart_tempering_1")), "a_treasure_in_hand", ["hud:treasure_1"],
      effects=[{"kind": "learn_recipe", "recipe": "bright_mirror"}], same_stage_ok=True)
    u("perfect_timing", "Perfect timing", all_of(realm("heart_tempering_1")), "lines_in_the_sand", [], same_stage_ok=True, toast=False)
    # S47 dual loadout: a spare weapon and the Swap button (R).
    # S48 stances (one per weapon family) come with Willow Leaf Parry's lessons; Inner Arts with Qi Unfurling.
    u("stances", "Stances", all_of(realm("qi_kindling_5")), "", [], same_stage_ok=True, toast=False)
    # S48 vows (the Buddhist path): a cultivator steady enough to temper the heart can bind it with a vow.
    u("vows", "Vows", all_of(realm("heart_tempering_1")), "", [], same_stage_ok=True, effects=[{"kind": "codex", "entry": "vows"}])
    u("dual_loadout", "Weapon swap", all_of(realm("heart_tempering_1")), "", ["hud:weapon_swap"], same_stage_ok=True)
    # S47 talisman craft (Qi Kindling 6): Old Scribe Bai on Artisan Row teaches the brush.
    u("talisman", "Talismans", all_of(realm("qi_kindling_6")), "ink_and_paper", ["page:talisman"], same_stage_ok=True)  # v2 Part 8: Talismans and "is it real" both open at QK6
    # S47 natal treasure and the wardrobe (appearance overrides) open at the same stage.
    u("natal", "Natal treasure", all_of(realm("heart_tempering_1")), "", [], same_stage_ok=True)
    # S44 medicinal baths (Part 8: Qi Unfurling 1, retreat rooms): a Bath station and its two recipes.
    u("medicinal_bath", "Medicinal baths", all_of(realm("qi_unfurling_1")), "", [], same_stage_ok=True,
      effects=[{"kind": "learn_recipe", "recipe": "copper_body_bath"}, {"kind": "learn_recipe", "recipe": "marrow_washing_bath"}])
    u("wardrobe", "Wardrobe", all_of(realm("heart_tempering_1")), "", [], same_stage_ok=True, toast=False)
    u("healing", "Healing", all_of(realm("heart_tempering_3")), "the_infirmary", [], effects=[{"kind": "grant_item", "item": "needle_case", "count": 1}])
    u("array_plates", "Array plates", all_of(realm("heart_tempering_5")), "carry_a_wall", [])
    u("spirit_eggs", "Spirit eggs", all_of(realm("heart_tempering_5")), "the_warm_egg", [], same_stage_ok=True)
    u("second_companion", "Second companion", all_of(realm("heart_tempering_6")), "brothers_in_arms", [])
    u("guard_formation", "Guard formation", all_of(realm("heart_tempering_7")), "keep_watch", [])
    u("heart_trial", "The Heart Trial", all_of(realm("heart_tempering_9")), "the_heart_trial", [])
    # S48 Core Forging: at Heart Tempering 9 the elders teach how a core is forged, and the pill for it.
    u("core_forging", "Core Forging", all_of(realm("heart_tempering_9")), "", [], same_stage_ok=True,
      effects=[{"kind": "learn_recipe", "recipe": "heavenly_flame_pill"}, {"kind": "codex", "entry": "core_forging"}])
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
    u("treasure_slot_2", "A second treasure", all_of(realm("spirit_awakening_1")), "a_lake_inside", ["hud:treasure_2"], same_stage_ok=True)
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
    # Act II · Phase C (S20/S21): the auction house after the Hall of Nine, clans at Sage 2.
    u("auction_house", "Auction house", all_of(realm("sage_1"), qdone("nine_seats")), "going_once", [], same_stage_ok=True)
    u("clans", "Clans", all_of(realm("sage_2"), qdone("the_canyon_toll")), "ironroot_blood", [], same_stage_ok=True)
    # S09 secret arts that come with a realm (the quest-taught ones come from the mentor).
    for art, rk, label in [("appraisal_eye", "qi_kindling_6", "Appraisal Eye"), ("breath_control", "qi_unfurling_3", "Breath Control"),
                           ("wind_blink", "spirit_awakening_5", "Wind Blink")]:
        u(art, label, all_of(realm(rk)), "", [], effects=[fx("learn_secret_art", art=art)], same_stage_ok=True)
    # S43 movement arts: a guided quest offers each, and the art is usable from its acceptance.
    # The art's own toast (with its how-to) shows when it is learned, so these unlocks stay quiet.
    u("glide", "Falling Leaf Glide", all_of(realm("qi_kindling_3")), "leaf_on_the_wind", [], same_stage_ok=True, toast=False)
    u("air_dash", "Swallow Dart", all_of(realm("qi_kindling_7")), "swallow_dart", [], same_stage_ok=True, toast=False)
    u("double_jump", "Cloud Ladder Step", all_of(realm("qi_unfurling_6")), "cloud_ladder", [], same_stage_ok=True, toast=False)
    u("wall_step", "Wall-Step", all_of(realm("heart_tempering_4")), "between_two_walls", [], same_stage_ok=True, toast=False)
    # Act II · Phase E (Part 4): Sage 3 opens the Starsea crafts and the will to survive out there; Sage 1 paired cultivation;
    # Sage Sovereign 1 upgrades the training sect's token.
    u("star_charting", "Star charts", all_of(realm("sage_3"), qdone("ironroot_blood")), "a_chart_of_ones_own", [], same_stage_ok=True)
    u("shipwright", "Vessel building", all_of(realm("sage_3"), qdone("ironroot_blood")), "keel_and_ward", [], same_stage_ok=True)
    u("starsea", "Starsea survival", all_of(realm("sage_3"), qdone("ironroot_blood")), "", [], same_stage_ok=True)
    u("paired_cultivation", "Paired cultivation", all_of(realm("sage_1"), qdone("sage")), "two_breaths", [], same_stage_ok=True)
    u("elder_token", "Elder's token", all_of(realm("sage_sovereign_1"), {"kind": "has_training_sect", "value": True}), "",
      [], effects=[{"kind": "upgrade_sect_token"}, {"kind": "send_mail", "template": "elder_token"}], same_stage_ok=True)
    # Act II (S18): the zone's attunement jades open once the broker has explained the storms.
    u("storm_ward", "Storm Ward attunement", all_of(realm("heaven_glimpse_3"), qdone("a_sky_full_of_toll_roads")), "storm_in_the_blood", [],
      same_stage_ok=True)
    entries("unlocks", U)
    return U


# ---------------------------------------------------------------------------------------------
# Quests
Q = []


def o(kind, text, count=1, **kw):
    d = {"kind": kind, "text": text, "count": count}
    d.update(kw)
    return d


# Gap report G1 · the karma ledger: deeds that ease another's lot earn merit on completion. Their merit, alignment
# and Fame are in karma.json (relations.py, S49); the quest reward names the deed.
from relations import QUEST_DEEDS as KARMA_QUESTS


def quest(qid, name, kind, giver, objectives, rewards=(), hand_in=None, offer=(), complete=(), progress=(), **kw):
    rewards = list(rewards)
    if qid in KARMA_QUESTS:
        rewards.append({"kind": "deed", "deed": qid})
    d = {"id": qid, "name": name, "kind": kind, "giver": giver, "hand_in": giver if hand_in is None else hand_in,
         "marker": kw.pop("marker", "gold" if kind in ("main", "prologue") else "blue"),
         "objectives": list(objectives), "rewards": rewards}
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
        offer=["My kite! It flew onto the inn roof! The big one!", "Climb the ladder on the Village Hall, then jump across. Or jump from the stall awning!"],
        progress=["Ladder, hall roof, then jump onto the inn. You can do it!"],
        complete=["My kite! You're the best! Here, I saved this rice ball. It's only a bit squashed."])
    quest("the_lost_ladle", "Aunt Ping's Ladle", "side", "aunt_ping", [
        o("deliver", "Fetch Aunt Ping's ladle from the hut roof", item="aunt_pings_ladle"),
    ], [item("rice_ball", 2), taels(15)], requires=all_of(qdone("the_runaway_kite")), target_room="lf_village", chapter="prologue",
        giver_any=["aunt_ping"], hand_in_any=["aunt_ping"],
        offer=["The gulls took my ladle again. It's on the hut roof, glinting at me.", "There's a ladder by the door. Mind the edge."],
        complete=["My ladle! I'd have made soup with a spoon for a week."])
    quest("mas_delivery", "Ma's Delivery", "prologue", "old_ma", [
        o("sell_item", "Sell the Old Net to Old Ma", item="old_net"),
        o("buy_item", "Buy Rice Balls", 2, item="rice_ball"),
    ], [taels(30)], requires=after_lu, target_room="lf_old_ma_store", chapter="prologue", marker="blue",
        on_accept=[taels(10)],
        offer=["Aunt Ping's old net has been in my way for a month. It's under the shelf. Sell it back to me, fair and square.",
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
        o("use_system", "Climb a roof and Plunge to the practice ground", 1, system="plunge"),
    ], [fx("sect_rank", rank="outer_disciple"), fx("add_contribution", amount=50)], offered_by_unlock=True, chapter="1", giver_any=M, hand_in_any=M,
        target_room="ja_pavilion_rooftops", on_accept=[fx("learn_secret_art", art="plunge")],
        offer=["Outer disciples are chosen by their fists. Win three spars at the practice posts.",
               "And learn to come down hard. From any height, pull down and strike: we call it Plunge. Show me once, from a roof."],
        complete=["Outer Disciple. You'll get a proper robe soon."])
    # S43 movement arts (Qi Kindling 3 and 7): each guided quest teaches its art on acceptance.
    quest("leaf_on_the_wind", "Leaf on the Wind", "guided", "elder_hu", [
        o("reach_room", "Go to the Falls Pool", room="cf_falls_pool"),
        o("use_system", "Climb the vine and glide over the pool", 2, system="glide"),
    ], [taels(60)], offered_by_unlock=True, chapter="qk3", same_stage_ok=True, giver_any=M, hand_in_any=M, target_room="cf_falls_pool",
        on_accept=[fx("learn_secret_art", art="falling_leaf_glide")],
        offer=["Watch a leaf fall from Crane Falls. It never hurries. Hold your breath, hold the jump, and fall like that.",
               "Climb the vine beside the falls and glide over the pool. The spray will carry you if you let it."],
        complete=["You came down like a leaf, not a stone. Good."])
    quest("swallow_dart", "Swallow Dart", "guided", "jade_librarian", [
        o("use_system", "Dart through the air three times", 3, system="air_dash"),
    ], [taels(100)], offered_by_unlock=True, chapter="qk7", same_stage_ok=True, giver_any=LIBRARIANS, hand_in_any=LIBRARIANS,
        on_accept=[fx("learn_secret_art", art="swallow_dart")],
        offer=["The first floor keeps a slim scroll: Swallow Dart. A swallow turns in the air without touching anything.",
               "Jump, then tap Evade. You will hang for a breath and dart ahead. Three times, and mind the shelves."],
        complete=["Once per leap, remember. Even swallows land."])
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
        complete=["Here's a drying rack for herbs. Steam them on it and their pills poison you less; soak them in rice wine and the pills bite harder.",
                  "Set it up by any garden bed."])
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
                                                             "bow": "pinning_arrow", "heavy_sabre": "thunder_dao_arc",
                                                             "fan": "returning_crane_fan", "flute": "reed_song"})],
        offer=["Qi Unfurling. Your Qi can fly now. Send it at a target ten times."],
        complete=["Inner Disciple. A retreat room is yours; the door is past the mission hall."])
    quest("ink_and_paper", "Ink and Paper", "guided", "old_scribe_bai", [
        o("craft", "Write a Flame Talisman at Old Scribe Bai's table", recipe="flame_talisman", craft="talisman"),
    ], [fx("learn_recipe", recipe="thunder_talisman"), fx("learn_recipe", recipe="veil_talisman"), fx("learn_recipe", recipe="binding_talisman"),
        fx("learn_recipe", recipe="beast_blood_ink"), fx("learn_recipe", recipe="spirit_paper"), fx("learn_recipe", recipe="revival_talisman"),
        fx("learn_recipe", recipe="lightning_rod_talisman")], offered_by_unlock=True, chapter="qk6", giver_any=["old_scribe_bai"], hand_in_any=["old_scribe_bai"],
        on_accept=[fx("learn_recipe", recipe="flame_talisman"), fx("learn_recipe", recipe="iron_wall_talisman"), fx("learn_recipe", recipe="wind_step_talisman"),
                   item("talisman_paper", 3), item("cinnabar", 3), item("ember_pepper", 1)],
        offer=["Paper, cinnabar and one clean stroke. That is all a talisman is, and all it ever will be.",
               "Trace the character without lifting your hand. Smooth and unhurried makes a strong one; a broken stroke spoils the paper."],
        complete=["Not bad for a first. Here: the rest of my book. Beast-blood ink for the stronger ones; spirit paper for anything that must hold."])
    quest("the_sect_forge", "The Sect Forge", "guided", "jade_smith", [
        o("craft", "Forge a Common weapon", craft="smithing"),
        o("use_system", "Enhance it to +1", system="enhance"),
    ], [fx("learn_recipe", recipe="jadeiron_jian")], offered_by_unlock=True, chapter="qu2", giver_any=SMITHS, hand_in_any=SMITHS,
        on_accept=[fx("learn_recipe", recipe="iron_jian"), fx("learn_recipe", recipe="iron_spear"), fx("learn_recipe", recipe="iron_gauntlets")],
        offer=["A disciple with Qi in their hands can work the sect forge. Take this hammer. Forge something, then make it better."],
        complete=["An Earth blueprint. Don't waste the Jadeiron."])
    quest("seeds_of_the_valley", "Seeds of the Valley", "guided", "jade_gardener", [
        o("use_system", "Plant a seed in three garden beds", 3, system="plant_seed"),
    ], [item("willow_moss", 5), item("spring_water", 3)], offered_by_unlock=True, chapter="qu4", giver_any=["jade_gardener", "cloud_gardener"],
        hand_in_any=["jade_gardener", "cloud_gardener"], on_accept=[fx("grant_item", item="willow_moss_seed", count=3)],
        offer=["Three willow moss seeds, three beds. Plant them.",
               "Granny Liu sells the common seeds. A perfect harvest shakes rarer ones loose, and the old inheritances hide the rarest."],
        complete=["You've got green hands. Water them with spring water and they grow while you're away.",
                  "A Qi spring gives three bottles a day. Here are three to start."])
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
    # S43 movement-art quests (Part 8 guided unlock quests).
    quest("cloud_ladder", "Cloud Ladder", "guided", "jade_librarian", [
        o("use_system", "Double jump to three high ledges", 3, system="double_jump"),
    ], [taels(80)], offered_by_unlock=True, chapter="qu6", same_stage_ok=True, giver_any=LIBRARIANS, hand_in_any=LIBRARIANS,
        on_accept=[fx("learn_secret_art", art="cloud_ladder_step")],
        offer=["This scroll is older than the sect: Cloud Ladder Step. Press off the air itself, once, at the top of a jump.",
               "Try it now. Three ledges you could not reach before, and tell me what the valley looks like from there."],
        complete=["Now you understand why the old masters built their halls so high."])
    quest("between_two_walls", "Between Two Walls", "guided", "elder_hu", [
        o("use_system", "Climb the Echo Cliffs shaft with Wall-Step", 3, system="wall_step"),
        o("kill", "Defeat Mist Vultures on the top tier", 3, enemy="mist_vulture"),
    ], [taels(120)], offered_by_unlock=True, chapter="ht4", same_stage_ok=True, giver_any=MENTORS, hand_in_any=MENTORS, target_room="wg_echo_cliffs",
        on_accept=[fx("learn_secret_art", art="wall_step")],
        offer=["Two walls close together are a ladder, if you are light enough. Push into one, kick, and reach for the other.",
               "Climb the shaft at the Echo Cliffs. The vultures nest at the top; clear three."],
        complete=["Three kicks and you were above them. Good. Height is a weapon."])
    quest("a_treasure_in_hand", "A Treasure in Hand", "guided", "elder_hu", [
        o("use_system", "Ring the Practice Bell in a fight", 3, system="treasure"),
    ], [taels(60)], offered_by_unlock=True, chapter="ht1", same_stage_ok=True, giver_any=M, hand_in_any=M,
        on_accept=[item("practice_bell", 1)],
        offer=["A cultivator carries more than a blade. Take this Practice Bell; it sits in your Treasure button.",
               "Ring it three times when foes press close. Feel what a treasure costs you."],
        complete=["Keep the bell. Better treasures wait in the valley: drowned bells, jade pagodas, mirrors that throw back arrows."])
    quest("the_infirmary", "The Infirmary", "guided", "jade_physician", [
        o("use_system", "Treat injured disciples", 3, system="treat_patient"),
    ], [fx("add_contribution", amount=100)], offered_by_unlock=True, chapter="ht3", giver_any=PHYSICIANS, hand_in_any=PHYSICIANS,
        offer=["Needles, pills and a gentle hand. Three patients."], complete=["Healing is cultivation turned outward."])
    quest("carry_a_wall", "Carry a Wall", "guided", "jade_formation_elder", [
        o("craft", "Craft an Array Plate", recipe="array_plate"),
    ], [item("blank_plate", 3)], offered_by_unlock=True, chapter="ht5", same_stage_ok=True, giver_any=FORMATION_ELDERS, hand_in_any=FORMATION_ELDERS,
        on_accept=[fx("learn_recipe", recipe="array_plate"), fx("learn_recipe", recipe="killing_array_plate"),
                   fx("learn_recipe", recipe="binding_array_plate"), item("blank_plate", 1), item("formation_stone", 1)],
        offer=["A formation you can carry. Etch one plate."], complete=["Take these blanks."])
    quest("skipping_stones", "Skipping Stones", "side", "hermit_yao", [
        o("use_system", "Sprint across the pond under the stilt house", 1, system="water_skimming"),
        o("collect", "Pick the Mist Lotus on the pond's rock", item="mist_lotus"),
    ], [taels(300)], requires=all_of(realm("qi_unfurling_8")), target_room="rm_hermit_stilt_house",
        on_accept=[fx("learn_secret_art", art="water_skimming")],
        offer=["A stone skips if it is fast and flat. So can you. Sprint at the pond and do not stop.",
               "A Mist Lotus grows on the rock in the middle. Stop on the water and you'll be fishing yourself out."],
        complete=["Wet to the knees only. The otters are impressed."])
    quest("the_warm_egg", "The Warm Egg", "guided", "hermit_yao", [
        o("use_system", "Incubate a spirit egg", system="egg_incubated"),
    ], [item("spirit_egg", 1)], offered_by_unlock=True, chapter="ht5", same_stage_ok=True, on_accept=[item("spirit_egg", 1)],
        offer=["An egg, warm and humming. Keep it close."], complete=["Another life in your care."])
    quest("brothers_in_arms", "Brothers in Arms", "guided", "elder_hu", [
        o("choose_companion", "Choose a second companion"),
        o("reach_room", "Clear Echo Cliffs together", room="wg_echo_cliffs"),
    ], [fx("learn_technique", technique="still_water_focus")], offered_by_unlock=True, chapter="ht6", giver_any=M, hand_in_any=M,
        offer=["The gorge is too much for two. Take a second companion."], complete=["Three together. Good."])
    quest("keep_watch", "Keep Watch", "guided", "jade_formation_elder", [
        o("breakthrough", "Break through a stage inside a guard formation", formation="guard"),
    ], [item("fuel_crystal_low", 2)], offered_by_unlock=True, chapter="ht7", giver_any=FORMATION_ELDERS, hand_in_any=FORMATION_ELDERS,
        offer=["A guard formation around you while you break through: nothing interrupts, nothing surprises."], complete=["Safe and stronger."])
    quest("the_heart_trial", "The Heart Trial", "main", "elder_hu", [
        o("pass_event", "Win the Trial of Reflections", event="heart_trial"),
    ], [fx("codex", entry="heart_trial")], offered_by_unlock=True, chapter="6", giver_any=M, hand_in_any=M,
        on_accept=[item("elder_hus_talisman", 1)],
        offer=["Step into the circle on my peak. What comes out of the mirror is you. Beat it.",
               "Take this: Elder Hu's Heaven-Splitting Palm, folded into paper. Three charges. Set it in a Treasure button and keep it for the worst moment."],
        complete=["You looked yourself in the eye and didn't blink. Cloud Stride awaits."])
    quest("wings_of_cloud", "Wings of Cloud", "main", "elder_hu", [
        o("use_system", "Take to the air: hold Jump as you start to fall", system="flight"),
        o("reach_room", "Reach the Cliff Faces", room="cc_cliff_faces"),
        o("kill", "Defeat Cloudwing Cranes", 3, enemy="cloudwing_crane"),
    ], [fx("codex", entry="flight")], offered_by_unlock=True, chapter="7", giver_any=M, hand_in_any=M,
        offer=["Cloud Stride. Your Qi can carry you. The cranes of the cliffs will teach you the rest."],
        complete=["The sky is a road now."])
    quest("riding_the_wind", "Riding the Wind", "guided", "hermit_yao", [
        o("bond_pet", "Bond with your spirit animal again"),
        o("use_system", "Ride it: Spirit Animals, choose Mount", system="mount"),
    ], [item("flying_sword_vessel", 1)], offered_by_unlock=True, chapter="cs1", same_stage_ok=True, offer=["A big enough friend can carry you."],
        complete=["Hold on tight.", "And when there is no friend, here: an old sword that remembers how to fly. Stand on the flat of it."])
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
    ], [item("cloud_talisman", 1), item("verdant_dew_vial", 1), fx("learn_technique", technique="mirror_mind_spike")], offered_by_unlock=True, chapter="sa1", giver_any=M, hand_in_any=M,
        offer=["Your soul has a lake now. Pulse it outward: Spirit Sense."],
        complete=["The world has more in it than eyes see.", "Take this vial too. It gathers a drop of dew a day. Pour it on your garden and the herb there grows a century."])
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
    ], [fx("learn_secret_art", art="lotus_heart_breathing"), fx("learn_technique", technique="soul_lantern_ward")], offered_by_unlock=True, chapter="sa5", giver_any=M, hand_in_any=M,
        offer=["Beat my best disciple and I'll teach you personally."],
        complete=["My personal disciple. My secret art is yours, and the cave behind the pagoda is your abode."])
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
    # S49 master inheritance: before the valley lets you go, your master goes into closed-door cultivation and passes
    # on the one art never written down.
    quest("the_elders_last_lesson", "The Elder's Last Lesson", "side", "elder_hu", [
        o("meditate_seconds", "Sit with your master one last time", 60),
    ], [fx("master_legacy"), item("thousand_year_lingzhi", 1), fx("codex", entry="lifespan")], giver_any=M, hand_in_any=M, requires=all_of(qdone("the_mentors_gift"), qdone("beyond_the_valley")),
        chapter="10",
        offer=["You are leaving the valley. So am I, in my way: I am going into closed-door cultivation, and I do not know when I will come out.",
               "Sit with me once more. There is one thing I never wrote down."],
        complete=["Breathe as I breathe. There. That is all of it, and now it is yours.",
                  "And take this. I kept it a hundred years for a longer life. Where I am going, years will not matter.",
                  "Go. If the heavens are kind, we will meet above the clouds."])
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
    ], [fx("codex", entry="riverbreath_inheritance"), item("cloudtop_orchid_seed", 2)], requires=all_of(qdone("lus_handwriting")), chapter="5", giver_any=M, hand_in_any=M,
        target_room="ds_scripture_well",
        offer=["Lu left more than words down there. An inheritance tests the one who claims it.",
               "Stand in the stone ring by the well and hold while the drowned rise. Breathe with the river."],
        complete=["The well accepted you. Now only the Abbot stands between you and Lu's method."])
    quest("the_drowned_abbot", "The Drowned Abbot", "main", "elder_hu", [
        o("kill", "Defeat the Drowned Abbot", enemy="drowned_abbot"),
    ], [item("riverbreath_scroll", 1), item("soulbell_flower_seed", 2)], requires=all_of(qdone("the_riverbreath_trial")), chapter="5", giver_any=M, hand_in_any=M,
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


def spirit_stones(n):
    return {"kind": "grant_currency", "currency": "spirit_stone", "amount": n}


def act2_quests():
    """Act II · chapter 11, Beyond the Gate (docs/act2_design.md)."""
    quest("through_the_gate", "Through the Gate", "main", "warden_cao", [
        o("reach_room", "Step through the Ascension Gate", room="ae_landing"),
        o("talk_to", "Speak with the toll warden on the Arrival Terrace", npc="warden_cao"),
    ], [spirit_stones(20), fx("codex", entry="cloudgate_port")], hand_in="", auto_accept=True, requires=all_of(qdone("the_ascension_gate"), realm("heaven_glimpse_3")),
        chapter="11", target_room="ae_landing",
        complete=["Valley-born, by the mud on your boots. No toll for your first step. There will be for every other.",
                  "Welcome to Cloudgate Port, gateway of the Nine Peaks Alliance."],
        next="a_sky_full_of_toll_roads")
    quest("a_sky_full_of_toll_roads", "A Sky Full of Toll Roads", "main", "warden_cao", [
        o("talk_to", "Meet the Alliance factor in the Port Market", npc="factor_ruan"),
        o("talk_to", "Find the free broker at the Wayfarers' Inn", npc="broker_mu"),
    ], [spirit_stones(30), fx("codex", entry="nine_peaks_alliance")], hand_in="broker_mu", requires=all_of(qdone("through_the_gate"), realm("heaven_glimpse_3")), chapter="11",
        target_room="ae_port_market",
        offer=["No papers, no road. The Factor sells Alliance goods in the market. The broker at the inn sells... other things.",
               "Talk to both. Then decide what kind of cultivator you mean to be up here."],
        complete=["The Factor told you the price of a road. I'll tell you the price of the sky: your blood.",
                  "The plains' storms pull Qi out of anyone who hasn't attuned to them. Sit. Let me show you."],
        next="storm_in_the_blood")
    quest("storm_in_the_blood", "Storm in the Blood", "main", "broker_mu", [
        o("use_system", "Raise your Storm Ward jades (Character, Attunement tab)", 4, system="attune_jade"),
        o("kill", "Hunt Spark Weasels on the Stormgrass Verge", 6, enemy="spark_weasel"),
        o("collect", "Gather Storm Shards", 10, item="storm_shard", consume=False),
    ], [spirit_stones(40), item("storm_blood_pill", 2), fx("codex", entry="storm_ward")], offered_by_unlock=True, chapter="11",
        target_room="tp_stormgrass_verge", on_accept=[item("storm_shard", 12)],
        offer=["Four jades, cut from storm-glass. Carry them and feed them the shards the storm leaves in its beasts.",
               "The more you feed them, the less the storm feeds on you. Start on the Verge. Weasels. Small, quick, angry."],
        complete=["See? You flinch less. Keep feeding the jades; the land further out asks for more.",
                  "One more thing, free: the alchemist in the Condensing Hall can make a Sage of you. She'll want thunder."],
        next="horns_for_the_furnace")
    quest("horns_for_the_furnace", "Horns for the Furnace", "main", "alchemist_fen", [
        o("collect", "Bring Thunderhorn horns from the Flats", 3, item="thunder_horn"),
    ], [item("sage_condensing_pill", 1), fx("learn_recipe", recipe="sage_condensing_pill"), spirit_stones(40)],
        requires=all_of(qdone("storm_in_the_blood"), realm("heaven_glimpse_3")),
        chapter="11", target_room="tp_thunderhorn_flats",
        offer=["Heaven Glimpse 3, and you want to be a Sage. Everyone does.",
               "The condensing needs thunder. Three thunderhorn horns from the Flats. I'll press them into your pill."],
        complete=["There. Swallow it here, where the Qi is thick. Not in a field with a rhino watching.",
                  "And a word from an old woman: the Drowned Abbot sealed a nine-dragon cauldron in his vault. If you never went back for it, go."],
        next="sage")
    quest("sage", "Sage", "main", "alchemist_fen", [
        o("reach_realm", "Break through to Sage 1 (third-grade purity, the pill, a land that can hold you)", realm="sage_1"),
    ], [spirit_stones(60), fx("codex", entry="sage_qi")], requires=all_of(qdone("horns_for_the_furnace"), realm("heaven_glimpse_3")), chapter="11",
        target_room="ae_condensing_hall",
        offer=["Purity of the third grade, the pill, and a land that can hold you. The Expanse can.",
               "Sit on the mat. Breathe until the True Qi turns to light."],
        complete=["Sage Qi. Feel how it moves? Like thunder that learned its manners.",
                  "The Nine Peaks will want your name now. So will people who are worse than the Alliance."])


def act2_chapter12():
    """Act II · chapter 12, The Grey Pilgrim (Sage 1-2)."""
    quest("shards_for_sale", "Shards for Sale", "main", "broker_mu", [
        o("talk_to", "Ask Old Suo about the grey buyer", npc="herder_suo"),
        o("interact_object", "Follow the buyer's tracks across the Lightning Scar", 3, type="inspect", room="tp_lightning_scar"),
        o("talk_to", "Catch up with the stranger on Frostpine Climb", npc="grey_pilgrim"),
    ], [spirit_stones(60), item("storm_shard", 15), fx("codex", entry="grey_pilgrim")], requires=all_of(qdone("sage"), realm("sage_1")),
        chapter="12", target_room="tp_herders_camp",
        offer=["Someone is buying Hollow shards across the Expanse. Grey robes, no shadow at noon.",
               "The herders have seen him on the plains. Old Suo misses nothing. Start there."],
        complete=["He let you catch him. That's worse than if he'd run.",
                  "If he went up into the snow, only one person up there would have seen him: the hermit of Rimefrost."],
        next="frost_and_silence")
    quest("frost_and_silence", "Frost and Silence", "main", "broker_mu", [
        o("reach_room", "Find the hermit's cave on Rimefrost Summit (Spirit Sense shows hidden ways)", room="rf_hermits_ice_cave"),
        o("talk_to", "Speak with Hermit Shuang", npc="hermit_shuang"),
        o("meditate_seconds", "Sit in silence in the Ice Cave", 90),
    ], [spirit_stones(80), item("frost_lotus", 2), fx("codex", entry="rimefrost_hermit")], requires=all_of(qdone("shards_for_sale")),
        hand_in="hermit_shuang", chapter="12", target_room="rf_rimefrost_summit",
        offer=["The hermit lives somewhere on Rimefrost Summit. People who look for him don't find him.",
               "People who stop looking sometimes do."],
        complete=["...You can sit still. Good. Most who climb up here only want to talk.",
                  "The grey one passed a month ago. He stopped at the lake. The lake remembers everything. Ask it."],
        next="the_mirror_remembers")
    quest("the_mirror_remembers", "The Mirror Remembers", "main", "hermit_shuang", [
        o("reach_room", "Take the sky-ship to Mirrorwater Lake and reach the Lake Shrine", room="ml_lake_shrine"),
        o("set_flag", "Look into the shrine's bronze mirror", flag="mirror_vision_seen"),
        o("kill", "Silence the Thousand-Eye Toad in Toad's Hollow", enemy="thousand_eye_toad"),
    ], [spirit_stones(120), item("storm_shard", 25), fx("codex", entry="lu_crossing"), fx("set_flag", flag="chapter_12_done")],
        requires=all_of(qdone("frost_and_silence"), realm("sage_2")), hand_in="", chapter="12", target_room="ml_lake_shrine",
        offer=["The mirror at the Lake Shrine shows what the lake has seen. The toad in the hollow drinks the reflections.",
               "Look into the mirror. Then quiet the toad, or the lake will forget everything it knows."],
        complete=["In the mirror: the grey one kneeling at the shore, feeding Hollow shards to the water. And behind him, older,",
                  "a young ferryman with a river-green token at his belt. Lu. The lake remembered him too."])


def act2_chapter13():
    """Act II · chapter 13, The Nine Peaks (Sage 2-3): a seat or the free road, the canyons, the Ironroot."""
    quest("nine_seats", "Nine Seats", "main", "dockmaster_fu", [
        o("reach_room", "Take the sky-ship to Nine Peaks and enter the Hall of Nine", room="np_hall_of_nine"),
        o("talk_to", "Hear the Alliance envoy", npc="envoy_lanshi"),
        o("set_flag", "Take an Alliance seat, or keep the free road", flag="path_alliance", alt_flag="path_independent"),
    ], [spirit_stones(100), fx("codex", entry="nine_seats")], requires=all_of(qdone("the_mirror_remembers"), realm("sage_2")),
        hand_in="elder_zhong", chapter="13", target_room="np_hall_of_nine",
        offer=["An invitation came with the morning ship. Nine Peaks wants to see you. They see everyone who crosses, sooner or later.",
               "The Alliance will offer you a seat. The broker will tell you why you shouldn't take it. Both are right."],
        complete=["Whichever you chose, choose it every day. The Hollow shards are coming from somewhere inside the Expanse.",
                  "The canyons east of here are where they pass. Go and see who is paying the tolls."],
        next="the_canyon_toll")
    quest("going_once", "Going Once", "guided", "auctioneer_tong", [
        o("use_system", "Place a bid at the Auction Pavilion", system="auction_bid"),
    ], [spirit_stones(20)], offered_by_unlock=True, chapter="13", target_room="np_auction_pavilion",
        offer=["First time at the block? Pick a lot, name a price. The other bidders will tell you if you're wrong."],
        complete=["There. Win or lose, you're a bidder now. The Pavilion opens new lots every dawn."])
    quest("the_canyon_toll", "The Canyon Toll", "main", "elder_zhong", [
        o("talk_to", "Ask the tollkeeper at the Canyon Mouth who pays in shards", npc="tollkeeper_bai"),
        o("kill", "Break the veiled brigands' hold on the canyon", 6, enemy="canyon_brigand"),
        o("reach_room", "Cross the Windbridge to Ironroot Hold", room="ir_hold_gate"),
    ], [spirit_stones(140), item("storm_shard", 30), fx("codex", entry="gale_canyons")], requires=all_of(qdone("nine_seats"), realm("sage_2")),
        hand_in="ironroot_warden", chapter="13", target_room="gc_canyon_mouth",
        offer=["Someone pays the canyon toll in Hollow shards. The tollkeeper takes them because they spend like stones.",
               "Follow the shards east. The veiled brigands carry them for someone."],
        complete=["You crossed the Windbridge with brigand blood on your boots. The Hold has been watching them too.",
                  "The Matriarch will want to meet you. She doesn't want to meet many."],
        next="ironroot_blood")
    quest("ironroot_blood", "Ironroot Blood", "main", "ironroot_warden", [
        o("win_spar", "Pass the warden's test of root", opponent="ironroot_warden"),
        o("talk_to", "Stand before the Matriarch", npc="matriarch_tie"),
        o("set_flag", "Honour the ancestral tablets in the Ancestor Hall", flag="tablets_honoured"),
    ], [spirit_stones(160), item("ironroot_token", 1), fx("set_flag", flag="clan_ironroot"), fx("grant_title", title="ironroot_kin"),
        fx("codex", entry="ironroot_clan")], offered_by_unlock=True, hand_in="matriarch_tie", chapter="13", target_room="ir_hold_gate",
        offer=["Kin is not given at the gate. Show me your root holds, then the Matriarch decides."],
        complete=["The ancestors did not object. That is as close to a welcome as they give.",
                  "You are Ironroot now, in the Hold and on the roads. Our forge is yours. So are our quarrels."])


def act2_chapter14():
    """Act II · chapter 14, Sunscar (Sage 3 - Sage Sovereign 1): across the desert, into the tomb, and the seal."""
    quest("glass_and_bone", "Glass and Bone", "main", "matriarch_tie", [
        o("reach_room", "Follow the desert road past the Clan Hearth to the Oasis of Bones", room="sd_oasis_of_bones"),
        o("kill", "Clear the Sandstorm Scorpions from the caravan road", 6, enemy="sandstorm_scorpion"),
        o("talk_to", "Ask the bone-reader about the Pilgrim's caravan", npc="bone_reader_xiu"),
    ], [spirit_stones(180), item("storm_shard", 20), fx("codex", entry="sunscar_desert")],
        requires=all_of(qdone("ironroot_blood"), realm("sage_3")), hand_in="bone_reader_xiu", chapter="14", target_room="sd_glass_dunes",
        offer=["Our scouts saw the Grey Pilgrim's caravan turn south into the Sunscar. Nobody goes there for trade anymore.",
               "Take the desert road past the Hearth. Find the Oasis of Bones. Its diviner sees what the sand hides."],
        complete=["A grey man with no shadow, buying water and asking about the tomb? The bones spoke of him before you did.",
                  "He wants the sun seal. The Tomb King took it into the dark with him, three thousand years ago."],
        next="the_sealed_gate")
    quest("the_sealed_gate", "The Sealed Gate", "main", "bone_reader_xiu", [
        o("collect", "Cut the pieces of the sun seal's key out of the Dune Worms of the Worm Sea", 3, item="sun_seal_shard", consume=True),
        o("reach_room", "Find the Sealed Gate beyond the Worm Sea", room="ts_sealed_gate"),
        o("set_flag", "Fit the pieces to the gate and read its inscription", flag="tomb_gate_opened"),
    ], [spirit_stones(200), item("storm_shard", 20), item("sovereign_settling_pill", 1), fx("codex", entry="tomb_of_sunscar")],
        requires=all_of(qdone("glass_and_bone")), hand_in="bone_reader_xiu", chapter="14", target_room="sd_worm_sea",
        offer=["The gate answers a key of gold and jade, and the worms swallowed that key in pieces when the tomb was sealed.",
               "Three pieces. Then read the inscription on the gate, if your eyes can hold it. It is written for scholars, not thieves."],
        complete=["The doors are open? Then do not go in. Not yet. He was a Sage Sovereign, and a Sage who walks into his hall joins his guard.",
                  "Take this pill for after. First, become what he was."],
        next="sovereign")
    quest("the_tomb_king", "The Tomb King", "main", "bone_reader_xiu", [
        o("reach_room", "Pass the Hall of Sand Kings into the Mirror Crypt", room="ts_mirror_crypt"),
        o("set_flag", "Find what Lu left in the crypt", flag="journal_tomb"),
        o("kill", "Face the Tomb King of Sunscar on his throne", 1, enemy="tomb_king"),
        o("collect", "Take up the sun seal", item="sunscar_seal", consume=False),
        o("set_flag", "Keep the seal from the Grey Pilgrim", flag="seal_kept", alt_flag="tomb_resealed"),
    ], [spirit_stones(300), item("sovereign_settling_pill", 2), fx("codex", entry="tomb_king")],
        requires=all_of(qdone("sovereign"), realm("sage_sovereign_1")), hand_in="bone_reader_xiu", chapter="14", target_room="ts_sealed_gate",
        offer=["Now you can go in. The King sealed himself in with the seal. Whoever holds it can open what the Hollow keeps shut.",
               "The grey man will be waiting on the stairs. He always is."],
        complete=["You came back, and the Pilgrim did not come back with you. The bones say that is enough for today.",
                  "Lu's page... he stood where you stood, and he walked away without the seal. You chose your own way. Good."])
    quest("sovereign", "Sovereign", "main", "bone_reader_xiu", [
        o("reach_realm", "Break through to Sage Sovereign 1 (a full Sage Qi reserve and one Dao at Adaptation)", realm="sage_sovereign_1"),
    ], [spirit_stones(250), fx("codex", entry="sage_sovereign")],
        requires=all_of(qdone("the_sealed_gate"), realm("sage_3")), chapter="14", target_room="sd_oasis_of_bones",
        offer=["The Tomb King was a Sage Sovereign. His land still holds the Qi for it. Fill your reserve and let one Dao adapt to you.",
               "Then sit by the water and break through. The Settling Pill will hold the new stage steady."],
        complete=["Sage Sovereign. The sand bends a little when you breathe now. Did you notice?",
                  "The Pilgrim noticed too. Whatever he serves has been waiting for someone like you to come this far."],
        next="the_tomb_king")


def act2_chapters_15_16():
    """Act II · chapter 15, Pirates of the Starsea (SS1-2), and chapter 16, The Presence Trial (SS3)."""
    quest("gus_ledger", "Gu's Ledger", "main", "auctioneer_tong", [
        o("talk_to", "Ask Broker Mu who sells pages of a valley ledger", npc="broker_mu"),
        o("talk_to", "Ask Navigator Sun at the Shipwrights' Yard about the Starsea", npc="navigator_sun"),
    ], [spirit_stones(200), item("sky_ink", 4), fx("codex", entry="starsea")],
        requires=all_of(qdone("the_tomb_king"), realm("sage_sovereign_1")), hand_in="navigator_sun", chapter="15", target_room="ae_shipyard",
        offer=["A lot came in this morning that I would not sell: one page of a smuggler's ledger. Valley family names, and what each paid him.",
               "The seller fled on a skiff with no flag, out toward the Starsea. Your valley's names. I thought you would want to know."],
        complete=["The Skyport Wreck. Pirates of the comet sails nest there now, where the old port broke on the edge of the Starsea.",
                  "Nobody walks there. You sail, or you stay. I can teach you to chart the way; Lao can build you something to sail in."],
        next="the_skyport_wreck")
    quest("the_skyport_wreck", "The Skyport Wreck", "main", "navigator_sun", [
        o("collect", "Chart the Wreck Run at Navigator Sun's table", item="star_chart_wreck", consume=False),
        o("collect", "Build a vessel on Shipwright Lao's slipway", item="cloud_skiff", consume=False),
        o("reach_room", "Sail the Wreck Run to the Skyport Wreck", room="sw_broken_pier"),
        o("collect", "Take back the ledger pages the pirates carry", 3, item="ledger_page", consume=True),
        o("set_flag", "Find the seller on the Pirate Deck", flag="gu_freed", alt_flag="gu_left"),
        o("collect", "Keep the Black Ledger", item="black_ledger", consume=False),
    ], [spirit_stones(350), item("comet_iron", 3), fx("codex", entry="skyport_wreck")],
        requires=all_of(qdone("gus_ledger")), hand_in="elder_zhong", chapter="15", target_room="ae_shipyard",
        offer=["Four readings and two measures of sky ink make the Wreck Run. The sighting stones are here, on Rimefrost Summit and on the Presence Terrace.",
               "Then a hull. Lao is waiting. When you are over the Starsea, trust the chart, not your eyes."],
        complete=["Gu. Of course it was Gu. And the comet sails did not take his ledger for the valley's pennies.",
                  "They took it for the names of three of our own peaks' disciples, who sold them the Gate's watch rota. The Gate is next."],
        next="the_gate_holds")
    quest("the_gate_holds", "Sect War", "main", "elder_zhong", [
        o("reach_realm", "Break through to Sage Sovereign 2", realm="sage_sovereign_2"),
        o("pass_event", "Strike the war gong at the Alliance Gate and hold the Gate against the comet sails", event="sect_war"),
        o("set_flag", "Decide what becomes of the Black Ledger", flag="ledger_burned", alt_flag="ledger_returned"),
    ], [spirit_stones(450), item("will_tempering_pill", 2), fx("codex", entry="sect_war")],
        requires=all_of(qdone("the_skyport_wreck"), realm("sage_sovereign_1")), hand_in="elder_zhong", chapter="15", target_room="np_alliance_gate",
        offer=["They will come when the watch changes, as the rota says. The rota is wrong now, but they do not know that.",
               "Every peak sends its best to the Gate. You are not ours, but you are the one who brought the warning. Stand with us."],
        complete=["The comet sails are scattered and their captain is in chains. Nine peaks owe you, and eight of them will even admit it.",
                  "A man came through here once with a river token like yours. He asked about the Trial Hall. Ask Wen about him."],
        next="lus_last_page")
    quest("lus_last_page", "Lu's Last Page", "main", "elder_zhong", [
        o("reach_room", "Climb the Riven Peak above the Skyport Wreck", room="sw_riven_peak"),
        o("set_flag", "Find Lu's last page where the stars are clearest", flag="journal_riven"),
        o("talk_to", "Show the page to Trial Master Wen in the Trial Hall", npc="trial_master_wen"),
    ], [spirit_stones(300), fx("codex", entry="lus_crossing")],
        requires=all_of(qdone("the_gate_holds")), hand_in="trial_master_wen", chapter="16", target_room="sw_riven_peak",
        offer=["Wen keeps the names of everyone who sat the Presence Trial. Your valley man's is written there, and then crossed out.",
               "He left something on the Riven Peak before he went home, the pirates say. They were too afraid of the stars up there to take it."],
        complete=["'I sat under eight seats and felt myself go thin as paper. I got up. The river was still in me, so I went home to it.'",
                  "He did not fail, whatever the ink says. He chose. Now it is your turn to sit."],
        next="the_presence_trial")
    quest("the_presence_trial", "The Presence Trial", "main", "trial_master_wen", [
        o("reach_realm", "Break through to Sage Sovereign 3", realm="sage_sovereign_3"),
        o("pass_event", "Sit beneath the empty ninth seat and bear the Presence of the other eight", event="presence_trial"),
    ], [spirit_stones(500), item("will_tempering_pill", 2), fx("grant_title", title="presence_bearer"), fx("codex", entry="presence_trial")],
        requires=all_of(qdone("lus_last_page")), hand_in="trial_master_wen", chapter="16", target_room="np_trial_hall",
        offer=["The Presence Trial is the door to Will Manifest. You cannot open it here; this land cannot hold a Will Manifest. You can earn the key.",
               "Sage Sovereign 3, then the circle. Bring Will. Will Tempering Pills help. Stubbornness does not."],
        complete=["The ninth seat looked like you, and you did not look away. That is the whole trial. Most people look away.",
                  "Your Presence is yours now. The Expanse is too small to hold what comes next. Go and ask the Launch where it points."],
        next="stars_beyond")
    quest("stars_beyond", "Stars Beyond", "main", "trial_master_wen", [
        o("collect", "Chart the Lantern Run from the stars over the Riven Peak", item="star_chart_lantern", consume=False),
        o("reach_room", "Go to the Starsea Launch", room="sw_starsea_launch"),
        o("talk_to", "Ask Warden He where the ring points", npc="launch_warden_he"),
    ], [spirit_stones(600), fx("set_flag", flag="stars_beyond_done"), fx("grant_title", title="starsea_voyager"), fx("codex", entry="lantern_star_field")],
        requires=all_of(qdone("the_presence_trial")), hand_in="launch_warden_he", chapter="16", target_room="sw_starsea_launch",
        offer=["Navigator Sun sells the lesson for the Lantern Run to Sage Sovereigns who ask nicely. Eight readings, and the stars over the Riven Peak are clearest.",
               "Then go to the Launch. The ring points somewhere. I have always wanted to know where."],
        complete=["The ring lit when you walked up. It has not done that in two hundred years.",
                  "Out there: the Lantern Star Field. Your chart reaches it. Your road does, too, when the time comes. Not today. Soon."])


def act2_starsea_side_quests():
    """Phase E side stories and guided quests: the Yard's two crafts, paired cultivation, deserters, comet iron, three rare Daos."""
    quest("a_chart_of_ones_own", "A Chart of One's Own", "guided", "navigator_sun", [
        o("gather_node", "Take star readings through the sighting stones", 4, item="star_reading", craft="star_charting"),
        o("craft", "Chart the Wreck Run at the chart table", recipe="star_chart_wreck"),
    ], [item("sky_ink", 4), spirit_stones(60)], offered_by_unlock=True, target_room="ae_shipyard",
        offer=["Sighting stones: here, on Rimefrost Summit, on the Presence Terrace. Each gives one reading every little while.",
               "Four readings and two measures of ink. I will give you the ink for the first chart."],
        complete=["Your first chart. The lines are shaky, but they go where they should. That is all a chart is."])
    quest("keel_and_ward", "Keel and Ward", "guided", "shipwright_lao", [
        o("craft", "Build a Cloud Skiff on the slipway", recipe="cloud_skiff"),
    ], [spirit_stones(80), item("formation_stone", 2)], offered_by_unlock=True, target_room="ae_shipyard",
        offer=["Six spirit wood, four stormsteel, two formation stones, three harpy plumes. Bring them, lay the keel, and I'll check your lines.",
               "You'll need a smith's hand. Adept, at least. Hulls forgive nothing."],
        complete=["She floats. On nothing, which is the point. Don't sail her anywhere you haven't charted."])
    quest("two_breaths", "Two Breaths, One River", "guided", "alchemist_fen", [
        o("meditate_seconds", "Meditate with a companion beside you", 30, near="companion"),
    ], [spirit_stones(40), item("qi_restoration_pill", 3)], offered_by_unlock=True, target_room="ae_condensing_hall",
        offer=["Sage Qi is thick. Two cultivators breathing together thin it for each other. Paired cultivation, the old texts call it.",
               "Sit with one of your companions. Breathe when they breathe. See what happens."],
        complete=["Faster, yes? Keep a companion close when you sit. The river flows better with two banks."])
    quest("the_deserters", "The Deserters", "side", "champion_qiao", [
        o("kill", "Bring down the rogue Nine Peaks disciples at the Broken Pier", 6, enemy="nine_peaks_disciple"),
        o("collect", "Return their scratched badges", 4, item="alliance_badge", consume=True),
    ], [spirit_stones(160), item("will_tempering_pill", 1)], requires=all_of(qdone("gus_ledger")), target_room="sw_broken_pier",
        offer=["Some of ours ran to the comet sails. They scratch the peaks off their badges, as if that makes them someone else.",
               "Bring the badges home. Six of them will not come quietly."],
        complete=["Four badges. I'll give them back to their peaks. What the peaks do with them is their business."])
    quest("iron_from_a_comet", "Iron from a Comet", "side", "shipwright_lao", [
        o("collect", "Bring comet iron from the pirates' hulls", 6, item="comet_iron", consume=True),
    ], [spirit_stones(150), fx("learn_recipe", recipe="storm_sloop")], requires=all_of(qdone("keel_and_ward"), qdone("gus_ledger")),
        target_room="sw_pirate_deck",
        offer=["The comet sails outrun everything in the Expanse. It's the iron: flew through a comet's tail and came out ringing.",
               "Six ingots. I'll teach you the sloop. Two sails, comet keel. You'll need a formation master's plates too."],
        complete=["Listen to it ring. Here: the sloop's lines. Half again as fast as the skiff, if your formations hold."])
    quest("clear_skies_over_the_peak", "Clear Skies over the Peak", "side", "navigator_sun", [
        o("gather_node", "Take star readings on the Riven Peak", 3, item="star_reading", craft="star_charting"),
    ], [spirit_stones(120), item("sky_ink", 6)], requires=all_of(qdone("the_skyport_wreck")), target_room="sw_riven_peak",
        offer=["The stars over the Riven Peak are the clearest in the Expanse. The pirates say they watch you back.",
               "Three readings from up there. I want to see if they are right."],
        complete=["These are... very clear. Hm. Keep your chart close up there."])
    # Rare Daos (v1.1): three teachers of the Expanse open a Dao the valley never taught.
    quest("blood_remembers", "Blood Remembers", "side", "matriarch_tie", [
        o("set_flag", "Kneel before the Ironroot tablets in the Ancestor Hall", flag="tablets_honoured"),
        o("reach_realm", "Become a Sage Sovereign", realm="sage_sovereign_1"),
    ], [fx("open_dao", dao="blood"), fx("learn_technique", technique="blood_burning"), spirit_stones(100)], requires=all_of(qdone("ironroot_blood")), target_room="ir_ancestor_hall",
        offer=["Kin by adoption is kin. But the blood still has to learn to hear you. Kneel before the tablets.",
               "And grow. The Blood Dao listens to Sovereigns. Come back when you are one."],
        complete=["There. Feel it? Every Ironroot who ever lived, in the beat under your ribs. That is the Blood Dao. It is yours now."])
    quest("what_the_bones_say", "What the Bones Say", "side", "bone_reader_xiu", [
        o("collect", "Bring shards of the Terracotta Wardens, who died and did not die", 3, item="terracotta_shard", consume=True),
    ], [fx("open_dao", dao="life_death"), spirit_stones(100)], requires=all_of(qdone("the_tomb_king")), target_room="ts_hall_of_sand_kings",
        offer=["The wardens were men once. Then clay. Then something that remembers being men. Bring me what is left of three.",
               "I will show you the line between living and not. It is thinner than you think, and it moves."],
        complete=["Hold this shard. Warm, yes? The Life and Death Dao begins where you stop being sure which side it is on."])
    quest("the_sound_of_snow", "The Sound of Snow", "side", "hermit_shuang", [
        o("kill", "Quiet the Snow Apes on their ledges", 6, enemy="snow_ape"),
        o("meditate_seconds", "Sit in silence in the hermit's ice cave", 30),
    ], [fx("open_dao", dao="emotion"), spirit_stones(100)], requires=all_of(qdone("frost_and_silence"), realm("sage_sovereign_1")),
        target_room="rf_hermits_ice_cave",
        offer=["...", "The apes are loud. Quiet them. Then sit here, with me, until you can hear what you feel."],
        complete=["...", "There. Every feeling has a sound. The Emotion Dao is only listening. You were loud for a long time."])


def act2_side_quests():
    """Act II side stories of the port, the plains, the heights, the lake, the canyons and the Hold."""
    quest("snow_for_the_cabinet", "Snow for the Cabinet", "side", "apothecary_wu", [
        o("collect", "Pick Frost Lotus on Rimefrost Heights", 3, item="frost_lotus", consume=True),
    ], [item("storm_blood_pill", 3), spirit_stones(40)], requires=all_of(qdone("frost_and_silence"), realm("sage_1")), target_room="rf_frostpine_climb",
        offer=["Frost Lotus. Three. It only blooms where the snow never melts.", "It steadies a Sage's Qi. And my prices."],
        complete=["Perfect petals. Here, Storm Blood Pills, fresh from the cabinet."])
    quest("clear_skies", "Clear Skies", "side", "dockmaster_fu", [
        o("kill", "Drive off the Azure Carp Dragonets over the Reedless Shore", 8, enemy="azure_carp_dragonet"),
    ], [spirit_stones(70), item("dragonet_scale", 2)], requires=all_of(qactive("the_mirror_remembers"), realm("sage_2")), target_room="ml_reedless_shore",
        offer=["Dragonets keep spitting at my lake ferry. The sails can't take much more.", "Eight of them. The rest will learn."],
        complete=["The ferry thanks you. So does my budget."])
    quest("a_lans_herd", "A-Lan's Herd", "side", "herder_a_lan", [
        o("kill", "Drive the Spark Weasels away from the herd", 10, enemy="spark_weasel"),
        o("collect", "Bring Spark Pelts for new saddle blankets", 4, item="spark_pelt", consume=True),
    ], [spirit_stones(50), item("thunderhorn_stew", 3)], requires=all_of(qdone("storm_in_the_blood"), realm("heaven_glimpse_3")), target_room="tp_stormgrass_verge",
        offer=["The weasels keep stealing lightning out of the grass, and then the rhinos stampede!", "Chase them off? Please?"],
        complete=["Grandpa says you'd make a good herder. That's the best thing he says about anyone."])
    quest("silk_on_the_wind", "Silk on the Wind", "side", "tollkeeper_bai", [
        o("collect", "Cut Kite Silk from the Wind Kites of the canyons", 5, item="kite_silk", consume=True),
    ], [spirit_stones(80), item("storm_shard", 10)], requires=all_of(qdone("nine_seats"), realm("sage_2")), target_room="gc_kite_winds",
        offer=["The canyon wind shreds my toll flags in a week. The kites up there are made of something it can't tear.",
               "Five lengths of their silk. The Alliance can keep its banners."],
        complete=["Look at that. Not a fray. The next brigand who says he couldn't see the flag can argue with it."])
    quest("plumes_for_the_bellows", "Plumes for the Bellows", "side", "clan_smith_gang", [
        o("collect", "Bring Harpy Plumes from the Harpy Roosts", 4, item="harpy_plume", consume=True),
    ], [spirit_stones(90), item("stormsteel_ore", 4)], requires=all_of(qdone("ironroot_blood")), target_room="gc_harpy_roosts",
        offer=["Harpy plumes hold a wind of their own. Line the bellows with them and the forge breathes like a storm.",
               "Four will do. Kin price, of course. Meaning you fetch them."],
        complete=["Hear that? The fire's roaring on its own. Take some stormsteel. It'll take a better edge now."])
    quest("cactus_water", "Cactus Water", "side", "oasis_keeper_meng", [
        o("collect", "Pick Ember Cactus flowers on the Glass Dunes", 4, item="ember_cactus", consume=True),
    ], [spirit_stones(90), item("cactus_water", 4)], requires=all_of(qdone("glass_and_bone")), target_room="sd_glass_dunes",
        offer=["The flowers store the sun. Steep them right and the water keeps the heat out of you instead.",
               "Four flowers. Pick them at dusk if you can. At noon they bite."],
        complete=["Cactus water. Drink it before the heat and your Essence runs cool. Here, the first jars are yours."])
    quest("glass_teeth", "Glass Teeth", "side", "bone_reader_xiu", [
        o("collect", "Bring Dune Worm glass teeth", 3, item="worm_glass_tooth", consume=True),
    ], [spirit_stones(110), item("clear_mind_pill", 2)], requires=all_of(qdone("glass_and_bone")), target_room="sd_worm_sea",
        offer=["Bones for the past, glass for the future. A worm's tooth shows what is coming, if you hold it to the sun.",
               "Three teeth. The worms will not give them politely."],
        complete=["Clear as water. I see... a ship with no sea. Hm. That one is yours to find, not mine."])
    quest("stingers_for_the_hold", "Stingers for the Hold", "side", "clan_smith_gang", [
        o("collect", "Bring Sandstorm Scorpion stingers", 5, item="scorpion_stinger", consume=True),
    ], [spirit_stones(120), item("stormsteel_ore", 4)], requires=all_of(qdone("glass_and_bone"), qdone("plumes_for_the_bellows")),
        target_room="sd_scorpion_flats",
        offer=["Scorpion venom on a quenched edge. Old Ironroot trick for the desert raiders. Bring me stingers.",
               "Five. Mind the tails."],
        complete=["Good. The raiders will think twice. Here, more ore. Kin price."])


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
    # S49 grudges: the Gorge Bandits' feud with Greyreed ends in a fair fight with their chief.
    quest("old_scores", "Old Scores", "side", "hamlet_trader_min", [
        o("win_spar", "Settle it hand to hand with Chief Yan Bo at the Gorge Mouth", opponent="gorge_chief"),
    ], [taels(300)], requires=all_of(qdone("mins_first_caravan")), target_room="wg_gorge_mouth",
          offer=["The Gorge Bandits and Greyreed have old scores. Their chief says he'll call it even if someone beats him fairly. No knives, no crowd.",
                 "He waits at the Gorge Mouth. Win, and the feud is over. For Greyreed, and for you."],
          complete=["Yan Bo sent word: the Gorge is quiet for Greyreed. And for you. I didn't think I'd live to see it."])
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
            rw = [fx("add_bond", amount=10), taels(80)] + ([item("wisp_banner", 1)] if qid == "bai_lings_formation" else [])
            quest(qid, qname, "side", cid, [ob], rw, requires=rq, chapter="companion",
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
                    "choices": [{"text": "Run to the hut! Now!", "effects": [{"kind": "set_flag", "flag": "dou_safe"}, {"kind": "deed", "deed": "rescue_dou"}, {"kind": "record_debt", "id": "dou_rescue"}], "close": True}]}})
    tree("granny_liu", [{"requires": all_of({"kind": "in_room", "room": "lf_village_night"}, noflag("granny_safe")), "node": "night"}],
         {"night": {"lines": ["My old legs... help me, child."],
                    "choices": [{"text": "Lean on me. To Aunt Ping's hut.", "effects": [{"kind": "set_flag", "flag": "granny_safe"}, {"kind": "deed", "deed": "rescue_granny"}], "close": True}]}})
    tree("old_ma", [{"requires": all_of({"kind": "in_room", "room": "lf_village_night"}, noflag("ma_safe")), "node": "night"}],
         {"night": {"lines": ["My shop! My stock!"],
                    "choices": [{"text": "Leave it! Get to the hut!", "effects": [{"kind": "set_flag", "flag": "ma_safe"}, {"kind": "deed", "deed": "rescue_ma"}], "close": True}]}})
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
    # Flavour trees speak only once the NPC has no quest to give (a tree entry outranks quest offers).
    tree("warden_cao", [{"requires": all_of(qdone("a_sky_full_of_toll_roads")), "node": "toll"}],
         {"toll": {"lines": ["The Alliance keeps the roads safe. Mostly from people who don't pay.",
                             "Your valley token means nothing here. Earn an Alliance name, or a reputation."],
                   "choices": [{"text": "Understood.", "close": True}]}})
    tree("envoy_lanshi", [{"requires": all_of(qactive("nine_seats"), noflag("path_alliance"), noflag("path_independent")), "node": "offer"},
                          {"requires": all_of(any_of(flag("path_alliance"), flag("path_independent")), noflag("path_changed")), "node": "change"}],
         {"offer": {"lines": ["The Alliance offers you a seat: a token that opens every sky road, the Factor's better prices, and the Hall's ear.",
                              "Or walk the free road, like the broker. No token, no tolls paid in obedience. Lower fees at the Pavilion. Fewer friends."],
                    "choices": [{"text": "Take the Alliance seat.", "effects": [{"kind": "set_flag", "flag": "path_alliance"},
                                 {"kind": "grant_item", "item": "alliance_token", "count": 1}, {"kind": "grant_title", "title": "alliance_envoy"}], "close": True},
                                {"text": "Keep the free road.", "effects": [{"kind": "set_flag", "flag": "path_independent"},
                                 {"kind": "grant_title", "title": "free_cultivator"}], "close": True},
                                {"text": "Let me think.", "close": True}]},
          "change": {"lines": ["Changed your mind? The Hall allows it once. It costs 300 Spirit Stones in paperwork, and it costs more in trust."],
                     "choices": [{"text": "Change my path (300 stones).", "requires": all_of({"kind": "currency_at_least", "currency": "spirit_stone", "amount": 300}),
                                  "effects": [{"kind": "grant_currency", "currency": "spirit_stone", "amount": -300}, {"kind": "swap_path"},
                                              {"kind": "set_flag", "flag": "path_changed"}], "close": True},
                                 {"text": "No. I'll keep to it.", "close": True}]}})
    tree("matriarch_tie", [], {})
    # Chapter 14: after the Tomb King falls, the Pilgrim asks for the seal. Either answer keeps it from him.
    tree("grey_pilgrim", [{"requires": all_of(qactive("the_tomb_king"), {"kind": "item_owned", "item": "sunscar_seal", "count": 1},
                                              noflag("seal_kept"), noflag("tomb_resealed")), "node": "seal"},
                          {"requires": all_of(qactive("the_tomb_king")), "node": "waiting"}],
         {"seal": {"lines": ["You did well. He was old when my master was young.",
                             "Now give me the seal. It is only a key, and you have no door for it."],
                   "choices": [{"text": "No. I keep the seal.", "effects": [{"kind": "set_flag", "flag": "seal_kept"},
                                {"kind": "grant_title", "title": "seal_keeper"}], "close": True},
                               {"text": "No. It goes back into the King's hand, and the tomb stays shut.",
                                "effects": [{"kind": "set_flag", "flag": "tomb_resealed"}, {"kind": "remove_item", "item": "sunscar_seal", "count": 1},
                                            {"kind": "deed", "deed": "tomb_resealed"},
                                            {"kind": "grant_title", "title": "sunscar_sealer"}], "close": True}]},
          "waiting": {"lines": ["Go on. He is waiting on his throne, as he has for three thousand years.", "I will wait too. I am good at it."],
                      "choices": [{"text": "(Leave him.)", "close": True}]}})
    tree("bone_reader_xiu", [], {})
    # Chapter 15: the smuggler in chains on the Pirate Deck. Freed or left, the Black Ledger comes with you.
    tree("gu_in_chains", [{"requires": all_of(qactive("the_skyport_wreck"), noflag("gu_freed"), noflag("gu_left")), "node": "chains"}],
         {"chains": {"lines": ["You. The fisher's child from Lotus Ferry. Look at you now.",
                               "I sold them the ledger for passage. They kept the ledger and kept me. The names they wanted were never the valley's.",
                               "Three disciples of the Nine Peaks sold them the Gate's watch. It is all in the ledger. Free me and it is yours."],
                     "choices": [{"text": "(Break his chains.) Go home, Gu. Pay your debts there.",
                                  "effects": [{"kind": "set_flag", "flag": "gu_freed"}, {"kind": "grant_item", "item": "black_ledger", "count": 1},
                                              {"kind": "deed", "deed": "gu_freed"},
                                              {"kind": "record_debt", "id": "gu_repays", "due_h": 48, "mail": "gu_repays",
                                               "attachments": [{"currency": "spirit_stone", "amount": 60}, {"item": "sentinel_core", "count": 1}]}],
                                  "close": True},
                                 {"text": "(Take the ledger from his belt.) The Alliance can decide about you.",
                                  "effects": [{"kind": "set_flag", "flag": "gu_left"}, {"kind": "grant_item", "item": "black_ledger", "count": 1},
                                              {"kind": "deed", "deed": "gu_left"},
                                              {"kind": "record_debt", "id": "gu_remembers", "due_h": 72, "mail": "gu_remembers", "attachments": []}],
                                  "close": True}]}})
    # Chapter 15: after the Gate holds, the Black Ledger's fate.
    tree("elder_zhong", [{"requires": all_of(qactive("the_gate_holds"), {"kind": "event_passed", "event": "sect_war"},
                                             {"kind": "item_owned", "item": "black_ledger", "count": 1}, noflag("ledger_burned"),
                                             noflag("ledger_returned")), "node": "ledger"}],
         {"ledger": {"lines": ["The deserters' names are copied. The rest of that book is your valley's business, not the Alliance's.",
                               "Burn it and nobody pays again. Or send each page home, and let every family decide what their secret is worth."],
                     "choices": [{"text": "Burn it. The debts end here.",
                                  "effects": [{"kind": "set_flag", "flag": "ledger_burned"}, {"kind": "remove_item", "item": "black_ledger", "count": 1},
                                              {"kind": "deed", "deed": "ledger_burned"},
                                              {"kind": "grant_title", "title": "ledger_burner"}], "close": True},
                                 {"text": "Send each page home to its family.",
                                  "effects": [{"kind": "set_flag", "flag": "ledger_returned"}, {"kind": "remove_item", "item": "black_ledger", "count": 1},
                                              {"kind": "deed", "deed": "ledger_returned"},
                                              {"kind": "grant_title", "title": "ledger_returner"}], "close": True}]}})
    tree("broker_mu", [{"requires": all_of(qdone("the_mirror_remembers"), noflag("heard_nine_seats")), "node": "rumours"}],
         {"rumours": {"lines": ["You look like someone who has seen a ghost in a lake. It happens.",
                                "Word from Nine Peaks: the Alliance is counting heads. Everyone who crossed the gate this year gets asked to pick a side."],
                      "choices": [{"text": "Then I'll decide when they ask.", "effects": [{"kind": "set_flag", "flag": "heard_nine_seats"}], "close": True}]}})
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
        {"id": "auction_won", "from": "The Auction Pavilion", "subject": "Your lot: {item}", "body": "The hammer fell in your favour. Your lot is enclosed, with the Pavilion's compliments."},
        {"id": "auction_won_recipe", "from": "The Market Street auctioneer", "subject": "Your lot: {item}",
         "body": "The hammer fell in your favour. The scroll was read to you on the spot, as is the custom; the recipe is yours."},
        {"id": "gu_repays", "from": "Gu, a free man", "subject": "What I owe you",
         "body": "I paid the valley what I could. This is for the fisher's child who broke my chains. A man who is paid back remembers how it felt."},
        # S49 named debts (Part 8).
        {"id": "dou_repays", "from": "Little Dou", "subject": "I found it myself!",
         "body": "You carried me through the Hollow Night so now I carried this up the cliff by myself. Granny Liu says it's a heaven herb. Don't eat it all at once."},
        {"id": "lieutenant_warning", "from": "A friend from the Hideout", "subject": "About Gu's warehouse",
         "body": "You let me walk away, so here is a warning for free. Gu has men waiting in the warehouse rafters. Look up before you go in. These might help."},
        {"id": "kuai_threat", "from": "Kuai Shan", "subject": "My brother",
         "body": "He threw down his sword and you cut him anyway. I will be on the Caravan Road. Come and try that with me."},
        {"id": "gu_remembers", "from": "Unsigned", "subject": "We know your name",
         "body": "You left our uncle in chains for the Alliance to weigh. The Gu family keeps ledgers too. One day it will be your page we open."},
        {"id": "garden_raid_pests", "from": "The sect gardener", "subject": "Pests in your bed at {place}",
         "body": "Beetles got into your {herb} while you were away. It will live, but it lost half its growth. A pet on Guard duty or a Protection formation would keep them off."},
        {"id": "garden_raid_thief", "from": "The sect gardener", "subject": "Your {herb} is gone",
         "body": "Someone dug up your {herb} at {place} in the night. The bed is bare. Next time leave a pet on Guard duty, or burn a Protection or Concealment formation there."},
        {"id": "elder_token", "from": "Your mentor", "subject": "An Elder's token", "body": "Word reached the sect that you are a Sage Sovereign. Your token is an Elder's now: at any teleport stone it will call you home, and the sect will not ask for shards. Come home sometimes."},
    ]
    entries("mail_templates", rows)


def codex():
    rows = [
        {"id": "lotus_ferry", "title": "Lotus Ferry", "body": "A fishing village at the river's bend. Aunt Ping, Lu and a few dozen others. Home."},
        {"id": "lu_float", "title": "Lu's float", "body": "A red-and-white cork float in the hut loft, older than you. Lu never fishes with it. He never throws it away either."},
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
        # S48 Soul Search: what an elite's soul gives up when it dies searched, one page at a time.
        {"id": "soul_memory_1", "title": "A soul's memory: the grey morning", "body": "A wolf remembers the morning the colour drained out of the forest one tree at a time, and the pack stopped hearing each other."},
        {"id": "soul_memory_2", "title": "A soul's memory: the ferry coin", "body": "A bandit remembers a fare paid in silver stamped with a sect crest no one on the river had seen for fifty years."},
        {"id": "soul_memory_3", "title": "A soul's memory: one rope", "body": "A guard remembers Jade and Cloud disciples hauling on one rope to raise the Gate stones, before either sect had a name."},
        {"id": "soul_memory_4", "title": "A soul's memory: lanterns under water", "body": "A spirit remembers lanterns burning under the river at the Drowned Shrine, tended by monks who no longer needed breath."},
        {"id": "soul_memory_5", "title": "A soul's memory: forty pills", "body": "A rogue cultivator remembers forty pills in a month, a breakthrough that held for a day, and a laugh that would not stop."},
        {"id": "soul_memory_6", "title": "A soul's memory: the open palm", "body": "A beast remembers a man kneeling in the tall grass with an open palm, and the pack deciding not to eat him."},
        {"id": "soul_memory_7", "title": "A soul's memory: the sky toll", "body": "A pirate remembers a toll warden of the Nine Peaks taking three coins and a finger for a missing seal."},
        {"id": "soul_memory_8", "title": "A soul's memory: the buried city", "body": "A tomb guard remembers a king who ordered the desert poured over his own city so that no one could ever leave it."},
        {"id": "soul_memory_9", "title": "A soul's memory: the oath", "body": "A ghost remembers a blade laid on an altar by someone who swore never to draw it again, and drew it the next night."},
        {"id": "soul_memory_10", "title": "A soul's memory: the star sea", "body": "Deep under this soul lies a memory that is not its own: a ship sailing a sea of stars, and a voice saying the river runs there too."},
        {"id": "cloudgate_port", "title": "Cloudgate Port", "body": "A harbour on a floating island where the Ascension Gate opens onto the Azure Expanse. Sky-ships, toll wardens and every kind of traveller."},
        {"id": "nine_peaks_alliance", "title": "The Nine Peaks Alliance", "body": "Nine sects on nine peaks, one law between them. They keep the sky roads safe and tax every step taken on them."},
        {"id": "storm_ward", "title": "Storm Ward", "body": "The Expanse's storms draw Qi out of anyone not attuned to them. Four jades, fed with Storm Shards, ward the blood. Each region asks for more."},
        {"id": "grey_pilgrim", "title": "The Grey Pilgrim", "body": "A robed stranger buying Hollow shards across the Expanse. He casts no shadow, and he knew your name."},
        {"id": "rimefrost_hermit", "title": "The Hermit of Rimefrost", "body": "Hermit Shuang has sat above the snow line so long the ice grows around him. He speaks when silence has earned it."},
        {"id": "lu_crossing", "title": "Lu's crossing", "body": "The lake's mirror showed a young Lu at Mirrorwater, long ago, a river token at his belt. He came through the Expanse once, too."},
        {"id": "nine_seats", "title": "The Nine Seats", "body": "Nine sects, nine seats in the Hall of Nine. Every cultivator who crosses the gate is asked to take the Alliance's token or keep the free road."},
        {"id": "gale_canyons", "title": "The Gale Canyons", "body": "Wind-carved sandstone east of Nine Peaks. Kites that are not kites, harpies in the roosts, and a toll paid in Hollow shards."},
        {"id": "ironroot_clan", "title": "The Ironroot clan", "body": "A clan of the canyon's far side whose ancestors' tablets are carved from iron-hard roots. Kin by choice, not only by blood."},
        {"id": "sunscar_desert", "title": "The Sunscar Desert", "body": "Dunes of fused glass south of Ironroot Hold. The sun here is heavier than elsewhere, and the sand remembers the sand kings who ruled it."},
        {"id": "tomb_of_sunscar", "title": "The Tomb of Sunscar", "body": "A burial palace sealed from within. Clay soldiers guard its halls, and a gate of bronze answers only a key of gold and jade."},
        {"id": "tomb_king", "title": "The Tomb King", "body": "A sage-king who carried the sun seal into his tomb rather than let the Hollow have it. Sand kept him; duty kept him awake."},
        {"id": "sage_sovereign", "title": "Sage Sovereign", "body": "The Sage whose Qi governs the land around it. A Sovereign's breakthrough needs a full reserve and one Dao that has learned to adapt."},
        {"id": "starsea", "title": "The Starsea", "body": "Beyond the Expanse's last peaks the sky has no floor: stars below as well as above. Only a Sage's Qi survives its wind, and only a charted vessel finds the far shore."},
        {"id": "skyport_wreck", "title": "The Skyport Wreck", "body": "An old sky-port that broke on the edge of the Starsea. Its piers hang over nothing; the pirates of the comet sails made a nest of its biggest hull."},
        {"id": "sect_war", "title": "The War at the Gate", "body": "When the comet sails struck the Alliance Gate, every peak sent its best. A valley cultivator held the line beside them."},
        {"id": "lus_crossing", "title": "Lu's Crossing", "body": "Five pages across the Expanse: the port, the lake, the tomb, the canyons, the peak. Lu sat the Presence Trial, felt himself go thin, and chose the river instead."},
        {"id": "presence_trial", "title": "The Presence Trial", "body": "Eight seats of the Nine Peaks press their Presence on one cultivator. Whoever stays themselves under it holds the key to Will Manifest."},
        {"id": "lantern_star_field", "title": "The Lantern Star Field", "body": "Past the Starsea Launch: a field of lanterns hanging in the dark. No one hangs them. They are simply there, waiting for the next age of your road."},
        # Gap report G1: what pills cost, the heart, the ledger, fire and furnace.
        {"id": "pills_and_the_body", "title": "What pills cost",
         "body": "Pills never spoil, but the body remembers them. Each dose of one kind works less than the last, until a great breakthrough lets it forget one. Qi that came mostly from pills makes a hollow foundation, and 5% of every pill's poison stays behind as residue. Settle foundation in seclusion, or pass through Heaven's Cleansing untouched, to make it your own again."},
        {"id": "heart_demons", "title": "Heart demons",
         "body": "Doubt, a forced breakthrough, a broken path, a death, a cruelty: each feeds the heart demon. Every 25 makes a major breakthrough one step riskier and brings one more demon into the Trial of Reflections. Meditation wears it down; Calm Incense clears it."},
        # S48: the body ladder, physiques, roots and the core.
        {"id": "body_ladder", "title": "The body ladder",
         "body": "A body is forged in four rungs: Copper at body level 18, then Iron, Jade and Gold. Each rung asks three things: the body level, its Temper trial (strike the Temper drum at a training ground) and a full soak in its medicinal bath. Copper lets body techniques spend HP when QI runs out; Iron shrugs off knockback; Jade heals half again as fast; Gold cannot be Qi-sealed. A bath beyond your rung injures the body."},
        {"id": "physiques", "title": "Physiques",
         "body": "A physique is earned, never bought: a flawless Heaven's Cleansing, ten nights of meditation at the Falls Pool, fifty Fire pills, Copper Body before Qi Unfurling 3, ten kilometres in the air. Each gives a gift and takes something back, for life."},
        {"id": "core_forging", "title": "Core Forging",
         "body": "At Heart Tempering 9 the Qi condenses into a core, and the core remembers how it was made. Five things help: a room of your method's element, the hour of your method's Yin or Yang, full Composure, no residue, and a Heavenly Flame Pill within the hour. Each one met has four chances in five to count. The core forms at grade 9 less what counted, never better than 5; a flawless Heaven's Cleansing adds one more, down to 4."},
        {"id": "heavenly_tribulation", "title": "Heavenly tribulation",
         "body": "From Cloud Stride on, every great breakthrough draws a cloud over the room. Bolts fall one by one, three into Spirit Awakening, six into Heaven Glimpse, nine into Sage, then waves of nine; each 25 heart demon and each 100 sin adds one more. A ring shows where each will land a second before it does: step out of it, or guard to take half. Roofs do not help. A Lightning Rod Talisman in the bag takes one bolt. Fall under the heavens and the breakthrough fails with the body."},
        {"id": "fates", "title": "Breakthrough fates",
         "body": "A great breakthrough shakes a cultivator's fate loose. Three cards are drawn and one is kept: a gift, and most often a cost. Some last for life, some only until the next great realm, and a few wait for the next tribulation or the next breakthrough."},
        {"id": "qi_deviation", "title": "Qi deviation",
         "body": "A breakthrough that fails at Severe risk, or on a method your elements fight, can send the Qi astray. For ten minutes every technique strikes with an element of its own choosing."},
        {"id": "vows", "title": "Vows",
         "body": "A vow forbids one thing for as long as it is held, and gives a steady gift for it. Mercy spares fleeing foes for better healing; Plain Fare refuses burst pills for a harder body; Silence sheathes the killing intent for Will; Fasting refuses food that lends a buff for faster accumulation. Letting a vow go breaks it, and a broken vow feeds the heart demon by 15."},
        {"id": "epiphany", "title": "Epiphany",
         "body": "Now and then, while insight comes in from contemplation or a hard fight, understanding arrives all at once: for a minute insight comes five times as fast, and sometimes a technique takes a step of mastery for nothing. After an epiphany the mind needs two hours before another."},
        {"id": "inner_arts", "title": "Inner Arts",
         "body": "Inner Arts are passive: a way of breathing, of standing, of carrying the Qi. The Mission Halls teach them from thin manuals. Two can be worn from Qi Unfurling 1, three from Heart Tempering 1, four from Spirit Awakening 1. A few belong to one weapon and sleep while another is in hand."},
        {"id": "karma", "title": "Merit and sin",
         "body": "The world keeps a ledger. Mercy and help earn merit: a hundred of it eases one great breakthrough in each realm. Cruelty and the back-room markets earn sin, and sin feeds the heart demon and strengthens the heavenly tribulation. Some deeds come back as letters. The Relations page keeps the ledger."},
        {"id": "alignment", "title": "The righteous and the demonic",
         "body": "Every choice leans you one way or the other, from demonic through shadowed, balanced and upright to righteous. The Cloud Sect's abbots keep some of their wares for the upright, and Broker Mu keeps his worst goods for the shadowed. Alignment opens and closes doors like these; it never stands between you and your next realm."},
        {"id": "affinity", "title": "Hearts and bonds",
         "body": "People remember kindness. Each quest done for someone, and one gift a day, brings you closer: up to five hearts. What a person loves is worth a heart at once. Hearts teach recipes and give keepsakes, shopkeepers take a little off at three and five, and companions spar with you at three. At four hearts a companion can be sworn as a sibling (three at most); at five, one can become your Dao Companion, who steadies your breakthroughs, shares your insight and meditates with you. The elder who takes you as a personal disciple is your master."},
        {"id": "grudges", "title": "Grudges and bounties",
         "body": "Kill a faction's named people and it remembers. Once the grudge passes its threshold, its hunters wait for you on the roads they know, at your own strength. Blood money settles it, or a duel with their champion, or doing right by the people they wronged. Elder Gu's smugglers are different: their grudge ends only when his ring does. The town boards post bounties on named targets, two at a time; a named foe who yields can be spared or finished, and either choice is remembered."},
        {"id": "fame", "title": "Fame",
         "body": "Your own name, apart from any sect's standing: Unknown, Noted, Rising, Renowned, Legendary. Tournaments, great foes and the Beast Tide raise it. People talk, and losing a spar where the town can see costs you. From Rising, young masters of good families come looking to test you. Accept and win, and your name grows; decline, and it shrinks a little."},
        {"id": "furnaces_and_fire", "title": "Furnace and fire",
         "body": "The furnace you set in the furnace slot decides the batch, how steady the heat is, how many impurities it strains out, and sometimes one pill more. Better ones are forged at the forge, and enhancing one steadies its heat. Charcoal takes a pill as far as Perfect. Earth Fire at a vent, or a beast core of rank 2 or more burnt as Beast Fire, can reach Pill Grain. Only a Heavenly Flame, or the Nine-Dragon Cauldron, reaches Halo and Soul."},
        {"id": "alchemist_guild", "title": "The Alchemist Guild",
         "body": "Guildmaster Tang keeps the guild's hall in Stoneford's Artisan Row. Each rank is one exam against the candle: five Fine Healing Pills in three minutes for Adept, three Superior Foundation Guard Pills in five for Expert. A badge opens the guild shop and the commission board, three orders a morning, paid in taels or contribution up to a fifth of what a day's work would earn you."},
        {"id": "rare_herbs", "title": "Rare herbs",
         "body": "Most herbs are ten years old when you find them. A few patches, always on high ground, grow for a hundred years or a thousand. They ripen only for twenty minutes around their hour, every second, third or fifth day, and some flower in one season only. Pick one early and it is a tier younger. The hold ends in a ring: tap inside the gold band for a perfect harvest, which keeps the herb's full age and may shake a seed loose. Miss, and it drops a tier. Guardians wake when you climb toward a ripe one: kill them, draw them off past their leash, or pick the herb unseen under Concealment. A Spirit Sense pulse reads each patch's time. In a recipe an older herb can stand in for a younger one of its family, and it refines better."},
        {"id": "herb_garden", "title": "The herb garden",
         "body": "A garden bed grows a herb from seed while you are away: willow moss in two hours, a ginseng root in four, an orchid in eight. A room's Qi speeds it (a cave abode's beds grow half again as fast). Bottled spring water, three bottles a day from any Qi spring, hurries a herb by a quarter. Each bed has a field grade: Low beds grow up to Earth-grade herbs, Mid up to Heaven, High up to Mystic. Spirit Soil raises a bed one grade for good. With a Spirit Spade and Expert gathering you can dig up a rare herb and bring it home at its age, though one in four dies on the way. The Verdant Dew Vial fills with a drop a day; each drop ages the herb in a bed one tier, as far as the valley's Qi allows: a thousand years."},
        {"id": "seasons", "title": "Seasons",
         "body": "The year turns every week with the Monday reset: Spring, Summer, Autumn, Winter. A rare herb tied to a season lies dormant outside it. The Codex's Seasons tab shows the calendar. No road and no realm ever waits on a season."},
        {"id": "experiments", "title": "Experiments",
         "body": "Put two to four herbs you know into the furnace together and see what they make. A few old recipes hide in the right herbs; everything else comes out a Murky Pill. Every attempt is written in the log for all your characters, so nobody wastes herbs on the same mix twice. Herbs that fight each other blow the furnace."},
        {"id": "ancient_recipes", "title": "Ancient recipes",
         "body": "Some recipes survive only as torn pages scattered through dungeons and secret realms. A full set teaches the recipe. With pages missing you can still Deduce it, at the cost of one set of ingredients: each page gives a fifth of a chance, each Alchemy Dao tier above the third a tenth more, never above 95%."},
        {"id": "mist_lantern_flame", "title": "Heavenly Flame: Mist Lantern",
         "body": "The valley's own Heavenly Flame. It drifted in a Weeping Lantern above the Forgotten Monastery for a hundred years. Absorbed, it widens every strike band a fifth."},
        {"id": "cold_lamp_flame", "title": "Heavenly Flame: Cold Lamp",
         "body": "Blue and quiet, it burned in the belly of the Thousand-Eye Toad under Mirrorwater Lake, long after the lamp it came from was gone."},
        {"id": "sunscar_throne_ember", "title": "Heavenly Flame: Sunscar Throne Ember",
         "body": "Three thousand years of desert sun, banked under a dead king's throne."},
        {"id": "comet_tail_flame", "title": "Heavenly Flame: Comet Tail",
         "body": "White fire from a comet's tail, which Captain Rao kept in a lamp and never learned to use."},
        {"id": "sage_qi", "title": "Sage Qi", "body": "True Qi pressed until it remembers it was light. Stronger by far, and the valley could never have held it."},
        {"id": "river_of_time", "title": "River of Time and Space", "body": "Locked.", "locked": True},
        {"id": "jade_river", "title": "The Jade River", "body": "It runs through every land you will ever see."},
        {"id": "river_dream", "title": "A dream of the River",
         "body": "You dreamed of the River from above: every land on its banks, the valley no bigger than a leaf, and further than the Starsea a light where it begins. Someone stood at its source, looking back down at you."},
        {"id": "lifespan", "title": "Years",
         "body": "A mortal body lasts eighty years or so. Every great realm pushes the end further off: a hundred years at Bone Forging, three hundred at Cloud Stride, a thousand and more once you are a Sage. The long-lived count years the way mortals count seasons. Peaches of long life and old lingzhi add a few more; nothing in the valley takes them away."},
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
    # Act II quests pay a smaller share of a stage's need: its stages are longer and hold more story (Part 4 pacing).
    n0 = len(Q)
    act2_quests()
    act2_chapter12()
    act2_chapter13()
    act2_chapter14()
    act2_chapters_15_16()
    for q in Q[n0:]:
        q.setdefault("qp", "act2_main")
    n1 = len(Q)
    act2_side_quests()
    act2_starsea_side_quests()
    for q in Q[n1:]:
        q.setdefault("qp", "act2_side")
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
