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
$ServiceName = 'sherlock-english'
$DeployPath = '/sherlock-english'
$ExpectedDomain = 'sherlock-english-family24-d7gqb6r6m2d722f7a.webapps.tcloudbase.com'
$WebAppOrigin = "https://$ExpectedDomain"
$CandidateUrl = "$WebAppOrigin$DeployPath/"
$GatewayUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'
$GitHubOrigin = 'https://summertxia0306-hue.github.io'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne $ExpectedEnvId) {
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

function Read-EnvFile([string]$Path) {
    $Values = [ordered]@{}
    foreach ($Line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($Line) -or $Line.TrimStart().StartsWith('#')) { continue }
        $Parts = $Line -split '=', 2
        if ($Parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($Parts[0])) { throw 'Pulled function environment file is malformed.' }
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

function Invoke-Http([string]$Method, [string]$Url, [string]$Origin = '', [string]$Body = '') {
    $Handler = New-Object System.Net.Http.HttpClientHandler
    $Handler.AllowAutoRedirect = $false
    $Client = New-Object System.Net.Http.HttpClient($Handler)
    $Request = $null
    try {
        $Request = New-Object System.Net.Http.HttpRequestMessage([System.Net.Http.HttpMethod]::new($Method), $Url)
        if (-not [string]::IsNullOrWhiteSpace($Origin)) { $Request.Headers.TryAddWithoutValidation('Origin', $Origin) | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($Body)) {
            $Request.Headers.TryAddWithoutValidation('X-Sherlock-Client-Id', 'webapp-candidate-20260902') | Out-Null
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
    if ($Payload.ok -ne $false -or $Payload.error.code -ne $ErrorCode) { throw "Expected API error $ErrorCode." }
}

function Find-DownloadedFunctionRoot([string]$Root) {
    $Package = Get-ChildItem -LiteralPath $Root -Recurse -File -Filter 'package.json' |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.Directory.FullName 'index.js') } |
        Select-Object -First 1
    if ($null -eq $Package) { throw 'Downloaded CloudBase backup does not contain the function root.' }
    return $Package.Directory.FullName
}

function Get-AppInfo([string]$Name) {
    return ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb app info $Name -e $EnvId --json)
}

function Wait-ForWebAppApi {
    $Last = $null
    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {
        try {
            $Last = Invoke-Http 'POST' $GatewayUrl $WebAppOrigin '{"action":"health"}'
            if ($Last.StatusCode -eq 200 -and ($Last.Body | ConvertFrom-Json).formal_entry_mode -eq 'github-http-only') { return }
        }
        catch {
            if ($Attempt -eq 12) { throw }
        }
        if ($Attempt -lt 12) { Start-Sleep -Seconds 3 }
    }
    throw "Web App API origin did not propagate. LastStatus=$($Last.StatusCode)"
}

function Wait-ForWebAppShell {
    $Last = $null
    for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
        try {
            $Last = Invoke-Http 'GET' $CandidateUrl
            $Type = if ($Last.Headers.ContainsKey('Content-Type')) { $Last.Headers['Content-Type'] } else { '' }
            $Disposition = if ($Last.Headers.ContainsKey('Content-Disposition')) { $Last.Headers['Content-Disposition'] } else { '' }
            if ($Last.StatusCode -eq 200 -and $Type -match '^text/html' `
                -and $Disposition -notmatch '^attachment' -and $Last.Body -match '/sherlock-english/assets/') { return $Last }
        }
        catch {
            if ($Attempt -eq 20) { throw }
        }
        if ($Attempt -lt 20) { Start-Sleep -Seconds 3 }
    }
    $LastType = if ($null -ne $Last -and $Last.Headers.ContainsKey('Content-Type')) { $Last.Headers['Content-Type'] } else { 'missing' }
    $LastDisposition = if ($null -ne $Last -and $Last.Headers.ContainsKey('Content-Disposition')) { $Last.Headers['Content-Disposition'] } else { 'none' }
    throw "Web App shell did not become usable. Status=$($Last.StatusCode) ContentType=$LastType ContentDisposition=$LastDisposition"
}

$RunId = [guid]::NewGuid().ToString('N')
$BeforeEnvPath = Join-Path $ProjectRoot ".webapp-before-$RunId.tmp"
$AfterEnvPath = Join-Path $ProjectRoot ".webapp-after-$RunId.tmp"
$BackupRoot = Join-Path $ProjectRoot "_runtime\webapp-api-backup-$RunId"
$AppConfigPath = Join-Path $ProjectRoot ".cloudbaserc.webapp-$RunId.json"
$SafeRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
foreach ($Path in @($BeforeEnvPath, $AfterEnvPath, $BackupRoot, $AppConfigPath)) {
    if (-not ([IO.Path]::GetFullPath($Path)).StartsWith($SafeRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe deployment path.' }
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

    $Apps = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb app list -e $EnvId --json)
    if (@($Apps.data | Where-Object { $_.serviceName -eq $ServiceName }).Count -ne 0) {
        throw 'A sherlock-english Web App already exists; refusing an unreviewed overwrite.'
    }
    $FamilyBefore = (Get-AppInfo 'family24-web').data
    if ($FamilyBefore.latestStatus -ne 'SUCCESS') { throw 'Existing family24-web is not healthy before candidate deployment.' }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $BeforeEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $BeforeEnvPath)) { throw 'Unable to capture the current function environment.' }
    $BeforeEnvironment = Read-EnvFile $BeforeEnvPath
    if ([string]$BeforeEnvironment['FORMAL_ENTRY_MODE'] -cne 'github-http-only') {
        throw 'Web App candidate requires the existing github-http-only safety mode.'
    }

    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code download sherlock-api $BackupRoot --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Unable to download the current function code for rollback.' }
    $BackupFunctionRoot = Find-DownloadedFunctionRoot $BackupRoot

    $env:VITE_APP_BASE = '/sherlock-english/'
    $env:VITE_SHERLOCK_API_URL = $GatewayUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = 'true'
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = 'true'
    Push-Location (Join-Path $ProjectRoot 'web')
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Web App candidate production build failed.' }
    }
    finally { Pop-Location }

    $CodeUpdateAttempted = $true
    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api `
        --dir (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api') --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Web App API candidate code deployment failed.' }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $AfterEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $AfterEnvPath)) { throw 'Unable to verify function environment after deployment.' }
    Assert-EnvironmentEqual $BeforeEnvironment (Read-EnvFile $AfterEnvPath)
    Wait-ForWebAppApi
    $WebAppDenied = Invoke-Http 'POST' $GatewayUrl $WebAppOrigin '{"action":"startChildSession"}'
    Assert-ApiError $WebAppDenied 403 'FORMAL_ENTRY_REQUIRED'
    $GitHubAllowed = Invoke-Http 'POST' $GatewayUrl $GitHubOrigin '{"action":"startChildSession"}'
    if ($GitHubAllowed.StatusCode -ne 200 -or -not (($GitHubAllowed.Body | ConvertFrom-Json).ok)) {
        throw 'Existing GitHub formal entry stopped working during Web App candidate deployment.'
    }

    $AppConfig = [ordered]@{
        '$schema' = 'https://static.cloudbase.net/cli/cloudbaserc.schema.json'
        envId = $EnvId
        app = [ordered]@{
            serviceName = $ServiceName; root = './web/dist'; framework = 'static'
            installCommand = ''; buildCommand = ''; outputDir = './'; deployPath = $DeployPath
        }
    }
    [IO.File]::WriteAllText($AppConfigPath, ($AppConfig | ConvertTo-Json -Depth 10), $Utf8NoBom)
    npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $AppConfigPath app deploy sherlock-english `
        --framework static --cwd web/dist --output-dir ./ --deploy-path /sherlock-english --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Independent Sherlock Web App deployment failed.' }

    $Info = (Get-AppInfo $ServiceName).data
    if ($Info.latestStatus -ne 'SUCCESS' -or $Info.domain -ne $ExpectedDomain -or $Info.appPath -ne $DeployPath) {
        throw 'Independent Sherlock Web App identity or deployment state is unexpected.'
    }
    $FamilyAfter = (Get-AppInfo 'family24-web').data
    if ($FamilyAfter.domain -ne $FamilyBefore.domain -or $FamilyAfter.latestVersionName -ne $FamilyBefore.latestVersionName `
        -or $FamilyAfter.latestStatus -ne 'SUCCESS') {
        throw 'Existing family24-web changed during the isolated deployment.'
    }

    $Shell = Wait-ForWebAppShell
    $AssetMatch = [regex]::Match($Shell.Body, '(?:src|href)="(?<path>/sherlock-english/assets/[^"]+)"')
    if (-not $AssetMatch.Success) { throw 'Web App shell does not reference the isolated hashed asset path.' }
    $Asset = Invoke-Http 'HEAD' ($WebAppOrigin + $AssetMatch.Groups['path'].Value)
    if ($Asset.StatusCode -ne 200) { throw 'Web App hashed asset validation failed.' }
    foreach ($Path in @('manifest.webmanifest', 'sw.js')) {
        $Resource = Invoke-Http 'GET' "$CandidateUrl$Path"
        if ($Resource.StatusCode -ne 200) { throw "Web App resource validation failed: $Path" }
    }
    $Health = Invoke-Http 'POST' $GatewayUrl $WebAppOrigin '{"action":"health"}'
    if ($Health.StatusCode -ne 200 -or ($Health.Body | ConvertFrom-Json).formal_entry_mode -ne 'github-http-only') {
        throw 'Web App cross-origin API validation failed.'
    }

    Write-Host 'Independent Sherlock Web App candidate deployment succeeded.'
    Write-Host "CandidateUrl=$CandidateUrl"
    Write-Host "ServiceName=$ServiceName"
    Write-Host 'FormalEntryMode=github-http-only'
    Write-Host 'WebAppFormalSession=blocked-until-cutover'
    Write-Host 'GitHubFormalSession=preserved'
    Write-Host "Family24Version=$($FamilyAfter.latestVersionName)"
}
catch {
    $OriginalError = $_
    if ($CodeUpdateAttempted -and $null -ne $BackupFunctionRoot) {
        try {
            npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api --dir $BackupFunctionRoot --json | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'Rollback code update failed.' }
            Write-Warning 'Web App candidate validation failed; the previous API function code was restored.'
        }
        catch { Write-Warning 'Automatic API rollback failed. Immediate CloudBase inspection is required.' }
    }
    throw $OriginalError
}
finally {
    $env:VITE_APP_BASE = $PreviousBase
    $env:VITE_SHERLOCK_API_URL = $PreviousApiUrl
    $env:VITE_DIRECT_UPLOAD_PROBE = $PreviousProbeFlag
    $env:VITE_SPEAKING_DIRECT_UPLOAD_TEST = $PreviousSpeakingDirectFlag
    foreach ($Path in @($BeforeEnvPath, $AfterEnvPath, $AppConfigPath)) {
        if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    }
    if (Test-Path -LiteralPath $BackupRoot) {
        $ResolvedBackup = [IO.Path]::GetFullPath($BackupRoot)
        if ($ResolvedBackup.StartsWith((Join-Path $SafeRoot '_runtime'), [StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $BackupRoot -Recurse -Force
        }
    }
}
