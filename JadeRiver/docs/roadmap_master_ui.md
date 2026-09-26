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
| M2 | More than one viable route through the world | Partial | Regions cross-link and the World map draws routes between them (`map_page.gd:75-81`), but each act's regions are ordered by Storm Ward / Starsea Endurance bands (`act2_design.md`, `act3_design.md`), so the order of regions inside an act is fixed even where the rooms are not | P10 |
| M3 | Hidden and optional maps that reward exploration | Present | 9 `secret` rooms (`ds_drowned_grotto`, `cf_behind_falls`, `bm_smugglers_cove`, …), 7 hidden portals from Spirit Awakening 2 (`unlocks.json` `hidden_portals`), 4 hidden regions, and the S43 optional ledges counted on the Codex's Paths Above tab (`map_page.gd:170`) | — |
| M4 | A world-expansion plan: maps per region, biomes, connections, hidden maps | Partial | `act2_design.md` and `act3_design.md` give rooms per region for Acts II–III. No plan exists for v1.3 Star Frontier, v1.4 Outer Heavens or v1.5 World Genesis; the room catalogue (`tools/data/catalogue.py`) covers the valley only | P10 |
| M5 | On-screen animation for realm breakthroughs | Partial | A flash and the `breakthrough` sound (`world.gd:458-462`), the heavens' storm for a phenomenon with NPC reactions (`world.gd:589-594`, S49), `breakthrough_failed` text. No full-screen sequence, no data-driven trigger and duration | P6 |
| M6 | On-screen animation for boss intros and phases | Partial | The boss bar (`hud.gd:1857`), an "appears" toast, a shake on `boss_phase` (`world.gd:640`), captions (`hud.gd` `CAPTIONS`). No intro, no phase card | P6 |
| M7 | On-screen animation for story beats | Partial | The room banner (`hud.gd:1811`), the fortune card (`hud.gd:1818`), set pieces as room events (`set_pieces.json`, `quest_authority.gd:522`). No cutscene layer (no letterbox, camera move or scripted staging) | P6 |
| M8 | On-screen animation for rare drops | Partial | Ground loot bounces and glows by quality (`loot_view.gd:3`), rare-pill toasts (`hud.gd:795`). No rare-drop flourish or fountain | P6 |
| M9 | A catalogue of animation types with trigger, duration and art requirements | Missing | Effects are hard-coded `fx.add(kind, …)` calls in `world.gd` (`flash`, `ring`, `wave`, `spark`, `motes`, `pill_cloud`, `heaven_storm`, …) | P6 |

#### Item economy and build diversity (Master 2)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M10 | A researched item-count target | Missing | No research page on item counts. The build has 454 defined items (`data/items.json`: 58 tools, 46 beast parts, 44 materials, 44 cores, 32 pills, 27 legend pieces, …) and generates gear by band instead of naming it (13 grade bands in `data/stats.json` `grade_bands`, slot shares, 16 affixes in `data/affixes.json`) | P7 |
| M11 | Items organised by slot, rarity, realm, element, path synergy and set | Partial | Grades and bands, item levels, affixes, weapon families, three sockets on Sage gear, five sets (`data/sets.json`: `jade_current`, `cloudpiercing`, `mudwater`, `drowned_abbot`, `crane`). No element or path tag on gear; five sets for three zones | P7 |
| M12 | Distinct build archetypes each with a full gear path | Partial | The archetypes exist as systems (S48 paths, the body ladder, ten weapon families, the Alchemy and Beast Taming Daos), but gear is the same banded set for everyone; only the legendary chains (`legendary_chains.json`) are family-specific | P7 |
| M13 | An Item Wiki, one entry per item (icon, slot, stats, rarity, requirement, sources, lore) | Missing | No wiki page. The in-game Codex Collection tab (`codex_page.gd`) lists items found; `desc` lines exist on items but no source list | P7 |

#### Player-experience playthrough (Master 3)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M14 | A new-player playthrough log, start to current end | Partial | `prologue_run` and `valley_run` play the Prologue to Act III chapter 19 headlessly with checkpoints; `docs/review-v08.md`, `review-v09.md`, `review-v13.md` review movement and art. No narrative UX log | P2 |
| M15 | UI friction, unclear feedback, confusing menus logged and fixed | Missing | No UI review exists (the reviews above are movement and art) | P2 |
| M16 | Collision problems, invisible walls and terrain snags | Partial | The movement suites (`tests/movement_v07.gd`, `landing_matrix.gd`, `room_gates.gd`, `obstacle_review.gd`) and the room lint cover reach and gates; a play-through pass has not been logged | P2 |
| M17 | Interaction conflicts (the training dummy answering as talk; conversations forced closed by hand) | Partial | One context per frame from `WorldAuthority.query_context` (`world.gd:_update_context`); the attack button is separate from the context button, and the dummy answers blows (`progression_authority.gd:1027`). A conversation closes itself when its last line ends with no choices, and after an accept or hand-in with only a farewell left (`dialogue_page.gd:99-146`). The dummy case must still be played to confirm | P2 |
| M18 | Overlapping objects that block interaction | Partial | The world builder keeps spawns clear of shrines and portals (`architecture.md` Data builders); nothing checks objects against each other | P2 |
| M19 | Houses and shops with no visible door | Present | Doors are portals of kind `door` (96) drawn with a plate and an arrow, and interior doors stand on the back wall (`portal_view.gd:4-54`) | — |
| M20 | Quest flow gaps, dead ends, missing guidance | Partial | `story.py` validates quests, NPCs and unlocks; V9f3 fixed one quest that could never start; `valley_run` checkpoints each chapter. A guidance review from the player's side is not done | P2 |
| M21 | Long-term engagement: daily reasons to log in, social loops, "one more level" | Partial | Daily missions, four activity chests, the weekly mission, the calendar's events and seasons, the Saturday auction, the weekly Beast Tide, the Trial Tower's daily sweep, the Heaven Ranking, county jobs, Keeping Post's daily round. No written retention plan, and no social loop until v2.0 Online | P2 |

#### Game psychology and sensory design (Master 4)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M22 | A skill-VFX escalation curve per realm | Missing | `data/techniques.json` has no vfx field (48 techniques); 34 hit one target, 7 hit 2–5. Effects are the generic kinds in `fx_layer.gd` | P6 |
| M23 | Multi-hit numbers, particles and screen shake | Partial | Damage numbers with crits larger and gold (`fx_layer.gd:24`), screen shake on heavy hits, crits and boss phases with a settings toggle (`world.gd:304-307, 413-414`), hit-stop 0.05 s / 0.08 s on crit (`combat_authority.gd:325, 1053`), the heavy sabre's cleave and the 36-sword swarm. No screen-filling effects; particles are eight sparks | P6 |
| M24 | Colour psychology: rarity coding, damage-number colours, biome palettes | Partial | 10 grade colours and 12 quality colours (`data/grades.json` → `UiKit.grade_color`); crit gold, Soul violet, Qi teal numbers (`fx_layer.gd:3-4`); a backdrop set per region. No written palette rule for biomes or a check that the colours read on a phone | P4 |
| M25 | Feedback loops: hit-stop, sound, knockback, loot fountains, level-up fanfare | Partial | Hit-stop, `Audio`, per-attack `knockback`, loot that bounces and glows. No loot fountain or fanfare sequence; a breakthrough is a flash and a sound | P6 |
| M26 | An implementation plan for each finding | Missing | — | P2 |

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
| M33 | Drop rates balanced by rarity and tier | Partial | `LootRules` and per-table chances; no documented balance pass and no `balance_sim` check on drops | P7 |
| M34 | A sprite audit of NPCs, equipment, terrain and monsters | Partial | 68 creature sheets for 111 enemies (`data/creature_art.json`), 749 icons, `docs/art-contracts.md`, the animation contract tests and the compatibility gallery. No gap list | P7 |
| M35 | Enemy sprite diversity per region | Partial | Eleven Act III sheets drawn ahead (CHANGELOG 1.2 A); many valley foes share a sheet with a dye. A per-region count is not written | P7 |
| M36 | A Monster & Drops Wiki | Missing | The in-game Collection tab shows found beasts (`enemies.json` `collection`); no page with full drop tables | P7 |
| M37 | Every item has a source; every monster is in the wiki with its drops | Partial | `data_validation` checks references exist; it does not check that every item is reachable from a drop, recipe, shop or quest | P7 |

#### Boss design (Master 7)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M38 | Research on MapleStory and Idleon boss fights | Missing | No research page | P9 |
| M39 | Phases, telegraphs, arena mechanics, enrage and reward loops on every boss | Partial | 11 bosses; 8 have `phases` (a summon at 60 %, enrage at 30 %), every attack has `windup_s` / `active_s` / `recover_s` and a "!" tell (`enemy_view.gd:178`), ground markers on the bombard and broadsides, Presence and Sphere clashes (v1.2). `the_reflection`, `elder_gu` and `hollow_behemoth` have no phases; no boss demands movement by arena geometry | P1, P9 |
| M40 | Re-runnable boss rewards | Partial | Dungeon keys, field boss timers, the Trial Tower and Beast Kings; no per-boss reward loop | P9 |

#### Soul Rings (Master 8)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M41 | A research page on the Douluo Dalu soul-ring system | Missing | — | P8 |
| M42 | An adapted system in Jade River's world | Missing | Nothing like it. Adjacent pieces to build on: `beast_rank` 1–9 on every enemy, 44 core items and the Core Exchange, pets devouring cores (`pet_authority.gd:556`), Bestiary Leaves per species (V10b), Beast Kings | P8 |

#### Theming and realm naming (Master 9)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M43 | Realms renamed to Qi Refining, Foundation Establishment, Golden Core, Nascent Soul, … | Missing (deliberately; conflict C1) | 19 great realms with Jade River's own names, Mortal → Bone Forging → Qi Kindling → Qi Unfurling → Heart Tempering → Cloud Stride → Spirit Awakening → Heaven Glimpse → Sage → Sage Sovereign → Will Manifest → Sphere Lord → Law Touching → … → World Genesis (`data/realms.json`), used by quests, strings, docs and Build Prompt v2 | P10 |
| M44 | Everything wuxia-leaning shifted toward xianxia | Partial | The world is already immortal cultivation (Qi, realms, tribulations, sects, Daos, heavens, lifespans); `README.md` calls it "wuxia/xianxia" and two atlases are named `wuxia-props-v4.png` and `wuxia-buildings-v4.png`. No text sweep has been done | P10 |

#### The core cultivation loop (Master 10)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M45 | Cultivate converts time into Qi; Qi-rich places are more efficient | Present | `ProgressionRules.meditation_rate` × the room's `qi_density`, Qi springs, ambient Qi, seclusion with its 12-hour cap | — |
| M46 | Stages Early / Middle / Late / Peak with a bottleneck at each | Partial (conflict C3) | Each great realm has up to nine sub-levels, each ending in a bottleneck ("tap Cultivate to break", `hud.gd:720`), with the Stored Qi cap. There are no four named stages | P10 |
| M47 | Minor breakthroughs use a stage pill by default, other resources sometimes | Partial (conflict C4) | A minor breakthrough is a tap at the bottleneck; pills, support pills and vessels raise the odds and add marks; some stages ask for an item (`qi_refining_pill` at `realms.json:758`) | P10 |
| M48 | Major breakthroughs: elixir, materials, sometimes a trial; quality affects success and stats | Present | `major_breakthrough.requirements` per realm (pills, body level, methods, the Heart Trial, Heaven's Cleansing, Core Forging), the risk index and success chance, pill marks +2 % each, the Core Forging grade and heavenly tribulation (S48) | — |

#### QA pass 2 and the Full Review (Master 11)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| M49 | A second full QA pass with every bug fixed | Missing | — | P11 |
| M50 | The Full Review Document (all sections, prompt-engineering style, no open bug list) | Missing | — | P2, P11 |
| M51 | Every system split into Single Player and Online tracks | Partial | `architecture.md` "Extension contract" and "Explicitly not implemented" describe the server boundary once for movement and once for the rest; not per system | P2, P11 |
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
| U1 | Every system: purpose, the player's goal, data and progression, connections | Partial | `architecture.md` lists the authorities and what they own; `README.md` the content. Nothing states the player's goal per system | P2 |
| U2 | Every screen's elements and what they do, with paths | Missing | 44 pages in `scripts/ui/pages/` plus the shell screens and the HUD, none documented. Note: pages are immediate-mode `Page` subclasses (`page.gd`: `btn`, `region`, `list`, `panel`) that draw in `_draw`; there are no Control scenes, so "scene/node path" becomes "page file and region id" | P2 |
| U3 | A navigation map with tap counts | Missing | The hub is `menu_page.gd` (21 entries, locked ones dimmed); the HUD icon row is Menu, Bag, Map, Mail (`hud.gd:42`); pages open other pages by id | P2 |
| U4 | The art/UI inventory: palette, fonts, pixel scale, inconsistencies | Partial | `tools/ui/README.md` (palette, the 20-asset kit and its nine-slice margins), `UiKit` tokens (15 colours), fonts (Cormorant Garamond for headings ≥ 22 px, Source Serif 4 for words, Pixelify Sans for numbers), two kits (the pixel kit at 2 px per art px and the HD analytic kit, `tools/ui/build_ui_hd.py`). No inconsistency list | P2 |
| U5 | Screenshots of every screen | Partial | `--open-page=<page>[:<preview>]` opens any page headlessly (`main.gd:388`), and the furnace has preview states; no captured set exists | P2 |
| U6 | Open questions, then stop | — | A human gate; §6 lists the questions | P2 |

#### Reference analysis (UI 2)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U7 | HUD, hub, themed screens, frames and feedback of each reference, with sources | Missing | `docs/research/idle_gathering_research.md` covers IdleOn's AFK mechanics, not its UI | P2 |
| U8 | A comparison table, Jade River system against its closest reference | Missing | — | P2 |

#### Mockups (UI 3)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U9 | Full-screen mockups of the HUD, the hub, every system screen and key states, in one style | Missing | The HD kit's `--review PNG` sheet shows frames, not screens | P3 |
| U10 | Approval before any spec | — | A human gate | P3 |

#### Full review (UI 4)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U11 | Problems per screen with severity and location; felt against intended | Missing | — | P2 |
| U12 | Global issues: consistency, palette, fonts, icons, scale, spacing | Missing | — | P2 |

#### Redesign every system to its theme (UI 5)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U13 | Techniques as a branching tree or constellation | Missing | `techniques_page.gd`: a list of techniques and four slots per tab (combat, Inner Arts, secret arts). The Dao tab is a list with bars (`cultivation_page.gd:315`); the sect tree is three columns of five nodes (`training_sect_page.gd:81`) | P5 |
| U14 | Cultivation as a meridian diagram or an ascent of realms | Partial | Overview with realm, progress and bottleneck; Foundation with meridians as rows and +1 buttons; the Body tab's four rungs; Heart, Paths, Methods, Dao, Seclusion tabs (`cultivation_page.gd`). No diagram or ascent | P5 |
| U15 | Inventory as a jade chest or spatial-ring grid | Partial | Paper doll, bag grid, key items, detail panel with actions (`inventory_page.gd:51-93`); slots use the kit's slot art and empty motif | P5 |
| U16 | Sect as a hall or courtyard with disciple positions | Partial | `your_sect_page.gd`: Buildings, Disciples, Expeditions, Territory tabs; the buildings themselves stand in the sect's rooms in the world as they are built (`README.md`) | P5 |
| U17 | Spirit Animals as a stable or bestiary scroll | Partial | `pets_page.gd`: Care, Growth, Fusion, Breeding, Eggs; the HUD pet strip; the Codex Collection | P5 |
| U18 | The world map as a painted ink scroll of linked rooms | Present | `map_page.gd:2`: one painted scroll per zone, regions with routes, events and boss timers, rooms on tap | — |
| U19 | Alchemy as a furnace with ingredient slots | Present | The five-screen furnace with fire and array (`crafts_page.gd:3-5`, V9e2) | — |
| U20 | Per system: concept, wireframe in px, element states, navigation and taps, annotated mockup, implementation notes | Missing | — | P5 |
| U21 | Godot notes: node tree, scenes and scripts touched, Control / NinePatchRect / Theme usage | Missing (conflict C8) | No Control trees or Theme resource: `UiKit.style()` hands nine-slice StyleBoxes from `data/ui_assets.json` and `HdStyleBox` to immediate-mode pages | P5 |

#### Style guide (UI 6)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U22 | A palette with roles (primary, rarity tiers, positive and negative, disabled) | Partial | `UiKit` constants and `grades.json` colours exist; roles are not written down, and nothing names the disabled or negative colour as such (`HOLLOW`, `RED`, `MIST` are used by convention) | P4 |
| U23 | Nine-slice panels with xianxia motifs | Present | The pixel kit (jade lines, gold and bronze trim, corner ornaments) and the HD kit (`art/ui/`, `art/ui/hd/`, 50 files) | — |
| U24 | Pixel scale, grid and spacing rules | Partial | The kit is authored at 2 screen px per art px; `Page.SAFE` and `frame_rect` fix the window; no spacing rule | P4 |
| U25 | Pixel fonts and sizes for headings, body and numbers | Partial (conflict C6) | Pixelify Sans for numbers only; serif words by deliberate deviation (`v2_audit.md` Deviations); `MIN_SIZE` 14, `DISPLAY_MIN` 22, three text sizes | P4 |
| U26 | Icon rules: size, outline, shading | Partial | 749 icons from `tools/icons`; 64 px slots, 48 px HUD; the rules live in the pipeline, not in a guide | P4 |
| U27 | Button states and a minimum touch target | Partial | `button_primary` and `button_secondary` in normal, pressed and disabled; HUD hit radii 30–74 px; no written minimum, and `btn` accepts any rect | P4 |
| U28 | The final HUD spec with the minimap | Present | v2 S24 positions in `hud.gd:25-42`, audited in `docs/v2_audit/p8_changes.md` §S24 | — |
| U29 | A Godot Theme resource plan | Missing (conflict C8) | See U21 | P4 |

#### Prioritised roadmap (UI 7)

| # | Item | Status | Evidence | Phase |
|---|---|---|---|---|
| U30 | Every change ordered by impact against effort, with files | Partial | §3 and §4 of this page order the phases; the per-change list comes out of P2 | P2 |

### 2.3 Totals

| Source | Present | Partial | Missing | Rows |
|---|---|---|---|---|
| Master Prompt (M1–M52) | 7 | 31 | 14 | 52 |
| UI Designer Prompt (U1–U30) | 4 | 13 | 11 | 28 (U6 and U10 are gates, not counted) |
| **Both** | **11** | **44** | **25** | **80** |

Two of the Missing rows (M43 realm renaming, U29 the Theme resource) are recommended to stay missing (§5).

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
| **P5 · Themed screens** (three parts) | **P5a**: the HUD and hub to the approved mockups; the bag as a jade chest with the spatial-ring grid (U15). **P5b**: Cultivation as a realm ascent (the nineteen great realms as a pagoda or stair, sub-levels as steps, the bottleneck at the landing, breakthrough shown on the ascent) with the meridian diagram on Foundation (U14); Techniques as a constellation with paths, locked and lit nodes and path glow, with the Dao and sect trees drawn the same way (U13). **P5c**: your sect as a courtyard with disciple positions and the buildings drawn where they stand (U16); Spirit Animals as a bestiary scroll with the stable (U17); the map's and furnace's polish to the guide. Each part follows U20's shape: concept, wireframe, states, navigation, annotated mockup, implementation notes naming the page file and `UiKit` calls | P4 | Every changed page: screenshot matches its mockup; `ui_suite` still passes; the pages' regions still submit the same intents (a `contract_tests` check that no intent type disappears); `valley_run` and `prologue_run` unchanged. Tap counts to each system no higher than the navigation map's target |
| **P6 · Moments** (the animation system) | `data/moments.json` from `tools/data/moments.py`: one row per moment kind (minor breakthrough, major breakthrough, realm phenomenon, boss intro, boss phase, story beat, rare drop, title earned, craft mastery), each with its trigger event, duration, layers (screen flash, banner, camera, FX kinds, sound) and art requirements. A `MomentView` in `scripts/presentation/` that plays rows from events; `world.gd`'s hard-coded `fx.add` calls for those events move to rows (M5–M9). The VFX escalation curve: a `vfx_tier` per technique by realm band in `techniques.json`, with hit sparks, ring size, number size and shake scaled by tier; multi-hit numbers; a loot fountain on boss and chest drops; the breakthrough fanfare (M22–M25). Moments use overlays and `fx_layer` kinds only; any new body pose follows `AGENTS.md` | P4 (the style) | `moments_suite`: every row's trigger is an event in `data/event_contract.json`; a moment plays and ends on time headlessly; the escalation numbers are monotone in tier; `perf_tests` stays within budget with a moment and a swarm on screen; settings still turn shake and numbers off |
| **P7 · Wikis and volume** (two parts) | **P7a**: `tools/dev/wiki.py` writes `docs/wiki/items.md` and `docs/wiki/monsters.md` from `data/` (every item with icon, slot or type, stats or effect, grade, requirement, sources found by scanning loot tables, recipes, shops and quest rewards; every enemy with sheet, region, level band, stats, behaviour and full drop table with rates), regenerated by `build_data.py`; a `data_validation` rule that every item has a source or a `source: story` mark (M13, M36, M37). **P7b**: the item and archetype plan: a target per zone of named gear and sets per archetype (body cultivator, sword Dao, alchemist, beast tamer, formation master, musician), element and path tags on gear, new sets, with drop rates rebalanced by grade and tier and a `balance_sim` drop check (M10–M12, M33); the sprite gap list per region with the enemy diversity backlog for the art pipelines (M34–M35) | P2 (the review's counts); P7b before v1.3 so its content is authored to the target | The wikis rebuild byte-identical; `data_validation` green with every item sourced; the plan names counts per zone; `balance_sim` reports gear per hour of hunting per grade within the targets |
| **P8 · Soul Bands** (the soul-ring adaptation; design now, build with v1.3) | **P8a** (design): `docs/research/soul_band_research.md` on the Douluo Dalu soul-ring system only (how rings are won from spirit beasts, age tiers to colour and power, ring abilities, absorption limits and risks, progression), and `docs/soul_bands_design.md` adapting it under Jade River's own name (**Soul Bands**, the name the user chose; conflict C5): a cultivator wins a band from a beast of a given rank (`beast_rank` 1–9 stands in for age), bands are worn as rings of light about the body with a colour per rank, each gives one beast art, the number of bands is capped by realm, absorbing above one's realm risks Qi Deviation, and the unlock sits at Spirit Awakening 1 with the Soul bar (the band is soul-bound). Interactions with cores, pets, Bestiary Leaves and S48 paths written as rules. **P8b** (build, inside v1.3): data, `BandRules`, the authority (Field or Pet), the Cultivation page's band ring on the ascent, the Codex's band tiers, quests | P8a after P2; P8b inside v1.3 | The design page follows `idle_gathering_design.md`'s shape (names table, loop, rules with worked examples, architecture, calibration); `band_suite` checks the cap, the risk and the arts; `valley_run` wins a first band |
| **P9 · Bosses** | From the P2 research: a per-boss redesign of the eleven bosses and v1.2's three (phases, telegraphs with ground markers, arena mechanics that demand movement, enrage timers, reward loops with a re-run reason), using P6's intros and phase cards (M38–M40). Written first as `docs/boss_design.md`, then built boss by boss | P6 | Every boss has at least two phases and one telegraphed arena mechanic; a `boss_suite` in `rules_tests` plays each boss headlessly to its last phase; `valley_run`'s boss chapters still pass |
| **P10 · World plan and terminology** | `docs/world_plan.md`: rooms per region, biomes, hidden maps and travel for v1.3 Star Frontier, v1.4 Outer Heavens and v1.5 World Genesis, with cross-links that give two routes through each act (M2, M4). The xianxia text sweep over `data/strings/en.json`, dialogue and codex entries, player-facing only (M44). The cultivation loop spec as a page in `docs/` (M45–M48) with the Early / Middle / Late / Peak labels shown on the ascent as bands of the nine sub-levels (conflict C3). The realm names stay; a Codex entry gives the old scrolls' names for each great realm (conflict C1) | P2 | The plan gives a room count and a biome per region; the sweep's diff touches strings only; `contract_tests` (strings) green; the loop spec matches `ProgressionRules` line by line |
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

Still open: where the Full Review lives. The default is one page, `docs/review-v12.md`, growing through P11.
