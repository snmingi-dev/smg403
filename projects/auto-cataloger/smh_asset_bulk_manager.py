# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Auto Cataloger (Rules-based Asset Catalog Assignment)",
    "author": "SMG Tools",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Auto Cataloger",
    "description": "Rules-based catalog creation and bulk assignment for Asset Browser.",
    "doc_url": "https://github.com/snmingi-dev/smg403/tree/main/projects/auto-cataloger",
    "tracker_url": "https://github.com/snmingi-dev/smg403/issues",
    "category": "Asset Management",
}

import hashlib
import os
import re
import shutil
import uuid
from collections import defaultdict

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import AddonPreferences, Operator, Panel, PropertyGroup, UIList


ADDON_ID = __name__
CATALOG_FILE_NAME = "blender_assets.cats.txt"
MANUAL_LIBRARY_KEY = "__MANUAL__"
REGISTERED_LIBRARY_PREFIX = "LIB_"
DEFAULT_HEADER_LINES = [
    "# This is an Asset Catalog Definition file for Blender.",
    "# Managed by Auto Cataloger.",
    "VERSION 1",
]
_ASSET_LIBRARY_ENUM_CACHE = []


def _normalize_path_fragment(value):
    cleaned = value.replace("\\", "/").strip()
    cleaned = re.sub(r"/{2,}", "/", cleaned)
    return cleaned.strip("/")


def _safe_segment(value):
    token = re.sub(r"\s+", "_", value.strip())
    token = re.sub(r"[^A-Za-z0-9._-]", "_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "Uncategorized"


def _pretty_catalog_leaf(value):
    leaf = value.split("/")[-1]
    leaf = leaf.replace("_", " ").replace("-", " ")
    leaf = re.sub(r"\s+", " ", leaf).strip()
    if not leaf:
        return "Uncategorized"
    return leaf.title()


def _catalog_paths_for_root(asset_library_root):
    catalog_file = os.path.join(asset_library_root, CATALOG_FILE_NAME)
    backup_file = catalog_file + ".bak"
    return catalog_file, backup_file


def _addon_prefs(context):
    addon = context.preferences.addons.get(ADDON_ID)
    if addon is None:
        return None
    return addon.preferences


def _library_item_id_for_path(abs_path):
    digest = hashlib.sha1(abs_path.encode("utf-8")).hexdigest()[:12].upper()
    return f"{REGISTERED_LIBRARY_PREFIX}{digest}"


def _asset_library_items(self, context):
    items = [
        (
            MANUAL_LIBRARY_KEY,
            "Manual Folder",
            "Use Asset Library Root Folder directly",
        )
    ]

    prefs_context = context if context is not None else bpy.context
    preferences = getattr(prefs_context, "preferences", None)
    filepaths = getattr(preferences, "filepaths", None)
    libs = getattr(filepaths, "asset_libraries", []) if filepaths is not None else []

    used_ids = {MANUAL_LIBRARY_KEY}
    for lib in libs:
        lib_path = os.path.abspath(bpy.path.abspath(lib.path).strip())
        if not lib_path:
            continue

        item_id = _library_item_id_for_path(lib_path)
        if item_id in used_ids:
            continue
        used_ids.add(item_id)

        display_name = lib.name.strip() if lib.name else os.path.basename(lib_path)
        if not display_name:
            display_name = lib_path
        items.append((item_id, display_name, lib_path))

    # Keep strong refs for Blender dynamic enum callback lifecycle.
    _ASSET_LIBRARY_ENUM_CACHE.clear()
    _ASSET_LIBRARY_ENUM_CACHE.extend(items)
    return _ASSET_LIBRARY_ENUM_CACHE


def _resolve_registered_library_root(context, prefs):
    if prefs.asset_library_name == MANUAL_LIBRARY_KEY:
        return None

    libs = getattr(context.preferences.filepaths, "asset_libraries", [])
    for lib in libs:
        candidate = os.path.abspath(bpy.path.abspath(lib.path).strip())
        candidate_id = _library_item_id_for_path(candidate)
        if candidate_id == prefs.asset_library_name:
            return candidate
    return None


def _resolve_asset_library_root(context, prefs):
    registered = _resolve_registered_library_root(context, prefs)
    if registered:
        return registered, "REGISTERED"

    manual = bpy.path.abspath(prefs.asset_library_root_folder).strip()
    if manual:
        return os.path.abspath(manual), "MANUAL"

    if bpy.data.filepath:
        return os.path.dirname(os.path.abspath(bpy.data.filepath)), "BLEND"

    return None, "NONE"


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
    catalog_file_path, _ = _catalog_paths_for_root(asset_library_root)
    headers, path_to_entry = _read_catalog_file(catalog_file_path)

    created = 0
    for catalog_path in sorted(catalog_paths):
        norm = _normalize_path_fragment(catalog_path)
        if not norm or norm in path_to_entry:
            continue
        path_to_entry[norm] = {
            "uuid": str(uuid.uuid4()),
            "name": _pretty_catalog_leaf(norm),
        }
        created += 1

    if created > 0:
        _write_catalog_file_with_backup(catalog_file_path, headers, path_to_entry)

    return {path: data["uuid"] for path, data in path_to_entry.items()}, created


def _iter_target_datablocks(prefs):
    buckets = []
    if prefs.target_type == "ALL":
        buckets = [
            ("Materials", bpy.data.materials),
            ("Node_Groups", bpy.data.node_groups),
            ("Objects", bpy.data.objects),
            ("Collections", bpy.data.collections),
        ]
    elif prefs.target_type == "MATERIALS":
        buckets = [("Materials", bpy.data.materials)]
    elif prefs.target_type == "NODE_GROUPS":
        buckets = [("Node_Groups", bpy.data.node_groups)]
    elif prefs.target_type == "OBJECTS_COLLECTIONS":
        buckets = [("Objects", bpy.data.objects), ("Collections", bpy.data.collections)]

    for type_segment, bucket in buckets:
        for datablock in bucket:
            yield datablock, type_segment


def _source_file_for_datablock(datablock):
    linked = getattr(datablock, "library", None)
    if linked is not None and linked.filepath:
        return os.path.abspath(bpy.path.abspath(linked.filepath))

    weak_ref = getattr(datablock, "library_weak_reference", None)
    weak_path = getattr(weak_ref, "filepath", "") if weak_ref is not None else ""
    if weak_path:
        return os.path.abspath(bpy.path.abspath(weak_path))

    datablock_data = getattr(datablock, "data", None)
    if datablock_data is not None:
        data_linked = getattr(datablock_data, "library", None)
        if data_linked is not None and data_linked.filepath:
            return os.path.abspath(bpy.path.abspath(data_linked.filepath))
        data_weak_ref = getattr(datablock_data, "library_weak_reference", None)
        data_weak_path = getattr(data_weak_ref, "filepath", "") if data_weak_ref is not None else ""
        if data_weak_path:
            return os.path.abspath(bpy.path.abspath(data_weak_path))

    return None


def _source_dir_for_datablock(datablock):
    source_file = _source_file_for_datablock(datablock)
    if source_file:
        return os.path.dirname(source_file), False
    if bpy.data.filepath:
        return os.path.dirname(os.path.abspath(bpy.data.filepath)), True
    return None, False


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


def _plan_signature(prefs, root, plan):
    digest = hashlib.sha1()
    digest.update(root.encode("utf-8"))
    digest.update(prefs.asset_library_name.encode("utf-8"))
    digest.update(prefs.asset_library_root_folder.encode("utf-8"))
    digest.update(prefs.classification_mode.encode("utf-8"))
    digest.update(prefs.prefix_delimiter.encode("utf-8"))
    digest.update(prefs.catalog_root_prefix.encode("utf-8"))
    digest.update(prefs.target_type.encode("utf-8"))
    digest.update(str(bool(prefs.auto_mark_missing_as_assets)).encode("utf-8"))
    for datablock, catalog_path in plan:
        digest.update(datablock.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(catalog_path.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _build_assignment_plan(context, prefs):
    library_root, root_source = _resolve_asset_library_root(context, prefs)
    if not library_root:
        raise ValueError("Asset Library Root is empty and current .blend is not saved.")

    plan = []
    skipped_linked = 0
    skipped_external = 0

    for datablock, type_segment in _iter_target_datablocks(prefs):
        if getattr(datablock, "library", None) is not None:
            skipped_linked += 1
            continue

        if prefs.classification_mode == "NAME_PREFIX":
            tail = _prefix_from_name(datablock.name, prefs.prefix_delimiter)
        else:
            src_dir, from_blend_fallback = _source_dir_for_datablock(datablock)
            if not src_dir:
                skipped_external += 1
                continue
            rel = os.path.relpath(src_dir, library_root)
            if rel.startswith(".."):
                skipped_external += 1
                continue
            if rel == ".":
                tail = _safe_segment(type_segment) if from_blend_fallback else ""
            else:
                segments = [_safe_segment(part) for part in rel.replace("\\", "/").split("/") if part and part != "."]
                if from_blend_fallback:
                    segments.append(_safe_segment(type_segment))
                tail = "/".join(segments)

        catalog_path = _compose_catalog_path(prefs.catalog_root_prefix, tail)
        plan.append((datablock, catalog_path))

    return library_root, root_source, plan, skipped_linked, skipped_external


class AUTO_CATALOGER_preferences(AddonPreferences):
    bl_idname = ADDON_ID

    asset_library_name: EnumProperty(
        name="Asset Library",
        description="Use a registered Asset Library from Blender Preferences",
        items=_asset_library_items,
        default=MANUAL_LIBRARY_KEY,
    )
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
    auto_mark_missing_as_assets: BoolProperty(
        name="Auto-Mark Missing as Assets",
        description="If enabled, non-asset datablocks are asset_mark()'ed during Apply",
        default=False,
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Settings used by the Auto Cataloger panel.")
        col = layout.column(align=True)
        col.prop(self, "asset_library_name")
        col.prop(self, "asset_library_root_folder")
        col.prop(self, "classification_mode")
        col.prop(self, "prefix_delimiter")
        col.prop(self, "catalog_root_prefix")
        col.prop(self, "target_type")
        col.prop(self, "auto_mark_missing_as_assets")


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
    preview_ready: BoolProperty(default=False)
    preview_signature: StringProperty(default="")
    last_root: StringProperty(default="")
    last_root_source: StringProperty(default="")


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
        prefs = _addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Addon preferences not found.")
            return {"CANCELLED"}

        state = context.scene.auto_cataloger_runtime
        state.preview_items.clear()
        state.preview_ready = False
        state.preview_signature = ""

        try:
            root, root_source, plan, skipped_linked, skipped_external = _build_assignment_plan(context, prefs)
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
        state.preview_signature = _plan_signature(prefs, root, plan)
        state.preview_ready = True
        state.last_root = root
        state.last_root_source = root_source

        self.report({"INFO"}, f"Preview: {len(plan)} assets, {len(by_catalog)} catalogs")
        return {"FINISHED"}


class AUTO_CATALOGER_OT_apply(Operator):
    bl_idname = "auto_cataloger.apply"
    bl_label = "Apply"
    bl_description = "Create catalogs and bulk assign asset catalog IDs"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        prefs = _addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Addon preferences not found.")
            return {"CANCELLED"}

        state = context.scene.auto_cataloger_runtime

        try:
            root, root_source, plan, skipped_linked, skipped_external = _build_assignment_plan(context, prefs)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        plan_sig = _plan_signature(prefs, root, plan)
        if not state.preview_ready:
            self.report({"ERROR"}, "Run Preview first.")
            return {"CANCELLED"}
        if state.preview_signature != plan_sig:
            self.report({"ERROR"}, "Options or target set changed. Run Preview again.")
            return {"CANCELLED"}
        if not plan:
            self.report({"WARNING"}, "No assignable assets found with current options.")
            return {"CANCELLED"}

        catalog_paths = sorted({catalog_path for _, catalog_path in plan})
        uuid_map, created = _ensure_catalogs(root, catalog_paths)

        assigned = 0
        skipped_unmarked = 0
        auto_marked = 0
        for datablock, catalog_path in plan:
            asset_data = getattr(datablock, "asset_data", None)
            if asset_data is None and prefs.auto_mark_missing_as_assets and hasattr(datablock, "asset_mark"):
                datablock.asset_mark()
                asset_data = getattr(datablock, "asset_data", None)
                if asset_data is not None:
                    auto_marked += 1

            if asset_data is None:
                skipped_unmarked += 1
                continue

            asset_data.catalog_id = uuid_map[catalog_path]
            assigned += 1

        state.preview_total = assigned
        state.preview_catalog_count = len(catalog_paths)
        state.preview_skipped_linked = skipped_linked
        state.preview_skipped_external = skipped_external
        state.preview_ready = False
        state.preview_signature = ""
        state.last_root = root
        state.last_root_source = root_source

        self.report(
            {"INFO"},
            (
                f"Applied: {assigned} assets, catalogs: {len(catalog_paths)} (created {created}), "
                f"skipped linked {skipped_linked}, skipped out-of-root {skipped_external}, "
                f"skipped non-assets {skipped_unmarked}, auto-marked {auto_marked}"
            ),
        )
        return {"FINISHED"}


class AUTO_CATALOGER_OT_restore_backup(Operator):
    bl_idname = "auto_cataloger.restore_backup"
    bl_label = "Restore from .bak"
    bl_description = "Restore blender_assets.cats.txt from blender_assets.cats.txt.bak"
    bl_options = {"REGISTER"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        prefs = _addon_prefs(context)
        if prefs is None:
            self.report({"ERROR"}, "Addon preferences not found.")
            return {"CANCELLED"}

        root, _ = _resolve_asset_library_root(context, prefs)
        if not root:
            self.report({"ERROR"}, "Cannot resolve Asset Library Root.")
            return {"CANCELLED"}

        catalog_file, backup_file = _catalog_paths_for_root(root)
        if not os.path.exists(backup_file):
            self.report({"ERROR"}, f"Backup not found: {backup_file}")
            return {"CANCELLED"}

        os.makedirs(root, exist_ok=True)
        shutil.copy2(backup_file, catalog_file)
        self.report({"INFO"}, f"Restored catalog file from backup: {backup_file}")
        return {"FINISHED"}


class AUTO_CATALOGER_PT_panel(Panel):
    bl_idname = "AUTO_CATALOGER_PT_panel"
    bl_label = "Auto Cataloger"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Auto Cataloger"

    def draw(self, context):
        layout = self.layout
        prefs = _addon_prefs(context)
        state = context.scene.auto_cataloger_runtime

        if prefs is None:
            layout.label(text="Addon preferences not available.")
            return

        root, root_source = _resolve_asset_library_root(context, prefs)
        catalog_file = ""
        backup_file = ""
        if root:
            catalog_file, backup_file = _catalog_paths_for_root(root)

        col = layout.column(align=True)
        col.prop(prefs, "asset_library_name")
        col.prop(prefs, "asset_library_root_folder")
        col.prop(prefs, "classification_mode")
        col.prop(prefs, "prefix_delimiter")
        col.prop(prefs, "catalog_root_prefix")
        col.prop(prefs, "target_type")
        col.prop(prefs, "auto_mark_missing_as_assets")

        row = layout.row(align=True)
        row.operator("auto_cataloger.preview", text="Preview", icon="HIDE_OFF")
        row.operator("auto_cataloger.apply", text="Apply", icon="CHECKMARK")

        safety = layout.box()
        safety.label(text="Safety & Recovery")
        safety.label(text=f"Root source: {root_source}")
        if root:
            safety.label(text=f"Catalog file: {'Exists' if os.path.exists(catalog_file) else 'Missing'}")
            safety.label(text=f"Backup file: {'Exists' if os.path.exists(backup_file) else 'Missing'}")
            safety.label(text=f".cats: {catalog_file}")
            safety.label(text=f".bak: {backup_file}")
        else:
            safety.label(text="Root not resolved yet.")
        restore_row = safety.row(align=True)
        restore_row.enabled = bool(backup_file and os.path.exists(backup_file))
        restore_row.operator("auto_cataloger.restore_backup", icon="LOOP_BACK")
        safety.label(text="Note: Blender Undo does not revert external .cats file changes.")

        box = layout.box()
        box.label(text=f"Preview assets: {state.preview_total}")
        box.label(text=f"Catalogs: {state.preview_catalog_count}")
        box.label(text=f"Preview ready: {'Yes' if state.preview_ready else 'No'}")
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
    AUTO_CATALOGER_OT_restore_backup,
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
