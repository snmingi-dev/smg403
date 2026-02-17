# Smart Curve Helper

Bezier handle quality-of-life toolset for curve editing.

## Supported Blender Versions

- 4.2 LTS
- 4.5 LTS
- 5.0

## Install

1. Build ZIP with `scripts/package_addons.ps1` or use `smart_curve_helper.py` directly.
2. Blender > `Edit > Preferences > Add-ons > Install...`
3. Select ZIP (recommended) or `.py`.
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
- Errors are standardized for invalid mode, missing Bezier targets, and missing view region.
- Undo is supported and should be validated after each operator.
- Handle type is applied after each transformation step.

## Known Limitations

- NURBS splines are ignored.
- `Axis=View` and `Axis Space=View` require an active 3D View region.
- Active point reference uses current selected control point fallback behavior.

## Before/After Captures

- Place screenshots/GIF here:
- `demo/before-after.gif`
- `demo/curve-ops-flow.gif`

## Demo Files

- Intended demo path: `demo/smart_curve_helper_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **safe curve editing** with edit-mode gating, axis-space control, and flatten reference options.
