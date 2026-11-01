# Project resources

Root `Project.md` stays the entrypoint for both agents. Keep its current state short and add links when creating files below `Project/`. Store design-specific evidence/notes in `Project/Context/` and skills in `Project/skills/project-<name>/SKILL.md`. Prefer links and relevant references over copying existing policy. Leave existing project files/skills where they are unless migration is requested. Existing CAD inputs/exports retain their folder conventions.

## Add a skill or context

The session may create useful local skills/context as part of authorized work. Keep `SKILL.md` frontmatter scoped (`name`, `description`), the procedure concise, and supporting scripts/references beside it. Use ordinary automatic invocation unless the user requests otherwise; preserve approval gates. Do not encode an unverified observation as a universal rule.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/project-resources.ps1 -Action NewSkill -Name interface-checks -Description 'Verify this project-specific interface and its measured fit requirements.'
# Fill in the actual project procedure, then refresh discovery and context links:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agents/scripts/project-resources.ps1 -Action Sync
```

`NewSkill` prefixes the name with `project-`; it never replaces an existing skill. The canonical procedure remains under `Project/skills/`. `Sync` generates a small `.agents/skills/project-<name>/SKILL.md` entry containing the same frontmatter and a link to that procedure. Both clients discover that entry using the existing shared skill tree; Claude exposes it under the `agentic-fusion` plugin namespace. Relative scripts/references are based on the canonical folder, not the generated entry. No global profile or extra plugin is installed.

The helper tracks hashes of its generated entries under `Project/.skill-registration.json`. It never overwrites pre-existing or manually edited entries. It can remove its own unchanged stale entry when a canonical skill is deleted, while preserving other files in that folder. On a collision, retain both procedures and report the name conflict; the canonical skill is still available through `Project.md`. Restart/reconnect a client if its catalog has not refreshed. The launchers sync registration at startup without Python or network access.

Create context files directly in `Project/Context/`, link them from `Project.md`, and run `Sync` to add missing links. An indexed directory link covers generated metadata and other resources. Keep usage/restart checkpoints in root `Project.md`; place deeper history in `Project/Context/History/`. Preserve existing `Project-History/` notes and links until an authorized migration is useful.

Discovery contracts: [Codex local skills](https://learn.chatgpt.com/docs/build-skills), [Claude plugin skills](https://code.claude.com/docs/en/plugins-reference). Generated entries use regular files to avoid Windows symlink privileges and plugin paths escaping their root.

For updating shared template resources, read the [updater guide](../../../../.updater/README.md).
