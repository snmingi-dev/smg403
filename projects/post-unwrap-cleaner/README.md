# Post-Unwrap Cleaner

UV cleanup addon MVP for Blender.

## MVP Core

After unwrap, run one action in UV Editor:

- Straighten
- Relax
- Pack

## UI

- UV Editor sidebar panel: `Post-Unwrap Cleaner`
- Button: `One-Click Clean`

## Options (4 only)

1. `Straighten Threshold` (0.1~1.0)
2. `Relax Iterations` (1~20)
3. `Packing Margin` (0.01~0.1)
4. `Target` (`Selected Islands` / `All Islands`)

## Non-goals

- UV unwrap generation itself
- Texture baking
- Advanced island split/merge

## Install

1. Blender > `Edit > Preferences > Add-ons > Install...`
2. Select `post_unwrap_cleaner.py`
3. Enable `Post-Unwrap Cleaner`

## License

GPL-3.0-or-later (see repository root `LICENSE`).
