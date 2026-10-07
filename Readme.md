# Fusion + Claude Code template

This repository contains a Windows template for using **Claude Code** with the **local Autodesk Fusion MCP Server**. The reusable project folder is [`FusionClaudeCodeTemplate/`](FusionClaudeCodeTemplate/); its `Fusion-Claude.bat` file is the entry point. The repository root is only for storing the template and this guide.

## 1. Install the applications

1. Install the **Fusion desktop application** and sign in. Autodesk provides the installer through your [Autodesk Account's Products and Services page](https://help.autodesk.com/view/fusion360/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FHow-to-download-Fusion-360.html). The web client cannot host the local MCP server.
2. Install **Claude Code** on Windows. In PowerShell, run Anthropic's [native installer](https://code.claude.com/docs/en/setup):

   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```

3. Open a new PowerShell window and run `claude --version` to confirm the CLI is on your PATH. Claude Code requires a Pro, Max, Team, Enterprise, or Console account; on first launch, follow its browser sign-in prompts. The batch file does not install Claude Code or store your account credentials in the project folder.

## 2. Enable Fusion's local MCP server

In Fusion, open **Preferences > General > API** and check **Fusion MCP Server (runs locally on this device)**. Note the port shown there; the default is **27182**. Keep Fusion running and open the design you want Claude to inspect or edit. [Autodesk's connection instructions](https://help.autodesk.com/view/fusion360/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html) describe the local endpoint.

The template already configures Claude Code to use `http://127.0.0.1:27182/mcp` through `.mcp.json`; no separate Claude Desktop connector or Fusion add-in is needed for this setup. This is Fusion's **local desktop MCP server**, not the separate cloud-hosted Fusion Data MCP server.

If Fusion shows a different port, edit `$McpPort` near the top of your copied `Fusion-Claude.bat` before running it. The launcher then updates that project's `.mcp.json` to the matching URL. Changing `.mcp.json` alone is insufficient because the launcher checks and rewrites its Fusion entry.

## 3. Create and open a project

1. Copy the **inner** [`FusionClaudeCodeTemplate/`](FusionClaudeCodeTemplate/) folder to any location and rename the copy for your project. Keep its six supplied files together; do not copy the repository's `.git` folder. Run the batch file from the **copy** so first-run files are created in your project rather than in the clean template.
2. Double-click **`Fusion-Claude.bat`** in the copied folder. It creates `Project.md` if absent, confirms the project MCP/settings files, starts Fusion if needed, waits up to 120 seconds for its MCP port, then starts `claude --settings settings.json` in that project folder. It does not overwrite an existing `Project.md`.
3. Complete Claude Code sign-in or workspace trust prompts if shown. In `Project.md`, record this design's intent, interfaces, important parameters, decisions, and Fusion document names. The supplied `CLAUDE.md` loads that file at session start.

You can instead **drag an existing project folder onto the template's `Fusion-Claude.bat`**. The launcher copies missing template files into that folder without replacing existing project context, then opens it. To initialize a copied project without opening Fusion or Claude, run `.\Fusion-Claude.bat --setup-only` in PowerShell from that project's folder.

## Check the connection

Inside Claude Code, run `/mcp` and check that `fusion` is connected. A safe first request is: "List the active Fusion document and its components without changing the design." Claude Code's [MCP guide](https://code.claude.com/docs/en/mcp) also documents `claude mcp list` from a terminal in the project folder.

If `fusion` is disconnected, confirm that Fusion is open, its MCP checkbox is enabled, a design is open, and the Fusion port matches `$McpPort`. If the launcher cannot find Fusion, start Fusion yourself before the batch file or set `$FusionPath` near the top of the batch file to its launcher path. If `claude` is not found, reopen PowerShell and run `claude --version`; Anthropic's [setup guide](https://code.claude.com/docs/en/setup) includes PATH troubleshooting and `claude doctor`.

## What the project folder contains

| File | Purpose |
| --- | --- |
| `Fusion-Claude.bat` | Initializes the project and launches Fusion and Claude Code. |
| `.mcp.json` | Project-scoped connection to Fusion's local MCP endpoint. |
| `settings.json` | Claude Code model and project MCP settings. |
| `CLAUDE.md` | Always-loaded Fusion design, modeling, and MCP guidance. |
| `DfAM.md` | Printing guidance read when a task concerns fabrication. |
| `Fusion-Failure-Repair.md` | Troubleshooting guidance read when a failure occurs. |
| `Project.md` | Created on first run for this project's own context and decisions. |

Fusion designs remain in Fusion's documents. Claude Code login and runtime data remain in its normal user configuration, outside the portable project folder.

## Benchmarking

See the [benchmark prompts and results sheet](Benchmarking/Readme.md) for repeatable tests and fields to record time, credit usage, and result quality by version.
