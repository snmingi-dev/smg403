# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Smart Curve Helper",
    "author": "SMG Tools",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Smart Curve Helper",
    "description": "Align, flatten, and equalize Bezier handles quickly.",
    "doc_url": "https://github.com/snmingi-dev/smg403/tree/main/projects/smart-curve-helper",
    "tracker_url": "https://github.com/snmingi-dev/smg403/issues",
    "category": "Curve",
}

import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from mathutils import Vector


ERR_EDIT_MODE = "Enter Edit Mode on a Curve object."
ERR_NO_BEZIER = "No Bezier points found in the selected target scope."
ERR_VIEW_AXIS = "View axis/space requires an active 3D View region."


def _active_curve_object(context):
    obj = context.active_object
    if obj is None or obj.type != "CURVE":
        return None
    return obj


def _curve_edit_context_ok(context):
    return context.mode == "EDIT_CURVE" and _active_curve_object(context) is not None


def _view_axis_world(context, axis):
    region_3d = context.region_data
    if region_3d is None:
        return None
    rotation = region_3d.view_rotation
    if axis == "X":
        return rotation @ Vector((1.0, 0.0, 0.0))
    if axis == "Y":
        return rotation @ Vector((0.0, 1.0, 0.0))
    return rotation @ Vector((0.0, 0.0, -1.0))


def _axis_local_vector(context, obj, axis, axis_space):
    if axis == "VIEW":
        world_vec = _view_axis_world(context, "Z")
        if world_vec is None:
            return None
        local_vec = obj.matrix_world.to_3x3().inverted_safe() @ world_vec
        return local_vec.normalized() if local_vec.length > 0.0 else None

    axis_map_local = {
        "X": Vector((1.0, 0.0, 0.0)),
        "Y": Vector((0.0, 1.0, 0.0)),
        "Z": Vector((0.0, 0.0, 1.0)),
    }

    if axis_space == "LOCAL":
        return axis_map_local[axis]

    if axis_space == "WORLD":
        world_vec = axis_map_local[axis]
        local_vec = obj.matrix_world.to_3x3().inverted_safe() @ world_vec
        return local_vec.normalized() if local_vec.length > 0.0 else None

    world_vec = _view_axis_world(context, axis)
    if world_vec is None:
        return None
    local_vec = obj.matrix_world.to_3x3().inverted_safe() @ world_vec
    return local_vec.normalized() if local_vec.length > 0.0 else None


def _iter_target_points(obj, target):
    for spline in obj.data.splines:
        if spline.type != "BEZIER":
            continue
        for point in spline.bezier_points:
            if target == "SELECTED_ONLY":
                if not (point.select_control_point or point.select_left_handle or point.select_right_handle):
                    continue
            yield point


def _active_point_or_first(points):
    for point in points:
        if point.select_control_point:
            return point
    return points[0]


def _set_handle_type(point, handle_type):
    point.handle_left_type = handle_type
    point.handle_right_type = handle_type


def _flatten_vector(value, axis_vec, target_dot, strength):
    delta = (target_dot - value.dot(axis_vec)) * strength
    return value + axis_vec * delta


def _flatten_target_dot(points, axis_vec, flatten_reference, obj, context):
    if flatten_reference == "AVERAGE":
        vectors = []
        for point in points:
            vectors.append(point.co.copy())
            vectors.append(point.handle_left.copy())
            vectors.append(point.handle_right.copy())
        return sum(vec.dot(axis_vec) for vec in vectors) / len(vectors)

    if flatten_reference == "ACTIVE_POINT":
        reference = _active_point_or_first(points)
        return reference.co.dot(axis_vec)

    if flatten_reference == "WORLD_ORIGIN":
        local_origin = obj.matrix_world.inverted_safe() @ Vector((0.0, 0.0, 0.0))
        return local_origin.dot(axis_vec)

    cursor_world = context.scene.cursor.location.copy()
    cursor_local = obj.matrix_world.inverted_safe() @ cursor_world
    return cursor_local.dot(axis_vec)


class SCH_Settings(PropertyGroup):
    axis: EnumProperty(
        name="Axis",
        items=[
            ("X", "X", "Use X axis"),
            ("Y", "Y", "Use Y axis"),
            ("Z", "Z", "Use Z axis"),
            ("VIEW", "View", "Use view depth axis"),
        ],
        default="X",
    )
    axis_space: EnumProperty(
        name="Axis Space",
        items=[
            ("LOCAL", "Local", "Use object local axis"),
            ("WORLD", "World", "Use world axis transformed into object local space"),
            ("VIEW", "View", "Use view-aligned axis"),
        ],
        default="LOCAL",
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
    flatten_reference: EnumProperty(
        name="Flatten Reference",
        items=[
            ("AVERAGE", "Average", "Flatten to average target plane"),
            ("ACTIVE_POINT", "Active Point", "Flatten to active/selected point plane"),
            ("WORLD_ORIGIN", "World Origin", "Flatten to world origin plane"),
            ("CURSOR_3D", "3D Cursor", "Flatten to 3D cursor plane"),
        ],
        default="AVERAGE",
    )


class SCH_OT_align_handles(Operator):
    bl_idname = "smart_curve.align_handles"
    bl_label = "Align Handles"
    bl_description = "Align selected handles along axis"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _curve_edit_context_ok(context)

    def execute(self, context):
        if not _curve_edit_context_ok(context):
            self.report({"ERROR"}, ERR_EDIT_MODE)
            return {"CANCELLED"}

        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis, settings.axis_space)
        if axis_vec is None:
            self.report({"ERROR"}, ERR_VIEW_AXIS)
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, ERR_NO_BEZIER)
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
        return _curve_edit_context_ok(context)

    def execute(self, context):
        if not _curve_edit_context_ok(context):
            self.report({"ERROR"}, ERR_EDIT_MODE)
            return {"CANCELLED"}

        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis, settings.axis_space)
        if axis_vec is None:
            self.report({"ERROR"}, ERR_VIEW_AXIS)
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, ERR_NO_BEZIER)
            return {"CANCELLED"}

        target_dot = _flatten_target_dot(
            points=points,
            axis_vec=axis_vec,
            flatten_reference=settings.flatten_reference,
            obj=obj,
            context=context,
        )

        for point in points:
            point.co = _flatten_vector(point.co, axis_vec, target_dot, settings.strength)
            point.handle_left = _flatten_vector(point.handle_left, axis_vec, target_dot, settings.strength)
            point.handle_right = _flatten_vector(point.handle_right, axis_vec, target_dot, settings.strength)
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
        return _curve_edit_context_ok(context)

    def execute(self, context):
        if not _curve_edit_context_ok(context):
            self.report({"ERROR"}, ERR_EDIT_MODE)
            return {"CANCELLED"}

        settings = context.scene.sch_settings
        obj = _active_curve_object(context)
        axis_vec = _axis_local_vector(context, obj, settings.axis, settings.axis_space)
        if axis_vec is None:
            self.report({"ERROR"}, ERR_VIEW_AXIS)
            return {"CANCELLED"}

        points = list(_iter_target_points(obj, settings.target))
        if not points:
            self.report({"WARNING"}, ERR_NO_BEZIER)
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
        col.prop(settings, "axis_space")
        col.prop(settings, "handle_type")
        col.prop(settings, "strength")
        col.prop(settings, "target")
        col.prop(settings, "flatten_reference")

        layout.separator()
        layout.operator("smart_curve.align_handles", icon="CURVE_BEZCURVE")
        layout.operator("smart_curve.flatten", icon="MESH_GRID")
        layout.operator("smart_curve.equalize_length", icon="DRIVER_DISTANCE")
        layout.label(text="Undo is supported for all three operators.")


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
