# Agentic Fusion: shared project rules

Read this guide each session in Claude Code or Codex. Designs live in Fusion cloud documents; this folder holds instructions, context, inputs and exports. Either launcher creates missing `Project.md`.

## Decision path for every Fusion session

Read `Project.md`'s `Current state` for intent, interfaces, parameters, decisions, document names and open items. If absent, scan headings and read relevant sections only. Load skills and references by task; read `FDM-Slicing.md` only for FDM work. Discover MCP tools by their actual schemas, since names vary by client/build.

| Condition | Action |
| --- | --- |
| Inspect | Use MCP read or read-only execution; leave geometry unchanged. Load the relevant `fusion-model` reference for scripts. |
| Model | Establish function, loads, interfaces, and intent-level parameters; use `fusion-model`, verify geometry, constraints, fit, and motion, then save. |
| Print | Use `fusion-print` and only task-relevant references. |
| Start OrcaSlicer or prepare/inspect an FDM slice | Use `orca-slice`; read `FDM-Slicing.md` and the current print state in `Project.md`. |
| Define or migrate a printer/profile | Use `printer-library`; read the relevant `Printers.json` record. |
| Calibrate a printer/nozzle/material | Use `fdm-calibrate`; distinguish measured results from slice estimates. |
| Compare slicing variants | Use `slice-compare`; preserve and verify the accepted baseline. |
| Broad DfAM assessment | Use `fusion-print` and its linked `DfAM.md` protocol for the parts in scope. |
| Observed call, save, sketch, feature, or DfAM failure | Use `fusion-repair` for the symptom; retain preventive and printing rules. |

For supervised tasks, use the runtime described in `Independent-Review.md`. It retains original user requirements and independently gates its delivery channel; the primary cannot waive required reviews or authorize exceptions. Budget exhaustion, failure and missing evidence never establish approval. This runtime requires protected controller state and a verified bounded reviewer/meter adapter; ordinary unguarded launches are not covered.

## Authority and memory

- Priority: `Project.md`'s design intent and function, then generic design rules, then DfAM preferences; ask about conflicts. Assembly symmetry outranks a printing tweak that breaks it.
- One home per fact: verified project intent, parameters, geometry, document/version names, export provenance, job/slice/calibration results, artifact paths, decisions and open items in `Project.md` or its indexed notes; printer hardware and portable native presets in `Printers.json`; slicing rules and user preferences in `FDM-Slicing.md`; shared priorities here. Task methods belong in the routed skills, broad assessment protocol in `DfAM.md`. Keep prevention in its operating guide even when a failure example lives in repair guidance.
- Record only verified behavior or user-stated rules. Preserve useful exact errors, numbers, parameter names, and reasons; merge duplicates. Keep project names, dimensions, and history out of generic files, and secrets, account IDs, and personal data out of all context files.

## Folder and launcher rules

- Copy the portable folder together, including both launchers, authored context, `.agents/` and `.codex/`. Either launcher accepts a dragged project folder and copies missing portable files, preserving existing context, skills and launchers while updating Fusion connection settings. Orca startup is opt-in through `orca-slice`; ordinary Fusion startup needs neither Python nor a slicer.
- Create `Reference CAD/` when source CAD files are supplied and `Output CAD/` for requested exports; the blank template needs neither directory. Overwrite the existing export file when asked to update it. If `personal logs/` exists in a project, leave it alone unless asked. Never read, print, or copy `.credentials.json`. Exclude `.credentials.json` and `.claude.json` from any template copy; they belong to one machine or account. Do not initialize Git here without the user's direction.
- Keep temporary build scripts in the session scratchpad and design results in Fusion. Do not archive ordinary projects.

## Context size and cleanup

- Decoded-character limits: `Project.md` ≤40,000; this guide ≤15,000; each agent or skill entry ≤4,000; `FDM-Slicing.md` and each task reference ≤20,000; combined always-read text <80,000. Flag and clean an over-limit file before adding memory; never discard unique facts to meet a limit.
- Keep `Project.md`'s `Current state` concise, with key parameter expressions and confirmed geometry alongside the session facts above. Index deeper sections for task-specific reading; never auto-import the whole file. Move only necessary older evidence to linked `Project-History/<topic>.md` when unique context exceeds the limit.
- For full cleanup, first copy files to the session scratchpad. Merge repetition and superseded facts while preserving useful exact values, parameter names, errors and reasons. Compare with the source: retain each unique fact, supersede it correctly, or obtain the user's explicit rejection. Preserve portable files, project memory, user folders and machine/account files; remove only identified obsolete runtime data.
- Re-read authored edits in the same session and check links and sizes before finishing.

## Generic design rules (any design)
The mechanisms named below are examples of checks, not assumed parts in this project. Confirm actual hardware and constraints in `Project.md` and Fusion.

- **Model only features that serve a function.** No material-saving ribs, lattices or lightening holes unless asked. Keep ventilation openings next to motors, and keep clearance cuts. To tell a clearance cut from a material saver, suppress it and re-run the joint sweeps.
- **Load paths:** carry primary loads through large bearing areas (dovetail flanks, datum faces). Latches only resist low-load directions, and screws only clamp; locating bosses in existing holes take the shear.
- **Analyze design intent on every touched part (user rule).** Trace real loads, compare strength and stiffness, and raise weak points unprompted; use the [design and assembly checks](.agents/skills/fusion-model/references/design-and-assembly.md) for calculation and shape checks.
- **Priorities (user): design intent, then real verification, then everything else; effort is always last.** Choose between layouts by comparing candidates on the requirements, never by convenience.
- **Almost everything is parametric (user rule).** Reuse a small set of meaningful user parameters and derive dependent dimensions from them. Inspect dependents before changing a shared driver; use non-parametric methods only cautiously. Follow [parameter design](.agents/skills/fusion-model/references/components.md#parameter-design) when creating or changing drivers.
- **Inspect the feature tree before every boss, join or cut extrude; prefer upstream edits (user rule).** Identify its controlling sketch, feature, parameters and downstream consumers. Edit that source when it owns the shape; add a feature only for a separate operation or when an upstream edit would break intended downstream geometry. Never append an extrude or fillet to mask an upstream mismatch. Place and group features by dependencies using the [timeline rules](.agents/skills/fusion-model/references/timeline.md), then recheck references, constraints, health, body count, volume, fit and motion. Reselect broken edges rather than silently altering the shape.
- **Avoid functionless crevices, peaks, and fragile patches (user rule).** Simplify at the controlling sketch or feature while preserving seats, clearances, and other functional geometry; use the [shape checks](.agents/skills/fusion-model/references/design-and-assembly.md) when changing a part.
- **Verify motion after changes near moving parts or added material.** Sweep affected joints and compare interference to the baseline; use the [motion checks](.agents/skills/fusion-model/references/design-and-assembly.md).
