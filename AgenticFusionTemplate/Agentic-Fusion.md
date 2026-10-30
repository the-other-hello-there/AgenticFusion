# Agentic Fusion: shared project rules

Read this guide for every Fusion task in Claude Code or Codex. The launcher creates `Project.md` if missing. Designs live in Fusion cloud documents; this folder holds instructions, context, inputs, and exports.

## Decision path for every Fusion session

At session start, read `Project.md`'s `Current state` for intent, interfaces, parameters, decisions, document names, and open items. If absent, scan headings and read only relevant sections. Then route the request:

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

Re-read an authored file after editing it in the same session.

For supervised tasks, use the runtime described in `Independent-Review.md`. It retains original user requirements and independently gates its delivery channel; the primary cannot waive required reviews or authorize exceptions. Budget exhaustion, failure and missing evidence never establish approval. This runtime requires protected controller state and a verified bounded reviewer/meter adapter; ordinary unguarded launches are not covered.

## Authority and memory

- Priority: `Project.md`'s design intent and function, then generic design rules, then DfAM preferences; ask about conflicts. Assembly symmetry outranks a printing tweak that breaks it.
- One home per fact: verified project intent, parameters, and job/slice/calibration results in `Project.md` or its indexed notes; printer hardware and portable native presets in `Printers.json`; slicing rules and user preferences in `FDM-Slicing.md`; shared priorities here; preventive modeling and MCP methods in `fusion-model`; CAD printing methods in `fusion-print`; slicing methods in the relevant shared skill; broad assessment protocol in `DfAM.md`; observed Fusion failures and recovery in `fusion-repair`. Keep prevention in its operating guide even when a failure example lives in repair guidance.
- Record only verified behavior or user-stated rules. Preserve useful exact errors, numbers, parameter names, and reasons; merge duplicates. Keep project names, dimensions, and history out of generic files, and secrets, account IDs, and personal data out of all context files.

## Folder and launcher rules

- Copy both launchers, `Agentic-Fusion.md`, `FDM-Slicing.md`, `Printers.json`, `CLAUDE.md`, `AGENTS.md`, `.agents/` (shared skills and Claude plugin), `.mcp.json`, `settings.json`, and `.codex/` together. Either launcher accepts a dragged project folder and copies missing files without replacing context or an existing printer library. Orca startup is opt-in through `orca-slice`; ordinary Fusion startup does not need Python or a slicer.
- Create `Reference CAD/` when source CAD files are supplied and `Output CAD/` for requested exports; the blank template needs neither directory. Overwrite the existing export file when asked to update it. If `personal logs/` exists in a project, leave it alone unless asked. Never read, print, or copy `.credentials.json`. Exclude `.credentials.json` and `.claude.json` from any template copy; they belong to one machine or account. Do not initialize Git here without the user's direction.
- Keep current facts in `Project.md`; if unique older evidence exceeds its limit, put it in `Project-History/<topic>.md` and link it from `Project.md`. Do not archive ordinary projects. Keep exports in `Output CAD/`, temporary build scripts in the session scratchpad, and design results in Fusion.

## Context size and cleanup

- Decoded-character limits: `Project.md` ≤40,000; this guide ≤15,000; each agent or skill entry ≤4,000; `FDM-Slicing.md` and each task reference ≤20,000; combined always-read text <80,000. Read slicing context only for FDM tasks. Flag and clean an over-limit file before adding memory; never discard unique facts to meet a limit.
- Start `Project.md` with a short `Current state`: purpose, active document, interfaces, key parameters and expressions, accepted decisions, verified geometry, open items. Index deeper sections as needed; read them only for a matching task. Never auto-import all of `Project.md` at startup.
- For full cleanup, first copy files to the session scratchpad. Merge repetition and superseded facts while preserving useful exact values, parameter names, errors, and reasons. Keep core decisions here and conditional procedures in the existing on-demand skill references. Keep current facts in `Project.md`; move only necessary older evidence to indexed `Project-History/`. Keep reusable rules and failure procedures in their shared files.
- Before finishing, compare with the source: retain each unique fact, supersede it correctly, or obtain the user's explicit rejection. Re-read edits, check links and sizes, and remove only identified obsolete runtime data. Preserve portable files, project memory, user folders, and machine or account files.

## Generic design rules (any design)
The mechanisms named below are examples of checks, not assumed parts in this project. Confirm actual hardware and constraints in `Project.md` and Fusion.

- **Model only features that serve a function.** No material-saving ribs, lattices or lightening holes unless asked. Keep ventilation openings next to motors, and keep clearance cuts. To tell a clearance cut from a material saver, suppress it and re-run the joint sweeps.
- **Load paths:** carry primary loads through large bearing areas (dovetail flanks, datum faces). Latches only resist low-load directions, and screws only clamp; locating bosses in existing holes take the shear.
- **Analyze design intent on every touched part (user rule).** Trace real loads, compare strength and stiffness, and raise weak points unprompted; use the [design and assembly checks](.agents/skills/fusion-model/references/design-and-assembly.md) for calculation and shape checks.
- **Priorities (user): design intent, then real verification, then everything else; effort is always last.** Choose between layouts by comparing candidates on the requirements, never by convenience.
- **Drive the design from a small set of intent-level parameters (user rule): almost everything is parametric.** Give an independent user parameter to a real design choice, such as cable diameter, wall thickness, clearance, groove angle, or interface position. Express dependent dimensions from those choices and shared datums instead of creating separate user parameters for every edge, copy, or calculated offset. Before adding a parameter, search for an existing parameter with the same meaning; reuse or derive from it. Promote a hard-coded sketch dimension to a meaningful user parameter when a new feature needs to depend on it. Keep parameter names and expressions tied to function, and inspect all dependents before changing a shared parameter. Use non-parametric methods (direct edits, Replace Face, Split + Remove, planes offset from faces, fills of whatever happens to be there) only very cautiously.
- **Inspect the existing feature tree before every boss, join, or cut extrude (user rule); prefer upstream edits.** Identify the controlling sketch, feature, intent-level parameters, and downstream consumers before changing shape. Edit that source when it owns the requested geometry; add a feature only for a genuinely separate operation or when an upstream edit would break intended downstream geometry. Place a new feature after its dependencies and before features that actually consume its geometry. Use named groups when they clarify the [modeling timeline](.agents/skills/fusion-model/references/timeline.md); design intent and dependencies determine placement. Never blindly append an extrude or fillet as a band-aid for an upstream mismatch. After an edit or insertion, recheck references, constraints, feature health, body count, volume, fit, and motion; reselect broken edges rather than silently altering the intended shape.
- **Avoid functionless crevices, peaks, and fragile patches (user rule).** Simplify at the controlling sketch or feature while preserving seats, clearances, and other functional geometry; use the [shape checks](.agents/skills/fusion-model/references/design-and-assembly.md) when changing a part.
- **Verify motion after changes near moving parts or added material.** Sweep affected joints and compare interference to the baseline; use the [motion checks](.agents/skills/fusion-model/references/design-and-assembly.md).
