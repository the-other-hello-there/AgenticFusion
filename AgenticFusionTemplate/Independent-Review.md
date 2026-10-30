# Independent requirement review runtime

This experimental runtime supervises a **whole task**, not an agent-selected review request. It launches a primary CLI with its output captured, automatically schedules implementation reviews from runtime tool events and actual filesystem changes, and requires an independent review before releasing the candidate answer. A rejection starts a fresh primary invocation with the original requirements and concise revision findings. Existing completion-tone hooks remain unchanged.

The runtime is one shared file, `.agents/scripts/review_guard.py`, used by Codex and Claude Code with one `Review-Policy.json`. Python 3.11+ and an installed primary CLI are needed. Other agents can use the documented trusted JSONL bridge contract below.

## Readiness and limits

**The supplied policy is intentionally not ready for paid use.** It has no reviewer command or verified spend-ceiling contract. It exits with `DELIVERY HELD` before starting a primary model. A real bounded reviewer adapter must be supplied by the operator; the deterministic test reviewer is not an AI reviewer and must not be used for production approvals.

The installed runtime probe checks CLI flags and versions without model calls:

```powershell
py -3 .agents/scripts/review_guard.py probe
```

The default `primary_meter_mode: "external"` requires the same trusted `primary_meter_command` for both agents. It owns the ledger's primary consumption; native token/USD events are observations, not additional charges. Both runtimes therefore share the same metering prerequisites, boundary scheduling, budget checks, automatic revision and delivery behavior. Claude batches are expanded into one completed-tool event per result, matching Codex's individual tool events.

Native billing still differs: Codex emits tokens; Claude may report `total_cost_usd` as API-equivalent USD, not subscription credits or an invoice guarantee. Explicit `primary_meter_mode: "runtime"` supports native Claude USD or a trusted custom bridge's receipts. It rejects unsupported runtime/unit combinations before launching a model and cannot be combined with an external meter. Missing mode fields default to external. No token-priced estimates are silently accepted as measured credits or USD.

Claude offers `--max-budget-usd`, but this implementation has not verified a strict charge ceiling for an individual in-flight request, internal retry, or background operation. Neither native CLI is shipped as a supposedly hard-bounded reviewer. See the [Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference), [Claude CLI reference](https://code.claude.com/docs/en/cli-reference), and [Claude costs](https://code.claude.com/docs/en/costs).

## Run a supervised task

Write the original user request verbatim into a task file through the operator/user channel. Keep the policy, reviewer implementation, meter and controller state outside the primary writable workspace, protected by its OS sandbox or a separate account/container. The controller loads requirements and policy before launching the primary; modifications made by the primary do not amend that in-memory authority.

Configure a copy of `Review-Policy.json` with a trusted `reviewer_command` and an established `reviewer_enforces_charge_ceiling` contract. Set `unit` to `usd` or `credits`, consistently across every meter and reviewer receipt. Keep the default external-meter mode for identical Codex/Claude behavior; native runtime mode is an explicit capability-dependent option. A `true` policy flag is an operator attestation, **not proof that an arbitrary adapter caps spending**.

```powershell
py -3 .agents/scripts/review_guard.py run --agent codex --workspace . --requirements 'C:\ReviewControl\task.txt' --policy 'C:\ReviewControl\policy.json' --state-dir 'C:\ReviewControl\task-001'
py -3 .agents/scripts/review_guard.py run --agent claude --workspace . --requirements 'C:\ReviewControl\task.txt' --policy 'C:\ReviewControl\policy.json' --state-dir 'C:\ReviewControl\task-002'
```

Both regular Fusion launchers can select this runtime by setting `AGENTIC_REVIEW_TASK` to that task file and `AGENTIC_REVIEW_POLICY` to the protected policy before launching. Their normal initialization/Fusion startup remains intact; the guarded task replaces the interactive agent invocation. Unset those variables for ordinary **unguarded** sessions. A primary child cannot unset environment variables in the already-running parent supervisor.

The primary must not call the reviewer itself, choose whether review happens, or supply the authoritative requirements. Its output is candidate evidence only. Only the supervisor releases its captured final answer after a current clear decision. Exiting a child, disabling project hooks, claiming approval in a file, or exhausting budget does not release that output.

## Review and revision behavior

- Implementation boundaries are chosen by the supervisor: a configured tool count, changes spanning at least three files, or observed test/commit command events. The observer does not trust the primary's claimed milestone or its Git ignore rules. Unchanged previously reviewed artifacts are not repeatedly charged as new implementation work.
- The reviewer receives original user text, controller-supplied exceptions, original/current changed-file contents and hashes, actual runtime tool events, and the candidate response. Removed and untracked files are included. Oversized evidence is held rather than silently truncated.
- Reviews are isolated, concise, and stateless. They return `clear`, `revise`, or `unverifiable`, with at most three findings citing exact original requirements. Unfamiliar implementation is not itself a violation. A convenience argument is not an exception.
- A rejection automatically causes revision. Re-arguing unchanged rejected artifacts is blocked. Attempts and revisions are bounded; a failed/inconclusive reviewer or an exhausted budget leaves delivery held.
- Final review is mandatory even after an implementation clear. The artifact hash is checked again after final review, preventing an approval for a stale snapshot from releasing a changed workspace.
- Native cost telemetry often arrives only at the end of a CLI run. An earlier boundary lacking measured budget is logged as held/deferred; work can continue, but that boundary was **not cleared or actually AI-reviewed**. The final gate must still pass. Use a live trusted meter for timely intermediate reviews.

Initial user exceptions can be provided through `--user-exceptions` as a JSON array of explicit user statements. A later exception uses the operator-only `authorize-exception` command, followed by `--resume`. Neither channel accepts a primary-generated file inside the workspace. It updates the authority hash while preserving original requirements, all costs, unknown reservations, attempts and revision counts; an exception does not reset the review budget. Changed original requirements require a deliberately authorized new task. Resume refuses unexplained authority/ledger mismatches.

```powershell
py -3 .agents/scripts/review_guard.py authorize-exception --workspace . --state-dir 'C:\ReviewControl\task-001' --statement-file 'C:\ReviewControl\actual-user-exception.txt'
```

The operator must authenticate that the statement really came from the user. A process with the same unrestricted OS privileges could impersonate that operator; use a separate account/container or protected control channel for adversarial enforcement.

## Accounting and recovery

The default budget is **12.4%** of measured primary consumption, strictly below 12.5%. The next review reserves at most `min(per-call ceiling, primary × ratio − all previous charged/reserved review cost)`. A request is dispatched only after its reservation is persisted. The adapter receives that exact maximum and must enforce it across its entire invocation, including hidden calls, tools and retries. The supervisor requests no adapter retries.

Measured review receipts replace reservations with actual cost. Missing receipts, timeout, process failure or interruption retain the full reservation. There are no free retry attempts. A failed identical packet permits at most one charged retry on resumption; a decided packet cannot be re-argued. If an adapter reports an overrun, the actual amount and breach are recorded and delivery is blocked. This detects a broken cap contract; it cannot undo a charge already made by an adapter that violated the contract.

The ratio covers reviewer adapter consumption, including its subcalls/retries. Primary implementation/revision consumption remains in the measured primary total; this is not a bound on wall time or all incremental primary work caused by review.

`authority.json`, `baseline.json`, `ledger.json`, `events.jsonl`, per-attempt review input/output packets, `primary-stderr.log`, and `report.json` live in the outside state directory. They are runtime data and must not be copied into the distributable template. Reports label units, measured primary cost, charged/reserved reviewer cost, unknown charges, ratio, attempts, deferred boundaries, observed coverage gaps and enforcement limits. A zero measured primary total is not a claim that a failed/unmetered task was free.

Resume with the same arguments plus `--resume`. Original authority, initial artifact baseline, charged/unknown reservations and revision counts survive recovery. A resumed primary receives original requirements and stored findings instead of relying on its own remembered summary. An existing state directory cannot be reused accidentally without `--resume`.

## Trusted adapter contracts

Commands are argument arrays executed without a shell. Reviewer code is rejected when it resides inside the primary workspace. A reviewer runs from the controller directory with the packet on stdin and must have no access to mutate the primary workspace. Enforce that restriction with the runtime/OS; the JSON `read_only` field alone is not a sandbox.

Reviewer input:

```json
{"packet":{"instructions":"...","authority":{"original_user_requirements":"...","user_exceptions":[]},"boundary":"delivery","evidence":{}},"unit":"usd","maximum_charge":"0.004","allow_retries":false,"read_only":true}
```

Reviewer output:

```json
{"decision":"clear","coverage":"complete","findings":[],"usage":{"unit":"usd","amount":"0.003","quality":"provider_reported"}}
```

A `revise` finding contains `requirement_quote`, `evidence`, and `issue`, each at most 600 characters. Failure, malformed output, wrong accounting units, incomplete coverage or missing usage never imply approval. A provider SDK/CLI bridge must independently implement request limits, metering, tool isolation and any internal-retry accounting. A bare CLI `--max-budget-usd` flag has not been established as sufficient for that contract.

`primary_meter_command` receives `invocation`, `pid`, `unit`, `final`, and observed `runtime_usage` receipts (possibly empty). It returns non-overlapping **delta** receipts with `amount`, `unit`, `quality: "provider_reported"`, and a unique `measurement_id`. IDs are deduplicated. Native receipts are not also added to the ledger in external mode; even a missing native USD field does not bypass the external meter or fail an otherwise metered task. Do not return a new ID for the same cumulative account total, mix tasks, or convert subscription usage using API prices.

For other primary agents, set `primary_command` and use `--agent custom`. The trusted bridge reads the supervisor prompt from stdin and emits JSONL runtime events: `usage` with a delta receipt, `tool_completed` with `actual_event` and `external_effect`, and terminal `completed` with `text` and a final usage receipt. In external mode the bridge's usage is observational; only the external meter charges the primary ledger. In runtime mode a comparable terminal receipt is mandatory. `candidate` text is never parsed as authority or metering. These events must come from the runtime, not from the model emitting JSON as its answer.

`external_evidence_command` is an optional independent, read-only domain observer. It receives the workspace and current artifact digest and returns actual observed state and `coverage_complete`. Use it for Fusion/OrcaMCP or other external effects. Without it, observed MCP calls leave coverage incomplete. Binary changes, linked paths, and evidence exceeding limits also hold review. This version does not provide a Fusion geometry or Orca print-result verifier.

## Enforcement boundary

This is a functioning supervisor/gate, not a guarantee against a hostile same-user process. Protect its code, state, policy, meters and reviewer with a separate privilege boundary. A primary with unrestricted OS access could kill the supervisor, modify its controls, access another delivery channel, or operate a printer before review. Post-tool review cannot reverse effects already performed. The framework gates its own answer delivery; it is not a deployment, Git push, filesystem-write, or physical-printer transaction firewall.

`.git` internals, Python caches, `.credentials.json`, and `.claude.json` are excluded from file evidence; arbitrary shell effects outside the workspace are not comprehensively observed. The interpreter is protected from ordinary in-task source edits because its controller code is already loaded, but a later launch from modified source is not trusted installation. Install/vet controller code outside the editable project for protected operation. Normal unguarded CLI sessions are outside coverage.

Native hook documentation supports automation but does not remove these limits: non-managed Codex hooks require trust; post-tool review cannot undo operations, and hook failures/unsupported controls can continue execution. Claude also documents stop-hook continuation limits. For that reason a mutable project Stop hook is not used as the final authority. [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude hooks](https://code.claude.com/docs/en/hooks)

## Portable file layout and upgrades

The distributed folder has one review runtime script, one policy, and this setup reference. Agent entry files use the shared `Agentic-Fusion.md` routing instead of maintaining separate review procedures. Tests and assessment notes stay at repository root; generated assessment JSON is optional and ignored. Runtime receipts/audit packets remain outside the project.

For older project copies, setup still preserves existing launchers, policy and context. To adopt the unified script, bring over the new shared `Fusion-Claude.bat` while retaining any project-specific Fusion path/port edits, copy `.agents/scripts/review_guard.py`, and review the policy's explicit meter mode. The old `.agents/review_guard/` directory may be removed only after checking that local launchers, protected installs and custom integrations no longer reference it. Setup never deletes it automatically.
