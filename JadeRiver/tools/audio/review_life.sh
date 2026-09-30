#!/usr/bin/env bash
# Decision 44's review pictures and loudness table (docs/redesign/sound.md §10): the living world's sounds and the
# places', each at its level as the game plays it (before the bus and the distance falloff), a contact sheet a group
# (waveform and spectrogram of each), and for scale a few of the fight's and the feet's and a bed they play among.
#   tools/audio/review_life.sh [OUT]
set -eu
cd "$(dirname "$0")/../.."
OUT="${1:-docs/redesign/feedback/sound/life}"
R="python3 tools/audio/review.py"
mkdir -p "$OUT"
{
  echo "### Critters"
  $R --out "$OUT" --sheet critters.png --no-singles --table life_sparrow_flee life_fish_flee life_frog_leap life_frog_plop \
    life_hen_flap life_cat_wake life_dog_bark life_dog_bark_b
  echo; echo "### Work"
  $R --out "$OUT" --sheet work.png --no-singles --table life_work_sweep life_work_set_down life_work_scrub life_work_hang \
    life_work_pick life_work_stir life_work_grind life_work_chop life_work_chop_hit life_work_hammer life_work_hammer_hit \
    life_work_stoke life_work_fish life_work_recast life_work_mend life_work_look life_work_write life_work_breathe
  echo; echo "### The takes played in turn"
  $R --out "$OUT" --sheet takes.png --no-singles --table life_work_sweep life_work_sweep_b life_work_sweep_c life_work_chop \
    life_work_chop_b life_work_chop_hit life_work_chop_hit_b life_work_chop_hit_c life_work_hammer life_work_hammer_b \
    life_work_hammer_hit life_work_hammer_hit_b life_work_hammer_hit_c life_work_scrub life_work_scrub_b
  echo; echo "### Places"
  $R --out "$OUT" --sheet places.png --no-singles --table place_open place_tend place_sit
  echo; echo "### For scale: the fight, the feet and a bed (not new)"
  $R --table hit:sword:flesh swing_sword step:grass door_open bed:river_village:day
} > "$OUT/table.md"
echo "review -> $OUT"
