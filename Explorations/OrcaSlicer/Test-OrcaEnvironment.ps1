# Read-only inventory. Does not launch applications, load models, or call tools.
[CmdletBinding()]
param(
    [string]$OrcaPath,
    [ValidateRange(50, 5000)]
    [int]$TimeoutMs = 300
)

$ErrorActionPreference = 'Stop'
$candidates = @()
if ($OrcaPath) {
    if (-not (Test-Path -LiteralPath $OrcaPath -PathType Leaf)) {
        throw "Executable not found: $OrcaPath"
    }
    if ([System.IO.Path]::GetExtension($OrcaPath) -ine '.exe') {
        throw 'OrcaPath must name a Windows executable.'
    }
    $candidates += [pscustomobject]@{ Variant = 'Explicit path'; Path = $OrcaPath }
}

$locations = @(
    @{ Variant = 'OrcaSlicer'; Relative = 'OrcaSlicer\orca-slicer.exe' },
    @{ Variant = 'OrcaMCP community fork'; Relative = 'OrcaMCP\orca-slicer.exe' },
    @{ Variant = 'OrcaMCP community fork'; Relative = 'OrcaMCP\OrcaMCP.exe' },
    @{ Variant = 'Snapmaker vendor fork'; Relative = 'Snapmaker_Orca\snapmaker-orca.exe' },
    @{ Variant = 'Bambu Studio (separate slicer)'; Relative = 'Bambu Studio\bambu-studio.exe' }
)
$roots = @($env:ProgramFiles, ${env:ProgramFiles(x86)})
if ($env:LOCALAPPDATA) { $roots += Join-Path $env:LOCALAPPDATA 'Programs' }
foreach ($root in @($roots | Where-Object { $_ } | Select-Object -Unique)) {
    foreach ($location in $locations) {
        $candidates += [pscustomobject]@{
            Variant = $location.Variant
            Path = Join-Path $root $location.Relative
        }
    }
}
foreach ($name in @('orca-slicer.exe', 'OrcaMCP.exe', 'snapmaker-orca.exe')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) {
        $candidates += [pscustomobject]@{ Variant = 'Found on PATH'; Path = $command.Source }
    }
}

$executables = @()
$seen = @{}
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate.Path -PathType Leaf)) { continue }
    $file = Get-Item -LiteralPath $candidate.Path
    if ($seen.ContainsKey($file.FullName)) { continue }
    $seen[$file.FullName] = $true
    $executables += [pscustomobject]@{
        Variant = $candidate.Variant
        Path = $file.FullName
        ProductName = $file.VersionInfo.ProductName
        ProductVersion = $file.VersionInfo.ProductVersion
        CliSupport = 'Not tested'
        McpSupport = 'Not tested; filename and version do not establish support'
    }
}

function Test-LocalPort {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    $pending = $null
    try {
        $pending = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne($TimeoutMs)) { return 'Not reachable (timeout)' }
        $client.EndConnect($pending)
        return 'Listening; application and protocol unverified'
    }
    catch { return 'Not reachable' }
    finally {
        if ($pending) { $pending.AsyncWaitHandle.Close() }
        $client.Close()
    }
}

$ports = @(
    @{ Candidate = 'Fusion MCP'; Port = 27182; Transport = 'Streamable HTTP /mcp' },
    @{ Candidate = 'OrcaMCP community fork'; Port = 13618; Transport = 'Streamable HTTP /mcp' },
    @{ Candidate = 'Upstream draft MCP proposal'; Port = 13619; Transport = 'Proposed Streamable HTTP /mcp' },
    @{ Candidate = 'MaxEllis remote API'; Port = 13130; Transport = 'Token-authenticated REST, not an MCP endpoint' }
)
$endpoints = @($ports | ForEach-Object {
    [pscustomobject]@{
        Candidate = $_.Candidate
        Address = '127.0.0.1'
        Port = $_.Port
        ExpectedTransport = $_.Transport
        TcpStatus = Test-LocalPort $_.Port
    }
})

[pscustomobject]@{
    CheckedAtUtc = [DateTime]::UtcNow.ToString('o')
    Scope = 'Standard install locations, PATH, and four loopback TCP ports only'
    Executables = $executables
    Endpoints = $endpoints
    Conclusion = 'Inventory only. Verify MCP initialize/tools/list and live operations in both agents before integration.'
} | ConvertTo-Json -Depth 6
