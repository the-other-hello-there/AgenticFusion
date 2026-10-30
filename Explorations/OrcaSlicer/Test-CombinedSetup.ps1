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
        New-Item -ItemType Directory -Path $project | Out-Null
        $projectFile = Join-Path $project 'Project.md'
        [System.IO.File]::WriteAllText($projectFile, "# Project: preserve verified context`n", $utf8)
        $contextHash = (Get-FileHash -LiteralPath $projectFile).Hash
        $slicingFile = Join-Path $project 'FDM-Slicing.md'
        [System.IO.File]::WriteAllText($slicingFile, "# FDM preferences`nUser preference: preserve this existing entry.`n", $utf8)
        $slicingHash = (Get-FileHash -LiteralPath $slicingFile).Hash
        $printerFile = Join-Path $project 'Printers.json'
        $printerRecord = Get-Content -LiteralPath (Join-Path $templateDir '.agents\skills\printer-library\assets\printer.example.json') -Raw | ConvertFrom-Json
        $printerLibrary = @{ schema_version = 1; printers = @($printerRecord) } | ConvertTo-Json -Depth 50
        [System.IO.File]::WriteAllText($printerFile, $printerLibrary, $utf8)
        $printerHash = (Get-FileHash -LiteralPath $printerFile).Hash
        $reviewPolicyFile = Join-Path $project 'Review-Policy.json'
        $reviewPolicy = Get-Content -LiteralPath (Join-Path $templateDir 'Review-Policy.json') -Raw | ConvertFrom-Json
        $reviewPolicy.max_review_ratio = '0.12'
        [System.IO.File]::WriteAllText($reviewPolicyFile, ($reviewPolicy | ConvertTo-Json -Depth 20), $utf8)
        $reviewPolicyHash = (Get-FileHash -LiteralPath $reviewPolicyFile).Hash
        $bootstrap = & (Join-Path $templateDir $firstLauncher) $project --setup-only 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0 -or $bootstrap -match '(?m)^Error:') { throw "Bootstrap failed:`n$bootstrap" }
        foreach ($name in @('SKILL.md', 'references\startup.md', 'references\workflow.md', 'scripts\start_orca.py')) {
            if (-not (Test-Path -LiteralPath (Join-Path $project ".agents\skills\orca-slice\$name"))) {
                throw "Bootstrap omitted Orca skill file: $name"
            }
        }
        foreach ($name in @('printer-library\SKILL.md', 'printer-library\references\format.md',
                           'printer-library\assets\printer.example.json', 'printer-library\scripts\printer_library.py',
                           'fdm-calibrate\SKILL.md', 'fdm-calibrate\references\practice.md', 'slice-compare\SKILL.md')) {
            if (-not (Test-Path -LiteralPath (Join-Path $project ".agents\skills\$name"))) {
                throw "Bootstrap omitted slicing skill file: $name"
            }
        }
        if (-not (Test-Path -LiteralPath (Join-Path $project '.agents\scripts\review_guard.py'))) {
            throw 'Bootstrap omitted the shared independent-review runtime.'
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
                (Get-FileHash -LiteralPath $printerFile).Hash -ne $printerHash -or
                (Get-FileHash -LiteralPath $reviewPolicyFile).Hash -ne $reviewPolicyHash) {
                throw "$launcher changed optional MCP configuration or project context."
            }
        }
    }
    Write-Output 'Combined setup passed in two fresh copies. Both agents preserved MCP entries, Project.md, slicing preferences, printer definitions, and existing review policy.'
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
