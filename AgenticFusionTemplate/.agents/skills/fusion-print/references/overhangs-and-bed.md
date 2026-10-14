# Overhangs, holes, bed contact, and support

**Overhangs and bridges**
- **Overhangs:** record the slicer's support threshold and angle convention in `Project.md`. Set `dfm_ovh_ang` to a slope from horizontal beyond that threshold by the project's chosen margin, and design unsupported down-facing faces to meet it. The project target may override Hydra's 50° from vertical. Teardrop flanks keep their own rule (Holes).
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

**Support policy (user rule)**
- Support is often unavoidable. Reduce it only where the change doesn't affect design intent at all.
- A gusset or fill under an overhang is allowed only if all of these hold:
  - the space below is empty at rest in every assembled instance;
  - it stays empty through single-joint sweeps of every joint to its limits;
  - it isn't a functional void (cable path, servo pocket, relief, window, tab pocket);
  - it isn't a gripping or ergonomic surface;
  - it stays out of camera fields of view and insertion paths.
- Faces within about 5° of the overhang limit aren't worth reshaping.
