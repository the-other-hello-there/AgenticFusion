"""Fixed secondary-verification notices. No model calls, transcript reads or credential reads."""
import argparse
from contextlib import closing, contextmanager
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
MARKS = (50, 25, 15, 10, 5)  # Remaining allowance, not context-window/token usage.
OFFER = (
    'You have objected to the approach more than once. Would you like to enable secondary agent verification? '
    'Expect increased 5-hour and weekly allowance usage from reviewer calls and possible revisions. '
    'The default reviewer spending cap is 12.5% of measured primary-task spending; that is not a subscription-allowance guarantee. '
    'Reply "Enable secondary agent verification for modeling, slicing" with your task types, or "Keep secondary agent verification off". '
    'It will stay off unless you approve.'
)
ASK_SCOPE = 'Which task types should use secondary agent verification? Reply "Enable secondary agent verification for modeling, slicing", or use "all" for every task. Nothing has been enabled.'
ENABLED = 'Secondary agent verification preferences saved for your selected tasks. Expect increased allowance usage. A configured bounded reviewer and meter are still required before verification can run.'
DISABLED = 'Secondary agent verification is off for this project. Your other saved choices are preserved.'
SETTINGS_ERROR = 'Secondary agent verification settings could not be confirmed. Check the saved preferences before continuing; no reviewer was started.'
REMINDERS = {
    window: {mark: f'The {label} allowance crossed the {mark}%-remaining reminder mark. Secondary agent verification is enabled for selected tasks in this project and can use additional allowance. You can ask to disable it or narrow its task scope.'
             for mark in MARKS}
    for window, label in [('five_hour', '5-hour'), ('weekly', 'weekly')]
}
OBJECTION = re.compile(
    r"^(?:no[,!]?\s+)?(?:i (?:object\b|disagree\b|(?:do not|don't) agree\b|(?:do not|don't) like (?:this|that|the) approach\b)|"
    r"(?:that(?:'s| is)|this is) (?:the )?(?:wrong approach\b|not (?:the (?:right|requested) approach|what i asked for)\b)|"
    r"you(?: have|'ve) misunderstood\b|(?:this|that) (?:approach|method|plan) (?:won't|will not|doesn't|does not) work\b)", re.I)
ENABLE = re.compile(r'^enable secondary agent verification for ([a-z][a-z0-9-]*(?:\s*(?:,|\band\b)\s*[a-z][a-z0-9-]*)*)(?:\s*;\s*budget=(\d+(?:\.\d+)?)%)?[.!]?$', re.I)


def direct_text(prompt):
    # Do not treat quoted examples, pasted logs/code, or forwarded messages as user objections/consent.
    text = re.sub(r'<pasted_content\b[^>]*>.*?</pasted_content>', '', prompt, flags=re.S)
    text = re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith(('>', '"', "'", '“', '‘'))).strip().replace('’', "'")


def objection(prompt):
    return any(OBJECTION.search(line.strip()) for line in direct_text(prompt).splitlines())


def windows(agent, payload):
    """Accept named native quota windows only. Never infer quotas from token counts or cost."""
    result = []
    if not isinstance(payload, dict):
        return result
    explicit = payload.get('allowance_windows')
    if isinstance(explicit, list):
        return [entry for entry in explicit if isinstance(entry, dict)]
    if agent == 'claude':
        rates = payload.get('rate_limits')
        if isinstance(rates, dict):
            for native, name in [('five_hour', 'five_hour'), ('seven_day', 'weekly')]:
                value = rates.get(native)
                if isinstance(value, dict):
                    result.append({'window': name, 'used_percent': value.get('used_percentage'), 'resets_at': value.get('resets_at')})
    elif agent == 'codex':
        source = payload.get('result', payload.get('params', payload))
        if not isinstance(source, dict):
            return result
        rates = source.get('rateLimits')
        if isinstance(rates, dict):
            for field in ('primary', 'secondary'):
                value = rates.get(field)
                if isinstance(value, dict) and value.get('windowDurationMins') in (300, 10080):
                    result.append({'window': 'five_hour' if value['windowDurationMins'] == 300 else 'weekly',
                                   'used_percent': value.get('usedPercent'), 'resets_at': value.get('resetsAt')})
    return result


def codex_snapshot(command=None, timeout=4):
    """Only initialize and read account limits. No thread/turn/model/reset/login requests."""
    executable = shutil.which('codex') if command is None else None
    if command is None and not executable:
        return {}
    process = subprocess.Popen(command or [executable, 'app-server', '--listen', 'stdio://'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    responses = queue.Queue()
    def read():
        for line in process.stdout:
            try:
                responses.put(json.loads(line))
            except ValueError:
                pass
        responses.put(None)
    threading.Thread(target=read, daemon=True).start()
    deadline = time.monotonic() + timeout
    def send(value):
        process.stdin.write(json.dumps(value) + '\n')
        process.stdin.flush()
    def receive(identifier):
        while time.monotonic() < deadline:
            try:
                value = responses.get(timeout=max(.01, deadline - time.monotonic()))
            except queue.Empty:
                return {}
            if value is None:
                return {}
            if isinstance(value, dict) and value.get('id') == identifier:
                return value.get('result', {})
        return {}
    try:
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'agentic_fusion_notices', 'version': '1.0'}}})
        if not receive(1):
            return {}
        send({'method': 'initialized'})
        send({'id': 2, 'method': 'account/rateLimits/read'})
        return receive(2)
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=.5)
        except subprocess.TimeoutExpired:
            process.terminate()  # This helper's own model-free server only.
            try:
                process.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        process.stdout.close()


class Notices:
    def __init__(self, workspace, state_root=None, preferences=None, clock=time.time):
        self.workspace = Path(workspace).resolve(strict=True)
        if preferences is None:
            from review_guard import project_preferences
            preferences = project_preferences(self.workspace)
        self.preferences = preferences
        self.clock = clock
        root = state_root or os.environ.get('AGENTIC_SECONDARY_STATE_ROOT')
        if root is None:
            base = os.environ.get('LOCALAPPDATA')
            if not base:
                raise ValueError('An external notification state root is required.')
            root = Path(base) / 'AgenticFusion/SecondaryVerification'
        root = Path(root).resolve()
        if root == self.workspace or self.workspace in root.parents:
            raise ValueError('Notification runtime state must stay outside the project.')
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / 'notices.sqlite3'
        self.key = hashlib.sha256(str(self.workspace).casefold().encode()).hexdigest()

    @contextmanager
    def state(self):
        with closing(sqlite3.connect(self.path, timeout=1)) as database:
            with database:
                database.execute('CREATE TABLE IF NOT EXISTS projects (key TEXT PRIMARY KEY, data TEXT NOT NULL)')
                database.execute('BEGIN IMMEDIATE')
                row = database.execute('SELECT data FROM projects WHERE key=?', (self.key,)).fetchone()
                value = json.loads(row[0]) if row else {'sessions': {}, 'windows': {}, 'pending': [], 'polls': {}}
                yield value
                database.execute('INSERT OR REPLACE INTO projects VALUES (?,?)', (self.key, json.dumps(value)))

    def record_objection(self, agent, session, event_id=None, prompt=''):
        if self.preferences.get('enabled') is True or not session:
            return []
        key = hashlib.sha256((agent + ':' + session).encode()).hexdigest()
        now = self.clock()
        with self.state() as state:
            entry = state['sessions'].setdefault(key, {'count': 0, 'seen': [], 'offered': False, 'pending': False})
            fingerprint = hashlib.sha256((('turn:' + str(event_id)) if event_id else ('prompt:' + prompt)).encode()).hexdigest()
            # Stable native turn IDs are exact. Without one, suppress only immediate hook retries.
            if event_id and fingerprint in entry['seen']:
                return []
            if not event_id and entry.get('last') == fingerprint and now - entry.get('at', 0) < 3:
                return []
            entry.update(last=fingerprint, at=now)
            entry['seen'] = (entry['seen'] + [fingerprint])[-100:]
            entry['count'] += 1
            state['sessions'] = dict(sorted(state['sessions'].items(), key=lambda pair: pair[1].get('at', 0))[-20:])
            if entry['count'] >= 2 and not entry['offered']:
                entry.update(offered=True, pending=True)
                return [OFFER]
        return []

    def pending_offer(self, agent, session, clear=False):
        key = hashlib.sha256((agent + ':' + session).encode()).hexdigest()
        with self.state() as state:
            entry = state['sessions'].get(key, {})
            result = entry.get('pending', False)
            if clear:
                entry['pending'] = False
            return result

    def observe(self, agent, payload):
        if self.preferences.get('enabled') is not True:
            return
        now = self.clock()
        with self.state() as state:
            for value in windows(agent, payload):
                name, reset, used = value.get('window'), value.get('resets_at'), value.get('used_percent')
                if name not in REMINDERS or type(reset) is not int or reset <= now or isinstance(used, bool):
                    continue
                try:
                    used = Decimal(str(used))
                except (InvalidOperation, ValueError):
                    continue
                if not used.is_finite() or not 0 <= used <= 100:
                    continue
                key = agent + ':' + name
                previous = state['windows'].get(key)
                if previous and reset < previous['reset']:
                    continue  # Stale/out-of-order telemetry never rearms a window.
                first = previous is None or reset > previous['reset']
                entry = {'reset': reset, 'seen': []} if first else previous
                reached = [mark for mark in MARKS if 100 - used <= mark and mark not in entry['seen']]
                entry['seen'] = sorted(set(entry['seen'] + reached), reverse=True)
                state['windows'][key] = entry
                # Attaching mid-window reports only the most urgent existing mark, not a burst of historical reminders.
                for mark in ([min(reached)] if first and reached else reached):
                    state['pending'].append({'agent': agent, 'window': name, 'reset': reset, 'message': REMINDERS[name][mark]})

    def poll_codex(self, fetch=codex_snapshot):
        if self.preferences.get('enabled') is not True:
            return
        with self.state() as state:
            now = self.clock()
            if now - state['polls'].get('codex', -1000) < 30:
                return
            state['polls']['codex'] = now
        try:
            self.observe('codex', fetch())
        except (OSError, ValueError, subprocess.SubprocessError):
            pass  # Unknown remains unknown; no token/cost-derived allowance estimate.

    def drain(self, agent):
        with self.state() as state:
            messages = [entry['message'] for entry in state['pending'] if entry['agent'] == agent and
                        entry.get('reset', 0) > self.clock() and
                        state['windows'].get(agent + ':' + entry.get('window', ''), {}).get('reset') == entry.get('reset')]
            state['pending'] = [entry for entry in state['pending'] if entry['agent'] != agent]
        return messages if self.preferences.get('enabled') is True else []


def hook(workspace, agent, payload, state_root=None, poll=True):
    if os.environ.get('AGENTIC_SECONDARY_SUPERVISED') == '1':
        return {}  # The parent supervisor owns notification display for captured primary output.
    notices = Notices(workspace, state_root)
    event = payload.get('hook_event_name')
    session = str(payload.get('session_id', ''))
    prompt = payload.get('prompt', '') if event == 'UserPromptSubmit' else ''
    if not isinstance(prompt, str):
        return {}
    if event != 'UserPromptSubmit' and notices.preferences.get('enabled') is not True:
        if notices.path.exists():
            notices.drain(agent)
        return {}
    match = ENABLE.fullmatch(prompt.strip())
    decline = re.fullmatch(r'(?:keep secondary agent verification off|disable secondary agent verification)[.!]?', prompt.strip(), re.I)
    pending = notices.pending_offer(agent, session) if notices.preferences.get('enabled') is not True and prompt.strip().lower() in {'yes', 'no', 'no thanks'} else False
    if pending and prompt.strip().lower() == 'yes':
        return {'systemMessage': ASK_SCOPE}  # Ambiguous answers still reach the ordinary work conversation.
    if pending and prompt.strip().lower() in {'no', 'no thanks'}:
        notices.pending_offer(agent, session, clear=True)
        return {'systemMessage': DISABLED}
    if match or decline:
        from review_guard import configure_project, Hold
        try:
            tasks = re.split(r'\s*(?:,|\band\b)\s*', match[1].lower()) if match else None
            configure_project(workspace, bool(match), tasks, match[2] if match else None)
            notices.pending_offer(agent, session, clear=True)
            return {'decision': 'block', 'reason': ENABLED if match else DISABLED}
        except (Hold, OSError, ValueError, subprocess.SubprocessError):
            return {'decision': 'block', 'reason': SETTINGS_ERROR}
    messages = []
    if prompt and objection(prompt):
        identifier = payload.get('turn_id') or payload.get('prompt_id') or payload.get('uuid')
        messages += notices.record_objection(agent, session, identifier, prompt)
    notices.observe(agent, payload)
    if agent == 'codex' and poll:
        notices.poll_codex()
    messages += notices.drain(agent)
    return {'systemMessage': '\n'.join(messages)} if messages else {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('hook', 'statusline', 'observe', 'objection'), default='hook')
    parser.add_argument('--agent', choices=('codex', 'claude'), required=True)
    parser.add_argument('--workspace', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--state-root', type=Path)
    parser.add_argument('--no-poll', action='store_true')
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(262145)
        if len(raw) > 262144:
            return 0
        payload = json.loads(raw, parse_float=Decimal) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0
        if args.mode == 'hook':
            result = hook(args.workspace, args.agent, payload, args.state_root, poll=not args.no_poll)
            if result:
                print(json.dumps(result))
        else:
            notices = Notices(args.workspace, args.state_root)
            if args.mode == 'objection':
                for message in notices.record_objection(args.agent, str(payload.get('session_id', '')), payload.get('turn_id')):
                    print(message)
            else:
                notices.observe(args.agent, payload)
            # Statusline is a quiet telemetry bridge; synchronous hooks display queued messages once.
        return 0
    except Exception:
        return 0  # Optional notices must never block CAD/agent work on telemetry/helper failures.


if __name__ == '__main__':
    raise SystemExit(main())
