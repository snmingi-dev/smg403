# SMH Asset Bulk Manager MVP

Blender addon MVP for Asset Browser mass management:

- Auto catalog generation from selected assets or folder names (regex-based)
- One-click bulk assign to catalogs
- Find duplicate assets (`.001` style) and replace all references

## Features

1. Auto catalogs
- Input regex (default: `^([A-Za-z0-9]+)_`)
- Example: `Chair_Wood_01`, `Chair_Modern_02` -> `Auto/Chair`
- Writes/updates `blender_assets.cats.txt` in chosen asset library root

2. Bulk assign to catalog
- Works on selected local IDs (Object, Material, Mesh, etc.)
- Auto mode: derive catalog path from name pattern
- Manual mode: assign all selected assets to one catalog path

3. Duplicate cleanup
- Detect duplicates by base name (`Name`, `Name.001`, `Name.002`)
- Keep strongest candidate (exact base name first, then most users)
- Remap users and remove duplicates

## Installation

1. In Blender: `Edit > Preferences > Add-ons > Install...`
2. Select `smh_asset_bulk_manager.py`
3. Enable addon: `SMH Asset Bulk Manager MVP`

## Usage

1. Open panel:
- `3D View > Sidebar > SMH Assets`
- or `Asset Browser > Sidebar > SMH Assets`

2. Set `Asset Library Root`
- Folder that contains (or will contain) `blender_assets.cats.txt`

3. Catalog automation
- Choose source: `Selected Assets` or `Folder Scan`
- Set regex and catalog root
- Click `Auto Create Catalogs`

4. Bulk assign
- Optional: set `Manual Catalog`
- Click `Bulk Assign to Catalog`

5. Duplicate replacement
- Choose type
- Click `Find Duplicate Assets`
- Click `Replace All Duplicates`

## Notes

- This is an MVP focused on fast production workflow.
- Recommended Blender version: 4.0+
- Test on a copy of production files before large-scale replacement.
