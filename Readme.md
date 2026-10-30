# Agentic Fusion

A portable Windows folder for Autodesk Fusion's local MCP server with **Claude Code or Codex**. Copy [`AgenticFusionTemplate/`](AgenticFusionTemplate/) for each project; either launcher prepares shared files and starts Fusion and the chosen agent.

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
2. Run `Fusion-Claude.bat` or `Fusion-Codex.bat`. Either launcher creates missing `Project.md`, prepares both agents' MCP configurations, starts Fusion if needed, waits up to 120 seconds for its server, and opens the selected agent. Codex may ask you to trust the project before loading its MCP configuration.
3. In `Project.md`, keep the `Current state` section concise and record verified design intent, interfaces, parameters, document names, decisions, and open items. The two agent entry files direct their agents to read that section and the short shared Fusion guide.

Claude loads `.agents/` through `--plugin-dir`; Codex discovers the same physical skill files in `.agents/skills/`. Use the Claude launcher to load its plugin. Both agents load detailed references only when needed; `CLAUDE.md` does not auto-import all of `Project.md`.

Both agents play a short Windows tone when their main agent finishes a response. Claude's plugin and Codex's project hook call the same `.agents/scripts/task-complete.ps1`; no instruction text or model call is involved. Codex requires project trust and a one-time review of the hook through `/hooks` before it runs. Start either agent through its launcher from the project folder.

Drag an existing project folder onto either template launcher to copy missing files, including both launchers, without replacing context. In a copied folder, run `./Fusion-Claude.bat --setup-only` or `./Fusion-Codex.bat --setup-only` to prepare files without opening Fusion or an agent; both use the same setup routine.

Setup preserves an older copy's launcher and instruction files. To fix Claude's instruction-size overflow, remove `@Project.md` and `@Agentic-Fusion.md` from its `CLAUDE.md`, then bring over current guide and skill routing while preserving project-specific edits. Setup copies missing skills only. If `Project.md` is large, keep current facts there and index needed history in `Project-History/` per the shared cleanup rule.

The launcher warns above the 40,000-character `Project.md` target. For Claude, it detects legacy full-file imports and stops before their combined text exceeds the observed 150,000-character instruction limit. It never rewrites existing context.

### Optional OrcaSlicer startup

The shared `orca-slice` skill starts an installed [OrcaMCP community build](https://github.com/okets/OrcaMCP/tree/mcp) and its embedded MCP server. Install that build outside your project and use Python 3.11+ for the helper. No Snapmaker dependency is required. Ordinary Fusion startup remains independent of Python and Orca.

From a project copy, ask either agent to use `orca-slice`, or run:

```powershell
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure
```

For a nonstandard installation add `--executable 'C:\Tools\OrcaMCP\orca-slicer.exe'`, or set `ORCAMCP_APP_PATH` on this machine. The helper starts/reuses the intended endpoint, verifies MCP initialization and tool discovery, and merges its `orcaslicer` entry into both clients' project settings. Reconnect/restart client MCP after the first registration. It does not install software or call slicing/printer tools. See the [startup reference](AgenticFusionTemplate/.agents/skills/orca-slice/references/startup.md) for setup-only mode, alternate ports, and recovery.

Keep slicing rules and preferences in [`FDM-Slicing.md`](AgenticFusionTemplate/FDM-Slicing.md), read only for FDM work. Keep verified geometry, selected job profiles, export provenance, and slice results in `Project.md`. Setup copies missing files and preserves a project's existing slicing preferences.

### Portable printers and slicing skills

The shared `printer-library` skill maintains [`Printers.json`](AgenticFusionTemplate/Printers.json): printer identity, known hardware limits, evidence, and optional embedded Orca machine/filament/process presets. JSON keeps these definitions easy to copy and paste while preserving native profile types and inheritance. The template starts with an empty library; use the skill to record actual printers from user-stated or verified information.

Copy the whole catalog to a new project, paste selected records into its `printers` array, or use the helper to merge them without silently replacing existing definitions:

```powershell
py -3 .agents/skills/printer-library/scripts/printer_library.py validate
py -3 .agents/skills/printer-library/scripts/printer_library.py export --id my-printer --output shared-printers.json
py -3 .agents/skills/printer-library/scripts/printer_library.py import --source shared-printers.json
```

`export-presets` also writes embedded presets as individual native JSON files. This catalog is agent context, not a slicer-native installer; review/import native presets through the slicer and verify declared system parents, firmware, nozzle and bed geometry. See the [format and migration reference](AgenticFusionTemplate/.agents/skills/printer-library/references/format.md) for the record template and full commands.

Use `fdm-calibrate` to plan and interpret measured printer/material calibration, and `slice-compare` to compare estimated time/material/quality tradeoffs while restoring the accepted baseline. Calibration evidence and job outcomes stay in `Project.md` or its indexed notes; reusable user preferences stay in `FDM-Slicing.md`. Both agents discover the same physical skill files.

### Optional independent requirement review

The experimental [independent-review runtime](AgenticFusionTemplate/Independent-Review.md) runs a second reviewer outside the primary process, captures original user requirements and actual changes, schedules implementation/delivery reviews, and automatically requests revisions. Its ledger reserves all review attempts against a default **12.4%** ratio. Missing budget, unknown usage, failure and inconclusive review hold delivery.

Set `AGENTIC_REVIEW_TASK` to an operator-authored task file and `AGENTIC_REVIEW_POLICY` to a protected policy before running either Fusion launcher, or run the documented supervisor command directly. Normal sessions remain unguarded. The supplied policy fails closed before starting a model until a trusted bounded reviewer is configured. Claude's reported USD can be used; guarded Codex requires an external comparable meter. Neither native CLI's strict reviewer spend ceiling was established, so out-of-box paid review is **not ready**. The [assessment](Benchmarking/ReviewGuard/Assessment.md) distinguishes tested control behavior, simulated costs, live-model gaps and enforcement limits.

### Check the connection

Inside the chosen agent, check `/mcp` for the `fusion` server. From a terminal in the project folder, `claude mcp list` or `codex mcp list` can also inspect configured servers. A safe first prompt is: “List the active Fusion document and its components without changing the design.” See the [Claude MCP guide](https://code.claude.com/docs/en/mcp) and [Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

If the server is disconnected, check that Fusion is running, its MCP option is enabled, a design is open, and the Fusion port matches `$McpPort`. If Fusion cannot be found automatically, start it yourself or set `$FusionPath` in `Fusion-Claude.bat` to its launcher path. If an agent executable is missing, reopen the terminal and check its version command. Codex project MCP settings load only after the project is trusted; if the server is absent from `codex mcp list`, check trust and restart Codex from the project folder.

## Project files

| File | Role |
| --- | --- |
| `Fusion-Claude.bat`, `Fusion-Codex.bat` | Shared first-run setup and Fusion startup; launch the chosen agent. |
| `Agentic-Fusion.md` | Short, always-read shared design priorities, routing, memory placement, and size rules. |
| `DfAM.md` | Optional protocol for a requested broad DfAM assessment; technical methods stay in the shared printing skill. |
| `FDM-Slicing.md` | Shared FDM slicing rules and user-stated preferences, loaded on demand. |
| `Printers.json` | Copyable printer definitions, evidence, and embedded native presets; initially empty. |
| `CLAUDE.md`, `AGENTS.md` | Small agent-specific startup and tool instructions. |
| `.mcp.json`, `settings.json` | Claude Code project MCP and agent settings. |
| `.codex/config.toml` | Codex project MCP connection. |
| `.agents/skills/fusion-model/` | Shared modeling skill with task-specific Fusion API, assembly, timeline, sketch, feature, and verification references. |
| `.agents/skills/fusion-print/` | Shared printing skill with references loaded by task: design rules, orientation, scan, and improvement. |
| `.agents/skills/fusion-repair/` | Shared repair skill with references loaded by failure type. |
| `.agents/skills/orca-slice/` | Shared Orca/MCP startup helper and slicing workflow; uses an installed OrcaMCP build. |
| `.agents/skills/printer-library/` | Printer definition, validation, selective export/import, and native preset export. |
| `.agents/skills/fdm-calibrate/`, `.agents/skills/slice-compare/` | Measured calibration and controlled slicing comparison guidance. |
| `.agents/.claude-plugin/plugin.json` | Lets the Claude launcher load those same skill files as a local plugin. Codex discovers them in `.agents/skills/`. |
| `.agents/scripts/task-complete.ps1`, `.agents/hooks/hooks.json`, `.codex/hooks.json` | One completion tone with agent-specific Stop hook declarations. |
| `Project.md` | Created on first run for this design's verified context and decisions. |

Fusion designs remain in Fusion's documents. Do not put agent credentials or generated agent runtime folders into a project copy.

## Benchmarking

Run [Run-Benchmark.bat](Benchmarking/Run-Benchmark.bat) to benchmark a fresh, disposable copy of the inner template. The guide opens the chosen agent, walks through B1–B7, times each prompt, and asks before adding results to [Benchmarking.md](Benchmarking/Benchmarking.md). Close the agent window before finishing so the temporary local copy can be deleted. Use a disposable Fusion project too; deleting the local copy does not remove Fusion cloud documents.

## Maintenance and OrcaSlicer evidence

The [OrcaSlicer feasibility study](Explorations/OrcaSlicer/README.md) retains backend comparisons, a local inventory probe, and the live slicing decision gates. Its setup check now exercises the shipped helper; superseded static configuration examples were removed. `Benchmarking/Test-OrcaSlicer.py` checks protocol handling, application launch behavior with a simulated process, configuration preservation, and rollback with a local mock server. Live slicing remains unverified.

`py -3 Benchmarking/Test-PrinterLibrary.py` checks catalog transfer, native preset preservation, inheritance, conflicts and failed writes without an installed slicer. It does not verify a real printer or GUI preset import.

Only the inner template is distributed. Benchmark sandboxes, exploration scratch files, and Python caches are ignored; keep application installs and agent runtime data outside that folder. Repository Git history is small and retained for recovery; cleanup does not require deleting or rewriting it.
