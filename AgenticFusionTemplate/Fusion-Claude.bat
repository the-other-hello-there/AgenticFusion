@echo off
rem =====================================================================
rem  Agentic Fusion launcher (single file: batch header + PowerShell)
rem  - Double-click: uses the folder this file is in as the project folder
rem  - Or drag a project folder onto this file to use that folder instead
rem  - Fusion-Codex.bat calls this file with --codex to launch Codex
rem  - Fixes PATH if the selected agent can't be found
rem  - Initializes missing project files and ensures the Fusion MCP settings
rem  - Use --setup-only to initialize without opening Fusion or an agent
rem  Edit the settings in the PowerShell section below if needed.
rem =====================================================================
setlocal
set "SELF=%~f0"
set "PROJDIR=%~dp0"
set "SETUP_ONLY="
set "AGENT=claude"
:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--setup-only" set "SETUP_ONLY=1"
if /I "%~1"=="--codex" set "AGENT=codex"
if /I not "%~1"=="--setup-only" if /I not "%~1"=="--codex" set "PROJDIR=%~1"
shift
goto parse_args
:args_done
set "PS_ARGS=-NoExit"
if defined SETUP_ONLY set "PS_ARGS="
powershell.exe -NoProfile -ExecutionPolicy Bypass %PS_ARGS% -Command "$f=[System.IO.File]::ReadAllText($env:SELF); $i=$f.LastIndexOf('#PS_BEGIN'); Invoke-Expression $f.Substring($i)"
goto :eof

#PS_BEGIN
# ----------------------------- Settings ------------------------------
$FusionPath     = ""          # optional: full path to Fusion .exe or .lnk
$ProcessName    = "Fusion360" # process name used to detect a running Fusion
$McpName        = "fusion"    # name the MCP server is registered under
$McpPort        = 27182       # Fusion MCP server port
$TimeoutSeconds = 120         # how long to wait for the MCP server
$ProjectDir     = $env:PROJDIR
$TemplateDir    = Split-Path -Parent $env:SELF
# ---------------------------------------------------------------------

function Test-McpPort {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if ($iar.AsyncWaitHandle.WaitOne(500) -and $client.Connected) {
            $client.EndConnect($iar)
            return $true
        }
        return $false
    }
    catch { return $false }
    finally { $client.Close() }
}

function Find-FusionLauncher {
    $roots = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
    )
    foreach ($root in $roots) {
        if (Test-Path -LiteralPath $root) {
            $lnk = Get-ChildItem -LiteralPath $root -Recurse -Filter "*Fusion*.lnk" -ErrorAction SilentlyContinue |
                   Where-Object { $_.Name -notmatch "Uninstall|Update|Manager|Help|Documentation" } |
                   Select-Object -First 1
            if ($lnk) { return $lnk.FullName }
        }
    }
    return $null
}

# Adds a folder to the persistent user PATH (no duplicates) AND to this
# session's PATH. Programs started from Explorer don't see PATH changes
# until restart, so fixing the current session is what makes it work now.
function Add-ToPath {
    param([string]$Dir)
    $want = $Dir.TrimEnd('\')

    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    $entries = @()
    if ($userPath) { $entries = @($userPath.Split(';') | Where-Object { $_ }) }
    $inUser = $entries | Where-Object { $_.TrimEnd('\') -ieq $want }
    if (-not $inUser) {
        [Environment]::SetEnvironmentVariable('PATH', (($entries + $Dir) -join ';'), 'User')
        Write-Host "Added $Dir to your user PATH." -ForegroundColor Yellow
    }

    $procEntries = @($env:PATH.Split(';') | Where-Object { $_ })
    $inProc = $procEntries | Where-Object { $_.TrimEnd('\') -ieq $want }
    if (-not $inProc) { $env:PATH = "$env:PATH;$Dir" }
}

function Confirm-Claude {
    if (Get-Command claude -ErrorAction SilentlyContinue) { return $true }
    Write-Host "'claude' not found on PATH - looking for it..." -ForegroundColor Yellow
    $candidates = @("$env:USERPROFILE\.local\bin", "$env:APPDATA\npm")
    foreach ($dir in $candidates) {
        if ((Test-Path -LiteralPath "$dir\claude.exe") -or (Test-Path -LiteralPath "$dir\claude.cmd")) {
            Add-ToPath -Dir $dir
            if (Get-Command claude -ErrorAction SilentlyContinue) { return $true }
        }
    }
    return $false
}

function Confirm-Codex {
    if (Get-Command codex -ErrorAction SilentlyContinue) { return $true }
    Write-Host "'codex' not found on PATH - looking for it..." -ForegroundColor Yellow
    $candidates = @("$env:LOCALAPPDATA\Programs\OpenAI\Codex\bin", "$env:APPDATA\npm")
    foreach ($dir in $candidates) {
        if ((Test-Path -LiteralPath "$dir\codex.exe") -or (Test-Path -LiteralPath "$dir\codex.cmd")) {
            Add-ToPath -Dir $dir
            if (Get-Command codex -ErrorAction SilentlyContinue) { return $true }
        }
    }
    return $false
}

function Write-ProjectJson {
    param([string]$File, [object]$Data)
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($File, (($Data | ConvertTo-Json -Depth 20) + "`n"), $utf8)
}

function Initialize-ProjectFiles {
    $portable = @(
        'Fusion-Claude.bat', 'Fusion-Codex.bat', 'Agentic-Fusion.md', 'DfAM.md', 'CLAUDE.md', 'AGENTS.md',
        '.mcp.json', 'settings.json', '.codex\config.toml',
        '.agents\.claude-plugin\plugin.json',
        '.agents\skills\fusion-model\SKILL.md',
        '.agents\skills\fusion-model\references\design-and-assembly.md',
        '.agents\skills\fusion-model\references\mcp.md',
        '.agents\skills\fusion-model\references\timeline.md',
        '.agents\skills\fusion-model\references\helpers.md',
        '.agents\skills\fusion-model\references\components.md',
        '.agents\skills\fusion-model\references\sketches-and-features.md',
        '.agents\skills\fusion-model\references\fillets.md',
        '.agents\skills\fusion-print\SKILL.md',
        '.agents\skills\fusion-print\references\sizes-and-fits.md',
        '.agents\skills\fusion-print\references\overhangs-and-bed.md',
        '.agents\skills\fusion-print\references\voids-and-cables.md',
        '.agents\skills\fusion-print\references\mechanisms-and-fasteners.md',
        '.agents\skills\fusion-print\references\orientation.md',
        '.agents\skills\fusion-print\references\scan.md',
        '.agents\skills\fusion-print\references\improvement.md',
        '.agents\skills\fusion-repair\SKILL.md',
        '.agents\skills\fusion-repair\references\mcp-and-save.md',
        '.agents\skills\fusion-repair\references\document-state.md',
        '.agents\skills\fusion-repair\references\geometry.md'
    )
    foreach ($name in $portable) {
        $source = Join-Path $TemplateDir $name
        $target = Join-Path $ProjectDir $name
        if (-not (Test-Path -LiteralPath $target)) {
            if (-not (Test-Path -LiteralPath $source)) { throw "Missing template file: $source" }
            $targetDir = Split-Path -Parent $target
            if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
            Copy-Item -LiteralPath $source -Destination $target
            Write-Host "Created $name" -ForegroundColor Yellow
        }
    }
    $projectFile = Join-Path $ProjectDir 'Project.md'
    if (-not (Test-Path -LiteralPath $projectFile)) {
        $starter = @'
# Project: TBD

## Current state

- **Design purpose:** TBD
- **Active Fusion document:** TBD
- **Interfaces and constraints:** TBD
- **Key parameters and expressions:** TBD
- **Accepted decisions and verified geometry:** TBD
- **Open items:** TBD

This file holds the current design intent and decisions for this design only. Keep this section concise and see `Agentic-Fusion.md` for context size and placement rules.

## Details index

- Add links to deeper sections here only when this project needs them.
'@
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($projectFile, ($starter + "`n"), $utf8)
        Write-Host 'Created Project.md' -ForegroundColor Yellow
    }
}

function Ensure-ProjectMcp {
    $file = Join-Path $ProjectDir '.mcp.json'
    try { $json = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json }
    catch { throw "Invalid .mcp.json; fix it before launching: $file" }
    if (-not $json.mcpServers) {
        $json | Add-Member -MemberType NoteProperty -Name 'mcpServers' -Value ([pscustomobject]@{}) -Force
    }
    $url = "http://127.0.0.1:$McpPort/mcp"
    $entry = $json.mcpServers.PSObject.Properties[$McpName]
    if (-not $entry -or $entry.Value.type -ne 'http' -or $entry.Value.url -ne $url) {
        $json.mcpServers | Add-Member -MemberType NoteProperty -Name $McpName -Value ([pscustomobject]@{type='http'; url=$url}) -Force
        Write-ProjectJson -File $file -Data $json
        Write-Host "Configured project Fusion MCP server: $url" -ForegroundColor Yellow
    }
}

function Ensure-CodexMcp {
    $file = Join-Path $ProjectDir '.codex\config.toml'
    $content = [System.IO.File]::ReadAllText($file)
    $url = "http://127.0.0.1:$McpPort/mcp"
    $line = 'url = "' + $url + '"'
    $pattern = '(?ms)(^\[mcp_servers\.fusion\][ \t]*\r?\n)(.*?)(?=^\[|\z)'
    $match = [regex]::Match($content, $pattern)
    if ($match.Success) {
        $section = $match.Groups[2].Value
        if ($section -match '(?m)^[ \t]*url[ \t]*=') {
            $updated = [regex]::new('(?m)^[ \t]*url[ \t]*=[^\r\n]*').Replace($section, $line, 1)
        }
        else { $updated = $line + "`n" + $section }
        $content = $content.Substring(0, $match.Groups[2].Index) + $updated + $content.Substring($match.Groups[2].Index + $match.Groups[2].Length)
    }
    else { $content = $content.TrimEnd() + "`n`n[mcp_servers.fusion]`n$line`n" }
    if ($content -ne [System.IO.File]::ReadAllText($file)) {
        [System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding($false)))
        Write-Host "Configured Codex Fusion MCP server: $url" -ForegroundColor Yellow
    }
}

function Ensure-ProjectSettings {
    $file = Join-Path $ProjectDir 'settings.json'
    try { $json = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json }
    catch { throw "Invalid settings.json; fix it before launching: $file" }
    $changed = $false
    $enabled = @($json.enabledMcpjsonServers | Where-Object { $_ })
    if ($enabled -notcontains $McpName) {
        $enabled += $McpName
        $json | Add-Member -MemberType NoteProperty -Name 'enabledMcpjsonServers' -Value $enabled -Force
        $changed = $true
    }
    if (-not $json.PSObject.Properties['autoMemoryEnabled'] -or $json.autoMemoryEnabled -ne $false) {
        $json | Add-Member -MemberType NoteProperty -Name 'autoMemoryEnabled' -Value $false -Force
        $changed = $true
    }
    if ($changed) {
        Write-ProjectJson -File $file -Data $json
        Write-Host 'Enabled the Fusion server and disabled Claude auto-memory.' -ForegroundColor Yellow
    }
    return $file
}

function Test-ContextBudget {
    $projectFile = Join-Path $ProjectDir 'Project.md'
    $projectChars = [System.IO.File]::ReadAllText($projectFile).Length
    if ($projectChars -gt 40000) {
        Write-Warning "Project.md has about $projectChars characters; the shared guide targets 40,000. Preserve unique facts while cleaning it."
    }

    if ($env:AGENT -ne 'claude') { return $true }
    $claudeFile = Join-Path $ProjectDir 'CLAUDE.md'
    $claudeText = [System.IO.File]::ReadAllText($claudeFile)
    $importChars = $claudeText.Length
    $legacyImports = @()
    foreach ($name in @('Agentic-Fusion.md', 'Project.md')) {
        if ($claudeText -match "(?m)^\s*@$([regex]::Escape($name))\s*$") {
            $legacyImports += $name
            $importChars += [System.IO.File]::ReadAllText((Join-Path $ProjectDir $name)).Length
        }
    }
    if ($legacyImports.Count -gt 0) {
        Write-Warning "This copy's CLAUDE.md still imports $($legacyImports -join ' and ') in full. Update it to use the short shared guide and selective Project.md reading."
    }
    if ($importChars -gt 150000) {
        if ($env:SETUP_ONLY -eq '1') {
            Write-Warning "A Claude launch would be stopped: these instruction files total about $importChars characters, above the observed 150,000-character limit. The existing files were not changed."
        }
        else {
            Write-Host "Claude launch stopped: these instruction files total about $importChars characters, above the observed 150,000-character limit. The existing files were not changed." -ForegroundColor Red
        }
        return $false
    }
    return $true
}

function Start-AgenticFusion {
    $ErrorActionPreference = "Stop"

    if (-not (Test-Path -LiteralPath $ProjectDir)) {
        Write-Host "Project folder not found: $ProjectDir" -ForegroundColor Red
        return
    }
    $ProjectDir = (Resolve-Path -LiteralPath $ProjectDir).Path
    Initialize-ProjectFiles
    Ensure-ProjectMcp
    Ensure-CodexMcp
    $settingsFile = Ensure-ProjectSettings
    $contextFits = Test-ContextBudget
    if ($env:SETUP_ONLY -eq '1') {
        Write-Host "Project initialized: $ProjectDir" -ForegroundColor Green
        return
    }
    if (-not $contextFits) { return }

    if ($env:AGENT -eq 'codex') {
        if (-not (Confirm-Codex)) {
            Write-Host "Codex ('codex') was not found on PATH or in the usual install folders. Install it, then run this again." -ForegroundColor Red
            return
        }
    }
    else {
        # Claude account and runtime data stay in its normal user config, outside the portable folder.
        Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
        if (-not (Confirm-Claude)) {
            Write-Host "Claude Code ('claude') was not found on PATH or in the usual install folders. Install it, then run this again." -ForegroundColor Red
            return
        }
    }
    Set-Location -LiteralPath $ProjectDir

    # Start Fusion if it isn't running.
    if (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue) {
        Write-Host "Fusion is already running." -ForegroundColor Green
    }
    else {
        $launcher = if ($FusionPath) { $FusionPath } else { Find-FusionLauncher }
        if (-not $launcher) {
            Write-Host "Couldn't find a Fusion launcher. Set `$FusionPath at the top of this file." -ForegroundColor Red
            return
        }
        Write-Host "Starting Fusion: $launcher"
        Start-Process -FilePath $launcher
    }

    # Wait for the Fusion MCP server.
    if (Test-McpPort -Port $McpPort) {
        Write-Host "Fusion MCP server is up on port $McpPort." -ForegroundColor Green
    }
    else {
        Write-Host "Waiting for Fusion MCP server on 127.0.0.1:$McpPort (up to $TimeoutSeconds s)..."
        $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
        $ready = $false
        while ((Get-Date) -lt $deadline) {
            if (Test-McpPort -Port $McpPort) { $ready = $true; break }
            Start-Sleep -Seconds 2
        }
        if ($ready) {
            Write-Host "Fusion MCP server is up." -ForegroundColor Green
        }
        else {
            Write-Warning "MCP server not detected. Open a design in Fusion and tick Preferences > General > API > 'Fusion MCP Server'. Starting $($env:AGENT) anyway."
        }
    }

    if ($env:AGENT -eq 'codex') {
        Write-Host "Starting Codex in $ProjectDir" -ForegroundColor Cyan
        codex
    }
    else {
        Write-Host "Starting Claude Code in $ProjectDir" -ForegroundColor Cyan
        claude --settings $settingsFile --plugin-dir (Join-Path $ProjectDir '.agents')
    }
}

try { Start-AgenticFusion }
catch { Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red }
