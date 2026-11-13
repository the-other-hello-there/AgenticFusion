## Iterative DfAM improvement
When the user says "iterative DfAM improvement" (alter the design toward the applicable rules linked from `SKILL.md` without breaching function or intent):
1. **Scan** every printed part in its fixed orientation (see [scan.md](scan.md)).
   - **Unnecessary earlier fixes:**
     - Suppress each existing DfAM feature in turn, compare the component volume, then unsuppress. If the volume doesn't change, a later edit superseded the fix; delete it.
     - Delete fixes that a rule no longer calls for, such as teardrops on small pilot or pin holes.
     - After the design changes, re-run the six-way orientation comparison, but keep chosen orientations unless the user asks.
     - Restoring material by deleting a removal-only fix can change fits: re-check rest-pose interference against the baseline.
2. **Apply without asking** fixes that only remove material and keep function and intent. Removal can't create interference, so no new collision sweep is needed.
   - **Teardrop:**
     - Use a sketch on the component origin plane perpendicular to the hole axis. Project the hole's circular edge (for partial cylinders, a fixed circle), then draw a construction line from the center along up (H/V).
     - Add two lines from its end, tangent to the circle and coincident on it, with an angle dimension of `2*dfm_td_ang`. This is fully constrained.
     - Cut over the hole's axial span, with `participantBodies` = the part.
     - Group holes that share an axis and span into one sketch.
     - Don't teardrop small pilot, self-tapping or pin holes (see the small-holes rule in [sizes-and-fits.md](sizes-and-fits.md)). They're accepted as is.
     - Check the apex is inside material at mid-length; otherwise skip and report.
   - **Flat-roof teardrop** for large clearance arcs: the same, plus a roof line perpendicular to the axis line, with its ends on the flanks and length `dfm_bridge_max`. Cut only the region below the roof.
   - **Sacrificial bridge steps:**
     - Use a sketch on the counterbore floor; its edges are already projected.
     - Draw a rectangle tangent to the hole, 2r wide, with two corners on the counterbore circle. Cut it `dfm_layer` deep into the material.
     - Draw a square of side 2r tangent to the hole, collinear with the rectangle, and cut it `2*dfm_layer` deep.
   - **Downward fillet → chamfer:**
     - Record later fillets' edges by geometry first, then roll to the fillet. Remove its downward edges, or delete the edge set from the highest index if none are left.
     - Repair any later fillet that lost references.
     - At the end of the timeline, chamfer the re-found edges with an equal distance taken from the fillet's radius expression. Keep the upward fillets.
     - If the equal chamfer fails (large radius, little material), leave the fillet and ask.
   - **Bed-edge chamfer:** make one chamfer of `dfm_base_ch` on all bed edges. After any change to bed-face edges, update its selection or it loses references. Delete and rebuild it at the timeline end only if no later feature follows it; deleting it can also delete those features. Otherwise, insert the bed-touching addition (corner rounds, flats) just before it (see [Timeline marker](../../fusion-model/references/timeline.md)), then re-select its edges. For failed or missing edges, see the `fusion-repair` skill.
   - **Bed corner rounds:** a fillet of `dfm_bed_r` on the free convex bed corners (see the Bed corners scan in [scan.md](scan.md) and the bed-contact rules in [overhangs-and-bed.md](overhangs-and-bed.md)), checked in each assembled instance.
   - **Crevices and stress raisers:** simplify the geometry first (see `Agentic-Fusion.md`, "No functionless crevices or peaks"). Blend only the load-path corners that remain.
     - Find concave edges and key them by the feature pair of their two faces (see [feature provenance](../../fusion-model/references/helpers.md)). At the edge midpoint, take t1 = tangent × n1, flipped so it points into face 1 (check with `isParameterOnFace`). The edge is concave if t1·n2 > 0.05 and the normals differ by more than 5°.
     - Exclude functional corners: holes, teardrops, bridge steps, pockets that seat purchased parts, servo walls, bed chamfers, and datum or seat corners that locate a mating part.
     - **No universal rule for corners (user):** decide each one by whether a round or chamfer helps or harms printing and function. Round a load-path junction where the round won't face down in print; otherwise use an equal-distance chamfer. Leave it sharp where it is a seat, fit or clearance.
     - Check the whole edge, not its midpoint: sample the round's normals (interpolated between the two face normals) and the chamfer normal along the edge against down. A root corner around an axis parallel to the bed can have a near-horizontal round face at the bottom, while a chamfer may print without support.
     - Measure the distance from the edge proxy to every body in each assembled instance (`measureMinimumDistance`); a bisector point probe missed a seated part. A neighbour within about 1.2 mm makes it a seat or clearance.
     - Apply blends on parts being reprinted anyway. On unchanged reference parts with low nominal stress, offer them instead: they force reprints.
     - Confirm every blend changed the volume by the expected amount (90° round: L·r²·(1 − π/4); 45° chamfer: area × circumference at its centroid). A dV of 0 means the "corner" was a zero-area sliver between nearly coplanar faces.
     - Edge-selected blends lose edges when an upstream parameter moves geometry. Flex-test them, and record which parameters need the edges re-selected.
   - **Open-cavity arcs** that curl over toward an open side: cut the sector polygon centre → tangent point at `dfm_td_ang` → flank meeting the open-side line → arc top, with every vertex as a parameter expression. The part inside the cavity cuts only air.
3. **Skip, and report as acceptable:**
   - pockets about 1 mm deep;
   - a teardrop that would break through a thin lug when the span left is a bridge of 10 mm or less;
   - bridges of 10 mm or less;
   - bed edges that already have chamfers of 45° or steeper.
4. **Ask first** (drastic), with options and their cost in strength, function and DfA symmetry:
   - adding material (gussets, ribs, pillars);
   - changing outlines, mating faces, fits or springs;
   - ergonomic surfaces such as grips;
   - hole sizes set by fasteners;
   - re-sloping faces, or splitting or reorienting parts.
   - Allowed without asking, under the applicable printing rules: free R4 bed corners, smaller fillet-to-chamfer conversions, and gussets that pass the support-policy test in [overhangs-and-bed.md](overhangs-and-bed.md).
   - Overhang-reduction options to weigh, roughly in order:
     - downward fillet → chamfer;
     - slope ledges to 50° or less;
     - **convex rounds that curl under toward the bed** (a sleeve's outer end round meeting the bed tangentially): keep the inside round and make the outside flat (user). Join a quadrilateral per round: the bed point under the centre → the bed point of the tangent → the tangent point, where the outer normal is `90° − dfm_td_ang` from down → a mid-wall point on the same radius. Use parameter-expression vertices, extrude over the round's depth, and insert it before the bed chamfer. It adds material: check it with the support-policy test and the [motion-check box sweep](../../fusion-model/references/design-and-assembly.md#motion-checks);
     - **low-angle ramps rising from the bed:** keep the bed contact flat further out, then rise at `dfm_ovh_ang` to where the ramp meets the next self-supporting face. This removes the support wedge and deepens the section. It adds material: run the support-policy test, joint sweeps, and clearance to external parts the part reaches into. End the new face exactly on any existing steeper plane nearby; an offset parallel face leaves a step and knife edge where the next cut ends;
     - **ceilings under walls that stand beside a box** (wall bottoms above the bed): a `dfm_ovh_ang` gusset from the box side to the wall's outer edge. Start it at the tangent line of any bed corner round on the box side; a lower start leaves a slit against the round. Raise the wall's lower end chamfer to the gusset start (removal only, as long as it stays ≥ `dfm_ovh_ang`), so the two meet in one edge instead of leaving a strip;
     - teardrops;
     - bridge steps;
     - shorten bridges or add a mid-span pillar;
     - split the part with a printed-to-printed joint;
     - add self-supporting ribs;
     - otherwise accept support.
5. **Verify:** use the full build, flex and saved-readback checks in the [modeling timeline](../../fusion-model/references/timeline.md), including active warning states and exact restore. Confirm the volume change against the hand calculation (e.g. a 45° teardrop cap is 0.2146·r² per unit length; a truncated cap subtracts the roof triangle) and take screenshots in print orientation.
6. **Save** a new version with a message listing the changes. Record the design's state and open items in `Project.md`, then report.
