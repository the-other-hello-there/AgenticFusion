# FDM slicing rules and preferences

Read for slicer tasks in either agent. This file holds reusable slicing rules and user-stated preferences for this project copy. Keep printer hardware and portable presets in `Printers.json`; verified part geometry, selected job profiles, export provenance, slice/calibration results, artifact paths, and open job items in `Project.md` or its indexed notes. Use `printer-library` to define/migrate machines, `orca-slice` for startup and ordinary slicing, `fdm-calibrate` for measured tuning, and `slice-compare` for estimated tradeoffs. CAD printability methods remain in `fusion-print`.

## Current preferences

- **Slicer/backend:** OrcaMCP community build with its embedded OrcaSlicer MCP server. No Snapmaker dependency is required for this template experiment.
- **Printer, nozzle and filament:** Not specified. Confirm them before selecting profiles or slicing.
  Look up a supplied printer ID in `Printers.json`; an entry's evidence and source scope determine what is known. The blank library establishes no hardware facts.
- **Quality/strength/time priorities:** Preserve the design's function and verified requirements; no numeric slicing defaults have been supplied.
- **Layer height, line widths, walls and infill:** Not specified. Do not mistake the CAD skill's analysis assumptions for validated slicing settings.
- **Supports and bed adhesion:** Not specified. Use the accepted orientation and functional-surface constraints; explain tradeoffs before changing them.
- **Output:** Save requested local artifacts and report warnings and estimates. Printer upload/start is a separate operation.

## Operating rules

- Preserve existing CAD design intent and parametric control. Re-export and invalidate old slices after a source change.
- Verify millimeter dimensions, selected plate/window, printer/nozzle, filament and resolved process settings. An active preset does not prove compatibility or approval.
- Keep an accepted orientation unless the task calls for changing it. Protect mating, bearing and cosmetic surfaces identified in `Project.md` when placing supports or seams.
- Prefer job-local overrides. Preserve user presets and unsaved changes when switching profiles; do not silently replace a global profile.
- Compare settings against the same source geometry and printer/material setup. Identify the changed variables and any restoration to the baseline.
- Report actual completion and warnings before claiming a successful slice. Time and filament values are estimates until measured from a real print.
- Record only verified facts or user-stated preferences. Keep credentials and machine-specific installation paths out of authored context.

## Preference updates

When the user gives a durable preference, update its existing entry with scope and exceptions. Keep this file concise (target at most 20,000 decoded characters), read only for FDM work, and preserve a copied project's edits during template setup. Link detailed calibration evidence from `Project.md` when needed.
