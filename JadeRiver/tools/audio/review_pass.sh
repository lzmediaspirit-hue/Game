#!/usr/bin/env bash
# Decision 43's review pictures and tables (docs/redesign/sound.md §8): before | after pairs of the sounds the pass
# replaced, contact sheets of the new ones, and the loudness tables. BEFORE is a copy of art/audio from before the pass.
#   tools/audio/review_pass.sh BEFORE_ART_AUDIO [OUT]
set -eu
cd "$(dirname "$0")/../.."
BEFORE="$1"
OUT="${2:-docs/redesign/feedback/sound}"
R="python3 tools/audio/review.py"
mkdir -p "$OUT/before_after" "$OUT/new"
$R --pair "$BEFORE" --out "$OUT/before_after" --sheet "" --table \
  hit=hit:sword:flesh hit=hit:sabre:shell hit=hit:fists:flesh hit=hit:spear:wood hit=hit:brush:slime hit_crit=hit:sword:flesh:crit \
  swing=swing_sword swing=swing_sabre swing=swing_bow tell=tell_beast enemy_die=die_shell land=land_stone water_step=step:water \
  water_ambience=bed:river:day wind_ambience=bed:bamboo:day crowd_ambience=bed:town:day battle=combat:field boss=boss_eel \
  boss_sting=boss_sting > "$OUT/table_before_after.md"
{
  echo "### Steps and landings"
  $R --out "$OUT/new" --sheet steps.png --no-singles --table step:grass step:dirt step:stone step:wood step:sand step:reeds \
    step:roof step:snow land_grass land_wood land_heavy splash
  echo; echo "### Hits"
  $R --out "$OUT/new" --sheet hits.png --no-singles --table hit:flute:flesh hit:bell:wood hit:fan:flesh hit:bow:flesh \
    hit:sword:shell:chain hit_accent_weave hit_el_fire hit_el_thunder hit_el_water hit_el_earth
  echo; echo "### Casts"
  $R --out "$OUT/new" --sheet casts.png --no-singles --table cast_qi cast_fire cast_water cast_wind cast_thunder cast_earth \
    cast_metal cast_wood cast_soul cast_space cast_time
  echo; echo "### Foes"
  $R --out "$OUT/new" --sheet foes.png --no-singles --table tell_human tell_construct tell_spirit tell_water die_flesh die_wood \
    die_slime die_spirit
  echo; echo "### The world, talk and the interface"
  $R --out "$OUT/new" --sheet world.png --no-singles --table door_open door_close loot_drop ui_confirm ui_tab talk_open \
    talk_next bark scene_in
  echo; echo "### Stingers"
  $R --out "$OUT/new" --sheet stingers.png --no-singles --table sting_quest sting_breakthrough sting_rare sting_unlock \
    sting_elite sting_victory
  echo; echo "### Beds"
  $R --out "$OUT/new" --sheet beds.png --no-singles --table bed_river bed:river:night bed_marsh bed:marsh:night bed_bamboo \
    bed_pines bed_field bed_town bed_sect bed_cave bed_interior bed_birds bed_insects bed_frogs
  echo; echo "### Music"
  $R --out "$OUT/new" --sheet music.png --no-singles --table village_day_combat village_night_combat field_combat river_combat \
    sect_combat boss_snapper boss_eel combat:village_night combat:river
} > "$OUT/table_new.md"
echo "review -> $OUT"
