"""Selected-agent bootstrap tests with fake CLIs/downloads; no software is installed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

LAUNCHER = Path(__file__).resolve().parents[1] / "AgenticFusionTemplate/Fusion-Claude.bat"
FIXTURE = r'''
param([string]$Launcher, [string]$Project, [string]$Agent, [string]$Case)
$ErrorActionPreference = 'Stop'
$source = [IO.File]::ReadAllText($Launcher)
$source = $source.Substring($source.LastIndexOf('#PS_BEGIN'))
$parseErrors = $null
$tree = [System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$null, [ref]$parseErrors)
if ($parseErrors) { throw ($parseErrors | Out-String) }
$definitions = @($tree.EndBlock.Statements | Where-Object { $_ -is [System.Management.Automation.Language.FunctionDefinitionAst] })
Invoke-Expression (($definitions | ForEach-Object { $_.Extent.Text }) -join "`n")

# Isolate discovery and all side effects in this disposable child process.
$env:USERPROFILE = Join-Path $Project 'User'
$env:LOCALAPPDATA = Join-Path $Project 'Local'
$env:APPDATA = Join-Path $Project 'Roaming'
$env:CODEX_INSTALL_DIR = if ($Case -eq 'custom_folder') { Join-Path $Project 'Custom Codex CLI' } else { $null }
$env:PATH = Join-Path $env:SystemRoot 'System32'
$env:SETUP_ONLY = if ($Case -eq 'setup_only') { '1' } else { '' }
$env:AGENT = $Agent
$ProjectDir = $Project; $TemplateDir = Split-Path -Parent $Launcher
$FusionPath = ''; $ProcessName = 'FixtureFusion'; $McpName = 'fusion'; $McpPort = 27182; $TimeoutSeconds = 1
$script:prompts = 0; $script:downloads = 0; $script:installs = 0; $script:refreshes = 0
$script:fusionLookups = 0; $script:repaired = @(); $script:downloadUri = $null; $script:installerPath = $null
$script:invocationLog = Join-Path $Project 'invocations.txt'
$script:info = Get-AgentInstallInfo -Agent $Agent
function Add-ToPath([string]$Dir) { $script:repaired += $Dir; $env:PATH = "$env:PATH;$Dir" }
function Refresh-SessionPath { $script:refreshes++ }
function Read-Host([string]$Prompt) {
    $script:prompts++
    if ($Case -eq 'no_input') { throw 'Non-interactive input unavailable' }
    if ($Case -eq 'decline') { return 'n' }
    if ($Case -eq 'blank') { return '' }
    return 'YES'
}
function New-FakeCli([string]$Name, [string]$Directory, [int]$VersionExit = 0) {
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $cli = Join-Path $Directory ($Name + '.cmd')
    [IO.File]::WriteAllText($cli, "@echo off`r`necho $Name %*>>`"$script:invocationLog`"`r`necho $Name test-version`r`nexit /b $VersionExit`r`n")
    return $cli
}
function Receive-AgentInstaller([string]$Uri, [string]$Destination) {
    $script:downloads++; $script:downloadUri = $Uri; $script:installerPath = $Destination
    if ($Case -eq 'download_failure') { throw 'fixture network unavailable' }
    $content = if ($Case -eq 'empty_download') { '' } else { '# mock official installer - never executed' }
    [IO.File]::WriteAllText($Destination, $content)
}
function Invoke-DownloadedInstaller([string]$InstallerFile) {
    $script:installs++
    if ($Case -eq 'installer_failure') { return 17 }
    if ($Case -eq 'missing_after_install') { return 0 }
    $versionExit = if ($Case -eq 'version_failure') { 3 } else { 0 }
    New-FakeCli $Agent $script:info.Directories[0] $versionExit | Out-Null
    return 0
}
function Initialize-ProjectFiles {}
function Ensure-ProjectMcp {}
function Ensure-CodexMcp {}
function Ensure-ProjectSettings { return (Join-Path $Project 'settings.json') }
function Test-ContextBudget { return $true }
function Get-Process {
    param([string]$Name)
    $script:fusionLookups++
    if ($script:fusionLookups -eq 1) { return [pscustomobject]@{ Id = 424242 } }
    return @()
}
function Find-FusionLauncher { return $null }
function Test-McpPort { return $true }

if ($Case -eq 'on_path') {
    $fakeBin = Join-Path $Project 'Existing CLI'
    New-FakeCli $Agent $fakeBin | Out-Null
    [IO.File]::WriteAllText((Join-Path $fakeBin ($Agent + '.ps1')), "throw 'The npm PowerShell shim must not run'")
    $env:PATH = "$fakeBin;$env:PATH"
}
if ($Case -in @('usual_folder','custom_folder')) { New-FakeCli $Agent $script:info.Directories[0] | Out-Null }
if ($Case -eq 'npm_folder') { New-FakeCli $Agent (Join-Path $env:APPDATA 'npm') | Out-Null }
if ($Case -eq 'other_present') {
    $other = if ($Agent -eq 'codex') { 'claude' } else { 'codex' }
    $fakeBin = Join-Path $Project 'Other CLI'
    New-FakeCli $other $fakeBin | Out-Null
    $env:PATH = "$fakeBin;$env:PATH"
}
$resolved = $null
if ($Case -in @('setup_only','full_start','decline_start')) {
    if ($Case -eq 'decline_start') { function Read-Host([string]$Prompt) { $script:prompts++; return 'n' } }
    Start-AgenticFusion
} else { $resolved = Confirm-AgentInstallation -Agent $Agent }
$calls = @()
if (Test-Path -LiteralPath $script:invocationLog) { $calls = @([IO.File]::ReadAllLines($script:invocationLog)) }
$report = @{ resolved = $resolved; prompts = $script:prompts; downloads = $script:downloads; installs = $script:installs;
    refreshes = $script:refreshes; repaired = @($script:repaired); uri = $script:downloadUri;
    temporary_removed = (-not $script:installerPath -or -not (Test-Path -LiteralPath $script:installerPath));
    fusion_lookups = $script:fusionLookups; invocations = $calls }
Write-Output ('RESULT:' + ($report | ConvertTo-Json -Depth 5 -Compress))
'''


@unittest.skipUnless(os.name == "nt", "Windows launcher bootstrap")
class AgentInstallationChecks(unittest.TestCase):
    def case(self, agent, name):
        with tempfile.TemporaryDirectory(prefix="agent install spaces ") as temporary:
            root = Path(temporary)
            project = root / "Project with spaces"
            project.mkdir()
            fixture = root / "fixture.ps1"
            fixture.write_text(FIXTURE, encoding="utf-8")
            result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                     "-File", str(fixture), str(LAUNCHER), str(project), agent, name],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("RESULT:", result.stdout, result.stdout + result.stderr)
            return json.loads(result.stdout.split("RESULT:", 1)[1])

    def test_existing_agent_or_usual_folder_needs_no_install_permission(self):
        for agent in ("claude", "codex"):
            names = ("on_path", "usual_folder", "npm_folder") + (("custom_folder",) if agent == "codex" else ())
            for name in names:
                with self.subTest(agent=agent, case=name):
                    result = self.case(agent, name)
                    self.assertTrue(result["resolved"].endswith(agent + ".cmd"))
                    self.assertEqual(result["prompts"], 0)
                    self.assertEqual(result["downloads"], 0)
                    self.assertEqual(len(result["repaired"]), int(name != "on_path"))

    def test_only_explicit_permission_allows_installation(self):
        for agent in ("claude", "codex"):
            for name in ("decline", "blank", "no_input"):
                with self.subTest(agent=agent, case=name):
                    result = self.case(agent, name)
                    self.assertFalse(result["resolved"])
                    self.assertEqual(result["downloads"], 0)
                    self.assertEqual(result["installs"], 0)

    def test_approved_install_is_selected_agent_only_even_when_the_other_exists(self):
        urls = {"claude": "https://claude.ai/install.ps1", "codex": "https://chatgpt.com/codex/install.ps1"}
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent):
                result = self.case(agent, "other_present")
                self.assertEqual(result["prompts"], 1)
                self.assertEqual(result["downloads"], 1)
                self.assertEqual(result["installs"], 1)
                self.assertEqual(result["refreshes"], 1)
                self.assertEqual(result["uri"], urls[agent])
                self.assertTrue(result["temporary_removed"])
                self.assertTrue(result["resolved"].endswith(agent + ".cmd"))
                self.assertEqual(result["invocations"], [agent + " --version"])

    def test_failed_download_installer_missing_cli_or_version_does_not_continue(self):
        for agent in ("claude", "codex"):
            for name in ("download_failure", "empty_download", "installer_failure", "missing_after_install", "version_failure"):
                with self.subTest(agent=agent, case=name):
                    result = self.case(agent, name)
                    self.assertFalse(result["resolved"])
                    self.assertTrue(result["temporary_removed"])
                    self.assertEqual(result["downloads"], 1)

    def test_setup_only_never_prompts_downloads_or_starts_fusion(self):
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent):
                result = self.case(agent, "setup_only")
                self.assertEqual(result["prompts"], 0)
                self.assertEqual(result["downloads"], 0)
                self.assertEqual(result["fusion_lookups"], 0)
                self.assertEqual(result["invocations"], [])

    def test_approved_install_continues_same_launch_and_decline_stops_before_fusion(self):
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent):
                result = self.case(agent, "full_start")
                self.assertGreater(result["fusion_lookups"], 0)
                self.assertEqual(len(result["invocations"]), 2)
                if agent == "claude":
                    self.assertIn("--settings", result["invocations"][1])
                    self.assertIn("--plugin-dir", result["invocations"][1])
                else:
                    self.assertEqual(result["invocations"][1].strip(), "codex")
                declined = self.case(agent, "decline_start")
                self.assertEqual(declined["fusion_lookups"], 0)
                self.assertEqual(declined["downloads"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
