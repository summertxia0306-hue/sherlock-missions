param([string]$EnvId = 'family24-d7gqb6r6m2d722f7a')

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$BaseUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
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

function Invoke-Sherlock([hashtable]$Event) {
    $Event.userInfo = @{ openId = 'p6-online-formal-boundary' }
    $Argument = ConvertTo-NativeJsonArgument ($Event | ConvertTo-Json -Compress -Depth 10)
    $Response = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $Argument --json)
    return $Response.data.RetMsg | ConvertFrom-Json
}

$Health = Invoke-Sherlock @{ action = 'health' }
if (-not $Health.ok -or $Health.stage -ne 'P5' -or -not $Health.formal_enabled -or $Health.writes -ne 'formal-and-test') {
    throw 'CloudBase health boundary is not P5 formal-and-test.'
}

$Session = Invoke-Sherlock @{ action = 'startChildSession' }
if (-not $Session.ok -or $Session.data_kind -ne 'formal' -or [string]::IsNullOrWhiteSpace($Session.session_token)) {
    throw 'Unable to establish the formal boundary probe session.'
}

$ListeningCourse = Invoke-RestMethod -Uri ([Uri]::new([Uri]$BaseUrl, "content/listening/L4A-T1-W01-D01.json?p6=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"))
$Listening = Invoke-Sherlock @{
    action = 'submitListeningResult'
    session_token = $Session.session_token
    submission = @{
        result_id = [guid]::NewGuid().ToString()
        student_id = 'sherlock'
        course_id = 'L4A-T1-W01-D01'
        course_version = $ListeningCourse.course_version
    }
}
if ($Listening.ok -ne $false -or $Listening.error.code -ne 'COURSE_NOT_FORMAL') {
    throw 'Hidden listening course was not rejected at the formal boundary.'
}

$SpeakingCourse = Invoke-RestMethod -Uri ([Uri]::new([Uri]$BaseUrl, "content/speaking/S4A-T1-W01-D01.json?p6=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"))
$Speaking = Invoke-Sherlock @{
    action = 'scoreSpeakingTake'
    session_token = $Session.session_token
    request = @{
        result_id = [guid]::NewGuid().ToString()
        course_id = 'S4A-T1-W01-D01'
        course_version = $SpeakingCourse.course_version
        question_id = 1
        attempt = 1
        wav_base64 = [Convert]::ToBase64String((New-Object byte[] 5000))
    }
}
if ($Speaking.ok -ne $false -or $Speaking.error.code -ne 'COURSE_NOT_FORMAL') {
    throw 'Hidden speaking course was not rejected at the formal boundary.'
}

Write-Host 'P6 CloudBase boundary verified: P5 healthy; hidden listening and speaking courses reject formal writes.'
