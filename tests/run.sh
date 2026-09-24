#!/bin/sh
# Runs headless rules tests; fails on any script error. Usage: GODOT=/path/to/godot tests/run.sh
G=${GODOT:-godot}
cd "$(dirname "$0")/.." || exit 1
OUT=$($G --headless --path . --script tests/test_rules.gd 2>&1)
echo "$OUT" | grep -vE "^(Godot Engine|$)"
echo "$OUT" | grep -q "SCRIPT ERROR" && { echo "script errors present"; exit 1; }
echo "$OUT" | grep -q " 0 failed" || exit 1
