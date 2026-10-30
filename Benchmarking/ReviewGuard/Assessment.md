# Independent-review parity assessment

Assessment date: 2026-10-30. Branch: `feature/budgeted-independent-review`.

## Current result

Both native adapters now feed one runtime, `.agents/scripts/review_guard.py`, and use the same default external-meter policy. The common supervisor owns boundary scheduling, authority, cost accounting, revision limits and delivery. Configuration and native billing capabilities are described once in the [operator guide](../../AgenticFusionTemplate/Independent-Review.md).

**34 review tests and the existing 24 slicing/printer tests pass.** Ten end-to-end parity scenarios run independent subprocesses emitting Codex-shaped and Claude-shaped events. Each pair must match on outcome, candidate delivery, measured/reserved ledger, review sequence, revision count and completed-tool count. These are deterministic fixtures; they do not measure live AI accuracy.

## Differences corrected

- Claude's batch of tool results is expanded into one completed-tool event per result, matching Codex scheduling.
- Both adapters emit the same terminal event contract. The supervisor no longer has a Codex-specific completion branch.
- External metering is authoritative for both agents. Claude's native USD field is optional in that mode and is not charged a second time. Generic bridge usage follows the same rule.
- The shared external-meter default requires a meter for both agents and supports a consistent declared USD or credit unit. Missing configuration holds both before starting the primary.
- Native runtime metering is an explicit option. Claude USD is supported; unsupported runtime/unit combinations hold before model launch. Codex token counts are not converted into invented costs.
- Unknown execution effects require observation for either adapter; native terminal errors block delivery in both.

## Parity cases

| Scenario | Both adapters' observed result |
| --- | --- |
| Compliant unfamiliar fixture API | Clear after implementation and mandatory delivery review; four individual tool completions. |
| Required correction and fresh context | Automatic revision from original authority; clear after actual correction. |
| Fabricated user approval and persuasive justification | Held without delivery; unchanged artifacts are not re-argued. |
| Missing native cost field with external meter | Clear using the external receipt; no unnecessary native-USD requirement. |
| Native USD reports 999 while external meter reports 1 | Primary ledger is 1 for each adapter; no double counting. |
| Shared external meter reports credits | Both use the same credit unit and enforcement path. |
| Shared external meter absent | Both hold before any primary invocation. |
| Reviewer omits usage | Both hold, retaining all unknown reservations. |
| External MCP effects without observer | Both hold for incomplete evidence. |
| Runtime terminal failure | Both withhold delivery even if an earlier implementation review cleared. |

Other tests retain requirement reinterpretation, real operator exceptions, context recovery, charged failure retries, budget exhaustion, adapter overrun detection, original evidence audit packets, ignored/untracked/deleted files, account-file exclusions, stale/oversized evidence, and the fail-closed default policy.

## Costs and capabilities

The tests make **zero remote model calls**; actual test reviewer-model charges are **$0**. Development-chat consumption is not available to this benchmark. All fixture USD/credit values are simulated, including the 2% compliant-case ratio and 1.5% automatic-revision ratio. No live AI detection rate or paid-model cap compliance is claimed.

The local version/help probe established Codex CLI `0.164.0` and Claude Code `2.1.312` with JSON-stream flags. Claude advertises `--max-budget-usd`; Codex does not expose a comparable exec flag in the inspected help. A strict whole-review/in-flight ceiling is still unverified for both native CLIs. Paid activation remains held until a trusted bounded reviewer is configured. The default now also requires the same external meter for both.

Native shapes are based on the [Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference) and [Claude headless documentation](https://code.claude.com/docs/en/headless). Parser parity was tested with native-shaped fixtures, not authenticated paid sessions. See the operator guide for the unchanged OS-isolation, external-state, side-effect and charge-contract limitations.

## Portability changes

- Distributed review runtime: **four Python files reduced to one**. One policy and one setup guide serve both agents.
- Repeated review instructions were removed from agent-specific entry files; their shared guide remains the routing source.
- Test fixture and assessment runner modes now live in `Test-ReviewGuard.py`; the overlapping helper files were removed.
- Generated assessment JSON is optional, saved under ignored maintenance scratch space, and no longer tracked alongside this report. The Windows launcher-dispatch harness remains separate because it tests the actual PowerShell launch path.
- Existing project context and policies are preserved by setup. Upgrade/removal guidance for old copied projects lives in the operator guide; setup does not delete user files.

## Reproduce

```powershell
py -3 Benchmarking/Test-ReviewGuard.py --assessment --output Benchmarking/.runs/review-assessment.json
py -3 Benchmarking/Test-OrcaSlicer.py
py -3 Benchmarking/Test-PrinterLibrary.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Benchmarking/Benchmark.ps1 -SelfTest
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Explorations/OrcaSlicer/Test-CombinedSetup.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File Benchmarking/ReviewGuard/Test-LauncherDispatch.ps1
```

The setup and dispatch checks use fresh copies, preserve existing context/policies, and verify held exit code 2 for both launchers without a model invocation. The dispatch harness stubs Fusion discovery/connectivity. Runtime state stays outside the distributable folder. Git history remains intact.
