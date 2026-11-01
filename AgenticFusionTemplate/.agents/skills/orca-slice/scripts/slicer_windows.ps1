# Inventory current-user applications, or activate one explicitly selected Store app.
[CmdletBinding()]
param([string]$AppId, [string]$OpenFile)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

if ($AppId) {
    # Use the selected app's file contract, never the default file association.
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class SlicerActivation {
    [ComImport, Guid("b63ea76d-1f85-456f-a19c-48159efa858b"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IShellItemArray {}
    [ComImport, Guid("2e941141-7f97-4756-ba1d-9decde894a3d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IApplicationActivationManager {
        [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string id,
            [MarshalAs(UnmanagedType.LPWStr)] string args, uint options, out uint pid);
        [PreserveSig] int ActivateForFile([MarshalAs(UnmanagedType.LPWStr)] string id,
            [MarshalAs(UnmanagedType.Interface)] IShellItemArray items,
            [MarshalAs(UnmanagedType.LPWStr)] string verb, out uint pid);
        [PreserveSig] int ActivateForProtocol([MarshalAs(UnmanagedType.LPWStr)] string id,
            [MarshalAs(UnmanagedType.Interface)] object items, out uint pid);
    }
    [DllImport("shell32.dll", CharSet=CharSet.Unicode, PreserveSig=false)]
    static extern void SHCreateItemFromParsingName(string path, IntPtr context,
        ref Guid iid, out IntPtr item);
    [DllImport("shell32.dll", PreserveSig=false)]
    static extern void SHCreateShellItemArrayFromShellItem(IntPtr item,
        ref Guid iid, [MarshalAs(UnmanagedType.Interface)] out IShellItemArray items);
    public static uint Open(string id, string path) {
        object manager = Activator.CreateInstance(Type.GetTypeFromCLSID(new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")));
        IntPtr item = IntPtr.Zero;
        IShellItemArray items = null;
        try {
            uint pid;
            int result;
            var activation = (IApplicationActivationManager)manager;
            if (String.IsNullOrEmpty(path)) result = activation.ActivateApplication(id, null, 0, out pid);
            else {
                var itemId = new Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE");
                var arrayId = new Guid("b63ea76d-1f85-456f-a19c-48159efa858b");
                SHCreateItemFromParsingName(path, IntPtr.Zero, ref itemId, out item);
                SHCreateShellItemArrayFromShellItem(item, ref arrayId, out items);
                result = activation.ActivateForFile(id, items, "open", out pid);
            }
            Marshal.ThrowExceptionForHR(result);
            return pid;
        } finally {
            if (items != null) Marshal.ReleaseComObject(items);
            if (item != IntPtr.Zero) Marshal.Release(item);
            Marshal.ReleaseComObject(manager);
        }
    }
}
'@
    $filePath = if ($OpenFile) { (Get-Item -LiteralPath $OpenFile).FullName } else { $null }
    $appProcess = [SlicerActivation]::Open($AppId, $filePath)
    @{ pid = $appProcess; activation = 'requested'; import_verified = $false } | ConvertTo-Json -Compress
    exit 0
}

$script:records = New-Object System.Collections.Generic.List[object]
$script:issues = New-Object System.Collections.Generic.List[string]
$pattern = '(?i)orca|bambu[ _-]?studio'
$exeNames = @('orca-slicer.exe', 'OrcaSlicer.exe', 'OrcaMCP.exe', 'snapmaker-orca.exe', 'bambu-studio.exe')
function Add-Executable([string]$Path, [string]$Name, [string]$Source) {
    if (-not $Path -or [IO.Path]::GetExtension($Path) -ine '.exe') { return }
    if ([IO.Path]::GetFileName($Path) -match '(?i)unins|setup|install|updat|crash') { return }
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $file = Get-Item -LiteralPath $Path
        $label = if ($file.VersionInfo.ProductName) { $file.VersionInfo.ProductName } else { $Name }
        $script:records.Add(@{ name = $label; version = $file.VersionInfo.ProductVersion;
            executable = $file.FullName; source = $Source })
    }
}
function Add-Folder([string]$Folder, [string]$Name, [string]$Source) {
    if (-not $Folder -or -not (Test-Path -LiteralPath $Folder -PathType Container)) { return }
    foreach ($exeName in $exeNames) { Add-Executable (Join-Path $Folder $exeName) $Name $Source }
    Get-ChildItem -LiteralPath $Folder -Filter '*.exe' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.BaseName -match $pattern -and $_.BaseName -notmatch '(?i)console' } |
        ForEach-Object { Add-Executable $_.FullName $Name $Source }
}

try {
    foreach ($root in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:LOCALAPPDATA\Programs", $env:LOCALAPPDATA)) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match $pattern } |
            ForEach-Object { Add-Folder $_.FullName $_.Name 'install folder' }
    }
    foreach ($exeName in $exeNames) {
        Get-Command $exeName -CommandType Application -All -ErrorAction SilentlyContinue |
            ForEach-Object { Add-Executable $_.Source $_.Name 'PATH' }
    }
} catch { $script:issues.Add("Folders/PATH: $($_.Exception.Message)") }

try {
    foreach ($hive in @('HKCU:', 'HKLM:')) {
        foreach ($subkey in @('Software\Microsoft\Windows\CurrentVersion\Uninstall',
                              'Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')) {
            Get-ItemProperty -Path "$hive\$subkey\*" -ErrorAction SilentlyContinue |
                Where-Object { $_.DisplayName -match $pattern } | ForEach-Object {
                    Add-Folder $_.InstallLocation $_.DisplayName 'installer registry'
                    if ($_.DisplayIcon -match '^"([^\"]+\.exe)"|^(.+?\.exe)(?:,|$)') {
                        $icon = if ($Matches[1]) { $Matches[1] } else { $Matches[2] }
                        Add-Executable $icon $_.DisplayName 'installer registry'
                        Add-Folder (Split-Path -Parent $icon) $_.DisplayName 'installer registry'
                    }
                }
        }
        Get-ChildItem -Path "$hive\Software\Microsoft\Windows\CurrentVersion\App Paths" -ErrorAction SilentlyContinue |
            Where-Object { $_.PSChildName -match $pattern } | ForEach-Object {
                Add-Executable ($_.GetValue('')) $_.PSChildName 'App Paths'
            }
    }
} catch { $script:issues.Add("Registry: $($_.Exception.Message)") }

try {
    $shortcutShell = New-Object -ComObject WScript.Shell
    foreach ($root in @("$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
                        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
                        [Environment]::GetFolderPath('DesktopDirectory'),
                        [Environment]::GetFolderPath('CommonDesktopDirectory'))) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Filter '*.lnk' -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.BaseName -match $pattern } | ForEach-Object {
                $shortcut = $shortcutShell.CreateShortcut($_.FullName)
                Add-Executable $shortcut.TargetPath $_.BaseName 'shortcut'
            }
    }
} catch { $script:issues.Add("Shortcuts: $($_.Exception.Message)") }

# Get-StartApps also finds packages with generic publisher/package names.
$startApps = @()
try { $startApps = @(Get-StartApps -ErrorAction Stop | Where-Object { $_.Name -match $pattern -or $_.AppID -match $pattern }) }
catch { $script:issues.Add("Start apps: $($_.Exception.Message)") }
$foundIds = @{}
try {
    Get-AppxPackage -ErrorAction Stop | ForEach-Object {
        $package = $_
        $matchesStart = @($startApps | Where-Object { $_.AppID -like "$($package.PackageFamilyName)!*" })
        if ($package.Name -notmatch $pattern -and $matchesStart.Count -eq 0) { return }
        try {
            $manifest = Get-AppxPackageManifest -Package $package.PackageFullName -ErrorAction Stop
            foreach ($app in $manifest.Package.Applications.Application) {
                $id = "$($package.PackageFamilyName)!$($app.Id)"
                $start = $matchesStart | Where-Object { $_.AppID -eq $id } | Select-Object -First 1
                $label = if ($start) { $start.Name } else { $package.Name }
                $binary = $null
                if ($app.Executable -and $app.Executable -notmatch '\$') {
                    $candidate = Join-Path $package.InstallLocation $app.Executable
                    if (Test-Path -LiteralPath $candidate -PathType Leaf) { $binary = $candidate }
                }
                $script:records.Add(@{ name = $label; version = $package.Version.ToString();
                    executable = $binary; app_id = $id; source = 'Windows Store/package' })
                $foundIds[$id] = $true
            }
        } catch { $script:issues.Add("Package $($package.Name): $($_.Exception.Message)") }
    }
} catch { $script:issues.Add("Packages: $($_.Exception.Message)") }
foreach ($app in $startApps) {
    if ($app.AppID -match '!' -and -not $foundIds.ContainsKey($app.AppID)) {
        $script:records.Add(@{ name = $app.Name; app_id = $app.AppID; source = 'Windows Start app' })
    }
}
@{ applications = @($script:records.ToArray()); warnings = @($script:issues.ToArray()) } | ConvertTo-Json -Depth 5
