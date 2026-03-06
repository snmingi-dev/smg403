# Post-Unwrap Cleaner

`Post-Unwrap Cleaner` extension ZIP for Blender Extensions installation.

## Version Status

- Verified: Blender 4.5.5 LTS
- Target support: Blender 4.2 LTS - 5.0

## Installation

1. Open Blender.
2. Go to `Edit > Preferences > Get Extensions`.
3. Open the top-right menu and choose `Install from Disk`.
4. Select this ZIP file.
5. Enable `Post-Unwrap Cleaner` if Blender does not enable it automatically.

## Quick Start

1. Open the UV Editor.
2. Enter Edit Mode on a mesh with UVs.
3. Open the sidebar tab `Post-Unwrap Cleaner`.
4. Set threshold, relax iterations, packing margin, and target scope.
5. Click `One-Click Clean`.

## Safety

- UV selection state is restored after execution.
- `Respect Pins` is ON by default.
- `Respect Pins` excludes pinned UVs from the prepared target selection.
- Pack-stage pin locking is requested when supported by the current Blender build.
- Undo is supported for mesh and UV changes.

## Limitations

- Multi-object Edit Mode is not supported.
- The tool is intended for the UV Editor workflow only.
- `Selected UV Selection` uses the current UV selection and does not expand by island flood-fill.

## Support

- Email: `support@smgtools.dev`
- Issues: `https://github.com/snmingi-dev/smg403/issues`
