# Shared Fusion/slicer lifetime tracking. State stays outside the portable project.
[CmdletBinding()]
param(
    [ValidateSet('Status','Register','Watch','Checkpoint','Close','Restart')]
    [string]$Action = 'Status',
    [string]$ProjectDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$StateRoot,
    [int]$ProcessId,
    [ValidateSet('Fusion','Slicer')][string]$Kind = 'Fusion',
    [string]$LaunchPath,
    [string]$ArgumentsJson = '[]',
    [string]$AppId,
    [string]$RestoreFile,
    [string]$CheckpointId,
    [switch]$SavedStateVerified,
    [switch]$CleanupVerified,
    [switch]$ApplicationIdle,
    [switch]$UnusedVerified,
    [switch]$UserApproved,
    [switch]$StartMonitor,
    [switch]$LibraryOnly
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)

function Get-AppIdentity([int]$TargetId) {
    try {
        $appProcess = Get-Process -Id $TargetId -ErrorAction Stop
        if (-not $appProcess.Path) { return $null }
        return [pscustomobject]@{ process_id = $appProcess.Id; name = $appProcess.ProcessName;
            executable = $appProcess.Path; started_utc = $appProcess.StartTime.ToUniversalTime().ToString('o') }
    } catch { return $null }
}

function Test-AppIdentity($Entry, $Current) {
    return $null -ne $Current -and $Entry.process_id -eq $Current.process_id -and
        $Entry.started_utc -eq $Current.started_utc -and
        $Entry.executable.Equals($Current.executable, [StringComparison]::OrdinalIgnoreCase)
}

function Get-AppAge([string]$StartedUtc, [datetime]$NowUtc = [datetime]::UtcNow) {
    $hours = [Math]::Max(0, ($NowUtc - [datetime]::Parse($StartedUtc).ToUniversalTime()).TotalHours)
    return [pscustomobject]@{ hours = [Math]::Round($hours, 4);
        checkpoint_recommended = ($hours -ge 11.5); maintenance_due = ($hours -ge 12) }
}

function Initialize-SessionStore {
    $script:sessionProject = [IO.Path]::GetFullPath($ProjectDir).TrimEnd('\')
    if (-not (Test-Path -LiteralPath (Join-Path $script:sessionProject 'Agentic-Fusion.md') -PathType Leaf)) {
        throw 'Select an initialized Agentic Fusion project.'
    }
    if (-not $StateRoot) {
        if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable; supply an external StateRoot.' }
        $StateRoot = Join-Path $env:LOCALAPPDATA 'AgenticFusion\Sessions'
    }
    $script:sessionRoot = [IO.Path]::GetFullPath($StateRoot).TrimEnd('\')
    if ($script:sessionRoot.Equals($script:sessionProject, [StringComparison]::OrdinalIgnoreCase) -or
        $script:sessionRoot.StartsWith($script:sessionProject + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Session runtime data must stay outside the portable project.'
    }
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { $script:sessionKey = ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($script:sessionProject.ToLowerInvariant())))).Replace('-','').Substring(0,24) }
    finally { $hasher.Dispose() }
    $script:sessionFile = Join-Path $script:sessionRoot ($script:sessionKey + '.json')
}

function Read-SessionState {
    if (Test-Path -LiteralPath $script:sessionFile) {
        $state = Get-Content -LiteralPath $script:sessionFile -Raw | ConvertFrom-Json
        if ($state.schema_version -ne 1 -or $state.project -ne $script:sessionProject) { throw 'Session state identity/schema mismatch.' }
        return $state
    }
    return [pscustomobject]@{ schema_version = 1; project = $script:sessionProject; applications = @() }
}

function Write-SessionState($State) {
    New-Item -ItemType Directory -Path $script:sessionRoot -Force | Out-Null
    $temporary = $script:sessionFile + '.' + [guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [IO.File]::WriteAllText($temporary, ($State | ConvertTo-Json -Depth 15), (New-Object Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $temporary -Destination $script:sessionFile -Force
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force } }
}

function ConvertTo-AppArgument([string]$Value) {
    # CommandLineToArgvW-compatible quoting for Start-Process's flattened argument string.
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}

function Start-SessionMonitor {
    $scriptPath = $PSCommandPath
    $commandArgs = @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',
        (ConvertTo-AppArgument $scriptPath), '-Action','Watch','-ProjectDir',
        (ConvertTo-AppArgument $script:sessionProject), '-StateRoot', (ConvertTo-AppArgument $script:sessionRoot))
    Start-Process -FilePath 'powershell.exe' -ArgumentList $commandArgs -WindowStyle Hidden | Out-Null
}

function Show-MaintenanceNotice($Entry) {
    # Non-modal notification only. The watcher cannot fabricate a semantic save/checkpoint.
    $notice = $null
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $notice = New-Object System.Windows.Forms.NotifyIcon
        $notice.Icon = [System.Drawing.SystemIcons]::Information
        $notice.Visible = $true
        $notice.BalloonTipTitle = 'Agentic Fusion: application maintenance due'
        $notice.BalloonTipText = "$($Entry.kind) reached 12 hours. The agent must checkpoint, clean up and request restart approval."
        $notice.ShowBalloonTip(5000)
        Start-Sleep -Seconds 5
    } catch { } finally { if ($notice) { $notice.Dispose() } }
}

function Close-AppProcess($Entry) {
    $appProcess = Get-Process -Id $Entry.process_id -ErrorAction Stop
    if ($appProcess.StartTime.ToUniversalTime().ToString('o') -ne $Entry.started_utc -or
        -not $appProcess.Path.Equals($Entry.executable, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Process identity changed before close; refusing to act on a reused PID.'
    }
    if (-not $appProcess.CloseMainWindow()) { return $false }
    return $appProcess.WaitForExit(30000)
}

function Start-AppProcess($Entry) {
    if ($Entry.app_id) {
        $storeHelper = Join-Path $script:sessionProject '.agents\skills\orca-slice\scripts\slicer_windows.ps1'
        $storeArgs = @('-AppId', $Entry.app_id)
        if ($Entry.restore_file) { $storeArgs += @('-OpenFile', $Entry.restore_file) }
        $resultText = & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $storeHelper @storeArgs | Out-String
        if ($LASTEXITCODE -ne 0) { throw 'Store activation failed; keep the checkpoint and rebind deliberately.' }
        return [int](($resultText | ConvertFrom-Json).pid)
    }
    $launchArgs = @($Entry.arguments)
    if ($Entry.restore_file) { $launchArgs += $Entry.restore_file }
    $startOptions = @{ FilePath = $Entry.launch_path; PassThru = $true }
    if ($launchArgs.Count) { $startOptions.ArgumentList = ($launchArgs | ForEach-Object { ConvertTo-AppArgument ([string]$_) }) -join ' ' }
    $startedApp = Start-Process @startOptions
    if ($startedApp) { return [int]$startedApp.Id }
    return 0
}

function Invoke-SessionAction {
    Initialize-SessionStore
    $mutex = New-Object Threading.Mutex($false, ('Local\AgenticFusionState-' + $script:sessionKey))
    if (-not $mutex.WaitOne(45000)) { $mutex.Dispose(); throw 'Another process is updating session state; retry.' }
    try {
        $state = Read-SessionState
        $entries = @($state.applications)
        if ($Action -eq 'Register') {
            $identity = Get-AppIdentity $ProcessId
            if (-not $identity) { throw 'Application PID/path/start time is unavailable; identify the real window process first.' }
            if ($identity.name -match '(?i)codex|claude|chatgpt|^(powershell|pwsh|cmd|conhost|node|python|WindowsTerminal)$') {
                throw 'AI agents and console/helper hosts are excluded from application restarts.'
            }
            if ($Kind -eq 'Fusion' -and $identity.name -notmatch '(?i)^Fusion(360)?$') { throw 'Fusion registration must identify its actual GUI process.' }
            if (-not $ArgumentsJson.Trim().StartsWith('[') -or -not $ArgumentsJson.Trim().EndsWith(']')) { throw 'ArgumentsJson must be an array of strings.' }
            $launchArguments = @($ArgumentsJson | ConvertFrom-Json)
            if ($launchArguments | Where-Object { $_ -isnot [string] }) { throw 'ArgumentsJson must be an array of strings.' }
            $existing = @($entries | Where-Object { Test-AppIdentity $_ $identity })
            if ($existing.Count -gt 0) {
                $entry = $existing[0]
                # Preserve the actual process start/deadline and any checkpoint on reattachment.
                if ($LaunchPath) { $entry.launch_path = [IO.Path]::GetFullPath($LaunchPath) }
                if ($AppId) { $entry.app_id = $AppId }
                if ($RestoreFile) { $entry.restore_file = [IO.Path]::GetFullPath($RestoreFile); $entry.checkpoint = $null }
            } else {
                $entry = [pscustomobject]@{ process_id = $identity.process_id; started_utc = $identity.started_utc;
                    executable = $identity.executable; kind = $Kind; launch_path = $identity.executable;
                    arguments = $launchArguments; app_id = $AppId; restore_file = $RestoreFile;
                    checkpoint = $null; status = 'running' }
                if ($LaunchPath) { $entry.launch_path = [IO.Path]::GetFullPath($LaunchPath) }
                if ($RestoreFile) { $entry.restore_file = [IO.Path]::GetFullPath($RestoreFile) }
                $entries = @($entries | Where-Object { Test-AppIdentity $_ (Get-AppIdentity $_.process_id) }) + @($entry)
            }
            $state.applications = $entries
            Write-SessionState $state
            if ($StartMonitor) { Start-SessionMonitor }
            return [pscustomobject]@{ status = 'registered'; application = $entry; state_file = $script:sessionFile }
        }

        if ($Action -eq 'Status') {
            $summary = @()
            foreach ($entry in $entries) {
                $current = Get-AppIdentity $entry.process_id
                $alive = Test-AppIdentity $entry $current
                $age = Get-AppAge $entry.started_utc
                if (-not $alive) { $entry.status = 'exited_or_identity_changed' }
                elseif ($age.maintenance_due) { $entry.status = 'checkpoint_cleanup_and_restart_approval_due' }
                else { $entry.status = 'running' }
                $summary += [pscustomobject]@{ process_id = $entry.process_id; started_utc = $entry.started_utc; kind = $entry.kind; status = $entry.status;
                    running = $alive; runtime_hours = $age.hours; checkpoint_recommended = ($alive -and $age.checkpoint_recommended);
                    maintenance_due = ($alive -and $age.maintenance_due); checkpoint_id = $(if ($entry.checkpoint) { $entry.checkpoint.id } else { $null }) }
            }
            if ($script:watching -and (Test-Path -LiteralPath $script:sessionFile)) { Write-SessionState $state }
            return [pscustomobject]@{ applications = $summary; state_file = $script:sessionFile;
                block_new_application_work = (@($summary | Where-Object { $_.maintenance_due }).Count -gt 0) }
        }

        $targets = @($entries | Where-Object { $_.process_id -eq $ProcessId -and (Test-AppIdentity $_ (Get-AppIdentity $ProcessId)) })
        if ($targets.Count -ne 1) { throw 'Registered process identity changed or is missing; rebind and checkpoint again.' }
        $entry = $targets[0]
        if ($Action -eq 'Checkpoint') {
            if (-not ($SavedStateVerified -and $CleanupVerified -and $ApplicationIdle)) {
                throw 'Checkpoint requires verified saved application state, completed context-preserving cleanup and an idle application.'
            }
            $projectFile = Join-Path $script:sessionProject 'Project.md'
            if (-not (Test-Path -LiteralPath $projectFile -PathType Leaf)) { throw 'Write the durable Project.md restart checkpoint first.' }
            if ($RestoreFile) { $entry.restore_file = [IO.Path]::GetFullPath($RestoreFile) }
            $artifactHash = $null
            if ($entry.restore_file) {
                if (-not (Test-Path -LiteralPath $entry.restore_file -PathType Leaf)) { throw 'Restore file is missing.' }
                $artifactHash = (Get-FileHash -LiteralPath $entry.restore_file -Algorithm SHA256).Hash
            }
            $entry.checkpoint = [pscustomobject]@{ id = [guid]::NewGuid().ToString('N'); saved_utc = [datetime]::UtcNow.ToString('o');
                project_sha256 = (Get-FileHash -LiteralPath $projectFile -Algorithm SHA256).Hash; restore_sha256 = $artifactHash }
            Write-SessionState $state
            return [pscustomobject]@{ status = 'checkpoint_recorded'; application = $entry }
        }

        if ($Action -eq 'Restart' -and -not $UserApproved) { throw 'Restart needs the user approval for this concrete application/session.' }
        if ($Action -eq 'Close' -and -not $UnusedVerified) { throw 'Automatic closure needs confirmation that this application is no longer in use.' }
        if (-not $ApplicationIdle) { throw 'Recheck the live application is idle and saved immediately before closure.' }
        $checkpoint = $entry.checkpoint
        if (-not $checkpoint -or $CheckpointId -ne $checkpoint.id -or
            ([datetime]::UtcNow - [datetime]::Parse($checkpoint.saved_utc).ToUniversalTime()).TotalMinutes -gt 5) {
            throw 'Supply a current checkpoint ID (within five minutes); recheck saves/cleanup if approval was delayed.'
        }
        if ((Get-FileHash -LiteralPath (Join-Path $script:sessionProject 'Project.md') -Algorithm SHA256).Hash -ne $checkpoint.project_sha256) {
            throw 'Project context changed after checkpoint; checkpoint again.'
        }
        if ($entry.restore_file -and (Get-FileHash -LiteralPath $entry.restore_file -Algorithm SHA256).Hash -ne $checkpoint.restore_sha256) {
            throw 'Saved slicer artifact changed after checkpoint; checkpoint again.'
        }
        if (-not (Close-AppProcess $entry)) {
            return [pscustomobject]@{ status = 'close_pending_or_blocked'; process_id = $entry.process_id; restarted = $false }
        }
        $entry.status = 'closed'; $entry.checkpoint = $null
        Write-SessionState $state
        if ($Action -eq 'Close') { return [pscustomobject]@{ status = 'closed'; process_id = $entry.process_id } }
        $newId = Start-AppProcess $entry
        return [pscustomobject]@{ status = 'restart_launched_rebind_and_verify_required'; previous_process_id = $entry.process_id;
            launched_process_id = $newId; restore_file = $entry.restore_file; checkpoint_preserved_in = (Join-Path $script:sessionProject 'Project.md') }
    } finally { $mutex.ReleaseMutex(); $mutex.Dispose() }
}

function Watch-ApplicationSessions {
    Initialize-SessionStore
    $watchLock = New-Object Threading.Mutex($false, ('Local\AgenticFusionWatch-' + $script:sessionKey))
    if (-not $watchLock.WaitOne(0)) { $watchLock.Dispose(); return }
    try {
        $script:watching = $true
        while ($true) {
            $script:Action = 'Status'
            $summary = Invoke-SessionAction
            if (@($summary.applications | Where-Object { $_.running }).Count -eq 0) { break }
            foreach ($app in @($summary.applications | Where-Object { $_.maintenance_due })) {
                if (-not $script:notices) { $script:notices = @{} }
                $noticeKey = [string]$app.process_id + ':' + $app.started_utc
                if (-not $script:notices.ContainsKey($noticeKey)) { $script:notices[$noticeKey] = $true; Show-MaintenanceNotice $app }
            }
            Start-Sleep -Seconds 30
        }
    } finally { $script:watching = $false; $watchLock.ReleaseMutex(); $watchLock.Dispose() }
}

if (-not $LibraryOnly) {
    try {
        if ($Action -eq 'Watch') { Watch-ApplicationSessions }
        else { Invoke-SessionAction | ConvertTo-Json -Depth 15 }
    } catch { Write-Error $_; exit 1 }
}
