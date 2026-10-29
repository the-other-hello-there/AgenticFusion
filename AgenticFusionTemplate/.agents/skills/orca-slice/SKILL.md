---
name: orca-slice
description: Start OrcaSlicer with its OrcaMCP server, connect Codex and Claude Code, and prepare or inspect FDM slices. Use for slicer startup, profiles, plate settings, slicing, and slice results; use fusion-print for CAD printability changes.
---

# OrcaSlicer and FDM slicing

Read `FDM-Slicing.md` for slicing rules/preferences, the selected `Printers.json` record, and `Project.md`'s current part and print state. Keep CAD intent and verified export/slice results in `Project.md`; do not turn an installed printer profile into an assumed user preference.

For startup or connection problems, read [startup](references/startup.md). From the project folder run:

```powershell
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure
```

The helper starts an installed **OrcaMCP community build**, whose embedded server starts with the app, verifies MCP initialization and tool discovery, and registers `orcaslicer` for both agents. It reuses the configured endpoint when already available. It needs Python 3.11+ and accepts `--executable` or `ORCAMCP_APP_PATH`. Stock OrcaSlicer and Snapmaker Orca do not become MCP-capable merely by launching them. Do not silently substitute a different application or instance.

After first registration, reconnect/restart the client's MCP session as needed and discover the actual tool schemas; names may differ between clients and builds. For slicing, read [workflow](references/workflow.md). Verify printer, nozzle, material, profiles, source dimensions, plate, and orientation before slicing. Report actual completion, warnings, units, estimates, and saved artifacts. Starting the slicer does not authorize uploads, heating, printer movement, or a print job.

Record new user-stated preferences in `FDM-Slicing.md` and confirmed job facts in `Project.md`. Re-read changed context. Use `fusion-print` for a CAD printability review and `fusion-model` for a requested parametric geometry edit.

Use `printer-library` to define/migrate machines and presets, `fdm-calibrate` for measured printer/material tuning, and `slice-compare` for controlled slicing comparisons.
