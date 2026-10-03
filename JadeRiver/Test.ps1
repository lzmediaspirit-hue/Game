param([string]$GodotPath = 'godot', [switch]$Long)
# Quality gates (Part 7). Fast suites run on every change; -Long adds the full
# Act I playthrough (tests/valley_run), which takes several minutes.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Validate-Animations.ps1')
$suites = @('engine_tests', 'data_validation', 'room_sweep', 'visibility_suite', 'rules_tests', 'contract_tests', 'balance_sim', 'perf_tests', 'prologue_run', 'tutorial_order', 'topdown_tutorial', 'tutorials', 'story_scenes', 'hollow_night', 'audio_tests', 'valley_run', 'places_tests', 'shared_runtime_tests', 'cue_tests', 'hud_tests')

$failed = @()
foreach ($s in $suites) {
    Write-Host "== $s"
    & $GodotPath --headless --path $PSScriptRoot --scene "res://tests/$s.tscn"
    # A suite that exits non-zero says with what code (a crash in teardown can follow a clean summary).
    if ($LASTEXITCODE -ne 0) { Write-Host "  $s exited with code $LASTEXITCODE"; $failed += $s }
}
if ($failed.Count -gt 0) { Write-Host "Failed: $($failed -join ', ')"; exit 1 }
Write-Host 'All suites passed.'
exit 0
