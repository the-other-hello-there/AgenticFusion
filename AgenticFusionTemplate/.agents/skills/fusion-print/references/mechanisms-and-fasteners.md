# Printed mechanisms, fasteners, and symmetry

**Printed mechanisms**
- Leaf-spring strain ε ≈ 1.5·t·δ/L². Keep it at or below about 1.5% for PETG, and lower for PLA.
- **Flexure roots (latches, cantilever snaps):** a root fillet shortens the free length. In a crotch of angle θ the tangent point moves out by r/tan(θ/2), so a large fillet in a shallow crotch can double the strain and multiply the deflection force. Compute strain from the real thickness profile (integrate M²/EI), not the formula alone.
  - Keep root fillets small (about 1 mm), or use a **filleted relief hole or undercut** that moves the root back and rounds it at the same time (user recommendation, especially for thicker flexures).
  - Check the relief's wall to neighbouring cavities.
- **Spring tongues in a bed-side wall:** keep the tongue flush with the bed face.
  - Thin it from the non-bed side, and raise the bump by the same amount. Stiffness, strain and preload stay the same.
  - Check that the outward deflection envelope (about bump height plus tolerance outside the wall) stays clear through all motion.

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
