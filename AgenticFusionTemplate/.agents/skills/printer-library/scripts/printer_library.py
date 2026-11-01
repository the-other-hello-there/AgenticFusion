"""Maintain a portable printer catalog; no application or printer access. Python 3.11+."""
import argparse
from datetime import date
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

KINDS = {"machine", "machine_model", "filament", "process"}
RECORD_FIELDS = {"id", "name", "manufacturer", "model", "hardware", "evidence", "slicer", "notes"}
HARDWARE_FIELDS = {"build_volume_mm", "bed_origin", "bed_shape_mm", "nozzle_diameters_mm", "firmware",
                   "max_nozzle_temp_c", "max_bed_temp_c"}
PRIVATE_FIELDS = {"print_host", "print_host_webui", "host_type", "api_key", "password", "token",
                  "access_code", "serial_number", "serial", "ip_address", "hostname", "device_id", "user_id"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, expected, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == expected, f"{label}: missing {sorted(expected - set(value))}; unknown {sorted(set(value) - expected)}")


def text(value, label, nullable=False):
    require((nullable and value is None) or (isinstance(value, str) and bool(value.strip())), f"{label} must be nonempty text or an allowed null")


def number(value, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def check_private(value):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower()
            private = normalized in PRIVATE_FIELDS or normalized.startswith("printhost_") or any(
                word in normalized for word in ("password", "api_key", "access_token", "access_code"))
            require(not private or item in (None, "", [], {}), f"Portable records must omit nonempty connection/credential field: {key}")
            check_private(item)
    elif isinstance(value, list):
        for item in value:
            check_private(item)


def validate_record(record):
    fields(record, RECORD_FIELDS, "printer record")
    text(record["id"], "id")
    require(len(record["id"]) <= 64 and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", record["id"]), "id must use lowercase letters/digits separated by single hyphens, at most 64 characters")
    for key in ("name", "manufacturer", "model"):
        text(record[key], key, nullable=key != "name")
    hardware = record["hardware"]
    fields(hardware, HARDWARE_FIELDS, "hardware")
    volume = hardware["build_volume_mm"]
    require(volume is None or (isinstance(volume, list) and len(volume) == 3 and all(number(n, True) for n in volume)), "build_volume_mm must be null or three positive dimensions")
    for key in ("bed_origin", "firmware"):
        text(hardware[key], key, nullable=True)
    shape = hardware["bed_shape_mm"]
    require(shape is None or (isinstance(shape, list) and len(shape) >= 3 and all(
        isinstance(point, list) and len(point) == 2 and all(number(n) for n in point) for point in shape)), "bed_shape_mm must be null or an XY polygon")
    nozzles = hardware["nozzle_diameters_mm"]
    require(isinstance(nozzles, list) and all(number(n, True) for n in nozzles), "nozzle_diameters_mm must contain positive numbers")
    for key in ("max_nozzle_temp_c", "max_bed_temp_c"):
        require(hardware[key] is None or number(hardware[key], True), f"{key} must be null or positive")
    evidence = record["evidence"]
    fields(evidence, {"status", "source", "checked_on"}, "evidence")
    require(evidence["status"] in {"unverified", "user-stated", "verified"}, "Invalid evidence status")
    text(evidence["source"], "evidence source")
    if evidence["checked_on"] is not None:
        require(isinstance(evidence["checked_on"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", evidence["checked_on"]), "checked_on must be an ISO date or null")
        date.fromisoformat(evidence["checked_on"])
    require(isinstance(record["notes"], list) and all(isinstance(n, str) for n in record["notes"]), "notes must be a string array")
    slicer = record["slicer"]
    fields(slicer, {"family", "version", "required_system_presets", "presets"}, "slicer")
    require(slicer["family"] == "OrcaSlicer", "Only the OrcaSlicer preset family is supported")
    text(slicer["version"], "slicer version", nullable=True)
    require(isinstance(slicer["presets"], list) and isinstance(slicer["required_system_presets"], list), "Preset collections must be arrays")
    external = set()
    for preset in slicer["required_system_presets"]:
        fields(preset, {"type", "name"}, "required system preset")
        require(preset["type"] in KINDS, "Unsupported external preset type")
        text(preset["name"], "system preset name")
        key = (preset["type"], preset["name"])
        require(key not in external, "Duplicate required system preset")
        external.add(key)
    profiles = {}
    for preset in slicer["presets"]:
        require(isinstance(preset, dict) and preset.get("type") in KINDS, "Native presets need a supported type")
        text(preset.get("name"), "native preset name")
        key = (preset["type"], preset["name"])
        require(key not in profiles and key not in external, f"Duplicate/ambiguous preset: {key}")
        require(isinstance(preset.get("inherits", ""), str), "Native inherits must retain its string type")
        profiles[key] = preset
    for key in profiles:
        trail, node = set(), key
        while node in profiles:
            require(node not in trail, f"Preset inheritance cycle at {node}")
            trail.add(node)
            parent = profiles[node].get("inherits", "")
            if not parent:
                break
            node = (node[0], parent)
            require(node in profiles or node in external, f"Missing inheritance parent {node}; include it or declare a required system preset")
    check_private(record)
    return record


def validate_catalog(catalog):
    fields(catalog, {"schema_version", "printers"}, "catalog")
    require(type(catalog["schema_version"]) is int and catalog["schema_version"] == 1, "Unsupported schema_version")
    require(isinstance(catalog["printers"], list), "printers must be an array")
    seen = set()
    for record in catalog["printers"]:
        validate_record(record)
        require(record["id"] not in seen, f"Duplicate printer ID: {record['id']}")
        seen.add(record["id"])
    return catalog


def read_json(path):
    path = Path(path)
    require(path.name.lower() not in {".credentials.json", ".claude.json"} and
            path.resolve().name.lower() not in {".credentials.json", ".claude.json"}, "Do not read account configuration as a printer definition")
    def invalid_constant(value):
        raise ValueError(f"Invalid JSON numeric constant: {value}")
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON field: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=invalid_constant,
                      object_pairs_hook=unique_fields)


def write_json(path, value, replace=False):
    path = Path(path)
    require(replace or not path.exists(), f"Output already exists: {path}")
    payload = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".printer-library-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
        if replace:
            os.replace(temporary, path)
        else:
            # Exclusive creation also protects against an output appearing after validation.
            with path.open("xb") as stream:
                stream.write(payload)
    finally:
        Path(temporary).unlink(missing_ok=True)


def merge(catalog, records, replace=False):
    updated = {record["id"]: record for record in catalog["printers"]}
    for record in records:
        validate_record(record)
        previous = updated.get(record["id"])
        require(previous is None or previous == record or replace, f"Printer ID {record['id']} conflicts; use --replace only for an intended update")
        updated[record["id"]] = record
    return validate_catalog({"schema_version": 1, "printers": list(updated.values())})


def select(catalog, ids):
    missing = set(ids) - {record["id"] for record in catalog["printers"]}
    require(not missing, f"Unknown printer IDs: {sorted(missing)}")
    return {"schema_version": 1, "printers": [p for p in catalog["printers"] if p["id"] in ids]}


def export_presets(catalog, destination):
    validate_catalog(catalog)
    destination = Path(destination).resolve()
    require(not destination.exists(), f"Output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".printer-transfer-", dir=destination.parent))
    try:
        write_json(stage / "Printers.json", catalog)
        for record in catalog["printers"]:
            for index, preset in enumerate(record["slicer"]["presets"], start=1):
                write_json(stage / ("printer-" + record["id"]) / f"{index:03d}-{preset['type']}.json", preset)
        stage.rename(destination)
    finally:
        if stage.exists():
            require(stage.resolve().parent == destination.parent.resolve() and
                    stage.name.startswith(".printer-transfer-") and not stage.is_symlink(),
                    "Refusing cleanup outside the newly created transfer staging directory")
            shutil.rmtree(stage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[4] / "Printers.json")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    commands.add_parser("validate")
    add = commands.add_parser("add")
    add.add_argument("--record", type=Path, required=True)
    add.add_argument("--replace", action="store_true")
    transfer = commands.add_parser("import")
    transfer.add_argument("--source", type=Path, required=True)
    transfer.add_argument("--replace", action="store_true")
    for command in ("export", "export-presets"):
        export = commands.add_parser(command)
        export.add_argument("--id", action="append", required=True)
        export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        catalog = validate_catalog(read_json(args.library))
        if args.command in {"add", "import"}:
            records = [validate_record(read_json(args.record))] if args.command == "add" else validate_catalog(read_json(args.source))["printers"]
            updated = merge(catalog, records, args.replace)
            if updated != catalog:
                write_json(args.library, updated, replace=True)
            print(json.dumps({"status": "saved", "printers": len(updated["printers"])}))
        elif args.command in {"export", "export-presets"}:
            chosen = select(catalog, args.id)
            if args.command == "export":
                write_json(args.output, chosen)
            else:
                export_presets(chosen, args.output)
            print(json.dumps({"status": "exported", "printers": len(chosen["printers"]), "output": str(args.output)}))
        elif args.command == "list":
            print(json.dumps([{"id": p["id"], "name": p["name"], "evidence": p["evidence"]["status"]} for p in catalog["printers"]], indent=2))
        else:
            print(json.dumps({"status": "valid", "printers": len(catalog["printers"])}))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f"Printer library: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
