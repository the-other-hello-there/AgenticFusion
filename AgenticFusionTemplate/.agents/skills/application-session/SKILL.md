---
name: application-session
description: Close unused Fusion documents or slicer windows, checkpoint work before agent usage exhaustion, and perform context-preserving cleanup with approved application restart at the 12-hour session deadline. Shared by Codex and Claude; excludes AI-agent processes and unrelated user applications.
---

# Application lifecycle and resumable work

Read [lifecycle](references/lifecycle.md) for save/close/restart operations or a usage/deadline handoff. `Project.md` is the durable source of current work, pending tasks and restart instructions for either agent. Runtime PID/launch/deadline state belongs outside the project under `%LOCALAPPDATA%\AgenticFusion\Sessions`.

At startup, before substantial application work, after a long operation and before yielding, check:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/application-session.ps1 -Action Status
```

Register the exact live Fusion/selected-slicer process if absent; the launcher and ordinary slicer CLI do this when identity is available. Reattachment uses actual process start time, never the time the agent noticed it. AI agents are excluded. Do not close/restart other user sessions based on an executable name alone.

Close unused reference/scratch documents and temporary slicer jobs promptly through supported APIs after checking ownership and saved/intentional-discard state. Preserve active tasks, dependencies and user work. Whole-app closure needs all its documents/jobs accounted for and an idle, verified saved state. Do not kill a process, dismiss an unknown save dialog or interrupt a tool, upload, slice or print.

Checkpoint at meaningful verified milestones. At 80% of an exposed account allowance, or a client warning sooner, save/record progress and avoid long new operations. At 90%, a limit-imminent warning, or insufficient reliable budget, complete the checkpoint/cleanup/handoff and stop new mutations. Missing telemetry stays unknown; context-window capacity is a different metric. Preserve a usable checkpoint even when no warning is exposed. Client-specific telemetry pointers live only in `AGENTS.md`/`CLAUDE.md`.

The application maintenance deadline is 12 hours of real process uptime, with preparation at 11.5 hours. When due, stop starting new work in that application, save/verify it, perform full context-preserving cleanup, record pending tasks, then ask whether the named applications can safely restart. After approval, recheck idle/saved state and use the helper's graceful `Restart` action, rebind real PIDs, reconnect MCP and verify restored documents/jobs before resuming.

The watcher queues deadline status and a non-modal notice independently of the agent; it cannot invent CAD saves or task summaries while the agent is absent or out of quota. Twelve hours is a maintenance boundary, not permission to force-quit: approval, an unfinished operation or an unverifiable save can defer restart. Record the reason and keep work checkpointed. Do not claim an exact unattended hard cutoff or uninterrupted recovery from unverified state.
