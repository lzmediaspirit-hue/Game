# v0.8 review and fixes

## Confirmed causes

1. Branch terrain was sorted behind tree sprites, hiding the actual climbable platforms. It now draws in front of the tree canopy; the supported player draws above it.
2. Branch/cloud/ledge sprites and roofs used full rectangular support even where their textures were transparent. Support now uses conservative 32×24 occupancy masks derived from the matching texture regions. Every accepted mask cell passed nine alpha samples above 220/255. Branch rendering and support use exactly the same destination bounds.
3. Ground recovery could choose a collision-free point outside a walkable ground surface. Recovery candidates now require ground support at the matching elevation.
4. Old saved positions could lie in areas removed from roof/branch support. Compatible v0.6/v0.7 saves move to the nearest supported point on that surface.
5. Sprint timing included vertical motion and reset on minor depth steering. It now tracks horizontal direction only: more than two seconds of left/right movement, reset on reversal, stopping, blocked horizontal movement or attack. Region transitions preserve an active sprint.
6. Platform shadows still used the older rendering order and disappeared underneath the platform. Shadows now sit between platform artwork and player feet.
7. Arrows did not test scenery collision. Their travel now uses small collision steps against solid scenery and still expires at its original maximum range.

## Repeated verification

- Render the actual terrain into a transparent viewport and compare every supported sample against the resulting pixels, for both roof variants, branches, clouds and rock ledges.
- Stand on each forest branch for two seconds; walk off all four edges and assert that grounded actors always have support.
- Walk off every town roof in four directions at 30, 60 and 120 updates per second; reject unsupported grounded or embedded states.
- Repeat seeded generation and route checks, continuous climbing/descent and disk-save tests, double-jump/ground-boundary tests, existing engine regression checks, and viewport touch input checks.
- Render a touch-triggered double jump followed by a stable branch landing and inspect the screenshot.

No new gameplay controls or character artwork were introduced. Collision masks are tied to the current environment texture regions; changing those regions requires regenerating masks and rerunning the rendered support check. Physical Android testing remains unverified; passing these checks is not a claim that every possible gameplay bug is absent.
