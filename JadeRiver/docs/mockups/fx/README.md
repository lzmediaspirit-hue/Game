# Technique animations: review sheets

The FX animation library of decision 23 (`docs/roadmap_master_ui.md`): one frame-by-frame effect per technique form,
the 24 of `docs/technique_plan.md` §3.2, in every element, at three richness bands. Built by
`tools/art/fx/build_fx.py` into `art/fx/` and `data/fx_art.json`; the sheets here are its `--review` output
(256-colour PNGs) and in-game captures. Pixel art at 2x native, nearest-neighbour; the game mirrors for the left.

## Generator sheets

| PNG | What it shows |
|---|---|
| `forms_band1_1x.png`, `forms_band1_2x.png` | every form (rows) × element (columns) at its impact frame, band 1 (vfx tiers 1–2), on the dark `#0A2027` and the earthy `#8a7a58` review backgrounds, at in-game size and at 2× |
| `forms_band2_1x.png`, `forms_band2_2x.png` | the same at band 2 (tiers 3–4): thicker strokes, more particles |
| `forms_band3_1x.png`, `forms_band3_2x.png` | the same at band 3 (tiers 5–7): the richest |
| `strip_<form>.png` (24) | every frame of one form (columns) × every element (rows) at band 2, 2×, the anchor marked in red and the impact frame starred: the motion, read left to right |
| `bolts_2x.png` | the four projectile loops (arc, volley, seeker, return) × every element, 2× |

Elements, in row order: water, wood, fire, earth, metal, wind, thunder, soul, formless, space, time.

## In-game captures

`ingame_<form>.png` (22): one technique per form in use today, four moments of its cast side by side (0, 0.15, 0.3
and 0.5 s after the cast; the hit frame at 0.2 s), cropped round the caster at 2×. Tester from the `valley_run`
checkpoint `ls6_end` (Sphere Lord 3, Lv 98; a copy, never the Max Tester save) on Willow Path East with two Wild
Boarlets set in front; under `--capture` the effect and the pose step a sixtieth a frame and the simulation holds
still from the cast, so the shot lands on the frame named and shows the effect on the pose (`main.gd`, `--cast`):

```
xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . -- \
  --load=user://valley_cp/ls6_end --load-slot --room=wp_east --at=420,760 --foe=wild_boarlet:2 \
  --cast=<technique>:<t> --capture --shot=<name>
```

| Form | Technique (element, pose) |
|---|---|
| strike | Cloudpiercing Stroke (wind, `swing_3`) |
| flurry | Flowing Palm (water, `punch`) |
| thrust | Jade Thrust (formless, `thrust_3`) |
| lunge | Tiger Rush (formless, `punch_2`) |
| sweep | Riverstone Sweep (earth, `thrust_3`) |
| arc | Thunder Dao Arc (thunder, `swing_3`) |
| volley | Twin Reed Shot (wood, `bow`) |
| rain | Cursive Storm (fire, `swing_2`, tier 5) |
| pillar | Mirror Mind Spike (soul, the wielded family's first combo step) |
| wave | Earthshaker Wave (earth, `thrust_3`) |
| burst | Ember Burst (fire, first combo step) |
| seeker | Flying Blades (metal, `thrust_1`) |
| return | Returning Crane Fan (wind, `swing_2`) |
| snare | Vine Snare (wood, first combo step) |
| counter | Willow Leaf Parry (wood, `swing_3`) |
| ward | Soul Lantern Ward (soul, first combo step, tier 3) |
| chorus | Clear Heart Melody (water, `attack`) |
| blink | Shadowstep Cut (wind, `thrust_1`, tier 3) |
| plunge | Cloud Descent (wind, `jump`, tier 3) |
| release | Sword Release (metal, `swing_3`) |
| swarm | Sword Swarm (metal, `swing_3`) |
| seal | Qi Seal Toll (metal, `swing_1`, tier 5) |

Domain and Echo have no technique yet (the plan's "(new)" forms); their sheets are reviewed on the generator sheets.
A `--cast` preview submits nothing: the hits it shows are drawn as a real cast's would be, at the hit frame.
