param([string]$GodotPath = 'godot', [switch]$Long)
# Quality gates (Part 7). Fast suites run on every change; -Long adds the full
# Act I playthrough (tests/valley_run), which takes several minutes.
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Validate-Animations.ps1')
$suites = @('engine_tests', 'data_validation', 'rules_tests', 'contract_tests', 'balance_sim', 'prologue_run', 'valley_run')

$failed = @()
foreach ($s in $suites) {
    Write-Host "== $s"
    & $GodotPath --headless --path $PSScriptRoot --scene "res://tests/$s.tscn"
    if ($LASTEXITCODE -ne 0) { $failed += $s }
}
if ($failed.Count -gt 0) { Write-Host "Failed: $($failed -join ', ')"; exit 1 }
Write-Host 'All suites passed.'
exit 0
