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
$CloudBaseUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
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

function Get-ExistingPublishKey {
    $Html = (Invoke-WebRequest -Uri $CloudBaseUrl -UseBasicParsing -TimeoutSec 30).Content
    $ScriptPath = [regex]::Match($Html, 'src="([^"]+\.js)"').Groups[1].Value
    if ([string]::IsNullOrWhiteSpace($ScriptPath)) { throw 'Current CloudBase bundle was not found.' }
    $JavaScript = (Invoke-WebRequest -Uri ([Uri]::new([Uri]$CloudBaseUrl, $ScriptPath)) -UseBasicParsing -TimeoutSec 30).Content
    foreach ($Candidate in [regex]::Matches($JavaScript, 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')) {
        $Token = $Candidate.Value
        $Part = $Token.Split('.')[1].Replace('-', '+').Replace('_', '/')
        while ($Part.Length % 4) { $Part += '=' }
        try {
            $Payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Part)) | ConvertFrom-Json
            if ($Payload.project_id -eq $EnvId -and $Payload.meta.platform -eq 'PublishableKey') { return $Token }
        }
        catch { continue }
    }
    throw 'Existing CloudBase publish key could not be recovered.'
}

$PagesStatusBefore = @(git -C $PagesCheckout status --porcelain)
if ($LASTEXITCODE -ne 0 -or $PagesStatusBefore.Count -ne 0) {
    throw 'Pages staging checkout is not clean before release preparation.'
}

try {
    $env:VITE_CLOUDBASE_ENV_ID = $EnvId
    $env:VITE_CLOUDBASE_ACCESS_KEY = Get-ExistingPublishKey
    $env:VITE_CLOUDBASE_FUNCTION_NAME = 'sherlock-api'

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
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
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
