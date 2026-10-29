"""Start OrcaMCP and verify its embedded MCP; optionally configure both clients.

Python 3.11+, standard library only. No slicer tools or printer commands are called.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

if sys.version_info < (3, 11):
    raise SystemExit("Orca startup needs Python 3.11 or newer.")

import tomllib
from urllib import error, parse, request


class Unavailable(RuntimeError):
    pass


def local_url(value):
    url = parse.urlsplit(value)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or url.username or url.password or url.query or url.fragment
            or url.path != "/mcp"):
        raise ValueError("Use a loopback HTTP /mcp URL without credentials, query, or fragment.")
    # Validate a malformed port before launching an application.
    _ = url.port
    return value


class McpClient:
    def __init__(self, url, timeout=3):
        self.url = local_url(url)
        self.timeout = timeout
        self.session = None
        self.protocol = "2025-06-18"
        self.counter = 0
        self.opener = request.build_opener(request.ProxyHandler({}))

    def send(self, method, params=None, notify=False):
        self.counter += 1
        message = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            message["id"] = self.counter
        headers = {"Accept": "application/json, text/event-stream",
                   "Content-Type": "application/json"}
        if method != "initialize":
            headers["MCP-Protocol-Version"] = self.protocol
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = request.Request(self.url, json.dumps(message).encode(), headers, method="POST")
        try:
            with self.opener.open(req, timeout=self.timeout) as response:
                if method == "initialize":
                    self.session = response.headers.get("Mcp-Session-Id")
                if notify:
                    return None
                if "text/event-stream" in response.headers.get("Content-Type", ""):
                    chunks, size = [], 0
                    for raw_line in response:
                        size += len(raw_line)
                        if size > 4_000_000:
                            raise RuntimeError("MCP response exceeded 4 MB.")
                        line = raw_line.decode("utf-8").rstrip("\r\n")
                        if line.startswith("data:"):
                            chunks.append(line[5:].lstrip(" "))
                        elif not line and chunks:
                            result = json.loads("\n".join(chunks))
                            chunks = []
                            if result.get("id") == message["id"]:
                                return self.result(result, message["id"])
                    raise RuntimeError("MCP stream ended without the requested response.")
                payload = response.read(4_000_001)
                if len(payload) > 4_000_000:
                    raise RuntimeError("MCP response exceeded 4 MB.")
                return self.result(json.loads(payload), message["id"])
        except error.HTTPError as exc:
            raise RuntimeError(f"MCP HTTP {exc.code} at {self.url}; check the selected server/window.") from exc
        except (error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise Unavailable(f"MCP unavailable at {self.url}: {exc.reason if isinstance(exc, error.URLError) else exc}") from exc

    @staticmethod
    def result(message, expected_id):
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or message.get("id") != expected_id:
            raise RuntimeError("Endpoint did not return the expected MCP JSON-RPC response.")
        if "error" in message:
            raise RuntimeError(f"MCP error: {message['error'].get('message', 'unspecified')}")
        if not isinstance(message.get("result"), dict):
            raise RuntimeError("MCP result must be an object.")
        return message["result"]

    def close(self):
        if self.session:
            req = request.Request(self.url, method="DELETE", headers={
                "Mcp-Session-Id": self.session, "MCP-Protocol-Version": self.protocol})
            try:
                with self.opener.open(req, timeout=self.timeout):
                    pass
            except (error.URLError, TimeoutError, OSError):
                pass  # Session deletion is optional; never stop the application.


def inspect_mcp(url, timeout=3):
    client = McpClient(url, timeout)
    try:
        initialized = client.send("initialize", {
            "protocolVersion": client.protocol, "capabilities": {},
            "clientInfo": {"name": "agentic-fusion-startup", "version": "1.0.0"}})
        identity = initialized.get("serverInfo", {})
        if "orca" not in identity.get("name", "").lower():
            raise RuntimeError("Endpoint is not an Orca MCP server; refusing to select another application.")
        client.protocol = initialized.get("protocolVersion", "")
        if client.protocol not in {"2025-03-26", "2025-06-18", "2025-11-25"}:
            raise RuntimeError(f"Unsupported MCP protocol: {client.protocol}")
        client.send("notifications/initialized", notify=True)
        tools, cursor, seen = [], None, set()
        for _ in range(64):
            page = client.send("tools/list", {"cursor": cursor} if cursor else {})
            if not isinstance(page.get("tools"), list):
                raise RuntimeError("MCP tools/list did not return a tools array.")
            tools.extend(page["tools"])
            cursor = page.get("nextCursor")
            if not cursor:
                break
            if cursor in seen:
                raise RuntimeError("MCP repeated a tools pagination cursor.")
            seen.add(cursor)
        else:
            raise RuntimeError("MCP tool discovery exceeded 64 pages.")
        if not tools:
            raise RuntimeError("Orca MCP exposed no tools.")
        return {"server": identity, "protocol": client.protocol, "tool_count": len(tools)}
    finally:
        client.close()


def configure(project, url):
    """Prepare every change before writing; restore original bytes on write failure."""
    project = project.resolve(strict=True)
    if not (project / "Agentic-Fusion.md").is_file():
        raise ValueError("Select an initialized Agentic Fusion project containing Agentic-Fusion.md.")
    mcp_file, toml_file, settings_file = project / ".mcp.json", project / ".codex/config.toml", project / "settings.json"
    targets = [mcp_file, toml_file, settings_file]
    originals = {path: path.read_bytes() if path.exists() else None for path in targets}
    mcp = json.loads(originals[mcp_file] or b"{}")
    servers = mcp.setdefault("mcpServers", {})
    existing = servers.get("orcaslicer")
    if existing is not None and (existing.get("type") != "http" or existing.get("url") != url or "command" in existing):
        raise ValueError("Claude's orcaslicer entry differs; resolve it deliberately before configuring.")
    if existing is None:
        servers["orcaslicer"] = {"type": "http", "url": url}

    text = (originals[toml_file] or b"").decode("utf-8-sig")
    codex = tomllib.loads(text)
    existing = codex.get("mcp_servers", {}).get("orcaslicer")
    if existing is not None and existing.get("enabled") is False:
        raise ValueError("Orca is explicitly disabled in Codex; resolve that preference before enabling.")
    if existing is not None and (existing.get("url") != url or "command" in existing):
        raise ValueError("Codex's orcaslicer entry differs; resolve it deliberately before configuring.")
    if existing is None:
        text = text.rstrip() + '\n\n[mcp_servers.orcaslicer]\nurl = ' + json.dumps(url) + '\ntool_timeout_sec = 180\n'
    tomllib.loads(text)

    settings = json.loads(originals[settings_file] or b"{}")
    enabled = settings.setdefault("enabledMcpjsonServers", [])
    if not isinstance(enabled, list):
        raise ValueError("settings.json enabledMcpjsonServers must be an array.")
    disabled = settings.get("disabledMcpjsonServers", [])
    if "orcaslicer" in disabled:
        raise ValueError("Orca is explicitly disabled in settings.json; resolve that preference before enabling.")
    if "orcaslicer" not in enabled:
        enabled.append("orcaslicer")
    updates = {mcp_file: (json.dumps(mcp, indent=2, ensure_ascii=False) + "\n").encode(),
               toml_file: text.encode(),
               settings_file: (json.dumps(settings, indent=2, ensure_ascii=False) + "\n").encode()}
    written = []
    try:
        for path, content in updates.items():
            if originals[path] == content:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            written.append(path)
            path.write_bytes(content)
    except OSError as exc:
        restore_errors = []
        for path in reversed(written):
            try:
                if originals[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(originals[path])
            except OSError:
                restore_errors.append(str(path.relative_to(project)))
        if restore_errors:
            raise RuntimeError("Configuration write failed; could not restore: " + ", ".join(restore_errors)) from exc
        raise
    return [str(path.relative_to(project)) for path in written]


def executable_path(explicit):
    selected = explicit or os.environ.get("ORCAMCP_APP_PATH")
    if selected:
        path = Path(selected).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".exe":
            raise ValueError(f"OrcaMCP executable not found: {path}")
        return path
    roots = [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")]
    if os.environ.get("LOCALAPPDATA"):
        roots.append(str(Path(os.environ["LOCALAPPDATA"]) / "Programs"))
    for root in filter(None, roots):
        for name in ("orca-slicer.exe", "OrcaMCP.exe"):
            path = Path(root) / "OrcaMCP" / name
            if path.is_file():
                return path
    found = shutil.which("OrcaMCP.exe")
    if found:
        return Path(found)
    raise ValueError("Install the OrcaMCP community build outside the project, then pass --executable or set ORCAMCP_APP_PATH. Stock/vendor Orca is not auto-selected.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--executable")
    parser.add_argument("--mcp-url", default="http://127.0.0.1:13618/mcp")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=45, choices=range(1, 121), metavar="1..120")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--configure", action="store_true")
    mode.add_argument("--setup-only", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        url = local_url(args.mcp_url)
        if args.setup_only:
            changed = configure(args.project_dir, url)
            print(json.dumps({"status": "configured_only", "mcp_verified": False, "changed": changed}, indent=2))
            return 0
        launched = None
        try:
            info = inspect_mcp(url)
        except Unavailable:
            if args.check_only:
                raise
            binary = executable_path(args.executable)
            if os.name != "nt":
                raise ValueError("Application startup currently supports Windows; --check-only and --setup-only are portable.")
            local_app = os.environ.get("LOCALAPPDATA")
            if not args.data_dir and not local_app:
                raise ValueError("Pass --data-dir when LOCALAPPDATA is unavailable.")
            data_dir = (args.data_dir or Path(local_app) / "AgenticFusion/OrcaMCP").resolve()
            project = args.project_dir.resolve()
            if data_dir == project or project in data_dir.parents:
                raise ValueError("Keep OrcaMCP application data outside the portable project.")
            environment = dict(os.environ, ORCAMCP_SKIP_CLOUD_LOGIN="1")
            process = subprocess.Popen([str(binary), "--datadir", str(data_dir)], cwd=binary.parent,
                                       env=environment, creationflags=subprocess.CREATE_NO_WINDOW,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched = process.pid
            deadline = time.monotonic() + args.timeout
            while True:
                try:
                    info = inspect_mcp(url, timeout=min(3, max(.1, deadline - time.monotonic())))
                    break
                except Unavailable as exc:
                    if process.poll() is not None:
                        raise RuntimeError(f"OrcaMCP exited before MCP was ready (code {process.returncode}).") from exc
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"Startup timed out at {url}; inspect the app and its MCP port. The app was left open.") from exc
                    time.sleep(.5)
        changed = configure(args.project_dir, url) if args.configure else []
        print(json.dumps({"status": "ready", "mcp_url": url, "launched_pid": launched,
                          **info, "changed": changed,
                          "next": "Reconnect/restart client MCP after first registration; verify the intended plate and profiles."}, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError, AttributeError, TypeError) as exc:
        print(f"Orca startup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
