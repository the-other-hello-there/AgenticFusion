---
name: slice-compare
description: Compare FDM slicing variants for time, material, supports, quality constraints, or strength requirements while preserving the accepted baseline. Use for controlled slicing experiments and recommendation tables; use fdm-calibrate for physical measurements.
---

# Compare slice variants

Read `FDM-Slicing.md`, the selected printer definition and current `Project.md` print state. Use `orca-slice` for connection, import and ordinary slicing. Confirm the objective, fixed requirements, source export/hash, printer/nozzle/material, plate, orientation and resolved baseline settings.

Define a small named variant set for the user's question. Change one variable at a time, or state exactly what a coupled variant changes. Do not alter CAD geometry or an accepted orientation unless requested. Preserve unsaved overrides and the original scene/profile selection before trying variants; use independent local project copies when reliable restoration is unavailable.

For each variant, wait for completion and read actual warnings, time and filament estimates with units. Verify that those estimates belong to that variant's current geometry/settings. Save comparison artifacts only within the requested scope. Mark failed or unavailable results explicitly; never rank a stale/failed slice as a valid candidate.

Report a table with the baseline, changed settings, estimated time, filament mass/length, supports, warnings and relevant requirement checks. State percentage deltas only for compatible nonzero baselines. Do not equate more infill with a quantified strength improvement or infer mechanical performance from slice estimates alone. Explain tradeoffs when no variant dominates.

Restore the accepted baseline, including the intended selection and overrides, unless the user requested adopting a variant. Verify restoration; if a call fails, retain the last verified state and report the unresolved difference. Record the experiment and any accepted decision in `Project.md`; update `FDM-Slicing.md` only for a new user-stated reusable preference. Physical performance needs `fdm-calibrate` or a measured part test.
