"""Capture actual workspace state without trusting an agent's file list or Git ignore rules."""
import base64
import hashlib
import os
from pathlib import Path
import stat

from core import Hold, digest

EXCLUDED_DIRS = {".git", "__pycache__"}
EXCLUDED_FILES = {".credentials.json", ".claude.json"}


def snapshot(workspace, max_bytes=2_000_000, max_files=2000):
    root = Path(workspace).resolve(strict=True)
    files, total, gaps = {}, 0, []
    for current, directories, names in os.walk(root, followlinks=False):
        current = Path(current)
        for name in list(directories):
            candidate = current / name
            if name in EXCLUDED_DIRS:
                directories.remove(name)
            elif candidate.is_symlink() or getattr(candidate.lstat(), "st_reparse_tag", 0) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", -1):
                gaps.append(f"linked directory: {candidate.relative_to(root).as_posix()}")
                directories.remove(name)
        for name in sorted(names):
            if name.lower() in EXCLUDED_FILES:
                continue  # Never inspect account files.
            path = current / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                gaps.append(f"linked file: {relative}")
                continue
            before = path.stat()
            if before.st_size + total > max_bytes or len(files) >= max_files:
                raise Hold("Workspace evidence exceeds the snapshot limit; no partial snapshot is approved.")
            raw = path.read_bytes()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                gaps.append(f"file changed during capture: {relative}")
            total += len(raw)
            try:
                text = raw.decode("utf-8")
                binary = "\x00" in text
            except UnicodeDecodeError:
                binary = True
                text = None
            files[relative] = {"sha256": hashlib.sha256(raw).hexdigest(), "binary": binary,
                               "content": base64.b64encode(raw).decode() if binary else text}
    return {"files": files, "gaps": gaps, "fingerprint": digest(files),
            "excluded": [".git metadata", "__pycache__", ".credentials.json", ".claude.json"]}


def packet_evidence(baseline, current, candidate_response, tool_events, external=None):
    changes, gaps = [], list(baseline["gaps"]) + list(current["gaps"])
    for path in sorted(set(baseline["files"]) | set(current["files"])):
        before, after = baseline["files"].get(path), current["files"].get(path)
        if before == after:
            continue
        changes.append({"path": path, "before": before, "after": after})
        if (before and before["binary"]) or (after and after["binary"]):
            gaps.append(f"binary change needs a domain-specific verifier: {path}")
    external_calls = [event for event in tool_events if event.get("external_effect")]
    if external_calls and not (isinstance(external, dict) and external.get("coverage_complete") is True):
        gaps.append("External tool effects lack an independent state observer.")
    return {"changes": changes, "artifact_digest": current["fingerprint"],
            "candidate_response": candidate_response, "tool_events": tool_events,
            "external_observation": external, "coverage_complete": not gaps, "coverage_gaps": gaps,
            "excluded_evidence": current["excluded"]}
