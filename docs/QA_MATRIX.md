# QA Matrix and Release Checklist

Last updated: `2026-03-07`

## Auto Cataloger Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| ZIP package build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension artifact includes `blender_manifest.toml`, `LICENSE`, and buyer `README.md`. |
| ZIP install + enable | 4.5.5 LTS | Pass | Installed from generated ZIP without traceback. |
| Preferences + panel registration | 4.5.5 LTS | Pass | Add-on preferences and `3D View` sidebar panel load correctly. |
| Preview with non-assets only, auto-mark OFF | 4.5.5 LTS | Pass | Preview returns `0 assignable`; Apply cancels without creating `.cats`. |
| Preview with non-assets, auto-mark ON | 4.5.5 LTS | Pass | Preview reports pending auto-mark count; Apply auto-marks and assigns catalogs. |
| First catalog write creates `.bak` | 4.5.5 LTS | Pass | First generated `.cats` file also produces a backup snapshot. |
| Restore from `.bak` is reversible | 4.5.5 LTS | Pass | Restore swaps current and backup so a second restore returns to prior content. |
| Missing explicit library root | 4.5.5 LTS | Pass | Preview/Apply cancel with clear error; no `.blend` folder fallback. |

## Post-Unwrap Cleaner Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| ZIP package build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension artifact includes `blender_manifest.toml`, `LICENSE`, and buyer `README.md`. |
| ZIP install + enable | 4.5.5 LTS | Pass | Installed and enabled in isolated Blender user scripts path. |
| UV-only poll gating | 4.5.5 LTS | Pass | Panel/operator no longer poll true in plain `IMAGE_EDITOR` mode. |
| Straighten=0 path still runs | 4.5.5 LTS | Pass | Forced `straightened=0` branch still completed Relax + Pack. |
| Selection restoration | 4.5.5 LTS | Pass | UV selection state matched snapshot after operator execution. |
| Pinned UV unchanged in test scene | 4.5.5 LTS | Pass | Straighten and pack path left pinned UV coordinates unchanged in runtime test. |

## Smart Curve Helper Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| ZIP package build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension artifact includes `blender_manifest.toml`, `LICENSE`, and buyer `README.md`. |
| ZIP install + enable | 4.5.5 LTS | Pass | Installed and enabled in isolated Blender user scripts path. |
| Object mode gate | 4.5.5 LTS | Pass | `Align Handles` poll is false outside `EDIT_CURVE`. |
| Selected-only scope | 4.5.5 LTS | Pass | Unselected Bezier point stayed unchanged during `Align Handles`. |
| Flatten operator runtime | 4.5.5 LTS | Pass | Flattened points/handles onto a consistent plane in test curve. |
| Equalize operator runtime | 4.5.5 LTS | Pass | Handle lengths converged within tolerance after equalize. |
| Strength clamp | 4.5.5 LTS | Pass | UI now limits `Strength` to `1.0` to avoid overshoot. |

## Version Status

| Product | 4.2 LTS | 4.5.5 LTS | 5.0 |
|---|---|---|---|
| Auto Cataloger | Pending verification | Verified | Pending verification |
| Post-Unwrap Cleaner | Pending verification | Verified | Pending verification |
| Smart Curve Helper | Pending verification | Verified | Pending verification |
