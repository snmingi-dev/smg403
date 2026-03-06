# QA Matrix and Release Checklist

Current submission scope: **Auto Cataloger** only.

Last updated: `2026-03-06`

## Auto Cataloger Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| ZIP package build | 4.5.5 LTS | Pass | `scripts/package_addons.ps1` outputs ZIP with addon package, `LICENSE`, and buyer `README.md`. |
| ZIP install + enable | 4.5.5 LTS | Pass | Installed from generated ZIP without traceback. |
| Preferences + panel registration | 4.5.5 LTS | Pass | Add-on preferences and `3D View` sidebar panel load correctly. |
| Preview with non-assets only, auto-mark OFF | 4.5.5 LTS | Pass | Preview returns `0 assignable`; Apply cancels without creating `.cats`. |
| Preview with non-assets, auto-mark ON | 4.5.5 LTS | Pass | Preview reports pending auto-mark count; Apply auto-marks and assigns catalogs. |
| First catalog write creates `.bak` | 4.5.5 LTS | Pass | First generated `.cats` file also produces a backup snapshot. |
| Restore from `.bak` is reversible | 4.5.5 LTS | Pass | Restore swaps current and backup so a second restore returns to prior content. |
| Missing explicit library root | 4.5.5 LTS | Pass | Preview/Apply cancel with clear error; no `.blend` folder fallback. |

## Version Status

| Blender Version | Status |
|---|---|
| 4.2 LTS | Pending verification |
| 4.5.5 LTS | Verified |
| 5.0 | Pending verification |

## Other Products

| Product | Status |
|---|---|
| Post-Unwrap Cleaner | Out of scope for this resubmission round |
| Smart Curve Helper | Out of scope for this resubmission round |
