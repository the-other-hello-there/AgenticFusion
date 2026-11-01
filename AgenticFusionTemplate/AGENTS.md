# Codex + Agentic Fusion

Run `Fusion-Codex.bat`; `Fusion-Claude.bat` opens the same project in Claude Code. Both use the shared setup and Fusion startup.

Each session, read `Agentic-Fusion.md` and follow its shared context-loading and skill decision path. Codex discovers the same physical `.agents/skills/` files that Claude loads as a plugin; load detailed references only for the current task.

Use root `Project.md` to discover project-specific resources. Create extra context and canonical skills under `Project/` through `project-resources`; the launcher syncs their native discovery entries. Read the canonical procedure before acting, with relative resources based on its `Project/skills/` folder.

Fusion is the project-scoped HTTP MCP server `fusion` in `.codex/config.toml`. Use its read, execute, and update tools per `Agentic-Fusion.md`; inspect schemas because Claude tool IDs may differ. Keep Codex sign-in and runtime data in the normal user profile, never `CODEX_HOME` here. Record durable verified facts in `Project.md`, not session memory.

For `application-session` usage checks, use exposed Codex account-limit warnings/status when available. `/status` is an interactive client command, not a shell command or guaranteed programmatic meter; `codex login status` reports authentication rather than remaining allowance. Never inject commands into the user's UI. If usage telemetry is unavailable, mark it unknown and rely on milestone checkpoints. [Official status command](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
