param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ExpectedEnvId = 'family24-d7gqb6r6m2d722f7a'
$GatewayUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api'
$AllowedOrigin = 'https://summertxia0306-hue.github.io'
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

function Invoke-HttpApi([hashtable]$Payload, [string]$ClientId) {
    $Body = $Payload | ConvertTo-Json -Compress -Depth 20
    $Response = Invoke-WebRequest -Uri $GatewayUrl -Method Post -UseBasicParsing -TimeoutSec 60 `
        -Headers @{ Origin = $AllowedOrigin; 'X-Sherlock-Client-Id' = $ClientId } `
        -ContentType 'application/json; charset=utf-8' -Body $Body
    if ($Response.StatusCode -ne 200) { throw "HTTP gateway returned $($Response.StatusCode)." }
    return $Response.Content | ConvertFrom-Json
}

function Wait-ForEntryMode([string]$ExpectedMode) {
    for ($Attempt = 1; $Attempt -le 12; $Attempt++) {
        try {
            $Health = Invoke-Function @{ action = 'health' }
            if ($Health.ok -and $Health.formal_enabled -and $Health.writes -eq 'formal-and-test' `
                -and $Health.formal_entry_mode -eq $ExpectedMode) {
                return $Health
            }
        }
        catch {
            if ($Attempt -eq 12) { throw }
        }
        if ($Attempt -lt 12) { Start-Sleep -Seconds 3 }
    }
    throw "Formal entry mode did not propagate: $ExpectedMode"
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

function Copy-Environment([System.Collections.IDictionary]$Source) {
    $Copy = [ordered]@{}
    foreach ($Key in $Source.Keys) { $Copy[$Key] = $Source[$Key] }
    return $Copy
}

function Write-DeployConfig([System.Collections.IDictionary]$Environment, [string]$Path) {
    $Config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'cloudbaserc.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $ApiFunction = $Config.functions | Where-Object { $_.name -eq 'sherlock-api' }
    if ($null -eq $ApiFunction) { throw 'sherlock-api is missing from cloudbaserc.json.' }
    $ApiFunction | Add-Member -NotePropertyName envVariables -NotePropertyValue $Environment -Force
    [IO.File]::WriteAllText($Path, ($Config | ConvertTo-Json -Depth 20), $Utf8NoBom)
}

function Deploy-Environment([System.Collections.IDictionary]$Environment, [string]$ConfigPath) {
    Write-DeployConfig $Environment $ConfigPath
    npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $ConfigPath fn deploy sherlock-api --force --install-dependency true --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'sherlock-api environment deployment failed.' }
}

$RunId = [guid]::NewGuid().ToString('N')
$BeforeEnvPath = Join-Path $ProjectRoot ".formal-entry-before-$RunId.tmp"
$ConfigPath = Join-Path $ProjectRoot ".cloudbaserc.formal-entry-$RunId.json"
$SafeRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
foreach ($Path in @($BeforeEnvPath, $ConfigPath)) {
    if (-not ([IO.Path]::GetFullPath($Path)).StartsWith($SafeRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Unsafe temporary path.'
    }
}

$OriginalEnvironment = $null
$SwitchAttempted = $false
try {
    $InitialHealth = Wait-ForEntryMode 'dual'
    $ClientId = "cutover-$RunId"
    $PreSwitchSession = Invoke-HttpApi @{ action = 'startChildSession' } $ClientId
    if (-not $PreSwitchSession.ok -or [string]::IsNullOrWhiteSpace($PreSwitchSession.session_token)) {
        throw 'HTTP formal session could not be created before the switch.'
    }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $BeforeEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $BeforeEnvPath)) {
        throw 'Unable to pull the existing function environment safely.'
    }
    $OriginalEnvironment = Read-EnvFile $BeforeEnvPath
    foreach ($Required in @('PARENT_PASSWORD_SCRYPT', 'PARENT_SESSION_HMAC_KEY', 'SPEAKING_INTERNAL_HMAC_KEY', 'FORMAL_ENABLED')) {
        if (-not $OriginalEnvironment.Contains($Required) -or [string]::IsNullOrWhiteSpace([string]$OriginalEnvironment[$Required])) {
            throw "Required existing function setting is missing: $Required"
        }
    }
    if ([string]$OriginalEnvironment['FORMAL_ENABLED'] -cne 'true') {
        throw 'Formal learning is not enabled; refusing to change its entry mode.'
    }

    $DesiredEnvironment = Copy-Environment $OriginalEnvironment
    $DesiredEnvironment['FORMAL_ENTRY_MODE'] = 'github-http-only'
    $SwitchAttempted = $true
    Deploy-Environment $DesiredEnvironment $ConfigPath

    $FinalHealth = Wait-ForEntryMode 'github-http-only'

    $Progress = Invoke-HttpApi @{
        action = 'getFormalProgress'
        session_token = $PreSwitchSession.session_token
    } $ClientId
    if (-not $Progress.ok) { throw 'The pre-switch GitHub HTTP session stopped working after cutover.' }

    $NewSession = Invoke-HttpApi @{ action = 'startChildSession' } $ClientId
    if (-not $NewSession.ok -or [string]::IsNullOrWhiteSpace($NewSession.session_token)) {
        throw 'A new GitHub HTTP formal session could not be created after cutover.'
    }

    $HiddenCourse = Invoke-HttpApi @{
        action = 'submitListeningResult'
        session_token = $NewSession.session_token
        submission = @{
            result_id = [guid]::NewGuid().ToString()
            course_id = 'L4A-T1-W01-D01'
        }
    } $ClientId
    if ($HiddenCourse.ok -ne $false -or $HiddenCourse.error.code -ne 'COURSE_NOT_FORMAL') {
        throw 'A withdrawn term course was not blocked from formal submission.'
    }

    $OldEntry = Invoke-Function @{ action = 'startChildSession' }
    if ($OldEntry.ok -ne $false -or $OldEntry.error.code -ne 'FORMAL_ENTRY_REQUIRED') {
        throw 'The legacy CloudBase Event formal entry was not blocked.'
    }

    Write-Host 'Formal entry cutover succeeded.'
    Write-Host "FormalEntryMode=$($FinalHealth.formal_entry_mode)"
    Write-Host 'GitHubHttpSession=allowed'
    Write-Host 'LegacyCloudBaseEventSession=blocked'
    Write-Host 'WithdrawnTermCourses=blocked'
}
catch {
    $OriginalError = $_
    if ($SwitchAttempted -and $null -ne $OriginalEnvironment) {
        try {
            Deploy-Environment $OriginalEnvironment $ConfigPath
            Write-Warning 'Cutover validation failed; the original function environment was restored.'
        }
        catch {
            Write-Warning 'Automatic rollback failed. Immediate CloudBase inspection is required.'
        }
    }
    throw $OriginalError
}
finally {
    foreach ($Path in @($BeforeEnvPath, $ConfigPath)) {
        if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    }
}
