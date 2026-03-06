# SMG403 Blender Add-on Projects

Repository for individually sold Blender add-ons by **SMG Tools**.

Primary submission artifacts are the `*-extension.zip` bundles. Legacy `*.zip` bundles remain available as manual-install fallbacks.

## Product Index

| Product | Project Path | Primary Deliverable | Current Status | Support |
|---|---|---|---|---|
| Auto Cataloger | `projects/auto-cataloger/` | `dist/auto-cataloger-<version>-extension.zip` | Verified: 4.5.5 LTS; target support: 4.2 LTS - 5.0 | support@smgtools.dev |
| Post-Unwrap Cleaner | `projects/post-unwrap-cleaner/` | `dist/post-unwrap-cleaner-<version>-extension.zip` | Verified: 4.5.5 LTS; target support: 4.2 LTS - 5.0 | support@smgtools.dev |
| Smart Curve Helper | `projects/smart-curve-helper/` | `dist/smart-curve-helper-<version>-extension.zip` | Verified: 4.5.5 LTS; target support: 4.2 LTS - 5.0 | support@smgtools.dev |

Issue tracker: `https://github.com/snmingi-dev/smg403/issues`

## Packaging

Each project builds two ZIP artifacts:

- `dist/<product-name>-<version>-extension.zip`: primary Blender Extensions package
- `dist/<product-name>-<version>.zip`: legacy manual-install fallback

If a project includes `README.market.md`, the packaging script uses it for the legacy ZIP. If a project includes `README.extension.md`, the packaging script uses it for the extension ZIP. Both ZIP types include the repository `LICENSE`.

```powershell
pwsh .\scripts\package_addons.ps1 -ProjectPath .\projects\auto-cataloger
```

Installation in Blender:

- Extension ZIP: `Edit > Preferences > Get Extensions > Install from Disk`
- Legacy ZIP: `Edit > Preferences > Add-ons > Install...`

## QA Matrix

Submission verification notes:

- `docs/QA_MATRIX.md`

## License

GPL-3.0-or-later (`LICENSE`).
