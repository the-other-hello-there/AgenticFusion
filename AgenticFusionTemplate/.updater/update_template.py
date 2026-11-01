"""Update only verified template resources; preserve project data and local changes."""
import argparse
from contextlib import contextmanager, ExitStack
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
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid
import zipfile

REPOSITORY = "the-other-hello-there/AgenticFusion"
MANIFEST = ".updater/Template-Manifest.json"
LEGACY_MANIFEST = "Template-Manifest.json"
STATE = ".updater/state.json"
LEGACY_STATE = "Project/.template-update/state.json"
PRESERVE = {"FDM-Slicing.md", "Printers.json", "Review-Policy.json", ".mcp.json", "settings.json", ".codex/config.toml"}
MAX_DOWNLOAD = 32 * 1024 * 1024
ROOT_FILES = {"Fusion-Claude.bat", "Fusion-Codex.bat", "updater.bat", "Update-Template.bat", "Agentic-Fusion.md",
              "AGENTS.md", "CLAUDE.md", "DfAM.md", "FDM-Slicing.md", "Printers.json", "Independent-Review.md", "Review-Policy.json",
              "settings.json", ".mcp.json", ".gitignore"}


class UpdateError(Exception):
    pass


def digest(data):
    """Git ZIPs and Windows copies differ only in BOM/line endings; ignore those."""
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def branch_name(value):
    if (not isinstance(value, str) or not value or value == '@' or value.startswith('-') or
            any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value) or
            re.search(r'[~^:?*\[\\]', value) or '..' in value or '@{' in value or value.endswith('.') or
            any(not part or part.startswith('.') or part.endswith('.lock') for part in value.split('/'))):
        raise UpdateError('Invalid branch name')
    return value


def manifest_branch(data):
    metadata = json.loads(data.decode('utf-8-sig'))
    if not isinstance(metadata, dict):
        raise UpdateError('Invalid template branch metadata')
    value = metadata.get('branch')
    return branch_name(value) if value is not None else None


def package_path(value, legacy_metadata=False):
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
    if parts[0] == '.updater' and (len(parts) == 1 or parts[1] in {'state.json', 'update.lock', 'backups', 'incoming'}):
        raise UpdateError(f"Updater state cannot be template-managed: {value}")
    if value == MANIFEST:
        raise UpdateError("The active manifest cannot list or retire itself")
    if legacy_metadata and value == LEGACY_MANIFEST:
        return value
    if value not in ROOT_FILES and not (len(parts) > 1 and parts[0] in {".agents", ".codex", ".updater"}):
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
        manifest_branch(data)
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


def retired_fingerprints(data):
    """Known stock files removed from the template, including old manifest locations."""
    try:
        result = {}
        for entry in json.loads(data.decode('utf-8-sig')).get('retired_files', []):
            name = package_path(entry['path'], legacy_metadata=True)
            if name.casefold() in {value.casefold() for value in result}:
                raise ValueError('Duplicate retired path')
            hashes = entry['sha256']
            if not isinstance(hashes, list) or not hashes or not all(re.fullmatch(r'[0-9a-f]{64}', value) for value in hashes):
                raise ValueError('Invalid retired fingerprints')
            result[name] = set(hashes)
        return result
    except (ValueError, KeyError, TypeError, UnicodeError) as error:
        raise UpdateError(f'Invalid retired template metadata: {error}') from error


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


def list_branches():
    """List every branch, without resolving tags or downloading template archives."""
    names = set()
    for page in range(1, 101):
        entries = json.loads(download(f'https://api.github.com/repos/{REPOSITORY}/branches?per_page=100&page={page}'))
        if not isinstance(entries, list) or len(entries) > 100:
            raise UpdateError('GitHub returned an invalid branch list')
        for entry in entries:
            if not isinstance(entry, dict):
                raise UpdateError('GitHub returned an invalid branch')
            name = branch_name(entry.get('name'))
            if name in names:
                raise UpdateError('GitHub returned duplicate branches; retry the update')
            names.add(name)
        if len(entries) < 100:
            if not names:
                raise UpdateError('No branches are available')
            return sorted(names, key=lambda name: (name != 'main', name))
    raise UpdateError('Branch listing exceeded its page limit')


def preferred_branch(project):
    for location in (STATE, LEGACY_STATE, MANIFEST, LEGACY_MANIFEST):
        path = safe_path(project, location)
        if path.is_file():
            name = manifest_branch(path.read_bytes())
            if name is not None:
                return name
    return 'main'


def choose_branch(project):
    names = list_branches()
    previous = preferred_branch(project)
    default = previous if previous in names else None
    print('Available update branches:')
    for number, name in enumerate(names, 1):
        label = ' (suggested)' if name == default else ''
        print(f'  {number}. {name}{label}')
    if default is None:
        print(f'Previous branch {previous} is unavailable; choose a branch explicitly.')
    while True:
        try:
            answer = input(f'Choose a number or branch name{f" [Enter: {default}]" if default else ""}; q to cancel: ').strip()
        except (EOFError, KeyboardInterrupt) as error:
            raise UpdateError('Branch selection cancelled or input unavailable; pass --branch NAME for unattended use.') from error
        if answer.lower() in {'q', 'quit', 'cancel'}:
            raise UpdateError('Branch selection cancelled; no project files changed.')
        if not answer and default:
            return default
        if answer in names:
            return answer
        if answer.isascii() and answer.isdigit() and 1 <= int(answer) <= len(names):
            return names[int(answer) - 1]
        print('Choose a listed branch or q to cancel.')


def get_source(directory=None, branch='main'):
    if directory:
        root = Path(directory).resolve(strict=True)
        if not (root / MANIFEST).is_file() and (root / "AgenticFusionTemplate" / MANIFEST).is_file():
            root = root / "AgenticFusionTemplate"
        raw = safe_path(root, MANIFEST).read_bytes()
        manifest = load_manifest(raw)
        files = {name: safe_path(root, name).read_bytes() for name in manifest}
        revision = "local-" + digest(raw)[:12]
    else:
        branch = branch_name(branch)
        resolved = json.loads(download(f'https://api.github.com/repos/{REPOSITORY}/branches/{quote(branch, safe="")}'))
        if not isinstance(resolved, dict) or resolved.get('name') != branch or not isinstance(resolved.get('commit'), dict):
            raise UpdateError('GitHub did not return the requested branch; no fallback was used')
        revision = resolved['commit'].get('sha')
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise UpdateError("GitHub did not return a commit ID")
        archive = download(f"https://codeload.github.com/{REPOSITORY}/zip/{revision}")
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            prefix = f"AgenticFusion-{revision}/AgenticFusionTemplate/"
            members = package.infolist()
            def read(name):
                matches = [item for item in members if item.filename == prefix + name]
                if len(matches) != 1 or matches[0].file_size > 2 * 1024 * 1024 or stat.S_ISLNK(matches[0].external_attr >> 16):
                    raise UpdateError(f"Missing, duplicate or unsafe package entry: {name}. Publish the updater-capable template to the selected branch first.")
                return package.read(matches[0])
            raw = read(MANIFEST)
            manifest = load_manifest(raw)
            published_branch = manifest_branch(raw)
            if published_branch is not None and published_branch != branch:
                raise UpdateError('The downloaded manifest belongs to another branch')
            if sum(item.file_size for item in members) > MAX_DOWNLOAD:
                raise UpdateError("Expanded archive exceeds the template size limit")
            files = {name: read(name) for name in manifest}
    for name, entry in manifest.items():
        if digest(files[name]) != entry["sha256"]:
            raise UpdateError(f"Downloaded content failed verification: {name}")
    retired = retired_fingerprints(raw)
    if set(manifest).intersection(retired):
        raise UpdateError('A template file cannot be both active and retired')
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


@contextmanager
def file_lock(path):
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


@contextmanager
def update_lock(project):
    with ExitStack() as locks:
        locks.enter_context(file_lock(safe_path(project, '.updater/update.lock')))
        legacy = 'Project/.template-update/update.lock'
        if (project / legacy).is_file():
            locks.enter_context(file_lock(safe_path(project, legacy)))
        yield


def installed_baseline(project):
    for location in (STATE, LEGACY_STATE):
        if location == LEGACY_STATE and not (project / location).is_file():
            continue
        state_file = safe_path(project, location)
        if not state_file.is_file():
            continue
        state = json.loads(state_file.read_text(encoding="utf-8-sig"))
        if state.get("schema_version") != 1 or not isinstance(state.get("files"), dict):
            raise UpdateError("Invalid installed-template state")
        for name, value in state["files"].items():
            package_path(name)
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise UpdateError("Invalid installed-template state hash")
        return state["files"], True
    for location in (MANIFEST, LEGACY_MANIFEST):
        local = safe_path(project, location)
        if local.is_file():
            return {name: entry["sha256"] for name, entry in load_manifest(local.read_bytes()).items()}, False
    return {}, False


def plan_update(project, manifest, files, retired=None):
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
    for name, fingerprints in (retired or {}).items():
        if name in manifest or name in PRESERVE:
            continue
        path = safe_path(project, name)
        if not path.is_file():
            continue
        before = path.read_bytes()
        current = digest(before)
        if current in fingerprints and (name not in baseline or current == baseline[name]):
            operations[name] = (before, None)
        elif name not in preserved:
            preserved.append(name)
    return operations, conflicts, preserved, next_baseline


def apply_update(project, raw, manifest, files, revision, check=False, branch=None):
    project = Path(project).resolve(strict=True)
    published_branch = manifest_branch(raw)
    if branch is not None:
        branch = branch_name(branch)
        if published_branch is not None and published_branch != branch:
            raise UpdateError('The requested branch and source manifest disagree')
    else:
        branch = published_branch
    retired = retired_fingerprints(raw)
    if set(manifest).intersection(retired):
        raise UpdateError('A template file cannot be both active and retired')
    operations, conflicts, preserved, baseline = plan_update(project, manifest, files, retired)
    report = {"revision": revision, "status": "conflicts" if conflicts else "check" if check else "updated",
              "branch": branch, "changes": list(operations), "conflicts": conflicts, "preserved": preserved}
    if check:
        return report
    with update_lock(project):
        # Re-plan under the lock, then verify all observed bytes again before writing.
        operations, conflicts, preserved, baseline = plan_update(project, manifest, files, retired)
        report.update(changes=list(operations), conflicts=conflicts, preserved=preserved)
        run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        if conflicts:
            incoming = ".updater/incoming/" + run
            for name in conflicts:
                atomic_write(safe_path(project, incoming + "/" + name), files[name])
            report.update(status="conflicts", incoming=incoming)
            return report
        state = json.dumps({"schema_version": 1, "revision": revision, "branch": branch or preferred_branch(project),
                            "files": baseline}, indent=2).encode() + b"\n"
        for name, data in [(MANIFEST, raw), (STATE, state)]:
            path = safe_path(project, name)
            operations[name] = (path.read_bytes() if path.is_file() else None, data)
        backup = ".updater/backups/" + run
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
    parser.add_argument("--project-dir", type=Path, default=Path(__file__).resolve().parents[1])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--source", type=Path, help="Verified offline template or repository directory; no branch prompt or network")
    source.add_argument("--branch", help="Explicit GitHub branch chosen by the user; otherwise prompt")
    source.add_argument("--list-branches", action="store_true", help="List available GitHub branches as JSON without updating")
    parser.add_argument("--check", action="store_true", help="Preview without changing any project files")
    args = parser.parse_args()
    try:
        if args.list_branches:
            print(json.dumps({'branches': list_branches()}, indent=2))
            return 0
        project = args.project_dir.resolve(strict=True)
        branch = (args.branch if args.branch is not None else choose_branch(project)) if args.source is None else None
        raw, manifest, files, revision = get_source(args.source, branch=branch)
        report = apply_update(project, raw, manifest, files, revision, args.check, branch=branch)
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
