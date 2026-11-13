"""Check an explicitly configured project evidence plan; no CAD or model calls.

Hashes establish artifact consistency, not the truth of supplied measurements.
The plan is project policy, not a security boundary or independent AI review.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def number(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def project_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Evidence paths must be explicit project-relative files.')
    if {part.casefold() for part in Path(name).parts} & {'.credentials.json', '.claude.json', 'auth.json', '.git'}:
        raise ValueError('Account and Git metadata are not design evidence.')
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Evidence file is missing or outside the project: ' + name)
    return path


def read_json(path, raw=None):
    def invalid_constant(value):
        raise ValueError('Nonfinite JSON value: ' + value)
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    data = json.loads((path.read_bytes() if raw is None else raw).decode('utf-8-sig'), parse_constant=invalid_constant,
                      object_pairs_hook=unique_pairs)
    if not isinstance(data, dict) or type(data.get('schema')) is not int or data['schema'] != 1:
        raise ValueError('Expected an evidence schema 1 object: ' + path.name)
    return data


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect_evidence(root, rule, receipt, revision):
    faults = []
    path = project_file(root, rule['evidence'])
    blob = path.read_bytes()
    blob_hash = hashlib.sha256(blob).hexdigest()
    data = read_json(path, blob)
    if receipt.get('sha256') != blob_hash:
        faults.append('Evidence bytes do not match the recorded receipt.')
    if data.get('revision') != revision or data.get('result') != 'pass':
        faults.append('Evidence is not passing readback for the saved revision.')
    if not all(isinstance(data.get(key), str) and data[key].strip() for key in ('run_id', 'method')):
        faults.append('Evidence needs its run ID and actual measurement/review method.')
    metrics = data.get('metrics', {})
    if not isinstance(metrics, dict):
        raise ValueError('Evidence metrics must be an object.')
    for name, bounds in rule['metrics'].items():
        value = metrics.get(name)
        if not number(value):
            faults.append('Missing or nonfinite numeric metric: ' + name)
        elif ('min' in bounds and value < bounds['min']) or ('max' in bounds and value > bounds['max']):
            faults.append('Metric outside the agreed bounds: ' + name)
    artifacts = data.get('artifacts', {})
    if not isinstance(artifacts, dict):
        raise ValueError('Evidence artifacts must be an object.')
    artifact_paths = set()
    for name in rule['artifacts']:
        artifact = artifacts.get(name)
        if not isinstance(artifact, dict):
            faults.append('Missing artifact: ' + name)
            continue
        target = project_file(root, artifact.get('path'))
        if target.stat().st_size == 0 or artifact.get('sha256') != digest(target):
            faults.append('Empty or modified artifact: ' + name)
        if target in artifact_paths or target == path:
            faults.append('Distinct evidence artifacts must not reuse the same file.')
        artifact_paths.add(target)
    return faults


def check(project, plan_name, state_name):
    root = Path(project).resolve(strict=True)
    plan = read_json(project_file(root, plan_name))
    state = read_json(project_file(root, state_name))
    revision = plan.get('revision')
    if not isinstance(revision, str) or not revision.strip() or state.get('revision') != revision:
        raise ValueError('Plan/state must name the same explicit saved document revision.')
    rules, tasks = plan.get('requirements'), state.get('tasks')
    if not isinstance(rules, list) or not rules or not isinstance(tasks, dict):
        raise ValueError('The plan needs required criteria and state needs a task map.')
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get('id'), str) or not rule['id'].strip() or rule['id'] in ids:
            raise ValueError('Each required criterion needs a unique nonempty ID.')
        ids.add(rule['id'])
        if rule.get('kind') not in {'local', 'external'} or not isinstance(rule.get('evidence'), str):
            raise ValueError('Each criterion needs local/external kind and an evidence path.')
        metrics, artifacts = rule.get('metrics', {}), rule.get('artifacts', [])
        if not isinstance(metrics, dict) or not isinstance(artifacts, list) or not (metrics or artifacts):
            raise ValueError('Each criterion needs measurable bounds and/or named artifacts.')
        if any(not isinstance(a, str) or not a.strip() for a in artifacts) or len(set(artifacts)) != len(artifacts):
            raise ValueError('Artifact names must be unique nonempty strings.')
        for name, bounds in metrics.items():
            if not isinstance(bounds, dict) or not bounds or set(bounds) - {'min', 'max'} or not all(number(v) for v in bounds.values()):
                raise ValueError('Metric bounds must contain finite min/max values.')
            if bounds.get('min', -math.inf) > bounds.get('max', math.inf):
                raise ValueError('Metric bounds are reversed.')
        rule['metrics'], rule['artifacts'] = metrics, artifacts
    if set(tasks) != ids:
        raise ValueError('State must retain every required criterion, with no unknown IDs.')
    local, external = {}, {}
    for rule in rules:
        receipt = tasks[rule['id']]
        if not isinstance(receipt, dict) or receipt.get('status') not in {'open', 'verified', 'external'}:
            raise ValueError('Invalid status for criterion: ' + rule['id'])
        if receipt['status'] != 'verified':
            faults = ['Required evidence is pending.']
        else:
            try:
                faults = inspect_evidence(root, rule, receipt, revision)
            except (OSError, ValueError, TypeError, KeyError) as exc:
                faults = [str(exc)]
        if faults:
            (external if rule['kind'] == 'external' else local)[rule['id']] = faults
    status = 'local_pending' if local else 'external_only' if external else 'pass'
    return dict(status=status, revision=revision, local_pending=local, external_pending=external,
                evidence_truth_verified=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--plan', required=True)
    parser.add_argument('--state', required=True)
    args = parser.parse_args(argv)
    try:
        result = check(args.project, args.plan, args.state)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = dict(status='invalid', error=str(exc), evidence_truth_verified=False)
    print(json.dumps(result, indent=2))
    return {'pass': 0, 'local_pending': 1, 'invalid': 2, 'external_only': 3}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
