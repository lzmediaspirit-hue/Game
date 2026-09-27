# P5 · The World map as drawn

Screenshots of the World map as the framed painting (`docs/page_identity.md` row 7, mockups 16 and 16_resources,
decisions 11, 17 and 25). They are 1280 × 720 as captured, reduced to 256 colours; the `.gdignore` of `docs/ui_p5/`
keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of its checkpoints taken
by a valley_run on this build in a data folder of its own: `bf5` (Bone Forging 5, early in the valley), `qu5` (Qi
Unfurling 5, the checkpoint the mockups were drawn from; the character in the Jade Sect Academy), `ae_end` (the end of
Act II, on the Skyport Wreck in the Azure Expanse) and `ls6_end` (Sphere Lord 3, in the Wardens' Hall of the Lantern
Star Field). None uses the Max Test character, `--max-character` or `--unlock-all`. Each was captured headlessly from
`JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

`--open-page=world_map:<view>` opens a view (areas, resources, objectives) or the ranking; `--tap=x,y` taps the page.

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `map_areas_qu5.png` | qu5 | `--open-page=world_map --tap=218,443` | The valley with the Drowned Shrine chosen, as mockup 16: its way from the Academy lit gold (4 areas), the tracked quest's lantern and the event's gold blossom beside its node, each plate the area's name alone, the card with the Shrine's picture, the quest with Walk there, the event, its rooms and Track Route |
| `map_resources_qu5.png` | qu5 | `--open-page=world_map:resources --tap=1088,274` | Resources, Ores, Copper, as mockup 16_resources: the quarry ringed with the copper disc, the ores (Cloudsteel and Mystic Ore greyed, in areas not yet reached), Copper's rank, rooms and regrowth, the daily that asks for it, Track Route (2 areas) |
| `map_objectives_qu5.png` | qu5 | `--open-page=world_map:objectives` | Objectives (no mockup): the tracked quest and the valley's world events a row each, the chosen one's area in the picture, its way lit and Track Route |
| `map_areas_bf5.png` | bf5 | `--open-page=world_map` | Early: most of the valley locked, a locked area beside a known one with its name (dim), farther ones a padlock alone; Track Route shut with its lock on the area you stand in |
| `map_text_large_qu5.png` | qu5 | `--text-size=2 --open-page=world_map --tap=218,443` | Settings › Text size › Large: every plate larger and still clear of the rest, the zone tags a step smaller to fit, the legend on two lines, the quest's line cut with an ellipsis |
| `map_valley_ls6_end.png` | ls6_end | `--open-page=world_map --tap=488,50` | The valley late: every area open, the paths above marked with the wind glyph, the way from the Lantern Star Field lit from the gorge |
| `map_star_field_ls6_end.png` | ls6_end | `--open-page=world_map` | The Lantern Star Field, drawn from tokens until it has a painting: the star river, drifting lanterns, each area an isle under its node |
| `map_azure_ae_end.png` | ae_end | `--open-page=world_map` | Act II, the Azure Expanse drawn from tokens: far ranges over a sea of cloud; the Storm Ward the chosen area asks and the room hazards; Mirrorwater Lake's field boss |
| `map_ranking_ls6_end.png` | ls6_end | `--open-page=world_map:ranking` | The Heaven Ranking as a lacquer board over the dimmed painting |
| `compare_16_world_map.png`, `compare_16_world_map_resources.png` | qu5 | — | Each mockup above, the build below |

## Against mockups 16 and 16_resources

Matches: the painting filling the screen in its lacquered frame with the four cloud-scroll corners; the title plate
("World map" over the zone's name) and the pennant; the zone tags hung from the top rail, the locked ones dim with
their lock, and the Heaven Ranking; every area's node where the painting drew it (jade, gold, a padlock), the selection
ring, the dotted routes and the way lit gold; the lantern and the event blossoms beside their nodes; the card with the area's picture and what
grows there, the chips, the quest with Walk there, the event, the rooms with the hazard, Track Route with its count;
the Areas, Resources and Objectives tablets and the legend changing with the view; on Resources the kind filters, the
two-column list, the chosen ore's line, its daily and the ringed area with its disc.

Differences, each on purpose:

1. **The plates' sides are the layout pass's** (decision 17), not hand-placed: where the mockup put a plate above
   (Willow Path, Caravan Road) the pass may put it below or beside, whichever side it reaches first clear of every other
   plate, mark and node. The test holds it to that on the real data, in every view and at every text size.
2. **The Hidden Vale is open** at qu5: its gate at Crane Falls asks only for the account's own sect, which it has, so it
   is jade with its name; the mockup drew it locked.
3. **The clock is the capture's**: the event has about 12 h left, not 23 h 57 m, and the coming (violet) events are the
   ones due then (the gorge, the Academy, Stoneford, the Reed Marsh).
4. **The rooms**: the goal room first, then the rooms seen, then the unknown, as drawn; the mockup's "the Abbot" after
   the goal room has no field in the game's data and is left out.
5. **Resources** name the craft as the game does ("Apprentice Mining", not "apprentice delving"), and the list's
   names are the items' own, cut with an ellipsis where the mockup shortened them by hand ("Spirit Stone…").
6. **The foot's tablets start at x 48**, inside the safe area (style guide §2), where the mockup had 30.
7. **A locked tag's padlock** sits at the tag's upper right (Page's shared lock mark), not after its name.
8. **The plates name the area and nothing more**, and the dots are smaller (an available area's 9 px across its
   radius, the area you stand in 11, where the mockup drew 15 and 17). The mockup's second and third lines (the level
   band, "You are here", "Locked · Safe", the field boss and "ready", the kinds on Resources) are on the card when the
   area is chosen; the legend drops the field boss and the kinds, which no longer mark the painting. The `map_suite`
   holds every plate, in every view and text size, to one line with its area's name.

Not shown in a still: the opening (the card slides in from the frame's edge over 0.2 s; the chosen way lights dot by
dot over 0.3 s; with Reduce motion on the way shows lit and the page only fades in), which the `identity_suite`'s rules
cover, and the live marks' breathing glow.
