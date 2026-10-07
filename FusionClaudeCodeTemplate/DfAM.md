# DfAM.md

Read this file for additive manufacturing (FFF 3D printing) tasks as directed by `CLAUDE.md`. It covers design rules (Hydra Research baseline), analysis, and iterative improvement for any design.

**Precedence:** preserve design intent and function in `Project.md` and general design rules in `CLAUDE.md`; ask when they conflict. Put design-specific print decisions (chosen orientations, open printability items) in `Project.md`. Keep this file generic and DfAM-specific under the placement rules in `CLAUDE.md`.

## Decision path for a printing task

Orientation missing → choose and record it (**Analysis setup**); chosen → keep it unless asked to change. Scan in that orientation (**Analysis**) → classify each finding (**Iterative DfAM improvement**): safe removal → apply; acceptable → report and skip; material addition or changed fit, function, or symmetry → ask unless an explicit exception applies. Then verify → save → record in `Project.md`. Failure → `Fusion-Failure-Repair.md`, with the rules here still in force.

## Design rules (FFF; baseline is Hydra Research, hydraresearch3d.com/design-rules)
- The values assume about 0.45 mm extrusion line width (0.4 mm nozzle). Scale line-width rules with the nozzle.
- Ask for the layer height or nozzle when a rule depends on them. The user prints with variable layer height; assume 0.2 mm (`dfm_layer`) for layer-based features until told otherwise.
- Where a user rule is stricter, the user rule wins.

**Strength and minimum sizes**
- **Walls:** at least 0.9 mm (2 line widths). Perimeters give most of the strength, so thicken walls on strong parts.
- **Features and pins:** at least 1.8 mm (4 line widths). Use store-bought pins in modeled holes for anything functional; thin printed pins (hinges, dowels) don't carry structure (user rule).
- **Holes:** at least Ø2 mm. For tight tolerance, undersize the hole and drill it after printing.
- **Small holes are acceptable as is (user rule)** when meant for self-tapping, or when short enough to drill or carve out easily. Even if poorly resolved, they still mark the center for drilling.

**Fits and threads**
- **Intentional mating or sliding fits between printed parts:** about 0.2 mm loose, 0.1 mm tight. Keep it a parameter. For parts that must remain separate throughout motion, use the about 1 mm running clearance in `CLAUDE.md`.
  - **Angled sliding fits (dovetails):** the clearance must be a true parallel offset of the mating profile. With flank angle a, depth d and clearance c: neck `+ c/cos a`, flare `+ c/cos a + (d + c)·tan a`, floor `− c`.
    - Adding c sideways and cutting c deeper makes the flank steeper and leaves about c/2 at the rail tip. A printed dovetail with 0.08 mm real gap was too stiff to slide (user).
    - **Size clearances by each face's job (user):** a slide-on dovetail only retains the part against pulling off; a clip stops sliding. Give the retaining flanks and the shoulder 0.2 mm square to the faces (about 0.4 mm play per slot; a zero-gap, flat-on-flat shoulder along a long dovetail jammed). Make every non-functional face generously clear, e.g. the rail tip about 0.6 mm from the groove roof.
    - **Interrupted roofs catch the leading end:** windows or gaps in a groove roof leave square edges facing the sliding part. A supported or sagging roof prints low, so a rail tip running close under it butts into the next roof section; the jam distance equals the distance to the first window edge. Clear the tip well below the roof, or lead-in the edges.
    - **Clip lead-in:** push-on force ≈ F_hook·tan(ramp angle + friction angle); a 50°+ ramp multiplies a stiff hook several times. Use about 35° (and keep a square catch face for retention). Check the shoulder or other cuts don't nick the ramp.
    - **Clip engagement at the worst pose:** square catch = hook depth − the part's float away from the latch side (fit clearance, spring-held stop, tilt) − any chamfer on the catch edge (bed chamfers count). Keep at least about 0.4 mm; below that the hook can ride up the chamfer. Cap the hook so it still clears the notch floor at the opposite stop.
    - **Drop-and-slide instead of a long slide (user):** the undercut is needed only where the male features sit at the final pose. Use a few short tabs (e.g. 4, at both ends of both rails) and an open drop-in pocket as wide as the flare beside each short lock slot. The part is set down offset by the travel (tab length + 2 × X clearance) and slid only that far.
      - Extend each lock slot past its tab by at least the latch's play, so the tab stays fully under the lips at either stop.
      - Where the roof holds nothing, cut the lock slots through: no bridge, no support, nothing for a tab to catch.
      - Insertion aids (user): lead-in chamfers on the lip ends and the tab noses, and funnel chamfers on the pocket rims. Don't chamfer the tabs' long flank or tip edges; that eats the flare's pull-out margin.
      - At the drop pose, check that the latch hook clears (e.g. lands past the end of the mating part), and re-check the drop and slide path against every neighbouring body.
    - When only one part is reprinted, derive the mating rail from the as-printed groove (its true flank angle) instead of the nominal profile.
    - Check the real gap with `measureMinimumDistance` between the mating faces, not the parameter.
  - **Grooves printed open toward the bed:** the neck is narrowed by elephant's foot (chamfer it; see Bed contact), and the roof is a bridge that sags into the fit (user practice):
    - support the roof;
    - cut windows through it between short roof "teeth". This roughly halves the area to support and lets the supports be pulled out through the windows;
    - this costs nothing where the roof isn't a bearing face (dovetail flanks bear). Check that the lips outboard of the groove stay attached through the teeth.
- **Modeled threads:** only M5 / UNC #10 and larger, and never in horizontal holes.
- **Holes for post-processed threads** (starting points; verify with calipers):
  - tapped: 90% of the major diameter;
  - self-tapping screw: about 85% of the major diameter, between the screw's core and major diameter, so the screw cuts its own thread (user). 96% left only 0.04 mm per side;
  - heat-set insert: 98% of the insert's outer diameter (reference only; the user rule below prohibits inserts).

**Overhangs and bridges**
- **Overhangs (user):** the slicer's support threshold angle is 30°, measured from horizontal (Bambu/Orca convention: faces flatter than that get support). Design every unsupported down-facing face at least 35° from horizontal (≤ 55° from vertical; `dfm_ovh_ang`) for a 5° margin. This replaces Hydra's 50° from vertical. Teardrop flanks keep their own rule (Holes).
- **Bridges:** 10 mm or less.
- **Unsupported horizontal edges:** 0.9 mm wide or less. The slicer still supports a narrow down-facing strip (e.g. a 0.5 mm relief step), often with a tall support column under it. Give such a strip a 45° underside fill instead, keeping whatever the step relieves.
- **Inside-corner chamfers:** an equal-distance chamfer is 45° (self-supporting) only between a near-vertical wall and a ceiling. Between a ceiling and a sloped face, it bisects them (67.5° against a 45° face). That's acceptable only where the ceiling already needs support.
- **Fillets:** at least Ø1 mm. Never fillet a downward-facing edge; use a chamfer there. Converting a downward fillet to a chamfer (user rule):
  - Convert it only if it isn't needed as a fillet for design intent or DfA (e.g. keep ergonomic grip rounds).
  - The chamfer may be smaller than the fillet, but must be more than half its size. Try equal first, then step down.
  - If nothing above half fits, keep the fillet. Also keep it if the neighboring face already overhangs, since a chamfer gains nothing there.

**Holes**
- **Axis parallel to the bed:** use a teardrop with the point up and flanks within 50° (user rule). Hydra's flat-roof variant offsets the hole top by about one layer (≈0.3 mm) to absorb droop.
- **Hole opening onto a downward-facing surface:** add sacrificial bridge steps, two rectangles tangent to the hole. The first is one layer thick, the second two layers.

**Bed contact and vibration**
- Chamfer bed-contact edges about 0.3 mm (first layer plus one) when printing without a brim, to prevent elephant's foot.
  - Include acute edges, where the neighbouring face overhangs the bed edge: a fit that opens onto the bed face (e.g. a dovetail groove neck) is narrowed exactly where its clearance is smallest.
  - Include the bed edges of corner rounds added after the bed chamfer.
- Round bed-contact corners to R ≥ 4 mm to reduce warping:
  - Apply it only to free convex corners. Skip corners within about 1 mm of another part (they may seat or locate it), and don't re-add rounds like ones the user suppressed.
  - Enlarge existing small corner rounds through their own parameter.
- Print thin, vibration-sensitive surfaces (springs, latches, thin walls, fins) near the bed (user rule).

**Text**
- Horizontal surfaces: emboss at least 0.9 mm wide and under 0.9 mm high; engrave at least 0.5 mm wide and under 0.9 mm deep.
- Vertical surfaces: the same widths, with height or depth under 2 mm.

**Internal voids and cable clips**
- **No closed internal voids (user rule).** Support printed inside one can't be removed, and since the slicer already prints solid regions with sparse infill, an enclosed void barely saves material. Check `body.shells.count == 1` on every printed body.
- **Lighten with open pockets instead:** the pocket isn't printed at all, so the saving is real, and nothing is trapped. Choose the opening face by comparing candidates, built as temporary cuts on the same solid, on stiffness, torsion, stress, bed contact and function.
  - For a beam loaded across its depth (bed side to top), side pockets that leave an I-section were stiffest. They keep both flanges and the full bed contact, and leave the functional top face intact.
  - Bed-side pockets lose the bed flange and bed contact. Top pockets break the top face.
  - Put the web on any line of through-holes, so the holes run inside the web rather than notching a pocket.
  - Gable the pocket roof at `dfm_ovh_ang` across its width so it needs no support. Leave the ridge sharp: a ridge round leaves a strip flatter than the threshold (1.2 mm wide at r 1).
  - Round the other pocket edges, especially those across the bending direction (pocket ends). Add the bed-edge chamfer to the rim.
  - Where the outer bottom rises off the bed (a 35° back), end the bed opening with a full-thickness wall, then follow the rising face at constant skin thickness. Letting the offset skin plane run out to the bed leaves a feather edge.
  - Keep load-introduction zones (roots, lugs, load pads) solid; they act as end diaphragms.
  - An open section is weaker in torsion and loses its bed-side flange, so re-check I and the twist against the reference. A worst-case deflection change of a few hundredths of a mm is negligible next to print tolerance.
- **Snap-in cable channel cut into the bed face:** a keyhole profile, all derived from the cable diameter D:
  - a mouth of D minus the snap squeeze (0.5 mm), with a **rounded inlet** (user: makes the cable easier to push in) built into the profile as arcs tangent to the bed face and the mouth walls. The inlet replaces the bed chamfer there; it is a bed-side curl-up of about the radius;
  - a ~0.8 mm lip, 45° widening, and a cavity of D + 0.2 under a 45° pointed roof;
  - bend radius ≥ 2·D, with the bend ending below the exit face, so no 0.05 mm sliver is left.

  Check the free cable route to it with Ø D cylinders against the neighbouring bodies.

**Printed mechanisms**
- Leaf-spring strain ε ≈ 1.5·t·δ/L². Keep it at or below about 1.5% for PETG, and lower for PLA.
- **Flexure roots (latches, cantilever snaps):** a root fillet shortens the free length. In a crotch of angle θ the tangent point moves out by r/tan(θ/2), so a large fillet in a shallow crotch can double the strain and multiply the deflection force. Compute strain from the real thickness profile (integrate M²/EI), not the formula alone.
  - Keep root fillets small (about 1 mm), or use a **filleted relief hole or undercut** that moves the root back and rounds it at the same time (user recommendation, especially for thicker flexures).
  - Check the relief's wall to neighbouring cavities.
- **Spring tongues in a bed-side wall:** keep the tongue flush with the bed face.
  - Thin it from the non-bed side, and raise the bump by the same amount. Stiffness, strain and preload stay the same.
  - Check that the outward deflection envelope (about bump height plus tolerance outside the wall) stays clear through all motion.

**Support policy (user rule)**
- Support is often unavoidable. Reduce it only where the change doesn't affect design intent at all.
- A gusset or fill under an overhang is allowed only if all of these hold:
  - the space below is empty at rest in every assembled instance;
  - it stays empty through single-joint sweeps of every joint to its limits;
  - it isn't a functional void (cable path, servo pocket, relief, window, tab pocket);
  - it isn't a gripping or ergonomic surface;
  - it stays out of camera fields of view and insertion paths.
- Faces within about 5° of the overhang limit aren't worth reshaping.

**Fastening printed parts (user rules)**
- No heat-set inserts and no captive nuts: they suffer from printing inconsistencies, and the user has neither a soldering iron nor inserts.
- Self-tapping screws into existing hardware (e.g. a servo case) are fine. Reuse existing screw positions with longer screws of the same type, when the user has them.
- **The clamped part gets clearance; only the part the screw threads into gets the pilot.** An M2 self-tapping screw needs Ø2.4 through every printed part under its head. A Ø2 printed "seat" gets threaded too and jacks the joint instead of clamping it. Size the head counterbore to the measured head + 0.3 mm per side.
- Counterbores opening onto the bed face get the bed-edge chamfer. Elephant's foot narrows them exactly where the head enters.
- Snaps and latches only between printed parts with controlled clearances, loaded only in a low-load direction, with finger access to release them.
- Plan screw access in assembly order: a screw that a later part hides must be installed first.

**DfA symmetry (user rule)**
- Symmetry that aids assembly beats a printing tweak that would break it. That covers mirrored left/right parts, reversible or interchangeable parts, and hole patterns that must line up either way round.
- In those cases, either:
  - use a symmetric form of the fix (e.g. matching chamfers on both sides);
  - apply the fix identically on every symmetric instance;
  - or flag the conflict.
- Changes that only remove material, such as teardrops on clearance holes, don't affect how parts mate.

## Analysis setup
- **Parameters:** every fix is driven by `dfm_` user parameters. Create them if missing:
  - `dfm_td_ang` (45°, teardrop flank angle from vertical, at most 50°);
  - `dfm_layer` (0.2 mm until the user gives one);
  - `dfm_base_ch` (0.3 mm);
  - `dfm_bridge_max` (10 mm);
  - `dfm_ovh_ang` (35°, minimum slope from horizontal of unsupported down-facing faces; see Overhangs).
- **Print orientation ("reorient for 3D printing"):**
  1. **Don't break the assembly.** Put one instance of each printed component in a separate grounded root component ("Print Layout") with `addExistingComponent`, set `isGroundToParent` on its children, and add no joints. Never move the assembled instances. Leave out purchased parts.
  2. Rest every part on Z = 0, in a grid with a gap of about 12 mm and the longer footprint side along X.
  3. **Choose orientation strength-first:**
     - keep the bending or tension direction of thin load-bearing features (arms, prongs, ears, tabs, springs, latches, dovetail flanks) in the layer plane. A cantilever's bending stress runs along its length, so a flexure whose length runs along the build direction bends across the layers;
     - when flexures in one part point in different directions and no orientation keeps them all in the layer plane, choose the orientation that suits the most-loaded ones. Offer to turn the others (e.g. a spring tongue's length direction) rather than accept bending across the layers;
     - keep vibration-sensitive surfaces near the bed;
     - print tubes and sleeves axis-vertical;
     - then minimize support area, then maximize flat bed contact, then minimize height.
  4. **Compare all six axis-aligned orientations** with a mesh metric: `body.meshManager.createMeshCalculator()`, `calculate()`, then `nodeCoordinatesAsDouble` / `nodeIndices`. The triangle winding gives outward normals. Sum the area that faces down beyond the limit, excluding bed contact.
     - Also sum the support volume (area × n·down × height above the bed), split by region (mount, cantilever, tip). Total area alone can hide a much shorter support under a cantilever.
     - Prefer support that lands on plain, non-functional faces.
     - **Interfaces on a layer plane:** where a load crosses between features stacked in the build direction (e.g. ear plates and a bridge), measure the material that crosses the layer plane. Sample `pointContainment` just above and below it, then compute the area, polar moment and shear under the peak load. Interlayer strength is the weakest property, so enlarge small crossings with webs or 45° gussets.
  5. **Once chosen, the orientation is fixed** (user rule). Later fixes adapt to it; reorient only if asked.
  6. **Report** per part: the face chosen and why, where strength overrode support, remaining support, and print quantity (one per assembly instance).
  7. Layout copies add to BOM counts (the API has no BOM-exclusion switch) and inherit their source's occurrence appearance.
- **Per-part down vector:** record each part's face-down direction in its own component coordinates. All analysis runs on the component's native body in that frame, so the result is the same for every instance.

## Analysis (scan functions)
Use height = −(p·down) and the overhang test n·down > cos(`dfm_ovh_ang`) (35° from horizontal). Faces built at exactly that angle sit on the threshold, so test with about 0.1° tolerance, and also report the area below the slicer's 30° (what will actually be supported).
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
- **Provenance:** name the feature that made each flagged face (see `CLAUDE.md` → feature provenance), so the report speaks in design terms.
- **Space below an overhang:**
  - Sample points in the box below the face, with depth equal to its smaller extent (a 45° gusset fits inside). Transform them by each assembled instance's `occurrence.transform2`, and test `pointContainment` against every other body: first at rest, then while sweeping each revolute as-built joint of the arm through its `rotationLimits`. Restore `rotationValue` afterwards.
  - Pre-filter with `boundingBox.contains`. Sweeps are slow, so log to a file.
  - Empty at rest but occupied in a sweep means motion clearance: don't fill it.
- **Bed corners:** a vertical edge touching the bed counts as a corner if its two faces aren't tangent (>10°). It's convex if the in-face direction t1 (perpendicular to the edge, into face 1) has t1·n2 < 0. Find who is near it with `measureManager.measureMinimumDistance(edgeProxy, body)` in each assembled instance.
- **Fit check after adding material:** run interference across the arm. Intended preloads (spring bumps into a purchased part) must keep their exact interference volume.

## Iterative DfAM improvement
When the user says "iterative DfAM improvement" (alter the design toward the rules above without breaching function or intent):
1. **Scan** every printed part in its fixed orientation (see above).
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
     - Don't teardrop small pilot, self-tapping or pin holes (see the small-holes rule above). They're accepted as is.
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
   - **Bed-edge chamfer:** make one chamfer of `dfm_base_ch` on all bed edges. After any change to bed-face edges, update its selection or it loses references. Delete and rebuild it at the timeline end only if no later feature follows it; deleting it can also delete those features. Otherwise, insert the bed-touching addition (corner rounds, flats) just before it (`CLAUDE.md` → Timeline marker), then re-select its edges. For failed or missing edges, see `Fusion-Failure-Repair.md`.
   - **Bed corner rounds:** a fillet of `dfm_bed_r` on the free convex bed corners (see the Bed corners scan and the bed-contact rules), checked in each assembled instance.
   - **Crevices and stress raisers:** simplify the geometry first (see `CLAUDE.md`, "No functionless crevices or peaks"). Blend only the load-path corners that remain.
     - Find concave edges and key them by the feature pair of their two faces (feature provenance, `CLAUDE.md`). At the edge midpoint, take t1 = tangent × n1, flipped so it points into face 1 (check with `isParameterOnFace`). The edge is concave if t1·n2 > 0.05 and the normals differ by more than 5°.
     - Exclude functional corners: holes, teardrops, bridge steps, pockets that seat purchased parts, servo walls, bed chamfers, and datum or seat corners that locate a mating part.
     - **No universal rule for corners (user):** decide each one by whether a round or chamfer helps or harms printing and function. Round a load-path junction where the round won't face down in print; otherwise use an equal-distance chamfer. Leave it sharp where it is a seat, fit or clearance.
     - Check the whole edge, not its midpoint: sample the round's normals (interpolated between the two face normals) and the chamfer normal along the edge against down. A root corner around a boss whose axis lies parallel to the bed has a near-horizontal round face at the bottom (4–7° measured), while a 45° chamfer prints there.
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
   - Allowed without asking, under the rules above: free R4 bed corners, smaller fillet-to-chamfer conversions, and gussets that pass the support-policy test.
   - Overhang-reduction options to weigh, roughly in order:
     - downward fillet → chamfer;
     - slope ledges to 50° or less;
     - **convex rounds that curl under toward the bed** (a sleeve's outer end round meeting the bed tangentially): keep the inside round and make the outside flat (user). Join a quadrilateral per round: the bed point under the centre → the bed point of the tangent → the tangent point, where the outer normal is `90° − dfm_td_ang` from down → a mid-wall point on the same radius. Use parameter-expression vertices, extrude over the round's depth, and insert it before the bed chamfer. It adds material: check it with the support-policy test and the box sweep in `CLAUDE.md` (Verify motion);
     - **low-angle ramps rising from the bed** (e.g. a tapered finger's underside at 20°): keep the bed contact flat further out, then rise at `dfm_ovh_ang` to where the ramp meets the next self-supporting face. That's the least material. This removes the support wedge and deepens the section. It adds material: run the support-policy test, the joint sweeps, and clearance to external parts the part reaches into. End the new face exactly on any existing steeper plane nearby (e.g. a 45° tip-trim cut). A parallel face about 1 mm off it leaves a step and a knife edge where the other cut's sketch ends;
     - **ceilings under walls that stand beside a box** (wall bottoms above the bed): a `dfm_ovh_ang` gusset from the box side to the wall's outer edge. Start it at the tangent line of any bed corner round on the box side; a lower start leaves a 0.1–0.4 mm slit against the round. Raise the wall's lower end chamfer to the gusset start (removal only, as long as it stays ≥ `dfm_ovh_ang`), so the two meet in one edge instead of leaving a 1–2 mm strip;
     - teardrops;
     - bridge steps;
     - shorten bridges or add a mid-span pillar;
     - split the part with a printed-to-printed joint;
     - add self-supporting ribs;
     - otherwise accept support.
5. **Verify:**
   - body count and health;
   - the volume change matches the hand calculation (e.g. a 45° teardrop cap is 0.2146·r² per unit length; a truncated cap subtracts the roof triangle);
   - screenshots in print orientation;
   - a full flex test with exact volume restore. Warnings that appear only while flexed are acceptable if restore is clean.
6. **Save** a new version with a message listing the changes. Record the design's state and open items in `Project.md`, then report.
