param([string]$GodotPath = 'godot')
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Validate-Animations.ps1')
& $GodotPath --headless --path $PSScriptRoot --scene res://tests/engine_tests.tscn
exit $LASTEXITCODE
