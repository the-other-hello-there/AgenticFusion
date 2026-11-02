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
function Confirm-AgentInstallation {
    param([string]$Agent)
    if ($script:fixtureCliMissing) { return $null }
    return $Agent
}
function codex { Write-Output 'UNGUARDED FIXTURE codex' }
function claude { Write-Output 'UNGUARDED FIXTURE claude' }
function Test-McpPort { param([int]$Port) return $true }
function Get-Process {
    [CmdletBinding()] param([string]$Name)
    $script:fixtureFusionCalls++
    if ($script:fixtureFusionCalls -eq 1) { return [pscustomobject]@{ProcessName='Fusion360'; Id=424242} }
    return @()
}
'@
    foreach ($agentName in @('codex', 'claude')) {
      foreach ($case in @('preflight', 'missing-cli', 'disabled', 'excluded', 'normal', 'normal-enabled')) {
        $scenario = $agentName + '-' + $case
        $project = Join-Path $testRoot ($scenario + ' project')
        New-Item -ItemType Directory -Path $project | Out-Null
        $preferenceFile = Join-Path $project 'Project\Context\Agentic-Verification.json'
        New-Item -ItemType Directory -Path (Split-Path -Parent $preferenceFile) -Force | Out-Null
        $scopes = if ($case -eq 'excluded') { @('slicing') } else { @('modeling') }
        $preferences = @{schema_version=1; enabled=($case -notin @('disabled','normal')); tasks=@($scopes); budget_percent='12.5'}
        [IO.File]::WriteAllText($preferenceFile, ($preferences | ConvertTo-Json -Depth 5), $utf8)
        $requirements = Join-Path $testRoot ($scenario + '-task.txt')
        [System.IO.File]::WriteAllText($requirements, 'Do not start any model; validate guarded preflight.', $utf8)
        $policy = Join-Path $testRoot ($scenario + '-policy.json')
        Copy-Item -LiteralPath (Join-Path $templateDir 'Review-Policy.json') -Destination $policy
        $state = Join-Path $testRoot ($scenario + '-controller')
        $missingLiteral = if ($case -eq 'missing-cli') { '$true' } else { '$false' }
        $header = @(
            ('$script:fixtureCliMissing = ' + $missingLiteral),
            ('$env:SELF = ' + (Quote-Literal $launcher)),
            ('$env:PROJDIR = ' + (Quote-Literal $project)),
            ('$env:AGENT = ' + (Quote-Literal $agentName)),
            '$env:SETUP_ONLY = $null',
            ('$env:AGENTIC_REVIEW_TASK = ' + $(if ($case -like 'normal*') { '$null' } else { Quote-Literal $requirements })),
            ('$env:AGENTIC_REVIEW_POLICY = ' + (Quote-Literal $policy)),
            ('$env:AGENTIC_REVIEW_STATE = ' + (Quote-Literal $state)),
            '$env:AGENTIC_REVIEW_SCOPE = ''modeling''',
            '$env:AGENTIC_REVIEW_BUDGET_PERCENT = ''20'''
        ) -join "`n"
        $harness = Join-Path $testRoot ($scenario + '-launch.ps1')
        [System.IO.File]::WriteAllText($harness, ($header + "`n" + $body.Substring(0, $insert) + $stubs + "`n" + $body.Substring($insert)), $utf8)
        $stdout = Join-Path $testRoot ($scenario + '-stdout.txt')
        $stderr = Join-Path $testRoot ($scenario + '-stderr.txt')
        $arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $harness + '"'
        $process = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $output = [System.IO.File]::ReadAllText($stdout) + [System.IO.File]::ReadAllText($stderr)
        if ($case -like 'normal*') {
            if ($process.ExitCode -ne 0 -or $output -notmatch "UNGUARDED FIXTURE $agentName" -or
                $output -match 'secondary agent verification supervisor' -or (Test-Path -LiteralPath $state)) {
                throw "$agentName did not preserve ordinary startup without a scoped task request:`n$output"
            }
            Write-Output "$agentName ordinary launch remained unguarded for $case; fixture agent only."
            continue
        }
        if ($case -in @('disabled','excluded')) {
            if ($process.ExitCode -ne 2 -or $output -notmatch 'Secondary agent verification is not enabled' -or
                $output -match 'UNGUARDED FIXTURE' -or (Test-Path -LiteralPath $state)) {
                throw "$agentName started review for a project/task without user opt-in:`n$output"
            }
            Write-Output "$agentName guarded task held without opt-in for $case; no primary/reviewer invoked."
            continue
        }
        if ($case -eq 'missing-cli') {
            if ($process.ExitCode -ne 2 -or $output -notmatch 'Guarded task could not start its primary runtime' -or
                $output -match 'secondary agent verification supervisor' -or (Test-Path -LiteralPath $state)) {
                throw "$agentName did not stop a guarded launch when installation was declined or failed:`n$output"
            }
            Write-Output "$agentName guarded launch stopped before Fusion/supervisor when the selected CLI was unavailable."
            continue
        }
        if ($process.ExitCode -ne 2 -or $output -notmatch 'DELIVERY HELD' -or $output -notmatch 'secondary agent verification supervisor') {
            throw "$agentName guarded dispatch failed (exit $($process.ExitCode)):`n$output"
        }
        if (-not (Test-Path -LiteralPath (Join-Path $state 'report.json'))) { throw "$agentName did not reach guarded preflight:`n$output" }
        $report = Get-Content -LiteralPath (Join-Path $state 'report.json') -Raw | ConvertFrom-Json
        if ($report.status -ne 'held' -or $report.accounting.attempts -ne 0 -or
            $report.accounting.ratio_limit -ne '0.2' -or $report.verification.task_scope -ne 'modeling') {
            throw "$agentName did not pass task scope/budget and hold before model review."
        }
        Write-Output "$agentName launcher dispatched to the real supervisor, held preflight, and propagated exit 2; no model invoked."
      }
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
