# Verify optional MCP entries survive both launchers without launching either app.
$ErrorActionPreference = 'Stop'
$explorationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repositoryDir = Split-Path -Parent (Split-Path -Parent $explorationDir)
$templateDir = Join-Path $repositoryDir 'AgenticFusionTemplate'
$localDir = Join-Path $explorationDir '.local'
$testRoot = Join-Path $localDir ([guid]::NewGuid().ToString('N'))
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Assert-ProjectFiles {
    param([string]$Project, [System.Collections.IDictionary]$Expected)
    foreach ($entry in $Expected.GetEnumerator()) {
        $file = Join-Path $Project $entry.Key
        if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-FileHash -LiteralPath $file).Hash -ne $entry.Value) {
            throw "Setup omitted or replaced portable/context file: $($entry.Key)"
        }
    }
}

try {
    New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
    $sourceTemplate = Join-Path $testRoot 'template source'
    Copy-Item -LiteralPath $templateDir -Destination $sourceTemplate -Recurse
    $excludedFiles = @('sessions\stale.json', '.agents\skills\orca-slice\scripts\__pycache__\stale.pyc')
    foreach ($name in $excludedFiles) {
        $file = Join-Path $sourceTemplate $name
        New-Item -ItemType Directory -Path (Split-Path -Parent $file) -Force | Out-Null
        [System.IO.File]::WriteAllText($file, 'Synthetic runtime data: do not distribute.', $utf8)
    }
    foreach ($firstLauncher in @('Fusion-Claude.bat', 'Fusion-Codex.bat')) {
        $project = Join-Path $testRoot $firstLauncher.Replace('.bat', ' fresh copy')
        New-Item -ItemType Directory -Path $project | Out-Null
        $projectFile = Join-Path $project 'Project.md'
        [System.IO.File]::WriteAllText($projectFile, "# Project: preserve verified context`n", $utf8)
        $slicingFile = Join-Path $project 'FDM-Slicing.md'
        [System.IO.File]::WriteAllText($slicingFile, "# FDM preferences`nUser preference: preserve this existing entry.`n", $utf8)
        $printerFile = Join-Path $project 'Printers.json'
        $printerRecord = Get-Content -LiteralPath (Join-Path $templateDir '.agents\skills\printer-library\assets\printer.example.json') -Raw | ConvertFrom-Json
        $printerLibrary = @{ schema_version = 1; printers = @($printerRecord) } | ConvertTo-Json -Depth 50
        [System.IO.File]::WriteAllText($printerFile, $printerLibrary, $utf8)
        $reviewPolicyFile = Join-Path $project 'Review-Policy.json'
        $reviewPolicy = Get-Content -LiteralPath (Join-Path $templateDir 'Review-Policy.json') -Raw | ConvertFrom-Json
        $reviewPolicy.max_review_ratio = '0.12'
        [System.IO.File]::WriteAllText($reviewPolicyFile, ($reviewPolicy | ConvertTo-Json -Depth 20), $utf8)
        foreach ($name in @('AGENTS.md', 'CLAUDE.md', '.agents\skills\fusion-model\references\mcp.md')) {
            $file = Join-Path $project $name
            New-Item -ItemType Directory -Path (Split-Path -Parent $file) -Force | Out-Null
            [System.IO.File]::WriteAllText($file, "# Preserve this project's customized $name`n", $utf8)
        }
        $otherLauncher = if ($firstLauncher -eq 'Fusion-Claude.bat') { 'Fusion-Codex.bat' } else { 'Fusion-Claude.bat' }
        $localLauncher = [System.IO.File]::ReadAllText((Join-Path $templateDir $otherLauncher)).Replace('@echo off', "@echo off`r`nrem Preserve this project's launcher edits.")
        [System.IO.File]::WriteAllText((Join-Path $project $otherLauncher), $localLauncher, $utf8)
        $expected = @{ 'Project.md' = (Get-FileHash -LiteralPath $projectFile).Hash }
        foreach ($sourceFile in Get-ChildItem -LiteralPath $templateDir -File -Recurse -Force) {
            $name = $sourceFile.FullName.Substring($templateDir.Length + 1)
            $target = Join-Path $project $name
            $expected[$name] = if (Test-Path -LiteralPath $target) { (Get-FileHash -LiteralPath $target).Hash } else { (Get-FileHash -LiteralPath $sourceFile.FullName).Hash }
        }
        $bootstrap = & (Join-Path $sourceTemplate $firstLauncher) $project --setup-only 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0 -or $bootstrap -match '(?m)^Error:') { throw "Bootstrap failed:`n$bootstrap" }
        Assert-ProjectFiles $project $expected
        foreach ($name in $excludedFiles) {
            if (Test-Path -LiteralPath (Join-Path $project $name)) { throw "Setup copied excluded runtime data: $name" }
        }
        $helper = Join-Path $project '.agents\skills\orca-slice\scripts\start_orca.py'
        $setup = & py -3 $helper --setup-only 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { throw "Orca setup failed:`n$setup" }
        foreach ($name in @('.mcp.json', '.codex\config.toml', 'settings.json')) {
            $expected[$name] = (Get-FileHash -LiteralPath (Join-Path $project $name)).Hash
        }
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
                $settings.autoMemoryEnabled -ne $false) {
                throw "$launcher changed optional MCP configuration or project context."
            }
            Assert-ProjectFiles $project $expected
        }
    }
    Write-Output 'Combined setup passed in two fresh copies: all portable files copied, runtime data excluded, and both agents preserved MCP entries, context, printer definitions, review policy, customized instructions, skills and launchers.'
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
