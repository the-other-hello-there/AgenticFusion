# Verify optional MCP entries survive both launchers without launching either app.
$ErrorActionPreference = 'Stop'
$benchmarkDir = $PSScriptRoot
$repositoryDir = Split-Path -Parent $benchmarkDir
$templateDir = Join-Path $repositoryDir 'AgenticFusionTemplate'
$runsDir = Join-Path $benchmarkDir '.runs'
$testRoot = Join-Path $runsDir ([guid]::NewGuid().ToString('N'))
$utf8 = New-Object System.Text.UTF8Encoding($false)

try {
    New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
    foreach ($firstLauncher in @('Fusion-Claude.bat', 'Fusion-Codex.bat')) {
        $project = Join-Path $testRoot $firstLauncher.Replace('.bat', ' fresh copy')
        New-Item -ItemType Directory -Path $project | Out-Null
        $projectFile = Join-Path $project 'Project.md'
        [System.IO.File]::WriteAllText($projectFile, "# Project: preserve verified context`n", $utf8)
        $originalContext = [IO.File]::ReadAllText($projectFile)
        $slicingFile = Join-Path $project 'FDM-Slicing.md'
        [System.IO.File]::WriteAllText($slicingFile, "# FDM preferences`nUser preference: preserve this existing entry.`n", $utf8)
        $slicingHash = (Get-FileHash -LiteralPath $slicingFile).Hash
        $printerFile = Join-Path $project 'Printers.json'
        $printerRecord = Get-Content -LiteralPath (Join-Path $templateDir '.agents\skills\printer-library\assets\printer.example.json') -Raw | ConvertFrom-Json
        $printerLibrary = @{ schema_version = 1; printers = @($printerRecord) } | ConvertTo-Json -Depth 50
        [System.IO.File]::WriteAllText($printerFile, $printerLibrary, $utf8)
        $printerHash = (Get-FileHash -LiteralPath $printerFile).Hash
        $bootstrap = & (Join-Path $templateDir $firstLauncher) $project --setup-only 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0 -or $bootstrap -match '(?m)^Error:') { throw "Bootstrap failed:`n$bootstrap" }
        if (-not [IO.File]::ReadAllText($projectFile).StartsWith($originalContext) -or
            [IO.File]::ReadAllText($projectFile) -notmatch '\]\(Project/\)') {
            throw 'Setup must preserve existing project context and append its project-resource index.'
        }
        $contextHash = (Get-FileHash -LiteralPath $projectFile).Hash
        foreach ($name in @('SKILL.md', 'references\startup.md', 'references\workflow.md',
                            'references\settings.md', 'references\layer-height.md', 'references\support-materials.md', 'scripts\start_orca.py',
                            'scripts\slicer.py', 'scripts\slicer_windows.ps1')) {
            if (-not (Test-Path -LiteralPath (Join-Path $project ".agents\skills\orca-slice\$name"))) {
                throw "Bootstrap omitted Orca skill file: $name"
            }
        }
        foreach ($name in @('printer-library\SKILL.md', 'printer-library\references\format.md',
                           'printer-library\assets\printer.example.json', 'printer-library\scripts\printer_library.py',
                           'fdm-calibrate\SKILL.md', 'fdm-calibrate\references\practice.md', 'slice-compare\SKILL.md',
                           'application-session\SKILL.md', 'application-session\references\lifecycle.md')) {
            if (-not (Test-Path -LiteralPath (Join-Path $project ".agents\skills\$name"))) {
                throw "Bootstrap omitted slicing skill file: $name"
            }
        }
        if (-not (Test-Path -LiteralPath (Join-Path $project '.agents\scripts\application-session.ps1'))) {
            throw 'Bootstrap omitted the shared application-session helper.'
        }
        $helper = Join-Path $project '.agents\skills\orca-slice\scripts\start_orca.py'
        $setup = & py -3 $helper --setup-only 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { throw "Orca setup failed:`n$setup" }
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
                $settings.enabledMcpjsonServers -notcontains 'orcaslicer' -or
                $settings.autoMemoryEnabled -ne $false -or
                (Get-FileHash -LiteralPath $projectFile).Hash -ne $contextHash -or
                (Get-FileHash -LiteralPath $slicingFile).Hash -ne $slicingHash -or
                (Get-FileHash -LiteralPath $printerFile).Hash -ne $printerHash) {
                throw "$launcher changed optional MCP configuration or project context."
            }
        }
    }
    Write-Output 'Combined setup passed in two fresh copies, starting with each agent and switching to the other. Both MCP entries, Project.md, FDM-Slicing.md, and existing printer definitions were preserved.'
}
finally {
    $absoluteRoot = [System.IO.Path]::GetFullPath($testRoot).TrimEnd('\')
    $absoluteParent = [System.IO.Path]::GetFullPath($runsDir).TrimEnd('\')
    $leafGuid = [guid]::Empty
    if (-not [System.IO.Path]::GetDirectoryName($absoluteRoot).Equals($absoluteParent, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not [guid]::TryParseExact([System.IO.Path]::GetFileName($absoluteRoot), 'N', [ref]$leafGuid)) {
        throw "Refusing cleanup outside Benchmarking/.runs: $absoluteRoot"
    }
    if (Test-Path -LiteralPath $absoluteRoot) { Remove-Item -LiteralPath $absoluteRoot -Recurse -Force }
}
