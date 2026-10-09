# Codex + Agentic Fusion

Run `Fusion-Codex.bat` to initialize this portable project, start Fusion, wait for its local MCP server, and launch Codex here. The same project can be opened with Claude Code through `Fusion-Claude.bat`.

At the start of every session, read `Agentic-Fusion.md` in full and read `Project.md` for this design's current intent, parameters, decisions, document names, and open items. Follow the shared decision path. Use the shared `fusion-print` skill for printing tasks and `fusion-repair` for an observed failure. Each skill routes to only the references needed for the task. Preserve the preventive rules in the shared guide.

Fusion is a project-scoped HTTP MCP server named `fusion` in `.codex/config.toml`. Use its available read, execute, and update tools according to `Agentic-Fusion.md`; inspect the exposed tool schemas instead of assuming Claude Code tool identifiers are available in Codex. Keep Codex sign-in and runtime data in the normal user profile; do not move `CODEX_HOME` into this portable project. Record durable, verified design facts in `Project.md`, not in session memory.
