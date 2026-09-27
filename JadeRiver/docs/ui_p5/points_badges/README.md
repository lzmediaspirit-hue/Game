# Points to spend: the badges by the HP panel

While a character has unspent points in a system it spends by hand, a small "+" badge shows at the top right of the
player panel, one for each system, in a row leftward from the corner. Each is a 32 px HUD glyph (`tools/icons`,
`families/hud.py` `POINT_BADGES`) inside a 48 px target, and each system has its own colour, shape and symbol, so
colour is never the only difference. A tap opens the system's page on the tab where the points are spent. A badge is
hidden while its system is locked or its count is 0. It pops in when it appears (with Reduce motion it just appears),
and a badge that appears during play also writes a line to the log (`hud.points_<id>`).

| Badge | System | Count (authority getter) | Unlock | Opens |
|---|---|---|---|---|
| jade circle, a meridian | Meridian points (Foundation) | `progression.meridian_points_free` | `foundation` | Cultivation · Foundation |
| violet diamond, a star | Realisations (the element trees) | `progression.realisations_free` (0 until a tree opens) | `technique_slots_2` | Techniques, on a tree tab |
| bronze square, a hammer | Bench points (Roll-Call) | `posts.bench_points_free` | `apprentice_bench` | Roll-Call · Bench |
| crimson hexagon, a scroll | Post Arts points | `posts.art_points_free` | `post_arts` | Works of the Post · Arts |

There are no other hand-spent point pools in the game's data and authorities. Dao insight fills tiers by itself,
pets learn from skill books, and sect contribution and activity points are currencies. The one table is
`HUD.POINT_SYSTEMS`; adding a row (and its glyph) adds a badge. `rules_tests` `points_badges_suite` checks each
system shown and hidden, each tap's page and tab, the row clear of every other HUD part, and the pop.

These pictures come from copies of this build's own `valley_run` checkpoints, run in a separate user folder
(`XDG_DATA_HOME` set to a scratch folder) and loaded with `--load`. They were captured at 1280 × 720 and reduced to
256 colours:

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `badges_all_rest.png` | `ls6_end` | `--wait=1` | All four at rest, right to left: meridian, Realisations, bench, Post Arts |
| `badges_row_x3.png` | `ls6_end` | | The same row enlarged 3× (nearest neighbour) |
| `badges_all_fight.png` | `ls6_end` | `--room=ar_ashborn_palisade --at=1500,840 --foe=ashborn_raider:2 --toggle=presence --wait=2` | In a fight: the row keeps clear of the party chips and the cluster |
| `badges_three_early.png` | `qu5` | `--wait=1` | Qi Unfurling 4: Post Arts is not unlocked yet, so three show |
| `tap_meridian_foundation.png` | `ls6_end` | `--tap-points=meridian --wait=2` | The jade badge tapped: Cultivation on Foundation, 240 meridian points |
| `tap_realisation_tree.png` | `ls6_end` | `--tap-points=realisation --wait=2` | The violet badge tapped: Techniques on the Water tree, 135 to place |
| `tap_bench.png` | `ls6_end` | `--tap-points=bench --wait=2` | The bronze badge tapped: Roll-Call on the Bench, 6 points free |
| `tap_post_art_arts.png` | `ls6_end` | `--tap-points=post_art --wait=2` | The crimson badge tapped: Works on Arts, 14 points |

`--tap-points=<id>` is a debug argument that taps the badge through the HUD, the same way a player does.
