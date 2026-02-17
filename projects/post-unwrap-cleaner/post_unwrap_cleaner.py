# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Post-Unwrap Cleaner",
    "author": "snmingi-dev + Codex",
    "version": (0, 1, 0),
    "blender": (4, 3, 0),
    "location": "UV Editor > Sidebar > Post-Unwrap Cleaner",
    "description": "One-click post unwrap cleanup: straighten, relax, pack.",
    "category": "UV",
}

import bpy
import bmesh
from bpy.props import EnumProperty, FloatProperty, IntProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup


def _get_edit_mesh_object(context):
    obj = context.edit_object
    if obj is None or obj.type != "MESH":
        return None
    return obj


def _get_uv_window_region(area):
    for region in area.regions:
        if region.type == "WINDOW":
            return region
    return None


def _iter_target_loops(bm, uv_layer, target):
    for face in bm.faces:
        if face.hide:
            continue
        for loop in face.loops:
            luv = loop[uv_layer]
            if target == "SELECTED" and not luv.select:
                continue
            yield loop


def _straighten_selected_loops(bm, uv_layer, threshold, target):
    adjusted = 0
    for loop in _iter_target_loops(bm, uv_layer, target):
        luv_a = loop[uv_layer]
        luv_b = loop.link_loop_next[uv_layer]
        dx = luv_b.uv.x - luv_a.uv.x
        dy = luv_b.uv.y - luv_a.uv.y
        adx = abs(dx)
        ady = abs(dy)
        if adx == 0.0 and ady == 0.0:
            continue
        if adx <= ady * threshold:
            snap_x = (luv_a.uv.x + luv_b.uv.x) * 0.5
            luv_a.uv.x = snap_x
            luv_b.uv.x = snap_x
            adjusted += 1
        elif ady <= adx * threshold:
            snap_y = (luv_a.uv.y + luv_b.uv.y) * 0.5
            luv_a.uv.y = snap_y
            luv_b.uv.y = snap_y
            adjusted += 1
    return adjusted


def _force_select_all_uv(bm, uv_layer):
    for face in bm.faces:
        if face.hide:
            continue
        for loop in face.loops:
            luv = loop[uv_layer]
            luv.select = True
            luv.select_edge = True


class PUC_Settings(PropertyGroup):
    straighten_threshold: FloatProperty(
        name="Straighten Threshold",
        min=0.1,
        max=1.0,
        default=0.35,
        description="Higher values straighten more edges",
    )
    relax_iterations: IntProperty(
        name="Relax Iterations",
        min=1,
        max=20,
        default=6,
        description="Iterations for UV relax pass",
    )
    packing_margin: FloatProperty(
        name="Packing Margin",
        min=0.01,
        max=0.1,
        default=0.02,
        description="Island packing margin",
    )
    target: EnumProperty(
        name="Target",
        items=[
            ("SELECTED", "Selected Islands", "Process selected islands only"),
            ("ALL", "All Islands", "Process all islands"),
        ],
        default="SELECTED",
    )


class PUC_OT_one_click_clean(Operator):
    bl_idname = "puc.one_click_clean"
    bl_label = "One-Click Clean"
    bl_description = "Straighten + Relax + Pack in one step"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        area = context.area
        if area is None or area.type != "IMAGE_EDITOR":
            return False
        return _get_edit_mesh_object(context) is not None

    def execute(self, context):
        settings = context.scene.puc_settings
        obj = _get_edit_mesh_object(context)
        if obj is None:
            self.report({"ERROR"}, "Enter Edit Mode with a mesh object.")
            return {"CANCELLED"}

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.verify()

        if settings.target == "ALL":
            _force_select_all_uv(bm, uv_layer)

        changed = _straighten_selected_loops(
            bm=bm,
            uv_layer=uv_layer,
            threshold=settings.straighten_threshold,
            target=settings.target,
        )
        if changed == 0 and settings.target == "SELECTED":
            self.report({"WARNING"}, "No selected UV islands/edges to process.")
            return {"CANCELLED"}

        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

        area = context.area
        region = _get_uv_window_region(area)
        if region is None:
            self.report({"ERROR"}, "UV window region not found.")
            return {"CANCELLED"}

        with context.temp_override(
            area=area,
            region=region,
            active_object=obj,
            object=obj,
            edit_object=obj,
        ):
            bpy.ops.uv.minimize_stretch(iterations=settings.relax_iterations)
            bpy.ops.uv.pack_islands(margin=settings.packing_margin)

        self.report({"INFO"}, f"Clean complete: straightened edges {changed}")
        return {"FINISHED"}


class PUC_PT_uv_sidebar(Panel):
    bl_idname = "PUC_PT_uv_sidebar"
    bl_label = "Post-Unwrap Cleaner"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Post-Unwrap Cleaner"

    @classmethod
    def poll(cls, context):
        area = context.area
        if area is None or area.type != "IMAGE_EDITOR":
            return False
        return getattr(area, "ui_type", "") in {"UV", "IMAGE_EDITOR"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.puc_settings

        col = layout.column(align=True)
        col.prop(settings, "straighten_threshold")
        col.prop(settings, "relax_iterations")
        col.prop(settings, "packing_margin")
        col.prop(settings, "target")
        layout.operator("puc.one_click_clean", icon="CHECKMARK")


classes = (
    PUC_Settings,
    PUC_OT_one_click_clean,
    PUC_PT_uv_sidebar,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.puc_settings = PointerProperty(type=PUC_Settings)


def unregister():
    del bpy.types.Scene.puc_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
