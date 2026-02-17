# Post-Unwrap Cleaner

UV Editor one-click cleanup pipeline for post-unwrap workflows.

## Supported Blender Versions

- 4.2 LTS
- 4.5 LTS
- 5.0

## Install

1. Build ZIP with `scripts/package_addons.ps1` or use `post_unwrap_cleaner.py` directly.
2. Blender > `Edit > Preferences > Add-ons > Install...`
3. Select ZIP (recommended) or `.py`.
4. Enable `Post-Unwrap Cleaner`.

## Usage Flow

1. Open UV Editor sidebar > `Post-Unwrap Cleaner`.
2. Set threshold/iterations/margin/target.
3. Configure optional step toggles (`Straighten`, `Relax`, `Pack`).
4. Click `One-Click Clean`.

## Safety & Recovery

- UV selection state is restored after execution.
- `Respect Pins` is ON by default.
- Straighten step can produce `0` edits while Relax/Pack still run.
- Undo is supported for mesh/UV data changes.

## Known Limitations

- Multi-object Edit Mode is intentionally blocked.
- Operator expects UV Editor region context.
- Advanced unwrap generation and baking are out of scope.

## Before/After Captures

- Place screenshots/GIF here:
- `demo/before-after.gif`
- `demo/one-click-flow.gif`

## Demo Files

- Intended demo path: `demo/post_unwrap_cleaner_demo.blend`
- Blender CLI is required to generate a valid `.blend` automatically.
- See `demo/README.md` for manual creation steps.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`

## Positioning

Focused on **selection-safe UV cleanup** with pin protection and staged execution.
