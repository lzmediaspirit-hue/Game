# Build Prompt v2 audit

*Jade River · Build Prompt, revision 2* (25 September 2026) folds the Xianxia Systems Gap Report into the build
prompt. It adds seven systems and the content they need:

- S43 traversal and room verticality;
- S44 pill depth;
- S45 herbs;
- S46 spirit beasts;
- S47 treasures;
- S48 paths, heart and heaven;
- S49 karma and the living world.

It also edits many existing sections, among them the resolved conflicts, the HUD layout, the unlock timeline,
the save format and the milestone prompts. v2 says it wins wherever it disagrees with older material. That
includes what phases G1 and G2a built from the gap report, so those were audited too.

The audit compared every concrete requirement in v2 with the build as it stood after G2a (commit 800f3a1). A
requirement is a rule, number, name, data file, field, event, UI element or test. Each was classed as:

- **Present:** as specified.
- **Differs:** built, but with other names, numbers or behaviour.
- **Partial:** part of it is built.
- **Missing:** not built.

The detailed tables, with file:line evidence and the change each row needs, are in `docs/v2_audit/`.

| Packet | v2 sections | Present | Differs | Partial | Missing | Rows |
|---|---|---|---|---|---|---|
| [Traversal](v2_audit/p1_traversal.md) | S43, room verticality catalogue, movement findings | 27 | 64 | 94 | 88 | 273 |
| [Pills](v2_audit/p2_pills.md) | S44, pill families, herb natures, fires and furnaces, new forms, Alchemist Guild | 43 | 44 | 20 | 95 | 202 |
| [Herbs](v2_audit/p3_herbs.md) | S45, rare herb nodes | 5 | 7 | 10 | 65 | 87 |
| [Spirit beasts](v2_audit/p4_beasts.md) | S46, beast kings, skill books, pet gear | 2 | 8 | 15 | 90 | 115 |
| [Treasures](v2_audit/p5_treasures.md) | S47, treasures, talismans, throwables, salvage | 43 | 48 | 19 | 152 | 262 |
| [Paths, heart and heaven](v2_audit/p6_paths.md) | S48, fates, physiques, body tiers, vows, Inner Arts, combos | 26 | 12 | 34 | 162 | 234 |
| [Living world](v2_audit/p7_world.md) | S49, karma, bonds, factions, calendar, fortune, tower, activity | 19 | 16 | 39 | 132 | 208 |
| [Changes to existing sections](v2_audit/p8_changes.md) | Part 1–7 edits: conflicts, HUD, saves, events, unlocks, milestones | 43 | 50 | 60 | 128 | 285 |

Some rows are counted in more than one packet, because each packet also carries v2's priority table, stay-out
list and new events.

## What the audit found

**The build calls itself 1.1, so every v2 row tagged v0.4 to v1.1 is due.** Most of S43–S49 is not built yet.
Phases G1 and G2a matched the gap report, but many of their names, numbers, sources and files differ from v2's
Part 8.

Defects found along the way, all fixed:

- Refined pills lost their gold marks on the way into the bag (dbeff8c).
- A breakthrough consumed support pills that the risk preview had already rejected, and counted them toward the
  +5 heart demon for two or more supports (a5aa5cd).
- Arrows, Qi projectiles and throwables flew over 30 of the 75 monsters (800f3a1).

The heart-demon numbers now follow v2 (a5aa5cd):

- Calm Incense −20;
- +1 per 10 sin;
- meditation −1 per 5 minutes;
- passing the Heart Trial −30.

## Plan

v2 is the reference from here on. Each phase follows v2's order of work, and ends with rules tests, a full test
run and a pushed commit:

1. data;
2. authority rules;
3. UI;
4. rules tests.

| Phase | Contents |
|---|---|
| **V1 · Align what exists** | Treasures, throwables, the talisman treasure and vessels take Part 8's names, numbers, costs and sources, with `treasures.json`. "A Treasure in Hand" and the Practice Bell. HUD positions and keys. Event names (`treasure_used`) and the event contract for G1/G2 events. G1's pill rules take v2's numbers: resistance steps, explicit families, Settle 5/5, mark ranges, Halo in storage, per-recipe Soul effect. |
| **V2 · Traversal (S43)** | Per-side edges, blocks, climbables, movers, volumes, `void_altitude` and camera bounds in room data. Coyote time and jump buffer. The double jump gated at QU6 (impulse 430). The v2 Wall-Step, climb mode, Drop Through, Ledge Mantle, Plunge, Glide, Swallow Dart and Water Skimming, each with its quest. Flight by holding Jump. The context button. Fall cost. Navigation graph for enemies and pets. Camera. The room catalogue re-built to the 88/100 grid. Room lint, reach-contract tests and traversal events. |
| **V3 · Treasures and gear (S47)** | Forge tabs for Enhance with pity, Inherit and Salvage (`salvage.json`). Talisman craft with Old Scribe Bai and tracing. Sword Release and Sword Intent. Dual loadout. Self-detonation. Rogue cultivators. Blood-drop bind. Natal treasure. Affix lock. Wardrobe. Relics. |
| **V4 · Pills (S44)** | Furnace line and slot. The valley Heavenly Flame. Beast Fire rank. Herb natures, roles and conflicts. Qi Flow Pill, oils, baths, draughts. Alchemist Guild. Recipe fragments and experiments. Pill tribulation. |
| **V5 · Paths, heart and heaven (S48)** | Breakthrough fates. Core Forging grade. Heavenly tribulation. Qi Deviation. Inner Arts. Technique grades. Stances. Combos. Body tiers. Vows. Physiques and named roots. Nascent-soul escape. |
| **V6 · Herbs (S45)** | Node age and flags. Harvest tap. Seeds. Ripening and guardians. Garden page and beds. Spirit Soil. Racks. Raids and fakes. Seasons. |
| **V7 · Spirit beasts (S46)** | PetState. Beast ranks, natures and cores. Grievous Wound. Taming fix. Incubation. Bloodline and aptitude. Mount slot. Capacity. Spirit Beast Bag. Contracts. Skill books and pet gear. Beast Kings and the Beast Tide. |
| **V8 · Living world (S49)** | Relations and Calendar authorities. Karma deeds and debts. Affinity and gifts. Bonds. Grudges and bounties. Idle-room eligibility. Auto-path. Valley auction. World events. Fortune deck. Trial Tower. Activity chests. |

Progress is recorded in `docs/CHANGELOG.md`.

### Status

- **V1** and **V2**: done.
- **V3**: done (V3a–V3c), except these v1.1+ items, left for a later pass:
  - the sword swarm;
  - weapon awakening and legendary chains;
  - imitation relics;
  - Artifact Spirit depth (affinity, barks, devour);
  - the heavy sabre, flute and fan weapon families;
  - the rooftop thief chase (S43 rule 15).
- **V4**: done, in five parts (V4a–V4e: furnaces; herb natures and conflicts; new forms; fragments, experiments and
  the guild; pill tribulation), except these, which wait on later phases:
  - the Beast Marrow Washing Pill, the Beast Revival Pill and the Purifying Offering (with S46, V7);
  - the Guild's Master rank (Azure Expanse, not defined by the spec);
  - the full five-screen furnace mini-game (the three strikes are labelled Extraction, Fusion and Condensation).
- **V5a**: done (body ladder, Core Forging grade, named roots, physiques). Hollow-Touched is in the data but cannot
  trigger until Hollowing can pass the valley cap (v1.2).
- **V5b**: done (heavenly tribulation, breakthrough fates, Qi Deviation). Fox Spirit's Favour waits for pet purity
  (S46).
- **V5c**: done (Inner Arts, stances, technique grades, combos).
- **V5d**: done (vows, epiphany, Killing Intent, Blood Burning, the false realm with veiled dialogue and bandit
  ambushes, the nascent-soul escape, the Comet Captain's self-detonation). S48 is complete.
- **V6a**: done (herb ages, rare nodes with ripening, guardians and seasons, the harvest tap, seeds, the Codex
  calendar).
- **V6b**: done (garden beds and the Garden page, field grades, Spirit Soil, spring water, transplanting, the
  Verdant Dew Vial; Cloud Sect beds). The 10,000-year herbs of the Azure Expanse wait for their nodes (v1.1).
- **V6c**: done (steaming and wine racks with prep carried into pills, sealed and fake merchant herbs with
  appraisal, garden raids with Guard pets and formations). Treasure births and gathering trials move to V8 with the
  S49 world calendar.
- Next:
  - V7 (S46 beasts). V7a is done: pet state depth, beast ranks and natures, cores and the Core Exchange, Grievous
    Wound and the Beast Revival Pill, the Purifying Offering and the taming fix. V7b is done: bloodline awakenings
    at 50 and 90, trait strength, Beast Essence Blood, suppression, the Equal and Blood Contracts, command capacity
    with a party beside you, incubation input, 3-heart hatchlings, the Beast Marrow Washing Pill and Fox Spirit's
    Favour. V7c is done: skill books (five of six sources; Guardian Spirit's waits for the Trial Grove), pet gear,
    fusion, pet breakthroughs with Pet Core Formation, and the Growth tab. V7d is done: Spirit Beast Bags and field
    swaps, the Mount slot and the HUD pet strip, the Riverstone Ox and Cloud Stag, rarity rolls for tames and eggs,
    Beast Kings with their zone buff and nests, and the weekly Beast Tide. V7e is done: the Beast Arena ladder with
    pet auto-battles, the daily Beast Trial Grove, Beast Taming Dao tiers 3-6, the Pavilion Feeding Trough and
    renaming. S46 is complete except the Insect Swarm (v1.2) and Dao tiers 5-6 (hooks, later ages);
  - V8 (S49 living world, with S45's treasure births and gathering trials). V8a is done: the Relations authority
    owns the karma ledger (old saves migrate), karma.json deeds from effects, code and events (Part 8's +30
    cleansing and +2 healing), the righteous-demonic alignment with its requirement kinds and first gates, personal
    Fame with its tiers, town greetings and Young Master challenges, and the Relations page. V8b is done: NPC hearts
    with Part 8's favourite gifts, one gift a day, heart rewards and keeper discounts, companion duels, sworn
    siblings, the Dao Companion (support slot, shared insight, resonance meditation) and the master with The Elder's
    Last Lesson. V8c is done: grudges against three factions with hunters, blood money, a duel, Old Scores and a
    story-bound ring; the town bounty board; Part 8's surrender choice, named debts (Dou, the lieutenant, his brother)
    and the night peddler. V8d1 is done: the Calendar authority and page, seeded world events (rifts, the shrine and
    cave reopenings with realm caps), seasons from the account's first week, weather tables and notifications. V8d2
    is done: the Saturday auction day on Market Street (seeds, eggs, recipe scrolls that teach on the hammer), Spirit
    Fruit treasure births with rivals and a guardian, the weekly Herb Terraces gathering trial with its ranking, and
    weather effects and visuals. V8e is done: the fortune deck with its meter (one encounter per three hours of
    play) and the Hidden Grotto, heavenly phenomena with NPC reactions and a jealous challenger, and lifespan as a
    display with ageing people and longevity treasures. V8f is done: the Heaven Ranking with its seeded cultivators,
    entry by CP or the finals and rank challenges; the 30-floor Trial Tower with four floor rules and a daily sweep;
    the four daily activity chests on the Quests page. V8g1 is done: idle Hunt and Gather only in eligible rooms,
    the auto-hunt toggle with its cut-offs, and quest auto-path over the room graph with the tracker button and a
    validation sweep. V8g2 is done: the County Hall with Magistrate Qian, three county jobs a day by Level, county
    favour with its tiers, titles and Stoneford discount, the relief fund, non-interference sin in mortal towns, the
    guqin rhythm page (a meditation bonus), chess problems at every insight stone, and regional teas. Next: V8g3
    (territory and spirit mines).
