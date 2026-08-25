param([string]$EnvId = 'family24-d7gqb6r6m2d722f7a')

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot -or $EnvId -ne 'family24-d7gqb6r6m2d722f7a') { throw 'Project root or CloudBase environment mismatch. Refusing to run.' }

& (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
if ($LASTEXITCODE -ne 0) { throw 'P3 CloudBase read-only preflight failed.' }

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
    if ([string]::IsNullOrWhiteSpace($ScriptPath)) { throw 'Current P2 site bundle was not found.' }
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
    throw 'Existing CloudBase publish key could not be recovered from the public P2 bundle.'
}

function Read-DeploymentSecrets {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $Form = New-Object System.Windows.Forms.Form
    $Form.Text = 'P3 TEST deployment credentials'
    $Form.ClientSize = New-Object System.Drawing.Size(620, 385)
    $Form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $Form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $Form.MaximizeBox = $false
    $Form.MinimizeBox = $false
    $Form.TopMost = $true

    $Introduction = New-Object System.Windows.Forms.Label
    $Introduction.Location = New-Object System.Drawing.Point(24, 18)
    $Introduction.Size = New-Object System.Drawing.Size(570, 42)
    $Introduction.Text = "Paste with Ctrl+V. Enter each value once. Values are masked. Cancel prevents deployment."
    $Form.Controls.Add($Introduction)

    $Specifications = @(
        [pscustomobject]@{ Key = 'ParentPassword'; Label = 'Parent TEST password'; MinimumLength = 12 },
        [pscustomobject]@{ Key = 'XfAppId'; Label = 'XF_APPID'; MinimumLength = 4 },
        [pscustomobject]@{ Key = 'XfApiKey'; Label = 'XF_API_KEY'; MinimumLength = 8 },
        [pscustomobject]@{ Key = 'XfApiSecret'; Label = 'XF_API_SECRET'; MinimumLength = 8 }
    )
    $TextBoxes = @{}
    $Y = 72
    foreach ($Specification in $Specifications) {
        $Label = New-Object System.Windows.Forms.Label
        $Label.Location = New-Object System.Drawing.Point(24, $Y)
        $Label.Size = New-Object System.Drawing.Size(200, 24)
        $Label.Text = $Specification.Label
        $Form.Controls.Add($Label)

        $TextBox = New-Object System.Windows.Forms.TextBox
        $TextBox.Location = New-Object System.Drawing.Point(230, ($Y - 3))
        $TextBox.Size = New-Object System.Drawing.Size(360, 26)
        $TextBox.UseSystemPasswordChar = $true
        $TextBox.ShortcutsEnabled = $true
        $TextBox.MaxLength = 512
        $Form.Controls.Add($TextBox)
        $TextBoxes[$Specification.Key] = $TextBox
        $Y += 55
    }

    $StartButton = New-Object System.Windows.Forms.Button
    $StartButton.Location = New-Object System.Drawing.Point(386, 320)
    $StartButton.Size = New-Object System.Drawing.Size(98, 34)
    $StartButton.Text = 'Start deployment'
    $StartButton.Add_Click({
        foreach ($Specification in $Specifications) {
            $Length = $TextBoxes[$Specification.Key].Text.Length
            if ($Length -lt $Specification.MinimumLength -or $Length -gt 512) {
                [void][System.Windows.Forms.MessageBox]::Show(
                    "$($Specification.Label) length must be between $($Specification.MinimumLength) and 512 characters.",
                    'Check the input',
                    [System.Windows.Forms.MessageBoxButtons]::OK,
                    [System.Windows.Forms.MessageBoxIcon]::Warning
                )
                $TextBoxes[$Specification.Key].Focus()
                return
            }
        }
        $Form.DialogResult = [System.Windows.Forms.DialogResult]::OK
        $Form.Close()
    })
    $Form.Controls.Add($StartButton)

    $CancelButton = New-Object System.Windows.Forms.Button
    $CancelButton.Location = New-Object System.Drawing.Point(492, 320)
    $CancelButton.Size = New-Object System.Drawing.Size(98, 34)
    $CancelButton.Text = 'Cancel'
    $CancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $Form.Controls.Add($CancelButton)
    $Form.AcceptButton = $StartButton
    $Form.CancelButton = $CancelButton

    $Result = $Form.ShowDialog()
    if ($Result -ne [System.Windows.Forms.DialogResult]::OK) {
        $Form.Dispose()
        throw 'Credential entry cancelled. No CloudBase changes were made.'
    }
    $Values = [pscustomobject]@{
        ParentPassword = $TextBoxes.ParentPassword.Text
        XfAppId = $TextBoxes.XfAppId.Text
        XfApiKey = $TextBoxes.XfApiKey.Text
        XfApiSecret = $TextBoxes.XfApiSecret.Text
    }
    foreach ($TextBox in $TextBoxes.Values) { $TextBox.Clear() }
    $Form.Dispose()
    return $Values
}

$TemporaryConfig = Join-Path $ProjectRoot ".cloudbaserc.p3.$([guid]::NewGuid().ToString('N')).json"
$TemporaryRoot = [IO.Path]::GetFullPath($ProjectRoot + [IO.Path]::DirectorySeparatorChar)
if (-not ([IO.Path]::GetFullPath($TemporaryConfig)).StartsWith($TemporaryRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary configuration path.' }

$Password = $null
$XfAppId = $null
$XfApiKey = $null
$XfApiSecret = $null
$InternalKey = $null
$Credentials = $null
try {
    $Credentials = Read-DeploymentSecrets
    $Password = $Credentials.ParentPassword
    $XfAppId = $Credentials.XfAppId
    $XfApiKey = $Credentials.XfApiKey
    $XfApiSecret = $Credentials.XfApiSecret
    $Credentials = $null

    $env:P1_PARENT_PASSWORD = $Password
    $SecretLines = @(node (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api\generate-secret.js'))
    if ($LASTEXITCODE -ne 0) { throw 'Password hash generation failed.' }
    $Secrets = @{}
    foreach ($Line in $SecretLines) {
        $Parts = $Line -split '=', 2
        if ($Parts.Count -eq 2) { $Secrets[$Parts[0]] = $Parts[1] }
    }
    if (-not $Secrets.PARENT_PASSWORD_SCRYPT -or -not $Secrets.PARENT_SESSION_HMAC_KEY) { throw 'Parent secret generation failed.' }
    $RandomBytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($RandomBytes)
    $InternalKey = [Convert]::ToBase64String($RandomBytes)

    $Config = Get-Content -LiteralPath (Join-Path $ProjectRoot 'cloudbaserc.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $ApiFunction = $Config.functions | Where-Object { $_.name -eq 'sherlock-api' }
    $ScoreFunction = $Config.functions | Where-Object { $_.name -eq 'score-speaking' }
    if (-not $ApiFunction -or -not $ScoreFunction) { throw 'P3 function configuration is incomplete.' }
    $ApiFunction | Add-Member -NotePropertyName envVariables -NotePropertyValue @{
        PARENT_PASSWORD_SCRYPT = $Secrets.PARENT_PASSWORD_SCRYPT
        PARENT_SESSION_HMAC_KEY = $Secrets.PARENT_SESSION_HMAC_KEY
        SPEAKING_INTERNAL_HMAC_KEY = $InternalKey
        SESSION_TTL_SECONDS = '7200'
        AUTH_MAX_FAILURES = '5'
        AUTH_WINDOW_SECONDS = '900'
    } -Force
    $ScoreFunction | Add-Member -NotePropertyName envVariables -NotePropertyValue @{
        XF_APPID = $XfAppId
        XF_API_KEY = $XfApiKey
        XF_API_SECRET = $XfApiSecret
        SPEAKING_INTERNAL_HMAC_KEY = $InternalKey
    } -Force
    [IO.File]::WriteAllText($TemporaryConfig, ($Config | ConvertTo-Json -Depth 20), $Utf8NoBom)

    Push-Location $ProjectRoot
    try {
        Push-Location (Join-Path $ProjectRoot 'cloudfunctions\sherlock-api')
        try {
            npm run test:coverage
            if ($LASTEXITCODE -ne 0) { throw 'sherlock-api tests failed.' }
        }
        finally { Pop-Location }
        Push-Location (Join-Path $ProjectRoot 'cloudfunctions\score-speaking')
        try {
            npm run test:coverage
            if ($LASTEXITCODE -ne 0) { throw 'score-speaking tests failed.' }
        }
        finally { Pop-Location }

        npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $TemporaryConfig fn deploy score-speaking --force --install-dependency true
        if ($LASTEXITCODE -ne 0) { throw 'score-speaking deployment failed.' }
        npx --yes --package=@cloudbase/cli@3.8.0 tcb --config-file $TemporaryConfig fn deploy sherlock-api --force --install-dependency true
        if ($LASTEXITCODE -ne 0) { throw 'sherlock-api P3 deployment failed.' }

        $BadEvent = ConvertTo-NativeJsonArgument ((@{ payload = @{}; signature = 'bad' } | ConvertTo-Json -Compress))
        $HealthEvent = ConvertTo-NativeJsonArgument ((@{ action = 'health' } | ConvertTo-Json -Compress))
        $BadResult = $null
        $Health = $null
        foreach ($Attempt in 1..6) {
            try {
                $BadInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke score-speaking -d $BadEvent --json)
                $BadResult = $BadInvoke.data.RetMsg | ConvertFrom-Json
                $HealthInvoke = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb -e $EnvId fn invoke sherlock-api -d $HealthEvent --json)
                $Health = $HealthInvoke.data.RetMsg | ConvertFrom-Json
                if ($BadResult.error.code -eq 'UNAUTHORIZED' -and $Health.ok -and $Health.stage -eq 'P3') { break }
            }
            catch {
                if ($Attempt -eq 6) { throw }
            }
            if ($Attempt -lt 6) { Start-Sleep -Seconds 5 }
        }
        if ($BadResult.ok -ne $false -or $BadResult.error.code -ne 'UNAUTHORIZED') { throw 'Private scorer boundary verification failed.' }
        if (-not $Health.ok -or $Health.stage -ne 'P3' -or $Health.writes -ne 'test-only') { throw 'P3 health verification failed.' }

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
            if ($LASTEXITCODE -ne 0) { throw 'P3 static hosting deployment failed.' }
        }
        finally { Pop-Location }
        $TestUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
        $Response = Invoke-WebRequest -Uri $TestUrl -UseBasicParsing -TimeoutSec 30
        $Catalog = Invoke-WebRequest -Uri ($TestUrl + 'content/speaking/catalog.json') -UseBasicParsing -TimeoutSec 30
        $ChildCourse = Invoke-WebRequest -Uri ($TestUrl + 'content/speaking/S01D39.json') -UseBasicParsing -TimeoutSec 30
        $Audio = Invoke-WebRequest -Uri ($TestUrl + 'audio/speaking/S01D39/q01.mp3') -UseBasicParsing -TimeoutSec 30
        if ($Response.StatusCode -ne 200 -or $Response.Content -notmatch '<div id="root"></div>' -or $Catalog.StatusCode -ne 200 -or $Audio.StatusCode -ne 200) {
            throw 'P3 TEST site online verification failed.'
        }
        $CatalogObject = $Catalog.Content | ConvertFrom-Json
        if ($CatalogObject.Count -ne 12 -or $ChildCourse.Content -match '"(expected|tag|parent_note)"') {
            throw 'P3 child speaking course isolation verification failed.'
        }
        & (Join-Path $PSScriptRoot 'p1-cloudbase-preflight.ps1') -EnvId $EnvId
        if ($LASTEXITCODE -ne 0) { throw 'P3 post-deploy family24 verification failed.' }
        Write-Host "P3 TEST deployment succeeded: $TestUrl"
        Write-Host 'Next: complete one real iPad speaking take to verify Xunfei and private recording playback.'
    }
    finally { Pop-Location }
}
finally {
    $env:P1_PARENT_PASSWORD = $null
    $env:VITE_CLOUDBASE_ENV_ID = $null
    $env:VITE_CLOUDBASE_ACCESS_KEY = $null
    $env:VITE_CLOUDBASE_FUNCTION_NAME = $null
    $Password = $null; $XfAppId = $null; $XfApiKey = $null; $XfApiSecret = $null; $InternalKey = $null; $Credentials = $null
    if (Test-Path -LiteralPath $TemporaryConfig) { Remove-Item -LiteralPath $TemporaryConfig -Force }
}
