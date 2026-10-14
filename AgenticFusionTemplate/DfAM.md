# Requested DfAM assessment

Use this file only when the user requests a broad design-for-additive-manufacturing assessment of a Fusion design or specified parts. Routine modeling, a single printed fit, and a targeted orientation or overhang check do not require this assessment. The [fusion-print skill](.agents/skills/fusion-print/SKILL.md) holds the printing rules and technical methods; read only its references needed for the assessment. Keep verified design-specific facts and accepted decisions in `Project.md`.

First establish which components will be printed and the intended process, material, nozzle, layer height, and orientation from the user's request and verified project context. State missing inputs or assumptions rather than treating defaults as decisions. Include purchased and nonprinted parts only where they constrain fit, assembly, or printing.

Assess the selected printed parts as a connected design: orientation and bed contact; supports, bridges, and overhangs; minimum features and printed fits; strength and stiffness in print orientation; assembly access and postprocessing. Use measurements or observed geometry to distinguish an actual manufacturing problem from a rule that is merely close to its limit. Trace actionable findings to the controlling sketch or feature where possible.

Report a short, prioritized decision table for actionable findings: part and feature, evidence and print consequence, proposed change, effect on function or other parts, and disposition (safe within the requested edit scope, acceptable as-is, or needs a user decision). Note checks that need slicer, material, or print evidence. Do not turn a request for assessment into permission to edit the model. If improvement is requested, use the skill's improvement reference and verify the resulting design; record only confirmed outcomes and accepted decisions in `Project.md`.

