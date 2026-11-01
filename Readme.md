# Agentic Fusion

A portable Windows folder for Autodesk Fusion's local MCP server with **Claude Code or Codex**. Copy [`AgenticFusionTemplate/`](AgenticFusionTemplate/) for each project; either launcher prepares shared files and starts Fusion and the chosen agent.

## Install Fusion and an agent

1. Install the [Fusion desktop application](https://help.autodesk.com/view/fusion360/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FHow-to-download-Fusion-360.html) and sign in. The local MCP server runs in the desktop application.
2. Install one or both agents:
   - **Claude Code:** use Anthropic's [Windows setup guide](https://code.claude.com/docs/en/setup). In PowerShell: `irm https://claude.ai/install.ps1 | iex`. Open a new terminal and check `claude --version`.
   - **Codex CLI:** use OpenAI's [Codex CLI guide](https://learn.chatgpt.com/docs/codex/cli) and [Windows installer](https://learn.chatgpt.com/docs/config-file/environment-variables). In PowerShell: `irm https://chatgpt.com/codex/install.ps1 | iex`. Open a new terminal and check `codex --version`.
3. Sign in when the chosen agent first opens. Its credentials stay in its normal user profile, outside the project template.

## Enable Fusion MCP

In Fusion, open **Preferences > General > API** and enable **Fusion MCP Server (runs locally on this device)**. Note the port; its default is **27182**. Open the design you want to inspect or edit. See [Autodesk's connection instructions](https://help.autodesk.com/view/fusion360/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html).

Both project configurations target `http://127.0.0.1:27182/mcp`: Claude uses `.mcp.json`, and Codex uses `.codex/config.toml`. If Fusion displays another port, change `$McpPort` near the top of `Fusion-Claude.bat` in your project copy. This shared launcher then updates **both** project MCP entries when either batch file runs. Changing only a JSON or TOML URL will be undone by the next launcher run.

## Start a project

1. Copy the **inner** [`AgenticFusionTemplate/`](AgenticFusionTemplate/) folder anywhere and rename the copy for your project. Keep its supplied files, `.agents/`, and `.codex/` together; leave the repository `.git/` behind.
2. Run `Fusion-Claude.bat` or `Fusion-Codex.bat`. Either launcher creates missing `Project.md`, prepares both agents' MCP configurations, starts Fusion if needed, waits up to 120 seconds for its server, and opens the selected agent. Codex may ask you to trust the project before loading its MCP configuration.
3. In `Project.md`, keep the `Current state` section concise and record verified design intent, interfaces, parameters, document names, decisions, and open items. The two agent entry files direct their agents to read that section and the short shared Fusion guide.

Claude loads `.agents/` through `--plugin-dir`; Codex discovers the same physical skill files in `.agents/skills/`. Use the Claude launcher to load its plugin. Both agents load detailed references only when needed; `CLAUDE.md` does not auto-import all of `Project.md`.

Both agents play a short Windows tone when their main agent finishes a response. Claude's plugin and Codex's project hook call the same `.agents/scripts/task-complete.ps1`; no instruction text or model call is involved. Codex requires project trust and a one-time review of the hook through `/hooks` before it runs. Start either agent through its launcher from the project folder.

Drag an existing project folder onto either template launcher to copy missing files, including both launchers, without replacing context. In a copied folder, run `./Fusion-Claude.bat --setup-only` or `./Fusion-Codex.bat --setup-only` to prepare files without opening Fusion or an agent; both use the same setup routine.

Setup preserves an older copy's launcher and instruction files. To fix Claude's instruction-size overflow, remove `@Project.md` and `@Agentic-Fusion.md` from its `CLAUDE.md`, then bring over current guide and skill routing while preserving project-specific edits. Setup copies missing skills only. If `Project.md` is large, keep current facts there and index needed history in `Project-History/` per the shared cleanup rule.

The launcher warns above the 40,000-character `Project.md` target. For Claude, it detects legacy full-file imports and stops before their combined text exceeds the observed 150,000-character instruction limit. It never rewrites existing context.

### Optional slicer discovery and startup

The shared `orca-slice` skill discovers installed OrcaSlicer variants, including Snapmaker Orca and Windows Store packages, plus Bambu Studio. On each new slicing request, the agent asks which discovered app to use, prepares/slices headlessly when that build supports CLI, then automatically opens the completed result in that same app for required layer/toolpath preview. A slicer explicitly named in the request counts as the choice. No special MCP build is required. The helpers use Python 3.11+ and Windows PowerShell; ordinary Fusion startup remains independent of Python and any slicer.

From a project copy, ask either agent to slice a model, or inventory installations yourself:

```powershell
py -3 .agents/skills/orca-slice/scripts/slicer.py list
# Interactive terminal: choose a slicer, slice a verified prepared project headlessly,
# then open the sliced result for UI preview. The output path must be new.
py -3 .agents/skills/orca-slice/scripts/slicer.py slice --input 'Print Jobs\prepared.3mf' --embedded-profiles --plate 1 --output 'Print Jobs\job-sliced.3mf'
```

Discovery reads installation folders, PATH, registry, shortcuts and current-user Store/package registrations without launching slicers. For an unregistered portable installation, add `--executable 'D:\Tools\Orca\orca-slicer.exe'`, or set `ORCA_SLICER_PATH` on this machine. In agent shells, the agent runs `list`, asks you, then passes the chosen ID using `--select`. Store apps use their application identity and file activation rather than a guessed WindowsApps path or default file association.

Slicing prefers the selected build's verified CLI until preview. The core CLI helper records logs/hashes, verifies exported toolpaths, and only then opens results in the same app. Intermediate comparisons can use `--no-open`, followed by UI preview of the final result. If usable CLI or indispensable setup is unavailable headlessly, the agent explains that limitation before using the UI earlier. An embedded MCP server still runs inside a GUI app. Version-independent discovery is not a guarantee that every release has the same slicing APIs. See [startup](AgenticFusionTemplate/.agents/skills/orca-slice/references/startup.md) and [workflow](AgenticFusionTemplate/.agents/skills/orca-slice/references/workflow.md) for commands and optional OrcaMCP configuration. No software installation or printer operation is performed by these helpers.

Keep slicing rules and preferences in [`FDM-Slicing.md`](AgenticFusionTemplate/FDM-Slicing.md), read only for FDM work. Keep verified geometry, selected job profiles, export provenance, and slice results in `Project.md`. Setup copies missing files and preserves a project's existing slicing preferences.

The [slicing workflow, hierarchy and flowchart](AgenticFusionTemplate/.agents/skills/orca-slice/references/workflow.md) separates policy, job coordination, native settings, adaptive/smoothed layer height, support-interface materials, calibration and comparisons. Detailed procedures load on demand. Rules include directly stacked infill by toolpath geometry (gyroid does not qualify), user-declared-final gating for high infill and specific approval before a second support-interface material is applied. Researched sources and build-specific incompatibilities are linked from the relevant procedures.

UI preview permits background window control only while normal computer operation continues uninterrupted: no cursor movement, focus takeover, global typing/clicks or clipboard replacement. The current activation helper cannot guarantee that a slicer will not foreground itself. When compliant access is unavailable, retain the headless result and report the exact pending visual check rather than take over the desktop.

### Application housekeeping and resumable sessions

Both agents use one [application-session procedure](AgenticFusionTemplate/.agents/skills/application-session/SKILL.md) and one Windows helper. Close unused task documents/windows after checking ownership and saved state. At verified milestones and before exposed usage limits run low, save the actual Fusion document/Orca editable project and record ordered pending tasks plus a restart checkpoint in `Project.md`. Either agent can resume from that record; agent-specific memory is not required.

The Fusion launcher and ordinary slicer opening path register actual GUI PIDs/start times and start a hidden per-project deadline watcher. Runtime state stays in `%LOCALAPPDATA%\AgenticFusion\Sessions`, outside the migration package. Reattachment does not reset an application's clock. Prepare maintenance at 11.5 hours; at 12 hours stop new application work, save/verify and perform full cleanup while retaining live tasks, then ask whether the named apps can safely restart. After approval the helper requests a graceful close, relaunches the recorded application and requires PID/MCP/document/job verification before continuing. AI-agent processes and unrelated user software are excluded. `--setup-only` starts no watcher.

The [detailed lifecycle guide](AgenticFusionTemplate/.agents/skills/application-session/references/lifecycle.md) distinguishes exported files, verified saves, cleanup and restart readiness. The watcher can queue maintenance and show a non-modal notice while the agent is idle, but it cannot invent semantic saves/task summaries when the agent is unavailable or quota-exhausted. Pending approval, an active operation or an unverifiable save may exceed the 12-hour deadline; no application is force-killed. Account telemetry is used when exposed by the client; missing telemetry remains unknown and milestone checkpoints provide the fallback. This is a cooperative maintenance deadline, not a guaranteed unattended hard cutoff.

### Portable printers and slicing skills

The shared `printer-library` skill maintains [`Printers.json`](AgenticFusionTemplate/Printers.json): printer identity, known hardware limits, evidence, and optional embedded Orca machine/filament/process presets. JSON keeps these definitions easy to copy and paste while preserving native profile types and inheritance. The template starts with an empty library; use the skill to record actual printers from user-stated or verified information.

Copy the whole catalog to a new project, paste selected records into its `printers` array, or use the helper to merge them without silently replacing existing definitions:

```powershell
py -3 .agents/skills/printer-library/scripts/printer_library.py validate
py -3 .agents/skills/printer-library/scripts/printer_library.py export --id my-printer --output shared-printers.json
py -3 .agents/skills/printer-library/scripts/printer_library.py import --source shared-printers.json
```

`export-presets` also writes embedded presets as individual native JSON files. This catalog is agent context, not a slicer-native installer; review/import native presets through the slicer and verify declared system parents, firmware, nozzle and bed geometry. See the [format and migration reference](AgenticFusionTemplate/.agents/skills/printer-library/references/format.md) for the record template and full commands.

Use `fdm-calibrate` to plan and interpret measured printer/material calibration, and `slice-compare` to compare estimated time/material/quality tradeoffs while restoring the accepted baseline. Calibration evidence and job outcomes stay in `Project.md` or its indexed notes; reusable user preferences stay in `FDM-Slicing.md`. Both agents discover the same physical skill files.

### Check the connection

Inside the chosen agent, check `/mcp` for the `fusion` server. From a terminal in the project folder, `claude mcp list` or `codex mcp list` can also inspect configured servers. A safe first prompt is: “List the active Fusion document and its components without changing the design.” See the [Claude MCP guide](https://code.claude.com/docs/en/mcp) and [Codex MCP guide](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

If the server is disconnected, check that Fusion is running, its MCP option is enabled, a design is open, and the Fusion port matches `$McpPort`. If Fusion cannot be found automatically, start it yourself or set `$FusionPath` in `Fusion-Claude.bat` to its launcher path. If an agent executable is missing, reopen the terminal and check its version command. Codex project MCP settings load only after the project is trusted; if the server is absent from `codex mcp list`, check trust and restart Codex from the project folder.

## Project files

| File | Role |
| --- | --- |
| `Fusion-Claude.bat`, `Fusion-Codex.bat` | Shared first-run setup and Fusion startup; launch the chosen agent. |
| `Agentic-Fusion.md` | Short, always-read shared design priorities, routing, memory placement, and size rules. |
| `DfAM.md` | Optional protocol for a requested broad DfAM assessment; technical methods stay in the shared printing skill. |
| `FDM-Slicing.md` | Shared FDM slicing rules and user-stated preferences, loaded on demand. |
| `Printers.json` | Copyable printer definitions, evidence, and embedded native presets; initially empty. |
| `CLAUDE.md`, `AGENTS.md` | Small agent-specific startup and tool instructions. |
| `.mcp.json`, `settings.json` | Claude Code project MCP and agent settings. |
| `.codex/config.toml` | Codex project MCP connection. |
| `.agents/skills/fusion-model/` | Shared modeling skill with task-specific Fusion API, assembly, timeline, sketch, feature, and verification references. |
| `.agents/skills/fusion-print/` | Shared printing skill with references loaded by task: design rules, orientation, scan, and improvement. |
| `.agents/skills/fusion-repair/` | Shared repair skill with references loaded by failure type. |
| `.agents/skills/orca-slice/` | Shared slicer discovery/choice, desktop/Store opening, CLI slicing and optional OrcaMCP startup. |
| `.agents/skills/printer-library/` | Printer definition, validation, selective export/import, and native preset export. |
| `.agents/skills/fdm-calibrate/`, `.agents/skills/slice-compare/` | Measured calibration and controlled slicing comparison guidance. |
| `.agents/.claude-plugin/plugin.json` | Lets the Claude launcher load those same skill files as a local plugin. Codex discovers them in `.agents/skills/`. |
| `.agents/scripts/task-complete.ps1`, `.agents/hooks/hooks.json`, `.codex/hooks.json` | One completion tone with agent-specific Stop hook declarations. |
| `Project.md` | Created on first run for this design's verified context and decisions. |

Fusion designs remain in Fusion's documents. Do not put agent credentials or generated agent runtime folders into a project copy.

## Benchmarking

Run [Run-Benchmark.bat](Benchmarking/Run-Benchmark.bat) to benchmark a fresh, disposable copy of the inner template. The guide opens the chosen agent, walks through B1–B7, times each prompt, and asks before adding results to [Benchmarking.md](Benchmarking/Benchmarking.md). Close the agent window before finishing so the temporary local copy can be deleted. Use a disposable Fusion project too; deleting the local copy does not remove Fusion cloud documents.

## Maintenance and OrcaSlicer evidence

The inner folder is the runtime migration package. Its shared launcher owns the explicit file allowlist; `py -3 Benchmarking/Test-PortablePackage.py` checks that the package contains exactly those files, has no generated/account data, and keeps its links self-contained. Maintenance tests, research/assessment notes, scratch copies and backups belong outside the inner folder. On-demand skill instructions, reference procedures and record templates are runtime resources and remain included.

For an existing agent that needs the slicing instructions, relay:

```text
Apply and persist the following slicing instructions in this project. Keep one shared policy for Codex and Claude, a short coordinating skill, and on-demand procedures for settings, adaptive layer height and multimaterial interfaces. Include a decision flowchart; reuse existing printer-library, CAD printability, calibration and slice-comparison skills. Preserve verified design context and project-specific preferences.

WORKFLOW
- On each new slicing request, discover installed slicers, including ordinary OrcaSlicer, Snapmaker Orca and Windows Store installations, and ask which to use. Ask even with one result unless I already named an unambiguous installed slicer. Keep that choice through job follow-ups. Never silently substitute another slicer or require a special MCP build.
- Prepare and slice headlessly through the chosen build's verified CLI when supported, then automatically open the completed slice in that same app for required layer/toolpath UI preview. Keep intermediate comparisons headless. Explain any indispensable earlier UI setup or unavailable capability; never claim an ignored setting or uninspected preview succeeded.
- Slicer-window control is allowed only without interrupting normal computer use. Do not move my cursor, steal focus, send global keystrokes/clicks, overwrite my clipboard or block my input. Use APIs or non-disruptive background controls. If compliant access is unavailable, retain the artifacts and report the exact pending preview/setup action.

SLICING RULES
Depart from these defaults only for a specific conflict with verified design intent, and record the rule and reason. Software limitations must be reported rather than silently treated as exceptions. High infill still requires my explicit final-version designation, and a second support-interface material requires specific approval before application.

1. Use concentric exposed top and bottom surfaces for my radial-compression objective, unless design intent conflicts; do not claim a universal strength advantage.
2. Use a linear solid pattern on the layer immediately above each exposed bottom surface and immediately below each top surface. Keep exposed surfaces concentric; inspect local shells on stepped features too.
3. Keep sparse infill between 10% and 70%. Use low for fit tests, medium for reasonably structural tests, and high only when I explicitly designate the version final. Working bands are low 10-20%, medium greater than 20% through 40%, and high greater than 40% through 70%; these are implementation conventions, not measured strength ratings.
4. Prefer simple infill: lines stack directly above other lines at the same XY positions across layers, rather than forming laterally shifting ramps/overhangs. Verify actual toolpaths. Grid or aligned rectilinear can qualify; gyroid does not. Ordinary alternating rectilinear is not automatically equivalent. Use another pattern only when design intent justifies it, such as a need for more multidirectional infill behavior; the whole printed part remains anisotropic.
5. Reserve one nominal wall for intentional flexibility, normally TPU. Otherwise use at least two walls, Alternate extra wall and Embedding wall into infill where supported. Treat those last two as distinct features and report missing capabilities.
6. For geometry thinner than twice the nozzle diameter, enable Detect thin walls with Classic. With Arachne, use its thin-feature mechanism because the separate checkbox may be disabled. Verify the feature survives.
7. Allow infill combination only for verified directly stacked patterns; check combined extrusion height and peak flow against actual nozzle/material limits.
8. Enable independent support layer height when using supports. Verify effective behavior; report conflicts with towers or support styles in the selected build.
9. Prefer tree supports for small/local features and normal supports for large overhang areas. Verify contact, removal and critical surfaces.
10. Use Arachne when geometry narrower than the configured line width is critical to design intent; otherwise use Classic. Check feature filtering and dimensional preservation.
11. Provide at least three actual solid layers in both top and bottom shells, including exposed surfaces, and satisfy functional thickness in mm. Sum actual layer heights when they vary.
12. Apply adaptive/variable layer height with smoothing on every job, within calibrated bounds. Preserve critical Z geometry and first-layer behavior; a valid adaptive result may be uniform. Verify the saved schedule and actual toolpaths. Smoothing alone does not prove good interlayer adhesion. Explain any necessary earlier UI generation step without taking over my desktop.
13. Prefer print by object for differently sized objects, printing small/short objects first. Use print by object for tall objects on a bed slinger. Verify complete head/gantry/bed sweep clearance and actual order; use separate plates/runs when necessary. Sequencing alone does not eliminate wobble.
14. Recommend a compatible second support-interface material for supported critical geometry, but prepare the concrete material/settings/tradeoff plan and obtain my approval before applying it. Enable a prime tower and verify adequate purging in both directions. Follow current primary manufacturer and slicer guides matched to the hardware/material pair.

For multimaterial interfaces, inspect weak bonding at swap heights, including contamination, priming, cooling, speed, contact and line-type classification. My suspected mechanism is a supported surface being classified as overhang/bridge rather than bottom solid, leading to inappropriate cooling or patterns; treat that as a hypothesis to verify. A better-contact/overlap solid-fill pattern or another user-selected slicer may help, but neither is a universal fix.

Use verified printer/nozzle/material profiles and inherited settings. Evaluate load paths, orientation, continuous walls and shell thickness before increasing infill. Check roof support, infill crossings, peak volumetric flow and small-layer cooling. Preserve accepted CAD orientation and functional surfaces. Use measured calibration for physical strength, fit and adhesion; slice estimates are not measurements.

Record source/profile/output provenance, effective settings, approvals, exceptions, warnings, estimates with units and unresolved checks in Project.md. Keep reusable rules in shared slicing policy. Slicing and preview do not authorize printer uploads, heating, motion or starting a print.
```

For legacy in-folder Claude configuration cleanup, generated `backups/`, `cache/`, `file-history/`, `session-env/`, `sessions/`, `shell-snapshots/`, `projects/`, `history.jsonl`, `.last-cleanup`, `.last-update-result.json`, `plugins/` and `skills/` are account/runtime data rather than migration-package source. Remove only identified obsolete backups (`backups/.claude.json.backup.*`), caches, past transcripts/tool results, file history, session environments and project paths from old locations after a recoverable copy. Preserve the current session, project/user files, credentials and installed plugins/skills. Do not read or copy `.credentials.json` or `.claude.json` into the template.

The [OrcaSlicer feasibility study](Explorations/OrcaSlicer/README.md) retains backend comparisons, a local inventory probe, and the live slicing decision gates. Its setup check now exercises the shipped helper; superseded static configuration examples were removed. `Benchmarking/Test-OrcaSlicer.py` checks protocol handling, application launch behavior with a simulated process, configuration preservation, and rollback with a local mock server. Live slicing remains unverified.

`py -3 Benchmarking/Test-SlicerDiscovery.py` checks selection before launching, duplicate discovery, Store activation routing, native interop compilation, CLI capability checks and verified-output/failure handling with simulated apps. `slicer.py list` found Windows Store OrcaSlicer, Snapmaker Orca and Bambu Studio on the assessment machine without opening them. Real GUI activation/import and slicing still need a chosen model and printer profiles.

`py -3 Benchmarking/Test-PrinterLibrary.py` checks catalog transfer, native preset preservation, inheritance, conflicts and failed writes without an installed slicer. It does not verify a real printer or GUI preset import.

Only the inner template is distributed. Benchmark sandboxes, exploration scratch files, and Python caches are ignored; keep application installs and agent runtime data outside that folder. Repository Git history is small and retained for recovery; cleanup does not require deleting or rewriting it.
