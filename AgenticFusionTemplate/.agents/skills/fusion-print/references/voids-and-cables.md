# Internal voids and cable clips

**Internal voids and cable clips**
- **No closed internal voids (user rule).** Support printed inside one can't be removed, and since the slicer already prints solid regions with sparse infill, an enclosed void barely saves material. Check `body.shells.count == 1` on every printed body.
- **Lighten with open pockets instead:** the pocket isn't printed at all, so the saving is real, and nothing is trapped. Choose the opening face by comparing candidates, built as temporary cuts on the same solid, on stiffness, torsion, stress, bed contact and function.
  - For a beam loaded across its depth (bed side to top), compare side pockets that leave an I-section. They can keep both flanges, full bed contact, and the functional top face intact.
  - Bed-side pockets lose the bed flange and bed contact. Top pockets break the top face.
  - Put the web on any line of through-holes, so the holes run inside the web rather than notching a pocket.
  - Gable the pocket roof at `dfm_ovh_ang` across its width so it needs no support. Leave the ridge sharp: a ridge round leaves a strip flatter than the threshold (1.2 mm wide at r 1).
  - Round the other pocket edges, especially those across the bending direction (pocket ends). Add the bed-edge chamfer to the rim.
  - Where the outer bottom rises off the bed (a 35° back), end the bed opening with a full-thickness wall, then follow the rising face at constant skin thickness. Letting the offset skin plane run out to the bed leaves a feather edge.
  - Keep load-introduction zones (roots, lugs, load pads) solid; they act as end diaphragms.
  - An open section can be much weaker in torsion; a bed-side opening also loses the bed flange. Re-check bending section properties and absolute twist against the reference and the functional allowance.
- **Snap-in cable channel cut into the bed face:** a keyhole profile, all derived from the cable diameter D:
  - a mouth of D minus the snap squeeze (0.5 mm), with a **rounded inlet** (user: makes the cable easier to push in) built into the profile as arcs tangent to the bed face and the mouth walls. The inlet replaces the bed chamfer there; it is a bed-side curl-up of about the radius;
  - a ~0.8 mm lip, 45° widening, and a cavity of D + 0.2 under a 45° pointed roof;
  - bend radius ≥ 2·D, with the bend ending below the exit face, so no 0.05 mm sliver is left.

  Check the free cable route to it with Ø D cylinders against the neighbouring bodies.
