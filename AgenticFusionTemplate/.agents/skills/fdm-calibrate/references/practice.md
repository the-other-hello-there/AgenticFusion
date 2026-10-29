# Calibration practice

Start from the requested goal or evidence. Prefer the installed slicer's relevant calibration tools and current schemas; do not assume every OrcaMCP build exposes a tower generator. Orca's upstream [calibration guide](https://github.com/OrcaSlicer/OrcaSlicer/wiki/calibration_guide) describes its supported tests; use the page appropriate to the installed version when detailed procedures are needed. Exit the slicer's calibration mode by creating a new project after preserving the test's results and any project that was open.

| Target | Evidence and controlled test |
| --- | --- |
| First layer/adhesion | Inspect plate condition, material/plate match, actual nozzle/bed state, leveling and first-layer dimensions. A gap/offset change is a hardware operation, not a slicer-only conclusion. |
| Temperature | Compare the actual spool's documented range, hardware ceilings, cooling and speed; use an appropriate test for bonding/finish/stringing. A material's generic name is not a verified temperature range. |
| Flow ratio | Use measured extrusion/printed surface evidence with temperature and speed held fixed. Separate feed/extruder configuration from per-material flow; do not change both to conceal the same defect. |
| Pressure advance | Use a test appropriate to the firmware and acceleration regime. Separate it from retraction and flow calibration; record how a saved value reaches the printer. |
| Maximum volumetric flow | Hold nozzle/material/temperature fixed, observe the onset of quality loss, and record the usable tested range and chosen margin. A calculated speed is not proof of sustainable flow. |
| Retraction/cooling/bridging | Use a specimen matching the symptom and distinguish moisture, temperature, travel and cooling effects. Avoid transferring a result across different hotends without a new check. |
| Fit/dimensions | Measure several axes/features and distinguish shrinkage, hole behavior, first-layer expansion, flow and source geometry. Keep an intentional CAD clearance separate from a printer-wide compensation. |

For every trial, record a specimen ID/path, baseline and changed values with units, measurement conditions, pass/fail observations and uncertainty. Use the same comparison method between trials. A photograph may support a visual judgment but cannot establish an exact dimension without a scale/measurement.

Apply an accepted value to the narrowest appropriate user preset or job override; preserve the old value and verify it reads back. Do not silently change firmware limits, start/end G-code, global presets, or physical printer settings while interpreting a calibration result.
