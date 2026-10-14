---
name: fusion-model
description: Inspect with scripts, build, edit, and verify parametric Autodesk Fusion designs through the local MCP server. Use for modeling, timeline edits, components, sketches, features, and saved design changes.
---

# Fusion modeling

Read the `Current state` section and task-relevant details in `Project.md`, plus the always-used rules in `Agentic-Fusion.md`. Preserve design intent, parameter relationships, and downstream feature health. Load only the reference that matches the operation:

- [Design and assembly checks](references/design-and-assembly.md): purchased-part fit, retention, installation paths, fasteners, and other assembly-specific checks.
- [MCP workflow](references/mcp.md): executing Fusion scripts, save and export timing, screenshots, and verification of tool results. Read when scripting, saving, or exporting.
- [Timeline](references/timeline.md): rollbacks, inserting or moving features, parameter flex checks, and timeline health.
- [Reusable helpers](references/helpers.md): scratchpad functions, parameter flex tests, geometry analysis, section properties, feature provenance, and screenshots. Read for a matching analysis or verification step.
- [Components](references/components.md): documents, components, occurrences, joints, assembly context, parameters, and interference APIs.
- [Sketches and features](references/sketches-and-features.md): sketch constraints and feature creation or editing.
- [Fillets](references/fillets.md): creating or editing fillets and chamfers when edge references matter.

Use the `fusion-print` skill for printing rules and `fusion-repair` for an observed failure. Design-specific decisions stay in `Project.md`; do not copy reference procedures into it.
