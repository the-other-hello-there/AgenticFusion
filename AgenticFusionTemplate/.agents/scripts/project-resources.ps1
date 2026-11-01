param(
    [ValidateSet('Initialize','Sync','NewSkill')][string]$Action = 'Sync',
    [string]$ProjectDir = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Name,
    [string]$Description
)
$ErrorActionPreference = 'Stop'
$ProjectDir = [IO.Path]::GetFullPath($ProjectDir).TrimEnd('\')
if ($ProjectDir -eq [IO.Path]::GetPathRoot($ProjectDir).TrimEnd('\')) { throw 'Use a project subfolder rather than a filesystem root.' }
$utf8 = New-Object Text.UTF8Encoding($false)

function Assert-ProjectPath([string]$Path) {
    $absolute = [IO.Path]::GetFullPath($Path)
    if (-not $absolute.StartsWith($ProjectDir + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Path leaves project: $Path" }
    $cursor = $absolute
    while ($cursor -ne $ProjectDir) {
        if (Test-Path -LiteralPath $cursor) {
            if ((Get-Item -LiteralPath $cursor -Force).LinkType -in @('Junction','SymbolicLink')) { throw "Project resource path is a filesystem link: $cursor" }
        }
        $cursor = Split-Path -Parent $cursor
    }
}
function Write-ResourceText([string]$Path, [string]$Text) {
    Assert-ProjectPath $Path
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    [IO.File]::WriteAllText($Path, $Text, $utf8)
}
function Get-ResourceHash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Add-ResourceLink([string]$Relative, [string]$Label) {
    $file = Join-Path $ProjectDir 'Project.md'
    Assert-ProjectPath $file
    $encoding = $utf8
    if (Test-Path -LiteralPath $file) {
        $reader = New-Object IO.StreamReader($file, $utf8, $true)
        try { $text = $reader.ReadToEnd(); $encoding = $reader.CurrentEncoding }
        finally { $reader.Dispose() }
    } else {
        $text = "# Project: TBD`n`n## Current state`n`n- **Design purpose:** TBD`n- **Open items:** TBD`n"
        Write-ResourceText $file $text
    }
    $target = (($Relative.Replace('\','/').Split('/') | ForEach-Object { [uri]::EscapeDataString($_) }) -join '/')
    if ($text.Contains('](' + $target + ')')) { return }
    $addition = if ($text.EndsWith("`n")) { '' } else { "`n" }
    if ($text -notmatch '(?m)^## Project resources\s*$') { $addition += "`n## Project resources`n" }
    $addition += "`n- [$Label]($target)`n"
    [IO.File]::AppendAllText($file, $addition, $encoding)
}

$resources = Join-Path $ProjectDir 'Project'
Assert-ProjectPath $resources
foreach ($relative in @('Project','Project\Context','Project\skills')) {
    $folder = Join-Path $ProjectDir $relative
    Assert-ProjectPath $folder
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}
Add-ResourceLink 'Project/' 'Project-specific resources'
if ($Action -eq 'Initialize') { return }

if ($Action -eq 'NewSkill') {
    if ($Name -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$') { throw 'Use a lowercase, hyphen-separated skill name.' }
    if (-not $Name.StartsWith('project-')) { $Name = 'project-' + $Name }
    if ($Name.Length -gt 63 -or [string]::IsNullOrWhiteSpace($Description)) { throw 'Supply a short name and a meaningful skill description.' }
    $skillFile = Join-Path $resources "skills\$Name\SKILL.md"
    Assert-ProjectPath $skillFile
    if (Test-Path -LiteralPath (Split-Path -Parent $skillFile)) { throw "Skill already exists: $Name" }
    $yamlDescription = $Description | ConvertTo-Json -Compress
    Write-ResourceText $skillFile "---`nname: $Name`ndescription: $yamlDescription`n---`n`n# $Name`n`nWrite the verified project-specific procedure here before using this skill.`n"
}

$registryFile = Join-Path $resources '.skill-registration.json'
Assert-ProjectPath $registryFile
$previous = @{}
if (Test-Path -LiteralPath $registryFile) {
    $registry = [IO.File]::ReadAllText($registryFile) | ConvertFrom-Json
    if ($registry.schema_version -ne 1) { throw 'Unsupported project skill registration state.' }
    foreach ($entry in $registry.entries) {
        if ($entry.name -notmatch '^project-[a-z0-9]+(?:-[a-z0-9]+)*$' -or $entry.sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Invalid project skill registration state.' }
        $previous[$entry.name] = $entry.sha256
    }
}
$registered = @()
$seen = @{}
foreach ($folder in @(Get-ChildItem -LiteralPath (Join-Path $resources 'skills') -Directory)) {
    Assert-ProjectPath $folder.FullName
    $skillFile = Join-Path $folder.FullName 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) { continue }
    Assert-ProjectPath $skillFile
    $relative = 'Project/skills/' + $folder.Name + '/SKILL.md'
    Add-ResourceLink $relative $folder.Name
    $text = [IO.File]::ReadAllText($skillFile)
    $header = [regex]::Match($text, '\A---\r?\n(.*?)^---\s*\r?\n', 'Singleline,Multiline')
    $nameMatch = [regex]::Match($header.Groups[1].Value, '(?m)^name:\s*(project-[a-z0-9]+(?:-[a-z0-9]+)*)\s*$')
    if (-not $header.Success -or -not $nameMatch.Success -or $nameMatch.Groups[1].Value -ne $folder.Name -or $text -notmatch '(?m)^description:\s*\S') {
        Write-Warning "Indexed $relative; native registration needs matching project-prefixed name and description frontmatter."
        continue
    }
    $skillName = $folder.Name
    $seen[$skillName] = $true
    $adapter = Join-Path $ProjectDir ".agents\skills\$skillName\SKILL.md"
    Assert-ProjectPath $adapter
    $body = "`nRead [the canonical project skill](../../../$relative) before acting. Its instructions and relative resources are based in ``Project/skills/$skillName/``. This generated discovery entry mirrors metadata only; edit the canonical skill, then run project-resources.ps1 -Action Sync.`n"
    $entryText = $header.Value.Replace("`r`n","`n") + $body
    if (Test-Path -LiteralPath $adapter) {
        $current = Get-ResourceHash $adapter
        if (-not $previous.ContainsKey($skillName) -or $current -ne $previous[$skillName]) {
            Write-Warning "Preserved existing or customized discovery entry: .agents/skills/$skillName/SKILL.md. The canonical skill remains linked from Project.md."
            if ($previous.ContainsKey($skillName)) { $registered += [ordered]@{ name = $skillName; sha256 = $previous[$skillName] } }
            continue
        }
    }
    Write-ResourceText $adapter $entryText
    $registered += [ordered]@{ name = $skillName; sha256 = (Get-ResourceHash $adapter) }
}
foreach ($skillName in $previous.Keys) {
    if ($seen.ContainsKey($skillName)) { continue }
    $adapter = Join-Path $ProjectDir ".agents\skills\$skillName\SKILL.md"
    Assert-ProjectPath $adapter
    if ((Test-Path -LiteralPath $adapter) -and (Get-ResourceHash $adapter) -eq $previous[$skillName]) {
        Remove-Item -LiteralPath $adapter -Force
        $folder = Split-Path -Parent $adapter
        if (@(Get-ChildItem -LiteralPath $folder -Force).Count -eq 0) { Remove-Item -LiteralPath $folder -Force }
    }
}
function Get-ContextFiles([string]$Folder) {
    foreach ($entry in @(Get-ChildItem -LiteralPath $Folder -Force)) {
        Assert-ProjectPath $entry.FullName
        if ($entry.PSIsContainer) { Get-ContextFiles $entry.FullName }
        else { $entry }
    }
}
foreach ($file in @(Get-ContextFiles (Join-Path $resources 'Context'))) {
    Assert-ProjectPath $file.FullName
    $relative = $file.FullName.Substring($ProjectDir.Length + 1).Replace('\','/')
    Add-ResourceLink $relative $file.Name.Replace('[','').Replace(']','')
}
Write-ResourceText $registryFile (([ordered]@{ schema_version = 1; entries = @($registered) } | ConvertTo-Json -Depth 8) + "`n")
