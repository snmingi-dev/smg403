# Auto Cataloger

Rules-based Asset Browser catalog assignment tool for Blender library maintenance.

## Supported Blender Versions

- 4.2 LTS
- 4.5 LTS
- 5.0

## Install

1. Build ZIP with `scripts/package_addons.ps1` or use `smh_asset_bulk_manager.py` directly.
2. Blender > `Edit > Preferences > Add-ons > Install...`
3. Select ZIP (recommended) or `.py`.
4. Enable `Auto Cataloger`.

## Usage Flow

1. Choose Asset Library source:
2. `Asset Library` (registered library in Blender Preferences), or
3. `Asset Library Root Folder` (manual path).
4. Set rule options and target type.
5. Click `Preview`.
6. Check preview list and skip counts.
7. Click `Apply`.

## Safety & Recovery

- `Apply` requires a fresh `Preview` signature match.
- Default behavior processes already-marked assets only.
- Optional `Auto-Mark Missing as Assets` is OFF by default.
- Catalog write backup: `blender_assets.cats.txt.bak`.
- UI includes `Restore from .bak` button.
- Blender Undo does not revert external `.cats` file edits.

## Known Limitations

- Linked datablocks are skipped.
- Relative folder mode depends on available source path metadata.
- Preview list is capped to 50 rows for UI performance.

## Before/After Captures

- Place screenshots/GIF here:
- `demo/before-after.gif`
- `demo/preview-apply.gif`

## Demo Files

- Intended demo path: `demo/auto_cataloger_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **library refactoring/maintenance**, not full asset management replacement.
