# Audit: S43 Traversal, platforms and room verticality (packet p1) against the build

Project root: `/home/user/Game/JadeRiver` (read-only audit; nothing was run). Paths below are relative to it.
Room evidence is the generated `data/rooms/<id>.json` cross-checked against `tools/data/world.py`.

**Counts (273 requirement rows):** Present 27 · Partial 94 · Differs 64 · Missing 88.

Build baseline in one paragraph: movement is `MovementSolver` (scripts/simulation/movement_solver.gd) plus `ZoneGeometry`
(scripts/simulation/zone_geometry.gd). A surface has only an `open_edges` bool. There is no `blocks`, `climbables`,
`movers`, `volumes`, `edges`, `void_altitude` or camera `bounds` key in any of the 122 room files. Solid scenery at 80 or
lower (or flagged `standable`) gets a walkable "support" top (scripts/simulation/zone_layout.gd:215-220). The whole world has one
ladder, a walkable ramp (`lf_village` `hall_ladder`). The double jump (full 530 impulse, apex 244) is available as soon as
Jump unlocks. `movement_pass()` (tools/data/world.py:2273-2328) adds generic 110/220/320 ledges (JUMP_ONE, JUMP_TWO,
FLIGHT_LEDGE, world.py:2141) to rooms that have nothing vertical. Every one of the 137 spawn groups is on `ground`. None of the
223 breakables and 1 of the 81 gathering nodes sit on a raised tier.

---

## 1. v0.3 measured facts (Kept / Changed)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| World model 2.5D plane + altitude; bounds 5,400 × 480 (y 480–960); ground strip y 620–960 | Present | data/world.json bounds [0,480,5400,480], `river_walk` [0,620,5400,340]; rooms use [0,480,W,480] + ground [0,620,W,340] (world.py:14-16,169,181) | — |
| Surface kinds ground, stairs, ramp, roof, branch: rect + height + optional rise/rise_axis | Present | scripts/surface.gd:14-25 (extra kinds rock_ledge, balcony, cloud, dock, deck, ladder, support also exist) | — |
| Ground stratum: walk only, steps ≤ 8, stairs by rise, closed edges are walls with axis sliding | Present | zone_geometry.gd:92-100 (8.0 step); movement_solver.gd:102-114 slide; engine_tests.gd:46-50, 85-87 | — |
| Platform stratum: one-way, land on crossing while falling, walking off an open edge drops | Present | zone_geometry.gd:109-124; movement_solver.gd:93-101; platform_contact.gd:59-69 | — |
| Jump impulse 530, gravity 1,150, substeps 1/120; apex 122.1; air time 0.92 s | Present | movement_solver.gd:3-5; rules_tests.gd:651 checks the apex (air time is not tested) | Add an air-time check to the regression suite |
| Reach: walk 205, sprint ×1.7 (190 / 322 flat), total air control | Present | stats.py:56 (`move.base` 205, `sprint` 1.7); player.gd:263; movement_solver.gd:77-78 | — |
| Landing reach by rise (+40 … −176 table) | Present | Physics unchanged, so the numbers still follow; no test asserts them | Add them to the regression suite (see Tests) |
| Rooftop route geometry (west chain 88/176/264, east chain 100/200/300, pine_branch 100, terrace 80 by depth stairs) | Present | Copied from world.json into `ja_gate_street` and `ja_pavilion_rooftops` (world.py:723-740, 762ff); engine_tests.gd:66-81 | — |
| "From the ground only 88 and 100 are reachable; 176/200/264/300 need the chains" | Differs | Spec: only 88/100 from the ground. Build: the double jump has no unlock (movement_solver.gd:14 allows `jumps_used` < 2), so 176 and 200 can be reached from the ground (apex 244) | Gate the second jump behind Cloud Ladder Step (Qi Unfurling 6) |
| Ladders → climb mode, 160 units/s × climb stat, context button or 0.3 s hold | Differs | The v0.3 `links` lerp code is gone. A ladder is now a walkable ramp surface of kind `ladder` (world.py:209-214; zone_geometry.gd:96-97), and there is one in 122 rooms | Implement `climbables[]` + climb mode (rule 5) |
| Fall recovery → room void_altitude, safe-position rule, 5% HP | Partial | The v0.3 part holds: altitude < −250 returns to the last safe spot, with the spawn as fallback (player.gd:288; world.gd:512-545), and resources are kept (engine_tests.gd:97-106). The changed parts are missing | See rule 6 |
| Air attack speed → ×0.8 in the air | Differs | Spec ×0.8 in the air. Build: ×0.3 whenever attacking, in the air too (combat_authority.gd:73; stats.py:56 `attack_factor` 0.3) | Add `move.air_attack_factor` 0.8 when `surface == null` |
| Solid objects → blocks (rule 1) | Partial | Building bodies and scenery footprints are solid; tops only for scenery ≤ 80 or `standable` (zone_layout.gd:208-220; world_authority.gd:61-66). There is no `blocks[]` | See rule 1 |

## 2. Problems M1–M15 (also covers the "Movement analysis findings" cross-reference table)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| M1 back edges: per-side edges, platform back edges closed by default | Partial | No per-side edges: `open_edges` is a bool, default true (surface.gd:10,25). By code reading, the void fall is avoided a different way: `constrain_air_motion` snaps an airborne actor outside the ground band to the nearest ground edge (zone_geometry.gd:73-82). The back edge still drops the player to the ground strip | Add `edges{n,s,e,w}`, with north closed by default |
| M2 objects to jump on/over: blocks | Partial | Standable scenery tops (22–86 high, STANDABLE world.py:2142-2147; zone_layout.gd:218-220). There is no blocks data or breakable blocks | Blocks section (rule 1) |
| M3 wall faces + redefined Wall-Step | Partial | Roof facades are solid `_body` volumes that Wall-Step can kick off (zone_layout.gd:208-214; movement_solver.gd:22-38). Numbers differ (see rule 7) and blocks have no wall faces | Add wall faces and edges; re-tune Wall-Step |
| M4 press-up vs depth: context button, 0.3 s hold with little sideways input | Partial | Attack doubles as context and shows "Enter" (hud.gd:273-279,814-824; world_authority.gd:417-422). Press-up still enters after a 0.18 s hold with `axis.y < -0.6` and no sideways limit (world.gd:228-240). There is no Context button | 0.3 s hold, sideways < 0.3; add a Context button |
| M5 ladder lerp → real climb mode | Differs | The ladder is a walked ramp and there is no climb mode (see rule 5) | Climb mode in MovementSolver |
| M6 coyote 0.10 s / buffer 0.12 s | Missing | No timers. Walking off an edge sets `jumps_used=1` (movement_solver.gd:101), so a late press spends the air jump at any point of the fall. There is no buffer | Add `coyote_left` and `buffer_left` |
| M7 air attacks ×0.8 | Differs | ×0.3 everywhere (combat_authority.gd:73) | As in section 1 |
| M8 reach ladder by realm band | Differs | No arts ladder. The full double jump is there from the first Jump; only Wall-Step (HT4), Wind Blink (SA5) and Flight (CS1) arrive later | Add the movement arts and reach table (rules 7–8) |
| M9 enemies stuck on own platform: nav graph, species jump data, out-of-reach rule | Missing | Enemies are clamped to their spawn surface (enemy_authority.gd:177-186); enemy_brain.gd:3 says "patrol (own platform)" | Rule 11 |
| M10 fall recovery goes to last safe (spawn only as fallback) | Present | world.gd:512-521 | — |
| M11 flight vertical input is not depth | Present | Held Jump rises and held Guard descends; the joystick moves x and depth (hud.gd:189-192,203-205; player.gd:269-274) | — |
| M12 per-room camera bounds, landing-based vertical follow | Partial | `camera{y_min,y_max}` in 18 rooms; default clamp 470–600 (world.gd:242-256) | Rule 13 |
| M13 movers and volumes | Partial | S17 hazards give gusts, currents, falling-rock strikes and pools (world.py:94-155; world_authority.gd:604ff). No movers, updrafts, bounce, crumble or rising water | Rule 1 movers/volumes |
| M14 required routes share ≥ 60 depth | Missing | pine_branch (y 680–760) and east_entry (y 560–710) still overlap by 30 (data/rooms/ja_pavilion_rooftops.json). 182 of 231 platforms are only 44–56 deep | Deepen platforms; lint |
| M15 rules for using height | Partial | `movement_pass()` makes sure 115 of 122 rooms have something to climb (world.py:2273-2328; rules_tests.gd:699-709). None of rule 14's placement rules exist, and there is no lint | Rule 14 + lint |

## 3. Owned state, intents, emitted events

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `mode`: ground · air · climb · mantle · glide · flight · swim · ride | Partial | Only the `flying` bool plus surface/null (actor_state.gd:12-22) | Add a mode enum |
| `surface` or `block_top` | Partial | Block tops are `support` surfaces, so `surface` covers them (zone_layout.gd:219) | Keep, or add `block_top` |
| `rider_of` (mover ID) | Missing | — | Add with movers |
| `jumps_used` per airtime | Present | actor_state.gd:12 | — |
| `air_dash_used` | Missing | — | Add with Swallow Dart |
| `wall_kicks_used` | Differs | Spec: a count (3 per airtime). Build: `wall_step_used` bool, one kick (actor_state.gd:18) | Make it an int |
| `coyote_left`, `buffer_left` | Missing | — | Add |
| `climb {climbable, t}` | Missing | The `climb` field is flight's vertical input (actor_state.gd:20) | Rename the flight field; add climb state |
| `last_safe {room, surface, x, y}` | Partial | Kept in the presentation node world.gd:34,486-489 as {surface,x,y,…}, with no room, not in ActorState and not in the snapshot | Move into ActorState |
| Arts cooldowns | Partial | `pools.cooldowns` holds dodge and wind_blink (combat_authority.gd:349,356-361) | Add per-art cooldowns |
| Intents `move`, `jump` | Present | local_authority.gd:12-19 | — |
| Intents `drop_through`, `climb`, `climb_move`, `glide` | Missing | — | Add |
| Intent `dash {dir}` | Partial | It exists as the Combat intent `dodge {direction}` (combat_authority.gd:88,336), not a movement intent | Route through Movement |
| Intent `fly_vertical {up · down · hold}` | Partial | `LocalAuthority.set_climb(-1..1)` + `fly(on)` (local_authority.gd:22-27) | Rename/align |
| LocalAuthority validates art known, cooldown ready, room allows | Partial | `jump()`/`wall_step()` check nothing (local_authority.gd:19-20). The checks live in player.gd:88-92 (unlock, secret art) and Combat.start_flight (combat_authority.gd:100-107) | Move validation into LocalAuthority |

## 4. Rule 1 · Geometry kinds and volumes

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Existing surface format kept (rect, height, rise, rise_axis, kind, stratum) | Present | surface.gd:14-25 | — |
| `edges {n,s,e,w}` = open / closed / wall; platform default n closed; `open_edges` true = that default, false = all closed | Missing | Only `open_edges`, where true means every edge is open (surface.gd:25; movement_solver.gd:93) | Implement per-side edges and wall faces |
| New visual kinds: ledge, deck, stilt, raft, bridge, pole, canopy, cloud | Partial | `cloud` (12) and `deck` (1, ground stratum, lf_lu_boat) exist. Ledges are `rock_ledge` (135). There are no stilt, raft, bridge, pole or canopy kinds | Add the kinds (or map rock_ledge → ledge) |
| `blocks[]`: id, rect, base, top, kind (crate…lantern), breakable loot, wall_faces | Missing | Nearest is `scenery[]` {id, prop, footprint, height, standable} (world.py:287-294); breakables are separate non-solid objects | Add the section and loader |
| Block: below top − 8 cannot enter, slides | Partial | `blocks_at` blocks any altitude below base+height, with no −8 tolerance (zone_geometry.gd:32-39); slides via resolve_motion (:51-60) | Add the −8 rule |
| Block: falling actor crossing top lands; top walkable, all edges open | Partial | Only scenery ≤ 80 or `standable` gets a top (zone_layout.gd:217-220). Taller blocks have none (spec: all blocks, standable to 110) | Give every block a top |
| Block: walk around in depth; a full-depth block must be jumped | Partial | Depth sliding works. No full-depth blocks (fences, walls) exist in any room | Author full-depth blocks |
| `climbables[]` (ladder, rope, vine, chain; at, top_at, bottom, top); old `links` load as climbables | Missing | A ladder is a ramp surface (world.py:209-214), 1 in the world; no `links` loader | Add the section and climb mode |
| `movers[]` (surface, path, speed, wait_s, loop/pingpong/trigger; tick-pure; riders carried) | Missing | — | Implement |
| `volumes[]` (rect, alt range, kind, parameters) | Missing | Nearest: room `areas[]` {kind, rect} (shallows, river, water, hollow_puddle, thorns, poison_mist, quicksand) and room `hazards` (world.py:220-223) | Add the section (can wrap areas/hazards) |
| Volume water_shallow: ×0.7, no sprint or dash | Partial | `shallows` area gives ×0.7 (player.gd:315-322; stats.py:57), but sprint and dodge still work there | Block sprint/dash |
| Volume water_deep: sink to −40 over 1 s, then recovery; Breath Control 30 s swim; Water Skimming | Partial | `deep_water` is a room aura hazard with a breath cycle and air pockets, only in ds_drowned_grotto (world.py:139-141, 2252-2267). `river` areas are unwalkable scenery. No sinking or recovery | Implement the volume |
| Volume current: push 60–160 along a vector | Partial | `current` flow hazard pushes along x in `shallows` (world.py:103-105); wg_rapids_terraces area `current: -60`; none in Flooded Gate | Make it a vector volume with a speed |
| Volume updraft: vertical speed eases to +220 | Missing | — | Implement |
| Volume wind: 4 s pulse (1.5 s strong), stronger near edges | Differs | Spec: 4 s cycle, 1.5 s strong, stronger near edges. Build: `wind_gust` cycle [2.5,1.2,1.8,6.0] (≈11.5 s, 1.8 s active), uniform push 230 (world.py:100-102) | Re-time the pulse; add the edge factor |
| Volume bounce: launch 700 (apex ≈ 213) | Missing | — | Implement |
| Volume crumble: breaks 0.8 s after stood on, returns after 5 s | Missing | — | Implement |
| Volume rising_water keyed to an event | Missing | — | Implement |
| Volume hazard: status/damage per second; falling rocks shadow 1 s ahead | Partial | Pool hazards pulse each 1 s (thorns, poison_mist, hollow_puddle). falling_rocks warns 1.1 s with marked spots (world.py:94-98,110-135). These are room-wide cycles, not alt-ranged volumes; Lower Pit has none | Express them as volumes; 1.0 s warning |
| Volume no_flight | Partial | Room flag `no_flight` (only ss_starsea_crossing, gc_windbridge) plus interiors (combat_authority.gd:106). Sect grounds and dungeons allow flight | Volume kind; flag sect grounds and dungeons |

## 5. Rule 2 · Jump model

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Impulse 530, gravity 1,150, 1/120 substeps kept; base jump never scales with stats or gear | Present | movement_solver.gd:3-5,18 (constants; move_speed only scales x) | — |
| Coyote time 0.10 s | Missing | — (see M6) | Add |
| Jump buffer 0.12 s | Missing | — | Add |
| Height fixed; early release does nothing | Present | No release handling; hud.gd:255 only clears `fly_up` | — |
| Air control total | Present | movement_solver.gd:77-78 | — |
| Air attack ×0.8, ground ×0.3 | Differs | ×0.3 in both (combat_authority.gd:73) | Split by support |
| Air attack: one hit, no combo, +10% damage | Missing | basic_attack combos the same in the air (combat_authority.gd:222-236) | Add an air branch |
| Plunge: down + Attack in the air | Missing | — | Implement (rule 7) |

## 6. Rules 3–4 · Drop through, ledge mantle

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Drop through: on a platform (not ground, not block), joystick toward camera ≥ 0.7 + tap Jump; surface ignored 0.25 s | Missing | Only walking off the front edge drops you (platform_contact.gd:66-69) | Implement `drop_through` |
| Ledge mantle: airborne, surface/block top 0–24 above within 16 → pulled up in 0.2 s | Missing | (PlatformLanding assists catch landings from above only: platform_landing.gd) | Implement mantle |

## 7. Rule 5 · Climbing

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Enter ladder/rope/vine/chain via context prompt, or hold up 0.3 s with sideways < 0.3 within 28 | Missing | The ladder ramp is simply walked onto (zone_geometry.gd:96-97) | Implement |
| Attack shows "Climb"/"Enter" only when no enemy is aggroed on the player within 400 | Differs | Spec: no aggroed enemy within 400. Build: the label shows when no non-passive enemy is within 150, aggro or not (hud.gd:281-285,814-824); "Enter" exists, "Climb" doesn't | Use an aggro check at 400; add a Climb label |
| Separate Context button at a fixed HUD spot while a ladder or portal is in range | Missing | — | Add the button (S24) |
| HUD buttons take priority over the joystick zone | Present | hud.gd:158-178 (joystick is the last fallback) | — |
| Climb speed 160 × (1 + climb stat, cap +50%) | Partial | The `climb_speed` stat exists with cap 0.5 (stats.py:17), but nothing reads it | Use it in climb mode |
| Joystick up/down on the climbable; stopping allowed | Partial | You walk the ramp in depth and can stand on it; there is no climb state | Climb mode |
| Jump leaves sideways; ropes/vines +20% horizontal | Missing | — | Implement |
| Hit knocks off; techniques blocked unless `on_climb`; mounts dismount/remount on landing | Missing | — | Implement |

## 8. Rule 6 · Falls and recovery

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Landing on any surface never costs HP | Present | No fall damage anywhere in scripts/ | — |
| Room `void_altitude` (default lowest surface − 250) | Differs | Spec: per room, from the lowest surface. Build: fixed `altitude < -250` (player.gd:288,397) | Add the room field |
| water_deep without the art → recovery | Missing | — | With the volume |
| 0.3 s fade out | Missing | Recovery is instant (world.gd:512-545) | Add the fade |
| Return to last safe position; room spawn only when none | Present | world.gd:512-521 | — |
| Fall costs 5% max HP (≥ 1 HP left); free in Prologue, towns, safe rooms | Missing | The room `safe` flag exists (world.py:167) but falls ignore it | Implement |
| Safe spot recorded only after 0.3 s standing ≥ 24 from an open edge; `record_safe_position()` forces a record | Partial | Recorded every frame on any surface, edges included (world.gd:265,486-489); the forcing call exists (engine_tests.gd:98) | Add the timer and edge-distance rule |
| Void-fall recovery may trigger a fortune encounter (S49) | Missing | — | Hook on `fell_out` |
| Enemies falling into the void despawn and respawn without loot | Missing | Enemies can't leave their surface (enemy_authority.gd:177-186) | With the nav graph |

## 9. Rule 7 · Movement arts

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Arts live in `secret_arts.json`; Movement owns their use | Partial | secret_arts.json (techniques.py:141-149) holds dodge_dash, wall_step, wind_blink, breath_control. Use is split across player.gd, MovementSolver and CombatAuthority | Add every movement art; route through Movement |
| Jump: Prologue P2 (The Runaway Kite); apex 122 | Present | Unlock `jump` after A Quiet River, tied to the_runaway_kite (story.py:373); apex rules_tests.gd:651 | — |
| Ladders and ropes: P2, Context button | Differs | No unlock and no context use; one walkable ladder ramp, no ropes | Climbables + unlock |
| Drop Through: P2, Down + Jump | Missing | — | Implement |
| Ledge Mantle: always, automatic | Missing | — | Implement |
| Sprint: always on, hold 2 s, ×1.7; Race to the Tower gives the title | Present | player.gd:252-263; stats.py:56; story.py:377,604-607 (title `fleet_footed`) | — |
| Plunge: BF4 (Outer Trial); 900/s, area 60, 120%, 0.5 s stun, cd 4 s | Missing | — | Implement with quest |
| Dodge Dash: BF5; Evade tap on the ground; 140, 0.25 s invulnerable, cd 2.5 s | Present | combat_authority.gd:336-361; stats.py:98-99; story.py:410 (also works in the air when Wind Blink is not known) | Restrict to the ground once the air dash exists |
| Falling Leaf Glide: QK3 via "Leaf on the Wind" (Crane Falls); 120/s descent, ×1.1, 2 QI/s | Missing | — | Implement art + quest |
| Swallow Dart: QK7 library quest; Evade in the air; 140, altitude held 0.25 s, once per airtime | Missing | — | Implement |
| Cloud Ladder Step: QU6 quest; impulse 430 (+80), apex ≈ 202, once per airtime | Differs | Spec: impulse 430 (apex ≈ 202), unlocked at QU6 by quest. Build: always available with the full 530 impulse (apex 244) and no unlock (movement_solver.gd:14-18; docs/movement.md) | Gate it; use impulse 430 for the second jump |
| Water Skimming: QU8 hermit quest; run on water_deep while sprinting | Missing | Hermit (hermit_yao) exists in rm_hermit_stilt_house; no art or quest | Implement |
| Wall-Step: HT4 via "Between Two Walls" at Echo Cliffs; Jump pushing into a wall within 12; vz 450 (+88), 90 away, 3 kicks | Differs | Spec: needs push into a wall within 12; vz 450; 90 units away; 3 kicks; guided quest. Build: realm unlock with no quest (story.py:499-500); wall probe 26 units with no push-in needed (movement_solver.gd:22-26); vz 0.95 × 530 = 503.5 (+110); away-push is 0.2 s of walk input (player.gd:94-96,266-268); 1 kick | Retune the numbers; add the quest |
| Wind Blink: SA5 Technique; blink 120, usable in the air, never through blocks | Partial | 120 in the air, collides via resolve_motion; fired by the Evade tap in the air rather than a technique; 10 s cd (combat_authority.gd:341-352) | Move to the technique bar or document |
| Flight: CS1; hold Jump in the air | Differs | Spec: hold Jump in the air. Build: a third press after the double jump takes off (player.gd:102-105; wings_of_cloud objective story.py:910) | Hold-to-fly while descending |
| Gale Step 200, Tiger Rush 120, Cloud Descent (flight dive) | Present | techniques.json gale_step dash 200, tiger_rush dash 120, cloud_descent flying_only | — |
| Grapple (rope-dart, v1.3+) | Missing | — (a later version) | Later |

## 10. Rule 8 · Reach table

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Contract: required routes use only the lowest band's arts with ≥ 15% margin, gaps measured at walk speed | Missing | No contract. JUMP_ONE 110 is 90% of apex 122, a 10% margin (world.py:2141) | Encode the table; ledge heights ≤ 100 before the double jump |
| Prologue–BF4 limits: rise ≤ 100, gap ≤ 150 (≤ 114 rising 88–100); sprint gaps ≤ 250 optional | Differs | Spec: rise ≤ 100 in the first band. Build: Lv 1–3 rooms have 110 rises (wp_west, wp_east `ledge_mv_0`; lf_old_ma_store `loft_mv`) and 220 double-jump ledges with chests (wp_west/wp_east `ledge_mv_1`) | Re-height early rooms |
| Later bands (+Plunge, +Glide, +Air dash, +Double jump ≤ 160/200, +Wall-Step shafts ≤ 370, +Flight below room ceiling) | Missing | Not banded. Flight has one global ceiling of 340 (stats.py:69), not a room ceiling | Add band gating and a room ceiling |

## 11. Rule 9 · Controls

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Jump button (new press) = jump / double jump / Wall-Step; Wall-Step wins at a wall face | Partial | Order holds, Wall-Step is checked first (player.gd:92-101). A third press also means flight (player.gd:102-105) | Drop the third-press flight |
| Glide / flight = Jump held while descending; holding from take-off never spends the double jump | Differs | Spec: hold Jump while descending. Build: flight is a third press and there is no glide | Hold logic |
| Drop through = joystick toward camera ≥ 0.7, sideways < 0.3, + Jump | Missing | — | Implement |
| Climb / enter portal = Attack label when no enemy aggroed; in fights Context button or press-up hold | Partial | "Enter" on Attack (150-unit proximity rule); 0.18 s press-up (world.gd:228-240); no Climb, no Context button | See rule 5 |
| Dodge / air dash = Evade tap; Guard = hold | Partial | Guard tap ≤ 0.18 s dodges, hold guards (hud.gd:257-261). There is no air dash (an air tap is Wind Blink, if known) | Add Swallow Dart |
| Plunge = joystick toward camera + Attack in the air | Missing | — | Implement |
| Flight: joystick x/depth; hold Jump rise; hold Evade descend; neither holds altitude; tap Evade = dash | Partial | All but the dash: in flight a Guard press only sets `fly_down`, so no dodge is sent (hud.gd:203-205,255-261) | Tap Evade = dash in flight |

## 12. Rule 10 · Combat on tiers

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Hit-test altitude band relative to the attacker's altitude | Present | combat_authority.gd:176-189 | — |
| Default melee band −30 to +60 (a ground fighter cannot hit a target on an 88 roof) | Differs | Spec: −30 to +60. Build: player families use [0,90] to [0,110] (weapon_families.json) and enemies default to [0,70] (combat_authority.gd:648). Fists reach a target standing at 88 | Set −30..+60 |
| Qi arcs −10 to +80 | Differs | Spec: −10 to +80. Build: technique default [0,110] (techniques.py:14; combat_authority.gd:546) | Set −10..+80 |
| Arrows and thrown weapons fly at launch altitude +58 | Present | combat_authority.gd:476 | — |
| Projectiles pass through platform decks; stopped by blocks and wall edges | Partial | Decks don't stop anything. Enemy shots under 60 stop at obstacles (combat_authority.gd:852); player shots ignore obstacles; there are no wall edges | Collide both teams with blocks and walls |
| Knockback along x and depth; can push actors off open edges | Partial | Player knockback is an x-only forced move through LocalAuthority and can carry you off an edge (combat_authority.gd:725-730). Enemies stay clamped to their surface (enemy_authority.gd:79-85,177-186) | Add depth; let enemies fall |
| Knocked off a ladder drops you | Missing | — | With climb mode |
| Plunge breaks breakable blocks and cracked floors | Missing | — | With Plunge |

## 13. Rule 11 · Enemy traversal

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `movement {jump, climb, fly, drop}` per enemy in enemies.json | Partial | Only a `flying` bool, on 13 species (enemies.json) | Add the block |
| ZoneGeometry navigation graph per room (surfaces + block tops; walk/jump/drop/climb/mover edges), deterministic, cached | Missing | — | Implement |
| EnemyBrain patrols home surface and chases along the graph within its leash | Partial | Patrol and chase stay on the spawn surface; leash 600 (enemy_brain.gd:74; enemy_authority.gd:177-186) | Chase on the graph |
| Out of reach: −50% damage after 2 s; leash home + 10% HP/s after 6 s; rubble throw (Pebble Imp, Cliff Ape) | Missing | — | Implement |
| Flyers ignore the graph | Present | Flying enemies move freely (enemy_authority.gd:174-176) | — |
| Tier natives (archers, imps, frogs, monkeys, vultures) start on raised surfaces | Missing | All 137 spawn groups use `surface: ground` (data/rooms/*.json) | Place spawns on tiers |

## 14. Rule 12 · Companions and pets

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Follow along the navigation graph | Differs | Spec: follow along the graph. Build: they follow on the plane with altitude fixed at 0 (ally_brain.gd:28,74-78) | Graph follow |
| Blink to the owner past 480, or after 2 s unable to reach, in a puff of mist | Differs | Spec: 480 units, or 2 s unable to reach. Build: snap past 700 units (ally_brain.gd:77), no 2 s rule | 480 + 2 s rule |
| Ground mounts jump with their species impulse (default 530), no climb/wall-step, dismount and remount; flying mounts use flight | Partial | A mount changes speed (player.gd:261) and flight QI (combat_authority.gd:136). The rider jumps with the player's 530; no dismount rule | Add mount movement data |

## 15. Rule 13 · Camera

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Room data `camera {bounds, look_ahead}` | Partial | `camera {y_min, y_max}` in 18 of 122 rooms (world.py:367,399,542) | Bounds rect + look_ahead |
| Follow x with look-ahead ×0.25 of velocity | Differs | Spec: ×0.25 of velocity. Build: room mode uses facing × 60 (world.gd:248); only the legacy map uses velocity × 0.25 (world.gd:243) | Use velocity |
| Vertical follow of the support surface, 0.4 s ease after landing, follows falls > one tier | Differs | Spec: follow the support surface, easing after landings. Build: follows the sprite position, jump arc included, minus 110, with an exp lerp at rate 6 (world.gd:249,263; player.gd:405) | Landing-based follow |
| Look down 60 after standing 0.5 s near an open edge over a drop > 150 | Missing | — | Implement |
| v0.3 clamp y 180–730 becomes the default for one-screen rooms | Differs | Spec: 180–730 by default. Build: room-mode default 470–600 (world.gd:253); 180–730 only on the legacy map (world.gd:245) | Change the default |

## 16. Rule 14 · Verticality rules (room lint)

Figures computed from data/rooms/*.json.

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Field/path/town rooms ≥ 2 screens: ≥ 2 tiers above ground plus a raised route spanning 40% of the width | Partial | 58 such rooms. Most have 2+ platform heights, but only 6 have raised surfaces whose widths add to 40% of the room: lf_village, sf_market, sf_artisan_row, np_hall_of_nine, sq_lower_pit, wg_echo_cliffs. None is a continuous route, and hv_sect_grounds has no platform | Author raised routes |
| ≥ 30% of breakables on raised tiers | Missing | 0 of 223 jars, crates and wine jars have `alt` | Move breakables up |
| One in three gathering nodes on raised tiers | Missing | 1 of 81 (ja_herb_terraces `herb_2` alt 120) | Move nodes up |
| Chests on the highest tier or behind an optional challenge | Partial | 43 of 67 chests are on ledges, mostly movement_pass 220/320 chests (world.py:2300-2312). The rest sit on the ground (e.g. sq_lower_pit `chest_11`, bg_whispering_bamboo `chest_10`) | Lift the rest |
| Every raised tier reachable two ways; every tier has a way down that is not a void fall | Partial | Ways down are fine (walk off onto the ground). The world has 1 ladder and 3 stair runs, so almost every tier has one way up (a jump) | Add ladders, ropes, stairs |
| No required landing < 80 wide or < 60 deep; consecutive route platforms share ≥ 60 depth | Differs | Spec: at least 60 deep. Build: 182 of 231 platforms are 44–56 deep (ledges 50, decks 52–56, lofts and shelves 46) | Deepen to ≥ 60 (kit: 80–150) |
| Standard heights (built 88 multiples, natural 100 multiples, blocks 40/60/80/110, ≤ 100 before the double jump) | Differs | Spec: built tiers in 88s, natural in 100s, blocks 40/60/80/110. Build standard is 110/220/320 (world.py:2141): 77 platforms at 110, 47 at 220, 14 at 320. Block tops are 22–86 (world.py:2142-2147) | Re-height |
| Blocks ≤ 60 high / ≤ 100 deep can be jumped over; blocks ≤ 110 standable | Partial | Physics allows the jump-over (apex 122). Tops exist only for scenery ≤ 80 or flagged (zone_layout.gd:218) | Tops to 110 |
| Some monsters in every field region live on tiers | Missing | 0 raised spawns | Rule 11 |
| Each region introduces one new traversal element in a safe spot first | Missing | — | Design pass |
| Visual language: lit lip on walkable tops, flat highlight on standable blocks; never on scenery | Missing | No lip or highlight drawing in terrain.gd or scenery_prop.gd | Art + draw |
| Shadow projects onto the support below | Present | shadow.gd:5-10 | — |
| Old rooms keep optional later-art ledges | Missing | No art-gated ledges (220 ledges are open to all through the ungated double jump) | Author later ledges |
| A "later" ledge is gated by height (> 122, > 202 with the double jump) and within the art's reach | Differs | Spec: gated by height against the band's arts. Build: 220 ledges are 98+ over the ground via a free double jump, so nothing is gated by an art | Heights per the rule |

## 17. Rule 15 · Traversal content, data, UI and tests

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Daily rooftop chase "catch the thief" (Stoneford, Gate Street) | Missing | — | Implement |
| Race to the Tower (timed route) | Partial | 25 s timed quest (story.py:604-607), but the goal bell is on the ground (lf_village `tower_bell` [3590,710], no alt), not a 264 flag | Put the finish on the tower top |
| Sect "Cloud Steps" trial ranked in S42 | Missing | — | Implement |
| Plum-blossom poles in the Sword Court: poles 40 wide at 60–110 | Differs | Spec: Sword Court, 40 wide, 60–110 high. Build: five `training_stump` blocks 26 wide, 64 high in hv_sect_grounds (world.py:2240-2242); cm_sword_court has only its hall roof (110) | Add poles to the Sword Court |
| Kites and chests on roofs; herbs on cliff ledges; ore on scaffolds | Partial | Kite on the Ferry Inn roof (alt 176) and roof_chest on heaven_roof (alt 300) are present. No herbs on ledges and no scaffolds | Place nodes up |
| Entry Trials: Jade = rooftop climb with moving planks; Cloud = ropes and ledges | Differs | Spec: Jade roof climb with movers; Cloud ropes, ledges and a crumble. Build: both trials are the same 60/120/180 rock_ledge steps (world.py:687; sf_trial_jade, sf_trial_cloud) | Rebuild both |
| "Paths Above" collection book page | Missing | — | Implement |
| Data: new sections in rooms/*.json (Part 5) | Missing | No blocks, climbables, movers, volumes, edges, void_altitude or camera bounds anywhere | Generator + loader |
| Data: movement.json holds every constant of the system | Missing | Constants are spread over movement_solver.gd:3-5 and stats.json `move`/`flight`/`combat` | Create movement.json |
| Data: movement arts in secret_arts.json | Partial | 4 of the ~14 arts are listed (techniques.py:141-149) | Add the rest |
| Data: `movement` in enemies.json and pets.json | Missing | Enemies have only `flying`; pets have nothing | Add |
| UI: landing ring when airborne within 200 above a surface | Missing | Only the drop shadow at the current position (shadow.gd) | Implement |
| UI: context labels Climb and Enter; in-fight Context button | Partial | "Enter" exists (world_authority.gd:422); no Climb, no button | Add |
| UI: minimap blocks as squares, climbables as vertical lines, movers as dashed lines | Missing | — | Implement |
| UI: unlock toast with a one-line how-to the first time each art is usable | Partial | The toast says "New: <label>" (hud.gd:431-433), with no how-to line | Add a how-to string |
| UI: wind glyph on the World map for opened later ledges | Missing | — | Implement |
| Test: every Kept fact holds as a regression suite; each Changed fact tested by its rule | Partial | engine_tests.gd:42-91 (strata, stairs, roof chains, one-jump limit); rules_tests.gd:651 (apex). No air-time, 190/322 reach or landing-reach-by-rise tests | Add the missing facts |
| Test: back edges closed, a north sweep never leaves the room | Partial | engine_tests.gd:234-243 sweeps 8 directions on the legacy map for supported positions; no per-room check that the actor stays in the room | Add over room data |
| Test: blocks stop walking and can be stood on; a 60 block is jumped at walk speed | Partial | engine_tests.gd:108-124; movement_review_v09.gd:89-96; rules_tests.gd:672-681 (crate landing); no 60-high jump-over | Add |
| Test: coyote and buffer at dt 1/30, 1/60, 1/120 | Missing | — | Add |
| Test: mantle; ladder climb, stop, jump off, knock-off | Missing | — | Add |
| Test: drop through only on platforms | Missing | — | Add |
| Test: each art at its numbers | Partial | Wall-Step once per airtime and only by a wall; double jump reaches 220 (rules_tests.gd:663-698). No dodge, blink or flight numbers | Add per art |
| Test: mover riders deterministic across replays | Missing | Command-replay determinism exists (engine_tests.gd:244-254) but there are no movers | Add |
| Test: every volume behaves as its row says | Partial | hazards_suite covers the gust push and the shallows current (rules_tests.gd:444-532) | Per-volume tests |
| Test: navigation graph identical on two builds | Missing | — | Add |
| Test: out-of-reach rule | Missing | — | Add |
| Test: pets blink after 2 s | Missing | — | Add |
| Test: room lint (rule 14) passes for every room | Missing | Only "≤ 3 flat rooms" (rules_tests.gd:699-709) | Add the lint |
| Test: reach table, a scripted character with the band's arts reaches every required objective | Missing | valley_run.gd travels rooms without a reach check | Add |

---

## 18. Platform kit (art and data)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Pavilion roof · roof/platform · 250–660 × 150 · 88/176/264 · lit ridge lip · back edge closed | Partial | v0.3 roofs (660/440/250 × 150) at 88/176/264 and 100/200/300 in ja_gate_street and ja_pavilion_rooftops. Other `Room.building` roofs are sized from their art, 68–120 deep, at 124–196 (e.g. fishers_hut 124, old_ma_store 168, stilt_house 196). No lip; back edges open | Standard heights, lip, closed back |
| Balcony, branch · branch/platform · 200–300 × 80 · 100 | Differs | Spec: 80 deep at 100. Build: `balcony` decks 200–300 × 46–56 at 110/220 (world.py:2317-2319, 2217-2240). Only pine_branch (300 × 80 at 100) matches | Re-size |
| Stall awning, tent top · deck/platform · 120–200 × 80 · 88 · bounce at the Fair | Missing | — | Add |
| Stilt deck, dock · stilt/platform · 160–260 × 100 · 60–120 · ladder on one side | Missing | Docks are ground-stratum h 0 (lf_village `pier_a`, `pier_b`) | Add |
| Driftwood, log raft · raft/platform (mover) · 120–220 × 60 · 30–90 · pingpong | Partial | lf_reed_shallows driftwood_a/b/c: `branch` 200–230 × 46 at 60/90/70, static | Make them movers of kind raft |
| Rock or cliff ledge · ledge/platform · 120–400 × 100 · 100/200/300 · back edge wall | Differs | Spec: 100 deep at 100/200/300 with a wall back. Build: `rock_ledge` 160–360 × 44–60, mostly at 110/220 (100/200/300 only in wg_echo_cliffs); no wall back | Re-size; wall back |
| Bamboo platform, pole · pole/platform · 40–80 × 40 · 60–270 | Missing | Closest: training stumps 26 × 18 at 64 (hv_sect_grounds) | Add |
| Rope bridge · bridge/platform · 300–600 × 60 · 100–200 · ladders at both ends | Missing | — | Add |
| Scaffold · deck/platform · 200 × 80 · 90/180 · ladders between | Partial | ae_shipyard `scaffold_slip` 280 × 50 at 120 (balcony); sq_quarry_rim `ledge_0` at 90 is a rock ledge; no ladders | Add |
| Cloud ledge · cloud/platform · 150–300 × 100 · 300+ | Partial | 12 `cloud` surfaces 240 × 44 at 320 (world.py:2306-2312) | Depth 100 |
| Crate, barrel · block · 40–60 × 40–60 · 40 / 80 stacked · breakable variants | Partial | Standable crate (top 36) / barrel (top 48), 26 deep (world.py:2143). Breakable crates are non-solid objects; no stacking | Block kinds, stacking, breakable blocks |
| Cart, wagon · block · 120 × 60 · 60–70 | Partial | `cart_broken` standable 120 × 26 at 70 (sf_gate, cr_caravan_road) | Depth 60 |
| Fence, low wall · block · 20–40 × full depth · 50–60 · forces a jump | Missing | `stone_wall_low` (48) is not full depth; `fence_wood` is decor without collision | Add |
| Wall, palisade · block (wall faces) · 20–40 × full depth · 160 | Missing | — | Add |
| Boulder, statue plinth · block · 80–120 × 80 · 80/110 · cover from arrows | Partial | rock_large 78 and boulder_moss 86 standable (world.py:2145); player shots pass through obstacles | Heights; arrow cover |
| Well, stone lantern · block · 60 × 60 · 40–60 | Differs | Spec: a 40–60 block. Build: the well is decor without collision; stone lanterns are 68–90 high, 25 deep (lf_village `stone_lantern_2` 90, ja_gate_street 68) | Make them blocks at 40–60 |
| Pillar · block (wall faces) · 40 × 40 · 110–220 · Wall-Step pairs 60–160 apart | Missing | — | Add |

## 19. Lotus Ferry and the Prologue

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Fisher's Hut (lf_fishers_hut): loft 88 by ladder; Lu's old float (Codex) + Herbal Tea on it, visible before Jump | Missing | Flat room; the three teas are on the floor (`tea_table`, `tea_shelf`, `tea_stove`) | Add loft, ladder, float |
| Home Lane (lf_village x 0–1280): 40–60 blocks, crates, fence with open gate, well, two cottage roofs 88; Aunt Ping's ladle | Partial | Two cottage roofs at 124 (`fishers_hut`) and 128 (`granny_hut`); one barrel 50. Well and fence are decor with no collision; no crates, gate or ladle | Blocks, 88 roofs, ladle |
| Village Square: 0 · 88 · 176 · tower 264; ladder to first roof, roof chain, watchtower ladder; kite on 176; race finish at 264 | Partial | hall_ladder → village_hall 88 → ferry_inn 176, kite alt 176, all present. No watchtower in the square (`watch_tower` 312 is in the Docks district, no ladder); race bell on the ground | Tower 264 + ladder; finish flag |
| Ferry Docks: 60 boat deck, 80 crates (40+40), mast lookout 150 by ladder; fishing at pier end; gull nest | Partial | `fish_docks` at the pier is present. Piers are ground at h 0; `sack_pile` stays decor; watch_tower roof 312. No boat deck, stacked crates, mast or nest | Add pieces |
| Old Ma's Store: loft 88 by ladder, shelves (blocks 110); Old Net on the storeroom floor; Straw Sandals in the loft | Differs | Spec: 88 loft with a ladder and 110 shelves. Build: generated `loft_mv` 110 with no ladder, one barrel 48; the Old Net is handed over on accept (story.py:590); no sandals | Rebuild |
| Granny Liu's Herb Hut: mezzanine 88, ladder, herb jars (breakable blocks); Willow Moss bundle for Granny's Remedy | Differs | Spec: 88 mezzanine by ladder with breakable jars. Build: `loft_mv` 110, no ladder, no jars; Granny's Remedy has no Willow Moss step (story.py:592-598) | Rebuild |
| Night in the village (P4): village roofs; Minnows can't jump; Eel lunges at roof edges; roofs as refuge | Partial | lf_village_night copies four roofs (88/124/128/168); no ladder or inn roof. hollow_minnow and hollowed_eel are `flying` (enemies.py:80-82), so they ignore tiers | Ground minnows; eel edge lunge; ladder |
| Lu's Boat (P5): deck 0, cabin roof 88, ladder, meditation spot on the roof | Missing | Flat deck by design (docs/movement.md) | Add cabin roof + ladder |
| Reed Shallows: driftwood 60–90 rafts (pingpong), stilt hut 100, reed bundles 40, rock 80, shallow strip; Willow Moss on stilt hut, jars on driftwood; Snapper dodge by hopping onto a rock | Partial | Three static driftwood platforms (60/90/70) and a `shallows` area are present. No stilt hut, reed or rock blocks or movers; moss and jars on the ground | Add pieces; lift nodes |

## 20. Willow Path, Stoneford and the sects

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Willow Path West (wp_west): branches 100, later 240 (+140, double jump); stumps 50, lifting stones 40, log 70; toads on branches; chest on 240 | Differs | Spec: 100 branches plus a 240 later ledge. Build: generated rock ledges 110 / 220 with a chest at 220, reachable by the free double jump. Stumps and lifting stones are objects without collision; toads spawn on the ground | Rebuild to spec |
| Willow Path East (wp_east): merchant cart 70, shrine roof 88, signpost; merchant on the cart | Differs | Spec: a 70 cart and an 88 shrine roof. Build: generated 110/220 ledges + chest; no cart or shrine roof; Old Pan on the ground | Rebuild |
| Market Street (sf_market): awnings 88, balconies 176, rooftops 264, bell tower 300, ladders; thief chase; notice copy on the tower; shard in a gutter | Differs | Spec: 88/176/264/300 tiers with ladders. Build: three roofs at 168/158/168; no awnings, ladders or tower | Rebuild |
| Artisan Row (sf_artisan_row): scaffolds 90/180 with ladders, crates, roofs 176, chimney 330; ore crates on scaffolds; gear on the chimney | Differs | Spec: 90/180 scaffolds and a 330 chimney. Build: roofs 158/168/128 only | Rebuild |
| Fairground (sf_fairground): tent tops 100, stage 60, drum bounce; lanterns via bounce; recruiters on the stage | Differs | Spec: 100 tents, 60 stage, a bounce drum. Build: balcony decks 110/220 (world.py:2226-2227); recruiters on the ground | Rebuild |
| Stoneford Gate (sf_gate): gatehouse walls 160, stairs to a 160 walltop; guard captain's post | Partial | Gatehouse roof 150 (520 wide) + guard_tower 312 + cart 70. No stairs or wall blocks; guard on the ground | Add stairs, walls, 160 walkway |
| Entry Trial (Jade): 0 → 88 → 176 → 264 roof climb, two moving planks, ladders; puppet at the top | Differs | Spec: roof climb to 264 with movers. Build: rock_ledge steps 60/120/180, bell alt 180; the puppet spawns on the ground | Rebuild |
| Entry Trial (Cloud): 0 → 100 → 200 → 300, ropes, one crumbling ledge; puppet at the top | Differs | Spec: ropes and a crumble to 300. Build: identical to the Jade trial | Rebuild |
| Gate Street (ja_gate_street): v0.3 west chain, back edges closed, ladder to 176; mission hall roof chest; thief chase | Partial | jade_roof 88 / bridge_roof 176 / cloud_roof 264 present. Back edges open (no `open_edges` key, so the default is open); no ladder, roof chest or chase | Close edges; ladder; chest |
| Pavilion Rooftops (ja_pavilion_rooftops): v0.3 east chain, pine branch, depth stairs, ladder terrace → 300; retreat entrance on the 300 roof; herb pot on the branch | Partial | east_entry 100 / east_step 200 / heaven_roof 300, pine_branch 100, rear_stairs + upper_terrace 80, roof_chest alt 300 present. No ladder; the retreat door is on the ground in ja_east_terrace; no herb pot | Ladder; move the door; pot |
| East Terrace (ja_east_terrace): 80 terrace, depth stairs, lanterns 40; cave-abode doors (SA5) | Differs | Spec: an 80 terrace by depth stairs. Build: roofs `mission_hall` 120 and `retreat_rooms` 200; no terrace or stairs; cave abodes open from the elders' peaks | Rebuild |
| Alchemy Hall (ja_alchemy_hall): mezzanine 88, ladder, furnace platform block 40; recipe shelf up | Differs | Spec: 88 mezzanine with a ladder. Build: `loft_mv` 110, no ladder; furnace is an object without collision | Rebuild |
| Library (ja_library, cm_cloud_library): floor 2 at 120, floor 3 at 240, ladders sealed by rank (Requirement) | Differs | Spec: floors 120/240 by sealed ladders. Build: `loft_mv` 110 in both; floors exist only as unlocks (story.py:477 `library_floor_3`) | Sealed climbables |
| Weapon Hall and Forge (both): racks 110, sparring ring 40; dummies on the ring | Differs | Spec: 110 racks and a 40 ring. Build: `loft_mv` 110; dummies on the floor | Rebuild |
| Herb Terraces (ja_herb_terraces): 0 · 40 · 80 · 120 ground terraces by depth stairs; beds on each | Differs | Spec: ground terraces 40/80/120 by stairs. Build: two platform rock ledges at 60/120; beds at alt 60 on the first only; no stairs | Ground terraces + stairs |
| Elder Hu's Peak (ja_elder_hu_peak): 100 · 200 · 300 ledges with ladders; meditation rock on 300 (Qi ×1.5) | Differs | Spec: 100/200/300 with ladders. Build: `ledge_peak_0` 110, `ledge_peak_1` 220, no ladders; insight stone on the ground | Rebuild |
| Cliff Stair (cm_cliff_stair): 100 · 200 · 300 by depth stairs and ropes; Cloud Library entrance on 300 | Partial | `stair_a` (rise 100) → ground landing 100, `ledge_hi` 200 present. No 300 tier, no ropes; the library door is in cm_sword_court | Add 300, ropes, door |
| Sword Court (cm_sword_court): plum-blossom poles 60–110 (40 wide), pillar pairs 160 tall 120 apart; spars; Wall-Step practice | Missing | Only `sword_hall` roof 110 | Add poles and pillars |
| Array Court (cm_array_court): dais 40, formation tables (blocks 60) | Differs | Spec: a 40 dais and 60 blocks. Build: tower roof 200 + `rope_ledge` 150; formation table is an object without collision | Rebuild |
| Elder Sung's Peak (cm_elder_sung_peak): 100 · rope bridge 200 · 300, ladders | Differs | Spec: a rope bridge between 100 and 300 peaks. Build: 110/220 shelves; no bridge or ladders | Rebuild |

## 21. Fields, dungeons and secret places

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| Quarry Rim (sq_quarry_rim): scaffolds 90/180, crane lift 0 ↔ 180 (trigger mover), ore carts 60; copper on scaffolds; imps throw from 180 | Partial | ledge_0 90 (spec 90) and ledge_1 120 (spec 180); falling_rocks hazard present. No lift or carts; copper and imps on the ground | Add pieces; lift nodes/spawns |
| Lower Pit (sq_lower_pit): tiers 200 · 100 · 0 with ramps, ladders, falling-rock volumes; Jadeiron bottom, Riverstone on ledges; plunge floor to a shard | Differs | Spec: 3 descending tiers with ramps and ladders. Build: ledges 90/180/264/120 above ground; no ramps, ladders or falling rocks; ores on the ground; the tunnel is a `hidden` portal, not a plunge floor | Rebuild |
| Collapsed Tunnel (sq_collapsed_tunnel): rubble blocks 40–80, cracked wall (Body); shard veins behind rubble | Differs | Spec: rubble blocks. Build: one `ledge_tunnel` 110; no rubble; shard vein on the open ground; no Body check on the way in | Rebuild |
| Marsh Edge (rm_marsh_edge): stilts 60–100, reed blocks; Reed Frogs hop; Willow Moss on stilts | Partial | branch platforms at 70/90 (within 60–100). No reed blocks; frogs and moss on the ground | Stilt kind, blocks, tier spawns |
| Grey Pools (rm_grey_pools): log rafts 30 over water_deep, lily-pad bounce, Hollow puddles; chest on raft loop; bounce to a 200 ledge | Partial | `hollow_puddle` areas present. Otherwise generic 110/220 ledges + chest; no rafts, deep water or bounce | Rebuild |
| Sunken Causeway (rm_sunken_causeway): broken causeway 40 with 120 gaps; 300 pillar top with jars (Wall-Step) | Differs | Spec: a 40 causeway with gaps and a 300 pillar. Build: generic 110/220 ledges + chest | Rebuild |
| Hermit's Stilt House (rm_hermit_stilt_house): house 120 by ladder; hermit; Water Skimming quest | Partial | `stilt_house` roof at 196 and hermit_yao present. No ladder; no Water Skimming quest | Ladder; 120; quest |
| Hamlet Square (gh_hamlet_square): grey roofs 88/176, well; "Grey Roofs" = cleanse lanterns on roofs | Differs | Spec: 88/176 roofs with lanterns on them. Build: roofs 124/158; `well_cleanse` inspect; `grey_roofs` is a kill quest in rm_grey_pools (story.py:1528) | Rebuild quest + roofs |
| Whispering Bamboo (bg_whispering_bamboo): bamboo 90 · 180 · later 330, bent bamboo bounce (apex 213), vines; monkeys on 90/180; Ember Pepper on 90; chest on 330 | Partial | branch platforms 110/180/110 (180 matches). No 330, bounce or vines; monkeys, pepper and chest on the ground | Add pieces; lift content |
| Thicket Heart (bg_thicket_heart): canopy decks 100/200, vines; nests on the canopy | Partial | Generic ledges 110/220 + chest; no vines or nests | Canopy kind at 100/200 |
| Falls Pool (cf_falls_pool): rocks 60–100 in shallow and deep water, waterfall updraft; ground portal to the Hidden Vale; Mist Lotus on a rock; glide quest | Partial | The `vale` ground portal is present. Flat by design; no rocks or updraft; lotus on the ground; no glide quest | Add rocks, updraft, quest |
| Behind the Falls (cf_behind_falls): 100 · 200 · later 520, Wall-Step shaft (walls 120 apart); lotus and journal on ledges; chest at the shaft top | Differs | Spec: 100/200 ledges and a Wall-Step shaft to 520. Build: one `ledge_falls` 110; chest and journal on the ground | Rebuild |
| Caravan Road (cr_caravan_road): cliff ledge 120 (ladder), rope bridge 200 (ladders), carts 60–70; archers on 120; crates on the bridge | Partial | Two `cart_broken` 70 blocks present. Generic 110/220 ledges; no ladders or bridge; bandits on the ground | Add pieces |
| Stockade (mh_stockade): palisade 160, gate, watchtowers 180 with ladders; archers on towers; key on a tower | Differs | Spec: walls and 180 towers. Build: generic 110/220 ledges + chests | Rebuild |
| Tunnels (mh_tunnels): 0 · 60 · pits; crumbling planks over spike pits, low beams; jars on planks | Differs | Spec: crumble over pits. Build: generic 110/220 ledges; poison_mist areas | Rebuild |
| Loot Cave (mh_loot_cave): stalagmite blocks 80/160, crates; loot on high stalagmites | Differs | Spec: 80/160 stalagmite blocks. Build: one generic 110 ledge | Rebuild |
| Boss Den (mh_boss_den): shelves 88 holding wine jars; Tan heals from them; break by jumping or plunging | Partial | Three `wine_jar` objects and Tan's `drink_wine` phase (enemies.py:255) present, but the jars are on the ground. Generic 110/220 ledges | 88 shelves with the jars on them |
| Pilgrim Stairs (cp_pilgrim_stairs): 0 → 80 → 160 → 240 by depth stairs, cliff shortcuts 100; guardians on landings | Partial | Heights 80/160/240 match, but as jump platforms, not stairs; no 100 shortcuts; guardians on the ground | Depth stairs; spawns on landings |
| Cleansing Summit (cp_cleansing_summit): pillars 60/120 around the rite circle; block ground shockwaves | Differs | Spec: pillar blocks that stop shockwaves. Build: two rock ledges at 110 | Pillar blocks |
| Bend Shore (dw_bend_shore): docks 60, boats (movers), stepping stones over deep water; ginseng on a boat roof; fishing | Partial | Fishing spot and shallows present. Generic 110/220 ledges; no docks, boats or deep water | Add pieces |
| Serpent's Shallows (dw_serpents_shallows): high rocks 90/120, rising_water to 60 in phase 2 | Partial | Three `high_rock` at 100. No rising water | Heights; rising_water |
| Flooded Gate (ds_flooded_gate): floating planks, current | Differs | Spec: planks and a current. Build: generic 110/220 ledges; a shallows strip with no current | Rebuild |
| Hall of Lanterns (ds_hall_of_lanterns): swinging lantern platforms 100–200 (circle movers); ghosts between tiers | Differs | Spec: circle movers. Build: one 110 ledge; ghosts are flyers | Movers |
| Scripture Well (ds_scripture_well): shaft 0 → −300, void_altitude −550, ledges down, Breath Control underwater section; inscriptions on ledges | Differs | Spec: a shaft down to −300. Build: flat ground + 110 ledge. The Breath Control dive is a separate room reached by a door (ds_drowned_grotto, world.py:2252-2267); inscriptions on the ground | Rebuild descent |
| Abbot's Sanctum (ds_abbots_sanctum): 100 · 200 platforms with four small bells; rising_water; ring bells by jumping | Partial | Four `small_bell` objects present, but at ground level. Generic 110/220 ledges; no rising water | Bells on 100/200 |
| Gorge Mouth (wg_gorge_mouth): rope bridge 200 with ladders at both ends | Differs | Spec: a 200 rope bridge. Build: generic 110/220 ledges + chest | Rebuild |
| Rapids Terraces (wg_rapids_terraces): stepping stones 40–80 over rapids, current; Earth Fire vent; fishing on a stone | Partial | Current in the shallows and `earth_vent_wg` present. Ledges 80/150/80, not stones; fishing on the ground | Stones; fishing up |
| Echo Cliffs (wg_echo_cliffs): 100 · 200 · 300, ledges with wall backs, pillar shafts; vultures dive from 300; Jadeiron on 200; Wall-Step quest | Partial | Ledges 100/200/300/200 match. No wall backs or pillars; vultures and ore on the ground; no quest | Walls, pillars, quest |
| Waterfall Cave (wg_waterfall_cave): wet ledges 100 · 200; Mist Lotus, shard vein, journal page | Partial | One 110 ledge; journal on the ground; no lotus or vein | Ledges; place content |
| Cliff Faces (cc_cliff_faces): ledges to 600, updraft columns; "Wings of Cloud" lessons; Cloudwing Cranes | Partial | Ledges 160/180/240/300 + cloud 320; cranes present. No updraft; flight ceiling 340 caps everything | Room ceiling; updrafts |
| Sky Ledges (cc_sky_ledges): 400–900, flight only, cloud ledges, updrafts | Differs | Spec: 400–900, flight only. Build: rock ledges 260/360 and the global flight ceiling of 340 | Room ceiling; re-height |
| Misty Slopes (mp_misty_slopes): 100 · 200 in fog; Soulbell on a fogged ledge | Partial | `fog` hazard present. Generic 110/220 + cloud 320; soulbell on the ground | Heights; lift the herb |
| Forgotten Monastery (mp_forgotten_monastery): ruined roofs 88/176, crumbling floors, hidden portals; remnants on roofs | Partial | Hall roof 120 and insight stone present. No crumble, hidden portals or 88/176 roofs | Add pieces |
| Ascension Gate (mp_ascension_gate): ring platforms 200, flight phase | Partial | Gate Guardian `flight_phase` present (enemies.py:286). Arch roof 220, no rings | Ring platforms |
| Windswept Ridge (sr_windswept_ridge): 100 · 200 ledges, gust volumes; Rocs gust you off ledges; Mystic ore | Partial | `wind_gust` hazard present. Ledges 160/220 + cloud; ore on the ground | Re-height; edge gusts |
| Frozen Shrine (sr_frozen_shrine): 100 · icicle platforms (crumble); Mystic ore, Soulbell | Partial | Generic 110/220 ledges; ore present on the ground. No crumble; no soulbell | Crumble platforms |
| Trial of Reflections (si_trial_of_reflections): mirror arena, 100 tiers left and right | Missing | Flat by design (docs/movement.md) | Add symmetric tiers |
| Gu's Warehouse (si_gus_warehouse): crate stacks 80, catwalks 176, rafters 264, ladders; stealth route over the rafters | Partial | Low standable sack piles 38 and a barrel 48. No stacks, catwalks, rafters or ladders | Add pieces |
| Siege of Two Sects (si_siege): battlements 160, towers 240, walls | Partial | Two `rampart` ledges at 110; no walls or towers | Rebuild |
| Vale Gate, Sect Grounds, Back Mountain: roofs by level (88/176); Back Mountain ledges 100/200/300 with cave abodes | Differs | Spec: 88/176 roofs and 100/200/300 ledges. Build: hv_vale_gate ledge 110; hv_sect_grounds has no roofs (buildings are inspect objects) and only 64 stumps; hv_back_mountain decks 110/220; cave abodes open from the elders' peaks | Rebuild |

## 22. Traversal events (S43–S49 list, traversal rows only)

| Requirement | Status | Evidence | Change needed |
|---|---|---|---|
| `jumped`, `landed`, `wall_kicked`, `art_used` (actor, surface, fall_height, art) → presentation, achievements, pets, quests | Missing | No such events. Movement emits nothing; Combat emits `flight_started`/`flight_ended`/`dodged` (combat_authority.gd:111,118,360) | Emit from Movement |
| `climb_started` / `climb_finished` (actor, climbable) | Missing | — | With climb mode |
| `fell_out` (actor, recovered_to) → 5% HP, fortune check, HUD fade | Missing | recover_to_safe emits nothing (world.gd:512-545) | Emit and subscribe |
| `volume_entered` / `volume_left` (actor, volume, kind) | Missing | Hazards emit `hazard_warned` etc. only (world_authority.gd:643) | With volumes |
