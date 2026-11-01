# FDM slicing rules and preferences

Read for slicer tasks in either agent. This file owns reusable slicing policy and user preferences. Keep hardware/presets in `Printers.json`, verified design/job facts in `Project.md`, and operating procedures in the [slicing workflow, hierarchy and flowchart](.agents/skills/orca-slice/references/workflow.md). Follow `Agentic-Fusion.md` for shared authority, context and CAD rules.

## Authority and exceptions

These are user-required slicing defaults, not universal material-strength claims. Depart from a rule only for a specific conflict with verified design intent; identify the rule, functional reason and job-local exception in `Project.md`. Convenience, a stock preset or faster slicing is not an exception. Resolve unclear intent before making a dependent choice. A software limitation is an unresolved capability limit, not evidence that a rule was satisfied. Explain incompatible requirements and find a supported route without silently switching slicers or disabling a requirement.

Two explicit gates remain: high infill needs the user to designate the version as final, and introducing a multimaterial support interface needs specific user approval. Inferred structural importance does not supply either authorization.

Record only verified facts or user-stated preferences. Keep credentials and machine-specific installation paths out of authored context.

## Workflow preferences

- **Slicer choice:** On each new slicing request, discover installed slicers and ask which to use (including OrcaSlicer, Snapmaker Orca and Windows Store installs). An unambiguous slicer named in that request is already a choice. Keep that choice through the job's follow-ups; ask again for a new job. Do not default to an old selection or require a special MCP build.
- **Execution and preview:** After the choice, keep preparation, profile loading and slicing headless through the selected build's verified CLI. Automatically open the completed slice in that same slicer's UI for layer/toolpath preview; visual preview is required before reporting the job reviewed. Keep intermediate comparison slices headless and open the final result. If that build lacks usable headless slicing or requires an indispensable setup step in the UI, explain the specific limitation before opening its UI earlier. An embedded MCP server does not make a GUI application headless. Preserve any already-open slicer and its unsaved work.
- **Non-disruptive UI:** Controlling the slicer window is allowed only while normal user computer operation continues uninterrupted. Use application APIs or background controls that preserve the user's cursor, focus, typing and clipboard. Never move the user's cursor, seize foreground focus, send global keystrokes/clicks, or require exclusive desktop use. If available UI tools cannot comply, keep completed artifacts and report the exact pending preview action; do not claim visual review. Opening a preview does not authorize desktop takeover.
- **Printer, nozzle and filament:** Not specified. Confirm them before selecting profiles or slicing.
  Look up a supplied printer ID in `Printers.json`; an entry's evidence and source scope determine what is known. The blank library establishes no hardware facts.
- **Quality/strength/time priorities:** Preserve function and verified requirements, then apply the rules below. A successful slice is not measured mechanical strength.
- **Supports and bed adhesion:** Preserve accepted orientation and functional surfaces. Use the support rules below when support is needed; no universal temperature, line width, adhesion aid or support gap has been supplied.
- **Output:** Save requested local artifacts and report warnings and estimates. Printer upload/start is a separate operation.

## Geometry, layers and shells

| Rule | Required default |
| --- | --- |
| R10: wall generator | Use Arachne when a feature narrower than the configured line width is critical to design intent; otherwise use Classic. Check that the critical feature survives in toolpaths, including any Arachne minimum-feature filtering. |
| R6: thin features | When geometry is thinner than twice the nozzle diameter, enable Detect thin walls in Classic. With Arachne, use its thin-feature mechanism because the separate checkbox may be disabled. Never report an unavailable/ignored checkbox as enabled or silently widen a critical CAD feature. |
| R12: variable layer height | Apply adaptive/variable layer height with smoothing for every job. Preserve critical Z geometry and calibrated first-layer behavior. A geometry-driven profile may legitimately remain uniform; do not invent variation. Use the [layer-height procedure](.agents/skills/orca-slice/references/layer-height.md), including bounded heights, smoothing, shell coverage, support compatibility and flow checks. |
| R11: solid shell coverage | Top and bottom shells each have at least 3 actual solid layers, including the exposed surface. Also satisfy any functional thickness in mm; with variable heights, sum the actual layer thicknesses rather than multiplying by a nominal height. |
| R1: exposed surfaces | Prefer concentric top and bottom surface patterns for the user's radial-compression objective. Check geometry and load direction; this preference does not establish a universal strength advantage. |
| R2: adjacent solid layers | The layer immediately above each exposed bottom surface (the second layer of that shell) and the layer immediately below each top surface use a linear solid pattern, such as rectilinear or an available linear/grid equivalent. A linear internal-solid pattern can satisfy this without changing the concentric exposed surfaces. Verify local shells on stepped features, not just the global first/last layers. |
| R5: walls and infill connection | One nominal wall is reserved for intentional flexibility, normally TPU. Otherwise use at least 2 nominal walls, Alternate extra wall, and Embedding wall into infill where supported. These are distinct features; do not pretend one is an alias for the other. Verify infill/wall bonding and report missing capabilities. Thin critical geometry may resolve to fewer paths only as a documented design-intent exception. |

## Infill and version purpose

| Rule | Required default |
| --- | --- |
| R3: density and purpose | Sparse infill is 10% minimum and 70% maximum. Use low infill for fit tests, medium for reasonably structural tests, and high only for a version the user explicitly calls final. Completion of CAD, an export or a good test does not imply final. |
| R4: simple infill | Prefer patterns whose lines stack directly over other lines at the same XY positions across layers, rather than forming laterally shifting ramps/overhangs. This is a toolpath property, not a speed rating or the number of directions. Grid or aligned rectilinear can qualify; verify the actual stack. Gyroid does not qualify. Ordinary alternating rectilinear is not automatically equivalent to aligned rectilinear. Depart only when design intent calls for a different load response, such as quasi-isotropic infill behavior; no pattern makes the whole FDM part isotropic. |
| R7: infill combination | Allow combined infill only with verified directly stacked patterns under R4. Otherwise keep it off. Also verify the combined extrusion height and flow against the actual nozzle/material limits. |

For an actionable convention, use **low = 10-20%, medium = greater than 20% through 40%, high = greater than 40% through 70%**. These bands are an assistant-defined implementation convention, not user-supplied measurements or strength ratings. Choose the actual percentage for the job and record it; they do not replace load-path analysis or calibration. Infer fit/structural-test purpose from an explicit task when clear; resolve ambiguity when it affects the setting, and never infer final status.

## Supports and object order

| Rule | Required default |
| --- | --- |
| R8: independent support heights | Enable Independent support layer height whenever support is used. Verify its effective behavior: some builds ignore it with a prime tower or do not offer it with particular support styles. Treat an ignored setting as an unresolved compatibility conflict. |
| R9: support type | Prefer tree support for small/local features and normal support for large overhang areas. Choose from the selected build's actual styles and verify contact, removability and critical surfaces. |
| R13: sequential objects | Prefer print by object for multiple objects of different sizes, with small/short objects first. Use print by object for tall parts on a bed slinger to reduce cross-object disturbance. Verify full toolhead/gantry/bed sweep clearance and actual order; split the job into separate plates/runs if sequencing cannot be made collision-free. Sequential mode alone does not remove bed-motion wobble. |
| R14: multimaterial interfaces | Recommend a compatible second support-interface material when supported critical geometry benefits, but prepare a concrete plan and obtain user approval before applying it. Enable a prime tower. Preserve the intended model material outside the interface. Read [support materials](.agents/skills/orca-slice/references/support-materials.md) for compatibility, purging, cooling, layer classification and bonding verification. |

For R14, weak bonding at material-swap heights is a specific concern. Inspect the user's suspected supported-surface misclassification (overhang/bridge versus bottom solid), excessive cooling, pattern/contact and speed changes, and possible material contamination. Comparing another slicer or a solid pattern with better line contact/overlap are candidate remedies, not proven fixes for every case. Never silently change the selected slicer. Follow a guide matched to the actual material pair and hardware; a prime tower does not replace adequate purging.

## Researched operating practices

Apply the supplementary profile/calibration, load-path/perimeter, roof-support/infill-crossing, flow/cooling and sequential-clearance practices in [settings and verification](.agents/skills/orca-slice/references/settings.md). That reference owns their procedures and primary sources; they support the user rules and yield to verified design-intent exceptions. The slicing workflow owns export provenance, profile preservation, effective-setting readback, final-preview checks and job reporting. Use `slice-compare` for controlled baseline comparisons and `fdm-calibrate` for physical strength, fit or adhesion evidence.

## Preference updates

When the user gives a durable preference, update its existing entry with scope and exceptions. Keep this file concise (target at most 20,000 decoded characters), read only for FDM work, and preserve a copied project's edits during template setup. Link detailed calibration evidence from `Project.md` when needed.
