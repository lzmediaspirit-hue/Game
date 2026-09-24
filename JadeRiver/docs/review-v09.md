# Movement review — 0.9

The map previously placed buildings against the rear ground edge, preventing circulation behind them. Roof spacing did not form traversable connections. A descending actor could be rejected by a building wall in the same physics step that crossed the roof top. Rectangular building volumes also disagreed with shaped roof edges.

## Changes

- Ground now extends behind buildings with a clear rear corridor; the front road stays open.
- Adjacent roofs form bidirectional double-jump routes. Higher roofs retain balcony approaches. No portals are introduced.
- Branch, cloud and ledge artwork projects above the ground's rear edge. Their physical support remains separate from the ground underneath.
- Landing is resolved at the crossed surface height before side-wall collision. Solid roof volumes use the same support silhouette as their roof, preventing edge snapping and unsupported walking.
- Generated regions contain stairs to a raised rear terrace. Stair entry uses destination elevation for collision. Elevated ground and its shadow use appropriate sprite depth.
- Older generator saves remain accepted. Missing surfaces retain safe spawn and preserve HP, QI, facing and skill page.
- Runtime map checks retain structural validation; expensive simulated route traversal runs in tests rather than blocking each mobile region transition.

## Coverage

`movement_review_v09.gd` exercises every generated route in six themes at 30, 60 and 120 FPS, both directions between roofs, rear circulation, stationary platform support, all four roof exits, position continuity, stairs, low obstacles, and roof-top crossings during frame delays up to 250 ms.

Other suites cover 72 seeded maps plus invalid layouts, character equipment and animation assets, saves and migration, touch input, double-jump limits and transitions, horizontal sprint after two seconds, skill-carousel animation, finite arrow travel, attack/meditation outlines and pixel-to-support alignment. Rendered captures cover building occlusion, roof standing, branches, terrace and the bottom ground edge.

This is bounded regression coverage, not a proof of every possible input sequence. Android export and signature verification do not substitute for testing on a physical phone.

## Preserved scope

Original character assets and environment artwork are retained. No NPCs, monsters, populated skills, new gameplay buttons, portals, network services or heavyweight dependencies are added. Equipment remains separate from character appearance. The simulation/authority boundary is retained for future multiplayer; online infrastructure is not implemented. The source packager still enforces 30,000,000 bytes.
