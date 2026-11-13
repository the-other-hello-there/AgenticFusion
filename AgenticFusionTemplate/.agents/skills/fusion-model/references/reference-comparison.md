# Reference-driven geometry and presentation

Read only for photo/CAD-reference matching, a surface/insertion defect, or delivery views. Keep reference identity, project transforms, thresholds and target names in `Project/`; do not import a previous design's landmarks, dimensions or acceptance exceptions. Use the [verification procedure](verification.md) for saved-revision provenance and optional evidence gating.

## Photos and visible shape

Record the specific mismatch in a matching view before editing the controlling geometry. Preserve the original source image separately from renders and overlays. Calibrate the camera first using multiple well-distributed landmarks and silhouette refinement; record residuals, image dimensions, projection type and crop. Fusion's perspective angle is vertical field of view; verify the installed camera API. Sparse landmarks, a different physical pose or incorrect field of view can make an accurate shape look wrong.

Compare rendered masks with the source in the same view. Useful diagnostics include intersection-over-union, bidirectional boundary distances, landmark error and localized overlays; report both region metrics and worst-feature locations. Choose thresholds from the actual task. Lighting-sensitive paint segmentation needs local contrast: a shaded light material may be darker than a lit dark one. Retain uncertain segmentation/occlusion as unknown. Unrolled masks do not verify the corresponding 3D pose. Painter-depth sorting is not a true z-buffer; check visibility before fitting a hidden region.

Parameterize camera/mask/metric code as project tools rather than copying a whole reference-specific scanner. NumPy, SciPy, OpenCV, Shapely and plotting packages are optional dependencies for such authored analyses, not template startup requirements. Use an isolated environment if needed and record the method/units. A generic example script's import success is not a successful visual comparison.

## CAD and mesh comparisons

Record mesh units explicitly; STL has no reliable unit field. Never infer scale from an expected part size or coordinate magnitude. Establish the source-to-model rigid transform and verify it using independent datums. Measure both directions (reference to candidate and candidate to reference), with area-informed samples, percentile/worst deviations and the affected face/region. A nearest-normal sign is local, not a reliable global inside/outside test.

The shared [measurement helpers](../scripts/fusion_helpers.py) provide an all-triangle nearest-distance calculation for a bounded sample budget, avoiding a fixed nearest-centroid shortlist that can miss a large, nearby triangle. Samples describe a tessellated surface at declared resolution; they do not prove continuous CAD equivalence. For larger meshes, use an acceleration structure with a valid distance bound, or label the approximation and its coverage. Compare pre/post-flex states as well as nominal shape.

## Inserts, pocket floors and closed skins

Before detailed insert construction, establish a feasible insertion path with the other pieces already installed. A straight push is a zero-rotation screw path. For a rigid screw path, rotate points about a declared axis with Rodrigues' formula and add the specified travel along that axis; sample endpoints and intermediate positions at a recorded angular/linear resolution. Check insert-to-host and insert-to-insert pairs in one coordinate frame. Restore any moved geometry/poses in `finally`; temporary copies can measure without becoming production bodies. This checks sampled geometry, not friction, snap force or hand assembly.

Minimum clearance and intersection volume can miss an absent pocket floor. Cast ordered rays from the insert back toward the host and measure the gap to the first intended host surface. Filter by body/occurrence, sort hits by distance and record missing hits explicitly. Where point containment is suspect near a pocket, cross-check with non-axial ray parity and exact sections; do not treat a failed Boolean cut as evidence of empty space.

For multi-part exterior skins, cast from an independent reference surface toward the expected body and record first-hit depth, body identity and intentional seams/openings. Cluster sampled gaps to locate defects; report sampling resolution, coverage and occluded regions. Neither no sampled gaps nor coarse mesh-node coverage proves a closed shell. Mesh nodes on planar faces may exist only at edges, so missing interior samples do not imply missing material.

## Reproducible views and materials

Apply requested appearances and layout visibility in the reproducible build/presentation stage and checkpoint, rather than only in an ad hoc display script. Appearance changes may recompute geometry and reset uncaptured joint poses: apply appearance first, then solve poses and capture views. Verify actual colour/material properties and effective face/body/occurrence overrides, including hidden ancestors; a name prefix or visible-body count is insufficient. Appearance does not assign slicer filament.

Appearance lookup may return null or raise in a particular client/build; handle both. Names may be nonunique according to [Autodesk's lookup contract](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Appearances_itemByName.htm). Resolve the intended appearance and verify readback instead of generalizing one observed failure.

Use temporary `customGraphicsGroups` with BRep copies for explanatory cutaways; they are display objects, not production solids or fit evidence. Snapshot camera, visibility and opacity first, then delete graphics and restore every property in `finally`, even if a render/report fails. Identify a reported defect by part, side, view and artifact path. Rehearse the [cold-start checkpoint](../../application-session/references/lifecycle.md) so either agent can reproduce the last verified visible state.
