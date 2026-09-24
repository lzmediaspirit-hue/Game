param([string]$CatalogPath = (Join-Path $PSScriptRoot 'data/parts.json'))
$ErrorActionPreference = 'Stop'
$catalog = Get-Content -LiteralPath $CatalogPath -Raw | ConvertFrom-Json
$problems = [Collections.Generic.List[string]]::new()
$checked = 0
foreach ($family in @('swing','thrust','punch')) {
    $hashes = @()
    foreach ($stage in 1..3) {
        $action = "${family}_$stage"
        if (-not $catalog._actions.$action -or $catalog._actions.$action.loop -ne $false) { $problems.Add("Missing non-looping combo stage: $action"); continue }
        $body = $catalog.body.light.layers[0].animations.$action
        if ($body.sheets) {
            $path = Join-Path $PSScriptRoot ($body.sheets[0] -replace '^art_v12/','art/')
            if (Test-Path -LiteralPath $path) { $hashes += (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
        }
    }
    if (($hashes | Select-Object -Unique).Count -ne 3) { $problems.Add("Combo requires three distinct body animations: $family") }
}
foreach ($action in $catalog._actions.PSObject.Properties) {
    if ($action.Value.frames -lt 1 -or $action.Value.fps -le 0) { $problems.Add("Invalid animation timing: $($action.Name)") }
}
foreach ($category in @('body','hair','shirt','pants','shoes','weapon')) {
    foreach ($item in $catalog.$category.PSObject.Properties) {
        if ($item.Name -ne 'none' -and $item.Value.layers.Count -eq 0) { $problems.Add("Item has no sprite layers: $category/$($item.Name)") }
        foreach ($action in $catalog._actions.PSObject.Properties) {
            $visible = 0
            foreach ($layer in $item.Value.layers) {
                $label = "$category/$($item.Name)/$($layer.section)/$($action.Name)"
                $animation = $layer.animations.($action.Name)
                if ($null -eq $animation) { $problems.Add("Missing pose: $label"); continue }
                if ($animation.hidden) {
                    if (-not $animation.reason) { $problems.Add("Hidden layer lacks a reason: $label") }
                    continue
                }
                $visible++
                if (-not $animation.sheets) { $problems.Add("Pose has no sheets: $label"); continue }
                if ($category -eq 'hair' -and $animation.sheets.Count -ne 6) { $problems.Add("Hair pose must cover six dyes: $label") }
                if ($animation.rig -and $animation.rig.track.Count -ne $action.Value.frames) { $problems.Add("Rig frame count differs from body: $label") }
                foreach ($sheet in $animation.sheets) {
                    $path = Join-Path $PSScriptRoot ($sheet -replace '^art_v12/','art/')
                    if (-not (Test-Path -LiteralPath $path)) { $problems.Add("Missing sprite: $sheet"); continue }
                    $bytes = [IO.File]::ReadAllBytes($path)
                    if ($bytes.Length -lt 24 -or $bytes[0] -ne 137 -or $bytes[1] -ne 80) { $problems.Add("Invalid PNG: $sheet"); continue }
                    $width = $bytes[16]*16777216 + $bytes[17]*65536 + $bytes[18]*256 + $bytes[19]
                    $height = $bytes[20]*16777216 + $bytes[21]*65536 + $bytes[22]*256 + $bytes[23]
                    if ($width -ne $animation.cell*$action.Value.frames -or $height -ne $animation.cell*2) {
                        $problems.Add("Frame grid/facings mismatch: $label ($width x $height)")
                    }
                    $checked++
                }
            }
            if ($item.Value.layers.Count -gt 0 -and $visible -eq 0) { $problems.Add("Entire item absent in action: $category/$($item.Name)/$($action.Name)") }
        }
    }
}
if ($problems.Count) { throw ($problems -join "`n") }
Write-Output "ANIMATION_CONTRACT: $checked sprite variants validated across all registered actions."
