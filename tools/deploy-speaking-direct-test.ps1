param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a',
    [ValidateSet('Enable', 'Disable')]
    [string]$Mode = 'Enable'
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

function Copy-Environment([System.Collections.IDictionary]$Source) {
    $Copy = [ordered]@{}
    foreach ($Key in $Source.Keys) { $Copy[$Key] = $Source[$Key] }
    return $Copy
}

function Get-EnvironmentHash([System.Collections.IDictionary]$Values) {
    $Canonical = @($Values.Keys | Sort-Object | ForEach-Object {
        $Encoded = [Convert]::ToBase64String($Utf8NoBom.GetBytes([string]$Values[$_]))
        "$_=$Encoded"
    }) -join "`n"
    $Hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($Hasher.ComputeHash($Utf8NoBom.GetBytes($Canonical)))).Replace('-', '').ToLowerInvariant() }
    finally { $Hasher.Dispose() }
}

function Assert-EnvironmentEqual([System.Collections.IDictionary]$Expected, [System.Collections.IDictionary]$Actual) {
    if ($Expected.Count -ne $Actual.Count) { throw 'Function environment variable count changed unexpectedly.' }
    foreach ($Key in $Expected.Keys) {
        if (-not $Actual.Contains($Key) -or [string]$Actual[$Key] -cne [string]$Expected[$Key]) {
            throw "Function environment variable drift detected: $Key"
        }
    }
}

function Invoke-Function([hashtable]$Event) {
    $Argument = ConvertTo-NativeJsonArgument ($Event | ConvertTo-Json -Compress -Depth 10)
    $Response = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $Argument --json)
    return $Response.data.RetMsg | ConvertFrom-Json
}

function Write-DeployConfig([System.Collections.IDictionary]$Environment, [string]$Path) {
    $Config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'cloudbaserc.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $ApiFunction = $Config.functions | Where-Object { $_.name -eq 'sherlock-api' }
    if ($null -eq $ApiFunction) { throw 'sherlock-api is missing from cloudbaserc.json.' }
    $ApiFunction | Add-Member -NotePropertyName envVariables -NotePropertyValue $Environment -Force
    [IO.File]::WriteAllText($Path, ($Config | ConvertTo-Json -Depth 20), $Utf8NoBom)
}

function Deploy-Function([System.Collections.IDictionary]$Environment, [string]$ConfigPath) {
    Write-DeployConfig $Environment $ConfigPath
    npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $ConfigPath fn deploy sherlock-api --force --install-dependency true --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'sherlock-api deployment failed.' }
}

$Token = [guid]::NewGuid().ToString('N')
$BeforeEnvPath = Join-Path $ProjectRoot ".speaking-direct-before-$Token.tmp"
$AfterEnvPath = Join-Path $ProjectRoot ".speaking-direct-after-$Token.tmp"
$ConfigPath = Join-Path $ProjectRoot ".cloudbaserc.speaking-direct-$Token.json"
$SafeRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
foreach ($Path in @($BeforeEnvPath, $AfterEnvPath, $ConfigPath)) {
    if (-not ([IO.Path]::GetFullPath($Path)).StartsWith($SafeRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary path.' }
}

$Original = $null
$DeploymentAttempted = $false
try {
    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'CloudBase preflight failed.' }

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $BeforeEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $BeforeEnvPath)) { throw 'Unable to pull existing function environment safely.' }
    $Original = Read-EnvFile $BeforeEnvPath
    foreach ($Required in @('PARENT_PASSWORD_SCRYPT', 'PARENT_SESSION_HMAC_KEY', 'SPEAKING_INTERNAL_HMAC_KEY', 'FORMAL_ENABLED')) {
        if (-not $Original.Contains($Required) -or [string]::IsNullOrWhiteSpace([string]$Original[$Required])) {
            throw "Required existing function setting is missing: $Required"
        }
    }
    if ([string]$Original['FORMAL_ENABLED'] -cne 'true') { throw 'Formal state drift detected before TEST-only deployment.' }

    $Desired = Copy-Environment $Original
    if ($Mode -eq 'Enable') { $Desired['SPEAKING_DIRECT_UPLOAD_TEST_ENABLED'] = 'true' }
    else { $Desired.Remove('SPEAKING_DIRECT_UPLOAD_TEST_ENABLED') }

    $DeploymentAttempted = $true
    Deploy-Function $Desired $ConfigPath

    npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $AfterEnvPath --json | Out-Null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $AfterEnvPath)) { throw 'Unable to verify deployed function environment.' }
    $After = Read-EnvFile $AfterEnvPath
    Assert-EnvironmentEqual $Desired $After

    $Health = Invoke-Function @{ action = 'health' }
    $ExpectedEnabled = $Mode -eq 'Enable'
    if (-not $Health.ok -or -not $Health.formal_enabled -or $Health.writes -ne 'formal-and-test' `
        -or [bool]$Health.speaking_direct_upload_test_enabled -ne $ExpectedEnabled) {
        throw 'sherlock-api health state does not match the requested TEST rollout.'
    }

    if ($ExpectedEnabled) {
        $Child = Invoke-Function @{ action = 'startChildSession' }
        $CourseVersion = [string]$Health.speaking_course_versions.S01D39
        $Denied = Invoke-Function @{
            action = 'createSpeakingDirectUpload'; session_token = $Child.session_token
            request = @{
                result_id = 'deployment-boundary-check'; course_id = 'S01D39'; course_version = $CourseVersion
                question_id = 1; attempt = 1; byte_length = 1000; sha256 = ('0' * 64); content_type = 'audio/wav'
            }
        }
        if ($Denied.ok -ne $false -or $Denied.error.code -ne 'UNAUTHORIZED') { throw 'Formal child direct-upload boundary verification failed.' }
    }

    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'CloudBase post-deployment preflight failed.' }
    Write-Host "sherlock-api speaking direct TEST mode: $Mode"
    Write-Host "EnvironmentVariables=$($After.Count)"
    Write-Host "EnvironmentHash=$(Get-EnvironmentHash $After)"
}
catch {
    $OriginalError = $_
    if ($DeploymentAttempted -and $null -ne $Original) {
        try {
            Deploy-Function $Original $ConfigPath
            Write-Warning 'Deployment validation failed; the original function environment was restored and the new code remains dormant.'
        }
        catch { Write-Warning 'Automatic rollback failed. Immediate manual CloudBase inspection is required.' }
    }
    throw $OriginalError
}
finally {
    foreach ($Path in @($BeforeEnvPath, $AfterEnvPath, $ConfigPath)) {
        if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    }
}
