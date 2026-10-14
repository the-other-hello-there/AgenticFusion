---
name: fusion-repair
description: Diagnose a specific failed Fusion MCP call, save, document operation, sketch, feature, or DfAM fix. Use after an observed error or unexpected result.
---

# Fusion failure repair

Read only the reference matching the observed symptom:

- [MCP and save failures](references/mcp-and-save.md): timeout, empty output, save collision, startup recovery dialog, or export timeout.
- [Document and assembly state](references/document-state.md): unexpected component features, occurrence placement, deleted occurrence history, or screenshot appearance.
- [Geometry failures](references/geometry.md): lost sketch references, blends, fillets, chamfers, bridge steps, or print-specific fixes.

Retain preventive rules in `Agentic-Fusion.md` and, for printing, `fusion-print`. Test in a rollback-capable script where possible; recheck applicable body count, volume, health, constraints, motion, and saved version. Load another symptom family only if evidence calls for it.
