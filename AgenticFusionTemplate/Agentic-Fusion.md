# Agentic Fusion: shared project rules

Read this short shared guide for every Fusion task, whether using Claude Code or Codex. The launcher creates `Project.md` before the agent starts and preserves an existing one. Fusion designs live in Fusion cloud documents; this folder holds instructions, project context, and requested inputs or exports.

## Decision path for every Fusion session

At session start, read the current-state section of `Project.md` for design intent, interfaces, parameters, decisions, document names, and open items. If it is large or lacks a current-state section, scan its headings and read the relevant sections; do not load the entire file by default. Then route each request:

| Condition | Action |
| --- | --- |
| Inspect a design | Use the MCP read or read-only execution tools; do not change geometry. For scripted inspection, use the relevant `fusion-model` reference. |
| Create or change a design | Establish function, loads, interfaces, and intent-level parameters; use the `fusion-model` skill for the relevant modeling steps; verify geometry, constraints, fit, and motion; then save. |
| Prepare or improve a print | Use the `fusion-print` skill in `.agents/skills/`; read only the references needed for this printing task. |
| Assess DfAM broadly | Use the `fusion-print` skill and its linked `DfAM.md` assessment protocol; assess only the parts in scope. |
| A call, save, sketch, feature, or DfAM fix fails | Use the `fusion-repair` skill for the observed symptom. Keep the preventive rules in this file and the relevant printing rules in force. |

Re-read an authored file after editing it in the same session.

## Authority and memory

- Preserve `Project.md` design intent and function first, then generic design rules, then DfAM preferences. Ask when they conflict. In DfAM, assembly symmetry takes precedence over a printing tweak that would break it.
- Put each fact in one place: current design-specific intent, parameters, and decisions in `Project.md`; shared design priorities in this guide; detailed preventive modeling and MCP procedures in `fusion-model`; generic printing rules and methods in `fusion-print`; the requested broad assessment protocol in `DfAM.md`; observed failure symptoms and recovery in `fusion-repair`. Keep a preventive rule in its operating guide even when its failure example moves to repair guidance.
- Record only verified behavior or user-stated rules. Keep exact useful error text, numbers, parameter names, and reasons. Merge related facts instead of adding duplicates. Generic files must not acquire a project's names, dimensions, or history. Never put secrets, account IDs, or personal data in context files.

## Folder and launcher rules

- Keep both launchers, `Agentic-Fusion.md`, `CLAUDE.md`, `AGENTS.md`, `.agents/` (the shared skills and Claude plugin), `.mcp.json`, `settings.json`, and `.codex/config.toml` together when copying the template. Each launcher accepts a dragged project folder and copies missing template files without replacing existing project context.
- Create `Reference CAD/` when source CAD files are supplied and `Output CAD/` for requested exports; the blank template needs neither directory. Overwrite the existing export file when asked to update it. If `personal logs/` exists in a project, leave it alone unless asked. Never read, print, or copy `.credentials.json`. Exclude `.credentials.json` and `.claude.json` from any template copy; they belong to one machine or account. Do not initialize Git here without the user's direction.
- Keep current project facts in `Project.md`. If preserving unique historical evidence would make it exceed the context limit below, put only that older detail in `Project-History/<topic>.md` and link to it from `Project.md`; do not create archives for ordinary projects. Keep exports in `Output CAD/` and temporary build scripts in the session scratchpad; results belong in Fusion.

## Context size and cleanup

- Keep `Project.md` at or below 40,000 characters, this always-read guide at or below 15,000, each agent or skill entry file at or below 4,000, and each task-specific reference at or below 20,000. Keep the combined always-read text below 80,000 characters. Count decoded characters, not file bytes. If a file already exceeds a limit, flag it and clean it before adding more memory; do not truncate it or drop unique facts just to hit a number.
- Keep a short `Current state` section at the top of `Project.md`: design purpose, active document, interfaces, key parameters and expressions, accepted decisions, current verified geometry, and open items. Add a topic index to deeper sections when needed. Read that section first; retrieve deeper history only for a matching task. Do not automatically import all of `Project.md` into agent startup instructions.
- During a full cleanup, first copy each file to the session scratchpad. Merge repetition and superseded facts while preserving exact useful values, parameter names, error text, and reasons. Keep current facts and decisions in `Project.md`; move only unique older evidence to indexed `Project-History/` files if the size target cannot otherwise be met. Do not move reusable rules or failure procedures into project memory.
- Before finishing cleanup, compare the result against the source and confirm that every unique fact is retained, correctly superseded, or explicitly rejected by the user. Re-read changed files, check links and size totals, and clean only obsolete runtime data after identifying the current session. Preserve portable files, project memory, user folders, and machine or account files.

## Generic design rules (any design)
The mechanisms named below are examples of checks, not assumed parts in this project. Confirm actual hardware and constraints in `Project.md` and Fusion.

- **Model only features that serve a function.** No material-saving ribs, lattices or lightening holes unless asked. Keep ventilation openings next to motors, and keep clearance cuts. To tell a clearance cut from a material saver, suppress it and re-run the joint sweeps.
- **Load paths:** carry primary loads through large bearing areas (dovetail flanks, datum faces). Latches only resist low-load directions, and screws only clamp; locating bosses in existing holes take the shear.
- **"Don't compromise design intent" means analyze, not just preserve (user rule).** Intent is the function, not the reference geometry. On any part touched, actively look for weak points:
  - Trace the primary load (e.g. servo stall torque) from where it enters to where it leaves.
  - Find the smallest section, especially overlaps between features and sharp steps.
  - Estimate the stress with rough numbers: σ = M·c/I under the limiting load (servo stall torque, a hand force), with I from a section sampled by `pointContainment`.
  - Rank stress raisers by that nominal stress before adding fillets. Sharp corners on sections at a few MPa don't need them. The usual hot spots are strain-limited flexures (latches, springs) and thin walls around fasteners that carry torque.
  - Reinforce with webs and 45° gussets where clearance sweeps allow.
  - Raise these issues unprompted rather than waiting for the user to spot them.
- **Size material to the loads (user: "thickness designed for load bearing").** Compute the actuator-limited loads (servo stall torque over its lever, plus what the next joints can push), then the bending moment along the part. Compare I and W section by section with the accepted reference. When stresses are tiny (≈1 MPa), stiffness and torsion size the part, not strength: keep I near the reference and check twist where an off-centre or skewed load acts. For printable material removal and void rules, use the `fusion-print` skill.
- **Priorities (user): design intent, then real verification, then everything else; effort is always last.** Choose between layouts by comparing candidates on the requirements, never by convenience.
- **Drive the design from a small set of intent-level parameters (user rule): almost everything is parametric.** Give an independent user parameter to a real design choice, such as cable diameter, wall thickness, clearance, groove angle, or interface position. Express dependent dimensions from those choices and shared datums instead of creating separate user parameters for every edge, copy, or calculated offset. Before adding a parameter, search for an existing parameter with the same meaning; reuse or derive from it. Promote a hard-coded sketch dimension to a meaningful user parameter when a new feature needs to depend on it. Keep parameter names and expressions tied to function, and inspect all dependents before changing a shared parameter. Use non-parametric methods (direct edits, Replace Face, Split + Remove, planes offset from faces, fills of whatever happens to be there) only very cautiously.
- **Inspect the existing feature tree before every boss, join, or cut extrude (user rule); prefer upstream edits.** Identify the controlling sketch, feature, intent-level parameters, and downstream consumers before changing shape. Edit that source when it owns the requested geometry; add a feature only for a genuinely separate operation or when an upstream edit would break intended downstream geometry. Place a new feature at its functional point in the timeline, after its dependencies and before consumers such as fillets, chamfers, patterns, and cuts. Never blindly append an extrude or fillet as a band-aid for an upstream mismatch. After an edit or insertion, recheck references, constraints, feature health, body count, volume, fit, and motion; reselect broken edges rather than silently altering the intended shape.
- **No functionless crevices or peaks (user rule).** Small steps, ledges, notches and grooves between features, and slivers, knife edges and stubs left where features overlap, add complexity. They make the part harder to modify and weaker. Simplify the geometry rather than decorating it:
  - Make nearly coplanar faces flush, preferably at the source: drive both features' sketch dimensions from one shared user parameter. A 0.05–0.25 mm mismatch between features that should meet is enough to leave a visible step.
  - When changing a dimension, first search every model parameter's expression for the old one. Features that copied it will otherwise keep the old value and leave a ledge; move them all to one user parameter.
  - Trim peaks, stubs and wall corners back to the neighbouring envelope plane with a cut whose sketch is driven by that plane's parameters. Split Body at a plane offset 0 from a face also works, but is less robust.
  - Fill gaps between adjacent features with one extrude, bounded by the neighbouring planes.
  - Replace a staircase of faces (a stepped approximation of a slope) with one plane through the step tops. If a later cut shapes the region, insert the fill before that cut.
  - Prefer sketch edits to direct-edit features. A Replace Face whose target is a face made by another direct edit loses its reference on any upstream recompute and doesn't recover when the value is restored. One that targets a regular feature's face restores, but warns while some upstream parameters are flexed. Move a sketch vertex onto the face's line, or widen the neighbouring feature's sketch, instead.
  - Use fillets only for real stress concentrations on load paths (rank them as above). No blanket of edge-selected fillets on every inside corner; those also break when parameters change.
  - Keep every functional step: datum, seat and locating faces, clearances, servo pockets, holes, teardrops, bridge steps, bed chamfers, lead-ins.
  - **Before removing a peak, check whether it touches a purchased part.** If its removal lowers the interference with a servo, it is part of a press-fit or seat: keep it. A sliver inside a clearance cut is a remnant: remove it.
  - Changing a face that a moving part passes needs a sweep, even if the move is tiny. Keep sloped edges on their original line when raising a top.
  - Give added clearance around functional contact points (e.g. a pinch point) the same treatment: clear the geometry around them.
- **Verify motion after any change near moving parts** (and after adding material anywhere): sweep each affected joint through its limits (`analyzeInterference`, `measureMinimumDistance`). Treat under about 1 mm between printed parts that must remain separate throughout motion as too tight; intentional mating or sliding faces use the fit clearances in the `fusion-print` skill.
  - Sweeping one joint alone from the as-built pose produces whole-arm self-collisions near the limits that don't depend on recent edits. Judge per pair against the same pose in the earlier version, or against recorded baselines.
  - Rolling the timeline marker back resets as-built joint values, so set the pose after moving the marker. A pose set before reads as zero interference.
  - When a rollback isn't practical, intersect the interference body with boxes around the new features to measure how much of it is new. For added material, sweep a TemporaryBRep box around just the addition, extended along the part's install path, against every other body. Exclude parts that move with it, such as the part it holds.
