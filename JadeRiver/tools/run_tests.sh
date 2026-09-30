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
# S43 room lint and reach contract over the built rooms (Part 7).
echo "== room_lint"
if ! python3 tools/data/room_lint.py; then failed+=("room_lint"); fi
# Redesign Phase 4: the top-down layouts are current and every thing in them is placed and reached on foot.
echo "== topdown_rooms"
if ! python3 tools/data/topdown_rooms.py --check; then failed+=("topdown_rooms"); fi
# Decision 42: no step of the sect stretch asks for a plain walk over 35 s with nothing on the way, nor a walk out and back.
echo "== sect_walks"
if ! python3 tools/data/sect_walks.py --check; then failed+=("sect_walks"); fi
# Decision 43: the places table is current, and every place stands where auto-path reaches it (tools/data/places.py).
echo "== places"
if ! python3 tools/data/places.py --check; then failed+=("places"); fi
# Decision 43: the sound pass's table is current, and every sound on disk passes its levels, loop seams and phone band.
echo "== sound"
if ! python3 tools/data/sound.py --check; then failed+=("sound"); fi
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
