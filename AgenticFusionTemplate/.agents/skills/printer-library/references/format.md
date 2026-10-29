# Printer library format and migration

`Printers.json` is a versioned, portable JSON document: `{"schema_version": 1, "printers": [...]}`. Copy the entire file to a new project, or paste selected records into its `printers` array and validate. Preserve an existing destination library by merging with the helper instead of replacing its file. No real printer ships in the template.

## Record fields

Use [the example record](../assets/printer.example.json) as the shape, not as hardware evidence. The helper rejects unknown top-level/record fields to catch misspellings; keep extra descriptions in `notes`.

| Field | Meaning |
| --- | --- |
| `id`, `name` | Stable lowercase ID using letters, digits and hyphens; readable printer/variant name. Use distinct IDs when configurations are not interchangeable. |
| `manufacturer`, `model` | User-stated or verified identity, or `null`. Keep serial numbers and network identity out. |
| `hardware.build_volume_mm` | Positive `[X, Y, Z]` usable bounding dimensions, or `null`. This does not imply a rectangular printable area. |
| `hardware.bed_origin`, `bed_shape_mm` | Origin description or `null`; actual XY polygon `[[x,y], ...]` in mm, or `null`. Preserve offsets/exclusions in native presets too. |
| `hardware.nozzle_diameters_mm` | Known compatible/installed nozzle diameters; empty when unknown. The job's active nozzle stays in `Project.md`. |
| `hardware.firmware` | Firmware/dialect description or `null`; preserve exact native `gcode_flavor` in the machine preset. |
| `hardware.max_nozzle_temp_c`, `max_bed_temp_c` | Verified hardware ceilings or `null`. These are not recommended print temperatures. |
| `evidence` | `status`: `unverified`, `user-stated`, or `verified`; `source`: descriptive reference; `checked_on`: ISO date or `null`. Name mixed/limited evidence in the source and notes. |
| `slicer.family`, `version` | `OrcaSlicer` (including OrcaMCP) and source application version, or unknown version `null`. |
| `slicer.presets` | Full native JSON objects of type `machine`, `machine_model`, `filament`, or `process`; each has an exact `name`. Include custom inheritance parents. Empty is valid for a hardware-only definition. |
| `slicer.required_system_presets` | Objects with native `type` and exact `name` for omitted system parents/variants that must exist at the destination. The helper checks inheritance closure/cycles; an external dependency is declared, not verified installed. |
| `notes` | Strings describing uncertainties, modifications, calibration evidence links, and missing bed assets. |

Orca uses JSON for machine, filament and process presets; `inherits` names a parent while `compatible_printers` expresses compatibility. Preserve native strings, arrays and conditions instead of converting them to the hardware summary's numeric types. [Upstream profile format](https://github.com/OrcaSlicer/OrcaSlicer/wiki/how_to_create_profiles)

## Helper commands

Python 3.11+; no third-party dependencies. Run from a project, or pass global `--library path/to/Printers.json` before the command. The default library is beside the helper's containing project, independent of the working directory.

```powershell
py -3 .agents/skills/printer-library/scripts/printer_library.py list
py -3 .agents/skills/printer-library/scripts/printer_library.py validate
# Author a single record from the example and actual evidence, then add it.
py -3 .agents/skills/printer-library/scripts/printer_library.py add --record printer.json
# Updating a different record with the same ID needs an explicit replacement.
py -3 .agents/skills/printer-library/scripts/printer_library.py add --record printer.json --replace
# Export one or several records as a copyable JSON library.
py -3 .agents/skills/printer-library/scripts/printer_library.py export --id my-printer --output shared-printers.json
py -3 .agents/skills/printer-library/scripts/printer_library.py import --source shared-printers.json
# Also write embedded presets as native individual JSON files in a new directory.
py -3 .agents/skills/printer-library/scripts/printer_library.py export-presets --id my-printer --output Printer-Transfer
```

The export directory contains selected `Printers.json` plus numbered native JSON files under `printer-<id>/`; names inside the presets and inheritance links are retained. Export refuses an existing output. Import merges catalog records and rejects conflicting IDs unless `--replace` is supplied; all validation happens before an atomic catalog replacement. The helper does not write into application profile directories.

For a complete slicer-native migration, Orca's **Export Preset Bundle > Printer config bundle** creates `.orca_printer` with the printer's filament/process presets; its **Import Configs** command imports preset bundles. This is preferable when preserving vendor bundle resources or GUI-managed profile relationships beyond the catalog. [Upstream import/export](https://github.com/OrcaSlicer/OrcaSlicer/wiki/import_export)

The catalog is not an Orca-native bundle. Use its definitions as agent context; use reviewed native JSON exports or the slicer's own bundle import to install presets. Bed textures/models or other binary assets are not embedded. Copy required assets separately, repair their references, install declared system parents from the matching slicer/vendor version, and verify compatibility in the destination GUI. Do not claim migration is complete merely because catalog validation passed.
