# Agentic Fusion: shared project rules

Read this guide each session in Claude Code or Codex. Designs live in Fusion cloud documents; this folder holds instructions, context, inputs and exports. Either launcher creates missing `Project.md`.

## Decision path for every Fusion session

Read `Project.md`'s `Current state` for intent, interfaces, parameters, decisions, document names and open items. If absent, scan headings and read relevant sections only. Load skills and references by task; read `FDM-Slicing.md` only for FDM work. Discover MCP tools by their actual schemas, since names vary by client/build.

Check the shared [application-session](.agents/skills/application-session/SKILL.md) status at startup, before substantial app work, after long operations and before yielding. Close unused task documents/windows after save/ownership checks. Checkpoint live work at verified milestones and before agent usage exhaustion. At 11.5 hours prepare maintenance; at 12 hours stop new work in that application, save/verify, perform full context-preserving cleanup and request safe-restart approval. After approval restart/reconnect/restore automatically and verify before resuming. Keep ongoing tasks in `Project.md`; preserve user work and never force-quit to satisfy the deadline. AI-agent processes and unrelated user applications are excluded.

| Condition | Action |
| --- | --- |
| Inspect | Use MCP read or read-only execution; leave geometry unchanged. Load the relevant `fusion-model` reference for scripts. |
| Model | Establish function, loads, interfaces, and intent-level parameters; use `fusion-model`, verify geometry, constraints, fit, and motion, then save. |
| Print | Use `fusion-print` and only task-relevant references. |
| Start an Orca-family slicer or prepare/inspect an FDM slice | Use `orca-slice`; discover installed slicers and ask which to use, keep slicing headless when supported, then open the final result for required UI preview. Read `FDM-Slicing.md` and the current print state in `Project.md`. |
| Define or migrate a printer/profile | Use `printer-library`; read the relevant `Printers.json` record. |
| Calibrate a printer/nozzle/material | Use `fdm-calibrate`; distinguish measured results from slice estimates. |
| Compare slicing variants | Use `slice-compare`; preserve and verify the accepted baseline. |
| Broad DfAM assessment | Use `fusion-print` and its linked `DfAM.md` protocol for the parts in scope. |
| Project-specific skills/context or template updates | Use `project-resources`; keep authored additions in `Project/` and link them from root `Project.md`. |
| Observed call, save, sketch, feature, or DfAM failure | Use `fusion-repair` for the symptom; retain preventive and printing rules. |
| Unused app resources, usage-limit handoff, or application restart deadline | Use `application-session` for shared checkpoints, cleanup, graceful close/restart and resumption. |

Agentic verification is off until the user explicitly requests it for this project. Read the saved choice, covered task types and budget in `Project/Context/Agentic-Verification.json` when present, indexed from `Project.md`. Configure or change it only on a specific user request; never infer opt-in from task complexity or the presence of review files. For an enabled task type, follow `Independent-Review.md` to use the supervisor with its matching task scope; preserve that choice across both agents and restarts. Other tasks retain ordinary modeling/toolpath checks without paid independent review. Default reviewer budget is 12.5% of measured primary-task spending unless the user sets another cap. The supervisor retains original requirements and gates delivery; the primary cannot waive its required reviews, enlarge its budget or authorize exceptions. Missing setup, exhausted budget or incomplete evidence never establishes approval. Protected controller state and a verified bounded reviewer/meter remain required.

## Authority and memory

- Priority: `Project.md`'s design intent and function, then generic design rules, then DfAM preferences; ask about conflicts. Assembly symmetry outranks a printing tweak that breaks it.
- One home per fact: verified project intent, parameters, geometry, document/version names, export provenance, job/slice/calibration results, artifact paths, decisions and open items in `Project.md` or its indexed notes; printer hardware and portable native presets in `Printers.json`; slicing rules and user preferences in `FDM-Slicing.md`; shared priorities here. Task methods belong in the routed skills, broad assessment protocol in `DfAM.md`. Keep prevention in its operating guide even when a failure example lives in repair guidance.
- Record only verified behavior or user-stated rules. Preserve useful exact errors, numbers, parameter names, and reasons; merge duplicates. Keep project names, dimensions, and history out of generic files, and secrets, account IDs, and personal data out of all context files.

## Folder and launcher rules

- Copy both launchers, `Agentic-Fusion.md`, `FDM-Slicing.md`, `Printers.json`, `CLAUDE.md`, `AGENTS.md`, `.agents/` (shared skills and Claude plugin), `.mcp.json`, `settings.json`, and `.codex/` together. Either launcher accepts a dragged project folder and copies missing files without replacing context or an existing printer library. Orca startup is opt-in through `orca-slice`; ordinary Fusion startup does not need Python or a slicer.
- Keep the source migration package runtime-only: launcher/configuration files, shared instructions and on-demand skill resources. Maintenance tests, assessments, backups and generated agent data stay outside it. Copied design projects may add their own verified `Project.md`, inputs and job outputs.
- Both agents may create useful design-specific skills and context within authorized work. Keep canonical skills in `Project/skills/project-<name>/` and supporting context in `Project/Context/`, indexed by root `Project.md`. Use `project-resources` to create/register them; its generated discovery entries contain metadata and a link, not duplicate procedures. Follow indexed project skills when relevant. Keep template guides/skills generic, and preserve existing project additions without relocating or replacing them automatically.
- Create `Reference CAD/` when source CAD files are supplied and `Output CAD/` for requested exports; the blank template needs neither directory. Overwrite the existing export file when asked to update it. If `personal logs/` exists in a project, leave it alone unless asked. Never read, print, or copy `.credentials.json`. Exclude `.credentials.json` and `.claude.json` from any template copy; they belong to one machine or account. Do not initialize Git here without the user's direction.
- Keep current facts in root `Project.md`; put necessary deeper evidence in `Project/Context/<topic>.md` and history in `Project/Context/History/`, linked from `Project.md`. Preserve existing `Project-History/` notes and links. Do not archive ordinary projects. Keep exports in `Output CAD/`, temporary build scripts in the session scratchpad, and design results in Fusion.

## Context size and cleanup

- Decoded-character limits: `Project.md` ≤40,000; this guide ≤15,000; each agent or skill entry ≤4,000; `FDM-Slicing.md` and each task reference ≤20,000; combined always-read text <80,000. Read slicing context only for FDM tasks. Flag and clean an over-limit file before adding memory; never discard unique facts to meet a limit.
- Start `Project.md` with a short `Current state`: purpose, active document, interfaces, key parameters and expressions, accepted decisions, verified geometry, open items. Index deeper sections as needed; read them only for a matching task. Never auto-import all of `Project.md` at startup.
- For full cleanup, first copy files to the session scratchpad. Merge repetition and superseded facts while preserving useful exact values, parameter names, errors, and reasons. Keep core decisions here and conditional procedures in the existing on-demand skill references. Keep current facts in `Project.md`; move only necessary older evidence to indexed `Project/Context/History/`. Keep template procedures shared and project-specific procedures under `Project/`.
- Before finishing, compare with the source: retain each unique fact, supersede it correctly, or obtain the user's explicit rejection. Re-read edits, check links and sizes, and remove only identified obsolete runtime data. Preserve portable files, project memory, user folders, and machine or account files.

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
