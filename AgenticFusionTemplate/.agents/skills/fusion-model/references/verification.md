# Evidence, long runs and delivery

Read for a substantial build/check, a disputed result, or an explicitly configured project completion gate. This procedure is shared by both agents. Paid secondary agent verification remains separately opt-in on its experimental branch.

## Define what a passing result means

Keep the authorized requirement, controlling cause, predicted correction and a comparison that could disprove it in project context. A failed required criterion rejects a candidate even when another metric improves. The user's latest rejection invalidates that acceptance and dependent conclusions; retain earlier measurements as history. Compare genuinely different constructions when the cause is uncertain; the number of alternatives and retry limits follow the project, rather than fixed universal counts.

Distinguish source changes, feasibility probes, live builds, saved artifacts and independent saved readback. A dimension-free probe can expose a failed loft but cannot verify parameter response. For edits to an existing parametric design, use a complete parametric trial copy with its real dependencies when practical. A pasted-solid harness tests only the copied shape. Project-specific construction restrictions belong in an indexed project skill, not every template user's policy.

Emit structured checks with `pass`, `fail`, `unknown` or `external_pending`, measured values/units, evaluated coverage and named failures. Script completion, healthy features, a status string, output existence or an instruction change alone does not establish acceptance. Failed reads and absent expected bodies/criteria are unknown/fail, never silently skipped. Bind reports to document lineage plus saved revision, run ID, source/profile hashes and actual artifacts. Verify claimed saved results by rereading that version; distinguish physical tests from CAD/slice predictions.

## Bound a long run

Use a new UUID for each actual execution; do not reuse it on retry. Log newline-terminated UTF-8 records `RUN <id> START`, `RUN <id> PROGRESS <detail>`, and `RUN <id> DONE` or `RUN <id> FAILED <detail>`. Flush progress during expensive stages. Emit DONE only after the run's own health/check results are evaluated. Catch exceptions to log FAILED, then re-raise; do not let diagnostic/report reads hide the original outcome. Keep application state explicit rather than relying on persistent interpreter globals.

From the copied project:

```powershell
py -3 .agents/scripts/watch_fusion.py 'Output CAD\build.log' --run-id RUN_ID --deadline 600 --startup 60 --stale 120
```

Choose deadlines from expected work and arrange tool polling to keep the user informed. The helper uses monotonic elapsed time, reads incrementally, detects rotation/truncation, ignores unrelated run IDs, and bounds line buffers. Exit codes: 0 completion marker; 1 explicit failure; 2 stale; 3 no current START; 4 hard deadline; 5 invalid/unreadable log. It never kills or cancels Fusion. Rotation needs a fresh START for the same active run. A completion marker reports execution only, with `acceptance_verified=false`.

After failure, timeout or stale monitoring, inspect actual timeline, bodies, parameters, volumes and in-flight activity before another mutation. A timed-out script may continue, and earlier edits may persist after an exception. Do not repeatedly rearm the monitor or rerun a destructive stage without establishing the actual state. Use `fusion-repair` and the application-session checkpoint procedure for hangs or restart needs.

## Optional project evidence gate

Use the shared `.agents/scripts/evidence_gate.py` only when the project has agreed required criteria. Store the authored plan, current state and evidence under `Project/Context/` and link them from root `Project.md` through `project-resources`. No plan, project hooks or new constraints are installed by default. Both agents invoke the same checker before a completion claim when the indexed project policy requires it. It does not block checkpoint saves or ordinary unrelated work.

The plan owns the required ID registry, independently of editable state. A minimal plan:

```json
{
  "schema": 1,
  "revision": "document-lineage:saved-version",
  "requirements": [{
    "id": "functional-clearance",
    "kind": "local",
    "evidence": "Project/Context/clearance.json",
    "metrics": {"minimum_mm": {"min": 0.2}},
    "artifacts": []
  }]
}
```

The bound is an example, not a template clearance default. Each rule needs `kind` (`local` or `external`), an evidence path and finite metric bounds and/or required artifact names. An external criterion remains a real obligation, such as a physical test. State names the same `schema`/`revision` and every required ID exactly once:

```json
{"schema":1,"revision":"document-lineage:saved-version","tasks":{"functional-clearance":{"status":"verified","sha256":"EXACT_EVIDENCE_FILE_SHA256"}}}
```

Evidence JSON names `schema:1`, the same `revision`, `run_id`, the actual `method`, `result:"pass"`, numeric `metrics`, and `artifacts`. Each required artifact maps to a distinct project-relative `path` plus its exact byte `sha256`. For a visual criterion, require original reference and paired comparison artifacts; a generated render is not a source reference. Pending state uses `open` or `external`, never a fabricated receipt. Regenerate evidence after affected source/document changes and invalidate stale receipts.

```powershell
py -3 .agents/scripts/evidence_gate.py --project . --plan 'Project/Context/Verification-Plan.json' --state 'Project/Context/Verification-State.json'
```

Exit 0: configured evidence is consistent; 1: local work pending; 2: invalid/missing plan or state; 3: only configured external obligations remain. All nonzero outcomes remain incomplete. The checker rejects omitted/unknown criteria, malformed or nonfinite numbers, wrong revisions, modified evidence/artifacts and paths outside the project. It does not independently establish the truth of measurements, genuine consent, camera fit or a physical test. Do not present editable project records, hashes, regex source scanners, timestamps or client hooks as an independent enforcement boundary. Keep any trusted secondary-review authority outside them.

For reference-driven acceptance, load [reference comparison](reference-comparison.md). For the actual API recipes, load [helpers](helpers.md); for restart reproduction, load the [lifecycle procedure](../../application-session/references/lifecycle.md).
