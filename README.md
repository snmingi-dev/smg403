# Auto Cataloger (Rules-based Asset Catalog Assignment)

Blender add-on MVP for fast Asset Browser catalog operations.

## Scope (MVP)

- Current `.blend` assets are auto-classified by rules.
- Catalogs are created in `blender_assets.cats.txt`.
- Assets are bulk assigned to generated catalogs.
- `Apply` requires a fresh `Preview` with unchanged options/targets.

## UI

- Sidebar panel: `3D View > Sidebar > Auto Cataloger`
- Buttons: `Preview`, `Apply`

## Options (exactly 5)

1. `Asset Library Root Folder`
2. `Classification Mode` (`Name Prefix` / `Relative Folder Path`)
3. `Prefix Delimiter` (`_` / `-` / `space`)
4. `Catalog Root Prefix` (example: `MyLib/`)
5. `Target Type` (`All` / `Materials` / `Node Groups` / `Objects&Collections`)

## Required Behaviors

- Blender compatibility: 4.3 LTS and 5.0+
- Undo support on apply
- CDF backup: `blender_assets.cats.txt.bak` before write (only when catalog file changes)
- Settings saved via Add-on Preferences
- GPL licensed

## Relative Folder Mode Notes

- First tries per-asset source path from `library_weak_reference` / linked library path.
- If unavailable, falls back to current `.blend` path and appends data type segment
  (`Materials`, `Node_Groups`, `Objects`, `Collections`).

## Non-goals

- Duplicate finder/replacer
- Keyword tagging
- Thumbnail generation
- Multi-catalog assignment per asset

## Install

1. Blender > `Edit > Preferences > Add-ons > Install...`
2. Select `smh_asset_bulk_manager.py`
3. Enable add-on

## Other Project

- `post-unwrap-cleaner/`:
  `Post-Unwrap Cleaner` (UV Editor one-click cleanup addon MVP)
