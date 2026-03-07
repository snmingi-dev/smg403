# Post-Unwrap Cleaner

UV Editor one-click cleanup pipeline for post-unwrap workflows.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Build Outputs

- `dist/post-unwrap-cleaner-<version>-extension.zip`: primary Blender Extensions bundle
- `dist/post-unwrap-cleaner-<version>.zip`: legacy manual-install fallback

## Install

1. Build ZIPs with `scripts/package_addons.ps1`.
2. For the extension ZIP: `Edit > Preferences > Get Extensions > Install from Disk`.
3. For the legacy ZIP: `Edit > Preferences > Add-ons > Install...`.
4. Enable `Post-Unwrap Cleaner`.

## Usage Flow

1. Open UV Editor sidebar > `Post-Unwrap Cleaner`.
2. Set threshold/iterations/margin/target.
3. Configure optional step toggles (`Straighten`, `Relax`, `Pack`).
4. Click `One-Click Clean`.

## Safety & Recovery

- UV selection state is restored after execution.
- `Respect Pins` is ON by default.
- `Respect Pins` excludes pinned UVs from prepared target selection.
- Pack-stage pin locking is requested when supported by the current Blender build.
- Straighten step can produce `0` edits while Relax/Pack still run.
- Undo is supported for mesh/UV data changes.
- If an operation fails after partial UV changes, the operator finishes with an error message and you should use Undo to revert.

## Known Limitations

- Multi-object Edit Mode is intentionally blocked.
- Operator expects UV Editor region context.
- `Selected UV Selection` uses the current UV selection and does not expand by island flood-fill.
- Advanced unwrap generation and baking are out of scope.

## Demo Files

- Intended demo path: `demo/post_unwrap_cleaner_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **selection-safe UV cleanup** with pin protection and staged execution.
