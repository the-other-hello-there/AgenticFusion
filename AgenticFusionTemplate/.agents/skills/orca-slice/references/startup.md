# Startup and connection

## Supported backend

Use [okets/OrcaMCP](https://github.com/okets/OrcaMCP/tree/mcp), an OrcaSlicer community build with an embedded MCP server. Install its Windows build from its [releases](https://github.com/okets/OrcaMCP/releases) outside the project folder. Keep an existing vendor slicer and its profiles intact. This helper does not download/install software or copy credentials.

The embedded server starts with the application; a second bridge process is unnecessary for direct HTTP. The default endpoint is `http://127.0.0.1:13618/mcp`. The app can select a later port when one is occupied; confirm the intended window's port under Preferences > MCP and pass `--mcp-url`. Never silently select another window. Backend details: [OrcaMCP configuration](https://github.com/okets/OrcaMCP/blob/mcp/docs/setup/configuration.md).

Python 3.11+ is needed by the helper; `py -3 --version` checks the Windows launcher. No third-party Python packages are required. From the project folder:

```powershell
# Start/reuse the application and embedded MCP, then configure both clients.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure
# Explicit installation path; alternatively set ORCAMCP_APP_PATH for this machine.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure --executable 'C:\Tools\OrcaMCP\orca-slicer.exe'
# Inspect a running endpoint without launching or writing configuration.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --check-only
# Prepare both clients without launching or asserting that MCP is available.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --setup-only
```

The helper defaults to its containing project, independent of the terminal's current directory. `--project-dir` selects another initialized project. It accepts only loopback HTTP endpoints. `--configure` merges the Orca entry into `.mcp.json`, `.codex/config.toml`, and Claude's `settings.json`, preserving Fusion and unrelated settings. A conflicting existing Orca entry is reported for deliberate resolution, not overwritten. Setup-only configuration is explicitly unverified.

The app starts with an isolated data directory at `%LOCALAPPDATA%\AgenticFusion\OrcaMCP` (override using `--data-dir`) and agent startup dialogs skipped. Select/install the actual printer and material profiles before using it. Neither a profile nor a loaded model is chosen automatically. The helper leaves an application it started open if startup fails, so the user can inspect the window; it never kills an existing slicer.

## Recovery

- Missing executable: install OrcaMCP outside the project or supply its executable path. Auto-discovery looks in OrcaMCP installation folders and for `OrcaMCP.exe` on PATH; it does not guess that a stock/vendor executable has MCP.
- Occupied endpoint or wrong server identity: inspect the selected application's port. Do not replace another service or attach to another plate implicitly.
- Timeout: inspect the app, selected port, and profile/setup state, then retry once the cause is understood. An open TCP port alone is not success.
- Configured server missing from the current chat: reconnect/restart MCP in the client or start a new agent session. Project trust still applies. Configuration changes do not inject tools into an already-running chat.
- MaxEllis backend: it needs its separate stdio server, matching application, and token. This helper targets OrcaMCP's direct HTTP endpoint; do not point it at MaxEllis's REST port `13130`.
