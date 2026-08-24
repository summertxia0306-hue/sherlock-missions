param(
    [string]$EnvId = 'family24-d7gqb6r6m2d722f7a'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Windows PowerShell 5.1 otherwise decodes UTF-8 output from native tools with
# the active legacy console code page, which can corrupt CloudBase JSON.
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $Utf8NoBom
[Console]::OutputEncoding = $Utf8NoBom
$OutputEncoding = $Utf8NoBom

$ExpectedRoot = 'D:\ObsidianVaults\Education\Sherlock\English-Learning'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ($ProjectRoot -ne $ExpectedRoot) {
    throw "Project root mismatch. Refusing to run: $ProjectRoot"
}
if ($EnvId -ne 'family24-d7gqb6r6m2d722f7a') {
    throw "CloudBase environment mismatch. Refusing to run: $EnvId"
}

function ConvertFrom-TcbOutput([object[]]$Lines) {
    $Joined = $Lines -join "`n"
    $Start = $Joined.IndexOf('{')
    if ($Start -lt 0) {
        throw 'CloudBase CLI did not return JSON.'
    }
    $Object = $Joined.Substring($Start) | ConvertFrom-Json
    if ($Object.PSObject.Properties['error']) {
        throw "CloudBase API failed: $($Object.error.code)"
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

$Environments = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb env list --json)
$Target = @($Environments.data | Where-Object { $_.EnvId -eq $EnvId })
if ($Target.Count -ne 1 -or $Target[0].Status -ne 'NORMAL') {
    throw 'The family24 environment is missing or unhealthy.'
}

$Billing = Invoke-TcbApi 'DescribeBillingInfo' @{ EnvId = $EnvId }
$BillingItem = @($Billing.data.EnvBillingInfoList | Where-Object { $_.EnvId -eq $EnvId })
if ($BillingItem.Count -ne 1) {
    throw 'Could not obtain exactly one family24 billing record.'
}
$Usage = ConvertFrom-TcbOutput @(npx --yes --package=@cloudbase/cli@3.8.0 tcb env usage -e $EnvId --json)
$Summary = $Usage.data.summary
if ($BillingItem[0].EnableOverrun -ne $false) {
    throw 'Overrun billing is enabled. P1 refuses to continue.'
}
if ($Summary.payAsYouGoDeduct -ne 0) {
    throw 'Pay-as-you-go deduction was detected. P1 refuses to continue.'
}

$Family24Url = 'https://family24-web-family24-d7gqb6r6m2d722f7a.webapps.tcloudbase.com/'
$Family24Response = Invoke-WebRequest -Uri $Family24Url -UseBasicParsing -TimeoutSec 30
if ($Family24Response.StatusCode -ne 200) {
    throw 'The Family24 site is unavailable. P1 refuses to continue.'
}

[pscustomobject]@{
    EnvId = $EnvId
    PackageName = $BillingItem[0].PackageName
    ExpireTime = $BillingItem[0].ExpireTime
    EnableOverrun = $BillingItem[0].EnableOverrun
    BillingCycle = "$($Usage.data.billingCycle.startDate) ~ $($Usage.data.billingCycle.endDate)"
    TotalCredits = $Summary.totalCredits
    UsedCredits = $Summary.usedCredits
    RemainingCredits = [math]::Round([double]$Summary.totalCredits - [double]$Summary.usedCredits, 2)
    Family24HttpStatus = [int]$Family24Response.StatusCode
} | Format-List
