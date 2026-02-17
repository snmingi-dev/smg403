# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Post-Unwrap Cleaner",
    "author": "SMG Tools",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "UV Editor > Sidebar > Post-Unwrap Cleaner",
    "description": "One-click post unwrap cleanup: straighten, relax, pack.",
    "doc_url": "https://github.com/snmingi-dev/smg403/tree/main/projects/post-unwrap-cleaner",
    "tracker_url": "https://github.com/snmingi-dev/smg403/issues",
    "category": "UV",
}

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty
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


def _snapshot_uv_selection_state(bm, uv_layer):
    snapshot = []
    for face in bm.faces:
        if face.hide:
            continue
        for loop in face.loops:
            luv = loop[uv_layer]
            snapshot.append((loop, luv.select, luv.select_edge))
    return snapshot


def _restore_uv_selection_state(snapshot, uv_layer):
    for loop, selected, selected_edge in snapshot:
        try:
            luv = loop[uv_layer]
        except ReferenceError:
            continue
        luv.select = selected
        luv.select_edge = selected_edge


def _prepare_target_selection(bm, uv_layer, target, respect_pins):
    target_loops = []
    skipped_pins = 0

    for face in bm.faces:
        if face.hide:
            continue
        for loop in face.loops:
            luv = loop[uv_layer]
            if respect_pins and luv.pin_uv:
                skipped_pins += 1
                continue
            if target == "SELECTED" and not luv.select:
                continue
            target_loops.append(loop)

    for face in bm.faces:
        if face.hide:
            continue
        for loop in face.loops:
            luv = loop[uv_layer]
            luv.select = False
            luv.select_edge = False

    for loop in target_loops:
        luv = loop[uv_layer]
        luv.select = True
        luv.select_edge = True

    return target_loops, skipped_pins


def _straighten_selected_loops(loops, uv_layer, threshold):
    adjusted = 0
    for loop in loops:
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

    run_straighten: BoolProperty(name="Run Straighten", default=True)
    run_relax: BoolProperty(name="Run Relax", default=True)
    run_pack: BoolProperty(name="Run Pack", default=True)
    respect_pins: BoolProperty(
        name="Respect Pins",
        description="Do not move pinned UVs",
        default=True,
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

        if not (settings.run_straighten or settings.run_relax or settings.run_pack):
            self.report({"ERROR"}, "Enable at least one step: Straighten, Relax, or Pack.")
            return {"CANCELLED"}

        in_mode = getattr(context, "objects_in_mode_unique_data", None)
        if in_mode and len(in_mode) > 1:
            self.report({"ERROR"}, "Multi-object Edit Mode is not supported.")
            return {"CANCELLED"}

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        uv_layer = bm.loops.layers.uv.verify()

        snapshot = _snapshot_uv_selection_state(bm, uv_layer)
        loops, skipped_pins = _prepare_target_selection(
            bm=bm,
            uv_layer=uv_layer,
            target=settings.target,
            respect_pins=settings.respect_pins,
        )

        if not loops:
            _restore_uv_selection_state(snapshot, uv_layer)
            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
            self.report({"WARNING"}, "No UVs available for current target/pin filter.")
            return {"CANCELLED"}

        changed = 0
        relaxed = False
        packed = False

        area = context.area
        region = _get_uv_window_region(area)
        if region is None:
            _restore_uv_selection_state(snapshot, uv_layer)
            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
            self.report({"ERROR"}, "UV window region not found.")
            return {"CANCELLED"}

        try:
            if settings.run_straighten:
                changed = _straighten_selected_loops(
                    loops=loops,
                    uv_layer=uv_layer,
                    threshold=settings.straighten_threshold,
                )

            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

            with context.temp_override(
                area=area,
                region=region,
                active_object=obj,
                object=obj,
                edit_object=obj,
            ):
                if settings.run_relax:
                    bpy.ops.uv.minimize_stretch(iterations=settings.relax_iterations)
                    relaxed = True
                if settings.run_pack:
                    bpy.ops.uv.pack_islands(margin=settings.packing_margin)
                    packed = True

        except RuntimeError as exc:
            _restore_uv_selection_state(snapshot, uv_layer)
            bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
            self.report({"ERROR"}, f"UV operation failed: {exc}")
            return {"CANCELLED"}

        _restore_uv_selection_state(snapshot, uv_layer)
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)

        self.report(
            {"INFO"},
            (
                f"Clean complete: straightened={changed}, "
                f"relaxed={'yes' if relaxed else 'no'}, packed={'yes' if packed else 'no'}, "
                f"pinned_skipped={skipped_pins}"
            ),
        )
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

        layout.separator()
        flow = layout.column(align=True)
        flow.label(text="Pipeline Steps")
        flow.prop(settings, "run_straighten")
        flow.prop(settings, "run_relax")
        flow.prop(settings, "run_pack")
        flow.prop(settings, "respect_pins")

        layout.operator("puc.one_click_clean", icon="CHECKMARK")
        layout.label(text="Selection is restored after execution.")


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
