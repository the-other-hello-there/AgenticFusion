# Template updater

Run the root `updater.bat` from a copied project. This folder contains its implementation, fingerprint manifest and guide. New updater state, incoming candidates and backups also stay here. Python 3.11+ and Windows PowerShell are needed; Git is not. Ordinary Fusion startup never downloads updates.

```powershell
# Choose a branch from the prompt:
.\updater.bat --check
.\updater.bat --project-dir .
# Or pass the user's branch choice explicitly:
.\updater.bat --branch 'experimental-feature/secondary-agent-verification' --check
.\updater.bat --branch 'experimental-feature/secondary-agent-verification'
.\updater.bat --list-branches
# From a fresh template download, update an older project:
.\updater.bat --project-dir 'C:\Designs\Existing project'
# Or use a verified offline template:
.\updater.bat --project-dir 'C:\Designs\Existing project' --source 'C:\Downloads\AgenticFusion-main\AgenticFusionTemplate'
```

The updater paginates through the repository's live GitHub branch list and asks which branch to use, by number or exact name. It does not keep a hardcoded allowlist, so newly created branches are available automatically. Enter accepts the suggested branch: the last successful choice, the installed template's published branch, or main for older copies without branch metadata. A deleted branch requires an explicit new choice; cancellation, missing input or discovery errors stop without applying an update. Agents should ask the user for a branch and pass that choice with `--branch`; `--list-branches` returns all available names as JSON. A current project reports `Already up to date` and makes no writes or backup. `--source` stays offline, skips the prompt and cannot be combined with `--branch`.

The selected branch is resolved through [GitHub's branch API](https://docs.github.com/en/rest/branches/branches) to one commit. The updater downloads that archive and verifies its runtime files against `.updater/Template-Manifest.json`, including its branch when recorded. Tags and similarly named branches are never substituted. Windows downloads use verified native HTTPS/certificate-chain support. `--check` writes nothing to the project. Download, archive/path and hash failures stop before changing it. Apply updates at a saved checkpoint, then restart agent sessions to reload saved instructions/catalogs; the updater never starts/closes an application or operates a printer.

Select the matching experimental branch to retain its integration. Selecting main deliberately replaces unchanged experimental runtime files with main's template. Existing `Review-Policy.json` is preserved even when switching away from the review branch; protected reviewer/controller installations remain outside the template update. Offline sources record their published branch when supplied by their manifest.

- Root `Project.md`, everything below `Project/`, CAD/exports and unknown added files/skills remain outside upstream ownership. Existing printer definitions, slicing preferences, review policy and MCP/agent settings are preserved. Updating alone does not create project context or append to `Project.md`; normal launcher setup maintains its project-resource index.
- Update a managed file only when it matches its recorded original or a known historical stock fingerprint. Normalize BOM/CRLF for comparison. An unrecognized edit/collision holds the whole template update and stages incoming candidates under `.updater/incoming/`. Move project-only rules into indexed project resources or merge deliberately; never erase edits just to clear a conflict.
- Remove an obsolete managed file only when it was owned by the installed version, is absent from the selected version, and still matches its installed fingerprint. Historical fingerprints alone never authorize deleting an untracked or project-created file. Modified obsolete files and all unknown files remain. Backups and a journal live under `.updater/backups/`; the active baseline is `.updater/state.json`. Write failure triggers rollback; concurrent edits are preserved and reported. Generated updater state/recovery directories are ignored by Git.
- A customized core launcher/skill may need manual integration before it matches upstream again. Report unresolved conflicts rather than claiming a fully updated project.

## Upgrade the former updater layout

Installed `Update-Template.bat` versions expect the old root manifest location. Upgrade them by downloading the fresh template and running its `updater.bat --project-dir 'C:\Designs\Existing project'`. Do not manually overwrite project instructions to migrate.

The new updater reads the former root manifest or `Project/.template-update/state.json` for ownership. It retires unchanged old updater files/root manifest only when their fingerprints are known. Customized old files remain and are reported. Existing recovery history below `Project/.template-update/` stays untouched; all new active state/recovery is under `.updater/`. Once migrated, use the project's `updater.bat`.

The maintenance fingerprint builder/tests belong outside the distributed folder. Rebuild the manifest after runtime source changes, retaining historical and retired-file fingerprints so existing projects can migrate safely.
