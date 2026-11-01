---
name: orca-slice
description: Coordinate FDM slice jobs with installed Orca-family slicers, including Snapmaker and Windows Store builds. Discover and ask which slicer to use, prepare/slice headlessly when supported, then open the actual result for non-disruptive UI preview. Use fusion-print for CAD printability and fdm-calibrate for measured tuning.
---

# FDM slicing coordinator

Read `FDM-Slicing.md`, relevant `Project.md` intent/print state and the selected `Printers.json` record. Policy lives there; do not infer preferences or ownership from installed profiles. Design-intent exceptions need a recorded rule/reason. High infill requires user-declared final status; a second support-interface material requires approval of a concrete plan before application.

For a new slicing request, read the [workflow, hierarchy and flowchart](references/workflow.md). Discover installed apps before opening/probing any candidate:

```powershell
py -3 .agents/skills/orca-slice/scripts/slicer.py list
```

Ask which found slicer to use, even with one result. An unambiguous slicer named in the request is already a choice. Retain it through job follow-ups; ask again for a new job. Do not silently substitute an old selection or a running MCP endpoint. `--executable` includes a portable install; Python 3.11+ is required by the standard-library helpers.

Load the needed procedure:

- [Settings and verification](references/settings.md): translate user rules into actual supported settings, resolve feature conflicts, apply job-local overrides and read back effective values.
- [Layer height](references/layer-height.md): apply R12 adaptive height plus smoothing; verify the saved schedule, shell coverage, support compatibility and flow.
- [Support materials](references/support-materials.md): only when proposing/applying a second interface material or diagnosing weak swap layers. Prepare the plan before requesting its required approval.
- [Startup and UI access](references/startup.md): discovery/launch problems, Store activation, non-disruptive background controls and optional MCP. Embedded MCP in a GUI app is not headless.

Default to verified CLI preparation/slicing, then open the completed slice for required layer/toolpath UI preview. `slicer.py slice --select ID ...` opens results after toolpath checks; do not open the source model first. Intermediate comparisons may use `--no-open`; the final result still needs UI preview. Explain an indispensable earlier UI setup exception. Read the chosen build's actual help/schema; never invent an unsupported flag or claim an ignored setting worked.

Window control is allowed only without interrupting normal computer use. Never move the user's cursor, seize focus, send global input or overwrite the clipboard. Use APIs/background controls; if tools cannot comply, keep artifacts and report the exact pending UI check. A window opening is not proof of a completed preview.

Use `printer-library` for portable machines/presets, `fusion-print` for CAD printability, `fdm-calibrate` for physical evidence and `slice-compare` for controlled variants. Record verified job results/exceptions in `Project.md`; reusable user preferences in `FDM-Slicing.md`. Slicing/preview does not authorize printer upload, heating, movement or printing.
