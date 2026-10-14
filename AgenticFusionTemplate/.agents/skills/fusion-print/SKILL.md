---
name: fusion-print
description: Review or improve a Fusion design for FFF 3D printing. Use for print orientation, printability scans, supports, printed fits, or iterative DfAM work.
---

# Fusion printing

Read the `Current state` section and relevant print decisions in `Project.md`. Preserve its function and the preventive rules in `Agentic-Fusion.md`. Put design-specific orientation and open printability decisions in `Project.md`. When they conflict, design intent and function take precedence over general design rules, which take precedence over printing preferences. Assembly symmetry takes precedence over a printing tweak that would break it.

The FFF rule baseline is Hydra Research's design rules. Size rules assume about 0.45 mm extrusion line width with a 0.4 mm nozzle; scale them with the actual nozzle. Ask for layer height or nozzle when relevant, and use 0.2 mm (`dfm_layer`) for layer-based features until the user supplies one. A stricter user rule wins.

Load only the reference needed for the current step:

- [Sizes and fits](references/sizes-and-fits.md): minimum dimensions, clearances, printed mating features, and threads. Read for any task involving those features.
- [Overhangs and bed](references/overhangs-and-bed.md): unsupported faces, bridges, holes, bed contact, text, and support policy. Read for printability reviews and changes involving these issues.
- [Voids and cables](references/voids-and-cables.md): open pockets, internal voids, and cable clips. Read when those features are present or proposed.
- [Mechanisms and fasteners](references/mechanisms-and-fasteners.md): printed flexures, screws, latches, and assembly symmetry. Read when the design includes these features.
- [Orientation](references/orientation.md): establish a print layout or evaluate and choose orientation. Read when orientation is missing or the user asks about it.
- [Scan](references/scan.md): inspect a design for overhangs, bridges, bed edges, and other printability findings. Read when performing a live scan or printability review. Use the selected orientation and its project-recorded `dfm_ovh_ang` target.
- [Improvement](references/improvement.md): make and verify print-specific design changes. Read only when the user asks to change or improve the design; also read [scan](references/scan.md) and the rule references that apply to the findings.
- [Requested DfAM assessment](../../../DfAM.md): scope and report a broad manufacturing assessment. Read only when the user asks for a broad DfAM assessment of the design or specified parts; routine printing tasks do not need it.

For a printing task, use the chosen orientation unless asked to change it. When scanning or improving, scan in that orientation and classify findings: safe removal may be applied within the user's requested edit scope; acceptable findings are reported; added material or changes to fit, function, or symmetry require a decision unless a stated exception applies. Verify, save, and record confirmed results in `Project.md` when the task changes the design. For an observed failure, use the `fusion-repair` skill and read only the matching symptom family.
