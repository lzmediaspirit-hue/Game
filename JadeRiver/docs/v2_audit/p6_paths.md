# Audit P6: S48 Cultivation paths, heart and heaven (v2 spec against the build)

Scope: every concrete requirement in `p6_paths.md` checked against `/home/user/Game/JadeRiver` at `796f089` (G1 follow-up; CHANGELOG head "1.1 — The Azure Expanse", G2a and G1 at top). I only read files. I ran no Godot, no tests and no build scripts.

Legend: **Present** = exists and matches. **Differs** = exists with a different name, number or behaviour. **Partial** = part of it exists. **Missing** = nothing like it.

**Counts (234 rows):** Present 26 · Differs 12 · Partial 34 · Missing 162. Of the Present rows, 10 are kept-out staples that the build respects. The only S48 system with real content is the G1 heart-demon meter, and its numbers differ from v2.

Milestone note: the build is already v1.1 (CHANGELOG line 3). Every S48 item tagged v0.8–v1.1 is therefore **due or overdue**. Only v1.2 items (Confucian, Hollow-Touched, the top of the Sword line) are still in the future.

Short paths used below: `PA` = scripts/simulation/authority/progression_authority.gd, `PR` = scripts/simulation/rules/progression_rules.gd, `CS` = scripts/simulation/state/cultivator_state.gd, `CA` = scripts/simulation/authority/combat_authority.gd, `WA` = scripts/simulation/authority/world_authority.gd, `CP` = scripts/ui/pages/cultivation_page.gd, `RT` = tests/rules_tests.gd.

---

## 1. S48 ownership: fields, transients, intents, emits

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `heart_demon` 0–100 on CultivatorState [field v0.5] | Present | CS:45 float; saved CS:95, clamped 0..100 on restore CS:135 | — |
| `body_tier` (mortal, copper, iron, jade, gold) | Missing | Only `body_level`/`body_xp` (CS:21-22) | Add `body_tier` string (default "mortal"), save/restore, bump `VERSION` (CS:7 is 4) |
| `core_grade` | Missing | Only `purity` 9→1 (CS:18), reset to ≤9 on entering True Qi (PA:468) | Add `core_grade` (the one-shot starting grade) and seed `purity` from it at HT9→CS1 |
| `fates[]` | Missing | none | Add an array of fate ids with their expiry ("this realm", "next tribulation", "next time") |
| `physiques[]` | Missing | The aptitude key `physique` (PA:507,521; stat_rules.gd:173) is a hidden ±% max-HP roll, not a list of physiques | Add `physiques[]`. Rename the aptitude key (e.g. `constitution`) so it does not collide with the new list |
| `vows[]` | Missing | none | Add `vows[]` (active toggles) |
| `inner_arts[]` | Missing | Secret arts are an always-on list (CS:68) | Add `inner_arts[]` slot array |
| `stances {family: id}` | Missing | Combat has a transient `stance` timer only (CA:46,385) | Add a saved dictionary of stance per family |
| `false_realm` | Missing | none | Add a realm key, "" meaning off |
| `epiphany_cooldown` | Missing | none | Add a float, saved |
| Transient `blood_essence`, `killing_intent` (not saved) | Missing | none | Keep both in the combat timeline (CA:44-46), not in the snapshot |
| Intents: choose_fate, take_body_trial, set_vow, equip_inner_art, set_stance, set_false_realm, tribulation_action | Missing | The Progression intent list PA:14-17 has none of them | Add all seven intents to ProgressionAuthority (and route tribulation_action through Combat) |
| Emit `heart_demon_changed` | Present | PA:713; payload is actor, value, delta, source, step_crossed (a superset of the spec's) | — |
| Emits fate_offered, fate_chosen, tribulation_started/_bolt/_result, core_graded, qi_deviation, epiphany, vow_broken, body_tier_reached, physique_awakened | Missing | Not emitted anywhere in scripts/ | Emit each from Progression when its feature exists |
| "Paths as layers, never class locks" | Present | Free build: meridians (CS:56), method switching (PA:805), any-family techniques. No class gate exists | — |

## 2. Paths as layers

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Body refining: named ladder Copper 18 / Iron 36 / Jade 54 / Gold 72 on body_level | Missing | `body_level` exists (CS:21). Soft body gates are 1/9/18/27 (tools/data/realms.py:27-39). No names or tiers | Add body_tiers.json and a `body_tier` gate that reads body_level |
| Each tier passed by a Temper trial (a timed stamina fight at a training ground) plus a medicinal bath (S44) | Missing | Only the Temper seclusion focus exists (PA:937-940). No baths ("bath" occurs 0 times in data/tools/scripts) | Add a `take_body_trial` room event per tier plus bath items. The tier is granted only when both are done |
| Body techniques cost HP or Composure instead of QI | Partial | A composure_cost path exists (CA:279-284), but every technique has composure_cost 0. There is no HP cost (techniques.json) | Add `hp_cost_pct` to the technique schema and to CA, then author body techniques |
| Gold Body is immune to Qi Seal | Missing | Qi Seal blocks techniques at CA:272 with no exemption | Skip the `qi_seal` check and the status when body_tier == gold |
| Tier caps the bath herb grade (S44) | Missing | no baths | Put a `max_herb_grade` on each tier row |
| Body milestone: Copper v0.9, one tier per realm after | Missing | — | Copper overdue (build is v1.1) |
| Sword: flying sword, sword swarm, Sword Intent, Sword Domain (S47) [v0.9–v1.2] | Partial | Flying Sword exists as a flight vessel (CHANGELOG G2a); the jian has a Qi arc (weapon_families.json `qi_arc_discount`); Sword Dao exists. No sword release/swarm, `sword_intent` or Domain ("sword_intent" occurs 0 times) | Implement S47 Sword Release and Intent (needed by the Sword Heart Inner Art, row 12.4) |
| Soul: illusion; soul search on elites (lore, extra drops); a sense lock that negates evasion; Spirit as a main-stat build [v1.0] | Partial | Two soul techniques, mirror_mind_spike (SA1) and soul_lantern_ward (SA5), in techniques.json. The Sense pulse is at WA:214. Spirit feeds Soul, Sense and Will (CP:93). No illusion, soul search or sense lock | Add three soul techniques (illusion, soul_search, sense_lock with `ignore_evasion`) and Spirit scaling on soul damage |
| Blood (demonic), opt-in: techniques spend 5–15% HP; lifesteal scales with Blood Dao; kills fill blood_essence; heart-demon gain ×2; orthodox reputation drops [v1.1] | Partial | Only the rare Blood Dao exists, opened by Matriarch Tie (daos.json `blood`, tools/data/techniques.py:120). No HP-cost techniques, no lifesteal ("lifesteal" occurs 0 times), no blood_essence, no heart-demon multiplier (PA:707-714 applies the amount raw) | Add a gain multiplier to apply_heart_demon (Blood ×2, Hollow-Touched ×1.5). Add blood techniques, lifesteal and a reputation hit |
| Buddhist: vows (+10% defence or healing); merit from sparing and healing (S49); a Golden Body buff; breaking a vow adds 15 heart demon [v1.1] | Partial | Merit exists (CS:46), but it comes from story choices and ten "helping" quests (tools/data/story.py:528-536,1588-1670), not from sparing or healing. No vows, no Golden Body | Add vows.json and set_vow. Add merit hooks for spar-ends (the `spar` enemy flag, CA:634) and ally heals. Add a Golden Body buff |
| Confucian: insight-scaled glyph techniques; Righteous Qi +25% vs Hollow and demonic [v1.2] | Missing | "righteous" occurs 0 times. Hollow enemies exist | Future (v1.2) |
| Music: flute and guqin families (S47) [v1.1] | Missing | weapon_families.json lists fists, gauntlets, jian, spear, short_blade, staff, bow only | Add the two families (S47) |
| Poison: player poison techniques; Poison Body, where own toxicity above 50% converts to on-hit poison [v1.1] | Partial | Toxicity and tolerance exist (PA:690-697). A `poison` status exists (hazards.json poison_mist). No player poison technique. Toxicity is absolute against a tolerance of 30 base, not a % | Define "50%" as toxicity ≥ 50% of toxicity_tolerance. Add poison techniques and an on-hit poison proc |
| Formation, talisman and puppet caster: quick-deploy Array Plates with Formation-Dao damage scaling; attack talismans (S47); one combat puppet from Cloud Stride 5 in a pet slot [v0.9–v1.0] | Partial | The Array Plate is a consumable +15% defence buff (tools/data/items.py:357-358), not deployed and with no damage. One talisman treasure exists (G2a Heaven Splitting). Puppetry opens at CS5 (tools/data/story.py:478), but its puppets are Worker/Carrier idle puppets (tools/data/crafts.py:23-29). There is no combat puppet | Add attack array plates scaled by Formation Dao, and a combat-puppet blueprint that occupies `active_pet` |
| Sect role variants: damage and support variant per sect signature line, plus a 3-branch × 5-node tree bought with contribution [v0.9] | Missing | sects.json entries have no signature, tree or line fields. Contribution exists | Add signature lines and trees to sects.json and a buy-node intent |

## 3. The heart-demon meter [field v0.5; rules v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| +10 per method switch | Present | stats.json heart_demon.method_switch 10; PA:820; RT:781 | — |
| +5 per breakthrough with 2 or more support pills | Present | PA:414-415 (`forced_supports` 2, `forced_breakthrough` 5) | See side finding Z1: spent or wrong-event supports still count toward the 2 |
| +15 per broken vow or oath | Missing | No vows and no oath mechanic (the only "oath" is a quest name, story.py:1546) | Add `vow_broken` and `heart_demon.vow_break: 15` |
| +3 per grave wound | Present | PA:565 on `player_gravely_wounded` (key `death` 3). The CHANGELOG calls it "a defeat" | Optionally rename the key to `grave_wound` |
| +1 per 10 sin (S49) | Differs | `per_sin` 0.2 means **+1 per 5 sin** (tools/data/stats.py:115; PA:723). RT:798 expects 25 sin → +5 | Set per_sin 0.1 and change the test to 25 sin → +2.5 |
| Myriad-Year Calm Incense −20 | Differs | **−40** (tools/data/items.py:287-288 "Clears Heart Demons (-40)"; RT:788; CHANGELOG "clears 40") | Set the amount to −20 and fix the item text, the test and the CHANGELOG |
| Meditation −1 per 5 minutes | Differs | `meditate_drain_per_min` 0.25 = **−1 per 4 min**, and doubled at a Qi spring (PA:138,167-168) | Set 0.2/min. Decide whether the spring should double it (the spec does not say so) |
| Passing the Heart Trial −30 | Missing | The Trial's `on_complete` only records event_passed (tools/data/world.py:1319) | Add `{"kind":"add_heart_demon","amount":-30}` to on_complete |
| Buddhist merit milestones drain | Missing | Merit only eases a breakthrough (PR:148-151). It never lowers the heart demon | Define milestones (e.g. each 100 merit) and the drain amount |
| Each 25 points adds +1 risk step at major breakthroughs (S05) | Present | PR:145-146; PA:367,380-381; RT:784 (55 → 2 steps) | — |
| The Reflection gains one Heart Demon add per 25 | Present | WA:830-835 spawns `ev.heart_demons` × steps; world.py:1318; RT:853 | — |
| Risk-word ceiling "Severe" | Present | PR:106-108 clamps 0..3; risk_words low/moderate/high/severe | — |

## 4. Heavenly tribulation [v1.0]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| From Cloud Stride on, every major breakthrough summons a tribulation cloud in the room | Missing | A major breakthrough is a 3 s channel and a roll (PA:391-441) | Add a tribulation room event, started from `_tick_channel` when from ≥ cloud_stride_9 |
| The Heart Trial stays the set piece into Cloud Stride | Present | realms.py:41-42 (event heart_trial); world.py:1314-1320 | — |
| Bolts: 3 into SA, 6 into HG, 9 into Sage, then 9 × waves (2 into SS, +1 wave per realm after) | Missing | No tribulations.json. The realm keys match (cloud_stride_9, spirit_awakening_9, heaven_glimpse_3, sage_3 in realms.json) | Generate tribulations.json from realms.py |
| +1 bolt per 25 heart demon and +1 per 100 sin | Missing | — | Add a formula in PR (reuse heart_demon_steps) |
| Damage 20% max HP × (1 + sin/500) × (1 + heart demon/200) | Missing | — | Add to PR, applied by Combat |
| Telegraph ring 1 s before; dodge (S43) or guard −50%; cover does not help | Missing | The lightning hazard has a warn phase to reuse (hazards.json `lightning`, cycle [2.5,1.2,0.3,6.0], aim player) | Spawn a lightning strike per bolt with a 1.0 s warn, guard ×0.5, ignoring `shelter` |
| A tribulation treasure consumable absorbs one bolt | Missing | none | Add an item with `absorb_bolt` |
| 0 HP during the tribulation is a breakthrough failure (Bodily failure), not a grave wound | Partial | failures.json `bodily_failure` exists; nothing links a 0-HP tribulation to it | Intercept defeat during the event and call `_fail_breakthrough(c,"bodily_failure")` |
| Breakthrough stream for bolt timing, combat stream for positions | Partial | Both streams exist (PA:428 `breakthrough`, PA:561 `combat`) | Use them as specified |

## 5. Core Forging grade [v1.0]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| HT9 → CS1 sets a one-shot starting purity grade instead of always 9 | Differs | Always 9: `cu.purity = mini(cu.purity, 9)` (PA:468) | Compute the grade at that step and emit `core_graded` |
| Point: room element matches the method | Partial | Room `element` (world.py rooms) and method `affinity` (methods.json) exist | Compare them |
| Point: in-game night or day matches the method's Yin or Yang | Partial | `Clock.time_of_day()` exists (scripts/core/clock_service.gd:47). Methods have no `yin_yang` | Add `yin_yang` to methods.json |
| Point: Composure full | Partial | The Composure pool exists (unlocked QU1, story.py:446) | Check that `pools.composure >= max` |
| Point: residue 0 | Partial | `residue` (CS:44) | Check it |
| Point: a Heavenly-Flame pill taken within the hour | Missing | Heavenly Flames are absorbed fires (G1), and there is no such pill ("flame_pill" occurs 0 times) | Add the pill, or reword the point to "a Heavenly Flame absorbed" |
| Each point counts at 80% on the breakthrough stream | Missing | — | Roll each point with `Rng.stream(id,"breakthrough")` |
| Starting grade = 9 − points, floor 5 | Missing | — | Add to PR |
| A flawless Heaven's Cleansing gives one more (floor 4), "which keeps the existing grade-8 bonus" | Differs | A flawless Cleansing clears residue and sets flag `cleansing_flawless` (world.py:2118; WA:875-877). **There is no grade-8 bonus in the build** | Read `cleansing_flawless` as +1 point (floor 4). Rewrite the spec sentence, because the bonus it claims already exists does not |

## 6. Breakthrough fates [v0.9]

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| On each major breakthrough roll 3 fate cards from fates.json on the breakthrough stream; pick 1 | Missing | `_advance` (PA:446-485) emits only breakthrough_succeeded and realm_changed | Offer 3 distinct cards after a major success, then `choose_fate` |
| Most cards mix a gift and a cost | Missing | — | See §13 |

## 7. Named roots and physiques

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Affinities within ±15% cap [v0.8] | Present | roll ±0.10, origin nudge +0.05, clamp ±0.15 (PA:518-524) | — |
| Root grade names: Heavenly (one element > +10%), True (2–3 at ≥ +5%), Mixed (4–5), Mutated (Thunder, Ice or Wind) [v0.8] | Missing | Raw values only | Add `root_name()` to PR |
| Mutated needs a Thunder or Ice affinity | Differs | Only water, wood, fire, earth, metal and wind are rolled (PA:521). Thunder and ice are never rolled, so Mutated can only come from wind. Heavenly (> +10%) is reachable only through the origin nudge | Add element_thunder and element_ice aptitudes, or narrow Mutated to Wind. State the Heavenly odds |
| physiques.json: 6–10 event-earned physiques, each with a drawback [v1.0] | Missing | No file. 6 are listed in Part 8, which is the minimum | See §14 |

## 8. Qi deviation, epiphany, costly arts, hidden cultivation

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Qi Deviation [v0.9]: at Severe risk or with a Poor method, a failure also triggers a 10-minute debuff that swaps random technique elements | Missing | The inputs exist: risk word (PR:153) and `method_compatibility` "poor" (PR:41-48). `_fail_breakthrough` (PA:487-503) has no deviation step | Add a `qi_deviation` status (600 s) and an element override in CA |
| Epiphany [v1.0]: 0.2% per insight tick during Contemplate or varied combat, weighted by Insight; 60 s ×5 insight; chance of a free technique variant; 2 h cooldown | Missing | Insight ticks exist (PA:634-658). Contemplate exists (PA:44-47) | Roll in `apply_insight`. Add a buff and `epiphany_cooldown` |
| Blood Burning: +50% damage 10 s, costs 30% HP, gives a body injury [v1.0] | Missing | The 7 secret arts are utilities (secret_arts.json) | Add it as an active secret art |
| Self-Detonation of a treasure: ends a fight, severe soul injury | Missing | Treasures exist (G2a). There is no detonate. Soul injury exists (injuries.json `soul`) | Add a detonate action per treasure that applies soul severity 3 |
| Enemies: telegraphed nascent-soul self-detonation boss mechanic | Missing | Boss phases exist (summon, enrage), no detonation | Add a boss phase kind |
| Concealment shows a false realm badge up to two major realms lower; changes dialogue; doubles bandit ambush odds [v1.0] | Partial | The Concealment secret art (SA2; techniques.py:146) only halves aggro (enemy_brain.gd:48). No badge, no ambush system ("ambush" occurs 0 times) | Add `false_realm`, a nameplate override and a dialogue requirement kind. Ambushes need S49 |
| Killing Intent: +1 per kill within 10 s, max 10, +1% crit each; at 10 stacks weaker enemies hesitate 0.5 s [v1.0] | Missing | No streak tracking | Add a transient stack in CA and a hesitation hook in enemy_brain |

## 9. Inner Arts, technique grades, stances, combos, soul escape

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Inner Arts [v0.9]: equippable passive slots from manuals, some weapon-linked | Missing | Secret arts are always on. The Techniques page has only Combat and Secret tabs (techniques_page.gd:9) | Add inner_arts.json, slots and `equip_inner_art` |
| Slots: 2 at QU1, 3 at HT1, 4 at SA1 | Missing | The unlock-driven slot pattern already exists for techniques (PR:194-198) | Add `inner_art_slot_count()` the same way |
| Technique grades Common / Earth / Heaven (+0 / 10 / 20% base) | Missing | Methods carry `grade` (methods.json: common, earth, heaven). Techniques carry none (techniques.json field list) | Add `grade` to techniques.py and apply the multiplier in CA damage |
| One stance toggle per family; Willow Leaf Parry is the jian's | Differs | Willow Leaf Parry is a slotted technique (damage_type "stance", `stance_s` 2.0, 10 Qi, 8 s cooldown) that opens a 2 s counter window (CA:519-520,684). It is not a toggle. There is no per-family stance | Add a `set_stance` toggle per family; decide whether WLP stays a technique |
| Combo pairs: A then B within 1 s adds a follow-up hit (pairs in data) | Missing | "combo" in the build means the basic-attack chain (weapon_families.json `combo`; CA:230-257) | Add combos.json. Track the last technique and its time in the timeline |
| Nascent-soul escape [v1.1]: from Sage, dying costs 5% progress instead of 10%; the soul flees to the shrine | Missing | Loss is 10% everywhere (tools/data/stats.py:101; PA:555) | Use `death.progress_loss_sage` 0.05 when at_least(sage_1) |

## 10. Data

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| New fates.json | Missing | not in data/ | Generate from a new tools/data/paths.py |
| New physiques.json | Missing | not in data/ | Same |
| New body_tiers.json | Missing | not in data/ | Same |
| New vows.json | Missing | not in data/ | Same |
| New inner_arts.json | Missing | not in data/ | Same |
| New tribulations.json | Missing | not in data/ | Same |
| New combos.json | Missing | not in data/ | Same (all 12 technique ids already exist) |
| techniques.json gets `grade` | Missing | 30 entries, no grade | Add |
| techniques.json gets `stance` | Missing | Only `stance_s` on willow_leaf_parry | Add a `stance` field (or put stances in their own table) |
| methods.json gets `yin_yang` | Missing | 9 methods, fields id, grade, ceiling, affinity, rate, capacity, source… | Add yin/yang/neutral. combat_rules.gd:19 already understands yin and yang |

## 11. UI

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Heart-demon ring on the Foundation tab, red when it adds risk | Differs | A **bar** on a **separate "Heart" tab** (CP:13,107-125). The bar is always crimson; only the text under it turns red at ≥1 step. The Foundation tab shows meridians only (CP:87-104) | Move it to the Foundation tab as a ring, or amend the spec to "Heart tab". Colour the ring by `heart_demon_steps > 0` |
| Fate-card picker after the breakthrough scene | Missing | — | New picker page opened on `fate_offered` |
| Tribulation HUD (bolt counter, telegraph rings) | Missing | — | HUD counter plus ring visuals |
| Core Forging preparation checklist in the Breakthrough dialog | Missing | breakthrough_page.gd:16-52 shows requirements, supports and reasons only | Add 5 checklist rows when from == heart_tempering_9 |
| Root name on the Aptitude tab | Missing | The Aptitude tab exists but prints raw values (character_page.gd:54-60) | Print the root name above the rows |
| Inner Arts slots on the Techniques page | Missing | techniques_page.gd:9 | Add a third tab |
| False-realm selector in Concealment | Missing | Concealment is text on the Secret Arts tab (techniques_page.gd:15-24) | Add a selector |
| HUD status icon at 25+ heart demon (event table) | Partial | Only a toast or log line when a step is crossed (hud.gd:490-493) | Add a persistent status icon while steps ≥ 1 |

## 12. Tests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Heart-demon gains, drains and risk steps at 24 and 25 | Partial | RT:776-798 covers switch +10, 55 → 2 steps, incense (−40, the wrong value), and 25 sin → +5 (the wrong rate). It does not cover forced +5, grave wound +3, meditation drain, or the 24/25 edge | Add the 24 → 0 and 25 → 1 steps; test every gain and drain at spec values |
| Bolt count formula by realm, sin and heart demon | Missing | — | — |
| Core grade from points with a fixed seed | Missing | — | — |
| Fate picker offers 3 distinct cards | Missing | — | — |
| Root naming at affinity edges | Missing | — | — |
| Qi Deviation only under its conditions | Missing | — | — |
| Vows block their actions and a break adds 15 | Missing | — | — |
| Body tier needs both trial and bath | Missing | — | — |
| data_validation for the new files | Missing | tests/data_validation.gd has no checks for fates, physiques, vows and the other new files | Validate ids, technique references in combos, and stat names in gifts and costs |

## 13. Part 8: fate cards (fates.json)

The whole deck is Missing: there is no file and no picker. The "hook" column says what the build can already express.

| Card: gift / cost | Status | Hook in the build | Change needed |
|---|---|---|---|
| Thunder-Tempered Meridians: +10% Thunder power / +5 heart demon | Missing | The Thunder element and Dao exist (elements.json parent, daos.json `thunder`). The `elemental_power` stat exists | Element-conditional modifier plus apply_heart_demon(+5) |
| Hungry Dantian: +8% accumulation this realm / pill resistance +1 in every family | Missing | `accumulation_rate` stat; `pill_resistance` (CS:42) | Needs "this realm" expiry on modifiers (none exists) |
| Quiet Heart: heart demon −15 / −5% insight this realm | Missing | apply_heart_demon; `insight_rate` | Same expiry need |
| Bone of the River: +3 Body / −3 Agility | Missing | `body` and `agility` attributes (stats.json) | Permanent attribute modifier source `fate:` |
| Lucky Star: +5 Fortune this realm / none (rare) | Missing | `fortune` stat | Needs rarity weights in fates.json |
| Debt of Heaven: +1 purity grade / next tribulation +2 bolts | Missing | `purity` (CS:18). No tribulation | Needs a tribulation bolt modifier |
| Wandering Eye: reveal one hidden portal in each new room / −10% Sense radius | Missing | Hidden portals and the Sense reveal exist (WA:214; `hidden_portal_revealed`); `sense_radius` stat | Auto-reveal on room_entered |
| Iron Will: +10 Will / −5% move speed this realm | Missing | `will` and `move_speed` stats | — |
| Fox Spirit's Favour: next pet egg +10 purity / −5% max QI this realm | Missing | Pets have no purity yet (gap_audit row 34, G3) | Blocked on S46 pet purity |
| Scar of Failure: +10% breakthrough success next time / start this realm Unstable | Missing | `success_chance` (PR:157-158); stability "unstable" | Add a success bonus term |
| Blood Memory: +5% crit / heart demon +1 per kill streak of 10 | Missing | `crit_chance`. No kill streak | Blocked on Killing Intent (§8) |
| Dao Echo: +20% insight for one Dao / other Daos −10% | Missing | apply_insight (PA:634) has no per-Dao multiplier | Add a per-Dao rate map |

## 14. Part 8: physiques (physiques.json)

| Physique: earned by / gift / drawback | Status | Hook in the build | Change needed |
|---|---|---|---|
| Jade Bone: flawless Heaven's Cleansing ("existing") / +10% max HP, +10% toxicity tolerance / −5% Qi Resistance | Missing | The flawless trigger exists (world.py:2118 flag `cleansing_flawless`), but it grants only a residue clear; no physique is granted. max_hp, toxicity_tolerance and qi_resistance stats exist | Add `{"kind":"awaken_physique","id":"jade_bone"}` to on_flawless |
| Yin Vessel: meditate 10 in-game nights at Falls Pool / +15% Yin, +10% Water / −10% Fire | Missing | The Falls Pool room exists (world.py:1087) and so does `Clock.time_of_day`. There is no Yin stat (yin appears only in combat_rules.gd:19) | Night counter in `lifetime_stats` (CS:77, never written today). Define "+15% Yin" as a stat |
| Ember Heart: refine 50 Fire pills / +15% Fire / −10% Water | Missing | Recipes have no element (recipes.json: 0 of 112 have one) | Tag Fire pills |
| Stone Marrow: reach Copper Body before QU3 / +15% Physical Defense / −5% move speed | Missing | Blocked on body tiers | — |
| Cloud Lung: glide 10 km in total / +10% flight speed, −10% flight QI / −5% max HP | Missing | Flight exists (flight vessels, `flight_speed`). There is no glide and no distance counter ("glide" occurs 0 times) | Track flight distance. The spec says "glide": clarify that it means flight |
| Hollow-Touched: survive 100% Hollowing once (v1.2) / +20% Hollow Ward / heart demon gain ×1.5 | Missing | Hollowing and `hollow_ward` exist | Future (v1.2). Needs the gain multiplier (§2 Blood) |

## 15. Part 8: body tiers (body_tiers.json)

| Tier: needs / trial / bath / gift | Status | Hook in the build | Change needed |
|---|---|---|---|
| Copper: body 18 / stumps and stones, 3 min without falling below 50% HP (Willow Path) / Copper Body Bath / +5% Physical Defense; body techniques may spend HP | Missing | Body 18 is already the QK9 soft gate (realms.py:34). Stumps and lifting stones feed body XP (PA:590-602). Willow Path rooms exist (world.py:698-710). There is no bath and no HP-cost path | Trial room event, bath item, tier grant |
| Iron: 36 / Stone Guardians ×5 in one run (Pilgrim Stairs) / Marrow-Washing Bath / +10% knockback resistance | Missing | Pilgrim Stairs spawns stone_guardian at Lv 17–19 (world.py:1155-1156). There is no player knockback-resistance stat (stats.json list) | Add a `knockback_resistance` stat. Re-level the guardians for body 36 |
| Jade: 54 / the Sword Court pole trial / Heaven bath (v1.0) / injuries heal ×1.5 faster | Missing | Sword Court exists (world.py:885). The plum-blossom poles stand in the home-sect yard (world.py:2240), not in the Sword Court. `injury_recovery` stat exists | Move or copy the poles, or name the right room |
| Gold: 72 / Azure Expanse trial (v1.1) / v1.1 / immune to Qi Seal | Missing | The Azure Expanse exists (Act II). qi_seal is at CA:272 | — |

## 16. Part 8: vows (vows.json)

| Vow | Status | Hook in the build | Change needed |
|---|---|---|---|
| Mercy: no killing blow on fleeing enemies; +10% healing | Missing | Enemies flee (`flee_below`, enemy_brain.gd:78-79) | Block or break on a kill of a fled enemy |
| Plain Fare: no burst pills; +10% defence | Missing | There is no "burst pill" category on items | Tag burst pills |
| Silence: no Presence use; +10% Will | Missing | Presence exists as a level and a trial; there is no player "use Presence" action | Define what counts as "Presence use" |
| Fasting: no food buffs; +5% accumulation | Missing | Food and cooking exist | Block `food` items |
| Breaking a vow adds 15 heart demon | Missing | — | See §3 |

## 17. Part 8: Inner Arts (inner_arts.json)

| Inner Art | Status | Hook in the build |
|---|---|---|
| Riverflow Circulation: +10% QI regen | Missing | `qi_regen` stat |
| Iron Shirt: +8% Physical Defense | Missing | `physical_defense` |
| Swallow's Breath: dodge cooldown −15% | Missing | Dodge exists (CA ~354). There is no dodge-cooldown stat |
| Sword Heart: jian only; Sword Intent max 12 | Missing | No Sword Intent (§2) |
| Stone Root: guard ×1.1 | Missing | `guard` stat |
| Clear Lake: insight +10% | Missing | `insight_rate` |
| Hunter's Patience: bow draw −10% | Missing | The bow has no draw time (weapon_families.json bow keys) |
| Ember Channel: Fire techniques −10% cost | Missing | `technique_cost` is global, not per element |

Change needed: a stat or field for dodge cooldown, bow draw and per-element cost, plus Sword Intent.

## 18. Part 8: stances (one per family)

| Stance | Status | Evidence / hook |
|---|---|---|
| Willow Leaf Parry (jian, existing) | Differs | Exists as a 2 s timed technique, not a toggle (see §9) |
| Iron Horse (gauntlets): knockback immune, −20% speed | Missing | The gauntlets family exists. The player cannot be made knockback-immune (only enemies: `knockback_immune`, CA:622) |
| Coiled Dragon (spear): +15% reach | Missing | The spear family has a `reach` field |
| Low Shadow (short blade): +10% crit from behind | Missing | The short_blade family has a `backstab` field |
| Mountain Root (staff): guard +10% | Missing | `guard` |
| Still Draw (bow): +15% damage when not moving | Missing | — |

## 19. Part 8: combos (A then B within 1 s)

All 12 technique ids exist in techniques.json. The pairs, the 1 s window and the effects are Missing.

| Combo | Status | Note |
|---|---|---|
| Flowing Palm → Tiger Rush: extra shockwave | Missing | Flowing Palm is family "any"; Tiger Rush needs fists or gauntlets (CA:270) |
| Cloudpiercing Stroke → Crescent Arc: arc +1 target | Missing | Crescent Arc already pierces 8 (`max_targets` 8), so +1 target is almost meaningless. Suggest +1 pierce **and** +range, or re-spec |
| Jade Thrust → Dragon Tail Sweep: pulls targets in | Missing | There is no pull effect (only `knockback`) |
| Reedcutter Slash → Shadow Flick: bleed refresh | Missing | Reedcutter applies a 20% chance of 3 s bleed |
| Riverstone Sweep → Bell Toll Strike: stun +0.3 s | Missing | Bell Toll stuns 0.6 s at a 25% chance, so the combo only extends a proc that may not happen |
| Twin Reed Shot → Pinning Arrow: root +0.5 s | Missing | Pinning Arrow roots 1.5 s |

## 20. Part 8: tribulations (tribulations.json)

| Row | Status | Evidence |
|---|---|---|
| CS9 → SA1: 3 bolts | Missing | Realm keys exist (realms.json cloud_stride_9) |
| SA9 → HG1: 6 | Missing | spirit_awakening_9 |
| HG3 → Sage 1: 9 | Missing | heaven_glimpse_3 |
| Sage 3 → SS1: 2 waves of 9 | Missing | sage_3 |
| Each later realm: +1 wave | Missing | WM3, SL3, LT3, M3… exist |
| Modifiers +1 per 25 heart demon, +1 per 100 sin | Missing | — |

## 21. Coverage matrix rows (report: "Different paths should refine different things")

| Row | Status | Evidence |
|---|---|---|
| Body refining (v0.9 Copper) | Partial | §2, §15 |
| Sword (v0.9–v1.2) | Partial | §2 |
| Soul (v1.0) | Partial | §2 |
| Blood / demonic (v1.1) | Partial | Blood Dao only |
| Buddhist (v1.1) | Partial | Merit only |
| Confucian (v1.2) | Missing | — |
| Music (v1.1) | Missing | — |
| Poison (v1.1) | Partial | Toxicity only |
| Formation / talisman / puppet caster (v0.9–v1.0) | Partial | Buff plates, one talisman treasure, worker puppets |
| Sect role variants (v0.9) | Missing | — |
| Heart-demon meter (field v0.5, rules v0.9) | Differs | Present, but the numbers differ (§3) and 3 drains are missing |
| Heavenly tribulation (v1.0) | Missing | §4 |
| Core Forging grade (v1.0) | Missing | §5 |
| Breakthrough fates (v0.9) | Missing | §6 |
| Named roots (v0.8) and physiques (v1.0) | Missing | Hidden aptitudes only |
| Qi deviation (v0.9) | Missing | — |
| Epiphany (v1.0) | Missing | — |
| Costly secret arts (v1.0) | Missing | — |
| Hide cultivation, killing intent (v1.0) | Partial | Concealment halves aggro only |
| Inner Arts passive slots (v0.9) | Missing | — |
| Technique grades, stances, combos (v0.9) | Partial | One timed parry stance; basic-attack chains |
| Nascent-soul escape (v1.1) | Missing | — |

## 22. Priority table

| # | Priority | Status | Evidence |
|---|---|---|---|
| 1 | Define S15's undefined rules | Partial | Fire and furnace, "pills never decay" (codex.json:197), auto-refine at 25% (crafting_authority.gd:433) and the heart-demon field are done. Seed sources are not (only `evergreen_heart_seed`, items.py:295) |
| 2 | Lifetime pill resistance, foundation share, residue | Present | CS:42-44; PR:120-142; RT:727-775. (`pill_resistance_changed` and `foundation_changed` are not emitted, §24) |
| 3 | Heart-demon meter and karma ledger | Differs | §3; karma events are named differently (§24) |
| 4 | Treasure quick slot, flying sword, talisman craft, throwables | Partial | G2a: two treasure buttons, throwables, one talisman treasure, flight vessels. No talisman crafting, no sword release |
| 5 | PetState depth | Missing | gap_audit rows 31-42 (G3) |
| 6 | Herb node flags and harvest tap | Missing | No herb_* events |
| 7 | Enhancement pity, transfer, salvage | Partial | `salvage_item` exists (crafting_authority.gd:29,473). There is no pity or transfer ("pity", "transfer" and "inherit" occur 0 times) |
| 8 | Heavenly tribulation, Core Forging grade, breakthrough fates | Missing | §4-6 (fates were due at v0.9) |
| 9 | World-event scheduler and calendar | Missing | No world_event_* events |
| 10 | NPC affinity, bonds, grudges and bounties | Missing | — |
| 11 | Pet skill books, pet gear, mount slot, Spirit Beast Bag, Beast Arena | Missing | — |
| 12 | Body ladder, soul line, sect role variants, Inner Arts, stances | Missing | §2, §9 (only the base pieces exist) |
| 13 | Associations, recipe fragments, experimentation | Missing | No recipe_deduced or experiment_result |
| 14 | Alignment, Blood and Buddhist paths, new weapon families | Missing | 7 families only; no alignment |
| 15 | Rankings, territory, mortal kingdom, weather, lifespan display, insect swarm, remaining families | Missing | — |

## 23. Rules the report found named but undefined

| Rule | Status | Evidence |
|---|---|---|
| Pill Grain "keeps longer"; pills never decay; Grain redefined | Present | codex.json:197 "Pills never spoil"; grades.json pill.toxicity.pill_grain 0.5; Grain skips resistance (RT:738) |
| "Rare fire or a special furnace" | Present | grades.json `pill.fires`; furnaces as items; nine_dragon_cauldron (RT:812-818) |
| Reflection uses Heart Demons with no state field | Present | CS:45; WA:830-835 |
| Gardening seeds with no seed source | Missing | Only the Evergreen Heart seed (items.py:295). This is S45 |
| Auto-refine XP unstated (25%) | Present | crafting_authority.gd:433 `* 0.25` |

## 24. Genre staples kept out on purpose

| Staple | Status | Evidence |
|---|---|---|
| Hard lifespan and old-age death | Present (kept out) | No lifespan code |
| Stamina and energy gates, battle passes | Present (kept out) | None |
| Pet permadeath | Present (kept out) | Pets retreat (pet_authority.gd:256) |
| Enhancement that destroys or de-levels | Present (kept out) | A failure only fails to raise the level (crafting_authority.gd:454-458) |
| Sexual dual cultivation | Present (kept out) | Paired cultivation is a companion sitting nearby (CHANGELOG Phase E) |
| Player full-loot | Present (kept out) | No PvP loot |
| A full Gu path | Present (kept out) | No Gu insects (Elder Gu is only an NPC name) |
| Corpse refining, soul banners, body seizing as player powers | Partial | The **Wisp Banner** treasure is "a banner of three bound wisps" (tools/data/items.py:80). That reads close to a soul banner. Reword it as spirit-lights or formation pennants |
| Stat and aptitude pills sold in shops | Present (kept out) | Shop stock scanned: no permanent stat or aptitude items |
| Herb rot and pill decay | Present (kept out) | codex.json:197 |
| Unrestricted auto-battle | Present (kept out) | The idle "Hunt" task is capped at ¼ loot (idle_tasks.json) |

## 25. S43–S49 events (the Progression-owned rows are the S48 concern; the rest are checked by grep only)

| Event(s) | Status | Evidence / change |
|---|---|---|
| jumped, landed, wall_kicked, art_used (Movement) | Missing | None emitted ("landed" appears only as a stop_flight reason, CA:93) |
| climb_started / climb_finished | Missing | — |
| fell_out | Missing | — |
| volume_entered / volume_left | Missing | — |
| pill_resistance_changed, foundation_changed, residue_changed | Partial | Only `residue_changed` (PA:704). Emit the other two from `inventory_authority.use_item`/`_advance` and `_track_foundation` (PA:311-316), then refresh pill tooltips |
| heart_demon_changed → risk preview, Heart Trial add count, HUD icon at 25+ | Partial | Emitted (PA:713). The risk preview (PA:367-368) and the Trial count (WA:831) read state. The HUD shows a toast, not an icon (hud.gd:490-493) |
| fate_offered / fate_chosen | Missing | — |
| tribulation_started, tribulation_bolt, tribulation_result | Missing | — |
| core_graded | Missing | — |
| qi_deviation, epiphany, vow_broken, body_tier_reached, physique_awakened | Missing | — |
| flame_absorbed, furnace_blast, pill_cloud, pill_tribulation_result | Partial | flame_absorbed and pill_cloud are emitted (crafting_authority.gd); the other two are not |
| recipe_deduced, experiment_result, guild_rank_changed, commission_completed | Missing | — |
| herb_harvested, guardian_spawned, seed_found, herb_ripening, garden_raided | Missing | — |
| bloodline_awakened … pet_core_formed | Missing | — |
| beast_king_spawned, beast_tide_started, beast_tide_result | Missing | — |
| treasure_used, sword_released, sword_returned, sword_intent_changed | Partial | treasure_used is emitted by Combat (G2a) and by Progression for the Jade Tree (PA:899). There are no sword_* events |
| natal_grew … weapon_awakened | Partial | The build emits `item_salvaged` (singular, crafting_authority.gd:473), while the spec says `items_salvaged`. The rest are not emitted |
| merit_changed, sin_changed, debt_recorded, debt_called (Relations) | Differs | The build emits **karma_changed** (merit and sin together), **karma_debt_recorded** and **karma_debt_repaid**, all from **Progression** (PA:724,731,739). Merit, sin and debts live on CultivatorState (CS:46-49) | Rename or alias to the spec names, or amend the spec. Decide the owner (spec: Relations) |
| alignment_changed, affinity_changed, bond_formed, grudge_changed, hunter_dispatched, fame_changed | Missing | Only `reputation_changed` (training sect) and pet `bond_changed` exist |
| world_event_scheduled / started / ended | Missing | — |
| season_changed, weather_changed, ranking_changed, fortune_encounter, heavenly_phenomenon | Missing | — |
| Contract gate: the new events are listed in data/event_contract.json | Missing | heart_demon_changed, karma_changed, residue_changed, flame_absorbed, pill_cloud and treasure_used are all absent from event_contract.json (tools/data/contract.py:112). contract_tests only checks listed events | Add the S43–S49 rows to contract.py as they land |

## Z. Side findings (bugs and inconsistencies found while auditing)

- **Z1. Forced-breakthrough +5 counts supports that did nothing.** `start_breakthrough` consumes and counts any item with `support` (PA:405-410). It does not apply the event match or the two-fail limit that `query_breakthrough` applies (PA:354-358). Example: a `cleansing_pill` taken outside Heaven's Cleansing, or a support pill already spent, is eaten and counts toward the ≥2 that adds +5 heart demon, yet it never lowered the risk. Fix: build `used` from the same filtered list the query uses.
- **Z2. The Qi-spring doubling also doubles the heart-demon drain** (PA:138,168). The spec gives a flat −1 per 5 min.
- **Z3. The aptitude key `physique`** is a hidden max-HP roll (stat_rules.gd:173). The spec's `physiques[]` are named traits. The two would be confused in UI and saves.
- **Z4. `lifetime_stats`** (CS:77) is saved but never written. It is the natural home for the physique counters (Falls Pool nights, Fire pills refined, distance flown).
- **Z5. The spec's Core Forging text assumes "the existing grade-8 bonus"** from a flawless Cleansing. The build has none; its flawless reward is a residue clear (G1).
- **Z6. The Heart tab** exists (CP:13) where the spec says "Foundation tab". The G1 CHANGELOG documents it as a new Heart tab. Pick one and align the spec or the UI.
