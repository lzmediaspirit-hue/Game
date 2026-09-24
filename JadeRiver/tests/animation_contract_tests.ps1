$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$original = Get-Content -LiteralPath (Join-Path $projectRoot 'data/parts.json') -Raw
$temporaryCatalog = Join-Path ([IO.Path]::GetTempPath()) ('jade-animation-' + [guid]::NewGuid().ToString() + '.json')
$cases = @('missing-pose','new-action','bad-grid','missing-dye','empty-item','repeated-combo','looping-combo')
try {
    foreach ($case in $cases) {
        $catalog = $original | ConvertFrom-Json
        switch ($case) {
            'missing-pose' { $catalog.shirt.cardigan.layers[0].animations.PSObject.Properties.Remove('swing') }
            'new-action' { $catalog._actions | Add-Member new_dodge ([pscustomobject]@{frames=6;fps=10}) }
            'bad-grid' { $catalog._actions.swing.frames = 7 }
            'missing-dye' { $catalog.hair.topknot.layers[0].animations.swing.sheets = @($catalog.hair.topknot.layers[0].animations.swing.sheets[0]) }
            'empty-item' { $catalog.weapon | Add-Member broken_sword ([pscustomobject]@{layers=@()}) }
            'repeated-combo' { $catalog.body.light.layers[0].animations.swing_2.sheets = $catalog.body.light.layers[0].animations.swing_1.sheets }
            'looping-combo' { $catalog._actions.swing_3.loop = $true }
        }
        $catalog | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $temporaryCatalog
        $rejected = $false
        try { & (Join-Path $projectRoot 'Validate-Animations.ps1') -CatalogPath $temporaryCatalog | Out-Null } catch { $rejected = $true }
        if (-not $rejected) { throw "Animation gate accepted $case" }
    }
} finally {
    if (Test-Path -LiteralPath $temporaryCatalog) { Remove-Item -LiteralPath $temporaryCatalog }
}
Write-Output 'ANIMATION_GATE_TESTS: 7/7 invalid content changes rejected'
