param([string]$GodotPath = $(if ($env:GODOT) { $env:GODOT } else { 'godot' }))
# Quality gates (Part 7) on Windows: the same gates and the same suites (tests/suites.txt) as tools/run_tests.sh, in the
# same order, read the same way. -GodotPath (or GODOT) names the Godot binary. valley_run plays all of Act I (about a
# minute).
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
# For the data gates that ask Godot too (topdown_rooms.py --check's grid parity): the same binary.
$env:GODOT = $GodotPath
# The Godot suites, one a line (tests/README.md): each prints "<name>: N checks, M failures", read below.
$suites = @(Get-Content (Join-Path $PSScriptRoot 'tests/suites.txt') | ForEach-Object { ($_ -replace '#.*$', '').Trim() } | Where-Object { $_ })
$python = @('python3', 'python', 'py') | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
$failed = New-Object System.Collections.Generic.List[string]

# A native command's output (stdout and stderr, as text lines: a line on stderr is output, never a PowerShell error) and
# its exit code.
function Invoke-Native([string]$exe, [string[]]$argv) {
    $was = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $lines = @(& $exe @argv 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $was }
    return [pscustomobject]@{ Lines = $lines; Code = $code }
}

# The animation rules (AGENTS.md).
Write-Host '== animations'
try { & (Join-Path $PSScriptRoot 'Validate-Animations.ps1') } catch { Write-Host $_.Exception.Message; $failed.Add('animations') }
# The data gates, each run as tools/run_tests.sh runs it:
#   build_data     audit 45 (S5): every data/*.json file is what its generator writes;
#   room_lint      S43 room lint and reach contract over the built rooms (Part 7);
#   topdown_rooms  redesign Phase 4: the top-down layouts are current, every thing placed and reached on foot;
#   room_engine    audit 45 (E1): every room spec compiles the same twice and to its layout, every anchor kind
#                  resolves, auto-path walks every room the engine lays out;
#   sect_walks     decision 42: no step of the sect stretch asks for a plain walk over 35 s, nor a walk out and back;
#   places         decision 43: the places table is current, every place where auto-path reaches it;
#   sound          decision 43: the sound table is current, every sound on disk passes its levels, seams and band;
#   cues           audit 45 (E6): the cue table (data/cues.json) is what its generator writes;
#   pix            audit 45 (S5): the pixel library for new art draws each shape exactly as its source;
#   monsters       audit 45 (E2): every species spec resolves and poses, its rows, loot, voice and sheets are what it makes.
$gates = @(
    @{ Name = 'build_data'; Args = @('tools/data/build_data.py', '--check') },
    @{ Name = 'room_lint'; Args = @('tools/data/room_lint.py') },
    @{ Name = 'topdown_rooms'; Args = @('tools/data/topdown_rooms.py', '--check') },
    @{ Name = 'room_engine'; Args = @('tools/content/rooms/test_engine.py') },
    @{ Name = 'sect_walks'; Args = @('tools/data/sect_walks.py', '--check') },
    @{ Name = 'places'; Args = @('tools/data/places.py', '--check') },
    @{ Name = 'sound'; Args = @('tools/data/sound.py', '--check') },
    @{ Name = 'cues'; Args = @('tools/data/cues.py', '--check') },
    @{ Name = 'pix'; Args = @('tools/lib/pix.py', '--check') },
    @{ Name = 'monsters'; Args = @('tools/content/monsters/build.py', '--check') }
)
foreach ($g in $gates) {
    Write-Host "== $($g.Name)"
    if (-not $python) { Write-Host '  no python3 on the PATH'; $failed.Add($g.Name); continue }
    $r = Invoke-Native $python $g.Args
    $r.Lines | ForEach-Object { Write-Host $_ }
    if ($r.Code -ne 0) { $failed.Add($g.Name) }
}
# The game starts: the project's main scene (project.godot run/main_scene) loads and runs a few frames. The suites
# load their own scenes, so only this catches a missing or broken main scene.
Write-Host '== boot'
$r = Invoke-Native $GodotPath @('--headless', '--path', '.', '--quit-after', '120')
if ($r.Code -ne 0 -or ($r.Lines -match 'Failed loading|SCRIPT ERROR')) {
    $r.Lines | Where-Object { $_ -match 'Failed loading|SCRIPT ERROR|ERROR' } | Select-Object -First 8 | ForEach-Object { Write-Host "  | $_" }
    $failed.Add('boot')
}
# The audio files: their last line when they pass, their failures when not.
if (-not $python) { $failed.Add('audio_check') }
else {
    $r = Invoke-Native $python @('tools/audio/build_audio.py', '--check')
    if ($r.Code -ne 0) {
        $r.Lines | Where-Object { $_ -match 'FAIL|MISSING|Error' } | Select-Object -First 20 | ForEach-Object { Write-Host $_ }
        $failed.Add('audio_check')
    } else { $r.Lines | Select-Object -Last 1 | ForEach-Object { Write-Host $_ } }
}
foreach ($s in $suites) {
    Write-Host "== $s"
    $r = Invoke-Native $GodotPath @('--headless', '--path', '.', "res://tests/$s.tscn")
    $r.Lines | Where-Object { $_ -match 'checks|passed|FAIL|SCRIPT ERROR' } | ForEach-Object { Write-Host $_ }
    $scriptError = @($r.Lines | Where-Object { $_ -match 'SCRIPT ERROR' }).Count -gt 0
    # A script error aborts a suite part-way and skips its remaining checks, so it fails the run too. A suite that exits
    # non-zero says with what code, and the last lines it printed, since its own summary may read clean.
    if ($r.Code -ne 0) {
        Write-Host "  $s exited with code $($r.Code)"
        $r.Lines | Select-Object -Last 12 | ForEach-Object { Write-Host "  | $_" }
    }
    if ($r.Code -ne 0 -or $scriptError) { $failed.Add($s) }
}
if ($failed.Count -gt 0) { Write-Host "Failed: $($failed -join ' ')"; exit 1 }
Write-Host 'All suites passed.'
exit 0
