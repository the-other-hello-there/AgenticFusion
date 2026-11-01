# OrcaSlicer MCP feasibility exploration

Initial assessment: 2026-10-28. Discovery/choice update: 2026-10-31. Branch: `explore/orcaslicer-mcp`, based on the self-benchmarking baseline `ba73f74`.

## Recommendation

Orca-family slicing is an **optional integration in the same project folder**, retaining one `Project.md` and one physical skill tree for Codex and Claude Code. The shared [orca-slice skill](../../AgenticFusionTemplate/.agents/skills/orca-slice/SKILL.md) discovers installed apps and asks which to use for each new slicing request, then handles startup/model loading and available CLI/GUI/MCP operations. Stock OrcaSlicer, Snapmaker Orca and Windows Store packages no longer require a special MCP build. [FDM-Slicing.md](../../AgenticFusionTemplate/FDM-Slicing.md) holds slicing rules/preferences. Normal Fusion startup remains independent of the slicer.

A separate MCP server process does not require a separate agent folder. Use a separate folder when slicing is an independent job, uses third-party models without a Fusion design, or needs an incompatible slicer build/profile set. For a Fusion-to-print workflow, two folders would introduce another context handoff and competing copies of design intent.

This folder retains backend research, an environment inventory, and a setup compatibility check. The user's current preference is to choose among installed slicers on each new slicing request. [slicer.py](../../AgenticFusionTemplate/.agents/skills/orca-slice/scripts/slicer.py) provides version-independent discovery/opening and capability-checked core CLI slicing; `start_orca.py` retains the optional OrcaMCP setup route. Neither installs software or implements a new MCP server. Discovery has been checked on this workstation; real GUI activation/import and end-to-end slicing remain unverified.

## Available integration routes

| Route | Evidence and capabilities | Fit for this repository |
| --- | --- | --- |
| Stock/vendor Orca CLI and GUI | Upstream documents headless model loading, transformations, profile loading, slicing, and exports. The shipped helper checks selected-build CLI help, runs a local slice, verifies exported toolpaths and opens results. [CLI documentation](https://github.com/OrcaSlicer/OrcaSlicer/wiki/cli_mode) | Default file-based route when supported. No MCP adapter required. GUI-only builds need available GUI automation; launching does not establish control of an already-open scene. |
| Windows Store/package activation | Current-user package manifests and Start apps supply AUMIDs; Windows file activation opens the selected app without default associations or WindowsApps permission changes. [Microsoft identity documentation](https://learn.microsoft.com/en-us/windows/configuration/store/find-aumid), [file activation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iapplicationactivationmanager-activateforfile) | Shipped inventory and activation helper. An accessible manifest executable allows CLI probing. A package with no accessible CLI/file contract remains a reported automation limit. |
| `okets/OrcaMCP` community fork | Documents direct Streamable HTTP at `http://127.0.0.1:13618/mcp`, plus a Python stdio bridge for app startup, waiting, and instance selection. Its tools cover the plate, settings, slicing, and printer operations. [Fork documentation](https://github.com/okets/OrcaMCP/tree/mcp) | First candidate for an HTTP experiment matching the existing Fusion connection pattern. Direct HTTP requires the app to be running and selects one port/window. |
| `MaxEllis/orcaslicer-mcp` and matching slicer fork | A local stdio MCP server connects to a token-authenticated remote API, normally on port `13130`. The documented tools include settings, slices, estimates, and comparisons. The API port is REST, not a direct MCP URL. [Server documentation](https://github.com/MaxEllis/orcaslicer-mcp) | Candidate when detailed slice analysis matters. Requires the matching fork, Python packaging/runtime, and local token handling. Do not put its token in committed example configuration. |
| Proposed upstream native MCP | Upstream PR #12667 is still marked draft in the reviewed page; its proposal uses port `13619`. [Upstream PR](https://github.com/OrcaSlicer/OrcaSlicer/pull/12667), [design discussion](https://github.com/OrcaSlicer/OrcaSlicer/discussions/12668) | Track upstream progress. This proposal does not establish that an installed stock release exposes MCP. |

The OrcaMCP releases page lists a Windows x64 installer, including `v2.5.0.13-dev` at assessment time. A listing is not a verified installation or compatibility result. [OrcaMCP releases](https://github.com/okets/OrcaMCP/releases/tag/v2.5.0.13-dev)

The MaxEllis fork separately lists `v2.4.2-mcp.13` and notes the corresponding server's plate-tool support. Match the server and application versions before comparing results. [Fork release](https://github.com/MaxEllis/OrcaSlicer/releases/tag/v2.4.2-mcp.13)

## Local evidence

Checks performed on the assessment workstation:

| Check | Result | Limit |
| --- | --- | --- |
| Baseline benchmark runner `-SelfTest` | Passed B1-B7 parsing, both fresh-copy setup checks, quoted batch launching, and temporary result append checks. | This checks the runner; it does not execute the Fusion modeling prompts or rate an agent. |
| `Test-CombinedSetup.ps1` | Uses the shipped setup helper in two fresh copies, then switches both launchers. Checks both server entries, `Project.md`, and edited `FDM-Slicing.md` preferences. | It does not test agent trust or a real slicer. |
| Shipped `slicer.py list` (2026-10-31) | Found Windows Store OrcaSlicer `2.4.3.0`, Snapmaker Orca `2.3.1`, and Bambu Studio; no inventory warnings. | Read-only discovery only; no app was launched. Neither CLI nor MCP is inferred from metadata. Unregistered portable installs require `--executable`/`-OrcaPath`. |
| `Test-SlicerDiscovery.py` | Checks choice gates, source merging, distinct installs, Store identities/fallbacks, quoted file arguments, capability gates, slice artifacts/failures, and compilation of shipped activation interop. | Mock apps/slices, plus native interop compilation. No real GUI activation or slicing. |
| Default loopback ports `27182`, `13618`, `13619`, `13130` | Not reachable from the probe environment at assessment time. | Applications may be closed, ports changed, or networking restricted. TCP reachability alone would not verify MCP. |
| Live Fusion-to-Orca export, slicing, and agent restart | Not run. | Requires a chosen slicer, a verified printer/nozzle/material profile, and disposable documents. MCP is optional. |

Run from the repository root in Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Benchmarking/Benchmark.ps1 -SelfTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-CombinedSetup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-OrcaEnvironment.ps1
py -3 Benchmarking/Test-OrcaSlicer.py
py -3 Benchmarking/Test-SlicerDiscovery.py
# Include an installation outside the standard locations:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-OrcaEnvironment.ps1 -OrcaPath 'D:\Tools\OrcaSlicer\orca-slicer.exe'
```

The environment inventory uses the shipped slicer discovery (Python 3.11+) and probes four loopback TCP ports. It does not execute slicer binaries, inspect printer credentials, or send application commands. Its JSON output can be redirected into this folder's ignored `.local/` directory after creating that directory. The combined setup check uses disposable copies there and deletes only its own GUID-named run folder.

## Integration shape

1. Keep the existing Fusion endpoint, launchers, shared modeling/printing/repair skills, completion hooks, and benchmark runner. Discovery/CLI/GUI work without registering another MCP server. The optional OrcaMCP helper configures both clients under `orcaslicer`; Fusion-only startup does not wait for a slicer.
2. The shared `orca-slice` entrypoint routes to startup and workflow references. Keep reusable slicing procedures there, rules/preferences in `FDM-Slicing.md`, and verified project/job facts in `Project.md`. Validate the real backend with the live checks below before claiming print-workflow viability.
3. Retain Fusion as the parametric source. Apply modeling changes through its existing parameters, sketches, and logical timeline position. Slicer transformations and settings belong to a recorded print setup; moving an exported mesh does not update the Fusion design.
4. Keep server installs, package caches, application profiles, tokens, and generated agent runtime data outside the distributable folder. Record versions and selected profile identifiers without copying a user's entire application configuration into the template.

The [startup helper](../../AgenticFusionTemplate/.agents/skills/orca-slice/scripts/start_orca.py) replaces the old static examples with one configuration path for both agents. `--setup-only` configures without starting an app or asserting connectivity; `--configure` verifies the running MCP before configuring. It preserves unrelated entries and explicit disables, and restores original configuration bytes on a write failure. Client project trust still applies. Do not point it at the MaxEllis REST port.

The CLI helper runs the chosen executable with an argument array, explicit profile files or a verified prepared 3MF, and a new output path. It records logs/hashes, verifies nonempty G-code in the result, and opens that result in the same app. Preview, warnings and estimates still need review. Resolve inherited printer, process, and filament settings rather than assuming a preset filename fully defines them.

## Project handoff contract

Add a concise print-state entry to `Project.md`, with a linked manifest for details:

| Record | Purpose |
| --- | --- |
| Fusion document identifier, saved version, component/body selection, and relevant parameter values | Tie the exported part to verified design intent. |
| Export path, SHA-256, export units, tessellation settings, and bounding dimensions in mm | Detect stale geometry or scaling errors. Explicitly record the units for STL. |
| Slicer build and server version, project/plate identifier, printer/nozzle, material, and resolved profile versions/hashes | Make a slice reproducible and distinguish it from another window or plate. |
| Object transforms, layer height, walls, infill, supports, and intended bed orientation | Preserve the decisions that affect strength, fit, and printability. |
| Saved 3MF/G-code paths and hashes, estimates, warnings, and unresolved review items | Give the next agent verifiable output and identify assumptions. |

Re-export and invalidate previous slice results after a Fusion parameter change. Check imported dimensions before slicing, and never infer printer compatibility merely because a slice completed. Initial experiments should stop at local file export; uploading or operating a physical printer is outside this exploration.

## Live experiments and decision gates

Use the same disposable B2/B5 bracket and the same printer/nozzle/material across comparisons. Run the existing B1-B7 suite for both agents with Fusion alone, then repeat with the optional slicer connected. Record elapsed time, usage, quality, selected backend versions, and failures without manufacturing benchmark scores.

| Check | Task and acceptance evidence |
| --- | --- |
| O1: connections | In both agents, discover both servers and inspect their actual schemas. Verify MCP initialization and tool discovery; an open port or REST health response is insufficient. |
| O2: identity | Report the active Fusion document and Orca project/plate/profile without changing either. Confirm the correct instance and nozzle. |
| O3: export/import | Export the saved B5 bracket, record provenance, import a disposable copy, and verify millimeter dimensions and intended orientation. |
| O4: baseline slice | Slice using explicit profiles; verify completion, warnings, time/filament units, and actual saved output. Compare with the GUI. |
| O5: bounded iteration | Change one approved setting, compare results, restore the original, and verify that no global preset or Fusion geometry changed. |
| O6: stale state and recovery | Change the wall-rise parameter in Fusion, detect the old export, re-export and re-slice. Exercise unavailable-server, wrong-profile, and failed-slice cases; report failure without inventing estimates. |
| O7: agent handoff | Restart with the other agent. Recover the same design/print intent from `Project.md`, verify both live applications, and identify stale or unverified facts. |

Promote the optional shared-folder approach when both agents pass O1-O7 and retain B1-B7 behavior at an acceptable measured time/usage cost. Choose a separate slicing folder if live tests reveal incompatible application/profile requirements, conflicting project lifecycles, or an independently managed print queue. In that case, pass the versioned export manifest between folders and keep CAD intent authoritative in the Fusion project.

The next live experiment is to choose an installed slicer, confirm printer/nozzle/material and a disposable model, verify automatic opening/import, and run O2-O4 through its available CLI/GUI interface. Repeat for Snapmaker and the Store installation. O1 applies only if the chosen build exposes MCP. Until then, discovery and setup are supported by local checks; real GUI and print-workflow compatibility remain open.
