# Codex + Agentic Fusion

Run `Fusion-Codex.bat`; `Fusion-Claude.bat` opens the same project in Claude Code. Both use the shared setup and Fusion startup.

Each session, read `Agentic-Fusion.md` and follow its context-reading and skill routing rules. Codex discovers the shared skills in `.agents/skills/`.

Fusion is the project-scoped HTTP MCP server `fusion` in `.codex/config.toml`. Discover its read, execute and update tools by schema; Claude tool IDs may differ. Keep Codex sign-in and runtime data in the normal user profile, never `CODEX_HOME` here. Durable context follows the shared guide, not session memory.
