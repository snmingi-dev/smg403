# Auto Cataloger

`Auto Cataloger` extension ZIP for Blender Extensions installation.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Get Extensions`.
3. Open the top-right menu and choose `Install from Disk`.
4. Select this ZIP file.
5. Enable `Auto Cataloger` if Blender does not enable it automatically.

## Quick Start

1. Register an Asset Library in Blender Preferences, or set `Asset Library Root Folder` manually in the add-on panel.
2. Open `3D View > Sidebar > Auto Cataloger`.
3. Choose a rule mode and target type.
4. Click `Preview`.
5. Review the assignable count, skip counts, and planned catalog paths.
6. Click `Apply`.

## Safety and Recovery

- This extension manages `blender_assets.cats.txt` and `.bak` files inside the chosen Asset Library root.
- Default behavior processes only datablocks already marked as assets.
- `Auto-Mark Missing as Assets` is OFF by default.
- Blender Undo does not revert external `.cats` file changes.
- `Restore from .bak` swaps the current `.cats` file with the backup so the restore action itself is reversible.

## Limitations

- You must choose a registered Asset Library or set `Asset Library Root Folder` explicitly.
- Linked datablocks are skipped.
- Relative folder mode skips datablocks that resolve outside the chosen library root or across different Windows drives.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`
