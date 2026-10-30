# Claude Code + Agentic Fusion

Run `Fusion-Claude.bat` to prepare the project and launch Claude Code with `settings.json` and the shared `.agents/` plugin. `Fusion-Codex.bat` opens the same project in Codex.

Each session, read `Agentic-Fusion.md` and follow its context-reading and skill routing rules. Do not import it, `Project.md`, skills or slicing context through startup `@` directives. The `agentic-fusion` plugin uses the same physical skills as Codex.

## Claude Code tool and configuration rules

- Load the Fusion tools via ToolSearch:
  - `mcp__fusion__fusion_mcp_execute`: scripts, open/save/close documents.
  - `mcp__fusion__fusion_mcp_read`: API docs, screenshots, document and project lists, active command.
  - `mcp__fusion__fusion_mcp_update`: undo/redo.
- Keep Claude account, login, and runtime data in its normal user configuration; never set `CLAUDE_CONFIG_DIR` here. Register Fusion in project `.mcp.json`, not a path-bound local `.claude.json`; `settings.json` enables it.
- Do not use Claude auto-memory or `projects/*/memory/` for durable context. Move useful facts into the correct authored file, then remove redundant memory. `settings.json` disables auto-memory for launcher sessions.
- Claude-generated `backups/`, `cache/`, `file-history/`, `session-env/`, `sessions/`, `shell-snapshots/`, `projects/`, `history.jsonl`, `.last-cleanup`, `.last-update-result.json`, `plugins/`, and `skills/` are runtime data, not template files. From an old in-folder configuration, remove obsolete `backups/.claude.json.backup.*`, `cache/*`, past transcripts, tool results, file history, session environments, and project paths from old locations. Preserve the current session, user files, credentials, and installed plugins and skills.
- If a Claude session needs compaction during full cleanup, ask the user to run `/compact`; Claude cannot invoke it.
