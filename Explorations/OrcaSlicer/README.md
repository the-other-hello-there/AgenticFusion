# OrcaSlicer MCP feasibility exploration

Assessment date: 2026-10-28. Branch: `explore/orcaslicer-mcp`, based on the self-benchmarking baseline `ba73f74`.

## Recommendation

OrcaSlicer is now an **optional integration in the same project folder**, retaining one `Project.md` and one physical skill tree for Codex and Claude Code. The shared [orca-slice skill](../../AgenticFusionTemplate/.agents/skills/orca-slice/SKILL.md) starts an installed OrcaMCP build and its embedded server. [FDM-Slicing.md](../../AgenticFusionTemplate/FDM-Slicing.md) holds slicing rules/preferences. Normal Fusion startup remains independent of the slicer.

A separate MCP server process does not require a separate agent folder. Use a separate folder when slicing is an independent job, uses third-party models without a Fusion design, or needs an incompatible slicer build/profile set. For a Fusion-to-print workflow, two folders would introduce another context handoff and competing copies of design intent.

This folder retains backend research, an environment inventory, and a setup compatibility check. The shipped helper can register Orca for both agents on request; it does not install a slicer or implement another MCP server. End-to-end slicing remains unverified. The user selected OrcaMCP with no Snapmaker dependency for this experiment.

## Available integration routes

| Route | Evidence and capabilities | Fit for this repository |
| --- | --- | --- |
| Stock OrcaSlicer CLI with a small MCP adapter | Upstream documents headless model loading, transformations, profile loading, slicing, and exports. The adapter would still need implementation. [CLI documentation](https://github.com/OrcaSlicer/OrcaSlicer/wiki/cli_mode) | Suitable for reproducible file-based slicing without adopting a fork. It does not establish control of an already-open GUI session. Pin the executable and profiles, and verify flags against that version's help. |
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
| `Test-OrcaEnvironment.ps1` | Found Snapmaker Orca `2.3.1` and Bambu Studio in standard install locations. | Neither finding establishes stock OrcaSlicer or MCP support. Portable installs elsewhere require `-OrcaPath`. |
| Default loopback ports `27182`, `13618`, `13619`, `13130` | Not reachable from the probe environment at assessment time. | Applications may be closed, ports changed, or networking restricted. TCP reachability alone would not verify MCP. |
| Live Fusion-to-Orca export, slicing, and agent restart | Not run. | Requires a selected MCP-capable build, a verified printer/nozzle/material profile, and disposable documents. |

Run from the repository root in Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Benchmarking/Benchmark.ps1 -SelfTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-CombinedSetup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-OrcaEnvironment.ps1
py -3 Benchmarking/Test-OrcaSlicer.py
# Include an installation outside the standard locations:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-OrcaEnvironment.ps1 -OrcaPath 'D:\Tools\OrcaSlicer\orca-slicer.exe'
```

The inventory reads executable metadata and connects to four loopback TCP ports. It does not execute the binaries, inspect printer credentials, or send application commands. Its JSON output can be redirected into this folder's ignored `.local/` directory after creating that directory. The combined setup check uses disposable copies there and deletes only its own GUID-named run folder.

## Integration shape

1. Keep the existing Fusion endpoint, launchers, shared modeling/printing/repair skills, completion hooks, and benchmark runner. The Orca helper explicitly configures both clients under `orcaslicer`; Fusion-only startup does not wait for a slicer.
2. The shared `orca-slice` entrypoint routes to startup and workflow references. Keep reusable slicing procedures there, rules/preferences in `FDM-Slicing.md`, and verified project/job facts in `Project.md`. Validate the real backend with the live checks below before claiming print-workflow viability.
3. Retain Fusion as the parametric source. Apply modeling changes through its existing parameters, sketches, and logical timeline position. Slicer transformations and settings belong to a recorded print setup; moving an exported mesh does not update the Fusion design.
4. Keep server installs, package caches, application profiles, tokens, and generated agent runtime data outside the distributable folder. Record versions and selected profile identifiers without copying a user's entire application configuration into the template.

The [startup helper](../../AgenticFusionTemplate/.agents/skills/orca-slice/scripts/start_orca.py) replaces the old static examples with one configuration path for both agents. `--setup-only` configures without starting an app or asserting connectivity; `--configure` verifies the running MCP before configuring. It preserves unrelated entries and explicit disables, and restores original configuration bytes on a write failure. Client project trust still applies. Do not point it at the MaxEllis REST port.

For a CLI adapter, expose bounded operations such as inspect version/profile, slice an approved input with explicit profiles, and read a completed result. Pass arguments directly to the process, retain exit code/logs, enforce a timeout, and inspect the output before reporting success. Resolve inherited printer, process, and filament settings rather than assuming a preset filename fully defines them. Start with one adapter shared by both clients.

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

The next live experiment is to install the selected OrcaMCP Windows build, confirm the target printer/nozzle/material, verify its MCP tools in both clients, and run O1-O4. Snapmaker-specific compatibility is not required. Until then, the configuration architecture is supported by local checks; backend and print-workflow viability remain open.
