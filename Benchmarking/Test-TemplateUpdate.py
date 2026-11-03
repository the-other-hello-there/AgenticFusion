"""Exercise actual update planning/transactions and native project-skill adapters in disposable copies."""
from contextlib import contextmanager
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "AgenticFusionTemplate"
SCRIPT = PACKAGE / ".updater/update_template.py"
HELPER = PACKAGE / ".agents/scripts/project-resources.ps1"
spec = importlib.util.spec_from_file_location("template_updater", SCRIPT)
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


def manifest(files, history=None, retired=None, branch=None):
    history = history or {}
    data = {"schema_version": 1, "repository": update.REPOSITORY, "hash_mode": "utf8-lf", "files": [
        {"path": name, "sha256": update.digest(value), "previous_sha256": history.get(name, []),
         "policy": "preserve" if name in update.PRESERVE else "managed"} for name, value in sorted(files.items())],
        "retired_files": [{"path": name, "sha256": hashes} for name, hashes in (retired or {}).items()]}
    if branch is not None:
        data['branch'] = branch
    raw = (json.dumps(data, indent=2) + "\n").encode()
    return raw, update.load_manifest(raw)


class UpdateChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="template update ")
        self.root = Path(self.temp.name)
        self.project = self.root / "Project with spaces"
        self.project.mkdir()
        self.old = {"Agentic-Fusion.md": b"original instructions\n", ".agents/scripts/tool.py": b"old tool\n"}
        self.new = {"Agentic-Fusion.md": b"new instructions\n", ".agents/scripts/tool.py": b"new tool\n"}
        self.write(self.old)
        self.raw_old, self.manifest_old = manifest(self.old)
        self.write({update.MANIFEST: self.raw_old})

    def tearDown(self):
        self.temp.cleanup()

    def write(self, files):
        for name, data in files.items():
            path = self.project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def apply(self, files=None, check=False, history=None, retired=None):
        files = self.new if files is None else files
        raw, entries = manifest(files, history, retired)
        return update.apply_update(self.project, raw, entries, files, "test-revision", check)

    def test_updates_pristine_files_preserves_project_settings_and_added_skills(self):
        personal = {"Project.md": b"verified dimensions and decisions", "Project/Context/loads.md": b"measured loads",
                    "Project/skills/project-fit/SKILL.md": b"canonical procedure", ".agents/skills/extra/SKILL.md": b"existing project skill",
                    "Printers.json": b'{"printers":["mine"]}', "FDM-Slicing.md": b"user preferences", ".mcp.json": b"custom MCP",
                    "settings.json": b"custom settings", ".codex/config.toml": b"custom TOML", "Output CAD/part.step": b"CAD",
                    "Review-Policy.json": b'{"max_review_ratio":"0.12"}'}
        self.write(personal)
        source = dict(self.new, **{key: b"stock defaults" for key in update.PRESERVE})
        report = self.apply(source)
        self.assertEqual(report["status"], "updated")
        for name, data in personal.items():
            self.assertEqual((self.project / name).read_bytes(), data, name)
        for name, data in self.new.items():
            self.assertEqual((self.project / name).read_bytes(), data)
        self.assertTrue((self.project / report["backup"] / "Agentic-Fusion.md").is_file())
        current = self.apply(source)
        self.assertEqual(current["status"], "up_to_date")
        self.assertEqual(current["changes"], [])

    def test_up_to_date_preview_and_apply_are_explicit_and_do_not_write(self):
        self.apply()
        before = {path.relative_to(self.project): path.read_bytes()
                  for path in self.project.rglob("*") if path.is_file()}
        preview = self.apply(check=True)
        self.assertEqual(preview["status"], "up_to_date")
        self.assertEqual(preview["changes"], [])
        self.assertNotIn("backup", preview)
        result = self.apply()
        self.assertEqual(result["status"], "up_to_date")
        self.assertNotIn("backup", result)
        after = {path.relative_to(self.project): path.read_bytes()
                 for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_branch_switch_with_identical_files_updates_only_branch_metadata(self):
        self.apply()
        raw, entries = manifest(self.new, branch="secondary-agent-verification")
        result = update.apply_update(self.project, raw, entries, self.new, "branch-revision",
                                     branch="secondary-agent-verification")
        self.assertEqual(result["status"], "updated")
        self.assertEqual(result["changes"], [update.MANIFEST, update.STATE])
        self.assertEqual(update.preferred_branch(self.project), "secondary-agent-verification")
        current = update.apply_update(self.project, raw, entries, self.new, "branch-revision",
                                      branch="secondary-agent-verification")
        self.assertEqual(current["status"], "up_to_date")

    def test_distributed_manifest_defaults_to_its_own_branch(self):
        installed_branch = update.manifest_branch((PACKAGE / update.MANIFEST).read_bytes())
        expected = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
        self.assertEqual(installed_branch, expected)

    def test_local_edits_hold_the_whole_update_and_stage_candidates(self):
        self.write({"Agentic-Fusion.md": b"project-specific rule\n"})
        report = self.apply()
        self.assertEqual(report["status"], "conflicts")
        self.assertEqual((self.project / "Agentic-Fusion.md").read_bytes(), b"project-specific rule\n")
        self.assertEqual((self.project / ".agents/scripts/tool.py").read_bytes(), self.old[".agents/scripts/tool.py"])
        self.assertEqual((self.project / report["incoming"] / "Agentic-Fusion.md").read_bytes(), self.new["Agentic-Fusion.md"])
        self.assertEqual((self.project / update.MANIFEST).read_bytes(), self.raw_old)

    def test_unknown_file_collision_is_preserved(self):
        self.write({".agents/skills/new/SKILL.md": b"my custom skill"})
        source = dict(self.new, **{".agents/skills/new/SKILL.md": b"new upstream skill"})
        self.assertIn(".agents/skills/new/SKILL.md", self.apply(source)["conflicts"])
        self.assertEqual((self.project / ".agents/skills/new/SKILL.md").read_bytes(), b"my custom skill")

    def test_legacy_adoption_requires_known_stock_fingerprints(self):
        (self.project / update.MANIFEST).unlink()
        fingerprints = {name: [update.digest(value)] for name, value in self.old.items()}
        self.assertEqual(self.apply(history=fingerprints)["status"], "updated")
        self.write({"Agentic-Fusion.md": b"private modification"})
        self.assertEqual(self.apply(history=fingerprints)["status"], "conflicts")

    def test_preview_is_read_only_and_line_endings_are_not_a_conflict(self):
        self.write({"Agentic-Fusion.md": b"\xef\xbb\xbforiginal instructions\r\n"})
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        report = self.apply(check=True)
        self.assertFalse(report["conflicts"])
        after = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.project / "Project").exists())

    def test_only_owned_unchanged_obsolete_files_are_removed(self):
        self.write({".agents/scripts/tool.py": b"project changed obsolete tool"})
        self.apply({"Agentic-Fusion.md": b"new instructions\n"})
        self.assertEqual((self.project / ".agents/scripts/tool.py").read_bytes(), b"project changed obsolete tool")
        self.write({".agents/scripts/retired.py": b"retire me"})
        self.apply({"Agentic-Fusion.md": b"new instructions\n", ".agents/scripts/retired.py": b"retire me"})
        report = self.apply({"Agentic-Fusion.md": b"new instructions\n"})
        self.assertFalse((self.project / ".agents/scripts/retired.py").exists())
        self.assertEqual((self.project / report["backup"] / ".agents/scripts/retired.py").read_bytes(), b"retire me")

    def test_write_failure_rolls_back_updated_files_and_manifest(self):
        original = update.atomic_write
        def fail(path, data):
            if path == self.project / "Agentic-Fusion.md" and data == self.new["Agentic-Fusion.md"]:
                raise PermissionError("simulated write failure")
            original(path, data)
        with mock.patch.object(update, "atomic_write", side_effect=fail), self.assertRaisesRegex(update.UpdateError, "recovery copies"):
            self.apply()
        for name, data in self.old.items():
            self.assertEqual((self.project / name).read_bytes(), data)
        self.assertEqual((self.project / update.MANIFEST).read_bytes(), self.raw_old)

    def test_rollback_preserves_a_concurrent_user_edit(self):
        original = update.atomic_write
        def fail(path, data):
            if path == self.project / "Agentic-Fusion.md" and data == self.new["Agentic-Fusion.md"]:
                (self.project / ".agents/scripts/tool.py").write_bytes(b"user edited during update")
                raise PermissionError("simulated concurrent failure")
            original(path, data)
        with mock.patch.object(update, "atomic_write", side_effect=fail), self.assertRaisesRegex(update.UpdateError, "tool.py"):
            self.apply()
        self.assertEqual((self.project / ".agents/scripts/tool.py").read_bytes(), b"user edited during update")

    def test_bad_manifest_paths_and_case_collisions_are_rejected(self):
        for name in ["../Project.md", "Project.md", "Project/skills/x/SKILL.md", "/absolute.md", "C:/escape.md", ".agents/../escape.md", ".agents/auth.json", ".agents/NUL/tool.py"]:
            with self.subTest(name=name), self.assertRaises(update.UpdateError):
                manifest({name: b"not managed"})
        raw, _ = manifest(self.new)
        value = json.loads(raw)
        value["files"].append(dict(value["files"][0]))
        with self.assertRaises(update.UpdateError):
            update.load_manifest(json.dumps(value).encode())

    def test_exclusive_update_lock_prevents_overlapping_writes(self):
        with update.update_lock(self.project), self.assertRaises(update.UpdateError):
            self.apply()
        self.assertEqual((self.project / 'Agentic-Fusion.md').read_bytes(), self.old['Agentic-Fusion.md'])
        self.assertEqual(self.apply()['status'], 'updated')

    def test_offline_source_hash_failure_prevents_any_update(self):
        source = self.root / "source"
        source.mkdir()
        raw, _ = manifest(self.new)
        (source / update.MANIFEST).parent.mkdir(parents=True)
        (source / update.MANIFEST).write_bytes(raw)
        for name, data in self.new.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data + b"tampered")
        with self.assertRaisesRegex(update.UpdateError, "verification"):
            update.get_source(source)
        self.assertEqual((self.project / "Agentic-Fusion.md").read_bytes(), self.old["Agentic-Fusion.md"])

    def test_offline_source_reports_the_missing_manifest_listed_file(self):
        source = self.root / "incomplete source"
        source.mkdir()
        raw, _ = manifest(self.new)
        (source / update.MANIFEST).parent.mkdir(parents=True)
        (source / update.MANIFEST).write_bytes(raw)
        (source / "Agentic-Fusion.md").write_bytes(self.new["Agentic-Fusion.md"])
        with self.assertRaisesRegex(update.UpdateError, r"manifest: \.agents/scripts/tool\.py"):
            update.get_source(source)

    def test_github_download_pins_archive_to_commit_and_rejects_missing_manifest(self):
        revision = "a" * 40
        raw, _ = manifest(self.new)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            prefix = f"AgenticFusion-{revision}/AgenticFusionTemplate/"
            archive.writestr(prefix + update.MANIFEST, raw)
            for name, data in self.new.items():
                archive.writestr(prefix + name, data)
        for branch in ['main', 'feature/self-benchmarking', 'secondary-agent-verification']:
            response = json.dumps({'name': branch, 'commit': {'sha': revision}}).encode()
            with self.subTest(branch=branch), mock.patch.object(update, "download", side_effect=[response, buffer.getvalue()]) as request:
                result = update.get_source(branch=branch)
                self.assertEqual(result[3], revision)
                self.assertEqual(result[2], self.new)
                self.assertTrue(request.call_args_list[0].args[0].endswith('/branches/' + branch.replace('/', '%2F')))
                self.assertTrue(request.call_args_list[1].args[0].endswith("/" + revision))
        empty = io.BytesIO()
        with zipfile.ZipFile(empty, "w"):
            pass
        with mock.patch.object(update, "download", side_effect=[json.dumps({'name': 'main', 'commit': {"sha": revision}}).encode(), empty.getvalue()]), self.assertRaisesRegex(update.UpdateError, "Publish"):
            update.get_source()
        incomplete = io.BytesIO()
        with zipfile.ZipFile(incomplete, "w") as archive:
            prefix = f"AgenticFusion-{revision}/AgenticFusionTemplate/"
            archive.writestr(prefix + update.MANIFEST, raw)
            archive.writestr(prefix + "Agentic-Fusion.md", self.new["Agentic-Fusion.md"])
        response = json.dumps({'name': 'main', 'commit': {'sha': revision}}).encode()
        with mock.patch.object(update, "download", side_effect=[response, incomplete.getvalue()]), self.assertRaisesRegex(update.UpdateError, r"missing expected entry .*\.agents/scripts/tool\.py"):
            update.get_source()

    def test_branch_listing_is_paginated_sorted_and_validated(self):
        page = [{'name': f'feature/test-{number:03}'} for number in range(100)]
        with mock.patch.object(update, 'download', side_effect=[json.dumps(page).encode(), b'[{"name":"main"}]']) as request:
            names = update.list_branches()
            self.assertEqual(names[0], 'main')
            self.assertEqual(len(names), 101)
            self.assertTrue(request.call_args_list[1].args[0].endswith('per_page=100&page=2'))
        for response in [{}, [], [{'name': 'bad\nbranch'}], [{'name': 'main'}, {'name': 'main'}]]:
            with self.subTest(response=response), mock.patch.object(update, 'download', return_value=json.dumps(response).encode()), self.assertRaises(update.UpdateError):
                update.list_branches()

    def test_published_branch_metadata_is_checked_and_offline_source_never_downloads(self):
        revision = 'b' * 40
        raw, _ = manifest(self.new, branch='main')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            prefix = f'AgenticFusion-{revision}/AgenticFusionTemplate/'
            archive.writestr(prefix + update.MANIFEST, raw)
            for name, data in self.new.items():
                archive.writestr(prefix + name, data)
        response = json.dumps({'name': 'feature/test', 'commit': {'sha': revision}}).encode()
        with mock.patch.object(update, 'download', side_effect=[response, buffer.getvalue()]), self.assertRaisesRegex(update.UpdateError, 'another branch'):
            update.get_source(branch='feature/test')
        offline = self.root / 'offline'
        for name, data in {**self.new, update.MANIFEST: raw}.items():
            path = offline / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        with mock.patch.object(update, 'download') as download:
            result = update.get_source(offline)
        download.assert_not_called()
        self.assertEqual(update.manifest_branch(result[0]), 'main')
        self.assertEqual(update.preferred_branch(self.project), 'main')

    def test_branch_prompt_supports_names_numbers_and_saved_suggestion(self):
        names = ['main', 'secondary-agent-verification', 'feature/self-benchmarking']
        self.write({update.STATE: json.dumps({'schema_version': 1, 'branch': names[1], 'files': {}}).encode()})
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}
        for answer, expected in [('1', 'main'), ('', names[1]), (names[2], names[2])]:
            with mock.patch.object(update, 'list_branches', return_value=names), mock.patch('builtins.input', return_value=answer) as prompt, mock.patch('sys.stdout', new=io.StringIO()):
                self.assertEqual(update.choose_branch(self.project), expected)
                self.assertIn('Enter: ' + names[1], prompt.call_args.args[0])
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob('*') if p.is_file()})

    def test_missing_previous_branch_requires_a_new_explicit_choice(self):
        raw, _ = manifest(self.old, branch='feature/deleted')
        self.write({update.MANIFEST: raw})
        with mock.patch.object(update, 'list_branches', return_value=['main']), mock.patch('builtins.input', side_effect=['', 'not-found', 'main']) as prompt, mock.patch('sys.stdout', new=io.StringIO()):
            self.assertEqual(update.choose_branch(self.project), 'main')
            self.assertEqual(prompt.call_count, 3)
            self.assertNotIn('Enter:', prompt.call_args.args[0])

    def test_branch_cancellation_unavailable_input_and_network_errors_never_apply(self):
        for answer in ['q', EOFError(), KeyboardInterrupt()]:
            arguments = {'side_effect': answer} if isinstance(answer, BaseException) else {'return_value': answer}
            with self.subTest(answer=type(answer).__name__), mock.patch.object(update, 'list_branches', return_value=['main']), mock.patch('builtins.input', **arguments), mock.patch('sys.stdout', new=io.StringIO()), self.assertRaises(update.UpdateError):
                update.choose_branch(self.project)
        with mock.patch.object(update, 'list_branches', side_effect=OSError('network unavailable')), mock.patch('builtins.input') as prompt, self.assertRaises(OSError):
            update.choose_branch(self.project)
        prompt.assert_not_called()
        self.assertFalse((self.project / update.STATE).exists())

    def test_invalid_unresolved_or_mismatched_branches_do_not_fallback(self):
        for branch in ['', '../main', '-main', 'a//b', 'a@{b', 'a.lock', 'bad\x1bbranch']:
            with self.subTest(branch=branch), mock.patch.object(update, 'download') as request, self.assertRaises(update.UpdateError):
                update.get_source(branch=branch)
            request.assert_not_called()
        for response in [{'name': 'main', 'commit': {'sha': 'a' * 40}}, {'name': 'feature/test', 'commit': {'sha': 'bad'}}, []]:
            with mock.patch.object(update, 'download', return_value=json.dumps(response).encode()) as request, self.assertRaises(update.UpdateError):
                update.get_source(branch='feature/test')
            self.assertEqual(request.call_count, 1)
        raw, entries = manifest(self.new, branch='main')
        with self.assertRaisesRegex(update.UpdateError, 'disagree'):
            update.apply_update(self.project, raw, entries, self.new, 'test', branch='feature/test')
        self.assertFalse((self.project / update.STATE).exists())

    def test_success_records_branch_but_preview_conflict_and_rollback_preserve_choice(self):
        self.apply()
        original_state = (self.project / update.STATE).read_bytes()
        raw, entries = manifest({'Agentic-Fusion.md': b'branch instructions'}, branch='feature/test')
        update.apply_update(self.project, raw, entries, {'Agentic-Fusion.md': b'branch instructions'}, 'test', check=True, branch='feature/test')
        self.assertEqual((self.project / update.STATE).read_bytes(), original_state)
        self.write({'Agentic-Fusion.md': b'customized'})
        report = update.apply_update(self.project, raw, entries, {'Agentic-Fusion.md': b'branch instructions'}, 'test', branch='feature/test')
        self.assertEqual(report['status'], 'conflicts')
        self.assertEqual((self.project / update.STATE).read_bytes(), original_state)
        self.write({'Agentic-Fusion.md': self.new['Agentic-Fusion.md']})
        original = update.atomic_write
        def fail(path, data):
            if path == self.project / update.STATE and data != original_state:
                raise PermissionError('simulated branch-state failure')
            original(path, data)
        with mock.patch.object(update, 'atomic_write', side_effect=fail), self.assertRaises(update.UpdateError):
            update.apply_update(self.project, raw, entries, {'Agentic-Fusion.md': b'branch instructions'}, 'test', branch='feature/test')
        self.assertEqual((self.project / update.STATE).read_bytes(), original_state)
        self.assertEqual((self.project / 'Agentic-Fusion.md').read_bytes(), self.new['Agentic-Fusion.md'])
        report = update.apply_update(self.project, raw, entries, {'Agentic-Fusion.md': b'branch instructions'}, 'test', branch='feature/test')
        self.assertEqual(report['branch'], 'feature/test')
        self.assertEqual(update.preferred_branch(self.project), 'feature/test')

    def test_switching_between_main_and_review_preserves_project_and_review_policy(self):
        review = dict(self.new, **{'Independent-Review.md': b'review guide', 'Review-Policy.json': b'stock policy', '.agents/scripts/review_guard.py': b'review runtime'})
        policy = b'custom bounded reviewer and meter'
        self.write({'Review-Policy.json': policy, 'Project.md': b'current design', '.agents/skills/custom/SKILL.md': b'custom skill'})
        for branch, files in [('secondary-agent-verification', review), ('main', self.new), ('secondary-agent-verification', review)]:
            raw, entries = manifest(files, branch=branch)
            report = update.apply_update(self.project, raw, entries, files, 'test', branch=branch)
            self.assertEqual(report['status'], 'updated')
            self.assertEqual(update.preferred_branch(self.project), branch)
            self.assertEqual((self.project / 'Review-Policy.json').read_bytes(), policy)
            self.assertEqual((self.project / 'Project.md').read_bytes(), b'current design')
            self.assertEqual((self.project / '.agents/skills/custom/SKILL.md').read_bytes(), b'custom skill')
            self.assertEqual((self.project / '.agents/scripts/review_guard.py').exists(), branch != 'main')

    def test_cli_branch_argument_prompt_listing_and_offline_modes(self):
        raw, entries = manifest(self.new)
        for arguments, chosen in [([], 'feature/test'), (['--branch', 'main'], 'main'), (['--source', str(self.root)], None)]:
            with mock.patch('sys.argv', ['updater', '--project-dir', str(self.project), '--check', *arguments]), mock.patch.object(update, 'choose_branch', return_value='feature/test') as choose, mock.patch.object(update, 'get_source', return_value=(raw, entries, self.new, 'test')) as source, mock.patch('sys.stdout', new=io.StringIO()):
                self.assertEqual(update.main(), 0)
                self.assertEqual(source.call_args.kwargs['branch'], chosen)
                self.assertEqual(choose.call_count, 1 if not arguments else 0)
        with mock.patch('sys.argv', ['updater', '--list-branches']), mock.patch.object(update, 'list_branches', return_value=['main']) as branches, mock.patch.object(update, 'get_source') as source, mock.patch('sys.stdout', new=io.StringIO()) as output:
            self.assertEqual(update.main(), 0)
            self.assertEqual(json.loads(output.getvalue())['branches'], ['main'])
            source.assert_not_called()
        with mock.patch('sys.argv', ['updater', '--source', str(self.root), '--branch', 'main']), mock.patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit) as stopped:
            update.main()
        self.assertEqual(stopped.exception.code, 2)
        self.assertFalse((self.project / update.STATE).exists())

    def test_cli_reports_when_the_selected_branch_is_already_up_to_date(self):
        raw, entries = manifest(self.new, branch="main")
        update.apply_update(self.project, raw, entries, self.new, "revision", branch="main")
        with mock.patch("sys.argv", ["updater", "--project-dir", str(self.project), "--branch", "main"]), \
             mock.patch.object(update, "get_source", return_value=(raw, entries, self.new, "revision")), \
             mock.patch("sys.stdout", new=io.StringIO()) as output:
            self.assertEqual(update.main(), 0)
        self.assertIn("Already up to date on main.", output.getvalue())

    def test_filesystem_links_are_rejected_without_mutating_targets(self):
        external = self.root / "outside"
        external.mkdir()
        (external / "tool.py").write_bytes(b"external work")
        shutil.rmtree(self.project / ".agents/scripts")
        link = self.project / ".agents/scripts"
        if os.name == "nt":
            script = self.root / "junction.ps1"
            script.write_text("param($Link,$Target)\nNew-Item -ItemType Junction -Path $Link -Target $Target | Out-Null", encoding="utf-8")
            subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script), str(link), str(external)], check=True, capture_output=True)
        else:
            link.symlink_to(external, target_is_directory=True)
        try:
            with self.assertRaisesRegex(update.UpdateError, "link"):
                self.apply()
            self.assertEqual((external / "tool.py").read_bytes(), b"external work")
        finally:
            if os.name == "nt":
                os.rmdir(link)
            else:
                link.unlink()

    def test_old_layout_migrates_without_touching_project_content_or_old_recovery(self):
        (self.project / update.MANIFEST).unlink()
        old = {'Agentic-Fusion.md': self.old['Agentic-Fusion.md'], 'Update-Template.bat': b'old launcher',
               '.agents/scripts/update_template.py': b'old updater'}
        old_raw, _ = manifest(old)
        self.write({**old, update.LEGACY_MANIFEST: old_raw,
                    update.LEGACY_STATE: json.dumps({'schema_version': 1, 'files': {name: update.digest(data) for name, data in old.items()}}).encode(),
                    'Project.md': b'Verified project context\r\n', 'Project/Context/loads.md': b'load evidence',
                    'Project/.template-update/backups/old/recovery.txt': b'old recovery evidence'})
        fresh = {'Agentic-Fusion.md': b'new instructions\n', 'updater.bat': b'new launcher', '.updater/update_template.py': b'new updater'}
        retired = {name: [update.digest(data)] for name, data in {**old, update.LEGACY_MANIFEST: old_raw}.items() if name not in fresh}
        report = self.apply(fresh, retired=retired)
        self.assertEqual(report['status'], 'updated')
        for name in retired:
            self.assertFalse((self.project / name).exists(), name)
        self.assertTrue((self.project / update.STATE).is_file())
        self.assertTrue(report['backup'].startswith('.updater/backups/'))
        self.assertEqual((self.project / 'Project.md').read_bytes(), b'Verified project context\r\n')
        self.assertEqual((self.project / 'Project/Context/loads.md').read_bytes(), b'load evidence')
        self.assertEqual((self.project / 'Project/.template-update/backups/old/recovery.txt').read_bytes(), b'old recovery evidence')
        self.assertFalse(self.apply(fresh, check=True, retired=retired)['changes'])

    def test_customized_retired_files_and_manifest_are_preserved(self):
        (self.project / update.MANIFEST).unlink()
        old_raw, _ = manifest(self.old)
        custom_raw = old_raw.rstrip() + b'\n\n'
        self.write({update.LEGACY_MANIFEST: custom_raw, 'Update-Template.bat': b'custom old launcher'})
        retired = {update.LEGACY_MANIFEST: [update.digest(old_raw)], 'Update-Template.bat': [update.digest(b'old stock launcher')]}
        report = self.apply(retired=retired)
        self.assertEqual(report['status'], 'updated')
        self.assertEqual((self.project / update.LEGACY_MANIFEST).read_bytes(), custom_raw)
        self.assertEqual((self.project / 'Update-Template.bat').read_bytes(), b'custom old launcher')
        self.assertIn(update.LEGACY_MANIFEST, report['preserved'])

    def test_retirement_metadata_cannot_delete_project_or_updater_state(self):
        for name in ['Project.md', 'Project/Context/evidence.md', update.STATE, update.MANIFEST]:
            with self.subTest(path=name), self.assertRaises(update.UpdateError):
                self.apply(retired={name: [update.digest(b'keep this')]})

    def test_retired_fingerprint_only_removes_files_owned_by_the_old_manifest(self):
        name = ".agents/scripts/retired-tool.py"
        stock = b"old template utility"
        self.write({name: stock})
        report = self.apply(retired={name: [update.digest(stock)]})
        self.assertIn(name, report["preserved"])
        self.assertEqual((self.project / name).read_bytes(), stock)

        old_raw, _ = manifest({**self.old, name: stock})
        self.write({update.MANIFEST: old_raw, name: stock})
        (self.project / update.STATE).unlink()
        report = self.apply(retired={name: [update.digest(stock)]})
        self.assertNotIn(name, report["preserved"])
        self.assertFalse((self.project / name).exists())

    def test_update_only_runs_keep_new_metadata_out_of_project_folder(self):
        self.apply()
        self.assertFalse((self.project / 'Project').exists())
        self.assertFalse((self.project / 'Project.md').exists())
        self.assertTrue((self.project / update.STATE).is_file())

    def test_running_legacy_updater_blocks_migration(self):
        legacy_lock = self.project / 'Project/.template-update/update.lock'
        with update.file_lock(legacy_lock), self.assertRaises(update.UpdateError):
            self.apply()
        self.assertEqual((self.project / 'Agentic-Fusion.md').read_bytes(), self.old['Agentic-Fusion.md'])


@unittest.skipUnless(os.name == "nt", "Windows project registration")
class ProjectResourceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="project resources ")
        self.root = Path(self.temp.name)
        (self.root / "Project.md").write_text("# Existing design\n\nVerified dimensions: 42 mm.\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_helper(self, *arguments):
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(HELPER),
                                 "-ProjectDir", str(self.root), *arguments], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_new_skill_is_canonical_in_project_and_discoverable_without_copying_body(self):
        self.run_helper("-Action", "NewSkill", "-Name", "fits", "-Description", "Check this design's measured interfaces.")
        canonical = self.root / "Project/skills/project-fits/SKILL.md"
        text = canonical.read_text(encoding="utf-8").replace("Write the verified project-specific procedure here before using this skill.", "Measure the 42 mm interface and compare the saved tolerance.")
        canonical.write_text(text, encoding="utf-8")
        note = self.root / "Project/Context/fit evidence.md"
        note.write_text("Verified measurements.", encoding="utf-8")
        self.run_helper("-Action", "Sync")
        adapter = self.root / ".agents/skills/project-fits/SKILL.md"
        entry = adapter.read_text(encoding="utf-8")
        self.assertIn("name: project-fits", entry)
        self.assertIn("../../../Project/skills/project-fits/SKILL.md", entry)
        self.assertNotIn("Measure the 42 mm", entry)
        index = (self.root / "Project.md").read_text(encoding="utf-8")
        self.assertTrue(index.startswith("# Existing design\n\nVerified dimensions: 42 mm.\n"))
        self.assertIn("Project/skills/project-fits/SKILL.md", index)
        self.assertIn("Project/Context/fit%20evidence.md", index)
        self.run_helper("-Action", "Sync")
        self.assertEqual((self.root / "Project.md").read_text(encoding="utf-8"), index)

    def test_existing_added_skill_and_modified_adapter_are_preserved(self):
        adapter = self.root / ".agents/skills/project-fits/SKILL.md"
        adapter.parent.mkdir(parents=True)
        adapter.write_text("Existing unrelated skill", encoding="utf-8")
        self.run_helper("-Action", "NewSkill", "-Name", "fits", "-Description", "Test interfaces.")
        self.assertEqual(adapter.read_text(encoding="utf-8"), "Existing unrelated skill")
        adapter.unlink()
        self.run_helper("-Action", "Sync")
        adapter.write_text("Manually customized adapter", encoding="utf-8")
        self.run_helper("-Action", "Sync")
        self.assertEqual(adapter.read_text(encoding="utf-8"), "Manually customized adapter")

    def test_deleting_canonical_removes_only_unchanged_generated_adapter(self):
        self.run_helper("-Action", "NewSkill", "-Name", "fits", "-Description", "Test interfaces.")
        canonical = self.root / "Project/skills/project-fits/SKILL.md"
        adapter = self.root / ".agents/skills/project-fits/SKILL.md"
        extra = adapter.parent / "user-note.txt"
        extra.write_text("Preserve this addition", encoding="utf-8")
        canonical.unlink()
        self.run_helper("-Action", "Sync")
        self.assertFalse(adapter.exists())
        self.assertEqual(extra.read_text(), "Preserve this addition")

    def test_index_append_preserves_existing_encoding_and_trailing_content(self):
        before = '# Existing design\r\n\r\nVerified text with trailing spaces.  \r\n\r\n'.encode('utf-16')
        (self.root / 'Project.md').write_bytes(before)
        self.run_helper('-Action', 'Initialize')
        after = (self.root / 'Project.md').read_bytes()
        self.assertTrue(after.startswith(before))
        self.assertIn('](Project/)', after.decode('utf-16'))
        self.run_helper('-Action', 'Initialize')
        self.assertEqual((self.root / 'Project.md').read_bytes(), after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
