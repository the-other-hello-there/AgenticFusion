# Command-only hook/status-line bridge. No model invocation; ordinary startup needs no Python.
[CmdletBinding()]
param(
    [ValidateSet('hook','statusline','observe','objection')][string]$Mode = 'hook',
    [ValidateSet('codex','claude')][string]$Agent = 'claude'
)
try {
    $OutputEncoding = New-Object Text.UTF8Encoding($false)
    [Console]::InputEncoding = $OutputEncoding
    [Console]::OutputEncoding = $OutputEncoding
    $inputJson = [Console]::In.ReadToEnd()
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) { exit 0 }
    $projectPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    $inputJson | & py -3 -B (Join-Path $PSScriptRoot 'secondary_verification.py') --mode $Mode --agent $Agent --workspace $projectPath
} catch { }
exit 0
