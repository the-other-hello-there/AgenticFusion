# Claude Code + Agentic Fusion

Run `Fusion-Claude.bat` to initialize this portable project, start Fusion, wait for its local MCP server, and launch Claude Code with project `settings.json`. The same project can be opened with Codex through `Fusion-Codex.bat`.

Read the shared Fusion rules and this project's design context at session start:

@Agentic-Fusion.md
@Project.md

Follow the shared decision path in `Agentic-Fusion.md`. The launcher loads the shared `agentic-fusion` plugin from `.agents/`; it contains `fusion-print` and `fusion-repair`. Invoke the relevant skill only for a printing task or an observed failure, and read only its needed references. Keep preventive rules in the shared guide. Do not import skill bodies or references at session start.

## Claude Code tool and configuration rules

- Load the Fusion tools via ToolSearch:
  - `mcp__fusion__fusion_mcp_execute`: scripts, open/save/close documents.
  - `mcp__fusion__fusion_mcp_read`: API docs, screenshots, document and project lists, active command.
  - `mcp__fusion__fusion_mcp_update`: undo/redo.
- The launcher keeps Claude account, login, and runtime data in Claude's normal user configuration. Do not set `CLAUDE_CONFIG_DIR` to this portable folder. Register Fusion in project `.mcp.json`, never a local-scope `.claude.json` tied to an absolute path. `settings.json` enables the project server.
- Do not use Claude auto-memory or `projects/*/memory/` for durable context. Move useful facts found there into the correct authored file, then remove redundant memory. `settings.json` disables auto-memory for launcher sessions.
- Claude-generated `backups/`, `cache/`, `file-history/`, `session-env/`, `sessions/`, `shell-snapshots/`, `projects/`, `history.jsonl`, `.last-cleanup`, `.last-update-result.json`, `plugins/`, and `skills/` are runtime data, not part of the template. If an old in-folder configuration left them here, remove obsolete `backups/.claude.json.backup.*` and `cache/*`, past session transcripts and tool results, their file history and session environments, and project paths from old folder locations. Never delete the current session, user files, credentials, or installed Claude plugins and skills during cleanup.
- If the Claude session needs compaction during full cleaning, ask the user to run `/compact`; Claude cannot invoke that command itself.
