param([string]$GodotPath = 'godot', [string]$OutputPath = (Join-Path $PSScriptRoot '../builds/JadeRiver-Android.apk'))
$ErrorActionPreference = 'Stop'
& $GodotPath --headless --path $PSScriptRoot --export-debug Android ([IO.Path]::GetFullPath($OutputPath))
if ($LASTEXITCODE -ne 0) { throw "Android export failed: $LASTEXITCODE" }
