---
name: fusion-repair
description: Diagnose a specific failed Fusion MCP call, save, document operation, sketch, feature, or DfAM fix. Use after an observed error or unexpected result.
---

# Fusion failure repair

Match the observed symptom and read only its reference:

- [MCP and save failures](references/mcp-and-save.md): timeout, empty output, save collision, startup recovery dialog, or export timeout.
- [Document and assembly state](references/document-state.md): unexpected component features, occurrence placement, deleted occurrence history, or screenshot appearance.
- [Geometry failures](references/geometry.md): lost sketch references, blends, fillets, chamfers, bridge steps, or print-specific fixes.

Do not use a repair in place of the preventive rules in `Agentic-Fusion.md` and, for printing work, the `fusion-print` skill. Test repairs in a rollback-capable script where possible. Recheck body count, volume, feature health, constraints, motion, and saved version as applicable. Do not load the other symptom families unless the evidence calls for them.
