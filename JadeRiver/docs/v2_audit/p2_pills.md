# Audit · Packet P2 (S44 Pill cultivation depth + Part 8 pills) against the build

Build audited: `/home/user/Game/JadeRiver` at commit `796f089` (G1 plus its follow-up; G2a treasures landed after G1). The audit was read-only: no Godot, tests or build scripts were run.

Status key:
- **Present:** it exists and matches the spec.
- **Differs:** it exists, but the name, number or behaviour is different.
- **Partial:** part of it exists.
- **Missing:** nothing like it exists.

**About milestones.** The build is on release 1.1 (Act II) and does not tag features with milestones. So every `[v0.5]`–`[v1.0]` item in the packet is already due, and so is anything tagged v1.1 (the guild Master rank, the Azure Expanse flame). The build's own roadmap puts some of this packet in later gap phases: guild, natures, fragments and experimentation in G5, and tribulation and Soul catch in G6 (`docs/gap_audit.md:34-41`, `:194-199`). Oils and baths were planned for G2, but G2a did not ship them. Where a milestone tag matters, the row says so.

**Found while auditing (not in the spec).** Pill marks are rolled but never stored.
- `crafting_authority.gd:268` passes `{"quality", "marks"}` to `apply_add`.
- `InventoryAuthority.pill_entry` (`inventory_authority.gd:207-213`) copies only `quality` and `halo`. `marks` is dropped, and the overflow copy at `:197` drops it too.
- As a result, every bag stack has 0 marks, and the +2 % per line and the slot's gold lines never apply.
- The G1 test at `rules_tests.gd:840` calls `pill_potency` on a hand-built dict, so it does not catch this.

---

## 1. S44 · What S44 owns: fields, intents and events

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `pill_resistance {family: {count, doses}}` on CultivatorState | Differs | `cultivator_state.gd:42`: `{family: doses}`, a flat int per family. Families are `qi, body, soul, insight` | Store `{count, doses}` and rename `qi` to `accumulation`. Add a `breakthrough_support` family. Migrate saves in `restore()` (`:132`) |
| `foundation {pill_qp, total_qp}` since the last major breakthrough | Differs | `cultivator_state.gd:43`: `{realm, total, pill}`, keyed by great realm (`progression_authority.gd:311-316`). Majors coincide with great-realm changes (`realms.json`), so the reset behaviour matches | Rename the keys to `pill_qp`/`total_qp`, or document the alias |
| `residue` | Present | `cultivator_state.gd:44`, saved at `:94`/`:134` | — |
| `support_failures {realm_key: n}` | Differs | Named `support_fails` (`cultivator_state.gd:50`), shaped `{realm: {item: n}}`. It counts the failures each item was used in, not the failures at that breakthrough | Rename. Count failed attempts per realm_key, as the spec does |
| Crafting `flames` (absorbed flames) | Present | `c.crafting.flames`, `crafting_authority.gd:333-338` | — |
| Crafting `recipe_fragments {recipe: pages[]}` | Missing | No field, grep empty | Add it with the Deduce system |
| Crafting `experiments` (account-shared log) | Missing | Not in `account_state.gd` | Add an account-scoped log |
| Crafting `guild {craft: rank}` | Missing | Only XP profession ranks (`crafting_authority.gd:55-80`) | Add guild ranks separate from XP ranks |
| Crafting `commissions` (open orders) | Missing | — | Add |
| Furnaces are item instances (Inventory) | Differs | Furnaces are stackless `type: tool` key items with a static `furnace` dict (`items.py:312-317`). The best one carried is auto-picked (`crafting_authority.gd:285-298`). There is no instance, uid or enhance level | Make furnaces equipment instances in a `tool_furnace` slot that the player chooses |
| Intent `select_fire {fire}` | Differs | No intent. `fire` is a parameter on `craft_step`/`refine` (`crafting_authority.gd:40-44`) and lives in page state (`crafts_page.gd:18`) | Add a `select_fire` intent, or record the alias in the spec |
| Intent `absorb_flame {flame}` | Differs | The intent exists (`crafting_authority.gd:30,45`) but takes a bag `index`, not `flame` | Accept `{flame}`, or document it |
| Intent `deduce_recipe {recipe}` | Missing | grep empty | Add |
| Intent `start_experiment {herbs[]}` | Missing | grep empty | Add |
| Intent `take_guild_exam {craft, rank}` | Missing | — | Add |
| Intents `accept_commission`, `deliver_commission` | Missing | — | Add |
| Intent `eat_raw {herb}` | Differs | Handled by the generic `use_item` on items with `raw` (`inventory_authority.gd:418-421`) | Add an `eat_raw` alias, or document the difference |
| Intent `start_bath {recipe}` | Missing | No baths | Add with the Bath station |
| Intent `catch_pill_soul {timing}` | Missing | — | Add (v1.0) |
| Intent `tribulation_shield {bolt, timing}` | Missing | — | Add (v1.0) |
| Emit `pill_resistance_changed` | Missing | Not emitted. `pill_used` carries `family`/`resistance` (`inventory_authority.gd:466-467`) | Emit it on each dose and at breakthrough decay |
| Emit `foundation_changed` | Missing | Not emitted from `_track_foundation` or Settle foundation | Emit it |
| Emit `residue_changed` | Partial | Emitted (`progression_authority.gd:704`), but missing from `data/event_contract.json` (`tools/data/contract.py:27,35`), so `contract_tests.gd` never checks its owner or reactor. Nothing reacts to it | Add it to the contract and to a reactor |
| Emit `flame_absorbed` | Partial | Emitted (`crafting_authority.gd:340`), and the HUD toasts it (`hud.gd:497`). Not in the event contract | Add it to the contract |
| Emit `furnace_blast` | Missing | — | Add with conflicts |
| Emit `pill_cloud` | Partial | Emitted (`crafting_authority.gd:280`), with a world reaction (`world.gd:397-409`). Not in the event contract | Add it to the contract |
| Emit `pill_tribulation_result` | Missing | — | Add |
| Emit `recipe_deduced`, `experiment_result` | Missing | — | Add |
| Emit `guild_rank_changed`, `commission_completed` | Missing | — | Add |

## 2. S44 · Lasting costs

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Resistance families: accumulation, body, soul, insight, breakthrough support. Healing, restoration, antidote and purging are exempt | Differs | Family comes from the effect kind (`progression_rules.gd:111-118`): `add_progress→qi`, `add_body_xp→body`, `add_soul→soul`, `add_insight→insight`. No `breakthrough_support` family: Foundation Guard and Cleansing have `use: []`, so they are exempt. No pill has `add_insight`, so **Clear Mind Pill has no family** and the insight family can never fill. Exempt pills are exempt because of how they are built | Add an explicit `family` field (see §9). Use it instead of inferring from effects |
| Every 5 doses add 1 to count; the remainder stays in doses | Differs | One dose adds 1 to the count (`inventory_authority.gd:426`) | Accumulate doses; at 5, count += 1 and doses −= 5 |
| Effect × 1 ÷ (1 + 0.25 × count) | Differs | The formula is the same, but it is applied to *doses* (`progression_rules.gd:121-124`, `stats.py:109` `resistance_step 0.25`) | Apply it to `count` |
| At each major breakthrough every count drops by 1, then halves (rounded down) | Differs | Drops by 1 dose only; no halving (`progression_authority.gd:469-473`) | Use `count = floor((count-1)/2)`, clamped at ≥0 |
| Budget: 10 doses per realm keeps pills ≥67 %; a pill-fed character falls toward 40 % | Differs | Under the build's per-dose rule, 10 doses leave pills at 1/3.5 = **29 %**. This is exactly the gap-report behaviour the spec rejects. `tests/balance_sim.gd` does not model resistance | Fix it with the three rows above. Add a balance-sim check |
| A support pill stops lowering risk after 2 failed attempts at the same breakthrough | Present | `progression_authority.gd:349-358` (limit `support_fail_limit 2`, `stats.py:109`), increment at `:435-437`, cleared on success at `:474` | Only the per-item vs per-realm count differs (§1) |
| Foundation: track the current major realm's QP and the part from pills and beast cores | Present | `_track_foundation` (`progression_authority.gd:311-316`) counts `item:` sources with a family: pills, cores (`items.py:241-248`) and raw herbs (an extension) | — |
| Share = pill_qp ÷ total_qp | Differs | `pill / max(total, need)` (`progression_rules.gd:131-134`). Early in a realm this is lower than the spec's ratio | Use `pill_qp / total_qp`, or state the floor in the spec |
| Share above 30 % adds the unmet soft requirement "Foundation: hollow" (cause structure, +1 risk step) | Present | `progression_rules.gd:136-137` (`hollow_share 0.30`), `progression_authority.gd:363-366`, string `sim.progression.foundation_hollow` | — |
| A failure caused by it picks "Weak foundation" | Differs | When the foundation is hollow, **every** failure becomes `weak_foundation` (`progression_authority.gd:439`), not only failures caused by it | Add `structure` to the unmet causes and let `pick_failure` choose, or accept the build's rule |
| Settle foundation focus (S07): −5 share points per hour, no progress, −5 residue per hour | Differs | The focus exists (`progression_authority.gd:906, 958-969`; UI `cultivation_page.gd:224`) and grants no progress. The rates are **6 points/h** (`settle_share_per_h 0.06`) and **3 residue/h** (`settle_residue_per_h 3`, `stats.py:111`). It works only through offline seclusion | Set 0.05 and 5 |
| A medicinal bath lowers the share by 10 points | Missing | No baths | Add with baths |
| Share resets at each major breakthrough | Present | It resets when the great realm changes (`progression_authority.gd:313`, `progression_rules.gd:133`). Every major is a great-realm change | — |
| 5 % of all toxicity becomes residue, and it never drains | Present | `progression_authority.gd:690-704` (`residue_share 0.05`) | — |
| Each 10 residue gives −1 % accumulation, capped at −10 % | Present | `progression_rules.gd:140-142`, applied at `progression_authority.gd:99` | — |
| Purging Pills do not touch residue | Present | Negative toxicity skips residue (`progression_authority.gd:694`). Test at `rules_tests.gd:758-759` | — |
| Clear paths: flawless Heaven's Cleansing (all) | Present | `world.py:2118` `on_flawless: clear_residue`. `world_authority.gd:875-877`, `game_authority.gd:142` | — |
| Clear paths: Marrow-Washing bath (−20) | Missing | No baths | Add |
| Clear paths: Settle foundation (−5/h) | Differs | 3/h (see above) | 5/h |
| Heart demon: a breakthrough taken with ≥2 support pills adds 5 [v0.9] | Present | `progression_authority.gd:414-415` (`forced_breakthrough 5`, `forced_supports 2`, `stats.py:114`) | — |
| Pills never decay (a text fix replacing "keeps longer") | Present | No decay code. Codex `pills_and_the_body`: "Pills never spoil" (`story.py:1776`). No "keeps longer" text remains | — |
| Pill Grain (180 %): −50 % toxicity, and that dose ignores resistance | Present | `grades.json` `pill_qualities.pill_grain 1.8`, `pill.toxicity.pill_grain 0.5` (`stats.py:283-287`). Resistance skipped at `inventory_authority.gd:424` | — |
| Pill Halo (200 %): +1 % per 24 h in a **storage chest** in a room with Qi density ≥2, cap +20 % | Differs | 200 % is present. Growth: **+5 % per hour** on Halo pills **in the bag** during offline seclusion with density ≥2, **cap +50 %** (`stats.py:286` `halo {per_hour 0.05, cap 0.5}`; `inventory_authority.gd:226-238`; `progression_authority.gd:973`) | Tick storage-chest stacks in density ≥2 rooms at 0.01 per 24 h, cap 0.20 |
| Pill Soul (220 %): a unique effect from the **recipe's `soul_effect`** | Differs | 220 % is present. On use, a 50 % roll from one global pool of 4 (`stats.py:299-304`, `inventory_authority.gd:454-464`) | Give each recipe (or pill) a `soul_effect` and always apply it |

## 3. S44 · Fire and furnace

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Fire slot on the Furnace screen | Present | `crafts_page.gd:18-20, 107-120` | — |
| Charcoal: everywhere, +0, up to Perfect | Present | `stats.py:293`; `rare_allowed` (`crafting_authority.gd:314-316`); test `rules_tests.gd:816-823` | — |
| Earth Fire: at a fixed vent, one per zone (valley: the hot-spring vent in Rapids Terraces), +10 %, Grain | Present | `earth_vent_wg` in `wg_rapids_terraces` (`world.py:2208-2214`); `stats.py:294`; the vent counts as a furnace station (`crafting_authority.gd:23`). Only 2 zones have a vent (valley, Sunscar) | Add a vent per remaining zone if "one per zone" means every zone. Hot-spring flavour text is optional |
| Beast Fire: anywhere, burns one beast core **of rank 2 or more** per batch, +15 %, Grain | Differs | +15 % and Grain are present, and one core is burnt per batch (`crafting_authority.gd:250, 318-321`). **Any** core works, including `pebble_core` (common). Cores have no rank | Add a core rank. Require rank ≥2 (guardian stone, serpent, jade and beast cores) |
| Heavenly Flame: one unique flame per zone tier, from a boss or secret realm, absorbed for good, +20 %, Grain/Halo/Soul | Present | `stats.py:296`; `absorb_flame` (`crafting_authority.gd:328-343`); a duplicate gutters into 20 SS | — |
| Earth and Beast Fire in v0.9, the first Heavenly Flame in v1.0, one more per zone in v1.1–v1.5 | Partial | Three flames: valley, Sunscar and Starsea (`items.py:62-66`). The first Azure Expanse zones have none | Add a flame for each Act II zone, per the milestone plan |
| Flames are Codex collectables | Present | `story.py:1783-1787`; codex entry added on absorb (`crafting_authority.gd:339`) | — |
| Furnaces become item instances in a tool slot | Differs | See §1 | See §1 |
| Heat stability: band width, +1 % per enhancement level at the forge | Partial | Band width is present (`furnace.band`, `band_mult` `crafting_authority.gd:309-312`). Furnaces are not equipment, so `enhance` refuses them (`crafting_authority.gd:442`), and there is no per-level bonus | Make furnaces enhanceable, with band +0.01 per level |
| Batch cap: bronze 3, Earth 5, Heaven 8, Mystic 10 (replaces 1–10) | Present | `items.py:50-60`; enforced at `crafting_authority.gd:233-234` and `:414`; UI clamp at `crafts_page.gd:161`. With no furnace the cap is 1 | — |
| Impurity filter: % of impurities removed automatically | Differs | `filter` is added straight to the quality roll (`crafting_authority.gd:242`), and the values are tiny (0.03–0.10) | Define it as the spec means (for example, cut toxicity or impurity by the %), then retune (§11) |
| Element affinity: +5 % quality chance for that element's recipes | Missing | No `element` on furnaces or recipes | Add `element` to furnaces and recipes |
| Yield chance: +1 pill, 5–15 % | Present | `crafting_authority.gd:263`; values 5–15 % (`items.py:50-60`). Bronze has 5 % where the spec gives none (§11) | Set bronze yield to 0 |
| Nine-Dragon Cauldron (Drowned Shrine sealed vault, Spirit Awakening 3) reaches Grain/Halo/Soul on any fire; no other furnace changes what a fire allows | Differs | The any-fire rule is present (`named: true`, `crafting_authority.gd:315`; test `:820`). The source is wrong: it is "Alchemist Fen's", the reward for *Horns for the Furnace* at **Heaven Glimpse 3**, chapter 11 (`story.py:1146-1148`). The sealed vault exists (`world.py:1213-1214`, SA3) but drops generic `chest_dungeon` | Move the cauldron into the `ds_abbots_sanctum` vault, gated at SA3. Stats in §11 |
| Each pill rolls 0–9 gold lines by quality [v0.9] | Partial | Rolled (`crafting_authority.gd:260, 323-325`), but **lost on storage**: `pill_entry` drops `marks` (`inventory_authority.gd:207-213`) | Copy `marks` in `pill_entry` and in the overflow at `:197` |
| Marks by quality: Flawed 0, Common 0–1, Fine 1–2, Superior 2–4, Perfect 4–6, Grain 6–7, Halo 8, Soul 9 | Differs | `stats.py:298-299`: fine [1,3], superior [2,5], perfect [4,7], grain [6,8], **halo [7,9]**, soul [9,9]. Rolled inclusively with `randi_range` | Set fine [1,2], superior [2,4], perfect [4,6], grain [6,7], halo [8,8] |
| Each line gives +2 % effect | Present | `pill_potency` (`inventory_authority.gd:220-223`), `per_line 0.02` | It has no effect until the marks bug is fixed |
| Stacks merge only with the same marks | Present | `stack_key` includes marks (`inventory_authority.gd:216-217`) | — |
| A Halo or Soul result triggers a room-wide cloud, a toast and NPC barks [v1.0] | Present | `world.gd:397-409` (cloud fx, floating title, barks within 700 px); `hud.gd:476` rare-pill toast | — |
| Pill tribulation (6th mini-game screen; Heaven grade and above; Halo/Soul roll) | Missing | The mini-game is 3 strikes (`curves.json` `craft_step.steps 3`), not 5 screens | Add it (v1.0). It also needs S15's five named screens (Extraction and the rest), which do not exist |
| Tribulation: 3 bolts +2 per grade above Heaven (≤9); all blocked holds the result, with a 10 % chance of +1 tier; a miss drops it to Perfect; uses the crafting stream | Missing | — | Add |
| Pill Soul flight: one timing tap; a miss makes it Halo, not a lost batch | Missing | — | Add |

## 4. S44 · Recipes and knowledge

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Herb nature: hot/cold/neutral; hot moves the Extraction band up 8 % of its range, cold down [data v0.8] | Missing | No `nature` on herbs (`data/items.json`). There is no Extraction screen: the band is placed at random (`crafts_page.gd:175-176, 194-195`) | Add `nature`. Make the band offset depend on nature |
| Recipe slots marked Principal, Minister, Assistant, Envoy | Missing | `recipes.json` keys: craft, default, grade, id, inputs, outputs, pet_food, requires_ranks, time_s, xp | Add `roles` (or define them by input order) |
| Alchemy Dao tier 5 substitute must match role and nature | Missing | The substitute exists as text only: "Substitute one ingredient per recipe", with effect `{}` (`techniques.py:109`) | Build the substitution with a role and nature check |
| Pairs in `herb_conflicts.json` cause a furnace blast: minor body injury, furnace durability −10, batch lost [v0.9] | Missing | No conflicts file and no blast. Furnaces have no durability | Add the file, the blast in `craft()`, and furnace durability |
| Ancient recipes split into 3–5 pages across dungeons and secret realms | Missing | Recipes are learned whole (`apply_learn_recipe`, `crafting_authority.gd:164-170`) | Add |
| Deduce with pages missing costs one set of ingredients; success 20 % per page + 10 % per Alchemy Dao tier above 3, cap 95 % | Missing | — | Add |
| Experimentation: 2–4 known herbs; a hidden-recipe match teaches it | Missing | `recipe_check` needs a known recipe (`crafting_authority.gd:186-189`) | Add, with `hidden` recipes |
| Otherwise a Murky Pill (toxicity only; sells for 1 tael) | Missing | No `murky_pill` | Add |
| Attempts logged in the Codex, account-shared, so none repeat | Missing | — | Add |
| Alchemist Guild: Stoneford guild hall, Guildmaster Tang [v0.8 Adept] | Missing | Artisan Row exists (`world.py:640`), with no hall. No Tang NPC; there is an unrelated `innkeeper_tang` (`npcs.json`) | Add the hall and NPC. Pick a name that doesn't clash |
| Adept exam: 5 Healing Pills at Fine+ in 3 min | Missing | — | Add |
| Expert exam: 3 Foundation Guard Pills at Superior+ in 5 min | Missing | — | Add |
| Passing gives a badge title, the guild shop and the commission board | Missing | No guild titles (`titles.json`) | Add |
| Commissions: 3 NPC orders a day, paid in taels or contribution | Missing | The `contribution` currency exists (`currencies.json`) | Add |
| Daily payout capped at 20 % of the zone's daily income target (S39) | Missing | No income target is defined anywhere (`grep income` is empty) | Define the S39 targets first |
| Formation and Artifact guilds follow in S49 | Missing | Not in scope for P2 | — |

## 5. S44 · New forms and auto-refine

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Poison Pills: thrown from quick-use, area DoT, poison family | Missing | The throwable framework exists (G2 `throw` effect, `items.py:322-330`), and so does the `poison` status (`stats.py:216`). No poison pill | Add Viper Smoke Pill on the throw effect with an area DoT |
| Weapon oils: 5-min element-on-hit buff (Viper = poison, Ember = burn) [v0.9] | Missing | grep `oil` finds only materials | Add the oil form and the on-hit status buff |
| Liquid medicines: no Condensation screen, ½ toxicity, go to a Draught slot, vanish 10 min after crafting | Missing | No Draught slot. There is no Condensation screen either | Add |
| Medicinal baths: Bath station in retreat rooms and cave abodes; uses the seclusion slot; big body XP; clears residue; injures if herb grade > body tier [v0.9] | Missing | No station, focus or items | Add a `bath` seclusion focus and a station object |
| Qi Flow Pill: +20 % accumulation for 60 min, then +15 toxicity | Missing | — | Add |
| Eat raw: any herb, 30 % of its reference pill at ×2 toxicity [v0.8] | Present | All 9 herbs carry `raw` (`items.py:172-186`), e.g. willow moss heal 0.09 = 30 % of the Healing Pill's 0.3, at toxicity 10 = 2×5. Flow at `inventory_authority.gd:418-421`; UI verb "Eat raw" (`inventory_page.gd:175`). The strings say "a third" (`ui_strings.json:227`), not 30 % | Optional wording fix. (Beast cores eaten raw and counted as resistance/foundation are an extension) |
| Auto-refine grants 25 % of manual profession XP | Present | `crafting_authority.gd:430-433` | — |

## 6. S44 · Data files and fields

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| New `flames.json` | Differs | Flames are `treasure` items in `items.json` (`items.py:336-339`), and the fire bands live in `grades.json` `pill.fires` (`stats.py:293-296`) | Split them into `flames.json` (id, zone, source, band, rare) or document the layout |
| New `herb_conflicts.json` | Missing | — | Add |
| New `guilds.json` (exams, commissions, shop) | Missing | — | Add |
| `pills.json` gets `family`, `marks`, `soul_effect` | Missing | There is no `pills.json`; pills live in `items.json` under `pill: {mark, toxicity, cause, group}`. There is no `family` or `soul_effect`. Mark ranges are global in `grades.json` | Add `family` and `soul_effect` to pill rows, and put mark ranges where the spec says |
| `items.json` herbs get `nature` | Missing | Herbs carry only `use`/`raw` | Add |
| `recipes.json` gets `roles`, `fragments`, `hidden` | Missing | Keys listed in §4 | Add |
| Furnaces in `artifacts.json` (slot `tool_furnace`) | Differs | In `items.json` as `type: tool` with a `furnace` dict. `artifacts.json` slots: boots, cape, gourd, hat, robe, talisman, trousers, weapon | Move them to artifacts with the `tool_furnace` slot |

## 7. S44 · UI

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Furnace screen: Fire selector | Present | `crafts_page.gd:114-120` (locked fires show a reason) | — |
| Furnace screen: batch cap from the furnace | Present | `crafts_page.gd:108-111, 161` (`furnace_stats` string) | — |
| Pill tooltip: marks | Partial | Drawn (`inventory_page.gd:88, 130, 157-158`), but always 0 because of the marks bug | Fix `pill_entry` |
| Pill tooltip: resistance multiplier | Missing | The tooltip shows toxicity and potency only (`inventory_page.gd:147-163`) | Add a "works at N %" line from `resistance_factor` |
| Pill tooltip: "ignores resistance" on Grain | Missing | — | Add |
| Foundation tab: share bar and residue | Differs | Both are on a new **Heart** tab (`cultivation_page.gd:12, 107-161`). The Foundation tab (`:87`) is body and meridians only | Move them to Foundation, or amend the spec |
| Guild page in Crafts | Missing | — | Add |
| Codex: flame pages | Present | `story.py:1783-1787`, plus `furnaces_and_fire` | — |
| Codex: experiment pages | Missing | — | Add |

## 8. S44 · Tests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Resistance arithmetic and decay at a major breakthrough | Differs | `rules_tests.gd:728-737` tests the per-dose rule (100/80/67 %) and a −1 dose decay | Rewrite for 5 doses per count and count−1 then halve |
| Foundation share at 29 % and 31 % | Differs | `rules_tests.gd:761-766` uses 20 % then 50 % | Add 29/31 boundary cases |
| Residue caps at −10 % and clears only by the listed paths | Partial | 2 % penalty, Purging and flawless-data checks (`:751-759`, `:855`). No cap test, and no Settle −5/h or bath test | Add a cap test and a test for each clear path |
| Fire gates Grain, Halo and Soul | Present | `rules_tests.gd:816-825` | — |
| Furnace batch cap | Partial | Checks the value only (`:815`), not that `refine` refuses count > batch | Assert the `batch` failure |
| Blast on each listed conflict | Missing | — | Add |
| Deduce probability | Missing | — | Add |
| Experiment log prevents repeats | Missing | — | Add |
| Tribulation and Soul-catch outcomes under a fixed seed | Missing | — | Add |
| Pills never decay; liquids expire at 10 minutes | Missing | — | Add |
| (implied) data validation of families, natures, conflicts and furnaces | Missing | `data_validation.gd` only checks `use_action` names (`:152`) | Add schema checks |

## 9. Part 8 · Pill families (pills.json `family`)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Accumulation: Qi Gathering Pill | Differs | Family is named `qi` (by `add_progress`) | Rename it to `accumulation` in a `family` field |
| Accumulation: Qi Flow Pill | Missing | The pill does not exist | Add |
| Body: Bone Strengthening Pill | Present | `add_body_xp → body` | — |
| Insight: Clear Mind Pill | Differs | Its effect is `add_modifier insight_rate` (`items.py:123-124`), so the build gives it **no family** | Set `family: insight` |
| Soul: Soul Soothing Pill | Present | `add_soul → soul` | — |
| Breakthrough support: Foundation Guard, Cleansing (resistance plus the two-failure rule) | Partial | The two-failure rule is present. There is no resistance family (`use: []`) | Set `family: breakthrough_support` and apply its factor to the support's risk step (define how) |
| Exempt: Healing, Qi Restoration, Purging, Viper Antidote, Tiger Blood, Meridian Reversal, Method Conversion, Qi Refining, Mind Lake Opening, Sage Condensing | Present | None of them has a family effect kind | Make it explicit with `family: none` |
| (not in spec) raw herbs and beast cores count toward families | Differs | `pill_family` also covers `raw`/`core` (`progression_rules.gd:115`) | Confirm with the spec owner |

## 10. Part 8 · Herb natures, recipe roles and conflicts

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Willow Moss neutral, Riverreed Ginseng hot, Ember Pepper hot, Mist Lotus cold, Cloudtop Orchid cold, Soulbell Flower neutral | Missing | All 6 herbs exist (`items.json`); none has `nature` | Add `nature` (and cover `frost_lotus` and `ember_cactus` too) |
| Roles follow recipe order: 1st Principal, 2nd Minister, 3rd Assistant, 4th Envoy | Missing | Recipes keep input order (`recipes.json`), but nothing reads a role | Derive roles from order, or store them |
| Conflict: Ember Pepper + Mist Lotus | Missing | — | Add |
| Conflict: Ember Pepper + Cloudtop Orchid | Missing | — | Add |
| Conflict: venom sac + Soulbell Flower | Missing | — | Add |

## 11. Part 8 · Fires and furnaces (flames.json, artifacts.json)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Charcoal: default, +0 | Present | `stats.py:293` | — |
| Earth Fire: hot-spring vent in Rapids Terraces (portable furnace at the vent), +10 %, Grain | Present | `world.py:2210`; `stats.py:294` | — |
| Beast Fire: one core of rank ≥2 per batch (guardian stone, serpent core, jade core, beast cores), +15 %, Grain | Differs | No rank gate; `pebble_core` qualifies (`crafting_authority.gd:318-321`) | Add a rank gate |
| **Mist Lantern Flame** (valley Heavenly Flame) from the **Weeping Lantern elite** in the Forgotten Monastery, absorbed once, +20 %, Halo/Soul, Codex | Differs | The valley flame is the **Cold Lamp Flame** from the **Drowned Abbot** (dungeon boss, Lv 27) on first defeat (`enemies.py:272`, `items.py:63`). The Weeping Lantern is a normal mob (`enemies.py:159`; spawns `world.py:1276`) with no elite and no flame. Sunscar Throne Ember (Tomb King, `enemies.py:219`) and Comet Tail (Rao, `:237`) are extras for later zones | Add a Weeping Lantern elite in `mp_forgotten_monastery` that drops `mist_lantern_flame`. Rename or move the Cold Lamp, or keep it as another zone's flame |
| Bronze Furnace (plain): from Mei Qing; batch 3, stability +0, filter 0 % | Differs | From Mei Qing (`story.py:431`), batch 3, band 0, filter 0, but **yield 5 %** (`items.py:51-52`) | Set yield to 0 |
| Jadeiron Furnace (Earth): forge with Jadeiron ×8, Riverstone ×6, crab shell ×4; batch 5, stability +5 %, filter 10 %, yield 5 % | Differs | Named **Earth-Vein Furnace**; inputs **Bronze Furnace ×1, Jadeiron ×12, Riverstone ×8** (smithing adept) (`economy.py:245-246`); batch 5, band 5 %, **filter 3 %, yield 8 %** (`items.py:53-54`) | Rename to `jadeiron_furnace`, use the spec inputs (no bronze furnace consumed) and set filter 0.10, yield 0.05 |
| Cloudsteel Furnace (Heaven): Cloudsteel ore ×8, cloud feather ×4, serpent scale ×4; batch 8, +8 %, filter 20 %, yield 10 % | Differs | Named **Cloud-Pattern Furnace**; inputs **Earth-Vein ×1, Cloudsteel ×12, cloud feather ×6** (`economy.py:247-248`); band **10 %**, filter **6 %**, yield **12 %** | Rename and retune |
| Mistjade Furnace (Mystic): Mystic ore ×6, roc feather ×4, vulture plume ×4; batch 10, +10 %, filter 30 %, yield 15 % | Differs | Named **Mystic Tripod**; inputs **Cloud-Pattern ×1, Mystic ore ×12, roc feather ×4** (`economy.py:249-250`); band **15 %**, filter **8 %**, yield 15 % | Rename and retune |
| Nine-Dragon Cauldron: Drowned Shrine sealed vault (SA3); batch 8, stability +12 %, any-fire Grain/Halo/Soul, Water affinity | Differs | Quest reward from Alchemist Fen at Heaven Glimpse 3 (`story.py:1146-1148`); **batch 10, band 20 %**, filter 10 %, yield 15 %; no affinity (`items.py:59-60`) | Place it in the vault. Set batch 8 and band 0.12. Add `element: water` |

## 12. Part 8 · New pills, medicines and baths

All ingredient items exist in `items.json`: venom_sac, viper_fang, river_mud, toad_oil, jade_scale, leech_oil, tortoise_plate, mole_claw, hound_fang, ape_fur, cloud_feather, lizard_scale, jade_core, frog_leg, boar_hide, prayer_beads, rat_tail, lantern_wick and river_minnow. None of the outputs exist.

| Item | Status | Evidence | Change needed |
|---|---|---|---|
| Murky Pill (—, no effect, toxicity 8, from any failed experiment) | Missing | — | Add |
| Qi Flow Pill (Earth, +20 % accumulation for 60 min then +15 toxicity; Riverreed Ginseng 100 yr ×1, jade scale ×2, leech oil ×1) | Missing | — | Add the item, the recipe and a delayed toxicity effect |
| Viper Smoke Pill (Common, thrown cloud, 4 % max HP/s for 5 s, r 90; venom sac ×2, viper fang ×1, river mud ×1) | Missing | — | Add |
| Viper Oil (Common, 5 min, poison on hit 20 %; venom sac ×1, toad oil ×1) | Missing | — | Add |
| Ember Oil (Common, 5 min, burn on hit 20 %; Ember Pepper ×2, toad oil ×1) | Missing | — | Add |
| Riverreed Draught (Common liquid, +30 % HP and cures a minor body injury, lasts 10 min, toxicity 2; Riverreed Ginseng 10 yr ×1, River Minnow ×1) | Missing | — | Add |
| Copper Body Bath (Common, +600 body XP, residue −10, toxicity 5; tortoise plate ×2, mole claw ×2, Willow Moss ×4) | Missing | — | Add |
| Marrow-Washing Bath (Earth, +1,500 body XP, residue −20, toxicity 8; Riverreed Ginseng 100 yr ×1, hound fang ×3, ape fur ×2, Mist Lotus ×1) | Missing | — | Add |
| Beast Marrow Washing Pill (Heaven, rerolls one pet aptitude, toxicity 0; cloud feather ×2, lizard scale ×3, jade core ×1) | Missing | Pet aptitude is Partial (gap_audit row 38) | Add with S46 |
| Beast Revival Pill (Earth, clears a pet's Grievous Wound; frog leg ×2, boar hide ×1, Willow Moss ×2) | Missing | No Grievous Wound yet (G3) | Add with S46 |
| Purifying Offering (Earth, lets you tame a demonic beast; Mist Lotus ×1, prayer beads ×1, rat tail ×3) | Missing | Only `bonding_offering_*` exist | Add |
| Calm Heart Incense (Earth, heart demon −10; prayer beads ×1, lantern wick ×2, Mist Lotus ×1) | Partial | The `add_heart_demon` effect kind exists. `myriad_year_calm_incense` gives −40 and `calm_incense` gives composure +30 (`items.json`). No −10 craftable incense | Add the item and recipe |

## 13. Part 8 · Alchemist Guild (guilds.json, Stoneford Artisan Row, Guildmaster Tang)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Location: Stoneford Artisan Row | Partial | The `sf_artisan_row` room exists (`world.py:640`) | Add the guild hall object and NPC |
| Guildmaster Tang | Missing | Only `innkeeper_tang` exists | Add (with a distinct id) |
| Adept: 5 Healing Pills Fine+ in 3 min → "Guild Adept" title, guild shop (Earth recipes, Jadeiron Furnace blueprint), commission board | Missing | No guild title, shop or blueprint item | Add |
| Expert: 3 Foundation Guard Pills Superior+ in 5 min → "Guild Expert", Qi Flow Pill recipe, higher commissions | Missing | — | Add |
| Master (Azure Expanse): defined in v1.1 | Missing | The build is on 1.1, so it is due | Define and add |
| Commissions: 3/day from known recipes, paid 1.2 × price in taels or contribution, daily cap 20 % of the zone's income target | Missing | No income target (S39) | Add after S39 targets exist |

## 14. Coverage matrix (report rows → S44)

| Gap report row | Status | Evidence | Change needed |
|---|---|---|---|
| Lifetime pill resistance (fields v0.5, rule v0.8) | Differs | §2: per-dose count, −1 decay, no support family, Clear Mind unfamilied | Implement the v2 rule |
| Foundation solidity | Differs | §2: rates 6 and 3 per hour; floor denominator; bath missing | Retune; add bath |
| Residual impurities (v0.8; Cleansing v0.9) | Partial | Core rule and the Cleansing clear are present; bath clear missing; Settle rate differs | Add bath; set Settle to 5/h |
| Heart-demon cost of forced breakthroughs (v0.9) | Present | §2 | — |
| Fire slot (v0.9, v1.0, v1.1–v1.5) | Differs | §3/§11: no Beast Fire rank gate; the valley flame and its source are wrong; flames missing for early Act II zones | See §11 |
| Furnaces as equipment (v0.9) | Differs | §3/§11: not instances or a slot; no enhancement, affinity or durability; names, recipes and stats differ | See §11 |
| Pill marks (v0.9) and pill cloud (v1.0) | Partial | Marks are rolled but lost (bug); ranges differ. The cloud is present | Fix the storage bug and the ranges |
| Pill tribulation (v1.0) | Missing | — | Add |
| Pill Soul flight (v1.0) | Missing | — | Add |
| Decay rule (text fix v0.8) | Partial | "Never decay" is present, but Halo growth and the Soul effect differ | See §2 |
| Herb nature and recipe roles (data v0.8, blast v0.9) | Missing | §10 | Add |
| Recipe fragments and deduction (v1.0) | Missing | §4 | Add |
| Experimentation (v1.0) | Missing | §4 | Add |
| Alchemist Guild (v0.8 Adept) | Missing | §13 | Add |
| New forms (v0.9, v1.0) | Missing | §5/§12 | Add |
| Eat raw (v0.8) | Present | §5 | — |
| Auto-refine XP (text fix) | Present | §5 | — |

## 15. Priority table (the rows that touch this packet)

| # | Requirement | Status | Evidence | Change needed |
|---|---|---|---|---|
| 1 | Define S15's undefined rules (fire, furnace, pills never decay, auto-refine XP) — v0.8 text fix | Partial | Fire, furnace, never-decay and auto-refine are all defined, but their numbers and structure differ (§3, §11). The seed-source and heart-demon parts belong to other packets (only `evergreen_heart_seed` exists) | Align with S44 |
| 2 | Lifetime pill resistance, foundation share, residue (fields v0.5, rules v0.8) | Differs | §2 | Implement the v2 numbers |
| 3 | Heart-demon meter and karma ledger (fields v0.5, rules v0.9) | Present (P2 part) | `heart_demon` 0–100, steps every 25, sources (`stats.py:114`, `progression_authority.gd:707-723`); the rest belongs to the S48/S49 packet | — |
| 13 | Associations, recipe fragments, experimentation (v0.8–v1.1) | Missing | §4/§13. The build's roadmap defers them to G5 (`gap_audit.md:198`) | Pull the guild's Adept rank forward (v0.8) |

## 16. Rules the report found named but undefined

| Rule | Status | Evidence | Change needed |
|---|---|---|---|
| Pill Grain "keeps longer" → pills never decay; Grain redefined | Present | §2 | — |
| "Rare fire or a special furnace" → fire slot and furnaces as items | Differs | Defined, but not as the v2 fires and furnaces (§11) | See §11 |
| The Reflection's heart demons need a state field | Present | `cultivator_state.gd:45`; the Trial summons one demon per 25 (`rules_tests.gd:853`) | — |
| Seeds with no seed source | Not this packet | Only `evergreen_heart_seed` exists | See the herbs packet (P3) |
| Auto-refine XP unstated → 25 % of manual | Present | `crafting_authority.gd:430-433` | — |

## 17. Genre staples kept out on purpose (the rows that touch pills)

| Staple | Status | Evidence | Change needed |
|---|---|---|---|
| Stat and aptitude pills sold in shops (kept out) | Present (compliant) | Shops sell cures, timed buffs and progress/support pills only (`shops.json`). The planned Beast Marrow Washing Pill must stay craft-only | Keep it out of shops when added |
| Herb rot and pill decay (kept out) | Present (compliant) | No expiry code. Liquids (10 min) will be the only exception, as the spec says | — |

## 18. Events S43–S49 (the rows owned by this packet; other rows belong to P1 and P3–P7)

| Event | Status | Evidence | Change needed |
|---|---|---|---|
| `pill_resistance_changed` (Progression; actor, values → pill tooltips, Foundation tab, risk preview) | Missing | Not emitted. Only `pill_used.resistance`. Also, Inventory owns the dose, not Progression | Emit from Progression; add to the contract |
| `foundation_changed` (Progression) | Missing | — | Emit; add to the contract |
| `residue_changed` (Progression; actor, value) | Partial | Emitted with the right owner (`progression_authority.gd:704`); not in the contract; no reactor | Add to the contract; the Heart/Foundation tab should react |
| `heart_demon_changed` (Progression; actor, value → risk preview, Heart Trial count, HUD status icon at 25+) | Partial | Emitted (`progression_authority.gd:713`) with `{actor, value, delta, source, step_crossed}`; the HUD shows a toast or log line (`hud.gd:490-493`). **No HUD status icon at 25+**, and not in the contract (the icon belongs to S48) | Add the icon; add to the contract |
| `flame_absorbed` (Crafting → Codex) | Partial | Emitted, and the Codex entry is added (`crafting_authority.gd:339-340`); not in the contract | Add to the contract |
| `furnace_blast` (Crafting → Progression blast injury) | Missing | — | Add |
| `pill_cloud` (Crafting → NPC barks) | Partial | Emitted with barks (`world.gd:397-409`); not in the contract | Add to the contract |
| `pill_tribulation_result` (Crafting → Achievements) | Missing | — | Add |
| `recipe_deduced`, `experiment_result` (Crafting → recipes known, Codex log) | Missing | — | Add |
| `guild_rank_changed`, `commission_completed` (Crafting → Economy capped pay, titles) | Missing | — | Add |

---

### Status counts (every table row above; the "Not this packet" row is excluded)

Present 43 · Differs 44 · Partial 20 · Missing 95 (202 rows).
