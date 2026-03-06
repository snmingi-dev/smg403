# Smart Curve Helper

Bezier handle quality-of-life toolset for curve editing.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Build Outputs

- `dist/smart-curve-helper-<version>-extension.zip`: primary Blender Extensions bundle
- `dist/smart-curve-helper-<version>.zip`: legacy manual-install fallback

## Install

1. Build ZIPs with `scripts/package_addons.ps1`.
2. For the extension ZIP: `Edit > Preferences > Get Extensions > Install from Disk`.
3. For the legacy ZIP: `Edit > Preferences > Add-ons > Install...`.
4. Enable `Smart Curve Helper`.

## Usage Flow

1. Enter `EDIT_CURVE` mode.
2. Set Axis, Axis Space, Handle Type, Strength, Target, and Flatten Reference.
3. Run:
4. `Align Handles`
5. `Flatten`
6. `Equalize Length`

## Safety & Recovery

- All operators require `EDIT_CURVE`.
- `Strength` is capped at `1.0` to avoid overshoot during align/flatten/equalize.
- Errors are standardized for invalid mode, missing Bezier targets, and missing view region.
- Undo is supported and should be validated after each operator.
- Handle type is applied after each transformation step.

## Known Limitations

- NURBS splines are ignored.
- `Axis=View` and `Axis Space=View` require an active 3D View region.
- Active point reference uses current selected control point fallback behavior.

## Demo Files

- Intended demo path: `demo/smart_curve_helper_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **safe curve editing** with edit-mode gating, axis-space control, and flatten reference options.
