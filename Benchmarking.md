# Agentic Fusion benchmarks

## Benchmark prompts

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
