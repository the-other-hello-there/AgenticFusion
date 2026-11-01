---
name: printer-library
description: Define, inspect, update, export, or migrate FDM printer definitions and Orca presets in the portable Printers.json library. Use for known printer hardware and copyable profile records; use orca-slice for application startup and print jobs.
---

# Portable printer definitions

Use the project's `Printers.json` as the shared machine library for both agents. Read only the requested printer records; it starts empty. Never infer ownership, bed size, nozzle, firmware, or limits from an installed slicer or a similarly named preset.

For field definitions and migration commands, read [format and migration](references/format.md). Capture user-stated hardware, a selected printer's documented specifications, or the relevant read-only MCP fields; distinguish those sources from measurements. Preserve unknowns as `null` or empty lists. Use the [record template](assets/printer.example.json) to prepare a record, then validate/add it with the standard-library helper:

```powershell
py -3 .agents/skills/printer-library/scripts/printer_library.py validate
py -3 .agents/skills/printer-library/scripts/printer_library.py add --record printer.json
```

Preserve native Orca preset names, types, value types, custom G-code, and inheritance. Include custom parents or declare required system presets and the source slicer version. Copying a printer record migrates its definition and embedded presets; applying it to a live slicer is a separate step. Review firmware, bed origin/shape, nozzles, limits, and dependencies at the destination before using it.

Keep connection credentials and device identifiers out of portable records. The helper rejects common credential/connection fields; inspect free-text/G-code before sharing. It never installs presets, contacts a printer, or executes stored G-code. Existing record conflicts require deliberate replacement; preserve the prior record through Git or an export when updating verified hardware.

Keep job selection and slice results in `Project.md`, user preferences in `FDM-Slicing.md`, and calibration evidence in the project's indexed results. Use `fdm-calibrate` for calibration and `orca-slice` to verify the actual active printer/profile.
