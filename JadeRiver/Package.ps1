param([string]$OutputPath = (Join-Path $PSScriptRoot '../builds/JadeRiver-Godot-Source-clean.zip'))
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Validate-Animations.ps1')
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$output = [IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $output) { throw "Output already exists: $output" }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($output)) | Out-Null
# Preserve source, runtime assets, tests, provenance and licenses.
# Excluded working documents and replaced artwork remain in the workspace.
$rootFiles = @('project.godot','export_presets.cfg','README.md','AGENTS.md','Run.ps1','Test.ps1','Package.ps1','Validate-Animations.ps1','Export-Android.ps1','.gitignore')
$docs = @('architecture.md','map-generation.md','art-generation.md','art-v03-prompts.md','art-v04-prompts.md','art-v06-prompts.md','art-v13-gate.md','review-v08.md','review-v09.md','review-v13.md')
$unusedArt = @('environment/sanctuary.png','environment/sanctuary-pixel.png','environment/terrain-atlas.png','fonts/PixelifySans.ttf','fonts/Pixelify-OFL.txt')
$files = @(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object {
    $relative = $_.FullName.Substring($root.Length + 1).Replace('\','/')
    if ($relative -in $rootFiles) { return $true }
    if ($relative -match '^(scripts|scenes|tests)/') { return $_.Extension -in @('.gd','.uid','.tscn','.tres','.json','.ps1') }
    if ($relative -match '^data/') { return $_.Extension -in @('.json','.txt') -and $_.Name -ne 'movement-review.json' }
    if ($relative -match '^docs/') { return $relative.Substring(5) -in $docs }
    if ($relative -match '^art/') {
        $asset = $relative.Substring(4) -replace '\.import$',''
        return -not $asset.StartsWith('concepts/') -and $asset -notin $unusedArt -and $_.Extension -in @('.png','.ttf','.txt','.import')
    }
    return $false
} | Sort-Object FullName)
$archive = [IO.Compression.ZipFile]::Open($output, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($file in $files) {
        $entry = 'JadeRiver/' + $file.FullName.Substring($root.Length + 1).Replace('\','/')
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,$file.FullName,$entry,[IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
} finally { $archive.Dispose() }
$bytes = (Get-Item -LiteralPath $output).Length
Write-Output ("Packaged {0} files: {1:N2} MB ({2} bytes): {3}" -f $files.Count,($bytes / 1000000),$bytes,$output)
