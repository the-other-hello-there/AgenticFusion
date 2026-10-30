"""Translate trusted runtime events, not model-authored claims, into supervisor events."""
import json
import shutil
import subprocess

from core import Hold


def probe():
    report = {"codex": {"available": False}, "claude": {"available": False}}
    for name in report:
        executable = shutil.which(name)
        if not executable:
            continue
        try:
            version = subprocess.run([executable, "--version"], text=True, capture_output=True, timeout=15,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            command = [executable, "exec", "--help"] if name == "codex" else [executable, "--help"]
            help_result = subprocess.run(command, text=True, capture_output=True, timeout=15,
                                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            report[name] = {"available": version.returncode == 0 and help_result.returncode == 0,
                            "version": version.stdout.strip(),
                            "json_stream": "--json" in help_result.stdout if name == "codex" else "stream-json" in help_result.stdout,
                            "provider_usd_result_documented": name == "claude",
                            "live_receipt_verified": False,
                            "max_budget_usd_flag": "--max-budget-usd" in help_result.stdout,
                            "native_task_credits_verified": False,
                            "strict_per_request_charge_cap_verified": False,
                            "notes": ("Usage tokens are available; no shared credit/USD meter or exec spend cap established."
                                      if name == "codex" else
                                      "Print mode reports total_cost_usd and offers --max-budget-usd; a strict in-flight charge ceiling is not established.")}
        except (OSError, subprocess.TimeoutExpired) as exc:
            report[name] = {"available": False, "error": type(exc).__name__}
    return report


def primary_command(agent, workspace, policy):
    if policy.get("primary_command"):
        return list(policy["primary_command"])
    if agent == "codex":
        return ["codex", "exec", "--json", "--skip-git-repo-check", "--color", "never", "--cd", str(workspace), "-"]
    if agent == "claude":
        return ["claude", "--print", "--verbose", "--output-format", "stream-json",
                "--settings", str(workspace / "settings.json"),
                "--plugin-dir", str(workspace / ".agents")]
    raise Hold("Other agents need a trusted JSONL runtime adapter in primary_command.")


def normalize(agent, event, invocation, tool_names=None):
    tool_names = tool_names if tool_names is not None else {}
    if agent == "codex":
        if event.get("type") == "turn.completed":
            return {"type": "unpriced_usage", "tokens": event.get("usage"), "runtime": "codex"}
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                return {"type": "candidate", "text": item.get("text", "")}
            if item.get("type") in {"command_execution", "file_change", "mcp_tool_call", "web_search"}:
                return {"type": "tool_completed", "actual_event": item,
                        "external_effect": item.get("type") == "mcp_tool_call"}
            if item.get("type") not in {"reasoning", "todo_list", "plan", "context_compaction"}:
                return {"type": "tool_completed", "actual_event": item, "external_effect": True,
                        "unknown_runtime_item": True}
        if event.get("type") in {"turn.failed", "error"}:
            return {"type": "error", "message": "Primary Codex runtime reported failure."}
    elif agent == "claude":
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_names[block.get("id")] = block
        if event.get("type") == "result":
            if event.get("is_error"):
                return {"type": "error", "message": "Primary Claude runtime reported failure."}
            if "total_cost_usd" not in event:
                raise Hold("Claude result omitted total_cost_usd.")
            return {"type": "completed", "text": event.get("result", ""), "usage": {
                "unit": "usd", "amount": str(event["total_cost_usd"]), "quality": "provider_reported",
                "measurement_id": f"claude:{invocation}:result"}}
        if event.get("type") == "user":
            content = event.get("message", {}).get("content", [])
            if any(isinstance(block, dict) and block.get("type") == "tool_result" for block in content):
                uses = [tool_names.get(block.get("tool_use_id")) for block in content if isinstance(block, dict) and block.get("type") == "tool_result"]
                return {"type": "tool_completed", "actual_event": {"result": event, "tool_uses": uses},
                        "external_effect": any(use is None or use.get("name", "").startswith("mcp__") for use in uses)}
    else:
        # This contract must be emitted by a trusted runtime bridge, not by an LLM as text.
        if event.get("type") in {"usage", "tool_completed", "candidate", "completed", "error"}:
            return event
    return {"type": "ignored"}
