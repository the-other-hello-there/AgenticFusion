# Shared workflow integration

The incoming review bundle supplied 44 project source files in 24 candidate groups. Its source manifest hashes were verified, and all 44 originals still existed unchanged in the originating project before the incoming copy was removed. Project geometry, task IDs, absolute paths, calibrated values and historical acceptance exceptions remain project material. No supplied builder, hook or CAD script was executed during extraction.

This map records the reusable topic's canonical home. Paths below are relative to `AgenticFusionTemplate/.agents/skills/` unless identified otherwise. Existing procedures were extended rather than adding parallel project-lesson skills.

| Group | Integrated procedure or helper |
| --- | --- |
| R01 | `fusion-model/references/components.md`, `fillets.md`, `helpers.md`, `mcp.md`; print orientation and repair recovery guidance: placement, context, bounded cleanup, result inspection and uncertain rollback. |
| R02 | Components, sketches/features, design/assembly, reference comparison: surface/thicken results, dimensions, joint limits, poses, units and floor-ray checks. Appearance null/exception behavior is qualified against the API contract. |
| R03 | Timeline, MCP and component procedures: real parametric trials, dependency-aware edits, explicit loft participants and result identity. Project-only construction prohibitions were not globalized. |
| R04 | Sketches/features, helpers, fillets and reference comparison: unstable primitives/lofts, immutable master tools, exact sections and insertion-first geometry. Unconditional rollback and unit guessing were rejected. |
| R05 | Shared `Agentic-Fusion.md` routing/authority, verification and lifecycle: cause-based edits, criterion rejection, evidence stages, prior decisions and cold-start reproduction. Fixed alternative/retry counts remain project policy. |
| R06 | Shared `.agents/scripts/watch_fusion.py`: unique-run incremental logs, monotonic deadlines, rotation/truncation, bounded buffers and explicit outcomes. Completion markers never establish design acceptance. |
| R07 | Shared `.agents/scripts/evidence_gate.py` and verification reference: project-configured criterion registry, saved revision, finite bounds, receipts, distinct artifacts and external obligations. No default gate or claims of independently true evidence. |
| R08 | Verification/reference-comparison procedures: opt-in project policies, paired original/comparison evidence, incomplete/unknown reporting. Project regex hooks and unverified Codex approval settings were not installed. |
| R09 | One `fusion-model/scripts/fusion_helpers.py` plus existing wrapper recipes: explicit inputs/units, checked batches, bounded deletion, participant selection and reporting. No duplicate f5/v2 library, implicit active app or project logging. |
| R10 | Design/assembly and components: snapshot/restore limits and poses, independent axis checks, downstream/combined sweeps and checked temporary intersections. Samples do not prove continuous clearance. |
| R11 | Reference comparison: host/insert and insert/insert checks, rigid screw paths, installed-piece order and ordered pocket-floor rays. Sample resolution and unknowns remain explicit. |
| R12 | Helpers and `section_bounds_mm`: exact BRep sections, configurable quality diagnostics, empty/error stations and evaluator failures. Small faces are diagnostic candidates. |
| R13 | Sketches/features and components: surface-following inserts from an intact master, explicit new-solid identity, host integrity and validated master-linked seeds. Project-specific part builders remain excluded. |
| R14 | Print orientation and components: explicit full transforms, transformed bounds, parent/child grounding and replay/reopen verification. Support scores remain proxies. |
| R15 | Print scan: printer-neutral capability envelope, downward-area/local-minimum diagnostics, material-height bands and conditional machine-specific slicing. |
| R16 | Print scan: node crossing sections, per-solid hole parity, occupancy union, empty layers and unsupported extensions. The optional third-party analysis recipe is loaded only for layer diagnostics, without installing new startup dependencies. |
| R17 | Reference comparison: camera calibration, silhouettes, local contrast, visibility, mask/boundary metrics and paired overlays. Camera error and painter-depth limitations remain explicit. |
| R18 | Reference comparison and `sampled_surface_distances`: bidirectional, unit-explicit sampled surface measurements with an all-triangle budget, avoiding an unbounded/incorrect centroid shortlist. |
| R19 | Reference comparison: independent-reference skin rays, first-hit identity/depth, intentional seams, gap clustering, coverage and occlusion limits. |
| R20 | Reference comparison and print orientation: reproducible appearance before pose, effective properties/overrides and ancestor visibility. No toy palettes or visible-body-count criteria. |
| R21 | Verification and run monitor: evaluated pass/fail/unknown, provenance, explicit failed reads and no DONE-on-unhealthy-build assurance. |
| R22 | Design/assembly: opt-in moving-chain mass/inertia and stop-impact studies, explicit assumptions and separate physical validation. No imported material/fatigue thresholds. |
| R23 | Reference comparison: temporary graphics for display, with camera/visibility/opacity and graphics cleanup in `finally`. |
| R24 | MCP/export workflow: selected body export, tessellation, units/provenance, actual file checks and owned-reference/prior-document restoration. |

The separate seven-reference bundle was merged into the same canonical model/print/repair/slicer references. Alternate extra walls retain minimum shell coverage while using the user's reduced vertical-shell preference; enums are verified against the selected build. Slicer startup uses one background dialog helper shared by desktop/Store opening and optional MCP boot. Required or unsupported dialogs are reported without accepting defaults or discarding user work.

`Test-FusionWorkflow.py` verifies the portable monitor, evidence validator and helper contracts using isolated fixtures; `Test-SlicerDialogs.py` covers scoped/chained dialog decisions and actual message delivery to an offscreen, non-activating test-owned window. Existing updater/package and fresh two-agent launcher checks cover distribution and wiring. These checks do not establish live CAD kernel behavior, cloud recovery, real slicer import/preview or physical performance.
