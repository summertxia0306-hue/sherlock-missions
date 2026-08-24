param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a',
    [switch]$StaticOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne 'family24-d7gqb6r6m2d722f7a') {
    throw 'Project root or CloudBase environment mismatch. Refusing to run.'
}

function ConvertFrom-TcbOutput([object[]]$Lines) {
    $Joined = $Lines -join "`n"
    $Start = $Joined.IndexOf('{')
    if ($Start -lt 0) { throw 'CloudBase CLI did not return JSON.' }
    $Object = $Joined.Substring($Start) | ConvertFrom-Json
    if ($Object.PSObject.Properties['error']) { throw "CloudBase operation failed: $($Object.error.code)" }
    return $Object
}

function ConvertTo-NativeJsonArgument([string]$Json) {
    if ($PSVersionTable.PSVersion.Major -le 5) { return $Json.Replace('"', '\"') }
    return $Json
}

function Get-ExistingPublishKey {
    $BaseUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
    $Html = (Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 30).Content
    $ScriptPath = [regex]::Match($Html, 'src="([^"]+\.js)"').Groups[1].Value
    if ([string]::IsNullOrWhiteSpace($ScriptPath)) { throw 'Current P1 site bundle was not found.' }
    $ScriptUrl = [Uri]::new([Uri]$BaseUrl, $ScriptPath)
    $JavaScript = (Invoke-WebRequest -Uri $ScriptUrl -UseBasicParsing -TimeoutSec 30).Content
    $Candidates = [regex]::Matches($JavaScript, 'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
    foreach ($Candidate in $Candidates) {
        $Token = $Candidate.Value
        $Part = $Token.Split('.')[1].Replace('-', '+').Replace('_', '/')
        while ($Part.Length % 4) { $Part += '=' }
        try {
            $Payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Part)) | ConvertFrom-Json
            if ($Payload.project_id -eq $EnvId -and $Payload.meta.platform -eq 'PublishableKey') { return $Token }
        }
        catch { continue }
    }
    throw 'Existing CloudBase publish key could not be recovered from the public P1 bundle.'
}

& (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
if ($LASTEXITCODE -ne 0) { throw 'P2 CloudBase read-only preflight failed.' }

Push-Location $ProjectRoot
try {
    node (Join-Path $PSScriptRoot 'sync-p2-assets.mjs')
    if ($LASTEXITCODE -ne 0) { throw 'P2 asset synchronization failed.' }

    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) { throw 'Web type check failed.' }
        npm run test:coverage
        if ($LASTEXITCODE -ne 0) { throw 'Web tests failed.' }
    }
    finally { Pop-Location }

    if (-not $StaticOnly) {
        Push-Location (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api')
        try {
            npm run test:coverage
            if ($LASTEXITCODE -ne 0) { throw 'Cloud function tests failed.' }
        }
        finally { Pop-Location }
    }

    $env:VITE_CLOUDBASE_ENV_ID = $EnvId
    $env:VITE_CLOUDBASE_ACCESS_KEY = Get-ExistingPublishKey
    $env:VITE_CLOUDBASE_FUNCTION_NAME = 'sherlock-api'
    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'P2 web build failed.' }
    }
    finally { Pop-Location }

    if (-not $StaticOnly) {
        npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api --dir (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api') --json
        if ($LASTEXITCODE -ne 0) { throw 'sherlock-api code-only update failed.' }
    }

    $HealthEvent = @{ action = 'health'; userInfo = @{ openId = 'p2-deploy-health' } } | ConvertTo-Json -Compress -Depth 5
    $Health = $null
    foreach ($Attempt in 1..6) {
        $HealthInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d (ConvertTo-NativeJsonArgument $HealthEvent) --json)
        $Health = $HealthInvoke.data.RetMsg | ConvertFrom-Json
        if ($Health.ok -and $Health.stage -eq 'P2' -and $Health.formal_enabled -eq $false -and $Health.writes -eq 'test-only') { break }
        if ($Attempt -lt 6) { Start-Sleep -Seconds 5 }
    }
    if (-not $Health.ok -or $Health.stage -ne 'P2' -or $Health.formal_enabled -ne $false -or $Health.writes -ne 'test-only') {
        throw "P2 server health enforcement verification failed: $($Health | ConvertTo-Json -Compress)"
    }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId hosting deploy (Join-Path $ProjectRoot 'web\dist') sherlock-english --json
    if ($LASTEXITCODE -ne 0) { throw 'P2 static hosting deployment failed.' }

    $BaseUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
    $Index = Invoke-WebRequest -Uri $BaseUrl -UseBasicParsing -TimeoutSec 30
    $Catalog = Invoke-WebRequest -Uri ($BaseUrl + 'content/listening/catalog.json') -UseBasicParsing -TimeoutSec 30
    $ChildCourse = Invoke-WebRequest -Uri ($BaseUrl + 'content/listening/W01D39.json') -UseBasicParsing -TimeoutSec 30
    $Audio = Invoke-WebRequest -Uri ($BaseUrl + 'audio/listening/W01D39/q01.mp3') -UseBasicParsing -TimeoutSec 30
    if ($Index.StatusCode -ne 200 -or $Catalog.StatusCode -ne 200 -or $Audio.StatusCode -ne 200) {
        throw 'P2 public site verification failed.'
    }
    $CatalogObject = $Catalog.Content | ConvertFrom-Json
    if ($CatalogObject.Count -ne 12 -or $ChildCourse.Content -match '"(answer|transcript|tag|parent_note)"') {
        throw 'P2 child course isolation verification failed.'
    }

    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'P2 post-deploy CloudBase preflight failed.' }
    node (Join-Path $PSScriptRoot 'verify-p2-cloudbase.mjs')
    if ($LASTEXITCODE -ne 0) { throw 'P2 CloudBase result-boundary verification failed.' }
    Write-Host "P2 TEST deployment succeeded: $BaseUrl"
    Write-Host 'Parent password and function environment variables were preserved by code-only update.'
}
finally {
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
    Pop-Location
}
