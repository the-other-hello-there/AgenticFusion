# Read-only inventory. Does not launch slicers, load models, or call MCP tools.
[CmdletBinding()]
param(
    [string]$OrcaPath,
    [ValidateRange(50, 5000)]
    [int]$TimeoutMs = 300
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$repositoryDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$helper = Join-Path $repositoryDir 'AgenticFusionTemplate\.agents\skills\orca-slice\scripts\slicer.py'
$discoveryArgs = @('-3', $helper, 'list')
if ($OrcaPath) { $discoveryArgs += @('--executable', $OrcaPath) }
$inventoryText = & py @discoveryArgs | Out-String
if ($LASTEXITCODE -ne 0) { throw 'Slicer discovery failed.' }
$inventory = $inventoryText | ConvertFrom-Json

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
    @{ Candidate = 'Upstream MCP proposal'; Port = 13619; Transport = 'Verify installed build capabilities' },
    @{ Candidate = 'MaxEllis remote API'; Port = 13130; Transport = 'Token-authenticated REST, not an MCP endpoint' }
)
[pscustomobject]@{
    CheckedAtUtc = [DateTime]::UtcNow.ToString('o')
    Scope = 'Shipped slicer discovery: install folders, PATH, registry, shortcuts, current-user Store/packages and Start apps'
    Applications = @($inventory.applications)
    DiscoveryWarnings = @($inventory.warnings)
    Endpoints = @($ports | ForEach-Object {
        [pscustomobject]@{
            Candidate = $_.Candidate
            Address = '127.0.0.1'
            Port = $_.Port
            ExpectedTransport = $_.Transport
            TcpStatus = Test-LocalPort $_.Port
        }
    })
    Conclusion = 'Inventory only. Ask which installed slicer to use, then verify that selected build and live operations in both agents.'
} | ConvertTo-Json -Depth 8
