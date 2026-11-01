# Save, close, checkpoint and restart

One procedure serves Fusion and the chosen slicer in both agents. Use `Agentic-Fusion.md` for context ownership/cleanup, `fusion-model`'s MCP reference for Fusion save timing, and `orca-slice` for saved slicing state and non-disruptive UI access. The 12-hour policy covers task-related Fusion/slicer application processes, not AI agents or arbitrary software open on the computer. Register other task applications only after extending/validating their save/restart adapter; do not sweep unrelated user programs.

## Continuous housekeeping

- After a read-only reference comparison, export or temporary experiment, close documents/jobs no longer needed. In Fusion, restore the working document after closing the reference; in the slicer, preserve the accepted saved job before replacing/closing a temporary plate/window.
- `doc.close(False)` is appropriate only for a verified unmodified saved reference or an agent-created disposable draft with no unique work. For modified or uncertain documents, save and verify first. Keep open any document/scene needed by an active operation, unsaved edit, dependency or user task. A hidden/minimized window is not proof that it is unused.
- Whole-app closure is allowed for an unused task session after every open document/job and other session/user has been accounted for. Use graceful application APIs or the helper's checkpoint-gated `Close`; never `taskkill`, `Stop-Process`, force termination or blanket process-name cleanup. The user authorized routine closure of unused task resources, not discarding their work.
- Existing recovery/command dialogs, uploads, slices, printer monitoring, active prints or external clients may prevent closure. Identify the blocker and leave the session pending. A timeout does not establish that a Fusion script stopped.

## Checkpoints before limits or restart

Update a concise `Restart checkpoint` under `Project.md` and link detail only if needed:

| Item | Required durable information |
| --- | --- |
| Current work | User objective, last verified result, current operation/transaction and whether it completed. Preserve relevant design intent, decisions, approvals and unresolved hypotheses. |
| Pending tasks | Ordered unfinished tasks, exact next action, dependencies/blockers, acceptance checks and anything unsafe to repeat. Keep live tasks in current context, not solely in old history. |
| Fusion | Cloud document/lineage IDs and names, verified saved version, active document, relevant parameters/body selection, health/constraints, and any unsaved/recovery condition. |
| Slicer | User-selected app/version, saved native 3MF job path/hash, model/export provenance, profiles/overrides, orientation, plate, materials, adaptive schedule and slice/preview status. G-code alone does not preserve an editable slicer project. |
| Long operations | Actual completed/running/cancelled state, log/output paths, safe resumption point and stale-result invalidations. Do not mark an in-flight operation as saved/idle. |
| Maintenance/handoff | Reason, applications due, checkpoint readiness, restart approval or deferral, and post-restart verification still needed. Keep machine-specific launch paths in the external helper state, not portable authored instructions. |

Save Fusion through its established autosave-aware procedure, in a separate MCP call; verify actual latest cloud version, unmodified state and saved readback before closing. For a new document, establish its intended name/location with `saveAs` rather than silently creating another design. Preserve the current timeline/pose/visibility and record anything restoration requires. A crash-recovery backup is not a verified save.

For Orca, save a native editable project containing the accepted geometry, transforms, profiles, overrides and layer-height schedule, then verify the actual file and any slice artifacts. A successful CLI slice does not save unsaved GUI edits. Use a supported API/background control; if saving requires cursor/focus takeover, retain the session and report the exact blocking action. Do not auto-discard a dialog or substitute G-code for the project state.

## Full context-preserving cleanup

Perform this automatically after verified saves and before asking about a deadline restart, or when handing off near usage exhaustion:

1. Copy authored context to an external session scratch/backup location before consolidation. Retain saved CAD/slicer artifacts and required manifests/logs.
2. Merge repeated/superseded context into its authoritative home. Keep the active objective, live pending tasks, parameters, document versions, decisions, approvals, errors and resumption steps available in `Current state`/`Restart checkpoint`. Keep current work out of history-only storage and out of agent-specific memory.
3. Close unused reference/scratch documents/windows under the housekeeping rules. Remove only identified obsolete, task-created temporary files after checking callers and pending-task dependencies. Preserve calibration/comparison evidence, failure logs needed for diagnosis, user files, installed profiles/plugins, credentials, current sessions and original source inputs. Do not purge Autodesk/Orca application caches, recovery data, profile directories, cloud documents or agent-wide histories as routine cleanup.
4. Verify that the checkpoint matches the saved application state and that the next task is actionable by either agent. Update the helper checkpoint only after these checks. If blocked, record the blocker and do not attest successful save/cleanup.

Do not close the AI agent before its final handoff is recorded/reported, and do not restart an agent to bypass usage limits. When quota is low, prioritize verified saves and the minimal live-task checkpoint before optional housekeeping; record any cleanup still pending rather than spending the remaining allowance on a long compaction. A surprise hard limit cannot guarantee one more model turn, so milestone checkpoints are mandatory fallbacks.

## Runtime helper

The PowerShell helper has no Python/package requirement. It stores per-project runtime state outside the portable folder. `Status` is read-only toward applications. `Register -StartMonitor` tracks exact PID, executable and OS start time and starts one hidden watcher per project. The watcher polls every 30 seconds, queues a due state and shows one non-modal notice per process; it never closes applications, edits CAD or fabricates a semantic checkpoint. Launcher `--setup-only` starts no watcher.

Ordinary `Status` also leaves runtime files unchanged, so a read-only agent check does not need to rewrite profile state. Registration, checkpointing and the already-running watcher own their state updates.

```powershell
# Use real process IDs from the actual application/window, never these placeholders.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Register -ProcessId 1234 -Kind Fusion -StartMonitor
# For a selected slicer, preserve its exact launcher or Store AUMID; optional saved job to reopen.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Register -ProcessId 5678 -Kind Slicer -LaunchPath 'C:\Tools\Orca\orca-slicer.exe' -RestoreFile 'Print Jobs\saved-job.3mf' -StartMonitor
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Status
```

For a Store app, supply `-AppId` from the selected application's discovery record; its file activation route is retained. For an explicit Fusion `.lnk`, pass `-LaunchPath`. If a special build needs startup arguments (for example its isolated `--datadir`), use a JSON string array in `-ArgumentsJson`; do not copy arbitrary process command lines or credentials. Confirm its actual data directory/profile set. If a launcher exits after handing off to an existing process, bind the verified window process rather than guessing a PID. Reattachment never resets process age.

After actual save verification, context-preserving cleanup and an idle check:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Checkpoint -ProcessId 5678 -SavedStateVerified -CleanupVerified -ApplicationIdle -RestoreFile 'Print Jobs\saved-job.3mf'
# Only after the user's approval for this specific application/session:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Restart -ProcessId 5678 -CheckpointId CHECKPOINT_ID -ApplicationIdle -UserApproved
# Or close a verified unused application without restarting it:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Close -ProcessId 5678 -CheckpointId CHECKPOINT_ID -ApplicationIdle -UnusedVerified
```

These flags attest the agent's completed checks; they do not read Fusion/Orca unsaved-state APIs automatically or supply user consent. Do not set them speculatively. The helper checks process identity, a checkpoint no older than five minutes and unchanged `Project.md`/saved restore-file hashes. If approval is delayed, refresh live saved/idle checks and the checkpoint; an existing approval for the same concrete restart remains valid unless its scope/state changed. If closing several apps, checkpoint all against the current `Project.md` before closure; editing it invalidates those hashes and requires refreshing remaining checkpoints.

The helper sends a graceful close request and waits up to 30 seconds. If a dialog or operation blocks closure, it returns pending and never force-quits or launches a duplicate. After confirmed exit it starts the recorded launcher/Store app, restoring the selected slicer file when supplied. A launch request is not verified restoration: immediately rebind the real new PID with `Register -StartMonitor`, reconnect/rediscover MCP, reopen the recorded Fusion documents by lineage/version, inspect the actual slicer project/plate/profiles, and reconcile `Project.md` before resuming. For the same paused slicing job retain its user's slicer choice; a new job follows normal selection policy.

Windows documents that [CloseMainWindow requests an orderly exit that the application may refuse](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process.closemainwindow); the helper deliberately has no forced-termination fallback.

If a process exits after a pending close or during a quota handoff, do not retry against its old/reused PID. Use the normal recorded launcher or selected-app opening route under the existing valid restart scope, restore the durable checkpoint, and register the real new process. A closed application does not erase the pending tasks in `Project.md`.

## Usage telemetry and approval limits

Use the current client's exposed account-usage fields/warnings; never treat context percentage as account allowance. The shared thresholds are checkpoint/avoid long new operations at 80% used and checkpoint/cleanup/handoff at 90% used, or earlier when the client warns or reliable budget is insufficient. Reset times are facts only when actually exposed. Missing/stale telemetry stays unknown. The client adapters in `AGENTS.md`/`CLAUDE.md` identify their supported UI/status sources; do not read credentials or scrape unrelated session transcripts to invent telemetry.

At 11.5 hours, prepare the restart checkpoint. At 12 hours, stop starting new work in that app and carry out saves/cleanup, then prompt once with the named apps, checkpoint state and any physical/other-session risks: can these applications safely restart now? Approval is required because the user requested it. A refusal/deferral leaves the saved checkpoint and pending restart visible. Do not repeatedly ask on each status poll; recheck after a relevant state change or the user's requested time.

An offline/exhausted agent cannot perform semantic saves, full cleanup or an interactive restart decision merely because a timer fired. The watcher supplies durable deadline detection/notification, and either agent performs pending maintenance on its next active boundary. An in-flight operation, approval wait or unsavable document may exceed the 12-hour deadline; report this explicitly rather than enforcing a destructive hard cutoff. Continued operations require resolving the pending maintenance, not resetting the registration clock.
