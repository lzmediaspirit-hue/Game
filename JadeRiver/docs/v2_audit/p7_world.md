# Audit p7: S49 Karma, bonds and the living world (v2 spec vs build)

Build audited: `/home/user/Game/JadeRiver` at commit `796f089` ("G1 follow-up"). CHANGELOG top is **1.1 (Act II)**, so every spec item tagged v0.8, v0.9, v1.0 or v1.1 is due in this build. v2.0 items are not due. The audit was read-only: no godot runs, no tests, no build scripts.

Main findings:
- **No Relations authority and no Calendar authority exist.** `scripts/simulation/authority/` has account, achievement, combat, companion, crafting, economy, enemy, game, inventory, mail, pet, progression, quest, sect, training_sect, workshop and world authorities. Nothing else.
- **The G1 karma ledger lives in Progression.** `CultivatorState` holds `merit`, `sin`, `debts{}` and `merit_used{}` (cultivator_state.gd:46-49). ProgressionAuthority applies them (progression_authority.gd:717-740).
- **The G1 event names differ from the spec**, and the G1 events are not in `data/event_contract.json`.
- **None of the Part 8 files exist:** karma, bonds, factions, calendar, fortune_deck, rankings, tower, activity and guilds (.json). Karma numbers are hard-coded in `tools/data/story.py`, `tools/data/stats.py` and `tools/data/economy.py`.

Status key:
- **Present**: exists and matches.
- **Differs**: exists with a different name, number or behaviour.
- **Partial**: part of it exists.
- **Missing**: nothing like it.

---

## 1. S49 "Owns": state

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| New Relations authority (per character) | Missing | No `relations_authority.gd`. Karma is handled in `progression_authority.gd:716-740` | Add RelationsAuthority. Move the karma ledger into it and have Progression query it for risk steps and heart demon |
| `karma {merit, sin, debts[]}` | Differs | `cultivator_state.gd:46-49`: flat `merit:int`, `sin:int`, `debts: Dictionary` (id → {due_utc, mail, attachments, paid}), plus an extra `merit_used{}`. The comment at line 48 says `{text, due_utc, kind, paid}`, which does not match what `apply_karma_debt` writes (progression_authority.gd:730) | Re-home as `relations.karma {merit, sin, debts[]}` with a save migration. Keep `merit_used`. Fix the stale comment |
| `alignment` (−100 demonic … +100 righteous) | Missing | No alignment state. The only path state is the Alliance/Independent flags (story.py `envoy_lanshi` tree) | Add `alignment:int` clamped ±100 |
| `fame` | Missing | No fame field. Only `training_sect.reputation` (training_sect_authority.gd:41-47) and sect prestige exist | Add `fame:int` and a tier table |
| `npc_affinity {npc: {hearts, gifts_today}}` | Missing | Nothing. `companions.bond{}` (game_character.gd:26) is displayed (companions_page.gd:44) but never written | Add `npc_affinity`. Either retire `companions.bond` or fold it into affinity |
| `bonds {dao_companion, master, sworn[]}` | Missing | None | Add |
| `grudges {faction: value}` | Missing | None. Enemies have no `faction` field (enemies.json keys) | Add. Tag named NPCs and enemies with a faction |
| `bounties[]` | Missing | None | Add |
| `mortal_missions` | Missing | None | Add (v1.1) |
| `fortune_meter` | Missing | None. `fortune` is only an attribute used for drops and crits (stat_rules.gd:120, 208, 225) | Add a meter that refills 1 per 3 h |
| New Calendar authority (account level): seed, schedule, season, weather per region, NPC ranking table, active world events, treasure births | Missing | None. `AccountState` has `rng_seed` and `resets` but no calendar, season or creation date (account_state.gd:8-34). The account RNG stream `("account","sect")` is used only for sect raids (sect_authority.gd:229) | Add CalendarAuthority with an `("account","calendar")` stream. Add `account.created_utc` for seasons |
| World: tower floors cleared | Missing | No tower state in `world_authority.gd` or `game_character.gd` | Add `tower {cleared: [], swept_day}` |
| Account: daily activity points | Missing | `account.resets` holds only `last_daily_day` and `last_weekly` (account_state.gd:30) | Add `activity {points, day, claimed[]}` |

## 2. S49 Intents

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `give_gift {npc, item}` | Missing | Not in any `intents()` list | Add to Relations |
| `offer_bond {kind, npc}` | Missing | None | Add |
| `pay_grudge {faction, method}` | Missing | None | Add |
| `take_bounty {id}` | Missing | None | Add |
| `claim_activity_chest {tier}` | Missing | None | Add to Account |
| `join_world_event {id}` | Missing | None | Add to Calendar |
| `sweep_floor {floor}` | Missing | None | Add to World |
| `set_auto_hunt {on}` | Missing | Only `set_idle_task` exists (offline) (account_authority.gd:151) | Add a live toggle, refused outside idle-eligible rooms |
| `auto_path {target}` | Missing | None | Add (Movement or World) |
| `challenge_rank {npc}` | Missing | None | Add (v1.1) |

## 3. S49 Emits

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `merit_changed`, `sin_changed` | Differs | Both are covered by one `karma_changed {merit, sin, delta_merit, delta_sin, reason}` (progression_authority.gd:724). The HUD listens for it (hud.gd:494) | Split into `merit_changed` and `sin_changed`, emitted by Relations |
| `debt_recorded` | Differs | Emitted as `karma_debt_recorded` (progression_authority.gd:731) | Rename |
| `debt_called` | Differs | Emitted as `karma_debt_repaid` (progression_authority.gd:739), and only when a timed mail fires | Rename. Also emit it from quest callbacks |
| `alignment_changed`, `affinity_changed`, `bond_formed`, `grudge_changed`, `hunter_dispatched`, `fame_changed` | Missing | Nothing emits them. The pet `bond_changed` (pet_authority.gd:103) is a different thing | Add |
| `world_event_scheduled`, `world_event_started`, `world_event_ended`, `season_changed`, `weather_changed`, `ranking_changed`, `fortune_encounter`, `heavenly_phenomenon` | Missing | No emitter. The closest are `daily_reset` and `weekly_reset` (account_authority.gd:322-333) and `room_event_started`, which is per-room | Add to Calendar |
| Event contract registers the Relations events | Missing | `data/event_contract.json` (121 events, built by tools/data/contract.py) has none of `karma_changed`, `karma_debt_*` or `heart_demon_changed`. So contract_tests do not police G1's events | Add the new Relations and Calendar events to contract.py |

## 4. S49 system rules

### 4.1 Karma ledger (State v0.9; callbacks v1.0)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Two counters (merit and sin) | Present | `cultivator_state.gd:46-47`. `apply_karma` clamps both at ≥0 (progression_authority.gd:717-724) | Move to Relations (§1) |
| Named debts in the **S19 flag system** | Differs | Debts are a separate dictionary on the cultivator (`cu.debts`), not quest flags. The choices do also set flags (`gu_freed`, `gu_left`; story.py:1648-1655) | Store each debt as an S19 flag (for example `debt:<id>`) so quests and dialogue can test it with `flag_set` |
| Merit sources: cleansing Hollowed villages, sparing foes, healing | Partial | Village and well cleansing give merit, at other values (see §8). Sparing: no spare choice exists. Healing: only the one-off `the_infirmary` +10; `treat_patient` gives no merit (workshop_authority.gd:143-164) | See §8 |
| Sin sources: black-market trade, killing surrendering NPCs, high-realm power in mortal towns | Partial | Only black-market trade, done differently (Broker Mu, +2 per item; economy_authority.gd:124-126). No surrender kill and no mortal-town rule | See §8 |
| "Each 100 merit gives −1 risk step once per major realm" | Differs | `merit_step` returns at most **1** when merit ≥ 100 (progression_rules.gd:149-151). 300 merit still gives −1. Merit is never spent. The great realm is marked used when the attempt **starts** (progression_authority.gd:416), so a failed attempt uses up the ease | If "each 100" means `floor(merit/100)` steps, change `merit_step`. Decide whether a failed attempt consumes it, and write that into the spec |
| Sin raises tribulation strength (S48) | Missing | No tribulation exists (no `tribulation` in scripts) | Add when the S48 tribulation lands |
| Sin raises heart demon | Present | `apply_heart_demon(sin × 0.2)` (progression_authority.gd:723; stats.py:114 `per_sin: 0.2`). Tested at rules_tests.gd:797-798 | The rate is not stated in this packet; check it against S48 |
| Debts come back in later **quests** (the saved NPC repays; a victim's relative hunts you) | Partial | Callbacks are timed **mails** only (`_settle_debts`, progression_authority.gd:733-740; `due_h` 48/72, story.py:1650-1656). "Hunts you" is only a threatening letter (`gu_remembers`, story.py:1727). No hunter spawns and no quest callback | Let debts start quests, set flags or spawn hunters (a `debt_called` → Quest/Enemies reaction) |

### 4.2 Other S49 rows

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Righteous–demonic alignment gates masters, shops and methods (Blood path, demonic black market) and sets faction hostility; never gates core realm progress [v1.1] | Missing | None. The black market is gated by `flag_set path_independent`, a political choice, not alignment (economy.py:140-141) | Add alignment. Gate the back-room market and Blood path on it. Add a `realm_at_least` safety test |
| NPC affinity 0–5 hearts, favourite gifts in npcs.json, one gift per NPC per day; hearts unlock teachings, duels, discounts, bond offers [v1.0] | Missing | npcs.json keys have no gifts or hearts. Duels exist ungated (`spar:` services). Discounts exist only by flag (`ironroot_clan` discount, economy.py) | Add `gifts` and `hearts` to npcs.json, a `give_gift` intent, and `affinity_at_least` requirement kinds |
| Dao Companion: one per character, from a companion at 5 hearts; joint breakthrough-support slot; +10% shared insight; SFW resonance meditation [NPC v1.0] | Partial | The 4 companions exist (companions.json). "Paired cultivation" gives +15% while meditating beside any active companion from Sage 1 (companion_authority.gd:90-97; unlock story.py:507). That is an SFW resonance analogue, but not a bond: no heart gate, no uniqueness, no support slot, no insight share | Add the bond. Re-point paired cultivation to the Dao Companion, or keep both |
| Master inheritance: the mentor's ascension or death passes a legacy art | Partial | Mentors exist (`MENTORS = ["elder_hu","elder_sung"]`, story.py:60). `the_mentors_gift` (SA5) teaches `lotus_heart_breathing` and gives the talisman (story.py:962-968), but it is a trial, not an inheritance beat | Add the end-of-Act-I "Elder's Last Lesson" inheritance (§10) |
| Sworn siblings: up to 3 companions share a title and a small party buff | Missing | None. Only 2 companions can be active (companion_authority.gd:22), so a buff for 3 sworn siblings could never have all 3 present | Add. Make the buff apply per sworn sibling in the party, or raise the active cap |
| Players take over these roles [v2.0] | n/a (not due) | — | — |
| Grudge ledger per faction; named-NPC kills raise it; thresholds spawn hunter elites in field rooms; paid off by blood money, duel or quest; town board of named-target bounties [v1.0] | Missing | None. The Notice board page exists (notice_page.gd) but lists missions and requests only. Elite spawning exists (`elite_spawned`, enemy_authority.gd:149) and could host hunters | Add factions.json, a grudge ledger, hunter spawns and a bounty board tab |
| Personal Fame, separate from reputation, tiers Unknown → Noted → Rising → Renowned → Legendary; unlocks greetings, NPC challenges, "Young Master" events; public defeats cost fame [v1.1] | Missing | None (no tier names in titles.json or achievements.json) | Add |
| Seeded world-event scheduler on the account calendar stream; public cycle with realm caps for repeat runs [v1.0] | Missing | Only sect raids (every 2–3 days, sect_authority.gd:200-229), field-boss respawn timers (enemy_authority.gd:292-295) and daily/weekly resets | Add the Calendar authority and calendar.json |
| Story entries, first visits and quest-bound vaults are never behind the cycle or cap | Present (by default) | No cycle exists, so all of it is always open: the Drowned Shrine opens at QU3 (world.py:1179), the vault at SA3 (world.py:1213), the Waterfall Cave journal (world.py:1248) | Keep this true once caps are added (test it) |
| Calendar page drives S37 notifications | Missing | No Calendar page. The `Notifier` autoload exists (scripts/shell/notifier.gd, project.godot:16) but **nothing calls `Notifier.schedule`** | Add the Calendar page and schedule notifications from `world_event_scheduled` |
| Fortune encounters: data deck, triggered on room entry, gathering or void-fall recovery; weighted by Fortune and karma; meter paces them (≤1 per 3 h) [v1.0] | Missing | No deck, no meter, no `fell_out` event (no void-fall recovery event in scripts) | Add fortune_deck.json, the meter and trigger hooks |
| Heavenly phenomena: visible cloud or lightning on major breakthroughs; NPC congratulations or a jealous challenger [v1.0] | Partial | Every successful breakthrough shows a spiral, the realm text and a 0.2 s shake (world.gd:356-360). No cloud or lightning, and no difference for major breakthroughs. NPC barks happen only for `pill_cloud` (world.gd:397-409), not breakthroughs. No challenger | Emit `heavenly_phenomenon` on major success. Add a cloud or lightning FX, NPC barks and an optional challenger spawn |
| Rankings: seeded "Heaven Ranking" NPCs advance on a schedule; player enters by CP and tournament results [v1.1] | Missing | None. Hooks exist: the `tournament_top8` flag (story.py:855), the finals (story.py:860) and `StatRules.combat_power` | Add rankings.json, a ranking table in Calendar, and a Ranking tab |
| Profession associations: Alchemist [v0.8], Artifact/forge [v1.0], Formation [v1.1] guilds with exams, commissions, exam-gated recipes | Partial | Only XP ranks: apprentice→grandmaster (stats.py:174), the `profession_rank` requirement, Alchemist NPCs. No guilds.json, exams or commissions | Add guilds.json (shared with S44) |
| Territory and spirit mines [v1.1] | Missing | Only sect expeditions (expeditions.json) and sect raid defence (defence.json) | Add |
| Mortal kingdom: county magistrate, missions, mortal-currency sink, non-interference sin [v1.1] | Missing | None (no magistrate NPC) | Add |
| Weather: rain, storm and fog tags per region from the calendar; Thunder +10% in storms; fishing and gathering modifiers; never gating [v1.1] | Partial | Only fixed per-room hazards (`fog`, `lightning`, `wind_gust` in hazards.json; e.g. sr_windswept_ridge `wind_gust`). They are not calendar-driven and have no element or fishing modifiers | Add a weather table in calendar.json, per-region tags and modifiers |
| Lifespan as flavour: display-only "max years" per realm in realms.json; named NPCs age; mentor's death as inheritance beat; longevity treasures as quest and auction goods; no death clock [v1.0] | Missing | realms.json has no years or lifespan field. No longevity items. No death clock (good) | Add `max_years` to realms.py, a display, and longevity items |
| Quest auto-path over the room graph (walks, climbs, uses portals with known arts; stops at danger) [v0.8] | Missing | Data is ready: 100 quests have `target_room`, and the tracker returns it (quest_authority.gd:489). The HUD tracker only draws text (hud.gd:747-765). No path code | Add the auto-path intent, a button and a room-graph solver that respects `secret_art` gates |
| Trial Tower ladder with sweep [v1.0] | Missing | None (see §15) | Add tower.json and floors |
| Daily activity points filling 4 chest tiers [v1.0] | Missing | None (see §15) | Add activity.json |
| Auto-hunt toggle only in idle-eligible rooms (S23 Hunt rule), off in bosses, trials and tribulations [v1.0] | Missing / Differs | No live auto-hunt. The offline idle "hunt" is **not restricted by room**: rooms carry an `idle` list (e.g. `sf_gate: []`, `rm_marsh_edge: ["hunt","gather"]`, written by world.py:167, 485, 562), but `set_idle_task` never reads it (account_authority.gd:151-162). `collect_idle` uses `max(1, recommended_cp)`, so a town or boss room still pays kills (account_authority.gd:185-196) | Enforce `room.idle` in `set_idle_task`. Add the `set_auto_hunt` toggle with the same check |
| Leisure arts: guqin rhythm, chess puzzles, teahouse regional timed buffs [v1.1] | Partial | The Stoneford Tea House sells food with timed buffs (economy.py:42-43, `stoneford_tea`). No guqin or chess | Add the mini-games. Make the teahouse regional |

## 5. S49 Data

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| karma.json (deeds → merit or sin) | Missing | No file. Deeds are hard-coded: `KARMA_QUESTS` (story.py:529-536), dialogue effects (story.py:1588-1670), `karma.black_market_sin` (stats.py:117) | Generate karma.json and read deed values from it |
| bonds.json | Missing | — | Add |
| factions.json (grudge thresholds, hunters) | Missing | — | Add |
| calendar.json (event rotation, secret-realm caps, seasons, weather tables) | Missing | — | Add |
| fortune_deck.json | Missing | — | Add |
| rankings.json (seeded NPCs) | Missing | — | Add |
| tower.json | Missing | — | Add |
| activity.json | Missing | — | Add |
| guilds.json (shared with S44) | Missing | — | Add |
| npcs.json gets gifts and hearts | Missing | npcs.json entry keys: barks, companion, id, lines, name, on_talk, outfit, scale, sect, service_labels, service_unlocks, services, tint, title, tree | Add `gifts[]` and `hearts_max` (story.py `npc()`) |
| Generator home | Partial | `tools/data/build_data.py` MODULES has no relations or calendar module | Add `relations.py` and `calendar.py`, or extend story.py and economy.py |

## 6. S49 UI

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Relations page (Karma, Bonds, Grudges, Fame tabs) under Character | Differs / Partial | Karma is shown on **Cultivation → Heart** (cultivation_page.gd:127-141): merit, sin, merit-ready line and the debt list. Character tabs are overview, stats, aptitude, titles, attunement (character_page.gd:14). No Bonds, Grudges or Fame UI | Add a Relations page under Character. Move the Karma block there, or mirror it and link from the Heart tab |
| Calendar page under World | Missing | Menu entries: menu_page.gd:5-24 | Add |
| Heaven Ranking tab on the World map | Missing | Map tabs are one per zone (map_page.gd:20-27) | Add |
| Activity chest bar on the Mission page | Missing | No "Mission page". Missions show on the Notice board (notice_page.gd) and in the Quests "daily" tab (quest_page.gd:8) | Pick the host page. Add the bar |
| Auto-path button on the quest tracker | Missing | hud.gd:747-765 draws text only. A tap opens the Quests page (hud.gd:218) | Add |
| Auto-hunt toggle on the HUD (small, only where allowed) | Missing | None | Add |

## 7. S49 Tests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Merit risk reduction once per realm | Present | rules_tests.gd:789-795 | Extend it if "each 100" becomes multi-step |
| Debts fire their callbacks | Partial | rules_tests.gd:805-810 covers the mail callback only | Add quest and hunter callback cases |
| Alignment never blocks a realm_at_least requirement | Missing | — | Add |
| Gifts once per day | Missing | — | Add |
| Bond limits | Missing | — | Add |
| Grudge thresholds spawn hunters | Missing | — | Add |
| Calendar identical for the same seed across devices | Missing | — | Add |
| Secret-realm caps are enforced | Missing | — | Add |
| Fortune meter pacing | Missing | — | Add |
| Auto-hunt is refused outside eligible rooms | Missing | Today the offline hunt is accepted anywhere (§4.2) | Add with the fix |
| Auto-path reaches every quest target using only known arts | Missing | — | Add (a data_validation sweep over `target_room`) |

---

## 8. Part 8: deeds (karma.json)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Cleanse a Hollowed village or well: **+30 merit** | Differs | `cleansing_the_well` gives **+15** and `grey_roofs` (clear the Hollowed from the Grey Pools) gives **+10** (story.py:529-530; quests.json) | Set each to +30 through karma.json |
| Spare a fleeing named foe (dialogue choice): +10 | Missing | No spare or kill choices. The only foe that flees is `elder_gu` (`flees_after_s: 60`, a story boss) | Add spare choices, e.g. for the Mudwater lieutenant (§9) |
| Heal an NPC patient (Healing craft): +2 | Missing | `treat_patient` pays contribution, insight and XP but no merit (workshop_authority.gd:143-164). There are 5 patients a day (professions.json `patients_per_day`) | Call `apply_karma(+2)` in `treat_patient` |
| Finish Beast Tide defence: +10 | Missing | No Beast Tide. The sect-raid defence win pays prestige and taels only (defence.json `prestige_win` 40, `taels_win` 200) | Add with the Beast Tide (§11) |
| Buy from the black-market peddler (Caravan Road, night): +5 sin | Differs | The build's black market is **Broker Mu's Back Room** (`free_market`, economy.py:139-144). It is at the Wayfarers' Inn in the Azure Expanse (Act II, world.py:1461-1471), gated by `path_independent`, and gives **+2 sin per item** (stats.py:117; economy_authority.gd:124-126; test rules_tests.gd:804). No valley or Caravan Road night peddler. A `time_of_day` requirement exists (requirement_rules.gd:209) | Add a night-only valley peddler on `cr_caravan_road` at +5 per purchase. Decide whether Broker Mu stays a second black market |
| Kill a surrendering bandit (dialogue choice): +15 sin | Missing | No surrender dialogue | Add |
| Use Presence or techniques on mortals in Lotus Ferry: +5 sin (v1.1) | Missing | No rule | Add |
| (Build extras not in spec) | Differs (extra) | Hollow Night rescues +10 each (Dou, Granny, Ma; story.py:1588-1594); tomb resealed +20 (1637); Gu freed +15, Gu left +10 sin (1649-1655); ledger burned +20, ledger returned +10 sin (1666-1670); 10 helping quests +5…+15 (`KARMA_QUESTS`) | Fold them into karma.json as extra deeds, or reconcile the spec with them |

## 9. Part 8: named debts (valley)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Little Dou's rescue → in Act I ch. 6 Little Dou brings a Heaven-grade herb | Missing | The rescue gives +10 merit and flag `dou_safe` (story.py:1588) but records no debt. No chapter-6 callback. The only Dou letter is `dou_drawing` | Record debt `dou_rescue` on the rescue. Call it in ch. 6 (quests `the_heart_trial` / `quiet_before_the_storm` / `shen_lians_failure`) with a heaven-grade herb |
| Spared Mudwater lieutenant warns of Gu's ambush | Missing | There is no Mudwater lieutenant. Mudwater Hideout has only `mudwater_bandit` and boss `big_toad_tan` (world.py:1127-1146) | Add a lieutenant with a spare/kill choice and a warning callback before `gus_warehouse` (ch. 8) |
| Killed lieutenant → his brother hunts you on Caravan Road | Missing | None | Add the brother as a hunter elite on `cr_caravan_road` |
| (Build's actual debts: `gu_repays` / `gu_remembers`, ch. 15) | Differs (extra) | story.py:1650-1656, mail story.py:1725-1728 | Keep them as Act II debts in karma.json |

## 10. Part 8: bonds

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Dao Companion: Lan Yue, Tie Niu, Qiu Feng or Bai Ling at 5 hearts, one per character | Partial | All four exist as companions (companions.json; npcs.json `lan_yue`, `tie_niu`, `qiu_feng`, `bai_ling`). No hearts and no bond | Add |
| Sworn siblings: up to 3 companions at 4 hearts | Missing | Active cap is 2 (companion_authority.gd:22) | Add (see §4.2) |
| Master: Elder Hu or Elder Sung; inheritance beat at the end of Act I, "the Elder's Last Lesson" | Partial | Both elders exist (npcs.json `elder_hu`, `elder_sung`; `MENTORS`). No "Last Lesson" quest. Act I ends with `farewells` / `the_ascension_gate` (ch. 10), and the mentor's art comes earlier in `the_mentors_gift` (SA5) | Add the "Elder's Last Lesson" beat that passes a legacy art |

## 11. Part 8: favourite gifts

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Aunt Ping: Riverfish Soup | Partial | NPC `aunt_ping` and item `riverfish_soup` exist. No gift data | Add `gifts` to the npcs.json row |
| Granny Liu: Mist Lotus | Partial | `granny_liu`, `mist_lotus` exist | Same |
| Old Ma: Pearls | Partial | `old_ma`, `pearl` exist | Same |
| Mei Qing: Cloudtop Orchid | Partial | `mei_qing` (**and a second entry, `mei_qing_sect`**) and `cloudtop_orchid` (a heaven herb from Crane Cliffs) exist | Same. Key affinity to one identity for both Mei Qing entries |
| Lan Yue: Lotus Root Tea | Partial | `lan_yue`, `lotus_root_tea` exist | Same |
| Tie Niu: Boar Bone Broth | Partial | `tie_niu`, `boar_bone_broth` exist | Same |
| Qiu Feng: vulture plume | Partial | `qiu_feng`, `vulture_plume` exist | Same |
| Bai Ling: formation stone | Partial | `bai_ling`, `formation_stone` exist | Same |

## 12. Part 8: factions with grudges (factions.json)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Mudwater Bandits: hunter threshold 30; clear with 200 taels or a duel with "Big Toad" Tan's brother | Missing | `mudwater_bandit` and `big_toad_tan` exist (enemies.py:252). No faction tag, no brother | Add a faction row and the brother NPC or duel |
| Gorge Bandits: threshold 30; 400 taels or quest "Old Scores" | Missing | `gorge_bandit_adept` exists (world.py:1225-1231). No "Old Scores" quest | Add the faction row and the quest |
| Stoneford smugglers (Elder Gu's ring): threshold 50; story-bound; cleared by Act I ch. 8 | Partial | Story is present: `gus_cargo` (ch. 3), `hidden_cargo` / `gus_warehouse` (ch. 8, sets `gu_fled`). No grudge value | Add the faction row. Clear it on `gus_warehouse` done |

## 13. Part 8: world calendar (valley, v1.0), seeded rotation

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Beast Tide at Stoneford Gate, every 7 real days, rank 2–5 beasts, any realm | Missing | The `sf_gate` room exists. No tide. `beast_rank` does not exist (p4 scope). The sect raid is at `hv_sect_grounds` every 2–3 days (defence.json) | Add a calendar row and a tide event in `sf_gate` |
| Spatial rift: random field room, every 3 days, 60 min, room band +3 levels | Missing | None. `the_rift` (ch. 8) is a story quest, not a rift | Add |
| Drowned Shrine reopening (Deepwater Bend): every 5 days for 24 h; cap Qi Unfurling 9 and below for repeat runs; story entry (ch. 5), sealed vault (SA3) and Nine-Dragon Cauldron always open | Differs | Always open from QU3 (world.py:1179). Repeats are gated only by the Abbot's 24 h respawn (world.py:1210). No cycle and no cap (`realm_below` exists in requirement_rules). Story entry ch. 5 (`the_shrine_surfaces`) ✓. Vault at SA3 ✓ (world.py:1213). **The Nine-Dragon Cauldron is not in the shrine**: it is Alchemist Fen's ch. 11 reward (`horns_for_the_furnace`, story.py:1146-1148) | Add a calendar gate for repeat runs only. Reconcile where the Cauldron comes from (spec implies the Shrine) |
| Waterfall Cave reopening (Whitewater Gorge): every 5 days for 24 h, offset 2 days; Heart Tempering 9 and below; repeat runs only; first visit and Lu's journal page always open | Differs | The cave is a hidden-portal secret room, always open (world.py:1238, 1246). Journal page ✓ (world.py:1248). The chest is one-time; there is no repeat content, so a cycle has nothing to gate | Add repeat loot, a cycle and a cap |
| NPC auction day: Stoneford Market Street, weekly Saturday, Spirit Stones; rare seeds, recipe pages, eggs | Differs | The build's auction is the **Auction Pavilion in Nine Peaks** (Act II, Sage 1; world.py:1678; economy.py:297-313). It is **always open** with 4 lots rotating every 2–6 h. Currency Spirit Stones ✓. Lots include `spirit_egg` and `manual_page` but **no seeds or recipe pages** (auction.json pool). `sf_market` exists but has no auction | Add a weekly Saturday valley auction on the calendar in `sf_market` with a seeds/recipes/eggs pool. Keep or re-cycle the Pavilion |
| Treasure birth (Spirit Fruit): random field room, every 4 days, rival NPC cultivators plus a mini-boss | Missing | No `spirit_fruit` item. The Evergreen tree fruit (7-day cycle, stats.py:65; crafting_authority.gd:346-376) is a personal garden. No rival-cultivator enemies or mini-boss role (enemy roles: dungeon_boss, elite, event, field_boss, normal, story_boss, trial) | Add |
| Gathering trial: Jade or Cloud Herb Terraces, weekly; ranking pays Foundation-pill recipes | Missing | `ja_herb_terraces` exists. **There is no Cloud Sect herb terraces room** (cm_* rooms). The `foundation_guard_pill` recipe exists | Add the event and a Cloud room, or restrict it to Jade |
| Seasons: spring…winter, one real week each, from the account creation date | Missing | No season state. The account has no creation date (only `character.created_utc`) | Add `account.created_utc` and a season calculation |
| Weather (v1.1): rain and fog in marsh and gorge; storms on Summit Ridge | Missing | Only static hazards. `sr_windswept_ridge` has `wind_gust`, not storm. Marsh and gorge rooms have no fog (rm_grey_pools `hollow_puddle`, wg_rapids_terraces `current`) | Add weather tables |

## 14. Part 8: fortune deck (fortune_deck.json)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Void-fall recovery lands in a hidden cave with a chest | Missing | No `fell_out` or void-fall recovery event | Add (needs the S43 fell_out) |
| Remnant soul in a ring (free manual page) | Missing | `manual_page` item exists | Add card |
| Old hermit's chess problem (insight) | Missing | — | Add card |
| Wounded crane (bond +2 with a Jade Crane) | Missing | Pet species `jade_crane` exists (pets.json). Pet bond is 0–10 (pet_authority.gd:102) | Add card |
| Buried jar of 100-year wine (Grain chance on next batch) | Missing | No wine item | Add |
| Lost child (merit) | Missing | — | Add |
| Meteor fragment (Cloudsteel) | Missing | `cloudsteel_ore` exists (there is no `cloudsteel`) | Add card and name the item |
| Dream of the River (Codex entry) | Missing | Codex system exists | Add |
| Meter refills one encounter per 3 h of play | Missing | — | Add |

## 15. Part 8: Heaven Ranking, Trial Tower, activity chests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Heaven Ranking seed: Shen Lian | Partial | NPC `shen_lian` (Cloud Sect disciple) exists | Add to rankings.json |
| Wen Zhao | Partial | NPC `wen_zhao` (Rival) exists | Same |
| Cloud Sect's first disciple | Missing | Not a named NPC | Name one or reuse `shen_lian` |
| Jade Sect's first disciple | Missing | Not a named NPC | Add |
| "Iron Crane" Guo Ming (rogue cultivator) | Missing | No NPC or enemy | Add |
| Madam Hua's guard captain | Missing | `madam_hua` exists. `guard_hou` ("Captain Hou") is the Stoneford gate guard, not hers | Add |
| Gorge Bandit Adept chief | Missing | Only the normal enemy `gorge_bandit_adept` | Add |
| Player enters at top-8 CP or tournament finals | Missing (hooks exist) | `tournament_top8` flag (story.py:855), finals quest (story.py:860) | Wire them in |
| Trial Tower: 30 floors at Stoneford Fairground, one room per floor with a clear condition; cleared floors swept once per day | Missing | `sf_fairground` exists (world.py:657) and hosts only the Entry Trials (`sf_trial_jade` / `sf_trial_cloud`) | Add tower.json and 30 floor rooms or one templated room |
| Activity chests: 4 tiers at 20/40/60/100 points; points from missions, dungeon clears, crafts, harvests, spars | Missing | None. The events these could count exist (`craft_completed`, `node_gathered`, spars, `daily_reset`) | Add activity.json and a counter in Account |

---

## 16. Coverage matrix rows (Living world)

Build is 1.1, so every row below is due except the v2.0 parts.

| Gap-report row (spec milestone) | Status | Evidence | Change needed |
|---|---|---|---|
| Karma ledger (State v0.9, callbacks v1.0) | Differs | §4.1, §8, §9 | Relations home, event names, karma.json, spec debts |
| Righteous–demonic alignment (v1.1) | Missing | §4.2 | Add |
| NPC affinity and gifts (v1.0) | Missing | §4.2, §11 | Add |
| Formal bonds (v1.0, v2.0) | Partial | Paired cultivation and mentors only (§10) | Add |
| Grudges and bounties (v1.0) | Missing | §12 | Add |
| Personal fame and face (v1.1) | Missing | §4.2 | Add |
| World-event scheduler and calendar (v1.0) | Missing | §13 | Add |
| Fortune encounters (v1.0) | Missing | §14 | Add |
| Heavenly phenomena (v1.0) | Partial | world.gd:356-360 | Complete |
| Rankings (v1.1) | Missing | §15 | Add |
| Profession associations (v0.8–v1.1) | Partial | Ranks only | Add guilds |
| Territory and spirit mines (v1.1) | Missing | — | Add |
| Mortal kingdom (v1.1) | Missing | — | Add |
| Weather (v1.1) | Partial | Static hazards only | Add |
| Lifespan as flavour (v1.0) | Missing | — | Add |
| Mobile conventions (v0.8–v1.0) | Missing | Auto-path, tower, chests and auto-hunt are all absent. The idle hunt ignores room eligibility | Add |
| Leisure arts and teahouse (v1.1) | Partial | Tea house only | Add |

## 17. Priority table

| # | Priority (milestone) | Status | Evidence | Change needed |
|---|---|---|---|---|
| 1 | Define S15's undefined rules (v0.8 text fix) | Partial | Fire and furnace, pills never decay (stats.py:297), auto-refine 25% (crafting_authority.gd:430-432) and the heart-demon field are done in G1. **Seed sources are missing**: only `evergreen_heart_seed` exists | Seeds (p3 scope) |
| 2 | Pill resistance, foundation share, residue | Present (existence) | G1 (stats.py:109). Numbers are audited in p2 | — |
| 3 | Heart-demon meter and karma ledger (fields v0.5, rules v0.9) | Partial | Meter ✓. Ledger differs (§4.1) | §4.1 |
| 4 | Treasure quick slot, flying sword, talisman craft, throwables (v0.8–v0.9) | Partial | G2a: treasure slots, throwables, talisman treasure and flight vessels. No Sword Release (`sword_released` never emitted) and no talisman crafting | p5 scope |
| 5 | PetState depth | Missing | No bloodline or contract state | p4 scope |
| 6 | Herb node flags and harvest tap | Missing | No ripening, guardian or harvest events | p3 scope |
| 7 | Enhancement pity, transfer, salvage (v0.9) | Partial | Salvage exists (`item_salvaged`). Pity and transfer do not (crafting_authority.gd:439-461) | p5 scope |
| 8 | Tribulation, Core Forging grade, fates | Missing | No tribulation, `core_graded` or `fate_offered` | p6 scope |
| 9 | World-event scheduler and calendar (v1.0) | Missing | §13 | This packet |
| 10 | NPC affinity, bonds, grudges, bounties (v1.0) | Missing | §§10–12 | This packet |
| 11 | Pet skill books, gear, mount slot, beast bag, Beast Arena | Missing | — | p4 scope |
| 12 | Body ladder, soul line, sect role variants, Inner Arts, stances | Partial | `body_level`, one parry stance | p6 scope |
| 13 | Associations, recipe fragments, experimentation | Missing / Partial | Ranks only. No `recipe_deduced` or `experiment_result` | Guilds here; the rest p2 |
| 14 | Alignment, Blood/Buddhist paths, weapon families (v1.1) | Missing | §4.2 | Alignment here |
| 15 | Rankings, territory, mortal kingdom, weather, lifespan, insect swarm, remaining families (v1.1–v1.3) | Missing / Partial | §§4.2, 13, 15 | This packet for the first five |

## 18. Rules the report found named but undefined

| Rule | Status | Evidence | Change needed |
|---|---|---|---|
| Pill Grain "keeps longer" → pills never decay; Grain redefined | Present | stats.py:297 comment. The G1 changelog says the Codex states it | — |
| "Rare fire or a special furnace" | Present | G1 fires and furnaces (items.py:59, 315) | Nine-Dragon Cauldron source differs (§13) |
| The Reflection uses Heart Demons with no state field | Present | `cultivator.heart_demon` (G1) | — |
| Gardening seeds with no seed source | Missing | Only `evergreen_heart_seed` in items.json | p3 |
| Auto-refine XP unstated → 25% of manual XP | Present | crafting_authority.gd:430-432 | — |

## 19. Genre staples kept out on purpose

| Staple | Status | Evidence | Change needed |
|---|---|---|---|
| Hard lifespan and old-age death | Present (kept out) | No lifespan anywhere | Add the display-only years without a clock |
| Stamina and energy gates, battle passes | Present (kept out) | None found | — |
| Pet permadeath | Present (kept out) | Pets retreat at 0 HP (gap_audit #43) | — |
| Enhancement that destroys or de-levels | Present (kept out) | A failure keeps the level (crafting_authority.gd:454-458) | — |
| Sexual dual cultivation | Present (kept out) | Paired cultivation is SFW meditation (companion_authority.gd:90-97) | — |
| Player full loot at v2.0 | n/a | — | — |
| Full Gu path | Present (kept out) | None | — |
| Corpse refining, soul banners, body seizing as player powers | Present (kept out) | The Wisp Banner treasure is a wisp summon, not a soul banner (CHANGELOG G2a) | — |
| Stat and aptitude pills sold in shops | Present (kept out) | Shop scan found no permanent attribute items | — |
| Herb rot and pill decay | Present (kept out) | Pills never decay | — |
| Unrestricted auto-battle | Partial | The idle hunt is abstract offline income, but it is **not limited to idle-eligible rooms** (account_authority.gd:151-196 ignores `room.idle`) | Enforce `room.idle` |

## 20. Event list S43–S49

### Relations and Calendar rows (this packet)

| Event row | Status | Evidence | Change needed |
|---|---|---|---|
| `merit_changed`, `sin_changed`, `debt_recorded`, `debt_called` (Relations → Progression risk step, heart demon from sin, Quest debt callbacks, tribulation strength) | Differs | `karma_changed`, `karma_debt_recorded`, `karma_debt_repaid` come from Progression. Reactors: HUD only (hud.gd:494-500) and mail. No Quest reactor, no tribulation | Rename, move and add the Quest reactor |
| `alignment_changed`, `affinity_changed`, `bond_formed`, `grudge_changed`, `hunter_dispatched`, `fame_changed` | Missing | — | Add |
| `world_event_scheduled`, `world_event_started`, `world_event_ended` (→ Notifier, map markers, Enemies, World gates) | Missing | — | Add |
| `season_changed`, `weather_changed`, `ranking_changed`, `fortune_encounter`, `heavenly_phenomenon` | Missing | — | Add |
| `fell_out` → Relations (fortune check) | Missing | No emitter | Add (p1) |
| `tribulation_*` → Calendar (heavenly phenomenon) and Relations (NPC reactions) | Missing | No tribulation | Add (p6) |

### Other rows (owned by other packets; existence only)

| Event row | Status | Evidence |
|---|---|---|
| jumped, landed, wall_kicked, art_used, climb_started/finished, fell_out, volume_entered/left | Missing | No emitters in scripts |
| pill_resistance_changed, foundation_changed, residue_changed | Partial | Only `residue_changed` is emitted (progression_authority.gd:704) |
| heart_demon_changed | Present | progression_authority.gd:713 (not in the event contract) |
| fate_offered/chosen, tribulation_*, core_graded, qi_deviation, epiphany, vow_broken, body_tier_reached, physique_awakened | Missing | — |
| flame_absorbed, furnace_blast, pill_cloud, pill_tribulation_result | Partial | `flame_absorbed` and `pill_cloud` only |
| recipe_deduced, experiment_result, guild_rank_changed, commission_completed | Missing | — |
| herb_harvested, guardian_spawned, seed_found, herb_ripening, garden_raided | Missing | The build uses `node_gathered` instead |
| bloodline_awakened … pet_core_formed | Missing | — |
| beast_king_spawned, beast_tide_started, beast_tide_result | Missing | — |
| treasure_used, sword_released/returned, sword_intent_changed | Partial | Only `treasure_used` |
| natal_grew … weapon_awakened | Partial | Only `item_salvaged`, which the spec calls `items_salvaged` |

---

## Status counts

Counted over all 208 table rows above. A row with two statuses (for example "Missing / Differs") is counted under the first one.

- **Present: 19.** This includes 9 "kept out" rows and 1 "by default" row.
- **Differs: 16.** This includes 2 rows for build extras that the spec does not list.
- **Partial: 39.**
- **Missing: 132.**
- **n/a: 2.** These are v2.0 player bonds and the full-loot stay-out row.
