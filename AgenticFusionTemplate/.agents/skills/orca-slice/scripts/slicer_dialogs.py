"""Dismiss recognized slicer startup dialogs through background Windows messages.

Only newly appearing dialogs in the selected application are eligible. Never use
global input, close the main window, accept consent, or dismiss work/error prompts.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re
import time


NOTICE = re.compile(
    r"^(?:(?:orca\s?slicer|snapmaker orca|bambu studio)\s*[-:]\s*)?"
    r"(?:software update|version update|new version available|update available|update|"
    r"check for updates|release notes|what['’]s new|tip of the day|daily tips|tips|"
    r"welcome(?: to (?:orca\s?slicer|snapmaker orca|bambu studio))?|"
    r"login|log in|sign in|configuration wizard|setup wizard|user guide|getting started)$", re.I)
PROTECTED = re.compile(
    r"\b(?:save|saving|discard|unsaved|recover\w*|restore|license|licence|terms|privacy|"
    r"consent|firmware|error|failed|warning|conflict|overwrite|incompatible|delete|"
    r"remove|upload|printing)\b", re.I)


def is_notice(window):
    text = window['title'] + '\n' + '\n'.join(window.get('labels', []))
    return bool(window['dialog'] and NOTICE.fullmatch(window['title'].strip())
                and not PROTECTED.search(text))


class WindowsUI:
    """Small, pointer-width-safe Win32 adapter; no desktop input/focus APIs."""
    def __init__(self):
        if os.name != 'nt':
            raise OSError('Startup dialog automation supports Windows.')
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        signatures = {
            'EnumWindows': ([self.callback, wintypes.LPARAM], wintypes.BOOL),
            'EnumChildWindows': ([wintypes.HWND, self.callback, wintypes.LPARAM], wintypes.BOOL),
            'GetWindowThreadProcessId': ([wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
            'IsWindowVisible': ([wintypes.HWND], wintypes.BOOL),
            'IsWindowEnabled': ([wintypes.HWND], wintypes.BOOL),
            'GetWindow': ([wintypes.HWND, wintypes.UINT], wintypes.HWND),
            'GetWindowLongW': ([wintypes.HWND, ctypes.c_int], wintypes.LONG),
            'GetWindowTextW': ([wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            'GetClassNameW': ([wintypes.HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int),
            'SendMessageTimeoutW': ([wintypes.HWND, wintypes.UINT, ctypes.c_size_t,
                                    ctypes.c_ssize_t, wintypes.UINT, wintypes.UINT,
                                    ctypes.POINTER(ctypes.c_size_t)], ctypes.c_ssize_t),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.user, name)
            function.argtypes, function.restype = args, result
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                         wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.kernel.GetProcessTimes.restype = wintypes.BOOL

    def identity(self, pid):
        handle = self.kernel.OpenProcess(0x1000, False, pid)  # query limited information
        if not handle:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            times = [wintypes.FILETIME() for _ in range(4)]
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None
            if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                return None
            return (os.path.normcase(buffer.value), (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
        finally:
            self.kernel.CloseHandle(handle)

    def handles(self):
        found = []
        callback = self.callback(lambda hwnd, _: (found.append(int(hwnd)), True)[1])
        if not self.user.EnumWindows(callback, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return found

    def text(self, hwnd, class_name=False):
        buffer = ctypes.create_unicode_buffer(1024)
        function = self.user.GetClassNameW if class_name else self.user.GetWindowTextW
        function(hwnd, buffer, len(buffer))
        return buffer.value

    def describe(self, hwnd):
        if not self.user.IsWindowVisible(hwnd):
            return None
        pid, identity = self.owner(hwnd)
        if not identity:
            return None
        owner = self.user.GetWindow(hwnd, 4)  # GW_OWNER
        dialog = bool(owner) or self.text(hwnd, True) == '#32770' or bool(self.user.GetWindowLongW(hwnd, -20) & 1)
        labels = []
        if dialog:
            def collect(child, _):
                # Never inspect edit/password/browser fields.
                if len(labels) < 40 and self.text(child, True).casefold() in {'static', 'button'}:
                    label = self.text(child)
                    if label:
                        labels.append(label)
                return True
            self.user.EnumChildWindows(hwnd, self.callback(collect), 0)
        return dict(hwnd=hwnd, pid=pid, identity=identity, title=self.text(hwnd),
                    dialog=dialog, labels=labels, enabled=bool(self.user.IsWindowEnabled(hwnd)))

    def owner(self, hwnd):
        pid = wintypes.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value, self.identity(pid.value)

    def close(self, window):
        # Recheck ownership and classification immediately before sending WM_CLOSE.
        current = self.describe(window['hwnd'])
        if not current or any(current[k] != window[k] for k in ('pid', 'identity', 'title')):
            return False
        if not current['enabled'] or not is_notice(current):
            return False
        result = ctypes.c_size_t()
        return bool(self.user.SendMessageTimeoutW(window['hwnd'], 0x0010, 0, 0,
                                                  0x0002 | 0x0020, 500, ctypes.byref(result)))


def prepare():
    """Capture existing handles before activation; failure must not prevent opening."""
    try:
        ui = WindowsUI()
        return ui, {hwnd: ui.owner(hwnd) for hwnd in ui.handles()}
    except (OSError, AttributeError):
        return None


def dismiss(app, pid, before, timeout=12, *, clock=time.monotonic, sleep=time.sleep):
    """Bounded boot pass, including single-instance handoff to the selected binary."""
    if not before:
        return dict(status='unverified', closed=[], pending=[], reason='Window inventory unavailable.')
    ui, existing = before
    selected_path = os.path.normcase(str(Path(app['executable']).resolve())) if app.get('executable') else None
    original = ui.identity(pid) if pid else None
    targets = {}
    if original and (not selected_path or original[0] == selected_path):
        targets[pid] = original
    handoffs = {candidate_pid: identity for candidate_pid, identity in existing.values()
                if identity and selected_path and identity[0] == selected_path}
    deadline = clock() + max(0, min(timeout, 30))
    closed, requested, attempts = [], {}, set()
    pending, main_pids = [], set()
    while True:
        pending, main_pids = [], set()
        visible = {}
        # Only a unique pre-launch instance may receive a single-instance handoff.
        # Another copy launched by the user during this pass is not ours to close.
        if not targets or (original and ui.identity(pid) != original):
            if len(handoffs) == 1:
                targets.update(handoffs)
        for hwnd in ui.handles():
            owner_pid, ident = ui.owner(hwnd)
            if not ident:
                continue
            if targets.get(owner_pid) != ident:
                continue
            window = ui.describe(hwnd)
            if not window or window['identity'] != ident:
                continue
            key = (hwnd, owner_pid, ident)
            visible[key] = window
            if not window['dialog']:
                main_pids.add(owner_pid)
                continue
            if hwnd in existing or not is_notice(window):
                pending.append(dict(title=window['title'], reason='Existing or unrecognized/required dialog.'))
            elif key not in attempts and len(attempts) < 12 and window['enabled']:
                attempts.add(key)
                if ui.close(window):
                    requested[key] = window['title']
                else:
                    pending.append(dict(title=window['title'], reason='Background close was refused.'))
            else:
                pending.append(dict(title=window['title'], reason='Dialog is still open.'))
        for key, title in list(requested.items()):
            if key not in visible:
                closed.append(title)
                del requested[key]
        if clock() >= deadline:
            break
        sleep(min(.25, max(0, deadline - clock())))
    pending.extend(dict(title=title, reason='Close requested; disappearance not verified.')
                   for title in requested.values() if not any(p['title'] == title for p in pending))
    return dict(status='clear' if main_pids and not pending else 'needs_attention', closed=closed, pending=pending,
                main_pid=next(iter(main_pids)) if len(main_pids) == 1 else None,
                preview_verified=False, reason='' if main_pids else 'Selected main window not verified.')


def finish(app, opening, before, timeout=12):
    try:
        return dismiss(app, opening.get('pid'), before, timeout)
    except (OSError, ValueError, AttributeError) as exc:
        return dict(status='unverified', closed=[], pending=[], reason=str(exc))
