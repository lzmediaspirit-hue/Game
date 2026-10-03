"""The two sects' people (docs/architecture/npc_engine.md): the staff each sect keeps, from one role template a post
(ROLES), filled for the Jade Sect and the Cloud Sect (SECTS); the inner disciple, the two elders who teach you; the
watch post both sects keep at the Marsh Edge; the arena master who stands at both sects' courts."""
from content.npcs.spec import ROLE, extra, look, npc, place, role, staff as _staff, work

SECTS = {"jade": dict(key="jade", Sect="Jade", sect="jade_sect", dye="jade", weapon="sword"),
         "cloud": dict(key="cloud", Sect="Cloud", sect="cloud_sect", dye="cloud", weapon="staff")}
JADE, CLOUD = SECTS["jade"], SECTS["cloud"]

# A post's look, voice, services and work, the same in both sects but for the sect's own colour ({dye}), name ({Sect})
# and weapon ({weapon}). story.py's paired lists (STEWARDS, DEACONS...) give a post's quests to both.
ROLES = {
    "steward": role("{Sect} Sect steward", dict(hair="topknot:5", shirt="scholar:{dye}", pants="scholar:grey", shoes="folded"),
                    ["Service disciples sweep, carry and learn. In that order.", "Your bunk is in the dorm. Keep it tidy."],
                    ["Brooms don't sweep themselves."], loop="pray"),
    "weapon_master": role("Weapon master", dict(hair="short_knot", shirt="sleeveless:{dye}", pants="martial", shoes="boots", weapon="{weapon}"),
                          ["Try each weapon. Your hands will choose before your head does.", "A weapon is only your arm, longer."],
                          ["Again!"], loop="{weapon}"),
    "deacon": role("Mission deacon", dict(hair="topknot", shirt="disciple:{dye}", pants="scholar:{dye}", shoes="folded"),
                   ["Missions earn contribution. Contribution earns everything else.", "Five missions a day. The board refreshes at dawn."],
                   ["Missions posted!"], services=["missions", "shop:{key}_sect"], loop="read"),
    "hall_master": role("Training hall master", dict(hair="high_pony", shirt="disciple:{dye}", pants="martial:ink", shoes="boots"),
                        ["A technique is a question your meridians learn to answer.", "Practice twenty times. Then twenty more."],
                        ["Form! Form!"]),
    "librarian": role("Librarian", dict(hair="long_tied:1", shirt="scholar:grey", pants="scholar:{dye}", shoes="folded"),
                      ["Methods by rank. Manuals by contribution. Silence by law.", "Torn pages can be restored. Torn students less so."],
                      ["Shh."], services=["page:library", "page:workshop"], loop="write",
                      service_labels={"page:library": "Browse", "page:workshop": "Restore manuals"},
                      service_unlocks={"page:workshop": "research"}),
    "smith": role("Sect smith", dict(hair="short_knot:5", shirt="sleeveless:ink", pants="martial", shoes="boots"),
                  ["The sect forge answers to disciples with Qi in their hands.", "Common first. Earth when you've earned it."],
                  ["*clang*"], loop="hammer"),
    "formation_elder": role("Formation elder", dict(hair="flowing:1", shirt="scholar:{dye}", pants="scholar", shoes="folded", cape="solid"),
                            ["Lines on the floor, fuel in the nodes, intent in the centre.", "A good formation outlives its maker."],
                            ["Mind the lines."], services=["page:workshop", "page:arrays"], loop="read",
                            service_labels={"page:workshop": "Formations", "page:arrays": "Etch plates"},
                            service_unlocks={"page:workshop": "formations", "page:arrays": "array_plates"}),
    "physician": role("Sect physician", dict(hair="ponytail:3", shirt="cardigan:white", pants="scholar", shoes="slippers"),
                      ["Injured disciples, bitter medicine.", "A needle in the right place is worth a hundred pills."],
                      ["Next patient."], services=["page:workshop"], service_labels={"page:workshop": "Infirmary"},
                      service_unlocks={"page:workshop": "healing"}),
    "gardener": role("Sect gardener", dict(hair="short_knot:5", shirt="vneck:earth", pants="cuffed", shoes="slippers", hat="straw"),
                     ["Plant, water, wait. Harvest.", "Willow moss likes shade and gossip."], ["Grow, little ones."], loop="herbs"),
    "disciple_a": role("Outer disciple", dict(hair="ponytail", shirt="disciple:{dye}", pants="martial:{dye}", shoes="boots"),
                       ["The Heart Trial? Don't talk about the Heart Trial.", "I heard the elders fought a Hollow thing last winter."],
                       ["Morning, junior."], loop="sweep"),
}


def staff(post, sect, name, **kw):
    return _staff(post, ROLES, sect, name, **kw)


NPCS = [
    # The Jade Sect's staff, then the Cloud Sect's, post by post.
    staff("steward", JADE, "Steward Wei", at=[place("ja_gate_street", work=work(ROLE, [7, 16, "s"], [5.4, 14.8, "n"]))]),
    staff("weapon_master", JADE, "Master Kong",
          at=[place("ja_weapon_hall", work=work(ROLE, [10, 5, "s"], [11.8, 6.2, "s"], [8.4, 6.0, "se"])),
              place("ja_pavilion_rooftops", "npc_jade_wm_yard", work=work(ROLE, auto=2))]),
    staff("deacon", JADE, "Deacon Rui", at=[place("ja_gate_street", work=work(ROLE, [57, 15, "s"], [58.8, 14.2, "ne"]))]),
    staff("hall_master", JADE, "Master Lin", at=[place("ja_pavilion_rooftops", work=work("fists", auto=2))]),
    staff("librarian", JADE, "Librarian Zhu", at=[place("ja_library", work=work(ROLE, auto=1))]),
    staff("smith", JADE, "Smith Ouyang",
          at=[place("ja_weapon_hall", work=work(ROLE, [18.0, 6.6, "e", "anvil"], [18.9, 4.6, "ne", "forge"], [17, 5, "s"]))]),
    staff("formation_elder", JADE, "Elder Bian", at=[place("ja_east_terrace", work=work(ROLE, auto=1))]),
    staff("physician", JADE, "Physician Nan", at=[place("ja_east_terrace", work=work("herbs", auto=2))]),
    staff("gardener", JADE, "Gardener Ji", at=[place("ja_herb_terraces", work=work(ROLE, auto=2))]),
    staff("disciple_a", JADE, "Disciple Hao",
          at=[place("ja_gate_street", work=work(ROLE, [29, 15, "sw"], [27.4, 16.2, "w"], [30.8, 16.4, "s"]))]),
    staff("steward", CLOUD, "Steward Ruo", at=[place("cm_cliff_stair", work=work(ROLE, [7, 21, "s"], [8.4, 19.6, "n"]))]),
    staff("weapon_master", CLOUD, "Master Fei",
          at=[place("cm_weapon_hall", work=work(ROLE, [10, 5, "s"], [11.8, 6.2, "s"], [8.4, 6.0, "se"]))]),
    staff("deacon", CLOUD, "Deacon Heng", at=[place("cm_cliff_stair", work=work(ROLE, [48, 22, "s"], [46.8, 21.0, "n"]))]),
    staff("hall_master", CLOUD, "Master Qiao", at=[place("cm_sword_court", work=work("staff", auto=2))]),
    staff("librarian", CLOUD, "Librarian Pei", at=[place("cm_cloud_library", work=work(ROLE, auto=1))]),
    staff("smith", CLOUD, "Smith Tan",
          at=[place("cm_weapon_hall", work=work(ROLE, [18.0, 6.6, "e", "anvil"], [18.9, 4.6, "ne", "forge"], [17, 5, "s"]))]),
    staff("formation_elder", CLOUD, "Elder Lou", at=[place("cm_array_court", work=work(ROLE, auto=1))]),
    staff("physician", CLOUD, "Physician Qu", at=[place("cm_array_court", work=work("cook", auto=1))]),
    staff("gardener", CLOUD, "Gardener Ren", at=[place("cm_array_court", work=work(ROLE, auto=2))]),
    staff("disciple_a", CLOUD, "Disciple Ling",
          at=[place("cm_cliff_stair", work=work(ROLE, [22, 22, "sw"], [20.4, 23.0, "w"], [23.8, 23.2, "s"]))]),

    npc("jade_disciple_b", "Disciple Yue", "Inner disciple",
        look("flowing:4", "disciple:jade", "martial:jade", "boots", weapon="sword"),
        ["Inner disciples get the good retreat rooms.", "Qi Unfurling feels like breathing with your whole skin."],
        ["Focus."], at=[place("ja_gate_street", work=work("sword", [40, 17, "s"], [41.8, 17.6, "se"], [38.4, 18.2, "s"]))]),
    npc("elder_hu", "Elder Hu", "Jade Sect elder", look("long_tied:1", "scholar:jade", "scholar:ink", "folded", cape="solid"),
        ["The river does not hurry, yet it carves the valley.", "Come to me when you hit a wall. Walls are my speciality."],
        ["Hmm."], tree="mentor", sect="jade_sect",
        concealed=["You can hide your realm from bandits, child. Not from the one who taught you to breathe."],
        at=[place("ja_elder_hu_peak", work=work("meditate", [24, 13, "s"])), place("rm_marsh_edge", "npc_elder_hu_marsh")]),
    npc("elder_sung", "Elder Sung", "Cloud Sect elder", look("topknot:1", "scholar:cloud", "scholar:ink", "folded", cape="solid"),
        ["The wind does not fight the mountain. It goes over.", "Bring me your walls. I'll show you the sky above them."],
        ["Hm-hm."], tree="mentor", sect="cloud_sect",
        concealed=["A cloud can look like a small thing from below. I am not below you. Put the mask away when we talk."],
        at=[place("cm_elder_sung_peak", work=work("meditate", [31, 5, "s"])), place("rm_marsh_edge", "npc_elder_sung_marsh")]),
    # Decision 42: the watch post both sects keep at the Marsh Edge, by its transfer array; the grey has touched its two
    # watchers, and Mei Qing tends them there (Mei Qing's Errand).
    npc("watcher_bo", "Watcher Bo", "Jade Sect watcher", look("short_knot:2", "disciple:jade", "martial:ink", "boots"),
        ["It came up out of the reeds like smoke. Then my arm went grey to the elbow.",
         "Mei Qing says it'll close. It had better. I'm left-handed."], ["Ow."],
        at=[place("rm_marsh_edge", work=work("watch", auto=2))]),
    npc("watcher_su", "Watcher Su", "Cloud Sect watcher", look("ponytail:4", "disciple:cloud", "martial:ink", "boots"),
        ["Our elders and yours keep this post together now. The grey doesn't care whose robe it eats.",
         "The array at our feet goes home to either sect. Stand in it and see."], ["Watch the reeds."],
        at=[place("rm_marsh_edge", work=work("watch", auto=2))]),
    npc("arena_master", "Arena Master Quan", "Arena", look("short_knot", "sleeveless:crimson", "martial", "boots", cape="solid"),
        ["Three wins for the qualifier. No excuses.", "The Valley Tournament crowns one champion a year."], ["Next bout!"],
        services=["spar:sparring_disciple"], service_labels={"spar:sparring_disciple": "Arena match"},
        at=[place("ja_east_terrace", work=work("watch", auto=2)), place("cm_sword_court", "npc_arena_cm", work=work("watch", auto=2))]),
]

# A service disciple sweeping the Jade gate street, a Cloud pupil at sword drill in the court.
EXTRAS = [
    extra("x_ja_sweeper", "ja_gate_street", look("ponytail:3", "disciple:jade", "martial:jade", "boots"),
          work("sweep", [47, 19.5, "w"], [45.4, 20.2, "w"], [48.6, 20.6, "sw"])),
    extra("x_cm_pupil", "cm_sword_court", look("high_pony", "disciple:cloud", "martial:cloud", "boots", weapon="sword"),
          work("sword", [24, 15, "s"], [26, 15.6, "s"])),
]
