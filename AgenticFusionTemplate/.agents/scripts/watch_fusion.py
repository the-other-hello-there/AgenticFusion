"""Bounded, incremental monitoring of a uniquely identified Fusion run log."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import time

CODES = {'completed': 0, 'failed': 1, 'stale': 2, 'no_start': 3, 'deadline': 4, 'invalid': 5}


def watch(path, run_id, *, deadline, stale=120, startup=60, poll=.5,
          ok=r'^DONE$', fail=r'^(?:FAILED|ERROR|Traceback)\b', clock=time.monotonic, sleep=time.sleep):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', run_id):
        raise ValueError('Use a unique alphanumeric run ID (hyphen/underscore allowed).')
    if any(isinstance(v, bool) or not math.isfinite(v) or v <= 0 for v in (deadline, stale, startup, poll)) or poll > 60:
        raise ValueError('Timeouts must be finite positive seconds; polling must not exceed 60 seconds.')
    success, failure = re.compile(ok), re.compile(fail)
    path = Path(path)
    beginning = activity = clock()
    offset, identity, anchor, partial = 0, None, b'', b''
    started = False
    prefix = 'RUN ' + run_id + ' '

    def result(status):
        return dict(status=status, run_id=run_id, elapsed_seconds=clock() - beginning,
                    acceptance_verified=False)

    while True:
        events = []
        try:
            with path.open('rb') as stream:
                stat = os.fstat(stream.fileno())
                current = (stat.st_dev, stat.st_ino)
                stream.seek(max(0, offset - len(anchor)))
                retained = stream.read(len(anchor))
                if identity != current or stat.st_size < offset or retained != anchor:
                    offset, partial, anchor, started = 0, b'', b'', False
                    identity = current
                stream.seek(offset)
                chunk = stream.read(65536)
                offset += len(chunk)
                stream.seek(max(0, offset - 64))
                anchor = stream.read(min(offset, 64))
            lines = (partial + chunk).split(b'\n')
            partial = lines.pop()
            if len(partial) > 16384:
                return result('invalid')
            for raw in lines:
                line = raw.decode('utf-8', errors='replace').strip()
                if not line.startswith(prefix):
                    continue
                event = line[len(prefix):]
                if event == 'START':
                    started = True
                if started:
                    activity = clock()
                    events.append(event)
        except FileNotFoundError:
            pass
        except OSError:
            return result('invalid')
        # A failed record takes precedence over DONE in the same read batch.
        if any(failure.search(event) for event in events):
            return result('failed')
        if any(success.search(event) for event in events):
            return result('completed')
        elapsed = clock() - beginning
        if elapsed >= deadline:
            return result('deadline')
        if not started and elapsed >= startup:
            return result('no_start')
        if started and clock() - activity >= stale:
            return result('stale')
        sleep(min(poll, deadline - elapsed))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--deadline', type=float, required=True, help='Hard monitoring deadline in seconds')
    parser.add_argument('--stale', type=float, default=120, help='Seconds without progress for this run')
    parser.add_argument('--startup', type=float, default=60, help='Seconds to wait for this run\'s START')
    parser.add_argument('--poll', type=float, default=.5)
    parser.add_argument('--ok', default=r'^DONE$')
    parser.add_argument('--fail', default=r'^(?:FAILED|ERROR|Traceback)\b')
    args = parser.parse_args(argv)
    try:
        report = watch(args.log, args.run_id, deadline=args.deadline, stale=args.stale,
                       startup=args.startup, poll=args.poll, ok=args.ok, fail=args.fail)
    except (ValueError, re.error) as exc:
        report = dict(status='invalid', error=str(exc), acceptance_verified=False)
    print(json.dumps(report))
    return CODES[report['status']]


if __name__ == '__main__':
    raise SystemExit(main())
