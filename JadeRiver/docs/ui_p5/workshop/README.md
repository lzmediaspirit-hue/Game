# P5 · The Workshop family: Crafts, Workshop, Garden

Screenshots of the Workshop family built to its rows in `docs/page_identity.md` (18, 29, 30) and its family in §2
(worked timber and tools: `wood`, `wood_dark`, `ember`, `SURFACE.soil`), the Crafts page beside its mockup
`15_crafts_furnace`. The Workshop and the Garden have no mockup. They are 1280 × 720 as captured, reduced to 256
colours; the `.gdignore` of `docs/ui_p5/` keeps Godot from importing them.

Every picture shows **Tester**, the character `tests/valley_run.gd` plays, from frozen copies of this build's own
valley_run checkpoints (run with `--cp=user://valley_cp/` under a scratch `XDG_DATA_HOME`): `ls6_end` (Sphere Lord 3,
in the Wardens' Hall) and `qk5` (Qi Kindling, on Elder Hu's Peak). None uses the Max Tester save, `--max-character` or
`--unlock-all`. Each was captured headlessly from `JadeRiver/`:

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=<copy of user://valley_cp/<checkpoint>> --load-slot --wait=2 --capture --shot=<name> <extra>
```

The furnace's screens use the page's own previews (`--open-page=alchemy:__extraction` and the rest): a Healing Pill
refine drawn with time stood still, nothing sent to the authority.

| Picture | Checkpoint | Extra arguments | What it shows |
|---|---|---|---|
| `crafts_extraction.png` | ls6_end | `--open-page=alchemy:__extraction` | Step 3: the five steps along the strip (two done, Extraction lit), the Nine-Dragon Cauldron over its fire on the brick hearth with the Still Water array round its foot, the two herbs on its rim (the first drawn 92%, the second in the fire), the heat gauge and its gold band at the left, the specks at the furnace's mouth; at the right the batch, "3 · Extraction", what to do, the herb's time, Put out the fire and Fan the flame |
| `compare_15_crafts_furnace.png` | — | — | Mockup 15 above, `crafts_extraction.png` below |
| `crafts_furnace.png` | ls6_end | `--open-page=alchemy:__furnace` | Step 2: the ingredients on the rim with their roles and natures, the furnace's line, the four fires (Earth Fire locked), the two arrays and the hint, Ingredients and Light the furnace |
| `crafts_fusion.png` | ls6_end | `--open-page=alchemy:__fusion_turn` | Step 4 while the array turns: the core glowing over the furnace, both essences merged, the needle on the mark bar, Turn the array |
| `crafts_condensation.png` | ls6_end | `--open-page=alchemy:__condensation` | Step 5: the ring closing on the pill over the furnace, Condense |
| `crafts_tribulation.png` | ls6_end | `--open-page=alchemy:__tribulation` | The pill tribulation: the storm over the hearth, two bolts answered and the third coming, Raise shield; the strip's sixth step lit |
| `crafts_alchemy.png` | ls6_end | `--open-page=alchemy` | Nothing chosen: the furnace on its fire, the recipe book at the right with the Experiment bench first, the rank on the brick |
| `crafts_cooking.png` | qk5 | `--open-page=cooking --tap=930,495` | The pot steaming over its fire, Riverfish Soup chosen: the River Minnow on the rim (0 / 2), the strip at Materials ("0 of 1 at hand"), − ×1 + and Cook shut with its reason |
| `crafts_forge.png` | ls6_end | `--open-page=forge` | The anvil over the forge's coals; the six forge modes along the strip |
| `crafts_forge_enhance.png` | ls6_end | `--open-page=forge:enhance` | The Forge's upkeep keeps its list on the workshop wall: the gear and the Enhance card |
| `crafts_talisman.png` | ls6_end | `--open-page=talisman` | Spirit paper standing on the hearth, the banked embers, the talismans at the right |
| `crafts_arrays.png`, `crafts_charts.png` | ls6_end | `--open-page=arrays`, `charts` | The blank plate and the star chart table as the vessels |
| `crafts_guild.png` | ls6_end | `--open-page=guild` | The three guilds along the strip, the ranks and the commission board on the wall |
| `crafts_text_large.png` | ls6_end | `--text-size=2 --open-page=alchemy:__extraction` | Settings › Text size › Large: the tags widen along the beam, the herb's name ends in an ellipsis on the rim |
| `workshop.png` | ls6_end | `--open-page=workshop` | The tool wall: Formations taken down (its compass's outline left on the pegboard, the compass laid on the bench), the blueprints and the standing formations on the bench |
| `workshop_appraisal.png`, `workshop_teaching.png` | ls6_end | `--open-page=workshop:appraisal`, `:teaching` | The loupe and the pointer taken down; the compass hung back on its hooks |
| `garden.png` | ls6_end | `--room=ja_herb_terraces --open-page=garden` | The Herb Terraces: three beds stepping down the hillside on their stone walls, the third's willow moss grown and ready; the basket of water, soil and dew; Bed 1 chosen, its tending at the right |
| `garden_racks.png` | ls6_end | `--room=ja_herb_terraces --open-page=garden:racks` | Two drying racks with their woven trays, both free; the board to put herbs on a rack |

## Against mockup 15

Matches: the tabs along the top and the title over them; the six steps as a strip across the top, each with its seal
(✓ done, the number lit gold now, dark to come), its name and the one thing it asks; one furnace for every step, over
its fire, with its slots, its fire and its array staying where they are; the ingredients on the rim, each with its
state ("92%", "In the fire", "Waiting"); the heat gauge at the left with its gold band, "Heat" over it and "cool" under
it; the array's name at the hearth's lower left and the fire's at its right; the specks at the furnace's mouth; at the
right the batch (the pill, ×n · fire · array), "3 · Extraction", what to do, the herb's bar, Put out the fire and Fan the
flame at the foot.

Differences, each on purpose:

1. **The material is the family's** (decision 14, page_identity §2): the window is the workshop's plank wall, the
   title hangs on a timber sign, the tabs are wooden tags on pegs along a beam, the strip and the controls are timber
   boards, and the furnace stands on a brick hearth with its fire burning in the arched mouth, where the mockup kept
   the kit's teal window and panels.
2. **The numbers are this build's preview**: a Healing Pill in the Nine-Dragon Cauldron over Charcoal with the Still
   Water array, not the mockup's Law Touching Pill over Heavenly Flame; its two herbs, not three.
3. **The herb's bar is its time in the fire** with the herb's name, as the page has always measured it; the mockup's
   "Next, Fusion" line and the "Hold" caption over the fan are left out (the strip already says what comes next).
4. **The other trades** follow the same shape with their own vessel (the pot, the anvil, the plate, the paper, the chart
   table, the hull as its output's icon) over a fire that burns hot, steady or banked by trade. The Forge's upkeep
   (Enhance, Inherit, Salvage, Reroll, Natal) and the Guild keep their two-column lists on the wall, with their modes or
   guilds along the strip; the Experiment bench lays your herbs along the rim.

## The Workshop and the Garden (rows 30 and 29, no mockup)

- **Workshop:** a pegboard of worked timber across the top with the six tools hung on two pegs each (HD
  `workshop_tool`: compass, loupe, needle roll, chisel, brush, pointer), each over its outline painted in ink at 40%;
  choosing a tab takes its tool off the hooks (the outline stays) and lays it on the bench (0.2 s; at once under Reduce
  motion). The bench below is dark planks seen from above; the jobs keep the kit's cards on it.
- **Garden:** a hillside of earth under a green cast; the beds step down the page on their stone walls, each its soil
  darker the richer its field, its herb at its stage (shoots, then the herb's own icon at 32, then at 64, glowing when
  ready), the field's grade on a hemp tag on a stake; the terraces settle into place as the page opens. The basket at
  the top holds the water, Spirit Soil and dew on hemp labels; the chosen bed's tending is a timber board at the right.
  The Racks tab hangs two bamboo racks with woven trays.
