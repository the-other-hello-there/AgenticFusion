"""Discover, choose, open and CLI-slice with installed Orca-family/Bambu slicers.

Python 3.11+, standard library only. Discovery never starts a slicer. No printer I/O.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
import slicer_dialogs
if sys.version_info < (3, 11):
    raise SystemExit("Slicer automation needs Python 3.11 or newer.")
WINDOWS_HELPER = Path(__file__).with_name("slicer_windows.ps1")


def powershell(*args):
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(WINDOWS_HELPER), *args],
        capture_output=True, text=True, encoding="utf-8-sig", errors="replace", timeout=45,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def binary_record(value):
    path = Path(os.path.expandvars(value)).expanduser().resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".exe":
        raise ValueError(f"Slicer executable not found: {path}")
    return {"name": path.parent.name or path.stem, "executable": str(path), "source": "explicit path"}


def normalize(records):
    """Merge discovery sources, retaining package activation and distinct installs."""
    merged = []
    for record in records:
        binary, app_id = record.get("executable"), record.get("app_id")
        if not binary and not app_id:
            continue
        same = [r for r in merged if (app_id and app_id == r.get("app_id")) or
                (binary and r.get("executable") and binary.casefold() == r["executable"].casefold()
                 and not (app_id and r.get("app_id") and app_id != r["app_id"]))]
        if same:
            target = same[0]
            target["sources"] = sorted(set(target["sources"] + [record.get("source", "unknown")]))
            for key in ("app_id", "executable", "version"):
                if record.get(key):
                    target[key] = record[key]
            if app_id:
                target["name"] = record["name"]
        else:
            merged.append({**record, "sources": [record.get("source", "unknown")]})
    for record in merged:
        identity = record.get("app_id") or record["executable"]
        record["id"] = hashlib.sha256(identity.casefold().encode()).hexdigest()[:16]
        record["cli"] = "unverified" if record.get("executable") else "unavailable: package activation only"
        record["mcp"] = "unverified; not inferred from product name/version"
        record.pop("source", None)
    return sorted(merged, key=lambda r: (r["name"].casefold(), r.get("version") or "", r["id"]))


def discover(explicit=None):
    records, warnings = [], []
    if os.name == "nt":
        try:
            result = powershell()
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Windows inventory failed")
            inventory = json.loads(result.stdout)
            records.extend(inventory["applications"])
            warnings.extend(inventory["warnings"])
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            warnings.append(str(exc))
    else:
        warnings.append("Automatic system discovery supports Windows.")
    for value in (explicit, os.environ.get("ORCA_SLICER_PATH"), os.environ.get("ORCAMCP_APP_PATH")):
        if value:
            try:
                records.append(binary_record(value))
            except (ValueError, OSError) as exc:
                if value == explicit:
                    raise
                warnings.append(str(exc))
    return {"applications": normalize(records), "warnings": warnings}


def choose(applications, selected=None):
    if selected:
        matches = [app for app in applications if app["id"] == selected]
        if len(matches) != 1:
            raise ValueError("Selected slicer is no longer present. Run list and choose again.")
        return matches[0]
    if not applications:
        raise ValueError("No slicers found. Supply --executable for an unregistered portable installation.")
    if not sys.stdin.isatty():
        raise ValueError("Slicer choice required. Run list, ask the user, then pass --select ID.")
    for index, app in enumerate(applications, 1):
        print(f"{index}. {app['name']} {app.get('version') or ''} [{', '.join(app['sources'])}] "
              f"{app.get('executable') or app.get('app_id')}", file=sys.stderr)
    print("Which slicer should open? Enter a number (or q to cancel): ", end="", file=sys.stderr, flush=True)
    answer = input().strip()
    if answer.lower() == "q":
        raise ValueError("Slicer selection cancelled.")
    if not answer.isdigit() or not 1 <= int(answer) <= len(applications):
        raise ValueError("Choose a listed slicer number.")
    return applications[int(answer) - 1]


def open_app(app, file=None):
    file = Path(file).resolve(strict=True) if file else None
    if file and not file.is_file():
        raise ValueError("Open a model/project file, not a folder.")
    if os.name != "nt":
        raise ValueError("Application opening supports Windows.")
    before = slicer_dialogs.prepare()
    activation_error = None
    if app.get("app_id"):
        args = ["-AppId", app["app_id"]]
        if file:
            args.extend(["-OpenFile", str(file)])
        result = powershell(*args)
        if result.returncode == 0:
            opening = json.loads(result.stdout)
            opening['dialog_cleanup'] = slicer_dialogs.finish(app, opening, before)
            opening['pid'] = opening['dialog_cleanup'].get('main_pid') or opening.get('pid')
            return opening
        activation_error = result.stderr.strip()
        if not app.get("executable"):
            raise RuntimeError(f"Selected Store app could not open the file: {activation_error}")
    binary = Path(app["executable"])
    process = subprocess.Popen([str(binary), *([str(file)] if file else [])], cwd=binary.parent,
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    opening = {"pid": process.pid, "activation": "requested", "import_verified": False,
               "store_activation_error": activation_error}
    opening['dialog_cleanup'] = slicer_dialogs.finish(app, opening, before)
    opening['pid'] = opening['dialog_cleanup'].get('main_pid') or process.pid
    return opening


def probe(app):
    if not app.get("executable"):
        return {"flags": [], "help": "No accessible executable; use selected Store app activation/GUI."}
    binary = Path(app["executable"])
    result = subprocess.run([str(binary), "--help"], cwd=binary.parent, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=20,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    help_text = result.stdout + "\n" + result.stderr
    return {"returncode": result.returncode, "flags": sorted(set(re.findall(r"--[a-z][a-z0-9-]*", help_text))),
            "help": help_text}


def track_session(app, opening, file=None):
    """Register a real GUI PID; failed handoff identification stays explicit."""
    if not opening.get("pid"):
        return {"status": "unverified", "next": "Identify and register the selected window's actual PID."}
    script = Path(__file__).resolve().parents[3] / "scripts/application-session.ps1"
    project = Path(__file__).resolve().parents[4]
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script),
               "-Action", "Register", "-ProjectDir", str(project), "-ProcessId", str(opening["pid"]),
               "-Kind", "Slicer", "-StartMonitor"]
    if app.get("executable"):
        command.extend(["-LaunchPath", app["executable"]])
    if app.get("app_id"):
        command.extend(["-AppId", app["app_id"]])
    if file:
        command.extend(["-RestoreFile", str(Path(file).resolve())])
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8-sig", errors="replace",
                                timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Session registration failed")
        return json.loads(result.stdout)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {"status": "unverified", "error": str(exc),
                "next": "Register the actual selected window PID with application-session before further app work."}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def slice_file(app, args):
    source = args.input.resolve(strict=True)
    output = args.output.resolve()
    if not source.is_file() or source.suffix.lower() not in {".3mf", ".stl", ".obj", ".step", ".stp"}:
        raise ValueError("Select a supported model or prepared 3MF project.")
    if output.exists() or output.suffix.lower() != ".3mf":
        raise ValueError("Choose a new .3mf output path; existing results are never reused as a fresh slice.")
    if not (args.settings and args.filaments) and not (source.suffix.lower() == ".3mf" and args.embedded_profiles):
        raise ValueError("Supply verified machine/process --settings and --filaments, or confirm a prepared 3MF with --embedded-profiles.")
    flags = set(probe(app)["flags"])
    required = {"--slice", "--export-3mf"}
    for option, values in (("--load-settings", args.settings), ("--load-filaments", args.filaments)):
        if values:
            required.add(option)
    if required - flags:
        raise ValueError("This build did not advertise required CLI options: " + ", ".join(sorted(required - flags)) +
                         ". Open the chosen app and use available GUI tools; do not assume MCP support.")
    command = [app["executable"], str(source)]
    profiles = []
    for option, values in (("--load-settings", args.settings), ("--load-filaments", args.filaments)):
        if values:
            paths = [p.resolve(strict=True) for p in values]
            if any(not p.is_file() or ";" in str(p) for p in paths):
                raise ValueError("Profile paths must be files without the CLI's semicolon delimiter.")
            command.extend([option, ";".join(map(str, paths))])
            profiles.extend({"path": str(p), "sha256": sha256(p)} for p in paths)
    command.extend(["--slice", str(args.plate), "--export-3mf", str(output)])
    output.parent.mkdir(parents=True, exist_ok=True)
    job = Path(tempfile.mkdtemp(prefix="slice-", dir=output.parent))
    manifest = {"status": "failed", "slicer": app, "command": command,
                "input": str(source), "input_sha256": sha256(source), "profiles": profiles,
                "output": str(output), "log": str(job / "slice.log"), "review_required": True}
    try:
        with (job / "slice.log").open("wb") as log:
            result = subprocess.run(command, cwd=job, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=args.timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        manifest["returncode"] = result.returncode
        if result.returncode:
            raise RuntimeError(f"Slicer exited with code {result.returncode}; inspect {job / 'slice.log'}")
        if not output.is_file():
            raise RuntimeError(f"Slicer did not produce {output}; inspect {job / 'slice.log'}")
        with zipfile.ZipFile(output) as archive:
            toolpaths = [entry.filename for entry in archive.infolist()
                         if entry.filename.lower().endswith(".gcode") and entry.file_size > 0]
        if not toolpaths:
            raise RuntimeError("Output 3MF contains no nonempty G-code; slice completion is unverified.")
        manifest.update(status="toolpaths_exported", output_sha256=sha256(output), toolpaths=toolpaths)
        if not args.no_open:
            try:
                manifest["opening"] = open_app(app, output)
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
                manifest["open_error"] = str(exc)
        return manifest
    except (OSError, RuntimeError, subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        manifest["error"] = str(exc)
        raise RuntimeError(f"{exc}. Job record: {job / 'result.json'}") from exc
    finally:
        (job / "result.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "open", "probe", "slice"), nargs="?", default="open")
    parser.add_argument("--executable", help="Include an unregistered/portable executable in discovery")
    parser.add_argument("--select", help="ID from list; without it a terminal prompts before launch")
    parser.add_argument("--file", type=Path, help="Model/project to load on open")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, help="New sliced .3mf artifact")
    parser.add_argument("--settings", type=Path, action="append", default=[])
    parser.add_argument("--filaments", type=Path, action="append", default=[])
    parser.add_argument("--embedded-profiles", action="store_true")
    parser.add_argument("--plate", type=int, default=0, help="0 = all plates; positive = selected plate")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--no-open", action="store_true", help="Do not open exported slice in the selected app")
    args = parser.parse_args(argv)
    try:
        if args.action == "slice" and (not args.input or not args.output or args.plate < 0 or args.timeout < 1):
            raise ValueError("slice needs --input, --output, nonnegative --plate and positive --timeout.")
        inventory = discover(args.executable)
        if args.action == "list":
            result = inventory
        else:
            app = choose(inventory["applications"], args.select)
            if args.action == "open":
                result = {"slicer": app, **open_app(app, args.file)}
                result["lifecycle"] = track_session(app, result, args.file)
            elif args.action == "probe":
                result = {"slicer": app, **probe(app)}
            else:
                result = slice_file(app, args)
                if result.get("opening"):
                    result["lifecycle"] = track_session(app, result["opening"], args.output)
            result["discovery_warnings"] = inventory["warnings"]
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired, EOFError) as exc:
        print(f"Slicer operation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
