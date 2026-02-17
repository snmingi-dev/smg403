# SMG403 Blender Add-on Projects

Repository for individually sold Blender add-ons by **SMG Tools**.

## Product Index

| Product | Project Path | Install File | Supported Blender | Support |
|---|---|---|---|---|
| Auto Cataloger | `projects/auto-cataloger/` | `smh_asset_bulk_manager.py` | 4.2 LTS, 4.5 LTS, 5.0 | support@smgtools.dev |
| Post-Unwrap Cleaner | `projects/post-unwrap-cleaner/` | `post_unwrap_cleaner.py` | 4.2 LTS, 4.5 LTS, 5.0 | support@smgtools.dev |
| Smart Curve Helper | `projects/smart-curve-helper/` | `smart_curve_helper.py` | 4.2 LTS, 4.5 LTS, 5.0 | support@smgtools.dev |

Issue tracker: `https://github.com/snmingi-dev/smg403/issues`

## Packaging

Official release artifact per product is a ZIP with a single addon `.py` file.

```powershell
pwsh .\scripts\package_addons.ps1 -ProjectPath .\projects\auto-cataloger
```

Output:

- `dist/<product-name>-<version>.zip`

Installation in Blender:

1. `Edit > Preferences > Add-ons > Install...`
2. Select the generated ZIP file.
3. Enable the addon.

## QA Matrix

Manual test matrix and release checklist:

- `docs/QA_MATRIX.md`

## License

GPL-3.0-or-later (`LICENSE`).
