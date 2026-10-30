---
name: orca-slice
description: Start OrcaSlicer with its OrcaMCP server, connect Codex and Claude Code, and prepare or inspect FDM slices. Use for slicer startup, profiles, plate settings, slicing, and slice results; use fusion-print for CAD printability changes.
---

# OrcaSlicer and FDM slicing

Read `FDM-Slicing.md`, the selected `Printers.json` record and `Project.md`'s current print state. An installed profile does not establish the user's printer or preferences.

For startup or connection problems, read [startup](references/startup.md). From the project folder run:

```powershell
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure
```

The Python 3.11+ helper starts/reuses the intended **OrcaMCP community build** and embedded server, verifies MCP initialization/tool discovery and registers `orcaslicer` for both clients. Stock/vendor Orca builds are not substitutes. Installation paths, alternate ports and recovery are in the startup reference.

After first registration, reconnect/restart client MCP and discover the actual schemas. For slicing, follow [workflow](references/workflow.md): verify the intended geometry, plate, orientation and printer/material/settings, then inspect completion, warnings, estimates and artifacts. Startup does not authorize uploads, heating, movement or printing.

Record user preferences in `FDM-Slicing.md` and verified job facts in `Project.md`. Use `printer-library` for portable definitions, `fdm-calibrate` for measured tuning, `slice-compare` for comparisons, and the Fusion skills for CAD work.
