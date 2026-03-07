# Auto Cataloger

Rules-based Asset Browser catalog assignment tool for Blender library maintenance.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Build Outputs

- `dist/auto-cataloger-<version>-extension.zip`: primary Blender Extensions bundle
- `dist/auto-cataloger-<version>.zip`: legacy manual-install fallback

## Install

1. Build ZIPs with `scripts/package_addons.ps1`.
2. For the extension ZIP: `Edit > Preferences > Get Extensions > Install from Disk`.
3. For the legacy ZIP: `Edit > Preferences > Add-ons > Install...`.
4. Enable `Auto Cataloger`.

## Usage Flow

1. Choose Asset Library source:
2. `Asset Library` (registered library in Blender Preferences), or
3. `Asset Library Root Folder` (manual path).
4. Set rule options and target type.
5. Click `Preview`.
6. Check assignable count, skip counts, and preview list.
7. Click `Apply`.

## Safety & Recovery

- `Apply` requires a fresh `Preview` signature match.
- Default behavior processes only datablocks that are already marked as assets.
- Optional `Auto-Mark Missing as Assets` is OFF by default.
- `Preview` and `Apply` use the same assignable-set logic.
- You must choose a registered Asset Library or set `Asset Library Root Folder` explicitly.
- The chosen Asset Library root must already exist. Preview, Apply, and Restore do not create missing folders.
- Catalog writes use an atomic replace and create `blender_assets.cats.txt.bak`.
- On the first write, `.bak` is a snapshot of the first generated catalog file.
- UI includes `Restore from .bak`, which swaps current and backup files so restore is reversible.
- Blender Undo does not revert external `.cats` file edits.
- If some datablocks fail during `Apply`, the operator can finish with partial results. Review the status message and use Undo to revert internal changes if needed.

## Known Limitations

- Linked datablocks are skipped.
- Relative folder mode depends on available source path metadata.
- Relative folder mode skips datablocks that resolve outside the chosen library root or across different Windows drives.
- Preview list is capped to 50 rows for UI performance.

## Demo Files

- Intended demo path: `demo/auto_cataloger_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **library refactoring/maintenance**, not full asset management replacement.
