# QA Matrix and Release Checklist

Last updated: `2026-03-07`

## Auto Cataloger Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| Legacy ZIP build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and legacy buyer `README.md`. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension ZIP contains `__init__.py`, `blender_manifest.toml`, `LICENSE`, and extension buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension validate | 4.5.5 LTS | Pass | `blender --command extension validate` passed for the extension ZIP. |
| Legacy ZIP install + enable | 4.5.5 LTS | Pass | Installed from generated ZIP without traceback. |
| Preferences + panel registration | 4.5.5 LTS | Pass | Add-on preferences and `3D View` sidebar panel load correctly. |
| Catalog root prefix validation | 4.5.5 LTS | Pass | `:` and line breaks are rejected before Preview/Apply; `.cats` remains unchanged. |
| Preview with non-assets only, auto-mark OFF | 4.5.5 LTS | Pass | Preview returns `0 assignable`; Apply cancels without creating `.cats`. |
| Preview with non-assets, auto-mark ON | 4.5.5 LTS | Pass | Preview reports pending auto-mark count; Apply auto-marks and assigns catalogs. |
| Cross-drive relative folder handling | 4.5.5 LTS | Pass | Different Windows drive letters are skipped as external instead of raising `ValueError`. |
| Existing root required | 4.5.5 LTS | Pass | Preview, Apply, and Restore reject missing root folders instead of creating them. |
| First catalog write creates `.bak` | 4.5.5 LTS | Pass | First generated `.cats` file also produces a backup snapshot. |
| Existing `.bak` refresh is atomic | 4.5.5 LTS | Pass | Backup refresh publishes via temp file + replace before the new `.cats` write. |
| First-write backup rollback | 4.5.5 LTS | Pass | First-write path prepares backup before publish so failed backup creation does not leave a half-published result. |
| Restore from `.bak` is reversible | 4.5.5 LTS | Pass | Restore swaps current and backup so a second restore returns to prior content. |
| Missing explicit library root | 4.5.5 LTS | Pass | Preview/Apply cancel with clear error; no `.blend` folder fallback. |
| Partial apply returns finished | 4.5.5 LTS | Pass | Assignment failures after catalog creation or asset updates now finish with an error summary instead of cancelling. |
| Partial apply recovery hint | 4.5.5 LTS | Pass | Error message distinguishes Undo-only, Restore-only, and combined recovery paths. |

## Post-Unwrap Cleaner Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| Legacy ZIP build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and legacy buyer `README.md`. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension ZIP contains `__init__.py`, `blender_manifest.toml`, `LICENSE`, and extension buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension validate | 4.5.5 LTS | Pass | `blender --command extension validate` passed for the extension ZIP. |
| Legacy ZIP install + enable | 4.5.5 LTS | Pass | Installed and enabled in isolated Blender user scripts path. |
| No-UV preflight | 4.5.5 LTS | Pass | Meshes without a UV map fail before any UV layer or edit data is created. |
| UV-only poll gating | 4.5.5 LTS | Pass | Panel/operator no longer poll true in plain `IMAGE_EDITOR` mode. |
| Straighten=0 path still runs | 4.5.5 LTS | Pass | Forced `straightened=0` branch still completed Relax + Pack. |
| Selection restoration | 4.5.5 LTS | Pass | UV selection state matched snapshot after operator execution. |
| Pinned UV unchanged in test scene | 4.5.5 LTS | Pass | Straighten and pack path left pinned UV coordinates unchanged in runtime test. |
| Target wording alignment | 4.5.5 LTS | Pass | UI and buyer docs now use `Selected UV Selection` instead of island wording. |
| Partial failure returns finished | 4.5.5 LTS | Pass | Runtime errors after UV edits now finish with an error message so Undo semantics stay consistent. |

## Smart Curve Helper Verification

| Check | Blender Version | Result | Notes |
|---|---|---|---|
| Legacy ZIP build | 4.5.5 LTS | Pass | Legacy ZIP contains addon package, `LICENSE`, and legacy buyer `README.md`. |
| Extension ZIP build | 4.5.5 LTS | Pass | Extension ZIP contains `__init__.py`, `blender_manifest.toml`, `LICENSE`, and extension buyer `README.md`. |
| ZIP entry portability | 4.5.5 LTS | Pass | ZIP entry names validated with forward slashes only; no `\` entries remain. |
| Extension validate | 4.5.5 LTS | Pass | `blender --command extension validate` passed for the extension ZIP. |
| Legacy ZIP install + enable | 4.5.5 LTS | Pass | Installed and enabled in isolated Blender user scripts path. |
| Object mode gate | 4.5.5 LTS | Pass | `Align Handles` poll is false outside `EDIT_CURVE`. |
| Selected-only scope | 4.5.5 LTS | Pass | Unselected Bezier point stayed unchanged during `Align Handles`. |
| Flatten operator runtime | 4.5.5 LTS | Pass | Flattened points/handles onto a consistent plane in test curve. |
| Equalize operator runtime | 4.5.5 LTS | Pass | Handle lengths converged within tolerance after equalize. |
| Strength clamp | 4.5.5 LTS | Pass | UI limits `Strength` to `1.0` to avoid overshoot. |

## Version Status

| Product | Verified | Target support |
|---|---|---|
| Auto Cataloger | 4.5.5 LTS | 4.2 LTS - 5.0 |
| Post-Unwrap Cleaner | 4.5.5 LTS | 4.2 LTS - 5.0 |
| Smart Curve Helper | 4.5.5 LTS | 4.2 LTS - 5.0 |
