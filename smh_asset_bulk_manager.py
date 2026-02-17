bl_info = {
    "name": "SMH Asset Bulk Manager MVP",
    "author": "snmingi-dev + Codex",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > SMH Assets / Asset Browser > Sidebar > SMH Assets",
    "description": "Bulk catalog automation and duplicate replacement for Blender Asset Browser workflows.",
    "category": "Asset Management",
}

import os
import re
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
from bpy.types import Operator, Panel, PropertyGroup, UIList


CATALOG_FILE_NAME = "blender_assets.cats.txt"
DEFAULT_HEADER_LINES = [
    "# This is an Asset Catalog Definition file for Blender.",
    "# You can edit it by hand, but keep the format intact.",
    "VERSION 1",
]


def _normalize_catalog_path(value):
    normalized = value.strip().replace("\\", "/")
    normalized = re.sub(r"/{2,}", "/", normalized)
    return normalized.strip("/")


def _safe_catalog_name(path):
    if not path:
        return "Uncategorized"
    return path.split("/")[-1]


def _base_name(name):
    return re.sub(r"\.\d{3}$", "", name)


def _selected_local_ids(context):
    collected = []
    seen = set()

    def _append_if_id(data):
        if not isinstance(data, bpy.types.ID):
            return
        pointer = data.as_pointer()
        if pointer in seen:
            return
        seen.add(pointer)
        collected.append(data)

    for obj in getattr(context, "selected_objects", []) or []:
        _append_if_id(obj)

    for data in getattr(context, "selected_ids", []) or []:
        _append_if_id(data)

    for asset_rep in getattr(context, "selected_assets", []) or []:
        local_id = getattr(asset_rep, "local_id", None)
        if local_id is not None:
            _append_if_id(local_id)

    active_obj = getattr(context, "active_object", None)
    if active_obj is not None:
        _append_if_id(active_obj)

    return collected


def _names_from_folder(folder_path, recursive):
    if not folder_path:
        return []
    if not os.path.isdir(folder_path):
        return []

    names = []
    for root, dirs, files in os.walk(folder_path):
        for directory in dirs:
            if not directory.startswith("."):
                names.append(directory)
        for filename in files:
            if filename.startswith("."):
                continue
            stem, _ = os.path.splitext(filename)
            if stem:
                names.append(stem)
        if not recursive:
            break
    return names


def _catalog_path_from_name(name, pattern, catalog_root):
    root = _normalize_catalog_path(catalog_root)
    match = re.search(pattern, name)
    if not match:
        return None
    if match.lastindex and match.lastindex >= 1:
        token = match.group(1)
    else:
        token = match.group(0)
    token = token.strip("_-/ ")
    if not token:
        return None
    token = token.replace(" ", "_")
    return _normalize_catalog_path(f"{root}/{token}" if root else token)


def _read_catalog_file(catalog_file_path):
    header_lines = []
    catalogs_by_path = {}

    if not os.path.exists(catalog_file_path):
        return DEFAULT_HEADER_LINES[:], catalogs_by_path

    with open(catalog_file_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#") or line.startswith("VERSION "):
                header_lines.append(line)
                continue

            parts = line.split(":", 2)
            if len(parts) != 3:
                continue

            catalog_uuid, catalog_path, simple_name = parts
            catalogs_by_path[catalog_path] = {
                "uuid": catalog_uuid,
                "name": simple_name,
            }

    if not any(line.startswith("VERSION ") for line in header_lines):
        header_lines.append("VERSION 1")
    if not header_lines:
        header_lines = DEFAULT_HEADER_LINES[:]

    return header_lines, catalogs_by_path


def _write_catalog_file(catalog_file_path, header_lines, catalogs_by_path):
    sorted_paths = sorted(catalogs_by_path.keys())
    output_lines = []

    for line in header_lines:
        output_lines.append(line.rstrip())

    for path in sorted_paths:
        entry = catalogs_by_path[path]
        output_lines.append(f"{entry['uuid']}:{path}:{entry['name']}")

    with open(catalog_file_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(output_lines) + "\n")


def _ensure_catalog(asset_library_root, catalog_path):
    normalized_path = _normalize_catalog_path(catalog_path)
    if not normalized_path:
        raise ValueError("Catalog path is empty.")

    os.makedirs(asset_library_root, exist_ok=True)
    catalog_file_path = os.path.join(asset_library_root, CATALOG_FILE_NAME)

    header_lines, catalogs_by_path = _read_catalog_file(catalog_file_path)
    created = False
    if normalized_path not in catalogs_by_path:
        catalogs_by_path[normalized_path] = {
            "uuid": str(uuid.uuid4()),
            "name": _safe_catalog_name(normalized_path),
        }
        _write_catalog_file(catalog_file_path, header_lines, catalogs_by_path)
        created = True

    return catalogs_by_path[normalized_path]["uuid"], created


def _id_collection(type_key):
    mapping = {
        "MESH": bpy.data.meshes,
        "MATERIAL": bpy.data.materials,
        "ACTION": bpy.data.actions,
        "NODETREE": bpy.data.node_groups,
        "IMAGE": bpy.data.images,
        "COLLECTION": bpy.data.collections,
    }
    return mapping.get(type_key)


def _duplicate_groups(type_key):
    collection = _id_collection(type_key)
    if collection is None:
        return {}

    groups = defaultdict(list)
    for datablock in collection:
        groups[_base_name(datablock.name)].append(datablock)

    return {base: blocks for base, blocks in groups.items() if len(blocks) > 1}


def _choose_keeper(base_name, datablocks):
    exact = [item for item in datablocks if item.name == base_name]
    if exact:
        return exact[0]
    return sorted(datablocks, key=lambda item: (item.users, -len(item.name)), reverse=True)[0]


def _remove_datablock(collection, datablock):
    try:
        collection.remove(datablock, do_unlink=True)
        return True
    except TypeError:
        try:
            collection.remove(datablock)
            return True
        except Exception:
            return False
    except Exception:
        return False


class SMH_DuplicateItem(PropertyGroup):
    base_name: StringProperty(name="Base Name")
    keeper_name: StringProperty(name="Keep")
    duplicate_names: StringProperty(name="Duplicates")


class SMH_AssetSettings(PropertyGroup):
    asset_library_root: StringProperty(
        name="Asset Library Root",
        description="Folder containing blender_assets.cats.txt",
        subtype="DIR_PATH",
    )
    source_mode: EnumProperty(
        name="Source",
        items=[
            ("SELECTED", "Selected Assets", "Use selected local assets/data-blocks"),
            ("FOLDER", "Folder Scan", "Use names from files/folders"),
        ],
        default="SELECTED",
    )
    scan_folder: StringProperty(
        name="Scan Folder",
        description="Folder to scan for names",
        subtype="DIR_PATH",
    )
    scan_recursive: BoolProperty(
        name="Recursive",
        description="Scan sub-folders",
        default=True,
    )
    name_pattern: StringProperty(
        name="Name Pattern (Regex)",
        description="Regex used to extract category token. Group 1 is preferred",
        default=r"^([A-Za-z0-9]+)_",
    )
    catalog_base_path: StringProperty(
        name="Catalog Root",
        description="Root catalog path where auto categories are created",
        default="Auto",
    )
    manual_catalog_path: StringProperty(
        name="Manual Catalog",
        description="If set, bulk assign uses this path for all selected assets",
        default="",
    )
    duplicate_type: EnumProperty(
        name="Duplicate Type",
        items=[
            ("MESH", "Mesh", "Find duplicate meshes"),
            ("MATERIAL", "Material", "Find duplicate materials"),
            ("ACTION", "Action", "Find duplicate actions"),
            ("NODETREE", "Node Group", "Find duplicate node groups"),
            ("IMAGE", "Image", "Find duplicate images"),
            ("COLLECTION", "Collection", "Find duplicate collections"),
        ],
        default="MESH",
    )
    duplicate_items: CollectionProperty(type=SMH_DuplicateItem)
    duplicate_index: IntProperty(default=0)
    last_created_catalogs: IntProperty(default=0)
    last_assigned_assets: IntProperty(default=0)
    last_duplicate_groups: IntProperty(default=0)
    last_replaced_assets: IntProperty(default=0)


class SMH_UL_duplicate_items(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.33)
        split.label(text=item.base_name)
        split.label(text=f"keep: {item.keeper_name}")
        layout.label(text=item.duplicate_names)


class SMH_OT_auto_catalog_from_names(Operator):
    bl_idname = "smh_assets.auto_catalog_from_names"
    bl_label = "Auto Create Catalogs"
    bl_description = "Create catalogs from selected asset/folder names using regex pattern"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.smh_assets
        asset_library_root = bpy.path.abspath(settings.asset_library_root).strip()
        if not asset_library_root:
            self.report({"ERROR"}, "Set Asset Library Root first.")
            return {"CANCELLED"}

        try:
            re.compile(settings.name_pattern)
        except re.error as exc:
            self.report({"ERROR"}, f"Invalid regex: {exc}")
            return {"CANCELLED"}

        if settings.source_mode == "SELECTED":
            names = [item.name for item in _selected_local_ids(context)]
        else:
            folder = bpy.path.abspath(settings.scan_folder).strip()
            names = _names_from_folder(folder, settings.scan_recursive)

        if not names:
            self.report({"WARNING"}, "No names found from selected source.")
            return {"CANCELLED"}

        unique_paths = set()
        created_count = 0
        for name in names:
            catalog_path = _catalog_path_from_name(name, settings.name_pattern, settings.catalog_base_path)
            if not catalog_path:
                continue
            unique_paths.add(catalog_path)

        for catalog_path in sorted(unique_paths):
            _, created = _ensure_catalog(asset_library_root, catalog_path)
            if created:
                created_count += 1

        settings.last_created_catalogs = created_count
        self.report(
            {"INFO"},
            f"Catalogs processed: {len(unique_paths)}, newly created: {created_count}",
        )
        return {"FINISHED"}


class SMH_OT_bulk_assign_catalog(Operator):
    bl_idname = "smh_assets.bulk_assign_catalog"
    bl_label = "Bulk Assign to Catalog"
    bl_description = "Assign selected assets/data-blocks to catalog in bulk"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.smh_assets
        asset_library_root = bpy.path.abspath(settings.asset_library_root).strip()
        if not asset_library_root:
            self.report({"ERROR"}, "Set Asset Library Root first.")
            return {"CANCELLED"}

        try:
            re.compile(settings.name_pattern)
        except re.error as exc:
            self.report({"ERROR"}, f"Invalid regex: {exc}")
            return {"CANCELLED"}

        selected_ids = _selected_local_ids(context)
        if not selected_ids:
            self.report({"ERROR"}, "No selected local IDs found.")
            return {"CANCELLED"}

        cache = {}
        assigned = 0
        skipped = 0

        for datablock in selected_ids:
            if settings.manual_catalog_path.strip():
                catalog_path = _normalize_catalog_path(settings.manual_catalog_path)
            else:
                catalog_path = _catalog_path_from_name(
                    datablock.name,
                    settings.name_pattern,
                    settings.catalog_base_path,
                )

            if not catalog_path:
                skipped += 1
                continue

            if catalog_path not in cache:
                catalog_uuid, _ = _ensure_catalog(asset_library_root, catalog_path)
                cache[catalog_path] = catalog_uuid

            if getattr(datablock, "asset_data", None) is None:
                if hasattr(datablock, "asset_mark"):
                    datablock.asset_mark()

            asset_data = getattr(datablock, "asset_data", None)
            if asset_data is None:
                skipped += 1
                continue

            asset_data.catalog_id = cache[catalog_path]
            assigned += 1

        settings.last_assigned_assets = assigned
        self.report({"INFO"}, f"Assigned: {assigned}, skipped: {skipped}")
        return {"FINISHED"}


class SMH_OT_find_duplicates(Operator):
    bl_idname = "smh_assets.find_duplicates"
    bl_label = "Find Duplicate Assets"
    bl_description = "Find duplicated data-block names based on .001 suffix style"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.smh_assets
        groups = _duplicate_groups(settings.duplicate_type)

        settings.duplicate_items.clear()
        for base in sorted(groups.keys()):
            keeper = _choose_keeper(base, groups[base])
            duplicates = [item.name for item in groups[base] if item != keeper]

            row = settings.duplicate_items.add()
            row.base_name = base
            row.keeper_name = keeper.name
            row.duplicate_names = ", ".join(duplicates)

        settings.last_duplicate_groups = len(groups)
        self.report({"INFO"}, f"Duplicate groups found: {len(groups)}")
        return {"FINISHED"}


class SMH_OT_replace_all_duplicates(Operator):
    bl_idname = "smh_assets.replace_all_duplicates"
    bl_label = "Replace All Duplicates"
    bl_description = "Remap duplicate users to keeper and remove duplicates"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.smh_assets
        collection = _id_collection(settings.duplicate_type)
        groups = _duplicate_groups(settings.duplicate_type)
        if not groups:
            self.report({"INFO"}, "No duplicates found.")
            settings.last_replaced_assets = 0
            return {"CANCELLED"}

        replaced = 0
        failed = 0

        for base, datablocks in groups.items():
            keeper = _choose_keeper(base, datablocks)
            for old in datablocks:
                if old == keeper:
                    continue
                try:
                    old.user_remap(keeper)
                    if _remove_datablock(collection, old):
                        replaced += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1

        settings.last_replaced_assets = replaced
        self.report({"INFO"}, f"Replaced: {replaced}, failed: {failed}")
        return {"FINISHED"}


class _SMHPanelMixin:
    bl_category = "SMH Assets"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.smh_assets

        box = layout.box()
        box.label(text="Catalog Automation")
        box.prop(settings, "asset_library_root")
        box.prop(settings, "source_mode")

        if settings.source_mode == "FOLDER":
            box.prop(settings, "scan_folder")
            box.prop(settings, "scan_recursive")

        box.prop(settings, "name_pattern")
        box.prop(settings, "catalog_base_path")
        box.operator("smh_assets.auto_catalog_from_names", icon="OUTLINER_COLLECTION")

        box.separator()
        box.prop(settings, "manual_catalog_path")
        box.operator("smh_assets.bulk_assign_catalog", icon="ASSET_MANAGER")

        stats = box.column(align=True)
        stats.label(text=f"Created catalogs: {settings.last_created_catalogs}")
        stats.label(text=f"Assigned assets: {settings.last_assigned_assets}")

        dup = layout.box()
        dup.label(text="Duplicate Replace")
        dup.prop(settings, "duplicate_type")
        row = dup.row(align=True)
        row.operator("smh_assets.find_duplicates", icon="VIEWZOOM")
        row.operator("smh_assets.replace_all_duplicates", icon="AUTOMERGE_ON")

        dup.label(text=f"Groups found: {settings.last_duplicate_groups}")
        dup.label(text=f"Replaced: {settings.last_replaced_assets}")

        dup.template_list(
            "SMH_UL_duplicate_items",
            "",
            settings,
            "duplicate_items",
            settings,
            "duplicate_index",
            rows=5,
        )


class SMH_PT_assets_view3d(_SMHPanelMixin, Panel):
    bl_idname = "SMH_PT_assets_view3d"
    bl_label = "SMH Asset Bulk Manager"
    bl_space_type = "VIEW_3D"


class SMH_PT_assets_browser(_SMHPanelMixin, Panel):
    bl_idname = "SMH_PT_assets_browser"
    bl_label = "SMH Asset Bulk Manager"
    bl_space_type = "FILE_BROWSER"

    @classmethod
    def poll(cls, context):
        area = getattr(context, "area", None)
        return area is not None and getattr(area, "ui_type", "") == "ASSETS"


classes = (
    SMH_DuplicateItem,
    SMH_AssetSettings,
    SMH_UL_duplicate_items,
    SMH_OT_auto_catalog_from_names,
    SMH_OT_bulk_assign_catalog,
    SMH_OT_find_duplicates,
    SMH_OT_replace_all_duplicates,
    SMH_PT_assets_view3d,
    SMH_PT_assets_browser,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.smh_assets = PointerProperty(type=SMH_AssetSettings)


def unregister():
    del bpy.types.Scene.smh_assets
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
