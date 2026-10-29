"""Startup/configuration regression checks; no installed slicer or printer needed."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import tomllib
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HELPER = Path(__file__).resolve().parents[1] / "AgenticFusionTemplate/.agents/skills/orca-slice/scripts/start_orca.py"
spec = importlib.util.spec_from_file_location("start_orca", HELPER)
orca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orca)


@contextlib.contextmanager
def endpoint(sse=False, name="orca-slicer"):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((msg, dict(self.headers)))
            method = msg["method"]
            if method != "initialize" and self.headers.get("Mcp-Session-Id") != "test-session":
                self.send_error(400)
                return
            if method == "notifications/initialized":
                self.send_response(202)
                self.end_headers()
                return
            if method == "initialize":
                result = {"serverInfo": {"name": name, "version": "test"},
                          "protocolVersion": "2025-06-18", "capabilities": {"tools": {}}}
            elif method == "tools/list":
                result = {"tools": [{"name": "inspect_plate", "inputSchema": {"type": "object"}}]}
                if not msg["params"].get("cursor"):
                    result["nextCursor"] = "second-page"
            else:
                self.send_error(400)
                return
            payload = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
            self.send_response(200)
            self.send_header("Mcp-Session-Id", "test-session")
            self.send_header("Content-Type", "text/event-stream" if sse else "application/json")
            self.end_headers()
            if sse:
                text = "event: message\n" + "\n".join("data: " + line for line in json.dumps(payload, indent=2).splitlines()) + "\n\n"
            else:
                text = json.dumps(payload)
            self.wfile.write(text.encode())

        def do_DELETE(self):
            calls.append(({"method": "DELETE"}, dict(self.headers)))
            self.send_response(204)
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/mcp", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class StartupChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="AgenticFusion-orca-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project with spaces"
        self.project.mkdir()
        (self.project / "Agentic-Fusion.md").write_text("shared context", encoding="utf-8")
        (self.project / "Project.md").write_text("verified geometry", encoding="utf-8")
        (self.project / "FDM-Slicing.md").write_text("user preferences", encoding="utf-8")
        (self.project / ".codex").mkdir()
        (self.project / ".mcp.json").write_text(json.dumps({"mcpServers": {
            "fusion": {"type": "http", "url": "http://127.0.0.1:27182/mcp"},
            "other": {"command": "preserve-me"}}}), encoding="utf-8")
        (self.project / ".codex/config.toml").write_text('# preserve comment\n[mcp_servers.fusion]\nurl = "http://127.0.0.1:27182/mcp"\n[other]\nvalue = 42\n', encoding="utf-8")
        (self.project / "settings.json").write_text(json.dumps({"enabledMcpjsonServers": ["fusion", "other"], "theme": "dark"}), encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}

    def test_json_and_sse_protocol_sessions_pagination_and_no_tool_calls(self):
        for sse in (False, True):
            with self.subTest(sse=sse), endpoint(sse) as (url, calls):
                info = orca.inspect_mcp(url)
                self.assertEqual(info["tool_count"], 2)
                self.assertEqual([m["method"] for m, _ in calls],
                                 ["initialize", "notifications/initialized", "tools/list", "tools/list", "DELETE"])
                self.assertIn("text/event-stream", calls[0][1]["Accept"])

    def test_configuration_preserves_context_fusion_other_servers_and_is_repeatable(self):
        before = self.snapshot()
        orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        after = self.snapshot()
        for name in ("Project.md", "FDM-Slicing.md", "Agentic-Fusion.md"):
            self.assertEqual(before[name], after[name])
        mcp = json.loads(after[".mcp.json"])
        self.assertEqual(mcp["mcpServers"]["other"]["command"], "preserve-me")
        codex = tomllib.loads(after[".codex/config.toml"].decode())
        self.assertEqual(codex["mcp_servers"]["fusion"]["url"], "http://127.0.0.1:27182/mcp")
        self.assertEqual(codex["other"]["value"], 42)
        self.assertTrue(after[".codex/config.toml"].startswith(b"# preserve comment"))
        self.assertEqual(json.loads(after["settings.json"])["enabledMcpjsonServers"], ["fusion", "other", "orcaslicer"])
        self.assertEqual(orca.configure(self.project, "http://127.0.0.1:13618/mcp"), [])
        self.assertEqual(after, self.snapshot())

    def test_conflicting_stdio_configuration_is_not_replaced(self):
        path = self.project / ".codex/config.toml"
        path.write_text(path.read_text() + '\n[mcp_servers.orcaslicer]\ncommand = "custom-bridge"\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "differs"):
            orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        self.assertEqual(before, self.snapshot())

    def test_explicit_disable_is_preserved(self):
        path = self.project / "settings.json"
        path.write_text(json.dumps({"disabledMcpjsonServers": ["orcaslicer"]}))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "disabled"):
            orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        self.assertEqual(before, self.snapshot())

    def test_failed_write_restores_original_configuration(self):
        before = self.snapshot()
        original_write = Path.write_bytes
        fail_once = [True]

        def write(path, data):
            if path.name == "settings.json" and fail_once[0]:
                fail_once[0] = False
                raise OSError("simulated write failure")
            return original_write(path, data)

        with mock.patch.object(Path, "write_bytes", write), self.assertRaises(OSError):
            orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        self.assertEqual(before, self.snapshot())

    def test_codex_disable_is_preserved_without_partial_changes(self):
        path = self.project / ".codex/config.toml"
        path.write_text(path.read_text() + '\n[mcp_servers.orcaslicer]\nurl = "http://127.0.0.1:13618/mcp"\nenabled = false\n')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "disabled"):
            orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        self.assertEqual(before, self.snapshot())

    def test_rollback_continues_when_one_file_remains_unwritable(self):
        before = self.snapshot()
        original_write = Path.write_bytes

        def write(path, data):
            if path.name == "settings.json":
                raise OSError("persistent write failure")
            return original_write(path, data)

        with mock.patch.object(Path, "write_bytes", write), self.assertRaisesRegex(RuntimeError, "could not restore"):
            orca.configure(self.project, "http://127.0.0.1:13618/mcp")
        self.assertEqual(before, self.snapshot())

    def test_setup_only_does_not_launch_or_verify(self):
        with mock.patch.object(orca.subprocess, "Popen") as launch, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(orca.main(["--project-dir", str(self.project), "--setup-only"]), 0)
        launch.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())["mcp_verified"])

    def test_running_server_is_reused_without_configuration_writes(self):
        before = self.snapshot()
        with endpoint() as (url, _), mock.patch.object(orca.subprocess, "Popen") as launch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(orca.main(["--project-dir", str(self.project), "--mcp-url", url, "--check-only"]), 0)
        launch.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_unrelated_server_is_not_selected_or_replaced(self):
        before = self.snapshot()
        with endpoint(name="unrelated-server") as (url, _), mock.patch.object(orca.subprocess, "Popen") as launch, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(orca.main(["--project-dir", str(self.project), "--mcp-url", url, "--configure"]), 1)
        launch.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_remote_endpoint_is_rejected_before_startup(self):
        with mock.patch.object(orca.subprocess, "Popen") as launch, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(orca.main(["--mcp-url", "http://192.0.2.1:13618/mcp"]), 1)
        launch.assert_not_called()

    @unittest.skipUnless(sys.platform == "win32", "Windows app launch path")
    def test_app_launch_uses_separate_data_directory_then_verifies(self):
        fake = mock.Mock(pid=123, returncode=None)
        fake.poll.return_value = None
        with mock.patch.object(orca, "inspect_mcp", side_effect=[orca.Unavailable("offline"), {"tool_count": 1}]), \
                mock.patch.object(orca, "executable_path", return_value=Path(self.temp.name) / "orca-slicer.exe"), \
                mock.patch.object(orca.subprocess, "Popen", return_value=fake) as launch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(orca.main(["--project-dir", str(self.project), "--data-dir", str(Path(self.temp.name) / "app data")]), 0)
        self.assertIn("--datadir", launch.call_args.args[0])
        self.assertEqual(launch.call_args.kwargs["env"]["ORCAMCP_SKIP_CLOUD_LOGIN"], "1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
