# Smart Curve Helper

`Smart Curve Helper` is a Bezier handle editing add-on for Blender.

## Tested Blender Version

- Blender 4.5.5 LTS

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Add-ons`.
3. Click `Install...`.
4. Select this ZIP file.
5. Enable `Smart Curve Helper`.

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
