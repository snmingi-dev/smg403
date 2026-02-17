# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Smart Curve Helper",
    "author": "snmingi-dev + Codex",
    "version": (0, 1, 0),
    "blender": (4, 3, 0),
    "location": "3D View > Sidebar > Smart Curve Helper",
    "description": "Align, flatten, and equalize Bezier handles quickly.",
    "category": "Curve",
}

import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector


def _active_curve_object(context):
    obj = context.active_object
    if obj is None or obj.type != "CURVE":
        return None
    return obj


def _axis_local_vector(context, obj, axis):
    if axis == "X":
        return Vector((1.0, 0.0, 0.0))
    if axis == "Y":
        return Vector((0.0, 1.0, 0.0))
    if axis == "Z":
        return Vector((0.0, 0.0, 1.0))

    region_3d = context.region_data
    if region_3d is None:
        return None
    view_dir_world = region_3d.view_rotation @ Vector((0.0, 0.0, -1.0))
    view_dir_local = obj.matrix_world.to_3x3().inverted_safe() @ view_dir_world
    if view_dir_local.length == 0.0:
        return None
    return view_dir_local.normalized()


def _iter_target_points(obj, target):
    for spline in obj.data.splines:
        if spline.type != "BEZIER":
            continue
        for point in spline.bezier_points:
            if target == "SELECTED_ONLY":
                if not (point.select_control_point or point.select_left_handle or point.select_right_handle):
                    continue
            yield point


def _set_handle_type(point, handle_type):
    point.handle_left_type = handle_type
    point.handle_right_type = handle_type


def _flatten_vector(value, axis_vec, target_dot, strength):
    delta = (target_dot - value.dot(axis_vec)) * strength
    return value + axis_vec * delta


class SCH_Settings(PropertyGroup):
    axis: EnumProperty(
        name="Axis",
        items=[
            ("X", "X", "Use X axis"),
            ("Y", "Y", "Use Y axis"),
            ("Z", "Z", "Use Z axis"),
            ("VIEW", "View", "Use current viewport direction"),
        ],
        default="X",
    )
    handle_type: EnumProperty(
        name="Handle Type",
        items=[
            ("AUTO", "Auto", "Auto handles"),
            ("VECTOR", "Vector", "Vector handles"),
            ("ALIGNED", "Aligned", "Aligned handles"),
            ("FREE", "Free", "Free handles"),
        ],
        default="ALIGNED",
    )
    strength: FloatProperty(
        name="Strength",
        min=0.0,
        max=2.0,
        default=1.0,
    )
    target: EnumProperty(
        name="Target",
        items=[
            ("SELECTED_ONLY", "Selected Points Only", "Affect selected Bezier points only"),
            ("ALL_IN_OBJECT", "All Curves in Object", "Affect all Bezier points in active object"),
        ],
        default="SELECTED_ONLY",
    )


class SCH_OT_align_handles(Operator):
    bl_idname = "smart_curve.align_handles"
    bl_label = "Align Handles"
    bl_description = "Align selected handles along axis"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _active_curve_object(context) is not None

    def execute(self, context):
        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis)
        if axis_vec is None:
            self.report({"ERROR"}, "View axis is unavailable in current context.")
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, "No target Bezier points.")
            return {"CANCELLED"}

        for point in points:
            co = point.co.copy()
            for side_name, sign_hint in (("handle_left", -1.0), ("handle_right", 1.0)):
                handle = getattr(point, side_name)
                vec = handle - co
                length = vec.length
                if length == 0.0:
                    sign = sign_hint
                    length = 0.0001
                else:
                    sign = 1.0 if vec.dot(axis_vec) >= 0.0 else -1.0
                target = co + axis_vec * length * sign
                setattr(point, side_name, handle.lerp(target, settings.strength))

            _set_handle_type(point, settings.handle_type)

        obj.data.update()
        self.report({"INFO"}, f"Aligned {len(points)} points")
        return {"FINISHED"}


class SCH_OT_flatten(Operator):
    bl_idname = "smart_curve.flatten"
    bl_label = "Flatten"
    bl_description = "Flatten points and handles on axis plane"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _active_curve_object(context) is not None

    def execute(self, context):
        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis)
        if axis_vec is None:
            self.report({"ERROR"}, "View axis is unavailable in current context.")
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, "No target Bezier points.")
            return {"CANCELLED"}

        vectors = []
        for point in points:
            vectors.append(point.co.copy())
            vectors.append(point.handle_left.copy())
            vectors.append(point.handle_right.copy())
        avg_dot = sum(v.dot(axis_vec) for v in vectors) / len(vectors)

        for point in points:
            point.co = _flatten_vector(point.co, axis_vec, avg_dot, settings.strength)
            point.handle_left = _flatten_vector(point.handle_left, axis_vec, avg_dot, settings.strength)
            point.handle_right = _flatten_vector(point.handle_right, axis_vec, avg_dot, settings.strength)
            _set_handle_type(point, settings.handle_type)

        obj.data.update()
        self.report({"INFO"}, f"Flattened {len(points)} points")
        return {"FINISHED"}


class SCH_OT_equalize_length(Operator):
    bl_idname = "smart_curve.equalize_length"
    bl_label = "Equalize Length"
    bl_description = "Equalize handle lengths across target points"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _active_curve_object(context) is not None

    def execute(self, context):
        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis)
        if axis_vec is None:
            self.report({"ERROR"}, "View axis is unavailable in current context.")
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, "No target Bezier points.")
            return {"CANCELLED"}

        lengths = []
        for point in points:
            lengths.append((point.handle_left - point.co).length)
            lengths.append((point.handle_right - point.co).length)
        non_zero = [value for value in lengths if value > 0.0]
        if not non_zero:
            self.report({"WARNING"}, "No non-zero handle lengths in target.")
            return {"CANCELLED"}
        target_len = sum(non_zero) / len(non_zero)

        for point in points:
            for side_name, sign_hint in (("handle_left", -1.0), ("handle_right", 1.0)):
                handle = getattr(point, side_name)
                vec = handle - point.co
                if vec.length > 0.0:
                    direction = vec.normalized()
                else:
                    direction = axis_vec * sign_hint
                target = point.co + direction * target_len
                setattr(point, side_name, handle.lerp(target, settings.strength))

            _set_handle_type(point, settings.handle_type)

        obj.data.update()
        self.report({"INFO"}, f"Equalized {len(points)} points")
        return {"FINISHED"}


class SCH_PT_panel(Panel):
    bl_idname = "SCH_PT_panel"
    bl_label = "Smart Curve Helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Smart Curve Helper"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.sch_settings

        col = layout.column(align=True)
        col.prop(settings, "axis")
        col.prop(settings, "handle_type")
        col.prop(settings, "strength")
        col.prop(settings, "target")

        layout.separator()
        layout.operator("smart_curve.align_handles", icon="CURVE_BEZCURVE")
        layout.operator("smart_curve.flatten", icon="MESH_GRID")
        layout.operator("smart_curve.equalize_length", icon="DRIVER_DISTANCE")


classes = (
    SCH_Settings,
    SCH_OT_align_handles,
    SCH_OT_flatten,
    SCH_OT_equalize_length,
    SCH_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sch_settings = PointerProperty(type=SCH_Settings)


def unregister():
    del bpy.types.Scene.sch_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
