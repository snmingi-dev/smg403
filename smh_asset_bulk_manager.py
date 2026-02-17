# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Auto Cataloger (Rules-based Asset Catalog Assignment)",
    "author": "snmingi-dev + Codex",
    "version": (0, 2, 0),
    "blender": (4, 3, 0),
    "location": "3D View > Sidebar > Auto Cataloger",
    "description": "Rules-based auto catalog creation and bulk assignment for Asset Browser.",
    "category": "Asset Management",
}

import os
import re
import shutil
import uuid
from collections import defaultdict

import bpy
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup, UIList


ADDON_ID = __name__
CATALOG_FILE_NAME = "blender_assets.cats.txt"
DEFAULT_HEADER_LINES = [
    "# This is an Asset Catalog Definition file for Blender.",
    "# Auto Cataloger manages this file.",
    "VERSION 1",
]


def _normalize_path_fragment(value):
    cleaned = value.replace("\\", "/").strip()
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    return cleaned.strip("/")


def _safe_segment(value):
    token = re.sub(r"\s+", "_", value.strip())
    token = re.sub(r"[^A-Za-z0-9._-]", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "Uncategorized"


def _get_addon_prefs(context):
    addon = context.preferences.addons.get(ADDON_ID)
    if addon is None:
        return None
    return addon.preferences


def _resolve_asset_library_root(context, prefs):
    root = bpy.path.abspath(prefs.asset_library_root_folder).strip()
    if root:
        return os.path.abspath(root)

    if bpy.data.filepath:
        return os.path.dirname(bpy.data.filepath)

    return None


def _delimiter_token(delimiter_enum):
    mapping = {
        "UNDERSCORE": "_",
        "DASH": "-",
        "SPACE": " ",
    }
    return mapping[delimiter_enum]


def _prefix_from_name(name, delimiter_enum):
    delim = _delimiter_token(delimiter_enum)
    if delim == " ":
        head = name.split()[0] if name.split() else name
    else:
        head = name.split(delim, 1)[0]
    return _safe_segment(head)


def _read_catalog_file(catalog_file_path):
    if not os.path.exists(catalog_file_path):
        return DEFAULT_HEADER_LINES[:], {}

    headers = []
    path_to_entry = {}
    with open(catalog_file_path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("VERSION "):
                headers.append(stripped)
                continue
            parts = stripped.split(":", 2)
            if len(parts) != 3:
                continue
            catalog_uuid, catalog_path, catalog_name = parts
            path_to_entry[catalog_path] = {
                "uuid": catalog_uuid,
                "name": catalog_name,
            }
    if not headers:
        headers = DEFAULT_HEADER_LINES[:]
    if not any(line.startswith("VERSION ") for line in headers):
        headers.append("VERSION 1")
    return headers, path_to_entry


def _write_catalog_file_with_backup(catalog_file_path, headers, path_to_entry):
    if os.path.exists(catalog_file_path):
        shutil.copy2(catalog_file_path, catalog_file_path + ".bak")

    lines = [line.rstrip() for line in headers]
    for catalog_path in sorted(path_to_entry.keys()):
        entry = path_to_entry[catalog_path]
        lines.append(f"{entry['uuid']}:{catalog_path}:{entry['name']}")

    with open(catalog_file_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def _ensure_catalogs(asset_library_root, catalog_paths):
    os.makedirs(asset_library_root, exist_ok=True)
    catalog_file_path = os.path.join(asset_library_root, CATALOG_FILE_NAME)
    headers, path_to_entry = _read_catalog_file(catalog_file_path)

    created = 0
    for catalog_path in sorted(catalog_paths):
        norm = _normalize_path_fragment(catalog_path)
        if not norm:
            continue
        if norm in path_to_entry:
            continue
        path_to_entry[norm] = {
            "uuid": str(uuid.uuid4()),
            "name": _safe_segment(norm.split("/")[-1]),
        }
        created += 1

    _write_catalog_file_with_backup(catalog_file_path, headers, path_to_entry)
    return {path: data["uuid"] for path, data in path_to_entry.items()}, created


def _iter_target_datablocks(prefs):
    buckets = []
    if prefs.target_type == "ALL":
        buckets = [bpy.data.materials, bpy.data.node_groups, bpy.data.objects, bpy.data.collections]
    elif prefs.target_type == "MATERIALS":
        buckets = [bpy.data.materials]
    elif prefs.target_type == "NODE_GROUPS":
        buckets = [bpy.data.node_groups]
    elif prefs.target_type == "OBJECTS_COLLECTIONS":
        buckets = [bpy.data.objects, bpy.data.collections]

    for bucket in buckets:
        for datablock in bucket:
            yield datablock


def _source_dir_for_datablock(datablock):
    linked = getattr(datablock, "library", None)
    if linked is not None and linked.filepath:
        library_path = bpy.path.abspath(linked.filepath)
        return os.path.dirname(os.path.abspath(library_path))
    if bpy.data.filepath:
        return os.path.dirname(os.path.abspath(bpy.data.filepath))
    return None


def _compose_catalog_path(root_prefix, tail):
    prefix = _normalize_path_fragment(root_prefix)
    tail_norm = _normalize_path_fragment(tail)
    if prefix and tail_norm:
        return f"{prefix}/{tail_norm}"
    if prefix:
        return prefix
    if tail_norm:
        return tail_norm
    return "Uncategorized"


def _build_assignment_plan(context, prefs):
    library_root = _resolve_asset_library_root(context, prefs)
    if not library_root:
        raise ValueError("Asset Library Root Folder is empty and current .blend is not saved.")

    plan = []
    skipped_linked = 0
    skipped_external = 0

    for datablock in _iter_target_datablocks(prefs):
        if getattr(datablock, "library", None) is not None:
            skipped_linked += 1
            continue

        if prefs.classification_mode == "NAME_PREFIX":
            tail = _prefix_from_name(datablock.name, prefs.prefix_delimiter)
        else:
            src_dir = _source_dir_for_datablock(datablock)
            if not src_dir:
                skipped_external += 1
                continue
            rel = os.path.relpath(src_dir, library_root)
            if rel.startswith(".."):
                skipped_external += 1
                continue
            if rel == ".":
                tail = ""
            else:
                segments = [_safe_segment(part) for part in rel.replace("\\", "/").split("/") if part and part != "."]
                tail = "/".join(segments)

        catalog_path = _compose_catalog_path(prefs.catalog_root_prefix, tail)
        plan.append((datablock, catalog_path))

    return library_root, plan, skipped_linked, skipped_external


class AUTO_CATALOGER_preferences(AddonPreferences):
    bl_idname = ADDON_ID

    asset_library_root_folder: StringProperty(
        name="Asset Library Root Folder",
        subtype="DIR_PATH",
        default="",
    )
    classification_mode: EnumProperty(
        name="Classification Mode",
        items=[
            ("NAME_PREFIX", "Name Prefix", "Use asset name prefix"),
            ("RELATIVE_FOLDER", "Relative Folder Path", "Use folder path relative to root"),
        ],
        default="NAME_PREFIX",
    )
    prefix_delimiter: EnumProperty(
        name="Prefix Delimiter",
        items=[
            ("UNDERSCORE", "_", "Split at underscore"),
            ("DASH", "-", "Split at dash"),
            ("SPACE", "space", "Split at space"),
        ],
        default="UNDERSCORE",
    )
    catalog_root_prefix: StringProperty(
        name="Catalog Root Prefix",
        default="MyLib/",
    )
    target_type: EnumProperty(
        name="Target Type",
        items=[
            ("ALL", "All", "Materials + Node Groups + Objects + Collections"),
            ("MATERIALS", "Materials", "Materials only"),
            ("NODE_GROUPS", "Node Groups", "Node groups only"),
            ("OBJECTS_COLLECTIONS", "Objects&Collections", "Objects and collections only"),
        ],
        default="ALL",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="These settings are reused in the Auto Cataloger panel.")
        col = layout.column(align=True)
        col.prop(self, "asset_library_root_folder")
        col.prop(self, "classification_mode")
        col.prop(self, "prefix_delimiter")
        col.prop(self, "catalog_root_prefix")
        col.prop(self, "target_type")


class AUTO_CATALOGER_preview_item(PropertyGroup):
    asset_name: StringProperty(name="Asset")
    catalog_path: StringProperty(name="Catalog")


class AUTO_CATALOGER_runtime(PropertyGroup):
    preview_items: CollectionProperty(type=AUTO_CATALOGER_preview_item)
    preview_index: IntProperty(default=0)
    preview_total: IntProperty(default=0)
    preview_catalog_count: IntProperty(default=0)
    preview_skipped_linked: IntProperty(default=0)
    preview_skipped_external: IntProperty(default=0)


class AUTO_CATALOGER_UL_preview(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.asset_name)
        row.label(text=item.catalog_path)


class AUTO_CATALOGER_OT_preview(Operator):
    bl_idname = "auto_cataloger.preview"
    bl_label = "Preview"
    bl_description = "Preview catalog assignments"
    bl_options = {"REGISTER"}

    def execute(self, context):
        prefs = _get_addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Addon preferences not found.")
            return {"CANCELLED"}

        state = context.scene.auto_cataloger_runtime
        state.preview_items.clear()

        try:
            _, plan, skipped_linked, skipped_external = _build_assignment_plan(context, prefs)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        by_catalog = defaultdict(int)
        for datablock, catalog_path in plan:
            by_catalog[catalog_path] += 1

        for datablock, catalog_path in plan[:50]:
            row = state.preview_items.add()
            row.asset_name = datablock.name
            row.catalog_path = catalog_path

        state.preview_total = len(plan)
        state.preview_catalog_count = len(by_catalog)
        state.preview_skipped_linked = skipped_linked
        state.preview_skipped_external = skipped_external
        self.report({"INFO"}, f"Preview: {len(plan)} assets, {len(by_catalog)} catalogs")
        return {"FINISHED"}


class AUTO_CATALOGER_OT_apply(Operator):
    bl_idname = "auto_cataloger.apply"
    bl_label = "Apply"
    bl_description = "Create catalogs and bulk assign asset catalog IDs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        prefs = _get_addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Addon preferences not found.")
            return {"CANCELLED"}

        try:
            library_root, plan, skipped_linked, skipped_external = _build_assignment_plan(context, prefs)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if not plan:
            self.report({"WARNING"}, "No assignable assets found with current options.")
            return {"CANCELLED"}

        catalog_paths = sorted({catalog_path for _, catalog_path in plan})
        uuid_map, created = _ensure_catalogs(library_root, catalog_paths)

        assigned = 0
        skipped_unmarkable = 0
        for datablock, catalog_path in plan:
            if getattr(datablock, "asset_data", None) is None:
                if hasattr(datablock, "asset_mark"):
                    datablock.asset_mark()
            asset_data = getattr(datablock, "asset_data", None)
            if asset_data is None:
                skipped_unmarkable += 1
                continue
            asset_data.catalog_id = uuid_map[catalog_path]
            assigned += 1

        state = context.scene.auto_cataloger_runtime
        state.preview_total = assigned
        state.preview_catalog_count = len(catalog_paths)
        state.preview_skipped_linked = skipped_linked
        state.preview_skipped_external = skipped_external

        self.report(
            {"INFO"},
            (
                f"Applied: {assigned} assets, catalogs: {len(catalog_paths)} "
                f"(created {created}), skipped linked {skipped_linked}, "
                f"skipped out-of-root {skipped_external}, unmarkable {skipped_unmarkable}"
            ),
        )
        return {"FINISHED"}


class AUTO_CATALOGER_PT_panel(Panel):
    bl_idname = "AUTO_CATALOGER_PT_panel"
    bl_label = "Auto Cataloger"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auto Cataloger"

    def draw(self, context):
        layout = self.layout
        prefs = _get_addon_prefs(context)
        state = context.scene.auto_cataloger_runtime

        if prefs is None:
            layout.label(text="Addon preferences not available.")
            return

        col = layout.column(align=True)
        col.prop(prefs, "asset_library_root_folder")
        col.prop(prefs, "classification_mode")
        col.prop(prefs, "prefix_delimiter")
        col.prop(prefs, "catalog_root_prefix")
        col.prop(prefs, "target_type")

        row = layout.row(align=True)
        row.operator("auto_cataloger.preview", text="Preview", icon="HIDE_OFF")
        row.operator("auto_cataloger.apply", text="Apply", icon="CHECKMARK")

        box = layout.box()
        box.label(text=f"Preview assets: {state.preview_total}")
        box.label(text=f"Catalogs: {state.preview_catalog_count}")
        box.label(text=f"Skipped linked: {state.preview_skipped_linked}")
        box.label(text=f"Skipped out-of-root: {state.preview_skipped_external}")
        box.template_list(
            "AUTO_CATALOGER_UL_preview",
            "",
            state,
            "preview_items",
            state,
            "preview_index",
            rows=6,
        )


classes = (
    AUTO_CATALOGER_preferences,
    AUTO_CATALOGER_preview_item,
    AUTO_CATALOGER_runtime,
    AUTO_CATALOGER_UL_preview,
    AUTO_CATALOGER_OT_preview,
    AUTO_CATALOGER_OT_apply,
    AUTO_CATALOGER_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.auto_cataloger_runtime = PointerProperty(type=AUTO_CATALOGER_runtime)


def unregister():
    del bpy.types.Scene.auto_cataloger_runtime
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
