# Slicing and context handoff

Read `FDM-Slicing.md` and only the relevant print state in `Project.md`. Resolve the target printer/nozzle/material when unknown; installation or a selected preset alone does not establish intent.

1. Inspect the live Orca project, window/port, plate, objects, units/dimensions, printer/nozzle, filament slots, and resolved process settings. Discover the available read tools from their schemas. Identify inherited settings and unsaved overrides that a profile switch could discard.
2. For Fusion exports, record the saved document/version, body/component selection, export path/hash, units and bounding dimensions. Recheck imported dimensions, object count, and the accepted orientation. Keep CAD changes in the parametric source. Invalidate prior slices when that source changes.
3. Apply only requested settings/orientation changes, preferably in the job rather than by overwriting global presets. Preserve functional interfaces and approved CAD orientation; explain a conflicting slicing request before changing it. Name assumptions and proposed tradeoffs when comparing quality, strength, time, supports, and material.
4. Slice the intended plate, wait for explicit completion, and inspect warnings, bed fit, unsupported regions, estimated time/filament and their units. A successful call or an output file alone is insufficient. If a check cannot be read, report that limit rather than infer success.
5. Save requested 3MF/G-code locally. Record source provenance, application/server versions, printer/nozzle/material, profile identifiers and overrides, transforms, warnings, estimates, and output paths/hashes in `Project.md`. Treat estimates as estimates. Store reusable user preferences in `FDM-Slicing.md`, without duplicating job history there.

Use `slice-compare` for a controlled comparison and restoration, `fdm-calibrate` for measured tuning, and `printer-library` for portable machine/preset records. Never report a stale slice as the result of the current geometry or settings. Printer uploads and physical operations require their own task authorization.
