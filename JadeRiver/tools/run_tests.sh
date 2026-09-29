#!/usr/bin/env bash
# Quality gates (Part 7) on Linux/macOS. Usage: tools/run_tests.sh
# GODOT=/path/to/godot overrides the binary. valley_run plays all of Act I (about a minute).
set -u
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
suites=(engine_tests data_validation room_sweep visibility_suite rules_tests contract_tests balance_sim perf_tests prologue_run tutorial_order topdown_tutorial tutorials story_scenes hollow_night valley_run places_tests)

failed=()
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
for s in "${suites[@]}"; do
  echo "== $s"
  out="$("$GODOT" --headless --path . "res://tests/$s.tscn" 2>&1)"
  code=$?
  grep -E "checks|passed|FAIL|SCRIPT ERROR" <<<"$out" || true
  # A script error aborts a suite part-way and skips its remaining checks, so it fails the run too.
  if [[ $code -ne 0 ]] || grep -q "SCRIPT ERROR" <<<"$out"; then failed+=("$s"); fi
done
if [[ ${#failed[@]} -gt 0 ]]; then echo "Failed: ${failed[*]}"; exit 1; fi
echo "All suites passed."
