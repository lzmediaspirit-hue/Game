# Jade River audio synthesizer

Deterministic numpy synthesis of every music loop and sound effect. There are no
samples or recordings: plucked strings, flutes, percussion and textures are all
generated from code, so rebuilding gives byte-identical files.

```
tools/audio/
  build_audio.py   CLI: render, write the files + manifest, check levels/seams/phone band, review PNGs
  synth.py         DSP toolkit (filters, Karplus-Strong, flute, modal percussion, textures, reverb)
  music.py         22 music loops (@music(id)), pentatonic melody generator, Track mixer
  music_adaptive.py  decision 43: a combat stem for 5 tracks (on each track's own grid), 2 boss themes
  sfx.py           the first 51 sound effects (@sfx(id)) and the helpers the others share
  sfx_pass.py      decision 43: 141 more: layered hits, whooshes, casts, steps and landings, foes, the world, stingers
  beds.py          decision 43: the ambient beds (16 s bases, 14-20 s layers of the hour)
  life.py          decision 44: the living world's 38: critters, the villagers' work (with takes), using a place
  review.py        waveform/spectrogram PNGs, before|after pairs, a loudness table (BS.1770-like LUFS)
  review_pass.sh   the sound pass's review pictures and tables (docs/redesign/feedback/sound/)
  review_life.sh   decision 44's review pictures and table (docs/redesign/feedback/sound/life/)
  apk_size.py      what the audio weighs in the APK (the imported files), after a Godot import
art/audio/music/<id>.ogg   Ogg Vorbis, mono, 22050 Hz, 32-48 s loops (q0.15, about 32 kbps)
art/audio/sfx/<id>.wav     16-bit PCM mono 22050 Hz one-shots (Godot packs them as QOA), peaks at -3 dBFS
art/audio/sfx/bed_*.ogg    the ambient beds, Ogg Vorbis (q0.1)
data/audio.json            manifest: each id's file, level (volume_db), length; a track's grid and stem
```

Requirements: Python 3.10+, numpy; soundfile (libsndfile) for the Ogg loops (without it the loops are written as
WAVs); Pillow only for `--review` and review.py.

```bash
python3 tools/audio/build_audio.py                  # build everything (~100 s on 3 cores)
python3 tools/audio/build_audio.py title coin       # rebuild some ids (the manifest keeps the others' entries)
python3 tools/audio/build_audio.py 'hit_*' 'bed_*'  # ids may be patterns
python3 tools/audio/build_audio.py -v               # + A-weighted level of each mixer bus
python3 tools/audio/build_audio.py --review DIR     # + spectrogram PNG per track, SFX contact sheet
python3 tools/audio/build_audio.py --check          # only verify the files on disk (tools/run_tests.sh runs it)
python3 tools/audio/review.py --out DIR --table hit:sword:flesh step:grass bed:river:night
python3 tools/audio/apk_size.py -v
```

The report shows the length, peak, RMS, phone band and loop-seam step of each file. The build exits with status 1 on
NaN, clipping, a seam jump, a non-zero start/end on a one-shot, a music length outside 32-48 s, an SFX peak other
than -3 dBFS, a combat stem that is not as long as its track, or a new sound whose energy lives under 300 Hz (less
than -12 dB above it: a phone speaker would barely play it). A full build removes the files of ids no longer built.

## How it works

- **Style**: pentatonic scales (gong-shang-jue-zhi-yu) in different modes and keys per
  track. Melodies come from seeded random walks shaped into A A' B A'' phrases, so they
  are original. Instruments: guzheng and pipa (Karplus-Strong strings solved in the
  frequency domain, so tuning is exact; they get an attack pitch settle, press bends,
  "yin" vibrato and body resonance EQ), pipa tremolo (one string re-excited about 15 times
  a second), dizi and xiao (additive tone, vibrato, grace notes, breath noise, membrane
  buzz), drones, muyu and bamboo blocks, drums, cymbals, gongs, bells, singing bowls, wind,
  water, crickets and birds.
- **Seamless loops**: notes are wrap-added into a buffer exactly one loop long, so their
  tails ring into the start. Drones use whole cycles per loop, noise is generated
  periodically in the FFT domain, and bus EQ, time-varying filters and reverb are
  applied circularly. Every note is placed 25 ms after the loop point, so the seam falls
  between attacks. The engine sets the loop mode (`scripts/audio/audio_director.gd`). The seam is checked on the
  decoded Vorbis, which is what the game plays.
- **Levels**: music is normalised to -18 dBFS RMS with at most 4 dB of transparent peak
  limiting (ceiling -1 dBFS); a combat stem to -20. SFX and ambience loops peak at -3 dBFS. The pass's sounds are then
  levelled by loudness (`VOLUME` in build_audio.py: a one-shot's loudest 400 ms, a loop's integrated loudness, against
  a target per category), written as each id's `volume_db`.
- **Determinism**: all randomness comes from `rng_for(...)`, which is seeded from the asset
  id and part name (`BASE_SEED` in synth.py re-rolls everything). The output is
  byte-identical for the same numpy and libsndfile versions and platform, including parallel builds; each Ogg
  stream's serial number (random in libsndfile) is set from its id and its pages' checksums redone.

## Decision 43: the sound pass

`docs/redesign/sound.md` holds the audit, the design, the review and a listening guide. In short:

- **Layered hits** (`sfx_pass.py`): `hit_<family>_a|b` (the weapon's transient: sword, sabre, spear, fan, brush,
  flute, bell, bow, fists), `hit_on_<material>_a|b` (flesh, shell, wood, slime), `hit_tail_<family>` (after the
  hit-stop), `hit_accent_crit|chain|weave`, `hit_el_<element>`; `swing_<family>`, `cast_<element>`.
- **Feet**: `step_<surface>_a..d` and `land_<surface>` for grass, dirt, stone, wood, sand, water, reeds, roof, snow;
  `land_heavy`, `splash`.
- **Foes**: `tell_<race>` (beast, human, construct, spirit, water), `die_<body>` (flesh, shell, wood, slime, spirit).
- **The world**: `door_open`, `door_close`, `loot_drop`, `ui_confirm`, `ui_tab`, `talk_open`, `talk_next`, `bark`,
  `scene_in`; stingers `sting_quest|breakthrough|rare|unlock|elite|victory`.
- **Beds** (`beds.py`): `bed_river|marsh|bamboo|pines|field|town|sect|cave|interior`, layers `bed_birds|insects|frogs`.
- **Music** (`music_adaptive.py`): `<track>_combat` for village_day, village_night, field, river and sect (the grid of
  each is listed in STEMS and must match its track's `Track(...)`), `boss_snapper`, `boss_eel`.

Which sound plays when is data: `tools/data/sound.py` (data/sound.json).

## Decision 44: the living world

`life.py` (docs/redesign/sound.md §10): the critters TopdownLife raises, `life_sparrow_flee|fish_flee|frog_leap|
frog_plop|hen_flap|cat_wake|dog_bark`; each work cue of data/topdown/life.json as `life_work_<cue>` (sweep, set_down,
scrub, hang, pick, stir, grind, chop, hammer, stoke, fish, recast, mend, look, write, breathe) and the blows
`life_work_chop_hit`, `life_work_hammer_hit`; a place used, `place_open|tend|sit`. Where one repeats there are takes
(`<id>_b`, `<id>_c`: the sweep, the chop and its blow, the hammer and its blow, the washing, the dog), played in turn.
They are levelled as ambience (`VOLUME`: -30 LUFS for a blow down to -41 for a breath, against the fight's -25).
`python3 tools/data/sound.py --check` fails when a cue the code or the data can raise has no sound here.

## Adding or changing a sound

Add a function decorated with `@music("id")` in music.py (build a `Track`, add buses,
place notes, `return tr.mix(...)`), or with `@sfx("id")` in sfx.py or sfx_pass.py (return a float
array; `loop=True` returns exactly one period). Give a new category a `VOLUME` target in build_audio.py, and name
the sound in tools/data/sound.py if the game should pick it. Then run the build, and
`python3 tools/data/build_data.py sound`. Run with `-v` and `--review` (or review.py) to check the balance and the
spectrogram, because nobody listens as part of the build; `godot --headless --import` makes the new files' `.import`.
