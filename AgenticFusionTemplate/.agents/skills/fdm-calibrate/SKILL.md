---
name: fdm-calibrate
description: Plan and interpret FDM printer, nozzle, and material calibration from measurements or observed print defects. Use for flow, temperature, pressure advance, retraction, volumetric flow, first-layer, or dimensional tuning; do not treat a successful slice as a measured calibration.
---

# FDM calibration

Read `FDM-Slicing.md`, the selected `Printers.json` record, and relevant `Project.md` results. Confirm the actual printer, firmware, nozzle, material/spool condition, and baseline profiles. Unknown hardware limits stay unknown; do not invent settings from a generic printer name.

Choose a test for the observed symptom or requested target; use [calibration practice](references/practice.md). Distinguish geometry/profile errors from a physical extrusion, cooling, adhesion or motion problem. Change one variable at a time unless the test explicitly isolates several. Preserve a named baseline and define measurable acceptance before proposing new values.

Prepare local calibration files with `orca-slice` when requested. Printing, heating, motion and firmware changes need their own task authorization. An MCP tool that generates or slices a tower does not prove it was printed, measured or successful.

Record printer/nozzle/material, source profile/version, test range, actual observations, measurement method and accepted result in `Project.md` or a linked calibration note. Scope results to that combination; do not promote a PLA flow result into a universal printer limit. Store confirmed hardware changes through `printer-library` and reusable user preferences in `FDM-Slicing.md`. Retain failed trials that explain the accepted range.

Use `slice-compare` for estimated setting tradeoffs and `fusion-print` for CAD fit or printability changes.
