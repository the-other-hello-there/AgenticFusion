## Fillets
- **Edge fillets selected after a pattern lose references** when the count changes (`Edge N missing`). Options:
  - fillet the seed, then pattern the fillet with its feature;
  - use **rule fillets**: `createRuleFilletInput()`, then `setByBetweenFacesOrFeatures` or `setByAllEdges` with `radius`, then `addRuleFillet`. These select by feature and survive count changes.
  - Edges that stay single full circles also survive.
- **A join added after a fillet stops the round at the new material.** Move the join before the fillet with `join.timelineObject.reorder(fillet.timelineObject.index)`, so the round continues over it. The fillet's edge references survive. Moving the fillet after the join instead changes nothing (dV 0): it keeps its original edge.
- Read edge data (length, vertices) before adding a blend on those edges. Edges the blend consumes raise `InternalValidationError : thisASMEdge` when read afterwards, and recovery state must be inspected; the exception does not prove rollback.
- Rule fillets after `CombineFeature`: the target body's feature still owns its faces. Tool-body faces count as the Combine's, and referencing the tool's own feature gives `ENTITY_REFERENCE_LOST`, so use its faces. Fillet any edges the rule would wrongly catch before applying it.
- Seed fillets that end on a pattern seam: fillet sharp corner edges first, then the face edges with `isTangentChain=False`. Otherwise you get `ASM_BL_CAP_COMPLEX`.
- Variable-radius sets need one tangent-connected edge chain, in order: `addVariableRadiusEdgeSet(edges, start, end, chain)`, then `setMidRadii(radii, positions)`.
- **Rounding a whole tool body:** use `body.edges`, omitting unwanted edges. To edit the set later, roll to the fillet and set `edgeSets.item(0).edges`. For fillet or chamfer failures, consult the `fusion-repair` skill; never silently change the radius or intended shape.
- **Editing an existing fillet's or chamfer's edges:**
  - Call `feature.timelineObject.rollTo(True)`, set `ConstantRadiusFilletEdgeSet.edges` (or `EqualDistanceChamferEdgeSet.edges`) `= collection`, then `timeline.moveToEnd()`.
  - A feature built in assembly context returns proxy edges (`edge.assemblyContext` = that occurrence). Add new edges as `edge.createForAssemblyContext(sameOcc)`.
  - To add edges made by a feature inserted before it (see [Timeline marker](timeline.md)), roll to it and re-select: a short edge the new feature consumed shows as `Edge N missing`.
  - `FilletEdgeSet.deleteMe()` invalidates the other edge-set objects (`An API Object refers to a deleted Object`). Re-fetch them by index, and delete from the highest index down.
  - Removing upstream fillet edges breaks later fillets whose chains included the fillet's boundary edges (`Edge N missing`). Record later fillets' edges by geometry first (line point and direction, or arc center and radius), then re-select them.
  - Downstream features trim edges, so re-find edges by collinearity or concentricity, not by midpoint.

## Complex unions and tangent chains

Where trimming partitions a union crease into short edges ending on sharp faces, test blending the untrimmed union before trimming. Added material changes clearance; rerun motion checks. For complex cavity rims, a task-owned trial can test edges individually with approved fallback radii, recollecting edges after each success. Smaller radii/chamfers remain design changes, not silent fallbacks.

Use `isTangentChain=False` for an isolated-edge diagnostic; otherwise each test may reselect the full tangent loop. Near-flat/fragmented edges can be expensive: bound compute and log progress rather than adopting one project's angle/time cutoff. After upstream changes, reselect by stable geometry and verify dependent blends; health alone does not prove surface quality.
