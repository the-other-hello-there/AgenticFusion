## Documents, components, parameters
- New documents may default to Part Design, which allows only one component. For multi-component work, set `design.designIntent = AssemblyDesignIntentType` right after `documents.add`.
- User parameters are document-wide, so they can drive internal components. Externally referenced components keep their own parameters.
- Features in a sub-component:
  - With native inputs (the component's own construction planes, sketches and bodies), build through `comp.sketches` / `comp.features` directly.
  - With proxy inputs, call `occ.activate()` first and pass `createForAssemblyContext(occ)` proxies, then `design.activateRootComponent()`. Otherwise you get "Failed to get owner occurrence transform".
- Fully constrain an assembly with a rigid joint (`JointGeometry.createByPoint` + `setAsRigidJointMotion()`) from each seed occurrence's origin to its parent's origin.
- **Cut/join features in an assembly hit other components' bodies** unless `participantBodies` is set (it silently adds features to those components). Always pass the part's own bodies, including after editing an existing cut; the same applies to `HoleFeatureInput.participantBodies`. See the `fusion-repair` skill if an edit added a hidden feature to another component.
- **Sub-assemblies:** create the parts at root, add instances with `sub.component.occurrences.addExistingComponent(comp, T)`, then delete the root originals. Don't use `moveToComponent` (it copies, and later copies fail with `Paste instance source occurrence context is lost`). A sub-component occurrence's transform can't be changed afterwards (`transform overrides can only be set on Occurrence proxy from root component`), so pass the final transform at creation.
  - Proxy bounding boxes read 0 until the next script runs.
- **Placing instances in a sub-assembly whose root occurrence is offset:** `addExistingComponent(comp, T)` can honour T's rotation but add a spurious translation that differs per component.
  - Verify the first instance of each component, by its world bounding box against a twin in an identity-placed copy, then compensate.
  - Compose transforms by multiplying `asArray()` values explicitly; don't rely on the order `Matrix3D.transformBy` uses.
  - A jointed occurrence's native `transform2` inside a sub-assembly can lag its solved pose. Place relative to the root proxy's `transform2`.
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

## Parameter design

Drive almost everything from a small set of intent-level parameters (user rule). Give an independent user parameter to a real design choice: cable diameter, wall thickness, clearance, groove angle or interface position. Derive dependent dimensions from those choices and shared datums; do not create a separate user parameter for every edge, copy or calculated offset.

Before adding a parameter, search for one with the same meaning; reuse or derive from it. Promote a hard-coded sketch dimension when a new feature needs to depend on it. Tie names and expressions to function, and inspect all dependents before changing a shared driver. Use direct edits, Replace Face, Split + Remove, planes offset from faces and fills of incidental geometry only very cautiously.

Expressions support `sin`/`cos`/`tan`/`sqrt`/`^`; unitless parameters use unit `''`. Derive tangent points and other dependent geometry as expressions too.

