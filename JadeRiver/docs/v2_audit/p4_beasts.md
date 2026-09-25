# Audit P4 · Spirit beasts (S46 and Part 8) against the build

**Build:** `/home/user/Game/JadeRiver` at commit `796f089` ("G1 follow-up"). The CHANGELOG head is "1.1 — The Azure Expanse" with G1 and G2a done. The export preset is `1.0.0`. `docs/gap_audit.md:196` puts all pet depth in phase **G3**, and fusion, breakthroughs, command capacity and the Arena in **G6**. Neither phase has started: the CHANGELOG has no G3 or G6 entry.

**How the audit was done:** read-only. I read the code and data and ran no Godot or tests. The data generators are `tools/data/economy.py` (`pets()`, lines 368-433), `tools/data/crafts.py:64-71` (eggs, taming, defence) and `tools/data/enemies.py`. Evidence cites file:line or a data id.

**No PetState class exists.** The task brief names `scripts/simulation/state/pet_state.gd`, and that file does not exist. A pet is an untyped Dictionary in `GameCharacter.pets` (`scripts/simulation/state/game_character.gd:27`). It is created only in `PetAuthority.apply_grant` (`pet_authority.gd:88-90`) with these fields: `uid, species, name, level, xp, bond, role, stage, hunger_day, rarity, branch, traits, revealed`. It is saved as-is (`game_character.gd:58,84`), with no per-field defaults or migration.

Status meanings: **Present** means it exists and matches. **Differs** means it exists with another name, number or behaviour. **Partial** means part of it exists. **Missing** means nothing like it exists. In the stay-out table (§14), **Present** means the build keeps the staple out, as required.

---

## Status counts

| Scope | Present | Differs | Partial | Missing | Rows |
|---|---|---|---|---|---|
| Beast scope (§1–§10, §12 beast rows, §15 beast rows) | 2 | 8 | 15 | 90 | 115 |
| Cross-packet rows (§12 other rows, §13, §14, §15 other rows), indicative only | 16 | 1 | 6 | 14 | 37 |

The coverage-matrix rows in §11 repeat the §6 mechanics. They are classified there but not counted twice.

---

## 1. S46 Owns: PetState fields [state v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| A PetState with new fields [state v0.9] | Differs | No `pet_state.gd`. A pet is a Dictionary built in `pet_authority.gd:88-90` and saved raw (`game_character.gd:58,84`) | Add a PetState class (or a schema with defaults) and a save migration that fills the new fields on older pets |
| `bloodline_purity` 0–100 | Missing | Not in the pet dict. The closest thing is `rarity` (`pet_growth.json` `rarities`, 5 tiers) | Add the field. Roll it at hatch or tame from a per-rarity range in `pet_growth.json` |
| `growth` 0.8–1.3 | Missing | Only `rarity_power` 1.0–1.7 (`pet_authority.gd:112`, `economy.py:420-422`) | Add a hidden growth roll that multiplies stats |
| `aptitude {hp, attack, defence, speed}` | Missing | A pet's strength is derived from its owner (`pet_authority.gd:223,243`). A pet has no stat block of its own | Add per-stat aptitude and give pets their own stats |
| `contract` (master, equal, blood) | Missing | Only `bond` 0–10 (`pet_authority.gd:102`) | Add the field, defaulting to `master` |
| `learned_skills[]` (2–4 slots by stage) | Missing | `pets.json` `skills` is a list of 4 display strings per species (`economy.py:371-389`), shown as text only (`pets_page.gd:50`) | Add the array, and the number of slots per stage to `pet_growth.json` `stages` |
| `equipment {collar, talisman, saddle}` | Missing | `saddle` exists only as a sprite offset in `pets.json` `mount.saddle` (`economy.py:376,380,389`) | Add the dict |
| `wounded_until` | Missing | Not in the pet dict | Add it (UTC) |
| `knockouts[]` | Missing | A knockout is not recorded. `apply_retreat` only sets the AI state (`pet_authority.gd:251-256`) | Add the array of timestamps |
| `core_grade` | Missing | Not in the pet dict | Add it |
| `colour_variant` | Missing | Not in the pet dict | Add it |
| `name` | Present | `pet_authority.gd:88`. The `rename_pet` intent trims it to 16 characters (`:63-67`) | None |
| `locked` | Missing | Not in the pet dict. Items can be locked (`inventory_authority.gd:10` `lock_item`) but pets cannot | Add it |
| `movement` | Missing | Only `pets.json` `mount {art, scale, lift, saddle, flying}` exists | Add per-pet movement (from `pets.json` `movement`) |

## 2. S46 Owns: per character

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `pet_bag` slots | Missing | `GameCharacter` has `pets` (unbounded), `eggs` and `active_pet` (`game_character.gd:27-29`) | Add a slot count and carried-pet uids, with the size set by the bag grade |
| `mount_slot` | Differs | Mount is a role on the single active pet (`pet_authority.gd:33-40,179-183`) | Add a `mount_slot` uid, separate from `active_pet` |
| `command_capacity` | Missing | There is one `active_pet`. Companions have their own separate cap of 2 (`companion_authority.gd:22,36`) | Add capacity by realm (1, 2 at Spirit Awakening, 3 at Sage), shared with puppets and a swarm |

## 3. S46 Owns: enemies

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `beast_rank` on enemy data [field v0.6] | Partial | Nothing in `enemies.json`. At runtime `e.realm_index = realm_index_for_level(level)` (`enemy_authority.gd:119`). This gives the same value as the rank bands, but it is not capped at 9 (it runs to 17) and humans get it too | Compute `beast_rank` in `enemies.py` from the level band, capped at 9, and only for beasts. Store it on EnemyState |
| `nature` on enemy data | Missing | No key in any of the 75 entries. Hollowed foes carry only a `hollow_*` element and `hollowing` (`enemies.py:105,107,165`) | Add `nature` (spirit, demonic, hollowed) in `mob()` (`enemies.py:12-24`) |

## 4. S46 Owns: intents

`PetAuthority.intents()` lists `set_active_pet, set_pet_role, feed_pet, pet_command, rename_pet, choose_starter, attempt_tame, incubate_egg, hatch_egg, evolve_pet, breed` (`pet_authority.gd:10`).

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `devour_core {pet, core}` | Missing | Cores can be absorbed only by the player, as `raw` or `core` items (`items.py:241-248`, `inventory_authority.gd:418`) | Add the intent. Cores need an element |
| `incubate_input {egg, kind}` | Missing | `incubate_egg` takes only a bag index and rolls the species by weight (`pet_authority.gd:445-467`) | Add the intent with kinds essence_blood and element_stone |
| `learn_skill_book {pet, book}` | Missing | None | Add it, with slot overwrite |
| `fuse_pets {keep, sacrifice}` | Missing | Only `breed` exists (`pet_authority.gd:137-170`) | Add it |
| `equip_pet {slot, item}` | Missing | None | Add it |
| `offer_contract {kind}` | Missing | None | Add it |
| `pet_breakthrough {support[]}` | Partial | `evolve_pet` checks level, hearts and owner realm (`pet_authority.gd:311-341`). It takes no support items and cannot fail | Add a breakthrough path from Awakened on (see §6) |
| `set_mount` | Differs | Done as `set_pet_role` with `role:"mount"` on a pet (`pet_authority.gd:29-41`) | Add `set_mount` for the separate slot |
| `swap_pet_from_bag` | Differs | `set_active_pet` picks any owned pet, anywhere, even in combat (`pet_authority.gd:22-28`) | Limit it to bag pets and block it in combat |
| `rename_pet` | Present | `pet_authority.gd:63-67` | None (no UI; see §6 Quality of life) |
| `lock_pet` | Missing | None | Add it |

## 5. S46 Emits

None of these events is emitted, and none is in `data/event_contract.json`, which is built by `tools/data/contract.py`.

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `bloodline_awakened` | Missing | Not emitted | Emit at purity 50 and 90 |
| `contract_formed` | Missing | Not emitted | Emit it |
| `pet_wounded` | Missing | The nearest event is `pet_retreated` (`pet_authority.gd:256`) | Emit when a Grievous Wound starts |
| `pet_skill_learned` | Missing | Not emitted | Emit it |
| `pets_fused` | Missing | The nearest event is `pets_bred` (`pet_authority.gd:168`) | Emit it |
| `pet_core_formed` | Missing | Not emitted | Emit it |
| `beast_king_spawned` | Missing | Only the generic `field_boss_spawned` and `field_boss_defeated` exist (`enemy_authority.gd:17,149`) | Emit it, and toggle the zone buff |
| `beast_tide_started` | Missing | The Sect emits `defence_warning` for its raids (`sect_authority.gd:222`) | Emit it |
| `beast_tide_result` | Missing | The Sect emits `defence_result` | Emit it |

## 6. S46 mechanics table

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| **Beast rank** 1–9 from the level band. Shown on nameplates and in the Bestiary. Sets core grade and taming difficulty [field v0.6, shown v0.9] | Partial | The runtime `realm_index` matches the bands (`realms.json`: Bone Forging 1–9 = 1 … Sage 64–72 = 8, Sage Sovereign 73+ = 9) (`enemy_authority.gd:119`). The nameplate shows `Lv N` plus a danger badge coloured by the realm gap (`enemy_view.gd:59-63,183`). The Codex Collection shows name and kills only (`codex_page.gd:47-74`). Taming uses the level gap, not rank (`pet_authority.gd:416-417`) | Add the data field, a rank badge on the nameplate and in Collection, and rank in core grade and tame chance |
| **Nature**: spirit, demonic or hollowed. Demonic beasts need a Purifying Offering. Hollowed beasts can be tamed only after cleansing [v0.9] | Missing | Taming checks only `tameable` (`pet_authority.gd:400`). The offerings are Common, Earth and Heaven (`taming.json`). `hollow_stag.cleansable=true` (`enemies.py:165`) is read by no script | Add `nature`, a `purifying_offering` item, and a cleanse step (for example, cleansing sets a flag on the EnemyState) |
| **Cores for every rank**: rank 2+ drops a core at 2% × rank. The Core Exchange at the Beast Pavilion pays fixed Spirit Stones, capped daily. Pets devour cores of their own element for XP [v0.9] | Partial | Four named cores are `core` items: `pebble_core` 8% from Pebble Imp (rank 1, which the rule gives no core), `jade_core` 8% from Jade Sentinel, and `serpent_core` 100% from the Riverbed Serpent (`enemies.py:92,162,258`; `items.py:241-248`). `sentinel_core` is a plain material at 30% (`enemies.py:188`, `items.py:202`). Cores are absorbed for Qi or burned as Beast Fire (G1). No Core Exchange. Pet XP comes only from kills (`pet_authority.gd:258-267`) | Add a `core_chance` of 0.02 × rank to rank-2+ beasts, a core item per rank and element, a daily-capped Core Exchange at the Beast Pavilion, and `devour_core` |
| **Bloodline purity**: rolled by rarity (Common 5–15 … Primordial 60–80). Raised by essence blood and fusion. 50 awakens an ancestral skill (Ember Fox → Nine-Tail). 90 changes form. +0.2% trait strength per point [state v0.9, awakenings v1.0] | Missing | Rarity tiers exist (`economy.py:420-422`), but wild tames and eggs always come out Common (`pet_authority.gd:90` defaults `rarity` to common). Traits are flat (`pet_authority.gd:366-370`) | Add purity ranges per rarity, `bloodline_skill` and `form_change` on species, and scale trait sums by (1 + 0.002 × purity) |
| **Bloodline suppression**: reuses the S12 Pressure contest. A higher bloodline tier inflicts Fear and gives +10% tame chance [v1.0] | Missing | `fear` exists in `status_effects.json`. `pressure` is only a stat base (`stat_rules.gd:235`) and there is no Pressure contest | Add after purity. The +10% belongs in `tame_chance` (`pet_authority.gd:413-420`) |
| **Contract types**: master–servant by default. At 10 hearts the pet may offer an Equal Contract (one per character, permanent): Resonance both ways and one free skill cast per fight. Blood Contract: +15% stats, and a knockout gives the owner a short soul injury [Equal v1.0, Blood v1.1] | Missing | Bond is 0–10 hearts (`pet_authority.gd:102`). Resonance runs one way, pet to owner (`:373-379`). Pets have no skill casts: AllyBrain makes basic attacks only (`ally_brain.gd`) | Add contracts, a once-per-character flag, an offer at bond 10, and pet skill casts |
| **Command capacity**: 1, then 2 at Spirit Awakening, then 3 at Sage. A puppet or swarm takes a slot [v1.0] | Missing | One `active_pet` and one spawned `ally_uid` (`pet_authority.gd:7,206-230`) | Allow several active pets, each spawned, with the cap by realm |
| **Aptitude and growth**: hidden, revealed at Juvenile. The Beast Marrow Washing Pill rerolls one stat and adds no toxicity [state v0.9, pill v1.0] | Partial | A reveal-at-Juvenile hook exists, but for traits (`pet_growth.json` stage `juvenile.reveal_trait`, `pet_authority.gd:340,352-357`). No aptitude, no growth roll, no pill (`marrow` appears nowhere) | Roll aptitude and growth, reveal them with the first trait, and add the pill recipe |
| **Skill books**: slots opened by stage (2–4). Books drop from bosses and the Beast Hall shop. When slots are full, a new book overwrites a random slot [v1.0] | Missing | Species skills are fixed display strings. There is no Beast Hall shop (`shops.json` has 26 shops, none for beasts) | Add `pet_skill_books.json`, the book items, the Beast Hall shop and seeded overwrite |
| **Fusion**: 30% per trait and skill of B, plus half of B's purity above A's. Confirmation dialog. Locked pets excluded [v1.1] | Missing | Only breeding exists | Add it |
| **Pet equipment**: Collar, Talisman and Saddle (mounts only), forged with normal affixes and enhancement [v1.0] | Missing | None in `artifacts.json` (96 entries, all for the player) | Add a `pet_gear` family to `artifacts.json` and forge recipes |
| **Pet breakthroughs**: from Awakened on, use the S05 dialog with support items. Failure costs 1 heart or a temporary injury. Core Formation (Adult → Awakened) rolls a core grade [v1.1] | Partial | The Awakened stage exists (level 55, 7 hearts, Sage 1; `economy.py:430`). Evolve is a plain button (`pets_page.gd:108-125`) and cannot fail | Route Awakened and later stage-ups through `breakthrough_page.gd` with supports, failure and a core-grade roll |
| **Grievous Wound**: pets never die. After 3 knockouts in 5 minutes, −20% stats until the pet rests at the Pavilion or takes a Beast Revival Pill [v0.9] | Partial | "Never dies" is Present: at 0 HP the pet retreats for 60 s or until the owner meditates (`combat_authority.gd:668-670`, `pet_authority.gd:250-256`, `ally_brain.gd:14-20`, `pet_growth.json retreat_s 60`). Knockouts are not counted, there is no penalty, and there is no Beast Revival Pill | Record knockouts, set `wounded_until`, apply the 0.8 multiplier, clear it on a Pavilion rest or the pill, and emit `pet_wounded` |
| **Spirit Beast Bag**: key item with 2–6 pet slots by grade. Swap in the field, not in combat [v1.0] | Missing | Unlimited roster, swappable anywhere (`pet_authority.gd:22-28`) | Add the bag item grades, a `pet_bag` field, the swap intent and a combat block |
| **Mount slot**: combat pet and mount together. Mount-only species: Riverstone Ox (ground), Cloud Stag (ground, jump 600) [v1.0] | Differs | Mount is a role of the active pet. While mounted, no combat pet is spawned (`pet_authority.gd:213`). The mountable species are ember_fox, jade_crane and mist_wolf (`economy.py:376,380,389`). Every mount walks ×1.5 (`pet_growth.json mount_speed`) and no mount changes the jump (`player.gd:262`) | Add a separate slot and per-species `movement` (walk multiplier, jump impulse, climb) |
| **Incubation input**: essence blood (−10% max HP for 24 h) or element stones steer the element, add +10 purity or reroll a trait. Self-incubated hatchlings start at 3 hearts [v0.9] | Differs | Plain incubation is present (`pet_authority.gd:445-467`, species weights in `eggs.json`). No inputs. Every new pet starts at `bond 1.0` (`pet_authority.gd:88`), not 3 | Add `incubate_input`, the essence-blood and element-stone items, and a 3.0 starting bond for self-incubated eggs |
| **Beast Kings and Beast Tides**: each zone's field boss is a King: +10% to its zone's beasts, extra paw spawns, rare egg nest on death. A town Beast Tide every 7 real days reuses the S25 waves and rewards cores and eggs [v1.0] | Partial | The field bosses exist: Riverbed Serpent in the valley and Thousand Eye Toad in Azure, on 45-minute timers (`world.py:1186,1636`; `enemy_authority.gd:31-35,288-296`). The S25 wave code exists but serves sect raids only (`sect_authority.gd:199-235`, `defence.json`). No buff, extra spawns, nest or tide | Add `beast_kings.json`, a zone buff tied to the King being alive, a nest object, and a tide scheduler that reuses `start_defence` |
| **Pet content**: Beast Arena in Stoneford (1v1 and 3v3 auto-battles, weekly ladder). Beast Trial Grove daily dungeon [v1.1] | Missing | Only the player sparring post exists (`gap_audit.md:84`). The Stoneford rooms `sf_*` have no arena | Build both |
| **Quality of life**: rename and lock, a 1% colour variant at hatch, a Pavilion Feeding Trough that auto-feeds offline [v0.9] | Partial | The `rename_pet` intent exists with no UI (`pet_authority.gd:63-67`; nothing in `scripts/ui` calls it). No lock, no variant and no trough. Hunger exists: `care_mult` 0.7 when unfed (`pet_authority.gd:306-308`) | Add a rename field and lock toggle to the page, a variant roll in `hatch_egg`, and trough feeding in the offline claim |
| **Beast Taming Dao** tiers 3–6: tame elites (3), teach NPCs (4), tame bosses after a trial (5), write a custom contract (6) [v1.1–v1.3] | Partial | The Dao has 2 generic tiers ("+5% quality or speed", "−10% materials"), valley cap 2 (`techniques.py:112-113`). Each tier adds +5% tame chance (`taming.json per_dao_tier`, `pet_authority.gd:418`) | Write taming-specific tier text, then tiers 3–6 in the later zones |
| **Insect swarm**: Copperjaw Beetle box, grows offline on ore, damage × log(population), a Queen mutation, countered by Wood [v1.2] | Missing | Nothing named Copperjaw. `rock_beetle` is only an enemy | Future (v1.2) |
| **Taming fix**: a beast at 0 HP stays "subdued" at 1 HP for 10 s while a Bonding Offering is on quick-use [v0.9] | Missing | Taming works from quick-use (`inventory_authority.gd:401`), but a one-hit beast dies normally (`enemy_authority.gd:280`). No `subdued` state | In the enemy damage path: if `tameable` and an offering is set on quick-use, clamp HP to 1 and set a 10 s subdued timer |

## 7. S46 data

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `pets.json` `bloodline_skill` | Missing | The species keys are art, branches, element, family, favourite_foods, id, inherit_owner, mount, name, skills, starter/tame and strength_role | Add it in `economy.py` `pets()` |
| `pets.json` `form_change` | Missing | Not a key | Add it |
| `pets.json` `movement` | Missing | Only the `mount` sprite spec | Add it |
| `pets.json` `mount_only` | Missing | Not a key. No mount-only species | Add it, with the two species |
| `pet_skill_books.json` | Missing | No such file in `data/` | Add a generator and the file |
| `pet_gear` in `artifacts.json` | Missing | No pet slots in `artifacts.json` | Add it |
| `enemies.json` `beast_rank` | Missing | Not a key (runtime `realm_index` only) | Add it in `mob()` |
| `enemies.json` `nature` | Missing | Not a key | Add it |
| `enemies.json` `core_chance` | Missing | Not a key. Cores are ad-hoc `d(item, p)` drops | Add it (0.02 × rank) |
| `beast_kings.json` | Missing | No such file | Add it |
| `beast_tide` wave sets in `expeditions.json` | Missing | `expeditions.json` holds only idle expeditions. The only wave sets are in `defence.json` | Add them (or put them in `defence.json` and change the spec) |

## 8. S46 UI

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Spirit Animals page **Growth tab** (purity bar, aptitude reveal, contract, learned slots, gear) | Partial | `pets_page.gd` is a single pane with no tabs. A growth panel shows the next-stage gates and Evolve (`:65,108-125`), plus bond, XP, species skills and traits (`:47-54`) | Add tabs and a Growth tab with the five widgets |
| **Bestiary rank badges** | Missing | The bestiary is the Codex Collection tab. It shows the creature, its name and "defeated N" (`codex_page.gd:47-74`) | Add a rank badge per beast. Humans, ghosts and constructs get none |
| **Pet Bag strip** on the party portrait | Missing | The HUD portrait (`hud.gd:173`) draws no pet | Add the strip, tied to `pet_bag` |
| **Mount button** in the Pet wheel | Missing | There is no Pet wheel. The HUD pet button opens the Spirit Animals page (`hud.gd:164,214,374`). Mounting is a role button on the page (`pets_page.gd:56-60`). `pet_command` has no UI (`pet_authority.gd:54-56`) | Add a pet wheel (follow, stay, mount, swap) on the pet button |

## 9. S46 tests

`pets_suite` (`tests/rules_tests.gd:166-243`) covers evolve gates, trait reveal, resonance, hunger, rarity and breeding. `valley_run.gd` covers taming (`:1045`), incubation (`:1110`) and riding the crane (`:2068-2073`).

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Purity thresholds at 49, 50, 89 and 90 | Missing | No purity | Add it |
| Equal Contract only at 10 hearts, once per character | Missing | No contracts | Add it |
| Command capacity by realm | Missing | No capacity | Add it |
| Skill-book overwrite under a fixed seed | Missing | No books | Add it |
| Fusion odds; a locked pet cannot be fused | Missing | No fusion | Add it |
| Grievous Wound after 3 knockouts in 5 minutes | Missing | No knockout tracking | Add it |
| Core drop chance by rank | Missing | No `core_chance` | Add it |
| Beast King buff lifts on the King's death | Missing | No buff | Add it |
| Pets never reach a dead state | Missing | The behaviour is right (retreat, `combat_authority.gd:668-670`) but untested: no test mentions `pet_retreated` or `downed` | Add a rules check: pet HP to 0 gives `downed`, `alive` stays true, and it returns |

## 10. Part 8 · Spirit beasts content

### 10a. Beast rank bands and natures

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Rank bands: Lv 1–9 → 1, 10–18 → 2, 19–27 → 3, 28–36 → 4, 37–45 → 5, 46–54 → 6, 55–63 → 7 | Partial | `realms.json` bands match exactly (index 1–7 at levels 1, 10, 19, 28, 37, 46, 55; Heaven Glimpse runs 55–63). Only used as the runtime `realm_index` | Put the value in data (see §3) |
| Hollowed Boarlet and Hollow Stag are **hollowed** | Missing | Both exist (`hollowed_boarlet` Lv 7–12, `hollow_stag` Lv 55–59) with `hollow_*` elements, and neither has a nature | Set `nature: hollowed` |
| Green Viper, Mud Hound and Mist Vulture are **demonic** | Missing | All three exist (`green_viper`, `mud_hound`, `mist_vulture`) with no nature. None is `tameable` | Set `nature: demonic`. Make them tameable behind the Purifying Offering |
| All other valley beasts are **spirit** | Missing | No default | Default `nature: spirit` for `race: beast` |
| Bandits, cultivators, ghosts and constructs have **no beast rank** | Differs | `race` exists and defaults to `beast` (`enemies.py:15`). Humans are marked, and `terracotta_warden` is a construct and `tomb_king` undead. But `paper_talisman_ghost`, `mirror_wisp` and `weeping_lantern` (ghosts) and `trial_puppet`, `stone_guardian`, `jade_sentinel`, `river_sentinel` and probably the story boss `gate_guardian` (constructs) are all `race: beast`. The Beast-Taking Cauldron already relies on `race` (`combat_authority.gd:956`) | Re-tag those as `ghost` or `construct`, and give ranks only to `race == beast` |

### 10b. Valley Beast King and Beast Tide

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| The Riverbed Serpent is the valley Beast King | Partial | It is a field boss, Lv 25, in `dw_serpents_shallows` (Deepwater Bend), with a 45-minute respawn (`world.py:1181-1186`) and drops `serpent_core` and `serpent_scale` (`enemies.py:258`). It is not marked as a King | Add it to `beast_kings.json` |
| While it lives, valley beasts get +10% stats | Missing | No zone buff. Mobs use `StatRules.mob_stats` only (`enemy_authority.gd:120`) | Apply ×1.1 in `_spawn` when the zone's King is alive. Lift it on `field_boss_defeated` |
| Extra paw-marked spawns in Deepwater Bend | Missing | `dw_bend_shore` spawns only jade_carp and tide_crab. The only `wild_pet` spawns are reed_otter, ember_fox and jade_crane_chick (`world.py:1020,1072,1096`) | Add conditional tameable spawns tied to the King |
| Killing it opens a rare egg nest for 30 minutes | Missing | No nest object | Add a timed room object that grants a rare-rarity egg |
| Beast Tide every 7 real days at Stoneford Gate | Missing | Stoneford Gate exists (`sf_gate`, `world.py:601`). The only wave event is the sect raid: every 2–3 days at `hv_sect_grounds` from sect level 6 (`defence.json`) | Add a tide config (7 days, room `sf_gate`) that reuses `start_defence` → `world.start_room_event` (`sect_authority.gd:208-223`) |
| Three waves of rank 2–5 beasts | Missing | The raid waves are `mudwater_bandit`, `mud_hound` and `hollow_stag` (a human, and a rank-7 beast). `start_defence` runs **one** wave per event, picked by wins (`sect_authority.gd:215-217`), not three in a row | Run the waves in sequence, drawn from rank 2–5 beasts |
| Rewards: cores, eggs and Spirit Soil | Missing | Raids reward 40 prestige and 200 taels (`defence.json`). No `spirit_soil` item exists | Add the rewards and the Spirit Soil item |

### 10c. Mount-only species

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| **Riverstone Ox**: tamed at Quarry Rim (paw-marked, Cloud Stride 1). Walk ×1.5, jump 530, cannot climb | Missing | No species or enemy. Quarry Rim exists (`sq_quarry_rim`, Lv 4–6, `world.py:994`). 530 is the player's jump impulse (`movement_solver.gd:4`) | Add pet, enemy and art, a spawn gated by `realm cloud_stride_1`, `mount_only`, and movement {walk 1.5, jump 530, climb false} |
| **Cloud Stag**: egg from the Beast Tide (Cloud Stride 1). Walk ×1.6, jump 600 (apex about 157) | Missing | No species. The apex figure matches the engine: 600² / (2 × 1150 `GRAVITY`) ≈ 156.5 | Add the species and a tide egg, with movement {walk 1.6, jump 600} applied in the player's jump while mounted |

### 10d. Pet skill books (all missing: no `pet_skill_books.json`, no book items)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Iron Hide: +10% defence (Beast Hall shop) | Differs | Only a pet **trait** `iron_hide`, "Takes 10% less damage" (`economy.py:403`) | Add a book with a distinct id (for example `book_iron_hide`) and the Beast Hall shop, or rename the trait |
| Frenzy: +15% attack speed for 6 s after a kill (Mudwater Boss Den) | Missing | The Boss Den exists (`mh_boss_den`, Big Toad Tan). Pets have no attack-speed stat: AllyBrain's windup and recover times are fixed (`ally_brain.gd`) | Add the book, a pet attack-speed term and the drop |
| Deep Pockets: +1 bag row while active (Beast Hall shop) | Missing | None | Add it |
| Herb Whisper: ripening timers within 400 (Falls Pool chest) | Missing | `cf_falls_pool` has no chest (only a wild crane spawn). Herb ripening (S45) does not exist | Add a chest and the book. Depends on S45 ripening |
| Thunder Roar: 1 s stun ring (Stormwing Hawk elite) | Missing | A Stormwing Hawk elite spawns in `cc_sky_ledges` (Lv 43). The `stun` status exists | Add the book and the drop |
| Guardian Spirit: absorbs one hit on the owner every 30 s (Beast Trial Grove, v1.1) | Missing | No Trial Grove | Add it with the Grove |

### 10e. Pet gear

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Bone Collar (Common): boar hide ×2, mole claw ×2 | Missing | Both materials exist (`boar_hide`, `mole_claw`) | Add the gear and a forge recipe |
| Scale Talisman (Earth): serpent scale ×2, jade scale ×2 | Missing | Both materials exist (`serpent_scale`, `jade_scale`) | Add it |
| Reed Saddle (Common, mounts): cloth ×3, boar hide ×2 | Missing | Both materials exist | Add it |

## 11. Coverage matrix rows (classified in §6; not counted again)

| Gap report row | Status | See |
|---|---|---|
| Beast rank on wild monsters | Partial | §6 rank, §3 |
| Spirit / demonic / Hollowed nature | Missing | §6, §10a |
| Cores for every rank | Partial | §6 |
| Bloodline purity | Missing | §6 |
| Bloodline suppression | Missing | §6 |
| Contract types | Missing | §6 |
| Command capacity ("Part 4 unlock additions") | Missing | §6. `unlocks.json` has no capacity unlocks (only `second_companion` for human companions) |
| Aptitude and growth rolls (Beast Marrow Washing Pill) | Partial | §6 |
| Skill books | Missing | §6, §10d |
| Fusion | Missing | §6 |
| Pet equipment | Missing | §6, §10e |
| Pet breakthroughs | Partial | §6 |
| Soft death penalty (Grievous Wound, never dies, Beast Revival Pill) | Partial | §6 |
| Spirit Beast Bag (S24 Pet wheel) | Missing | §6, §8 |
| Separate mount slot | Differs | §6, §10c |
| Incubation input | Differs | §6 |
| Beast tides and beast kings (S25 defence code, S49 calendar) | Partial | §6, §10b. There is no S49 calendar (`world_event_*` is never emitted) |
| Pet content | Missing | §6 |
| Quality of life | Partial | §6 |
| Beast Taming Dao | Partial | §6 |
| Insect swarm companion | Missing | §6 |

## 12. Priority table

The beast rows (5, 11 and the swarm part of 15) are counted in beast scope. The other rows belong to sibling packets, and their status here is indicative, taken from the CHANGELOG (G1, G2a) and quick greps.

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| #5 PetState depth [fields v0.9, features v1.0] | Missing | §1. No new field exists | Build the G3 fields first (priority 5) |
| #11 Pet skill books, pet gear, mount slot, Spirit Beast Bag, Beast Arena [v1.0–v1.1] | Missing | §6, §10 (the mount exists only as a role) | G3 and G6 |
| #15 (swarm part) Insect swarm [v1.1–v1.3] | Missing | §6 | G7 |
| #1 Define S15's undefined rules [v0.8] | Partial | G1 settled fire, furnace, pills never decay and auto-refine at 25%. Seed sources (S45) are absent: the only seed is `evergreen_heart_seed` (`items.py:295`) | Sibling packet |
| #2 Lifetime pill resistance, foundation share, residue | Present | CHANGELOG G1. `residue_changed` is emitted | — |
| #3 Heart-demon meter and karma ledger | Present | CHANGELOG G1. `heart_demon_changed` is emitted. `merit_changed` and `sin_changed` are not | Sibling packet (events) |
| #4 Treasure slot, flying sword, talisman craft, throwables | Partial | G2a: two treasure slots, throwables and one talisman treasure. No Sword Release (`sword_released` never emitted) and no talisman crafting | Sibling packet |
| #6 Herb node flags and harvest tap | Missing | G3 not started (`herb_harvested`, `guardian_spawned` and `herb_ripening` never emitted) | Sibling packet |
| #7 Enhancement pity, transfer, salvage | Partial | Salvage exists (`crafting_authority.gd:463`, emits `item_salvaged`, not `items_salvaged`). Failure has no pity (`:455-458`). No transfer | Sibling packet |
| #8 Tribulation, Core Forging grade, fates | Missing | No `tribulation` or `fate_*` in the scripts | Sibling packet |
| #9 World-event scheduler and calendar | Missing | `world_event_*` never emitted | Sibling packet. The Beast Tide depends on it |
| #10 NPC affinity, bonds, grudges, bounties | Missing | No `grudge`, `bounty` or `affinity_changed` | Sibling packet |
| #12 Body ladder, soul line, sect roles, Inner Arts, stances | Missing | No `body_tier`, `inner_art` | Sibling packet |
| #13 Associations, recipe fragments, experimentation | Missing | No `experiment` or `Alchemist Guild` | Sibling packet |
| #14 Alignment, Blood and Buddhist paths, weapon families | Missing | No `alignment` | Sibling packet |
| #15 (other parts) Rankings, territory, mortal kingdom, weather, lifespan | Missing | No `ranking`, `territory` or `lifespan` | Sibling packet |

## 13. Rules the report found named but undefined (cross-packet, indicative)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Pill Grain "keeps longer": pills never decay, Grain redefined | Present | CHANGELOG G1. `stats.py:297` "Pills never decay" | — |
| "Rare fire or a special furnace" | Present | CHANGELOG G1 fires (charcoal, earth, beast, heavenly) and furnaces | — |
| The Reflection's Heart Demons need a state field | Present | CHANGELOG G1 heart-demon meter. `heart_demon` enemy | — |
| Gardening seeds with no seed source | Missing | Only the Evergreen Heart seed exists (`crafting_authority.gd:361-371`) | Sibling packet (S45) |
| Auto-refine XP unstated (25%) | Present | CHANGELOG G1: "Auto-refine teaches 25%" | — |

## 14. Genre staples kept out on purpose (Present means kept out, as required)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Hard lifespan and old-age death | Present | No `lifespan` anywhere. The S49 lifespan display is also absent (not a violation) | — |
| Stamina and energy gates, battle passes | Present | No `stamina` or `battle_pass`. Enemy `energy` is a Qi type only | — |
| **Pet permadeath** | Present | Pets retreat at 0 HP and return (`pet_authority.gd:250-256`, `ally_brain.gd:14-20`) | Add the missing test (§9) |
| Enhancement that destroys or de-levels items | Present | A failed enhance keeps the level (`crafting_authority.gd:455-458`) | — |
| Sexual dual cultivation | Present | Only "Paired cultivation" with a companion while meditating (`companion_authority.gd:93-96`) | — |
| Player full-loot at v2.0 | Present | No PvP loot code | — |
| A full Gu path as a core system | Present | "Gu" is only a character and family name (Elder Gu, Gu's warehouse) | — |
| Corpse refining, soul banners, body seizing as player powers | Differs | No corpse or body-seizing powers. The **Wisp Banner** treasure is "a banner of three bound wisps" that strike foes (`items.py:80`), which reads close to a soul banner | Confirm the wording is acceptable, or reword it (spirit wisps, not bound souls) |
| Stat and aptitude pills sold in shops | Present | No shop item carries a permanent-stat effect (item effect kinds checked). The Beast Marrow Washing Pill must stay alchemy-only | — |
| Herb rot and pill decay | Present | G1: pills never decay. Herbs never perish (`gap_audit.md` row 30) | — |
| Unrestricted auto-battle | Present | No auto-battle or auto-hunt. The Arena's pet auto-battles (S46) will need a scope limit when built | — |

## 15. Events S43–S49

### Beast rows (counted in beast scope)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `bloodline_awakened, contract_formed, pet_wounded, pet_skill_learned, pets_fused, pet_core_formed` (Pet; payload pet, values; reacts: Pet StatBlock, owner Resonance, HUD portrait) | Missing | None emitted (§5). Pets have no StatBlock; `a.stats = {"attack": 0.0}` (`pet_authority.gd:227`). The HUD portrait shows no pet | Emit them, add to `contract.py` CATALOGUE, and add HUD handlers in `hud.gd` beside `pet_evolved` (`:554`) |
| `beast_king_spawned, beast_tide_started, beast_tide_result` (Enemies / Sect; payload zone, values; reacts: zone buff, HUD banner, Mail, rewards) | Missing | None emitted. Field bosses have a HUD toast (`hud.gd:467,532`). Raids use `defence_*` | Emit them. Add mail templates and a banner |
| Pets and companions **follow** on `jumped` and `landed` | Partial | AllyBrain follows on the ground plane at `altitude = 0` and ignores jumps (`ally_brain.gd`, last lines). The movement events are not emitted | Needs the S43 events. Follow the owner's altitude or tier |
| Pets **blink** when they cannot climb (`climb_started`); mounts dismount | Partial | A generic blink when more than 700 away (`ally_brain.gd`, `a.plane.distance_to(st.plane) > 700`). No climb events and no dismount on climbing (dismount is only on a hit, `pet_authority.gd:195-201`) | Blink on `climb_started` for non-climbers, and dismount on climbing |

### Other rows (cross-packet, indicative; a script grep for `emit("<name>"` across `scripts/`)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Movement events: `jumped, landed, wall_kicked, art_used, climb_*, fell_out, volume_*` | Missing | 0 emits | Sibling packet (S43) |
| Progression: `pill_resistance_changed, foundation_changed, residue_changed, heart_demon_changed` | Partial | Only `residue_changed` and `heart_demon_changed` are emitted | Sibling |
| `fate_*, tribulation_*, core_graded, qi_deviation, epiphany, vow_broken, body_tier_reached, physique_awakened` | Missing | 0 emits | Sibling |
| Crafting: `flame_absorbed, furnace_blast, pill_cloud, pill_tribulation_result` | Partial | `flame_absorbed` and `pill_cloud` are emitted | Sibling |
| `recipe_deduced … commission_completed`; herb events | Missing | 0 emits | Sibling |
| Combat treasure and sword: `treasure_used` and the `sword_*` events | Partial | Only `treasure_used` is emitted (3 sites) | Sibling |
| Inventory: `natal_*, enhancement_inherited, items_salvaged, loadout_swapped, talisman_crafted, weapon_awakened` | Missing | 0 emits (`item_salvaged` exists under a different name) | Sibling |
| Relations and Calendar: `merit_changed … heavenly_phenomenon` | Missing | 0 emits | Sibling |

---

## Notes for the implementer

- **Wild and egg pets are always Common.** `apply_grant` defaults `rarity` to common (`pet_authority.gd:90`), and only bred eggs carry a rarity. A purity roll "by rarity at hatch or tame" therefore needs a rarity roll for tames and eggs first.
- **Pets have no stats of their own.** HP is 40% of the owner's × rarity, and damage is the owner's physical attack × inherit share (`pet_authority.gd:223,243`). Aptitude, growth, the Blood Contract +15%, the Grievous −20%, the King +10% (for pets), gear and skill books all need a pet StatBlock or a multiplier chain in `PetAuthority.tick`.
- **Only one pet is spawned.** `ally_uid` holds a single pet (`pet_authority.gd:7`). Command capacity and a mount slot next to a combat pet both need a list of spawned allies.
- **Data validation whitelists `use_action`** (`data_validation.gd:152`: appraise, incubate, tame, absorb_flame, talisman_charge). New item kinds (skill book, essence blood, element stone, pet gear, Purifying Offering, bag) must be added there.
- **The Beast Tide needs a scheduler.** It is specified to reuse S25 waves, and S49's calendar does not exist yet. A standalone 7-day timer, like `next_defence_utc` (`sect_authority.gd:229`), would work until S49 lands.
