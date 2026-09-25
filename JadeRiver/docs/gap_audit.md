# Gap report audit

This audit checks every proposal in *Jade River · Xianxia Systems Gap Report* (25 September 2026) against the
build as it stood at commit a92519f. Each row is classed:

- **Present:** the system exists as proposed.
- **Partial:** a related piece exists, but part of the proposal is missing.
- **Missing:** nothing like it exists yet.

The evidence column cites the code or data that decided the class. The **Plan** column gives the implementation
phase from the table at the end. The report's "stay out" list is checked separately at the bottom.

**Totals:** 111 proposals.

| Status | Count |
|---|---|
| Present | 2 |
| Partial | 38 |
| Missing | 71 |

The game breaks none of the ten "stay out" rules.

## 1. Pills and alchemy (report §"Pill cultivation")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 1 | Lifetime pill resistance (`pill_resistance {family: count}`, ÷(1+0.25·count), −1 per major breakthrough) | Missing | Only a 300 s same-pill repeat penalty ×0.5 (`inventory_authority.gd` `use_item`, `cultivator_state.pill_memory`) | G1 |
| 2 | Foundation solidity (pill/core share of a realm's QP; >30 % → "Foundation: hollow", +1 risk, Weak-foundation failure; Settle foundation focus) | Partial | `weak_foundation` failure and +1 risk for an unstable foundation exist (`stats.py`, `progression_rules.risk_index`); no QP-share tracking | G1 |
| 3 | Residual impurities (5 % of toxicity; −1 % accumulation per 10; cleared by flawless Cleansing, bath or Settle foundation) | Missing | Toxicity is a single draining float (`progression_authority.apply_toxicity`) | G1 |
| 4 | Heart-demon cost of pill-forced breakthroughs (+5 each with ≥2 support pills) | Missing | Calm Incense "clears Heart Demons" in text only (`items.py`) | G1 |
| 5 | Fire slot: charcoal, Earth Fire (vent rooms), Beast Fire (a core per batch), Heavenly Flames (absorbed, in the Codex) | Missing | Cores are recipe inputs only; the furnace bonus comes from the station | G1 |
| 6 | Furnaces as equipment (band width, batch cap, impurity filter, element, yield chance); Nine-Dragon Cauldron | Missing | `bronze_furnace` is a tool whose power is never read | G1 |
| 7 | Pill marks (0–9 gold lines, +2 % each) and a pill-cloud VFX on Halo/Soul | Partial | Rare-quality toasts (`hud.gd`) and a bag glow (`page._pill_glow`) | G1 |
| 8 | Pill tribulation mini-game screen | Missing | — | G6 |
| 9 | Pill Soul "flight" catch | Missing | The Soul effect is rolled on use | G6 |
| 10 | Decay rule stated (none); Grain = −50 % toxicity and ignores resistance; Halo grows in density | Partial | Grain toxicity ×0.5 and Halo growth exist (`apply_halo_growth`); "never decays" is not stated | G1 |
| 11 | Herb nature (hot/cold) and recipe roles; conflicting pairs blast the furnace | Missing | The mini-game band is random (`crafts_page.gd`) | G5 |
| 12 | Recipe fragments and Deduce | Missing | Recipes are learned whole | G5 |
| 13 | Experimentation mode (Murky Pill; attempts logged) | Missing | `recipe_check` needs a known recipe | G5 |
| 14 | Alchemist Guild (rank exams, badge, guild shop, commissions) | Missing | Alchemist NPCs and XP ranks only | G5 |
| 15 | New pill forms: poison pills, weapon oils, liquid medicines, medicinal baths, Qi Flow Pill | Missing | Items are only "pill" or "food" | G2 (oils, baths), G5 (rest) |
| 16 | Eat herbs raw (30 %, ×2 toxicity) | Missing | Herbs have no `use` | G1 |
| 17 | Auto-refine gives 25 % profession XP | Missing | `collect_auto` gives no XP | G1 |

## 2. Herbs and gathering (report §"Herb harvesting")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 18 | Guardian beasts on rare nodes | Missing | Rare nodes are gated by rank only (`world.py` `HERB_RANK`) | G3 |
| 19 | Ripening windows, Spirit Sense countdown, early pick −1 age | Missing | Nodes are ready/depleted on a 240 s timer | G3 |
| 20 | Harvest timing tap (perfect = full age + 10 % seed) | Missing | A 1.5 s channel, then `complete_node` | G3 |
| 21 | Seed sources (shops, 10 % of perfect harvests, rare seeds from secret realms) | Missing | Only `evergreen_heart_seed` | G1 |
| 22 | Garden beds with field grades, Spirit Soil, bottled spring water | Missing | `garden_bed` objects open the Crafts page; `crafting.garden` is unused | G3 |
| 23 | Transplanting (spade) | Missing | — | G3 |
| 24 | Verdant Dew Vial (ages a bed) | Missing | — | G3 |
| 25 | Steaming and wine-soaking racks | Missing | `drying_rack` is an inert tool | G3 |
| 26 | Treasure births (world event with rivals and a mini-boss) | Missing | The room-event framework could host it | G4 |
| 27 | Gathering trials (sect event dungeon) | Missing | — | G4 |
| 28 | Seasons (rare herbs flower in named seasons) | Missing | Only the Evergreen tree's 7-day fruit cycle | G3 |
| 29 | Garden raids and fake herbs revealed by Appraisal | Missing | Sect raids hit buildings; Appraisal only reads curios | G3 |
| 30 | Herbs never perish | Present | No expiry on bag stacks | — |

## 3. Spirit beasts (report §"Spirit beasts")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 31 | `beast_rank` 1–9 on wild monsters (nameplate, Bestiary, core grade, taming) | Missing | Enemies carry level and realm index only | G3 |
| 32 | Spirit / demonic / Hollowed nature; Purifying Offering; cleanse before taming | Partial | A `hollow` element on Hollowed foes; taming checks `tameable` | G3 |
| 33 | Cores at every rank (2 %×rank), Core Exchange, pets devour cores | Partial | A few named cores drop from specific foes | G3 |
| 34 | Bloodline purity 0–100 (rolled at hatch; awakenings at 50 and 90) | Missing | Pets have `rarity` only | G3 |
| 35 | Bloodline suppression (Fear, +10 % taming) | Missing | — | G3 |
| 36 | Contract types (master–servant, Equal at 10 hearts, Blood) | Missing | One bond meter, 0–10 hearts | G3 |
| 37 | Command capacity by Soul (1 → 2 → 3 active) | Missing | One `active_pet` | G6 |
| 38 | Aptitude and growth rolls; Beast Marrow Washing Pill | Partial | Rarity plus three hidden traits | G3 |
| 39 | Skill books and learned slots | Missing | Species skills are display strings | G3 |
| 40 | Fusion (sacrifice for traits, skills, purity) | Missing | Breeding only | G6 |
| 41 | Pet equipment (collar, talisman, saddle) | Missing | `saddle` is only a sprite offset | G3 |
| 42 | Pet breakthroughs (breakthrough dialog, support items, core grade) | Partial | `evolve_gates` check level, hearts and owner realm | G6 |
| 43 | Grievous Wound after 3 knockouts in 5 minutes | Partial | A 60 s retreat at 0 HP | G3 |
| 44 | Spirit Beast Bag (2–6 carried pets) | Missing | Unlimited `pets`; one active | G3 |
| 45 | Separate mount slot and mount-only species | Partial | Mount is a role of the active pet | G3 |
| 46 | Incubation inputs (essence blood, element stones) | Missing | `incubate_egg` takes only the egg | G3 |
| 47 | Beast tides and Beast Kings | Partial | Field-boss timers; sect raids every 2–3 days | G4 |
| 48 | Beast Arena and Beast Trial Grove | Missing | Only the player's sparring post | G6 |
| 49 | Pet QoL: rename, lock, colour variants, feeding trough | Partial | A `rename_pet` intent with no UI | G3 |
| 50 | Beast Taming Dao tiers 3–6 | Partial | Two tiers, valley cap 2 | G3 |
| 51 | Insect swarm companion | Missing | — | G7 |

## 4. Treasures and weapons (report §"Treasures")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 52 | Treasure quick slot (Bell, Pagoda, Mirror, Seal, Cauldron, Banner, Gourd) | Partial | One consumable quick slot (`hud.gd` `use_quick`) | G2 |
| 53 | Flying sword (Sword Release) | Partial | Seeking projectiles exist (`flying_blades`) | G2 |
| 54 | Sword swarm | Missing | — | G6 |
| 55 | Sword Intent stacks; Sword Domain | Missing | Sword Dao tiers only | G2 (intent) |
| 56 | Natal treasure (grows; can break with an injury) | Missing | — | G6 |
| 57 | Talisman craft (stroke trace; attack, defence, movement and sealing talismans) | Partial | The Revival Talisman is inscribed under Formations; paper and ink items exist | G2 |
| 58 | Talisman treasure (3 charges of a high technique) | Missing | Talismans are single-use | G2 |
| 59 | Throwables (needles, knives, thunderclap pellets) | Missing | A knife-throw technique only | G2 |
| 60 | Enhancement pity (+5 % per failure, on the item) | Missing | +6 and up fail at 12 %/level with nothing stored (`crafting_authority.enhance`) | G2 |
| 61 | Enhancement transfer (inherit N−2 levels) | Missing | — | G2 |
| 62 | Salvage (dismantle into materials) | Partial | `CraftingAuthority.salvage` exists, **but no page offers it, nor Enhance** | G2 |
| 63 | Affix lock (reroll with one locked) | Missing | Affixes are rolled once; there is no reroll | G2 |
| 64 | Wardrobe override per slot | Partial | Per-item `appearance`; chosen only at creation | G6 |
| 65 | Dual weapon loadout and swap | Missing | An unused `loadouts` array | G6 |
| 66 | Rogue cultivators with visible, guaranteed gear and sealed pouches | Partial | Rogue disciples are normal foes; Appraisal reads curios | G4 |
| 67 | Broken and imitation treasures | Missing | Relics are sealed until bound | G6 |
| 68 | Weapon awakening at +10; legendary chains | Missing | Enhance stops at +10 | G7 |
| 69 | Artifact Spirit depth (affinity, barks, awakening, devour) | Partial | Dormant→awake via `subdue_spirit` | G6 |
| 70 | Flight vessels (sword, cloud, gourd, leaf) | Partial | Flight costs QI/s; a flying mount halves it | G2 |
| 71 | Blood-drop bind animation on first equip | Partial | A timed bind bar and toast | G2 |
| 72 | New weapon families (sabre, flute/guqin, fan, brush, bell, dual blades, umbrella, whip, rope dart) | Missing | Seven families: fists, gauntlets, jian, spear, short blade, staff, bow | G7 |

## 5. Paths and core mechanics (report §"Different paths")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 73 | Body refining ladder (Copper/Iron/Jade/Gold Body; HP-cost body arts; Gold Body ignores Qi Seal) | Partial | `body_level`, the Temper focus and body gates exist | G5 |
| 74 | Sword path | Partial | Jian combos, Qi arcs, Sword Dao | G2 |
| 75 | Soul line (illusion, soul search, sense lock) | Partial | Two soul techniques and the Sense pulse | G5 |
| 76 | Blood path (HP-cost arts, lifesteal, blood essence) | Partial | Blood Dao stat tiers only; no lifesteal anywhere | G7 |
| 77 | Buddhist vows and merit | Missing | — | G7 |
| 78 | Confucian written word, Righteous Qi | Missing | — | G7 |
| 79 | Music path | Missing | — | G7 |
| 80 | Poison path (player poisons, Poison Body) | Missing | Poison is enemy-only | G7 |
| 81 | Formation/talisman/puppet caster in combat | Partial | Array plate is a one-use buff; puppets only gather | G2 |
| 82 | Sect role variants (damage/support tree bought with contribution) | Missing | Contribution buys shop goods only | G5 |
| 83 | Heart-demon meter (0–100) | Missing | — | G1 |
| 84 | Heavenly tribulation from Cloud Stride | Missing | A lightning hazard exists to reuse | G2 |
| 85 | Core Forging grade rolled from preparation | Partial | Purity 9→1 exists; always starts at 9 | G2 |
| 86 | Breakthrough fates (pick 1 of 3) | Missing | — | G2 |
| 87 | Named roots and physiques | Partial | Hidden ±15 % aptitudes | G5 |
| 88 | Qi Deviation debuff | Missing | Failures give injury or instability | G2 |
| 89 | Epiphany | Missing | Contemplate and insight stones exist | G5 |
| 90 | Costly secret arts (Blood Burning, self-detonation) | Missing | Secret arts are utilities | G5 |
| 91 | Hide cultivation and Killing Intent | Missing | Concealment halves aggro range | G5 |
| 92 | Inner Arts passive slots | Missing | Secret arts are always on | G5 |
| 93 | Technique grades, stances, combo chains | Partial | Basic combos; one parry stance | G5 |
| 94 | Nascent-soul escape at death | Missing | Death costs 10 % progress | G5 |

## 6. Living world (report §"A living world")

| # | Proposal | Status | Evidence | Plan |
|---|---|---|---|---|
| 95 | Karma ledger (merit, sin, named debts) | Missing | — | G1 |
| 96 | Righteous–demonic alignment | Missing | Alliance/Independent path flags only | G7 |
| 97 | NPC affinity 0–5 hearts and gifts | Missing | Companion `bond` is never written; pets have hearts | G4 |
| 98 | Formal bonds (Dao Companion, sworn siblings, master inheritance) | Partial | Story beats and paired cultivation | G4 |
| 99 | Grudges and bounties | Missing | Per-faction reputation exists | G4 |
| 100 | Personal Fame track | Missing | Sect Prestige and titles only | G4 |
| 101 | World-event scheduler and Calendar | Partial | Sect raids, the war gong, field-boss timers, daily/weekly resets | G4 |
| 102 | Fortune encounters | Missing | Fortune affects drops and crits | G4 |
| 103 | Heavenly phenomena on breakthroughs | Partial | A spiral, ring and shake (`world.gd`) | G2 |
| 104 | Rankings (Heaven Ranking) | Missing | — | G7 |
| 105 | Profession associations (guilds, exams, commissions) | Partial | Profession ranks by XP | G5 |
| 106 | Territory and spirit mines | Missing | Sect expeditions only | G7 |
| 107 | Mortal kingdom | Missing | — | G7 |
| 108 | Weather tags | Partial | Fixed per-room hazards; day and night | G7 |
| 109 | Lifespan as flavour | Missing | — | G7 |
| 110 | Mobile conventions (auto-path, tower sweep, activity chests, auto-hunt) | Partial | Dailies, weekly, idle hunt; the tracker's `target_room` is unused | G4 |
| 111 | Leisure arts and teahouse | Partial | The Stoneford Tea House sells timed teas | G7 |

## "Stay out" list: no violations

| Rule | Build |
|---|---|
| No hard lifespan | None |
| No stamina or energy gates | None |
| No item decay | None |
| No pet permadeath | Pets retreat into their token at 0 HP (`pet_authority.gd`) |
| No destructive enhancement | A failed enhance consumes materials only (`crafting_authority.enhance`) |
| No sexual dual cultivation | Paired cultivation is meditating beside a companion |
| No player full-loot | None |
| No Gu path | None |
| No corpse refining or body seizing for players | None |
| No stat or aptitude pills in shops | Shops sell timed buffs, cures and progress pills only |
| No unrestricted auto-battle | The idle hunt is abstract offline income. G4 limits it to idle-eligible rooms |

## Implementation plan

The phases follow the report's own priority table (§"What to add first"). Each phase ships with:

- data from `tools/data`;
- authority rules;
- UI;
- rules tests;
- a valley-run step where the loop needs one.

Each phase is committed on its own.

| Phase | Report priorities | Contents |
|---|---|---|
| **G1** | 1, 2, 3 | Undefined S15 rules: fire slot, furnaces, "pills never decay", seeds, auto-refine XP, raw herbs. Pill resistance, foundation share with Settle foundation, residue. Heart-demon meter. Karma ledger. Pill marks and the pill cloud |
| **G2** | 4, 7, 8 | Treasure slot and treasures. Sword Release and Sword Intent. Talisman craft and throwables. A forge page for enhance (with pity), transfer, salvage and affix lock. Heavenly tribulation, Core Forging grade, breakthrough fates, Qi Deviation and phenomena. Oils and baths. Flight vessels. Bind animation |
| **G3** | 5, 6, 11 | Pet depth: purity, aptitude, contracts, Grievous Wound, beast ranks and cores, gear, mount slot, beast bag, skill books, incubation inputs, QoL. Herb flags: guardian, ripening, season, seed, fake. Harvest tap, garden beds, racks, dew vial, transplanting |
| **G4** | 9, 10 | World-event scheduler and Calendar page (beast tides, capped secret realms, auction days, treasure births, gathering trials, rogue cultivators). NPC hearts and gifts, bonds, grudges and bounties, Fame, fortune encounters. Auto-path and activity chests |
| **G5** | 12, 13 | Body ladder, soul line, sect role trees, Inner Arts, technique grades, stances and combos, roots and physiques, epiphany, costly arts, concealment and Killing Intent, soul escape. Alchemist Guild, herb nature and roles, fragments, experimentation, new pill forms |
| **G6** | 11, 12 (v1.1 set) | Pet fusion, breakthroughs, command capacity, Beast Arena. Sword swarm, natal treasure, dual loadout, wardrobe, relic restoration, spirit depth. Pill tribulation and Soul catch |
| **G7** | 14, 15 | Alignment, Blood/Buddhist/Poison/Confucian/Music paths, new weapon families. Rankings, territory, mortal kingdom, weather, lifespan display, insect swarm, awakening chains, leisure arts |

Progress on each phase is recorded in `docs/CHANGELOG.md`.
