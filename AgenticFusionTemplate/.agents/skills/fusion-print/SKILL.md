---
name: fusion-print
description: Review or improve a Fusion design for FFF 3D printing. Use for print orientation, printability scans, supports, printed fits, or iterative DfAM work.
---

# Fusion printing

Use `Project.md`'s `Current state` and print decisions with `Agentic-Fusion.md`'s preventive rules. Record project orientation and open print decisions in `Project.md`. Priority: design intent and function, general design rules, printing preferences; preserve assembly symmetry.

For slicer startup, profile selection or actual slices use `orca-slice` and `FDM-Slicing.md`. The analysis assumptions below are not validated slicing settings.

FFF baseline: Hydra Research design rules. Sizes assume a 0.45 mm line from a 0.4 mm nozzle; scale for the actual nozzle. Ask for nozzle or layer height when relevant; use `dfm_layer = 0.2 mm` until supplied. Stricter user rules win.

Load only relevant references:

- [Sizes and fits](references/sizes-and-fits.md): dimensions, clearances, mating features, threads.
- [Overhangs and bed](references/overhangs-and-bed.md): unsupported faces, bridges, holes, bed contact, text, supports.
- [Voids and cables](references/voids-and-cables.md): pockets, closed voids, cable clips.
- [Mechanisms and fasteners](references/mechanisms-and-fasteners.md): flexures, screws, latches, symmetry.
- [Orientation](references/orientation.md): print layout and orientation selection.
- [Scan](references/scan.md): live printability review in the chosen orientation using project `dfm_ovh_ang`.
- [Improvement](references/improvement.md): requested design changes; also read [scan](references/scan.md) and applicable rule references.
- [Broad DfAM assessment](../../../DfAM.md): requested assessment of the design or specified parts; skip for routine print tasks.

Keep the chosen orientation unless asked to change it. Scan there; safe removal may be applied within requested edit scope, acceptable findings are reported, and added material or changes to fit, function, or symmetry need a decision unless a stated exception applies. For edits, verify, save, and record confirmed results in `Project.md`. Use `fusion-repair` for an observed failure.
