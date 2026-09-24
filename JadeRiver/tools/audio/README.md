# Jade River audio synthesizer

Deterministic numpy synthesis of every music loop and sound effect. There are no
samples or recordings: plucked strings, flutes, percussion and textures are all
generated from code, so rebuilding gives byte-identical files.

```
tools/audio/
  build_audio.py   CLI: render, write WAVs + manifest, check levels/seams, review PNGs
  synth.py         DSP toolkit (filters, Karplus-Strong, flute, modal percussion, textures, reverb)
  music.py         12 music loops (@music(id)), pentatonic melody generator, Track mixer
  sfx.py           39 sound effects (@sfx(id)), including 3 seamless 6 s ambience loops
art/audio/music/<id>.wav   16-bit PCM, mono, 22050 Hz, 36-40 s loops
art/audio/sfx/<id>.wav     same format, peaks at -3 dBFS
data/audio.json            manifest (sorted keys, indent 1; an existing "rooms" map is kept)
```

Requirements: Python 3.10+, numpy. Pillow only for `--review`.

```bash
python3 tools/audio/build_audio.py                  # build everything (~15 s on 4 cores)
python3 tools/audio/build_audio.py title coin       # rebuild some ids (manifest still lists all)
python3 tools/audio/build_audio.py -v               # + A-weighted level of each mixer bus
python3 tools/audio/build_audio.py --review DIR     # + spectrogram PNG per track, SFX contact sheet
python3 tools/audio/build_audio.py --check          # only verify the WAVs on disk
```

The report shows the length, peak, RMS and loop-seam step of each file. The build exits
with status 1 on NaN, clipping, a seam jump, a non-zero start/end on a one-shot, a music
length outside 32-48 s, or an SFX peak other than -3 dBFS.

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
  between attacks. The engine sets the loop mode (`scripts/audio/audio_director.gd`).
- **Levels**: music is normalised to -18 dBFS RMS with at most 4 dB of transparent peak
  limiting (ceiling -1 dBFS). SFX and ambience loops peak at -3 dBFS.
- **Determinism**: all randomness comes from `rng_for(...)`, which is seeded from the asset
  id and part name (`BASE_SEED` in synth.py re-rolls everything). The output is
  byte-identical for the same numpy version and platform, including parallel builds.

## Adding or changing a sound

Add a function decorated with `@music("id")` in music.py (build a `Track`, add buses,
place notes, `return tr.mix(...)`), or with `@sfx("id")` in sfx.py (return a float
array; `loop=True` returns exactly one period). Then run the build. Run with `-v` and
`--review` to check the balance and the spectrogram, because nobody listens as part of
the build.
