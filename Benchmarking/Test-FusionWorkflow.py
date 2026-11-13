"""Portable log/evidence/helper tests; no model, Fusion, slicer or project writes."""
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1] / 'AgenticFusionTemplate'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, PACKAGE / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


watcher = module('watch_fusion', '.agents/scripts/watch_fusion.py')
gate = module('evidence_gate', '.agents/scripts/evidence_gate.py')
helpers = module('fusion_helpers', '.agents/skills/fusion-model/scripts/fusion_helpers.py')


class LogChecks(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='Fusion run log ')
        self.addCleanup(temp.cleanup)
        self.log = Path(temp.name) / 'run.log'
        self.time = 0

    def watch(self, change=None, **kwargs):
        def sleep(seconds):
            self.time += seconds
            if change:
                change()
        return watcher.watch(self.log, 'unique', deadline=2, startup=1, stale=.5, poll=.1,
                             clock=lambda: self.time, sleep=sleep, **kwargs)

    def test_current_run_ignores_old_completion_and_other_run(self):
        self.log.write_text('RUN old START\nRUN old DONE\nRUN unique DONE\n')
        self.assertEqual(self.watch()['status'], 'no_start')

    def test_partial_records_and_start_progress_done(self):
        self.log.write_text('RUN unique START\nRUN unique DO')
        def change():
            if self.time < .15:
                with self.log.open('a') as f:
                    f.write('NE\n')
        result = self.watch(change)
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(result['acceptance_verified'])

    def test_failure_precedes_completion_in_batch(self):
        self.log.write_text('RUN unique START\nRUN unique DONE\nRUN unique FAILED shape\n')
        self.assertEqual(self.watch()['status'], 'failed')

    def test_unrelated_growth_does_not_reset_progress(self):
        self.log.write_text('RUN unique START\n')
        def change():
            with self.log.open('a') as f:
                f.write('RUN other PROGRESS working\n')
        self.assertEqual(self.watch(change)['status'], 'stale')

    def test_continued_progress_stops_at_deadline(self):
        self.log.write_text('RUN unique START\n')
        def change():
            with self.log.open('a') as f:
                f.write('RUN unique PROGRESS working\n')
        self.assertEqual(self.watch(change)['status'], 'deadline')
        self.assertLessEqual(self.time, 2)

    def test_rotation_requires_a_new_start(self):
        self.log.write_text('RUN unique START\n')
        def change():
            if self.time < .15:
                replacement = self.log.with_suffix('.new')
                replacement.write_text('RUN unique DONE\n')
                replacement.replace(self.log)
        self.assertEqual(self.watch(change)['status'], 'no_start')

    def test_truncation_same_inode_and_later_start(self):
        self.log.write_text('RUN unique START\n' + 'x'*100 + '\n')
        def change():
            if self.time < .15:
                self.log.write_text('RUN unique START\nRUN unique DONE\n')
        self.assertEqual(self.watch(change)['status'], 'completed')

    def test_missing_log_overlong_line_and_invalid_configuration(self):
        self.assertEqual(self.watch()['status'], 'no_start')
        self.log.write_bytes(b'x'*20000)
        self.assertEqual(self.watch()['status'], 'invalid')
        for value in (float('inf'), float('nan'), -1, True):
            with self.assertRaises(ValueError):
                watcher.watch(self.log, 'unique', deadline=value)

    def test_actual_monitor_cli_returns_json_and_meaningful_exit(self):
        self.log.write_text('RUN unique START\nRUN unique DONE\n')
        result = subprocess.run([sys.executable, '-B', str(PACKAGE / '.agents/scripts/watch_fusion.py'),
                                 str(self.log), '--run-id', 'unique', '--deadline', '1'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'completed')


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='Fusion evidence ')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.context = self.root / 'Project/Context'
        self.context.mkdir(parents=True)
        self.plan = {'schema': 1, 'revision': 'lineage:7', 'requirements': [
            {'id': 'clearance', 'kind': 'local', 'evidence': 'Project/Context/check.json',
             'metrics': {'gap_mm': {'min': .2}}, 'artifacts': ['reference', 'comparison']},
            {'id': 'physical', 'kind': 'external', 'evidence': 'Project/Context/physical.json',
             'metrics': {'force_N': {'min': 1}}}]}
        self.state = {'schema': 1, 'revision': 'lineage:7', 'tasks': {
            'clearance': {'status': 'verified'}, 'physical': {'status': 'open'}}}
        self.evidence = {'schema': 1, 'revision': 'lineage:7', 'result': 'pass',
                         'run_id': 'measured-run', 'method': 'saved document readback',
                         'metrics': {'gap_mm': .3}, 'artifacts': {}}
        for name in ('reference', 'comparison'):
            path = self.context / (name + '.txt')
            path.write_text(name)
            self.evidence['artifacts'][name] = {'path': path.relative_to(self.root).as_posix(),
                                                'sha256': gate.digest(path)}

    def check(self):
        for name, value in (('plan.json', self.plan), ('state.json', self.state), ('check.json', self.evidence)):
            (self.context / name).write_text(json.dumps(value))
        self.state['tasks']['clearance']['sha256'] = gate.digest(self.context / 'check.json')
        (self.context / 'state.json').write_text(json.dumps(self.state))
        return gate.check(self.root, 'Project/Context/plan.json', 'Project/Context/state.json')

    def test_external_obligation_stays_incomplete_with_valid_local_evidence(self):
        result = self.check()
        self.assertEqual(result['status'], 'external_only')
        self.assertFalse(result['evidence_truth_verified'])

    def test_complete_configured_evidence_can_pass(self):
        self.plan['requirements'].pop()
        self.state['tasks'].pop('physical')
        self.assertEqual(self.check()['status'], 'pass')

    def test_deleted_or_unknown_required_id_is_invalid(self):
        self.state['tasks'].pop('physical')
        with self.assertRaisesRegex(ValueError, 'every required'):
            self.check()
        self.state['tasks']['physical'] = {'status': 'open'}
        self.state['tasks']['unrequested'] = {'status': 'verified'}
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_revision_boolean_missing_and_out_of_range_measurements(self):
        for change in ({'revision': 'lineage:6'}, {'metrics': {'gap_mm': True}},
                       {'metrics': {}}, {'metrics': {'gap_mm': .1}}, {'result': 'failed'}):
            original = self.evidence.copy()
            self.evidence.update(change)
            self.assertEqual(self.check()['status'], 'local_pending')
            self.evidence = original

    def test_nonfinite_metrics_and_invalid_bounds_do_not_pass(self):
        for value in (float('nan'), 10**400):
            self.evidence['metrics']['gap_mm'] = value
            self.assertEqual(self.check()['status'], 'local_pending')
        self.plan['requirements'][0]['metrics']['gap_mm'] = {'min': 1, 'max': .1}
        with self.assertRaises(ValueError):
            self.check()

    def test_external_label_cannot_waive_local_criterion(self):
        self.state['tasks']['clearance']['status'] = 'external'
        self.assertEqual(self.check()['status'], 'local_pending')

    def test_modified_artifact_and_duplicate_artifact_paths_are_rejected(self):
        (self.context / 'reference.txt').write_text('changed')
        self.assertEqual(self.check()['status'], 'local_pending')
        self.evidence['artifacts']['reference']['sha256'] = gate.digest(self.context / 'reference.txt')
        self.evidence['artifacts']['comparison'] = self.evidence['artifacts']['reference'].copy()
        self.assertEqual(self.check()['status'], 'local_pending')

    def test_evidence_modified_after_receipt_does_not_pass(self):
        self.check()
        (self.context / 'check.json').write_text(json.dumps(self.evidence) + ' ')
        result = gate.check(self.root, 'Project/Context/plan.json', 'Project/Context/state.json')
        self.assertEqual(result['status'], 'local_pending')

    def test_path_escape_and_malformed_or_duplicate_json_are_rejected(self):
        with self.assertRaises(ValueError):
            gate.project_file(self.root, '../outside.json')
        with self.assertRaises(ValueError):
            gate.project_file(self.root, '.credentials.json')
        p = self.context / 'bad.json'
        for content in ('{"schema":1,"schema":1}', '{"schema":true}', '[]', '{bad'):
            p.write_text(content)
            with self.assertRaises(ValueError):
                gate.read_json(p)

    def test_actual_evidence_cli_keeps_external_obligations_nonzero(self):
        self.check()
        result = subprocess.run([sys.executable, '-B', str(PACKAGE / '.agents/scripts/evidence_gate.py'),
                                 '--project', str(self.root), '--plan', 'Project/Context/plan.json',
                                 '--state', 'Project/Context/state.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'external_only')


class HelperChecks(unittest.TestCase):
    def test_parameter_deletion_checks_absence_and_dependency_progress(self):
        dependencies = {'base': set(), 'dependent': {'base'}, 'unrelated': set()}
        def find(name):
            if name not in dependencies:
                return None
            def delete():
                if not any(name in d for d in dependencies.values()):
                    del dependencies[name]
                return True  # Deliberately reproduce the documented success-reporting bug.
            return types.SimpleNamespace(deleteMe=delete)
        collection = types.SimpleNamespace(itemByName=find)
        with self.assertRaisesRegex(RuntimeError, 'blocked'):
            helpers.delete_selected_parameters(collection, ['base'])
        helpers.delete_selected_parameters(collection, ['dependent', 'base'])
        self.assertEqual(set(dependencies), {'unrelated'})

    def test_batch_parameter_contract_rejects_missing_or_failed_api(self):
        parameter = object()
        design = types.SimpleNamespace(allParameters=types.SimpleNamespace(itemByName=lambda n: parameter if n == 'wall' else None),
                                       modifyParameters=mock.Mock(return_value=True))
        factory = types.SimpleNamespace(createByString=lambda expression: ('expression', expression))
        helpers.batch_parameters(design, {'wall': 'thickness*2'}, factory)
        design.modifyParameters.assert_called_once_with([parameter], [('expression', 'thickness*2')])
        design.modifyParameters.return_value = False
        with self.assertRaises(RuntimeError):
            helpers.batch_parameters(design, {'wall': '2 mm'}, factory)
        with self.assertRaises(ValueError):
            helpers.batch_parameters(design, {'missing': '2 mm'}, factory)

    def test_failed_boolean_is_unknown_not_zero_volume(self):
        manager = types.SimpleNamespace(copy=lambda b: types.SimpleNamespace(volume=.01),
                                        booleanOperation=mock.Mock(return_value=False))
        with self.assertRaises(RuntimeError):
            helpers.temporary_overlap_mm3(manager, 'a', 'b', 'intersection')
        manager.booleanOperation.return_value = True
        self.assertEqual(helpers.temporary_overlap_mm3(manager, 'a', 'b', 'intersection'), 10)

    def test_sections_retain_empty_and_error_stations(self):
        manager = types.SimpleNamespace(planeIntersection=mock.Mock(side_effect=[None, RuntimeError('kernel failed')]))
        result = helpers.section_bounds_mm(manager, 'body', [(0, 'plane0'), (1, 'plane1')])
        self.assertEqual([r['status'] for r in result], ['empty', 'unknown'])
        self.assertIn('kernel failed', result[1]['error'])

    def test_surface_distances_cover_triangle_interior_edges_and_degeneracy(self):
        triangle = ((0, 0, 0), (10, 0, 0), (0, 10, 0))
        self.assertEqual(helpers.point_triangle_distance_squared((2, 2, 3), triangle), 9)
        self.assertEqual(helpers.point_triangle_distance_squared((-1, 0, 0), triangle), 1)
        self.assertEqual(helpers.point_triangle_distance_squared((0, 3, 0), ((0,0,0),)*3), 9)
        # The large triangle's centroid is far away, but its interior is nearest.
        triangles = [((0,0,0),(1000,0,0),(0,1000,0)), ((0,0,4),(1,0,4),(0,1,4))]
        result = helpers.sampled_surface_distances([(1,1,1)], triangles)
        self.assertEqual(result['maximum'], 1)
        self.assertFalse(result['continuous_equivalence_verified'])
        with self.assertRaises(ValueError):
            helpers.sampled_surface_distances([(1,1,1)], triangles, max_pairs=1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
