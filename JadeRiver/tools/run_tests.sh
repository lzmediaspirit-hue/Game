#!/usr/bin/env bash
# Quality gates (Part 7) on Linux/macOS. Usage: tools/run_tests.sh
# GODOT=/path/to/godot overrides the binary. valley_run plays all of Act I (about a minute).
set -u
cd "$(dirname "$0")/.."
GODOT="${GODOT:-godot}"
suites=(engine_tests data_validation rules_tests contract_tests balance_sim perf_tests prologue_run valley_run)

failed=()
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
