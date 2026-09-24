param([string]$GodotPath = 'godot')
$ErrorActionPreference = 'Stop'
& $GodotPath --path $PSScriptRoot
