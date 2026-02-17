# Smart Curve Helper

Bezier curve editing QoL MVP for Blender.

## MVP Core

Auto-fix selected Bezier points/handles with three one-click tools:

- Align Handles
- Flatten
- Equalize Length

## UI

- Panel: `3D Viewport > Sidebar > Smart Curve Helper`
- Buttons:
  - `Align Handles`
  - `Flatten`
  - `Equalize Length`

## Options (4 only)

1. `Axis` (`X` / `Y` / `Z` / `View`)
2. `Handle Type` (`Auto` / `Vector` / `Aligned` / `Free`)
3. `Strength` (`0.0 ~ 2.0`)
4. `Target` (`Selected Points Only` / `All Curves in Object`)

## Non-goals

- New curve generation
- Animation keyframing
- Bevel or taper profile tooling
- NURBS support

## Install

1. Blender > `Edit > Preferences > Add-ons > Install...`
2. Select `smart_curve_helper.py`
3. Enable `Smart Curve Helper`
