## Additional design and assembly checks
Apply these checks only to relevant parts and mechanisms confirmed for the current design. Examples and past retention preferences are not project facts; `Project.md` records the current project's choices.

- **Choose the assembly workflow from the relationships that must change together, not a component-count threshold.** For interdependent custom parts, establish shared parameters, datums, and any useful layout or skeleton geometry, place purchased parts that define interfaces, then create or edit the custom components in assembly context. Activate each component before defining its geometry. Make only the necessary interface references associative, and prefer stable origins, datums, sketches, or construction geometry over edges likely to change. Keep the dependency direction clear and avoid circular or unnecessary cross-component references.
  - Standard, reusable, or independently specified parts can be modeled separately and inserted; a mixed workflow is valid when different subassemblies have different needs. Preserve an existing assembly's sound structure for a local fix. Verify fit, motion, and reference updates after changing shared drivers.
- **Purchased-part models may be only about ±1 mm accurate:**
  - locate the part on hard datum faces of the holder;
  - take up the tolerance with spring preload, never by depending on the part's size;
  - don't let snaps bear on the part;
  - expose its dimensions and every clearance as user parameters, so the real part can be measured and only the holder reprinted;
  - keep openings for its unremovable features (sockets, cable stubs, mics) and use them as extra keys;
  - before filling a gap next to it, check the detailed vendor model (if one is in the reference files) for features the simplified model leaves out. A gap that the real part never reaches is a leftover, not a clearance;
  - **verify every holder against the vendor model, not only the simplified one:** `tm.copy` the vendor bodies, place them at each instance's pose, intersect, and sweep a few mm along the seating axis. Where an original reference part exists, align their native frames and compare at the same pose: equal overlap means an inherited fit, more means a rebuild regression. Take pilot depths and horn positions from the vendor model too;
  - to make a purchased-part model more accurate, append features in its timeline rather than editing old ones, and keep the face or edge a joint was built on (for example a horn's outer circle) untouched, so the joints don't move.
- **Check the mechanism before adding a requested feature, and say what it can and can't do.** For a rotating jaw, compute how its contact moves toward the hinge as it opens and which object sizes each contact can reach. A pair of grooves aligns where their seat points have the same radius from the hinge; compute that size before moving either groove.
  - Show the usable object range with a demo body over the closing range against the whole assembly. Neighbouring parts may set the size and length limits.
- **Read a requested geometry for its function and material use.** A wall described as running diagonally from a corner to a contact point at a support-free angle is a strut: its down-facing side is the printable diagonal, the space under it stays open, and the material behind it reinforces the neighbours. It is not a solid fill under the diagonal. When asked to restructure a feature, aim to reduce material without losing its function, and say what each region does.
- **Retention methods the user rejects:** straps (inconsistent) and adhesive pads (too permanent).
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
- **Rigid clamp faces must be truly parallel at the closing pose.** Measure the gap at several points. A hinge axis tilted to the clamp face gives a gap that varies along the face. A rubber layer hides it, so re-check whenever a compliant layer is removed.
- **Trace every screw path end to end:** head seat → clearance → the material it threads into, with the engagement length, using the screw length the user actually has. Store it as a parameter, with the engagement as a derived parameter (length − clamped stack − gaps), so a different screw shows up at once.
  - A clearance bore through a locating boss into an empty hole fastens nothing.
  - Give the screw a pilot in the part it threads into (see the `fusion-print` skill for pilot sizes), blind with a skin if something lies beyond.
  - **Threading into a purchased part:** take the hole positions, depths and the faces around them from the vendor model, mapped into the assembly, not from the simplified model.
    - Centre each seat on a real pilot axis, and put the part's face at the pilot on the case face (pad it if it stands back).
    - For a tapped horn: printed stack = screw length − horn plate thickness.
  - **Model every screw in the functional assembly (user rule):**
    - Use one parametric component per screw type (head and shank from user parameters) and one instance per hole.
    - Give each instance a rigid as-built joint to the part it clamps; horn centre screws go to their servo.
    - Find the seats from the as-built geometry: each step from a clearance bore to a counterbore along a hole axis is a head seat.
    - At rest a screw may touch only the material it threads into, an overlap equal to its thread engagement. Anything else is an error.
    - Sweep every joint with the screws present.
- **Explain every accepted interference baseline.** Compare each holder's clamped span at the fastener spots with the real part; a recorded overlap alone does not establish fit.

## Structural and shape checks

- **"Don't compromise design intent" means analyze, not just preserve (user rule).** Intent is the function, not the reference geometry. On any part touched, actively look for weak points:
  - Trace the primary load (e.g. servo stall torque) from where it enters to where it leaves.
  - Find the smallest section, especially overlaps between features and sharp steps.
  - Estimate the stress with rough numbers: σ = M·c/I under the limiting load (servo stall torque, a hand force), with I from a section sampled by `pointContainment`.
  - Rank stress raisers by that nominal stress before adding fillets. Sharp corners on sections at a few MPa don't need them. The usual hot spots are strain-limited flexures (latches, springs) and thin walls around fasteners that carry torque.
  - Reinforce with webs and 45° gussets where clearance sweeps allow.
  - Raise these issues unprompted rather than waiting for the user to spot them.
- **Size material to the loads (user: "thickness designed for load bearing").** Compute the actuator-limited loads (servo stall torque over its lever, plus what the next joints can push), then the bending moment along the part. Compare I and W section by section with the accepted reference. When stresses are tiny (≈1 MPa), stiffness and torsion size the part, not strength: keep I near the reference and check twist where an off-centre or skewed load acts. For printable material removal and void rules, use the `fusion-print` skill.
- **No functionless crevices or peaks (user rule).** Small steps, ledges, notches and grooves between features, and slivers, knife edges and stubs left where features overlap, add complexity. They make the part harder to modify and weaker. Simplify the geometry rather than decorating it:
  - Make nearly coplanar faces flush, preferably at the source: drive both features' sketch dimensions from one shared user parameter. A 0.05–0.25 mm mismatch between features that should meet is enough to leave a visible step.
  - When changing a dimension, first search every model parameter's expression for the old one. Features that copied it will otherwise keep the old value and leave a ledge; move them all to one user parameter.
  - Trim peaks, stubs and wall corners back to the neighbouring envelope plane with a cut whose sketch is driven by that plane's parameters. Split Body at a plane offset 0 from a face also works, but is less robust.
  - Fill gaps between adjacent features with one extrude, bounded by the neighbouring planes.
  - Replace a staircase of faces (a stepped approximation of a slope) with one plane through the step tops. If a later cut shapes the region, insert the fill before that cut.
  - Prefer sketch edits to direct-edit features. A Replace Face whose target is a face made by another direct edit loses its reference on any upstream recompute and doesn't recover when the value is restored. One that targets a regular feature's face restores, but warns while some upstream parameters are flexed. Move a sketch vertex onto the face's line, or widen the neighbouring feature's sketch, instead.
  - Use fillets only for real stress concentrations on load paths (rank them as above). No blanket of edge-selected fillets on every inside corner; those also break when parameters change.
  - Keep every functional step: datum, seat and locating faces, clearances, servo pockets, holes, teardrops, bridge steps, bed chamfers, lead-ins.
  - **Before removing a peak, check whether it touches a purchased part.** If its removal lowers the interference with a servo, it is part of a press-fit or seat: keep it. A sliver inside a clearance cut is a remnant: remove it.
  - Changing a face that a moving part passes needs a sweep, even if the move is tiny. Keep sloped edges on their original line when raising a top.
  - Give added clearance around functional contact points (e.g. a pinch point) the same treatment: clear the geometry around them.

## Motion checks

- **Verify motion after any change near moving parts** (and after adding material anywhere): sweep each affected joint through its limits (`analyzeInterference`, `measureMinimumDistance`). Treat under about 1 mm between printed parts that must remain separate throughout motion as too tight; intentional mating or sliding faces use the fit clearances in the `fusion-print` skill.
  - Sweeping one joint alone from the as-built pose produces whole-arm self-collisions near the limits that don't depend on recent edits. Judge per pair against the same pose in the earlier version, or against recorded baselines.
  - Rolling the timeline marker back resets as-built joint values, so set the pose after moving the marker. A pose set before reads as zero interference.
  - When a rollback isn't practical, intersect the interference body with boxes around the new features to measure how much of it is new. For added material, sweep a TemporaryBRep box around just the addition, extended along the part's install path, against every other body. Exclude parts that move with it, such as the part it holds.
