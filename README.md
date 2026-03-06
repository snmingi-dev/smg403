# SMG403 Blender Add-on Projects

Repository for individually sold Blender add-ons by **SMG Tools**.

Current market resubmission scope: **Auto Cataloger** only.

## Product Index

| Product | Project Path | Install File | Current Status | Support |
|---|---|---|---|---|
| Auto Cataloger | `projects/auto-cataloger/` | `auto_cataloger/__init__.py` | Verified in Blender 4.5.5 LTS; 4.2/5.0 pending | support@smgtools.dev |
| Post-Unwrap Cleaner | `projects/post-unwrap-cleaner/` | `post_unwrap_cleaner/__init__.py` | Basic runtime QA verified in Blender 4.5.5 LTS; 4.2/5.0 pending | support@smgtools.dev |
| Smart Curve Helper | `projects/smart-curve-helper/` | `smart_curve_helper/__init__.py` | Basic runtime QA verified in Blender 4.5.5 LTS; 4.2/5.0 pending | support@smgtools.dev |

Issue tracker: `https://github.com/snmingi-dev/smg403/issues`

## Packaging

Official release artifact per product is a ZIP containing one addon package folder with `__init__.py`.

If a project includes `README.market.md`, the packaging script bundles it into the ZIP as `README.md` together with the repository `LICENSE`.
The packaging script also generates an extension-ready ZIP when `blender_manifest.toml` is present in the addon package.

```powershell
pwsh .\scripts\package_addons.ps1 -ProjectPath .\projects\auto-cataloger
```

Output:

- `dist/<product-name>-<version>.zip`
- `dist/<product-name>-<version>-extension.zip`

Installation in Blender:

1. `Edit > Preferences > Add-ons > Install...`
2. Select the generated ZIP file.
3. Enable the addon.

## QA Matrix

Submission verification notes:

- `docs/QA_MATRIX.md`

## License

GPL-3.0-or-later (`LICENSE`).
