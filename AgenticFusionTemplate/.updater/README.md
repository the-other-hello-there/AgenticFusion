# Template updater

Run the root `updater.bat` from a copied project. This folder contains its implementation, fingerprint manifest and guide. New updater state, incoming candidates and backups also stay here. Python 3.11+ and Windows PowerShell are needed; Git is not. Ordinary Fusion startup never downloads updates.

```powershell
.\updater.bat --check
.\updater.bat --project-dir .
# From a fresh template download, update an older project:
.\updater.bat --project-dir 'C:\Designs\Existing project'
# Or use a verified offline template:
.\updater.bat --project-dir 'C:\Designs\Existing project' --source 'C:\Downloads\AgenticFusion-main\AgenticFusionTemplate'
```

The updater resolves GitHub main to one commit, downloads that archive and verifies its runtime files against `.updater/Template-Manifest.json`. Windows downloads use verified native HTTPS/certificate-chain support. `--check` writes nothing to the project. Download, archive/path and hash failures stop before changing it. Apply updates at a saved checkpoint, then restart agent sessions to reload saved instructions/catalogs; the updater never starts/closes an application or operates a printer.

- Root `Project.md`, everything below `Project/`, CAD/exports and unknown added files/skills remain outside upstream ownership. Existing printer definitions, slicing preferences and MCP/agent settings are preserved. Updating alone does not create project context or append to `Project.md`; normal launcher setup maintains its project-resource index.
- Update a managed file only when it matches its recorded original or a known historical stock fingerprint. Normalize BOM/CRLF for comparison. An unrecognized edit/collision holds the whole template update and stages incoming candidates under `.updater/incoming/`. Move project-only rules into indexed project resources or merge deliberately; never erase edits just to clear a conflict.
- Remove an obsolete managed file only when its fingerprint still matches. Modified obsolete files and all unknown files remain. Backups and a journal live under `.updater/backups/`; the active baseline is `.updater/state.json`. Write failure triggers rollback; concurrent edits are preserved and reported. Generated updater state/recovery directories are ignored by Git.
- A customized core launcher/skill may need manual integration before it matches upstream again. Report unresolved conflicts rather than claiming a fully updated project.

## Upgrade the former updater layout

Installed `Update-Template.bat` versions expect the old root manifest location. Upgrade them by downloading the fresh template and running its `updater.bat --project-dir 'C:\Designs\Existing project'`. Do not manually overwrite project instructions to migrate.

The new updater reads the former root manifest or `Project/.template-update/state.json` for ownership. It retires unchanged old updater files/root manifest only when their fingerprints are known. Customized old files remain and are reported. Existing recovery history below `Project/.template-update/` stays untouched; all new active state/recovery is under `.updater/`. Once migrated, use the project's `updater.bat`.

The maintenance fingerprint builder/tests belong outside the distributed folder. Rebuild the manifest after runtime source changes, retaining historical and retired-file fingerprints so existing projects can migrate safely.
