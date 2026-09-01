param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a',
    [string]$PagesCheckout = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$GatewayUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne 'family24-d7gqb6r6m2d722f7a') {
    throw 'Project root or CloudBase environment mismatch. Refusing to run.'
}
if ([string]::IsNullOrWhiteSpace($PagesCheckout)) {
    $PagesCheckout = Join-Path $ProjectRoot '_runtime\github-pages-stage'
}
$PagesCheckout = (Resolve-Path -LiteralPath $PagesCheckout).Path
$ExpectedPagesCheckout = (Resolve-Path -LiteralPath (Join-Path $ProjectRoot '_runtime\github-pages-stage')).Path
if ($PagesCheckout -ne $ExpectedPagesCheckout) {
    throw 'Pages checkout mismatch. Only the protected _runtime staging checkout is allowed.'
}

$PagesStatusBefore = @(git -C $PagesCheckout status --porcelain)
if ($LASTEXITCODE -ne 0 -or $PagesStatusBefore.Count -ne 0) {
    throw 'Pages staging checkout is not clean before release preparation.'
}

$PreviousApiUrl = $env:VITE_SHERLOCK_API_URL
$PreviousProbeFlag = $env:VITE_DIRECT_UPLOAD_PROBE
$PreviousSpeakingDirectFlag = $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST
try {
    $env:VITE_SHERLOCK_API_URL = $GatewayUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = 'true'
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = 'true'

    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'GitHub Pages production build failed.' }
    }
    finally { Pop-Location }

    node (Join-Path $ProjectRoot 'tools\prepare-github-pages-release.mjs') `
        (Join-Path $ProjectRoot 'web\dist') $PagesCheckout
    if ($LASTEXITCODE -ne 0) { throw 'GitHub Pages release preparation failed.' }
}
finally {
    $env:VITE_SHERLOCK_API_URL = $PreviousApiUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = $PreviousProbeFlag
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = $PreviousSpeakingDirectFlag
}

$Changed = @(git -C $PagesCheckout status --short)
if ($LASTEXITCODE -ne 0 -or $Changed.Count -eq 0) {
    throw 'Pages staging checkout has no prepared release changes.'
}
foreach ($Line in $Changed) {
    $Path = if ($Line.Length -gt 3) { $Line.Substring(3).Replace('"', '') } else { '' }
    if ((-not $Path.StartsWith('sherlock-english/', [StringComparison]::OrdinalIgnoreCase)) `
        -and $Path -ne 'sherlock-english') {
        throw "Prepared release changed a protected Pages root path: $Line"
    }
}

Write-Host 'GitHub Pages candidate release is staged locally only.'
Write-Host "PagesCheckout=$PagesCheckout"
Write-Host "ChangedEntries=$($Changed.Count)"
