# Fusion failure repair

Read this file when a Fusion MCP call, save, sketch, feature, occurrence, screenshot, or DfAM fix fails or produces an unexpected result. Match the observed symptom below; do not use a repair as a substitute for the preventive rules in `CLAUDE.md` and `DfAM.md`. Test repairs in one rollback-capable script where possible, then recheck body count, volume, feature health, constraints, motion, and the saved version as applicable.

## MCP output, timeout, and crash

- **`The operation timed out.`** The script can still be running in Fusion, with later calls queued behind it. Wait, then poll with a read-only script; do not blindly rerun the build. Split future heavy builds into batches and log progress to a scratchpad file.
- **Empty MCP output mid-session:** scripts may return an empty message even while `sys.stdout` works. Write results to a scratchpad file and read it with Bash for the rest of that session.
- **Save collision or `ECONNRESET`:** a scripted `doc.save()` started in the same second as an autosave and crashed Fusion with heap corruption `0xc0000374` after `NEUTRON_BUG_ALERT` floods in `BinaryBulkSaveVisitor`. The version was not saved; its crash-recovery backup was `not a valid zip package`. Follow the autosave timing and version checks in `CLAUDE.md` before another save.
- **Startup recovery dialog after a crash:** it blocks every MCP call, including read-only calls, with `The operation timed out.` Ask the user to dismiss the dialog.
- **Export timeout during save upload:** an export can return `The operation timed out.` and still finish; check output-file timestamps before retrying.

## Unexpected document or assembly state

- **An edited cut creates a feature in another component:** reassigning profiles while rolled back can add that component's body as a participant. A hidden feature such as `Extrude20` shares the original's timeline index. List every component's features and find duplicate indices. Roll to the original with `rollTo(True)` and reset `participantBodies` to the part's body. Do not call `deleteMe()` on the stray: that also deletes the original. The stray can remain as an inert stub (0 bodies, 0 faces, health 4) on the shared index; ignore it in later duplicate-index checks.
- **A grounded layout instance will not move:** setting `transform2` on its root proxy can silently do nothing even after clearing `isGroundToParent` and adding a snapshot; `MoveFeatures.createInput2(occurrences)` raises `invalid argument inputEntities`. Record its `transform2` and `appearance`, delete and re-add it with `addExistingComponent(comp, T')`, then re-ground and restore its appearance.
- **A deleted occurrence leaves `RemoveInstance-…` history:** the name remains reserved (the replacement gets ` (1)`), and its user parameters cannot be deleted (`deleteMe()` returns False). The API cannot purge it (`InternalValidationError`); delete the original timeline item in the UI or reuse the component. A demo component created and deleted with all occurrence, joint, and feature timeline items in one unsaved session left no `RemoveInstance` item, and its parameters could be deleted.
- **A large dark body appears flat grey in a screenshot:** zoom in or move the camera eye.

## Sketches, blends, and DfAM fixes

- **Sketch warning `Edge 1 missing` / `Curve 1 missing`:** a projected curve lost its source, and reading `referencedEntity` raises. Delete lost curves only when no used profile needs them; in the same script, compare the consuming feature's health and volume and raise to roll back if either changes.
- **Whole-tool-body fillet raises `InternalValidationError : body` or `FILLET_NO_EDGE_FOUND`:** passing its creating Feature objects caused the former for a loft-plus-cut tool; passing BRepFaces caused the latter. Pass `body.edges` after excluding unwanted edges. To edit later, roll to the fillet and set `edgeSets.item(0).edges`.
- **A groove or cut round fails:** fillet its edges one at a time in a script that raises at the end, so the probes roll back. Check what the failing rim meets, such as a neighbouring fillet or a hole 0.1–0.3 mm away.
- **`ASM_BL_UNFIN_SHEET` / `BLEND_TOO_BIG`:** the radius usually exceeds local material. Probe the limit and tell the user rather than silently changing the design. An equal-distance chamfer in place of a large fillet can fail the same way.
- **Cable-channel mouth chamfer gives `ASM_BL_CAP_COMPLEX`:** a separate chamfer on the sweep's mouth edges failed at the ends. Build the rounded inlet into the keyhole profile as specified in `DfAM.md`.
- **Sacrificial bridge steps lose constraints:** a later change can split the counterbore floor face. Delete the steps and rebuild them on the new floor.
- **Bed-edge chamfer fails or loses an edge:** bisect its edge list to exclude edges it cannot take. A short edge consumed by an inserted bed feature appears as `Edge N missing`; follow the timeline placement and edge-reselection procedure in `DfAM.md`.
