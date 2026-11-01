"""Choice, Windows activation and CLI regression checks; no real slicer is opened."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "AgenticFusionTemplate/.agents/skills/orca-slice/scripts/slicer.py"
spec = importlib.util.spec_from_file_location("slicer", SCRIPT)
slicer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(slicer)


class SlicerChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="slicer choice spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = self.root / "Snapmaker Orca" / "snapmaker-orca.exe"
        self.binary.parent.mkdir()
        self.binary.touch()
        self.app = slicer.normalize([{"name": "Snapmaker Orca", "version": "any-version",
                                     "executable": str(self.binary), "source": "test"}])[0]

    def args(self, **overrides):
        source = self.root / "prepared job.3mf"
        source.write_bytes(b"source geometry and settings")
        values = dict(input=source, output=self.root / "sliced job.3mf", settings=[], filaments=[],
                      embedded_profiles=True, plate=1, timeout=10, no_open=False)
        return argparse.Namespace(**(values | overrides))

    def test_duplicates_merge_but_distinct_installs_remain_and_ids_are_stable(self):
        path = str(self.binary)
        records = [dict(name="Orca", executable=path, source="registry"),
                   dict(name="Store Orca", executable=path.upper(), app_id="package!app", version="99.7", source="Store"),
                   dict(name="Orca portable", executable=path + "other.exe", source="shortcut")]
        found = slicer.normalize(records)
        self.assertEqual(len(found), 2)
        store = next(app for app in found if app.get("app_id"))
        self.assertEqual(store["sources"], ["Store", "registry"])
        self.assertEqual(store["id"], next(app for app in slicer.normalize(list(reversed(records))) if app.get("app_id"))["id"])
        self.assertEqual(len(slicer.normalize([dict(name="Orca Store", app_id="package!app", source="Start apps")])), 1)

    def test_list_never_launches_or_probes_and_supports_portable_executable(self):
        with mock.patch.object(slicer, "powershell", return_value=subprocess.CompletedProcess([], 0,
                json.dumps({"applications": [], "warnings": []}), "")), \
                mock.patch.object(slicer, "open_app") as launch, mock.patch.object(slicer, "probe") as probe, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(slicer.main(["list", "--executable", str(self.binary)]), 0)
        launch.assert_not_called()
        probe.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["applications"][0]["executable"], str(self.binary.resolve()))

    def test_noninteractive_single_result_still_needs_a_choice(self):
        with mock.patch.object(slicer.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(ValueError, "choice required"):
                slicer.choose([self.app])
        with self.assertRaisesRegex(ValueError, "no longer present"):
            slicer.choose([self.app], "stale-selection")
        self.assertEqual(slicer.choose([self.app], self.app["id"]), self.app)

    def test_choice_gate_prevents_open_and_probe_and_slice(self):
        for action in ("open", "probe", "slice"):
            args = [action]
            if action == "slice":
                args += ["--input", str(self.root / "input.3mf"), "--output", str(self.root / "out.3mf")]
            with self.subTest(action=action), mock.patch.object(slicer, "discover", return_value={"applications": [self.app], "warnings": []}), \
                    mock.patch.object(slicer.sys.stdin, "isatty", return_value=False), \
                    mock.patch.object(slicer, "open_app") as launch, mock.patch.object(slicer, "probe") as probe, \
                    mock.patch.object(slicer, "slice_file") as slicing, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(slicer.main(args), 1)
                launch.assert_not_called()
                probe.assert_not_called()
                slicing.assert_not_called()

    def test_terminal_choice_and_cancellation(self):
        with mock.patch.object(slicer.sys.stdin, "isatty", return_value=True), contextlib.redirect_stderr(io.StringIO()):
            with mock.patch("builtins.input", return_value="1"):
                self.assertEqual(slicer.choose([self.app]), self.app)
            with mock.patch("builtins.input", return_value="q"), self.assertRaisesRegex(ValueError, "cancelled"):
                slicer.choose([self.app])

    @unittest.skipUnless(os.name == "nt", "Windows activation")
    def test_store_file_activation_without_executable_uses_selected_identity(self):
        source = self.args().input
        app = dict(name="Orca Store", app_id="publisher.orca!app")
        with mock.patch.object(slicer, "powershell", return_value=subprocess.CompletedProcess([], 0, '{"pid":42}', "")) as activate, \
                mock.patch.object(slicer.subprocess, "Popen") as launch:
            self.assertEqual(slicer.open_app(app, source)["pid"], 42)
        self.assertEqual(activate.call_args.args, ("-AppId", app["app_id"], "-OpenFile", str(source.resolve())))
        launch.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows activation")
    def test_failed_store_activation_never_uses_another_app(self):
        with mock.patch.object(slicer, "powershell", return_value=subprocess.CompletedProcess([], 1, "", "contract unavailable")), \
                mock.patch.object(slicer.subprocess, "Popen") as launch, self.assertRaisesRegex(RuntimeError, "contract unavailable"):
            slicer.open_app(dict(name="Orca Store", app_id="publisher!app"))
        launch.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows activation")
    def test_desktop_file_arguments_preserve_spaces_and_normal_profile_directory(self):
        source = self.args().input
        with mock.patch.object(slicer.subprocess, "Popen", return_value=mock.Mock(pid=7)) as launch:
            result = slicer.open_app(self.app, source)
        self.assertEqual(launch.call_args.args[0], [str(self.binary), str(source)])
        self.assertNotIn("env", launch.call_args.kwargs)
        self.assertNotIn("shell", launch.call_args.kwargs)
        self.assertFalse(result["import_verified"])

    @unittest.skipUnless(os.name == "nt", "Windows activation")
    def test_store_file_contract_falls_back_only_to_its_manifest_executable(self):
        source = self.args().input
        with mock.patch.object(slicer, "powershell", return_value=subprocess.CompletedProcess([], 1, "", "no file contract")), \
                mock.patch.object(slicer.subprocess, "Popen", return_value=mock.Mock(pid=5)) as launch:
            result = slicer.open_app({**self.app, "app_id": "publisher!app"}, source)
        self.assertEqual(launch.call_args.args[0], [str(self.binary), str(source)])
        self.assertIn("no file contract", result["store_activation_error"])

    def test_cli_probe_uses_the_selected_binary_and_does_not_infer_capabilities(self):
        with mock.patch.object(slicer.subprocess, "run", return_value=subprocess.CompletedProcess([], 0,
                "Usage --slice N --export-3mf FILE", "--load-settings FILE")) as run:
            self.assertEqual(slicer.probe(self.app)["flags"], ["--export-3mf", "--load-settings", "--slice"])
        self.assertEqual(run.call_args.args[0], [str(self.binary), "--help"])
        self.assertEqual(slicer.probe(dict(app_id="publisher!app"))["flags"], [])

    def test_lifecycle_registration_uses_selected_store_identity_and_actual_pid(self):
        app = {**self.app, "app_id": "chosen.publisher!orca"}
        result_file = self.args().input
        with mock.patch.object(slicer.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"status":"registered"}', "")) as run:
            result = slicer.track_session(app, {"pid": 42}, result_file)
        command = run.call_args.args[0]
        self.assertEqual(result["status"], "registered")
        self.assertEqual(command[command.index("-ProcessId") + 1], "42")
        self.assertEqual(command[command.index("-AppId") + 1], app["app_id"])
        self.assertEqual(command[command.index("-RestoreFile") + 1], str(result_file.resolve()))
        self.assertIn("-StartMonitor", command)

    def test_lifecycle_failure_is_explicit_without_closing_the_opened_app(self):
        with mock.patch.object(slicer.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "PID already exited")), \
                mock.patch.object(slicer.subprocess, "Popen") as launch:
            result = slicer.track_session(self.app, {"pid": 42})
        self.assertEqual(result["status"], "unverified")
        self.assertIn("PID already exited", result["error"])
        launch.assert_not_called()

    def test_cli_missing_flags_profiles_and_stale_output_are_rejected_before_slicing(self):
        with mock.patch.object(slicer, "probe", return_value={"flags": []}), self.assertRaisesRegex(ValueError, "required CLI"):
            slicer.slice_file(self.app, self.args())
        with mock.patch.object(slicer, "probe") as probe:
            with self.assertRaisesRegex(ValueError, "verified machine"):
                slicer.slice_file(self.app, self.args(embedded_profiles=False))
            args = self.args()
            args.output.touch()
            with self.assertRaisesRegex(ValueError, "new .3mf"):
                slicer.slice_file(self.app, args)
            probe.assert_not_called()

    def test_slice_writes_provenance_verifies_gcode_and_opens_selected_result(self):
        args = self.args()

        def run(command, **kwargs):
            self.assertEqual(command[:2], [str(self.binary), str(args.input)])
            self.assertEqual(command[2:4], ["--slice", "1"])
            self.assertEqual(command[-2:], ["--export-3mf", str(args.output)])
            self.assertNotEqual(kwargs["cwd"], self.binary.parent)
            with zipfile.ZipFile(args.output, "w") as archive:
                archive.writestr("Metadata/plate_1.gcode", "G1 X1 Y1\n")
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(slicer, "probe", return_value={"flags": ["--slice", "--export-3mf"]}), \
                mock.patch.object(slicer.subprocess, "run", side_effect=run), \
                mock.patch.object(slicer, "open_app", return_value={"pid": 3}) as launch:
            result = slicer.slice_file(self.app, args)
        self.assertEqual(result["status"], "toolpaths_exported")
        self.assertTrue(result["review_required"])
        self.assertEqual(result["output_sha256"], slicer.sha256(args.output))
        launch.assert_called_once_with(self.app, args.output)
        saved = json.loads((Path(result["log"]).parent / "result.json").read_text())
        self.assertEqual(saved["input_sha256"], slicer.sha256(args.input))

    def test_failed_timeout_or_model_only_output_never_claims_slice_success(self):
        for failure in ("exit", "timeout", "no_gcode", "no_file"):
            args = self.args(output=self.root / (failure + ".3mf"))

            def run(command, **kwargs):
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(command, 10)
                if failure == "no_gcode":
                    with zipfile.ZipFile(args.output, "w") as archive:
                        archive.writestr("3D/model.model", "mesh only")
                return subprocess.CompletedProcess(command, 1 if failure == "exit" else 0)

            with self.subTest(failure=failure), mock.patch.object(slicer, "probe", return_value={"flags": ["--slice", "--export-3mf"]}), \
                    mock.patch.object(slicer.subprocess, "run", side_effect=run), \
                    mock.patch.object(slicer, "open_app") as launch, self.assertRaises(RuntimeError):
                slicer.slice_file(self.app, args)
            launch.assert_not_called()
        manifests = [json.loads(p.read_text()) for p in self.root.glob("slice-*/result.json")]
        self.assertEqual(len(manifests), 4)
        self.assertTrue(all(m["status"] == "failed" and "error" in m for m in manifests))

    @unittest.skipUnless(os.name == "nt", "Windows interop compiler")
    def test_real_store_activation_interop_compiles_without_activating_an_app(self):
        # Compile the exact shipped COM declarations; never call Open().
        command = "$code = Get-Content -LiteralPath $args[0] -Raw; $native = [regex]::Match($code, \"(?s)@'\\r?\\n(.*?)\\r?\\n'@\").Groups[1].Value; Add-Type -TypeDefinition $native -ErrorAction Stop"
        # -Command argument passing varies between PowerShell versions; use a temporary file.
        script = self.root / "compile.ps1"
        script.write_text(command, encoding="utf-8")
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                 "-File", str(script), str(slicer.WINDOWS_HELPER)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
