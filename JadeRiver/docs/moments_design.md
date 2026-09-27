# P6 · Moments: the animation system (design and build brief)

This page is the design half of P6 in `docs/roadmap_master_ui.md` (§3 row P6; §2.1 rows M5–M9 and M22–M25;
conflict C11). It also plans findings F1, F2 and F4 of `docs/review-v12.md` (e) and change ranks 12–14 of its part
(f). The approved breakthrough is mockup `docs/mockups/05_breakthrough.png` (P3, decision 6 in the roadmap's §6). The
research behind it is `docs/research/ui_reference_notes.md` §2 and §10–§12 (feedback, and boss presentation, where no
reference's intro staging could be verified, so the intro below is Jade River's own).

P9 (`docs/boss_design.md` §3.9) depends on this page for the boss intro card, the phase card and the loot fountain.
P8b (`docs/soul_bands_design.md`) adds one row to it.

The build of P6 follows this page after the script refactor now in progress is merged. File and line references are
to commit c0e5225; the refactor will move lines, so the build finds each call by its `_on_event` branch name.

---

## 0. The brief

**Role.** You are adding a data-driven moments system to a Godot 4.5 offline-first game. Its simulation is pure rules
(`scripts/simulation/rules/`) and authorities that own state and emit events (`scripts/simulation/authority/`).
Presentation (`world.gd`, `hud.gd`, `scripts/presentation/`) listens to `GameEvents.event` and never changes state.
Content is generated from `tools/data/*.py` into `data/*.json`.

**Goal.** The big beats of the game land: a breakthrough is named, felt and itemised; a boss arrives, changes and
falls where the player can see it; a rare find is seen from across the room; a technique learned in a later realm
looks like one. All of it is one table of rows, not effects scattered through `world.gd`.

**Definition of done (P6).**

1. `data/moments.json` from `tools/data/moments.py`: one row per moment kind (§2), with trigger, duration, layers,
   input lock, queue rule and art (§3).
2. `MomentView` in `scripts/presentation/` plays the rows from events (§4). The `world.gd` calls listed in §4.8 move
   into rows.
3. The escalation curve: a `vfx` block on every technique in `techniques.json`, the tier table, multi-hit numbers,
   particles by element, the loot fountain and the breakthrough fanfare (§5).
4. `rules_tests` `moments_suite` (§7), `data_validation` and `contract_tests` rules; `perf_tests` within budget with a
   moment and a sword swarm on screen; `docs/CHANGELOG.md` entry per step.

**Constraints.**

- **Presentation only.** No moment decides, delays or changes anything in the simulation. The simulation is never
  paused or slowed by a moment; the only time dilation is the hit-stop CombatAuthority already owns
  (`combat_authority.gd:325, 1076`). The headless suites run without `MomentView` and give the same results.
- **No new body pose (C11, `AGENTS.md`).** Moments are overlays, FX kinds, camera and sound. The character keeps the
  registered poses the player node already chooses (the breakthrough channel may show the existing `meditate` pose,
  as mockup 05 does). A breakthrough stance or a boss roar pose would go through `AGENTS.md`'s full review and is not
  part of P6.
- **Input.** No moment locks input for more than 1.5 s (F4), and none locks it in a fight.
- **Colour.** No new hex literal outside `UiKit` (§6).
- **No new HUD button (C14).**
- **Settings.** Screen shake, Bright flashes, Damage numbers, Vibration and Captions keep working; a Reduce motion
  setting is added (§4.6).

**Order of work:** contract and data → `MomentRules` and `MomentView` → moved effects → new layers and FX kinds →
sounds and art → strings → tests → docs.

---

## 1. What exists

### 1.1 Effects that become moments

Every progression, boss and reward effect in `world.gd` `_on_event` (`world.gd:355-641`). "At" offsets are from the
player's feet; colours are `UiKit` constants unless written as a hex literal.

| Event (payload keys read) | `world.gd` | FX kinds and parameters | Colour | Shake | Text | Sound |
|---|---|---|---|---|---|---|
| `breakthrough_started` (`duration`) | 603–604 | `ring` r 90 for `duration` (3.0 s) | `QI` | — | — | — |
| `breakthrough_succeeded` (`to`) | 458–462 | `spiral` at −20, 1.6 s | `PALE_GOLD` | 0.2 s | realm label (`ContentDB.realm_label`) 28 px at −150, 2.5 s | `breakthrough` |
| `breakthrough_failed` | 605–607 | — | `RED` | — | `world_view.breakthrough_failed` 24 px at −150, 2.5 s | `fail` |
| `heavenly_phenomenon` `kind` = `cloud` | 588–602 | `heaven_cloud` at −20, 5.5 s; NPC barks within 900 px, 4 s | `#f5c86a` | — | barks `world_view.phenomenon_cloud_0..2` | `breakthrough` |
| `heavenly_phenomenon` `kind` = `lightning` | 588–602 | `heaven_storm` at −20, 6.0 s; NPC barks | `#9fc4ff` | 0.25 s | barks `world_view.phenomenon_storm_0..2` | `thunder` |
| `level_changed` (`level`) | 615–616 | — | `PALE_GOLD` | — | `world_view.level` 22 px at −160, 2.0 s | `level` (AudioDirector) |
| `body_level_changed` (`value`) | 613–614 | — | `#f0a060` | — | `world_view.body_level` 20 px at −140, 2.0 s | — |
| `pill_cloud` (`quality`) | 574–587 | `pill_cloud` at −70, 3.5 s; NPC barks within 700 px, 3.5 s | `#ffd76a` halo, `#ff9a6a` soul | 0.12 s | `world_view.pill_cloud_<quality>` 26 px at −190, 3.0 s | `breakthrough` |
| `weapon_awakened` | 499–502 | `wave` r 140, 0.8 s | `#ffd27a` | — | — | `breakthrough` |
| `room_event_started` (`event`) | 638–639 | — | `RED` | — | `event.<id>` 30 px at the camera −180, 3.0 s | — |
| `boss_phase` | 640–641 | — | — | 0.3 s | — | `boss_roar` (AudioDirector) |
| `loot_dropped` (`items`) | 369–373 | one `LootView` per item: a 36 px bounce over 0.5 s; a 110 px beam for Fine and better (`loot_view.gd:38-46`) | quality colour | — | label 16 px (`loot_view.gd:56-59`) | — |

### 1.2 Combat and traversal feedback that stays in `world.gd`

These fire many times a second or answer one input. They stay where they are; P6e scales the technique ones by tier
(§5).

| Event | `world.gd` | FX, colour, shake, text, sound |
|---|---|---|
| `hit_landed` | 400–415 | `number` 22 px (+8 on a crit), 1.0 s: `PAPER` on a foe, `RED` on the player, `GOLD` crit, `QI`, `SOUL`; `spark` 0.25 s in the element colour (`SpriteCache.element_color`, from `data/elements.json`); shake 0.25 s when the player loses over 15% of max HP, 0.12 s on a crit; `hit`, `hit_crit`, `hurt` |
| `attack_started` | 435–447 | technique: `slash` r 46, 0.3 s, element colour; `wave` at the hitbox reach, 0.45 s, when `both_sides`; `technique`. Basic: `swing`. Enemy: `tell` |
| `parried` | 431–434 | `flash` r 30, 0.25 s, `PALE_GOLD`; "Parry" 22 px `GOLD`; `parry` |
| `hit_missed`, `hit_immune`, `hit_dodged` | 425–430 | "Miss" and "Immune" 18 px `MIST`; "Evade" 18 px `BRIGHT_JADE` |
| `hazard_warned`, `hazard_struck` | 416–424 | a sound by hazard (`rumble`, `charge`, `hiss`, `tell`); the hazard's name 17 px `PALE_GOLD`, or answered in `BRIGHT_JADE` |
| `landed` | 375–384 | plunge: `ring` r 60, 0.35 s, `PALE_GOLD` α 0.8; `dust` 0.4 s; shake 0.2 s; `rumble`. A fall over 120: `ring` r 34, 0.3 s; `land` |
| `art_used`, `volume_entered`, `wall_kicked`, `fell_out` | 385–399 | glide `dust` `BRIGHT_JADE` α 0.5; `spark` `PAPER` 0.25 s; `hud.fell` 18 px `MIST`; `dodge`, `water_step`, `land` |
| `actor_defeated` | 448–449 | `dust` 0.5 s; `enemy_die` (`audio_director.gd:140`) |
| `object_hit`, `object_broken` | 450–457 | hit flash 0.15 s; `spark` `PALE_GOLD` 0.2 s; `dust` 0.5 s; `hit`, `break` |
| `artifact_detonated` | 464–468 | `wave` `#ff9a5a` r 180, 0.5 s; `flash` `#ffe0a0` r 90, 0.35 s; shake 0.35 s; `rumble` |
| `talisman_used` | 469–478 | attack: `wave` `#ff8a4a` or `#9fd8ff` r 90 + `flash` `#fff0c0` r 50; defence: `wave` `#c8ccd0` r 46; other: `spark` `#e8d99a`; `technique` |
| `item_blooded`, `natal_broken` | 479–486 | `spark` `#c0303a`, "·" 34 px `#d23a44`; `flash` `#ff6a5a` r 70, shake 0.3 s, `break` |
| `array_deployed`, `array_faded` | 487–490, 503–504 | `wave` in `FxLayer.ARRAY_COLOURS` (`fx_layer.gd:8`) at the array's radius; `forge`, `ui_close` |
| `artifact_skill_used` | 493–498 | `wave` `#ffd27a` or `#b18de2`; `surge` |
| `illusion_cast`, `illusion_broken` | 505–523 | a pale copy of the avatar; `wave` and `spark` `SOUL`; `technique` |
| `melody_pulse`, `melody_changed` | 524–534 | `ring` jade at the pulse radius; two `note`s `#8fe8cf` and `PALE_GOLD`; `wave` `#8fe8cf`; `meditate` |
| `sword_released`, `sword_returned` | 535–537 | `spark` `#dff3ff`; `forge` |
| `treasure_used` | 538–564 | bell: two `wave`s `PALE_GOLD`, `GOLD`, `bell`; pagoda: `pagoda` `BRIGHT_JADE` 4.0 s; mirror: `flash` `#bfe8ff`; seal: `seal_slam` `BRIGHT_JADE`, shake 0.25 s; cauldron: `spiral` `QI`; banner and gourd: `ring` `QI` or `SOUL` r 110; palm: `talisman_wave` `PALE_GOLD` 540 long, shake 0.3 s, `breakthrough` |
| `wisp_struck`, `projectile_*` | 565–573, 619–620 | `spark` `QI`, `#bfe8ff`, `SOUL`, `PAPER`; burst: `wave` `#ffd76a` + `flash` `#fff0b0`, shake 0.15 s, `break` |
| `meditation_tick` | 608–612 | `motes` `QI`, `BRIGHT_JADE` at a spring, `#f4ecd5` with no Qi |
| `player_revived`, `dodged`, `node_gathered`, `loot_picked`, `emote_played` | 617–637 | `flash` `BRIGHT_JADE` r 60; `dust`; `motes` `BRIGHT_JADE`; `coin`, `pickup`, `dodge`; the emote's text 20 px `PAPER` |
| `enemy_aggro` | 362–364 | "!" 26 px `GOLD` above the foe |
| a refused intent | 253–254; `player.gd:139, 248, 340` | the reason 18 px `MIST`, 1.6–1.8 s |

### 1.3 The camera, the HUD and the sound

| Where | What |
|---|---|
| `world.gd:48, 304-310` | One `shake` value in seconds. The camera offset is random ±4 px across, ±3 px up, × `shake / 0.25`, while the `screen_shake` setting is on; the camera position snaps to 2 px. Writers take the larger of old and new |
| `hazard_view.gd:86, 115` | Shake 0.2 s near a hazard strike; 0.35 s on a tribulation bolt |
| `combat_authority.gd:325, 672-673, 1076` | Hit-stop 0.05 s, 0.1 s on a crit (`stats.py:125`). Simulation, not presentation |
| `enemy_view.gd:178` | The red "!" 26 px wind-up tell |
| `hud.gd:669-671, 1903-1914` | Toasts: at most 3, at (810, 300), 410 wide; 3.2 s, or 5.0 s with a sub line; `PALE_GOLD`, `RED` or `BRIGHT_JADE` by kind |
| `hud.gd:722, 1870-1875` | The room banner: name 34 px `PALE_GOLD` at y 76, region 16 px `MIST`, 3.4 s, slides 30 px |
| `hud.gd:1018-1022, 1877-1901` | The fortune card: 9 s under the banner, `bell` |
| `hud.gd:57-58, 662-667, 695-696` | Captions for sound-only cues (`boss_phase` → "boss roar"), 2.6 s, when Captions is on |
| `hud.gd:659-660, 805-808` | Vibration: 120 ms on `breakthrough_succeeded`, 200 ms on a grave wound |
| `hud.gd:1916-1926` | The boss bar `Rect2(340, 118, 600, 14)`, name 18 px above it |
| `hud.gd:1964` | The tribulation panel (bolts done and left, "move") |
| `hud.gd` toasts for moments | bottleneck 728–729, achievement 732–733, title 785–786, "appears" 795–797, rare pill 802–804, craft level 886–888, guild rank 1043–1044, body tier 1065–1066, tribulation 1071–1080 (with its own `thunder`), self-detonation 1101–1102, field boss defeated 1228–1229, weapon awakened 1263–1264, pet evolved 1265–1266 |
| `audio_director.gd:7-10, 133-140` | `EVENT_SFX` plays a sound per event name, including `level_changed` → `level` and `boss_phase` → `boss_roar` |

### 1.4 FX kinds in `fx_layer.gd`

Transient kinds, added with `fx.add(kind, pos, {color, radius, dur, facing, text, size, vel})`; at most 160 live
(`fx_layer.gd:17-22`).

| Kind | Lines | Draws |
|---|---|---|
| `number` | 24–27, 54–56 | outlined text rising 70 px/s (90 on a crit), easing out, fading after 60%; crit +8 px |
| `spark` | 57–63 | 8 squares flying out to r 28, 6 px shrinking to 2, and a white core r 10 |
| `slash` | 64–71 | a 9-point arc of `radius`, 8 px thinning to 2, with a white inner line |
| `dust` | 72–75 | 5 puffs spreading |
| `ring` | 76–79 | one ellipse (depth × 0.35) growing from 0.3 to 1.3 × `radius`, 4 px |
| `note` | 80–83 | a quaver that rises and sways |
| `wave` | 84–87 | one ellipse growing from 0 to `radius`, 10 px thinning to 2 |
| `spiral` | 88–92 | 24 squares spiralling up |
| `motes` | 93–97 | 6 squares rising 70 px |
| `flash` | 98–100 | a disc to 1.5 × `radius`; alpha 0.5, or 0.15 with Bright flashes off |
| `pagoda` | 101–112 | a four-storey pagoda dropping onto a foe |
| `seal_slam` | 113–123 | a seal falling 200 px, then a wave |
| `talisman_wave` | 124–130 | a blade of light `radius` long in front |
| `pill_cloud` | 131–142 | 14 cloud puffs and 10 sparks over a furnace |
| `heaven_cloud` | 143–154 | a column of light 68 px wide, a cloud bank 620 px wide at −320, 14 motes |
| `heaven_storm` | 155–174 | a dark bank 820 px wide, lit 3 times a second, a bolt on each lit beat |
| `text` | 175–177 | outlined text fading after 70% |

Also drawn from state each frame: arrays (265), ground fire (249), the Presence (216), the Sphere (196) and
projectiles (320).

### 1.5 The sound synth

`tools/audio/sfx.py` (built by `tools/audio/build_audio.py` from `tools/audio/synth.py`) has 45 effects and three
ambience loops. Played by `Audio.play(id)` (`audio_director.gd:75`). The ones moments use today: `breakthrough` (2.6 s:
a gong at 105 Hz, a drum, ten rising chimes; `sfx.py:399`), `level` (1.5 s: a guzheng run and three chimes; 430),
`unlock` (1.3 s: two small bells; 442), `bell` (the Stilling Bell; 555), `thunder` (541), `boss_roar` (209), `fail`
(418), `coin` (385), `rumble` (521).

### 1.6 What the audit found

1. **Effects cannot be triggered from data** (M9). Every effect is a hard-coded branch; nothing states a duration,
   what may overlap, or what a row needs drawn.
2. **The Damage numbers setting does nothing.** It is stored (`account_state.gd:48`, `settings_page.gd:5`), but
   `FxLayer.numbers_enabled` (`fx_layer.gd:11`) is never set, and `world.gd:410` checks the HUD reveal, not the
   setting. P6a wires it.
3. **Two sounds at once.** A major breakthrough plays `breakthrough` twice: once for the breakthrough
   (`world.gd:462`) and once for the cloud phenomenon that follows it in the same pass (`world.gd:594`). A tribulation
   plays `thunder` twice: `hud.gd:1073` and `world.gd:594`.
4. **Silent milestones.** `dao_tier_up` and `profession_rank_up` reach the player nowhere: no toast, no effect, no
   sound. Their only listeners are the unlock service and the stat refresh.
5. **Two moment events are outside the contract.** `level_changed` (`progression_authority.gd:368`) and
   `room_event_started` (`world_authority.gd:1380`) are emitted but not in `tools/data/contract.py`, so
   `contract_tests` checks neither.
6. **`loot_dropped` does not say where the loot came from.** Its payload is `room, items, x, y`
   (`world_authority.gd:863`); a boss's drop, a chest's and a jar's look alike, so a fountain cannot tell them apart.
7. **The pill cloud's colours disagree with the quality colours.** A Halo pill's cloud is gold (`#ffd76a`) and a
   Soul pill's orange (`#ff9a6a`); `grades.json` `quality_colors` gives `pill_halo` orange (`#e8764c`) and
   `pill_soul` pale violet (`#f2e6ff`).
8. **The failure line falls back to ids.** `hud.gd:731` reads `failure.<id>`; none of the seven failure ids in
   `data/failures.json` has that string, so `ContentDB.text` shows the capitalised id (`content_db.gd:180-186`).
9. **`boss_defeated` names the def as `enemy`.** Today its payload is `room, enemy, role, clean` with `enemy` a def
   id (`enemy_authority.gd:24`). `docs/boss_design.md` §3.10 plans `enemy` as the uid plus `def`. The boss rows read
   whichever the contract declares (§3.7), and P9a changes both together.
10. **The tribulation's storm lasts 6 s** of a rite that runs up to a minute and more; the sky clears while bolts
    still fall.
11. **`battery_saver` is stored and read nowhere** (`account_state.gd:49`).

---

## 2. The moment table

### 2.1 The rows

Priority orders the screen (§4.4): 90 cuts a lower row, the rest queue. "World" rows (priority 0) have no screen part
and never queue. Duration is the screen part; world layers may run longer. Lock is the time the HUD ignores world
input from the row's start. In "When", "actor" means the payload's actor is the active character; "—" is no filter.

| # | Row | Trigger (catalogue name · payload keys) | When | Pri | Dur s | Lock s | Two at once | Art and sound | Step |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `breakthrough_channel` | `breakthrough_started` · actor, from, to, risk, duration | actor is active | world | 3.0 | 0 | plays at once | — | P6a |
| 2 | `breakthrough_minor` | `breakthrough_succeeded` · actor, from, to, major, formation | `major` false | 60 | 1.8 | 0 | absorbs `level_changed`, `realm_changed`, `system_unlocked` (2) | ink band; `level` | P6a, P6b |
| 3 | `breakthrough_major` | `breakthrough_succeeded` | `major` true | 70 | 4.0 | 1.5, tap skips | absorbs `level_changed`, `realm_changed`, `system_unlocked` (2), `tribulation_result` (survived); silences `heavenly_phenomenon` (cloud), whose clouds still play | ink band; `brush_stroke`, `seal_press` new | P6b |
| 4 | `breakthrough_failed` | `breakthrough_failed` · actor, failure_id, losses, injuries, recovery | actor | 60 | 2.4 | 0 | absorbs `tribulation_result` (failed) | — | P6a, P6b |
| 5 | `realm_phenomenon` | `heavenly_phenomenon` · actor, kind, realm, room, people | `kind` = cloud | world | 5.5 | 0 | plays at once; silent (the breakthrough row has the sound) | — | P6a |
| 6 | `tribulation` | `tribulation_started` · actor, from, to, bolts, waves | actor | 80 | held | 0 | absorbs `heavenly_phenomenon` (lightning); held until `tribulation_result`, at most 120 s | — | P6a, P6b |
| 7 | `level_up` | `level_changed` · actor, level (into the catalogue in P6a) | actor | world | 1.0 | 0 | folded into 2, 3 when in the same pass | `gong_short` new | P6a, P6b |
| 8 | `body_level` | `body_level_changed` · actor, value | actor | world | 2.0 | 0 | folded into 9 when in the same pass | — | P6a |
| 9 | `body_tier` | `body_tier_reached` · actor, tier, name | actor | 50 | 1.6 | 0 | queues | ink band; `bell` | P6b |
| 10 | `dao_tier` | `dao_tier_up` · actor, dao, tier | actor | 50 | 1.8 | 0 | queues; tier 6 uses the large band, 2.4 s | ink band; `bell` | P6b |
| 11 | `title_earned` | `title_changed` · actor, title, earned | `earned` true | 40 | 1.6 | 0 | folded into 13 and into P9's `boss_defeated` seals; in a fight, a toast | seal; `seal_press` | P6b |
| 12 | `craft_mastery` | `profession_rank_up` · actor, craft, rank | actor | 50 | 1.6 | 0 | queues | ink band; `unlock` | P6b |
| 13 | `guild_rank` | `guild_rank_changed` · actor, craft, rank, title | actor | 50 | 1.6 | 0 | absorbs `title_changed` | ink band; `unlock` | P6b |
| 14 | `pet_evolution` | `pet_evolved` · actor, pet, from, stage, branch | actor | 50 | 1.6 | 0 | queues | ink band; `unlock` | P6b |
| 15 | `weapon_awakened` | `weapon_awakened` · actor, item, skill, legend | actor | 50 | 1.6 | 0 | queues | ink band; `bell` | P6a, P6b |
| 16 | `rare_pill` | `pill_cloud` · actor, recipe, quality | — | world | 3.5 | 0 | plays at once | `rare_chime` new | P6a |
| 17 | `boss_intro` | `enemy_aggro` · enemy, target, def | target is active; the def's role is a boss role; first aggro of this boss in this visit | 90 | 2.0 | 0 (1.5 from P9a) | cuts any lower row | letterbox; `boss_sting` new | P6c |
| 18 | `boss_phase` | `boss_phase` · enemy, phase, action | — | 90 | 1.2 | 0 | cuts any lower row; dropped if it waits 1.0 s | ink band; `boss_roar` | P6a, P6c |
| 19 | `boss_defeated` | `boss_defeated` · room, enemy, role, clean | — | 70 | 2.4 | 0 | absorbs `achievement_unlocked` (the Untouched line) | ink band; `boss_fall` new | P6c |
| 20 | `field_boss_defeated` | `field_boss_defeated` · room, enemy | — | 70 | 2.4 | 0 | as 19 | ink band; `boss_fall` | P6c |
| 21 | `loot_fountain` | `loot_dropped` · room, items, x, y, source (`source` from P6c, §3.7) | `source` is boss, field_boss, chest, tower or rift | world | 0.9 | 0 | plays at once | `coin` | P6c |
| 22 | `rare_drop` | `loot_dropped` | an item is rare (§3.4) | 40 | 1.8 | 0 | rare drops within 1.5 s merge into one strip (3 names, then "+N"); in a fight, a toast | beam; `rare_chime` | P6d |
| 23 | `story_beat` | `quest_completed` · actor, quest, name, kind | `kind` main and the quest closes its chapter | 60 | 2.6 | 0 | waits for the dialogue page to close; in a fight, a toast | letterbox, ink band; `bell` | P6d |
| 24 | `trial_opens` | `room_event_started` · actor, room, event, duration (into the catalogue in P6a) | actor | 60 | 1.8 | 0 | queues; ends on leaving the room | ink band; `bell` | P6a, P6d |
| 25 | `boss_intro_again` | `boss_engaged` · enemy, def, room, level, first | `first` false | 90 | 0.8 | 0 | as 17 | — | P9a |
| 26 | `boss_enrage` | `boss_enraged` · enemy, def, reason, stage | — | 90 | 1.0 | 0 | as 18 | vignette | P9a |
| 27 | `boss_escape`, `boss_kneels` | `boss_fled` · enemy, def, room; `foe_surrendered` (Kharn) | the story boss | 60 | 2.6 | 0 | as 23 | letterbox | P9c, P9f |
| 28 | `soul_band_won` | `band_worn` · actor, band, slot, replaced, over, word, chance | actor | 60 | 1.8 | 0 | queues | `band_rise` FX kind (P8b); `bell` | P8b (v1.3) |

Rows 25–28 are listed so the data shape is proved against them; P9 and P8b add them with their events. From P9a,
row 17's trigger becomes `boss_engaged` with `first` true (§2.4).

**No row needs a new body pose.** New art for P6 is one UI asset, the ink band (an HD kit overlay built by
`tools/ui/build_ui_hd.py`, §3.3). Everything else is drawn by `FxLayer` and `MomentView` from shapes, or synthesised.

### 2.2 The layers of each row

Screen layers draw on two canvas layers (§4.1): **under** the HUD (dim, vignette, flash, letterbox) and **over** it
(band, strip, card, stats, chip, seal). Text sizes are screen px; "display" is Cormorant Garamond Bold through
`UiKit.draw_text(..., display = true)`.

**Progression**

| Row | Screen (text source) | Camera | World FX (kind, parameters) | Sound, buzz |
|---|---|---|---|---|
| 1 `breakthrough_channel` | — | — | `ring` `QI` r 90 for `duration` at the actor | — |
| 2 `breakthrough_minor` | strip at y 170, 0.1–1.8 s: from ➤ to (`realm.<key>`, the stage band word after P5b) 30 px `PALE_GOLD`; "Level N ▲" from the absorbed `level_changed` 20 px `BRIGHT_JADE`; an Opens chip per absorbed `system_unlocked` (its `label`) at 0.5 s | none (today 0.2 s; question 3) | `spiral` `PALE_GOLD` at −20, 1.6 s; `ring` `PALE_GOLD` r 70, 0.5 s | `level`; buzz 60 ms |
| 3 `breakthrough_major` | the three beats of §2.3 | shake 0.2 s at 0.6 s | `converge`, `pillar`, `ring` ×3 (§2.3) | the fanfare (§5.9); buzz 120 ms |
| 4 `breakthrough_failed` | dim `INK` α 0.3, 0–1.2 s; strip at y 170: `world_view.breakthrough_failed` 30 px `RED`, the cause `failure.<failure_id>` 20 px `PAPER`, `recovery` 18 px `MIST`; after a failed tribulation, `moment.tribulation.struck` ("struck S of B bolts") | — | `spark` style `shard`, 12, `MIST`, at −60 (the channel ring breaking) | `fail` |
| 5 `realm_phenomenon` | — | — | `heaven_cloud` `HEAVEN_CLOUD` at −20, 5.5 s; barks as today | none (the breakthrough has it) |
| 6 `tribulation` | band at y 170, 0–1.6 s: `hud.tribulation_started` (bolts) 34 px `PALE_GOLD`, `hud.tribulation_hint` 18 px `PAPER`; vignette `INK` α 0.25 on the upper edge, held; the HUD's tribulation panel stays | shake 0.25 s at 0 | `heaven_storm` `HEAVEN_BOLT` at −20, laid again every 5 s while held; barks as today | `thunder` once |
| 7 `level_up` | — (the world text is enough) | — | `ring` `PALE_GOLD` r 40, 0.4 s; `text` `world_view.level` 22 px `PALE_GOLD` at −160, 2.0 s | `gong_short` |
| 8 `body_level` | — | — | `text` `world_view.body_level` 20 px `BODY` at −140, 2.0 s | — |
| 9 `body_tier` | strip at y 170: `name` 30 px `PALE_GOLD`, `moment.body_tier.sub` 18 px `MIST` | — | `ring` `BRONZE` r 80, 0.6 s; `dust` | `bell` |
| 10 `dao_tier` | strip at y 170: `daos` name · `moment.dao.tier` (N) 30 px `PALE_GOLD`; the tier's line from `daos.json` `tiers` 18 px `MIST`. Tier 6: the large band, 64 px title, 2.4 s | — | `converge` 16 motes r 160, 0.6 s, in the Dao's colour (§6) | `bell` at 0.4 s |
| 11 `title_earned` | strip at y 200: `titles` name 30 px `PALE_GOLD`; the title's bonus (`UiKit.affix_text`) 18 px `MIST`; a seal 40 px `RED` stamped at 0.25 s | — | — | `seal_press` at 0.25 s |
| 12 `craft_mastery` | strip at y 200: `craft.<craft>` · `ui.guild.rank_<rank>` 30 px `PALE_GOLD` (adept, expert and master exist; P6b adds grandmaster) | — | `converge` `BRIGHT_JADE` r 120, 0.6 s | `unlock` |
| 13 `guild_rank` | as 12, plus `moment.guild.title` (the absorbed title's name) 18 px `MIST` | — | as 12 | `unlock` |
| 14 `pet_evolution` | strip at y 200: `hud.grows_into_a` (pet name, `branch` or the stage's name) 28 px `PALE_GOLD` | — | `spiral` `PALE_GOLD` at the pet, 1.2 s; `ring` r 60 | `unlock` |
| 15 `weapon_awakened` | strip at y 200: the item's name 30 px in its grade colour; `hud.weapon_awakened_sub` (`skill`) 18 px `PAPER` | — | `wave` `PALE_GOLD` r 140, 0.8 s; `pillar` `GOLD` 60 wide, 300 high, 0.8 s | `bell` |
| 16 `rare_pill` | — | shake 0.12 s | `pill_cloud` in `quality:<quality>` at −70, 3.5 s; `text` `world_view.pill_cloud_<quality>` 26 px at −190, 3.0 s; barks as today | `rare_chime` (today `breakthrough`) |

**Bosses**

| Row | Screen (text source) | Camera | World FX | Sound |
|---|---|---|---|---|
| 17 `boss_intro` | letterbox 64 px, in 0–0.3 s, out 1.7–2.0 s; card over the HUD at y 250: the boss's name (`enemies` name) 56 px display `PALE_GOLD`; `boss.<def>.epithet` 22 px `MIST` (before P9's strings exist: `moment.boss.level` with the level read from the boss's state); a subtitle at y 610: `boss.<def>.intro` 20 px `PAPER` (none before P9) | P6: none. P9a: eases to the boss (−120 up) over 0.6 s, holds, eases back 1.5–1.9 s | — | `boss_sting`; caption `hud.caption.boss_sting` |
| 18 `boss_phase` | band at y 176, under the boss bar (y 118–132): the numeral `moment.numeral.<phase>` 40 px display `GOLD` and the phase's card (`boss.<def>.p<phase>`, P9) 34 px `PALE_GOLD`; wipe 0–0.2 s, fade 0.9–1.2 s | shake 0.3 s (from `world.gd:641`) | — | `boss_roar` (moved from `EVENT_SFX`); the HUD caption stays |
| 19 `boss_defeated` | flash `PALE_GOLD` α 0.35, 0–0.25 s; band at y 230: the boss's name 44 px display `PALE_GOLD`; `moment.boss.defeated` 22 px `GOLD`; when `clean`, `moment.boss.untouched` 18 px `BRIGHT_JADE`. P9a adds the `stamps` layer (seals, 0.3 s each) | shake 0.25 s | the fountain comes from row 21 | `boss_fall` |
| 20 `field_boss_defeated` | as 19; replaces the toast at `hud.gd:1228-1229` | as 19 | as 19 | `boss_fall` |
| 21 `loot_fountain` | — | — | `fountain` (§5.8); for a boss, `flash` `PALE_GOLD` r 90, 0.3 s at the drop | `coin` at launch; `rare_chime` when the first rare item lands |

**Rewards and story**

| Row | Screen (text source) | Camera | World FX | Sound, buzz |
|---|---|---|---|---|
| 22 `rare_drop` | strip at y 206: `moment.rare.title` 18 px `GOLD`, then each item's name 24 px in its grade or quality colour | — | `beam` on each rare `LootView`: 240 px high, 10 px wide, pulsing at 0.6 Hz until picked up | `rare_chime`; buzz 40 ms |
| 23 `story_beat` | letterbox 48 px, in 0–0.3 s; band at y 300: `moment.story.chapter` (the chapter) 22 px `GOLD`, letter-spaced; the quest's `name` 44 px display `PALE_GOLD`; `moment.story.done` 20 px `MIST` | — | — | `bell` |
| 24 `trial_opens` | band at y 170: `event.<event>` 34 px `PALE_GOLD` (today `RED` world text) | — | — | `bell` |

### 2.3 The major breakthrough, beat by beat

The approved mockup 05 at 1280 × 720. Beats 1–3 are the mockup's own timing strip; the hold and the fade after them
are this page's (question 1).

| Time s | Layer | What |
|---|---|---|
| 0.0–0.6 | **Beat 1: the light gathers.** `dim` | the world darkens to `INK` α 0.45, radial, lighter round the actor (the mockup's night wash), over 0.3 s |
| 0.0–0.6 | `converge` | 16 motes `PALE_GOLD` from r 300 along 8 curved paths into the actor at −60 |
| 0.0–3.0 | `pillar` | a column of light on the actor: 180 px wide at full width, an 8 px white core, 660 px high; widens 0–0.6 s, fades 2.6–3.0 s |
| 0.0–1.2 | `ring` ×3 | ellipses at the feet: 260 × 56, 164 × 36, 88 × 18, `PALE_GOLD` |
| 0.0 | sound, buzz | `breakthrough`; 120 ms |
| 0.6–1.4 | **Beat 2: the name is written.** `band` | the ink band (`INK` α 0.9) wipes left to right across x 300–1000, y 138–250, over 0.4 s |
| 0.6 | sound, shake | `brush_stroke`; shake 0.2 s |
| 0.7–0.9 | band line | `moment.breakthrough.over` ("BREAKTHROUGH") 26 px `PALE_GOLD`, letter-spaced 4 px, y 104 |
| 0.8–1.1 | band title | the great realm's name (`realm_great.<id>`) 92 px display `PALE_GOLD`, glow `GOLD`, y 138 |
| 1.1–1.3 | band sub | from ➤ to, and the stage band word, 20 px `PAPER`, y 262 |
| 1.3 | `seal`, sound | the stage numeral in a 44 px `RED` seal, −8°, at (992, 190); `seal_press` |
| 1.4–2.4 | **Beat 3: the stats rise.** `stats` | up to 7 rows at (880, 318), 36 px apart, each rising 12 px and fading in 0.12 s after the last: name 16 px `MIST`, value 20 px `PAPER`, "▲ delta" 16 px `BRIGHT_JADE` |
| 1.4 | `card` | the absorbed tribulation, if any: `moment.tribulation.weathered`, waves, bolts, struck, and the HP kept as a bar, in the `toast` frame 352 × 104 at (72, 330), sliding in from the left |
| 1.5 | lock | input returns |
| 2.0 | `chip`, sound | the Opens chip for each absorbed unlock (the kit's next-unlock chip) at (960, 588); `unlock` |
| 2.4–3.6 | hold | everything shown |
| 3.6–4.0 | fade | every screen layer fades out |

A tap, click or key during 0–1.5 s jumps to 2.4 s and returns input at once. After 1.5 s a tap goes to the HUD and the
card fades on its own.

The stat rows come from two snapshots of the active character, read by `MomentView` (never written): one taken at
`breakthrough_started` and refreshed every 1.0 s while no moment plays, and one taken when the row starts, after the
stat refresh that `realm_changed` triggers (`combat_authority.gd:12`). The list and its order are data
(`moments.json` `stats`): Level, Max HP, Max Qi, Max Soul, Physical attack, Qi attack, Soul attack, Crit chance,
Lifespan (the display span from ProgressionAuthority). Only stats that changed are shown, at most 7.

### 2.4 The boss intro and the phase card, and what P9 changes

| | P6c (this page) | P9a (`boss_design.md` §3.5, §3.9) |
|---|---|---|
| Trigger | `enemy_aggro` whose target is the active character and whose def's role is `field_boss`, `dungeon_boss` or `story_boss`; the first aggro of that boss since the room was entered | `boss_engaged` `first` true (row 17), `first` false (row 25, a 0.8 s name strip with `intro_again`) |
| Lock | 0: the boss does not wait, so the player keeps control | 1.5 s: EnemyAuthority holds the first attack 1.5 s (`ai.timer = max(ai.timer, 1.5)`) |
| Camera | none: a pan while the boss is free to attack would lose the player | the pan of §2.2 row 17 |
| Text | name and level line | name, epithet, one line of speech (`boss.<id>.epithet`, `.intro`, `.intro_again`) |
| Phase card | the numeral alone | the numeral and `phases[].card` from the widened payload (`def`, `card`) |
| Enrage | — | row 26 on `boss_enraged`: vignette `element:fire` α 0.25 on the edges, pulsing at 1 Hz (steady with Bright flashes off), `moment.boss.enrage` and `boss.<id>.enrage`, 1.0 s |
| The fall | row 19 and the fountain | the `stamps` layer presses the fight's seals, 0.3 s each; the Worthy Foes page opens after the row on a first kill |

Each change in the P9a column is a data change in `moments.py` plus the simulation work P9a already plans; no
`MomentView` code changes.

---

## 3. The data: `data/moments.json` from `tools/data/moments.py`

### 3.1 The file

`moments.py` is a new module in `tools/data/build_data.py` `MODULES`, placed before `contract`. It reads
`data/quests.json`, `data/enemies.json`, `data/items.json`, `data/sets.json` and `data/legendary_chains.json`, which
the modules before it write in the same build. `ContentDB` loads the file with no code change: `entries` becomes the
`moments` table (`ContentDB.all("moments")`) and the other keys become `ContentDB.config("moments")`
(`content_db.gd:35-54`).

| Key | Type | Holds |
|---|---|---|
| `entries` | array | the rows (§3.2) |
| `settings` | dict | `max_lock_s` 1.5, `queue_max` 4, `stale_s` 6.0, `cut_fade_s` 0.15, `flash_gap_s` 1.0, `shake_amp_per_s` 16, `fight_radius` 400, `snapshot_s` 1.0, `merge_rare_s` 1.5 |
| `stats` | array of stat ids | the stat rise list and order (§2.3) |
| `rare` | dict | `qualities` [`perfect`, `relic`]; `types` [`legend_piece`, `pet_book`, `treasure`, `treasure_art`]; `items`: every enemy's `unique_drop`, `first_defeat` and `elite_first_defeat` item, every set piece and every legendary-chain piece (P9 adds signature drops) |
| `chapter_ends` | dict quest → chapter | per chapter (`prologue`, `1`–`22`), the main quest whose `next` is empty or leads out of the chapter |
| `vfx_tiers` | array of 7 dicts | the escalation numbers (§5.2) |
| `vfx_shapes` | dict shape → fx | what each technique shape draws (§5.3) |
| `particles` | dict | spark style by weapon family and element (§5.6) |
| `numbers` | dict | multi-hit and shortening numbers (§5.5, §5.7) |
| `fountain` | dict source → numbers | the loot fountain (§5.8) |

### 3.2 A row

| Field | Type | Meaning |
|---|---|---|
| `id` | string | unique |
| `event` | string | the trigger, a catalogue name. Written as `"event": "<name>"`, so `contract_tests` already counts the row as the event's reactor (`contract_tests.gd:51-52`) |
| `when` | dict | matchers that must all hold (§3.4); `{}` for none |
| `priority` | int | 0–100; 0 marks a world row with no screen part |
| `duration_s` | float | the screen part |
| `lock_s` | float | ≤ `settings.max_lock_s`; 0 for none |
| `skip` | string | `tap` or `""` |
| `skip_to_s` | float | where a skip jumps |
| `stale_s` | float | the longest it may wait in the queue (default `settings.stale_s`) |
| `in_fight` | string | `play`, or `toast` (world layers and a toast only) |
| `scope` | string | `actor`, or `room` (ends on leaving the room) |
| `merge` | array | `{event, when, into, max, keep_sound}`: events folded into this row (§4.3) |
| `hold_until` | array of events | a held row lasts until one arrives |
| `max_s` | float | the guard for a held row |
| `toast` | text source | the line posted when the row is cut, stale or in a fight |
| `layers` | array | `{t, kind, …}` (§3.3) |
| `art` | array of asset ids | new assets the row needs; `[]` for none |
| `sample` | dict | a payload for tests and the `--moment` preview |
| `step` | string | the build step that ships it (`P6a`…) |

### 3.3 Layer kinds

Screen (drawn by `MomentView`):

| Kind | Canvas | Parameters | Draws |
|---|---|---|---|
| `dim` | under | `color`, `alpha`, `fade_in`, `until`, `radial` | a tint over the world |
| `vignette` | under | `color`, `alpha`, `edge` (px), `pulse_hz`, `until` | a tint on the screen's edges |
| `flash` | under | `color`, `alpha`, `dur` | a full-screen flash, subject to the flash limiter (§5.10) |
| `letterbox` | under | `height`, `slide_s` | two `INK` bars, top and bottom, under the HUD so its controls stay visible |
| `band` | over | `y`, `over`, `title`, `sub`, `size`, `wipe_s`, `color`, `glow` | the ink band with centred text (mockup 05) |
| `strip` | over | `y`, `title`, `sub`, `size`, `color` | a slim ink band, one or two lines |
| `card` | over | `rect`, `slot`, `lines`, `slide_from` | a panel in the kit's `toast` frame |
| `stats` | over | `at`, `row_h`, `gap_s` | the stat rise |
| `chip` | over | `at`, `slot` | the next-unlock chip |
| `seal` | over | `at`, `size`, `text`, `angle` | a vermilion seal stamped with a 0.12 s squash from 1.4× |
| `stamps` | over | `at`, `slot`, `gap_s` | P9's seals, one by one |
| `subtitle` | over | `y`, `text` | a speech line |
| `toast`, `caption` | HUD | `text`, `kind` / `key` | hands a line to `hud.toast` or the caption |

World (played at their `t` through `world.gd`, `FxLayer`, `LootView` and `Audio`):

| Kind | Parameters |
|---|---|
| `fx` | `fx` (an `FxLayer.KINDS` name), `at` (anchor), `offset`, `color`, `radius`, `dur`, `count`, `size`, `height`, `repeat_s` |
| `text` | `text`, `at`, `offset`, `size`, `color`, `dur` (an `FxLayer` `text`) |
| `shake` | `s`, `amp` (default `s × settings.shake_amp_per_s`, as today's 4 px at 0.25 s) |
| `camera` | `to` (anchor), `offset`, `in_s`, `hold_s`, `out_s` |
| `sound` | `sfx`, `bus`, `if_slot` |
| `buzz` | `ms` |
| `bark` | `key` (prefix; three lines), `radius`, `dur` |
| `fountain` | `source` numbers from `fountain` (§5.8) |
| `beam` | `height`, `width`, `pulse_hz` |

Anchors: `actor` (the active character's view), `enemy` (the payload's enemy uid), `pet` (the actor's active spirit
animal), `drop` (the payload's `x`, `y`), `item` (each rare `LootView`), `camera` (the screen centre). An anchor with
no view (a headless run, a boss already gone) skips its world layers and logs them.

New art: **the ink band**, `art/ui/hd/ink_band.png`, a dry-brush stroke in three slices (left cap, stretchable
middle, right cap), drawn procedurally by `tools/ui/build_ui_hd.py` and registered in `data/ui_assets_hd.json`. It
is a UI overlay, not a sprite and not a pose. The seal, letterbox, dim, vignette, chips and cards use shapes and the
existing kit.

### 3.4 Text sources, colours and matchers

**Text sources.** Every text field is one of these; no text is written in code (`contract_tests` `_strings_gate`):

| Source | Resolves to |
|---|---|
| `{"key": k, "args": [...]}` | `Tx.t(k)` formatted with the args (payload values, or other sources) |
| `{"realm": "payload.to"}` | `ContentDB.realm_label` |
| `{"realm_great": "payload.to"}` | `realm_great.<great realm>` (P6b adds these 19 keys; only single-stage realms have a name key today) |
| `{"transition": ["payload.from", "payload.to"]}` | from ➤ to, and the stage band word once P5b adds it |
| `{"stage": "payload.to"}` | the realm row's stage number (`realms.json` `sub`), for the seal |
| `{"name_of": table, "id": "payload.x"}` | `ContentDB.name_of(table, id)` |
| `{"item": "payload.item"}` | `ContentDB.item_name` |
| `{"craft": "payload.craft"}` | `craft.<id>` (P6b adds the keys for every craft id `add_xp` and `guilds.json` use) |
| `{"boss": field, "id": "payload.def"}` | `boss.<def>.<field>` if the key exists, else nothing (P9 writes the keys) |
| `{"payload": "name"}` | a payload value that is already player text (a quest's name) |

**Colours.** A `UiKit` constant name (`PALE_GOLD`), `element:<id>` (`data/elements.json`), `grade:<id>` and
`quality:<id>` (`data/grades.json`), or the same with a payload value (`quality:payload.quality`,
`grade:item.grade`). Never a hex literal (§6).

**Matchers** (`MomentRules.MATCHERS`, a closed list):

| Matcher | Holds when |
|---|---|
| `actor: "active"` / `target: "active"` | the payload's `actor` / `target` is the active character |
| any payload key with a value | equality (`major: true`, `kind: "cloud"`) |
| `role_in: [...]` | the payload's `def` (or `enemy`) is an enemy of one of these roles |
| `first_in_room: true` | the first match for this enemy uid since the last `room_entered` |
| `chapter_end: true` | the payload's `quest` is in `chapter_ends` |
| `rare: true` | an entry of `items` is rare: its `quality` in `rare.qualities`, its item's `type` in `rare.types`, or its id in `rare.items` (coins never) |
| `source_in: [...]` | the payload's `source` is one of these |
| `level_mod: n` | the payload's `level` is a multiple of n |

### 3.5 An example row

```json
{
 "id": "breakthrough_major",
 "event": "breakthrough_succeeded",
 "when": {"actor": "active", "major": true},
 "priority": 70, "duration_s": 4.0, "lock_s": 1.5, "skip": "tap", "skip_to_s": 2.4,
 "stale_s": 6.0, "in_fight": "play", "scope": "actor",
 "merge": [
  {"event": "level_changed", "into": "level", "keep_sound": false},
  {"event": "realm_changed", "into": "", "keep_sound": false},
  {"event": "system_unlocked", "into": "unlocks", "max": 2, "keep_sound": false},
  {"event": "tribulation_result", "when": {"survived": true}, "into": "tribulation"},
  {"event": "heavenly_phenomenon", "when": {"kind": "cloud"}, "into": "", "keep_sound": false}
 ],
 "toast": {"key": "moment.breakthrough.toast", "args": [{"realm": "payload.to"}]},
 "layers": [
  {"t": 0.0, "kind": "dim", "color": "INK", "alpha": 0.45, "fade_in": 0.3, "until": 3.6, "radial": true},
  {"t": 0.0, "kind": "fx", "fx": "converge", "at": "actor", "offset": [0, -60], "color": "PALE_GOLD", "count": 16, "radius": 300, "dur": 0.6},
  {"t": 0.0, "kind": "fx", "fx": "pillar", "at": "actor", "color": "PALE_GOLD", "radius": 90, "height": 660, "dur": 3.0},
  {"t": 0.0, "kind": "fx", "fx": "ring", "at": "actor", "color": "PALE_GOLD", "radius": 130, "count": 3, "dur": 1.2},
  {"t": 0.0, "kind": "sound", "sfx": "breakthrough"},
  {"t": 0.0, "kind": "buzz", "ms": 120},
  {"t": 0.6, "kind": "band", "y": 138, "wipe_s": 0.4, "size": 92, "color": "PALE_GOLD", "glow": "GOLD",
   "over": {"key": "moment.breakthrough.over"},
   "title": {"realm_great": "payload.to"},
   "sub": {"transition": ["payload.from", "payload.to"]}},
  {"t": 0.6, "kind": "sound", "sfx": "brush_stroke"},
  {"t": 0.6, "kind": "shake", "s": 0.2},
  {"t": 1.3, "kind": "seal", "at": [992, 190], "size": 44, "angle": -8, "color": "RED", "text": {"stage": "payload.to"}},
  {"t": 1.3, "kind": "sound", "sfx": "seal_press"},
  {"t": 1.4, "kind": "card", "slot": "tribulation", "rect": [72, 330, 352, 104], "slide_from": "left"},
  {"t": 1.4, "kind": "stats", "at": [880, 318], "row_h": 36, "gap_s": 0.12},
  {"t": 2.0, "kind": "chip", "slot": "unlocks", "at": [960, 588]},
  {"t": 2.0, "kind": "sound", "sfx": "unlock", "bus": "UI", "if_slot": "unlocks"}
 ],
 "art": ["ink_band"],
 "sample": {"actor": "c1", "from": "will_manifest_3", "to": "sphere_lord_1", "major": true, "formation": ""},
 "step": "P6b"
}
```

### 3.6 The technique `vfx` block

`tools/data/techniques.py` adds, at the end of `build()`, a `vfx` block to every row of `techniques.json`. The
roadmap's `vfx_tier` is `vfx.tier`.

| Field | Values | Set by |
|---|---|---|
| `tier` | 1–7 | the realm band of the technique's `unlock` (§5.1) |
| `shape` | `strike`, `wave`, `ring`, `rain`, `pillar`, `domain`, `bolt` | a rule on the row (§5.3), with `SHAPE_OVERRIDES` for the exceptions |
| `particles` | `square`, `ink`, `ring`, `ember`, `shard` | the family, else the element (§5.6) |

Example: `{"id": "cursive_storm", …, "vfx": {"tier": 5, "shape": "rain", "particles": "ink"}}`.

### 3.7 Contract changes

In `tools/data/contract.py`:

- **Catalogue:** `level_changed` into `Progression`, `room_event_started` into `World` (finding 5). P9a adds
  `boss_engaged` and `boss_enraged`; P8b adds `band_worn`.
- **Declared payloads:** a new `PAYLOAD` dict names the keys of every event a moment reads (the "Trigger" column of
  §2.1, plus the merged events: `realm_changed`, `system_unlocked`, `tribulation_result`, `achievement_unlocked`),
  written into `event_contract.json` as each event's `payload`.
- **`loot_dropped` gains `source`** (finding 6): `WorldAuthority._drop_loot` takes the caller's kind and puts it in
  the payload. It is the one simulation-file edit in P6: a payload key, no state and no rule. The six callers and
  their kinds: a defeated foe, `enemy`, `elite`, `boss` or `field_boss` by its role (`world_authority.gd:824`); a boss
  that flees, `fled` (`enemy_authority.gd:391`); a broken jar, `jar` (`world_authority.gd:516`); a chest, `chest`
  (572); a survived rift, `rift` (1358); a Trial Tower floor, `tower` (1654).

### 3.8 How the data is checked

`tests/data_validation.gd`, a new `moments_data_suite`:

1. Every row's `event` and every `merge` event is in `data/event_contract.json`.
2. Every `payload.<key>` a row reads (in `when`, text sources, colours, anchors) is in that event's declared
   `payload`.
3. Every `fx` layer names a kind in `FxLayer.KINDS`; every technique's `vfx.shape` maps through `vfx_shapes` to kinds
   in `FxLayer.KINDS`.
4. Every `sound` is an `sfx` id in `data/audio.json`.
5. Every `key` text source exists in `ContentDB.strings` itself, not through `ContentDB.text`'s fallback. For
   `name_of`, the table exists. For `boss` sources, every boss has the P9 keys once P9a lands.
6. Every colour is a `UiKit` constant (`load("res://scripts/ui/ui_kit.gd").get_script_constant_map()`), an
   `element:`, `grade:` or `quality:` id that exists, or one of those with a payload value.
7. Every matcher is in `MomentRules.MATCHERS`, every layer kind in `MomentRules.LAYER_KINDS`, every anchor in
   `MomentRules.ANCHORS`.
8. Timing: `lock_s` ≤ `settings.max_lock_s`; `lock_s`, `skip_to_s` and every screen layer's `t` < `duration_s`; a
   held row has `hold_until` and `max_s`.
9. `rare.items` all exist; `chapter_ends` has one main quest per chapter, 23 in all.
10. Every technique has a `vfx` block with a tier equal to its unlock realm's band (§5.1) and a known shape and style.
11. The `vfx_tiers` table has 7 rows; every numeric column is non-decreasing in tier and `spark_count` rises strictly;
    `number_size` + 8 ≤ 40; `shake_s` ≤ 0.15; `tint_alpha` ≤ 0.2.
12. Every `sample` has every declared payload key of its event.

`tests/contract_tests.gd` gains:

1. The catalogue additions are emitted only by their systems (the existing check).
2. For each event with a declared `payload`, every emit site names every declared key in its dict literal (the
   emit line and its continuation lines to the closing brace).
3. `FxLayer.KINDS` and the `match str(e.kind)` arms of `fx_layer.gd` `_draw` list the same kinds.
4. **Presentation only:** `moment_view.gd` and `moment_rules.gd` contain none of `Game.submit(`, `emit(`,
   `emit_event(`, `GameEvents.subscribe(`, `.apply_`, `Rng.`, `Clock.`, and assign to no `Game.` member.
5. `STRING_SCOPE` gains `moment_view.gd`, `moment_rules.gd` and `fx_layer.gd`.

---

## 4. `MomentView`

### 4.1 Where it lives

| File | Holds |
|---|---|
| `scripts/presentation/moment_rules.gd` | `class_name MomentRules`, static and pure: the matchers, the rare rule, text and colour resolution, the tier numbers, the constant lists (`MATCHERS`, `LAYER_KINDS`, `ANCHORS`, `SHAPES`, `STYLES`) |
| `scripts/presentation/moment_view.gd` | `class_name MomentView extends Node`: the gather, the queue, the timelines, the input lock, and two child canvases: `under` (a `CanvasLayer` at layer 4, between the world and the HUD at 5) and `over` (layer 8, above the HUD, below the shell at 15 and pages at 20) |

`main.gd` `_mount_world` creates it after the HUD, sets `moments.world = world` and `moments.hud = hud`, and adds it;
`_unmount_world` frees it (`main.gd:611-638`). So moments exist only while the world is mounted: events raised while
the save loads, or during offline settlement, never play.

### 4.2 Events in

1. `MomentView` connects to `GameEvents.event`, the presentation signal that fires after every authority reacted
   (`game_events.gd:8-11`), as `world.gd` and `hud.gd` do. It never uses `GameEvents.subscribe`.
2. At `_ready` it indexes rows by `event`. An event with no rows costs one dictionary lookup.
3. **Gather.** A matching event is appended to `pending` with its payload. Nothing plays inside the signal. At the
   start of its next `_process`, `MomentView` resolves everything gathered. All events of one `Game._after_pass`
   (`game_authority.gd:285-294`), including the unlocks evaluated after it, arrive in one frame, so a breakthrough,
   its level, its unlocks and its phenomenon are resolved together.
4. **Match.** Each gathered event is tested against its rows' `when`. Several rows may match one event (a boss drop
   can start `loot_fountain` and `rare_drop`).
5. **Merge.** For each matched row, gathered events named in its `merge` fill its slots (`level`, `unlocks`,
   `tribulation`, `title`); their own rows then do not play, and their sounds play only with `keep_sound`. A merge
   event with no host row plays its own row.

### 4.3 Playing a row

- **World layers** start when the row is accepted, whatever the screen is doing: FX through `world.fx`, text through
  `FxLayer` `text`, shakes through the camera rig (§4.9), sounds through `Audio.play`, barks on the NPC views, the
  fountain and beam on `LootView`s. They follow their `t` offsets on a small scheduler.
- **Screen layers** wait for the screen slot (§4.4). The playing row's screen state is drawn from its elapsed time,
  so a skip or a cut is only a change of time.
- A **held** row (the tribulation) keeps its screen part to the end of its last layer and its world layers until a
  `hold_until` event or `max_s`.
- Rows time themselves on frame delta, not the simulation clock. While `Game.paused` is set they stand still.
- `advance(delta)` does the work of one frame; `_process` calls it. Tests call it directly (§7).

### 4.4 Queue and priority

1. **One screen row at a time.** A row takes the screen when the slot is free, no page is open (`main.gd` `pages`),
   and it is first by priority, then by arrival.
2. **Cuts.** A row of priority 90 or more cuts a playing row of lower priority: the playing row fades out over
   `cut_fade_s` (0.15 s) and posts its `toast`; it does not come back. Equal priorities never cut; they queue.
3. **Queue size.** At most `queue_max` (4) wait; a fifth drops the lowest-priority waiting row to its toast.
4. **Stale.** A row that waited longer than its `stale_s` drops to its toast. Boss rows have short limits (phase 1.0 s,
   intro 1.5 s) and drop silently: a late phase card would be wrong, and the boss bar already says it.
5. **Pages.** A row does not start its screen part while a page is open; its world layers already played. When the
   last page closes, the waiting rows start in order. A row already playing when a page opens keeps its clock under
   the page (pages draw at layer 20).
6. **In a fight.** The active character is in a fight when a living foe within `fight_radius` (400) is in aggro,
   wind-up, attack or recovery (the HUD's `_enemy_close`, `hud.gd:446-451`), when a boss is alive in the room, or
   while a tribulation runs. Rows with `in_fight: "toast"` then play their world layers and post their toast.
7. **Room change.** `room_left` ends every `scope: "room"` row, playing or waiting, with no toast.
   `character_switched` clears everything.
8. **Sound and shake.** Shakes combine by the larger, as today. The same sound id within 0.1 s plays once.
9. **Repeats.** The same row with an equal payload within 0.5 s plays once.

### 4.5 Input lock and skip

- The HUD gets a `moment_lock` flag, separate from `blocked` (`hud.gd:563-568`), so closing a page never ends a moment's
  lock and a moment never ends a page's block. `_input` returns early while either is set, except that a lock with a
  `skip` lets the first press through to `MomentView`.
- A lock starts when the row's screen part starts and lasts `lock_s`, never more than `settings.max_lock_s` (1.5 s,
  F4). Held controls are released when it starts, as `set_blocked` does.
- **Skip.** During the lock, the first touch, click or key is consumed: the row jumps to `skip_to_s` and the lock ends.
- **Never in a fight.** A lock does not start in a fight, and one that is running ends the moment a foe aggroes.
- Rows with a lock: `breakthrough_major` (1.5 s, skips) now; `boss_intro` (1.5 s, no skip) from P9a, when the boss
  itself waits.

### 4.6 Settings

| Setting | Default | What moments and feedback do |
|---|---|---|
| Screen shake (`screen_shake`, exists) | on | off: every camera offset is 0, from moments and from feedback (`world.gd:306` today) |
| Bright flashes (`flashes`, exists) | on | off: `flash` layers, `FxLayer` `flash` and screen tints at 0.3 of their alpha (`fx_layer.gd:99` uses 0.5 → 0.15); vignette pulses steady |
| Damage numbers (`damage_numbers`, exists, unread) | on | off: no floating damage numbers; Miss, Immune, Evade and Parry stay (finding 2) |
| Vibration (`haptics`, exists) | on | off: no `buzz` |
| Captions (`captions`, exists) | off | on: a row's `caption` shows through the HUD caption |
| **Reduce motion** (`reduce_motion`, new, Accessibility tab) | off | on: no camera pans and no shake; letterbox, bands and strips fade in over 0.2 s instead of sliding and wiping; stat rows fade without rising; `converge`, `spark`, `rain` counts at tier 1; the loot fountain becomes today's bounce; no screen tints |
| Battery saver (`battery_saver`, exists, unread) | off | on: particle counts capped at tier 2; no screen tints |
| Text size (`text_size`, exists) | 1 | moment text scales as all text does (`UiKit.draw_text`) |

Durations and locks are the same under every setting, so the words stay readable. `reduce_motion` goes into
`AccountState.default_settings` (`account_state.gd:46-51`) and the Accessibility list (`settings_page.gd:8`) with
`ui.settings.reduce_motion`.

### 4.7 Staying out of the simulation

- It listens, draws and plays sound. It never calls `Game.submit`, an authority's `apply_*`, `emit` or
  `GameEvents.emit_event`, and it writes no state object (checked by `contract_tests`, §3.8).
- It reads only: the active character's stats, pools and pets, `Game.room_rt` living enemies, the account settings,
  `ContentDB`, `Game.progression.tribulation_view` and the lifespan display. The HUD reads the same things.
- It uses no `Rng` stream and no `Clock`; shake jitter uses `randf` as `world.gd:307` does. Timing is frame delta.
- The simulation never waits on it. P9a's first-attack hold is EnemyAuthority's own timer, set whether or not a
  moment plays.
- **Headless.** `world` and `hud` may be null. World layers are then written to `log` (`{t, row, layer, params}`)
  instead of drawn, toasts to `toasts_posted`, and the lock to `lock_left()`. Test hooks `fight_override` and
  `pages_override` stand in for the room and the pages. The suites that do not mount it (every other `rules_tests`
  suite, `valley_run`, `prologue_run`, `balance_sim`) run unchanged; `replay_suite` still proves the same seed gives
  the same run.

### 4.8 What moves out of `world.gd`, `hud.gd` and `AudioDirector`

| From | Into row | Step |
|---|---|---|
| `world.gd:458-462` `breakthrough_succeeded` | 2, 3 | P6a (as is), P6b |
| `world.gd:588-602` `heavenly_phenomenon`, with its barks | 5, 6 | P6a |
| `world.gd:603-604` `breakthrough_started` | 1 | P6a |
| `world.gd:605-607` `breakthrough_failed` | 4 | P6a, P6b |
| `world.gd:613-614` `body_level_changed` | 8 | P6a |
| `world.gd:615-616` `level_changed` | 7 | P6a |
| `world.gd:574-587` `pill_cloud`, with its barks | 16 | P6a |
| `world.gd:499-502` `weapon_awakened` | 15 | P6a |
| `world.gd:638-639` `room_event_started` | 24 | P6a |
| `world.gd:640-641` `boss_phase` | 18 | P6a |
| `hud.gd:805-806` the breakthrough buzz | 2, 3 | P6a |
| `hud.gd:1073` the tribulation's second `thunder` | 6 | P6a |
| `hud.gd:1071-1072` the tribulation toast | 6 (its band) | P6b |
| `hud.gd:785-786` title, `1043-1044` guild rank, `1065-1066` body tier, `1228-1229` field boss defeated, `1263-1264` weapon awakened, `1265-1266` pet evolved | the rows' `toast` fallback | P6b, P6c |
| `audio_director.gd:8, 10` `EVENT_SFX` `level_changed`, `boss_phase` | 7, 18 | P6a |

Everything in §1.2 stays in `world.gd`. `loot_dropped` (`world.gd:369-373`) keeps building `LootView`s, because they
are room nodes; rows 21 and 22 act on those views in the same frame, before their first draw. `enemy_aggro`'s "!"
stays; row 17 reads the same event. The HUD keeps its toast function, room banner, fortune card, captions, log, boss
bar and tribulation panel.

### 4.9 Changes to other presentation files

| File | Change | Step |
|---|---|---|
| `world.gd` | A camera rig: `add_shake(s, amp)` (the one writer of `shake` and `shake_amp`; `hazard_view.gd:86, 115` call it), and `camera_hold {target, weight}` blended into the follow in `_process`. Reads `screen_shake` and `reduce_motion`. Reads `damage_numbers` for `fx.number`. | P6a |
| `fx_layer.gd` | `const KINDS`; `numbers_enabled` follows the setting (P6a); new kinds `pillar`, `converge` (P6b), `rain` (P6e); `count`, `size`, `style` on `spark`, `count` on `ring`, `repeat_s` handled by the scheduler; a `stack` key on `number` for multi-hit stacks; tier numbers from `MomentRules.tier_numbers` (§5) | P6a–P6e |
| `loot_view.gd` | `launch(from, delay, apex, flight)` for the fountain; `beam` for rare items, as tall and pulsing as §2.2 row 22 | P6c, P6d |
| `hud.gd` | `moment_lock`; the toasts above become fallbacks | P6a, P6b |
| `main.gd` | mount and free `MomentView`; the `--moment=<id>[:t]` preview flag (plays a row with its `sample` and holds at `t`, for screenshots, as `--hazard` does) | P6a |
| `settings_page.gd`, `account_state.gd` | `reduce_motion` | P6b |
| `tools/audio/sfx.py` | six new sounds (§5.9) | P6b, P6c, P6d |
| `tools/ui/build_ui_hd.py`, `data/ui_assets_hd.json` | the ink band | P6b |
| `tools/data/ui_strings.json` | `moment.*`, `realm_great.*`, `craft.*`, `failure.<id>` (finding 8), `ui.num.*`, `hud.caption.boss_sting`, `ui.settings.reduce_motion` | P6a–P6e |

---

## 5. The escalation curve (M22–M25)

### 5.1 `vfx.tier` by realm band

The tier is the band of the realm that teaches the technique. It matches the technique grades already in the data
(`techniques.py:199-201`: Common, Earth, Heaven) and splits Heaven by zone.

| Tier | Realms that teach it (realm index) | Levels | Zone | Grade | Techniques today |
|---|---|---|---|---|---|
| 1 | Mortal, Bone Forging, Qi Kindling (0–2) | 0–18 | Jade River Valley | Common | 16 |
| 2 | Qi Unfurling, Heart Tempering (3–4) | 19–36 | Jade River Valley | Earth | 22 |
| 3 | Cloud Stride, Spirit Awakening, Heaven Glimpse (5–7) | 37–63 | Jade River Valley | Heaven | 9 |
| 4 | Sage, Sage Sovereign (8–9) | 64–81 | Azure Expanse | Heaven | 1 |
| 5 | Will Manifest, Sphere Lord (10–11) | 82–99 | Lantern Star Field | Heaven | 8 |
| 6 | Law Touching, Monarch, Half-Heaven Monarch (12–14) | 100–118 | v1.3–v1.4 | — | 0 |
| 7 | Dao Sigil, Heaven's Threshold, Inner Heaven, World Genesis (15–18) | 119+ | v1.4–v1.5 | — | 0 |

56 techniques in all. Companions' and spirit animals' hits draw one tier below their technique's (at least 1), so the
player's own blows stay the brightest.

### 5.2 What scales with the tier

| Tier | Spark count | Spark size px | Spark reach px | Core r | Cast ring r | Area wave width px | Echo waves | Number px (crit) | Shake per cast s (amp px) | Screen tint α, 0.4 s |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8 | 6 | 28 | 10 | — | 8 | 0 | 22 (30) | — | — |
| 2 | 10 | 6 | 32 | 12 | 40 | 9 | 0 | 22 (30) | — | — |
| 3 | 12 | 8 | 38 | 16 | 60 | 10 | 1 | 24 (32) | 0.06 (1) | 0.06 |
| 4 | 14 | 8 | 44 | 20 | 80 | 12 | 1 | 24 (32) | 0.08 (1.5) | 0.08 |
| 5 | 16 | 10 | 50 | 24 | 100 | 14 | 2 | 26 (34) | 0.10 (2) | 0.10 |
| 6 | 18 | 10 | 56 | 28 | 120 | 16 | 2 | 28 (36) | 0.12 (2) | 0.14 |
| 7 | 20 | 12 | 64 | 32 | 140 | 18 | 3 | 30 (38) | 0.14 (2.5) | 0.18 |

Tier 1 is today's look (`fx_layer.gd:57-63`, `world.gd:411`), so the valley's first techniques do not change.

- **Spark:** count, start size and reach of the hit spark on each hit; core is the white centre's radius.
- **Cast ring:** a `ring` at the caster's feet when the technique fires, 0.3 s, in the element colour.
- **Area wave:** the ring or line that shows an area, drawn at the hitbox's true reach. The tier makes it thicker and
  adds echo waves inside it (at 0.7 and 0.4 of the reach, 0.08 s apart), never beyond it (§5.4).
- **Numbers:** the size of damage numbers from a technique of that tier; basic attacks stay 22. A crit adds 8, as
  today.
- **Shake:** once per cast, on the first hit that lands; the player's blows never shake at tiers 1–2, as today.
- **Screen tint:** F1's "Heaven grade fills the screen for 0.4 s". A full-screen tint in the element colour at cast,
  from tier 3 (the first Heaven tier), under the flash limiter (§5.10) and Bright flashes.
- **Hit-stop** stays CombatAuthority's (0.05 s, 0.1 s on a crit); scaling it would change the simulation (question 5).

### 5.3 Shapes

| Shape | Rule in `techniques.py` | Draws on cast | Today |
|---|---|---|---|
| `strike` | none of the below; also stances, the sword arts and movement | `slash`, radius 46 + 6 × (tier − 1) | 14 |
| `wave` | reach 200 or more, or `line` | `talisman_wave` along the hitbox reach, 20 + 2 × tier px tall | 7 |
| `ring` | `both_sides` | `wave` at the hitbox reach, with the tier's width and echoes | 9 |
| `rain` | 4 or more hits on 4 or more targets | `rain` (new): streaks over the hitbox, 3 × hits + 2 × tier of them, 0.5 s | 2 |
| `pillar` | Soul damage on one target | `pillar` (new) on the target, 24 + 8 × tier wide, 300 high, 0.35 s | 4 |
| `domain` | buffs, heals, illusions | `ring` at the heal or buff radius, and `motes` | 9 |
| `bolt` | a projectile | nothing more on cast; the projectile's own art (`fx_layer.gd:320`) and the spark on impact | 11 |

`SHAPE_OVERRIDES`: `glimpse_of_heaven` → `pillar` (heaven's light from above), `shadowstep_cut` → `strike` (a blink
and a cut, though its reach is 240). With them: strike 15, wave 5, pillar 5, the rest as listed.

### 5.4 Drawn = hit

A shape that shows an area is drawn at the area the technique really strikes. The tier changes thickness, echoes and
brightness inside that edge, never the edge. Players read the edge as the reach; `docs/boss_design.md` §1.4 finding 5
shows what a drawn edge that lies costs.

### 5.5 Multi-hit numbers

Eight techniques hit more than once (`flowing_palm` 2, `twin_reed_shot` 2, `returning_crane_fan` 2, `reed_song` 3,
`flying_blades` 3, `venom_needles` 3, `cursive_storm` 4, `rain_of_reeds` 5). Each hit is its own `hit_landed`
(`combat_authority.gd:973-977`); today their numbers spawn on top of each other.

| Rule | Value |
|---|---|
| A stack | numbers on one target from one `source` (`tech:<id>`) within 0.3 s |
| The i-th number (from 0) | starts 0.06 s × i later, 18 px × i higher, x alternating ±12 px; speed as today |
| Total | after a stack of 3 or more, 0.1 s after its last number: the sum in `PALE_GOLD`, the stack's size + 2 px, 24 px above the top number |
| Cap | 6 numbers per stack; the rest only add to the total |
| Crits | `GOLD` and +8 px, as today |

### 5.6 Particles by element and family

The hit spark's `style` (F2), coloured by `data/elements.json` as today:

| Style | Draws | Used by |
|---|---|---|
| `square` | today's squares | the default: none, water, wood, earth, wind, star, space |
| `ember` | squares that rise and flicker | fire |
| `shard` | 2 px lines that fall | metal, ice, thunder |
| `ink` | round drops that fall under 400 px/s² | the brush family |
| `ring` | three thin rings spreading | the bell and flute families, Soul |

### 5.7 Large numbers

Numbers of 10,000 and more are shortened to three figures: 12,400 → "12.4K", 1,250,000 → "1.25M", as mockup 01 draws
"18.2K". A new `UiKit.fmt_short`; the unit letters are strings (`ui.num.thousand`, `ui.num.million`), since a unit is
a word the player reads (the B8 rule in `contract_tests` `_format_words_gate`). Every number size in §5.2 is at least
`UiKit.PIXEL_NUMERALS_MIN` (20), so all are drawn in Pixelify Sans.

### 5.8 The loot fountain

Each item's `LootView` starts at the drop point and flies on a parabola to its real place in the room (the
simulation's `x` and `y`, 22 px apart, `world_authority.gd:853-857`), then does today's 36 px bounce.

| Source | Apex px | Flight s | Launch gap s | Also |
|---|---|---|---|---|
| boss, field boss | 120 + 14 per item, at most 200 | 0.55 + 0.04 per item, at most 0.9 | 0.05 | `flash` `PALE_GOLD` r 90, 0.3 s at the drop; coins burst as 6 coins that settle into one pile |
| chest, tower, rift | 80 + 10 per item, at most 140 | 0.45 + 0.03 per item, at most 0.7 | 0.04 | — |
| other (a foe, a jar) | no fountain: today's bounce | | | |

Rare items launch last, so they land on top; `rare_chime` plays when the first one lands. An item picked up in flight
simply goes, as it would today. Reduce motion turns the fountain off.

### 5.9 The breakthrough fanfare and the new sounds

The major breakthrough's sound, on the SFX bus except `unlock` (UI):

| Time s | Sound | Exists |
|---|---|---|
| 0.0 | `breakthrough`: a gong, a drum and ten rising chimes, 2.6 s | yes (`sfx.py:399`) |
| 0.6 | `brush_stroke` | new |
| 1.3 | `seal_press` | new |
| 2.0 | `unlock`, only with an Opens chip | yes |

The minor breakthrough plays `level`; a level gained alone plays `gong_short` (F4's "short gong").

Six new sounds in `tools/audio/sfx.py`, from `synth.py`'s parts:

| Id | Length s | Recipe | Rows |
|---|---|---|---|
| `brush_stroke` | 0.5 | a noise whoosh through a band moving 800 → 2,400 Hz, with a scatter of grains at its end | 3 |
| `seal_press` | 0.35 | a woodblock and a membrane at 120 Hz | 3, 11 |
| `gong_short` | 0.8 | a gong at 196 Hz, decay 0.35, brightness 0.6 | 7 |
| `boss_sting` | 1.4 | two membrane hits at 55 Hz (0 and 0.25 s) and a low gong at 73 Hz falling | 17 |
| `boss_fall` | 2.0 | a gong at 65 Hz, decay 1.0, a membrane at 48 Hz and three falling chimes | 19, 20 |
| `rare_chime` | 0.9 | three bells at 1,568, 2,093 and 2,637 Hz, 0.09 s apart | 16, 21, 22 |

### 5.10 The flash limiter

Screen flashes and screen tints from every source share one limiter: at most one a second (`flash_gap_s`). A second
one inside the gap is skipped. This keeps the game well under three flashes a second, the usual limit for
photosensitive players, even in a crowd of tier-5 techniques.

---

## 6. Colour

The style guide (`docs/ui_style_guide.md`, P4) is being written in parallel and is not in this checkout. Until it
lands, moments use the `UiKit` constants (`ui_kit.gd:11-25`) and the colours in data, with the roles the P3 kit
already names (`docs/mockups/kit/kit.css:53-60`). When P4's tokens land, they replace these names in `moments.py`;
`data_validation` accepts only names that exist in `UiKit`, so a stale name fails the build.

Rules:

1. No hex literal in `moments.json`, `moment_view.gd` or `moment_rules.gd`. Colours are `UiKit` names, element, grade
   or quality ids (§3.4).
2. Heading `PALE_GOLD`, text `PAPER`, dim text `MIST`, accent `GOLD`, positive `BRIGHT_JADE`, negative `RED`, as the
   kit's roles.
3. Ink is `INK`: the band, the letterbox, the dim.
4. A thing with a grade or quality is drawn in that colour, from `grades.json`: rare drops, awakened weapons, pill
   clouds (finding 7), Soul Bands by rank.
5. An element's effect is its `data/elements.json` colour.
6. Colour never carries meaning alone: every row has words, and danger rows use `RED` words as well as tints.

Three literals move out of `world.gd` with their rows. P6a names them in `UiKit` beside the others, for P4 to rename
or merge: `HEAVEN_CLOUD` (`#f5c86a`, `world.gd:593`), `HEAVEN_BOLT` (`#9fc4ff`, `world.gd:593`) and `BODY` (`#f0a060`,
`world.gd:614`). `weapon_awakened`'s `#ffd27a` becomes `PALE_GOLD` and the pill cloud takes its quality colour.

| Row | Title | Sub | Accent and seal | Screen tint | World FX |
|---|---|---|---|---|---|
| breakthrough minor, major | `PALE_GOLD` (glow `GOLD`) | `PAPER`, deltas `BRIGHT_JADE`, names `MIST` | seal `RED` | dim `INK` | `PALE_GOLD` |
| breakthrough failed | `RED` | `PAPER`, `MIST` | — | dim `INK` | `MIST` |
| phenomenon, tribulation | `PALE_GOLD` | `PAPER` | — | vignette `INK` | `HEAVEN_CLOUD`, `HEAVEN_BOLT` |
| level, body level, body tier | `PALE_GOLD` | `MIST` | — | — | `PALE_GOLD`, `BODY`, `BRONZE` |
| Dao tier | `PALE_GOLD` | `MIST` | — | — | the element's colour; weapon Daos `PALE_GOLD`; craft Daos `BRIGHT_JADE`; rare Daos `SOUL` |
| title, craft, guild, pet | `PALE_GOLD` | `MIST` | seal `RED` (title) | — | `BRIGHT_JADE`, `PALE_GOLD` |
| weapon awakened | the item's grade colour | `PAPER` | — | — | `PALE_GOLD`, `GOLD` |
| rare pill | — | — | — | — | `quality:<quality>` |
| boss intro | `PALE_GOLD` | `MIST`, speech `PAPER` | — | letterbox `INK` | — |
| boss phase | `PALE_GOLD` | — | numeral `GOLD` | — | — |
| boss enrage (P9) | `RED` | `PAPER` | — | vignette `element:fire` | — |
| boss defeated | `PALE_GOLD` | `GOLD`; Untouched `BRIGHT_JADE` | — | flash `PALE_GOLD` | — |
| loot fountain, rare drop | the item's grade or quality colour | `GOLD` label | — | — | beam in the item's colour; flash `PALE_GOLD` |
| story beat, trial opens | `PALE_GOLD` | `MIST`, chapter `GOLD` | — | letterbox `INK` | — |
| Soul Band (P8b) | the rank's colour | `MIST` | rim `PALE_GOLD` when crowned | — | the rank's colour |

---

## 7. Tests

### 7.1 `rules_tests` `moments_suite`

A `MomentView` is added as a child of the test node with no world and no HUD, and stepped with `advance(1 / 60)`.
The cases name the rows of the finished P6. Cases 3–10 can also run on fixture rows a test loads with
`MomentView.load_rows(array)`, so the gather, queue, cut, lock and settings are proved in P6a, before any real row has
a screen part; each later step runs them again on its real rows (§8).

1. **Every row fires from its event.** For each row: feed its `sample` through the signal handler, `advance(0)`, and
   check the row is playing, queued or (a world row) logged. Step to `duration_s` + 0.1 s: it has ended; each layer
   was logged within one frame of its `t`; the screen slot is free.
2. **Real events.** Three rows through the real path: a minor breakthrough by `start_breakthrough` at a bottleneck
   (row 2, with `level_changed` merged); a level gained by meditation progress (row 7); a boss phase by chipping
   Big Toad Tan to 49% and `Game.enemies._check_phases` (row 18), the shortcut `boss_suite` uses.
3. **Gather and merge.** In one frame: `breakthrough_succeeded` (major), `level_changed`, `realm_changed`, two
   `system_unlocked`, `heavenly_phenomenon` (cloud), `title_changed`. After `advance(0)`: row 3 plays with `level`
   and two `unlocks` filled; `breakthrough` is logged once; row 5's world layers are logged; row 11 waits.
4. **Queue order.** Add `rare_drop` and `dao_tier` to case 3: after row 3 ends, `dao_tier` (50), then
   `title_earned` and `rare_drop` (40) by arrival.
5. **Cut.** Feed `boss_phase` 1.0 s into row 3: row 3 fades within 0.15 s, its toast is posted, row 18 plays, and
   row 3 does not return.
6. **Stale and full.** Queue five rows behind a playing one: the lowest drops to its toast at once. Hold the slot 7 s:
   every waiting row past its `stale_s` drops to its toast; a waiting `boss_phase` drops after 1.0 s with no toast.
7. **Pages and fights.** With `pages_override` set, a row's world layers log but its screen part waits, then starts
   when it is cleared. With `fight_override` set, `title_earned` posts a toast and draws nothing on screen, and
   `breakthrough_major` starts no lock.
8. **Room change.** `room_left` ends a playing `boss_intro` and a waiting `trial_opens` with no toast; a waiting
   `title_earned` survives.
9. **Settings.** With `screen_shake` off, every logged shake has amplitude 0; with `flashes` off, flash and tint alphas
   are 0.3 of their row's; with `reduce_motion` on, no `camera` layer runs, letterbox and band layers log `motion:
   false`, spark and converge counts equal tier 1's, and the fountain logs `bounce`; with `damage_numbers` off,
   `FxLayer.number` adds nothing to a headless `FxLayer`'s `fx`; with `haptics` off, no `buzz`.
10. **The lock.** For every row: `lock_left()` never exceeds the row's `lock_s` nor 1.5 s, and is 0 one frame after
    `lock_s`. During row 3's lock, one press jumps it to 2.4 s and the lock is 0 at once. A lock never starts with
    `fight_override` set, and one running ends the frame `fight_override` is set.
11. **Held rows.** Row 6 holds until `tribulation_result`, lays `heaven_storm` again every 5 s, and ends at `max_s`
    if no result comes.
12. **Escalation.** The `vfx_tiers` columns are non-decreasing in tier and `spark_count` rises strictly. For one
    technique per tier, `MomentRules.tier_numbers("tech:<id>")` gives that tier's row, and a headless `FxLayer`'s
    `spark` entry added with them carries that count and size. A companion's hit gives one tier lower.
13. **Multi-hit.** Three `FxLayer.number` calls with one `stack` key (target and `tech:flying_blades`) within 0.2 s
    give three entries 18 px apart, 0.06 s apart, on alternating sides, then a total. Seven calls: six numbers and a
    total of seven. A headless `FxLayer` is inspected through its `fx` array; nothing is drawn.
14. **Rare rule.** `MomentRules.is_rare` is true for a perfect piece, a legend piece and a set piece, false for coins
    and a common herb.

### 7.2 `data_validation` and `contract_tests`

As §3.8. In short: every trigger is a catalogue event with declared payload keys; every FX kind exists in
`fx_layer.gd`; every sound, string, colour and asset exists; every lock is within 1.5 s; the presentation files make
no call into the simulation.

### 7.3 `perf_tests`

The `_crowd` case (`perf_tests.gd:83-102`) with `MomentView` mounted, row 3 playing, a sword swarm and fifteen
monsters: each frame, the simulation tick plus `MomentView.advance` and `FxLayer._process`, stays under 16.6 ms. The
FX cap of 160 holds.

### 7.4 Screenshots

Through `--moment=<id>:<t>`: row 3 at 0.3, 1.0, 1.4 and 2.4 s against mockup 05; rows 2, 4, 10, 11, 17, 18, 19 and 22
at their full frame; the fountain of Big Toad Tan's first kill mid-flight; one technique per tier at its spark's
largest (F1's test) and `cursive_storm` on one foe (F2's test). Each at Bright flashes on and off.

---

## 8. Build order

Each step ships with its tests, its `docs/CHANGELOG.md` entry, a commit and a push.

| Step | Contents | Acceptance |
|---|---|---|
| **P6a · The table and the view** | `moments.py`, `moments.json` with rows 1, 2 (today's look, for every breakthrough until row 3 exists, and silencing the cloud's second `breakthrough`), 4 (today's look), 5, 6 (today's storm), 7, 8, 15, 16, 18 (today's shake), 24 (today's text). `MomentRules`, `MomentView` with gather, merge, queue, lock (0 everywhere), settings and the headless log. The camera rig; `hazard_view.gd` through it. The moves of §4.8 marked P6a. Catalogue: `level_changed`, `room_event_started`; `PAYLOAD`. `FxLayer.KINDS`. Findings 2 and 3 fixed (the damage numbers setting, the double sounds). The three `UiKit` colours. `--moment`. `moments_data_suite`, the contract checks, `moments_suite` case 1 on the real rows and cases 3–10 on fixture rows | Screenshots of the moved effects match the build before them, except the two sounds now played once. All suites green; `valley_run` and `prologue_run` unchanged |
| **P6b · The breakthrough** | Row 3 to mockup 05; rows 2, 4, 6 redesigned; rows 9–15. Screen layers `dim`, `vignette`, `band`, `strip`, `card`, `stats`, `chip`, `seal`; FX kinds `pillar`, `converge`; the ink band; `brush_stroke`, `seal_press`, `gong_short`; `reduce_motion`; the lock and skip; strings (`realm_great.*`, `craft.*`, `failure.*`, `moment.*`) | Screenshots of §7.4 for row 3 match mockup 05; `moments_suite` cases 2 (breakthrough, level), 3, 7, 9, 10 and 11 on the real rows; the F4 check "never blocks input for more than 1.5 s" |
| **P6c · Bosses and the fountain** | Rows 17 (P6 form), 18 (card), 19, 20, 21. `loot_dropped` `source`. `LootView.launch`. `boss_sting`, `boss_fall`, `rare_chime` | A headless intro at Big Toad Tan's den (`valley_run` `sec_qk5` room); the phase card at his 50%; cases 2 (boss phase), 5 and 8 on the real rows; the fountain screenshot; `boss_suite`'s cases that exist still pass |
| **P6d · Rare finds and story** | Rows 22, 23, 24 (band). `rare` and `chapter_ends`. The `LootView` beam | Cases 4 and 14; screenshots of a rare drop, a chapter end and a trial opening |
| **P6e · The escalation curve** | The `vfx` block in `techniques.py`; `vfx_tiers`, `vfx_shapes`, `particles`, `numbers`; `FxLayer` spark count, size, style; cast rings; area wave width and echoes; number sizes; multi-hit stacks; `UiKit.fmt_short`; shake per cast; screen tints and the flash limiter; FX kind `rain` | Cases 12 and 13; screenshots one per tier and the three-hit case; `perf_tests` within budget with a swarm |

P6d and P6e do not depend on each other and may swap; each needs P6a, and P6d's strips need P6b.

**What P9 takes.** P9a can start when P6a–P6c are done (P6c's cards use P6b's screen layers). It uses: row 17, switching its trigger to `boss_engaged`
and adding its camera pan and 1.5 s lock (§2.4); row 18 with the phase card's text from the payload; row 19 with the
`stamps` layer for seals; row 21, the fountain; the camera rig's `add_shake` for `telegraph_struck` impacts
(`boss_design.md` §3.7). It adds rows 25, 26 and 27 and their strings. Its ground markers are not moments: they are
`fx_layer.gd`'s ground layer, polled from state, as `boss_design.md` §3.7 says.

**What P8b takes.** Row 28 and the FX kind `band_rise` (the band's ring rising from the feet to the waist in the
rank's colour), with `band_worn` in the catalogue.

---

## 9. Open questions, with recommendations

| # | Question | Recommendation |
|---|---|---|
| 1 | Mockup 05 times the three beats to 2.4 s. Hold the full frame to 3.6 s and fade by 4.0 s, with input back at 1.5 s? | Yes. Seven stat rows need a second to read, and the player has control throughout the hold |
| 2 | No camera zoom in any row. The art is drawn at 2 screen px per art px and the camera snaps to 2 px; any zoom but ×1.5 breaks the pixel grid | Yes, no zoom. If a punch-in is wanted later, only ×1.5 keeps whole pixels |
| 3 | Minor breakthroughs lose today's 0.2 s shake (nine of them a realm) | Yes; the major keeps it |
| 4 | In a fight, celebration cards (title, Dao, craft, pet, rare drop, chapter end) become toasts | Yes |
| 5 | A boss's killing blow could hold for 0.25 s of hit-stop. That is CombatAuthority's, a simulation change | Leave it to P9; P6 changes no simulation timing |
| 6 | The pill cloud takes its quality's colour (Halo orange, Soul pale violet) instead of today's gold and orange | Yes: one colour per quality everywhere (M24) |
| 7 | A new Reduce motion setting in Accessibility, off by default | Yes |
| 8 | Until P9a, the boss intro plays on the first aggro of every visit, not only the first fight | Accept for the gap; P9a's `first` limits it |
| 9 | A level gained alone plays a new short gong instead of today's guzheng run | Yes, per F4; the minor breakthrough keeps the run |
| 10 | The tribulation's storm is laid again every 5 s for the whole rite (today 6 s once) | Yes |
| 11 | `loot_dropped` gains `source`, a payload key in `world_authority.gd` | Yes: no state or rule changes, and the fountain cannot tell a boss from a jar without it |

## Decisions taken

The recommendations above are taken (2026-09-27) so the build can start. The user can overturn any of them before its
step lands: 1, 2, 3, 4, 6, 7, 9, 10 and 11 as recommended; 5 goes to P9; 8 is accepted for the gap until P9a.
