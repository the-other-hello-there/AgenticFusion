# Slicer discovery, choice and startup

## Choose the installed application

Python 3.11+, Windows PowerShell and the standard library are sufficient. Normal Fusion startup needs neither Python nor a slicer. There is no version allowlist or special-build requirement for discovery/opening.

```powershell
py -3 .agents/skills/orca-slice/scripts/slicer.py list
# Include an unregistered portable executable (also accepted through ORCA_SLICER_PATH).
py -3 .agents/skills/orca-slice/scripts/slicer.py list --executable 'D:\Tools\My Orca\orca-slicer.exe'
```

Discovery reads standard/versioned install folders, PATH, per-user/machine installer registry and App Paths, Start menu/Desktop shortcuts, and current-user Windows Store/package manifests and Start app identities. It finds OrcaSlicer, Snapmaker Orca, OrcaMCP, other Orca-named builds and Bambu Studio; Bambu is labeled as its own application. It merges duplicate discoveries while keeping separate installations selectable. Arbitrary unregistered portable folders need an explicit executable; it does not scan every disk. Discovery warnings describe partial coverage. It does not execute candidates or contact a printer.

Apply the slicer-choice policy in `FDM-Slicing.md`. In a noninteractive agent shell, run `list`, obtain the choice in chat, then pass its stable ID with `--select`. In an interactive terminal, `open` without `--select` offers a numbered choice, even with one candidate. Cancellation launches nothing. IDs are local selection handles, not portable preferences; rerun discovery if an app moves or is removed. Use source/path to distinguish otherwise identical names/versions.

```powershell
# After the user chooses, inspect only that executable's advertised CLI flags.
py -3 .agents/skills/orca-slice/scripts/slicer.py probe --select ID
# Prepare and slice headlessly per workflow.md; slice opens the result after success.
# For a saved sliced result, open it in the chosen app for UI preview:
py -3 .agents/skills/orca-slice/scripts/slicer.py open --select ID --file 'Print Jobs\job-sliced.3mf'
```

The agent handles exporting, file/profile preparation and headless slicing, then opens the completed local result for UI preview. Do not launch the GUI on the source model before a CLI-capable job. An explicit request merely to open a model can still use `open --file MODEL`. Ordinary installs receive the preview file as a separate process argument, with their normal profiles and data directory. Do not replace profiles or apply OrcaMCP-specific flags to a stock/vendor app. Store installs use their AUMID and Windows application/file activation contracts; the default file association is never used to guess the chosen slicer. If file activation is unsupported, an accessible manifest executable is tried. A failed activation with no accessible executable is a reported limit, not permission to select another app. Never take ownership of WindowsApps or change its permissions. [Microsoft application identities](https://learn.microsoft.com/en-us/windows/configuration/store/find-aumid), [file activation](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-iapplicationactivationmanager-activateforfile).

Activation/process success means an open request was accepted. For the final slice, enter the selected build's layer/toolpath Preview if it does not appear automatically, and verify that it displays this job's actual sliced output. Inspect dimensions, plate and profiles with available app/GUI tools under the access rule below. Opening an unsliced model or Prepare tab does not satisfy preview. Preserve unsaved work and any already-open slicer; headless processing does not require closing it. The helpers never kill existing slicers.

## Automatic startup dialog cleanup

Both `slicer.py open` (including the opening after `slice`) and a fresh `start_orca.py` launch run the shared `slicer_dialogs.py` boot pass automatically. It snapshots existing windows before activation, then checks newly appearing dialogs for up to 12 seconds. Recognized English-titled update notices, login, welcome/setup, tips and release notes receive a background close request; chained notices are handled in the same pass. It never selects an installation, login, consent or profile-change action. A single-instance handoff requires a unique pre-existing instance of the selected executable and uses its actual window PID; package-only activation stays on its returned PID.

The helper uses process creation identity and the selected executable/PID to scope access. It preserves the main window and pre-existing dialogs, never sends keyboard/mouse input or requests focus, and verifies disappearance before reporting a close. Windows' [WM_CLOSE](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-close) is an application-handled request, not a forced close; [bounded delivery](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendmessagetimeoutw) limits a hung window's response wait. Applications may decline it or open another prompt.

Read the returned `dialog_cleanup` result: `clear` only means a main window was found without an observed pending dialog. Save/discard, recovery, consent/privacy/license, error and unrecognized dialogs stay open and are reported as `needs_attention`; unavailable window access is `unverified`. Custom/web/localized dialogs and delayed prompts may need the selected build's verified API or background accessibility controls. Resolve required printer/profile setup from verified job data; ask only when an actual user decision is needed. Never bypass a required decision to make startup look successful. A clean boot pass does not verify import or slice preview.

## Non-disruptive UI access

Apply `FDM-Slicing.md`'s non-disruptive UI policy. Prefer application APIs/MCP, passive screenshots/accessibility reads and background controls. Verify the tool's actual behavior: a window-scoped label does not prove its clicks/typing preserve cursor, focus, typing and clipboard. SendKeys/SendInput, blanket input blocking and foreground/cursor takeover are unsuitable routes even when slicer control was authorized.

The current desktop/Store `open` helper requests application/file activation, and the target app may foreground itself; it does not guarantee focus isolation. Prefer a supported background/non-activating launch or an already-open window when that can be verified. If compliant opening/control is unavailable while the user is working, keep the headless artifact (`--no-open`), stop dependent UI interaction and report the exact pending preview/setup action. Never claim the visual check passed. Retain the selected app and completed work rather than retrying through pointer takeover.

## Capability-based slicing

Use the selected build's `probe` results and local help. The helper's `slice` operation uses only advertised core options and explicit profiles/prepared 3MF; see [workflow](workflow.md). Prefer CLI through completed toolpath export, then open the final result for required UI preview. Older/vendor builds may expose different CLI options or no usable CLI. Store GUI activation does not imply headless CLI access. If CLI or an indispensable profile/orientation setup step is unavailable headlessly, explain the specific limitation before opening the UI earlier; continue with available GUI automation or that build's verified MCP. If neither is available, automated slicing is unverified; report the exact limit. Do not silently switch slicers or describe a hidden/minimized GUI as headless. No helper can add an automation interface to every historical/future build. [Upstream CLI documentation](https://github.com/OrcaSlicer/OrcaSlicer/wiki/cli_mode).

## Optional OrcaMCP connection

Only use this route when the chosen app is an actual [OrcaMCP build](https://github.com/okets/OrcaMCP/tree/mcp), or an already-running selected window has a verified embedded MCP server. This embedded server runs inside the GUI app; starting it is not a headless substitute for CLI slicing. Prefer CLI for a headless job, then open the UI at preview. MCP is optional; do not require users of stock/Snapmaker/Store builds to install a different slicer.

Confirm the selected window's endpoint in Preferences > MCP before attaching. The common default is `http://127.0.0.1:13618/mcp`; another window may use a different port. Do not automatically attach to whichever Orca server answers. The MCP helper cannot establish window ownership from server identity alone.

```powershell
# Only after confirming this endpoint belongs to the chosen app/window.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --configure --executable 'C:\Tools\OrcaMCP\orca-slicer.exe' --mcp-url 'http://127.0.0.1:13618/mcp'
py -3 .agents/skills/orca-slice/scripts/start_orca.py --check-only --mcp-url 'http://127.0.0.1:13618/mcp'
# Maintenance/config preparation only: no app or MCP verification.
py -3 .agents/skills/orca-slice/scripts/start_orca.py --setup-only
```

This legacy MCP helper verifies initialize/tools/list before `--configure` merges `orcaslicer` into `.mcp.json`, `.codex/config.toml` and `settings.json`. It preserves unrelated entries, explicit disables and conflicting configurations, restoring original bytes on write failure. Reconnect/restart the client's MCP session after first registration and inspect the actual tool schemas. Setup-only does not establish connectivity. Configuration changes cannot inject tools into a running chat.

If the endpoint is offline, this MCP-specific helper launches the explicitly selected executable (or discovers OrcaMCP only), with an isolated `%LOCALAPPDATA%\AgenticFusion\OrcaMCP` data directory (`--data-dir` overrides) and `ORCAMCP_SKIP_CLOUD_LOGIN=1`. This is separate from ordinary `slicer.py open`, which uses normal installed profiles. Select the real printer/material in that isolated instance. Leave a failed startup open for inspection. Only loopback HTTP `/mcp` endpoints are accepted; MaxEllis REST port `13130` needs its separate matching stdio server and token and is not this backend.
