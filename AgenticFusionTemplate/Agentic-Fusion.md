# Agentic Fusion: shared project rules

Read this file for every Fusion task, whether using Claude Code or Codex. The launcher creates `Project.md` before the agent starts and preserves an existing one. Fusion designs live in Fusion cloud documents; this folder holds instructions, project context, and requested inputs or exports.

## Decision path for every Fusion session

Read `Project.md` at session start for design intent, interfaces, parameters, decisions, document names, and open items. Then route each request:

| Condition | Action |
| --- | --- |
| Inspect a design | Use the MCP read or read-only execution tools; do not change geometry. |
| Create or change a design | Establish function, loads, interfaces, and intent-level parameters; build or edit in timeline order; verify geometry, constraints, fit, and motion; then save. Use the sections below at each stage. |
| Prepare or improve a print | Read `DfAM.md` and follow its orientation, scan, decision, and verification path. |
| A call, save, sketch, feature, or DfAM fix fails | Read `Fusion-Failure-Repair.md` for the observed symptom. Keep the preventive rules in this file and `DfAM.md` in force. |

Re-read an authored file after editing it in the same session.

## Authority and memory

- Preserve `Project.md` design intent and function first, then generic design rules, then DfAM preferences. Ask when they conflict. In DfAM, assembly symmetry takes precedence over a printing tweak that would break it.
- Put each fact in one place: design-specific intent and print decisions in `Project.md`; preventive design, MCP, and modeling rules in the matching section below; generic printing rules and methods in `DfAM.md`; observed failure symptoms and recovery in `Fusion-Failure-Repair.md`. Keep a preventive rule here even when its failure example moves to the repair file.
- Record only verified behavior or user-stated rules. Keep exact useful error text, numbers, parameter names, and reasons. Merge related facts instead of adding duplicates. Generic files must not acquire a project's names, dimensions, or history. Never put secrets, account IDs, or personal data in context files.

## Folder and launcher rules

- Keep both launchers, `Agentic-Fusion.md`, `CLAUDE.md`, `AGENTS.md`, `DfAM.md`, `Fusion-Failure-Repair.md`, `.mcp.json`, `settings.json`, and `.codex/config.toml` together when copying the template. Each launcher accepts a dragged project folder and copies missing template files without replacing existing project context.
- Create `Reference CAD/` when source CAD files are supplied and `Output CAD/` for requested exports; the blank template needs neither directory. Overwrite the existing export file when asked to update it. If `personal logs/` exists in a project, leave it alone unless asked. Never read, print, or copy `.credentials.json`. Exclude `.credentials.json` and `.claude.json` from any template copy; they belong to one machine or account. Do not initialize Git here without the user's direction.
- Do not put project notes outside `Project.md`, exports outside `Output CAD/`, or temporary build scripts in this portable folder. Use the session scratchpad for temporary scripts; results belong in Fusion.

## When asked for full cleaning

1. Put every verified or settled lesson, including useful agent memory content, into the proper authored file. Re-read edited files.
2. Remove repetition and superseded facts without losing rules, values, parameter names, error text, or reasons. First copy each file to the scratchpad; afterward check that every number, parameter name, and error string remains or was deliberately superseded.
3. Clean only obsolete runtime data after identifying the current session. Preserve the portable files, `Project.md`, user folders, and machine or account files.

## Generic design rules (any design)
- **Top-down assembly design** for assemblies expected to have more than 5 custom components:
  - Lay out purchased and skeleton parts (motors, cameras) first. Then create each custom component inside the assembly, deriving its interfaces from neighboring geometry so they stay associative.
  - Don't build parts standalone and place them afterwards; bottom-up placement leaves parts out of sync and needs hand-made seating fixes.
  - Small fixes to an existing bottom-up assembly don't need restructuring unless asked.
- **Model only features that serve a function.** No material-saving ribs, lattices or lightening holes unless asked. Keep ventilation openings next to motors, and keep clearance cuts. To tell a clearance cut from a material saver, suppress it and re-run the joint sweeps.
- **Purchased-part models may be only about ±1 mm accurate:**
  - locate the part on hard datum faces of the holder;
  - take up the tolerance with spring preload, never by depending on the part's size;
  - don't let snaps bear on the part;
  - expose its dimensions and every clearance as user parameters, so the real part can be measured and only the holder reprinted;
  - keep openings for its unremovable features (sockets, cable stubs, mics) and use them as extra keys;
  - before filling a gap next to it, check the detailed vendor model (if one is in the reference files) for features the simplified model leaves out. A gap that the real part never reaches is a leftover, not a clearance. Screw-seat fills checked only against a simplified servo once covered the real case's motor boss and label pad, and blocked the insertion path;
  - **verify every holder against the vendor model, not only the simplified one:** `tm.copy` the vendor bodies, place them at each instance's pose, intersect, and sweep a few mm along the seating axis. Where an original reference part exists, place it at the same pose (rebuilt parts keep the reference STEP's native frame): equal overlap means an inherited fit, more means a rebuild regression. Take pilot depths and horn positions from the vendor model too;
  - to make a purchased-part model more accurate, append features in its timeline rather than editing old ones, and keep the face or edge a joint was built on (for example a horn's outer circle) untouched, so the joints don't move.
- **Load paths:** carry primary loads through large bearing areas (dovetail flanks, datum faces). Latches only resist low-load directions, and screws only clamp; locating bosses in existing holes take the shear.
- **"Don't compromise design intent" means analyze, not just preserve (user rule).** Intent is the function, not the reference geometry. On any part touched, actively look for weak points:
  - Trace the primary load (e.g. servo stall torque) from where it enters to where it leaves.
  - Find the smallest section, especially overlaps between features and sharp steps.
  - Estimate the stress with rough numbers: σ = M·c/I under the limiting load (servo stall torque, a hand force), with I from a section sampled by `pointContainment`.
  - Rank stress raisers by that nominal stress before adding fillets. Sharp corners on sections at a few MPa don't need them. The usual hot spots are strain-limited flexures (latches, springs) and thin walls around fasteners that carry torque.
  - Reinforce with webs and 45° gussets where clearance sweeps allow.
  - Raise these issues unprompted rather than waiting for the user to spot them.
- **Size material to the loads (user: "thickness designed for load bearing").** Compute the actuator-limited loads (servo stall torque over its lever, plus what the next joints can push), then the bending moment along the part. Compare I and W section by section with the accepted reference. When stresses are tiny (≈1 MPa), stiffness and torsion size the part, not strength: keep I near the reference and check twist where an off-centre or skewed load acts. Remove the rest with open, support-free pockets, never closed internal voids (user rule; see `DfAM.md`).
- **Priorities (user): design intent, then real verification, then everything else; effort is always last.** Choose between layouts by comparing candidates on the requirements, never by convenience.
- **Check the mechanism before adding a requested feature, and say what it can and can't do.** Example: a rotating jaw's contact moves toward its hinge as it opens. A groove on the moving jaw therefore only catches the small end of the size range; larger objects are held by the fixed-jaw groove alone.
  - A groove pair lines up for one object size only: where the seat points on both jaws lie at the same radius from the hinge. Compute that size before moving a groove.
  - Show a gripped-object range with a demo body over the closing range against the whole arm, not just the jaws. Neighbouring parts (camera mount, servo, walls) may set the size and length limits.
- **Drive the design from intent-level parameters (user rule): almost everything is parametric.** New features take their sizes from a few parameters that state the intent (cable diameter, wall thickness, groove depth and angle, feature position). Dependent sizes are derived expressions; hard-coded sketch numbers a new feature depends on are promoted to user parameters first, at the same value. Use non-parametric methods (direct edits, Replace Face, Split + Remove, planes offset from faces, fills of whatever happens to be there) only very cautiously.
- **Read a requested geometry for its function and material use.** A wall described as running diagonally from a corner to a contact point at a support-free angle is a strut: its down-facing side is the printable diagonal, the space under it stays open, and the material behind it reinforces the neighbours. It is not a solid fill under the diagonal. When asked to restructure a feature, aim to reduce material without losing its function, and say what each region does.
- **No functionless crevices or peaks (user rule).** Small steps, ledges, notches and grooves between features, and slivers, knife edges and stubs left where features overlap, add complexity. They make the part harder to modify and weaker. Simplify the geometry rather than decorating it:
  - Make nearly coplanar faces flush, preferably at the source: drive both features' sketch dimensions from one shared user parameter. Rebuilt reference parts are full of 0.05–0.25 mm mismatches between features that should meet.
  - When changing a dimension, first search every model parameter's expression for the old one (e.g. `cs_zfr + cs_rail_w / 2`). The features that copied it will otherwise keep the old value and leave a ledge; move them all to one user parameter.
  - Trim peaks, stubs and wall corners back to the neighbouring envelope plane with a cut whose sketch is driven by that plane's parameters. Split Body at a plane offset 0 from a face also works, but is less robust.
  - Fill gaps between adjacent features with one extrude, bounded by the neighbouring planes.
  - Replace a staircase of faces (a stepped approximation of a slope) with one plane through the step tops. If a later cut shapes the region, insert the fill before that cut.
  - Prefer sketch edits to direct-edit features. A Replace Face whose target is a face made by another direct edit loses its reference on any upstream recompute and doesn't recover when the value is restored. One that targets a regular feature's face restores, but warns while some upstream parameters are flexed. Move a sketch vertex onto the face's line, or widen the neighbouring feature's sketch, instead.
  - Use fillets only for real stress concentrations on load paths (rank them as above). No blanket of edge-selected fillets on every inside corner; those also break when parameters change.
  - Keep every functional step: datum, seat and locating faces, clearances, servo pockets, holes, teardrops, bridge steps, bed chamfers, lead-ins.
  - **Before removing a peak, check whether it touches a purchased part.** If its removal lowers the interference with a servo, it is part of a press-fit or seat: keep it. A sliver inside a clearance cut is a remnant: remove it.
  - Changing a face that a moving part passes needs a sweep, even if it moved only 0.07 mm. Keep sloped edges on their original line when raising a top.
  - Give added clearance around functional contact points (e.g. a pinch point) the same treatment: clear the geometry around them.
- **Retention methods the user rejects:** straps (inconsistent) and adhesive pads (too permanent).
- **Verify motion after any change near moving parts** (and after adding material anywhere): sweep each affected joint through its limits (`analyzeInterference`, `measureMinimumDistance`). Treat under about 1 mm between printed parts that must remain separate throughout motion as too tight; intentional mating or sliding faces use the fit clearances in `DfAM.md`.
  - Sweeping one joint alone from the as-built pose produces whole-arm self-collisions near the limits that don't depend on recent edits. Judge per pair against the same pose in the earlier version, or against recorded baselines.
  - Rolling the timeline marker back resets as-built joint values, so set the pose after moving the marker. A pose set before reads as zero interference.
  - When a rollback isn't practical, intersect the interference body with boxes around the new features to measure how much of it is new. For added material, sweep a TemporaryBRep box around just the addition, extended along the part's install path, against every other body. Exclude parts that move with it, such as the part it holds.
- **Verify assembly paths, not just the final fit:** a holder can fit a part perfectly yet make it impossible to install.
  - Move temp copies of the part along each candidate path, both straight and pivoting about an end, and check intersection with the holder.
  - Holders that wrap past a part's widest point, or flanges (dovetail flares, lips) overhanging the cavity, trap the part.
  - Contact with spring bumps and latch hooks along the path is expected.
  - Path clearances must cover the purchased part's uncertainty (e.g. 1 mm for a ±1 mm model). Check the paths with the part offset by that amount too.
  - Insertion that rotates a keyed part (a boss in a hole) needs relief along the swept arc, or the key must move.
  - **Every relief for a mating part's protrusion must run out along that part's assembly path, never stop as a closed recess or window.** This covers case bosses and pads in a holder, and screw heads and bearing bosses under a fork or clamp that slides onto a horn. Find the path by translating the part along candidate directions: a direction is free when the overlap never increases from the seated value. Include the installed fasteners at their real (not modelled-flush) height.
- **Verify retention as a configuration space, not a few poses:** for a part held by slots or clips, grid its rigid-body offsets (translations across the slot, roll, pitch, yaw) and test each pose with a TemporaryBRep intersection of slab-clipped copies (about 20 ms each). Then flood-fill the free cells from the seated pose: the part is retained if the reachable set is closed and never touches the scan boundary. Then pull it along the slide direction from the extreme reachable poses to check the stop. Long scans exceed the MCP timeout but finish in Fusion; write results per slice to a file.
- **Check every attachment between features with a wall-thickness map and cross-sections, not just the part's overall look.** Sample face points, ray-march inward with `pointContainment` to the next boundary, and flag anything under about 2 mm by its source feature.
  - Values near acute edges and chamfer toes are artifacts.
  - Watch especially where removal cuts (cavity flanks, openings, slots) meet rounded blanks or neighbouring slots. They leave feather edges and slivers at exactly the connections that carry load.
- **Rigid clamp faces must be truly parallel at the closing pose.** Measure the gap at several points. A hinge axis tilted to the clamp face (e.g. 0.5° from servo seating) gives a gap that varies along the face. A rubber layer hides it, so re-check whenever a compliant layer is removed.
- **Trace every screw path end to end:** head seat → clearance → the material it threads into, with the engagement length, using the screw length the user actually has. Store it as a parameter, with the engagement as a derived parameter (length − clamped stack − gaps), so a different screw shows up at once. A stack sized for a longer screw left a shorter one 0.4 mm short of its pilot.
  - A clearance bore through a locating boss into an empty hole fastens nothing.
  - Give the screw a pilot in the part it threads into (see `DfAM.md` for pilot sizes), blind with a skin if something lies beyond.
  - **Threading into a purchased part:** take the hole positions, depths and the faces around them from the vendor model, mapped into the assembly, not from the simplified model. A rebuild had silently lost seats (counterbores cut through whole walls), moved holes up to 3.8 mm, and left horn stacks 2–5 mm instead of 3–3.5. Its simplified servo lacked the case pilots, had its top deck 1.3 mm low in places, and had its horn hole pattern rotated 45° from the parts.
    - Centre each seat on a real pilot axis, and put the part's face at the pilot on the case face (pad it if it stands back).
    - For a tapped horn: printed stack = screw length − horn plate thickness.
  - **Model every screw in the functional assembly (user rule):**
    - Use one parametric component per screw type (head and shank from user parameters) and one instance per hole.
    - Give each instance a rigid as-built joint to the part it clamps; horn centre screws go to their servo.
    - Find the seats from the as-built geometry: each step from a clearance bore to a counterbore along a hole axis is a head seat.
    - At rest a screw may touch only the material it threads into, an overlap equal to its thread engagement. Anything else is an error.
    - Sweep every joint with the screws present.
- **Explain every accepted interference baseline.** A 539 mm³ "servo vs pocket" overlap, long accepted, was a pocket 1 mm narrower than the reference, so the real servo could not fit. Compare each holder's clamped span at the fastener spots with the real part.

## Fusion MCP workflow
- Scripts must define `def run(_context=None):`. The harness calls it after the top-level code runs. Return output with `print()`.
- Pass `readOnly: true` for inspection-only scripts. These are the only scripts that run while a Fusion command dialog is open; ask the user to close the dialog rather than closing it yourself.
- **The script namespace persists between calls and exec'd helpers share it.** Set every flag and input explicitly on each call: `globals().get('X', default)` can silently reuse an old `X` (a crevice scan kept scanning one part). Give helper globals unique names: a helper's `OUT` replaced the caller's output path. For long scripts, keep the file in the scratchpad and run `exec(compile(open(p).read(), p, 'exec'))` at top level.
- Don't name scratch modules after standard-library modules: a scratchpad `inspect.py` shadowed `inspect` for local Python, and `import numpy` failed. Run local analysis with `python -P` (doesn't prepend the script's folder), or use distinct names.
- Split heavy scripts into batches and log progress to a scratchpad file. After `The operation timed out.`, follow `Fusion-Failure-Repair.md`; a script may still be running.
- A script that raises is rolled back as one transaction. A script that finishes is also one transaction: MCP `undo` reverts the whole run (e.g. a flex-test batch that broke features).
- **Scripted saves and autosave:** Fusion autosaves modified documents at observed 5- and 10-minute intervals. The newest AppLog at `%LOCALAPPDATA%\Autodesk\Autodesk Fusion 360\<id>\logs\AppLogFile*.log` gives the interval as `Autosave background thread started with saveTime: N` and logs `Started Autosave for: <doc>`; closing another document can trigger an off-grid `Started forced Autosave for: <doc>`. Before `doc.save()`, read the latest `Started Autosave` or `Started forced Autosave` time and save well clear of the next tick. If unsure, wait for a new start line and save just after it: ticks can be skipped when nothing changed since the last autosave (only read-only scripts ran), and the next can come a full interval later. Ticks are not reliably on the grid; a modified document went over 10 minutes without a tick at a 5-minute interval. Save in its own MCP call, then confirm `dataFile.versionNumber` against `app.data.findFileById(id).latestVersionNumber` (the document handle can still show the old number immediately after saving) before export. A save collision can crash Fusion; see `Fusion-Failure-Repair.md`.
- **Check a parameter's sign before negating it in an expression:** values like a back face may be stored negative (`-35.2 mm`), so `-param` lands on the wrong side. A sketch that flips sides this way makes a cut that splits the body.
- Look up the API with `queryType: "apiDocumentation"` (a `filter` like `adsk.fusion.LoftFeatureInput`, `apiCategory` member/class) instead of guessing.
- Build in a new scratch document first. Close an unsaved draft with `doc.close(False)`, and touch saved documents only once the result is verified.
- To replace a saved design as a new version: `timeline.moveToBeginning(); timeline.deleteAllAfterMarker()`, delete the user parameters, rebuild in the same document, then `doc.save(msg)`.
- Name a new part with `doc.saveAs(name, app.data.activeProject.rootFolder, desc, '')`. The root component's name follows the document name.
- **Comparing with an earlier version:**
  - Open it with `app.documents.open(doc.dataFile.versions.item(i), True)`. This *replaces* the open document of the same lineage; the old handle then raises `An API Object refers to a deleted Object`.
  - It can instead return the already-open latest document unchanged, so check `dataFile.versionNumber` afterwards. If that happens, `doc.close(False)` first, then open the version from `app.data.findFileById(lineageId).versions` (the `versions` order isn't by number; match `versionNumber`).
  - Only do this when the current version is saved and unmodified.
  - To find a user's edits, dump user parameters, model-parameter expressions, per-component volumes and feature lists to JSON for both versions, then diff them.
  - Measure, then `close(False)`, then reopen the latest with the MCP document `open` and the lineage `fileId`.
- `AsBuiltJoint` has no `healthState`; use `joint.timelineObject.healthState`.
- `jointMotion.rotationValue` can't be set from a `readOnly` script (`Cannot modify the design from a read-only context`).
- An extrude from a sketch on an offset construction plane measures `OffsetStartDefinition` from the sketch plane, not the origin. Sketch on the origin plane and let the extent set the height ("No target body!" otherwise).
- Sketches placed on a HoleFeature's counterbore floor (bridge steps, teardrops) follow `counterboreDepth` edits.
- **Plugging an old hole with a join:** before creating it, check that a ring just outside the fill tool (excluding its teardrop cap) is all material by `pointContainment`. Otherwise use the exact old void shape (diameter plus teardrop) and confirm dV equals the void volume. Where a hole breaks out into a pocket or an edge round, fill only the span that will be re-cut.
- An extrude cut whose tool misses every participant body only warns (health 1, `No target body!`); it doesn't remove anything. A Combine cut whose tool body misses the target stays healthy. So for a trim that legitimately becomes empty over part of a parameter range, extrude the tool as a new body and Combine-cut it. Define its profile so it can't flip (e.g. a quadrilateral bounded by the moving plane and fixed offsets): a sketch triangle whose vertices cross over turns inside out and cuts elsewhere.
- **Split Body + Remove is fragile under parameter changes.** When the split misses its target or the bodies come out in a different order, Remove deletes the main body and the part collapses (a jaw dropped from 30 cm³ to 0.26 cm³ in 5 bodies). Prefer bounded cut features.
- **Rebuilding a hand-made chain (Splits, RemoveBodies, Combines, face-offset planes, profile-based sketches) parametrically:**
  - Roll the marker to each step, `tm.copy` the body (union of all bodies), and difference consecutive states to get each step's net added and removed solids. Name each face by the feature that owns the coplanar face of the model, and convert its vertices into the part's design frame. Each delta is then a few planes that existing parameters already define.
  - Extra material a fill tool puts inside the existing body changes nothing, so its inner boundary may be any line that stays inside the body over the parameter range.
  - In one script: `tm.copy` the final body, delete the old items from the highest timeline index down, insert the new features at the old positions, then difference the result against the copy both ways. Raise (roll back) unless both differences are 0, there is one shell, and every feature is healthy. A trial run with a forced raise is free; long runs time out over MCP but finish, so log to a file.
  - Deleting the Combine where the body identity started broke nothing: later features re-bound to the remaining body.
  - Check edge-selected fillets and chamfers that touch the rebuilt area. Their edges appear and disappear as the parameter moves, and a sweep away from the value and back can leave one permanently `Edge N missing` (the volume doesn't restore; MCP-undo the sweep). Move those edges out of the edge set and rebuild their geometry as sketch-based fills, e.g. a loft between parallel polygons for a 45° chamfer along a polyline.
  - Then sweep the parameter over its intended range and back in the same transaction. Record each value's body count and health, and the parameter's own geometric limits.
- **Retargeting parameters:**
  - Find model parameters by their expression text, with spaces stripped, e.g. `p.expression.replace(' ', '')`, and rewrite them to reference new user parameters.
  - To tell apart sketch dimensions that share an expression, map each dimension's non-origin `SketchPoint` through `sketch.sketchToModelSpace`.
- `TemporaryBRepManager.copy(occurrenceProxyBody)` gives world-space geometry. Transform it and intersect it with `booleanOperation(..., IntersectionBooleanType)` to test paths without moving occurrences.
- `PointContainment` values: 0 = inside, 1 = on, 2 = outside.

## Timeline
- **Feature order (user rule): insert each new feature where it belongs, not at the end by default.** Shape-defining features (bosses, fills, pockets, channels, cuts) go before the finishing features that act on their edges (fillets, chamfers, bed chamfers, bridge steps, teardrops), normally right after the feature they modify. Append after a finish only when it is unavoidable, and say why. A cut added after the rounds leaves part-rounds, steps and unchamfered bed edges (crevices and bumps).
- **Marker (`timelineObject.rollTo(...)`; return with `timeline.moveToEnd()`):**
  - To insert before an existing feature, `rollTo(True)` on it, then create the new feature; it lands at the marker. Then re-check every later feature's health and re-select the edges of fillets and chamfers that changed.
  - Rolling invalidates occurrence handles fetched before it, so fetch them afterwards. At an early marker a sub-assembly occurrence may not exist yet, so take any occurrence of the component (`o.component.name == ...`).
  - Some feature inputs can be read only after `feature.timelineObject.rollTo(True)`, which a `readOnly` script can't do (`Didn't roll editing feature back`): fillet `edgeSet.edges`, pattern `inputEntities`, `ReplaceFaceFeature.targetFaces`, and a sketch's `referencePlane` when it is a face. Read `feature.faces` instead, or use a normal script. `ReplaceFaceFeature` has no source-face getter.
- **Reorder:** `TimelineObject.reorder(beforeIndex)` can't move an item to the very end (`beforeIndex` = count raises `InternalValidationError : featureAtIndex`); move the other items before it instead. Reorder is refused while the moved item fails to compute: delete the failing fillet (check that the feature list lost nothing else), then recreate it at its proper position.
  - A feature that targets a body can't move before the feature where that body's identity starts (a Combine, Split/RemoveBody, or the join that created it): `InternalValidationError : featureCanReoder` or `CIRCULAR_DEPENDENCY`. Use the earliest position after it. A sketch also can't move before the construction plane it lies on (same `featureCanReoder`); move the plane with it.
  - A reorder can change results without failing: a later edge-selected round loses an edge (`Edge 1 missing`, cached geometry), a teardrop loses its body (`No target body!`), or a hole fill moved before the old teardrops lets them re-open the caps inside the plug. Do each part's reorder in a script that compares body count, volume and the health list before and after, and raises (rolls back) on any difference; then try the next slot.
- **Deleting a feature silently deletes later features whose references were its faces or edges** (e.g. a chamfer on a deleted fillet's edges; corner rounds whose vertical edges ended on a deleted bed chamfer). A health check won't show it; re-list features after a delete.
- **Editing an earlier sketch that a later chain depends on:** `rollTo(True)` on the feature that consumes the sketch, edit the sketch there, reassign `feature.profile`, roll on to the next fragile feature to re-select its edges, then `moveToEnd()`. Editing at the end of the timeline recomputes every later feature after each change; an intermediate state broke a fillet and raised.
  - Sketch distance dimensions are magnitudes. On the XZ plane sketch y is −Z, and an existing dimension may read `-( -( expr ) )`. Set a new one to the positive magnitude (e.g. `wf_pk_zb`); a sign slip silently flips the profile and the cut removes the wrong region (the jaw lost 14 cm³ before an undo).
  - To remove a profile vertex: delete its dimensions and the edge to its neighbour, add a coincident constraint to the neighbour, reassign `feature.profile`, then re-select dependent fillets.
- **Don't widen an early cut to fix a later problem:** changing an early feature's extent can split the body, and every later `participantBodies` reference fails (`No target body!`). Restoring the value doesn't repair the references; use MCP undo for both transactions. Insert a new feature at the right position instead.

**Verify every build:** body count, bounding box (cm; ×10 for mm) and volume; every timeline item's `healthState` / `errorOrWarningMessage`; `sketch.isFullyConstrained`; then screenshots (see Screenshot camera; call `viewport.fit()` when done); then a flex test (below). A volume that doesn't return *exactly* after a flex means the geometry resolved differently (e.g. a flipped arc).

## Reusable functions (recreate in the scratchpad each session)
- **Sketch wrapper:**
  - Takes points in model coordinates, as numbers or parameter expressions. It maps them to sketch axes via `sketchToModelSpace` of the unit vectors.
  - Dimensions every vertex to the sketch origin with its expression, so the sketch is fully constrained by construction.
  - On an alignment refusal (see Sketches), nudges the point and retries.
  - Sets each dimension to its positive magnitude (see Features → editing an earlier sketch), then compares every vertex's `worldGeometry` with the intended model point and raises on any mismatch (the raise rolls the script back). A wrong sign on a negative sketch axis stretched a 0.5 mm triangle to 88 mm and joined 884 mm³ instead of 4.
- **Feature wrapper:** extrude, cut or join between two expression extents along the plane normal. For any non-new-body operation, default `participantBodies` to the component's own bodies.
- **Part builder runner:** activate the occurrence, build, return to the root, then report:
  - body count, bounding box and volume;
  - unhealthy features (ignore timeline-suppressed ones);
  - sketches that aren't fully constrained.
- **Flex test:**
  - For each user parameter, add 0.5 mm (length) or −3° (angle). Record only health problems that aren't in the baseline.
  - Restore it and compare every component's volume to 1e-6 cm³, and every sketch's `isFullyConstrained` against the baseline. Fusion silently deletes constraints that a flexed value makes unsatisfiable, and they don't come back on restore while geometry, health and volume all return exactly.
  - Append each result to a scratchpad log. Run it in batches of about 15 parameters, and poll the log after `The operation timed out.`
  - If a parameter leaves features broken after restore (`restore_ok=False`), stop, MCP-undo the batch, and fix the fragile feature before continuing; later results in that batch are polluted.
- **Rest-pose baseline:** save every arm's pairwise interference (identify by `parentComponent.name`), every printed component's volume, and the list of unhealthy features to a JSON file before a multi-part change. Compare after each part.
- **Crevice/peak scan** (per printed component, native coordinates):
  - Narrow planar faces: width ≈ 2·area / outer-loop perimeter, under about 1.5 mm. Classify by their edges: two concave edges is a groove floor, two convex is a fin or ridge top, mixed is a step or ledge.
  - Knife edges: convex edges with an interior angle under about 60°.
  - Name each candidate by feature provenance and skip functional features (holes, teardrops, bridge steps, chamfers, rounds, springs, latches, dovetails).
  - Small pocket faces: under about 12 mm² with only concave edges (blind crescents and slots, e.g. where a fill plane stops short of a round). And bare ledges where a rounded end recedes from a flat interface, leaving a rail or web top exposed.
  - For each one, list the neighbouring faces with their planes (normal and offset) and the features and sketches behind them. Parallel planes offset by 0.05–0.25 mm are sketch mismatches; align them.
  - **Re-run it after every change that splits faces or moves a boundary** (relief strips, windows, a grown neck), not just at the end of a cleanup pass. A missed re-run left a pocket the user had to fill by hand.
  - **Resolve every flag on a feature just added or changed:** fix it, or name the function it serves. A face under about 0.2 mm wide where a new feature meets an existing one is always a leftover. Three such faces at a new strut's junction with a paddle were flagged, passed as "functional", and then fixed by hand by the user. Open gaps a new fill or boss leaves next to the part it fills against (e.g. a boss stopped short of the pocket walls) are crevices too.
- **Section properties:** sample a plane through the native body on a 0.25–0.4 mm grid with `body.pointContainment`, then sum the area, centroid and second moments; the section modulus is I/c. Run it read-only and write the results to a file.
- **Unit slips:** API lengths are cm. Convert every quantity (vertices, bounding boxes, mesh nodes) once, at read time; a mixed cm/mm height silently zeroed an overhang scan. `unitsManager.evaluateExpression(expr, 'mm')` also returns cm (a 30 mm parameter reads 3.0).
- **Feature provenance:** find which feature made a face by matching `face.entityToken` against `feature.faces` for the component's features. Provenance through proxy faces (`face.nativeObject.entityToken`) can mislabel; locate by coordinates instead.
- **Screenshot camera:**
  - Set an orthographic `viewport.camera`: `target`, `eye` = target + direction, `upVector`, `viewExtents` (cm; about half the visible width).
  - To look along a part axis, or at a point given in a part's own frame, transform the point and direction by `occurrence.transform2`. Isolate the part by turning off other occurrences' light bulbs. For see-through views, set native `body.opacity` (0–1) and hide blockers with `isLightBulbOn = False`. Restore visibility and opacity **in the same step, right after the screenshot**.
  - Before every save or export, check that no occurrence is unintentionally hidden: a STEP export silently omits hidden occurrences (235 KB instead of 4.3 MB), and the hidden state is saved with the version.

## Documents, components, parameters
- New documents may default to Part Design, which allows only one component. For multi-component work, set `design.designIntent = AssemblyDesignIntentType` right after `documents.add`.
- User parameters are document-wide, so they can drive internal components. Externally referenced components keep their own parameters.
- Parameter expressions support `sin`/`cos`/`tan`/`sqrt`/`^`. Unitless parameters use unit `''`. Derive dependent geometry, such as tangent points, as parameter expressions to keep it parametric.
- Features in a sub-component:
  - With native inputs (the component's own construction planes, sketches and bodies), build through `comp.sketches` / `comp.features` directly.
  - With proxy inputs, call `occ.activate()` first and pass `createForAssemblyContext(occ)` proxies, then `design.activateRootComponent()`. Otherwise you get "Failed to get owner occurrence transform".
- Fully constrain an assembly with a rigid joint (`JointGeometry.createByPoint` + `setAsRigidJointMotion()`) from each seed occurrence's origin to its parent's origin.
- **Cut/join features in an assembly hit other components' bodies** unless `participantBodies` is set (it silently adds features to those components). Always pass the part's own bodies, including after editing an existing cut; the same applies to `HoleFeatureInput.participantBodies`. See `Fusion-Failure-Repair.md` if an edit added a hidden feature to another component.
- **Sub-assemblies:** create the parts at root, add instances with `sub.component.occurrences.addExistingComponent(comp, T)`, then delete the root originals. Don't use `moveToComponent` (it copies, and later copies fail with `Paste instance source occurrence context is lost`). A sub-component occurrence's transform can't be changed afterwards (`transform overrides can only be set on Occurrence proxy from root component`), so pass the final transform at creation.
  - Proxy bounding boxes read 0 until the next script runs.
- **Placing instances in a sub-assembly whose root occurrence is offset:** `addExistingComponent(comp, T)` honoured T's rotation but added a constant spurious translation that differed per component: (+32, +32, 0) cm for one, (+64, 0, 0) cm for another, in a sub-assembly offset −32 cm in X.
  - Verify the first instance of each component, by its world bounding box against a twin in an identity-placed copy, then compensate.
  - Compose transforms by multiplying `asArray()` values explicitly; don't rely on the order `Matrix3D.transformBy` uses.
  - A jointed occurrence's native `transform2` inside a sub-assembly can lag its solved pose: a trigger at a joint stop read 10° off. Place relative to the root proxy's `transform2`.
- Deleting a component's only occurrence removes the component (it disappears from `allComponents`). Create the first instance at its final transform with `addNewComponent(T)`.
- Sketches in a transformed nested component work in component space: `sketchToModelSpace` returns component coordinates. So a part can be built directly at its final placement with `occurrences.addNewComponent(T)` and the proxy activated.
  - But an existing sketch made while an instance of a shared component was active can return that instance's root coordinates from `sketchToModelSpace` and `worldGeometry`. Check one known point, then map back with the instance's inverse `transform2`. A sketch added later with `comp.sketches.add(comp.xYConstructionPlane)` maps 1:1 to component space.
- The first component created in a document is grounded, and `addExistingComponent` copies inherit it, which silently blocks joint motion (setting `rotationValue` has no effect). Clear `isGroundToParent` on every instance except the intended base. The occurrence collection reorders as you change it, so loop over names until none remain.
- As-built joints inside a sub-assembly: `sub.component.asBuiltJoints.createInput(occ1, occ2, geometry)` with native child occurrences and `edge.createForAssemblyContext(childOcc)` geometry; a circular edge with `JointKeyPointTypes.CenterKeyPoint` gives the revolute axis. Rigid inputs take `None` geometry. Drive with `joint.jointMotion.rotationValue`; limits via `rotationLimits`.
- Body appearance overrides occurrence appearance. To color instances of one component differently, clear `body.appearance` and set it on root-context occurrence proxies.
- **Interference and distance:**
  - `design.createInterferenceInput(proxies)` + `analyzeInterference` (`areCoincidentFacesIncluded = False`), with body proxies (`occ.bRepBodies`). Occurrences nested in a sub-assembly silently return no results.
  - Result `entityOne/Two` may come back without `assemblyContext` (None, seen after `occ.activate()` / `activateRootComponent()`), so a name filter on it silently matches nothing. Identify them by `body.parentComponent.name`, and sanity-check every sweep against a known contact.
  - Minimum distance is `app.measureManager.measureMinimumDistance` (not on `Design`). It rejects native faces of a non-root component (`invalid argument geometryOne`); pass `face.createForAssemblyContext(occ)` proxies. It also accepts TemporaryBRep bodies and `Point3D`.
  - **Line-of-sight checks** (camera field of view): `rootComponent.findBRepUsingRay(origin, dir, BRepBodyEntityTypes.BRepBodyEntityType, 0.001, False, hitPoints)` returns body proxies and an ObjectCollection of hit points in no particular order. Sort the hits by distance, skip the source body and unrelated occurrences (layout copies, the other arm), and take the first.
  - **Clearance to another design** (e.g. the machine a part reaches into): open it, then in one script get its design with `app.documents` → `products.itemByProductType('DesignProductType')`. `tm.copy` its body proxies, transform them into the active design's frame (e.g. through a demo part placed in both), and intersect or measure. Sanity-check the mapping on a part present in both (it should land exactly), then `close(False)` the reference and `activate()` the working document.
  - TemporaryBRep booleans between an imported STEP body and a rebuilt look-alike often fail (`ASM_INCONS_REL`, `ASM_BAD_CONTAINMENT`); compare by `body.pointContainment` sampling or plane sections (`TemporaryBRepManager.planeIntersection`) instead. In a plane-section wire, sample each edge strictly inside its parameter range (`getPointAtParameter` at the exact end can raise `invalid argument parameter`).
- Sketch and feature names share one namespace: a feature named like an existing sketch gets a ` (1)` suffix. Name sketches `<feature> sketch`.

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
- **Tetrahedral corner cut (a corner chamfer through 3 points):** loft from a triangle profile to a `SketchPoint` in a sketch on a parallel offset plane (`loftSections.add(sketchPoint)`). Extend the triangle past the faces that bound the corner into air, so no tool face has to coincide with a slightly tilted model face.
- **Loft rails:**
  - Build multi-curve rails as `adsk.fusion.Path.create(explicitCurves, ChainedCurveOptions.noChainedCurves)`.
  - `createPath(curve, True)` chains into construction lines that share an end point (`ASM_WIRE_SELF_INTERSECTS2`).
  - A shared end point can also drop curves from the path. Keep construction lines off rail end points.
  - Rails must pass exactly through section points (`ASM_GUIDE_NOT_INTERSECT`), so project the section points into the rail sketches.
- **Blended features with true sections** (e.g. elliptical spokes that merge into each other): loft between half-sections of two neighbors, with rails for the outline and the crest, then pattern. Halves meet on the symmetry plane; check for gaps with `body.pointContainment`. Plain lofts carry the true section beyond the blend.

## Fillets
- **Edge fillets selected after a pattern lose references** when the count changes (`Edge N missing`). Options:
  - fillet the seed, then pattern the fillet with its feature;
  - use **rule fillets**: `createRuleFilletInput()`, then `setByBetweenFacesOrFeatures` or `setByAllEdges` with `radius`, then `addRuleFillet`. These select by feature and survive count changes.
  - Edges that stay single full circles also survive.
- **A join added after a fillet stops the round at the new material.** Move the join before the fillet with `join.timelineObject.reorder(fillet.timelineObject.index)`, so the round continues over it. The fillet's edge references survive. Moving the fillet after the join instead changes nothing (dV 0): it keeps its original edge.
- Read edge data (length, vertices) before adding a blend on those edges. Edges the blend consumes raise `InternalValidationError : thisASMEdge` when read afterwards, and the raise rolls back the whole script.
- Rule fillets after `CombineFeature`: the target body's feature still owns its faces. Tool-body faces count as the Combine's, and referencing the tool's own feature gives `ENTITY_REFERENCE_LOST`, so use its faces. Fillet any edges the rule would wrongly catch before applying it.
- Seed fillets that end on a pattern seam: fillet sharp corner edges first, then the face edges with `isTangentChain=False`. Otherwise you get `ASM_BL_CAP_COMPLEX`.
- Variable-radius sets need one tangent-connected edge chain, in order: `addVariableRadiusEdgeSet(edges, start, end, chain)`, then `setMidRadii(radii, positions)`.
- **Rounding a whole tool body:** use `body.edges`, omitting unwanted edges. To edit the set later, roll to the fillet and set `edgeSets.item(0).edges`. For fillet or chamfer failures, consult `Fusion-Failure-Repair.md`; never silently change the radius or intended shape.
- **Editing an existing fillet's or chamfer's edges:**
  - Call `feature.timelineObject.rollTo(True)`, set `ConstantRadiusFilletEdgeSet.edges` (or `EqualDistanceChamferEdgeSet.edges`) `= collection`, then `timeline.moveToEnd()`.
  - A feature built in assembly context returns proxy edges (`edge.assemblyContext` = that occurrence). Add new edges as `edge.createForAssemblyContext(sameOcc)`.
  - To add edges made by a feature inserted before it (see Timeline marker), roll to it and re-select: a short edge the new feature consumed shows as `Edge N missing`.
  - `FilletEdgeSet.deleteMe()` invalidates the other edge-set objects (`An API Object refers to a deleted Object`). Re-fetch them by index, and delete from the highest index down.
  - Removing upstream fillet edges breaks later fillets whose chains included the fillet's boundary edges (`Edge N missing`). Record later fillets' edges by geometry first (line point and direction, or arc center and radius), then re-select them.
  - Downstream features trim edges, so re-find edges by collinearity or concentricity, not by midpoint.
