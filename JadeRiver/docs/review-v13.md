# v0.13 review

## Landing defect and correction

The old tests steered toward hidden world-depth coordinates. A new reproduction
placed the player below the visible platform and held normal joystick directions:
only 12 of 320 original cases landed. The visible contact and the required depth
plane disagreed, explaining why steering down sometimes appeared necessary.

`PlatformLanding` now combines visible descending-foot contact with the existing
physical support rules. It requires the jump to have reached the platform height,
limits depth correction by the jump's elevation budget, checks the exact visible
support mask and solid obstacles, and preserves the rendered foot location.
Landing finalization is shared rather than recomputing a second incompatible
height crossing. Holding up retains support. Jumping again or releasing/steering
away preserves normal control. Ordinary walk-off falls do not receive projected
capture, preventing unwanted catches on neighbouring balconies.

## Gates

Generated rooms have two data-defined gates. Entry and complete exit of the
opening are tracked separately, with body clearance and height checks. Passing
beside a gate, reversing before completion, spawning outside it, and walking to a
map edge do not change rooms. Solid posts match the opening; the image has far
and near depth layers. Room changes preserve input, sprint, resources and save
identity, with a safe position inside the destination entrance.

## Review and checks

- 1,354 landing cases: all six map themes, stationary/held-up/diagonal visual
  approaches, eight-direction physical approaches, multiple speeds, 4–120 FPS,
  reachable double jumps and rejected unreachable single jumps.
- 501 foot-contact and platform walking checks.
- 304 held-up landing and snapshot replay checks.
- 1,751 movement/roof/stair/obstacle and route checks.
- 276 gate crossing, cancellation, clearance and post-collision checks.
- 76 generated-map cases, including invalid layouts.
- 127 runtime checks including forward/backward gate travel and save restoration.
- 2,057 combo checks; 1,963 engine checks; 1,820 animation sprite variants.
- Rendered actual HUD jump input, branch support, and gate depth in the game.

The review caught unwanted balcony capture during ordinary roof-edge falls;
projected capture is now limited to jumps. It also updated migration spawn and
destination entry positions to avoid beginning within a gate crossing.

## Cleanup and scope

Landing guidance/contact policy lives in `PlatformLanding`; ballistic integration
and one landing finalizer remain in `MovementSolver`. `RoomTravel` owns crossing
state independently of gate rendering. Transient recovery state is reset together.
Temporary trace scripts and an orphan UID were removed; script endings normalized.
Build caches, logs, concepts and candidate archives are excluded from the ZIP.
Automatic approval review blocked removal of old external build scratch artifacts;
those remain outside the packaged project.

The new body-first animation rule is in `AGENTS.md`; no new movement animation was
introduced in this release. The source ZIP may exceed 30 MB as requested. Existing
character art and the v0.12 weapon combos are preserved. There is no claim of
exhaustive proof or physical Android-device testing.
