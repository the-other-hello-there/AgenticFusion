# Claude Code + Agentic Fusion

Run `Fusion-Claude.bat` to initialize the project, start Fusion, wait for its local MCP server, and launch Claude Code with `settings.json`. `Fusion-Codex.bat` opens the same project in Codex.

Each session, read `Agentic-Fusion.md` and follow its shared context-loading and skill decision path. Do not import it or `Project.md` through `@` directives. The launcher loads `.agents/` as the `agentic-fusion` plugin, using the same physical skill files as Codex; load relevant references on demand, not all skills or slicing context at startup.

## Claude Code tool and configuration rules

- Load the Fusion tools via ToolSearch:
  - `mcp__fusion__fusion_mcp_execute`: scripts, open/save/close documents.
  - `mcp__fusion__fusion_mcp_read`: API docs, screenshots, document and project lists, active command.
  - `mcp__fusion__fusion_mcp_update`: undo/redo.
- Keep Claude account, login, and runtime data in its normal user configuration; never set `CLAUDE_CONFIG_DIR` here. Register Fusion in project `.mcp.json`, not a path-bound local `.claude.json`; `settings.json` enables it.
- Do not use Claude auto-memory or `projects/*/memory/` for durable context. Move useful facts into the correct authored file, then remove redundant memory. `settings.json` disables auto-memory for launcher sessions.
- If a Claude session needs compaction during full cleanup, ask the user to run `/compact`; Claude cannot invoke it.
- For `application-session` usage checks, use exposed Claude Code limit warnings, `/usage`, or supported status-line `rate_limits.*.used_percentage` fields when available. Those account limits differ from `context_window.used_percentage`; `/cost` is not a universal subscription-allowance meter. Missing fields stay unknown; do not inject interactive commands into the user's UI. [Official status-line fields](https://code.claude.com/docs/en/statusline), [interactive commands](https://code.claude.com/docs/en/interactive-mode).
