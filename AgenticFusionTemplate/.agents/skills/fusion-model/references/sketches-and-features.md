## Sketches
- `addTwoPointRectangle` adds no horizontal/vertical constraints; add them yourself.
- On the XZ plane, model X is sketch horizontal. Dimension radial distances from the origin parallel to the line; the perpendicular orientation over-constrains the sketch.
- A horizontal/vertical distance dimension from the origin is refused (`VCS_SKETCH_OVER_CONSTRAINTS`, sometimes `Already has same dimension on referenced geometry`) when the point is exactly aligned with another point that already has that dimension, even though it isn't redundant. Nudge the point with `sp.move(vector)`, add the dimension, then set its expression. For a point that mirrors a dimensioned one, use `addSymmetry` about the axis instead. Two points on one horizontal line: dimension one, and constrain the line horizontal.
- `sketchFittedSplines.add(points)` makes new fit points even when given SketchPoints; add coincident constraints from `spline.fitPoints` to the dimensioned points.
- Sketch rectangular pattern: `createRectangularPatternInput(entities, SpacingPatternDistanceType)`, `setDirectionOne/Two(line, qty, spacing)`. `isSuppressed` takes q1*q2-1 flags (seed excluded) ordered with direction one fastest. This is the reliable way to skip instances; suppressing elements of a *feature* pattern via the API fails (`Didn't roll editing feature back` / `API Function not yet implemented`).
- Redundant constraints raise `VCS_SKETCH_OVER_CONSTRAINTS`. Common cases:
  - collinear on a line whose points are already fixed (use point-on-line coincident instead);
  - a vertical constraint plus symmetry;
  - tangency plus equal radius on symmetric arcs.
- Ellipses need a constraint on `majorAxisLine` (horizontal, vertical, or parallel to a projected axis) to be fully constrained. Making `minorAxisLine` non-construction splits the ellipse into two half profiles.
- **An arc with two fixed end points and a radius dimension has two solutions,** and a recompute can flip it. Fix it with a tangent constraint and make the radius a driven dimension (`isDriving=False`).
- Sketch circular pattern: `geometricConstraints.createCircularPatternInput(entities, centerPoint)` with `quantity = V('Param')`. It stays fully constrained, and copies close profiles with the seed.
- A sketch created on a `BRepFace` already contains that face's edges as projected curves; projecting one of them again returns an empty item (`None`). Find the existing curve instead (e.g. by radius).
- `sketch.project(sketchPointOrCurve)` links geometry across sketches. A projected point's `worldGeometry` is in model coordinates. `profile.areaProperties().centroid` is in sketch space; convert it with `sketchToModelSpace`.
- A construction plane made with `setByAngle(axis, angle, plane)` can have either normal direction. Check it, and negate the offset if needed.
- Avoid driving a critical cut from a construction plane whose path or target is a B-Rep face or edge when stable user-parameter datums can define the same plane. A path-based plane can flip orientation on a parameter flex and leave the cut using stale geometry even after the parameter is restored. Use a parameter-driven angle and offset; fully constrain the cut sketch to that plane and recheck the cut on flex and exact restore.

## Features
- Rectangular patterns have only two directions. For 3D grids, pattern inside a sub-component, then pattern that occurrence.
- With only direction one, set `quantityTwo = '1'`. The default is 3 at 0 spacing, which makes stacked duplicates.
- A join feature only merges bodies listed in `participantBodies` that it touches. Check the body count after each join.
- A symmetric Through All extrude (`setAllExtent(SymmetricExtentDirection)`) can cut only one side. Use a bounded two-sided distance instead.
- Seam edges of revolved bodies can have one face, so check `edge.faces.count` before calling `faces.item(1)`.
- Non-uniform scale: create it with `createByReal` factors, then set `scaleFeature.zScale.expression`. Expression ValueInputs fail.
- `DraftFeatures.createInput` needs a Python list of `BRepFace` (not an ObjectCollection). It also drafted faces that weren't selected, which changed the volume by hundreds of mm³. For a small tilt of one face, use an explicit wedge cut with parameter-expression vertices instead.
- **Sweep paths:** `adsk.fusion.Path.create(collection, noChainedCurves)` raised `InternalValidationError : Utils::getObjectPath` for a sketch line + arc + line. `comp.features.createPath(firstCurve, True)` chained them. An arc with a dimensioned centre and one shared end is fully constrained by a horizontal/vertical constraint on the next line; dimensioning both arc ends over-constrains it.
- **Prismatic tapered pockets as lofts:** a loft between two polygon sections whose corresponding edges are parallel gives exact planar faces. Use it for voids whose walls follow a tapered side and whose roof follows a sloped face, and for equal-distance chamfer fills along a polyline: the first section is the polyline offset by d (mitred corners), the second is the polyline itself, d further along the normal.
  - When a pocket approaches another cut, derive its bounding edge from that cut's maximum reach and the intended wall thickness so the voids remain separated over parameter changes. A downstream Boolean guard that merely clips their overlap can create thin wedges and small sliver faces where the guard meets the pocket web.
- **Tetrahedral corner cut (a corner chamfer through 3 points):** loft from a triangle profile to a `SketchPoint` in a sketch on a parallel offset plane (`loftSections.add(sketchPoint)`). Extend the triangle past the faces that bound the corner into air, so no tool face has to coincide with a slightly tilted model face.
- **Loft rails:**
  - Build multi-curve rails as `adsk.fusion.Path.create(explicitCurves, ChainedCurveOptions.noChainedCurves)`.
  - `createPath(curve, True)` chains into construction lines that share an end point (`ASM_WIRE_SELF_INTERSECTS2`).
  - A shared end point can also drop curves from the path. Keep construction lines off rail end points.
  - Rails must pass exactly through section points (`ASM_GUIDE_NOT_INTERSECT`), so project the section points into the rail sketches.
- **Blended features with true sections** (e.g. elliptical spokes that merge into each other): loft between half-sections of two neighbors, with rails for the outline and the crest, then pattern. Halves meet on the symmetry plane; check for gaps with `body.pointContainment`. Plain lofts carry the true section beyond the blend.

