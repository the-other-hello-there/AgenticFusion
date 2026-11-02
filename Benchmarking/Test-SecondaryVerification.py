"""Exercise fixed notices, native quota adapters and hook replies; zero model calls."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'AgenticFusionTemplate/.agents/scripts'
sys.path.insert(0, str(SCRIPTS))
from secondary_verification import Notices, OFFER, REMINDERS, ASK_SCOPE, ENABLED, DISABLED, objection, hook, windows, codex_snapshot
from review_guard import PROJECT_VERIFICATION, project_preferences


class NoticeChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='secondary verification ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'project'
        self.workspace.mkdir()
        self.state = self.root / 'runtime'
        self.now = 1000
        self.environment = mock.patch.dict(os.environ, {'AGENTIC_SECONDARY_SUPERVISED': ''})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def notices(self, enabled=True):
        return Notices(self.workspace, self.state, preferences={'enabled': enabled}, clock=lambda: self.now)

    def sample(self, name='five_hour', used=50, reset=20000):
        return {'allowance_windows': [{'window': name, 'used_percent': used, 'resets_at': reset}]}

    def save_preferences(self, enabled):
        path = self.workspace / PROJECT_VERIFICATION
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'schema_version': 1, 'enabled': enabled, 'tasks': ['modeling'], 'budget_percent': '12.5'}))

    def event(self, number, prompt):
        return {'hook_event_name': 'UserPromptSubmit', 'session_id': 'conversation', 'turn_id': str(number), 'prompt': prompt}

    def test_second_objection_offers_once_without_enabling_or_model_context(self):
        for agent in ['codex', 'claude']:
            self.assertEqual(hook(self.workspace, agent, self.event(1, 'I disagree with this approach.'), self.state, poll=False), {})
            result = hook(self.workspace, agent, self.event(2, "That's the wrong approach."), self.state, poll=False)
            self.assertEqual(result, {'systemMessage': OFFER})
            self.assertNotIn('additionalContext', json.dumps(result))
            self.assertEqual(hook(self.workspace, agent, self.event(3, 'I disagree again.'), self.state, poll=False), {})
        self.assertFalse((self.workspace / PROJECT_VERIFICATION).exists())

    def test_turn_retries_are_deduplicated_and_new_conversations_count_separately(self):
        notices = self.notices(False)
        self.assertEqual(notices.record_objection('codex', 'session', '1'), [])
        self.assertEqual(notices.record_objection('codex', 'session', '1'), [])
        self.assertEqual(notices.record_objection('codex', 'session', '2'), [OFFER])
        self.assertEqual(notices.record_objection('codex', 'other session', '3'), [])
        self.assertEqual(notices.record_objection('codex', 'other session', '4'), [OFFER])

    def test_pasted_quoted_code_and_neutral_corrections_do_not_count(self):
        for text in ['Please make the hole 4 mm.', '> I disagree.', '```\nI object to this.\n```',
                     '<pasted_content id="1">I disagree.</pasted_content>', '"I disagree with this approach"',
                     'The user might say I disagree.', '“I disagree with this approach”', 'How does secondary agent verification work?']:
            self.assertFalse(objection(text), text)
        self.assertTrue(objection("No, that is not what I asked for."))
        self.assertTrue(objection("This approach won't work for the load."))
        self.assertTrue(objection("That’s the wrong approach."))

    def test_offer_is_not_repeated_when_verification_is_already_enabled(self):
        notices = self.notices()
        self.assertEqual(notices.record_objection('codex', 'session', '1'), [])
        self.assertEqual(notices.record_objection('codex', 'session', '2'), [])

    def test_bare_yes_asks_for_scope_without_enabling_and_decline_stays_off(self):
        for number in (1, 2):
            hook(self.workspace, 'claude', self.event(number, 'I disagree.'), self.state, poll=False)
        self.assertEqual(hook(self.workspace, 'claude', self.event(3, 'yes'), self.state, poll=False),
                         {'systemMessage': ASK_SCOPE})
        self.assertFalse((self.workspace / PROJECT_VERIFICATION).exists())
        result = hook(self.workspace, 'claude', self.event(4, 'no thanks'), self.state, poll=False)
        self.assertEqual(result, {'systemMessage': DISABLED})
        self.assertFalse(project_preferences(self.workspace)['enabled'])

    def test_ambiguous_answers_to_other_work_never_disable_existing_verification(self):
        for number in (1,2):
            hook(self.workspace,'claude',self.event(number,'I disagree.'),self.state,poll=False)
        self.save_preferences(True)
        self.assertEqual(hook(self.workspace,'claude',self.event(3,'no'),self.state,poll=False),{})
        self.assertTrue(project_preferences(self.workspace)['enabled'])

    def test_explicit_approval_records_task_scope_budget_and_preserves_project_bytes(self):
        before = '# Verified project\r\nDimensions: 42 mm.  \r\n'.encode('utf-16')
        (self.workspace / 'Project.md').write_bytes(before)
        result = hook(self.workspace, 'claude', self.event(1, 'Enable secondary agent verification for modeling, slicing; budget=20%'), self.state, poll=False)
        self.assertEqual(result, {'decision': 'block', 'reason': ENABLED})
        preferences = project_preferences(self.workspace)
        self.assertTrue(preferences['enabled'])
        self.assertEqual(preferences['tasks'], ['modeling', 'slicing'])
        self.assertEqual(preferences['budget_percent'], '20')
        self.assertTrue((self.workspace / 'Project.md').read_bytes().startswith(before))
        self.assertIn('Agentic-Verification.json', (self.workspace / 'Project.md').read_text(encoding='utf-16'))

    def test_quoted_consent_or_a_message_with_other_work_does_not_change_settings(self):
        for prompt in ['> Enable secondary agent verification for all',
                       'Enable secondary agent verification for modeling and then export the bracket',
                       'Please describe how to enable secondary agent verification for all']:
            self.assertEqual(hook(self.workspace, 'claude', self.event(1, prompt), self.state, poll=False), {})
        self.assertFalse((self.workspace / PROJECT_VERIFICATION).exists())

    def test_every_mark_is_emitted_once_for_each_window_and_no_other_percentages(self):
        notices = self.notices()
        for name in ['five_hour', 'weekly']:
            for used, mark in [(0,None),(49,None),(50,50),(51,None),(74,None),(75,25),(76,None),
                               (85,15),(86,None),(90,10),(91,None),(95,5),(96,None),(100,None)]:
                notices.observe('claude', self.sample(name, used))
                self.assertEqual(notices.drain('claude'), [] if mark is None else [REMINDERS[name][mark]], (name, used))
        restarted = self.notices()
        restarted.observe('claude', self.sample(used=100))
        self.assertEqual(restarted.drain('claude'), [])

    def test_initial_low_allowance_reports_only_the_most_urgent_existing_mark(self):
        notices = self.notices()
        notices.observe('codex', self.sample(used=94))
        self.assertEqual(notices.drain('codex'), [REMINDERS['five_hour'][10]])
        notices.observe('codex', self.sample(used=95))
        self.assertEqual(notices.drain('codex'), [REMINDERS['five_hour'][5]])

    def test_large_jumps_report_only_newly_crossed_configured_marks(self):
        notices = self.notices()
        notices.observe('codex', self.sample(used=10))
        self.assertEqual(notices.drain('codex'), [])
        notices.observe('codex', self.sample(used=96))
        self.assertEqual(notices.drain('codex'), [REMINDERS['five_hour'][mark] for mark in (50,25,15,10,5)])

    def test_independent_window_resets_and_stale_updates(self):
        notices = self.notices()
        for name in ['five_hour', 'weekly']:
            notices.observe('claude', self.sample(name, 50, 20000))
        self.assertEqual(len(notices.drain('claude')), 2)
        notices.observe('claude', self.sample('five_hour', 50, 30000))
        notices.observe('claude', self.sample('weekly', 50, 20000))
        self.assertEqual(notices.drain('claude'), [REMINDERS['five_hour'][50]])
        notices.observe('claude', self.sample('five_hour', 99, 25000))
        notices.observe('claude', self.sample('weekly', 99, 900))
        self.assertEqual(notices.drain('claude'), [])

    def test_queued_reminders_expire_and_a_reset_discards_old_pending_marks(self):
        notices = self.notices()
        notices.observe('codex', self.sample(reset=2000))
        self.now = 2100
        self.assertEqual(notices.drain('codex'), [])
        notices.observe('codex', self.sample(reset=3000))
        notices.observe('codex', self.sample(reset=4000))
        self.assertEqual(notices.drain('codex'), [REMINDERS['five_hour'][50]])
        notices.observe('codex', self.sample(used=75,reset=4000))
        self.assertEqual(self.notices(False).drain('codex'), [])
        self.assertEqual(notices.drain('codex'), [])

    def test_provider_counters_are_separate_and_disabled_preferences_never_warn(self):
        disabled = self.notices(False)
        disabled.observe('claude', self.sample())
        self.assertEqual(disabled.drain('claude'), [])
        enabled = self.notices()
        for agent in ['codex','claude']:
            enabled.observe(agent, self.sample())
            self.assertEqual(enabled.drain(agent), [REMINDERS['five_hour'][50]])

    def test_unknown_invalid_and_context_cost_usage_never_become_allowance_estimates(self):
        notices = self.notices()
        for used in [None, True, 'NaN', '-1', '101']:
            notices.observe('claude', self.sample(used=used))
        for value in [{'context_window': {'used_percentage': 99}}, {'total_cost_usd': 99}, {'rate_limit_info': {'utilization': .99}}]:
            notices.observe('claude', value)
        self.assertEqual(notices.drain('claude'), [])

    def test_native_adapters_use_verified_window_identifiers(self):
        result = windows('codex', {'rateLimits': {'primary': {'windowDurationMins':10080,'usedPercent':75,'resetsAt':20000},
                                                 'secondary': {'windowDurationMins':300,'usedPercent':50,'resetsAt':20000}}})
        self.assertEqual([entry['window'] for entry in result], ['weekly','five_hour'])
        self.assertEqual(windows('codex', {'rateLimits': {'primary': {'windowDurationMins':15,'usedPercent':99,'resetsAt':20000}}}), [])
        result = windows('claude', {'rate_limits': {'five_hour': {'used_percentage':50,'resets_at':20000},
                                                  'seven_day': {'used_percentage':75,'resets_at':20000}}})
        self.assertEqual([entry['window'] for entry in result], ['five_hour','weekly'])

    def test_quota_cache_is_throttled_and_failed_telemetry_stays_quiet(self):
        notices = self.notices()
        fetch = mock.Mock(return_value=self.sample())
        notices.poll_codex(fetch)
        notices.poll_codex(fetch)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(notices.drain('codex'), [REMINDERS['five_hour'][50]])
        self.now += 31
        notices.poll_codex(mock.Mock(side_effect=OSError('telemetry unavailable')))
        self.assertEqual(notices.drain('codex'), [])

    def test_captured_primary_hooks_do_not_consume_parent_notifications(self):
        with mock.patch.dict(os.environ, {'AGENTIC_SECONDARY_SUPERVISED':'1'}):
            self.assertEqual(hook(self.workspace, 'codex', self.event(1,'I disagree.'), self.state, poll=False), {})
        self.assertFalse(self.state.exists())

    def test_state_cannot_be_generated_inside_the_portable_project(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            Notices(self.workspace, self.workspace/'runtime', preferences={'enabled':False})

    def test_codex_rpc_reader_uses_no_thread_turn_model_or_account_mutation_requests(self):
        log = self.root / 'requests.json'
        program = """import json,sys
from pathlib import Path
seen=[]
for line in sys.stdin:
 value=json.loads(line); seen.append(value['method'])
 assert value['method'] in ['initialize','initialized','account/rateLimits/read']
 if value['method']=='initialize': print(json.dumps({'id':1,'result':{'server':'fixture'}}),flush=True)
 elif value['method']=='account/rateLimits/read': print(json.dumps({'id':2,'result':{'rateLimits':{'primary':{'windowDurationMins':300,'usedPercent':75,'resetsAt':20000}}}}),flush=True)
Path(sys.argv[1]).write_text(json.dumps(seen))
"""
        result = codex_snapshot([sys.executable,'-u','-c',program,str(log)])
        self.assertEqual(json.loads(log.read_text()), ['initialize','initialized','account/rateLimits/read'])
        self.assertEqual(windows('codex',result)[0]['used_percent'],75)

    @unittest.skipUnless(os.name=='nt','Windows hook integration')
    def test_setup_preserves_global_and_project_status_lines_and_installs_only_when_missing(self):
        launcher = ROOT/'AgenticFusionTemplate/Fusion-Claude.bat'
        content = launcher.read_text(encoding='utf-8-sig')
        body = content[content.rindex('#PS_BEGIN'):]
        body = body[:body.rindex('try { Start-AgenticFusion }')]
        settings=self.workspace/'settings.json'
        settings.write_text(json.dumps({'autoMemoryEnabled':False,'enabledMcpjsonServers':['fusion']}))
        literal=lambda value: "'"+str(value).replace("'","''")+"'"
        header='$env:PROJDIR='+literal(self.workspace)+'\n$env:SELF='+literal(launcher)+'\n'
        checks=r'''
$script:globalFixture=$true
function Get-GlobalClaudeStatusLine { if ($script:globalFixture) { return [pscustomobject]@{type='command';command='echo global-custom'} }; return $null }
$null=Ensure-ProjectSettings
$file=Join-Path $ProjectDir 'settings.json'
$record=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
if ($record.PSObject.Properties['statusLine']) { throw 'Global status line was shadowed.' }
$script:globalFixture=$false
$null=Ensure-ProjectSettings
$record=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
if ($record.statusLine.command -notmatch 'secondary-verification.ps1') { throw 'Missing native quota bridge.' }
$record.statusLine.command='echo project-custom'
Write-ProjectJson -File $file -Data $record
$script:globalFixture=$true
$null=Ensure-ProjectSettings
$record=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
if ($record.statusLine.command -ne 'echo project-custom') { throw 'Project status line was replaced.' }
'''
        harness=self.root/'settings-check.ps1'
        harness.write_text(header+body+checks,encoding='utf-8')
        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(harness)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    @unittest.skipUnless(os.name=='nt','Windows hook integration')
    def test_real_claude_statusline_bridge_queues_quota_warnings_without_model_context(self):
        scripts = self.workspace / '.agents/scripts'
        scripts.mkdir(parents=True)
        for name in ['secondary-verification.ps1','secondary_verification.py','review_guard.py']:
            shutil.copyfile(SCRIPTS/name,scripts/name)
        self.save_preferences(True)
        command = ['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(scripts/'secondary-verification.ps1'),'-Agent','claude']
        environment = dict(os.environ, AGENTIC_SECONDARY_STATE_ROOT=str(self.state))
        payload={'rate_limits':{'five_hour':{'used_percentage':50,'resets_at':int(time.time())+18000},
                                'seven_day':{'used_percentage':75,'resets_at':int(time.time())+604800}}}
        result=subprocess.run(command+['-Mode','statusline'],input=json.dumps(payload),text=True,capture_output=True,env=environment,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'')
        event=json.dumps({'hook_event_name':'Stop','session_id':'conversation'})
        result=subprocess.run(command+['-Mode','hook'],input=event,text=True,capture_output=True,env=environment,timeout=15)
        self.assertEqual(json.loads(result.stdout),{'systemMessage':REMINDERS['five_hour'][50]+'\n'+REMINDERS['weekly'][25]})
        result=subprocess.run(command+['-Mode','hook'],input=event,text=True,capture_output=True,env=environment,timeout=15)
        self.assertEqual(result.stdout,'')

    @unittest.skipUnless(os.name=='nt','Windows hook integration')
    def test_real_powershell_hook_shows_fixed_offer_and_consumes_explicit_setting_reply(self):
        scripts = self.workspace / '.agents/scripts'
        scripts.mkdir(parents=True)
        for name in ['secondary-verification.ps1','secondary_verification.py','review_guard.py','project-resources.ps1']:
            shutil.copyfile(SCRIPTS/name,scripts/name)
        command = ['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(scripts/'secondary-verification.ps1'),'-Mode','hook','-Agent','claude']
        environment = dict(os.environ, AGENTIC_SECONDARY_STATE_ROOT=str(self.state))
        results=[]
        for number,prompt in [(1,'I disagree.'),(2,"That's the wrong approach."),(3,'Enable secondary agent verification for modeling')]:
            result=subprocess.run(command,input=json.dumps(self.event(number,prompt)),text=True,capture_output=True,env=environment,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            results.append(json.loads(result.stdout) if result.stdout.strip() else {})
        self.assertEqual(results[0],{})
        self.assertEqual(results[1],{'systemMessage':OFFER})
        self.assertEqual(results[2],{'decision':'block','reason':ENABLED})
        self.assertTrue(project_preferences(self.workspace)['enabled'])


if __name__=='__main__':
    unittest.main(verbosity=2)
