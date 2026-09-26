# P9 · Bosses: phases, ground markers, enrage timers and reward loops (design and build brief)

This page is the design half of P9 in `docs/roadmap_master_ui.md` (§3 row P9; §2.1 rows M38–M40) and the plan for
finding F5 of `docs/review-v12.md` (e): "ground markers before every heavy blow, a phase card at each phase, and an
enrage timer". The research behind it is `docs/research/ui_reference_notes.md` §11 (boss presentation, sources R23–R30,
R59–R65, R71, R86, R100–R101) and §10. The references are used for mechanics only. Every name on this page is Jade
River's own.

The build follows it boss by boss (§5). It depends on P6 (the moments system, `data/moments.json`), which gives the
intro card, the phase card and the loot fountain this page asks for.

---

## 0. The brief

**Role.** You are adding boss mechanics to a Godot 4.5 offline-first game. Its simulation is split into pure rules
(`scripts/simulation/rules/`), authorities that own state and emit events (`scripts/simulation/authority/`) and brains
(`scripts/simulation/ai/`). All content is generated from `tools/data/*.py` into `data/*.json`.

**Goal.** Every boss reads as a fight with a shape: three phases, danger drawn on the ground before it lands, a room
whose ledges, water and walls matter, a clock that ends stalling, and a reason to come back.

**Definition of done (P9).**

1. Every boss has three phases (two thresholds), at least one telegraphed arena mechanic that demands movement, an
   enrage timer, a reward loop and its P6 moments (§4).
2. The shared blocks of §3: marker data in `tools/data/enemies.py`, `TelegraphRules`, scheduling in `EnemyBrain` and
   `EnemyAuthority`, resolution in `CombatAuthority`, drawing in `fx_layer.gd`, the boss bar and its incense in
   `hud.gd`, the events in `tools/data/contract.py`, the Worthy Foes record, two accessibility settings.
3. `rules_tests` `boss_suite` plays each boss headlessly to its last phase (§6.1); `valley_run`'s boss chapters still
   pass (§6.2); `data_validation`, `contract_tests` and `perf_tests` green.
4. `docs/CHANGELOG.md` entry per step, commit and push.

**Constraints.**

- Authorities write only their own state. Enemies place markers; Combat resolves damage; World moves water and
  resets objects through its room scripts; Achievement keeps the records.
- Randomness from named `Rng` streams, time from the sim clock, so a replay with the same seed places the same markers.
- No new body pose (conflict C11, `AGENTS.md`). Markers are ground drawings; bosses use their existing wind-up, hop
  and hover.
- No new HUD button (conflict C14). The incense stick sits beside the existing boss bar.
- A mechanic hurts but never kills from full health in one cycle (§2.1).

**Order of work:** data → rules → brain and authorities → drawing and HUD → strings → tests → docs.

---

## 1. The bosses today

### 1.1 The count

`data/enemies.json` has **13** entries with a boss role: 5 `dungeon_boss`, 3 `field_boss`, 5 `story_boss`. Ten come
from Acts I–II. Three come from v1.2: Admiral Voss, General Kharn and the Nebula Leviathan.

The roadmap's "eleven bosses" (M39) was counted at V10d1. Admiral Voss (v1.2 Phase B) was already built then. So
"the eleven of Acts I–II plus v1.2's three" counts Voss twice. There are 13, not 14.

Not counted, because nothing treats them as bosses (`EnemyState.is_boss()` keys on the three roles; so do the boss
bar and the phase validation):

- the Ninth Presence (role `normal`, 12× HP, the Presence Trial's finale; §7 question 8);
- Old Snapper (an elite with a dig-in phase, the tell tutorial);
- the named elites (Fruit-Guardian Boar, One-Eye Pang, Ferryman Lou, Knife-Hand Sui) and the Ashborn Pyre-Keeper;
- the spar and trial opponents (role `trial`) and the Trial Tower's floor guardians (normal foes).

### 1.2 As built

HP and attack follow `data/stats.json` `mob`: HP = (30 + 15L + 1.1L²) × role HP (field 40, dungeon 80, story 20) ×
`hp_mult`; attack = (5 + 2.2L + 0.1L²) × role attack (2, 2.2, 1.6) × `attack_mult`. The run logs confirm the HP
column (Tan 31,507; Serpent 43,700; Abbot 98,952; Gate Guardian 106,818; Toad 245,456).

| # | Boss (`id`) | Role, Lv | Room (type, width) | HP | Attack | Attacks | Phases | Comes back |
|---|---|---|---|---|---|---|---|---|
| 1 | Big Toad Tan (`big_toad_tan`) | dungeon, 18 | Boss Den `mh_boss_den` (arena, 2560) | 31,507 | 136 | club swing 0.55 s; call bandits | 50% drink wine (+10% HP, 2 bandits) | daily |
| 2 | Riverbed Serpent (`riverbed_serpent`) | field, 25, Beast King | Serpent's Shallows `dw_serpents_shallows` (arena, 3840) | 43,700 | 245 | bite 0.6 s; tail flood 1.0 s, both sides | 50% flood: the shallows rise to 30 for 14 s | every 45 min |
| 3 | Drowned Abbot (`drowned_abbot`) | dungeon, 27 | Abbot's Sanctum `ds_abbots_sanctum` (arena, 2560) | 98,952 | 302 | bell shockwave 0.7 s, both sides; summon ghosts | 66% flood; 33% ghosts | every 5th day, Qi Unfurling 9 and below |
| 4 | The Reflection (`the_reflection`) | story, 36 | Trial of Reflections `si_trial_of_reflections` (instance, 1280; 600 s event) | 39,912 | 342 | mirror strike 0.45 s | 50% heart demon; 25% enrage | never |
| 5 | Elder Gu (`elder_gu`) | story, 53, cannot be hurt | Gu's Warehouse `si_gus_warehouse` (instance, 2560) | (78,298) | 644 | tide palm 0.5 s | 20 s hired blades; 40 s enrage; flees at 60 s | never |
| 6 | Hollow Behemoth (`hollow_behemoth`) | story, 58 | Siege of Two Sects `si_siege` (instance, 3840; 240 s event) | 92,008 | 750 | stampede 0.7 s (dash 240, shatter); drone burst 1.0 s | 60% boarlets; 30% enrage | never |
| 7 | Gate Guardian (`gate_guardian`) | story, 63 | Ascension Gate `mp_ascension_gate` (arena, 3840) | 106,818 | 865 | ring sweep 0.7 s, both sides; soul gaze 0.9 s | 66% `soul_phase`; 33% `flight_phase` | never |
| 8 | Thousand-Eye Toad (`thousand_eye_toad`) | field, 68, Beast King | Toad's Hollow `ml_toads_hollow` (field, 2560) | 245,456 | 1,234 | belly slam 0.8 s, both sides; tongue lash 0.6 s; mirror gaze (dragonets) | 50% summon | every 45 min |
| 9 | Tomb King of Sunscar (`tomb_king`) | dungeon, 77 | Throne of the Tomb King `ts_throne` (arena, 2560) | 215,793 | 1,350 | glaive sweep 0.75 s (shatter); sand crescent 0.9 s; sun flare 1.1 s | 60% two wardens (74); 30% enrage | daily |
| 10 | Comet Captain Rao (`pirate_captain`) | story, 80 | Sect War `si_sect_war` (instance, 3840; 300 s event, lands at 40 s) | 248,100 | 1,182 | comet cleave 0.6 s; anchor throw 0.9 s; boarding call | 40% enrage; 12% soul detonation (3 s, 280, 60% of max HP) | never |
| 11 | Admiral Voss (`admiral_voss`) | dungeon, 90 | Flagship Deck `bm_flagship_deck` (arena, 2560) | 1,317,120 | 2,006 | starsteel cutlass 0.5 s; broadside 1.2 s (projectile 420); all hands | 60% two gunners (88); 30% enrage | daily |
| 12 | General Kharn (`general_kharn`) | dungeon, 92 | Kharn's Pyre `ar_kharns_pyre` (arena, 2560) | 1,457,974 | 2,087 | cinder glaive 0.55 s; leaping cleave 1.0 s (fire); pyre rings 1.4 s (four fires) | 60% Pyre-Keeper (91); 30% enrage; kneels at 20% | daily |
| 13 | Nebula Leviathan (`nebula_leviathan`) | field, 99 | Leviathan's Maw `nd_leviathans_maw` (field, no flight, 3840) | 1,082,057 | 2,165 | current swallow 1.2 s (pull 220); void breath 1.3 s (460); gravity crash 1.0 s | 60% two eels (97); 30% enrage | every 45 min |

Every room's floor is 340 deep (plane y 620–960). Most ledges stand toward the back, at heights 88–264.

### 1.3 The stat scale at each fight

The player's HP is the valley run's: a checkpoint's saved HP at the start or end of the section, or an earlier run's
`godot.log`. Both are current HP, so read them as "about" and as a floor on max HP.

| Boss | Fought in | Player realm (Lv) | Player HP | A plain blow | Fight today | Par (target) | Enrage |
|---|---|---|---|---|---|---|---|
| Big Toad Tan | `sec_qk5` | Qi Kindling 7–9 (16–18) | ≈ 900 (log: 903 before the first blow) | 130–155, ≈ 15% (log) | 67 s at Qi Unfurling 1, after a first try that ran out | 90 s | 180 s |
| Riverbed Serpent | `sec_qu5` | Qi Unfurling 7 (25) | ≈ 2,000 (log) | ≈ 15% | 95 s (log) | 120 s | 240 s |
| Drowned Abbot | `sec_qu5` | Qi Unfurling 9 (27) | ≈ 2,500 (log; checkpoint `ht1` 2,309) | ≈ 15% | 184 s (log) | 180 s | 360 s |
| The Reflection | `sec_ht5` | Heart Tempering 9 (36) | ≈ 2,500 (log) | ≈ 15% | 75 s (log) | 90 s | 180 s |
| Elder Gu | `sec_sa5` | Spirit Awakening 8 (53) | ≈ 8,000 (checkpoint `hg1`) | ≈ 15% | 60 s (he flees) | none | his 40 s clock |
| Hollow Behemoth | `sec_hg1` | Heaven Glimpse 1–2 (55–58) | ≈ 9,800 (log) | ≈ 15% | inside the 240 s siege | 150 s (to kill it) | the siege's 180 s mark |
| Gate Guardian | `sec_hg1` | Heaven Glimpse 3 (61–63) | ≈ 10,800 (log) | ≈ 15% | 83 s (log) | 120 s | 240 s |
| Thousand-Eye Toad | `sec_ae2` | Sage 2 (67–69) | ≈ 11,500 (checkpoint `ae3`) | ≈ 15% | not logged | 180 s | 360 s |
| Tomb King | `sec_ae4` | Sage Sovereign 1–2 (73–78) | ≈ 15,500 (checkpoint `ae5`) | ≈ 15% | not logged | 150 s | 300 s |
| Comet Captain Rao | `sec_ae5` | Sage Sovereign 2 (76–78) | ≈ 15,500 (`ae6` 14,352; `ae_end` 16,053) | 1,430–1,590, ≈ 14% (log) | not logged | 150 s from his landing | the war's 240 s mark |
| Admiral Voss | `sec_ls2` | Will Manifest 2 (85–87) | ≈ 22,000 (`ls2_end` 21,892) | ≈ 15% | inside a 900 s fight cap | 240 s | 480 s |
| General Kharn | `sec_ls5` | Sphere Lord 1 (91–93) | ≈ 26,000 (`ls4_end` 26,182) | ≈ 15% | chipped by the run's shortcut | 240 s | 480 s |
| Nebula Leviathan | `sec_ls6` | Sphere Lord 2–3 (94–99) | ≈ 27,000–29,000 (`ls5_end`, `ls6_end`) | ≈ 15% | chipped by the run's shortcut | 300 s | 600 s |

The v1.2 fights are long today. The run chips Kharn and the Leviathan to a quarter (`valley_run.gd:2605-2609`,
`2677-2694`). Extrapolating the logged damage per second (about 540 at Lv 27–36, 1,290 at Lv 63) along the monster HP
curve gives roughly 2,500–3,000 at Lv 90–99, so 6–9 minutes for these three. §7 question 5 covers the fix.

### 1.4 What the audit found

1. **No ground markers exist.** M39 lists "ground markers on the bombard and broadsides". The Pirate Gunner's bombard
   and Voss's broadside are plain projectiles (`combat_authority.gd:2050-2055`) with the "!" tell over the head
   (`enemy_view.gd:178`). The only boss drawings on the ground are ground-fire patches, drawn after the blow lands
   (`fx_layer.gd:249`), and Rao's detonation ring (`hazard_view.gd:205-212`).
2. **Two phases do nothing.** `_check_phases` (`enemy_authority.gd:284-314`) has no branch for the Gate Guardian's
   `soul_phase` and `flight_phase`. They roar and shake, and the fight goes on unchanged.
3. **Tan's jars are not wired.** `drink_wine` heals 10% at half health whatever state the three wine jars are in
   (`enemy_authority.gd:297-299`). The phase's `breakable` field is never read.
4. **Two floods are the only arena mechanics.** The Serpent's and the Abbot's rooms raise water on `boss_phase`
   (`zone_geometry.gd:392-399`). The water covers only the front of the depth band (Serpent y 820–960, Abbot y
   700–960), so a step toward the back wall escapes it, and nothing marks it while it rises.
5. **What is drawn is not what hits.** Ground fire, hazard strikes and Rao's detonation test a circle in the room
   plane (`combat_authority.gd:1355`, `world_authority.gd:1192`, `combat_authority.gd:208`). They are drawn as ellipses
   squashed to 0.35–0.42 in depth (`fx_layer.gd:254`, `hazard_view.gd:210-211, 228-229`). The plane maps one to one to
   the screen (`enemy_view.gd:79`), so a player a step outside the drawn edge in depth is still hit. Rao's 280 ring is
   drawn 118 deep and strikes 280 deep, most of the 340 band.
6. **`boss_defeated` is never emitted.** The Untouched achievement listens for it (`tools/data/economy.py:949`) and can
   never be earned.
7. **Three boss events are outside the contract.** `boss_phase`, `enemy_summoned` and `boss_fled` are emitted
   (`enemy_authority.gd:263, 314, 384`) but are not in `tools/data/contract.py`, so `contract_tests` checks none of
   them. `enemy_summoned` has no consumer.
8. **Fights have no clock.** `ai.engaged_t` runs only for bosses with `flees_after_s` (`enemy_authority.gd:139-145`).
9. **Phases are nearly invisible.** One red bar with no marks (`hud.gd:1913-1923`); a phase is a 0.3 s shake
   (`world.gd:640`), plus a toast for Rao's detonation only (`hud.gd:1101`).
10. **No re-run loop.** Field bosses return every 45 minutes, dungeon bosses daily, the Abbot every fifth day at Qi
    Unfurling 9 and below, story bosses never. No boss keeps a record or counts toward anything past its first kill.

---

## 2. The standard every fight meets

### 2.1 Damage

- **A plain blow** takes about 15% of a character's max HP at the boss's band (Tan 130–155 of about 900; Rao
  1,430–1,590 of about 10,500 in an older run). This page keeps it.
- **A marked blow** deals a share of the struck actor's max HP, as the tribulation, the hazards, ground fire and
  Rao's detonation already do. So a mechanic stays a mechanic whatever the gear. The share is the attack's `mult` ×
  15%, rounded to 5%, plus 5% for being avoidable. Tiers: light 15%, medium 20–25%, heavy 30–35%, floor 35–45%.
- **The burst cap.** Markers that can land within any 3 s window sum to at most 60% of max HP before the enrage. A
  character at full HP never falls to one cycle.
- **Enrage stage two** multiplies marker shares by 1.5, capped at 68%. Rao's detonation (60%) is the one exception to these
  caps: it is announced for 3 s and ends the fight.
- **Answers** a marker can have: step out; go up (the ground band reaches altitude 40, as ground fire does, so any
  ledge is above it); dodge through (the dash's 0.25 s of invulnerability at the moment of impact slips it); guard
  (halves it, except floors); interact (a bell, a jar, a keg).

### 2.2 Wind-ups

- **Escape time.** From the worst point inside a marker to the nearest safe point: distance ÷ 205 (walk speed,
  `stats.json` `move.base`), plus 0.45 s for a jump to 122 or less, 0.6 s for a double jump to 202 or less (from Qi
  Unfurling 6), or height ÷ 160 + 0.3 s for a rope or ladder. Circles, rings and cones are ellipses in depth (§3.1),
  so the quickest way out is often a short step toward or away from the camera.
- **The rule.** A marker's wind-up is at least its escape time + 0.4 s of reaction, and never under 0.9 s. A floor
  marker's is at most 3.5 s; a longer one reads as a lull. `data_validation` checks this against the boss's room
  (§6.3).
- **The stage rule.** One marked attack winds up at a time per boss. A floor marker holds the stage alone. The next
  marker starts at least 1.0 s after the last one lands. A rain of several circles counts as one.
- **The setting.** *Boss wind-ups: Standard, Longer (×1.25), Longest (×1.5)* stretches every marker and the boss's
  own wind-up with it (§3.12).

### 2.3 Phases

Each boss has three phases: I from the start, II and III at two thresholds (of HP, or of the clock for Elder Gu).
Each new phase adds a marker, changes the room, or both. Existing thresholds are kept where they exist, so the
Captain's 12%, Kharn's kneel at 20% and the tests that check them stay true.

### 2.4 Par and enrage

- **Par** is the time a character at the boss's band should take. `boss_suite` measures it with the valley run's
  reference character (§6.1). The build sets `hp_mult` so the measured time lands within 0.8–1.25 × par.
- **The enrage timer** is 2 × par, counted from `boss_engaged`, drawn as an incense stick beside the bar. The game
  already uses incense as a clock ("The incense has burned down", the Cloud Steps route). When it burns out: shorter
  pauses and harder blows (the existing enrage numbers, or stronger), and markers twice as often. Stage two, 60 s
  later: marker shares ×1.5. It never ends the fight by itself.
- Event bosses (the Reflection, the Behemoth, Rao) keep their room event's clock as the outer limit. Their enrage
  fires on it.

---

## 3. The shared building blocks

### 3.1 Marker kinds

All sizes are in room-plane px. The ground plane's depth factor is `DEPTH_K = 0.42`, the factor `HazardView` already
draws with. A circle of radius r is an ellipse r wide and r × 0.42 deep, and it hits exactly the ellipse it draws.

| Kind | Size fields | Hit test | Typical answer |
|---|---|---|---|
| **circle** | `r` | (dx / r)² + (dy / (r × DEPTH_K))² ≤ 1 | step out; go up |
| **line** | `length`, `half_depth`; `both_sides`; `across` (full depth, `length` is then the x width) | a rectangle in the plane | step out in depth (along) or in x (across) |
| **cone** | `length`, `spread_deg` | a wedge from the boss's front, depth scaled by DEPTH_K | step behind or to the side |
| **ring** | `r_in`, `r_out` | inside the outer ellipse and outside the inner one | hug the boss, or get clear |
| **floor** | `area` [x, y, w, h] or `within` (x distance from the boss), `safe` [...] | the ground band of the room (or the area) minus the safe zones | reach a safe zone |
| **rows** | `rows` (3), `struck` (2) | the depth band cut into equal rows; the struck rows along the whole room | move to the unstruck row |

Every marker has an altitude band `alt`: `[-20, 40]` for the ground, `[-20, 400]` for a column (sunlight, a gaze from
above). Safe zones for a floor or any marker:

| Safe entry | Meaning |
|---|---|
| `{"surface": id}` | standing on that surface |
| `{"above": 60}` | any altitude over 60 (every ledge) |
| `{"circle": [x, y, r]}` | a fixed spot on the ground |
| `{"shade_of": ["self", "terracotta_warden"], "dx": -130, "r": 90}` | a moving ellipse beside each named actor, checked at impact |
| `{"patch": "ash"}` | inside a patch of that kind (§3.6) |
| `{"sphere": "own"}` | inside the actor's own Sphere while it holds |
| `{"beyond": r}` | outside r from the marker's centre |
| `{"row": "unstruck"}` | the free row of a rows marker |

### 3.2 How markers look, and accessibility

Boss markers speak the language room hazards already taught: a broken amber border and a "!" that read without
colour (`hazard_view.gd` header, S17). Colour is never the only carrier. Every kind has a shape cue as well.

| Element | Drawing | Colour |
|---|---|---|
| Danger rim | a dashed ellipse, rectangle or wedge edge, 2 px over a 2 px ink outline | amber `#e8a33c` (`HazardView.AMBER`) |
| Wind-up progress | a dark fill that grows from the centre (circle, ring, floor) or from the boss (line, cone) and meets the rim at impact | the fill is tinted by damage: umber (physical), teal (Qi, `UiKit.QI`), violet (soul, `UiKit.SOUL`), ember (fire), river blue (water) |
| Last 0.5 s | a pulsing "!" at the centre, the rim doubles | red "!" as in hazards |
| Push or pull | chevrons along the rim pointing the way | jade (`UiKit.BRIGHT_JADE`) |
| Control (stun, confusion, seal) | a small spiral glyph beside the "!" | as the fill |
| Breaks a natal weapon | a cracked-blade glyph | as the fill |
| Safe zone | a solid double rim and a four-petal lotus glyph; on a ledge, its top edge traced with a lotus every 120 px | pale gold (`UiKit.PALE_GOLD`), steady, never pulsing |
| Left behind | wine, frost, water, ash patches beside the existing ground-fire art, each with a hatch pattern of its own | as the patch |

Settings, in Settings › Accessibility next to *Bright flashes*, *Vibration* and *Captions*:

- **Boss wind-ups:** Standard, Longer (×1.25), Longest (×1.5). A simulation setting on the account, read by
  EnemyAuthority. It counts for every reward (§3.11).
- **Marker contrast:** Normal, High. High draws 4 px rims, a darker fill and glyphs half again as large.
- **Captions** (existing): each marker names itself and its answer ("[Wine Flood: climb a shelf]").
- **Vibration** (existing): a short buzz when a marker starts, a double buzz if the player is still inside with 0.5 s
  left.
- **Screen shake** and **Bright flashes** (existing) govern the impact.

### 3.3 Data: `tools/data/enemies.py`

A helper beside `atk()`:

```python
DEPTH_K = 0.42   # the ground plane's depth factor, as HazardView draws it

def mark(shape, pct, aim="self", alt=(-20, 40), guard="half", **size):
    """P9 · a telegraphed marker. Its wind-up is the attack's windup_s. `pct` is the share of the struck actor's max
    HP. `size` by shape: circle r; line length, half_depth, both_sides, across; cone length, spread_deg; ring r_in, r_out;
    floor area or within, safe; rows rows, struck. Optional: status, push, pull, knockback, shatter, leaves, count,
    gap_s, spots, track_s, answer, caption."""
    return {"shape": shape, "pct": pct, "aim": aim, "alt": list(alt), "guard": "none" if shape == "floor" else guard, **size}
```

`aim`: `self` (centred on the boss), `ahead` (from its front), `target` (the target's spot when the wind-up starts),
`follow` (tracks the target for `track_s`, then locks), `surface` (the surface under the target), `each` (`spots`,
the `count` nearest the target), `fixed` (`at`).

New fields on attacks, phases and the boss row:

| Field | On | Meaning |
|---|---|---|
| `marker` | attack | a `mark(...)`: the attack is a marked blow. It deals `pct`, not `mult` |
| `from_phase` | attack | the first phase (1–3) that may use it; default 1 |
| `detached` | attack | the boss keeps fighting while the marker counts down (floors, rains) |
| `leap` | attack | the boss travels to the marker's centre during the wind-up (the existing hop arc) and lands at impact |
| `mechanics` | boss | `[{"attack", "every_s", "first_s", "from_phase"}]`: marked attacks on a clock, not chosen by range |
| `phases[].card` | phase | the phase card's string key; every phase has one |
| `phases[].action` | phase | new actions `drink` (replaces `drink_wine`; gated by jars), `stone_skin`, `take_wing` (these two replace `soul_phase` and `flight_phase`) |
| `enrage_timer` | boss | `{"after_s", "cooldown", "damage", "every_mult", "stage2_s", "pct_mult", "card"}` |
| `boss` | boss | `{"epithet", "intro", "par_s", "feat", "signature": {"item", "chance", "pity"}, "rerun"}` |

Big Toad Tan as written in P9a (§4.1):

```python
mob("big_toad_tan", 18, "dungeon_boss", "none", None, [d("mudwater_manual", 1.0)],
    [atk("club_swing", 0.55, 90, 1.2, depth=34, knockback=60),
     atk("call_bandits", 1.0, 0, 0.0, summon="mudwater_bandit"),
     atk("jar_hurl", 1.2, 420, 0.0, marker=mark("circle", 0.15, aim="target", r=70,
         leaves={"kind": "wine", "r": 70, "duration_s": 5, "slow": 0.3})),
     atk("belly_flop", 1.6, 0, 0.0, from_phase=2, leap=True, marker=mark("circle", 0.25, aim="target", r=140,
         status={"id": "stun", "chance": 1.0, "power": 1.0, "duration_s": 0.6})),
     atk("drunken_rampage", 1.4, 900, 0.0, from_phase=3, dash=900, marker=mark("line", 0.25, aim="ahead",
         length=900, half_depth=50, knockback=120)),
     atk("wine_flood", 3.0, 0, 0.0, from_phase=3, detached=True, marker=mark("floor", 0.35, safe=[{"above": 60}],
         status={"id": "slow", "chance": 1.0, "power": 0.3, "duration_s": 2}))],
    ai="boss_tan", art=human("big_toad_tan"), race="human", energy="primal_qi", width=24, height=96,
    mechanics=[{"attack": "jar_hurl", "every_s": 9, "first_s": 4},
               {"attack": "belly_flop", "every_s": 14, "first_s": 3, "from_phase": 2},
               {"attack": "wine_flood", "every_s": 24, "first_s": 6, "from_phase": 3}],
    phases=[{"below": 0.5, "action": "drink", "heal": 0.1, "jar": "wine_jar", "retry_s": 25, "card": "boss.big_toad_tan.p2"},
            {"below": 0.25, "action": "enrage", "cooldown": 0.8, "damage": 1.15, "card": "boss.big_toad_tan.p3"}],
    enrage_timer={"after_s": 180, "cooldown": 0.6, "damage": 1.3, "every_mult": 0.5, "stage2_s": 60, "pct_mult": 1.5,
                  "card": "boss.big_toad_tan.enrage"},
    boss={"epithet": "boss.big_toad_tan.epithet", "intro": "boss.big_toad_tan.intro", "par_s": 90, "feat": "dry_den",
          "signature": {"set": "mudwater", "chance": 0.08, "pity": 12}, "rerun": "daily"},
    unique_drop="mudwater_cleaver", hp_mult=0.6, attack_mult=0.8, pet_book={"item": "pet_book_frenzy", "chance": 0.35},
    faction="mudwater", named=True)
```

Other files:

- **Rooms** (`tools/data/world.py`, `catalogue_rows_dungeons.py`, `lantern.py`): the arena changes of §4 (Voss's three
  powder kegs as breakable objects; room-script keys so water and objects answer `telegraph_started`, as they answer
  `boss_phase` today).
- **Strings** (`tools/data/ui_strings.json`): `boss.<id>.epithet`, `.intro`, `.intro_again`, `.p2`, `.p3`,
  `.enrage`; `boss.marker.<attack id>` (the caption, with its answer); `ui.foes.*` for the Worthy Foes page;
  `ui.settings.boss_windups`, `ui.settings.marker_contrast`.
- **Items and titles** (`items.py`, `economy.py`): the signature drops and the four seal titles of §3.11.
- **Contract** (`contract.py`): §3.10.

### 3.4 TelegraphRules (pure)

A new `scripts/simulation/rules/telegraph_rules.gd`. Every function takes its numbers as arguments; none reads the
clock or a random stream (the caller passes an `Rng` stream where a spot is chosen).

| Function | Returns |
|---|---|
| `place(marker, boss_plane, facing, target_plane, target_alt, room_def, rng)` | a telegraph's geometry: shape, centre, facing, sizes, spots |
| `contains(tg, point, alt)` | whether a point at that altitude is inside the drawn shape |
| `is_safe(tg, point, alt, ctx)` | whether it is in a safe zone; `ctx` holds the surface underfoot, living actors by def, patches and the actor's Sphere |
| `nearest_safe(tg, point, alt, geometry, move)` | the nearest safe `{pos, alt}` a character with `move` (jump, double jump, climb, flight) can reach |
| `escape_s(tg, room_def, move)` | the worst escape time of §2.2, for validation |
| `rows_of(room_def, n)` | the depth rows of a rows marker |

### 3.5 Scheduling: EnemyBrain and EnemyAuthority

**EnemyAuthority** (`enemy_authority.gd`) owns a boss's fight state and the room's live markers
(`RoomRuntime.telegraphs`, beside `projectiles`; cleared on leaving the room; at most 8 live).

1. **Engaged.** The first time a boss enters `aggro`: start `ai.engaged_t` for every boss (today only for
   `flees_after_s`), open the tally `{t0, marker_hits, wounded, revived}`, emit `boss_engaged`, and hold the first
   attack 1.5 s for the intro card (`ai.timer = max(ai.timer, 1.5)`).
2. **Mechanic clocks.** `ai.mech_t[i]` counts down each tick. A mechanic starts counting at `first_s` when its
   `from_phase` opens, and resets to `every_s` (× `every_mult` once enraged) when used.
3. **Phases.** `_check_phases` gains `drink` (walk to the nearest intact jar; drink only if it is still intact on
   arrival; a broken jar dazes the boss 3 s with the existing `vulnerable` status), `stone_skin` (physical damage taken
   × `physical_taken`), `take_wing` (hover at `hover`, land for `land_s` after each named mechanic). A test in
   `data_validation` keeps every phase action in `EnemyAuthority.PHASE_ACTIONS` or a room script, so no phase can be
   dead again. Every phase emits `boss_phase` with its `card`.
4. **Enrage timer.** At `engaged_t ≥ after_s`: `ai.enraged` takes the stronger of the existing HP enrage and the
   timer's numbers; emit `boss_enraged` (reason `timer`, stage 1). At `after_s + stage2_s`: stage 2, marker shares ×
   `pct_mult`.
5. **Markers.** `place_telegraph(e, attack)` calls `TelegraphRules.place` with the `world` stream, stores the
   telegraph `{uid, enemy, attack, geometry, t, windup, active, pct, stage, safe, detached}`, emits
   `telegraph_started`. Each tick advances `t`; a `follow` marker re-centres until `track_s`; at `t ≥ windup`,
   `game.combat.resolve_telegraph(tg)` (as `boss_detonate` calls `resolve_boss_detonation` today); the marker stays
   0.25 s for the flash, then goes.
6. **Defeat.** After `actor_defeated` for a boss, emit `boss_defeated` with the tally (§3.10). Rao's detonation and
   Kharn's judgement count as defeats; Gu's flight emits `boss_fled` as now.

**EnemyBrain** (`enemy_brain.gd`), in the `aggro` branch, before the reach check:

1. If a mechanic is due and the stage is free (§2.2), start its attack whatever the range: the wind-up state, the
   `attack_started` event, and `place_telegraph`. Wind-up = `windup_s` × the account's wind-up scale.
2. `_choose_attack` skips attacks listed in `mechanics` and attacks whose `from_phase` is not open yet.
3. At the end of a marked wind-up, the boss plays its attack pose; the marker resolves on its own clock at the same
   moment. A `detached` attack returns the boss to `aggro` after 0.5 s while its marker counts down.
4. `leap`: the boss rides the existing hop arc to the marker's centre and lands at impact.

**AllyBrain** (`ally_brain.gd`): companions and spirit animals inside a marker when it starts walk to
`TelegraphRules.nearest_safe`. One that stays takes the share of its own max HP.

### 3.6 Resolution: CombatAuthority

`resolve_telegraph(tg)` generalises `apply_detonation_blast` (`combat_authority.gd:206-214`):

- For the player and each ally: skip if not `contains` or if `is_safe`. A dodge in progress or invulnerability gives
  `hit_dodged`. Guard halves the share unless `guard` is `none`.
- Damage = max HP × `pct` × stage multiplier (cap 0.68), through `_damage_player` with the marker's damage type, then
  its status, push, pull, knockback and `shatter` (the natal-weapon break, as today).
- `leaves` adds a patch to `ground_patches`, the renamed `ground_fires`, which gains kinds: fire (as now), ash (fire
  that has burnt out: cannot burn for 20 s), wine (slow), frost (slow), water. The `ground_fire` event stays.
- Emit `telegraph_struck` (actor, amount, dodged, safe) for each actor inside.

The rule "drawn = hit" applies to the old shapes too, in P9a: ground fire, hazard strikes and the detonation ring test
the same DEPTH_K ellipse they draw (finding 5).

### 3.7 Drawing: `fx_layer.gd`

- `fx_layer` gains a `ground` child at z −1850 (as `HazardView.ground`), so fills and rims lie under the actors;
  glyphs and the "!" stay on the main layer at 4000.
- `_draw_telegraph(tg)`, polled each frame from `Game.room_rt.telegraphs` like ground fire, draws §3.2 by shape.
  Moving safe zones (shade, Sphere, ash) are drawn where they are this frame.
- The ellipse and dashed-rim helpers move from `HazardView` into a small static `GroundDraw`, used by both, so hazards
  and boss markers look alike.
- The impact: a flash in the marker's colour under *Bright flashes*, dust, and a shake of 0.2 s from `world.gd` on
  `telegraph_struck` when the marker is a floor or the player was inside.
- A `--telegraph=<boss>:<attack>[:k]` preview flag, like `--hazard`, holds one marker at wind-up fraction `k` for
  screenshots.

### 3.8 HUD: the boss bar and the incense

`hud.gd` `_draw_boss` (`Rect2(340, 118, 600, 14)`):

- **Notches** at each HP threshold, with the phase numeral under each ("II", "III"). Past a notch the fill darkens a
  step (red, crimson, ember), so the phase also reads by the notch count, not only by hue. Elder Gu's bar is his clock,
  with notches at 20 s and 40 s and a mark at 60 s.
- **The incense stick** left of the name: a stick that burns down over `after_s`; the seconds are written on it when 30
  or fewer are left. When it burns out it snaps, the frame pulses ember and the word *Enraged* sits under the bar.
- **Captions** gain `telegraph_started` (the marker's own caption) and `boss_enraged`; `_caption_worthy` already
  passes bosses.
- The Rao toast (`hud.gd:1101`) gives way to the phase card.

### 3.9 Moments (P6)

P6 builds `data/moments.json` with rows for `boss_intro` and `boss_phase`. P9 uses them and adds `boss_enrage`. Rules
for every boss (each boss's text is in §4):

- **Intro card** (trigger `boss_engaged`): letterbox bars slide in over 0.3 s; the camera eases to the boss over
  0.6 s; the name in the display face with its epithet beneath; one line of speech as a subtitle (a caption line for
  beasts); 2.0 s in all. Control returns within 1.5 s (F4's rule), and the boss holds its first attack until the card
  closes. On later fights, a 0.8 s name strip with the `intro_again` line.
- **Phase card** (trigger `boss_phase`): an ink-brush banner across the upper third with the phase numeral and name,
  1.2 s; the bar's notch flashes; the existing roar and shake. The boss starts no wind-up during the card.
- **Enrage card** (trigger `boss_enraged`): the incense snaps, "The incense is spent" and the boss's own enrage line,
  1.0 s; an ember vignette at the screen's edge under *Bright flashes*.
- **The fall** (trigger `boss_defeated`): P6's loot fountain (F4); the seals earned this fight pressed one by one on a
  small scroll (0.3 s each); on a first kill the Worthy Foes page unrolls (skippable). Story beats (Kharn kneels, Gu
  slips away) use P6's story-beat row.

### 3.10 Events (contract)

Into `tools/data/contract.py`. Each has an emitter in its system's files and a consumer, as `event_contract.json`
requires.

| Event | System (emits) | Payload | Consumers |
|---|---|---|---|
| `boss_engaged` | Enemies | enemy, def, room, level, first | HUD (intro card via P6's MomentView; bar and incense); AudioDirector (boss sting) |
| `boss_phase` (exists; into the catalogue) | Enemies | enemy, def, phase, action, card | WorldAuthority (room scripts: water, objects); `world.gd` (shake); HUD (phase card, caption); AudioDirector |
| `telegraph_started` | Enemies | enemy, def, attack, shape, x, y, facing, windup, pct, detached | HUD (caption, vibration); AudioDirector (a heavy tell); WorldAuthority (room scripts: the Serpent's rising river, Voss's kegs). The drawing is polled |
| `telegraph_struck` | Combat | enemy, attack, actor, amount, dodged | `world.gd` (impact, shake); EnemyAuthority (the tally's marker hits) |
| `boss_enraged` | Enemies | enemy, def, reason (`timer`, `hp`), stage | HUD (enrage card, the incense); AudioDirector |
| `boss_defeated` | Enemies | actor, enemy, def, room, time_s, marker_hits, clean (never gravely wounded), revived, first, in_band, feat, judged | AchievementAuthority (the Untouched rule, which listens today; Worthy Foes records, seals, pity); HUD (the fall) |
| `boss_fled` (exists; into the catalogue) | Enemies | enemy, def, room | HUD (story beat "Gu slips away") |
| `enemy_summoned` (exists) | Enemies | enemy | HUD (caption "[Help arrives]"), or it is removed |

### 3.11 The reward loop: Worthy Foes

One loop for all thirteen, recorded per character by AchievementAuthority and shown on a new Codex tab, **Worthy
Foes**: one scroll page per boss with its portrait (its own sprite, in ink until all four seals, then in colour), the
seals, kills, best time, fewest marker hits, the signature's pity bar and when it can next be fought.

| Part | Rule |
|---|---|
| **First kill** | The boss's existing first-kill rewards (listed in §4), and its Worthy Foes page |
| **Signature drop** | One named item per boss (§4). A chance per kill with pity: guaranteed by the Nth kill without it. Dungeon bosses 8% (pity 12), field bosses 3% (pity 30), story replays 15% (pity 6) |
| **Rhythm** | As today: dungeon bosses once a day, field bosses every 45 minutes (account-wide), the Abbot on the calendar. Story bosses once a week through Recollection (§7 question 1) |
| **Weekly tribute** | The first kill of each boss after the weekly reset doubles its guaranteed drops and adds one equipment roll at its quality floor. Field bosses also still count for Sect Service |
| **Seals** | Four per boss, each paying once (three of the boss's key material): **Clear Sight** (no marker struck you), **Swift** (at or under par), **Unbowed** (never gravely wounded, no revival), and the boss's **Feat** (§4). Seals count only within 8 levels above the boss (the ambushers' reach), so an outgrown boss still asks for skill, not stats |
| **Titles** | By seals held: 8 *Reader of Omens* (+1% evasion), 20 *Steady Before Giants* (+2% max HP), 36 *Tempered by Worthy Foes* (+3 Will), all 51 *Peerless Among Foes* (+1% crit chance). Elder Gu has no Swift seal, so 13 bosses hold 51 |
| **Record** | Best time and fewest marker hits, at any level |

Seals, drops and tribute count the same at every wind-up setting.

### 3.12 State, save and settings

- The fight is not saved. Leaving the room resets the boss, as today; the telegraphs and the tally go with it.
- Per character (`GameCharacter.boss_records`, saved with the achievements): `{def: {kills, first_utc, best_s,
  fewest_marker_hits, seals: [..], pity, tribute_week}}`. An old save loads with none.
- Per account (`account.settings`): `boss_windups` (1.0, 1.25, 1.5; default 1.0) and `marker_contrast` (`normal`,
  `high`).

### 3.13 Single Player and Online

Single Player (now): all of the above runs locally. Online (v2.0): the server owns the mechanic clocks, marker
placement (from its own streams) and resolution; clients draw from the server's telegraph list. In a shared fight the
wind-up setting cannot differ per player; the fight uses Longer (×1.25) for all. The Worthy Foes record and seals are
server-held.

---

## 4. The bosses

Each boss keeps its lore, its attacks and its existing thresholds. Marker tables give the share of max HP and, in
brackets, about what it takes from a character at the band's HP of §1.3. "Ground" means the band up to altitude 40;
"column" reaches 400.

### 4.1 Big Toad Tan (`big_toad_tan`): Master of the Mudwater Den

The bandit chief of the Mudwater Hideout and the first boss every player meets. His design note already says he
teaches the pattern rather than walls it. He teaches the three answers: step out, go up, read the room.

**Numbers.** Lv 18, 31,507 HP, attack 136. Player: Qi Kindling 7–9, about 900 HP, one jump (apex 122), no double jump
yet. Par 90 s; enrage 180 s.

**Arena.** The Boss Den, 2560 wide. Three wine shelves at height 88 in the back row (x 300–600, 1100–1400,
1900–2200), each with a ladder and one wine jar. The worst floor point is 2.3 s from a shelf.

| Phase | Opens | What changes |
|---|---|---|
| I · Host of the Den | start | Club swing; Jar Hurl |
| II · The Wine Runs Low | 50% | He lumbers to the nearest shelf with an intact jar and drinks: +10% HP and two bandits, only if the jar is still whole when he gets there. A jar already broken dazes him 3 s (vulnerable). He tries again every 25 s while jars remain. Belly Flop opens |
| III · Last Call | 25% | HP enrage (pauses × 0.8, blows × 1.15); Drunken Rampage and Wine Flood open |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Jar Hurl | circle, amber rim, wine fill | on you, r 70 | 1.2 s | 15% (≈ 135), and a wine puddle (slow 30%) for 5 s | a step out, or a shelf |
| Belly Flop | circle, umber, spiral glyph | on you, r 140; he leaps there | 1.6 s | 25% (≈ 225) and a 0.6 s stun | out of it, or on a shelf |
| Drunken Rampage | line along the room, umber | from him toward you, 900 × 50 deep | 1.4 s | 25% and a knockback; if the charge ends at the den's wall, he stuns himself 2.5 s | a step in depth |
| Wine Flood | floor, wine fill, lotus marks on the shelves | the whole ground | 3.0 s | 35% (≈ 315) and slowed 2 s | any shelf |

**Enrage (180 s): "The Den bars its door."** Two bandits every 20 s; pauses × 0.6, blows × 1.3; Wine Flood every 12 s.
Stage two at 240 s.

**Rewards.** First kill: the Mudwater Manual, 300 taels, the unique Mudwater Cleaver. Signature: a piece of the
existing Mudwater set, 8% (pity 12); the Frenzy pet book stays at 35%. Daily; weekly tribute. Feat **Dry Den**: break
all three jars before his first drink (each shelf is a jump or a ladder).

**Moments.** Intro card: *"Big Toad" Tan, Master of the Mudwater Den*: "You broke my door. You'll pay for the door."
On this first fight only, the first Jar Hurl and the first Belly Flop carry a one-time teaching line ("Step out of
the ring", "Or get above it"). Phase cards: *The Wine Runs Low*, *Last Call*. Enrage card: *The Den Bars Its Door*.

### 4.2 Riverbed Serpent (`riverbed_serpent`): King of the Deepwater Bend

The valley's Beast King. While it lives, the zone's beasts are 10% stronger; when it falls, its egg nest opens for 30
minutes. It already floods its arena at half health.

**Numbers.** Lv 25, 43,700 HP, attack 245. Player: Qi Unfurling 7, about 2,000 HP, double jump. Par 120 s; enrage
240 s.

**Arena.** Serpent's Shallows, 3840 wide. The shallows are the front strip (x 400–3400, y 820–960); the back of the
beach (y 620–820) is dry. Three high rocks at 100 (x 900–1080, 1700–1880, 2500–2680), each 180 wide, with ropes;
the nest sits on the third.

| Phase | Opens | What changes |
|---|---|---|
| I · The Bend Stirs | start | Bite; Tail Flood and Surge Lane marked |
| II · The River Rises | 50% | The existing flood, now marked, and then again every 40 s; Rock Coil while the water holds |
| III · Whirlpool | 25% (new) | Riverbed Churn |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Tail Flood | line both ways, river blue | from it, 260 × 80 deep | 1.0 s | 15% (≈ 300) and a knockback | a step in depth |
| Surge Lane | line along the shallows | from it along the front strip, 1200 long | 1.4 s | 20% and slowed | the dry back of the beach, or a rock |
| The River Rises | floor limited to the shallows (the room's `serpent_flood` volume), droplet glyph | x 400–3400, y 820–960 | 4.0 s (the water's rise) | the existing deep water for 14 s (sink, return to the last dry spot), plus 10% each time you sink | y under 820, or a rock |
| Rock Coil | circle, column | on the half of your rock nearest it, r 80 | 1.2 s | 20% and knocked off the rock | the rock's far half |
| Riverbed Churn | ring with jade chevrons pointing in, then a circle | pull ring r 320 around it, then its maw r 90 | 1.4 s, then a 2 s pull of 120 px/s | the maw: 30% | outside 320, or on a rock (the pull works on the ground band) |

The repeat flood needs one room-data change: the `serpent_flood` volume's `rise` list also answers `telegraph_started`
with `{"attack": "the_river_rises"}`.

**Enrage (240 s): "The Bend floods for good."** The river rises every 20 s; Surge Lane every 6 s.

**Rewards.** First kill: the Serpent Core and 300 taels (the quest), the Mountainsplit spine (legend chain). Signature:
**Riverbed Pearl** (new; a Water jade), 3% (pity 30). Every 45 minutes; weekly tribute; the nest's rare spirit egg.
Feat **Dry Feet**: never sink while the river is up.

**Moments.** Intro card: *Riverbed Serpent, King of the Deepwater Bend*; caption: "The water draws back from the
shore." Phase cards: *The River Rises*, *Whirlpool*. Enrage card: *The Bend Floods for Good*.

### 4.3 Drowned Abbot (`drowned_abbot`): Keeper of the Sunken Shrine

The abbot who went down with his shrine and rings its great bell still. His sanctum holds four small bells on ledges;
today they can be rung and do nothing. They become the answer to his chant.

**Numbers.** Lv 27, 98,952 HP, attack 302. Player: Qi Unfurling 9, about 2,500 HP. Par 180 s; enrage 360 s.

**Arena.** The Abbot's Sanctum, 2560 wide. Bell ledges: 0 (x 420–640, h 100), 1 (1000–1220, h 200), 2 (1580–1800,
h 100), 3 (2160–2380, h 200), each with a rope and a small bell. Two statue plinths (top 80). The flood covers x
260–2320, y 700–960; the back strip (y 620–700) and the ledges stay dry.

| Phase | Opens | What changes |
|---|---|---|
| I · The Bell Tolls | start | Great Bell Toll; ghosts |
| II · The Sanctum Floods | 66% | The existing flood, marked; Drowned Chant on the dry ground and the ledges |
| III · Scripture Rain | 33% | Ghosts (existing); Scripture Rain; the flood returns every 35 s |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Great Bell Toll | ring, violet | around him, r_in 70, r_out 220 | 1.0 s | 20% soul (≈ 500) and a knockback | hug him, or beyond 220 |
| The Sanctum Floods | floor limited to the flood's area, droplet glyph | x 260–2320, y 700–960 | 4.0 s | deep water for 14 s | the back strip, a ledge, a plinth top |
| Drowned Chant | circle, column, violet | on your spot, r 90 | 2.0 s | 25% soul (≈ 625) and Qi sealed 2 s | ring the small bell on your ledge (it answers the great bell: the chant breaks and he is stunned 1.5 s; the bell re-arms after 6 s), or move 90 along the strip |
| Scripture Rain | three circles, amber | on you, one after another 0.8 s apart, r 60 | 1.0 s each | 12% each | keep moving |

**Enrage (360 s): "The tide returns."** The flood every 25 s; ghosts every 20 s.

**Rewards.** First kill: the Riverbreath Scroll, the Drowned Robe, the Bronze Bell and the Shattered Moon Blade,
soulbell seeds. Signature: a piece of the existing Drowned Abbot set, 8% (pity 10). He returns with the calendar's
*Drowned Shrine Surfaces* (every fifth day, at Qi Unfurling 9 and below); the first kill of each surfacing is his
tribute. Feat **The Small Bells Answer**: answer every Drowned Chant with a bell.

**Moments.** Intro card: *The Drowned Abbot, Keeper of the Sunken Shrine*: "The shrine went under with its prayers.
Stay, and pray with us." Phase cards: *The Sanctum Floods*, *Scripture Rain*. Enrage card: *The Tide Returns*.

### 4.4 The Reflection (`the_reflection`): Your Own Doubt

The heart trial: the cultivator faces themselves, in their own clothes, in pale light. Doubt feeds the heart-demon
meter, and every 25 on it already brings a heart demon into the trial. The Tide of Doubt ties the mechanic to that
meter.

**Numbers.** Lv 36, 39,912 HP, attack 342. Player: Heart Tempering 9, about 2,500 HP. Par 90 s; enrage 180 s; the
trial's own 600 s clock stays the outer limit.

**Arena.** The Trial of Reflections, 1280 wide. Two mirror ledges at 100 (x 220–460 and 820–1060), with ropes and step
rocks (top 40). The worst floor point is 1.9 s from a ledge.

| Phase | Opens | What changes |
|---|---|---|
| I · Your Own Hand | start | Mirror strike; Echo Palm |
| II · Doubt | 50% | A heart demon (existing); Tide of Doubt |
| III · Desperate as You | 25% | HP enrage (existing); Broken Mirror |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Echo Palm | circle, violet | where you stand, r 80 | 1.4 s | 15% soul (≈ 375) | a step out |
| Tide of Doubt | floor, violet | the whole ground | 2.6 s | 30% soul (≈ 750) and +10 heart demon (which can call another demon) | either mirror ledge |
| Broken Mirror | circle, column | the ledge you have stood on for 3 s, r 130 | 1.4 s | 25% and knocked down | drop to the floor, or cross to the other ledge |

Up for the Tide, down for the Broken Mirror: the fight's rhythm.

**Enrage (180 s): "Doubt takes root."** The Tide every 9 s; a heart demon every 20 s whatever the meter.

**Rewards.** First kill: the heart trial passed and −30 heart demon (existing). Re-runs: the **Mirror Rite**, once a
week at the rite on the mentor's peak (`rite_reflection` on Elder Hu's, `rite_reflection_cm` on Elder Sung's). There
the Reflection takes your level (it is your reflection), and a win takes −20 heart demon if you carry any. Signature:
**Clear Heart Mirror** (new treasure art: turns aside the next soul blow, once a minute), 15% per rite (pity 6). Feat
**Unmoved**: gain no heart demon in the fight.

**Moments.** Intro card: *The Reflection, Your Own Doubt*: "Everything you did not do, I did." Phase cards: *Doubt*,
*Desperate as You*. Enrage card: *Doubt Takes Root*.

### 4.5 Elder Gu (`elder_gu`): the Smuggler of Stoneford

He cannot be beaten here: he holds for a minute and escapes, dropping his ledger, and turns up again as Voss's purser
in Act III. His fight is a survival test with a thief's reward on the rafters.

**Numbers.** Lv 53, cannot be hurt, attack 644. Player: Spirit Awakening 8, about 8,000 HP, flight allowed. No par;
his clock is the fight (20 s, 40 s, 60 s).

**Arena.** Gu's Warehouse, 2560 wide. West and east catwalks at 176 (x 240–940 and 1620–2320; ladders at 280 and
2280). Four rafters at 264 from x 620 to 2000 (ropes at 1140 and 1480; ladders from the catwalks at 700 and 1920).
High crates (top 80) at 880 and 1630. The vault chest on the east rafter at (1920, 264).

| Phase | Opens | What changes |
|---|---|---|
| I · Business as Usual | start | Tide palm; Cargo Drop |
| II · Hired Blades | 20 s | Two gorge bandit adepts (existing); The Sluice at 25 s and 50 s |
| III · A Cornered Rat | 40 s | Enrage (existing); Smoke and Mirrors |
| (end) | 60 s | He flees with the ledger dropped (existing) |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Cargo Drop | three circles, umber, spiral glyph | under the rafter spans, the one nearest you and two more, r 70 | 1.4 s | 20% (≈ 1,600) and a 0.6 s stun | between the spans |
| The Sluice | floor, river blue, chevrons pointing west | the whole ground | 3.2 s | 30% (≈ 2,400), pushed 200 west and slowed | catwalks, rafters, high crates |
| Smoke and Mirrors | circle, grey | around him, r 160; then he blinks to the far catwalk | 1.0 s | 15% and blinded 3 s (accuracy −30%, as fog) | out of it |

**Enrage.** His 40 s phase is the enrage (pauses × 0.7, blows × 1.25); at 60 s the fight ends.

**Rewards.** First kill (his flight): the smuggler's ledger. Re-runs: Recollection, once a week. Signature:
**Tide-Palm Scroll** (new; a Water palm technique manual), 15% (pity 6). Seals: Clear Sight, Unbowed and his Feat;
no Swift. Feat **Light Fingers**: open his vault on the east rafter before he flees.

**Moments.** Intro card: *Elder Gu, the Smuggler of Stoneford*: "Everyone in this valley owes me something. Today,
it's you." Phase cards: *Hired Blades*, *A Cornered Rat*. His escape: a story beat, *Gu Slips Away*.

### 4.6 Hollow Behemoth (`hollow_behemoth`): the Siege-Breaker

The Hollow's ram at the siege of the two sects: the defenders hold the wall for four minutes while it breaks on them.
The wall is the arena, and in phase III the wall itself gives way.

**Numbers.** Lv 58, 92,008 HP, attack 750. Player: Heaven Glimpse 1–2, about 9,800 HP, flight allowed. Par 150 s
(to kill it; the siege is won by holding 240 s); the enrage fires at the siege's 180 s mark.

**Arena.** The Siege, 3840 wide. The battlement at 160 (x 640–2200; ladder at 1500; steps of 40, 80, 110 at 760–940).
Towers at 240 (x 420–640 and 2200–2420). The Behemoth at 3200; boarlets every 3 s from the east. East of 2420 there is
no high ground, so its markers there are lanes and rings.

| Phase | Opens | What changes |
|---|---|---|
| I · At the Gate | start | Stampede Lane; Drone Burst marked |
| II · The Brood | 60% | Boarlets (existing); Hollow Quake |
| III · The Wall Cracks | 30% | HP enrage (existing); Breach, and the room changes |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Stampede Lane | line along the room, grey, cracked-blade glyph | from it toward you, 1000 × 60 deep | 1.4 s | 30% (≈ 2,940), a knockback, a natal weapon broken | a step in depth, or on the wall |
| Drone Burst | line both ways | 200 × 70 deep | 1.0 s | 15% and +8 Hollowing (existing) | a step in depth |
| Hollow Quake | ring, grey | around it, r_in 120, r_out 380 | 1.6 s | 25% and slowed | hug it, or beyond 380 |
| Breach | circle, column | the battlement span nearest it (or yours, if you are on it), r 180 | 2.0 s | 35% and thrown off the wall | off that span |

**The room changes.** Each Breach that lands removes 360 of the battlement for the rest of the siege (a crumbled
span), at most two; boarlets then come through the gap.

**Enrage (the siege's 180 s mark): "The Hollow pours in."** Waves every 1.5 s (up to 12); the Behemoth's pauses × 0.6
and blows × 1.3; Hollow Quake every 7 s.

**Rewards.** First kill: the Siege Medal (quest) and the Mistjade Robe. Re-runs: Recollection, weekly (a 180 s
siege). Signature: **Hollow-Tusk Gauntlets** (new; gauntlets, Earth), 15% (pity 6). Feat **Siege-Breaker Broken**: it
falls before the siege ends.

**Moments.** Intro card: *Hollow Behemoth, the Siege-Breaker*; caption: "The ground shakes under the gate." Phase
cards: *The Brood*, *The Wall Cracks*. Enrage card: *The Hollow Pours In*.

### 4.7 Gate Guardian (`gate_guardian`): Warden of the Ascension Gate

The stone warden who decides who crosses from the valley to the Expanse. Its two phases exist in the data and do
nothing today. P9 builds them: first it weighs the soul, then it takes to the air, and only what can rise may pass.

**Numbers.** Lv 63, 106,818 HP, attack 865. Player: Heaven Glimpse 3, about 10,800 HP, double jump, flight allowed.
Par 120 s; enrage 240 s.

**Arena.** The Ascension Gate, 3840 wide. The arch at 220 (x 1550–2250; ladder at 1860). Six cloud rings at 200 in two
arcs: west x 760–980, 1000–1240, 1280–1520; east 2320–2560, 2600–2840, 2860–3080. The player comes in from the
east.

| Phase | Opens | What changes |
|---|---|---|
| I · The Gate Stands | start | Ring Sweep marked; Soul Gaze (a projectile) shows its lane |
| II · Weighing of Souls | 66% | `stone_skin`: physical damage taken × 0.6 (Qi and soul unchanged, a reason to use techniques); The Gaze That Follows |
| III · Trial of Flight | 33% | `take_wing`: it hovers at 210 over the arch, in reach from the arch, the rings, flight or range; Gate Quake; after each Quake it lands for 6 s |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Ring Sweep | line both ways, umber | 180 × 70 deep | 0.9 s (from 0.7) | 20% (≈ 2,160) and a knockback | a step in depth |
| Soul Gaze | thin line, violet | its lane, 320 long | 0.9 s | 12% soul | out of the lane |
| The Gaze That Follows | circle, column, violet | follows you 2.0 s, locks, r 100 | 2.0 s + 0.8 s locked | 25% soul (≈ 2,700) and slowed 2 s | be elsewhere when it locks |
| Gate Quake | floor within 900 of the gate, umber, spiral glyph | x 1000–2800 | 3.0 s | 40% (≈ 4,320) and a 1 s stun | a cloud ring, the arch, or beyond 900 |

**Enrage (240 s): "The Gate closes."** Gate Quake every 9 s, and the arch is no longer safe: only the rings.

**Rewards.** First kill: the Gate opens (the end of Act I). Re-runs: Recollection, weekly. Signature: **Gatekeeper's
Ring-Staff** (new; staff, Earth), 15% (pity 6). Feat **Stepped Through Heaven**: no Gate Quake touches you.

**Moments.** Intro card: *The Gate Guardian, Warden of the Ascension Gate*: "Only what can rise may pass." Phase cards:
*Weighing of Souls*, *Trial of Flight*. Enrage card: *The Gate Closes*.

### 4.8 Thousand-Eye Toad (`thousand_eye_toad`): Mirror of Mirrorwater Lake

The Expanse's Beast King under Mirrorwater Lake, with a swallowed Heavenly Flame, the Cold Lamp, burning in its belly
and a hide of mirror eyes that show what they last saw.

**Numbers.** Lv 68, 245,456 HP, attack 1,234. Player: Sage 2, about 11,500 HP, flight allowed. Par 180 s; enrage
360 s.

**Arena.** Toad's Hollow, 2560 wide. Ledges at 100 (x 600–880) and 200 (x 1180–1460, with a chest); a branch at 200
(x 240–480) by a vine; the egg nest on the ground at (2300, 860). East of 1460 there is no high ground; the nest mound
is its safe spot.

| Phase | Opens | What changes |
|---|---|---|
| I · The Lake Watches | start | Belly Slam, Tongue Lash, Leap marked |
| II · A Thousand Eyes Open | 50% | Dragonets (existing); Mirror Glare; Cold Lamp Breath |
| III · Lake Surge | 25% (new) | Lake Surge |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Belly Slam | ring, umber | around it, r_in 90, r_out 280 | 1.0 s (from 0.8) | 25% (≈ 2,875) and a knockback 140 | hug it, or beyond 280 |
| Tongue Lash | line ahead, jade chevrons toward it | 240 × 40 deep | 0.9 s | 15% and pulled 120 | a step in depth |
| Leap | circle, spiral glyph | on you, r 150; it lands there | 1.6 s | 30% (≈ 3,450) and a 0.8 s stun | out, or on a ledge |
| Mirror Glare | three lines across the depth, teal, spiral glyph | 120 wide each, at three eyes (one at your x) | 1.4 s | 20% and confused 2 s | between the lines |
| Cold Lamp Breath | cone, teal | ahead, 360 long, 30° | 1.3 s | 25% Qi, and frost patches (slow 30%) for 5 s | behind or beside it |
| Lake Surge | floor, river blue | the whole ground | 3.2 s | 35% (≈ 4,025) and slowed | the ledges, the branch, the nest mound (r 110 around the nest: the Toad never floods its own nest) |

**Enrage (360 s): "The lake rises."** Lake Surge every 11 s.

**Rewards.** First kill: the Cold Lamp Flame, the chapter 12 quest, the Stone Drum heart (legend chain). Signature:
**Thousand-Eye Mirror** (new treasure art: once a minute, shows hidden foes and confuses those it shows), 3% (pity 30).
Every 45 minutes; weekly tribute; the nest's egg. Feat **Unblinking**: never confused.

**Moments.** Intro card: *Thousand-Eye Toad, Mirror of Mirrorwater Lake*; caption: "A thousand eyes open on the
water." Phase cards: *A Thousand Eyes Open*, *Lake Surge*. Enrage card: *The Lake Rises*.

### 4.9 Tomb King of Sunscar (`tomb_king`): Three Thousand Years on the Throne

The desert king who wakes on his throne with the sun disc behind him and clay guards at his call. His markers are
light and shade: the sun stands east, behind the throne, and the only shade is the shadow each body throws west.

**Numbers.** Lv 77, 215,793 HP, attack 1,350. Player: Sage Sovereign 1–2, about 15,500 HP, flight allowed (sunlight
reaches it). Par 150 s; enrage 300 s.

**Arena.** The Throne, 2560 wide. Ledges at 100 (x 940–1220) and 200 (x 1520–1800); the throne at (1900, 690); the
King at 1700. The west third is far from any ledge (5 s), so the big marker's safety moves with the fight.

| Phase | Opens | What changes |
|---|---|---|
| I · The King Wakes | start | Glaive Sweep, Sun Flare marked; Sand Crescent shows its lane |
| II · Clay Court | 60% | Two Terracotta Wardens (existing); Noon of Sunscar |
| III · Sandstorm Crown | 30% | HP enrage (existing); Crown of Sand |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Glaive Sweep | line both ways, umber, cracked-blade glyph | 190 × 70 deep | 0.9 s (from 0.75) | 25% (≈ 3,875), a knockback, a natal weapon broken | a step in depth |
| Sun Flare | cone, ember | ahead, 300 long, 35° | 1.1 s | 25% Qi and burning | behind or beside him |
| Noon of Sunscar | floor, column, ember | the whole ground and the air | 3.0 s | 40% Qi (≈ 6,200) and burning 4 s | the shade: an ellipse r 90 at 130 west of the King and of each living Warden, checked at impact |
| Crown of Sand | rows: two of three struck, sand | the depth band in three rows along the whole room | 1.6 s | 25% | the free row |

Killing the Wardens removes their shade. It is a real choice: fewer blades, or more shelter.

**Enrage (300 s): "Sunset over Sunscar."** Noon every 12 s; pauses × 0.6.

**Rewards.** First kill: the Sunscar Throne Ember, the sun seal and its choice (the titles exist), the quest.
Signature: **Sunscar Crown** (new; a Sage-grade hat, Earth: the crown his fragments come from), 8% (pity 12). Daily;
weekly tribute. Feat **Unbroken Blade**: no natal weapon broken.

**Moments.** Intro card: *The Tomb King of Sunscar, Three Thousand Years on the Throne*: "Who wakes the King? Kneel, or
be buried with him." Phase cards: *Clay Court*, *Sandstorm Crown*. Enrage card: *Sunset over Sunscar*.

### 4.10 Comet Captain Rao (`pirate_captain`): Scourge of the Starsea Lanes

The pirate captain who drops from his junk onto the Alliance Gate forty seconds into the sect war and, cornered,
burns his nascent soul. The detonation is the game's oldest boss telegraph; P9 draws it true and gives the rest of
the fight the same language.

**Numbers.** Lv 80, 248,100 HP, attack 1,182. Player: Sage Sovereign 2, about 15,500 HP. Par 150 s from his landing;
the enrage fires at the war's 240 s mark (the war fails at 300 s).

**Arena.** The Sect War, 3840 wide. Wall-walks at 88 (x 900–1200 and 2000–2300); he lands at 3300, far from them, so
his markers are circles, cones and lanes.

| Phase | Opens | What changes |
|---|---|---|
| I · Boarding Party | he lands | Comet Cleave and Anchor Throw marked |
| II · Comet Fury | 40% | HP enrage (existing); Comet Rain |
| III · Burning Soul | 12% | The soul detonation (existing), drawn as it strikes |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Comet Cleave | cone, umber | ahead, 160 long, 40° | 0.8 s (from 0.6) | 25% (≈ 3,875) and a knockback | behind or beside him |
| Anchor Throw | line ahead, jade chevrons toward him | 330 × 26 deep | 0.9 s | 15% and pulled 200 to him | a step in depth |
| Comet Rain | four circles, ember | one on you, three within 400, r 90 | 1.6 s | 20% each and burning | the gaps |
| Burning Soul | circle, ember, doubled rim | around him, r 280 (now 118 deep, as drawn) | 3.0 s | 60% (≈ 9,300); guard halves, a dodge slips | outside the ring |

**Enrage (the war's 240 s mark): "The junk opens fire."** Comet Rain every 5 s; the pirate waves double.

**Rewards.** First kill: the Comet Tail Flame, the war's rewards, the Black Ledger's choice. Re-runs: Recollection,
weekly. Signature: **Comet-Hook Blade** (new; short blade, Metal), 15% (pity 6). Feat **Cannon-Proof**: no Comet Rain
strikes you.

**Moments.** Intro card: *Comet Captain Rao, Scourge of the Starsea Lanes*: "Strike your gong, little sect. My comets
are louder." Phase cards: *Comet Fury*, *Burning Soul*. Enrage card: *The Junk Opens Fire*.

### 4.11 Admiral Voss (`admiral_voss`): Master of the Blackmast Fleet

The admiral who taxes every lantern lane, fought on his own flagship, the first Presence the player's Presence meets.
The deck is long and flat with its high ground at the stern, so his guns work in rows along the depth, the one axis a
side-scroller's deck has to spare.

**Numbers.** Lv 90, 1,317,120 HP, attack 2,006. Player: Will Manifest 2, about 22,000 HP, the Presence. Par 240 s;
enrage 480 s.

**Arena.** The Flagship Deck, 2560 wide. The quarterdeck at 100 (x 260–540) and the mast-top at 200 (x 840–1120), with
ropes at 400 and 980; Voss at 1700; the chest at 2300. New: three powder kegs (breakable objects) at (1200, 700),
(1900, 900) and (2300, 760), inert until phase III.

| Phase | Opens | What changes |
|---|---|---|
| I · On My Deck | start | Cutlass marked; Broadside becomes rows |
| II · Gun Crews | 60% | Two gunners (existing); Chain Shot |
| III · Scuttle the Ship | 30% | HP enrage (existing); the kegs are lit, and relit every 30 s |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Starsteel Cutlass | cone, umber | ahead, 140 long, 45° | 0.8 s (from 0.5) | 20% (≈ 4,400) | behind or beside him |
| Broadside | rows: two of three struck, teal | the whole deck, by depth | 1.6 s | 25% Qi (≈ 5,500) and a knockback | the free row, the quarterdeck or the mast-top (the guns fire along the deck) |
| Chain Shot | two lines across the depth, grey, spiral glyph | 160 wide, at your x and 400 from it | 1.4 s | 20% and slowed 40% for 2 s | between them |
| Powder Kegs | a circle on each keg, ember, fuse counting down | r 150 | 5.0 s fuse; a keg you strike goes off 1.0 s later | 35% (≈ 7,700) and burning | outside; or strike a keg while he stands in its circle |

The kegs are World's objects. World resets them when it hears `telegraph_started` for `powder_kegs` (a room script, as
water answers `boss_phase` today).

**Enrage (480 s): "The magazine catches."** Broadside every 6 s; kegs every 15 s.

**Rewards.** First kill: the Admiral's Seal, 60 Sage Crystals and the title Breaker of the Blackmast (the quest).
Signature: **Blackmast Starsteel Sabre** (new; heavy sabre, Metal, Will grade), 8% (pity 12). Daily; weekly tribute.
Feat **Powder Monkey**: set off a keg with him inside its circle.

**Moments.** Intro card: *Admiral Voss, Master of the Blackmast Fleet*: "Every lantern lane pays the Blackmast. You'll
pay in full." Phase cards: *Gun Crews*, *Scuttle the Ship*. Enrage card: *The Magazine Catches*. The Presence clash
keeps its own effect.

### 4.12 General Kharn (`general_kharn`): Pyre-General of the Ashborn

An enemy, not a villain: he wants the lanterns' fire for his people's pyres, and at a fifth of his health he kneels
for judgement. He is the first Sphere clash, so his great marker makes the player's own Sphere a place to stand.

**Numbers.** Lv 92, 1,457,974 HP, attack 2,087. Player: Sphere Lord 1, about 26,000 HP, the Sphere. Par 240 s;
enrage 480 s.

**Arena.** Kharn's Pyre, 2560 wide, a fire room. Ledges at 100 (x 260–540) and 200 (x 840–1120), far west; Kharn at
1500. His own fires make the rest of the safety: burnt-out ground cannot burn twice.

| Phase | Opens | What changes |
|---|---|---|
| I · The General's Challenge | start | Cinder Glaive, Leaping Cleave, Pyre Rings marked |
| II · Keepers of the Flame | 60% | A Pyre-Keeper (existing); Pyre of the Fallen |
| III · Last Ember | 30% | HP enrage (existing); Ember Waves |
| (judgement) | 20% | He kneels (existing): spare or slay |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Cinder Glaive | cone, ember | ahead, 150 long, 40° | 0.8 s | 20% (≈ 5,200) | behind or beside him |
| Leaping Cleave | circle, ember | on you, r 110; he lands there | 1.2 s (from 1.0) | 30% (≈ 7,800); fire r 80 for 5 s (existing) | out of it |
| Pyre Rings | four circles, ember | at ±150 and ±300 from him, r 70 | 1.4 s, then burning 7 s (existing) | the existing burn | between them; each turns to ash when it goes out |
| Pyre of the Fallen | floor, ember | the whole ground; cast 3–10 s after a Pyre Rings burns out | 3.0 s | 40% (≈ 10,400) and burning | the ledges; any ash patch; inside your own Sphere while it holds against his |
| Ember Waves | three rings in turn, ember | from him: 0–150, 250–400, 500–650, 1.2 s apart | 1.2 s each | 20% each | in a gap as a wave passes |

**Enrage (480 s): "The pyre reaches the sky."** Pyre Rings leave no ash; Pyre of the Fallen every 13 s.

**Rewards.** First kill: Kharn's Glaive Shard, 90 Sage Crystals, the judgement and its debt. Re-runs follow the
judgement:

- **Spared:** *Kharn's Proving*, once a week at the War Camp: a spar with Kharn at his level, with every marker, no
  death. It pays the tribute and Ashborn standing for Act IV.
- **Slain:** *the Pyre Rite*, once a day: the Pyre-Keepers raise **Kharn's Cinder Shade** (a tinted twin, dungeon role)
  at the pyre.

Signature on either road: **Cinder Oath Glaive** (new; spear, Fire, Will grade), 8% (pity 12). Feat **Held Ground**:
answer every Pyre of the Fallen inside your own Sphere.

**Moments.** Intro card: *General Kharn, Pyre-General of the Ashborn*: "My people burn their dead with starlight.
Stand aside, or be the next fire." Phase cards: *Keepers of the Flame*, *Last Ember*. The kneel is a story beat,
*Kharn Kneels*. Enrage card: *The Pyre Reaches the Sky*.

### 4.13 Nebula Leviathan (`nebula_leviathan`): the Maw Between Islands

The field boss of the Nebula Deep, a flying leviathan with a Sphere of Space that swallows the current. Its Maw is a
no-flight room, so its reef branches are the high ground.

**Numbers.** Lv 99, 1,082,057 HP, attack 2,165. Player: Sphere Lord 2–3, about 27,000–29,000 HP, no flight here. Par
300 s; enrage 600 s.

**Arena.** The Leviathan's Maw, 3840 wide. Ledges at 100 (x 260–540) and 200 (x 840–1120); reef branches at 100
(x 1200–1440), 200 (1540–1780) and 100 (1880–2120); the Leviathan hovers near 2200. The east half is open.

| Phase | Opens | What changes |
|---|---|---|
| I · The Deep Wakes | start | Void Breath, Gravity Crash, Current Swallow marked |
| II · The Eel Tide | 60% | Two eels (existing); Star-Fall |
| III · Swallow the Sky | 30% | HP enrage (existing); Swallow the Sky |

| Marker | Shape and colour | Aim and size | Wind-up | If you stand in it | Safe |
|---|---|---|---|---|---|
| Void Breath | line ahead, violet | 460 × 100 deep | 1.3 s | 30% Qi (≈ 8,400) | a step in depth, or a branch |
| Gravity Crash | circle, violet, spiral glyph | on you, r 160 | 1.2 s (from 1.0) | 30% and a 40% chance of a 1 s stun | out of it |
| Current Swallow | ring with jade chevrons pointing in, then its maw | pull ring r 300; maw r 90 before it | 1.2 s, then a 2 s pull of 220 | the maw: 25% Qi | beyond 300, or on a branch or ledge |
| Star-Fall | five circles, violet | one on you, four within 500, r 80 | 1.6 s | 18% each and burning | the gaps |
| Swallow the Sky | floor within 1100 of it, violet, chevrons in | x ±1100 around it | 3.2 s | 45% Qi (≈ 12,600) and pulled | the branches, the ledges, or beyond 1100 |

**Enrage (600 s): "The Maw closes."** Swallow the Sky every 12 s; the current drifts toward the maw at 60 px/s the
whole time.

**Rewards.** First kill: 200 Sage Crystals, two scales and the codex entry (the quest). Signature: **Nebula Pearl**
(new; a Space jade), 3% (pity 30). Every 45 minutes; weekly tribute; Sect Service. Feat **Anchored**: never pulled into
the maw.

**Moments.** Intro card: *The Nebula Leviathan, the Maw Between Islands*; caption: "The stars in the nebula begin to
turn." Phase cards: *The Eel Tide*, *Swallow the Sky*. Enrage card: *The Maw Closes*.

### 4.14 The thirteen at a glance

| Boss | Phases (thresholds) | The mechanic that moves you | Enrage | Re-run and feat |
|---|---|---|---|---|
| Big Toad Tan | 50%, 25% | Wine Flood: climb a shelf | 180 s | daily; Dry Den |
| Riverbed Serpent | 50%, 25% | The River Rises: dry sand or a rock | 240 s | 45 min; Dry Feet |
| Drowned Abbot | 66%, 33% | Drowned Chant: ring your ledge's bell | 360 s | every 5th day; The Small Bells Answer |
| The Reflection | 50%, 25% | Tide of Doubt up, Broken Mirror down | 180 s | weekly rite; Unmoved |
| Elder Gu | 20 s, 40 s | The Sluice: catwalks and rafters | 40 s (flees at 60 s) | weekly; Light Fingers |
| Hollow Behemoth | 60%, 30% | Breach: the wall gives way | siege 180 s | weekly; Siege-Breaker Broken |
| Gate Guardian | 66%, 33% | Gate Quake: the cloud rings | 240 s | weekly; Stepped Through Heaven |
| Thousand-Eye Toad | 50%, 25% | Lake Surge: ledges, branch, nest mound | 360 s | 45 min; Unblinking |
| Tomb King | 60%, 30% | Noon of Sunscar: stand in a shadow | 300 s | daily; Unbroken Blade |
| Comet Captain Rao | 40%, 12% | Burning Soul: out of the true ring | war 240 s | weekly; Cannon-Proof |
| Admiral Voss | 60%, 30% | Broadside: the free row | 480 s | daily; Powder Monkey |
| General Kharn | 60%, 30% | Pyre of the Fallen: ash, ledge or Sphere | 480 s | weekly or daily by judgement; Held Ground |
| Nebula Leviathan | 60%, 30% | Swallow the Sky: the reef branches | 600 s | 45 min; Anchored |

---

## 5. Build order

**Big Toad Tan first.** He is the first boss every character meets (Qi Kindling 7–9). His design note already says he
teaches the pattern. His room is the simplest in the game: a flat floor and three shelves at 88 that one jump or a
ladder reaches, the worst point 2.3 s from safety. His fight is short and cheap to lose. His three markers are the
three lessons (step out, go up, read the floor). And `valley_run` meets him in its fifth section, so the fight
helper's marker reading is proven before any harder boss.

| Step | Contents | Acceptance |
|---|---|---|
| **P9a · The blocks, and Tan** | §3 whole: `mark()` and the new fields, `TelegraphRules`, the brain and authority scheduling, `resolve_telegraph`, `ground_patches`, `GroundDraw` and `_draw_telegraph`, the boss bar and incense, the six events and the catalogue entries, the two settings, `boss_records`, the Worthy Foes tab, the four titles. Fixes found in §1.4: drawn = hit for ground fire, hazards and the detonation; `boss_defeated` emitted (Untouched works); Tan's jars gate his drink. Tan per §4.1 | `boss_suite` for Tan; `valley_run` `sec_qk5`; `hazards_suite` and `ash_tide_suite` updated to the ellipse; `data_validation`, `contract_tests`, `perf_tests` green; screenshots of each marker through `--telegraph` |
| **P9b · The valley's waters** | The Riverbed Serpent and the Drowned Abbot: the floods marked, the repeat rise on `telegraph_started`, the bell answer | `boss_suite` for both; `sec_qu5` |
| **P9c · The heart and the wall** | The Reflection (the Mirror Rite), Elder Gu, the Hollow Behemoth (the breach spans). Recollection, if approved (§7 question 1) | `boss_suite` for the three; `sec_ht5`, `sec_sa5`, `sec_hg1` |
| **P9d · The Gate** | The Gate Guardian: `stone_skin` and `take_wing` built, the hover, the rings as safety | `boss_suite`; `sec_hg1`; a validation rule that every phase action is handled |
| **P9e · The Expanse** | The Thousand-Eye Toad, the Tomb King (moving shade), Comet Captain Rao (the true detonation) | `boss_suite` for the three; `sec_ae2`, `sec_ae4`, `sec_ae5` |
| **P9f · The Lantern Star Field** | Admiral Voss (rows, kegs), General Kharn (ash and Sphere safety; the Proving and the Rite), the Nebula Leviathan. The par calibration of their `hp_mult` (§7 question 5) | `boss_suite` for the three with par within 0.8–1.25; `sec_ls2`, `sec_ls5`, `sec_ls6`; `lantern_heart_suite` and `ash_tide_suite` still pass |

Each step ships with its CHANGELOG entry, commit and push. P9 sits after P6 (it uses the moments) and before v1.3, so
v1.3's bosses are written to this standard from the start.

---

## 6. Tests

### 6.1 `rules_tests` `boss_suite`

One case per boss, driven by a table (boss, room, band realm, event to start, the phase checks of §4). Each case:

1. **Set up.** A test character at the boss's band (`cu.realm_key` and `refresh_stats`, full HP), with `double_jump`,
   `dodge_dash`, `guard` and, where the band has them, `flight`, `presence` and `sphere` forced on
   (`Unlocks.force_unlock`).
   `Game.world.load_room(c, room, "")`. For event rooms, the room event is started and its clock advanced to the
   boss's spawn (Rao at 40 s); the Behemoth and the Reflection come from the event's fixed spawns.
2. **Engage.** Place the player 150 from the boss; tick `Game.enemies.tick(0.1)` until `boss_engaged`. No
   `attack_started` in the first 1.4 s (the intro hold).
3. **Phase I markers.** For each mechanic open in phase I, tick until its `telegraph_started`. Check its shape, size
   and wind-up (× 1.0). Then, from full HP each time:
   - inside at impact (no guard, no dodge): HP falls by `pct` × max HP within 2%, and the status lands;
   - at `TelegraphRules.nearest_safe` (with altitude for a ledge): no loss;
   - a dodge started 0.1 s before impact: `hit_dodged`, no loss;
   - guarding: half, except floors: full.
4. **Each threshold.** Chip the boss to just under the threshold (the test shortcut below) and tick: `boss_phase` with
   the right number and card; the phase's action (bandits, water at 30 after 4 s, stone skin's × 0.6, the Guardian's
   hover at 210, the Wardens' shade zones, the breach span gone); its new markers checked as in step 3.
5. **The enrage timer.** Set `ai.engaged_t` to `after_s − 0.5` and tick 1 s: `boss_enraged` (reason `timer`, stage 1),
   the pauses and the mechanic clocks shortened. Advance `stage2_s`: shares × 1.5, never above 0.68.
6. **The last phase.** `ai.phase` equals the last index. Set HP to 1 and land one real `basic_attack`: `boss_defeated`
   with the tally. Special endings: Gu's clock reaches 60 s and `boss_fled`; Kharn kneels at 20% and `judge_foe`
   gives `boss_defeated` with `judged`; Rao's detonation resolves and counts.
7. **The setting.** With `boss_windups` 1.5, a marker's wind-up and the boss's are × 1.5.
8. **Rewards.** First kill pays once; the weekly tribute pays once per week (`Clock.debug_offset_s` + 7 days pays
   again); pity at N − 1 guarantees the signature on the next kill; a seal is refused 9 levels above the boss;
   Clear Sight is false after step 3's hits and true in a scripted clean kill; titles at 8, 20, 36 and 51 seals.
9. **Rules.** `TelegraphRules.contains` on each shape at the rim ± 1 px, including depth (the ellipse); `is_safe` for
   every safe entry; `escape_s` for Tan's Wine Flood equals 2.3 s ± 0.1.

**Test shortcuts** (each labelled `test_shortcut`, as the valley run's are):

- *Careful chipping:* `boss.pools.hp = boss.pools.max_hp × x`, then `Game.enemies._check_phases(boss)` (the valley
  run's `long_boss_fight` and the existing detonation test do the same).
- *A long fight's clock:* `boss.ai.engaged_t` set forward.
- *Stepping there:* the actor's plane and altitude set directly, as the runs' `place()`.
- *A week passes:* `Clock.debug_offset_s`.
- *Unlocks:* `Unlocks.force_unlock`.

### 6.2 `valley_run` and the fight helper

The fight helper (`tests/prologue_run.gd` `fight()`) learns to read markers, as it learned to step out of wind-ups:

- `careful` (the default): when a live telegraph contains the player, `place()` at `TelegraphRules.nearest_safe`
  (with its altitude), and interact with an `answer` object (the Abbot's bell) when there is one.
- `careful = false` (a new player): stands in them. This proves no cycle kills from full HP.

The boss chapters must still pass with no more tries than today: `sec_qk5` (and its `sec_qu1` retry) for Tan; `sec_qu5`
for the Serpent and the Abbot; `sec_ht5` for the Reflection; `sec_sa5` for Gu; `sec_hg1` for the Behemoth's siege and
the Gate Guardian; `sec_ae2` for the Toad; `sec_ae4` for the Tomb King; `sec_ae5` for Rao's war; `sec_ls2` for Voss
(with his Presence clash); `sec_ls5` for Kharn (kneels, spared); `sec_ls6` for the Leviathan. In `sec_qk5` the run also
breaks the three jars before Tan's drink and checks that he does not heal.

### 6.3 `data_validation`

- Every boss has two threshold phases (today: one or more), a `card` on each, at least one `marker`, an
  `enrage_timer` and a `boss` block with `par_s`, `feat` and `signature`.
- Every phase action is one EnemyAuthority handles or a room script answers (so `soul_phase` can never pass silently
  again).
- Every marker: `pct` in (0, 0.45] (0.6 for the detonation); wind-up ≥ 0.9 s and ≥ `escape_s` + 0.4 s in the boss's
  room at the band's movement (moving safe zones excluded); floors ≤ 3.5 s; every `surface` safe entry exists in the
  room and is reachable at the band; `every_s` ≥ wind-up + 3 s.
- The burst cap: the mechanics' schedule never lets markers worth more than 0.6 land within 3 s.
- Every signature item, set and title exists; every string key exists.

### 6.4 Also

- `contract_tests`: the new and newly catalogued events are emitted only by their systems and each has a consumer.
- `perf_tests`: eight live markers, residue patches and a swarm on screen stay within budget.
- `ui_suite`: the Worthy Foes tab at 48 px targets; the settings' two new rows.
- Screenshots through `--telegraph` of each marker at wind-up 0.5 and at impact, and of the boss bar with notches and
  incense, compared at Normal and High contrast.

---

## 7. Open questions, with recommendations

| # | Question | Recommendation |
|---|---|---|
| 1 | Story bosses never come back. Add **Recollection**: at the meditation mat of a cave abode (`ja_cave_abode`, `cm_cave_abode`) or a retreat room, re-fight a beaten story boss in its instanced room at its own level, no death penalty, rewards once a week per boss, practice after that for the record only? | Yes, built in P9c. It is small (the rooms are already instanced; the Prologue's no-penalty rule exists) and it is the only way four of the thirteen get a loop |
| 2 | Seals only within 8 levels above the boss? | Yes. Otherwise an outgrown boss hands out Clear Sight and Swift for free. The record keeps any level |
| 3 | Make ground fire, hazard strikes and the detonation hit what they draw (the ellipse)? It makes them slightly easier in depth | Yes, in P9a, with `hazards_suite` and `ash_tide_suite` updated. A player must be able to trust the drawing |
| 4 | Markers deal a share of max HP, past defence? | Yes, as the tribulation, hazards, ground fire and the detonation already do. Gear should not erase a mechanic |
| 5 | Voss, Kharn and the Leviathan likely take 6–9 minutes today (the run chips two of them) | Par 240 s, 240 s and 300 s. Measure in `boss_suite` and lower `hp_mult` until the reference character lands within 0.8–1.25 × par |
| 6 | Kharn's re-run follows the judgement (a weekly Proving if spared, a daily Cinder Shade if slain)? | Yes. It keeps the choice meaningful, and it needs only a trial-role twin and a tinted twin of an existing enemy |
| 7 | Do the longer wind-up settings still earn seals and Swift? | Yes. Accessibility should not gate rewards; par is loose enough |
| 8 | The Ninth Presence (12× HP, the Presence Trial's finale) is a boss in all but role | Leave it out of P9; give it the story-boss role and a design of its own in v1.3's pass, when the Presence Trial is revisited |
| 9 | The Reflection takes the player's level on the weekly rite, not its fixed 36? | Yes. It is the one boss whose lore says it should, and it keeps the rite worth doing |
