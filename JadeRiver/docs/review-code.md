# Code review: architecture, duplication, dead code and bugs

Scope: `scripts/` (144 GDScript files, about 40,000 lines), `tools/data/*.py` (about 15,000 lines) and the suites in
`tests/`, at commit 6ef9c7a. Line numbers below are at that commit. Every dead-code entry was checked with a whole-tree
word search (scripts, tests, tools, scenes, project files); every bug has a concrete failing scenario, and the ones
fixed in this branch have a regression test in `tests/rules_tests.gd` (`fixes_suite`).

Baseline before any change (`tools/run_tests.sh`): room_lint 168 rooms / 0 failing; engine_tests 3735/3735;
data_validation 14318 checks / 22 failures (the known missing icons and brush and bell appearances); rules_tests 1488 / 0;
contract_tests 999 / 0; balance_sim 24 / 0; perf_tests 4 / 0; prologue_run 107 / 0; valley_run 1253 / 0;
`tools/dev/check_scripts.gd` 0 failures.

## 1. The architecture as it really is

### Layers

| Layer | Where | Size | Notes |
|---|---|---|---|
| Data | `data/*.json`, `data/rooms/`, `data/dialogue/`, `data/strings/en.json` | built by 24 modules in `tools/data/` | Loaded once by `ContentDB` (`scripts/core/content_db.gd`). 331 events in `data/event_contract.json`. |
| State | `scripts/simulation/state/` (9 classes), `actor_state.gd`, `room_runtime.gd` | ~1,000 lines | Plain RefCounted objects with `snapshot()/restore()`. Several carry small helpers (`InventoryState.count/find_uid/room_for`, `QuestState.is_done`, `RelationsState.hearts_of`). |
| Rules | `scripts/simulation/rules/` (11 files), `scripts/core/requirement_rules.gd`, `ai/enemy_brain.gd`, `ai/ally_brain.gd` | ~2,500 lines | Mostly pure. Exceptions in section 2.3. |
| Authorities | `scripts/simulation/authority/` (20 authorities + base + `GameAuthority` facade) | ~17,000 lines | The heart of the game. Five files are over 1,400 lines (combat 2466, crafting 2063, world 1872, pets 1677, progression 1616, posts 1418). |
| Presentation | `world.gd`, `player.gd`, `main.gd`, `hud.gd`, `scripts/presentation/`, `scripts/ui/` (46 pages + `page.gd` + `ui_kit.gd`), `scripts/shell/` | ~15,000 lines | Immediate-mode pages; `hud.gd` alone is 1,987 lines, of which 600 are one `match` over events. |

Autoloads: `ContentDB`, `GameEvents`, `Clock`, `Rng`, `Unlocks`, `Saves`, `Game`, `Audio`, `Notifier`, `Wardrobe`.
`Unlocks` (`scripts/core/unlock_service.gd`) is a de-facto authority: it is the only writer of
`CultivatorState.unlocked/offered/revealed` and emits `unlock_offered`, `hud_element_revealed` and `system_unlocked`.

### Intents, events and the tick

- `Game.submit(intent)` (`game_authority.gd:121`) routes by `type` to the one authority that listed it in `intents()`
  (duplicates are asserted at registration), rejects stale sequences and non-finite values, then runs `_after_pass()`:
  flush the event queue, re-evaluate unlocks if an unlock trigger fired, flush again, and save if a save trigger fired.
- `Game.apply_effects` (`game_authority.gd:138`) is the data-driven command table: 75 effect kinds, each dispatched to
  the owner's `apply_*` command. Quest rewards, dialogue choices, unlock grants, fates, fortune cards and item uses all
  go through it.
- `GameEvents` queues events raised during a pass and delivers them after it in emission order, authorities first by
  priority (combat 20, progression 30, inventory/crafting 40, enemies 40-45, pets 45-75, world 50-55, quest 60-65,
  account 70/88, achievements 80, relations 85-95, calendar 90), then the presentation through the `event` signal.
  Reactions may queue further events (depth-limited to 8).
- `Game.tick(delta)` (`game_authority.gd:266`): combat → field → progression → enemies → world → crafting, companions,
  pets, quest, economy, accounts, sect, training, achievements, mail, inventory → deliver events → unlocks → autosave.
  **`RelationsAuthority.tick` and `CalendarAuthority.tick` exist but are not in this list** (bug B1 below).
  `WorkshopAuthority` and `PostAuthority` have no tick (they settle from the clock on demand).
- The world scene (`world.gd:223`) calls `Game.tick` each physics frame; `player.gd` samples input and moves its
  `ActorState` through `LocalAuthority` (`scripts/simulation/local_authority.gd`), whose traversal events
  (`jumped`, `landed`, `fell_out`, ...) go out on the same bus.

### Who writes what

| State | Owner (writer) | Also written by |
|---|---|---|
| `ResourcePool` (hp, qi, soul, composure, hollowing, statuses, shield) | Combat | Enemy (`enemy_authority.gd:405,427`: the player's HP at the end of a spar), World (`world_authority.gd:394`: Soul for Spirit Sense), the world scene (`world.gd:775`: fall damage through Combat's command, but decided in presentation) |
| `ResourcePool.cooldowns` | shared cooldown table | Combat, Inventory (item groups), World (`sense`), Companions (`comp_heal`), Progression, Pets: a shared scratch table, keyed by owner prefix |
| `EnemyState` (pools, ai, statuses) | Enemy (spawn, AI, phases) and Combat (hits) | Pets/Companions (their allies), Relations (`apply_surrender` sets `ai.surrendered`) |
| `CultivatorState` | Progression | Unlocks (unlocked/offered/revealed), Achievements (titles), Field (`field_powers`), Account (creation, `meditating = false` on enter) |
| `InventoryState` | Inventory | Combat (`treasures[slot] = ""` when a treasure is spent, `combat_authority.gd:2163,2254`), and **every authority that mints an item instance** increments `next_uid` itself (World, Crafting, Economy, Account: 12 sites) |
| `QuestState` | Quest | Relations (`relations_authority.gd:725-727,745`: county jobs erase and create quest entries), World (`world_authority.gd:594`: `inspected_*` flags set without `flag_set`), Account (skip-Prologue start) |
| `GameCharacter.crafting` | Crafting | Posts (bench XP through `crafting.add_xp`) |
| `GameCharacter.posts`, `AccountState.storehouse/leaves/works` | Posts | — |
| `GameCharacter.rooms`, `tower`, `last_shrine`, `last_town`, `position` | World | Account (creation), Progression (tribulation reads) |
| `AccountState.currencies` | Economy | — (contribution is delegated to Training) |
| `AccountState.mail` | Mail | — |
| `AccountState.sect` | Sect | Account (Max Test character) |
| `AccountState.calendar` | Calendar | — |
| `RelationsState` | Relations | — |
| `HerbRules.origin_week` (a static on a rule) | Calendar | — |

## 2. Where the code breaks the five-layer rules

### 2.1 Presentation writing state

| Where | What | Proposed fix |
|---|---|---|
| `world.gd:769-775` | The world scene decides and applies fall damage (5% max HP, never in towns or the Prologue) through `Game.combat.apply_resource_change`, bypassing intents. | Combat reacts to `fell_out` (the event `LocalAuthority` already emits) and applies the cost itself. **Fixed.** |
| `ui/pages/posts_page.gd:190` | `_draw_bench` calls `Game.posts._bench_settle(ch)` every frame: drawing the page settles the Apprentice Bench and grants smithing XP. | A read-only `bench_view` that projects the stock without writing. Left (see section 7). |
| `ui/pages/inventory_page.gd:355` | Selecting a bag slot erases `inventory.new_items[id]` directly. | Needs a new `mark_seen` intent (a contract change), so left and listed. |
| `main.gd:146-481` | Debug arguments (`--relic=`, `--posts-demo`, `--give=` ...) write state and call private authority functions. | Acceptable as debug tools (S38); they only run where `Unlocks.debug_tools()` is true. |
| Pages calling private authority functions | `auction_page.gd:27` (`_au_cfg`), `your_sect_page.gd:144,174` (`_on_expedition`), `works_page.gd:65,67,90` (`_curve_of`), `hud.gd:1451,1460` (`_pet`) | Read-only, but they reach past the public surface. Left for the UI restyle. |

### 2.2 An authority writing another authority's state

| Where | What | Fixed |
|---|---|---|
| `relations_authority.gd:724-727,745` | County jobs erase quests from `quests.active/tracked/daily` and write new daily quest rows. | Yes: `QuestAuthority.apply_drop` and `apply_daily`. |
| `enemy_authority.gd:405,427` | The end of a spar sets the player's HP to full without `resource_changed`. | Yes: `CombatAuthority.end_spar` heals through its own pool command. |
| `world_authority.gd:394-395` | Spirit Sense spends Soul with `pools.set_value` and no `resource_changed`. | Yes: `combat.apply_resource_change`. |
| `world_authority.gd:593-594` | Inspecting an object sets `inspected_<id>` straight into `quests.flags` (no `flag_set`). | Yes: `quest.apply_flag`. |
| 12 sites (`account_authority.gd:86,256`, `world_authority.gd:848`, `crafting_authority.gd:1066,1679`, `economy_authority.gd:135`, `inventory_authority.gd:286,320,478,489,505`, `inventory_state.gd:154`) | Every instance minter increments `inventory.next_uid` itself. | Yes: `InventoryState.take_uid()`. |
| `combat_authority.gd:2163,2254` | Spending a single-use treasure clears `inventory.treasures[slot]`. | Left: small, and the treasure slot is Combat-facing. |
| `account_authority.gd:56-117,127-234` | Character creation and the Max Test character build every sub-state directly. | Accepted: creation has no other owner yet. |

### 2.3 Rules and queries with side effects

- `StatRules.rebuild(c)` (`stat_rules.gd:164`) writes `c.stats` and the pool maxima; it is a rule called by
  Combat, Account and `Game.boot`. It is the one sanctioned exception (Combat's `refresh_stats` wraps it).
- `HerbRules.origin_week` (`herb_rules.gd:17`) is mutable static state inside a rule, set by the Calendar's tick
  (and, because that tick never ran, never set in play: bug B1).
- Queries that write: `CombatAuthority.can_act` stops meditation (`combat_authority.gd:415`);
  `RelationsAuthority.county_jobs` (an intent, but also called as a query by tests) creates and accepts quests;
  `CraftingAuthority.settle_bed/bed_view/dew_state/commissions`, `PostAuthority.state/pouch`,
  `PetAuthority.ensure_fields/swarm_of`, `AccountAuthority.activity()` lazily create or settle their records when
  read. They are deterministic settlements, so reading twice gives the same answer, but a page that draws them writes
  the save. Listed; changing them would move settlement timing.

### 2.4 Player-facing literals outside `Tx.t`

`contract_tests` checks only the files in its `STRING_SCOPE`. The same rule run over every script finds:
- `content_db.gd:138`: `realm_label` builds `"%s · Lv %d"` in code; it is shown by the HUD, the character, characters,
  menu, techniques pages and the shell. **Fixed**: the format moved to `ui.realm_label` in `ui_strings.json`.
- Defaults that can reach the screen: `"Disciple"` (`game_character.gd:11,78-79`, `save_service.gd:141`),
  `"New Disciple"` and `"Jade"` (`wardrobe.gd:12,19,22`). They are fallbacks for an empty or damaged name; left.
- `combo_rig.gd:7-15` (step names) and `map_validator.gd` (errors) are developer-only.

## 3. Duplication

Verbatim clones are rare (a 4-line clone detector finds almost none); the duplication is of *logic*: the same rule
written again in another place, sometimes drifting. Each row names the single home it should have.

| # | Duplicated logic | Where | Single home | Done |
|---|---|---|---|---|
| D1 | Minting an item uid (`inst.uid = next_uid; next_uid += 1`) | 12 sites (2.2) | `InventoryState.take_uid()` | Yes |
| D2 | Finding an instance by uid | `inventory_authority.gd:191` (`_instance_by_uid`), `:744` (`_find_uid`), `crafting_authority.gd:1441` (`locate`); slot/index fallbacks at `crafting_authority.gd:1494-1498,1710-1715` and `inventory_authority.gd:183` | `InventoryState.locate(uid)` | Yes |
| D3 | First free bag slot | `inventory_authority.gd:484,773,797,983` | `bag.find(null)` | Yes |
| D4 | Meridian gates: the data has flags (`stats.json meridian_gates`) and `StatRules.gate_flag`, but the code tests the thresholds again | `combat_authority.gd:645,664` (agility 25), `:1448` (body 50), `:1472` (body 100), `player.gd:295` (agility 100) | `StatRules.gate_flag` | Yes |
| D5 | The dodge cooldown formula | `combat_authority.gd:644-646` and `:663-665` | one `_dodge_cooldown(c)` | Yes |
| D6 | "defeat, announce, count Killing Intent" | `combat_authority.gd:199-203`, `:1302-1306`, `:1309-1315` | `_defeat(e, attacker)` | Yes |
| D7 | Ending a spar | `enemy_authority.gd:399-407` and `:419-428` | `_finish_spar(e, winner)` | Yes |
| D8 | The "strongest Dao", three ways with different weights (tier×1e6, tier×1000) | `progression_authority.gd:838` (Dao Echo), `:1605-1614` (chess, insight sites), `field_authority.gd:111-118` (the Sphere) | `ProgressionRules.strongest_dao(c, filter)` | Yes (bug B9) |
| D9 | Length of an in-game day | `clock_service.gd:47-59` (twice), `herb_rules.gd:7-12`, `progression_authority.gd:1109` | `Clock.game_day_s()` / `Clock.game_day()` | Yes |
| D10 | Dotted config lookup | `content_db.gd:148-169` (`stat_const`, `movement`, `curve`) | one `_dotted(config, path, fallback)` | Yes |
| D11 | The hidden-portal flag `"seen_" + room + "_" + portal` | `world_authority.gd:48,315,404,1739` | `WorldAuthority.seen_flag()` | Yes |
| D12 | "May a character be switched out / withdraw here?" (town, sect, home, interior or safe) | `account_authority.gd:319`, `post_authority.gd:418` | `WorldRules.safe_room(def)` | Yes |
| D13 | Merging the post ledger into the welcome report | `account_authority.gd:296-301`, `:609-614` | `_with_ledger()` | Yes |
| D14 | The position of a route step (dock or portal) | `world_authority.gd:1764-1773` (`auto_path_step`), `:1800-1816` (`guide_step`) | `_step_point()` | Yes |
| D15 | Removing a quest from active/tracked/daily | `quest_authority.gd:60-61,585-587,601-602,619-621`, `relations_authority.gd:725-727` | `QuestAuthority.apply_drop` | Yes |
| D16 | A weighted draw written out by hand | `relations_authority.gd:628-636` | `Rng.weighted(rng, cards, "w")` (same single `randf`) | Yes |
| D17 | "The tier at this value / the next tier" | `relations_authority.gd:158-168` (Fame), `:692-701` (county favour) | `_tier_at`, `_tier_after` | Yes |
| D18 | Node yield (roll, tool power, gatherer, herb trait) | `crafting_authority.gd:174-180` and `:201-207` | `_node_yield()` | Yes |
| D19 | Step grade from a score | `crafting_authority.gd:672` inline and `_step_grade` at `:840` | `_step_grade` | Yes |
| D20 | Pass-through `RelationsAuthority.apply_insight_best` | `relations_authority.gd:667` → progression | dispatch `insight_best` straight to Progression | Yes |
| D21 | The slot → wardrobe category map | `inventory_authority.gd:625` (`WARDROBE_CATEGORY`) and `:814` (`outfit_for` map) | the const | Yes |
| D22 | Expedition-busy loops | `sect_authority.gd:158-160` and `_on_expedition` `:315-319`; `mine_holder_rival` `:504` repeats `mine_holder` `:293` | reuse | Yes |
| D23 | Duration text | `calendar_page.gd:73`, `your_sect_page.gd:148` (identical), `relations_page.gd:105` (no days), `posts_page.gd:319` ≈ `post_authority.gd:824`, `works_page.gd:266`, `welcome_page.gd:62` | `UiKit.span()` / `UiKit.hours()` | Yes (UI commit) |
| D24 | Two-column page layout (`left`, then `right := Rect2(left.end.x + gap, ...)`) | ~20 pages (`calendar`, `county`, `chess`, `tower`, `relations`, `codex`, `workshop`, `posts`, `gift`, `pets`, `quest`, `mail`, `beast_arena`, `cultivation`, `character`, ...) | `Page.columns(left_w, gap)` | Left for the UI restyle (it would touch every page the restyle rewrites) |
| D25 | Requirement constructors (`realm`, `flag`, `noflag`, `qdone`, `qactive`, `unlocked`, `sect`, `all_of`, `any_of`) | `tools/data/economy.py:15-28`, `story.py:15-48`, `world.py:37-66` | `tools/data/common.py` | Yes |
| D26 | Catalogue helpers (`_w`, `authored`, `surf`, `obj`, `drop_decor`, `drop_surfaces`) | `catalogue.py:12-36`, `catalogue_rows_dungeons.py:13-58`, `catalogue_rows_fields.py:20-36`, `catalogue_rows_towns.py:7-17` | `catalogue.py` | Yes |
| D27 | The S43 reach table and the later-art rises, twice with separate numbers | `room_lint.py:36-55` (`BANDS`, `ART_RISE`) and `verticality.py:22-29` (`band`, `LATER_ART`) | `room_lint.BANDS/ART_RISE` | Yes |
| D28 | Refine checks (cracked furnace, batch, fire, substitute) | `crafting_authority.gd:752-764` (`refine_block`) and `:977-988` (`craft`) | — | Left: `craft` returns distinct reason codes the tests assert (`batch`, `cracked`) |
| D29 | Enhance / reroll cost checks | `enhance_check` `:1471` vs `enhance` `:1503-1508`; `reroll_check` `:1481` vs `reroll` `:1599-1601` | — | Left: same, distinct reason codes |

## 4. Dead code (each verified by a whole-tree word search: only the definition matches)

Functions: `Clock.uptime_s` (`clock_service.gd:18`), `Clock.day_fraction` (`:56`), `HerbRules.game_day` (`herb_rules.gd:11`),
`ContentDB.validate` (`content_db.gd:193`, loads a `data_validator.gd` that does not exist), `GameCharacter.has_qi_pool`
(`game_character.gd:57`), `InventoryState.quick_capacity` (`inventory_state.gd:38`), `StatBlock.set_bases` and `has_source`
(`stat_block.gd:24,55`), `WorldCatalog.valid_theme` (`world_catalog.gd:11`), `ZoneGeometry.is_mover` (`zone_geometry.gd:364`),
`UiKit.draw_frame` (`ui_kit.gd:328`), `Wardrobe.save_slot` (`wardrobe.gd:47`), `player.land_from_flight` (`player.gd:160`),
`CreatureSprite.frame_count` (`creature_sprite.gd:34`), `CombatAuthority.arrays_inside` (`combat_authority.gd:1826`),
`CompanionAuthority.is_companion` (`companion_authority.gd:30`: ally kills are credited to the owner's id, so no killer id
ever starts with `comp:`; its one use in `quest_authority.gd:393` is always false).

Constants: `Rng.CHARACTER_STREAMS`, `ACCOUNT_STREAMS` (`rng_service.gd:6-7`), `MapGenerator.LANE` (`map_generator.gd:10`),
`Page.SAFE` (`page.gd:12`).

Variables and signals: `hud.gd:78` `boss_uid`, `:80` `hint_timer`; `progression_authority.gd:14` `last_level`;
`world_authority.gd:12` `pending_transfer`; `enemy_state.gd:31` `hurt_time`; `room_runtime.gd:16` `npcs_hidden`;
`world.gd:38` `save_error`, `:41` `transitions_enabled`, `:52` signal `region_exit`.

Stale state: `QuestState.last_daily_day` (saved and restored, never read; the account keeps the real one) and
`QuestState.seen_dialogue` (never written, read only for `.size()`, always 0).

Unreachable branches: the `on_accept` debt trigger (`relations_authority.gd:104`; no debt carries `on_accept`);
the herb-yield trait bonus in `complete_node` (`crafting_authority.gd:179-180`; herb patches always go to `_harvest`);
the `not attacker.begins_with("ally")` test in `_damage_enemy` (`combat_authority.gd:1275`; the attacker is always an
owner id, see bug B8); `var ch` in `progression_authority.gd:972`; the trailing `pass` in `crafting_authority.gd:2063`.

## 5. Bugs

| # | Bug | Failing scenario (inputs → wrong result) | Fix | Test |
|---|---|---|---|---|
| B1 | `Game.tick` never calls `RelationsAuthority.tick` or `CalendarAuthority.tick`. | Play for three hours: the Fortune meter stays at 0, so no fortune encounter ever happens outside tests. Kill the yielded lieutenant: Kuai Shan's threat (due in 15 min) waits for the next quest event. The calendar never announces world events, never pays the Herb Terraces trial, never sets `HerbRules.origin_week` (every account's seasons start from week 0, not its creation week) and never re-applies a changing sky. | Tick both, after the others. | `fixes_suite`: ticks fill the meter; the calendar records the season and sets `origin_week`. |
| B2 | Buyback drops a stack's quality, Halo, marks, prep and seal, and loses what does not fit. | Sell 3 Superior Healing Pills, buy them back: 3 Common pills. With room for 1 of 3: 1 comes back, 2 vanish, the full price is paid. | Pass the stack as the new stack's fields; take what fits and charge for it; the rest stays in the buyback list. | `fixes_suite` |
| B3 | An instance moved between characters keeps the uid of the character it came from; splitting a locked stack copies its uid. | c1 deposits a sword (uid 3) into the shared chest; c2, whose robe is uid 3 and locked, withdraws it: both show locked, and forge actions by uid act on the robe. Split a locked pill stack: both halves are locked by one uid; unlocking one unlocks both. | `apply_add_instance` gives an instance a fresh uid when its uid is taken in the new bag and keeps `next_uid` past any kept uid; a split part carries no uid. | `fixes_suite` |
| B4 | Standing by loot with a full bag emits `bag_full` every physics tick. | Full bag, a herb stack at your feet: 60 `bag_full` events a second and the HUD log shows five "Your gourd is full" lines until you walk off. | Auto-pickup skips a stack it already could not take while the bag still has no room for it. | `fixes_suite` |
| B5 | Guild commissions take locked items. | Lock your forged robe; deliver a Forge Guild order for that robe: the locked robe is taken. | Locked items are neither counted nor taken. | `fixes_suite` |
| B6 | Guild commission boards turn over at 00:00 UTC, not at the daily reset. | Time zone UTC-8: the board changes at 16:00 local, unlike every other daily in the game (04:00 local). | `commission_day()` uses `Clock.reset_day`. | `fixes_suite` |
| B7 | A Wind Step Talisman's free dodge is spent by a dodge that then fails. | Dodge on cooldown, a free-dodge charge held, standing in shallow water: the dodge fails `in_water` and the charge is gone. | The charge is spent only when the dodge happens. | `fixes_suite` |
| B8 | Pet and companion blows interrupt a normal monster's wind-up, against the rule's own exclusion. | A spirit animal's hit on a winding-up boarlet staggers it; `not attacker.begins_with("ally")` can never be false because ally hits pass the owner's id. | Test the attack's `ally:` source. | `fixes_suite` |
| B9 | "The Dao you know best" differs between systems. | Sword Dao tier 6 (12,500 insight) and a Fist Dao held at its valley cap, tier 5, with 30,000 insight: the Sphere and Dao Echo choose Sword; the hermit's chess problem and the insight sites choose Fist. | One `ProgressionRules.strongest_dao` (tier first, then insight). | `fixes_suite` |

Also reported, not changed: an interrupted breakthrough channel (`progression_authority.gd:971-974`) consumes its support
pills without counting a failed supported attempt (the tribulation path counts it); `purity_changed` carries `value`
from `apply_purity` and `grade` from `apply_purity_grade` (no reactor reads either key, and the payload is contract);
`SectAuthority.upgrade` dereferences a null character when called without one (only reachable from a malformed
intent); `buff_allies` (`enemy_authority.gd:265-269`) multiplies allies' attack permanently on every cast.

## 6. Ranked plan (impact against risk)

1. B1 ticks (high impact: three systems silent in play; low risk, one line, watched by valley_run).
2. B2-B9 bugs, each with its regression test (medium impact, low risk).
3. Layer fixes: quest writes, spar heal, Spirit Sense Soul, inspect flag, fall damage through Combat (low risk).
4. Dead code (no risk).
5. Inventory uid minting and lookup (D1-D3): the largest single dedupe, touches six authorities.
6. Combat and progression helpers (D4-D6, D8), enemy spar (D7), clock and config lookups (D9, D10).
7. World, account, quest, relations, crafting, sect helpers (D11-D22).
8. `tools/data`: requirement constructors, catalogue helpers, reach table (D25-D27), `data/` byte-identical.
9. Last, in their own commits after merging the build branch: pages (D23), `realm_label` text.

## 7. Found but left

- D24 page columns, D28/D29 refine and forge checks, the posts page bench settle and the inventory page's `new_items`:
  each would change the intent contract, tested reason codes, or the pages the UI restyle is rewriting.
- The lazy settle-on-read queries in 2.3: behaviour-preserving changes would move settlement timing.
- `hud.gd:_on_event` (600 lines, one `match`) could be a table of event → toast/log rows; it belongs to the restyle.
