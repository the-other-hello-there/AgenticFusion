# Agentic Fusion benchmarks

Run `Run-Benchmark.bat` from this folder for a guided Windows benchmark. It copies the distributable template into `Benchmarking/.runs/`, checks both launchers in fresh copies, opens the selected agent, and guides B1-B7 with a timer and results fields. At the end it asks whether to append results under `vYYYY-MM-DD`, then deletes the temporary local copy after the agent window is closed. Use a disposable Fusion project; Fusion cloud documents are outside the local copy.

## Benchmark prompts

For maintenance checks without an installed slicer, run `py -3 Benchmarking/Test-OrcaSlicer.py` and `powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-CombinedSetup.ps1` from the repository root. These check the shared Orca startup/configuration helper against mock MCP and disposable project copies; they are not live slicing scores.

Run `py -3 Benchmarking/Test-PrinterLibrary.py` for printer catalog/preset transfer checks. The combined setup check also verifies that both launchers preserve an existing printer library.

Run `py -3 Benchmarking/Test-ReviewGuard.py --assessment` for independent-review controls, Codex/Claude event-stream parity, the local capability probe and explicitly simulated ledgers. Optional `--output Benchmarking/.runs/review-assessment.json` saves an ignored report. See [the assessment](ReviewGuard/Assessment.md) for results and limitations; these tests do not invoke live AI reviewers.

Run these in order in a **disposable Fusion project** using a fresh copy of the template for each version you compare. Start the chosen agent through `Fusion-Claude.bat` or `Fusion-Codex.bat`, open a new blank Fusion design before B1, and keep the same project and design through B6. Before B3, select one mounting-hole feature in Fusion's timeline. Before B7, close the agent and reopen it through the same batch file. Start timing when you send each prompt and stop when the agent finishes its answer; record the change in the credit or usage measure you have available. Keep the same measurement method across versions. Do not include your own preparation or review time.

### B1 — Connection and read-only inspection

> Using the Fusion MCP connection, identify the active document, its units, root component, and current body and component counts. If there is no active document, say so. Do not create, modify, or save anything.

**Accept when:** The report matches Fusion and leaves the design unchanged.

### B2 — Parametric modeling and first save

> In the new blank Fusion design, make one solid L bracket. Its base is 60 mm in X, 30 mm in Y, and 4 mm thick in Z. At the X = 0 end, add a wall across the full 30 mm width; the wall is 4 mm thick in X and rises 25 mm above the base's top face. Add two 4.5 mm diameter through holes in the base at (X, Y) = (20, 15) mm and (45, 15) mm, measured from the X = 0, Y = 0 base corner. Use named user parameters for these dimensions and positions. Do not add ribs or decorative features. Verify dimensions, body count, and timeline health, then save as `Benchmark L Bracket`. Record the verified design intent, document name, and parameters in `Project.md`.

**Accept when:** The saved design has one healthy parametric body with the specified geometry, independent design choices use named user parameters, dependent dimensions use expressions, and `Project.md` contains verified facts.

### B3 — Selected-feature identification

> I selected a mounting-hole feature in Fusion's timeline. Identify the selected feature, its owning component, hole diameter and every position controlled by it, and what it does in the bracket. If the selection or a property is unavailable, say exactly what you could verify. Do not change the design.

**Accept when:** The selected feature and measured properties are correct, with no invented details or edits.

### B4 — Design analysis

> Assume a 20 N load acts normal to the wall at its top edge. Estimate the bending moment where the wall meets the base. Compare the wall's idealized bending stiffness at 4 mm and 5 mm thickness while keeping its width and height fixed. State the assumptions and what else you would need to judge real strength and deflection. Do not modify Fusion or `Project.md`.

**Accept when:** The moment is about 500 N·mm, the idealized 5 mm wall is about 1.95 times as stiff in the stated bending direction, and material, load path, and joint limitations are stated.

### B5 — Parameter change, verification, and memory

> In `Benchmark L Bracket`, change only the wall rise above the base from 25 mm to 30 mm by editing its user parameter. Verify that the base, both holes, body count, and timeline health remain correct. Save a new version with a descriptive message and update `Project.md` with the verified new state. Report any problem instead of silently rebuilding the part.

**Accept when:** The wall rise is 30 mm through its existing parameter, no corrective geometry feature was appended, the rest of the geometry is preserved, the new version is saved, and `Project.md` agrees with Fusion.

### B6 — Printability review

> Review the current bracket for FFF printing with the base flat on the bed. Follow the DfAM decision path: identify likely print issues, distinguish safe changes from changes that need approval, and explain fit or clearance rules only if they apply to this bracket. Report the result without changing or saving the design.

**Accept when:** The review uses the relevant `fusion-print` skill references, respects the existing geometry and design intent, and makes no unauthorized changes.

### B7 — New-session context recovery

> In this new agent session, summarize the bracket's recorded design intent, current wall rise, hole layout, Fusion document name, and any open items. Check `Project.md` and the live Fusion document; distinguish confirmed facts from anything you cannot verify. Do not edit either one.

**Accept when:** The answer matches both `Project.md` and Fusion after the restart and does not invent missing context.

### Results to fill in

Copy this block for each template revision. Use the Git commit ID if the template has no version tag. Rate acceptability from **1 (unusable)** to **5 (fully acceptable)**, and note the specific errors or extra corrections needed.

- Template version or Git commit: **[fill in]**
- Agent and CLI version (`claude --version` or `codex --version`): **[fill in]**
- Fusion version: **[fill in]**
- Model and effort: **[fill in]**
- Date and credit/usage unit: **[fill in]**

| Prompt | Time (mm:ss) | Credits or usage delta | Acceptability (1–5) | Notes |
| --- | --- | --- | --- | --- |
| B1 | [fill in] | [fill in] | [fill in] | [fill in] |
| B2 | [fill in] | [fill in] | [fill in] | [fill in] |
| B3 | [fill in] | [fill in] | [fill in] | [fill in] |
| B4 | [fill in] | [fill in] | [fill in] | [fill in] |
| B5 | [fill in] | [fill in] | [fill in] | [fill in] |
| B6 | [fill in] | [fill in] | [fill in] | [fill in] |
| B7 | [fill in] | [fill in] | [fill in] | [fill in] |

## Template consolidation assessment, 2026-10-30

The portable module's 50 files were audited for repeated instructions, overlapping references, launcher code and configuration. Shared routing/context placement now lives in `Agentic-Fusion.md`; agent entry files retain their own discovery, tool and account rules. Detailed parameter design moved to its linked modeling reference. Repeated slicing routing and startup detail were shortened without changing preferences, hardware records or helper behavior.

| Area | Decision |
| --- | --- |
| Launchers | One agent-discovery function and a shorter copy manifest; retain the explicit allowlist and both user-facing batch entrypoints. |
| Native config and hooks | Keep both clients' formats and trust behavior, with one shared completion script. |
| Skills and references | Keep seven discoverable skills, the copyable printer record and task-specific references. Their distinct scopes support selective reading; technical rules, numerical examples and recovery evidence remain. |
| Orca/printer helpers | Keep standalone standard-library tools. Their configuration rollback and catalog-validation/write contracts differ; a shared library would add coupling. |
| Independent review | Retain the single runtime, policy and setup reference, including budget holds and existing activation/enforcement limits. |

The entry file plus shared guide shrank from 10,614 to 8,700 decoded characters for Codex (18.0%) and from 11,803 to 9,951 for Claude (15.7%), excluding project-specific context and runtime-provided skill metadata. No distributed files were added or removed; Git history was retained.

Validation: all 58 regression tests passed, along with both fresh-copy launcher checks, guarded dispatch and installed CLI discovery. The combined setup check now verifies all shipped files, excludes injected runtime leftovers, and preserves customized instructions, a skill reference, launchers, project context, slicing preferences, printer definitions and review policy. Local links/anchors, context budgets, JSON/TOML and Python/PowerShell syntax passed; all skill discovery metadata is unchanged. Live Fusion modeling, slicing and paid-model behavior were not exercised by this audit.
