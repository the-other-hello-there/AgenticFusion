---
name: printer-library
description: Define, inspect, update, export, or migrate FDM printer definitions and Orca presets in the portable Printers.json library. Use for known printer hardware and copyable profile records; use orca-slice for application startup and print jobs.
---

# Portable printer definitions

Read the requested records in `Printers.json`, shared by both agents and initially empty. Never infer ownership or hardware from an installed slicer or similarly named preset.

Read [format and migration](references/format.md) for fields and transfer commands. Distinguish user statements, documented specifications and read-only MCP observations from measurements; preserve unknowns as `null` or empty lists. Prepare a record from the [template](assets/printer.example.json), then validate/add it:

```powershell
py -3 .agents/skills/printer-library/scripts/printer_library.py validate
py -3 .agents/skills/printer-library/scripts/printer_library.py add --record printer.json
```

Preserve native Orca preset names, types, value types, custom G-code, and inheritance. Include custom parents or declare required system presets and the source slicer version. Copying a printer record migrates its definition and embedded presets; applying it to a live slicer is a separate step. Review firmware, bed origin/shape, nozzles, limits, and dependencies at the destination before using it.

Keep connection credentials and device identifiers out of portable records. The helper rejects common credential/connection fields; inspect free-text/G-code before sharing. It never installs presets, contacts a printer, or executes stored G-code. Existing record conflicts require deliberate replacement; preserve the prior record through Git or an export when updating verified hardware.

Keep job/calibration results in `Project.md` and indexed notes, and preferences in `FDM-Slicing.md`. Use `fdm-calibrate` for calibration and `orca-slice` to verify the live printer/profile.
