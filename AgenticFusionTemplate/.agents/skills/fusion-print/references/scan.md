## Analysis (scan functions)
Use height = −(p·down) and the overhang test n·down > cos(`dfm_ovh_ang`), with the target angle from `Project.md`. Faces built at exactly that angle sit on the threshold, so test with about 0.1° tolerance, and also report the area below the project's slicer support threshold (what will actually be supported).
- **Teardrop candidates:** concave cylinders whose axis is perpendicular to down, with some sampled normal past the limit. A cylinder is concave when the face normal points toward the axis. Sample normals over the parametric range with `evaluator.isParameterOnFace` / `getNormalAtParameter`.
- **Downward fillets:** for each edge of a fillet edge set, interpolate between its two face normals at the edge midpoint. It overhangs if any interpolated normal passes the limit. This covers convex bottom edges and concave ceiling corners.
- **Bed edges:** edges of the planar bed face (normal = down, at minimum height) whose other face is near-vertical or overhanging (n·down < 0.2; negative means an acute edge). Skip faces that slope outward (n·down > 0.6) or meet the bed tangentially. Then check which are still unchamfered, edge by edge, after any later feature that touched the bed face.
- **Bed-facing counterbores:** planar down-facing faces with two single-circle loops.
- **Ceilings:** planar down-facing faces past the limit and above the bed. Classify each edge with `pointContainment` at a point just below and outside it:
  - material there means an anchored edge (bridge abutment);
  - air means a free edge (cantilever).
  - Anchored on two opposite sides means a bridge, and the span is the gap between them.
- **Lowest-line edges** (the face-slope scan misses them; found by the user): straight convex edges that lie horizontal in print, above the bed, where both faces face down and both rise away from the edge. Test the rise with the in-face direction t = edge tangent × n, flipped to point into the face (`isParameterOnFace`); require −t·down > 0. Such an edge is a V knife edge whose first layer is an unsupported line, even when both faces pass the slope rule.
  - If the V stands out from a wall, cut it with a `dfm_ovh_ang` plane through its root at the wall, so the feature grows from the wall. Everything above the plane is unchanged, and the cut only removes material.
  - Don't extend the V's faces below its tip to add a wedge: past the apex the faces cross, and the wedge meets the feature only along the tip line (non-manifold; later blends fail).
- **Provenance:** name the feature that made each flagged face (see [feature provenance](../../fusion-model/references/helpers.md)), so the report speaks in design terms.
- **Space below an overhang:**
  - Sample points in the box below the face, with depth equal to its smaller extent (a 45° gusset fits inside). Transform them by each assembled instance's `occurrence.transform2`, and test `pointContainment` against every other body: first at rest, then while sweeping each revolute as-built joint of the arm through its `rotationLimits`. Restore `rotationValue` afterwards.
  - Pre-filter with `boundingBox.contains`. Sweeps are slow, so log to a file.
  - Empty at rest but occupied in a sweep means motion clearance: don't fill it.
- **Bed corners:** a vertical edge touching the bed counts as a corner if its two faces aren't tangent (>10°). It's convex if the in-face direction t1 (perpendicular to the edge, into face 1) has t1·n2 < 0. Find who is near it with `measureManager.measureMinimumDistance(edgeProxy, body)` in each assembled instance.
- **Fit check after adding material:** run interference across the arm. Intended preloads (spring bumps into a purchased part) must keep their exact interference volume.

## Printer-neutral capability and layer diagnostics

For a printer-neutral requirement, derive the minimum bed envelope, feature/gap resolution, overhang/bridge/support needs and material-change height bands from geometry before using a named machine preset. Inspect several plausible layer schedules; a nominal nozzle assumption or automatic material swapping is not a universal printer capability. A machine-specific slice is a labeled diagnostic until that machine is in scope.

Transform mesh nodes by the complete verified occurrence transform before calculating bounds, downward-facing area and region grouping. An occurrence bounding box can be a loose transformed box; use precise bounds or transformed tessellation, with reported resolution. Mesh local minima, downward area and plan-box clusters flag candidates but do not prove actual layer support.

For offline layer-island diagnostics, intersect triangles with each actual layer plane, node crossing contour segments before polygonizing, classify holes by parity within each closed solid, then union occupied regions across separate solids. Preserve empty layers, including after the first occupied layer: a later reappearing region has no preceding-layer support. Record units, mesh validity, layer origins/heights, tolerances, source hashes and invalid/empty/short-mesh cases. Creating outputs must not overwrite source meshes.

A region overlapping its previous layer can still have a large unsupported extension. Compare the unsupported difference area as well as wholly disconnected islands; neither test evaluates extrusion width, bridging feasibility or complete slicer behavior. Use actual toolpath preview and measured calibration for those claims. Detailed photo/CAD, shell-gap and surface-distance methods live in [reference comparison](../../fusion-model/references/reference-comparison.md), rather than parallel scan implementations.
