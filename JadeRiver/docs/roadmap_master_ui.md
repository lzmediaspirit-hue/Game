# Roadmap · the Master Prompt and the UI Designer Prompt

Two prompts arrived on 26 September 2026 and are kept unchanged as reference material:

- `docs/research/master_prompt.md`: *Jade River — Full Review, Expansion & QA Master Prompt*, eleven phases of review,
  research, content and QA;
- `docs/research/ui_designer_prompt.md`: a brief for a senior pixel-art UI/UX designer, seven phases from reading the
  project to a prioritised UI roadmap, with a mockup approval gate in the middle.

This page breaks both into buildable work items, audits each against the build at commit f7a7817 (V10d1) the way
`docs/gap_audit.md` and `docs/v2_audit.md` do, groups the items into phases in the style of
`docs/idle_gathering_design.md` §9 and `docs/act3_design.md`, and says where each phase sits against V10d3, v1.2
Phases C–E and the later versions. Where a prompt disagrees with Build Prompt v2 or the design pages, §5 lists the
conflict and a recommended resolution; nothing is settled silently.

Neither prompt is a build order by itself. Both are written for an agent that reviews first and proposes second, and
the UI prompt forbids touching project files before its mockups are approved. The phases below keep those gates.

---

## 1. The two documents in short

### 1.1 The Master Prompt

Role: a combined designer, MMORPG psychologist, QA tester, content designer and technical reviewer working on a
"2D pixel-art, xianxia-themed, MapleStory-style mobile game". Global rules: every finding written as an instruction a
later agent can execute; every approved change added to the roadmap; bugs fixed in code as found (the review holds
resolutions, not an open bug list); every system split into a **Single Player (now)** and an **Online (future)** track.

| Phase | Asks for |
|---|---|
| 1 World | Audit the world map against MapleStory's structure; a world-expansion plan (maps per region, biomes, travel, hidden maps); an on-screen animation system for breakthroughs, story beats, boss intros and rare drops |
| 2 Items | A MapleStory-derived item-count target; new items by slot, rarity, realm, element, path and set; build archetypes with full gear paths; an Item Wiki with one entry per item |
| 3 UX pass 1 | Play start to end as a new player; log and fix friction, collision, interaction conflicts, missing doors, quest dead ends; a long-term-engagement plan from MapleStory's retention psychology |
| 4 Psychology | Skill-VFX escalation per realm; colour psychology (rarity, damage numbers, biome moods); feedback loops (hit-stop, sound, knockback, loot fountains, fanfare); an implementation plan |
| 5 Guidance | Main-quest tracking with directional guidance; side quests across the world; MapleStory's NPC head markers (! / coloured ! / ? / …) verified through the quest lifecycle |
| 6 Drops and sprites | An equipment drop table on every monster; a sprite audit prioritising enemy diversity; a Monster & Drops Wiki cross-linked with the Item Wiki |
| 7 Bosses | Research MapleStory and Idleon boss fights; gap list against Jade River's bosses; phase, telegraph and reward instructions |
| 8 Soul Rings | Research the Douluo Dalu soul-ring system only; adapt it to Jade River's world, unlock timing and builds; roadmap it |
| 9 Theming | Rename realms to widely recognised xianxia terms; shift anything wuxia-leaning toward xianxia |
| 10 Cultivation loop | Enforce: cultivate for Qi (Qi-rich places are better) → bottleneck at each of Early / Middle / Late / Peak → minor breakthroughs with stage pills and varied resources → major breakthroughs with elixirs, materials and sometimes a trial, quality affecting success and stats |
| 11 QA pass 2 | A second full QA pass; the Full Review Document with every section; the SP/Online split; the roadmap updated with the review itself as a deliverable |

### 1.2 The UI Designer Prompt

Role: a pixel-art UI/UX designer and art director who reads Godot projects. Context claimed: landscape, offline idle
cultivation, fists at creation, portal-linked rooms, account play with unlocking slots, a Sect after "more than 3
characters", Spirit Animals at a level, a top-right minimap, a planned World Creation system. The project is the source
of truth where it disagrees (§2.2 checks each claim).

| Phase | Asks for |
|---|---|
| 1 Understand | From the project: every system (purpose, goal, data, connections); every screen's elements with node paths; a navigation map with tap counts; the art/UI inventory (palette, fonts, pixel scale, inconsistencies); screenshots; open questions, then stop |
| 2 References | MapleStory / MapleStory M, Soul Saver, Legends of Idleon, Idle Skilling and 2–4 more: HUD, hub structure, themed system UIs, frame style, feedback; a comparison table against Jade River |
| 3 Mockups | Full-screen landscape mockups at the base resolution of the HUD, the hub, every system screen in its theme, key states; real content; one style; **stop for approval** |
| 4 Review | Problems per screen with severity and location; what the player feels now against what they should; global consistency issues |
| 5 Redesign | Each system as what it *is* (a technique constellation, a realm ascent, a jade chest, a sect courtyard, a beast scroll, an ink-scroll map, a pill furnace); concept, wireframe in px, element states, navigation, annotated mockup, Godot implementation notes |
| 6 Style guide | Palette roles, nine-slice frames with xianxia motifs, pixel grid and spacing, pixel fonts and sizes, icon rules, button states and touch targets, the final HUD spec with the minimap, a Godot Theme resource plan |
| 7 Roadmap | Every change ordered by impact against effort, with the files each touches |

Rules: specific and critical; project-based claims; originals only, no copied art; landscape and thumb reach; no
specs before the Phase 3 approval; propose, do not apply; one phase at a time.

---

## 2. Audit against the build

Each row is one work item. **Present** means the build already does it; **Partial** means a related piece exists and
part is missing; **Missing** means nothing like it exists. Evidence names the files that decided the class. The
**Phase** column points at §3.

### 2.1 Master Prompt items

#### World structure and exploration (Master 1)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M1 | Many interconnected rooms, distinct biomes, towns as hubs, travel as content | Present | 144 rooms in 3 zones and 44 regions (`data/rooms/`, `data/zones.json`); 283 portals (147 edges, 96 doors, 19 sealed, 11 gates, 7 hidden, 3 dungeon); 29 town rooms; six map themes (`data/map_themes.json`); one backdrop set per region; teleport stones; the Lantern Run and Starsea voyages | — |
| M2 | More than one viable route through the world | Partial | `docs/world_plan.md` §1 gives one cross-link per built act (a second road through Acts I–III, not yet built) and two routes through each planned act (§3–§5, Routes and cross-links) | P10 |
| M3 | Hidden and optional maps that reward exploration | Present | 9 `secret` rooms (`ds_drowned_grotto`, `cf_behind_falls`, `bm_smugglers_cove`, …), 7 hidden portals from Spirit Awakening 2 (`unlocks.json` `hidden_portals`), 4 hidden regions, and the S43 optional ledges counted on the Codex's Paths Above tab (`map_page.gd:170`) | — |
| M4 | A world-expansion plan: maps per region, biomes, connections, hidden maps | Present | `docs/world_plan.md`: rooms per region, biomes, routes, travel and hidden maps for v1.3 Star Frontier (64 rooms), v1.4 Outer Heavens (57 and the Inner World) and v1.5 World Genesis | P10 |
| M5 | On-screen animation for realm breakthroughs | Present | P6: `data/moments.json` rows `breakthrough_channel`, `breakthrough_minor`, `breakthrough_major`, `breakthrough_failed`, `realm_phenomenon`, `tribulation`, played by `MomentView` (`scripts/presentation/moment_view.gd`). The major breakthrough is mockup 05: the world dims round you and the HUD recedes, motes gather, a pillar and rings rise; the great realm is written on an ink band with a seal; the stats that rose, the tribulation card and an Opens chip; input back at 1.5 s, a tap skips; its fanfare is `breakthrough`, `brush_stroke`, `seal_press`, `unlock`. A failure says why and how to recover (`failure.*`); the tribulation holds its storm to the result. `rules_tests` `moments_suite` cases 1–3, 9–11 on the real rows; `docs/moments/breakthrough_major_*.png`, `breakthrough_minor.png` | — |
| M6 | On-screen animation for boss intros and phases | Present | P6: `boss_intro` (ink bars, the name and Level on a band, `boss_sting`, captioned; the first aggro of a visit, no lock), `boss_phase` (the stage numeral on a band under the boss bar, with the shake and roar), `boss_defeated` and `field_boss_defeated` (a pale-gold flash, the name with Defeated, the Untouched line for a clean kill, `boss_fall`). `moments_suite` plays Big Toad Tan's den for real (intro once a visit, phase card at 49%, the cut, the room change); `docs/moments/boss_intro.png`, `boss_phase.png`, `boss_defeated.png`. P9a switches the intro to `boss_engaged` with its camera pan and adds epithets and lines (`docs/moments_design.md` §2.4) | P9 |
| M7 | On-screen animation for story beats | Present | P6: `story_beat` closes a chapter when its last main quest is handed in, after the dialogue page: ink bars close in, a band writes the chapter over the quest's name, with the bell (`moments.json` `chapter_ends`, the 23 closing quests); `trial_opens` on a band; the camera rig (`World.hold_camera`, the `camera` layer) and `letterbox` layer for staging. Set pieces keep their room events (`set_pieces.json`). `docs/moments/story_beat.png`, `trial_opens.png` | — |
| M8 | On-screen animation for rare drops | Present | P6: `rare_drop` (a beam over the piece until it is picked up, a strip naming it in its grade or quality colour, `rare_chime`; finds within 1.5 s share one strip; a toast in a fight) by the rare rule in `moments.json` `rare` (Perfect and Relic pieces, legend pieces, spirit animal books, treasures, 49 named drops); `loot_fountain` flies a boss's, field boss's, chest's, tower floor's or rift's drop out one piece after another to where it lies (`LootView.launch`, `loot_dropped` `source`); `rare_pill` for a Halo or Soul pill. Cases 4 and 14; `docs/moments/rare_drop.png`, `loot_fountain.png` | — |
| M9 | A catalogue of animation types with trigger, duration and art requirements | Present | P6: `data/moments.json` from `tools/data/moments.py`, 24 rows, each with its trigger event and matchers, merges, duration, lock and skip, priority and queue rules, fight and page behaviour, layers (under or over the HUD, through the HUD, or in the world, each with its time) and its art (`ink_band`); designed in `docs/moments_design.md`. `data_validation` `moments_data_suite` checks every event and payload key against `data/event_contract.json`, every FX kind, sound, string, colour and anchor, the timing, and the technique `vfx` blocks; `contract_tests` checks the declared payloads at every emit site and that the view writes no game state | — |

#### Item economy and build diversity (Master 2)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M10 | A researched item-count target | Present | `docs/item_plan.md` §2: a target of 481 pieces through v1.3 (264 named), per zone and archetype, set against today's counts (§1) | P7 |
| M11 | Items organised by slot, rarity, realm, element, path synergy and set | Partial | P7b part 1: named tags (archetype, zone, element, path, fixed affixes) in `tools/data/gear.py` / `data/gear.json`; set rows with archetype, tier, element and path; 71 banded bases (brush and bell at every grade, Sovereign and Will). The named sets per archetype come with step 8 | P7 |
| M12 | Distinct build archetypes each with a full gear path | Partial | P7b part 1: six set lines with their mechanics (Unbroken, Honed Intent, Venom Hand, Kin-Bond, Living Array, Sustained Note) and the one-in-three family bias; each archetype can use 75–81% of drops. The named gear path per archetype is step 8 | P7 |
| M13 | An Item Wiki, one entry per item (icon, slot, stats, rarity, requirement, sources, lore) | Present | `docs/wiki/items.md`: all 614 items with icon, grade, iLv, stats or effect, requirement, description and every source with its rate, written by `tools/dev/wiki.py` | P7 |

#### Player-experience playthrough (Master 3)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M14 | A new-player playthrough log, start to current end | Present | `docs/review-v12.md` (a): `prologue_run` and `valley_run` play a new character from the Prologue to the end of Act III by intents; ten Act III findings, each with root cause, fix and test | P2 |
| M15 | UI friction, unclear feedback, confusing menus logged and fixed | Present | `docs/review-v12.md` (d) and `docs/ui_inventory.md` §5: 25 faults (B1–B25) and 14 inconsistencies logged with file, line and screenshot; the P2 bug pass fixed B1–B25 (B19 to the code review), the `ui_suite` checks sizes, overlaps and label fit on every page | P2 |
| M16 | Collision problems, invisible walls and terrain snags | Present | `tests/room_sweep` (in `run_tests.sh`): every room headless with the real `MovementSolver`; every door and interactable reached from every way in, every arrival reaches a way out, the route between every pair walked (about 3,400 s of walking), no body held in place, every solid footprint under its art. It found the ground running in under raised steps in four rooms; `under_steps()` in `tools/data/world.py` fixed them (`docs/review-v12.md` (a) "Findings in the P2 close-out") | P2 |
| M17 | Interaction conflicts (the training dummy answering as talk; conversations forced closed by hand) | Present | Played as the `valley_run` character (bf5): between Uncle Guo and his dummy the context button talks to Guo and the attack button strikes the dummy only (`_dummy_beside_npc`); on the real dialogue page a last line with nothing to choose, an accept and a hand-in close the conversation by themselves (`_conversations_close`, `_choose_on_page`). `query_context` skips objects more than 48 above or below, as `interact` refused them (`world_authority.gd`) | P2 |
| M18 | Overlapping objects that block interaction | Present | `data_validation` `overlap_suite`: no interactable's reach covers another's spot where it would take the context button (by `WorldAuthority.context_rank`), nor a door. The 41 overlaps it found are moved in the builders, and `verticality.in_reach` keeps lifted nodes and chests apart (`docs/review-v12.md` (a)) | P2 |
| M19 | Houses and shops with no visible door | Present | Doors are portals of kind `door` (96) drawn with a plate and an arrow, and interior doors stand on the back wall (`portal_view.gd:4-54`) | — |
| M20 | Quest flow gaps, dead ends, missing guidance | Present | `data_validation` `quest_guidance_suite`: every guided and main quest where the story offers it, played on a probe with the game's own rules: the giver reachable, marked and offering it; each objective with a place gets a direction mark to a real room that holds it and that the player can reach then; the mark leads to the hand-in. The mark now follows the current objective and finds NPCs where they stand (`QuestAuthority.quest_target`, `rules_tests` `guidance_suite`) | P2 |
| M21 | Long-term engagement: daily reasons to log in, social loops, "one more level" | Present | `docs/review-v12.md` (e) "The engagement plan" (E1–E6) and `docs/research/retention_notes.md`; the daily and weekly loops listed above. The social loop waits for v2.0 Online | P2 |

#### Game psychology and sensory design (Master 4)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M22 | A skill-VFX escalation curve per realm | Present | P6e: every technique has a `vfx` block (`tools/data/techniques.py`): its tier by the band of the realm that teaches it (`moments.json` `vfx_bands`, 1–7), its shape and its spark style; `vfx_tiers` scales spark count, size, reach and core, cast ring, area wave width and echo waves, number size, shake per cast and screen tint (§5.2). Today tiers 1–5 hold 16, 22, 9, 1 and 8 of the 56 techniques; tier 1 is the old look. Shapes are drawn at the true reach (`World._cast`). `moments_suite` case 12, `moments_data_suite` (tier against the realm band and grade, shapes against `FxLayer.KINDS`); `docs/moments/escalation.png` | — |
| M23 | Multi-hit numbers, particles and screen shake | Present | P6e: the hits of one cast on one foe stack 18 px apart and 0.06 s apart, swaying, six at most, with a pale-gold total from three (`FxLayer.number`, case 13); numbers from 10,000 in three figures (`UiKit.short`); sparks by tier and by family or element (ink, rings, embers, shards, squares); one shake per cast on its first hit from tier 3; a screen tint in the element's colour from tier 3 under the flash limiter; `rain` and `pillar` FX. Screen shake, Bright flashes, Reduce motion (new), Battery saver and Damage numbers all respected (case 9). `perf_tests` plays the crowd under the major breakthrough and a Sword Swarm inside the frame budget and the FX cap. Hit-stop stays CombatAuthority's | — |
| M24 | Colour psychology: rarity coding, damage-number colours, biome palettes | Partial | 10 grade colours and 12 quality colours (`data/grades.json` → `UiKit.grade_color`); crit gold, Soul violet, Qi teal numbers (`fx_layer.gd:3-4`); a backdrop set per region. P6: every moment colour is a `UiKit` token or an element, grade, quality or Dao id (checked by `moments_data_suite`); a pill cloud, a rare beam and a find's name take the one colour of their quality or grade; a stack's total is pale gold. No written palette rule for biomes or a check that the colours read on a phone | P4 |
| M25 | Feedback loops: hit-stop, sound, knockback, loot fountains, level-up fanfare | Present | Hit-stop, `Audio`, per-attack `knockback`; P6: the loot fountain (§5.8), the breakthrough fanfare (gong and chimes, brush stroke, seal, unlock bell) and the level's short gong (`gong_short`), `boss_sting`, `boss_fall` and `rare_chime`, all from `tools/audio/sfx.py`; each moment's sound, buzz and caption from its row | — |
| M26 | An implementation plan for each finding | Present | `docs/review-v12.md` (e) tables and (f): every finding has a fix, a phase and files | P2 |

#### Quest guidance and side content (Master 5)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M27 | The current objective always visible, with a direction to the target map | Partial | The quest tracker (`hud.gd:1515`, revealed by `navigation`), `target_room` on quests, and the auto-path button that walks the room graph (V8g1, `hud.gd:306`). No arrow and no marker on the minimap; the minimap draws only the current room (`hud.gd:1577`) | P1 |
| M28 | Side quests across the world | Present | 210 quests: 66 main, 75 side, 60 guided, 9 prologue (`data/quests.json`); county jobs, the bounty board, daily missions | — |
| M29 | NPC head markers: ! for a new quest, ? to hand in, … in progress | Present | `quest_authority.npc_marker` returns `main`, `side`, `ready`, `talk`; `npc_view.gd:87-101` draws a gold diamond !, a blue circle !, a ? and an … | — |
| M30 | A second ! colour when the player has done a quest for this NPC and it has another | Missing | The second colour today means side against main, not "again" | P1 |
| M31 | Markers verified through the whole lifecycle | Partial | `valley_run` plays quests but asserts no marker states | P1 |

#### Drops, sprites and content volume (Master 6)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M32 | Every monster has an equipment drop table | Partial | 92 of 124 loot tables carry an `equipment` roll (chance and `min_quality`, drawn from the bands) and 35 a `rare` list (`data/loot_tables.json`); 32 tables have none (trial puppets and event foes among them, to be sorted) | P1 |
| M33 | Drop rates balanced by rarity and tier | Present | P7b part 1: the drop rules in `grades.json` read by `LootRules`, and a `balance_sim` drop check: 5.9 pieces an hour of hunting across 29 regions, every grade inside its quality targets | P7 |
| M34 | A sprite audit of NPCs, equipment, terrain and monsters | Partial | 68 creature sheets for 111 enemies (`data/creature_art.json`), 749 icons, `docs/art-contracts.md`, the animation contract tests and the compatibility gallery. No gap list | P7 |
| M35 | Enemy sprite diversity per region | Partial | Eleven Act III sheets drawn ahead (CHANGELOG 1.2 A); many valley foes share a sheet with a dye. A per-region count is not written | P7 |
| M36 | A Monster & Drops Wiki | Present | `docs/wiki/monsters.md`: all 121 enemies by zone with sheet, spawns, level band, stats, attacks, phases and full drop tables | P7 |
| M37 | Every item has a source; every monster is in the wiki with its drops | Present | `data_validation` `item_source_suite`: every item has a source or a mark, and `KNOWN_SOURCE_GAPS` is empty (P7b part 1); every monster is in `docs/wiki/monsters.md` with its drops | P7 |

#### Boss design (Master 7)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M38 | Research on MapleStory and Idleon boss fights | Present | `docs/research/ui_reference_notes.md` §11 (boss presentation, sources R23–R30) and `docs/boss_design.md` | P9 |
| M39 | Phases, telegraphs, arena mechanics, enrage and reward loops on every boss | Partial | 11 bosses; 8 have `phases` (a summon at 60 %, enrage at 30 %), every attack has `windup_s` / `active_s` / `recover_s` and a "!" tell (`enemy_view.gd:178`), ground markers on the bombard and broadsides, Presence and Sphere clashes (v1.2). `the_reflection`, `elder_gu` and `hollow_behemoth` have no phases; no boss demands movement by arena geometry | P1, P9 |
| M40 | Re-runnable boss rewards | Partial | Dungeon keys, field boss timers, the Trial Tower and Beast Kings; no per-boss reward loop | P9 |

#### Soul Rings (Master 8)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M41 | A research page on the Douluo Dalu soul-ring system | Present | `docs/research/soul_band_research.md` | P8 |
| M42 | An adapted system in Jade River's world | Partial | Designed: `docs/soul_bands_design.md` (Soul Bands, unlocked at Spirit Awakening 1, §11 decisions). Built with v1.3 (P8b) | P8 |

#### Theming and realm naming (Master 9)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M43 | Realms renamed to Qi Refining, Foundation Establishment, Golden Core, Nascent Soul, … | Present (as C1) | The ladder keeps its names; the Codex's `old_scrolls` entries give the old scrolls' name for each great realm (`tools/data/story.py`, `docs/realm_old_names.md`), granted by the account's highest realm | P10 |
| M44 | Everything wuxia-leaning shifted toward xianxia | Partial | The world is already immortal cultivation (Qi, realms, tribulations, sects, Daos, heavens, lifespans); `README.md` calls it "wuxia/xianxia" and two atlases are named `wuxia-props-v4.png` and `wuxia-buildings-v4.png`. No text sweep has been done | P10 |

#### The core cultivation loop (Master 10)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M45 | Cultivate converts time into Qi; Qi-rich places are more efficient | Present | `ProgressionRules.meditation_rate` × the room's `qi_density`, Qi springs, ambient Qi, seclusion with its 12-hour cap | — |
| M46 | Stages Early / Middle / Late / Peak with a bottleneck at each | Partial (conflict C3) | `docs/cultivation_loop.md` §14: Early 1–3, Middle 4–6, Late 7–8, Peak 9 as bands of the nine sub-levels; drawn on the ascent in P5b | P10 |
| M47 | Minor breakthroughs use a stage pill by default, other resources sometimes | Present (conflict C4) | `docs/cultivation_loop.md` §7 and §13 F3: the minor step stays a free tap; a stage pill, if wanted, needs a `stage_requirements` field read only for minor steps | P10 |
| M48 | Major breakthroughs: elixir, materials, sometimes a trial; quality affects success and stats | Partial | `major_breakthrough.requirements` per realm (pills, body level, methods, the Heart Trial, Heaven's Cleansing, Core Forging), the risk index and success chance, pill marks +2 % each, the Core Forging grade and heavenly tribulation (S48). Found in P10 (`docs/cultivation_loop.md` §13): a pill's quality and marks change its potency (the Qi it gives, `inventory_authority.gd:386-390`), and stats only through the Core Forging grade; they do not change the success chance. Planned: the breakthrough pill's quality as a term of the risk index, with v1.3 | — |

#### QA pass 2 and the Full Review (Master 11)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M49 | A second full QA pass with every bug fixed | Missing | — | P11 |
| M50 | The Full Review Document (all sections, prompt-engineering style, no open bug list) | Missing | — | P2, P11 |
| M51 | Every system split into Single Player and Online tracks | Present | `docs/architecture.md` "Single Player and Online, per system" and `docs/review-v12.md` (e); P11 revisits it for v2.0 | P2, P11 |
| M52 | The roadmap updated, with the review itself as a deliverable | Partial | This page; the review is registered as P2 and P11 | — |

### 2.2 UI Designer Prompt items

The prompt's context claims, checked against the project:

| Claim | Project |
|---|---|
| Landscape | `project.godot`: 1280×720, `canvas_items` stretch, `keep` aspect, `handheld/orientation=0` (landscape) |
| Offline idle cultivation | Seclusion, idle tasks and Keeping Post (V10) |
| Fists at creation | `README.md`: "bare fists and no Qi"; weapons at the Weapon Hall, Bone Forging 3 |
| Rooms linked by portals | 283 portals across 144 rooms |
| Character slots unlock with progress | 12 slots by account realm or sect level (`data/account_rules.json`) |
| A Sect after more than 3 characters | **Differs**: your own sect opens at account realm Qi Unfurling 1 (`unlocks.json` `your_sect`), the same gate as the fourth slot, so it reads as "at four slots" (`README.md`) without counting characters |
| Spirit Animals at a level | Qi Unfurling 5 (`unlocks.json` `spirit_animals`) |
| Minimap top-right | `hud.gd:41` `minimap_rect = Rect2(1032, 16, 232, 140)` |
| World Creation planned | v1.5 World Genesis (the last great realm in `realms.json`; `CHANGELOG.md:1025`) |

#### Understand the project (UI 1)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U1 | Every system: purpose, the player's goal, data and progression, connections | Present | `docs/ui_inventory.md` §1: every authority with its purpose, the player's goal, data, progression and connections | P2 |
| U2 | Every screen's elements and what they do, with paths | Present | `docs/ui_inventory.md` §2: every page, the shell and the HUD, element by element with paths | P2 |
| U3 | A navigation map with tap counts | Present | `docs/ui_inventory.md` §3: the navigation map with tap counts | P2 |
| U4 | The art/UI inventory: palette, fonts, pixel scale, inconsistencies | Present | `docs/ui_inventory.md` §4: palette, fonts, pixel scale, the two kits and the inconsistencies I1–I14 | P2 |
| U5 | Screenshots of every screen | Present | `docs/ui_inventory/*.png`: 122 screenshots, every page and tab, taken as the `valley_run` character on the current build | P2 |
| U6 | Open questions, then stop | Present | §6 lists the questions; the answers are recorded there | P2 |

#### Reference analysis (UI 2)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U7 | HUD, hub, themed screens, frames and feedback of each reference, with sources | Present | `docs/research/ui_reference_notes.md` §2–§11: HUD, hub, system screens, feedback and bosses of eight references, with sources | P2 |
| U8 | A comparison table, Jade River system against its closest reference | Present | `docs/research/ui_reference_notes.md` §12 | P2 |

#### Mockups (UI 3)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U9 | Full-screen mockups of the HUD, the hub, every system screen and key states, in one style | Missing | The HD kit's `--review PNG` sheet shows frames, not screens | P3 |
| U10 | Approval before any spec | — | A human gate | P3 |

#### Full review (UI 4)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U11 | Problems per screen with severity and location; felt against intended | Present | `docs/review-v12.md` (d) "Per screen": each fault with severity, place and owner; fixed in the P2 bug pass | P2 |
| U12 | Global issues: consistency, palette, fonts, icons, scale, spacing | Present | `docs/review-v12.md` (d) "Global issues" G1–G6: G1 and G2 fixed in P4a. **G3 fixed in P5a**: the technique slots and system toggles left the lower middle for two rings round the attack button and the fan (`hud.gd`, decision 20), an empty slot is not drawn, and nothing of the HUD stands in the clear zone round the player (`rules_tests` `hud_suite`). **G4 fixed in P5a**: world labels keep an offset per kind and a layout pass places them in rows so none touches another or sits under a control (`scripts/presentation/world_labels.gd`, `labels_suite`); evidence in `docs/ui_p5/hud/` (`hud_town.png`, `hud_boss.png`). G5 and G6 stay with P4 and P5 | P2 |

#### Redesign every system to its theme (UI 5)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U13 | Techniques as a branching tree or constellation | Built (P13b: one tree a tab, `docs/ui_p5/techniques/`) | `techniques_page.gd`: a list of techniques and four slots per tab (combat, Inner Arts, secret arts). The Dao tab is a list with bars (`cultivation_page.gd:315`); the sect tree is three columns of five nodes (`training_sect_page.gd:81`) | P5 |
| U14 | Cultivation as a meridian diagram or an ascent of realms | Partial | Overview with realm, progress and bottleneck; Foundation with meridians as rows and +1 buttons; the Body tab's four rungs; Heart, Paths, Methods, Dao, Seclusion tabs (`cultivation_page.gd`). No diagram or ascent | P5 |
| U15 | Inventory as a jade chest or spatial-ring grid | Present | **Built in P5 as concept B** (decision 24; mockups 07_bag_b, _card, _pill, 08_bag_b_empty): the heaven inside the Spirit Gourd, a sky with no frame that grows with the gourd; the figure at 2.5 with the eight worn slots on a gold orbit (decision 8, `CharacterPage.draw_worn`); one grid ten across, five rows in view, the next gourd's spaces locked at its end; the kinds (items.json `bag_kinds`), the Key Pouch, Sort and the purses as floating tokens; a small card beside a tapped space (decision 15) with what wearing a piece would make of your own totals (`StatRules.equip_change`) and "···" for the rest (`inventory_page.gd`). The gourd of 07 and 08 v2 was withdrawn by decision 15. Screenshots beside the mockups in `docs/ui_p5/bag/` | P5 |
| U16 | Sect as a hall or courtyard with disciple positions | Partial | `your_sect_page.gd`: Buildings, Disciples, Expeditions, Territory tabs; the buildings themselves stand in the sect's rooms in the world as they are built (`README.md`) | P5 |
| U17 | Spirit Animals as a stable or bestiary scroll | Partial | `pets_page.gd`: Care, Growth, Fusion, Breeding, Eggs; the HUD pet strip; the Codex Collection | P5 |
| U18 | The world map as a painted ink scroll of linked rooms | Present | **P5, decision 25:** `map_page.gd` built to mockups 16 and 16_resources: the zone's painting in a lacquered frame filling the screen, areas as glowing nodes on dotted routes, plates placed by one layout pass so no text touches (decision 17), the area card with Track Route and Walk there (auto-path), Resources and Objectives views, zone tags and the Heaven Ranking; `rules_tests` `map_suite`; the build beside the mockups in `docs/ui_p5/map/` | — |
| U19 | Alchemy as a furnace with ingredient slots | Present | The five-screen furnace with fire and array (`crafts_page.gd:3-5`, V9e2) | — |
| U20 | Per system: concept, wireframe in px, element states, navigation and taps, annotated mockup, implementation notes | Partial | `docs/page_identity.md`: a row per page (concept, material, layout signature, motion, what stays shared) and drawn mockups for twelve; the Character page built to its row and mockup 09 v2, with its titles as honours (decision 16), screenshots in `docs/ui_p5/` against the mockup; the Post family (Roll-Call, Works, Welcome Back, Pouches) built to rows 12, 14, 23 and 44 and mockups 13, 13_first and 14 v4 (decisions 11, 21, 26), screenshots in `docs/ui_p5/post/`; the other pages wait for their parts; **the Records family started**: the Codex as the field book and its Old Scrolls as a mounted rubbing (mockups 18 and 18_scrolls, decision 11) and the Calendar to mockup 19 (decision 22), screenshots and comparisons in `docs/ui_p5/records/`; **the Records family finished**: the Dialogue strip, the Quests board, the Mail's letter case and the Notice Board's wall (rows 2, 6, 17, 21; mockups 21, 12 v2, 22), in `docs/ui_p5/records/` too; Market family built**: the Shop as the stall of mockup 17 with the bag in the gourd's heaven and buy-back a token (decisions 11, 24), the Storage chest with the Treasury's tray, the Exchange's barred window, the County Hall's bench and the Auction's stage, screenshots in `docs/ui_p5/market/`; the other pages wait for their parts | P5 |
| U21 | Godot notes: node tree, scenes and scripts touched, Control / NinePatchRect / Theme usage | Present (conflict C8) | As C8 recommended, the notes name page files, `Page` hooks and `UiKit` calls instead of node trees: `docs/page_identity.md` §8, How a page takes its identity (`Page.Identity`, `draw_surface`, `content_rect`, the title and tab hooks, `ground`/`face` for contrast, `unfold` for motion, `SURFACE` and `TEXT_ON`, HD art through `build_ui_hd.py`), with the steps to convert a page and the Character page as the worked case | P5 |

#### Style guide (UI 6)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U22 | A palette with roles (primary, rarity tiers, positive and negative, disabled) | Present | `docs/ui_style_guide.md` §1 names every role (primary `PAPER`, secondary `MIST`, heading `GOLD`, positive `BRIGHT_JADE`, negative `RED_TEXT`, warning `WARNING`, disabled `HOLLOW`) and the grade and quality tiers; `UiKit` holds them as tokens, every grade has a colour (`tools/data/stats.py`), no page or the HUD carries a colour literal, and `rules_tests` measures every text token on the kit art it sits on (P4 steps 1 and 2) | — |
| U23 | Nine-slice panels with xianxia motifs | Present | The HD kit (`tools/ui/build_ui_hd.py`, `art/ui/hd/`) draws every frame, now with the HUD's `hud_ring` too; the pixel kit keeps the motifs inside them (style guide §5) | — |
| U24 | Pixel scale, grid and spacing rules | Present | Style guide §2: the 8 px grid, the safe area and six standard windows as `Page` constants; every window standard and every list pitch on the grid, checked by the `ui_suite` (P4 step 5); icons and figures only at whole-number scales (§8, P4b) | — |
| U25 | Pixel fonts and sizes for headings, body and numbers | Present (conflict C6) | Style guide §3: the scale 14–22 for words and 22–34 for Cormorant, Pixelify for numerals of 20 and up over the world, serif words by the recorded deviation; every word asked for on the scale and at 14 or more, checked on every page and in `hud.gd` (P4 step 3) | — |
| U26 | Icon rules: size, outline, shading | Present | Style guide §8 and `tools/icons/README.md`: Style A (decision 7), the allowed draw sizes, the 76 and 44 px slots; `SpriteCache.draw_icon` draws only whole-number scales, checked by the `ui_suite` (P4b) | — |
| U27 | Button states and a minimum touch target | Present | Style guide §6 and §7: normal, pressed (only under the finger), selected, disabled, with option C's inked primary labels (decision 10); 48 px targets on every page (`Page.MIN_TAP`) and on the HUD (`hud.gd hit_targets`, nearest centre wins), checked by the `ui_suite` and the `hud_suite` (P4a, P4 steps 6 and 7) | — |
| U28 | The final HUD spec with the minimap | Present | Style guide §9 from mockups 01 and 02 (no portrait roundel, decision 6); the P4 parts applied (bar labels, "a / b", the plate, the log, targets); **built in P5a** (§9 "As built"): the two rings and the fan, rest and fight, the party chips, the Hollowing meter, the tracker's 48 px go button, the Menu seal and Mail count, the boss bar's phase notches, the progress edge's Level stops and bottleneck glow, the top centre's stack; `hud_suite` holds the cluster to the mockups' positions and the clear zone; the build beside mockups 01 and 02 in `docs/ui_p5/hud/compare_*.png` | — |
| U29 | A Godot Theme resource plan | Present (conflict C8) | Style guide §10: the `UiKit` token table (colour, type, `TEXT_ON`), `Page`'s layout constants and the two kit manifests stand in for a Theme resource, as C8 recommended | — |

#### Prioritised roadmap (UI 7)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U30 | Every change ordered by impact against effort, with files | Present | `docs/review-v12.md` (f): 17 changes ranked by impact against effort, with files and phase | P2 |

### 2.3 Totals

| Source | Present | Partial | Missing | Rows |
|---|---|---|---|---|
| Master Prompt (M1–M52) | 7 | 31 | 14 | 52 |
| UI Designer Prompt (U1–U30) | 4 | 13 | 11 | 28 (U6 and U10 are gates, not counted) |
| **Both** | **11** | **44** | **25** | **80** |

Two of the Missing rows (M43 realm renaming, U29 the Theme resource) were recommended to stay missing (§5). U29 is now
met the way C8 recommended, by the `UiKit` token table and the kit manifests (P4); the table above is the audit as first
taken.

---

## 3. Phases

Each phase ships as the other milestones do: data from `tools/data`, authority rules, UI, rules tests, a
`docs/CHANGELOG.md` entry, a commit and a push. Phases that produce documents ship the document under `docs/` with
its sources under `docs/research/`. Research that needs the web uses the deep-research skill and cites its sources
with the confidence labels `idle_gathering_research.md` uses.

| Phase | Contents | Depends on | Acceptance |
|---|---|---|---|
| **P1 · Guidance and gaps** (code, one phase) | Quest direction: the tracker names the target room and its region, the minimap frame shows a mark on the edge toward the next room on the auto-path route, and the World map highlights the target (M27). A third head marker for an NPC who has another quest after one you finished, drawn as the gold diamond with a jade ring, never by re-using the side-quest blue (M30). An `equipment` roll on the 32 loot tables without one, or an explicit `no_equipment` reason for trial puppets and event foes (M32). Phases for `the_reflection`, `elder_gu` and `hollow_behemoth` (M39, first part). A `valley_run` step that plays the training dummy and the nearest NPC together and asserts the context (M17) | V10d3 done | `rules_tests` `guidance_suite`: the marker for offered, again, ready and talk states through one quest's lifecycle; the direction mark against a known route; every normal and elite loot table rolls equipment or carries a reason (`data_validation`). `valley_run` plays the dummy beside an NPC. Full suite green |
| **P2 · Review pass** (docs and bug fixes) | The first half of the Full Review, in prompt-engineering style. (a) The new-player playthrough log, Prologue to the end of v1.2, each finding as *finding → root cause → fix → verification*, bugs fixed in code as found (M14–M20). (b) The project inventory the UI prompt asks for: systems with the player's goal, every page's regions and what they submit, the navigation map with tap counts, the art/UI inventory with its inconsistencies, one screenshot per page from `--open-page` (U1–U5). (c) Reference research: MapleStory, MapleStory M, Soul Saver, Legends of Idleon, Idle Skilling and two to four more, on HUD, hubs, themed system UIs, frames, feedback and retention psychology, with sources and a comparison table (U7–U8, M21's research, M38's research). (d) The UI review with severity and location (U11–U12). (e) The engagement plan, the psychology and feel plan and the per-system Single Player / Online note (M21, M26, M51). (f) The per-change impact-against-effort list (U30). Deliverables: `docs/review-v12.md`, `docs/research/ui_reference_notes.md`, `docs/research/retention_notes.md`, `docs/ui_inventory.md`; the SP/Online notes go into `architecture.md`'s authority table | Can start beside v1.2 Phase C; finishes after Phase E so the log covers Act III | Every finding has a fix with a test or a screenshot; no open bug list; `contract_tests` and the full suite green after the fixes; every reference claim carries a source; the inventory lists every page in `scripts/ui/pages/` and every HUD region in `hud.gd` |
| **P3 · Mockups** (gate) | Full-screen 1280×720 mockups, in the build's own fonts and kit, of: the HUD in a fight and at rest; the hub; every system page in its theme (U13–U19), including the Roll-Call and Works pages from V10; locked, unlocked, breakthrough, empty and full states. Rendered from HTML/SVG to PNG under `docs/mockups/`, two or three lines under each on the idea and the reference. Then **stop** for approval; revise until approved (U9–U10) | P2 (the review says what to fix) | The user says "approved". Nothing in `scripts/`, `art/` or `data/` changes in this phase |
| **P4 · Style guide and kit** | `docs/ui_style_guide.md`: palette roles (primary, the grade and quality tiers, positive, negative, disabled) mapped onto `UiKit` tokens and `grades.json`; the spacing grid (multiples of 8 screen px) and margins; the type scale (heading, body, label, numbers) with the serif deviation kept; icon rules written from `tools/icons`; button states; a minimum touch target of 48 screen px enforced by `Page.btn` and `Page.region` in a debug check; the HUD spec confirmed. New or changed kit assets through `tools/ui/build_ui.py` and `build_ui_hd.py`. The "Theme resource plan" is the `UiKit` token table and the two `ui_assets` manifests (conflict C8) | P3 approved | The style page names every token and asset; a `ui_suite` in `rules_tests` checks every `btn` and `region` rect on every page at its default state is at least 48 px on both sides, and that no text is drawn under `MIN_SIZE`; the kit builds byte-identical twice; screenshots of every page re-taken and compared with the mockups |
| **P5 · Themed screens** (three parts) | **P5a**: the HUD and hub to the approved mockups; the bag as a jade chest with the spatial-ring grid (U15). **P5b**: Cultivation as a realm ascent (the nineteen great realms as a pagoda or stair, sub-levels as steps, the bottleneck at the landing, breakthrough shown on the ascent) with the meridian diagram on Foundation (U14); Techniques as a constellation with paths, locked and lit nodes and path glow, with the Dao and sect trees drawn the same way (U13). **P5c**: your sect as a courtyard with disciple positions and the buildings drawn where they stand (U16); Spirit Animals as a bestiary scroll with the stable (U17); the map's and furnace's polish to the guide. Each part follows U20's shape: concept, wireframe, states, navigation, annotated mockup, implementation notes naming the page file and `UiKit` calls. **Started** (decision 14, `docs/page_identity.md`): the foundation that lets a page take its own identity (§8) and the Character page as the jade-slip record; the Bag waits on decision 15's concepts | P4 | Every changed page: screenshot matches its mockup; `ui_suite` still passes; the pages' regions still submit the same intents (a `contract_tests` check that no intent type disappears); `valley_run` and `prologue_run` unchanged. Tap counts to each system no higher than the navigation map's target |
| **P6 · Moments** (the animation system) | `data/moments.json` from `tools/data/moments.py`: one row per moment kind (minor breakthrough, major breakthrough, realm phenomenon, boss intro, boss phase, story beat, rare drop, title earned, craft mastery), each with its trigger event, duration, layers (screen flash, banner, camera, FX kinds, sound) and art requirements. A `MomentView` in `scripts/presentation/` that plays rows from events; `world.gd`'s hard-coded `fx.add` calls for those events move to rows (M5–M9). The VFX escalation curve: a `vfx_tier` per technique by realm band in `techniques.json`, with hit sparks, ring size, number size and shake scaled by tier; multi-hit numbers; a loot fountain on boss and chest drops; the breakthrough fanfare (M22–M25). Moments use overlays and `fx_layer` kinds only; any new body pose follows `AGENTS.md` | P4 (the style) | `moments_suite`: every row's trigger is an event in `data/event_contract.json`; a moment plays and ends on time headlessly; the escalation numbers are monotone in tier; `perf_tests` stays within budget with a moment and a swarm on screen; settings still turn shake and numbers off |
| **P7 · Wikis and volume** (two parts) | **P7a**: `tools/dev/wiki.py` writes `docs/wiki/items.md` and `docs/wiki/monsters.md` from `data/` (every item with icon, slot or type, stats or effect, grade, requirement, sources found by scanning loot tables, recipes, shops and quest rewards; every enemy with sheet, region, level band, stats, behaviour and full drop table with rates), regenerated by `build_data.py`; a `data_validation` rule that every item has a source or a `source: story` mark (M13, M36, M37). **P7b**: the item and archetype plan: a target per zone of named gear and sets per archetype (body cultivator, sword Dao, alchemist, beast tamer, formation master, musician), element and path tags on gear, new sets, with drop rates rebalanced by grade and tier and a `balance_sim` drop check (M10–M12, M33); the sprite gap list per region with the enemy diversity backlog for the art pipelines (M34–M35) | P2 (the review's counts); P7b before v1.3 so its content is authored to the target | The wikis rebuild byte-identical; `data_validation` green with every item sourced; the plan names counts per zone; `balance_sim` reports gear per hour of hunting per grade within the targets |
| **P8 · Soul Bands** (the soul-ring adaptation; design now, build with v1.3) | **P8a** (design): `docs/research/soul_band_research.md` on the Douluo Dalu soul-ring system only (how rings are won from spirit beasts, age tiers to colour and power, ring abilities, absorption limits and risks, progression), and `docs/soul_bands_design.md` adapting it under Jade River's own name (**Soul Bands**, the name the user chose; conflict C5): a cultivator wins a band from a beast of a given rank (`beast_rank` 1–9 stands in for age), bands are worn as rings of light about the body with a colour per rank, each gives one beast art, the number of bands is capped by realm, absorbing above one's realm risks Qi Deviation, and the unlock sits at Spirit Awakening 1 with the Soul bar (the band is soul-bound). Interactions with cores, pets, Bestiary Leaves and S48 paths written as rules. **P8b** (build, inside v1.3): data, `BandRules`, the authority (Field or Pet), the Cultivation page's band ring on the ascent, the Codex's band tiers, quests | P8a after P2; P8b inside v1.3 | The design page follows `idle_gathering_design.md`'s shape (names table, loop, rules with worked examples, architecture, calibration); `band_suite` checks the cap, the risk and the arts; `valley_run` wins a first band |
| **P9 · Bosses** | From the P2 research: a per-boss redesign of the eleven bosses and v1.2's three (phases, telegraphs with ground markers, arena mechanics that demand movement, enrage timers, reward loops with a re-run reason), using P6's intros and phase cards (M38–M40). Written first as `docs/boss_design.md`, then built boss by boss | P6 | Every boss has at least two phases and one telegraphed arena mechanic; a `boss_suite` in `rules_tests` plays each boss headlessly to its last phase; `valley_run`'s boss chapters still pass |
| **P10 · World plan and terminology** | `docs/world_plan.md`: rooms per region, biomes, hidden maps and travel for v1.3 Star Frontier, v1.4 Outer Heavens and v1.5 World Genesis, with cross-links that give two routes through each act (M2, M4). The xianxia text sweep over `data/strings/en.json`, dialogue and codex entries, player-facing only (M44). The cultivation loop spec as a page in `docs/` (M45–M48) with the Early / Middle / Late / Peak labels shown on the ascent as bands of the nine sub-levels (conflict C3). The realm names stay; a Codex entry gives the old scrolls' names for each great realm (conflict C1) | P2 | The plan gives a room count and a biome per region; the sweep's diff touches strings only; `contract_tests` (strings) green; the loop spec matches `ProgressionRules` line by line |
| **P12 · Might** (stat scaling) | From `docs/research/stat_scaling_research.md` §6: a Might multiplier per great realm, major breakthrough and Level on the player's attacks, HP and defences and on every monster of the same Level; the par character; monster HP, attack and boss HP set from par; one additive damage bucket and a short list of final multipliers; the energy multiplier folded into a Qi edge; `UiKit.short` for large numbers; a Level floor on every chapter's main quests; a save migration; valley_run's labelled par-up shortcut and regenerated checkpoints | P7b part 1 | A par character hits about 136K at Level 99 and 600K at Level 120; the new `balance_sim` checks and `might_suite` green; every chapter has a floor; old saves load with HP kept as a fraction. **Built** (CHANGELOG "P12 · Might"; what differs in the research's §6.8): the par character built with the real rules hits 130K at Level 99 (531K with its main art) and the table gives 571K at 120; the ten checks and `might_suite` green; chapters 2–22 have floors; the migration keeps health's share |
| **P13 · Techniques at scale** | From `docs/technique_plan.md`: eleven element trees (16 weapon-family sectors × 13 grade rings), the FORM × FAMILY × ELEMENT × PATH × RING grammar with generated names and run-time composed Style A emblems, 244 hand-made keystones, about 114 Lost Arts, Realisations as the one tree currency, the per-element tabs and the Lost Arts board (mockups 06); about 1,770 arts in v1.2.x, the rest with v1.3–v1.5 | P12 | Every family and path has hundreds of arts; names unique and checked against the denylist; the loadout limits hold the balance targets of the stat research. **P13a built** (the data; CHANGELOG "P13a · Techniques at scale, the data"; `docs/technique_plan.md` "As built"): 3,171 arts, 1,773 of them on the v1.2.x trees (1,661 in the cells of Acts I–III and 112 keystones), 38 Dao arts, 62 lost arts found only in the world (decision 19: counted, never described), the later acts' 1,308 written and locked; 138 own arts a family and 149–162 a path in Acts I–III; the trees, Realisations, respec, the heavy-art cap and the save migration in the rules; the par main art on the plan's line within ±7% (Level 200 +10%); every emblem composed from one atlas. **P13b built** (the page; CHANGELOG "P13b · The Techniques page"; `docs/technique_plan.md` "As built: P13b"; screenshots `docs/ui_p5/techniques/`): one whole tree a tab, dragged along, the chooser jumping to a family and Learned to the next learned art, only what is in view drawn; Learn naming the Realisations it spends; the Dao bar following the tab; the Lost Arts album with Read for a manual carried and every unfound art only counted; the Inner Arts and stances in the dock's drawer. Later: each tab's own projection, zoom, the minimap and the path chips |
| **P14 · Cast poses** (after the technique animations, decision 23) | Three body poses the form sheets now borrow from: a **dive** (weapon down, body tucked) for Plunge, which plays `jump` today; a **held guard** for Counter and Ward, which play a cut under the parry flash or the dome; a **palm-out cast** for the Qi forms (Pillar, Burst, Seal, Chorus, Snare), which play the family's first combo cut. Per `AGENTS.md`: each drawn on the unclothed body first and reviewed, then on every hair, shirt, pants, shoes and weapon layer, both facings, every dye; then `tools/data/technique_anim.py` maps the forms to them. | The technique animations | Every form plays a pose drawn for it; the compatibility gallery inspected; the animation contract passes. |
| **P11 · QA pass 2 and the Full Review** | The second playthrough after P1–P10; every bug fixed; the Full Review Document compiled from P2's sections plus the world, item, boss, theming and loop sections; the per-system SP/Online split completed; this roadmap updated (M49–M52) | Everything above | No open bug list; the full suite green; the review's every recommendation is a row in this page or in `v2_audit.md` |

---

## 4. Where the phases sit

The existing order is: V10d2 (in progress) → V10d3 (a thirty-day balance run) → v1.2 Phases C, D, E → v1.3 Star
Frontier → v1.4 Outer Heavens → v1.5 World Genesis → possibly v2.0 Online. The recommended order with the new phases:

| Order | Milestone | Why here |
|---|---|---|
| 1 | V10d2, V10d3 | In progress; unchanged |
| 2 | **P1 · Guidance and gaps** | One short code phase that every player feels (where to go next) and that closes the three data gaps found in this audit. It touches `hud.gd`, `npc_view.gd`, `quest_authority.gd` and loot tables, none of which v1.2 C depends on |
| 3 | v1.2 Phase C, D, E | Act III keeps moving. **P2** runs beside C–E as document work, and its bug fixes land as they are found |
| 4 | **P2 · Review pass** (finishes) | Its playthrough must cover chapters 20–22, so it closes after E |
| 5 | **P3 · Mockups** | The gate. It needs P2's review to know what to fix, and Act III's pages (Presence, the Sphere, the Roll-Call) must exist to be drawn |
| 6 | **P4 · Style guide and kit** | First after approval: every later screen is built on it |
| 7 | **P5 · Themed screens** | The restyle, in three parts, HUD and hub first (the most seen for the least work) |
| 8 | **P6 · Moments** | Presentation work that belongs with the restyle and is needed by P9 |
| 9 | **P9 · Bosses** | Before v1.3 so its bosses are built to the new standard; after P6 for the intros |
| 10 | **P7 · Wikis and volume**, **P10 · World plan and terminology**, **P8a · Soul Bands design** | Data and document work that can run in parallel with P5–P9 and must finish before v1.3's content is authored |
| 11 | v1.3 Star Frontier, with **P8b · Soul Bands** built inside it | A new zone is where a new headline system unlocks best; its beasts get band ranks from the start and the earlier zones' `beast_rank` values are already in the data |
| 12 | **P11 · QA pass 2 and the Full Review** | After the restyle and v1.3, before v1.4, so the review covers the game as it will look |
| 13 | v1.4, v1.5, v2.0 | The SP/Online notes from P2 and P11 feed v2.0 |

Why the UI phases wait for Act III to finish: the restyle touches all 44 pages, the shell screens and the HUD, the mockups must include
Act III's pages, and Phase C–E's own new pages would otherwise be built twice. Why P1 does not wait: it is small and
has no design dependency. If Act III slips, P2's research and inventory can still run, since they change no code.

An alternative order, if the look matters more than Act III right now: P2 → P3 → P4 → P5a after V10d3, then v1.2
C–E on the new kit, then P5b–c. Its cost is that Phase C–E pages would be designed before their mockups exist.

---

## 5. Conflicts and recommended resolutions

| # | Conflict | Recommendation |
|---|---|---|
| C1 | Master 9 renames the realms to the common xianxia ladder (Qi Refining, Foundation Establishment, Golden Core, Nascent Soul, …). Build Prompt v2 and every design page use Jade River's own nineteen great realms, in 89+ stage rows, 210 quests, the strings, the docs and the tests; and the working rule is that names are the game's own | Keep the names. Add one Codex entry per great realm giving "the names the old scrolls use" so a reader of other xianxia recognises the rung (Qi Kindling ≈ Qi Refining, Heart Tempering ≈ Foundation Establishment, Cloud Stride and Spirit Awakening ≈ Golden Core, Heaven Glimpse ≈ Nascent Soul, and so on). Do not rename data, strings or docs (P10). Confirmed by the user |
| C2 | Master 9 asks to shift everything wuxia-leaning toward xianxia; `README.md` calls the game wuxia/xianxia and two art atlases carry `wuxia-` names | Sweep player-facing text only (strings, dialogue, codex). Leave file names, the README's genre line and the art prompts; the world is already immortal cultivation (P10) |
| C3 | Master 10 names four stages (Early / Middle / Late / Peak) per realm; the build has up to nine sub-levels per realm, each with a bottleneck, and v2's ladder depends on them | Keep the nine sub-levels. Show the four words as bands on the cultivation ascent (1–3 Early, 4–6 Middle, 7–8 Late, 9 Peak) and in the realm label where room allows; no data change (P5b, P10) |
| C4 | Master 10 says a minor breakthrough "normally uses a stage-appropriate pill"; the build's minor breakthrough is a free tap at the bottleneck, with pills and supports raising odds and marks | Keep the tap: an idle game must not stall a character on a consumable. Where the loop spec wants a pill, the stage requirement rows already exist (`qi_refining_pill` at Qi Kindling) and can be added per stage in data (P10) |
| C5 | Master 8 asks for the Douluo Dalu soul-ring system; the rule is never to copy another work's names or content | Adapt the mechanics under an original name (Soul Bands, the user's choice), with Jade River's own colours per rank, arts and lore; the research page cites the source, the game never does (P8) |
| C6 | UI 6 asks for pixel fonts; the build sets words in Source Serif 4 and Cormorant Garamond by a recorded deviation (players could not read the style guide's hairlines on a phone) and keeps Pixelify Sans for numbers | Keep the serif words and the pixel numbers. The mockups (P3) use the build's fonts so approval is of what will ship (P4) |
| C7 | UI's "keep everything true to pixel art" against the HD kit, which is anti-aliased and analytic so frames stay sharp at 1.5–3× phone scales | Keep the HD kit for frames and the pixel kit's motifs inside it; icons, sprites and numbers stay pixel. Write the rule down in the style guide (P4) |
| C8 | UI 5 and 6 ask for Control node trees, NinePatchRect and a Godot Theme resource; the build's pages are immediate-mode `Page` subclasses with `UiKit` tokens and nine-slice StyleBoxes from `data/ui_assets.json` and `HdStyleBox` | Keep the page model; it is what the tests drive headlessly and what the intent contract checks. The "Theme resource plan" becomes the `UiKit` token table and the manifests; implementation notes name page files, region ids and `UiKit` calls instead of node paths (P4, P5) |
| C9 | The UI prompt says the Sect unlocks after more than three characters; the build unlocks it at account realm Qi Unfurling 1, which is also slot 4's gate | The project is the source of truth, as the prompt itself says. No change; the inventory (P2) records the real gate |
| C10 | The UI prompt forbids modifying project files before approval; the Master prompt says fix bugs in code as found | Bugs are fixed in code at once (P1, P2). Design changes, kit changes and restyles wait for the P3 approval (P4 onward) |
| C11 | Master 1 and 4 want screen-filling animations and new animation types; `AGENTS.md` requires every new body animation to be drawn on every layer, dye and facing before it is enabled | Moments are overlays, FX kinds, camera and sound (P6). Any new body pose (a breakthrough stance, a boss roar) goes through `AGENTS.md`'s full review or is not added |
| C12 | Master 2 derives an item count from MapleStory (thousands of items); Jade River's gear is banded and procedural, and its pixel pipelines draw every piece in every pose | Set the target as named gear and sets per archetype and zone, not a raw count (P7b). The wiki (P7a) counts what exists honestly, bands included |
| C13 | Master 5's second `!` colour (a repeat NPC) against the build's use of colour for main against side | A third marker state with its own drawing (the gold diamond with a jade ring), leaving gold and blue as they are (P1) |
| C14 | Master 5's arrow or minimap marker against v2's S24 HUD layout, which is audited and has no free slot for a new button | No new button. The direction mark sits on the minimap's frame edge and the tracker names the target; the auto-path button stays where V8g1 put it (P1) |
| C15 | The UI prompt's Phase 3 stop and Phase 1 stop are human gates; an agent cannot approve its own mockups | The phases keep the gates (P2's questions, P3's approval). The user, not the builder, says "approved" |
| C16 | Both prompts ask for web research (MapleStory, Idleon, Douluo Dalu, Soul Saver, retention psychology); the build's research so far is one page | Research pages go under `docs/research/` with sources and confidence labels, written by the deep-research skill; the game itself never names a reference |

---

## 6. Decisions (the user, 2026-09-26)

1. **Realm names** (C1): keep Jade River's ladder; add the Codex cross-reference to the old scrolls' names (P10).
2. **The soul-ring adaptation** (C5): named **Soul Bands**, unlocked at **Spirit Awakening 1** with the Soul bar (P8).
3. **The UI restyle** (§4): starts after Act III, in the recommended order.
4. **Mockup approval** (C15): the user approves; the mockups are sent to the user as PNGs in the conversation, and
   kept under `docs/mockups/`.
5. **The item target** (C12): named gear and sets per archetype and zone (P7b).

6. **The first mockups** (2026-09-26, P3): 00–05 approved, with two notes:
   - Remove the portrait roundel with the initial ("T") left of the HP and Qi bars. Done in the HUD and in mockups 01
     and 02: the name, realm and bars take the panel's width; the bottleneck shows on the Stored Qi edge.
   - The icons across the whole game must look better. A style study goes to the user first (a before-and-after sheet
     of representative icons in the proposed style); once it is approved, every icon family is redrawn to it (P4b).

7. **The icon style** (2026-09-27, P4b): **Style A, "HD pixel"**, from the study in `docs/mockups/icon_study/`. It uses 64
   art px shown 1:1 on pages and 32 px HUD glyphs, with native 48 and 32 re-renders for the HUD rings. It has
   seven-step material ramps, a selective outline, one light from the top-left with a rim on metal, glass and jade, and
   grade shown by material and stepped glow. Page slots become 76 px so the icon shows 1:1 (I2). Every family is redrawn
   through the study's pipeline, family by family, each sheet going to the user.
8. **Equipment on the character** (2026-09-27, P5a): the Bag and Character pages show the character's full figure
   wearing the equipped pieces, drawn from the real sprite layers, with the slots around it. A row of slots with no
   figure is not enough.
9. **The version** (2026-09-27): the game and the APK both show 1.2, from `project.godot` (B9).
10. **The primary button** (2026-09-27, P4): option C of `docs/mockups/00b_button_faces.png`. The bright jade face
    stays; primary labels and page titles carry a 2 px ink outline (`docs/ui_style_guide.md` §1.5).
11. **Mockup notes** (2026-09-27, P3):
    - Roll-Call (13) should look more interactive and friendlier.
    - The world map (16) takes after the user's reference: a painted landscape of the zone with its landmarks drawn,
      glowing nodes on a dotted route, and a side card with the area's picture, level band, resources and "Track
      Route". Tabs sit along the foot (Areas, Resources, Objectives) with a legend. The names stay Jade River's own.
    - The shop (17) drops the buy-back column, so the bag side has room; buy-back becomes a small control.
    - The Codex Collection (18) should read as a book, and the Old Scrolls tab should look like nothing else in the
      game.
    - Techniques (06): a large tree per element, each element in its own tab, plus a tab for lost arts found only
      through quests, drops and exploration.
12. **Technique volume** (2026-09-27): hundreds of techniques for each weapon family and each cultivation path, planned
    in `docs/technique_plan.md` before they are built.
13. **Stat scaling** (2026-09-27): research how 2D MMORPGs scale stats and gate main quests by level, compared with
    Jade River's curves. A high-level character should deal hundreds of thousands of damage
    (`docs/research/stat_scaling_research.md`).
14. **Every page its own** (2026-09-27, P5): each page is a thing from the world with its own concept, material and
    layout signature (the Codex a book, the map a painted landscape, and so on); no two pages share one. Only the
    close button, primary buttons, text tokens, the type scale and 48 px targets stay shared. Catalogued in
    `docs/page_identity.md`.
15. **The Bag** (2026-09-27): no gourd drawing. The inventory must feel like a big space, with a small information
    card for a chosen item instead of a large detail panel. New concepts go to the user before the Bag is built.
16. **Character titles** (2026-09-27): the titles on the Overview look and feel more fancy (each a named honour, not
    a plain row).
17. **World map text** never overlaps: name plates, levels, boss and event marks are placed so no two touch.
18. **Techniques pages** (2026-09-27): styled after the user's skill-tree reference (a central tree of illustrated
    node cards joined by arrows, each with its status; a selector panel with mastery bars and the character; a detail
    panel with a large illustration, prerequisites with ticks and crosses, the cost and Learn; the equipped bar along
    the foot). Inspiration only, nothing copied.
19. **Secret and lost techniques** are unknown until found: no hints, no sources, no silhouettes that tell where they
    are; a found art appears, the rest are counted, not described.
20. **The HUD's system toggles fold into the fan** (P5a). Built: the fan opens and closes with a tap, shows the toggles
    that are on pinned beside it while closed, folds in a fight and opens again at rest as the player left it.
21. **Works and posts icons** are drawn better (P4b and P5).
22. **The Calendar** keeps the first mockup (19), not the almanac (19 v2).
23. **Skills have proper animations**: every technique form has its own animated effect, on the existing body poses
    (`AGENTS.md`).
24. **The Bag is concept B** (mockups `07_bag_b`, `07_bag_b_card`, `07_bag_b_pill`, `08_bag_b_empty`): the worn figure
    beside one wide grid, and the small item card. A and C stay as the record.
25. **The world map mockup is approved** (`16_world_map`, `16_world_map_resources`) and is built as drawn.
26. **Works: the Seal Scripts section is bigger** (`14_works_v4`): more rows show at once, the shelf gives it room.
27. **Codex page-completion rewards** (2026-09-27, mockup 18's two seals). Every collection page has two seals. Seal I:
    every card on the page filled (50 defeated). Seal II: every card studied through, 500 for a common beast, 200 for an
    elite and 100 for a boss (`kills_to_master` in `enemies.json`), claimed after seal I. The Account authority owns
    them: a seal is earned the kill its condition first holds (a toast says so), claimed once for the account by the
    intent `claim_collection_seal` (Claim on the book page, which stamps it) and saved (`collection_seals`). Each gift
    is small and permanent, kept by every character through the stat rules (source `collection:`): seal I one
    defensive or finding stat (Hollow Ward +2%, tenacity +1%, max HP +1%, drop rate +1%, coin find +2%), seal II
    healing received +1%, knockback resistance +5% or mastery gain +2%, and a Bestiary Leaf of one of the page's beasts.
    No attack or damage stat; each stat's sum over the book has a budget in `account_rules.json`
    (`collection_seals`), and `balance_sim` holds every seal together under +3% of the par character's Combat Power
    (about +0.6% at Level 99).
28. **The top-down redesign keeps a Jump button** (2026-09-27, `docs/redesign_top_down_plan.md` §6 item 1). Touch
    keeps the joystick, Jump, Dodge/Guard and Attack as now. Auto-hop off ledges at speed and the dash-jump over gaps
    may stay as extras, but jumping is always on the button. Phase 1's prototype room is built to it (the plan's "As
    built: Phase 1").

29. **Top-down movement (Phase 1 review):** the dash cooldown (2.5 s) stays; walking stops at the water's edge (walking on water
    comes from a special skill); the player can jump off rooftops (roofs are standable height levels).
31. **Top-down art style:** the map, terrain and world are drawn in a style close to Alabaster Dawn's (bright, detailed ¾
    top-down pixel art with clear height levels, soft shading and lush tiles), but the theme stays xianxia: Jade River's
    own places, palette and motifs (river towns, terraces, pagodas, lotus, mist, jade). Inspiration only: original art, no
    copied tiles, sprites or names.
Still open: where the Full Review lives. The default is one page, `docs/review-v12.md`, growing through P11.
