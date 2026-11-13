"""Background boot-dialog checks using simulated windows; never close real apps."""
import importlib.util
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / 'AgenticFusionTemplate/.agents/skills/orca-slice/scripts'
sys.path.insert(0, str(SCRIPTS))
import slicer_dialogs as dialogs
import slicer


class FakeUI:
    def __init__(self, windows, refuse=False):
        self.windows = {w['hwnd']: w for w in windows}
        self.closed = []
        self.read = []
        self.refuse = refuse
        self.followups = []

    def handles(self):
        return list(self.windows)

    def owner(self, hwnd):
        w = self.windows[hwnd]
        return w['pid'], w['identity']

    def identity(self, pid):
        return next((w['identity'] for w in self.windows.values() if w['pid'] == pid), None)

    def describe(self, hwnd):
        self.read.append(hwnd)
        return self.windows.get(hwnd)

    def close(self, window):
        self.closed.append(window['hwnd'])
        if self.refuse:
            return False
        self.windows.pop(window['hwnd'])
        if self.followups:
            w = self.followups.pop(0)
            self.windows[w['hwnd']] = w
        return True


class BootDialogChecks(unittest.TestCase):
    def setUp(self):
        self.binary = str((Path.cwd() / 'fixture-orca.exe').resolve())
        self.identity = (os.path.normcase(self.binary), 100)
        self.app = {'executable': self.binary}
        self.now = 0

    def window(self, hwnd, title='Update available', **changes):
        return dict(hwnd=hwnd, title=title, pid=42, identity=self.identity,
                    dialog=True, labels=[], enabled=True) | changes

    def run_boot(self, ui, existing=(), pid=42):
        def sleep(seconds):
            self.now += seconds
        return dialogs.dismiss(self.app, pid, (ui, {h: ui.owner(h) for h in existing}), timeout=1,
                               clock=lambda: self.now, sleep=sleep)

    def test_chained_startup_dialogs_close_and_disappearance_is_verified(self):
        ui = FakeUI([self.window(1, 'OrcaSlicer', dialog=False), self.window(2)])
        ui.followups = [self.window(3, 'Sign in'), self.window(4, 'Tip of the day')]
        result = self.run_boot(ui)
        self.assertEqual(ui.closed, [2, 3, 4])
        self.assertEqual(result['closed'], ['Update available', 'Sign in', 'Tip of the day'])
        self.assertEqual(result['status'], 'clear')
        self.assertFalse(result['preview_verified'])

    def test_existing_dialogs_main_window_and_other_install_are_preserved(self):
        ui = FakeUI([self.window(1, 'Welcome', dialog=False), self.window(2),
                     self.window(3, pid=99, identity=('different-install.exe', 9))])
        result = self.run_boot(ui, existing=[1, 2])
        self.assertEqual(ui.closed, [])
        self.assertNotIn(3, ui.read, 'Do not inspect another application\'s labels')
        self.assertEqual(result['status'], 'needs_attention')

    def test_unknown_and_protected_prompts_are_reported(self):
        for title, labels in [('Save changes?', []), ('Privacy policy', []),
                              ('Update available', ['Unsaved work']),
                              ('Welcome', ['Accept the license']),
                              ('Update available', ['Firmware warning']),
                              ('Unrecognized vendor dialog', [])]:
            with self.subTest(title=title, labels=labels):
                ui = FakeUI([self.window(2, title, labels=labels)])
                result = self.run_boot(ui)
                self.assertFalse(ui.closed)
                self.assertEqual(result['status'], 'needs_attention')
                self.assertEqual(result['pending'][0]['title'], title)

    def test_single_instance_handoff_resolves_only_selected_executable(self):
        ui = FakeUI([self.window(1, dialog=False), self.window(2)])
        self.assertEqual(self.run_boot(ui, existing=[1], pid=999)['status'], 'clear')
        self.assertEqual(ui.closed, [2])

    def test_simultaneous_unrelated_launch_of_same_binary_is_preserved(self):
        ui = FakeUI([self.window(1, dialog=False), self.window(2), self.window(3, pid=99)])
        self.run_boot(ui)
        self.assertEqual(ui.closed, [2])
        self.assertNotIn(3, ui.read)

    def test_recycled_process_identity_is_not_adopted(self):
        ui = FakeUI([self.window(2, identity=(self.identity[0], 200))])
        with mock.patch.object(ui, 'identity', return_value=self.identity):
            result = self.run_boot(ui)
        self.assertEqual(ui.closed, [])
        self.assertEqual(result['status'], 'needs_attention')

    def test_package_activation_without_executable_stays_on_returned_pid(self):
        self.app = {'app_id': 'chosen.package!app'}
        ui = FakeUI([self.window(1, dialog=False), self.window(2),
                     self.window(3, pid=99)])
        self.assertEqual(self.run_boot(ui)['status'], 'clear')
        self.assertEqual(ui.closed, [2])
        self.assertNotIn(3, ui.read)

    def test_process_reuse_unavailable_access_and_disabled_dialog_do_not_close(self):
        ui = FakeUI([self.window(2, enabled=False), self.window(3, pid=99, identity=None)])
        self.assertEqual(self.run_boot(ui)['status'], 'needs_attention')
        self.assertFalse(ui.closed)
        self.assertEqual(dialogs.dismiss(self.app, 42, None)['status'], 'unverified')

    def test_refusal_is_bounded_and_does_not_count_as_closed(self):
        ui = FakeUI([self.window(2)], refuse=True)
        result = self.run_boot(ui)
        self.assertEqual(ui.closed, [2])
        self.assertEqual(result['closed'], [])
        self.assertEqual(result['status'], 'needs_attention')
        self.assertLessEqual(self.now, 1)

    def test_missing_main_window_does_not_establish_readiness(self):
        result = self.run_boot(FakeUI([self.window(2)]))
        self.assertEqual(result['closed'], ['Update available'])
        self.assertEqual(result['status'], 'needs_attention')

    def test_changed_identity_or_title_cannot_receive_close(self):
        native = object.__new__(dialogs.WindowsUI)
        native.user = mock.Mock()
        original = self.window(2)
        for changed in (dict(identity=(self.identity[0], 200)), dict(title='Save changes?'),
                        dict(labels=['Privacy consent']), dict(enabled=False)):
            native.describe = mock.Mock(return_value=original | changed)
            self.assertFalse(native.close(original))
        native.user.SendMessageTimeoutW.assert_not_called()

    def test_close_sends_only_targeted_wm_close_and_no_input(self):
        native = object.__new__(dialogs.WindowsUI)
        native.user = mock.Mock()
        native.describe = mock.Mock(return_value=self.window(2))
        self.assertTrue(native.close(self.window(2)))
        args = native.user.SendMessageTimeoutW.call_args.args
        self.assertEqual(args[:4], (2, 0x0010, 0, 0))
        self.assertEqual([c[0] for c in native.user.mock_calls], ['SendMessageTimeoutW'])

    @unittest.skipUnless(os.name == 'nt', 'Win32 ABI check')
    def test_native_adapter_can_read_own_process_identity_without_opening_windows(self):
        ui = dialogs.WindowsUI()
        identity = ui.identity(os.getpid())
        self.assertRegex(Path(identity[0]).name, r'^python[\d.]*\.exe$')
        self.assertGreater(identity[1], 0)
        self.assertEqual(identity, ui.identity(os.getpid()))
        try:
            self.assertIsInstance(ui.handles(), list)
        except OSError:
            # Some CI/sandbox desktops prohibit enumeration; opening still works
            # and the helper explicitly reports unverified dialog state.
            with mock.patch.object(dialogs, 'WindowsUI', return_value=ui):
                self.assertIsNone(dialogs.prepare())

    @unittest.skipUnless(os.name == 'nt', 'Windows opening paths')
    def test_both_opening_paths_snapshot_before_launch_and_run_cleanup(self):
        for store in (False, True):
            calls = []
            with self.subTest(store=store), \
                    mock.patch.object(slicer.slicer_dialogs, 'prepare', side_effect=lambda: calls.append('before') or ('fixture', set())), \
                    mock.patch.object(slicer.slicer_dialogs, 'finish', side_effect=lambda *a: calls.append('cleanup') or {'status': 'clear'}) as finish, \
                    mock.patch.object(slicer, 'powershell', side_effect=lambda *a: calls.append('launch') or mock.Mock(returncode=0, stdout='{"pid":42}')), \
                    mock.patch.object(slicer.subprocess, 'Popen', side_effect=lambda *a, **kw: calls.append('launch') or mock.Mock(pid=42)):
                app = self.app | ({'app_id': 'chosen!app'} if store else {})
                result = slicer.open_app(app)
                self.assertEqual(calls, ['before', 'launch', 'cleanup'])
                self.assertEqual(result['dialog_cleanup']['status'], 'clear')
                self.assertEqual(finish.call_args.args[1]['pid'], 42)

    @unittest.skipUnless(os.name == 'nt', 'Native background-message check')
    def test_native_close_of_own_offscreen_nonactivating_fixture(self):
        ui = dialogs.WindowsUI()
        proc_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT,
                                      ctypes.c_size_t, ctypes.c_ssize_t)

        class WindowClass(ctypes.Structure):
            _fields_ = [('style', wintypes.UINT), ('proc', proc_type),
                        ('class_extra', ctypes.c_int), ('window_extra', ctypes.c_int),
                        ('instance', wintypes.HINSTANCE), ('icon', wintypes.HANDLE),
                        ('cursor', wintypes.HANDLE), ('background', wintypes.HANDLE),
                        ('menu', wintypes.LPCWSTR), ('name', wintypes.LPCWSTR)]

        ui.user.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, ctypes.c_size_t, ctypes.c_ssize_t]
        ui.user.DefWindowProcW.restype = ctypes.c_ssize_t
        ui.user.DestroyWindow.argtypes = [wintypes.HWND]
        ui.user.DestroyWindow.restype = wintypes.BOOL
        ui.user.RegisterClassW.argtypes = [ctypes.POINTER(WindowClass)]
        ui.user.RegisterClassW.restype = wintypes.WORD
        ui.user.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
        ui.user.UnregisterClassW.restype = wintypes.BOOL
        ui.user.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                          wintypes.DWORD] + [ctypes.c_int] * 4 + [wintypes.HWND,
                                          wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
        ui.user.CreateWindowExW.restype = wintypes.HWND
        ui.kernel.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        ui.kernel.GetModuleHandleW.restype = wintypes.HMODULE

        def process(hwnd, message, wparam, lparam):
            if message == 0x0010:
                ui.user.DestroyWindow(hwnd)
                return 0
            return ui.user.DefWindowProcW(hwnd, message, wparam, lparam)

        callback = proc_type(process)
        module = ui.kernel.GetModuleHandleW(None)
        name = 'AgenticFusionDialogFixture' + str(os.getpid())
        definition = WindowClass(instance=module, proc=callback, name=name)
        if not ui.user.RegisterClassW(ctypes.byref(definition)):
            self.skipTest('Desktop window registration is unavailable.')
        window = None
        try:
            # EX_NOACTIVATE + TOOLWINDOW, offscreen and one pixel: no focus,
            # taskbar entry, cursor movement or normal-desktop interference.
            window = ui.user.CreateWindowExW(0x08000000 | 0x80 | 1, name, 'Tip of the day',
                                             0x80000000 | 0x10000000, -32000, -32000, 1, 1,
                                             None, None, module, None)
            if not window:
                self.skipTest('Desktop window creation is unavailable.')
            description = ui.describe(window)
            self.assertTrue(dialogs.is_notice(description))
            self.assertEqual(description['pid'], os.getpid())
            self.assertTrue(ui.close(description))
            self.assertIsNone(ui.describe(window))
        finally:
            if window:
                ui.user.DestroyWindow(window)
            ui.user.UnregisterClassW(name, module)


if __name__ == '__main__':
    unittest.main(verbosity=2)
