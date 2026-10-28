# Verify optional MCP entries survive both launchers without launching either app.
$ErrorActionPreference = 'Stop'
$explorationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryDir = Split-Path -Parent (Split-Path -Parent $explorationDir)
$templateDir = Join-Path $repositoryDir 'AgenticFusionTemplate'
$localDir = Join-Path $explorationDir '.local'
$testRoot = Join-Path $localDir ([guid]::NewGuid().ToString('N'))
$utf8 = New-Object System.Text.UTF8Encoding($false)

try {
    New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
    foreach ($firstLauncher in @('Fusion-Claude.bat', 'Fusion-Codex.bat')) {
        $project = Join-Path $testRoot $firstLauncher.Replace('.bat', ' fresh copy')
        Copy-Item -LiteralPath $templateDir -Destination $project -Recurse
        Copy-Item -LiteralPath (Join-Path $explorationDir 'examples\claude.mcp.json.example') -Destination (Join-Path $project '.mcp.json') -Force
        Copy-Item -LiteralPath (Join-Path $explorationDir 'examples\codex.config.toml.example') -Destination (Join-Path $project '.codex\config.toml') -Force
        $projectFile = Join-Path $project 'Project.md'
        [System.IO.File]::WriteAllText($projectFile, "# Project: preserve verified context`n", $utf8)
        $contextHash = (Get-FileHash -LiteralPath $projectFile).Hash
        $otherLauncher = if ($firstLauncher -eq 'Fusion-Claude.bat') { 'Fusion-Codex.bat' } else { 'Fusion-Claude.bat' }
        foreach ($launcher in @($firstLauncher, $otherLauncher)) {
            $output = & (Join-Path $project $launcher) --setup-only 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0 -or $output -match '(?m)^Error:') { throw "$launcher failed:`n$output" }
            $claude = Get-Content -LiteralPath (Join-Path $project '.mcp.json') -Raw | ConvertFrom-Json
            $codex = [System.IO.File]::ReadAllText((Join-Path $project '.codex\config.toml'))
            $settings = Get-Content -LiteralPath (Join-Path $project 'settings.json') -Raw | ConvertFrom-Json
            if ($claude.mcpServers.fusion.url -ne 'http://127.0.0.1:27182/mcp' -or
                $claude.mcpServers.orcaslicer.url -ne 'http://127.0.0.1:13618/mcp' -or
                $codex -notmatch '(?m)^\[mcp_servers\.fusion\]\r?$' -or
                $codex -notmatch '(?m)^\[mcp_servers\.orcaslicer\]\r?$' -or
                $codex -notmatch 'http://127\.0\.0\.1:27182/mcp' -or
                $codex -notmatch 'http://127\.0\.0\.1:13618/mcp' -or
                $settings.enabledMcpjsonServers -notcontains 'fusion' -or
                $settings.autoMemoryEnabled -ne $false -or
                (Get-FileHash -LiteralPath $projectFile).Hash -ne $contextHash) {
                throw "$launcher changed optional MCP configuration or project context."
            }
        }
    }
    Write-Output 'Combined setup passed in two fresh copies, starting with each agent and switching to the other. Both MCP entries and Project.md were preserved.'
}
finally {
    $absoluteRoot = [System.IO.Path]::GetFullPath($testRoot).TrimEnd('\')
    $absoluteParent = [System.IO.Path]::GetFullPath($localDir).TrimEnd('\')
    $leafGuid = [guid]::Empty
    if (-not [System.IO.Path]::GetDirectoryName($absoluteRoot).Equals($absoluteParent, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not [guid]::TryParseExact([System.IO.Path]::GetFileName($absoluteRoot), 'N', [ref]$leafGuid)) {
        throw "Refusing cleanup outside the exploration's .local directory: $absoluteRoot"
    }
    if (Test-Path -LiteralPath $absoluteRoot) { Remove-Item -LiteralPath $absoluteRoot -Recurse -Force }
}
