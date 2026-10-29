"""Portable catalog and native-preset migration regression checks."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "AgenticFusionTemplate/.agents/skills/printer-library"
spec = importlib.util.spec_from_file_location("printer_library", SKILL / "scripts/printer_library.py")
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


class PrinterChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="AgenticFusion-printers-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.catalog_file = self.folder / "project with spaces/Printers.json"
        self.catalog_file.parent.mkdir()
        self.catalog_file.write_text('{"schema_version": 1, "printers": []}', encoding="utf-8")
        self.record = json.loads((SKILL / "assets/printer.example.json").read_text(encoding="utf-8"))
        self.record.update(id="test-machine", name="Synthetic fixture, not owned hardware")
        self.record["slicer"]["presets"] = [
            {"type": "machine", "name": "Fixture base", "instantiation": "false", "nozzle_diameter": ["0.4"], "machine_start_gcode": "G28\n; preserve exactly"},
            {"type": "machine", "name": "Fixture variant", "inherits": "Fixture base", "instantiation": "true"},
            {"type": "filament", "name": "Fixture material", "compatible_printers": ["Fixture variant"], "temperature": ["210"]},
            {"type": "process", "name": "Fixture process", "layer_height": "0.2"}]

    def run_cli(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return library.main(["--library", str(self.catalog_file), *map(str, arguments)])

    def record_file(self, record=None):
        path = self.folder / "record.json"
        path.write_text(json.dumps(self.record if record is None else record), encoding="utf-8")
        return path

    def test_add_export_import_round_trip_keeps_native_types_and_gcode(self):
        self.assertEqual(self.run_cli("add", "--record", self.record_file()), 0)
        exported = self.folder / "portable.json"
        self.assertEqual(self.run_cli("export", "--id", "test-machine", "--output", exported), 0)
        self.assertEqual(json.loads(exported.read_text())["printers"], [self.record])
        self.catalog_file.write_text('{"schema_version": 1, "printers": []}')
        self.assertEqual(self.run_cli("import", "--source", exported), 0)
        self.assertEqual(json.loads(self.catalog_file.read_text())["printers"], [self.record])

    def test_conflict_does_not_modify_existing_catalog_and_replace_is_explicit(self):
        self.assertEqual(self.run_cli("add", "--record", self.record_file()), 0)
        before = self.catalog_file.read_bytes()
        self.record["name"] = "Updated fixture"
        incoming = self.record_file()
        self.assertEqual(self.run_cli("add", "--record", incoming), 1)
        self.assertEqual(before, self.catalog_file.read_bytes())
        self.assertEqual(self.run_cli("add", "--record", incoming, "--replace"), 0)
        self.assertEqual(json.loads(self.catalog_file.read_text())["printers"][0]["name"], "Updated fixture")

    def test_native_preset_export_is_copyable_and_preserves_catalog(self):
        catalog = {"schema_version": 1, "printers": [self.record]}
        output = self.folder / "transfer"
        library.export_presets(catalog, output)
        self.assertEqual(json.loads((output / "Printers.json").read_text()), catalog)
        presets = [json.loads(p.read_text()) for p in sorted((output / "printer-test-machine").glob("*.json"))]
        self.assertEqual(presets, self.record["slicer"]["presets"])
        with self.assertRaisesRegex(ValueError, "exists"):
            library.export_presets(catalog, output)
        self.assertFalse(list(self.folder.glob(".printer-transfer-*")))

    def test_export_never_overwrites_an_existing_file(self):
        output = self.folder / "keep.json"
        output.write_bytes(b"user data")
        with self.assertRaisesRegex(ValueError, "exists"):
            library.write_json(output, {})
        self.assertEqual(output.read_bytes(), b"user data")

    def test_missing_parent_requires_an_explicit_system_dependency(self):
        record = copy.deepcopy(self.record)
        record["slicer"]["presets"].pop(0)
        with self.assertRaisesRegex(ValueError, "Missing inheritance parent"):
            library.validate_record(record)
        record["slicer"]["required_system_presets"] = [{"type": "machine", "name": "Fixture base"}]
        library.validate_record(record)

    def test_inheritance_cycles_and_duplicate_printer_ids_are_rejected(self):
        record = copy.deepcopy(self.record)
        record["slicer"]["presets"][0]["inherits"] = "Fixture variant"
        with self.assertRaisesRegex(ValueError, "cycle"):
            library.validate_record(record)
        with self.assertRaisesRegex(ValueError, "Duplicate printer ID"):
            library.validate_catalog({"schema_version": 1, "printers": [self.record, self.record]})

    def test_invalid_dimensions_and_unknown_record_keys_are_rejected(self):
        for value in ([0, 200, 200], [-1, 200, 200], [True, 200, 200], [float("inf"), 200, 200]):
            record = copy.deepcopy(self.record)
            record["hardware"]["build_volume_mm"] = value
            with self.assertRaises(ValueError):
                library.validate_record(record)
        record = dict(self.record, misspelled_field="bad")
        with self.assertRaisesRegex(ValueError, "unknown"):
            library.validate_record(record)

    def test_connection_credentials_are_not_exportable(self):
        record = copy.deepcopy(self.record)
        record["slicer"]["presets"][0]["printhost_apikey"] = "synthetic-not-a-secret"
        before = self.catalog_file.read_bytes()
        self.assertEqual(self.run_cli("add", "--record", self.record_file(record)), 1)
        self.assertEqual(before, self.catalog_file.read_bytes())

    def test_account_configuration_is_rejected_before_reading(self):
        with mock.patch.object(Path, "read_text") as read, self.assertRaisesRegex(ValueError, "account configuration"):
            library.read_json(self.folder / ".credentials.json")
        read.assert_not_called()

    def test_failed_atomic_replace_leaves_existing_library_intact(self):
        before = self.catalog_file.read_bytes()
        with mock.patch.object(library.os, "replace", side_effect=OSError("simulated lock")), self.assertRaises(OSError):
            library.write_json(self.catalog_file, {"schema_version": 1, "printers": [self.record]}, replace=True)
        self.assertEqual(before, self.catalog_file.read_bytes())
        self.assertFalse(list(self.catalog_file.parent.glob(".printer-library-*")))

    def test_template_starts_empty_and_unknown_hardware_remains_unknown(self):
        template = library.validate_catalog(library.read_json(ROOT / "AgenticFusionTemplate/Printers.json"))
        self.assertEqual(template["printers"], [])
        example = library.validate_record(library.read_json(SKILL / "assets/printer.example.json"))
        self.assertIsNone(example["hardware"]["build_volume_mm"])

    def test_duplicate_json_fields_are_rejected_instead_of_silently_lost(self):
        path = self.folder / "duplicate.json"
        path.write_text('{"schema_version": 1, "schema_version": 2, "printers": []}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON field"):
            library.read_json(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
