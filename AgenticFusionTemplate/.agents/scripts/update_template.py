"""Update only verified template resources; preserve project data and local changes."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
import uuid
import zipfile

REPOSITORY = "the-other-hello-there/AgenticFusion"
MANIFEST = "Template-Manifest.json"
PRESERVE = {"FDM-Slicing.md", "Printers.json", ".mcp.json", "settings.json", ".codex/config.toml"}
MAX_DOWNLOAD = 32 * 1024 * 1024
ROOT_FILES = {"Fusion-Claude.bat", "Fusion-Codex.bat", "Update-Template.bat", "Agentic-Fusion.md",
              "AGENTS.md", "CLAUDE.md", "DfAM.md", "FDM-Slicing.md", "Printers.json", "settings.json", ".mcp.json", ".gitignore"}


class UpdateError(Exception):
    pass


def digest(data):
    """Git ZIPs and Windows copies differ only in BOM/line endings; ignore those."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def package_path(value):
    if not isinstance(value, str) or not value or "\\" in value or re.search(r'[<>:"|?*\x00-\x1f]', value):
        raise UpdateError("Invalid template path")
    parts = PurePosixPath(value).parts
    if value != "/".join(parts) or any(part in {".", ".."} or part.endswith((".", " ")) for part in parts):
        raise UpdateError(f"Invalid template path: {value}")
    if any(re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) for part in parts):
        raise UpdateError(f"Reserved Windows template path: {value}")
    blocked = {".git", ".local", ".claude", ".credentials.json", ".claude.json", "auth.json", "sessions", "cache", "log", "__pycache__"}
    if any(part.casefold() in blocked for part in parts) or parts[0].casefold() == "project":
        raise UpdateError(f"Project/account path cannot be template-managed: {value}")
    if value not in ROOT_FILES and not (len(parts) > 1 and parts[0] in {".agents", ".codex"}):
        raise UpdateError(f"Path is outside template resources: {value}")
    return value


def safe_path(root, relative):
    parts = PurePosixPath(relative).parts
    if not parts or any(part in {".", ".."} for part in parts) or PurePosixPath(relative).is_absolute() or "\\" in relative or ":" in relative:
        raise UpdateError(f"Unsafe relative path: {relative}")
    cursor = root
    for part in parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise UpdateError(f"Refusing filesystem link: {cursor}")
        if cursor.exists():
            tag = getattr(cursor.lstat(), "st_reparse_tag", 0)
            if tag in {0xA0000003, 0xA000000C}:  # junction/symlink, not OneDrive cloud placeholders
                raise UpdateError(f"Refusing filesystem link: {cursor}")
    return cursor


def load_manifest(data):
    try:
        manifest = json.loads(data.decode("utf-8-sig"))
        if manifest["schema_version"] != 1 or manifest["repository"] != REPOSITORY or manifest["hash_mode"] != "utf8-lf":
            raise ValueError("Unsupported template manifest")
        result = {}
        names = set()
        for entry in manifest["files"]:
            name = package_path(entry["path"])
            if name.casefold() in names or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
                raise ValueError("Duplicate path or invalid hash")
            if entry["policy"] not in {"managed", "preserve"}:
                raise ValueError("Invalid file policy")
            if not all(re.fullmatch(r"[0-9a-f]{64}", item) for item in entry.get("previous_sha256", [])):
                raise ValueError("Invalid historical hashes")
            names.add(name.casefold())
            result[name] = entry
        if not result or len(result) > 2000:
            raise ValueError("Invalid template file count")
        return result
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        raise UpdateError(f"Invalid template manifest: {error}") from error


def download(url):
    if os.name == "nt":
        # Windows builds certificate chains using its native trust store/AIA support.
        script = r'''
param([string]$Uri, [string]$Destination, [long]$Maximum)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$request = [Net.HttpWebRequest]::Create($Uri)
$request.UserAgent = 'AgenticFusion-Template-Updater'
$request.Accept = 'application/vnd.github+json'
$request.Timeout = 120000
$request.ReadWriteTimeout = 120000
$response = $null; $inputStream = $null; $outputStream = $null
try {
    $response = $request.GetResponse()
    if ($response.ContentLength -gt $Maximum) { throw 'Download exceeds the template size limit.' }
    $inputStream = $response.GetResponseStream()
    $outputStream = [IO.File]::Create($Destination)
    $buffer = New-Object byte[] 65536
    $total = 0L
    while (($count = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        $total += $count
        if ($total -gt $Maximum) { throw 'Download exceeds the template size limit.' }
        $outputStream.Write($buffer, 0, $count)
    }
} finally {
    if ($outputStream) { $outputStream.Dispose() }
    if ($inputStream) { $inputStream.Dispose() }
    if ($response) { $response.Dispose() }
}
'''
        with tempfile.TemporaryDirectory(prefix="AgenticFusion-download-") as temporary:
            root = Path(temporary)
            helper = root / "download.ps1"
            destination = root / "download.bin"
            helper.write_text(script, encoding="utf-8")
            result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                                     str(helper), url, str(destination), str(MAX_DOWNLOAD)], capture_output=True, text=True, timeout=150)
            if result.returncode:
                raise UpdateError("GitHub download failed: " + result.stderr.strip())
            return destination.read_bytes()
    request = Request(url, headers={"User-Agent": "AgenticFusion-Template-Updater", "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=120) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise UpdateError("Download exceeds the template size limit")
    return data


def get_source(directory=None):
    if directory:
        root = Path(directory).resolve(strict=True)
        if not (root / MANIFEST).is_file() and (root / "AgenticFusionTemplate" / MANIFEST).is_file():
            root = root / "AgenticFusionTemplate"
        raw = safe_path(root, MANIFEST).read_bytes()
        manifest = load_manifest(raw)
        files = {name: safe_path(root, name).read_bytes() for name in manifest}
        revision = "local-" + digest(raw)[:12]
    else:
        revision = json.loads(download(f"https://api.github.com/repos/{REPOSITORY}/commits/main"))["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise UpdateError("GitHub did not return a commit ID")
        archive = download(f"https://codeload.github.com/{REPOSITORY}/zip/{revision}")
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            prefix = f"AgenticFusion-{revision}/AgenticFusionTemplate/"
            members = package.infolist()
            def read(name):
                matches = [item for item in members if item.filename == prefix + name]
                if len(matches) != 1 or matches[0].file_size > 2 * 1024 * 1024 or stat.S_ISLNK(matches[0].external_attr >> 16):
                    raise UpdateError(f"Missing, duplicate or unsafe package entry: {name}. Publish the updater-capable template to main first.")
                return package.read(matches[0])
            raw = read(MANIFEST)
            manifest = load_manifest(raw)
            if sum(item.file_size for item in members) > MAX_DOWNLOAD:
                raise UpdateError("Expanded archive exceeds the template size limit")
            files = {name: read(name) for name in manifest}
    for name, entry in manifest.items():
        if digest(files[name]) != entry["sha256"]:
            raise UpdateError(f"Downloaded content failed verification: {name}")
    return raw, manifest, files, revision


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".agentic-update-" + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def initialize_resources(project):
    helper = Path(__file__).with_name("project-resources.ps1")
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
                             str(helper), "-Action", "Initialize", "-ProjectDir", str(project)], capture_output=True, text=True)
    if result.returncode:
        raise UpdateError("Cannot initialize indexed project resources: " + result.stdout + result.stderr)


@contextmanager
def update_lock(project):
    path = safe_path(project, "Project/.template-update/update.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            if os.fstat(stream.fileno()).st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise UpdateError("Another template update is running") from error
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        stream.close()


def installed_baseline(project):
    state_file = safe_path(project, "Project/.template-update/state.json")
    if state_file.is_file():
        state = json.loads(state_file.read_text(encoding="utf-8-sig"))
        if state.get("schema_version") != 1 or not isinstance(state.get("files"), dict):
            raise UpdateError("Invalid installed-template state")
        for name, value in state["files"].items():
            package_path(name)
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise UpdateError("Invalid installed-template state hash")
        return state["files"], True
    local = safe_path(project, MANIFEST)
    if local.is_file():
        return {name: entry["sha256"] for name, entry in load_manifest(local.read_bytes()).items()}, False
    return {}, False


def plan_update(project, manifest, files):
    baseline, recorded = installed_baseline(project)
    operations, conflicts, preserved = {}, [], []
    next_baseline = dict(baseline)
    for name, entry in manifest.items():
        path = safe_path(project, name)
        before = path.read_bytes() if path.is_file() else None
        if path.exists() and not path.is_file():
            raise UpdateError(f"Template file is occupied by a directory: {name}")
        if before is not None and (name in PRESERVE or entry["policy"] == "preserve"):
            preserved.append(name)
            continue
        current = digest(before) if before is not None else None
        known = {baseline[name]} if name in baseline else set()
        if not recorded:
            known.update(entry.get("previous_sha256", []))
        if before is not None and current != entry["sha256"] and current not in known:
            conflicts.append(name)
            continue
        next_baseline[name] = entry["sha256"]
        if current != entry["sha256"]:
            operations[name] = (before, files[name])
    for name, previous_hash in baseline.items():
        if name in manifest or name in PRESERVE:
            continue
        path = safe_path(project, package_path(name))
        if path.is_file():
            before = path.read_bytes()
            if digest(before) == previous_hash:
                operations[name] = (before, None)
            else:
                preserved.append(name)
        next_baseline.pop(name, None)
    return operations, conflicts, preserved, next_baseline


def apply_update(project, raw, manifest, files, revision, check=False):
    project = Path(project).resolve(strict=True)
    operations, conflicts, preserved, baseline = plan_update(project, manifest, files)
    report = {"revision": revision, "status": "conflicts" if conflicts else "check" if check else "updated",
              "changes": list(operations), "conflicts": conflicts, "preserved": preserved}
    if check:
        return report
    initialize_resources(project)
    with update_lock(project):
        # Re-plan under the lock, then verify all observed bytes again before writing.
        operations, conflicts, preserved, baseline = plan_update(project, manifest, files)
        report.update(changes=list(operations), conflicts=conflicts, preserved=preserved)
        run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        if conflicts:
            incoming = "Project/.template-update/incoming/" + run
            for name in conflicts:
                atomic_write(safe_path(project, incoming + "/" + name), files[name])
            report.update(status="conflicts", incoming=incoming)
            return report
        state = json.dumps({"schema_version": 1, "revision": revision, "files": baseline}, indent=2).encode() + b"\n"
        for name, data in [(MANIFEST, raw), ("Project/.template-update/state.json", state)]:
            path = safe_path(project, name)
            operations[name] = (path.read_bytes() if path.is_file() else None, data)
        backup = "Project/.template-update/backups/" + run
        for name, (before, after) in operations.items():
            path = safe_path(project, name)
            if (path.read_bytes() if path.is_file() else None) != before:
                raise UpdateError(f"File changed while planning; no update applied: {name}")
            if before is not None:
                atomic_write(safe_path(project, backup + "/" + name), before)
        journal = {name: {"existed": before is not None, "removed": after is None} for name, (before, after) in operations.items()}
        atomic_write(safe_path(project, backup + "/journal.json"), json.dumps(journal, indent=2).encode() + b"\n")
        written = []
        try:
            for name, (before, after) in operations.items():
                path = safe_path(project, name)
                if (path.read_bytes() if path.is_file() else None) != before:
                    raise UpdateError(f"Concurrent edit detected: {name}")
                if after is None:
                    path.unlink()
                else:
                    atomic_write(path, after)
                written.append(name)
        except Exception as error:
            held = []
            for name in reversed(written):
                before, after = operations[name]
                path = safe_path(project, name)
                if (path.read_bytes() if path.is_file() else None) != after:
                    held.append(name)
                    continue
                try:
                    if before is None:
                        path.unlink(missing_ok=True)
                    else:
                        atomic_write(path, before)
                except OSError:
                    held.append(name)
            raise UpdateError(f"Update failed; recovery copies: {backup}. Concurrent/unrestored files: {held}. {error}") from error
        report.update(status="updated", backup=backup)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source", type=Path, help="Verified offline template or repository directory")
    parser.add_argument("--check", action="store_true", help="Preview without changing any project files")
    args = parser.parse_args()
    try:
        raw, manifest, files, revision = get_source(args.source)
        report = apply_update(args.project_dir, raw, manifest, files, revision, args.check)
        print(json.dumps(report, indent=2))
        if report["conflicts"]:
            print("Local template edits were preserved. Review incoming candidates, move project-only rules into Project/, then rerun.", file=sys.stderr)
            return 2
        return 0
    except (UpdateError, OSError, ValueError, KeyError, subprocess.TimeoutExpired, zipfile.BadZipFile) as error:
        print(f"Template update stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        raise SystemExit("Template updates require Python 3.11 or newer.")
    raise SystemExit(main())
