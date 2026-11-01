"""Audit the distributable package without launching apps or generating runtime files."""
import ast
import hashlib
import json
from pathlib import Path
import re
import tomllib
import unittest

PACKAGE = Path(__file__).resolve().parents[1] / "AgenticFusionTemplate"


class PortablePackageChecks(unittest.TestCase):
    def test_update_manifest_matches_runtime_content_and_ownership(self):
        manifest = json.loads((PACKAGE / 'Template-Manifest.json').read_text(encoding='utf-8-sig'))
        expected = {path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob('*') if path.is_file()} - {'Template-Manifest.json'}
        self.assertEqual({entry['path'] for entry in manifest['files']}, expected)
        for entry in manifest['files']:
            data = (PACKAGE / entry['path']).read_bytes().removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
            self.assertEqual(entry['sha256'], hashlib.sha256(data).hexdigest(), entry['path'])
        preserved = {entry['path'] for entry in manifest['files'] if entry['policy'] == 'preserve'}
        self.assertEqual(preserved, {'FDM-Slicing.md', 'Printers.json', '.mcp.json', 'settings.json', '.codex/config.toml'})

    def test_package_matches_launcher_allowlist_and_excludes_generated_data(self):
        launcher = (PACKAGE / "Fusion-Claude.bat").read_text(encoding="utf-8-sig")
        manifest = re.search(r"\$portable = @\((.*?)\n\s*\)", launcher, re.S)
        self.assertIsNotNone(manifest, "Shared launcher must declare its portable files")
        entries = [value.replace("\\", "/") for value in re.findall(r"'([^']+)'", manifest[1])]
        self.assertEqual(len(entries), len(set(path.casefold() for path in entries)), "Duplicate portable entry")
        self.assertTrue(all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in entries))
        actual = {path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*") if path.is_file()}
        self.assertEqual(actual, set(entries), "Runtime package and copy allowlist differ; keep maintenance/generated files outside")
        blocked_names = {".credentials.json", ".claude.json", "__pycache__", ".claude", ".local", ".runs", "cache", "sessions", "log"}
        for name in actual:
            with self.subTest(path=name):
                path = Path(name)
                self.assertFalse(blocked_names.intersection(part.casefold() for part in path.parts))
                self.assertNotIn(path.suffix.lower(), {".pyc", ".pyo", ".tmp", ".bak", ".log", ".zip"})

    def test_runtime_documents_are_self_contained_and_within_context_budgets(self):
        for path in PACKAGE.rglob("*.md"):
            content = path.read_text(encoding="utf-8-sig")
            limit = 4000 if path.name in {"SKILL.md", "AGENTS.md", "CLAUDE.md"} else 15000 if path.name == "Agentic-Fusion.md" else 20000
            with self.subTest(path=path.relative_to(PACKAGE)):
                self.assertLessEqual(len(content), limit)
                for target in re.findall(r"\]\(([^)]+)\)", content):
                    if target.startswith(("https://", "http://", "#")):
                        continue
                    destination = (path.parent / target.split("#")[0]).resolve()
                    self.assertTrue(destination.is_relative_to(PACKAGE.resolve()), f"Runtime link points outside the package: {target}")
                    self.assertTrue(destination.exists(), f"Missing runtime reference: {target}")

    def test_runtime_configuration_and_python_parse_without_cache_files(self):
        counts = {".json": 0, ".toml": 0, ".py": 0}
        for path in PACKAGE.rglob("*"):
            if not path.is_file() or path.suffix not in counts:
                continue
            if path.name.casefold() in {".credentials.json", ".claude.json", "auth.json"}:
                continue  # The inventory test rejects account files; never inspect their contents.
            content = path.read_text(encoding="utf-8-sig")
            with self.subTest(path=path.relative_to(PACKAGE)):
                if path.suffix == ".json":
                    json.loads(content)
                elif path.suffix == ".toml":
                    tomllib.loads(content)
                else:
                    ast.parse(content, filename=str(path))
                counts[path.suffix] += 1
        self.assertTrue(all(counts.values()), f"Missing expected runtime resource classes: {counts}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
