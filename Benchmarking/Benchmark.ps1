param([switch]$SelfTest, [switch]$UiSmokeTest)

$ErrorActionPreference = 'Stop'
$script:BenchmarkDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:RepositoryDir = Split-Path -Parent $script:BenchmarkDir
$script:TemplateDir = Join-Path $script:RepositoryDir 'AgenticFusionTemplate'
$script:RunsDir = Join-Path $script:BenchmarkDir '.runs'
$script:ResultsFile = Join-Path $script:BenchmarkDir 'Benchmarking.md'
$script:RunRoot = $null
$script:Sandbox = $null
$script:Saved = $false
$script:Finished = $false
$script:Restarted = $false
$script:StepIndex = 0
$script:Stopwatch = New-Object System.Diagnostics.Stopwatch
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)

function Get-BenchmarkSteps {
    $markdown = [System.IO.File]::ReadAllText($script:ResultsFile, $script:Utf8)
    $headings = [regex]::Matches($markdown, '(?m)^### (B[1-7])([^\r\n]*)\r?$')
    if ($headings.Count -ne 7) { throw 'Benchmarking.md must contain B1 through B7.' }
    $steps = @()
    for ($i = 0; $i -lt $headings.Count; $i++) {
        $start = $headings[$i].Index + $headings[$i].Length
        $end = if ($i + 1 -lt $headings.Count) { $headings[$i + 1].Index } else { $markdown.Length }
        $body = $markdown.Substring($start, $end - $start)
        $prompt = [regex]::Match($body, '(?m)^> (.+)\r?$')
        $accept = [regex]::Match($body, '(?m)^\*\*Accept when:\*\* (.+)\r?$')
        if (-not $prompt.Success -or -not $accept.Success) { throw "Missing prompt or acceptance rule for B$($i + 1)." }
        $steps += [pscustomobject]@{
            Id = $headings[$i].Groups[1].Value
            Title = $headings[$i].Value.Trim()
            Prompt = $prompt.Groups[1].Value.Trim()
            Accept = $accept.Groups[1].Value.Trim()
            Seconds = $null
            Usage = ''
            Rating = ''
            Notes = ''
        }
    }
    return ,$steps
}

function New-RunRoot {
    New-Item -ItemType Directory -Path $script:RunsDir -Force | Out-Null
    $path = Join-Path $script:RunsDir ([guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $path | Out-Null
    return $path
}

function Copy-Template {
    param([string]$Destination)
    if (-not (Test-Path -LiteralPath $script:TemplateDir -PathType Container)) { throw "Template folder is missing: $script:TemplateDir" }
    Copy-Item -LiteralPath $script:TemplateDir -Destination $Destination -Recurse -Force
    if (-not (Test-Path -LiteralPath (Join-Path $Destination 'Fusion-Claude.bat'))) { throw "Template copy failed: $Destination" }
}

function Remove-RunRoot {
    param([string]$Path)
    if (-not $Path) { return }
    $absolute = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $expectedParent = [System.IO.Path]::GetFullPath($script:RunsDir).TrimEnd('\')
    $parent = [System.IO.Path]::GetDirectoryName($absolute).TrimEnd('\')
    $leaf = [System.IO.Path]::GetFileName($absolute)
    $parsed = [guid]::Empty
    if (-not $parent.Equals($expectedParent, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not [guid]::TryParseExact($leaf, 'N', [ref]$parsed)) {
        throw "Refusing to remove a folder outside Benchmarking/.runs: $Path"
    }
    if (Test-Path -LiteralPath $absolute) { Remove-Item -LiteralPath $absolute -Recurse -Force -ErrorAction Stop }
}

function Test-LauncherSetup {
    param([string]$Project, [string]$LauncherName)
    $launcher = Join-Path $Project $LauncherName
    $output = (& $launcher --setup-only 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0 -or $output -match '(?m)^Error:') { throw "$LauncherName setup failed:`n$output" }
    foreach ($file in @('Project.md', 'FDM-Slicing.md', 'Printers.json', '.mcp.json', '.codex\config.toml', 'settings.json',
                        'Independent-Review.md', 'Review-Policy.json', '.agents\review_guard\supervisor.py',
                        '.agents\skills\orca-slice\SKILL.md', '.agents\skills\orca-slice\scripts\start_orca.py',
                        '.agents\skills\printer-library\SKILL.md', '.agents\skills\printer-library\scripts\printer_library.py',
                        '.agents\skills\fdm-calibrate\SKILL.md', '.agents\skills\slice-compare\SKILL.md')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Project $file) -PathType Leaf)) {
            throw "$LauncherName did not prepare $file.`n$output"
        }
    }
    $mcp = Get-Content -LiteralPath (Join-Path $Project '.mcp.json') -Raw | ConvertFrom-Json
    $settings = Get-Content -LiteralPath (Join-Path $Project 'settings.json') -Raw | ConvertFrom-Json
    $codex = [System.IO.File]::ReadAllText((Join-Path $Project '.codex\config.toml'))
    $url = 'http://127.0.0.1:27182/mcp'
    if ($mcp.mcpServers.fusion.url -ne $url -or $settings.enabledMcpjsonServers -notcontains 'fusion' -or
        $settings.autoMemoryEnabled -ne $false -or $codex -notmatch [regex]::Escape($url)) {
        throw "$LauncherName left inconsistent Fusion configuration.`n$output"
    }
    return $output.Trim()
}

function Get-TemplateVersion {
    try {
        $commit = (& git -C $script:RepositoryDir rev-parse --short HEAD 2>$null | Select-Object -First 1)
        if (-not $commit) { return 'unknown' }
        $changes = (& git -C $script:RepositoryDir status --porcelain -- AgenticFusionTemplate 2>$null | Out-String)
        if ($changes.Trim()) { return "$commit (modified template)" }
        return $commit.Trim()
    } catch { return 'unknown' }
}

function Get-AgentVersion {
    param([string]$Agent)
    $command = if ($Agent -eq 'Codex') { 'codex' } else { 'claude' }
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { return "$command (version unavailable)" }
    try {
        $version = (& $command --version 2>$null | Select-Object -First 1)
        if ($version) { return $version.Trim() }
    } catch { }
    return "$command (version unavailable)"
}

function Start-BenchmarkAgent {
    $name = if ($script:Agent -eq 'Codex') { 'Fusion-Codex.bat' } else { 'Fusion-Claude.bat' }
    $launcher = Join-Path $script:Sandbox $name
    # /c closes cmd after the launcher's interactive PowerShell window exits.
    $arguments = '/c ""' + $launcher + '""'
    Start-Process -FilePath $env:ComSpec -ArgumentList $arguments -WorkingDirectory $script:Sandbox -WindowStyle Normal | Out-Null
}

function Format-Duration {
    param([object]$Seconds)
    if ($null -eq $Seconds) { return '[not timed]' }
    $total = [int]$Seconds
    return ('{0:00}:{1:00}' -f [math]::Floor($total / 60), ($total % 60))
}

function Escape-TableCell {
    param([string]$Value)
    if (-not $Value) { return 'not recorded' }
    return ($Value.Trim() -replace '\|', '\|' -replace '\r?\n', '<br>')
}

function Save-BenchmarkResults {
    $date = Get-Date -Format 'yyyy-MM-dd'
    $time = Get-Date -Format 'HH:mm:ss'
    $heading = "## v$date"
    $lines = @(
        "### Run $time - $($script:Agent)",
        '',
        "- Template version or Git commit: **$(Escape-TableCell $script:VersionBox.Text)**",
        "- Agent and CLI version: **$(Escape-TableCell $script:AgentVersionBox.Text)**",
        "- Fusion version: **$(Escape-TableCell $script:FusionVersionBox.Text)**",
        "- Model and effort: **$(Escape-TableCell $script:ModelBox.Text)**",
        "- Date and credit/usage unit: **$date; $(Escape-TableCell $script:UnitBox.Text)**",
        '',
        '| Prompt | Time (mm:ss) | Credits or usage delta | Acceptability (1-5) | Notes |',
        '| --- | --- | --- | --- | --- |'
    )
    foreach ($step in $script:Steps) {
        $lines += "| $($step.Id) | $(Format-Duration $step.Seconds) | $(Escape-TableCell $step.Usage) | $(Escape-TableCell $step.Rating) | $(Escape-TableCell $step.Notes) |"
    }
    $entry = ($lines -join "`n") + "`n`n"
    $original = [System.IO.File]::ReadAllText($script:ResultsFile, $script:Utf8)
    $normalized = $original.Replace("`r`n", "`n")
    $match = [regex]::Match($normalized, '(?m)^' + [regex]::Escape($heading) + '[ \t]*$')
    if ($match.Success) {
        $later = [regex]::Match($normalized.Substring($match.Index + $match.Length), '(?m)^## (?!#)')
        $at = if ($later.Success) { $match.Index + $match.Length + $later.Index } else { $normalized.Length }
        $updated = $normalized.Substring(0, $at).TrimEnd("`n") + "`n`n" + $entry + $normalized.Substring($at)
    } else {
        $updated = $normalized.TrimEnd("`n") + "`n`n" + $heading + "`n`n" + $entry
    }
    [System.IO.File]::WriteAllText($script:ResultsFile, $updated, $script:Utf8)
}

$script:Steps = Get-BenchmarkSteps

if ($SelfTest) {
    $testRoot = New-RunRoot
    $originalResultsFile = $script:ResultsFile
    try {
        $claudeCopy = Join-Path $testRoot 'ClaudeFresh'
        $codexCopy = Join-Path $testRoot 'CodexFresh'
        Copy-Template $claudeCopy
        Copy-Template $codexCopy
        Test-LauncherSetup $claudeCopy 'Fusion-Claude.bat' | Out-Null
        Test-LauncherSetup $codexCopy 'Fusion-Codex.bat' | Out-Null
        $batchPath = Join-Path $codexCopy 'Fusion-Codex.bat'
        $batchArguments = '/c ""' + $batchPath + '" --setup-only"'
        $batchProcess = Start-Process -FilePath $env:ComSpec -ArgumentList $batchArguments -WorkingDirectory $codexCopy -Wait -PassThru -WindowStyle Hidden
        if ($batchProcess.ExitCode -ne 0) { throw 'Quoted batch launch from a path with spaces failed.' }
        $script:ResultsFile = Join-Path $testRoot 'Benchmarking.md'
        Copy-Item -LiteralPath $originalResultsFile -Destination $script:ResultsFile
        $script:Agent = 'Codex'
        $script:VersionBox = [pscustomobject]@{ Text = 'test commit' }
        $script:AgentVersionBox = [pscustomobject]@{ Text = 'test cli' }
        $script:FusionVersionBox = [pscustomobject]@{ Text = 'test Fusion' }
        $script:ModelBox = [pscustomobject]@{ Text = 'test model' }
        $script:UnitBox = [pscustomobject]@{ Text = 'test units' }
        foreach ($step in $script:Steps) {
            $step.Seconds = 60
            $step.Rating = '5'
            $step.Notes = 'pipe | check'
        }
        Save-BenchmarkResults
        Save-BenchmarkResults
        $savedText = [System.IO.File]::ReadAllText($script:ResultsFile, $script:Utf8)
        $dateHeader = '## v' + (Get-Date -Format 'yyyy-MM-dd')
        $headerCount = ([regex]::Matches($savedText, '(?m)^' + [regex]::Escape($dateHeader) + '$')).Count
        $runCount = ([regex]::Matches($savedText, '(?m)^### Run ')).Count
        $rowCount = ([regex]::Matches($savedText, '(?m)^\| B[1-7] \|')).Count
        $escaped = $savedText.Contains('pipe \| check')
        if ($headerCount -ne 1 -or $runCount -ne 2 -or $rowCount -ne 21 -or -not $escaped) {
            throw "Results save failed: headers=$headerCount runs=$runCount rows=$rowCount escaped=$escaped"
        }
        Write-Output 'B1-B7 parsed; both launchers passed setup-only checks in separate fresh copies; quoted batch launch and temporary results save/append passed.'
    } finally {
        $script:ResultsFile = $originalResultsFile
        Remove-RunRoot $testRoot
    }
    return
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$script:Form = New-Object System.Windows.Forms.Form
$script:Form.Text = 'Agentic Fusion Benchmark'
$script:Form.Size = New-Object System.Drawing.Size(1080, 820)
$script:Form.MinimumSize = New-Object System.Drawing.Size(940, 760)
$script:Form.AutoScroll = $true
$script:Form.AutoScrollMinSize = New-Object System.Drawing.Size(1060, 790)
$script:Form.StartPosition = 'CenterScreen'
$script:Form.Font = New-Object System.Drawing.Font('Segoe UI', 9)

function Add-Label {
    param([string]$Text, [int]$X, [int]$Y, [int]$Width, [int]$Height)
    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Text
    $label.SetBounds($X, $Y, $Width, $Height)
    $script:Form.Controls.Add($label)
    return $label
}

function Add-Box {
    param([int]$X, [int]$Y, [int]$Width, [int]$Height, [switch]$Multiline)
    $box = New-Object System.Windows.Forms.TextBox
    $box.SetBounds($X, $Y, $Width, $Height)
    if ($Multiline) { $box.Multiline = $true; $box.ScrollBars = 'Vertical' }
    $script:Form.Controls.Add($box)
    return $box
}

function Add-Button {
    param([string]$Text, [int]$X, [int]$Y, [int]$Width, [int]$Height)
    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.SetBounds($X, $Y, $Width, $Height)
    $script:Form.Controls.Add($button)
    return $button
}

$titleLabel = Add-Label 'Benchmark a fresh copy of AgenticFusionTemplate' 20 16 900 28
$titleLabel.Font = New-Object System.Drawing.Font('Segoe UI', 13, [System.Drawing.FontStyle]::Bold)
$introLabel = Add-Label 'Use a disposable Fusion project. The runner deletes only its local copy; Fusion cloud documents remain.' 20 47 1020 25

Add-Label 'Agent' 20 82 60 22 | Out-Null
$script:AgentCombo = New-Object System.Windows.Forms.ComboBox
$script:AgentCombo.DropDownStyle = 'DropDownList'
$script:AgentCombo.Items.AddRange(@('Codex', 'Claude Code'))
$script:AgentCombo.SelectedIndex = 0
$script:AgentCombo.SetBounds(84, 79, 145, 27)
$script:Form.Controls.Add($script:AgentCombo)
$script:PrepareButton = Add-Button 'Create copy, check setup, open agent' 245 77 285 32
$script:StatusLabel = Add-Label 'Choose an agent, then prepare the disposable copy.' 548 79 500 45

Add-Label 'Template commit' 20 128 130 22 | Out-Null
$script:VersionBox = Add-Box 150 125 300 26
$script:VersionBox.Text = Get-TemplateVersion
Add-Label 'Agent version' 470 128 115 22 | Out-Null
$script:AgentVersionBox = Add-Box 585 125 450 26
Add-Label 'Fusion version' 20 163 130 22 | Out-Null
$script:FusionVersionBox = Add-Box 150 160 300 26
Add-Label 'Model / effort' 470 163 115 22 | Out-Null
$script:ModelBox = Add-Box 585 160 450 26
Add-Label 'Credit / usage unit' 20 198 130 22 | Out-Null
$script:UnitBox = Add-Box 150 195 300 26
$script:UnitBox.Text = 'not recorded'
$script:SandboxLabel = Add-Label '' 470 198 565 42

$script:StepTitle = Add-Label 'B1-B7: prepare a copy to begin' 20 239 1015 28
$script:StepTitle.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$script:PrepLabel = Add-Label '' 20 274 1015 43
$script:PromptBox = Add-Box 20 321 1015 156 -Multiline
$script:PromptBox.ReadOnly = $true
$script:PromptBox.BackColor = [System.Drawing.Color]::White
$script:AcceptLabel = Add-Label '' 20 485 1015 62

$script:CopyButton = Add-Button 'Copy prompt' 20 550 125 32
$script:StartTimerButton = Add-Button 'Start timer' 155 550 125 32
$script:StopTimerButton = Add-Button 'Stop timer' 290 550 125 32
$script:RestartButton = Add-Button 'Open new agent session' 425 550 190 32
$script:TimerLabel = Add-Label 'Time: 00:00' 635 554 180 27
$script:TimerLabel.Font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)

Add-Label 'Usage delta' 20 602 110 22 | Out-Null
$script:UsageBox = Add-Box 130 599 220 26
Add-Label 'Acceptability' 372 602 100 22 | Out-Null
$script:RatingCombo = New-Object System.Windows.Forms.ComboBox
$script:RatingCombo.DropDownStyle = 'DropDownList'
$script:RatingCombo.Items.AddRange(@('1', '2', '3', '4', '5'))
$script:RatingCombo.SetBounds(476, 599, 75, 27)
$script:Form.Controls.Add($script:RatingCombo)
Add-Label '1 = unusable; 5 = fully acceptable' 570 602 430 22 | Out-Null
Add-Label 'Errors, corrections, and review notes' 20 640 1015 22 | Out-Null
$script:NotesBox = Add-Box 20 665 1015 70 -Multiline
$script:NextButton = Add-Button 'Next step' 875 742 160 32

$script:ClockTimer = New-Object System.Windows.Forms.Timer
$script:ClockTimer.Interval = 250
$script:ClockTimer.Add_Tick({
    if ($script:Stopwatch.IsRunning) { $script:TimerLabel.Text = 'Time: ' + (Format-Duration ([math]::Floor($script:Stopwatch.Elapsed.TotalSeconds))) }
})
$script:ClockTimer.Start()

$script:Preparation = @(
    'Open a new blank design in the disposable Fusion project before sending B1.',
    'Keep the same Fusion project and design. Send B2, then inspect the saved bracket.',
    'Select one mounting-hole feature in the Fusion timeline before sending B3.',
    'Keep the same design. B4 is analysis only.',
    'Keep the same design. B5 changes the existing wall-rise parameter.',
    'Keep the same design. B6 is a read-only printability review.',
    'Close the agent session, click Open new agent session, then send B7 in that new session.'
)

function Save-CurrentStep {
    if (-not $script:Sandbox) { return }
    $step = $script:Steps[$script:StepIndex]
    $step.Usage = $script:UsageBox.Text.Trim()
    $step.Rating = [string]$script:RatingCombo.Text
    $step.Notes = $script:NotesBox.Text.Trim()
}

function Show-Step {
    $step = $script:Steps[$script:StepIndex]
    $script:StepTitle.Text = $step.Title
    $script:PrepLabel.Text = $script:Preparation[$script:StepIndex]
    $script:PromptBox.Text = $step.Prompt
    $script:AcceptLabel.Text = 'Accept when: ' + $step.Accept
    $script:UsageBox.Text = $step.Usage
    $script:RatingCombo.Text = $step.Rating
    $script:NotesBox.Text = $step.Notes
    $script:TimerLabel.Text = 'Time: ' + (Format-Duration $step.Seconds)
    $script:RestartButton.Enabled = ($script:StepIndex -eq 6)
    $script:NextButton.Text = if ($script:StepIndex -eq 6) { 'Finish run' } else { 'Next step' }
}

foreach ($control in @($script:CopyButton, $script:StartTimerButton, $script:StopTimerButton,
                     $script:RestartButton, $script:UsageBox, $script:RatingCombo,
                     $script:NotesBox, $script:NextButton)) { $control.Enabled = $false }

$script:PrepareButton.Add_Click({
    $script:PrepareButton.Enabled = $false
    $script:Form.UseWaitCursor = $true
    $script:StatusLabel.Text = 'Copying template and checking both launchers...'
    $script:Form.Refresh()
    try {
        $script:Agent = [string]$script:AgentCombo.SelectedItem
        $script:RunRoot = New-RunRoot
        $script:Sandbox = Join-Path $script:RunRoot 'AgenticFusionTemplate'
        $other = Join-Path $script:RunRoot 'OtherLauncherFresh'
        Copy-Template $script:Sandbox
        Copy-Template $other
        $selectedLauncher = if ($script:Agent -eq 'Codex') { 'Fusion-Codex.bat' } else { 'Fusion-Claude.bat' }
        $otherLauncher = if ($script:Agent -eq 'Codex') { 'Fusion-Claude.bat' } else { 'Fusion-Codex.bat' }
        Test-LauncherSetup $script:Sandbox $selectedLauncher | Out-Null
        Test-LauncherSetup $other $otherLauncher | Out-Null
        Remove-Item -LiteralPath $other -Recurse -Force
        $script:AgentVersionBox.Text = Get-AgentVersion $script:Agent
        $script:SandboxLabel.Text = 'Local copy: ' + $script:Sandbox
        Start-BenchmarkAgent
        $script:StatusLabel.Text = 'Both setup checks passed. The agent is opening in the disposable copy.'
        $script:AgentCombo.Enabled = $false
        foreach ($control in @($script:CopyButton, $script:StartTimerButton, $script:StopTimerButton,
                             $script:UsageBox, $script:RatingCombo, $script:NotesBox, $script:NextButton)) {
            $control.Enabled = $true
        }
        Show-Step
    } catch {
        $message = $_.Exception.Message
        try { Remove-RunRoot $script:RunRoot; $script:RunRoot = $null; $script:Sandbox = $null } catch { $message += "`nCleanup: $($_.Exception.Message)" }
        [System.Windows.Forms.MessageBox]::Show($message, 'Preparation failed', 'OK', 'Error') | Out-Null
        $script:StatusLabel.Text = 'Preparation failed. Correct the issue and try again.'
        $script:PrepareButton.Enabled = $true
    } finally {
        $script:Form.UseWaitCursor = $false
    }
})

$script:CopyButton.Add_Click({
    [System.Windows.Forms.Clipboard]::SetText($script:Steps[$script:StepIndex].Prompt)
    $script:StatusLabel.Text = 'Prompt copied. Start the timer immediately before sending it.'
})

$script:StartTimerButton.Add_Click({
    $step = $script:Steps[$script:StepIndex]
    if ($null -ne $step.Seconds) {
        $choice = [System.Windows.Forms.MessageBox]::Show('Replace the recorded time for this prompt?', 'Restart timer', 'YesNo', 'Question')
        if ($choice -ne 'Yes') { return }
    }
    $step.Seconds = $null
    $script:Stopwatch.Restart()
    $script:TimerLabel.Text = 'Time: 00:00'
})

$script:StopTimerButton.Add_Click({
    if (-not $script:Stopwatch.IsRunning) { return }
    $script:Stopwatch.Stop()
    $script:Steps[$script:StepIndex].Seconds = [int][math]::Ceiling($script:Stopwatch.Elapsed.TotalSeconds)
    $script:TimerLabel.Text = 'Time: ' + (Format-Duration $script:Steps[$script:StepIndex].Seconds)
})

$script:RestartButton.Add_Click({
    $choice = [System.Windows.Forms.MessageBox]::Show(
        'Close the previous agent session before opening a new one. Is it closed?',
        'B7 session restart', 'YesNo', 'Question')
    if ($choice -ne 'Yes') { return }
    try { Start-BenchmarkAgent; $script:Restarted = $true; $script:StatusLabel.Text = 'New agent session opened for B7.' }
    catch { [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Agent launch failed', 'OK', 'Error') | Out-Null }
})

$script:NextButton.Add_Click({
    if ($script:Stopwatch.IsRunning) {
        [System.Windows.Forms.MessageBox]::Show('Stop the timer after the agent finishes.', 'Timer running', 'OK', 'Information') | Out-Null
        return
    }
    Save-CurrentStep
    $step = $script:Steps[$script:StepIndex]
    if ($null -eq $step.Seconds -or $step.Rating -notmatch '^[1-5]$') {
        [System.Windows.Forms.MessageBox]::Show('Record a time and an acceptability rating before continuing. Use rating 1 and explain in Notes if the step failed.', 'Step incomplete', 'OK', 'Information') | Out-Null
        return
    }
    if ($script:StepIndex -eq 6 -and -not $script:Restarted) {
        [System.Windows.Forms.MessageBox]::Show('Open a new agent session through the B7 button before finishing.', 'B7 restart required', 'OK', 'Information') | Out-Null
        return
    }
    if ($script:StepIndex -lt 6) {
        $script:StepIndex++
        Show-Step
        return
    }
    $choice = [System.Windows.Forms.MessageBox]::Show(
        'Save this run in Benchmarking.md under the current date?',
        'Save benchmark results', 'YesNo', 'Question')
    if ($choice -eq 'Yes' -and -not $script:Saved) {
        try { Save-BenchmarkResults; $script:Saved = $true }
        catch {
            [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Could not save results', 'OK', 'Error') | Out-Null
            return
        }
    }
    $closed = [System.Windows.Forms.MessageBox]::Show(
        'Close the benchmark agent window now so its local copy can be deleted. Is it closed?',
        'Clean up sandbox', 'YesNo', 'Question')
    if ($closed -ne 'Yes') { return }
    try {
        Remove-RunRoot $script:RunRoot
        $script:RunRoot = $null
        $script:Sandbox = $null
        $script:Finished = $true
        [System.Windows.Forms.MessageBox]::Show('The temporary local copy was deleted.', 'Benchmark complete', 'OK', 'Information') | Out-Null
        $script:Form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Could not delete the local copy. Close all windows using it and click Finish run again.`n$($_.Exception.Message)", 'Cleanup failed', 'OK', 'Error') | Out-Null
    }
})

$script:Form.Add_FormClosing({ param($sender, $eventArgs)
    if ($script:Finished -or -not $script:RunRoot) { return }
    $choice = [System.Windows.Forms.MessageBox]::Show(
        'Discard this unfinished run and delete its temporary local copy? Close the agent window first.',
        'Close benchmark', 'YesNo', 'Question')
    if ($choice -ne 'Yes') { $eventArgs.Cancel = $true; return }
    try { Remove-RunRoot $script:RunRoot; $script:RunRoot = $null; $script:Sandbox = $null }
    catch {
        $eventArgs.Cancel = $true
        [System.Windows.Forms.MessageBox]::Show("Could not delete the local copy. Close the agent window and try again.`n$($_.Exception.Message)", 'Cleanup failed', 'OK', 'Error') | Out-Null
    }
})

if ($UiSmokeTest) { $script:Form.Add_Shown({ $script:Form.Close() }) }
[void]$script:Form.ShowDialog()
if ($UiSmokeTest) { Write-Output 'Benchmark GUI initialized.' }
$script:ClockTimer.Stop()
$script:Form.Dispose()
