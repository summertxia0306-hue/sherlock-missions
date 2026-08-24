param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Keep native CloudBase CLI JSON intact under Windows PowerShell 5.1.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne 'family24-d7gqb6r6m2d722f7a') {
    throw 'Project root or CloudBase environment mismatch. Refusing to run.'
}

& (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
if ($LASTEXITCODE -ne 0) {
    throw 'P1 CloudBase read-only preflight failed.'
}

function ConvertFrom-TcbOutput([object[]]$Lines) {
    $Joined = $Lines -join "`n"
    $Start = $Joined.IndexOf('{')
    if ($Start -lt 0) {
        throw 'CloudBase CLI did not return JSON.'
    }
    $Object = $Joined.Substring($Start) | ConvertFrom-Json
    if ($Object.PSObject.Properties['error']) {
        throw "CloudBase operation failed: $($Object.error.code)"
    }
    return $Object
}

function ConvertTo-NativeJsonArgument([string]$Json) {
    if ($PSVersionTable.PSVersion.Major -le 5) {
        return $Json.Replace('"', '\"')
    }
    return $Json
}

function Invoke-TcbApi([string]$Action, [hashtable]$Body) {
    $BodyJson = $Body | ConvertTo-Json -Compress -Depth 10
    $BodyArgument = ConvertTo-NativeJsonArgument $BodyJson
    return ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb api tcb $Action --body $BodyArgument --json)
}

function ConvertTo-PlainText([Security.SecureString]$SecureValue) {
    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer)
    }
}

$First = Read-Host 'Enter the parent TEST acceptance password (at least 12 characters)' -AsSecureString
$Second = Read-Host 'Enter the same password again' -AsSecureString
$Password = ConvertTo-PlainText $First
$PasswordAgain = ConvertTo-PlainText $Second
if ($Password -cne $PasswordAgain) {
    throw 'The two passwords do not match.'
}
if ($Password.Length -lt 12 -or $Password.Length -gt 256) {
    throw 'Password length must be between 12 and 256 characters.'
}

$TemporaryConfig = Join-Path $ProjectRoot ".cloudbaserc.p1.$([guid]::NewGuid().ToString('N')).json"
$TemporaryRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
if (-not ([IO.Path]::GetFullPath($TemporaryConfig)).StartsWith($TemporaryRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Unsafe temporary configuration path.'
}

try {
    $env:P1_PARENT_PASSWORD = $Password
    $SecretLines = @(node (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api\generate-secret.js'))
    if ($LASTEXITCODE -ne 0) {
        throw 'Password hash generation failed.'
    }
    $Secrets = @{}
    foreach ($Line in $SecretLines) {
        $Parts = $Line -split '=', 2
        if ($Parts.Count -eq 2) {
            $Secrets[$Parts[0]] = $Parts[1]
        }
    }
    if (-not $Secrets.PARENT_PASSWORD_SCRYPT -or -not $Secrets.PARENT_SESSION_HMAC_KEY) {
        throw 'Password hash or session key generation failed.'
    }

    $Config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'cloudbaserc.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $Config.functions[0] | Add-Member -NotePropertyName envVariables -NotePropertyValue @{
        PARENT_PASSWORD_SCRYPT = $Secrets.PARENT_PASSWORD_SCRYPT
        PARENT_SESSION_HMAC_KEY = $Secrets.PARENT_SESSION_HMAC_KEY
        SESSION_TTL_SECONDS = '7200'
        AUTH_MAX_FAILURES = '5'
        AUTH_WINDOW_SECONDS = '900'
    } -Force
    $ConfigJson = $Config | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($TemporaryConfig, $ConfigJson, $Utf8NoBom)

    Push-Location $ProjectRoot
    try {
        npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $TemporaryConfig fn deploy sherlock-api --force --install-dependency true
        if ($LASTEXITCODE -ne 0) {
            throw 'sherlock-api secret configuration deployment failed.'
        }

        $Caller = 'p1-script-acceptance'
        $AuthEvent = @{ action = 'parentAuth'; password = $Password; userInfo = @{ openId = $Caller } } | ConvertTo-Json -Compress -Depth 6
        $AuthEventArgument = ConvertTo-NativeJsonArgument $AuthEvent
        $AuthInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $AuthEventArgument --json)
        $AuthResult = $AuthInvoke.data.RetMsg | ConvertFrom-Json
        if (-not $AuthResult.ok -or $AuthResult.data_kind -ne 'test') {
            throw 'Parent TEST session verification failed.'
        }

        $Now = [DateTime]::UtcNow.ToString('o')
        $SubmitEvent = @{
            action = 'submitResult'
            session_token = $AuthResult.session_token
            userInfo = @{ openId = $Caller }
            result = @{
                student_id = 'p1-parent-acceptance'
                module_type = 'listening'
                course_id = 'P1-SMOKE'
                data_kind = 'formal'
                course_version = 'p1'
                started_at = $Now
                submitted_at = $Now
                duration_seconds = 0
                device_info = @{ platform = 'p1-deploy-script' }
                payload = @{ check = 'p1-cloudbase-test-write' }
            }
        } | ConvertTo-Json -Compress -Depth 10
        $SubmitEventArgument = ConvertTo-NativeJsonArgument $SubmitEvent
        $SubmitInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $SubmitEventArgument --json)
        $SubmitResult = $SubmitInvoke.data.RetMsg | ConvertFrom-Json
        if (-not $SubmitResult.ok -or $SubmitResult.data_kind -ne 'test' -or $SubmitResult.formal_completion_eligible -ne $false) {
            throw 'Server-side TEST enforcement verification failed.'
        }

        $PublishKey = Invoke-TcbApi 'CreateApiKey' @{ EnvId = $EnvId; KeyType = 'publish_key'; KeyName = 'sherlock-english-p1' }
        if ([string]::IsNullOrWhiteSpace($PublishKey.data.ApiKey)) {
            throw 'Could not obtain the frontend publish key.'
        }

        $env:VITE_CLOUDBASE_ENV_ID = $EnvId
        $env:VITE_CLOUDBASE_ACCESS_KEY = $PublishKey.data.ApiKey
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
            if ($LASTEXITCODE -ne 0) { throw 'P1 static hosting deployment failed.' }
        }
        finally {
            Pop-Location
        }

        $TestUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
        $Response = Invoke-WebRequest -Uri $TestUrl -UseBasicParsing -TimeoutSec 30
        if ($Response.StatusCode -ne 200 -or $Response.Content -notmatch '<div id="root"></div>') {
            throw 'P1 TEST site online verification failed.'
        }
        Write-Host "P1 TEST deployment succeeded: $TestUrl"
        Write-Host "TEST result ID: $($SubmitResult.result_id)"
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:P1_PARENT_PASSWORD = $null
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
    $Password = $null
    $PasswordAgain = $null
    if (Test-Path -LiteralPath $TemporaryConfig) {
        Remove-Item -LiteralPath $TemporaryConfig -Force
    }
}
