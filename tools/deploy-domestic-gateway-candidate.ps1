param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom
Add-Type -AssemblyName System.Net.Http

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ExpectedEnvId = 'family24-d7gqb6r6m2d722f7a'
$GatewayUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'
$DomesticOrigin = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com'
$GitHubOrigin = 'https://summertxia0306-hue.github.io'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne $ExpectedEnvId) {
    throw 'Project root or CloudBase environment mismatch. Refusing to run.'
}

function Read-EnvFile([string]$Path) {
    $Values = [ordered]@{}
    foreach ($Line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($Line) -or $Line.TrimStart().StartsWith('#')) { continue }
        $Parts = $Line -split '=', 2
        if ($Parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($Parts[0])) {
            throw 'Pulled function environment file is malformed.'
        }
        $Values[$Parts[0].Trim()] = $Parts[1]
    }
    return $Values
}

function Assert-EnvironmentEqual([System.Collections.IDictionary]$Expected, [System.Collections.IDictionary]$Actual) {
    if ($Expected.Count -ne $Actual.Count) { throw 'Function environment variable count changed during code-only deployment.' }
    foreach ($Key in $Expected.Keys) {
        if (-not $Actual.Contains($Key) -or [string]$Actual[$Key] -cne [string]$Expected[$Key]) {
            throw "Function environment variable drift detected: $Key"
        }
    }
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

function Invoke-Function([hashtable]$Event) {
    $Argument = ConvertTo-NativeJsonArgument ($Event | ConvertTo-Json -Compress -Depth 10)
    $Response = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $Argument --json)
    if ($LASTEXITCODE -ne 0) { throw 'CloudBase function invocation failed.' }
    return $Response.data.RetMsg | ConvertFrom-Json
}

function Invoke-Http([string]$Method, [string]$Url, [string]$Origin = '', [string]$Body = '') {
    $Handler = New-Object System.Net.Http.HttpClientHandler
    $Handler.AllowAutoRedirect = $false
    $Client = New-Object System.Net.Http.HttpClient($Handler)
    $Request = $null
    try {
        $Request = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::new($Method), $Url)
        if (-not [string]::IsNullOrWhiteSpace($Origin)) { $Request.Headers.TryAddWithoutValidation('Origin', $Origin) | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($Body)) {
            $Request.Content = New-Object System.Net.Http.StringContent($Body, $Utf8NoBom, 'application/json')
        }
        $Response = $Client.SendAsync($Request).GetAwaiter().GetResult()
        $Content = $Response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        $Headers = @{}
        foreach ($Header in $Response.Headers) { $Headers[$Header.Key] = @($Header.Value) -join ', ' }
        foreach ($Header in $Response.Content.Headers) { $Headers[$Header.Key] = @($Header.Value) -join ', ' }
        return [pscustomobject]@{ StatusCode = [int]$Response.StatusCode; Body = $Content; Headers = $Headers }
    }
    finally {
        if ($null -ne $Request) { $Request.Dispose() }
        $Client.Dispose()
        $Handler.Dispose()
    }
}

function Assert-ApiError([object]$Response, [int]$StatusCode, [string]$ErrorCode) {
    if ($Response.StatusCode -ne $StatusCode) { throw "Expected HTTP $StatusCode but received $($Response.StatusCode)." }
    $Payload = $Response.Body | ConvertFrom-Json
    if ($Payload.ok -ne $false -or $Payload.error.code -ne $ErrorCode) {
        throw "Expected API error $ErrorCode."
    }
}

function Wait-ForStaticShell {
    $LastResponse = $null
    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {
        $LastResponse = Invoke-Http 'GET' "$GatewayUrl/"
        $ContentType = if ($LastResponse.Headers.ContainsKey('Content-Type')) { $LastResponse.Headers['Content-Type'] } else { '' }
        $Disposition = if ($LastResponse.Headers.ContainsKey('Content-Disposition')) { $LastResponse.Headers['Content-Disposition'] } else { '' }
        $DownloadLike = -not [string]::IsNullOrWhiteSpace($Disposition) -and $Disposition -notmatch '^inline(?:;|$)'
        if ($LastResponse.StatusCode -eq 200 -and $ContentType -match '^text/html' -and -not $DownloadLike `
            -and $LastResponse.Body -match '/sherlock-api/assets/') {
            return $LastResponse
        }
        if ($Attempt -lt 12) { Start-Sleep -Seconds 3 }
    }
    $LastType = if ($LastResponse.Headers.ContainsKey('Content-Type')) { $LastResponse.Headers['Content-Type'] } else { 'missing' }
    $LastDisposition = if ($LastResponse.Headers.ContainsKey('Content-Disposition')) { $LastResponse.Headers['Content-Disposition'] } else { 'none' }
    throw "Domestic gateway shell did not propagate safely. Status=$($LastResponse.StatusCode) ContentType=$LastType ContentDisposition=$LastDisposition"
}

function Find-DownloadedFunctionRoot([string]$Root) {
    $Package = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter 'package.json' |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.Directory.FullName 'index.js') } |
        Select-Object -First 1
    if ($null -eq $Package) { throw 'Downloaded CloudBase backup does not contain the function root.' }
    return $Package.Directory.FullName
}

$RunId = [guid]::NewGuid().ToString('N')
$BeforeEnvPath = Join-Path $ProjectRoot ".domestic-candidate-before-$RunId.tmp"
$AfterEnvPath = Join-Path $ProjectRoot ".domestic-candidate-after-$RunId.tmp"
$BackupRoot = Join-Path $ProjectRoot "_runtime\domestic-candidate-backup-$RunId"
$PublicAppRoot = Join-Path $ProjectRoot 'cloudfunctions\sherlock-api\public-app'
$SafeRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
foreach ($Path in @($BeforeEnvPath, $AfterEnvPath, $BackupRoot, $PublicAppRoot)) {
    if (-not ([IO.Path]::GetFullPath($Path)).StartsWith($SafeRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Unsafe deployment path.'
    }
}

$PreviousBase = $env:VITE_APP_BASE
$PreviousApiUrl = $env:VITE_SHERLOCK_API_URL
$PreviousProbeFlag = $env:VITE_DIRECT_UPLOAD_PROBE
$PreviousSpeakingDirectFlag = $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST
$CodeUpdateAttempted = $false
$BackupFunctionRoot = $null
try {
    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'CloudBase preflight failed.' }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $BeforeEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $BeforeEnvPath)) { throw 'Unable to capture the current function environment.' }
    $BeforeEnvironment = Read-EnvFile $BeforeEnvPath
    if ([string]$BeforeEnvironment['FORMAL_ENTRY_MODE'] -cne 'github-http-only') {
        throw 'Candidate deployment requires the existing github-http-only safety mode.'
    }

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code download sherlock-api $BackupRoot --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Unable to download the current function code for rollback.' }
    $BackupFunctionRoot = Find-DownloadedFunctionRoot $BackupRoot

    $env:VITE_APP_BASE = '/sherlock-api/'
    $env:VITE_SHERLOCK_API_URL = $GatewayUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = 'true'
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = 'true'
    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Domestic gateway production build failed.' }
    }
    finally { Pop-Location }

    node (Join-Path $ProjectRoot 'tools\prepare-domestic-gateway-release.mjs') `
        (Join-Path $ProjectRoot 'web\dist') $PublicAppRoot
    if ($LASTEXITCODE -ne 0) { throw 'Domestic gateway release preparation failed.' }

    $CodeUpdateAttempted = $true
    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api `
        --dir (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api') --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Domestic gateway candidate code deployment failed.' }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $AfterEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $AfterEnvPath)) { throw 'Unable to verify function environment after deployment.' }
    Assert-EnvironmentEqual $BeforeEnvironment (Read-EnvFile $AfterEnvPath)

    $Health = Invoke-Function @{ action = 'health' }
    if (-not $Health.ok -or $Health.formal_entry_mode -ne 'github-http-only') {
        throw 'Candidate deployment changed the formal entry mode unexpectedly.'
    }

    $Shell = Wait-ForStaticShell
    $AssetMatch = [regex]::Match($Shell.Body, '(?:src|href)="(?<path>/sherlock-api/assets/[^"]+)"')
    if (-not $AssetMatch.Success) { throw 'Domestic gateway shell does not reference a base-safe hashed asset.' }
    $Asset = Invoke-Http 'HEAD' ($DomesticOrigin + $AssetMatch.Groups['path'].Value)
    if ($Asset.StatusCode -ne 200 -or $Asset.Headers['Cache-Control'] -notmatch 'immutable') {
        throw 'Domestic gateway hashed asset validation failed.'
    }

    $DomesticDenied = Invoke-Http 'POST' $GatewayUrl $DomesticOrigin '{"action":"startChildSession"}'
    Assert-ApiError $DomesticDenied 403 'FORMAL_ENTRY_REQUIRED'
    $GitHubAllowed = Invoke-Http 'POST' $GatewayUrl $GitHubOrigin '{"action":"startChildSession"}'
    if ($GitHubAllowed.StatusCode -ne 200 -or -not (($GitHubAllowed.Body | ConvertFrom-Json).ok)) {
        throw 'Existing GitHub formal entry stopped working during candidate deployment.'
    }

    Write-Host 'Domestic gateway candidate deployment succeeded.'
    Write-Host "CandidateUrl=$GatewayUrl/"
    Write-Host 'FormalEntryMode=github-http-only'
    Write-Host 'DomesticFormalSession=blocked-until-cutover'
    Write-Host 'GitHubFormalSession=preserved'
}
catch {
    $OriginalError = $_
    if ($CodeUpdateAttempted -and $null -ne $BackupFunctionRoot) {
        try {
            npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api --dir $BackupFunctionRoot --json | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Rollback code update failed.' }
            Write-Warning 'Candidate validation failed; the previous CloudBase function code was restored.'
        }
        catch { Write-Warning 'Automatic code rollback failed. Immediate CloudBase inspection is required.' }
    }
    throw $OriginalError
}
finally {
    $env:VITE_APP_BASE = $PreviousBase
    $env:VITE_SHERLOCK_API_URL = $PreviousApiUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = $PreviousProbeFlag
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = $PreviousSpeakingDirectFlag
    foreach ($Path in @($BeforeEnvPath, $AfterEnvPath)) {
        if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    }
    if (Test-Path -LiteralPath $BackupRoot) {
        $ResolvedBackup = [IO.Path]::GetFullPath($BackupRoot)
        if ($ResolvedBackup.StartsWith((Join-Path $SafeRoot '_runtime'), [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $BackupRoot -Recurse -Force
        }
    }
}
