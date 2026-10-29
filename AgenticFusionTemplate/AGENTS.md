# Codex + Agentic Fusion

Run `Fusion-Codex.bat` to initialize the project, start Fusion, wait for its local MCP server, and launch Codex. `Fusion-Claude.bat` opens the same project in Claude Code.

Each session, read `Agentic-Fusion.md` and `Project.md`'s `Current state` for intent, parameters, decisions, document names, and open items. If absent, scan headings and read relevant sections only. Follow the shared decision path: `fusion-model` for modeling, `fusion-print` for CAD printability, `orca-slice` for Orca/MCP startup and slicing, `fusion-repair` for observed Fusion failures. Read `FDM-Slicing.md` only for FDM tasks. Load only relevant references.

Fusion is the project-scoped HTTP MCP server `fusion` in `.codex/config.toml`. Use its read, execute, and update tools per `Agentic-Fusion.md`; inspect schemas because Claude tool IDs may differ. Keep Codex sign-in and runtime data in the normal user profile, never `CODEX_HOME` here. Record durable verified facts in `Project.md`, not session memory.
