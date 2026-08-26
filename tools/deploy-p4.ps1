param([string]$EnvId = 'family24-d7gqb6r6m2d722f7a')

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
    if ([string]::IsNullOrWhiteSpace($ScriptPath)) { throw 'Current site bundle was not found.' }
    $ScriptUrl = [Uri]::new([Uri]$BaseUrl, $ScriptPath)
    $JavaScript = (Invoke-WebRequest -Uri $ScriptUrl -UseBasicParsing -TimeoutSec 30).Content
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
    throw 'Existing CloudBase publish key could not be recovered from the deployed bundle.'
}

& (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
if ($LASTEXITCODE -ne 0) { throw 'P4 CloudBase read-only preflight failed.' }

Push-Location $ProjectRoot
try {
    node --test .\tools\p4-migration.test.mjs
    if ($LASTEXITCODE -ne 0) { throw 'P4 migration tests failed.' }

    Push-Location (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api')
    try {
        npm run test:coverage
        if ($LASTEXITCODE -ne 0) { throw 'sherlock-api tests failed.' }
    }
    finally { Pop-Location }

    # Code-only update deliberately preserves the existing password, session and scorer secrets.
    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api --dir (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api') --json
    if ($LASTEXITCODE -ne 0) { throw 'sherlock-api P4 code update failed.' }

    $HealthEvent = ConvertTo-NativeJsonArgument ((@{ action = 'health' } | ConvertTo-Json -Compress))
    $UnauthenticatedEvent = ConvertTo-NativeJsonArgument ((@{ action = 'listParentResults' } | ConvertTo-Json -Compress))
    $Health = $null
    $Unauthorized = $null
    foreach ($Attempt in 1..6) {
        try {
            $HealthInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $HealthEvent --json)
            $Health = $HealthInvoke.data.RetMsg | ConvertFrom-Json
            $UnauthorizedInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $UnauthenticatedEvent --json)
            $Unauthorized = $UnauthorizedInvoke.data.RetMsg | ConvertFrom-Json
            if ($Health.ok -and $Health.stage -eq 'P4' -and $Unauthorized.error.code -eq 'UNAUTHORIZED') { break }
        }
        catch {
            if ($Attempt -eq 6) { throw }
        }
        if ($Attempt -lt 6) { Start-Sleep -Seconds 5 }
    }
    if (-not $Health.ok -or $Health.stage -ne 'P4' -or $Health.writes -ne 'test-only' -or $Health.formal_enabled) {
        throw 'P4 health boundary verification failed.'
    }
    if ($Unauthorized.ok -ne $false -or $Unauthorized.error.code -ne 'UNAUTHORIZED') {
        throw 'P4 parent authentication boundary verification failed.'
    }

    $env:VITE_CLOUDBASE_ENV_ID = $EnvId
    $env:VITE_CLOUDBASE_ACCESS_KEY = Get-ExistingPublishKey
    $env:VITE_CLOUDBASE_FUNCTION_NAME = 'sherlock-api'
    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run typecheck
        if ($LASTEXITCODE -ne 0) { throw 'Web type check failed.' }
        npm run test:coverage
        if ($LASTEXITCODE -ne 0) { throw 'Web tests failed.' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
        npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId hosting deploy .\dist sherlock-english --json
        if ($LASTEXITCODE -ne 0) { throw 'P4 static hosting deployment failed.' }
    }
    finally { Pop-Location }

    $TestUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
    $Response = Invoke-WebRequest -Uri $TestUrl -UseBasicParsing -TimeoutSec 30
    if ($Response.StatusCode -ne 200 -or $Response.Content -notmatch '<div id="root"></div>') {
        throw 'P4 site online verification failed.'
    }

    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'P4 post-deploy family24 verification failed.' }
    Write-Host "P4 TEST deployment succeeded: $TestUrl"
}
finally {
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
    Pop-Location
}
