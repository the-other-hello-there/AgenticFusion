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

1. Copy the **inner** [`AgenticFusionTemplate/`](AgenticFusionTemplate/) folder anywhere and rename the copy for your project. Keep its supplied files, `.agents/`, and `.codex/` together; leave the repository `.git/` behind.
2. Run `Fusion-Claude.bat` for Claude Code or `Fusion-Codex.bat` for Codex. The launchers create `Project.md` only if it is missing, prepare both agents' local MCP configurations, start Fusion if needed, wait up to 120 seconds for its server, and then launch the chosen agent in the project folder. Codex may ask you to trust the project before using its project-scoped MCP configuration.
3. In `Project.md`, keep the `Current state` section concise and record verified design intent, interfaces, parameters, document names, decisions, and open items. The two agent entry files direct their agents to read that section and the short shared Fusion guide.

The Claude launcher loads `.agents/` as a local plugin with `--plugin-dir`; Codex discovers the same skill files in `.agents/skills/`. Launch Claude through `Fusion-Claude.bat` to make the shared skills available. The short shared guide routes modeling, printing, and repair to one physical set of skills used by both agents. Each skill reads detailed references only when the task needs them. Claude's `CLAUDE.md` does not automatically import the full `Project.md`.

You may drag an existing project folder onto either launcher in the template. Missing template files, including both launchers, are copied into that project without replacing existing context. To prepare files without opening Fusion or an agent, run `./Fusion-Claude.bat --setup-only` or `./Fusion-Codex.bat --setup-only` from PowerShell in a copied project folder. Each batch file uses the same setup routine.

An older project copy keeps its existing launcher and instruction files during setup. To remove Claude's instruction-size overflow in an older copy, update its `CLAUDE.md` to remove `@Project.md` and `@Agentic-Fusion.md`, then bring over the short shared guide and skill routing after preserving project-specific edits. Setup copies missing skills but does not replace existing context. If `Project.md` is large, follow the shared guide's cleanup rule; retain current facts there and index any necessary historical detail in `Project-History/`.

The shared launcher warns when `Project.md` exceeds the 40,000-character target. For Claude, it also detects legacy full-file imports and stops before launch if their combined text exceeds the observed 150,000-character instruction limit. It does not rewrite existing project context.

### Check the connection

Inside the chosen agent, check `/mcp` for the `fusion` server. From a terminal in the project folder, `claude mcp list` or `codex mcp list` can also inspect configured servers. A safe first prompt is: “List the active Fusion document and its components without changing the design.” See the [Claude MCP guide](https://code.claude.com/docs/en/mcp) and [Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

If the server is disconnected, check that Fusion is running, its MCP option is enabled, a design is open, and the Fusion port matches `$McpPort`. If Fusion cannot be found automatically, start it yourself or set `$FusionPath` in `Fusion-Claude.bat` to its launcher path. If an agent executable is missing, reopen the terminal and check its version command. Codex project MCP settings load only after the project is trusted; if the server is absent from `codex mcp list`, check trust and restart Codex from the project folder.

## Project files

| File | Role |
| --- | --- |
| `Fusion-Claude.bat`, `Fusion-Codex.bat` | Shared first-run setup and Fusion startup; launch the chosen agent. |
| `Agentic-Fusion.md` | Short, always-read shared design priorities, routing, memory placement, and size rules. |
| `DfAM.md` | Optional protocol for a requested broad DfAM assessment; technical methods stay in the shared printing skill. |
| `CLAUDE.md`, `AGENTS.md` | Small agent-specific startup and tool instructions. |
| `.mcp.json`, `settings.json` | Claude Code project MCP and agent settings. |
| `.codex/config.toml` | Codex project MCP connection. |
| `.agents/skills/fusion-model/` | Shared modeling skill with task-specific Fusion API, assembly, timeline, sketch, feature, and verification references. |
| `.agents/skills/fusion-print/` | Shared printing skill with references loaded by task: design rules, orientation, scan, and improvement. |
| `.agents/skills/fusion-repair/` | Shared repair skill with references loaded by failure type. |
| `.agents/.claude-plugin/plugin.json` | Lets the Claude launcher load those same skill files as a local plugin. Codex discovers them in `.agents/skills/`. |
| `Project.md` | Created on first run for this design's verified context and decisions. |

Fusion designs remain in Fusion's documents. Do not put agent credentials or generated agent runtime folders into a project copy.

## Benchmarking

Use the [benchmark prompts and results sheet](Benchmarking.md) to record time, usage, and result quality by template and agent version.
