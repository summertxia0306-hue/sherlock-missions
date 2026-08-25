param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a',
    [string]$CourseId = 'S01D39',
    [int]$QuestionId = 1
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ProbeRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$ProbeLeaf = '.p3-probe-' + [guid]::NewGuid().ToString('N')
$ProbeDirectory = Join-Path $ProbeRoot $ProbeLeaf
$ProbeArgumentPrefix = "@tools/$ProbeLeaf/"
$Utf8NoBom = [Text.UTF8Encoding]::new($false)

function ConvertFrom-TcbJsonOutput {
    param([object[]]$Lines)
    $TextLines = @($Lines | ForEach-Object { $_.ToString() })
    $Start = ($TextLines | Select-String -Pattern '^\s*\{' | Select-Object -First 1).LineNumber
    if (-not $Start) { throw 'CloudBase CLI did not return JSON.' }
    return (($TextLines[($Start - 1)..($TextLines.Count - 1)] -join "`n") | ConvertFrom-Json)
}

function Find-Ffmpeg {
    $Command = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }
    $Bundled = 'C:\Users\summe\AppData\Local\Programs\Python\Python312\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
    if (Test-Path -LiteralPath $Bundled) { return $Bundled }
    throw 'ffmpeg was not found.'
}

[IO.Directory]::CreateDirectory($ProbeDirectory) | Out-Null
try {
    $CoursePath = Join-Path $ProjectRoot "content\speaking\$CourseId.json"
    $PublicCoursePath = Join-Path $ProjectRoot "web\public\content\speaking\$CourseId.json"
    $Course = Get-Content -LiteralPath $CoursePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $PublicCourse = Get-Content -LiteralPath $PublicCoursePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $Question = $Course.questions | Where-Object id -eq $QuestionId | Select-Object -First 1
    if (-not $Question -or $Question.type -ne 'repeat') { throw 'The probe requires a repeat question.' }

    $AudioPath = Join-Path $ProjectRoot $Question.audio.Replace('/', '\')
    $WavPath = Join-Path $ProbeDirectory 'probe-16k.wav'
    & (Find-Ffmpeg) -hide_banner -loglevel error -y -i $AudioPath -ac 1 -ar 16000 -c:a pcm_s16le $WavPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $WavPath)) { throw 'Audio conversion failed.' }

    $BoundaryPayload = [ordered]@{
        result_id = 'probe-boundary'
        course_id = $CourseId
        course_version = [string]$PublicCourse.course_version
        question_id = $QuestionId
        attempt = 1
        target_text = [string]$Question.text
        session_marker = '0000000000000000'
        wav_base64 = 'A' * 1024
    }
    $BoundaryPayloadPath = Join-Path $ProbeDirectory 'boundary-payload.json'
    $BoundaryEventPath = Join-Path $ProbeDirectory 'boundary-event.json'
    [IO.File]::WriteAllText($BoundaryPayloadPath, ($BoundaryPayload | ConvertTo-Json -Compress -Depth 10), $Utf8NoBom)
    node (Join-Path $PSScriptRoot 'create-p3-probe-event.mjs') $BoundaryPayloadPath $BoundaryEventPath $EnvId
    if ($LASTEXITCODE -ne 0) { throw 'Boundary request signing failed.' }
    Push-Location $ProjectRoot
    try { $BoundaryInvoke = ConvertFrom-TcbJsonOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke score-speaking -d ($ProbeArgumentPrefix + 'boundary-event.json') --json 2>&1) }
    finally { Pop-Location }
    $BoundaryResult = $BoundaryInvoke.data.RetMsg
    if ($BoundaryResult -is [string]) { $BoundaryResult = $BoundaryResult | ConvertFrom-Json }
    if ($BoundaryResult.error.code -ne 'INVALID_AUDIO') {
        Write-Host "P3 signer boundary failed: $($BoundaryResult.error.code)"
        throw 'The deployed scorer did not accept the live internal signature.'
    }

    $Payload = [ordered]@{
        result_id = 'probe-' + [guid]::NewGuid().ToString('N')
        course_id = $CourseId
        course_version = [string]$PublicCourse.course_version
        question_id = $QuestionId
        attempt = 1
        target_text = [string]$Question.text
        session_marker = '0000000000000000'
        wav_base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($WavPath))
    }
    $PayloadPath = Join-Path $ProbeDirectory 'payload.json'
    $EventPath = Join-Path $ProbeDirectory 'event.json'
    [IO.File]::WriteAllText($PayloadPath, ($Payload | ConvertTo-Json -Compress -Depth 10), $Utf8NoBom)
    node (Join-Path $PSScriptRoot 'create-p3-probe-event.mjs') $PayloadPath $EventPath $EnvId
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $EventPath)) { throw 'Probe request signing failed.' }

    $Result = $null
    foreach ($AttemptNumber in 1..3) {
        Push-Location $ProjectRoot
        try { $Invoke = ConvertFrom-TcbJsonOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke score-speaking -d ($ProbeArgumentPrefix + 'event.json') --json 2>&1) }
        finally { Pop-Location }
        $Result = $Invoke.data.RetMsg
        if ($Result -is [string]) { $Result = $Result | ConvertFrom-Json }
        if ($Result.ok) { break }
        if ($AttemptNumber -lt 3) { Start-Sleep -Seconds 5 }
    }
    if (-not $Result.ok) {
        Write-Host "P3 live scorer probe failed: $($Result.error.code)"
        throw 'P3 live scorer probe did not return a score.'
    }

    $Stars = if ($Result.is_rejected) { 0 } elseif ([double]$Result.total -ge 75) { 3 } elseif ([double]$Result.total -ge 50) { 2 } else { 1 }
    [pscustomobject]@{
        Probe = 'PASSED'
        Course = $Result.course_id
        Question = $Result.question_id
        ProviderScore = [math]::Round([double]$Result.total, 1)
        Stars = $Stars
        Rejected = [bool]$Result.is_rejected
        RecordingSaved = ([string]$Result.recording_path -like 'sherlock-english/test/test/*')
    } | Format-List
}
finally {
    $ResolvedProbe = [IO.Path]::GetFullPath($ProbeDirectory)
    if ($ResolvedProbe.StartsWith($ProbeRoot, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path -Leaf $ResolvedProbe) -like '.p3-probe-*') {
        Remove-Item -LiteralPath $ResolvedProbe -Recurse -Force -ErrorAction SilentlyContinue
    }
}
