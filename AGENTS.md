# Repository context

This repository maintains the portable Windows folder in `AgenticFusionTemplate/` for working with Autodesk Fusion's local MCP server. A user copies that inner folder for a design and can use `Fusion-Codex.bat` and `Fusion-Claude.bat` interchangeably. Both agents must preserve the same verified design context and each other's compatibility.

The repository root is for template maintenance; only the inner folder is distributed. Keep shared, reusable instructions in the inner `Agentic-Fusion.md` and `.agents/skills/` tree, slicing rules/preferences in `FDM-Slicing.md`, and portable printer hardware/presets in `Printers.json`. Keep agent-specific startup and configuration in the corresponding agent files. In a copied project, `Project.md` holds verified design intent, parameters, document names, job/slice/calibration results, decisions, and open items.

Keep skill entrypoints short and load detailed references when their procedures are needed. Maintain one physical set of skill files that both Codex and Claude Code can use. Favor sound parametric design: edit controlling sketches or features when appropriate, place new features at their logical timeline position, derive dimensions from a small set of meaningful parameters, and verify downstream features.

When changing the template, check both launchers' setup-only behavior in a fresh copy. `Benchmarking/Benchmarking.md` describes behavioral checks. Keep assessment notes and generated agent runtime data out of the distributable folder.
