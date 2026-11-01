"""Lifecycle regression checks using mocked GUI processes; no live app is closed."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HELPER = Path(__file__).resolve().parents[1] / "AgenticFusionTemplate/.agents/scripts/application-session.ps1"
FIXTURE = r'''
param([string]$Helper, [string]$Project, [string]$Store, [string]$Case)
$ErrorActionPreference = 'Stop'
. $Helper -LibraryOnly -ProjectDir $Project -StateRoot $Store
$script:fakeApp = [pscustomobject]@{ process_id = 424242; name = 'Fusion360'; executable = 'C:\Apps\Fusion360.exe'; started_utc = [datetime]::UtcNow.AddHours(-13).ToString('o') }
$script:closeCalls = 0; $script:launchCalls = 0; $script:canClose = $true
function Get-AppIdentity([int]$TargetId) { if ($TargetId -eq 424242) { return $script:fakeApp }; return $null }
function Close-AppProcess($Entry) { $script:closeCalls++; return $script:canClose }
function Start-AppProcess($Entry) { $script:launchCalls++; return 424243 }
function Record-Checkpoint {
    $script:Action = 'Checkpoint'; $script:SavedStateVerified = $true
    $script:CleanupVerified = $true; $script:ApplicationIdle = $true
    $result = Invoke-SessionAction
    $script:CheckpointId = $result.application.checkpoint.id
    return $result
}
$script:ProcessId = 424242
$caught = $null; $result = $null
try {
    if ($Case -eq 'external_state') { $script:StateRoot = Join-Path $Project 'runtime-data' }
    if ($Case -eq 'agent_excluded') { $script:fakeApp.name = 'codex' }
    $script:Action = 'Register'; $registration = Invoke-SessionAction
    if ($Case -eq 'monitor_command') {
        function Start-Process {
            param($FilePath, $ArgumentList, $WindowStyle)
            $script:monitorCommand = @{ file = $FilePath; arguments = $ArgumentList; style = $WindowStyle }
        }
        Start-SessionMonitor
        $result = $script:monitorCommand
    } elseif ($Case -eq 'deadline') {
        $script:Action = 'Register'; $again = Invoke-SessionAction
        $script:Action = 'Status'; $result = Invoke-SessionAction
    } elseif ($Case -eq 'checkpoint_needs_cleanup') {
        $script:Action = 'Checkpoint'; $script:SavedStateVerified = $true; $script:ApplicationIdle = $true
        $result = Invoke-SessionAction
    } else {
        if ($Case -ne 'missing_checkpoint') { $checkpoint = Record-Checkpoint }
        $script:Action = 'Restart'; $script:UserApproved = $true; $script:ApplicationIdle = $true
        if ($Case -eq 'approval_required') { $script:UserApproved = $false }
        if ($Case -eq 'context_changed') { Add-Content -LiteralPath (Join-Path $Project 'Project.md') -Value 'new pending task' }
        if ($Case -eq 'expired_checkpoint') {
            $state = Read-SessionState
            $state.applications[0].checkpoint.saved_utc = [datetime]::UtcNow.AddMinutes(-6).ToString('o')
            Write-SessionState $state
        }
        if ($Case -eq 'pid_reused') { $script:fakeApp.started_utc = [datetime]::UtcNow.ToString('o') }
        if ($Case -eq 'close_blocked') { $script:canClose = $false }
        if ($Case -eq 'unused_close') { $script:Action = 'Close'; $script:UserApproved = $false; $script:UnusedVerified = $true }
        if ($Case -eq 'idle_required') { $script:ApplicationIdle = $false }
        $result = Invoke-SessionAction
    }
} catch { $caught = $_.Exception.Message }
@{ result = $result; error = $caught; close_calls = $script:closeCalls; launch_calls = $script:launchCalls;
    project_exists = (Test-Path -LiteralPath (Join-Path $Project 'Project.md')) } | ConvertTo-Json -Depth 20
'''


@unittest.skipUnless(os.name == "nt", "Windows process lifecycle helper")
class ApplicationSessionChecks(unittest.TestCase):
    def case(self, name):
        with tempfile.TemporaryDirectory(prefix="application session spaces ") as temporary:
            root = Path(temporary)
            project = root / "portable project"
            project.mkdir()
            (project / "Agentic-Fusion.md").write_text("Shared rules", encoding="utf-8")
            (project / "Project.md").write_text("# Current state\nPending: resume verified CAD work\n", encoding="utf-8")
            fixture = root / "fixture.ps1"
            fixture.write_text(FIXTURE, encoding="utf-8")
            result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                     "-File", str(fixture), str(HELPER), str(project), str(root / "external state"), name],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)

    def test_deadline_uses_real_process_age_and_reattachment_does_not_reset_it(self):
        result = self.case("deadline")
        self.assertIsNone(result["error"])
        app = result["result"]["applications"][0]
        self.assertGreaterEqual(app["runtime_hours"], 13)
        self.assertTrue(app["maintenance_due"])
        self.assertTrue(app["checkpoint_recommended"])
        self.assertTrue(result["result"]["block_new_application_work"])
        self.assertEqual(result["close_calls"], 0)

    def test_restart_requires_approval_checkpoint_idle_and_unchanged_identity_and_context(self):
        cases = {"approval_required": "approval", "missing_checkpoint": "checkpoint", "context_changed": "context changed",
                 "expired_checkpoint": "current checkpoint", "pid_reused": "identity changed", "idle_required": "idle"}
        for name, message in cases.items():
            with self.subTest(case=name):
                result = self.case(name)
                self.assertIn(message, result["error"])
                self.assertEqual(result["close_calls"], 0)
                self.assertEqual(result["launch_calls"], 0)

    def test_checkpoint_cannot_attest_unperformed_cleanup(self):
        result = self.case("checkpoint_needs_cleanup")
        self.assertIn("completed context-preserving cleanup", result["error"])
        self.assertEqual(result["close_calls"], 0)

    def test_blocked_close_does_not_force_quit_or_start_duplicate(self):
        result = self.case("close_blocked")
        self.assertIsNone(result["error"])
        self.assertEqual(result["result"]["status"], "close_pending_or_blocked")
        self.assertEqual(result["close_calls"], 1)
        self.assertEqual(result["launch_calls"], 0)

    def test_approved_restart_is_graceful_and_requires_post_launch_verification(self):
        result = self.case("approved_restart")
        self.assertIsNone(result["error"])
        self.assertEqual(result["close_calls"], 1)
        self.assertEqual(result["launch_calls"], 1)
        self.assertEqual(result["result"]["status"], "restart_launched_rebind_and_verify_required")
        self.assertTrue(result["project_exists"])

    def test_unused_application_can_close_without_restart_or_extra_approval(self):
        result = self.case("unused_close")
        self.assertIsNone(result["error"])
        self.assertEqual(result["result"]["status"], "closed")
        self.assertEqual(result["launch_calls"], 0)

    def test_ai_agents_and_runtime_inside_project_are_rejected(self):
        for name, message in (("agent_excluded", "AI agents"), ("external_state", "outside the portable project")):
            with self.subTest(case=name):
                result = self.case(name)
                self.assertIn(message, result["error"])
                self.assertEqual(result["close_calls"], 0)

    def test_monitor_uses_the_shipped_helper_and_hidden_window_with_quoted_paths(self):
        result = self.case("monitor_command")
        self.assertIsNone(result["error"])
        command = result["result"]
        self.assertEqual(command["style"], "Hidden")
        args = command["arguments"]
        self.assertEqual(args[args.index("-File") + 1], '"' + str(HELPER) + '"')
        self.assertEqual(args[args.index("-Action") + 1], "Watch")
        self.assertTrue(args[args.index("-ProjectDir") + 1].startswith('"'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
