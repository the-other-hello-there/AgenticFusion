# Exercise each launcher's guarded dispatch with stubbed Fusion discovery/connectivity.
# The real supervisor must fail preflight before invoking any model.
$ErrorActionPreference = 'Stop'
$assessmentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryDir = Split-Path -Parent (Split-Path -Parent $assessmentDir)
$templateDir = Join-Path $repositoryDir 'AgenticFusionTemplate'
$launcher = Join-Path $templateDir 'Fusion-Claude.bat'
$temporaryParent = [System.IO.Path]::GetTempPath()
$testRoot = Join-Path $temporaryParent ('AgenticFusion-review-launch-' + [guid]::NewGuid().ToString('N'))
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Quote-Literal([string]$Value) { return "'" + $Value.Replace("'", "''") + "'" }
try {
    New-Item -ItemType Directory -Path $testRoot | Out-Null
    $source = [System.IO.File]::ReadAllText($launcher)
    $body = $source.Substring($source.LastIndexOf('#PS_BEGIN'))
    $insert = $body.LastIndexOf('try { Start-AgenticFusion }')
    if ($insert -lt 0) { throw 'Cannot locate the launcher entrypoint.' }
    $stubs = @'
function Confirm-Agent { param([string]$Name) return $true }
function Test-McpPort { param([int]$Port) return $true }
function Get-Process { [CmdletBinding()] param([string]$Name) return [pscustomobject]@{ProcessName='Fusion360'} }
'@
    foreach ($agentName in @('codex', 'claude')) {
        $project = Join-Path $testRoot ($agentName + ' project')
        New-Item -ItemType Directory -Path $project | Out-Null
        $requirements = Join-Path $testRoot ($agentName + '-task.txt')
        [System.IO.File]::WriteAllText($requirements, 'Do not start any model; validate guarded preflight.', $utf8)
        $policy = Join-Path $testRoot ($agentName + '-policy.json')
        Copy-Item -LiteralPath (Join-Path $templateDir 'Review-Policy.json') -Destination $policy
        $state = Join-Path $testRoot ($agentName + '-controller')
        $header = @(
            ('$env:SELF = ' + (Quote-Literal $launcher)),
            ('$env:PROJDIR = ' + (Quote-Literal $project)),
            ('$env:AGENT = ' + (Quote-Literal $agentName)),
            '$env:SETUP_ONLY = $null',
            ('$env:AGENTIC_REVIEW_TASK = ' + (Quote-Literal $requirements)),
            ('$env:AGENTIC_REVIEW_POLICY = ' + (Quote-Literal $policy)),
            ('$env:AGENTIC_REVIEW_STATE = ' + (Quote-Literal $state))
        ) -join "`n"
        $harness = Join-Path $testRoot ($agentName + '-launch.ps1')
        [System.IO.File]::WriteAllText($harness, ($header + "`n" + $body.Substring(0, $insert) + $stubs + "`n" + $body.Substring($insert)), $utf8)
        $stdout = Join-Path $testRoot ($agentName + '-stdout.txt')
        $stderr = Join-Path $testRoot ($agentName + '-stderr.txt')
        $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $harness + '"'
        $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $output = [System.IO.File]::ReadAllText($stdout) + [System.IO.File]::ReadAllText($stderr)
        if ($process.ExitCode -ne 2 -or $output -notmatch 'DELIVERY HELD' -or $output -notmatch 'independent task supervisor') {
            throw "$agentName guarded dispatch failed (exit $($process.ExitCode)):`n$output"
        }
        $report = Get-Content -LiteralPath (Join-Path $state 'report.json') -Raw | ConvertFrom-Json
        if ($report.status -ne 'held' -or $report.accounting.attempts -ne 0) { throw "$agentName did not hold before model review." }
        Write-Output "$agentName launcher dispatched to the real supervisor, held preflight, and propagated exit 2; no model invoked."
    }
}
finally {
    $resolvedRoot = [System.IO.Path]::GetFullPath($testRoot).TrimEnd('\')
    $resolvedParent = [System.IO.Path]::GetFullPath($temporaryParent).TrimEnd('\')
    if (-not [System.IO.Path]::GetDirectoryName($resolvedRoot).Equals($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not [System.IO.Path]::GetFileName($resolvedRoot).StartsWith('AgenticFusion-review-launch-')) {
        throw "Refusing cleanup outside the temporary test directory: $resolvedRoot"
    }
    if (Test-Path -LiteralPath $resolvedRoot) { Remove-Item -LiteralPath $resolvedRoot -Recurse -Force }
}
