param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a',
    [switch]$StreamlitReadOnlyConfirmed
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
$StreamlitUrl = 'https://sherlock-missions-pesuyw9p75offrqtdadiag.streamlit.app/'
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne 'family24-d7gqb6r6m2d722f7a') {
    throw 'Project root or CloudBase environment mismatch. Refusing to run.'
}
if (-not $StreamlitReadOnlyConfirmed) { throw 'A rendered-browser confirmation of Streamlit read-only mode is required.' }

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

function Invoke-Function([string]$Name, [hashtable]$Event) {
    $Argument = ConvertTo-NativeJsonArgument ($Event | ConvertTo-Json -Compress -Depth 10)
    $Response = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke $Name -d $Argument --json)
    return $Response.data.RetMsg | ConvertFrom-Json
}

function Wait-ForHealth([bool]$FormalEnabled, [string]$Writes) {
    for ($Attempt = 1; $Attempt -le 10; $Attempt++) {
        try {
            $Health = Invoke-Function 'sherlock-api' @{ action = 'health' }
            if ($Health.ok -and $Health.stage -eq 'P5' -and [bool]$Health.formal_enabled -eq $FormalEnabled -and $Health.writes -eq $Writes) {
                return $Health
            }
        }
        catch {
            if ($Attempt -eq 10) { throw }
        }
        if ($Attempt -lt 10) { Start-Sleep -Seconds 3 }
    }
    throw "P5 health state did not propagate: formal_enabled=$FormalEnabled, writes=$Writes"
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

$TemporaryEnv = Join-Path $ProjectRoot ".p5-env.$([guid]::NewGuid().ToString('N')).tmp"
$TemporaryConfig = Join-Path $ProjectRoot ".cloudbaserc.p5.$([guid]::NewGuid().ToString('N')).json"
$Environment = $null
$Config = $null
$FormalSwitchAttempted = $false
$SafeRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
foreach ($Path in @($TemporaryEnv, $TemporaryConfig)) {
    if (-not ([IO.Path]::GetFullPath($Path)).StartsWith($SafeRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary path.' }
}

try {
    $Streamlit = Invoke-WebRequest -Uri $StreamlitUrl -UseBasicParsing -TimeoutSec 30
    if ($Streamlit.StatusCode -ne 200) { throw 'Streamlit is unavailable. CloudBase formal remains disabled.' }

    & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'P5 CloudBase preflight failed.' }

    Push-Location $ProjectRoot
    try {
        Push-Location (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api')
        try { npm run test:coverage; if ($LASTEXITCODE -ne 0) { throw 'sherlock-api tests failed.' } }
        finally { Pop-Location }
        Push-Location (Join-Path $ProjectRoot 'cloudfunctions\score-speaking')
        try { npm run test:coverage; if ($LASTEXITCODE -ne 0) { throw 'score-speaking tests failed.' } }
        finally { Pop-Location }
        python -m unittest tests.test_access_routes
        if ($LASTEXITCODE -ne 0) { throw 'Streamlit read-only tests failed.' }

        # Deploy both functions while FORMAL_ENABLED is still absent/false.
        npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update score-speaking --dir (Join-Path $ProjectRoot 'cloudfunctions\score-speaking') --json
        if ($LASTEXITCODE -ne 0) { throw 'score-speaking P5 code update failed.' }
        npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn code update sherlock-api --dir (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api') --json
        if ($LASTEXITCODE -ne 0) { throw 'sherlock-api P5 code update failed.' }

        $Health = Wait-ForHealth $false 'test-only'

        $env:VITE_CLOUDBASE_ENV_ID = $EnvId
        $env:VITE_CLOUDBASE_ACCESS_KEY = Get-ExistingPublishKey
        $env:VITE_CLOUDBASE_FUNCTION_NAME = 'sherlock-api'
        Push-Location (Join-Path $ProjectRoot 'web')
        try {
            npm run typecheck; if ($LASTEXITCODE -ne 0) { throw 'Web type check failed.' }
            npm run test:coverage; if ($LASTEXITCODE -ne 0) { throw 'Web tests failed.' }
            npm run build; if ($LASTEXITCODE -ne 0) { throw 'Web build failed.' }
            npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId hosting deploy .\dist sherlock-english --json
            if ($LASTEXITCODE -ne 0) { throw 'P5 static hosting deployment failed.' }
        }
        finally { Pop-Location }

        $Site = Invoke-WebRequest -Uri $CloudBaseUrl -UseBasicParsing -TimeoutSec 30
        if ($Site.StatusCode -ne 200 -or $Site.Content -notmatch '<div id="root"></div>') { throw 'P5 site online verification failed.' }

        # Preserve every existing secret while adding the single formal switch.
        npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn env pull sherlock-api --output-file $TemporaryEnv --json | Out-Null
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $TemporaryEnv)) { throw 'Unable to pull existing function environment safely.' }
        $Environment = Read-EnvFile $TemporaryEnv
        foreach ($Required in @('PARENT_PASSWORD_SCRYPT', 'PARENT_SESSION_HMAC_KEY', 'SPEAKING_INTERNAL_HMAC_KEY')) {
            if (-not $Environment.Contains($Required) -or [string]::IsNullOrWhiteSpace($Environment[$Required])) { throw "Required existing function setting is missing: $Required" }
        }
        $Environment['FORMAL_ENABLED'] = 'true'
        $Config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'cloudbaserc.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $ApiFunction = $Config.functions | Where-Object { $_.name -eq 'sherlock-api' }
        $ApiFunction | Add-Member -NotePropertyName envVariables -NotePropertyValue $Environment -Force
        $ApiFunction.description = 'sherlock-english P5 formal and isolated parent test API'
        [IO.File]::WriteAllText($TemporaryConfig, ($Config | ConvertTo-Json -Depth 20), $Utf8NoBom)
        $FormalSwitchAttempted = $true
        npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $TemporaryConfig fn deploy sherlock-api --force --install-dependency true
        if ($LASTEXITCODE -ne 0) { throw 'P5 formal switch deployment failed.' }

        $Health = Wait-ForHealth $true 'formal-and-test'
        $FormalSession = Invoke-Function 'sherlock-api' @{ action = 'startChildSession' }
        if (-not $FormalSession.ok -or $FormalSession.data_kind -ne 'formal' -or [string]::IsNullOrWhiteSpace($FormalSession.session_token)) {
            throw 'P5 formal child session verification failed.'
        }
        $Unauthorized = Invoke-Function 'sherlock-api' @{ action = 'submitListeningResult'; session_token = 'invalid'; submission = @{} }
        if ($Unauthorized.ok -ne $false -or $Unauthorized.error.code -ne 'UNAUTHORIZED') { throw 'P5 session boundary verification failed.' }

        & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
        if ($LASTEXITCODE -ne 0) { throw 'P5 post-cutover family24 verification failed.' }
        Write-Host "P5 formal cutover succeeded: $CloudBaseUrl"
        Write-Host "Streamlit read-only confirmed: $StreamlitUrl"
        Write-Host 'Next: complete one new formal listening course and one new formal speaking course on the real iPad.'
    }
    finally { Pop-Location }
}
catch {
    $OriginalError = $_
    if ($FormalSwitchAttempted -and $null -ne $Environment -and $null -ne $Config) {
        try {
            $Environment['FORMAL_ENABLED'] = 'false'
            $ApiFunction = $Config.functions | Where-Object { $_.name -eq 'sherlock-api' }
            $ApiFunction.envVariables = $Environment
            [IO.File]::WriteAllText($TemporaryConfig, ($Config | ConvertTo-Json -Depth 20), $Utf8NoBom)
            npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $TemporaryConfig fn deploy sherlock-api --force --install-dependency true | Out-Null
            Write-Warning 'P5 validation failed after the formal switch attempt; CloudBase formal was set back to false.'
        }
        catch { Write-Warning 'Automatic CloudBase formal rollback also failed. Immediate manual intervention is required.' }
    }
    throw $OriginalError
}
finally {
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
    if (Test-Path -LiteralPath $TemporaryEnv) { Remove-Item -LiteralPath $TemporaryEnv -Force }
    if (Test-Path -LiteralPath $TemporaryConfig) { Remove-Item -LiteralPath $TemporaryConfig -Force }
}
