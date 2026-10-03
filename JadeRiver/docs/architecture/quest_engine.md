# The quest engine (E5)

Audit 45 §6.5, phase 3. A side quest used to be a `quest(...)` call in `story.py`. Its target room, the realm it opens
at and its pay were each chosen by hand, and the daily mission board was a hand table in `economy.py`. Now a side quest
is one `side(...)` spec and a daily job is one `job(...)`. The engine derives where a quest leads, when it opens and
what it pays, and writes the rows the game has always read. The game reads nothing new.

Decision 45 made quests pay a fixed amount of cultivation instead of a share of the player's stage. The engine's band
table makes that one rule for side quests: a quest pays its band's cultivation and its band's money.

| File | What it holds |
|---|---|
| `tools/content/quests/spec.py` | the spec language: `side()`, the templates (`clear`, `fetch`, `deliver`, `gather`, `talk`, `spar`, `escort`, `reach`, `step`), `daily()` and `job()`, the reward parts (`item`, `fx`, `taels`, `stones`, `crystals`), `AUTO`, `PAY`, `DROP`. Its docstring is the format |
| `tools/content/quests/bands.py` | the band table: what a side quest pays at its tier |
| `tools/content/quests/engine.py` | the world it reads, the compile, the pay settled at the tier, the daily board, the checks and the command line |
| `tools/content/quests/tests.py` | the engine's own tests (`engine.py --check` runs them) |
| `tools/content/quests/specs/<module>.py` | the quests, in modules; `specs/__init__.py` lists the sections `story.py` places and the modules in each |

```
python3 tools/content/quests/engine.py --check      # the engine's gate (tools/run_tests.sh and Test.ps1: quest_engine)
python3 tools/content/quests/engine.py --list       # every quest: its section, tier, room, realm and pay
python3 tools/content/quests/engine.py --show ID    # one quest: the row, what was derived, what is pinned, its band
python3 tools/content/quests/engine.py --bands      # the band table
python3 tools/content/quests/engine.py --diffs      # the quests that pay otherwise than their band, or sit far from their room
```

## What a spec writes

| What | Where it goes | Host |
|---|---|---|
| the quest's row: its steps, texts, giver, `requires`, `target_room`, rewards and the rest | `data/quests.json` | `story.py` places each section with `Q.extend(QE.rows(section))` among its hand quests. After `quest_tiers` has found each quest's tier, `QE.settle(Q)` fills in each engine quest's pay from its band |
| its cultivation | the row's `tier` and `cultivation` | `story.py` `quest_tiers`, phase 1's rule, unchanged: the band table's cultivation is the same number |
| a daily job | `data/mission_templates.json` | `economy.py` `missions()` takes `QE.missions()` |
| its strings | `data/strings/en.json` | `economy.py` `strings()` reads the built quests. A quest that teaches an art names its source there |

Every quest's row now has one layout, `QE.quest_row`. `story.py`'s `quest()` writes its hand quests with it. The
objective, item and effect constructors have their one home in `spec.py`, and `story.py` imports them.

## A spec

Here is the audit's own example, The Muddy Wash (`specs/valley.py`):

```python
side("the_muddy_wash", clear("reedtail_rat", 6, "Chase the Reedtail Rats off the washing lines"), giver="washer_mei",
     offer="Rats in the reeds again. They chew the lines and drag the washing through the mud. Six of them, at least.",
     done="Clean sheets for once. Bless you.", realm="bone_forging_3"),
```

From this spec the engine derives:
- the name, "The Muddy Wash", from the id;
- the target room, `lf_reed_shallows`, where the reedtail rats spawn;
- the pay, 40 taels, from the Bone Forging 3 band. The band's cultivation, +120, is what `quest_tiers` pays at that
  tier.

Its realm is pinned: the Reed Shallows' band of Levels (1 to 3) would open it at Bone Forging 2, and the hand quest
opened at 3.

A new quest needs no pins. Claws for the Grindstone (`specs/valley_new.py`) is Apprentice Tao's:

```python
side("claws_for_the_grindstone", fetch("mole_claw", 5, "Bring Ironclaw Mole claws from the Lower Pit"), giver="apprentice_tao",
     offer=["Master Bao's grindstone has gone smooth as a river pebble. Nothing dresses a stone like a mole's claw.",
            "The Lower Pit is full of them. Five claws, and don't tell him it was my idea."],
     done=["Hear it bite? He'll say the stone was always this good.", "Here. Apprentice pay, but it's honest."]),
```

From this spec the engine derives:
- the target room, `sq_lower_pit`: the claws drop from Ironclaw Moles, and most of them spawn there;
- `requires`, Bone Forging 6, the realm at the middle of the Lower Pit's band (Levels 5 to 7);
- the tier, Bone Forging 6, which `quest_tiers` finds from that floor;
- the pay, 90 taels, from the Bone Forging band (5 to 9), with +310 cultivation.

`engine.py --show claws_for_the_grindstone` prints all of this.

## The templates

Each template makes one objective (escort two), the row `o()` always wrote. Each step's `text` is its line in the
quest log. Every migrated quest gives its own text. When a new one leaves it out, the text is made from the names:
"Defeat Reedtail Rats", "Bring Mole Claws", "Gather Willow Moss", "Mine Jadeiron", "Talk to Elder Gao".

| Template | Objective | Where it leads (`target_room`) |
|---|---|---|
| `clear(enemy, n)` | `kill` | The room where most of the foe spawn (by the spawns' `max`), then the lowest band, then the first by id. A spawn gated by `requires` (a quest's own boss) and a wild pet don't count |
| `fetch(item, n, consume=True)` | `collect` | Where the item comes from: the rooms where its droppers spawn (the monster engine's loot, `loot_tables.json`; a quest drop counts for its own quest only) and its herbs, ores, swarms and sighting stones. It picks the one with the most |
| `deliver(item, n)` | `deliver`, always handed over | nowhere: a thing made or bought |
| `gather(item, n, craft=)` | `gather_node` | the room with the most of its nodes |
| `talk(npc)` | `talk_to` | their home (the NPC engine's first place), unless they give the quest or take it back |
| `spar(opponent)` | `win_spar` | the room of their spar post, or of them, unless they give the quest |
| `escort(npc, to)` | `talk_to`, then `reach_room` | `to` |
| `reach(room)` | `reach_room` | the room |
| `step(kind, text, n, **fields)` | anything else (`set_flag`, `use_system`, `hit_object`, `meditate_seconds`, `buy_item`, `reach_realm`) | nowhere |

A quest leads to the room of its first step that leads anywhere.

## What the engine derives

- **`target_room`**: from the steps, as above.
- **The realm it opens at**: the realm at the middle Level of the target room's band (`level_range`).
  - This applies only to a quest that follows no other. A quest that follows another opens when the story gets there.
  - A town has no band.
- **`requires`**: the quests it follows (`after`, `quest_done` each), the quests it runs during (`during`,
  `quest_active`), then the realm, then its other conditions (`needs`: an unlock, a companion owned). This is the
  order the hand quests had.
- **The pay**: the band table's at the quest's tier, settled once `quest_tiers` has found it. It goes first among the
  rewards, or where the spec's `gives` puts `PAY`.
- **The row's keys**: `requires`, `offered_by_unlock`, `chapter` and `target_room` first (`spec.ORDER`), then the spec's
  other keys in its own order (`on_accept`, `marker`, `giver_any`, ...).
- **The giver and the people**: NPC engine ids, or one of `story.py`'s one-off rows. Every item it names or gives is
  in `items.json` or `artifacts.json`, the item engine's families and one-offs.

## The band table

`bands.py`: a band is a run of Levels with one need. A band's cultivation is therefore one number: the side quest's
share of that need (`curves.json` `quest_cultivation`), rounded as a reward (`realms.cultivation`). That is phase 1's
rule, so it equals what `quest_tiers` pays at every tier in the band. The cultivation is not written in the table.
It follows the curves and `realms.json`, so it cannot drift.

The money is written, a sum for each band. Each sum is the middle value of the hand quests in that band, and the sums
rise in between where no hand quest stood. The currency follows the act: taels in Act I, spirit stones in Act II, sage
crystals in Act III. Act II and III pay the smaller share their longer stages were tuned for (`act2_side`).

| Band | Levels | Need | Cultivation | Pay |
|---|---|---|---|---|
| Bone Forging 1 | 1 | 600 | +60 | 30 taels |
| Bone Forging 2 | 2 | 900 | +90 | 40 taels |
| Bone Forging 3 | 3 | 1,200 | +120 | 40 taels |
| Bone Forging 4 | 4 | 1,600 | +160 | 60 taels |
| Bone Forging | 5–9 | 3,100 | +310 | 90 taels |
| Qi Kindling | 10–18 | 5,300 | +530 | 120 taels |
| Qi Unfurling | 19–27 | 4,700 | +470 | 200 taels |
| Heart Tempering | 28–36 | 6,700 | +670 | 200 taels |
| Cloud Stride | 37–45 | 8,000 | +800 | 250 taels |
| Spirit Awakening | 46–54 | 8,700 | +870 | 300 taels |
| Heaven Glimpse | 55–63 | 30,000 | +3,000 | 400 taels |
| Sage | 64–72 | 315,000 | +13,000 | 90 spirit stones |
| Sage Sovereign | 73–81 | 60,000 | +2,400 | 120 spirit stones |
| Will Manifest | 82–90 | 99,900 | +4,000 | 25 sage crystals |
| Sphere Lord | 91–99 | 99,900 | +4,000 | 30 sage crystals |
| Law Touching, Monarch, the Heaven's Gate, Inner Heaven | 100–165 | 120,000 to 200,000 | +4,800 to +8,000 | 40 to 80 sage crystals |

The Mortal band (Level 0, +50, 30 taels) holds the prologue's errands, which stay hand-written.

**What it pays an hour (balance_sim).** The pacing counts each side quest as ten minutes of detour
(`balance.json` `quest_minutes`). `balance_sim` now shows what each band's side quests pay an hour of that detour,
against what an hour of the session's mix gathers and earns at their tier. Two new checks hold it for Act I, the act
the pacing is tuned for:
- cultivation 0.1 to 5 times the session's hour;
- taels 0.2 to 2.5 times, for the quests that pay taels.

| Band | Side quests | Cultivation × | Taels × |
|---|---|---|---|
| Bone Forging | 13 (12 before E5's own) | 0.17 (0.15) | 1.75 (1.78) |
| Qi Kindling | 20 (19) | 0.60 (0.60) | 0.76 (0.74) |
| Qi Unfurling | 11 (10) | 0.60 (0.60) | 0.86 (0.87) |
| Heart Tempering | 11 (10) | 0.89 (0.89) | 0.94 (0.96) |
| Cloud Stride, Spirit Awakening, Heaven Glimpse | 1, 2, 12 | 1.15, 1.24, 3.95 | (no taels) |
| Sage, Sage Sovereign, Will Manifest, Sphere Lord | 8, 5, 1, 2 | 17.6, 3.25, 5.30, 5.30 | (shown, not checked) |

These figures count every side quest, the hand-written lessons too. A Sage side quest pays 17.6 times an hour of play
for ten minutes, by design: Act II's share of the Sage stages' 315,000 need. The pacing still lands every realm within
±15%. Qi Kindling 1 moved from 4.8 h to 4.9, Heart Tempering 1 from 19.4 h to 19.8 and the act's end from 64.5 h to
65.0, against targets of 5, 20 and 65.

## Pins

Every derived value can be pinned in the spec, never in the JSON (audit 45 §6, rule 3):

- `target_room="..."` pins the room, and `target_room=None` leaves it out;
- `realm="..."` pins the realm, and `realm=None` leaves it out. `requires={...}` pins all of `requires`;
- `pay=40` pins the sum (in the band's currency), `pay=stones(50)` pins the currency too, and `pay=None` pays no
  money;
- `name="..."` pins the title, and a step's text is always its own when given;
- `row={key: value}` pins a key of the finished row. A key the row has keeps its place, and a new one goes at the end.
  `DROP` takes one out;
- `job(..., levels=(lo, hi))` pins a daily job's Levels.

## The daily board

`specs/dailies.py`: six templates (Hunt, Gather, Mine, Deliver, Craft, Spar), 19 jobs.

A job is a template step and the Levels it is posted at. When the spec doesn't give them, the Levels come from the
monster engine's foe, or from the node's rooms:
- a foe's band runs from one Level under its first to four over its last;
- a node runs from one Level under the first field band it grows in to twenty over;
- anything else may be posted at any Level of the board, up to 70.

Nine of the 19 jobs take their derived Levels; ten keep theirs pinned. The objective's text comes from the names, and
all 19 are what the hand table said. `QuestAuthority._fill_board` posts them and pays them at the Level they are posted
at, as before.

## Adding a quest

1. Write the spec in its module. A new side quest of the valley goes in `specs/valley_new.py`, a new module into
   `specs/__init__.py`'s `SECTIONS` (a new section also needs its `Q.extend(QE.rows("<section>"))` in `story.py`).
   Give it:
   - the giver (an NPC engine id), the step or steps, and the words: `offer`, `done`, and `progress` if it has some;
   - `after="<quest>"` if the story must reach something first (the giver isn't home before then, say);
   - `gives=[item(...), fx(...)]` for what it gives besides its pay.
2. Build, then look:
   ```
   python3 tools/data/build_data.py
   python3 tools/content/quests/engine.py --show <id>     # the room, the realm, the tier, the band and the pay it chose
   git diff data/                                          # only the new row (and a reward source in docs/wiki/items.md)
   ```
3. Pin what reads wrong in the spec: a room that isn't where the story means, a realm, a sum.
4. `python3 tools/content/quests/engine.py --check`, then `tools/run_tests.sh`.

## The checks

- **`engine.py --check`** (`quest_engine` in `tools/run_tests.sh` and `Test.ps1`):
  - two compiles write the same rows and the same board;
  - every spec resolves: its giver and hand-in are people, every foe, item, person and room it names exists, every
    item it gives exists, and a step that leads somewhere finds a room in the built data (or pins one);
  - the built data holds every quest as the engine writes it. Each one's pay is settled at its built tier, its keys
    are in order and the sections are in order. `story.py` adds only `qp`, `tier` and `cultivation`. Each one's
    cultivation is phase 1's at its tier. `mission_templates.json` is the engine's board;
  - each band holds one need and pays a known currency;
  - `tests.py`, 9 tests on a world of their own:
    - the row's layout;
    - the templates and the default texts (plurals);
    - every room rule (ties, gated spawns, quest drops, a giver who is the target);
    - the realm and `requires`;
    - the pay and the key order (`PAY`, every kind of pay pin, `settle`, `row` and `DROP`);
    - the bands against phase 1's numbers at every Level;
    - the board (key order, derived and pinned Levels);
    - the errors;
    - today's specs (E5's own quests carry no pins; the favours are their template's).
- **`build_data.py --check`**: `quests.json` and `mission_templates.json` are what `story.py` and `economy.py` write.
- **`story.validate`**: every quest's people, items, foes and rooms exist, and every giver is placed.
- **`balance_sim`**: the pacing, and the side quests' pay an hour above.
- **`topdown_side_quests`** (a new suite, 20 checks) plays Claws for the Grindstone on the grid with a top-down
  character:
  - Apprentice Tao doesn't offer it at Bone Forging 5, and does at 6;
  - its tracker leads to the Lower Pit, and the walk there goes by Stoneford Gate and the quarry road, every room on
    the grid;
  - Ironclaw Moles are fought there until five claws drop;
  - back on Artisan Row it is handed in: the claws are taken, and it pays the row's +310 cultivation and 90 taels,
    which are the band table's at its tier.

## The migration (the round trip)

The side and daily quests were re-expressed as specs, one section at a time, until the built data was byte for byte
what the hand rows wrote (`build_data.py`, then `git diff data/` empty). The prologue, the main story and the guided
lessons stay hand-written: they are beats, not templates.

| Modules | Section in `story.py` | Quests | Spec lines | Hand lines they replaced |
|---|---|---|---|---|
| `valley.py`, `companions.py` (the `favours()` template), `hidden_vale.py` | `side_quests()` | 21 + 12 + 3 | 79 + 49 + 12 | 117 |
| `expanse.py` | `act2_side_quests()` | 8 | 47 | 51 |
| `starsea.py` | `act2_starsea_side_quests()`, after its 3 guided lessons | 6 | 43 | 43 |
| `act3.py` | one in each of chapters 20, 21 and 22 | 3 | 36 | 27 |
| `dailies.py` | `economy.py` `missions()` | 6 templates, 19 jobs | 37 | 30 |

That is 53 side quests and the board. `story.py` went from 2,662 lines to 2,401 (281 lines removed, 20 added), and
`economy.py` lost 26 lines net (30 removed, 4 added).

The helpers (`o`, `item`, `fx`, the currencies and the row's layout) moved to the engine and `story.py` imports them.
`unlock_req` went: only the side quests used it.

What the specs pinned to come out the same:

| Value | Derived | Pinned |
|---|---|---|
| `target_room` | 35 (23 a room, 12 none: a delivery, a talk with the giver) | 22: 8 a room (the Reedless Shore and the Pirate Deck, which the derivation would not pick; six where no step leads anywhere: a giver's village, the hamlet, the Ancestor Hall, the hermit's cave, the chandlery, the Bastion), 14 none (the 12 companion favours, Copper for the Bellows, The Broken Kindling) |
| the realm | 44 (6 from a room's band: Nets and Shells, Beetle Shell Lacquer, Clear Skies and three of E5's own; 38 none: they follow another quest, or lead to no room with a band) | 12 a realm, 1 a whole `requires` (Dou's Kite Returns, whose realm comes before the quest it follows) |
| the pay | 15 the band's | 35 a sum, 7 no money |
| the name | 33 from the id | 24 (the companions' twelve titles, and the names with an apostrophe or a hyphen) |

The specs are about as long as the lines they replaced, as with the other engines. What they save is the next quest.
E5's four new quests take 26 lines, comments included, and none of them names a room, a realm or a sum.

29 quests of kind `side` stay in `guided_quests()`:
- the systems' lessons that the unlock rows offer (16);
- the weapon spirit's and the two spirits' quests;
- the nine legendary weapons' chains, written by a loop over `legends.py`'s chains;
- the Elder's last lesson.

The prologue's two errands stay too. These are `unlocks.json`'s guided quests and the story's beats, not side
quests. A lesson could become a template later (`use_system` from an unlock), but none is migrated here.

### Where the hand quests pay otherwise than their band

These are pinned in the specs, so nothing changed. Some may be balance bugs worth a later look; none is fixed here.
`engine.py --diffs` prints this table. Each band's sum in the table above is the middle value of its hand quests.

| Band (its pay) | Quests that pay otherwise |
|---|---|
| Bone Forging 1 (30 taels) | Tie Niu's three favours: 80 |
| Bone Forging 3 (40 taels) | Dou's Kite Returns 50; Dou Wants to Train, no money (a title) |
| Bone Forging (90 taels) | Copper for the Bellows 100 (and the old hammer), Auntie Rong's Soup 80 |
| Qi Kindling (120 taels) | Kai's Wager 150; Guo's Old Wound 80; Lan Yue's and Qiu Feng's six favours 80; Old Pan's three errands, no money (spirit stones, a flag) |
| Qi Unfurling (200 taels) | A Hall of Our Own 300, Walls of the Vale 400; Bai Ling's three favours 80; A Second Try, no money (a title) |
| Heart Tempering (200 taels) | Su Qing's Map 250, Old Scores 300, Grey Roofs 120, Cleansing the Well 150; Min's First Caravan, no money (spirit stones) |
| Cloud Stride (250 taels) | Wen Zhao's Challenge, no money (a title) |
| Heaven Glimpse (400 taels, +3,000) | A-Lan's Herd: 50 spirit stones and +1,200, an Act II quest at an Act I tier paying Act II's share |
| Sage (90 spirit stones) | Snow for the Cabinet 40, Clear Skies 70, Silk on the Wind 80, Glass Teeth 110, Stingers for the Hold 120, Blood Remembers 100 |
| Sage Sovereign (120 spirit stones) | The Deserters 160, Iron from a Comet 150, What the Bones Say 100, The Sound of Snow 100 |
| Sphere Lord (30 sage crystals) | The Leviathan's Maw 200 (a world boss) |

The companions' twelve favours all pay 80 taels and a bond, whatever their tier: that is their template's pin.

`--diffs` also lists the quests whose room lies far from their tier: more than four Levels over it (the kill gap's
full-credit band) or eight under. These are worth the same look:
- Grey Roofs pays Heart Tempering 1's +670 for the Grey Pools, Levels 7 to 12: the hamlet opens at the quest's own
  realm.
- Tie Niu's favours are pitched at Bone Forging 1, from the plain grade of the copper the first asks for. The third
  sends you to the Echo Cliffs, Levels 32 to 36, for +60.
- Lan Yue's oath (Levels 21 to 27) is pitched at Qi Kindling 1, and Qiu Feng's One Arrow (Levels 32 to 36) at Qi
  Kindling 2.
- Bai Ling's three favours are pitched at Qi Unfurling 1, but the jade sentinels live in the Forgotten Monastery,
  Levels 50 to 56.
- In Act II, four quests of the canyons and the desert are pitched three to ten Levels under their rooms. These are
  Silk on the Wind, Plumes for the Bellows, Glass Teeth and Stingers for the Hold, and their tiers come from the story
  quest they follow.
- So are Iron from a Comet, Clear Skies over the Peak and The Leviathan's Maw.

## The first new quests: four rooms that had none

Four converted Act I rooms had no side quest, and four people of the NPC engine had no quest:

| Quest | Giver | Step | Room (derived) | Opens (derived) | Pays (band) |
|---|---|---|---|---|---|
| Claws for the Grindstone | Apprentice Tao, Artisan Row | `fetch("mole_claw", 5)` | the Lower Pit (5–7) | Bone Forging 6 | +310, 90 taels |
| Pelted at the Fair | Rui, the Fairground | `clear("bamboo_monkey", 8)` | Whispering Bamboo (10–14) | Qi Kindling 3 | +530, 120 taels, and two Toad Oil Dumplings |
| Scales for the Lanterns | Vendor He, the Fairground | `fetch("jade_scale", 4)` | Bend Shore (19–23) | Qi Unfurling 3 | +470, 200 taels, and a Return Charm |
| The Weir at the Rapids | Fisher Gan, Greyreed Hamlet | `clear("rapids_lizard", 6)`, after Cleansing the Well | the Rapids Terraces (28–33) | with the hamlet's return (Heart Tempering 1) | +670, 200 taels, and a Hemp Net |

Fisher Gan is home only once the well runs clean (E3). His quest follows Cleansing the Well, so it opens when he does
and pays that quest's band. Each is one spec of five to seven lines. The data diff is their four rows, plus their
rewards as sources in `docs/wiki/items.md`.

**Engine size.** `spec.py` 212 lines, `bands.py` 87, `engine.py` 637, `tests.py` 204; the specs 353.
