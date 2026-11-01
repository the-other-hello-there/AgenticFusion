# Adaptive layer height with smoothing

Read for R12 on every new or changed job. User policy requires variable/adaptive height with smoothing. This procedure is engineering synthesis of the linked documentation; it is not a validated universal height, smoothing radius or mechanical-strength prescription.

## Prepare a bounded profile

Use the selected printer/nozzle/material's calibrated minimum/maximum heights and accepted first-layer settings. Orca's [layer-height guidance](https://github.com/OrcaSlicer/OrcaSlicer/wiki/quality_settings_layer_height) describes roughly 20-80% of nozzle diameter as usual guidance and warns about flow behavior below and adhesion above that range. Treat that as a reasonableness check, not a replacement for narrower verified hardware/material limits. Do not change nozzle/bed calibration merely to enable adaptation.

Identify shallow slopes, curves, critical Z steps, mating surfaces and support contact heights. Generate an adaptive schedule inside those bounds, balancing the actual quality/time objective. A straight-sided part may yield a uniform schedule; accept that valid outcome rather than adding gratuitous variation. Preserve intentional layer-based pauses/color changes by rechecking their Z positions after regeneration.

## Smooth and inspect the actual schedule

Orca's [variable-layer-height guide](https://github.com/OrcaSlicer/OrcaSlicer/wiki/prepare_variable_layer_height) documents Adaptive, Quality/Speed and Smooth; the Smooth radius sets the Gaussian-filter width. Start from the selected profile's known setting, smooth the schedule, then inspect whether transitions are gradual without erasing fine-detail regions. Record the radius/quality setting if exposed and the saved profile used. Never invent a universal radius or assume that clicking Smooth proves it took effect.

Prusa's [variable-height procedure](https://help.prusa3d.com/article/variable-layer-height-function_1750) describes preserving minimum-height regions with Keep min and manually refining the schedule. Use equivalent selected-build controls when available, not an assumed Orca flag. Smoothing improves height transitions/appearance; these guides do not prove that smoothing alone prevents layer delamination. Bonding still depends on temperature, flow, cooling, material condition and actual contact.

For a conservative flow check, use `Q approximately equals line width x actual layer height x speed` in mm³/s, or prefer the slicer's actual flow preview. This simple rectangular estimate is a planning bound, not an exact bead model. Check the largest local heights and combined infill heights against verified limits; adapt speed if necessary without silently reducing critical geometry. Use `fdm-calibrate` for unverified flow/bonding limits.

## Shells, supports and headless execution

- Verify at least 3 real solid layers on both top and bottom, plus functional thickness. For variable heights, shell thickness is the sum of those local layer heights. Inspect stepped/sloping roofs and the linear layers next to concentric exposed skins.
- Check contact Z gaps, actual support interface heights and whether the selected build can preserve its tower/support synchronization with this layer schedule. Independent support height can be ignored with towers in documented builds; use the effective settings and [support-material procedure](support-materials.md) for an approved second interface material. A rule conflict stays explicit.
- For headless work, reuse a verified prepared 3MF carrying the saved object layer-height profiles, or a supported API that generates/saves them. CLI profile loading alone does not establish that adaptive generation and smoothing occurred. Verify the resulting layer-height sequence in preview. If generation is UI-only in this build, explain that earlier setup exception and use background controls only; never move the user's cursor or seize focus. If unavailable, retain a concrete pending setup item rather than claim adaptive height was applied.
- Keep adaptive profiles tied to the source geometry and orientation. Recompute after geometry/orientation changes; do not reuse a profile just because the file name stayed the same.

At final UI preview, inspect the actual layer-height transitions, critical detail regions, shell coverage, support contact, flow/speed and cooling around changes. Record any unreadable check as unverified. Printed adhesion or dimensional evidence belongs to `fdm-calibrate`; an attractive height graph is not a mechanical test.
