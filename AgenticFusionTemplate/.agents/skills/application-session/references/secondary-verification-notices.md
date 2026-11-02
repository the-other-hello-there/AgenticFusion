# Secondary agent verification notices

The shared [notice helper](../../../scripts/secondary_verification.py) uses fixed strings and deterministic rules. Both agents run it through [command hooks](../../../scripts/secondary-verification.ps1). It never invokes a model to classify feedback or write an offer/reminder. Ordinary replies to the user's underlying work request still have their normal usage. Keep opt-in, task scopes, budgets and protected review authority in the [verification guide](../../../../Independent-Review.md).

## Offer after repeated objections

`UserPromptSubmit` counts direct, explicit objections such as “I disagree” or “That's the wrong approach.” On the second distinct objection in the same conversation, while verification is off, it shows one fixed offer through the CLI's `systemMessage` UI channel. It does not add model context, block the underlying correction request or enable anything. Further objections do not repeat that conversation's offer.

The offer warns that reviewer calls and revisions increase 5-hour/weekly allowance usage. The 12.5% default is a reviewer spending ratio, not a guarantee about subscription allowance usage. Approval must name tasks:

```text
Enable secondary agent verification for modeling, slicing
Enable secondary agent verification for all; budget=20%
Keep secondary agent verification off
```

These exact standalone settings replies are consumed by the hook, saved using the existing preference/indexing helper, and answered with a fixed confirmation before a model is called. A bare “yes” after the offer shows fixed task-scope help without enabling anything; “no” keeps it off. Bare answers still reach the ordinary work conversation so they cannot swallow unrelated replies or disable existing verification. Quoted/pasted examples and messages combining settings with other work do not authorize changes.

This is a conservative phrase recognizer, not a complete semantic detector. Neutral edits do not count; ambiguous objections may be missed. Custom clients can record an independently identified objection with the helper's `--mode objection` JSON input (`session_id`, `turn_id`) and display its fixed output directly. Do not invent objections or run another classifier model. Stable turn IDs deduplicate hook retries; without one, identical immediate submissions are briefly deduplicated.

## Allowance reminders

While enabled, remind only at **50%, 25%, 15%, 10%, and 5% remaining**, separately for each provider's 5-hour and weekly window. A fixed reminder names the window/mark and states that secondary agent verification is enabled for selected tasks and can use additional allowance. Never substitute context-window percentages, token counts or estimated cost for account allowance.

Each mark is emitted once per window/reset period, including across process restarts. A reset rearms only that window; stale snapshots do not rearm it. If one observation jumps across several marks, the newly crossed marks are reported together at the next hook checkpoint. Attaching mid-window reports only the most urgent already-reached mark, avoiding a burst of old reminders. Missing/unavailable quota data stays unknown and produces no guessed reminders. Unsupported account plans may expose no 5-hour limit.

- **Codex:** the helper's model-free local app-server client sends only `initialize`, `initialized` and `account/rateLimits/read`, at most once per 30 seconds while enabled. Only reported 300-minute and 10080-minute windows are accepted; it does not create threads/turns or change account/reset settings. See [Codex account limits](https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt).
- **Claude Code:** a quiet status-line command receives native `rate_limits.five_hour` / `seven_day` values, queues marks, and synchronous hooks show each warning once. Setup installs the bridge only if neither a project nor a user-level status line exists, preserving existing custom displays. For a custom line, forward its unchanged input JSON to `py -3 .agents/scripts/secondary_verification.py --mode observe --agent claude --workspace .` and retain the original display. See [Claude status-line quota fields](https://code.claude.com/docs/en/statusline#available-data).
- **Supervised/headless work:** the parent owns display so captured child hooks cannot lose or duplicate warnings. Codex uses the same account reader. Claude/custom trusted meters may include `allowance_windows` in their existing receipt: `[{"window":"five_hour","used_percent":75,"resets_at":UNIX_SECONDS},{"window":"weekly","used_percent":90,"resets_at":UNIX_SECONDS}]`. Unnamed `rate_limit_event.utilization` alone cannot establish which window it describes. Without a native bridge or verified meter data, headless quota monitoring remains unavailable.

Hooks emit only user-facing JSON (`systemMessage`, or a settings reply's `decision: block` plus fixed `reason`), never `additionalContext` or an agent/prompt hook. See [Codex hook output](https://learn.chatgpt.com/docs/hooks#common-output-fields) and [Claude hook output](https://code.claude.com/docs/en/hooks#json-output). Codex requires the user's normal hook trust review; never bypass it. Python is needed for this optional feature; missing Python or helper/telemetry failure quietly skips notices without blocking ordinary startup or changing review approval/budget rules.

Runtime counters, hashed event IDs, reset IDs and queued fixed messages live under `%LOCALAPPDATA%/AgenticFusion/SecondaryVerification/`, outside the project. No prompt bodies, transcripts, credentials or quota responses are archived. `AGENTIC_SECONDARY_STATE_ROOT` supplies another external state directory for controlled tests/integrations. Do not delete live reminder state during routine cleanup, or the same marks could be repeated. Existing `Agentic-Verification.json`, `Independent-Review.md`, `review_guard.py` and `AGENTIC_REVIEW_*` identifiers remain compatible; the system's user-facing name is **secondary agent verification**.
