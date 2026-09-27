# Technique plan · hundreds of arts per weapon and path, one tree per element

This page plans Jade River's techniques at the scale the user asked for (`docs/roadmap_master_ui.md` §6, decisions 11
and 12): "a huge skill tree for each element in its own separate tab", "a tab for techniques that can only be found on
special occasions like quests or monster drops or finding it in the game, like a lost cultivation system", and
"hundreds of skills for each weapon and cultivation path". It does eight things:

1. It counts the 56 techniques that exist today by element, weapon family, path, grade, ring and source, with the
   systems around them and the gaps (§1).
2. It sets the target: real numbers per element, family, path and act, through Acts I–V and the Epilogue (§2).
3. It says how four thousand arts stay distinct and worth having: a grammar in data (form × element × family × path ×
   ring) with hand-named keystones, names from word lists, icons from the Style A emblem grammar, and VFX tiers,
   moments and poses from what exists (§3).
4. It designs the element trees: nodes, rings, sectors, keystones, prerequisites, the Realisations that pay for them,
   respec, how families and paths branch inside a tree, how the Dao and the sect trees relate, and how every existing
   art and save moves in (§4).
5. It designs Lost Arts: found only in the world, unknown until found (only counted before; decision 19), with six lost
   lineages, tied to P7b's sources and the world plan's hidden maps (§5).
6. It says how so many arts avoid power creep, the loadout limits, and how the stat scaling research's Might and par
   numbers set the budgets (§6).
7. It sizes the data and names the headless tests that keep it valid (§7).
8. It orders the build across v1.2.x, v1.3, v1.4 and v1.5 (§8), then lists the open questions with recommendations and
   the decisions taken.

Counts are taken from `data/` at commit 57e4d30: `techniques.json` (56 rows), `daos.json` (28), `inner_arts.json`
(10), `stances.json` (9), `combos.json` (6), `secret_arts.json` (12), `sect_roles.json`, `weapon_families.json`,
`elements.json`, `grades.json`, `stats.json`, `quests.json`, `shops` in `tools/data/economy.py`, and the rules in
`progression_rules.gd`, `progression_authority.gd` and `combat_rules.gd`. The worked examples use Tester, the
valley_run character, at checkpoint `ls6_end` (Sphere Lord 3, Level 98), read from the save on 2026-09-27. Nothing here
changes `scripts/`, `data/` or `art/`; §8 says what the build changes.

Every name on this page that is not already in the data is new and original to Jade River. The two mockups that go with
it are `docs/mockups/06_techniques_element.png` (the Water tab) and `docs/mockups/06_techniques_lost.png` (Lost Arts).

---

## 1. Today's counts

### 1.1 By element

`elements.json` has the five phases (wood, fire, earth, metal, water), their children (wind and thunder of wood, ice
and tide of water, lava of fire, crystal and sand of earth, star and blade of metal) and the neutral keys (space, time,
soul, life and death, hollow, none). Techniques use nine of them.

| Element | Techniques | Of which learned from a library or hall | Element Dao |
|---|---|---|---|
| None (Formless) | 11 | 5 | — |
| Wood | 10 | 4 | Wood (valley cap 5) |
| Wind | 7 | 4 | Wind (5) |
| Metal | 7 | 2 | Metal (2) |
| Water | 5 | 2 | Water (5) |
| Earth | 5 | 4 | Earth (5) |
| Fire | 5 | 0 | Fire (2) |
| Soul | 5 | 0 | Soul (3; its tiers 1–3 teach Sense Lock, Phantom Double, Soul Search) |
| Thunder | 1 | 0 | Thunder (2) |
| **Total** | **56** | **21** | 8 element Daos, plus Space (six tiers in the Lantern Star Field) |

Thunder has one art (Thunder Dao Arc); Fire and Soul have none a library teaches.

### 1.2 By weapon family

`weapon_families.json` has twelve rows (fists and gauntlets share the Fist Dao and every technique). v1.3 adds four
(dual blades, rope dart, whip, umbrella; `docs/item_plan.md` decision 1). "Any" is a free-hand art: a palm, a Qi art or
a buff that works whatever is held.

| Family | Dao | Techniques | Names |
|---|---|---|---|
| Any (free hand) | by element or path | 24 | Flowing Palm, Rising Tide, Vine Snare, Stone Skin, Gale Step, Ember Burst, Still Water Focus, Cloud Descent, Mirror Mind Spike, Soul Lantern Ward, Sense Lock, Phantom Double, Soul Search, Crimson Palm, Blood River Slash, Sanguine Lotus, Golden Body, Venom Needles, Miasma Palm, Upright Glyph, Benevolent Script, Rite Seal Script, Blood Burning, Glimpse of Heaven |
| Jian | Sword | 5 | Cloudpiercing Stroke, Willow Leaf Parry, Crescent Arc, Sword Release, Sword Swarm |
| Short blade | Blade | 4 | Reedcutter Slash, Shadow Flick, Flying Blades, Shadowstep Cut |
| Staff | Staff | 4 | Riverstone Sweep, Bell Toll Strike, Earthshaker Wave, Mountain Shaker |
| Spear | Spear | 3 | Jade Thrust, Dragon Tail Sweep, Spear Lance |
| Bow | Bow | 3 | Twin Reed Shot, Pinning Arrow, Rain of Reeds |
| Bell | Music | 3 | Stilling Peal, Qi Seal Toll, Warden's Call |
| Fists | Fist | 2 | Tiger Rush, Palm Wave |
| Heavy sabre | Blade | 2 | Mountain Cleaver, Thunder Dao Arc |
| Fan | Fan | 2 | Gale Fan, Returning Crane Fan |
| Flute | Music | 2 | Reed Song, Clear Heart Melody |
| Brush | Brush | 2 | Splashed Ink, Cursive Storm |

Ten families have five or fewer. A jian user at Level 98 can learn 5 jian arts and 24 free-hand ones.

### 1.3 By path

S48 made paths layers, never class locks: the Body ladder (Copper Body lets a `body` art spend HP), the Blood path
(opt-in at alignment −20 or lower from Heart Tempering 1), the Buddhist path (a vow held), the Poison path (knowing a
poison art opens the Poison Body) and, in v1.2, the Confucian path (alignment 20 or higher, from Will Manifest; never
beside the Blood path). Each row carries a flag for its path.

| Path | Flag | Techniques | Names |
|---|---|---|---|
| Orthodox (no layer) | — | 44 | the rest, including the Soul line |
| Body | `body` | 3 | Tiger Rush, Stone Skin, Mountain Shaker |
| Blood | `blood_path` | 3 | Crimson Palm, Blood River Slash, Sanguine Lotus (Blood Burning carries no flag; it is the Blood Dao teacher's secret art) |
| Confucian | `confucian_path` | 3 | Upright Glyph, Benevolent Script, Rite Seal Script |
| Poison | `poison_path` | 2 | Venom Needles, Miasma Palm |
| Buddhist | `needs_vow` | 1 | Golden Body |

P7b tags gear by archetype with a path (`docs/item_plan.md` §2.2): body cultivator `body_ladder`, sword Dao
`sword_dao`, alchemist `poison`, beast tamer `beast_taming`, formation master `confucian`, musician `buddhist`, and the
Blood tag on two named weapons. §4.6 maps these onto the trees.

### 1.4 By grade, ring and act

Today's grade comes from the teaching realm (`techniques.py:199-201`): Common for Bone Forging and Qi Kindling, Earth
for Qi Unfurling and Heart Tempering, Heaven for every later realm, worth +0, +10 and +20% on the multiplier. P6's
`vfx.tier` splits the same bands by zone (`docs/moments_design.md` §5.1). This plan uses the item grade bands
(`stats.json` `grade_bands`) as **rings**, one per grade, so a technique's grade colour matches the gear of its band:

| Ring | Grade | Levels | Act | Techniques today | `vfx.tier` |
|---|---|---|---|---|---|
| 1 | Common (and Plain) | 0–18 | I | 16 | 1 |
| 2 | Earth | 19–36 | I | 22 | 2 |
| 3 | Heaven | 37–54 | I | 8 | 3 |
| 4 | Mystic | 55–63 | I | 1 (Glimpse of Heaven) | 3 |
| 5 | Spirit | 64–72 | II | 0 | 4 |
| 6 | Sage | 73–81 | II | 1 (Blood Burning) | 4 |
| 7 | Sovereign | 82–90 | III | 2 (Upright Glyph, Benevolent Script) | 5 |
| 8 | Will | 91–99 | III | 6 (the Bastion's brush and bell arts, Cursive Storm, Rite Seal Script) | 5 |
| 9 | Sphere | 100–108 | IV | 0 | 6 |
| 10 | Law | 109–120 | IV | 0 | 6 |
| 11 | Monarch | 121–140 | V | 0 | 7 |
| 12 | Inner Heaven | 141–165 | V | 0 | 7 |
| 13 | Genesis | 166+ | Epilogue | 0 | 7 |

By act: Act I 47, Act II 1, Act III 8. By today's grade word: Common 16, Earth 22, Heaven 18.

### 1.5 By source

| Kind | Sources (the `source` field) | Techniques |
|---|---|---|
| Training hall (the entry choice) | `training_hall`, `training_hall_jade`, `training_hall_cloud` | 6 |
| Mission Hall library (contribution, by sect rank) | `library_1` 9, `library_2` 3, `library_3` 1, `cloud_library` 1, `mission_hall` 1 (Golden Body) | 15 |
| Quest from a teacher | `after_the_cleansing` 8 (a choice by family), `brothers_in_arms`, `above_the_mist`, `a_lake_inside`, `the_mentors_gift`, `a_wider_sky` (Elder Hu), `blood_remembers` (Matriarch Tie Yun) | 14 |
| Shop | `night_peddler` 5 (Peddler Shao, after dark, +5 sin a purchase), `bastion_armoury` 5 (Splashed Ink also from the quest Brush and Bell), `lanternwright_han` 3 (Upright Glyph also from The Written Word) | 13 |
| Dao tier | `sword_dao_3`, `sword_dao_5`, `soul_dao_1`–`3` | 5 |
| World drop (a manual item) | the Mudwater Manual (Big Toad Tan, always; Lieutenant Kuai 30%), the Drowned Shrine's manual, the gorge bandit adept's (3%); the Research craft restores torn manuals into the last two | 3 |

Sources have no player-facing names (open item in `docs/mockups/README.md`); an unlearned node's "where from" line
needs them (§8 step 1).

### 1.6 The systems around techniques

| System | Today | Where |
|---|---|---|
| Slots | 2, 4, 6, then 8 (unlocks `technique_slots_2`, `_4`, `technique_page_2`, `technique_slots_8`); the HUD shows four on one ring and a 1/2 swap for the second four; each weapon keeps its own bar (S47 dual loadout) | `ProgressionRules.technique_slot_count`, `_on_loadout_swapped` |
| Mastery | Tiers 1–6; tier n needs 100 × 2^(n−1) practice; tiers 3→4→5→6 each take a Manual Page (from `technique_slots_8`); +8% damage and −5% Qi cost a tier | `mastery_needed`, `rank_up_technique`, `stats.json` `technique_cost` |
| Grades | Common, Earth, Heaven: +0, +10, +20% | `technique_grade_bonus` |
| Daos | 28 rows: 9 weapon, 8 element, 5 craft, 6 rare; tiers at 100, 300, 800, 2,000, 5,000 and 12,000 insight, capped by zone; +5% damage a tier, −10% Qi cost from tier 2; a tier can teach an art | `daos.json`, `apply_insight` |
| Inner Arts | 10 passives (two are legacies: Elder Hu's Lotus Mind, Elder Sung's Drifting Cloud); 2 slots at Qi Unfurling 1, 3 at Heart Tempering 1, 4 at Spirit Awakening 1 | `inner_arts.json`, `active_inner_arts` |
| Stances | 9, one per family, held only with that weapon | `stances.json`, `active_stance` |
| Combos | 6 pairs of named arts inside a 1 s window | `combos.json`, `combo_for` |
| Secret Arts | 12, most of them movement arts taught by guided quests | `secret_arts.json` |
| Sect tree | 3 branches of 5 nodes, bought with contribution; the sect's three signature arts get a role variant (Jade: Flowing Palm, Palm Wave, Rising Tide; Cloud: Jade Thrust, Spear Lance, Dragon Tail Sweep) | `sect_roles.json`, `sect_tree_flag`, `signature_variant` |
| Research | A torn manual and restoration ink at a librarian's bench give Rain of Reeds, Ember Burst or Manual Pages | `crafts.py` `research` |

### 1.7 The gaps

- **Volume.** 56 arts across 12 families and 9 elements, 47 of them in Act I; Act II has one, Act III eight, nothing
  above the Will band (Level 99) although the grade ladder runs to Inner Heaven (Level 165) and Genesis.
- **Shape.** No tree: techniques are a flat list, nothing leads from one to the next, and nothing is chosen at the cost
  of something else. There is no respec because there is nothing to spend.
- **Found arts.** Three world drops and two legacies. Nothing is hidden in a place, on a stele or in a ruin, and an art
  not yet found is invisible.
- **Presentation.** Every icon is hand-drawn (66 marks on one emblem), there is no `vfx` block yet (P6), and sources have
  no player-facing names.

---

## 2. The target

### 2.1 What counts

A **technique** (an art) is a row in `techniques.json` that can be put in a slot. Passive tree nodes, Inner Arts,
stances and Secret Arts are counted apart. The target is set per **element tree**, **family**, **path** and **act**,
and every number below comes from the rules in §3 and §4 (a script computed them, so the sums agree).

The shape that gives the numbers:

- **Eleven element trees**: the nine elements techniques use today (Wood, Fire, Earth, Metal, Water, Wind, Thunder,
  Soul and Formless, the `none` element), plus **Space** from ring 7 (its Dao opens in the Lantern Star Field) and
  **Time** from ring 9 (its Dao opens in v1.3).
- **Sixteen sectors** in each tree: the fifteen weapon families of v1.3 and the free hand. Until v1.3 a tree has
  twelve.
- **Thirteen rings**, one per grade band (§1.4), grouped by act: Act I rings 1–4, Act II 5–6, Act III 7–8, Act IV
  9–10, Act V 11–12, the Epilogue 13.
- In each **cell** (a sector's ring in one tree): one **orthodox art**, and from ring 2 one **path art** of one of the
  five paths.
- At the outer edge of each act's rings: four **keystones** per tree, one for each kin group of four sectors.

### 2.2 Per element

| Tree | Rings | Orthodox | Path | Keystones | Arts | Act I | II | III | IV | V | Epilogue |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Wood, Fire, Earth, Metal, Water, Wind, Thunder, Soul, Formless (each) | 1–13 | 208 | 192 | 24 | **424** | 116 | 68 | 68 | 68 | 68 | 36 |
| Space | 7–13 | 112 | 96 | 16 | **224** | — | — | 52 | 68 | 68 | 36 |
| Time | 9–13 | 80 | 64 | 12 | **156** | — | — | — | 52 | 68 | 36 |
| **All eleven** | | **2,064** | **1,888** | **244** | **4,196** | 1,044 | 612 | 664 | 732 | 748 | 396 |

About 40 **Dao arts** sit on the Dao trunks on top of this (§4.7; 5 exist), and **114 Lost Arts** off the trees (§5).
With them the game holds about **4,350 arts** through v1.5, against 56 today.

### 2.3 Per weapon family

Every family has the same share: one orthodox art per ring in every tree it appears in, one path art per ring from
ring 2, and the keystones of its kin group.

| Family | Orthodox | Path arts | Own arts | Kin keystones it can use | **Usable** | Act I | II | III | IV | V | Epilogue |
|---|---|---|---|---|---|---|---|---|---|---|---|
| each of the 16 | 129 | 118 | 247 | 61 | **308** | 63 | 36 | 39 | 43 | 44 | 22 |

The sixteen: free hand, fists (and gauntlets), flute, bell · jian, dual blades, short blade, heavy sabre · spear,
staff, whip, rope dart · bow, fan, umbrella, brush. The dots mark the four **kin groups** (Body and Voice, Edges, Reach,
Distance and Ink) that share keystones. Free-hand arts work with any weapon, so a jian user can reach 247 jian arts,
247 free-hand arts and 61 + 61 keystones: about 600 arts to choose eight from.

### 2.4 Per cultivation path

The five path layers get the path arts; the orthodox trunk is everyone's.

| Path | Path arts | Act I | II | III | IV | V | Epilogue | Families with it as an affinity (three rings a sector, not two) |
|---|---|---|---|---|---|---|---|---|
| Body | 376 | 86 | 57 | 59 | 69 | 68 | 37 | fists, heavy sabre, spear, staff, whip, rope dart |
| Blood | 365 | 84 | 57 | 56 | 65 | 70 | 33 | free hand, jian, dual blades, short blade, heavy sabre |
| Buddhist | 385 | 88 | 55 | 67 | 70 | 69 | 36 | free hand, fists, flute, bell, staff, umbrella, brush |
| Poison | 378 | 85 | 63 | 58 | 63 | 73 | 36 | flute, dual blades, short blade, whip, rope dart, bow, fan |
| Confucian | 384 | 89 | 56 | 64 | 69 | 72 | 34 | bell, jian, spear, bow, fan, umbrella, brush |
| Orthodox (no layer) | 2,064 | 576 | 288 | 320 | 352 | 352 | 176 | every family, every ring |

Each path has between 365 and 386 arts, and 55 or more in every act. The Soul line stays what it is today: the Soul
element and its Dao, not a layer.

### 2.5 Per act and per build

| Act | Version it is written for | Arts | Cumulative |
|---|---|---|---|
| I · Jade River Valley (rings 1–4) | v1.2.x | 1,044 | 1,044 |
| II · Azure Expanse (5–6) | v1.2.x | 612 | 1,656 |
| III · Lantern Star Field (7–8, and Space 7–8) | v1.2.x | 664 | 2,320 |
| IV · Star Frontier (9–10, and Time 9–10) | v1.3 | 732 | 3,052 |
| V · Outer Heavens (11–12) | v1.4 | 748 | 3,800 |
| Epilogue · World Genesis (13) | v1.5 | 396 | 4,196 |

What lands in each build, since v1.3's four families come with their rings 1–8 back-filled (open question 5):

| Build | Arts | What |
|---|---|---|
| v1.2.x | 1,768 | Acts I–III in twelve sectors; Space rings 7–8 |
| v1.3 | 1,284 | Act IV for every tree; the four new families' rings 1–8; the Time tree |
| v1.4 | 748 | Act V |
| v1.5 | 396 | The Epilogue ring |

A v1.2.x tree has 192 arts on 343 nodes; a finished tree has 424 arts on 751 nodes (§4.2).

---

## 3. How so many stay distinct and worth having

### 3.1 The grammar

An art is built in data from five parts, and only the keystones, the Dao arts and the Lost Arts are designed by hand:

```text
art = FORM (one of 24) × FAMILY (who draws it) × ELEMENT (its verbs) × PATH (a modifier, or none) × RING (a grade budget)
```

- The **form** says what the art does: its shape, role, hits, targets, cooldown and the pose it borrows. There are 24.
- The **family** draws the form with its own reach, pose and weapon mark; each family can draw 14 to 17 of the 24
  (§3.2), more than the 13 rings a tree asks of it.
- The **element** says what the art does besides damage: its status, a secondary verb, its particles, its colour and
  its name's images (§3.3).
- The **path** changes the cost and adds one rule (§3.4). Path arts exist only as path arts; an orthodox art has no
  path.
- The **ring** sets the grade, the budget, extra targets and the `vfx.tier` (§3.5).

`tools/data/technique_grammar.py` holds the tables; `tools/data/technique_gen.py` walks the cells of each tree and
writes one row per art, deterministically, honouring hand rows first (the 56 existing arts, the keystones, the Dao
arts). A generated row is an ordinary `techniques.json` row, read by today's `CombatAuthority`.

### 3.2 The 24 forms

Ring-1 numbers come from the existing arts of each form, so the old rows sit on the line. Poses are the existing
actions only (`parts.json` `_actions`: `punch_1`–`3`, `punch`, `swing_1`–`3`, `thrust_1`–`3`, `attack`, `bow`, `jump`,
`meditate`; `meditate_burst` resolves to the family's first combo action). No form needs a new body pose (`AGENTS.md`).
The pose column names the usual action; a family without it uses the matching step of its own combo (the bow always
`bow`, the flute always `attack`).

| # | Form | Role | `vfx.shape` | Type | Hits × targets | Ring-1 mult | Cooldown s | QI | Pose | Families | Today |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Strike | burst | strike | physical | 1 × 1 | 1.50–1.80 | 6 | 12 | combo 3rd | every family | Tiger Rush, Mountain Cleaver |
| 2 | Flurry | burst | strike | physical | 2–5 × 1 | 0.55–0.65 a hit | 3–5 | 8–12 | `punch` or combo 1st | free hand, fists, jian, dual blades, short blade, spear, staff, whip, brush | Flowing Palm |
| 3 | Thrust | line | strike or wave | physical | 1 × 2 in a line | 1.40–1.70 | 4 | 10 | `thrust_1` / `_3` | fists, jian, dual blades, short blade, spear, staff, rope dart, umbrella | Jade Thrust |
| 4 | Lunge | close the gap | strike | physical | 1 × 1–8 passed | 1.50–1.80 | 6 | 12 | `thrust_3` / `punch_2` / `jump` | free hand, fists, jian, dual blades, short blade, heavy sabre, spear, staff, whip, rope dart | Tiger Rush, Gale Step |
| 5 | Sweep | crowd | ring | physical | 1 × 6 | 1.00–1.40 | 4–6 | 10–12 | combo 3rd | fists, bell, jian, dual blades, heavy sabre, spear, staff, whip, rope dart, fan, umbrella | Riverstone Sweep, Dragon Tail Sweep |
| 6 | Arc | pierce | bolt | qi | 1 × 8 | 0.90–1.20 | 5 | 14 | `swing_2` / `punch_2` | free hand, fists, jian, dual blades, heavy sabre, spear, whip, bow, fan, brush | Crescent Arc, Palm Wave |
| 7 | Volley | ranged | bolt | physical | 2–3 × 1 | 0.70–0.90 each | 3–5 | 8–12 | `bow` / `swing_1` | flute, short blade, rope dart, bow, fan, umbrella | Twin Reed Shot |
| 8 | Rain | area | rain | physical or qi | 4–5 × 5 | 0.45–0.60 each | 8 | 18–22 | `bow` / `swing_3` / `meditate` | free hand, flute, jian, spear, bow, fan, umbrella, brush | Rain of Reeds, Cursive Storm |
| 9 | Pillar | one foe | pillar | soul or qi | 1 × 1 | 1.50–1.80 | 9–15 | 10–35 | `meditate` | free hand, flute, bell, jian, bow, brush | Mirror Mind Spike, Glimpse of Heaven |
| 10 | Wave | line area | wave | qi | 1 × 8 | 1.10–1.40 | 6 | 14 | combo 3rd / `punch_3` | free hand, fists, flute, bell, jian, heavy sabre, spear, staff, whip, bow, fan, brush | Earthshaker Wave |
| 11 | Burst | around you | ring | qi | 1 × 8 | 1.40–1.70 | 9 | 20 | `meditate` | free hand, fists, flute, bell, heavy sabre, staff, whip, rope dart, bow, fan, umbrella, brush | Ember Burst, Rising Tide |
| 12 | Seeker | homing | bolt | qi | 3 × 3 | 0.50–0.70 each | 5 | 12 | `attack` / `swing_1` | free hand, flute, jian, short blade, whip, rope dart, bow, brush | Flying Blades, Reed Song |
| 13 | Return | thrown | bolt | physical | 2 × 8 | 0.80–1.00 | 6 | 14 | `swing_3` | bell, dual blades, short blade, heavy sabre, spear, rope dart, fan, umbrella | Returning Crane Fan |
| 14 | Snare | control | ring or wave | qi | 1 × 3 | 0.60–0.80 + control 1.5–2 s | 10 | 14 | `meditate` / combo 1st | free hand, fists, flute, bell, short blade, spear, staff, whip, rope dart, bow, fan, brush | Vine Snare, Pinning Arrow |
| 15 | Counter | stance | strike | stance | counter 2.00 | — | 8 | 10 | combo 1st | fists, flute, bell, jian, dual blades, short blade, heavy sabre, spear, staff, whip, rope dart, umbrella | Willow Leaf Parry |
| 16 | Ward | self | domain | buff | — | — | 20–30 | 15–18 | `meditate` | free hand, fists, flute, bell, heavy sabre, staff, fan, umbrella, brush | Stone Skin, Still Water Focus, Soul Lantern Ward |
| 17 | Chorus | allies | domain | buff | — | heal 4–6% | 20–24 | 16–24 | `attack` / `meditate` | free hand, flute, bell, fan, umbrella, brush | Clear Heart Melody, Warden's Call |
| 18 | Blink | behind | strike | physical | 1 × 1 | 2.00–2.60 | 12 | 20 | `thrust_1` | free hand, fists, jian, dual blades, short blade, rope dart, bow, fan | Shadowstep Cut |
| 19 | Plunge | from above | ring | physical | 1 × 8 below | 1.60–2.00 | 8 | 20 | `jump` | free hand, fists, bell, jian, dual blades, short blade, heavy sabre, spear, staff, whip, rope dart, bow, umbrella | Cloud Descent |
| 20 | Release | the weapon flies | strike | release | 0.60 × 1.5 a second for 8 s | 0.60 | 12 | 20 | combo 1st | jian, dual blades, heavy sabre, spear, fan, umbrella | Sword Release |
| 21 | Swarm | constructs orbit | strike | swarm | 0.30 a strike | 0.30 | 30 | 30 | `meditate` | flute, jian, dual blades, short blade, bow, brush | Sword Swarm |
| 22 | Domain | a field for 8 s | domain | qi | 8 ticks × up to 8 | 0.30 a tick | 16 | 22 | `meditate` | free hand, flute, bell, jian, heavy sabre, staff, whip, bow, fan, umbrella, brush | (new) |
| 23 | Seal | debuff | strike or bolt | qi or soul | 1 × 1–3 | 0.70–0.85 + seal 3 s | 8 | 16 | combo 2nd | free hand, fists, flute, bell, dual blades, short blade, heavy sabre, staff, whip, rope dart, bow, umbrella, brush | Qi Seal Toll, Stilling Peal |
| 24 | Echo | strikes again | strike | physical | 1 × 1, then 50% at 1 s | 1.20–1.50 | 7 | 12 | combo 2nd | free hand, fists, flute, bell, jian, dual blades, short blade, heavy sabre, spear, staff, whip, rope dart, bow, brush | (new) |

### 3.3 The element's verbs

The element fixes the damage element (and so the cycle, the Laws and the resistances already in `CombatRules`), the
status a form applies, a second verb for the forms that carry one, the particles (`docs/moments_design.md` §5.6) and
the image words of the name (§3.8).

| Element | Status (control forms) | Second verb (other forms) | Particles | Disc colour |
|---|---|---|---|---|
| Water | slow 20% for 2 s | pull 40 toward you, or heal 2% of damage dealt | square | #32bed1 |
| Wood | root 1.5–2 s | a bloom that ticks 1% a second for 4 s; thorns return 10% of melee damage | square | #67d67a |
| Fire | burn 5% for 3 s | the burn spreads to one neighbour | ember | #f08a3c |
| Earth | stun 0.6–0.8 s | knockback 80; Vulnerable for 3 s | square | #c9a060 |
| Metal | Sundered (armour break) 4 s | +10% crit; pierce one more | shard | #d8dde0 |
| Wind | knock-up 0.6–0.8 s | +15% reach; +10% move speed for 3 s | square | #cfe8e6 |
| Thunder | shock (+20% taken, 0.6 s stun) | chains to two more foes at 50% | shard | #e8d24c |
| Soul | confusion 20% for 2 s | ignores armour; costs Soul | ring | #9b78d1 |
| Formless | none | +10% multiplier and +10% penetration: the plain form, strongest in raw numbers | by family | #e8e1cf |
| Space | pulled to a point | ignores 10% resistance; a short blink | square | #8f7ae0 |
| Time | slow 30% for 2 s | echoes: the art strikes again at 30% after 1 s | ring | #d6f5ff (proposed) |

A form's damage budget is the same in every element; the verb is the difference. The balance check (§6.4) prices the
verb in, so a Water Arc with a pull and a Formless Arc with +10% land on one line.

### 3.4 The path's modifier

| Path | Gate (today's rule) | Cost | Rule added | Budget |
|---|---|---|---|---|
| Body | Copper Body or higher | may spend HP when Qi runs short (the `body` flag) | knockback immune while it plays; +10% knockback | +10% damage |
| Blood | walking the Blood path | 5–15% of max HP (blood essence pays first) | lifesteal counts double (`blood_art_lifesteal_mult`) | +25% damage |
| Buddhist | a vow held | Composure instead of Qi | a shield of 6% max HP, or heals allies | −10% damage |
| Poison | a poison art known opens the Poison Body | as orthodox | poison 2–3% of max HP a second for 5–6 s | −20% up front, the poison makes it back |
| Confucian | walking the Confucian path | as orthodox | half the multiplier rides on Insight (`insight_scale` 0.5); writes a glyph that lingers 2 s | ±0 |

A path art takes its path's favoured form when the family can draw it (Body: Strike, Wave, Lunge; Blood: Lunge,
Strike, Burst; Buddhist: Ward, Chorus, Domain; Poison: Seeker, Snare, Volley; Confucian: Pillar, Domain, Seal), else the
family's nearest form of the same role.

A path art on a ring below the one where its path can first be walked (a Confucian art on ring 3, say) is one of the
path's **foundations**: it can be realised the day the path is walked.

### 3.5 The ring's budget

| Ring | Grade bonus | Form budget (the par main art's multiplier) | Extra targets | Reach | `vfx.tier` |
|---|---|---|---|---|---|
| 1–4 | +0, +10, +20, +20% | rises about 1.2 → 1.5 → 2.0 → 2.2 as heavier forms open | — | the family's reach | 1, 2, 3, 3 |
| 5–8 | +20% | flat, about 2.2 | +1 from ring 5 | +2% a ring, within S43's family caps | 4, 4, 5, 5 |
| 9–13 | +20% | flat, about 2.2 | +2 from ring 9 | +2% a ring | 6, 6, 7, 7, 7 |

The grade bonus is the stat scaling research's skill-bucket grade (`docs/research/stat_scaling_research.md` §6.3):
today's Common, Earth and Heaven values, +0, +10 and +20%, with every ring from 3 on at +20%. No existing art changes
strength. Rings past Act I bring new forms, targets, reach and verbs, not a bigger multiplier: the realm's growth is
Might's (×1.30 a great realm), and the growth of a technique over a basic blow is mastery's and the Dao's (§6.1).

### 3.6 Rules that keep arts distinct

`data_validation` checks each of these on every build:

1. Within one tree, a sector's thirteen rings use thirteen different forms.
2. Within one family, at most two trees put the same form on the same ring, so the eleven versions of a family's ring
   are at least six different forms (a family has 14 to 17 to choose from).
3. Two neighbouring rings of a sector differ in role (burst, area, control, self, allies, movement).
4. No two arts share a name; no art's name is an item's, a place's, an NPC's, a title's or a realm's.
5. Every art's expected damage per Qi and per cooldown second is within ±10% of its form's line for its ring, verbs
   included (§6.4).
6. Every kin group's keystone in an act uses a keystone template that no other keystone of that tree and act uses.

### 3.7 Keystones: the hand-named signature arts

Each tree has four keystones at the outer edge of each act's rings, one per kin group; realising one needs the four
ring-edge passages of its kin group lit on the way (any one of them is enough) and a **source**: a teacher, a trial or
a sect library's top floor, the way today's quest arts are taught. A keystone is a template plus the element's verb
plus one rule of its own:

| Template | What it is | Today's model |
|---|---|---|
| Constructs | things of the element that fight beside you for a time | Sword Swarm |
| Field | a domain that changes a rule inside it | (new) |
| Avatar | a form you take for 8–12 s | Golden Body |
| Finisher | spends a status on a foe for one large hit | (new) |
| Mirror | an image or an echo that draws or repeats | Phantom Double |
| Procession | every art of the kin group in this element gains the verb while it lasts | (new) |

The Water tree's 24, as the pattern for the rest (the other trees' keystones are written with their acts in §8):

| Act | Body and Voice | Edges | Reach | Distance and Ink |
|---|---|---|---|---|
| I | **Hundred Springs Rising** (Field: springs rise under foes for 6 s and slow them) · the Falls Pool night trial | **Nine Undertows** (Constructs: nine water blades circle you and pull what they cut) · a sect library's top floor | **Heron Stands in the Flood** (Avatar: rooted and unmovable, every parry sends a flood wave) · Hermit Yao | **Rain Over Nine Ferries** (Field: rain over the screen, foes slowed, allies healed 1% a second) · the Trial Tower, floor 30 |
| II | **Glacier Heart Mantle** (Avatar, Ice) | **Riptide Procession** (Procession) | **Tidal Bore Charge** (Finisher: spends Slow) | **Mirrorwater Downpour** (Field: rain that confuses) |
| III | **Star-Sea Undertow** (Field: pulls everything to a point) | **Returning Tide of Lanternfall** (Constructs) | **Leviathan's Breath** (Finisher) | **Harbour of Returning Waves** (Mirror: each art echoes once) |
| IV | **Deluge That Waters Worlds** (Field) | **Twin-Moon Tide Blade** (Mirror) | **Current Under the Sunken Throne** (Procession) | **Rain on Six Worlds** (Constructs: rain-spirits) |
| V | **Sea Between the Heavens** (Avatar) | **Tide Against the Grey** (Finisher: doubled on Hollowed foes) | **Wyrmspine Cascade** (Constructs) | **Relic-Salt Rain** (Field) |
| Epilogue | **The River Remembers** (Mirror: replays your last three arts) | **Headwater Mandate** (Procession) | **All Currents Return** (Finisher) | **The Last Rain of the Loom** (Field) |

### 3.8 Names

Names are built from word lists in `technique_grammar.py`, original and xianxia-flavoured, never copied from other
works. The builder picks words by a seeded hash of the art's cell, so a rebuild gives the same names.

**Patterns**

| Pattern | Used for | Examples |
|---|---|---|
| {Image} {Noun} | most arts | Undertow Crescent, Ripple Peal, Ember Needles |
| {Number} {Image} {Noun} | multi-hit forms (the number is the hits) | Three Ripple Cuts, Five Cinder Needles, Nine-Rain Sword |
| {Image}-{Verb}ing {Noun} | heavy and moving forms | Falls-Splitting Descent, Brook-Cutting Stroke, Stone-Rending Palm |
| {Creature} {Noun} | forms with a body | Heron Thrust, Kingfisher Lunge, Mantis Snare |
| {Noun} of the {Place-image} | rings 9 and above, keystones | Palm of the Deep Pool, Bell of the Drowned Moon |
| path epithet + image | path arts | Crimson Riptide, Vowbound Tide Hymn, Venom Shoal, Upright Undertow Script, Iron-Bone Breakwater |

**Image words by element** (rings 1–4 homely, 5–8 wild and far, 9–13 of laws and worlds):

| Element | Rings 1–4 | Rings 5–8 | Rings 9–13 | Creatures |
|---|---|---|---|---|
| Water | brook, ripple, spring, dew, ferry, current, undertow, eddy, rain, drizzle, mist, flood, falls, deep pool, whirlpool, tidal bore, backwater | glacier, hoarfrost, riptide, swell, shoal, maelstrom, star-sea, moon-tide, abyss | sea between worlds, headwater, the river of worlds, all currents | heron, kingfisher, carp, otter, turtle, eel, crab |
| Wood | reed, willow, bamboo, moss, root, thorn, vine, seedling, bark, sap, bloom, bramble | old pine, iron-bark, banyan, hanging moss, pollen-storm, deep forest | world-tree, first seed, orchard of worlds | mantis, stag, cicada, silkworm, tree frog |
| Fire | ember, spark, cinder, lamp, kiln, hearth, coal, smoke, wick, flare | pyre, magma, comet, sunscar, ash-wind, furnace | star-core, burning law, first flame | firefly, red kite, cinder hound, kiln cat |
| Earth | pebble, riverstone, clay, loam, quarry, boulder, dust, ridge, terrace | landslide, sand-king, crystal, bedrock, mountain root | world-floor, the weight of laws | ox, tortoise, pangolin, badger, mole |
| Metal | iron, copper, bronze, needle, bell, edge, coin, chain, anvil | starsteel, sunsteel, blade-wind, gong, broadside | law-edge, the unbroken | white tiger, hawk, wasp, magpie |
| Wind | breeze, gust, kite, feather, cloud, swallow, updraft, whirl | gale, harpy wind, sky-road, storm-front, jet-stream | the wind between worlds | crane, swallow, egret, sparrow |
| Thunder | spark-drum, rumble, flash, static, drumhead | storm-horn, lightning scar, thunder-plain | heaven's drum, the verdict | ram, drum-beast, stormbird |
| Soul | lantern, dream, echo, shadow, reflection, whisper, candle | mirror-lake, spirit-sea, ghost-light | the lamp before birth, the last reflection | moth, owl, fox, lantern-fish |
| Formless | plain, empty, single, straight, bare, still | uncarved, unborn | the one line, before form | — |
| Space | orbit, fold, gap, step-between | gravity, void-rim | the space between stars | — |
| Time | hour, water-clock, dusk, dawn, echo | eclipse, the hour between | yesterday, the unwinding | — |

**Nouns by form**: Strike blow, cut, palm, fist, cleave, stroke · Flurry flurry, cuts, palms, hundred strikes · Thrust
thrust, lance, piercing · Lunge rush, lunge, charge · Sweep sweep, tail, wheel · Arc crescent, arc, wave-edge · Volley
shot, arrows, knives · Rain rain, downpour, hail · Pillar pillar, column, spike · Wave wave, surge, tremor · Burst bloom,
burst, lotus · Seeker needles, swallows, notes · Return returning (form) · Snare net, snare, grip, vines · Counter
parry, guard, answer · Ward mantle, skin, shell, focus · Chorus melody, hymn, air, call · Blink step, flicker · Plunge
descent, dive · Release release, flight · Swarm swarm, host · Domain field, court, sea · Seal seal, toll, knell · Echo
echo, twice-strike.

**Path epithets**: Blood crimson, sanguine, vein-, red river · Buddhist vowbound, lotus, merciful, of mercy · Poison
venom, miasma, nightshade, marsh-fever · Confucian upright, rite of, benevolent, script · Body iron-bone, marrow,
bronze-skin, sinew.

**Rules**: at most 28 characters; title case; words from the lists only (so a translation translates the lists and the
patterns, not 4,000 names); no two arts share a name; no name equals an item, place, NPC, title or realm name; an NPC's
name appears only in a legacy (Lotus Mind is "Elder Hu's legacy", never "Hu's Palm"); a denylist of well-known named
arts from other fiction and games, and of real scripture titles, is checked in `data_validation` for exact and
near matches (edit distance 2).

### 3.9 Icons: the Style A emblem grammar

Today's technique icons are one emblem (a disc in the element's colour, a pale mark with a dark keyline; secret arts
add a gold rim with four studs; `tools/icons/families/techniques.py`) and 66 hand-drawn marks. Style A (decision 7)
keeps the emblem and redraws it at 64 art px (`study_icons.py` `_emblem`, `mark`; `docs/ui_style_guide.md` §8.3 rule
8: a domed disc with the keyline under the mark). The plan makes the emblem a grammar, so 4,000 arts need about 400
drawings, not 4,000:

| Layer | Count | Set by | Drawn |
|---|---|---|---|
| **Disc** | 11 | the element | the study's disc ramps (`EL`), Time added |
| **Mark** | 24 forms × the families that draw them ≈ 260 | the form, with the family's weapon inset for weapon forms (a crescent over a jian, streaks over a bow) | once each, in the study's 64-px description, re-rendered natively at 48 and 32 |
| **Rim** | 13 grade rims + 3 kinds | the ring (bronze → silver → gold → jade → starsteel as the grades climb), or the kind: keystone (gold, eight studs), Dao art (jade, six studs), lost art (a torn rim) | once each |
| **Stamp** | 5 | the path: a blood drop, a lotus, a needle, a square script seal, a bone | once each |
| **Glow** | by grade | Mystic and above: the stepped glow bands of Style A rule 6, drawn by the slot, not baked | UI |

Keystones (244), Dao arts (about 40) and Lost Arts (114) get marks of their own, drawn by hand in the same description
language: about 400 drawings in all. Composing happens at run time from one atlas (`UiKit.emblem(tid, rect)` draws disc,
mark, rim and stamp and caches the result per id), so no 4,000 PNGs ship (§7). `docs/mockups/assets/emblemA_*.png` are
four compositions from the study's pipeline (`tools/icons/study/technique_emblems.py`, native at 64, 48 and 32): a Water
Arc with the Earth rim (Undertow Crescent), its Confucian path art (a Pillar with the path's square stamp), a Water
keystone (Nine Undertows: the gold rim with eight studs) and a lost art's torn rim (Tide-Palm).

Path colours, for stamps, pennants and chips: Body bronze #b87a3c, Blood crimson #b8283a, Buddhist gold #d9a632, Poison
green #6aa82c, Confucian ink-violet #4a5ab8.

### 3.10 VFX, moments and poses

- **`vfx` block** (P6, `docs/moments_design.md` §3.6): the generator writes it for every row: `tier` from the ring
  (§3.5), `shape` from the form (§3.2), `particles` from the family (brush `ink`; bell and flute `ring`) else the
  element (§3.3). The escalation curve (§5.2 there) then scales sparks, rings, numbers, shake and tint by tier, and the
  flash limiter (§5.10) keeps a crowd of tier-7 arts under one flash a second.
- **Moments**: three new rows for `data/moments.json`. `keystone_cast`: the first time a keystone is cast in a fight
  its name is brushed across the top of the screen for 0.8 s (skipped inside the flash gap). `lost_art_found`: the
  rare-drop row's layers with a rubbing unrolling and the art's name. `keystone_realised`: the chart's ink spreads from
  the node for 1.2 s on the Techniques page.
- **Numbers**: a technique's damage numbers of 10,000 and more print through `UiKit.short` ("527K"; the research's
  §6.5); a multi-hit art prints each hit, and one total instead for arts of more than three hits when the player sets it
  (the research's question 10, with P6's stacking in `docs/moments_design.md` §5.5).
- **Poses**: every form uses an action in the catalog (§3.2); `data_validation` fails a row whose `action` is not in
  `parts.json` `_actions` (or `meditate_burst`). A technique adds FX, never a pose. Any future pose goes through
  `AGENTS.md`'s full review first.

### 3.11 A worked example: one cell

The Water tree, the jian sector, ring 2 (Earth grade):

- **Form**: the generator's pick gives the jian's Arc here. Crescent Arc, the jian's Arc in the Wind tree, sits on the
  same ring and is known to Tester; rule 2 allows this second tree and no third.
- **Element**: Water adds its second verb, a pull of 40.
- **Ring**: Earth grade, +10% when it strikes; no extra target until ring 5; `vfx` tier 2. On the card: 99–132%.
- **Row**: `undertow_crescent`, "Undertow Crescent", jian, water, qi, mult 0.90–1.20 (the Arc's line; the grade is
  applied as it strikes), 1 hit, 8 targets, cooldown 5, QI 14, projectile 360 along the depth band with pierce 8,
  `pull: 40`, action `swing_2`, `vfx {tier 2, shape bolt, particles square}`, icon = Water disc × jian Arc mark × Earth
  rim.
- **Path art** in the same cell: the jian's rotation puts Confucian on ring 2 of the Water tree, so
  `upright_undertow_script`, "Upright Undertow Script": a Pillar of written water on one foe, half its multiplier on
  Insight, the Confucian stamp on its emblem.

---

## 4. The element trees

### 4.1 Topology: one graph, eleven drawings

Every tree has the same topology, drawn eleven ways (§4.10):

- The **heart** is the element's Dao. Its six tiers are the **trunk**: lit by insight, never bought.
- **Sixteen sectors** leave the heart in four kin groups (Body and Voice: free hand, fists, flute, bell · Edges: jian,
  dual blades, short blade, heavy sabre · Reach: spear, staff, whip, rope dart · Distance and Ink: bow, fan, umbrella,
  brush). Each sector opens with a **gate** that shows its weapon Dao's tier.
- **Thirteen rings** cross the sectors (§1.4). In each cell: a **passage** on the sector's line, the **orthodox art**
  beside it, and from ring 2 the **path art** beside the passage on the other side.
- At the last ring of each act, each sector has a **notable** (a passive with a real effect: "Water palms slow a
  second longer"), and each kin group a **keystone** joined to its four sectors' passages.
- **Channels** join neighbouring sectors at every notable, so a build can cross from the jian to the short blade
  without going back to the heart.

### 4.2 Node kinds and costs

| Node | Per full tree | Cost in Realisations | Needs |
|---|---|---|---|
| Heart and trunk (the Dao's six tiers) | 1 + 6 | none: lit by the Dao's insight | — |
| Sector gate | 16 | none | the family used once, or an art of it known |
| Passage | 208 (16 × 13) | 1 | the passage inside it (or the gate), and the ring's band reached |
| Orthodox art | 208 | 2 | its passage |
| Path art | 192 | 2 | its passage, and the path walked |
| Notable | 96 (16 × 6 acts) | 3 | its passage |
| Keystone | 24 | 5 | one passage of its kin group at that ring, and its source |
| **All nodes** | **751** (a v1.2.x tree: 343) | | |

A passage gives a small passive (+1% of the element's power for that family, or −2% of its Qi cost, alternating), so
walking out is never dead weight. Minor passives add inside the existing additive layers (§6.2).

### 4.3 Realisations

Nodes are paid for with **Realisations**, one pool for all trees:

```text
Realisations = Level + 2 × major breakthroughs passed + Dao tiers reached (all Daos) + Σ over arts max(0, mastery tier − 2)
```

Everything that grows a cultivator grows the pool, and mastering an art past tier 2 pays back. Tester at `ls6_end`:
Level 98, 11 majors (Bone Forging 1 through Sphere Lord 1), 12 Dao tiers (Sword 5, Blood 2, Fist 2, Life and Death 1,
Soul 1, Space 1), mastery (Flowing Palm tier 5 gives 3, Crescent Arc tier 3 gives 1): **98 + 22 + 12 + 4 = 136**. At
World Genesis a character has about 290.

An art **taught** by a manual, a teacher, a quest, a shop or a Dao tier is known at once and its node lights at no
cost; the route to it stays unlit until realised, and is needed only to go further out. Realised arts cost their node.
So every existing source keeps its worth: it saves Realisations.

### 4.4 Gates and prerequisites

1. **Ring**: a ring's nodes can be realised once the character's Level reaches its band (ring 2 at Level 19). A known
   art is never re-gated.
2. **Route**: a node needs the node inside it on its sector line (or a channel), back to the gate.
3. **Path**: a path art needs its path walked, to realise and to use (as today's flags).
4. **Keystone**: its source met (a teacher's quest done, a trial passed, a library floor reached).
5. **Family**: a family art needs that family in hand to use, as today; free-hand arts work with anything.
6. **Rest**: nodes are realised and unrealised out of combat only.

### 4.5 Respec

- **Unrealise** a node out of combat, leaves first (nothing realised may depend on it) and not while its art is in a
  slot: its Realisations come back at once. An unlearned art keeps its mastery, so realising it again restores it.
- **Reset a tree**: once free in each great realm; after that it takes a **Clear Heart Incense** (a new item, sold by
  the Mission Halls for contribution and by the harbour apothecaries later).
- Taught arts cannot be unrealised (they were never paid for); their routes can.

### 4.6 Families and paths inside a tree

A family is a **sector**, the same sixteen in every tree, so a jian user finds the jian in the same place in the Water
chart and the Fire sky. Paths are **layers**: each cell's path art hangs beside its passage in its path's colour, drawn
bright when the path is walked and faint when not, with the path chips on the page to show or hide each layer.

| P7b archetype | Its sectors | Its path layer | Trees it leans to |
|---|---|---|---|
| Body cultivator | fists, heavy sabre, staff, spear | Body | Earth, Thunder, Fire |
| Sword Dao | jian, dual blades | Confucian or Blood (the jian's affinities) | Water, Metal, Space |
| Alchemist | short blade, rope dart | Poison | Wood, Fire |
| Beast tamer | bow, whip | Poison or Body | Wood, Water |
| Formation master | fan, brush, umbrella | Confucian | Earth, Space |
| Musician | flute, bell | Buddhist | Water, Wind, Metal |

The path of each cell's path art rotates through the five so that no path repeats on neighbouring rings, each path
takes two rings of a sector and the sector's two affinity paths take three, and the rotation starts at an offset set by
the element and the family, which spreads every path across every act (§2.4).

### 4.7 The Dao, Dao arts and the sect trees

- **The element Dao is the heart.** Its tiers light the trunk (and, as today, add damage, cut cost and deepen by zone).
  A tier also adds one Realisation (§4.3).
- **The weapon Daos are the gates.** Every tree shows the family's weapon Dao tier on its gate; a tier lights nothing
  more, since the Dao is shared by every tree.
- **Dao arts** sit on the trunk or the gate at tiers 3 and 5, as the Sword Dao teaches Sword Release and Sword Swarm
  today: two for each weapon Dao, two for each element Dao, the Soul Dao keeping its three and adding one at tier 5:
  about 40, of which 5 exist. They are taught, so they cost nothing.
- **The sect tree stays on Sect › Role** (three branches of five, bought with contribution), drawn there in the same
  node language. On the element tree the sect's three signature arts wear the vermilion seal, and a seal at the heart
  of the sect's element (Water for the Jade Sect) opens Sect › Role. Contribution and Realisations never mix.

### 4.8 The 56 existing arts, re-homed

Each art takes the cell of its element, family and ring; "any" becomes the free hand and `none` Formless. 47 go into
cells, 5 onto Dao trunks (Sword Release and Sword Swarm on the jian gate; Sense Lock, Phantom Double and Soul Search on
the Soul trunk), and 4 become Lost Arts (§5): Rising Tide, Rain of Reeds, Ember Burst (world drops) and Blood Burning
(the Blood Dao teacher's secret art). Five cells hold two existing arts; they stay **twin cells** rather than push
either art to a ring its teacher does not teach:

| Cell | Arts |
|---|---|
| Formless · spear · ring 1 | Jade Thrust, Dragon Tail Sweep |
| Soul · free hand · ring 3 | Mirror Mind Spike, Soul Lantern Ward |
| Earth · free hand · ring 2 (path) | Stone Skin (Body), Golden Body (Buddhist) |
| Fire · free hand · ring 2 (path) | Crimson Palm, Blood River Slash (both Blood) |
| Wood · free hand · ring 2 (path) | Venom Needles, Miasma Palm (both Poison) |

The generator fills every other cell; a cell holding an existing art is never generated over.

### 4.9 Saves: the migration

On load, a save from before the trees: every known art lights its node (taught); the route from its gate to it is
lit and paid from Realisations; mastery, slots and bars are untouched. Tester at `ls6_end`:

| Tree | Known arts | Route lit | Realisations |
|---|---|---|---|
| Water | Flowing Palm (ring 1), Still Water Focus (ring 2) | free hand, passages I–II | 2 |
| Wind | Crescent Arc (jian, 2), Cloud Descent (free hand, 3) | jian I–II, free hand I–III | 5 |
| Soul | Mirror Mind Spike, Soul Lantern Ward (3); Sense Lock on the trunk | free hand I–III | 3 |
| Metal | Upright Glyph (free hand, 7, Confucian); Sword Release and Sword Swarm on the jian gate | free hand I–VII | 7 |
| Formless | Glimpse of Heaven (free hand, 4), Splashed Ink (brush, 8) | free hand I–IV, brush I–VIII | 12 |
| Lost Arts | Blood Burning | — | — |
| **All** | 13 | 29 passages | **29 placed, 107 to place** |

The 107 are the tree's opening gift to an established character, shown on the Techniques page's counter.

### 4.10 The page: tabs, and each tab's look

The Techniques page drops the window with panels (decision 14: every page its own). What stays from
the shared kit: the close button, primary buttons with inked labels (decision 10), the text tokens, 48 px targets and
the type sizes. Everything else is the page's own.

**Tabs** run along the top as element seals, each a 52 px disc with its name under it at 14 px, in the generating
cycle: **Wood, Fire, Earth, Metal, Water**, then **Wind, Thunder, Soul, Formless**, then **Space** (open with its Dao;
Tester has it at tier 1) and **Time** (locked until its Dao, Act IV, with its line on tap); then **Lost Arts** and
**Secret Arts**. The page opens on the tab of the art last selected.

- **Inner Arts** move into the **loadout dock** at the foot of every tab: four Inner Art slots and the stance for the
  weapon in hand sit beside Ring I and Ring II; a tap on an Inner Art slot opens the drawer of known Inner Arts and
  stances. They are worn like techniques, so they belong with the slots, not in a tab of their own.
- **Secret Arts** keep a tab, last, drawn as a footwork chart: they are movement and utility arts that are known, not
  slotted, and each has a "how to" line that wants room.

**Each tab's look**, one topology drawn eleven ways (`TechniqueChart` with a projection per element: a layout
function, a background painter and a node painter):

| Tab | The chart | Heart and trunk | Arts | Keystones | Paths |
|---|---|---|---|---|---|
| **Water** | A tide chart on celadon silk in indigo ink: the sectors are currents flowing down from the Spring, the rings depth contours labelled like soundings, notables anchors | the Spring and a tide gauge of six marks | buoys (hollow with the form's chart mark, then inked with the emblem when realised); passages are sounding dots | whirlpools | pennants in the path colour |
| **Wood** | A living tree on warm ochre paper: sectors are boughs, rings the height bands | the root crown, the Dao as growth rings in the trunk's cut | buds, in leaf when realised | fruit | vines and moss |
| **Fire** | A forge-lit night sky: sparks rising from a forge mouth, rings as heat bands from red to white | the forge mouth, six bellows vents | ember stars | comets | coloured smoke |
| **Earth** | A cliff in cross-section: rings as strata going down | the surface marker, six boundary stones | ore seams and fossils | geodes | mineral veins |
| **Metal** | The back of a cast-bronze mirror: concentric bands in relief with silver inlay for the routes | the central boss, six bell-studs | bosses, polished when realised | cast masks | gold and copper inlay |
| **Wind** | Kite paper with cloud scrolls: sectors as wind streams | the kite reel, six knots on the string | kites | whirlwinds | ribbons |
| **Thunder** | A storm-dark sky with forked channels | the great drum, six beats | drumheads | thunder drums | lightning colours |
| **Soul** | A lantern-lit mirror lake at night; the chart and its reflection | the lamp-post, six lanterns | floating lanterns | moons in the water | reflections tinted by path |
| **Formless** | An ensō on rice paper in black ink | the open circle, six dots | ink dots | vermilion seals | dry-brush strokes |
| **Space** | An armillary sphere: rings as orbits | the axis, six armillary rings | stones in orbit | planets | — (from its first ring, paths as on the others) |
| **Time** | A water clock and dial | the float, six tiers of the clock | hour marks | eclipse discs | shadows |
| **Lost Arts** | A dark wood board with manuscript fragments, stele rubbings and bamboo slips pinned to it; red thread for lineages | — | found: the page with its emblem; not found: only counted per act (decision 19) | lineage cards, once a piece is found | — |
| **Secret Arts** | A woven practice mat with footwork diagrams (footprints and arrows) | — | one diagram per art, its how-to line beside it | — | — |

**On every element tab**: the chart fills the screen; pan by dragging, zoom with two fingers or the + and − buttons
(48 px), **Fit** and **Heart** buttons; a **minimap** of the whole tree with the view's frame (uncharted rings drawn
faint); the **path chips** (show or hide each path's layer, the walked ones marked); the **Realisations** counter; the
**node card** for the selected node (what it does, its numbers, its route and cost, the same form in other trees, its
path art, **Realise** as the primary button); the **loadout dock**. Level of detail: zoomed out, nodes are dots;
halfway, emblems; zoomed in, names.

---

## 5. Lost Arts

### 5.1 What a lost art is

An art of any kind (a technique, an Inner Art, a stance or a Secret Art) that is **found only in the world**: from a
quest with a hidden condition, a rare drop, a hidden place, a stele, a dying or departing master, a ruin, or a calendar
event. It is on no tree and costs no Realisations: finding it (and reading it, if it is a manual) teaches it. Lost arts
are strong in a different way from tree arts: each has a rule no generated art has, and each counts as a **heavy art**
in the loadout (§6.3).

### 5.2 Sources

| Kind | How it is found | Ties to |
|---|---|---|
| Stele | Rub a stele with a Rubbing Kit (a new tool, Stoneford General Store) when a condition holds (a Dao tier, a time of day, a season) | the valley's and the Expanse's seven insight stones; the Frontier's Law steles |
| Ruin or hidden place | Reach a hidden room, vault or secret realm | the world plan's hidden maps (§5.6) |
| Master | A master's last lesson (a legacy) or a hermit's, after a quest or a chain of gifts | Elder Hu's and Elder Sung's legacies today; hermits Yao, Shuang, the Orbit Hermit |
| Rare drop | A manual from an elite or boss, with pity | P9's Worthy Foes reward loop (`docs/boss_design.md` §3.11) |
| Quest | A quest with a hidden condition, or a choice | Blood Remembers today |
| Event | A world event or calendar day | the calendar's world events, the eclipse, the Remnant Battlefield |
| Lineage | Pieces gathered over acts restore a lost school (§5.5) | Lu's journal; the Tomb of Sunscar; the Orbit Ruins; the Nameless Barrow; the Bellwood World; the Unwoven Shore |

### 5.3 Rarity and pity

| Rarity | Where | Rate | Pity |
|---|---|---|---|
| Sure | a hidden place, a stele, a master, a quest, a lineage piece | once per character | — |
| Rare | an elite | 2–5% | P9's counter: sure by the 30th |
| Very rare | a field or dungeon boss | 3–6% (15% for a boss whose signature it is, pity 6, as the Tide-Palm Scroll) | sure by the 20th |
| Chance | a world event's chest, the Research craft, a night peddler's rotation | a weighted pool of that act's drop arts | the craft's pool drops what the character lacks first |

A manual found twice is a Manual Page the second time (or a gift for a disciple once its Dao can teach: tier 4).

### 5.4 Before it is found: counted, never described

**Decided (roadmap §6 decision 19, 2026-09-27): secret and lost techniques are unknown until found.** The player is
never told how to find one. So there are **no hints, no source lines, no silhouettes, no Track guidance and no "ask a
companion"** for an art not yet found:

- The Lost Arts board shows, for each act the character has reached, only a **count**: "3 of 20 found in this act".
- An art not yet found has no scrap, no emblem silhouette, no kind, no name and no place on the board.
- A **found** art appears with its full card (name, emblem, kind, element and family, what it does). A lineage's card
  appears with its first found piece and counts its pieces found, never the missing ones' names.
- The sources stay in the data (`data/lost_arts.json`: the stele, the room, the master, the foe and its rate), since
  the world needs them; the query the page reads (`ProgressionAuthority.lost_arts_view`, from
  `TechniqueTreeRules.lost_view`) returns counts and found cards only, and `rules_tests` checks that nothing of an
  unfound art (its id, name or source) is in it.
- A stele, a ruin or a master that holds a lost art says nothing about it until its condition holds: a locked object
  reads as plain scenery ("Weathered carvings."), never as a rumour.

The hint lines of the tables below are the design's notes on where each art is placed, not text the game shows; the
data keeps no hints.

### 5.5 Lost lineages: the lost cultivation systems

Six schools that died out, each found piece by piece. A lineage is a small system with its own rule, not only a list of
arts: its first piece opens its card on the board, and each further piece adds an art.

| Lineage | Acts | Pieces | Its rule | Its six arts |
|---|---|---|---|---|
| **The Ferryman's Oar** (Lu's own school, written in his journal) | I–V | Lu's journal pages: one art at 5, 10, 15, 20, 25 and 30 pages | Oar arts (staff and free hand) strike harder on water and in rain | Oar Across the Current, Ferry Pole Vault, Mooring Knot, Fog-Crossing Step (a Secret Art), Lantern at the Bow, The Ferry Waits (an Inner Art) |
| **The Sand-King Script** | II | Six clay tablets in the Tomb of Sunscar, read by Bone-Reader Xiu | Written arts leave glyphs in sand that go off when a foe steps on them | Tablet of Dry Wells, Sand-Glyph Snare, Throne-Dust Veil, Scorpion Script, Oasis Mirage (a Secret Art), The King Who Waits (a keystone-grade art) |
| **The Orbit Lamp** | III | Six lamp-lenses in the Orbit Ruins and the Observatory | Arts cast under a lamp curve toward the nearest foe and orbit once | Lamp on a Tether, Inverted Stair Kick, Orbit-Stone Sling, Gravity Knot, Lens of Far Seeing (an Inner Art), Lamp That Circles the Dark |
| **The Barrow Oath** | IV | Six oath-plates in Kingsgrave Barrows and the Nameless Barrow | Arts grow stronger for each ally or summon beside you | Banner That Does Not Fall, Oath-Plate Guard, Remnant March, Grave-Bell Toll, Kingsgrave Stance (a stance), The Oath Outlives the King |
| **The Bellwood Canon** | V | Six bronze leaves from the Bellwood World (a Relic World) | Every art rings: a ring stacks on the foe and the sixth breaks its guard | Bronze Leaf Fall, Bellwood Echo, Ringing Root, Six-Leaf Chime, Stilled Bell (an Inner Art), The Forest That Rang |
| **The Loose Thread** | Epilogue | Six threads on the Unwoven Shore | Arts unpick: each strips one buff or shield from what it strikes | Pulled Thread, Unwoven Step (a Secret Art), Knot Undone, Frayed Edge, Needle of Mending, The Hand That Unweaves |

### 5.6 How they tie into P7b's sources and the world plan's hidden maps

- **P7b** (`docs/item_plan.md` §2.10, §4): lost manuals are loot-table rows with a `named`-style exclusion (never in the
  random roll), sourced like named gear; the wiki lists them with their rates; `data_validation` requires a source for
  every lost art as P7b does for every item.
- **P9**: a boss's Worthy Foes loop can carry a lost art as its signature (the Tide-Palm Scroll already does); its pity
  is P9's.
- **World plan** (`docs/world_plan.md` §3–5, Hidden maps): each hidden map holds one lost art or lineage piece on top of
  what it already holds. Act IV: the Cold Hearth (a Fire art that works where Fire is silenced), the Sunken Library
  (two, one per road), the Seed Vault (a Wood stance), the Nameless Barrow (the Barrow Oath's keystone piece: the dead
  king's legacy art *or* his sword, as written there), the Hour Between (a Time art, eclipse only), Yesterday's Room (a
  Time Secret Art). Act V: the Kiln vault, Lu's locked drawer (a Ferryman's page), the Chapel crypt (a demonic art; taking
  it is a sin, S49), the Primordial Den, the Pilgrim's Camp, Tidewatch Tower's crown. Epilogue: the memory rooms re-offer
  any lost art of an earlier act the character missed, as an echo (the rule v1.5 already uses for named gear).

### 5.7 The list, Acts I–III

Found or not, these 44 singles and the first three lineages (18 pieces) are pinned on the board by the end of Act III:
62 in all. "Today" marks the six that exist.

**Act I · Jade River Valley (20)**

| Art | Kind · element · family | Source | Rarity | Hint (first line) |
|---|---|---|---|---|
| Rising Tide (today) | technique · Water · free hand | the Mudwater Manual: Big Toad Tan, Lieutenant Kuai | sure | "The Mudwater gang stole a manual they cannot read." |
| Rain of Reeds (today) | technique · Wood · bow | the Drowned Shrine's manual; Research | sure | "A drowned archer's manual lies where the lanterns are." |
| Ember Burst (today) | technique · Fire · free hand | gorge bandit adepts; Research | rare (3%, pity 30) | "Gorge bandits carry torn copies of an old fire art." |
| Lotus Mind (today) | Inner Art | Elder Hu's legacy (Jade Sect) | sure | "An elder's last lesson is for his own disciples." |
| Drifting Cloud (today) | Inner Art | Elder Sung's legacy (Cloud Sect) | sure | "The Cloud Sect's elder keeps one lesson back." |
| Tide-Palm | technique · Water · fists | the Tide-Palm Scroll, Elder Gu's vault (P9) | very rare (15%, pity 6) | "The smuggler of Stoneford keeps a scroll he was paid in." |
| Falls-Climbing Step | Secret Art · Water | the stele behind the falls (`insight_falls`) | sure | "A stele behind falling water remembers a step the water cannot follow." |
| Willowbark Script | technique · Wood · brush | the stele on Elder Hu's Peak (`insight_hu`) | sure | "An old carved stone on the elder's peak was cut by a brush, not a chisel." |
| Kite-String Cut | technique · Wind · short blade | the stele on Elder Sung's Peak (`insight_sung`) | sure | "Wind has worn a stone on the Cloud peak into the shape of a blade." |
| Mist-Lamp Meditation | Inner Art · Soul | the stele on the Misty Slopes (`insight_mist`) | sure | "In the mist below the gate a stone is warm at night." |
| Mudskipper Kick | technique · Earth · fists | Hermit Yao, after the marsh herbs | sure | "The marsh hermit fights like something that lives in mud." |
| Well-Bottom Sutra | technique · Soul · bell (Buddhist) | the Scripture Well, Drowned Shrine | sure | "Something is written at the bottom of a well that no one has drained." |
| Monastery Gate Staff | technique · Earth · staff (Buddhist) | the Forgotten Monastery, Mist Peak | sure | "A monastery nobody remembers still keeps its gate." |
| Quarry-Breaker Fist | technique · Earth · fists (Body) | the Collapsed Tunnel, Stonewall Quarry | sure | "The miners who dug too deep left their training marks on the rock." |
| Grotto Moon Flick | technique · Metal · short blade | the Hidden Grotto (unmapped) | sure | "A grotto no map shows faces the moon." |
| Vale Serpent Spear | technique · Wood · spear | the Back Mountain, Hidden Vale | sure | "Your own vale has a back mountain nobody has climbed." |
| Frost-Shrine Sword | technique · Water · jian | the Frozen Shrine, Summit Ridge, in winter | sure | "The shrine on the ridge only opens when it is coldest." |
| Echo-Cliff Refrain | technique · Wind · flute | the Echo Cliffs, Whitewater Gorge | sure | "Play one note at the cliffs and listen to what answers." |
| Serpent-Coil Thrust | technique · Water · spear | Riverbed Serpent | very rare (4%, pity 20) | "The serpent of the bend coils the way a spear should turn." |
| Surfacing Bell | technique · Water · bell | the world event The Drowned Shrine Surfaces | chance | "When the shrine rises, its bell rings once for someone." |

**Act II · Azure Expanse (12)**

| Art | Kind · element · family | Source | Rarity | Hint (first line) |
|---|---|---|---|---|
| Blood Burning (today) | technique · Formless · free hand | Blood Remembers, Matriarch Tie Yun | sure | "The Ironroot matriarch knows what blood can buy." |
| Scar-Lightning Lance | technique · Thunder · spear | the stele at the Lightning Scar (`insight_thunder`) | sure | "Lightning has struck one stone on the plains a thousand times." |
| Hoarfrost Arrow | technique · Water · bow | the stele in the Rimefrost (`insight_frost`) | sure | "Ice has kept a hunter's mark for longer than the hunter lived." |
| Mirror-Lake Knell | technique · Soul · bell | the stele at the Lake Shrine (`insight_mirror`) | sure | "The lake shows a bell that is not there." |
| Snowfall Without Sound | technique · Water · jian | Hermit Shuang, on the day she leaves the Ice Cave | sure | "The Rimefrost hermit will not stay another winter." |
| Crypt-Seal Cleave | technique · Earth · heavy sabre | the Mirror Crypt, Tomb of Sunscar | sure | "One mirror in the crypt shows a blade instead of you." |
| Sand-Throne Sweep | technique · Earth · staff | the Tomb King | very rare (4%, pity 20) | "The king who sat three thousand years learned to sweep his hall." |
| Many-Eyed Pool Air | technique · Water · flute | the Thousand-Eye Toad | very rare (4%, pity 20) | "The toad of the mirror lake hums when it hunts." |
| Roost-Scatter Fan | technique · Wind · fan | the Harpy Roosts, Gale Canyons | sure | "The harpies nest where a fan-master fell." |
| Deck-Cutter Flick | technique · Wind · short blade | the Pirate Deck, Skyport Wreck | sure | "The wreck's pirates hid more than cargo under the deck." |
| Grey Footfall | Secret Art · Soul | the Grey Pilgrim | sure | "A stranger in grey walks without sound. Ask how." |
| Ninth Peak Scroll | technique · Metal · jian | Auction Day, the Auction Pavilion | chance | "Some lots at the Nine Peaks' auction are older than the peaks." |

**Act III · Lantern Star Field (12)**

| Art | Kind · element · family | Source | Rarity | Hint (first line) |
|---|---|---|---|---|
| Star-Sighting Shot | technique · Space · bow | the Observatory, Stargazer Ming | sure | "The stargazer's lens was ground for aiming, not only seeing." |
| Upside-Down Staff | technique · Space · staff | the Inverted Hall, Orbit Ruins | sure | "In the hall where the floor is the ceiling, a staff hangs upright." |
| Wyrm-Egg Knuckle | technique · Fire · fists | the Hatching Cave, Wyrmnest Isles | sure | "Wyrm shells are harder than knuckles. Someone learned from that." |
| Hulk-Breaker | technique · Water · heavy sabre | Old Bo, keeper of the Moored Hulks | sure | "The old hulk-keeper broke ships for a living once." |
| Cove Knife | technique · Metal · short blade | Smugglers' Cove, Blackmast Haven | sure | "The smugglers' cove has a knife-thrower's target no one uses." |
| Broadside Fan | technique · Metal · fan | Admiral Voss | very rare (4%, pity 20) | "The admiral fans his orders to the guns." |
| Pyre-General's Lance | technique · Fire · spear | General Kharn | very rare (4%, pity 20) | "The pyre-general carries a lance he never uses. Make him." |
| Comet-Tail Arrow | technique · Fire · bow | Comet Captain Rao | very rare (5%, pity 20) | "The comet captain's sails leave a burning tail." |
| Maw-Song | technique · Space · flute | the Nebula Leviathan | very rare (3%, pity 20) | "The leviathan sings before it swallows." |
| Burning-Star Peal | technique · Fire · bell | the Hall of Burning Stars, Lantern Heart | sure | "A bell in the lantern's heart is cast from a fallen star." |
| Breakwater Sword | technique · Formless · jian | The Tide Breaks (the battle, holding the line to its end) | sure | "Whoever holds the breakwater to the last wave learns what it knew." |
| Held Presence | Inner Art · Soul | Presence-Master Ruo, after the Presence Court's last trial | sure | "The master of the Presence Court has one thing left to teach." |

Lineage pieces pinned by then: the Ferryman's Oar (pages 1–20 reachable in Acts I–III), the Sand-King Script and the
Orbit Lamp.

### 5.8 Acts IV, V and the Epilogue in outline

| Act | Singles | Lineage | Sources |
|---|---|---|---|
| IV · Star Frontier | 14 | the Barrow Oath | six Law steles (one per world), the six hidden maps of §5.6, the throne contest's winner's art, the four new field and dungeon bosses, the eclipse |
| V · Outer Heavens | 14 | the Bellwood Canon | the four Relic Worlds' vaults, the Refuge's cleansed villagers (a master among them), front missions, the Hollowed Primordial, the hidden maps of §5.6 |
| Epilogue | 6 | the Loose Thread | the memory rooms, the Unwoven Shore, woven worlds' own steles |

Totals: singles 20 + 12 + 12 + 14 + 14 + 6 = 78; lineages 6 × 6 = 36; **114 lost arts**, of which 6 exist.

---

## 6. Balance

The numbers come from the stat scaling research (`docs/research/stat_scaling_research.md`, merged, its recommendations
taken; roadmap phase P12 · Might). It puts the realm's power in **Might**, ×1.30 a great realm (×1.17 at the major, the
rest over its Levels), on the player's attacks, HP and defences and on every monster of the same Level. Its par
character hits **136K** with a basic blow and **527K** with a technique at Level 99 (922K on a crit), 611K and 2.69M at
Level 120, 5.95M and 27.2M at Level 165. Techniques ride Might through the attack stat; nothing in this plan scales
with the realm on its own.

### 6.1 Why four thousand arts need not creep

1. **Might carries the scale, techniques the shape.** The absolute growth (×15 by Level 99, ×153 by 165) is the
   realm's. A technique's own terms are the research's skill bucket: its multiplier and grade, +8% a mastery tier, +5%
   a tier of its Dao (`CombatRules.resolve` step 4, unchanged).
2. **Budgets by form and ring, not by row.** Every art's expected damage per cast, per Qi and per cooldown second sits
   within ±10% of its form's line at its ring (§3.6 rule 5). A new art is a new shape or verb, not more damage.
3. **The ring's multiplier flattens after Act I.** Grade is +0, +10, +20% (Common, Earth, Heaven) and stays +20% from
   ring 3; the form budgets rise through Act I as heavier forms open and are flat from ring 4 (§3.5). A ring-12 art is
   not stronger than a ring-4 art of the same form; it reaches further, strikes more foes and carries a later verb.
4. **Old arts climb with mastery.** An art's effective ring is `min(the band's ring, home ring + mastery tier − 1)` for
   its grade, targets and reach: a Common palm mastered to tier 3 strikes with Heaven's +20%. Favourites stay viable;
   mastery (and its Manual Pages) is how.
5. **No new multiplier.** Tree passives, keystones' passive halves and path rules feed the research's buckets
   (damage%, attack%, crit), never Might and never its short **final damage** list (natal treasure, legendary chain,
   Genesis Mastery).

**The line a par character's main art must meet.** The research's technique hit over its basic hit, which the form
budgets are tuned to (the par main art is the band's best single-target form at par mastery and Dao: the weapon's Dao at
tier 1 by Qi Kindling, 3 by Spirit Awakening, 5 by Will Manifest, 6 by Monarch; the art's mastery climbing 3 to 6):

| Level | 20–30 | 45 | 60 | 72–80 | 90–99 | 100–108 | 117–120 | 130–165 | 200 |
|---|---|---|---|---|---|---|---|---|---|
| Technique hit ÷ basic hit (research §6.2) | 1.5 | 2.3 | 3.6 | 3.7 | 3.9 | 4.1 | 4.4 | 4.6 | 4.5 |
| Par technique hit | 420–1,246 | 7,402 | 39.5K | 94.5K–154K | 313K–527K | 726K–999K | 1.77M–2.69M | 4.74M–27.2M | 100M |

From Level 60 the ratio grows by only 27% to Level 165, which mastery (tier 4 to 6: +32% to +48%) and the Dao (tier 3
to 6: +15% to +30%) nearly give on their own (×1.21); that is why the ring adds no multiplier there.

### 6.2 Tree passives

Passages, notables and keystones' passive halves feed the research's buckets: the one additive **damage%** bucket
(elemental power by element, a family's damage, boss damage from keystones that name it), **attack%** (rarely, from
notables), crit and crit damage within the cap of ×3.0, cost reduction and status chance. The research's par character
has +13% damage% at Level 99 and +20% at 165 from sets and named pieces; the trees add at most **+15% by Level 99 and
+25% by Level 165** to any one bucket, a notable's conditional effect counting toward it, and the par character built by
P12's `balance_sim` places its Realisations along its main family's route so these shares are inside par (monster HP is
3.5 par basic hits, so time to kill holds). `elemental_power` keeps its cap of 150%.

**Percent-of-HP effects.** Poison (Venom Needles 2% a second, Miasma Palm 3%), the Wood bloom and any path art that
takes a share of the target's health are capped against elites and bosses at 60% of the caster's attack a second: on a
Might-scaled boss (the Nebula Leviathan at 127M) an uncapped 2% a second would deal six times par DPS. Shares of the
caster's own HP (Blood costs, Buddhist shields) scale with Might as HP does and need no cap.

### 6.3 Loadout limits

| Limit | Value | Today |
|---|---|---|
| Active arts | 8: Ring I and Ring II of four (the HUD's ring and its 1/2 swap), per weapon | same |
| Heavy arts (keystones and lost arts) | one per ring, two in all | new |
| Inner Arts | 4 (from Spirit Awakening 1) | same |
| Stance | 1, for the weapon in hand | same |
| Path arts | usable only while their path is walked | same flags |
| Combos | by **form pairs**, not art pairs: about 30 rows (Snare → Pillar: +20% on a rooted foe; Arc → Echo; Seal → Finisher), so every generated art combines without new rows; the six named pairs stay | 6 named pairs |

### 6.4 The checks

- **`balance_sim` technique check**, per band and per family: the best eight-art loadout's damage a second and damage per
  Qi against the band's baseline (the stat curve's expected), within ±15%; no family more than 10% above the median
  family of its band; a path art's net value (damage less the value of its HP or Composure cost) within ±10% of its
  cell's orthodox art; every element's verb priced so that Water's pull and Formless's +10% land on one line.
- **Against the research's par table** (`balance_sim`, once P12 lands): the par character with a par tree and its
  band's best eight arts meets the par basic and technique hits of §6.1 within ±15% at every Level the table gives
  (136K and 527K at 99), and the percent-of-HP cap holds on every boss of `docs/boss_design.md`. The trees' form budgets
  are tuned after P12 (Might) is in; if the trees come first, they are tuned to today's curve and re-run with P12.
- This plan fixes the shapes, the relative budgets and the caps; the research fixes the absolute curve. If the curve
  moves (its §7 leaves Might's step and the realm gap open to review), only Might changes and every ratio here holds.

---

## 7. Performance and data size

| Item | Today | v1.2.x | v1.5 |
|---|---|---|---|
| `techniques.json` rows | 56 | about 1,860 (1,768 tree arts, 5 twins, about 20 Dao arts, 62 lost arts) | about 4,350 |
| Size as written today (858 B a row, indented) | 48 KB | 1.6 MB | 3.7 MB |
| Size with compact rows (defaults from the form at load; about 260 B a row) | — | 0.5 MB | 1.1 MB |
| Tree data | — | implicit: nodes follow from the rows' cells; `technique_trees.json` holds only the exceptions (twins, trunk arts, channels), under 30 KB | same |
| Save | known ids, mastery, slots | + one bitset of realised nodes per tree (751 bits, about 100 B base64) | 1.1 KB |
| Icons | 66 PNGs | one emblem atlas at 64 and one at 48 (discs, about 260 marks, rims, stamps, plus hand marks), about 1 MB each | same atlases, more hand marks |

- **Rows are baked** in `tools/data` (the project's pattern: diffable, wiki-able, readable by the tests) and written
  compact: a row keeps only what differs from its form's defaults, and `ContentDB` fills the defaults when it loads.
- **Loading**: `ContentDB` parses the file once at start and builds three indexes (by id, by element and sector, by
  cell). Budget in `perf_tests`: +60 ms on the desktop reference, +200 ms on the phone reference, at v1.5's size.
- **Drawing**: the chart draws only nodes inside the view (culling), dots when zoomed out, emblems halfway, names zoomed
  in; emblems are composed once per id and cached (256 held); one atlas texture keeps draw calls low. Budget: a full tree
  of 751 nodes at any zoom within the page's frame budget in `perf_tests`.

**The headless tests that keep them valid**

| Suite | Checks |
|---|---|
| `data_validation` `technique_suite` | counts per element, family, path and act equal §2's for the acts built; rules 1–6 of §3.6; every row's `action` in the catalog; every row has `vfx`; every cell of a built ring is filled; every node reachable from its gate; every twin, trunk and channel exception listed; names unique, lexicon-only, not on the denylist, ≤ 28 characters |
| `data_validation` `lost_art_suite` | every lost art has a source row (loot table, stele, room object, quest reward, event) wired into the world; no hint strings (decision 19); every lineage has six pieces with sources; lost manuals are excluded from the random roll |
| `rules_tests` `tree_suite` | the Realisations formula; realise and unrealise (leaves first, not while slotted, refunds); ring, path, keystone and rest gates; the free reset once a great realm; the heavy-art cap; the percent-of-HP cap on a boss; taught arts light for free; the migration of `ls6_end` (29 placed, 107 to place, every known art still known, mastery unchanged) |
| `balance_sim` technique check | §6.4 |
| `perf_tests` | load time and chart draw time at the v1.5 size (a generated fixture) |
| `contract_tests` | the new intents (`realise_node`, `unrealise_node`, `reset_tree`) in the catalog (no `track_lost_art`: decision 19); every generated string present; no intent the page used before disappears |
| `ui_suite` | every region at least 48 px, no text under 14 px, on every tab at its default zoom |
| The icon build | byte-identical twice; every row resolves to an emblem |
| The wiki | `docs/wiki/techniques.md` (new, from `tools/dev/wiki.py`) rebuilt byte-identical |

---

## 8. Build order

Steps 1–9 land in v1.2.x (as P7c, beside P7b and before v1.3's content is written); 10 with v1.3, 11 with v1.4, 12
with v1.5. Steps 4, 7 and 9 tune their budgets against P12's par character (Might), which lands after P7b part 1 and
before v1.3; if a step runs before P12, it tunes to today's curve and re-runs its `balance_sim` once P12 is in. Code
changes are marked; the rest is data from `tools/data/*.py` through `build_data.py`.

| # | Change | Lands in | Tests |
|---|---|---|---|
| 1 | Re-tag the 56: `form`, `ring`, `cell`, `kin`, `path`, `source_kind`; the grade kept as today (+0, +10, +20%) and every ring from 3 at +20%; `lost: true` on four; player-facing source names; the `vfx` block if P6 has not added it | `techniques.py`; strings | `data_validation` fields; `balance_sim` shows no change |
| 2 | The grammar and the generator: forms, elements, paths, rings, lexicons, budgets, poses, `vfx`, the denylist | `technique_grammar.py`, `technique_gen.py` (new) | generator byte-identical twice; §3.6 rules |
| 3 | The tree rules and state: `TechniqueTreeRules` (pure), intents, `cultivator.tree`, Realisations, respec, the heavy cap, the percent-of-HP cap against elites and bosses (§6.2), the save migration | **code**: `scripts/simulation/rules/technique_tree_rules.gd` (new), `progression_authority.gd`, `cultivator_state.gd`, `combat_authority.gd` (heavy cap, percent-of-HP cap) | `tree_suite`; the migration on every valley_run checkpoint |
| 4 | Pilot: the Water tree's Act I (12 sectors, rings 1–4: 88 arts) and its four keystones' sources | data; the Falls Pool trial and the Trial Tower's floor 30 | `balance_sim` rings 1–4; `valley_run` realises a Water art |
| 5 | Icons: the Style A emblem pipeline (the icon study's conversion step 2), discs, form marks, rims, stamps; the 66 existing technique icons redrawn as emblems; run-time composition | `tools/icons/families/techniques.py`; **code**: `UiKit.emblem` | icon build byte-identical; every row resolves |
| 6 | The page (P5b's Techniques): `TechniqueChart` and its projections (Water, Wood and Fire first, then the rest), the Lost Arts board, the Secret Arts footwork chart, the loadout dock with Inner Arts and the stance | **code**: `techniques_page.gd`, `technique_chart.gd` (new) | `ui_suite`; `contract_tests`; screenshots against these mockups |
| 7 | Act I for all nine trees (792 arts), keystone sources, notables, form-pair combos | data | counts; `balance_sim` rings 1–4 |
| 8 | Lost Arts, Act I (20) and the Ferryman's Oar; the Rubbing Kit; the found-only board (decision 19: no hints, no Track) | `enemies.py`, `world.py`, `story.py`, `economy.py`; **code**: the stele object, `learn_lost_art` | `lost_art_suite`; `valley_run` finds one |
| 9 | Acts II–III for all trees and Space rings 7–8 (976 arts), their keystones; Lost Arts II–III (24) and two lineages; the wiki page | data; `wiki.py` | counts; `balance_sim` rings 5–8; wiki rebuild |
| 10 | **v1.3**: Act IV (rings 9–10) for every tree, the four new families' sectors rings 1–10, the Time tree, the new Daos' arts, Lost Arts IV and the Barrow Oath | data with `frontier.py` | as 7–9 for rings 9–10 |
| 11 | **v1.4**: Act V (rings 11–12), Lost Arts V and the Bellwood Canon | data | as above |
| 12 | **v1.5**: the Genesis ring, the Epilogue's Lost Arts and the Loose Thread; memory rooms re-offer missed lost arts | data; **code**: the echo rule | as above |

---

## 9. Open questions

| # | Question | Recommendation |
|---|---|---|
| 1 | Space and Time as tabs of their own, or branches of other trees? | Tabs, opening with their Daos: Space in v1.2.x (the Orbit Hermit), Time in v1.3 (Timekeeper Gong Yi). They start at their act's ring, so their trees are smaller |
| 2 | Formless (the `none` element) as a tab? | Yes: 11 of today's 56 are Formless, and the plain form is a build of its own (raw numbers, no verb) |
| 3 | Realisations: one pool, or one per element? | One pool, fed by Level, breakthroughs, every Dao's tiers and mastery, so a hybrid build is paid for by everything the character does |
| 4 | Respec cost | Free out of combat, node by node from the leaves; one free tree reset each great realm, then a Clear Heart Incense |
| 5 | v1.3's four families: full sectors from ring 1? | Yes, with banded bases at every grade, as P7b decided for the brush and bell; otherwise a late family arrives with no early arts |
| 6 | Path arts on rings before the path can be walked | Keep them as the path's foundations, realisable the day it is walked |
| 7 | Icons composed at run time or baked into PNGs | At run time from one atlas; 4,000 baked icons at two sizes would be about 16 MB |
| 8 | Heavy arts: one per ring? | Yes; keystones and lost arts share the cap |
| 9 | Rows baked or expanded from the grammar at load | Baked and compact: tests, the wiki and diffs read them; the defaults come from the form |
| 10 | The grade bonus across thirteen rings | The research's skill-bucket grade: +0, +10, +20% and flat from ring 3; the form budgets rise through Act I and are flat after it, so Might and mastery carry the growth (§6.1) |
| 11 | The sect tree on the Techniques page | No: it stays on Sect › Role; a seal at the sect element's heart opens it |
| 12 | Scope, if it must shrink | Halve the path arts (one every other ring from ring 2): about 190 a path and 190 a family, still hundreds; never cut the rings or the keystones |
| 13 | Can a found lost art be taught to the account's other characters? | Singles yes, once its Dao reaches tier 4 ("can teach it"); lineage arts no |
| 14 | The new page drops the window with panels (decision 14); is a pale Water chart readable in the dark HUD's world? | Yes on the page: ink on paper uses `PAPER_INK` (12.3:1), and the loadout dock stays dark so slots read the same on every tab |

## Decisions taken

The questions this page left open take the recommended answer, which the user can overturn before step 1:

| Question | Decision |
|---|---|
| Space and Time | Their own tabs, opening with their Daos |
| Formless | A tab |
| Realisations | One pool |
| Respec | Free out of combat, leaves first; one free reset a great realm, then a Clear Heart Incense |
| v1.3's families | Full sectors from ring 1, with banded bases at every grade |
| Path foundations | Kept |
| Icons | Composed at run time from one atlas |
| Heavy arts | One per ring |
| Rows | Baked, compact |
| Grade across the rings | +0, +10, +20%, flat from ring 3 (the research's skill bucket); form budgets flat after Act I |
| Sect tree | Stays on Sect › Role |
| Scope | Keep the full target; halve the path arts if it must shrink |
| Teaching lost arts | Singles from Dao tier 4; lineages never |
| Unfound lost and secret arts (roadmap §6 decision 19) | Unknown until found: no hints, no sources, no silhouettes, no Track, no companion's tip; each act's are only counted; a found art shows its full card |
| Inner Arts and Secret Arts | Inner Arts in the loadout dock with the stance; Secret Arts a tab of their own, last |
