# Printed sizes and fits

**Strength and minimum sizes**
- **Walls:** at least 0.9 mm (2 line widths). Perimeters give most of the strength, so thicken walls on strong parts.
- **Features and pins:** at least 1.8 mm (4 line widths). Use store-bought pins in modeled holes for anything functional; thin printed pins (hinges, dowels) don't carry structure (user rule).
- **Holes:** at least Ø2 mm. For tight tolerance, undersize the hole and drill it after printing.
- **Small holes are acceptable as is (user rule)** when meant for self-tapping, or when short enough to drill or carve out easily. Even if poorly resolved, they still mark the center for drilling.

**Fits and threads**
- **Intentional mating or sliding fits between printed parts:** about 0.2 mm loose, 0.1 mm tight. Keep it a parameter. For parts that must remain separate throughout motion, use the about 1 mm running clearance in `Agentic-Fusion.md`.
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
  - **Grooves printed open toward the bed:** the neck is narrowed by elephant's foot (chamfer it; see [overhangs-and-bed.md](overhangs-and-bed.md) for bed contact), and the roof is a bridge that sags into the fit (user practice):
    - support the roof;
    - cut windows through it between short roof "teeth". This roughly halves the area to support and lets the supports be pulled out through the windows;
    - this costs nothing where the roof isn't a bearing face (dovetail flanks bear). Check that the lips outboard of the groove stay attached through the teeth.
- **Modeled threads:** only M5 / UNC #10 and larger, and never in horizontal holes.
- **Holes for post-processed threads** (starting points; verify with calipers):
  - tapped: 90% of the major diameter;
  - self-tapping screw: about 85% of the major diameter, between the screw's core and major diameter, so the screw cuts its own thread (user). 96% left only 0.04 mm per side;
  - heat-set insert: 98% of the insert's outer diameter (reference only; the user rule in [mechanisms-and-fasteners.md](mechanisms-and-fasteners.md) prohibits inserts).
