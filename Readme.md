# Agentic Fusion

A portable Windows project template for working with Autodesk Fusion's local MCP server through **Claude Code or Codex**. The reusable folder is [`AgenticFusionTemplate/`](AgenticFusionTemplate/). Run either launcher from a copy of that folder; both prepare the same project files, start Fusion if needed, wait for the MCP port, and open the chosen agent.

## Install Fusion and an agent

1. Install the [Fusion desktop application](https://help.autodesk.com/view/fusion360/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FHow-to-download-Fusion-360.html) and sign in. The local MCP server runs in the desktop application.
2. Install one or both agents:
   - **Claude Code:** use Anthropic's [Windows setup guide](https://code.claude.com/docs/en/setup). In PowerShell: `irm https://claude.ai/install.ps1 | iex`. Open a new terminal and check `claude --version`.
   - **Codex CLI:** use OpenAI's [Codex CLI guide](https://learn.chatgpt.com/docs/codex/cli) and [Windows installer](https://learn.chatgpt.com/docs/config-file/environment-variables). In PowerShell: `irm https://chatgpt.com/codex/install.ps1 | iex`. Open a new terminal and check `codex --version`.
3. Sign in when the chosen agent first opens. Its credentials stay in its normal user profile, outside the project template.

## Enable Fusion MCP

In Fusion, open **Preferences > General > API** and enable **Fusion MCP Server (runs locally on this device)**. Note the port; its default is **27182**. Open the design you want to inspect or edit. See [Autodesk's connection instructions](https://help.autodesk.com/view/fusion360/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html).

Both project configurations target `http://127.0.0.1:27182/mcp`: Claude uses `.mcp.json`, and Codex uses `.codex/config.toml`. If Fusion displays another port, change `$McpPort` near the top of `Fusion-Claude.bat` in your project copy. This shared launcher then updates **both** project MCP entries when either batch file runs. Changing only a JSON or TOML URL will be undone by the next launcher run.

## Start a project

1. Copy the **inner** [`AgenticFusionTemplate/`](AgenticFusionTemplate/) folder anywhere and rename the copy for your project. You can also unpack [`AgenticFusionTemplate.zip`](AgenticFusionTemplate.zip), which contains the same project files. Keep its supplied files and `.codex/` together; leave the repository `.git/` behind.
2. Run `Fusion-Claude.bat` for Claude Code or `Fusion-Codex.bat` for Codex. The launchers create `Project.md` only if it is missing, prepare both agents' local MCP configurations, start Fusion if needed, wait up to 120 seconds for its server, and then launch the chosen agent in the project folder. Codex may ask you to trust the project before using its project-scoped MCP configuration.
3. In `Project.md`, record verified design intent, interfaces, parameters, document names, decisions, and open items. The two agent entry files direct their agents to read it and the shared Fusion rules.

You may drag an existing project folder onto either launcher in the template. Missing template files, including both launchers, are copied into that project without replacing existing context. To prepare files without opening Fusion or an agent, run `./Fusion-Claude.bat --setup-only` or `./Fusion-Codex.bat --setup-only` from PowerShell in a copied project folder. Each batch file uses the same setup routine.

### Check the connection

Inside the chosen agent, check `/mcp` for the `fusion` server. From a terminal in the project folder, `claude mcp list` or `codex mcp list` can also inspect configured servers. A safe first prompt is: “List the active Fusion document and its components without changing the design.” See the [Claude MCP guide](https://code.claude.com/docs/en/mcp) and [Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

If the server is disconnected, check that Fusion is running, its MCP option is enabled, a design is open, and the Fusion port matches `$McpPort`. If Fusion cannot be found automatically, start it yourself or set `$FusionPath` in `Fusion-Claude.bat` to its launcher path. If an agent executable is missing, reopen the terminal and check its version command. Codex project MCP settings load only after the project is trusted; if the server is absent from `codex mcp list`, check trust and restart Codex from the project folder.

## Project files

| File | Role |
| --- | --- |
| `Fusion-Claude.bat`, `Fusion-Codex.bat` | Shared first-run setup and Fusion startup; launch the chosen agent. |
| `Agentic-Fusion.md` | Shared, always-used Fusion design, modeling, MCP, saving, and document rules. |
| `CLAUDE.md`, `AGENTS.md` | Small agent-specific startup and tool instructions. |
| `.mcp.json`, `settings.json` | Claude Code project MCP and agent settings. |
| `.codex/config.toml` | Codex project MCP connection. |
| `DfAM.md` | Printing guidance loaded for fabrication tasks. |
| `Fusion-Failure-Repair.md` | Symptom-specific repair guidance loaded after failures. |
| `Project.md` | Created on first run for this design's verified context and decisions. |

Fusion designs remain in Fusion's documents. Do not put agent credentials or generated agent runtime folders into a project copy.

## Benchmarking

Use the [benchmark prompts and results sheet](Benchmarking.md) to record time, usage, and result quality by template and agent version.
