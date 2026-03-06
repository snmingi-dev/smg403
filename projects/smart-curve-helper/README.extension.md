# Smart Curve Helper

`Smart Curve Helper` extension ZIP for Blender Extensions installation.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Get Extensions`.
3. Open the top-right menu and choose `Install from Disk`.
4. Select this ZIP file.
5. Enable `Smart Curve Helper` if Blender does not enable it automatically.

## Quick Start

1. Select a curve object.
2. Enter `EDIT_CURVE`.
3. Open the sidebar tab `Smart Curve Helper`.
4. Set Axis, Axis Space, Handle Type, Strength, Target, and Flatten Reference.
5. Run `Align Handles`, `Flatten`, or `Equalize Length`.

## Safety

- All operators require `EDIT_CURVE`.
- `Strength` is capped at `1.0` to avoid overshoot.
- Undo is supported for all three operators.

## Limitations

- NURBS splines are ignored.
- View-aligned modes require an active 3D View region.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`
