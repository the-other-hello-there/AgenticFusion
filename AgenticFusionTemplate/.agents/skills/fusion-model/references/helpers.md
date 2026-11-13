## Reusable functions and task-specific wrappers
- **Sketch wrapper:**
  - Takes points in model coordinates, as numbers or parameter expressions. It maps them to sketch axes via `sketchToModelSpace` of the unit vectors.
  - Dimensions every vertex to the sketch origin with its expression, so the sketch is fully constrained by construction.
  - On an alignment refusal (see [Sketches](sketches-and-features.md)), nudges the point and retries.
  - Sets each dimension to its positive magnitude (see [Timeline → editing an earlier sketch](timeline.md)), then compares every vertex's `worldGeometry` with the intended model point and rejects any mismatch. Raising does not guarantee rollback; inspect actual state and recover from the verified trial/checkpoint.
- **Feature wrapper:** extrude, cut or join between two expression extents along the plane normal. For any non-new-body operation, default `participantBodies` to the component's own bodies.
- **Part builder runner:** activate the occurrence, build, return to the root, then report:
  - body count, bounding box and volume;
  - unhealthy features (ignore timeline-suppressed ones);
  - sketches that aren't fully constrained.
- **Flex test:**
  - When the user asks for a robust parametric solution, keep working through every observed failure until the intended parameter domain regenerates without stale references, preserves functional geometry, and restores exact volume and sketch constraints. A few successful flexes do not establish robustness. State physical parameter bounds from interface geometry and test on both sides of each nominal value within those bounds; do not use an arbitrary narrow range to hide a failure.
  - Check geometric quality while flexed as well as feature health: disappearing fillet edges, sub-0.2 mm slivers, changed contact faces, disconnected solids, and support-facing ceilings can survive a healthy recompute. Resolve each issue or record an explicit, justified domain limit before calling the design complete.
  - For each user parameter, add 0.5 mm (length) or −3° (angle). Record only health problems that aren't in the baseline.
  - Restore it and compare every component's volume to 1e-6 cm³, and every sketch's `isFullyConstrained` against the baseline. Fusion silently deletes constraints that a flexed value makes unsatisfiable, and they don't come back on restore while geometry, health and volume all return exactly.
  - Append each result to a scratchpad log. Run it in batches of about 15 parameters, and use the [bounded log monitor](verification.md#bound-a-long-run) after `The operation timed out.`
  - If a parameter leaves features broken after restore (`restore_ok=False`), stop, recover the trial with verified undo/checkpoint state and fix the fragile feature before continuing; later results in that batch are polluted.
- **Rest-pose baseline:** save every arm's pairwise interference (identify by `parentComponent.name`), every printed component's volume, and the list of unhealthy features to a JSON file before a multi-part change. Compare after each part.
- **Crevice/peak scan** (per printed component, native coordinates):
  - Narrow planar faces: width ≈ 2·area / outer-loop perimeter, under about 1.5 mm. Classify by their edges: two concave edges is a groove floor, two convex is a fin or ridge top, mixed is a step or ledge.
  - Knife edges: convex edges with an interior angle under about 60°.
  - Name each candidate by feature provenance and skip functional features (holes, teardrops, bridge steps, chamfers, rounds, springs, latches, dovetails).
  - Small pocket faces: under about 12 mm² with only concave edges (blind crescents and slots, e.g. where a fill plane stops short of a round). And bare ledges where a rounded end recedes from a flat interface, leaving a rail or web top exposed.
  - For each one, list the neighbouring faces with their planes (normal and offset) and the features and sketches behind them. Parallel planes offset by 0.05–0.25 mm are sketch mismatches; align them.
  - **Re-run it after every change that splits faces or moves a boundary** (relief strips, windows, a grown neck), not just at the end of a cleanup pass.
  - **Resolve every flag on a feature just added or changed:** fix it, or name the function it serves. A face under about 0.2 mm wide where a new feature meets an existing one is a leftover. Open gaps a new fill or boss leaves next to the part it fills against are crevices too.
- **Section properties:** sample a plane through the native body on a 0.25–0.4 mm grid with `body.pointContainment`, then sum the area, centroid and second moments; the section modulus is I/c. Run it read-only and write the results to a file.
- **Unit slips:** API lengths are cm. Convert every quantity (vertices, bounding boxes, mesh nodes) once, at read time; a mixed cm/mm height silently zeroed an overhang scan. `unitsManager.evaluateExpression(expr, 'mm')` also returns cm (a 30 mm parameter reads 3.0).
- **Feature provenance:** resolve entity tokens through the Design, then corroborate the owning feature, component context and geometric coordinates. Comparing token strings alone is not stable identity; proxy/native provenance can mislabel a face.
- **Screenshot camera:**
  - Set an orthographic `viewport.camera`: `target`, `eye` = target + direction, `upVector`, `viewExtents` (cm; about half the visible width).
  - To look along a part axis, or at a point given in a part's own frame, transform the point and direction by `occurrence.transform2`. Isolate the part by turning off other occurrences' light bulbs. For see-through views, set native `body.opacity` (0–1) and hide blockers with `isLightBulbOn = False`. Restore visibility and opacity **in the same step, right after the screenshot**.
  - Before every save or export, check that no occurrence is unintentionally hidden: a STEP export silently omits hidden occurrences, and the hidden state is saved with the version.

## Shared helper library and measurement limits

Use [fusion_helpers.py](../scripts/fusion_helpers.py) from a task script, passing the intended Design, ValueInput factory, TemporaryBRepManager and bodies explicitly. It has no active-document globals or project paths. It provides batched parameter updates, bounded selected-parameter deletion, checked temporary intersection volume, exact plane-section bounds and bounded all-triangle sampled surface distances. API-adapter tests verify contracts with fixtures; verify the live kernel result in the actual project before claiming a design passes.

A modeling wrapper should preserve parameter expressions and explicit units for points, planes, arcs, profiles, extrudes/revolves and participating bodies. Map general planes using their complete basis rather than assuming axis alignment. Project datums before deferred computation, use dimension methods appropriate to their entities, and verify full constraint plus intended point positions after solving. A profile bounding box is not true containment or correct loop/hole selection. Read and identify feature results at creation; see [components](components.md).

For outline width/height along an axis, sample exact `TemporaryBRepManager.planeIntersection` wires at explicit stations and inspect their bounds. Retain empty stations and evaluator errors. Mesh-node bins can create false outline turns or miss flat face interiors. Count significant changes only at a declared smoothing tolerance and spacing; these specify diagnostic resolution, not universal acceptance. [Autodesk plane sections](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_TemporaryBRepManager_planeIntersection.htm).

Budget containment, ray, Boolean and mesh comparisons before launching large grids; record coverage and unknowns. For small-face/edge surveys, check evaluator success flags, sample strictly inside edge parameter ranges and report failed normals/reads instead of skipping them. Small faces, short edges and near-tangent creases are diagnostic candidates, not intrinsically invalid geometry. Use [reference comparison](reference-comparison.md) for CAD/photo metrics, pocket floors, insertion paths and display-only graphics.
