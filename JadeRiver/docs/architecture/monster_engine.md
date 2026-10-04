# The monster engine (audit 45 §6.2, E2, M1, M2)

A species is one `species(...)` spec. The engine makes everything the species is from it, through the generators that
already existed:

| What | Made by | From the spec's |
|---|---|---|
| its `enemies.json` row | `tools/data/enemies.py` (`mob()`, `atk()`, `d()`) | `data` |
| its `loot_tables.json` row | `enemies.py`'s loot pass | `data.drops`, `loot` |
| its top-down sheets and its `data/topdown/foes.json` block | `tools/art/topdown/creatures.py`, `build_foes.py` | `plan`, `parts`, `mats`, `motion`, `opts` and the art fields |
| its voice in `sound.json` | `tools/data/sound.py` | `sound` |
| its codex page | its row's collection `page` (`data.page`) | `data.page` |
| its wiki entry | `tools/dev/wiki.py`, from `data/` after a full build | (the row and the loot) |

Nothing else names a species: a new spec needs no edit to `enemies.py`, `creatures.py` or `sound.py`.

## Files

```
tools/content/monsters/__init__.py      the engine: species(), and what each generator asks of it (row, rows,
                                        loot, voices, art)
tools/content/monsters/build.py         the command line: build, --check, --list, --review ID, --update ID[,ID]
tools/content/monsters/specs/*.py       the specs, one file a region (sorted by name when read)
tools/art/topdown/creature/plans/       the body plans: kit.py (what they share), and one module a plan
tools/art/topdown/creature/sculpt.py    the sculpture and the renderer (unchanged)
tools/art/topdown/creature/motion.py    the action catalogue, frames and HIT_FRAME (unchanged)
tools/art/topdown/creature/mats.py      the ramps (five steps a material) and the single colours
```

## Body plans

A plan is a pose function: `pose(body, action, frame, **facing) -> Pose`. It reads its sizes from the species' parts
and its motion from named styles. Each plan was extracted from the species first drawn by hand with it. Every one of
those species draws byte-identical through its plan, so the hand modules are gone.

| Plan | Variants | Extracted from | Parts (kinds) |
|---|---|---|---|
| `quadruped` | `rodent`, `mustelid`, `suid` | the reed rat, the reed otter, the boarlets | body (three ellipsoids), head (`rodent`, `mustelid`, `suid`), legs (`paw`, `lope`, `hoof`), tail (`reed`, `thick`, `tassel`), coat (`streak`, `pale_chest`, `youth`), crest, dust; `opts.hollowed`: the Hollow's strands, cold eyes, a death into motes |
| `amphibian` | `frog`, `toad` | the reed frog, the mossback toad | body, throat sac and cheeks, eyes (`bead`, `lidded`), legs (`spring`, `squat`), the back's glands, moss and ferns, the tongue |
| `crab` | `mud` | the mud crab | shell (blotches, grooves, rim, brow), eye stalks, legs a side, two claws; drawn side-on (`sideways`) |
| `serpent` | `eel`, `leech` | the hollowed eel, the marsh leech | `eel`: a spine through key poses rising out of the water, fins, a loop of the back, the head and jaw, strands, the water round it, `awake`; `leech`: a ringed body along a resampled spine, the inchworm loop, the rear in an S, the sucker mouth |
| `fish` | `minnow`, `greyfin` | the hollow minnow; **new:** the greyfin | trunk, head, tail and lobes, dorsal plates, pectoral fins, eye socket, jaw, the Hollow's wake; `pool`: a puddle of its own, the fish under its surface (the greyfin) |
| `shell` | `snapper`, `beetle` | Old Snapper; **new:** the rock beetle | `snapper`: dome, rim and plastron, keels, barnacles, weed, a beaked head on its neck, pillar legs, a saw tail, the crusher; `beetle`: elytra, pronotum and underside, rocky lumps, a horned head with antennae, six jointed legs, `ball` and `spin` (it curls up and rolls) |
| `humanoid` | `puppet`, `imp` | the Trial Puppet; **new:** the pebble imp | hips, two-bone legs and arms, a trunk of three pieces, a head; joints (balls and wraps, or none), paint (`grain`, `stone`), face (`slits`, `grin`), studs and a glowing crack, a held stone, the Qi orb; `crumble`: a body of stone coming apart into a heap (`kit.collapse`) |

M1 added these variants and plans. Each new part kind is optional, so the species drawn before draw byte-identical.

| Plan | Variant (M1) | Made for | What it adds |
|---|---|---|---|
| `quadruped` | `canine` | the ember fox, the mud hound | the dogs' and cats' head kind, built once for the wolves, foxes and lynxes after: a skull on a neck, a tapering muzzle to a nose pad, a jaw that drops on its fangs and tongue, tall ears that read head-on (a short muzzle and wide ears make a cat of it), a `collar`; `digit` legs, a `brush` tail (`flame`: the fox's burning tip), a `bib` coat with dried `mud`; styles idle `alert`, `pant`, windup `crouch`, `bark`, attack `pounce_bite` |
| `quadruped` | `talpid` | the ironclaw mole | the rodent's body made plump and low: `velvet` coat, a `star` nose, no ears, `dig` legs with great iron claws, a stub tail; its tell bursts up out of its hole rearing, clods flying |
| `quadruped` | (`suid` parts) | the thornback boar | `coat` `vines` (vines and leaves winding over it), `crest` `thorns` (bristling in anger), `head.tusk`, `head.eyes` colours |
| `shell` | `tortoise` | the stone tortoise | the snapper without its crusher, saw plates or weed: a shell that is a small mountain (`crag` paint in strata, crags, a pine on the saddle, cracks as it dies); styles `rear_up`, `stomp` (a ring of dust on both sides), `withdraw_crack` |
| `crab` | (`mud` parts) | the tide crab | `claws.scale` (one great shield claw), `shell.pearls` |
| `fish` | (`minnow` parts) | the jade carp | `Z` (it rides the water line), `barbels`, gold fin tips, `eye.ring` |
| `serpent` | `viper` | the green viper | a slender snake, its hind body coiled flat, its neck raised in an S; styles `coiled`, `sidewind`, `draw_s`, `strike`, `recoil`, `go_limp` |
| `humanoid` | `monkey` | the bamboo monkey | a hunched body (`hunch`), `fur` paint, a monkey face, a curling tail, a held bamboo shoot it hurls (`shoot`) |
| `humanoid` | `guardian` | the stone guardian | a squat temple lion-dog of carved stone: `temple` paint with moss, a mane of curls, a collar and bell, jade-glowing eyes and cracks |
| `bird` (new) | `chick` | the jade crane chick | a ball of down on two long legs (two bones by IK), a neck and round head, a beak, wings that fold, spread and beat, a tail tuft; styles `peer`, `strut`, `spread_puff`, `buffet`, `ruffle`, `fold_sit` |
| `spirit` (new) | `talisman` | the paper talisman ghost | a floating body of paper strips (flat plates cut square, a column of red script down each, torn ends): a hooded dome, a dark face under it with eyes glowing violet and a talisman hanging over it (a red seal), strips hanging round it that flutter, a bundle of strips at each side that fans out like a peacock in the tell; styles `hover`, `drift`, `fan`, `fling`, `flutter_back`, `come_apart` |
| `person` (new) | `fighter`, `archer`, `brute` | the human foes | not a sculpture: the shared character body (below) |

M2 added these. Again each new part kind is optional, so every species drawn before draws byte for byte.

| Plan | Variant (M2) | Made for | What it adds |
|---|---|---|---|
| `serpent` | `dragon` | the riverbed serpent | the eel's spine made a river dragon: jade scales in arcs, a belly of gold scutes, gold spines down its back, a tail fin, horns, whiskers, a gill frill, glowing gold eyes, clear water round it; its tell gathers a water orb before its open jaws (`orb`); styles `coil_sway`, `surge`, `rear_orb`, `dragon_bite`, `toss_back`, `dive_under` |
| `serpent` | `boulder` | the boulder serpent | a thick snake under grey stone plates with a bigger head; it curls into a ball of rock (`ball`: its coils wound over a rock-painted core) and rolls; styles `rest_s`, `slither`, `curl_ball`, `boulder_roll`, `flinch_back`, `slump_crack` |
| `quadruped` | `saurian` | the rapids lizard | a saurian head, `sprawl` legs (the elbow out at the body's height, the foot further out), a `fin` crest and a finned tail, a `river` coat; its tail whip spins it round (`spin`); styles `bask`, `scurry`, `tail_curl`, `spin_whip`, `flip_over` |
| `quadruped` | `bovid` | the riverstone ox | a bovid head with horns and snorted steam, a `cracked` coat with a crest of `pebbles`, heavy `hoof` legs (`legs.thick`, `legs.bones`) |
| `quadruped` | `cervid` | the hollow stag | a cervid head with antlers, hollow eyes and mist, a `saddle` coat and `hackles`; the Hollow's look without its strands (`strands: False`) |
| `quadruped` | (`canine` parts) | the mist wolf | `opts.misty` (it comes apart into mist as it dies), a `mist` brush tail, `hackles` |
| `bird` | `vulture`, `crane`, `hawk`, `roc` | the mist vulture, the cloudwing crane, the stormwing hawk, the cloudpeak roc | flyers (`wings.seg`): jointed wings of a span, their flight feathers painted, drawn in the air over their feet (the room view's hover is a few px); styles `soar`, `flap`, `rise_fold`, `rise_coil`, `mantle`, `gather_wind`, `dive_rake`, `swoop_peck`, `lightning_dive`, `wing_gust`, `tumble_back`, `fold_fall` |
| `spirit` | `wisp`, `lantern` | the mirror wisp, the weeping lantern | `wisp`: one great eye in a ring of mirror shards that swing before it into a lens in its tell; `lantern`: a paper globe with a weeping face painted on it, lit from inside by a soul flame, a tassel under it; it flares, and beaten it bursts |
| `humanoid` | `ape` | the cliff ape | the monkey's body grown: a mane, a pale face under a heavy brow, a boulder it hoists over its head and smashes down |
| `humanoid` | `sentinel`, `gate` | the jade sentinel, the gate guardian | `armor` paint (rows of plates, a belt), a `helm` face (dome, brim, crest, mask, glowing eyes), pauldrons, tassets, gold runes, a held halberd; the gate guardian's horned crown, bronze chest plate and two jade bi rings orbiting it (`rings`) |
| `humanoid` | `chief`, `abbot`, `elder` | Big Toad Tan, the Drowned Abbot, Elder Gu | the people of size (below) |

### People (`person`, M1)

A human foe is drawn as the player and the villagers are. Its spec gives its outfit with `person(name, hair=...,
shirt=..., pants=..., shoes=..., hat=..., weapon=..., tint=...)`: the fields of a villager's `art.avatar`, kept in the
foe's row as before. `plans/person.py` maps each frame of the foe catalogue to a frame of the character's own actions
(`tools/art/topdown/figure/actions.py`):

| Foe action | Style | The character's frames |
|---|---|---|
| idle | `stand` | its breathing idle, eased over six frames |
| walk | `stride` | its walk |
| windup | `charge` (fighter) | its strike's pull-back, then the charged finisher's wind-up, held until the blow |
| | `raise` (brute) | a heavy blow's wind-up held high (the club or staff over the head) |
| | `draw` (archer) | the bow raised, the arrow nocked and drawn, held |
| attack | `strike` | its weapon family's first combo step (`weapon_families.json`, `combat_feel.json`), from the frame before its blow, so the blow is on frame 1; the brute's is the overhead `swing_3` |
| | `loose` (archer) | the drawn bow released on frame 1 |
| hurt | `flinch` | its hurt, the recoil held a frame |
| death | `fall` | its knock-down, lying still at the end |

`creatures.draw` casts that pose through the figure's own pipeline (`figure/frame.py` `cast_all`, the same layers,
palettes and stacking the player and villagers are composed from) at the figure's 46 px. A bandit is the same pixels
as a villager in the same clothes. No new body movement and no new layer pose was drawn (AGENTS.md rules 1-4). An
elite is cast at 1.2 times the figure's density (never resampled). Its clothes, hair and steel darken toward the §14
shadow as a sculpted elite's ramps do (the skin less), its eyes turn gold, and it wears the ring of Qi. A `tint`
multiplies the picture, as the side view's and the villagers' tint does (the drowned's pallor). The room view plays
the sheet like any foe's, so a person has its tell, its blow on frame 1, the hit flash and its elite look. Its label
(the block's `top`) stands over its head where a villager's marks do (`creatures.PERSON_LIFT`, 8 art px:
`TopdownPlaces.HEAD_LIFT`), not on its hair.

### The people of size (`humanoid`, M2)

A boss who is a person needs a bulk and a posture of his own that the one figure body cannot take: cast in it, Big
Toad Tan and the Drowned Abbot read as ordinary villagers. So the three bosses who are people (`chief`, `abbot`,
`elder`) are sculpted on the humanoid plan's body, as the guardians are:
- **The body first** (AGENTS.md rule 4): `opts.bare` draws the unclothed sculpture, reviewed in every action and facing
  before anything is laid over it (`docs/redesign/feedback/monsters/m2/<id>_body_x4.png`).
- **Then dressed:** `paint` kind `clothes` paints zones over the body's own parts (a sash, trousers, a vest, a kasaya,
  a collar; folds and trims). A face wears no clothes. Parts are laid over the body: a robe's skirt to the floor,
  wide sleeves, a hat, a cape. Then the props in his hands: the cleaver, the ringed staff and its bell, the tide's orb.
- **Face kind `human`:** brows, eyes (glowing for the drowned), a nose, a mouth (a toad's grin, open in a roar), ears;
  `hair` (`topknot`, `tail`, `loose`) and `beard` (`stubble`, `moustache`).

Their rows keep `art=person(...)`: the side view still dresses its avatar in it.

| Boss | Build | Tell (held) and blow |
|---|---|---|
| Big Toad Tan (`chief`) | a head and a half taller than his men and twice as broad: a great bare belly under an open leather vest, a red sash, baggy trousers wrapped at the shin, a small head with a topknot and a toad's grin, a wine gourd | the Mudwater Cleaver (nine brass rings on its spine) raised over his head in both hands as he roars; slammed down in dust (also the tell of his call for his bandits) |
| the Drowned Abbot (`abbot`) | tall, gaunt and stooped, pale with the river: a waterlogged robe with weed at its hem, a faded kasaya, long white hair under a wide straw hat that drips, prayer beads | the ringed staff raised high in his right hand, its bronze bell over his hat, his eyes glowing cold; struck down in both hands as the bell tolls rings of sound and water (also the tell of his ghosts) |
| Elder Gu (`elder`) | portly and stately: a crimson robe trimmed in gold with wide sleeves, a black sash, a dark teal cape, grey hair tied back, a drooping moustache and goatee | the river's tide gathering into an orb over his drawn-back palm; thrown as a palm strike that bursts in a crescent wave |

### Parts

A variant is a table of part parameters (`plans/<plan>.py`, `VARIANTS`). A spec lays its own over them (`parts=`),
key by key. A size that turns with the facing is written `(x, head-on, tail-on)`: `motion.headon`'s `fr` (facing the
camera) and `bk` (walking away), `x + kf·fr + kb·bk` (`kit.lin`). Materials are roles (`coat`, `pale`, `skin`,
`shell`...) that the variant maps to ramp names (`mats=`). A spec changes them to recolour a body: the hollowed
boarlet is the boarlet's body with the `h_*` ramps and `opts=dict(hollowed=True)`.

### Motion styles

Every species draws the same catalogue (`motion.py`): idle 6, walk 8, windup 4, attack 6 (the blow on frame 1),
hurt 3, death 8, and any extras (the leech's swim 8). A spec names one style for each action:

```python
motion={"idle": "sniff", "walk": "bound", "windup": "rear", "attack": "lunge_bite", "hurt": "knock_squash",
        "death": "topple_side"}
```

A style is a dict in the plan's `STYLES`:
- its tables: a tuple per channel, one value per frame (`lunge`, `pitch`, `head`, `yaw`, `gape`, `squash`, `roll`,
  `tail`...). These are the hand modules' `LUNGE`, `PITCH`, ... tables, split by action and named.
- its scalars: a loop's amplitudes and phases (`bob_amp`, `pitch_amp`...), and flags the plan's code reads
  (`reared`, `angry`, `dust`...).
- `kind`: the formula a loop runs (`bound`, `lope`, `trot`, `tripod`, `march`, `cruise`...).

Overrides go in the spec: `motion={"windup": ("rear", {"pitch": (8.0, 18.0, 30.0, 40.0)})}`. The styles each plan has
are listed in its module's docstring.

## The spec

A real one, the reed rat (`specs/lotus_ferry.py`):

```python
species("reedtail_rat", plan="quadruped.rodent", size=1.26,
        palette=["fur", "fur_light", "pink", "tail_a", "tail_b"], accents=("pink",), shadow=(10, 3), cycle=11.0, view=True,
        data=dict(level=2, role="normal", element="none", page="valley_shore", drops=[("rat_tail", 0.6)], attacks=[("bite", 0.35, 36)],
                  ai="melee", speed=120, flee=0.25, width=18, height=22, aggro=150),
        loot=dict(starter=True, finds=EARLY))
```

It takes the rodent's own parts and styles, so it needs no `parts` or `motion`. A new one, the rock beetle
(`specs/stonewall_quarry.py`):

```python
species("rock_beetle", plan="shell.beetle", size=1.6,
        palette=["beetle_rock", "beetle_pronotum", "beetle_lichen", "beetle_chitin", "beetle_horn"], accents=("beetle_horn",),
        shadow=(11, 4), cycle=9.0, view=True,
        data=dict(level=(4, 5), role="normal", element="earth", page="quarry", drops=[("beetle_shell", 0.6), ("copper_ore", 0.3)],
                  attacks=[("roll", 0.5, 40, 1.1, dict(dash=90))], ai="charger", speed=60, width=20, height=24),
        sound=dict(body="shell"))
```

| Field | What |
|---|---|
| `plan` | `"plan.variant"`; or `pose="module:function"`, the escape hatch (below) |
| `parts`, `mats`, `motion`, `opts` | laid over the variant's (`opts.hollowed`; the engine adds `seed` and `id`) |
| `size` | the species against its sculpture's art px (the people are 46 px; an elite is `ELITE` 1.2 times larger again) |
| `palette` | its ramps (`mats.RAMPS`); `accents` keep their colour on an elite, `gold` turn gold |
| `elite` | it has an elite sheet (default True). Give one to every species a room can make an elite. |
| `aura` | it wears the ring of Qi in its own look (a boss's presence) |
| `shadow`, `cycle` | the blob shadow (rx, ry art px); how far one walk cycle carries it (art px at size 1: the walk's rate) |
| `view` | its pose is told the facing's turn (head-on and tail-on poses, decision 44) |
| `sideways`, `sized`, `extra`, `awakened` | the crab's side-on stance; the eel posed at its size; actions past the catalogue; a boss's second look |
| `canvas` | (M2) the working canvas `(w, h)` a big species is drawn on, its feet at `(w // 2, h - 40)` (`creatures.foot_of`); the default is the sculpture's 136 x 124. `creatures.build` refuses a frame that runs off its canvas's top or left edge (its cell would wrap round) |
| `share` | (M1) identical frames of a facing share one cell of the sheet, and an elite's ring is lean: it flickers by its pose (`sculpt.ring_seed`), so its held poses share too, and its alphas come in steps of 32 (`sculpt._aura`'s `lean`; the ring was half an elite sheet's cost). Every M1 species has it; the species before keep their sheets byte for byte |
| `data` | the row: `level`, `role`, `element`, `page` (the codex page), `drops` (`(item, chance[, count[, weight]])`), `attacks` (`(id, windup, reach[, mult][, {extras}])`), then any `mob()` field in order |
| `loot` | `starter=True` (the first rooms' starter gear), `finds="early"` or rare rows, `quest=[...]` (drops while a quest wants them) |
| `sound` | `"race"` (default: its race's and nature's voice), or `dict(body="shell" \| "slime" \| "wood", tell="water")` |

**Order and ties.** A spec's row keeps its place among `enemies.py`'s hand rows when it is placed there with
`spec_row("id")`. Otherwise it comes after them, in spec order. Its voice keeps its place in `sound.py`'s lists when
it is named there, or comes after them. So migrating a species changes no byte of the data.

**Deterministic.** There is no randomness. A plan that varies a look by species (the beetle's flecks and lichen, the
imp's stone grain, a heap's spread) hashes `opts.seed`, which is the id's crc32. The seed is the id.

## Adding a species

1. **Pick the plan and variant** nearest the creature. Read the variant's parts in `plans/<plan>.py`.
   - If no part kind fits, add one to the plan (a head kind, a leg kind). Keep the existing kinds' code unchanged, so
     the species already drawn stay byte-identical (`--check` proves it).
2. **Add its ramps** to `mats.py`, from its side-view sheet's materials (`tools/art/creatures/<id>.py`), five steps:
   deep, shadow, base, light, highlight.
3. **Write the spec** in its region's file. If the species has a hand row in `enemies.py`, move the row into
   `data` (same values, same field order) and put `spec_row("id")` in its place. Otherwise the engine appends the row.
4. **Build:** `python3 tools/content/monsters/build.py`. It runs `build_data.py` (rows, loot, sound, the wiki) and
   `build_foes.py --jobs 2` (sheets, `foes.json`). `--update ID[,ID]` builds only those species' sheets and merges
   their blocks into `foes.json`, leaving the rest as they are (the blocks are independent; a full build gives the same
   bytes). Then let Godot import the new sheets (`godot --headless --path . --import`) and commit the `.png.import`
   files.
5. **Review by eye.** Numbers cannot certify the art (AGENTS.md rule 3). Look at every action in every facing, base
   and elite:
   - `python3 tools/content/monsters/build.py --review ID` writes `docs/redesign/feedback/monsters/sheets/<ID>_x3.png`
     (every frame, five facings, both looks) and `<ID>_se.gif` (the catalogue at the game's rates).
   - **In the game:** the capture set `monsters_e2`, `monsters_m1` or `monsters_m2` (or a set of your own beside them
     in `tools/dev/capture/shots.gd`):
     `xvfb-run -a -s "-screen 0 1280x720x24" godot --rendering-driver opengl3 --path . res://tools/dev/capture/capture.tscn -- monsters_m1`.
     It shows the lineup on the Reed Shallows beside drawn foes for scale: head-on, walking, the tell, the strike,
     struck, side-on, tail-on, falling, the elites, and a live fight. It plays on its own saves, never the Max Tester.
   - Check that the tell reads and is its own, that the blow lands on frame 1, the feet sit on the line, the head-on
     and tail-on rows read as the creature, and the elite wears its ring with gold eyes.
6. **Check:** `python3 tools/content/monsters/build.py --check` (the runners' `monsters` gate), then
   `tools/run_tests.sh`.
7. **APK size:** report the new sheets' sizes. A sheet costs about half its PNG in the APK: the imported `.ctex`
   (lossless WebP at the project's settings), which `.godot/imported/` holds after the import. An elite sheet is about
   twice its base (with `share`, about 1.8 times); leave it out where no room makes an elite.

## The escape hatch

`species("x", pose="creature.mymodule:fn", ...)` draws the species with a hand-written pose function `fn(action,
frame, **facing) -> Pose`. It takes the same keywords a plan does (`view`, `aim`, `k`, `awake`, by the art fields).
Use it when no plan draws the creature well and a new part kind would not pay for itself. The data, voice and sheet
paths are the same. `--check` proves the hatch works with a stand-in module.

## Checks (`build.py --check`, the `monsters` gate)

| Part | What it proves |
|---|---|
| specs | Every spec resolves: its plan, variant and motion styles; its palette ramps, accents and gold; its voice; a hand module loads |
| poses | Every species poses every action and frame in the five drawn facings and each of its looks; the catalogue's counts and `HIT_FRAME` are 1 |
| data | Every spec's `enemies.json` row is the row its spec makes (after `enemies.py`'s passes); its loot table has its starter mark, finds and quest drops; `sound.json` gives it its spec's voice |
| sheets | `foes.json` has every spec's block and looks, every action's frames, the blow on frame 1; the sheets are on disk; sampled frames drawn twice are identical and equal to the sheet's cell |
| elite | An elite is larger and wears the ring of Qi; its species' own look does not |
| hatch | A spec's hand module draws the species; every seed differs |

`build_foes.py --check` builds every sheet twice and fails unless both builds are byte-identical. `build_data.py
--check` fails unless every data file is what its generator writes.

## Migration (decision 45, E2)

| Species | Plan | Sheets | Data rows |
|---|---|---|---|
| mudshell_crab | `crab.mud` | identical | identical |
| reedtail_rat | `quadruped.rodent` | identical | identical |
| reed_otter | `quadruped.mustelid` | identical | identical |
| wild_boarlet | `quadruped.suid` | identical | identical |
| hollowed_boarlet | `quadruped.suid` + hollowed | identical | identical |
| reed_frog | `amphibian.frog` | identical | identical |
| mossback_toad | `amphibian.toad` | identical | identical |
| hollow_minnow | `fish.minnow` | identical | identical |
| hollowed_eel | `serpent.eel` (and its awakened look) | identical | identical |
| marsh_leech | `serpent.leech` (and its swim) | identical | identical |
| old_snapper | `shell.snapper` | identical | identical |
| trial_puppet | `humanoid.puppet` | identical | identical |

"Identical" means byte for byte: every sheet's PNG, every `foes.json` block, `enemies.json`, `loot_tables.json` and
`sound.json`. So no frame needed a reviewed diff, and no species kept a hand module. The eleven hand pose modules
(1,879 lines) are deleted.

The first new species are the three a top-down player meets first past the top-down rooms. They had side-view
stand-ins before. Each has a sheet, an elite where a room makes one, and its rows moved into its spec unchanged:
- the rock beetle and the pebble imp of Stonewall Quarry (`sq_quarry_rim`, off Stoneford's quarry road; the quest
  `stone_and_sweat`);
- the greyfin of the Grey Pools (`rm_grey_pools`, east of the Marsh Edge).

## M1: the first batch past E2

Twenty species: the foes a top-down player meets next, by chapter. They stood in with their side-view sheets before.
Each is one spec; its rows moved in unchanged (`spec_row`). `enemies.json`, `loot_tables.json` and `sound.json` are
byte-identical, and the only change to `foes.json` is the twenty new blocks. Every species before draws byte for byte.

| Species | Where it is first met | Plan | PNG KB (base / elite) | APK KB (base / elite) |
|---|---|---|---|---|
| ironclaw_mole | Stonewall Quarry: the Lower Pit, the Collapsed Tunnel | `quadruped.talpid` | 65 / 132 | 35 / 67 |
| stone_tortoise | the Lower Pit | `shell.tortoise` | 110 / 206 | 54 / 99 |
| mudwater_bandit | chapter 3: the Caravan Road | `person.fighter` | 94 / 170 | 53 / 87 |
| bandit_archer | the Mudwater Hideout | `person.archer` | 95 | 52 |
| mud_hound | the Mudwater Hideout | `quadruped.canine` | 90 | 44 |
| mudwater_lieutenant | the Loot Cave | `person.fighter` | 106 | 59 |
| big_toad_tan | the Boss Den (dungeon boss) | `person.brute` | 131 | 67 |
| jade_carp | Bend Shore | `fish.minnow` | 62 / 122 | 35 / 64 |
| tide_crab | Bend Shore (and the Rapids Terraces) | `crab.mud` | 121 / 220 | 54 / 96 |
| ember_fox | Bend Shore, the Whispering Bamboo | `quadruped.canine` | 76 | 39 |
| bamboo_monkey | chapter 4: the Whispering Bamboo | `humanoid.monkey` | 78 / 148 | 37 / 69 |
| green_viper | the Whispering Bamboo, the Thicket Heart | `serpent.viper` | 43 / 97 | 25 / 53 |
| thornback_boar | the Thicket Heart | `quadruped.suid` | 160 / 287 | 74 / 129 |
| jade_crane_chick | the Falls Pool | `bird.chick` | 69 | 34 |
| stone_guardian | Cleansing Peak: the Pilgrim Stairs | `humanoid.guardian` | 154 | 69 |
| drowned_acolyte | chapter 5: the Drowned Shrine | `person.fighter` | 102 | 54 |
| paper_talisman_ghost | the Hall of Lanterns, the Scripture Well | `spirit.talisman` | 130 | 66 |
| rogue_cultivator | the Drowned Grotto (elite) | `person.fighter` | 113 / 206 | 61 / 104 |
| drowned_abbot | the Abbot's Sanctum (dungeon boss) | `person.brute` | 121 | 62 |
| gorge_bandit_adept | Whitewater Gorge: the Gorge Mouth | `person.fighter` | 111 | 61 |

All twenty: 3,620 KB of PNG, 1,807 KB in the APK (1.76 MiB): the bases 1,038 KB, the nine elite sheets 769 KB. The
elites are where a room makes one (each of those rooms has one set-piece elite); a spec's `elite=False` and
`build.py --update ID` drop one. Each creature's size keeps it near its share of a person (46 px) in the side view.

The bosses keep their phases and tells: Big Toad Tan's raised club is the tell of his blow and of his call for his
bandits, and the Drowned Abbot's raised staff of his bell's shockwave and of his ghosts. No boss here has a second look
or wears the ring in its own look (`aura`), so their sheets stay near a person's.

Review: `docs/redesign/feedback/monsters/sheets/<id>_x3.png` and `<id>_se.gif`; the gallery in
`docs/redesign/feedback/monsters/m1/` (the twenty side by side facing SE, idle, in their tells and on their blows, and
the elites' tells beside their bases); and the capture set `monsters_m1` (`docs/redesign/feedback/monsters/m1/after/`):
the lineups held in every pose beside drawn foes for scale, the elites, and live fights in ten of the species' own
top-down rooms.

## M2: the Act I zones' foes, and the bosses of their own build

The seventeen species M1 left, in story order: the rest of the Act I zones' foes, the Trial Tower's twelve without a
sheet among them. Each is one spec; its rows moved in unchanged (`spec_row`). `enemies.json`, `loot_tables.json` and
`sound.json` are byte-identical, and `foes.json` changes only in their blocks and the two revised bosses'. Every species
before draws byte for byte. The bosses were given a silhouette and a presence of their own (bulk, posture, a signature
prop, a colour), and M1's two people-bosses were redrawn to that standard, their tells kept.

| Species | Where it is first met | Plan | PNG KB (base / elite) | APK KB (base / elite) |
|---|---|---|---|---|
| riverbed_serpent | Deepwater Bend, the Serpent's Shallows (field boss, 25) | `serpent.dragon` | 361 | 151 |
| rapids_lizard | Whitewater Gorge, the Rapids Terraces (28-31) | `quadruped.saurian` | 104 / 199 | 50 / 96 |
| boulder_serpent | the Echo Cliffs (32-35) | `serpent.boulder` | 131 / 241 | 58 / 104 |
| mist_vulture | the Echo Cliffs (34-36) | `bird.vulture` | 90 | 51 |
| riverstone_ox | the Quarry Rim (37-38) | `quadruped.bovid` | 178 | 82 |
| cloudwing_crane | the Crane Cliffs, the Cliff Faces (37-40) | `bird.crane` | 96 / 211 | 53 / 103 |
| stormwing_hawk | the Cliff Faces, the Sky Ledges (38-43) | `bird.hawk` | 49 / 109 | 29 / 58 |
| cliff_ape | the Sky Ledges (41-45) | `humanoid.ape` | 159 | 74 |
| mist_wolf | Mist Peak, the Misty Slopes (46-50) | `quadruped.canine` (misty) | 150 / 297 | 70 / 129 |
| mirror_wisp | the Misty Slopes, the Frozen Shrine (47-51) | `spirit.wisp` | 102 / 219 | 56 / 106 |
| rogue_treasure_adept | the Misty Slopes (48-50) | `person.fighter` | 89 / 163 | 49 / 82 |
| weeping_lantern | the Forgotten Monastery (50-55) | `spirit.lantern` | 81 / 175 | 46 / 86 |
| jade_sentinel | the Forgotten Monastery (52-56) | `humanoid.sentinel` | 218 | 90 |
| elder_gu | Gu's Warehouse (story boss, 53) | `humanoid.elder` | 150 | 65 |
| hollow_stag | the Summit Ridge, the Windswept Ridge (55-59) | `quadruped.cervid` | 165 / 334 | 79 / 152 |
| cloudpeak_roc | the Windswept Ridge, the Frozen Shrine (58-63) | `bird.roc` | 181 / 358 | 88 / 159 |
| gate_guardian | the Ascension Gate (story boss, 63) | `humanoid.gate` | 573 | 227 |
| big_toad_tan (redrawn) | the Boss Den (dungeon boss) | `humanoid.chief` (was `person.brute`, 131 / 67) | 216 | 95 |
| drowned_abbot (redrawn) | the Abbot's Sanctum (dungeon boss) | `humanoid.abbot` (was `person.brute`, 121 / 62) | 152 | 68 |

All nineteen: 5,549 KB of PNG, 2,557 KB in the APK (2.50 MiB): the bases 1,482 KB, the ten elite sheets 1,074 KB. Less
the two boss sheets they replace, the APK grows by 2,428 KB (2.37 MiB). Every one has `share`. An elite sheet is drawn
only where a room makes an elite (the ten above); the rest have `elite=False`. Each creature is near its side-view
sheet's share of a person (side-view px x ~0.45: a person's 46 px), so the bosses are big because their side views
are: the gate guardian stands twice a person's height, as its row's height (180 to a person's 90) does.

- **The bosses.** The riverbed serpent rears out of clear water as a jade river dragon with gold horns, whiskers and
  belly, and gathers a water orb before its jaws. The cloudpeak roc is the biggest bird, white and gold with a crest,
  gathering a storm wind under its spread wings. The gate guardian towers in jade and bronze with a horned crown, its
  two bi rings rising and spinning out to both sides in its tell. Elder Gu, the Drowned Abbot and Big Toad Tan are the
  people of size (above).
- **Big canvases.** A creature taller than the sculpture's 136 x 124 working canvas names its own (`canvas`): the
  serpent (180 x 170), Big Toad Tan (164 x 156), the roc (176 x 150) and the gate guardian (200 x 186).
  `creatures.build` raises an error when a frame runs off its canvas's top or left edge, where its cell would wrap
  round (an elite roc once did, and its sheet came out empty). Off the bottom or right edge a frame only loses its
  cell's margin there, as the hollowed eel's awakened look always has, so the sheets before stay as they were.
  `build.py --check` reads each sheet's cell against its canvas's feet.

Review: `docs/redesign/feedback/monsters/sheets/<id>_x3.png` and `<id>_se.gif`; the gallery in
`docs/redesign/feedback/monsters/m2/` (the nineteen side by side facing SE beside a Mudwater bandit, idle, in their
tells and on their blows; the elites' tells beside their bases; Tan's and the Abbot's sheets before and after; the
three people of size's bodies beside them dressed); and the capture set `monsters_m2`
(`docs/redesign/feedback/monsters/m2/after/`): the lineups held in every pose beside drawn foes for scale, the elites,
and live fights in fourteen of the species' own top-down rooms.

## Still to draw

The species the top-down rooms spawn that still stand in with their side-view sheet (R5's to R9's rooms, the Tidebreak
Front's), by level. The Trial Tower has none left.

| Species | Where | Start from |
|---|---|---|
| the_reflection | the Trial of Reflections (36) | `person` (the player's own outfit, its tint) |
| hollow_behemoth | the Siege (story boss, 58) | `humanoid.gate`'s build, `hollowed` |
| spark_weasel | the Azure Expanse: the Thunder Plains (64-66) | `quadruped.mustelid` |
| stormgrass_stag | the Stormgrass Verge, the Thunderhorn Flats (64-68) | `quadruped.cervid` |
| thunderhorn_rhino | the Lightning Scar, the Thunderhorn Flats (64-69) | `quadruped.bovid` |
| frost_lynx | Rimefrost: the Frostpine Climb, the Snow Ape Ledges (67-70) | `quadruped.canine` (a cat's head) |
| azure_carp_dragonet | Mirror Lake: the Mirror Shallows, the Reedless Shore, the Sentinel Causeway (68-72) | `fish.minnow` with the dragon's horns |
| snow_ape | the Snow Ape Ledges, the Rimefrost Summit (68-72) | `humanoid.ape` |
| thousand_eye_toad | Toad's Hollow (68) | `amphibian.toad` |
| river_sentinel | the Sentinel Causeway (70-75) | `humanoid.sentinel` |
| canyon_brigand | Gale Canyons: the Canyon Mouth, the Windbridge (73-76) | `person.fighter` |
| wind_kite | the Canyon Mouth, the Kite Winds, the Windbridge, the Riven Peak, the Starsea Crossing (73-76) | `bird.hawk` or a `spirit` of paper |
| sandstorm_scorpion | the Sunscar Desert, the Sealed Gate (73-78) | `crab.mud` (a tail kind) |
| canyon_harpy | the Harpy Roosts, the Kite Winds, the Windbridge (74-78) | `bird` flyer with a `humanoid` head |
| nine_peaks_disciple | the Sect War, the Broken Pier, the Pirate Deck (76-78) | `person.fighter` |
| dune_worm | the Worm Sea (77-81) | `serpent.boulder` (it rises out of the sand) |
| terracotta_warden | the Tomb of Sunscar (77) | `humanoid.sentinel` in terracotta |
| tomb_king | the Throne (boss, 77) | `humanoid` of size |
| starsea_pirate | Blackmast's docks, battery and cove, the Broken Pier, the Pirate Deck, the Riven Peak, the Sect War, the Starsea Crossing (79-81) | `person.fighter` |
| pirate_captain | the Sect War (story boss, 80) | `humanoid` of size |
| presence_phantom, ninth_presence | the Presence Trial (81) | `spirit`; the Ninth of size |
| comet_sparrow | the Driftglass Bank, the Sparrow Reefs, the Jellyfish Shallows, the Nest Cliffs, the Lantern Run (82-87) | `bird.hawk`, small |
| star_jellyfish | the Driftglass Bank, the Jellyfish Shallows, the Sparrow Reefs, the Lantern Run (82-87) | `spirit.lantern` (a bell trailing tendrils) |
| nest_guardian | the Nest Cliffs, the Eggshell Terraces, the Hatching Cave, the Guardian's Crown (85-93) | `quadruped` or `humanoid.sentinel` |
| pirate_gunner | the Blackmast Docks, the Gunners' Battery (85-90) | `person.archer` |
| hollow_drone | the Tidebreak Front, the Cinder Fields, the Wick Gate, the Hall of Burning Stars (88-99) | `spirit` or `bird`, `hollowed` |
| hollowed_wyrmling | the Tidebreak Front, the Eggshell Terraces, the Guardian's Crown, the Wick Gate, the Hall of Burning Stars (88-99) | `serpent.dragon`, `hollowed` |
| orbit_moth | the Orbit Ruins: the Tumbling Stair, the Orbit Garden, the Golem Foundry, the Inverted Hall (88-93) | `spirit.wisp` with a moth's wings |
| gravity_golem | the Tumbling Stair, the Golem Foundry, the Inverted Hall (88-93) | `humanoid.sentinel` of rune-cut stone |
| ashborn_raider | the Ashen Reach: the Cinder Fields, the Ashborn Palisade, the War Camp (88-93) | `person.fighter` |
| admiral_voss | the Flagship Deck (dungeon boss, 90) | `humanoid` of size |
| ashborn_pyre_keeper | the Ashborn Palisade, the War Camp (91-94) | `person`, a caster lit by embers |
| general_kharn | Kharn's Pyre (story boss, 92) | `humanoid` of size |
| nebula_eel | the Nebula Deep: the Nebula Verge, the Eel Currents, the Crab Grottoes (94-97) | `serpent` (the hollowed eel's build) |
| void_crab | the Nebula Verge, the Crab Grottoes (94-98) | `crab.mud` |
| nebula_leviathan | the Leviathan's Maw (boss, 99) | `serpent.dragon` of size |
