## Analysis setup
- **Parameters:** every fix is driven by `dfm_` user parameters. Create them if missing:
  - `dfm_td_ang` (45°, teardrop flank angle from vertical, at most 50°);
  - `dfm_layer` (0.2 mm until the user gives one);
  - `dfm_base_ch` (0.3 mm);
  - `dfm_bridge_max` (10 mm);
  - `dfm_ovh_ang` (35°, minimum slope from horizontal of unsupported down-facing faces; see [overhangs-and-bed.md](overhangs-and-bed.md)).
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
