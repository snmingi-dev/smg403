# Auto Cataloger

`auto_cataloger` is a rules-based Asset Browser catalog assignment add-on for Blender.

## Tested Blender Version

- Blender 4.5.5 LTS

Verification for Blender 4.2 LTS and 5.0 is still pending for this release bundle.

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Add-ons`.
3. Click `Install...`.
4. Select this ZIP file.
5. Enable `auto_cataloger`.

## Quick Start

1. In Blender Preferences, register an Asset Library, or set `Asset Library Root Folder` manually in the add-on panel.
2. Open `3D View > Sidebar > Auto Cataloger`.
3. Choose a rule mode and target type.
4. Click `Preview`.
5. Review the assignable count, skip counts, and planned catalog paths.
6. Click `Apply`.

## Safety and Recovery

- Default behavior processes only datablocks that are already marked as assets.
- `Auto-Mark Missing as Assets` is OFF by default.
- External catalog changes are written to `blender_assets.cats.txt`.
- Blender Undo does not revert external `.cats` file changes.
- A `.bak` file is created alongside the catalog file.
- `Restore from .bak` swaps the current `.cats` file with the backup so the restore action itself is reversible.
- On the first catalog write, the backup is a snapshot of the first generated file.

## Limitations

- You must choose a registered Asset Library or set `Asset Library Root Folder` explicitly.
- Linked datablocks are skipped.
- Relative folder mode depends on source path metadata for the datablock.
- Preview shows up to 50 rows in the UI list.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`
