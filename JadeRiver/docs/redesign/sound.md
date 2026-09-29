# The sound pass (decision 43)

The user's pick from the suggestions list after build 109: "layered hits, footsteps by surface, ambient beds, combat
music that comes in with a fight, and stingers", with a mix under them. Every sound is still synthesized in code
(`tools/audio/`, numpy, seeded: the same build writes the same bytes) and original: no samples, no recordings.

- The synthesis: `tools/audio/sfx_pass.py` (hits, whooshes, casts, steps, landings, foes, the world, stingers),
  `tools/audio/beds.py` (the ambient beds), `tools/audio/music_adaptive.py` (the combat stems and the two boss themes),
  built with the rest by `tools/audio/build_audio.py`.
- The tables: `tools/data/sound.py` writes `data/sound.json` (which sound plays when, and the mix).
- The runtime: the `Audio` autoload (`scripts/audio/audio_director.gd`), `SoundBank` (the lookups) and `TopdownSound`
  (the feet, the listener and the hour in a room on the grid).
- The checks: `tools/audio/build_audio.py --check` (levels, seams, the phone band) and the `audio_tests` suite.
- The review: `tools/audio/review.py` (waveform and spectrogram PNGs, a loudness table), its pictures in
  `docs/redesign/feedback/sound/`.

## 1. The audit: what the top-down prototype played before

Every call to `Audio` in the prototype's code and data at build 109, and when it played.

| When | What played | Where |
|---|---|---|
| a jump | `jump` (one whoosh) | `topdown_world.gd` `_feedback` |
| a dash, the Plunge | `dodge` | same |
| a landing | `land` for a fall over 12 units, one sound on every floor; the Plunge `rumble` | same |
| a fall into water | `water_step` | same |
| a basic attack | `swing`: one whoosh for every weapon (a bow's shot included) | `_on_event` `attack_started` |
| a technique | `technique`: one chime run for every element | same |
| a foe's wind-up | `tell`: one wooden tick, the same for a crab and a bandit, at full level wherever it stood | same |
| a blow landed | `hit`, `hit_crit` or `hurt`: one sound for every weapon and every body | `combat_fx.gd` |
| a foe falling | `enemy_die`: one sound for every foe | `audio_director.gd` |
| a parry | `parry` | `world_shared.gd` |
| any way out (a hut's door, a path's edge, an array) | `portal` | `audio_director.gd` `EVENT_SFX` |
| loot picked up, a node gathered | `coin`, `pickup` | `world_shared.gd` |
| hazards, arts, treasures, talismans, arrays | `gust`, `surge`, `frost`, `hiss`, `rockfall`, `thunder`, `forge`, `break`, `technique`, `bell`... | `world_shared.gd`, `hazard_view.gd` |
| moments (a level, a breakthrough, a boss, a rare drop, an elite) | `level`, `breakthrough`, `brush_stroke`, `seal_press`, `unlock`, `gong_short`, `bell`, `rare_chime`, `boss_sting`, `boss_roar`, `boss_fall` | `data/moments.json` |
| quests, mail, meditation, crafts, shops | `quest_accept`, `quest_complete` (twice on a hand-in's button), `mail`, `meditate`, `forge`, `coin` | `EVENT_SFX`, the pages |
| the interface | `ui_tap` on every press (tabs too), `ui_open`, `ui_close`, `error`; `ui_confirm` was asked for and did not exist | `page.gd`, `hud.gd` |
| music | the room's mood, one track, a 1 s crossfade on a room change | `audio_director.gd` |
| ambience | three 6 s loops (water, wind, crowd) for nine moods; 76 of the 168 rooms had none; no day or night | same |

The mix: four buses and their sliders, no Master slider, no limiter; ten SFX players, the first free one taken and an
eleventh sound dropped whatever it was; ±5 % pitch on everything; nothing quieter with distance; nothing ducked.

**The gaps found.**

- **Feet:** walking and sprinting were silent. Landings had one sound for grass and roof tiles alike, and a drop of
  under 12 units none. Wading was silent.
- **Hits:** one hit for a jian, a heavy sabre and a bell, on a crab or a boar; nothing tied to the hit-stop; nothing
  for the chain's last blow, a finisher or a weave cancel. One whoosh for every weapon.
- **Techniques:** one sound for fire, water, thunder and the rest.
- **Foes:** one tell and one death for every kind; tells at full level across the room; fifteen foes filled the ten
  players and a blow of the player's own could find none free.
- **The world:** a hut's door sounded like a transfer array; loot hitting the ground was silent; a talk opening, its
  lines, barks and a staged scene's letterbox were silent.
- **Beds:** six-second loops (the repetition is plain within a minute), no hour, most rooms silent.
- **Music:** nothing changed when a fight started; Old Snapper and the Hollowed Eel played their room's tune; the
  stingers were few (`rare_chime`, `boss_sting`, `unlock`).
- **The mix:** no limiter, no voice priorities; `boss_sting` lived almost wholly under 100 Hz (-23 dB above 300 Hz,
  which a phone speaker barely plays).

## 2. Layered hits

A blow is three sounds the director plays as one (`AudioDirector.hit`, from the `hit_landed` payload):

1. **the transient** of the attacker's weapon family, 60-200 ms: `hit_<family>_a|b`;
2. **the body** of what is struck, 100-350 ms: `hit_on_<material>_a|b`;
3. **the tail** of the family, played the moment the hit-stop lets go (`CombatFeel.hitstop_s` for the blow's weight,
   0 under Reduce motion): `hit_tail_<family>`.

| Sound family | Weapon families (weapon_families.json) | Transient | Tail |
|---|---|---|---|
| sword | jian, short blade | a slice of air and a short high steel kiss | the blade ringing, the air closing |
| sabre | heavy sabre | a heavy chop: a saturated thud with a darker clang | a low follow-through whoosh and a low metal hum |
| spear | spear, staff | the point's hard "tchk" and the shaft's wooden knock | the shaft buzzing |
| fan | fan | a papery double slap and a bamboo rib's tick | a silk flutter |
| brush | brush | a wet ink flick with droplets | a spatter of drops |
| flute | flute | a hollow bamboo tok and a short high note | a breathy xiao note fading (the qi's resonance) |
| bell | bell | a bronze clang | the bell humming out |
| bow | bow | the arrow's thwack, its shaft buzzing | the fletching whirring |
| fists | fists, gauntlets | a dull punch with a skin slap | a puff of displaced air |

| Material | Foes (data/sound.json `foes`) | Body |
|---|---|---|
| flesh | beasts, people, the Ashborn | a soft saturated thud and a wet smack |
| shell | crabs, tortoises, beetles, moles, scorpions, Old Snapper, stone imps | a hard click-crack, chips flying |
| wood | puppets, constructs, paper ghosts, lanterns | a hollow knock that rattles twice |
| slime | leeches, frogs, fish, eels, jellyfish, the Hollow | a wet splat and bubbles |

A technique's blow sounds its element (`hit_el_<element>`: qi, fire, water, wind, thunder, earth, metal, wood,
soul, space, time) over the body, and its cast `cast_<element>` when it starts. The accents: a crit or a finisher
rings `hit_accent_crit` (a deep saturated boom under a bright double ring); the family's last combo step
`hit_accent_chain` (a rising qi zing landing on a small cymbal flick); a weave cancel (`attack_cancelled` with an
`into`) `hit_accent_weave` (a quick flick of air and a tick).

**Varied:** two round-robin takes of each transient and body, each layer ±3.5 % in pitch and ±1.5 dB, the blow's
weight moving the whole hit (light 3 dB quieter and 4 % higher, a finisher 1 dB louder and 8 % lower). Blows landing
within 35 ms (one swing through a crowd) sound as the first. A foe's blow on the player plays its race's family (a
beast's claws as fists, a bandit's blade as a sword) over `hurt`.

**Whiffs:** each family's own swing (`swing_<family>`): the sword's thin fast whoosh, the sabre's heavy low one, the
spear's short thrust, the fan's fluttering sweep, the brush's soft swish with bristles, the flute's whoosh with a
breath of a dizi note, the bell's swing with a faint jingle, the bow's string twang and the arrow leaving, the fist's
short punch. The chain's steps are pitched apart (1.0, 1.05, 0.95; a finisher 0.9).

## 3. Footsteps by surface

`TopdownSound` reads the floor under the feet from the room's own data (`SoundBank.surface_at`): a prop's top the
body stands on (a house's or hall's roof tiles, crates' planks), water (level -1: wading), else the cell's paint mark.

| Mark (proto_tileset.json) | Surface | Steps |
|---|---|---|
| `g`, `f`, `b` grass | grass | a swishy crunch of blades |
| `d` dirt path | dirt | a soft scuff with a little grit |
| `p` paving, `s` stone, `r` rock, `l` wall top | stone | a heel's click and ring, the toe's scrape |
| `w` wood | wood (planks) | a hollow knock, now and then a creak |
| `m` marsh | reeds | a wet squelch in rustling reeds |
| `t` roof | roof | a ceramic clack of tiles |
| water (level -1) | water | a shallow splash with bubbles |
| (none yet) `a`, `n` | sand, snow | a dry hiss-crunch; a squeaky crunch (ready for their tiles) |

Four takes of each; a step's round robin never repeats the last. **Timed to the frames:** a step plays on the frame
of the walk or run cycle where a foot lands (`steps.contacts`: a fraction of the cycle, 0 and 0.5, the stride's ends
in `tools/art/topdown/figure/actions.py`; frames 0 and 4 of eight, so a cycle redrawn with more frames keeps them).
The run's steps are 4 dB louder and 6 % brighter than the walk's. **Landings** by surface (both feet 22 ms apart),
silent under a 6-unit hop, rising from -8 dB to +2 dB with the height fallen, the body's weight (`land_heavy`, a
thump and the robe settling) over them from 40 units; a fall into water splashes (`splash`).

**Others' feet:** a foe that walks steps at the halves of its sheet's walk cycle (by its named `walk` action, not its
frame numbers, so the monsters' new frames keep it; a cadence of 0.34 s without one), 7 dB under the player's, a
villager a route walks on its walk's contact frames, 9 dB under; both where they stand, falling off with distance
(0 dB within 96 units, -24 dB at 900, silent past it). Only the six nearest walking foes step aloud (a crowd's feet
are a blur, and the voices are the fight's); nothing that flies or hovers steps. A step still lands when a slow
frame skips past its contact frame.

## 4. Ambient beds

Each place has a bed (`data/sound.json` `beds`): one or two base loops and the layers the hour adds. The bases are
16 s, the layers 18 s (birds), 14 s (insects) and 20 s (frogs), each started at its own random point, so a base and
its layer line up the same way only after minutes.

| Bed | Base | By day | By night |
|---|---|---|---|
| river | a broad soft rush, babbling over stones, a deeper plop now and then | birds | frogs |
| river village (Lotus Ferry) | the river, a town's murmur 7 dB under it | birds | frogs (the murmur 3 dB lower) |
| marsh | still water lapping, reeds hissing in the gusts, drips, a warbler far off | birds | frogs |
| bamboo | the grove's hush, dry leaves in gusts, stems knocking hollow, a creak | birds | insects |
| pines | a long sighing roar with the needles hissing on top | birds | insects |
| field | a light breeze and the grass stirring | birds | insects |
| town | a murmur of voices, a vendor's clapper, wood being chopped, a cart creaking past, a far hand-bell | | insects (the town 9 dB quieter) |
| sect | a hushed breeze, wind chimes under the eaves, one temple bell far up the mountain | birds | insects |
| sect on the heights | the sect's courtyard with the pines' wind | birds | insects |
| cave | drops into still pools, a low hollow air, a trickle further in | | |
| indoors | a room's quiet, a hearth's small crackle, a beam settling once | | |

A room's bed: by its id (`beds.rooms`: Lotus Ferry's village, huts and boat, the marsh, the sects' halls and peaks),
else its ambience mood (the rooms' `ambience`), its type, its id's area prefix, else the field. Kept in
`tools/data/sound.py`, not `topdown_rooms.py`, so the living world's edits there never meet it. **Crossfaded** over
2 s on a room change. **The hour:** in a room on the grid the bed follows the light the eye sees (`TopdownLight.look`:
morning and day bring the birds, evening fades them under the first insects, night and the Hollow Night bring the
insects or frogs; a lamplit interior has neither); in the side view the clock's `time_of_day`.

## 5. Adaptive music

- **The exploration layer** is the room's track, as before (its mood through `music.alias`).
- **The combat stem.** Village by day, village by night, the field, the river and the sect each have a stem
  (`<track>_combat`) built on the track's own grid (the same tempo, metre, bars, loop length, key and chord roots):
  war drums, a pipa ostinato on the chord roots, tremolo swells at the phrase ends, cymbals on the phrase starts. It
  starts with its track, silent, in the same mix, so the two stay in step. **It comes in** when a foe near the player
  (within 560 units; a boss anywhere in the room) is hostile, awake and out of its calm states (`idle`, `patrol`,
  `return`, ...): on the track's next beat, over two beats, the tune 2 dB under it. **It leaves** 4 s after the last
  fighting foe falls or gives up, on the next bar line, over one bar. A track with no stem crossfades on the beat to
  the battle theme and back instead.
- **Boss themes.** Old Snapper (`boss_snapper`, 96 bpm 4/4, 40 s): heavy four-square drums that lumber, the jaw's
  clack in the woodblocks, a low pipa tremolo circling A, a reed drone, a dark xiao, splashes. The Hollowed Eel of the
  Hollow Night (`boss_eel`, 132 bpm 6/8, 43.6 s): toms rolling in waves, a guzheng rippling over a beating drone with
  a flat second, a xiao that sinks at its phrase ends, drops of water, a bowed gong swelling every four bars. Other
  bosses play `boss`. A boss's theme comes in on the beat over whatever plays and hands back when it falls.
- **Stingers** (on the Music bus; the music ducks 10 dB under them; one at a time, a lesser one waiting for a greater):

| Stinger | When | What it is |
|---|---|---|
| `sting_quest` | a quest completed | a guzheng figure rising to the tonic, a small bell, a soft drum |
| `sting_breakthrough` | a major breakthrough (a new realm) | a gong swells, a dizi climbs the scale, chimes cascade, the drum answers |
| `sting_rare` | a rare find, a first weapon | a guzheng sweep up the strings into three bright bells and a shimmer |
| `sting_unlock` | a system unlocked | two bianzhong bells a fifth apart over a plucked tonic |
| `sting_elite` | an elite appears | two war-drum strokes, a low pipa tremolo on a clashing second, a falling flute bend |
| `sting_victory` | a boss falls; a fight that felled an elite ends | the drums call (da-da-DUM), a bright guzheng cadence home, a cymbal and a bell |

## 6. The mix

- **Buses:** Master, Music, Ambience, SFX, UI, each driven by its Settings slider; a new **All sound** slider drives
  Master (`master`, default 1.0). On Master a 45 Hz high-pass (nothing a phone plays lives under it) and a hard
  limiter at -0.5 dBFS.
- **Levels by loudness.** Each new sound's level (`data/audio.json` `volume_db`) is set by the builder from its
  loudness (the loudest 400 ms of a one-shot, the integrated loudness of a loop; `build_audio.py` `VOLUME`), not its
  peak, so a tick and a roar of one category sound alike: the hit's transient at -24 LUFS, its body -25, its tail -30,
  steps -30, swings -27, casts -23, tells and deaths -25, stingers -18, the beds -29 (their layers -34 to -35).
- **Ducking:** the music dips 10 dB under a stinger, 6 dB while a talk is open, 4 dB under a bark or a staged scene;
  the beds half as much; 80 ms down, 0.9 s back.
- **Voices:** 24 players for the SFX and the world, 6 for the interface. Each sound's rule (`mix.voices.rules`) gives
  its priority, how many of it may sound at once and the least gap between two of its starts (a step 5 at once 40 ms
  apart, a transient 4 at 25 ms, a tell 3 at 80 ms...); the player's own sounds rank 20 higher. A new sound takes a free
  player, else steals the quietest, oldest one of a lower priority, else is dropped. In the fifteen-monster fight the
  pool peaks at about half full with nothing over its cap (`audio_tests`).
- **Phones:** every new sound keeps at least a sixteenth of its energy (-12 dB) above 300 Hz; the builder fails one
  that does not. The low thumps are saturated so their weight carries in harmonics. `boss_sting` was fixed the same
  way (-22.9 dB to -11.1 dB).

## 7. For the other passes

- A critter, a worker's hammer, a mill: `Audio.world_sound(id, at, gain_db)` plays any sound at a place (world units),
  falling off with distance, a little under the fight in the voice pool.
- A villager's or a critter's step: `Audio.step_at(surface, at, "npc")`; `SoundBank.surface_at(room, at)` gives the
  surface.
- A foe's new tell or death frames: the tell plays on the named `attack_started` wind-up and the death on
  `actor_defeated`, the foe's walk steps on its sheet's named `walk` action; none keys on a frame number.
- A new sound: a function in `tools/audio/sfx_pass.py` (or `beds.py`, `music_adaptive.py`), a `VOLUME` prefix in
  `build_audio.py` if it is a new category, a row in `tools/data/sound.py` if the game should pick it, then
  `python3 tools/audio/build_audio.py <id>` and `python3 tools/data/build_data.py sound`.

## 8. The review

Nobody can listen during the build, so the pass was checked by analysis (`tools/audio/review_pass.sh BEFORE`, which
runs `tools/audio/review.py` over a copy of `art/audio` from before the pass). Every picture shows a sound at its
level as the game plays it (its `volume_db`, a layer's mix level), before the bus: the title, the waveform (peak dim,
RMS bright, the 0 and -3 dBFS lines), the spectrogram (40 Hz to 11 kHz, log), and for a loop the seam (its last and
first quarter second, the red line where it joins).

- **Before | after pairs** (`docs/redesign/feedback/sound/before_after/`): the hit as a sword on flesh, a sabre on a
  shell, fists on flesh, a spear on wood, a brush on slime and a sword's crit; the swing of the sword, the sabre and
  the bow; the tell (a beast's); a death (a shell's); a landing on stone; wading; the river, bamboo and town beds
  against the old 6 s loops; the field's track with its stem coming in against the old battle theme; the eel's theme
  against the old boss theme; `boss_sting` before and after its phone fix.
- **The new sounds** (`docs/redesign/feedback/sound/new/`): `steps.png` (eight surfaces at the sprint's cadence,
  landings, the splash), `hits.png` (more families and bodies, the chain's and the weave's accents, element hits),
  `casts.png` (the eleven elements), `foes.png` (the tells and deaths), `world.png` (doors, loot, the interface, talk,
  barks, the scene cue), `stingers.png`, `beds.png` (every bed and layer; the river and the marsh at night),
  `music.png` (the five stems, the two boss themes, the village at night and the river with their stems coming in).
- **Tables:** `docs/redesign/feedback/sound/table_before_after.md` and `table_new.md` (length, peak, RMS, integrated
  and momentary loudness, the phone band, clipped samples, the loop seam of every sound pictured).

**Loudness, as played** (the momentary maximum of a one-shot, LUFS, before the bus):

| | before | after |
|---|---:|---:|
| a hit | -24.9 (`hit`, every weapon) | -22.4 to -24.9 (a sword on flesh -23.6, a sabre on a shell -24.0, fists on flesh -23.4, a spear on wood -24.9, a brush on slime -22.6) |
| a crit | -24.0 | -22.4 (the sword's, its accent over it) |
| a swing | -21.2 (louder than the hit it led to) | -24.8 to -25.2 (just under the hit) |
| a tell | -28.2 (a tick) | -24.8 (a beast's growl and the tick; less with distance) |
| a death | -20.6 | -22.9 (a shell's) |
| a landing | -27.5 | -26.9 (on stone) |
| wading | -29.3 (one `water_step`) | -27.0 (the sprint's four splashes) |

No sound clips: every file's peak is at -3 dBFS before its level (the loops' at -1 dBFS after the limiter and within
0.6 dB of it once decoded), no composite pictured passes -0.9 dBFS before the bus, and the Master limiter holds
-0.5 dBFS whatever sums. The phone band: every new sound keeps -12 dB or more above 300 Hz (the lowest, `land_heavy`
-9.6, `hit_el_earth` -10.3, the stems -6 to -9); `boss_sting` went from -22.9 to -11.1.

**Loop seams** (`build_audio.py --check`, on the decoded Vorbis the game plays): every loop's jump across its seam is
under the 99.9th percentile of its own sample-to-sample steps (the music from 0.0000 to 0.063 against 0.063 to 0.34;
the beds from 0.0013 to 0.097 against 0.10 to 0.53), and its level across the seam steps by under 6 dB for the music
(the 15 ms before its first downbeat) and 16 dB for a sparse bed layer (a bird call can sit on one side). Each stem is
sample for sample as long as its track (the builder fails a drift).

**Size** (`tools/audio/apk_size.py` after `godot --headless --import`):

| | before | after |
|---|---:|---:|
| in the APK | 8.38 MB, 76 files (all QOA) | 7.04 MB, 233 files |
| &nbsp;&nbsp;music | 7.3 MB, 22 loops | 5.22 MB, 29 loops (22 tracks, 5 stems, 2 boss themes; Vorbis q0.15, about 32 kbps) |
| &nbsp;&nbsp;beds | 0.16 MB, 3 loops of 6 s | 0.89 MB, 12 loops of 14-20 s (Vorbis q0.1) |
| &nbsp;&nbsp;one-shots | 0.9 MB, 51 | 0.93 MB, 192 (QOA; silent tails trimmed at -60 dB) |
| sources in the repository | 41.3 MB of WAVs | 9.8 MB |

The loops went to Ogg Vorbis (`soundfile`/libsndfile; each stream's serial number is set from its id so a build
writes the same bytes), the one-shots stay WAVs Godot packs as QOA (instant to start, no decoding).

## 9. A listening guide

Where to hear the pass on the phone, and what to listen for.

- **Out of the Fisher's Hut into Lotus Ferry** (a top-down character's start): the hut's door opens (a latch, a creak,
  the air moving) and thuds shut behind you; outside the river's soft rush and babble with the village murmuring under it and birds by day,
  frogs at night. Sprint: your steps change as the ground does, a hollow knock on the jetty's planks, a soft scuff on
  the lane, a swishy crunch in the grass, a splash wading; walk (a light touch) and they soften. Jump off a roof: two
  feet land, and from a height a thump of the body.
- **Crab Trouble in the reed shallows:** the marsh's lapping and hissing reeds under the river tune; when the crabs
  turn on you the tune gains war drums and a driving pipa on its next beat (the tune dips a little under them); your jian's cut is a thin slice and a steel kiss, the crab's shell
  a hard click-crack with chips, and a beat later (as the freeze lets go) the blade rings. The crabs' wind-ups gurgle
  with the wooden tick you know; the third blow of your chain rings a little zing, a crit a deep boom under a bright
  double ring. A crab dies in a crack and a clatter. Four seconds after the last one, on a bar line, the drums leave.
- **Other weapons:** the heavy sabre chops dark and heavy with a low whoosh after; the spear clicks and its shaft
  buzzes; the fan slaps like paper; the brush flicks ink; the flute taps and breathes a note; the bell clangs and hums;
  the bow twangs and the arrow thwacks; fists punch dull with a puff of air. A technique sounds its element as it is
  cast (fire roars and crackles, water swirls and bubbles, thunder crackles to a snap, earth rumbles, metal rings).
- **The Hollow Night:** the night village with the river and frogs; the minnows bring the night tune's drums; when the
  Hollowed Eel rises its own theme comes in on the beat, a rolling 6/8 with a sinking xiao and water dripping; when it
  falls, the victory stinger (da-da-DUM and a bright guzheng cadence home).
- **Old Snapper in the reed shallows:** when the old turtle joins the fight its own theme comes in on the beat,
  lumbering heavy drums with the clack of its jaw in the woodblocks; a hit on its shell cracks rather than thuds.
- **The Marsh Edge:** the marsh bed (lapping, reeds hissing in the gusts, a warbler far off); wet squelching steps in
  the marsh grass.
- **The sects:** a hushed courtyard with wind chimes and a temple bell far up the mountain; on the Cloud sect's cliffs
  the pines' long sigh under it.
- **Stingers:** hand in a quest (a guzheng figure rising home), reach a new realm (a gong swells, a dizi climbs, chimes
  cascade), a rare drop (a sweep up the strings into bright bells), a system unlocked (two bronze bells), an elite
  appearing (war drums and a clashing tremolo). The music ducks under each.
- **Talk:** a talk opens with a scroll unrolled, each next line a soft high pluck, and the music dips while it is open;
  a villager's bark over their head pips where they stand.
- **Settings, Audio:** All sound over Music, Ambience, Effects and Interface.
