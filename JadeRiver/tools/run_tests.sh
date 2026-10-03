#!/usr/bin/env bash
# Quality gates (Part 7) on Linux/macOS. Usage: tools/run_tests.sh
# GODOT=/path/to/godot overrides the binary. valley_run plays all of Act I (about a minute).
# Test.ps1 runs the same gates and the same suites (tests/suites.txt), in the same order, on Windows.
set -u
cd "$(dirname "$0")/.."
# Exported, so the data gates that ask Godot (topdown_rooms.py --check's grid parity) use the same binary.
export GODOT="${GODOT:-godot}"
# The Godot suites, one a line (tests/README.md): each prints "<name>: N checks, M failures", read below.
suites=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="${line//[[:space:]]/}"
  if [[ -n "$line" ]]; then suites+=("$line"); fi
done < tests/suites.txt

failed=()
# The animation rules (AGENTS.md; Validate-Animations.ps1), where PowerShell is installed.
if command -v pwsh >/dev/null 2>&1; then
  echo "== animations"
  if ! pwsh -NoProfile -File Validate-Animations.ps1; then failed+=("animations"); fi
fi
# Audit 45 (S5): every data/*.json file is what its generator writes.
echo "== build_data"
if ! python3 tools/data/build_data.py --check; then failed+=("build_data"); fi
# S43 room lint and reach contract over the built rooms (Part 7).
echo "== room_lint"
if ! python3 tools/data/room_lint.py; then failed+=("room_lint"); fi
# Redesign Phase 4: the top-down layouts are current and every thing in them is placed and reached on foot.
echo "== topdown_rooms"
if ! python3 tools/data/topdown_rooms.py --check; then failed+=("topdown_rooms"); fi
# Audit 45 (E1): the room engine compiles every spec the same twice and to its layout, resolves every anchor kind, and
# auto-path walks every room it lays out (tools/content/rooms/test_engine.py).
echo "== room_engine"
if ! python3 tools/content/rooms/test_engine.py; then failed+=("room_engine"); fi
# Decision 42: no step of the sect stretch asks for a plain walk over 35 s with nothing on the way, nor a walk out and back.
echo "== sect_walks"
if ! python3 tools/data/sect_walks.py --check; then failed+=("sect_walks"); fi
# Decision 43: the places table is current, and every place stands where auto-path reaches it (tools/data/places.py).
echo "== places"
if ! python3 tools/data/places.py --check; then failed+=("places"); fi
# Decision 43: the sound pass's table is current, and every sound on disk passes its levels, loop seams and phone band.
echo "== sound"
if ! python3 tools/data/sound.py --check; then failed+=("sound"); fi
# Audit 45 (E6): the cue table (data/cues.json) is what its generator writes.
echo "== cues"
if ! python3 tools/data/cues.py --check; then failed+=("cues"); fi
# Audit 45 (E4): the data holds every item family as its spec writes it, each source a family names is found, its pill
# icons are current, and the engine's own tests pass (tools/content/items).
echo "== item_engine"
if ! python3 tools/content/items/engine.py --check; then failed+=("item_engine"); fi
# Audit 45 (S5): the pixel library for new art draws each shape exactly as the source it came from.
echo "== pix"
if ! python3 tools/lib/pix.py --check; then failed+=("pix"); fi
# Audit 45 (E2): the monster engine: every species spec resolves and poses in every action and facing, and its rows,
# loot, voice and sheets are what it makes (tools/content/monsters/build.py).
echo "== monsters"
if ! python3 tools/content/monsters/build.py --check; then failed+=("monsters"); fi
# Audit 45 (E3): the NPC engine: every person's spec resolves, compiles the same twice, and is what npcs.json and
# life.json hold (its work spots resolved on the layouts); the engine's own tests pass (tools/content/npcs).
echo "== npc_engine"
if ! python3 tools/content/npcs/engine.py --check; then failed+=("npc_engine"); fi
# The game starts: the project's main scene (project.godot run/main_scene) loads and runs a few frames. The suites
# load their own scenes, so only this catches a missing or broken main scene.
echo "== boot"
bout="$("$GODOT" --headless --path . --quit-after 120 2>&1)"
bcode=$?
if [[ $bcode -ne 0 ]] || grep -qE "Failed loading|SCRIPT ERROR" <<<"$bout"; then
  grep -E "Failed loading|SCRIPT ERROR|ERROR" <<<"$bout" | head -8 | sed 's/^/  | /'
  failed+=("boot")
fi
alog="$(mktemp)"
if ! python3 tools/audio/build_audio.py --check > "$alog" 2>&1; then grep -E "FAIL|MISSING|Error" "$alog" | head -20; failed+=("audio_check"); else tail -1 "$alog"; fi
rm -f "$alog"
for s in "${suites[@]}"; do
  echo "== $s"
  out="$("$GODOT" --headless --path . "res://tests/$s.tscn" 2>&1)"
  code=$?
  grep -E "checks|passed|FAIL|SCRIPT ERROR" <<<"$out" || true
  # A script error aborts a suite part-way and skips its remaining checks, so it fails the run too.
  # A suite that exits non-zero says with what code (a crash in teardown shows as 128 + its signal: 134 abort, 139
  # segfault), and the last lines it printed, since its own summary may read clean.
  if [[ $code -ne 0 ]]; then
    echo "  $s exited with code $code$( ((code > 128)) && echo " (signal $((code - 128)))")"
    tail -n 12 <<<"$out" | sed 's/^/  | /'
  fi
  if [[ $code -ne 0 ]] || grep -q "SCRIPT ERROR" <<<"$out"; then failed+=("$s"); fi
done
if [[ ${#failed[@]} -gt 0 ]]; then echo "Failed: ${failed[*]}"; exit 1; fi
echo "All suites passed."
