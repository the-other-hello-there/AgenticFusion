"""Build/check the runtime fingerprint manifest from the launcher's copy allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "AgenticFusionTemplate"
MANIFEST = "Template-Manifest.json"
PRESERVE = {"FDM-Slicing.md", "Printers.json", ".mcp.json", "settings.json", ".codex/config.toml"}


def digest(data):
    return hashlib.sha256(data.removeprefix(b"\xef\xbb\xbf").replace(b"\r\n", b"\n")).hexdigest()


def build(include_history=True):
    launcher = (PACKAGE / "Fusion-Claude.bat").read_text(encoding="utf-8-sig")
    block = re.search(r"\$portable = @\((.*?)\n\s*\)", launcher, re.S)
    names = sorted(value.replace("\\", "/") for value in re.findall(r"'([^']+)'", block[1]) if value != MANIFEST)
    history = {}
    if include_history:
        try:
            previous = json.loads(subprocess.check_output(["git", "show", "HEAD:AgenticFusionTemplate/" + MANIFEST], cwd=ROOT, stderr=subprocess.DEVNULL))
            history = {entry["path"]: {entry["sha256"], *entry.get("previous_sha256", [])} for entry in previous["files"]}
        except (subprocess.CalledProcessError, ValueError):
            pass
    entries = []
    for name in names:
        prior = history.get(name, set()).copy()
        if include_history:
            tracked = 'AgenticFusionTemplate/' + name
            revisions = subprocess.check_output(['git', 'log', '--format=%H', 'HEAD', '--', tracked], cwd=ROOT).decode().splitlines()
            for revision in revisions:
                try:
                    prior.add(digest(subprocess.check_output(["git", "show", revision + ':' + tracked], cwd=ROOT, stderr=subprocess.DEVNULL)))
                except subprocess.CalledProcessError:
                    pass  # A historical deletion has no blob to adopt.
        current = digest((PACKAGE / name).read_bytes())
        entries.append({"path": name, "sha256": current, "previous_sha256": sorted(prior - {current}),
                        "policy": "preserve" if name in PRESERVE else "managed"})
    return {"schema_version": 1, "repository": "the-other-hello-there/AgenticFusion", "hash_mode": "utf8-lf", "files": entries}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build(include_history=not args.check)
    destination = PACKAGE / MANIFEST
    if args.check:
        # Historical hashes remain valid after HEAD advances; compare current ownership/content.
        actual = json.loads(destination.read_text(encoding="utf-8-sig"))
        assert {k: v for k, v in actual.items() if k != "files"} == {k: v for k, v in expected.items() if k != "files"}
        assert [{k: v for k, v in entry.items() if k != "previous_sha256"} for entry in actual["files"]] == [
            {k: v for k, v in entry.items() if k != "previous_sha256"} for entry in expected["files"]], "Rebuild the runtime manifest after template edits"
        print("Runtime fingerprints and ownership policies are current.")
    else:
        destination.write_bytes((json.dumps(expected, indent=2) + "\n").encode())
        print(f"Recorded {len(expected['files'])} runtime fingerprints and known historical originals.")
