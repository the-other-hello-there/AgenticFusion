# FDM slicing rules and preferences

Read for FDM tasks in either agent. Store reusable slicing rules and user-stated preferences here; printer hardware/presets in `Printers.json`; job facts and evidence in `Project.md` or its indexed notes. `Agentic-Fusion.md` owns skill routing and context placement; CAD printability methods remain in `fusion-print`.

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

Record new user-stated durable preferences or update an existing entry with its scope and exceptions. Follow the shared context-size rules; setup preserves copied projects' edits. Link detailed calibration evidence from `Project.md`.
