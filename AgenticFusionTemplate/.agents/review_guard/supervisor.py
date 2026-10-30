"""Outside-process review supervisor for Codex, Claude Code, and JSONL runtime bridges."""
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid

sys.dont_write_bytecode = True
from adapters import normalize, primary_command, probe
from core import Engine, Hold, command_call, digest, validate_policy, write_json
from evidence import packet_evidence, snapshot


def outside(path, workspace):
    resolved = Path(path).resolve()
    if resolved == workspace or workspace in resolved.parents:
        raise Hold("Controller state must be outside the primary workspace.")
    return resolved


def trusted_reviewer(command, workspace, role="Reviewer"):
    if not command:
        raise Hold("Configure an independent reviewer command with a verifiable charge ceiling.")
    for argument in command:
        candidate = Path(argument)
        if candidate.is_file() and (candidate.resolve() == workspace or workspace in candidate.resolve().parents):
            raise Hold(f"{role} code must be outside the primary writable workspace.")


def reader(stream, messages, kind):
    try:
        for line in stream:
            messages.put((kind, line))
    finally:
        messages.put((kind, None))


def stop_process(process):
    if process.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def authorize_exception(workspace, state, statement_file):
    """Operator-only control path. It never resets spending, attempts or original requirements."""
    workspace = Path(workspace).resolve(strict=True)
    state = outside(state, workspace)
    statement_file = outside(statement_file, workspace)
    statement = statement_file.read_text(encoding="utf-8-sig").strip()
    if not statement:
        raise Hold("An explicit user exception statement is required.")
    authority_file, ledger_file = state / "authority.json", state / "ledger.json"
    authority = json.loads(authority_file.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
    old_hash = digest(authority)
    if ledger["task_hash"] != old_hash:
        raise Hold("Controller authority and ledger do not match; do not reset accounting.")
    if statement not in authority["user_exceptions"]:
        authority["user_exceptions"].append(statement)
        ledger.setdefault("authority_history", []).append(old_hash)
        ledger["task_hash"] = digest(authority)
        # A crash between these writes produces a mismatch and fails closed on resume.
        write_json(authority_file, authority)
        write_json(ledger_file, ledger)
        with (state / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"type": "user_exception_authorized", "statement": statement,
                                     "authority_hash": ledger["task_hash"]}) + "\n")
    return {"status": "exception_recorded", "review_spending_preserved": True,
            "authority_hash": ledger["task_hash"]}


class Supervisor:
    def __init__(self, workspace, state, policy, requirements, exceptions=(), agent="codex", resume=False):
        self.workspace = Path(workspace).resolve(strict=True)
        self.state = outside(state, self.workspace)
        self.state.mkdir(parents=True, exist_ok=True)
        if (self.state / "baseline.json").exists() and not resume:
            raise Hold("Existing controller state requires explicit --resume; do not reset review spending.")
        self.agent = agent
        self.engine = Engine(self.state, policy, requirements, exceptions)
        baseline_file = self.state / "baseline.json"
        if baseline_file.exists():
            self.baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
        else:
            self.baseline = snapshot(self.workspace)
            write_json(baseline_file, self.baseline)
        self.events = []
        self.unpriced_usage = []
        self.deferred = []
        self.boundary_results = []
        self.last_boundary_digest = None
        self.coverage_gaps = set()

    def preflight(self):
        policy = self.engine.policy
        trusted_reviewer(policy.get("reviewer_command"), self.workspace)
        for name in ("primary_meter_command", "external_evidence_command", "primary_command"):
            if policy.get(name):
                trusted_reviewer(policy[name], self.workspace, name)
        if not policy.get("reviewer_enforces_charge_ceiling"):
            raise Hold("A reviewer spend-ceiling contract must be established before any model is launched.")
        if self.agent == "codex" and not policy.get("primary_meter_command"):
            raise Hold("Codex emits tokens, not provider USD/task credits; supply a trusted primary_meter_command.")
        if self.agent == "claude" and policy["unit"] != "usd" and not policy.get("primary_meter_command"):
            raise Hold("Claude's native receipt is USD. Credits require an external meter.")
        if self.agent == "custom" and not policy.get("primary_command"):
            raise Hold("A custom agent requires a trusted JSONL runtime bridge.")

    def meter(self, invocation, pid, final=False):
        command = self.engine.policy.get("primary_meter_command")
        if command:
            receipt = command_call(command, {"invocation": invocation, "pid": pid,
                                   "unit": self.engine.policy["unit"], "final": final},
                                   self.state, 15)
            self.engine.ledger.record_primary(receipt)

    def evidence(self, response):
        current = snapshot(self.workspace)
        external = None
        command = self.engine.policy.get("external_evidence_command")
        if command:
            external = command_call(command, {"workspace": str(self.workspace), "boundary_state": current["fingerprint"]},
                                    self.state, 15)
        evidence = packet_evidence(self.baseline, current, response, self.events, external)
        self.coverage_gaps.update(evidence["coverage_gaps"])
        return evidence

    def boundary(self, invocation, pid):
        try:
            self.meter(invocation, pid)
            evidence = self.evidence("")
            if not evidence["changes"] and not any(e.get("external_effect") for e in self.events):
                return
            if evidence["artifact_digest"] == self.last_boundary_digest:
                return
            result = self.engine.review(evidence, "implementation")
            result["artifact_digest"] = evidence["artifact_digest"]
            self.boundary_results.append(result)
            self.last_boundary_digest = evidence["artifact_digest"]
        except Hold as exc:
            # Lack of telemetry/budget never clears work. The final delivery gate still runs.
            self.deferred.append(str(exc))
            self.engine.event("boundary_held_or_deferred", reason=str(exc))

    def invoke_primary(self, prompt):
        invocation = str(uuid.uuid4())
        command = primary_command(self.agent, self.workspace, self.engine.policy)
        process = subprocess.Popen(command, cwd=self.workspace, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        messages = queue.Queue()
        for kind, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
            threading.Thread(target=reader, args=(stream, messages, kind), daemon=True).start()
        process.stdin.write(prompt)
        process.stdin.close()
        final_response, completed, tools, closed, tool_names = "", False, 0, set(), {}
        deadline = time.monotonic() + self.engine.policy["primary_timeout_seconds"]
        try:
            while len(closed) < 2:
                if time.monotonic() > deadline:
                    raise Hold("Primary runtime timed out; candidate output was not delivered.")
                try:
                    kind, line = messages.get(timeout=.2)
                except queue.Empty:
                    continue
                if line is None:
                    closed.add(kind)
                    continue
                if kind == "stderr":
                    # Do not expose unreviewed primary output via a second channel.
                    with (self.state / "primary-stderr.log").open("a", encoding="utf-8") as stream:
                        stream.write(line)
                    continue
                if len(line.encode()) > self.engine.policy["max_packet_bytes"]:
                    raise Hold("Primary event exceeds the evidence limit; not silently truncated.")
                try:
                    raw = json.loads(line, parse_float=Decimal)
                except ValueError as exc:
                    raise Hold("Primary runtime did not emit its documented JSONL stream.") from exc
                if not isinstance(raw, dict):
                    raise Hold("Primary runtime emitted a non-object event.")
                event = normalize(self.agent, raw, invocation, tool_names)
                event_type = event["type"]
                if event_type == "error":
                    raise Hold(event.get("message", "Primary runtime failed."))
                if event_type == "usage":
                    self.engine.ledger.record_primary(event["usage"])
                elif event_type == "unpriced_usage":
                    self.unpriced_usage.append(event)
                elif event_type == "candidate":
                    final_response = event.get("text", "")
                elif event_type == "completed":
                    final_response = event.get("text", final_response)
                    if not self.engine.policy.get("primary_meter_command"):
                        self.engine.ledger.record_primary(event["usage"])
                    completed = True
                elif event_type == "tool_completed":
                    self.events.append(event)
                    tools += 1
                    if sum(len(json.dumps(e, default=str).encode()) for e in self.events) > self.engine.policy["max_packet_bytes"]:
                        raise Hold("Tool evidence exceeded the bounded packet; no lossy approval.")
                    actual_text = json.dumps(event.get("actual_event", {}), default=str)
                    changed = snapshot(self.workspace)
                    changed_files = sum(self.baseline["files"].get(path) != changed["files"].get(path)
                                        for path in set(self.baseline["files"]) | set(changed["files"]))
                    meaningful_command = re.search(r"\b(pytest|unittest|ctest)\b|npm\s+test|cargo\s+test|git\s+commit", actual_text)
                    if tools % self.engine.policy["boundary_tool_count"] == 0 or changed_files >= 3 or meaningful_command:
                        self.boundary(invocation, process.pid)
                if self.agent == "codex" and raw.get("type") == "turn.completed":
                    completed = True
            process.wait(timeout=5)
            if process.returncode or not completed:
                raise Hold("Primary exited without a successful terminal runtime event.")
            self.meter(invocation, process.pid, final=True)
            return final_response
        finally:
            stop_process(process)
            process.stdout.close()
            process.stderr.close()

    def run(self):
        self.preflight()
        previous = self.engine.ledger.data["reviews"]
        feedback = json.dumps(previous[-1].get("findings", [])) if previous and previous[-1].get("decision") == "revise" else ""
        remaining = self.engine.policy["max_revisions"] - self.engine.ledger.data.get("revisions", 0)
        for revision in range(remaining + 1):
            # Fresh process/context: always restore original authority, never an agent summary.
            prompt = json.dumps({"authority": self.engine.authority,
                                 "instruction": "Implement the task autonomously. Independent supervisor review runs automatically. Only the real user may authorize exceptions.",
                                 "revision_feedback": feedback}, ensure_ascii=False)
            response = self.invoke_primary(prompt)
            evidence = self.evidence(response)
            last = self.boundary_results[-1] if self.boundary_results else None
            if last and last["decision"] == "revise" and last["artifact_digest"] == evidence["artifact_digest"]:
                result = last  # Already rejected work goes directly to automatic revision, not persuasion.
            else:
                result = self.engine.review(evidence, "delivery")
            if result["decision"] == "clear":
                # Never deliver a pass for stale artifacts changed during review.
                if snapshot(self.workspace)["fingerprint"] != evidence["artifact_digest"]:
                    raise Hold("Workspace changed during final review; approval is stale.")
                self.engine.event("delivery_cleared", fingerprint=result["fingerprint"])
                return response
            feedback = json.dumps({"required_revisions": result["findings"],
                                   "authority": "Original requirements remain binding. Convenience is not an exception."})
            if self.engine.ledger.data.get("revisions", 0) >= self.engine.policy["max_revisions"]:
                raise Hold("Automatic revision limit reached; the user has not approved an exception.")
            self.engine.ledger.data["revisions"] = self.engine.ledger.data.get("revisions", 0) + 1
            self.engine.ledger.save()
            self.engine.event("automatic_revision", iteration=revision + 1)
        raise Hold("Automatic revision limit reached; the user has not approved an exception.")

    def report(self, status, reason=None):
        result = {"status": status, "reason": reason, "accounting": self.engine.ledger.report(),
                  "implementation_reviews": len(self.boundary_results),
                  "deferred_or_held_boundaries": self.deferred,
                  "observed_coverage_gaps": sorted(self.coverage_gaps),
                  "unpriced_primary_usage": self.unpriced_usage,
                  "enforcement_limits": ["Same-user processes are not an OS security boundary.",
                      "Only this supervisor's delivery channel is gated; tool side effects already happened.",
                      "Independent observer required for MCP/external state; excluded files are not reviewed.",
                      "Spend prevention depends on the trusted review adapter enforcing its declared ceiling.",
                      "Project hooks alone are bypassable; normal unguarded launches are not covered."]}
        write_json(self.state / "report.json", result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("probe")
    authorize = commands.add_parser("authorize-exception")
    authorize.add_argument("--workspace", type=Path, required=True)
    authorize.add_argument("--state-dir", type=Path, required=True)
    authorize.add_argument("--statement-file", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--agent", choices=("codex", "claude", "custom"), required=True)
    run.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[2])
    run.add_argument("--requirements", type=Path, required=True)
    run.add_argument("--policy", type=Path, required=True)
    run.add_argument("--user-exceptions", type=Path)
    run.add_argument("--state-dir", type=Path)
    run.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "probe":
        print(json.dumps(probe(), indent=2))
        return 0
    if args.command == "authorize-exception":
        try:
            print(json.dumps(authorize_exception(args.workspace, args.state_dir, args.statement_file)))
            return 0
        except (Hold, OSError, ValueError, KeyError) as exc:
            print(f"EXCEPTION NOT AUTHORIZED: {exc}", file=sys.stderr)
            return 2
    supervisor = None
    try:
        workspace = args.workspace.resolve(strict=True)
        outside(args.policy, workspace)
        outside(args.requirements, workspace)
        if args.user_exceptions:
            outside(args.user_exceptions, workspace)
        policy = validate_policy(json.loads(args.policy.read_text(encoding="utf-8-sig")))
        requirements = args.requirements.read_text(encoding="utf-8-sig")
        if not requirements.strip():
            raise Hold("Original user requirements cannot be empty.")
        exceptions = json.loads(args.user_exceptions.read_text(encoding="utf-8-sig")) if args.user_exceptions else []
        if args.resume and not args.user_exceptions and args.state_dir:
            exceptions = json.loads((args.state_dir / "authority.json").read_text(encoding="utf-8"))["user_exceptions"]
        if not isinstance(exceptions, list) or not all(isinstance(item, str) and item for item in exceptions):
            raise Hold("User exceptions must be an operator-supplied string array.")
        state = args.state_dir or Path(tempfile.mkdtemp(prefix="AgenticFusion-review-"))
        supervisor = Supervisor(args.workspace, state, policy, requirements, exceptions, args.agent, args.resume)
        answer = supervisor.run()
        supervisor.report("cleared")
        print(answer)
        print(f"Independent review cleared. Report: {supervisor.state / 'report.json'}", file=sys.stderr)
        return 0
    except (Hold, OSError, ValueError, KeyError, TypeError) as exc:
        if supervisor:
            supervisor.engine.event("delivery_held", reason=str(exc))
            supervisor.report("held", str(exc))
        print(f"DELIVERY HELD: {exc}", file=sys.stderr)
        if supervisor:
            print(f"Report: {supervisor.state / 'report.json'}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
