# Simulation and future multiplayer boundary

## What runs now

`ActorState` is a scene-free state model with stable entity and zone IDs, planar position, absolute elevation, vertical velocity, support surface, and takeoff elevation. Versioned snapshots contain primitive values and stable IDs, not scene paths or Node references.

`ZoneGeometry` loads the map once, indexes surfaces by ID, and owns walking, landing, obstacle footprints, save relocation, and occlusion volumes. `MovementSolver` integrates motion with bounded 1/120-second substeps and ballistic height, resolves both axes at closed boundaries, and treats elevated platforms as one-way jump surfaces. Decorative objects opt out explicitly. Platform actors ignore ground footprints below them; an actor falling to ground is moved to the nearest valid point before support is assigned.

`PlatformLanding` owns joystick landing guidance and projected-foot contact. It corrects depth registration only after a jump reaches the platform's elevation, while the descending visible feet overlap support. It never raises a player to an unreachable height or intercepts an ordinary walk-off fall. One landing finalizer updates support, height, jump count and guidance together. `ActorState.air_peak` makes the reachability decision reproducible through trusted snapshots.

`RoomTravel` owns full gate-crossing detection using the same gate data as generation. It tracks entry, cancellation and whole-body exit, independently of scene drawing. `room_gate.gd` draws the far and near portions with separate depth orders; `ZoneLayout` supplies solid posts. World only dispatches the accepted transition and mounts the next region. A future server must run this crossing state per actor rather than accept a client-requested destination.

`LocalAuthority` owns command ordering and movement execution. It rejects duplicate/stale sequences, nonfinite vectors and durations, and invalid movement parameters. Positions and speed are not supplied in client movement intent. The local caller supplies elapsed time and server-owned speed. It supports validated trusted snapshot correction and deterministic replay on the same runtime. This is a local authority adapter, not a network-security claim or a cross-platform bit-identical physics guarantee.

`player.gd` owns local input sampling, sprint/action timers, and animation. Its position properties delegate to ActorState. `world.gd` builds scenery depth, renderer-independent outline occlusion, camera, projectile effects, and save checkpoints. `wardrobe.gd` remains the local appearance/catalog/save adapter. `hud.gd` only routes controls and draws the requested interface.

Static object definitions are data, not scene-node collision bodies. The same footprint contract is used by local movement and trusted snapshot validation, which is necessary before moving the solver to a server. Occlusion is presentation-only. A future remote-actor view must evaluate the same volumes per replicated actor; outline state must never affect authoritative simulation.

## Extension contract

A future zone server should instantiate one ActorState and authority per authenticated entity, advance fixed ticks using server time, and bind input sequence streams to server-owned identities. The transport should carry normalized movement/action intents, acknowledged input sequences, and versioned state snapshots. It must not expose `restore_authoritative_snapshot` as a client command. Clients can reuse MovementSolver for prediction, then reconcile acknowledged snapshots and replay outstanding commands. Remote actors should interpolate snapshots separately from local prediction.

Combat, sprint eligibility, resource changes, equipment swaps, cooldowns, arrow spawning/hits, inventory, quests, and persistence must become server-owned before online release. Today those action/resource timers and projectiles are local. Preserve the same equipment IDs in authoritative inventories; rendering can continue using the existing avatar compositor.

Use zone IDs to partition simulation and interest regions to select nearby entities for replication. Put account authentication, database transactions, inventory authority, and session ownership behind separate adapters. Replace local JSON writes with a repository keyed by authenticated character ID; retain local JSON as offline storage or a cache only. Version and migrate save/snapshot schemas deliberately.

## Explicitly not implemented

No networking transport, login/accounts, live server, database, matchmaking, shards, interest management, client prediction/reconciliation loop, remote actor interpolation, authoritative combat, trading, or anti-cheat service is shipped. The changes provide the shared movement/state boundary and validation/replay tests needed before those systems are added.
