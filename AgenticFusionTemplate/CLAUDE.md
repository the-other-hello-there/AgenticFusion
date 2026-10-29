# Claude Code + Agentic Fusion

Run `Fusion-Claude.bat` to initialize the project, start Fusion, wait for its local MCP server, and launch Claude Code with `settings.json`. `Fusion-Codex.bat` opens the same project in Codex.

Each session, read `Agentic-Fusion.md` and `Project.md`'s `Current state`; if absent, scan headings and read relevant sections only. Do not import either file through `@` directives.

Follow the shared decision path. The launcher loads `.agents/` as the `agentic-fusion` plugin; invoke `fusion-model`, `fusion-print`, `orca-slice`, or `fusion-repair` as needed and read only relevant references. For Orca startup/slicing read `FDM-Slicing.md` and discover the `orcaslicer` tools by their actual schemas. Do not import skills or slicing context at startup.

## Claude Code tool and configuration rules

- Load the Fusion tools via ToolSearch:
  - `mcp__fusion__fusion_mcp_execute`: scripts, open/save/close documents.
  - `mcp__fusion__fusion_mcp_read`: API docs, screenshots, document and project lists, active command.
  - `mcp__fusion__fusion_mcp_update`: undo/redo.
- Keep Claude account, login, and runtime data in its normal user configuration; never set `CLAUDE_CONFIG_DIR` here. Register Fusion in project `.mcp.json`, not a path-bound local `.claude.json`; `settings.json` enables it.
- Do not use Claude auto-memory or `projects/*/memory/` for durable context. Move useful facts into the correct authored file, then remove redundant memory. `settings.json` disables auto-memory for launcher sessions.
- Claude-generated `backups/`, `cache/`, `file-history/`, `session-env/`, `sessions/`, `shell-snapshots/`, `projects/`, `history.jsonl`, `.last-cleanup`, `.last-update-result.json`, `plugins/`, and `skills/` are runtime data, not template files. From an old in-folder configuration, remove obsolete `backups/.claude.json.backup.*`, `cache/*`, past transcripts, tool results, file history, session environments, and project paths from old locations. Preserve the current session, user files, credentials, and installed plugins and skills.
- If a Claude session needs compaction during full cleanup, ask the user to run `/compact`; Claude cannot invoke it.
