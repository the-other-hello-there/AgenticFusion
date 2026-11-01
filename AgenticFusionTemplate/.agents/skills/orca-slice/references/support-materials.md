# Multimaterial support interfaces

Read when critical supported geometry would benefit from a different interface material, or when diagnosing weak layers around material swaps. R14 recommends considering it and requires approval before implementation. This file separates user requirements, documented behavior and diagnostic hypotheses.

## Prepare the proposal before approval

Identify the critical surface/tolerance, model material, candidate interface material, actual printer/toolchanger or single-nozzle material system, nozzle temperatures, chamber/bed environment, handling/drying needs, and removal method. Prefer a manufacturer-supported material pair/profile for that exact configuration. Do not assume any PLA/PETG pairing or every soluble material works with every model polymer.

Prepare a job-local plan naming the model/support-base/interface assignments, proposed contact gap and interface density/layers, required prime tower, purge/priming strategy, estimated added changes/time/waste and intended small validation specimen. Check support-height/adaptive-profile/tower compatibility before asking. Present the tradeoff, then request specific approval. Keep the single-material baseline and any unapproved changes unapplied. An explicit approval already given for that concrete plan persists; do not ask again.

## Sources to use for implementation

| Source | Use and scope |
| --- | --- |
| [Prusa: water-soluble materials PVA/BVOH](https://help.prusa3d.com/article/water-soluble-materials-pva-bvoh_162860) | Material compatibility, soluble-interface versus full-support profiles, handling and removal. Its printer/profile instructions concern supported Prusa MMU/XL systems; transfer principles, not printer-specific presets. |
| [Orca: support advanced](https://github.com/OrcaSlicer/OrcaSlicer/wiki/support_settings_advanced) | Actual interface spacing/layers, top/bottom contact gaps and independent support heights. Zero top gap is documented for soluble support; do not apply it universally to an untested breakaway material pair. |
| [Orca: prime tower](https://github.com/OrcaSlicer/OrcaSlicer/wiki/multimaterial_settings_prime_tower) | Prime-tower controls and printer-dependent Type 1/Type 2 behavior. A tower restores extrusion conditions; adequate material purging still needs a verified transition strategy. |
| [Bambu: Support for PLA/PETG technical data sheet](https://store.bblcdn.com/s6/default/fd441c590b03464dba1d5237008732b2/Bambu_Support_for_PLA_PETG_Technical_Data_Sheet.pdf) | An explicit manufacturer starting source when that exact dedicated support filament is proposed. Check its revision, handling and supported base materials; its settings do not apply automatically to generic PLA/PETG used as mutual supports. |
| The actual interface-filament manufacturer's current technical/printing guide | Verify the exact formulation, supported base polymers, temperatures and feed-system compatibility. Find/read the primary guide for the selected material before applying its values; a generic material name or third-party recipe is insufficient. |

Do not copy a universal Z gap, flush volume or fan percentage from a different machine/material. A dedicated soluble interface and a dissimilar-polymer breakaway interface have different bonding/removal behavior. Keep any manufacturer guidance linked in the job record with the actual material/profile version.

## Apply only the approved plan

Enable and verify the required prime tower. Confirm the model stays on the intended structural material and the second material goes only to approved interface regions; support base can remain model material when appropriate. Verify both transition directions, not only model-to-interface. Keep foreign purge out of structural infill/walls unless it was specifically validated and authorized; hidden contamination can undermine the part despite good appearance. A prime tower is not proof that the nozzle was adequately purged.

Read back normalized settings and inspect the actual tower, material assignments, interface contact and support schedule. If independent support height is unavailable/ignored with this tower/style, report the effective conflict and propose a compatible route; do not turn off the required tower or silently claim support independence. For sequential objects, include tower/support geometry and toolchange travels in clearance checks.

## Diagnose weak layers without assuming one cause

The user's proposed failure mode is that a supported model surface is treated as overhang/bridge rather than bottom solid, receiving inappropriate cooling, speed or pattern. Treat that as a hypothesis to test on this build, not a universal diagnosis. Inspect line-type classification, fan commands, speed/flow and temperature at the supported surface and swap heights. Also check cross-material contamination, inadequate priming, elapsed cooling time, support contact and actual line overlap.

There is primary issue evidence of [geometry-dependent overhang-speed/adhesion problems](https://github.com/bambulab/BambuStudio/issues/9366) and an [Orca counterpart](https://github.com/OrcaSlicer/OrcaSlicer/issues/11955), plus historical [Orca cooling discussion](https://github.com/OrcaSlicer/OrcaSlicer/issues/1042). These reports justify inspection; they do not prove the user's exact misclassification mechanism or establish a fix in every release. Check the installed build and current issue evidence when diagnosing a real job.

Candidate remedies include correcting a verified cooling/speed/material-transition issue, choosing a linear solid-fill pattern with better actual adjacent-line contact/overlap, or comparing another slicer after the user selects it. Check width, spacing, flow and wall overlap separately: a wall-overlap setting is not the same as overlap between adjacent solid lines. Do not raise extrusion indiscriminately or present a pattern change as a cure for contamination/thermal defects. Re-slice and compare toolpaths, then use `fdm-calibrate` for a small approved physical bonding/removal test before trusting critical structural parts. A failed specimen remains failed even if its interface removes cleanly.

Record approval scope, material identities and source guides, profile/settings changes, transitions, warnings, measured bonding/removal observations and unresolved hypotheses. Keep final UI preview non-disruptive; if it cannot be inspected without cursor/focus takeover, report the exact pending check and retain the local artifacts.
